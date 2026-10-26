"""TimeDomainFilterBank: Ingest raw time-domain filters, dynamically partition by length,
automatically select optimal FFT block sizes, and filter continuous series."""

import math
from collections import OrderedDict
import collections
import collections.abc as _abc
import os
import time
from typing import Any, NamedTuple, Optional, Sequence, Union, Tuple, List, Dict
import sys
import threading
import weakref
import numpy as np
from . import _calibration, _config
from . import _trial
from ._choice import _AUTOTUNE_LOCK
from ._results import FilterResults, _EMPTY_FILTER_RESULTS  # noqa: F401  (public here)
from ._windows import _is_index, _normalize_windows, _window_layout  # noqa: F401
from ._windows import _merge_window_bins, _window_bin_phases
# The bank's layout planning lives in _layout; these names stay importable from here.
from ._layout import (_CORR_COSTS, _batch_target, _corr_block_cost,  # noqa: F401
                      _corr_block_costs, _corr_layout, _corr_measure, _corr_partition,
                      _partition_templates)
try:
    from . import _core
except ImportError:
    _core = None


def reference_profile(template, psd, f_low, f_high, delta_f) -> np.ndarray:
    """The expected signal power spectrum |h|^2 / S (float64) on the template's frequency
    grid, zero below f_low, above f_high (when positive) and where S is not positive: the
    profile set_reference takes, for a template and a noise spectrum."""
    h = np.asarray(template)
    S = np.asarray(psd)
    m = min(len(h), len(S))
    w = np.zeros(m, dtype=np.float64)
    good = S[:m] > 0
    w[good] = (np.abs(h[:m][good]) ** 2) / S[:m][good]
    f = np.arange(m) * float(delta_f)
    w[f < float(f_low)] = 0.0
    if f_high and float(f_high) > 0:
        w[f > float(f_high)] = 0.0
    return w


def _settle_device_writes():
    """Wait for GPU writes left in flight (correlate_series(wait=False)) before a host
    read. Device consumers are ordered on the GPU, so only host readers wait."""
    import sys
    for name in ('._mtlcompute', '._vkcompute', '._cudacompute'):
        mod = sys.modules.get(__package__ + name)
        if mod is not None and hasattr(mod, 'settle_all'):
            mod.settle_all()


class _RaggedSplit:
    """A ragged result's per-bin-count parts, in the order per-count calls give them: part i
    is the blocks with the i-th smallest bin count, with that many bins. Computed once per
    result (one pass over a sparse result's entries) and shared by every part."""

    def __init__(self, bc):
        bc = np.asarray(bc, np.int64)
        self.bc = bc
        self.us = [int(u) for u in np.unique(bc)]
        self.masks = [bc == u for u in self.us]
        self.rank = np.zeros(bc.size, np.int64)
        for m in self.masks:
            self.rank[m] = np.arange(int(m.sum()))

    def parts(self, r):
        from ._results import _SparsePeaks
        if not isinstance(r, _SparsePeaks):
            return [(r[0][m][:, :, :u], r[1][m][:, :, :u]) for m, u in zip(self.masks, self.us)]
        nt, nb = r.shape[1], r.shape[2]
        b, rest = np.divmod(r.flat, nt * nb)
        t, k = np.divmod(rest, nb)
        cb = self.bc[b]
        out = []
        for m, u in zip(self.masks, self.us):
            sel = (cb == u) & (k < u)
            out.append(_SparsePeaks((int(m.sum()), nt, u),
                                    (self.rank[b[sel]] * nt + t[sel]) * u + k[sel],
                                    r.idx[sel], r.val[sel]))
        return out

    def deferred(self, d):
        """One _Deferred per part of the deferred result d, sharing one split."""
        from ._results import _Deferred
        cell = []

        def part(i):
            if not cell:
                cell.append(self.parts(d.result()))
            return cell[0][i]
        return [_Deferred(lambda i=i: part(i)) for i in range(len(self.us))]


def _interval_mask(S: int, starts: np.ndarray, stops: np.ndarray) -> np.ndarray:
    """Boolean mask of length S that is True on the union of [starts, stops)."""
    edge = np.zeros(S + 1, dtype=np.int32)
    np.add.at(edge, np.clip(starts, 0, S), 1)
    np.add.at(edge, np.clip(stops, 0, S), -1)
    return np.cumsum(edge[:-1]) > 0


def _page_aligned_empty(shape, dtype=np.complex64, page: int = 16384) -> np.ndarray:
    """np.empty, starting on a page boundary: unified-memory GPUs can then write into it
    in place (see _correlate_group). Costs at most one page."""
    dtype = np.dtype(dtype)
    nbytes = int(np.prod(shape)) * dtype.itemsize
    raw = np.empty(nbytes + page, dtype=np.uint8)
    off = (-raw.ctypes.data) % page
    return raw[off:off + nbytes].view(dtype).reshape(shape)


def _interval_runs(S: int, starts: np.ndarray, stops: np.ndarray) -> np.ndarray:
    """The union of [starts, stops) clipped to [0, S), as sorted disjoint (K, 2) runs.

    What _interval_mask describes, without an S-long array: a 2^20-sample mask costs a
    cumsum and a pass per use, and the middle stage needed three per group per call.
    """
    a = np.clip(np.asarray(starts, np.int64), 0, S)
    b = np.clip(np.asarray(stops, np.int64), 0, S)
    keep = b > a
    a, b = a[keep], b[keep]
    if a.size == 0:
        return np.empty((0, 2), np.int64)
    order = np.argsort(a, kind="stable")
    a, b = a[order], np.maximum.accumulate(b[order])
    # A run starts where a start lies beyond every earlier stop.
    new = np.ones(a.size, bool)
    new[1:] = a[1:] > b[:-1]
    first = np.flatnonzero(new)
    last = np.append(first[1:] - 1, a.size - 1)
    return np.stack([a[first], b[last]], axis=1)


def _intersect_runs(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Intersection of two sorted disjoint run lists (a merge walk: the lists are a few runs,
    where numpy's per-call cost exceeds the loop's)."""
    out = []
    i = j = 0
    while i < len(x) and j < len(y):
        a, b = max(x[i, 0], y[j, 0]), min(x[i, 1], y[j, 1])
        if a < b:
            out.append((a, b))
        if x[i, 1] < y[j, 1]:
            i += 1
        else:
            j += 1
    return np.asarray(out, np.int64).reshape(-1, 2)


#: Joint trials (_trial) of banks. A bank's arms: DEFAULT (its smallest single block size); the
#: whole bank at its next single size and at the model's priced layout ("n=4096", "n=model":
#: _BLOCK_TRIAL_RANKS candidate layouts in all); its plans' other shortlisted
#: chains ("chain=n:..."), the _CHAIN_ARMS most often shortlisted; the Q15 screen both ways. Block
#: sizes are absolute candidates, smallest first: on a loaded Haswell node the model priced 4096
#: at 1.2x 2048 where it ran 1.6-1.95x, and fresh processes put 0-231 of test67's 323 banks on
#: 4096 (2026-10-25); ranked by its price, the candidates were its errors.
_BLOCK_TRIAL_RANKS = 3
_CHAIN_ARMS = 3


def _small_blocks_fit(device):
    """Whether 1024-sample blocks are a candidate for a CPU bank above 1024 Hz: when a 2048
    block's pair working set -- its data and template spectra and the intermediate, 3 x 8n
    bytes, 48 KB -- fills the L1D. Then the valid-fraction rule takes 1024 wherever it keeps
    half of each block valid. Flat banks only: the hierarchical engine prices its own block
    sizes (_choose_layout). Measured 2026-10-24 on test27's fine banks (257-297 taps; 1024
    against 2048): Haswell and Zen 3 (32 KB) -10% / -11%, Ivy Bridge (32 KB) -15%, Zen 5
    (48 KB) -9%, an M2 (128 KB) +2.6%, which keeps 2048. Above 1024 Hz the candidates had started
    at 2048 since a decimation scheme removed on 2026-10-05; no measurement chose that. GPU
    banks keep it."""
    from .device import parse as _parse_device
    try:
        if _parse_device(device).kind != "cpu":
            return False
    except (TypeError, ValueError):
        return False
    from . import _core
    l1d = int(_core.l1d_bytes())
    return bool(l1d) and 3 * 8 * 2048 >= l1d


def _trial_key(bank):
    """The joint trial a bank joins: its device, its block-size candidates (smallest single
    sizes, then "model"), its statistics. An arm means the same for every bank of the key, so
    the banks of a search pool their rounds into one trial and one lock."""
    return "bank|%s|%s|%g|%g" % (bank.device, ",".join(str(n) for n in bank._trial_cands),
                                 float(bank.threshold), float(bank.false_dismissal))


def _built(banks):
    """Recordings built so far by the GPU contexts of these banks' live layouts
    (Executor.built): a batch that built one paid setup, which is not what a trial ranks."""
    total = 0
    for bank in banks:
        for g in getattr(bank, '_groups', ()) or ():
            ctx = getattr(getattr(g, '_plan', None), '_gpu', None)     # built plans only
            if ctx is not None:
                total += ctx.built()
    return total


#: Set while a joint round replays a batch: the replays run as calls, not as rounds.
_REPLAYING = [False]


def _joint_round(jobs):
    """A round of the joint trial of every bank of this batch that is in one (_trial.run_round):
    each distinct configuration of the trial's live arms runs the whole batch, settled then
    timed, and the result is DEFAULT's. Banks whose trial has locked adopt the lock here. Returns
    the batch's results, or None when no bank of the batch is in an open trial."""
    from ._choice import _autotune_enabled
    from .device import parse as _parse_device
    if _REPLAYING[0] or not jobs or not _autotune_enabled():
        return None
    groups = {}
    for bank, _, kw in jobs:
        if (kw or {}).get("template_index") is not None or not getattr(bank, '_in_trial', False):
            continue
        key = _trial_key(bank)
        w = _trial.winner(key)
        if w is not None:
            bank._lock_arm(w)
            continue
        groups.setdefault(key, {})[id(bank)] = bank
    if not groups:
        return None
    work = sum(len(b.filters_f) * int(np.asarray(x).size) for b, x, kw in jobs
               if (kw or {}).get("template_index") is None)
    if work <= 0:
        return None
    gpu = any(_parse_device(b.device).kind == "gpu" for b, _, _ in jobs)
    import time
    from . import _record_cpu_trial

    def replay():
        return TimeDomainFilterBank.filter_series_many(jobs)

    def settle():
        # a GPU batch after a switch builds recordings and uploads: replayed until it builds
        # nothing more (at most three times), so the timed batch is steady state
        banks = [b for b, _, _ in jobs]
        before = _built(banks)
        replay()
        for _ in range(2):
            now = _built(banks)
            if now == before:
                break
            before = now
            replay()

    begin = time.perf_counter()
    result = None
    _REPLAYING[0] = True
    try:
        for key, byid in groups.items():
            banks = list(byid.values())
            for b in banks:
                b._prepare_arms()
            tr = _trial.trial(key, banks[0]._joint_arms)
            if len(tr.live()) < 2:
                with _AUTOTUNE_LOCK:
                    tr.choice.lock(_trial.DEFAULT)
            if tr.winner is not None:
                for b in banks:
                    b._lock_arm(tr.winner)
                continue
            result = _trial.run_round(tr, _BankArms.of(banks), replay, work,
                                      settle=settle if gpu else None)
    finally:
        _REPLAYING[0] = False
    if result is None:
        return None
    if not gpu:
        _record_cpu_trial(begin)
    return result


class _BankArms:
    """A bank as a joint-trial subject (_trial.run_round)."""

    def __init__(self, bank):
        self.bank = bank

    @classmethod
    def of(cls, banks):
        return [cls(b) for b in banks]

    def arm_config(self, label):
        return self.bank._arm_config(label)

    def use_arm(self, label):
        self.bank._use_arm(label)

    def lock_arm(self, label):
        self.bank._lock_arm(label)


def _max_tiers(device) -> int:
    """Gate tiers the device's hierarchical engine executes (HierarchicalFilter._MAX_TIERS)."""
    from . import HierarchicalFilter
    from .device import parse as _parse_device
    return min(3, HierarchicalFilter._MAX_TIERS[_parse_device(device).kind])


#: Identifies one filter_series_many batch to the plans it defers.
_BATCH_TOKEN = 0

def _single_key(key):
    """MF_COST_FILE key of a single-template device choice (device, n, block-count bucket)."""
    return "single-device|%s|%d|%d" % key


def _fuse_begin(jobs, trial):
    """Fuse this batch's submissions (_gpuexec.fused) or not, measured per set of GPU
    devices: (close or None, sample token or None for _fuse_end). Fusing interleaves every
    job's phases in shared command buffers -- worth +16% on an M2, -3 to -6% on an 8060S,
    nothing on a RENOIR (paired ladders, 2026-10-19) -- so neither is assumed. A batch is a
    sample only when no other trial is trying candidates in it and it builds no
    recording."""
    from ._choice import _autotune_enabled
    from .device import parse as _parse_device
    devs = tuple(sorted({"%s %s" % (d, d.name) for d in (
        _parse_device(b.device) for b, _, _ in jobs if getattr(b, "device", None) is not None)
        if d.kind == "gpu"}))
    if not devs:
        return None, None
    side, record = ("fused", None)
    if _autotune_enabled():
        from . import _choice
        side, record = _choice.choice("fused-batch", devs, ("fused", "unfused"),
                                      store_key="fused-batch|%s" % "+".join(devs),
                                      what="FUSE %s" % (devs,)).next()
    from ._gpuexec import fused
    close = fused() if side == "fused" else None
    work = sum(len(b.filters_f) * int(np.asarray(x).size) for b, x, kw in jobs
               if (kw or {}).get("template_index") is None)
    trying = bool(trial)
    if record is None or trying or work <= 0:
        return close, None
    import time
    banks = [b for b, _, _ in jobs]
    return close, (record, time.perf_counter(), work, banks, _built(banks))


