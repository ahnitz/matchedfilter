"""The listed Q15 screen (ap_mf_q15_pairs) decides each listed pair exactly as the dense screen
decides it: same pass bit and same maximum, at every band, for lists that span several data
slabs and template groups, partial batches, with and without the margin, and after data and
templates change."""
import ctypes as C

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core


@pytest.fixture(scope="module")
def lib():
    lib = C.CDLL(_core.__file__)
    P, I, Z, F = C.c_void_p, C.c_int, C.c_size_t, C.c_float
    for name, args, res in (
            ("ap_mf_create_pairbatch", [Z, I, I], P), ("ap_mf_create", [Z, I, I], P),
            ("ap_mf_destroy", [P], None), ("ap_mf_set_data", [P, I, P], I),
            ("ap_mf_set_template", [P, I, P], I), ("ap_mf_q15_lanes", [P], I),
            ("ap_mf_set_q15_margin", [P, I], I),
            ("ap_mf_q15_screen", [P, I, I, I, I, F, Z, Z, P, P], I),
            ("ap_mf_q15_pairs", [P, I, P, P, I, I, F, Z, Z, P, P], I),
            ("ap_mf_q15_pairs_lag", [P, I, P, P, I, I, F, Z, Z, P, P, P], I),
            ("ap_mf_run", [P, I, I, I, I, Z, F, P, P, Z, Z], I),
            ("ap_mf_run_pairs_packed", [P, I, P, P, I, I, Z, F, P, Z, Z], I)):
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = args, res
    return lib


def _rows(rng, k, m):
    return np.ascontiguousarray((rng.standard_normal((k, m, 2)) / 8).astype(np.float32))


@pytest.fixture(params=mf.targets())
def target(request):
    mf.backend()
    mf.set_target(request.param)
    yield request.param
    mf.set_target(None)


@pytest.mark.parametrize("m", [256, 512, 1024])
@pytest.mark.parametrize("pairbatch", [True, False])
@pytest.mark.parametrize("margin", [True, False])
def test_listed_screen_matches_dense(lib, target, m, pairbatch, margin):
    nd, nt = 70, 101                  # three data slabs at 32 lanes; groups need not fill
    rng = np.random.default_rng(m + 7 * pairbatch + margin)
    p = (lib.ap_mf_create_pairbatch if pairbatch else lib.ap_mf_create)(m, nd, nt)
    assert p
    try:
        if lib.ap_mf_q15_lanes(p) <= 0:
            pytest.skip("no Q15 screen on this target")
        lib.ap_mf_set_q15_margin(p, int(margin))
        D, T = _rows(rng, nd, m), _rows(rng, nt, m)
        D[5] *= 40                       # a loud block: its pairs pass
        lo, hi, thr = int(m * .09), int(m * .9), 2.4
        for rnd in range(2):
            for d in range(nd):
                assert lib.ap_mf_set_data(p, d, D[d].ctypes.data) == 0
            for t in range(nt):
                assert lib.ap_mf_set_template(p, t, T[t].ctypes.data) == 0
            dense_pass = np.zeros(nd * nt, np.uint8)
            dense_stat = np.zeros(nd * nt, np.float32)
            lib.ap_mf_q15_screen(p, 0, nd, 0, nt, C.c_float(thr), lo, hi,
                                 dense_pass.ctypes.data, dense_stat.ctypes.data)
            assert 0 < dense_pass.sum() < nd * nt
            for frac in (0.004, 0.08, 0.6):
                sel = np.sort(rng.choice(nd * nt, max(1, int(frac * nd * nt)), replace=False))
                ds, ts = (np.ascontiguousarray(x, np.int32) for x in np.divmod(sel, nt))
                lp = np.full(len(sel), 7, np.uint8)
                ls = np.zeros(len(sel), np.float32)
                got = lib.ap_mf_q15_pairs(p, 0, ds.ctypes.data, ts.ctypes.data, len(sel), 0,
                                          C.c_float(thr), lo, hi, lp.ctypes.data, ls.ctypes.data)
                assert got == int(lp.sum())
                np.testing.assert_array_equal(lp, dense_pass[sel])
                np.testing.assert_array_equal(ls, dense_stat[sel])
            # the next round's inputs differ: the slab copies and quantised rows must follow
            D[rng.integers(nd, size=9)] *= -1.5
            T[rng.integers(nt, size=9)] *= .5
    finally:
        lib.ap_mf_destroy(p)


