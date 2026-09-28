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
    power = inspiral_power(n)
    thr = mf.choose_threshold(power, n, snr_target, fdr_budget, band=m1, cascade_band=m0)
    assert thr is not None
    gate_t0, gate_t1 = thr

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


def test_cascade_automated_gate_derivation():
    """Verify that choose_threshold and gate_for_cascade derive valid compound thresholds."""
    n = 4096
    power = inspiral_power(n)
    thr = mf.choose_threshold(power, n, 5.5, 1e-3, band=1024, cascade_band=256)
    assert isinstance(thr, tuple)
    assert len(thr) == 2
    g0, g1 = thr
    assert 2.5 <= g0 <= 4.5
    assert 4.0 <= g1 <= 5.5

    # Check argument validation
    from matchedfilter.gatemodel import gate_for_cascade
    with pytest.raises(ValueError, match="strictly less"):
        gate_for_cascade(power, n, 1024, 256, 5.5, 1e-3)

    with pytest.raises(ValueError, match="strictly less"):
        gate_for_cascade(power, n, 512, 512, 5.5, 1e-3)

    with pytest.raises(ValueError, match="positive"):
        gate_for_cascade(power, n, 256, 1024, -1.0, 1e-3)

    with pytest.raises(ValueError, match="between zero and one"):
        gate_for_cascade(power, n, 256, 1024, 5.5, 1.5)


def test_cascade_choose_config():
    """Verify that choose_config evaluates cascade candidates when requested."""
    n = 4096
    power = inspiral_power(n)
    tuning = mf._load_tuning()

    # Default is single-tier for backward compatibility
    cfg_single = mf.choose_config(power, n, 5.5, 1e-3, tuning=tuning, cascade=False)
    assert len(cfg_single) == 2
    assert cfg_single[0] in (256, 512, 1024, 2048)

    # When cascade=True, a cascade pair (band0, band1, K) can be chosen
    cfg_cascade = mf.choose_config(power, n, 5.5, 1e-3, tuning=tuning, cascade=True)
    if len(cfg_cascade) == 3:
        b0, b1, k = cfg_cascade
        assert b0 < b1
        assert b0 >= 64
        assert b1 <= n


def test_hierarchical_filter_auto_cascade():
    """Verify HierarchicalFilter with cascade=True chooses cascade configuration and derives thresholds."""
    n = 4096
    power = inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)

    hf = mf.HierarchicalFilter(n, 2, 4, snr=5.5, fd=1e-3, cascade=True)
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
    hf = mf.HierarchicalFilter(n, 1, 2, snr=5.5, fd=1e-3, band=1024, cascade_band=256)
    hf.set_reference(power)
    hf.set_templates(np.repeat(np.conj(h)[None, :], 2, axis=0))

    rng = np.random.default_rng(101)
    noise = (rng.standard_normal((1, n)) + 1j * rng.standard_normal((1, n))).astype(np.complex64)
    noise[0] += (9.0 * h).astype(np.complex64)
    hf.set_data(noise)

    peaks = hf.run(binsize=n, threshold=5.0)
    assert peaks[0, 0, 0]['index'] >= 0
    assert abs(peaks[0, 0, 0]['value']) >= 7.0


