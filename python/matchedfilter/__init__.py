"""matchedfilter - batched correlation with full or peak-only output.

Correlate D data segments against T templates and report, for each pair, the
loudest sample in each bin of a search window:

    >>> import matchedfilter as mf
    >>> filt = mf.MatchedFilter(1 << 14, ndata=16, ntemplates=16)
    >>> filt.set_data(data_spectra)       # (16, 16384) complex64, ALREADY FFT'd
    >>> filt.set_templates(template_spectra)
    >>> peaks = filt.run(binsize=1024, threshold=t, window=(a, b))
    >>> peaks["index"], peaks["value"]

Produce the spectra with whatever you already use - numpy, MKL, FFTW.  matchedfilter
does not need to own that step, and there is no plan object to manage: the
MatchedFilter is built once and reused for every pair.

Inputs are FREQUENCY-DOMAIN: the unnormalised forward transform of each segment,
in natural order.  Ingest only rearranges - templates are conjugated and both
sides are stored in the layout the correlation loop walks - which measures at
2-4% of total and shrinks as the number of templates grows.

Peak-only lengths are powers of two from 64 to 1048576 on CPU and 64 to 65536
on GPU. Full-output lengths are 1024 to 4194304 on either device, subject to
device limits. Hierarchical calibration coverage is separate from transform support.
"""
import hashlib
import math
from types import SimpleNamespace
import operator
import os
import sys
import threading
import time
import warnings

import numpy as np
from . import _core
from . import gatechain as _gatechain

try:
    from importlib.metadata import version as _version, PackageNotFoundError
    __version__ = _version("matchedfilter")
except (ImportError, PackageNotFoundError):  # running from a source tree
    __version__ = "0.0.0.dev0"

#: dtype of the arrays returned by :meth:`MatchedFilter.run`.
#: A peak is WHERE and WHAT, nothing else. The magnitude used to be a third
#: field and was always abs(value) to the last bit, so it carried no
#: information -- it cost a field copy on assembly, a buffer, and on the GPU
#: a third output array and a sqrt per bin. Callers who want it write
#: np.abs(peaks["value"]).
PEAK_DTYPE = np.dtype([("index", "<i8"), ("value", "<c8")])

#: Transform lengths the GPU kernel covers. One workgroup carries a whole
#: transform and n = threads * points-per-thread, so the 1024-thread cap puts
#: the ceiling at 16384 while a thread holds 16 points, at 32768 while it
#: holds 32, and at 65536 while it holds 64. Above that the transform state
#: no longer fits the register file and the four-step has to be split across
#: dispatches -- a different kernel, so 65536 is where this one ends.
#:
#: Keep in step with tools/build_spirv.py TIER_B, which is what emits them.
#: The short lengths were built as coarse bands before they were offered as
#: transform lengths -- the kernel generalises down without change, so they
#: cost nothing to expose and close the bottom of the CPU's range.
_GPU_SIZES = frozenset((64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384,
                        32768, 65536))

__all__ = ["MatchedFilter", "CorrelationFilter", "HierarchicalFilter", "PEAK_DTYPE", "backend",
           "targets", "set_target", "devices", "Device", "__version__",
           "get_autotune_state", "clear_autotune_cache",
           "TimeDomainFilterBank", "FilterResults", "taps_to_spectra",
           "template_spectra", "template_valid"]

from .time_domain import TimeDomainFilterBank, FilterResults, template_spectra, template_valid


def taps_to_spectra(taps, counts, n, max_taps=None, out=None):
    """Convert time-domain FIR filter taps to frequency-domain spectra in C.

    Vectorized implementation with AVX-512 SIMD and circular center-tap roll alignment.
    Releases the Python GIL during transformation.

    Parameters:
        taps: 2D array of shape (n_templates, max_taps) float32
        counts: 1D array of tap counts (int64 or int32)
        n: FFT block size (int)
        max_taps: Optional maximum taps (defaults to taps.shape[1])
        out: Optional output array of shape (n_templates, n) complex64

    Returns:
        Complex64 array of shape (n_templates, n) with forward FFT spectra.
    """
    taps_arr = np.ascontiguousarray(taps, dtype=np.float32)
    if taps_arr.ndim != 2:
        raise ValueError("taps must be a 2D array of shape (n_templates, max_taps)")
    n_templates, default_max = taps_arr.shape
    m_taps = default_max if max_taps is None else int(max_taps)
    counts_arr = np.ascontiguousarray(counts, dtype=np.int64)
    if counts_arr.ndim != 1 or len(counts_arr) != n_templates:
        raise ValueError("counts must be a 1D array matching n_templates")
    if out is None:
        out_spec = np.empty((n_templates, int(n)), dtype=np.complex64)
    else:
        out_spec = np.ascontiguousarray(out, dtype=np.complex64)
        if out_spec.shape != (n_templates, int(n)):
            raise ValueError(f"out shape {out_spec.shape} must match ({n_templates}, {n})")

    _core.taps_to_spectra(taps_arr, counts_arr, int(n), m_taps, out_spec)
    return out_spec


def backend():
    """Name of the SIMD target selected for this CPU, e.g. ``"AVX2"``.

    Which one runs depends on the host, so a benchmark number is not
    interpretable without it.  ``MF_ISA`` forces one from the environment and
    :func:`set_target` does the same inside a running process.
    """
    return _core.backend()


def targets():
    """SIMD targets this build contains that this CPU can run, widest first.

    What a build contains is decided by the compiler, not by matchedfilter, so
    this is the only reliable list -- a machine without AVX-512 will not
    report ``AVX3`` however the wheel was built.
    """
    return _core.targets()


def set_target(name):
    """Narrow the choice to one target, or restore the default with ``None``.

    For comparing targets in one process.  Plans already created keep the
    kernel they were built with, so create the plan after setting this.
    """
    _core.set_target(name)


#: DLPack device types we can read without a copy across a bus.
#: kDLCPU is 1; kDLCUDAHost (3) and kDLROCMHost (11) are pinned host memory,
#: which is still host memory.
_DLPACK_HOST = {1, 3, 11}

_DLPACK_NAMES = {2: "CUDA", 4: "OpenCL", 7: "Vulkan", 8: "Metal", 10: "ROCm",
                 13: "CUDA managed", 14: "one-API"}


def _from_any(a):
    """Accept any array that speaks DLPack, not just numpy's.

    DLPack is the cross-library standard for handing over a buffer -- numpy 2,
    torch, cupy and jax all implement ``__dlpack__`` -- so keying off it means
    this works with arrays from libraries matchedfilter has never heard of and
    does not depend on.  Anything older falls through to numpy's own coercion,
    which covers the buffer protocol and ``__array__``.

    Data that already lives on an accelerator is REFUSED rather than copied.
    A silent device-to-host transfer here would be invisible in the API and
    would dominate the runtime of the very kernel the caller came for; a GPU
    tensor reaching the CPU backend is a mistake worth reporting, not
    absorbing.
    """
    if isinstance(a, np.ndarray):
        return a
    if hasattr(a, "__dlpack_device__"):
        try:
            kind = int(a.__dlpack_device__()[0])
        except Exception:
            kind = 1                      # unreadable: let numpy try
        if kind not in _DLPACK_HOST:
            raise TypeError(
                "array is on a %s device; matchedfilter will not copy it to "
                "the host implicitly. External accelerator allocations cannot be "
                "imported by the Vulkan/Metal backends; use empty_shared() "
                "for host-visible GPU storage, or transfer explicitly"
                % _DLPACK_NAMES.get(kind, "non-host"))
        try:
            return np.from_dlpack(a)
        except Exception:
            pass                          # e.g. read-only producer; coerce below
    return a


def devices():
    """Every device this build can dispatch to.  See :mod:`matchedfilter.device`."""
    from .device import devices as _devices
    return _devices()


def _as_c64(a, n, what):
    a = np.ascontiguousarray(_from_any(a), dtype=np.complex64)
    if a.ndim != 1 or a.size != n:
        raise ValueError(f"{what} must be a 1-D complex array of {n} samples, got shape {a.shape}")
    return a


from ._errors import UnsupportedSize      # noqa: E402


def _unpack_half(a, n, hermitian):
    """Full length-n spectra from (T, n // 2) templates, the convention the CPU plans read.

    hermitian: the spectrum of a real filter, packed with the Nyquist bin in the imaginary
    part of bin 0; the upper half is the conjugate mirror. Otherwise the template is
    band-limited to the lower half and zero above.
    """
    K = n // 2
    full = np.zeros((a.shape[0], n), dtype=np.complex64)
    full[:, :K] = a
    if hermitian:
        full[:, 0] = a[:, 0].real
        full[:, K] = a[:, 0].imag
        full[:, K + 1:] = np.conj(a[:, 1:][:, ::-1])
    return full


class _SparsePeaks:
    """The peaks of a (blocks, templates, bins) result, sparse: flat indices into that shape,
    sample indices and values, in C order. What a backend with ``supports_sparse`` returns
    when a caller asks (``_want_sparse``): at a detection threshold almost every bin is
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


class _SeriesOutput:
    """Where a series call's batches land (MatchedFilter._run_series_gpu): the aggregate
    peak tables of a call with several batches (none for a single batch, whose own result is
    returned), and the sparse pieces kept aside until the call is finished."""

    def __init__(self, plan, c):
        self.plan, self.c = plan, c
        self.shape = shape = (c.nblk, c.nt, c.nb)
        self.sparse_parts = []
        self.dense_seen = False
        self.idx = self.val = self.peaks = None
        if c.single:
            return
        if c.defer:
            # A deferred call's tables outlive this call: its own.
            if c.raw:
                self.idx = np.empty(shape, dtype=np.int64)
                self.val = np.empty(shape, dtype=np.complex64)
            else:
                self.peaks = np.empty(shape, dtype=PEAK_DTYPE)
        elif c.raw:
            sb = getattr(plan, "_sbuf", None)
            if sb is None or sb[0] != shape:
                sb = plan._sbuf = (shape, np.empty(shape, dtype=np.int64),
                                   np.empty(shape, dtype=np.complex64))
            _, self.idx, self.val = sb
        else:
            spbuf = getattr(plan, "_spbuf", None)
            if spbuf is None or spbuf[0] != shape:
                spbuf = plan._spbuf = (shape, np.empty(shape, dtype=PEAK_DTYPE))
            _, self.peaks = spbuf

    def take(self, b_start, b_end, r):
        """Store one batch's result (a grouped call: always several batches' tables); sparse
        pieces are kept aside (see finish)."""
        if isinstance(r, _SparsePeaks):
            self.sparse_parts.append((b_start, r))
            return
        gi, gv = r
        if self.c.raw:
            self.idx[b_start:b_end], self.val[b_start:b_end] = gi, gv
        else:
            _core.pack_peaks(self.peaks[b_start:b_end], gi, gv)

    def take_one(self, b_start, b_end, r, final=False):
        """Store one batch's result of a call by window group; a single batch's result is
        returned as the call's own (formatted). final: collected when the call finishes,
        where a deferred single batch gets tables of its own."""
        c = self.c
        if isinstance(r, _SparsePeaks):
            if c.single:
                return r
            self.sparse_parts.append((b_start, r))
            return None
        gi, gv = r
        self.dense_seen = True
        if c.single:
            if c.raw:
                return _format_result(gi, gv, raw=True)
            if final and c.defer:
                out = np.empty(self.shape, dtype=PEAK_DTYPE)
            else:
                spbuf = getattr(self.plan, '_spbuf', None)
                if spbuf is None or spbuf[0] != self.shape:
                    spbuf = self.plan._spbuf = (self.shape, np.empty(self.shape, dtype=PEAK_DTYPE))
                out = spbuf[1]
            return _format_result(gi, gv, raw=False, out=out)
        if c.raw:
            self.idx[b_start:b_end], self.val[b_start:b_end] = gi, gv
        else:
            _core.pack_peaks(self.peaks[b_start:b_end], gi, gv)
        return None

    def finish(self):
        """The call's result from every batch taken."""
        c = self.c
        if not c.raw:
            return _format_result(None, None, raw=False, order=c.layout.order, out=self.peaks)
        if self.sparse_parts:
            sp = _SparsePeaks.combine(self.sparse_parts, self.shape, c.layout.order)
            if not self.dense_seen:
                return sp
            # Mixed (a tiled fallback came back dense): densify the sparse pieces.
            for b0, part in self.sparse_parts:
                pi, pv = part.dense()
                self.idx[b0:b0 + part.shape[0]], self.val[b0:b0 + part.shape[0]] = pi, pv
        return _format_result(self.idx, self.val, raw=True, order=c.layout.order)


def _format_result(idx, val, *, raw=False, counts=None, out=None, order=None):
    """Assemble the public dtype once, or return separate raw arrays."""
    if counts is True:
        counts = ((idx >= 0) if idx is not None else (out["index"] >= 0)).sum(axis=2, dtype=np.int32)
    if raw:
        if order is None:
            result = (idx.astype(np.int64, copy=False), val)
        else:
            ri = np.empty(idx.shape, np.int64)
            rv = np.empty(val.shape, np.complex64)
            ri[order], rv[order] = idx, val
            result = ri, rv
    else:
        if idx is not None:
            if order is None:
                result = np.empty(idx.shape, PEAK_DTYPE) if out is None else out
                _core.pack_peaks(result, idx, val)
            else:
                result = np.empty(idx.shape, PEAK_DTYPE) if out is None else out
                tmp = np.empty(idx.shape, PEAK_DTYPE)
                _core.pack_peaks(tmp, idx, val)
                result[order] = tmp
        else:
            if order is None:
                result = out
            else:
                result = np.empty(out.shape, PEAK_DTYPE)
                result[order] = out
    return (result, counts) if counts is not None and counts is not False else result


def _valid_series_window(n, valid):
    if valid is None:
        return None
    try:
        lo, hi = map(operator.index, valid)
    except (TypeError, ValueError) as exc:
        raise ValueError('valid must be a (start, end) integer lag interval') from exc
    if lo < 0 or lo >= hi or hi > n:
        raise ValueError('valid must satisfy 0 <= start < end <= n')
    return lo, hi


def _automatic_series_layout(length, valid):
    if valid is None:
        raise ValueError('automatic run_series requires valid=(start, end) on the filter')
    lo, hi = valid
    if length <= lo:
        raise ValueError('series ends before the first valid output sample')
    starts = np.arange(0, length - lo, hi - lo, dtype=np.uintp)
    return starts, np.full(starts.size, lo, np.uintp), np.minimum(
        hi, length - starts)


def _absolute_peak_indices(result, starts, raw):
    """Automatic series calls report positions in the supplied series."""
    index = result[0] if raw else result['index']
    st = starts.view(np.int64) if starts.dtype != np.int64 else starts
    np.add(index, st[:, None, None], out=index,
           where=index >= 0)
    return result


_SCRATCH = threading.local()


def _scratch_counts(size):
    """An int32 work buffer of size entries for one sparse series call, shared by every plan
    on this thread: the per-(block, template) counts are read only inside the call, so a
    plan holding its own (4 bytes a pair, ~11 KB a template) would keep it for nothing."""
    buf = getattr(_SCRATCH, "counts", None)
    if buf is None or buf.size < size:
        buf = _SCRATCH.counts = np.empty(max(int(size), 1), dtype=np.int32)
    return buf[:size]



def _host_copy(a, dtype):
    """np.ascontiguousarray(a, dtype), first waiting for GPU writes left in flight when it
    copies (time_domain._host_copy): the host is about to read a series a device may still
    be writing."""
    from .time_domain import _host_copy as copy
    return copy(a, dtype)

