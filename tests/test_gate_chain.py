import os
import numpy as np
import pytest
import matchedfilter as mf
from matchedfilter import _calibration
import matchedfilter._core as _core


def inspiral_power(n, exponent=-7 / 3.0, knee_frac=0.0150):
    p = np.zeros(n, dtype=np.float32)
    k = np.arange(1, n // 2).astype(np.float64)
    p[1:n // 2] = (k ** exponent / ((knee_frac * n / k) ** 4 + 1.0)).astype(np.float32)
    return p / p.sum()


def _poisson_upper(mean, alpha):
    """Smallest k with P(X > k) < alpha for X ~ Poisson(mean)."""
    import math
    k, term = 0, math.exp(-mean)
    cdf = term
    while 1.0 - cdf >= alpha:
        k += 1
        term *= mean / k
        cdf += term
    return k


def test_cascade_construction_and_config():
    n = 4096
    hmf_single = _core.HMF(n, 4, 16, [1024], 8)
    assert hmf_single.chain() == (1024,)

    hmf_cascade = _core.HMF(n, 4, 16, [256, 1024], 8)
    assert hmf_cascade.chain() == (256, 1024)


def test_cascade_noise_rejection():
    n = 4096
    nd, nt = 8, 32
    # Thresholds calibrated for SNR=5.5, FDR<=0.1%
    # gamma0=3.7, gamma1=4.8
    hmf = _core.HMF(n, nd, nt, [256, 1024], 8)
    hmf.set_thresholds([3.7, 4.8])

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
    hmf = _core.HMF(n, nd, nt, [256, 1024], 8)
    hmf.set_thresholds([3.6, 4.8])

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
    power = inspiral_power(n)
    plan = mf._gatechain.chain_thresholds(power, n, snr_target, fdr_budget, (m0, m1))
    assert plan is not None
    gate_t0, gate_t1 = plan["thresholds"]

    h_freq = np.sqrt(power).astype(np.complex64)
    h_conj = np.conj(h_freq)

    mf_full = mf.MatchedFilter(n, ndata=1, ntemplates=1)
    mf_full.set_templates(h_conj[None, :])

    hmf_cascade = _core.HMF(n, 1, 1, [m0, m1], 8)
    hmf_cascade.set_reference(power)
    hmf_cascade.set_thresholds([gate_t0, gate_t1])
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

    # The model places the gates AT the budget, so a finite sample exceeds it about half the
    # time. Test what the guarantee says: misses are not significantly above budget.
    expected = fdr_budget * n_fine_detections
    assert missed_cascade <= _poisson_upper(expected, 1e-3), (
        f"{missed_cascade} misses in {n_fine_detections} detections is significantly above "
        f"the {fdr_budget*100:.2f}% budget (expected {expected:.1f})")


def test_cascade_run_series():
    """Verify that ap_hmf_run_series functions correctly with a two-tier cascade."""
    n = 4096
    nt = 8
    hmf = _core.HMF(n, 8, nt, [256, 1024], 8)
    hmf.set_thresholds([3.6, 4.8])

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
    hmf_single = _core.HMF(n, nd, nt, [1024], 8)
    hmf_cascade = _core.HMF(n, nd, nt, [256, 1024], 8)

    hmf_single.set_thresholds([4.8])
    hmf_cascade.set_thresholds([3.6, 4.8])

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
    """HierarchicalFilter accepts a pinned two-tier chain and one threshold per tier."""
    n = 4096
    power = inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)

    hf = mf.HierarchicalFilter(n, 2, 4, snr=5.5, fd=1e-3, chain=(256, 1024))
    hf.set_reference(power)
    hf.set_coarse_threshold((3.8, 4.8))
    hf.set_templates(np.repeat(np.conj(h)[None, :], 4, axis=0))

    rng = np.random.default_rng(42)
    noise = (rng.standard_normal((2, n)) + 1j * rng.standard_normal((2, n))).astype(np.complex64)
    hf.set_data(noise)

    peaks = hf.run(binsize=n, threshold=5.0)
    assert peaks.shape == (2, 4, 1)
    assert hf.refine_rate >= 0.0


def test_chain_thresholds_per_tier():
    """The model gives one gate per tier, inside sane ranges; invalid chains are refused."""
    n = 4096
    power = inspiral_power(n)
    for chain in ((1024,), (256, 1024), (128, 512, 1024)):
        plan = mf._gatechain.chain_thresholds(power, n, 5.5, 1e-3, chain)
        assert plan is not None and len(plan["thresholds"]) == len(chain)
        assert all(1.0 <= g <= 5.5 for g in plan["thresholds"])
    g0, g1 = mf._gatechain.chain_thresholds(power, n, 5.5, 1e-3, (256, 1024))["thresholds"]
    assert 2.5 <= g0 <= 4.5 and 4.0 <= g1 <= 5.5
    for bad in ((1024, 256), (512, 512), (32,), (4096,), (300,), ()):
        with pytest.raises(ValueError):
            mf.HierarchicalFilter(n, chain=bad)


def test_hierarchical_filter_auto_cascade():
    """Verify HierarchicalFilter with cascade=True chooses cascade configuration and derives thresholds."""
    n = 4096
    power = inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)

    hf = mf.HierarchicalFilter(n, 2, 4, snr=5.5, fd=1e-3)
    hf.set_reference(power)
    hf.set_templates(np.repeat(np.conj(h)[None, :], 4, axis=0))

    rng = np.random.default_rng(99)
    noise = (rng.standard_normal((2, n)) + 1j * rng.standard_normal((2, n))).astype(np.complex64)
    # Add strong injection in pair (0, 0)
    noise[0] += (8.0 * h).astype(np.complex64)
    hf.set_data(noise)

    peaks = hf.run(binsize=n, threshold=5.0)
    assert peaks.shape == (2, 4, 1)
    # Strong signal should be detected
    assert peaks[0, 0, 0]['index'] >= 0
    assert abs(peaks[0, 0, 0]['value']) >= 7.0
    assert hf.refine_rate >= 0.0


