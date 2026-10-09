"""The backend-neutral GPU host helpers (_gpuhost): layouts every backend must agree on."""
import numpy as np
import pytest

from matchedfilter._errors import UnsupportedSize
from matchedfilter._gpuhost import bin_shift, plan_items, split_items


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
