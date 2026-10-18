"""A hierarchical search: a tree of filters run over transformed input blocks.

See docs/hierarchical-search-design.md. The caller describes the hierarchy (a root
filter, inner FIR filters below it, searched leaf banks below those), hands over its
input blocks per channel and, through hooks, sees each node's series while it is held
in memory. The library chooses how the work is laid out.

Phase 1 of the design: one chunk per input block, each block filtered on its own (its
valid span padded by the filters' reach, as a caller filtering block by block would),
the root on the host.
"""
from typing import Callable, Dict, List, NamedTuple, Optional
import time

import numpy as np

from . import _core
from .time_domain import TimeDomainFilterBank, FilterResults, _EMPTY_FILTER_RESULTS

__all__ = ["Root", "Inner", "Leaf", "BlockInput", "HierarchicalSearch", "SeriesContext",
           "PeaksContext", "ChunkContext"]


class Leaf:
    """A searched bank of FIR templates filtering its parent's output.

    taps: (T, max_taps) float32 or complex64 rows, counts: taps per row (centre tap
    counts[t] // 2 at lag 0, as TimeDomainFilterBank). lags: per-template sample offset
    subtracted from a peak's sample before the threshold envelope is evaluated there
    (default 0). node_id: the caller's name for the group, handed back to hooks."""

    def __init__(self, taps, counts, lags=None, node_id=None):
        self.taps = taps
        self.counts = np.asarray(counts, dtype=np.int64)
        self.lags = (np.zeros(len(self.counts), dtype=np.int64) if lags is None
                     else np.asarray(lags, dtype=np.int64))
        if self.lags.shape != self.counts.shape:
            raise ValueError("lags must give one offset per template")
        self.node_id = node_id


class Inner:
    """An FIR filter on its parent's output whose own output its children filter.

    taps: 1D taps (count of them used; centre tap count // 2 at lag 0)."""

    def __init__(self, taps, count=None, children=(), node_id=None):
        self.taps = np.asarray(taps)
        if self.taps.ndim != 1:
            raise ValueError("an inner filter's taps are one row")
        self.count = int(len(self.taps) if count is None else count)
        if not (1 <= self.count <= len(self.taps)):
            raise ValueError("inner filter count (%d) must be in [1, %d]"
                             % (self.count, len(self.taps)))
        self.children = list(children)
        self.node_id = node_id


class Root:
    """The root filter: a one-sided spectrum on the input blocks' frequency grid.

    Its output for an input block D is the real series scale * C2R(conj(spectrum) D) over
    bins [band[0], band[1]) (twice the real part of the analytic series), scale given per
    block by the caller. profile: (w, delta_f), the expected signal power spectrum the leaf
    banks' gates are calibrated with (TimeDomainFilterBank.set_reference)."""

    def __init__(self, spectrum, band, children=(), profile=None, node_id=None):
        self.spectrum = np.ascontiguousarray(spectrum, dtype=np.complex64)
        self.band = (int(band[0]), int(band[1]))
        self.children = list(children)
        self.profile = profile
        self.node_id = node_id


class BlockInput:
    """One channel's input: transformed blocks of a common length n.

    spectra: one-sided spectra (n/2 + 1 bins, complex64), one per block. valid: per block,
    the (start, stop) samples of its output that are searched (pycbc: a segment's analyse
    range). tags: opaque per-block objects handed back to hooks. root_scale(root, block)
    gives the root output's scale for a block."""

    def __init__(self, spectra, valid, root_scale, tags=None):
        self.spectra = list(spectra)
        self.valid = [(int(a), int(b)) for a, b in valid]
        if len(self.valid) != len(self.spectra):
            raise ValueError("one valid span per block")
        self.tags = list(tags) if tags is not None else [None] * len(self.spectra)
        if len(self.tags) != len(self.spectra):
            raise ValueError("one tag per block")
        self.root_scale = root_scale


class ChunkContext(NamedTuple):
    chunk: int
    channels: List[str]
    tags: Dict[str, object]


class SeriesContext(NamedTuple):
    """A node's output for one chunk, for every active channel."""
    node: object
    chunk: int
    channels: List[str]
    tags: Dict[str, object]
    series: Dict[str, np.ndarray]


