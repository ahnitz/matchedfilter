"""Every shipped Vulkan coarse tile, at every subgroup size the device can run it at, must
elect what the untiled build elects and fail open on an overflowing row.

Which tile runs is a per-device measured choice (_vkcompute._coarse_choice), and a tiled
pair takes the in-subgroup election (peakTwoWave) only when it fits one subgroup: at band
1024 on a 32-wide subgroup (Intel, NVIDIA) it takes the cross-subgroup one instead. That
branch tested overflow with isnan(), which the compiler folded, and every pair of a loud row
was dismissed -- on a 64-wide Radeon the branch only ran at band 2048, where nothing used
it. Requiring each narrower subgroup the device allows runs that branch here as well.
"""
import ctypes

import numpy as np
import pytest

from matchedfilter import _vulkan

_devices, _reason = _vulkan.enumerate_devices()
pytestmark = pytest.mark.skipif(not _devices, reason=_reason or "no Vulkan device")


@pytest.fixture(scope="module")
def ctx():
    from conftest import vulkan_runs
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)
    from matchedfilter import _vkcompute
    c = _vkcompute.Context(0)
    yield c
    c.destroy()


#: What a spare output slot past the last pair holds before a dispatch (the tail test).
_SENTINEL = 0x5EED5EED


def _coarse(ctx, band, tile, x, t, subgroup=0, ppg=1, tail=None, twt=1):
    """(peak index, peak value) per (row, template) from one coarse build at `ppg` pairs per
    group, launched as the host launches it (coarse_launch). With `tail` (a list), the output
    buffers carry spare slots past the last pair, seeded with _SENTINEL; their contents after
    the dispatch are appended to it."""
    from matchedfilter import _vkcompute as V
    nd, nt = x.shape[0], t.shape[0]
    spare = 64 if tail is not None else 0
    bufs = [V._Buffer(ctx, x.nbytes), V._Buffer(ctx, nt * band * 4),
            V._Buffer(ctx, (nd * nt + spare) * 4), V._Buffer(ctx, (nd * nt + spare) * 8)]
    vk, cmd = ctx.vk, V._vp()
    try:
        bufs[0].write(x)
        bufs[1].write(V._pack_half2(t))
        if spare:
            bufs[2].write(np.full(nd * nt + spare, _SENTINEL, np.uint32))
            bufs[3].write(np.full(2 * (nd * nt + spare), _SENTINEL, np.uint32))
        pipe, layout, sl = ctx._build_pipeline(
            ("coarse16-test", band, ppg, tile), V.coarse_stem(band, ppg, tile) + ".spv",
            V._NBIND, V._PUSH_BYTES, data_stride=band, subgroup=subgroup, coarse_twt=twt)
        dset = ctx._descriptor_set(sl, bufs)
        slot_val, groups = V.coarse_launch(nd, nt, ppg, tile, band, ragged_groups=True)
        V._check(vk.vkAllocateCommandBuffers(ctx.device, ctypes.byref(
            V._CmdBufAlloc(40, None, ctx.command_pool, 0, 1)), ctypes.byref(cmd)), "alloc")
        V._check(vk.vkBeginCommandBuffer(cmd, ctypes.byref(V._CmdBufBegin(42, None, 0, None))),
                 "begin")
        vk.vkCmdBindPipeline(cmd, V._BIND_POINT_COMPUTE, pipe)
        vk.vkCmdBindDescriptorSets(cmd, V._BIND_POINT_COMPUTE, layout, 0, 1,
                                   (V._vp * 1)(dset), 0, None)
        pc = (ctypes.c_uint32 * 7)(nt, 0, band, slot_val, band.bit_length() - 1, 1, 0)
        vk.vkCmdPushConstants(cmd, layout, V._STAGE_COMPUTE, 0, V._PUSH_BYTES, ctypes.byref(pc))
        vk.vkCmdDispatch(cmd, groups, 1, 1)
        V._check(vk.vkEndCommandBuffer(cmd), "end")
        ctx._submit(cmd)
        vk.vkQueueWaitIdle(ctx.queue)
        idx = bufs[2].read(np.int32, nd * nt).reshape(nd, nt)
        val = bufs[3].read(np.float32, 2 * nd * nt).reshape(nd, nt, 2)
        if spare:
            tail.append(bufs[2].read(np.uint32, nd * nt + spare)[nd * nt:])
            tail.append(bufs[3].read(np.uint32, 2 * (nd * nt + spare))[2 * nd * nt:])
    finally:
        if cmd:
            vk.vkFreeCommandBuffers.argtypes = [V._vp, V._vp, V._u32, ctypes.POINTER(V._vp)]
            vk.vkFreeCommandBuffers(ctx.device, ctx.command_pool, 1, (V._vp * 1)(cmd))
        for b in bufs:
            b.destroy()
    return idx, val


