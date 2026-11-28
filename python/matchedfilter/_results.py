"""The result containers every layer hands back: the structured peak dtype, a sparse
peak table, and a submitted-but-uncollected result."""
import weakref
from typing import NamedTuple

import numpy as np

from . import _core


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
            if sp.flat.size:
                flats.append(sp.flat + b0 * per_block)
                idxs.append(sp.idx)
                vals.append(sp.val)
        if not flats:
            return _SparsePeaks(shape, np.empty(0, np.int64), np.empty(0, np.int64),
                                np.empty(0, np.complex64))
        flat = np.concatenate(flats)
        idx = np.concatenate(idxs)
        val = np.concatenate(vals)
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


class _CallParts:
    """A hierarchical GPU call's result as its parts, for the extension's assembly
    (_core.assemble_peaks): per batch of blocks its first block and its result in flight (a
    Pending, whose readback the assembly reads where the device wrote it) or already
    collected. A filter_series call holds one per call; a deferred call is also the owner of
    the plan's slots it used (MatchedFilter._slot_owner), so a later call collects it before
    reusing them. order and shape are the call's: its layout's block order (the output row of
    each computed row) or None, and (blocks, templates, bins). The plan is held by weak
    reference (its slot owners hold this: a strong one made a cycle that kept a dropped bank's
    plans and their device buffers until the collector ran) and its work counters directly."""
    __slots__ = ("parts", "plan", "work", "order", "shape")

    def __init__(self, parts, plan, order, shape):
        self.parts, self.plan, self.work = parts, weakref.ref(plan), plan._gwork
        self.order, self.shape = order, shape

    @property
    def _done(self):
        """Whether every part has been collected (MatchedFilter._next_batch_base)."""
        return all(getattr(item, "done", True) for _, item in self.parts)

    def result(self):
        """Collect every part still in flight into host arrays, as a later call on the same
        slots needs (their buffers are about to be reused); the parts stay for take()."""
        for _, item in self.parts:
            if not getattr(item, "done", True):
                item()

    def take(self):
        """The parts as assemble_peaks reads them, once: [(first block, part)], a part the
        readback tuple of a run collected now, or the host result of one collected earlier,
        whose counts are added to the plan's work counters here (the assembly adds a
        readback's). Returns the list."""
        out = []
        for b0, item in self.parts:
            take = getattr(item, "take", None)
            if take is not None:
                live, value = take()
            elif callable(item):
                live, value = False, item()     # a collector without a readback (split bins)
            else:
                out.append((b0, item))          # a synchronous result, already counted
                continue
            plan = self.plan()
            if not live and plan is not None:
                plan._account(value)
            out.append((b0, value))
        self.parts = ()
        return out


class _PeaksJob(_Deferred):
    """A filter_series call's peaks, assembled in the extension when first asked for
    (_core.assemble_peaks, the step table's assembly): its calls, each (the bank index of each
    template of its result, the blocks' starts in output order, each block's bin count where
    one call computed several or None, the block length, the result: _CallParts, a deferred
    result, or a host result), the window starts and the bin sizes whose partial bins
    merge. The jobs of one batch (filter_series_many) share a _PeaksBatch: the first
    job asked assembles them all in one extension call."""
    __slots__ = ("calls", "win_starts", "merge_bs", "batch")

    def __init__(self, calls, win_starts, merge_bs):
        super().__init__(None)
        self.calls, self.win_starts, self.merge_bs, self.batch = calls, win_starts, merge_bs, None

    def spec(self):
        """The job as assemble_peaks takes it, its parts taken (once): (calls, window starts,
        merge bin sizes)."""
        calls = []
        for templates, starts, row_bins, block_len, res in self.calls:
            if isinstance(res, _CallParts):
                calls.append(((templates, starts, res.order, row_bins, res.shape[1], res.shape[2],
                               block_len, res.work), res.take()))
                continue
            if isinstance(res, _Deferred):
                res = res.result()
            shape = res.shape if isinstance(res, _SparsePeaks) else res[0].shape
            calls.append(((templates, starts, None, row_bins, shape[1], shape[2], block_len, None),
                          ((0, res),)))
        self.calls = ()
        return calls, self.win_starts, self.merge_bs

    def result(self):
        if not self._done:
            if self.batch is not None:
                self.batch.collect()
            else:
                _assemble_jobs([self])
        return self._value


class _PeaksBatch:
    """The jobs of one filter_series_many batch, assembled together (_PeaksJob)."""
    __slots__ = ("jobs",)

    def __init__(self, jobs):
        self.jobs = jobs
        for job in jobs:
            job.batch = self

    def collect(self):
        """Assemble every job not yet assembled, in one extension call."""
        jobs = [job for job in self.jobs if not job._done]
        self.jobs = ()
        _assemble_jobs(jobs)


def _assemble_jobs(jobs):
    """Assemble jobs (_PeaksJob) in one extension call: each job's FilterResults, slices of one
    arena (the empty result for a job without peaks), becomes its value. Returns nothing."""
    offsets, *columns = _core.assemble_peaks([job.spec() for job in jobs])
    offsets = np.frombuffer(offsets, np.int64)
    columns = [np.frombuffer(c, d) for c, d in zip(columns, _ARENA_DTYPES)]
    for k, job in enumerate(jobs):
        lo, hi = int(offsets[k]), int(offsets[k + 1])
        job._value = (FilterResults(*(c[lo:hi] for c in columns)) if hi > lo
                      else _EMPTY_FILTER_RESULTS)
        job._done = True


#: The arena's columns (_core.assemble_peaks, _core.HMFTable.run), as FilterResults has them.
_ARENA_DTYPES = (np.int64, np.int64, np.complex64, np.int64, np.int64)


class FilterResults(NamedTuple):
    """The peaks a time-domain filtering call found, one entry per peak.

    Attributes
    ----------
    template_indices : ndarray
        int64, the template's index in the bank's input.
    sample_indices : ndarray
        int64, the peak's sample in the series.
    snr : ndarray
        complex64, the peak's complex SNR.
    block_starts : ndarray
        int64, the first sample of the block that found it.
    block_lengths : ndarray
        int64, the FFT block length that found it.
    """
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