def _normalize_windows(windows, length):
    if windows is None:
        return [(0, length)]
    if isinstance(windows, slice):
        start, stop, _ = windows.indices(length)
        return [(start, stop)] if stop > start else []
    out = []
    for w in windows:
        if isinstance(w, slice):
            a, b, _ = w.indices(length)
        else:
            a, b = int(w[0]), int(w[1])
        if b > a:
            out.append((a, b))
    return out


def _spans_cover(support, requested):
    for a, b in requested:
        if b <= a:
            continue
        if not any(sa <= a and b <= sb for sa, sb in support):
            return False
    return True


class PeaksContext:
    """A leaf group's peaks for one chunk, with read access to its ancestors' series."""

    def __init__(self, search, root, leaf, chunk, channels, tags, peaks, held, scales,
                 support=None):
        self.root, self.leaf, self.chunk = root, leaf, chunk
        self.channels, self.tags, self.peaks = channels, tags, peaks
        self._search, self._held, self._scales = search, held, scales
        self._support = support or {}

    def envelope(self, channel):
        """The threshold envelope's values at channel's peaks (aligned with them), as the
        search evaluated them -- e(sample - lag) -- or None without an envelope."""
        return self._scales.get(channel)

    def support(self, channel, node=None):
        """The computed (start, stop) intervals for node (default: this leaf's parent) in
        channel for this chunk."""
        node = self._search._parent[id(self.leaf)] if node is None else node
        chan_sup = self._support.get(channel)
        if chan_sup is not None and id(node) in chan_sup:
            return list(chan_sup[id(node)])
        ser = self._held[channel][id(node)]
        return [(0, len(ser))]

    def series(self, channel, node=None, span=None):
        """The output of node (default: this leaf's parent) in channel, for this chunk.
        Note: returns a callback-scoped view; copy if retaining past the hook. If span=(start,
        stop) is given, verifies that interval lies within the node's computed support."""
        node = self._search._parent[id(self.leaf)] if node is None else node
        ser = self._held[channel][id(node)]
        if span is not None:
            req = _clip([(int(span[0]), int(span[1]))], 0, len(ser))
            sup = self.support(channel, node)
            if not _spans_cover(sup, req):
                raise ValueError("requested series span %r in channel %r lies outside "
                                 "computed support %r" % (span, channel, sup))
        return ser

    def refilter(self, channel, windows, binsize, threshold, template_index=None):
        """This leaf bank over its parent's series in channel, in other windows, bin size
        and threshold. No envelope applies. Raises ValueError if windows fall outside the
        parent series' computed support in channel."""
        ser = self.series(channel)
        req = _clip(_normalize_windows(windows, len(ser)), 0, len(ser))
        if not req and windows is not None:
            return _EMPTY_FILTER_RESULTS
        sup = self.support(channel)
        if not _spans_cover(sup, req):
            raise ValueError("refilter windows %r in channel %r lie outside computed "
                             "series support %r" % (windows, channel, sup))
        bank = self._search.leaf_bank(self.root, self.leaf)
        return bank.filter_series(ser, windows=windows, binsize=binsize,
                                  threshold=threshold, template_index=template_index)


def _merge(spans):
    out = []
    for a, b in sorted(spans):
        if b <= a:
            continue
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def _clip(spans, lo, hi):
    return [(max(lo, a), min(hi, b)) for a, b in spans if min(hi, b) > max(lo, a)]