def test_hierarchical_filter_explicit_cascade_band_auto_threshold():
    """Verify HierarchicalFilter with explicit cascade_band derives dual thresholds automatically from reference."""
    n = 4096
    power = inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)

    # band=1024, cascade_band=256, no set_coarse_threshold call
    hf = mf.HierarchicalFilter(n, 1, 2, snr=5.5, fd=1e-3, chain=(256, 1024))
    hf.set_reference(power)
    hf.set_templates(np.repeat(np.conj(h)[None, :], 2, axis=0))

    rng = np.random.default_rng(101)
    noise = (rng.standard_normal((1, n)) + 1j * rng.standard_normal((1, n))).astype(np.complex64)
    noise[0] += (9.0 * h).astype(np.complex64)
    hf.set_data(noise)

    peaks = hf.run(binsize=n, threshold=5.0)
    assert peaks[0, 0, 0]['index'] >= 0
    assert abs(peaks[0, 0, 0]['value']) >= 7.0


def test_cascade_signal_retention_and_scalloping():
    """Verify signal retention at high SNR across discrete and fractional lag offsets.

    Guarantees no false dismissal dropouts from lag-grid scalloping losses
    (specifically validating SNR 5.985 at band 512, as well as SNR 6.5, 7.5).
    """
    n = 4096
    m0, m1 = 256, 512
    power = inspiral_power(n)
    h_freq = np.sqrt(power).astype(np.complex64)
    h_conj = np.conj(h_freq)

    # Dynamically derive calibrated gates with tolerance bound
    plan = mf._gatechain.chain_thresholds(power, n, 5.5, 0.001, (m0, m1))
    assert plan is not None
    g0, g1 = plan["thresholds"]

    hmf = _core.HMF(n, 1, 1, [m0, m1], 8)
    hmf.set_reference(power)
    hmf.set_thresholds([g0, g1])
    hmf.set_template(0, h_conj)

    p_cascade = np.empty((1, 1), dtype=mf.PEAK_DTYPE)
    cnt_buf = np.empty(1, dtype=np.int32)
    empty_idx = np.empty(0, dtype=np.int64)
    empty_val = np.empty(0, dtype=np.complex64)
    mag_buf = np.empty(0, dtype=np.float32)

    # Test signals at SNR 5.985 (reported scalloping telemetry deficit) and SNR 6.5, 7.5
    for snr_test in (5.985, 6.5, 7.5):
        # Sample across sub-sample fractional offsets to exercise peak scalloping
        for frac in (0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875):
            for base_lag in (500, 1024, 2048):
                lag = base_lag + frac
                k = np.arange(n)
                phase_shift = np.exp(2j * np.pi * lag * k / n).astype(np.complex64)
                sig = (snr_test * h_freq * phase_shift).astype(np.complex64)
                hmf.set_data(0, sig)
                hmf.run(0, 1, 0, 1, n, 5.5, 0, n, empty_idx, empty_val, mag_buf, cnt_buf, p_cascade)

                peak_idx = p_cascade[0, 0]["index"]
                peak_val = abs(p_cascade[0, 0]["value"])
                assert peak_idx >= 0, f"Signal lost at SNR {snr_test}, lag {lag}"
                assert peak_val >= 5.5, f"Peak {peak_val:.3f} below 5.5 at SNR {snr_test}, lag {lag}"

    # Explicit reproduction test under noise:
    # A signal at SNR 5.985 at the worst-case scalloping trough (offset = 4.0 samples on m1=512)
    # suffers a 0.711 SNR scalloping loss (noiseless peak drops from 5.736 to 5.025).
    # Under old hardcoded/unmargined gate (g1=4.740), negative noise fluctuations caused
    # a 3.2% - 3.6% false dismissal rate on signals detected by the full un-decimated filter.
    # We verify that under the calibrated gate (g1=4.202), 0 misses occur across noisy trials.
    worst_lag = 1024 + 4.0
    phase_shift = np.exp(2j * np.pi * worst_lag * k / n).astype(np.complex64)
    sig_scallop = (5.985 * h_freq * phase_shift).astype(np.complex64)

    mf_full = mf.MatchedFilter(n, ndata=1, ntemplates=1)
    mf_full.set_templates(h_conj[None, :])

    rng = np.random.default_rng(42)
    detected_full = 0
    missed_cascade = 0
    for _ in range(150):
        noise = (rng.standard_normal(n, dtype=np.float32) + 1j * rng.standard_normal(n, dtype=np.float32))
        d = sig_scallop + noise
        mf_full.set_data(d[None, :])
        res = mf_full.run(binsize=n, threshold=5.5)
        if abs(res['value'][0, 0, 0]) < 5.5:
            continue
        detected_full += 1

        hmf.set_data(0, d)
        hmf.run(0, 1, 0, 1, n, 5.5, 0, n, empty_idx, empty_val, mag_buf, cnt_buf, p_cascade)
        if p_cascade[0, 0]['index'] < 0 or abs(p_cascade[0, 0]['value']) < 5.5:
            missed_cascade += 1

    assert detected_full >= 100, f"Expected >= 100 detections, got {detected_full}"
    assert missed_cascade == 0, (
        f"Cascade missed {missed_cascade} / {detected_full} detections at worst-case scalloping trough"
    )


