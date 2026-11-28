"""Gate chains: one model for every hierarchical configuration.

A configuration is a chain of coarse bands b1 < b2 < ... < bk followed by the
full refine. k = 1 is what used to be called a single-tier gate, k = 2 a
cascade; they are the same object here, enumerated, priced and chosen on equal
footing. Each tier runs on the previous tier's survivors.

Two questions decide a chain, and they are kept separate:

  ACCURACY  For a signal of strength `snr`, the thresholds g1..gk (and on the
            CPU the direct refine's window) must dismiss `fd` of the pairs the
            full filter would keep, on average, with the per-plan tail
            gatemodel.fit_order states. Taken from joint draws of every tier's
            coarse maximum and the fine maximum under signal (the same
            construction as gatemodel, generalised from two tiers to any set of
            bands; all candidate bands are drawn jointly, so every chain is
            evaluated on the same draws).

  COST      Expected cost per (block, template) pair:
                dense(b1) + sum_i P(reach tier i) sparse(b_i | density)
                          + P(reach refine) refine(density)
            The P's are noise-only pass probabilities of whole-block maxima,
            simulated exactly from the reference profile: the filter output
            noise in a block has independent bins with variance given by the
            profile, so a tier at band b sees the b-point inverse transform of
            the first b bins -- precisely its coarse lag grid. Tiers are nested
            and share their noise, so their passes are strongly correlated; the
            simulation carries that, which a product of marginal rates cannot.
            Per-tier costs are measured on the machine the job runs on, through
            the engine itself (calibrate_costs), as functions of survivor
            density: pooled tiers and the refine amortise less when few pairs
            survive. Nothing is tabulated; the numbers belong to this process.

The model does not have to be exact. Its job is to keep the cheapest chain on a
short list; the autotuner measures the short list on the real workload.

The budget is split between the tiers by minimising that cost on half the draws, and
the thresholds are fitted on the other half (plan_chain), so that no choice is judged on
the draws it was made on; the split is part of the chain's plan.
"""
import math
import weakref
from collections import OrderedDict
import numpy as np

from . import gatemodel as _gm
from . import _config, _costfile, _costmodel, _gatedraws
# The decision rules live in _choice; gatechain's callers keep them by these names.
from ._choice import TIE
# The cost file lives in _costfile. The calibration, the bank's layout and the Vulkan back end
# reach these through gatechain (and tests patch _cost_file here), so they stay bound here.
_cost_file, _store_first = _costfile._cost_file, _costfile._store_first
store_choice, stored_choice = _costfile.store_choice, _costfile.stored_choice

# The draws a plan rests on live in _gatedraws. The planner uses these; private names of
# that module are reached there, not here.
from ._gatedraws import (
    _MIN_BAND, model_draws, _band_slice, band_offset, candidate_bands, usable_bands,
    enumerate_chains, _norm_profile, _cache_put, _similar_get, _similar_put, _SEED,
    local_window, _law_applies, _law_profile, _signal_table, _Beside, _column, _signal_records,
    noise_block_maxima,
)
from . import _core
# Its public names, kept under gatechain as well.
signal_draws = _gatedraws.signal_draws

#: The per-tier budget shares the split search tries (plan_chain; three tiers search their
#: product). MEASURED: the fitted plans of a search on 19 shares instead (19 x 19 for three
#: tiers) cost within 0.05% of these on average over every given chain, and within 0.4 +- 0.3%
#: for the pick, where a few of 50 picks change chain either way (5 profiles x 10 model seeds,
#: n = 2048 and 4096, fd 1e-3, Zen 5 costs, with and without a direct refine; 2026-10-29). The
#: fit moves every tier's threshold, so the split's fine structure matters little.
_SPLIT = np.linspace(0.05, 0.95, 9)




# The cost model lives in _costmodel; callers and tests reach it through these names.
_LOG_TABLES = _costmodel._LOG_TABLES
_log_table = _costmodel._log_table
_interp_clamped = _costmodel._interp_clamped
band_forward_wanted = _costmodel.band_forward_wanted
CostModel = _costmodel.CostModel
_COSTS = _costmodel._COSTS
_PLAN_DIAGNOSTICS = _costmodel._PLAN_DIAGNOSTICS
_internal_plans = _costmodel._internal_plans
cpu_gate_kind = _costmodel.cpu_gate_kind
_cost_sig = _costmodel._cost_sig
_CAL_DENSITIES = _costmodel._CAL_DENSITIES
gpu_kernel_id = _costmodel.gpu_kernel_id
_cost_model_ok = _costmodel._cost_model_ok
_stored_cost_model = _costmodel._stored_cost_model
_CAL_TEMPLATES = _costmodel._CAL_TEMPLATES
_Q15_BAND = _costmodel._Q15_BAND
_q15_band = _costmodel._q15_band
default_series_group = _costmodel.default_series_group
_run_ms = _costmodel._run_ms
_is_gpu = _costmodel._is_gpu


def _reach(N, cols, thresholds):
    """Cumulative noise pass probabilities through the chain."""
    alive = np.ones(N.shape[0], bool)
    out = [1.0]
    for c, g in zip(cols, thresholds):
        alive &= N[:, c] >= g
        out.append(float(alive.mean()))
    return out


_KEPT = OrderedDict()
_KEPT_MAX = 4096


def _derived_get(cache, key, *sources):
    """(True, value) when `cache` holds a value derived from exactly these arrays under
    `key`, else (False, None)."""
    hit = cache.get(key)
    if hit is None or len(hit[0]) != len(sources) or any(r() is not s for r, s in zip(hit[0], sources)):
        return False, None
    cache.move_to_end(key)
    return True, hit[1]


def _derived_put(cache, key, sources, value, cap):
    """Hold `value`, derived from the arrays `sources`, under `key` for as long as they live.

    The key names the sources by identity, so the entry holds weak references to them and is
    dropped when one is freed: it can neither be served for a new array at a recycled id nor
    keep the draws alive after their own cache (_SIGNAL_CACHE, _NOISE_CACHE) has let them go.
    Holding the sources themselves kept every evicted set of draws, and what was derived
    from it, until `cap` entries had passed."""
    def drop(ref, cache=cache, key=key):
        hit = cache.get(key)
        if hit is not None and any(r is ref for r in hit[0]):
            del cache[key]
    cache[key] = (tuple(weakref.ref(x, drop) for x in sources), value)
    while len(cache) > cap:
        cache.popitem(last=False)


def kept_draws(sig, bands, chain, snr):
    """Coarse maxima of `chain`'s tiers for the draws the fine stage keeps (fine max >= snr).

    signal_draws' maxima are over the whole searched window, as the engine's (hmf.c), so a
    tier whose gate falls below the window's noise floor passes the draws a noise peak
    elsewhere in the block carries. Memoised per draws (by identity, held so they cannot be
    reused), chain and snr: every template group pricing a profile asks again."""
    C, F = sig[0], sig[1]
    held = sig[0]                       # what the memo is kept with: a _Beside is written out
    if isinstance(C, _Beside):
        C = C.full()
    cols = [bands.index(b) for b in chain]
    key = (id(held), id(F), tuple(cols), float(snr))
    found, out = _derived_get(_KEPT, key, held, F)
    if found:
        return out
    # When F broadcasts one fine maximum across all columns (signal_draws), filter C once per
    # (C, F, snr) and slice columns per chain rather than copying and scanning F[:, cols].
    if F.ndim == 2 and F.shape[1] > 0 and F.strides[1] == 0:
        bkey = ("kept_all", id(held), id(F), float(snr))
        found, c_kept = _derived_get(_KEPT, bkey, held, F)
        if not found:
            c_kept = C[F[:, 0] >= snr]
            _derived_put(_KEPT, bkey, (held, F), c_kept, _KEPT_MAX)
        out = c_kept[:, cols]
    else:
        keep = F[:, cols[0]] >= snr
        for c in cols[1:]:
            keep = keep | (F[:, c] >= snr)
        out = C[keep][:, cols]
    out.setflags(write=False)
    _derived_put(_KEPT, key, (held, F), out, _KEPT_MAX)
    return out


def _smallest(col, m):
    """Indices of col's m smallest values, in ascending order of value (O(len) selection)."""
    m = min(int(m), col.size)
    if m <= 0:
        return np.empty(0, np.int64)
    idx = np.argpartition(col, m - 1)[:m] if m < col.size else np.arange(col.size)
    return idx[np.argsort(col[idx], kind="stable")]


#: plan_chain's candidates per (draws, chain, prune, half-widths): they do not depend on the
#: cost model, so every template group pricing the same profile and window reuses them.
_CAND_CACHE = OrderedDict()
_CAND_CACHE_MAX = 4096


