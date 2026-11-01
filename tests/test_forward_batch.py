"""Batched small-N forward transforms (fft_forward_batch / fft_real_batch), fused scaled
stage-A loads (fft_forward_scaled), and windowed correlation stores (corr_prod_window) across
all supported targets, block sizes, real strides, ragged edge blocks, and narrow windows."""
import ctypes
import math
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


def _guard_float_buffer(n_floats):
    """Allocate a two-region mmap where `n_floats` float32 values end on the exact byte
    before a PROT_NONE guard page."""
    pagesz = mmap.PAGESIZE
    nbytes = n_floats * 4
    data_bytes = ((nbytes + pagesz - 1) // pagesz) * pagesz
    buf = mmap.mmap(-1, data_bytes + pagesz, prot=mmap.PROT_READ | mmap.PROT_WRITE)
    addr = ctypes.addressof(ctypes.c_char.from_buffer(buf))
    libc = ctypes.CDLL(None)
    if libc.mprotect(ctypes.c_void_p(addr + data_bytes), ctypes.c_size_t(pagesz), 0) != 0:
        buf.close()
        pytest.skip("mprotect guard page unavailable")
    offset = data_bytes - nbytes
    arr = np.frombuffer(buf, dtype=np.float32, count=n_floats, offset=offset)
    return buf, arr, addr + data_bytes, pagesz


@pytest.mark.parametrize("n", [128, 256, 512, 1024, 2048, 4096, 8192])
@pytest.mark.parametrize("real_kind", ["complex", "real_contig", "real_stride2"])
def test_forward_batch_matches_reference_and_is_batch_invariant(target, n, real_kind):
    rng = np.random.default_rng(100 + n)
    nt = 4
    L_tap = min(65, n // 4 + 1)
    taps = (rng.standard_normal((nt, L_tap)) + 1j * rng.standard_normal((nt, L_tap))).astype(np.complex64)
    taps /= np.linalg.norm(taps, axis=1, keepdims=True)
    step = n - L_tap + 1
    # 19 blocks + 13 samples exercises a full SIMD batch + a partial tail batch + a ragged final block
    S = 18 * step + L_tap + 13
    if real_kind == "complex":
        ser = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
        ser_ref = ser
    elif real_kind == "real_contig":
        ser = rng.standard_normal(S).astype(np.float32)
        ser_ref = ser.astype(np.complex64)
    else:
        packed = np.empty(S, np.complex64)
        packed.real = rng.standard_normal(S).astype(np.float32)
        packed.imag = rng.standard_normal(S).astype(np.float32)
        ser = packed.imag
        ser_ref = np.ascontiguousarray(ser, dtype=np.complex64)

    # 1. CorrelationFilter (via TimeDomainFilterBank engine='corr', ndata=1)
    cbank = mf.TimeDomainFilterBank(taps, engine="corr", fft_lengths=(n,), device="cpu")
    got = cbank.correlate_series(ser)
    # Direct numpy overlap-save reference
    for t in range(nt):
        ref_t = np.correlate(ser_ref, taps[t], mode="same")
        lo = L_tap // 2
        hi = S - L_tap // 2
        np.testing.assert_allclose(got[t, lo:hi], ref_t[lo:hi], rtol=3e-5, atol=3e-5)

    # Multi-window vs single-window must be bit-for-bit identical (cnt=1 vs cnt>1 & corr_prod_window)
    wins = [(n + 3, n + 4), (n + 17, n + 150), (3 * step + 50, 3 * step + 250)]
    if wins[-1][1] < S - L_tap:
        z_union = cbank.correlate_series(ser, windows=wins)
        for a, b in wins:
            z_one = cbank.correlate_series(ser, windows=slice(a, b))
            np.testing.assert_array_equal(z_union[:, a:b], z_one[:, a:b])
            np.testing.assert_allclose(z_one[:, a:b], got[:, a:b], rtol=0.0, atol=0.0)

    # 2. HierarchicalFilter real & complex series forward path (including ragged edge block + have==0)
    hf = mf.HierarchicalFilter(n, 1, nt, chain=(min(64, n // 2),), device="cpu")
    hf.set_reference(np.ones(n, np.float32))
    hf.set_coarse_threshold((0.0,))
    hf.set_templates(np.conj(np.fft.fft(taps, n=n, axis=1)).astype(np.complex64))
    nblk = 19
    starts = (np.arange(nblk) * step).astype(np.uintp)
    # Put last block start past S to test have == 0 zero-block edge handling in batched forward
    starts[-1] = S + 16
    ws = np.full(nblk, L_tap // 2, np.uintp)
    we = np.full(nblk, n - L_tap // 2, np.uintp)
    p_all = hf.run_series(ser, starts, ws, we, binsize=n, threshold=0.0).copy()
    p_one = hf.run_series(ser, starts[:1], ws[:1], we[:1], binsize=n, threshold=0.0).copy()
    np.testing.assert_array_equal(p_all["index"][:1], p_one["index"])
    np.testing.assert_array_equal(p_all["value"][:1], p_one["value"])
    # Zero block (starts[-1] >= S) produces zero correlation
    np.testing.assert_allclose(np.abs(p_all["value"][-1]), 0.0, atol=1e-7)


@pytest.mark.parametrize("h", [64, 128, 256, 512, 1024, 2048])
@pytest.mark.parametrize("stride", [1, 2])
def test_fft_forward_scaled_and_real_batch_guard_page(target, h, stride):
    """Directly verify single-pass ap_fft_forward_scaled (both balanced and small plans) and
    ap_fft_real_batch (full AP_W and partial batches, mirror=0/1) right before a PROT_NONE page."""
    lib = ctypes.CDLL(_core.__file__)
    float_p = ctypes.POINTER(ctypes.c_float)
    lib.ap_create.argtypes = [ctypes.c_size_t]
    lib.ap_create.restype = ctypes.c_void_p
    lib.ap_create_pairbatch.argtypes = [ctypes.c_size_t]
    lib.ap_create_pairbatch.restype = ctypes.c_void_p
    lib.ap_destroy.argtypes = [ctypes.c_void_p]
    lib.ap_destroy.restype = None
    lib.ap_plan_lanes.argtypes = [ctypes.c_void_p]
    lib.ap_plan_lanes.restype = ctypes.c_int
    lib.ap_fft_forward_scaled.argtypes = [
        ctypes.c_void_p, float_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_float, float_p,
    ]
    lib.ap_fft_forward_scaled.restype = None
    lib.ap_fft_real_batch.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(float_p),
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_size_t,
        ctypes.c_int,
        ctypes.c_float,
        float_p,
        ctypes.c_int,
        ctypes.POINTER(float_p),
    ]
    lib.ap_fft_real_batch.restype = ctypes.c_int

    n = 2 * h
    scale = 1.0 / n
    # Place exact (n - 1)*stride + 1 floats right before PROT_NONE so reading even 1 float past
    # the final strided sample faults immediately.
    total_floats = (n + 32) * stride
    buf, raw, guard_addr, pagesz = _guard_float_buffer(total_floats)
    plan_bal = lib.ap_create(h)
    plan_pb = lib.ap_create_pairbatch(h)
    try:
        rng = np.random.default_rng(5000 + h * 3 + stride)
        raw[:] = rng.standard_normal(total_floats).astype(np.float32)
        base_addr = raw.ctypes.data

        # 1. Test both balanced and small (pairbatch) plans on ap_fft_forward_scaled
        for plan in (plan_bal, plan_pb):
            if not plan:
                continue
            out = np.empty(h, dtype=np.complex64)
            out_p = out.view(np.float32).ctypes.data_as(float_p)
            for have in (n, n - 1, 32, 33, 1, 0):
                # Position start so the final readable sample raw[(start + have - 1)*stride] is the
                # very last float32 before the PROT_NONE page (raw[-1]).
                start_idx = (total_floats - 1) // stride - (have - 1) if have > 0 else 0
                src_p = ctypes.cast(base_addr + start_idx * stride * 4, float_p)
                lib.ap_fft_forward_scaled(plan, src_p, have, stride, scale, out_p)
                padded = np.zeros(n, dtype=np.float32)
                if have > 0:
                    padded[:have] = raw[start_idx * stride : (start_idx + have) * stride : stride]
                z_ref = np.fft.fft((padded[0::2] + 1j * padded[1::2]).astype(np.complex64)) * scale
                np.testing.assert_allclose(out, z_ref, rtol=3e-5, atol=3e-5)

        # 2. Test ap_fft_real_batch for full (cnt == W) and partial batches with guard-page lane
        if plan_pb:
            W = lib.ap_plan_lanes(plan_pb)
            rtw = np.empty(2 * (h + 1), dtype=np.float32)
            ks = np.arange(h + 1, dtype=np.float64)
            ang = 2.0 * math.pi * ks / n
            rtw[0::2] = np.cos(ang).astype(np.float32)
            rtw[1::2] = np.sin(ang).astype(np.float32)
            rtw_p = rtw.ctypes.data_as(float_p)

            for cnt, all_full in ((W, True), (W, False), (max(1, W - 3), False)):
                for mirror in (0, 1):
                    srcs = (float_p * cnt)()
                    haves = (ctypes.c_size_t * cnt)()
                    outs_arr = np.full((cnt, n), np.nan + 1j * np.nan, dtype=np.complex64)
                    outs = (float_p * cnt)()
                    expected = []
                    for l in range(cnt):
                        hv = n if all_full else [n, n - 1, 32, 33, 1, 0][l % 6]
                        s_idx = (total_floats - 1) // stride - (hv - 1) if hv > 0 else 0
                        # Spread full-batch lanes across different offsets while keeping the final
                        # lane pinned right against the guard page.
                        if all_full and l + 1 < cnt:
                            s_idx = max(0, s_idx - (cnt - 1 - l))
                        srcs[l] = ctypes.cast(base_addr + s_idx * stride * 4, float_p)
                        haves[l] = hv
                        outs[l] = outs_arr[l].view(np.float32).ctypes.data_as(float_p)
                        padded = np.zeros(n, dtype=np.float32)
                        if hv > 0:
                            padded[:hv] = raw[s_idx * stride : (s_idx + hv) * stride : stride]
                        expected.append(np.fft.fft(padded) * scale)
                    rc = lib.ap_fft_real_batch(
                        plan_pb, srcs, haves, stride, cnt, scale, rtw_p, mirror, outs
                    )
                    assert rc == 0
                    nbins = n if mirror else (h + 1)
                    for l in range(cnt):
                        np.testing.assert_allclose(
                            outs_arr[l, :nbins], expected[l][:nbins], rtol=3e-5, atol=3e-5
                        )
    finally:
        if plan_bal:
            lib.ap_destroy(plan_bal)
        if plan_pb:
            lib.ap_destroy(plan_pb)
        del raw
        ctypes.CDLL(None).mprotect(
            ctypes.c_void_p(guard_addr),
            ctypes.c_size_t(pagesz),
            mmap.PROT_READ | mmap.PROT_WRITE,
        )
        buf.close()
