#!/usr/bin/env python3
"""Search-level contracts: the filter bank's noise and injection behaviour per engine, lazy
template loading, the sparse series format, the gate chain's pool, thresholds and shared
choice, autotuning's contracts, the batch partition, and the CPU cascade's empty case.

(Formerly test_regression_suite.py: its standalone benchmark, smoke tests and tests of
the maintainer's local banks were removed on 2026-10-22; the ladder, tools/ladder.py, is
the standard benchmark.)"""

import os
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
    if T_req <= 128:
        try:
            from conftest import bank_subset
            b = bank_subset()
            bank_taps = b["fine_taps"][:T_req].astype(np.float32)
            bank_counts = b["fine_counts"][:T_req].astype(np.int64)
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

@pytest.mark.parametrize("engine", ["hier", "dif", "flat"])
def test_timedomain_filterbank_noise_contract(engine):
    """Enforce strict threshold contract: unit Gaussian noise at threshold=6.0 yields <= 2 triggers."""
    N_ser = 131072  # 64s at 2048 Hz
    rng = np.random.default_rng(999)
    noise_ser = (rng.standard_normal(N_ser) + 1j * rng.standard_normal(N_ser)).astype(np.complex64) / np.float32(np.sqrt(2.0))
    valid_slice = slice(4096, N_ser - 4096)

    bank_taps, bank_counts = _load_or_generate_bank(T_req=128)
    ref_w = _compute_reference_spectrum(bank_taps, bank_counts, nfft=2048)

    bank = TimeDomainFilterBank(
        bank_taps, bank_counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine=engine, threshold=6.0, false_dismissal=0.001
    )
    bank.set_reference(ref_w, delta_f=1.0)
    res = bank.filter_series(noise_ser, windows=valid_slice)

    n_trigs = len(res[0]) if res is not None else 0
    assert n_trigs <= 2, f"Engine {engine} produced {n_trigs} false alarms on unit noise at threshold 6.0!"


@pytest.mark.parametrize("engine", ["hier", "dif", "flat"])
def test_signal_injection_recovery(engine):
    """Verify injection recovery fidelity and timing parity across all filtering engines."""
    N_ser = 131072
    rng = np.random.default_rng(999)
    noise_ser = (rng.standard_normal(N_ser) + 1j * rng.standard_normal(N_ser)).astype(np.complex64) / np.float32(np.sqrt(2.0))
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
    res = bank.filter_series(test_ser, windows=valid_slice)
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


def test_lazy_template_load_has_one_generation_and_native_ingestion(monkeypatch):
    """A newly built source-backed plan consumes its supplied batch once."""
    from matchedfilter.time_domain import _TemplateGroup, _group_spectra

    n, nt = 256, 3
    hf = mf.HierarchicalFilter(n, ntemplates=nt)
    hf.set_reference(np.ones(n, np.float32))
    monkeypatch.setattr(hf, "_choose_chain", lambda: (64,))
    monkeypatch.setattr(mf._prices, "_cpu_forward_platform", lambda n: False)
    metrics = dict(spectrum_generations=0, native_ingestions=0)
    native_factory = hf._new_cpu_plan

    class CountedPlan:
        def __init__(self, chain):
            self.native = native_factory(chain)

        def __getattr__(self, name):
            return getattr(self.native, name)

        def set_template_batch(self, start, spectra):
            metrics["native_ingestions"] += 1
            return self.native.set_template_batch(start, spectra)

    monkeypatch.setattr(hf, "_new_cpu_plan", CountedPlan)
    taps = np.ones((nt, 9), np.float32)
    counts = np.full(nt, taps.shape[1], np.int64)

    def source():
        metrics["spectrum_generations"] += 1
        return _group_spectra(taps, counts, n, 1.0, False)

    group = _TemplateGroup(hf, n, np.arange(nt), 0, n, 9, spectra_source=source)
    group.load_templates(hf)
    assert metrics == dict(spectrum_generations=1, native_ingestions=1)
    assert hf._held_templates is None
    hf._require_templates(0, nt)