def _halves(x):
    """(search half, fit half) of the detections x: its even rows and its odd rows, each
    contiguous. The detections are independent draws in simulation order, so the halves are
    independent of each other."""
    key = ("halves", id(x))
    found, halves = _derived_get(_KEPT, key, x)
    if found:
        return halves
    a = np.ascontiguousarray(x[0::2])
    b = np.ascontiguousarray(x[1::2])
    a.setflags(write=False)
    b.setflags(write=False)
    _derived_put(_KEPT, key, (x,), (a, b), _KEPT_MAX)
    return a, b


class _Columns:
    """A chain's columns of one half of a table's detections, without a copy of them: `cols`
    the tier's columns, each a contiguous 1-D view of the table's half (held column by
    column, _kept_halves). Reads like the (M, k) array it stands for where the planner reads
    one: shape, S[:, i], S[rows, i]."""
    __slots__ = ("cols", "held", "shape")

    def __init__(self, cols, held=None):
        self.cols = tuple(cols)
        # per column, (the array that holds it, which of its columns): what a column's
        # memos are kept with, a view being made anew for every chain
        self.held = tuple(held) if held is not None else tuple((c, 0) for c in self.cols)
        self.shape = (int(self.cols[0].shape[0]), len(self.cols))

    def __getitem__(self, key):
        rows, i = key
        return self.cols[i][rows]

    def smallest(self, i, m):
        """_smallest of column i, held with the column: every chain through a band, every
        window and cost model asks for the same few of the same column."""
        owner, which = self.held[i]
        key = ("smallest", id(owner), int(which), int(m))
        found, out = _derived_get(_KEPT, key, owner)
        if not found:
            out = _smallest(self.cols[i], m)
            out.setflags(write=False)
            _derived_put(_KEPT, key, (owner,), out, _KEPT_MAX)
        return out

    def score(self, thresholds):
        """Per detection, the smallest of its columns less their thresholds (_fit)."""
        out = self.cols[0] - np.float64(thresholds[0])
        for col, t in zip(self.cols[1:], thresholds[1:]):
            np.minimum(out, col - np.float64(t), out=out)
        return out


def _kept_halves(sig, bands, cols, chain, snr):
    """(search half, fit half) of kept_draws(sig, bands, chain, snr), as _halves of it would
    be, each a _Columns. Where one fine maximum serves every band (signal_draws), the kept
    draws of all bands are halved once per draws, column by column (Fortran order), and a
    chain's halves are views of its columns: every chain of every window and cost model of a
    profile reads the same two arrays, where each held its own copies of both halves (ten to
    twenty chains a table, four times the table)."""
    C, F = sig[0], sig[1]
    if not (F.ndim == 2 and F.shape[1] > 0 and F.strides[1] == 0):
        a, b = _halves(kept_draws(sig, bands, chain, snr))
        return (_Columns([a[:, i] for i in range(a.shape[1])], [(a, i) for i in range(a.shape[1])]),
                _Columns([b[:, i] for i in range(b.shape[1])], [(b, i) for i in range(b.shape[1])]))
    if isinstance(C, _Beside):
        # a retention's draws: the plain draws' halves of the columns they share (F is the
        # plain draws' own, so the kept rows are theirs), its own of the others
        pa, pb = _kept_table(C.plain, F, snr)
        a_cols, b_cols, a_held, b_held = [], [], [], []
        for c in cols:
            if c not in C.own:
                a_cols.append(pa[:, c]); b_cols.append(pb[:, c])
                a_held.append((pa, c)); b_held.append((pb, c))
            else:
                key = ("kept_column", id(C), id(F), int(c), float(snr))
                found, own = _derived_get(_KEPT, key, C, F)
                if not found:
                    kept = C.own[c][F[:, 0] >= snr]
                    own = (np.ascontiguousarray(kept[0::2]), np.ascontiguousarray(kept[1::2]))
                    for x in own:
                        x.setflags(write=False)
                    _derived_put(_KEPT, key, (C, F), own, _KEPT_MAX)
                a_cols.append(own[0]); b_cols.append(own[1])
                a_held.append((own[0], 0)); b_held.append((own[1], 0))
        return _Columns(a_cols, a_held), _Columns(b_cols, b_held)
    a, b = _kept_table(C, F, snr)
    return (_Columns([a[:, c] for c in cols], [(a, c) for c in cols]),
            _Columns([b[:, c] for c in cols], [(b, c) for c in cols]))


def _kept_table(C, F, snr):
    """The two halves (even rows, odd rows) of the draws C whose fine maximum F reaches snr,
    each in Fortran order: a column of either is contiguous."""
    key = ("kept_columns", id(C), id(F), float(snr))
    found, halves = _derived_get(_KEPT, key, C, F)
    if not found:
        kept = C[F[:, 0] >= snr]
        halves = (np.asfortranarray(kept[0::2]), np.asfortranarray(kept[1::2]))
        for x in halves:
            x.setflags(write=False)
        _derived_put(_KEPT, key, (C, F), halves, _KEPT_MAX)
    return halves


#: One buffer the C search reads the shape of its detections from (it reads nothing else of
#: them, _core.chain_candidates): grown to the largest (M, k) asked, so no call allocates.
_SHAPE_ONLY = [np.empty(0, np.float32)]


def _shape_only(M, k):
    if _SHAPE_ONLY[0].size < M * k:
        _SHAPE_ONLY[0] = np.empty(M * k, np.float32)
    return _SHAPE_ONLY[0][:M * k].reshape(M, k)


def _distances(sig, lags, bands, chain, snr, n, far=None):
    """Per detection (kept_draws' rows), how far the fine maximum lies from the chain's last
    tier's coarse maximum, in that tier's coarse samples: the direct refine's window of
    half-width h around the coarse maximum holds the fine peak iff this is at most h
    (hmf.c refine_direct_pair).

    far: the noise maxima of the window searched (noise_block_maxima), for draws read in a
    narrower window (local_window). The engine refines around the last tier's largest coarse
    value in the window, and noise far from the signal can be that: the refine then looks
    where the signal is not. Draws in the local window cannot show it, so each is paired
    with one block's noise maximum of the searched window (stationary noise: what lies far
    from the signal is independent of what lies beside it), and where that exceeds the
    draw's own coarse maximum the distance is the band's whole length, beyond any window.
    The pairing counts the local window's own lags among the far ones, so it errs towards
    more such draws, which the plan charges to its budget."""
    A, B = _distance_halves(sig, lags, bands, chain, snr, n, far)
    out = np.empty(A.size + B.size, np.float64)
    out[0::2], out[1::2] = A.values(), B.values()
    return out


class _Distances:
    """One half of a table's detections' _distances, without an array per window: `base`
    the distances in the draws' own window (float32: whole coarse samples over a power of
    two, exact), shared by every window; `far` the few detections (indices into the half,
    ascending) that noise far from the signal draws the refine away from in the window
    searched, which lie beyond every half-width (at `limit`, the band's length)."""
    __slots__ = ("base", "far", "limit", "size", "__weakref__")

    def __init__(self, base, far, limit):
        self.base, self.far, self.limit, self.size = base, far, float(limit), int(base.size)

    def beyond(self, h):
        """Indices of the detections beyond half-width h, ascending."""
        out = np.flatnonzero(self.base > h)
        return np.union1d(out, self.far) if self.far.size else out

    def mask_beyond(self, h):
        out = self.base > h
        if self.far.size:
            out[self.far] = True
        return out

    def count_beyond(self, h):
        return int(np.count_nonzero(self.base > h)) + int(np.count_nonzero(self.base[self.far] <= h))

    def values(self):
        """The distances as one array (a copy), the far ones at the limit."""
        out = self.base.astype(np.float64)
        out[self.far] = self.limit
        return out


