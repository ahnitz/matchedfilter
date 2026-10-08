"""TimeDomainFilterBank: Ingest raw time-domain filters, dynamically partition by length,
automatically select optimal FFT block sizes, and filter continuous series."""

import math
from collections import OrderedDict
import time
from typing import Any, NamedTuple, Optional, Sequence, Union, Tuple, List, Dict
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
    order = np.argsort(counts)
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


def _max_tiers(device) -> int:
    """Gate tiers the device's hierarchical engine executes (HierarchicalFilter._MAX_TIERS)."""
    from . import HierarchicalFilter
    from .device import parse as _parse_device
    return min(3, HierarchicalFilter._MAX_TIERS[_parse_device(device).kind])


#: Identifies one filter_series_many batch to the plans it defers.
_BATCH_TOKEN = 0

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
            dest = cf.empty_shared((nt, L), readback=True)
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
    order = np.argsort(counts)
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

    def get_single_plan(self, ti: int):
        """An ungated plan holding only local template ti (a few kept per group): what a
        single-template call needs, without building the group's whole ungated bank."""
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
        if _parse_device(self.device).kind == 'gpu':
            # A GPU plan owns a device context (~10 ms to create): keep one and load the
            # template into it. The caller runs the plan before asking for the next one.
            plan = self.__dict__.get('_single_gpu_plan')
            if plan is None:
                plan = self._single_gpu_plan = MatchedFilter(self.n, ndata=1, ntemplates=1,
                                                             device=self.device)
            if self.__dict__.get('_single_gpu_ti') != int(ti):
                plan.set_templates(np.ascontiguousarray(sp))
                self._single_gpu_ti = int(ti)
            return plan
        plan = MatchedFilter(self.n, ndata=1, ntemplates=1, device=self.device)
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
            has_fast_c = (self.rate_ratio == 1.0 and _core is not None and hasattr(_core, 'taps_to_spectra'))
            used_fast_c = False
            if has_fast_c:
                try:
                    if self._raw_taps is not None and self._raw_taps.shape[1] >= orig_taps_max:
                        group_taps = np.ascontiguousarray(self._raw_taps[tmpl_indices, :orig_taps_max])
                    else:
                        group_taps = np.zeros((T, orig_taps_max), dtype=np.float32)
                        for r, g_idx in enumerate(tmpl_indices):
                            t_arr = self._taps_list[g_idx]
                            cnt = min(int(self.tap_counts[g_idx]), orig_taps_max)
                            group_taps[r, :cnt] = t_arr[:cnt]
                    group_counts = np.ascontiguousarray(self.tap_counts[tmpl_indices], dtype=np.int64)
                    _core.taps_to_spectra(group_taps, group_counts, chosen_N, orig_taps_max, spectra)
                    for row, g_idx in enumerate(tmpl_indices):
                        self._filters_f_list[g_idx] = np.conj(spectra[row])
                        self._block_lengths_arr[g_idx] = chosen_N
                    used_fast_c = True
                except Exception:
                    used_fast_c = False

            if not used_fast_c:
                for row, g_idx in enumerate(tmpl_indices):
                    t_arr = self._taps_list[g_idx]
                    cnt = int(self.tap_counts[g_idx])
                    N_taps = int(round(chosen_N * self.rate_ratio))

                    buf = np.zeros(N_taps, dtype=np.float32)
                    buf[:cnt] = t_arr[:cnt]
                    # Center-tap circular roll alignment
                    buf = np.roll(buf, -(cnt // 2))

                    spec = np.fft.fft(buf).astype(np.complex64)
                    if self.analytic and N_taps > chosen_N:
                        # For an analytic series with positive-frequency support [f_low, f_high) < data Nyquist:
                        # Positive-frequency bins [0, chosen_N) map directly to [0, f_Nyquist) without
                        # negative-frequency mirroring.
                        spec_data = np.ascontiguousarray(spec[:chosen_N])
                    elif N_taps > chosen_N:
                        # Truncate frequencies above data Nyquist (preserving positive and negative bins)
                        spec_data = np.zeros(chosen_N, dtype=np.complex64)
                        spec_data[:chosen_N // 2 + 1] = spec[:chosen_N // 2 + 1]
                        neg_count = chosen_N - (chosen_N // 2 + 1)
                        spec_data[chosen_N // 2 + 1:] = spec[N_taps - neg_count:]
                    elif N_taps < chosen_N:
                        # Zero-pad frequencies above template Nyquist
                        spec_data = np.zeros(chosen_N, dtype=np.complex64)
                        half_taps = N_taps // 2
                        spec_data[:half_taps + 1] = spec[:half_taps + 1]
                        neg_count = N_taps - (half_taps + 1)
                        spec_data[chosen_N - neg_count:] = spec[half_taps + 1:]
                    else:
                        spec_data = spec

                    spectra[row] = spec_data
                    self._filters_f_list[g_idx] = np.conj(spec_data)
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

    def _choose_layout(self, fine: np.ndarray, delta_f: float):
        """Partition with each length batch at its cheapest modelled block size."""
        from . import gatechain, _log_autotune
        groups, order = self._legacy_layout
        counts = self.effective_data_counts[order]
        n_sorted = np.empty(len(order), dtype=np.int64)
        for i, j, n0, _ in groups:
            longest = int(counts[j - 1])
            taps_max = int(np.max(self.tap_counts[order[i:j]]))
            margin = int(np.ceil((taps_max // 2) / self.rate_ratio))
            ranked = gatechain.price_block_sizes(
                fine, delta_f, self.data_sample_rate, longest, margin, j - i,
                self.threshold, self.false_dismissal, [n for n in self._choice_ns if n > longest],
                max_tiers=_max_tiers(self.device), device=self.device)
            n_sorted[i:j] = ranked[0][1] if ranked else n0
            _log_autotune("BLOCK templates=%d longest=%d legacy n=%d -> n=%d  %s", j - i, longest, n0,
                          int(n_sorted[i]), " ".join("%d:%.3g" % (n, c) for c, n, _ in ranked))
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
                layout = self._choose_layout(np.asarray(reference, dtype=np.float64), float(delta_f))
                if self._built is None or layout[0] != self._built_layout:
                    self._build(*layout)
                self.chosen_layout = [(int(e - b), int(n)) for b, e, n, _ in layout[0]]
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

        W = _normalize_windows(windows, S)
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

        cache_key = (S, W.tobytes())

        if template_index is not None:
            if template_index < 0 or template_index >= self.n_templates:
                raise IndexError(f"template_index {template_index} out of range [0, {self.n_templates})")
            self._groups
            target_g, ti_local = self._template_map[template_index]
            work_items = [(target_g, (ti_local, 1))]
        else:
            work_items = [(g, None) for g in self._groups]

        def consume(aidx, aval, sub_starts, g, tmpl_arg, N):
            # aidx has shape (nblocks, ntemplates, nbins)
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

        from . import _Deferred
        defer = getattr(self, '_defer', False)
        pending = []
        for g, tmpl_arg in work_items:
            plan_templates = tmpl_arg
            if self.engine == 'hier' and tmpl_arg is not None:
                # one template ungated: a plan holding just it, not the group's whole ungated bank
                active_plan = g.get_single_plan(tmpl_arg[0])
                plan_templates = None
            elif self.engine == 'hier' and (eff_threshold < self.threshold or eff_threshold <= 0.0):
                active_plan = g.get_flat_plan()
            else:
                active_plan = g.plan

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
                res = active_plan._run_series_ragged(
                    data_in, bstarts, bws, bwe, binsize=bs,
                    threshold=eff_threshold, templates=plan_templates)
                if res is not None:
                    work = [((bstarts, bws, bwe), res)]
            for (sub_starts, sub_bws, sub_bwe), res in work:
                if res is None:
                    if defer:
                        active_plan._defer_series = defer       # the batch's token
                        if getattr(active_plan, '_gpu', None) is not None:
                            active_plan._gpu._queue_offset = getattr(self, '_queue_offset', 0)
                    try:
                        res = active_plan.run_series(
                            data_in, sub_starts, sub_bws, sub_bwe, binsize=bs,
                            threshold=eff_threshold, templates=plan_templates, raw=True
                        )
                    finally:
                        if defer:
                            active_plan._defer_series = False
                if isinstance(res, _Deferred):
                    pending.append((res, sub_starts, g, tmpl_arg, N))
                    continue
                aidx, aval = res
                if getattr(active_plan, '_last_n_triggers', None) == 0:
                    continue
                consume(aidx, aval, sub_starts, g, tmpl_arg, N)

        def build():
            for d, sub_starts, g, tmpl_arg, N in pending:
                consume(*d.result(), sub_starts, g, tmpl_arg, N)
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

    @staticmethod
    def filter_series_many(jobs):
        """Several filter_series calls as one batch: jobs is [(bank, series, kwargs)], the
        result the list of their FilterResults, identical to calling each in turn.

        On a GPU every call is submitted before any is collected, and each job's work goes to
        its own compute queue: the device runs banks concurrently and works on early banks
        while the host uploads later ones, and the host waits once rather than per call.
        On a CPU the calls simply run in order.
        """
        from . import _Deferred
        global _BATCH_TOKEN
        _BATCH_TOKEN += 1
        out = []
        for j, (bank, series, kw) in enumerate(jobs):
            bank._defer, bank._queue_offset = _BATCH_TOKEN, j
            try:
                out.append(bank.filter_series(series, **(kw or {})))
            finally:
                bank._defer, bank._queue_offset = 0, 0
        return [r.result() if isinstance(r, _Deferred) else r for r in out]

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
        from ._shared import shared_buffer
        if dest.flags.c_contiguous and shared_buffer(dest, cplan._gpu) is not None:
            cplan._continuous_gpu(ser, st, t0, nt, dest)
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
                           t0: int, nt: int, dest: np.ndarray) -> None:
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
        # Zero the complement by contiguous runs. Not dest[:, ~keep] = 0: boolean indexing
        # along axis 1 thrashes one cache set once 17+ rows sit 2^20 samples apart (see
        # _correlate_group); 27 rows took ~400 ms against ~10 ms by runs.
        edges = np.concatenate(([0], keep.ravel(), [S]))
        for a, b in zip(edges[::2], edges[1::2]):
            if b > a:
                dest[:, a:b] = 0

    def correlate_series(
        self,
        series: np.ndarray,
        windows=None,
        scales: Optional[Union[np.ndarray, Sequence[float]]] = None,
        template_index: Optional[int] = None,
        out: Optional[np.ndarray] = None,
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
            self._correlate_windows(g, ser, W, 0, g_cnt, g_dest)
            if scales_arr is not None:
                np.multiply(g_dest, scales_arr[g_indices][:, None], out=g_dest)
            if not is_contiguous_slice:
                result[g_indices] = g_dest

        return result
