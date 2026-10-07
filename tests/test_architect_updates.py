"""Unit tests for search architect updates:
- _core.taps_to_spectra vectorized FIR ingestion
- TimeDomainFilterBank memory management and raw_taps
- chain trials: what is measured and how it is normalised
"""
import os
import tempfile
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core, CorrelationFilter
from matchedfilter.time_domain import TimeDomainFilterBank


def test_taps_to_spectra_numpy_equivalence():
    """Verify that _core.taps_to_spectra matches np.fft.fft circularly-rolled taps."""
    rng = np.random.default_rng(42)
    for n in (1024, 2048, 4096):
        T = 8
        max_taps = 350
        taps = rng.standard_normal((T, max_taps)).astype(np.float32)
        counts = rng.integers(50, max_taps, size=T, dtype=np.int64)

        py_spectra = np.zeros((T, n), dtype=np.complex64)
        for t in range(T):
            cnt = int(counts[t])
            buf = np.zeros(n, dtype=np.float32)
            buf[:cnt] = taps[t, :cnt]
            buf = np.roll(buf, -(cnt // 2))
            py_spectra[t] = np.fft.fft(buf).astype(np.complex64)

        c_spectra = np.zeros((T, n), dtype=np.complex64)
        _core.taps_to_spectra(taps, counts, n, max_taps, c_spectra)

        assert np.allclose(py_spectra, c_spectra, atol=1e-4, rtol=1e-4)


def test_taps_to_spectra_int32_and_int64():
    """Verify that _core.taps_to_spectra supports both int32 and int64 count arrays identically."""
    rng = np.random.default_rng(123)
    n = 2048
    T = 6
    max_taps = 200
    taps = rng.standard_normal((T, max_taps)).astype(np.float32)
    counts64 = rng.integers(30, max_taps, size=T, dtype=np.int64)
    counts32 = counts64.astype(np.int32)

    out64 = np.zeros((T, n), dtype=np.complex64)
    out32 = np.zeros((T, n), dtype=np.complex64)

    _core.taps_to_spectra(taps, counts64, n, max_taps, out64)
    _core.taps_to_spectra(taps, counts32, n, max_taps, out32)

    assert np.array_equal(out64, out32)


def test_taps_to_spectra_error_handling():
    """Verify that _core.taps_to_spectra strictly validates arguments and buffer sizes."""
    taps = np.ones((4, 50), dtype=np.float32)
    counts = np.full(4, 50, dtype=np.int64)
    out = np.zeros((4, 1024), dtype=np.complex64)

    # Invalid n or max_taps
    with pytest.raises(ValueError, match="positive"):
        _core.taps_to_spectra(taps, counts, 0, 50, out)
    with pytest.raises(ValueError, match="positive"):
        _core.taps_to_spectra(taps, counts, 1024, -1, out)

    # Taps shape not divisible by max_taps
    with pytest.raises(ValueError, match="invalid taps shape"):
        _core.taps_to_spectra(np.ones(196, dtype=np.float32), counts, 1024, 50, out)

    # Counts buffer size mismatch
    with pytest.raises(ValueError, match="counts buffer size mismatch"):
        _core.taps_to_spectra(taps, counts[:1], 1024, 50, out)
    with pytest.raises(ValueError, match="counts buffer size mismatch"):
        _core.taps_to_spectra(taps, counts[:3], 1024, 50, out)

    # Output buffer too small
    with pytest.raises(ValueError, match="output buffer too small"):
        _core.taps_to_spectra(taps, counts, 1024, 50, out[:3])


def test_taps_to_spectra_nonpositive_counts():
    """Verify that non-positive counts are safely zeroed rather than corrupting memory."""
    taps = np.ones((2, 50), dtype=np.float32)
    counts = np.array([0, -5], dtype=np.int64)
    out = np.ones((2, 1024), dtype=np.complex64)

    _core.taps_to_spectra(taps, counts, 1024, 50, out)
    assert np.all(out == 0)


def test_timedomainfilterbank_2d_raw_taps_and_memory():
    """Verify that TimeDomainFilterBank accepts 2D arrays, matches list input, and frees raw taps."""
    rng = np.random.default_rng(999)
    T = 8
    max_taps = 300
    taps_2d = rng.standard_normal((T, max_taps)).astype(np.float32)
    counts = rng.integers(100, max_taps, size=T, dtype=np.int64)
    taps_list = [taps_2d[i, :counts[i]] for i in range(T)]

    bank_2d = TimeDomainFilterBank(taps_2d, tap_counts=counts, engine='flat', threshold=5.0)
    bank_list = TimeDomainFilterBank(taps_list, tap_counts=counts, engine='flat', threshold=5.0)

    # Memory cleanup verification: both raw_taps and taps_list must be freed
    assert bank_2d._raw_taps is None
    assert bank_2d._taps_list is None
    assert bank_list._raw_taps is None
    assert bank_list._taps_list is None

    # Filter outputs should match
    data = (rng.standard_normal(32768) + 1j * rng.standard_normal(32768)).astype(np.complex64)
    res_2d = bank_2d.filter_series(data)
    res_list = bank_list.filter_series(data)

    assert np.array_equal(res_2d.sample_indices, res_list.sample_indices)
    assert np.allclose(res_2d.snr, res_list.snr, atol=1e-5)


def test_public_taps_to_spectra_api():
    """Verify that public matchedfilter.taps_to_spectra matches np.fft.fft circularly rolled taps."""
    rng = np.random.default_rng(999)
    n = 2048
    T = 4
    max_taps = 180
    taps = rng.standard_normal((T, max_taps)).astype(np.float32)
    counts = np.array([80, 120, 150, 180], dtype=np.int64)

    # Public API with out=None
    res1 = mf.taps_to_spectra(taps, counts, n)
    assert res1.shape == (T, n)
    assert res1.dtype == np.complex64

    # Public API with preallocated out
    res2 = np.zeros((T, n), dtype=np.complex64)
    mf.taps_to_spectra(taps, counts, n, out=res2)
    assert np.array_equal(res1, res2)

    # Verify against numpy
    for t in range(T):
        cnt = int(counts[t])
        buf = np.zeros(n, dtype=np.float32)
        buf[:cnt] = taps[t, :cnt]
        buf = np.roll(buf, -(cnt // 2))
        np.testing.assert_allclose(res1[t], np.fft.fft(buf), atol=1e-5)


def test_time_domain_filter_bank_narrow_slice_and_template_index():
    """Verify that TimeDomainFilterBank narrow slice O(1) layout matches full segment filtering exactly."""
    rng = np.random.default_rng(555)
    counts = [200, 400]
    taps = [rng.standard_normal(c).astype(np.float32) for c in counts]
    bank = TimeDomainFilterBank(
        taps, tap_counts=counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine='flat', threshold=10.0
    )

    data_len = 65536
    data = (rng.standard_normal(data_len) + 1j * rng.standard_normal(data_len)).astype(np.complex64)
    # Inject template 1 at sample 30000
    c1 = counts[1]
    data[30000 - c1 // 2 : 30000 - c1 // 2 + c1] += taps[1] * 20.0

    full_res = bank.filter_series(data)
    # Target trigger around 30000
    mask_full = (full_res.template_indices == 1) & (full_res.sample_indices == 30000)
    assert np.any(mask_full)
    full_snr = full_res.snr[mask_full][0]

    # Narrow slice follow-up for template 1 around 30000
    narrow_slice = slice(29500, 30500)
    narrow_res = bank.filter_series(data, windows=narrow_slice, template_index=1)
    mask_narrow = (narrow_res.template_indices == 1) & (narrow_res.sample_indices == 30000)
    assert np.any(mask_narrow)
    narrow_snr = narrow_res.snr[mask_narrow][0]

    assert np.isclose(full_snr, narrow_snr, atol=1e-5)
    # All triggers from narrow slice must be within [29500, 30500)
    assert np.all(narrow_res.sample_indices >= 29500)
    assert np.all(narrow_res.sample_indices < 30500)


def test_chain_trial_work_normalization(monkeypatch):
    """Chain trials time full-template series calls per (block x template) and ignore follow-up slices."""
    def inspiral_power(n, exponent=-7 / 3.0, knee_frac=0.0150):
        p = np.zeros(n, dtype=np.float32)
        k = np.arange(1, n // 2).astype(np.float64)
        p[1:n // 2] = (k ** exponent / ((knee_frac * n / k) ** 4 + 1.0)).astype(np.float32)
        return p / p.sum()

    monkeypatch.setenv("MF_CHAIN_MARGIN", "100")      # keep several chains on the short list
    monkeypatch.setenv("MF_AUTOTUNE", "1")
    mf.clear_autotune_cache()
    n, nt = 4096, 4
    power = inspiral_power(n)
    h = np.conj(np.sqrt(power).astype(np.complex64))
    hf = mf.HierarchicalFilter(n, 1, nt, snr=5.5, fd=1e-3, valid=(0, n))
    hf.set_reference(power)
    hf.set_templates(np.repeat(h[None, :], nt, axis=0))
    assert hf.autotune_info["status"] == "trial" and len(hf.autotune_info["shortlist"]) > 1

    rng = np.random.default_rng(77)
    series = (rng.standard_normal(n * 8) + 1j * rng.standard_normal(n * 8)).astype(np.complex64)

    def samples():
        (trial,) = mf.get_autotune_state()["trials"].values()
        return trial["samples"][hf.config]

    # A follow-up on one template over one block is not representative work: not recorded.
    hf.run_series(series, starts=np.array([0], dtype=np.uintp), win_start=np.array([0], dtype=np.uintp),
                  win_end=np.array([n], dtype=np.uintp), binsize=n, threshold=5.0, templates=(1, 1))
    assert samples() == []
    # A full call over 4 blocks is recorded once, per pair.
    starts = np.array([0, n, 2 * n, 3 * n], dtype=np.uintp)
    hf.run_series(series, starts=starts, win_start=np.zeros(4, dtype=np.uintp),
                  win_end=np.full(4, n, dtype=np.uintp), binsize=n, threshold=5.0)
    s = samples()
    assert len(s) == 1 and 0 < s[0] < 1e-3          # seconds per (block x template) pair
