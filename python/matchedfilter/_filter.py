"""The flat filters: MatchedFilter (peak output) and CorrelationFilter (full output), and
the input and output helpers they share. Re-exported by the package as matchedfilter.*."""
import hashlib
import math
import operator
import os
import sys
import threading
import time
import warnings
from types import SimpleNamespace
from typing import NamedTuple, Optional

import numpy as np

from . import _config
from . import _core
from . import gatechain as _gatechain
from . import _chains, _choice, _prices
from ._choice import _AUTOTUNE_LOCK, _autotune_enabled, _log_autotune  # noqa: F401
from ._results import PEAK_DTYPE, _Deferred, _SparsePeaks  # noqa: F401


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


def _check_threshold(threshold):
    """Refuse a NaN threshold: every comparison with it is false, so a run would report
    nothing (or everything) without saying why. Infinite thresholds are legal."""
    if threshold is not None and np.isnan(np.float64(threshold)):
        raise ValueError("threshold is NaN")


def _as_c64(a, n, what):
    a = np.ascontiguousarray(_from_any(a), dtype=np.complex64)
    if a.ndim != 1 or a.size != n:
        raise ValueError(f"{what} must be a 1-D complex array of {n} samples, got shape {a.shape}")
    return a


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


def _compute_module(device):
    """The driver module for a GPU device: the one choice made by API, as a driver is one
    API's implementation of the executor's primitives (Metal on Apple, CUDA on NVIDIA, else
    Vulkan)."""
    backend = getattr(device, "backend", None)
    if backend == "metal":
        from . import _mtlcompute
        return _mtlcompute
    if backend == "cuda":
        from . import _cudacompute
        return _cudacompute
    from . import _vkcompute
    return _vkcompute


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
    #: Whether this is a HierarchicalFilter, for the shared code paths that differ for one
    #: (a class attribute, not isinstance: _filter does not import _hierarchical).
    _is_hierarchical = False

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
        # return skipped the calibration it was supposed to set, and every Metal
        # call died in _gpu_calibration on a missing attribute.
        if self.n not in self._gpu_sizes:
            raise ValueError(
                "device='gpu' supports n in %s for this filter; got %d."
                % (sorted(self._gpu_sizes), self.n))
        self._gpu = self._backend().Context(self.device.index)
        self._gdata = None  # series execution uses its own workspace
        self._gtmpl = None

    def _backend(self):
        """The compute module for this device (_compute_module)."""
        return _compute_module(self.device)

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
            # A copy, not the caller's array: it is replayed into a rebuilt plan, which
            # must see the data as it was set, whatever the caller did to its array since.
            a = np.array(_as_c64(spectra, self.n, "spectrum"), copy=True)
            self._held[int(index)] = a
            self._ensure().set_data(int(index), a)
            self._dataset = True
            self._mark_ready("data", index)
            return
        a = np.array(_from_any(spectra), dtype=np.complex64, order="C", copy=True)
        if a.ndim != 2 or a.shape != (self.ndata, self.n):
            raise ValueError(f"expected shape ({self.ndata}, {self.n}), got {a.shape}")
        self._held[-1] = a                      # a copy: see the note above
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
        _check_threshold(threshold)
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
        if (not np.iscomplexobj(a) and self._is_hierarchical
                and self._reads_real_series()):
            if (isinstance(a, np.ndarray) and a.dtype == np.float32 and a.ndim == 1
                    and a.strides in ((8,), (4,)) and a.size > 0):
                return a            # read in place: contiguous, or one lane of a complex row
            return _host_copy(a, np.float32)
        return _host_copy(a, np.complex64)

    def _series_layout(self, series, starts, win_start, win_end, binsize, templates,
                       ragged=False, bin_phase=None):
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
        layout = SeriesLayout(self.n, st, ws, we, binsize, ragged=ragged,
                              phase=None if bin_phase is None else _from_any(bin_phase))
        return ser, layout, binsize, t0, nt

    def _grouped_layout(self, series, starts, win_start, win_end, binsize, templates,
                        ragged=False, bin_phase=None):
        """_series_layout, grouped, cached per layout signature.

        A search calls the same plan with the same blocks every segment: validating and
        grouping them again was a large part of the per-call host time. The key is the
        layout's bytes (not array identity), so a caller reusing and rewriting its arrays
        still gets a fresh layout. A cached layout is never mutated after grouping."""
        group = self._gpu is not None or self.ndata > 1 or self._is_hierarchical
        key = None
        if (type(starts) is np.ndarray and type(win_start) is np.ndarray
                and type(win_end) is np.ndarray):
            key = (starts.dtype.char, starts.tobytes(), win_start.dtype.char, win_start.tobytes(),
                   win_end.dtype.char, win_end.tobytes(), binsize,
                   None if templates is None else (int(templates[0]), int(templates[1])),
                   group, self._gpu is not None, ragged,
                   None if bin_phase is None else np.asarray(bin_phase, np.uint32).tobytes())
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
            series, starts, win_start, win_end, binsize, templates, ragged=ragged,
            bin_phase=bin_phase)
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

        Several allocations share one spectra workspace (the forward takes a row range).
        wait=False: returns a callable giving that list once the submission completes, so a caller submits every template group's
        items before waiting on any (an idle GPU takes ~1 ms to start each small submission
        on an M2 or an APU)."""
        from ._shared import containing
        gpu = self._gpu
        if (gpu is None or not hasattr(gpu, "peaks_items") or type(self) is not MatchedFilter
                or self._gtmpl is None or not jobs):
            return None
        n = self.n
        # A job may carry its blocks' bin phases (filter_series' window bins) as a sixth item.
        jobs = [j if len(j) == 6 else tuple(j) + (None,) for j in jobs]
        allocs, rows = {}, []                 # id(whole) -> [whole, row0 in the workspace, rows]
        for ser, st, ws, we, t, _ in jobs:
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
        phase = (np.zeros(max(total, 1), np.uint32)
                 if any(j[5] is not None for j in jobs) else None)
        for (ser, st, ws, we, t, ph), (k_alloc, row) in zip(jobs, rows):
            k = int(st.size)
            pos = fill[k_alloc]
            fill[k_alloc] += k
            place.append(pos)
            if ph is not None:
                phase[pos:pos + k] = ph
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
                              **({"async_submit": True} if async_ok else {}),
                              **({} if phase is None else {"phase": phase}))

        def assemble(res):
            out, it = [], 0
            for (ser, st, ws, we, t, _), pos in zip(jobs, place):
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
                           threshold=0.0, templates=None, bin_phase=None):
        """run_series(raw=True) over blocks whose windows give DIFFERENT bin counts.

        The result is (nblocks, nt, max bins); a block's bins past its own count are
        dismissed (-1, 0), as each block's own call would report them. Every window
        group is one dispatch of a single submission, where calling run_series once per
        distinct bin count costs a submission and a wait each -- most of a
        single-template follow-up's time on a GPU.

        A hierarchical plan takes this path too: its grouped call runs per-row windows (each block's own [lo, hi)) under one
        recording of the largest bin count, so a block's bins past its own count are
        empty exactly as for a flat plan.

        Returns None when this plan cannot (CPU, a backend without ragged support, or a
        shape the grouped path does not take); the caller then makes one call per bin count.
        """
        if self._gpu is None:
            return None
        # (A GPU plan in a joint trial is judged per batch, not per call: it takes the same
        # paths as any other -- ragged, deferred, replayed.)
        if not self._is_hierarchical and type(self) is not MatchedFilter:
            return None
        # Cached per layout bytes (as run_series), so a repeated call keeps its layout and
        # with it its call plan.
        ser, layout, binsize, t0, nt = self._grouped_layout(
            series, starts, win_start, win_end, binsize, templates, ragged=True,
            bin_phase=bin_phase)
        if ((len(layout.groups) < 2 and layout.phase is None)
                or layout.nbins > getattr(self._gpu, "max_grouped_bins", 0)
                or nt > self._gpu_pair_limit()):
            return None
        self._dataset = False
        self._data_ready = set()
        return self._run_series_gpu(ser, layout, binsize, threshold, t0, nt, True)

    def run_series(self, series, starts=None, win_start=None, win_end=None,
                   binsize=None, threshold=0.0, templates=None, raw=False,
                   decimated=None, bin_phase=None):
        """Filter a series using this filter's ``valid`` overlap-save window.

        ``run_series(series)`` derives contiguous blocks and returns peak
        indices in series coordinates. ``run_blocks`` accepts explicit block
        starts and windows, returning block-local lag indices. Passing those
        arguments here remains supported for existing callers.

        ``bin_phase`` (explicit blocks only): one value per block, numbering block b's
        bins from ``win_start[b] - bin_phase[b]`` rather than from ``win_start[b]``, so that
        a window spanning several blocks keeps its own bin grid; a bin cut by a block edge is
        then two partial bins, one per block. Bins before ``win_start[b]`` are empty, which
        lets blocks with fewer bins share one call with the rest.

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
        _check_threshold(threshold)
        is_outer = not getattr(self, '_in_series_call', False)
        if is_outer:
            self._in_series_call = True
            t0 = time.perf_counter()
        try:
            return self._run_series_inner(series, starts=starts, win_start=win_start,
                                          win_end=win_end, binsize=binsize,
                                          threshold=threshold, templates=templates,
                                          raw=raw, decimated=decimated, bin_phase=bin_phase)
        finally:
            if is_outer:
                self._in_series_call = False
                self._record_batch_time(time.perf_counter() - t0)

    def _run_series_inner(self, series, starts=None, win_start=None, win_end=None,
                          binsize=None, threshold=0.0, templates=None, raw=False,
                          decimated=None, bin_phase=None):
        if starts is None:
            if win_start is not None or win_end is not None or bin_phase is not None:
                raise ValueError('win_start, win_end and bin_phase require explicit starts')
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
        if getattr(self, '_bandlimited', False) and not self._is_hierarchical:
            if decimated is None:
                decim = getattr(series, 'sample_rate', 2048) < getattr(series, 'input_sample_rate', 2048)
            else:
                decim = bool(decimated)
            return self.run_series_dif(
                series, starts, win_start, win_end, binsize=binsize,
                threshold=threshold, templates=templates, raw=raw,
                decimated=decim, bin_phase=bin_phase
            )
        ser, layout, binsize, t0, nt = self._grouped_layout(
            series, starts, win_start, win_end, binsize, templates, bin_phase=bin_phase)
        st, ws, we = layout.starts, layout.low, layout.high
        nblk = st.size
        # CPU series execution reuses the data slots. Require fresh spectra
        # before a later run(), consistently on both devices.
        self._dataset = False
        self._data_ready = set()
        if self._gpu is not None:
            return self._run_series_gpu(ser, layout, binsize, threshold, t0, nt, raw)
        nb = layout.nbins
        ph = layout.phase
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
                                                   float(threshold), cnt, ph)
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
                                                    float(threshold), idx, val, mag, cnt,
                                                    None, ph)
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
                                                float(threshold), empty_idx, empty_val, mag, cnt,
                                                peaks, ph)
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
                       decimated=False, bin_phase=None):
        """Filter a full-rate series using 2-channel decimation-in-frequency (DIF)."""
        _check_threshold(threshold)
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
        ph = None
        if bin_phase is not None:
            ph = np.ascontiguousarray(_from_any(bin_phase), dtype=np.uint32)
            if ph.shape != st.shape or np.any(ph >= 1 << 24):
                raise ValueError("bin_phase needs one entry per block, each below 2**24")
            if not np.any(ph):
                ph = None
        bin_counts = (ends - ws + (0 if ph is None else ph.astype(ends.dtype)) + bs - 1) // bs
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
                                                  float(threshold), idx, val, mag, cnt, None, decim,
                                                  ph)
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
                                              float(threshold), empty_idx, empty_val, mag, cnt, peaks,
                                              decim, ph)
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
            "backend": _core.backend(),
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
        objs = (layout, self._gpu, self._gtmpl, self.__dict__.get("_resolved"),
                self.__dict__.get("_ct"), self.__dict__.get("_ckey"),
                None if ws is None else ws[2], None if ws is None else ws[3])
        vals = (int(binsize), float(threshold), t0, nt, self.__dict__.get("_series_batch_bytes"),
                _config.get("MF_GPU_QUEUE_AHEAD"),
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
                _config.get("MF_GPU_QUEUE_AHEAD"), bool(d.get("_want_sparse", False)))
        addr = ser.ctypes.data
        entry = plans.get((addr, ser.size, vals, id(layout)))
        if entry is None:
            return None
        # The objects of _call_plan_state, by identity, inline (this is the hot path).
        objs = entry["state"][0]
        ws = d.get("_series_workspace")
        if (objs[0] is not layout or objs[1] is not self._gpu or objs[2] is not self._gtmpl
                or objs[3] is not d.get("_resolved") or objs[4] is not d.get("_ct")
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
        if self._is_hierarchical:
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
        c.single = single = (len(layout.groups) == 1 and nblk <= batch
                             and layout.phase is None)
        # Sparse results (time_domain asks with _want_sparse): only the peaks come back.
        # At threshold 0 (follow-ups) every bin holds a peak: dense is cheaper there.
        sparse = bool(raw and threshold > 0 and getattr(self, "_want_sparse", False))
        c.skw = {"sparse": True} if sparse else {}
        c.is_hier = self._is_hierarchical
        # A declared capability, not a probe for one backend's internals.
        can_pipeline = getattr(self._gpu, "cache_limit_bytes", 10**9) > 1024 * 1024
        # A phased call (bin_phase) reads every row's window and bin phase from a row table,
        # which only the grouped dispatch has: it goes grouped even with one window group.
        phased = layout.phase is not None
        if phased and (nb > getattr(self._gpu, "max_grouped_bins", 0)
                       or nt > self._gpu_pair_limit()):
            raise ValueError("bin_phase needs the grouped dispatch: at most %d bins and %d "
                             "templates a call here" % (getattr(self._gpu, "max_grouped_bins", 0),
                                                         self._gpu_pair_limit()))
        grouped_flat = ((len(layout.groups) > 1 or phased) and type(self) is MatchedFilter
                        and nb <= getattr(self._gpu, "max_grouped_bins", 0)
                        and nt <= self._gpu_pair_limit())
        # Deferred (TimeDomainFilterBank.filter_series_many): submit now, collect later, so the
        # GPU works on this call while the host prepares the next bank's. (A joint trial's
        # round replays whole batches in the mode the search runs: deferred too.)
        # A grouped flat call defers too when it is one batch (a follow-up's window: one
        # submission for every bin count).
        c.defer = defer = (getattr(self, "_defer_series", False) and can_pipeline
                           and (not grouped_flat or nblk <= batch))
        c.pipelined = can_pipeline and (not single or defer)
        queue_ahead = _config.get("MF_GPU_QUEUE_AHEAD")
        c.K = K = max(1, queue_ahead) if c.pipelined else 1
        # Irregular flat windows share one forward FFT dispatch and submission per bounded
        # batch. Hierarchical plans join when the backend submits grouped hierarchical windows
        # (one dispatch per tier over every row, each in its own window). Deferred calls
        # (filter_series_many) keep the one-submission grouped path: without it a deferred
        # hierarchical call became one submission per window group (3x the submissions and
        # launches of the synchronous call, measured 1.4x slower on CUDA).
        c.grouped = grouped_flat or (
            (len(layout.groups) > 1 or phased) and c.is_hier
            and nb <= getattr(self._gpu, "max_grouped_bins", 0)
            and nt <= self._gpu_pair_limit())
        # A real series: the GPU forward reads its samples from complex64 storage, by float
        # offset and stride (c.real), never widened on the host.
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
                     - base).astype(np.uint32),
                    None if layout.phase is None else layout.phase[begin:end]))
            plan_b = bc[ckey] = (layout, parts)
        # A deferred call reading a device allocation in place records its call plan
        # (_replay_call_plan): every batch's forward and hierarchical record handles.
        # Read in place means a row of an allocation (contained) or a whole one -- not a
        # host array viewed for this call (series_owner).
        record = (c.defer and c.is_hier and c.raw and c.pipelined
                  and (c.contained is not None or (c.source_shared and not c.viewed)))
        recorded = []
        for begin, end, count, groups, rebased, phase in plan_b[1]:
            fh, hh = [], []
            slot, spec = self._series_submit(c, slot_idx, begin, count, rebased,
                                             **({"handle_out": fh} if record else {}))
            slot_idx += 1
            try:
                res = self._grouped_dispatch(
                    c.n, spec, c.H, groups, c.binsize, c.threshold,
                    slot=slot if c.pipelined else None, async_submit=c.pipelined,
                    **({"nbins": c.nb} if getattr(layout, "ragged", False) else {}), **c.skw,
                    **({"handle_out": hh} if record else {}),
                    **({} if phase is None else {"phase": phase}))
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
        # A real series: the forward reads its samples from complex64 storage, by float
        # offset and stride -- in place where it lies in a device
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
            kw = {'wait': False} if not wait and scales is None else {}
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


#: n -> whether continuous correlation at n runs through the platform FFT (vDSP on macOS):
#: set by time_domain._corr_block_costs, which prices both and keeps the cheaper.
_CORR_PFFT = {}
