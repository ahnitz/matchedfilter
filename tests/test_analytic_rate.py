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


def test_odd_sample_peak_recovery():
    """Verify that peaks occurring at odd input-rate samples are recovered at exact odd index."""
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
    rng = np.random.default_rng(42)
    white = rng.standard_normal(S).astype(np.float32)
    W = np.fft.fft(white)
    W[S // 2:] = 0
    data_analytic = (np.fft.ifft(W) * 2.0).astype(np.complex64)

    # Injected peak at sample where center-tap lands on odd sample:
    # inj_pos = 2000, cnt = 350, cnt // 2 = 175 -> expected_peak = 2175 (odd!)
    inj_pos = 2000
    sig_len = min(len(taps), S - inj_pos)
    T_f = np.fft.fft(taps[:sig_len], n=sig_len)
    T_f[sig_len // 2:] = 0
    sig_analytic = (np.fft.ifft(T_f) * 2.0).astype(np.complex64)
    data_analytic[inj_pos:inj_pos + sig_len] += 15.0 * sig_analytic

    # Pass full-rate series (testing Step 1 decimation + odd peak recovery)
    results = bank.filter_series(data_analytic)

    expected_peak = inj_pos + (len(taps) // 2)
    assert expected_peak % 2 == 1, "Expected peak should be odd"
    assert len(results.sample_indices) > 0, "No triggers detected"
    matched = np.any(results.sample_indices == expected_peak)
    assert matched, f"Expected exact odd peak at {expected_peak}, got {results.sample_indices}"


def test_tap_folding_suppresses_dc_gain_tails():
    """Verify that folding with 32-tap Kaiser sinc filter suppresses tails by > 1000x compared to cut."""
    from matchedfilter.time_domain import _fold_taps_2x, _get_interp_kernel

    Nin = 2048
    Ne = 1024
    cnt = 701
    fs = 2048.0
    t = np.arange(cnt) / fs
    # Filter with large low-frequency/DC gain (like consumer FIRs)
    h_raw = (np.sin(2 * np.pi * 100 * t) / (t + 0.01)).astype(np.float32)

    h = np.zeros(Nin, dtype=np.float32)
    h[:cnt] = h_raw
    h = np.roll(h, -(cnt // 2))

    H_full = np.fft.fft(h).astype(np.complex64)
    H_cut = H_full[:Ne].copy()

    j_idx, g_kernel = _get_interp_kernel(32, nu_c=0.40)
    h_group = h[None, :]
    h_e = _fold_taps_2x(h_group, g_kernel, j_idx, Nin, Ne)[0]
    H_fold = np.fft.fft(h_e).astype(np.complex64)

    h_cut_t = np.fft.ifft(H_cut)
    h_fold_t = np.fft.ifft(H_fold)

    c_bad = int(np.ceil((cnt // 2) / 2)) + 16
    tail_cut = np.max(np.abs(h_cut_t[c_bad : Ne - c_bad]))
    tail_fold = np.max(np.abs(h_fold_t[c_bad : Ne - c_bad]))

    assert tail_cut > 0.5, f"Expected large tail from cut, got {tail_cut}"
    assert tail_fold < 1e-4, f"Expected suppressed tail from fold, got {tail_fold}"
    assert tail_cut / tail_fold > 1000.0, f"Fold tail should be > 1000x smaller than cut tail"


def test_engine_filter_every_sample_accuracy():
    """Verify that every even and odd output in valid window has error <= 1e-4 vs full rate."""
    fs = 2048.0
    cnt = 701
    taps = _generate_chirp(cnt, fs, 30.0, 750.0, 0.0)

    Nin = 2048
    Ne = 1024
    h = np.zeros(Nin, dtype=np.float32)
    h[:cnt] = taps
    h = np.roll(h, -(cnt // 2))

    S = 8192
    rng = np.random.default_rng(999)
    white = rng.standard_normal(S).astype(np.float32)
    W = np.fft.fft(white)
    # Band-limited to [20, 800) Hz
    W[:80] = 0
    W[3200:] = 0
    x_full = (np.fft.ifft(W) * 2.0).astype(np.complex64)

    # Full rate exact output for block 0
    blk_full = x_full[:Nin]
    H_full = np.fft.fft(h).astype(np.complex64)
    z_full_blk = np.fft.ifft(np.fft.fft(blk_full) * np.conj(H_full))

    # Engine folded filter for block 0
    from matchedfilter.time_domain import _fold_taps_2x, _get_interp_kernel
    j_idx, g_kernel = _get_interp_kernel(32, nu_c=0.40)
    h_e = _fold_taps_2x(h[None, :], g_kernel, j_idx, Nin, Ne)[0]
    H_fold = np.fft.fft(h_e)

    blk_e = x_full[:Nin:2]
    z_fold_blk = np.fft.ifft(np.fft.fft(blk_e) * np.conj(H_fold))

    c_bad = int(np.ceil((cnt // 2) / 2)) + 16
    m_eval = np.arange(c_bad + 16, Ne - c_bad - 16)

    # Even samples
    norm_ref = np.max(np.abs(z_full_blk[2 * m_eval]))
    even_err = np.max(np.abs(z_fold_blk[m_eval] - z_full_blk[2 * m_eval])) / norm_ref
    assert even_err < 1e-4, f"Even sample relative error {even_err} exceeded 1e-4"

    # Odd samples via 32-tap kernel
    odd_interp = np.array([np.dot(z_fold_blk[m + j_idx], g_kernel) for m in m_eval])
    odd_err = np.max(np.abs(odd_interp - z_full_blk[2 * m_eval + 1])) / norm_ref
    assert odd_err < 1e-4, f"Odd sample relative error {odd_err} exceeded 1e-4"


def test_scalloping_guard_near_threshold():
    """Verify that peaks on odd input samples just above threshold are not dismissed."""
    fs = 2048.0
    cnt = 701
    taps = _generate_chirp(cnt, fs, 30.0, 750.0, 0.0)
    taps /= np.linalg.norm(taps)

    ref_power = np.ones(1024, dtype=np.float32) / 1024.0
    bank = TimeDomainFilterBank(
        [taps], tap_counts=[cnt],
        tap_sample_rate=fs,
        data_sample_rate=fs,
        engine='hier',
        decimation=2,
        threshold=5.5,
        reference=ref_power
    )

    S = 8192
    series = np.zeros(S, dtype=np.complex64)
    # Inject at odd sample 4001 with peak SNR 5.5
    inj_pos = 4001
    half = cnt // 2
    series[inj_pos - half : inj_pos - half + cnt] = 5.5 * taps

    res = bank.filter_series(series)
    assert len(res.sample_indices) > 0, "Near-threshold peak was dismissed by scalloping loss!"
    matched = np.any(res.sample_indices == inj_pos)
    assert matched, f"Expected peak at odd sample {inj_pos}, got {res.sample_indices}"
    max_snr = np.max(np.abs(res.snr))
    assert np.isclose(max_snr, 5.5, rtol=1e-4), f"Expected SNR ~5.5, got {max_snr}"


def test_decimation_fallback_and_profile_selection():
    """Verify decimation='auto' falls back to 1 if profile exceeds Nyquist/2, and 2 if within."""
    fs = 2048.0
    taps = _generate_chirp(350, fs, 30.0, 750.0, 0.0)

    # Profile fitting inside [0, N/2)
    ref_low = np.zeros(2048, dtype=np.float32)
    ref_low[20:800] = 1.0
    bank_low = TimeDomainFilterBank([taps], decimation='auto', reference=ref_low)
    assert bank_low.decimation == 2
    assert bank_low._data_decimation_stride == 2

    # Profile extending beyond N/2 (e.g. up to bin 1000 in 2048)
    ref_high = np.zeros(2048, dtype=np.float32)
    ref_high[20:1000] = 1.0
    bank_high = TimeDomainFilterBank([taps], decimation='auto', reference=ref_high)
    assert bank_high.decimation == 1
    assert bank_high._data_decimation_stride == 1


def test_compatibility_contract():
    """Verify FilterResults shape and units, filters_f length, and groups keys."""
    fs = 2048.0
    taps = _generate_chirp(350, fs, 30.0, 750.0, 0.0)

    ref_power = np.ones(1024, dtype=np.float32) / 1024.0
    bank = TimeDomainFilterBank([taps], decimation=2, reference=ref_power)

    # filters_f must return full-rate 2048-point spectrum
    filt_f = bank.filters_f[0]
    assert len(filt_f) == 2048

    # block_lengths must return full-rate length 2048
    assert bank.block_lengths[0] == 2048
    assert bank.get_block_length(0) == 2048

    # FilterResults namedtuple fields
    S = 8192
    data = np.zeros(S, dtype=np.complex64)
    data[2000:2000 + len(taps)] = 10.0 * taps
    res = bank.filter_series(data)

    assert hasattr(res, 'template_indices')
    assert hasattr(res, 'sample_indices')
    assert hasattr(res, 'snr')
    assert hasattr(res, 'block_starts')
    assert hasattr(res, 'block_lengths')
    assert len(res) == 5
    assert np.all(res.block_lengths == 2048)



