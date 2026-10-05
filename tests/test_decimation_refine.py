"""Unit tests verifying reduced-rate D=2 filtering, AVX2 SIMD peak refinement,
and SNR normalization / noise-floor invariants.
"""

from unittest.mock import patch
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank
from matchedfilter import _core


def _generate_chirp(N, fs, f_low=30.0, f_high=750.0, phase_offset=0.0):
    """Generate a linear chirp template."""
    t = np.arange(N) / fs
    duration = N / fs
    phase = 2.0 * np.pi * (f_low * t + 0.5 * (f_high - f_low) / duration * (t ** 2)) + phase_offset
    return np.cos(phase).astype(np.float32)


def _make_analytic_injection(S, taps, target_snr, inj_pos):
    """Create an analytic signal with an injected template at inj_pos."""
    cnt = len(taps)
    half = cnt // 2
    s_real = np.zeros(S, dtype=np.float32)
    s_real[inj_pos - half : inj_pos - half + cnt] = float(target_snr) * taps
    D = np.fft.fft(s_real)
    D[S // 2:] = 0
    return (np.fft.ifft(D) * 2.0).astype(np.complex64)


# ==============================================================================
# 1. Noise Floor Normalization Invariant
# ==============================================================================

@pytest.mark.parametrize("engine", ["flat", "hier"])
@pytest.mark.parametrize("decimation", [1, 2])
def test_noise_floor_normalization_invariant(engine, decimation):
    """Verify that both D=1 and D=2 with flat and hier engines satisfy unit SNR std on Gaussian noise."""
    fs = 2048.0
    cnt = 350
    taps = _generate_chirp(cnt, fs, 30.0, 750.0, 0.0)
    taps /= np.linalg.norm(taps)

    ref_w = np.zeros(2048, dtype=np.float32)
    ref_w[20:480] = 1.0

    b = TimeDomainFilterBank(
        [taps], [cnt],
        tap_sample_rate=fs,
        data_sample_rate=fs,
        engine=engine,
        decimation=decimation,
        threshold=6.0,
    )
    if engine == "hier":
        b.set_reference(ref_w, delta_f=1.0)

    N = 131072
    rng = np.random.default_rng(42)
    # Unit Gaussian noise: std(Re) = 1.0, std(Im) = 1.0
    noise = (rng.standard_normal(N) + 1j * rng.standard_normal(N)).astype(np.complex64)

    # Invariant check on correlate_series (dense correlation output)
    rho = b.correlate_series(noise)
    valid = slice(2048, N - 2048)
    re_std = float(np.std(rho[0, valid].real))
    im_std = float(np.std(rho[0, valid].imag))

    assert 0.95 <= re_std <= 1.05, f"{engine} D={decimation} correlate Re std {re_std:.4f} not in 1.00 ± 0.05"
    assert 0.95 <= im_std <= 1.05, f"{engine} D={decimation} correlate Im std {im_std:.4f} not in 1.00 ± 0.05"

    # Invariant check on filter_series with threshold=0.0 and binsize=1 (sample-by-sample output)
    res = b.filter_series(noise, threshold=0.0, binsize=1)
    re_std_f = float(np.std(res.snr.real))
    im_std_f = float(np.std(res.snr.imag))

    assert 0.95 <= re_std_f <= 1.05, f"{engine} D={decimation} filter_series Re std {re_std_f:.4f} not in 1.00 ± 0.05"
    assert 0.95 <= im_std_f <= 1.05, f"{engine} D={decimation} filter_series Im std {im_std_f:.4f} not in 1.00 ± 0.05"


@pytest.mark.parametrize("engine", ["flat", "hier"])
@pytest.mark.parametrize("decimation", [1, 2])
def test_noise_floor_normalization_multitemplate(engine, decimation):
    """Verify that multi-template banks with diverse tap lengths maintain unit SNR std across all templates."""
    fs = 2048.0
    counts = [150, 350, 701]
    taps_list = [_generate_chirp(c, fs, 30.0, 750.0, 0.0) for c in counts]
    for t in taps_list:
        t /= np.linalg.norm(t)

    ref_w = np.zeros(2048, dtype=np.float32)
    ref_w[20:480] = 1.0

    b = TimeDomainFilterBank(
        taps_list, counts,
        tap_sample_rate=fs,
        data_sample_rate=fs,
        engine=engine,
        decimation=decimation,
        threshold=6.0,
    )
    if engine == "hier":
        b.set_reference(ref_w, delta_f=1.0)

    N = 131072
    rng = np.random.default_rng(1234)
    noise = (rng.standard_normal(N) + 1j * rng.standard_normal(N)).astype(np.complex64)

    rho = b.correlate_series(noise)
    valid = slice(2048, N - 2048)
    for i in range(len(counts)):
        re_std = float(np.std(rho[i, valid].real))
        im_std = float(np.std(rho[i, valid].imag))
        assert 0.95 <= re_std <= 1.05, f"{engine} D={decimation} tmpl={i} Re std {re_std:.4f} not in 1.00 ± 0.05"
        assert 0.95 <= im_std <= 1.05, f"{engine} D={decimation} tmpl={i} Im std {im_std:.4f} not in 1.00 ± 0.05"


# ==============================================================================
# 2. Threshold Rejection in Noise
# ==============================================================================

@pytest.mark.parametrize("engine", ["flat", "hier"])
@pytest.mark.parametrize("decimation", [1, 2])
def test_threshold_rejection_in_noise(engine, decimation):
    """Verify that pure Gaussian noise at threshold=6.0 returns <= 1 trigger for 10^6 samples."""
    fs = 2048.0
    cnt = 350
    taps = _generate_chirp(cnt, fs, 30.0, 750.0, 0.0)
    taps /= np.linalg.norm(taps)

    ref_w = np.zeros(2048, dtype=np.float32)
    ref_w[20:480] = 1.0

    b = TimeDomainFilterBank(
        [taps], [cnt],
        tap_sample_rate=fs,
        data_sample_rate=fs,
        engine=engine,
        decimation=decimation,
        threshold=6.0,
    )
    if engine == "hier":
        b.set_reference(ref_w, delta_f=1.0)

    # 2^20 = 1,048,576 samples (~10^6 samples)
    N = 1048576
    rng = np.random.default_rng(999)
    noise = (rng.standard_normal(N) + 1j * rng.standard_normal(N)).astype(np.complex64)

    res = b.filter_series(noise, threshold=6.0)
    n_triggers = len(res.sample_indices)
    assert n_triggers <= 1, f"{engine} D={decimation} produced {n_triggers} triggers at 6.0 sigma on 10^6 samples"


# ==============================================================================
# 3. Signal Recovery Fidelity
# ==============================================================================

@pytest.mark.parametrize("engine", ["flat", "hier"])
@pytest.mark.parametrize("decimation", [1, 2])
@pytest.mark.parametrize("target_snr", [10.0, 15.0])
@pytest.mark.parametrize("inj_parity", ["even", "odd"])
def test_signal_recovery_fidelity(engine, decimation, target_snr, inj_parity):
    """Verify that injected signals are recovered with SNR within 0.5% and timing error < 1 sample."""
    fs = 2048.0
    cnt = 350
    taps = _generate_chirp(cnt, fs, 30.0, 450.0, 0.0)
    taps /= np.linalg.norm(taps)

    ref_w = np.zeros(2048, dtype=np.float32)
    ref_w[20:480] = 1.0

    b = TimeDomainFilterBank(
        [taps], [cnt],
        tap_sample_rate=fs,
        data_sample_rate=fs,
        engine=engine,
        decimation=decimation,
        threshold=6.0,
    )
    if engine == "hier":
        b.set_reference(ref_w, delta_f=1.0)

    N = 32768
    inj_pos = 10000 if inj_parity == "even" else 10001
    series = _make_analytic_injection(N, taps, target_snr, inj_pos)

    res = b.filter_series(series)
    assert len(res.sample_indices) == 1, (
        f"{engine} D={decimation} SNR={target_snr} inj={inj_pos}: expected 1 trigger, got {len(res.sample_indices)}"
    )

    rec_time = res.sample_indices[0]
    rec_snr = float(abs(res.snr[0]))

    time_err = abs(rec_time - inj_pos)
    snr_rel_err = abs(rec_snr - target_snr) / target_snr

    assert time_err < 1.0, f"Timing error {time_err} >= 1 sample for injection at {inj_pos}"
    assert snr_rel_err < 0.005, f"SNR relative error {snr_rel_err * 100:.3f}% exceeded 0.5% (target={target_snr}, got={rec_snr})"


@pytest.mark.parametrize("engine", ["flat", "hier"])
def test_scalloping_guard_near_threshold_fidelity(engine):
    """Verify that near-threshold odd peaks (SNR 6.00 at odd sample) are recovered, while subthreshold (5.5) are rejected."""
    fs = 2048.0
    cnt = 701
    taps = _generate_chirp(cnt, fs, 30.0, 450.0, 0.0)
    taps /= np.linalg.norm(taps)

    ref_w = np.zeros(2048, dtype=np.float32)
    ref_w[20:480] = 1.0

    b = TimeDomainFilterBank(
        [taps], [cnt],
        tap_sample_rate=fs,
        data_sample_rate=fs,
        engine=engine,
        decimation=2,
        threshold=6.0,
    )
    if engine == "hier":
        b.set_reference(ref_w, delta_f=1.0)

    N = 32768
    inj_pos = 10001  # Odd sample subject to coarse decimation scalloping loss

    # Exactly at threshold 6.0: scalloping reduces coarse SNR to ~5.6, but refine_thr=5.52 catches it
    s_thr = _make_analytic_injection(N, taps, 6.0, inj_pos)
    res_thr = b.filter_series(s_thr)
    assert len(res_thr.sample_indices) == 1, f"Expected 1 trigger at threshold 6.0, got {len(res_thr.sample_indices)}"
    assert res_thr.sample_indices[0] == inj_pos
    assert np.isclose(abs(res_thr.snr[0]), 6.0, rtol=1e-3)

    # Subthreshold 5.5: must be rejected
    s_sub = _make_analytic_injection(N, taps, 5.5, inj_pos)
    res_sub = b.filter_series(s_sub)
    assert len(res_sub.sample_indices) == 0, f"Expected 0 triggers for subthreshold 5.5, got {len(res_sub.sample_indices)}"


@pytest.mark.parametrize("engine", ["flat", "hier"])
@pytest.mark.parametrize("decimation", [1, 2])
def test_signal_recovery_multitemplate(engine, decimation):
    """Verify that injection into a multi-template filter bank recovers the correct template and coordinates."""
    fs = 2048.0
    counts = [150, 350, 701]
    taps_list = [_generate_chirp(c, fs, 30.0, 450.0, 0.0) for c in counts]
    for t in taps_list:
        t /= np.linalg.norm(t)

    ref_w = np.zeros(2048, dtype=np.float32)
    ref_w[20:480] = 1.0

    b = TimeDomainFilterBank(
        taps_list, counts,
        tap_sample_rate=fs,
        data_sample_rate=fs,
        engine=engine,
        decimation=decimation,
        threshold=6.0,
    )
    if engine == "hier":
        b.set_reference(ref_w, delta_f=1.0)

    N = 32768
    inj_tmpl = 1
    inj_pos = 10001  # Odd sample
    series = _make_analytic_injection(N, taps_list[inj_tmpl], 14.0, inj_pos)

    res = b.filter_series(series)
    assert len(res.sample_indices) == 1
    assert res.template_indices[0] == inj_tmpl
    assert abs(res.sample_indices[0] - inj_pos) < 1
    assert abs(abs(res.snr[0]) - 14.0) / 14.0 < 0.005


# ==============================================================================
# 4. AVX2 Refinement Fast Path Parity & Robustness
# ==============================================================================

@pytest.mark.parametrize("cnt", [7, 16, 33, 64, 137, 513, 701])
@pytest.mark.parametrize("candidate_offset", [-1, 0, 1])
def test_avx2_refinement_fast_path_parity(cnt, candidate_offset):
    """Directly unit-test _core.refine_peaks_decim against un-decimated convolution across various tap counts and peak offsets."""
    assert hasattr(_core, "refine_peaks_decim"), "_core.refine_peaks_decim is missing"

    fs = 2048.0
    if cnt > 10:
        taps = _generate_chirp(cnt, fs, 30.0, 400.0, 0.0)
    else:
        taps = np.array([0.1, 0.3, 0.8, 1.0, 0.8, 0.3, 0.1], dtype=np.float32)[:cnt]
    taps = taps / np.linalg.norm(taps)
    half = cnt // 2

    # Injected peak
    inj_pos = 2000
    S = 8192
    series = _make_analytic_injection(S, taps, 12.0, inj_pos)

    # Coarse candidate setup:
    # If candidate_offset == 0: coarse m=1000, k_even=2000, true peak at k_even
    # If candidate_offset == 1: coarse m=999, k_even=1998 -> true peak at k_even + 2 (not +-1).
    # Correct relative offset:
    # m_cand = 1000: k_even = 2000
    # For candidate_offset = -1: coarse candidate is at m=1001 (k_even=2002), true peak is k_even - 1 = 2001
    # For candidate_offset =  0: coarse candidate is at m=1000 (k_even=2000), true peak is k_even = 2000
    # For candidate_offset = +1: coarse candidate is at m=1000 (k_even=2000), true peak is k_even + 1 = 2001
    if candidate_offset == 0:
        true_k = 2000
        m_cand = 1000
    elif candidate_offset == 1:
        true_k = 2001
        m_cand = 1000
    else:  # candidate_offset == -1
        true_k = 2001
        m_cand = 1001

    k_even = m_cand * 2
    eval_ks = [k_even - 1, k_even, k_even + 1]

    # Re-inject at true_k
    series = _make_analytic_injection(S, taps, 12.0, true_k)
    ref_dots = [np.dot(series[k - half : k - half + cnt], taps) for k in eval_ks]
    best_idx = int(np.argmax([abs(d) for d in ref_dots]))
    expected_k = eval_ks[best_idx]
    expected_snr = ref_dots[best_idx]

    # Prepare input buffers for C refine
    raw_taps = np.ascontiguousarray(taps.reshape(1, -1), dtype=np.float32)
    counts_arr = np.array([cnt], dtype=np.int64)
    in_tmpl = np.array([0], dtype=np.int64)
    in_samp = np.array([m_cand], dtype=np.int64)
    in_snr = np.array([ref_dots[1]], dtype=np.complex64)

    out_tmpl = np.empty(1, dtype=np.int64)
    out_samp = np.empty(1, dtype=np.int64)
    out_snr = np.empty(1, dtype=np.complex64)
    out_surv = np.empty(1, dtype=np.int64)

    n_out = _core.refine_peaks_decim(
        series, raw_taps, counts_arr,
        in_tmpl, in_samp, in_snr,
        6.0, 0.08, 2,
        out_tmpl, out_samp, out_snr, out_surv
    )

    assert n_out == 1, f"Expected 1 refined peak, got {n_out} for cnt={cnt}, true_k={true_k}"
    assert out_samp[0] == expected_k, f"cnt={cnt} true_k={true_k}: got sample {out_samp[0]} != expected {expected_k}"
    snr_diff = abs(out_snr[0] - expected_snr)
    assert snr_diff < 1e-4, f"cnt={cnt} true_k={true_k}: SNR diff {snr_diff} >= 1e-4 vs un-decimated convolution"


def test_avx2_refinement_clustering():
    """Verify that adjacent candidate triggers within cluster_win are clustered to the true peak."""
    assert hasattr(_core, "refine_peaks_decim"), "_core.refine_peaks_decim is missing"

    fs = 2048.0
    cnt = 701
    taps = _generate_chirp(cnt, fs, 30.0, 400.0, 0.0)
    taps /= np.linalg.norm(taps)

    inj_pos = 2001
    S = 8192
    series = _make_analytic_injection(S, taps, 15.0, inj_pos)

    # Provide two adjacent candidate triggers: m=1000 and m=1001
    raw_taps = np.ascontiguousarray(taps.reshape(1, -1), dtype=np.float32)
    counts_arr = np.array([cnt], dtype=np.int64)
    in_tmpl = np.array([0, 0], dtype=np.int64)
    in_samp = np.array([1000, 1001], dtype=np.int64)
    in_snr = np.array([14.0 + 0j, 14.0 + 0j], dtype=np.complex64)

    out_tmpl = np.empty(2, dtype=np.int64)
    out_samp = np.empty(2, dtype=np.int64)
    out_snr = np.empty(2, dtype=np.complex64)
    out_surv = np.empty(2, dtype=np.int64)

    n_out = _core.refine_peaks_decim(
        series, raw_taps, counts_arr,
        in_tmpl, in_samp, in_snr,
        6.0, 0.08, 2,
        out_tmpl, out_samp, out_snr, out_surv
    )

    # Should cluster the two candidates into one peak
    assert n_out == 1, f"Expected 1 clustered peak, got {n_out}"
    assert out_samp[0] == 2001, f"Expected peak at 2001, got {out_samp[0]}"
    assert np.isclose(abs(out_snr[0]), 15.0, atol=1e-4)


def test_avx2_refinement_heap_allocation_over_512():
    """Verify that _core.refine_peaks_decim safely handles n_cand > 512 using dynamic heap allocation."""
    assert hasattr(_core, "refine_peaks_decim")

    n_cand = 1000
    S = 65536
    cnt = 64
    series = np.ones(S, dtype=np.complex64)
    raw_taps = np.ones((1, cnt), dtype=np.float32) / np.sqrt(cnt)
    counts_arr = np.array([cnt], dtype=np.int64)

    in_tmpl = np.zeros(n_cand, dtype=np.int64)
    # Space candidates by 16 samples so they exceed cluster_win (4) and do not cluster
    in_samp = (np.arange(n_cand, dtype=np.int64) * 16 + 100)
    in_snr = np.full(n_cand, 10.0 + 0j, dtype=np.complex64)

    out_tmpl = np.empty(n_cand, dtype=np.int64)
    out_samp = np.empty(n_cand, dtype=np.int64)
    out_snr = np.empty(n_cand, dtype=np.complex64)
    out_surv = np.empty(n_cand, dtype=np.int64)

    n_out = _core.refine_peaks_decim(
        series, raw_taps, counts_arr,
        in_tmpl, in_samp, in_snr,
        6.0, 0.08, 2,
        out_tmpl, out_samp, out_snr, out_surv
    )

    assert n_out == n_cand, f"Expected {n_cand} candidates to survive heap allocation path, got {n_out}"
    assert np.all(out_tmpl == 0)
    assert np.all(out_samp == in_samp * 2)


def test_avx2_refinement_boundaries():
    """Verify that candidate refinement near the series boundaries does not crash or access invalid memory."""
    assert hasattr(_core, "refine_peaks_decim")

    S = 1000
    cnt = 300
    series = np.ones(S, dtype=np.complex64)
    raw_taps = np.ones((1, cnt), dtype=np.float32) / np.sqrt(cnt)
    counts_arr = np.array([cnt], dtype=np.int64)

    # m=0 (k_even=0, k_even-half < 0) and m=499 (k_even=998, k_even-half+cnt > 1000)
    in_tmpl = np.array([0, 0], dtype=np.int64)
    in_samp = np.array([0, 499], dtype=np.int64)
    in_snr = np.array([10.0 + 0j, 10.0 + 0j], dtype=np.complex64)

    out_tmpl = np.empty(2, dtype=np.int64)
    out_samp = np.empty(2, dtype=np.int64)
    out_snr = np.empty(2, dtype=np.complex64)
    out_surv = np.empty(2, dtype=np.int64)

    n_out = _core.refine_peaks_decim(
        series, raw_taps, counts_arr,
        in_tmpl, in_samp, in_snr,
        6.0, 0.08, 2,
        out_tmpl, out_samp, out_snr, out_surv
    )

    assert n_out == 2
    assert out_samp[0] == 0
    assert out_samp[1] == 998


def test_avx2_refinement_multitemplate():
    """Verify multi-template candidate refinement with differing tap lengths and no cross-template clustering."""
    assert hasattr(_core, "refine_peaks_decim")

    fs = 2048.0
    cnt0 = 350
    cnt1 = 701
    taps0 = _generate_chirp(cnt0, fs, 30.0, 400.0, 0.0)
    taps0 /= np.linalg.norm(taps0)
    taps1 = _generate_chirp(cnt1, fs, 30.0, 400.0, 0.0)
    taps1 /= np.linalg.norm(taps1)

    max_taps = max(cnt0, cnt1)
    raw_taps = np.zeros((2, max_taps), dtype=np.float32)
    raw_taps[0, :cnt0] = taps0
    raw_taps[1, :cnt1] = taps1
    counts_arr = np.array([cnt0, cnt1], dtype=np.int64)

    S = 8192
    inj_pos0 = 1000
    inj_pos1 = 2001
    s0 = _make_analytic_injection(S, taps0, 12.0, inj_pos0)
    s1 = _make_analytic_injection(S, taps1, 15.0, inj_pos1)
    series = s0 + s1

    # Candidates: template 0 at m=500 (k=1000) and template 1 at m=1000 (k=2000 -> refines to 2001)
    in_tmpl = np.array([0, 1], dtype=np.int64)
    in_samp = np.array([500, 1000], dtype=np.int64)
    in_snr = np.array([12.0 + 0j, 14.5 + 0j], dtype=np.complex64)

    out_tmpl = np.empty(2, dtype=np.int64)
    out_samp = np.empty(2, dtype=np.int64)
    out_snr = np.empty(2, dtype=np.complex64)
    out_surv = np.empty(2, dtype=np.int64)

    n_out = _core.refine_peaks_decim(
        series, raw_taps, counts_arr,
        in_tmpl, in_samp, in_snr,
        6.0, 0.08, 2,
        out_tmpl, out_samp, out_snr, out_surv
    )

    assert n_out == 2
    assert list(out_tmpl) == [0, 1]
    assert out_samp[0] == inj_pos0
    assert out_samp[1] == inj_pos1
    assert np.isclose(abs(out_snr[0]), 12.0, rtol=1e-3)
    assert np.isclose(abs(out_snr[1]), 15.0, rtol=1e-3)


# ==============================================================================
# 5. Zero-Threshold / Asymmetric Followup Behavior
# ==============================================================================

@pytest.mark.parametrize("engine", ["flat", "hier"])
def test_zero_threshold_asymmetric_followup(engine):
    """Verify that when threshold <= 0.0, filter_series returns grid samples without invoking refinement dot products."""
    cnt = 350
    fs = 2048.0
    taps = _generate_chirp(cnt, fs, 30.0, 400.0, 0.0)
    taps /= np.linalg.norm(taps)

    ref_w = np.zeros(2048, dtype=np.float32)
    ref_w[20:480] = 1.0

    b = TimeDomainFilterBank(
        [taps], [cnt],
        tap_sample_rate=fs,
        data_sample_rate=fs,
        engine=engine,
        decimation=2,
        threshold=6.0,
    )
    if engine == "hier":
        b.set_reference(ref_w, delta_f=1.0)

    S = 8192
    rng = np.random.default_rng(123)
    series = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)

    # Case A: threshold <= 0.0 must NOT invoke refine_peaks_decim
    with patch.object(mf._core, "refine_peaks_decim", side_effect=RuntimeError("Refinement invoked when threshold <= 0!")) as mock_refine:
        res0 = b.filter_series(series, threshold=0.0, binsize=256)
        assert not mock_refine.called, "refine_peaks_decim was invoked for threshold=0.0"
        assert len(res0.sample_indices) > 0, "Expected non-empty results for threshold=0.0"
        # All sample indices returned must be on the decimated grid (multiples of decim_stride = 2)
        assert np.all(res0.sample_indices % 2 == 0), "Returned non-grid sample indices for threshold=0.0"
        assert np.all(res0.block_starts % 2 == 0)
        assert np.all(res0.block_lengths >= 1024)

        res_neg = b.filter_series(series, threshold=-1.0, binsize=256)
        assert not mock_refine.called, "refine_peaks_decim was invoked for threshold=-1.0"
        assert np.all(res_neg.sample_indices % 2 == 0)

    # Case B: threshold > 0.0 with signal MUST invoke refine_peaks_decim and refine to odd peak
    inj_pos = 4001
    series_sig = _make_analytic_injection(S, taps, 15.0, inj_pos)

    with patch.object(mf._core, "refine_peaks_decim", wraps=mf._core.refine_peaks_decim) as mock_refine:
        res_pos = b.filter_series(series_sig, threshold=6.0)
        assert mock_refine.called, "refine_peaks_decim was NOT invoked for threshold=6.0"
        assert inj_pos in res_pos.sample_indices, f"Expected odd peak {inj_pos} in refined results {res_pos.sample_indices}"