def test_a_cascades_first_gate_is_looser_than_the_single_tier_gate():
    """A two-tier cascade's first gate is looser than the single-tier gate at its last band.

    (Within one plan the survivors nest, tier by tier -- tested on the engine's own counters
    in test_gate_chain's tier_stats test.)

    Cross-Configuration Non-Subset Behavior:
      Across distinct configurations (e.g. two-tier cascade vs single-tier filter,
      or differing bands), the detected triggers are NOT subsets of each other.
      Because Tier 0 operates with a looser gate (e.g. g0 ~ 3.68 vs g_single ~ 4.83)
      and different frequency decimation, marginal triggers near threshold can be
      gained (passed looser Tier 0) or lost (marginal phase/noise difference).
      Cross-configuration subset behavior is neither expected nor mathematically
      required; each configuration independently guarantees compound FDR <= fd.
    """
    n = 4096
    m0, m1 = 256, 1024
    snr_target = 5.5
    fd_target = 0.001
    power = inspiral_power(n)
    h_freq = np.sqrt(power).astype(np.complex64)

    plan = mf._gatechain.chain_thresholds(power, n, snr_target, fd_target, (m0, m1))
    assert plan is not None
    g0, g1 = plan["thresholds"]
    g_single = float(mf.choose_threshold(power, n, snr_target, fd_target, band=m1))

    # Cross-configuration: Tier 0 gate is strictly looser than single-tier gate
    assert g0 < g_single, f"Tier 0 gate {g0:.3f} should be looser than single gate {g_single:.3f}"


def test_performance_tracking_and_summary():
    """Verify lightweight performance self-tracking, docstring retention, and bounded timing history."""
    assert mf.MatchedFilter.run.__doc__ is not None
    assert "structured array" in mf.MatchedFilter.run.__doc__
    n = 2048
    f = mf.MatchedFilter(n, ndata=2, ntemplates=2)
    assert f.performance_stats["total_calls"] == 0
    assert f.performance_stats["total_time_s"] == 0.0

    d = np.zeros((2, n), dtype=np.complex64)
    h = np.zeros((2, n), dtype=np.complex64)
    f.set_data(d)
    f.set_templates(h)

    f.run(threshold=0.0)
    f.run(threshold=0.0)

    summary = f.performance_summary()
    assert summary["total_calls"] == 2
    assert summary["timed_calls"] == 2
    assert summary["sampled_calls"] == 2
    assert summary["total_time_s"] > 0.0
    assert summary["min_batch_time_ms"] > 0.0
    assert summary["max_batch_time_ms"] >= summary["min_batch_time_ms"]
    assert summary["median_batch_time_ms"] >= summary["min_batch_time_ms"]
    assert summary["mean_batch_time_ms"] >= summary["min_batch_time_ms"]
    assert "device" in summary
    assert "backend" in summary
    assert f.performance_info == summary

    for _ in range(300):
        f._record_batch_time(0.001)
    assert len(f.performance_stats["batch_times_ms"]) == mf.MatchedFilter._MAX_BATCH_TIMINGS
    assert f.performance_summary()["total_calls"] == 302



