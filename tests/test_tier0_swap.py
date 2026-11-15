"""gatechain._best_swap finds, for an unmatched template, the swap that pairs it and another
unmatched one by breaking a matched pair (cluster_tier0_candidates). Checked against the plain
loop over the other unmatched templates that it replaced, with scores that tie."""
import numpy as np
import pytest

from matchedfilter import gatechain as gc


def _loop(scores, u, vs, w_arr, z_arr, floor):
    """The loop the vectorised search replaced: every v in order, u on w's side then on z's,
    a swap taken only when its gain is strictly larger than the best so far."""
    uw_ok = scores[u, w_arr] >= floor
    uz_ok = scores[u, z_arr] >= floor
    best_gain, best = -1.0, None
    for v in (int(x) for x in vs):
        hit = np.flatnonzero(uw_ok & (scores[v, z_arr] >= floor))
        if hit.size:
            gains = scores[u, w_arr[hit]] + scores[v, z_arr[hit]]
            e = int(hit[int(np.argmax(gains))])
            gain = float(scores[u, w_arr[e]] + scores[v, z_arr[e]])
            if gain > best_gain:
                w, z = int(w_arr[e]), int(z_arr[e])
                best_gain, best = gain, (e, v, (min(u, w), max(u, w)), (min(v, z), max(v, z)))
        hit = np.flatnonzero(uz_ok & (scores[v, w_arr] >= floor))
        if hit.size:
            gains = scores[u, z_arr[hit]] + scores[v, w_arr[hit]]
            e = int(hit[int(np.argmax(gains))])
            gain = float(scores[u, z_arr[e]] + scores[v, w_arr[e]])
            if gain > best_gain:
                w, z = int(w_arr[e]), int(z_arr[e])
                best_gain, best = gain, (e, v, (min(u, z), max(u, z)), (min(v, w), max(v, w)))
    return best


def _case(rng, m, pairs, levels):
    """m nodes, the first 2 * pairs of them matched in pairs, scores drawn from `levels`
    values (few levels: many equal gains), symmetric."""
    upper = np.triu(rng.integers(0, levels, (m, m)).astype(np.float32) / levels, 1)
    scores = upper + upper.T
    order = rng.permutation(2 * pairs)
    w_arr, z_arr = order[:pairs].astype(np.int32), order[pairs:].astype(np.int32)
    free = np.arange(2 * pairs, m)
    return scores, w_arr, z_arr, free


@pytest.mark.parametrize("levels", [2, 3, 5, 1000])
def test_matches_the_loop_it_replaced(levels):
    rng = np.random.default_rng(levels)
    found = same_gain_seen = 0
    for _ in range(300):
        m, pairs = int(rng.integers(6, 30)), int(rng.integers(1, 3))
        scores, w_arr, z_arr, free = _case(rng, m, pairs, levels)
        floor = float(rng.choice([0.3, 0.5, 0.7]))
        for i, u in enumerate(free[:-1]):
            vs = free[i + 1:][rng.random(free.size - i - 1) < 0.8]       # some already used
            want = _loop(scores, int(u), vs, w_arr, z_arr, floor)
            assert gc._best_swap(scores, int(u), vs, w_arr, z_arr, floor) == want
            found += want is not None
    assert found > 200                                 # swaps exist in these cases


def test_ties_go_to_the_first():
    """Two v's and two pairs that all give the same gain: the first v, u on w's side, the
    first pair."""
    scores = np.full((6, 6), 0.9, np.float32)
    w_arr, z_arr = np.array([0, 2], np.int32), np.array([1, 3], np.int32)
    assert gc._best_swap(scores, 4, np.array([5]), w_arr, z_arr, 0.5) == (0, 5, (0, 4), (1, 5))
    # u cannot stand on w's side of pair 0: the next in order is pair 1, still on w's side
    scores[4, 0] = scores[0, 4] = 0.1
    assert gc._best_swap(scores, 4, np.array([5]), w_arr, z_arr, 0.5) == (1, 5, (2, 4), (3, 5))


def test_no_swap():
    scores = np.full((6, 6), 0.2, np.float32)
    w_arr, z_arr = np.array([0, 2], np.int32), np.array([1, 3], np.int32)
    assert gc._best_swap(scores, 4, np.array([5]), w_arr, z_arr, 0.5) is None
    assert gc._best_swap(scores, 4, np.array([], np.int64), w_arr, z_arr, 0.1) is None
