"""Follow-ups (_gpuhost.FollowupSpec) on Vulkan as one fixed recording per template group.

The host path runs each selected follow-up as a single-template filter_series call: per
template group a forward of the windows' blocks and one peaks_items submission, recorded
afresh almost every segment (the rows, workspace and allocation combinations never repeat).
Here every follow-up of a batch is a listed entry (data row, template, window, output slot)
for the refineItems kernel (src/gpu/refine_bounded.slang, shared with CUDA), and each
template group runs one recording made once and replayed every segment:

  per series allocation (a fixed workspace region each): forward of the region's rows,
  dispatched indirectly (row count written by the host);
  refineItems over the group's entry list (count read on the device).

The host still selects (FollowupSpec.select) and lays out the blocks with
TimeDomainFilterBank._window_layout, so the windows are the host path's by construction; the
results are assembled exactly as _items_batch assembles them. Anything outside the fixed
capacities, a block reading past its series (the host path pads with zeros), or a backend
other than Vulkan returns None and the caller runs the follow-ups on the host.
"""
import ctypes

import numpy as np

from . import _vkcompute as vkc
from ._shared import containing, shared_buffer
from ._gpuhost import bin_shift, MAX_BINS


class Unsupported(Exception):
    pass


#: Workspace rows per series allocation region, regions per group, entries per group.
REGION_ROWS = 256
REGIONS = 1
MAX_ENTRIES = 512
#: Workgroups the refineItems grid strides with.
GRID = 64


