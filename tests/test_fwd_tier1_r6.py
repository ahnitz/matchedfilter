"""Tests for fused and interleaved quadrature complex-pair forward transforms,
listed Q15 Tier-1+ gather screening, and sparse FP16 gate16 tiers."""
import ctypes
import math
import mmap

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _calibration, _core, gatechain


@pytest.fixture(params=mf.targets())
def target(request):
    """Select each compiled SIMD target in turn and restore default afterward."""
    mf.backend()
    mf.set_target(request.param)
    yield request.param
    mf.set_target(None)


def _guard_float_buffer(n_floats):
    """Allocate float32 storage ending on the exact byte before a PROT_NONE page.

    Parameters
    ----------
    n_floats : int
        Number of accessible float32 elements before the guard page.

    Returns
    -------
    tuple
        ``(mmap_obj, float_array)`` backed by a trailing ``PROT_NONE`` page.
    """
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
    return buf, arr


@pytest.mark.parametrize("h", [64, 128, 256, 512, 1024, 2048])
def test_fft_quad_pair_batch_exact_and_guard_page(target, h):
    """Verify ap_fft_quad_pair_batch matches strided ap_fft_real_batch bit-for-bit
    and never reads past 2*have floats at a PROT_NONE boundary."""
    lib = ctypes.CDLL(_core.__file__)
    float_p = ctypes.POINTER(ctypes.c_float)
    lib.ap_create_pairbatch.argtypes = [ctypes.c_size_t]
    lib.ap_create_pairbatch.restype = ctypes.c_void_p
    lib.ap_destroy.argtypes = [ctypes.c_void_p]
    lib.ap_destroy.restype = None
    lib.ap_plan_lanes.argtypes = [ctypes.c_void_p]
    lib.ap_plan_lanes.restype = ctypes.c_int
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
    lib.ap_fft_quad_pair_batch.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(float_p),
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_int,
        ctypes.c_float,
        float_p,
        ctypes.POINTER(float_p),
        ctypes.POINTER(float_p),
    ]
    lib.ap_fft_quad_pair_batch.restype = ctypes.c_int

    n = 2 * h
    scale = 1.0 / n
    total_cplx = n + 32
    buf, raw = _guard_float_buffer(2 * total_cplx)
    plan_pb = lib.ap_create_pairbatch(h)
    try:
        if not plan_pb:
            pytest.skip("pairbatch plan unavailable")
        lanes = lib.ap_plan_lanes(plan_pb)
        half_lanes = lanes // 2
        if half_lanes < 1:
            assert lib.ap_fft_quad_pair_batch(
                plan_pb, None, None, 1, scale, None, None, None
            ) == -1
            return

        rng = np.random.default_rng(7000 + h)
        raw[:] = rng.standard_normal(2 * total_cplx).astype(np.float32)
        base_addr = raw.ctypes.data

        # Precompute real-split twiddle table for length n = 2*h.
        rtw = np.empty(2 * (h + 1), dtype=np.float32)
        ks = np.arange(h + 1, dtype=np.float64)
        ang = 2.0 * math.pi * ks / n
        rtw[0::2] = np.cos(ang).astype(np.float32)
        rtw[1::2] = np.sin(ang).astype(np.float32)
        rtw_p = rtw.ctypes.data_as(float_p)

        # Test full batches, partial batches, and ragged edge blocks pinned to guard page.
        cases = [(half_lanes, True), (half_lanes, False), (1, False)]
        if half_lanes > 2:
            cases.append((half_lanes - 1, False))
        for cnt, all_full in cases:
            zsrcs = (float_p * cnt)()
            srcs_re = (float_p * cnt)()
            srcs_im = (float_p * cnt)()
            haves = (ctypes.c_size_t * cnt)()
            got_re = np.full((cnt, n), np.nan + 1j * np.nan, dtype=np.complex64)
            got_im = np.full((cnt, n), np.nan + 1j * np.nan, dtype=np.complex64)
            ref_re = np.full((cnt, n), np.nan + 1j * np.nan, dtype=np.complex64)
            ref_im = np.full((cnt, n), np.nan + 1j * np.nan, dtype=np.complex64)
            out_re_p = (float_p * cnt)()
            out_im_p = (float_p * cnt)()
            ref_re_p = (float_p * cnt)()
            ref_im_p = (float_p * cnt)()

            for l in range(cnt):
                hv = n if all_full else [n, n - 1, 32, 33, 1, 0][l % 6]
                s_idx = (total_cplx - hv) if hv > 0 else 0
                if all_full and l + 1 < cnt:
                    s_idx = max(0, s_idx - (cnt - 1 - l))
                zsrcs[l] = ctypes.cast(base_addr + 2 * s_idx * 4, float_p)
                # Keep strided reference away from the very last guard float when hv == n.
                ref_idx = max(0, s_idx - 1) if (hv > 0 and s_idx + hv == total_cplx) else s_idx
                srcs_re[l] = ctypes.cast(base_addr + 2 * ref_idx * 4, float_p)
                srcs_im[l] = ctypes.cast(base_addr + (2 * ref_idx + 1) * 4, float_p)
                haves[l] = hv
                out_re_p[l] = got_re[l].view(np.float32).ctypes.data_as(float_p)
                out_im_p[l] = got_im[l].view(np.float32).ctypes.data_as(float_p)
                ref_re_p[l] = ref_re[l].view(np.float32).ctypes.data_as(float_p)
                ref_im_p[l] = ref_im[l].view(np.float32).ctypes.data_as(float_p)

            rc = lib.ap_fft_quad_pair_batch(
                plan_pb, zsrcs, haves, cnt, scale, rtw_p, out_re_p, out_im_p
            )
            assert rc == 0

            # Compare against NumPy reference on every lane and bit-exact against real_batch
            # where strided reference uses identical start index.
            assert lib.ap_fft_real_batch(
                plan_pb, srcs_re, haves, 2, cnt, scale, rtw_p, 0, ref_re_p
            ) == 0
            assert lib.ap_fft_real_batch(
                plan_pb, srcs_im, haves, 2, cnt, scale, rtw_p, 0, ref_im_p
            ) == 0
            for l in range(cnt):
                hv = int(haves[l])
                s_idx = (total_cplx - hv) if hv > 0 else 0
                if all_full and l + 1 < cnt:
                    s_idx = max(0, s_idx - (cnt - 1 - l))
                pad_re = np.zeros(n, dtype=np.float32)
                pad_im = np.zeros(n, dtype=np.float32)
                if hv > 0:
                    pad_re[:hv] = raw[2 * s_idx : 2 * (s_idx + hv) : 2]
                    pad_im[:hv] = raw[2 * s_idx + 1 : 2 * (s_idx + hv) : 2]
                np.testing.assert_allclose(
                    got_re[l, : h + 1], np.fft.rfft(pad_re) * scale, rtol=3e-5, atol=3e-5
                )
                np.testing.assert_allclose(
                    got_im[l, : h + 1], np.fft.rfft(pad_im) * scale, rtol=3e-5, atol=3e-5
                )
                if not (hv > 0 and s_idx + hv == total_cplx):
                    np.testing.assert_array_equal(got_re[l, : h + 1], ref_re[l, : h + 1])
                    np.testing.assert_array_equal(got_im[l, : h + 1], ref_im[l, : h + 1])
    finally:
        if plan_pb:
            lib.ap_destroy(plan_pb)
        del raw
        buf.close()


