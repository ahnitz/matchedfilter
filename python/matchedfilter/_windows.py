"""Analysis windows over a series: the one parser every caller uses (_normalize_windows) and
how a template group's blocks are laid out to cover them (_window_layout)."""
import numpy as np

from . import _core


def coarse_lags(n, band, lo, hi):
    """(c0, c1): the coarse lags [c0, c1) a tier at `band` searches for the window [lo, hi)
    of an n-point block -- one band sample past each end (a signal near an end has coarse
    samples on both sides), inside the band, at least one. The engine's rule (hmf.c), and
    every host's and the gate model's: lo and hi are ints or integer arrays alike."""
    r = n // band
    if np.ndim(lo) == 0 and np.ndim(hi) == 0:
        c0 = int(lo) // r
        c0 = c0 - 1 if c0 > 0 else c0
        return c0, max(c0 + 1, min(band, -(-int(hi) // r) + 1))
    lo, hi = np.asarray(lo, np.int64), np.asarray(hi, np.int64)
    c0 = lo // r
    c0 = np.where(c0 > 0, c0 - 1, c0)
    return c0, np.maximum(c0 + 1, np.minimum(band, -(-hi // r) + 1))


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


def _window_layout(g, W: np.ndarray, S: int):
    """Block entries (start, window start, window end) for normalised windows W.

    One entry per (block, window) pair: two windows inside one block give
    two entries for the same start, each with its own peak-search span, so
    a peak in the gap can never be reported or displace a real one.
    Per window this is the bank's established vectorised layout."""
    STEP = g.n_valid
    c_bad = g.c_bad
    parts_t, parts_s, parts_e = [], [], []
    for v_start, v_stop in W.tolist():
        first_block_idx = max(0, (v_start - c_bad) // STEP)
        # Only starts whose valid span can intersect this window. Building the
        # whole remaining series per narrow window makes sparse layouts quadratic.
        ts = np.arange(first_block_idx * STEP, min(S, v_stop - c_bad), STEP,
                       dtype=np.int64)
        if not ts.size:
            continue
        # The first block ends after v_start and the exclusive stop keeps every
        # block's valid start before v_stop, so every generated block intersects.
        bvt0 = ts + c_bad
        rs = np.maximum(v_start, bvt0)
        re = np.minimum(v_stop, bvt0 + STEP)
        parts_t.append(ts); parts_s.append(rs - ts); parts_e.append(re - ts)
    if not parts_t:
        empty = np.empty(0, np.uintp)
        return empty, empty, empty
    cat = (lambda xs: np.ascontiguousarray(np.concatenate(xs), dtype=np.uintp))
    return cat(parts_t), cat(parts_s), cat(parts_e)


def _window_bin_phases(W: np.ndarray, starts: np.ndarray, ws: np.ndarray, binsize: int):
    """Each block entry's bin phase on its window's bin grid, or None if every one is 0.

    Window [v0, v1) has bins v0 + k*binsize; an entry searching from absolute sample
    a = starts + ws numbers its bins from a - phase, phase = (a - v0) mod binsize, so its
    bins are the window's (matchedfilter.h, ap_mf_run_series' bin_phase)."""
    a = starts.astype(np.int64) + ws.astype(np.int64)
    v0 = W[np.searchsorted(W[:, 0], a, side='right') - 1, 0]
    ph = ((a - v0) % int(binsize)).astype(np.uint32)
    return ph if ph.any() else None


def _merge_window_bins(W: np.ndarray, binsize: int, t, s, v, *rest):
    """The peaks of partial bins merged into their window bins: per (template, window,
    bin) the largest |v|, the earlier sample on a tie (the scans' own rule). The arrays
    (and any in rest, aligned with them) come back filtered, in their original order."""
    if s.size < 2:
        return (t, s, v) + rest
    if t.dtype == np.int64 and s.dtype in (np.int64, np.float64) and v.dtype == np.complex64:
        # Ordered by template, then sample (a follow-up window; a bank's peaks in template
        # order): a window bin's partial bins are adjacent runs, merged in one pass. This
        # runs once per follow-up window, where a dozen array operations cost more than the
        # filtering.
        keep = np.empty(s.size, np.int64)
        kept = _core.window_bin_keep(np.ascontiguousarray(W[:, 0], np.int64), int(binsize),
                                     np.ascontiguousarray(t), np.ascontiguousarray(s),
                                     np.ascontiguousarray(v), keep, s.dtype == np.float64)
        if kept == s.size:
            return (t, s, v) + rest
        if kept >= 0:
            keep = keep[:kept]
            return tuple(x[keep] for x in (t, s, v) + rest)
    wi = np.searchsorted(W[:, 0], s, side='right') - 1
    b = (s - W[wi, 0]) // int(binsize)
    order = np.lexsort((s, -np.abs(v), b, wi, t))
    key = np.stack((t[order], wi[order], b[order]))
    first = np.r_[True, np.any(key[:, 1:] != key[:, :-1], axis=0)]
    keep = np.sort(order[first])
    if keep.size == s.size:
        return (t, s, v) + rest
    return tuple(a[keep] for a in (t, s, v) + rest)
