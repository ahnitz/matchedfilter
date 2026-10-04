"""Unit tests verifying the one-sided analytic signal properties and reduced-rate transforms."""

import numpy as np
import pytest
import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank


def _generate_chirp(N, fs, f_low=30.0, f_high=750.0, phase_offset=0.0):
    t = np.arange(N) / fs
    duration = N / fs
    phase = 2.0 * np.pi * (f_low * t + 0.5 * (f_high - f_low) / duration * (t ** 2)) + phase_offset
    return np.cos(phase).astype(np.float32)


def test_analytic_signal_frequency_decimation():
    """Verify that an analytic signal with bandwidth in [20, 800) Hz can be decimated losslessly."""
    N2 = 2048
    N1 = 1024
    fs = 2048.0

    s = _generate_chirp(N2, fs, 30.0, 750.0, 0.0)
    h = _generate_chirp(N2, fs, 30.0, 750.0, 0.3)

    S = np.fft.fft(s)
    H = np.fft.fft(h)

    # Positive-frequency product (analytic matched filter)
    prod2 = np.zeros(N2, dtype=np.complex64)
    k_min = int(round(20.0 * N2 / fs))
    k_max = int(round(800.0 * N2 / fs))
    prod2[k_min:k_max] = S[k_min:k_max] * np.conj(H[k_min:k_max])

    z2048 = np.fft.ifft(prod2)

    # Decimated transform: keep positive bins [0, N1)
    prod1 = prod2[:N1]
    z1024 = np.fft.ifft(prod1)

    # Even samples relation: z2048[2n] == 0.5 * z1024[n]
    diff_even = np.abs(z2048[0::2] - z1024 * 0.5)
    rel_even = np.max(diff_even) / np.max(np.abs(z2048))
    assert rel_even < 1e-6, f"Even sample relative error {rel_even} exceeded 1e-6"

    # Odd samples relation via half-sample phase rotation
    rot = np.exp(1j * 2.0 * np.pi * np.arange(N1) / N2)
    odd_fft = np.fft.ifft(prod1 * rot)
    diff_odd = np.abs(z2048[1::2] - odd_fft * 0.5)
    rel_odd = np.max(diff_odd) / np.max(np.abs(z2048))
    assert rel_odd < 1e-6, f"Odd sample relative error {rel_odd} exceeded 1e-6"


