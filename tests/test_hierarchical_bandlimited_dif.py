"""Unit tests for HierarchicalFilter with zero-pruned template storage (K = N // 2)
and Decimation-in-Frequency (DIF) refinement engine integration.
"""
import numpy as np
import pytest
import matchedfilter as mf


def test_hierarchical_filter_bandlimited_dif_direct():
    """Verify that HierarchicalFilter produces identical results with full (N) and half (N//2) templates."""
    N = 2048
    K = N // 2
    n_templates = 16
    band = 256
    taps = 8

    rng = np.random.default_rng(42)

    # Generate synthetic bandlimited templates (zero above bin 800)
    tmpl_full = np.zeros((n_templates, N), dtype=np.complex64)
    for i in range(n_templates):
        # generate random frequency spectrum up to bin 800
        spec = (rng.standard_normal(800) + 1j * rng.standard_normal(800)).astype(np.complex64)
        tmpl_full[i, :800] = spec / np.linalg.norm(spec)

    tmpl_half = np.ascontiguousarray(tmpl_full[:, :K])

    # Reference profile (power profile of template)
    ref_profile = np.abs(tmpl_full[0]) ** 2
    ref_profile /= np.sum(ref_profile)

    # Generate test data (bandlimited noise + injected templates)
    S_len = 32768
    data = (rng.standard_normal(S_len) + 1j * rng.standard_normal(S_len)).astype(np.complex64)
    data_f = np.fft.fft(data)
    data_f[int(S_len * 800 / N):] = 0
    data = np.fft.ifft(data_f).astype(np.complex64) * 5.0

    # Inject template 3 with known SNR ~ 8.0
    sig = np.fft.ifft(np.pad(tmpl_full[3], (0, 0))) * np.sqrt(N)
    data[10000:10000 + N] += sig * 8.0

    threshold = 5.5

    # 1. Full-size templates HierarchicalFilter
    hf_full = mf.HierarchicalFilter(
        N, ndata=1, ntemplates=n_templates,
        band=band, taps=taps, snr=threshold, fd=0.01,
        cascade=False
    )
    hf_full.set_coarse_threshold(3.0)
    hf_full.set_templates(tmpl_full)

    # 2. Half-size templates HierarchicalFilter (DIF)
    hf_half = mf.HierarchicalFilter(
        N, ndata=1, ntemplates=n_templates,
        band=band, taps=taps, snr=threshold, fd=0.01,
        cascade=False
    )
    hf_half.set_coarse_threshold(3.0)
    hf_half.set_templates(tmpl_half)

    starts = np.arange(0, S_len - N, N // 2, dtype=np.uintp)
    wstart = np.full(len(starts), N // 4, dtype=np.uintp)
    wend = np.full(len(starts), 3 * N // 4, dtype=np.uintp)

    res_full = hf_full.run_series(data, starts=starts, win_start=wstart, win_end=wend,
                                  binsize=N, threshold=threshold)
    res_half = hf_half.run_series(data, starts=starts, win_start=wstart, win_end=wend,
                                  binsize=N, threshold=threshold)

    # Verify both detected triggers
    assert len(res_full) > 0, "No triggers detected by full filter"
    assert len(res_half) > 0, "No triggers detected by half filter"
    assert len(res_full) == len(res_half), f"Trigger count mismatch: {len(res_full)} vs {len(res_half)}"

    # Check peak indices and SNR values
    np.testing.assert_array_equal(res_full['index'], res_half['index'])
    np.testing.assert_allclose(res_full['value'], res_half['value'], atol=1e-5, rtol=1e-5)
    max_err = np.max(np.abs(np.abs(res_full['value']) - np.abs(res_half['value'])))
    assert max_err <= 1e-5, f"Max SNR error {max_err} exceeds 1e-5"


def test_time_domain_filter_bank_hier_template_memory_halved():
    """Verify that TimeDomainFilterBank with engine='hier' stores K = N // 2 templates."""
    N = 2048
    n_templates = 8
    rng = np.random.default_rng(123)

    taps = [rng.standard_normal(300).astype(np.float32) for _ in range(n_templates)]
    counts = [300] * n_templates

    bank = mf.TimeDomainFilterBank(
        taps, counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine='hier', threshold=5.0,
        coarse_band_hz=256.0,
    )

    # Check that each group has spectra of width N // 2
    for g in bank._groups:
        assert g.spectra.shape[1] == g.n // 2, (
            f"Expected group spectra shape ({len(g.template_indices)}, {g.n // 2}), "
            f"got {g.spectra.shape}"
        )
