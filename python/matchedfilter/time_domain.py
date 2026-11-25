"""TimeDomainFilterBank: Ingest raw time-domain filters, dynamically partition by length,
automatically select optimal FFT block sizes, and filter continuous series."""

from collections import OrderedDict
import itertools
import collections.abc as _abc
from typing import Any, Optional, Sequence, Union, Tuple, List, Dict
import threading
import weakref
import sys
import time
import numpy as np
from . import _calibration, _config
from . import _settings, _trial
from ._choice import (_AUTOTUNE_LOCK, TIE as _TIE, _autotune_enabled, held, playing,
                      _log_autotune)
from ._results import FilterResults, _EMPTY_FILTER_RESULTS  # noqa: F401  (public here)
from ._windows import _normalize_windows, _window_layout, _merge_window_bins, _window_bin_phases
# The bank's layout planning lives in _layout.
from ._layout import _corr_partition, _partition_templates
from . import _core, _choice
from ._hierarchical import _record_cpu_trial
from ._results import _SparsePeaks, _Deferred
from ._filter import _from_any, _automatic_series_layout
from ._shared import containing_samples, shared_buffer, shared_view
from . import _layout, gatechain
from . import device as _device


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
        cell = []

        def part(i):
            if not cell:
                cell.append(self.parts(d.result()))
            return cell[0][i]
        return [_Deferred(lambda i=i: part(i)) for i in range(len(self.us))]


def _page_aligned_empty(shape, dtype=np.complex64, page: int = 16384) -> np.ndarray:
    """np.empty, starting on a page boundary: unified-memory GPUs can then write into it
    in place (see _correlate_group). Costs at most one page."""
    dtype = np.dtype(dtype)
    nbytes = int(np.prod(shape)) * dtype.itemsize
    raw = np.empty(nbytes + page, dtype=np.uint8)
    off = (-raw.ctypes.data) % page
    return raw[off:off + nbytes].view(dtype).reshape(shape)


def _aligned_zeros(shape, dtype=np.complex64, align: int = 64) -> np.ndarray:
    """np.zeros starting on an align-byte boundary while keeping calloc zero-page backing."""
    dtype = np.dtype(dtype)
    nbytes = int(np.prod(shape)) * dtype.itemsize
    raw = np.zeros(nbytes + align, dtype=np.uint8)
    off = (-raw.ctypes.data) % align
    return raw[off:off + nbytes].view(dtype).reshape(shape)


class _RecycledBuffer:
    """Array-interface owner keeping a backing uint8 buffer alive across all NumPy views."""
    __slots__ = ("__array_interface__", "_raw", "__weakref__")

    def __init__(self, raw: np.ndarray, off: int, shape: tuple, dtype: np.dtype):
        self._raw = raw
        self.__array_interface__ = {
            "shape": shape,
            "typestr": dtype.str,
            "data": (raw.ctypes.data + off, False),
            "version": 3,
        }


def _interval_runs(S: int, starts: np.ndarray, stops: np.ndarray) -> np.ndarray:
    """The union of [starts, stops) clipped to [0, S), as sorted disjoint (K, 2) runs.

    The set a boolean mask of length S would describe, without the S-long array: a
    2^20-sample mask costs a cumsum and a pass per use, and the middle stage needed three
    per group per call.
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
#: _BLOCK_TRIAL_RANKS candidate layouts in all); the Q15 screen both ways. (Each plan's chain is
#: its model's: see _trial.) Block
#: sizes are absolute candidates, smallest first: on a loaded Haswell node the model priced 4096
#: at 1.2x 2048 where it ran 1.6-1.95x, and fresh processes put 0-231 of test67's 323 banks on
#: 4096 (2026-10-25); ranked by its price, the candidates were its errors.
_BLOCK_TRIAL_RANKS = 3


def _small_blocks_fit(device):
    """Whether 1024-sample blocks are a candidate for a CPU bank above 1024 Hz: when a 2048
    block's pair working set -- its data and template spectra and the intermediate, 3 x 8n
    bytes, 48 KB -- fills the L1D. Then the valid-fraction rule takes 1024 wherever it keeps
    half of each block valid. Flat banks only: the hierarchical engine prices its own block
    sizes (_choose_layout). Measured 2026-10-24 on test27's fine banks (257-297 taps; 1024
    against 2048): Haswell and Zen 3 (32 KB) -10% / -11%, Ivy Bridge (32 KB) -15%, Zen 5
    (48 KB) -9%, an M2 (128 KB) +2.6%, which keeps 2048. Above 1024 Hz the candidates had started
    at 2048 since a decimation scheme removed on 2026-10-05; no measurement chose that. A
    GPU bank has no such rule: its block-size candidates are _gpu_small_blocks'."""
    try:
        if _device.parse(device).kind != "cpu":
            return False
    except (TypeError, ValueError):
        return False
    l1d = int(_core.l1d_bytes())
    return bool(l1d) and 3 * 8 * 2048 >= l1d


def _gpu_small_blocks(device, engine, binsize):
    """Whether 1024-sample blocks are a candidate for a GPU bank above 1024 Hz: for a
    hierarchical bank with a peak granularity, which measures its block size (the bank's
    joint trial, _choose_layout) rather than taking the valid-fraction rule. Excluding 1024
    there was no measurement's choice: offered it, the 8060S's trial took 1024 on the
    171,828-template BNS search (2026-11-25; 2048 and 1024 timed within 0.2% per call) and
    the pycbc job ran 98-102 s against 112-128 s at 2048, most of it the per-plan chain
    choice and clustering, which cost less at the smaller block."""
    try:
        if _device.parse(device).kind != "gpu":
            return False
    except (TypeError, ValueError):
        return False
    return engine == 'hier' and binsize is not None


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


#: Banks of a batch a joint round replays: a round needs comparable work, not the whole batch.
#: Rounds pool as ratios, so a few banks per round, rotated from round to round over the
#: batch's banks (other profiles in turn), sample the arms as well as all of them; the rest of
#: the batch runs once, on the default. A test67 batch held 17 banks: replaying all of them
#: for every configuration cost 11 s of a 74 s job (dev2, 2026-10-26).
_ROUND_BANKS = 2
#: Maximum banks in a batch that ever materialize trial layouts across all rounds of a trial.
_TRIAL_SAMPLE_BANKS = 4 * _ROUND_BANKS

#: A joint round's settle on a GPU (_joint_round): replays until one builds nothing and runs
#: within this fraction of the one before -- half the paired rule's tie, so what is left of
#: the drift cannot by itself carry an arm past the tie -- and at most this many replays.
_SETTLE_TOL = _TIE / 2
_SETTLE_REPLAYS = 5


def _settle(replay, built, clock=None):
    """Replay a GPU batch until it is in steady state, for a joint round's timed replay;
    returns the replays run. A batch after a switch builds recordings and uploads, and runs
    slower for a replay or two after it has built everything (the driver settling the
    buffers it just allocated). So it is replayed until a replay builds nothing (built(),
    the batch's contexts' recordings) and runs within _SETTLE_TOL of the replay before, at
    most _SETTLE_REPLAYS times. Settled by builds alone, a round's first configuration timed
    10-25% slower than its second use (dev3, Renoir RADV), and the arm played first in a
    round read 14-21% slower than the same configuration played later; settled to time, the order made no difference."""
    clock = clock or time.perf_counter
    prev = None
    for n in range(1, _SETTLE_REPLAYS + 1):
        before = built()
        t0 = clock()
        replay()
        t = clock() - t0
        if built() == before and prev is not None and abs(t - prev) <= _SETTLE_TOL * prev:
            return n
        prev = t
    return _SETTLE_REPLAYS