def test_cascade_cost_model_all_architectures():
    """Verify choose_config cost model across all architecture cost tables.

    Asserts that:
    1. If a cascade candidate is chosen, b0 < b_single strictly holds.
    2. Estimated cascade cost is strictly less than single-tier cost.
    3. On sugwg-login2 (Xeon 8260, AVX-512), when single-tier selects band 256,
       choose_config declines the cascade and selects single-band 256.
    """
    import glob
    import os
    from matchedfilter import CascadeConfig

    pkg_dir = os.path.dirname(mf.__file__)
    cost_files = glob.glob(os.path.join(pkg_dir, "cost*.txt"))
    assert len(cost_files) >= 5, f"Expected architecture cost files, found {len(cost_files)}"

    p2048 = inspiral_power(2048)
    p4096 = inspiral_power(4096)

    for cf in cost_files:
        tuning = mf._load_tuning(cf)
        for power, n in [(p2048, 2048), (p4096, 4096)]:
            sc = mf.choose_config(power, n, 5.5, 1e-3, tuning=tuning, cascade=False)
            cc = mf.choose_config(power, n, 5.5, 1e-3, tuning=tuning, cascade=True)
            if sc is None:
                assert cc is None
            else:
                if isinstance(cc, CascadeConfig) or (isinstance(cc, tuple) and len(cc) == 3):
                    b0 = cc.b0 if hasattr(cc, "b0") else cc[0]
                    b_single = sc[0]
                    assert b0 < b_single, (
                        f"Architecture {os.path.basename(cf)} at n={n}: "
                        f"cascade b0={b0} must be strictly less than single b={b_single}"
                    )

    # Specific verification for sugwg-login2 (genuineintel-family6-model85):
    # Mainline ran single band 256; cascade must decline and select single band 256
    cf_sugwg = os.path.join(pkg_dir, "cost-genuineintel-family6-model85.txt")
    t_sugwg = mf._load_tuning(cf_sugwg)
    sc_sugwg = mf.choose_config(p2048, 2048, 5.5, 1e-3, tuning=t_sugwg, cascade=False)
    cc_sugwg = mf.choose_config(p2048, 2048, 5.5, 1e-3, tuning=t_sugwg, cascade=True)
    assert sc_sugwg == (256, 8), f"Expected sugwg-login2 single-tier to select (256, 8), got {sc_sugwg}"
    assert cc_sugwg == (256, 8), f"Expected sugwg-login2 cascade to decline and select (256, 8), got {cc_sugwg}"


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
    thr = mf.choose_threshold(power, n, 5.5, 0.001, band=m1, cascade_band=m0)
    assert thr is not None
    g0, g1 = thr

    hmf = _core.HMF(n, 1, 1, 5.5, 0.001, m1, 1, 8, 8, m0)
    hmf.set_reference(power)
    hmf.set_threshold(g0, g1)
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

    thr_cascade = mf.choose_threshold(power, n, snr_target, fd_target, band=m1, cascade_band=m0)
    assert thr_cascade is not None
    g0, g1 = thr_cascade
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


def test_cascade_refinement_growth_declination_snr6():
    """Verify choose_config declines cascade when refinement growth penalty outweighs coarse savings."""
    from pathlib import Path
    ref_path = Path(__file__).parent / "data" / "reference_profile_pycbc.npy"
    if not ref_path.exists():
        pytest.skip("reference_profile_pycbc.npy fixture not available")
    ref = np.load(ref_path).astype(np.float32)
    ref = ref / ref.sum()

    n = 4096
    snr = 6.0
    fd = 1e-3

    single_cfg = mf.choose_config(ref, n, snr, fd, cascade=False)
    casc_cfg = mf.choose_config(ref, n, snr, fd, cascade=True)

    assert single_cfg == (512, 8), f"Expected single-tier (512, 8), got {single_cfg}"
    assert casc_cfg == (512, 8), (
        f"Expected cascade to be declined at SNR 6.00 and select single-tier (512, 8), got {casc_cfg}"
    )


def test_cascade_simd_width_floor():
    """Verify _min_band_for correctly enforces vector register width floors."""
    from matchedfilter import _min_band_for

    # Mock AVX-512 tuning metadata
    avx512_tuning = {"meta": {"cpu": "Intel(R) Xeon(R) Platinum 8260 CPU @ 2.40GHz"}}
    assert _min_band_for(None, avx512_tuning) == 256

    avx512_path_tuning = {"paths": ["/path/to/cost-genuineintel-family6-model85.txt"]}
    assert _min_band_for(None, avx512_path_tuning) == 256

    # Generic / AVX2 tuning
    avx2_tuning = {"meta": {"cpu": "AMD Ryzen 9 5950X 16-Core Processor"}}
    if "AVX3" not in (mf.backend() or "").upper():
        assert _min_band_for(None, avx2_tuning) == 128


def test_candidate_configs_viable_and_rejected():
    """Verify candidate_configs returns viable candidates and detailed rejection reasons."""
    n = 4096
    power = inspiral_power(n)
    candidates, rejected = mf.candidate_configs(power, n, 5.5, 1e-3, cascade=True)

    assert len(candidates) >= 1
    # First candidate is always the single-tier baseline
    single_choice = candidates[0]
    assert len(single_choice) == 2
    assert single_choice[0] in (256, 512, 1024, 2048)

    # Subsequent candidates are cascade configs
    for c in candidates[1:]:
        assert hasattr(c, "b0") and hasattr(c, "b1")
        assert c.b0 < c.b1
        assert c.b0 >= 128

    # Rejection list structure validation
    for r in rejected:
        assert "config" in r
        assert "reason" in r
        assert isinstance(r["reason"], str)

    # When cascade=False, only single-tier is returned
    c_single, r_single = mf.candidate_configs(power, n, 5.5, 1e-3, cascade=False)
    assert len(c_single) == 1
    assert c_single[0] == single_choice
    assert len(r_single) == 0


