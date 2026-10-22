"""Analysis windows over a series: the one parser every caller uses (_normalize_windows) and
how a template group's blocks are laid out to cover them (_window_layout)."""
import numpy as np


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
