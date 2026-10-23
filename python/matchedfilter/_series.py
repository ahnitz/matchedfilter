"""Validated windows and optional row ordering shared by series executors."""
import numpy as np


class SeriesLayout:
    """Blocks of a series call: starts, windows [low, high) and, as phase, each block's bin
    phase (uint32, below 2**24; None for all 0): block b's bins are numbered from
    low[b] - phase[b] (matchedfilter.h, ap_mf_run_series); bins before low[b] are empty."""

    def __init__(self, n, starts, low, high, binsize, ragged=False, phase=None):
        self.order = None
        self.groups = None
        self.ragged = False
        self.starts = starts
        self.phase = None
        if phase is not None:
            phase = np.ascontiguousarray(phase, dtype=np.uint32)
            if phase.shape != starts.shape:
                raise ValueError('bin_phase needs one entry per block')
            if np.any(phase >= 1 << 24):
                raise ValueError('bin_phase must be below 2**24')
            if np.any(phase):
                self.phase = phase
        limit = np.iinfo(np.intp).max
        if self.phase is not None:
            self._phased(n, low, high, binsize, ragged, limit)
            return
        if low.size == 1 or (np.all(low == low[0]) and np.all(high == high[0])):
            lo, hi = int(low[0]), int(high[0])
            if lo > limit or hi > limit:
                raise ValueError('window offsets must be nonnegative and fit in the index range')
            lo, hi = min(lo, n), min(hi, n)
            if lo >= hi:
                raise ValueError('every block must have a nonempty search window')
            self.low = low if lo == int(low[0]) else np.full_like(low, lo)
            self.high = high if hi == int(high[0]) else np.full_like(high, hi)
            self.nbins = 1 + (hi - lo - 1) // binsize
            self.groups = [(lo, hi, 0, low.size)]
            return
        if np.any(low > limit) or np.any(high > limit):
            raise ValueError('window offsets must be nonnegative and fit in the index range')
        self.low = np.minimum(low, n)
        self.high = np.minimum(high, n)
        if np.any(self.low >= self.high):
            raise ValueError('every block must have a nonempty search window')
        widths = self.high - self.low
        # Avoid unsigned/object arithmetic for a Python binsize above uintp.
        bins = np.ones_like(widths) if binsize >= n else 1 + (widths - 1) // binsize
        self.nbins = int(bins.max()) if ragged else int(bins[0])
        if not ragged and np.any(bins != self.nbins):
            raise ValueError('every block\'s window must give the same bin count; '
                             'call run_series once per distinct bin count')

    def _phased(self, n, low, high, binsize, ragged, limit):
        if np.any(low > limit) or np.any(high > limit):
            raise ValueError('window offsets must be nonnegative and fit in the index range')
        self.low = np.minimum(low, n)
        self.high = np.minimum(high, n)
        if np.any(self.low >= self.high):
            raise ValueError('every block must have a nonempty search window')
        bins = (self.high - self.low + self.phase.astype(self.high.dtype) + binsize - 1) // binsize
        self.nbins = int(bins.max()) if ragged else int(bins[0])
        if not ragged and np.any(bins != self.nbins):
            raise ValueError('every block\'s window and bin phase must give the same bin count; '
                             'call run_series once per distinct bin count')
        if np.all(low == low[0]) and np.all(high == high[0]):
            self.groups = [(int(self.low[0]), int(self.high[0]), 0, low.size)]

    def group(self, *, materialize=True):
        """Group repeated windows, keeping original order when already grouped."""
        if self.groups is not None:
            return self
        low, high = self.low, self.high
        cuts = np.flatnonzero((low[1:] != low[:-1]) | (high[1:] != high[:-1])) + 1
        if not cuts.size:
            self.groups = [(int(low[0]), int(high[0]), 0, low.size)]
            return self
        begin = np.r_[0, cuts]
        windows = np.stack((low[begin], high[begin]), axis=1)
        sort = np.lexsort((windows[:, 1], windows[:, 0]))
        ordered = windows[sort]
        if np.any(np.all(ordered[1:] == ordered[:-1], axis=1)):
            self.order = np.lexsort((self.starts, high, low))
            self.starts = self.starts[self.order]
            if self.phase is not None:
                self.phase = self.phase[self.order]
            low = self.low = low[self.order]
            high = self.high = high[self.order]
            if materialize:
                cuts = np.flatnonzero((low[1:] != low[:-1]) | (high[1:] != high[:-1])) + 1
        if not materialize:
            return self
        edges = np.r_[0, cuts, low.size]
        self.groups = [(int(low[a]), int(high[a]), int(a), int(b))
                       for a, b in zip(edges[:-1], edges[1:])]
        return self
