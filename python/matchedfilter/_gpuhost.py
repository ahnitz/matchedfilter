"""Backend-neutral host logic shared by the Vulkan, CUDA and Metal GPU backends.

Everything here is pure Python/NumPy over plain integers and arrays: what to dispatch and
how results are laid out, never how. Each backend keeps its own submission mechanism
(command buffers and fences, streams and graphs, Metal command buffers) and calls these
helpers for the parts that must agree across backends. See docs/cross-platform-review.md
section 3.1 for the layer this is growing into.
"""

import numpy as np

from ._errors import UnsupportedSize

#: Most bins one peak kernel dispatch reduces into (the kernels' compiled limit).
MAX_BINS = 2048


def bin_shift(binsize):
    """log2(binsize) when binsize is a power of two, else -1 (the kernels divide)."""
    binsize = int(binsize)
    return binsize.bit_length() - 1 if binsize & (binsize - 1) == 0 else -1


def coarse_span(n, band, lo, hi):
    """A gate tier's window in band samples, (start, end, span, shift): the caller's window
    [lo, hi) at n, widened by one band sample at each end (as hmf.c), so a signal near either
    end has coarse samples on both sides.
    The tier reduces it to ONE bin, so the reported peak is the window's maximum -- all a
    gate needs. shift is bin_shift(span) (-1 when span is not a power of two)."""
    r = n // band
    cstart = lo // r
    cend = min(band, (hi + r - 1) // r + 1)
    if cstart > 0:
        cstart -= 1
    cend = max(cstart + 1, cend)
    cspan = max(1, cend - cstart)
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


def band_windows(rowwin, n, band):
    """Per-row windows [lo, hi) in samples of an n-point transform, mapped onto a coarse band
    as coarse_span maps one window: band samples [lo // R - 1, ceil(hi / R) + 1) with R = n // band,
    clamped to the band, at least one sample. The coarse and listed tiers read these as they
    are. Mapped in the kernel instead, the same arithmetic made the band-256 coarse kernel
    1.47x slower at SIMD16 on an Iris Xe. Memoised per table (grouped_row_windows' tables
    are memoised and read-only), as a call per segment maps the same few."""
    import numpy as np
    key = (id(rowwin), n, band)
    hit = _BAND_WINDOWS.get(key)
    if hit is not None and hit[0] is rowwin:
        return hit[1]
    rr = n // band
    w = np.asarray(rowwin, np.uint32).reshape(-1, 3)[:, :2].astype(np.int64)
    cs = w[:, 0] // rr
    ce = np.minimum(band, (w[:, 1] + rr - 1) // rr + 1)
    cs = np.where(cs > 0, cs - 1, cs)
    ce = np.maximum(cs + 1, ce)
    # A coarse tier is one bin: its rows' bin phase is 0.
    out = np.ascontiguousarray(np.stack([cs, ce, np.zeros_like(cs)], 1).astype(np.uint32))
    if len(_BAND_WINDOWS) > 4096:
        _BAND_WINDOWS.clear()
    _BAND_WINDOWS[key] = (rowwin, out)
    return out


def hier_peaks_grouped(ctx, n, band, data, tmpl, ct0, raw_thr, groups, binsize, threshold, *,
                       upload_tmpl=True, cascade_band=None, ct1=None, raw_thr1=None,
                       slot=None, async_submit=False, sparse=False, nbins=None, max_bins=MAX_BINS,
                       handle_out=None, refine_reach=None, phase=None):
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
    return ctx.hier_peaks(n, band, data, tmpl, ct0, raw_thr, binsize=int(binsize),
                          threshold=threshold, window=window, upload_data=False, nbins=nb,
                          upload_tmpl=upload_tmpl, cascade_band=cascade_band, ct1=ct1,
                          raw_thr1=raw_thr1, slot=slot, async_submit=async_submit,
                          sparse=sparse, row_windows=(groups, win), refine_reach=refine_reach,
                          **({} if handle_out is None else {"handle_out": handle_out}))


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


def followup_layout(jobs, ctx, max_rows=None):
    """(groups, layout) for single-template follow-up jobs [(bank, series, kwargs)], each a
    filter_series(series, windows=, binsize=, threshold=0, template_index=) call.

    groups: one dict per work group with plan, n, bs, alloc (the series allocation, as
    complex64), code and nser (the forward's sample layout and length in its units:
    seriesSample), rows (uint32 block starts in those units), entries ((rows, 5) uint32) and
    nbins (the widest window's bin count, rounded up to a power of two so few shapes occur).
    A real series is read in place: contiguous floats, or one lane of a complex row.
    layout: per job (group, starts, window starts, window ends, first entry, template group,
    local template, global template). Raises FollowupUnsupported when a job is not such a
    call, is not on ctx's device, has a series that is not device memory, has a block
    reading past its series (the host path pads with zeros), or a group passes max_rows."""
    from ._shared import _same_device, containing, containing_samples
    from ._windows import _normalize_windows, _window_bin_phases, _window_layout
    groups = {}
    layout = []
    for (bank, ser, kw) in jobs:
        kw = kw or {}
        ti = kw.get("template_index")
        if ti is None or kw.get("threshold") is None or float(kw["threshold"]) != 0.0 \
                or set(kw) - {"windows", "binsize", "threshold", "template_index"}:
            raise FollowupUnsupported("not a threshold-0 single-template call")
        g, tl = bank._template_map[ti]
        bs = int(kw["binsize"]) if kw.get("binsize") is not None else (bank.binsize or g.n)
        if bs >= g.n:
            raise FollowupUnsupported("binsize spans a block")
        S = len(ser)
        W = _normalize_windows(kw["windows"], S)
        st, ws, we = _window_layout(g, W, S)
        # The window's bins (filter_series): each block's bins numbered from its window's grid.
        ph = _window_bin_phases(W, st, ws, bs)
        ph = np.zeros(st.size, np.uint32) if ph is None else ph
        plan = g.get_flat_plan()
        pctx = getattr(plan, "_gpu", None)
        if pctx is None or not _same_device(pctx, ctx) or plan._gtmpl is None:
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
        # One group per (template group, binsize, series allocation and layout): a group
        # searching two detectors' allocations is two groups, not one per combination.
        gw = groups.setdefault((id(plan), bs, id(alloc), code), dict(
            plan=plan, n=g.n, bs=bs, alloc=alloc, code=code, nser=nser, rows=[], entries=[],
            nent=0))
        # The job's blocks as arrays (one row and one entry per block): a segment's
        # follow-ups are ~1000 blocks.
        k = int(st.size)
        first = gw["nent"]
        if max_rows is not None and first + k > max_rows:
            raise FollowupUnsupported("too many rows")
        gw["rows"].append(np.asarray(st, np.int64) + base)
        ent = np.empty((k, 6), np.int64)               # refineItems' six words
        ent[:, 0] = first + np.arange(k)
        ent[:, 1] = tl
        ent[:, 2] = np.minimum(np.asarray(ws, np.int64), g.n)
        ent[:, 3] = np.minimum(np.asarray(we, np.int64), g.n)
        ent[:, 4] = ent[:, 0]
        ent[:, 5] = ph
        gw["entries"].append(ent)
        gw["nent"] = first + k
        layout.append((gw, st, ws, we, first, g, tl, ti, W, ph))
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
    return out, layout


def assemble_followups(layout, read):
    """Each job's FilterResults from a device run of followup_layout's groups, ordered as
    TimeDomainFilterBank._items_batch orders them. read(group) gives the group's (idx, val),
    each (entries, nbins), read once per group."""
    from ._results import FilterResults
    from ._windows import _merge_window_bins
    reads = {}
    out = []
    for gw, st, ws, we, first, g, tl, ti, W, ph in layout:
        r = reads.get(id(gw))
        if r is None:
            r = reads[id(gw)] = read(gw)
        k = int(st.size)
        idx = r[0][first:first + k]
        val = r[1][first:first + k]
        bs, nbins = gw["bs"], gw["nbins"]
        counts = ((we.astype(np.int64) - ws.astype(np.int64) + ph.astype(np.int64) + bs - 1)
                  // bs)
        hit = (idx >= 0) & (np.arange(nbins)[None, :] < counts[:, None])
        res = window_results(hit, counts, st, idx, val, ti, g.n, by_count=not ph.any())
        if ph.any():
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
        g, _ = bank._template_map[(kw or {}).get("template_index")]
        ctx = getattr(g.get_flat_plan(), "_gpu", None)
        if ctx is None:
            return None
        return ctx.submit_followups(jobs)
    except (FollowupUnsupported, KeyError, TypeError):
        return None