@pytest.mark.parametrize("band", [256, 512, 1024, 2048])
def test_tiles_match_untiled_and_fail_open(ctx, band):
    from matchedfilter import _vkcompute as V
    tiles = V.shipped_tiles(band, 1, V._spv_shipped)
    if not tiles or not V._spv_shipped(V.coarse_stem(band, 1, 1)):
        pytest.skip("no tiled builds at band %d" % band)
    rng = np.random.default_rng(band)
    nd, nt = 3, 9                            # an odd template count: a ragged last tile
    x = (rng.standard_normal((nd, band)) + 1j * rng.standard_normal((nd, band))).astype(np.complex64)
    t = (rng.standard_normal((nt, band)) + 1j * rng.standard_normal((nt, band))).astype(np.complex64)
    x[1] *= 1e5                              # overflows fp16 in the transform
    rngs = getattr(ctx, "subgroup_range", None)
    # Every size the device can be required to run, the default first. The reference is the
    # untiled build at the DEFAULT size: on the Iris Xe every build at 8 and 16 went wrong
    # together, so a same-size reference could not see it.
    sizes = [0] + ([s for s in (4, 8, 16, 32, 64) if rngs[0] <= s < ctx.subgroup_size]
                   if rngs else [])
    ref_idx, ref_val = _coarse(ctx, band, 1, x, t, 0)
    for sg in sizes:
        for tile, twt in ((1, 1), (1, 0)) + tuple((tl, 1) for tl in tiles):
            idx, val = _coarse(ctx, band, tile, x, t, sg, twt=twt)
            where = "band %d tile %d twt %d subgroup %d" % (band, tile, twt, sg or ctx.subgroup_size)
            # The loud row must pass the gate: a listed peak, its value not below any
            # threshold (NaN or inf, which the compaction lists).
            mag = np.hypot(val[1, :, 0], val[1, :, 1])
            assert (idx[1] >= 0).all(), "%s: loud row dismissed: %s" % (where, idx[1])
            assert not (mag < 1e30).any(), "%s: loud row reported finite %s" % (where, mag)
            # Quiet rows: the untiled build's peaks, values to fp16 rounding (finite).
            for r in (0, 2):
                np.testing.assert_array_equal(idx[r], ref_idx[r], err_msg=where)
                assert np.isfinite(val[r]).all(), "%s: row %d values %s" % (where, r, val[r])
                np.testing.assert_allclose(val[r], ref_val[r], rtol=2e-2, atol=1.0,
                                           err_msg=where)