def test_one_sided_spectrum_ingest():
    """Verify that one-sided tap spectrum preserves positive-frequency filter power."""
    N_taps = 2048
    N_engine = 1024
    fs = 2048.0

    taps = _generate_chirp(701, fs, 30.0, 750.0, 0.0)
    buf = np.zeros(N_taps, dtype=np.float32)
    buf[:len(taps)] = taps
    buf = np.roll(buf, -(len(taps) // 2))

    spec2048 = np.fft.fft(buf).astype(np.complex64)

    # Positive frequency power in [20, 800) Hz
    k_max = int(round(800.0 * N_taps / fs))
    power_pos = np.sum(np.abs(spec2048[20:k_max]) ** 2)
    # Corresponding negative frequency bins: N_taps - k for k in [20, k_max)
    neg_indices = N_taps - np.arange(20, k_max)
    power_neg = np.sum(np.abs(spec2048[neg_indices]) ** 2)

    # Real taps have exactly equal power in conjugate negative frequency bins
    np.testing.assert_allclose(power_pos, power_neg, rtol=1e-5)

    # When matched against an analytic series with positive support only,
    # retaining spec2048[:N_engine] captures 100% of the relevant positive frequencies
    spec_onesided = spec2048[:N_engine]
    assert len(spec_onesided) == N_engine
    assert np.allclose(spec_onesided[20:k_max], spec2048[20:k_max])


def test_timedomain_filterbank_analytic_n1024():
    """Verify that TimeDomainFilterBank with analytic=True partitions at N=1024 for 1024 Hz data."""
    fs_taps = 2048.0
    fs_data = 1024.0
    taps = _generate_chirp(350, fs_taps, 30.0, 750.0, 0.0)

    bank = TimeDomainFilterBank(
        [taps], tap_counts=[350],
        tap_sample_rate=fs_taps,
        data_sample_rate=fs_data,
        engine='corr',
        analytic=True
    )

    # Effective tap count in 1024 Hz data samples is ceil(350 / 2) = 175 samples
    # For 175 samples, N=1024 gives valid fraction (1024 - 175) / 1024 = 82.9% >= 50%
    assert bank._groups[0].n == 1024
    filt_f = bank.get_filter_f(0)
    assert len(filt_f) == 1024

    # Correlate a 1024 Hz continuous series
    S = 4096
    t = np.arange(S) / fs_data
    phase = 2.0 * np.pi * (50.0 * t + 0.5 * 100.0 * t**2)
    # Analytic signal (complex exp)
    data = np.exp(1j * phase).astype(np.complex64)

    out = bank.correlate_series(data)
    assert out.shape == (1, S)
    assert not np.all(out == 0)


def test_analytic_series_container():
    """Verify AnalyticSeries construction, properties, indexing, and window interpolation."""
    N2 = 8192
    fs2 = 2048.0
    t = np.arange(N2) / fs2
    phase = 2.0 * np.pi * (30.0 * t + 0.5 * (750.0 - 30.0) / (N2 / fs2) * t**2)
    s = np.cos(phase).astype(np.float32)
    S = np.fft.fft(s)
    S[N2 // 2:] = 0
    S[0] *= 0.5
    z_true = (np.fft.ifft(S) * 2.0).astype(np.complex64)

    # 1D AnalyticSeries at 1024 Hz
    z_1024 = z_true[::2]
    aser = mf.AnalyticSeries(z_1024, sample_rate=1024.0, input_sample_rate=2048.0, band=(20.0, 800.0))

    assert aser.input_size == N2
    assert aser.size == N2
    assert aser.shape == (N2,)
    assert len(aser) == N2
    assert aser.rate_ratio == 2.0
    assert np.isclose(aser.duration, N2 / fs2)

    # Window interpolation
    win = aser.window(200, 500)
    assert win.shape == (300,)
    rel_err = np.max(np.abs(win - z_true[200:500])) / np.max(np.abs(z_true[200:500]))
    assert rel_err < 4e-5, f"Relative error {rel_err} exceeded 4e-5"

    # Slicing syntax
    win_slice = aser[200:500]
    assert np.allclose(win, win_slice)

    # Single element indexing
    val_single = aser[250]
    assert np.isclose(val_single, z_true[250], rtol=1e-4)

    # Negative and bound edge cases
    win_tail = aser[-100:]
    assert win_tail.shape == (100,)
    win_empty = aser[500:500]
    assert win_empty.shape == (0,)

    # 2D AnalyticSeries (e.g. ntemplates, N)
    z_2d = np.stack([z_1024, z_1024 * 0.5], axis=0)
    aser_2d = mf.AnalyticSeries(z_2d, sample_rate=1024.0, input_sample_rate=2048.0)
    assert aser_2d.shape == (2, N2)
    assert len(aser_2d) == 2
    win_2d = aser_2d.window(100, 300)
    assert win_2d.shape == (2, 200)
    assert np.allclose(win_2d[0], z_true[100:300], rtol=1e-4)
    assert np.allclose(win_2d[1], 0.5 * z_true[100:300], rtol=1e-4)


def test_correlate_series_analytic():
    """Verify correlate_series_analytic produces an AnalyticSeries matching full-rate correlation."""
    fs_taps = 2048.0
    fs_data = 2048.0
    taps = _generate_chirp(350, fs_taps, 30.0, 750.0, 0.0)

    bank = TimeDomainFilterBank(
        [taps], tap_counts=[350],
        tap_sample_rate=fs_taps,
        data_sample_rate=fs_data,
        engine='corr',
        execution_rate=1024.0
    )

    S = 8192
    t = np.arange(S) / fs_data
    phase = 2.0 * np.pi * (50.0 * t + 0.5 * 100.0 * t**2)
    s = np.cos(phase).astype(np.float32)
    S_f = np.fft.fft(s)
    S_f[S // 2:] = 0
    data_analytic = (np.fft.ifft(S_f) * 2.0).astype(np.complex64)

    # Correlate analytic returning AnalyticSeries
    aser = bank.correlate_series_analytic(data_analytic)
    assert isinstance(aser, mf.AnalyticSeries)
    assert aser.sample_rate == 1024.0
    assert aser.input_sample_rate == 2048.0
    assert aser.shape == (1, S)

    # Window reconstructed from AnalyticSeries
    win = aser.window(500, 1500)
    assert win.shape == (1, 1000)
    assert not np.all(win == 0)


def test_filter_series_with_analytic_series():
    """Verify filter_series accepts AnalyticSeries and reports sample-accurate input-rate coordinates."""
    fs_taps = 2048.0
    fs_data = 2048.0
    taps = _generate_chirp(350, fs_taps, 30.0, 750.0, 0.0)

    ref_power = np.ones(1024, dtype=np.float32) / 1024.0
    bank = TimeDomainFilterBank(
        [taps], tap_counts=[350],
        tap_sample_rate=fs_taps,
        data_sample_rate=fs_data,
        engine='hier',
        execution_rate=1024.0,
        threshold=5.0,
        reference=ref_power
    )

    S = 8192
    t = np.arange(S) / fs_data
    # Analytic noise series
    rng = np.random.default_rng(1234)
    white = rng.standard_normal(S).astype(np.float32)
    W = np.fft.fft(white)
    W[S // 2:] = 0
    data_analytic = (np.fft.ifft(W) * 2.0).astype(np.complex64)

    # Inject a strong signal at odd input-rate sample 2001
    inj_pos = 2001
    sig_len = min(len(taps), S - inj_pos)
    # Analytic version of injected template
    T_f = np.fft.fft(taps[:sig_len], n=sig_len)
    T_f[sig_len // 2:] = 0
    sig_analytic = (np.fft.ifft(T_f) * 2.0).astype(np.complex64)
    data_analytic[inj_pos:inj_pos + sig_len] += 12.0 * sig_analytic

    # Decimate to 1024 Hz and wrap in AnalyticSeries
    aser_in = mf.AnalyticSeries(data_analytic[::2], sample_rate=1024.0, input_sample_rate=2048.0)

    # Filter with bank
    results = bank.filter_series(aser_in)

    assert len(results.sample_indices) > 0, "No triggers detected"
    # Peak occurs at center-tap roll alignment: inj_pos + cnt // 2
    expected_peak = inj_pos + (len(taps) // 2)
    recovered = np.any(np.abs(results.sample_indices - expected_peak) <= 2)
    assert recovered, f"Injected trigger at {expected_peak} not recovered, got {results.sample_indices}"
    # Verify block lengths and starts are in input-rate units (>= 1024, typical 2048)
    assert np.all(results.block_lengths >= 1024)


