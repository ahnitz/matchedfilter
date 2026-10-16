"""Device follow-ups on Vulkan: the executor for _gpuhost.followup_layout's groups.

The host path runs each selected follow-up as a single-template filter_series call: per
template group a forward of the windows' blocks and one peaks_items submission, recorded
afresh almost every segment (the rows, workspace and allocation combinations never repeat).
Here each work group runs one recording made once and replayed every segment:

  forward of the group's rows from its series allocation, dispatched indirectly (row count
  written by the host);
  refineItems over the group's entry list (count read on the device).

Every group of a batch goes out in one submission. Anything past the fixed capacities returns
None from _gpuhost.submit_followups, and the caller runs the follow-ups on the host.
"""
import ctypes

import numpy as np

from . import _vkcompute as vkc
from ._shared import shared_buffer
from ._gpuhost import FollowupUnsupported as Unsupported, assemble_followups, bin_shift, \
    followup_layout

#: Workspace rows (= entries) per group.
ROWS = 256
#: Workgroups the refineItems grid strides with.
GRID = 64


class _Workspace:
    """Buffers, descriptor sets and recording for one group of a submission.

    Pooled per (n, nbins, slot of the group within its submission) and shared by every
    template group: a group's templates and its series allocation are bindings,
    rewritten in place (vkUpdateDescriptorSets) when they change, and the short recording is
    redone only then. A steady search therefore creates no buffer, descriptor pool or
    workspace after warm-up, however its follow-ups spread over template groups."""

    def __init__(self, ctx, n, nbins):
        self.ctx, self.n, self.nbins = ctx, n, nbins
        self.spec = ctx.empty_shared((ROWS, n))
        self.starts = ctx.empty_shared(ROWS, np.uint32)
        self.items = vkc._Buffer(ctx, ROWS * 5 * 4)
        self.count = vkc._Buffer(ctx, 16)
        self.args = vkc._Buffer(ctx, 12, usage=vkc._BUF_STORAGE | vkc._BUF_INDIRECT
                                | vkc._BUF_TRANSFER_DST)
        self.idx = vkc._Buffer(ctx, ROWS * nbins * 4, readback=True)
        self.val = vkc._Buffer(ctx, ROWS * nbins * 8, readback=True)
        self.dummy = vkc._Buffer(ctx, 64)
        self.pending = None              # the collector of the submission in flight, if any
        self.b_spec = shared_buffer(self.spec, ctx)
        self.b_starts = shared_buffer(self.starts, ctx)
        self.fpipe, self.flayout, fsl = ctx._build_pipeline(("forward", n), "forward_%d.spv" % n,
                                                            3, 4)
        info = (vkc._manifest().get("modules", {}).get(str(n)) or {}).get("items")
        if info is None:
            raise Unsupported("no refineItems module for n=%d" % n)
        file = info["file"]
        if info.get("portable") and (vkc._manifest()["modules"][str(n)].get("lds_bytes", 0)
                                     > ctx.max_shared_memory):
            file = info["portable"]["file"]
        self.ipipe, self.ilayout, isl = ctx._build_pipeline(("items", file), file, 6, 24,
                                                            subgroup=ctx._fit_subgroup(n))
        # The module's entry parameters are its LAST six bindings: tierb.slang's global
        # resources (unused here) take the first ones; the dummy fills those.
        self.nlead = vkc._module_bindings((vkc._SPIRV / file).read_bytes()) - 6
        if self.nlead < 0:
            raise Unsupported("unexpected refineItems bindings")
        # Made once, against placeholders; _bind writes the real bindings before any use.
        self.fset = ctx._descriptor_set(fsl, *self._fbufs(self.dummy))
        ib, io = self._ibufs(self.dummy)
        self.iset = ctx._descriptor_set(isl, ib, io)
        self.bound = None                # (templates array, allocation, nt, binsize) recorded
        self.cmd = None

    def _fbufs(self, whole):
        b = [whole if isinstance(whole, vkc._Buffer) else shared_buffer(whole, self.ctx),
             self.b_starts, self.b_spec]
        return b, [getattr(x, "offset", 0) for x in b]

    def _ibufs(self, tmpl):
        b = [self.dummy] * self.nlead + [self.b_spec, tmpl, self.idx, self.val, self.items,
                                         self.count]
        return b, [getattr(x, "offset", 0) for x in b]

    def bind(self, plan, alloc, binsize):
        """Point the workspace at this group (its templates, its series allocation) and make
        sure the recording matches. The caller has collected any submission in flight."""
        key = (plan._gtmpl, alloc, int(plan._gtmpl.shape[0]), int(binsize))
        b = self.bound
        if b is not None and b[0] is key[0] and b[1] is key[1] and b[2:] == key[2:]:
            return False
        tmpl = shared_buffer(plan._gtmpl, self.ctx)
        if tmpl is None:
            raise Unsupported("templates are not device-resident")
        if b is None or b[0] is not key[0]:
            _rewrite(self.ctx, self.iset, *self._ibufs(tmpl))
        if b is None or b[1] is not alloc:
            _rewrite(self.ctx, self.fset, *self._fbufs(alloc))
        self._record(key[2], key[3], alloc)
        self.bound = key
        return True

    def _record(self, nt, binsize, alloc):
        ctx, vk, _check = self.ctx, self.ctx.vk, vkc._check
        if self.cmd is not None:
            vk.vkFreeCommandBuffers.argtypes = [vkc._vp, vkc._vp, vkc._u32,
                                                ctypes.POINTER(vkc._vp)]
            vk.vkFreeCommandBuffers(ctx.device, ctx.command_pool, 1, (vkc._vp * 1)(self.cmd))
            self.cmd = None
        cmd = vkc._vp()
        _check(vk.vkAllocateCommandBuffers(ctx.device, ctypes.byref(
            vkc._CmdBufAlloc(40, None, ctx.command_pool, 0, 1)), ctypes.byref(cmd)),
            "allocate follow-ups")
        _check(vk.vkBeginCommandBuffer(cmd, ctypes.byref(vkc._CmdBufBegin(42, None, 0, None))),
               "begin follow-ups")
        # Earlier submissions on this queue -- the middle stage writing the series, left in
        # flight (correlate_series(wait=False)) -- are made visible here, on the device, so the
        # host never waits for them.
        mb0 = vkc._MemBarrier(46, None, vkc._ACCESS_SHADER_WRITE | vkc._ACCESS_TRANSFER_WRITE,
                              vkc._ACCESS_SHADER_READ)
        vk.vkCmdPipelineBarrier(cmd, vkc._STAGE_COMPUTE_BIT | vkc._STAGE_TRANSFER_BIT,
                                vkc._STAGE_COMPUTE_BIT | vkc._STAGE_DRAW_INDIRECT_BIT, 0, 1,
                                ctypes.byref(mb0), 0, None, 0, None)
        vk.vkCmdBindPipeline(cmd, vkc._BIND_POINT_COMPUTE, self.fpipe)
        vk.vkCmdBindDescriptorSets(cmd, vkc._BIND_POINT_COMPUTE, self.flayout, 0, 1,
                                   (vkc._vp * 1)(self.fset), 0, None)
        vk.vkCmdPushConstants(cmd, self.flayout, vkc._STAGE_COMPUTE, 0, 4,
                              ctypes.byref(vkc._u32(alloc.size)))
        vk.vkCmdDispatchIndirect(cmd, self.args.handle, 0)
        mb = vkc._MemBarrier(46, None, vkc._ACCESS_SHADER_WRITE, vkc._ACCESS_SHADER_READ)
        vk.vkCmdPipelineBarrier(cmd, vkc._STAGE_COMPUTE_BIT, vkc._STAGE_COMPUTE_BIT, 0, 1,
                                ctypes.byref(mb), 0, None, 0, None)
        vk.vkCmdBindPipeline(cmd, vkc._BIND_POINT_COMPUTE, self.ipipe)
        vk.vkCmdBindDescriptorSets(cmd, vkc._BIND_POINT_COMPUTE, self.ilayout, 0, 1,
                                   (vkc._vp * 1)(self.iset), 0, None)
        pc = (vkc._u32 * 6)(nt, int(binsize), bin_shift(binsize) & 0xFFFFFFFF, self.nbins, 0,
                            GRID)
        vk.vkCmdPushConstants(cmd, self.ilayout, vkc._STAGE_COMPUTE, 0, 24, ctypes.byref(pc))
        vk.vkCmdDispatch(cmd, GRID, 1, 1)
        mb = vkc._MemBarrier(46, None, vkc._ACCESS_SHADER_WRITE, vkc._ACCESS_HOST_READ)
        vk.vkCmdPipelineBarrier(cmd, vkc._STAGE_COMPUTE_BIT, vkc._STAGE_HOST_BIT, 0, 1,
                                ctypes.byref(mb), 0, None, 0, None)
        _check(vk.vkEndCommandBuffer(cmd), "end follow-ups")
        self.cmd = cmd


