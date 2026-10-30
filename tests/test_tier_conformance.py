"""Every first-tier kind on every device makes the same gate decisions and reports the same
peaks, at tier thresholds that no rounding can decide.

The kinds: the CPU's FP32 gate, its Q15 screen in front of it (x86), its FP16 gate (ARM,
src/gate16.cc), and the machine's GPU (an fp16 tier, tierb.slang). Each gates on its own
statistic of a pair's coarse maximum: exact, or within about 1% of it in reduced precision
(tools/gate_margin.py). So a threshold in a wide gap of the pairs' exact maxima --
taken from the FP32 gate's own dump (MF_HMF_DUMP) -- must pass exactly the pairs above it on
every kind. The final threshold is 0, so every refined pair reports a peak: the peak indices
are the gate decisions. tests/test_coarse_conformance.py does the same for every GPU coarse
layout; this suite puts the CPU tiers and the GPU on one footing.
"""
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core

CASES = [(2048, (128,)), (2048, (256,)), (2048, (512,)), (4096, (256, 1024))]


def _case(n, rng):
    nd, nt = 6, 21                      # 21: a partial group of eight lanes
    f = np.fft.fftfreq(n)
    power = np.zeros(n)
    power[f > 0] = f[f > 0] ** (-7 / 3)
    h = (np.sqrt(power) * np.exp(2j * np.pi * rng.random((nt, n)))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    d = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    d[2] += (12.0 * np.sqrt(n) * h[5] * np.exp(2j * np.pi * np.arange(n) * 300 / n)).astype(np.complex64)
    d[4] += (9.0 * np.sqrt(n) * h[17] * np.exp(2j * np.pi * np.arange(n) * 1700 / n)).astype(np.complex64)
    return d, h, power


def _filter(device, n, chain, d, h, power, thr):
    hf = mf.HierarchicalFilter(n, ndata=d.shape[0], ntemplates=h.shape[0], chain=chain,
                               device=device)
    hf.set_reference(power)
    hf.set_coarse_threshold(thr)
    hf.set_data(d)
    hf.set_templates(h)
    return hf


def _run(device, kind, n, chain, d, h, power, thr, monkeypatch):
    monkeypatch.setenv("MF_GATE16", "1" if kind == "f16" else "0")
    hf = _filter(device, n, chain, d, h, power, thr)
    if device == "cpu":
        hf._ensure()
        if kind == "q15":
            if not hf._mf.set_q15(True):
                pytest.skip("no Q15 screen on this back end")
        else:
            hf._mf.set_q15(False)
    out = hf.run(binsize=n // 4, threshold=0.0)
    if kind == "q15" and not hf._mf.q15_stats()[0]:
        pytest.skip("the Q15 screen did not run at chain %s" % (chain,))
    return np.asarray(out["index"]).copy(), np.asarray(out["value"]).copy()


def _exact_maxima(n, chain, d, h, power, monkeypatch, tmp_path):
    """Each pair's exact first-tier maximum, from the FP32 gate passing every pair."""
    path = tmp_path / "f32.bin"
    monkeypatch.setenv("MF_HMF_DUMP", str(path))
    monkeypatch.setenv("MF_GATE16", "0")
    hf = _filter("cpu", n, chain, d, h, power, tuple(0.0 for _ in chain))
    hf.run(binsize=n // 4, threshold=0.0)
    del hf
    monkeypatch.delenv("MF_HMF_DUMP")
    rec = np.fromfile(path, np.float32).reshape(-1, 8)
    ex = np.zeros((d.shape[0], h.shape[0]))
    ex[rec[:, 6].astype(int), rec[:, 7].astype(int)] = rec[:, 0]
    return ex


def _gap_threshold(ex, ratio=1.08):
    """The geometric midpoint of the widest gap above the median, at least `ratio` wide."""
    v = np.unique(ex.ravel())
    v = v[v >= np.median(v)]
    gaps = [(v[i + 1] / v[i], np.sqrt(v[i] * v[i + 1])) for i in range(len(v) - 1)
            if v[i] > 0 and v[i + 1] / v[i] >= ratio]
    assert gaps, "no wide gap in the coarse maxima"
    return float(max(gaps)[1])


def _devices():
    from conftest import usable_gpu
    gpu = usable_gpu()
    return ["cpu"] + ([gpu] if gpu else [])


@pytest.mark.parametrize("n,chain", CASES)
def test_every_tier_kind_makes_the_exact_gate_decisions(n, chain, monkeypatch, tmp_path):
    rng = np.random.default_rng(n + chain[0])
    d, h, power = _case(n, rng)
    ex = _exact_maxima(n, chain, d, h, power, monkeypatch, tmp_path)
    t0 = _gap_threshold(ex)
    thr = (t0,) + tuple(0.0 for _ in chain[1:])     # later tiers pass what tier 0 passes
    want = ex > t0
    assert 0 < want.sum() < want.size
    kinds = [("cpu", "f32"), ("cpu", "q15")]
    if getattr(_core, "gate16", lambda: False)():
        kinds.append(("cpu", "f16"))
    kinds += [(dev, "gpu") for dev in _devices()[1:]]
    ref = None
    for device, kind in kinds:
        try:
            idx, val = _run(device, kind, n, chain, d, h, power, thr, monkeypatch)
        except pytest.skip.Exception:
            continue
        where = "%s %s chain %s" % (device, kind, chain)
        passed = (idx >= 0).any(axis=-1)
        np.testing.assert_array_equal(passed, want, err_msg="%s: gate decisions" % where)
        if ref is None:
            ref = (idx, val)
            continue
        np.testing.assert_array_equal(idx, ref[0], err_msg=where)
        if device == "cpu":
            np.testing.assert_array_equal(val, ref[1], err_msg=where)   # one FP32 refine
        else:
            np.testing.assert_allclose(val, ref[1], rtol=1e-4, atol=1e-3, err_msg=where)
