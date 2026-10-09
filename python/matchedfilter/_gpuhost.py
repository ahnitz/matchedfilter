"""Backend-neutral host logic shared by the Vulkan, CUDA and Metal GPU backends.

Everything here is pure Python/NumPy over plain integers and arrays: what to dispatch and
how results are laid out, never how. Each backend keeps its own submission mechanism
(command buffers and fences, streams and graphs, Metal command buffers) and calls these
helpers for the parts that must agree across backends. See docs/cross-platform-review.md
section 3.1 for the layer this is growing into.
"""

from ._errors import UnsupportedSize

#: Most bins one peak kernel dispatch reduces into (the kernels' compiled limit).
MAX_BINS = 2048


def bin_shift(binsize):
    """log2(binsize) when binsize is a power of two, else -1 (the kernels divide)."""
    binsize = int(binsize)
    return binsize.bit_length() - 1 if binsize & (binsize - 1) == 0 else -1


def plan_items(items, binsize, align_words=1, max_bins=MAX_BINS):
    """Output layout of a peaks_items submission.

    items are (lo, hi, a, b, t): rows a:b against template t over [lo, hi). Each item's
    (b - a, nbins) results start at a multiple of align_words 4-byte words -- a backend
    that selects them by descriptor offset passes its storage-offset alignment, one that
    uses pointers passes 1. Returns (offsets, nbins per item, total words)."""
    offs, nbs, size = [], [], 0
    for lo, hi, a, b, t in items:
        nb = -(-(hi - lo) // binsize)
        if nb > max_bins:
            raise UnsupportedSize("an item's window exceeds the kernel bin limit")
        offs.append(size)
        nbs.append(nb)
        size += -(-((b - a) * nb) // align_words) * align_words
    return offs, nbs, size


def split_items(items, offs, nbs, indices, values, copy=False):
    """Per item (idx, val) shaped (b - a, 1, nbins) from the flat readback of plan_items.
    copy=True when the flat arrays are a reused host buffer."""
    out = []
    for (lo, hi, a, b, t), off, nb in zip(items, offs, nbs):
        c = (b - a) * nb
        i = indices[off:off + c].reshape(b - a, 1, nb)
        v = values[off:off + c].reshape(b - a, 1, nb)
        out.append((i.copy(), v.copy()) if copy else (i, v))
    return out
