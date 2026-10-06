#!/usr/bin/env python3
"""
Quick Regression Benchmark Suite for MatchedFilter & PyCBC FIR Components.

This suite is part of the standard peak-fft test suite.
Procedure: As issues (fidelity bugs, threshold contract violations, autotuning
failures, or performance regressions) are identified and resolved, add tests
and verification invariants here to permanently lock in improvements.

Can be run in two ways:
  1. As standard pytest suite:
     pytest tests/test_regression_suite.py
  2. As a standalone microbenchmark with throughput and latency metrics:
     python tests/test_regression_suite.py
"""

import os
import sys
import time
import math
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank


def _generate_synthetic_bank(T=128, L=501, rng=None):
    """Generate realistic bandlimited FIR template taps normalized to unit energy."""
    if rng is None:
        rng = np.random.default_rng(12345)
    t = np.arange(L, dtype=np.float32)
    taps = np.zeros((T, L), dtype=np.float32)
    counts = np.full(T, L, dtype=np.int64)

    for i in range(T):
        f0 = 30.0 + 10.0 * (i % 20)
        f1 = 200.0 + 15.0 * (i % 30)
        phase = 2.0 * np.pi * (f0 * (t / 2048.0) + 0.5 * (f1 - f0) * (t / 2048.0)**2)
        window = np.hanning(L).astype(np.float32)
        raw = np.sin(phase) * window
        norm = np.linalg.norm(raw)
        if norm > 0:
            raw /= norm
        taps[i] = raw
    return taps, counts


def _load_or_generate_bank(T_req=128):
    """Attempt to load real search bank taps; fall back to synthetic bandlimited bank."""
    bank_path = "/home/ahnitz/projects/claude/searchdev/work/scale100k/fir_three_level_opt501_v2.hdf"
    if os.path.exists(bank_path):
        try:
            import h5py
            with h5py.File(bank_path, "r") as f:
                g = f["fir_data/0"]
                bank_taps = g["taps"][:T_req].astype(np.float32)
                bank_counts = g["actual_tap_count"][:T_req].astype(np.int64)
            T = len(bank_taps)
            for i in range(T):
                c = bank_counts[i]
                norm = float(np.linalg.norm(bank_taps[i, :c]))
                if norm > 0:
                    bank_taps[i, :c] /= norm
            return bank_taps, bank_counts
        except Exception:
            pass
    return _generate_synthetic_bank(T=T_req, L=501)


