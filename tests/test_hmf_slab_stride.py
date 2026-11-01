"""Tests for strided real-series forward transforms (stride=2 guard-page safety and stride=1
parity), L2-resident 512 KB series slab sizing (ap_hmf_effective_group), and Q15 window-maximum
and sparse survivor compaction across all compiled CPU SIMD targets."""
import ctypes
import mmap

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core


@pytest.fixture(params=mf.targets())
def target(request):
    mf.backend()
    mf.set_target(request.param)
    yield request.param
    mf.set_target(None)


def _guard_complex_buffer(n_complex):
    """Allocate a 2-region mmap where `n_complex` complex64 elements end on the exact byte
    before a PROT_NONE guard page, so reading even 1 float past `imag[-1]` faults."""
    pagesz = mmap.PAGESIZE
    nbytes = n_complex * 8
    data_bytes = ((nbytes + pagesz - 1) // pagesz) * pagesz
    buf = mmap.mmap(-1, data_bytes + pagesz, prot=mmap.PROT_READ | mmap.PROT_WRITE)
    addr = ctypes.addressof(ctypes.c_char.from_buffer(buf))
    libc = ctypes.CDLL(None)
    rc = libc.mprotect(ctypes.c_void_p(addr + data_bytes), ctypes.c_size_t(pagesz), 0)
    if rc != 0:
        buf.close()
        pytest.skip("mprotect guard page unavailable")
    offset = data_bytes - nbytes
    arr = np.frombuffer(buf, dtype=np.complex64, count=n_complex, offset=offset)
    return buf, arr


@pytest.mark.parametrize("n", [128, 256, 512, 1024, 2048, 4096])
def test_strided_real_forward_guard_page_and_parity(target, n):
    rng = np.random.default_rng(700 + n)
    nt = 5
    # S chosen so blocks hit exact end of buffer (have == n), partial 2*Wchunk, odd have, and have == 0
    S = n + 37
    buf, packed = _guard_complex_buffer(S)
    try:
        packed.real = rng.standard_normal(S).astype(np.float32)
        packed.imag = rng.standard_normal(S).astype(np.float32)
        spec = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
        spec /= np.linalg.norm(spec, axis=1, keepdims=True)

        # Starts chosen so block 1 has have == n ending on the exact final sample before PROT_NONE,
        # block 2 has have == 32 (exact 2*16 chunk), block 3 has odd have == 33, block 4 has have == 1,
        # and block 5 has have == 0.
        starts = np.array([0, 37, S - 32, S - 33, S - 1, S + 4], dtype=np.uint64)
        nblk = len(starts)
        ws = np.zeros(nblk, dtype=np.uint64)
        we = np.full(nblk, n, dtype=np.uint64)

        for lane_view in (packed.real, packed.imag):
            contig = np.ascontiguousarray(lane_view, dtype=np.float32)
            hf_st2 = mf.HierarchicalFilter(n, 1, nt, chain=(min(128, n // 2),), device="cpu")
            hf_st1 = mf.HierarchicalFilter(n, 1, nt, chain=(min(128, n // 2),), device="cpu")
            for h in (hf_st2, hf_st1):
                h.set_reference(np.ones(n, dtype=np.float32))
                h.set_coarse_threshold((0.0,))
                h.set_templates(spec)
            got_st2 = hf_st2.run_series(lane_view, starts, ws, we, binsize=n, threshold=0.0)
            got_st1 = hf_st1.run_series(contig, starts, ws, we, binsize=n, threshold=0.0)
            np.testing.assert_array_equal(got_st2["index"], got_st1["index"])
            np.testing.assert_allclose(got_st2["value"], got_st1["value"], rtol=1e-6, atol=1e-6)
        del lane_view
    finally:
        del packed
        # Restore RW before closing mmap
        addr = ctypes.addressof(ctypes.c_char.from_buffer(buf))
        pagesz = mmap.PAGESIZE
        data_bytes = len(buf) - pagesz
        ctypes.CDLL(None).mprotect(
            ctypes.c_void_p(addr + data_bytes),
            ctypes.c_size_t(pagesz),
            mmap.PROT_READ | mmap.PROT_WRITE,
        )
        buf.close()


def test_l2_slab_effective_group_and_dgroup_invariance(monkeypatch):
    monkeypatch.delenv("MF_DGROUP", raising=False)
    # 512 KB cap: n=1024 -> up to 64, n=2048 -> 32, n=4096 -> 16, n=1<<20 -> 1
    assert _core.series_group(1024, 32) == 32
    assert _core.series_group(2048, 256) == 32
    assert _core.series_group(4096, 256) == 16
    assert _core.series_group(8192, 256) == 8
    assert _core.series_group(1 << 20, 16) == 1

    # Explicit MF_DGROUP override still honors measurement requests up to 4 MB
    monkeypatch.setenv("MF_DGROUP", "256")
    assert _core.series_group(2048, 32) == 256
    monkeypatch.delenv("MF_DGROUP", raising=False)

    # Output invariance across slab sizes (8, 16, 32, 64) on multi-tier Q15 + real_stride=2
    rng = np.random.default_rng(20261031)
    n, nt, nblocks = 2048, 37, 70
    step = n - 128
    S = nblocks * step + n
    packed = np.empty(S, dtype=np.complex64)
    packed.real = rng.standard_normal(S).astype(np.float32)
    packed.imag = rng.standard_normal(S).astype(np.float32)
    spec = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    spec /= np.sqrt(np.sum(np.abs(spec) ** 2, axis=1, keepdims=True) / n)
    starts = (np.arange(nblocks) * step).astype(np.uint64)
    ws = np.full(nblocks, 128, dtype=np.uint64)
    we = np.full(nblocks, n - 128, dtype=np.uint64)

    ref_res = None
    for dg in (8, 16, 32, 64):
        monkeypatch.setenv("MF_DGROUP", str(dg))
        monkeypatch.setenv("MF_AUTOTUNE", "0")
        hf = mf.HierarchicalFilter(n, 1, nt, chain=(256, 512), device="cpu")
        hf.set_reference(np.ones(n, dtype=np.float32))
        hf.set_coarse_threshold((2.2, 2.8))
        hf.set_templates(spec)
        res = hf.run_series(packed.imag, starts, ws, we, binsize=256, threshold=3.4)
        if ref_res is None:
            ref_res = res
        else:
            np.testing.assert_array_equal(res["index"], ref_res["index"])
            np.testing.assert_allclose(res["value"], ref_res["value"], rtol=1e-6, atol=1e-6)


@pytest.mark.parametrize("b", [128, 256, 512, 1024])
def test_q15_window_maximum_exact_for_all_codelet_sizes(target, b):
    nd, nt = 2, 35
    rng = np.random.default_rng(9100 + b)
    d = (rng.standard_normal((nd, b)) + 1j * rng.standard_normal((nd, b))).astype(np.complex64)
    t = (rng.standard_normal((nt, b)) + 1j * rng.standard_normal((nt, b))).astype(np.complex64)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    m = _core.MF(b, nd, nt)
    if m.q15_lanes() == 0:
        pytest.skip("no Q15 screen on this back end")
    m.set_data_batch(0, d.view(np.float32).tobytes())
    m.set_template_batch(0, t.view(np.float32).tobytes())
    ps = np.empty(nd * nt, dtype=np.uint8)
    samples = np.empty((b, nd * nt), dtype=np.float32)
    for k in range(b):
        m.q15_screen(0, nd, 0, nt, 0.0, k, k + 1, ps, samples[k])
    # Exercise both interior fast-path (qsr16_twmax_middle / qsr32_twmax_middle) and edge fallback
    q = b // 8
    windows = [
        (0, b),
        (q, b - q),
        (q + 1, b - q),
        (q, b - q - 1),
        (3, b - 2),
        (b // 2 - 1, b // 2 + 2),
        (b - 1, b),
    ]
    for start, end in windows:
        stat = np.empty(nd * nt, dtype=np.float32)
        m.q15_screen(0, nd, 0, nt, 0.0, start, end, ps, stat)
        np.testing.assert_array_equal(stat, samples[start:end].max(axis=0))


@pytest.mark.parametrize("nt", [1, 7, 8, 9, 37, 70])
def test_hmf_sparse_q15_compaction_matches_dense(target, nt):
    rng = np.random.default_rng(4200 + nt)
    n, nblocks = 2048, 35
    step = n - 128
    S = nblocks * step + n
    ser = rng.standard_normal(S).astype(np.float32)
    spec = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    spec /= np.sqrt(np.sum(np.abs(spec) ** 2, axis=1, keepdims=True) / n)
    starts = (np.arange(nblocks) * step).astype(np.uint64)
    ws = np.full(nblocks, 128, dtype=np.uint64)
    we = np.full(nblocks, n - 128, dtype=np.uint64)

    p_sp = _core.HMF(n, 32, nt, [256, 512, 1024], 32, n)
    p_dn = _core.HMF(n, 32, nt, [256, 512, 1024], 32, n)
    for p in (p_sp, p_dn):
        p.set_real_series(True, 1)
        p.set_reference(np.ones(n, dtype=np.float32))
        p.set_template_batch(0, spec)
        p.set_thresholds([2.2, 2.8, 3.2])
        p.set_q15(True)

    binsize = (n - 256) // 4
    nb = p_sp.nbins(binsize, 128, n - 128)
    cnt_sp = np.full((nblocks, nt), 99, dtype=np.int32)
    fl_b, ix_b, vl_b, tot_sp = p_sp.run_series_sparse(
        ser, starts, ws, we, 0, nt, binsize, 3.5, cnt_sp
    )

    idx_dn = np.full((nblocks, nt, nb), -1, dtype=np.int64)
    val_dn = np.zeros((nblocks, nt, nb), dtype=np.complex64)
    mag_dn = np.zeros((nblocks, nt, nb), dtype=np.float32)
    cnt_dn = np.full((nblocks, nt), 77, dtype=np.int32)
    tot_dn = p_dn.run_series(
        ser, starts, ws, we, 0, nt, binsize, 3.5, idx_dn, val_dn, mag_dn, cnt_dn
    )

    assert tot_sp == tot_dn
    np.testing.assert_array_equal(cnt_sp, cnt_dn)
    fl = np.frombuffer(fl_b, dtype=np.int64)
    ix = np.frombuffer(ix_b, dtype=np.int64)
    vl = np.frombuffer(vl_b, dtype=np.complex64)
    idx_rec = np.full(nblocks * nt * nb, -1, dtype=np.int64)
    val_rec = np.zeros(nblocks * nt * nb, dtype=np.complex64)
    idx_rec[fl] = ix
    val_rec[fl] = vl
    idx_rec = idx_rec.reshape(nblocks, nt, nb)
    val_rec = val_rec.reshape(nblocks, nt, nb)
    for b_i in range(nblocks):
        for t_i in range(nt):
            c = int(cnt_dn[b_i, t_i])
            if c > 0:
                np.testing.assert_array_equal(idx_rec[b_i, t_i, :c], idx_dn[b_i, t_i, :c])
                np.testing.assert_array_equal(val_rec[b_i, t_i, :c], val_dn[b_i, t_i, :c])