class _InnerBatch:
    """The inner children of one node, filtered over the node's output.

    Real taps on a real series run as packed pairs: two filters as one complex filter
    h_a - i h_b, each placed so its own centre tap is the pair's centre, whose output is
    out_a + i out_b. Neighbours in tap count are paired. Other combinations run one row
    per child (complex output). The rows are a correlation bank (TimeDomainFilterBank,
    engine 'corr'), which chooses their block sizes.

    Rows are written into a channel's slots, reused across chunks. A slot reads as fresh:
    the correlation over the spans it was computed for and exact zero elsewhere. Each slot
    remembers those spans, and the bank clears only there (out_support), not the whole
    row every chunk."""

    def __init__(self, children, length, real_input):
        self.children = children
        self.length = int(length)
        counts = np.array([c.count for c in children], dtype=np.int64)
        order = np.argsort(counts)               # the pairing pycbc's middle stage used
        cplx = any(np.iscomplexobj(c.taps) for c in children)
        self.packed = bool(real_input) and not cplx
        self.real_input = bool(real_input)
        width = int(counts.max())
        if self.packed:
            npair = (len(children) + 1) // 2
            pc = np.array([int(max(counts[order[2 * q:2 * q + 2]])) for q in range(npair)],
                          dtype=np.int64)
            taps = np.zeros((npair, int(pc.max())), dtype=np.complex64)
            for r, ci in enumerate(order):
                q, lane = divmod(r, 2)
                c_i = int(counts[ci])
                o = int(pc[q]) // 2 - c_i // 2
                taps[q, o:o + c_i] += (1.0 if lane == 0 else -1j) * children[ci].taps[:c_i]
            rows_counts = pc
        else:
            dt = np.complex64 if cplx else np.float32
            taps = np.zeros((len(children), width), dtype=dt)
            for r, ci in enumerate(order):
                taps[r, :counts[ci]] = children[ci].taps[:counts[ci]]
            rows_counts = counts[order]
        self.n_rows = len(rows_counts)
        # child position -> (row, lane: 0 real part, 1 imaginary part, None the whole row)
        self.row_of = {}
        for r, ci in enumerate(order):
            self.row_of[int(ci)] = divmod(r, 2) if self.packed else (r, None)
        self.bank = TimeDomainFilterBank(taps, rows_counts, engine="corr")
        for g in self.bank._groups:
            g.get_correlation_plan()
        # An output depends on input within its filter's tap reach (centre tap to either end).
        self.tap_reach = int(rows_counts.max()) // 2
        self._chan = {}                          # channel -> slots, series and regions

    def prepare(self, channel, series, regions):
        """channel's series and the merged (start, stop) spans its rows must hold this chunk."""
        if len(series) != self.length:
            raise ValueError("an inner batch's input length changed between chunks")
        state = self._chan.setdefault(channel, {"slots": None, "support": []})
        state["series"] = np.ascontiguousarray(
            series, dtype=np.float32 if self.real_input else np.complex64)
        state["regions"] = regions

    def compute(self, channel, rows):
        """Rows (ascending) into channel's first len(rows) slots. Returns row -> slot."""
        state = self._chan[channel]
        k = len(rows)
        if state["slots"] is None or state["slots"].shape[0] < k:
            state["slots"] = np.zeros((k, self.length), dtype=np.complex64)
            state["support"] = [[] for _ in range(k)]      # where each slot may be nonzero
        support = state["support"]
        self.bank.correlate_series(state["series"], windows=state["regions"], templates=rows,
                                   out=state["slots"][:k],
                                   out_support=_merge([w for j in range(k) for w in support[j]]))
        for j in range(k):
            support[j] = state["regions"]
        return {r: j for j, r in enumerate(rows)}

    def view(self, channel, slot, pos):
        """Child pos's series in the slot its row was computed into."""
        row = self._chan[channel]["slots"][slot]
        lane = self.row_of[pos][1]
        if lane is None:
            return row
        return row.real if lane == 0 else row.imag


class _Step(NamedTuple):
    """What one chunk of one root's walk carries."""
    root: object
    chunk: int
    active: list
    tags: dict
    held: dict          # channel -> node id -> series
    support: dict       # channel -> node id -> list of computed (start, stop) spans
    need: dict          # (leaf id, channel) -> spans its parent's series must hold
    win: dict           # (leaf id, channel) -> searched windows
    envelopes: dict
    pads: dict          # leaf id -> samples its parent's series holds past its windows
    live: set
    on_peaks: Optional[Callable]