def _distance_halves(sig, lags, bands, chain, snr, n, far=None):
    """(search half, fit half) of _distances(sig, lags, bands, chain, snr, n, far), each a
    _Distances: the draws' own distances halved once per draws and last band, whatever the
    window, and per window only the indices of the detections its far noise takes
    (_distances has what they are). A window's own array of distances and its two halves
    were a megabyte and a half for a few dozen such detections."""
    F = sig[1]
    fat, cat = lags
    b = int(chain[-1])
    col = bands.index(b)
    C = sig[0]
    if isinstance(C, _Beside) and col not in C.own:
        # a retention that leaves the last band alone: the plain draws' distances are its own
        C, cat = C.plain, cat.plain
    key = ("dist32", id(F), id(fat), id(cat), col, b, float(snr), int(n))
    found, base = _derived_get(_KEPT, key, F, fat, cat)
    if not found:
        keep = F[:, 0] >= snr
        base = (np.abs(fat[keep] - _column(cat, col)[keep]) / (n // b)).astype(np.float32)
        base.setflags(write=False)
        _derived_put(_KEPT, key, (F, fat, cat), base, _KEPT_MAX)
    a, bb = _halves(base)
    none = np.empty(0, np.int64)
    if far is None:
        return _Distances(a, none, b), _Distances(bb, none, b)
    fkey = ("far", id(C), id(F), col, float(snr), id(far))
    found, idx = _derived_get(_KEPT, fkey, C, F, far)
    if not found:
        own = _column(C, col)[F[:, 0] >= snr]
        # the noise rows, repeated in order to the length of the kept draws
        rows = np.flatnonzero(np.resize(far[:, col], own.size) > own)
        idx = (rows[rows % 2 == 0] // 2, rows[rows % 2 == 1] // 2)
        _derived_put(_KEPT, fkey, (C, F, far), idx, _KEPT_MAX)
    return _Distances(a, idx[0], b), _Distances(bb, idx[1], b)


def _all_halfwidths(dist, allow):
    """Cost-independent candidate half-widths (None, hmin, ...) for search half `dist`."""
    if dist is None or allow < 0:
        return (None,)
    if isinstance(dist, _Distances):
        key = ("hws", id(dist.base), dist.far.tobytes(), int(allow))
        found, out = _derived_get(_KEPT, key, dist.base)
        if found:
            return out
        source, dist = (dist.base,), dist.values()
    else:
        key = ("hws", id(dist), int(allow))
        found, out = _derived_get(_KEPT, key, dist)
        if found:
            return out
        source = (dist,)
    if dist.size > allow:
        kth = dist.size - 1 - allow
        hmin = max(1, int(math.ceil(np.partition(dist, kth)[kth])))
    else:
        hmin = 1
    up = np.ceil(dist[dist > hmin]).astype(np.int64)
    out = (None,) + tuple(sorted({hmin} | {int(h) for h in up}))
    _derived_put(_KEPT, key, source, out, _KEPT_MAX)
    return out


def _halfwidths(dist, allow, cost, chain, n, all_hws=None):
    """The direct refine's candidate half-widths for `chain` on the search half (dist its
    detections' _distances): None, the whole-block refine, which loses no detection; and,
    where the cost model prices a direct refine for the chain (CostModel.prices_direct), each
    whole number of coarse samples at which a different set of the detections lies beyond
    it, from the smallest leaving at most `allow` of them beyond it (gatemodel.
    window_allowance; -1: none may be missed) to the largest whose window the model prices
    below its dearest whole-block refine. Each is the smallest half-width with its set, so the
    cheapest window losing those detections."""
    if dist is None or cost is None or allow < 0 or not cost.prices_direct(chain):
        return (None,)
    R = n // int(chain[-1])
    top = max(v for _, v in cost._refine)
    dbase = getattr(cost, "direct_base", 0.0)
    hmax = int(((top - dbase) / cost.direct_lag - 1.0) // (2 * R))      # 2 h R + 1 lags priced below top
    if all_hws is None:
        all_hws = _all_halfwidths(dist, allow)
    if len(all_hws) < 2 or hmax < all_hws[1]:
        return (None,)
    return (None,) + tuple(h for h in all_hws[1:] if h <= hmax)


class _LazyPlan(dict):
    """A plan_chain dict whose fit-half thresholds and noise reach materialize on first read."""

    __slots__ = ("_pending",)

    def __init__(self, eager, pending):
        super().__init__(eager)
        self._pending = pending

    def _materialize(self):
        pending = self._pending
        if pending is None:
            return
        self._pending = None
        B, dB, th, hw, fd, noise, cols = pending
        thresholds, halfwidth = _fit(B, dB, th, hw, fd)
        super().__setitem__("thresholds", thresholds)
        super().__setitem__("reach", tuple(_reach(noise, cols, thresholds)))
        super().__setitem__("halfwidth", halfwidth)

    def __getitem__(self, key):
        if not super().__contains__(key) and self._pending is not None:
            self._materialize()
        return super().__getitem__(key)

    def get(self, key, default=None):
        if not super().__contains__(key) and self._pending is not None:
            self._materialize()
        return super().get(key, default)

    def __contains__(self, key):
        if super().__contains__(key):
            return True
        if self._pending is not None:
            self._materialize()
            return super().__contains__(key)
        return False

    def __len__(self):
        if self._pending is not None:
            self._materialize()
        return super().__len__()

    def __iter__(self):
        if self._pending is not None:
            self._materialize()
        return super().__iter__()

    def keys(self):
        if self._pending is not None:
            self._materialize()
        return super().keys()

    def values(self):
        if self._pending is not None:
            self._materialize()
        return super().values()

    def items(self):
        if self._pending is not None:
            self._materialize()
        return super().items()

    def copy(self):
        if self._pending is not None:
            self._materialize()
        return dict(self)

    def __eq__(self, other):
        if self._pending is not None:
            self._materialize()
        if isinstance(other, _LazyPlan) and other._pending is not None:
            other._materialize()
        return super().__eq__(other)

    def __repr__(self):
        if self._pending is not None:
            self._materialize()
        return super().__repr__()

    def __reduce__(self):
        if self._pending is not None:
            self._materialize()
        return (dict, (dict(self),))


def plan_chain(sig, noise, bands, chain, fd, cost, n, snr, prune=False, ntemplates=None,
               memo=None, lags=None, lazy_fit=False, offsets=None, far=False,
               band_forward=_costmodel.READ_ENV):
    """The thresholds and direct-refine half-width for `chain` that meet the false-dismissal
    budget fd at minimum modelled cost.

    sig, noise: signal_draws / noise_block_maxima over `bands` and the same window; lags: the
    draws' lags (signal_draws(..., lags_too=True)), for the direct refine's window where the
    cost model prices one. Returns dict(chain, thresholds, reach, halfwidth, cost, q15,
    search), or None when fd cannot be resolved: the thresholds and the half-width (None:
    the whole-block refine) the filter runs with and the noise share reaching each tier and
    the refine under them; the modelled cost, q15 and `search` (its thresholds, reach,
    half-width and the search half's detections its window misses, of a budget of K) of the
    plan as searched, which every choice ranks plans by.

    The detections fall into two independent halves (_halves), and the plan's dismissal is
    a fraction of the detections: those some tier dismisses or the direct refine's window
    misses, together.

    The SEARCH half decides the plan's structure. Every split of its budget of K dismissed
    detections between the tiers (over the shares _SPLIT) and every candidate half-width
    (_halfwidths: windows missing at most gatemodel.window_allowance of the detections, which
    count against the same K) gives candidate thresholds, and the one the cost model prices
    cheapest wins, the earliest on a tie. A search keeps the candidate those draws flatter,
    so its dismissal on them is not its dismissal: nothing it chooses is judged on them.

    The FIT half sets the thresholds: the search's, every tier moved by one shift fitted to
    the fit half (_fit). Given the search half, the fit half is independent of the plan's
    structure, so the plan's dismissal has mean fd and the tail gatemodel.fit_order sets,
    whatever the search and every choice made from it (choose_chain's among chains included).

    The search's candidates do not depend on the cost model; only their pricing does. Its
    selection works on each column's K-or-so smallest values (a selection, not a sort) and
    on the few dismissed draws' indices, and carries noise passes down the split search, so
    candidates sharing a prefix share its work. memo, a key naming the draws (_choose_chain
    passes the profile, n, window and draw parameters), caches the candidates, so another
    template group or cost model prices them without searching again. band_forward:
    MF_BAND_FORWARD's value where the caller has read it (a chain choice prices many chains
    and reads it once), for the feed's price (CostModel.feed_delta).
    """
    # The search's structure -- the draws' halves, the budget, the detections' distances,
    # the candidate half-widths -- does not depend on the cost model or the template count,
    # only on the draws: kept per draws and chain (_PREP_CACHE), so the template groups and
    # banks that share draws but price apart (a GPU's feed per template, a group's
    # direct-refine fraction) price one search's structure.
    eff_prune = bool(prune) and len(chain) > 1
    pkey = None if memo is None else (("prep",) + tuple(memo)
                                      + (tuple(int(b) for b in chain), eff_prune, bool(far),
                                         lags is not None))
    found, prep = (_derived_get(_PREP_CACHE, pkey, sig[0], sig[1], noise) if pkey is not None
                   else (False, None))
    if not found:
        prep = _prepare_chain(sig, noise, bands, chain, fd, n, snr, lags, far)
        if pkey is not None:
            _derived_put(_PREP_CACHE, pkey, (sig[0], sig[1], noise), prep, _CAND_CACHE_MAX)
    if prep is None:
        return None
    cols, A, B, K, dA_all, dB_all, allow, all_hws = prep
    dA = dB = None
    if lags is not None and cost is not None and cost.prices_direct(chain):
        dA, dB = dA_all, dB_all
    hws = _halfwidths(dA, allow, cost, chain, n, all_hws=all_hws)
    key = None if memo is None else tuple(memo) + (tuple(int(b) for b in chain), eff_prune, all_hws)
    found, cands = _derived_get(_CAND_CACHE, key, sig[0], noise) if key is not None else (False, None)
    if not found:
        cand_hws = all_hws if key is not None else hws
        dead = tuple(np.empty(0, np.int64) if h is None else dA_all.beyond(h)
                     for h in cand_hws)
        cands = _chain_candidates(A, noise, cols, K, eff_prune, dead)
        if key is not None:
            _derived_put(_CAND_CACHE, key, (sig[0], noise), cands, _CAND_CACHE_MAX)
    best = None
    has_feed = bool(ntemplates and getattr(cost, "feed", None))
    if has_feed and band_forward is _costmodel.READ_ENV:
        band_forward = _config.get("MF_BAND_FORWARD")
    k = len(chain)
    # Hoist prefix tier costs across candidate half-widths when pricing on CostModel (k >= 2)
    if isinstance(cost, CostModel) and k >= 2:
        later = chain[1:]
        prices_dir = cost.prices_direct(chain)
        dlag = cost.direct_lag if prices_dir else 0.0
        dbase = cost.direct_base if prices_dir else 0.0
        dmfrac = cost.direct_multi_frac if prices_dir else 0.0
        dfrac = cost.direct_frac if prices_dir else 1.0
        b_last = int(chain[-1]) if prices_dir else 0
        has_last_sparse = bool(prices_dir and dmfrac > 0.0 and b_last in cost._sparse)
        R = n // b_last if prices_dir else 0
        tables = None if not _C_PRICING else _pricing_tables(
            cost, chain, prices_dir, dbase, dlag, R, dfrac, dmfrac if has_last_sparse else None)
        if tables is not None:
            # every candidate priced in C (_core.plan_best), as the loop below prices them,
            # the feed by feed_delta's rule (feed_rule)
            feed = (_costmodel.feed_rule(cost, chain, ntemplates, band_forward)
                    if has_feed else None)
            found = _core.plan_best(cands, tuple(hws), *tables, feed)
            if found is not None:
                c, at, which = found
                pth, preach, lasts = cands[at]
                best = (c, pth + (lasts[which][0],), preach + (lasts[which][1],), hws[which])
            cands = ()
        for pth, preach, lasts in cands:
            c_prefix, screened = cost.first_tier_for(chain, preach[1])
            for idx_t, bt in enumerate(later, 1):
                ri = preach[idx_t]
                c_prefix += ri * cost.sparse_for(bt, ri, screened)
            for hw, last in zip(hws, lasts):
                if last is None:
                    continue
                f = last[1]
                r_cost = cost.refine(f)
                if hw is not None and prices_dir:
                    d_cost = dbase + dlag * (2 * int(hw) * R + 1)
                    if has_last_sparse and f >= 0.05:
                        d_cost += dmfrac * cost.sparse(b_last, f)
                    d_cost = min(r_cost, d_cost)
                    r_cost = (1.0 - dfrac) * r_cost + dfrac * d_cost
                c = c_prefix + f * r_cost
                if has_feed:
                    c += cost.feed_delta(chain, preach + (f,), ntemplates, hw, band_forward)
                if best is None or c < best[0]:
                    best = (float(c), pth + (last[0],), preach + (f,), hw)
    else:
        for pth, preach, lasts in cands:
            for hw, last in zip(hws, lasts):
                if last is None:
                    continue
                th, reach = pth + (last[0],), preach + (last[1],)
                c = cost.chain_cost(chain, list(reach), hw) if cost is not None else _flop_cost(chain, list(reach), n)
                if has_feed:
                    # the change from the feed `block` was measured with; pick_stable's tie window
                    # is absolute-valued, so a change that takes a total below zero still compares
                    c += cost.feed_delta(chain, list(reach), ntemplates, hw, band_forward)
                if best is None or c < best[0]:
                    best = (float(c), th, reach, hw)
    if best is None:
        return None
    c, th, reach, hw = best
    if hasattr(cost, "first_tier_for"):
        q15 = bool(cost.first_tier_for(chain, reach[1])[1])
    elif hasattr(cost, "first_tier"):
        q15 = bool(cost.first_tier(chain[0], reach[1])[1])
    else:
        q15 = False
    missed = 0 if hw is None else dA.count_beyond(hw)
    search_info = dict(thresholds=th, reach=reach, halfwidth=hw, missed=missed, K=K)
    offs = (0,) * len(chain) if offsets is None else tuple(int(x) for x in offsets)
    if lazy_fit:
        return _LazyPlan(
            dict(chain=tuple(chain), offsets=offs, cost=c, q15=q15, search=search_info),
            (B, dB, th, hw, fd, noise, cols),
        )
    fit = _fit(B, dB, th, hw, fd)
    if fit is None:
        return None
    thresholds, halfwidth = fit
    return dict(chain=tuple(chain), offsets=offs, thresholds=thresholds,
                reach=tuple(_reach(noise, cols, thresholds)), halfwidth=halfwidth, cost=c,
                q15=q15, search=search_info)


#: plan_chain's searches by draws and chain (_prepare_chain), as long as the draws live.
_PREP_CACHE = OrderedDict()


def _prepare_chain(sig, noise, bands, chain, fd, n, snr, lags, far):
    """What plan_chain searches `chain` on before any price, from the draws alone: (cols, the
    search half, the fit half, the search budget K, the detections' distances (search half,
    fit half), the window allowance, the candidate half-widths), or None where fd cannot be
    resolved on these draws."""
    cols = [bands.index(b) for b in chain]
    A, B = _kept_halves(sig, bands, cols, chain, snr)
    K = int(round(float(fd) * (A.shape[0] + 1))) - 1      # the search half's budget, as the fit's
    fit_j = int(round(float(fd) * (B.shape[0] + 1)))
    if K < 0 or fit_j < 1 or fit_j > B.shape[0]:
        return None
    dA_all = dB_all = None
    allow = -1
    if lags is not None:
        # far: the signal draws are a narrower window's than the noise's (local_window), so
        # the refine's coarse maximum may be noise the draws do not hold (_distances)
        dA_all, dB_all = _distance_halves(sig, lags, bands, chain, snr, n, noise if far else None)
        allow = _gm.window_allowance(float(fd), A.shape[0], B.shape[0])
    return cols, A, B, K, dA_all, dB_all, allow, _all_halfwidths(dA_all, allow)


#: plan_chain prices a chain's candidates on a CostModel in C (_core.plan_best; the Python
#: loop in plan_chain is the reference, the same plan to the bit). False runs the Python one
#: (tests compare them).
_C_PRICING = True


def _pricing_tables(cost, chain, prices_dir, dbase, dlag, R, dfrac, dmfrac):
    """What _core.plan_best needs of a CostModel to price `chain`'s candidates as
    CostModel.first_tier_for, sparse_for and refine do: (first, later, refine, direct), or
    None where a table is longer than the routine holds.

    Parameters
    ----------
    cost : CostModel
        The model the chain is priced on.
    chain : sequence of int
        The chain's bands, at least two.
    prices_dir : bool
        Whether the model prices a direct refine for the chain.
    dbase, dlag, R, dfrac : float, float, int, float
        The direct refine's base price, its price per lag, the lags a half-width step
        covers and the fraction of blocks it applies to.
    dmfrac : float or None
        The share of the last tier's sparse price a direct refine adds, None for none.

    Returns
    -------
    tuple or None
        ``first``: (dense first tier's cost per pair, None or (the screen's cost per pair,
        its cost per pair passed, its excess table, TIE)); ``later``: per later tier (its
        sparse table, the one behind a screen); ``refine``: the refine table; ``direct``:
        None or (dbase, dlag, R, dfrac, None or (dmfrac, the last tier's sparse table)). A
        table is (log densities, values).
    """
    b = int(chain[0])
    ratio = (getattr(cost, "tier0_ratios", None) or {}).get(b, 1.0)
    sc = cost.screen.get(b)
    screen = None
    if sc is not None and sc["excess"]:
        screen = (sc["dense"] * ratio, sc["recheck"], _log_table(sc["excess"], "ratio"), TIE)
    later = []
    for bt in chain[1:]:
        plain = _log_table(cost._sparse[int(bt)], "cost")
        behind = cost.screen.get(int(bt))
        later.append((plain, _log_table(behind["sparse"], "cost")
                      if behind is not None and behind.get("sparse") else plain))
    refine = _log_table(cost._refine, "cost")
    direct = None
    if prices_dir:
        last = None if dmfrac is None else (dmfrac, _log_table(cost._sparse[int(chain[-1])], "cost"))
        direct = (float(dbase), float(dlag), int(R), float(dfrac), last)
    tables = [refine] + [t for pair in later for t in pair]
    tables += [screen[2]] if screen else []
    tables += [direct[4][1]] if direct and direct[4] else []
    if len(later) > 8 or any(len(t[0]) > 64 for t in tables):
        return None
    return (cost.dense[b] * ratio, screen), tuple(later), refine, direct


def _fit(B, dist, thresholds, hw, fd):
    """The plan's (thresholds, half-width) from the fit half B (M, k) of the detections, dist
    their _distances (None without a direct refine): the search's `thresholds` and half-width
    `hw`, every tier moved by one shift s, or None when M draws cannot place the budget.

    A detection passes every tier at shift s iff s <= its score, the smallest of its coarse
    maxima less their thresholds; one the window misses (dist > hw) is dismissed at any s. s
    is the j-th smallest score, j = round(fd (M + 1)) (gatemodel.fit_order), so j - 1 of B
    are dismissed, and on fresh draws the plan's dismissal is the j-th smallest of M uniforms
    (gatemodel.fit_order): its mean is fd whatever the search chose.

    Where the window alone misses j of B, the plan refines by transform instead (half-width
    None), which misses none, and the tiers take the whole budget. That branch is taken on B,
    so the plan is then not the j-th smallest uniform (fitted on the detections that showed
    the window failing, 17 such plans dismissed 1.14 fd on average; tools/split_bias.py,
    2026-10-29): the search offers only windows for which the branch has at most the
    probability the fit's tail leaves (gatemodel.window_allowance, at most 0.002), so a plan
    exceeds 1.25 fd with probability at most gatemodel._TAIL_SHARE with the branch included,
    and its mean moves by at most that probability times the branch's dismissal."""
    M = B.shape[0]
    j = int(round(float(fd) * (M + 1)))
    if j < 1 or j > M:
        return None
    th = np.asarray(thresholds, np.float64)
    score = B.score(th) if isinstance(B, _Columns) else (B - th).min(axis=1)
    if hw is not None:
        out = dist.mask_beyond(hw) if isinstance(dist, _Distances) else dist > hw
        if np.count_nonzero(out) >= j:
            hw = None
        else:
            score[out] = -np.inf
    s = float(np.partition(score, j - 1)[j - 1])
    return tuple(max(float(g) + s, 0.0) for g in th), hw


def _chain_candidates(S, noise, cols, K, prune, dead):
    """plan_chain's search on the search half's detections S (M, k), each tier's coarse
    maxima, with noise the noise blocks' maxima and cols the chain's columns of them: every
    split of the budget of K dismissed detections it considers, in its order, as (earlier
    thresholds, earlier reach, lasts). The earlier tiers' thresholds and the noise shares
    reaching each tier; and per set in `dead`, detections dismissed whatever the tiers (the
    direct refine's window's misses at one half-width), the last tier's threshold, the K-th
    from the budget, and the noise share it passes on, or None where the set leaves it no
    budget. A split the last tier has budget for under no set is left out."""
    M, k = S.shape
    # The earlier tiers' thresholds sit at index <= K of their sorted columns; the last
    # tier's is the rem-th smallest alive value with rem + dismissed <= K.
    if isinstance(S, _Columns):
        low = [S.smallest(i, K + 1) for i in range(k - 1)]
        last_order = S.smallest(k - 1, K + 1)
    else:
        low = [_smallest(S[:, i], K + 1) for i in range(k - 1)]
        last_order = _smallest(S[:, k - 1], K + 1)
    low_val = [S[o, i] for i, o in enumerate(low)]
    last_val = S[last_order, k - 1]
    out = []
    Nn = noise.shape[0]
    # The draws the earlier tiers dismiss, set and unset as the search descends and returns
    # (a copy per node was much of a search). Noise blocks below the lowest first-tier
    # threshold the search tries are dismissed on every branch: the search runs on the others
    # only, their chain columns contiguous, with alive masks over them. A reach is the alive
    # count over all Nn blocks, the same float as the mean of a full-length mask.
    marks = np.zeros(M, np.uint8)
    splits = _SPLIT
    if k > 1:
        firsts = [int(math.floor(a * K)) for a in splits]
        g0 = min((float(low_val[0][i]) for i in firsts if i >= 1), default=None)
        rows = noise[:, cols[0]] >= g0 if g0 is not None else np.zeros(Nn, bool)
        Nc = np.ascontiguousarray(noise[rows][:, cols].T)
    else:
        Nc = np.ascontiguousarray(noise[:, cols].T)

    def consider(prefix, ndead, alive, fracs):
        """Given thresholds for tiers 0..k-2, the last uses the remaining budget: ndead draws
        are dismissed (marked), alive the noise blocks passing every earlier tier (None: all
        of them), fracs those tiers' pass rates."""
        if prune and any(r > _USELESS_PASS for r in fracs):
            # choosing: a tier that passes most of its pairs on to ANOTHER TIER only adds its
            # own cost. (The last tier's pass rate into the refine is not judged here: at a
            # low snr every chain refines most pairs, and the cost already says so.)
            return
        lasts = []
        for D in dead:
            extra = D[marks[D] == 0]
            nd = ndead + int(extra.size)
            rem = K - nd
            at = None
            if 0 <= rem < M - nd:
                # the rem-th smallest last-tier value among draws not yet dismissed
                marks[extra] = 255
                pos = np.flatnonzero(marks[last_order] == 0)
                marks[extra] = 0
                at = int(pos[rem]) if pos.size > rem else None
            if at is None:
                lasts.append(None)
                continue
            g = float(last_val[at])
            hit = Nc[-1] >= g
            if alive is not None:
                hit &= alive
            lasts.append((g, int(np.count_nonzero(hit)) / Nn))
        if any(x is not None for x in lasts):
            out.append((tuple(prefix), (1.0,) + tuple(fracs), tuple(lasts)))

    def rec(i, prefix, remaining, ndead, alive, fracs):
        # tier i takes a share of the budget still unallocated; the last tier gets what is left
        if i == k - 1:
            consider(prefix, ndead, alive, fracs)
            return
        for a in splits:
            share = a * remaining
            idx = int(math.floor(share * K))
            if idx < 1:
                continue
            g = float(low_val[i][idx])
            # draws this tier dismisses: its column strictly below g
            cut = int(np.searchsorted(low_val[i], g, side="left"))
            cand = low[i][:cut]
            new = cand[marks[cand] == 0]
            marks[new] = i + 1
            an = Nc[i] >= g
            if alive is not None:
                an &= alive
            rec(i + 1, prefix + [g], remaining - share, ndead + int(new.size), an,
                fracs + [int(np.count_nonzero(an)) / Nn])
            marks[new] = 0

    if _C_SEARCH and all(len(o) == K + 1 for o in low) and len(last_order) == K + 1:
        shape = _shape_only(M, k) if isinstance(S, _Columns) else np.ascontiguousarray(S, np.float32)
        return _core.chain_candidates(shape, Nc, tuple(low),
                                      tuple(np.ascontiguousarray(v, np.float32) for v in low_val),
                                      np.ascontiguousarray(last_order, np.int64),
                                      np.ascontiguousarray(last_val, np.float32),
                                      tuple(float(a) for a in splits), int(K), int(Nn), bool(prune),
                                      float(_USELESS_PASS),
                                      tuple(np.ascontiguousarray(d, np.int64) for d in dead))
    rec(0, [], 1.0, 0, None, [])
    return out


#: _chain_candidates runs its search in C (_core.chain_candidates; the Python recursion above
#: it is the reference, identical candidates in the same order, ~1.3 ms a call of Python and
#: small array operations on dev2). False runs the Python one (tests compare them).
_C_SEARCH = True


#: A tier whose modelled noise pass rate exceeds this rejects too little to be worth running:
#: such a split is skipped, so a chain is priced only with thresholds that make every tier
#: gate. (Seen on Vulkan: a band-64 first tier ahead of 256 passing 4,337,904 of 4,337,904
#: pairs, at 2-3x the segment time of every other choice.)
_USELESS_PASS = 0.5


def canonical_order(chain):
    """Deterministic preference among tied chains: fewer tiers, then the smaller bands."""
    return (len(chain), tuple(chain))


def pick_stable(items, cost, key):
    """The canonical-first of the items whose cost is within TIE of the cheapest."""
    items = list(items)
    if not items:
        return None
    lo = min(cost(x) for x in items)
    return min((x for x in items if cost(x) <= lo + TIE * abs(lo)), key=key)


def _flop_cost(chain, reach, n):
    """Fallback when no measured table exists: transform-size proxy b log b per tier, n log n per refine."""
    c = chain[0] * math.log2(chain[0])
    for i in range(1, len(chain)):
        c += reach[i] * chain[i] * math.log2(chain[i])
    return c + reach[len(chain)] * n * math.log2(n)


_CHOICE_CACHE = OrderedDict()
_OFFSET_CACHE = OrderedDict()
#: choose_chain's template-count slot for a choice that holds at every count (its plans take
#: no priced feed), and the value it keeps under that key where the plans do take one.
_ANY_COUNT = "any count"
_COUNT_NEEDED = ("count needed",)


def _cached_band_offsets(p, sig_p, n, floor):
    """Return cached (k0_cand, usable_bands_list) for normalized profile `p` at `(n, floor)`."""
    off_key = (sig_p, int(n), int(floor))
    hit = _OFFSET_CACHE.get(off_key)
    if hit is not None:
        _OFFSET_CACHE.move_to_end(off_key)
        return hit
    c_bands = candidate_bands(n, floor)
    k0_cand = tuple(band_offset(p, n, b) for b in c_bands)
    bands = [b for b, k0 in zip(c_bands, k0_cand) if p[slice(*_band_slice(n, b, k0))].sum() > 0]
    res = (c_bands, k0_cand, bands)
    _cache_put(_OFFSET_CACHE, off_key, res)
    return res


def choose_chain(power, n, snr, fd, cost=None, max_tiers=3, floor=_MIN_BAND, nsim=None, window=None,
                 ntemplates=None, nsamp=None, tier0_clusters=None, first=None):
    """Price every chain and return (best, all plans sorted by cost): plan_chain's plans,
    ranked by their searched cost, (None, []) when none can be planned. nsamp: the
    detections to draw (default: model_draws'). first: price only the chains of two or more
    tiers whose first tier is this band (a bound on one tier-0 band needs no others).

    Cached like the draws it is built from: by profile signature, and reused for
    profiles within the cosine similarity gatemodel applies to them. A cost model with a feed
    (a GPU's) is priced per template count only where some chain's plan takes a priced feed;
    otherwise the choice is the same at every count and is kept and shared without it.
    """
    p = _norm_profile(power, n)
    win = None if window is None else (int(window[0]), int(window[1]))
    dsamp, dsim = model_draws(fd)
    nsamp = dsamp if nsamp is None else int(nsamp)
    nsim = dsim if nsim is None else int(nsim)
    if nsamp is None:
        return None, []          # the tail bound needs more detections than the model holds
    t0_single = bool(getattr(cost, "tier0_single", True))
    min_t0_len = 1 if t0_single else 2
    t0_map = {}
    if tier0_clusters and int(max_tiers) >= min_t0_len:
        for b, sp in tier0_clusters.items():
            a, lp = (sp.alpha, sp.lag_pad) if hasattr(sp, "alpha") else sp
            t0_map[int(b)] = (round(max(0.0, min(1.0, float(a))), 4), max(0, int(lp)))
    sig_p = _gm._profile_sig(p)
    c_bands, k0_cand, bands = _cached_band_offsets(p, sig_p, n, floor)
    extra = (k0_cand,) if any(k0_cand) else ()
    if t0_map:
        extra = extra + (("t0", tuple(sorted(t0_map.items()))),)
    head = (n, float(snr), float(fd), int(max_tiers), int(floor), int(nsim), int(nsamp), win,
            _cost_sig(cost))
    tail = (None if first is None else int(first),) + extra
    offsets_map = dict(zip(c_bands, k0_cand))
    count = None if not getattr(cost, "feed", None) else int(ntemplates or 0)
    if count:
        # A GPU's model prices a feed: a forward's per-block price spread over the template
        # count (CostModel.feed_delta), so a choice could depend on the count. Where every
        # chain's plan priced without the feed takes a forward priced 0 (on the Radeon 8060S
        # at n = 1024 the band forwards are 0 and only the full forward is priced), the feed
        # adds 0 to that plan's cost and nothing below it to any other candidate, so every
        # chain plans the same at any count: the choice, the ranking and every plan's cost are
        # the count's own. Such a choice is kept without the count and shared as a CPU's is,
        # by the similarity store too; a key whose plans take a priced feed is marked, and
        # its choices are made and kept per count.
        free_params = head + (_ANY_COUNT,) + tail
        free_key = (sig_p,) + free_params
        hit = _CHOICE_CACHE.get(free_key)
        if hit is None:
            unit, hit = _similar_get("choice", p, free_params)
            if hit is None:
                out = _choose_chain(p, n, snr, fd, cost, max_tiers, floor, nsim, win, None,
                                    nsamp, bands=bands, offsets_by_band=offsets_map,
                                    tier0_clusters=t0_map, first=first)
                band_forward = _config.get("MF_BAND_FORWARD")
                if all(cost.feed_delta(q["chain"], q["search"]["reach"], 1,
                                       q["search"]["halfwidth"], band_forward) == 0.0
                       for q in out[1]):
                    _similar_put("choice", unit, free_params, out)
                    hit = out
                else:
                    hit = _COUNT_NEEDED
            _cache_put(_CHOICE_CACHE, free_key, hit)
        else:
            _CHOICE_CACHE.move_to_end(free_key)
        if hit is not _COUNT_NEEDED:
            return hit
    params = head + (count,) + tail
    key = (sig_p,) + params
    hit = _CHOICE_CACHE.get(key)
    if hit is not None:
        _CHOICE_CACHE.move_to_end(key)
        return hit
    unit, hit = _similar_get("choice", p, params)
    if hit is not None:
        _cache_put(_CHOICE_CACHE, key, hit)
        return hit
    out = _choose_chain(p, n, snr, fd, cost, max_tiers, floor, nsim, win, ntemplates, nsamp,
                        bands=bands, offsets_by_band=offsets_map, tier0_clusters=t0_map,
                        first=first)
    _cache_put(_CHOICE_CACHE, key, out)
    _similar_put("choice", unit, params, out)
    return out


def _choose_chain(power, n, snr, fd, cost, max_tiers, floor, nsim, window, ntemplates=None,
                  nsamp=None, bands=None, offsets_by_band=None, tier0_clusters=None, first=None):
    p = _norm_profile(power, n)
    if bands is None:
        bands = usable_bands(p, n, floor)
    else:
        bands = sorted(int(b) for b in bands)
    if not bands:
        return None, []
    win = None if window is None else (int(window[0]), int(window[1]))
    nsamp = _gm._nsamp_for(fd) if nsamp is None else int(nsamp)
    if offsets_by_band is None:
        offsets_by_band = {b: band_offset(p, n, b) for b in bands}
    k0s = tuple(offsets_by_band[b] for b in bands)
    Fb = np.array([p[slice(*_band_slice(n, b, k0))].sum() for b, k0 in zip(bands, k0s)])
    if np.any(Fb <= 0):
        return None, []
    # Resolve the canonical profile in _SIGNAL_RECORDS so base and clustered draws share one realization
    sr_kw = {"k0s": k0s} if any(k0s) else {}
    p_base = (_law_profile(p, n, bands, float(snr), k0s)
              if _law_applies(n, local_window(p, n, bands, win))
              else _signal_records(p, n, bands, Fb, float(snr), nsamp, _SEED, **sr_kw)["p"])
    # the signals in the window local to them, the noise in the window searched (local_window)
    sig_win = local_window(p_base, n, bands, win)
    drawn = _signal_table(p_base, n, bands, snr, nsamp, window=sig_win, lags_too=True)
    if drawn is None:
        return None, []
    sig, lags = drawn
    noise = noise_block_maxima(p_base, n, bands, nsim=nsim, window=win)
    memo = ("choose", id(sig[0]), id(noise), n, float(snr), float(fd), tuple(bands), win,
            int(nsim), int(nsamp))

    # Build joint multi-tier signal & noise matrices per clustered Tier-0 band (matching chain_thresholds)
    t0_single = bool(getattr(cost, "tier0_single", True))
    min_t0_len = 1 if t0_single else 2
    t0_draws = {}
    if tier0_clusters and int(max_tiers) >= min_t0_len and len(bands) >= min_t0_len:
        t0_map = {}
        for b, sp in tier0_clusters.items():
            a, lp = (sp.alpha, sp.lag_pad) if hasattr(sp, "alpha") else sp
            t0_map[int(b)] = (round(max(0.0, min(1.0, float(a))), 4), max(0, int(lp)))
        cand_t0 = bands if t0_single else bands[:-1]
        t0_bands = [b for b in cand_t0 if b in t0_map]
        for b0 in t0_bands:
            a0, lp0 = t0_map[b0]
            al_b0 = tuple(a0 if b == b0 else 1.0 for b in bands)
            lp_b0 = tuple(lp0 if b == b0 else 0 for b in bands)
            drawn_b0 = _signal_table(p_base, n, bands, snr, nsamp, window=sig_win,
                                    lags_too=True, alphas=al_b0)
            if drawn_b0 is None:
                continue
            sig_b0, lags_b0 = drawn_b0
            noise_b0 = noise_block_maxima(p_base, n, bands, nsim=nsim, window=win,
                                          alphas=al_b0, lag_pads=lp_b0)
            memo_b0 = ("choose_t0", id(sig_b0[0]), id(noise_b0), b0, t0_map[b0], n, float(snr),
                       float(fd), tuple(bands), win, int(nsim), int(nsamp))
            t0_draws[b0] = (sig_b0, noise_b0, memo_b0, lags_b0)

    plans = []
    band_forward = _config.get("MF_BAND_FORWARD")       # read once for every chain's feed
    for chain in enumerate_chains(n, max_tiers, floor, bands=bands):
        if first is not None and (len(chain) < min_t0_len or chain[0] != first):
            continue
        offs = tuple(offsets_by_band[b] for b in chain)
        if len(chain) >= min_t0_len and chain[0] in t0_draws:
            sig_use, noise_use, memo_use, lags_use = t0_draws[chain[0]]
            if len(chain) == 1:
                lags_use = lags
                memo_use = memo_use + ("l1",)
        else:
            sig_use, noise_use, memo_use, lags_use = sig, noise, memo, lags
        pl = plan_chain(sig_use, noise_use, bands, list(chain), fd, cost, n, snr, prune=True,
                        ntemplates=ntemplates, memo=memo_use, lags=lags_use, lazy_fit=True, offsets=offs,
                        far=sig_win != ((0, int(n)) if win is None else win),
                        band_forward=band_forward)
        if pl is not None:
            plans.append(pl)
    plans.sort(key=lambda d: d["cost"])
    # Ties (within the calibration's process-to-process noise) go to the chain with fewer
    # tiers, then to the cheaper one on the calibration-free flop proxy: deterministic for a
    # given profile. A tier adds a pass over its survivors that the costs underprice: on the
    # 171,828-template BNS search (128, 256) and (128, 256, 512) priced within 1% of each
    # other and the two-tier chain's fine stage took 17% less CPU on Ivy Bridge, 18% less on
    # Haswell and 3-6% less on Zen 5; the flop proxy chose three tiers. Both are the searched
    # plans' (plan_chain), so the choice is made on the search half only.
    best = pick_stable(plans, lambda d: d["cost"],
                       lambda d: (len(d["chain"]), _flop_cost(d["chain"], d["search"]["reach"], n),
                                  d["chain"]))
    return best, plans


_PLAN_CACHE = OrderedDict()


#: calibrate_costs(n, ntemplates, ...) measures this machine's tier costs at transform size n
#: through the engine itself and returns the CostModel the chain choice prices with, kept in
#: MF_COST_FILE when it is set. It runs hierarchical plans, which sit above this module, so
#: it is matchedfilter._calibration.calibrate_costs (which documents the measurement), bound
#: to this name when that module loads (the package loads it): one function, one set of
#: defaults, wherever it is called from.
calibrate_costs = None


def chain_thresholds(power, n, snr, fd, chain, cost=None, floor=_MIN_BAND, nsim=None, window=None,
                     nsamp=None, tier0_cluster=None, tier1_cluster=None):
    """The plan (plan_chain's: thresholds, reach, the direct refine's half-width where the
    cost model prices one, cost) for one given chain under `power`, or None where it cannot
    be planned. nsamp: the detections to draw (default: model_draws').

    tier0_cluster / tier1_cluster: a _screeners.Tier0Cluster (or an (alpha, lag_pad) pair) whose
    retention and lag padding the signal draws and noise maxima of tier 0 / tier 1 are
    modelled with. A Tier-1 sub-screener bank applies only with a Tier-0 one and a chain of
    at least two tiers.

    Called whenever a plan's reference changes, inside the caller's filtering,
    so results are cached -- by profile signature, and reused for profiles
    within the same cosine similarity gatemodel applies to its draws.
    """
    p = _norm_profile(power, n)
    chain = tuple(int(b) for b in chain)
    win = None if window is None else (int(window[0]), int(window[1]))
    dsamp, dsim = model_draws(fd)
    nsamp = dsamp if nsamp is None else int(nsamp)
    nsim = dsim if nsim is None else int(nsim)
    if nsamp is None:
        return None              # the tail bound needs more detections than the model holds
    t0_single = bool(getattr(cost, "tier0_single", True))
    min_t0_len = 1 if t0_single else 2
    t0_cl = None
    if tier0_cluster is not None and len(chain) >= min_t0_len:
        a, lp = (tier0_cluster.alpha, tier0_cluster.lag_pad) if hasattr(tier0_cluster, "alpha") else tier0_cluster
        t0_cl = (round(max(0.0, min(1.0, float(a))), 4), max(0, int(lp)))
    t1_cl = None
    if t0_cl is not None and tier1_cluster is not None and len(chain) >= 2:
        a1, lp1 = ((tier1_cluster.alpha, tier1_cluster.lag_pad)
                   if hasattr(tier1_cluster, "alpha") else tier1_cluster)
        t1_cl = (round(max(0.0, min(1.0, float(a1))), 4), max(0, int(lp1)))
    sig_p = _gm._profile_sig(p)
    ch_off_key = ("chain", sig_p, int(n), chain)
    k0_chain = _OFFSET_CACHE.get(ch_off_key)
    if k0_chain is None:
        k0_chain = tuple(band_offset(p, n, b) for b in chain)
        _cache_put(_OFFSET_CACHE, ch_off_key, k0_chain)
    else:
        _OFFSET_CACHE.move_to_end(ch_off_key)
    extra = (k0_chain,) if any(k0_chain) else ()
    if t0_cl is not None:
        extra = extra + (("t0", t0_cl),)
    if t1_cl is not None:
        extra = extra + (("t1", t1_cl),)
    key = (sig_p, n, chain, float(snr), float(fd), win, int(nsim), int(nsamp), _cost_sig(cost), *extra)
    hit = _PLAN_CACHE.get(key)
    if hit is not None:
        _PLAN_CACHE.move_to_end(key)
        return hit
    sim_params = (n, chain, float(snr), float(fd), win, int(nsim), int(nsamp), _cost_sig(cost)) + extra
    unit, hit = _similar_get("plan", p, sim_params)
    if hit is not None:
        _cache_put(_PLAN_CACHE, key, hit)
        return hit
    _, k0_cand, bands = _cached_band_offsets(p, sig_p, n, floor)
    if not set(chain) <= set(bands):
        return None
    if t0_cl is not None:
        b0 = chain[0]
        c_bands, _, _ = _cached_band_offsets(p, sig_p, n, floor)
        off_map = dict(zip(c_bands, k0_cand))
        k0s = tuple(off_map[b] for b in bands)
        Fb = np.array([p[slice(*_band_slice(n, b, k0))].sum() for b, k0 in zip(bands, k0s)])
        sr_kw = {"k0s": k0s} if any(k0s) else {}
        p_base = (_law_profile(p, n, bands, float(snr), k0s)
                  if _law_applies(n, local_window(p, n, bands, window))
                  else _signal_records(p, n, bands, Fb, float(snr), nsamp, _SEED, **sr_kw)["p"])
        b1 = chain[1] if t1_cl is not None else None
        al_vec = tuple(t0_cl[0] if b == b0 else (t1_cl[0] if b == b1 else 1.0) for b in bands)
        lp_vec = tuple(t0_cl[1] if b == b0 else (t1_cl[1] if b == b1 else 0) for b in bands)
        sig_win = local_window(p_base, n, bands, window)
        drawn = _signal_table(p_base, n, bands, snr, nsamp, window=sig_win, lags_too=True, alphas=al_vec)
        if drawn is None:
            return None
        sig, lags = drawn
        if len(chain) == 1:
            base_drawn = _signal_table(p_base, n, bands, snr, nsamp, window=sig_win, lags_too=True)
            if base_drawn is not None:
                lags = base_drawn[1]
        noise = noise_block_maxima(p_base, n, bands, nsim=nsim, window=window,
                                   alphas=al_vec, lag_pads=lp_vec)
        memo = (("choose_t0", id(sig[0]), id(noise), chain[0], t0_cl, n, float(snr), float(fd),
                 tuple(bands), win, int(nsim), int(nsamp))
                + ((("t1", b1, t1_cl),) if t1_cl is not None else ())
                + (("l1",) if len(chain) == 1 else ()))
    else:
        sig_win = local_window(p, n, bands, window)
        drawn = _signal_table(p, n, bands, snr, nsamp, window=sig_win, lags_too=True)
        if drawn is None:
            return None
        sig, lags = drawn
        noise = noise_block_maxima(p, n, bands, nsim=nsim, window=window)
        memo = ("choose", id(sig[0]), id(noise), n, float(snr), float(fd), tuple(bands), win,
                int(nsim), int(nsamp))
    out = plan_chain(sig, noise, bands, list(chain), fd, cost, n, snr, memo=memo, lags=lags,
                     offsets=k0_chain, far=sig_win != ((0, int(n)) if win is None else win))
    _cache_put(_PLAN_CACHE, key, out)
    _similar_put("plan", unit, sim_params, out)
    return out


_BOUND_PRICE_CACHE = OrderedDict()


def _cost_model_nonneg(cost):
    if any(v < 0.0 for v in cost.dense.values()):
        return False
    if any(v < 0.0 for _, v in cost._refine):
        return False
    if any(v < 0.0 for rows in cost._sparse.values() for _, v in rows):
        return False
    if any(sc["dense"] < 0.0 or sc["recheck"] < 0.0
           or any(v < 0.0 for _, v in sc.get("sparse", ()))
           for sc in cost.screen.values()):
        return False
    t0r = getattr(cost, "tier0_ratios", None)
    if t0r and any(not (0.0 < r <= 1.0) for r in t0r.values()):
        return False
    dlag = getattr(cost, "direct_lag", None)
    if dlag is not None:
        dfrac = getattr(cost, "direct_frac", 1.0)
        if not (0.0 <= dfrac <= 1.0) or getattr(cost, "direct_multi_frac", 0.0) < 0.0:
            return False
        if dlag < 0.0 or getattr(cost, "direct_base", 0.0) + dlag < 0.0:
            return False
    return True


def pair_cost_lower_bound(power, n, snr, fd, cost, max_tiers=3, floor=_MIN_BAND, nsim=None,
                          window=None, ntemplates=None, nsamp=None, max_cost=None):
    """Analytic lower bound on `choose_chain(...)[0]["cost"]` without Monte Carlo draws.

    Parameters
    ----------
    power : array_like
        Nonnegative filter-output power profile of length `n`.
    n : int
        Transform block length.
    snr : float
        Target detection signal-to-noise ratio.
    fd : float
        False-dismissal budget.
    cost : CostModel
        Calibrated tier and refine cost model at block length `n`.
    max_tiers : int, optional
        Maximum number of coarse gate tiers to consider (default `3`).
    floor : int, optional
        Minimum candidate coarse band size (default `_MIN_BAND`).
    nsim : int, optional
        Number of noise blocks in the gate model (default `model_draws(fd)[1]`).
    window : tuple of int, optional
        Searched fine-lag window `(start, end)` within `[0, n)`, or `None` for the whole block.
    ntemplates : int, optional
        Template count for GPU feed pricing (`CostModel.feed_delta`), or `None`.
    nsamp : int, optional
        Number of signal detections in the gate model (default `model_draws(fd)[0]`).
    max_cost : float, optional
        Optional branch-and-bound threshold. When provided, evaluation stops early as soon
        as a sound lower bound at or below `max_cost` is certified, while still returning a
        valid lower bound on the minimum pair cost across all chains.

    Returns
    -------
    float or None
        Conservative lower bound on the best searched chain cost per `(block, template)` pair,
        or `None` when `cost` is not a nonnegative `CostModel` or `fd` cannot be resolved.
    """
    if not isinstance(cost, CostModel) or not cost._refine or not _cost_model_nonneg(cost):
        return None
    p = _norm_profile(power, n)
    win = None if window is None else (int(window[0]), int(window[1]))
    dsamp, dsim = model_draws(fd)
    nsamp = dsamp if nsamp is None else int(nsamp)
    nsim = dsim if nsim is None else int(nsim)
    if nsamp is None or nsamp < 2 or nsim < 1:
        return None
    m_search = (int(nsamp) + 1) // 2
    m_fit = int(nsamp) // 2
    k_bud = int(round(float(fd) * (m_search + 1))) - 1
    fit_j = int(round(float(fd) * (m_fit + 1)))
    span_chk = n if win is None else (win[1] - win[0])
    if k_bud < 0 or fit_j < 1 or fit_j > m_fit or span_chk < 1:
        return None

    sig_p = _gm._profile_sig(p)
    _, k0_cand, bands = _cached_band_offsets(p, sig_p, n, floor)
    if not bands:
        return None

    # Check exact cache for previously computed lower bounds
    extra = (k0_cand,) if any(k0_cand) else ()
    feed_nt = None if not getattr(cost, "feed", None) else int(ntemplates or 0)
    price_params = (int(n), float(snr), float(fd), int(max_tiers), int(floor), int(nsim),
                    int(nsamp), win, _cost_sig(cost), feed_nt) + extra
    price_key = (sig_p,) + price_params
    if price_key in _BOUND_PRICE_CACHE:
        _BOUND_PRICE_CACHE.move_to_end(price_key)
        return _BOUND_PRICE_CACHE[price_key]

    # Build piecewise-monotone knot grid for CostModel tables
    has_feed = bool(ntemplates and getattr(cost, "feed", None))
    band_forward = _config.get("MF_BAND_FORWARD") if has_feed else None
    base_knots = {0.0, 1e-12, 1e-6, 0.05 - 1e-12, 0.05, float(_USELESS_PASS), 1.0}
    for f_k, _ in cost._refine:
        base_knots.add(float(f_k))
    for rows in cost._sparse.values():
        for f_k, _ in rows:
            base_knots.add(float(f_k))
    for sc in cost.screen.values():
        for f_k, _ in sc["excess"]:
            base_knots.add(float(f_k))
        for f_k, _ in sc.get("sparse", ()):
            base_knots.add(float(f_k))
    knots_tup = tuple(sorted(f_k for f_k in base_knots if 0.0 <= f_k <= 1.0))

    ft_memo = {}
    t0r = getattr(cost, "tier0_ratios", None)

    def _first_tier_lb(b0, f_lo, f_hi, multi_tier=False):
        ratio = t0r[b0] if (multi_tier and t0r and b0 in t0r) else 1.0
        key_ft = (b0, ratio, f_lo, f_hi)
        hit = ft_memo.get(key_ft)
        if hit is not None:
            return hit
        c_dense = cost.dense[int(b0)] * ratio
        sc = cost.screen.get(int(b0))
        if sc is None or not sc["excess"]:
            res = (c_dense, None, c_dense)
            ft_memo[key_ft] = res
            return res
        sr_lo = cost.screen_reach(b0, f_lo)
        sr_hi = cost.screen_reach(b0, f_hi)
        cq_min = sc["dense"] * ratio + min(sr_lo, sr_hi) * sc["recheck"]
        cq_max = sc["dense"] * ratio + max(sr_lo, sr_hi) * sc["recheck"]
        scr_lb = cq_min if cq_min <= c_dense * (1.0 + TIE) else None
        flt_lb = c_dense if cq_max > c_dense * (1.0 + TIE) else None
        c_min = min(scr_lb if scr_lb is not None else float("inf"),
                    flt_lb if flt_lb is not None else float("inf"))
        res = (c_min, scr_lb, flt_lb)
        ft_memo[key_ft] = res
        return res

    def _feed_min(chain):
        if not has_feed:
            return 0.0
        vals = [cost.feed_delta(chain, [1.0] * len(chain) + [0.0], ntemplates, None, band_forward),
                cost.feed_delta(chain, [1.0] * len(chain) + [1.0], ntemplates, None, band_forward)]
        if cost.prices_direct(chain):
            vals.append(cost.feed_delta(chain, [1.0] * len(chain) + [1.0], ntemplates, 1,
                                        band_forward))
        return min(vals)

    # Zero-FFT tier-0 + feed floor across all candidate chains
    c0_floor_1 = {
        b: min(_first_tier_lb(b, knots_tup[i], knots_tup[i + 1], False)[0]
               for i in range(len(knots_tup) - 1))
        for b in bands
    }
    c0_floor_m = {
        b: min(_first_tier_lb(b, knots_tup[i], knots_tup[i + 1], True)[0]
               for i in range(len(knots_tup) - 1))
        for b in bands
    }
    all_chains = enumerate_chains(n, max_tiers, floor, bands=bands)
    if not all_chains:
        return None
    t0_single = bool(getattr(cost, "tier0_single", True))
    min_all_floor = min(
        (c0_floor_m[ch[0]] if (len(ch) > 1 or t0_single) else c0_floor_1[ch[0]]) + _feed_min(ch)
        for ch in all_chains
    )
    out_val = min_all_floor if math.isfinite(min_all_floor) else None
    if max_cost is None or (out_val is not None and out_val <= float(max_cost)):
        _cache_put(_BOUND_PRICE_CACHE, price_key, out_val)
    return out_val


def rebin_profile(fine, delta_f, data_rate, n):
    """A fine-grid output-power profile (spacing delta_f) on block size n's bins, normalised."""
    fine = np.asarray(fine, np.float64)
    ratio = max(int(round((data_rate / n) / float(delta_f))), 1)
    keep = (len(fine) // ratio) * ratio
    binned = fine[:keep].reshape(-1, ratio).sum(axis=1)
    out = np.zeros(n)
    k = min(len(binned), n // 2 + 1)
    out[:k] = binned[:k]
    tot = out.sum()
    return out / tot if tot > 0 else None


_PRICE_CACHE = OrderedDict()


