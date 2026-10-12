"""TimeDomainFilterBank: Ingest raw time-domain filters, dynamically partition by length,
automatically select optimal FFT block sizes, and filter continuous series."""

import math
from collections import OrderedDict
import os
import time
from typing import Any, NamedTuple, Optional, Sequence, Union, Tuple, List, Dict
import sys
import numpy as np
try:
    from . import _core
except ImportError:
    _core = None



class FilterResults(NamedTuple):
    template_indices: np.ndarray   # int64: index into original input templates
    sample_indices: np.ndarray     # int64: sample index in continuous series
    snr: np.ndarray                # complex64: peak complex SNR
    block_starts: np.ndarray       # int64: start sample index of the block
    block_lengths: np.ndarray      # int64: FFT block length used for this template


_EMPTY_FILTER_RESULTS = FilterResults(
    template_indices=np.empty(0, dtype=np.int64),
    sample_indices=np.empty(0, dtype=np.int64),
    snr=np.empty(0, dtype=np.complex64),
    block_starts=np.empty(0, dtype=np.int64),
    block_lengths=np.empty(0, dtype=np.int64),
)


def _is_index(x) -> bool:
    return isinstance(x, (int, np.integer)) and not isinstance(x, (bool, np.bool_))


def _settle_metal_writes():
    """Wait for Metal writes left in flight (zero_columns_done(wait=False)) before a host
    read. Metal orders its own contexts on the GPU, so only host readers wait."""
    import sys
    mtl = sys.modules.get(__package__ + '._mtlcompute')
    if mtl is not None:
        mtl.settle_all()


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
        from . import _SparsePeaks
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
        from . import _Deferred
        cell = []

        def part(i):
            if not cell:
                cell.append(self.parts(d.result()))
            return cell[0][i]
        return [_Deferred(lambda i=i: part(i)) for i in range(len(self.us))]