def test_pinned_chain_is_reproducible_without_tuning():
    """A pinned chain never trials or switches."""
    n = 4096
    power = inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)
    hf = mf.HierarchicalFilter(n, 1, 2, snr=5.5, fd=1e-3, chain=(256, 1024))
    assert hf.autotune_info["status"] == "pinned" and hf.config == (256, 1024)
    hf.set_reference(power)
    hf.set_templates(np.repeat(np.conj(h)[None, :], 2, axis=0))
    rng = np.random.default_rng(88)
    hf.set_data((rng.standard_normal((1, n)) + 1j * rng.standard_normal((1, n))).astype(np.complex64))
    assert hf.run(binsize=n, threshold=5.0).shape == (1, 2, 1)
    assert hf.autotune_info["status"] == "pinned" and hf.config == (256, 1024)


def _bank_case(n, nt, nd, seed):
    power = inspiral_power(n)
    rng = np.random.default_rng(seed)
    H = (np.sqrt(power) * np.exp(2j * np.pi * rng.random((nt, n)))).astype(np.complex64)
    H /= np.sqrt((np.abs(H) ** 2).sum(axis=1, keepdims=True))
    D = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    k = np.arange(n)
    for d in range(0, nd, 3):                     # some loud events so refines happen
        D[d] += (9.0 * np.conj(H[d % nt]) * np.exp(2j * np.pi * (300 + 37 * d) * k / n)).astype(np.complex64)
    return power, np.conj(H), D


@pytest.mark.parametrize("chain", [(256,), (128, 512), (128, 256, 1024)])
def test_every_reported_peak_is_exact(chain):
    """Any chain length: every peak it reports is the flat filter's peak, bit for bit."""
    n, nt, nd = 4096, 8, 12
    power, H, D = _bank_case(n, nt, nd, 5)
    flat = mf.MatchedFilter(n, nd, nt)
    flat.set_templates(H); flat.set_data(D)
    a = flat.run(binsize=n, threshold=5.0).copy()
    hf = mf.HierarchicalFilter(n, nd, nt, snr=5.5, fd=1e-3, chain=chain)
    hf.set_reference(power); hf.set_templates(H); hf.set_data(D)
    b = hf.run(binsize=n, threshold=5.0).copy()
    hit = b["index"] >= 0
    assert hit.sum() > 0
    np.testing.assert_array_equal(b["index"][hit], a["index"][hit])
    np.testing.assert_array_equal(b["value"][hit], a["value"][hit])
    # survivors nest: each tier passes no more pairs than the one before, and the refine sees the last tier's
    ts = hf.tier_stats
    passed = [t[1] for t in ts[:-1]]
    assert all(x >= y for x, y in zip(passed, passed[1:])) and ts[-1][1] == passed[-1]


def test_o2_noise_curve_prefers_a_multi_tier_chain():
    """On a real O2 reference (poor low-frequency sensitivity) no single coarse band is a good
    gate, and the model ranks two-tier chains first -- the case the cascade lock used to hide."""
    from pathlib import Path
    p = np.load(Path(__file__).parent / "data" / "reference_profile_o2_h1l1_2048.npy")
    gc = mf._gatechain
    best, plans = gc.choose_chain(p, 2048, 6.0, 1e-3, cost=_recorded_model(), max_tiers=2,
                                  window=(150, 1898))
    assert best is not None and len(best["chain"]) == 2, [(q["chain"], round(q["cost"])) for q in plans[:5]]


def test_autotune_off_keeps_the_model_choice(monkeypatch):
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    mf.clear_autotune_cache()
    n = 4096
    power, H, D = _bank_case(n, 8, 4, 9)
    hf = mf.HierarchicalFilter(n, 4, 8, snr=5.5, fd=1e-3)
    hf.set_reference(power); hf.set_templates(H); hf.set_data(D)
    hf.run(binsize=n, threshold=5.0)
    assert hf.autotune_info["status"] == "model"
    assert hf.config == hf.autotune_info["model"]


