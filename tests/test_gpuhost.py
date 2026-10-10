"""The backend-neutral GPU host helpers (_gpuhost): layouts every backend must agree on."""
import numpy as np
import pytest

from matchedfilter._errors import UnsupportedSize
from matchedfilter._gpuhost import (bin_shift, plan_items, split_items, hier_tiers, hier_window,
                                    split_bins, padded_rows, grouped_windows)


def test_bin_shift():
    assert [bin_shift(b) for b in (1, 2, 64, 1024)] == [0, 1, 6, 10]
    assert bin_shift(48) == -1 and bin_shift(np.int64(256)) == 8


@pytest.mark.parametrize("align", [1, 16, 64])
def test_plan_and_split_items(align):
    items = [(0, 100, 0, 3, 0), (5, 9, 2, 4, 1), (0, 2048, 1, 2, 2)]
    offs, nbs, size = plan_items(items, 16, align)
    assert nbs == [7, 1, 128]
    assert all(o % align == 0 for o in offs)
    counts = [(b - a) * nb for (_, _, a, b, _), nb in zip(items, nbs)]
    for o, c, nxt in zip(offs, counts, offs[1:] + [size]):
        assert o + c <= nxt                       # items never overlap
    idx = np.arange(size, dtype=np.int32)
    val = idx.astype(np.complex64)
    out = split_items(items, offs, nbs, idx, val, copy=True)
    for (i, v), (_, _, a, b, _), o, nb in zip(out, items, offs, nbs):
        assert i.shape == (b - a, 1, nb) and v.shape == i.shape
        assert i.ravel()[0] == o and np.array_equal(v.real, i)


def test_plan_items_bin_limit():
    with pytest.raises(UnsupportedSize):
        plan_items([(0, 100, 0, 1, 0)], 1, 1, max_bins=64)


def test_hier_tiers_and_window():
    assert hier_tiers(4096, (256, 1024), ("c0", "c1"), (1.0, 2.0)) == \
        (1024, "c0", 1.0, 256, "c1", 2.0)
    assert hier_tiers(4096, 512, "c0", 3.0) == (512, "c0", 3.0, None, None, None)
    with pytest.raises(ValueError):
        hier_tiers(4096, 1024, "c0", 1.0, cascade_band=256)
    assert hier_window(4096, None, None) == (0, 4096, 4096, 1)
    assert hier_window(4096, (-5, 5000), 100) == (0, 4096, 100, 41)
    with pytest.raises(ValueError):
        hier_window(4096, (10, 10), 1)


@pytest.mark.parametrize("sparse", [False, True])
@pytest.mark.parametrize("async_submit", [False, True])
def test_split_bins_matches_one_call(sparse, async_submit):
    calls = []

    def call(w, ud, ut):
        calls.append((w, ud, ut))
        nb = -(-(w[1] - w[0]) // 4)
        idx = np.where(np.arange(nb) % 3 == 0, np.arange(w[0], w[1], 4), -1)
        idx = np.broadcast_to(idx, (2, 3, nb)).astype(np.int32)
        return idx, idx.astype(np.complex64)
    res = split_bins(call, 0, 100, 4, 10, True, True, sparse, async_submit)
    if async_submit:
        assert callable(res)
        res = res()
    assert [c[0] for c in calls] == [(0, 40), (40, 80), (80, 100)]
    assert [c[1:] for c in calls] == [(True, True), (False, False), (False, False)]
    if sparse:
        assert res.shape == (2, 3, 25)
    else:
        assert res[0].shape == (2, 3, 25)


def test_padded_rows_and_grouped_windows():
    assert padded_rows(5, 3, 4) == 8 and padded_rows(4, 2, 8) == 4 and padded_rows(7, 1, 1) == 7
    groups, nb = grouped_windows([(0, 100, 0, 2), (10, 90, 2, 5)], 4096, 5, 16)
    assert nb == 7 and groups[1] == (10, 90, 2, 5)
    with pytest.raises(ValueError):
        grouped_windows([(0, 10, 0, 2), (0, 100, 2, 3)], 4096, 5, 16)
    with pytest.raises(ValueError):
        grouped_windows([(0, 10, 0, 6)], 4096, 5, 16)


def test_grouped_row_windows():
    from matchedfilter._gpuhost import grouped_row_windows
    g, nb, win, (lo0, hi0) = grouped_row_windows([(100, 900, 0, 2), (0, 1024, 2, 5)], 1024, 5, 256)
    assert nb == 4 and (lo0, hi0) == (100, 1024)           # clipped to n, still 4 bins
    assert win.tolist() == [100, 900, 100, 900, 0, 1024, 0, 1024, 0, 1024]
    assert not win.flags.writeable
    assert grouped_row_windows([(100, 900, 0, 2), (0, 1024, 2, 5)], 1024, 5, 256)[2] is win
    g, nb, win, w = grouped_row_windows([(0, 300, 0, 1)], 1024, 1, 256, nbins=3)
    assert nb == 3 and w == (0, 768)