def _normalize_windows(windows, S: int) -> np.ndarray:
    """Analysis windows as a sorted, disjoint int64 (K, 2) array of [start, stop).

    Accepts None (the whole series), a slice, a sequence of slices or
    (start, stop) pairs, or a (K, 2) integer array.  Each interval follows
    Python slice rules (None, negative indices, clipping to [0, S]); empty ones
    are dropped and overlapping or touching ones merged, so the result depends
    only on the union of samples.  A bare pair [a, b] is rejected: it is
    ambiguous, and slice(a, b) or [(a, b)] says it plainly."""
    if windows is None:
        return np.array([[0, S]], dtype=np.int64) if S > 0 else np.empty((0, 2), dtype=np.int64)
    if isinstance(windows, slice):
        items = [windows]
    elif isinstance(windows, np.ndarray):
        if windows.ndim != 2 or windows.shape[1] != 2:
            raise ValueError(f"windows array must have shape (K, 2), got {windows.shape}")
        if windows.dtype.kind not in "iu":
            raise TypeError(f"windows array must be integer, got dtype {windows.dtype}")
        items = [(int(a), int(b)) for a, b in windows.tolist()]
    else:
        try:
            items = list(windows)
        except TypeError:
            raise TypeError("windows must be None, a slice, a sequence of slices or "
                            "(start, stop) pairs, or a (K, 2) integer array") from None
        if len(items) == 2 and all(_is_index(x) for x in items):
            raise ValueError("windows=[a, b] is ambiguous; pass slice(a, b) or [(a, b)]")
    pairs = []
    for it in items:
        if isinstance(it, slice):
            if it.step not in (None, 1):
                raise ValueError("window slices must have step 1")
            for v in (it.start, it.stop):
                if v is not None and not _is_index(v):
                    raise TypeError(f"window bounds must be integers, got {v!r}")
            sl = it
        else:
            try:
                seq = tuple(it)
            except TypeError:
                raise TypeError(f"each window must be a slice or a (start, stop) pair, got {it!r}") from None
            if len(seq) != 2 or not all(_is_index(v) for v in seq):
                raise TypeError(f"each window must be a slice or an integer (start, stop) pair, got {it!r}")
            sl = slice(int(seq[0]), int(seq[1]))
        a, b, _ = sl.indices(S)
        if b > a:
            pairs.append((a, b))
    if not pairs:
        return np.empty((0, 2), dtype=np.int64)
    pairs.sort()
    merged = [list(pairs[0])]
    for a, b in pairs[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return np.asarray(merged, dtype=np.int64)


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
    """Intersection of two sorted disjoint run lists."""
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


def _partition_templates(
    counts: np.ndarray,
    max_batch: Optional[int] = None,
    candidate_ns: Sequence[int] = (2048, 4096, 8192, 16384, 32768, 65536),
    engine: Optional[str] = None,
    device: Optional[Any] = None,
    n_sorted: Optional[np.ndarray] = None,
    **kwargs: Any,
) -> Tuple[List[Tuple[int, int, int, int]], np.ndarray]:
    """Partition templates sorted by length into homogeneous, balanced sub-batches.

    Avoids over-fragmentation by keeping sub-batches sized according to the L2 cache
    budget (up to 256 templates fitting inside 512 KB L2 cache) when max_batch is None, or
    bounded by max_batch if explicitly specified. Selects FFT block sizes based on
    filter length to guarantee high efficiency (valid fraction >= 50%) while
    maximizing L1/L2 cache hit rates and SIMD lane utilization.

    n_sorted, when given, is the block size of each template in sorted order (a
    choice made elsewhere, e.g. by cost); runs then follow it instead of the
    valid-fraction rule.

    Returns:
        (groups, sort_order)
        where each group is a tuple: (start_idx, end_idx, chosen_N, max_tap_count).
    """
    counts = np.asarray(counts, dtype=np.int64)
    # Stable: equal lengths keep their index order, so a bank already sorted by length
    # (pycbc's, the ladder's) yields groups that are contiguous row ranges, which a GPU
    # writes in place; quicksort swapped ties and forced a scatter copy (~5 ms per call).
    order = np.argsort(counts, kind="stable")
    sorted_counts = counts[order]
    M = len(sorted_counts)
    if M == 0:
        return [], order

    valid_ns = sorted(int(n) for n in candidate_ns)

    min_cand = valid_ns[0] if valid_ns else 1024

    def pick_n(max_c: int) -> int:
        for n in valid_ns:
            if n > max_c and (n - max_c) / n >= 0.50:
                return n
        for n in reversed(valid_ns):
            if n > max_c:
                return n
        return 1 << int(math.ceil(math.log2(max(min_cand, 2 * max_c))))

    # Partition contiguous runs sharing the same chosen FFT block size,
    # then split each run into balanced sub-batches sized to the cache budget.
    # This guarantees that all M templates are included without dropping any.
    if n_sorted is None:
        n_at = lambda i: pick_n(int(sorted_counts[i]))
    else:
        n_at = lambda i: int(n_sorted[i])

    groups = []
    run_start = 0
    while run_start < M:
        current_n = n_at(run_start)
        run_end = run_start + 1
        while run_end < M and n_at(run_end) == current_n:
            run_end += 1

        if max_batch is None:
            # Sized to stay resident within 1 MB L2 cache per core:
            # coarse template memory = b * sizeof(complex64) = (current_n // 8) * 8 bytes = current_n bytes.
            batch_target = min(512, max(32, 1048576 // (max(64, current_n // 8) * 8)))
        else:
            batch_target = int(max_batch)

        run_len = run_end - run_start
        k_run = math.ceil(run_len / batch_target)
        sub_i = run_start
        for k in range(k_run):
            rem = k_run - k
            target_sz = (run_end - sub_i + rem - 1) // rem
            sub_j = min(run_end, sub_i + target_sz)
            max_c = int(sorted_counts[sub_j - 1])
            groups.append((sub_i, sub_j, current_n, max_c))
            sub_i = sub_j

        run_start = run_end
    return groups, order


#: Block-size trials. Candidates per bank: the model's layout (rank 0), then the whole bank at
#: each of its cheapest single block sizes, _BLOCK_TRIAL_RANKS in all. A sample is one whole
#: batch (fused, concurrent: as steady state runs) timed from submission to its last result,
#: per template x series sample; a rank's first batch after a switch only settles (it uploads).
#: _BLOCK_TRIAL_SAMPLES per rank. The lock is kept in MF_COST_FILE when one is set, so a
#: machine pays for the trial once and every process then runs the same layout.
_BLOCK_TRIAL_RANKS = 3
_BLOCK_TRIAL_SAMPLES = 2


def _trial_key(bank):
    """The pooled trial a bank joins: device and its candidate block sizes. Ranks mean the
    same for every bank -- 0 its model layout, k its k-th proposed single size -- so all banks
    of a search pool their samples into one trial and one lock."""
    return "%s|%s" % (bank.device, ",".join(str(n) for n in bank._choice_ns))


def _cands_key(bank):
    """Where a bank's own proposal list is kept: its model layout, so a later process maps the
    pooled lock's rank to this bank's block size without pricing proposals again."""
    return "block-cands|%s|%s" % (bank.device, getattr(bank, '_model_sig', ''))


def _stored_cands(bank):
    from . import gatechain
    path = gatechain._cost_file()
    if path is None:
        return None
    rec = gatechain._load_cost_file(path).get(_cands_key(bank))
    return list(rec["cands"]) if isinstance(rec, dict) and "cands" in rec else None


def _store_cands(bank, cands):
    from . import gatechain
    path = gatechain._cost_file()
    if path is not None:
        gatechain._store_cost(path, _cands_key(bank), {"cands": list(cands)})


#: Noise rule: a rank beats the model's layout only when its median is more than gatechain.TIE
#: faster AND the gap exceeds _BLOCK_TRIAL_Z standard errors of the two medians' difference.
#: Unclear: both ranks are sampled further, up to _BLOCK_TRIAL_MAX each; still unclear, the
#: model's layout stays (a tie keeps the model).
_BLOCK_TRIAL_Z = 2.0
_BLOCK_TRIAL_MAX = 6
#: Re-check: after a lock, steady batches stay timed. When the winner's steady median (over
#: _BLOCK_RECHECK_N batches) exceeds what the trial measured for it, or for the best other
#: rank, by more than _BLOCK_RECHECK, the lock was wrong for steady state: it is reopened in
#: MF_COST_FILE, so the next process trials again.
_BLOCK_RECHECK = 0.15
_BLOCK_RECHECK_N = 5


def _spread(v):
    """Robust standard deviation of samples (MAD), with the plain one as a floor on 2-3."""
    v = np.asarray(v, float)
    if v.size < 2:
        return float("inf")
    mad = 1.4826 * float(np.median(np.abs(v - np.median(v))))
    return max(mad, float(np.std(v, ddof=1)) if v.size <= 3 else mad)


class _BlockTrials:
    """Measure block-size candidates end to end and lock the fastest.

    A layout's modelled cost is a sum of calibrated per-term costs, and on a latency-bound GPU
    those terms are below a call's noise, so the model alone cannot separate block sizes that
    differ by tens of percent, and it picks differently from process to process
    (docs/gate-model.md, "Large-n pricing"). Ranks run in turn, the model's first. Three
    guards keep a trial from locking on transients (M2: n=4096 locked 5.4% "faster" on two
    samples taken while chain trials moved, and ran 34% slower in steady state):
      * a batch is a sample only when no plan of the trialling banks is still calibrating
        (chain or Q15 trial; _bank_calibrating), since those switch kernels between calls;
      * a rank r > 0 wins only by more than gatechain.TIE AND by more than the samples' own
        noise (_BLOCK_TRIAL_Z standard errors); unclear contests sample further, up to
        _BLOCK_TRIAL_MAX, then keep the model's layout;
      * a locked winner is re-checked against steady-state batches (observe) and reopened
        when steady state clearly disagrees with the trial.
    Samples persist in MF_COST_FILE, so a trial carries across short processes. Trials are
    keyed by _trial_key, so only banks offering the same candidates pool their samples.
    MF_AUTOTUNE=0 keeps rank 0 unless a lock is on file."""

    def __init__(self):
        self.state = {}

    def _st(self, key):
        st = self.state.get(key)
        if st is None:
            st = self.state[key] = {"samples": {}, "winner": None, "need": {}, "median": None,
                                    "steady": [], "reopened": False}
            from . import gatechain
            path = gatechain._cost_file()
            if path is not None:
                rec = gatechain._load_cost_file(path).get("block-trial|" + key)
                st["reopened"] = bool(isinstance(rec, dict) and rec.get("rechecked"))
                if isinstance(rec, dict) and "winner" in rec:
                    st["winner"] = int(rec["winner"])
                    med = rec.get("median")
                    if isinstance(med, dict):
                        st["median"] = {int(r): float(v) for r, v in med.items()}
                elif isinstance(rec, dict) and isinstance(rec.get("samples"), dict):
                    st["reopened"] = st["reopened"] or "reopened" in rec
                    # An unfinished trial an earlier process left: continue it. Without this a
                    # process shorter than the trial (ranks x (settle + samples) batches)
                    # restarted it from nothing every time and never locked.
                    st["samples"] = {int(r): [float(x) for x in v]
                                     for r, v in rec["samples"].items()}
                    st["need"] = {int(r): int(v) for r, v in (rec.get("need") or {}).items()}
        return st

    @staticmethod
    def _base_need():
        return int(os.environ.get("MF_BLOCK_TRIALS", _BLOCK_TRIAL_SAMPLES))

    def _need(self, st, r):
        return max(self._base_need(), st["need"].get(r, 0))

    def rank_for(self, key, nranks):
        st = self._st(key)
        if st["winner"] is not None:
            return st["winner"]
        for r in range(nranks):
            st["samples"].setdefault(r, [])
        return next((r for r in range(nranks) if len(st["samples"][r]) < self._need(st, r)), 0)

    def _store(self, key, rec):
        from . import gatechain
        path = gatechain._cost_file()
        if path is not None:
            gatechain._store_cost(path, "block-trial|" + key, rec)

    def record(self, key, rank, value):
        from . import gatechain, _log_autotune
        st = self._st(key)
        if st["winner"] is not None:
            return
        st["samples"].setdefault(rank, []).append(float(value))
        partial = {"samples": {str(r): v for r, v in st["samples"].items()},
                   "need": {str(r): v for r, v in st["need"].items()},
                   "rechecked": st["reopened"]}
        if not all(len(v) >= self._need(st, r) for r, v in st["samples"].items()):
            self._store(key, partial)        # partial: the next process continues from here
            return
        smp = st["samples"]
        med = {r: float(np.median(v)) for r, v in smp.items()}
        best = min(med, key=med.get)
        win = 0
        if best != 0 and med[best] < med[0] * (1.0 - gatechain.TIE):
            se = float(np.sqrt(_spread(smp[0]) ** 2 / len(smp[0])
                               + _spread(smp[best]) ** 2 / len(smp[best])))
            if med[0] - med[best] > _BLOCK_TRIAL_Z * se:
                win = best
            elif min(len(smp[0]), len(smp[best])) < _BLOCK_TRIAL_MAX:
                # Faster, but not clear of the samples' own noise: measure both further.
                for r in (0, best):
                    st["need"][r] = len(smp[r]) + 1
                partial["need"] = {str(r): v for r, v in st["need"].items()}
                _log_autotune("BLOCK-TRIAL %s rank %d vs 0 unclear (gap %.3g, se %.3g): "
                              "sampling further", key, best, med[0] - med[best], se)
                self._store(key, partial)
                return
        st["winner"], st["median"] = win, med
        _log_autotune("BLOCK-TRIAL %s locked rank %d  median s/unit %s", key, win,
                      {r: "%.3g" % v for r, v in med.items()})
        # A lock re-trialled after a reopen is final ("rechecked"): one re-check per key, so
        # a lock cannot flap between processes on noisy steady-state timings.
        self._store(key, {"winner": win, "median": {str(r): v for r, v in med.items()},
                          "rechecked": st["reopened"]})

    def observe(self, key, value):
        """A steady-state batch of a locked key (s/unit). Reopens the lock when steady state
        clearly disagrees with the trial. Returns True when it reopened."""
        from . import _log_autotune
        st = self._st(key)
        w, med = st["winner"], st["median"]
        if w is None or not med or w not in med or st["reopened"]:
            return False
        st["steady"].append(float(value))
        if len(st["steady"]) < _BLOCK_RECHECK_N:
            return False
        steady = float(np.median(st["steady"][-_BLOCK_RECHECK_N:]))
        others = [v for r, v in med.items() if r != w]
        ref = min([med[w]] + others)
        if steady <= ref * (1.0 + _BLOCK_RECHECK):
            return False
        st["reopened"] = True
        _log_autotune("BLOCK-TRIAL %s rank %d steady %.3g s/unit vs trial %s: reopened",
                      key, w, steady, {r: "%.3g" % v for r, v in med.items()})
        # The lock goes; the steady evidence is kept so the next trial starts from it.
        self._store(key, {"samples": {}, "rechecked": True,
                          "reopened": {"rank": w, "steady": steady,
                                                      "trial": {str(r): v for r, v in med.items()}}})
        return True

    def winner(self, key):
        return self._st(key)["winner"]

    def open_keys(self):
        """Every key this process has seen without a winner (sampled or not yet)."""
        return sorted(k for k, st in self.state.items() if st["winner"] is None)

    def unlocked(self):
        """Keys this process trialled that have no winner yet (a measurement over such a
        process includes layout switches, not one steady layout)."""
        return sorted(k for k, st in self.state.items() if st["winner"] is None and st["samples"])


_BLOCK_TRIALS = _BlockTrials()


def _bank_calibrating(bank):
    """Whether any plan of the bank's live layout is still settling a measured choice (chain
    trial, Q15 trial, or a plan not built yet): such calls switch kernels between calls, so
    their batch times say nothing about the block size."""
    for g in getattr(bank, '_groups', ()) or ():
        if not getattr(g, 'is_hier', False):
            continue
        plan = getattr(g, '_plan', None)
        if plan is None:
            return True
        cal = getattr(plan, 'calibrating', None)
        if cal is not None and cal():
            return True
    return False


def _trial_begin(jobs):
    """Put every trialling bank of the batch on its key's current rank (or lock it, once its key
    has a winner). Returns [(key, rank, banks, settled, steady)]: banks still trialling, and
    locked banks whose batches are timed for the re-check (steady=True)."""
    from . import _autotune_enabled, gatechain
    groups, locked = {}, {}
    for bank, _, kw in jobs:
        if (kw or {}).get("template_index") is not None:
            continue
        if getattr(bank, '_layouts', None):
            groups.setdefault(_trial_key(bank), []).append(bank)
        elif getattr(bank, '_trial_monitor', False):
            locked.setdefault(_trial_key(bank), []).append(bank)
    plan = []
    chains = _chain_trials_begin(jobs)
    for key, bs in groups.items():
        w = _BLOCK_TRIALS.winner(key)
        if w is None and (not _autotune_enabled() or gatechain._cost_file() is None):
            # A trial is paid for once per machine, so it runs only where its lock can be kept
            # (MF_COST_FILE). Run every process, it costs that process its warm-up and more --
            # 2-3 s of fine stage on dev3 -- and gains a few percent: never worth it.
            w = 0
        if w is not None:
            for b in bs:
                b._lock_layout(w)
            continue
        r = _BLOCK_TRIALS.rank_for(key, min(len(b._layouts) for b in bs))
        settled = all(getattr(b, '_layout_rank', 0) == r and getattr(b, '_layout_warm', False)
                      for b in bs)
        for b in bs:
            b._use_layout(r)
            b.__dict__.setdefault('_ranks_run', set()).add(r)
        settled = settled and not any(_bank_calibrating(b) for b in bs)
        plan.append((key, r, bs, settled, False))
    for key, bs in locked.items():
        if _BLOCK_TRIALS.winner(key) is not None and not any(_bank_calibrating(b) for b in bs):
            plan.append((key, _BLOCK_TRIALS.winner(key), bs, True, True))
    if not plan and not chains:
        return None
    import time
    work = sum(len(b.filters_f) * int(np.asarray(x).size) for b, x, kw in jobs
               if (kw or {}).get("template_index") is None)
    return (time.perf_counter(), plan, work, chains)


#: Batches a GPU chain trial runs a candidate before it takes samples of it: after a switch
#: the ladder's fine stage took 150, 55, then 17 ms for a 17 ms segment, so the third batch
#: is the first sample.
_CHAIN_WARM_BATCHES = 2


def _chain_trials_begin(jobs):
    """GPU chain trials judged per batch: every hierarchical GPU plan of the batch in a chain
    trial is put on its trial's candidate for this batch (_chain_trial_next), so the batch's
    time is that candidate's. Returns [(trial key, chain, plans, settled)]; settled when every
    plan already ran that chain in an earlier batch (its first batch builds recordings and
    calibrates: one-off costs, not the chain's)."""
    from . import _chain_trial_next, _chain_trial_pending
    by = {}
    for bank, _, kw in jobs:
        if (kw or {}).get("template_index") is not None:
            continue
        for g in bank._groups:
            p = getattr(g, "_plan", None)
            tk = getattr(p, "_chain_trial", None) if p is not None else None
            if tk is not None and getattr(p, "_gpu", None) is not None:
                by.setdefault(tk, {})[id(p)] = p
    out = []
    for tk, plans in by.items():
        c = _chain_trial_next(tk)
        if c is None:
            continue
        settled = True
        for p in plans.values():
            # A sample only once the plans have run this chain for _CHAIN_WARM_BATCHES batches
            # in a row: after a switch, thresholds, uploads, recordings and call plans settle.
            last, run = p.__dict__.get("_chain_last_batch", (None, 0))
            if tuple(p._chain) != tuple(c):
                p._switch_chain(c)
            run = run + 1 if last == tuple(c) else 1
            settled = settled and run > _CHAIN_WARM_BATCHES
            p._chain_last_batch = (tuple(c), run)
        if settled:
            _chain_trial_pending(tk, c, +1)
        out.append((tk, tuple(c), list(plans.values()), settled))
    return out


def _trial_end(tok):
    import time
    if tok is None:
        return
    t0, plan, work, chains = tok
    dt = time.perf_counter() - t0
    from . import _chain_trial_batch, _chain_trial_pending
    for tk, c, plans, settled in chains:
        if settled:
            _chain_trial_pending(tk, c, -1)
        from . import _log_autotune
        _log_autotune("CHAIN-TRIAL batch %s settled=%s dt=%.4f work=%d", c, settled, dt, work)
        w = _chain_trial_batch(tk, c, dt / work) if (settled and work > 0) else None
        if w is not None:
            for p in plans:
                p._chain_trial = None
                p.autotune_info.update(status="locked", winner=tuple(w))
                if tuple(w) != tuple(p._chain):
                    p._switch_chain(w)
    for key, r, bs, settled, steady in plan:
        if steady:
            if work > 0 and _BLOCK_TRIALS.observe(key, dt / work):
                for b in bs:
                    b._trial_monitor = False
            continue
        if settled and work > 0:
            _BLOCK_TRIALS.record(key, r, dt / work)
        for b in bs:
            b._layout_warm = True
        w = _BLOCK_TRIALS.winner(key)
        if w is not None:
            for b in bs:
                if getattr(b, '_layouts', None) is not None:
                    b._lock_layout(w)


def _max_tiers(device) -> int:
    """Gate tiers the device's hierarchical engine executes (HierarchicalFilter._MAX_TIERS)."""
    from . import HierarchicalFilter
    from .device import parse as _parse_device
    return min(3, HierarchicalFilter._MAX_TIERS[_parse_device(device).kind])


#: Identifies one filter_series_many batch to the plans it defers.
_BATCH_TOKEN = 0

#: Device choice for single-template calls, per (device, n, block-count bucket); see
#: TimeDomainFilterBank._single_device. The first sample of each side is discarded (warm-up).
_SINGLE_CHOICE: Dict[Tuple[str, int, int], Dict[str, Any]] = {}
_SINGLE_TRIALS = 4

_CORR_COSTS: Dict[Tuple[int, str], Tuple[float, float]] = {}


def _corr_block_costs(n: int, device: Optional[Any] = None) -> Tuple[float, float]:
    """Seconds per block of continuous correlation at transform size n: (fixed, per template).

    The fixed part is the block's forward transform and bookkeeping, the per-template part its
    product and inverse transform. Measured once per process (or read from MF_COST_FILE) through
    the engine at 2 and 16 templates -- the sizes the layout builds groups of, so the per-template
    cost includes the cache footprint of a group's spectra -- taking the fastest of a few
    repetitions, which is the least load-sensitive estimate of a fixed amount of work.
    Measured on the device the bank runs on (a GPU's costs rank sizes differently), through
    the same continuous path the bank uses there.
    """
    n = int(n)
    from .device import parse as _parse_device
    dkey = "cpu" if _parse_device(device).kind == "cpu" else str(device)
    hit = _CORR_COSTS.get((n, dkey))
    if hit is not None:
        return hit
    from . import CorrelationFilter, _automatic_series_layout, gatechain
    path = gatechain._cost_file()
    key = "corr,%d" % n if dkey == "cpu" else "corr,%d,%s" % (n, dkey)
    if path is not None:
        stored = gatechain._load_cost_file(path).get(key)
        if stored is not None:
            _CORR_COSTS[(n, dkey)] = hit = (float(stored[0]), float(stored[1]))
            return hit
    rng = np.random.default_rng(7)
    taps = n // 4
    # A GPU call carries a fixed submit-and-wait cost (~0.2 ms on an M2) that production
    # spreads over a whole series of blocks. Over 8 blocks it was most of a(n) and noisy enough
    # to flip the middle bank between n=8192 and 16384 run to run (16384 runs 2.3x slower
    # there), so a GPU is priced over about half a million samples, as the bank calls it.
    nblocks = 8 if dkey == "cpu" else max(8, (1 << 19) // (n - taps))
    L = nblocks * (n - taps) + n
    ser = ((rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
    per_block = []
    for nt in (2, 16):
        h = np.zeros((nt, n), np.complex64)
        h[:, :taps] = rng.standard_normal((nt, taps))
        cf = CorrelationFilter(n, ndata=1, ntemplates=nt, valid=(taps // 2, n - taps // 2), device=device)
        cf.set_templates(np.fft.fft(h, axis=1).astype(np.complex64))
        lo, hi = cf.valid
        st, _, _ = _automatic_series_layout(L, cf.valid)
        if cf._gpu is not None:
            # On a discrete GPU the destination's residency dominates: a host-read
            # output is written over the bus at a cost per sample independent of n, which
            # swamped the kernel and priced n=32768 (whose CUDA kernel spills) as cheapest.
            # There, price the kernel into device-resident output (the resident path).
            dest = cf.empty_shared((nt, L), readback=not getattr(cf._gpu, 'discrete', False))
            run = lambda: cf._continuous_gpu(ser, st, 0, nt, dest)
        else:
            dest = np.zeros((nt, L), np.complex64)
            ep = cf._execution_plan()
            run = lambda: ep.correlate_series_continuous(ser, st, lo, hi, 0, nt, dest)
        run()
        best = np.inf
        for _ in range(5):
            t0 = time.perf_counter()
            run()
            best = min(best, time.perf_counter() - t0)
        per_block.append(best / len(st))
    b = max((per_block[1] - per_block[0]) / 14.0, 0.0)
    hit = (max(per_block[0] - 2.0 * b, 0.0), b)
    _CORR_COSTS[(n, dkey)] = hit
    if path is not None:
        gatechain._store_cost(path, key, list(hit))
    return hit


def _batch_target(n: int, max_batch: Optional[int]) -> int:
    """Templates per group: the bank's cache-resident sizing, or the caller's bound."""
    if max_batch is not None:
        return int(max_batch)
    return min(512, max(32, 1048576 // (max(64, n // 8) * 8)))


def _corr_layout(counts: np.ndarray, candidate_ns: Sequence[int], max_batch: Optional[int],
                 device: Optional[Any] = None):
    """Partition for continuous correlation by cost: contiguous runs of length-sorted templates,
    each at the transform size minimising the calibrated cost per output sample.

    A run [i, j) at size n costs (a(n) + (j - i) b(n)) / (n - L_j + 1) per output sample, where
    L_j is its longest template; a dynamic programme over j picks the cheapest partition.
    Runs are bounded by the bank's group sizing. Returns (groups, order) as _partition_templates.
    """
    counts = np.asarray(counts, dtype=np.int64)
    # Stable: equal lengths keep their index order, so a bank already sorted by length
    # (pycbc's, the ladder's) yields groups that are contiguous row ranges, which a GPU
    # writes in place; quicksort swapped ties and forced a scatter copy (~5 ms per call).
    order = np.argsort(counts, kind="stable")
    Ls = counts[order]
    M = len(Ls)
    if M == 0:
        return [], order
    ns = sorted(int(n) for n in candidate_ns)
    best = np.full(M + 1, np.inf); best[0] = 0.0
    arg: List[Tuple[int, int]] = [(0, 0)] * (M + 1)
    for j in range(1, M + 1):
        L = int(Ls[j - 1])
        for n in ns:
            nv = n - L + 1
            if nv < 1:
                continue
            a, b = _corr_block_costs(n, device)
            cap = _batch_target(n, max_batch)
            i0 = max(0, j - cap)
            i = np.arange(i0, j)
            c = best[i0:j] + (a + (j - i) * b) / nv
            k = int(np.argmin(c))
            if c[k] < best[j]:
                best[j] = c[k]; arg[j] = (int(i[k]), n)
    if not np.isfinite(best[M]):
        return None
    groups = []
    j = M
    while j > 0:
        i, n = arg[j]
        groups.append((i, j, n, int(Ls[j - 1])))
        j = i
    return groups[::-1], order


# Keyed by object identity for speed; each entry also holds the objects it was keyed on, so
# an id cannot be handed to a new object while its entry exists (a freed array's id is
# reused, which would serve the new array the old one's profile).
_REF_PROFILE_CACHE: Dict[Tuple[int, int, float, float, float], Tuple[Any, Any, np.ndarray]] = {}
_REF_BINNED_CACHE: Dict[Tuple[int, int, float], Tuple[Any, Optional[np.ndarray]]] = {}


class _TemplateGroup:
    """Internal container for a homogeneous batch of templates sharing an FFT size."""

    def __init__(self, plan, n, template_indices, c_bad, n_valid, spectra, orig_taps_max, device=None,
                 plan_factory=None, kind=None):
        # A hierarchical plan is made up front (references and templates load into it); a flat or
        # correlation plan only when something first filters with it, so a bank kept for its
        # spectra and layout alone costs no plan memory.
        self._plan = plan
        self._plan_factory = plan_factory
        self.is_hier = plan_factory is None and type(plan).__name__ == 'HierarchicalFilter'
        self.kind = kind
        self._spectra_source = None
        self.n = int(n)
        self.template_indices = np.asarray(template_indices, dtype=np.int64)
        self.c_bad = int(c_bad)
        self.n_valid = int(n_valid)
        self.spectra = spectra
        self.orig_taps_max = int(orig_taps_max)
        self.device = device
        self.templates_loaded = False
        self._cached_layout: Optional[Tuple[Tuple[int, int, int], np.ndarray, np.ndarray, np.ndarray]] = None
        self._flat_plan: Optional[Any] = None
        self._corr_plan: Optional[Any] = None

    @property
    def spectra(self):
        # A lazily planned group keeps no copy of its spectra: the bank's filters_f holds them
        # (conjugated), and the plan, if one is ever made, is loaded from those.
        if self._spectra is None and self._spectra_source is not None:
            return self._spectra_source()
        return self._spectra

    @spectra.setter
    def spectra(self, value):
        self._spectra = value

    @property
    def plan(self):
        if self._plan is None and self._plan_factory is not None:
            from . import CorrelationFilter
            plan = self._plan_factory()
            plan.set_templates(self.spectra)
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
            if self.spectra.shape[1] < self.n:
                K = self.spectra.shape[1]
                full_sp = np.zeros((self.spectra.shape[0], self.n), dtype=np.complex64)
                full_sp[:, 0] = self.spectra[:, 0].real
                full_sp[:, K] = self.spectra[:, 0].imag
                full_sp[:, 1:K] = self.spectra[:, 1:K]
                full_sp[:, K + 1:] = np.conj(self.spectra[:, K - 1:0:-1])
                fp.set_templates(full_sp)
            else:
                fp.set_templates(self.spectra)
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
        sp = self.spectra[int(ti):int(ti) + 1]
        if sp.shape[1] < self.n:
            K = sp.shape[1]
            full_sp = np.zeros((1, self.n), dtype=np.complex64)
            full_sp[:, 0] = sp[:, 0].real
            full_sp[:, K] = sp[:, 0].imag
            full_sp[:, 1:K] = sp[:, 1:K]
            full_sp[:, K + 1:] = np.conj(sp[:, K - 1:0:-1])
            sp = full_sp
        from .device import parse as _parse_device
        if _parse_device(self.device).kind == 'gpu' and not on_cpu:
            # A GPU plan owns a device context (~10 ms to create): keep one and load the
            # template into it. The caller runs the plan before asking for the next one.
            plan = self.__dict__.get('_single_gpu_plan')
            if plan is None:
                plan = self._single_gpu_plan = MatchedFilter(self.n, ndata=1, ntemplates=1,
                                                             device=self.device)
            if self.__dict__.get('_single_gpu_ti') != int(ti):
                # Calls deferred in a batch still read the current template: let them finish.
                plan._settle_deferred()
                plan.set_templates(np.ascontiguousarray(sp))
                self._single_gpu_ti = int(ti)
            return plan
        plan = MatchedFilter(self.n, ndata=1, ntemplates=1, device=None if on_cpu else self.device)
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
                if self.spectra.shape[1] < self.n:
                    K = self.spectra.shape[1]
                    full_sp = np.zeros((self.spectra.shape[0], self.n), dtype=np.complex64)
                    full_sp[:, 0] = self.spectra[:, 0].real
                    full_sp[:, K] = self.spectra[:, 0].imag
                    full_sp[:, 1:K] = self.spectra[:, 1:K]
                    full_sp[:, K + 1:] = np.conj(self.spectra[:, K - 1:0:-1])
                    cp.set_templates(full_sp)
                else:
                    cp.set_templates(self.spectra)
                self._corr_plan = cp
        return self._corr_plan



def _tap_spectra(taps: np.ndarray, counts: np.ndarray, n: int, rate_ratio: float,
                 analytic: bool, out: np.ndarray) -> None:
    """Spectra of FIR taps on an n-sample data block, written into out (T, n).

    taps is (T, m) float32 with each row's first counts[i] samples valid. The
    centre tap is rolled to lag 0; with taps at a higher rate than the data
    (rate_ratio > 1) the spectrum is cut at the data Nyquist, at a lower rate it
    is zero-padded. Not conjugated: filters_f is the conjugate of this.
    """
    T, m = taps.shape
    if rate_ratio == 1.0 and _core is not None and hasattr(_core, 'taps_to_spectra'):
        try:
            _core.taps_to_spectra(taps, counts, n, m, out)
            return
        except Exception:
            pass
    N_taps = int(round(n * rate_ratio))
    for row in range(T):
        cnt = int(counts[row])
        buf = np.zeros(N_taps, dtype=np.float32)
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
    taps = np.ascontiguousarray(taps, dtype=np.float32)
    if taps.ndim == 1:
        taps = taps[None, :]
    T = taps.shape[0]
    counts = (np.full(T, taps.shape[1], dtype=np.int64) if tap_counts is None
              else np.ascontiguousarray(tap_counts, dtype=np.int64))
    if counts.shape != (T,):
        raise ValueError(f"tap_counts must have one entry per template ({T})")
    n = int(block_length)
    rate_ratio = float(tap_sample_rate) / float(data_sample_rate)
    data_counts = np.ceil(counts / rate_ratio).astype(np.int64)
    start = np.ceil((counts // 2) / rate_ratio).astype(np.int64)
    stop = start + n - data_counts + 1
    if np.any(stop <= start):
        raise ValueError(f"block_length {n} is shorter than the longest filter "
                         f"({int(data_counts.max())} data samples)")
    if out is None:
        out = np.empty((T, n), dtype=np.complex64)
    elif (out.shape != (T, n) or out.dtype != np.complex64
          or not out.flags.c_contiguous):
        raise ValueError(f"out must be C-contiguous complex64 of shape ({T}, {n})")
    m = max(int(counts.max()), 1)
    _tap_spectra(taps[:, :m], counts, n, rate_ratio, analytic, out)
    np.conjugate(out, out=out)
    return out, np.stack([start, stop], axis=1)


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
        from . import MatchedFilter, HierarchicalFilter

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

        # Parse inputs
        self._raw_taps = None
        if isinstance(taps, (list, tuple)):
            n_templates = len(taps)
            if tap_counts is None:
                tap_counts = np.array([len(t) for t in taps], dtype=np.int64)
            else:
                tap_counts = np.asarray(tap_counts, dtype=np.int64)
            taps_list = [np.asarray(t, dtype=np.float32) for t in taps]
        elif isinstance(taps, np.ndarray):
            if taps.ndim == 1:
                taps = taps[None, :]
            n_templates = taps.shape[0]
            if tap_counts is None:
                tap_counts = np.full(n_templates, taps.shape[1], dtype=np.int64)
            else:
                tap_counts = np.asarray(tap_counts, dtype=np.int64)
            taps_list = [taps[i, :tap_counts[i]].astype(np.float32) for i in range(n_templates)]
            self._raw_taps = np.ascontiguousarray(taps, dtype=np.float32)
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
            if self.data_sample_rate <= 1024.0 or self.analytic:
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
        # Block size by cost. With a stated peak granularity the block size no
        # longer shapes the output, so it is the bank's to choose: the first
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
        from .device import parse as _parse_device
        if self.engine == 'corr' and fft_lengths is None:
            # Continuous correlation outputs every sample whatever the blocking, so its layout is
            # a pure cost choice: price partitions and transform sizes with block costs calibrated
            # on the bank's own device.
            layout = _corr_layout(self.effective_data_counts, candidate_ns, self.max_batch_size,
                                  self.device)
            if layout is not None:
                self._legacy_layout = layout
        if not self._choose_n:
            self._build(*self._legacy_layout)
        if reference is not None:
            self.set_reference(reference)
            for g in self._groups:
                if g.is_hier and not g.templates_loaded:
                    g.plan.set_templates(g.spectra)
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
        self._filters_f_list = [None] * n_templates
        self._block_lengths_arr = np.zeros(n_templates, dtype=np.int64)

        for start_idx, end_idx, chosen_N, _ in raw_groups:
            tmpl_indices = order[start_idx:end_idx]
            T = len(tmpl_indices)
            chosen_N = int(chosen_N)

            orig_taps_max = int(np.max(self.tap_counts[tmpl_indices]))
            l_data_max = int(np.max(self.effective_data_counts[tmpl_indices]))
            c_bad = int(np.ceil((orig_taps_max // 2) / self.rate_ratio))
            n_valid = int(chosen_N - l_data_max + 1)

            # Frequency domain conversion for each template in this group
            spectra = np.zeros((T, chosen_N), dtype=np.complex64)
            if self._raw_taps is not None and self._raw_taps.shape[1] >= orig_taps_max:
                group_taps = np.ascontiguousarray(self._raw_taps[tmpl_indices, :orig_taps_max])
            else:
                group_taps = np.zeros((T, orig_taps_max), dtype=np.float32)
                for r, g_idx in enumerate(tmpl_indices):
                    cnt = min(int(self.tap_counts[g_idx]), orig_taps_max)
                    group_taps[r, :cnt] = self._taps_list[g_idx][:cnt]
            group_counts = np.ascontiguousarray(self.tap_counts[tmpl_indices], dtype=np.int64)
            _tap_spectra(group_taps, group_counts, chosen_N, self.rate_ratio, self.analytic, spectra)
            for row, g_idx in enumerate(tmpl_indices):
                self._filters_f_list[g_idx] = np.conj(spectra[row])
                self._block_lengths_arr[g_idx] = chosen_N

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
                if self.first_stage_snr > 0:
                    plan.set_first_stage(self.first_stage_snr)
            else:
                factory = (lambda n_=chosen_N, T_=T, dev=self.device:
                           MatchedFilter(n_, ndata=1, ntemplates=T_, device=dev))
                plan = None
            if self.engine == 'hier' and self.pack_templates and chosen_N >= 1024:
                K = chosen_N // 2
                grp_spectra = np.ascontiguousarray(spectra[:, :K])
                grp_spectra[:, 0] = spectra[:, 0].real + 1j * spectra[:, K].real
                if hasattr(plan, 'set_hermitian'):
                    plan.set_hermitian(True)
            else:
                grp_spectra = spectra

            grp = _TemplateGroup(
                plan=plan,
                n=chosen_N,
                template_indices=tmpl_indices,
                c_bad=c_bad,
                n_valid=n_valid,
                spectra=grp_spectra,
                orig_taps_max=orig_taps_max,
                device=self.device,
                plan_factory=factory,
                kind=self.engine,
            )
            grp.templates_loaded = False
            if factory is not None:
                grp._spectra_source = (lambda idx=tmpl_indices, ff=self._filters_f_list:
                                       np.conj(np.stack([ff[int(i)] for i in idx])))
                grp.spectra = None
            self._built.append(grp)

        self._template_map = [None] * n_templates
        for g in self._built:
            for ti_local, global_idx in enumerate(g.template_indices):
                self._template_map[int(global_idx)] = (g, int(ti_local))
        self._current_ref_key = None

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

    def _choose_layout(self, fine: np.ndarray, delta_f: float, single_n: Optional[int] = None,
                       propose: bool = False):
        """Partition with each length batch at its cheapest modelled block size -- or, with
        single_n, every batch at that one size (a block-size trial candidate, _BlockTrials).
        Also leaves self._single_ns: the sizes every batch can use, cheapest total first."""
        from . import gatechain, _log_autotune
        groups, order = self._legacy_layout
        counts = self.effective_data_counts[order]
        n_sorted = np.empty(len(order), dtype=np.int64)
        totals, first = {}, True
        for i, j, n0, _ in groups:
            longest = int(counts[j - 1])
            taps_max = int(np.max(self.tap_counts[order[i:j]]))
            margin = int(np.ceil((taps_max // 2) / self.rate_ratio))
            ranked = gatechain.price_block_sizes(
                fine, delta_f, self.data_sample_rate, longest, margin, j - i,
                self.threshold, self.false_dismissal, [n for n in self._choice_ns if n > longest],
                max_tiers=_max_tiers(self.device), device=self.device)
            if propose:
                # Trial candidates are ranked with the band-forward credit at the model's
                # refine-block fraction (gatechain.CostModel.chain_forward_delta(model_f)): a
                # proposal only -- rank 0 stays the model's own choice, and the trial decides.
                ranked = gatechain.price_block_sizes(
                    fine, delta_f, self.data_sample_rate, longest, margin, j - i,
                    self.threshold, self.false_dismissal, [n for n in self._choice_ns if n > longest],
                    max_tiers=_max_tiers(self.device), device=self.device,
                    ahead=_BLOCK_TRIAL_RANKS - 1, model_f=True) or ranked
            priced = {n: c * (j - i) for c, n, _ in ranked}
            totals = priced if first else {n: totals[n] + priced[n] for n in totals if n in priced}
            first = False
            n_sorted[i:j] = (single_n if single_n is not None else ranked[0][1]) if ranked else n0
            if single_n is None and not propose:
                _log_autotune("BLOCK templates=%d longest=%d legacy n=%d -> n=%d  %s", j - i, longest, n0,
                              int(n_sorted[i]), " ".join("%d:%.3g" % (n, c) for c, n, _ in ranked))
        self._single_ns = [n for _, n in sorted((v, n) for n, v in totals.items())]
        return _partition_templates(self.effective_data_counts, max_batch=self.max_batch_size,
                                    candidate_ns=self._candidate_ns, n_sorted=n_sorted)

    @property
    def filters_f(self) -> Sequence[np.ndarray]:
        """Sequence of frequency-domain filters for each template."""
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
                layout = self._choose_layout(fine_ref, float(delta_f))
                self._model_sig = ";".join("%d:%d" % (int(e - b), int(n)) for b, e, n, _ in layout[0])
                self._model_sig += "|" + ",".join(str(n) for n in self._choice_ns)
                # Candidates (_BlockTrials): the model's layout, then the whole bank at each of
                # its _BLOCK_TRIAL_RANKS - 1 cheapest single block sizes.
                from . import gatechain as _gc, _autotune_enabled
                # Candidates only where a trial's lock can be kept (see _trial_begin); otherwise
                # none are built, so the bank is the model's layout at no extra cost.
                nr = (int(os.environ.get('MF_BLOCK_TRIAL_RANKS', _BLOCK_TRIAL_RANKS))
                      if _gc._cost_file() is not None and _autotune_enabled() else 1)
                # Locked or trialling, a bank whose block size is a measured choice keeps its
                # batches timed for the re-check (_BlockTrials.observe).
                self._trial_monitor = nr > 1
                w = _BLOCK_TRIALS.winner(_trial_key(self)) if nr > 1 else None
                cands = _stored_cands(self) if w else None
                if w == 0 or (w and cands and w < len(cands)):
                    # locked on this machine: build only the winner, no proposals priced
                    if w:
                        layout = self._choose_layout(fine_ref, float(delta_f), single_n=int(cands[w]))
                    nr = 1
                alts, sig = [layout], ["model"]
                if nr > 1:
                    # proposals: single sizes ranked WITH the model-f band-forward credit
                    self._choose_layout(fine_ref, float(delta_f), propose=True)
                    for n in list(self._single_ns):
                        if len(alts) >= nr:
                            break
                        alt = self._choose_layout(fine_ref, float(delta_f), single_n=n)
                        if alt[0] != layout[0]:      # a single size equal to the model's adds nothing
                            alts.append(alt); sig.append(n)
                    _store_cands(self, sig)
                self._candidate_sig = tuple(sig)
                if self._built is None or layout[0] != self._built_layout:
                    self._build(*layout)
                self.chosen_layout = [(int(e - b), int(n)) for b, e, n, _ in layout[0]]
                # Block-size trials (_BlockTrials): the model's alternatives within its margin are
                # built now -- the taps are freed below -- and measured on real calls.
                self._layouts = [self._snapshot()]
                for alt in alts[1:]:
                    if alt[0] == layout[0]:
                        self._layouts.append(self._layouts[0])      # same partition: share it
                        continue
                    self._build(*alt)
                    self._layouts.append(self._snapshot())
                self._restore(self._layouts[0])
                self._layout_rank = 0
                self._layout_ref = (reference, delta_f)
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

        ref_key = (id(reference), float(delta_f) if delta_f is not None else None)
        if getattr(self, '_current_ref_key', None) == ref_key and all(g.templates_loaded for g in self._groups if g.is_hier):
            return

        ref_arr = np.asarray(reference, dtype=np.float64)
        if delta_f is not None and float(delta_f) > 0:
            for g in self._groups:
                if g.is_hier:
                    b_key = (id(reference), g.n, float(delta_f))
                    hit = _REF_BINNED_CACHE.get(b_key)
                    if hit is not None and hit[0] is reference:
                        ref_input = hit[1]
                    else:
                        from .gatechain import rebin_profile
                        ref_g = rebin_profile(ref_arr, float(delta_f), self.data_sample_rate, g.n)
                        ref_input = ref_g.astype(np.float32) if ref_g is not None else None
                        _REF_BINNED_CACHE[b_key] = (reference, ref_input)
                    if ref_input is not None:
                        g.plan.set_reference(ref_input)
        else:
            # A 1-D profile without delta_f is per-bin on one block size.  Applying
            # it only to the groups it happens to fit left the others with no
            # reference, which surfaced later as a misleading gate-model error.
            wrong = [n for n in hier_ns if n != len(ref_arr)]
            if wrong:
                raise ValueError(f"1-D reference of length {len(ref_arr)} does not match hierarchical "
                                 f"block size(s) {wrong} (bank block sizes: {hier_ns}); {accepted}")
            for g in self._groups:
                if g.is_hier:
                    g.plan.set_reference(ref_arr.astype(np.float32))

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
        if layouts[rank] is layouts[self._layout_rank]:
            self._layout_rank = rank                  # the same partition: nothing to switch
            return
        self._layouts[self._layout_rank] = self._snapshot()
        self._layout_warm = False
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
        # only layouts this bank actually ran have anything on the device
        ran = getattr(self, '_ranks_run', set())
        dropped = [snap for i, snap in enumerate(self._layouts or []) if i != rank and i in ran]
        self._layouts = None
        ctxs = {}
        for snap in dropped:
            for g in snap.get('_built') or []:
                ctx = getattr(getattr(g, 'plan', None), '_gpu', None)
                if ctx is not None and hasattr(ctx, '_evict_all'):
                    ctxs[id(ctx)] = ctx
        for ctx in ctxs.values():
            if hasattr(ctx, '_drain'):
                ctx._drain()
            ctx._evict_all()                 # live layouts re-upload once, on their next call

    def _load_templates(self) -> None:
        for g in self._groups:
            if g.is_hier and not g.templates_loaded:
                g.plan.set_templates(g.spectra)
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
        hit = _REF_PROFILE_CACHE.get(p_key)
        w = hit[2] if hit is not None and hit[0] is ref_template and hit[1] is psd else None
        if w is None:
            h = np.asarray(ref_template)
            S = np.asarray(psd)
            m = min(len(h), len(S))
            w = np.zeros(m, dtype=np.float64)
            good = S[:m] > 0
            w[good] = (np.abs(h[:m][good]) ** 2) / S[:m][good]
            f = np.arange(m) * df
            w[f < flo] = 0.0
            if fhi > 0:
                w[f > fhi] = 0.0
            _REF_PROFILE_CACHE[p_key] = (ref_template, psd, w)
        self.set_reference(w, delta_f=df)

    @staticmethod
    def _window_layout(g: "_TemplateGroup", W: np.ndarray, S: int):
        """Block entries (start, window start, window end) for normalised windows W.

        One entry per (block, window) pair: two windows inside one block give
        two entries for the same start, each with its own peak-search span, so
        a peak in the gap can never be reported or displace a real one.
        Per window this is the bank's established vectorised layout."""
        STEP = g.n_valid
        c_bad = g.c_bad
        N_valid = g.n_valid
        parts_t, parts_s, parts_e = [], [], []
        for v_start, v_stop in W.tolist():
            first_block_idx = max(0, (v_start - c_bad) // STEP)
            ts = np.arange(first_block_idx * STEP, S, STEP, dtype=np.int64)
            bvt0 = ts + c_bad
            keep = (bvt0 < v_stop) & (bvt0 + N_valid > v_start)
            ts = ts[keep]
            if not ts.size:
                continue
            rs = np.maximum(v_start, bvt0[keep])
            re = np.minimum(v_stop, bvt0[keep] + N_valid)
            good = re > rs
            parts_t.append(ts[good]); parts_s.append((rs - ts)[good]); parts_e.append((re - ts)[good])
        if not parts_t:
            empty = np.empty(0, np.uintp)
            return empty, empty, empty
        cat = (lambda xs: np.ascontiguousarray(np.concatenate(xs), dtype=np.uintp))
        return cat(parts_t), cat(parts_s), cat(parts_e)

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
        ser = np.ascontiguousarray(series, dtype=np.complex64)
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

        from . import _Deferred, _SparsePeaks
        defer = getattr(self, '_defer', False)
        pending = []
        sink = getattr(self, '_trace_sink', None)
        if sink is not None:
            sink.append((pending, template_index, [False]))
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
                _settle_metal_writes()

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
            if getattr(active_plan, '_bandlimited', False) and type(active_plan).__name__ != 'HierarchicalFilter':
                bs_k = max(1, bs // 2) if bs < N else g.n // 2
                wk_s = (bws // 2).astype(np.int64)
                w_end = np.minimum(bwe, N)
                wk_e = ((w_end + 1) // 2).astype(np.int64)
                bin_counts = np.maximum(1, (wk_e - wk_s + bs_k - 1) // bs_k)
                if len(bstarts) <= 1 or np.all(bin_counts == bin_counts[0]):
                    groups_bins = [(bstarts, bws, bwe)]
                else:
                    groups_bins = []
                    for u_cnt in np.unique(bin_counts):
                        mask = (bin_counts == u_cnt)
                        groups_bins.append((bstarts[mask], bws[mask], bwe[mask]))
            elif bs >= N:
                groups_bins = [(bstarts, bws, bwe)]
            else:
                bin_counts = ((bwe - bws + bs - 1) // bs).astype(np.int64)
                if len(bstarts) <= 1 or np.all(bin_counts == bin_counts[0]):
                    groups_bins = [(bstarts, bws, bwe)]
                else:
                    groups_bins = []
                    for u_cnt in np.unique(bin_counts):
                        mask = (bin_counts == u_cnt)
                        groups_bins.append((bstarts[mask], bws[mask], bwe[mask]))

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
                        threshold=eff_threshold, templates=plan_templates)
                finally:
                    if defer and trial is None:
                        active_plan._defer_series = False
                    if sparse_ragged:
                        active_plan._want_sparse = False
                if res is not None:
                    # Split back into the per-count groups, in their order, so the result
                    # is the one per-count calls give (peak order included).
                    bc = ((bwe - bws + bs - 1) // bs).astype(np.int64)
                    split = _RaggedSplit(bc)
                    subs = [(bstarts[m], bws[m], bwe[m]) for m in split.masks]
                    if fast_key is not None and isinstance(res, _Deferred):
                        g.__dict__.setdefault('_fast_calls', {})[fast_key] = (
                            active_plan, getattr(active_plan, '_last_layout', None),
                            (split, [sb[0] for sb in subs]))
                    parts = (split.deferred(res) if isinstance(res, _Deferred)
                             else split.parts(res))
                    work = list(zip(subs, parts))
            t_trial = time.perf_counter()
            for (sub_starts, sub_bws, sub_bwe), res in work:
                if res is None:
                    if defer and trial is None:
                        active_plan._defer_series = defer       # the batch's token
                        if getattr(active_plan, '_gpu', None) is not None:
                            active_plan._gpu._queue_offset = getattr(self, '_queue_offset', 0)
                    active_plan._want_sparse = True
                    try:
                        res = active_plan.run_series(
                            data_in, sub_starts, sub_bws, sub_bwe, binsize=bs,
                            threshold=eff_threshold, templates=plan_templates, raw=True
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
                if sink is not None:
                    sink[-1][2][0] = True          # a synchronous result: not replayable
                if getattr(active_plan, '_last_n_triggers', None) == 0:
                    continue
                if pending:
                    # Keep the call's order: parts already deferred are consumed at build().
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

    def empty_shared(self, shape, dtype=np.complex64):
        """An array in this bank's device memory (host-readable), for outputs a caller reuses:
        correlate_series(out=...) writes such an array in place, and a fine bank on the same
        device reads its rows in place. On a CPU bank, ordinary page-aligned memory."""
        self._groups
        for g in self._groups:
            plan = g.get_correlation_plan() if self.engine == 'corr' else g.plan
            gpu = getattr(plan, '_gpu', None)
            if gpu is not None:
                return gpu.empty_shared(tuple(shape), dtype, readback=True)
        return _page_aligned_empty(tuple(shape), dtype)

    def _single_device(self, g, nblocks):
        """(on_cpu, trial recorder or None) for a single-template call on group g.

        A follow-up filters one template over a few dozen blocks: a GPU call is then all
        fixed cost (submission, recording for its window, readback, the wake from idle),
        which a CPU core undercuts by far. Neither side is assumed: the first calls of a
        shape (device, block size, block count) alternate between the GPU plan and a CPU
        plan, timed synchronously, and the faster is kept for every bank.
        MF_AUTOTUNE=0 keeps the bank's device.
        """
        from .device import parse as _parse_device
        from . import _autotune_enabled
        import os
        # MF_SINGLE_DEVICE=bank keeps every call on the bank's device: the pure-GPU path is a
        # product in its own right and is benchmarked as one (tools/ladder.py --pure).
        if (_parse_device(self.device).kind != 'gpu' or not _autotune_enabled()
                or os.environ.get("MF_SINGLE_DEVICE", "auto") == "bank"):
            return False, None
        key = (str(self.device), int(g.n), 1 << max(0, int(nblocks) - 1).bit_length())
        tr = _SINGLE_CHOICE.setdefault(key, {"gpu": [], "cpu": [], "winner": None})
        if tr["winner"] is not None:
            return tr["winner"] == "cpu", None
        side = "gpu" if len(tr["gpu"]) <= len(tr["cpu"]) else "cpu"

        def record(dt, side=side):
            tr[side].append(dt)
            if tr["winner"] is None and min(len(tr["gpu"]), len(tr["cpu"])) >= _SINGLE_TRIALS:
                med = {k: float(np.median(tr[k][1:])) for k in ("gpu", "cpu")}
                tr["winner"] = min(med, key=med.get)
                from . import _log_autotune
                _log_autotune("SINGLE %s n=%d blocks~%d -> %s  median s %s", key[0], key[1],
                              key[2], tr["winner"], {k: "%.3g" % v for k, v in med.items()})
        return side == "cpu", record

    @staticmethod
    def _run_followups(jobs, fine, spec, side_queue=False):
        """(follow-ups, "device" or "host"): on a backend that runs selected follow-ups as
        one fixed recording per template group (Vulkan: _vkfollowup), else on the host."""
        import os
        if os.environ.get("MF_VK_DEVICE_FOLLOWUPS", "1") != "0":
            try:
                from . import _vkfollowup
            except ImportError:
                _vkfollowup = None
            if _vkfollowup is not None:
                res = _vkfollowup.run(spec, spec.select(jobs, fine), side_queue)
                if res is not None:
                    return res, "device"
        return spec.run_host(jobs, fine), "host"

    @staticmethod
    def filter_series_many(jobs, wait=True, followups=None):
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
        if followups is not None:
            # The fine stage, then the follow-up rule on its results (_gpuhost.FollowupSpec).
            # A CUDA segment graph runs both on the device: SegmentPlan.run(followup=...).
            fine = TimeDomainFilterBank.filter_series_many(jobs)
            return fine, TimeDomainFilterBank._run_followups(jobs, fine, followups)[0]
        from . import _Deferred
        import os
        global _BATCH_TOKEN
        trial = _trial_begin(jobs)
        _BATCH_TOKEN += 1
        # On Vulkan the deferred submissions are also fused: one command buffer runs every
        # job's forward transforms, then every job's first tier, ..., one barrier per phase
        # (MF_GPU_FUSE=0 submits them separately, for comparison).
        close = None
        if os.environ.get("MF_GPU_FUSE", "1") != "0" and any(
                getattr(b, "device", None) is not None for b, _, _ in jobs):
            # Every GPU backend in use shares the protocol: fused() begins collecting on its
            # devices and returns a close (Vulkan: _vkcompute._FusedBatch; Metal: shared
            # command buffers, _mtlcompute._FusedBatch).
            closes = []
            for name in ('_vkcompute', '_mtlcompute'):
                mod = sys.modules.get(__package__ + '.' + name)
                if mod is None and name == '_vkcompute':
                    try:
                        from . import _vkcompute as mod
                    except Exception:
                        mod = None
                if mod is not None and hasattr(mod, 'fused'):
                    try:
                        closes.append(mod.fused())
                    except Exception:
                        pass
            if closes:
                def close(closes=closes):
                    for c in closes:
                        c()
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
            if trial is not None:
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
                                _trial_end(trial)
                        return v
                    return _Deferred(get)
                res = [wrap(d) for d in res]
            return res
        res = [r.result() if isinstance(r, _Deferred) else r for r in out]
        _trial_end(trial)
        return res

    @staticmethod
    def _items_batch(jobs, out):
        """Run eligible single-template GPU jobs of a batch together; returns their indices."""
        import os
        from .device import parse as _parse_device
        if os.environ.get("MF_GPU_ITEMS", "1") == "0":
            return set()
        groups = {}
        for j, (bank, series, kw) in enumerate(jobs):
            kw = kw or {}
            ti = kw.get("template_index")
            if (ti is None or bank.engine != 'hier' or _parse_device(bank.device).kind != 'gpu'
                    or set(kw) - {"windows", "binsize", "threshold", "template_index"}):
                continue
            ser = np.ascontiguousarray(series, dtype=np.complex64)
            S = ser.size
            W = _normalize_windows(kw.get("windows"), S)
            bank._groups
            g, ti_local = bank._template_map[ti]
            bs = int(kw["binsize"]) if kw.get("binsize") is not None else (bank.binsize or g.n)
            if bs >= g.n or W.shape[0] == 0:
                continue
            on_cpu, trial = bank._single_device(g, 1)
            if on_cpu or trial is not None:
                continue
            thr = bank.threshold if kw.get("threshold") is None else float(kw["threshold"])
            bstarts, bws, bwe = bank._window_layout(g, W, S)
            if bstarts.size == 0:
                continue
            groups.setdefault((id(bank), id(g), bs, thr), []).append(
                (j, bank, g, ser, bstarts, bws, bwe, ti_local, ti))
        done = set()
        # Threshold-0 follow-ups on Vulkan: every group's items as listed entries of one fixed
        # recording per template group (_vkfollowup), all in one submission. None (another
        # backend, past a capacity): the per-group path below.
        if os.environ.get("MF_VK_DEVICE_FOLLOWUPS", "1") != "0":
            fast = sorted(m[0] for (_, _, _, thr), members in groups.items() if thr == 0.0
                          for m in members)
            if fast:
                try:
                    from . import _vkfollowup
                except ImportError:
                    _vkfollowup = None
                collect = (_vkfollowup.submit_jobs([jobs[j] for j in fast])
                           if _vkfollowup else None)
                if collect is not None:
                    # Submitted, not waited on: each job's result is read when asked for, so a
                    # caller collecting later (filter_series_many(wait=False)) never waits here.
                    from . import _Deferred
                    for i, j in enumerate(fast):
                        out[j] = _Deferred(lambda c=collect, i=i: c()[i])
                        done.add(j)
                    groups = {k: v for k, v in groups.items() if k[3] != 0.0}
        # Submit every template group's items, then collect: a backend that can leaves each
        # submission in flight (wait=False), so the device runs them back to back.
        submitted = []
        for (_, _, bs, thr), members in groups.items():
            g = members[0][2]
            plan = g.get_flat_plan()
            res = plan._items_gpu([(ser, st, ws, we, tl) for _, _, _, ser, st, ws, we, tl, _ in members],
                                  bs, thr, wait=False) if hasattr(plan, "_items_gpu") else None
            if res is not None:
                submitted.append((bs, members, res))
        for bs, members, res in submitted:
            res = res()
            for (j, bank, g, ser, st, ws, we, tl, ti), (idx, val) in zip(members, res):
                lists = ([], [], [], [], [])
                # Peaks in the order one call per bin count gives them.
                counts = ((we - ws + bs - 1) // bs).astype(np.int64)
                for u in np.unique(counts):
                    m = counts == u
                    _consume_into(lists, idx[m][:, :, :u], val[m][:, :, :u], st[m], g,
                                  (tl, 1), g.n, ti)
                out[j] = _results_from(lists)
                done.add(j)
        return done

    @staticmethod
    def _block_coverage(S: int, st: np.ndarray, lo: int, hi: int) -> np.ndarray:
        """Runs of samples written by blocks starting at st, each valid over [st+lo, st+hi)."""
        b0 = st.astype(np.int64) + lo
        return _interval_runs(S, b0, np.minimum(b0 + (hi - lo), S))

    def _correlate_group(self, g: "_TemplateGroup", ser: np.ndarray, st: np.ndarray,
                         t0: int, nt: int, dest: np.ndarray) -> None:
        """Correlate rows [t0, t0+nt) of group g over blocks st into dest (nt, S).

        Writes only the samples the blocks cover; leaves the rest of dest alone.
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
            if dest.flags.c_contiguous and dest.flags.writeable:
                cplan._execution_plan().correlate_series_continuous(ser, st, lo, hi, t0, nt, dest)
            else:
                tmp = np.empty((nt, S), dtype=np.complex64)
                cplan._execution_plan().correlate_series_continuous(ser, st, lo, hi, t0, nt, tmp)
                for a, b in self._block_coverage(S, st, lo, hi):
                    dest[:, a:b] = tmp[:, a:b]                # see below
            return
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
        from ._shared import shared_buffer, shared_view
        in_place = (shared_view(dest, cplan._gpu) if getattr(cplan._gpu, 'continuous_out_views', False)
                    else shared_buffer(dest, cplan._gpu))
        if dest.flags.c_contiguous and in_place is not None:
            # A backend that zeroes on the device also finishes this work there
            # (zero_columns_done in _correlate_windows): leave it in flight meanwhile.
            defer = getattr(cplan._gpu, 'defers_continuous', False)
            cplan._continuous_gpu(ser, st, t0, nt, dest, **({'defer': True} if defer else {}))
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

    def _correlate_windows(self, g: "_TemplateGroup", ser: np.ndarray, W: np.ndarray,
                           t0: int, nt: int, dest: np.ndarray, settle=None) -> None:
        """Fill dest (nt, S) for group rows [t0, t0+nt): the correlation inside the
        union of W (where blocks compute it), exact zeros everywhere else.

        Only blocks whose valid span intersects a window are computed, each once
        even when several windows touch it."""
        from . import _automatic_series_layout
        S = ser.size
        keep = np.empty((0, 2), np.int64)
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
                    self._correlate_group(g, ser, st, t0, nt, dest)
                    keep = _intersect_runs(_interval_runs(S, W[:, 0], W[:, 1]),
                                           _interval_runs(S, b0[hit], b1[hit]))
                    # Work counters for matchedfilter._roofline: per block length, the
                    # blocks transformed, (block, template) products and inverses, the
                    # output samples the windows ask for, and template spectra read.
                    wk = self.__dict__.setdefault('_corr_work', {}).setdefault(
                        g.n, dict(blocks=0, pairs=0, out_samples=0, tmpl_values=0))
                    wk['blocks'] += int(st.size)
                    wk['pairs'] += int(st.size) * nt
                    wk['out_samples'] += int((keep[:, 1] - keep[:, 0]).sum()) * nt
                    wk['tmpl_values'] += nt * int(np.shape(g.spectra)[1])
        # Zero the complement by contiguous runs. Not dest[:, ~keep] = 0: boolean indexing
        # along axis 1 thrashes one cache set once 17+ rows sit 2^20 samples apart (see
        # _correlate_group); 27 rows took ~400 ms against ~10 ms by runs.
        edges = np.concatenate(([0], keep.ravel(), [S]))
        # A GPU-shared dest is zeroed on the device: host writes would pull its pages
        # back to the CPU (CUDA managed memory) only for the next kernel to fault them in.
        gpu = getattr(g.get_correlation_plan(), '_gpu', None) if W.shape[0] else None
        zero = getattr(gpu, 'zero_columns', None)
        if zero is not None:
            from ._shared import shared_buffer, shared_view
            held = (shared_view(dest, gpu, align=4) if getattr(gpu, 'continuous_out_views', False)
                    else shared_buffer(dest, gpu))
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
    ) -> np.ndarray:
        """Correlate a continuous series across all templates (or a specific template).

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

        ser = np.ascontiguousarray(_from_any(series), dtype=np.complex64)
        if ser.ndim != 1:
            raise ValueError("series must be a 1D array")
        S = ser.size
        nt = self.n_templates
        W = _normalize_windows(windows, S)
        # Input samples the windows read (matchedfilter._roofline), once per call.
        self._corr_in_samples = (getattr(self, '_corr_in_samples', 0)
                                 + int((W[:, 1] - W[:, 0]).sum()))

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

            self._correlate_windows(target_g, ser, W, ti_local, 1, out_2d)
            if single_scale is not None:
                np.multiply(out_2d, single_scale[:, None], out=out_2d)

            if out is not None and out.ndim == 1:
                return out
            return out_2d[0] if out is None else out_2d

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
            self._correlate_bank(ser, W, scales_arr, result, settle)
            ok = True
        finally:
            for gpu in {id(x): x for x in settle}.values():
                if ok and not wait and getattr(gpu, 'async_zero', False):
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
        back), not for every write on the device. A backend without settle_until settles
        all its writes, as before."""
        from ._shared import shared_buffer
        gpus = []
        for g in self._groups:
            gpu = getattr(g.get_correlation_plan(), '_gpu', None)
            if gpu is None:
                return ser
            gpus.append(gpu)
        if len(gpus) < 2 or getattr(gpus[0], 'host_view', None) is not None:
            return ser                       # one group, or unified memory read in place
        if all(shared_buffer(ser, gpu) is not None for gpu in gpus):
            return ser
        devs = {id(x): x for x in gpus}.values()
        double = all(hasattr(g, 'settle_until') and hasattr(g, 'write_token') for g in devs)
        bufs = self.__dict__.setdefault('_ser_stagings', [])
        k = self.__dict__.get('_ser_staging_next', 0) % (2 if double else 1)
        self._ser_staging_next = k + 1
        while len(bufs) <= k:
            bufs.append([None, []])
        slot = bufs[k]
        if double:
            for gpu, token in slot[1]:
                gpu.settle_until(token)      # the call that read this buffer has finished
        else:
            for gpu in devs:
                settle = getattr(gpu, 'settle_writes', None)
                if settle is not None:
                    settle()                 # a call left in flight may still read it
        slot[1] = []
        staged = slot[0]
        if staged is None or staged.shape != ser.shape or any(
                shared_buffer(staged, gpu) is None for gpu in gpus):
            staged = gpus[0].empty_shared(ser.shape)
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
        slot[1] = [(gpu, gpu.write_token()) for gpu in devs if hasattr(gpu, 'write_token')]

    @staticmethod
    def _fill_staging(staged, ser):
        staged[:] = ser

    def _correlate_bank(self, ser, W, scales_arr, result, settle):
        S = ser.size
        ser = self._stage_series(ser)
        try:
            self._correlate_groups(ser, W, scales_arr, result, settle)
        finally:
            self._staging_done()

    def _correlate_groups(self, ser, W, scales_arr, result, settle):
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
            self._correlate_windows(g, ser, W, 0, g_cnt, g_dest, settle if late else None)
            if scales_arr is not None:
                np.multiply(g_dest, scales_arr[g_indices][:, None], out=g_dest)
            if not is_contiguous_slice:
                result[g_indices] = g_dest


from ._gpuhost import FollowupSpec                        # noqa: E402
FollowUp = FollowupSpec                                       # the name the CUDA track used


class _SegmentResult:
    """SegmentPlan.submit's handle: result() gives what SegmentPlan.run returns."""

    def __init__(self, fn):
        self._fn, self._done, self._value = fn, False, None

    def result(self):
        if not self._done:
            self._value, self._done, self._fn = self._fn(), True, None
        return self._value


class _Same:
    """An object compared by identity, held: a signature entry that cannot match another
    object, because the one it names stays alive as long as the signature does (an id() or
    an address can come back as a different object or allocation)."""
    __slots__ = ("obj",)

    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        return isinstance(other, _Same) and other.obj is self.obj

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return id(self.obj)

    def __repr__(self):
        return "_Same(%s at %#x)" % (type(self.obj).__name__, id(self.obj))


class _VkReplay:
    """A Vulkan segment replay in flight (SegmentPlan.submit): its launch, and the read of its
    results, done once. The read is registered as an in-flight readback on every context the
    trace's records belong to, so evicting one of them (which frees result buffers) reads
    this replay's results first instead of reading freed memory later."""

    def __init__(self, plan, tr, launch):
        self.plan, self.tr, self.launch = plan, tr, launch
        self.out = None
        self.pendings = [ctx._track(self.read) for ctx in tr["ctxs"]]
        # And as the owner of every slot its dispatches use, on their fine plans: any later
        # call on those plans that reuses a slot (a deferred one taking it, a synchronous one
        # settling the plan first) reads this replay's results before overwriting them.
        self.owned = []
        for entries, _ in tr["jobs"]:
            for d, *_ in entries:
                fp = d.trace["plan"]
                owners = fp.__dict__.setdefault("_slot_owner", {})
                for sl in d.trace["slots"]:
                    owners[sl] = self
                    self.owned.append((owners, sl))

    @property
    def _done(self):                           # as a slot owner (MatchedFilter._slot_owner)
        return self.out is not None

    def read(self):
        if self.out is None:
            self.launch.wait()
            self.out = self.plan._parse_vk(self.tr)
        return self.out

    def result(self):
        out = self.read()
        for p in self.pendings:                 # deregister from every context
            p()
        self.pendings = []
        for owners, sl in self.owned:
            if owners.get(sl) is self:
                del owners[sl]
        self.owned = []
        return out


class SegmentPlan:
    """filter_series_many for a job set that recurs, e.g. every segment of one top template.

    The first run of a job set is traced: which fused GPU recordings it submitted and where
    each job's results land. A later run with the same banks (same reference and thresholds),
    the same windows and the same input buffers -- device memory the caller rewrites in place,
    such as a reused correlate_series(out=...) -- replays the recordings as one submission,
    waits once, and reads back only the jobs whose gates refined anything: the host no
    longer rebuilds every call's layout, keys and submissions. Anything else (another job set,
    an evicted recording, a non-Vulkan device, a CPU bank) runs filter_series_many as usual.
    The results are identical either way.
    """

    def __init__(self, slot_half=None):
        """slot_half (0 or 1): this plan's calls use that half of every fine plan's slots, so
        two SegmentPlans can keep their segments in flight together (submit) without their
        device records aliasing."""
        self._trace = None
        self.replays = 0
        self.slot_half = slot_half
        self._seen = None          # CUDA: the signature of the last untraced run
        self._graph = None         # CUDA: this plan's SegmentGraph (its own fork streams)
        self.capture_failures = 0

    @staticmethod
    def _cuda_context(jobs):
        """The CUDA Context of a job set run wholly on one CUDA device, else None."""
        ctx = None
        for bank, _, _ in jobs:
            for g in bank._groups:
                gpu = getattr(g._plan, "_gpu", None) if getattr(g, "_plan", None) is not None else None
                if gpu is None:
                    continue
                if (not type(gpu).__module__.endswith("_cudacompute")
                        or getattr(gpu, "_device_state", None) is None):
                    return None
                if ctx is not None and gpu._device_state is not ctx._device_state:
                    return None
                ctx = ctx or gpu
        return ctx

    @staticmethod
    def _signature(jobs):
        sig = []
        for bank, series, kw in jobs:
            kw = kw or {}
            items = []
            for k in sorted(kw):
                v = kw[k]
                if isinstance(v, slice):
                    v = ("slice", v.start, v.stop, v.step)
                elif isinstance(v, np.ndarray):
                    v = ("arr", v.tobytes())
                items.append((k, v))
            plans = tuple((_Same(g.plan), getattr(g.plan, '_chain', None),
                           (getattr(g.plan, '_gcal', None) or (None,))[0])
                          for g in bank._groups if g.is_hier)
            # The series by the allocation that holds it and its place in it, both held:
            # an address alone could come back as another allocation once this one is freed.
            root = series
            while isinstance(getattr(root, 'base', None), np.ndarray):
                root = root.base
            where = (series.ctypes.data - root.ctypes.data
                     if isinstance(series, np.ndarray) else None)
            sig.append((_Same(bank), getattr(bank, '_state_version', 0), plans,
                        _Same(root), where, getattr(series, 'size', None), tuple(items)))
        return tuple(sig)

    def run(self, jobs, prelude=None, prelude_key=None, followup=None):
        """filter_series_many(jobs), replayed when the job set recurs.

        prelude (CUDA): a callable submitting the work that produces the jobs' input series
        on the device -- e.g. the middle stage, correlate_series(..., out=<the jobs' series
        buffer>, wait=False) from inputs the caller rewrites in place -- run before the jobs
        and captured into the same graph. prelude_key identifies what it submits (the caller
        guarantees the same key means the same submission: buffers, windows, banks); a
        replay then runs it from the graph without calling it.

        followup (FollowUp): also run its follow-ups, and return (fine results, follow-ups)."""
        import os
        ctx = self._cuda_context(jobs)
        if ctx is not None and os.environ.get("MF_CUDA_SEGMENT_GRAPH", "1") != "0":
            out = self._run_cuda(jobs, ctx, prelude, prelude_key, followup)
            if followup is None:
                return out
            fine, fu = out
            if fu is None:
                fu = followup.run_host(jobs, fine)
            return fine, fu
        if self._vk_replay_on():
            return self.submit(jobs, prelude=prelude, prelude_key=prelude_key,
                               followup=followup).result()
        if prelude is not None:
            prelude()
        if followup is not None:
            fine = TimeDomainFilterBank.filter_series_many(jobs)
            return fine, self._followups(jobs, fine, followup)
        return TimeDomainFilterBank.filter_series_many(jobs)

    @staticmethod
    def _vk_replay_on():
        """Vulkan segment replay: on unless MF_SEGMENT_REPLAY=0. Against the pipelined batched
        path on the ladder (--profiles, n=2048, same measured chains), two segments in flight
        replayed: wall 15.8 -> 14.7 ms per segment, host CPU equal, results identical."""
        import os
        return os.environ.get("MF_SEGMENT_REPLAY", "1") != "0"

    def _followups(self, jobs, fine, followup, side_queue=False):
        fu, how = TimeDomainFilterBank._run_followups(jobs, fine, followup, side_queue)
        name = "followups_device" if how == "device" else "followups_host"
        setattr(self, name, getattr(self, name, 0) + 1)
        return fu

    # ---- CUDA: the whole fine stage as one graph -----------------------------------------
    def _halves(self, jobs, on):
        if self.slot_half is None:
            return
        for bank, _, _ in jobs:
            for g in bank._groups:
                p = getattr(g, "_plan", None)
                if p is not None:
                    if on:
                        p._force_slot_half = self.slot_half
                    else:
                        p.__dict__.pop("_force_slot_half", None)

    def submit(self, jobs, prelude=None, prelude_key=None, followup=None):
        """run(), started: a replayed segment graph is launched and not waited for, so the
        host can collect the previous segment meanwhile. Returns an object whose result()
        gives what run() returns. Any other path runs now (after the graphs in flight)."""
        import os
        ctx = self._cuda_context(jobs)
        if ctx is not None and os.environ.get("MF_CUDA_SEGMENT_GRAPH", "1") != "0":
            from . import _cudacompute
            sig = (self._signature(jobs), prelude_key if prelude is not None else None,
                   followup.key() if followup is not None else None)
            tr = self._trace
            if tr is not None and tr["sig"] == sig and self._graph.launch():
                self.replays += 1
                return _SegmentResult(lambda: self._collect_cuda(tr, followup))
            _cudacompute.SegmentGraph.wait_all()
        elif self._vk_replay_on():
            return self._submit_vk(jobs, prelude, prelude_key, followup)
        out = self.run(jobs, prelude=prelude, prelude_key=prelude_key, followup=followup)
        return _SegmentResult(lambda: out)

    # ---- Vulkan: the fine stage's fused recordings, replayed ------------------------------
    def _submit_vk(self, jobs, prelude, prelude_key, followup):
        """The Vulkan replay, started. Same contract as the CUDA graph: the signature (jobs,
        prelude key, follow-up rule) must match the traced run; the prelude is called each
        time (its submission is not part of the recordings) after the trace has validated
        and before the replay is submitted; follow-ups run when the result is collected."""
        import os
        sig = (self._signature(jobs), prelude_key if prelude is not None else None,
               followup.key() if followup is not None else None)
        tr = self._trace
        if os.environ.get("MF_REPLAY_DEBUG"):
            if tr is None:
                print("replay: no trace", flush=True)
            elif tr["sig"] != sig:
                print("replay: signature differs", flush=True)
        if tr is not None and tr["sig"] == sig:
            from . import _vkcompute
            prev = self.__dict__.pop("_vk_inflight", None)
            if prev is not None:
                prev.read()                      # this plan's records and starts are reused

            def before():
                # The batches' block starts, written by the host when the segment was traced:
                # any call on the same plans since (a synchronous one reuses slot 0, a host
                # follow-up) may have rewritten them.
                for entries, _ in tr["jobs"]:
                    for d, *_ in entries:
                        for arr, vals in d.trace.get("starts", ()):
                            arr[:len(vals)] = vals
                if prelude is not None:
                    prelude()
            launch = _vkcompute.replay_fused(tr["dev"], tr["keys"], wait=False, before=before)
            if launch:
                self.replays += 1
                h = self._vk_inflight = _VkReplay(self, tr, launch)

                def collect():
                    fine = h.result()
                    if followup is None:
                        return fine
                    # On a side queue: the next segment's replay may already be queued on the
                    # main one, and these need only this segment (finished: h waited for it).
                    return fine, self._followups(jobs, fine, followup, side_queue=True)
                return _SegmentResult(collect)
            self._trace = None
        if prelude is not None:
            prelude()
        fine = self._trace_run(jobs, sig)
        out = (fine, self._followups(jobs, fine, followup)) if followup is not None else fine
        return _SegmentResult(lambda: out)

    def _collect_cuda(self, tr, followup):
        self._graph.wait()
        out = self._parse_cuda(tr)
        if followup is None:
            return out
        fu = self._read_followups(tr.get("fu"))
        if fu is None:
            fu = followup.run_host(self._jobs_of(tr), out)
        return out, fu

    def _run_cuda(self, jobs, ctx, prelude=None, prelude_key=None, followup=None):
        """One CUDA graph per recurring job set: the first run of a signature runs as usual
        (allocations, module loads, per-call graphs and plans settle), the second is captured
        whole -- every bank's forwards, gates, compactions, refines and readbacks, across the
        fork streams -- and later runs relaunch it with one cuGraphLaunch and one wait, then
        read each dispatch's results. Any change (signature, a freed buffer, a failed
        capture) falls back to filter_series_many."""
        import os
        from . import _cudacompute
        sig = (self._signature(jobs), prelude_key if prelude is not None else None,
               followup.key() if followup is not None else None)
        wrap = (lambda out, fu=None: (out, fu)) if followup is not None else (lambda out, fu=None: out)
        tr = self._trace
        if tr is not None and tr["sig"] == sig:
            out = self._replay_cuda(tr)
            if out is not None:
                self.replays += 1
                return wrap(out, self._read_followups(tr.get("fu")))
        self._trace = None
        if self._seen != sig:
            self._seen = sig
            if prelude is not None:
                prelude()
            self._halves(jobs, True)
            try:
                return wrap(TimeDomainFilterBank.filter_series_many(jobs))
            finally:
                self._halves(jobs, False)
        if self._graph is None:
            self._graph = _cudacompute.SegmentGraph(ctx)
        for bank, _, _ in jobs:
            bank._trace_sink = []
        built = {}

        def submit():
            if prelude is not None:
                prelude()
            futures = TimeDomainFilterBank.filter_series_many(jobs, wait=False)
            if followup is not None:
                built["fu"] = self._device_followups(ctx, jobs, followup)
            return futures
        self._halves(jobs, True)
        try:
            futures = self._graph.capture(submit)
            sinks = [bank._trace_sink for bank, _, _ in jobs]
        except RuntimeError as e:
            self.capture_failures += 1
            self.last_capture_error = str(e)
            if os.environ.get("MF_REPLAY_DEBUG"):
                import traceback
                traceback.print_exc()
            self._seen = None
            if prelude is not None:
                prelude()
            return wrap(TimeDomainFilterBank.filter_series_many(jobs))
        finally:
            self._halves(jobs, False)
            for bank, _, _ in jobs:
                bank._trace_sink = None
        self._graph.replay()
        out = [f.result() if hasattr(f, "result") else f for f in futures]
        per_job, cursor = [], {}
        for j, (bank, _, _) in enumerate(jobs):
            k = cursor.get(id(bank), 0)
            cursor[id(bank)] = k + 1
            per_job.append(sinks[j][k] if k < len(sinks[j]) else None)
        if all(e is not None and not e[2][0]
               and all(getattr(d, "trace", None) is not None for d, *_ in e[0]) for e in per_job):
            self._trace = dict(sig=sig, jobs=[(e[0], e[1]) for e in per_job], fu=built.get("fu"),
                               all_jobs=jobs)
        return wrap(out, self._read_followups(built.get("fu")))

    def _read_followups(self, dfu):
        """The device follow-ups' results, or None (the caller runs them on the host)."""
        if dfu is None:
            self.followups_host = getattr(self, "followups_host", 0) + 1
            return None
        res = dfu.read()
        if res is None:
            self.followups_overflow = getattr(self, "followups_overflow", 0) + 1
        else:
            self.followups_device = getattr(self, "followups_device", 0) + 1
        return res

    def _device_followups(self, ctx, jobs, followup):
        """Inside the capture, after the fine stage: the follow-ups on the device, or None
        (the host then runs them) when this job set cannot take that path."""
        import os
        try:
            from . import _cudafollowup
        except ImportError:                    # a build without the CUDA follow-up kernels
            return None
        if os.environ.get("MF_CUDA_DEVICE_FOLLOWUPS", "1") == "0":
            return None
        per_job, cursor = [], {}
        for j, (bank, _, _) in enumerate(jobs):
            k = cursor.get(id(bank), 0)
            cursor[id(bank)] = k + 1
            sink = bank._trace_sink
            e = sink[k] if k < len(sink) else None
            if e is None or e[2][0] or not all(getattr(d, "trace", None) is not None
                                               for d, *_ in e[0]):
                return None
            per_job.append(e[0])
        try:
            dfu = _cudafollowup.DeviceFollowUps(ctx, self._graph, followup, jobs, per_job)
        except _cudafollowup.Unsupported as e:
            self.followup_unsupported = str(e)
            return None
        self._graph.join()
        dfu.enqueue()
        return dfu

    @staticmethod
    def _jobs_of(tr):
        return tr["all_jobs"]

    def _replay_cuda(self, tr):
        """Relaunch the segment graph, wait, then read every dispatch (_parse_cuda)."""
        if not self._graph.replay():
            return None
        return self._parse_cuda(tr)

    def _parse_cuda(self, tr, reader=None):
        """Read every dispatch of a finished segment graph. Sparse results go straight
        into the job's peak lists, without dense tables, in the order filter_series gives:
        (block, template, bin), blocks in the caller's order. A dense dispatch (threshold 0,
        or a fallback) takes the table route for its whole call."""
        from . import _SparsePeaks
        results = []
        for entries, template_index in tr["jobs"]:
            lists = ([], [], [], [], [])
            for d, sub_starts, g, tmpl_arg, N in entries:
                t = d.trace
                nt, nb = t["shape"][1], t["shape"][2]
                order = t["order"]
                rows, tis, bns, idxs, vals = [], [], [], [], []
                dense = None
                for b0, b1, entry in t["groups"]:
                    r = entry() if reader is None else reader(entry, t)
                    if isinstance(r, _SparsePeaks):
                        if r.flat.size == 0:
                            continue
                        per = r.shape[1] * r.shape[2]
                        keep = r.flat < (b1 - b0) * per          # padded rows dropped
                        bi, rest = np.divmod(r.flat[keep].astype(np.int64), per)
                        ti, bn = np.divmod(rest, r.shape[2])
                        rows.append(bi + b0)                       # layout row
                        tis.append(ti)
                        bns.append(bn)
                        idxs.append(r.idx[keep].astype(np.int64))
                        vals.append(r.val[keep])
                    else:
                        gi, gv = r
                        if not (gi >= 0).any():
                            continue
                        if dense is None:
                            dense = (np.full(t["shape"], -1, dtype=np.int64),
                                     np.zeros(t["shape"], dtype=np.complex64))
                        dense[0][b0:b1], dense[1][b0:b1] = gi[:b1 - b0], gv[:b1 - b0]
                if dense is not None:
                    idx, val = dense
                    if rows:
                        lr, ti, bn = (np.concatenate(x) for x in (rows, tis, bns))
                        idx[lr, ti, bn] = np.concatenate(idxs)
                        val[lr, ti, bn] = np.concatenate(vals)
                    if order is not None:
                        ri, rv = np.empty_like(idx), np.empty_like(val)
                        ri[order], rv[order] = idx, val
                        idx, val = ri, rv
                    _consume_into(lists, idx, val, sub_starts, g, tmpl_arg, N, template_index)
                    continue
                if not rows:
                    continue
                row = np.concatenate(rows)
                if order is not None:
                    row = order[row]                               # the caller's block
                ti, bn = np.concatenate(tis), np.concatenate(bns)
                srt = np.argsort((row * nt + ti) * nb + bn, kind="stable")
                row, ti = row[srt], ti[srt]
                ii = np.concatenate(idxs)[srt]
                vv = np.concatenate(vals)[srt]
                if tmpl_arg is not None:
                    lists[0].append(np.full(row.size, template_index, dtype=np.int64))
                else:
                    lists[0].append(g.template_indices[ti])
                lists[1].append(sub_starts[row] + ii)
                lists[2].append(vv)
                lists[3].append(sub_starts[row])
                lists[4].append(np.full(row.size, N, dtype=np.int64))
            results.append(_results_from(lists))
        return results

    def _trace_run(self, jobs, sig):
        from . import _vkcompute
        devs = list(_vkcompute._DEVICES.values())
        for dev in devs:
            dev.trace = []
        sinks = []
        for bank, _, _ in jobs:
            bank._trace_sink = []
        self._halves(jobs, True)
        try:
            out = TimeDomainFilterBank.filter_series_many(jobs)
            sinks = [bank._trace_sink for bank, _, _ in jobs]
        finally:
            self._halves(jobs, False)
            for bank, _, _ in jobs:
                bank._trace_sink = None
            keys = {id(dev): dev.trace for dev in devs}
            for dev in devs:
                dev.trace = None
        # One sink entry per filter_series call, in job order; a bank appearing in several
        # jobs logged each call in turn.
        per_job, cursor = [], {}
        for j, (bank, _, _) in enumerate(jobs):
            k = cursor.get(id(bank), 0)
            cursor[id(bank)] = k + 1
            per_job.append(sinks[j][k] if k < len(sinks[j]) else None)
        used = [dev for dev in devs if keys[id(dev)]]
        replayable = (len(used) == 1
                      and all(e is not None and not e[2][0]
                              and all(getattr(d, "trace", None) is not None for d, *_ in e[0])
                              for e in per_job))
        if replayable:
            # Every dispatch must own its result buffers for the whole segment: one that
            # reused an earlier dispatch's record (more batches than slots) was read before
            # the reuse when run call by call, but a replay runs both and reads after.
            # Likewise every slot (its starts and spectra, written by the host per batch):
            # a slot used twice in the segment holds only the later batch's starts, which a
            # replay would then read for both.
            seen, slots = set(), set()
            for e in per_job:
                for d, *_ in e[0]:
                    for _, _, entry in d.trace["groups"]:
                        if id(entry[0]) in seen:         # live objects: ids are unique here
                            replayable = False
                        seen.add(id(entry[0]))
                    for sl in d.trace.get("slots", ()):
                        k = (id(d.trace["plan"]), sl)    # the plan is alive (held by d)
                        if k in slots:
                            replayable = False
                        slots.add(k)
        # The contexts whose records hold the traced dispatches' result buffers (held here).
        ctxs = list({id(c): c for c in (getattr(g.plan, '_gpu', None) for bank, _, _ in jobs
                                         for g in bank._groups) if c is not None}.values())
        self._trace = dict(sig=sig, dev=used[0], keys=list(keys[id(used[0])]), ctxs=ctxs,
                           jobs=[(e[0], e[1]) for e in per_job]) if replayable else None
        if os.environ.get("MF_REPLAY_DEBUG") and not replayable:
            print("replay: trace not replayable: devices", len(used), "sync jobs",
                  sum(1 for e in per_job if e is None or e[2][0]),
                  "untraced", sum(1 for e in per_job if e is not None and not all(
                      getattr(d, "trace", None) is not None for d, *_ in e[0])), flush=True)
        return out

    def _parse_vk(self, tr):
        """Every job's results from a finished Vulkan replay: the dispatches' survivor lists
        read as sparse peaks, assembled exactly as a CUDA replay's (_parse_cuda)."""
        from . import _vkcompute
        return self._parse_cuda(tr, reader=_vkcompute.read_dispatch_sparse)


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