def test_trials_lock_one_winner_and_every_plan_switches(monkeypatch):
    """Close calls are measured: standalone plans of one key pool paired rounds into one joint
    trial (every arm on the same call), which locks within its cap; every plan then runs the
    winning arm, resolved against its own model choice."""
    monkeypatch.setenv("MF_AUTOTUNE", "1")
    monkeypatch.setenv("MF_TRIAL_ROUNDS", "2")
    mf.clear_autotune_cache()
    n, nt = 4096, 8
    power, H, _ = _bank_case(n, nt, 1, 11)
    rng = np.random.default_rng(3)
    ser = (rng.standard_normal(n * 9) + 1j * rng.standard_normal(n * 9)).astype(np.complex64)
    starts = (np.arange(8) * n).astype(np.uintp)
    ws = np.zeros(8, np.uintp); we = np.full(8, n, np.uintp)
    plans = []
    for _ in range(4):
        hf = mf.HierarchicalFilter(n, 1, nt, snr=5.5, fd=1e-3)
        hf.set_reference(power); hf.set_templates(H)
        plans.append(hf)
    for _ in range(2 * 2 + 1):                      # at most the cap of rounds, one per call
        for p in plans:
            p.run_series(ser, starts, ws, we, binsize=n, threshold=6.0)
    trials = list(mf.get_autotune_state()["trials"].values())
    if not trials:
        pytest.skip("no Q15 screen for this chain here: a plan has one arm, so no trial")
    (trial,) = trials
    assert len(trial["arms"]) > 1 and trial["winner"] in trial["arms"]
    for p in plans:
        p.run_series(ser, starts, ws, we, binsize=n, threshold=6.0)     # adopts the lock
        assert p.autotune_info["status"] == "locked" and p._arm == trial["winner"]
        assert tuple(p.config) == p.arm_config(trial["winner"])[0]


def _recorded_model():
    """A cost model measured once (tests/data/cost_model_2048_zen5.json): tests that rank
    chains or compare costs use it, so their outcome is not this machine's timing."""
    import json
    from pathlib import Path
    rec = json.loads((Path(__file__).parent / "data" / "cost_model_2048_zen5.json").read_text())
    return mf._gatechain.CostModel.from_dict(rec["model"])


def test_cost_calibration_is_sane():
    """A live calibration's structure (every band priced, finite and positive); the cost
    relations are checked on the recorded model, not on this host's timing."""
    cm = _calibration.calibrate_costs(2048, 32)
    assert set(cm.dense) >= {64, 128, 256, 512, 1024}
    assert all(np.isfinite(v) and v > 0 for v in cm.dense.values())
    assert np.isfinite(cm.refine(0.05)) and cm.refine(0.05) > 0
    rec = _recorded_model()
    assert rec.dense[64] < rec.dense[1024]             # wider first tiers cost more per pair
    assert rec.refine(0.05) > rec.dense[256]           # a refine costs more than a coarse evaluation


def test_cost_file_reproduces_the_measured_models(monkeypatch, tmp_path):
    gc = mf._gatechain
    path = tmp_path / "costs.json"
    monkeypatch.setenv("MF_COST_FILE", str(path))
    monkeypatch.setattr(gc, "_COSTS", {})
    measured = _calibration.calibrate_costs(1024, 24)
    assert path.exists()
    monkeypatch.setattr(gc, "_COSTS", {})
    monkeypatch.setattr(gc.np.random, "default_rng", None)    # a reload must not measure
    loaded = _calibration.calibrate_costs(1024, 24)
    assert loaded.to_dict() == measured.to_dict()
    reach = [1.0, 0.05, 0.01]
    assert loaded.chain_cost((128, 512), reach) == measured.chain_cost((128, 512), reach)


