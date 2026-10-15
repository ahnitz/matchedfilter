"""Vulkan coarse builds launched directly, without the host's choice: an untiled build with
several pairs per group runs any pair count and writes nothing past the last pair, at every
subgroup size the device can require. Every layout through the production path, on every
backend, is tests/test_coarse_conformance.py."""
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
        slot_val, groups = V.coarse_launch(nd, nt, ppg, tile, band)
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
