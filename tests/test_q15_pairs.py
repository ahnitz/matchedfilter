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
            ("ap_mf_q15_pairs", [P, I, P, P, I, I, F, Z, Z, P, P], I)):
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