def _plan_chain_bruteforce(sig, noise, bands, chain, fd, cost, n, snr):
    """The split search done the plain way: mask and sort every kept draw for each candidate
    (each draw's coarse maxima over the window, as plan_chain)."""
    import math
    gc = mf._gatechain
    cols = [bands.index(b) for b in chain]
    S = gc.kept_draws(sig, bands, chain, snr)
    M, k = S.shape[0], len(chain)
    K = int(math.floor(fd * M)) if k == 1 else int(math.floor(fd * M - 1.645 * math.sqrt(M * fd * (1 - fd))))
    if K < 8:
        return None
    sorted_cols = [np.sort(S[:, i]) for i in range(k - 1)]
    cands = []

    def rec(i, prefix, remaining):
        if i == k - 1:
            alive = np.ones(M, bool)
            for j, g in enumerate(prefix):
                alive &= S[:, j] >= g
            rem = K - (M - int(alive.sum()))
            last = np.sort(S[alive, k - 1])
            if 0 <= rem < len(last):
                cands.append(list(prefix) + [float(last[rem])])
            return
        for a in (gc._SPLIT if k <= 2 else gc._SPLIT_COARSE):
            share = a * remaining
            idx = int(math.floor(share * K))
            if idx >= 1:
                rec(i + 1, prefix + [float(sorted_cols[i][idx])], remaining - share)
    rec(0, [], 1.0)
    best = None
    for th in cands:
        reach = gc._reach(noise, cols, th)
        c = cost.chain_cost(chain, reach)
        if best is None or c < best["cost"]:
            best = dict(thresholds=tuple(th), reach=tuple(reach), cost=float(c))
    return best


def test_plan_chain_matches_the_plain_split_search():
    gc = mf._gatechain
    prof = np.load(os.path.join(os.path.dirname(__file__), "data", "reference_profile_o2_h1l1_2048.npy"))
    n = 2048
    cm = _calibration.calibrate_costs(n, 32)
    bands = gc.usable_bands(prof, n)
    sig = gc.signal_draws(prof, n, bands, 6.0, gc._gm._nsamp_for(1e-3), window=(192, n - 192))
    noise = gc.noise_block_maxima(prof, n, bands, window=(192, n - 192))
    for chain in gc.enumerate_chains(n, 3, bands=bands):
        fast = gc.plan_chain(sig, noise, bands, list(chain), 1e-3, cm, n, 6.0)
        ref = _plan_chain_bruteforce(sig, noise, bands, list(chain), 1e-3, cm, n, 6.0)
        assert (fast is None) == (ref is None), chain
        if fast is not None:
            assert fast["thresholds"] == ref["thresholds"] and fast["reach"] == ref["reach"], chain
            assert fast["cost"] == ref["cost"], chain


def test_choice_cache_keys_on_cost_content_not_identity(monkeypatch):
    """A new cost model must not inherit cached choices of an old one that happened to share its id."""
    gc = mf._gatechain
    prof = np.load(os.path.join(os.path.dirname(__file__), "data", "reference_profile_o2_h1l1_2048.npy"))
    cm = _calibration.calibrate_costs(2048, 32)
    d = cm.to_dict()
    cheap_refine = gc.CostModel.from_dict(dict(d, refine=[(f, v * 1e-3) for f, v in d["refine"]]))
    dear_refine = gc.CostModel.from_dict(dict(d, refine=[(f, v * 1e3) for f, v in d["refine"]]))
    a, _ = gc.choose_chain(prof, 2048, 6.0, 1e-3, cost=cheap_refine, window=(192, 1856))
    b, _ = gc.choose_chain(prof, 2048, 6.0, 1e-3, cost=dear_refine, window=(192, 1856))
    assert a["cost"] != b["cost"]
    same = gc.CostModel.from_dict(dear_refine.to_dict())
    assert gc.choose_chain(prof, 2048, 6.0, 1e-3, cost=same, window=(192, 1856))[0] is b   # content hit


def test_bounding_first_tier_excess_is_priced():
    """A first tier that reports a bound passes extra pairs; the model charges the next stage."""
    gc = mf._gatechain
    dense = {256: 10.0, 512: 30.0}
    sparse = {256: [(0.01, 40.0), (0.1, 35.0)], 512: [(0.01, 60.0), (0.1, 50.0)]}
    refine = [(0.01, 1000.0), (0.1, 900.0)]
    plain = gc.CostModel(2048, dense, sparse, refine)
    bound = gc.CostModel(2048, dense, sparse, refine,
                         excess={256: [(0.01, 0.0108), (0.1, 0.105)]})
    assert plain.pass_excess(256, 0.02) == 1.0
    assert 1.05 < bound.pass_excess(256, 0.02) < 1.08
    assert bound.pass_excess(512, 0.02) == 1.0          # no row for this band
    reach = [1.0, 0.02, 0.002]
    extra = bound.chain_cost((256, 512), reach) - plain.chain_cost((256, 512), reach)
    r1 = 0.02 * bound.pass_excess(256, 0.02)
    assert extra == pytest.approx(r1 * plain.sparse(512, r1) - 0.02 * plain.sparse(512, 0.02))
    assert extra > 0
    import json
    rt = gc.CostModel.from_dict(json.loads(json.dumps(bound.to_dict())))
    assert rt.signature() == bound.signature()


