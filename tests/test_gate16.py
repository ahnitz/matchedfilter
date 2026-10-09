"""The FP16 first gate (src/gate16.cc, ARM with FP16 vectors): an upper bound on the FP32
gate's coarse maximum for every pair, so it passes every pair the FP32 gate passes, and the
hierarchical results are those of the FP32 gate."""
import os

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core

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
def test_fp16_gate_bounds_the_fp32_gate_and_keeps_its_results(monkeypatch, tmp_path, n, chain):
    rng = np.random.default_rng(n + chain[0])
    nd, nt = 6, 21                      # 21: a partial group of eight lanes
    h, power = _bank(n, nt, rng)
    d = ((rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n)))).astype(np.complex64)
    d[2] += (9.0 * np.sqrt(n) * h[5] * np.exp(2j * np.pi * np.arange(n) * 300 / n)).astype(np.complex64)
    d[4] *= 30.0                        # a loud block: the bound must scale with it
    zeros = tuple(0.0 for _ in chain)
    r32, _ = _dumped(monkeypatch, tmp_path, "f32", n, chain, d, h, power, zeros)
    r16, _ = _dumped(monkeypatch, tmp_path, "f16", n, chain, d, h, power, zeros)
    assert r32.shape == r16.shape and np.array_equal(r32[:, 6:], r16[:, 6:])
    bound, exact = r16[:, 0], r32[:, 0]
    assert np.all(bound >= exact), "the FP16 bound fell below the FP32 maximum"
    assert np.all(bound - exact <= 1e-2 * np.maximum(exact, 1.0) + 1e-6)
    # With real gates every FP32 peak is found, identically (the refine is FP32 in both); the
    # FP16 gate may pass a pair the FP32 gate dismissed by less than its margin, and only then
    # report a peak the FP32 run did not.
    thr = tuple(float(np.quantile(exact, 0.9)) * (1 + 0.1 * i) for i in range(len(chain)))
    _, o32 = _dumped(monkeypatch, tmp_path, "f32", n, chain, d, h, power, thr)
    _, o16 = _dumped(monkeypatch, tmp_path, "f16", n, chain, d, h, power, thr)
    found = o32["index"] >= 0
    assert found.any()
    np.testing.assert_array_equal(o16["index"][found], o32["index"][found])
    np.testing.assert_array_equal(o16["value"][found], o32["value"][found])


def test_fp16_gate_switch_is_reported_to_the_cost_cache(monkeypatch):
    from matchedfilter import gatechain
    monkeypatch.setenv("MF_GATE16", "0")
    assert gatechain.cpu_gate_kind() == "f32"
    monkeypatch.delenv("MF_GATE16")
    assert gatechain.cpu_gate_kind() == "f16"
