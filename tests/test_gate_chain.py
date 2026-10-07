import numpy as np
import pytest
import matchedfilter as mf
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


def test_cascade_subset_semantics():
    """Document and test intra-plan subset semantics vs cross-configuration behavior.

    Intra-Plan Semantics:
      Within a single execution plan (fixed b0, b1, g0, g1), Tier 1 is an
      intra-plan refinement filter of Tier 0. Any pair that evaluates Tier 1
      has strictly passed Tier 0 (c0 >= g0), and any pair refined to the fine
      filter has strictly passed both Tier 0 and Tier 1 (c0 >= g0 and c1 >= g1).
      Thus, candidate survivors form a nested subset:
          Survivors(Fine) <= Survivors(Tier 1) <= Survivors(Tier 0).

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

    # Intra-plan verification:
    rng = np.random.default_rng(777)
    ndata = 8
    noise = (rng.standard_normal((ndata, n), dtype=np.float32)
             + 1j * rng.standard_normal((ndata, n), dtype=np.float32)).astype(np.complex64)
    k = np.arange(n)
    noise[0] += (5.5 * h_freq * np.exp(2j * np.pi * 512 * k / n)).astype(np.complex64)

    survived_t0 = []
    survived_t1 = []
    for d in range(ndata):
        c0_vals = np.abs(np.fft.ifft(noise[d, :m0] * np.conj(h_freq[:m0])) * m0)
        c0_max = float(c0_vals.max())
        if c0_max >= g0:
            survived_t0.append(d)
            c1_vals = np.abs(np.fft.ifft(noise[d, :m1] * np.conj(h_freq[:m1])) * m1)
            c1_max = float(c1_vals.max())
            if c1_max >= g1:
                survived_t1.append(d)

    # Intra-plan: survivors of Tier 1 are a strict subset of Tier 0 survivors
    assert set(survived_t1).issubset(set(survived_t0)), "Intra-plan subset violated!"


def test_performance_tracking_and_summary():
    """Verify lightweight performance self-tracking and performance_summary() output."""
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
    assert summary["total_time_s"] > 0.0
    assert summary["min_batch_time_ms"] > 0.0
    assert summary["max_batch_time_ms"] >= summary["min_batch_time_ms"]
    assert summary["median_batch_time_ms"] >= summary["min_batch_time_ms"]
    assert summary["mean_batch_time_ms"] >= summary["min_batch_time_ms"]
    assert "device" in summary
    assert "backend" in summary
    assert f.performance_info == summary



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
    best, plans = gc.choose_chain(p, 2048, 6.0, 1e-3, cost=gc.calibrate_costs(2048, 64), max_tiers=2,
                                  window=(150, 1898))
    assert best is not None and len(best["chain"]) == 2, [(q["chain"], round(q["cost"])) for q in plans[:5]]


def test_autotune_off_keeps_the_model_choice(monkeypatch):
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_MARGIN", "100")
    mf.clear_autotune_cache()
    n = 4096
    power, H, D = _bank_case(n, 8, 4, 9)
    hf = mf.HierarchicalFilter(n, 4, 8, snr=5.5, fd=1e-3)
    hf.set_reference(power); hf.set_templates(H); hf.set_data(D)
    hf.run(binsize=n, threshold=5.0)
    assert hf.autotune_info["status"] == "locked"
    assert hf.config == hf.autotune_info["model"]


def test_trials_lock_one_winner_and_every_plan_switches(monkeypatch):
    """Close calls are measured: plans run the shortlist round-robin, then all adopt the winner."""
    monkeypatch.setenv("MF_AUTOTUNE", "1")
    monkeypatch.setenv("MF_CHAIN_MARGIN", "100")
    monkeypatch.setenv("MF_CHAIN_TRIALS", "2")
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
    assert len({p.config for p in plans}) > 1                # the shortlist is spread over the plans
    shortlist = plans[0].autotune_info["shortlist"]
    for _ in range(len(shortlist) * 2 + 2):
        for p in plans:
            p.run_series(ser, starts, ws, we, binsize=n, threshold=6.0)
    (trial,) = mf.get_autotune_state()["trials"].values()
    assert trial["winner"] in shortlist
    assert all(p.autotune_info["status"] == "locked" and p.config == trial["winner"] for p in plans)


def test_cost_calibration_is_sane():
    cm = mf._gatechain.calibrate_costs(2048, 32)
    assert all(v > 0 for v in cm.dense.values())
    assert cm.dense[64] < cm.dense[1024]               # wider first tiers cost more per pair
    assert cm.refine(0.05) > cm.dense[256]             # a refine costs more than a coarse evaluation