def _joint_round(jobs):
    """A round of the joint trial of the banks of this batch that are in one (_trial.run_round):
    each distinct configuration of the trial's live arms runs a few of those banks' jobs
    (_ROUND_BANKS, rotated), settled on its first run and timed, and their results are
    DEFAULT's; the rest of the batch runs once. Banks whose trial has locked adopt the lock
    here. Returns the batch's results, or None when no round ran."""
    if playing() or not jobs or not _autotune_enabled():
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
    gpu = any(_device.parse(b.device).kind == "gpu" for b, _, _ in jobs)

    def settle_for(sub):
        banks = [b for b, _, _ in sub]
        return lambda: _settle(lambda: TimeDomainFilterBank.filter_series_many(sub),
                               lambda: _built(banks))

    begin = time.perf_counter()
    out = [None] * len(jobs)
    timed = set()
    for key, byid in groups.items():
        banks = list(byid.values())
        tr = _trial.trial(key, banks[0]._joint_arms)
        if len(tr.live()) < 2:
            ch = tr.choice
            with _AUTOTUNE_LOCK:
                ch.lock(_trial.DEFAULT)
        if tr.winner is not None:
            for b in banks:
                b._lock_arm(tr.winner)
            continue
        # Sample up to _TRIAL_SAMPLE_BANKS interior tap-length quantiles paired antithetically,
        # rotating by a monotonic round counter so every round balances short and long profiles
        # without materializing new trial layouts in late rounds.
        ordered = sorted(
            banks,
            key=lambda b: int(np.max(b.tap_counts)) if len(b.tap_counts) else 0,
        )
        if len(ordered) > _TRIAL_SAMPLE_BANKS:
            m = _TRIAL_SAMPLE_BANKS
            quantiles = [ordered[(2 * i + 1) * len(ordered) // (2 * m)] for i in range(m)]
        else:
            quantiles = ordered
        sample = []
        lo, hi = 0, len(quantiles) - 1
        while lo <= hi:
            sample.append(quantiles[lo])
            if lo < hi:
                sample.append(quantiles[hi])
            lo += 1
            hi -= 1
        seq = getattr(tr, "_round_seq", 0)
        tr._round_seq = seq + 1
        k = (seq * _ROUND_BANKS) % len(sample)
        chosen = (sample[k:] + sample[:k])[:_ROUND_BANKS]
        # A bank's first round materializes every candidate layout it may be asked for (and
        # prices the model's block sizes), so all of that happens within the cohort's warmup
        # rounds: lazily, a later pass of the trial meeting a configuration the bank had not
        # yet built priced it then (Nightly arm64, 2026-11-11: 8 priced calls where 6).
        for b in chosen:
            b._prepare_arms()
        pick = {id(b) for b in chosen}
        idx = [j for j, (b, _, kw) in enumerate(jobs) if id(b) in pick
               and (kw or {}).get("template_index") is None and j not in timed]
        if not idx:
            continue
        sub = [jobs[j] for j in idx]
        sub_work = sum(len(b.filters_f) * int(np.asarray(x).size) for b, x, _ in sub)
        if sub_work <= 0:
            continue

        def replay(sub=sub):
            return TimeDomainFilterBank.filter_series_many(sub)

        res = _trial.run_round(tr, _BankArms.of([jobs[j][0] for j in idx]), replay, sub_work,
                               settle=settle_for(sub) if gpu else None)
        if tr.winner is not None:
            for b in banks:
                if b._in_trial:
                    b._lock_arm(tr.winner)
        for j, r in zip(idx, res):
            out[j] = r
        timed.update(idx)
    rest = [j for j in range(len(jobs)) if j not in timed]
    if timed and rest:
        with held():                                    # the rest runs once, untimed
            for j, r in zip(rest, TimeDomainFilterBank.filter_series_many([jobs[j] for j in rest])):
                out[j] = r
    if not timed:
        return None
    if not gpu:
        _record_cpu_trial(begin)
    return out


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
    return min(3, HierarchicalFilter._MAX_TIERS[_device.parse(device).kind])


#: "the profile in use": the default of the calls that take a profile (None is a profile's name).
_SAME_PROFILE = object()

#: The configurations each device set's trials have settled (Choice.play's `ran`).
_GPU_RAN = {}
#: The kernel slots each batch composition (devices, banks, follow-ups or not) consulted the
#: last time a waited run of it ran (_gpu_batch).
_SEEN_BY_BATCH = {}


def _gpu_trials(gpus, jobs, seen):
    """The device trials of a batch: (name, {dimension: alternatives}, exercised(dimension)).
    Each decides its dimensions (_settings.DIMS) together, in coordinate passes
    (_trial.current_pass): the first pass's arms move one. exercised says
    whether this batch runs a dimension at all: an arm counts as running the batch
    differently only through dimensions it exercises (_gpu_batch), so a trial is played
    only on batches that can tell its arms apart."""
    follow = any((kw or {}).get("template_index") is not None for _, _, kw in jobs)
    yield "gpu-single", {"single": ["cpu"]}, lambda d: follow
    registered = _settings.slots({g.name for g in gpus})
    yield "gpu-kernels", {d: [alt] for d, (_, alt) in registered.items()}, lambda d: d in seen


def _gpu_default(name, registered):
    """A batch dimension's default: the declared one, or a kernel slot's registered one."""
    if name in registered:
        return registered[name][0]
    return _settings.dim(name).default


def _gpu_batch(jobs, run):
    """Run a batch (run() -> its results) with the device trials' settings (_gpu_trials): per
    set of GPU devices, a paired _choice.Choice per trial over its arms, played on the batch
    itself where the batch can tell them apart (Choice.play: every arm that runs the batch
    differently runs it, waited, back to back), its lock then in force for every batch
    (_settings). One trial plays a batch; the others take their locks or defaults. Returns
    run()'s results."""
    # A bank's device None is MF_DEVICE's (device.parse), as everywhere in the library.
    parsed = [_device.parse(b.device) for b, _, _ in jobs if hasattr(b, "device")]
    gpus = [d for d in parsed if d.kind == "gpu"]
    if not gpus:
        return run()
    devs = _gpu_devs(gpus)
    locked = _settings.locks(devs)
    names = {d.name for d in gpus}
    if playing() or not _autotune_enabled():
        with _settings.running(dict(locked)):
            return run()
    # the slots this batch's composition consulted when a waited run of it last ran
    comp = (devs, tuple(sorted({id(b) for b, _, _ in jobs})),
            any((kw or {}).get("template_index") is not None for _, _, kw in jobs))
    seen = _SEEN_BY_BATCH.get(comp, set())
    registered = _settings.slots(names)

    def seen_run(moved):
        _settings._SEEN.clear()
        try:
            with _settings.running(dict(locked, **moved)):
                return run()
        finally:
            # a pipelined batch (wait=False) submits its calls after run() returns: it records
            # nothing here, and must not erase what a waited run (a play) recorded
            got = {d for dev, d in _settings._SEEN if dev in names}
            if got:
                _SEEN_BY_BATCH[comp] = got
                while len(_SEEN_BY_BATCH) > 256:
                    _SEEN_BY_BATCH.pop(next(iter(_SEEN_BY_BATCH)))

    for name, dims, exercised in _gpu_trials(gpus, jobs, seen):
        if not dims or all(d in locked for d in dims):
            continue
        proposals = [_settings.arm(d, v) for d in sorted(dims) for v in dims[d]]

        def make(base, arms, name=name):
            what = "%s %s" % (name.upper(), devs) + ("" if base == _settings.DEFAULT
                                                      else " around %s" % base)
            return _choice.choice(name, (devs, base), arms, confirm=True, parse=_settings.valid,
                                  store_key=_trial.pass_key("%s|%s" % (name, "+".join(devs)), base),
                                  what=what)
        ch = _trial.current_pass(make, proposals)
        if ch.winner is None:
            def config(label, dims=dims, exercised=exercised):
                mv = _settings.moves(label)
                return tuple(mv.get(d, _gpu_default(d, registered)) if exercised(d)
                             else _gpu_default(d, registered) for d in sorted(dims))
            if len({config(a) for a in ch.live()}) < 2:
                continue            # every live arm runs this batch alike: nothing to play
            ran = _GPU_RAN.setdefault((name, devs), set())
            res = ch.play(lambda label: seen_run(_settings.moves(label)), ran, config=config)
            ch = _trial.current_pass(make, proposals)
            if ch.winner is not None:
                _lock_trial(locked, ch.winner, dims, registered)
            return res
        _lock_trial(locked, ch.winner, dims, registered)
    return seen_run({})


def _lock_trial(locked, winner, dims, registered):
    """A device trial's end into its device set's settings: each of its dimensions at the
    winning arm's value, or at its default."""
    win = _settings.moves(winner)
    for d in dims:
        locked[d] = win.get(d, _gpu_default(d, registered))


def _gpu_devs(gpus):
    return tuple(sorted({"%s %s" % (d, d.name) for d in gpus}))


def _single_choice(device, n, nblocks):
    """Where single-template calls of this shape (device, block size, block count's power of
    two) run (_settings "side"): paired, played on the calls (TimeDomainFilterBank._single_play)."""
    key = (str(device), int(n), 1 << max(0, int(nblocks) - 1).bit_length())
    return _choice.choice("single-device", key, (_settings.DEFAULT, _settings.arm("side", "cpu")),
                          confirm=True, parse=_settings.valid,
                          store_key="single-device|%s|%d|%d" % key,
                          what="SINGLE %s n=%d blocks~%d" % key)


def _side_of(label):
    return _settings.moves(label).get("side", _settings.dim("side").default)


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
#: id of a reference array found to hold power -> a weak reference to it (the entry goes
#: when the array does, so an id that is used again is not taken for it)
_REFERENCES_WITH_POWER = {}
_REF_BINNED_CACHE = _ReferenceCache()


#: The CPU's single-template plans, one per block length, shared by every group of that length
#: (_TemplateGroup.get_single_plan).
_SINGLE_CPU_PLANS: Dict[int, Any] = {}
_GROUP_SERIAL = itertools.count()


def _single_plan_blocks(n):
    """Blocks a CPU single-template plan of block length n filters per kernel call. One block
    per call left the kernels' batching unused: a follow-up window of 51,000 samples at
    n = 1024 took 0.81 ms a block at a time and 0.27 ms in batches of 32 (Zen 5, replay of a
    search's refilter calls, tools/bench_refilter.py). The batch is held to about 256 KB of
    block spectra, so it stays in the second-level cache."""
    return int(max(4, min(32, (1 << 15) // int(n))))


class _TemplateGroup:
    """Internal container for a homogeneous batch of templates sharing an FFT size."""

    def __init__(self, plan, n, template_indices, c_bad, n_valid, orig_taps_max, device=None,
                 plan_factory=None, kind=None, spectra_source=None, row_source=None,
                 stored_bins=None, group_taps=None):
        # A hierarchical plan is made up front (references and templates load into it); a flat or
        # correlation plan only when something first filters with it, so a bank kept for its
        # spectra and layout alone costs no plan memory.
        self._plan = plan
        self._plan_factory = plan_factory
        self.is_hier = plan_factory is None and getattr(plan, '_is_hierarchical', False)
        self.kind = kind
        self._spectra_source = spectra_source
        self._row_source = row_source
        self._group_taps = group_taps
        self.n = int(n)
        self._stored_bins = int(n if stored_bins is None else stored_bins)
        self.template_indices = np.asarray(template_indices, dtype=np.int64)
        self.c_bad = int(c_bad)
        self.n_valid = int(n_valid)
        self.orig_taps_max = int(orig_taps_max)
        self.device = device
        self.templates_loaded = False
        self._cached_layout: Optional[Tuple[Tuple[int, int, int], np.ndarray, np.ndarray, np.ndarray]] = None
        self._cached_single_layout = None       # the same for single-template calls
        self._serial = next(_GROUP_SERIAL)       # this group's name in shared plans' records
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
        """An ungated plan holding only local template ti: what a single-template call needs,
        without building the group's whole ungated bank. The plan is shared and the template
        loaded into it when it is not the one already there, so the caller runs the plan
        before asking for the next one.

        On the CPU every group of one block length shares one plan (_SINGLE_CPU_PLANS), which
        filters several blocks per kernel call (_single_plan_blocks). A GPU group keeps its
        own, since a plan there owns a device context (~10 ms to create).

        Parameters
        ----------
        ti : int
            The template, as its row in this group.
        on_cpu : bool, optional
            The CPU's plan even for a GPU group (TimeDomainFilterBank._single_device).
            Default False.

        Returns
        -------
        MatchedFilter
            A one-template plan of this group's block length with template ti loaded.
        """
        from . import MatchedFilter
        # Which plan: the group's own on a GPU, the block length's shared one on the CPU.
        if _device.parse(self.device).kind == 'gpu' and not on_cpu:
            plan = self.__dict__.get('_single_gpu_plan')
            if plan is None:
                plan = self._single_gpu_plan = MatchedFilter(self.n, ndata=1, ntemplates=1,
                                                             device=self.device)
        else:
            plan = _SINGLE_CPU_PLANS.get(self.n)
            if plan is None:
                # 'cpu', not None: None means MF_DEVICE, which would move the CPU's own plan
                # to a GPU.
                plan = _SINGLE_CPU_PLANS[self.n] = MatchedFilter(
                    self.n, ndata=_single_plan_blocks(self.n), ntemplates=1, device='cpu')
        # Load the template unless the plan holds it. The group's serial names the group: an
        # id() would be reused by a later group and leave another bank's template loaded.
        loaded = (self._serial, int(ti))
        if plan.__dict__.get('_single_loaded') != loaded:
            sp = self.full_spectra(slice(int(ti), int(ti) + 1))
            if hasattr(plan, '_settle_deferred'):
                # Calls deferred in a batch still read the current template: let them finish.
                plan._settle_deferred()
            plan.set_templates(np.ascontiguousarray(sp))
            plan._single_loaded = loaded
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
        # The last spectrum made, of any bank's filters, is kept: a consumer's signal-
        # consistency test asks for one template's filter twice in a row (pycbc's power chisq:
        # the trigger's correlation, then its template), and each is 18 us of Python and
        # transform in the 171,828-template pycbc job. A copy is returned, as a fresh spectrum
        # would be, so a caller that writes into its array leaves the kept one alone.
        last = _LAST_FILTER[0]
        if last is not None and last[1] == i and last[0]() is self:
            return last[2].copy()
        g, ti = self._map[i]
        spec = np.conj(g.full_spectra(slice(ti, ti + 1))[0])
        _LAST_FILTER[0] = (weakref.ref(self), i, spec.copy())
        return spec


#: (weak reference to a _Filters, template index, its spectrum): the last one _Filters made.
_LAST_FILTER = [None]


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
    if rate_ratio == 1.0:
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

    The filters are those a :class:`TimeDomainFilterBank` holds for a block of
    ``block_length`` (conjugate spectrum, centre tap at lag 0). Nothing else is built.

    Parameters
    ----------
    taps : ndarray
        (T, m) float32 or complex64 taps.
    tap_counts : sequence of int or None
        Taps used per row. None: all m.
    block_length : int
        The FFT block length.
    tap_sample_rate : float, optional
        Sample rate of the taps in Hz (default 2048).
    data_sample_rate : float, optional
        Sample rate of the data in Hz (default 2048).
    analytic : bool, optional
        Whether the data is analytic (default False).
    out : ndarray, optional
        (T, block_length) complex64, C-contiguous: the filters are written there and nothing
        is allocated for them.

    Returns
    -------
    filters : ndarray
        (T, block_length) complex64.
    valid : ndarray
        (T, 2) int64: each template's [start, stop) of lags in a block whose correlation is
        not wrapped by its own taps.

    Raises
    ------
    ValueError
        If a template does not fit the block.
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
    """The lags where each template's correlation on one block length is valid.

    The same ``valid`` as :func:`template_spectra` returns, from the tap counts alone.

    Parameters
    ----------
    tap_counts : sequence of int
        Taps per template.
    block_length : int
        The FFT block length.
    tap_sample_rate : float, optional
        Sample rate of the taps in Hz (default 2048).
    data_sample_rate : float, optional
        Sample rate of the data in Hz (default 2048).

    Returns
    -------
    ndarray
        (T, 2) int64: each template's [start, stop) of lags in a block whose correlation is
        not wrapped by its own taps.

    Raises
    ------
    ValueError
        If a template does not fit the block.
    """
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
    """A bank of time-domain FIR templates filtered over continuous series.

    The bank takes each template's taps and sample rate, groups the templates by length,
    chooses an FFT block size per group, converts between the tap and data sample rates, and
    runs overlap-save filtering. Results are in the series' own sample coordinates.

    Parameters
    ----------
    taps : ndarray or sequence of ndarray
        The templates' taps: a (T, m) float32 or complex64 array, or a sequence of 1-D
        arrays. Row t's centre tap, ``tap_counts[t] // 2``, is lag 0. Real and complex taps
        both work on real and complex series with the engines ``"flat"``, ``"dif"`` and
        ``"corr"``. The ``"hier"`` engine's gates place their bands in the lower half of each
        block's spectrum (bins 0 to n / 2 - 1, the positive frequencies). A signal with most
        of its power in the upper half, as complex taps at negative frequencies give, is gated
        on the little of its power there: the gates pass most pairs, so the bank stays within
        its false-dismissal budget (when the reference describes every template) but runs
        slowly, and ``"flat"`` is the better engine.
    tap_counts : sequence of int, optional
        Taps used per row. Defaults to every column of the array, or each array's length.
    tap_sample_rate : float, optional
        Sample rate of the taps in Hz (default 2048).
    data_sample_rate : float, optional
        Sample rate of the series in Hz (default 2048).
    engine : str, optional
        ``"hier"`` (default) for gated hierarchical filtering, ``"flat"`` for a full
        search of every pair, or ``"corr"`` for full correlation output
        (:meth:`correlate_series`).
    threshold : float, optional
        The SNR threshold a peak must exceed (default 5.0). A call may raise it.
    false_dismissal : float, optional
        The hierarchical gates' false-dismissal budget per plan at ``threshold``
        (default 0.001).
    first_stage_snr : float, optional
        SNR the gates are calibrated at, if not ``threshold`` (default 0: ``threshold``).
    coarse_band_hz : float or tuple of float, optional
        Pins the gate chain: one first band, or every band, in Hz. Default None: the cost
        model chooses the chain.
    device : str, optional
        Where the bank runs, as :meth:`matchedfilter.device.Device.parse` takes it.
        Default None: ``MF_DEVICE``, else the CPU.
    max_batch_size : int, optional
        The most templates one group holds. Default None: no limit.
    fft_lengths : sequence of int, optional
        The block sizes the bank may use. Default None: powers of two from 1024 or 2048
        up to 65536.
    reference : ndarray or dict, optional
        A reference profile, set as :meth:`set_reference` sets it. Default None.
    analytic : bool, optional
        Whether the series is analytic (positive frequencies only). Default False.
    bandlimited : bool, optional
        Run flat filtering as two-channel decimation in frequency (``engine`` becomes
        ``"dif"``). Default False.
    pack_templates : bool, optional
        Store real hierarchical templates Hermitian-packed, in half the memory. Exact, but
        slower to refine. Default False.
    binsize : int, optional
        Samples per peak bin, fixing the bins on each window's grid. With the hierarchical
        engine, it also lets the bank choose block sizes by cost once a reference is set.
        Default None: one peak per block.
    max_block_length : int, optional
        The largest block size the bank may choose by cost (default 8192). The caller
        pads its series and guards its windows by the longest block.
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
        # Arguments outside what the bank can run are refused here, by name, rather than
        # ignored or left to fail (or loop) deep in the planner.
        for name, rate in (("tap_sample_rate", self.tap_sample_rate),
                           ("data_sample_rate", self.data_sample_rate)):
            if not (np.isfinite(rate) and rate > 0.0):
                raise ValueError("%s must be positive and finite; got %r" % (name, rate))
        if not 0.0 < self.false_dismissal < 1.0:
            raise ValueError("false_dismissal must be between 0 and 1, exclusive; got %r"
                             % (false_dismissal,))
        if not (np.isfinite(self.first_stage_snr) and self.first_stage_snr >= 0.0):
            raise ValueError("first_stage_snr must be finite and >= 0 (0: the threshold); "
                             "got %r" % (first_stage_snr,))
        if coarse_band_hz is not None:
            bands = np.atleast_1d(np.asarray(coarse_band_hz, dtype=np.float64))
            if not (np.isfinite(bands).all() and (bands >= 0.0).all()):
                raise ValueError("coarse_band_hz must be finite and >= 0 (0 or None: the "
                                 "model's chain); got %r" % (coarse_band_hz,))
        if max_batch_size is not None and int(max_batch_size) < 1:
            raise ValueError("max_batch_size must be >= 1, or None for no limit; got %r"
                             % (max_batch_size,))
        if binsize is not None and (int(binsize) != binsize or int(binsize) < 0):
            raise ValueError("binsize must be a positive integer, or None for one peak per "
                             "block; got %r" % (binsize,))
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
        if mode not in ('flat', 'hier', 'corr', 'dif'):
            raise ValueError("unknown engine %r: one of 'hier', 'flat', 'corr' (or their "
                             "aliases 'matchedfilter-hierarchical', 'matchedfilter', 'pycbc', "
                             "'correlation')" % (engine,))
        self.engine = mode

        # Parse inputs. Complex taps (complex_taps) are correlated with a real or complex
        # series as real taps are, the series against the conjugate tap spectrum. A common
        # use is quadrature filters, the analytic version of a real filter, which turn a real
        # series into the complex SNR without an analytic series. The hierarchical gates use
        # the lower half of the spectrum only.
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
        held = np.array([len(t) for t in taps], dtype=np.int64)
        if np.any(tap_counts < 0) or np.any(tap_counts > held):
            bad = int(np.flatnonzero((tap_counts < 0) | (tap_counts > held))[0])
            raise ValueError("tap_counts[%d] = %d is outside its template's %d taps"
                             % (bad, int(tap_counts[bad]), int(held[bad])))

        self.n_templates = n_templates
        self.tap_counts = tap_counts
        self._taps_list = taps_list


        # Multi-rate scaling: ratio of tap sample rate to data sample rate
        self.rate_ratio = self.tap_sample_rate / self.data_sample_rate
        # Effective tap length in data samples
        self.effective_data_counts = np.ceil(self.tap_counts / self.rate_ratio).astype(np.int64)

        if fft_lengths is None:
            if (self.data_sample_rate <= 1024.0 or self.analytic
                    or ((self.engine == 'flat' or (self.engine == 'hier' and binsize is not None))
                        and _small_blocks_fit(device))
                    or _gpu_small_blocks(device, self.engine, binsize)):
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
            self._legacy_layout = self._corr_bank_layout(candidate_ns)
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

    def _corr_bank_layout(self, candidate_ns: Sequence[int]):
        """Partition correlation templates by calibrated transform cost without L2 coarse-band caps.

        Parameters
        ----------
        candidate_ns : Sequence[int]
            Candidate power-of-two FFT block lengths to evaluate.

        Returns
        -------
        tuple
            ``(groups, order)`` matching ``_corr_partition``'s layout format.
        """
        counts = np.asarray(self.effective_data_counts, dtype=np.int64)
        M = len(counts)
        if M == 0:
            return _corr_partition(counts, candidate_ns, self.max_batch_size, self.device)
        order = np.argsort(counts, kind="stable")
        Ls = counts[order]
        ns = sorted(int(n) for n in candidate_ns)
        is_gpu = _device.parse(self.device).kind == "gpu"
        cap = int(self.max_batch_size) if self.max_batch_size is not None else M
        # On CPU, reconstruct s1 = b + w*(3n/4) to cancel 3rd-point w(n) calibration jitter and
        # the 8-block L3-vs-DRAM streaming step, subtracting a uniform write floor across n.
        # On GPU, w(n) is measured over ~512K samples in VRAM and captures LDS spill above 8192.
        group_per_samp = 0.0 if is_gpu else 6e-10
        raw_costs = [(n, *_layout._corr_block_costs(n, self.device)) for n in ns]
        if is_gpu:
            costs = raw_costs
        else:
            s1_list = [(n, a, b + w * (n - n // 4), n - n // 4) for n, a, b, w in raw_costs]
            w_floor = 0.5 * min(s1 / v0 for _, _, s1, v0 in s1_list) if s1_list else 0.0
            costs = [(n, a, max(0.0, s1 - w_floor * v0), 0.0) for n, a, s1, v0 in s1_list]
        best = np.full(M + 1, np.inf)
        best[0] = 0.0
        arg: List[Tuple[int, int]] = [(0, 0)] * (M + 1)
        for j in range(1, M + 1):
            L = int(Ls[j - 1])
            i0 = max(0, j - cap)
            i = np.arange(i0, j)
            span_count = j - i
            for n, a, b_eff, w_eff in costs:
                nv = n - L + 1
                if nv < 1:
                    continue
                c = best[i0:j] + (a + group_per_samp * nv + span_count * (b_eff + w_eff * nv)) / nv
                k = int(np.argmin(c))
                if c[k] < best[j]:
                    best[j] = c[k]
                    arg[j] = (int(i[k]), n)
        if not np.isfinite(best[M]):
            return _corr_partition(counts, candidate_ns, self.max_batch_size, self.device)
        groups = []
        j = M
        while j > 0:
            i_prev, n_chosen = arg[j]
            groups.append((i_prev, j, n_chosen, int(Ls[j - 1])))
            j = i_prev
        return groups[::-1], order

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

            donor = getattr(self, '_tap_donor', None)
            if self._raw_taps is not None and self._raw_taps.shape[1] >= orig_taps_max:
                group_taps = np.ascontiguousarray(self._raw_taps[tmpl_indices, :orig_taps_max])
            else:
                group_taps = np.zeros((T, orig_taps_max), dtype=self._raw_taps.dtype
                                      if self._raw_taps is not None else
                                      (np.complex64 if self.complex_taps else np.float32))
                for r, g_idx in enumerate(tmpl_indices):
                    cnt = min(int(self.tap_counts[g_idx]), orig_taps_max)
                    if self._taps_list is not None:
                        group_taps[r, :cnt] = self._taps_list[g_idx][:cnt]
                    elif donor is not None:
                        dg, dti = donor[int(g_idx)]
                        group_taps[r, :cnt] = dg._group_taps[dti, :cnt]
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
                if self.rate_ratio == 1.0 and hasattr(plan, "set_taps"):
                    # The taps themselves, for the CPU's direct refine (survivors refined at
                    # the few lags their coarse tier points to, by direct correlation, where
                    # that is priced cheaper than a whole-block transform). At other rate
                    # ratios the spectra are cut or padded and the taps are not the filter.
                    if self.binsize is not None:
                        # Fraction of blocks whose valid span touches at most max_bins output bins
                        # (4 on CPU multi-bin direct refine, 1 on GPU single-bin refine_td).
                        max_bins = 4 if plan.device.kind == "cpu" else 1
                        plan._one_bin_frac = min(
                            1.0, max(0.0, (max_bins * self.binsize - n_valid + 1) / float(self.binsize))
                        )
                        plan._unsplit_bin_frac = min(
                            1.0, max(0.0, (self.binsize - n_valid + 1) / float(self.binsize))
                        )
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
                group_taps=group_taps,
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
        """The block sizes every batch of the bank can run at (keeping at least half the block
        valid where possible, else above its longest data count), smallest first: the joint
        trial's block-size arms besides the model's layout."""
        groups, order = self._legacy_layout
        counts = self.effective_data_counts[order]
        longest = max((int(counts[j - 1]) for _, j, _, _ in groups), default=0)
        good = sorted(int(n) for n in self._choice_ns if int(n) - longest >= int(n) // 2)
        return good or sorted(int(n) for n in self._choice_ns if int(n) > longest)

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
        """The frequency-domain filter of one template.

        Parameters
        ----------
        template_index : int
            The template, as indexed in the bank's input.

        Returns
        -------
        ndarray
            The template's conjugate spectrum on its group's block length, complex64, with the
            centre tap at lag 0.
        """
        return self.filters_f[template_index]

    def get_block_length(self, template_index: int) -> int:
        """The FFT block length one template is filtered with.

        Parameters
        ----------
        template_index : int
            The template, as indexed in the bank's input.

        Returns
        -------
        int
            The block length of the template's group.
        """
        return int(self.block_lengths[template_index])

    def set_reference(
        self,
        reference: Union[np.ndarray, Dict[int, np.ndarray]],
        delta_f: Optional[float] = None,
        profile=_SAME_PROFILE,
    ) -> None:
        """Set the reference profile the hierarchical gates are calibrated with.

        Parameters
        ----------
        reference : ndarray or dict
            One of: a dict mapping block length to a 1-D reference of that length; the power
            spectrum w(f) on a fine frequency grid of spacing ``delta_f``; or a 1-D reference
            when every group has one block length.
        delta_f : float, optional
            The fine grid's frequency spacing in Hz. Required when ``reference`` is w(f).
        profile : hashable, optional
            The name of the noise profile this reference calibrates. A bank holds one
            calibration per name over one set of templates. The first reference also settles
            the block sizes; a reference under another name adds that profile's chain,
            thresholds and screeners. Default: the profile in use (the bank's only one unless
            :meth:`use_profile` or a named reference chose another).

        Raises
        ------
        ValueError
            If the reference holds no power or is not finite.
        """
        if not isinstance(reference, dict):
            # A profile with no power, or one that is not finite, is a noise spectrum that is
            # not positive anywhere or not finite (a detector with no data in the stretch):
            # said here, where the profile is named, and not as a chain that cannot be found.
            # (one sum finds both: a profile is not negative, so a sum that is positive and
            # finite has power and no value that is not finite; a top template's leaf banks
            # are given one array, which is summed once)
            w = np.asarray(reference)
            seen = _REFERENCES_WITH_POWER.get(id(reference))
            total = 1.0 if seen is not None and seen() is reference else float(w.sum())
            if not (total > 0.0 and np.isfinite(total)):
                which = "" if profile is _SAME_PROFILE else " for profile %r" % (profile,)
                raise ValueError(
                    "the reference%s holds no power or is not finite (%d of %d values positive, "
                    "%d not finite): the noise spectrum it was made from is not positive and "
                    "finite anywhere in the band, as for data that are absent or not finite"
                    % (which, int(np.count_nonzero(w > 0)), w.size,
                       int(np.count_nonzero(~np.isfinite(w)))))
            try:
                _REFERENCES_WITH_POWER[id(reference)] = weakref.ref(
                    reference, lambda _, key=id(reference): _REFERENCES_WITH_POWER.pop(key, None))
            except TypeError:
                pass                                 # not an array: checked each time
        if profile is not _SAME_PROFILE:
            if not self.__dict__.get("_refs"):
                self._first_profile = profile
            self.use_profile(profile)
        self.__dict__.setdefault("_refs", {})[self.__dict__.get("_profile")] = (reference, delta_f)
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
                on = _autotune_enabled()
                singles = self._single_sizes()[:_BLOCK_TRIAL_RANKS - 1] if on else []
                self._trial_cands = tuple(singles) + ("model",)
                w = _trial.winner(_trial_key(self)) if on else None
                self._bank_arm = w or _trial.DEFAULT
                self._in_trial = on and w is None
                v = _settings.moves(self._bank_arm).get("n")
                if w is not None:
                    # the lock's layout alone: its "n=" size, else the default (smallest) size
                    n = (None if v == "model" else v) if v is not None else (singles[0] if singles else None)
                    alt0 = self._choose_layout(fine_ref, df, single_n=n)
                    sig = [n or "model"]
                else:
                    sig = list(singles) + ["model"]
                    n0 = None if sig[0] == "model" else sig[0]
                    alt0 = self._choose_layout(fine_ref, df, single_n=n0)
                self._candidate_sig = tuple(sig)
                # Build DEFAULT's layout (rank 0) up front; any further trial candidate layouts
                # are materialized lazily in _ensure_layout only on banks sampled by _joint_round
                # (or if a non-default block-size arm wins the trial), avoiding block-size pricing
                # and duplicate plans across unsampled leaf banks while freeing raw taps now.
                if self._built is None or alt0[0] != self._built_layout:
                    self._build(*alt0)
                self._layout_rank = 0
                self.chosen_layout = [(int(e - b), int(n)) for b, e, n, _ in self._built_layout]
                self._layout_ref = (reference, delta_f)
                self._arms_ready = False
                if len(sig) >= 2:
                    self._layouts = [self._snapshot()] + [None] * (len(sig) - 1)
                    self._lazy_trial_ref = (fine_ref, df)
                else:
                    self._layouts = None
                    self._lazy_trial_ref = None
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
                profiles = {}
                for n in hier_ns:
                    ref_g = gatechain.rebin_profile(ref_arr, fine_df, self.data_sample_rate, n)
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
        self._sync_plans()

    # ---- several noise profiles ----------------------------------------------------
    # A bank's templates are searched in more than one noise -- one detector's and
    # another's -- with one calibration each: set_reference(..., profile=name) adds a
    # profile, and a filtering call names the one it runs (profile=name). The templates,
    # their grouping into block sizes and the compiled plans' template storage are the
    # bank's, once (HierarchicalFilter.use_profile).
    def _plan_profile(self, profile):
        """The name a plan holds `profile` under: None for the bank's first."""
        return None if profile == self.__dict__.get("_first_profile") else profile

    def _sync_plans(self):
        """Every built plan of the layout in use on the bank's profile."""
        key = self._plan_profile(self.__dict__.get("_profile"))
        for g in self.__dict__.get("_built") or ():
            plan = getattr(g, "_plan", None)
            if g.is_hier and plan is not None and hasattr(plan, "use_profile"):
                plan.use_profile(key)

    def use_profile(self, profile) -> None:
        """Filter with one noise profile's calibration from the next call on.

        Parameters
        ----------
        profile : hashable or None
            A name a reference was set under. None is the bank's first profile when it was set
            without a name.
        """
        if profile != self.__dict__.get("_profile"):
            self._profile = profile
            self._sync_plans()

    @property
    def profiles(self):
        """The names of the profiles a reference has been set for, in the order set."""
        return tuple(self.__dict__.get("_refs", {}))

    @property
    def _current_ref_key(self):
        return self.__dict__.get("_ref_keys", {}).get(self.__dict__.get("_profile"))

    @_current_ref_key.setter
    def _current_ref_key(self, value):
        if value is None:
            self.__dict__["_ref_keys"] = {}          # every profile's reference is to be set again
        else:
            self.__dict__.setdefault("_ref_keys", {})[self.__dict__.get("_profile")] = value

    def _reapply_references(self):
        """Give the layout in use every profile's reference (a layout built after they were set)."""
        home = self.__dict__.get("_profile")
        self._current_ref_key = None
        try:
            for name, (ref, df) in list(self.__dict__.get("_refs", {}).items()):
                self.use_profile(name)
                self.set_reference(ref, delta_f=df)
        finally:
            self.use_profile(home)

    def _ensure_layout(self, rank: int):
        """Materialize the rank-th candidate layout on demand from rank 0's group taps."""
        layouts = getattr(self, '_layouts', None)
        if not layouts or rank < 0 or rank >= len(layouts):
            return None
        if layouts[rank] is not None:
            return layouts[rank]
        cur = getattr(self, '_layout_rank', 0)
        layouts[cur] = self._snapshot()
        want = self._candidate_sig[rank]
        fine_ref, df = self._lazy_trial_ref
        alt = self._choose_layout(fine_ref, df, single_n=None if want == "model" else want)
        same = next((i for i, s in enumerate(layouts)
                     if s is not None and s.get('_built_layout') == alt[0]), None)
        if same is not None:
            layouts[rank] = layouts[same]
        else:
            prev_ref_key = getattr(self, '_current_ref_key', None)
            self._tap_donor = layouts[0]['_template_map']
            try:
                self._build(*alt)
            finally:
                self._tap_donor = None
            self._reapply_references()
            layouts[rank] = self._snapshot()
            self._restore(layouts[cur])
            self._current_ref_key = prev_ref_key
            self.chosen_layout = [(int(e - b), int(n)) for b, e, n, _ in self._built_layout]
        if all(s is not None for s in layouts):
            self._lazy_trial_ref = None
        return layouts[rank]

    def _use_layout(self, rank: int) -> None:
        """Run on the rank-th candidate layout (materialized lazily if needed). The plans differ,
        so the state version moves and recorded call plans are invalidated."""
        layouts = getattr(self, '_layouts', None)
        if not layouts or rank == getattr(self, '_layout_rank', 0) or rank >= len(layouts):
            return
        self._ensure_layout(rank)
        if layouts[rank].get('_built') is layouts[self._layout_rank].get('_built'):
            self._layout_rank = rank                  # the same partition: nothing to switch
            return
        self._layouts[self._layout_rank] = self._snapshot()
        self._restore(layouts[rank])
        self._layout_rank = rank
        self.chosen_layout = [(int(e - b), int(n)) for b, e, n, _ in self._built_layout]
        self._reapply_references()                   # this layout's groups get them, and templates
        self._state_version = getattr(self, '_state_version', 0) + 1

    def _lock_layout(self, rank: int) -> None:
        """Keep the rank-th layout and free the others, on the device too: the dropped
        layout's spectra and recordings sit in its GPU context's caches, which LRU evicts only
        under pressure -- on a small shared-memory GPU, after re-uploading live data."""
        layouts = self._layouts
        if layouts and 0 <= rank < len(layouts) and layouts[rank] is None:
            cur = getattr(self, '_layout_rank', 0)
            layouts[cur] = self._snapshot()
            want = self._candidate_sig[rank]
            fine_ref, df = self._lazy_trial_ref
            alt = self._choose_layout(fine_ref, df, single_n=None if want == "model" else want)
            same = next((i for i, s in enumerate(layouts)
                         if s is not None and s.get('_built_layout') == alt[0]), None)
            if same is None:
                # Release earlier layouts' plans before building the locked layout so peak RSS
                # never holds two layouts simultaneously on unsampled banks.
                donor_map = layouts[0]['_template_map']
                ctxs = {}
                for snap in layouts:
                    if snap is None:
                        continue
                    for g in snap.get('_built') or []:
                        p = getattr(g, '_plan', None)
                        ctx = getattr(p, '_gpu', None)
                        if ctx is not None:
                            ctxs[id(ctx)] = ctx
                        g._plan = None
                for ctx in ctxs.values():
                    ctx._drain()
                    ctx._evict_all()
                self._layouts = None
                self._lazy_trial_ref = None
                self._built = None
                self._tap_donor = donor_map
                try:
                    self._build(*alt)
                finally:
                    self._tap_donor = None
                self._layout_rank = rank
                self.chosen_layout = [(int(e - b), int(n)) for b, e, n, _ in self._built_layout]
                self._reapply_references()
                self._state_version = getattr(self, '_state_version', 0) + 1
                return
            layouts[rank] = layouts[same]
        self._ensure_layout(rank)
        self._use_layout(rank)
        # a layout another rank shares (the same partition) is the live one: compared by its
        # groups, which every snapshot of the partition holds (a snapshot is retaken on leaving)
        keep = self._layouts[rank].get('_built') if self._layouts else None
        dropped = [snap for snap in (self._layouts or [])
                   if snap is not None and snap.get('_built') is not keep]
        self._layouts = None
        self._lazy_trial_ref = None
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
        want = _settings.moves(label).get("n", sig[0])
        return sig.index(want) if want in sig else 0

    def _layout_plans(self, rank):
        """The hierarchical plans of the rank-th candidate layout."""
        if self._layouts is None or rank == self._layout_rank:
            groups = self._built or ()
        else:
            snap = self._ensure_layout(rank)
            groups = (snap.get('_built') if snap is not None else None) or ()
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
                p.arm_configs(_trial.DEFAULT)
        self._use_layout(home)
        self._arms_ready = True

    def _joint_arms(self):
        """The arms this bank proposes for its trial (_BLOCK_TRIAL_RANKS block sizes, the screen)."""
        arms = [_trial.DEFAULT] + [_settings.arm("n", n) for n in self._trial_cands[1:]]
        plans = self._layout_plans(self._arm_rank(_trial.DEFAULT))
        for p in plans:
            p.arm_configs(_trial.DEFAULT)
        if any(p._q15_ok(tuple(p._chain)) for p in plans if p._chain is not None):
            arms += [_settings.arm("q15", True), _settings.arm("q15", False)]
        return arms

    def _arm_config(self, label):
        """The configuration this bank runs for an arm: its layout (by partition) and what each
        of the layout's plans runs."""
        r = self._arm_rank(label)
        snap = self._ensure_layout(r) if self._layouts else None
        part = tuple((int(b), int(e), int(n)) for b, e, n, _ in
                     (snap.get('_built_layout') if snap is not None else self._built_layout))
        return part, tuple(p.arm_configs(label) for p in self._layout_plans(r))

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
            elif (g.is_hier and g.plan.device.kind == "cpu" and g.plan._pending_ref is not None
                  and g.plan._mf is None):
                # a further profile of loaded templates: its compiled plan, which reads the
                # first one's templates
                g.plan._ensure()
            # Solve the plan's thresholds now, with the rest of the calibration: left to the
            # first filtering call, a chain whose plan the choice did not already hold (one
            # with second-tier shared screeners) solves them inside that call.
            if g.is_hier and g.plan.device.kind == "cpu" and g.plan._pending_ref is not None:
                g.plan._resolve()

    def set_reference_from_template(
        self,
        stilde,
        psd,
        ref_template,
        f_high: Optional[float] = None
    ) -> None:
        """Set the reference profile from a template and a noise spectrum.

        The profile is |h|^2 / S (:func:`reference_profile`) between the template's ``f_lower``
        and ``f_high``, on the frequency grid of ``stilde``.

        Parameters
        ----------
        stilde : FrequencySeries
            Supplies the frequency spacing ``delta_f``.
        psd : array_like
            The noise power spectral density S on that grid.
        ref_template : array_like
            The template's frequency-domain waveform h. Its ``f_lower`` attribute, where it has
            one, is the lower cutoff.
        f_high : float, optional
            Upper frequency cutoff in Hz. Default None: none.
        """
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

    def _call_windows(self, windows, S):
        """A call's windows over a series of S samples, normalised, with their cache key.

        A slice of a given series length normalises the same way every call (a search's
        windows recur every segment), so those are memoised.

        Returns
        -------
        W : ndarray
            (K, 2) int64 merged windows (`_normalize_windows`); read-only when memoised.
        cache_key : tuple
            (S, the windows' bytes): what a group's block layout is cached under.
        """
        wkey = ((S, windows.start, windows.stop, windows.step)
                if type(windows) is slice else None)
        wmemo = self.__dict__.setdefault('_window_memo', {})
        hit = wmemo.get(wkey) if wkey is not None else None
        if hit is not None:
            return hit
        W = _normalize_windows(windows, S)
        cache_key = (S, W.tobytes())
        if wkey is not None:
            if len(wmemo) >= 64:
                wmemo.clear()
            W.flags.writeable = False
            wmemo[wkey] = (W, cache_key)
        return W, cache_key

    def _group_blocks(self, g, W, S, cache_key, single=False):
        """The blocks a template group filters for windows W of a series of S samples: each
        block's start and its searched lags (block starts, window starts, window ends), as
        `_window_layout` lays them out. The group keeps its last layout under cache_key, one
        for the bank's calls and one for single-template calls (single): a follow-up's
        windows replaced the bank calls' layout, and half the leaf calls of a pycbc GPU job
        (13,529 of 26,588) laid their blocks out again."""
        name = "_cached_single_layout" if single else "_cached_layout"
        layout = getattr(g, name, None)
        if layout is None or layout[0] != cache_key:
            bstarts, bws, bwe = self._window_layout(g, W, S)
            setattr(g, name, (cache_key, bstarts, bws, bwe))
            return bstarts, bws, bwe
        return layout[1:]

    def filter_series(
        self,
        series: np.ndarray,
        windows=None,
        binsize: Optional[int] = None,
        threshold: Optional[float] = None,
        template_index: Optional[int] = None,
        profile=_SAME_PROFILE,
    ) -> FilterResults:
        """Filter a continuous series with every template, or one, and return the peaks.

        Parameters
        ----------
        series : ndarray
            The continuous series. The hierarchical gates are calibrated for an analytic
            (positive-frequency) series, which is what pycbc passes.
        windows : slice, sequence or ndarray, optional
            Analysis windows in series coordinates: None (the whole series), a slice, a
            sequence of slices or (start, stop) pairs, or a (K, 2) integer array. Python slice
            rules apply. Overlapping or touching windows merge, so the result depends only on
            the union of samples, and a block no window intersects is not computed. Each peak
            search stays inside its window. Padding for filter context is the caller's job.
        binsize : int, optional
            Samples per peak bin. Defaults to the bank's ``binsize``, else the block length (one
            bin per block).
        threshold : float, optional
            SNR threshold for this call. Default None: the bank's.
        template_index : int, optional
            Filter only this template. Default None: every template.
        profile : hashable, optional
            The noise profile whose calibration the call runs with. Default: the one in use.

        Returns
        -------
        FilterResults
            One entry per peak above the threshold: the template's index in the bank's input,
            the sample index in the series, the complex SNR, and the start and length of the
            block that found it.
        """
        if profile is not _SAME_PROFILE:
            self.use_profile(profile)
        # One template on the CPU (a search's follow-up, PeaksContext.refilter): the batched
        # follow-up path, as a batch of one. It reads the series in place (real, or one lane
        # of a packed pair), lays the blocks out and merges the bins in C, and keeps the
        # template's taps and spectrum on the group. The call-at-a-time path below did the
        # layout, the grouping and the bin merge in Python around a one-template plan: 1.2 ms
        # a call against 0.2 ms (Zen 5, replay of a search's refilter calls,
        # tools/bench_refilter.py). It remains for what the batch declines (a resampled
        # bank, a GPU group, a wrapped plan).
        if template_index is not None and not getattr(self, '_defer', False):
            res = _batches._cpu_single_td_one(self, series, windows, binsize, threshold,
                                              template_index)
            if res is not None:
                return res
            res = self._single_locked_cpu(series, windows, binsize, threshold, template_index)
            if res is not None:
                return res

        ser = self._input_series(series)
        if ser.ndim != 1:
            raise ValueError("series must be a 1D array")
        S = len(ser)

        W, cache_key = self._call_windows(windows, S)
        if W.shape[0] == 0:
            return _EMPTY_FILTER_RESULTS

        if template_index is not None:
            if template_index < 0 or template_index >= self.n_templates:
                raise IndexError(f"template_index {template_index} out of range [0, {self.n_templates})")
            played = self._single_play(series, windows, binsize, threshold, template_index, W)
            if played is not None:
                return played
            if (self.engine == 'hier' and not getattr(self, '_defer', False)
                    and _device.parse(self.device).kind == 'gpu'):
                # A GPU bank's call that runs on the CPU side (its call shape's lock, or a
                # play's CPU arm) takes the CPU banks' batched follow-up path, as a batch of
                # one: 0.2 ms a call where the one-template plan below took 0.5-0.7.
                g, _ = self._template_map[template_index]
                if self._single_device(g, self._group_blocks(g, W, S, cache_key, True)[0].size)[0]:
                    single_out = [None]
                    if _batches._cpu_single_td_batch(
                            [(self, series, dict(windows=windows, binsize=binsize,
                                                 threshold=threshold,
                                                 template_index=template_index))],
                            single_out, force_cpu=True):
                        return single_out[0]

        eff_threshold = self.threshold if threshold is None else float(threshold)
        if template_index is None and not getattr(self, '_defer', False) and self.engine == 'hier':
            single_out = [None]
            if _batches._cpu_sparse_batch(
                None, single_out,
                pre_jobs=[(0, self, ser, W, cache_key, binsize, eff_threshold)],
            ):
                return single_out[0]

        # The peaks' columns, filled by _consume_into and read by _results_from.
        lists = ([], [], [], [], [])
        # A bin size the caller (or the bank) gives is each window's: its bins start at the
        # window's start, wherever the blocks fall (_window_bin_phases). A bin a block edge
        # cuts comes back as two partial bins, merged in build(). Without one, a bin is the
        # block's span (the documented default, one bin per block).
        aligned = binsize is not None or self.binsize is not None
        merge_bs = []

        if template_index is not None:
            self._groups
            target_g, ti_local = self._template_map[template_index]
            work_items = [(target_g, (ti_local, 1))]
        else:
            work_items = [(g, None) for g in self._groups]

        # In a batch (filter_series_many): its token, and this job's compute queue offset.
        defer, queue_offset = getattr(self, '_defer', False), getattr(self, '_queue_offset', 0)
        pending = []
        for g, tmpl_arg in work_items:
            plan_templates = tmpl_arg
            timed = False
            if self.engine == 'hier' and tmpl_arg is not None:
                # one template ungated: a plan holding just it, not the group's whole ungated
                # bank -- on whichever device runs this call shape faster
                nblocks = self._group_blocks(g, W, S, cache_key, True)[0].size
                on_cpu, timed = self._single_device(g, nblocks)
                active_plan = g.get_single_plan(tmpl_arg[0], on_cpu=on_cpu)
                plan_templates = None
            elif self.engine == 'hier' and (eff_threshold < self.threshold or eff_threshold <= 0.0):
                active_plan = g.get_flat_plan()
            else:
                active_plan = g.plan
            # The plan's calls defer in a batch (_series_flags), except a timed one (a play's).
            call_defer = False if timed else defer
            if getattr(active_plan, '_gpu', None) is None:
                # A host plan reads the series on the host: device writes left in flight
                # to it (correlate_series(wait=False)) must land first.
                _settle_device_writes()

            N = g.n
            bstarts, bws, bwe = self._group_blocks(g, W, S, cache_key, tmpl_arg is not None)
            if bstarts.size == 0:
                continue

            data_in = ser

            bs = int(binsize) if binsize is not None else (self.binsize or N)
            bph = None
            if aligned:
                bph = _bin_phases(g, active_plan, W, cache_key, bs, bstarts, bws, bwe)
                if bph is not None and bs not in merge_bs:
                    merge_bs.append(bs)
            # A repeat of a deferred call this group's plan has made before goes straight to
            # the plan's recorded call plan: no bin grouping, layout or key building. The
            # plan validates everything (layout identity, state, series memory, records);
            # on a miss the full call below runs and records again.
            fast_key = None
            if (self.engine == 'hier' and tmpl_arg is None and defer and not timed
                    and active_plan is g.plan and getattr(active_plan, '_gpu', None) is not None
                    and hasattr(active_plan, '_fast_series')):
                fast_key = (cache_key, bs, eff_threshold)
                fast = g.__dict__.get('_fast_calls')
                hit = fast.get(fast_key) if fast else None
                if hit is not None and hit[0] is active_plan:
                    with active_plan._series_flags(defer=call_defer, sparse=True,
                                                   queue_offset=queue_offset):
                        res = active_plan._fast_series(data_in, hit[1], bs, eff_threshold)
                    if res is not None:
                        if hit[2] is None:
                            pending.append((res, bstarts, g, tmpl_arg, N))
                        else:
                            split, starts_parts = hit[2]
                            for d, st_part in zip(split.deferred(res), starts_parts):
                                pending.append((d, st_part, g, tmpl_arg, N))
                        continue
            groups_bins = _blocks_by_bin_count(active_plan, N, bs, bstarts, bws, bwe, bph)

            # Every bin count in one GPU submission where the backend can, instead of a
            # submission and a wait per count (see MatchedFilter._run_series_ragged).
            work = [(gb, None) for gb in groups_bins]
            if (len(groups_bins) > 1 and getattr(active_plan, '_gpu', None) is not None
                    and not getattr(active_plan, '_bandlimited', False)
                    and hasattr(active_plan, '_run_series_ragged')):
                # A hierarchical ragged call reads back sparse, as its per-count calls would.
                with active_plan._series_flags(
                        defer=call_defer, sparse=getattr(active_plan, '_is_hierarchical', False),
                        queue_offset=queue_offset):
                    res = active_plan._run_series_ragged(
                        data_in, bstarts, bws, bwe, binsize=bs,
                        threshold=eff_threshold, templates=plan_templates,
                        **({} if bph is None else {'bin_phase': bph}))
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
            for (sub_starts, sub_bws, sub_bwe, sub_ph), res in work:
                if res is None:
                    run_in, run_starts = data_in, sub_starts
                    if data_in.dtype == np.float32 and not _reads_real(active_plan):
                        # A plan without a real-series path (the ungated single-template plan
                        # of a follow-up) widens to complex only the span its blocks read --
                        # not the whole series, which was 4.7 s of copies over a test27 job.
                        lo = int(sub_starts.min())
                        hi = min(S, int(sub_starts.max()) + N)
                        run_in = _host_copy(data_in[lo:hi], np.complex64)
                        run_starts = (sub_starts - lo).astype(sub_starts.dtype)
                    with active_plan._series_flags(defer=call_defer, sparse=True,
                                                   queue_offset=queue_offset):
                        res = active_plan.run_series(
                            run_in, run_starts, sub_bws, sub_bwe, binsize=bs,
                            threshold=eff_threshold, templates=plan_templates, raw=True,
                            **({} if sub_ph is None else {'bin_phase': sub_ph})
                        )
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
                _consume_into(lists, aidx, aval, sub_starts, g, tmpl_arg, N, template_index)

        def build():
            for d, sub_starts, g, tmpl_arg, N in pending:
                res = d.result()
                if not d.empty:
                    _consume_into(lists, *((res, None) if isinstance(res, _SparsePeaks) else res),
                                  sub_starts, g, tmpl_arg, N, template_index)
            if merge_bs and lists[0]:
                # Partial bins (a block edge inside a window bin) into their window bins.
                cols = [np.concatenate(c) for c in lists]
                for bs_m in merge_bs:
                    cols = list(_merge_window_bins(W, bs_m, *cols))
                for lst, c in zip(lists, cols):
                    lst[:] = [c]
            return _results_from(lists)

        return _Deferred(build) if pending else build()

    def empty_shared(self, shape, dtype=np.complex64, input=False):
        """An array in this bank's device memory that the host can read, for reused buffers.

        :meth:`correlate_series` writes such an array in place (``out=``), and a bank on the
        same device reads its rows in place. On a CPU bank it is ordinary page-aligned memory.

        Parameters
        ----------
        shape : tuple of int
            The array's shape.
        dtype : dtype, optional
            The array's dtype (default complex64).
        input : bool, optional
            True for an input series the host rewrites before every call: the backend may keep
            it in host memory the device maps, rather than moving it each call. Default False.

        Returns
        -------
        ndarray
            The array. Its contents are not initialised.
        """
        self._groups
        for g in self._groups:
            plan = g.get_correlation_plan() if self.engine == 'corr' else g.plan
            gpu = getattr(plan, '_gpu', None)
            if gpu is not None:
                if input:
                    return gpu.empty_shared(tuple(shape), dtype, host_input=True)
                return gpu.empty_shared(tuple(shape), dtype, readback=True)
        return _page_aligned_empty(tuple(shape), dtype)

    def _single_play(self, series, windows, binsize, threshold, template_index, W):
        """A single-template call on a GPU bank, played on both sides (the result), or None
        where it is not: the call runs as decided (_single_device).

        A follow-up filters one template over a few dozen blocks: a GPU call is then all
        fixed cost (submission, recording for its window, readback, the wake from idle),
        which a CPU core undercuts by far. Neither side is assumed: per call shape (device,
        block size, block count) a paired _choice.Choice plays the call on the GPU plan and on
        a CPU plan (Choice.play), synchronously, and its lock holds for every bank, and for
        later processes through MF_COST_FILE. A batch's single-template jobs follow the device
        trial instead (_settings "single", _items_batch): batched, the GPU call is another
        dispatch. MF_AUTOTUNE=0 or MF_SINGLE_DEVICE=bank keeps the bank's device.

        Each side's timed run is its first run of the call, with no untimed run before it
        (Choice.play's warm): production never repeats a follow-up -- each is another
        template over another window -- so what it pays is a first run (the template's
        upload, the window's recording, the wake from idle). A warmed repeat timed the 8060S
        at 0.31 ms a call against the CPU's 0.32 and kept the GPU, where its calls in the
        171,828-template pycbc job cost about 2 ms against the CPU's 0.22 (2026-11-25)."""
        if (self.engine != 'hier' or _device.parse(self.device).kind != 'gpu'
                or not _autotune_enabled() or _config.get("MF_SINGLE_DEVICE") == "bank"
                or "_single_force" in self.__dict__ or playing()):
            return None
        g, _ = self._template_map[template_index]
        nblocks = int(self._window_layout(g, W, len(series))[0].size)
        ch = _single_choice(self.device, g.n, nblocks)
        if ch.winner is not None:
            return None

        def run(label):
            self._single_force, self._single_timed = _side_of(label), True
            try:
                return self.filter_series(series, windows=windows, binsize=binsize,
                                          threshold=threshold, template_index=template_index)
            finally:
                del self._single_force, self._single_timed
        ran = self.__dict__.setdefault("_single_ran", {}).setdefault(ch.store_key, set())
        return ch.play(run, ran, warm=lambda label: None)

    def _single_locked_cpu(self, series, windows, binsize, threshold, template_index):
        """A GPU bank's single-template call whose call shape is locked to the CPU side, run
        there at once (the batched follow-up path), or None for every other call.

        The general path reaches the same run after laying out the window twice (for
        _single_play, which finds the lock and steps aside, and for _single_device) and
        trying the CPU batch twice: about 70 us a call of Python in the 171,828-template pycbc
        job on the 8060S (instrumented), against 170 us for the follow-up's filtering. Here a
        lone slice window's block count comes from its bounds; the choice, the lock and the
        run are the general path's."""
        if (self.engine != 'hier' or type(windows) is not slice
                or not (windows.step is None or windows.step == 1)
                or not (windows.start is None or type(windows.start) is int)
                or not (windows.stop is None or type(windows.stop) is int)
                or not isinstance(series, np.ndarray) or series.ndim != 1
                or "_single_force" in self.__dict__
                or _device.parse(self.device).kind != 'gpu' or not _autotune_enabled()
                or _config.get("MF_SINGLE_DEVICE") == "bank" or playing()):
            return None
        ti = int(template_index)
        if ti < 0 or ti >= self.n_templates:
            return None
        S = len(series)
        v0, v1, _ = windows.indices(S)
        if v1 <= v0:
            return None
        self._groups
        g, _ = self._template_map[ti]
        # the blocks _window_layout lays out for the one window [v0, v1)
        step, c_bad = g.n_valid, g.c_bad
        first = max(0, (v0 - c_bad) // step) * step
        lim = min(S, v1 - c_bad)
        nblocks = (lim - first + step - 1) // step if lim > first else 0
        w = _single_choice(self.device, g.n, nblocks).winner
        if w is None or _side_of(w) != "cpu":
            return None
        return _batches._cpu_single_td_one(self, series, windows, binsize, threshold, ti,
                                           force_cpu=True)

    def _single_device(self, g, nblocks):
        """(on_cpu, timed) for a single-template call on group g: the side a play runs
        (_single_play), else the locked choice for this call shape, else the bank's device;
        timed while a play runs it (the call is then waited on, not deferred)."""
        force = self.__dict__.get("_single_force")
        if force is not None:
            return force == "cpu", bool(self.__dict__.get("_single_timed"))
        if _device.parse(self.device).kind != 'gpu' or _config.get("MF_SINGLE_DEVICE") == "bank":
            return False, False
        w = _single_choice(self.device, g.n, nblocks).winner
        return w is not None and _side_of(w) == "cpu", False

    @staticmethod
    def filter_series_many(jobs, wait=True):
        """Run several :meth:`filter_series` calls as one batch.

        On a GPU every call is submitted before any is collected and each job's work has its own
        compute queue, so the device runs banks concurrently and the host waits once. On a CPU
        the calls run in order. The results equal those of calling each job in turn.

        Parameters
        ----------
        jobs : sequence of tuple
            ``(bank, series, kwargs)`` per call, kwargs as :meth:`filter_series` takes them.
        wait : bool, optional
            True (default) returns the results. False returns, per job, an object whose
            ``result()`` gives them, so the GPU keeps working while the caller prepares the next
            batch. The jobs' series must not be overwritten until then. A later batch on the
            same banks first finishes whatever of this one it would overwrite.

        Returns
        -------
        list
            Per job, its FilterResults, or with ``wait=False`` the object that gives them.
        """
        paired = _joint_round(jobs)
        if paired is not None:
            return paired if wait else [_Deferred(lambda r=r: r) for r in paired]
        res = _gpu_batch(jobs, lambda: _batches._run_batch(jobs, wait or playing()))
        if not wait:
            # a played batch ran waited (its arms are timed to their last result)
            res = [r if isinstance(r, _Deferred) else _Deferred(lambda r=r: r) for r in res]
        return res

    #: Default L3-resident middle-output tile target in bytes for CPU
    #: correlate_and_filter_many execution (0 disables tiling).
    _TILE_BYTES = 4 << 20
    _STREAM_HOOKS = None

    @staticmethod
    def correlate_and_filter_many(corr_jobs, leaf_jobs, wait=True, timings=None,
                                  tile_bytes=None, retain_radius=None,
                                  retain_threshold=None):
        """Correlate middle-stage banks and filter dependent leaf banks in L3-resident tiles.

        On CPU when ``wait`` is True and no joint autotuning trial is open, correlation jobs
        that share a middle bank and window layout are grouped into multi-detector cohorts
        and executed row-by-row in L3-resident sample chunks. Each middle block's forward
        transform is computed once per input series and reused across the group's templates,
        writing into a persistent L3-resident scratch buffer that all dependent leaf banks
        filter immediately across all detectors before moving to the next row. Any GPU,
        deferred, trial-playing, or non-sparse job falls back cleanly to untiled
        ``correlate_series`` and ``filter_series_many``.

        Parameters
        ----------
        corr_jobs : sequence of tuple
            Sequence of ``(corr_bank, series, kwargs)`` items passed to ``correlate_series``.
            To couple with ``leaf_jobs``, ``kwargs["out"]`` must be the preallocated 2D
            C-contiguous ``complex64`` array whose rows or real/imag lanes appear in
            ``leaf_jobs``.
        leaf_jobs : sequence of tuple
            Sequence of ``(leaf_bank, series, kwargs)`` items passed to
            ``filter_series_many``.
        wait : bool, optional
            Whether to wait for device jobs before returning (default True). When False,
            executes untiled and returns deferred result handles.
        timings : dict, optional
            Mutable mapping populated in place with ``"correlate"`` (total correlation wall
            seconds), ``"correlate_per_job"`` (list of per-``corr_job`` wall seconds),
            ``"filter"`` (total leaf-filtering wall seconds), and ``"ephemeral_used"``
            (True when ``retain_radius == 0`` skipped writing ``out``).
        tile_bytes : int, optional
            Target byte footprint per L3-resident middle-row chunk (default ``None``, which
            uses ``_TILE_BYTES`` when the cohort's active middle output fits within the L3
            budget and falls back to untiled non-temporal streaming on oversized full-segment
            cohorts). Passing a positive integer forces tiled execution at that chunk budget;
            passing ``0`` disables tiling and runs untiled ``correlate_series`` followed by
            ``filter_series_many``.
        retain_radius : int, optional
            Controls how much of each ``kwargs["out"]`` array is materialized in DRAM:
            ``None`` (default) writes every sample so ``out`` is byte-for-byte identical to
            ``correlate_series``; ``0`` treats ``out`` as an addressing descriptor only and
            writes nothing to DRAM; a positive integer ``R`` writes ``[c0 - R, c0 + R)``
            around every leaf peak with ``|snr| >= retain_threshold`` across the cohort.
        retain_threshold : float, optional
            Minimum ``|snr|`` of leaf peaks that trigger ``retain_radius`` retention when
            ``retain_radius > 0`` (default ``0.0``).

        Returns
        -------
        list of FilterResults
            One ``FilterResults`` (or deferred handle when ``wait=False``) per entry in
            ``leaf_jobs``, bit-for-bit identical in order and content to calling
            ``correlate_series`` on each ``corr_jobs`` entry followed by
            ``filter_series_many(leaf_jobs, wait=wait)``.
        """
        return _batches.correlate_and_filter_many(
            corr_jobs, leaf_jobs, wait, timings, tile_bytes, retain_radius, retain_threshold)

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
                tmp = _page_aligned_empty((nt, S), dtype=np.complex64)
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
            # The views' owners: shared_buffer() recognises an array only while its owner
            # lives, so both are held until the call returns, and dropped before the arrays.
            owners = [out_owner, view(ser) if ser.flags.writeable else None]
            del out_owner
            try:
                cplan._continuous_gpu(ser, st, t0, nt, dest)
            finally:
                owners.clear()
            return
        # A destination in device memory on this device (a caller's reused buffer) is
        # written in place: no workspace, no copy-out.
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
        need_gpu = (W.shape[0] > 0 or getattr(g, '_corr_plan', None) is not None
                    or _device.parse(self.device).kind == 'gpu')
        gpu = getattr(g.get_correlation_plan(), '_gpu', None) if need_gpu else None
        if gpu is not None and settle:
            q = getattr(gpu, 'queue', None)
            if q is not None:
                for prev in settle:
                    if getattr(prev, 'queue', None) is q:
                        gpu = prev
                        break
        zero = gpu.zero_columns if gpu is not None else None
        if zero is not None:
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
        """Correlate a continuous series with every template, one, or a list of them.

        Templates are filtered at their groups' block lengths. Rows are in the bank's template
        order.

        Parameters
        ----------
        series : ndarray
            The continuous series, 1-D complex64.
        windows : slice, sequence or ndarray, optional
            Analysis windows in series coordinates, in the forms :meth:`filter_series` takes.
            Only blocks a window intersects are computed. The output holds the correlation
            inside the union of the windows and exact zeros everywhere else. Padding for filter
            context is the caller's job.
        scales : ndarray or sequence of float, optional
            Per-template scale factors: one per template, or one with ``template_index``.
        template_index : int, optional
            Correlate only this template; the result is then 1-D.
        out : ndarray, optional
            Preallocated complex64 output: ``(n_templates, len(series))``, or with
            ``template_index`` ``(len(series),)`` or ``(1, len(series))``. Every sample is
            written, so it need not be cleared. Default None: a new array.
        wait : bool, optional
            False, with ``out`` from :meth:`empty_shared` on a backend that can (Vulkan),
            returns once the work is submitted. Later work on the same device, such as
            :meth:`filter_series_many` reading ``out``, is ordered after it. Call :meth:`wait`
            before reading ``out`` on the host. Default True.
        templates : sequence of int, optional
            Distinct template indices: output row j is template ``templates[j]``. Templates
            adjacent both here and in a block-size group share one call, which transforms each
            block once for all of them, so list them in ascending order.
        out_support : optional
            With ``out``: where ``out`` may hold nonzero values on entry, in the forms
            ``windows`` takes. Elsewhere it is taken to be zero already and is not written. A
            caller reusing ``out`` passes the windows of the call that last filled it. Default
            None: all of ``out`` is written.

        Returns
        -------
        ndarray
            complex64, ``(n_templates, len(series))``, ``(len(templates), len(series))``, or with
            ``template_index`` ``(len(series),)``. It is ``out`` when that was given.
        """

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
                    and _device.parse(self.device).kind != 'cpu')
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
        w_span = int((W[:, 1] - W[:, 0]).sum())
        self._add_corr_in(w_span)

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
                out_2d, support = self._alloc_corr_output((1, S), S, w_span)

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
            result, support = self._alloc_corr_output(shape, S, w_span)

        settle = []
        ok = False
        try:
            self._correlate_bank(ser, W, scales_arr, result, settle, support)
            ok = True
        finally:
            gpus = list({id(x): x for x in settle}.values())
            for gpu in gpus:
                gpu.zero_columns_done(wait=False)
            if not (ok and not wait):
                for gpu in gpus:
                    gpu.settle_writes()
                    gpu._x_idle()
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
        gpus = []
        for g in self._groups:
            gpu = getattr(g.get_correlation_plan(), '_gpu', None)
            if gpu is None:
                return ser
            gpus.append(gpu)
        if len(gpus) < 2 or getattr(gpus[0], 'host_view', None) is not None:
            return ser                       # one group, or unified memory read in place
        if all((containing_samples(ser, gpu) if ser.dtype == np.float32
                else shared_buffer(ser, gpu)) is not None for gpu in gpus):
            return ser                       # read in place (a real series by its layout)
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
        if _device.parse(self.device).kind == 'cpu':
            return True
        self._groups
        return all(_gpu_reads_real(g.get_correlation_plan()._gpu, g.n) for g in self._groups)

    def _alloc_corr_output(self, shape, S: int, w_span: int):
        """Allocate a correlation output array and its initial dirty-region support.

        On CPU when windows cover more than half of S, uninitialized page-aligned memory backed
        by a 1-slot weakref-finalized pool avoids both user-space zero-fill and >32 MiB glibc
        mmap/munmap kernel page-fault zeroing once an earlier result and all views over it are
        freed, while _correlate_windows clears only unwritten margins. Sparse windows and GPU
        outputs retain calloc zero-page backing so untouched pages are never faulted.
        """
        dtype = np.dtype(np.complex64)
        nbytes = int(np.prod(shape)) * dtype.itemsize
        if nbytes > 0 and _device.parse(self.device).kind == 'cpu' and w_span > S // 2:
            page = 16384
            need = nbytes + page
            pool = self.__dict__.setdefault('_corr_out_pool', [])
            raw = None
            while pool:
                try:
                    cand = pool.pop()
                except IndexError:
                    break
                if cand.size >= need:
                    raw = cand
                    break
            if raw is None:
                raw = np.empty(need, dtype=np.uint8)
            off = (-raw.ctypes.data) % page
            owner = _RecycledBuffer(raw, off, shape, dtype)
            wself = weakref.ref(self)

            def _return_raw(buf=raw, bank_ref=wself):
                bank = bank_ref()
                if bank is not None:
                    free_list = bank.__dict__.get('_corr_out_pool')
                    if free_list is not None and len(free_list) < 1:
                        free_list.append(buf)

            weakref.finalize(owner, _return_raw)
            return np.asarray(owner), None
        return (_aligned_zeros(shape, dtype=dtype, align=16384),
                np.empty((0, 2), dtype=np.int64))

    def _correlate_selected(self, ser, W, templates, scales, out, support=None, wait=True):
        """correlate_series(templates=...): row j of the result is template templates[j]."""
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
            w_span = int((W[:, 1] - W[:, 0]).sum())
            result, support = self._alloc_corr_output(shape, S, w_span)
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
            gpus = list({id(x): x for x in settle}.values())
            for gpu in gpus:
                gpu.zero_columns_done(wait=False)
            if not (ok and not wait and scales is None):
                for gpu in gpus:
                    gpu.settle_writes()
                    gpu._x_idle()
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
                g_dest = _page_aligned_empty((g_cnt, S), dtype=np.complex64)
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


def _dif_plan(plan):
    """Whether plan is a band-limited flat plan (two-channel decimation in frequency), whose
    windows and bins are counted on its half-rate grid."""
    return (getattr(plan, '_bandlimited', False)
            and not getattr(plan, '_is_hierarchical', False))


def _bin_phases(g, plan, W, cache_key, bs, bstarts, bws, bwe):
    """Each block's bin phase for windows W at bin size bs, or None where every window's
    bins already start at its blocks' window starts (`_window_bin_phases`).

    Every entry is padded to the call's largest bin count: an entry with fewer bins starts
    its numbering whole bins earlier (empty bins before its window), so the group is one
    call rather than one per bin count; each call pays its setup and the Q15 screen's
    preparation again. The group memoises the phases under (cache_key, bs)."""
    pkey = ('_bin_phase', cache_key, bs)
    memo = g.__dict__.setdefault('_phase_memo', {})
    if pkey not in memo:
        if len(memo) >= 16:
            memo.clear()
        ph = _window_bin_phases(W, bstarts, bws, bs)
        if ph is not None:
            w_end = (np.minimum(bwe, g.n) if _dif_plan(plan) else bwe).astype(np.int64)
            counts = (w_end - bws.astype(np.int64) + ph.astype(np.int64) + bs - 1) // bs
            ph = (ph.astype(np.int64) + bs * (counts.max() - counts)).astype(np.uint32)
        memo[pkey] = ph
    return memo[pkey]


def _blocks_by_bin_count(plan, N, bs, bstarts, bws, bwe, bph):
    """A group's blocks as the calls that filter them: [(starts, window starts, window
    ends, bin phases or None)], the blocks of one call having one bin count. With bin
    phases the blocks are one call (the phases pad every block to the same count); so are
    they when a bin is at least a block."""
    if bph is not None:
        return [(bstarts, bws, bwe, bph)]
    if _dif_plan(plan):
        bs_k = max(1, bs // 2) if bs < N else N // 2
        wk_s = (bws // 2).astype(np.int64)
        wk_e = ((np.minimum(bwe, N) + 1) // 2).astype(np.int64)
        return _bin_count_groups(
            bstarts, bws, bwe, np.maximum(1, (wk_e - wk_s + bs_k - 1) // bs_k))
    if bs >= N:
        return [(bstarts, bws, bwe, None)]
    return _bin_count_groups(bstarts, bws, bwe, ((bwe - bws + bs - 1) // bs).astype(np.int64))


def _bin_count_groups(bstarts, bws, bwe, bin_counts):
    """Returns the blocks split into run_series calls of one bin count each: a list of
    (starts, window starts, window ends, None), one per bin count in increasing order, or
    one entry holding every block when they all have the same count."""
    if len(bstarts) <= 1 or np.all(bin_counts == bin_counts[0]):
        return [(bstarts, bws, bwe, None)]
    groups = []
    for u in np.unique(bin_counts):
        m = bin_counts == u
        groups.append((bstarts[m], bws[m], bwe[m], None))
    return groups


def _consume_into(lists, aidx, aval, sub_starts, g, tmpl_arg, N, template_index):
    """Append the peaks of one run_series result of shape (nblocks, ntemplates, nbins) to
    lists, the five columns of a FilterResults, in the result's C order (block, template,
    bin). Returns nothing.

    The result is dense, aidx and aval arrays of that shape (aidx -1 in an empty bin), or
    sparse, a _SparsePeaks as aidx and aval None. Blocks start at sub_starts and are N long.
    With tmpl_arg given the call filtered one template, whose peaks are template_index's;
    otherwise template t of the result is group g's template g.template_indices[t]."""
    ti_out, si_out, snr_out, ts_out, bl_out = lists
    if aval is None:
        if aidx.flat.size == 0:
            return
        nt, nb = aidx.shape[1], aidx.shape[2]
        bi, rest = np.divmod(aidx.flat, nt * nb)
        ti = rest // nb
        si, snr = sub_starts[bi] + aidx.idx, aidx.val
    else:
        bi, ti, bini = np.nonzero(aidx >= 0)
        if not bi.size:
            return
        t = 0 if tmpl_arg is not None else ti
        si, snr = sub_starts[bi] + aidx[bi, t, bini], aval[bi, t, bini]
    ti_out.append(np.full(bi.size, template_index, dtype=np.int64) if tmpl_arg is not None
                  else g.template_indices[ti])
    si_out.append(si)
    snr_out.append(snr)
    ts_out.append(sub_starts[bi])
    bl_out.append(np.full(bi.size, N, dtype=np.int64))


def _results_from(lists):
    """Returns the FilterResults of the columns _consume_into filled, or the empty result
    when they hold no peaks. A column of one chunk is that chunk itself where its dtype
    already matches, not a copy; a column of several chunks is their concatenation."""
    ti, si, snr, ts, bl = lists
    if not ti:
        return _EMPTY_FILTER_RESULTS
    join = (lambda c: c[0]) if len(ti) == 1 else np.concatenate
    return FilterResults(
        template_indices=join(ti).astype(np.int64, copy=False),
        sample_indices=join(si).astype(np.int64, copy=False),
        snr=join(snr).astype(np.complex64, copy=False),
        block_starts=join(ts).astype(np.int64, copy=False),
        block_lengths=join(bl).astype(np.int64, copy=False),
    )


# The batch machinery reads this module's helpers, so it is imported last; the class's
# batch methods reach it when they are called.
from . import _batches