def _unpack_sparse(res_tuple):
    """Decode a ``(flat_bytes, idx_bytes, val_bytes, total)`` sparse job tuple."""
    fl_b, ix_b, vl_b, total = res_tuple
    return (
        np.frombuffer(fl_b, dtype=np.int64),
        np.frombuffer(ix_b, dtype=np.int64),
        np.frombuffer(vl_b, dtype=np.complex64),
        total,
    )


@pytest.mark.parametrize("n", [128, 256, 512, 1024, 2048, 4096])
@pytest.mark.parametrize("swap_lanes", [False, True])
@pytest.mark.parametrize("nblocks", [1, 3, 4, 5, 8, 9, 17])
def test_quad_pair_sparse_batch_parity_and_swap_order(target, n, swap_lanes, nblocks):
    """Verify paired quadrature sparse batch execution matches standalone execution
    for both (Re, Im) and swapped (Im, Re) job ordering and ragged edge blocks."""
    rng = np.random.default_rng(9100 + n * 7 + int(swap_lanes) * 3 + nblocks)
    nt = 12
    tap_len = min(48, n // 4)
    taps = rng.standard_normal((nt, tap_len)).astype(np.float32)
    taps /= np.linalg.norm(taps, axis=1, keepdims=True)
    specs = np.conj(np.fft.fft(taps, n=n, axis=1)).astype(np.complex64)
    ref = np.ones(n, dtype=np.float32)
    chain = [min(64, n // 2)] if n <= 256 else [64, min(256, n // 2)]
    thr_coarse = [2.2] * len(chain)
    threshold = 3.2

    step = n - tap_len
    # Leave the final block short when nblocks > 1 to exercise ragged have < n padding.
    nseries = max(tap_len + 5, (nblocks - 1) * step + n - 11)
    z = (rng.standard_normal(nseries) + 1j * rng.standard_normal(nseries)).astype(np.complex64)
    # Inject a clear signal in both real and imaginary quadrature lanes on block 0.
    inj_lag = tap_len + 7
    if inj_lag + tap_len <= min(n, nseries):
        z.real[inj_lag : inj_lag + tap_len] += 6.5 * taps[2]
        z.imag[inj_lag : inj_lag + tap_len] += 6.0 * taps[5]

    starts = (np.arange(nblocks) * step).astype(np.uint64)
    ws = np.full(nblocks, tap_len, dtype=np.uint64)
    we = np.full(nblocks, n, dtype=np.uint64)
    bph = np.zeros(nblocks, dtype=np.uint32)
    binsize = n - tap_len

    # Build two independent real_series plans sharing the complex64 buffer at stride 2.
    plans = []
    for _ in range(2):
        p = _core.HMF(n, 1, nt, chain, 32, n)
        assert p.set_real_series(True, 2)
        p.set_reference(ref)
        p.set_template_batch(0, specs)
        p.set_thresholds(thr_coarse)
        p.set_q15(True)
        plans.append(p)

    z_f32 = z.view(np.float32)
    ser_re = z_f32[:-1]
    ser_im = z_f32[1:]
    lanes = [ser_im, ser_re] if swap_lanes else [ser_re, ser_im]

    # Reference: run each lane independently through single-job sparse execution.
    expected = []
    for p, ser in zip(plans, lanes):
        res = _core.HMF.run_series_batch_sparse(
            [(p, ser, starts, ws, we, 0, nt, binsize, threshold, None, bph, 0)]
        )[0]
        expected.append(_unpack_sparse(res))

    # Paired cluster_id=0 batch call triggers hmf_forward_slab_quad_pair -> ap_fft_quad_pair_batch.
    got_raw = _core.HMF.run_series_batch_sparse(
        [
            (plans[0], lanes[0], starts, ws, we, 0, nt, binsize, threshold, None, bph, 0),
            (plans[1], lanes[1], starts, ws, we, 0, nt, binsize, threshold, None, bph, 0),
        ]
    )
    for g_raw, e_item in zip(got_raw, expected):
        g_item = _unpack_sparse(g_raw)
        assert g_item[3] == e_item[3]
        np.testing.assert_array_equal(g_item[0], e_item[0])
        np.testing.assert_array_equal(g_item[1], e_item[1])
        np.testing.assert_allclose(g_item[2], e_item[2], rtol=1e-6, atol=1e-6)


@pytest.mark.parametrize("n", [512, 2048])
def test_quadrature_time_domain_bank_filter_series_many(target, n):
    """Verify end-to-end quadrature TimeDomainFilterBank.filter_series_many parity."""
    rng = np.random.default_rng(5500 + n)
    nt = 16
    tap_len = 64
    taps0 = rng.standard_normal((nt, tap_len)).astype(np.float32)
    taps0 /= np.linalg.norm(taps0, axis=1, keepdims=True)
    taps1 = rng.standard_normal((nt, tap_len)).astype(np.float32)
    taps1 /= np.linalg.norm(taps1, axis=1, keepdims=True)
    bank0 = mf.TimeDomainFilterBank(taps0, fft_lengths=(n,), engine="hier", device="cpu")
    bank1 = mf.TimeDomainFilterBank(taps1, fft_lengths=(n,), engine="hier", device="cpu")
    flat_ref = np.ones(n // 2 + 1, dtype=np.float32)
    bank0.set_reference(flat_ref, delta_f=2048.0 / n)
    bank1.set_reference(flat_ref, delta_f=2048.0 / n)
    nseries = 9 * (n - tap_len) + n - 17
    z = (rng.standard_normal(nseries) + 1j * rng.standard_normal(nseries)).astype(np.complex64)
    z.real[300 : 300 + tap_len] += 10.5 * taps0[4]
    z.imag[340 : 340 + tap_len] += 10.0 * taps1[7]

    # Compute standalone references first (also warming plan templates), then run paired batch.
    kw = {"threshold": 5.5, "binsize": n - tap_len}
    ref_re = bank0.filter_series(z.real, **kw)
    ref_im = bank1.filter_series(z.imag, **kw)
    res_re, res_im = mf.TimeDomainFilterBank.filter_series_many(
        [(bank0, z.real, kw), (bank1, z.imag, kw)]
    )
    for got, ref_res in ((res_re, ref_re), (res_im, ref_im)):
        np.testing.assert_array_equal(got.template_indices, ref_res.template_indices)
        np.testing.assert_array_equal(got.sample_indices, ref_res.sample_indices)
        np.testing.assert_allclose(got.snr, ref_res.snr, rtol=1e-5, atol=1e-5)


@pytest.mark.parametrize("n", [512, 2048])
@pytest.mark.parametrize("swap_lanes", [False, True])
def test_quadrature_unequal_starts_and_twin_peers(target, n, swap_lanes):
    """Verify unequal-stride quadrature sparse batch pairing and spectrum sharing across twins."""
    rng = np.random.default_rng(7700 + n + int(swap_lanes))
    nt = 10
    tap_a = 48
    tap_b = 80
    step_a = n - tap_a
    step_b = n - tap_b
    nseries = 20 * step_a + n - 13
    z = (rng.standard_normal(nseries) + 1j * rng.standard_normal(nseries)).astype(np.complex64)

    # Build two twin plans on lane A (step_a) and two twin plans on lane B (step_b).
    ref = np.ones(n, dtype=np.float32)
    chain = [64, min(256, n // 2)]
    thr_coarse = [2.2, 2.5]
    threshold = 3.5

    def make_plan(tap_len, inj_target, inj_offset, amp):
        taps = rng.standard_normal((nt, tap_len)).astype(np.float32)
        taps /= np.linalg.norm(taps, axis=1, keepdims=True)
        specs = np.conj(np.fft.fft(taps, n=n, axis=1)).astype(np.complex64)
        inj_target[inj_offset : inj_offset + tap_len] += amp * taps[3]
        p = _core.HMF(n, 1, nt, chain, 32, n)
        assert p.set_real_series(True, 2)
        p.set_reference(ref)
        p.set_template_batch(0, specs)
        p.set_thresholds(thr_coarse)
        p.set_q15(True)
        return p

    pa0 = make_plan(tap_a, z.real, 500, 7.5)
    pa1 = make_plan(tap_a, z.real, 3400, 7.2)
    pb0 = make_plan(tap_b, z.imag, 620, 7.8)
    pb1 = make_plan(tap_b, z.imag, 4100, 7.4)

    nblk_a = (nseries - tap_a) // step_a + 1
    starts_a = (np.arange(nblk_a) * step_a).astype(np.uint64)
    ws_a = np.full(nblk_a, tap_a, dtype=np.uint64)
    we_a = np.full(nblk_a, n, dtype=np.uint64)
    bph_a = np.zeros(nblk_a, dtype=np.uint32)

    nblk_b = (nseries - tap_b) // step_b + 1
    starts_b = (np.arange(nblk_b) * step_b).astype(np.uint64)
    ws_b = np.full(nblk_b, tap_b, dtype=np.uint64)
    we_b = np.full(nblk_b, n, dtype=np.uint64)
    bph_b = np.zeros(nblk_b, dtype=np.uint32)

    z_f32 = z.view(np.float32)
    ser_re = z_f32[:-1]
    ser_im = z_f32[1:]

    # Build batch job list in either (Re, Im) or (Im, Re) order within cluster_id=0.
    jobs_a = [
        (pa0, ser_re, starts_a, ws_a, we_a, 0, nt, step_a, threshold, None, bph_a, 0),
        (pa1, ser_re, starts_a, ws_a, we_a, 0, nt, step_a, threshold, None, bph_a, 0),
    ]
    jobs_b = [
        (pb0, ser_im, starts_b, ws_b, we_b, 0, nt, step_b, threshold, None, bph_b, 0),
        (pb1, ser_im, starts_b, ws_b, we_b, 0, nt, step_b, threshold, None, bph_b, 0),
    ]
    batch_jobs = (jobs_b + jobs_a) if swap_lanes else (jobs_a + jobs_b)

    # Compare clustered batch results against standalone single-job execution.
    expected = [_unpack_sparse(_core.HMF.run_series_batch_sparse([jb])[0]) for jb in batch_jobs]
    got_raw = _core.HMF.run_series_batch_sparse(batch_jobs)
    for g_raw, e_item in zip(got_raw, expected):
        g_item = _unpack_sparse(g_raw)
        assert g_item[3] == e_item[3]
        np.testing.assert_array_equal(g_item[0], e_item[0])
        np.testing.assert_array_equal(g_item[1], e_item[1])
        np.testing.assert_allclose(g_item[2], e_item[2], rtol=1e-6, atol=1e-6)


@pytest.mark.parametrize(
    "chain",
    [(128, 512), (128, 256, 512), (256, 512, 1024)],
)
@pytest.mark.parametrize("use_direct", [False, True])
@pytest.mark.parametrize("multi_bin", [False, True])
def test_listed_q15_tier1_sorted_and_direct_lag_parity(target, chain, use_direct, multi_bin):
    """Verify listed Q15 Tier-1+ direct band quantisation and batched gather screening
    preserve deterministic (d, t) output ordering and recover injected peaks."""
    n = 2048
    nt = 96
    nblocks = 32
    tap_len = 96
    rng = np.random.default_rng(4200 + sum(chain) + int(use_direct) * 11 + int(multi_bin) * 23)
    # Construct localized band-limited analytic FIR taps (99%+ energy below chain[0])
    # and convert with taps_to_spectra so FFT refine and direct FIR refine align.
    grid = np.arange(tap_len, dtype=np.float32) - (tap_len // 2)
    env = np.exp(-0.5 * (grid / 8.0) ** 2)
    carriers = rng.uniform(4.0, 28.0, size=(nt, 1)).astype(np.float32)
    phases = rng.uniform(0.0, 2.0 * math.pi, size=(nt, 1)).astype(np.float32)
    taps = (env[None, :] * np.exp(1j * (2.0 * math.pi * carriers * grid[None, :] / n + phases))).astype(
        np.complex64
    )
    taps = np.ascontiguousarray(taps, dtype=np.complex64)
    taps /= np.linalg.norm(taps, axis=1, keepdims=True)
    counts_tap = np.full(nt, tap_len, dtype=np.int64)
    specs_raw = np.empty((nt, n), dtype=np.complex64)
    _core.taps_to_spectra(taps, counts_tap, n, tap_len, specs_raw, True)
    specs = np.conj(specs_raw).astype(np.complex64)
    ref = np.ones(n, dtype=np.float32)

    step = n - tap_len
    nseries = (nblocks - 1) * step + n
    ser = ((rng.standard_normal(nseries) + 1j * rng.standard_normal(nseries)) / np.sqrt(2)).astype(
        np.complex64
    )
    # Inject three loud signals across different blocks and templates; peak lands at lag + tap_len // 2.
    injections = [(3, 17, tap_len + 120, 11.5), (14, 63, tap_len + 640, 12.0), (27, 5, tap_len + 910, 11.0)]
    for blk, tmpl, lag, amp in injections:
        s0 = blk * step + lag
        ser[s0 : s0 + tap_len] += amp * taps[tmpl]

    starts = (np.arange(nblocks) * step).astype(np.uint64)
    ws = np.full(nblocks, tap_len, dtype=np.uint64)
    we = np.full(nblocks, n, dtype=np.uint64)
    bph = np.zeros(nblocks, dtype=np.uint32)
    win = n - tap_len
    binsize = (win + 1) // 2 if multi_bin else win
    nbins = (win + binsize - 1) // binsize

    # Set a permissive Tier-0 threshold so nfire spans multiple Q15 gather batches.
    thr_coarse = [1.8] + [2.8] * (len(chain) - 1)
    threshold = 7.5

    p = _core.HMF(n, 1, nt, list(chain), 32, n)
    p.set_reference(ref)
    p.set_template_batch(0, specs)
    p.set_thresholds(thr_coarse)
    if not p.set_q15(True):
        pytest.skip("Q15 unavailable on selected target")
    if use_direct:
        p.set_taps(taps, tap_len, counts_tap, True)
        p.set_direct_prices(1e-4, 1e6)
        p.set_direct(True, 2)

    ser_f32 = ser.view(np.float32)
    res_raw = _core.HMF.run_series_batch_sparse(
        [(p, ser_f32, starts, ws, we, 0, nt, binsize, threshold, None, bph, 0)]
    )[0]
    flat, idx, val, total = _unpack_sparse(res_raw)
    assert total == len(flat)
    # Sparse output flat indices must be strictly increasing (preserving (d, t, b) order).
    if len(flat) > 1:
        assert np.all(np.diff(flat) > 0)

    # Dense ap_hmf_run_series call exercises non-fast_sparse pass_out compaction too.
    idx_d = np.zeros((nblocks, nt, nbins), dtype=np.int64)
    val_d = np.zeros((nblocks, nt, nbins), dtype=np.complex64)
    mag_d = np.zeros((nblocks, nt, nbins), dtype=np.float32)
    cnt_d = np.zeros((nblocks, nt), dtype=np.int32)
    total_d = p.run_series(
        ser_f32, starts, ws, we, 0, nt, binsize, threshold, idx_d, val_d, mag_d, cnt_d
    )
    assert total_d == total

    # Float-tier reference plan verifies Q15 Tier-1+ + direct refine parity.
    p_ref = _core.HMF(n, 1, nt, list(chain), 32, n)
    p_ref.set_reference(ref)
    p_ref.set_template_batch(0, specs)
    p_ref.set_thresholds(thr_coarse)
    p_ref.set_q15(False)
    idx_ref = np.zeros((nblocks, nt, nbins), dtype=np.int64)
    val_ref = np.zeros((nblocks, nt, nbins), dtype=np.complex64)
    mag_ref = np.zeros((nblocks, nt, nbins), dtype=np.float32)
    cnt_ref = np.zeros((nblocks, nt), dtype=np.int32)
    p_ref.run_series(
        ser_f32, starts, ws, we, 0, nt, binsize, threshold, idx_ref, val_ref, mag_ref, cnt_ref
    )

    # Every injected peak must match the float-tier reference at the exact fine lag.
    for blk, tmpl, lag, _ in injections:
        peak_lag = lag + tap_len // 2
        b = (peak_lag - tap_len) // binsize
        assert abs(int(idx_d[blk, tmpl, b]) - peak_lag) <= 4
        assert idx_d[blk, tmpl, b] == idx_ref[blk, tmpl, b]
        np.testing.assert_allclose(mag_d[blk, tmpl, b], mag_ref[blk, tmpl, b], rtol=1e-5, atol=1e-5)
        assert mag_d[blk, tmpl, b] > 9.0


@pytest.mark.parametrize("m", [64, 128, 256, 512, 1024])
@pytest.mark.parametrize("k0", [0, 37, 290])
@pytest.mark.parametrize("win_kind", ["full", "middle", "wide", "narrow"])
def test_q15_direct_band_and_pairs_batch_exact_parity(target, m, k0, win_kind):
    """Verify ap_q15_data_band_on and ap_q15_pairs_batch_on match ap_mf_q15_pairs_lag
    bit-for-bit across cyclic band offsets, lag window modes, and partial tails."""
    lib = ctypes.CDLL(_core.__file__)
    float_p = ctypes.POINTER(ctypes.c_float)
    i16_p = ctypes.POINTER(ctypes.c_int16)
    i32_p = ctypes.POINTER(ctypes.c_int)
    u8_p = ctypes.POINTER(ctypes.c_ubyte)

    lib.ap_create.argtypes = [ctypes.c_size_t]
    lib.ap_create.restype = ctypes.c_void_p
    lib.ap_destroy.argtypes = [ctypes.c_void_p]
    lib.ap_destroy.restype = None
    lib.ap_q15_lanes.argtypes = [ctypes.c_void_p]
    lib.ap_q15_lanes.restype = ctypes.c_int
    lib.ap_mf_create_pairbatch.argtypes = [ctypes.c_size_t, ctypes.c_int, ctypes.c_int]
    lib.ap_mf_create_pairbatch.restype = ctypes.c_void_p
    lib.ap_mf_create.argtypes = [ctypes.c_size_t, ctypes.c_int, ctypes.c_int]
    lib.ap_mf_create.restype = ctypes.c_void_p
    lib.ap_mf_destroy.argtypes = [ctypes.c_void_p]
    lib.ap_mf_destroy.restype = None
    lib.ap_mf_set_data.argtypes = [ctypes.c_void_p, ctypes.c_int, float_p]
    lib.ap_mf_set_data.restype = ctypes.c_int
    lib.ap_mf_set_template.argtypes = [ctypes.c_void_p, ctypes.c_int, float_p]
    lib.ap_mf_set_template.restype = ctypes.c_int
    lib.ap_mf_set_q15_margin.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.ap_mf_set_q15_margin.restype = ctypes.c_int
    lib.ap_mf_q15_pairs_lag.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        i32_p,
        i32_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_size_t,
        ctypes.c_size_t,
        u8_p,
        float_p,
        i16_p,
    ]
    lib.ap_mf_q15_pairs_lag.restype = ctypes.c_int
    lib.ap_q15_data_band_on.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        float_p,
        ctypes.c_size_t,
        ctypes.c_size_t,
        i16_p,
        i16_p,
        float_p,
    ]
    lib.ap_q15_data_band_on.restype = ctypes.c_int
    lib.ap_q15_pairs_batch_on.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        i16_p,
        float_p,
        i16_p,
        float_p,
        ctypes.c_int,
        ctypes.c_int,
        i32_p,
        i32_p,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_size_t,
        ctypes.c_size_t,
        i32_p,
        i32_p,
        u8_p,
        i16_p,
        ctypes.c_void_p,
    ]
    lib.ap_q15_pairs_batch_on.restype = ctypes.c_int

    n_full = 2048
    nd = 12
    nt = 40
    npairs = 73
    plan = lib.ap_create(n_full)
    mf_plan = lib.ap_mf_create_pairbatch(m, nd, nt) or lib.ap_mf_create(m, nd, nt)
    scratch_raw = np.zeros(2 * 33 * 32 * 64 + 64, dtype=np.uint8)
    off64 = (-scratch_raw.ctypes.data) & 63
    scratch = scratch_raw[off64:].view(np.int16)
    try:
        ql = lib.ap_q15_lanes(plan)
        if ql <= 0:
            pytest.skip("Q15 unavailable on selected target")

        rng = np.random.default_rng(6100 + m * 5 + k0 + hash(win_kind) % 97)
        dspecs = (rng.standard_normal((nd, n_full)) + 1j * rng.standard_normal((nd, n_full))).astype(
            np.complex64
        )
        tspecs = (rng.standard_normal((nt, m)) + 1j * rng.standard_normal((nt, m))).astype(
            np.complex64
        )
        tspecs /= np.linalg.norm(tspecs, axis=1, keepdims=True)
        khi = min(n_full // 2, k0 + m) if k0 > 0 else m

        # Ingest cyclic band [k0, khi) into both the reference MF plan and direct Q15 rows.
        stride = 2 * m + 32
        qdm = np.zeros((nd, stride), dtype=np.int16)
        qds = np.zeros(nd, dtype=np.float32)
        for d in range(nd):
            band = np.zeros(m, dtype=np.complex64)
            if k0 == 0:
                band[:] = dspecs[d, :m]
            else:
                ln = max(0, min(m, khi - k0))
                u0 = k0 & (m - 1)
                first = min(ln, m - u0)
                if first:
                    band[u0 : u0 + first] = dspecs[d, k0 : k0 + first]
                if ln > first:
                    band[: ln - first] = dspecs[d, k0 + first : k0 + ln]
            assert lib.ap_mf_set_data(mf_plan, d, band.view(np.float32).ctypes.data_as(float_p)) == 0
            qdr_p = qdm[d].ctypes.data_as(i16_p)
            qdi_p = qdm[d, m:].ctypes.data_as(i16_p)
            sc_c = ctypes.c_float(0.0)
            assert (
                lib.ap_q15_data_band_on(
                    plan,
                    m,
                    dspecs[d].view(np.float32).ctypes.data_as(float_p),
                    k0,
                    khi,
                    qdr_p,
                    qdi_p,
                    ctypes.byref(sc_c),
                )
                == 0
            )
            qds[d] = sc_c.value

        # Quantise templates identically to load_tiers / q15_template_contig.
        qtm = np.zeros((nt, stride), dtype=np.int16)
        qts = np.zeros(nt, dtype=np.float32)
        tnorm = 16384.0 * math.sqrt(float(m)) / 4.0
        for t in range(nt):
            assert lib.ap_mf_set_template(mf_plan, t, tspecs[t].view(np.float32).ctypes.data_as(float_p)) == 0
            rf = tspecs[t].real.astype(np.float64)
            imf = (-tspecs[t].imag).astype(np.float64)
            ss = float(np.sum(rf * rf + imf * imf))
            amax = float(max(np.max(np.abs(rf)), np.max(np.abs(imf))))
            sc = min(tnorm / math.sqrt(ss), 32767.0 / amax) if ss > 0.0 else 0.0
            qtm[t, :m] = np.clip(np.rint(rf * sc), -32767, 32767).astype(np.int16)
            qtm[t, m : 2 * m] = np.clip(np.rint(imf * sc), -32767, 32767).astype(np.int16)
            qts[t] = np.float32(sc)

        lib.ap_mf_set_q15_margin(mf_plan, 0)
        dsel = rng.integers(0, nd, size=npairs, dtype=np.int32)
        tsel = rng.integers(0, nt, size=npairs, dtype=np.int32)

        if win_kind == "full":
            ws, we = 0, m
        elif win_kind == "middle":
            ws, we = m // 8, m - m // 8
        elif win_kind == "wide":
            ws, we = m // 4, m - m // 4
        else:
            ws, we = m // 2 - 3, m // 2 + 4

        thr = 2.6
        pass_ref = np.zeros(npairs, dtype=np.uint8)
        lag_ref = np.zeros(npairs, dtype=np.int16)
        n_ref = lib.ap_mf_q15_pairs_lag(
            mf_plan,
            0,
            dsel.ctypes.data_as(i32_p),
            tsel.ctypes.data_as(i32_p),
            npairs,
            0,
            thr,
            ws,
            we,
            pass_ref.ctypes.data_as(u8_p),
            None,
            lag_ref.ctypes.data_as(i16_p),
        )
        assert n_ref >= 0

        # Check pass_out mode with and without lag election.
        for use_lag in (False, True):
            pass_got = np.zeros(npairs, dtype=np.uint8)
            lag_got = np.zeros(npairs, dtype=np.int16)
            n_got = lib.ap_q15_pairs_batch_on(
                plan,
                m,
                qdm.ctypes.data_as(i16_p),
                qds.ctypes.data_as(float_p),
                qtm.ctypes.data_as(i16_p),
                qts.ctypes.data_as(float_p),
                0,
                0,
                dsel.ctypes.data_as(i32_p),
                tsel.ctypes.data_as(i32_p),
                npairs,
                thr,
                1,
                ws,
                we,
                None,
                None,
                pass_got.ctypes.data_as(u8_p),
                lag_got.ctypes.data_as(i16_p) if use_lag else None,
                scratch.ctypes.data_as(ctypes.c_void_p),
            )
            assert n_got == n_ref
            np.testing.assert_array_equal(pass_got, pass_ref)
            if use_lag:
                np.testing.assert_array_equal(lag_got, lag_ref)

            # Check direct dst_d/dst_t compaction mode.
            dst_d = np.full(npairs, -1, dtype=np.int32)
            dst_t = np.full(npairs, -1, dtype=np.int32)
            lag_comp = np.full(npairs, -2, dtype=np.int16)
            n_comp = lib.ap_q15_pairs_batch_on(
                plan,
                m,
                qdm.ctypes.data_as(i16_p),
                qds.ctypes.data_as(float_p),
                qtm.ctypes.data_as(i16_p),
                qts.ctypes.data_as(float_p),
                0,
                0,
                dsel.ctypes.data_as(i32_p),
                tsel.ctypes.data_as(i32_p),
                npairs,
                thr,
                1,
                ws,
                we,
                dst_d.ctypes.data_as(i32_p),
                dst_t.ctypes.data_as(i32_p),
                None,
                lag_comp.ctypes.data_as(i16_p) if use_lag else None,
                scratch.ctypes.data_as(ctypes.c_void_p),
            )
            assert n_comp == n_ref
            keep = pass_ref.astype(bool)
            np.testing.assert_array_equal(dst_d[:n_comp], dsel[keep])
            np.testing.assert_array_equal(dst_t[:n_comp], tsel[keep])
            if use_lag:
                np.testing.assert_array_equal(lag_comp[:n_comp], lag_ref[keep])
    finally:
        if mf_plan:
            lib.ap_mf_destroy(mf_plan)
        if plan:
            lib.ap_destroy(plan)


def test_gate16_sparse_later_tiers_and_calibration_key(monkeypatch):
    """Verify calibration cache tag bumps to g16s for FP16 CPU gates and exercise
    sparse later-tier gate16 execution when available on ARM64."""
    # Check calibration key separation when cpu_gate_kind() == "f16".
    sentinel = object()
    key = (1024, gatechain._CAL_TEMPLATES, _core.series_group(1024, 32), 32, 3, 0, "g16s")
    monkeypatch.setattr(gatechain, "cpu_gate_kind", lambda: "f16")
    monkeypatch.setitem(gatechain._COSTS, key, sentinel)
    assert _calibration.calibrate_costs(1024, 64, blocks=32, reps=3, seed=0, group=32) is sentinel
    monkeypatch.undo()

    # Verify 3-tier chains with q15=False (exercising gate16 on ARM64 NEON) across sparse survivor counts.
    n = 2048
    nt = 32
    nblocks = 16
    tap_len = 64
    rng = np.random.default_rng(8801)
    raw_taps = rng.standard_normal((nt, tap_len)).astype(np.float32)
    raw_spec = np.fft.rfft(raw_taps, n=n, axis=1)
    raw_spec[:, 128:] = 0.0
    taps = np.ascontiguousarray(np.fft.irfft(raw_spec, n=n, axis=1)[:, :tap_len], dtype=np.float32)
    taps /= np.linalg.norm(taps, axis=1, keepdims=True)
    counts_tap = np.full(nt, tap_len, dtype=np.int64)
    specs = np.empty((nt, n), dtype=np.complex64)
    _core.taps_to_spectra(taps, counts_tap, n, tap_len, specs)
    ref = np.ones(n, dtype=np.float32)
    step = n - tap_len
    nseries = (nblocks - 1) * step + n
    ser = rng.standard_normal(nseries).astype(np.float32)
    ser[2 * step + 200 : 2 * step + 200 + tap_len] += 11.0 * taps[9]

    starts = (np.arange(nblocks) * step).astype(np.uint64)
    ws = np.full(nblocks, tap_len, dtype=np.uint64)
    we = np.full(nblocks, n, dtype=np.uint64)
    bph = np.zeros(nblocks, dtype=np.uint32)

    # Exact 100%-pass FP32 reference for peak lag and amplitude.
    p_ref = _core.HMF(n, 1, nt, [128], 16, n)
    p_ref.set_real_series(True)
    p_ref.set_reference(ref)
    p_ref.set_template_batch(0, specs)
    p_ref.set_thresholds([0.0])
    p_ref.set_q15(False)
    ref_raw = _core.HMF.run_series_batch_sparse(
        [(p_ref, ser, starts, ws, we, 0, nt, n - tap_len, 7.5, None, bph, 0)]
    )[0]
    ref_flat, ref_idx, ref_val, _ = _unpack_sparse(ref_raw)
    target_row = 2 * nt + 9
    ref_pos = np.where(ref_flat == target_row)[0]
    assert len(ref_pos) == 1
    expected_idx = int(ref_idx[ref_pos[0]])
    expected_val = ref_val[ref_pos[0]]

    for use_direct in (False, True):
        p = _core.HMF(n, 1, nt, [128, 512, 1024], 16, n)
        p.set_real_series(True)
        p.set_reference(ref)
        p.set_template_batch(0, specs)
        p.set_thresholds([2.0, 2.8, 3.4])
        p.set_q15(False)
        if use_direct:
            p.set_taps(taps, tap_len, counts_tap, False)
            p.set_direct_prices(1e-4, 1e6)
            p.set_direct(True, 2)
        res_raw = _core.HMF.run_series_batch_sparse(
            [(p, ser, starts, ws, we, 0, nt, n - tap_len, 7.5, None, bph, 0)]
        )[0]
        flat, idx, val, total = _unpack_sparse(res_raw)
        assert total >= 1
        pos = np.where(flat == target_row)[0]
        assert len(pos) == 1
        assert int(idx[pos[0]]) == expected_idx
        np.testing.assert_allclose(val[pos[0]], expected_val, rtol=5e-3, atol=1e-3)


@pytest.mark.parametrize("k0s", [(0, 0), (19, 43)])
def test_hmf_q15_toggle_and_band_offsets_state_parity(target, k0s):
    """Verify HMF lazy Tier-1+ Q15 data ingestion across set_q15 toggles and band offsets."""
    n = 1024
    nd = 8
    nt = 48
    chain = [128, 512]
    rng = np.random.default_rng(3300 + sum(k0s))
    dspecs = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    tspecs = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    tspecs /= np.linalg.norm(tspecs, axis=1, keepdims=True)
    # Plant a clean lag-0 template signal in row 3, template 11.
    dspecs[3] += 14.0 * tspecs[11]
    ref = np.ones(n, dtype=np.float32)

    p = _core.HMF(n, nd, nt, chain, 8, n)
    p.set_reference(ref)
    p.set_band_offsets(list(k0s))
    p.set_template_batch(0, tspecs)
    p.set_thresholds([1.9, 2.5])
    # Load data with Q15 initially disabled, run float, then enable Q15 and re-run.
    p.set_q15(False)
    for d in range(nd):
        p.set_data(d, dspecs[d])

    idx_f = np.zeros((nd, nt, 1), dtype=np.int64)
    val_f = np.zeros((nd, nt, 1), dtype=np.complex64)
    mag_f = np.zeros((nd, nt, 1), dtype=np.float32)
    cnt_f = np.zeros((nd, nt), dtype=np.int32)
    p.run(0, nd, 0, nt, n, 6.0, 0, n, idx_f, val_f, mag_f, cnt_f)
    assert cnt_f[3, 11] == 1

    if not p.set_q15(True):
        pytest.skip("Q15 unavailable on selected target")
    idx_q = np.zeros((nd, nt, 1), dtype=np.int64)
    val_q = np.zeros((nd, nt, 1), dtype=np.complex64)
    mag_q = np.zeros((nd, nt, 1), dtype=np.float32)
    cnt_q = np.zeros((nd, nt), dtype=np.int32)
    p.run(0, nd, 0, nt, n, 6.0, 0, n, idx_q, val_q, mag_q, cnt_q)
    assert cnt_q[3, 11] == 1
    assert idx_q[3, 11, 0] == idx_f[3, 11, 0]
    np.testing.assert_allclose(mag_q[3, 11, 0], mag_f[3, 11, 0], rtol=1e-5, atol=1e-5)

    # Update band offsets and verify Q15 re-ingests cleanly.
    new_k0s = [k0s[0] + 5, k0s[1] + 9]
    p.set_band_offsets(new_k0s)
    p.set_template_batch(0, tspecs)
    p.run(0, nd, 0, nt, n, 6.0, 0, n, idx_q, val_q, mag_q, cnt_q)
    assert cnt_q[3, 11] == 1


@pytest.mark.parametrize("n", [64, 128, 256, 512, 1024, 2048])
def test_fft_forward_batch_prefix_exact_and_untouched_tail(target, n):
    """Verify ap_fft_forward_batch_prefix matches ap_fft_forward_batch on [0, out_bins)
    without writing past out_bins across full, partial, and zero-padded batches."""
    lib = ctypes.CDLL(_core.__file__)
    float_p = ctypes.POINTER(ctypes.c_float)
    lib.ap_create_pairbatch.argtypes = [ctypes.c_size_t]
    lib.ap_create_pairbatch.restype = ctypes.c_void_p
    lib.ap_destroy.argtypes = [ctypes.c_void_p]
    lib.ap_destroy.restype = None
    lib.ap_plan_lanes.argtypes = [ctypes.c_void_p]
    lib.ap_plan_lanes.restype = ctypes.c_int
    lib.ap_fft_forward_batch.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(float_p),
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_int,
        ctypes.c_float,
        ctypes.POINTER(float_p),
    ]
    lib.ap_fft_forward_batch.restype = ctypes.c_int
    lib.ap_fft_forward_batch_prefix.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(float_p),
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_size_t,
        ctypes.POINTER(float_p),
    ]
    lib.ap_fft_forward_batch_prefix.restype = ctypes.c_int

    plan_pb = lib.ap_create_pairbatch(n)
    if not plan_pb:
        pytest.skip("pairbatch plan unavailable")
    try:
        lanes = lib.ap_plan_lanes(plan_pb)
        rng = np.random.default_rng(6100 + n)
        x = (rng.standard_normal((lanes, n)) + 1j * rng.standard_normal((lanes, n))).astype(
            np.complex64
        )
        scale = 1.0 / n
        sentinel = np.complex64(-1234.5 + 6789.25j)

        # Test half-spectrum prefix, non-vector-multiple prefix, and full spectrum (out_bins=0).
        for out_bins in (n // 2, max(1, n // 2 - 3), 0):
            eff_bins = n if out_bins == 0 else out_bins
            for cnt, all_full in ((lanes, True), (max(1, lanes - 1), False), (1, False)):
                srcs = (float_p * cnt)()
                haves = (ctypes.c_size_t * cnt)()
                got = np.full((cnt, n), sentinel, dtype=np.complex64)
                ref = np.full((cnt, n), sentinel, dtype=np.complex64)
                got_p = (float_p * cnt)()
                ref_p = (float_p * cnt)()
                for l in range(cnt):
                    haves[l] = n if all_full else [n, n - 5, 19, 1, 0][l % 5]
                    srcs[l] = x[l].view(np.float32).ctypes.data_as(float_p)
                    got_p[l] = got[l].view(np.float32).ctypes.data_as(float_p)
                    ref_p[l] = ref[l].view(np.float32).ctypes.data_as(float_p)

                assert lib.ap_fft_forward_batch(plan_pb, srcs, haves, cnt, scale, ref_p) == 0
                assert (
                    lib.ap_fft_forward_batch_prefix(
                        plan_pb, srcs, haves, cnt, scale, out_bins, got_p
                    )
                    == 0
                )
                np.testing.assert_allclose(
                    got[:, :eff_bins], ref[:, :eff_bins], rtol=2e-6, atol=2e-6
                )
                if eff_bins < n:
                    assert np.all(got[:, eff_bins:] == sentinel)
    finally:
        lib.ap_destroy(plan_pb)


@pytest.mark.parametrize("n", [256, 1024, 2048])
@pytest.mark.parametrize("mode", ["direct", "direct_fallback_and_peer", "hermitian"])
def test_complex_series_half_prefix_and_fft_refine_completion(target, n, mode):
    """Verify complex-series HMF half-spectrum forward batching (out_bins = n/2) across
    direct refine, multi-bin/peer FFT refine lazy completion, and Hermitian plans."""
    rng = np.random.default_rng(9400 + n + len(mode) * 13)
    nt = 16
    tap_len = 64
    grid = np.arange(tap_len, dtype=np.float32) - (tap_len // 2)
    env = np.exp(-0.5 * (grid / 9.0) ** 2)
    c_pos = rng.uniform(10.0, 15.0, size=(nt, 1)).astype(np.float32)
    ph = rng.uniform(0.0, 2.0 * math.pi, size=(nt, 2)).astype(np.float32)
    counts_tap = np.full(nt, tap_len, dtype=np.int64)
    chain = [64, n // 2] if n > 256 else [64, 128]

    if mode == "hermitian":
        # Real FIR taps packed into (nt, n // 2) Hermitian format (DC.imag = Nyquist.real).
        taps_r = (
            env[None, :] * np.cos(2.0 * math.pi * c_pos * grid[None, :] / n + ph[:, 0:1])
        ).astype(np.float32)
        taps_r = np.ascontiguousarray(taps_r / np.linalg.norm(taps_r, axis=1, keepdims=True))
        specs_full = np.empty((nt, n), dtype=np.complex64)
        _core.taps_to_spectra(taps_r, counts_tap, n, tap_len, specs_full, False)
        k_half = n // 2
        specs = np.ascontiguousarray(specs_full[:, :k_half], dtype=np.complex64)
        specs[:, 0] = specs_full[:, 0].real + 1j * specs_full[:, k_half].real
        ref = np.ones(k_half, dtype=np.float32)
        inj5 = taps_r[5].astype(np.complex64)
        inj11 = taps_r[11].astype(np.complex64)
    else:
        # Two-carrier complex taps: 50% power in [0, 32) and 50% in [n - 32, n).
        c_neg = rng.uniform(-16.0, -11.0, size=(nt, 1)).astype(np.float32)
        taps = (
            env[None, :]
            * (
                np.exp(1j * (2.0 * math.pi * c_pos * grid[None, :] / n + ph[:, 0:1]))
                + np.exp(1j * (2.0 * math.pi * c_neg * grid[None, :] / n + ph[:, 1:2]))
            )
        ).astype(np.complex64)
        taps = np.ascontiguousarray(taps / np.linalg.norm(taps, axis=1, keepdims=True))
        specs = np.empty((nt, n), dtype=np.complex64)
        _core.taps_to_spectra(taps, counts_tap, n, tap_len, specs, True)
        ref = np.ones(n, dtype=np.float32)
        inj5 = np.conj(taps[5])
        inj11 = np.conj(taps[11])

    step = n - tap_len
    nblocks = 19
    nseries = (nblocks - 1) * step + n - 23
    z = ((rng.standard_normal(nseries) + 1j * rng.standard_normal(nseries)) / np.sqrt(2)).astype(
        np.complex64
    )
    z[3 * step + 80 : 3 * step + 80 + tap_len] += 15.0 * inj5
    last_s0 = (nblocks - 1) * step
    z[last_s0 + 72 : last_s0 + 72 + tap_len] += 15.5 * inj11

    starts = (np.arange(nblocks) * step).astype(np.uint64)
    ws = np.full(nblocks, tap_len, dtype=np.uint64)
    we = np.full(nblocks, n, dtype=np.uint64)
    bph = np.zeros(nblocks, dtype=np.uint32)
    binsize = n - tap_len
    threshold = 7.0

    # Reference: eager set_data per block (dmirrored=1 full spectrum).
    k_plan = n // 2 if mode == "hermitian" else n
    p_ref = _core.HMF(n, nblocks, nt, chain, 16, k_plan)
    if mode == "hermitian":
        p_ref.set_hermitian(True)
    p_ref.set_reference(ref)
    p_ref.set_template_batch(0, specs)
    p_ref.set_thresholds([1.8, 2.2])
    p_ref.set_q15(False)
    for b in range(nblocks):
        s0 = int(starts[b])
        blk = np.zeros(n, dtype=np.complex64)
        hv = min(n, max(0, nseries - s0))
        blk[:hv] = z[s0 : s0 + hv]
        p_ref.set_data(b, (np.fft.fft(blk) / n).astype(np.complex64))
    idx_ref = np.zeros((nblocks, nt, 1), dtype=np.int64)
    val_ref = np.zeros((nblocks, nt, 1), dtype=np.complex64)
    mag_ref = np.zeros((nblocks, nt, 1), dtype=np.float32)
    cnt_ref = np.zeros((nblocks, nt), dtype=np.int32)
    p_ref.run(0, nblocks, 0, nt, binsize, threshold, tap_len, n, idx_ref, val_ref, mag_ref, cnt_ref)
    assert cnt_ref[3, 5] == 1
    assert cnt_ref[nblocks - 1, 11] == 1

    # Owner plan triggers half_prefix=1; in direct_fallback_and_peer, plan 0 forces FFT fallback
    # via tinydir_fftpair while peer plan 1 has direct=False and shares owner's half-prefix slab.
    plans = []
    for p_idx in range(2):
        p = _core.HMF(n, 1, nt, chain, 16, k_plan)
        if mode == "hermitian":
            p.set_hermitian(True)
        p.set_reference(ref)
        p.set_template_batch(0, specs)
        p.set_thresholds([1.8, 2.2])
        p.set_q15(True)
        if mode == "direct":
            p.set_taps(taps, tap_len, counts_tap, True)
            p.set_direct_prices(1e-4, 1e6)
            p.set_direct(True, 2)
        elif mode == "direct_fallback_and_peer" and p_idx == 0:
            p.set_taps(taps, tap_len, counts_tap, True)
            p.set_direct_prices(1e6, 1.0)
            p.set_direct(True, 2)
        plans.append(p)

    z_f32 = z.view(np.float32)
    res_pair = _core.HMF.run_series_batch_sparse(
        [
            (plans[0], z_f32, starts, ws, we, 0, nt, binsize, threshold, None, bph, 0),
            (plans[1], z_f32, starts, ws, we, 0, nt, binsize, threshold, None, bph, 0),
        ]
    )
    for res_raw in res_pair:
        flat, idx, val, total = _unpack_sparse(res_raw)
        for b_exp, t_exp in ((3, 5), (nblocks - 1, 11)):
            pos = np.where(flat == b_exp * nt + t_exp)[0]
            assert len(pos) == 1
            assert idx[pos[0]] == idx_ref[b_exp, t_exp, 0]
            np.testing.assert_allclose(
                np.abs(val[pos[0]]), mag_ref[b_exp, t_exp, 0], rtol=2e-4, atol=2e-4
            )


