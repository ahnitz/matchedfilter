"""How a TimeDomainFilterBank lays out its templates: the partition into groups by tap count,
the transform size each group runs at (_corr_layout, priced by _corr_block_costs: the
continuous correlation's per-block costs, measured once per machine), and the batches a group
is split into."""
import math
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from ._prices import price_once
from ._filter import _automatic_series_layout
from . import _core
from . import _choice
from .device import parse as _parse_device


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
            batch_target = _batch_target(current_n, None)
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


_CORR_COSTS: Dict[Tuple[int, str], Tuple[float, float, float]] = {}


def _corr_block_cost(n: int, templates: int, valid: int, device: Optional[Any] = None) -> float:
    """Seconds for one block of continuous correlation at transform size n, for `templates`
    templates and `valid` output samples each (_corr_block_costs: a + k (b + w valid))."""
    a, b, w = _corr_block_costs(n, device)
    return a + templates * (b + w * valid)


def _corr_block_costs(n: int, device: Optional[Any] = None) -> Tuple[float, float, float]:
    """Seconds per block of continuous correlation at transform size n: (fixed, per template,
    per template per output sample).

    The fixed part is the block's forward transform and bookkeeping; per template, its product
    and inverse transform (b) and writing its valid output samples (w per sample). The write
    is separate because it is most of a GPU's cost at these sizes (the stage is memory-bound),
    and filters near the transform's length leave few valid samples per block: priced per
    block at a quarter-length filter, n = 8192 cost 1.7x its measured cost for 5000-tap
    filters and n = 32768 0.8x, and a GPU middle stage ran at 32768, 20% slower.
    Measured once per process (or read from MF_COST_FILE) through the engine at 2 and 16
    templates -- the sizes the layout builds groups of, so the per-template cost includes the
    cache footprint of a group's spectra -- and at 16 templates over half the valid span,
    taking the fastest of a few repetitions, which is the least load-sensitive estimate of a
    fixed amount of work. Measured on the device the bank runs on (a GPU's costs rank sizes
    differently), through the same continuous path the bank uses there.
    """
    n = int(n)
    dev = _parse_device(device)
    dkey = "cpu" if dev.kind == "cpu" else str(device)
    # corr4: the fixed cost has a floor (_corr_measure); files with corr3 entries hold zeros.
    # A GPU's prices are keyed on the kernels they timed, so a rebuilt kernel is priced again
    # rather than chosen by its predecessor's costs.
    key = ("corr4,%d" % n if dkey == "cpu" else "corr4,%d,%s|k%s"
           % (n, dkey, _corr_kernel_id(n, getattr(dev, "backend", None))))
    if (n, dkey) in _CORR_COSTS:
        return _CORR_COSTS[(n, dkey)]

    def measure():
        rng = np.random.default_rng(7)
        taps = n // 4
        # A GPU call carries a fixed submit-and-wait cost (~0.2 ms on an M2) that production
        # spreads over a whole series of blocks. Over 8 blocks it was most of a(n) and noisy enough
        # to flip the middle bank between n=8192 and 16384 run to run (16384 runs 2.3x slower
        # there), so a GPU is priced over about half a million samples, as the bank calls it.
        nblocks = 8 if dkey == "cpu" else max(8, (1 << 19) // (n - taps))
        L = nblocks * (n - taps) + n
        ser = ((rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
        hit = _corr_measure(n, device, dkey, rng, taps, nblocks, L, ser)
        return hit, list(hit)
    return price_once(_CORR_COSTS, (n, dkey), key, measure,
                      lambda r: tuple(float(v) for v in r[:3]) if isinstance(r, list)
                      and len(r) >= 3 else None)


def _corr_kernel_id(n, backend):
    """Identity of the kernels a GPU's continuous correlation at length n runs (the forward
    and the series correlation, one- or two-stage, either staging build)."""
    from ._kernel_id import BACKENDS, kernel_id
    if backend not in BACKENDS:
        return "-"
    stems = [s % n + lds for s in ("forward_%d", "full_series_%d", "tc_fwd1_%d", "tc_fwd2_%d",
                                   "tc_corr1_%d", "tc_corr_series2_%d")
             for lds in ("", "_lds32")]
    return kernel_id(backend, stems)


def _corr_measure(n, device, dkey, rng, taps, nblocks, L, ser):
    """(fixed, per template, per template per output sample) seconds per block through the
    bank's continuous path: 2 and 16 templates with `taps`-tap filters, and 16 with filters
    leaving half the valid span, each the fastest of 5 interleaved rounds
    (_choice.fastest_of_rounds). The fixed cost is at least half the per-template cost."""
    from . import CorrelationFilter
    runs, blocks, valid = [], [], []
    short = n - (n - taps) // 2
    for nt, tp in ((2, taps), (16, taps), (16, short)):
        h = np.zeros((nt, n), np.complex64)
        h[:, :tp] = rng.standard_normal((nt, tp))
        cf = CorrelationFilter(n, ndata=1, ntemplates=nt, valid=(tp // 2, n - tp // 2), device=device)
        cf.set_templates(np.fft.fft(h, axis=1).astype(np.complex64))
        lo, hi = cf.valid
        st, _, _ = _automatic_series_layout(L, cf.valid)
        if cf._gpu is not None:
            # On a discrete GPU the destination's residency dominates: a host-read
            # output is written over the bus at a cost per sample independent of n, which
            # swamped the kernel and priced n=32768 (whose CUDA kernel spills) as cheapest.
            # There, price the kernel into device-resident output (the resident path).
            dest = cf.empty_shared((nt, L), readback=cf._gpu.props.unified_memory)
            run = lambda cf=cf, st=st, nt=nt, dest=dest: cf._continuous_gpu(ser, st, 0, nt, dest)
        else:
            dest = np.zeros((nt, L), np.complex64)
            ep = cf._continuous_plan()
            run = (lambda ep=ep, st=st, lo=lo, hi=hi, nt=nt, dest=dest:
                   ep.correlate_series_continuous(ser, st, lo, hi, 0, nt, dest))
        run()                                   # warm-up
        runs.append(run)
        blocks.append(len(st))
        valid.append(hi - lo)

    def time_one(i):
        t0 = time.perf_counter()
        runs[i]()
        return time.perf_counter() - t0
    best = _choice.fastest_of_rounds(range(len(runs)), time_one, 5)
    per_block = [best[i] / blocks[i] for i in range(len(runs))]
    s1 = max((per_block[1] - per_block[0]) / 14.0, 0.0)        # per template at valid[0]
    w = max((per_block[1] - per_block[2]) / (16.0 * (valid[1] - valid[2])), 0.0)
    b = max(s1 - w * valid[0], 0.0)
    # The fixed cost is the block's forward transform and data handling: no less than half a
    # template's product, inverse transform and store. As a difference of two timings it read
    # zero whenever sixteen templates cost more each than two -- on a loaded node, or where
    # sixteen spectra leave the second-level cache (Haswell: 256 KB) -- and a zero fixed cost
    # makes a group per filter look free: five filters were split into five groups, each
    # with its own forward pass, at half the speed of one group.
    return (max(per_block[0] - 2.0 * s1, 0.5 * s1), b, w)


#: (device, rows, taps, candidate sizes) -> {n: seconds per row per series sample}
#: (_corr_group_prices).
_CORR_GROUP_PRICES: Dict[Tuple[str, int, int, Tuple[int, ...]], Dict[int, float]] = {}

#: Series samples a group is priced over: about the half million a middle stage's call
#: covers, so a price carries the call's fixed costs (the forward's latency, a partly filled
#: last round of workgroups) in the proportion the call does.
_GROUP_PRICE_SPAN = 1 << 19


def _corr_group_prices(cands, rows, taps, device):
    """{n: seconds per row per series sample} of continuous correlation at each transform
    size of `cands`, for a group of `rows` templates of at most `taps` (data-rate) taps,
    measured at that shape: a call over _GROUP_PRICE_SPAN samples of a real series in device
    memory into device output, as the middle stage calls it, timed by the device's timers
    (else the host clock). The sizes are timed in turn, round after round
    (_choice.fastest_of_rounds): an idle GPU's clock ramps over the first calls and moved one
    call's device time 3x (0.65 to 2.1 ms on a Radeon 8060S), so sizes priced one after the
    other ranked by when they ran. Kept in MF_COST_FILE under the kernels they timed.

    The per-size model (_corr_block_costs) is measured at 2 and 16 templates of n/4 taps and
    extrapolated; it priced n=16384 at 1.8x its device time for the middle stage's 18 rows
    of 5720 taps (n=32768 within 5%), so a bank ran at 32768, which spills registers there
    and is 6% slower over a whole call and 18% over the real job's shorter calls."""
    cands = tuple(sorted(int(n) for n in cands))
    dev = _parse_device(device)
    dkey = str(device)
    kids = ";".join(_corr_kernel_id(n, getattr(dev, "backend", None)) for n in cands)
    key = "corrgroup2,%s,%d,%d,%s|k%s" % (dkey, int(rows), int(taps),
                                         ";".join(map(str, cands)), kids)
    mkey = (dkey, int(rows), int(taps), cands)

    def measure():
        v = _corr_group_measure(cands, int(rows), int(taps), device)
        ok = all(p > 0 for p in v.values())
        return v, ({"prices": {str(n): p for n, p in v.items()}} if ok else None)

    def read(r):
        if not (isinstance(r, dict) and isinstance(r.get("prices"), dict)):
            return None
        try:
            v = {int(n): float(p) for n, p in r["prices"].items()}
        except (TypeError, ValueError):
            return None
        return v if set(v) == set(cands) and all(p > 0 for p in v.values()) else None
    return price_once(_CORR_GROUP_PRICES, mkey, "choice|" + key, measure, read)


def _corr_group_measure(cands, rows, taps, device):
    """_corr_group_prices' measurement: per size, the fastest of 5 rounds that time every size
    once in turn; device time where the call's submissions recorded one, else the host time
    of the waited call."""
    from . import CorrelationFilter
    from . import gatechain
    length = _GROUP_PRICE_SPAN + max(cands)
    runs = {}
    for n in cands:
        half = min(int(taps) // 2, n // 2 - 1)
        cf = CorrelationFilter(n, ndata=1, ntemplates=rows, valid=(half, n - half), device=device)
        cf.set_templates(np.zeros((rows, n), np.complex64))     # values do not move the time
        ser = cf.empty_shared((length,), np.float32)
        ser[:] = np.random.default_rng(7).standard_normal(length)
        st, _, _ = _automatic_series_layout(length, cf.valid)
        dest = cf.empty_shared((rows, length))
        runs[n] = (cf._gpu, lambda cf=cf, ser=ser, st=st, dest=dest:
                   cf._continuous_gpu(ser, st, 0, rows, dest))

    def time_one(n):
        # The context's timers on for this call (as the GPU calibration times its calls),
        # its own entries read and dropped, the log and the setting left as they were.
        ctx, call = runs[n]
        was = getattr(ctx, "_timing", False)
        ctx._timing = True
        first = len(ctx.timings())
        try:
            t0 = time.perf_counter()
            call()
            host = time.perf_counter() - t0
            log = ctx.timings()
            dev_s = gatechain._run_ms(log[first:]) * 1e-3
            del log[first:]
        finally:
            ctx._timing = was
        return dev_s if dev_s > 0 else host
    for _, call in runs.values():
        call()                                  # warm-up: recordings and uploads
    best = _choice.fastest_of_rounds(list(cands), time_one, 5)
    return {n: (best[n] / (rows * length) if best[n] > 0 else 0.0) for n in cands}


def _corr_group_size(ns, n_model, rows, taps, device):
    """The transform size a GPU bank's group of `rows` templates of at most `taps` taps runs
    at: of the model's choice n_model and its neighbours n/2 and 2n among ns (each long
    enough for the taps), the one _corr_group_prices measures cheapest at the group's shape.
    A neighbour replaces the model's choice only when it is cheaper by more than
    _choice.TIE, so measurement noise does not move a bank between sizes run to run."""
    cands = [m for m in (n_model // 2, n_model, 2 * n_model) if m in ns and m - taps >= 1]
    if len(cands) < 2:
        return n_model
    # Priced at the taps rounded up to a sixteenth of the shortest candidate: a pycbc job's
    # middle banks (one per top template) then share prices -- 62 tops priced 62 shapes at
    # about 46 ms each, 2.9 s of setup -- and a sixteenth moves a size's valid span, and so
    # its price, by at most 1/15.
    q = max(1, min(cands) // 16)
    shape_taps = -(-int(taps) // q) * q
    if min(cands) - shape_taps < 1:
        shape_taps = int(taps)
    prices = _corr_group_prices(cands, rows, shape_taps, device)
    if not all(prices.get(m, 0) > 0 for m in cands):
        return n_model
    best = min(cands, key=prices.get)
    return best if prices[best] < prices[n_model] * (1.0 - _choice.TIE) else n_model


def _batch_target(n: int, max_batch: Optional[int]) -> int:
    """Templates per group: the bank's cache-resident sizing, or the caller's bound."""
    if max_batch is not None:
        return int(max_batch)
    l2 = int(_core.l2_bytes())
    cap = 1024 if l2 >= 1048576 else 512
    return min(cap, max(32, 1048576 // (max(64, int(n) // 8) * 8)))


def _corr_partition(counts, candidate_ns=(2048, 4096, 8192, 16384, 32768, 65536),
                    max_batch=None, device=None):
    """The continuous correlation's partition of filters of these tap counts into block sizes:
    by calibrated cost (_corr_layout), else by the valid-fraction rule. Continuous correlation
    outputs every lag whatever the blocking, so this is a pure cost choice. Returns
    (groups, order) as _partition_templates."""
    layout = _corr_layout(counts, candidate_ns, max_batch, device)
    if layout is not None:
        return layout
    return _partition_templates(counts, max_batch=max_batch, candidate_ns=candidate_ns,
                                engine='corr', device=device)


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
            a, b, w = _corr_block_costs(n, device)
            cap = _batch_target(n, max_batch)
            i0 = max(0, j - cap)
            i = np.arange(i0, j)
            c = best[i0:j] + (a + (j - i) * (b + w * nv)) / nv
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
