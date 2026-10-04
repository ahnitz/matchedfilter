"""Test the optional fixed-point (Q15 / INT16) coarse matched filter path."""
import os
import numpy as np
import pytest
import matchedfilter as mf
from matchedfilter.benchmark import _inspiral_power


@pytest.mark.parametrize("n", [128, 256, 512])
def test_q15_matched_filter_peak_accuracy(n, monkeypatch):
    """Verify that Q15 coarse matched filtering preserves peak index and magnitude."""
    nd, nt = 4, 32
    rng = np.random.default_rng(12345 + n)
    d = (rng.normal(size=(nd, n)) + 1j * rng.normal(size=(nd, n))).astype(np.complex64)
    t = (rng.normal(size=(nt, n)) + 1j * rng.normal(size=(nt, n))).astype(np.complex64)

    # 1. Baseline FP32
    monkeypatch.delenv("MF_COARSE_INT16", raising=False)
    mf_fp = mf.MatchedFilter(n, nd, nt)
    mf_fp.set_data(d)
    mf_fp.set_templates(t)
    pk_fp, _ = mf_fp.run(binsize=n, threshold=0.0, counts=True)

    # 2. Optional Q15 path
    monkeypatch.setenv("MF_COARSE_INT16", "1")
    mf_q15 = mf.MatchedFilter(n, nd, nt)
    mf_q15.set_data(d)
    mf_q15.set_templates(t)
    pk_q15, _ = mf_q15.run(binsize=n, threshold=0.0, counts=True)

    # Check that magnitude matches to within Q15 fixed-point quantization tolerance (1%)
    np.testing.assert_allclose(
        np.abs(pk_fp["value"]), np.abs(pk_q15["value"]), rtol=1e-2, atol=1.0
    )
    # Check that indices match, allowing ties where peak magnitude difference is within quantization tolerance
    idx_match = (pk_fp["index"] == pk_q15["index"])
    if not idx_match.all():
        mag_diff = np.abs(np.abs(pk_fp["value"]) - np.abs(pk_q15["value"]))
        assert (idx_match | (mag_diff < 1.0)).all()


def test_q15_hierarchical_injection_preservation(monkeypatch):
    """Verify that Q15 coarse filtering triggers on injected signals and matches FP32 refinement."""
    n = 4096
    power = _inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)
    h_conj = np.conj(h)
    nd, nt = 4, 32

    rng = np.random.default_rng(2026)
    noise = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    # Inject signal in pair (0, 0)
    noise[0] += (12.0 * h).astype(np.complex64)

    # Baseline FP32
    monkeypatch.delenv("MF_COARSE_INT16", raising=False)
    hf_fp = mf.HierarchicalFilter(n, nd, nt, band=512, snr=5.5, fd=1e-3)
    hf_fp.set_reference(power)
    hf_fp.set_templates(np.repeat(h_conj[None, :], nt, axis=0))
    hf_fp.set_data(noise)
    res_fp = hf_fp.run(binsize=n, threshold=5.0)

    # Q15 coarse screening
    monkeypatch.setenv("MF_COARSE_INT16", "1")
    hf_q15 = mf.HierarchicalFilter(n, nd, nt, band=512, snr=5.5, fd=1e-3)
    hf_q15.set_reference(power)
    hf_q15.set_templates(np.repeat(h_conj[None, :], nt, axis=0))
    hf_q15.set_data(noise)
    res_q15 = hf_q15.run(binsize=n, threshold=5.0)

    # Verify identical trigger count
    assert hf_fp.stats == hf_q15.stats
    # Verify exact match on refined peak index and value
    np.testing.assert_array_equal(res_fp["index"], res_q15["index"])
    np.testing.assert_allclose(res_fp["value"], res_q15["value"], rtol=1e-5, atol=1e-5)
