"""Backend-neutral host logic shared by the Vulkan, CUDA and Metal GPU backends.

Everything here is pure Python/NumPy over plain integers and arrays: what to dispatch and
how results are laid out, never how. Each backend keeps its own submission mechanism
(command buffers and fences, streams and graphs, Metal command buffers) and calls these
helpers for the parts that must agree across backends. See docs/cross-platform-review.md
section 3.1 for the layer this is growing into.
"""

from collections import OrderedDict
import numpy as np

from ._errors import UnsupportedSize

#: Most bins one peak kernel dispatch reduces into (the kernels' compiled limit).
MAX_BINS = 2048


def bin_shift(binsize):
    """log2(binsize) when binsize is a power of two, else -1 (the kernels divide)."""
    binsize = int(binsize)
    return binsize.bit_length() - 1 if binsize & (binsize - 1) == 0 else -1


def coarse_span(n, band, lo, hi, lag_pad=0):
    """A gate tier's window in band samples, (start, end, span, shift): the caller's window
    [lo, hi) at n, widened by one band sample (plus lag_pad when clustered) at each end (as
    hmf.c), so a signal near either end has coarse samples on both sides.
    The tier reduces it to ONE bin, so the reported peak is the window's maximum -- all a
    gate needs. shift is bin_shift(span) (-1 when span is not a power of two)."""
    from ._windows import coarse_lags
    lp = int(lag_pad)
    if lp > 0:
        r = n // band
        lo_i, hi_i = int(lo), int(hi)
        if lo_i < lp * r or hi_i + lp * r > n:
            cstart, cend = 0, band
        else:
            pad = 1 + lp
            c0 = lo_i // r
            cstart = c0 - pad if c0 > pad else 0
            cend = max(cstart + 1, min(band, -(-hi_i // r) + pad))
    else:
        cstart, cend = coarse_lags(n, band, lo, hi)
    cspan = cend - cstart
    return cstart, cend, cspan, bin_shift(cspan)


def plan_items(items, binsize, align_words=1, max_bins=MAX_BINS, phase=None):
    """Output layout of a peaks_items submission.

    items are (lo, hi, a, b, t): rows a:b against template t over [lo, hi). Each item's
    (b - a, nbins) results start at a multiple of align_words 4-byte words -- a backend
    that selects them by descriptor offset passes its storage-offset alignment, one that
    uses pointers passes 1. phase: the rows' bin phases (or None), which count toward an
    item's bins (the most any of its rows needs). Returns (offsets, nbins per item, total
    words)."""
    offs, nbs, size = [], [], 0
    for lo, hi, a, b, t in items:
        top = 0 if phase is None or b <= a else int(np.max(phase[a:b]))
        nb = -(-(hi - lo + top) // binsize)
        if nb > max_bins:
            raise UnsupportedSize("an item's window exceeds the kernel bin limit")
        offs.append(size)
        nbs.append(nb)
        size += -(-((b - a) * nb) // align_words) * align_words
    return offs, nbs, size


def split_items(items, offs, nbs, indices, values, copy=False):
    """Per item (idx, val) shaped (b - a, 1, nbins) from the flat readback of plan_items.
    copy=True when the flat arrays are a reused host buffer."""
    out = []
    for (lo, hi, a, b, t), off, nb in zip(items, offs, nbs):
        c = (b - a) * nb
        i = indices[off:off + c].reshape(b - a, 1, nb)
        v = values[off:off + c].reshape(b - a, 1, nb)
        out.append((i.copy(), v.copy()) if copy else (i, v))
    return out


# ---- hierarchical calls: the argument contract every backend's hier_peaks shares ----------

def hier_tiers(n, band, ct0, raw_thr, cascade_band=None, ct1=None, raw_thr1=None):
    """Normalise a hier_peaks/hier_peaks_grouped chain to (band, ct0, raw_thr, cascade_band,
    ct1, raw_thr1) in the keyword convention.

    band/ct0/raw_thr may each be a (tier0, tier1) pair; a two-tier chain is then tier 0 =
    cascade_band with ct0/raw_thr and tier 1 = band with ct1/raw_thr1. An incomplete
    cascade raises: running one tier with another tier's threshold would be a different
    computation, not a slower one."""
    if isinstance(band, (tuple, list)):
        cascade_band, band = band[0], band[1]
    if isinstance(ct0, (tuple, list)):
        ct0, ct1 = ct0[0], ct0[1]
    if isinstance(raw_thr, (tuple, list)):
        raw_thr, raw_thr1 = raw_thr[0], raw_thr[1]
    if cascade_band is not None and (ct1 is None or raw_thr1 is None):
        raise ValueError("a two-tier cascade needs ct1 and raw_thr1")
    return band, ct0, raw_thr, cascade_band, ct1, raw_thr1


def hier_window(n, window, binsize):
    """(lo, hi, binsize, nbins) of a hierarchical call: the window clamped to [0, n],
    binsize defaulting to n (one bin)."""
    lo, hi = (0, n) if window is None else (int(window[0]), int(window[1]))
    lo, hi = max(0, min(lo, n)), max(0, min(hi, n))
    if lo >= hi:
        raise ValueError("empty window (%d, %d)" % (lo, hi))
    binsize = n if binsize is None else int(binsize)
    return lo, hi, binsize, -(-(hi - lo) // binsize)


def split_bins(call, lo, hi, binsize, max_bins, upload_data, upload_tmpl, sparse, async_submit):
    """A window wider than max_bins bins, as consecutive sub-windows of max_bins bins.

    call(window, upload_data, upload_tmpl) returns one sub-window's dense (idx, val); inputs
    upload with the first only. The result honours sparse and async_submit exactly as one
    call would (a collector when async_submit)."""
    from ._shared import sparsified
    span = max_bins * binsize
    pi, pv = [], []
    for a in range(lo, hi, span):
        i2, v2 = call((a, min(a + span, hi)), upload_data, upload_tmpl)
        pi.append(i2)
        pv.append(v2)
        upload_data = upload_tmpl = False             # already on the device
    import numpy as np
    res = sparsified((np.concatenate(pi, axis=2), np.concatenate(pv, axis=2)), sparse)
    return (lambda: res) if async_submit else res


def grouped_windows(groups, n, nd, binsize, max_bins=MAX_BINS, nbins=None, phase=None):
    """Validated (lo, hi, a, b) groups of a grouped call, as ints, and their common bin count
    (the first group's, or nbins if larger; no group may need more). phase: the rows' bin
    phases ([nd], or None), which count toward a row's bins (ap_bin_count)."""
    groups = tuple((int(lo), int(hi), int(a), int(b)) for lo, hi, a, b in groups)
    binsize = int(binsize)
    top = (lambda a, b: 0) if phase is None else (lambda a, b: int(np.max(phase[a:b])))
    need = lambda lo, hi, a, b: (hi - lo + top(a, b) + binsize - 1) // binsize
    nb = need(*groups[0])
    if nbins is not None:
        nb = max(nb, int(nbins))
    if nb > max_bins:
        raise ValueError("grouped dispatch exceeds the kernel bin limit")
    for lo, hi, a, b in groups:
        if not (0 <= lo < hi <= n) or not (0 <= a < b <= nd):
            raise ValueError("invalid group (%d, %d, %d, %d)" % (lo, hi, a, b))
        if need(lo, hi, a, b) > nb:
            raise ValueError("grouped windows must not exceed the first group's bin count")
    return groups, nb


_ROW_WINDOWS = {}


def grouped_row_windows(groups, n, nd, binsize, max_bins=MAX_BINS, nbins=None, phase=None):
    """The per-row form of a grouped call, for a backend whose hier_peaks takes row_windows:
    (groups, nb, win, (lo0, hi0)).

    win is uint32 [lo, hi, bin phase] per data row (tierb.slang ROWWIN_WORDS), phase the
    rows' bin phases ([nd], or None for 0: run_series' bin_phase); (lo0, hi0) is the
    recording's window, nb bins from the first group's start (clipped to n), which the
    per-row windows narrow on the device. A series call repeats the same few group layouts,
    so results are memoised (win is read-only)."""
    key = (tuple(tuple(g) for g in groups), n, nd, int(binsize), max_bins, nbins,
           None if phase is None else bytes(memoryview(np.ascontiguousarray(phase, np.uint32))))
    hit = _ROW_WINDOWS.get(key)
    if hit is not None:
        return hit
    groups, nb = grouped_windows(groups, n, nd, binsize, max_bins, nbins, phase)
    win = np.zeros(3 * nd, np.uint32)
    for lo, hi, a, b in groups:
        win[3 * a:3 * b:3] = lo
        win[3 * a + 1:3 * b:3] = hi
    if phase is not None:
        win[2::3] = np.asarray(phase, np.uint32)
    win.flags.writeable = False
    binsize = int(binsize)
    lo0 = groups[0][0]
    hi0 = min(n, lo0 + nb * binsize)
    if -(-(hi0 - lo0) // binsize) != nb:
        lo0, hi0 = max(0, n - nb * binsize), n
    if len(_ROW_WINDOWS) > 4096:
        _ROW_WINDOWS.clear()
    hit = _ROW_WINDOWS[key] = (groups, nb, win, (lo0, hi0))
    return hit


#: A window start that tells the coarse and refine kernels to read each data row's window from
#: their row-window table (tierb.slang ROWWIN_ON): CUDA and Metal, which have no
#: specialization constant for it.
ROWWIN_ON = 0xFFFFFFFF

_BAND_WINDOWS = {}


def band_windows(rowwin, n, band, lag_pad=0):
    """Per-row windows [lo, hi) in samples of an n-point transform, mapped onto a coarse band
    as coarse_span maps one window: band samples [lo // R - 1, ceil(hi / R) + 1) with R = n // band,
    widened by lag_pad when clustered (full [0, band) where cyclic wrap could clip a shifted
    member peak, matching hmf.c), clamped to the band, at least one sample. The coarse and
    listed tiers read these as they are. Mapped in the kernel instead, the same arithmetic
    made the band-256 coarse kernel 1.47x slower at SIMD16 on an Iris Xe. Memoised per table
    (grouped_row_windows' tables are memoised and read-only), as a call per segment maps the
    same few."""
    import numpy as np
    lp = int(lag_pad)
    key = (id(rowwin), n, band, lp) if lp else (id(rowwin), n, band)
    hit = _BAND_WINDOWS.get(key)
    if hit is not None and hit[0] is rowwin:
        return hit[1]
    from ._windows import coarse_lags
    w = np.asarray(rowwin, np.uint32).reshape(-1, 3)[:, :2].astype(np.int64)
    if lp > 0:
        r = n // band
        pad = 1 + lp
        lo, hi = w[:, 0], w[:, 1]
        c0 = lo // r
        cs = np.where(c0 > pad, c0 - pad, 0)
        ce = np.maximum(cs + 1, np.minimum(band, -(-hi // r) + pad))
        wrap = (lo < lp * r) | (hi + lp * r > n)
        cs = np.where(wrap, 0, cs)
        ce = np.where(wrap, band, ce)
    else:
        cs, ce = coarse_lags(n, band, w[:, 0], w[:, 1])
    # A coarse tier is one bin: its rows' bin phase is 0.
    out = np.ascontiguousarray(np.stack([cs, ce, np.zeros_like(cs)], 1).astype(np.uint32))
    if len(_BAND_WINDOWS) > 4096:
        _BAND_WINDOWS.clear()
    _BAND_WINDOWS[key] = (rowwin, out)
    return out


def hier_peaks_grouped(ctx, n, band, data, tmpl, ct0, raw_thr, groups, binsize, threshold,
                       upload_tmpl=True, cascade_band=None, ct1=None, raw_thr1=None,
                       slot=None, async_submit=False, sparse=False, nbins=None, max_bins=MAX_BINS,
                       handle_out=None, refine_reach=None, phase=None, band_offsets=None,
                       direct=None, tier0_cluster=None):
    """hier_peaks_grouped for any backend whose hier_peaks accepts row_windows: one
    recording, each tier a single dispatch over all rows, per-row windows in the kernels.

    groups holds (lo, hi, a, b): rows a..b of data searched over [lo, hi). Output bins
    follow the first group's bin count (or nbins). phase: the rows' bin phases (run_series'
    bin_phase), which the refine's row table carries."""
    from ._shared import shared_buffer
    if shared_buffer(data, ctx) is None:
        raise ValueError("grouped spectra must be GPU-shared (a forward batch)")
    groups, nb, win, window = grouped_row_windows(groups, n, data.shape[0], binsize,
                                                  max_bins, nbins, phase)
    extra = {} if handle_out is None else {"handle_out": handle_out}
    if band_offsets is not None:
        extra["band_offsets"] = band_offsets
    if tier0_cluster is not None:
        extra["tier0_cluster"] = tier0_cluster
    return ctx.hier_peaks(n, band, data, tmpl, ct0, raw_thr, binsize=int(binsize),
                          threshold=threshold, window=window, upload_data=False, nbins=nb,
                          upload_tmpl=upload_tmpl, cascade_band=cascade_band, ct1=ct1,
                          raw_thr1=raw_thr1, slot=slot, async_submit=async_submit,
                          sparse=sparse, row_windows=(groups, win), refine_reach=refine_reach,
                          direct=direct, **extra)


def window_results(hit, counts, starts, idx, val, template, n, by_count=True):
    """FilterResults of one follow-up window, as TimeDomainFilterBank._items_batch orders them:
    the (block, bin) pairs where ``hit`` holds, by the block's bin count, then block, then bin
    -- the order filter_series' one call per bin count gives -- or, by_count False (a window
    whose blocks carry bin phases: filter_series makes one call), by block, then bin.

    hit: (blocks, nbins) bool; counts: bins per block; starts: block start samples; idx/val:
    (blocks, nbins) peak lag and value; template: the global template index; n: block length.
    The one ordering rule every device follow-up path assembles with."""
    from ._results import FilterResults, _EMPTY_FILTER_RESULTS
    bi, bn = np.nonzero(hit)
    if not bi.size:
        return _EMPTY_FILTER_RESULTS
    if by_count:
        o = np.argsort(np.asarray(counts)[bi], kind="stable")
        bi, bn = bi[o], bn[o]
    st = np.asarray(starts, dtype=np.int64)[bi]
    return FilterResults(
        template_indices=np.full(bi.size, template, dtype=np.int64),
        sample_indices=st + np.asarray(idx)[bi, bn].astype(np.int64),
        snr=np.asarray(val)[bi, bn].astype(np.complex64),
        block_starts=st,
        block_lengths=np.full(bi.size, n, dtype=np.int64))


# ---- device follow-ups ---------------------------------------------------------------------
# A batch of threshold-0 single-template calls (a search's follow-ups) as listed entries
# for the refineItems kernel (src/gpu/refine_bounded.slang): per work group -- one
# (template group, binsize, series allocation) -- the rows to forward (block starts as offsets
# into the allocation) and one entry per row (row, local template, window start, window end,
# output slot). The host lays the blocks out with TimeDomainFilterBank._window_layout, so the
# windows are the host path's by construction, and assemble_followups orders the results as
# _items_batch does. The executor runs them (Executor.submit_followups): the forward of each
# group's rows, refineItems over its entries, and one wait.

class FollowupUnsupported(Exception):
    """Device follow-ups cannot take this batch; the caller runs it on the host."""


def _gpu_ctx_of(bank, g):
    """Return a GPU executor context on ``g``'s device without loading full bank spectra."""
    ctx = bank.__dict__.get("_followup_gpu_ctx")
    if ctx is not None:
        return ctx
    bank._groups
    plan = g._plan
    if plan is not None:
        return getattr(plan, "_gpu", None)
    from .device import parse as _parse_device
    if g.device is None or _parse_device(g.device).kind != "gpu":
        return None
    return getattr(g.get_single_plan(0), "_gpu", None)


def _followup_owner_ctx(bank, g):
    """Return the device's live follow-up GPU context or attach a fresh sibling to ``bank``."""
    pctx = _gpu_ctx_of(bank, g)
    if pctx is None:
        return None
    holder = getattr(pctx, "_device_state", None)
    if holder is not None:
        ref = holder.__dict__.get("followup_owner")
        owner = ref() if ref is not None else None
        if owner is not None:
            return owner
    ctx = bank.__dict__.get("_followup_gpu_ctx")
    if ctx is None:
        from .device import parse as _parse_device
        ctx = type(pctx)(_parse_device(g.device).index)
        bank._followup_gpu_ctx = ctx
    return ctx


def _followup_job_ok(bank, g, ser, bstarts):
    """Return True when ``(bank, g, ser, bstarts)`` is eligible for ``submit_followups``."""
    from ._shared import containing, containing_samples
    if not isinstance(ser, np.ndarray):
        return False
    if bstarts.size and int(bstarts.max()) + g.n > ser.size:
        return False
    ctx = _gpu_ctx_of(bank, g)
    if ctx is None:
        return False
    if ser.dtype == np.complex64:
        return containing(np.ascontiguousarray(ser), ctx) is not None
    if ser.dtype == np.float32:
        return containing_samples(ser, ctx) is not None
    return False


def followup_layout(jobs, ctx, max_rows=None):
    """(groups, layout) for single-template follow-up jobs [(bank, series, kwargs)], each a
    filter_series(series, windows=, binsize=, threshold=0, template_index=) call.

    groups: one dict per coalesced work group (n, bs, series allocation, layout code) with
    tstage (compact complex64 upload rows), n, bs, alloc, code, nser, rows, entries, and nbins.
    A real series is read in place: contiguous floats, or one lane of a complex row.
    layout: per job (group, starts, window starts, window ends, first entry, template group,
    local template, global template, windows, phases). Raises FollowupUnsupported when a job
    is not such a call, is not on ctx's device, has a series that is not device memory, has a
    block reading past its series (the host path pads with zeros), or a group passes max_rows."""
    from ._shared import _same_device, containing, containing_samples
    from ._windows import _normalize_windows, _window_bin_phases, _window_layout
    groups = {}
    cold_by_group = {}
    layout = []
    for (bank, ser, kw) in jobs:
        kw = kw or {}
        ti = kw.get("template_index")
        if ti is None or kw.get("threshold") is None or float(kw["threshold"]) != 0.0 \
                or set(kw) - {"windows", "binsize", "threshold", "template_index"}:
            raise FollowupUnsupported("not a threshold-0 single-template call")
        bank._groups
        if ti < 0 or ti >= bank.n_templates:
            raise FollowupUnsupported("template_index out of range")
        g, tl = bank._template_map[ti]
        aligned = kw.get("binsize") is not None or bank.binsize is not None
        bs = int(kw["binsize"]) if kw.get("binsize") is not None else (bank.binsize or g.n)
        if bs < 1:
            raise FollowupUnsupported("invalid binsize")
        S = len(ser)
        w_arg = kw.get("windows")
        if w_arg is None or (
            type(w_arg) is slice and (w_arg.step is None or w_arg.step == 1)
            and (w_arg.start is None or type(w_arg.start) is int)
            and (w_arg.stop is None or type(w_arg.stop) is int)
        ):
            v0, v1 = (0, S) if w_arg is None else w_arg.indices(S)[:2]
            if v1 <= v0:
                W = np.empty((0, 2), dtype=np.int64)
                st = ws = we = np.empty(0, dtype=np.int64)
                ph = np.zeros(0, dtype=np.uint32)
            else:
                W = np.array([[v0, v1]], dtype=np.int64)
                step = g.n_valid
                c_bad = g.c_bad
                fidx = max(0, (v0 - c_bad) // step)
                st = np.arange(fidx * step, min(S, v1 - c_bad), step, dtype=np.int64)
                if st.size:
                    bvt0 = st + c_bad
                    rs = np.maximum(v0, bvt0)
                    re = np.minimum(v1, bvt0 + step)
                    ws = rs - st
                    we = re - st
                    ph = (((rs - v0) % bs).astype(np.uint32)
                          if aligned else np.zeros(st.size, dtype=np.uint32))
                else:
                    ws = we = st
                    ph = np.zeros(0, dtype=np.uint32)
        else:
            W = _normalize_windows(w_arg, S)
            st, ws, we = _window_layout(g, W, S)
            # The window's bins (filter_series): each block's bins numbered from its window's grid.
            ph = _window_bin_phases(W, st, ws, bs) if aligned else None
            ph = np.zeros(st.size, np.uint32) if ph is None else ph
        pctx = _gpu_ctx_of(bank, g)
        if pctx is None or not _same_device(pctx, ctx):
            raise FollowupUnsupported("not a plan on this device")
        ser = np.asarray(ser)
        if ser.dtype == np.complex64:
            c = containing(np.ascontiguousarray(ser), ctx)
            if c is None:
                raise FollowupUnsupported("series not device-resident")
            alloc, base, code, nser = c[0], c[1], 0, c[0].size
        elif ser.dtype == np.float32:
            c = containing_samples(ser, ctx)
            if c is None:
                raise FollowupUnsupported("series not device-resident")
            alloc, foff, stride = c
            if stride == 1:                 # floats, by their index in the allocation
                base, code, nser = foff, 1, 2 * alloc.size
            else:                           # one lane of complex samples
                base, code, nser = foff >> 1, ((foff & 1) << 2) | 2, alloc.size
        else:
            raise FollowupUnsupported("series is neither complex64 nor float32")
        if st.size and int(st.max()) + g.n > ser.size:
            raise FollowupUnsupported("a block reads past the series")
        k = int(st.size)
        if k == 0:
            layout.append((None, st, ws, we, 0, g, tl, ti, W, ph))
            continue
        # Coalesce across leaf template groups sharing (n, binsize, series allocation, layout):
        # a two-detector segment becomes two groups instead of one per active leaf bank.
        gw = groups.setdefault((g.n, bs, id(alloc), code), dict(
            n=g.n, bs=bs, alloc=alloc, code=code, nser=nser, rows=[], entries=[],
            nent=0, tmap={}, trows=[]))
        first = gw["nent"]
        if max_rows is not None and first + k > max_rows:
            raise FollowupUnsupported("too many rows")
        tkey = (id(g), int(tl))
        tslot = gw["tmap"].get(tkey)
        if tslot is None:
            tslot = len(gw["trows"])
            gw["tmap"][tkey] = tslot
            hcache = g.__dict__.setdefault("_followup_host_spec", OrderedDict())
            tl_i = int(tl)
            sp = hcache.get(tl_i)
            if sp is not None:
                hcache.move_to_end(tl_i)
                gw["trows"].append(sp)
            else:
                gw["trows"].append(None)
                cold_g = cold_by_group.get(id(g))
                if cold_g is None:
                    cold_g = cold_by_group[id(g)] = (g, OrderedDict())
                cold_g[1].setdefault(tl_i, []).append((gw, tslot))
        gw["rows"].append(np.asarray(st, np.int64) + base)
        ent = np.empty((k, 6), np.int64)               # refineItems' six words
        ent[:, 0] = first + np.arange(k)
        ent[:, 1] = tslot
        ent[:, 2] = np.minimum(np.asarray(ws, np.int64), g.n)
        ent[:, 3] = np.minimum(np.asarray(we, np.int64), g.n)
        ent[:, 4] = ent[:, 0]
        ent[:, 5] = ph
        gw["entries"].append(ent)
        gw["nent"] = first + k
        layout.append((gw, st, ws, we, first, g, tl, ti, W, ph))

    # Batch-transform all uncached template spectra per group in one C SIMD pass.
    for g, tl_map in cold_by_group.values():
        tls = list(tl_map.keys())
        specs = np.ascontiguousarray(g.full_spectra(tls), dtype=np.complex64)
        hcache = g._followup_host_spec
        for row_k, tl_i in enumerate(tls):
            sp = specs[row_k]
            hcache[tl_i] = sp
            for gw_ref, slot_idx in tl_map[tl_i]:
                gw_ref["trows"][slot_idx] = sp
        while len(hcache) > 512:
            hcache.popitem(last=False)

    out = list(groups.values())
    for gw in out:
        e = (np.concatenate(gw["entries"]) if gw["entries"] else np.empty((0, 6), np.int64))
        gw["rows"] = (np.concatenate(gw["rows"]) if gw["rows"]
                      else np.empty(0, np.int64)).astype(np.uint32)
        gw["entries"] = e.astype(np.uint32)
        nbins = max(1, int(((e[:, 3] - e[:, 2] + e[:, 5] + gw["bs"] - 1) // gw["bs"]).max())
                    if e.size else 1)
        nbins = 1 << (nbins - 1).bit_length()
        if nbins > MAX_BINS:
            raise FollowupUnsupported("window has too many bins")
        gw["nbins"] = nbins
        trows = gw["trows"]
        gw["tstage"] = (np.ascontiguousarray(np.stack(trows, axis=0), dtype=np.complex64)
                        if trows else np.empty((0, gw["n"]), dtype=np.complex64))
    return out, layout


def assemble_followups(layout, read):
    """Each job's FilterResults from a device run of followup_layout's groups, ordered as
    TimeDomainFilterBank._items_batch orders them. read(group) gives the group's (idx, val),
    each (entries, nbins), read once per group."""
    from ._results import FilterResults
    from ._windows import _merge_window_bins
    reads = {}
    empty = None
    out = []
    for gw, st, ws, we, first, g, tl, ti, W, ph in layout:
        if gw is None:
            if empty is None:
                z64 = np.empty(0, dtype=np.int64)
                empty = FilterResults(z64, z64, np.empty(0, dtype=np.complex64), z64, z64)
            out.append(empty)
            continue
        r = reads.get(id(gw))
        if r is None:
            idx_g, val_g = read(gw)
            r = reads[id(gw)] = (idx_g, val_g, np.arange(gw["nbins"])[None, :])
        k = int(st.size)
        idx = r[0][first:first + k]
        val = r[1][first:first + k]
        bs = gw["bs"]
        has_ph = bool(ph.any())
        if has_ph:
            counts = ((np.asarray(we, np.int64) - np.asarray(ws, np.int64)
                       + ph.astype(np.int64) + bs - 1) // bs)
        else:
            counts = (np.asarray(we, np.int64) - np.asarray(ws, np.int64) + bs - 1) // bs
        hit = (idx >= 0) & (r[2] < counts[:, None])
        res = window_results(hit, counts, st, idx, val, ti, g.n, by_count=not has_ph)
        if has_ph:
            # A bin a block edge cut is two partial bins: one per window bin (filter_series).
            res = FilterResults(*_merge_window_bins(W, bs, *res))
        out.append(res)
    return out


def submit_followups(jobs):
    """A collector giving the FilterResults of single-template follow-up jobs, submitted on
    the jobs' device without waiting (Executor.submit_followups); or None (not a GPU, or a
    batch outside what the device path takes: the caller runs the jobs on the host)."""
    if not jobs:
        return lambda: []
    try:
        bank, _, kw = jobs[0]
        bank._groups
        kw = kw or {}
        ti = kw.get("template_index")
        if ti is None or ti < 0 or ti >= bank.n_templates:
            return None
        if kw.get("threshold") is None or float(kw["threshold"]) != 0.0:
            return None
        g, _ = bank._template_map[ti]
        ctx = _followup_owner_ctx(bank, g)
        if ctx is None:
            return None
        return ctx.submit_followups(jobs)
    except (FollowupUnsupported, KeyError, IndexError, TypeError):
        return None
