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
           "TimeDomainFilterBank", "FilterResults", "taps_to_spectra"]

from .time_domain import TimeDomainFilterBank, FilterResults


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
    __slots__ = ("_finish", "_value", "_done", "empty", "trace")

    def __init__(self, finish):
        self._finish, self._value, self._done, self.empty = finish, None, False, False
        self.trace = None

    def result(self):
        if not self._done:
            self._value, self._finish, self._done = self._finish(), None, True
        return self._value


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
        self.performance_stats = {
            "total_calls": 0,
            "total_time_s": 0.0,
            "batch_times_ms": []
        }
        self._in_series_call = False
        self._gpu = None
        self._gpairs = 0
        self._gtrig = 0
        self._ddirty = True
        self._tdirty = True

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
        self._held_templates = a.copy()
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
    def run(self, binsize=None, threshold=0.0, window=None,
            data=None, templates=None, counts=False, raw=False):
        t0 = time.perf_counter()
        try:
            return self._run_inner(binsize=binsize, threshold=threshold, window=window,
                                  data=data, templates=templates, counts=counts, raw=raw)
        finally:
            dt = time.perf_counter() - t0
            self.performance_stats["total_calls"] += 1
            self.performance_stats["total_time_s"] += dt
            self.performance_stats["batch_times_ms"].append(dt * 1000.0)

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


    def _series_layout(self, series, starts, win_start, win_end, binsize, templates,
                       ragged=False):
        """Validate the shared series contract before either native backend."""
        ser = np.ascontiguousarray(_from_any(series), dtype=np.complex64)
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

    def _settle_deferred(self):
        """Collect every deferred call still in flight on this plan (filter_series_many)."""
        owners = self.__dict__.get("_slot_owner")
        if owners:
            pending = list(owners.values())
            owners.clear()
            for d in pending:
                d.result()

    def _items_gpu(self, jobs, binsize, threshold):
        """Many single-template series calls as one forward dispatch and one submission.

        jobs: [(series, starts, win_start, win_end, template)] -- each a run_series call on one
        template of this plan. Every series must lie in one device allocation (rows of a
        reused device buffer), read in place. Returns per job (idx, val) shaped
        (nblocks, 1, max bins) with -1 in bins past a block's own count, or None when this
        plan or these inputs cannot take the path (the caller then makes the calls)."""
        from ._shared import containing
        gpu = self._gpu
        if (gpu is None or not hasattr(gpu, "peaks_items") or type(self) is not MatchedFilter
                or self._gtmpl is None or not jobs):
            return None
        whole, rows = None, []
        for ser, st, ws, we, t in jobs:
            c = containing(np.ascontiguousarray(ser), gpu)
            if c is None or (whole is not None and c[0] is not whole):
                return None
            if st.size and int(st.max()) + self.n > ser.size:
                return None                     # needs the upload's zero padding past the end
            whole = c[0]
            rows.append(c[1])
        n = self.n
        total = sum(int(st.size) for _, st, _, _, _ in jobs)
        if total == 0:
            return [(np.empty((0, 1, 1), np.int64), np.empty((0, 1, 1), np.complex64))
                    for _ in jobs]
        cap = getattr(self, "_items_ws", None)
        if cap is None or cap[0].shape[0] < total:
            cap = (gpu.empty_shared((max(total, 2 * (cap[0].shape[0] if cap else 0)), n)),
                   gpu.empty_shared(max(total, 2 * (cap[0].shape[0] if cap else 0)), np.uint32))
            self._items_ws = cap
        spec, starts = cap
        items, pos = [], 0
        for (ser, st, ws, we, t), row in zip(jobs, rows):
            k = int(st.size)
            starts[pos:pos + k] = np.minimum(st, ser.size).astype(np.int64) + row
            lo_hi = np.stack([np.minimum(ws, n), np.minimum(we, n)], 1).astype(np.int64)
            j = 0
            while j < k:                        # runs of blocks with one window
                e = j + 1
                while e < k and lo_hi[e, 0] == lo_hi[j, 0] and lo_hi[e, 1] == lo_hi[j, 1]:
                    e += 1
                items.append((int(lo_hi[j, 0]), int(lo_hi[j, 1]), pos + j, pos + e, int(t)))
                j = e
            pos += k
        self._settle_deferred()
        gpu.forward(n, whole, starts[:total], spec[:total], defer=True)
        res = gpu.peaks_items(n, spec[:total], self._gtmpl, items, binsize, threshold)
        out, it, pos = [], 0, 0
        for ser, st, ws, we, t in jobs:
            k = int(st.size)
            mine = []
            while it < len(items) and items[it][3] <= pos + k:
                mine.append((items[it], res[it]))
                it += 1
            nbmax = max([r[0].shape[2] for _, r in mine] or [1])
            idx = np.full((k, 1, nbmax), -1, np.int64)
            val = np.zeros((k, 1, nbmax), np.complex64)
            for (lo, hi, a, b, _), (gi, gv) in mine:
                idx[a - pos:b - pos, :, :gi.shape[2]] = gi
                val[a - pos:b - pos, :, :gv.shape[2]] = gv
            out.append((idx, val))
            pos += k
        return out

    def _run_series_ragged(self, series, starts, win_start, win_end, binsize=None,
                           threshold=0.0, templates=None):
        """run_series(raw=True) over blocks whose windows give DIFFERENT bin counts.

        The result is (nblocks, nt, max bins); a block's bins past its own count are
        dismissed (-1, 0), as each block's own call would report them. Every window
        group is one dispatch of a single submission, where calling run_series once per
        distinct bin count costs a submission and a wait each -- most of a
        single-template follow-up's time on a GPU.

        Returns None when this plan cannot (CPU, a hierarchical plan, a backend
        without ``supports_ragged_bins``, or a shape the grouped path does not take);
        the caller then makes one call per bin count.
        """
        if (self._gpu is None or type(self) is not MatchedFilter
                or not getattr(self._gpu, "supports_ragged_bins", False)):
            return None
        ser, layout, binsize, t0, nt = self._series_layout(
            series, starts, win_start, win_end, binsize, templates, ragged=True)
        layout.group(materialize=True)
        if (len(layout.groups) < 2 or layout.nbins > getattr(self._gpu, "max_grouped_bins", 0)
                or nt > self._gpu_pair_limit()):
            return None
        layout.ragged = True
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
                dt = time.perf_counter() - t0
                self.performance_stats["total_calls"] += 1
                self.performance_stats["total_time_s"] += dt
                self.performance_stats["batch_times_ms"].append(dt * 1000.0)

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
        ser, layout, binsize, t0, nt = self._series_layout(
            series, starts, win_start, win_end, binsize, templates)
        if self._gpu is not None or self.ndata > 1 or isinstance(self, HierarchicalFilter):
            layout.group(materialize=self._gpu is not None)
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
        if raw:
            sb = self._sbuf
            if sb is None or sb[0] != shape:
                sb = self._sbuf = (shape,
                                   np.empty(need, dtype=np.int64),
                                   np.empty(need, dtype=np.complex64),
                                   np.empty(0, dtype=np.float32),
                                   np.empty(nblk * nt, dtype=np.int32))
            _, idx, val, mag, cnt = sb
            tot = self._execution_plan().run_series(ser, st, ws, we, t0, nt, binsize,
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
        tot = self._execution_plan().run_series(ser, st, ws, we, t0, nt, binsize,
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
            wk_s0 = int(ws[0])
            wk_e0 = min(k_val, int(we[0]))
            bs = N if binsize is None else int(binsize)
            bs_k = k_val if bs >= k_val else max(1, int(bs))
        else:
            N = self.n if getattr(self, '_bandlimited', False) else self.n * 2
            wk_s0 = int(ws[0] // 2)
            wk_e0 = min(k_val, int((we[0] + 1) // 2))
            bs = N if binsize is None else int(binsize)
            bs_k = k_val if bs >= N else max(1, int(bs // 2))
        if bs < 1:
            raise ValueError("binsize must be >= 1")
        t0, nt = (0, self.ntemplates) if templates is None else (
            int(templates[0]), int(templates[1]))
        if nt < 1 or t0 < 0 or t0 + nt > self.ntemplates:
            raise ValueError("templates sub-range out of bounds")
        self._require_templates(t0, nt)

        nblk = st.size
        nb = 1 + (wk_e0 - wk_s0 - 1) // bs_k
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
        times = self.performance_stats.get("batch_times_ms", [])
        total_calls = self.performance_stats.get("total_calls", 0)
        total_time_s = self.performance_stats.get("total_time_s", 0.0)
        if times:
            min_ms = float(np.min(times))
            max_ms = float(np.max(times))
            med_ms = float(np.median(times))
            mean_ms = float(np.mean(times))
        else:
            min_ms = max_ms = med_ms = mean_ms = 0.0

        summary = {
            "total_calls": total_calls,
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

    def _run_series_gpu(self, ser, layout, binsize, threshold, t0, nt, raw):
        """Execute shared layout groups with bounded FFT/gather storage."""
        n, nb, nblk = self.n, layout.nbins, layout.starts.size
        H = self._gtmpl[t0:t0 + nt]
        from ._shared import shared_buffer
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
        policy = self._series_policy(operation, band, nt)
        if policy:
            batch = min(batch, policy['series_group'])
        single = len(layout.groups) == 1 and nblk <= batch
        self._last_series_batch = batch
        # Sparse results (time_domain asks with _want_sparse): only the peaks come back.
        # At threshold 0 (follow-ups) every bin holds a peak: dense is cheaper there.
        sparse = bool(raw and threshold > 0 and getattr(self, "_want_sparse", False)
                      and getattr(self._gpu, "supports_sparse", False))
        skw = {"sparse": True} if sparse else {}
        sparse_parts = []

        def take_dense(b_start, b_end, r):
            """Store one batch's result; sparse pieces are kept aside (see finish)."""
            if isinstance(r, _SparsePeaks):
                sparse_parts.append((b_start, r))
                return
            gi, gv = r
            if raw:
                idx[b_start:b_end], val[b_start:b_end] = gi, gv
            else:
                _core.pack_peaks(peaks[b_start:b_end], gi, gv)

        def finish_raw():
            if sparse_parts:
                sp = _SparsePeaks.combine(sparse_parts, shape, layout.order)
                if not dense_seen[0]:
                    return sp
                # Mixed (a tiled fallback came back dense): densify the sparse pieces.
                for b0, part in sparse_parts:
                    pi, pv = part.dense()
                    idx[b0:b0 + part.shape[0]], val[b0:b0 + part.shape[0]] = pi, pv
            return _format_result(idx, val, raw=True, order=layout.order)
        dense_seen = [False]
        is_hier = isinstance(self, HierarchicalFilter)
        # A declared capability, not a probe for one backend's internals.
        can_pipeline = (getattr(self._gpu, "supports_async", False)
                        and getattr(self._gpu, "cache_limit_bytes", 10**9) > 1024 * 1024)
        grouped_flat = (len(layout.groups) > 1 and type(self) is MatchedFilter
                        and nb <= getattr(self._gpu, "max_grouped_bins", 0)
                        and nt <= self._gpu_pair_limit())
        # Deferred (TimeDomainFilterBank.filter_series_many): submit now, collect later, so the
        # GPU works on this call while the host prepares the next bank's. Chain trials time
        # their calls, so a plan under trial runs synchronously.
        # A grouped flat call defers too when it is one batch (a follow-up's window: one
        # submission for every bin count), on a backend that declares it can.
        defer = (getattr(self, "_defer_series", False) and can_pipeline
                 and (not grouped_flat or (nblk <= batch
                                           and getattr(self._gpu, "defers_grouped", False)))
                 and getattr(self, "_chain_trial", None) is None)
        pipelined = can_pipeline and (not single or defer)
        queue_ahead = int(os.environ.get("MF_GPU_QUEUE_AHEAD", "8"))
        K = max(1, queue_ahead) if pipelined else 1
        source_shared = shared_buffer(ser, self._gpu) is not None
        # Unified memory: read a page-aligned series where it is rather than copying the
        # span into the source buffer (a fine-stage call copied ~6 MB per call). The owner
        # lives for this call; each command buffer retains what it reads.
        view = getattr(self._gpu, "host_view", None)
        series_owner = view(ser) if (view is not None and not source_shared) else None
        if series_owner is not None:
            source_shared = True
        # A series inside a device allocation (a row of a device buffer a caller reuses, e.g.
        # correlate_series(out=bank.empty_shared(...))) is read where it is, by offset --
        # unless a block would read past its end, where the upload's zero padding is needed.
        contained = None
        if not source_shared and nblk:
            from ._shared import containing
            contained = containing(ser, self._gpu)
            if contained is not None and int(layout.starts.max()) + n > ser.size:
                contained = None
        # Pools are sized by capacity, not by this call's batch: windowed calls vary in
        # block count, and reallocating would also discard every recording built on them.
        # Capacity in both batch and slots: a call alternating unpipelined (K=1) and pipelined
        # (K=8) groups reallocated every call, and recordings are keyed on these buffers.
        workspace = getattr(self, "_series_workspace", None)
        if (workspace is None or workspace[0][1] != n or workspace[0][0] < batch
                or workspace[0][2] < K):
            cap_b = (batch if workspace is None or workspace[0][1] != n else max(batch, workspace[0][0])) + 16
            cap_k = K if workspace is None or workspace[0][1] != n else max(K, workspace[0][2])
            spectra_pool = [self._gpu.empty_shared((cap_b, n)) for _ in range(cap_k)]
            starts_pool = [self._gpu.empty_shared(cap_b, np.uint32) for _ in range(cap_k)]
            workspace = ((cap_b, n, cap_k), None if workspace is None else workspace[1],
                         spectra_pool, starts_pool)
        _, source, spectra_pool, starts_pool = workspace
        if not defer:
            # A synchronous call reuses slots (and their fences) from 0: finish whatever a
            # batch still has in flight on this plan first, or two submissions share a fence
            # and one wait never returns.
            self._settle_deferred()
        if defer and getattr(self, "_defer_token", None) != self._defer_series:
            # A new batch starts at slot 0: slots only have to differ among calls in flight
            # together, and reusing the same few keeps their recordings and sources warm.
            self._defer_token, self._defer_slot = self._defer_series, 0
        slot0 = getattr(self, "_defer_slot", 0) % K if defer else 0
        if defer:
            # Settle whatever still holds the slots this call will use: its spectra, starts,
            # source and recordings are about to be rewritten.
            owners = self.__dict__.setdefault("_slot_owner", {})
            nslots = min(K, -(-nblk // batch) + len(layout.groups))
            for k in range(nslots):
                prev = owners.pop((slot0 + k) % K, None)
                if prev is not None:
                    prev.result()
        if contained is not None:
            source, base = contained[0], -contained[1]
            self._series_workspace = (workspace[0], workspace[1], spectra_pool, starts_pool)
        elif source_shared:
            source, base = ser, 0
            # A viewed series keeps the copy buffer for later calls that need one.
            self._series_workspace = (workspace[0], workspace[1] if series_owner is not None
                                      else None, spectra_pool, starts_pool)
        else:
            # Upload only the span the blocks read: a windowed call touches a small part
            # of a long series. Starts are rebased onto it; reads past the series end
            # stay past the end of the span.
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
            src[:top - base] = ser[base:top]
            self._series_workspace = (workspace[0], sources, spectra_pool, starts_pool)
            source = src[:top - base]
        # A single group needs no aggregate buffers or scatter.
        single = len(layout.groups) == 1 and nblk <= batch
        shape = (nblk, nt, nb)
        if not single and defer:
            if raw:
                idx = np.empty(shape, dtype=np.int64)
                val = np.empty(shape, dtype=np.complex64)
            else:
                peaks = np.empty(shape, dtype=PEAK_DTYPE)
        elif not single:
            if raw:
                sb = getattr(self, "_sbuf", None)
                if sb is None or sb[0] != shape:
                    sb = self._sbuf = (shape,
                                       np.empty(shape, dtype=np.int64),
                                       np.empty(shape, dtype=np.complex64))
                _, idx, val = sb
            else:
                spbuf = getattr(self, "_spbuf", None)
                if spbuf is None or spbuf[0] != shape:
                    spbuf = self._spbuf = (shape, np.empty(shape, dtype=PEAK_DTYPE))
                _, peaks = spbuf
        # Irregular flat windows share one forward FFT dispatch and submission per
        # bounded batch. Hierarchical and other backends keep their executor.
        # Hierarchical plans join when the backend submits grouped hierarchical windows in one
        # submission -- unless this call is deferred (filter_series_many), which overlaps
        # whole calls instead.
        # Deferred calls (filter_series_many) keep the one-submission grouped path: without
        # it a deferred hierarchical call became one submission per window group (3x the
        # submissions and launches of the synchronous call, measured 1.4x slower on CUDA).
        grouped = grouped_flat or (
            len(layout.groups) > 1 and isinstance(self, HierarchicalFilter)
            and hasattr(self._gpu, "hier_peaks_grouped")
            and nb <= getattr(self._gpu, "max_grouped_bins", 0)
            and nt <= self._gpu_pair_limit())
        if grouped:
            in_flight = []
            slot_idx = slot0 if defer else 0
            for begin in range(0, nblk, batch):
                end = min(begin + batch, nblk)
                count = end - begin
                groups = [(lo, hi, max(a, begin)-begin, min(b, end)-begin)
                          for lo, hi, a, b in layout.groups if a < end and b > begin]
                slot = slot_idx % K
                slot_idx += 1
                starts = starts_pool[slot]
                spec = spectra_pool[slot][:count]
                starts[:count] = np.minimum(layout.starts[begin:end], ser.size).astype(np.int64) - base
                self._gpu.forward(n, source, starts[:count], spec, defer=True,
                                  slot=slot if pipelined else None)
                try:
                    res = self._grouped_dispatch(
                        n, spec, H, groups, binsize, threshold,
                        slot=slot if pipelined else None, async_submit=pipelined,
                        **({"nbins": nb} if getattr(layout, "ragged", False) else {}), **skw)
                    self._tdirty = False
                except Exception:
                    self._gpu.cancel_forward(slot=slot if pipelined else None)
                    raise
                in_flight.append((begin, end, res))
                if len(in_flight) >= K:
                    b_start, b_end, item = in_flight.pop(0)
                    take_dense(b_start, b_end, item() if callable(item) else item)

            def finish_grouped():
                while in_flight:
                    b_start, b_end, item = in_flight.pop(0)
                    take_dense(b_start, b_end, item() if callable(item) else item)
                if raw:
                    return finish_raw()
                return _format_result(None, None, raw=False, order=layout.order, out=peaks)
            if not defer:
                return finish_grouped()
            self._defer_slot = slot_idx
            deferred = _Deferred(finish_grouped)
            owners = self.__dict__.setdefault("_slot_owner", {})
            for k in range(slot0, slot_idx):
                owners[k % K] = deferred
            return deferred
        in_flight = []
        collected_early = [False]
        trace_groups = []
        slot_idx = slot0
        # The packed coarse kernel takes pairs in groups of up to 16 per workgroup and needs
        # the pair count to divide: pad a hierarchical dispatch with copies of its last block
        # (results dropped) rather than fall back to an unpacked, half-idle kernel.
        pad_unit = (16 // math.gcd(nt, 16)) if (is_hier and getattr(self._gpu, "_device_state", None)
                                                 is not None
                                                 and not getattr(self._gpu, "pads_coarse_groups", False)) else 1
        for w0, w1, a, b in layout.groups:
            for begin in range(a, b, batch):
                end = min(begin + batch, b)
                count = end - begin
                count_p = -(-count // pad_unit) * pad_unit
                slot = slot_idx % K
                slot_idx += 1
                starts = starts_pool[slot]
                spec = spectra_pool[slot][:count_p]
                starts[:count] = np.minimum(layout.starts[begin:end], ser.size).astype(np.int64) - base
                if count_p > count:
                    starts[count:count_p] = starts[count - 1]
                self._gpu.forward(n, source, starts[:count_p], spec, defer=True,
                                  slot=slot if pipelined else None)
                try:
                    res = self._series_window(spec, H, binsize, threshold, w0, w1,
                                              slot=slot if pipelined else None,
                                              async_submit=pipelined,
                                              **(skw if count_p == count else {}))
                except Exception:
                    self._gpu.cancel_forward(slot=slot if pipelined else None)
                    raise
                self._ddirty = self._tdirty = False
                if count_p > count:
                    if callable(res):
                        res = (lambda r=res, c=count: tuple(x[:c] for x in r()))
                    else:
                        res = tuple(x[:count] for x in res)
                in_flight.append((begin, end, res))
                if defer and is_hier:
                    trace_groups.append((begin, end, getattr(self._gpu, "_last_dispatch", None)))
                if len(in_flight) >= K:
                    collected_early[0] = True
                    b_start, b_end, item = in_flight.pop(0)
                    r = item() if callable(item) else item
                    if isinstance(r, _SparsePeaks):
                        if single:
                            return r
                        sparse_parts.append((b_start, r))
                        continue
                    gi, gv = r
                    dense_seen[0] = True
                    if single:
                        if raw:
                            return _format_result(gi, gv, raw=True)
                        spbuf = getattr(self, '_spbuf', None)
                        if spbuf is None or spbuf[0] != shape:
                            spbuf = self._spbuf = (shape, np.empty(shape, dtype=PEAK_DTYPE))
                        _, peaks = spbuf
                        return _format_result(gi, gv, raw=False, out=peaks)
                    if raw:
                        idx[b_start:b_end], val[b_start:b_end] = gi, gv
                    else:
                        _core.pack_peaks(peaks[b_start:b_end], gi, gv)
        refined = [0]
        hier = isinstance(self, HierarchicalFilter)

        def finish():
            while in_flight:
                b_start, b_end, item = in_flight.pop(0)
                r = item() if callable(item) else item
                if hier:
                    refined[0] += getattr(self._gpu, "last_refinements", 1)
                if isinstance(r, _SparsePeaks):
                    if single:
                        return r
                    sparse_parts.append((b_start, r))
                    continue
                gi, gv = r
                dense_seen[0] = True
                if single:
                    if raw:
                        return _format_result(gi, gv, raw=True)
                    if defer:
                        out = np.empty(shape, dtype=PEAK_DTYPE)
                    else:
                        spbuf = getattr(self, '_spbuf', None)
                        if spbuf is None or spbuf[0] != shape:
                            spbuf = self._spbuf = (shape, np.empty(shape, dtype=PEAK_DTYPE))
                        out = spbuf[1]
                    return _format_result(gi, gv, raw=False, out=out)
                if raw:
                    idx[b_start:b_end], val[b_start:b_end] = gi, gv
                else:
                    _core.pack_peaks(peaks[b_start:b_end], gi, gv)
            if raw:
                return finish_raw()
            return _format_result(None, None, raw=False, order=layout.order, out=peaks)

        if not defer:
            return finish()
        self._defer_slot = slot_idx

        def finish_marking():
            value = finish()
            # Refinements already collected mid-loop are not counted: only claim empty when
            # every batch was collected here.
            if hier and refined[0] == 0 and not collected_early[0]:
                deferred.empty = True
            return value
        deferred = _Deferred(finish_marking)
        if trace_groups and all(t[2] is not None for t in trace_groups) and raw:
            # How to read this call's result again from its buffers (SegmentPlan replay).
            deferred.trace = dict(groups=trace_groups, shape=shape, order=layout.order)
        owners = self.__dict__.setdefault("_slot_owner", {})
        for k in range(slot0, slot_idx):
            owners[k % K] = deferred
        return deferred

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
            self._continuous_workspace = None
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
        key = (batch, nt, self.n, ser.size)
        work = getattr(self, '_continuous_workspace', None)
        if work is None or work[0] != key:
            work = (key, self.empty_shared(ser.shape),
                    self.empty_shared((batch, self.n)),
                    self.empty_shared(batch, np.uint32))
            self._continuous_workspace = work
        _, staging, spec, offsets = work
        source = ser if shared_buffer(ser, self._gpu) is not None else staging
        if source is staging and defer:
            # Unified memory: read the caller's series in place; the context keeps the
            # view until zero_columns_done has waited for the work that reads it.
            owner = getattr(self._gpu, 'host_view', lambda a: None)(ser)
            if owner is not None:
                self._gpu._keep_until_done.append(owner)
                source = ser
        if source is staging:
            source[:] = ser
        lo, hi = self.valid
        for b0 in range(0, starts.size, batch):
            b1 = min(b0 + batch, starts.size)
            count = b1 - b0
            offsets[:count] = np.minimum(starts[b0:b1], ser.size)
            self._gpu.forward(self.n, source, offsets[:count], spec[:count], defer=True)
            try:
                kw = dict(async_submit=True) if (defer and b1 == starts.size) else {}
                self._gpu.correlate_continuous(
                    self.n, spec[:count], self._gtmpl[t0:t0 + nt],
                    offsets[:count], out, lo, hi,
                    upload_data=True, upload_tmpl=self._tdirty, **kw)
            finally:
                self._gpu.cancel_forward()
            self._tdirty = False

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

    def run(self, data=None, templates=None, out=None, scales=None):
        """Return the full unnormalised circular correlation for each pair."""
        d0, nd, t0, nt = self._pair_range(data, templates)
        result = self._full_output((nd, nt, self.n), out)
        if self._gpu is None:
            self._execution_plan().correlate(d0, nd, t0, nt, result)
        else:
            self._gpu.correlate(self.n, self._gdata[d0:d0 + nd],
                                self._gtmpl[t0:t0 + nt], result,
                                upload_data=self._ddirty,
                                upload_tmpl=self._tdirty)
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
                self._execution_plan().correlate_series_continuous(
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


_AUTOTUNE_LOCK = threading.Lock()
#: (n, snr, fd, tiers, window, profile signature) -> (model's chain, shortlist)
_CHAIN_CHOICE = {}
#: (n, snr, fd, tiers, shortlist) -> measured trials shared by every plan with that shortlist
_CHAIN_TRIALS = {}
#: Relative cost margin inside which modelled chains are measured rather than decided by the
#: model. It is the model's demonstrated error: tier costs agreed with the engine counters to
#: ~25% in the consumer.
_CHAIN_MARGIN = 0.30
_CHAIN_SHORTLIST_MAX = 4
_CHAIN_TRIALS_PER_CAND = 6


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

    Every reported peak is refined by the full filter. The gate can omit
    peaks; ``fd`` is its modelled false-dismissal target at strength ``snr``,
    shared between the chain's tiers. Use :class:`MatchedFilter` to avoid
    gate omissions.

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
    def _new_cpu_plan(self, chain):
        self._execution_policy = self._series_policy('hierarchical_series', chain[-1], self.ntemplates)
        grp = self._execution_policy.get('series_group', 32 if self.n <= 2048 else 16)
        plan = _core.HMF(self.n, self.ndata, self.ntemplates, list(chain), grp,
                         int(getattr(self, 'k', self.n) or self.n))
        if self._hermitian:
            plan.set_hermitian(True)
        return plan

    def _restore_into(self, plan):
        """Replay reference, templates and data into a freshly built plan."""
        if self._pending_ref is not None:
            plan.set_reference(self._pending_ref)
        t = self._held_templates
        if isinstance(t, np.ndarray):
            plan.set_template_batch(0, t)
        elif isinstance(t, list):
            for i, x in enumerate(t):
                if x is not None:
                    plan.set_template(i, x)
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
            self._chain = self._choose_chain()
        self._mf = self._new_cpu_plan(self._chain)
        self._thr_applied = False
        self._restore_into(self._mf)
        return self._mf

    def _execution_plan(self):
        plan = self._ensure()
        if not self._thr_applied:
            plan.set_thresholds(list(self._thresholds(required=True)))
            self._thr_applied = True
        return plan

    def _switch_chain(self, chain):
        """Run a different chain from now on, keeping loaded data and templates."""
        self._chain = tuple(chain)
        self._thr_applied = False
        if self._gpu is not None:
            self._gcal = None
            self._tdirty = True
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
            return
        self._pending_ref = p.copy()
        if self._mf is not None:
            self._mf.set_reference(p)

    # ---- chain choice ----------------------------------------------------------
    def _cost_model(self):
        """The costs of the device this plan runs on: chains rank differently on a GPU (a refined
        pair costs ~30 coarse pairs there against ~100 on a CPU core)."""
        if self.device.kind == "gpu":
            return _gatechain.calibrate_costs_gpu(self.n, str(self.device))
        policy = self._series_policy('hierarchical_series', 0, self.ntemplates) or {}
        return _gatechain.calibrate_costs(self.n, self.ntemplates,
                                          group=policy.get('series_group', _gatechain.default_series_group(self.n)))

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
        key = (self.n, float(snr), float(self.fd), tiers, self.search_window, prof, str(self.device))
        with _AUTOTUNE_LOCK:
            hit = _CHAIN_CHOICE.get(key)
        if hit is None:
            best, plans = _gatechain.choose_chain(self._pending_ref, self.n, snr, self.fd,
                                                  cost=self._cost_model(), max_tiers=tiers,
                                                  window=self.search_window)
            if best is None:
                raise ValueError(_uncovered_message(self.n, self.snr, self.fd))
            margin = float(os.environ.get("MF_CHAIN_MARGIN", _CHAIN_MARGIN))
            shortlist = tuple(q["chain"] for q in plans if q["cost"] <= best["cost"] * (1.0 + margin))
            hit = (tuple(best["chain"]), shortlist[:_CHAIN_SHORTLIST_MAX])
            with _AUTOTUNE_LOCK:
                _CHAIN_CHOICE[key] = hit
            _log_autotune("CHAIN n=%d model=%s shortlist=%s ranking=%s", self.n, hit[0], hit[1],
                          [(q["chain"], round(q["cost"], 1)) for q in plans[:6]])
        model_best, shortlist = hit
        if not _autotune_enabled():
            shortlist = shortlist[:1]
        chain = model_best
        self._chain_trial = None
        if len(shortlist) > 1:
            # One trial per configuration: plans whose references differ slightly (another
            # segment's PSD, another template group) have slightly different short lists, and
            # their union is what gets measured. Candidates arriving before the lock join it;
            # after the lock every plan adopts the winner.
            tkey = (self.n, float(snr), float(self.fd), tiers, str(self.device))
            with _AUTOTUNE_LOCK:
                tr = _CHAIN_TRIALS.setdefault(tkey, {"samples": {}, "assigned": {}, "winner": None})
                if tr["winner"] is not None:
                    chain = tr["winner"]
                else:
                    for c in shortlist:
                        tr["samples"].setdefault(c, []); tr["assigned"].setdefault(c, 0)
                    chain = min(shortlist, key=lambda c: (len(tr["samples"][c]) + tr["assigned"][c],
                                                          shortlist.index(c)))
                    tr["assigned"][chain] += 1
                    self._chain_trial = tkey
        self.autotune_info = {"status": "trial" if self._chain_trial else "locked",
                              "winner": tuple(chain), "shortlist": shortlist, "model": model_best}
        return tuple(chain)

    def _chain_trial_record(self, dt, pairs):
        """Record one measured call for this plan's trial chain; lock the winner once every candidate has enough."""
        with _AUTOTUNE_LOCK:
            tr = _CHAIN_TRIALS.get(self._chain_trial)
            if tr is None:
                return
            if tr["winner"] is None and pairs > 0:
                tr["samples"][self._chain].append(dt / pairs)
                need = int(os.environ.get("MF_CHAIN_TRIALS", _CHAIN_TRIALS_PER_CAND))
                if all(len(v) >= need for v in tr["samples"].values()):
                    med = {c: float(np.median(v)) for c, v in tr["samples"].items()}
                    tr["winner"] = min(med, key=med.get)
                    _log_autotune("CHAIN-TRIAL locked %s  median s/pair %s", tr["winner"],
                                  {c: "%.3g" % v for c, v in med.items()})
            winner = tr["winner"]
        if winner is not None:
            self._chain_trial = None
            self.autotune_info.update(status="locked", winner=tuple(winner))
            if tuple(winner) != tuple(self._chain):
                self._switch_chain(winner)

    # ---- run ----------------------------------------------------------------
    def run_series(self, series, starts=None, win_start=None, win_end=None,
                   binsize=None, threshold=0.0, templates=None, raw=False,
                   decimated=None):
        if self._chain_trial is None:
            return super().run_series(series, starts=starts, win_start=win_start, win_end=win_end,
                                      binsize=binsize, threshold=threshold, templates=templates,
                                      raw=raw, decimated=decimated)
        # One-off work (building the plan, calibrating its thresholds) is not the chain's cost.
        self._execution_plan()
        t0 = time.perf_counter()
        res = super().run_series(series, starts=starts, win_start=win_start, win_end=win_end,
                                 binsize=binsize, threshold=threshold, templates=templates,
                                 raw=raw, decimated=decimated)
        dt = time.perf_counter() - t0
        full = templates is None or templates[1] >= self.ntemplates
        nblk = len(starts) if starts is not None else 1
        if full and nblk >= 2 and self._chain_trial is not None:
            self._chain_trial_record(dt, nblk * self.ntemplates * self.ndata)
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
        self._held_templates = a.copy()
        if rebuild:
            self._mf = None
        plan = self._ensure()
        if not rebuild:
            plan.set_template_batch(0, a)
        self._mark_ready("template", None)

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
            self._chain = self._choose_chain()
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

    @property
    def tier_stats(self):
        """Per tier ``(band, passed, ticks)``, then ``(n, refined, ticks)`` for the refine (CPU)."""
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