# ==============================================================================
# 6. Edge Cases
# ==============================================================================

def test_avx2_refinement_empty_candidates():
    """Verify that _core.refine_peaks_decim safely handles zero input candidates."""
    assert hasattr(_core, "refine_peaks_decim")
    series = np.zeros(1024, dtype=np.complex64)
    raw_taps = np.zeros((1, 64), dtype=np.float32)
    counts = np.array([64], dtype=np.int64)

    out_tmpl = np.empty(0, dtype=np.int64)
    out_samp = np.empty(0, dtype=np.int64)
    out_snr = np.empty(0, dtype=np.complex64)
    out_surv = np.empty(0, dtype=np.int64)

    n_out = _core.refine_peaks_decim(
        series, raw_taps, counts,
        np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64), np.empty(0, dtype=np.complex64),
        6.0, 0.08, 2,
        out_tmpl, out_samp, out_snr, out_surv,
    )
    assert n_out == 0


def test_avx2_refinement_subthreshold_rejected():
    """Verify that candidate peaks below refine_thr are rejected without dot products."""
    assert hasattr(_core, "refine_peaks_decim")
    series = np.zeros(2048, dtype=np.complex64)
    raw_taps = np.zeros((1, 64), dtype=np.float32)
    counts = np.array([64], dtype=np.int64)

    # Candidate with SNR 3.0, well below 6.0 * (1 - 0.08) = 5.52
    in_tmpl = np.array([0], dtype=np.int64)
    in_samp = np.array([100], dtype=np.int64)
    in_snr = np.array([3.0 + 0j], dtype=np.complex64)

    out_tmpl = np.empty(1, dtype=np.int64)
    out_samp = np.empty(1, dtype=np.int64)
    out_snr = np.empty(1, dtype=np.complex64)
    out_surv = np.empty(1, dtype=np.int64)

    n_out = _core.refine_peaks_decim(
        series, raw_taps, counts,
        in_tmpl, in_samp, in_snr,
        6.0, 0.08, 2,
        out_tmpl, out_samp, out_snr, out_surv,
    )
    assert n_out == 0


def test_decimation_zero_noise_series():
    """Verify that filtering all-zero noise at threshold=6.0 returns 0 triggers."""
    cnt = 350
    fs = 2048.0
    taps = _generate_chirp(cnt, fs, 30.0, 400.0, 0.0)
    taps /= np.linalg.norm(taps)

    b = TimeDomainFilterBank([taps], [cnt], tap_sample_rate=fs, data_sample_rate=fs, engine="flat", decimation=2, threshold=6.0)
    series = np.zeros(8192, dtype=np.complex64)
    res = b.filter_series(series)
    assert len(res.sample_indices) == 0