class _Workspace:
    """Buffers, descriptor sets and recording for one group of a submission.

    Pooled per (n, nbins, allocations, slot of the group within its submission) and shared by
    every template group: a group's templates and its series allocations are bindings,
    rewritten in place (vkUpdateDescriptorSets) when they change, and the short recording is
    redone only then. A steady search therefore creates no buffer, descriptor pool or
    workspace after warm-up, however its follow-ups spread over template groups."""

    def __init__(self, ctx, n, nbins, nalloc):
        self.ctx, self.n, self.nbins = ctx, n, nbins
        rows = REGION_ROWS * REGIONS
        self.spec = ctx.empty_shared((rows, n))
        self.starts = ctx.empty_shared(rows, np.uint32)
        self.items = vkc._Buffer(ctx, MAX_ENTRIES * 5 * 4)
        self.count = vkc._Buffer(ctx, 16)
        self.args = [vkc._Buffer(ctx, 12, usage=vkc._BUF_STORAGE | vkc._BUF_INDIRECT
                                 | vkc._BUF_TRANSFER_DST) for _ in range(nalloc)]
        self.idx = vkc._Buffer(ctx, MAX_ENTRIES * nbins * 4, readback=True)
        self.val = vkc._Buffer(ctx, MAX_ENTRIES * nbins * 8, readback=True)
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
        self.fsets = [ctx._descriptor_set(fsl, self._fbufs(self.dummy, a)[0],
                                          self._fbufs(self.dummy, a)[1])
                      for a in range(nalloc)]
        ib, io = self._ibufs(self.dummy)
        self.iset = ctx._descriptor_set(isl, ib, io)
        self.bound = None                # (templates array, allocations, nt, binsize) recorded
        self.cmd = None

    def _fbufs(self, whole, a):
        r0 = a * REGION_ROWS
        b = [whole if isinstance(whole, vkc._Buffer) else shared_buffer(whole, self.ctx),
             self.b_starts, self.b_spec]
        return b, [getattr(b[0], "offset", 0), getattr(b[1], "offset", 0) + r0 * 4,
                   getattr(b[2], "offset", 0) + r0 * self.n * 8]

    def _ibufs(self, tmpl):
        b = [self.dummy] * self.nlead + [self.b_spec, tmpl, self.idx, self.val, self.items,
                                         self.count]
        return b, [getattr(x, "offset", 0) for x in b]

    def bind(self, plan, allocs, binsize):
        """Point the workspace at this group (its templates, its series allocations) and
        make sure the recording matches. The caller has collected any submission in flight."""
        key = (plan._gtmpl, tuple(allocs), int(plan._gtmpl.shape[0]), int(binsize))
        b = self.bound
        if b is not None and b[0] is key[0] and b[2:] == key[2:] and len(b[1]) == len(key[1]) \
                and all(x is y for x, y in zip(b[1], key[1])):
            return False
        tmpl = shared_buffer(plan._gtmpl, self.ctx)
        if tmpl is None:
            raise Unsupported("templates are not device-resident")
        if b is None or b[0] is not key[0]:
            _rewrite(self.ctx, self.iset, *self._ibufs(tmpl))
        for a, whole in enumerate(allocs):
            if b is None or b[1][a] is not whole:
                _rewrite(self.ctx, self.fsets[a], *self._fbufs(whole, a))
        self._record(key[2], key[3], allocs)
        self.bound = key
        return True

    def _record(self, nt, binsize, allocs):
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
        for a, whole in enumerate(allocs):
            vk.vkCmdBindDescriptorSets(cmd, vkc._BIND_POINT_COMPUTE, self.flayout, 0, 1,
                                       (vkc._vp * 1)(self.fsets[a]), 0, None)
            vk.vkCmdPushConstants(cmd, self.flayout, vkc._STAGE_COMPUTE, 0, 4,
                                  ctypes.byref(vkc._u32(whole.size)))
            vk.vkCmdDispatchIndirect(cmd, self.args[a].handle, 0)
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
        """FilterResults of single-template follow-up jobs [(bank, series, kwargs)] -- each
        filter_series(series, windows=, binsize=, threshold=0, template_index=) -- as
        _items_batch gives them; raises Unsupported when they cannot all run here."""
        from .time_domain import TimeDomainFilterBank, _normalize_windows
        groups = {}                                    # (id(plan), binsize) -> group work
        layout = []                                    # per job: (group, st, ws, we, first slot)
        for (bank, ser, kw) in jobs:
            kw = kw or {}
            ti = kw.get("template_index")
            if ti is None or kw.get("threshold") is None or float(kw["threshold"]) != 0.0 \
                    or set(kw) - {"windows", "binsize", "threshold", "template_index"}:
                raise Unsupported("not a threshold-0 single-template call")
            g, tl = bank._template_map[ti]
            bs = int(kw["binsize"]) if kw.get("binsize") is not None else (bank.binsize or g.n)
            if bs >= g.n:
                raise Unsupported("binsize spans a block")
            S = len(ser)
            W = _normalize_windows(kw["windows"], S)
            st, ws, we = TimeDomainFilterBank._window_layout(g, W, S)
            plan = g.get_flat_plan()
            ctx = getattr(plan, "_gpu", None)
            if not isinstance(ctx, vkc.Context) or plan._gtmpl is None:
                raise Unsupported("not a Vulkan plan")
            c = containing(np.ascontiguousarray(ser), ctx)
            if c is None:
                raise Unsupported("series not device-resident")
            if st.size and int(st.max()) + g.n > ser.size:
                raise Unsupported("a block reads past the series")
            # One record per (template group, binsize, series allocation): a group searching
            # two detectors' allocations uses two records rather than one per combination and
            # order of allocations, which would rarely repeat.
            gw = groups.setdefault((id(plan), bs, id(c[0])), dict(plan=plan, ctx=ctx, n=g.n, bs=bs,
                                                        allocs=[], entries=[],
                                                        rows=[[] for _ in range(REGIONS)]))
            wid = [i for i, a in enumerate(gw["allocs"]) if a is c[0]]
            if not wid:
                if len(gw["allocs"]) >= REGIONS:
                    raise Unsupported("more series allocations than regions")
                gw["allocs"].append(c[0])
                wid = [len(gw["allocs"]) - 1]
            a = wid[0]
            first = len(gw["entries"])
            n = g.n
            for k in range(int(st.size)):
                row = len(gw["rows"][a])
                if row >= REGION_ROWS:
                    raise Unsupported("region full")
                gw["rows"][a].append(min(int(st[k]), ser.size) + c[1])
                lo, hi = min(int(ws[k]), n), min(int(we[k]), n)
                gw["entries"].append((a * REGION_ROWS + row, tl, lo, hi))
            if len(gw["entries"]) > MAX_ENTRIES:
                raise Unsupported("too many entries")
            layout.append((gw, st, ws, we, first, g, tl, ti))
        if not groups:
            return []
        cmds, recs = [], []
        slots = {}
        for gw in groups.values():
            bs = gw["bs"]
            nbins = max([1] + [-(-(hi - lo) // bs) for _, _, lo, hi in gw["entries"]])
            nbins = 1 << (nbins - 1).bit_length()      # few distinct recordings
            if nbins > MAX_BINS:
                raise Unsupported("window has too many bins")
            gw["nbins"] = nbins
            # Groups of one submission take distinct workspaces (slot 0, 1, ... per shape).
            shape = (gw["n"], nbins, len(gw["allocs"]))
            slot = slots[shape] = slots.get(shape, -1) + 1
            ws = self.workspaces.get(shape + (slot,))
            if ws is None:
                ws = self.workspaces[shape + (slot,)] = _Workspace(gw["ctx"], *shape)
            pending = ws.pending
            if pending is not None:
                pending()                          # its tables and outputs are rewritten below
            ws.bind(gw["plan"], gw["allocs"], bs)
            rec = ws
            for a in range(len(gw["allocs"])):
                rows = np.asarray(gw["rows"][a], np.uint32)
                rec.starts[a * REGION_ROWS:a * REGION_ROWS + rows.size] = rows
                rec.args[a].write(np.array([rows.size, 1, 1], np.uint32))
            ent = np.asarray([(d, t, lo, hi, s) for s, (d, t, lo, hi) in enumerate(gw["entries"])],
                             np.uint32).reshape(-1, 5)
            rec.items.write(ent)
            rec.count.write(np.array([len(ent), 0, 0, 0], np.uint32))
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
                done.append(self._assemble(layout))
            return done[0]
        for rec in recs:
            rec.pending = collect
        return collect

    @staticmethod
    def _assemble(layout):
        # Assemble as _items_batch does: per item, its blocks' bins, per bin count.
        from .time_domain import _consume_into, _results_from
        reads = {}
        out = []
        for gw, st, ws, we, first, g, tl, ti in layout:
            rec, nbins, bs = gw["rec"], gw["nbins"], gw["bs"]
            r = reads.get(id(gw))
            if r is None:
                m = len(gw["entries"])
                r = reads[id(gw)] = (rec.idx.read(np.int32, m * nbins).reshape(m, nbins),
                                      rec.val.read(np.complex64, m * nbins).reshape(m, nbins))
            k = int(st.size)
            idx = r[0][first:first + k].astype(np.int64).reshape(k, 1, nbins)
            val = r[1][first:first + k].reshape(k, 1, nbins)
            counts = ((we - ws + bs - 1) // bs).astype(np.int64)
            lists = ([], [], [], [], [])
            stt = st.astype(np.int64)
            for u in np.unique(counts):
                mk = counts == u
                _consume_into(lists, idx[mk][:, :, :u], val[mk][:, :, :u], stt[mk], g,
                              (tl, 1), g.n, ti)
            out.append(_results_from(lists))
        return out


_EXECUTORS = {}


def submit_jobs(jobs):
    """A collector giving the FilterResults of single-template follow-up jobs, submitted on
    Vulkan without waiting; or None (the host path)."""
    if not jobs:
        return lambda: []
    try:
        bank, _, kw = jobs[0]
        g, _ = bank._template_map[(kw or {}).get("template_index")]
        ctx = getattr(g.get_flat_plan(), "_gpu", None)
        if not isinstance(ctx, vkc.Context):
            return None
        ex = _EXECUTORS.setdefault(id(ctx._device_state), Executor())
        return ex.submit_jobs(jobs)
    except (Unsupported, KeyError, TypeError):
        return None


def run_jobs(jobs):
    """FilterResults for single-template follow-up jobs on Vulkan, or None (host path)."""
    if not jobs:
        return []
    try:
        bank, _, kw = jobs[0]
        g, _ = bank._template_map[(kw or {}).get("template_index")]
        ctx = getattr(g.get_flat_plan(), "_gpu", None)
        if not isinstance(ctx, vkc.Context):
            return None
        ex = _EXECUTORS.setdefault(id(ctx._device_state), Executor())
        return ex.run_jobs(jobs)
    except (Unsupported, KeyError, TypeError):
        return None


def run(spec, sel):
    """FollowupSpec results for sel (FollowupSpec.select's list) on Vulkan, or None."""
    res = run_jobs([s[4] for s in sel])
    if res is None:
        return None
    return [(j, rank, c0, ti, r) for (j, rank, c0, ti, _), r in zip(sel, res)]