def test_gpu_gate_kind_keys(monkeypatch):
    gc = mf._gatechain
    monkeypatch.setattr(gc, "_is_gpu", lambda d: d.startswith("gpu"))
    monkeypatch.delenv("MF_COARSE_RAW", raising=False)
    assert gc.gpu_gate_kind("gpu:0") == "c16b"
    assert gc.gpu_gate_kind("cpu") == "f32"
    monkeypatch.setenv("MF_COARSE_RAW", "1")
    assert gc.gpu_gate_kind("gpu:0") == "f32"


def test_the_band_forward_is_priced_on_gpus_only():
    """Every GPU backend can claim its forward; a CPU never does (its device has a backend
    name too, AVX2/AVX3, which the pricing once took for a GPU's)."""
    gc = mf._gatechain
    assert gc._is_gpu("cpu") is False


def test_a_tier_that_passes_most_pairs_is_never_chosen():
    """A first tier with almost none of the profile's power cannot gate; choice must skip it."""
    gc = mf._gatechain
    n = 2048
    f = np.arange(n, dtype=float)
    power = np.where((f >= 60) & (f < 900), np.maximum(f, 1.0) ** (-7.0 / 3), 0.0)
    power[:60] = 1e-9 * power[60]                       # band 64 holds ~nothing
    best, plans = gc.choose_chain(power, n, 6.0, 1e-3, max_tiers=2)
    assert best is not None
    for q in plans:
        assert all(r <= gc._USELESS_PASS for r in q["reach"][1:len(q["chain"])]), q


def test_ties_break_deterministically():
    gc = mf._gatechain
    items = [((256, 1024), 100.0), ((256, 512), 101.0), ((512,), 120.0)]
    for perm in (items, items[::-1], items[1:] + items[:1]):
        got = gc.pick_stable(perm, lambda x: x[1], lambda x: gc.canonical_order(x[0]))
        assert got[0] == (256, 512)                     # tied with the cheapest; canonical first
    assert gc.pick_stable(items, lambda x: x[1] if x[0] != (512,) else 10.0,
                          lambda x: gc.canonical_order(x[0]))[0] == (512,)


def test_legacy_host_costs_do_not_change_chain_ranking():
    import json
    gc = mf._gatechain
    cm = gc.CostModel(
        2048, {256: 10.0, 512: 18.0}, {512: [(0.01, 20.0), (0.1, 18.0)]},
        [(0.001, 100.0), (0.01, 80.0)], block=300.0, forward=250.0, band_forward=True,
        screen={256: {"dense": 6.0, "recheck": 10.0, "excess": [(0.01, 0.02), (0.1, 0.15)]}},
        excess={256: [(0.01, 0.02), (0.1, 0.15)]})
    legacy = dict(cm.to_dict(), host_call=1e20, host_block=1e15)
    rt = gc.CostModel.from_dict(json.loads(json.dumps(legacy)))
    assert rt.to_dict() == cm.to_dict()
    assert rt.signature() == cm.signature()
    candidates = [((256,), [1.0, 0.01]), ((512,), [1.0, 0.002]),
                  ((256, 512), [1.0, 0.1, 0.001])]

    def rank(cost):
        return sorted((cost.chain_cost(chain, reach), chain) for chain, reach in candidates)

    assert rank(rt) == rank(cm)
    assert rank(rt)[0][1] == (256,)


def test_forward_priced_per_chain():
    """Band forwards credit chains that refine few blocks; the backend's own byte rule decides."""
    import json
    gc = mf._gatechain
    gc._REFINE_BLOCKS.clear()                 # earlier GPU calls in this process may have noted some
    kw = dict(block=300.0, forward=300.0)
    cm = gc.CostModel(2048, {256: 1.0, 512: 2.0, 1024: 4.0}, {}, [(0.01, 9.0)], band_forward=True, **kw)
    # B = 512: bands pay iff f < (2048 - 512) / 4096 = 0.375
    assert cm.forward_cost((256, 512), 0.087) == pytest.approx(300 * (0.5 + 0.125) + 0.087 * 300)
    assert cm.forward_cost((256, 512), 0.40) == 300.0
    assert cm.forward_cost((512, 1024), 0.20) == pytest.approx(300 * 0.75 + 0.2 * 300)
    assert cm.forward_cost((512, 1024), 0.30) == 300.0          # past 0.25 for B = n/2
    off = gc.CostModel(2048, {256: 1.0}, {}, [(0.01, 9.0)], **kw)
    assert off.forward_cost((256, 512), 0.0) == 300.0              # no capability: full
    # per pair: no credit without a measured refine-block fraction
    assert cm.chain_forward_delta((256, 512), [1.0, 0.01, 0.0005], 100) == 0.0
    try:
        gc.note_refine_blocks(2048, 512, 0.087)                     # measured: bands win
        d = cm.chain_forward_delta((256, 512), [1.0, 0.01, 0.0005], 100)
        assert d == pytest.approx((cm.forward_cost((256, 512), 0.087) - 300.0) / 100) and d < 0
        gc._REFINE_BLOCKS.clear()
        gc.note_refine_blocks(2048, 512, 0.5)                       # measured: bands lose
        assert cm.chain_forward_delta((256, 512), [1.0, 0.01, 0.0005], 100) == 0.0
    finally:
        gc._REFINE_BLOCKS.clear()
    rt = gc.CostModel.from_dict(json.loads(json.dumps(cm.to_dict())))
    assert (rt.forward, rt.band_forward) == (300.0, True)


