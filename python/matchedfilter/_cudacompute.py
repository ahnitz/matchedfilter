"""Dispatching Slang PTX kernels via the native CUDA Driver API.

Zero runtime dependencies: uses libcuda.so.1 through ctypes directly.
Does not require CUDA Toolkit, nvcc, or runtime compilers.
Loads pre-compiled PTX blobs from python/matchedfilter/ptx/.

Execution model. Every public call enqueues its uploads, kernels and readbacks
on one stream and synchronizes ONCE, at the end (or in the returned readback
callable when ``async_submit``). Nothing reads a device value back to the host
between kernels: the hierarchical refine takes its survivor count from device
memory (a grid-stride launch, refineListed's CUDA build), not from the host.

Timing. With ``MF_GPU_TIMING=1`` in the environment when the Context is made,
every kernel launch and transfer is bracketed by a pair of cuEvents and, at the
synchronization that completes it, ``(label, device_ms)`` is appended to
``self.timing_log``. With it off no event is recorded anywhere.
"""
import ctypes
import os
import pathlib

import numpy as np

from . import _cuda, _gputime
from ._cuda import check_cuda
from ._errors import UnsupportedSize
from ._gpu_cache import InputUploads
from ._shared import empty_shared, shared_buffer, shared_key, _Borrowed

def _borrowed_dptr(self):
    """Device address of a shared array, including a view's offset into its allocation."""
    base = getattr(self.owner.buffer, "dptr", None)
    base = base.value if base is not None else int(getattr(self.handle, "value", self.handle))
    return ctypes.c_uint64(base + getattr(self, "offset", 0))


_Borrowed.dptr = property(_borrowed_dptr)


class _DeviceShared:
    """Per-device state every Context on that device shares: the primary context's
    loaded modules and functions, occupancy and labels. All Contexts on one device
    retain the same primary context, so one module load serves every plan (a bank
    makes dozens of plans; each used to JIT-load its own copy of every kernel)."""

    def __init__(self, cuda, device):
        self.ctx = ctypes.c_void_p()
        check_cuda(cuda.cuDevicePrimaryCtxRetain(ctypes.byref(self.ctx), device),
                   "cuDevicePrimaryCtxRetain")       # held for the process lifetime
        self.modules = {}
        self.pipelines = {}
        self.occupancy = {}
        self.labels = {}


_DEVICE_SHARED = {}


_HERE = pathlib.Path(__file__).resolve().parent
_PTX_DIR = _HERE / "ptx"
_MANIFEST = _PTX_DIR / "manifest.json"

_manifest_cache = None


def _manifest():
    """Build manifest for the PTX kernels."""
    global _manifest_cache
    if _manifest_cache is None:
        import json
        _manifest_cache = (
            json.loads(_MANIFEST.read_text()) if _MANIFEST.is_file() else {}
        )
    return _manifest_cache


_MAX_BINS = 2048
_COARSE_TILE_T = {128: 2, 256: 2, 512: 4, 1024: 2}
# Device scratch bound per tile of a full correlation into a host array.
_TILE_BYTES = 64 * 1024 * 1024

# cuFuncGetAttribute / cuMemAdvise / cuDeviceGetAttribute enums
_FUNC_ATTR_MAX_THREADS = 0
_FUNC_ATTR_SHARED = 1
_FUNC_ATTR_LOCAL = 3
_FUNC_ATTR_NUM_REGS = 4
_ADVISE_PREFERRED_LOCATION = 3
_ADVISE_ACCESSED_BY = 5
_CPU_DEVICE = -1


_STATIC_SHARED_MAX = 48 * 1024
_SHARED_DECL = None
_shared_cache = {}


def _static_shared(path):
    """Bytes of static .shared memory a PTX module declares."""
    global _SHARED_DECL
    key = str(path)
    if key not in _shared_cache:
        import re
        if _SHARED_DECL is None:
            _SHARED_DECL = re.compile(rb"^\s*\.shared\s+(?:\.align\s+\d+\s+)?\.(?:b|u|s|f)(\d+)\s+[\w$]+\[(\d+)\]",
                                      re.M)
        total = 0
        for bits, count in _SHARED_DECL.findall(pathlib.Path(path).read_bytes()):
            total += int(bits) // 8 * int(count)
        _shared_cache[key] = total
    return _shared_cache[key]


def _radix(n):
    return {32768: 32, 65536: 64}.get(n, 16)


def _use_c16(band):
    return band <= 1024


def _pack_half2(a):
    """Bit-pack complex64 into uint32 holding (real_half, imag_half)."""
    a = np.ascontiguousarray(a, dtype=np.complex64)
    r = a.real.astype(np.float16).view(np.uint16)
    i = a.imag.astype(np.float16).view(np.uint16)
    return (r.astype(np.uint32) | (i.astype(np.uint32) << 16)).copy()


def _shift(binsize):
    return (binsize.bit_length() - 1) if binsize & (binsize - 1) == 0 else -1


