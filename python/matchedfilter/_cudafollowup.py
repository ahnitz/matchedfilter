"""Device-side follow-ups for a CUDA segment graph (SegmentPlan, FollowUp).

The fine stage's sparse peaks are turned into follow-up windows on the device
(src/gpu/followup.cu): select (threshold, rank, one per dedupe interval), lay each window on
its group's block grid, forward the partner series' blocks, and refine each block against
the peak's template (refineItems, src/gpu/refine_bounded.slang). Everything is enqueued inside
the segment capture after the fine stage, so a replay runs it with no host round trip; the
host reads the item list and the peaks back with the rest of the segment and assembles
FilterResults exactly as TimeDomainFilterBank._items_batch does.

Every capacity is fixed at capture; a segment that exceeds one (a flag the kernels set) has
its follow-ups redone on the host path, so results never depend on the capacities.
"""
import ctypes

import numpy as np

from . import _cudacompute as cc

from ._gpuhost import FOLLOWUP_ITEM_WORDS as IT

DT, JT, GT = 16, 8, 8


class Unsupported(Exception):
    pass


class DeviceFollowUps:
    """Built inside a segment capture, from the traced fine stage; read after each run."""

    def __init__(self, ctx, graph, spec, jobs, per_job):
        """per_job[j] = the job's trace entries: [(deferred, sub_starts, g, tmpl_arg, N)]."""
        from ._shared import containing
        self.ctx, self.graph, self.spec, self.jobs = ctx, graph, spec, jobs
        cu = ctx.cuda
        if getattr(spec, "pairs", None) is None:
            raise Unsupported("no partner map")
        # ---- jobs: series allocations and offsets ---------------------------------------
        self.alloc_ids, jinfo = {}, []
        for j, (bank, series, kw) in enumerate(jobs):
            c = containing(np.ascontiguousarray(series), ctx)
            if c is None:
                raise Unsupported("a job's series is not device memory")
            aid = self.alloc_ids.setdefault(id(c[0]), (len(self.alloc_ids), c[0]))[0]
            jinfo.append((aid, int(c[1]), int(series.size)))
        self.jinfo = jinfo
        # ---- dispatches and follow-up groups ---------------------------------------------
        dtab, dgroup, jtab = [], [], np.zeros((len(jobs), JT), np.uint32)
        self.keep = []                          # host arrays the device tables point into
        fu_groups, fu_list = {}, []             # (id(g), partner alloc) -> id
        regions = {}                            # (n, alloc) -> id
        for j, entries in enumerate(per_job):
            bank = jobs[j][0]
            partner = int(spec.pairs[j])
            p_alloc = jinfo[partner][0]
            jtab[j, 0] = len(dtab)
            for e, (d, sub_starts, g, tmpl_arg, N) in enumerate(entries):
                if tmpl_arg is not None:
                    raise Unsupported("single-template fine calls")
                t = d.trace
                nt, nb = int(t["shape"][1]), int(t["shape"][2])
                order = t["order"]
                nblk = int(t["shape"][0])
                caller = (np.arange(nblk, dtype=np.uint32) if order is None
                          else np.asarray(order, dtype=np.uint32))
                samp = np.asarray(sub_starts, dtype=np.int64)[caller.astype(np.int64)]
                tg = np.ascontiguousarray(g.template_indices, dtype=np.int64)
                dev = [self._const(caller), self._const(samp), self._const(tg)]
                key = (id(g), p_alloc)
                gid = fu_groups.get(key)
                if gid is None:
                    fp = g.get_flat_plan()
                    if getattr(fp, "_gpu", None) is None or fp._gtmpl is None:
                        raise Unsupported("no GPU flat plan for a group")
                    rid = regions.setdefault((g.n, p_alloc), len(regions))
                    gid = fu_groups[key] = len(fu_list)
                    fu_list.append(dict(g=g, fp=fp, region=rid, n=g.n, step=int(g.n_valid),
                                        cbad=int(g.c_bad)))
                for b0, b1, entry in t["groups"]:
                    sp = getattr(entry, "sparse_dev", None)
                    if sp is None:
                        raise Unsupported("a fine dispatch without device sparse peaks")
                    row = np.zeros(DT, np.uint32)
                    row[0], row[1], row[2], row[3] = j, e, nt, nb
                    row[4], row[5] = b0, b1 - b0
                    row[6:8] = _u64(sp[1])
                    row[8:10] = _u64(sp[0])
                    row[10:12] = _u64(dev[1].dptr.value)
                    row[12:14] = _u64(dev[0].dptr.value)
                    row[14:16] = _u64(dev[2].dptr.value)
                    dtab.append(row)
                    dgroup.append(gid)
            jtab[j, 1] = len(dtab) - jtab[j, 0]
            jtab[j, 2] = partner
            jtab[j, 4] = jinfo[j][2]
            jtab[j, 5:7] = _u64(jinfo[j][1])
        if not dtab:
            raise Unsupported("no fine dispatches")
        self.fu_list, self.regions = fu_list, regions
        half, bs = int(spec.half), int(spec.binsize)
        self.bpi = max(fu["step"] and (2 * half) // fu["step"] + 3 for fu in fu_list)
        self.max_items = int(spec.max_items)
        rcap = np.full(len(regions), int(spec.max_items_per_region), np.uint32)
        self.nbins = max(-(-fu["step"] // bs) + 1 for fu in fu_list)
        gtab = np.zeros((len(fu_list), GT), np.uint32)
        for i, fu in enumerate(fu_list):
            gtab[i, 0], gtab[i, 1], gtab[i, 2] = fu["n"], fu["step"], fu["cbad"]
            gtab[i, 3], gtab[i, 4] = fu["region"], i
        lcap = np.full(len(fu_list), int(spec.max_items_per_region) * self.bpi, np.uint32)
        lbase = np.concatenate([[0], np.cumsum(lcap)[:-1]]).astype(np.uint32)
        self.lbase = lbase
        rrows = rcap * self.bpi
        rbase = np.concatenate([[0], np.cumsum(rrows)[:-1]]).astype(np.uint32)
        # ---- device buffers ---------------------------------------------------------------
        self.t_d = self._const(np.ascontiguousarray(np.stack(dtab)))
        self.t_dg = self._const(np.asarray(dgroup, np.uint32))
        self.t_j = self._const(jtab)
        self.t_g = self._const(gtab)
        self.t_rcap = self._const(rcap)
        self.t_lcap = self._const(lcap)
        self.t_lbase = self._const(lbase)
        self.t_rbase = self._const(rbase)
        self.items = cc._Buffer(ctx, self.max_items * IT * 4)
        self.counts = cc._Buffer(ctx, 4 * (1 + len(regions)))
        self.flags = cc._Buffer(ctx, 16)
        self.starts = cc._Buffer(ctx, 4 * int(rrows.sum()))
        self.lists = cc._Buffer(ctx, 20 * int(lcap.sum()))
        self.lcounts = cc._Buffer(ctx, 4 * len(fu_list))
        nslot = self.max_items * self.bpi * self.nbins
        self.idx = cc._Buffer(ctx, 4 * nslot)
        self.val = cc._Buffer(ctx, 8 * nslot)
        self.host = cc._Pinned(ctx, 16 + 4 * (1 + len(regions)) + self.max_items * IT * 4
                               + 12 * nslot)
        self.nslot = nslot
        # Region spectra: rows rcap * bpi of n complex64 each.
        self.spec_bufs = []
        for (n, aid), rid in sorted(regions.items(), key=lambda kv: kv[1]):
            self.spec_bufs.append((n, aid, cc._Buffer(ctx, int(rrows[rid]) * n * 8), int(rbase[rid]),
                                   int(rrows[rid])))
        self.allocs = {aid: whole for aid, whole in self.alloc_ids.values()}
        mod = cc._PTX_DIR / "followup.ptx"
        if not mod.is_file():
            raise Unsupported("followup.ptx not built")
        self.f_select = ctx._load("followup", mod, "fuSelect", 256)
        self.f_blocks = ctx._load("followup", mod, "fuBlocks", 256)
        self.items_fn = {}
        for fu in fu_list:
            n = fu["n"]
            if n not in self.items_fn:
                f = cc._PTX_DIR / ("items_%d.ptx" % n)
                if cc._static_shared(f) > cc._STATIC_SHARED_MAX:
                    f = cc._PTX_DIR / ("items_%d_lds32.ptx" % n)
                if not f.is_file():
                    raise Unsupported("no refineItems build for n=%d" % n)
                self.items_fn[n] = (ctx._load(f.stem, f, "refineItems", n // cc._radix(n)),
                                    n // cc._radix(n))

    def _const(self, arr):
        """A device copy of a static host table, uploaded by a captured copy from pinned
        staging (both kept alive with this object)."""
        arr = np.ascontiguousarray(arr)
        dev = cc._Buffer(self.ctx, max(arr.nbytes, 16))
        pin = cc._Pinned(self.ctx, max(arr.nbytes, 16))
        ctypes.memmove(pin.ptr, arr.ctypes.data, arr.nbytes)
        self.ctx._copy_h2d(dev.dptr.value, pin.ptr, arr.nbytes, self.graph.streams[0], "upload")
        self.keep.append((dev, pin, arr))
        return dev

    def enqueue(self):
        """Enqueue the follow-ups on stream 0, after the joined fine stage (inside capture)."""
        ctx, st = self.ctx, self.graph.streams[0]
        u32, ptr = cc._u32, cc._ptr
        spec = self.spec
        ctx._fill32(self.counts.dptr.value, 0, 1 + len(self.regions), st)
        ctx._fill32(self.flags.dptr.value, 0, 4, st)
        ctx._fill32(self.lcounts.dptr.value, 0, len(self.fu_list), st)
        njobs = len(self.jobs)
        ctx._launch(self.f_select, njobs, 256,
                    [self.t_d.dptr, self.t_j.dptr, self.t_dg.dptr, self.t_g.dptr,
                     self.items.dptr, self.counts.dptr, self.flags.dptr, u32(self.max_items),
                     self.t_rcap.dptr, ctypes.c_float(float(spec.threshold)),
                     u32(spec.dedupe), u32(njobs)], stream=st)
        tot = self.max_items * self.bpi
        ctx._launch(self.f_blocks, (tot + 255) // 256, 256,
                    [self.items.dptr, self.counts.dptr, self.t_j.dptr, self.t_g.dptr,
                     self.starts.dptr, self.lists.dptr, self.lcounts.dptr, self.t_lcap.dptr,
                     self.flags.dptr, u32(self.max_items), u32(self.bpi), u32(spec.half),
                     self.t_rbase.dptr, self.t_lbase.dptr], stream=st)
        # Forward every region's rows from its allocation (rows past the region's count read
        # stale but valid offsets; nothing reads their spectra).
        for n, aid, sbuf, rb, rows in self.spec_bufs:
            whole = self.allocs[aid]
            fn, wg = ctx.pipeline(n, "seriesForward")
            ctx._launch(fn, rows, wg, [ptr(whole.ctypes.data), ptr(self.starts.dptr.value + 4 * rb),
                                       sbuf.dptr, u32(whole.size)], stream=st)
        lbase = self.lbase
        bs = int(spec.binsize)
        shift = cc._shift(bs)
        grid_cap = ctx.sm_count * 4
        for i, fu in enumerate(self.fu_list):
            n = fu["n"]
            fn, wg = self.items_fn[n]
            sbuf = self.spec_bufs[fu["region"]][2]
            cap = int(spec.max_items_per_region) * self.bpi
            grid = min(cap, grid_cap)
            ctx._launch(fn, grid, wg,
                        [sbuf.dptr, ptr(fu["fp"]._gtmpl.ctypes.data), self.idx.dptr, self.val.dptr,
                         ptr(self.lists.dptr.value + 20 * int(lbase[i])),
                         ptr(self.lcounts.dptr.value + 4 * i),
                         u32(fu["fp"].ntemplates), u32(bs), cc._i32(shift), u32(self.nbins),
                         u32(0), u32(grid)], stream=st)
        # Read back: flags, counts, items, peaks (one copy each, with the rest of the segment).
        h = self.host.ptr
        off = 0
        ctx._copy_d2h(h, self.flags.dptr.value, 16, st, "readback"); off += 16
        nc = 4 * (1 + len(self.regions))
        ctx._copy_d2h(h + off, self.counts.dptr.value, nc, st, "readback"); off += nc
        ni = self.max_items * IT * 4
        ctx._copy_d2h(h + off, self.items.dptr.value, ni, st, "readback"); off += ni
        ctx._copy_d2h(h + off, self.idx.dptr.value, 4 * self.nslot, st, "readback")
        ctx._copy_d2h(h + off + 4 * self.nslot, self.val.dptr.value, 8 * self.nslot, st, "readback")

    def read(self):
        """[(source job, rank, c0, template index, FilterResults)] in (job, rank) order, or None
        when a capacity overflowed (the caller then runs the follow-ups on the host)."""
        hp, nr = self.host, len(self.regions)
        if hp.view(np.uint32, 1)[0]:
            return None
        nitems = int(hp.view(np.uint32, 1, offset=16)[0])
        if nitems > self.max_items:
            return None
        off = 16 + 4 * (1 + nr)
        items = hp.view(np.uint32, nitems * IT, offset=off).reshape(nitems, IT).copy()
        off += self.max_items * IT * 4
        idx_all = hp.view(np.int32, self.nslot, offset=off)
        val_all = hp.view(np.complex64, self.nslot, offset=off + 4 * self.nslot)
        from ._gpuhost import read_followup_items
        return read_followup_items(items, idx_all, val_all, self.nbins, self.bpi,
                                   [fu["g"] for fu in self.fu_list], self.spec,
                                   [ji[2] for ji in self.jinfo])


def _u64(v):
    v = int(v)
    return np.array([v & 0xFFFFFFFF, (v >> 32) & 0xFFFFFFFF], np.uint32)