class MatchedFilter:
    """Correlate a set of data segments against a set of templates.

    Inputs are the segments' spectra.  Every pair (d, t) gives
    ``IFFT(data_d * conj(template_t))``, of which only the loudest sample per bin
    is reported.  The transform is unnormalised, matching FFTW and MKL, so a perfect
    match returns ``n * energy``.

    ``ndata`` and ``ntemplates`` are arbitrary; they need not match or be powers
    of two.  Setting a segment transforms it once and stores it in the layout the
    correlation loop wants, so that cost is paid once rather than per pair.
    """

    #: Class-level so subclasses with their own __init__ -- HierarchicalFilter
    #: -- inherit the CPU default instead of raising on first use.
    _gpu = None
    _gpu_sizes = _GPU_SIZES
    _cpu_max_n = 1 << 20


    def __init__(self, n, ndata=1, ntemplates=1, device=None, *, valid=None):
        from .device import parse as _parse_device
        self.device = _parse_device(device)
        self.n = int(n)
        self.valid = _valid_series_window(self.n, valid)
        self.ndata = int(ndata)
        self.ntemplates = int(ntemplates)
        if self.ndata < 1 or self.ntemplates < 1:
            raise ValueError("ndata and ntemplates must be >= 1")
        if self.device.kind == 'cpu' and self.n > self._cpu_max_n:
            raise ValueError("CPU transform size %d exceeds this filter's limit of %d"
                             % (self.n, self._cpu_max_n))
        self._init_state()
        if self.device.kind == "gpu":
            self._start_gpu()
            return
        self._mf = _core.MF(self.n, self.ndata, self.ntemplates)

    def _init_state(self):
        self._buf = None
        self._sbuf = None
        #: Has any spectrum reached the plan? The hierarchical refine path
        #: dereferences the stored pointer, so run() with no set_data() was a
        #: SEGFAULT -- and only once a pair actually fired, which made it look
        #: intermittent rather than like a missing call.
        self._dataset = False
        self._data_ready = set()
        self._template_ready = set()
        # Arrays the plan holds pointers into. The C side keeps the caller's
        # spectrum rather than copying it, so the wrapper must keep it alive.
        self._held = {}
        self._held_templates = None
        self._template_source = None
        self.performance_stats = {
            "total_calls": 0,
            "timed_calls": 0,
            "total_time_s": 0.0,
            "min_batch_time_ms": None,
            "max_batch_time_ms": None,
            "batch_times_ms": [],
        }
        self._in_series_call = False
        self._gpu = None
        self._gpairs = 0
        self._gtrig = 0
        self._gt1 = 0          # GPU: pairs tier 0 passed (cascade chains), for _roofline
        self._ddirty = True
        self._tdirty = True

    _MAX_BATCH_TIMINGS = 256

    def _record_batch_time(self, dt):
        stats = self.performance_stats
        ms = dt * 1000.0
        stats["total_calls"] = stats.get("total_calls", 0) + 1
        timed = stats["timed_calls"] = stats.get("timed_calls", 0) + 1
        stats["total_time_s"] = stats.get("total_time_s", 0.0) + dt
        prev_min = stats.get("min_batch_time_ms")
        stats["min_batch_time_ms"] = ms if prev_min is None or ms < prev_min else prev_min
        prev_max = stats.get("max_batch_time_ms")
        stats["max_batch_time_ms"] = ms if prev_max is None or ms > prev_max else prev_max
        times = stats.setdefault("batch_times_ms", [])
        if len(times) < self._MAX_BATCH_TIMINGS:
            times.append(ms)
        else:
            times[(timed - 1) % self._MAX_BATCH_TIMINGS] = ms

    # ---- GPU -----------------------------------------------------------
    #
    # The GPU holds the spectra itself rather than handing them to the C
    # plan, so the two paths diverge at ingest and meet again at run().
    # Everything user-visible -- shapes, dtype, bin layout, the index -1
    # convention -- is identical, which is what lets one test body assert
    # against both.
    def _start_gpu(self):
        # One flat-filter contract, two backends behind it. Both expose
        # peaks() with the same signature and the same conventions, so
        # nothing above this line knows which it got.
        #
        # Only the Context differs. Everything after it is shared, and it is
        # written once for that reason: when this was a branch per backend
        # with its own copy of the tail, the hierarchical version's early
        # return skipped the _gcal it was supposed to set, and every Metal
        # call died in _gpu_calibration on a missing attribute.
        if self.n not in self._gpu_sizes:
            raise ValueError(
                "device='gpu' supports n in %s for this filter; got %d."
                % (sorted(self._gpu_sizes), self.n))
        self._gpu = self._backend().Context(self.device.index)
        self._gdata = None  # series execution uses its own workspace
        self._gtmpl = None

    def _backend(self):
        """The compute module for this device: Metal on Apple, CUDA on NVIDIA, else Vulkan."""
        if getattr(self.device, "backend", None) == "metal":
            from . import _mtlcompute
            return _mtlcompute
        if getattr(self.device, "backend", None) == "cuda":
            from . import _cudacompute
            return _cudacompute
        from . import _vkcompute
        return _vkcompute

    # ---- ingest -------------------------------------------------------------
    def _ensure(self):
        """The live plan. Always built here; HierarchicalFilter defers."""
        return self._mf

    def _input_index(self, index, size):
        if index is None:
            return None
        index = int(index)
        if index < 0 or index >= size:
            raise IndexError("index %d out of range" % index)
        return index

    def _mark_ready(self, kind, index):
        attr = "_" + kind + "_ready"
        ready = getattr(self, attr)
        if index is None:
            setattr(self, attr, None)  # complete bank: constant-time hot-path check
        elif ready is not None:
            ready.add(index)
            size = self.ndata if kind == "data" else self.ntemplates
            if len(ready) == size:
                setattr(self, attr, None)

    def _missing(self, kind, start, count):
        ready = getattr(self, "_" + kind + "_ready")
        return ready is not None and any(i not in ready for i in range(start, start + count))

    def _require_templates(self, start, count):
        if self._missing("template", start, count):
            raise ValueError("no templates for requested rows: call set_templates() first")

    def _pair_range(self, data, templates):
        d0, nd = (0, self.ndata) if data is None else (int(data[0]), int(data[1]))
        t0, nt = (0, self.ntemplates) if templates is None else (int(templates[0]), int(templates[1]))
        if nd < 1 or nt < 1 or d0 < 0 or t0 < 0 \
           or d0 + nd > self.ndata or t0 + nt > self.ntemplates:
            raise ValueError("data/templates sub-range out of bounds")
        if not self._dataset or self._missing("data", d0, nd):
            raise ValueError("no data: call set_data() before run()")
        self._require_templates(t0, nt)
        return d0, nd, t0, nt

    def _gpu_set(self, store, spectra, index, what):
        if what == "data":
            self._ddirty = True
        else:
            self._tdirty = True
        if index is None:
            a = np.ascontiguousarray(_from_any(spectra), dtype=np.complex64)
            shape = (self.ndata if what == "data" else self.ntemplates, self.n)
            if a.shape != shape:
                if what == "template" and a.ndim == 2 and a.shape == (self.ntemplates, self.n // 2):
                    self._gpu_packed = a
                    a = _unpack_half(a, self.n, getattr(self, "_hermitian", False))
                else:
                    raise ValueError("expected shape %s, got %s" % (shape, a.shape))
            from ._shared import shared_buffer
            attr = "_gdata" if what == "data" else "_gtmpl"
            if shared_buffer(a, self._gpu) is not None:
                setattr(self, attr, a)
            elif what == "template" and getattr(self._gpu, "_device_state", None) is not None:
                # One device copy of the bank that every recording binds in place. Copied per
                # storage (per slot, window group and chain), the spectra overran the cache
                # budget at n=4096, and each eviction drained the in-flight batch.
                self._settle_deferred()
                buf = store if (store is not None and store.shape == a.shape
                                and shared_buffer(store, self._gpu) is not None) else None
                if buf is None:
                    # Host-cached: the host reads it too (coarse templates are cut from it),
                    # and reads from write-combined memory cost 70 ms per plan.
                    buf = self._gpu.empty_shared(a.shape, readback=True)
                buf[:] = a
                setattr(self, attr, buf)
            elif store is None or shared_buffer(store, self._gpu) is not None or not store.flags.writeable:
                setattr(self, attr, a.copy())
            else:
                store[:] = a
        else:
            if store is None:
                shape = (self.ndata if what == "data" else self.ntemplates, self.n)
                store = np.zeros(shape, dtype=np.complex64)
                setattr(self, "_gdata" if what == "data" else "_gtmpl", store)
            if not store.flags.writeable:
                store = store.copy()
                setattr(self, "_gdata" if what == "data" else "_gtmpl", store)
            store[int(index)] = _as_c64(spectra, self.n, "spectrum")

    def set_data(self, spectra, index=None):
        """Set one data spectrum (with ``index``) or all from a (ndata, n) array.

        Inputs are frequency domain - the unnormalised forward transform of the
        segment, natural order.
        """
        index = self._input_index(index, self.ndata)
        if self._gpu is not None:
            self._gpu_set(self._gdata, spectra, index, "data")
            self._dataset = True
            self._mark_ready("data", index)
            return
        if index is not None:
            a = _as_c64(spectra, self.n, "spectrum")
            # The plan keeps this pointer -- the coarse band is read straight
            # out of it during run(), and the full spectrum is ingested lazily
            # only if a pair fires. A caller passing a temporary would have it
            # freed before either happens, which is a use-after-free that only
            # shows when the refine path runs. Hold a reference.
            self._held[int(index)] = a
            self._ensure().set_data(int(index), a)
            self._dataset = True
            self._mark_ready("data", index)
            return
        a = np.ascontiguousarray(_from_any(spectra), dtype=np.complex64)
        if a.ndim != 2 or a.shape != (self.ndata, self.n):
            raise ValueError(f"expected shape ({self.ndata}, {self.n}), got {a.shape}")
        self._held[-1] = a                      # see the note above
        plan = self._ensure()
        if hasattr(plan, 'set_data_batch'):
            plan.set_data_batch(0, a)
        else:
            set_data_fn = plan.set_data
            for i in range(self.ndata):
                set_data_fn(i, a[i])
        self._held = {-1: a}
        self._dataset = True
        self._mark_ready("data", None)

    def set_template_source(self, source):
        """Give a callable that returns the (ntemplates, n) spectra set_templates is called
        with: the plan then keeps no copy of its own, and a rebuilt plan (a new chain, a
        trial) reloads from the source."""
        self._template_source = source

    def _hold(self, a):
        """What a rebuilt plan reloads its templates from: a copy, or nothing when a template
        source can make them again."""
        return None if getattr(self, "_template_source", None) is not None else a.copy()

    def set_templates(self, spectra, index=None):
        """Set one template spectrum (with ``index``) or all from a (ntemplates, n) array.

        Conjugation happens here, once, rather than in the pair loop.
        """
        index = self._input_index(index, self.ntemplates)
        if self._gpu is not None:
            self._gpu_set(self._gtmpl, spectra, index, "template")
            self._mark_ready("template", index)
            return
        if index is not None:
            c = _as_c64(spectra, self.n, "spectrum")
            if not hasattr(self, '_held_templates') or self._held_templates is None:
                self._held_templates = [None] * self.ntemplates
            elif isinstance(self._held_templates, np.ndarray):
                self._held_templates = self._held_templates.copy()
            self._held_templates[int(index)] = c
            self._ensure().set_template(int(index), c)
            self._mark_ready("template", index)
            return
        a = np.ascontiguousarray(_from_any(spectra), dtype=np.complex64)
        if a.ndim != 2:
            raise ValueError(f"expected 2D array of spectra, got {a.shape}")
        if a.shape[0] != self.ntemplates:
            raise ValueError(f"expected {self.ntemplates} templates, got {a.shape[0]}")
        if a.shape[1] == self.n:
            self._bandlimited = False
            self.k = self.n
        elif a.shape[1] == self.n // 2:
            self._bandlimited = True
            self.k = self.n // 2
            if self._gpu is None and type(self).__name__ != 'HierarchicalFilter' and (not hasattr(self, '_mf') or self._mf is None or getattr(self._mf, 'n', None) != self.k):
                self._mf = _core.MF(self.k, 2, self.ntemplates)
        else:
            raise ValueError(f"expected shape ({self.ntemplates}, {self.n}) or ({self.ntemplates}, {self.n // 2}), got {a.shape}")
        self._held_templates = self._hold(a)
        plan = self._ensure()
        if hasattr(plan, 'set_template_batch'):
            plan.set_template_batch(0, a)
        else:
            set_tmpl_fn = plan.set_template
            for i in range(self.ntemplates):
                set_tmpl_fn(i, a[i])
        self._mark_ready("template", None)


    def _gpu_pair_limit(self):
        limit = getattr(self._gpu, 'max_dispatch_x', 2**32 - 1)
        # Large transforms can exceed a driver's submission timeout when a
        # whole bank runs at once. Bound worst-case work, including a fully
        # admitted hierarchical batch, independently of storage capacity.
        if self.n >= 32768:
            limit = min(limit, (1 << 28) // self.n)
        return limit

    def _series_policy(self, operation, band, templates):
        from ._execution_policy import select
        return select(self.device, operation, self.n, band, templates)

    def _gpu_window(self, D, H, binsize, threshold, start, end, slot=None, async_submit=False,
                    **kw):
        nd, nt = D.shape[0], H.shape[0]
        limit = self._gpu_pair_limit()
        if nd * nt <= limit:
            # No signature probing: a TypeError raised after a submit would
            # have dispatched the same work twice.
            return self._gpu_dispatch(D, H, binsize, threshold, start, end,
                                      slot=slot, async_submit=async_submit, **kw)
        nb = 1 + (end - start - 1) // binsize
        idx = np.empty((nd, nt, nb), np.int32)
        val = np.empty((nd, nt, nb), np.complex64)
        for t0 in range(0, nt, limit):
            t1 = min(t0 + limit, nt)
            rows = max(1, limit // (t1 - t0))
            for d0 in range(0, nd, rows):
                d1 = min(d0 + rows, nd)
                gi, gv = self._gpu_dispatch(D[d0:d1], H[t0:t1], binsize,
                                           threshold, start, end)
                idx[d0:d1, t0:t1], val[d0:d1, t0:t1] = gi, gv
        if async_submit:
            return lambda: (idx, val)
        return idx, val

    def _gpu_dispatch(self, D, H, binsize, threshold, start, end, slot=None, async_submit=False,
                      **kw):
        res = self._gpu.peaks(
            self.n, D, H, binsize=binsize, threshold=threshold,
            window=(start, end), upload_data=self._ddirty,
            upload_tmpl=self._tdirty, slot=slot, async_submit=async_submit, **kw)
        self._ddirty = self._tdirty = False
        return res

    # ---- run ----------------------------------------------------------------
    def _execution_plan(self):
        return self._ensure()

    def _continuous_plan(self):
        """The CPU plan for continuous correlation, on the transform the cost model chose
        for this n (_CORR_PFFT: the platform FFT where it measured cheaper)."""
        ep = self._execution_plan()
        want = bool(_CORR_PFFT.get(self.n, False))
        if self.__dict__.get("_pfft_on") != want:
            ok = ep.set_platform_fft(want) if hasattr(ep, "set_platform_fft") else False
            if want and not ok:
                ep.set_platform_fft(False)
            self._pfft_on = want
        return ep

    def nbins(self, binsize, window=None):
        binsize = int(binsize)
        if binsize < 1:
            raise ValueError("binsize must be >= 1")
        start, end = self._window(window)
        if self._gpu is not None:
            return 0 if start >= end else -(-(end - start) // int(binsize))
        return self._ensure().nbins(int(binsize), start, end)

    def _window(self, window):
        if window is None:
            return 0, self.n
        start, end = int(window[0]), int(window[1])
        start = max(0, min(start, self.n))
        end = max(0, min(end, self.n))
        if start >= end:
            raise ValueError(f"empty window ({start}, {end})")
        return start, end

    def run(self, binsize=None, threshold=0.0, window=None,
            data=None, templates=None, counts=False, raw=False):
        """Correlate and report the loudest sample per bin.

        Returns a structured array of shape ``(ndata, ntemplates, nbins)`` with
        fields ``index`` (lag, int64) and ``value`` (complex64).  A bin whose
        maximum does not exceed ``threshold`` comes back with ``index == -1``
        and ``value == 0``, so bin j always sits at slot j and the result can
        be indexed by frequency without searching.

        For the magnitude, take ``np.abs(peaks["value"])``.  It was a third
        field once; it equalled that expression exactly, so it only cost a
        copy.

        ``data`` and ``templates`` restrict the run to a sub-range, given as
        ``(start, count)``; the answer is identical to the matching slice of a
        full run.  ``window=(start, end)`` restricts the lags searched.

        With ``counts=True`` returns ``(peaks, counts)``, where counts has shape
        ``(ndata, ntemplates)`` and holds how many bins crossed the threshold.

        ``raw=True`` returns ``(index, value)`` as two plain arrays
        of shape ``(ndata, ntemplates, nbins)`` instead of assembling a
        structured array.  A caller driving small batches in a tight loop pays
        for that assembly on every call -- a field copy here and a
        structured-array slice at the other end -- which can exceed the filter
        work itself.

        Results may reuse buffers; do not rely on retention across calls.  The next ``run`` on this
        filter overwrites it in place; ``.copy()`` anything that must outlive
        that call.  Six allocations are nothing beside a 2^20 transform, but a
        caller driving small batches pays them every time -- at 37 templates
        they were 15 of the 21 us a call took -- so the buffer is kept.  The
        trap is real enough that it caught the first draft of the worked
        example in ``matchedfilter.tutorial``, which compared a full run
        against a windowed one and printed the windowed answer twice.
        """
        t0 = time.perf_counter()
        try:
            return self._run_inner(binsize=binsize, threshold=threshold, window=window,
                                   data=data, templates=templates, counts=counts, raw=raw)
        finally:
            self._record_batch_time(time.perf_counter() - t0)

    def _run_inner(self, binsize=None, threshold=0.0, window=None,
                   data=None, templates=None, counts=False, raw=False):
        n = self.n
        binsize = n if binsize is None else int(binsize)
        if binsize < 1:
            raise ValueError("binsize must be >= 1")
        start, end = self._window(window)
        d0, nd, t0, nt = self._pair_range(data, templates)
        if self._gpu is not None:
            idx, val = self._gpu_window(
                self._gdata[d0:d0 + nd], self._gtmpl[t0:t0 + nt],
                binsize, threshold, start, end)
            if raw:
                return _format_result(idx, val, raw=True, counts=bool(counts))
            nb = idx.shape[-1]
            shape = (nd, nt, nb)
            pbuf = getattr(self, '_pbuf', None)
            if pbuf is None or pbuf[0] != shape:
                peaks = np.empty(shape, dtype=PEAK_DTYPE)
                pbuf = self._pbuf = (shape, peaks)
            _, peaks = pbuf
            return _format_result(idx, val, raw=False, counts=bool(counts), out=peaks)
        nb = self._ensure().nbins(binsize, start, end)
        rows = nd * nt
        shape = (nd, nt, nb)
        need = rows * nb
        if raw:
            buf = self._buf
            if buf is None or buf[0] != (rows, nb):
                idx = np.empty(need, dtype=np.int64)
                val = np.empty(need, dtype=np.complex64)
                mag = np.empty(0, dtype=np.float32)
                cnt = np.empty(rows, dtype=np.int32)
                buf = self._buf = ((rows, nb), idx, val, mag, cnt)
            _, idx, val, mag, cnt = buf
            self._execution_plan().run(d0, nd, t0, nt, binsize, float(threshold), start, end,
                                       idx, val, mag, cnt)
            return _format_result(idx.reshape(shape), val.reshape(shape),
                                  raw=True, counts=cnt.reshape(nd, nt) if counts else None)
        pbuf = getattr(self, '_pbuf', None)
        if pbuf is None or pbuf[0] != shape:
            peaks = np.empty(shape, dtype=PEAK_DTYPE)
            cnt = np.empty(rows, dtype=np.int32)
            mag = np.empty(0, dtype=np.float32)
            empty_idx = np.empty(0, dtype=np.int64)
            empty_val = np.empty(0, dtype=np.complex64)
            pbuf = self._pbuf = (shape, peaks, cnt, mag, empty_idx, empty_val)
        _, peaks, cnt, mag, empty_idx, empty_val = pbuf
        self._execution_plan().run(d0, nd, t0, nt, binsize, float(threshold), start, end,
                                   empty_idx, empty_val, mag, cnt, peaks)
        return _format_result(None, None, raw=False, counts=cnt.reshape(nd, nt) if counts else None,
                              out=peaks)


    def _series_array(self, series):
        """The series as the engine reads it: complex64, or -- for a hierarchical plan that
        reads real series (_reads_real_series) given one (the middle output of a
        real-real-complex hierarchy, filtered with complex quadrature templates) -- float32:
        a CPU plan transforms it at half size into the same full spectrum
        (ap_hmf_set_real_series), a GPU plan's forward reads the real samples."""
        a = _from_any(series)
        if (not np.iscomplexobj(a) and isinstance(self, HierarchicalFilter)
                and self._reads_real_series()):
            if (isinstance(a, np.ndarray) and a.dtype == np.float32 and a.ndim == 1
                    and a.strides in ((8,), (4,)) and a.size > 0):
                return a            # read in place: contiguous, or one lane of a complex row
            return _host_copy(a, np.float32)
        return _host_copy(a, np.complex64)

    def _series_layout(self, series, starts, win_start, win_end, binsize, templates,
                       ragged=False):
        """Validate the shared series contract before either native backend."""
        ser = self._series_array(series)
        st = np.ascontiguousarray(_from_any(starts), dtype=np.uintp)
        ws = np.ascontiguousarray(_from_any(win_start), dtype=np.uintp)
        we = np.ascontiguousarray(_from_any(win_end), dtype=np.uintp)
        if any(a.ndim != 1 for a in (ser, st, ws, we)):
            raise ValueError("series, starts, win_start and win_end must be one-dimensional")
        if not (st.size == ws.size == we.size):
            raise ValueError("starts, win_start and win_end must be the same length")
        if st.size < 1:
            raise ValueError("run_series needs at least one block")
        # Negative signed offsets wrap on conversion to uintp. Also reserve
        # room for the block's sample offsets in the GPU's signed gather.
        if np.any(st > np.iinfo(np.intp).max - self.n):
            raise ValueError("starts must be nonnegative and fit in the sample index range")
        binsize = self.n if binsize is None else int(binsize)
        if binsize < 1:
            raise ValueError("binsize must be >= 1")
        t0, nt = (0, self.ntemplates) if templates is None else (
            int(templates[0]), int(templates[1]))
        if nt < 1 or t0 < 0 or t0 + nt > self.ntemplates:
            raise ValueError("templates sub-range out of bounds")
        self._require_templates(t0, nt)
        from ._series import SeriesLayout
        layout = SeriesLayout(self.n, st, ws, we, binsize, ragged=ragged)
        return ser, layout, binsize, t0, nt

    def _grouped_layout(self, series, starts, win_start, win_end, binsize, templates,
                        ragged=False):
        """_series_layout, grouped, cached per layout signature.

        A search calls the same plan with the same blocks every segment: validating and
        grouping them again was a large part of the per-call host time. The key is the
        layout's bytes (not array identity), so a caller reusing and rewriting its arrays
        still gets a fresh layout. A cached layout is never mutated after grouping."""
        group = self._gpu is not None or self.ndata > 1 or isinstance(self, HierarchicalFilter)
        key = None
        if (type(starts) is np.ndarray and type(win_start) is np.ndarray
                and type(win_end) is np.ndarray):
            key = (starts.dtype.char, starts.tobytes(), win_start.dtype.char, win_start.tobytes(),
                   win_end.dtype.char, win_end.tobytes(), binsize,
                   None if templates is None else (int(templates[0]), int(templates[1])),
                   group, self._gpu is not None, ragged)
            cache = self.__dict__.get("_layout_cache")
            hit = cache.get(key) if cache is not None else None
            if hit is not None:
                ser = self._series_array(series)
                if ser.ndim != 1:
                    raise ValueError("series, starts, win_start and win_end must be one-dimensional")
                layout, binsize, t0, nt = hit
                self._require_templates(t0, nt)
                return ser, layout, binsize, t0, nt
        ser, layout, binsize, t0, nt = self._series_layout(
            series, starts, win_start, win_end, binsize, templates, ragged=ragged)
        if group:
            layout.group(materialize=self._gpu is not None)
        if ragged:
            layout.ragged = True
        if key is not None:
            cache = self.__dict__.setdefault("_layout_cache", {})
            if len(cache) >= 32:
                cache.clear()
            cache[key] = (layout, binsize, t0, nt)
        return ser, layout, binsize, t0, nt

    def _settle_deferred(self):
        """Collect every deferred call still in flight on this plan (filter_series_many)."""
        owners = self.__dict__.get("_slot_owner")
        if owners:
            pending = list(owners.values())
            owners.clear()
            for d in pending:
                d.result()

    def _items_gpu(self, jobs, binsize, threshold, wait=True):
        """Many single-template series calls as one submission: a forward per series
        allocation (e.g. each detector's rows of a reused device buffer, read in place) and
        one peak dispatch per window.

        jobs: [(series, starts, win_start, win_end, template)] -- each a run_series call on one
        template of this plan. Returns per job (idx, val) shaped (nblocks, 1, max bins) with -1
        in bins past a block's own count, or None when this plan or these inputs cannot take
        the path (the caller then makes the calls).

        Several allocations share one spectra workspace on a backend whose forward takes a
        row range (``forward_rows``); elsewhere each allocation is its own submission.
        wait=False on a backend declaring ``items_async``: returns a callable giving that
        list once the submission completes, so a caller submits every template group's
        items before waiting on any (an idle GPU takes ~1 ms to start each small submission
        on an M2 or an APU)."""
        from ._shared import containing
        gpu = self._gpu
        if (gpu is None or not hasattr(gpu, "peaks_items") or type(self) is not MatchedFilter
                or self._gtmpl is None or not jobs):
            return None
        n = self.n
        allocs, rows = {}, []                 # id(whole) -> [whole, row0 in the workspace, rows]
        for ser, st, ws, we, t in jobs:
            c = containing(np.ascontiguousarray(ser), gpu)
            if c is None:
                return None
            if st.size and int(st.max()) + n > ser.size:
                return None                     # needs the upload's zero padding past the end
            allocs.setdefault(id(c[0]), [c[0], 0, 0])[2] += int(st.size)
            rows.append((id(c[0]), c[1]))
        by_rows = n <= 65536                   # one-stage forwards take row ranges
        if len(allocs) > 1 and not by_rows:
            return self._items_by_allocation(jobs, rows, binsize, threshold, wait)
        total = 0
        for a in allocs.values():               # each allocation's rows start 64-aligned
            a[1] = total
            total += -(-a[2] // 64) * 64 if by_rows else a[2]
        if sum(a[2] for a in allocs.values()) == 0:
            res = [(np.empty((0, 1, 1), np.int64), np.empty((0, 1, 1), np.complex64))
                   for _ in jobs]
            return res if wait else (lambda: res)
        prior = self.__dict__.pop("_items_pending", None)
        if prior is not None:
            prior()                              # its workspace is about to be rewritten
        # Workspaces come from a per-device pool (follow-ups run on a different single-template
        # plan per bank, and per-plan workspaces were a new allocation -- and new forward
        # recordings -- whenever a bank first had follow-ups). One is checked out for this
        # submission and returned once its results are read; sizes are powers of two rows,
        # so a recurring call takes the same workspace and its recordings repeat.
        cap = self._items_checkout(gpu, n, total)
        spec, starts = cap
        items, place, fill = [], [], {k: a[1] for k, a in allocs.items()}
        for (ser, st, ws, we, t), (k_alloc, row) in zip(jobs, rows):
            k = int(st.size)
            pos = fill[k_alloc]
            fill[k_alloc] += k
            place.append(pos)
            starts[pos:pos + k] = np.minimum(st, ser.size).astype(np.int64) + row
            lo_hi = np.stack([np.minimum(ws, n), np.minimum(we, n)], 1).astype(np.int64)
            j = 0
            while j < k:                        # runs of blocks with one window
                e = j + 1
                while e < k and lo_hi[e, 0] == lo_hi[j, 0] and lo_hi[e, 1] == lo_hi[j, 1]:
                    e += 1
                items.append((int(lo_hi[j, 0]), int(lo_hi[j, 1]), pos + j, pos + e, int(t)))
                j = e
        self._settle_deferred()
        if by_rows:
            for i, (whole, r0, count) in enumerate(allocs.values()):
                if count:
                    # Whole 64-row chunks (padding rows read the allocation's start), so the
                    # forward recordings repeat across calls.
                    padded = -(-count // 64) * 64
                    starts[r0 + count:r0 + padded] = 0
                    gpu.forward(n, whole, starts, spec, defer=True, slot=('items', i),
                                rows=(r0, padded))
            data = spec
        else:
            whole = next(iter(allocs.values()))[0]
            gpu.forward(n, whole, starts[:total], spec[:total], defer=True)
            data = spec[:total]
        async_ok = not wait
        res = gpu.peaks_items(n, data, self._gtmpl, items, binsize, threshold,
                              **({"async_submit": True} if async_ok else {}))

        def assemble(res):
            out, it = [], 0
            for (ser, st, ws, we, t), pos in zip(jobs, place):
                k = int(st.size)
                mine = []
                while it < len(items) and items[it][3] <= pos + k and items[it][2] >= pos:
                    mine.append((items[it], res[it]))
                    it += 1
                nbmax = max([r[0].shape[2] for _, r in mine] or [1])
                idx = np.full((k, 1, nbmax), -1, np.int64)
                val = np.zeros((k, 1, nbmax), np.complex64)
                for (lo, hi, a, b, _), (gi, gv) in mine:
                    idx[a - pos:b - pos, :, :gi.shape[2]] = gi
                    val[a - pos:b - pos, :, :gv.shape[2]] = gv
                out.append((idx, val))
            return out
        if not async_ok:
            out = assemble(res)
            self._items_return(gpu, n, cap)
            return out if wait else (lambda: out)
        done = []

        def collect():
            if not done:
                self.__dict__.pop("_items_pending", None)
                try:
                    done.append(assemble(res()))
                finally:
                    self._items_return(gpu, n, cap)
            return done[0]
        self._items_pending = collect
        return collect

    @staticmethod
    def _items_pool(gpu, n):
        holder = getattr(gpu, "_device_state", None) or gpu
        return holder.__dict__.setdefault("items_pool", {}).setdefault(n, [])

    def _items_checkout(self, gpu, n, rows):
        """A free (spectra, starts) workspace of at least rows rows, taken out of the pool."""
        pool = self._items_pool(gpu, n)
        # This plan's last workspace first: its forward recordings are on it.
        last = self.__dict__.get("_items_last")
        for i, ws in enumerate(pool):
            if ws is last and ws[0].shape[0] >= rows:
                return pool.pop(i)
        fits = [i for i, ws in enumerate(pool) if ws[0].shape[0] >= rows]
        if fits:
            ws = pool.pop(min(fits, key=lambda i: pool[i][0].shape[0]))
        else:
            size = 64
            while size < rows:
                size *= 2
            ws = gpu.empty_shared((size, n)), gpu.empty_shared(size, np.uint32)
        self._items_last = ws
        return ws

    def _items_return(self, gpu, n, ws):
        pool = self._items_pool(gpu, n)
        if all(w is not ws for w in pool):
            pool.append(ws)

    def _items_by_allocation(self, jobs, rows, binsize, threshold, wait):
        """_items_gpu for jobs spanning allocations on a backend without forward row ranges:
        one submission per allocation, in turn."""
        by = {}
        for j, (k_alloc, _) in enumerate(rows):
            by.setdefault(k_alloc, []).append(j)
        out = [None] * len(jobs)
        for js in by.values():
            res = self._items_gpu([jobs[j] for j in js], binsize, threshold)
            if res is None:
                return None
            for j, r in zip(js, res):
                out[j] = r
        return out if wait else (lambda: out)

    def _run_series_ragged(self, series, starts, win_start, win_end, binsize=None,
                           threshold=0.0, templates=None):
        """run_series(raw=True) over blocks whose windows give DIFFERENT bin counts.

        The result is (nblocks, nt, max bins); a block's bins past its own count are
        dismissed (-1, 0), as each block's own call would report them. Every window
        group is one dispatch of a single submission, where calling run_series once per
        distinct bin count costs a submission and a wait each -- most of a
        single-template follow-up's time on a GPU.

        A hierarchical plan takes this path on a backend with ``supports_ragged_hier``:
        its grouped call runs per-row windows (each block's own [lo, hi)) under one
        recording of the largest bin count, so a block's bins past its own count are
        empty exactly as for a flat plan.

        Returns None when this plan cannot (CPU, a backend without ragged support, or a
        shape the grouped path does not take); the caller then makes one call per bin count.
        """
        if self._gpu is None:
            return None
        # (A GPU plan under a chain trial is judged per batch, not per call: it takes the
        # same paths as any other -- ragged, deferred, replayed.)
        if not isinstance(self, HierarchicalFilter) and type(self) is not MatchedFilter:
            return None
        # Cached per layout bytes (as run_series), so a repeated call keeps its layout and
        # with it its call plan.
        ser, layout, binsize, t0, nt = self._grouped_layout(
            series, starts, win_start, win_end, binsize, templates, ragged=True)
        if (len(layout.groups) < 2 or layout.nbins > getattr(self._gpu, "max_grouped_bins", 0)
                or nt > self._gpu_pair_limit()):
            return None
        self._dataset = False
        self._data_ready = set()
        return self._run_series_gpu(ser, layout, binsize, threshold, t0, nt, True)

    def run_series(self, series, starts=None, win_start=None, win_end=None,
                   binsize=None, threshold=0.0, templates=None, raw=False,
                   decimated=None):
        """Filter a series using this filter's ``valid`` overlap-save window.

        ``run_series(series)`` derives contiguous blocks and returns peak
        indices in series coordinates. ``run_blocks`` accepts explicit block
        starts and windows, returning block-local lag indices. Passing those
        arguments here remains supported for existing callers.

        Returns a structured array of shape
        ``(nblocks, ntemplates, nbins)``, or with ``raw=True`` the two plain
        arrays ``(index, value)`` of that shape.

        Equal-window blocks are grouped internally; output retains caller order.
        Flat CPU batches use up to ``ndata`` slots. Hierarchical CPU batches
        use a bounded internal group (normally eight). GPU batches follow the
        series memory budget independently of ``ndata``.

        Raw CPU results reuse buffers; copy retained results.
        A later run() requires set_data() again because series execution
        uses the plan's data slots. This rule applies on both devices.
        """
        is_outer = not getattr(self, '_in_series_call', False)
        if is_outer:
            self._in_series_call = True
            t0 = time.perf_counter()
        try:
            return self._run_series_inner(series, starts=starts, win_start=win_start,
                                          win_end=win_end, binsize=binsize,
                                          threshold=threshold, templates=templates,
                                          raw=raw, decimated=decimated)
        finally:
            if is_outer:
                self._in_series_call = False
                self._record_batch_time(time.perf_counter() - t0)

    def _run_series_inner(self, series, starts=None, win_start=None, win_end=None,
                          binsize=None, threshold=0.0, templates=None, raw=False,
                          decimated=None):
        if starts is None:
            if win_start is not None or win_end is not None:
                raise ValueError('win_start and win_end require explicit starts')
            ser = np.ascontiguousarray(_from_any(series), dtype=np.complex64)
            if ser.ndim != 1:
                raise ValueError('series must be one-dimensional')
            st, ws, we = _automatic_series_layout(ser.size, self.valid)
            # The final clipped block can have fewer bins than the rest.
            # Keep its result in the same rectangular return shape, with
            # dismissed bins in the unused slots.
            bs = self.n if binsize is None else int(binsize)
            if bs < 1:
                raise ValueError('binsize must be >= 1')
            counts = 1 + (we - ws - 1) // bs
            if np.all(counts == counts[0]):
                result = self.run_series(ser, st, ws, we, binsize=bs,
                                         threshold=threshold, templates=templates,
                                         raw=raw)
                return _absolute_peak_indices(result, st, raw)
            main = self.run_series(ser, st[:-1], ws[:-1], we[:-1],
                                   binsize=bs, threshold=threshold,
                                   templates=templates, raw=raw) if st.size > 1 else None
            if main is not None:
                main = tuple(a.copy() for a in main) if raw else main.copy()
            tail = self.run_series(ser, st[-1:], ws[-1:], we[-1:],
                                   binsize=bs, threshold=threshold,
                                   templates=templates, raw=raw)
            if raw:
                ti, tv = tail
                nt = ti.shape[1]
                nb = int(max(counts))
                idx = np.full((st.size, nt, nb), -1, np.int64)
                val = np.zeros((st.size, nt, nb), np.complex64)
                if main is not None:
                    idx[:-1], val[:-1] = main
                idx[-1, :, :ti.shape[-1]] = ti[0]
                val[-1, :, :tv.shape[-1]] = tv[0]
                return _absolute_peak_indices((idx, val), st, True)
            nt = tail.shape[1]
            nb = int(max(counts))
            result = np.empty((st.size, nt, nb), PEAK_DTYPE)
            result['index'] = -1
            result['value'] = 0
            if main is not None:
                result[:-1] = main
            result[-1, :, :tail.shape[-1]] = tail[0]
            return _absolute_peak_indices(result, st, False)
        if win_start is None or win_end is None:
            raise ValueError('explicit starts require win_start and win_end')
        if getattr(self, '_bandlimited', False) and not isinstance(self, HierarchicalFilter):
            if decimated is None:
                decim = getattr(series, 'sample_rate', 2048) < getattr(series, 'input_sample_rate', 2048)
            else:
                decim = bool(decimated)
            return self.run_series_dif(
                series, starts, win_start, win_end, binsize=binsize,
                threshold=threshold, templates=templates, raw=raw,
                decimated=decim
            )
        ser, layout, binsize, t0, nt = self._grouped_layout(
            series, starts, win_start, win_end, binsize, templates)
        st, ws, we = layout.starts, layout.low, layout.high
        nblk = st.size
        # CPU series execution reuses the data slots. Require fresh spectra
        # before a later run(), consistently on both devices.
        self._dataset = False
        self._data_ready = set()
        if self._gpu is not None:
            return self._run_series_gpu(ser, layout, binsize, threshold, t0, nt, raw)
        nb = layout.nbins
        need = nblk * nt * nb
        shape = (nblk, nt, nb)
        ep = self._execution_plan()
        real = ser.dtype == np.float32
        stride = 2 if real and ser.strides == (8,) else 1
        held = self.__dict__.get("_ep_real")
        if real or (held is not None and held[0] is ep and held[1]):
            # The plan reads what it is given: real samples (one lane of a complex series,
            # stride 2, in place) or complex ones.
            if not ep.set_real_series(real, stride) and real:
                ser = np.ascontiguousarray(ser, dtype=np.complex64)
                real, stride = False, 1
                ep.set_real_series(False)
            self._ep_real = (ep, real)
        cser = ser
        if stride == 2:
            # The contiguous floats the lane lies in: the C plan reads every second one.
            cser = np.lib.stride_tricks.as_strided(ser, shape=(2 * ser.size - 1,), strides=(4,))
        if (raw and threshold > 0 and getattr(self, "_want_sparse", False)
                and hasattr(ep, "run_series_sparse")):
            # Sparse (time_domain asks with _want_sparse): the engine writes peaks only for
            # rows a tier passed, and only those come back -- no dense table written,
            # copied or scanned (at a detection threshold almost every row is empty).
            cnt = _scratch_counts(nblk * nt)
            fl, ix, vl, tot = ep.run_series_sparse(cser, st, ws, we, t0, nt, binsize,
                                                   float(threshold), cnt)
            self._last_n_triggers = tot
            sp = _SparsePeaks(shape, np.frombuffer(fl, np.int64), np.frombuffer(ix, np.int64),
                              np.frombuffer(vl, np.complex64))
            return sp if layout.order is None else _SparsePeaks.combine([(0, sp)], shape,
                                                                        layout.order)
        if raw:
            sb = self._sbuf
            if sb is None or sb[0] != shape:
                sb = self._sbuf = (shape,
                                   np.empty(need, dtype=np.int64),
                                   np.empty(need, dtype=np.complex64),
                                   np.empty(0, dtype=np.float32),
                                   np.empty(nblk * nt, dtype=np.int32))
            _, idx, val, mag, cnt = sb
            tot = self._execution_plan().run_series(cser, st, ws, we, t0, nt, binsize,
                                                    float(threshold), idx, val, mag, cnt)
            self._last_n_triggers = tot
            if tot == 0 and layout.order is not None:
                return (idx.reshape(shape), val.reshape(shape))
            return _format_result(idx.reshape(shape), val.reshape(shape),
                                  raw=True, order=layout.order)
        spbuf = getattr(self, '_spbuf', None)
        if spbuf is None or spbuf[0] != shape:
            spbuf = self._spbuf = (shape,
                                   np.empty(shape, dtype=PEAK_DTYPE),
                                   np.empty(0, dtype=np.int64),
                                   np.empty(0, dtype=np.complex64),
                                   np.empty(0, dtype=np.float32),
                                   np.empty(nblk * nt, dtype=np.int32))
        _, peaks, empty_idx, empty_val, mag, cnt = spbuf
        tot = self._execution_plan().run_series(cser, st, ws, we, t0, nt, binsize,
                                                float(threshold), empty_idx, empty_val, mag, cnt, peaks)
        self._last_n_triggers = tot
        return _format_result(None, None, raw=False, order=layout.order, out=peaks)

    def run_blocks(self, series, starts, win_start, win_end,
                   binsize=None, threshold=0.0, templates=None, raw=False):
        """Filter explicit blocks; peak indices are block-local lag positions.

        ``starts``, ``win_start`` and ``win_end`` contain one entry per block.
        This form supports irregular overlap-save layouts and per-block windows.
        """
        return self.run_series(series, starts, win_start, win_end,
                               binsize=binsize, threshold=threshold,
                               templates=templates, raw=raw)

    def run_series_dif(self, series, starts, win_start, win_end,
                       binsize=None, threshold=0.0, templates=None, raw=False,
                       decimated=False):
        """Filter a full-rate series using 2-channel decimation-in-frequency (DIF)."""
        ser = np.ascontiguousarray(_from_any(series), dtype=np.complex64)
        st = np.ascontiguousarray(_from_any(starts), dtype=np.uintp)
        ws = np.ascontiguousarray(_from_any(win_start), dtype=np.uintp)
        we = np.ascontiguousarray(_from_any(win_end), dtype=np.uintp)
        if any(a.ndim != 1 for a in (ser, st, ws, we)):
            raise ValueError("series, starts, win_start and win_end must be one-dimensional")
        if not (st.size == ws.size == we.size):
            raise ValueError("starts, win_start and win_end must be the same length")
        if st.size < 1:
            raise ValueError("run_series_dif needs at least one block")
        decim = int(bool(decimated))
        k_val = getattr(self, 'k', self.n)
        if decim:
            N = k_val
        else:
            N = self.n if getattr(self, '_bandlimited', False) else self.n * 2
        bs = N if binsize is None else int(binsize)
        if bs < 1:
            raise ValueError("binsize must be >= 1")
        ends = np.minimum(we, N)
        if np.any(ws >= ends):
            raise ValueError("invalid search window in DIF")
        bin_counts = 1 + (ends - ws - 1) // bs
        if np.any(bin_counts != bin_counts[0]):
            raise ValueError("block windows must have equal bin counts")
        t0, nt = (0, self.ntemplates) if templates is None else (
            int(templates[0]), int(templates[1]))
        if nt < 1 or t0 < 0 or t0 + nt > self.ntemplates:
            raise ValueError("templates sub-range out of bounds")
        self._require_templates(t0, nt)

        nblk = st.size
        nb = int(bin_counts[0])
        need = nblk * nt * nb
        shape = (nblk, nt, nb)

        self._dataset = False
        self._data_ready = set()

        if raw:
            sb = getattr(self, '_sbuf_dif', None)
            if sb is None or sb[0] != shape:
                sb = self._sbuf_dif = (shape,
                                       np.empty(need, dtype=np.int64),
                                       np.empty(need, dtype=np.complex64),
                                       np.empty(0, dtype=np.float32),
                                       np.empty(nblk * nt, dtype=np.int32))
            _, idx, val, mag, cnt = sb
            self._execution_plan().run_series_dif(ser, st, ws, we, t0, nt, bs,
                                                  float(threshold), idx, val, mag, cnt, None, decim)
            return _format_result(idx.reshape(shape), val.reshape(shape), raw=True)
        spbuf = getattr(self, '_spbuf_dif', None)
        if spbuf is None or spbuf[0] != shape:
            spbuf = self._spbuf_dif = (shape,
                                       np.empty(shape, dtype=PEAK_DTYPE),
                                       np.empty(0, dtype=np.int64),
                                       np.empty(0, dtype=np.complex64),
                                       np.empty(0, dtype=np.float32),
                                       np.empty(nblk * nt, dtype=np.int32))
        _, peaks, empty_idx, empty_val, mag, cnt = spbuf
        self._execution_plan().run_series_dif(ser, st, ws, we, t0, nt, bs,
                                              float(threshold), empty_idx, empty_val, mag, cnt, peaks, decim)
        return _format_result(None, None, raw=False, out=peaks)

    @property
    def performance_info(self):
        """Dictionary of performance summary metrics."""
        return self.performance_summary()

    def performance_summary(self):
        """Return a dictionary summarizing performance metrics and configuration."""
        stats = self.performance_stats
        times = stats.get("batch_times_ms", [])
        total_calls = stats.get("total_calls", 0)
        timed_calls = stats.get("timed_calls", len(times))
        total_time_s = stats.get("total_time_s", 0.0)
        if times:
            min_ms = stats.get("min_batch_time_ms")
            max_ms = stats.get("max_batch_time_ms")
            min_ms = float(np.min(times)) if min_ms is None else float(min_ms)
            max_ms = float(np.max(times)) if max_ms is None else float(max_ms)
            med_ms = float(np.median(times))
            mean_ms = (total_time_s * 1000.0 / timed_calls) if timed_calls > 0 else float(np.mean(times))
        else:
            min_ms = max_ms = med_ms = mean_ms = 0.0

        summary = {
            "total_calls": total_calls,
            "timed_calls": timed_calls,
            "sampled_calls": len(times),
            "total_time_s": total_time_s,
            "min_batch_time_ms": min_ms,
            "max_batch_time_ms": max_ms,
            "median_batch_time_ms": med_ms,
            "mean_batch_time_ms": mean_ms,
            "device": getattr(self.device, "name", str(self.device)),
            "backend": backend(),
        }
        if hasattr(self, "autotune_info"):
            summary["autotune"] = dict(self.autotune_info)
        return summary

    def _grouped_dispatch(self, n, spec, H, groups, binsize, threshold, **kw):
        """Every window group of one spectra batch in one backend submission."""
        return self._gpu.peaks_grouped(n, spec, H, groups, binsize, threshold,
                                       upload_tmpl=self._tdirty, **kw)

    def _series_window(self, spec, H, binsize, threshold, w0, w1, slot=None, async_submit=False,
                       **kw):
        # Each group has fresh spectra, even when it reuses an allocation.
        self._ddirty = True
        return self._gpu_window(spec, H, binsize, threshold, w0, w1, slot=slot,
                                async_submit=async_submit, **kw)

    def _next_batch_base(self, K):
        """The first slot of a new deferred batch: the previous batch's base once that batch
        has been collected, else the other half (0 <-> K/2). Slots, their recordings and call
        plans are per slot, so alternating unconditionally doubled them (and with them cache
        evictions and re-recording, every segment) for callers that never keep two batches
        in flight; a caller that does (a pipeline collecting k-2) gets disjoint slots for the
        batch still running."""
        prev = self.__dict__.get("_defer_base")
        if prev is None or K < 2:
            return 0
        owners = self.__dict__.get("_slot_owner") or {}
        busy = any(not getattr(d, "_done", True) for d in owners.values())
        return (prev + K // 2) % K if busy else prev

    def _call_plan_state(self, layout, binsize, threshold, t0, nt):
        """Everything a recorded call plan was built under: (objects, values). Objects are
        compared by identity -- the plan holds them, so none can be freed and replaced at the
        same address -- and values by equality. Anything that changes what the call would
        submit changes one of them: new templates or coarse templates, a recalibrated chain,
        replaced pools, another backend context, the queue depth, the batch budget."""
        ws = self.__dict__.get("_series_workspace")
        objs = (layout, self._gpu, self._gtmpl, self.__dict__.get("_gcal"),
                self.__dict__.get("_ct"), self.__dict__.get("_ckey"),
                None if ws is None else ws[2], None if ws is None else ws[3])
        vals = (int(binsize), float(threshold), t0, nt, self.__dict__.get("_series_batch_bytes"),
                os.environ.get("MF_GPU_QUEUE_AHEAD", "8"),
                bool(self.__dict__.get("_want_sparse", False)))
        return objs, vals

    @staticmethod
    def _same_state(a, b):
        return (a[1] == b[1] and len(a[0]) == len(b[0])
                and all(x is y for x, y in zip(a[0], b[0])))

    def _replay_call_plan(self, ser, layout, binsize, threshold, t0, nt, raw):
        """A deferred grouped hierarchical call submitted from its recorded call plan, or None.

        The first deferred call of a shape runs the full path below and records what it
        submitted (_record_call_plan): the batches' rebased starts, and per batch the
        backend's forward and hierarchical records (handles). A repeat with the same state
        (_call_plan_state), the same series memory and the same slot skips layout, policy,
        source resolution and key building: it rewrites the starts, re-queues the records and
        returns the same kind of deferred result. The backend checks each handle (record
        identity, resident input signatures) before anything is submitted; any stale handle
        falls back to the full path, which records afresh."""
        plans = self.__dict__.get("_call_plans")
        if (not plans or not raw or self._tdirty or not getattr(self, "_defer_series", False)):
            return None
        d = self.__dict__
        vals = (int(binsize), float(threshold), t0, nt, d.get("_series_batch_bytes"),
                os.environ.get("MF_GPU_QUEUE_AHEAD", "8"), bool(d.get("_want_sparse", False)))
        addr = ser.ctypes.data
        entry = plans.get((addr, ser.size, vals, id(layout)))
        if entry is None:
            return None
        # The objects of _call_plan_state, by identity, inline (this is the hot path).
        objs = entry["state"][0]
        ws = d.get("_series_workspace")
        if (objs[0] is not layout or objs[1] is not self._gpu or objs[2] is not self._gtmpl
                or objs[3] is not d.get("_gcal") or objs[4] is not d.get("_ct")
                or objs[5] is not d.get("_ckey") or ws is None or objs[6] is not ws[2]
                or objs[7] is not ws[3]):
            return None
        lo_addr, hi_addr = entry["span"]
        extent = (ser.size - 1) * ser.strides[0] + ser.itemsize if ser.size else 0
        if not (lo_addr <= addr and addr + extent <= hi_addr):
            return None
        K = entry["K"]
        token = self._defer_series
        slot0 = self._next_batch_base(K) if getattr(self, "_defer_token", None) != token else (
            getattr(self, "_defer_slot", 0) % K)
        parts = entry["slots"].get(slot0)
        lo, span = 0, K
        if parts is None or len(parts) > span:
            # More batches than slots: a batch would reuse an earlier one's slot (fence,
            # recordings, result buffers) while it is in flight. The full path collects the
            # earlier one first.
            return None
        gpu = self._gpu
        for _, fh, hh in parts:
            if not (gpu.forward_valid(fh) and gpu.hier_valid(hh)):
                return None
        if getattr(self, "_defer_token", None) != token:
            self._defer_base = slot0
            self._defer_token, self._defer_slot = token, slot0
        owners = self.__dict__.setdefault("_slot_owner", {})
        for k in range(min(span, len(parts) + len(layout.groups))):
            prev = owners.pop(lo + (slot0 + k - lo) % span, None)
            if prev is not None:
                prev.result()
        n = self.n
        shape = (layout.starts.size, nt, layout.nbins)
        self._last_series_batch = entry["batch"]
        starts_pool = entry["starts_pool"]
        in_flight = []
        slot_idx = slot0
        for (begin, end, count, rebased), fh, hh in parts:
            slot = lo + (slot_idx - lo) % span
            slot_idx += 1
            starts_pool[slot][:count] = rebased
            gpu.forward_replay(fh, slot)
            res = gpu.hier_replay(hh, slot, True, validated=True)
            if res is None:
                raise RuntimeError("a validated call plan part was refused")
            in_flight.append((begin, end, res))
        idx = np.empty(shape, dtype=np.int64)
        val = np.empty(shape, dtype=np.complex64)
        sparse_parts = []

        def finish_grouped():
            # As the full path's finish_grouped/take_dense/finish_raw for a grouped call.
            for b_start, b_end, item in in_flight:
                r = item()
                shp = r.shape if isinstance(r, _SparsePeaks) else r[0].shape
                self._gpairs += shp[0] * shp[1]
                self._gtrig += gpu.last_refinements
                self._gt1 += getattr(gpu, "last_tier1_survivors", 0) or 0
                if isinstance(r, _SparsePeaks):
                    sparse_parts.append((b_start, r))
                else:
                    idx[b_start:b_end], val[b_start:b_end] = r
            in_flight.clear()
            if sparse_parts:
                return _SparsePeaks.combine(sparse_parts, shape, layout.order)
            return _format_result(idx, val, raw=True, order=layout.order)
        self._defer_slot = slot_idx
        deferred = _Deferred(finish_grouped)
        for k in range(slot0, slot_idx):
            owners[lo + (k - lo) % span] = deferred
        self.call_plan_replays = getattr(self, "call_plan_replays", 0) + 1
        return deferred

    def _record_call_plan(self, ser, layout, binsize, threshold, t0, nt, K, batch, slot0,
                          whole, parts, starts_pool):
        """Keep what a deferred grouped call submitted, for _replay_call_plan."""
        state = self._call_plan_state(layout, binsize, threshold, t0, nt)
        plans = self.__dict__.setdefault("_call_plans", {})
        key = (ser.ctypes.data, ser.size, state[1], id(layout))
        entry = plans.get(key)
        if entry is None or not self._same_state(entry["state"], state):
            if len(plans) >= 16:
                plans.clear()
            start = whole.ctypes.data
            # Holding whole keeps its allocation alive, so its address range cannot be
            # reused by another allocation while this plan exists.
            entry = plans[key] = dict(state=state, K=K, batch=batch, whole=whole,
                                      span=(start, start + whole.nbytes), slots={},
                                      starts_pool=starts_pool)
        entry["slots"][slot0] = parts

    def _fast_series(self, ser, layout, binsize, threshold, defer, queue_offset, sparse):
        """A repeated deferred series call straight from its call plan (_replay_call_plan),
        with the flags run_series would set around it; None when the plan does not hold
        (the caller then makes the full call). layout is the one this plan's full call
        used (_last_layout): the plan checks its identity."""
        self._defer_series, self._want_sparse = defer, sparse
        self._gpu._queue_offset = queue_offset
        try:
            res = self._replay_call_plan(ser, layout, binsize, threshold, 0, self.ntemplates,
                                         True)
        finally:
            self._defer_series, self._want_sparse = False, False
        if res is not None:
            self._dataset = False
            self._data_ready = set()
            self.performance_stats["total_calls"] += 1
        return res

    def _run_series_gpu(self, ser, layout, binsize, threshold, t0, nt, raw):
        """Execute shared layout groups with bounded FFT/gather storage: a recorded call plan
        when this call repeats one (_replay_call_plan); else the call's setup (_series_call),
        then every batch -- one grouped dispatch over all window groups where the backend
        has one (_series_grouped), else one dispatch per window group (_series_by_group)."""
        self._last_layout = layout
        replayed = self._replay_call_plan(ser, layout, binsize, threshold, t0, nt, raw)
        if replayed is not None:
            return replayed
        c = self._series_call(ser, layout, binsize, threshold, t0, nt, raw)
        out = _SeriesOutput(self, c)
        try:
            if c.grouped:
                return self._series_grouped(c, out)
            return self._series_by_group(c, out)
        finally:
            # A viewed series' owner and the workspace this call started from live for the
            # call, not for its deferred result (whose closures keep `c`): an owner kept
            # until a later call collected the result unregistered a series that call had
            # found already shared (and so had not viewed), and Metal's forward refused it.
            c.series_owner = c.workspace = None

    def _series_call(self, ser, layout, binsize, threshold, t0, nt, raw):
        """Everything a series call decides before it dispatches: its batch size, whether it
        is deferred, pipelined, sparse or grouped, its slots, and where the blocks read the
        series from (in place, or a span uploaded to a slot's source buffer)."""
        from ._shared import shared_buffer
        c = SimpleNamespace(ser=ser, layout=layout, binsize=binsize, threshold=threshold,
                            t0=t0, nt=nt, raw=raw)
        n, nb, nblk = self.n, layout.nbins, layout.starts.size
        c.n, c.nb, c.nblk = n, nb, nblk
        c.H = self._gtmpl[t0:t0 + nt]
        if ser.size > np.iinfo(np.uint32).max:
            raise ValueError("GPU series exceeds the 32-bit sample address range")
        budget = getattr(self, "_series_batch_bytes", 64 * 1024 * 1024)
        batch = min(nblk, 65535, max(1, self._gpu_pair_limit() // nt),
                    max(1, budget // (8*n + 4 + 12*nt*nb)))
        if isinstance(self, HierarchicalFilter):
            band = self._gpu_calibration(threshold)[0][-1]
            operation = 'hierarchical_series'
        else:
            band, operation = 0, 'flat_series'
        pkey = (operation, band, nt)
        pc = self.__dict__.setdefault("_policy_cache", {})
        policy = pc.get(pkey, pc)
        if policy is pc:
            policy = pc[pkey] = self._series_policy(operation, band, nt)
        if policy:
            batch = min(batch, policy['series_group'])
        c.batch = batch
        self._last_series_batch = batch
        # A single group needs no aggregate buffers or scatter.
        c.single = single = len(layout.groups) == 1 and nblk <= batch
        # Sparse results (time_domain asks with _want_sparse): only the peaks come back.
        # At threshold 0 (follow-ups) every bin holds a peak: dense is cheaper there.
        sparse = bool(raw and threshold > 0 and getattr(self, "_want_sparse", False))
        c.skw = {"sparse": True} if sparse else {}
        c.is_hier = isinstance(self, HierarchicalFilter)
        # A declared capability, not a probe for one backend's internals.
        can_pipeline = getattr(self._gpu, "cache_limit_bytes", 10**9) > 1024 * 1024
        grouped_flat = (len(layout.groups) > 1 and type(self) is MatchedFilter
                        and nb <= getattr(self._gpu, "max_grouped_bins", 0)
                        and nt <= self._gpu_pair_limit())
        # Deferred (TimeDomainFilterBank.filter_series_many): submit now, collect later, so the
        # GPU works on this call while the host prepares the next bank's. (A chain trial on the
        # GPU is judged per batch, in the mode the search runs: deferred too.)
        # A grouped flat call defers too when it is one batch (a follow-up's window: one
        # submission for every bin count).
        c.defer = defer = (getattr(self, "_defer_series", False) and can_pipeline
                           and (not grouped_flat or nblk <= batch))
        c.pipelined = can_pipeline and (not single or defer)
        queue_ahead = int(os.environ.get("MF_GPU_QUEUE_AHEAD", "8"))
        c.K = K = max(1, queue_ahead) if c.pipelined else 1
        # Irregular flat windows share one forward FFT dispatch and submission per bounded
        # batch. Hierarchical plans join when the backend submits grouped hierarchical windows
        # (one dispatch per tier over every row, each in its own window). Deferred calls
        # (filter_series_many) keep the one-submission grouped path: without it a deferred
        # hierarchical call became one submission per window group (3x the submissions and
        # launches of the synchronous call, measured 1.4x slower on CUDA).
        c.grouped = grouped_flat or (
            len(layout.groups) > 1 and c.is_hier
            and hasattr(self._gpu, "hier_peaks_grouped")
            and nb <= getattr(self._gpu, "max_grouped_bins", 0)
            and nt <= self._gpu_pair_limit())
        # A real series (a backend with real_series): the forward reads its samples from
        # complex64 storage, by float offset and stride (c.real), never widened on the host.
        real = ser.dtype == np.float32
        c.real = None
        source_shared = not real and shared_buffer(ser, self._gpu) is not None
        # Unified memory: read a page-aligned series where it is rather than copying the
        # span into the source buffer (a fine-stage call copied ~6 MB per call). The owner
        # lives for this call; each command buffer retains what it reads.
        view = getattr(self._gpu, "host_view", None)
        series_owner = view(ser) if (view is not None and not source_shared
                                     and not real) else None
        if series_owner is not None:
            source_shared = True
        # A series inside a device allocation (a row of a device buffer a caller reuses, e.g.
        # correlate_series(out=bank.empty_shared(...)), or one real lane of such a row) is
        # read where it is, by offset -- unless a block would read past its end, where the
        # upload's zero padding is needed.
        contained = None
        if not source_shared and nblk:
            from ._shared import containing, containing_samples
            contained = (containing_samples if real else containing)(ser, self._gpu)
            if contained is not None and int(layout.starts.max()) + n > ser.size:
                contained = None
            if real and contained is not None and (
                    contained[1] + contained[2] * ser.size > np.iinfo(np.uint32).max):
                contained = None            # float offsets past the kernel's 32-bit index
        c.contained, c.source_shared, c.series_owner = contained, source_shared, series_owner
        c.viewed = series_owner is not None
        # Pools are sized by capacity, not by this call's batch: windowed calls vary in
        # block count, and reallocating would also discard every recording built on them.
        # Capacity in both batch and slots: a call alternating unpipelined (K=1) and pipelined
        # (K=8) groups reallocated every call, and recordings are keyed on these buffers.
        workspace = getattr(self, "_series_workspace", None)
        if (workspace is None or workspace[0][1] != n or workspace[0][0] < batch
                or workspace[0][2] < K):
            # The old pools go when this call replaces them: deferred calls of this plan still
            # in flight (or captured into an unsubmitted fused batch) write their spectra, so
            # settle them first. Dropping the pools under them was a GPU write to freed pages
            # (amdgpu page fault, VK_ERROR_DEVICE_LOST) in about one ladder run in five.
            self._settle_deferred()
            cap_b = (batch if workspace is None or workspace[0][1] != n else max(batch, workspace[0][0])) + 16
            cap_k = K if workspace is None or workspace[0][1] != n else max(K, workspace[0][2])
            spectra_pool = [self._gpu.empty_shared((cap_b, n)) for _ in range(cap_k)]
            starts_pool = [self._gpu.empty_shared(cap_b, np.uint32) for _ in range(cap_k)]
            workspace = ((cap_b, n, cap_k), None if workspace is None else workspace[1],
                         spectra_pool, starts_pool)
        _, source, c.spectra_pool, c.starts_pool = workspace
        if not defer:
            # A synchronous call reuses slots (and their fences) from 0: finish whatever a
            # batch still has in flight on this plan first, or two submissions share a fence
            # and one wait never returns.
            self._settle_deferred()
        if defer and getattr(self, "_defer_token", None) != self._defer_series:
            # A new batch starts at slot 0 or K/2, alternately: slots only have to differ
            # among calls in flight together -- a batch's own, and the previous batch's
            # while the caller keeps two in flight (a pipeline collecting segment k-2) --
            # and reusing the same few keeps their recordings and sources warm.
            base = self._next_batch_base(K)
            self._defer_base = base
            self._defer_token, self._defer_slot = self._defer_series, base
        c.slot0 = slot0 = getattr(self, "_defer_slot", 0) % K if defer else 0
        if defer:
            # Settle whatever still holds the slots this call will use: its spectra, starts,
            # source and recordings are about to be rewritten.
            owners = self.__dict__.setdefault("_slot_owner", {})
            for k in range(min(K, -(-nblk // batch) + len(layout.groups))):
                prev = owners.pop((slot0 + k) % K, None)
                if prev is not None:
                    prev.result()
        if contained is not None and real:
            whole, offset, stride = contained
            source, base = whole, -(offset // stride)
            c.real = (offset % stride, stride, ser.size - base)
            self._series_workspace = (workspace[0], workspace[1], c.spectra_pool, c.starts_pool)
        elif contained is not None:
            source, base = contained[0], -contained[1]
            self._series_workspace = (workspace[0], workspace[1], c.spectra_pool, c.starts_pool)
        elif source_shared:
            source, base = ser, 0
            # A viewed series keeps the copy buffer for later calls that need one.
            self._series_workspace = (workspace[0], workspace[1] if series_owner is not None
                                      else None, c.spectra_pool, c.starts_pool)
        else:
            # Upload only the span the blocks read: a windowed call touches a small part
            # of a long series. Starts are rebased onto it; reads past the series end
            # stay past the end of the span.
            # The host reads the series here: writes left in flight to it must land first.
            settle = getattr(self._gpu, 'settle_writes', None)
            if settle is not None:
                settle()
            base = min(int(layout.starts.min()), ser.size) if nblk else 0
            top = min(ser.size, int(layout.starts.max()) + n) if nblk else 0
            if top - base < 1:                # every block starts at the series end
                base = max(0, top - 1)
            span = max(top - base, 1)
            # One source per slot: deferred calls on this plan can be in flight together
            # with different series (a bank filters each detector's).
            sources = source if isinstance(source, dict) else ({} if source is None else {0: source})
            src = sources.get(slot0)
            if src is None or src.size < span:
                # Capacity for the whole series: later windows need not reallocate.
                src = sources[slot0] = self._gpu.empty_shared((max(ser.size, span),))
            self._series_workspace = (workspace[0], sources, c.spectra_pool, c.starts_pool)
            if real:
                src.view(np.float32)[:top - base] = ser[base:top]
                source = src[:(top - base + 1) // 2]
                c.real = (0, 1, top - base)
            else:
                src[:top - base] = ser[base:top]
                source = src[:top - base]
        c.source, c.base = source, base
        c.workspace = workspace          # held for the call (see _run_series_gpu)
        return c

    def _series_submit(self, c, slot_idx, begin, count, rebased, **forward_kw):
        """A batch's slot and spectra, with its block starts written and its forward submitted
        (deferred: the dispatch that reads the spectra takes it)."""
        slot = slot_idx % c.K
        starts = c.starts_pool[slot]
        spec = c.spectra_pool[slot][:count]
        starts[:count] = rebased
        if c.real is not None:
            forward_kw["real"] = c.real
        self._gpu.forward(c.n, c.source, starts[:count], spec, defer=True,
                          slot=slot if c.pipelined else None, **forward_kw)
        return slot, spec

    def _series_deferred(self, c, slot_idx, finish):
        """A deferred call's result: its next slot kept for the next call, and every slot it
        used owned by it until it is collected."""
        self._defer_slot = slot_idx
        deferred = _Deferred(finish)
        owners = self.__dict__.setdefault("_slot_owner", {})
        for k in range(c.slot0, slot_idx):
            owners[k % c.K] = deferred
        return deferred

    def _series_grouped(self, c, out):
        """Every batch as one grouped dispatch over all its window groups."""
        layout, nblk, batch, ser, base = c.layout, c.nblk, c.batch, c.ser, c.base
        in_flight = []
        slot_idx = c.slot0 if c.defer else 0
        # The batches' groups and rebased starts, per (layout, batch, series size, base):
        # the same every segment of a search.
        ckey = (id(layout), batch, ser.size, base)
        bc = self.__dict__.setdefault("_batch_cache", {})
        plan_b = bc.get(ckey)
        if plan_b is None or plan_b[0] is not layout:
            if len(bc) >= 32:
                bc.clear()
            parts = []
            for begin in range(0, nblk, batch):
                end = min(begin + batch, nblk)
                parts.append((begin, end, end - begin, tuple(
                    (lo, hi, max(a, begin)-begin, min(b, end)-begin)
                    for lo, hi, a, b in layout.groups if a < end and b > begin),
                    (np.minimum(layout.starts[begin:end], ser.size).astype(np.int64)
                     - base).astype(np.uint32)))
            plan_b = bc[ckey] = (layout, parts)
        # A deferred call reading a device allocation in place records its call plan
        # (_replay_call_plan): every batch's forward and hierarchical record handles.
        # Read in place means a row of an allocation (contained) or a whole one -- not a
        # host array viewed for this call (series_owner).
        record = (c.defer and c.is_hier and c.raw and c.pipelined
                  and (c.contained is not None or (c.source_shared and not c.viewed)))
        recorded = []
        for begin, end, count, groups, rebased in plan_b[1]:
            fh, hh = [], []
            slot, spec = self._series_submit(c, slot_idx, begin, count, rebased,
                                             **({"handle_out": fh} if record else {}))
            slot_idx += 1
            try:
                res = self._grouped_dispatch(
                    c.n, spec, c.H, groups, c.binsize, c.threshold,
                    slot=slot if c.pipelined else None, async_submit=c.pipelined,
                    **({"nbins": c.nb} if getattr(layout, "ragged", False) else {}), **c.skw,
                    **({"handle_out": hh} if record else {}))
                self._tdirty = False
            except Exception:
                self._gpu.cancel_forward(slot=slot if c.pipelined else None)
                raise
            if record:
                if len(fh) == 1 and len(hh) == 1:
                    recorded.append(((begin, end, count, rebased), fh[0], hh[0]))
                else:
                    record = False              # e.g. a split window: not one record
            in_flight.append((begin, end, res))
            if len(in_flight) >= c.K:
                b_start, b_end, item = in_flight.pop(0)
                out.take(b_start, b_end, item() if callable(item) else item)

        def finish_grouped():
            while in_flight:
                b_start, b_end, item = in_flight.pop(0)
                out.take(b_start, b_end, item() if callable(item) else item)
            return out.finish()
        if not c.defer:
            return finish_grouped()
        if record and recorded:
            self._record_call_plan(ser, layout, c.binsize, c.threshold, c.t0, c.nt, c.K, batch,
                                   c.slot0, c.contained[0] if c.contained is not None else ser,
                                   recorded, c.starts_pool)
        return self._series_deferred(c, slot_idx, finish_grouped)

    def _series_by_group(self, c, out):
        """Every window group's batches as their own dispatches (one group, or a backend or
        shape without a grouped dispatch)."""
        layout, ser, base = c.layout, c.ser, c.base
        in_flight = []
        collected_early = [False]
        slot_idx = c.slot0
        for w0, w1, a, b in layout.groups:
            for begin in range(a, b, c.batch):
                end = min(begin + c.batch, b)
                count = end - begin
                rebased = np.minimum(layout.starts[begin:end], ser.size).astype(np.int64) - base
                slot, spec = self._series_submit(c, slot_idx, begin, count, rebased)
                slot_idx += 1
                try:
                    res = self._series_window(spec, c.H, c.binsize, c.threshold, w0, w1,
                                              slot=slot if c.pipelined else None,
                                              async_submit=c.pipelined, **c.skw)
                except Exception:
                    self._gpu.cancel_forward(slot=slot if c.pipelined else None)
                    raise
                self._ddirty = self._tdirty = False
                in_flight.append((begin, end, res))
                if len(in_flight) >= c.K:
                    collected_early[0] = True
                    b_start, b_end, item = in_flight.pop(0)
                    r = out.take_one(b_start, b_end, item() if callable(item) else item)
                    if r is not None:
                        return r
        refined = [0]

        def finish():
            while in_flight:
                b_start, b_end, item = in_flight.pop(0)
                r = item() if callable(item) else item
                if c.is_hier:
                    refined[0] += getattr(self._gpu, "last_refinements", 1)
                r = out.take_one(b_start, b_end, r, final=True)
                if r is not None:
                    return r
            return out.finish()

        if not c.defer:
            return finish()

        def finish_marking():
            value = finish()
            # Refinements already collected mid-loop are not counted: only claim empty when
            # every batch was collected here.
            if c.is_hier and refined[0] == 0 and not collected_early[0]:
                deferred.empty = True
            return value
        deferred = self._series_deferred(c, slot_idx, finish_marking)
        return deferred

    def wait(self):
        """Finish the device work this plan left in flight (run(wait=False)), before a
        host read of what it writes. Nothing to do on the CPU."""
        settle = getattr(self._gpu, 'settle_writes', None)
        if settle is not None:
            settle()

    def empty_shared(self, shape, dtype=np.complex64, *, readback=False):
        """Allocate a NumPy array backed by this filter's GPU shared memory.

        CPU filters return ordinary NumPy storage. On GPU, contiguous full
        banks passed to the setters bind directly without an input copy.
        Set ``readback=True`` for an output that NumPy will read or modify
        after GPU execution. Vulkan then prefers host-cached memory instead
        of the faster GPU-write, uncached CPU-read memory used by default.
        Keep mutations outside run/run_series calls; call the setter again
        after editing a bank to invalidate hierarchical coarse caches.
        NumPy views and CPU DLPack consumers retain the allocation's lifetime.
        This does not export a CUDA/ROCm allocation or an asynchronous stream.
        """
        if self._gpu is None:
            return np.empty(shape, dtype=dtype)
        return self._gpu.empty_shared(shape, dtype, readback=readback)

    def set_memory_limits(self, *, cache_bytes=None, series_bytes=None):
        """Set GPU dispatch-cache and series-temporary budgets in bytes.

        Defaults: 512 MiB of dispatch buffers, 32 storage shapes (and up to
        256 Vulkan command recordings), and 64 MiB of series working storage. A single dispatch/block can exceed a
        budget. The source-series upload (unless already shared) and final
        returned output are not included in the batch working budget.
        Changing the cache budget releases existing dispatch buffers.
        """
        if self._gpu is None:
            raise ValueError("memory budgets apply to GPU filters")
        for value in (cache_bytes, series_bytes):
            if value is not None and int(value) < 1:
                raise ValueError("memory budgets must be positive")
        if cache_bytes is not None:
            self.clear_cache()
            self._gpu.cache_limit_bytes = int(cache_bytes)
        if series_bytes is not None:
            self._series_batch_bytes = int(series_bytes)

    def clear_cache(self):
        """Release GPU dispatch buffers, keeping spectra and compiled pipelines."""
        if self._gpu is not None:
            self._gpu.clear_cache()
            self._series_workspace = None
            self._continuous_workspaces = []
            self._ddirty = self._tdirty = True


class CorrelationFilter(MatchedFilter):
    """Return every complex lag for each data/template pair.

    Spectra, device selection and pair selectors follow :class:`MatchedFilter`.
    ``run`` returns ``(ndata, ntemplates, n)`` complex64 samples in natural
    lag order. No peak threshold or binning is applied.
    """

    _gpu_sizes = frozenset(1 << k for k in range(10, 23))
    _cpu_max_n = 1 << 22
    _max_auto_output_bytes = 512 * 1024 * 1024

    def _continuous_gpu(self, ser, starts, t0, nt, out, defer=False):
        """Forward-transform bounded block batches into continuous GPU output.

        ``defer``: leave the last batch in flight (a backend with zero_columns finishes it
        in zero_columns_done), so the caller's zeroing overlaps the device's work."""
        from ._shared import shared_buffer
        if ser.size > np.iinfo(np.uint32).max or nt * ser.size > np.iinfo(np.uint32).max:
            raise ValueError("GPU series exceeds the 32-bit sample address range")
        budget = getattr(self, '_series_batch_bytes', 64 * 1024 * 1024)
        per_block = 8 * self.n * ((1 + nt) if self.n > 65536 else 1)
        batch = max(1, min(starts.size, self._gpu_pair_limit() // nt,
                           budget // per_block))
        policy = self._series_policy('correlation_series', 0, nt)
        if policy:
            batch = min(batch, policy['series_group'])
        # Two workspaces, alternating per call, each remembering the write it left in flight:
        # rewriting one waits only for the call two back, not for every write on the device
        # (the previous call -- another detector's middle stage -- keeps running).
        pool = self.__dict__.setdefault('_continuous_workspaces', [])
        k = self.__dict__.get('_continuous_next', 0) % 2
        self._continuous_next = k + 1
        while len(pool) <= k:
            pool.append(None)
        work = pool[k]
        if work is not None:
            self._gpu.settle_until(work[4])  # the call that used it has finished reading it
        # Reused while large enough: the block count follows each call's windows, and a
        # workspace keyed on it was three new allocations (and new recordings) per call.
        if work is None or work[1].size < ser.size or work[2].shape[0] < batch:
            cap = (max(ser.size, work[1].size), max(batch, work[2].shape[0])) if work else (
                ser.size, batch)
            work = (None, self.empty_shared((cap[0],)), self.empty_shared((cap[1], self.n)),
                    self.empty_shared(cap[1], np.uint32), None)
        _, staging, spec, offsets, _ = work
        # A real series (a backend with real_series): the forward reads its samples from
        # complex64 storage, by float offset and stride -- in place where it lies in a device
        # allocation (then block starts move by the series' offset in it, so the forward
        # takes its own copy of them; the output keeps the caller's), else copied as floats.
        real, shift = None, 0
        if ser.dtype == np.float32:
            from ._shared import containing_samples
            c = containing_samples(ser, self._gpu)
            if c is not None and c[1] + c[2] * ser.size <= np.iinfo(np.uint32).max:
                whole, off, stride = c
                shift = off // stride
                source, real = whole, (off % stride, stride, shift + ser.size)
            else:
                staging.view(np.float32)[:ser.size] = ser
                source, real = staging[:max(1, (ser.size + 1) // 2)], (0, 1, ser.size)
        else:
            staging = staging[:ser.size]
            source = ser if shared_buffer(ser, self._gpu) is not None else staging
        fwd_offsets = offsets
        if shift:
            fo = self.__dict__.setdefault('_continuous_fwd_offsets', {})
            fwd_offsets = fo.get(k)
            if fwd_offsets is None or fwd_offsets.size < offsets.size:
                fwd_offsets = fo[k] = self.empty_shared(offsets.size, np.uint32)
        if real is None and source is staging and defer:
            # Unified memory: read the caller's series in place; the context keeps the
            # view until zero_columns_done has waited for the work that reads it.
            owner = getattr(self._gpu, 'host_view', lambda a: None)(ser)
            if owner is not None:
                self._gpu._keep_until_done.append(owner)
                source = ser
        if real is None and source is staging:
            source[:] = ser
        lo, hi = self.valid
        for b0 in range(0, starts.size, batch):
            b1 = min(b0 + batch, starts.size)
            count = b1 - b0
            offsets[:count] = np.minimum(starts[b0:b1], ser.size)
            if shift:
                fwd_offsets[:count] = offsets[:count] + np.uint32(shift)
            self._gpu.forward(self.n, source, fwd_offsets[:count], spec[:count], defer=True,
                              **({'real': real} if real is not None else {}))
            try:
                kw = dict(async_submit=True) if (defer and b1 == starts.size) else {}
                self._gpu.correlate_continuous(
                    self.n, spec[:count], self._gtmpl[t0:t0 + nt],
                    offsets[:count], out, lo, hi,
                    upload_data=True, upload_tmpl=self._tdirty, **kw)
            finally:
                self._gpu.cancel_forward()
            self._tdirty = False
        pool[k] = work[:4] + (self._gpu.write_token(),)

    def _full_output(self, shape, out):
        nbytes = math.prod(shape) * np.dtype(np.complex64).itemsize
        if out is None:
            if nbytes > self._max_auto_output_bytes:
                raise ValueError(
                    "full correlation needs %d bytes of output; select smaller "
                    "data/templates ranges or pass a preallocated out array" % nbytes)
            return self.empty_shared(shape)
        if not isinstance(out, np.ndarray) or out.dtype != np.complex64 \
           or out.shape != shape or not out.flags.c_contiguous \
           or not out.flags.writeable:
            raise ValueError("out must be a writable C-contiguous complex64 array of shape %s" % (shape,))
        return out

    def run(self, data=None, templates=None, out=None, scales=None, wait=True):
        """Return the full unnormalised circular correlation for each pair.

        wait=False, with ``out`` from :meth:`empty_shared` and no ``scales``: a GPU backend
        that can (Vulkan) leaves the work in flight. Work on the same device that reads
        ``out`` is ordered after it; read it on the host only after :meth:`wait`.
        Elsewhere the call finishes as with wait=True."""
        d0, nd, t0, nt = self._pair_range(data, templates)
        result = self._full_output((nd, nt, self.n), out)
        if self._gpu is None:
            self._execution_plan().correlate(d0, nd, t0, nt, result)
        else:
            kw = ({'wait': False} if (not wait and scales is None
                                      and getattr(self._gpu, 'async_correlate', False)) else {})
            self._gpu.correlate(self.n, self._gdata[d0:d0 + nd],
                                self._gtmpl[t0:t0 + nt], result,
                                upload_data=self._ddirty,
                                upload_tmpl=self._tdirty, **kw)
            self._ddirty = self._tdirty = False
        if scales is not None:
            sc = np.ascontiguousarray(_from_any(scales), dtype=np.float32)
            if sc.ndim != 1 or sc.size != nt:
                raise ValueError(f"scales must be a 1D array of length {nt}, got shape {sc.shape}")
            np.multiply(result, sc[None, :, None], out=result)
        return result

    def run_series(self, series, starts=None, templates=None, out=None, scales=None):
        """Correlate a series into continuous output over the configured valid window.

        With explicit ``starts``, preserve the block-major full-output form.
        """
        ser = np.ascontiguousarray(_from_any(series), dtype=np.complex64)
        if ser.ndim != 1:
            raise ValueError("series must be one-dimensional")
        if starts is None:
            if out is not None:
                raise ValueError('automatic run_series owns its output; omit out')
            st, _, _ = _automatic_series_layout(ser.size, self.valid)
            t0, nt = (0, self.ntemplates) if templates is None else (
                int(templates[0]), int(templates[1]))
            if nt < 1 or t0 < 0 or t0 + nt > self.ntemplates:
                raise ValueError("templates sub-range out of bounds")
            self._require_templates(t0, nt)
            shape = (nt, ser.size)
            result = getattr(self, '_continuous_output', None)
            if result is None or result.shape != shape:
                nbytes = math.prod(shape) * np.dtype(np.complex64).itemsize
                if nbytes > self._max_auto_output_bytes:
                    raise ValueError("continuous correlation needs %d bytes of output; "
                                     "select fewer templates or a shorter series" % nbytes)
                result = (self._gpu.empty_shared(shape, readback=True)
                          if self._gpu is not None else self.empty_shared(shape))
                result[:, :self.valid[0]] = 0
                self._continuous_output = result
            self._dataset = False
            self._data_ready = set()
            if self._gpu is not None:
                self._continuous_gpu(ser, st, t0, nt, result)
            else:
                self._continuous_plan().correlate_series_continuous(
                    ser, st, self.valid[0], self.valid[1], t0, nt, result)
            if scales is not None:
                sc = np.ascontiguousarray(_from_any(scales), dtype=np.float32)
                if sc.ndim != 1 or sc.size != nt:
                    raise ValueError(f"scales must be a 1D array of length {nt}, got shape {sc.shape}")
                np.multiply(result, sc[:, None], out=result)
            return result
        st = np.ascontiguousarray(_from_any(starts), dtype=np.uintp)
        if st.ndim != 1 or st.size < 1:
            raise ValueError("starts must be a nonempty one-dimensional array")
        if np.any(st > np.iinfo(np.intp).max - self.n):
            raise ValueError("starts must be nonnegative and fit the sample index range")
        t0, nt = (0, self.ntemplates) if templates is None else (int(templates[0]), int(templates[1]))
        if nt < 1 or t0 < 0 or t0 + nt > self.ntemplates:
            raise ValueError("templates sub-range out of bounds")
        self._require_templates(t0, nt)
        if self._gpu is not None and ser.size > np.iinfo(np.uint32).max:
            raise ValueError("GPU series exceeds the 32-bit sample address range")
        result = self._full_output((st.size, nt, self.n), out)
        self._dataset = False
        self._data_ready = set()
        if self._gpu is None:
            self._execution_plan().correlate_series(ser, st, t0, nt, result)
        else:
            from ._shared import shared_buffer
            source = ser if shared_buffer(ser, self._gpu) is not None else self.empty_shared(ser.shape)
            if source is not ser:
                source[:] = ser
            budget = getattr(self, "_series_batch_bytes", 64 * 1024 * 1024)
            batch = max(1, min(st.size, self._gpu_pair_limit() // nt,
                               budget // max(8 * self.n * (1 + nt), 1)))
            spec = self.empty_shared((batch, self.n))
            offsets = self.empty_shared(batch, np.uint32)
            for b0 in range(0, st.size, batch):
                b1 = min(b0 + batch, st.size)
                count = b1 - b0
                offsets[:count] = np.minimum(st[b0:b1], ser.size)
                self._gpu.forward(self.n, source, offsets[:count], spec[:count], defer=True)
                try:
                    self._gpu.correlate(self.n, spec[:count], self._gtmpl[t0:t0 + nt],
                                        result[b0:b1], upload_data=True,
                                        upload_tmpl=self._tdirty)
                finally:
                    self._gpu.cancel_forward()
                self._tdirty = False
        if scales is not None:
            sc = np.ascontiguousarray(_from_any(scales), dtype=np.float32)
            if sc.ndim != 1 or sc.size != nt:
                raise ValueError(f"scales must be a 1D array of length {nt}, got shape {sc.shape}")
            np.multiply(result, sc[None, :, None], out=result)
        return result

    def run_blocks(self, series, starts, templates=None, out=None):
        """Return every lag for explicit blocks as ``(blocks, templates, n)``.

        Unlike ``run_series(series)``, this form has block-major output and
        accepts a caller-owned ``out`` buffer for reuse.
        """
        return self.run_series(series, starts, templates=templates, out=out)




def include_dir():
    """Directory holding matchedfilter.h, for building C code against this package.

    Direct C use is not the main path - the Python class is - but linking is
    cheap to support::

        cc myprog.c $(python -c "import matchedfilter; print('-I'+matchedfilter.include_dir())") ...

    The C interface is the same ten functions the class wraps; see matchedfilter.h.
    """
    import os
    return os.path.dirname(os.path.abspath(__file__))



def _uncovered_message(n, snr, fd):
    return (
        f"no gate chain for n={n} snr={snr:.2f} fd={fd:.0e}: the gate model cannot resolve "
        "the false-dismissal budget for this reference profile. Provide a reference with a "
        "localised correlation peak, or pin a chain and set its thresholds explicitly."
    )


def _band_features(power, m):
    """(in-band fraction, effective bandwidth in bins) at band m."""
    p = np.asarray(power, dtype=np.float64)
    p = np.where(p > 0, p, 0.0)
    tot = p.sum()
    if tot <= 0:
        return 0.0, 1.0
    inb = p[:m]
    s = inb.sum()
    if s <= 0:
        return 0.0, 1.0
    q = inb / s
    return float(s / tot), float(1.0 / np.sum(q ** 2))


# References without a localised correlation peak are outside automatic selection.
_BEFF_MIN = 8.0


def _uncovered_reference(power, n):
    """True when no candidate band has a localised peak to work with.

    A reference whose in-band power sits in a bin or two gives a correlation
    of nearly constant magnitude -- there is no peak to find coarsely and
    refine, so the hierarchical method does not apply. See `_BEFF_MIN`.
    """
    bands = _gatechain.candidate_bands(n)
    return bool(bands) and all(_band_features(power, b)[1] < _BEFF_MIN for b in bands)


def choose_threshold(power, n, snr, fd, band):
    """The single-tier gate at `band` for this reference and budget (gatemodel.gate_for)."""
    from .gatemodel import gate_for
    return gate_for(power, n, int(band), snr, fd)


def _normalize_chain(chain, n):
    """A chain as a tuple of strictly increasing power-of-two bands in [64, n)."""
    if isinstance(chain, (int, np.integer)):
        chain = (int(chain),)
    chain = tuple(int(b) for b in chain)
    if not chain:
        raise ValueError("a chain needs at least one band")
    for i, b in enumerate(chain):
        if b < 64 or b >= n or b & (b - 1):
            raise ValueError("chain bands must be powers of two, >= 64 and < n; got %s" % (chain,))
        if i and b <= chain[i - 1]:
            raise ValueError("chain bands must be strictly increasing; got %s" % (chain,))
    return chain


_Q15_BANDS = {}


def _q15_available(band):
    """Whether this machine's back end has a Q15 screen for a first tier at `band`."""
    band = int(band)
    if band not in _Q15_BANDS:
        try:
            _Q15_BANDS[band] = _core.MF(band, 1, 1).q15_lanes() > 0
        except (ValueError, AttributeError):
            _Q15_BANDS[band] = False
    return _Q15_BANDS[band]


_AUTOTUNE_LOCK = threading.Lock()


def _chain_lock_key(tkey):
    n, snr, fd, tiers, device = tkey[:5]
    # tkey[5]: present (1) when the direct refine is priced in, which changes what refining
    # costs and so which chain wins (HierarchicalFilter._chain_trial_key).
    direct = tkey[5] if len(tkey) > 5 else None
    return "chain-trial|%d|%g|%g|%d|%s" % (n, snr, fd, tiers, device) + (
        "|direct" if direct is not None else "")


def _stored_chain_lock(tkey, feasible):
    """A chain-trial winner kept in MF_COST_FILE by an earlier process, if this plan can run it
    (`feasible`: every chain the gate model covers for it). Deliberately NOT only when it is
    on this process's shortlist: the lock key is the trial's identity, and in-process every
    plan with the key adopts the winner whatever its own shortlist -- the shortlist is a
    per-process pruning of what to measure (the model's best few for this group's shape),
    not of what is valid. Filtered by it, a group whose shortlist missed the winner ignored
    the lock and the chain varied between processes. Chain trials, like block-size trials (time_domain._BlockTrials) and the cost
    models themselves, are per machine: re-run in every process they lock differently on noise,
    and that was the remaining process-to-process variation of a pinned layout
    (docs/gate-model.md, "Block-size trials, round 3")."""
    path = _gatechain._cost_file()
    if path is None:
        return None
    rec = _gatechain._load_cost_file(path).get(_chain_lock_key(tkey))
    if not isinstance(rec, dict):
        return None
    chain = tuple(int(b) for b in rec.get("chain", ()))
    if not chain:
        return None
    if feasible is None:
        return chain                 # the key's lock, whichever plan asks (see _choose_chain)
    return chain if chain in tuple(tuple(c) for c in feasible) else None


def _chain_trial_next(tkey):
    """The candidate a GPU chain trial's next batch runs on every plan of the trial: the one
    with fewest batch samples, in shortlist order. None once the trial has a winner."""
    with _AUTOTUNE_LOCK:
        tr = _CHAIN_TRIALS.get(tkey)
        if tr is None or tr["winner"] is not None:
            return None
        if "batch" not in tr:
            tr["batch"] = {c: [] for c in tr["samples"]}
            path = _gatechain._cost_file()
            rec = (_gatechain._load_cost_file(path).get(_chain_lock_key(tkey) + "|batches")
                   if path is not None else None)
            if isinstance(rec, dict) and isinstance(rec.get("samples"), dict):
                for k, v in rec["samples"].items():
                    c = tuple(int(b) for b in k.split(",") if b)
                    if c in tr["batch"]:            # still a candidate here
                        tr["batch"][c] = [float(x) for x in v]
                for k, v in (rec.get("need") or {}).items():
                    c = tuple(int(b) for b in k.split(",") if b)
                    tr.setdefault("batch_need", {})[c] = int(v)
                tr["batches"] = int(rec.get("batches", 0))
                tr["dropped"] = {tuple(int(b) for b in k.split(",") if b)
                                 for k in rec.get("dropped", ())}
        bs = tr["batch"]
        dropped = tr.setdefault("dropped", set())
        for c in tr["samples"]:
            if c not in dropped:
                bs.setdefault(c, [])
        # Candidates in turn, each for a run of batches: a switch rebuilds thresholds and
        # uploads (the batch after it is not a sample), so alternating every batch measured
        # mostly the switching -- cheapest for the chain with fewest tiers.
        base = int(os.environ.get("MF_CHAIN_TRIALS", _CHAIN_BATCH_TRIALS))
        bneed = tr.setdefault("batch_need", {})
        needs = {c: max(base, bneed.get(c, 0)) for c in bs}
        # Samples taken plus batches in flight that will be (a caller keeping batches in
        # flight records them later than the next batch starts).
        pend = tr.setdefault("batch_pending", {})
        have = {c: len(bs[c]) + pend.get(c, 0) for c in bs}
        cur = tr.get("batch_current")
        from .time_domain import _CHAIN_WARM_BATCHES as warm
        # A candidate current for longer than its warm-up and samples (+2) without yielding
        # one cannot or will not run here (a plan that does not switch to it, batches never
        # recorded): it leaves the contest instead of being waited for.
        if cur is not None and cur in bs:
            run, got0 = tr.get("cur_run", (0, len(bs[cur])))
            if len(bs[cur]) == got0 and run > warm + needs[cur] + 2:
                bs.pop(cur)
                dropped.add(cur)
                _log_autotune("CHAIN-TRIAL %s: %s yielded no sample in %d batches: dropped",
                              tkey, cur, run)
                cur = None
        tr["batches"] = tr.get("batches", 0) + 1
        # Budget backstop: a bounded number of batches in all, then the shared rule decides
        # among what was measured (_trial_budget_choice).
        if tr["batches"] > len(tr["samples"]) * (warm + base) + 6 or not bs:
            w = _trial_budget_choice(bs, next(iter(tr["samples"])), 2)
            if w is not None:
                med = {c: float(np.median(v)) for c, v in bs.items() if len(v)}
                _chain_lock(tkey, tr, w, med)
                _log_autotune("CHAIN-TRIAL %s budget of batches spent: locked %s", tkey, w)
                return None
        if cur is not None and cur in bs and (have[cur] < needs[cur]
                                              or all(have[c] >= needs[c] for c in bs)):
            r, g = tr.get("cur_run", (0, len(bs[cur])))
            tr["cur_run"] = (r + 1, g)
            return cur          # (all sampled, the last samples still in flight: no switch)
        if not bs:
            return None
        cur = tr["batch_current"] = min(bs, key=lambda c: (have[c] >= needs[c], have[c],
                                                          list(tr["samples"]).index(c)))
        tr["cur_run"] = (1, len(bs[cur]))
        return cur


def _chain_trial_pending(tkey, chain, delta):
    """A settled batch of a GPU chain trial started (+1) or finished (-1) on chain."""
    with _AUTOTUNE_LOCK:
        tr = _CHAIN_TRIALS.get(tkey)
        if tr is not None:
            pend = tr.setdefault("batch_pending", {})
            pend[tuple(chain)] = pend.get(tuple(chain), 0) + delta


def _chain_trial_batch(tkey, chain, value):
    """One sample of a GPU chain trial: a whole batch (every job of a segment, submission to
    last result) per unit of work, with every plan of the trial on `chain`. Judged on what a
    search pays -- host and device, readback, everything the chain changes -- not on one
    call's time per pair. Decides by the shared rule (gatechain.measured_choice) once every
    candidate still in the contest has MF_CHAIN_TRIALS samples; _chain_trial_next drops a
    candidate that yields none and bounds the trial in batches."""
    with _AUTOTUNE_LOCK:
        tr = _CHAIN_TRIALS.get(tkey)
        if tr is None or tr["winner"] is not None:
            return None if tr is None else tr["winner"]
        bs = tr.setdefault("batch", {c: [] for c in tr["samples"]})
        if tuple(chain) in tr.get("dropped", ()):
            return None                     # left the contest (_chain_trial_next)
        bs.setdefault(tuple(chain), []).append(float(value))
        _log_autotune("CHAIN-TRIAL batch sample %s %.3g", tuple(chain), value)
        base = int(os.environ.get("MF_CHAIN_TRIALS", _CHAIN_BATCH_TRIALS))
        bneed = tr.setdefault("batch_need", {})
        done = all(len(v) >= max(base, bneed.get(c, 0)) for c, v in bs.items())
        if done:
            # The shared rule (gatechain.measured_choice): the model's chain (the shortlist's
            # first) stands unless another is clearly faster, past TIE and the noise.
            w, more = _gatechain.measured_choice(bs, next(iter(tr["samples"])), 2 * base)
            if w is None:
                bneed.update(more)
                done = False
                _log_autotune("CHAIN-TRIAL (batches) unclear, sampling further %s", more)
        if not done and sum(len(v) for v in bs.values()) >= _TRIAL_BUDGET * base * len(bs):
            w = _trial_budget_choice(bs, next(iter(tr["samples"])), base)
            if w is not None:
                done = True
                _log_autotune("CHAIN-TRIAL (batches) budget spent: deciding on %s",
                              [c for c, v in bs.items() if len(v) >= base])
        if not done:
            # Unfinished: kept in MF_COST_FILE, so a shorter process than the trial
            # continues it in the next (as block-size trials do).
            path = _gatechain._cost_file()
            if path is not None:
                _gatechain._store_cost(path, _chain_lock_key(tkey) + "|batches",
                                       {"samples": {_chain_str(c): v for c, v in bs.items()},
                                        "need": {_chain_str(c): v for c, v in bneed.items()},
                                        "batches": int(tr.get("batches", 0)),
                                        "dropped": [_chain_str(c) for c in tr.get("dropped", ())]})
        else:
            med = {c: float(np.median(v)) for c, v in bs.items() if len(v)}
            _chain_lock(tkey, tr, w, med)
            _log_autotune("CHAIN-TRIAL (batches) locked %s  median s/unit %s", tr["winner"],
                          {c: "%.3g" % v for c, v in med.items()})
        return tr["winner"]


#: A trial that has taken this many times its per-candidate samples in total without locking
#: decides among the candidates it measured (_trial_budget_choice): candidates some live plan
#: never runs -- another process's shortlist, a group that stopped calling -- must not keep a
#: trial open for good (a partial "|batches" record with two empty candidates never finished).
_TRIAL_BUDGET = 3


def _trial_budget_choice(samples, model, base):
    """The shared rule over the candidates with at least `base` samples (model first); None
    while none has."""
    sub = {c: v for c, v in samples.items() if len(v) >= base}
    if not sub:
        return None
    w, _ = _gatechain.measured_choice(sub, model if model in sub else next(iter(sub)), 0)
    return w


def _chain_str(c):
    return ",".join(str(int(b)) for b in c)


def _store_chain_lock(tkey, chain, median=None, rechecked=False):
    path = _gatechain._cost_file()
    if path is not None and tkey is not None:
        rec = {"chain": [int(b) for b in chain], "rechecked": bool(rechecked)}
        if median:
            rec["median"] = {_chain_str(c): float(v) for c, v in median.items()}
        _gatechain._store_cost(path, _chain_lock_key(tkey), rec)


def _chain_lock_state(tkey):
    """(trial medians {chain: s/unit}, rechecked) of the lock on file, for the re-check."""
    path = _gatechain._cost_file()
    rec = _gatechain._load_cost_file(path).get(_chain_lock_key(tkey)) if path else None
    if not isinstance(rec, dict):
        return None, False
    med = rec.get("median")
    med = ({tuple(int(b) for b in k.split(",") if b): float(v) for k, v in med.items()}
           if isinstance(med, dict) else None)
    return med, bool(rec.get("rechecked"))


def _chain_lock(tkey, tr, winner, median):
    """Lock a chain trial (caller holds _AUTOTUNE_LOCK): winner, the medians the re-check
    compares steady state with, and the lock on file."""
    tr["winner"], tr["median"] = tuple(winner), dict(median)
    _store_chain_lock(tkey, tr["winner"], median, tr.get("rechecked", False))


def _chain_steady(tkey, value):
    """A steady-state sample (s/unit, the trial's own unit) of a locked chain trial: reopens
    the lock on file -- the next process trials again -- when steady state contradicts the
    trial, once per key (gatechain.observe_steady)."""
    with _AUTOTUNE_LOCK:
        tr = _CHAIN_TRIALS.get(tkey)
        if tr is None:
            return False

        def reopen():
            path = _gatechain._cost_file()
            if path is not None:
                _gatechain._store_cost(path, _chain_lock_key(tkey),
                                       {"rechecked": True,
                                        "reopened": {"chain": _chain_str(tr["winner"]),
                                                     "steady": float(np.median(tr["steady"][-5:]))}})
                _gatechain._store_cost(path, _chain_lock_key(tkey) + "|batches", {"samples": {}})
            _log_autotune("CHAIN-TRIAL %s steady state contradicts the trial: reopened", tkey)
        return _gatechain.observe_steady(tr, value, reopen)
#: n -> whether continuous correlation at n runs through the platform FFT (vDSP on macOS):
#: set by time_domain._corr_block_costs, which prices both and keeps the cheaper.
_CORR_PFFT = {}
#: (n, snr, fd, chain, device) -> {"samples": {False: [...], True: [...]}, "winner": bool|None}
_Q15_TRIALS = {}
# Cumulative host calibration work, for benchmark boundaries (not search timing).
_CPU_TRIAL_WORK = {"calls": 0, "seconds": 0.0}


def _record_cpu_trial(start):
    _CPU_TRIAL_WORK["calls"] += 1
    _CPU_TRIAL_WORK["seconds"] += time.perf_counter() - start
#: n -> whether the hierarchical series' block forward runs through the platform FFT
#: (vDSP on macOS): priced once per n (_cpu_forward_platform), kept in MF_COST_FILE.
_CPU_FWD_PFFT = {}


_Q15_TIER0 = {}


def _q15_tier0_fp16(band):
    """Whether tier 0 behind the Q15 screen runs on the FP16 gate at this band: both kernels
    are timed once on a synthetic survivor list (_core.price_q15_tier0) and the cheaper is
    kept ("q15-tier0|band" in MF_COST_FILE). The FP16 gate reports an upper bound on the
    FP32 magnitude, so its survivors are a superset of the FP32 pass's and the next tier and
    the refine decide them; only time is at stake, and a whole-call trial of a tier ~10% of
    a call sits at the shared rule's tie (gatechain.measured_choice), so it is priced."""
    band = int(band)
    hit = _Q15_TIER0.get(band)
    if hit is not None:
        return hit
    if not getattr(_core, "gate16", lambda: False)():
        _Q15_TIER0[band] = False
        return False
    path = _gatechain._cost_file()
    key = "q15-tier0|%d" % band
    if path is not None:
        rec = _gatechain._load_cost_file(path).get(key)
        if isinstance(rec, dict) and "fp16" in rec:
            _Q15_TIER0[band] = hit = bool(rec["fp16"])
            return hit
    try:
        fp32, fp16 = _core.price_q15_tier0(band, 128)
    except Exception:                      # noqa: BLE001 -- no price: keep the FP32 pass
        fp32, fp16 = 1.0, -1.0
    hit = bool(fp16 > 0 and fp16 < fp32)
    _Q15_TIER0[band] = hit
    if path is not None:
        _gatechain._store_cost(path, key, {"fp16": hit, "ticks": {"fp32": fp32, "fp16": fp16}})
    return hit


def _cpu_forward_platform(n):
    """Whether the block forward at n is cheaper through the platform FFT. Both transforms
    are timed once on this size (_core.forward_cost: copy with 1/n and transform, best of a
    few repetitions) and the cheaper is kept ("cpu-fft|n|cpu" in MF_COST_FILE). Their
    results differ by fp32 rounding only, so this is a price, not a contest: a trial over
    whole calls dilutes a transform that is ~11% of a call below the shared tie margin
    (gatechain.measured_choice), which kept the slower transform in half of fresh files."""
    n = int(n)
    hit = _CPU_FWD_PFFT.get(n)
    if hit is not None:
        return hit
    path = _gatechain._cost_file()
    key = "cpu-fft|%d|cpu" % n
    if path is not None:
        rec = _gatechain._load_cost_file(path).get(key)
        if isinstance(rec, dict) and "platform" in rec:
            _CPU_FWD_PFFT[n] = hit = bool(rec["platform"])
            return hit
    native, platform = _core.forward_cost(n)
    hit = bool(platform > 0 and platform < native)
    _CPU_FWD_PFFT[n] = hit
    if path is not None:
        _gatechain._store_cost(path, key, {"platform": hit, "seconds": {"engine": native,
                                                                        "platform": platform}})
    return hit
#: (chain-choice key, chain) -> whether the cost model prices the Q15 screen cheaper
_Q15_MODEL = {}
#: (n, snr, fd, tiers, window, profile signature) -> (model's chain, shortlist)
_CHAIN_CHOICE = {}
#: (n, snr, fd, tiers, shortlist) -> measured trials shared by every plan with that shortlist
_CHAIN_TRIALS = {}
#: Relative cost margin inside which modelled chains are measured rather than decided by the
#: model. It is the model's demonstrated error: tier costs agreed with the engine counters to
#: ~25% in the consumer.
_CHAIN_MARGIN = 0.30
_CHAIN_SHORTLIST_MAX = 4
#: GPU chain trials measure the model's best three, each over whole batches (see _choose).
_CHAIN_SHORTLIST_GPU = 3
_CHAIN_TRIALS_PER_CAND = 6
#: Batch samples per candidate of a GPU chain trial (a batch is a whole segment's jobs; its
#: first batch on a candidate builds recordings and is not counted).
_CHAIN_BATCH_TRIALS = 4


def _log_autotune(msg, *args):
    if os.environ.get("MF_AUTOTUNE_LOG", "0") != "0":
        text = msg % args if args else msg
        print(f"[MF_AUTOTUNE] {text}", file=sys.stderr, flush=True)


def _autotune_enabled():
    """MF_AUTOTUNE=0 keeps the model's choice (deterministic); otherwise close calls are measured."""
    return os.environ.get("MF_AUTOTUNE", "1").strip().lower() not in ("0", "false", "no", "off")


def get_autotune_state():
    """Snapshot of the process's chain choices and measured trials."""
    with _AUTOTUNE_LOCK:
        return {"choices": dict(_CHAIN_CHOICE),
                "trials": {k: {"winner": v["winner"], "samples": {c: list(s) for c, s in v["samples"].items()}}
                           for k, v in _CHAIN_TRIALS.items()}}


def clear_autotune_cache():
    """Forget every chain choice and trial in this process."""
    with _AUTOTUNE_LOCK:
        _CHAIN_CHOICE.clear()
        _CHAIN_TRIALS.clear()
        _Q15_TRIALS.clear()
        _CPU_FWD_PFFT.clear()
        _Q15_TIER0.clear()




def _direct_refine_enabled():
    return os.environ.get("MF_DIRECT_REFINE", "1") != "0"


def _direct_lagtap():
    """Ticks per lag x tap of the direct refine on this machine: timed once and kept in
    MF_COST_FILE, so every process sharing the file prices chains alike (the chain choice
    depends on it)."""
    key = "direct-lagtap|%s|%s" % (_core.backend() if hasattr(_core, "backend") else "", _gatechain.cpu_gate_kind())
    held = _gatechain.stored_choice(key)
    if isinstance(held, (int, float)) and held > 0:
        return float(held)
    v = float(_core.price_direct())
    if v > 0:
        _gatechain.store_choice(key, v)
    return v


class HierarchicalFilter(MatchedFilter):
    """Matched filter that gates on cheap coarse correlations and refines on demand.

    Most of a template's SNR sits in the low part of its band. A gate chain
    correlates only low bands -- tier 0 at band b1 on every pair, tier i at
    band b_i on the survivors of tier i-1 -- and pays for the full correlation
    only for pairs that pass every tier.

        >>> hf = matchedfilter.HierarchicalFilter(1 << 12, ndata=16, ntemplates=16,
        ...                                       snr=5.5, fd=1e-2)
        >>> hf.set_reference(profile)          # expected output power per bin
        >>> hf.set_data(data_spectra)
        >>> hf.set_templates(template_spectra)
        >>> peaks = hf.run(binsize=1024, threshold=t)
        >>> hf.config, hf.refine_rate          # the chain in use, fraction refined

    Surviving pairs normally receive a full correlation and binned peak search;
    equivalent transform paths can differ by floating-point rounding. With
    :meth:`set_taps`, direct refinement can instead search near the last coarse
    candidate for a single-bin result. With several excursions this can return
    a smaller local maximum than the whole-bin search. ``MF_DIRECT_REFINE=0``
    disables that approximation. The gate can omit peaks; ``fd`` is its modelled
    false-dismissal target at strength ``snr``, shared between the chain's tiers.
    Use :class:`MatchedFilter` for an ungated full-bin search.

    The chain is chosen automatically from the reference: every chain of up to
    ``max_tiers`` bands is priced by a model (gate thresholds from the profile,
    noise pass rates simulated from it, tier costs calibrated on this machine),
    and the ones the model cannot separate are measured on the real workload
    (``MF_AUTOTUNE=0`` keeps the model's choice). Pin a chain with
    ``chain=(b1, b2, ...)``; pass explicit thresholds with
    :meth:`set_coarse_threshold` to skip the model entirely.
    """

    #: Tiers each device's engine executes.
    _MAX_TIERS = {"cpu": 8, "gpu": 2}

    def __init__(self, n, ndata=1, ntemplates=1, snr=5.5, fd=1e-2, chain=None,
                 device=None, *, valid=None, max_tiers=3, search_window=None):
        from .device import parse as _parse_device
        self.device = _parse_device(device)
        self.n = int(n)
        self.valid = _valid_series_window(self.n, valid)
        self.ndata = int(ndata)
        self.ntemplates = int(ntemplates)
        if self.ndata < 1 or self.ntemplates < 1:
            raise ValueError("ndata and ntemplates must be >= 1")
        if self.device.kind == 'cpu' and self.n > self._cpu_max_n:
            raise ValueError("CPU transform size %d exceeds this filter's limit of %d"
                             % (self.n, self._cpu_max_n))
        self.snr = float(snr)
        self.fd = float(fd)
        self.max_tiers = int(max_tiers)
        if self.max_tiers < 1:
            raise ValueError("max_tiers must be >= 1")
        #: Lags each block's peak search covers, (start, end) in samples; prices noise passes.
        self.search_window = None if search_window is None else (int(search_window[0]), int(search_window[1]))
        self._init_state()
        self._pending_ref = None
        self._cal_thr = None           # explicit per-tier thresholds, bypassing the model
        self._thr_applied = False
        self._fs_snr = None
        self._hermitian = False
        self._mf = None
        self._chain_trial = None
        self._q15 = False
        self._pinned = None if chain is None else _normalize_chain(chain, self.n)
        if self._pinned is not None and len(self._pinned) > self._MAX_TIERS[self.device.kind]:
            raise ValueError("this device executes chains of at most %d tiers"
                             % self._MAX_TIERS[self.device.kind])
        self._chain = self._pinned
        self.autotune_info = {"status": "pinned" if self._pinned else "uninitialized",
                              "winner": self._pinned, "shortlist": ()}
        if self.device.kind == "gpu":
            self._start_gpu()
            return
        if self._pinned is not None:
            self._mf = self._new_cpu_plan(self._pinned)

    # ---- plan --------------------------------------------------------------
    def _reads_real_series(self):
        """Whether run_series reads a real (float32) series as it is: the CPU plan
        transforms it at half size; a GPU forward declaring real_series reads its samples
        (one-stage forwards only, n <= 65536). Elsewhere a real series is widened."""
        if self._gpu is None:
            return self.device.kind == "cpu" and self.n >= 4
        return self.n <= 65536

    def _new_cpu_plan(self, chain):
        self._execution_policy = self._series_policy('hierarchical_series', chain[-1], self.ntemplates)
        grp = self._execution_policy.get('series_group', 32 if self.n <= 2048 else 16)
        plan = _core.HMF(self.n, self.ndata, self.ntemplates, list(chain), grp,
                         int(getattr(self, 'k', self.n) or self.n))
        if self._hermitian:
            plan.set_hermitian(True)
        if getattr(self, "_q15", False) and not plan.set_q15(True):
            self._q15 = False
        # The block forward's transform: a cost-model price (_cpu_forward_platform), not a
        # trial -- its effect is under the shared rule's tie margin of a whole call.
        self._pfft = _cpu_forward_platform(self.n) and plan.set_platform_fft(True)
        # Tier 0 behind the Q15 screen: the FP16 gate over the screen's survivors where it is
        # priced cheaper than the pooled FP32 pass (_q15_tier0_fp16).
        plan.set_q15_tier0(_q15_tier0_fp16(int(chain[0])))
        taps = getattr(self, "_taps", None)
        if taps is not None:
            plan.set_taps(taps[0], taps[0].shape[1], taps[1])   # direct: with the thresholds
        return plan

    # ---- Q15 screen: a measured candidate, never a default ---------------------
    # The screen in front of the first tier (docs/cpu-q15-gate.md) changes no result -- the
    # float tier re-runs every pair it passes -- so only time is at stake, and time is
    # measured: plans whose chain's first band has a screen alternate it on and off over
    # identical-input pairs, pooled per (n, snr, fd, chain). Complete rounds persist
    # across processes; every plan adopts the paired trial's winner. MF_AUTOTUNE=0 keeps the cost model's choice
    # (gatechain.CostModel.first_tier).
    def _q15_trial_key(self):
        return (self.n, float(self._fs_snr or self.snr), float(self.fd), tuple(self._chain), str(self.device))

    @staticmethod
    def _q15_lock_key(tkey):
        n, snr, fd, chain, device = tkey
        return "q15-trial|%d|%g|%g|%s|%s" % (n, snr, fd, ",".join(str(int(b)) for b in chain), device)

    def _q15_trial(self):
        """This plan's Q15 trial (caller holds _AUTOTUNE_LOCK), adopting a winner an earlier
        process kept in MF_COST_FILE: per machine, like chain and block-size locks, so a
        process does not re-alternate the screen on its first calls -- which would also keep
        every block-size trial from sampling (time_domain._bank_calibrating)."""
        tkey = self._q15_trial_key()
        tr = _Q15_TRIALS.get(tkey)
        if tr is None:
            tr = _Q15_TRIALS[tkey] = {"samples": {False: [], True: []}, "winner": None}
            path = _gatechain._cost_file()
            if path is not None:
                rec = _gatechain._load_cost_file(path).get(self._q15_lock_key(tkey))
                if isinstance(rec, dict):
                    tr["rechecked"] = bool(rec.get("rechecked"))
                    if rec.get("method") == "paired-v1" and "q15" not in rec:
                        smp = rec.get("samples", {})
                        a, b = smp.get("False", []), smp.get("True", [])
                        if len(a) == len(b) and all(np.isfinite(x) and x > 0 for x in a + b):
                            tr["samples"] = {False: a, True: b}
                    if "q15" in rec:
                        tr["winner"] = bool(rec["q15"])
                        m = rec.get("median")
                        if isinstance(m, dict):
                            tr["median"] = {k == "True": float(v) for k, v in m.items()}
        return tr

    def _q15_before_call(self):
        """Pick the screen setting for this call; True when the call is a timed sample."""
        if (self.device.kind != "cpu" or self._mf is None or self._chain is None
                or not _autotune_enabled() or not _q15_available(self._chain[0])
                or getattr(self, "_trial_hold", False)):
            return False
        with _AUTOTUNE_LOCK:
            tr = self._q15_trial()
            win = tr["winner"]
            want = win if win is not None else len(tr["samples"][True]) < len(tr["samples"][False])
        if bool(want) != bool(self._q15):
            self._q15 = bool(want) and self._mf.set_q15(True)
            if not want:
                self._mf.set_q15(False)
        return win is None

    def calibrating(self):
        """Whether this plan is still settling a measured choice -- its chain trial, or the Q15
        screen trial of its chain -- so that its calls alternate kernels. A block-size trial
        does not sample batches while any of its plans is (time_domain._bank_calibrating).
        A plan not built yet is not calibrating (its first batch is the trial's settle batch),
        and a held plan (block-size trial open) runs no trial at all."""
        if self._chain is None or getattr(self, "_trial_hold", False):
            return False
        if self._chain_trial is not None:
            return True
        if (self.device.kind == "cpu" and self._mf is not None and _autotune_enabled()
                and _q15_available(self._chain[0])):
            with _AUTOTUNE_LOCK:
                tr = self._q15_trial()
            return tr["winner"] is None
        return False

    def _q15_record_pair(self, timings, pairs):
        """Persist only complete same-input rounds, never unrelated per-call samples."""
        with _AUTOTUNE_LOCK:
            tr = self._q15_trial()
            if tr["winner"] is not None or pairs <= 0:
                return
            if not all(np.isfinite(timings[c]) and timings[c] > 0 for c in (False, True)):
                return
            for c in (False, True):
                tr["samples"][c].append(timings[c] / pairs)
            base = max(5, int(os.environ.get("MF_CHAIN_TRIALS", _CHAIN_TRIALS_PER_CAND)))
            model = bool(getattr(self, "_q15_pref", False))
            w, _ = _gatechain.paired_choice(tr["samples"], model, 2 * base, minimum=base)
            med = {c: float(np.median(v)) for c, v in tr["samples"].items()}
            record = {"method": "paired-v1", "samples": {str(c): v for c, v in tr["samples"].items()},
                      "median": {str(c): v for c, v in med.items()},
                      "rechecked": bool(tr.get("rechecked"))}
            if w is not None:
                tr["winner"], tr["median"] = bool(w), med
                record["q15"] = bool(w)
            path = _gatechain._cost_file()
            if path is not None:
                _gatechain._store_cost(path, self._q15_lock_key(self._q15_trial_key()), record)
            _log_autotune("Q15-TRIAL paired chain=%s round=%d winner=%s timings=%s", self._chain,
                          len(tr["samples"][False]), tr["winner"], timings)

    def _q15_run_pair(self, run, pairs):
        """Two settled timings on identical input; alternate which setting runs first.

        Replays are calibration work, included in native work counters. Return only
        the final call's result, whose buffers have not been overwritten by a replay.
        """
        begin = time.perf_counter()
        with _AUTOTUNE_LOCK:
            count = len(self._q15_trial()["samples"][False])
        timings = {}
        for on in ((False, True) if count % 2 == 0 else (True, False)):
            self._q15 = on
            self._mf.set_q15(on)
            run()                           # settle switching and lazy ingestion
            t0 = time.perf_counter()
            result = run()
            timings[on] = time.perf_counter() - t0
        self._q15_record_pair(timings, pairs)
        _record_cpu_trial(begin)
        return result

    def _load_held_templates(self, plan):
        """Load into plan the templates this filter was given: from its template source, or
        the copy it holds."""
        t = self._held_templates
        if t is None and getattr(self, "_template_source", None) is not None:
            t = np.ascontiguousarray(self._template_source(), dtype=np.complex64)
        if isinstance(t, np.ndarray):
            plan.set_template_batch(0, t)
        elif isinstance(t, list):
            for i, x in enumerate(t):
                if x is not None:
                    plan.set_template(i, x)

    def _restore_into(self, plan):
        """Replay reference, templates and data into a freshly built plan."""
        if self._pending_ref is not None:
            plan.set_reference(self._pending_ref)
        self._load_held_templates(plan)
        if self._held:
            if -1 in self._held:
                plan.set_data_batch(0, self._held[-1])
            else:
                for i, d in self._held.items():
                    if d is not None and i >= 0:
                        plan.set_data(i, d)

    def _ensure(self):
        """The live plan, built on first use once the chain is known."""
        if self._mf is not None:
            return self._mf
        if self._chain is None:
            if self._pending_ref is None:
                raise ValueError("set a reference first (set_reference), or pin a chain")
            self._chain = self._choose_chain(); self._q15 = getattr(self, "_q15_pref", False)
        self._mf = self._new_cpu_plan(self._chain)
        self._thr_applied = False
        self._restore_into(self._mf)
        return self._mf

    def _execution_plan(self):
        plan = self._ensure()
        if not self._thr_applied:
            thr = list(self._thresholds(required=True))
            plan.set_thresholds(thr)
            self._q15_order_choice = None
            if (self.device.kind == 'cpu' and self._pending_ref is not None
                    and len(self._chain) >= 2):
                self._q15_order_choice = _gatechain.q15_recheck_order(
                    self._pending_ref, self.n, self._chain, thr, self._cost_model(),
                    window=self.search_window)
            plan.set_q15_recheck_late(bool(self._q15_order_choice
                                          and self._q15_order_choice['late']))
            if getattr(self, "_taps", None) is not None:
                hw = self._direct_halfwidth(tuple(self._chain), thr)
                plan.set_direct(hw is not None, hw or 1)
            self._thr_applied = True
        return plan

    def _direct_halfwidth(self, chain, thresholds, nsim=20000):
        """The direct refine's window half-width for this chain (gatechain.direct_halfwidth,
        plus one coarse sample), or None where it does not apply: off (MF_DIRECT_REFINE=0),
        or no reference to model it on."""
        if not _direct_refine_enabled() or self._pending_ref is None:
            return None
        hw, _, _ = _gatechain.direct_halfwidth(self._pending_ref, self.n, chain, thresholds,
                                               self._fs_snr or self.snr, self.fd,
                                               window=self.search_window, nsim=nsim)
        return hw + 1

    def _direct_prices(self, base):
        """{band: ticks per refined pair} of the direct refine with this plan's taps, for a
        chain whose last tier is that band (window from the single-tier model at the band);
        empty where the direct refine does not apply. Cached per reference and taps."""
        taps = getattr(self, "_taps", None)
        if taps is None or not _direct_refine_enabled() or self._pending_ref is None:
            return {}
        key = (float(self._fs_snr or self.snr), float(self.fd), self.search_window)
        hit = getattr(self, "_dprice", None)
        if (hit is not None and hit[0] == key and hit[2] is self._pending_ref
                and hit[3] is taps[0]):
            return hit[1]
        lagtap = _direct_lagtap()
        L = 32.0 * max(1, int(round(float(np.mean(taps[1])) / 32.0)))   # as the chain key rounds it
        prices = {}
        if lagtap > 0:
            p = np.asarray(self._pending_ref, dtype=np.float64)
            for b in _gatechain.usable_bands(p / p.sum(), self.n):
                pl = _gatechain.chain_thresholds(self._pending_ref, self.n, self._fs_snr or self.snr,
                                                 self.fd, (b,), cost=base, window=self.search_window)
                if pl is None:
                    continue
                # Pricing only ranks chains: a tenth of the draws. The chain that runs gets its
                # window from the full draw count (_execution_plan).
                hw = self._direct_halfwidth((b,), pl["thresholds"], nsim=2000)
                lags = 2 * hw * (self.n // b) + 1
                # the correlation, plus the per-lag binning around it (~4 ticks a lag)
                prices[int(b)] = lagtap * L * lags + 4.0 * lags
        self._dprice = (key, prices, self._pending_ref, taps[0])   # held: identity is the key
        return prices


    def release_trials(self):
        """The bank's block-size trial locked on this plan's layout: start the measured choices
        it held back (chain trial, then Q15) by choosing the chain again."""
        if not getattr(self, "_trial_hold", False):
            return
        self._trial_hold = False
        if self._chain is None or self._pending_ref is None:
            return                              # chosen, unheld, at first use
        chain = self._choose_chain()
        if tuple(chain) != tuple(self._chain):
            self._switch_chain(chain)
        else:
            self._q15 = bool(getattr(self, "_q15_pref", False)) and (
                self._mf is None or bool(self._mf.set_q15(bool(getattr(self, "_q15_pref", False)))))

    def _switch_chain(self, chain):
        """Run a different configuration from now on, keeping loaded data and templates."""
        self._chain, self._q15 = tuple(chain), False
        self._thr_applied = False
        if self._gpu is not None:
            self._gcal = None
            self._tdirty = True
            # A host plan built for the old chain (_execution_plan builds one for a timed
            # trial call) would take the new chain's thresholds: one per tier of a chain it
            # does not run. Rebuilt on next use.
            self._mf = None
            return
        self._mf = self._new_cpu_plan(self._chain)
        self._restore_into(self._mf)

    # ---- thresholds ----------------------------------------------------------
    def _thresholds(self, *, required=True):
        """One threshold per tier: explicit, or from the reference model."""
        if self._cal_thr is not None:
            if len(self._cal_thr) != len(self._chain):
                raise ValueError("explicit thresholds %s do not match chain %s" % (self._cal_thr, self._chain))
            return self._cal_thr
        if self._pending_ref is not None:
            pl = _gatechain.chain_thresholds(self._pending_ref, self.n, self._fs_snr or self.snr, self.fd,
                                             self._chain, cost=self._cost_model(),
                                             window=self.search_window)
            if pl is not None:
                th = tuple(float(x) for x in pl["thresholds"])
                for v in th:
                    if not np.isfinite(v) or v < 0 or v > float(np.finfo(np.float32).max):
                        raise ValueError("calibrated coarse threshold must be finite, nonnegative float32; got %r" % (th,))
                return th
        if required:
            raise ValueError(
                "no calibrated coarse threshold for chain %s at n=%d: provide a reference and a "
                "resolvable budget, or set the thresholds explicitly" % (self._chain, self.n))
        return None

    def set_coarse_threshold(self, value):
        """Set the gate thresholds directly, bypassing the model.

        ``value`` is one number per tier of the pinned chain (a bare number
        for a one-tier chain). Each tier's coarse maximum is compared against
        its threshold; a pair that falls below any is dismissed. The guarantee
        becomes whatever these thresholds imply. Pass None to return to the model.
        """
        if value is None:
            self._cal_thr = None
            self._thr_applied = False
            return
        vals = (value,) if np.isscalar(value) else tuple(value)
        vals = tuple(float(v) for v in vals)
        for v in vals:
            if not np.isfinite(v) or v < 0 or v > float(np.finfo(np.float32).max):
                raise ValueError("coarse thresholds must be finite nonnegative float32, or None")
        if self._pinned is None:
            raise ValueError("explicit thresholds require an explicit band (a pinned chain)")
        if len(vals) != len(self._pinned):
            raise ValueError("chain %s needs %d thresholds" % (self._pinned, len(self._pinned)))
        self._cal_thr = vals
        self._thr_applied = False
        self._gcal = None

    def set_first_stage(self, snr):
        """Calibrate the gate against `snr` rather than the constructor's.

        Final triggers are still cut at the threshold passed to :meth:`run`;
        this sets only where the gate decides a full reconstruction is needed.
        Pass ``None`` or a non-positive value to use the constructor's SNR.
        """
        self._fs_snr = float(snr) if snr is not None and float(snr) > 0 else None
        self._thr_applied = False
        self._gcal = None

    def set_reference(self, power):
        """Set the reference SNR distribution: expected power per bin of the filter output.

        Only its shape matters. The profile must describe every template in
        this plan. Pass ``None`` to use each template's own band fraction
        (explicit thresholds only). Changing it recalibrates the thresholds of
        the chain in use.
        """
        if power is not None:
            p = np.ascontiguousarray(_from_any(power), dtype=np.float32)
            if p.shape != (self.n,) and p.shape != (getattr(self, 'k', self.n),):
                raise ValueError("reference must be a one-dimensional array of length %d" % self.n)
            if not np.isfinite(p).all() or np.any(p < 0) or not np.any(p > 0):
                raise ValueError("reference must be finite, nonnegative, with positive total power")
            if self._pending_ref is not None and np.array_equal(p, self._pending_ref):
                return
        self._thr_applied = False
        if self._gpu is not None:
            self._gcal = None
            self._tdirty = True
        if power is None:
            self._pending_ref = None
            if self._mf is not None:
                self._mf.set_reference(None)
                self._reload_templates()
            return
        self._pending_ref = p.copy()
        if self._mf is not None:
            self._mf.set_reference(p)
            self._reload_templates()

    def _reload_templates(self):
        """After a reference change: the CPU plan's loaded templates were scaled for the old
        reference and are stale (it keeps no unscaled copy); load them again."""
        if self._template_ready is None or self._template_ready:
            self._load_held_templates(self._mf)

    # ---- chain choice ----------------------------------------------------------
    def _cost_model(self):
        """The costs of the device this plan runs on: chains rank differently on a GPU (a refined
        pair costs ~30 coarse pairs there against ~100 on a CPU core)."""
        if self.device.kind == "gpu":
            return _gatechain.calibrate_costs_gpu(self.n, str(self.device))
        policy = self._series_policy('hierarchical_series', 0, self.ntemplates) or {}
        cm = _gatechain.calibrate_costs(self.n, self.ntemplates,
                                        group=policy.get('series_group', _gatechain.default_series_group(self.n)))
        prices = self._direct_prices(cm)
        return (cm.with_direct(prices, single_tier=_gatechain.cpu_gate_kind() != "f16")
                if prices else cm)

    def _direct_key(self):
        """The direct refine's rounded tap length when it is priced into this plan's chain
        choice (HierarchicalFilter._direct_prices), else None: chain choices and locks are
        kept apart by it, since a cheaper refine changes which chain wins."""
        taps = getattr(self, "_taps", None)
        if taps is None or not _direct_refine_enabled() or self.device.kind != "cpu":
            return None
        return int(round(float(np.mean(taps[1])) / 32.0))

    def _chain_trial_key(self):
        """The key this plan's chain trial and its stored lock are filed under."""
        tiers = min(self.max_tiers, self._MAX_TIERS[self.device.kind])
        tkey = (self.n, float(self._fs_snr or self.snr), float(self.fd), tiers, str(self.device))
        # Whether the direct refine is priced in, not at which tap length: groups of every
        # shape share one trial and its lock (each still prices its own taps in the model).
        return tkey if self._direct_key() is None else tkey + (1,)

    def _choose_chain(self):
        """Pick a gate chain: the model prices every chain, measurement settles the close ones.

        The model need not be exact. It prunes: chains whose modelled cost is
        more than the model's error margin above the best cannot win and are
        never run. If more than one chain survives, plans sharing a shortlist
        run it round-robin on real calls, and the chain with the lowest
        measured time per pair is kept for all of them. MF_AUTOTUNE=0 keeps
        the model's choice.
        """
        if _uncovered_reference(self._pending_ref, self.n):
            raise ValueError(
                "the reference has no localised correlation peak at n=%d: every candidate "
                "band has an effective bandwidth below %.0f bins, so there is nothing for a "
                "coarse pass to localise -- use MatchedFilter. A reference like this is "
                "usually |h|^2 without the 1/S(f), or a spectrum with no low-frequency cutoff."
                % (self.n, _BEFF_MIN))
        snr = self._fs_snr or self.snr
        tiers = min(self.max_tiers, self._MAX_TIERS[self.device.kind])
        ref = np.asarray(self._pending_ref, np.float64)
        prof = _gatechain._gm._profile_sig(ref / ref.sum())
        direct = self._direct_key()
        key = (self.n, float(snr), float(self.fd), tiers, self.search_window, prof, str(self.device),
               _gatechain.cpu_gate_kind() if self.device.kind == "cpu" else None, direct)
        with _AUTOTUNE_LOCK:
            hit = _CHAIN_CHOICE.get(key)
        if hit is None:
            best, plans = _gatechain.choose_chain(self._pending_ref, self.n, snr, self.fd, ntemplates=self.ntemplates,
                                                  cost=self._cost_model(), max_tiers=tiers,
                                                  window=self.search_window)
            if best is None:
                raise ValueError(_uncovered_message(self.n, self.snr, self.fd))
            margin = float(os.environ.get("MF_CHAIN_MARGIN", _CHAIN_MARGIN))
            # On a GPU the trial runs on whole batches in the search's own mode, so its cost
            # is a few segments: the model's best few are measured whatever their modelled
            # gap. The model prices device work only, and missed the faster chain by 38%
            # (n=2048: (256, 1024) priced 1.8 against 1.3, measured ~1.5 ms/segment faster).
            near = (lambda q: True) if self.device.kind == "gpu" else (
                lambda q: q["cost"] <= best["cost"] * (1.0 + margin))
            shortlist = tuple(q["chain"] for q in sorted(
                (q for q in plans if near(q)),
                key=lambda q: (q["chain"] != best["chain"], q["cost"])))
            hit = (tuple(best["chain"]), shortlist[:_CHAIN_SHORTLIST_MAX if self.device.kind != "gpu"
                                                   else _CHAIN_SHORTLIST_GPU],
                   tuple(tuple(q["chain"]) for q in plans))
            with _AUTOTUNE_LOCK:
                _Q15_MODEL[(key, tuple(best["chain"]))] = bool(best.get("q15", False))
            with _AUTOTUNE_LOCK:
                _CHAIN_CHOICE[key] = hit
            _log_autotune("CHAIN n=%d model=%s shortlist=%s ranking=%s", self.n, hit[0], hit[1],
                          [(q["chain"], round(q["cost"], 1)) for q in plans[:6]])
        model_best, shortlist, feasible = hit
        forced = os.environ.get("MF_CHAIN_FORCE")
        pinned = False
        if forced:
            # Measurement only (chain studies): every hierarchical plan of this n runs the
            # given bands, outside any trial. "n:b1,b2;n2:b1" or "b1,b2" for every n.
            for part in forced.split(";"):
                pn, _, bands = part.rpartition(":")
                if not pn or int(pn) == self.n:
                    want = tuple(int(b) for b in bands.split(",") if b)
                    if want and len(want) <= tiers and all(b < self.n for b in want):
                        model_best, shortlist, feasible = want, (want,), (want,)
                        pinned = True
        if not _autotune_enabled():
            shortlist = shortlist[:1]

        chain = model_best
        self._chain_trial = None
        tkey = self._chain_trial_key()
        # The key's lock -- reached in this process or read from MF_COST_FILE -- decides
        # the chain of EVERY plan of the key: the plan runs it if it can (its feasible set),
        # else its model's chain, and a locked key never opens a trial. The in-process
        # record holds the file's lock unfiltered: filtered by the first plan's feasible set,
        # a plan that could not run it cached "no lock" and every later plan of the key
        # ignored the file and re-trialled (two processes on one file ended on different
        # chains, L40S).
        w = None
        if not pinned and _autotune_enabled():
            with _AUTOTUNE_LOCK:
                tr = _CHAIN_TRIALS.get(tkey)
                if tr is None:
                    tr = _CHAIN_TRIALS[tkey] = {"samples": {}, "assigned": {},
                                                "winner": _stored_chain_lock(tkey, None)}
                    tr["median"], tr["rechecked"] = _chain_lock_state(tkey)
                w = tr["winner"]
            if w is not None:
                if tuple(w) in feasible:
                    chain = tuple(w)
                    self._chain_monitor = tkey
        # While the bank's block-size trial is open (time_domain: _trial_hold), the plan runs
        # the model's chain: chain and Q15 trials wait for the winning layout (release_trials).
        held = getattr(self, "_trial_hold", False)
        if w is None and len(shortlist) > 1 and not held and not pinned and _autotune_enabled():
            # One trial per configuration: plans whose references differ slightly (another
            # segment's PSD, another template group) have slightly different short lists, and
            # their union is what gets measured. Candidates arriving before the lock join it;
            # after the lock every plan adopts the winner.
            self._chain_monitor = tkey        # steady calls re-check the lock (_chain_steady)
            with _AUTOTUNE_LOCK:
                tr = _CHAIN_TRIALS[tkey]
                if tr["winner"] is not None:
                    if tuple(tr["winner"]) in feasible:
                        chain = tuple(tr["winner"])
                else:
                    for c in shortlist:
                        tr["samples"].setdefault(c, []); tr["assigned"].setdefault(c, 0)
                    chain = min(shortlist, key=lambda c: (len(tr["samples"][c]) + tr["assigned"][c],
                                                          shortlist.index(c)))
                    tr["assigned"][chain] += 1
                    self._chain_trial = tkey
        self.autotune_info = {"status": "trial" if self._chain_trial else "locked",
                              "winner": tuple(chain), "shortlist": shortlist, "model": model_best}
        # The model's screen choice for this chain; with MF_AUTOTUNE on, trials override it.
        with _AUTOTUNE_LOCK:
            self._q15_pref = _Q15_MODEL.get((key, tuple(chain)), False)
        return tuple(chain)

    def _first_tier_pass(self, pairs):
        """Fraction of the last call's pairs the first tier passed, where the engine reports it."""
        if len(self._chain) < 2:
            return None          # a single tier's passes are refines; its cost already shows them
        if self._gpu is not None:
            n1 = getattr(self._gpu, "last_tier1_survivors", None)
            return None if n1 is None else n1 / pairs
        if self._mf is None:
            return None
        prev, self._tier0_seen = getattr(self, "_tier0_seen", None), (
            self._mf.first_gate_passed(), self._mf.stats()[0])
        if prev is None or self._tier0_seen[1] <= prev[1]:
            return None
        return (self._tier0_seen[0] - prev[0]) / (self._tier0_seen[1] - prev[1])

    def _chain_trial_record(self, dt, pairs):
        """Record one measured call for this plan's trial chain; lock the winner once every
        candidate has enough samples and the shared rule (gatechain.measured_choice) is clear."""
        with _AUTOTUNE_LOCK:
            tr = _CHAIN_TRIALS.get(self._chain_trial)
            if tr is None:
                return
            base = int(os.environ.get("MF_CHAIN_TRIALS", _CHAIN_TRIALS_PER_CAND))
            tneed = tr.setdefault("need", {})
            needs = lambda c: max(base, tneed.get(c, 0))   # noqa: E731

            def decide(smp, model):
                """Lock from smp, or ask for more (tneed) when the contest is unclear."""
                w, more = _gatechain.measured_choice(smp, model, 2 * base)
                if w is None:
                    tneed.update(more)
                    _log_autotune("CHAIN-TRIAL unclear, sampling further %s", more)
                return w
            if tr["winner"] is None and pairs > 0:
                # A chain whose first tier passed most pairs on this call gates nothing: it
                # is priced at infinity, so it can never be locked in whatever its time.
                frac = self._first_tier_pass(pairs)
                tr["samples"][self._chain].append(
                    float("inf") if frac is not None and frac > _gatechain._USELESS_PASS else dt / pairs)
                if all(len(v) >= needs(c) for c, v in tr["samples"].items()):
                    # The model's chain (the shortlist's first) stands unless another is
                    # clearly faster, past TIE and the samples' noise.
                    w = decide(tr["samples"], next(iter(tr["samples"])))
                    if w is not None:
                        med = {c: float(np.median(v)) for c, v in tr["samples"].items()}
                        _chain_lock(self._chain_trial, tr, w, med)
                        _log_autotune("CHAIN-TRIAL locked %s  median s/pair %s", tr["winner"],
                                      {c: "%.3g" % v for c, v in med.items()})
            if (tr["winner"] is None
                    and sum(len(v) for v in tr["samples"].values())
                    >= _TRIAL_BUDGET * base * len(tr["samples"])):
                w = _trial_budget_choice(tr["samples"], next(iter(tr["samples"])), base)
                if w is not None:
                    med = {c: float(np.median(v)) for c, v in tr["samples"].items() if len(v)}
                    _chain_lock(self._chain_trial, tr, w, med)
                    _log_autotune("CHAIN-TRIAL budget spent: locked %s", tr["winner"])
            winner = tr["winner"]
            move = None
            if winner is None:
                # Candidates that joined later (another plan's shortlist, another reference)
                # may never be run by any live plan: their samples never come, the trial
                # never locks, and every plan in it stays synchronous and untimed for good.
                # A plan whose own shortlist is fully sampled settles on its own: it moves
                # to an unsampled candidate of ITS shortlist, or locks the best of it.
                own = [tuple(c) for c in self.autotune_info.get("shortlist", ())
                       if tuple(c) in tr["samples"]]
                mine = tuple(self._chain)
                if own and len(tr["samples"].get(mine, ())) >= needs(mine):
                    lacking = [c for c in own if len(tr["samples"][c]) < needs(c)]
                    if not lacking:
                        winner = decide({c: tr["samples"][c] for c in own}, own[0])
                        if winner is not None:
                            _log_autotune("CHAIN-TRIAL plan locked %s on its own shortlist", winner)
                        lacking = [c for c in own if len(tr["samples"][c]) < needs(c)]
                    if winner is None and lacking:
                        move = min(lacking, key=lambda c: (len(tr["samples"][c]) + tr["assigned"][c],
                                                           own.index(c)))
                        tr["assigned"][move] += 1
                        tr["assigned"][mine] = max(0, tr["assigned"].get(mine, 1) - 1)
        if winner is not None:
            self._chain_trial = None
            self.autotune_info.update(status="locked", winner=tuple(winner))
            if tuple(winner) != tuple(self._chain):
                self._switch_chain(winner)
        elif move is not None:
            self._switch_chain(move)

    # ---- run ----------------------------------------------------------------
    def run_series(self, series, starts=None, win_start=None, win_end=None,
                   binsize=None, threshold=0.0, templates=None, raw=False,
                   decimated=None):
        if self._chain_trial is None and self.device.kind == "cpu" and self._mf is not None:
            q15_timed = self._q15_before_call()
            full = templates is None or templates[1] >= self.ntemplates
            try:
                nblk = len(starts) if starts is not None else 1
            except TypeError:
                nblk = 0
            if q15_timed and full and nblk >= 2:
                # Resolve thresholds before timing either arm, then replay exactly the
                # same workload. Pool complete ratios across groups, not their raw costs.
                self._execution_plan()
                parent_run = super().run_series
                def run():
                    return parent_run(series, starts=starts, win_start=win_start, win_end=win_end,
                                      binsize=binsize, threshold=threshold, templates=templates,
                                      raw=raw, decimated=decimated)
                return self._q15_run_pair(run, nblk * self.ntemplates * self.ndata)
        if self._chain_trial is None:
            return super().run_series(series, starts=starts, win_start=win_start, win_end=win_end,
                                      binsize=binsize, threshold=threshold, templates=templates,
                                      raw=raw, decimated=decimated)
        # One-off work (building the plan, calibrating its thresholds) is not the chain's cost.
        trial_begin = time.perf_counter()
        self._execution_plan()
        t0 = time.perf_counter()
        res = super().run_series(series, starts=starts, win_start=win_start, win_end=win_end,
                                 binsize=binsize, threshold=threshold, templates=templates,
                                 raw=raw, decimated=decimated)
        dt = time.perf_counter() - t0
        full = templates is None or templates[1] >= self.ntemplates
        nblk = len(starts) if starts is not None else 1
        if full and nblk >= 2 and self._chain_trial is not None and self._gpu is None:
            # (GPU plans are judged per batch instead: time_domain._trial_begin/_trial_end.)
            self._chain_trial_record(dt, nblk * self.ntemplates * self.ndata)
        if self._gpu is None:
            _record_cpu_trial(trial_begin)
        return res

    def set_templates(self, spectra, index=None):
        if self._gpu is not None or index is not None:
            return super().set_templates(spectra, index=index)
        a = np.ascontiguousarray(_from_any(spectra), dtype=np.complex64)
        if a.ndim != 2:
            raise ValueError(f"expected 2D array of spectra, got {a.shape}")
        if a.shape[0] != self.ntemplates:
            raise ValueError(f"expected {self.ntemplates} templates, got {a.shape[0]}")
        if a.shape[1] == self.n:
            self._bandlimited, k = False, self.n
        elif a.shape[1] == self.n // 2:
            self._bandlimited, k = True, self.n // 2
        else:
            raise ValueError(f"expected shape ({self.ntemplates}, {self.n}) or ({self.ntemplates}, {self.n // 2}), got {a.shape}")
        rebuild = self._mf is not None and getattr(self._mf, 'k', self.n) != k
        self.k = k
        self._held_templates = self._hold(a)
        if rebuild:
            self._mf = None
        plan = self._ensure()
        if not rebuild:
            plan.set_template_batch(0, a)
        self._mark_ready("template", None)

    def set_taps(self, taps, counts=None):
        """Each template's real FIR taps, for the direct refine on the CPU.

        taps (ntemplates, m) float32, row t's first counts[t] taps valid (all m when counts
        is None), the centre tap counts[t] // 2 at lag 0 -- the filter whose spectrum
        set_templates holds, at the data's sample rate (time_domain.template_spectra with
        tap and data rates equal). run_series then refines a survivor by direct correlation
        at the lags around its last tier's firing coarse lags wherever that is priced
        cheaper than a whole-block transform; MF_DIRECT_REFINE=0 turns it off."""
        taps = np.ascontiguousarray(taps, dtype=np.float32)
        if taps.ndim != 2 or taps.shape[0] != self.ntemplates:
            raise ValueError("taps must be (ntemplates, m) = (%d, m)" % self.ntemplates)
        counts = (np.full(self.ntemplates, taps.shape[1], np.int64) if counts is None
                  else np.ascontiguousarray(counts, dtype=np.int64))
        if counts.shape != (self.ntemplates,) or counts.min() < 1 or counts.max() > min(taps.shape[1], self.n):
            raise ValueError("counts must be (ntemplates,) in [1, min(m, n)]")
        self._taps = (taps, counts)
        self._dprice = None
        if self._pinned is None and self._chain is not None and self.device.kind == "cpu":
            # The model priced the chain without the direct refine: choose again (the plan is
            # rebuilt on next use and replays reference, templates and data).
            self._chain, self._mf, self._gcal = None, None, None
        elif self._mf is not None:
            self._mf.set_taps(taps, taps.shape[1], counts)
            self._thr_applied = False           # the direct window is set with the thresholds

    def direct_stats(self):
        """Direct-refine counters of the CPU plan ({} before one exists)."""
        return self._mf.direct_stats() if self._mf is not None else {}

    def set_hermitian(self, hermitian: bool):
        self._hermitian = bool(hermitian)
        if self._mf is not None:
            self._mf.set_hermitian(self._hermitian)
        # The GPU kernels take full spectra: half-length templates were unpacked when
        # set, so a change of convention re-unpacks them.
        if self._gpu is not None and getattr(self, "_gpu_packed", None) is not None:
            self.set_templates(self._gpu_packed)

    @property
    def hermitian(self):
        return self._hermitian

    @hermitian.setter
    def hermitian(self, value):
        self.set_hermitian(value)

    # ---- GPU -----------------------------------------------------------
    #
    # The coarse pass IS a matched filter on an m-point plan: the ordinary flat
    # filter at length `band`, on templates truncated to that band and scaled
    # by 1/sqrt(f). A supplied reference gives a common power fraction;
    # otherwise each coarse template is normalized by its own.
    def _start_gpu(self):
        if self.n not in _GPU_SIZES:
            raise ValueError(
                "device='gpu' supports n in %s; got %d"
                % (sorted(_GPU_SIZES), self.n))
        self._gpu = self._backend().Context(self.device.index)
        self._gdata = None  # series execution uses its own workspace
        self._gtmpl = None
        self._gcal = None

    def _gpu_calibration(self, threshold):
        """(chain, per-tier reference band fractions or None, per-tier thresholds)."""
        key = (self.snr, self.fd, self._fs_snr, self._chain, self._cal_thr)
        if self._gcal is not None and self._gcal[0] == key:
            return self._gcal[1]
        if self._chain is None:
            if self._pending_ref is None:
                raise ValueError("set a reference first (set_reference), or pin a chain")
            self._chain = self._choose_chain(); self._q15 = getattr(self, "_q15_pref", False)
            key = (self.snr, self.fd, self._fs_snr, self._chain, self._cal_thr)
        thr = self._thresholds(required=True)
        f = None
        if self._pending_ref is not None:
            ref = np.asarray(self._pending_ref, dtype=np.float64)
            tot = ref.sum()
            f = tuple(float(ref[:b].sum() / tot) if tot > 0 else 0.0 for b in self._chain)
        out = (self._chain, f, thr)
        self._gcal = (key, out)
        return out

    def _coarse_templates(self, H, bands, f):
        """Coarse templates per tier: the first b bins scaled by 1/sqrt(band fraction)."""
        out = []
        for i, b in enumerate(bands):
            if f is None:
                power = H.real * H.real + H.imag * H.imag
                total = power.sum(axis=1, dtype=np.float64)
                frac = np.divide(power[:, :b].sum(axis=1, dtype=np.float64), total,
                                 out=np.zeros_like(total), where=total > 0)
                sc = np.divide(1.0, np.sqrt(frac), out=np.zeros_like(frac), where=frac > 0)[:, None].astype(np.float32)
            else:
                sc = np.float32(1.0 / np.sqrt(f[i])) if f[i] > 0 else np.float32(0.0)
            out.append(H[:, :b] * sc)
        return out

    def _grouped_dispatch(self, n, spec, H, groups, binsize, threshold, **kw):
        """The gate chain over every window group of one spectra batch, one submission."""
        chain, f, thr = self._gpu_calibration(threshold)
        ck = (chain, f, H.ctypes.data, H.shape)
        if getattr(self, "_ckey", None) != ck or self._tdirty:
            self._ct = self._coarse_templates(H, chain, f)
            self._ckey = ck
        ct = self._ct
        extra = {} if len(chain) == 1 else dict(cascade_band=chain[0], ct1=ct[1], raw_thr1=thr[1])
        res = self._gpu.hier_peaks_grouped(n, chain[-1], spec, H, ct[0], thr[0], groups, binsize,
                                           threshold, upload_tmpl=self._tdirty, **extra, **kw)

        def account(r):
            shp = r.shape if isinstance(r, _SparsePeaks) else r[0].shape
            self._gpairs += shp[0] * shp[1]
            self._gtrig += self._gpu.last_refinements
            self._gt1 += getattr(self._gpu, "last_tier1_survivors", 0) or 0
            return r
        if kw.get("async_submit"):
            return lambda: account(res())
        return account(res)

    def _gpu_dispatch(self, D, H, binsize, threshold, start, end, slot=None, async_submit=False,
                      **kw):
        """Run the gate chain and refinement without host survivor readback."""
        chain, f, thr = self._gpu_calibration(threshold)
        ck = (chain, f, H.ctypes.data, H.shape)
        if getattr(self, "_ckey", None) != ck or self._tdirty:
            self._ct = self._coarse_templates(H, chain, f)
            self._ckey = ck
        ct = self._ct
        if len(chain) == 1:
            res = self._gpu.hier_peaks(
                self.n, chain[0], D, H, ct[0], thr[0],
                binsize=binsize, threshold=threshold, window=(start, end),
                upload_data=self._ddirty, upload_tmpl=self._tdirty,
                slot=slot, async_submit=async_submit, **kw)
        else:
            res = self._gpu.hier_peaks(
                self.n, chain[1], D, H, ct[0], thr[0],
                binsize=binsize, threshold=threshold, window=(start, end),
                upload_data=self._ddirty, upload_tmpl=self._tdirty,
                cascade_band=chain[0], ct1=ct[1], raw_thr1=thr[1],
                slot=slot, async_submit=async_submit, **kw)
        self._ddirty = self._tdirty = False

        def account(r):
            shp = r.shape if isinstance(r, _SparsePeaks) else r[0].shape
            self._gpairs += shp[0] * shp[1]
            self._gtrig += self._gpu.last_refinements
            self._gt1 += getattr(self._gpu, "last_tier1_survivors", 0) or 0
            return r
        if async_submit:
            return lambda: account(res())
        return account(res)

    # ---- reporting -----------------------------------------------------------
    @property
    def config(self):
        """The gate chain in use: a tuple of bands."""
        if self._chain is None:
            if self._gpu is not None:
                self._gpu_calibration(self.snr)
            else:
                self._ensure()
        return tuple(self._chain)

    @property
    def stats(self):
        """``(pairs, refined)`` accumulated since construction."""
        if self._gpu is not None:
            return (self._gpairs, self._gtrig)
        return self._ensure().stats()

    def work_counts(self):
        """Cumulative work counters for matchedfilter._roofline: a dict with the chain
        (bands), pairs (block, template) seen by tier 0, passed (pairs each tier passed;
        the last tier's passes are the refines), refined, q15 (pairs the int16 screen
        passed to the float tier 0, or None when no screen ran) and, on the CPU, ticks per
        tier, refine, screen and whole series calls. GPU passes for tier 0 of a two-tier
        chain come from the backend's last_tier1_survivors; ticks are None there."""
        chain = tuple(self._chain) if self._chain else ()
        if self._gpu is not None:
            passed = ([self._gt1] if len(chain) == 2 else []) + [self._gtrig]
            return dict(backend="gpu", chain=chain, pairs=self._gpairs, passed=passed,
                        refined=self._gtrig, q15=None, ticks=None, ident=id(self))
        mf = getattr(self, "_mf", None)
        if mf is None:
            return dict(backend="cpu", chain=chain, pairs=0, passed=[0] * len(chain),
                        refined=0, q15=None, ticks=None, ident=None)
        st = mf.tier_stats()
        pairs, refined = mf.stats()
        q_on, q_passed, q_ticks = mf.q15_stats()
        return dict(backend="cpu", chain=tuple(int(b) for b, _, _ in st[:-1]), pairs=int(pairs),
                    passed=[int(p) for _, p, _ in st[:-1]],
                    checked=[int(c) for c in mf.tier_inputs()], refined=int(refined),
                    q15=int(q_passed), q15_on=bool(q_on),
                    ticks=dict(tiers=[int(t) for _, _, t in st[:-1]], refine=int(st[-1][2]),
                               q15=int(q_ticks), series=int(mf.series_ticks())),
                    ident=id(mf))

    @property
    def tier_stats(self):
        """Per logical tier ``(band, passed, ticks)``, then refine ``(n, refined, ticks)``.

        Passed counts include only pairs evaluated at that gate. With reordered
        gates they need not decrease in logical band order; work_counts()['checked']
        gives each gate's actual input count.
        """
        if self._gpu is not None:
            return None
        return self._ensure().tier_stats()

    @property
    def refine_rate(self):
        """Fraction of pairs that needed the full correlation.

        This is what the speedup rides on, and the first thing to look at when
        the filter is slower than expected. Counted over the plan's lifetime.
        """
        pairs, trig = self.stats
        return trig / pairs if pairs else 0.0


def __getattr__(name):
    """Expose ``Device`` without enumerating hardware at import time.

    Listing devices creates a Vulkan instance, which is far too much work to
    do on ``import matchedfilter`` for the majority of callers who will only
    ever use the CPU.
    """
    if name == "Device":
        from .device import Device
        return Device
    if name == "device":
        import importlib
        return importlib.import_module(".device", __name__)
    raise AttributeError(name)
