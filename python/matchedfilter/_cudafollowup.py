"""Device follow-ups on CUDA: the executor for _gpuhost.followup_layout's groups.

The host path runs each selected follow-up as a single-template filter_series call: per
template group a forward of the windows' blocks and one peaks_items submission (a launch per
item), each with its own host bookkeeping. Here a batch is one upload of every group's tables,
per group a forward of its rows from its series allocation and one refineItems launch over its
entry list, and one readback -- enqueued on one stream with no wait until collected.
"""
import numpy as np

from . import _cudacompute as cc
from ._errors import UnsupportedSize
from ._shared import shared_buffer
from ._gpuhost import FollowupUnsupported as Unsupported, assemble_followups, followup_layout


class Executor:
    """Device follow-ups for one CUDA device: device and pinned buffers grown to the largest
    batch, reused by every batch after it."""

    def __init__(self):
        self.rec = {}
        self.pending = None              # the collector of the batch in flight, if any
        self.items_fn = {}

    def _items(self, ctx, n):
        fn = self.items_fn.get(n)
        if fn is None:
            f = cc._PTX_DIR / ("items_%d.ptx" % n)
            if f.is_file() and cc._static_shared(f) > cc._STATIC_SHARED_MAX:
                f = cc._PTX_DIR / ("items_%d_lds32.ptx" % n)
            if not f.is_file():
                raise Unsupported("no refineItems build for n=%d" % n)
            wg = n // cc._radix(n)
            fn = self.items_fn[n] = (ctx._load(f.stem, f, "refineItems", wg), wg)
        return fn

    def submit_jobs(self, jobs):
        """A collector giving the FilterResults of single-template follow-up jobs
        [(bank, series, kwargs)] as _items_batch gives them, enqueued without waiting;
        raises Unsupported when they cannot all run here."""
        groups, layout = followup_layout(jobs, cc.Context)
        if not groups:
            return lambda: []
        ctx = groups[0]["ctx"]
        for gw in groups:
            if gw["n"] > 65536:
                raise Unsupported("tier-C block length")
            gw["b_alloc"] = shared_buffer(gw["alloc"], ctx)
            gw["b_tmpl"] = shared_buffer(gw["plan"]._gtmpl, ctx)
            if gw["b_alloc"] is None or gw["b_tmpl"] is None:
                raise Unsupported("series or templates are not device allocations")
            try:
                gw["fwd"] = ctx.pipeline(gw["n"], "seriesForward")
            except UnsupportedSize as e:
                raise Unsupported(str(e))
            gw["items_fn"] = self._items(ctx, gw["n"])
        if self.pending is not None:
            self.pending()                       # its buffers are rewritten below
        ctx._bind()
        stream = ctx.get_stream(None)
        ctx._after_writes(stream)                # the series may be a middle output in flight
        # One table upload: per group its rows, its entries and its entry count; per group
        # the spectra and the peaks at offsets into shared buffers.
        tab, spec_off, out_off = 0, 0, 0
        for gw in groups:
            m = gw["rows"].size
            gw["t_rows"], gw["t_ent"], gw["t_cnt"] = tab, tab + 4 * m, tab + 24 * m
            tab += 24 * m + 16
            gw["spec"] = spec_off
            spec_off += m * gw["n"] * 8
            gw["out"] = out_off
            out_off += m * gw["nbins"]
        rec = self.rec
        for name, nbytes, cls in (("tables", tab, cc._Buffer), ("stage", tab, cc._Pinned),
                                  ("spec", spec_off, cc._Buffer), ("idx", out_off * 4, cc._Buffer),
                                  ("val", out_off * 8, cc._Buffer),
                                  ("host", out_off * 12, cc._Pinned)):
            # Powers of two: a steady search's batches vary by a few rows, and should reuse
            # the buffers rather than grow them by a few rows at a time.
            ctx._grow(rec, name, 1 << max(6, (int(nbytes) - 1).bit_length()), cls, stream)
        stage = rec["stage"]
        for gw in groups:
            m = gw["rows"].size
            stage.view(np.uint32, m, gw["t_rows"])[:] = gw["rows"]
            stage.view(np.uint32, 5 * m, gw["t_ent"])[:] = gw["entries"].ravel()
            stage.view(np.uint32, 4, gw["t_cnt"])[:] = (m, 0, 0, 0)
        t0, s0 = rec["tables"].dptr.value, rec["spec"].dptr.value
        i0, v0 = rec["idx"].dptr.value, rec["val"].dptr.value
        ctx._copy_h2d(t0, stage.ptr, tab, stream, "upload")
        ptr, u32 = cc._ptr, cc._u32
        grid_cap = ctx.sm_count * 4
        for gw in groups:
            m = gw["rows"].size
            if not m:
                continue
            fn, wg = gw["fwd"]
            ctx._launch(fn, m, wg, [gw["b_alloc"].dptr, ptr(t0 + gw["t_rows"]),
                                    ptr(s0 + gw["spec"]), u32(gw["alloc"].size), u32(0)],
                        stream=stream)
            fn, wg = gw["items_fn"]
            grid = min(m, grid_cap)
            bs = gw["bs"]
            ctx._launch(fn, grid, wg,
                        [ptr(s0 + gw["spec"]), gw["b_tmpl"].dptr, ptr(i0 + 4 * gw["out"]),
                         ptr(v0 + 8 * gw["out"]), ptr(t0 + gw["t_ent"]), ptr(t0 + gw["t_cnt"]),
                         u32(gw["plan"]._gtmpl.shape[0]), u32(bs), cc._i32(cc._shift(bs)),
                         u32(gw["nbins"]), u32(0), u32(grid)], stream=stream)
        host = rec["host"]
        if out_off:
            ctx._copy_d2h(host.ptr, i0, out_off * 4, stream, "readback")
            ctx._copy_d2h(host.ptr + out_off * 4, v0, out_off * 8, stream, "readback")
        done = []

        def read(gw):
            m, nbins = gw["rows"].size, gw["nbins"]
            idx = host.view(np.int32, m * nbins, 4 * gw["out"]).reshape(m, nbins)
            val = host.view(np.complex64, m * nbins, out_off * 4 + 8 * gw["out"])
            return idx, val.reshape(m, nbins)

        def collect():
            """Wait for the batch and assemble every job's results (once)."""
            if not done:
                try:
                    ctx._sync(stream)
                finally:
                    if self.pending is collect:
                        self.pending = None
                # FilterResults index into the pinned buffer: copy before the next batch.
                done.append(assemble_followups(layout, lambda gw: tuple(
                    np.array(a) for a in read(gw))))
            return done[0]
        self.pending = collect
        return collect


def executor(ctx):
    """The device's follow-up executor, held by the device state (one per device: every
    single-template plan of a bank is its own Context)."""
    ds = ctx._device_state if ctx._device_state is not None else ctx
    ex = getattr(ds, "_followups", None)
    if ex is None:
        ex = ds._followups = Executor()
    return ex