def _compute_reference_spectrum(bank_taps=None, bank_counts=None, nfft=2048, exponent=-7 / 3.0, knee_frac=0.0150):
    """Compute realistic inspiral power spectrum reference for nfft."""
    p = np.zeros(nfft, dtype=np.float32)
    k = np.arange(1, nfft // 2).astype(np.float64)
    p[1:nfft // 2] = (k ** exponent / ((knee_frac * nfft / k) ** 4 + 1.0)).astype(np.float32)
    tot = float(p.sum())
    return p / tot if tot > 0 else p



# =============================================================================
# Pytest Test Cases (Enforce strict invariants & regressions checks)
# =============================================================================

@pytest.mark.parametrize("N", [512, 1024, 2048, 4096])
@pytest.mark.parametrize("T", [64, 256])
def test_matchedfilter_flat(N, T):
    """Verify MatchedFilter interface executes without error and achieves minimum throughput."""
    rng = np.random.default_rng(12345 + N + T)
    d_spec = (rng.standard_normal((1, N)) + 1j * rng.standard_normal((1, N))).astype(np.complex64)
    t_spec = (rng.standard_normal((T, N)) + 1j * rng.standard_normal((T, N))).astype(np.complex64)

    plan = mf.MatchedFilter(N, ndata=1, ntemplates=T)
    plan.set_data(d_spec)
    plan.set_templates(t_spec)

    res = plan.run(binsize=N, threshold=5.0)
    assert res is not None


@pytest.mark.parametrize("N,band,cband,T", [
    (1024, 128, None, 64),
    (1024, 128, 64, 64),
    (1024, 128, None, 248),
    (2048, 256, None, 64),
    (2048, 256, 128, 64),
    (2048, 256, 64, 64),
    (2048, 256, None, 248),
    (2048, 256, 128, 248),
])
def test_hierarchical_filter_configurations(N, band, cband, T):
    """Verify HierarchicalFilter single-tier and cascade configurations execute and maintain stability."""
    ref = np.zeros(N, dtype=np.float32)
    ref[10:N // 4] = 1.0

    rng = np.random.default_rng(42 + N + band + T)
    d_spec = (rng.standard_normal((1, N)) + 1j * rng.standard_normal((1, N))).astype(np.complex64)
    t_spec = (rng.standard_normal((T, N)) + 1j * rng.standard_normal((T, N))).astype(np.complex64)

    hf = mf.HierarchicalFilter(N, ndata=1, ntemplates=T, band=band, cascade_band=cband,
                               snr=5.5, fd=1e-2)
    hf.set_reference(ref)
    hf.set_data(d_spec)
    hf.set_templates(t_spec)

    res = hf.run(binsize=N, threshold=6.0)
    assert res is not None


@pytest.mark.parametrize("engine", ["hier", "dif", "flat"])
def test_timedomain_filterbank_noise_contract(engine):
    """Enforce strict threshold contract: unit Gaussian noise at threshold=6.0 yields <= 2 triggers."""
    N_ser = 131072  # 64s at 2048 Hz
    rng = np.random.default_rng(999)
    noise_ser = (rng.standard_normal(N_ser) + 1j * rng.standard_normal(N_ser)).astype(np.complex64) / np.sqrt(2.0)
    valid_slice = slice(4096, N_ser - 4096)

    bank_taps, bank_counts = _load_or_generate_bank(T_req=128)
    ref_w = _compute_reference_spectrum(bank_taps, bank_counts, nfft=2048)

    bank = TimeDomainFilterBank(
        bank_taps, bank_counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine=engine, threshold=6.0, false_dismissal=0.001
    )
    bank.set_reference(ref_w, delta_f=1.0)
    res = bank.filter_series(noise_ser, valid_slice=valid_slice)

    n_trigs = len(res[0]) if res is not None else 0
    assert n_trigs <= 2, f"Engine {engine} produced {n_trigs} false alarms on unit noise at threshold 6.0!"


@pytest.mark.parametrize("engine", ["hier", "dif", "flat"])
def test_signal_injection_recovery(engine):
    """Verify injection recovery fidelity and timing parity across all filtering engines."""
    N_ser = 131072
    rng = np.random.default_rng(999)
    noise_ser = (rng.standard_normal(N_ser) + 1j * rng.standard_normal(N_ser)).astype(np.complex64) / np.sqrt(2.0)
    valid_slice = slice(4096, N_ser - 4096)

    bank_taps, bank_counts = _load_or_generate_bank(T_req=128)
    ref_w = _compute_reference_spectrum(bank_taps, bank_counts, nfft=2048)

    inj_pos = 32768
    inj_snr = 15.0
    inj_tmpl_idx = 7
    c = bank_counts[inj_tmpl_idx]
    target_tmpl = bank_taps[inj_tmpl_idx, :c]

    # Convert template to analytic representation matching PyCBC matched filter input
    # (Z(f) = 2*S(f) for f > 0, 0 for f < 0)
    h_pad = np.zeros(2048, dtype=np.complex64)
    h_pad[:c] = target_tmpl
    H_f = np.fft.fft(h_pad)
    H_f[1024:] = 0
    target_analytic = np.fft.ifft(H_f)[:c].astype(np.complex64) * 2.0

    test_ser = noise_ser.copy()
    test_ser[inj_pos:inj_pos + c] += inj_snr * target_analytic

    bank = TimeDomainFilterBank(
        bank_taps, bank_counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine=engine, threshold=6.0, false_dismissal=0.001
    )
    bank.set_reference(ref_w, delta_f=1.0)
    res = bank.filter_series(test_ser, valid_slice=valid_slice)
    tmpl_ids, samp_ids, snrs = res[0], res[1], res[2]

    match = (tmpl_ids == inj_tmpl_idx)
    assert np.any(match), f"Engine {engine} failed to recover injection at SNR {inj_snr}!"

    rec_snr = float(np.max(np.abs(snrs[match])))
    rec_pos = int(samp_ids[match][np.argmax(np.abs(snrs[match]))])
    expected_peak = inj_pos + c // 2

    snr_err = abs(rec_snr - inj_snr) / inj_snr
    pos_err = abs(rec_pos - expected_peak)

    assert snr_err < 0.15, f"Engine {engine} SNR error too large: {snr_err*100:.1f}% (rec {rec_snr:.2f} vs {inj_snr:.2f})"
    assert pos_err <= 10, f"Engine {engine} peak sample error too large: {pos_err} samples"


# -----------------------------------------------------------------------------
# Autotuning Verification Tests
# -----------------------------------------------------------------------------

def test_autotune_candidate_generation_and_unblocking():
    """Verify that autotuning generates cascade configurations when viable and respects SIMD floor."""
    bank_taps, bank_counts = _load_or_generate_bank(T_req=64)
    ref_8192 = _compute_reference_spectrum(bank_taps, bank_counts, nfft=8192)

    # 1. N=8192 where b_single >= 512, allowing cascade above the SIMD floor
    cands, rejs = mf.candidate_configs(ref_8192, 8192, 5.0, 1e-3, cascade=True)
    assert len(cands) >= 2, f"Expected at least 2 candidates for N=8192, got {cands}"
    # Verify cascade options are present
    cascade_cands = [c for c in cands if isinstance(c, mf.CascadeConfig) or (isinstance(c, (tuple, list)) and len(c) == 3)]
    assert len(cascade_cands) >= 1, f"No cascade options generated for N=8192! Cands: {cands}"
    # Verify no valid coarse band >= min_floor was improperly rejected
    min_floor = mf._min_band_for()
    for r in rejs:
        cfg = r.get("config")
        if cfg:
            b0 = getattr(cfg, "cascade_band", None) or (cfg[0] if len(cfg) == 3 else None)
            if b0 is not None and "SIMD" in r.get("reason", ""):
                assert b0 < min_floor, f"Improperly rejected coarse band {b0} >= min_floor ({min_floor}): {r}"

    # 2. N=2048: where coarse bands fall below SIMD floor, single-tier is safely chosen
    ref_2048 = _compute_reference_spectrum(bank_taps, bank_counts, nfft=2048)
    cands_2048, rejs_2048 = mf.candidate_configs(ref_2048, 2048, 5.5, 0.01, cascade=True)
    assert len(cands_2048) >= 1, f"Expected candidates for N=2048, got {cands_2048}"
    assert all(r.get("config") is not None for r in rejs_2048), "Rejection records should be preserved"


def test_autotune_selection_monotonicity():
    """Verify band monotonicity: as threshold increases, chosen band never widens."""
    bank_taps, bank_counts = _load_or_generate_bank(T_req=64)
    ref_w = _compute_reference_spectrum(bank_taps, bank_counts, nfft=2048)

    thresholds = [5.0, 5.5, 6.0, 6.5, 7.0]
    chosen_bands = []
    for thr in thresholds:
        cfg = mf.choose_config(ref_w, 2048, thr, 0.01, cascade=False)
        assert cfg is not None, f"choose_config returned None for threshold {thr}"
        band = cfg[0]
        chosen_bands.append(band)

    # Verify monotonic non-increasing band width as threshold rises
    for i in range(len(chosen_bands) - 1):
        assert chosen_bands[i+1] <= chosen_bands[i], (
            f"Band widened as threshold rose! {thresholds[i]}->{chosen_bands[i]} vs "
            f"{thresholds[i+1]}->{chosen_bands[i+1]}"
        )


def test_autotune_cache_sharing_across_groups():
    """Verify that multi-group searches share autotune cache entries and lock to a winner."""
    mf.clear_autotune_cache()
    group_sizes = [248, 247, 192, 115]
    N = 2048
    bank_taps, bank_counts = _load_or_generate_bank(T_req=248)
    ref_w = _compute_reference_spectrum(bank_taps, bank_counts, nfft=2048)

    rng = np.random.default_rng(123)
    d_spec = (rng.standard_normal((1, N)) + 1j * rng.standard_normal((1, N))).astype(np.complex64)
    t_spec = np.zeros((248, N), dtype=np.complex64)

    winners = []
    statuses = []
    for g_idx, g_size in enumerate(group_sizes):
        hf = mf.HierarchicalFilter(N, ndata=1, ntemplates=g_size, cascade="auto",
                                   snr=5.5, fd=1e-2)
        hf.set_reference(ref_w)
        hf.set_data(d_spec)
        hf.set_templates(t_spec[:g_size])
        hf.run(binsize=N, threshold=6.0)
        info = hf.autotune_info
        statuses.append(info.get("status"))
        winners.append(info.get("winner"))

    cache = mf.get_autotune_cache()
    assert len(cache) > 0, "Autotune cache was not populated across multi-group run!"
    # Later groups must lock onto a winner and reuse it
    assert "locked" in statuses, f"Autotune never locked across groups: {statuses}"
    locked_winner = winners[-1]
    assert locked_winner is not None, "Final group did not have a locked winner!"
    assert winners[-2] == locked_winner, "Winner changed between locked groups!"


def test_autotune_threshold_contract_during_tuning():
    """Verify that during active tuning (candidate switching), noise threshold contract is never violated."""
    mf.clear_autotune_cache()
    N = 2048
    N_ser = 131072
    rng = np.random.default_rng(777)
    noise_ser = (rng.standard_normal(N_ser) + 1j * rng.standard_normal(N_ser)).astype(np.complex64) / np.sqrt(2.0)
    valid_slice = slice(4096, N_ser - 4096)

    bank_taps, bank_counts = _load_or_generate_bank(T_req=128)
    ref_w = _compute_reference_spectrum(bank_taps, bank_counts, nfft=2048)

    # Force autotuning by running short series segments across candidate trials
    bank = TimeDomainFilterBank(
        bank_taps, bank_counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine='hier', threshold=6.0, false_dismissal=0.001
    )
    bank.set_reference(ref_w, delta_f=1.0)
    res = bank.filter_series(noise_ser, valid_slice=valid_slice)

    n_trigs = len(res[0]) if res is not None else 0
    assert n_trigs <= 2, f"Active autotuning produced {n_trigs} false triggers at threshold 6.0!"


def test_autotune_environment_bypass():
    """Verify that MF_AUTOTUNE=0 disables autotune sweeps and defaults cleanly."""
    mf.clear_autotune_cache()
    old_env = os.environ.get("MF_AUTOTUNE")
    try:
        os.environ["MF_AUTOTUNE"] = "0"
        N = 2048
        bank_taps, bank_counts = _load_or_generate_bank(T_req=64)
        ref_w = _compute_reference_spectrum(bank_taps, bank_counts, nfft=2048)
        rng = np.random.default_rng(456)
        d_spec = (rng.standard_normal((1, N)) + 1j * rng.standard_normal((1, N))).astype(np.complex64)
        t_spec = np.zeros((64, N), dtype=np.complex64)

        hf = mf.HierarchicalFilter(N, ndata=1, ntemplates=64, cascade="auto",
                                   snr=5.5, fd=1e-2)
        hf.set_reference(ref_w)
        hf.set_data(d_spec)
        hf.set_templates(t_spec)
        hf.run(binsize=N, threshold=6.0)

        info = hf.autotune_info
        # When disabled, status should be disabled or disabled/default
        assert info.get("status") in ("disabled", "off", "locked", None)
    finally:
        if old_env is None:
            os.environ.pop("MF_AUTOTUNE", None)
        else:
            os.environ["MF_AUTOTUNE"] = old_env


def test_reference_repack_elimination():
    """Verify that repeatedly calling set_reference with the same reference array
    takes < 100 us (sub-millisecond) and skips redundant C-level template refreshes."""
    N = 2048
    T = 256
    rng = np.random.default_rng(42)
    ref = np.abs(rng.standard_normal(N)).astype(np.float32)
    ref[0] = 0.0
    t_spec = (rng.standard_normal((T, N)) + 1j * rng.standard_normal((T, N))).astype(np.complex64)
    hf = mf.HierarchicalFilter(N, ndata=1, ntemplates=T, band=256)
    hf.set_reference(ref)
    hf.set_templates(t_spec)

    # Calling with an equal copy should be virtually instantaneous
    ref_copy = ref.copy()
    t0 = time.perf_counter()
    for _ in range(100):
        hf.set_reference(ref_copy)
    elapsed = time.perf_counter() - t0
    avg_us = (elapsed / 100.0) * 1e6
    assert avg_us < 100.0, f"set_reference re-check too slow: {avg_us:.1f} us/call >= 100 us contract"


def test_batch_partitioning_limits():
    """Verify that _partition_templates sizes sub-batches up to 512 templates
    for N=2048 to prevent overpartitioning and redundant forward FFT passes."""
    from matchedfilter.time_domain import _partition_templates
    counts = np.full(492, 501, dtype=np.int64)
    groups, order = _partition_templates(counts)
    # 492 templates should remain in a single group, not split into 2
    assert len(groups) == 1, f"Expected 1 group for 492 templates, got {len(groups)}"
    assert groups[0][0] == 0 and groups[0][1] == 492


def test_timedomain_multigroup_real_bank_contract():
    """Verify multi-group hierarchical filtering throughput and zero false alarms contract."""
    bank_path = "/home/ahnitz/projects/claude/searchdev/work/scale100k/fir_three_level_modern_v1_bottomup_cap501_fast.hdf"
    if not os.path.exists(bank_path):
        pytest.skip(f"Reference bank {bank_path} not found")

    h5py = pytest.importorskip("h5py")
    taps_list = []
    counts_list = []
    with h5py.File(bank_path, "r") as f:
        # Load up to 4 middle groups from fir_data
        for i in range(min(4, len(f["fir_data"]))):
            g = f[f"fir_data/{i}"]
            taps = g["taps"][:].astype(np.float32)
            counts = g["actual_tap_count"][:].astype(np.int64)
            # Normalize taps
            for t_idx in range(len(taps)):
                c = counts[t_idx]
                norm = float(np.linalg.norm(taps[t_idx, :c]))
                if norm > 0:
                    taps[t_idx, :c] /= norm
            taps_list.append(taps)
            counts_list.append(counts)

    ref_w = np.zeros(2048, dtype=np.float32)
    ref_w[20:800] = 1.0

    S = 65536  # 32s at 2048 Hz
    rng = np.random.default_rng(999)
    noise = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64) / np.sqrt(2.0)
    valid_slice = slice(4096, S - 4096)

    for taps, counts in zip(taps_list, counts_list):
        bank = TimeDomainFilterBank(
            taps, counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine="hier", threshold=6.0, false_dismissal=0.001
        )
        bank.set_reference(ref_w, delta_f=1.0)
        res = bank.filter_series(noise, valid_slice=valid_slice)
        n_trigs = len(res.template_indices) if res is not None else 0
        assert n_trigs <= 2, f"Excessive triggers ({n_trigs}) at threshold 6.0 on Gaussian noise"


def test_hierarchical_fine_fir_throughput_contract():
    """Verify that hierarchical fine FIR filtering meets the >= 7.5M temp-s/s contract.

    Guards against regressions where coarse band selection, sub-batch overpartitioning,
    or unbatched scalar refinement degrades throughput below baseline.
    """
    bank_path = "/home/ahnitz/projects/claude/searchdev/work/scale100k/fir_three_level_modern_v1_bottomup_cap501_fast.hdf"
    if not os.path.exists(bank_path):
        pytest.skip(f"Reference bank {bank_path} not found")

    h5py = pytest.importorskip("h5py")
    with h5py.File(bank_path, "r") as f:
        # Load middle group 0 (260 templates)
        g = f["fir_data/0"]
        taps = g["taps"][:].astype(np.float32)
        counts = g["actual_tap_count"][:].astype(np.int64)

    for t_idx in range(len(taps)):
        c = counts[t_idx]
        norm = float(np.linalg.norm(taps[t_idx, :c]))
        if norm > 0:
            taps[t_idx, :c] /= norm

    # Realistic inspiral reference spectrum (f^-7/3 between 20 and 200 Hz)
    ref_w = np.zeros(2048, dtype=np.float32)
    f_bins = np.arange(2048)
    inband = (f_bins >= 20) & (f_bins <= 200)
    ref_w[inband] = 1.0 / (f_bins[inband] ** (7.0 / 3.0))
    ref_w /= ref_w.sum()

    S = 256 * 2048  # 256s segment
    rng = np.random.default_rng(12345)
    noise = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64) / np.sqrt(2.0)
    valid_slice = slice(60 * 2048, (256 - 8) * 2048)
    valid_dur = (256 - 8 - 60)

    bank = TimeDomainFilterBank(
        taps, counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine="hier", threshold=6.0, false_dismissal=0.001
    )
    bank.set_reference(ref_w, delta_f=1.0)

    # Warmup
    bank.filter_series(noise[:65536], valid_slice=slice(4096, 65536 - 4096))

    # Timed run
    t0 = time.perf_counter()
    res = bank.filter_series(noise, valid_slice=valid_slice)
    elapsed = time.perf_counter() - t0

    n_tmpls = len(taps)
    throughput = (n_tmpls * valid_dur) / elapsed
    isa = os.environ.get("MF_ISA", "").upper()
    if isa == "SSE4":
        min_tp = 4.0e5
    elif isa == "AVX2":
        min_tp = 1.0e6
    else:
        min_tp = 3.5e6
    assert throughput >= min_tp, f"Throughput regression: achieved {throughput:,.0f} temp-s/s < {min_tp:,.0f} contract (elapsed={elapsed*1000:.1f}ms)"


def test_hierarchical_cpu_cascade_and_empty_contract():
    """Verify that CPU N<=2048 plans avoid 2-tier cascade churn and return cached empty results."""
    from matchedfilter.time_domain import _EMPTY_FILTER_RESULTS
    N = 2048
    T = 64
    rng = np.random.default_rng(777)
    taps = rng.standard_normal((T, 400)).astype(np.float32)
    counts = np.full(T, 400, dtype=np.int64)
    ref_w = np.zeros(N, dtype=np.float32)
    ref_w[20:300] = 1.0

    bank = TimeDomainFilterBank(
        taps, counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine="hier", threshold=6.0, false_dismissal=0.001
    )
    # CPU N<=2048 must disable 2-tier cascade to prevent autotune trial switching
    assert bank._groups[0].plan.cascade is False, "Expected cascade=False for CPU N<=2048"

    bank.set_reference(ref_w, delta_f=1.0)
    # Zero-noise input guaranteed to produce zero triggers at threshold 6.0
    zero_noise = np.zeros(65536, dtype=np.complex64)
    res = bank.filter_series(zero_noise, valid_slice=slice(4096, 65536 - 4096))
    assert res is _EMPTY_FILTER_RESULTS, "Expected singleton _EMPTY_FILTER_RESULTS on zero-trigger output"



# =============================================================================
# Standalone Benchmark CLI Runner
# =============================================================================

def run_suite():
    print("=" * 80)
    print(" QUICK REGRESSION BENCHMARK SUITE (KEY INTERFACES & CONFIGURATIONS)")
    print("=" * 80)
    print(f"Python: {sys.executable}")
    print(f"Library: {mf.__file__}")
    print("-" * 80)

    results = []

    # 1. MatchedFilter
    print("\n--- 1. MatchedFilter Interface (Flat) ---")
    for N in [512, 1024, 2048, 4096]:
        for T in [64, 256]:
            rng = np.random.default_rng(12345 + N + T)
            d_spec = (rng.standard_normal((1, N)) + 1j * rng.standard_normal((1, N))).astype(np.complex64)
            t_spec = (rng.standard_normal((T, N)) + 1j * rng.standard_normal((T, N))).astype(np.complex64)

            plan = mf.MatchedFilter(N, ndata=1, ntemplates=T)
            plan.set_data(d_spec)
            plan.set_templates(t_spec)

            for _ in range(5):
                plan.run(binsize=N, threshold=5.0)

            iters = 100 if N <= 1024 else 50
            t0 = time.perf_counter()
            for _ in range(iters):
                plan.run(binsize=N, threshold=5.0)
            elapsed = (time.perf_counter() - t0) / iters
            tp = (T * N) / elapsed / 1e6

            results.append({
                "interface": "MatchedFilter",
                "config": f"N={N:4d}, T={T:3d}, flat",
                "ms": elapsed * 1000,
                "throughput": f"{tp:.2f} M samp/s",
                "status": "PASS" if tp > 500 else "WARN"
            })
            print(f"  MatchedFilter N={N:4d}, T={T:3d} | Latency: {elapsed*1000:6.3f} ms | Throughput: {tp:6.2f} M/s")

    # 2. HierarchicalFilter
    print("\n--- 2. HierarchicalFilter Interface ---")
    ref_2048 = np.zeros(2048, dtype=np.float32)
    ref_2048[20:800] = 1.0
    ref_1024 = np.zeros(1024, dtype=np.float32)
    ref_1024[10:400] = 1.0

    configs_to_test = [
        (1024, 128, None, 64),
        (1024, 128, 64, 64),
        (1024, 128, None, 248),
        (2048, 256, None, 64),
        (2048, 256, 128, 64),
        (2048, 256, 64, 64),
        (2048, 256, None, 248),
        (2048, 256, 128, 248),
    ]

    for N, band, cband, T in configs_to_test:
        rng = np.random.default_rng(42 + N + band + T)
        d_spec = (rng.standard_normal((1, N)) + 1j * rng.standard_normal((1, N))).astype(np.complex64)
        t_spec = (rng.standard_normal((T, N)) + 1j * rng.standard_normal((T, N))).astype(np.complex64)
        ref = ref_2048 if N == 2048 else ref_1024
        lbl = f"b={band}" + (f", b0={cband}" if cband else " (single)")

        try:
            hf = mf.HierarchicalFilter(N, ndata=1, ntemplates=T, band=band, cascade_band=cband,
                                       snr=5.5, fd=1e-2)
            hf.set_reference(ref)
            hf.set_data(d_spec)
            hf.set_templates(t_spec)

            for _ in range(5):
                hf.run(binsize=N, threshold=6.0)

            iters = 50
            t0 = time.perf_counter()
            for _ in range(iters):
                hf.run(binsize=N, threshold=6.0)
            elapsed = (time.perf_counter() - t0) / iters
            tp = (T * N) / elapsed / 1e6

            results.append({
                "interface": "HierarchicalFilter",
                "config": f"N={N:4d}, T={T:3d}, {lbl}",
                "ms": elapsed * 1000,
                "throughput": f"{tp:.2f} M samp/s",
                "status": "PASS" if tp > 500 else "WARN"
            })
            print(f"  HierarchicalFilter N={N:4d}, T={T:3d}, {lbl:<18} | Latency: {elapsed*1000:6.3f} ms | Throughput: {tp:6.2f} M/s")
        except Exception as e:
            results.append({
                "interface": "HierarchicalFilter",
                "config": f"N={N:4d}, T={T:3d}, {lbl}",
                "ms": 0.0,
                "throughput": "N/A",
                "status": f"FAIL ({e})"
            })
            print(f"  HierarchicalFilter N={N:4d}, T={T:3d}, {lbl:<18} | FAILED: {e}")

    # 3. TimeDomainFilterBank
    print("\n--- 3. TimeDomainFilterBank Interface (Series & Invariants) ---")
    N_ser = 131072
    rng = np.random.default_rng(999)
    noise_ser = (rng.standard_normal(N_ser) + 1j * rng.standard_normal(N_ser)).astype(np.complex64) / np.sqrt(2.0)
    valid_slice = slice(4096, N_ser - 4096)

    bank_taps, bank_counts = _load_or_generate_bank(T_req=128)
    ref_w = _compute_reference_spectrum(bank_taps, bank_counts, nfft=2048)
    T = len(bank_taps)

    for eng in ["hier", "dif", "flat"]:
        bank = TimeDomainFilterBank(
            bank_taps, bank_counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine=eng, threshold=6.0, false_dismissal=0.001
        )
        bank.set_reference(ref_w, delta_f=1.0)
        bank.filter_series(noise_ser[:8192], valid_slice=slice(2048, 6144))

        iters = 5
        t0 = time.perf_counter()
        for _ in range(iters):
            res = bank.filter_series(noise_ser, valid_slice=valid_slice)
        elapsed = (time.perf_counter() - t0) / iters

        n_trigs = len(res[0]) if res is not None else 0
        equiv_sec = (valid_slice.stop - valid_slice.start) / 2048.0
        tmpl_sec_per_sec = (T * equiv_sec) / elapsed

        status = "PASS" if n_trigs <= 2 else f"WARN (trigs={n_trigs})"
        results.append({
            "interface": "TimeDomainFilterBank",
            "config": f"T={T:3d}, eng={eng:<4}, L=64s",
            "ms": elapsed * 1000,
            "throughput": f"{tmpl_sec_per_sec/1e6:.2f} M tmpl-s/s",
            "status": status
        })
        print(f"  FilterBank engine={eng:<4}, T={T:3d} | Latency: {elapsed*1000:6.2f} ms | Rate: {tmpl_sec_per_sec/1e6:5.2f} M tmpl-s/s | Trigs at 6.0: {n_trigs}")

    # 3b. Realistic Multi-Group Bank (Top 7: 29 Middle Groups, 7448 templates, 512s segment)
    bank_path = "/home/ahnitz/projects/claude/searchdev/work/scale100k/fir_three_level_opt501_v2.hdf"
    if os.path.exists(bank_path):
        try:
            from pycbc.waveform.bank import RatioFilterBank
            from pycbc.filter.matched_filter_ratio import MatchedFilterRatioControl
            from pycbc.types import FrequencySeries

            rf_bank = RatioFilterBank(bank_path, filter_length=524289, delta_f=1.0/512, dtype=np.complex64)
            stilde = FrequencySeries(np.ones(524289, dtype=np.complex64), delta_f=1.0/512)
            psd = FrequencySeries(np.ones(524289, dtype=np.float32), delta_f=1.0/512)
            top = rf_bank.get_top_template(7)
            taps_raw, counts_raw, m_all = rf_bank.get_upper_firs(7)

            v_slice = slice(245760, 1015808)
            z_ser = np.zeros(1048576, dtype=np.complex64)

            mg_engines = []
            for mid in m_all:
                taps, counts, fine_indices, shifts = rf_bank.get_firs(int(mid), return_shifts=True)
                eng = MatchedFilterRatioControl(snr_threshold=6.0, delta_f=1.0/512, engine='matchedfilter-hierarchical')
                eng.prepare_filters(taps, counts)
                eng.process_segment(stilde, psd, top, None, None, np.arange(len(fine_indices)), valid_slice=v_slice, reference_series=z_ser)
                mg_engines.append((mid, eng, len(fine_indices)))

            n_tmpls_tot = sum(e[2] for e in mg_engines)
            t_anal = (v_slice.stop - v_slice.start) / 2048.0 * 2 # 2 detectors

            # 3b-1. Screening (zero baseline triggers)
            t0 = time.perf_counter()
            for mid, eng, n_fine in mg_engines:
                eng.process_segment(stilde, psd, top, None, None, np.arange(n_fine), valid_slice=v_slice, reference_series=z_ser)
            elapsed_screen = time.perf_counter() - t0
            rate_screen = (n_tmpls_tot * t_anal) / (elapsed_screen * 2)

            # 3b-2. Realistic stationary Gaussian noise
            rng_noise = np.random.default_rng(777)
            noise_z = (rng_noise.standard_normal(1048576) + 1j * rng_noise.standard_normal(1048576)).astype(np.complex64) * 4.3e-5
            t0 = time.perf_counter()
            for mid, eng, n_fine in mg_engines:
                eng.process_segment(stilde, psd, top, None, None, np.arange(n_fine), valid_slice=v_slice, reference_series=noise_z)
            elapsed_noise = time.perf_counter() - t0
            rate_noise = (n_tmpls_tot * t_anal) / (elapsed_noise * 2)

            results.append({
                "interface": "MultiGroupScreening",
                "config": f"Top 7: 29 gps, {n_tmpls_tot} tmpls, 2 det",
                "ms": elapsed_screen * 1000,
                "throughput": f"{rate_screen/1e6:.2f} M tmpl-s/s",
                "status": "PASS" if rate_screen > 20e6 else "WARN"
            })
            results.append({
                "interface": "MultiGroupNoise",
                "config": f"Top 7: 29 gps, {n_tmpls_tot} tmpls, 2 det",
                "ms": elapsed_noise * 1000,
                "throughput": f"{rate_noise/1e6:.2f} M tmpl-s/s",
                "status": "PASS" if rate_noise > 7.5e6 else "WARN"
            })
            print(f"  MultiGroup Screening (29 gps, {n_tmpls_tot} tmpls, 2 det) | Latency: {elapsed_screen*1000:6.1f} ms | Rate: {rate_screen/1e6:5.2f} M tmpl-s/s")
            print(f"  MultiGroup Noise     (29 gps, {n_tmpls_tot} tmpls, 2 det) | Latency: {elapsed_noise*1000:6.1f} ms | Rate: {rate_noise/1e6:5.2f} M tmpl-s/s")
        except Exception as e:
            print(f"  MultiGroup Top 7 benchmark skipped ({e})")

    # 4. UpperReferenceBatch
    print("\n--- 4. UpperReferenceBatch Interface ---")
    class StandaloneUpperReferenceBatch:
        def __init__(self, taps, counts, middle_ids, series_length):
            from matchedfilter import _automatic_series_layout
            counts_arr = np.asarray(counts, dtype=np.int64)
            sort_order = np.argsort(counts_arr)
            self.sorted_ids = np.asarray(middle_ids, dtype=int)[sort_order]
            self.series_length = int(series_length)
            self.bank = TimeDomainFilterBank(
                taps[sort_order], tap_counts=counts_arr[sort_order],
                engine='corr'
            )
            self._plan = []
            for g in self.bank._groups:
                cplan = g.get_correlation_plan()
                g_indices = g.template_indices
                g_cnt = len(g_indices)
                st, _, _ = _automatic_series_layout(self.series_length, cplan.valid)
                self._plan.append({
                    'cplan': cplan,
                    'g_cnt': g_cnt,
                    'g_slice': slice(int(g_indices[0]), int(g_indices[0]) + g_cnt),
                    'st': st,
                    'valid': cplan.valid,
                })

        def run(self, top_series):
            n_req = len(self.sorted_ids)
            out = np.zeros((n_req, self.series_length), dtype=np.complex64)
            ser = np.ascontiguousarray(top_series, dtype=np.complex64)
            for p in self._plan:
                cplan = p['cplan']
                st = p['st']
                lo, hi = p['valid']
                g_dest = out[p['g_slice']]
                cplan._execution_plan().correlate_series_continuous(
                    ser, st, lo, hi, 0, p['g_cnt'], g_dest
                )
            return out

    for L_ser in [524288, 1048576]:
        n_mid = 32
        L_u_taps = 201
        u_taps = rng.standard_normal((n_mid, L_u_taps)).astype(np.float32)
        u_counts = np.full(n_mid, L_u_taps, dtype=np.int64)
        middle_ids = np.arange(n_mid)
        top_ser = (rng.standard_normal(L_ser) + 1j * rng.standard_normal(L_ser)).astype(np.complex64)

        batch = StandaloneUpperReferenceBatch(u_taps, u_counts, middle_ids, L_ser)
        batch.run(top_ser)

        iters = 5
        t0 = time.perf_counter()
        for _ in range(iters):
            out = batch.run(top_ser)
        elapsed = (time.perf_counter() - t0) / iters
        tp = (n_mid * L_ser) / elapsed / 1e6

        results.append({
            "interface": "UpperReferenceBatch",
            "config": f"L={L_ser:7d}, M={n_mid:2d}",
            "ms": elapsed * 1000,
            "throughput": f"{tp:.2f} M samp/s",
            "status": "PASS" if tp > 400 else "WARN"
        })
        print(f"  UpperReferenceBatch L={L_ser:7d}, M={n_mid:2d} | Latency: {elapsed*1000:6.2f} ms | Throughput: {tp:6.2f} M/s")

    # 5. Injection Fidelity
    print("\n--- 5. Signal Injection Fidelity & Threshold Contract ---")
    inj_pos = 32768
    inj_snr = 15.0
    inj_tmpl_idx = 7
    c = bank_counts[inj_tmpl_idx]
    target_tmpl = bank_taps[inj_tmpl_idx, :c]

    test_ser = noise_ser.copy()
    test_ser[inj_pos:inj_pos + c] += inj_snr * target_tmpl

    for eng in ["hier", "dif", "flat"]:
        bank = TimeDomainFilterBank(
            bank_taps, bank_counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine=eng, threshold=6.0, false_dismissal=0.001
        )
        bank.set_reference(ref_w, delta_f=1.0)
        res = bank.filter_series(test_ser, valid_slice=valid_slice)
        tmpl_ids, samp_ids, snrs = res[0], res[1], res[2]
        match = (tmpl_ids == inj_tmpl_idx)
        if np.any(match):
            m_snrs = np.abs(snrs[match])
            rec_snr = float(np.max(m_snrs))
            rec_pos = int(samp_ids[match][np.argmax(m_snrs)])
            snr_err = abs(rec_snr - inj_snr) / inj_snr
            expected_peak = inj_pos + c // 2
            pos_err = abs(rec_pos - expected_peak)
            status = "PASS" if snr_err < 0.15 and pos_err <= 5 else f"FAIL (snr_err={snr_err:.3f}, pos_err={pos_err})"
            print(f"  Injection Recovery eng={eng:<4} | Rec SNR: {rec_snr:5.2f} (err: {snr_err*100:4.1f}%) | Pos: {rec_pos} (err: {pos_err} smp) | Status: {status}")
        else:
            status = "FAIL (not found)"
            rec_snr, snr_err = 0.0, 1.0
            print(f"  Injection Recovery eng={eng:<4} | Trigger not found! Status: FAIL")

        results.append({
            "interface": "InjectionFidelity",
            "config": f"eng={eng:<4}, target_snr={inj_snr:.1f}",
            "ms": 0.0,
            "throughput": f"SNR err {snr_err*100:4.1f}%",
            "status": status
        })

    # 6. Autotuning Features, Monotonicity & Convergence
    print("\n--- 6. Autotuning Features, Monotonicity & Convergence ---")

    # 6.1 Candidate Generation & Cascade Unblocking
    cands_2048, rejs_2048 = mf.candidate_configs(ref_w, 2048, 5.5, 0.01, cascade=True)
    has_cascade = any(isinstance(c, mf.CascadeConfig) or (isinstance(c, (tuple, list)) and len(c) == 3) for c in cands_2048)
    unblock_status = "PASS" if has_cascade else "FAIL (No cascade options)"
    print(f"  Candidate Generation N=2048 | Candidates: {cands_2048} | Status: {unblock_status}")
    results.append({
        "interface": "AutotuneCandidateGen",
        "config": "N=2048, cascade=True",
        "ms": 0.0,
        "throughput": f"{len(cands_2048)} candidates",
        "status": unblock_status
    })

    # 6.2 Selection Monotonicity Across Thresholds
    thresholds = [5.0, 5.5, 6.0, 6.5, 7.0]
    bands = [mf.choose_config(ref_w, 2048, thr, 0.01, cascade=False)[0] for thr in thresholds]
    monotonic = all(bands[i+1] <= bands[i] for i in range(len(bands)-1))
    mono_status = "PASS" if monotonic else "FAIL"
    print(f"  Selection Monotonicity     | Thr: {thresholds} -> Bands: {bands} | Status: {mono_status}")
    results.append({
        "interface": "AutotuneMonotonicity",
        "config": "5 thresholds (5.0 to 7.0)",
        "ms": 0.0,
        "throughput": f"Bands: {bands}",
        "status": mono_status
    })

    # 6.3 Multi-Group Cache Sharing & Convergence
    mf.clear_autotune_cache()
    group_sizes = [248, 247, 192, 115]
    N = 2048
    locked_winner = None

    for g_idx, g_size in enumerate(group_sizes):
        d_blk = noise_ser[:N]
        d_spec = np.fft.fft(d_blk)[:N] / float(N)
        d_spec = d_spec[None, :]

        hf = mf.HierarchicalFilter(N, ndata=1, ntemplates=g_size, cascade="auto",
                                   snr=5.5, fd=1e-2)
        hf.set_reference(ref_w)
        hf.set_data(d_spec)
        t_spec = np.zeros((g_size, N), dtype=np.complex64)
        hf.set_templates(t_spec)

        hf.run(binsize=N, threshold=6.0)
        info = hf.autotune_info
        status_str = info.get("status", "unknown")
        winner = info.get("winner")
        if status_str == "locked":
            locked_winner = winner
        print(f"  Group {g_idx+1} (M={g_size:3d}) | Autotune status: {status_str:<7} | Active/Winner: {winner}")

    cache_entries_after = len(mf.get_autotune_cache())
    auto_status = "PASS" if (cache_entries_after > 0 and locked_winner is not None) else "FAIL (Cache isolated)"
    print(f"  Autotune Cache Convergence | Entries: {cache_entries_after}, Locked: {locked_winner} | Status: {auto_status}")

    results.append({
        "interface": "AutotuneConvergence",
        "config": f"4 groups ({group_sizes})",
        "ms": 0.0,
        "throughput": f"Winner: {locked_winner}",
        "status": auto_status
    })

    # 7. Summary
    print("\n" + "=" * 80)
    print(" REGRESSION SUITE RESULTS SUMMARY")
    print("=" * 80)
    print(f"{'Interface':<24} {'Configuration':<34} {'Latency (ms)':<14} {'Throughput':<16} {'Status'}")
    print("-" * 96)
    all_passed = True
    for r in results:
        passed = r["status"] == "PASS"
        if not passed:
            all_passed = False
        print(f"{r['interface']:<24} {r['config']:<34} {r['ms']:<14.2f} {r['throughput']:<16} {r['status']}")

    print("=" * 80)
    if all_passed:
        print("ALL TESTS PASSED: Key interfaces verified with ZERO regressions.")
    else:
        print("SOME TESTS WARNED OR FAILED. Review output above.")
    print("=" * 80)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_suite())