def test_model_f_credit_is_proposal_only():
    """The model's refine-block fraction credits the band forward only when asked to (block-size
    trial proposals); priced normally a chain without a measurement gets no credit."""
    gc = mf._gatechain
    gc._REFINE_BLOCKS.clear()
    cm = gc.CostModel(2048, {256: 1.0, 512: 2.0}, {}, [(0.01, 9.0)], block=300.0, forward=300.0,
                      band_forward=True)
    reach = [1.0, 0.01, 0.0005]
    assert cm.chain_forward_delta((256, 512), reach, 100) == 0.0
    f = 1 - (1 - 0.0005) ** 100
    d = cm.chain_forward_delta((256, 512), reach, 100, model_f=True)
    assert d == pytest.approx((cm.forward_cost((256, 512), f) - 300.0) / 100) and d < 0


def test_price_block_sizes_stops_at_the_first_dearer_size(monkeypatch):
    """A size dearer than the best -- even within TIE -- ends the search (it is still listed for
    the tie-break): the next size is not priced, since pricing it means calibrating and
    simulating at that n. With `ahead`, that many more dearer sizes are priced."""
    from matchedfilter import gatechain as gc
    priced = []
    # modelled cost per valid sample and template for each n (choose_chain's cost / nvalid)
    pair = {2048: 1.00, 4096: 1.00 * (1 + gc.TIE / 2), 8192: 0.5, 16384: 9.0}

    class _Cost:
        block = 0.0

    def fake_costs(n, device=None, ntemplates=None, group=None):
        priced.append(n)
        return _Cost()

    monkeypatch.setattr(_calibration, "device_costs", fake_costs)
    monkeypatch.setattr(gc, "rebin_profile", lambda fine, df, rate, n: np.ones(n))
    monkeypatch.setattr(gc, "choose_chain",
                        lambda ref, n, snr, fd, **kw: ({"cost": pair[n] * (n - 99), "chain": (n // 8,)}, []))
    gc._PRICE_CACHE.clear()
    fine = np.ones(2048)
    out = _calibration.price_block_sizes(fine, 1.0, 2048.0, 100, 0, 64, 6.0, 1e-3, [2048, 4096, 8192, 16384])
    assert priced == [2048, 4096] and [o[1] for o in out] == [2048, 4096]
    gc._PRICE_CACHE.clear(); priced.clear()
    out = _calibration.price_block_sizes(fine, 1.0, 2048.0, 100, 0, 64, 6.0, 1e-3, [2048, 4096, 8192, 16384],
                               ahead=2)
    # 4096 is the first dearer size, 8192 the new best, 16384 the second dearer one
    assert priced == [2048, 4096, 8192, 16384] and out[0][1] == 8192
    gc._PRICE_CACHE.clear()


@pytest.mark.parametrize("order", [(512, 2048), (1024, 2048), (2048, 1024), (4096, 8192), (1024, 4096, 8192)])
def test_calibrations_sharing_band_costs_in_any_order(monkeypatch, order):
    """Sizes on one series group share their band costs, so a later size measures only the
    bands an earlier one did not. Every order calibrates, and every size gets a screen price
    for each screen band (n = 1024 before 2048 left band 1024's screen without the recheck
    job it reads: KeyError, in the nightly's reverse-order run)."""
    gc = mf._gatechain
    monkeypatch.setattr(gc, "_COSTS", {})
    monkeypatch.delenv("MF_COST_FILE", raising=False)
    for n in order:
        cm = _calibration.calibrate_costs(n, 64)
        for b in gc.candidate_bands(n):
            if gc._q15_band(b) and gc.cpu_gate_kind() != "f16":
                assert b in cm.screen and cm.screen[b]["recheck"] >= 0, (n, b)
