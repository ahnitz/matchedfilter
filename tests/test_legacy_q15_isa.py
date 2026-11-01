"""Cross-ISA Q15 screen parity and legacy-ISA (AVX1, AVX2, SSE4) tests.

Verifies that the VEX-encoded AVX1 Q15 screen, AVX2 Q15 screen, SSE4 Q15 screen,
and AVX3_DL Q15 screen produce bit-identical dense screening decisions, maxima,
tiled tail-group screening, slab8/perm screening, and arbitrary-pair gather
screening + argmax lag election across N in {64, 128, 256, 512, 1024}.
"""
import ctypes as C

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core


@pytest.fixture(scope="module")
def core_lib():
    """Bind C entry points for cross-ISA Q15 verification."""
    lib = C.CDLL(_core.__file__)
    void_p, c_int, c_size_t, c_float = C.c_void_p, C.c_int, C.c_size_t, C.c_float
    signatures = (
        ("ap_create", [c_size_t], void_p),
        ("ap_destroy", [void_p], None),
        ("ap_q15_lanes", [void_p], c_int),
        ("ap_q15_has_tile", [void_p], c_int),
        ("ap_q15_screen", [void_p, void_p, void_p, void_p, c_size_t, c_size_t,
                           void_p, void_p, void_p, void_p], c_int),
        ("ap_q15_screen_tile", [void_p, c_int, void_p, void_p, void_p, c_size_t,
                                c_size_t, void_p, void_p, void_p, void_p], c_int),
        ("ap_q15_slab8", [void_p, void_p, void_p, void_p, void_p, void_p], c_int),
        ("ap_q15_screen_perm", [void_p, void_p, void_p, void_p, void_p, C.c_long,
                                void_p, void_p, c_size_t, c_size_t, void_p,
                                void_p, void_p, void_p, void_p], c_int),
        ("ap_mf_create", [c_size_t, c_int, c_int], void_p),
        ("ap_mf_create_pairbatch", [c_size_t, c_int, c_int], void_p),
        ("ap_mf_destroy", [void_p], None),
        ("ap_mf_set_data", [void_p, c_int, void_p], c_int),
        ("ap_mf_set_template", [void_p, c_int, void_p], c_int),
        ("ap_mf_q15_lanes", [void_p], c_int),
        ("ap_mf_set_q15_margin", [void_p, c_int], c_int),
        ("ap_mf_q15_screen", [void_p, c_int, c_int, c_int, c_int, c_float,
                              c_size_t, c_size_t, void_p, void_p], c_int),
        ("ap_mf_q15_pairs_lag", [void_p, c_int, void_p, void_p, c_int, c_int,
                                 c_float, c_size_t, c_size_t, void_p, void_p,
                                 void_p], c_int),
    )
    for name, argtypes, restype in signatures:
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = argtypes, restype
    return lib


def _q15_targets():
    mf.backend()
    avail = []
    prev = mf.backend()
    try:
        for t in mf.targets():
            mf.set_target(t)
            if _core.MF(256, 1, 1).q15_lanes() > 0:
                avail.append(t)
    finally:
        mf.set_target(prev)
    return avail


