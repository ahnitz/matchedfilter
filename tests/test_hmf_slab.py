"""Unit tests for L2-adaptive series slab sizing (ap_hmf_effective_group), 16-lane AVX-512
tier-1024 pair-batch parity, and per-block unpacked sample caching (p->dx) in direct refinement."""
import ctypes

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core, gatechain


@pytest.fixture(params=mf.targets())
def target(request):
    mf.backend()
    mf.set_target(request.param)
    yield request.param
    mf.set_target(None)


def test_effective_group_l2_adaptive_and_hierarchical_policy(monkeypatch):
    """Verify hardware L2-bounded slab group sizing and HierarchicalFilter default policy."""
    monkeypatch.delenv("MF_DGROUP", raising=False)
    lib = ctypes.CDLL(_core.__file__)
    lib.ap_hmf_effective_group.argtypes = [ctypes.c_size_t, ctypes.c_int]
    lib.ap_hmf_effective_group.restype = ctypes.c_int

    for n in (512, 1024, 2048, 4096, 8192):
        grp_auto = lib.ap_hmf_effective_group(n, 0)
        grp_eff = _core.series_group(n, gatechain.default_series_group(n))
        assert grp_auto == grp_eff
        assert grp_auto >= 1
        # Active positive-frequency slab (n * 4 bytes per block) never exceeds 256 KB
        assert grp_auto * n * 4 <= 256 * 1024

        hf = mf.HierarchicalFilter(n, 1, 4, chain=(min(128, n // 2),), device="cpu")
        hf.set_reference(np.ones(n, dtype=np.float32))
        hf.set_coarse_threshold((0.0,))
        assert hf._ensure().series_group() == grp_eff

    monkeypatch.setenv("MF_DGROUP", "16")
    assert _core.series_group(2048, gatechain.default_series_group(2048)) == 16
    hf16 = mf.HierarchicalFilter(2048, 1, 4, chain=(256,), device="cpu")
    hf16.set_reference(np.ones(2048, dtype=np.float32))
    hf16.set_coarse_threshold((0.0,))
    assert hf16._ensure().series_group() == 16


def test_tier_b1024_pairbatch_matches_balanced(target, monkeypatch):
    """Verify 3-tier (256, 512, 1024) HMF with default pblim=1024 on 16-lane AVX-512 matches
    MF_PBMAX=128 balanced execution across strided real series runs."""
    rng = np.random.default_rng(20261101)
    n, nt, nblocks = 2048, 35, 34
    step = n - 256
    S = nblocks * step + n
    packed = np.empty(S + 1, dtype=np.complex64)
    packed.real[:S] = rng.standard_normal(S).astype(np.float32)
    packed.imag[:S] = rng.standard_normal(S).astype(np.float32)
    packed[-1] = 0.0
    imag_buf = packed.view(np.float32)[1 : 2 * S + 1]
    spec = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    spec /= np.sqrt(np.sum(np.abs(spec) ** 2, axis=1, keepdims=True) / n)

    starts = (np.arange(nblocks) * step).astype(np.uint64)
    ws = np.full(nblocks, 128, dtype=np.uint64)
    we = np.full(nblocks, n - 128, dtype=np.uint64)
    binsize = 512

    results = []
    for pbmax in (None, "128"):
        if pbmax is None:
            monkeypatch.delenv("MF_PBMAX", raising=False)
        else:
            monkeypatch.setenv("MF_PBMAX", pbmax)
        p = _core.HMF(n, 32, nt, [256, 512, 1024], 32, n)
        assert p.set_real_series(True, 2)
        p.set_reference(np.ones(n, dtype=np.float32))
        p.set_template_batch(0, spec)
        p.set_thresholds([1.8, 2.1, 2.4])
        nb = p.nbins(binsize, 128, n - 128)
        idx = np.full((nblocks, nt, nb), -1, dtype=np.int64)
        val = np.zeros((nblocks, nt, nb), dtype=np.complex64)
        mag = np.zeros((nblocks, nt, nb), dtype=np.float32)
        cnt = np.zeros((nblocks, nt), dtype=np.int32)
        tot = p.run_series(
            imag_buf, starts, ws, we, 0, nt, binsize, 2.7, idx, val, mag, cnt
        )
        tstats = p.tier_stats()
        assert tstats[1][1] >= 20
        results.append((tot, cnt, idx, val))

    tot_def, cnt_def, idx_def, val_def = results[0]
    tot_bal, cnt_bal, idx_bal, val_bal = results[1]
    assert tot_def == tot_bal
    np.testing.assert_array_equal(cnt_def, cnt_bal)
    np.testing.assert_array_equal(idx_def, idx_bal)
    np.testing.assert_allclose(val_def, val_bal, rtol=2e-5, atol=2e-5)


@pytest.mark.parametrize("tap_complex", [False, True])
@pytest.mark.parametrize("nbins_target", [1, 3])
def test_direct_refine_dx_cache_across_same_block_survivors(target, tap_complex, nbins_target):
    """Verify unpacked p->dx span reuse, left/right extension, disjoint replacement, and ragged
    zero-padding across multiple direct-refine survivors in the same block d."""
    rng = np.random.default_rng(8800 + int(tap_complex) * 17 + nbins_target)
    n = 2048
    nt = 10
    L_max = 129
    # Vary tap lengths and inject impulses at distinct lags inside block 0 and ragged block 2
    # so consecutive survivors in the same block exercise:
    #   t=0,1: identical window
    #   t=2:   subset window (smaller tap length around same lag)
    #   t=3:   left-extended window (earlier lag overlapping [dx_lo, dx_hi))
    #   t=4:   right-extended window (later lag overlapping [dx_lo, dx_hi))
    #   t=5:   disjoint window far away in the same block (replaces [dx_lo, dx_hi))
    #   t=6..9: overlapping/extending windows near the ragged end of block 2 (s_max > have)
    tap_counts = np.array([97, 97, 49, 113, 113, 81, 97, 129, 65, 113], dtype=np.int64)
    if tap_complex:
        taps = np.zeros((nt, L_max), dtype=np.complex64)
    else:
        taps = np.zeros((nt, L_max), dtype=np.float32)

    for t in range(nt):
        L = int(tap_counts[t])
        if tap_complex:
            row = (rng.standard_normal(L) + 1j * rng.standard_normal(L)).astype(np.complex64)
        else:
            row = rng.standard_normal(L).astype(np.float32)
        row /= np.linalg.norm(row)
        taps[t, :L] = row

    specs = np.empty((nt, n), dtype=np.complex64)
    for t in range(nt):
        L = int(tap_counts[t])
        c = L // 2
        ker = np.zeros(n, dtype=np.complex64)
        for u in range(L):
            val = np.conj(taps[t, u]) if tap_complex else taps[t, u]
            ker[(c - u) % n] = np.conj(val)
        specs[t] = np.fft.fft(ker).astype(np.complex64)

    step = 1536
    S = 2 * step + n - 180
    packed = np.zeros(S + 1, dtype=np.complex64)
    packed.real[:S] = rng.standard_normal(S).astype(np.float32)
    packed.imag[:S] = rng.standard_normal(S).astype(np.float32) * 0.25

    lag_targets_b0 = [420, 420, 420, 404, 438, 1260]
    for idx_t, lag in enumerate(lag_targets_b0):
        L = int(tap_counts[idx_t])
        c = L // 2
        sig = np.real(taps[idx_t, :L])
        packed.imag[lag - c : lag - c + L] += 18.0 * sig

    lag_targets_b2 = [1820, 1835, 1828, 1850]
    for k_i, lag in enumerate(lag_targets_b2):
        idx_t = 6 + k_i
        L = int(tap_counts[idx_t])
        c = L // 2
        s0 = 2 * step + lag - c
        avail = max(0, min(L, S - s0))
        if avail > 0:
            packed.imag[s0 : s0 + avail] += 18.0 * np.real(taps[idx_t, :avail])

    imag_buf = packed.view(np.float32)[1 : 2 * S + 1]
    starts = np.array([0, step, 2 * step], dtype=np.uint64)
    ws = np.full(3, 128, dtype=np.uint64)
    we = np.full(3, n - 128, dtype=np.uint64)
    span = n - 256
    binsize = span if nbins_target == 1 else (span + nbins_target - 1) // nbins_target

    def make_plan():
        p = _core.HMF(n, 8, nt, [256, 512], 8, n)
        assert p.set_real_series(True, 2)
        p.set_reference(np.ones(n, dtype=np.float32))
        p.set_template_batch(0, specs)
        p.set_taps(taps, L_max, tap_counts, tap_complex)
        p.set_thresholds([1.5, 1.8])
        assert p.set_direct(True, 2)
        assert p.set_direct_prices(1e-9, 1e9)
        return p

    # 1. Batched run across all nt templates (reuses/extends/replaces p->dx within each block d)
    p_all = make_plan()
    nb = p_all.nbins(binsize, 128, n - 128)
    idx_all = np.full((3, nt, nb), -1, dtype=np.int64)
    val_all = np.zeros((3, nt, nb), dtype=np.complex64)
    mag_all = np.zeros((3, nt, nb), dtype=np.float32)
    cnt_all = np.zeros((3, nt), dtype=np.int32)
    tot_all = p_all.run_series(
        imag_buf, starts, ws, we, 0, nt, binsize, 2.5, idx_all, val_all, mag_all, cnt_all
    )
    assert p_all.direct_stats()["pairs"] >= 8

    # 2. Single-template isolated runs (nt=1 per call -> no cross-template p->dx reuse in block d)
    tot_iso = 0
    for t in range(nt):
        p_one = make_plan()
        idx_1 = np.full((3, 1, nb), -1, dtype=np.int64)
        val_1 = np.zeros((3, 1, nb), dtype=np.complex64)
        mag_1 = np.zeros((3, 1, nb), dtype=np.float32)
        cnt_1 = np.zeros((3, 1), dtype=np.int32)
        tot_iso += p_one.run_series(
            imag_buf, starts, ws, we, t, 1, binsize, 2.5, idx_1, val_1, mag_1, cnt_1
        )
        np.testing.assert_array_equal(cnt_all[:, t], cnt_1[:, 0])
        np.testing.assert_array_equal(idx_all[:, t, :], idx_1[:, 0, :])
        np.testing.assert_array_equal(val_all[:, t, :], val_1[:, 0, :])
        np.testing.assert_array_equal(mag_all[:, t, :], mag_1[:, 0, :])
    assert tot_all == tot_iso
