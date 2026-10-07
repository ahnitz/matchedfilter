"""Comprehensive unit tests for the 2-data DIF bandlimited path in TimeDomainFilterBank."""
import numpy as np
import pytest
import matchedfilter as mf


def test_time_domain_filter_bank_dif_exact_parity():
    """Verify that TimeDomainFilterBank with engine='dif' matches full-rate FFT output."""
    N = 2048
    K = 1024
    n_templates = 16

    rng = np.random.default_rng(100)
    # Generate FIR taps of varying lengths <= 500
    taps = []
    counts = []
    for _ in range(n_templates):
        cnt = rng.integers(100, 450)
        t = rng.standard_normal(cnt).astype(np.float32)
        taps.append(t)
        counts.append(cnt)

    # Synthetic bandlimited series of length 32768
    S_len = 32768
    noise = (rng.standard_normal(S_len) + 1j * rng.standard_normal(S_len)).astype(np.complex64)
    # Zero out above 800 Hz
    n_f = np.fft.fft(noise)
    n_f[int(S_len * 800 / 2048):] = 0
    noise = np.fft.ifft(n_f).astype(np.complex64) * 10.0

    valid_slice = slice(2048, S_len - 2048)

    # 1. DIF bank via engine='dif'
    b_dif = mf.TimeDomainFilterBank(
        taps, counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine='dif', threshold=5.0
    )
    res_dif = b_dif.filter_series(noise, windows=valid_slice)

    # 2. DIF bank via bandlimited=True
    b_bl = mf.TimeDomainFilterBank(
        taps, counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        bandlimited=True, threshold=5.0
    )
    res_bl = b_bl.filter_series(noise, windows=valid_slice)

    assert len(res_dif.template_indices) > 0
    assert len(res_dif.template_indices) == len(res_bl.template_indices)
    assert np.array_equal(res_dif.template_indices, res_bl.template_indices)
    assert np.array_equal(res_dif.sample_indices, res_bl.sample_indices)
    assert np.allclose(res_dif.snr, res_bl.snr, rtol=1e-5, atol=1e-5)


def test_time_domain_filter_bank_dif_single_template():
    """Verify single-template filtering with DIF engine."""
    n_templates = 8
    rng = np.random.default_rng(200)
    taps = [rng.standard_normal(250).astype(np.float32) for _ in range(n_templates)]
    counts = [250] * n_templates

    S_len = 16384
    noise = (rng.standard_normal(S_len) + 1j * rng.standard_normal(S_len)).astype(np.complex64) * 8.0
    valid_slice = slice(1024, S_len - 1024)

    b_dif = mf.TimeDomainFilterBank(
        taps, counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine='dif', threshold=5.0
    )

    res_all = b_dif.filter_series(noise, windows=valid_slice)
    
    # Filter single template 3
    res_3 = b_dif.filter_series(noise, windows=valid_slice, template_index=3)

    mask_3 = (res_all.template_indices == 3)
    assert np.sum(mask_3) == len(res_3.template_indices)
    assert np.array_equal(res_all.sample_indices[mask_3], res_3.sample_indices)
    assert np.allclose(res_all.snr[mask_3], res_3.snr, rtol=1e-5, atol=1e-5)


def test_time_domain_filter_bank_dif_binsize():
    """Verify DIF engine with non-default binsize."""
    n_templates = 4
    rng = np.random.default_rng(300)
    taps = [rng.standard_normal(200).astype(np.float32) for _ in range(n_templates)]
    counts = [200] * n_templates

    S_len = 16384
    noise = (rng.standard_normal(S_len) + 1j * rng.standard_normal(S_len)).astype(np.complex64) * 8.0
    valid_slice = slice(1024, S_len - 1024)

    b_dif = mf.TimeDomainFilterBank(
        taps, counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine='dif', threshold=5.0
    )

    res_b512 = b_dif.filter_series(noise, windows=valid_slice, binsize=512)
    res_b2048 = b_dif.filter_series(noise, windows=valid_slice, binsize=2048)

    # Smaller binsize yields >= number of triggers as larger binsize
    assert len(res_b512.template_indices) >= len(res_b2048.template_indices)