@pytest.mark.parametrize("band", [64, 128, 256, 512, 1024, 2048, 4096])
def test_untiled_groups_are_ragged(ctx, band):
    """An untiled build with several pairs per group runs any pair count (RAGGED GROUPS):
    the last group's spare slots recompute the last pair, at every subgroup size the
    device can require, and write nothing -- each pair's peak is the one-pair build's,
    and the outputs past the last pair are untouched. The exact-divisor rule this replaced
    ran odd counts at one pair per group."""
    from matchedfilter import _vkcompute as V
    ppgs = [p for p in (2, 4, 8, 16, 32) if V._spv_shipped(V.coarse_stem(band, p, 1))]
    if not ppgs or not V._spv_shipped(V.coarse_stem(band, 1, 1)):
        pytest.skip("no packed untiled builds at band %d" % band)
    rng = np.random.default_rng(band + 3)
    nd, nt = 3, 7                            # 21 pairs: no packing divides them
    x = (rng.standard_normal((nd, band)) + 1j * rng.standard_normal((nd, band))).astype(np.complex64)
    t = (rng.standard_normal((nt, band)) + 1j * rng.standard_normal((nt, band))).astype(np.complex64)
    rngs = getattr(ctx, "subgroup_range", None)
    sizes = [0] + ([s for s in (4, 8, 16, 32, 64) if rngs[0] <= s < ctx.subgroup_size]
                   if rngs else [])
    ref_idx, ref_val = _coarse(ctx, band, 1, x, t, 0)
    assert (ref_idx >= 0).all()
    for sg in sizes:
        for ppg in ppgs:
            if (band // 16 * ppg > ctx.max_invocations       # as _coarse_layouts offers them
                    or (band * 17 // 16 + 32) * 4 * ppg > ctx.max_shared_memory):
                continue
            tail = []
            idx, val = _coarse(ctx, band, 1, x, t, sg, ppg=ppg, tail=tail)
            where = "band %d ppg %d subgroup %d" % (band, ppg, sg or ctx.subgroup_size)
            np.testing.assert_array_equal(idx, ref_idx, err_msg=where)
            np.testing.assert_allclose(val, ref_val, rtol=1e-6, atol=0, err_msg=where)
            for part in tail:
                assert (part == _SENTINEL).all(), "%s: wrote past the last pair" % where


@pytest.mark.parametrize("K", [1.0, 32.0])
@pytest.mark.parametrize("band", [128, 256, 512, 1024])
def test_transient_fails_open_in_every_layout(ctx, band, K, monkeypatch):
    """gate_margin's transient family through the production path (hier_peaks, the band read
    out of n-point spectra), in every layout the coarse choice can take -- each subgroup size
    the device allows, each packing and tile, forced: a loud broadband burst in the data and
    templates scaled so every pair's exact maximum is K, so a gate at 0.999 K must pass every
    pair.

    K = 1 is gate_margin's scale: templates of ~5e-5, subnormal in fp16. A device that
    flushes fp16 subnormals (the Iris Xe) dismissed every pair there until the tier placed
    its operands by powers of two (_vkcompute._c16_scales); K = 32 sits in range either way."""
    from matchedfilter import _vkcompute as V
    n, nt = 4096, 16
    rng = np.random.default_rng(band + 7)
    burst = np.zeros(band, complex)
    t0 = int(rng.integers(0, band - 8))
    burst[t0:t0 + 8] = 200.0 * np.exp(1j * np.linspace(0, 6, 8))
    D = (rng.standard_normal(band) + 1j * rng.standard_normal(band)) + np.fft.fft(burst)
    T = rng.standard_normal((nt, band)) + 1j * rng.standard_normal((nt, band))
    exact = np.abs(np.fft.ifft(D[None] * np.conj(T), axis=1) * band).max(1)
    T = T / exact[:, None] * K
    data = (np.random.default_rng(0).standard_normal((1, n)) * 1e-3).astype(np.complex64)
    data[0, :band] = D
    tmpl = np.zeros((nt, n), np.complex64)
    tmpl[:, :band] = T
    ct0 = np.ascontiguousarray(tmpl[:, :band])
    rngs = getattr(ctx, "subgroup_range", None)
    sizes = [ctx.subgroup_size] + ([s for s in (8, 16, 32, 64) if rngs[0] <= s < ctx.subgroup_size]
                                   if rngs else [])
    for sg in sizes:
        for ppg in (1, 2, 4, 8, 16):
            for tile, twt in [(1, 1), (1, 0)] + [(t, 1) for t in
                                                  V.shipped_tiles(band, ppg, V._spv_shipped)]:
                if not V._spv_shipped(V.coarse_stem(band, ppg, tile)):
                    continue
                monkeypatch.setenv("MF_VK_COARSE_SUBGROUP", str(sg))
                monkeypatch.setenv("MF_VK_COARSE_PPG", str(ppg))
                monkeypatch.setenv("MF_VK_COARSE_TILE", str(tile))
                monkeypatch.setenv("MF_VK_COARSE_TWT", str(twt))   # untiled: table and recurrence
                c = V.Context(0)              # recorded plans are cached per context, not per layout
                try:
                    idx, _ = c.hier_peaks(n, band, data, tmpl, ct0, 0.999 * K, binsize=n, threshold=0.0)
                    geom = c._coarse_geometry(band, 1, nt)
                finally:
                    c.destroy()
                where = "band %d subgroup %d ppg %d tile %d twt %d (ran %s)" % (
                    band, sg, ppg, tile, twt, (geom[:3], geom[5]))
                lost = int((idx.reshape(nt) < 0).sum())
                assert not lost, "%s: gate dismissed %d of %d pairs" % (where, lost, nt)
