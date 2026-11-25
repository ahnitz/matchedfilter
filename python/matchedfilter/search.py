"""A hierarchical search: a tree of filters run over transformed input blocks.

See docs/hierarchical-search-design.md. The caller describes the hierarchy (a root
filter, inner FIR filters below it, searched leaf banks below those), hands over its
input blocks per channel and, through hooks, sees each node's series while it is held
in memory. The library chooses how the work is laid out.

Phase 1 of the design: one chunk per input block, each block filtered on its own (its
valid span padded by the filters' reach, as a caller filtering block by block would).
On a GPU search the root runs on the device or the host, as measured (_gpuroot).
"""
from typing import Callable, Dict, List, NamedTuple, Optional
import time

import numpy as np

from . import _core, _gpuroot
from ._errors import UnsupportedSize
from .time_domain import (TimeDomainFilterBank, FilterResults, _EMPTY_FILTER_RESULTS,
                          _aligned_zeros, _normalize_windows, _page_aligned_empty,
                          _settle_device_writes)
from .device import parse as _parse_device

__all__ = ["Root", "Inner", "Leaf", "BlockInput", "HierarchicalSearch", "SeriesContext",
           "PeaksContext", "ChunkContext"]


class Leaf:
    """A searched bank of FIR templates filtering its parent's output.

    Parameters
    ----------
    taps : ndarray
        (T, max_taps) float32 or complex64 rows. Row t's centre tap, ``counts[t] // 2``, is
        at lag 0, as :class:`TimeDomainFilterBank` takes them.
    counts : array_like of int
        Taps used per row.
    lags : array_like of int, optional
        Per template, a sample offset subtracted from a peak's sample before the threshold
        envelope is evaluated there. Default None: 0.
    node_id : object, optional
        The caller's name for the group, handed back to hooks.

    Raises
    ------
    ValueError
        If ``lags`` does not give one offset per template.
    """

    def __init__(self, taps, counts, lags=None, node_id=None):
        self.taps = taps
        self.counts = np.asarray(counts, dtype=np.int64)
        self.lags = (np.zeros(len(self.counts), dtype=np.int64) if lags is None
                     else np.asarray(lags, dtype=np.int64))
        if self.lags.shape != self.counts.shape:
            raise ValueError("lags must give one offset per template")
        self.node_id = node_id