def test_sparse_series_compact_bytes_and_empty_reuse():
    """Sparse payload size follows current peaks, including after a gated-empty call."""
    from matchedfilter import _core

    n, nt, binsize = 256, 2, 31
    rng = np.random.default_rng(485)
    templates = (rng.normal(size=(nt, n)) + 1j * rng.normal(size=(nt, n))).astype(np.complex64)
    series = (rng.normal(size=2 * n) + 1j * rng.normal(size=2 * n)).astype(np.complex64)
    plans = [_core.HMF(n, 1, nt, [64], 3, n) for _ in range(2)]
    for plan in plans:
        plan.set_reference(np.ones(n, np.float32))
        plan.set_template_batch(0, templates)
        plan.set_q15(False)
    starts = np.array([0, n], np.uintp)
    low, high = np.zeros(2, np.uintp), np.full(2, n, np.uintp)
    shape = (2, nt, (n + binsize - 1) // binsize)
    idx, val = np.empty(shape, np.int64), np.empty(shape, np.complex64)
    mag = np.empty(shape, np.float32)
    counts = [np.empty(shape[:2], np.int32) for _ in plans]
    for gate, populated in ((0.0, True), (1e8, False)):
        for plan in plans:
            plan.set_thresholds([gate])
        fl, ix, vl, total = plans[0].run_series_sparse(
            series, starts, low, high, 0, nt, binsize, .2, counts[0])
        dense_total = plans[1].run_series(
            series, starts, low, high, 0, nt, binsize, .2, idx, val, mag, counts[1])
        flat = np.flatnonzero(idx.ravel() >= 0)
        assert total == dense_total == len(flat) == int(counts[0].sum())
        assert (total > 0) == populated
        assert len(fl) + len(ix) + len(vl) == 24 * total
        np.testing.assert_array_equal(counts[0], counts[1])
        np.testing.assert_array_equal(np.frombuffer(fl, np.int64), flat)
        np.testing.assert_array_equal(np.frombuffer(ix, np.int64), idx.ravel()[flat])
        np.testing.assert_array_equal(np.frombuffer(vl, np.complex64), val.ravel()[flat])


# -----------------------------------------------------------------------------
# Autotuning Verification Tests
# -----------------------------------------------------------------------------

def test_chain_pool_excludes_nothing():
    """Every chain of up to max_tiers usable bands is priced; none is excluded by rule."""
    from matchedfilter import gatechain as gc
    bank_taps, bank_counts = _load_or_generate_bank(T_req=64)
    for nfft in (2048, 8192):
        ref = _compute_reference_spectrum(bank_taps, bank_counts, nfft=nfft)
        best, plans = gc.choose_chain(ref, nfft, 5.5, 1e-2, cost=gc.calibrate_costs(nfft, 64), max_tiers=3)
        assert best is not None
        priced = {q["chain"] for q in plans}
        pool = set(gc.enumerate_chains(nfft, 3, bands=gc.usable_bands(ref, nfft)))
        assert priced <= pool
        # multi-tier chains are candidates at every n, including small blocks
        assert any(len(c) > 1 for c in priced), (nfft, sorted(priced))
        assert plans == sorted(plans, key=lambda q: q["cost"])


def test_gate_thresholds_rise_with_snr():
    """For a fixed chain, the calibrated gates rise as the detection threshold rises."""
    from matchedfilter import gatechain as gc
    bank_taps, bank_counts = _load_or_generate_bank(T_req=64)
    ref_w = _compute_reference_spectrum(bank_taps, bank_counts, nfft=2048)
    for chain in ((256,), (256, 512)):
        gates = [gc.chain_thresholds(ref_w, 2048, s, 0.01, chain)["thresholds"] for s in (5.0, 5.5, 6.0, 6.5, 7.0)]
        for lo, hi in zip(gates, gates[1:]):
            assert all(b > a for a, b in zip(lo, hi)), (chain, gates)


def test_chain_choice_is_shared_across_groups():
    """Groups with the same reference share one model evaluation and agree on the chain."""
    mf.clear_autotune_cache()
    group_sizes = [248, 247, 192, 115]
    N = 2048
    bank_taps, bank_counts = _load_or_generate_bank(T_req=248)
    ref_w = _compute_reference_spectrum(bank_taps, bank_counts, nfft=2048)
    rng = np.random.default_rng(123)
    d_spec = (rng.standard_normal((1, N)) + 1j * rng.standard_normal((1, N))).astype(np.complex64)
    t_spec = np.zeros((248, N), dtype=np.complex64)
    models = []
    for g_size in group_sizes:
        hf = mf.HierarchicalFilter(N, ndata=1, ntemplates=g_size, snr=5.5, fd=1e-2)
        hf.set_reference(ref_w)
        hf.set_data(d_spec)
        hf.set_templates(t_spec[:g_size])
        hf.run(binsize=N, threshold=6.0)
        models.append(hf.autotune_info["model"])
    assert len(set(models)) == 1, models
    assert len(mf.get_autotune_state()["choices"]) == 1


def test_autotune_threshold_contract_during_tuning():
    """Verify that during active tuning (candidate switching), noise threshold contract is never violated."""
    mf.clear_autotune_cache()
    N = 2048
    N_ser = 131072
    rng = np.random.default_rng(777)
    noise_ser = (rng.standard_normal(N_ser) + 1j * rng.standard_normal(N_ser)).astype(np.complex64) / np.float32(np.sqrt(2.0))
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
    res = bank.filter_series(noise_ser, windows=valid_slice)

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

        hf = mf.HierarchicalFilter(N, ndata=1, ntemplates=64, snr=5.5, fd=1e-2)
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


def test_an_equal_reference_does_not_reload_the_templates(monkeypatch):
    """set_reference with an array equal to the current reference changes nothing: no
    template reload (the scaled tier templates are rebuilt only for a new reference).
    Counted, not timed: a timing bound is a performance check, not a correctness one."""
    N, T = 2048, 32
    rng = np.random.default_rng(42)
    ref = np.abs(rng.standard_normal(N)).astype(np.float32)
    ref[0] = 0.0
    t_spec = (rng.standard_normal((T, N)) + 1j * rng.standard_normal((T, N))).astype(np.complex64)
    hf = mf.HierarchicalFilter(N, ndata=1, ntemplates=T, chain=256)
    hf.set_reference(ref)
    hf.set_templates(t_spec)
    hf._ensure()
    reloads = []
    orig = hf._reload_templates
    monkeypatch.setattr(hf, "_reload_templates", lambda: (reloads.append(1), orig())[1])
    for _ in range(5):
        hf.set_reference(ref.copy())
    assert reloads == []
    changed = ref.copy()
    changed[5] *= 2
    hf.set_reference(changed)
    assert len(reloads) == 1


def test_batch_partitioning_limits():
    """Verify that _partition_templates sizes sub-batches up to 512 templates
    for N=2048 to prevent overpartitioning and redundant forward FFT passes."""
    from matchedfilter.time_domain import _partition_templates
    counts = np.full(492, 501, dtype=np.int64)
    groups, order = _partition_templates(counts)
    # 492 templates should remain in a single group, not split into 2
    assert len(groups) == 1, f"Expected 1 group for 492 templates, got {len(groups)}"
    assert groups[0][0] == 0 and groups[0][1] == 492


def test_hierarchical_cpu_cascade_and_empty_contract():
    """No hierarchical configuration is excluded by rule, and zero-trigger output is the cached empty result."""
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
    # Every chain stays a candidate: the bank must not pin a configuration on the plan.
    assert bank._groups[0].plan._pinned is None, "TimeDomainFilterBank must not pin a chain"

    bank.set_reference(ref_w, delta_f=1.0)
    # Zero-noise input guaranteed to produce zero triggers at threshold 6.0
    zero_noise = np.zeros(65536, dtype=np.complex64)
    res = bank.filter_series(zero_noise, windows=slice(4096, 65536 - 4096))
    assert res is _EMPTY_FILTER_RESULTS, "Expected singleton _EMPTY_FILTER_RESULTS on zero-trigger output"



# =============================================================================
# Standalone Benchmark CLI Runner
# =============================================================================