def _fuse_end(tok):
    """Record a fusion sample (_fuse_begin), from the batch's submission to its last result."""
    if tok is None:
        return
    import time
    record, t0, work, banks, built = tok
    if _built(banks) == built:
        record((time.perf_counter() - t0) / work)


class _ReferenceCache:
    """Bounded derived profiles, invalidated when an input changes or dies.

    Setters compare an input with its saved values: an explicit setter must observe
    in-place edits. Filtering does no comparison or hashing. Weak references protect
    identity keys without retaining every PSD/template from a long search; the LRU
    also bounds snapshots and derived arrays while their inputs remain alive.
    """

    def __init__(self, max_entries=64, max_bytes=64 << 20):
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self.entries = OrderedDict()
        self.nbytes = 0
        self._version = 0
        self._lock = threading.RLock()

    def _remove(self, key, version=None):
        with self._lock:
            entry = self.entries.get(key)
            if entry is not None and (version is None or entry[0] == version):
                self.nbytes -= entry[4]
                del self.entries[key]

    def get(self, key, sources):
        # array_equal releases the GIL; another bank's setter must not evict the
        # entry between its comparison and the LRU update.
        with self._lock:
            entry = self.entries.get(key)
            if entry is None:
                return None
            _, refs, snapshots, _, _ = entry
            if (len(sources) != len(refs)
                    or any(ref() is not source or not np.array_equal(np.asarray(source), snapshot)
                           for ref, source, snapshot in zip(refs, sources, snapshots))):
                self._remove(key)
                return None
            self.entries.move_to_end(key)
            return entry

    def put(self, key, sources, value):
        with self._lock:
            self._remove(key)
            self._version += 1
            version = self._version
            try:
                refs = tuple(weakref.ref(source, lambda _, k=key, v=version: self._remove(k, v))
                             for source in sources)
            except TypeError:
                return None         # non-weakrefable inputs (e.g. lists) work uncached
            arrays = tuple(np.asarray(source) for source in sources)
            values = value.values() if isinstance(value, dict) else (value,)
            nbytes = sum(a.nbytes for a in arrays) + sum(
                a.nbytes for a in values if a is not None)
            if self.max_entries < 1 or nbytes > self.max_bytes:
                return None
            snapshots = tuple(a.copy() for a in arrays)
            while self.entries and (len(self.entries) >= self.max_entries
                                    or self.nbytes + nbytes > self.max_bytes):
                self._remove(next(iter(self.entries)))
            entry = (version, refs, snapshots, value, nbytes)
            self.entries[key] = entry
            self.nbytes += nbytes
            return entry


_REF_PROFILE_CACHE = _ReferenceCache()
_REF_BINNED_CACHE = _ReferenceCache()


class _TemplateGroup:
    """Internal container for a homogeneous batch of templates sharing an FFT size."""

    def __init__(self, plan, n, template_indices, c_bad, n_valid, orig_taps_max, device=None,
                 plan_factory=None, kind=None, spectra_source=None, row_source=None,
                 stored_bins=None):
        # A hierarchical plan is made up front (references and templates load into it); a flat or
        # correlation plan only when something first filters with it, so a bank kept for its
        # spectra and layout alone costs no plan memory.
        self._plan = plan
        self._plan_factory = plan_factory
        self.is_hier = plan_factory is None and type(plan).__name__ == 'HierarchicalFilter'
        self.kind = kind
        self._spectra_source = spectra_source
        self._row_source = row_source
        self.n = int(n)
        self._stored_bins = int(n if stored_bins is None else stored_bins)
        self.template_indices = np.asarray(template_indices, dtype=np.int64)
        self.c_bad = int(c_bad)
        self.n_valid = int(n_valid)
        self.orig_taps_max = int(orig_taps_max)
        self.device = device
        self.templates_loaded = False
        self._cached_layout: Optional[Tuple[Tuple[int, int, int], np.ndarray, np.ndarray, np.ndarray]] = None
        self._flat_plan: Optional[Any] = None
        self._corr_plan: Optional[Any] = None

    @property
    def spectra(self):
        """The spectra the group's plan holds, (T, stored bins): made from the group's taps
        whenever asked for (a plan loads them once; the group keeps none)."""
        return self._spectra_source()

    def full_spectra(self, rows=None):
        """Full n-bin spectra (not conjugated, not packed) of the group's templates, or of the
        local rows given: what an ungated plan is loaded with."""
        return self._row_source(rows)

    def load_templates(self, plan):
        """Load the group's spectra into plan, which reloads from the same source (rather than
        a copy of its own) if it is ever rebuilt."""
        if hasattr(plan, "set_template_source"):
            plan.set_template_source(self._spectra_source)
        plan.set_templates(self.spectra)

    @property
    def plan(self):
        if self._plan is None and self._plan_factory is not None:
            from . import CorrelationFilter
            plan = self._plan_factory()
            self.load_templates(plan)
            self.templates_loaded = True
            if isinstance(plan, CorrelationFilter):
                self._corr_plan = plan
            self._plan = plan
        return self._plan

    def get_flat_plan(self):
        from . import MatchedFilter, HierarchicalFilter
        if not isinstance(self.plan, HierarchicalFilter):
            return self.plan
        if self._flat_plan is None:
            fp = MatchedFilter(
                self.n, ndata=1, ntemplates=len(self.template_indices),
                device=self.device
            )
            fp.set_templates(self.full_spectra())
            self._flat_plan = fp
        return self._flat_plan

    def get_single_plan(self, ti: int, on_cpu: bool = False):
        """An ungated plan holding only local template ti (a few kept per group): what a
        single-template call needs, without building the group's whole ungated bank.
        on_cpu: the CPU's plan even for a GPU group (see TimeDomainFilterBank._single_device)."""
        from . import MatchedFilter
        cache = self.__dict__.setdefault('_single_plans', OrderedDict())
        plan = cache.get(int(ti))
        if plan is not None:
            cache.move_to_end(int(ti))
            return plan
        from .device import parse as _parse_device
        if _parse_device(self.device).kind == 'gpu' and not on_cpu:
            # A GPU plan owns a device context (~10 ms to create): keep one and load the
            # template into it. The caller runs the plan before asking for the next one.
            plan = self.__dict__.get('_single_gpu_plan')
            if self.__dict__.get('_single_gpu_ti') != int(ti):
                sp = self.full_spectra(slice(int(ti), int(ti) + 1))
                if plan is None:
                    plan = self._single_gpu_plan = MatchedFilter(self.n, ndata=1, ntemplates=1,
                                                                 device=self.device)
                # Calls deferred in a batch still read the current template: let them finish.
                plan._settle_deferred()
                plan.set_templates(np.ascontiguousarray(sp))
                self._single_gpu_ti = int(ti)
            return plan
        sp = self.full_spectra(slice(int(ti), int(ti) + 1))
        # 'cpu', not None: None means MF_DEVICE, which would move the CPU's own plan to a GPU.
        plan = MatchedFilter(self.n, ndata=1, ntemplates=1, device='cpu' if on_cpu else self.device)
        plan.set_templates(np.ascontiguousarray(sp))
        cache[int(ti)] = plan
        while len(cache) > 8:
            cache.popitem(last=False)
        return plan

    def get_correlation_plan(self):
        if self._corr_plan is None:
            from . import CorrelationFilter
            if self.kind == 'corr':
                self._corr_plan = self.plan
            else:
                cp = CorrelationFilter(
                    self.n, ndata=1, ntemplates=len(self.template_indices),
                    device=self.device, valid=(self.c_bad, self.n - self.c_bad)
                )
                cp.set_templates(self.full_spectra())
                self._corr_plan = cp
        return self._corr_plan


def _group_spectra(taps, counts, n, rate_ratio, analytic, rows=None, pack=False):
    """Spectra of a group's taps on n-sample blocks (T or len(rows), n), not conjugated; with
    pack, Hermitian-packed to n/2 bins with the Nyquist bin in DC's imaginary part (real taps)."""
    if rows is not None:
        taps, counts = taps[rows], counts[rows]
    spectra = np.zeros((len(counts), n), dtype=np.complex64)
    _tap_spectra(np.ascontiguousarray(taps), np.ascontiguousarray(counts), n, rate_ratio,
                 analytic, spectra)
    if not pack:
        return spectra
    K = n // 2
    packed = np.ascontiguousarray(spectra[:, :K])
    packed[:, 0] = spectra[:, 0].real + 1j * spectra[:, K].real
    return packed


class _Filters(_abc.Sequence):
    """filters_f, made when read: each template's conjugated full spectrum from its group's
    taps, so a bank holds no spectra of its own."""

    def __init__(self, template_map):
        self._map = template_map

    def __len__(self):
        return len(self._map)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return [self[j] for j in range(*i.indices(len(self)))]
        g, ti = self._map[i]
        return np.conj(g.full_spectra(slice(ti, ti + 1))[0])


