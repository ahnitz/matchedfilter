"""Sparse window planning visits only blocks near each requested interval."""
from types import SimpleNamespace

import numpy as np

from matchedfilter.time_domain import TimeDomainFilterBank, _normalize_windows


def test_sparse_layout_matches_independent_block_intersections():
    rng = np.random.default_rng(2048)
    for step, margin, length in ((1798, 125, 20000), (31, 17, 1000), (17, 0, 100)):
        group = SimpleNamespace(n_valid=step, c_bad=margin)
        for _ in range(20):
            starts = rng.integers(-length, length, 20)
            windows = _normalize_windows([(int(a), int(a + rng.integers(1, 200)))
                                          for a in starts], length)
            want = []
            for a, b in windows:
                for block in range(0, length, step):
                    lo, hi = max(a, block + margin), min(b, block + margin + step)
                    if lo < hi:
                        want.append((block, lo - block, hi - block))
            got = TimeDomainFilterBank._window_layout(group, windows, length)
            np.testing.assert_array_equal(np.stack(got, axis=1),
                                           np.asarray(want, dtype=np.uintp).reshape(-1, 3))


def test_sparse_layout_does_not_materialize_series_tail(monkeypatch):
    real_arange = np.arange
    visits = []

    def track(*args, **kwargs):
        result = real_arange(*args, **kwargs)
        visits.append(result.size)
        return result

    monkeypatch.setattr(np, "arange", track)
    group = SimpleNamespace(n_valid=1798, c_bad=125)
    windows = np.array([[1000, 1020], [1000000, 1000020]], dtype=np.int64)
    result = TimeDomainFilterBank._window_layout(group, windows, 1 << 26)
    assert result[0].size == 2
    assert sum(visits) == 2
