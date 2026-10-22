"""The result containers every layer hands back: the structured peak dtype, a sparse
peak table, and a submitted-but-uncollected result."""
from typing import NamedTuple

import numpy as np


#: dtype of the arrays returned by :meth:`MatchedFilter.run`.
#: A peak is WHERE and WHAT, nothing else. The magnitude used to be a third
#: field and was always abs(value) to the last bit, so it carried no
#: information -- it cost a field copy on assembly, a buffer, and on the GPU
#: a third output array and a sqrt per bin. Callers who want it write
#: np.abs(peaks["value"]).
PEAK_DTYPE = np.dtype([("index", "<i8"), ("value", "<c8")])


class _SparsePeaks:
    """The peaks of a (blocks, templates, bins) result, sparse: flat indices into that shape,
    sample indices and values, in C order. What a GPU returns when a caller asks (``_want_sparse``): at a detection threshold almost every bin is
    empty, and reading back, widening and scanning the dense table cost more host time than
    the device spent on the call."""
    __slots__ = ("shape", "flat", "idx", "val")

    def __init__(self, shape, flat, idx, val):
        self.shape = tuple(shape)
        self.flat = np.asarray(flat, np.int64)
        self.idx = np.asarray(idx, np.int64)
        self.val = np.asarray(val, np.complex64)

    def dense(self):
        idx = np.full(self.shape, -1, np.int64)
        val = np.zeros(self.shape, np.complex64)
        idx.reshape(-1)[self.flat] = self.idx
        val.reshape(-1)[self.flat] = self.val
        return idx, val

    def blocks(self, mask, nbins):
        """The blocks selected by a boolean mask, with their first nbins bins: the sparse
        form of ``(idx[mask][:, :, :nbins], val[mask][:, :, :nbins])``."""
        nt, nb = self.shape[1], self.shape[2]
        b, rest = np.divmod(self.flat, nt * nb)
        t, k = np.divmod(rest, nb)
        mask = np.asarray(mask, bool)
        keep = mask[b] & (k < nbins)
        rank = np.cumsum(mask) - 1
        flat = (rank[b[keep]] * nt + t[keep]) * nbins + k[keep]
        return _SparsePeaks((int(mask.sum()), nt, int(nbins)), flat, self.idx[keep],
                            self.val[keep])

    @staticmethod
    def combine(parts, shape, order=None):
        """One result for a call from (first block, part) pieces; ``order`` maps computed
        block rows to output rows as _format_result does (out[order] = computed)."""
        nt, nb = shape[1], shape[2]
        per_block = nt * nb
        flats, idxs, vals = [], [], []
        for b0, sp in parts:
            flats.append(sp.flat + b0 * per_block)
            idxs.append(sp.idx)
            vals.append(sp.val)
        flat = np.concatenate(flats) if flats else np.empty(0, np.int64)
        idx = np.concatenate(idxs) if idxs else np.empty(0, np.int64)
        val = np.concatenate(vals) if vals else np.empty(0, np.complex64)
        if order is not None and flat.size:
            rows, rest = np.divmod(flat, per_block)
            flat = np.asarray(order, np.int64)[rows] * per_block + rest
        k = np.argsort(flat, kind="stable")
        return _SparsePeaks(shape, flat[k], idx[k], val[k])


class _Deferred:
    """A GPU result submitted but not yet collected; result() waits once and caches.
    empty: True once collected if the gates refined nothing (every slot is -1), so a
    consumer can skip scanning it."""
    __slots__ = ("_finish", "_value", "_done", "empty")

    def __init__(self, finish):
        self._finish, self._value, self._done, self.empty = finish, None, False, False

    def result(self):
        if not self._done:
            self._value, self._finish, self._done = self._finish(), None, True
        return self._value


class FilterResults(NamedTuple):
    template_indices: np.ndarray   # int64: index into original input templates
    sample_indices: np.ndarray     # int64: sample index in continuous series
    snr: np.ndarray                # complex64: peak complex SNR
    block_starts: np.ndarray       # int64: start sample index of the block
    block_lengths: np.ndarray      # int64: FFT block length used for this template


_EMPTY_FILTER_RESULTS = FilterResults(
    template_indices=np.empty(0, dtype=np.int64),
    sample_indices=np.empty(0, dtype=np.int64),
    snr=np.empty(0, dtype=np.complex64),
    block_starts=np.empty(0, dtype=np.int64),
    block_lengths=np.empty(0, dtype=np.int64),
)


# FilterResults is public as matchedfilter.FilterResults and was defined in time_domain:
# its pickles and repr name that module, which still exports it.
FilterResults.__module__ = "matchedfilter.time_domain"