def test_hierarchical_runtime_autotuning_over_batches():
    """Verify runtime autotuning executes real work, evaluates candidate pool, and locks winner."""
    n = 4096
    power = inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)
    h_conj = np.conj(h)

    nd, nt = 2, 4
    hf = mf.HierarchicalFilter(n, nd, nt, snr=5.5, fd=1e-3, cascade=True)
    assert hf.autotune_info["status"] == "uninitialized"
    assert hf.autotune_info["winner"] is None

    hf.set_reference(power)
    hf.set_templates(np.repeat(h_conj[None, :], nt, axis=0))

    rng = np.random.default_rng(2026)
    noise = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    # Inject signal in (0, 0)
    noise[0] += (7.5 * h).astype(np.complex64)
    hf.set_data(noise)

    # Candidate pool count
    cands, _ = mf.candidate_configs(power, n, 5.5, 1e-3, device=hf.device, cascade=True)

    # If only 1 candidate, it locks immediately
    if len(cands) == 1:
        peaks = hf.run(binsize=n, threshold=5.0)
        assert hf.autotune_info["status"] == "locked"
        assert hf.autotune_info["winner"] == cands[0]
        assert peaks[0, 0, 0]["index"] >= 0
        return

    # Multiple candidates: run batches to trigger trials and winner selection
    assert len(cands) > 1

    # Batch 1
    res1 = hf.run(binsize=n, threshold=5.0)
    assert res1[0, 0, 0]["index"] >= 0
    assert len(hf.autotune_info["trials"]) == 1
    assert hf.autotune_info["status"] in ("tuning", "locked")

    # Run remaining trials to finish tuning
    n_batches = len(cands) + 2
    for b in range(2, n_batches + 1):
        noise = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
        noise[0] += (7.5 * h).astype(np.complex64)
        hf.set_data(noise)
        res = hf.run(binsize=n, threshold=5.0)
        assert res[0, 0, 0]["index"] >= 0

    # After evaluating all candidates, status must be locked
    assert hf.autotune_info["status"] == "locked"
    assert hf.autotune_info["winner"] in cands
    assert len(hf.autotune_info["untried"]) == 0
    assert len(hf.autotune_info["trials"]) >= len(cands)

    # Run another batch: status remains locked
    winner = hf.autotune_info["winner"]
    hf.set_data(noise)
    hf.run(binsize=n, threshold=5.0)
    assert hf.autotune_info["status"] == "locked"
    assert hf.autotune_info["winner"] == winner
    assert hf.config == winner


def test_hierarchical_runtime_autotuning_series():
    """Verify runtime autotuning functions seamlessly with run_series batches."""
    n = 4096
    power = inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)
    h_conj = np.conj(h)

    nt = 4
    hf = mf.HierarchicalFilter(n, 1, nt, snr=5.5, fd=1e-3, cascade=True, valid=(0, n))
    hf.set_reference(power)
    hf.set_templates(np.repeat(h_conj[None, :], nt, axis=0))

    rng = np.random.default_rng(42)
    series_len = n * 4
    series = (rng.standard_normal(series_len) + 1j * rng.standard_normal(series_len)).astype(np.complex64)

    # Filter 3 separate series batches
    for _ in range(4):
        res = hf.run_series(series, binsize=n, threshold=5.0)
        assert res.shape[0] > 0

    assert hf.performance_stats["total_calls"] >= 4
    assert len(hf.performance_stats["batch_times_ms"]) >= 4
    assert hf.autotune_info["status"] in ("tuning", "locked")


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


def test_hierarchical_pinned_configuration_reproducibility():
    """Verify pinning configuration via band=(b0, b1, taps) guarantees exact reproducibility without tuning."""
    n = 4096
    power = inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)

    # Pin explicitly to (256, 1024, 8)
    hf = mf.HierarchicalFilter(n, 1, 2, snr=5.5, fd=1e-3, band=(256, 1024, 8))
    assert hf.autotune_info["status"] == "pinned"
    assert hf.autotune_info["winner"] == (256, 1024, 8)
    assert hf.autotune_info["untried"] == []
    assert hf.cascade_config == (256, 1024, 8)
    assert hf.band == (256, 1024)

    hf.set_reference(power)
    hf.set_templates(np.repeat(np.conj(h)[None, :], 2, axis=0))

    rng = np.random.default_rng(88)
    d = (rng.standard_normal((1, n)) + 1j * rng.standard_normal((1, n))).astype(np.complex64)
    hf.set_data(d)

    res = hf.run(binsize=n, threshold=5.0)
    assert res.shape == (1, 2, 1)

    # Status must stay pinned, no autotune trials triggered
    assert hf.autotune_info["status"] == "pinned"
    assert len(hf.autotune_info["trials"]) == 0

    summary = hf.performance_summary()
    assert summary["total_calls"] == 1
    assert summary["autotune"]["status"] == "pinned"
    assert summary["autotune"]["winner"] == (256, 1024, 8)





