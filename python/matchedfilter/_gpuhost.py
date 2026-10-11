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


def plan_items(items, binsize, align_words=1, max_bins=MAX_BINS):
    """Output layout of a peaks_items submission.

    items are (lo, hi, a, b, t): rows a:b against template t over [lo, hi). Each item's
    (b - a, nbins) results start at a multiple of align_words 4-byte words -- a backend
    that selects them by descriptor offset passes its storage-offset alignment, one that
    uses pointers passes 1. Returns (offsets, nbins per item, total words)."""
    offs, nbs, size = [], [], 0
    for lo, hi, a, b, t in items:
        nb = -(-(hi - lo) // binsize)
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


def padded_rows(rows, nt, unit):
    """Data rows padded so rows * nt pairs fill whole coarse groups of `unit` pairs (pairs
    per group x templates per tile). Padding pairs land past the real ones and are never
    listed by the compaction."""
    while (rows * nt) % unit:
        rows += 1
    return rows


def grouped_windows(groups, n, nd, binsize, max_bins=MAX_BINS, nbins=None):
    """Validated (lo, hi, a, b) groups of a grouped call, as ints, and their common bin count
    (the first group's, or nbins if larger; no group may need more)."""
    groups = tuple((int(lo), int(hi), int(a), int(b)) for lo, hi, a, b in groups)
    binsize = int(binsize)
    nb = (groups[0][1] - groups[0][0] - 1) // binsize + 1
    if nbins is not None:
        nb = max(nb, int(nbins))
    if nb > max_bins:
        raise ValueError("grouped dispatch exceeds the kernel bin limit")
    for lo, hi, a, b in groups:
        if not (0 <= lo < hi <= n) or not (0 <= a < b <= nd):
            raise ValueError("invalid group (%d, %d, %d, %d)" % (lo, hi, a, b))
        if (hi - lo - 1) // binsize + 1 > nb:
            raise ValueError("grouped windows must not exceed the first group's bin count")
    return groups, nb


_ROW_WINDOWS = {}


def grouped_row_windows(groups, n, nd, binsize, max_bins=MAX_BINS, nbins=None):
    """The per-row form of a grouped call, for a backend whose hier_peaks takes row_windows:
    (groups, nb, win, (lo0, hi0)).

    win is uint32 [lo, hi] per data row; (lo0, hi0) is the recording's window, nb bins from
    the first group's start (clipped to n), which the per-row windows narrow on the device.
    A series call repeats the same few group layouts, so results are memoised (win is
    read-only)."""
    key = (tuple(tuple(g) for g in groups), n, nd, int(binsize), max_bins, nbins)
    hit = _ROW_WINDOWS.get(key)
    if hit is not None:
        return hit
    import numpy as np
    groups, nb = grouped_windows(groups, n, nd, binsize, max_bins, nbins)
    win = np.zeros(2 * nd, np.uint32)
    for lo, hi, a, b in groups:
        win[2 * a:2 * b:2] = lo
        win[2 * a + 1:2 * b:2] = hi
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


def hier_peaks_grouped(ctx, n, band, data, tmpl, ct0, raw_thr, groups, binsize, threshold, *,
                       upload_tmpl=True, cascade_band=None, ct1=None, raw_thr1=None,
                       slot=None, async_submit=False, sparse=False, nbins=None, max_bins=MAX_BINS,
                       handle_out=None):
    """hier_peaks_grouped for any backend whose hier_peaks accepts row_windows: one
    recording, each tier a single dispatch over all rows, per-row windows in the kernels.

    groups holds (lo, hi, a, b): rows a..b of data searched over [lo, hi). Output bins
    follow the first group's bin count (or nbins)."""
    from ._shared import shared_buffer
    if shared_buffer(data, ctx) is None:
        raise ValueError("grouped spectra must be GPU-shared (a forward batch)")
    groups, nb, win, window = grouped_row_windows(groups, n, data.shape[0], binsize,
                                                  max_bins, nbins)
    return ctx.hier_peaks(n, band, data, tmpl, ct0, raw_thr, binsize=int(binsize),
                          threshold=threshold, window=window, upload_data=False,
                          upload_tmpl=upload_tmpl, cascade_band=cascade_band, ct1=ct1,
                          raw_thr1=raw_thr1, slot=slot, async_submit=async_submit,
                          sparse=sparse, row_windows=(groups, win),
                          **({} if handle_out is None else {"handle_out": handle_out}))


# ---- device follow-up items (FollowupSpec), shared by the GPU backends -----------------------
class FollowupSpec:
    """A follow-up rule over a segment's fine results (pycbc's asymmetric follow-up).

    For each job j: its peaks with |snr| >= threshold, by |snr| descending (ties in result
    order), keeping the first in each interval of ``dedupe`` samples; each kept peak at
    sample c with template ti is followed up on the PARTNER job's series (pairs[j], same
    bank): filter_series(windows=slice(max(0, c - half), min(S, c + half)), binsize,
    threshold=0, template_index=ti).

    TimeDomainFilterBank.filter_series_many(jobs, followups=spec) and
    SegmentPlan.run(jobs, followup=spec) apply it: on the device where a backend can (the CUDA
    segment graph, _cudafollowup), else on the host (run_host). Both give
    [(source job, rank, c, ti, FilterResults)] in (job, rank) order, and a device selection
    must equal select() exactly: same candidates (|snr| = hypot(re, im) >= threshold), same
    order (|snr| descending, ties by FOLLOWUP_KEY_SHIFTS), same dedupe."""

    def __init__(self, pairs, threshold, dedupe, half, binsize, max_items=128,
                 max_items_per_region=48):
        self.pairs = [int(p) for p in pairs]
        self.threshold, self.dedupe = float(threshold), int(dedupe)
        self.half, self.binsize = int(half), int(binsize)
        self.max_items, self.max_items_per_region = int(max_items), int(max_items_per_region)

    def key(self):
        return (tuple(self.pairs), self.threshold, self.dedupe, self.half, self.binsize)

    def select(self, jobs, fine_out):
        """[(j, rank, c, ti, follow-up job)] by the rule, from host results."""
        sel = []
        for j, r in enumerate(fine_out):
            a = np.abs(r.snr)
            keep = np.flatnonzero(a >= self.threshold)
            keep = keep[np.argsort(-a[keep], kind="stable")]
            used = set()
            bank = jobs[j][0]
            partner = jobs[self.pairs[j]][1]
            S = len(partner)
            for rank, i in enumerate(keep):
                sec = int(r.sample_indices[i] // self.dedupe)
                if sec in used:
                    continue
                used.add(sec)
                c0 = int(r.sample_indices[i])
                ti = int(r.template_indices[i])
                sel.append((j, rank, c0, ti, (bank, partner, dict(
                    windows=slice(max(0, c0 - self.half), min(S, c0 + self.half)),
                    binsize=self.binsize, threshold=0.0, template_index=ti))))
        return sel

    def run_host(self, jobs, fine_out):
        sel = self.select(jobs, fine_out)
        from .time_domain import TimeDomainFilterBank
        res = TimeDomainFilterBank.filter_series_many([s[4] for s in sel])
        return [(j, rank, c0, ti, r) for (j, rank, c0, ti, _), r in zip(sel, res)]


#: The device follow-up item record: FOLLOWUP_ITEM_WORDS uint32 words, in this order.
#: c0 and the global template index are 64-bit (lo, hi). "rank" is the peak's position in the
#: source job's candidates ordered by |snr| descending, ties by FOLLOWUP_KEY (result order).
FOLLOWUP_ITEM_FIELDS = ("job", "rank", "c0_lo", "c0_hi", "ti_lo", "ti_hi", "t_local", "group",
                        "slot", "nblocks")
FOLLOWUP_ITEM_WORDS = len(FOLLOWUP_ITEM_FIELDS)
#: The tie key a device selection ranks equal |snr| by (= FilterResults order of the job):
#: entry (the job's sub-call) << 56 | caller block << 32 | local template << 16 | bin.
FOLLOWUP_KEY_SHIFTS = dict(entry=56, row=32, template=16, bin=0)
#: The logical per-dispatch descriptor a backend encodes into its own binding: the source job,
#: its sub-call entry, (templates, bins) of the call, the dispatch's first layout row and row
#: count, the layout-row -> caller-block map, the block start samples, the global templates.
FOLLOWUP_DISPATCH_FIELDS = ("job", "entry", "nt", "nb", "b0", "rows", "row_caller",
                            "row_sample", "template_global")


def read_followup_items(items, idx_all, val_all, nbins, bpi, groups, spec, series_len):
    """Host assembly of device follow-ups: [(job, rank, c0, ti, FilterResults)] in (job, rank)
    order, or None when the device and host block layouts disagree (the caller then runs the
    follow-ups on the host).

    items: (k, FOLLOWUP_ITEM_WORDS) uint32 records; idx_all/val_all: the per-slot peaks, slot
    (item index * bpi + block) holding nbins bins; groups[item.group]: the bank template group;
    series_len[j]: the length of job j's series. Assembled exactly as
    TimeDomainFilterBank._items_batch does for the same calls."""
    from .time_domain import TimeDomainFilterBank, _consume_into, _results_from
    out = []
    order = np.lexsort((items[:, 1], items[:, 0]))
    bs = int(spec.binsize)
    for it in order:
        o = items[it]
        j, rank = int(o[0]), int(o[1])
        c0 = int(o[2]) | (int(o[3]) << 32)
        ti = int(o[4]) | (int(o[5]) << 32)
        g = groups[int(o[7])]
        S = int(series_len[int(spec.pairs[j])])
        W = np.array([[max(0, c0 - int(spec.half)), min(S, c0 + int(spec.half))]], np.int64)
        st, ws, we = TimeDomainFilterBank._window_layout(g, W, S)
        m = int(st.size)
        if m != int(o[9]) or m > bpi:
            return None
        base = int(it) * bpi * nbins
        idx = np.asarray(idx_all[base:base + m * nbins]).reshape(m, 1, nbins).astype(np.int64)
        val = np.array(val_all[base:base + m * nbins]).reshape(m, 1, nbins)
        counts = ((we - ws + bs - 1) // bs).astype(np.int64)
        lists = ([], [], [], [], [])
        stt = st.astype(np.int64)
        for u in np.unique(counts):
            mk = counts == u
            _consume_into(lists, idx[mk][:, :, :u], val[mk][:, :, :u], stt[mk], g,
                          (int(o[6]), 1), g.n, ti)
        out.append((j, rank, c0, ti, _results_from(lists)))
    return out