def test_listed_screen_rejects_out_of_range_pairs(lib):
    p = lib.ap_mf_create_pairbatch(256, 4, 8)
    try:
        if lib.ap_mf_q15_lanes(p) <= 0:
            pytest.skip("no Q15 screen on this target")
        ds = np.array([0, 4], np.int32)
        ts = np.array([0, 1], np.int32)
        out = np.zeros(2, np.uint8)
        assert lib.ap_mf_q15_pairs(p, 0, ds.ctypes.data, ts.ctypes.data, 2, 0,
                                   C.c_float(1.0), 0, 256, out.ctypes.data, None) == -1
    finally:
        lib.ap_mf_destroy(p)


@pytest.mark.parametrize("m", [64, 128, 256, 512, 1024])
def test_listed_screen_lag_election_and_zero_nan_scales(lib, target, m):
    nd, nt = 6, 20
    rng = np.random.default_rng(1000 + m)
    p = lib.ap_mf_create_pairbatch(m, nd, nt)
    assert p
    try:
        if lib.ap_mf_q15_lanes(p) <= 0:
            pytest.skip("no Q15 screen on this target")
        lib.ap_mf_set_q15_margin(p, 0)
        D = _rows(rng, nd, m)
        T = _rows(rng, nt, m)
        # Inject clear peaks at known lags on blocks 0..2
        k = np.arange(m, dtype=np.float64)
        lags_true = [m // 4 + 3, m // 2 - 5, 3 * m // 4 + 1]
        for b, lag in enumerate(lags_true):
            tc = T[b, :, 0] + 1j * T[b, :, 1]
            sig = 12.0 * tc * np.exp(-2j * np.pi * k * lag / m)
            D[b, :, 0] += sig.real.astype(np.float32)
            D[b, :, 1] += sig.imag.astype(np.float32)
        D[3] = 0.0                  # exact zero data block
        D[4, 0, 0] = np.nan         # non-finite data block (must fail open)
        T[nt - 1] = 0.0             # exact zero template
        for d in range(nd):
            assert lib.ap_mf_set_data(p, d, D[d].ctypes.data) == 0
        for t in range(nt):
            assert lib.ap_mf_set_template(p, t, T[t].ctypes.data) == 0
        ds = np.array([0, 1, 2, 3, 4, 0], np.int32)
        ts = np.array([0, 1, 2, 0, 0, nt - 1], np.int32)
        lp = np.zeros(len(ds), np.uint8)
        ls = np.zeros(len(ds), np.float32)
        li = np.full(len(ds), -99, np.int16)
        lo, hi = m // 8, m - m // 8
        got = lib.ap_mf_q15_pairs_lag(p, 0, ds.ctypes.data, ts.ctypes.data, len(ds), 0,
                                      C.c_float(2.0), lo, hi,
                                      lp.ctypes.data, ls.ctypes.data, li.ctypes.data)
        assert got == int(lp.sum())
        assert list(lp[:3]) == [1, 1, 1]
        assert list(li[:3]) == lags_true
        # Exact-zero data (pair 3) and exact-zero template (pair 5) reject at threshold > 0
        assert lp[3] == 0 and ls[3] == 0.0 and li[3] == -1
        assert lp[5] == 0 and ls[5] == 0.0 and li[5] == -1
        # Non-finite data (pair 4) fails open with stat == -1.0 and lag_idx == -1
        assert lp[4] == 1 and ls[4] == -1.0 and li[4] == -1
        # At threshold == 0.0, exact-zero rows pass
        got0 = lib.ap_mf_q15_pairs_lag(p, 0, ds.ctypes.data, ts.ctypes.data, len(ds), 0,
                                       C.c_float(0.0), lo, hi,
                                       lp.ctypes.data, ls.ctypes.data, li.ctypes.data)
        assert got0 == len(ds) and np.all(lp == 1)
    finally:
        lib.ap_mf_destroy(p)


def test_deferred_tmre_q15_then_sparse_fp32_and_template_update(lib, target):
    """Pairbatch plans defer tmre/tmim allocation during Q15 quantisation/screening and
    materialize tmre/tmim lazily on first sparse FP32 pair evaluation without drift."""
    m, nd, nt = 256, 5, 19            # nt not a multiple of pairbatch width
    rng = np.random.default_rng(7719)
    p = lib.ap_mf_create_pairbatch(m, nd, nt)
    assert p
    try:
        D = _rows(rng, nd, m)
        T = _rows(rng, nt, m)
        for d in range(nd):
            assert lib.ap_mf_set_data(p, d, D[d].ctypes.data) == 0
        for t in range(nt):
            assert lib.ap_mf_set_template(p, t, T[t].ctypes.data) == 0
        lo, hi = 16, m - 16
        if lib.ap_mf_q15_lanes(p) > 0:
            qpass = np.zeros(nd * nt, np.uint8)
            qstat = np.zeros(nd * nt, np.float32)
            assert lib.ap_mf_q15_screen(p, 0, nd, 0, nt, C.c_float(1.5), lo, hi,
                                        qpass.ctypes.data, qstat.ctypes.data) >= 0

        # Dense FP32 reference vs sparse packed FP32 (which triggers lazy mf_ensure_tm)
        ap_peak_dt = np.dtype([("index", np.int64), ("value", np.complex64),
                               ("magnitude", np.float32)], align=True)
        dense_pk = np.empty((nd, nt), ap_peak_dt)
        assert lib.ap_mf_run(p, 0, nd, 0, nt, m, C.c_float(0.0),
                             dense_pk.ctypes.data, None, lo, hi) >= 0
        sel = np.array([0, 3, 18, 19, 25, 44, 71, 94], np.int64)
        ds, ts = (np.ascontiguousarray(x, np.int32) for x in np.divmod(sel, nt))
        sparse_pk = np.empty(len(sel), ap_peak_dt)
        assert lib.ap_mf_run_pairs_packed(p, 0, ds.ctypes.data, ts.ctypes.data, len(sel),
                                          0, m, C.c_float(0.0), sparse_pk.ctypes.data, lo, hi) == 1
        ref_pk = dense_pk.reshape(-1)[sel]
        np.testing.assert_array_equal(sparse_pk["index"], ref_pk["index"])
        np.testing.assert_allclose(sparse_pk["value"], ref_pk["value"], rtol=2e-5, atol=2e-5)

        # Overwrite templates after tmre/tmim has been materialized and verify sync
        T2 = _rows(rng, nt, m)
        for t in range(nt):
            assert lib.ap_mf_set_template(p, t, T2[t].ctypes.data) == 0
        assert lib.ap_mf_run(p, 0, nd, 0, nt, m, C.c_float(0.0),
                             dense_pk.ctypes.data, None, lo, hi) >= 0
        assert lib.ap_mf_run_pairs_packed(p, 0, ds.ctypes.data, ts.ctypes.data, len(sel),
                                          0, m, C.c_float(0.0), sparse_pk.ctypes.data, lo, hi) == 1
        ref_pk2 = dense_pk.reshape(-1)[sel]
        np.testing.assert_array_equal(sparse_pk["index"], ref_pk2["index"])
        np.testing.assert_allclose(sparse_pk["value"], ref_pk2["value"], rtol=2e-5, atol=2e-5)
    finally:
        lib.ap_mf_destroy(p)