def _rewrite(ctx, dset, bufs, offsets):
    """Rewrite every binding of a descriptor set in place (as _descriptor_set writes them)."""
    n = len(bufs)
    infos = (vkc._DescBufferInfo * n)(
        *[vkc._DescBufferInfo(b.handle, o, b.nbytes + getattr(b, "offset", 0) - o)
          for b, o in zip(bufs, offsets)])
    writes = (vkc._WriteDescSet * n)(*[
        vkc._WriteDescSet(35, None, dset, i, 0, 1, vkc._DESC_STORAGE_BUFFER, None,
                          ctypes.pointer(infos[i]), None) for i in range(n)])
    ctx.vk.vkUpdateDescriptorSets(ctx.device, n, writes, 0, None)


class Executor:
    """Device follow-ups for one Vulkan device: records per template group, reused."""

    def __init__(self):
        self.workspaces = {}

    def run_jobs(self, jobs):
        return self.submit_jobs(jobs)()

    def submit_jobs(self, jobs):
        """A collector giving the FilterResults of single-template follow-up jobs
        [(bank, series, kwargs)] as _items_batch gives them, submitted without waiting;
        raises Unsupported when they cannot all run here."""
        groups, layout = followup_layout(jobs, vkc.Context, max_rows=ROWS)
        if not groups:
            return lambda: []
        cmds, recs = [], []
        slots = {}
        for gw in groups:
            # Groups of one submission take distinct workspaces (slot 0, 1, ... per shape).
            shape = (gw["n"], gw["nbins"])
            slot = slots[shape] = slots.get(shape, -1) + 1
            rec = self.workspaces.get(shape + (slot,))
            if rec is None:
                rec = self.workspaces[shape + (slot,)] = _Workspace(gw["ctx"], *shape)
            if rec.pending is not None:
                rec.pending()                      # its tables and outputs are rewritten below
            rec.bind(gw["plan"], gw["alloc"], gw["bs"])
            m = gw["rows"].size
            rec.starts[:m] = gw["rows"]
            rec.args.write(np.array([m, 1, 1], np.uint32))
            rec.items.write(gw["entries"])
            rec.count.write(np.array([m, 0, 0, 0], np.uint32))
            gw["rec"] = rec
            cmds.append(rec.cmd)
            recs.append(rec)
        dev = recs[0].ctx._device_state
        vk = dev.vk
        arr = (vkc._vp * len(cmds))(*cmds)
        submit = vkc._SubmitInfo(4, None, 0, None, None, len(cmds), arr, 0, None)
        fence = vkc._vp()
        vkc._check(vk.vkCreateFence(dev.device, ctypes.byref(vkc._FenceCreate(8, None, 0)), None,
                                    ctypes.byref(fence)), "vkCreateFence")
        try:
            vkc._check(vk.vkQueueSubmit(dev.queue, 1, ctypes.byref(submit), fence),
                       "vkQueueSubmit")
        except BaseException:
            vk.vkDestroyFence(dev.device, fence, None)
            raise
        done = []

        def read(gw):
            m, nbins = gw["rows"].size, gw["nbins"]
            return (gw["rec"].idx.read(np.int32, m * nbins).reshape(m, nbins),
                    gw["rec"].val.read(np.complex64, m * nbins).reshape(m, nbins))

        def collect():
            """Wait for the submission and assemble every job's results (once)."""
            if not done:
                try:
                    vkc._check(vk.vkWaitForFences(dev.device, 1, (vkc._vp * 1)(fence), 1,
                                                  0xFFFFFFFFFFFFFFFF), "vkWaitForFences")
                finally:
                    vk.vkDestroyFence(dev.device, fence, None)
                    for rec in recs:
                        if rec.pending is collect:
                            rec.pending = None
                done.append(assemble_followups(layout, read))
            return done[0]
        for rec in recs:
            rec.pending = collect
        return collect


def executor(ctx):
    """The device's follow-up executor, held by the device state itself: a dict keyed by
    id(device state) could hand a new device a dead one's executor at a reused address."""
    ds = ctx._device_state
    ex = getattr(ds, "_followups", None)
    if ex is None:
        ex = ds._followups = Executor()
    return ex