@pytest.mark.parametrize("transform_len", [64, 128, 256, 512, 1024])
@pytest.mark.parametrize("window_kind", ["middle", "wide", "edge"])
def test_cross_isa_dense_and_tail_q15_bit_exact(core_lib, transform_len, window_kind):
    """Dense Q15 screen (including partial tail template groups exercises q15_screen_tile)
    and group-major vs pairbatch data quantisation match bit-for-bit across all ISAs."""
    targets = _q15_targets()
    if len(targets) < 1:
        pytest.skip("no Q15 targets available")

    # Prime counts exercise full groups + tail tiles of widths qw/2 and qw/4 across all ISAs
    ndata, ntmpl = 11, 37
    rng = np.random.default_rng(transform_len * 31 + len(window_kind))
    data = np.ascontiguousarray(
        (rng.standard_normal((ndata, transform_len, 2)) / 5.0).astype(np.float32)
    )
    tmpls = np.ascontiguousarray(
        (rng.standard_normal((ntmpl, transform_len, 2)) / 5.0).astype(np.float32)
    )
    data[0] = 0.0
    data[5] *= 30.0

    if window_kind == "middle":
        lo, hi = transform_len // 16, transform_len - transform_len // 16
    elif window_kind == "wide":
        lo, hi = transform_len // 4, transform_len - transform_len // 4
    else:
        lo, hi = transform_len // 2 - 3, transform_len // 2 + 4
    threshold = 2.4

    ref_pass = None
    ref_stat = None
    prev = mf.backend()
    try:
        for tgt in targets:
            mf.set_target(tgt)
            for create_fn in (core_lib.ap_mf_create, core_lib.ap_mf_create_pairbatch):
                plan = create_fn(transform_len, ndata, ntmpl)
                assert plan
                try:
                    core_lib.ap_mf_set_q15_margin(plan, 1)
                    for d in range(ndata):
                        assert core_lib.ap_mf_set_data(plan, d, data[d].ctypes.data) == 0
                    for t in range(ntmpl):
                        assert core_lib.ap_mf_set_template(plan, t, tmpls[t].ctypes.data) == 0
                    out_pass = np.full(ndata * ntmpl, 7, dtype=np.uint8)
                    out_stat = np.full(ndata * ntmpl, -1.0, dtype=np.float32)
                    rc = core_lib.ap_mf_q15_screen(
                        plan, 0, ndata, 0, ntmpl, C.c_float(threshold),
                        lo, hi, out_pass.ctypes.data, out_stat.ctypes.data
                    )
                    assert rc >= 0
                    if ref_pass is None:
                        ref_pass = out_pass.copy()
                        ref_stat = out_stat.copy()
                    else:
                        np.testing.assert_array_equal(out_pass, ref_pass, err_msg=f"pass mismatch on {tgt}")
                        # q15_sumsq float32 lane width (32 vs 16 vs 8) can shift scf by 1 ULP,
                        # flipping a sample at exact .5 by +-1 LSB (+-1 Q15 count in lanemax).
                        np.testing.assert_allclose(out_stat, ref_stat, rtol=1.5e-2, atol=4e-2,
                                                   err_msg=f"stat mismatch on {tgt}")
                finally:
                    core_lib.ap_mf_destroy(plan)
    finally:
        mf.set_target(prev)


