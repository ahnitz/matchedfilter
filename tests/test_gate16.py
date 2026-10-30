"""The FP16 first gate (src/gate16.cc, ARM with FP16 vectors) reports its own statistic: each
pair's FP16 maximum, which tracks the FP32 gate's coarse maximum to FP16 precision. What its
rounding does to the search is accepted by the chain's false dismissal against the flat
filter (tools/fdr_audit.py on an ARM runner), not here. These check for gross errors -- a
wrong lag, a wrong scale, an overflow -- with a limit of 2^-6 relative (the GPU's fp16 tier
uses the same, tests/test_gpu_c16_statistic.py), and that the hierarchical results are the
FP32 gate's except for pairs that gate decided within that of its threshold."""
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core

#: The relative limit of a gross error (see the module docstring).
GROSS = 2.0 ** -6

pytestmark = pytest.mark.skipif(not getattr(_core, "gate16", lambda: False)(),
                                reason="no FP16 first gate in this build (ARM with FP16 vectors only)")


def _bank(n, nt, rng):
    f = np.fft.fftfreq(n)
    power = np.zeros(n)
    power[f > 0] = f[f > 0] ** (-7 / 3)
    h = (np.sqrt(power) * np.exp(2j * np.pi * rng.random((nt, n)))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    return h, power


def _dumped(monkeypatch, tmp_path, kind, n, chain, d, h, power, thr):
    path = tmp_path / ("%s.bin" % kind)
    monkeypatch.setenv("MF_HMF_DUMP", str(path))
    monkeypatch.setenv("MF_GATE16", "1" if kind == "f16" else "0")
    hf = mf.HierarchicalFilter(n, ndata=d.shape[0], ntemplates=h.shape[0], chain=chain)
    hf.set_reference(power)
    hf.set_coarse_threshold(thr)
    hf.set_data(d)
    hf.set_templates(h)
    out = hf.run(binsize=n // 4, threshold=4.0).copy()
    del hf
    return np.fromfile(path, np.float32).reshape(-1, 8), out


@pytest.mark.parametrize("n,chain", [(2048, (128,)), (2048, (256, 512)), (4096, (512,)),
                                     (1024, (64,))])
def test_fp16_gate_reports_its_own_statistic_and_keeps_the_fp32_results(monkeypatch, tmp_path,
                                                                         n, chain):
    rng = np.random.default_rng(n + chain[0])
    nd, nt = 6, 21                      # 21: a partial group of eight lanes
    h, power = _bank(n, nt, rng)
    d = ((rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n)))).astype(np.complex64)
    d[2] += (9.0 * np.sqrt(n) * h[5] * np.exp(2j * np.pi * np.arange(n) * 300 / n)).astype(np.complex64)
    d[4] *= 30.0                        # a loud block: the statistic must scale with it
    zeros = tuple(0.0 for _ in chain)
    r32, _ = _dumped(monkeypatch, tmp_path, "f32", n, chain, d, h, power, zeros)
    r16, _ = _dumped(monkeypatch, tmp_path, "f16", n, chain, d, h, power, zeros)
    assert r32.shape == r16.shape and np.array_equal(r32[:, 6:], r16[:, 6:])
    stat, exact = r16[:, 0], r32[:, 0]
    err = np.abs(stat - exact) / np.maximum(exact, 1.0)
    assert err.max() < GROSS, "relative error %.2e against the FP32 maximum" % err.max()
    # With real gates both runs refine in FP32, so a peak both report is the same peak; a pair
    # whose results differ is one the first tier decided within its rounding of the threshold
    # (later tiers are FP32 on both sides).
    thr = tuple(float(np.quantile(exact, 0.9)) * (1 + 0.1 * i) for i in range(len(chain)))
    _, o32 = _dumped(monkeypatch, tmp_path, "f32", n, chain, d, h, power, thr)
    _, o16 = _dumped(monkeypatch, tmp_path, "f16", n, chain, d, h, power, thr)
    both = (o32["index"] >= 0) & (o16["index"] >= 0)
    assert both.any()
    np.testing.assert_array_equal(o16["index"][both], o32["index"][both])
    np.testing.assert_array_equal(o16["value"][both], o32["value"][both])
    margin = {(int(dd), int(tt)) for v, dd, tt in zip(exact, r32[:, 6], r32[:, 7])
              if abs(v - thr[0]) <= GROSS * max(v, 1.0)}
    found32, found16 = o32["index"] >= 0, o16["index"] >= 0
    differ = {(int(a), int(b)) for a, b, *_ in zip(*np.nonzero(found32 != found16))}
    assert differ <= margin, "pairs decided differently away from the threshold: %s" % sorted(
        differ - margin)[:6]


def test_fp16_gate_switch_is_reported_to_the_cost_cache(monkeypatch):
    from matchedfilter import gatechain
    monkeypatch.setenv("MF_GATE16", "0")
    assert gatechain.cpu_gate_kind() == "f32"
    monkeypatch.delenv("MF_GATE16")
    assert gatechain.cpu_gate_kind() == "f16"