class HierarchicalSearch:
    """Run a forest of hierarchies over input blocks, delivering peaks through hooks.

    threshold: the leaf search threshold T. envelope_floor: the least value any threshold
    envelope returned by a hook may take (default 1: envelopes only raise the threshold);
    leaf banks are calibrated at T * envelope_floor, so no envelope can need a peak their
    gates dismissed. leaf_options: keyword arguments for each leaf's TimeDomainFilterBank
    (engine, false_dismissal, binsize, coarse_band_hz, first_stage_snr, device,
    fft_lengths, tap_sample_rate, data_sample_rate). context: samples beyond a leaf's
    windows over which hooks may read or refilter its parent's series. min_pad: minimum
    guard samples any leaf's parent series holds past its windows (e.g. for chisq blocks)."""

    _MIN_ENVELOPE_FLOOR = 1e-3

    def __init__(self, roots, threshold, envelope_floor=1.0, leaf_options=None, context=0,
                 min_pad=0):
        self.roots = list(roots)
        self.threshold = float(threshold)
        if not (np.isfinite(self.threshold) and self.threshold >= 0.0):
            raise ValueError("threshold must be finite and non-negative")
        self.envelope_floor = float(envelope_floor)
        if not (np.isfinite(self.envelope_floor) and self.envelope_floor >= self._MIN_ENVELOPE_FLOOR):
            raise ValueError("envelope_floor (%g) must be finite and >= %g"
                             % (self.envelope_floor, self._MIN_ENVELOPE_FLOOR))
        self.leaf_options = dict(leaf_options or {})
        if "threshold" in self.leaf_options:
            raise ValueError("the leaf threshold is the search's (threshold, envelope_floor), "
                             "not a leaf option")
        self.context = int(context)
        if self.context < 0:
            raise ValueError("context must be non-negative")
        self.min_pad = int(min_pad)
        if self.min_pad < 0:
            raise ValueError("min_pad must be non-negative")
        self.timings = dict(root=0.0, inner=0.0, leaf=0.0, hooks=0.0, setup=0.0)
        self._parent = {}
        self._kids = {}                  # node -> (inner children, leaf children)
        self._leaf_banks = {}
        self._inner = {}
        self._root_plans = {}
        for root in self.roots:
            if not isinstance(root, Root):
                raise TypeError("roots must be Root nodes")
            self._index(root)

    def _index(self, node):
        if id(node) in self._kids:
            raise ValueError("a node appears more than once in the hierarchy")
        self._kids[id(node)] = None
        inner, leaves = [], []
        for child in node.children:
            if id(child) in self._parent or id(child) in self._kids:
                raise ValueError("a child node is shared across multiple parents or forms a cycle")
            self._parent[id(child)] = node
            if isinstance(child, Inner):
                inner.append(child)
                self._index(child)
            elif isinstance(child, Leaf):
                leaves.append(child)
            else:
                raise TypeError("children are Inner or Leaf nodes")
        self._kids[id(node)] = (inner, leaves)

    def leaf_bank(self, root, leaf):
        """The TimeDomainFilterBank that searches leaf, below root (built on first use, with
        root's profile as its reference)."""
        bank = self._leaf_banks.get(id(leaf))
        if bank is None:
            t0 = time.perf_counter()
            opts = dict(self.leaf_options)
            opts["threshold"] = self.threshold * self.envelope_floor
            bank = self._leaf_banks[id(leaf)] = TimeDomainFilterBank(
                leaf.taps, leaf.counts, **opts)
            if root.profile is not None:
                # the first reference settles the bank's block sizes and calibrates its gates
                w, df = root.profile
                bank.set_reference(w, delta_f=df)
            self.timings["setup"] += time.perf_counter() - t0
        return bank

    def _leaves_below(self, node):
        inner, leaves = self._kids[id(node)]
        yield from leaves
        for c in inner:
            yield from self._leaves_below(c)

    def pad(self, root):
        """The most samples any leaf's parent series holds past the leaf's windows below root:
        the longest block any of root's leaf banks uses or may still choose (at least min_pad).
        Builds (and calibrates) every leaf bank below root."""
        return max([self.min_pad] + [int(self.leaf_bank(root, lf).max_block_length)
                                     for lf in self._leaves_below(root)])

    def _batches(self, node, length):
        """Build the inner batches of node's subtree for series of length samples (once)."""
        inner = self._kids[id(node)][0]
        if inner and id(node) not in self._inner:
            t0 = time.perf_counter()
            self._inner[id(node)] = _InnerBatch(inner, length, self._real_output(node))
            self.timings["setup"] += time.perf_counter() - t0
        for c in inner:
            self._batches(c, length)

    def _real_output(self, node):
        """Whether node's output series is real: the root's is, and an inner node's is when
        its input is and its taps are."""
        if isinstance(node, Root):
            return True
        return (not np.iscomplexobj(node.taps)) and self._real_output(self._parent[id(node)])

    def _root_plan(self, n):
        p = self._root_plans.get(n)
        if p is None:
            p = self._root_plans[n] = _core.Root(n)
        return p

    def run(self, inputs: Dict[str, BlockInput], windows: Optional[Callable] = None,
            on_series: Optional[Callable] = None, on_peaks: Optional[Callable] = None,
            on_chunk: Optional[Callable] = None):
        """Filter every input block through each root's hierarchy.

        windows(leaf, chunk, channel, extra): where leaf peaks are searched, widened by
        extra samples: None (the block's valid span), a list of (start, stop), or empty
        (the leaf is skipped in this chunk and channel). Windows are clipped to the valid
        span. on_series(SeriesContext) runs when a root's output for a chunk is ready (the
        root only: inner nodes' series are read through PeaksContext.series) and may return
        {channel: envelope}: envelope(samples) -> threshold scale at those
        samples (>= envelope_floor), applied to every leaf below the root. on_peaks
        (PeaksContext) runs per leaf per chunk; on_chunk(ChunkContext) after a chunk."""
        channels = list(inputs)
        nchunks = max(len(inputs[c].spectra) for c in channels) if channels else 0
        for root in self.roots:
            leaves = list(self._leaves_below(root))
            pads = {id(lf): max(self.min_pad, int(self.leaf_bank(root, lf).max_block_length))
                    for lf in leaves}
            for k in range(nchunks):
                active = [c for c in channels if k < len(inputs[c].spectra)]
                if not active:
                    continue
                tags = {c: inputs[c].tags[k] for c in active}
                # leaf windows (searched) and the spans their parents must hold
                win, need = {}, {}
                for c in active:
                    v0, v1 = inputs[c].valid[k]
                    for lf in leaves:
                        w = windows(lf, k, c, 0) if windows is not None else None
                        w = [(v0, v1)] if w is None else _clip(_merge(w), v0, v1)
                        win[(id(lf), c)] = w
                        if w:
                            wx = windows(lf, k, c, self.context) if windows is not None else None
                            wx = [(v0, v1)] if wx is None else _clip(_merge(wx), v0, v1)
                            need[(id(lf), c)] = wx
                if not any(win.values()):
                    continue
                held = {c: {} for c in active}
                support = {c: {} for c in active}
                t0 = time.perf_counter()
                for c in active:
                    spec = inputs[c].spectra[k]
                    n = 2 * (len(spec) - 1)
                    out = np.empty(n, dtype=np.float32)
                    k0, k1 = root.band
                    self._root_plan(n).real(np.ascontiguousarray(spec, dtype=np.complex64),
                                            root.spectrum, k0, k1,
                                            float(inputs[c].root_scale(root, k)), out)
                    held[c][id(root)] = out
                    support[c][id(root)] = [(0, n)]
                self.timings["root"] += time.perf_counter() - t0
                self._batches(root, len(out))
                envelopes = {}
                if on_series is not None:
                    t0 = time.perf_counter()
                    envelopes = on_series(SeriesContext(
                        root, k, active, tags, {c: held[c][id(root)] for c in active})) or {}
                    self.timings["hooks"] += time.perf_counter() - t0
                # A node any channel needs in this chunk is produced in every channel (where
                # a channel's own windows are empty, its series is zero), so a hook can read
                # it in another channel.
                live = set()
                for lf in leaves:
                    if any(win[(id(lf), c)] for c in active):
                        node = self._parent[id(lf)]
                        while node is not root:
                            live.add(id(node))
                            node = self._parent[id(node)]
                step = _Step(root, k, active, tags, held, support, need, win, envelopes, pads,
                             live, on_peaks)
                self._walk(root, step)
                if on_chunk is not None:
                    on_chunk(ChunkContext(k, active, tags))

    def _walk(self, node, step):
        """Search node's leaves, then produce its live inner children (every channel) and
        walk each."""
        inner, leaves = self._kids[id(node)]
        for lf in leaves:
            self._search_leaf(lf, step)
        if not inner:
            return
        held = step.held
        L = len(held[step.active[0]][id(node)])
        batch = self._inner[id(node)]
        wanted = [pos for pos, ch in enumerate(batch.children) if id(ch) in step.live]
        if not wanted:
            return
        t0 = time.perf_counter()
        rows = sorted({batch.row_of[pos][0] for pos in wanted})
        slot_of = {}
        regions_by_chan = {}
        for c in step.active:
            spans = []
            for pos in wanted:
                self._span(batch.children[pos], c, step.need, step.pads, spans)
            regions = _clip(_merge(spans), 0, L)
            regions_by_chan[c] = regions
            batch.prepare(c, held[c][id(node)], regions)
            slot_of[c] = batch.compute(c, rows)
        members = sorted(wanted, key=lambda p: batch.row_of[p])
        for pos in members:
            child = batch.children[pos]
            for c in step.active:
                held[c][id(child)] = batch.view(c, slot_of[c][batch.row_of[pos][0]], pos)
                step.support[c][id(child)] = regions_by_chan[c]
        self.timings["inner"] += time.perf_counter() - t0
        for pos in members:
            self._walk(batch.children[pos], step)
        for pos in members:
            for c in step.active:
                del held[c][id(batch.children[pos])]
                step.support[c].pop(id(batch.children[pos]), None)

    def _search_leaf(self, lf, step):
        """lf's peak search in every channel of the step, and its on_peaks."""
        if not any(step.win[(id(lf), c)] for c in step.active):
            return
        peaks, scales = {}, {}
        t0 = time.perf_counter()
        for c in step.active:
            w = step.win[(id(lf), c)]
            envelope = step.envelopes.get(c)
            if not w:
                peaks[c] = _EMPTY_FILTER_RESULTS
                if envelope is not None:
                    scales[c] = np.empty(0, dtype=np.float64)
                continue
            series = step.held[c][id(self._parent[id(lf)])]
            # one window as a slice: filter_series memoises a slice's layout
            res = self.leaf_bank(step.root, lf).filter_series(
                series, windows=slice(*w[0]) if len(w) == 1 else w)
            peaks[c], e = self._apply_envelope(res, lf, envelope, len(series))
            if e is not None:
                scales[c] = e
        self.timings["leaf"] += time.perf_counter() - t0
        if step.on_peaks is not None:
            t0 = time.perf_counter()
            step.on_peaks(PeaksContext(self, step.root, lf, step.chunk, step.active, step.tags,
                                       peaks, step.held, scales, step.support))
            self.timings["hooks"] += time.perf_counter() - t0

    def _span(self, node, channel, need, pads, out):
        """Append to out where node's output must be valid in channel: each leaf's windows
        (with context) padded by that leaf bank's longest block, and its inner children's
        spans padded by the tap reach of the batch that filters them. Unmerged."""
        inner, leaves = self._kids[id(node)]
        for c in leaves:
            pad = pads[id(c)]
            for a, b in need.get((id(c), channel), ()):
                out.append((a - pad, b + pad))
        if inner:
            batch = self._inner[id(node)]
            sub = []
            for c in inner:
                self._span(c, channel, need, pads, sub)
            out.extend((a - batch.tap_reach, b + batch.tap_reach) for a, b in sub)

    def _apply_envelope(self, res, leaf, envelope, length):
        """Keep the peaks at or above T * envelope(sample - lag). Returns the kept peaks and
        the envelope's values at them (None without an envelope)."""
        if envelope is None:
            return res, None
        if res.snr.size == 0:
            return res, np.empty(0, dtype=np.float64)
        t = np.clip(res.sample_indices - leaf.lags[res.template_indices], 0, length - 1)
        e = np.asarray(envelope(t), dtype=np.float64)
        if e.shape != t.shape:
            raise ValueError("threshold envelope returned shape %s for %s samples"
                             % (e.shape, t.shape))
        if not np.isfinite(e).all():
            raise ValueError("threshold envelope returned non-finite values")
        if e.min() < self.envelope_floor * (1 - 1e-6):
            raise ValueError("a threshold envelope fell below envelope_floor (%g < %g)"
                             % (e.min(), self.envelope_floor))
        keep = np.abs(res.snr) >= self.threshold * e
        if keep.all():
            return res, e
        return FilterResults(*(f[keep] for f in res)), e[keep]