def _coarse_span(n, band, lo, hi):
    """Coarse-sample window covering [lo, hi), widened by one sample at the start."""
    r = n // band
    cstart = lo // r
    cend = min(band, (hi + r - 1) // r)
    if cstart > 0:
        cstart -= 1
    cend = max(cstart + 1, cend)
    cspan = max(1, cend - cstart)
    return cstart, cend, cspan, _shift(cspan)


def _u32(x):
    return ctypes.c_uint32(int(x) & 0xFFFFFFFF)


def _i32(x):
    return ctypes.c_int32(int(x))


def _f32bits(x):
    return ctypes.c_uint32(int(np.float32(x).view(np.uint32)))


def _ptr(v):
    return ctypes.c_uint64(int(v))


def _uint4(*v):
    """A Slang ``uniform uint4``: ONE 16-byte kernel parameter, not four u32s."""
    return (ctypes.c_uint32 * 4)(*(int(x) & 0xFFFFFFFF for x in v))


class _Buffer:
    """Device memory allocation managed via cuMemAlloc / cuMemFree."""

    def __init__(self, ctx, nbytes):
        self.ctx = ctx
        self.nbytes = int(nbytes)
        self.dptr = ctypes.c_uint64(0)
        if self.nbytes > 0:
            ctx._bind()
            check_cuda(
                self.ctx.cuda.cuMemAlloc_v2(ctypes.byref(self.dptr), self.nbytes),
                "cuMemAlloc",
            )
        self.ptr = self.dptr.value
        self.handle = self.dptr.value

    def write(self, array, stream=None):
        """Host to device copy, ordered on ``stream`` (the context's default stream if None)."""
        array = np.ascontiguousarray(array)
        to_copy = min(self.nbytes, array.nbytes)
        if to_copy > 0:
            self.ctx._copy_h2d(self.dptr.value, array.ctypes.data, to_copy, stream, "upload")

    def read(self, dtype, count, stream=None):
        """Device to host read (synchronous)."""
        out = np.empty(count, dtype=dtype)
        self.read_into(out, stream=stream)
        return out

    def read_into(self, out, stream=None):
        """Direct read into a caller-provided contiguous array (synchronous)."""
        if not out.flags.c_contiguous:
            raise ValueError("read_into needs a C-contiguous array")
        to_copy = min(self.nbytes, out.nbytes)
        if to_copy > 0:
            st = self.ctx.stream if stream is None else stream
            self.ctx._copy_d2h(out.ctypes.data, self.dptr.value, to_copy, st, "readback")
            self.ctx._sync(st)
        return out

    def destroy(self):
        if self.dptr.value:
            self.ctx._bind()
            self.ctx.cuda.cuMemFree_v2(self.dptr)
            self.dptr.value = 0
            self.ptr = 0
            self.handle = 0

    def __del__(self):
        try:
            self.destroy()
        except Exception:
            pass


class _HostBuffer:
    """Host-visible allocation for empty_shared: CUDA managed (unified) memory.

    One address valid on host and device. A ``readback`` allocation (an output
    the host will read) is advised to live in host memory and be mapped by the
    device, so a GPU write goes straight over the bus instead of migrating pages
    to the GPU and back on every call.
    """

    def __init__(self, ctx, nbytes, readback=False):
        self.ctx = ctx
        self.nbytes = max(int(nbytes), 4)
        self.dptr = ctypes.c_uint64(0)
        self.managed = hasattr(self.ctx.cuda, "cuMemAllocManaged")
        ctx._bind()
        if self.managed:
            check_cuda(
                self.ctx.cuda.cuMemAllocManaged(ctypes.byref(self.dptr), self.nbytes, 1),
                "cuMemAllocManaged",
            )
            # No placement advice, readback or not. Host-preferred placement made every GPU
            # write cross PCIe (the middle stage's 216 MB output: 33 ms, against 0.6 ms
            # device-resident); and a `readback` output is often consumed on the device
            # (TimeDomainFilterBank.empty_shared feeds the fine stage). Unadvised managed
            # pages stay where they were last written and migrate when read elsewhere.
        else:
            p = ctypes.c_void_p()
            check_cuda(self.ctx.cuda.cuMemAllocHost_v2(ctypes.byref(p), self.nbytes),
                       "cuMemAllocHost")
            self.dptr.value = p.value
        self.ptr = self.dptr.value
        self.handle = self.dptr.value

    def write(self, array, *args, **kwargs):
        flat = np.ascontiguousarray(array)
        ctypes.memmove(self.ptr, flat.ctypes.data, min(self.nbytes, flat.nbytes))

    def read(self, dtype, count, *args, **kwargs):
        out = np.empty(count, dtype=dtype)
        ctypes.memmove(out.ctypes.data, self.ptr, min(self.nbytes, out.nbytes))
        return out

    def read_into(self, out, *args, **kwargs):
        flat = np.ascontiguousarray(out)
        ctypes.memmove(flat.ctypes.data, self.ptr, min(self.nbytes, flat.nbytes))
        return out

    def destroy(self):
        if self.dptr.value:
            self.ctx._bind()
            # Device work may still reference it; freeing must wait for it.
            self.ctx.cuda.cuCtxSynchronize()
            if self.managed:
                self.ctx.cuda.cuMemFree_v2(self.dptr)
            else:
                self.ctx.cuda.cuMemFreeHost(ctypes.c_void_p(self.dptr.value))
            self.dptr.value = 0
            self.ptr = 0
            self.handle = 0

    def __del__(self):
        try:
            self.destroy()
        except Exception:
            pass


class _Pinned:
    """Page-locked host staging for asynchronous readback (cuMemAllocHost)."""

    def __init__(self, ctx, nbytes):
        self.ctx = ctx
        self.nbytes = max(int(nbytes), 16)
        p = ctypes.c_void_p()
        ctx._bind()
        check_cuda(ctx.cuda.cuMemAllocHost_v2(ctypes.byref(p), self.nbytes), "cuMemAllocHost")
        self.ptr = p.value
        self.handle = p.value
        self._raw = (ctypes.c_ubyte * self.nbytes).from_address(self.ptr)

    def view(self, dtype, count, offset=0):
        return np.frombuffer(self._raw, dtype=dtype, count=count, offset=offset)

    def destroy(self):
        if self.ptr:
            self.ctx._bind()
            self.ctx.cuda.cuMemFreeHost(ctypes.c_void_p(self.ptr))
            self.ptr = 0
            self.handle = 0

    def __del__(self):
        try:
            self.destroy()
        except Exception:
            pass


class _BatchTuple(tuple):
    """Tuple supporting both dict key access and tuple slicing."""
    def __new__(cls, data, tmpl, idx, val, *extra):
        t = super().__new__(cls, (data, tmpl, idx, val, *extra))
        t._dict = {"data": data, "tmpl": tmpl, "idx": idx, "val": val}
        if extra:
            t._dict["host"] = extra[0]
        return t

    def __getitem__(self, item):
        if isinstance(item, str):
            return self._dict[item]
        return super().__getitem__(item)

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def values(self):
        return self._dict.values()

    def items(self):
        return self._dict.items()

    def keys(self):
        return self._dict.keys()


class _Record(dict):
    """A cache record: named buffers, also indexable in the legacy tuple order."""
    ORDER = ("data", "tmpl", "idx", "val", "host")

    def __getitem__(self, item):
        if isinstance(item, int):
            return dict.__getitem__(self, self.ORDER[item])
        if isinstance(item, slice):
            return tuple(dict.__getitem__(self, k) for k in self.ORDER[item])
        return dict.__getitem__(self, item)


class _Resident(_Buffer):
    """A context-wide device copy of a template bank (or its coarse bands). Records
    reference it but do not own it: one copy serves every record and slot of a plan."""


def _owned(buffers):
    """The allocations a cache record owns: not borrowed shared arrays, not residents."""
    return [b for b in buffers if isinstance(b, (_Buffer, _Pinned)) and not isinstance(b, _Resident)]


class Context(InputUploads):
    """One NVIDIA CUDA device context, stream, and loaded PTX pipelines."""

    max_grouped_bins = _MAX_BINS
    cache_limit_bytes = 1024 * 1024 * 1024
    # Unified addressing: a view inside a shared allocation is a device pointer.
    shared_views = True
    # Device memory is separate from host memory (residency matters for pricing).
    discrete = True
    # forward/peaks/peaks_grouped/hier_peaks(_grouped) take slot= and async_submit=:
    # a slot maps to one of 4 streams, and its readback callable syncs that stream only.
    supports_async = True

    @property
    def timing(self):
        """Device timers on. ``_timing`` is the attribute shared with the Vulkan backend:
        gatechain.calibrate_costs_gpu switches it on around its measurement runs."""
        return self._timing

    def shares_memory_with(self, other):
        """Contexts on one device share its primary context, hence every allocation."""
        return isinstance(other, Context) and other.dev_idx == self.dev_idx

    def __init__(self, index=0):
        self.cuda = _cuda.get_cuda_lib()
        self.dev_idx = index
        self.device = ctypes.c_int(0)
        self.ctx = ctypes.c_void_p()
        self.stream = ctypes.c_void_p()
        self.streams = []
        self._using_primary_ctx = False

        check_cuda(self.cuda.cuInit(0), "cuInit")
        check_cuda(self.cuda.cuDeviceGet(ctypes.byref(self.device), index), "cuDeviceGet")
        name_buf = ctypes.create_string_buffer(256)
        self.cuda.cuDeviceGetName(name_buf, len(name_buf), self.device.value)
        self.name = name_buf.value.decode("utf-8", "replace").strip()
        self.sm_count = self._attr(_cuda._CUDA_DEVICE_ATTR_MULTIPROCESSOR_COUNT) or 1
        self.cc = (self._attr(_cuda._CUDA_DEVICE_ATTR_COMPUTE_CAPABILITY_MAJOR),
                   self._attr(_cuda._CUDA_DEVICE_ATTR_COMPUTE_CAPABILITY_MINOR))

        if hasattr(self.cuda, "cuDevicePrimaryCtxRetain"):
            check_cuda(
                self.cuda.cuDevicePrimaryCtxRetain(ctypes.byref(self.ctx), self.device.value),
                "cuDevicePrimaryCtxRetain",
            )
            self._using_primary_ctx = True
        else:
            check_cuda(
                self.cuda.cuCtxCreate_v2(ctypes.byref(self.ctx), 0, self.device),
                "cuCtxCreate",
            )
        check_cuda(self.cuda.cuCtxSetCurrent(self.ctx), "cuCtxSetCurrent")
        for _ in range(4):
            s = ctypes.c_void_p()
            check_cuda(self.cuda.cuStreamCreate(ctypes.byref(s), 1), "cuStreamCreate")
            self.streams.append(s)
        self.stream = self.streams[0]

        # The shared timing contract (_gputime): register, keep (label, device_ms).
        self._fwd_events = {}
        self._timing = _gputime.enabled()
        self.timing_log = []
        self._event_pool = []
        self._pending_events = {}
        if self._timing:
            _gputime.register(self)

        self.last_gpu_time = 0.0
        self.last_refinements = 0
        self.last_tier1_survivors = 0
        shared = _DEVICE_SHARED.get(index)
        if shared is None and self._using_primary_ctx:
            shared = _DEVICE_SHARED[index] = _DeviceShared(self.cuda, self.device.value)
        if shared is not None:
            self._modules, self._pipelines = shared.modules, shared.pipelines
            self._occupancy, self._labels = shared.occupancy, shared.labels
            self._shared_modules = True
        else:
            self._modules, self._pipelines, self._occupancy, self._labels = {}, {}, {}, {}
            self._shared_modules = False
        self._scratch_bufs = {}
        self._residents = {}
        self._batches = {}
        self._full_batches = {}
        self._tierc_batches = {}
        self._forwards = {}
        self._hier = {}
        self._uploaded = {"data": {}, "tmpl": {}}

    # ---- device plumbing -----------------------------------------------------
    def _attr(self, attr):
        v = ctypes.c_int(0)
        self.cuda.cuDeviceGetAttribute(ctypes.byref(v), attr, self.device.value)
        return v.value

    def _bind(self):
        if getattr(self, "ctx", None) and self.ctx.value:
            check_cuda(self.cuda.cuCtxSetCurrent(self.ctx), "cuCtxSetCurrent")

    def get_stream(self, slot=None):
        if slot is not None and self.streams:
            return self.streams[slot % len(self.streams)]
        return self.stream

    def _event(self):
        if self._event_pool:
            return self._event_pool.pop()
        e = ctypes.c_void_p()
        check_cuda(self.cuda.cuEventCreate(ctypes.byref(e), 0), "cuEventCreate")
        return e

    def _new_event(self):
        e = ctypes.c_void_p()
        check_cuda(self.cuda.cuEventCreate(ctypes.byref(e), 2), "cuEventCreate")  # no timing
        return e

    def _after_forwards(self, stream):
        """Order ``stream`` after every deferred forward enqueued on other streams."""
        for key, ev in self._fwd_events.items():
            if key != stream.value:
                check_cuda(self.cuda.cuStreamWaitEvent(stream, ev, 0), "cuStreamWaitEvent")

    def _mark(self, stream):
        """Open a timed region on ``stream``; returns a token for _close (None when off)."""
        if not self._timing:
            return None
        e0 = self._event()
        check_cuda(self.cuda.cuEventRecord(e0, stream), "cuEventRecord")
        return e0

    def _close(self, token, stream, label):
        if token is None:
            return
        e1 = self._event()
        check_cuda(self.cuda.cuEventRecord(e1, stream), "cuEventRecord")
        self._pending_events.setdefault(stream.value, []).append((label, token, e1))

    def _sync(self, stream=None):
        """Wait for ``stream``; resolve its timed regions into timing_log."""
        st = self.stream if stream is None else stream
        check_cuda(self.cuda.cuStreamSynchronize(st), "cuStreamSynchronize")
        self._resolve(st.value)

    def _resolve(self, key):
        pending = self._pending_events.pop(key, None)
        if pending:
            total = 0.0
            ms = ctypes.c_float(0.0)
            for label, e0, e1 in pending:
                check_cuda(self.cuda.cuEventSynchronize(e1), "cuEventSynchronize")
                check_cuda(self.cuda.cuEventElapsedTime(ctypes.byref(ms), e0, e1),
                           "cuEventElapsedTime")
                self.timing_log.append((label, float(ms.value)))
                total += float(ms.value)
                self._event_pool.extend((e0, e1))
            self.last_gpu_time = total * 1e-3

    def timings(self):
        """Settle every outstanding measurement and return timing_log (the _gputime contract)."""
        if self._pending_events:
            self._bind()
            for key in list(self._pending_events):
                self._resolve(key)
        return self.timing_log

    def _copy_h2d(self, dst, src, nbytes, stream, label):
        st = self.stream if stream is None else stream
        tok = self._mark(st)
        check_cuda(self.cuda.cuMemcpyHtoDAsync_v2(dst, src, nbytes, st), "cuMemcpyHtoDAsync")
        self._close(tok, st, label)

    def _copy_d2h(self, dst, src, nbytes, stream, label):
        st = self.stream if stream is None else stream
        tok = self._mark(st)
        check_cuda(self.cuda.cuMemcpyDtoHAsync_v2(dst, src, nbytes, st), "cuMemcpyDtoHAsync")
        self._close(tok, st, label)

    def _fill32(self, dptr, value, count, stream):
        if count > 0:
            check_cuda(self.cuda.cuMemsetD32Async(dptr, value, count, stream), "cuMemsetD32Async")

    def _small_input(self, name, array, stream, slot=None):
        """A device copy of a small host-written input (block starts): one async copy.

        Kernels must not read these from managed memory: the host rewrites them every
        call, so each launch's first read page-faults them back onto the GPU (the
        forward kernel took 132 us/launch on the L40S, 15 us with this). Nor may the
        copy read managed memory (144 us per cuMemcpyAsync): the values go through a
        pinned staging buffer, which the previous call's sync has released."""
        array = np.ascontiguousarray(array)
        nbytes = max(array.nbytes, 4)
        # Keyed by SLOT, not stream: slots s and s+4 share a stream, and the host rewrites
        # this pinned buffer before the stream has run the previous slot's copy from it.
        # A slot is reused only after its readback synchronized, so per-slot is safe.
        k = (name, slot, stream.value)
        sc = self._scratch_bufs.get(k)
        if sc is None or sc[0].nbytes < nbytes:
            if sc is not None:
                self._sync(stream)
                sc[0].destroy()
                sc[1].destroy()
            size = max(nbytes, 4096)
            sc = self._scratch_bufs[k] = (_Buffer(self, size), _Pinned(self, size))
        dev, pin = sc
        if array.nbytes:
            ctypes.memmove(pin.ptr, array.ctypes.data, array.nbytes)
            self._copy_h2d(dev.dptr.value, pin.ptr, array.nbytes, stream, "upload")
        return dev

    def _prefetch(self, buf, offset, nbytes, stream):
        """Migrate a managed span to this device ahead of the kernel that reads it.

        Host-written managed pages would otherwise be faulted in page by page by the
        kernel itself; already-resident pages make this nearly free."""
        if (isinstance(buf, _Borrowed) and getattr(buf.owner.buffer, "managed", False)
                and nbytes > 0 and hasattr(self.cuda, "cuMemPrefetchAsync")):
            self.cuda.cuMemPrefetchAsync(buf.dptr.value + offset, nbytes, self.device.value, stream)

    def _resident(self, name, array, dirty, stream, pack=None):
        """The context's one device copy of ``array`` (templates or a coarse band).

        Re-uploaded only when the caller marks it dirty or a different array arrives.
        Records keyed by slot or window shape used to hold a copy each and upload it on
        first use: a plan alternating grouped and single-window calls, with K pipelined
        slots, uploaded its bank up to 2K times."""
        sig = (array.ctypes.data, array.shape, array.strides)
        data = pack(array) if (pack is not None) else None
        nbytes = data.nbytes if data is not None else array.size * 8
        ent = self._residents.get(name)
        if ent is None or ent[0].nbytes < nbytes:
            if ent is not None:
                self._bind()
                check_cuda(self.cuda.cuCtxSynchronize(), "cuCtxSynchronize")
                ent[0].destroy()
            ent = [_Resident(self, nbytes), None]
            self._residents[name] = ent
        if dirty or ent[1] != sig:
            if data is None:
                data = np.ascontiguousarray(array, np.complex64)
            ent[0].write(data, stream)
            ent[1] = sig
        return ent[0]

    def _upload(self, buf, array, stream):
        """Bring a host input onto the device, or verify a shared one is already there."""
        if isinstance(buf, _Borrowed):
            buf.write(array)
        else:
            buf.write(np.ascontiguousarray(array, np.complex64), stream)

    # ---- kernels -------------------------------------------------------------
    def _stem(self, n, entry, one_bin=False, c16=False, ppg=1, tile=1):
        if entry == "packCoarse":
            return "pack_coarse"
        if entry == "compactPairs":
            return "compact"
        if entry == "seriesForward":
            return f"forward_{n}"
        if entry == "coarseTile":
            return f"coarse_{n}"
        if c16:
            p_s = f"p{ppg}" if ppg > 1 else ""
            t_s = f"t{tile}" if tile > 1 else ""
            return f"tierb_{n}_c16{p_s}{t_s}"
        if entry == "refineListed":
            return f"refine_{n}_onebin" if (one_bin and n >= 4096) else f"refine_{n}"
        if entry == "fullCorrelation":
            return f"full_{n}"
        if entry == "fullCorrelationSeries":
            return f"full_series_{n}"
        if one_bin and n >= 4096:
            return f"tierb_{n}_onebin"
        return f"tierb_{n}"

    def pipeline(self, n, entry="fusedTierB", one_bin=False, c16=False, ppg=1, tile=1):
        """Retrieve or load the compiled PTX kernel function: (function, threads per block)."""
        key = (n, entry, one_bin, c16, ppg, tile)
        if key in self._pipelines:
            return self._pipelines[key]

        r = _radix(n)
        wg = (n // r) * ppg if entry in ("fusedTierB", "refineListed") else (
            256 if entry in ("compactPairs", "packCoarse") else (
                64 if entry == "coarseTile" else (n // r)
            )
        )

        stem = self._stem(n, entry, one_bin=one_bin, c16=c16, ppg=ppg, tile=tile)
        ptx_file = _PTX_DIR / f"{stem}.ptx"
        if ptx_file.is_file() and _static_shared(ptx_file) > _STATIC_SHARED_MAX:
            # CUDA caps STATIC shared memory at 48 KB per block on every
            # architecture (more needs dynamic shared memory and an opt-in);
            # the JIT rejects the module outright (CUDA_ERROR_INVALID_PTX). The
            # 32 KB staging build computes the same transform in more passes.
            small = _PTX_DIR / f"{stem}_lds32.ptx"
            if not small.is_file():
                raise UnsupportedSize(f"{stem} needs more than 48 KB static shared memory "
                                      f"and has no _lds32 build")
            stem, ptx_file = f"{stem}_lds32", small
        if not ptx_file.is_file():
            # A missing variant is not silently replaced by a different one: the
            # PPG/TILE_T are compiled in and the launch geometry depends on them.
            raise UnsupportedSize(f"no PTX kernel for {stem} (n={n}, entry={entry})")
        fn_name = "fusedTierB" if (c16 and entry not in ("coarseTile", "refineListed")) else entry
        if entry == "refineListed":
            fn_name = "refineListedBounded"      # src/gpu/refine_bounded.slang
        res = (self._load(stem, ptx_file, fn_name, wg), wg)
        self._pipelines[key] = res
        return res

    def _load(self, stem, ptx_file, fn_name, wg):
        """Load (once) a PTX module and return one of its functions."""
        if stem not in self._modules:
            self._bind()
            mod = ctypes.c_void_p()
            ptx_bytes = ptx_file.read_bytes() + b"\0"
            # A block of wg threads must fit the SM's 64K-register file, or the
            # launch fails with CUDA_ERROR_LAUNCH_OUT_OF_RESOURCES: cap the JIT's
            # allocation at 65536 / wg (64 at 1024 threads, 128 at 512).
            cap = min(255, (65536 // max(wg, 1)) // 8 * 8)
            if cap < 255 and hasattr(self.cuda, "cuModuleLoadDataEx"):
                options = (ctypes.c_int * 1)(0)  # CU_JIT_MAX_REGISTERS
                values = (ctypes.c_void_p * 1)(ctypes.c_void_p(cap))
                check_cuda(
                    self.cuda.cuModuleLoadDataEx(ctypes.byref(mod), ptx_bytes, 1, options, values),
                    f"cuModuleLoadDataEx({stem})",
                )
            else:
                check_cuda(
                    self.cuda.cuModuleLoadData(ctypes.byref(mod), ptx_bytes),
                    f"cuModuleLoadData({stem})",
                )
            self._modules[stem] = mod
        hfunc = ctypes.c_void_p()
        check_cuda(
            self.cuda.cuModuleGetFunction(ctypes.byref(hfunc), self._modules[stem],
                                          fn_name.encode("utf-8")),
            f"cuModuleGetFunction({fn_name})",
        )
        self._labels[hfunc.value] = stem
        return hfunc

    _TC_ENTRY = {"corr1": "tcStage1", "corr2": "tcFullStage3",
                 "corr_series2": "tcFullSeriesStage3",
                 "fwd1": "tcForwardStage1", "fwd2": "tcForwardStage3"}

    def _tierc(self, n, role):
        """A two-stage (Tier C) kernel past 65536: (function, threads, n1, n2)."""
        key = ("tierc", n, role)
        if key not in self._pipelines:
            info = _manifest().get("full_tierc", {}).get(str(n))
            if info is None or role not in info:
                raise UnsupportedSize(f"no two-stage CUDA kernel for n={n}")
            f = info[role]
            wg = int(f["local_size"][0])
            fn = self._load(f["file"][:-4], _PTX_DIR / f["file"], self._TC_ENTRY[role], wg)
            self._pipelines[key] = (fn, wg, int(info["n1"]), int(info["n2"]))
        return self._pipelines[key]

    def kernel_info(self, n, entry="fusedTierB", **kw):
        """Registers, static shared memory, local (spill) bytes and occupancy of one kernel."""
        fn, wg = self.pipeline(n, entry, **kw)
        out = {"stem": self._labels[fn.value], "threads": wg}
        if hasattr(self.cuda, "cuFuncGetAttribute"):
            for name, attr in (("registers", _FUNC_ATTR_NUM_REGS),
                               ("shared_bytes", _FUNC_ATTR_SHARED),
                               ("local_bytes", _FUNC_ATTR_LOCAL),
                               ("max_threads", _FUNC_ATTR_MAX_THREADS)):
                v = ctypes.c_int(0)
                self.cuda.cuFuncGetAttribute(ctypes.byref(v), attr, fn)
                out[name] = v.value
        out["blocks_per_sm"] = self._blocks_per_sm(fn, wg)
        return out

    def _blocks_per_sm(self, fn, wg):
        key = fn.value
        if key not in self._occupancy:
            v = ctypes.c_int(0)
            if hasattr(self.cuda, "cuOccupancyMaxActiveBlocksPerMultiprocessor"):
                check_cuda(self.cuda.cuOccupancyMaxActiveBlocksPerMultiprocessor(
                    ctypes.byref(v), fn, int(wg), 0), "cuOccupancyMaxActiveBlocksPerMultiprocessor")
            self._occupancy[key] = max(1, v.value)
        return self._occupancy[key]

    def _launch(self, hfunc, grid_dim, block_dim, params, shared_mem=0, stream=None, label=None):
        if (grid_dim if not isinstance(grid_dim, tuple) else grid_dim[0]) <= 0:
            return
        param_ptrs = (ctypes.c_void_p * len(params))(
            *[ctypes.c_void_p(ctypes.addressof(p)) for p in params]
        )
        gx, gy, gz = grid_dim if isinstance(grid_dim, tuple) else (grid_dim, 1, 1)
        bx, by, bz = block_dim if isinstance(block_dim, tuple) else (block_dim, 1, 1)
        st = self.stream if stream is None else stream
        tok = self._mark(st)
        check_cuda(
            self.cuda.cuLaunchKernel(hfunc, gx, gy, gz, bx, by, bz, shared_mem, st,
                                     param_ptrs, None),
            "cuLaunchKernel",
        )
        if tok is not None:
            self._close(tok, st, label or self._labels.get(hfunc.value, "kernel"))

    def empty_shared(self, shape, dtype=np.complex64, *, readback=False):
        factory = (lambda ctx, size: _HostBuffer(ctx, size, readback=True)) if readback else _HostBuffer
        return empty_shared(self, factory, shape, dtype)

    # ---- cache ----------------------------------------------------------------
    def _cached_buffers(self):
        for table in (self._batches, self._hier, self._full_batches, self._forwards):
            for rec in table.values():
                yield from _owned(rec.values() if hasattr(rec, "values") else rec)

    def _evict_record(self, kind, key, keep_storage=None):
        table = {"flat": self._batches, "hier": self._hier, "full": self._full_batches,
                 "forward": self._forwards}[kind]
        rec = table.pop(key, None)
        if rec is None:
            return
        # A record may still be referenced by enqueued work on any stream.
        self._bind()
        check_cuda(self.cuda.cuCtxSynchronize(), "cuCtxSynchronize")
        for b in _owned(rec.values() if hasattr(rec, "values") else rec):
            b.destroy()
        for name in ("data", "tmpl"):
            self._uploaded[name].pop(key, None)

    def _record(self, kind, table, key, estimate, make):
        """The cached record for ``key``, building it (after LRU eviction) if absent."""
        rec = table.get(key)
        fresh = rec is None
        if fresh:
            self._cache_room(estimate)
            rec = make()
            table[key] = rec
        self._cache_touch(kind, key)
        return rec, fresh

    def _grow(self, rec, name, nbytes, cls, stream):
        """Ensure rec[name] holds at least nbytes, growing geometrically. Returns True if
        it was (re)allocated -- its contents are then undefined."""
        cur = rec.get(name)
        if cur is not None and (isinstance(cur, _Borrowed) or cur.nbytes >= nbytes):
            return False
        if cur is not None:
            self._sync(stream)            # enqueued work may still use the old allocation
            cur.destroy()
        rec[name] = cls(self, max(int(nbytes), 64) if cur is None else max(int(nbytes), 2 * cur.nbytes))
        return True

    def _flat_record(self, key, n, nd, nt, out, dsh, tsh, stream):
        """The flat-filter record for (n, templates, slot, shared inputs), sized by
        capacity: a call with another block or bin count reuses it (growing it if
        needed) instead of allocating a record per shape. Returns (record, fresh)."""
        estimate = (0 if dsh else nd * n * 8) + (0 if tsh else nt * n * 8) + out * 24
        rec, fresh = self._record("flat", self._batches, key, estimate, _Record)
        if dsh is not None:
            rec["data"] = dsh
        elif self._grow(rec, "data", nd * n * 8, _Buffer, stream):
            fresh = True
        if tsh is not None:
            rec["tmpl"] = tsh
        elif self._grow(rec, "tmpl", nt * n * 8, _Buffer, stream):
            fresh = True
        self._grow(rec, "idx", out * 4, _Buffer, stream)
        self._grow(rec, "val", out * 8, _Buffer, stream)
        self._grow(rec, "host", out * 12, _Pinned, stream)
        return rec, fresh

    def _results(self, host, nd, nt, nbins):
        out = nd * nt * nbins
        idx = host.view(np.int32, out).reshape(nd, nt, nbins).copy()
        val = host.view(np.complex64, out, offset=out * 4).reshape(nd, nt, nbins).copy()
        return idx, val

    # ---- flat ------------------------------------------------------------------
    def peaks(self, n, data, tmpl, binsize=None, threshold=0.0, window=None,
              upload_data=True, upload_tmpl=True, _groups=None,
              slot=None, async_submit=False):
        self._bind()
        nd, nt = data.shape[0], tmpl.shape[0]
        lo, hi = (0, n) if window is None else (int(window[0]), int(window[1]))
        lo, hi = max(0, min(lo, n)), max(0, min(hi, n))
        if lo >= hi:
            raise ValueError(f"empty window ({lo}, {hi})")
        binsize = n if binsize is None else int(binsize)
        if binsize < 1:
            raise ValueError("binsize must be >= 1")
        nbins = -(-(hi - lo) // binsize)
        if nbins > _MAX_BINS:
            span = _MAX_BINS * binsize
            pi, pv = [], []
            for a in range(lo, hi, span):
                i2, v2 = self.peaks(n, data, tmpl, binsize=binsize,
                                    threshold=threshold,
                                    window=(a, min(a + span, hi)),
                                    upload_data=upload_data,
                                    upload_tmpl=upload_tmpl, slot=slot)
                pi.append(i2)
                pv.append(v2)
                upload_data = upload_tmpl = False
            res = (np.concatenate(pi, axis=2), np.concatenate(pv, axis=2))
            return (lambda: res) if async_submit else res

        t2 = float(threshold) ** 2 if threshold > 0 else 0.0
        stream = self.get_stream(slot)
        self._after_forwards(stream)
        dsh, tsh = shared_buffer(data, self), shared_buffer(tmpl, self)
        key = (n, nt, slot, dsh and data.ctypes.data, tsh and tmpl.ctypes.data)
        upload_data, upload_tmpl, dsig, tsig = self._input_uploads(
            key, data, tmpl, upload_data, upload_tmpl)
        out = nd * nt * nbins
        bufs, fresh = self._flat_record(key, n, nd, nt, out, dsh, tsh, stream)
        if fresh:
            upload_data = upload_tmpl = True
        if upload_data:
            self._upload(bufs["data"], data, stream)
            self._uploaded["data"][key] = dsig
        if upload_tmpl:
            self._upload(bufs["tmpl"], tmpl, stream)
            self._uploaded["tmpl"][key] = tsig

        hfunc, wg = self.pipeline(n, "fusedTierB", one_bin=(nbins == 1))
        params = [bufs["data"].dptr, bufs["tmpl"].dptr, bufs["idx"].dptr, bufs["val"].dptr,
                  _u32(nt), _u32(lo), _u32(hi), _u32(binsize), _i32(_shift(binsize)),
                  _u32(nbins), _f32bits(t2)]
        self._launch(hfunc, nd * nt, wg, params, stream=stream)
        host = bufs["host"]
        self._copy_d2h(host.ptr, bufs["idx"].dptr.value, out * 4, stream, "readback")
        self._copy_d2h(host.ptr + out * 4, bufs["val"].dptr.value, out * 8, stream, "readback")

        def readback():
            self._sync(stream)
            return self._results(host, nd, nt, nbins)
        if async_submit:
            return readback
        return readback()

    def peaks_grouped(self, n, data, tmpl, groups, binsize, threshold, *, upload_tmpl=True,
                      slot=None, async_submit=False):
        """Distinct flat search windows over row ranges of one spectra batch: one sync.

        ``groups`` holds (lo, hi, a, b): rows a..b of ``data`` are searched over
        the window [lo, hi). Every group shares one bin count (the first group's).
        """
        self._bind()
        nd, nt = data.shape[0], tmpl.shape[0]
        groups = tuple((int(lo), int(hi), int(a), int(b)) for lo, hi, a, b in groups)
        binsize = int(binsize)
        nb = (groups[0][1] - groups[0][0] - 1) // binsize + 1
        if nb > _MAX_BINS:
            raise ValueError("grouped dispatch exceeds the kernel bin limit")
        for lo, hi, a, b in groups:
            if not (0 <= lo < hi <= n) or not (0 <= a < b <= nd):
                raise ValueError(f"invalid group ({lo}, {hi}, {a}, {b})")
            if (hi - lo - 1) // binsize + 1 > nb:
                raise ValueError("grouped windows must not exceed the first group's bin count")
        t2 = float(threshold) ** 2 if threshold > 0 else 0.0
        stream = self.get_stream(slot)
        self._after_forwards(stream)
        dsh, tsh = shared_buffer(data, self), shared_buffer(tmpl, self)
        key = (n, nt, slot, dsh and data.ctypes.data, tsh and tmpl.ctypes.data)
        upload_data, upload_tmpl, dsig, tsig = self._input_uploads(
            key, data, tmpl, True, upload_tmpl)
        out = nd * nt * nb
        bufs, fresh = self._flat_record(key, n, nd, nt, out, dsh, tsh, stream)
        if fresh:
            upload_tmpl = True
        # Grouped spectra are a fresh forward batch on every call.
        self._upload(bufs["data"], data, stream)
        if upload_tmpl:
            self._upload(bufs["tmpl"], tmpl, stream)
            self._uploaded["tmpl"][key] = tsig
        covered = np.zeros(nd, bool)
        for _, _, a, b in groups:
            covered[a:b] = True
        if not covered.all():
            self._fill32(bufs["idx"].dptr, 0xFFFFFFFF, out, stream)
            self._fill32(bufs["val"].dptr, 0, out * 2, stream)
        hfunc, wg = self.pipeline(n, "fusedTierB", one_bin=(nb == 1))
        d0, i0, v0 = bufs["data"].dptr.value, bufs["idx"].dptr.value, bufs["val"].dptr.value
        for lo, hi, a, b in groups:
            params = [_ptr(d0 + a * n * 8), bufs["tmpl"].dptr,
                      _ptr(i0 + a * nt * nb * 4), _ptr(v0 + a * nt * nb * 8),
                      _u32(nt), _u32(lo), _u32(hi), _u32(binsize), _i32(_shift(binsize)),
                      _u32(nb), _f32bits(t2)]
            self._launch(hfunc, (b - a) * nt, wg, params, stream=stream)
        host = bufs["host"]
        self._copy_d2h(host.ptr, i0, out * 4, stream, "readback")
        self._copy_d2h(host.ptr + out * 4, v0, out * 8, stream, "readback")

        def readback():
            self._sync(stream)
            return self._results(host, nd, nt, nb)
        if async_submit:
            return readback
        return readback()

    # ---- full correlation --------------------------------------------------------
    def _full_inputs(self, kind, n, data, tmpl, upload_data, upload_tmpl, stream):
        nd, nt = data.shape[0], tmpl.shape[0]
        dsh, tsh = shared_buffer(data, self), shared_buffer(tmpl, self)
        key = (kind, n, nd, nt, dsh and data.ctypes.data, tsh and tmpl.ctypes.data)
        upload_data, upload_tmpl, dsig, tsig = self._input_uploads(
            key, data, tmpl, upload_data, upload_tmpl)
        estimate = (0 if dsh else data.nbytes) + (0 if tsh else tmpl.nbytes)
        bufs, fresh = self._record("full", self._full_batches, key, estimate, lambda: {
            "data": dsh or _Buffer(self, nd * n * 8),
            "tmpl": tsh or _Buffer(self, nt * n * 8),
        })
        if fresh:
            upload_data = upload_tmpl = True
        if upload_data:
            self._upload(bufs["data"], data, stream)
            self._uploaded["data"][key] = dsig
        if upload_tmpl:
            self._upload(bufs["tmpl"], tmpl, stream)
            self._uploaded["tmpl"][key] = tsig
        return key, bufs

    def _scratch(self, key, name, nbytes):
        """A reusable device scratch buffer in a full-correlation record."""
        bufs = self._full_batches[key]
        s = bufs.get(name)
        if s is None or s.nbytes < nbytes:
            if s is not None:
                self._sync()
                s.destroy()
            s = bufs[name] = _Buffer(self, nbytes)
        return s

    def correlate(self, n, data, tmpl, out, *, upload_data=True, upload_tmpl=True):
        """Full circular correlation in natural lag order: out[d, t, lag]."""
        self._bind()
        nd, nt = data.shape[0], tmpl.shape[0]
        if out.shape != (nd, nt, n) or out.dtype != np.complex64 or not out.flags.c_contiguous:
            raise ValueError("out must be a C-contiguous complex64 (%d, %d, %d) array" % (nd, nt, n))
        stream = self.stream
        key, bufs = self._full_inputs("full", n, data, tmpl, upload_data, upload_tmpl, stream)
        dptr, tptr = bufs["data"].dptr.value, bufs["tmpl"].dptr.value
        osh = shared_buffer(out, self)
        tierc = n > 65536
        if tierc:
            s1, s1wg, n1, n2 = self._tierc(n, "corr1")
            s3, s3wg, _, _ = self._tierc(n, "corr2")
        else:
            hfunc, wg = self.pipeline(n, "fullCorrelation")
        if osh is not None and not tierc:
            self._launch(hfunc, nd * nt, wg,
                         [_ptr(dptr), _ptr(tptr), osh.dptr, _u32(nt)], stream=stream)
            self._sync(stream)
            return out
        # Tiled, so device scratch stays bounded. A tile is a run of whole data
        # rows, or a run of templates within one row; either way its output is
        # one contiguous span of ``out``. Tier C also needs its inter-stage
        # scratch per tile.
        tiles = self._tiles(nd, nt, n * 8)
        most = max((d1 - d0) * (t1 - t0) for d0, d1, t0, t1 in tiles) * n * 8
        flat = out.reshape(-1)
        for d0, d1, t0, t1 in tiles:
            k = t1 - t0
            pairs = (d1 - d0) * k
            start = (d0 * nt + t0) * n
            if osh is not None:
                dst = osh.dptr.value + start * 8
            else:
                dst = self._scratch(key, "stage", most).dptr.value
            args = [_ptr(dptr + d0 * n * 8), _ptr(tptr + t0 * n * 8)]
            if tierc:
                mid = self._scratch(key, "tierc", most)
                self._launch(s1, pairs * n1, s1wg, args + [mid.dptr, _u32(k)], stream=stream)
                self._launch(s3, pairs * n2, s3wg, [mid.dptr, _ptr(dst)], stream=stream)
            else:
                self._launch(hfunc, pairs, wg, args + [_ptr(dst), _u32(k)], stream=stream)
            if osh is None:
                self._copy_d2h(flat[start:start + pairs * n].ctypes.data, dst,
                               pairs * n * 8, stream, "readback")
                # The staging buffer is reused by the next tile.
                self._sync(stream)
        self._sync(stream)
        return out

    @staticmethod
    def _tiles(nd, nt, pair_bytes):
        """(d0, d1, t0, t1) tiles of at most _TILE_BYTES of per-pair working storage."""
        row = nt * pair_bytes
        if row <= _TILE_BYTES:
            rows = max(1, _TILE_BYTES // row)
            return [(d0, min(d0 + rows, nd), 0, nt) for d0 in range(0, nd, rows)]
        per = max(1, _TILE_BYTES // pair_bytes)
        return [(d, d + 1, t0, min(t0 + per, nt)) for d in range(nd) for t0 in range(0, nt, per)]

    def correlate_continuous(self, n, data, tmpl, starts, out, lo, hi,
                             *, upload_data=True, upload_tmpl=True):
        """Full correlation written at continuous absolute series offsets: out[t, start + lag]."""
        self._bind()
        nd, nt = data.shape[0], tmpl.shape[0]
        if out.ndim != 2 or out.shape[0] != nt or out.dtype != np.complex64 or not out.flags.c_contiguous:
            raise ValueError("out must be a C-contiguous complex64 (templates, samples) array")
        stream = self.stream
        key, bufs = self._full_inputs("full_series", n, data, tmpl, upload_data, upload_tmpl, stream)
        starts = np.ascontiguousarray(starts, np.uint32)
        ssh = self._small_input("cstarts", starts, stream)
        S = out.shape[1]
        osh = shared_buffer(out, self)
        tierc = n > 65536
        if tierc:
            s1, s1wg, n1, n2 = self._tierc(n, "corr1")
            s3, s3wg, _, _ = self._tierc(n, "corr_series2")
        else:
            hfunc, wg = self.pipeline(n, "fullCorrelationSeries")
        if osh is None:
            # Into a host array: only the span these blocks write is staged and
            # copied, so the rest of ``out`` (written by other calls) is untouched.
            w0 = int(starts.min()) + int(lo)
            w1 = min(S, int(starts.max()) + int(hi))
            if w1 <= w0:
                return out
            span = w1 - w0
            stage = self._scratch(key, "stage", nt * span * 8)
            # Rebase the starts onto the span: the kernel writes at t*span + start + lag.
            rebased = (starts.astype(np.int64) - (w0 - int(lo))).astype(np.uint32)
            rb = bufs.get("rebased")
            if rb is None or rb.nbytes < rebased.nbytes:
                rb = bufs["rebased"] = _Buffer(self, max(rebased.nbytes, 4))
            rb.write(rebased, stream)
            for t in range(nt):     # lags outside [lo, hi) keep their current values
                self._copy_h2d(stage.dptr.value + t * span * 8, out[t, w0:w1].ctypes.data,
                               span * 8, stream, "upload")
            dst, length, sptr = stage.dptr.value, span, rb.dptr.value
        else:
            dst, length, sptr = osh.dptr.value, S, ssh.dptr.value
        dptr, tptr = bufs["data"].dptr.value, bufs["tmpl"].dptr.value
        if tierc:
            tiles = self._tiles(nd, nt, n * 8)
            most = max((d1 - d0) * (t1 - t0) for d0, d1, t0, t1 in tiles) * n * 8
            for d0, d1, t0, t1 in tiles:
                k = t1 - t0
                pairs = (d1 - d0) * k
                mid = self._scratch(key, "tierc", most)
                self._launch(s1, pairs * n1, s1wg,
                             [_ptr(dptr + d0 * n * 8), _ptr(tptr + t0 * n * 8), mid.dptr, _u32(k)],
                             stream=stream)
                self._launch(s3, pairs * n2, s3wg,
                             [mid.dptr, _ptr(sptr + d0 * 4), _ptr(dst + t0 * length * 8),
                              _uint4(k, length, lo, hi)], stream=stream)
        else:
            self._launch(hfunc, nd * nt, wg,
                         [_ptr(dptr), _ptr(tptr), _ptr(sptr), _ptr(dst),
                          _uint4(nt, length, lo, hi)], stream=stream)
        if osh is None:
            for t in range(nt):
                self._copy_d2h(out[t, w0:w1].ctypes.data, dst + t * length * 8,
                               length * 8, stream, "readback")
        self._sync(stream)
        return out

    def zero_columns(self, dest, a, b):
        """Zero dest[:, a:b] of a GPU-shared 2-D array on the device (enqueued).

        Call zero_columns_done() after the last one: it waits, so work on another
        Context's stream sees the zeros."""
        sb = shared_buffer(dest, self)
        if sb is None or dest.ndim != 2 or b <= a:
            raise ValueError("zero_columns needs a GPU-shared 2-D array and a nonempty range")
        width = (b - a) * dest.itemsize // 4
        self._bind()
        check_cuda(self.cuda.cuMemsetD2D32Async(sb.dptr.value + a * dest.itemsize, dest.strides[0],
                                                0, width, dest.shape[0], self.stream),
                   "cuMemsetD2D32Async")

    def zero_columns_done(self):
        self._sync(self.stream)

    # ---- hierarchical ---------------------------------------------------------------
    def _coarse_kernel(self, band, nt):
        """The coarse gate kernel for ``band``: (fn, threads, ppg, tile, c16).

        PPG pairs per block and TILE_T templates per pair-group are compiled in. The
        choice is the shipped variant with the highest theoretical occupancy on this
        device (threads resident per SM), ties to the larger group. A tile walks
        TILE_T consecutive templates of one data row, so it needs nt % TILE_T == 0;
        a partial PPG group is handled by padding the data rows (hier_peaks)."""
        if not _use_c16(band):
            fn, wg = self.pipeline(band, "fusedTierB")
            return fn, wg, 1, 1, False
        key = ("coarse_choice", band, nt % max(_COARSE_TILE_T.get(band, 1), 1) == 0)
        if key not in self._pipelines:
            best = None
            tiles = (1, _COARSE_TILE_T[band]) if (band in _COARSE_TILE_T and key[2]) else (1,)
            for tile in tiles:
                for ppg in (1, 2, 4, 8, 16):
                    if ppg > 1 and band // 16 * ppg > 1024:
                        continue
                    try:
                        fn, wg = self.pipeline(band, "fusedTierB", c16=True, ppg=ppg, tile=tile)
                    except UnsupportedSize:
                        continue
                    resident = self._blocks_per_sm(fn, wg) * wg
                    score = (resident, ppg * tile)
                    if best is None or score > best[0]:
                        best = (score, fn, wg, ppg, tile)
            if best is None:
                raise UnsupportedSize(f"no coarse c16 kernel for band {band}")
            self._pipelines[key] = best[1:]
        fn, wg, ppg, tile = self._pipelines[key]
        return fn, wg, ppg, tile, True

    def _refine_grid(self, fn, wg, pairs):
        return max(1, min(pairs, self._blocks_per_sm(fn, wg) * self.sm_count))

    def hier_peaks(self, n, band, data, tmpl, ct0, raw_thr, binsize=None,
                   threshold=0.0, window=None, upload_data=True, upload_tmpl=True,
                   cascade_band=None, ct1=None, raw_thr1=None,
                   slot=None, async_submit=False):
        """Hierarchical coarse-to-fine peaks, one or two coarse tiers, one sync.

        Single tier: ``band``/``ct0``/``raw_thr``. Two tiers (the Vulkan
        convention): tier 0 is ``cascade_band`` with ``ct0``/``raw_thr``, tier 1
        is ``band`` with ``ct1``/``raw_thr1``.
        """
        self._bind()
        if isinstance(band, (tuple, list)):
            cascade_band, band = band[0], band[1]
        if isinstance(ct0, (tuple, list)):
            ct0, ct1 = ct0[0], ct0[1]
        if isinstance(raw_thr, (tuple, list)):
            raw_thr, raw_thr1 = raw_thr[0], raw_thr[1]
        cascade = cascade_band is not None
        if cascade and (ct1 is None or raw_thr1 is None):
            raise ValueError("a two-tier chain needs ct1 and raw_thr1")
        nd, nt = data.shape[0], tmpl.shape[0]
        pairs = nd * nt
        lo, hi = (0, n) if window is None else (int(window[0]), int(window[1]))
        lo, hi = max(0, min(lo, n)), max(0, min(hi, n))
        if lo >= hi:
            raise ValueError(f"empty window ({lo}, {hi})")
        binsize = n if binsize is None else int(binsize)
        nbins = -(-(hi - lo) // binsize)
        if nbins > _MAX_BINS:
            span = _MAX_BINS * binsize
            pi, pv = [], []
            for a in range(lo, hi, span):
                i2, v2 = self.hier_peaks(n, band, data, tmpl, ct0, raw_thr,
                                         binsize=binsize, threshold=threshold,
                                         window=(a, min(a + span, hi)),
                                         upload_data=upload_data, upload_tmpl=upload_tmpl,
                                         cascade_band=cascade_band, ct1=ct1, raw_thr1=raw_thr1,
                                         slot=slot)
                pi.append(i2)
                pv.append(v2)
                upload_data = upload_tmpl = False
            res = (np.concatenate(pi, axis=2), np.concatenate(pv, axis=2))
            return (lambda: res) if async_submit else res

        band0 = int(cascade_band) if cascade else int(band)
        band1 = int(band) if cascade else None
        if ct0.shape != (nt, band0):
            raise ValueError(f"tier-0 coarse templates must be ({nt}, {band0}), got {ct0.shape}")
        if cascade and ct1.shape != (nt, band1):
            raise ValueError(f"tier-1 coarse templates must be ({nt}, {band1}), got {ct1.shape}")
        t2 = float(threshold) ** 2 if threshold > 0 else 0.0
        stream = self.get_stream(slot)
        self._after_forwards(stream)
        dsh, tsh = shared_buffer(data, self), shared_buffer(tmpl, self)
        # Keyed without block or bin counts: buffers are sized by capacity and grow,
        # so windowed calls of varying size reuse one record (no per-shape churn).
        key = (n, band0, band1, nt, slot, dsh and data.ctypes.data, tsh and tmpl.ctypes.data)
        tmpl_dirty = upload_tmpl
        upload_data, upload_tmpl, dsig, tsig = self._input_uploads(
            key, data, tmpl, upload_data, upload_tmpl)
        c16 = _use_c16(band0)
        cb0 = 4 if c16 else 8
        out = nd * nt * nbins
        cfn, cwg, ppg, tile, _ = self._coarse_kernel(band0, nt)
        group = ppg * tile
        # Data rows padded so the pair count fills whole groups. The padding pairs'
        # coarse values land past `pairs`, which the compaction never reads.
        ndp = nd
        while (ndp * nt) % group:
            ndp += 1
        estimate = ((0 if dsh else nd * n * 8) + (0 if tsh else nt * n * 8)
                    + (nd + nt) * (band0 * cb0 + (band1 or 0) * 8) + pairs * 40 + out * 24)
        bufs, fresh = self._record("hier", self._hier, key, estimate, dict)
        sizes = [("cdata0", ndp * band0 * cb0, _Buffer), ("cidx0", ndp * nt * 4, _Buffer),
                 ("cval0", ndp * nt * 8, _Buffer), ("surv0", pairs * 4, _Buffer),
                 ("args", 16, _Buffer), ("idx", out * 4, _Buffer), ("val", out * 8, _Buffer),
                 ("host", out * 12 + 16, _Pinned)]
        if cascade:
            sizes += [("cdata1", nd * band1 * 8, _Buffer), ("cidx1", pairs * 4, _Buffer),
                      ("cval1", pairs * 8, _Buffer), ("surv1", pairs * 4, _Buffer)]
        for name, nbytes, cls in sizes:
            if self._grow(bufs, name, nbytes, cls, stream) and name.startswith("cdata"):
                upload_data = True           # its packed copy of the data is gone
        if dsh is not None:
            bufs["data"] = dsh
        elif self._grow(bufs, "data", nd * n * 8, _Buffer, stream):
            fresh = True
        if fresh:
            upload_data = True
        bufs["tmpl"] = tsh or self._resident("tmpl", tmpl, tmpl_dirty, stream)
        bufs["ct0"] = self._resident(("ct", band0, c16), ct0, tmpl_dirty, stream,
                                     _pack_half2 if c16 else None)
        if cascade:
            bufs["ct1"] = self._resident(("ct", band1, False), ct1, tmpl_dirty, stream)
        upload_tmpl = False                  # the residents above handled the templates

        if upload_data:
            self._upload(bufs["data"], data, stream)
            if dsh is None:
                bufs["cdata0"].write(_pack_half2(data[:, :band0]) if c16
                                     else np.ascontiguousarray(data[:, :band0], np.complex64), stream)
                if cascade:
                    bufs["cdata1"].write(np.ascontiguousarray(data[:, :band1], np.complex64), stream)
            self._uploaded["data"][key] = dsig
        if upload_tmpl:
            self._upload(bufs["tmpl"], tmpl, stream)
            bufs["ct0"].write(_pack_half2(ct0) if c16 else np.ascontiguousarray(ct0, np.complex64),
                              stream)
            if cascade:
                bufs["ct1"].write(np.ascontiguousarray(ct1, np.complex64), stream)
            self._uploaded["tmpl"][key] = tsig

        args = bufs["args"].dptr.value
        self._fill32(_ptr(args), 0, 4, stream)
        self._fill32(bufs["idx"].dptr, 0xFFFFFFFF, out, stream)
        self._fill32(bufs["val"].dptr, 0, out * 2, stream)

        if dsh is not None:
            # Coarse bands straight from the device spectra.
            pack_fn, pack_wg = self.pipeline(4096, "packCoarse")
            for name, b, packed in (("cdata0", band0, int(c16)),) + (
                    (("cdata1", band1, 0),) if cascade else ()):
                self._launch(pack_fn, (nd * b + 255) // 256, 256,
                             [bufs["data"].dptr, bufs[name].dptr, _u32(n), _u32(b),
                              _u32(nd * b), _u32(packed)], stream=stream)

        # Tier 0: the coarse gate over every pair (and the padding rows' pairs).
        cs, ce, csp, csh = _coarse_span(n, band0, lo, hi)
        self._launch(cfn, ndp * nt // group, cwg,
                     [bufs["cdata0"].dptr, bufs["ct0"].dptr, bufs["cidx0"].dptr,
                      bufs["cval0"].dptr, _u32(nt), _u32(cs), _u32(ce), _u32(csp),
                      _i32(csh), _u32(1), _u32(0)], stream=stream)
        kfn, _ = self.pipeline(band0, "compactPairs")
        cpt = (pairs + 255) // 256
        if cascade:
            # Tier 0 compaction counts into args[1]; tier 1 refines those pairs at
            # band1 (one bin over its coarse window) and compacts into args[0].
            self._fill32(bufs["cval1"].dptr, 0, pairs * 2, stream)
            self._launch(kfn, cpt, 256, [bufs["cval0"].dptr, bufs["surv0"].dptr, _ptr(args + 4),
                                         _u32(pairs), ctypes.c_float(float(raw_thr)), _u32(nbins)],
                         stream=stream)
            r1, r1wg = self.pipeline(band1, "refineListed", one_bin=True)
            cs1, ce1, csp1, csh1 = _coarse_span(n, band1, lo, hi)
            g1 = self._refine_grid(r1, r1wg, pairs)
            self._launch(r1, g1, r1wg,
                         [bufs["cdata1"].dptr, bufs["ct1"].dptr, bufs["cidx1"].dptr,
                          bufs["cval1"].dptr, bufs["surv0"].dptr, _ptr(args + 4),
                          _u32(nt), _u32(cs1), _u32(ce1), _u32(csp1), _i32(csh1), _u32(1),
                          _u32(0), _u32(g1)], stream=stream, label=f"tier1_{band1}")
            self._launch(kfn, cpt, 256, [bufs["cval1"].dptr, bufs["surv1"].dptr, _ptr(args),
                                         _u32(pairs), ctypes.c_float(float(raw_thr1)), _u32(nbins)],
                         stream=stream)
            surv = bufs["surv1"]
        else:
            self._launch(kfn, cpt, 256, [bufs["cval0"].dptr, bufs["surv0"].dptr, _ptr(args),
                                         _u32(pairs), ctypes.c_float(float(raw_thr)), _u32(nbins)],
                         stream=stream)
            surv = bufs["surv0"]

        rfn, rwg = self.pipeline(n, "refineListed", one_bin=(nbins == 1))
        g = self._refine_grid(rfn, rwg, pairs)
        self._launch(rfn, g, rwg,
                     [bufs["data"].dptr, bufs["tmpl"].dptr, bufs["idx"].dptr, bufs["val"].dptr,
                      surv.dptr, _ptr(args), _u32(nt), _u32(lo), _u32(hi), _u32(binsize),
                      _i32(_shift(binsize)), _u32(nbins), _f32bits(t2), _u32(g)], stream=stream)

        host = bufs["host"]
        self._copy_d2h(host.ptr, bufs["idx"].dptr.value, out * 4, stream, "readback")
        self._copy_d2h(host.ptr + out * 4, bufs["val"].dptr.value, out * 8, stream, "readback")
        self._copy_d2h(host.ptr + out * 12, args, 8, stream, "readback")

        def readback():
            self._sync(stream)
            counts = host.view(np.uint32, 2, offset=out * 12)
            self.last_refinements = int(counts[0])
            self.last_tier1_survivors = int(counts[1]) if cascade else int(counts[0])
            return self._results(host, nd, nt, nbins)
        if async_submit:
            return readback
        return readback()

    def hier_peaks_grouped(self, n, band, data, tmpl, ct0, raw_thr, groups, binsize, threshold,
                           *, upload_tmpl=True, cascade_band=None, ct1=None, raw_thr1=None,
                           slot=None, async_submit=False):
        """Hierarchical peaks over row ranges of one spectra batch, each with its own
        window -- every group in ONE submission and one sync (plan D2).

        ``groups`` holds (lo, hi, a, b): rows a..b of ``data`` are searched over
        [lo, hi). A series call has a first and a last block whose windows differ
        from the interior blocks', so per-group calls cost two extra round trips per
        call for one block of work each. Tiers as in hier_peaks.
        """
        self._bind()
        cascade = cascade_band is not None
        if cascade and (ct1 is None or raw_thr1 is None):
            raise ValueError("a two-tier chain needs ct1 and raw_thr1")
        nd, nt = data.shape[0], tmpl.shape[0]
        groups = tuple((int(lo), int(hi), int(a), int(b)) for lo, hi, a, b in groups)
        binsize = int(binsize)
        nb = (groups[0][1] - groups[0][0] - 1) // binsize + 1
        if nb > _MAX_BINS:
            raise ValueError("grouped dispatch exceeds the kernel bin limit")
        for lo, hi, a, b in groups:
            if not (0 <= lo < hi <= n) or not (0 <= a < b <= nd):
                raise ValueError(f"invalid group ({lo}, {hi}, {a}, {b})")
            if (hi - lo - 1) // binsize + 1 > nb:
                raise ValueError("grouped windows must not exceed the first group's bin count")
        band0 = int(cascade_band) if cascade else int(band)
        band1 = int(band) if cascade else None
        if ct0.shape != (nt, band0) or (cascade and ct1.shape != (nt, band1)):
            raise ValueError("coarse templates do not match the chain's bands")
        t2 = float(threshold) ** 2 if threshold > 0 else 0.0
        stream = self.get_stream(slot)
        self._after_forwards(stream)
        dsh, tsh = shared_buffer(data, self), shared_buffer(tmpl, self)
        if dsh is None:
            raise ValueError("grouped spectra must be GPU-shared (a forward batch)")
        c16 = _use_c16(band0)
        cb0 = 4 if c16 else 8
        cfn, cwg, ppg, tile, _ = self._coarse_kernel(band0, nt)
        unit = ppg * tile
        # Coarse rows in a padded layout: group g at rows off[g].., padded so its pairs
        # fill whole PPG/tile groups. Padding rows hold whatever an earlier call left;
        # their pairs land past the group's own pairs, which is all its compaction reads.
        offs, ndp = [], 0
        for lo, hi, a, b in groups:
            rows = b - a
            while (rows * nt) % unit:
                rows += 1
            offs.append(ndp)
            ndp += rows
        ng = len(groups)
        out = nd * nt * nb
        pairs = nd * nt
        key = ("grouped", n, band0, band1, nt, slot, data.ctypes.data, tsh and tmpl.ctypes.data)
        tmpl_dirty = upload_tmpl
        estimate = ((0 if tsh else nt * n * 8) + nt * (band0 * cb0 + (band1 or 0) * 8)
                    + pairs * 40 + out * 24)
        bufs, fresh = self._record("hier", self._hier, key, estimate, dict)
        bufs["data"] = dsh
        bufs["tmpl"] = tsh or self._resident("tmpl", tmpl, tmpl_dirty, stream)
        bufs["ct0"] = self._resident(("ct", band0, c16), ct0, tmpl_dirty, stream,
                                     _pack_half2 if c16 else None)
        if cascade:
            bufs["ct1"] = self._resident(("ct", band1, False), ct1, tmpl_dirty, stream)
        sizes = [("surv0", pairs * 4, _Buffer),
                 ("idx", out * 4, _Buffer), ("val", out * 8, _Buffer),
                 ("cdata0", ndp * band0 * cb0, _Buffer), ("cidx0", ndp * nt * 4, _Buffer),
                 ("cval0", ndp * nt * 8, _Buffer), ("args", 8 * ng, _Buffer),
                 ("host", out * 12 + 8 * ng, _Pinned)]
        if cascade:
            sizes += [("cdata1", nd * band1 * 8, _Buffer),
                      ("cidx1", pairs * 4, _Buffer), ("cval1", pairs * 8, _Buffer),
                      ("surv1", pairs * 4, _Buffer)]
        for name, nbytes, cls in sizes:
            self._grow(bufs, name, nbytes, cls, stream)

        args = bufs["args"].dptr.value
        self._fill32(_ptr(args), 0, 2 * ng, stream)
        self._fill32(bufs["idx"].dptr, 0xFFFFFFFF, out, stream)
        self._fill32(bufs["val"].dptr, 0, out * 2, stream)
        if cascade:
            self._fill32(bufs["cval1"].dptr, 0, pairs * 2, stream)

        dptr = dsh.dptr.value
        cd0, ci0, cv0 = (bufs[k].dptr.value for k in ("cdata0", "cidx0", "cval0"))
        s0, i0, v0 = bufs["surv0"].dptr.value, bufs["idx"].dptr.value, bufs["val"].dptr.value
        pack_fn, _ = self.pipeline(4096, "packCoarse")
        kfn, _ = self.pipeline(band0, "compactPairs")
        rfn, rwg = self.pipeline(n, "refineListed", one_bin=(nb == 1))
        if cascade:
            self._launch(pack_fn, (nd * band1 + 255) // 256, 256,
                         [_ptr(dptr), bufs["cdata1"].dptr, _u32(n), _u32(band1),
                          _u32(nd * band1), _u32(0)], stream=stream)
            r1, r1wg = self.pipeline(band1, "refineListed", one_bin=True)
            cd1, ci1, cv1 = (bufs[k].dptr.value for k in ("cdata1", "cidx1", "cval1"))
            s1 = bufs["surv1"].dptr.value
        for g, ((lo, hi, a, b), off) in enumerate(zip(groups, offs)):
            gp = (b - a) * nt
            rows = next(r for r in range(b - a, b - a + unit + 1) if (r * nt) % unit == 0)
            cnt_ref, cnt_t1 = _ptr(args + 8 * g), _ptr(args + 8 * g + 4)
            self._launch(pack_fn, ((b - a) * band0 + 255) // 256, 256,
                         [_ptr(dptr + a * n * 8), _ptr(cd0 + off * band0 * cb0), _u32(n),
                          _u32(band0), _u32((b - a) * band0), _u32(int(c16))], stream=stream)
            cs, ce, csp, csh = _coarse_span(n, band0, lo, hi)
            self._launch(cfn, rows * nt // unit, cwg,
                         [_ptr(cd0 + off * band0 * cb0), bufs["ct0"].dptr, _ptr(ci0 + off * nt * 4),
                          _ptr(cv0 + off * nt * 8), _u32(nt), _u32(cs), _u32(ce), _u32(csp),
                          _i32(csh), _u32(1), _u32(0)], stream=stream)
            cpt = (gp + 255) // 256
            if cascade:
                self._launch(kfn, cpt, 256, [_ptr(cv0 + off * nt * 8), _ptr(s0 + a * nt * 4), cnt_t1,
                                             _u32(gp), ctypes.c_float(float(raw_thr)), _u32(nb)],
                             stream=stream)
                cs1, ce1, csp1, csh1 = _coarse_span(n, band1, lo, hi)
                g1 = self._refine_grid(r1, r1wg, gp)
                self._launch(r1, g1, r1wg,
                             [_ptr(cd1 + a * band1 * 8), bufs["ct1"].dptr, _ptr(ci1 + a * nt * 4),
                              _ptr(cv1 + a * nt * 8), _ptr(s0 + a * nt * 4), cnt_t1,
                              _u32(nt), _u32(cs1), _u32(ce1), _u32(csp1), _i32(csh1), _u32(1),
                              _u32(0), _u32(g1)], stream=stream, label=f"tier1_{band1}")
                self._launch(kfn, cpt, 256, [_ptr(cv1 + a * nt * 8), _ptr(s1 + a * nt * 4), cnt_ref,
                                             _u32(gp), ctypes.c_float(float(raw_thr1)), _u32(nb)],
                             stream=stream)
                surv = s1
            else:
                self._launch(kfn, cpt, 256, [_ptr(cv0 + off * nt * 8), _ptr(s0 + a * nt * 4), cnt_ref,
                                             _u32(gp), ctypes.c_float(float(raw_thr)), _u32(nb)],
                             stream=stream)
                surv = s0
            g2 = self._refine_grid(rfn, rwg, gp)
            self._launch(rfn, g2, rwg,
                         [_ptr(dptr + a * n * 8), bufs["tmpl"].dptr, _ptr(i0 + a * nt * nb * 4),
                          _ptr(v0 + a * nt * nb * 8), _ptr(surv + a * nt * 4), cnt_ref, _u32(nt),
                          _u32(lo), _u32(hi), _u32(binsize), _i32(_shift(binsize)), _u32(nb),
                          _f32bits(t2), _u32(g2)], stream=stream)
        host = bufs["host"]
        self._copy_d2h(host.ptr, i0, out * 4, stream, "readback")
        self._copy_d2h(host.ptr + out * 4, v0, out * 8, stream, "readback")
        self._copy_d2h(host.ptr + out * 12, args, 8 * ng, stream, "readback")

        def readback():
            self._sync(stream)
            counts = host.view(np.uint32, 2 * ng, offset=out * 12).reshape(ng, 2)
            self.last_refinements = int(counts[:, 0].sum())
            self.last_tier1_survivors = int(counts[:, 1].sum()) if cascade else self.last_refinements
            return self._results(host, nd, nt, nb)
        if async_submit:
            return readback
        return readback()

    # ---- series forward -----------------------------------------------------------
    def _forward_fused(self, n, series, starts, spectra, *, defer=False, slot=None):
        """Dispatch fused forward FFT kernel path."""
        return self.forward(n, series, starts, spectra, defer=defer, slot=slot, fused=True)

    def forward(self, n, series, starts, spectra, *, defer=False, slot=None, fused=False):
        """Batch forward FFTs of series blocks into ``spectra`` (deferred: no sync)."""
        self._bind()
        stream = self.get_stream(slot)
        tierc = n > 65536
        if tierc:
            f1, f1wg, n1, n2 = self._tierc(n, "fwd1")
            f3, f3wg, _, _ = self._tierc(n, "fwd2")
        else:
            hfunc, wg = self.pipeline(n, "seriesForward")
        sh = [shared_buffer(a, self) for a in (series, starts, spectra)]
        if sh[0] is not None and sh[2] is not None:
            st = np.asarray(starts, dtype=np.int64)
            if st.size:
                lo_ = int(min(st.min(), series.size))
                hi_ = int(min(series.size, st.max() + n))
                self._prefetch(sh[0], lo_ * series.itemsize, (hi_ - lo_) * series.itemsize, stream)
            sh[1] = self._small_input("starts", np.asarray(starts, np.uint32), stream, slot)
        if any(b is None for b in sh):
            key = ("forward", n, series.nbytes, starts.nbytes, spectra.nbytes, slot)
            bufs, _ = self._record("forward", self._forwards, key,
                                   series.nbytes + starts.nbytes + spectra.nbytes, lambda: {
                                       "series": _Buffer(self, series.nbytes),
                                       "starts": _Buffer(self, starts.nbytes),
                                       "spectra": _Buffer(self, spectra.nbytes)})
            sh = [s or bufs[k] for s, k in zip(sh, ("series", "starts", "spectra"))]
            for b, a in zip(sh[:2], (series, starts)):
                if not isinstance(b, _Borrowed):
                    b.write(a, stream)
        blocks = spectra.shape[0]
        if tierc:
            key = ("forward_tierc", n, slot)
            rec, _ = self._record("forward", self._forwards, key, blocks * n * 8, lambda: {})
            mid = rec.get("scratch")
            if mid is None or mid.nbytes < blocks * n * 8:
                if mid is not None:
                    self._sync(stream)
                    mid.destroy()
                mid = rec["scratch"] = _Buffer(self, blocks * n * 8)
            self._launch(f1, blocks * n1, f1wg,
                         [sh[0].dptr, sh[1].dptr, mid.dptr, _u32(series.size)], stream=stream)
            self._launch(f3, blocks * n2, f3wg, [mid.dptr, sh[2].dptr], stream=stream)
        else:
            self._launch(hfunc, blocks, wg,
                         [sh[0].dptr, sh[1].dptr, sh[2].dptr, _u32(series.size)], stream=stream)
        if not isinstance(sh[2], _Borrowed):
            self._copy_d2h(spectra.ctypes.data, sh[2].dptr.value, spectra.nbytes, stream, "readback")
            self._sync(stream)
        elif not defer:
            self._sync(stream)
        else:
            # A consumer may run on another stream (a tiled or unslotted dispatch of these
            # spectra): it must wait for this forward. Recorded here, waited on in _after.
            ev = self._fwd_events.get(stream.value)
            if ev is None:
                ev = self._fwd_events[stream.value] = self._new_event()
            check_cuda(self.cuda.cuEventRecord(ev, stream), "cuEventRecord")

    def cancel_forward(self, slot=None):
        # Launches are already enqueued; the stream orders whatever follows.
        pass

    # ---- lifetime ----------------------------------------------------------------
    def clear_cache(self):
        self._bind()
        if self.ctx.value:
            self.cuda.cuCtxSynchronize()
        for table in (self._batches, self._full_batches, self._hier, self._forwards):
            for rec in table.values():
                for b in _owned(rec.values() if hasattr(rec, "values") else rec):
                    b.destroy()
            table.clear()
        for ent in self._residents.values():
            ent[0].destroy()
        self._residents.clear()
        self._uploaded = {"data": {}, "tmpl": {}}
        self._cache_order = {}

    def destroy(self):
        if not getattr(self, "ctx", None) or not self.ctx.value:
            return
        self._bind()
        self.clear_cache()
        if not self._shared_modules:
            for mod in self._modules.values():
                self.cuda.cuModuleUnload(mod)
            self._modules.clear()
            self._pipelines.clear()
        for _, pending in self._pending_events.items():
            for _, e0, e1 in pending:
                self._event_pool.extend((e0, e1))
        self._pending_events.clear()
        for e in self._event_pool:
            if e.value:
                self.cuda.cuEventDestroy_v2(e)
        for e in self._fwd_events.values():
            if e.value:
                self.cuda.cuEventDestroy_v2(e)
        self._fwd_events.clear()
        self._event_pool.clear()
        for s in self.streams:
            if s.value:
                self.cuda.cuStreamDestroy_v2(s)
                s.value = 0
        self.streams.clear()
        if self._using_primary_ctx:
            self.cuda.cuDevicePrimaryCtxRelease(self.device.value)
        else:
            self.cuda.cuCtxDestroy_v2(self.ctx)
        self.ctx.value = 0

    def __del__(self):
        try:
            self.destroy()
        except Exception:
            pass