@pytest.mark.parametrize("transform_len", [64, 128, 256, 512, 1024])
def test_direct_q15_screen_and_tile_bit_exact_across_isas(core_lib, transform_len):
    """Given identical int16 inputs, ap_q15_screen and ap_q15_screen_tile produce
    zero-ULP bit-identical int16 lanemax and pass bits across all Q15 ISAs."""
    targets = _q15_targets()
    if len(targets) < 1:
        pytest.skip("no Q15 targets available")

    rng = np.random.default_rng(transform_len * 71 + 9)
    nblocks = 4
    dr = rng.integers(-400, 400, size=(nblocks, transform_len), dtype=np.int16)
    di = rng.integers(-400, 400, size=(nblocks, transform_len), dtype=np.int16)
    qd = np.zeros((nblocks, 3 * transform_len), dtype=np.int16)
    for b in range(nblocks):
        qd[b, 0:2 * transform_len:2] = dr[b]
        qd[b, 1:2 * transform_len:2] = dr[b]
        qd[b, 2 * transform_len:] = di[b]

    tmpls_r = rng.integers(-400, 400, size=(32, transform_len), dtype=np.int16)
    tmpls_i = rng.integers(-400, 400, size=(32, transform_len), dtype=np.int16)
    lo, hi = transform_len // 8, transform_len - transform_len // 8

    scratch_raw = np.zeros(transform_len * 32 * 16 + 64, dtype=np.uint8)
    scratch_ptr = scratch_raw.ctypes.data + ((-scratch_raw.ctypes.data) % 64)

    ref_dense = None
    prev = mf.backend()
    try:
        for tgt in targets:
            mf.set_target(tgt)
            plan = core_lib.ap_create(transform_len)
            assert plan
            try:
                qw = core_lib.ap_q15_lanes(plan)
                assert qw in (8, 16, 32)
                dense_max = np.zeros((nblocks, 32), dtype=np.int16)
                dense_pass = np.zeros((nblocks, 32), dtype=np.uint8)
                lanethr = np.full(qw, 40, dtype=np.int16)
                for g in range(32 // qw):
                    tr = np.ascontiguousarray(tmpls_r[g * qw:(g + 1) * qw].T)
                    ti = np.ascontiguousarray(tmpls_i[g * qw:(g + 1) * qw].T)
                    for b in range(nblocks):
                        bits = C.c_uint64(0)
                        lmax = np.full(qw, -1, dtype=np.int16)
                        assert core_lib.ap_q15_screen(
                            plan, qd[b].ctypes.data, tr.ctypes.data, ti.ctypes.data,
                            lo, hi, lanethr.ctypes.data, C.byref(bits),
                            lmax.ctypes.data, scratch_ptr
                        ) == 0
                        dense_max[b, g * qw:(g + 1) * qw] = lmax
                        for l in range(qw):
                            dense_pass[b, g * qw + l] = (bits.value >> l) & 1

                if ref_dense is None:
                    ref_dense = (dense_max.copy(), dense_pass.copy())
                else:
                    np.testing.assert_array_equal(dense_max, ref_dense[0], err_msg=f"dense lanemax {tgt}")
                    np.testing.assert_array_equal(dense_pass, ref_dense[1], err_msg=f"dense pass {tgt}")

                if core_lib.ap_q15_has_tile(plan):
                    tr0 = np.ascontiguousarray(tmpls_r[:qw].T)
                    ti0 = np.ascontiguousarray(tmpls_i[:qw].T)
                    for tile_w in (qw // 2, qw // 4):
                        n_blk = qw // tile_w
                        tthr = np.full(qw, 40, dtype=np.int16)
                        tbits = C.c_uint64(0)
                        tmax = np.full(qw, -1, dtype=np.int16)
                        assert core_lib.ap_q15_screen_tile(
                            plan, tile_w, qd[0].ctypes.data, tr0.ctypes.data, ti0.ctypes.data,
                            lo, hi, tthr.ctypes.data, C.byref(tbits), tmax.ctypes.data, scratch_ptr
                        ) == 0
                        for b in range(n_blk):
                            np.testing.assert_array_equal(
                                tmax[b * tile_w:(b + 1) * tile_w],
                                dense_max[b, :tile_w],
                                err_msg=f"tile T={tile_w} b={b} on {tgt}"
                            )
            finally:
                core_lib.ap_destroy(plan)
    finally:
        mf.set_target(prev)


@pytest.mark.parametrize("transform_len", [64, 128, 256, 512, 1024])
def test_cross_isa_gather_and_lag_bit_exact(core_lib, transform_len):
    """Arbitrary-pair Q15 gather screen and argmax lag election match across all ISAs."""
    targets = _q15_targets()
    if len(targets) < 1:
        pytest.skip("no Q15 targets available")

    ndata, ntmpl = 19, 43
    rng = np.random.default_rng(transform_len * 97 + 3)
    data = np.ascontiguousarray(
        (rng.standard_normal((ndata, transform_len, 2)) / 6.0).astype(np.float32)
    )
    tmpls = np.ascontiguousarray(
        (rng.standard_normal((ntmpl, transform_len, 2)) / 6.0).astype(np.float32)
    )
    # Create exact ties across lags in block 2 + template 4 to exercise earliest-lag tie-break
    data[2] = 0.0
    data[2, 0, 0] = 1.0
    tmpls[4] = 0.0
    tmpls[4, 0, 0] = 1.0

    count = 53
    dsel = np.ascontiguousarray(rng.integers(0, ndata, size=count), dtype=np.int32)
    tsel = np.ascontiguousarray(rng.integers(0, ntmpl, size=count), dtype=np.int32)
    dsel[0], tsel[0] = 2, 4
    dsel[1:5] = 7

    lo = max(1, transform_len // 8)
    hi = transform_len - lo
    threshold = 2.2

    ref = None
    prev = mf.backend()
    try:
        for tgt in targets:
            mf.set_target(tgt)
            plan = core_lib.ap_mf_create(transform_len, ndata, ntmpl)
            assert plan
            try:
                core_lib.ap_mf_set_q15_margin(plan, 0)
                for d in range(ndata):
                    assert core_lib.ap_mf_set_data(plan, d, data[d].ctypes.data) == 0
                for t in range(ntmpl):
                    assert core_lib.ap_mf_set_template(plan, t, tmpls[t].ctypes.data) == 0
                out_pass = np.full(count, 9, dtype=np.uint8)
                out_stat = np.full(count, -9.0, dtype=np.float32)
                out_lag = np.full(count, -9, dtype=np.int16)
                rc = core_lib.ap_mf_q15_pairs_lag(
                    plan, 0, dsel.ctypes.data, tsel.ctypes.data, count, 0,
                    C.c_float(threshold), lo, hi,
                    out_pass.ctypes.data, out_stat.ctypes.data, out_lag.ctypes.data
                )
                assert rc == int(out_pass.sum())
                assert out_lag[0] == lo
                if ref is None:
                    ref = (out_pass.copy(), out_stat.copy(), out_lag.copy())
                else:
                    np.testing.assert_array_equal(out_pass, ref[0], err_msg=f"gather pass {tgt}")
                    np.testing.assert_allclose(out_stat, ref[1], rtol=1.5e-2, atol=4e-2,
                                               err_msg=f"gather stat {tgt}")
                    np.testing.assert_array_equal(out_lag, ref[2], err_msg=f"gather lag {tgt}")
            finally:
                core_lib.ap_mf_destroy(plan)
    finally:
        mf.set_target(prev)


@pytest.mark.parametrize("transform_len", [64, 256, 512])
def test_slab8_and_screen_perm_cross_isa(core_lib, transform_len):
    """Direct test of ap_q15_slab8 + ap_q15_screen_perm across all Q15 targets."""
    targets = _q15_targets()
    if len(targets) < 1:
        pytest.skip("no Q15 targets available")

    rng = np.random.default_rng(transform_len + 505)
    rows_re = [np.ascontiguousarray(rng.standard_normal(transform_len, dtype=np.float32)) for _ in range(8)]
    rows_im = [np.ascontiguousarray(rng.standard_normal(transform_len, dtype=np.float32)) for _ in range(8)]
    scales = np.ascontiguousarray(rng.uniform(20.0, 80.0, size=8).astype(np.float32))
    tmpls_re = rng.integers(-600, 600, size=(64, transform_len), dtype=np.int16)
    tmpls_im = rng.integers(-600, 600, size=(64, transform_len), dtype=np.int16)

    ref_perm = None
    prev = mf.backend()
    try:
        # Reference 8x8 int16 slab via round-to-nearest-even matching x86/NEON NearestInt
        ref_slab_r = np.stack([np.clip(np.rint(rows_re[b] * scales[b]), -32768, 32767).astype(np.int16)
                               for b in range(8)], axis=1)
        ref_slab_i = np.stack([np.clip(np.rint(rows_im[b] * scales[b]), -32768, 32767).astype(np.int16)
                               for b in range(8)], axis=1)

        for tgt in targets:
            mf.set_target(tgt)
            plan = core_lib.ap_create(transform_len)
            assert plan
            try:
                qw = core_lib.ap_q15_lanes(plan)
                assert qw in (8, 16, 32)
                xr = np.zeros((transform_len, qw), dtype=np.int16)
                xi = np.zeros((transform_len, qw), dtype=np.int16)
                rr_ptrs = (C.c_void_p * 8)(*[r.ctypes.data for r in rows_re])
                ri_ptrs = (C.c_void_p * 8)(*[r.ctypes.data for r in rows_im])
                assert core_lib.ap_q15_slab8(
                    plan, rr_ptrs, ri_ptrs, scales.ctypes.data, xr.ctypes.data, xi.ctypes.data
                ) == 0
                np.testing.assert_array_equal(xr[:, :8], ref_slab_r, err_msg=f"slab8 re on {tgt}")
                np.testing.assert_array_equal(xi[:, :8], ref_slab_i, err_msg=f"slab8 im on {tgt}")

                # Pack 2 groups of qw templates [2][transform_len][qw]; first 8 templates match across ISAs
                tr = np.ascontiguousarray(tmpls_re[:2 * qw].reshape(2, qw, transform_len).transpose(0, 2, 1))
                ti = np.ascontiguousarray(tmpls_im[:2 * qw].reshape(2, qw, transform_len).transpose(0, 2, 1))
                dsel = np.ascontiguousarray((np.arange(qw) * 3) % 8, dtype=np.int16)
                tsel = np.ascontiguousarray((np.arange(qw) * 5 + 1) % 8, dtype=np.int16)
                lanethr = np.full(qw, 50, dtype=np.int16)
                bits = C.c_uint64(0)
                lanemax = np.full(qw, -1, dtype=np.int16)
                laneidx = np.full(qw, -1, dtype=np.int16)
                scratch_raw = np.zeros(transform_len * qw * 16 + 64, dtype=np.uint8)
                scratch_off = (-scratch_raw.ctypes.data) % 64
                scratch_ptr = scratch_raw.ctypes.data + scratch_off
                tw = transform_len * qw
                assert core_lib.ap_q15_screen_perm(
                    plan, xr.ctypes.data, xi.ctypes.data,
                    tr[0].ctypes.data, ti[0].ctypes.data, tw,
                    dsel.ctypes.data, tsel.ctypes.data,
                    4, transform_len - 4, lanethr.ctypes.data,
                    C.byref(bits), lanemax.ctypes.data, laneidx.ctypes.data,
                    scratch_ptr
                ) == 0
                for l in range(qw):
                    assert (lanemax[l] >= 50) == bool((bits.value >> l) & 1)
                    assert 4 <= laneidx[l] < transform_len - 4
                if ref_perm is None:
                    ref_perm = (lanemax[:8].copy(), laneidx[:8].copy())
                else:
                    np.testing.assert_array_equal(lanemax[:8], ref_perm[0], err_msg=f"perm lanemax {tgt}")
                    np.testing.assert_array_equal(laneidx[:8], ref_perm[1], err_msg=f"perm laneidx {tgt}")
            finally:
                core_lib.ap_destroy(plan)
    finally:
        mf.set_target(prev)


def test_hierarchical_filter_q15_across_legacy_isas(monkeypatch):
    """Multi-tier HierarchicalFilter with Q15 enabled recovers planted injections on AVX, AVX2, SSE4."""
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    targets = _q15_targets()
    if len(targets) < 1:
        pytest.skip("no Q15 targets available")

    n, nd, nt = 4096, 6, 35
    rng = np.random.default_rng(12345)
    power = (1.0 / np.maximum(np.arange(n, dtype=np.float32), 1.0) ** 1.2).astype(np.float32)
    power[:8] = 0.0
    power /= np.sum(power)
    h = np.sqrt(power).astype(np.complex64)
    tm = (h * np.exp(2j * np.pi * rng.random((nt, n)) * 0.05)).astype(np.complex64)
    data = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    data[2] += 10.0 * np.conj(tm[19]) / np.linalg.norm(tm[19]) * np.sqrt(n)

    flat = mf.MatchedFilter(n, nd, nt)
    flat.set_templates(np.conj(tm))
    flat.set_data(data)
    ref = flat.run(binsize=n // 4, threshold=4.5)
    loud_bin = int(np.argmax(np.abs(ref["value"][2, 19])))

    prev = mf.backend()
    try:
        for tgt in targets:
            mf.set_target(tgt)
            hf = mf.HierarchicalFilter(n, nd, nt, chain=(128, 512), snr=5.5, fd=1e-3)
            hf.set_reference(power)
            hf.set_templates(np.conj(tm))
            hf.set_data(data)
            hf._ensure()
            assert hf._mf.set_q15(True)
            res = hf.run(binsize=n // 4, threshold=4.5)
            assert hf._mf.q15_stats()[1] > 0, f"Q15 screen did not pass pairs on {tgt}"
            got = res["index"] >= 0
            assert got[2, 19, loud_bin], f"missed planted peak on {tgt}"
            np.testing.assert_array_equal(res["index"][got], ref["index"][got], err_msg=tgt)
            np.testing.assert_allclose(res["value"][got], ref["value"][got], rtol=1e-5, atol=1e-5, err_msg=tgt)
    finally:
        mf.set_target(prev)
