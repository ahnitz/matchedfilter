"""How a TimeDomainFilterBank lays out its templates: the partition into groups by tap count,
the transform size each group runs at (_corr_layout, priced by _corr_block_costs: the
continuous correlation's per-block costs, measured once per machine), and the batches a group
is split into."""
import math
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np


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
    from .device import parse as _parse_device
    dkey = "cpu" if _parse_device(device).kind == "cpu" else str(device)
    from . import CorrelationFilter, gatechain
    from ._prices import price_once
    path = gatechain._cost_file()
    key = "corr3,%d" % n if dkey == "cpu" else "corr3,%d,%s" % (n, dkey)
    from ._filter import _CORR_PFFT
    if (n, dkey) in _CORR_COSTS:
        return _CORR_COSTS[(n, dkey)]
    measured = []

    def measure():
        measured.append(True)
        rng = np.random.default_rng(7)
        taps = n // 4
        # A GPU call carries a fixed submit-and-wait cost (~0.2 ms on an M2) that production
        # spreads over a whole series of blocks. Over 8 blocks it was most of a(n) and noisy enough
        # to flip the middle bank between n=8192 and 16384 run to run (16384 runs 2.3x slower
        # there), so a GPU is priced over about half a million samples, as the bank calls it.
        nblocks = 8 if dkey == "cpu" else max(8, (1 << 19) // (n - taps))
        L = nblocks * (n - taps) + n
        ser = ((rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
        # CPU: the engine's transform and the platform FFT (vDSP on macOS) are both priced, and
        # the cheaper at a group of 16 templates is the one this n runs (_CORR_PFFT).
        modes = [False]
        if dkey == "cpu":
            probe = CorrelationFilter(n, ndata=1, ntemplates=1, valid=(taps // 2, n - taps // 2),
                                      device='cpu')      # the CPU's price, whatever MF_DEVICE says
            probe.set_templates(np.zeros((1, n), np.complex64))
            if probe._execution_plan().set_platform_fft(True):
                modes.append(True)
        hits = {}
        for mode in modes:
            _CORR_PFFT[n] = mode
            hits[mode] = _corr_measure(n, device, dkey, rng, taps, nblocks, L, ser)
        best_mode = min(hits, key=lambda m: hits[m][0] + 16 * (hits[m][1] + hits[m][2] * (n - taps)))
        hit = hits[best_mode]
        if path is not None and dkey == "cpu":    # a mode another process stored first is used
            best_mode = bool(gatechain._store_first(path, "corr-pfft,%d" % n, bool(best_mode),
                                                    lambda r: isinstance(r, bool)))
            hit = hits.get(best_mode, hit)  # this process timed that mode too
        _CORR_PFFT[n] = best_mode
        return hit, list(hit)
    hit = price_once(_CORR_COSTS, (n, dkey), key, measure,
                     lambda r: tuple(float(v) for v in r[:3]) if isinstance(r, list)
                     and len(r) >= 3 else None)
    if dkey == "cpu" and not measured and path is not None:   # the price came from the file
        _CORR_PFFT[n] = bool(gatechain._load_cost_file(path).get("corr-pfft,%d" % n, False))
    return hit


def _corr_measure(n, device, dkey, rng, taps, nblocks, L, ser):
    """(fixed, per template, per template per output sample) seconds per block through the
    bank's continuous path: 2 and 16 templates with `taps`-tap filters, and 16 with filters
    leaving half the valid span."""
    from . import CorrelationFilter
    from ._filter import _automatic_series_layout
    per_block, valid = [], []
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
            dest = cf.empty_shared((nt, L), readback=not getattr(cf._gpu, 'discrete', False))
            run = lambda: cf._continuous_gpu(ser, st, 0, nt, dest)
        else:
            dest = np.zeros((nt, L), np.complex64)
            ep = cf._continuous_plan()
            run = lambda: ep.correlate_series_continuous(ser, st, lo, hi, 0, nt, dest)
        run()
        best = np.inf
        for _ in range(5):
            t0 = time.perf_counter()
            run()
            best = min(best, time.perf_counter() - t0)
        per_block.append(best / len(st))
        valid.append(hi - lo)
    s1 = max((per_block[1] - per_block[0]) / 14.0, 0.0)        # per template at valid[0]
    w = max((per_block[1] - per_block[2]) / (16.0 * (valid[1] - valid[2])), 0.0)
    b = max(s1 - w * valid[0], 0.0)
    return (max(per_block[0] - 2.0 * s1, 0.0), b, w)


def _batch_target(n: int, max_batch: Optional[int]) -> int:
    """Templates per group: the bank's cache-resident sizing, or the caller's bound."""
    if max_batch is not None:
        return int(max_batch)
    return min(512, max(32, 1048576 // (max(64, n // 8) * 8)))


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