class Inner:
    """An FIR filter on its parent's output, whose own output its children filter.

    Parameters
    ----------
    taps : ndarray
        1-D taps. The centre tap, ``count // 2``, is at lag 0.
    count : int, optional
        Taps used. Default None: all of them.
    children : sequence, optional
        The nodes that filter this one's output: :class:`Inner` or :class:`Leaf`.
    node_id : object, optional
        The caller's name for the node, handed back to hooks.

    Raises
    ------
    ValueError
        If ``taps`` is not one row or ``count`` is not in [1, len(taps)].
    """

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

    Its output for an input block D is the real series ``scale * C2R(conj(spectrum) D)``
    over bins [band[0], band[1]) (twice the real part of the analytic series), with the
    scale given per block by the caller (:class:`BlockInput`).

    Parameters
    ----------
    spectrum : ndarray
        The one-sided spectrum, complex64.
    band : tuple of int
        ``(first, stop)`` bins the root filters.
    children : sequence, optional
        The nodes that filter the root's output: :class:`Inner` or :class:`Leaf`.
    profile : tuple or dict, optional
        ``(w, delta_f)``, the expected signal power spectrum the leaf banks' gates are
        calibrated with (:meth:`TimeDomainFilterBank.set_reference`), or a dict
        ``{channel: (w, delta_f)}`` where the channels' noise spectra differ (two
        detectors). Each leaf bank then holds a calibration for every channel's profile over
        one copy of its templates (on a GPU: a bank for each profile). A channel the dict
        does not name takes the first profile.
    node_id : object, optional
        The caller's name for the root, handed back to hooks.
    """

    def __init__(self, spectrum, band, children=(), profile=None, node_id=None):
        self.spectrum = np.ascontiguousarray(spectrum, dtype=np.complex64)
        self.band = (int(band[0]), int(band[1]))
        self.children = list(children)
        self.profile = profile
        self.node_id = node_id


class BlockInput:
    """One channel's input: transformed blocks of a common length n.

    Parameters
    ----------
    spectra : sequence of ndarray
        One one-sided spectrum per block (n/2 + 1 bins, complex64), read, never written. A
        GPU search keeps a device copy of each block's array for as long as the array object
        lives, so that searches over the same blocks (one per root, as PyCBC builds them)
        upload each block once; it checks the array's contents before each use (one read of
        the array) and uploads it again where a caller rewrote it in place.
    valid : sequence of tuple of int
        Per block, the (start, stop) samples of its output that are searched (pycbc: a
        segment's analysis range).
    root_scale : callable
        ``root_scale(root, block)`` gives the root output's scale for a block.
    tags : sequence, optional
        Opaque per-block objects handed back to hooks.

    Raises
    ------
    ValueError
        If ``valid`` or ``tags`` does not give one entry per block.
    """

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
    """What an ``on_chunk`` hook is given after a chunk.

    Attributes
    ----------
    chunk : int
        The chunk's number.
    channels : list of str
        The channels active in the chunk.
    tags : dict
        Per channel, the chunk's tag from :class:`BlockInput`.
    """
    chunk: int
    channels: List[str]
    tags: Dict[str, object]


class SeriesContext(NamedTuple):
    """A node's output for one chunk, for every active channel, as ``on_series`` is given it.

    Attributes
    ----------
    node : Root
        The node.
    chunk : int
        The chunk's number.
    channels : list of str
        The channels active in the chunk.
    tags : dict
        Per channel, the chunk's tag.
    series : dict
        Per channel, the node's output series.
    """
    node: object
    chunk: int
    channels: List[str]
    tags: Dict[str, object]
    series: Dict[str, np.ndarray]


def _spans_cover(support, requested):
    for a, b in requested:
        if b <= a:
            continue
        if not any(sa <= a and b <= sb for sa, sb in support):
            return False
    return True


class PeaksContext:
    """A leaf's peaks for one chunk, with read access to its ancestors' series.

    An ``on_peaks`` hook is given one per leaf per chunk. Its attributes ``root``,
    ``leaf``, ``chunk``, ``channels`` and ``tags`` say where it is, and ``peaks`` holds per
    channel the leaf's :class:`FilterResults` above the threshold envelope.
    """

    def __init__(self, search, root, leaf, chunk, channels, tags, peaks, held, scales,
                 support=None):
        self.root, self.leaf, self.chunk = root, leaf, chunk
        self.channels, self.tags, self.peaks = channels, tags, peaks
        self._search, self._held, self._scales = search, held, scales
        self._support = support or {}
        # The search's inner rows are settled at the first read: nothing writes them again
        # while the chunk's hooks run.
        self._settled = False

    def envelope(self, channel):
        """The threshold envelope's values at a channel's peaks.

        Parameters
        ----------
        channel : str
            The channel.

        Returns
        -------
        ndarray or None
            Aligned with ``peaks[channel]``: the envelope as the search evaluated it,
            ``e(sample - lag)``. None without an envelope.
        """
        return self._scales.get(channel)

    def support(self, channel, node=None):
        """The intervals of a node's output that were computed in a channel for this chunk.

        Parameters
        ----------
        channel : str
            The channel.
        node : Root or Inner, optional
            The node. Default None: this leaf's parent.

        Returns
        -------
        list of tuple of int
            (start, stop) intervals in the node's series.
        """
        node = self._search._parent[id(self.leaf)] if node is None else node
        chan_sup = self._support.get(channel)
        if chan_sup is not None and id(node) in chan_sup:
            return list(chan_sup[id(node)])
        ser = self._held[channel][id(node)]
        return [(0, len(ser))]

    def series(self, channel, node=None, span=None):
        """The output of a node in a channel, for this chunk.

        Parameters
        ----------
        channel : str
            The channel.
        node : Root or Inner, optional
            The node. Default None: this leaf's parent.
        span : tuple of int, optional
            ``(start, stop)`` the caller will read; checked to lie within the computed support.

        Returns
        -------
        ndarray
            A view valid only during the hook; copy it to keep it.

        Raises
        ------
        ValueError
            If ``span`` lies outside the node's computed support.
        """
        search = self._search
        node = search._parent[id(self.leaf)] if node is None else node
        if not self._settled:
            search._settle()
            self._settled = True
        ser = self._held[channel][id(node)]
        if span is not None:
            req = _clip([(int(span[0]), int(span[1]))], 0, len(ser))
            sup = self.support(channel, node)
            if not _spans_cover(sup, req):
                raise ValueError("requested series span %r in channel %r lies outside "
                                 "computed support %r" % (span, channel, sup))
        return ser

    def refilter(self, channel, windows, binsize, threshold, template_index=None):
        """Filter this leaf's parent series again, in other windows, bin size and threshold.

        No envelope applies.

        Parameters
        ----------
        channel : str
            The channel.
        windows : optional
            Windows in the forms :meth:`TimeDomainFilterBank.filter_series` takes.
        binsize : int
            Samples per peak bin.
        threshold : float
            SNR threshold.
        template_index : int, optional
            Filter only this template. Default None: every template of the leaf.

        Returns
        -------
        FilterResults
            The peaks, as :meth:`TimeDomainFilterBank.filter_series` returns them.

        Raises
        ------
        ValueError
            If the windows fall outside the parent series' computed support.
        """
        ser = self.series(channel)
        # The bank's parser (time_domain._normalize_windows): the windows filter_series takes,
        # parsed as it parses them, so the support check and the call cannot disagree. A
        # lone slice with integer bounds (a search's follow-up) is what the parser makes of
        # it: its clipped span, if not empty.
        if (type(windows) is slice and (windows.step is None or windows.step == 1)
                and (windows.start is None or type(windows.start) is int)
                and (windows.stop is None or type(windows.stop) is int)):
            a, b, _ = windows.indices(len(ser))
            req = [(a, b)] if b > a else []
        else:
            req = [(int(a), int(b)) for a, b in _normalize_windows(windows, len(ser))]
        if not req and windows is not None:
            return _EMPTY_FILTER_RESULTS
        sup = self.support(channel)
        if not _spans_cover(sup, req):
            raise ValueError("refilter windows %r in channel %r lie outside computed "
                             "series support %r" % (windows, channel, sup))
        search = self._search
        bank = search.leaf_bank(self.root, self.leaf, channel)
        return bank.filter_series(ser, windows=windows, binsize=binsize,
                                  threshold=threshold, template_index=template_index,
                                  profile=search._call_profile(self.root, channel))


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
    row every chunk.

    device: the device the rows are correlated on and stored in -- on a GPU search the
    leaves', so a leaf reads its parent's row (or its lane of a packed row) where the
    correlation wrote it, with no host round trip."""

    def __init__(self, children, length, real_input, device=None):
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
        self.bank = TimeDomainFilterBank(taps, rows_counts, engine="corr", device=device)
        for g in self.bank._groups:
            g.get_correlation_plan()
        # An output depends on input within its filter's tap reach (centre tap to either end).
        self.tap_reach = int(rows_counts.max()) // 2
        self._chan = {}                          # channel -> slots, series and regions
        self.in_flight = False                   # rows written on the device, not yet waited for
        self._alloc = self.bank.empty_shared if device is not None else None

    def prepare(self, channel, series, regions):
        """channel's series and the merged (start, stop) spans its rows must hold this chunk."""
        if len(series) != self.length:
            raise ValueError("an inner batch's input length changed between chunks")
        state = self._chan.setdefault(channel, {"slots": None, "support": []})
        dt = np.float32 if self.real_input else np.complex64
        # On a device a parent's row -- or its lane of a packed row (stride 2) -- is read
        # where it is; a host copy waits for the device's writes to it first.
        lane = (self._alloc is not None and isinstance(series, np.ndarray) and series.dtype == dt
                and series.ndim == 1 and series.strides in ((series.itemsize,), (8,)))
        if not lane:
            _settle_device_writes()
            series = np.ascontiguousarray(series, dtype=dt)
        state["series"] = series
        state["regions"] = regions

    def compute(self, channel, rows):
        """Rows (ascending) into channel's first len(rows) slots. Returns row -> slot."""
        return self.compute_channels([channel], rows)[channel]

    def compute_channels(self, channels, rows):
        """Rows (ascending) into each channel's first len(rows) slots, every channel in one
        bank call (TimeDomainFilterBank.correlate_series_channels: on a device, one
        submission per block-size group for all of them). Returns channel -> row -> slot."""
        for channel in channels:
            self._slots(channel, len(rows))
        # On a device the rows are left in flight: the leaves' forwards are ordered after them
        # on the GPU, and a host reader settles them first (HierarchicalSearch._settle).
        on_device = self._alloc is not None
        k = len(rows)
        sel = None if k == self.n_rows else rows
        states = [self._chan[c] for c in channels]
        supports = [_merge([w for j in range(k) for w in st["support"][j]]) for st in states]
        self.bank.correlate_series_channels(
            [st["series"] for st in states], [st["regions"] for st in states],
            [st["slots"][:k] for st in states], supports, templates=sel, wait=not on_device)
        self.in_flight = self.in_flight or on_device
        for st in states:
            for j in range(k):
                st["support"][j] = st["regions"]
        return {c: {r: j for j, r in enumerate(rows)} for c in channels}

    def _slots(self, channel, k):
        """Make channel's slots hold at least k rows."""
        state = self._chan[channel]
        if state["slots"] is None or state["slots"].shape[0] < k:
            if self._alloc is None:
                state["slots"] = _aligned_zeros((k, self.length), dtype=np.complex64)
                state["support"] = [[] for _ in range(k)]  # where each slot may be nonzero
            else:
                # Device rows may hold anything (a recycled allocation): every sample is
                # support, so the bank clears what its windows do not write on the device.
                # A host fill of the rows wrote ~80 MB of device-visible memory per channel
                # for each search, 0.67 s of a pycbc job's 64 top templates.
                state["slots"] = self._alloc((k, self.length))
                state["support"] = [[(0, self.length)] for _ in range(k)]

    def prepare_job(self, channel, rows):
        """Prepare channel's first len(rows) slots and return (slot_of, (corr_job, commit))
        for coupled CPU middle-to-leaf execution."""
        state = self._chan[channel]
        k = len(rows)
        if state["slots"] is None or state["slots"].shape[0] < k:
            state["slots"] = _aligned_zeros((k, self.length), dtype=np.complex64)
            state["support"] = [[] for _ in range(k)]
        support = state["support"]
        regions = state["regions"]
        sel = None if k == self.n_rows else rows
        out_support = _merge([w for j in range(k) for w in support[j]])

        def commit():
            for j in range(k):
                support[j] = regions

        job = (self.bank, state["series"], dict(
            windows=regions,
            templates=sel,
            out=state["slots"][:k],
            out_support=out_support,
        ))
        return {r: j for j, r in enumerate(rows)}, (job, commit)

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
    pending: list       # leaves in walk order, searched once the chunk's series exist
    corr_jobs: list     # CPU inner correlation jobs coupled with leaf filtering


#: Root transform plans by series length (HierarchicalSearch._root_plan).
_ROOT_PLANS: Dict[int, object] = {}


class HierarchicalSearch:
    """Run a forest of filter hierarchies over input blocks, delivering peaks through hooks.

    Parameters
    ----------
    roots : sequence of Root
        The hierarchies.
    threshold : float
        The leaf search threshold T.
    envelope_floor : float, optional
        The least value any threshold envelope a hook returns may take (default 1:
        envelopes only raise the threshold). Leaf banks are calibrated at
        T * envelope_floor, so no envelope can need a peak their gates dismissed.
    leaf_options : dict, optional
        Keyword arguments for each leaf's :class:`TimeDomainFilterBank` (engine,
        false_dismissal, binsize, coarse_band_hz, first_stage_snr, device, fft_lengths,
        tap_sample_rate, data_sample_rate), not ``threshold``.
    context : int, optional
        Samples beyond a leaf's windows over which hooks may read or refilter its parent's
        series (default 0).
    min_pad : int, optional
        The fewest guard samples any leaf's parent series holds past its windows, for
        example for chi-squared blocks (default 0).

    Raises
    ------
    ValueError
        For a threshold that is negative or not finite, an envelope floor below the
        minimum, a ``threshold`` in ``leaf_options``, or a negative ``context`` or
        ``min_pad``.
    """

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
        # a GPU plan holds one calibration: there each profile has a leaf bank of its own
        self._bank_per_profile = _parse_device(self.leaf_options.get("device")).kind == "gpu"
        self._parent = {}
        self._kids = {}                  # node -> (inner children, leaf children)
        self._leaf_banks = {}
        self._ready_banks = {}           # (leaf, channel) -> its bank, built and referenced
        self._inner = {}
        self._root_outs = {}             # (root, channel, n, parity) -> output buffer
        self._root_pos = {}              # channel -> its position (a GPU search's root buffers)
        self._root_placed = {}           # chunk -> where the current root's output was computed
        self._root_pooled = {}           # _root_outs keys taken from the device's pool -> pool
        self._root_tmpl = set()          # (root, n) whose spectrum the device holds this run
        #: The root's work done so far, {n: [blocks, band bins]}: _roofline.root_work's count.
        self.root_counts = {}
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

    def _channel_profile(self, root, channel):
        """The name of root's profile that channel is searched with (None where root has
        one profile for every channel, or none)."""
        prof = root.profile
        if not isinstance(prof, dict):
            return None
        return channel if channel in prof else next(iter(prof), None)

    def _call_profile(self, root, channel):
        """The profile a filtering call in channel names to its leaf bank: the channel's
        profile, or None where each profile has a bank of its own (a GPU search)."""
        return None if self._bank_per_profile else self._channel_profile(root, channel)

    def leaf_bank(self, root, leaf, channel=None):
        """The bank that searches a leaf below a root, built on first use.

        On the CPU one bank serves the leaf, holding a calibration for each of the root's
        profiles; its templates are stored once whatever the number of profiles. A channel's
        profile is set as its reference the first time that channel asks, and a filtering call
        names the profile it runs (``profile=``). On a GPU a plan holds one calibration, so
        each profile has a bank of its own, with its own copy of the templates.

        Parameters
        ----------
        root : Root
            The leaf's root.
        leaf : Leaf
            The leaf.
        channel : str, optional
            The channel whose profile the bank is to hold.

        Returns
        -------
        TimeDomainFilterBank
            The leaf's bank.
        """
        # Asked again for a bank it has handed out (every hook call asks): that bank.
        bank = self._ready_banks.get((id(leaf), channel))
        if bank is not None:
            return bank
        prof = root.profile
        which = self._channel_profile(root, channel)
        if isinstance(prof, dict):
            prof = prof.get(which)
        key = (id(leaf), which) if self._bank_per_profile else id(leaf)
        bank = self._leaf_banks.get(key)
        new = bank is None
        if new:
            t0 = time.perf_counter()
            opts = dict(self.leaf_options)
            opts["threshold"] = self.threshold * self.envelope_floor
            bank = self._leaf_banks[key] = TimeDomainFilterBank(leaf.taps, leaf.counts, **opts)
            self.timings["setup"] += time.perf_counter() - t0
        name = self._call_profile(root, channel)
        if prof is not None and (new if self._bank_per_profile else name not in bank.profiles):
            # the first reference settles the bank's block sizes; each calibrates its gates
            t0 = time.perf_counter()
            w, df = prof
            bank.set_reference(w, delta_f=df, profile=name)
            self.timings["setup"] += time.perf_counter() - t0
        self._ready_banks[(id(leaf), channel)] = bank
        return bank

    def _leaf_block_length(self, root, leaf):
        """The longest block leaf's bank below root uses or may still choose, once it holds
        every one of root's profiles."""
        prof = root.profile
        chans = list(prof) if isinstance(prof, dict) and prof else [None]
        return max(int(self.leaf_bank(root, leaf, c).max_block_length) for c in chans)

    def _leaves_below(self, node):
        inner, leaves = self._kids[id(node)]
        yield from leaves
        for c in inner:
            yield from self._leaves_below(c)

    def pad(self, root):
        """The most samples any leaf's parent series holds past its windows, below a root.

        This builds and calibrates every leaf bank below the root.

        Parameters
        ----------
        root : Root
            The root.

        Returns
        -------
        int
            The longest block any of the root's leaf banks uses or may still choose, and at
            least ``min_pad``.
        """
        return max([self.min_pad] + [self._leaf_block_length(root, lf)
                                     for lf in self._leaves_below(root)])

    def _batches(self, node, length, root=None):
        """Build the inner batches of node's subtree for series of length samples (once).
        On a GPU search their rows live in the leaf banks' device memory. root: the root
        above node (default node itself), whose profile a leaf bank built here is given."""
        root = node if root is None else root
        inner = self._kids[id(node)][0]
        if inner and id(node) not in self._inner:
            t0 = time.perf_counter()
            bank = self.leaf_bank(root, next(self._leaves_below(node)))
            dev = _parse_device(bank.device)
            self._inner[id(node)] = _InnerBatch(inner, length, self._real_output(node),
                                                device=dev if dev.kind == "gpu" else None)
            self.timings["setup"] += time.perf_counter() - t0
        for c in inner:
            self._batches(c, length, root)

    def _settle(self):
        """Wait for inner rows still being written on a device: a host reader follows."""
        for batch in self._inner.values():
            if batch.in_flight:
                batch.bank.wait()
                batch.in_flight = False

    def _root_output(self, root, channel, n, chunk):
        """Where root's output for a chunk goes. On a GPU search: two buffers per root and
        channel in the leaf device's memory, alternating by chunk, which the middle stage
        (and leaves directly below the root) read in place -- a hook reads it during its
        chunk, as it does the inner series. The next chunk's output is written while this
        chunk's leaves run (run); the buffer it reuses was read by the chunk before, whose
        leaves -- ordered after everything that read it -- have been collected. They are
        taken from the device's pool for the run (_gpuroot.DeviceRoot.take_output), so the
        search a caller builds for its next root writes the same ones, and whether the host
        or the device computes a root changes no buffer the middle stage reads. Elsewhere a
        host array of the search's own."""
        key = (id(root), channel, n, chunk % 2)
        out = self._root_outs.get(key)
        if out is None:
            dev = self._device_root(root)
            if dev is not None:
                pos = self._root_pos.setdefault(channel, len(self._root_pos))
                out = dev.take_output(n, pos, chunk % 2)
                self._root_pooled[key] = (dev, n, pos, chunk % 2)
            else:
                bank = self.leaf_bank(root, next(self._leaves_below(root)))
                on_gpu = _parse_device(bank.device).kind == "gpu"
                out = (bank.empty_shared((n,), np.float32) if on_gpu
                       else _page_aligned_empty((n,), np.float32))
            self._root_outs[key] = out
        return out

    def _device_root(self, root):
        """The root stage's device state (_gpuroot.DeviceRoot) on a GPU search, else None."""
        bank = self.leaf_bank(root, next(self._leaves_below(root)))
        dev = _parse_device(bank.device)
        return _gpuroot.device_root(dev) if dev.kind == "gpu" else None

    def _give_root_outputs(self):
        """Return the pooled root buffers this run took (see _root_output), once nothing
        reads or writes them (after a normal run nothing does: this waits on finished work)."""
        if not self._root_pooled:
            return
        _settle_device_writes()
        devs = set()
        for key, (dev, n, pos, parity) in self._root_pooled.items():
            dev.give_output(n, pos, parity, self._root_outs.pop(key))
            devs.add(dev)
        self._root_pooled.clear()
        for dev in devs:
            dev.collect()                 # free the copies of blocks whose arrays died

    def _root_place(self, root, n, k):
        """Where root's output of length n for chunk k is computed: "device" or "host"
        (_gpuroot.Placement), "host" on a CPU search or a length the device cannot run."""
        dev = self._device_root(root)
        if dev is None or dev.kernels(n) is None:
            return "host"
        return _gpuroot.placement(dev, n).next(k)

    def _real_output(self, node):
        """Whether node's output series is real: the root's is, and an inner node's is when
        its input is and its taps are."""
        if isinstance(node, Root):
            return True
        return (not np.iscomplexobj(node.taps)) and self._real_output(self._parent[id(node)])

    def _root_plan(self, n):
        """The root transform's plan for series length n, shared by every search in the
        process: a caller that builds a search per root (pycbc builds one per top template)
        made the same plan, with its twiddle tables, for each."""
        p = _ROOT_PLANS.get(n)
        if p is None:
            p = _ROOT_PLANS[n] = _core.Root(n)
        return p

    def run(self, inputs: Dict[str, BlockInput], windows: Optional[Callable] = None,
            on_series: Optional[Callable] = None, on_peaks: Optional[Callable] = None,
            on_chunk: Optional[Callable] = None):
        """Filter every input block through each root's hierarchy and call the hooks.

        Parameters
        ----------
        inputs : dict
            ``{channel: BlockInput}``.
        windows : callable, optional
            ``windows(leaf, chunk, channel, extra)`` says where a leaf's peaks are searched,
            widened by ``extra`` samples: None (the block's valid span), a list of
            (start, stop), or empty (the leaf is skipped in this chunk and channel). Windows
            are clipped to the valid span.
        on_series : callable, optional
            ``on_series(SeriesContext)`` runs when a root's output for a chunk is ready (inner
            nodes' series are read through :meth:`PeaksContext.series`). It may return
            ``{channel: envelope}``, where ``envelope(samples)`` gives the threshold scale at
            those samples (at least ``envelope_floor``), applied to every leaf below the root.
        on_peaks : callable, optional
            ``on_peaks(PeaksContext)`` runs per leaf per chunk.
        on_chunk : callable, optional
            ``on_chunk(ChunkContext)`` runs after a chunk.
        """
        try:
            self._run(inputs, windows, on_series, on_peaks, on_chunk)
        finally:
            self._give_root_outputs()

    def _run(self, inputs, windows, on_series, on_peaks, on_chunk):
        channels = list(inputs)
        nchunks = max(len(inputs[c].spectra) for c in channels) if channels else 0
        for root in self.roots:
            leaves = list(self._leaves_below(root))
            pads = {id(lf): max(self.min_pad, self._leaf_block_length(root, lf))
                    for lf in leaves}
            ahead = None                        # (chunk, channels, held, support) computed early
            self._root_placed.clear()
            self._root_tmpl.clear()
            trial = self._root_trial(root, inputs, channels, nchunks)
            started = False                     # a chunk ran: later ones may be samples
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
                mark = self._root_mark(root) if trial is not None and started else None
                started = True
                if ahead is not None and ahead[:2] == (k, active):
                    held, support = ahead[2], ahead[3]
                else:
                    held, support = self._roots(root, inputs, k, active)
                ahead = None
                self._batches(root, len(held[active[0]][id(root)]))
                envelopes = {}
                if on_series is not None:
                    if self._root_placed.get(k) == "device":
                        _settle_device_writes()     # the hook reads the root's output
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
                             live, on_peaks, [], [])
                self._walk(root, step)
                submitted = self._submit_leaves(step)
                # While the device searches this chunk's leaves, the next chunk's root outputs
                # on the host (into the other of two buffers: this chunk's are still read).
                nxt = [c for c in channels if k + 1 < len(inputs[c].spectra)]
                if submitted is not None and submitted[3] and nxt:
                    ahead = (k + 1, nxt) + self._roots(root, inputs, k + 1, nxt)
                self._finish_leaves(step, submitted)
                if on_chunk is not None:
                    on_chunk(ChunkContext(k, active, tags))
                if mark is not None:
                    self._root_sample(trial, root, mark, k, step)
            if trial is not None:
                trial.end_run()                 # the run's two halves are one round

    def _walk(self, node, step):
        """Queue node's leaves for the chunk's leaf search, then produce its live inner
        children (every channel) and walk each. Every node has its own row slots, so all the
        chunk's series coexist until the next chunk: the leaves are searched together once the
        walk is done (_submit_leaves, then _finish_leaves), with their ancestors' series still held for the hooks."""
        inner, leaves = self._kids[id(node)]
        step.pending.extend(leaves)
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
        couple_cpu = (batch._alloc is None
                      and all(not self._kids[id(batch.children[pos])][0] for pos in wanted))
        for c in step.active:
            spans = []
            for pos in wanted:
                self._span(batch.children[pos], c, step.need, step.pads, spans)
            regions = _clip(_merge(spans), 0, L)
            regions_by_chan[c] = regions
            batch.prepare(c, held[c][id(node)], regions)
            if couple_cpu:
                slot_of[c], job = batch.prepare_job(c, rows)
                step.corr_jobs.append(job)
        if not couple_cpu:
            slot_of.update(batch.compute_channels(step.active, rows))
        members = sorted(wanted, key=lambda p: batch.row_of[p])
        for pos in members:
            child = batch.children[pos]
            for c in step.active:
                held[c][id(child)] = batch.view(c, slot_of[c][batch.row_of[pos][0]], pos)
                step.support[c][id(child)] = regions_by_chan[c]
        self.timings["inner"] += time.perf_counter() - t0
        for pos in members:
            self._walk(batch.children[pos], step)

    def _roots(self, root, inputs, k, active):
        """Root's output for chunk k in every active channel: (held, support). Computed on
        the device or the host as _root_place says (the same buffers either way); a device
        root is left in flight, ordered before the device's readers of it."""
        held = {c: {} for c in active}
        support = {c: {} for c in active}
        t0 = time.perf_counter()
        specs = [inputs[c].spectra[k] for c in active]
        lengths = {2 * (len(spec) - 1) for spec in specs}
        outs = [self._root_output(root, c, 2 * (len(spec) - 1), k)
                for c, spec in zip(active, specs)]
        scales = [float(inputs[c].root_scale(root, k)) for c in active]
        k0, k1 = root.band
        place = self._root_place(root, lengths.pop(), k) if len(lengths) == 1 else "host"
        if place == "device":
            n = len(outs[0])
            dev = self._device_root(root)
            try:
                if (id(root), n) not in self._root_tmpl:
                    dev.set_template(n, root.spectrum)
                    self._root_tmpl.add((id(root), n))
                dev.run(n, k % 2, specs, outs, (k0, k1), scales)
            except UnsupportedSize:        # an input the device cannot hold: on the host
                place = "host"
        if place == "host":
            for spec, out, scale in zip(specs, outs, scales):
                self._root_plan(len(out)).real(np.ascontiguousarray(spec, dtype=np.complex64),
                                               root.spectrum, k0, k1, scale, out)
        self._root_placed[k] = place
        for out in outs:
            cnt = self.root_counts.setdefault(len(out), [0, 0])
            cnt[0] += 1
            cnt[1] += max(0, min(k1, len(out) // 2 + 1) - k0)
        for c, out in zip(active, outs):
            held[c][id(root)] = out
            support[c][id(root)] = [(0, len(out))]
        self.timings["root"] += time.perf_counter() - t0
        return held, support

    def _root_trial(self, root, inputs, channels, nchunks):
        """The open placement trial (_gpuroot.Placement) of root's outputs in this run of
        nchunks chunks, or None: a CPU search, a length the device cannot run, or a
        placement already chosen."""
        spectra = [inputs[c].spectra[0] for c in channels if len(inputs[c].spectra)]
        if not spectra:
            return None
        n = 2 * (len(spectra[0]) - 1)
        dev = self._device_root(root)
        if dev is None or dev.kernels(n) is None:
            return None
        trial = _gpuroot.placement(dev, n)
        if trial.winner() is not None:
            return None
        trial.new_run(nchunks)
        return trial

    def _root_mark(self, root):
        """What a chunk's placement sample starts from: (time, setup time, device root
        setup count, host root plans)."""
        return (time.perf_counter(), self.timings["setup"], self._device_root(root).built,
                len(_ROOT_PLANS))

    def _root_sample(self, trial, root, mark, k, step):
        """Chunk k's wall time and leaf work for the placement trial (_gpuroot.Placement):
        when both roots it used were computed at one place and no setup ran in it."""
        place = self._root_placed.get(k)
        if place is None or self._root_placed.get(k + 1, place) != place:
            return
        if (self.timings["setup"] != mark[1] or self._device_root(root).built != mark[2]
                or len(_ROOT_PLANS) != mark[3]):
            return
        work = sum(len(lf.counts) * sum(b - a for a, b in step.win[(id(lf), c)])
                   for lf in self._leaves_below(root) for c in step.active)
        if work:
            trial.sample(place, time.perf_counter() - mark[0], work)

    def _submit_leaves(self, step):
        """Start the chunk's leaf searches, in every channel: (leaves, jobs, where, deferred,
        results), or None when no leaf is searched.

        On a GPU the searches are one filter_series_many batch, submitted and left in flight
        (deferred): every call submitted before any is collected, so the device is not idle
        while the host prepares the next leaf -- or the next chunk's root. On the CPU the batch
        runs each in turn, as filter_series, and its banks' joint trial takes its rounds on it.
        The results are the same either way."""
        leaves = [lf for lf in step.pending if any(step.win[(id(lf), c)] for c in step.active)]
        if not leaves:
            if step.corr_jobs:
                cjobs = [jb for jb, _ in step.corr_jobs]
                t_info = {}
                TimeDomainFilterBank.correlate_and_filter_many(
                    cjobs, [], timings=t_info,
                    retain_radius=0 if step.on_peaks is None else None,
                )
                if not t_info.get("ephemeral_used", False):
                    for _, commit in step.corr_jobs:
                        commit()
                self.timings["inner"] += t_info["correlate"]
            return None
        t0 = time.perf_counter()
        jobs, where = [], {}
        for lf in leaves:
            for c in step.active:
                w = step.win[(id(lf), c)]
                if w:
                    bank = self.leaf_bank(step.root, lf, c)
                    series = step.held[c][id(self._parent[id(lf)])]
                    # one window as a slice: filter_series memoises a slice's layout
                    where[(id(lf), c)] = len(jobs)
                    jobs.append((bank, series, dict(windows=slice(*w[0]) if len(w) == 1 else w,
                                                    profile=self._call_profile(step.root, c))))
        # A bank's device None is MF_DEVICE's (device.parse), as everywhere in the library.
        deferred = any(_parse_device(b.device).kind == "gpu" for b, _, _ in jobs)
        if step.corr_jobs and not deferred:
            cjobs = [jb for jb, _ in step.corr_jobs]
            t_info = {}
            results = TimeDomainFilterBank.correlate_and_filter_many(
                cjobs, jobs, wait=True, timings=t_info,
                retain_radius=0 if step.on_peaks is None else None,
            )
            if not t_info.get("ephemeral_used", False):
                for _, commit in step.corr_jobs:
                    commit()
            dt_total = time.perf_counter() - t0
            self.timings["inner"] += t_info["correlate"]
            self.timings["leaf"] += max(0.0, dt_total - t_info["correlate"])
        else:
            if step.corr_jobs:
                cjobs = [jb for jb, _ in step.corr_jobs]
                t_info = {}
                TimeDomainFilterBank.correlate_and_filter_many(cjobs, [], timings=t_info)
                for _, commit in step.corr_jobs:
                    commit()
                self.timings["inner"] += t_info["correlate"]
                t0 = time.perf_counter()
            # On the CPU too as one batch (filter_series_many runs it in order), where the leaves'
            # joint trial takes its rounds on real calls (time_domain._joint_round).
            results = TimeDomainFilterBank.filter_series_many(jobs, wait=not deferred)
            self.timings["leaf"] += time.perf_counter() - t0
        return leaves, jobs, where, deferred, results

    def _finish_leaves(self, step, submitted):
        """Collect what _submit_leaves started, apply the envelopes, and run each leaf's
        on_peaks in walk order."""
        if submitted is None:
            return
        leaves, jobs, where, deferred, results = submitted
        t0 = time.perf_counter()
        if deferred:
            results = [r.result() for r in results]
        found = []
        for lf in leaves:
            peaks, scales = {}, {}
            for c in step.active:
                envelope = step.envelopes.get(c)
                j = where.get((id(lf), c))
                if j is None:
                    peaks[c] = _EMPTY_FILTER_RESULTS
                    if envelope is not None:
                        scales[c] = np.empty(0, dtype=np.float64)
                    continue
                peaks[c], e = self._apply_envelope(results[j], lf, envelope, len(jobs[j][1]))
                if e is not None:
                    scales[c] = e
            found.append((lf, peaks, scales))
        self.timings["leaf"] += time.perf_counter() - t0
        if step.on_peaks is not None:
            t0 = time.perf_counter()
            for lf, peaks, scales in found:
                step.on_peaks(PeaksContext(self, step.root, lf, step.chunk, step.active,
                                           step.tags, peaks, step.held, scales, step.support))
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