def _tap_spectra(taps: np.ndarray, counts: np.ndarray, n: int, rate_ratio: float,
                 analytic: bool, out: np.ndarray) -> None:
    """Spectra of FIR taps on an n-sample data block, written into out (T, n).

    taps is (T, m) float32 -- or complex64, a quadrature filter (the analytic version of a
    real one) that turns a real series into the complex SNR -- with each row's first
    counts[i] samples valid. The centre tap is rolled to lag 0; with taps at a higher rate
    than the data (rate_ratio > 1) the spectrum is cut at the data Nyquist, at a lower rate
    it is zero-padded. Not conjugated: filters_f is the conjugate of this.
    """
    T, m = taps.shape
    cplx = np.iscomplexobj(taps)
    if rate_ratio == 1.0 and _core is not None and hasattr(_core, 'taps_to_spectra'):
        try:
            if cplx:
                _core.taps_to_spectra(np.ascontiguousarray(taps, np.complex64), counts, n, m, out, True)
            else:
                _core.taps_to_spectra(taps, counts, n, m, out)
            return
        except Exception:
            pass
    N_taps = int(round(n * rate_ratio))
    for row in range(T):
        cnt = int(counts[row])
        buf = np.zeros(N_taps, dtype=np.complex64 if cplx else np.float32)
        buf[:cnt] = taps[row, :cnt]
        # Center-tap circular roll alignment
        buf = np.roll(buf, -(cnt // 2))
        spec = np.fft.fft(buf).astype(np.complex64)
        if analytic and N_taps > n:
            # For an analytic series with positive-frequency support [f_low, f_high) < data Nyquist:
            # Positive-frequency bins [0, n) map directly to [0, f_Nyquist) without
            # negative-frequency mirroring.
            out[row] = spec[:n]
        elif N_taps > n:
            # Truncate frequencies above data Nyquist (preserving positive and negative bins)
            out[row] = 0
            out[row, :n // 2 + 1] = spec[:n // 2 + 1]
            neg_count = n - (n // 2 + 1)
            out[row, n // 2 + 1:] = spec[N_taps - neg_count:]
        elif N_taps < n:
            # Zero-pad frequencies above template Nyquist
            out[row] = 0
            half_taps = N_taps // 2
            out[row, :half_taps + 1] = spec[:half_taps + 1]
            neg_count = N_taps - (half_taps + 1)
            out[row, n - neg_count:] = spec[half_taps + 1:]
        else:
            out[row] = spec


def _host_copy(series, dtype):
    """np.ascontiguousarray(series, dtype), first waiting for GPU writes left in flight
    when it copies: the series may be a device row a correlation is still writing
    (correlate_series(wait=False)), read here by the host. No copy, no wait."""
    if not (isinstance(series, np.ndarray) and series.dtype == dtype
            and series.flags.c_contiguous):
        _settle_device_writes()
    return np.ascontiguousarray(series, dtype=dtype)


def _gpu_reads_real(gpu, n) -> bool:
    """Whether a GPU context's forward reads a real series at block length n."""
    return gpu is not None and n <= 65536


def _reads_real(plan) -> bool:
    """Whether the plan reads a real (float32) series itself: a hierarchical plan whose
    engine does (HierarchicalFilter._reads_real_series)."""
    from . import HierarchicalFilter
    return isinstance(plan, HierarchicalFilter) and plan._reads_real_series()


def _tap_dtype(taps) -> type:
    """complex64 for complex (quadrature) taps, float32 for real ones."""
    if isinstance(taps, (list, tuple)):
        return np.complex64 if any(np.iscomplexobj(t) for t in taps) else np.float32
    return np.complex64 if np.iscomplexobj(taps) else np.float32


def template_spectra(
    taps: np.ndarray,
    tap_counts: Optional[Sequence[int]],
    block_length: int,
    *,
    tap_sample_rate: float = 2048.0,
    data_sample_rate: float = 2048.0,
    analytic: bool = False,
    out: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Each template's filter on one block length, and the lags where it is valid.

    The filters are those TimeDomainFilterBank.filters_f holds for a block of
    block_length (conjugate spectrum, centre tap at lag 0); nothing else is
    built: no plans, no groups. With out (T, block_length) complex64, C-contiguous,
    they are written there and nothing is allocated for them.

    Returns (filters, valid): valid is (T, 2) int64, each template's [start, stop)
    of lags in a block whose correlation is not wrapped by its own taps.
    Raises if a template does not fit the block.
    """
    taps = np.ascontiguousarray(taps, dtype=_tap_dtype(taps))
    if taps.ndim == 1:
        taps = taps[None, :]
    T = taps.shape[0]
    counts = (np.full(T, taps.shape[1], dtype=np.int64) if tap_counts is None
              else np.ascontiguousarray(tap_counts, dtype=np.int64))
    if counts.shape != (T,):
        raise ValueError(f"tap_counts must have one entry per template ({T})")
    n = int(block_length)
    rate_ratio = float(tap_sample_rate) / float(data_sample_rate)
    valid = template_valid(counts, n, tap_sample_rate=tap_sample_rate,
                           data_sample_rate=data_sample_rate)
    if out is None:
        out = np.empty((T, n), dtype=np.complex64)
    elif (out.shape != (T, n) or out.dtype != np.complex64
          or not out.flags.c_contiguous):
        raise ValueError(f"out must be C-contiguous complex64 of shape ({T}, {n})")
    m = max(int(counts.max()), 1)
    _tap_spectra(taps[:, :m], counts, n, rate_ratio, analytic, out)
    np.conjugate(out, out=out)
    return out, valid


def template_valid(tap_counts, block_length, *, tap_sample_rate=2048.0,
                   data_sample_rate=2048.0):
    """The lags where each template's correlation on a block of block_length is valid (not
    wrapped by its own taps): (T, 2) int64 [start, stop), as template_spectra returns with
    the filters, from the tap counts alone. Raises if a template does not fit the block."""
    counts = np.ascontiguousarray(tap_counts, dtype=np.int64)
    n = int(block_length)
    rate_ratio = float(tap_sample_rate) / float(data_sample_rate)
    data_counts = np.ceil(counts / rate_ratio).astype(np.int64)
    start = np.ceil((counts // 2) / rate_ratio).astype(np.int64)
    stop = start + n - data_counts + 1
    if np.any(stop <= start):
        raise ValueError(f"block_length {n} is shorter than the longest filter "
                         f"({int(data_counts.max())} data samples)")
    return np.stack([start, stop], axis=1)


class TimeDomainFilterBank:
    """Filter bank that ingests raw time-domain filters and optimizes blocking dynamically.

    PyCBC passes raw time-domain FIR taps and sample rates.
    TimeDomainFilterBank clusters templates by length, chooses optimal FFT block sizes
    per cluster, handles rate conversion (zero-padding or Nyquist truncation), rolls center
    taps circularly, and executes overlap-save filtering returning trigger coordinates
    directly in continuous series coordinates.
    """

    def __init__(
        self,
        taps: Union[np.ndarray, Sequence[np.ndarray]],
        tap_counts: Optional[Sequence[int]] = None,
        *,
        tap_sample_rate: float = 2048.0,
        data_sample_rate: float = 2048.0,
        engine: str = 'hier',
        threshold: float = 5.0,
        false_dismissal: float = 0.001,
        first_stage_snr: float = 0.0,
        coarse_band_hz: Optional[float] = None,
        device: Optional[str] = None,
        max_batch_size: Optional[int] = None,
        fft_lengths: Optional[Sequence[int]] = None,
        reference: Optional[Any] = None,
        analytic: bool = False,
        bandlimited: bool = False,
        pack_templates: bool = False,
        binsize: Optional[int] = None,
        max_block_length: int = 8192,
    ):
        self.tap_sample_rate = float(tap_sample_rate)
        self.data_sample_rate = float(data_sample_rate)
        self.threshold = float(threshold)
        self.false_dismissal = float(false_dismissal)
        self.first_stage_snr = float(first_stage_snr)
        self.coarse_band_hz = coarse_band_hz
        self.device = device
        self.analytic = bool(analytic)
        # Off by default: halving the stored hierarchical templates (Hermitian
        # packing of real taps) is exact, but its refine builds the product in a
        # separate pass and measured slower than the fused full-template refine
        # (+14-25% refine cycles on Zen 5, +35-45% on Haswell, 2026-10-06).
        self.pack_templates = bool(pack_templates)
        self.max_batch_size = int(max_batch_size) if max_batch_size is not None else None

        mode = {'pycbc': 'flat', 'matchedfilter': 'flat',
                'matchedfilter-hierarchical': 'hier',
                'correlation': 'corr', 'corr': 'corr'}.get(engine, engine).lower()
        if bandlimited:
            mode = 'dif'
        self.engine = mode

        # Parse inputs. Complex taps are quadrature filters (complex_taps): the analytic
        # version of a real filter, applied to a REAL series to give the complex SNR -- the
        # same correlation (series against the conjugate tap spectrum) as real taps on an
        # analytic series, without the analytic series.
        self._raw_taps = None
        tdt = _tap_dtype(taps)
        self.complex_taps = tdt is np.complex64
        if isinstance(taps, (list, tuple)):
            n_templates = len(taps)
            if tap_counts is None:
                tap_counts = np.array([len(t) for t in taps], dtype=np.int64)
            else:
                tap_counts = np.asarray(tap_counts, dtype=np.int64)
            taps_list = [np.asarray(t, dtype=tdt) for t in taps]
        elif isinstance(taps, np.ndarray):
            if taps.ndim == 1:
                taps = taps[None, :]
            n_templates = taps.shape[0]
            if tap_counts is None:
                tap_counts = np.full(n_templates, taps.shape[1], dtype=np.int64)
            else:
                tap_counts = np.asarray(tap_counts, dtype=np.int64)
            taps_list = [taps[i, :tap_counts[i]].astype(tdt) for i in range(n_templates)]
            self._raw_taps = np.ascontiguousarray(taps, dtype=tdt)
        else:
            self._raw_taps = None
            raise TypeError("taps must be a numpy array or sequence of arrays")

        if len(tap_counts) != n_templates:
            raise ValueError(f"tap_counts length ({len(tap_counts)}) does not match n_templates ({n_templates})")

        self.n_templates = n_templates
        self.tap_counts = tap_counts
        self._taps_list = taps_list


        # Multi-rate scaling: ratio of tap sample rate to data sample rate
        self.rate_ratio = self.tap_sample_rate / self.data_sample_rate
        # Effective tap length in data samples
        self.effective_data_counts = np.ceil(self.tap_counts / self.rate_ratio).astype(np.int64)

        if fft_lengths is None:
            if (self.data_sample_rate <= 1024.0 or self.analytic
                    or (self.engine == 'flat' and _small_blocks_fit(device))):
                candidate_ns = (1024, 2048, 4096, 8192, 16384, 32768, 65536)
            else:
                candidate_ns = (2048, 4096, 8192, 16384, 32768, 65536)
        else:
            candidate_ns = tuple(sorted(int(n) for n in fft_lengths))

        # Peak granularity the caller asks for (samples); None keeps one peak per block.
        self.binsize = int(binsize) if binsize else None
        self._candidate_ns = candidate_ns
        self._legacy_layout = _partition_templates(
            self.effective_data_counts,
            max_batch=self.max_batch_size,
            candidate_ns=candidate_ns,
            engine=self.engine,
            device=self.device,
        )
        # Block size by cost. A stated peak granularity fixes the peak bins on each
        # window's grid, whatever the block size (bin phases). The first
        # fine-grid reference prices every candidate per length batch (gate model,
        # calibrated tier costs) and the groups are built at the cheapest. Without
        # one, or with lengths or a chain pinned, the valid-fraction rule stands.
        # max_block_length bounds the candidates: the caller pads its series and
        # guards its windows by the longest block, costs the model does not price.
        self._choose_n = (self.engine == 'hier' and self.binsize is not None and fft_lengths is None
                          and not (isinstance(coarse_band_hz, (tuple, list)) or (coarse_band_hz or 0) > 0))
        legacy_max = max(g[2] for g in self._legacy_layout[0]) if self._legacy_layout[0] else 0
        self._choice_ns = tuple(n for n in candidate_ns if n <= max(int(max_block_length), legacy_max))
        self._built: Optional[List[_TemplateGroup]] = None
        if self.engine == 'corr' and fft_lengths is None:
            self._legacy_layout = _corr_partition(self.effective_data_counts, candidate_ns,
                                                  self.max_batch_size, self.device)
        if not self._choose_n:
            self._build(*self._legacy_layout)
        if reference is not None:
            self.set_reference(reference)
            for g in self._groups:
                if g.is_hier and not g.templates_loaded:
                    g.load_templates(g.plan)
                    g.templates_loaded = True
        if not self._choose_n:
            self._taps_list = None
            self._raw_taps = None

    def _build(self, raw_groups, order) -> None:
        """Groups, spectra and plans for one partition of the bank."""
        from . import MatchedFilter, HierarchicalFilter
        n_templates = self.n_templates
        self._built = []
        self._built_layout = list(raw_groups)
        self._block_lengths_arr = np.zeros(n_templates, dtype=np.int64)

        for start_idx, end_idx, chosen_N, _ in raw_groups:
            tmpl_indices = order[start_idx:end_idx]
            T = len(tmpl_indices)
            chosen_N = int(chosen_N)

            orig_taps_max = int(np.max(self.tap_counts[tmpl_indices]))
            l_data_max = int(np.max(self.effective_data_counts[tmpl_indices]))
            c_bad = int(np.ceil((orig_taps_max // 2) / self.rate_ratio))
            n_valid = int(chosen_N - l_data_max + 1)

            if self._raw_taps is not None and self._raw_taps.shape[1] >= orig_taps_max:
                group_taps = np.ascontiguousarray(self._raw_taps[tmpl_indices, :orig_taps_max])
            else:
                group_taps = np.zeros((T, orig_taps_max), dtype=self._raw_taps.dtype
                                      if self._raw_taps is not None else
                                      (np.complex64 if self.complex_taps else np.float32))
                for r, g_idx in enumerate(tmpl_indices):
                    cnt = min(int(self.tap_counts[g_idx]), orig_taps_max)
                    group_taps[r, :cnt] = self._taps_list[g_idx][:cnt]
            group_counts = np.ascontiguousarray(self.tap_counts[tmpl_indices], dtype=np.int64)
            self._block_lengths_arr[tmpl_indices] = chosen_N

            # Create matchedfilter plan
            factory = None
            if self.engine == 'corr':
                from . import CorrelationFilter
                factory = (lambda n_=chosen_N, T_=T, v_=(c_bad, chosen_N - c_bad), dev=self.device:
                           CorrelationFilter(n_, ndata=1, ntemplates=T_, device=dev, valid=v_))
                plan = None
            elif self.engine == 'hier':
                # coarse_band_hz pins a chain (one band or a tuple of bands, in Hz);
                # otherwise the plan chooses its own from the reference.
                chain = None
                if isinstance(self.coarse_band_hz, (tuple, list)):
                    delta_f = self.data_sample_rate / chosen_N
                    chain = tuple(int(round(float(b) / delta_f)) for b in self.coarse_band_hz)
                elif self.coarse_band_hz is not None and self.coarse_band_hz > 0:
                    delta_f = self.data_sample_rate / chosen_N
                    chain = (int(round(self.coarse_band_hz / delta_f)),)
                plan = HierarchicalFilter(
                    chosen_N, ndata=1, ntemplates=T,
                    snr=self.threshold, fd=self.false_dismissal,
                    chain=chain, device=self.device,
                    # the lags each block's peak search covers: noise passes are priced over these.
                    # Rounded outward to n/32: the window only enters the cost model's noise pass
                    # rates (dismissal is set by the signal draws), it over-counts lags by <= ~3%,
                    # and groups of similar filter length then share one chain choice.
                    search_window=self._priced_window(c_bad, chosen_N),
                )
                # the bank's joint trial governs the plan (_use_arm, _lock_arm)
                plan._governed, plan._arm = True, getattr(self, '_bank_arm', _trial.DEFAULT)
                if self.first_stage_snr > 0:
                    plan.set_first_stage(self.first_stage_snr)
                if self.rate_ratio == 1.0 and hasattr(plan, "set_taps") and not self.complex_taps:
                    # The taps themselves, for the CPU's direct refine (survivors refined at
                    # the few lags their coarse tier points to, by direct correlation, where
                    # that is priced cheaper than a whole-block transform). At other rate
                    # ratios the spectra are cut or padded and the taps are not the filter.
                    plan.set_taps(group_taps, group_counts)
            else:
                factory = (lambda n_=chosen_N, T_=T, dev=self.device:
                           MatchedFilter(n_, ndata=1, ntemplates=T_, device=dev))
                plan = None
            pack = (self.engine == 'hier' and self.pack_templates and chosen_N >= 1024
                    and not self.complex_taps)      # Hermitian packing: real taps only
            if pack and hasattr(plan, 'set_hermitian'):
                plan.set_hermitian(True)

            # The group keeps its taps, not their spectra (T x n complex): those are made again
            # from the taps whenever a plan is loaded or a filter is asked for.
            src = dict(taps=group_taps, counts=group_counts, n=chosen_N,
                       rate_ratio=self.rate_ratio, analytic=self.analytic)
            grp = _TemplateGroup(
                plan=plan,
                n=chosen_N,
                template_indices=tmpl_indices,
                c_bad=c_bad,
                n_valid=n_valid,
                orig_taps_max=orig_taps_max,
                device=self.device,
                plan_factory=factory,
                kind=self.engine,
                spectra_source=lambda s=src, p=pack: _group_spectra(pack=p, **s),
                row_source=lambda rows, s=src: _group_spectra(rows=rows, **s),
                stored_bins=chosen_N // 2 if pack else chosen_N,
            )
            grp.templates_loaded = False
            self._built.append(grp)

        self._template_map = [None] * n_templates
        for g in self._built:
            for ti_local, global_idx in enumerate(g.template_indices):
                self._template_map[int(global_idx)] = (g, int(ti_local))
        self._filters_f_list = _Filters(self._template_map)
        self._current_ref_key = None

    def _input_series(self, series) -> np.ndarray:
        """The series as this bank filters it. A real series with complex (quadrature) taps
        stays real -- the middle output of a real-real-complex hierarchy -- and a CPU
        hierarchical plan transforms its blocks at half size; anything else is complex64."""
        if (self.complex_taps and self.engine == 'hier' and isinstance(series, np.ndarray)
                and not np.iscomplexobj(series)):
            if series.dtype == np.float32 and series.ndim == 1 and series.strides == (8,):
                return series       # one lane of a complex series (a packed pair), in place
            return _host_copy(series, np.float32)
        return _host_copy(series, np.complex64)

    @staticmethod
    def _priced_window(c_bad: int, n: int) -> Tuple[int, int]:
        q = max(n // 32, 1)
        lo = (int(c_bad) // q) * q
        return lo, int(n) - lo

    @property
    def _groups(self) -> List[_TemplateGroup]:
        # Asked for before a reference has chosen the block sizes: build by the
        # valid-fraction rule; the first fine-grid reference may still rebuild.
        if self._built is None:
            self._build(*self._legacy_layout)
        return self._built

    @property
    def max_block_length(self) -> int:
        """The longest block the bank uses, or may choose before its first reference."""
        if self._choose_n:
            return int(max(self._choice_ns + tuple(g[2] for g in self._legacy_layout[0])))
        return int(max((g.n for g in self._groups), default=0))

    def _choose_layout(self, fine: np.ndarray, delta_f: float, single_n: Optional[int] = None):
        """Partition with each length batch at its cheapest modelled block size -- or, with
        single_n, every batch at that one size (a joint trial's "n=" arm, _trial), unpriced."""
        from . import gatechain
        from ._choice import _log_autotune
        groups, order = self._legacy_layout
        counts = self.effective_data_counts[order]
        n_sorted = np.empty(len(order), dtype=np.int64)
        if single_n is not None:
            # every batch at one given size (a trial candidate, or a locked size): nothing to
            # price, the partition only
            n_sorted[:] = int(single_n)
            return _partition_templates(self.effective_data_counts, max_batch=self.max_batch_size,
                                        candidate_ns=self._candidate_ns, n_sorted=n_sorted)
        for i, j, n0, _ in groups:
            longest = int(counts[j - 1])
            taps_max = int(np.max(self.tap_counts[order[i:j]]))
            margin = int(np.ceil((taps_max // 2) / self.rate_ratio))
            ranked = _calibration.price_block_sizes(
                fine, delta_f, self.data_sample_rate, longest, margin, j - i,
                self.threshold, self.false_dismissal, [n for n in self._choice_ns if n > longest],
                max_tiers=_max_tiers(self.device), device=self.device)
            n_sorted[i:j] = ranked[0][1] if ranked else n0
            _log_autotune("BLOCK templates=%d longest=%d legacy n=%d -> n=%d  %s", j - i, longest, n0,
                          int(n_sorted[i]), " ".join("%d:%.3g" % (n, c) for c, n, _ in ranked))
        return _partition_templates(self.effective_data_counts, max_batch=self.max_batch_size,
                                    candidate_ns=self._candidate_ns, n_sorted=n_sorted)

    def _single_sizes(self):
        """The block sizes every batch of the bank can run at (above its longest data count),
        smallest first: the joint trial's block-size arms besides the model's layout."""
        groups, order = self._legacy_layout
        counts = self.effective_data_counts[order]
        longest = max((int(counts[j - 1]) for i, j, _, _ in groups), default=0)
        return sorted(int(n) for n in self._choice_ns if int(n) > longest)

    @property
    def filters_f(self) -> Sequence[np.ndarray]:
        """Sequence of frequency-domain filters (conjugated n-bin spectra), one per template,
        each made from the template's taps when read."""
        self._groups
        return self._filters_f_list

    @property
    def block_lengths(self) -> np.ndarray:
        """FFT block length assigned to each template."""
        self._groups
        return self._block_lengths_arr

    @property
    def groups(self) -> List[Dict]:
        """Summary of template partitions."""
        return [
            {
                'n': g.n,
                'count': len(g.template_indices),
                'template_indices': g.template_indices,
                'c_bad': g.c_bad,
                'n_valid': g.n_valid,
                'orig_taps_max': g.orig_taps_max,
                'efficiency': g.n_valid / g.n
            }
            for g in self._groups
        ]

    def get_filter_f(self, template_index: int) -> np.ndarray:
        """Return the frequency-domain filter for a specific template."""
        return self.filters_f[template_index]

    def get_block_length(self, template_index: int) -> int:
        """Return the FFT block length for a specific template."""
        return int(self.block_lengths[template_index])

    def set_reference(
        self,
        reference: Union[np.ndarray, Dict[int, np.ndarray]],
        delta_f: Optional[float] = None
    ) -> None:
        """Set reference SNR profile across all hierarchical groups.

        Parameters:
            reference:
                - Dict mapping block length N -> 1D reference array of length N, OR
                - 1D array of power spectrum w(f) on fine grid with frequency spacing delta_f, OR
                - 1D reference profile if all groups share the same block size.
            delta_f: Frequency resolution of fine grid (required when reference is w(f)).
        """
        if self._choose_n and not getattr(self, '_n_chosen', False):
            # The first reference settles the block sizes: by cost from a fine-grid
            # profile, else by the valid-fraction rule.
            if not isinstance(reference, dict) and delta_f is not None and float(delta_f) > 0:
                fine_ref = np.asarray(reference, dtype=np.float64)
                df = float(delta_f)
                # The bank's joint trial (_trial, _joint_round) decides block size, chains and
                # screen together on real calls, its arms the same labels for every bank of the
                # key (_trial_key). Its lock -- this process's or MF_COST_FILE's -- builds the
                # winner's layout alone, with no block-size pricing for an "n=" lock.
                from ._choice import _autotune_enabled
                on = _autotune_enabled()
                singles = self._single_sizes()[:_BLOCK_TRIAL_RANKS - 1] if on else []
                self._trial_cands = tuple(singles) + ("model",)
                w = _trial.winner(_trial_key(self)) if on else None
                self._bank_arm = w or _trial.DEFAULT
                self._in_trial = on and w is None
                kind, v = _trial.parse_arm(self._bank_arm)
                if w is not None:
                    # the lock's layout alone: its "n=" size, else the default (smallest) size
                    n = (None if v == "model" else v) if kind == "n" else (singles[0] if singles else None)
                    alts, sig = [self._choose_layout(fine_ref, df, single_n=n)], [n or "model"]
                else:
                    alts = [self._choose_layout(fine_ref, df, single_n=n) for n in singles]
                    alts.append(self._choose_layout(fine_ref, df))
                    sig = list(singles) + ["model"]
                self._candidate_sig = tuple(sig)
                # The candidate layouts are built now -- the taps are freed below. One with an
                # earlier one's partition shares its built layout. The bank starts on DEFAULT's,
                # the first (its smallest size).
                self._layouts = []
                for k, alt in enumerate(alts):
                    same = next((i for i in range(k) if alts[i][0] == alt[0]), None)
                    if same is not None:
                        self._layouts.append(self._layouts[same])
                        continue
                    if self._built is None or alt[0] != self._built_layout:
                        self._build(*alt)
                    self._layouts.append(self._snapshot())
                start = 0
                self._restore(self._layouts[start])
                self._layout_rank = start
                self.chosen_layout = [(int(e - b), int(n)) for b, e, n, _ in self._built_layout]
                self._layout_ref = (reference, delta_f)
                self._arms_ready = False
                if len(self._layouts) < 2:
                    self._layouts = None
            self._groups
            self._n_chosen = True
            self._taps_list = None
            self._raw_taps = None

        hier_ns = sorted({g.n for g in self._groups if g.is_hier})
        accepted = ("pass a dict {n: profile} with one length-n profile per block size, "
                    "or a fine-grid profile together with delta_f")
        if isinstance(reference, dict):
            missing = [n for n in hier_ns if n not in reference]
            if missing:
                raise ValueError(f"reference dict has no profile for hierarchical block size(s) "
                                 f"{missing} (bank block sizes: {hier_ns}); {accepted}")
            for g in self._groups:
                if g.is_hier:
                    g.plan.set_reference(reference[g.n])
            # Load templates as the other forms do; returning here left a bank
            # given its dict after construction with no templates at all.
            self._load_templates()
            self._current_ref_key = None
            self._state_version = getattr(self, '_state_version', 0) + 1
            return

        fine_df = float(delta_f) if delta_f is not None and float(delta_f) > 0 else None
        # All block sizes share one snapshot/comparison of the fine-grid input.
        # The sample rate matters: a frequency maps to different bins at another rate.
        cache_key = (id(reference), fine_df, self.data_sample_rate, tuple(hier_ns))
        hit = _REF_BINNED_CACHE.get(cache_key, (reference,))
        ref_key = (cache_key, hit[0]) if hit is not None else None
        if (ref_key is not None and getattr(self, '_current_ref_key', None) == ref_key
                and all(g.templates_loaded for g in self._groups if g.is_hier)):
            return

        if hit is not None:
            profiles = hit[3]
        else:
            ref_arr = np.asarray(reference, dtype=np.float64)
            if fine_df is not None:
                from .gatechain import rebin_profile
                profiles = {}
                for n in hier_ns:
                    ref_g = rebin_profile(ref_arr, fine_df, self.data_sample_rate, n)
                    profiles[n] = ref_g.astype(np.float32) if ref_g is not None else None
            else:
                # A per-bin profile without delta_f must cover every block size.
                wrong = [n for n in hier_ns if n != len(ref_arr)]
                if wrong:
                    raise ValueError(f"1-D reference of length {len(ref_arr)} does not match hierarchical "
                                     f"block size(s) {wrong} (bank block sizes: {hier_ns}); {accepted}")
                profiles = {n: ref_arr.astype(np.float32) for n in hier_ns}
            hit = _REF_BINNED_CACHE.put(cache_key, (reference,), profiles)
            ref_key = (cache_key, hit[0]) if hit is not None else None
        for g in self._groups:
            if g.is_hier and profiles[g.n] is not None:
                g.plan.set_reference(profiles[g.n])

        self._load_templates()
        self._current_ref_key = ref_key
        self._state_version = getattr(self, '_state_version', 0) + 1

    _LAYOUT_ATTRS = ('_built', '_built_layout', '_filters_f_list', '_block_lengths_arr',
                     '_template_map')

    def _snapshot(self):
        return {k: getattr(self, k, None) for k in self._LAYOUT_ATTRS}

    def _restore(self, snap):
        for k, v in snap.items():
            setattr(self, k, v)

    def _use_layout(self, rank: int) -> None:
        """Run on the rank-th candidate layout (built at the first reference). The plans differ,
        so the state version moves and recorded call plans are invalidated."""
        layouts = getattr(self, '_layouts', None)
        if not layouts or rank == getattr(self, '_layout_rank', 0) or rank >= len(layouts):
            return
        if layouts[rank].get('_built') is layouts[self._layout_rank].get('_built'):
            self._layout_rank = rank                  # the same partition: nothing to switch
            return
        self._layouts[self._layout_rank] = self._snapshot()
        self._restore(layouts[rank])
        self._layout_rank = rank
        self.chosen_layout = [(int(e - b), int(n)) for b, e, n, _ in self._built_layout]
        ref, df = self._layout_ref
        self._current_ref_key = None
        self.set_reference(ref, delta_f=df)          # this layout's groups get it, and templates
        self._state_version = getattr(self, '_state_version', 0) + 1

    def _lock_layout(self, rank: int) -> None:
        """Keep the rank-th layout and free the others, on the device too: the dropped
        layout's spectra and recordings sit in its GPU context's caches, which LRU evicts only
        under pressure -- on a small shared-memory GPU, after re-uploading live data."""
        self._use_layout(rank)
        # a layout another rank shares (the same partition) is the live one: compared by its
        # groups, which every snapshot of the partition holds (a snapshot is retaken on leaving)
        keep = self._layouts[rank].get('_built') if self._layouts else None
        dropped = [snap for snap in (self._layouts or []) if snap.get('_built') is not keep]
        self._layouts = None
        ctxs = {}
        for snap in dropped:
            for g in snap.get('_built') or []:
                ctx = getattr(getattr(g, 'plan', None), '_gpu', None)
                if ctx is not None:
                    ctxs[id(ctx)] = ctx
        for ctx in ctxs.values():
            ctx._drain()
            ctx._evict_all()                 # live layouts re-upload once, on their next call

    # ---- the bank's joint trial (_trial, _joint_round) ---------------------------------
    def _arm_rank(self, label) -> int:
        """The candidate layout an arm runs: its own for "n=" (a size, or the model's priced
        layout), else the default -- the first candidate, the smallest size."""
        sig = list(getattr(self, '_candidate_sig', ()) or ("model",))
        kind, v = _trial.parse_arm(label)
        want = v if kind == "n" else sig[0]
        return sig.index(want) if want in sig else 0

    def _layout_plans(self, rank):
        """The hierarchical plans of the rank-th candidate layout."""
        if self._layouts is None or rank == self._layout_rank:
            groups = self._built or ()
        else:
            groups = self._layouts[rank].get('_built') or ()
        return [g._plan for g in groups if g.is_hier and getattr(g, '_plan', None) is not None]

    def _prepare_arms(self) -> None:
        """Before the first round: every candidate layout given its reference and every plan
        its model choice (arm_config resolves against it)."""
        if getattr(self, '_arms_ready', True):
            return
        home = self._layout_rank
        for r in dict.fromkeys(range(len(self._layouts or [None]))):
            self._use_layout(r)
            for p in self._layout_plans(r):
                p.arm_config(_trial.DEFAULT)
        self._use_layout(home)
        self._arms_ready = True

    def _joint_arms(self):
        """The arms this bank proposes for its trial (_BLOCK_TRIAL_RANKS, _CHAIN_ARMS)."""
        arms = [_trial.DEFAULT] + [_trial.n_arm(n) for n in self._trial_cands[1:]]
        plans = self._layout_plans(self._arm_rank(_trial.DEFAULT))
        seen = collections.Counter()
        for p in plans:
            for c in getattr(p, '_shortlist', ()):
                if tuple(c) != p._model_chain:
                    seen[(p.n, tuple(c))] += 1
        arms += [_trial.chain_arm(n, c) for (n, c), _ in seen.most_common(_CHAIN_ARMS)]
        if any(p._q15_ok(p._model_chain) for p in plans if p._model_chain is not None):
            arms += [_trial.q15_arm(True), _trial.q15_arm(False)]
        return arms

    def _arm_config(self, label):
        """The configuration this bank runs for an arm: its layout (by partition) and what each
        of the layout's plans runs."""
        r = self._arm_rank(label)
        part = tuple((int(b), int(e), int(n)) for b, e, n, _ in
                     (self._layouts[r].get('_built_layout') if self._layouts else self._built_layout))
        return part, tuple(p.arm_config(label) for p in self._layout_plans(r))

    def _use_arm(self, label) -> None:
        """Run an arm from the next call on."""
        self._use_layout(self._arm_rank(label))
        for p in self._layout_plans(self._layout_rank):
            p.use_arm(label)
        self._bank_arm = str(label)

    def _lock_arm(self, label) -> None:
        """Run an arm from now on (the trial's lock): the other layouts and plans are freed."""
        if self._layouts is not None:
            self._lock_layout(self._arm_rank(label))
        for p in self._layout_plans(self._layout_rank):
            p.lock_arm(label)
        self._bank_arm, self._in_trial = str(label), False

    def _load_templates(self) -> None:
        for g in self._groups:
            if g.is_hier and not g.templates_loaded:
                g.load_templates(g.plan)
                g.templates_loaded = True

    def set_reference_from_template(
        self,
        stilde,
        psd,
        ref_template,
        f_high: Optional[float] = None
    ) -> None:
        """Compute closed-form reference SNR profile and set across all groups."""
        flo = float(getattr(ref_template, 'f_lower', 0.0) or 0.0)
        fhi = float(f_high or 0.0)
        df = float(stilde.delta_f)
        p_key = (id(ref_template), id(psd), flo, fhi, df)
        hit = _REF_PROFILE_CACHE.get(p_key, (ref_template, psd))
        w = hit[3] if hit is not None else None
        if w is None:
            w = reference_profile(ref_template, psd, flo, fhi, df)
            _REF_PROFILE_CACHE.put(p_key, (ref_template, psd), w)
        self.set_reference(w, delta_f=df)

    _window_layout = staticmethod(_window_layout)   # _windows._window_layout

    def filter_series(
        self,
        series: np.ndarray,
        windows=None,
        binsize: Optional[int] = None,
        threshold: Optional[float] = None,
        template_index: Optional[int] = None
    ) -> FilterResults:
        """Filter a continuous series across all template groups (or a specific template).

        Parameters:
            series: Continuous data series (e.g. complex reference SNR). The
                hierarchical engine's coarse gate is calibrated for an analytic
                (positive-frequency) series, which is what pycbc passes.
            windows: Analysis windows in series coordinates: None (the whole
                series), a slice, a sequence of slices or (start, stop) pairs,
                or a (K, 2) integer array. Python slice rules apply; overlapping
                or touching windows merge, so the result depends only on the
                union of samples. One call returns exactly what one call per
                (merged) window would, and a block that no window intersects
                is never computed. Each peak search stays inside its window.
                Padding for filter context is the caller's job.
            binsize: Samples per peak bin. Defaults to the bank's binsize, else the
                block size N (1 bin per block).
            threshold: Optional SNR threshold override. None uses bank threshold.
            template_index: Optional single template index to filter.

        Returns:
            FilterResults namedtuple with:
                template_indices: index into original input templates
                sample_indices: sample index in continuous series
                snr: complex peak SNR value
                block_starts: start sample of block containing each trigger
                block_lengths: FFT block length used for each trigger
        """
        ser = self._input_series(series)
        if ser.ndim != 1:
            raise ValueError("series must be a 1D array")
        S = len(ser)

        # A slice of a given series length normalises the same way every call (the
        # search's windows recur every segment): memoised, with its layout cache key.
        wkey = ((S, windows.start, windows.stop, windows.step)
                if type(windows) is slice else None)
        wmemo = self.__dict__.setdefault('_window_memo', {})
        hit = wmemo.get(wkey) if wkey is not None else None
        if hit is not None:
            W, cache_key = hit
        else:
            W = _normalize_windows(windows, S)
            cache_key = (S, W.tobytes())
            if wkey is not None:
                if len(wmemo) >= 64:
                    wmemo.clear()
                W.flags.writeable = False
                wmemo[wkey] = (W, cache_key)
        if W.shape[0] == 0:
            return _EMPTY_FILTER_RESULTS

        if template_index is not None:
            if template_index < 0 or template_index >= self.n_templates:
                raise IndexError(f"template_index {template_index} out of range [0, {self.n_templates})")

        eff_threshold = self.threshold if threshold is None else float(threshold)

        out_template_indices = []
        out_sample_indices = []
        out_snrs = []
        out_tstarts = []
        out_block_lens = []
        # A bin size the caller (or the bank) gives is each window's: its bins start at the
        # window's start, wherever the blocks fall (_window_bin_phases). A bin a block edge
        # cuts comes back as two partial bins, merged in build(). Without one, a bin is the
        # block's span (the documented default, one bin per block).
        aligned = binsize is not None or self.binsize is not None
        merge_bs = []


        if template_index is not None:
            if template_index < 0 or template_index >= self.n_templates:
                raise IndexError(f"template_index {template_index} out of range [0, {self.n_templates})")
            self._groups
            target_g, ti_local = self._template_map[template_index]
            work_items = [(target_g, (ti_local, 1))]
        else:
            work_items = [(g, None) for g in self._groups]

        def consume(aidx, aval, sub_starts, g, tmpl_arg, N):
            # aidx has shape (nblocks, ntemplates, nbins), or is a sparse result (aval None)
            if aval is None:
                sp = aidx
                if sp.flat.size == 0:
                    return
                nt_, nb_ = sp.shape[1], sp.shape[2]
                bi, rest = np.divmod(sp.flat, nt_ * nb_)
                ti = rest // nb_
                out_template_indices.append(np.full(bi.size, template_index, dtype=np.int64)
                                            if tmpl_arg is not None else g.template_indices[ti])
                out_sample_indices.append(sub_starts[bi] + sp.idx)
                out_snrs.append(sp.val)
                out_tstarts.append(sub_starts[bi])
                out_block_lens.append(np.full(bi.size, N, dtype=np.int64))
                return
            if tmpl_arg is not None:
                # Single template filtered (ntemplates == 1)
                if aidx.ndim == 3 and aidx.shape[2] == 1:
                    ii = aidx[:, 0, 0]
                    bi = np.nonzero(ii >= 0)[0]
                    if bi.size:
                        out_template_indices.append(np.full(bi.size, template_index, dtype=np.int64))
                        out_sample_indices.append(sub_starts[bi] + ii[bi])
                        out_snrs.append(aval[:, 0, 0][bi])
                        out_tstarts.append(sub_starts[bi])
                        out_block_lens.append(np.full(bi.size, N, dtype=np.int64))
                else:
                    bi, _, bini = np.nonzero(aidx >= 0)
                    if bi.size:
                        out_template_indices.append(np.full(bi.size, template_index, dtype=np.int64))
                        out_sample_indices.append(sub_starts[bi] + aidx[bi, 0, bini])
                        out_snrs.append(aval[bi, 0, bini])
                        out_tstarts.append(sub_starts[bi])
                        out_block_lens.append(np.full(bi.size, N, dtype=np.int64))
            else:
                if aidx.ndim == 3 and aidx.shape[2] == 1:
                    ii = aidx[:, :, 0]
                    bi, ti = np.nonzero(ii >= 0)
                    if bi.size:
                        out_template_indices.append(g.template_indices[ti])
                        out_sample_indices.append(sub_starts[bi] + ii[bi, ti])
                        out_snrs.append(aval[:, :, 0][bi, ti])
                        out_tstarts.append(sub_starts[bi])
                        out_block_lens.append(np.full(bi.size, N, dtype=np.int64))
                else:
                    bi, ti, bini = np.nonzero(aidx >= 0)
                    if bi.size:
                        out_template_indices.append(g.template_indices[ti])
                        out_sample_indices.append(sub_starts[bi] + aidx[bi, ti, bini])
                        out_snrs.append(aval[bi, ti, bini])
                        out_tstarts.append(sub_starts[bi])
                        out_block_lens.append(np.full(bi.size, N, dtype=np.int64))

        from ._results import _Deferred, _SparsePeaks
        defer = getattr(self, '_defer', False)
        pending = []
        for g, tmpl_arg in work_items:
            plan_templates = tmpl_arg
            trial = None
            if self.engine == 'hier' and tmpl_arg is not None:
                # one template ungated: a plan holding just it, not the group's whole ungated
                # bank -- on whichever device runs this call shape faster
                layout = g._cached_layout
                if layout is None or layout[0] != cache_key:
                    bstarts, bws, bwe = self._window_layout(g, W, S)
                    g._cached_layout = (cache_key, bstarts, bws, bwe)
                on_cpu, trial = self._single_device(g, g._cached_layout[1].size)
                active_plan = g.get_single_plan(tmpl_arg[0], on_cpu=on_cpu)
                plan_templates = None
            elif self.engine == 'hier' and (eff_threshold < self.threshold or eff_threshold <= 0.0):
                active_plan = g.get_flat_plan()
            else:
                active_plan = g.plan
            if getattr(active_plan, '_gpu', None) is None:
                # A host plan reads the series on the host: device writes left in flight
                # to it (correlate_series(wait=False)) must land first.
                _settle_device_writes()

            N = g.n
            layout = g._cached_layout
            if layout is None or layout[0] != cache_key:
                bstarts, bws, bwe = self._window_layout(g, W, S)
                g._cached_layout = (cache_key, bstarts, bws, bwe)
            else:
                _, bstarts, bws, bwe = layout

            if bstarts.size == 0:
                continue

            data_in = ser

            bs = int(binsize) if binsize is not None else (self.binsize or N)
            bph = None
            if aligned:
                pkey = ('_bin_phase', cache_key, bs)
                memo = g.__dict__.setdefault('_phase_memo', {})
                if pkey not in memo:
                    if len(memo) >= 16:
                        memo.clear()
                    ph = _window_bin_phases(W, bstarts, bws, bs)
                    if ph is not None:
                        # Every entry at the call's bin count: one with fewer bins starts its
                        # numbering whole bins earlier (empty bins before its window), so the
                        # bank is one call rather than one per bin count -- each call pays its
                        # setup and the Q15 screen's preparation again.
                        w_end = (np.minimum(bwe, N)
                                 if getattr(active_plan, '_bandlimited', False)
                                 and type(active_plan).__name__ != 'HierarchicalFilter'
                                 else bwe).astype(np.int64)
                        counts = (w_end - bws.astype(np.int64) + ph.astype(np.int64)
                                  + bs - 1) // bs
                        ph = (ph.astype(np.int64) + bs * (counts.max() - counts)).astype(np.uint32)
                    memo[pkey] = ph
                bph = memo[pkey]
                if bph is not None and bs not in merge_bs:
                    merge_bs.append(bs)
            # A repeat of a deferred call this group's plan has made before goes straight to
            # the plan's recorded call plan: no bin grouping, layout or key building. The
            # plan validates everything (layout identity, state, series memory, records);
            # on a miss the full call below runs and records again.
            fast_key = None
            if (self.engine == 'hier' and tmpl_arg is None and defer and trial is None
                    and active_plan is g.plan and getattr(active_plan, '_gpu', None) is not None
                    and hasattr(active_plan, '_fast_series')):
                fast_key = (cache_key, bs, eff_threshold)
                fast = g.__dict__.get('_fast_calls')
                hit = fast.get(fast_key) if fast else None
                if hit is not None and hit[0] is active_plan:
                    res = active_plan._fast_series(data_in, hit[1], bs, eff_threshold, defer,
                                                                   getattr(self, '_queue_offset', 0), True)
                    if res is not None:
                        if hit[2] is None:
                            pending.append((res, bstarts, g, tmpl_arg, N))
                        else:
                            split, starts_parts = hit[2]
                            for d, st_part in zip(split.deferred(res), starts_parts):
                                pending.append((d, st_part, g, tmpl_arg, N))
                        continue
            if bph is not None:
                # One call: the phases pad every entry to the same bin count (above).
                groups_bins = [(bstarts, bws, bwe, bph)]
            elif getattr(active_plan, '_bandlimited', False) and type(active_plan).__name__ != 'HierarchicalFilter':
                bs_k = max(1, bs // 2) if bs < N else g.n // 2
                wk_s = (bws // 2).astype(np.int64)
                w_end = np.minimum(bwe, N)
                wk_e = ((w_end + 1) // 2).astype(np.int64)
                bin_counts = np.maximum(1, (wk_e - wk_s + bs_k - 1) // bs_k)
                if len(bstarts) <= 1 or np.all(bin_counts == bin_counts[0]):
                    groups_bins = [(bstarts, bws, bwe, None)]
                else:
                    groups_bins = []
                    for u_cnt in np.unique(bin_counts):
                        mask = (bin_counts == u_cnt)
                        groups_bins.append((bstarts[mask], bws[mask], bwe[mask], None))
            elif bs >= N:
                groups_bins = [(bstarts, bws, bwe, None)]
            else:
                bin_counts = ((bwe - bws + bs - 1) // bs).astype(np.int64)
                if len(bstarts) <= 1 or np.all(bin_counts == bin_counts[0]):
                    groups_bins = [(bstarts, bws, bwe, None)]
                else:
                    groups_bins = []
                    for u_cnt in np.unique(bin_counts):
                        mask = (bin_counts == u_cnt)
                        groups_bins.append((bstarts[mask], bws[mask], bwe[mask], None))

            # Every bin count in one GPU submission where the backend can, instead of a
            # submission and a wait per count (see MatchedFilter._run_series_ragged).
            work = [(gb, None) for gb in groups_bins]
            if (len(groups_bins) > 1 and getattr(active_plan, '_gpu', None) is not None
                    and not getattr(active_plan, '_bandlimited', False)
                    and hasattr(active_plan, '_run_series_ragged')):
                if defer and trial is None:
                    active_plan._defer_series = defer
                    active_plan._gpu._queue_offset = getattr(self, '_queue_offset', 0)
                # A hierarchical ragged call reads back sparse, as its per-count calls would.
                sparse_ragged = type(active_plan).__name__ == 'HierarchicalFilter'
                if sparse_ragged:
                    active_plan._want_sparse = True
                try:
                    res = active_plan._run_series_ragged(
                        data_in, bstarts, bws, bwe, binsize=bs,
                        threshold=eff_threshold, templates=plan_templates,
                        **({} if bph is None else {'bin_phase': bph}))
                finally:
                    if defer and trial is None:
                        active_plan._defer_series = False
                    if sparse_ragged:
                        active_plan._want_sparse = False
                if res is not None:
                    # Split back into the per-count groups, in their order, so the result
                    # is the one per-count calls give (peak order included).
                    bc = ((bwe.astype(np.int64) - bws.astype(np.int64)
                           + (0 if bph is None else bph.astype(np.int64)) + bs - 1) // bs)
                    split = _RaggedSplit(bc)
                    subs = [(bstarts[m], bws[m], bwe[m], None if bph is None else bph[m])
                            for m in split.masks]
                    if fast_key is not None and isinstance(res, _Deferred):
                        g.__dict__.setdefault('_fast_calls', {})[fast_key] = (
                            active_plan, getattr(active_plan, '_last_layout', None),
                            (split, [sb[0] for sb in subs]))
                    parts = (split.deferred(res) if isinstance(res, _Deferred)
                             else split.parts(res))
                    work = list(zip(subs, parts))
            t_trial = time.perf_counter()
            for (sub_starts, sub_bws, sub_bwe, sub_ph), res in work:
                if res is None:
                    if defer and trial is None:
                        active_plan._defer_series = defer       # the batch's token
                        if getattr(active_plan, '_gpu', None) is not None:
                            active_plan._gpu._queue_offset = getattr(self, '_queue_offset', 0)
                    active_plan._want_sparse = True
                    run_in, run_starts = data_in, sub_starts
                    if data_in.dtype == np.float32 and not _reads_real(active_plan):
                        # A plan without a real-series path (the ungated single-template plan
                        # of a follow-up) widens to complex only the span its blocks read --
                        # not the whole series, which was 4.7 s of copies over a test27 job.
                        lo = int(sub_starts.min())
                        hi = min(S, int(sub_starts.max()) + N)
                        run_in = _host_copy(data_in[lo:hi], np.complex64)
                        run_starts = (sub_starts - lo).astype(sub_starts.dtype)
                    try:
                        res = active_plan.run_series(
                            run_in, run_starts, sub_bws, sub_bwe, binsize=bs,
                            threshold=eff_threshold, templates=plan_templates, raw=True,
                            **({} if sub_ph is None else {'bin_phase': sub_ph})
                        )
                    finally:
                        active_plan._want_sparse = False
                        if defer and trial is None:
                            active_plan._defer_series = False
                if isinstance(res, _Deferred):
                    pending.append((res, sub_starts, g, tmpl_arg, N))
                    if fast_key is not None and len(work) == 1:
                        g.__dict__.setdefault('_fast_calls', {})[fast_key] = (
                            active_plan, getattr(active_plan, '_last_layout', None), None)
                    continue
                aidx, aval = (res, None) if isinstance(res, _SparsePeaks) else res
                if getattr(active_plan, '_last_n_triggers', None) == 0:
                    continue
                if pending:
                    # Keep the call's order: parts already deferred are consumed at build().
                    # A synchronous result may be the plan's reused output buffers (_sbuf):
                    # held until build(), a later call of the same shape on this plan (the
                    # next follow-up of a batch) overwrote it, and this call returned that
                    # call's peaks. Own a copy.
                    if aval is not None:
                        aidx, aval = np.array(aidx), np.array(aval)
                    pending.append((_Deferred(lambda r=(aidx, aval): r), sub_starts, g,
                                    tmpl_arg, N))
                    continue
                consume(aidx, aval, sub_starts, g, tmpl_arg, N)
            if trial is not None:
                trial(time.perf_counter() - t_trial)

        def build():
            for d, sub_starts, g, tmpl_arg, N in pending:
                res = d.result()
                if not d.empty:
                    consume(*((res, None) if isinstance(res, _SparsePeaks) else res),
                            sub_starts, g, tmpl_arg, N)
            if merge_bs and out_template_indices:
                # Partial bins (a block edge inside a window bin) into their window bins.
                cols = [np.concatenate(c) for c in (out_template_indices, out_sample_indices,
                                                    out_snrs, out_tstarts, out_block_lens)]
                for bs_m in merge_bs:
                    cols = list(_merge_window_bins(W, bs_m, *cols))
                for lst, c in zip((out_template_indices, out_sample_indices, out_snrs,
                                   out_tstarts, out_block_lens), cols):
                    lst[:] = [c]
            if out_template_indices:
                if len(out_template_indices) == 1:
                    return FilterResults(
                        template_indices=out_template_indices[0].astype(np.int64, copy=False),
                        sample_indices=out_sample_indices[0].astype(np.int64, copy=False),
                        snr=out_snrs[0].astype(np.complex64, copy=False),
                        block_starts=out_tstarts[0].astype(np.int64, copy=False),
                        block_lengths=out_block_lens[0].astype(np.int64, copy=False),
                    )
                return FilterResults(
                    template_indices=np.concatenate(out_template_indices).astype(np.int64),
                    sample_indices=np.concatenate(out_sample_indices).astype(np.int64),
                    snr=np.concatenate(out_snrs).astype(np.complex64),
                    block_starts=np.concatenate(out_tstarts).astype(np.int64),
                    block_lengths=np.concatenate(out_block_lens).astype(np.int64),
                )
            else:
                return _EMPTY_FILTER_RESULTS

        return _Deferred(build) if pending else build()

    def empty_shared(self, shape, dtype=np.complex64, input=False):
        """An array in this bank's device memory (host-readable), for outputs a caller reuses:
        correlate_series(out=...) writes such an array in place, and a fine bank on the same
        device reads its rows in place. On a CPU bank, ordinary page-aligned memory.

        input=True: an input series the host rewrites before every call (a segment's data)
        and this bank reads in place: the backend may keep it in host memory mapped by the
        device rather than migrating it there and back each call."""
        self._groups
        for g in self._groups:
            plan = g.get_correlation_plan() if self.engine == 'corr' else g.plan
            gpu = getattr(plan, '_gpu', None)
            if gpu is not None:
                if input:
                    return gpu.empty_shared(tuple(shape), dtype, host_input=True)
                return gpu.empty_shared(tuple(shape), dtype, readback=True)
        return _page_aligned_empty(tuple(shape), dtype)

    def _single_device(self, g, nblocks):
        """(on_cpu, trial recorder or None) for a single-template call on group g.

        A follow-up filters one template over a few dozen blocks: a GPU call is then all
        fixed cost (submission, recording for its window, readback, the wake from idle),
        which a CPU core undercuts by far. Neither side is assumed: the first calls of a
        shape (device, block size, block count) alternate between the GPU plan and a CPU
        plan, timed synchronously, and the shared rule (gatechain.measured_choice) keeps one
        for every bank, and for later processes through MF_COST_FILE.
        MF_AUTOTUNE=0 keeps the bank's device.
        """
        from .device import parse as _parse_device
        from ._choice import _autotune_enabled
        import os
        force = self.__dict__.get("_single_force")
        if force is not None:                # a batch's measured side (_batch_device)
            return force == "cpu", None
        # MF_SINGLE_DEVICE=bank keeps every call on the bank's device: the pure-GPU path is a
        # product in its own right and is benchmarked as one (tools/ladder.py --pure).
        if (_parse_device(self.device).kind != 'gpu' or not _autotune_enabled()
                or _config.get("MF_SINGLE_DEVICE") == "bank"):
            return False, None
        from . import _choice
        key = (str(self.device), int(g.n), 1 << max(0, int(nblocks) - 1).bit_length())
        side, record = _choice.choice("single-device", key, ("gpu", "cpu"),
                                      store_key=_single_key(key),
                                      what="SINGLE %s n=%d blocks~%d" % key).next()
        return side == "cpu", record

    def _batch_device(self):
        """(side, record or None) for a batch's single-template jobs on this bank's GPU
        (filter_series_many): "gpu" runs them batched on the device (device follow-ups, one
        items submission per template group), "cpu" each call on a CPU plan. Measured per
        device (_choice), each batch timed from submission to its last result per
        block. The per-call choice (_single_device) times one call on its own, a dispatch a
        batch never makes: it once kept every batch off the device."""
        from .device import parse as _parse_device
        from ._choice import _autotune_enabled
        import os
        if (_parse_device(self.device).kind != 'gpu' or not _autotune_enabled()
                or _config.get("MF_SINGLE_DEVICE") == "bank"):
            return "gpu", None
        from . import _choice
        key = (str(self.device),)
        return _choice.choice("single-batch", key, ("gpu", "cpu"),
                              store_key="single-batch|%s" % key, what="BATCH %s" % key).next()

    @staticmethod
    def filter_series_many(jobs, wait=True):
        """Several filter_series calls as one batch: jobs is [(bank, series, kwargs)], the
        result the list of their FilterResults, identical to calling each in turn.

        On a GPU every call is submitted before any is collected, and each job's work goes to
        its own compute queue: the device runs banks concurrently and works on early banks
        while the host uploads later ones, and the host waits once rather than per call.
        On a CPU the calls simply run in order.

        wait=False returns, per job, an object whose result() gives its FilterResults: the GPU
        keeps working while the caller prepares the next batch (keeping the device busy keeps
        its clock up). The jobs' input series must not be overwritten until then. A later
        batch on the same banks first finishes whatever of this one it would overwrite.
        """
        from ._results import _Deferred
        global _BATCH_TOKEN
        paired = _joint_round(jobs)
        if paired is not None:
            return paired if wait else [_Deferred(lambda r=r: r) for r in paired]
        trial = _REPLAYING[0]           # a round's replay: the fused-batch choice does not sample
        _BATCH_TOKEN += 1
        # The deferred submissions may also be fused where a GPU driver batches them (Vulkan:
        # one command buffer runs every job's forward transforms, then every job's first
        # tier, ..., one barrier per phase; _gpuexec.fused): a measured choice.
        close, fuse = _fuse_begin(jobs, trial)
        out = [None] * len(jobs)
        # Single-template (follow-up) calls on a GPU bank, per template group: one forward
        # dispatch and one submission for all of them instead of a few submissions each.
        done = TimeDomainFilterBank._items_batch(jobs, out)
        try:
            for j, (bank, series, kw) in enumerate(jobs):
                if j in done:
                    continue
                bank._defer, bank._queue_offset = _BATCH_TOKEN, j
                try:
                    out[j] = bank.filter_series(series, **(kw or {}))
                finally:
                    bank._defer, bank._queue_offset = 0, 0
        finally:
            if close is not None:
                close()
        if not wait:
            res = [r if isinstance(r, _Deferred) else _Deferred(lambda r=r: r) for r in out]
            if fuse is not None:
                # a trial sample runs from submission to the batch's last result
                left = [len(res)]
                def wrap(d):
                    seen = [False]
                    def get(d=d):
                        v = d.result()
                        if not seen[0]:
                            seen[0] = True
                            left[0] -= 1
                            if left[0] == 0:
                                _fuse_end(fuse)
                        return v
                    return _Deferred(get)
                res = [wrap(d) for d in res]
            return res
        res = [r.result() if isinstance(r, _Deferred) else r for r in out]
        _fuse_end(fuse)
        return res

    @staticmethod
    def _items_batch(jobs, out):
        """Run eligible single-template GPU jobs of a batch together; returns their indices."""
        import os
        from .device import parse as _parse_device
        if not _config.get("MF_GPU_ITEMS"):
            return set()
        groups = {}
        side = record = device = None
        for j, (bank, series, kw) in enumerate(jobs):
            kw = kw or {}
            ti = kw.get("template_index")
            if (ti is None or bank.engine != 'hier' or _parse_device(bank.device).kind != 'gpu'
                    or set(kw) - {"windows", "binsize", "threshold", "template_index"}):
                continue
            ser = series                     # widened only for the items path, below
            S = len(ser)
            W = _normalize_windows(kw.get("windows"), S)
            bank._groups
            g, ti_local = bank._template_map[ti]
            bs = int(kw["binsize"]) if kw.get("binsize") is not None else (bank.binsize or g.n)
            if bs >= g.n or W.shape[0] == 0:
                continue
            # Where the batch runs: one measured side per device (_batch_device); a batch's
            # jobs on another device run per call.
            if side is None:
                device = str(bank.device)
                side, record = bank._batch_device()
            elif str(bank.device) != device:
                continue
            thr = bank.threshold if kw.get("threshold") is None else float(kw["threshold"])
            bstarts, bws, bwe = bank._window_layout(g, W, S)
            if bstarts.size == 0:
                continue
            # The window's bins (filter_series): each block's phase on its window's grid.
            ph = _window_bin_phases(W, bstarts, bws, bs)
            groups.setdefault((id(bank), id(g), bs, thr), []).append(
                (j, bank, g, ser, bstarts, bws, bwe, ti_local, ti, W, ph))
        done = set()
        if not groups:
            return done
        import time
        blocks = max(1, sum(m[4].size for members in groups.values() for m in members))
        eligible = {m[0] for members in groups.values() for m in members}
        t0 = time.perf_counter()
        if side == "cpu":
            for members in groups.values():
                for j, bank, *_ in members:
                    bank._single_force = "cpu"
                    try:
                        out[j] = bank.filter_series(jobs[j][1], **(jobs[j][2] or {}))
                    finally:
                        del bank._single_force
                    done.add(j)
            if record is not None:
                record((time.perf_counter() - t0) / blocks)
            return done
        # Threshold-0 follow-ups: every group's items as listed entries, all in one
        # submission (_gpuhost.submit_followups). None (past what the device path takes):
        # the per-group path below.
        if _config.get("MF_DEVICE_FOLLOWUPS"):
            fast = sorted(m[0] for (_, _, _, thr), members in groups.items() if thr == 0.0
                          for m in members)
            if fast:
                from ._gpuhost import submit_followups
                collect = submit_followups([jobs[j] for j in fast])
                if collect is not None:
                    # Submitted, not waited on: each job's result is read when asked for, so a
                    # caller collecting later (filter_series_many(wait=False)) never waits here.
                    from ._results import _Deferred
                    for i, j in enumerate(fast):
                        out[j] = _Deferred(lambda c=collect, i=i: c()[i])
                        done.add(j)
                    groups = {k: v for k, v in groups.items() if k[3] != 0.0}
                    if record is not None:
                        collect()             # a trial sample runs to the batch's last result
        # Submit every template group's items, then collect: a backend that can leaves each
        # submission in flight (wait=False), so the device runs them back to back.
        submitted = []
        for (_, _, bs, thr), members in groups.items():
            g = members[0][2]
            plan = g.get_flat_plan()
            res = plan._items_gpu([(_host_copy(ser, np.complex64), st, ws, we, tl, ph)
                                   for _, _, _, ser, st, ws, we, tl, _, _, ph in members],
                                  bs, thr, wait=False) if hasattr(plan, "_items_gpu") else None
            if res is not None:
                submitted.append((bs, members, res))
        for bs, members, res in submitted:
            res = res()
            for (j, bank, g, ser, st, ws, we, tl, ti, W, ph), (idx, val) in zip(members, res):
                lists = ([], [], [], [], [])
                if ph is None:
                    # Peaks in the order one call per bin count gives them.
                    counts = ((we - ws + bs - 1) // bs).astype(np.int64)
                    for u in np.unique(counts):
                        m = counts == u
                        _consume_into(lists, idx[m][:, :, :u], val[m][:, :, :u], st[m], g,
                                      (tl, 1), g.n, ti)
                else:
                    # A phased window is one filter_series call: peaks by block, then bin
                    # (bins a block does not have are empty).
                    _consume_into(lists, idx, val, st, g, (tl, 1), g.n, ti)
                res_j = _results_from(lists)
                if ph is not None:
                    # Partial bins (a block edge inside a window bin) into their window bins.
                    res_j = FilterResults(*_merge_window_bins(W, bs, *res_j))
                out[j] = res_j
                done.add(j)
        if record is not None and eligible <= done:
            record((time.perf_counter() - t0) / blocks)   # all on the device: a sample
        return done

    @staticmethod
    def _block_coverage(S: int, st: np.ndarray, lo: int, hi: int) -> np.ndarray:
        """Runs of samples written by blocks starting at st, each valid over [st+lo, st+hi)."""
        b0 = st.astype(np.int64) + lo
        return _interval_runs(S, b0, np.minimum(b0 + (hi - lo), S))

    def _correlate_group(self, g: "_TemplateGroup", ser: np.ndarray, st: np.ndarray,
                         t0: int, nt: int, dest: np.ndarray, bounds=None) -> None:
        """Correlate rows [t0, t0+nt) of group g over blocks st into dest (nt, S).

        Writes only the samples the blocks cover; leaves the rest of dest alone. On the CPU,
        bounds (nblocks, 2) narrows what block b writes to [st[b]+bounds[b,0],
        st[b]+bounds[b,1]) within its valid span (the block is computed the same; only its
        copy-out is shorter).
        The GPU path cannot write into caller memory, so it computes into a
        cached shared workspace and copies the covered samples out.  Mirrors
        what CorrelationFilter.run_series does before touching the execution
        layer, so the plan's invariants hold without going through it."""
        if st.size == 0:
            return
        cplan = g.get_correlation_plan()
        S = ser.size
        cplan._require_templates(t0, nt)
        cplan._dataset = False
        cplan._data_ready = set()
        lo, hi = cplan.valid
        if cplan._gpu is None:
            ep = cplan._continuous_plan()
            run = (ep.correlate_series_continuous_real if ser.dtype == np.float32
                   and hasattr(ep, "correlate_series_continuous_real")
                   else ep.correlate_series_continuous)
            if run is ep.correlate_series_continuous and ser.dtype != np.complex64:
                ser = _host_copy(ser, np.complex64)
            bnd = bounds
            if dest.flags.c_contiguous and dest.flags.writeable:
                run(ser, st, lo, hi, t0, nt, dest, bnd)
            else:
                tmp = np.empty((nt, S), dtype=np.complex64)
                run(ser, st, lo, hi, t0, nt, tmp, bnd)
                if bounds is None:
                    runs = self._block_coverage(S, st, lo, hi)
                else:
                    s64, bnd64 = st.astype(np.int64), bounds.astype(np.int64)
                    runs = _interval_runs(S, s64 + bnd64[:, 0], s64 + bnd64[:, 1])
                for a, b in runs:
                    dest[:, a:b] = tmp[:, a:b]                # see below
            return
        if ser.dtype != np.complex64 and not _gpu_reads_real(cplan._gpu, g.n):
            ser = _host_copy(ser, np.complex64)   # this plan reads complex
        # Unified memory (Metal): write straight into dest, and read the series where it
        # is. A page-aligned destination needs no workspace and no copy-out.
        view = getattr(cplan._gpu, 'host_view', None)
        out_owner = view(dest) if view is not None else None
        if out_owner is not None:
            ser_owner = view(ser) if ser.flags.writeable else None
            try:
                cplan._continuous_gpu(ser, st, t0, nt, dest)
            finally:
                del ser_owner, out_owner
            return
        # A destination in device memory on this device (a caller's reused buffer) is
        # written in place: no workspace, no copy-out.
        from ._shared import shared_view
        in_place = shared_view(dest, cplan._gpu)
        if dest.flags.c_contiguous and in_place is not None:
            # A backend that zeroes on the device also finishes this work there
            # (zero_columns_done in _correlate_windows): leave it in flight meanwhile.
            cplan._continuous_gpu(ser, st, t0, nt, dest, defer=True)
            return
        shape = (nt, S)
        ws = getattr(g, '_corr_workspace', None)
        if ws is None or ws.shape != shape:
            nbytes = nt * S * np.dtype(np.complex64).itemsize
            if nbytes > cplan._max_auto_output_bytes:
                raise ValueError("continuous correlation needs %d bytes of output; "
                                 "select fewer templates or a shorter series" % nbytes)
            ws = cplan._gpu.empty_shared(shape, readback=True)
            g._corr_workspace = ws
        cplan._continuous_gpu(ser, st, t0, nt, ws)
        # Not dest[:, cover] = ws[:, cover]: boolean indexing along axis 1 walks the rows
        # column by column, and with rows a power of two apart (2^20 samples = 8 MiB) every
        # access lands in one cache set -- 16 rows fit, 17+ thrash it (16 -> 24 templates
        # took 70 ms -> 2.1 s). Copying the covered runs row by row is a plain memcpy per
        # row, 2.6x faster again than copyto with a broadcast mask (4.6 ms against 12.1 ms
        # for 27 rows on an M2), and builds no S-long mask.
        for a, b in self._block_coverage(S, st, lo, hi):
            dest[:, a:b] = ws[:, a:b]

    def _add_corr_work(self, n, d):
        """Middle-stage work counters (matchedfilter._roofline), per block length n."""
        wk = self.__dict__.setdefault('_corr_work', {}).setdefault(
            n, dict(blocks=0, pairs=0, out_samples=0, tmpl_values=0))
        for k, v in d.items():
            wk[k] += v

    def _add_corr_in(self, samples):
        self._corr_in_samples = getattr(self, '_corr_in_samples', 0) + samples

    def _windows_layout(self, g: "_TemplateGroup", S: int, W: np.ndarray, support):
        """What _correlate_windows does for group g, windows W and support over S samples:
        (block starts, per-block copy-out bounds or None, the runs it fills, the flat
        [a0, b0, a1, b1, ...] edges of the runs it clears). Cached per group for a few
        recent (S, W, support): a search asks the same each chunk."""
        key = (S, W.tobytes(), None if support is None else support.tobytes())
        cache = g.__dict__.setdefault('_windows_layouts', OrderedDict())
        hit_ = cache.get(key)
        if hit_ is not None:
            cache.move_to_end(key)
            return hit_
        from . import _automatic_series_layout
        st = np.empty(0, dtype=np.uintp)
        bounds = None
        keep = written = np.empty((0, 2), np.int64)
        if W.shape[0]:
            cplan = g.get_correlation_plan()
            lo, hi = cplan.valid
            st, _, _ = _automatic_series_layout(S, cplan.valid)
            st = np.asarray(st, dtype=np.uintp)
            if st.size:
                b0 = st.astype(np.int64) + lo
                b1 = np.minimum(st.astype(np.int64) + hi, S)
                j = np.searchsorted(W[:, 1], b0, side='right')   # first window ending after b0
                hit = j < W.shape[0]
                hit[hit] = W[j[hit], 0] < b1[hit]
                st = st[hit]
                if st.size:
                    c0, c1 = b0[hit], b1[hit]
                    if cplan._gpu is None:
                        # Each block writes only from the first window it meets to the end
                        # of the last: no overhang computed into dest and then cleared.
                        jl = np.searchsorted(W[:, 0], c1, side='left') - 1
                        c0 = np.maximum(c0, W[j[hit], 0])
                        c1 = np.minimum(c1, W[jl, 1])
                        s64 = st.astype(np.int64)
                        bounds = np.ascontiguousarray(np.stack([c0 - s64, c1 - s64], axis=1),
                                                      dtype=np.uintp)
                    # the blocks are in order and disjoint: runs break where one ends short
                    brk = np.flatnonzero(c0[1:] > c1[:-1]) + 1
                    written = np.stack([c0[np.concatenate(([0], brk))],
                                        c1[np.concatenate((brk - 1, [c1.size - 1]))]], axis=1)
                    keep = _intersect_runs(W, written)      # W: sorted, disjoint
        # the complement of what is filled, as runs
        edges = np.concatenate(([0], keep.ravel(), [S]))
        if support is not None:
            dirty = _interval_runs(S, np.concatenate((support[:, 0], written[:, 0])),
                                   np.concatenate((support[:, 1], written[:, 1])))
            edges = _intersect_runs(edges.reshape(-1, 2), dirty).ravel()
        out = (st, bounds, keep, edges)
        cache[key] = out
        while len(cache) > 8:
            cache.popitem(last=False)
        return out

    def _correlate_windows(self, g: "_TemplateGroup", ser: np.ndarray, W: np.ndarray,
                           t0: int, nt: int, dest: np.ndarray, settle=None,
                           support=None) -> None:
        """Fill dest (nt, S) for group rows [t0, t0+nt): the correlation inside the
        union of W (where blocks compute it), exact zeros everywhere else. support:
        (K, 2) runs outside which dest is already zero (None: dest may hold anything);
        what is cleared is the complement of the result inside support and inside the
        blocks this call wrote.

        Only blocks whose valid span intersects a window are computed, each once
        even when several windows touch it."""
        S = ser.size
        st, bounds, keep, edges = self._windows_layout(g, S, W, support)
        if st.size:
            self._correlate_group(g, ser, st, t0, nt, dest, bounds)
            # Work counters for matchedfilter._roofline: per block length, the
            # blocks transformed, (block, template) products and inverses, the
            # output samples the windows ask for, and template spectra read.
            # (Stored bins per template without materialising a lazily planned
            # group's spectra: that stacked every template's filter, ~1 ms a call.)
            self._add_corr_work(g.n, dict(
                blocks=int(st.size), pairs=int(st.size) * nt,
                out_samples=int((keep[:, 1] - keep[:, 0]).sum()) * nt,
                tmpl_values=nt * _stored_bins(g)))
        # Clear by contiguous runs. Not dest[:, ~keep] = 0: boolean indexing along axis 1
        # thrashes one cache set once 17+ rows sit 2^20 samples apart (see _correlate_group);
        # 27 rows took ~400 ms against ~10 ms by runs.
        # A GPU-shared dest is zeroed on the device: host writes would pull its pages
        # back to the CPU (CUDA managed memory) only for the next kernel to fault them in.
        gpu = getattr(g.get_correlation_plan(), '_gpu', None) if W.shape[0] else None
        zero = gpu.zero_columns if gpu is not None else None
        if zero is not None:
            from ._shared import shared_view
            held = shared_view(dest, gpu, align=4)
            if held is None:
                zero = None
        for a, b in zip(edges[::2], edges[1::2]):
            if b > a:
                if zero is not None:
                    zero(dest, int(a), int(b))
                else:
                    dest[:, a:b] = 0
        if zero is not None:
            # `settle` collects contexts to finish later, so groups on different
            # contexts run concurrently; the caller settles them before returning.
            if settle is not None:
                settle.append(gpu)
            else:
                gpu.zero_columns_done()

    def correlate_series(
        self,
        series: np.ndarray,
        windows=None,
        scales: Optional[Union[np.ndarray, Sequence[float]]] = None,
        template_index: Optional[int] = None,
        out: Optional[np.ndarray] = None,
        wait: bool = True,
        templates: Optional[Sequence[int]] = None,
        out_support=None,
    ) -> np.ndarray:
        """Correlate a continuous series across all templates (or a specific template, or a
        list of them).

        Templates are filtered using their dynamically partitioned FFT block sizes
        for optimal cache and SIMD efficiency. Returns continuous correlation series
        in the original template ordering.

        Parameters:
            series: Continuous data series (1D complex64).
            windows: Analysis windows in series coordinates, in the same forms as
                     `filter_series`. Only blocks intersecting a window are
                     computed. The output holds the correlation inside the union
                     of the windows and exact zeros everywhere else, including
                     the parts of partially covered blocks outside every window.
                     Padding for filter context is the caller's job.
            scales: Optional per-template scale factors. Must have length `n_templates`
                    (or 1 / length matching template if `template_index` is specified).
            template_index: Optional single template index to filter. If specified,
                            returns a 1D array of shape `(len(series),)`.
            templates: Optional distinct template indices: output row j is template
                       templates[j], shape `(len(templates), len(series))`. Templates
                       adjacent both here and in a block-size group are correlated in one
                       call, which transforms each block once for all of them; list them in
                       bank order (ascending) to make those runs long.
            out_support: With `out`: where `out` may hold nonzero values on entry, in the
                     forms `windows` takes; elsewhere it is taken to be exact zero already
                     and is not written. A caller reusing `out` passes the windows of the
                     call that last filled it (after a call, `out` is zero outside its
                     windows). None: `out` may hold anything, and all of it is written.
            out: Optional preallocated output array. If `template_index` is None, shape
                 must be `(n_templates, len(series))` and dtype `complex64`. If `template_index`
                 is specified, shape can be `(len(series),)` or `(1, len(series))`.
                 Every sample is overwritten, so it need not be cleared.
                 If None, a new array is allocated.
            wait: False, with `out` a device-shared array (`empty_shared`) on a backend
                  that can (Vulkan): return once the work is submitted. Later work on the
                  same device -- e.g. filter_series_many reading `out` -- is ordered after
                  it on the device, so the GPU is fed without a host round trip. Before
                  reading `out` on the host, call `wait()`.

        Returns:
            If `template_index` is None: 2D complex64 array of shape `(n_templates, len(series))`.
            If `template_index` is specified: 1D complex64 array of shape `(len(series),)`.
        """
        from . import _from_any
        from .device import parse as _parse_device

        a = _from_any(series)
        # A real series stays real (a real-real-complex hierarchy's middle stage filtering
        # the real top output) where every group reads one: on the CPU, half-size block
        # transforms (correlate_series_continuous_real); on a GPU, a forward that reads
        # the real samples in place. Elsewhere it is widened to complex.
        if (isinstance(a, np.ndarray) and not np.iscomplexobj(a)
                and self._correlation_reads_real()):
            # A GPU forward reads one lane of a complex row (stride 2) in place; the CPU's
            # half-size transforms take a contiguous series.
            lane = (a.dtype == np.float32 and a.ndim == 1 and a.strides == (8,)
                    and _parse_device(self.device).kind != 'cpu')
            ser = a if lane else np.ascontiguousarray(a, np.float32)
        else:
            ser = _host_copy(a, np.complex64)
        if ser.ndim != 1:
            raise ValueError("series must be a 1D array")
        S = ser.size
        nt = self.n_templates
        W = _normalize_windows(windows, S)
        if out_support is not None:
            if out is None:
                raise ValueError("out_support describes out; pass out")
            support = _normalize_windows(out_support, S)
        else:
            support = None
        # Input samples the windows read (matchedfilter._roofline), once per call.
        self._add_corr_in(int((W[:, 1] - W[:, 0]).sum()))

        if template_index is not None:
            if template_index < 0 or template_index >= nt:
                raise IndexError(f"template_index {template_index} out of range [0, {nt})")
            self._groups
            target_g, ti_local = self._template_map[template_index]

            if scales is not None:
                sc_arr = np.ascontiguousarray(_from_any(scales), dtype=np.float32)
                if sc_arr.size == nt:
                    single_scale = sc_arr[template_index:template_index + 1]
                elif sc_arr.size == 1:
                    single_scale = sc_arr.ravel()[:1]
                else:
                    raise ValueError(f"scales must have length {nt} or 1 for single template")
            else:
                single_scale = None

            if out is not None:
                if not isinstance(out, np.ndarray) or out.dtype != np.complex64 \
                   or not out.flags.c_contiguous or not out.flags.writeable:
                    raise ValueError("out must be a writable C-contiguous complex64 array")
                if out.shape == (S,):
                    out_2d = out.reshape(1, S)
                elif out.shape == (1, S):
                    out_2d = out
                else:
                    raise ValueError(f"out shape {out.shape} must match ({S},) or (1, {S})")
            else:
                out_2d = np.empty((1, S), dtype=np.complex64)

            self._correlate_windows(target_g, ser, W, ti_local, 1, out_2d, support=support)
            if single_scale is not None:
                np.multiply(out_2d, single_scale[:, None], out=out_2d)

            if out is not None and out.ndim == 1:
                return out
            return out_2d[0] if out is None else out_2d

        if templates is not None:
            if template_index is not None:
                raise ValueError("give template_index or templates, not both")
            return self._correlate_selected(ser, W, templates, scales, out, support, wait=wait)

        # Full bank correlation across all groups
        shape = (nt, S)
        if scales is not None:
            scales_arr = np.ascontiguousarray(_from_any(scales), dtype=np.float32)
            if scales_arr.ndim != 1 or scales_arr.size != nt:
                raise ValueError(f"scales must be a 1D array of length {nt}, got shape {scales_arr.shape}")
        else:
            scales_arr = None

        if out is not None:
            if not isinstance(out, np.ndarray) or out.dtype != np.complex64 \
               or out.shape != shape or not out.flags.c_contiguous \
               or not out.flags.writeable:
                raise ValueError(f"out must be a writable C-contiguous complex64 array of shape {shape}")
            result = out
        else:
            result = _page_aligned_empty(shape)

        settle = []
        ok = False
        try:
            self._correlate_bank(ser, W, scales_arr, result, settle, support)
            ok = True
        finally:
            for gpu in {id(x): x for x in settle}.values():
                if ok and not wait:
                    gpu.zero_columns_done(wait=False)
                else:
                    gpu.zero_columns_done()
        return result

    def wait(self) -> None:
        """Finish work this bank's devices left in flight (correlate_series(wait=False))."""
        for g in self._groups:
            for plan in (getattr(g, '_corr_plan', None), g.plan):
                settle = getattr(getattr(plan, '_gpu', None), 'settle_writes', None)
                if settle is not None:
                    settle()

    def _stage_series(self, ser):
        """ser in device-shared memory usable by every group's correlation plan: ser itself if
        it is, else one copy for the whole bank (each group copied the series into its own
        staging buffer, ~0.6 ms per group per call at 2^20 samples), else ser.

        Two staging buffers alternate per call. Each remembers, per device, the write its
        call left in flight (_staging_done): rewriting it waits for exactly that call (two
        back), not for every write on the device."""
        from ._shared import shared_buffer
        gpus = []
        for g in self._groups:
            gpu = getattr(g.get_correlation_plan(), '_gpu', None)
            if gpu is None:
                return ser
            gpus.append(gpu)
        if len(gpus) < 2 or getattr(gpus[0], 'host_view', None) is not None:
            return ser                       # one group, or unified memory read in place
        from ._shared import containing_samples
        if all((containing_samples(ser, gpu) if ser.dtype == np.float32
                else shared_buffer(ser, gpu)) is not None for gpu in gpus):
            return ser                       # read in place (a real series by its layout)
        devs = {id(x): x for x in gpus}.values()
        bufs = self.__dict__.setdefault('_ser_stagings', [])
        k = self.__dict__.get('_ser_staging_next', 0) % 2
        self._ser_staging_next = k + 1
        while len(bufs) <= k:
            bufs.append([None, []])
        slot = bufs[k]
        for gpu, token in slot[1]:
            gpu.settle_until(token)          # the call that read this buffer has finished
        slot[1] = []
        staged = slot[0]
        if staged is None or staged.shape != ser.shape or staged.dtype != ser.dtype or any(
                shared_buffer(staged, gpu) is None for gpu in gpus):
            staged = gpus[0].empty_shared(ser.shape, ser.dtype)
            if any(shared_buffer(staged, gpu) is None for gpu in gpus):
                return ser
            slot[0] = staged
        self._fill_staging(staged, ser)
        self._staging_slot = slot
        return staged

    def _staging_done(self):
        """Remember, per device, the write left in flight by the call that read the staging
        buffer just filled (see _stage_series)."""
        slot = self.__dict__.pop('_staging_slot', None)
        if slot is None:
            return
        devs = {id(g.get_correlation_plan()._gpu): g.get_correlation_plan()._gpu
                for g in self._groups}.values()
        slot[1] = [(gpu, gpu.write_token()) for gpu in devs]

    @staticmethod
    def _fill_staging(staged, ser):
        staged[:] = ser

    def _correlate_bank(self, ser, W, scales_arr, result, settle, support=None):
        ser = self._stage_series(ser)
        try:
            self._correlate_groups(ser, W, scales_arr, result, settle, support)
        finally:
            self._staging_done()

    def _correlation_reads_real(self) -> bool:
        """Whether every group's correlation plan reads a real series itself: the CPU's, or a
        GPU's whose forward takes real samples (one-stage, n <= 65536)."""
        from .device import parse as _parse_device
        if _parse_device(self.device).kind == 'cpu':
            return True
        self._groups
        return all(_gpu_reads_real(g.get_correlation_plan()._gpu, g.n) for g in self._groups)

    def _correlate_selected(self, ser, W, templates, scales, out, support=None, wait=True):
        """correlate_series(templates=...): row j of the result is template templates[j]."""
        from . import _from_any
        S = ser.size
        sel = np.asarray(templates, dtype=np.int64).ravel()
        if sel.size and (sel.min() < 0 or sel.max() >= self.n_templates):
            raise IndexError(f"templates out of range [0, {self.n_templates})")
        if np.unique(sel).size != sel.size:
            raise ValueError("templates must be distinct")
        shape = (sel.size, S)
        if out is not None:
            if not isinstance(out, np.ndarray) or out.dtype != np.complex64 \
               or out.shape != shape or not out.flags.c_contiguous or not out.flags.writeable:
                raise ValueError(f"out must be a writable C-contiguous complex64 array of shape {shape}")
            result = out
        else:
            result = _page_aligned_empty(shape)
        if scales is not None:
            sc = np.ascontiguousarray(_from_any(scales), dtype=np.float32)
            if sc.ndim != 1 or sc.size != self.n_templates:
                raise ValueError(f"scales must be a 1D array of length {self.n_templates}")
        self._groups
        # runs of rows adjacent in the result and in one group: (group, first local, first row, count)
        runs = []
        for j, t in enumerate(sel):
            g, li = self._template_map[int(t)]
            if runs and runs[-1][0] is g and runs[-1][1] + runs[-1][3] == li:
                runs[-1][3] += 1
            else:
                runs.append([g, li, j, 1])
        settle = []
        ok = False
        try:
            ser = self._stage_series(ser)
            try:
                for g, li, j, cnt in runs:
                    self._correlate_windows(g, ser, W, li, cnt, result[j:j + cnt], settle,
                                            support=support)
            finally:
                self._staging_done()
            ok = True
        finally:
            # Scales are applied on the host below, so a scaled call finishes its work here.
            for gpu in {id(x): x for x in settle}.values():
                if ok and not wait and scales is None:
                    gpu.zero_columns_done(wait=False)
                else:
                    gpu.zero_columns_done()
        if scales is not None:
            np.multiply(result, sc[sel][:, None], out=result)
        return result

    def _correlate_groups(self, ser, W, scales_arr, result, settle, support=None):
        S = ser.size
        for g in self._groups:
            g_indices = g.template_indices
            g_cnt = len(g_indices)
            if g_cnt == 0:
                continue
            is_contiguous_slice = (
                (g_indices[-1] - g_indices[0] + 1 == g_cnt) and
                np.array_equal(g_indices, np.arange(g_indices[0], g_indices[0] + g_cnt))
            )
            if is_contiguous_slice:
                g_dest = result[g_indices[0] : g_indices[0] + g_cnt]
            else:
                # Interleaved templates: compute into a group-sized array, then scatter.
                g_dest = np.empty((g_cnt, S), dtype=np.complex64)
            # Only a group written in place with nothing to do after may stay in flight.
            late = is_contiguous_slice and scales_arr is None
            # a scratch destination holds anything: all of it is written
            self._correlate_windows(g, ser, W, 0, g_cnt, g_dest, settle if late else None,
                                    support=support if is_contiguous_slice else None)
            if scales_arr is not None:
                np.multiply(g_dest, scales_arr[g_indices][:, None], out=g_dest)
            if not is_contiguous_slice:
                result[g_indices] = g_dest


def _stored_bins(g):
    """Bins stored per template spectrum of group g (n, or n/2 when Hermitian-packed)."""
    return g._stored_bins


def _consume_into(lists, aidx, aval, sub_starts, g, tmpl_arg, N, template_index):
    """Append the peaks of one run_series result (nblocks, ntemplates, nbins) to lists."""
    ti_out, si_out, snr_out, ts_out, bl_out = lists
    if tmpl_arg is not None:
        bi, _, bini = np.nonzero(aidx >= 0)
        if bi.size:
            ti_out.append(np.full(bi.size, template_index, dtype=np.int64))
            si_out.append(sub_starts[bi] + aidx[bi, 0, bini])
            snr_out.append(aval[bi, 0, bini])
            ts_out.append(sub_starts[bi])
            bl_out.append(np.full(bi.size, N, dtype=np.int64))
    else:
        bi, ti, bini = np.nonzero(aidx >= 0)
        if bi.size:
            ti_out.append(g.template_indices[ti])
            si_out.append(sub_starts[bi] + aidx[bi, ti, bini])
            snr_out.append(aval[bi, ti, bini])
            ts_out.append(sub_starts[bi])
            bl_out.append(np.full(bi.size, N, dtype=np.int64))


def _results_from(lists):
    ti, si, snr, ts, bl = lists
    if not ti:
        return _EMPTY_FILTER_RESULTS
    return FilterResults(
        template_indices=np.concatenate(ti).astype(np.int64),
        sample_indices=np.concatenate(si).astype(np.int64),
        snr=np.concatenate(snr).astype(np.complex64),
        block_starts=np.concatenate(ts).astype(np.int64),
        block_lengths=np.concatenate(bl).astype(np.int64),
    )
