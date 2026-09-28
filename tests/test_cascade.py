import numpy as np
import pytest
import matchedfilter as mf
import matchedfilter._core as _core


def inspiral_power(n, exponent=-7 / 3.0, knee_frac=0.0150):
    p = np.zeros(n, dtype=np.float32)
    k = np.arange(1, n // 2).astype(np.float64)
    p[1:n // 2] = (k ** exponent / ((knee_frac * n / k) ** 4 + 1.0)).astype(np.float32)
    return p / p.sum()


def test_cascade_construction_and_config():
    n = 4096
    hmf_single = _core.HMF(n, 4, 16, 5.5, 0.01, 1024, 1, 8, 8)
    assert hmf_single.config() == (1024, 1, 8)

    hmf_cascade = _core.HMF(n, 4, 16, 5.5, 0.01, 1024, 1, 8, 8, 256)
    assert hmf_cascade.config() == (256, 1024, 1, 8)


def test_cascade_noise_rejection():
    n = 4096
    nd, nt = 8, 32
    # Thresholds calibrated for SNR=5.5, FDR<=0.1%
    # gamma0=3.7, gamma1=4.8
    hmf = _core.HMF(n, nd, nt, 5.5, 0.001, 1024, 1, 8, 8, 256)
    hmf.set_threshold(3.7, 4.8)

    power = inspiral_power(n)
    hmf.set_reference(power)

    rng = np.random.default_rng(123)
    # Pure noise
    noise_data = (rng.standard_normal((nd, n), dtype=np.float32) + 1j * rng.standard_normal((nd, n), dtype=np.float32))
    templates = np.sqrt(power)[None, :] * np.exp(2j * np.pi * rng.random((nt, n))).astype(np.complex64)

    for d in range(nd):
        hmf.set_data(d, noise_data[d])
    for t in range(nt):
        hmf.set_template(t, templates[t])

    peaks = np.empty((nd * nt, 1), dtype=mf.PEAK_DTYPE)
    cnts = np.empty(nd * nt, dtype=np.int32)
    empty_idx = np.empty(0, dtype=np.int64)
    empty_val = np.empty(0, dtype=np.complex64)
    mag = np.empty(0, dtype=np.float32)

    total_crossings = hmf.run(0, nd, 0, nt, n, 6.0, 0, n, empty_idx, empty_val, mag, cnts, peaks)
    pairs, triggers = hmf.stats()
    assert pairs == nd * nt
    # In pure noise at threshold 6.0, triggers escalating to fine should be very small
    assert triggers <= pairs * 0.15


def test_cascade_signal_at_threshold():
    """Verify that a signal exactly at the target SNR threshold is properly detected."""
    n = 4096
    nd, nt = 2, 4
    snr_target = 5.5
    hmf = _core.HMF(n, nd, nt, snr_target, 0.005, 1024, 1, 8, 8, 256)
    hmf.set_threshold(3.6, 4.8)

    power = inspiral_power(n)
    hmf.set_reference(power)

    h = np.sqrt(power).astype(np.complex64)
    # Matched filter templates must be conjugated
    h_conj = np.conj(h)
    for t in range(nt):
        hmf.set_template(t, h_conj)

    # Place a signal with intrinsic SNR = snr_target in data slot 0
    rng = np.random.default_rng(42)
    # Small noise to test clean detection
    noise = 0.1 * (rng.standard_normal((nd, n), dtype=np.float32) + 1j * rng.standard_normal((nd, n), dtype=np.float32))
    lag = n // 2
    phase_shift = np.exp(2j * np.pi * lag * np.arange(n) / n).astype(np.complex64)
    # Signal added in slot 0
    noise[0] += (snr_target * h * phase_shift).astype(np.complex64)

    for d in range(nd):
        hmf.set_data(d, noise[d])

    peaks = np.empty((nd * nt, 1), dtype=mf.PEAK_DTYPE)
    cnts = np.empty(nd * nt, dtype=np.int32)
    empty_idx = np.empty(0, dtype=np.int64)
    empty_val = np.empty(0, dtype=np.complex64)
    mag = np.empty(0, dtype=np.float32)

    # Run at detection threshold = 5.0
    hmf.run(0, nd, 0, nt, n, 5.0, 0, n, empty_idx, empty_val, mag, cnts, peaks)
    # Slot 0 template 0 should be detected!
    slot0_t0_peak = peaks[0, 0]
    assert slot0_t0_peak['index'] >= 0
    assert abs(slot0_t0_peak['value']) >= 5.0
    assert abs(slot0_t0_peak['index'] - lag) <= 2


def test_cascade_fdr_guarantee():
    """Verify that Two-Tier Cascade strictly maintains FDR <= target budget across signal injections."""
    n = 4096
    m0, m1 = 256, 1024
    snr_target = 5.5
    fdr_budget = 0.0020  # 0.20% budget for fast unit test
    # Calibrated gates with conservative safety margin
    gate_t0, gate_t1 = 3.58, 4.74

    power = inspiral_power(n)
    h_freq = np.sqrt(power).astype(np.complex64)
    h_conj = np.conj(h_freq)

    mf_full = mf.MatchedFilter(n, ndata=1, ntemplates=1)
    mf_full.set_templates(h_conj[None, :])

    hmf_cascade = _core.HMF(n, 1, 1, snr_target, fdr_budget, m1, 1, 8, 8, m0)
    hmf_cascade.set_reference(power)
    hmf_cascade.set_threshold(gate_t0, gate_t1)
    hmf_cascade.set_template(0, h_conj)

    p_single = np.empty((1, 1), dtype=mf.PEAK_DTYPE)
    cnt_buf = np.empty(1, dtype=np.int32)
    empty_idx = np.empty(0, dtype=np.int64)
    empty_val = np.empty(0, dtype=np.complex64)
    mag_buf = np.empty(0, dtype=np.float32)

    rng = np.random.default_rng(2026)
    n_trials = 4000
    n_fine_detections = 0
    missed_cascade = 0

    for _ in range(n_trials):
        lag = rng.integers(n // 4, 3 * n // 4)
        k = np.arange(n)
        phase_shift = np.exp(2j * np.pi * lag * k / n).astype(np.complex64)
        sig = (snr_target * h_freq * phase_shift).astype(np.complex64)
        noise = (rng.standard_normal(n, dtype=np.float32) + 1j * rng.standard_normal(n, dtype=np.float32))
        d = sig + noise

        mf_full.set_data(d[None, :])
        res_full = mf_full.run(binsize=n, threshold=snr_target)
        if abs(res_full['value'][0, 0, 0]) < snr_target:
            continue

        n_fine_detections += 1
        hmf_cascade.set_data(0, d)
        hmf_cascade.run(0, 1, 0, 1, n, snr_target, 0, n, empty_idx, empty_val, mag_buf, cnt_buf, p_single)
        if p_single[0, 0]['index'] < 0 or abs(p_single[0, 0]['value']) < snr_target:
            missed_cascade += 1

    measured_fdr = missed_cascade / n_fine_detections
    assert measured_fdr <= fdr_budget, (
        f"Measured FDR {measured_fdr*100:.3f}% exceeded budget {fdr_budget*100:.3f}%"
    )


def test_cascade_run_series():
    """Verify that ap_hmf_run_series functions correctly with a two-tier cascade."""
    n = 4096
    nt = 8
    hmf = _core.HMF(n, 8, nt, 5.5, 0.01, 1024, 1, 8, 8, 256)
    hmf.set_threshold(3.6, 4.8)

    power = inspiral_power(n)
    hmf.set_reference(power)
    h = np.sqrt(power).astype(np.complex64)
    h_conj = np.conj(h)
    for t in range(nt):
        hmf.set_template(t, h_conj)

    # 4 blocks in a continuous time series
    series_len = n * 4
    rng = np.random.default_rng(99)
    series = (rng.standard_normal(series_len) + 1j * rng.standard_normal(series_len)).astype(np.complex64)
    # Inject a loud signal in block 1 (offset n)
    lag = n // 3
    sig_time = np.fft.ifft(h) * float(n) * 10.0
    series[n + lag : n + lag + n] += sig_time[: min(n, series_len - (n + lag))]

    starts = np.array([0, n, 2 * n, 3 * n], dtype=np.uintp)
    win_start = np.zeros(4, dtype=np.uintp)
    win_end = np.full(4, n, dtype=np.uintp)

    peaks = np.empty((4 * nt, 1), dtype=mf.PEAK_DTYPE)
    cnts = np.empty(4 * nt, dtype=np.int32)
    empty_idx = np.empty(0, dtype=np.int64)
    empty_val = np.empty(0, dtype=np.complex64)
    mag = np.empty(0, dtype=np.float32)

    total_trig = hmf.run_series(series, starts, win_start, win_end, 0, nt, n, 5.0,
                                empty_idx, empty_val, mag, cnts, peaks)
    assert total_trig > 0
    # Block 1, template 0 should detect the injection
    row_block1_t0 = 1 * nt + 0
    pk = peaks[row_block1_t0, 0]
    assert pk['index'] >= 0
    assert abs(pk['value']) >= 5.0


def test_cascade_matches_single_tier_on_detections():
    """Verify that when a signal is detected, the peak location and complex SNR
    match between single-tier and two-tier cascade within floating-point roundoff."""
    n = 4096
    nd, nt = 1, 4
    hmf_single = _core.HMF(n, nd, nt, 5.5, 0.001, 1024, 1, 8, 8)
    hmf_cascade = _core.HMF(n, nd, nt, 5.5, 0.001, 1024, 1, 8, 8, 256)

    hmf_single.set_threshold(4.8)
    hmf_cascade.set_threshold(3.6, 4.8)

    power = inspiral_power(n)
    hmf_single.set_reference(power)
    hmf_cascade.set_reference(power)

    h = np.sqrt(power).astype(np.complex64)
    h_conj = np.conj(h)
    for t in range(nt):
        hmf_single.set_template(t, h_conj)
        hmf_cascade.set_template(t, h_conj)

    # Injected signal with SNR 7.5
    rng = np.random.default_rng(77)
    noise = 0.05 * (rng.standard_normal((nd, n), dtype=np.float32) + 1j * rng.standard_normal((nd, n), dtype=np.float32))
    lag = 1234
    phase_shift = np.exp(2j * np.pi * lag * np.arange(n) / n).astype(np.complex64)
    noise[0] += (7.5 * h * phase_shift).astype(np.complex64)

    hmf_single.set_data(0, noise[0])
    hmf_cascade.set_data(0, noise[0])

    peaks1 = np.empty((nd * nt, 1), dtype=mf.PEAK_DTYPE)
    peaks2 = np.empty((nd * nt, 1), dtype=mf.PEAK_DTYPE)
    cnts1 = np.empty(nd * nt, dtype=np.int32)
    cnts2 = np.empty(nd * nt, dtype=np.int32)
    empty_idx = np.empty(0, dtype=np.int64)
    empty_val = np.empty(0, dtype=np.complex64)
    mag = np.empty(0, dtype=np.float32)

    hmf_single.run(0, nd, 0, nt, n, 5.0, 0, n, empty_idx, empty_val, mag, cnts1, peaks1)
    hmf_cascade.run(0, nd, 0, nt, n, 5.0, 0, n, empty_idx, empty_val, mag, cnts2, peaks2)

    for i in range(nd * nt):
        p1 = peaks1[i, 0]
        p2 = peaks2[i, 0]
        assert p1['index'] == p2['index']
        np.testing.assert_allclose(p1['value'], p2['value'], rtol=1e-5, atol=1e-5)


def test_hierarchical_filter_cascade_python_api():
    """Verify that HierarchicalFilter accepts cascade_band and set_coarse_threshold((t0, t1))."""
    n = 4096
    power = inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)

    hf = mf.HierarchicalFilter(n, 2, 4, snr=5.5, fd=1e-3, band=1024, taps=8, cascade_band=256)
    hf.set_reference(power)
    hf.set_coarse_threshold((3.8, 4.8))
    hf.set_templates(np.repeat(np.conj(h)[None, :], 4, axis=0))

    rng = np.random.default_rng(42)
    noise = (rng.standard_normal((2, n)) + 1j * rng.standard_normal((2, n))).astype(np.complex64)
    hf.set_data(noise)

    peaks = hf.run(binsize=n, threshold=5.0)
    assert peaks.shape == (2, 4, 1)
    assert hf.refine_rate >= 0.0


