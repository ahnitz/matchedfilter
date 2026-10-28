"""Run-list interval algebra used by the continuous correlation's copy and zeroing."""
import numpy as np
import pytest

from matchedfilter.time_domain import _intersect_runs, _interval_runs


def _interval_mask(S, starts, stops):
    """The reference: a boolean mask of length S that is True on the union of
    [starts, stops) clipped to [0, S)."""
    edge = np.zeros(S + 1, dtype=np.int32)
    np.add.at(edge, np.clip(starts, 0, S), 1)
    np.add.at(edge, np.clip(stops, 0, S), -1)
    return np.cumsum(edge[:-1]) > 0


def _mask(S, runs):
    m = np.zeros(S, bool)
    for a, b in runs:
        m[a:b] = True
    return m


@pytest.mark.parametrize("seed", range(40))
def test_runs_match_the_mask(seed):
    rng = np.random.default_rng(seed)
    S = int(rng.integers(1, 300))
    k = int(rng.integers(0, 12))
    a = rng.integers(-20, S + 20, k)
    b = a + rng.integers(0, 60, k)          # callers never pass stop < start
    runs = _interval_runs(S, a, b)
    np.testing.assert_array_equal(_mask(S, runs), _interval_mask(S, a, b))
    # Sorted, disjoint and non-touching: a touching pair would be one run.
    assert np.all(runs[:, 0] < runs[:, 1])
    assert np.all(runs[1:, 0] > runs[:-1, 1])
    c = rng.integers(-20, S + 20, k + 1)
    d = c + rng.integers(0, 60, k + 1)
    other = _interval_runs(S, c, d)
    both = _intersect_runs(runs, other)
    np.testing.assert_array_equal(_mask(S, both), _interval_mask(S, a, b) & _interval_mask(S, c, d))


def test_touching_and_nested_intervals_merge():
    runs = _interval_runs(100, np.array([10, 20, 12, 50]), np.array([20, 30, 15, 60]))
    np.testing.assert_array_equal(runs, [[10, 30], [50, 60]])
    assert _interval_runs(10, np.array([5]), np.array([5])).shape == (0, 2)
