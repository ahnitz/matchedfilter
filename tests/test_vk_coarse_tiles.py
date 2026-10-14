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


def _coarse(ctx, band, tile, x, t, subgroup=0):
    """(peak index, peak value) per (row, template) from one coarse build, one pair per group."""
    from matchedfilter import _vkcompute as V
    nd, nt = x.shape[0], t.shape[0]
    bufs = [V._Buffer(ctx, x.nbytes), V._Buffer(ctx, nt * band * 4),
            V._Buffer(ctx, nd * nt * 4), V._Buffer(ctx, nd * nt * 8)]
    vk, cmd = ctx.vk, V._vp()
    try:
        bufs[0].write(x)
        bufs[1].write(V._pack_half2(t))
        pipe, layout, sl = ctx._build_pipeline(
            ("coarse16-test", band, 1, tile), V.coarse_stem(band, 1, tile) + ".spv",
            V._NBIND, V._PUSH_BYTES, data_stride=band, subgroup=subgroup)
        dset = ctx._descriptor_set(sl, bufs)
        slot_val, groups = V.coarse_launch(nd, nt, 1, tile, band)
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
    # Every size the layout choice can pick (_coarse_layouts), the default first.
    sizes = [0] + ([s for s in (4, 8, 16, 32, 64) if rngs[0] <= s < ctx.subgroup_size]
                   if rngs else [])
    for sg in sizes:
        ref_idx, ref_val = _coarse(ctx, band, 1, x, t, sg)
        for tile in tiles:
            idx, val = _coarse(ctx, band, tile, x, t, sg)
            where = "band %d tile %d subgroup %d" % (band, tile, sg or ctx.subgroup_size)
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
