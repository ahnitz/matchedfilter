"""Dispatching the Metal kernels, with ctypes over the Objective-C runtime.

No PyObjC and no compiled helper: the wheel carries kernels, and the only
thing it needs from the machine is Metal itself, which every Mac has.

The calling convention differs from Vulkan and the difference is silent if
got wrong. Slang lowers the entry point's uniform parameters to a CONSTANT
BUFFER at index 0 and shifts the storage buffers to 1..4, where SPIR-V puts
the storage buffers at 0..3 and the uniforms in push constants. The struct
is the same seven 32-bit fields in the same order.

UNTESTED ON LINUX by construction -- there is no Apple hardware on the
development machine, so every line here is exercised only by the macOS CI
job. It is written to fail loudly rather than plausibly.
"""
import ctypes
import os
import pathlib
import sys
from contextlib import contextmanager
from functools import lru_cache, wraps

import numpy as np
from ._shared import empty_shared, shared_buffer, shared_key, write_input
from ._gpuhost import (MAX_BINS, band_forward_wanted, bin_shift, coarse_span, refine_block_fraction,
                       plan_items, split_items, hier_tiers, hier_window,
                       split_bins)
from ._shared import pack_half2 as _pack_half2, sparsified as _sparsified

_HERE = pathlib.Path(__file__).resolve().parent
_METAL_DIR = _HERE / "metal"
_MANIFEST = _HERE / "spirv" / "manifest.json"

_manifest_cache = None


def _manifest():
    """The build manifest, shared with the SPIR-V backend.

    Both backends are generated from the same Slang source. The manifest
    records the Metal staging cap separately from Vulkan's.
    """
    global _manifest_cache
    if _manifest_cache is None:
        import json
        _manifest_cache = (json.loads(_MANIFEST.read_text())
                           if _MANIFEST.is_file() else {})
    return _manifest_cache

#: MTLResourceStorageModeShared: one allocation both CPU and GPU can see.
#: Apple silicon is unified memory, so this is the natural mode rather than
#: a compromise -- there is no separate device heap to stage into.
_STORAGE_SHARED = 0

#: The per-bin table aliases the exchange staging inside the kernel, so the
#: kernel cannot hold more bins than that. Identical to the SPIR-V build --
#: same Slang source, same limit -- and the split below is how both stay
#: correct past it rather than quietly writing off the end of the table.
_MAX_BINS = MAX_BINS          # _gpuhost.MAX_BINS: one limit for every backend


from ._errors import UnsupportedSize      # noqa: F401  (re-export)
from . import _gputime
from ._gpu_cache import InputUploads, Pending as _Pending
from ._gpuexec import Arg, Executor


#: Points per thread, which is also how many threads carry a transform:
#: WG = n / R. Vulkan bakes this into the SPIR-V and the host never needs
#: it; Metal is dispatched with an explicit threadgroup size, so the host
#: has to agree with the kernel. Getting it wrong here does not fail to
#: launch -- it launches the wrong shape.
#:
#: Mirrors tools/build_spirv.py RADIX, which is what compiled them.
_RADIX = {32768: 32, 65536: 64}


def _radix(n):
    return _RADIX.get(n, 16)


@lru_cache(maxsize=None)
def _shipped(stem):
    """Whether a kernel shipped (source or library). Asked per dispatch, so cached:
    the stat calls were ~18 per fine-stage call."""
    return any((_METAL_DIR / (stem + ext)).is_file() for ext in (".metal", ".metallib"))


def _ieee_kernel(stem):
    """Whether a kernel library compiles with IEEE (not fast) math: the survivor compaction,
    which must list a NaN coarse value (see Context._library). MF_METAL_IEEE=all|none
    overrides, for measurement."""
    import os
    mode = os.environ.get("MF_METAL_IEEE", "default")
    if mode in ("all", "none"):
        return mode == "all"
    # The coarse kernels keep fast math (IEEE cost the band-256 tiled kernel 1.00 -> 1.23 ms)
    # and fail open by an integer test of the fp16 exponent instead (tierb.slang, MF_METAL);
    # the compaction is cheap and compares the possibly-NaN coarse value, so it is IEEE.
    return stem.startswith("compact_")


def _use_c16(band):
    """Half-width coarse path where the FP16 kernel is available.

    Loads tierb_<band>_c16.metal. Applies at every coarse band where
    a pre-compiled FP16 kernel exists.
    """
    return _shipped("tierb_%d_c16" % band)


def _ppg_of(entry):
    """Pairs per threadgroup an entry name carries: coarse16p8 -> 8, coarse16p8t2w -> 8 (a
    trailing "w" asks for the twiddle table, _twt_entry)."""
    if not entry.startswith("coarse16p"):
        return 1
    return int(entry[len("coarse16p"):].rstrip("w").split("t")[0])


def _twt_entry(entry):
    """(entry without its twiddle suffix, True when a coarse entry asks for the fp16 twiddle
    table): "coarse16p4t2w" builds coarse16p4t2's library with MF_COARSE_TWT=1."""
    if entry.startswith("coarse16") and entry.endswith("w"):
        return entry[:-1], True
    return entry, False


def coarse_geometry(band, nd, nt, simd_width=32, choose=None):
    """(entry, pairs per threadgroup, tile, groups, ragged) for the half-width coarse pass.

    The layout -- pairs per threadgroup, templates per lane (TILE_T) and the twiddle source
    (a trailing "w" on the entry: the build's fp16 table, _twt_entry) -- is choose(band)'s,
    the device's measured choice (Context._coarse_layout). Without one: the smallest shipped
    tile at the smallest packing that fills the SIMD width (threadExecutionWidth), else the
    untiled build at coarse_ppg's packing, with the recurrence. Every launch is ragged
    (_coarse.coarse_launch). MF_METAL_COARSE_TILE (0 or 1 = untiled), MF_METAL_COARSE_PPG and
    MF_METAL_COARSE_TWT force a field, for measurement and tests."""
    import os
    from ._coarse import coarse_launch, coarse_stem, shipped_tiles, forced_tile
    wg = band // _radix(band)
    built = [p for p in (1, 2, 4, 8, 16, 32) if shipped_tiles(band, p, _shipped)]
    tp = next((p for p in built if wg * p >= simd_width), built[-1]) if built else None
    if choose is not None:
        ppg, tile, twt = choose(band)
    elif tp is not None:
        ppg, tile, twt = tp, shipped_tiles(band, tp, _shipped)[0], 0
    else:
        ppg, tile, twt = coarse_ppg(band, nd * nt, simd_width=simd_width), 1, 0
    ft = forced_tile("MF_METAL_COARSE_TILE")
    fp = os.environ.get("MF_METAL_COARSE_PPG") or None
    fw = forced_tile("MF_METAL_COARSE_TWT")
    if ft is not None:
        tile = max(1, ft)
        if tile > 1:
            ppg = tp if tp is not None else ppg
        elif fp is None:
            ppg = coarse_ppg(band, nd * nt, simd_width=simd_width)
    if fp is not None:
        ppg = int(fp)
    if fw is not None:
        twt = fw
    if tile > 1 and tile not in shipped_tiles(band, ppg, _shipped):
        tile = 1
    if tile == 1 and ppg > 1 and not _shipped(coarse_stem(band, ppg, 1)):
        ppg = 1
    entry = ("coarse16" + coarse_stem(band, ppg, tile)[len("tierb_%d_c16" % band):]
             + ("w" if twt else ""))
    return entry, ppg, tile, coarse_launch(nd, nt, ppg, tile, 0)[1], tile > 1 or ppg > 1


def coarse_ppg(band, pairs, override=None, simd_width=None):
    """Pairs per threadgroup for the half-width coarse pass at this band.

    One pair is band/16 threads; an Apple SIMD group is 32 lanes. Pick the
    smallest packing that fills at least simd_width lanes (the pipeline's
    threadExecutionWidth; TARGET_THREADS when not given), from the
    variants shipped. A partial last group is ragged: its spare slots compute
    and write nothing (_coarse.coarse_launch). ``MF_METAL_COARSE_PPG`` overrides,
    for measurement.
    """
    import os
    want = override if override is not None else (os.environ.get("MF_METAL_COARSE_PPG") or None)
    shipped = [p for p in (32, 16, 8, 4, 2) if _shipped("tierb_%d_c16p%d" % (band, p))]
    if want is not None:
        want = int(want)
        return want if want == 1 or want in shipped else 1
    target = simd_width or TARGET_THREADS
    wg = band // _radix(band)
    for p in sorted(shipped):
        if wg * p >= target:
            return p
    return max(shipped, default=1) if wg < target else 1


#: Hierarchical calls that took the fused forward (for tests and the bench).
_FUSED_FORWARDS = [0]


def _fused_forward_enabled():
    """forward_tier0.slang may serve the hierarchical fine stage (MF_BAND_FORWARD=0: never).
    Whether a call takes it is _gpuhost.band_forward_wanted's, every backend's rule."""
    import os
    return os.environ.get("MF_BAND_FORWARD") != "0"


#: Threads the coarse pass packs pairs up to when no pipeline width is known; the host passes
#: the coarse pipeline's threadExecutionWidth (Context._simd_width).
TARGET_THREADS = 32


class MetalError(RuntimeError):
    pass


class _ObjC:
    """The handful of Objective-C entry points this needs.

    Each message signature gets its OWN function pointer. Reusing one
    objc_msgSend and reassigning argtypes is the classic way to get silent
    corruption on arm64, where the calling convention depends on the
    argument types.
    """

    def __init__(self):
        self._selectors = {}
        self._senders = {}
        self.objc = ctypes.CDLL("/usr/lib/libobjc.dylib")
        self.metal = ctypes.CDLL(
            "/System/Library/Frameworks/Metal.framework/Metal")
        self.foundation = ctypes.CDLL(
            "/System/Library/Frameworks/Foundation.framework/Foundation")
        self.objc.sel_registerName.restype = ctypes.c_void_p
        self.objc.sel_registerName.argtypes = [ctypes.c_char_p]
        self.objc.objc_getClass.restype = ctypes.c_void_p
        self.objc.objc_getClass.argtypes = [ctypes.c_char_p]

    @contextmanager
    def autorelease_pool(self):
        push = self.objc.objc_autoreleasePoolPush
        push.restype = ctypes.c_void_p
        push.argtypes = []
        pop = self.objc.objc_autoreleasePoolPop
        pop.restype = None
        pop.argtypes = [ctypes.c_void_p]
        pool = push()
        try:
            yield
        finally:
            pop(pool)

    def sel(self, name):
        if name not in self._selectors:
            self._selectors[name] = self.objc.sel_registerName(name)
        return self._selectors[name]

    def send(self, restype, argtypes):
        """A correctly-typed objc_msgSend for one signature."""
        key = (restype, tuple(argtypes))
        if key not in self._senders:
            self._senders[key] = ctypes.cast(
                self.objc.objc_msgSend,
                ctypes.CFUNCTYPE(restype, ctypes.c_void_p, ctypes.c_void_p, *argtypes))
        return self._senders[key]

    def call(self, obj, selector, restype=ctypes.c_void_p, args=(),
             argtypes=()):
        return self.send(restype, argtypes)(obj, self.sel(selector), *args)

    def nsstring(self, text):
        cls = self.objc.objc_getClass(b"NSString")
        return self.call(cls, b"stringWithUTF8String:",
                         args=(text.encode("utf-8"),),
                         argtypes=(ctypes.c_char_p,))

    def to_str(self, ns):
        if not ns:
            return ""
        ptr = self.call(ns, b"UTF8String")
        return ctypes.cast(ptr, ctypes.c_char_p).value.decode("utf-8", "replace") \
            if ptr else ""


class _NSRange(ctypes.Structure):
    _fields_ = [("location", ctypes.c_ulong), ("length", ctypes.c_ulong)]


class _MTLSize(ctypes.Structure):
    _fields_ = [("width", ctypes.c_ulong),
                ("height", ctypes.c_ulong),
                ("depth", ctypes.c_ulong)]


class _Buffer:
    """A shared-storage buffer, mapped for the lifetime of the object."""

    def __init__(self, ctx, nbytes):
        self.ctx = ctx
        self.nbytes = max(int(nbytes), 16)
        self.handle = ctx.o.call(
            ctx.device, b"newBufferWithLength:options:",
            args=(self.nbytes, _STORAGE_SHARED),
            argtypes=(ctypes.c_ulong, ctypes.c_ulong))
        if not self.handle:
            raise MetalError("newBufferWithLength failed for %d bytes" % nbytes)
        self.ptr = ctx.o.call(self.handle, b"contents")

    def write(self, array):
        flat = np.ascontiguousarray(array)
        if flat.nbytes > self.nbytes:
            raise MetalError("write of %d into a %d-byte buffer"
                             % (flat.nbytes, self.nbytes))
        ctypes.memmove(self.ptr, flat.ctypes.data, flat.nbytes)

    def read(self, dtype, count):
        out = np.empty(count, dtype=dtype)
        ctypes.memmove(out.ctypes.data, self.ptr, out.nbytes)
        return out

    def view(self, dtype, count):
        """The first `count` elements as a NumPy view of the buffer (no copy)."""
        dtype = np.dtype(dtype)
        raw = (ctypes.c_ubyte * (count * dtype.itemsize)).from_address(
            self.ptr.value if hasattr(self.ptr, "value") else self.ptr)
        return np.frombuffer(raw, dtype=dtype, count=count)

    def read_into(self, out):
        """Zero-copy direct read into caller-provided contiguous array."""
        ctypes.memmove(out.ctypes.data, self.ptr, min(self.nbytes, out.nbytes))
        return out

    def destroy(self):
        if self.handle:
            self.ctx.o.call(self.handle, b"release")
            self.handle = None


class _HostBuffer(_Buffer):
    """A device buffer over caller memory, without a copy (unified memory).

    newBufferWithBytesNoCopy needs a page-aligned pointer and a whole number
    of pages; the caller's array keeps the memory alive, and this object must
    be dropped before the array is. No deallocator: Metal never frees it.
    """

    def __init__(self, ctx, array):
        self.ctx = ctx
        self.nbytes = array.nbytes
        self.ptr = ctypes.c_void_p(array.ctypes.data)
        self.handle = ctx.o.call(
            ctx.device, b"newBufferWithBytesNoCopy:length:options:deallocator:",
            args=(self.ptr, self.nbytes, _STORAGE_SHARED, None),
            argtypes=(ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p))
        if not self.handle:
            raise MetalError("newBufferWithBytesNoCopy failed for %d bytes" % self.nbytes)


def describe_error(o, err):
    """Everything the NSError carries, not only its one-line summary.

    A pipeline that fails to build reports "Compilation failed" as its
    localizedDescription and puts the actual back-end diagnostics in
    userInfo, so the short form names the failure without ever saying
    what it was -- which is exactly the report that cost a CI round
    trip. `description` dumps the whole object, userInfo included.
    """
    if not err or not err.value:
        return "no error object"
    parts = []
    for sel in (b"localizedDescription", b"localizedFailureReason",
                b"localizedRecoverySuggestion", b"description"):
        try:
            got = o.to_str(o.call(err.value, sel))
        except Exception:                      # selector not implemented
            continue
        got = (got or "").strip()
        if got and not any(got in seen for seen in parts):
            parts.append(got)
    domain = o.to_str(o.call(err.value, b"domain"))
    code = int(o.call(err.value, b"code", restype=ctypes.c_long))
    parts.append("[domain=%s code=%d]" % (domain or "?", code))
    return " | ".join(parts)


def _autoreleased(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self.o.autorelease_pool():
            return method(self, *args, **kwargs)
    return call


class _Device:
    """One Metal device per index for the life of the process, with the Objective-C
    bindings and every compiled pipeline.

    A bank holds dozens of plans, each with its own Context. Giving each its own device
    handle recompiled every kernel from source per plan (the ladder's first segment was
    mostly that), and made buffers of one plan foreign to another: a fine bank reading
    the middle bank's output could not bind it by offset, and wrapping that memory in a
    second buffer cost ~60 ms per call on the M2. Contexts on one _Device share buffers
    (_shared._same_device), pipelines and libraries; each keeps its own queue and caches.
    Never released: it lives as long as the process.
    """

    def __init__(self, index):
        self.o = o = _ObjC()
        o.metal.MTLCreateSystemDefaultDevice.restype = ctypes.c_void_p
        # Enumerate rather than ask for the "system default", which is the device
        # recommended for RENDERING and is nil with no display attached.
        from . import _metal
        with o.autorelease_pool():
            found = _metal._all_devices(o.objc, o.metal)
            if not found:
                one = o.metal.MTLCreateSystemDefaultDevice()
                found = [one] if one else []
            if index < 0 or index >= len(found):
                for handle in found:
                    o.call(handle, b"release", restype=None)
                raise MetalError(
                    "no Metal device with index %d (found %d); "
                    "MTLCopyAllDevices is the enumeration and "
                    "MTLCreateSystemDefaultDevice needs a display"
                    % (index, len(found)))
            self.handle = found[index]
            for i, handle in enumerate(found):
                if i != index:
                    o.call(handle, b"release", restype=None)
            self.name = o.to_str(o.call(self.handle, b"name"))
            self.max_shared_memory = int(o.call(
                self.handle, b"maxThreadgroupMemoryLength", restype=ctypes.c_ulong))
        self.pipelines = {}
        self.pipeline_names = {}
        #: Contexts holding writes left in flight by zero_columns_done(wait=False). Each
        #: signals its own MTLSharedEvent after them (one event per queue: a shared one
        #: could be set back by a later, lower signal from another queue). Contexts have
        #: their own queues, so another context's command buffer waits on those events on
        #: the GPU (Context._new_cmd) -- no host wait between the stages.
        self.pending_contexts = []
        #: A _FusedBatch while filter_series_many is collecting (fused()), else None.
        self.collector = None


_DEVICES = {}


class _FusedBatch:
    """Command buffers shared by every context on one device while a batch collects
    (TimeDomainFilterBank.filter_series_many): the protocol of _vkcompute._FusedBatch.

    Each plan has its own Context and queue, so a segment's fine stage was ~200 small
    command buffers, each committed separately, with the GPU idle across every host gap
    between them. While collecting, Context._new_cmd hands out the batch's current command
    buffer instead (on one device-level queue, so successive batch buffers run in order);
    an asynchronous _commit leaves it open, and it is committed once `chunk` submissions
    have joined it (the device starts on a chunk while the host prepares the next), when
    a result from it is waited on, or at close. Encoders are always ended before the
    methods that open them return, so contexts never interleave inside one encoder."""

    #: Submissions per command buffer.
    #: Metal commits are cheap and the device sat idle while the host filled a chunk:
    #: M2 ladder (bank3, H1) 100.8 ms per segment at 16, 95.8 at 4, 92.6 at 2, 93.6 at 1;
    #: with --pipeline 110.0 at 16, 96.9 at 1. Committing on device idle (status) instead,
    #: 95.7. So 2.
    chunk = 2

    def __init__(self, dev):
        self.dev, self.cmd, self.count = dev, None, 0
        self.holders = []           # contexts holding self.cmd uncommitted (deferred forward)
        self.waited = {}            # id(ctx) -> event value already waited on in self.cmd
        self.untimed = set()        # committed buffers whose device time is not yet recorded

    def acquire(self, ctx):
        """The current shared command buffer (autoreleased semantics: callers retain)."""
        o = self.dev.o
        if self.cmd is None:
            if getattr(self.dev, "batch_queue", None) is None:
                self.dev.batch_queue = o.call(self.dev.handle, b"newCommandQueue")
            self.cmd = o.call(self.dev.batch_queue, b"commandBuffer")
            o.call(self.cmd, b"retain")
            self.waited = {}
        for c in self.dev.pending_contexts:
            # Writes another context left in flight: ordered here, between encoders, as
            # _new_cmd orders a fresh buffer.
            if self.waited.get(id(c), 0) < c._signal_value:
                o.call(self.cmd, b"encodeWaitForEvent:value:", restype=None,
                       args=(c._signal_event, c._signal_value),
                       argtypes=(ctypes.c_void_p, ctypes.c_uint64))
                self.waited[id(c)] = c._signal_value
        self.holders.append(ctx)
        return self.cmd

    def owns(self, cmd):
        return cmd is not None and self.cmd is not None and cmd == self.cmd

    def _release_holder(self, ctx):
        try:
            self.holders.remove(ctx)
        except ValueError:
            pass

    def joined(self, ctx, async_submit):
        """ctx submitted into the shared buffer: commit it when due (a synchronous
        submission waits right away, so it is due now)."""
        self._release_holder(ctx)
        self.count += 1
        if not async_submit or (self.count >= self.chunk and not self.holders):
            self.flush()

    def dropped(self, ctx):
        self._release_holder(ctx)

    def flush(self):
        """Commit the current buffer. A context still holding it (a deferred forward
        waiting for its consumer) has its forward committed with it: the consumer then
        starts a new buffer on the same queue, which runs after this one."""
        if self.cmd is None:
            return
        cmd, self.cmd, self.count = self.cmd, None, 0
        for ctx in self.holders:
            pending = ctx._pending_metal
            if pending is not None and pending[0] == cmd:
                ctx._materialize_forward()
                ctx._pending_metal = None
                self.dev.o.call(cmd, b"release", restype=None)   # the forward's retain
        self.holders = []
        self.untimed.add(cmd)
        self.dev.o.call(cmd, b"commit", restype=None)
        self.dev.o.call(cmd, b"release", restype=None)


def fused():
    """Begin a fused batch on every Metal device in use; returns a callable closing it
    (the same protocol as _vkcompute.fused)."""
    devs = [d for d in _DEVICES.values() if d.collector is None]
    for d in devs:
        d.collector = _FusedBatch(d)

    def close():
        for d in devs:
            b, d.collector = d.collector, None
            if b is not None:
                b.flush()
    return close


def settle_all():
    """Wait for every write left in flight on any Metal device (a host read follows)."""
    for dev in _DEVICES.values():
        if dev.pending_contexts:
            dev.pending_contexts[0].settle_writes()


def _device(index):
    dev = _DEVICES.get(index)
    if dev is None:
        dev = _DEVICES[index] = _Device(index)
    return dev


class _MtlList:
    """A command list (_gpuexec's driver interface): the dispatches, encoded per run into
    serial compute encoders (each sees the previous one's writes), with each Arg bound to
    that run's buffer or words. A fill is a blit between them."""

    def __init__(self, label):
        self.label, self.ops = label, []

    def dispatch(self, kernel, groups, buffers, words=(), offsets=None):
        flat = []
        for w in words:
            flat.extend(w if isinstance(w, tuple) else (w,))
        self.ops.append((kernel, int(groups), list(buffers), offsets, flat))

    def barrier(self):
        pass

    def stamp(self, name):
        pass

    def fill(self, buf, word):
        if word not in (0, 0xFFFFFFFF):
            raise ValueError("a fill is a byte pattern: 0 or 0xFFFFFFFF")
        self.ops.append(("fill", buf, 0xFF if word else 0))

    def readback(self, buf, nbytes):
        pass                        # shared storage: the host reads it after the run

    def end(self):
        return self.label, self.ops


class Context(Executor, InputUploads):
    """A queue and dispatch caches on one process-wide Metal device (see _Device)."""

    max_grouped_bins = _MAX_BINS
    #: peaks_grouped takes nbins: window groups may give different bin counts.
    supports_ragged_bins = True
    #: peaks, peaks_grouped and hier_peaks take sparse=True and return a _SparsePeaks;
    #: hier_peaks reads back only its refined pairs and skips the output fill.
    supports_sparse = True
    #: forward takes rows=(r0, count) (MatchedFilter._items_gpu: both detectors' series
    #: in one workspace and one submission).
    forward_rows = True
    #: forward takes real=(lane, stride, length): a real series read in place, not widened.
    real_series = True
    #: shared_buffer() may hand back a view inside an allocation (one row of a device-
    #: resident middle output); every binding adds its offset.
    shared_views = True
    #: Commits return without waiting when asked (async_submit with a slot):
    #: the series loop keeps several batches in flight. Declared, so callers
    #: test a capability instead of probing signatures for a TypeError.
    supports_async = True
    _pending_metal = None
    _timing = False

    def __init__(self, index=0):
        if sys.platform != "darwin":
            raise MetalError("Metal is only available on macOS")
        self.device = self.queue = None
        self._pipelines = {}
        self._batches = {}
        self._hier = {}
        self._inflight = {}
        #: Host memory a deferred command reads in place (host_view owners).
        self._keep_until_done = []
        #: (label, device_ms) per command buffer when MF_GPU_TIMING=1, from
        #: GPUStartTime/GPUEndTime (the contract in _gputime). Off, nothing
        #: registers and nothing is appended.
        self.timing_log = []
        self._timing = _gputime.enabled()
        if self._timing:
            _gputime.register(self)
        dev = _device(index)
        self.o = dev.o
        try:
            self._initialize(index, dev)
        except Exception:
            self.destroy()
            raise

    def _initialize(self, index, dev):
        self._device_state = dev
        self.device = dev.handle
        self.name = dev.name
        self.max_shared_memory = dev.max_shared_memory
        self._pipelines = dev.pipelines
        self.pipeline_names = dev.pipeline_names
        with self.o.autorelease_pool():
            self.queue = self.o.call(self.device, b"newCommandQueue")
        #: Device-only seconds for the last dispatch, see _record_gpu_time.
        self.last_gpu_time = 0.0
        if not self.queue:
            raise MetalError("newCommandQueue failed")
        self._batches = {}
        self._hier = {}
        self._uploaded = {"data": {}, "tmpl": {}}

    # ---- kernels ----------------------------------------------------------
    def _library(self, stem, twt=False):
        """A compiled .metallib if one shipped, else compile the source.

        The library is what a macOS wheel carries, built by Apple's compiler
        on the macOS runner. The .metal source travels as well so a wheel
        built elsewhere -- or one whose library is stale -- still runs,
        paying a compile on first use rather than refusing.
        """
        raw = (stem.startswith("tierb_") and "_c16" in stem
               and os.environ.get("MF_VK_C16_BOUND", "1") == "0")
        lib_path = _METAL_DIR / (stem + ".metallib")
        # A shipped .metallib is built with the compiler's defaults (tools/build_spirv.py):
        # fast math, no macros. A kernel that needs other options -- the raw fp16 maximum
        # (MF_C16_RAW) or IEEE math for the fail-open compaction -- compiles from source, or
        # the library silently runs the default build instead (on the macOS runner the
        # physics tests then measured the fp16 BOUND as if it were the raw statistic).
        if lib_path.is_file() and not raw and not twt and not _ieee_kernel(stem):
            url_cls = self.o.objc.objc_getClass(b"NSURL")
            url = self.o.call(url_cls, b"fileURLWithPath:",
                              args=(self.o.nsstring(str(lib_path)),),
                              argtypes=(ctypes.c_void_p,))
            err = ctypes.c_void_p()
            lib = self.o.call(self.device, b"newLibraryWithURL:error:",
                              args=(url, ctypes.byref(err)),
                              argtypes=(ctypes.c_void_p, ctypes.c_void_p))
            if lib:
                return lib
        src_path = _METAL_DIR / (stem + ".metal")
        if not src_path.is_file():
            raise MetalError("no Metal kernel for %s (looked for %s and %s)"
                             % (stem, lib_path.name, src_path.name))
        err = ctypes.c_void_p()
        opts = None
        # Library macros (twiddle.slang): MF_C16_RAW=1 is the fp16 bound switch
        # (gatechain._RAW_GATE_SWITCH; Vulkan's constant 77), the raw fp16 maximum, for
        # measuring the bound's margin only; MF_COARSE_TWT=1 takes the coarse twiddles from
        # the build's fp16 table (Vulkan's constant 80), a measured choice (_coarse_layout).
        names = [k for k, on in (("MF_C16_RAW", raw), ("MF_COARSE_TWT", twt)) if on]
        if names:
            o = self.o
            opts = o.call(o.call(o.objc.objc_getClass(b"MTLCompileOptions"), b"alloc"), b"init")
            macros = o.call(o.call(o.objc.objc_getClass(b"NSMutableDictionary"), b"alloc"), b"init")
            for name in names:
                num = o.call(o.objc.objc_getClass(b"NSNumber"), b"numberWithInt:", args=(1,),
                             argtypes=(ctypes.c_int,))
                o.call(macros, b"setObject:forKey:", restype=None,
                       args=(num, o.nsstring(name)), argtypes=(ctypes.c_void_p, ctypes.c_void_p))
            o.call(opts, b"setPreprocessorMacros:", restype=None, args=(macros,),
                   argtypes=(ctypes.c_void_p,))
            o.call(macros, b"release", restype=None)
        if _ieee_kernel(stem):
            # Gates must fail open: a value that overflows fp16 becomes inf, and an
            # inf - inf in the transform becomes NaN. Under the default fast-math the
            # compiler assumes neither exists and a NaN magnitude lost every comparison,
            # dismissing the loudest pair (tools/gate_margin.py --loud). IEEE semantics
            # make NaN and inf compare as the largest bit patterns, so they pass.
            opts = self.o.call(self.o.call(self.o.objc.objc_getClass(b"MTLCompileOptions"),
                                           b"alloc"), b"init")
            self.o.call(opts, b"setFastMathEnabled:", restype=None, args=(False,),
                        argtypes=(ctypes.c_bool,))
        lib = self.o.call(self.device, b"newLibraryWithSource:options:error:",
                          args=(self.o.nsstring(src_path.read_text()), opts,
                                ctypes.byref(err)),
                          argtypes=(ctypes.c_void_p, ctypes.c_void_p,
                                    ctypes.c_void_p))
        if opts:
            self.o.call(opts, b"release", restype=None)
        if not lib:
            raise MetalError("could not build a Metal library from %s: %s"
                             % (src_path.name, self._error(err)))
        return lib

    def _error(self, err):
        return describe_error(self.o, err)

    def _stem(self, n, entry):
        """The kernel variant this device can actually hold.

        Apple caps threadgroup memory at 32 KB. The tuned staging asks for
        64 KB at n=16384 and exactly 32 KB at n=8192, so on Apple the
        preferred build cannot create a pipeline at all -- and it reports
        that as "Compilation failed", which names nothing. Choosing the
        portable build here turns a dead end into a slower kernel.
        """
        # One stem per entry point. This was a two-way choice -- fusedTierB
        # or "the other one" -- which silently sends every new entry to the
        # gated library, where its function does not exist. The same
        # assumption was in the build script's artifact naming.
        if entry == "packCoarse":
            return "pack_coarse"
        if entry == "compactPeaks":
            return "compact_peaks"
        if entry == "seriesForward":
            return "forward_%d" % n
        if entry == "forwardTier0":
            return "forward_tier0_%d" % n
        if entry == "seriesForwardListed":
            return "forward_listed_%d" % n
        if entry == "markBlocks":
            return "markblocks"
        if entry.startswith("coarse16"):
            return "tierb_%d_c16%s" % (n, entry[len("coarse16"):])
        tierc = {"tcStage1": "corr1", "tcFullStage3": "corr2",
                 "tcFullSeriesStage3": "corr_series2",
                 "tcForwardStage1": "fwd1", "tcForwardStage3": "fwd2"}
        if entry in tierc:
            return "tc_%s_%d" % (tierc[entry], n)
        base = "%s_%d" % ({"fusedTierB": "tierb",
                           "compactPairs": "compact",
                           "refineListed": "refine",
                           "fullCorrelation": "full",
                           "fullCorrelationSeries": "full_series"}[entry], n)
        info = _manifest().get("modules", {}).get(str(n), {})
        # The Metal column. Metal is built against its own staging cap
        # -- Apple and the Radeon want opposite answers -- so reading
        # the Vulkan "lds_bytes" here would compare this device's limit
        # against a number no Metal kernel was built with, and pick the
        # portable variant at sizes that do not need it.
        need = info.get("metal_lds_bytes", info.get("lds_bytes", 0))
        if need <= self.max_shared_memory:
            return base
        alt = base + "_lds32"
        if not any((_METAL_DIR / (alt + ext)).is_file()
                   for ext in (".metallib", ".metal")):
            raise UnsupportedSize(
                "n=%d needs %d KB of threadgroup memory, %s offers %d KB, "
                "and no portable build was shipped for it"
                % (n, need // 1024, self.name,
                   self.max_shared_memory // 1024))
        return alt

    def _pipeline_sized(self, stem, fn, want):
        """Rebuild the pipeline having told the compiler the group size.

        maxTotalThreadsPerThreadgroup is an INPUT to the descriptor form, not
        only a report. Left alone the compiler optimises for occupancy and
        stops wherever the registers land -- 576 for the n=16384 kernel on an
        M2, against the 1024 it is dispatched at, so that length was refused
        outright. Asked for 1024 it delivers 1024, spilling if it must.

        ONLY when the default is short, which is the part worth stating.
        Declaring it unconditionally also works, in the sense that every
        pipeline builds and reports the size asked for -- and it changed the
        answer at n=4096 on an M2, where the default allows 448 and nothing
        needed asking. test_run_series_agrees_with_the_cpu failed
        deterministically, three runs out of three, and passed again the
        moment the descriptor was dropped. Constraining a kernel that did not
        need constraining is not free, so it is not done.

        Measured on an M2:

            kernel               needs   default   declared
            tierb_4096             256       448        --    (left alone)
            tierb_8192_lds32       512       512        --    (left alone)
            tierb_16384_lds32     1024       576      1024
        """
        desc = self.o.call(
            self.o.call(self.o.objc.objc_getClass(
                b"MTLComputePipelineDescriptor"), b"alloc"), b"init")
        try:
            self.o.call(desc, b"setComputeFunction:", restype=None,
                        args=(fn,), argtypes=(ctypes.c_void_p,))
            self.o.call(desc, b"setMaxTotalThreadsPerThreadgroup:", restype=None,
                        args=(want,), argtypes=(ctypes.c_ulong,))
            err = ctypes.c_void_p()
            pso = self.o.call(
                self.device,
                b"newComputePipelineStateWithDescriptor:options:reflection:error:",
                args=(desc, 0, None, ctypes.byref(err)),
                argtypes=(ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p,
                          ctypes.c_void_p))
        finally:
            self.o.call(desc, b"release", restype=None)
        if not pso:
            raise UnsupportedSize(
                "%s needs a %d-thread threadgroup and asking for one failed on %s: "
                "%s" % (stem, want, self.name, self._error(err)))
        return pso, int(self.o.call(pso, b"maxTotalThreadsPerThreadgroup",
                                    restype=ctypes.c_ulong))

    @_autoreleased
    def pipeline(self, n, entry="fusedTierB", one_bin=False, c16=False):
        if c16 or entry.startswith("coarse16"):
            entry_name = entry if entry.startswith("coarse16") else "coarse16"
            fn_name = "fusedTierB"
        else:
            entry_name = entry
            fn_name = entry
        single = (_manifest().get("modules", {}).get(str(n), {}).get("metal", {})
                  .get(entry_name, {}).get("one_bin")) if (one_bin and not entry_name.startswith("coarse16")) else None
        if single and single["lds_bytes"] > self.max_shared_memory:
            single = None
        key = (n, entry_name, True) if single else (n, entry_name)
        if entry_name.startswith("coarse16") and os.environ.get("MF_VK_C16_BOUND", "1") == "0":
            # The raw-maximum build (_library's MF_C16_RAW) is a different library: a process
            # that switches it (the physics tests) must not reuse the bound pipeline.
            key = key + ("raw",)
        if key in self._pipelines:
            return self._pipelines[key]
        base, twt = _twt_entry(entry_name)
        stem = pathlib.Path(single["msl"]).stem if single else self._stem(n, base)
        lib = self._library(stem, twt=twt)
        fn = pso = None
        try:
            fn = self.o.call(lib, b"newFunctionWithName:",
                             args=(self.o.nsstring(fn_name),),
                             argtypes=(ctypes.c_void_p,))
            if not fn:
                raise MetalError("no function %r in %s" % (fn_name, stem))
            roles = {"tcStage1": "corr1", "tcFullStage3": "corr2",
                     "tcFullSeriesStage3": "corr_series2",
                     "tcForwardStage1": "fwd1", "tcForwardStage3": "fwd2"}
            if entry_name in roles:
                want = (_manifest()['full_tierc'][str(n)][roles[entry_name]]['local_size'][0])
            elif entry_name in ("compactPairs", "markBlocks", "compactPeaks"):
                want = 256
            else:
                want = n // _radix(n) * _ppg_of(entry_name)
            err = ctypes.c_void_p()
            pso = self.o.call(self.device,
                              b"newComputePipelineStateWithFunction:error:",
                              args=(fn, ctypes.byref(err)),
                              argtypes=(ctypes.c_void_p, ctypes.c_void_p))
            if not pso:
                raise MetalError("could not build a pipeline for %s: %s"
                                 % (stem, self._error(err)))
            limit = int(self.o.call(pso, b"maxTotalThreadsPerThreadgroup",
                                    restype=ctypes.c_ulong))
            if limit < want:
                self.o.call(pso, b"release", restype=None)
                pso = None
                pso, limit = self._pipeline_sized(stem, fn, want)
            if limit < want:
                raise UnsupportedSize(
                    "n=%d needs a %d-thread threadgroup and this pipeline allows "
                    "%d on %s even when asked for %d; use a shorter transform or "
                    "device='cpu'" % (n, want, limit, self.name, want))
            self._pipelines[key] = pso
            #: What each pipeline is, for profilers that observe _dispatch.
            if "pipeline_names" not in self.__dict__:
                self.pipeline_names = {}
            self.pipeline_names[pso] = (stem, n, entry_name)
            result, pso = pso, None  # ownership transferred to the cache
            return result

        finally:
            for obj in (pso, fn, lib):
                if obj:
                    self.o.call(obj, b"release", restype=None)

    # ---- dispatch ---------------------------------------------------------
    def _record_gpu_time(self, cmd, label="dispatch"):
        """Device-only duration of the command buffer just completed.

        Metal builds its encoders per dispatch, so there is no recording to
        replay the way the Vulkan path times device work. GPUEndTime and
        GPUStartTime give the same thing more directly: the window the GPU
        actually spent, with the host's marshalling left out. Cost tuning
        needs that -- timing the whole call instead adds a per-call constant
        to every configuration, which compresses the ratios it is trying to
        measure and made adjacent margins come out non-monotonic on Vulkan.

        With MF_GPU_TIMING=1 each command buffer is also logged as
        (label, device_ms) in timing_log -- the contract the Vulkan and CUDA
        backends share. Only meaningful after waitUntilCompleted.
        """
        t0 = self.o.call(cmd, b"GPUStartTime", restype=ctypes.c_double)
        t1 = self.o.call(cmd, b"GPUEndTime", restype=ctypes.c_double)
        self.last_gpu_time = float(t1) - float(t0)
        if self._timing:
            self.timing_log.append((label, self.last_gpu_time * 1e3))
            if t1 > t0 > 0:
                _gputime.INTERVALS.append((float(t0), float(t1)))

    def timings(self):
        """Finish outstanding command buffers and return the timing log (MF_GPU_TIMING=1)."""
        self._drain()
        return self.timing_log

    def _new_cmd(self, shared_ok=True):
        """A new (autoreleased) command buffer on this context's queue, ordered on the GPU
        after writes other contexts left in flight (zero_columns_done(wait=False))."""
        dev = getattr(self, "_device_state", None)
        batch = getattr(dev, "collector", None)
        if batch is not None and not shared_ok:
            batch = None
        if batch is not None:
            return batch.acquire(self)
        cmd = self.o.call(self.queue, b"commandBuffer")
        for c in (dev.pending_contexts if dev is not None else ()):
            if c is not self:
                self.o.call(cmd, b"encodeWaitForEvent:value:", restype=None,
                            args=(c._signal_event, c._signal_value),
                            argtypes=(ctypes.c_void_p, ctypes.c_uint64))
        return cmd

    def _command_buffer(self):
        """An OWNED command buffer: the deferred forward's, or a new one.

        The forward that deferred its commit retained its buffer; a fresh one
        is retained here, so every path releases exactly once in _commit,
        after completion. An autoreleased command buffer would otherwise die
        with the pool of the method that made it, while still in flight.
        """
        self._materialize_forward()
        pending = self._pending_metal
        if pending is None:
            cmd = self._new_cmd()
            self.o.call(cmd, b"retain")
            self._cmd_prefix = ""
            return cmd
        self._pending_metal = None
        self._cmd_prefix = "forward+"
        return pending[0]

    def _commit(self, cmd, label, *, async_submit=False, finish=None, owner=None):
        """Commit an owned command buffer; ``finish()`` reads its outputs.

        Synchronous unless async_submit, in which case a _Pending is returned
        and the wait happens when it is called. Each in-flight result owns
        its buffers (callers key their storage by slot), so the host never
        writes a buffer a running command still reads.
        """
        label = getattr(self, "_cmd_prefix", "") + label
        self._cmd_prefix = ""
        dev = getattr(self, "_device_state", None)
        batch = getattr(dev, "collector", None)
        if batch is not None and batch.owns(cmd):
            batch.joined(self, async_submit)
        else:
            batch = None
            self.o.call(cmd, b"commit", restype=None)

        def complete():
            try:
                if batch is not None and batch.owns(cmd):
                    batch.flush()           # waited on before its chunk filled
                self.o.call(cmd, b"waitUntilCompleted", restype=None)
                self._check_completed(cmd)
                if batch is None:
                    self._record_gpu_time(cmd, label)
                elif cmd in batch.untimed:
                    batch.untimed.discard(cmd)  # one shared buffer, timed once
                    self._record_gpu_time(cmd, "fused")
                else:
                    self.last_gpu_time = 0.0
            finally:
                self.o.call(cmd, b"release", restype=None)
            return finish() if finish is not None else None

        if not async_submit:
            return complete()
        return self._track(complete, owner=owner)

    def _set_buffers(self, enc, buffers, start=1, offsets=None):
        for slot, buf in enumerate(buffers, start=start):
            off = getattr(buf, "offset", 0) + (0 if offsets is None else offsets[slot - start])
            self.o.call(enc, b"setBuffer:offset:atIndex:", restype=None,
                        args=(buf.handle, off, slot),
                        argtypes=(ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong))

    def _set_params(self, enc, params):
        blk = (ctypes.c_uint32 * len(params))(*params)
        self.o.call(enc, b"setBytes:length:atIndex:", restype=None,
                    args=(ctypes.byref(blk), ctypes.sizeof(blk), 0),
                    argtypes=(ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong))

    def _dispatch(self, enc, pso, params, buffers, tg, groups=None, indirect=None,
                  offsets=None):
        """One kernel: pipeline, uniforms at 0, buffers from 1, then the grid.

        ``indirect`` is an args buffer whose first word a compaction filled
        on the device; the threadgroup count then never reaches the host.
        Every kernel is encoded here, so this is also the one place a
        per-kernel profiler (tools/metal_roofline.py) has to observe.
        """
        self.o.call(enc, b"setComputePipelineState:", restype=None,
                    args=(pso,), argtypes=(ctypes.c_void_p,))
        self._set_params(enc, params)
        self._set_buffers(enc, buffers, offsets=offsets)
        if indirect is not None:
            self.o.call(
                enc,
                b"dispatchThreadgroupsWithIndirectBuffer:"
                b"indirectBufferOffset:threadsPerThreadgroup:",
                restype=None,
                args=(indirect.handle, 0, _MTLSize(tg, 1, 1)),
                argtypes=(ctypes.c_void_p, ctypes.c_ulong, _MTLSize))
        else:
            self.o.call(enc, b"dispatchThreadgroups:threadsPerThreadgroup:",
                        restype=None,
                        args=(_MTLSize(groups, 1, 1), _MTLSize(tg, 1, 1)),
                        argtypes=(_MTLSize, _MTLSize))

    def empty_shared(self, shape, dtype=np.complex64, *, readback=False, host_input=False):
        return empty_shared(self, _Buffer, shape, dtype)

    #: Page size newBufferWithBytesNoCopy requires (16 KiB on Apple silicon).
    page_bytes = 16384

    def host_view(self, array):
        """Make caller memory usable as device memory in place, or return None.

        Unified memory: a page-aligned, whole-page, C-contiguous array can back a
        Metal buffer directly, so a kernel writes its output where the caller
        reads it -- no workspace and no copy. Returns an owner; shared_buffer()
        recognises the array while the owner lives. Drop the owner when the
        dispatch has completed, and before the array.
        """
        from ._shared import _Allocation, _containing
        if isinstance(array, np.ndarray) and array.nbytes:
            # Memory already inside a device allocation is bound by offset instead: a
            # second buffer over the same pages cost ~60 ms before the GPU started.
            start, owner = _containing(array.ctypes.data)
            if owner is not None and array.ctypes.data < start + owner.buffer.nbytes:
                return None
        if (not isinstance(array, np.ndarray) or not array.flags.c_contiguous
                or not array.flags.writeable or array.nbytes == 0
                or array.ctypes.data % self.page_bytes or array.nbytes % self.page_bytes):
            return None
        try:
            return _Allocation(_HostBuffer(self, array))
        except MetalError:
            return None

    def _materialize_forward(self, skip=None):
        """Encode the deferred forwards still held lazily (forward()), except `skip`."""
        lazy = self.__dict__.pop("_lazy_fwd", None)
        for item in lazy or ():
            if item is skip:
                continue
            n, pso, buffers, count, (size, code), cmd = item
            enc = self.o.call(cmd, b"computeCommandEncoder")
            self._dispatch(enc, pso, (size, code), buffers, n // _radix(n), groups=count)
            self.o.call(enc, b"endEncoding", restype=None)

    def _claim_forward(self, spectra_buf, rows):
        """The lazy forward writing exactly `rows` rows of spectra_buf from row 0, taken
        out of the pending list (its consumer encodes it), or None."""
        lazy = getattr(self, "_lazy_fwd", None)
        if not lazy:
            return None
        pending = self._pending_metal
        for item in reversed(lazy):
            sp = item[2][2]
            if (sp.handle == spectra_buf.handle and getattr(sp, "offset", 0) ==
                    getattr(spectra_buf, "offset", 0) and item[3] == rows
                    and pending is not None and item[5] == pending[0]):
                lazy.remove(item)
                return item
        return None

    def _flush_forward(self):
        self._materialize_forward()
        pending = self._pending_metal
        if pending is not None:
            self._pending_metal = None
            self._cmd_prefix = ""
            self._commit(pending[0], "forward")

    def cancel_forward(self, slot=None):
        """Drop a deferred forward that will not be committed."""
        self.__dict__.pop("_lazy_fwd", None)
        pending = self._pending_metal
        if pending is not None:
            self._pending_metal = None
            batch = getattr(getattr(self, "_device_state", None), "collector", None)
            if batch is not None and batch.owns(pending[0]):
                batch.dropped(self)
            self.o.call(pending[0], b"release", restype=None)

    #: peaks_items takes async_submit (MatchedFilter._items_gpu(wait=False)).
    items_async = True

    @_autoreleased
    def peaks_items(self, n, data, tmpl, items, binsize, threshold, async_submit=False):
        """One command buffer over items (lo, hi, a, b, t): rows a:b of data against
        template row t, searched over [lo, hi) in bins of binsize. Returns per item
        (idx, val) shaped (b - a, 1, nbins). Data and templates are device allocations;
        buffer offsets select each item's rows, so nothing is copied or recorded."""
        b_data, b_tmpl = shared_buffer(data, self), shared_buffer(tmpl, self)
        if b_data is None or b_tmpl is None:
            raise ValueError("item spectra and templates must be shared allocations")
        shift = bin_shift(binsize)
        t2 = int(np.float32(float(threshold) ** 2 if threshold > 0 else 0).view(np.uint32))
        offs, nbs, size = plan_items(items, binsize, 1, _MAX_BINS)    # buffer offsets: 4 B
        prior = self.__dict__.pop("_items_inflight", None)
        if prior is not None and not prior.done:
            prior()                          # its output buffers are about to be reused
        if getattr(self, "_items_cap", 0) < size:
            self._drain()
            cap = max(size, 2 * getattr(self, "_items_cap", 0))
            for buf in getattr(self, "_items_out", ()):
                buf.destroy()
            self._items_out = (_Buffer(self, cap * 4), _Buffer(self, cap * 8))
            self._items_cap = cap
        b_idx, b_val = self._items_out
        cmd = self._command_buffer()
        enc = self.o.call(cmd, b"computeCommandEncoder")
        for (lo, hi, a, b, t), off, nb in zip(items, offs, nbs):
            self._dispatch(enc, self.pipeline(n, "fusedTierB", nb == 1),
                           (1, lo, hi, binsize, shift & 0xFFFFFFFF, nb, t2),
                           (b_data, b_tmpl, b_idx, b_val), n // _radix(n), groups=b - a,
                           offsets=(a * n * 8, t * n * 8, off * 4, off * 8))
        self.o.call(enc, b"endEncoding", restype=None)

        def finish():
            return split_items(items, offs, nbs, b_idx.read(np.int32, size),
                               b_val.read(np.complex64, size))
        res = self._commit(cmd, "items", async_submit=async_submit, finish=finish)
        if async_submit:
            self._items_inflight = res
        return res

    #: _continuous_gpu may leave its last batch in flight: zero_columns_done finishes it.
    defers_continuous = True
    #: A grouped flat call may stay in flight (filter_series_many): peaks_grouped keys its
    #: buffers by slot when asked to submit asynchronously.
    defers_grouped = True

    def zero_columns(self, dest, a, b):
        """Zero dest[:, a:b] of a device-shared 2-D array on the device (enqueued after
        whatever this context has submitted that writes it: tracked buffers order them).

        Call zero_columns_done() after the last one: it commits and waits, for these and
        for every command still in flight on this context."""
        sb = shared_buffer(dest, self)
        if sb is None or dest.ndim != 2 or b <= a or not dest.flags.c_contiguous:
            raise ValueError("zero_columns needs a device-shared 2-D array and a nonempty range")
        o = self.o
        if getattr(self, "_zero_enc", None) is None:
            with o.autorelease_pool():
                cmd = self._new_cmd(shared_ok=False)   # its encoder stays open across calls
                o.call(cmd, b"retain")
                enc = o.call(cmd, b"blitCommandEncoder")
                o.call(enc, b"retain")          # outlives this pool until zero_columns_done
            self._zero_cmd, self._zero_enc = cmd, enc
        row = dest.strides[0]
        base = getattr(sb, "offset", 0) + a * dest.itemsize
        length = (b - a) * dest.itemsize
        fill = o.send(None, (ctypes.c_void_p, _NSRange, ctypes.c_ubyte))
        sel = o.sel(b"fillBuffer:range:value:")
        for r in range(dest.shape[0]):
            fill(self._zero_enc, sel, sb.handle, _NSRange(base + r * row, length), 0)

    def zero_columns_done(self, wait=True):
        """Commit the collected zeroing and wait for it and every command still in flight on
        this context -- or, wait=False, leave them in flight: the zeroing then signals this
        context's event, which other contexts' command buffers wait on (_new_cmd), and
        settle_writes() waits on the host."""
        enc = getattr(self, "_zero_enc", None)
        dev = getattr(self, "_device_state", None)
        if not wait and dev is not None:
            if enc is None:
                with self.o.autorelease_pool():
                    cmd = self._new_cmd(shared_ok=False)
                    self.o.call(cmd, b"retain")
                self._zero_cmd = cmd
            else:
                self._zero_enc = None
                self.o.call(enc, b"endEncoding", restype=None)
                self.o.call(enc, b"release", restype=None)
            if getattr(self, "_signal_event", None) is None:
                self._signal_event = self.o.call(self.device, b"newSharedEvent")
                self._signal_value = 0
            self._signal_value += 1
            self.o.call(self._zero_cmd, b"encodeSignalEvent:value:", restype=None,
                        args=(self._signal_event, self._signal_value),
                        argtypes=(ctypes.c_void_p, ctypes.c_uint64))
            self._cmd_prefix = ""
            self._commit(self._zero_cmd, "zero", async_submit=True)
            if self not in dev.pending_contexts:
                dev.pending_contexts.append(self)
            return
        try:
            if enc is not None:
                self._zero_enc = None
                self.o.call(enc, b"endEncoding", restype=None)
                self.o.call(enc, b"release", restype=None)
                self._cmd_prefix = ""
                self._commit(self._zero_cmd, "zero")
            self._drain()
        finally:
            self._keep_until_done.clear()
        self.settle_writes()

    def settle_writes(self):
        """Wait for every write left in flight on this device (zero_columns_done(wait=False)),
        and release the host memory those commands read in place."""
        dev = getattr(self, "_device_state", None)
        if dev is None:
            self._drain()
            return
        ctxs, dev.pending_contexts = dev.pending_contexts, []
        for ctx in ctxs:
            try:
                ctx._drain()
            finally:
                ctx._keep_until_done.clear()

    #: zero_columns_done(wait=False) leaves the zeroing and the middle stage in flight.
    async_zero = True

    # ---- driver primitives (_gpuexec) -----------------------------------------------------
    #: The most threadgroups one dispatch takes, and the byte alignment of a bound view
    #: (setBuffer:offset: for the widest element a kernel reads, float2).
    max_dispatch_x = 2 ** 32 - 1
    storage_offset_alignment = 16

    def _x_kernel(self, name, n):
        if name in ("peaks", "peaks1"):
            return self.pipeline(n, "fusedTierB", name == "peaks1"), n // _radix(n)
        if name == "compact":
            return self.pipeline(0, "compactPeaks"), 256
        if name in ("full", "series", "forward"):
            entry = {"full": 'fullCorrelation', "series": 'fullCorrelationSeries',
                     "forward": 'seriesForward'}[name]
            return self.pipeline(n, entry), n // _radix(n)
        geometry = _manifest().get('full_tierc', {}).get(str(n))
        if geometry is None:
            raise UnsupportedSize('no two-stage full-correlation kernel for n=%d' % n)
        role, entry = {"tc1": ('corr1', 'tcStage1'), "tc2": ('corr2', 'tcFullStage3'),
                       "tcs2": ('corr_series2', 'tcFullSeriesStage3'),
                       "tf1": ('fwd1', 'tcForwardStage1'),
                       "tf2": ('fwd2', 'tcForwardStage3')}[name]
        return self.pipeline(n, entry), geometry[role]['local_size'][0]

    def _x_tierc(self, n):
        geometry = _manifest().get('full_tierc', {}).get(str(n))
        if geometry is None:
            raise UnsupportedSize('no two-stage full-correlation kernel for n=%d' % n)
        return geometry['n1'], geometry['n2']

    def _x_alloc(self, nbytes, readback=False, upload=False):
        return _Buffer(self, nbytes)

    def _x_list(self, label):
        return _MtlList(label)

    def _x_encode(self, cmd, ops, binds):
        """Encode a recorded list into a command buffer: serial compute encoders, a blit for
        a fill. Returns the buffers it bound."""
        enc, used = None, []
        for op in ops:
            if op[0] == "fill":
                if enc is not None:
                    self.o.call(enc, b'endEncoding', restype=None)
                    enc = None
                blit = self.o.call(cmd, b'blitCommandEncoder')
                self.o.call(blit, b'fillBuffer:range:value:', restype=None,
                            args=(op[1].handle, _NSRange(getattr(op[1], "offset", 0),
                                                         op[1].nbytes), op[2]),
                            argtypes=(ctypes.c_void_p, _NSRange, ctypes.c_uint8))
                self.o.call(blit, b'endEncoding', restype=None)
                continue
            if enc is None:
                enc = self.o.call(cmd, b'computeCommandEncoder')
            (pso, tg), groups, buffers, offsets, words = op
            bound = [binds[b.name] if isinstance(b, Arg) else b for b in buffers]
            used += bound
            flat = []
            for w in words:
                flat.extend(binds[w.name] if isinstance(w, Arg) else (w,))
            flat = tuple(int(w) & 0xFFFFFFFF for w in flat)
            if flat:
                self._dispatch(enc, pso, flat, bound, tg, groups=groups, offsets=offsets)
            else:                    # no uniforms: the buffers bind from index 0
                self.o.call(enc, b"setComputePipelineState:", restype=None,
                            args=(pso,), argtypes=(ctypes.c_void_p,))
                self._set_buffers(enc, bound, start=0, offsets=offsets)
                self.o.call(enc, b"dispatchThreadgroups:threadsPerThreadgroup:", restype=None,
                            args=(_MTLSize(groups, 1, 1), _MTLSize(tg, 1, 1)),
                            argtypes=(_MTLSize, _MTLSize))
        if enc is not None:
            self.o.call(enc, b'endEncoding', restype=None)
        return used

    @_autoreleased
    def _x_run(self, native, wait, binds=None, slot=None):
        label, ops = native
        cmd = self._command_buffer()
        self._x_encode(cmd, ops, binds)
        if wait:
            self._commit(cmd, label)
            return
        # Left in flight: it signals this context's event, which other contexts' command
        # buffers wait on (_new_cmd), and settle_writes() waits on the host.
        dev = self._device_state
        if getattr(self, "_signal_event", None) is None:
            self._signal_event = self.o.call(self.device, b"newSharedEvent")
            self._signal_value = 0
        self._signal_value += 1
        self.o.call(cmd, b"encodeSignalEvent:value:", restype=None,
                    args=(self._signal_event, self._signal_value),
                    argtypes=(ctypes.c_void_p, ctypes.c_uint64))
        self._commit(cmd, label, async_submit=True)
        if self not in dev.pending_contexts:
            dev.pending_contexts.append(self)

    @_autoreleased
    def _x_submit(self, native, binds, slot):
        label, ops = native
        cmd = self._command_buffer()
        self._x_encode(cmd, ops, binds)
        return self._commit(cmd, label, async_submit=True)

    @_autoreleased
    def _x_defer(self, native, binds, slot, source):
        """Held in the pending command buffer for the work that consumes it (several deferred
        forwards share it). A one-stage forward of a whole spectra workspace stays unencoded
        until its consumer is known: a hierarchical call reading these spectra takes it as
        forwardTier0 instead (_claim_forward), else it is encoded (_materialize_forward)."""
        label, ops = native
        pending = self._pending_metal
        if pending is not None:
            cmd = pending[0]
        else:
            self._flush_forward()          # an earlier deferred forward nothing reads
            cmd = self._new_cmd()
            self.o.call(cmd, b"retain")
        held = tuple(pending[1]) if pending is not None else ()
        if (source is not None and source[3] == 0 and ops[0][3] in (None, [0, 0, 0])
                and _fused_forward_enabled()):
            # Its kernel reads block i's start at element i of starts and writes row i of
            # spectra from the binding's start: true of a whole-workspace forward.
            n, series, starts, _, count, nser, code, spectra, _ = source
            (pso, _), _, _, _, _ = ops[0]           # the forward dispatch
            buffers = [series, starts, spectra]
            self._lazy_fwd = list(getattr(self, "_lazy_fwd", None) or ()) + [
                (n, pso, buffers, count, (nser, code), cmd)]
            self._pending_metal = (cmd, held + tuple(buffers))
            return
        used = self._x_encode(cmd, ops, binds)
        self._pending_metal = (cmd, held + tuple(used))

    @staticmethod
    def _x_upload(buf, array, slot):
        buf.write(array)

    def _x_prefetch(self, view, offset, nbytes, slot):
        pass

    def _x_after_readers(self):
        pass                # no wait added (open question: docs/unification-plan.md log)

    def _x_release(self, native):
        # Nothing recorded (every run encodes afresh); a deferred forward may still use the
        # buffers about to be freed: finish it first.
        if self._pending_metal is not None:
            self._flush_forward()

    @staticmethod
    def _x_read(buf, out, offset=0):
        ctypes.memmove(out.ctypes.data, buf.ptr + offset, out.nbytes)

    # ---- hierarchical -----------------------------------------------------
    def _simd_width(self, band):
        """threadExecutionWidth of this band's coarse pipeline (32 on Apple GPUs): what the
        coarse packing fills, queried rather than assumed (cross-platform review)."""
        cache = self.__dict__.setdefault("_simd_widths", {})
        if band not in cache:
            width = None
            try:
                pso = self.pipeline(band, "coarse16")
                width = self.o.call(pso, b"threadExecutionWidth", restype=ctypes.c_ulong)
            except (MetalError, UnsupportedSize, AttributeError, TypeError):
                pass
            cache[band] = int(width) if isinstance(width, int) and width > 0 else TARGET_THREADS
        return cache[band]

    def _coarse_layout(self, band):
        """The coarse layout (ppg, tile, twt) at this band: the fastest of _coarse_candidates on
        this device, timed once and kept in MF_COST_FILE (the choice every backend makes,
        _coarse). A fixed packing rule missed both ways on an M2: band 512 wants two pairs per
        threadgroup (25.7 against 26.4 ns per pair), band 1024 one (52.7 against 54.8),
        though one pair fills the SIMD group at both."""
        from . import gatechain
        from ._coarse import forced_layout, layout_label, stored_measured_choice
        return stored_measured_choice(
            self.__dict__.setdefault("_coarse_layouts", {}), "mtl-coarse",
            getattr(self, "name", ""), band, self._coarse_candidates(band),
            lambda c: layout_label(band, *c), gatechain.gpu_kernel_id("metal"),
            lambda cs: self._time_coarse_layouts(band, cs),
            tiebreak=lambda c: (c[1], c[2], c[0]), forced=forced_layout(band))

    def _coarse_candidates(self, band):
        """Every coarse layout (ppg, tile, twt) the choice may take at this band: the untiled
        build at every shipped packing that fits a threadgroup, with each twiddle source, then
        the tiles at the packing that fills the SIMD width. The first is the default without
        a measurement (coarse_geometry's)."""
        from ._coarse import coarse_stem, shipped_tiles
        w = self._simd_width(band)
        wg = band // _radix(band)
        built = [p for p in (1, 2, 4, 8, 16, 32) if shipped_tiles(band, p, _shipped)]
        tp = next((p for p in built if wg * p >= w), built[-1]) if built else None
        tiles = shipped_tiles(band, tp, _shipped) if tp else ()
        untiled = [(p, 1, t) for p in (1, 2, 4, 8, 16, 32)
                   if (p == 1 or _shipped(coarse_stem(band, p, 1))) and wg * p <= 1024
                   for t in (0, 1)]
        tiled = [(tp, t, x) for t in tiles for x in (0, 1)]
        first = tiled[:1] or [(coarse_ppg(band, 1 << 20, simd_width=w), 1, 0)]
        return first + [c for c in untiled + tiled if c not in first]

    def coarse_layouts(self, band):
        """The names (_coarse.layout_label) of every coarse layout the choice may take at this
        band on this device; MF_COARSE_LAYOUT forces one."""
        from ._coarse import layout_label
        return [layout_label(band, *c) for c in self._coarse_candidates(band)]

    def _time_coarse_layouts(self, band, cands, pairs=65536, ntm=16, reps=4):
        """Device seconds per pair of each coarse layout (ppg, tile, twt) on synthetic data: a
        warm-up, then the untiled and the tiled layouts as two stages of reps - 1 interleaved
        rounds, each stage's fastest confirmed against the fastest (_coarse.time_staged), in
        self.coarse_times[band] for reports. A layout this device cannot build is dropped."""
        from ._coarse import Timings, coarse_launch, coarse_stem, layout_label, time_staged
        ndm = pairs // ntm
        rng = np.random.default_rng(0)
        x = (rng.standard_normal((ndm, band)) + 1j * rng.standard_normal((ndm, band))) * 0.1
        bufs = [_Buffer(self, ndm * band * 4), _Buffer(self, ntm * band * 4),
                _Buffer(self, pairs * 4), _Buffer(self, pairs * 8)]
        bufs[0].write(_pack_half2(x))
        bufs[1].write(_pack_half2(x[:ntm]))
        shift = band.bit_length() - 1
        gate = (band // _radix(band) <= self._simd_width(band)
                and os.environ.get("MF_VK_C16_BOUND", "1") != "0")
        launch = {}

        def time_one(c):
            pso, slot_val, groups, thr, tg = launch[c]
            cmd = self.o.call(self.queue, b"commandBuffer")
            enc = self.o.call(cmd, b"computeCommandEncoder")
            # Encoded here, not through _dispatch: the calibration is not the call's
            # work, and _dispatch is what per-kernel profilers and tests observe.
            self.o.call(enc, b"setComputePipelineState:", restype=None,
                        args=(pso,), argtypes=(ctypes.c_void_p,))
            self._set_params(enc, (ntm, 0, band, slot_val, shift, 1, thr))
            self._set_buffers(enc, bufs)
            self.o.call(enc, b"dispatchThreadgroups:threadsPerThreadgroup:", restype=None,
                        args=(_MTLSize(groups, 1, 1), _MTLSize(tg, 1, 1)),
                        argtypes=(_MTLSize, _MTLSize))
            self.o.call(enc, b"endEncoding", restype=None)
            self.o.call(cmd, b"commit", restype=None)
            self.o.call(cmd, b"waitUntilCompleted", restype=None)
            t0 = self.o.call(cmd, b"GPUStartTime", restype=ctypes.c_double)
            t1 = self.o.call(cmd, b"GPUEndTime", restype=ctypes.c_double)
            if not (isinstance(t0, float) and isinstance(t1, float) and t1 > t0):
                return None                     # no device timestamps: nothing to choose by
            return t1 - t0

        try:
            for c in cands:                 # (ppg, tile, twt): twt 1 is the fp16 twiddle table
                ppg, tile, twt = c
                stem = coarse_stem(band, ppg, tile)
                try:
                    pso = self.pipeline(band, "coarse16" + stem[len("tierb_%d_c16" % band):]
                                        + ("w" if twt else ""))
                except (MetalError, UnsupportedSize):
                    continue                # past this device's limits for the kernel
                slot_val, groups = coarse_launch(ndm, ntm, ppg, tile, band)
                thr = (int(np.float32(1.1754944e-38).view(np.uint32))
                       if gate and tile > 1 else 0)
                launch[c] = (pso, slot_val, groups, thr, band // _radix(band) * ppg)
            ok = [c for c in cands if c in launch]
            # A warm-up dispatch each, then interleaved rounds and a paired confirmation of
            # the contenders (_coarse: the GPU may be shared).
            for c in ok:
                if time_one(c) is None:
                    return None
            times = time_staged([[c for c in ok if c[1] == 1], [c for c in ok if c[1] > 1]],
                                time_one, rounds=reps - 1)
            if times is None:
                return None
            out = Timings({t: v / pairs for t, v in times.items()})
            out.close = times.close
        finally:
            for b in bufs:
                b.destroy()
        self.__dict__.setdefault("coarse_times", {}).setdefault(band, {}).update(
            {layout_label(band, *c): v for c, v in out.items()})
        return out

    @_autoreleased
    def hier_peaks(self, n, band, data, tmpl, ct0, raw_thr,
                   binsize=None, threshold=0.0, window=None,
                   upload_data=True, upload_tmpl=True,
                   cascade_band=None, ct1=None, raw_thr1=None,
                   slot=None, async_submit=False, sparse=False):
        """The whole hierarchical filter in ONE command buffer.

        One or two gate tiers, then listed refinement at n. Tier 0 correlates
        every pair at its band (half width where that kernel exists); a
        compaction lists the pairs whose maximum clears the tier's threshold,
        and that list's length lands in an indirect-dispatch argument, so the
        survivor count never reaches the host. A second tier refines only the
        listed pairs at its own band, at full precision, and is compacted the
        same way before the final refine. Shared input uses a preceding GPU
        coarse-band extraction per tier.

        Two tiers are (cascade_band, ct0, raw_thr) then (band, ct1, raw_thr1),
        the order HierarchicalFilter passes them. An incomplete cascade
        raises: running one tier with another tier's threshold would be a
        different computation, not a slower one.
        """
        band, ct0, raw_thr, cascade_band, ct1, raw_thr1 = hier_tiers(
            n, band, ct0, raw_thr, cascade_band, ct1, raw_thr1)
        if cascade_band is None:
            tiers = ((int(band), ct0, float(raw_thr)),)
        else:
            tiers = ((int(cascade_band), ct0, float(raw_thr)),
                     (int(band), ct1, float(raw_thr1)))
            if not tiers[0][0] < tiers[1][0] < n:
                raise ValueError("cascade bands must increase below n: %r"
                                 % ((tiers[0][0], tiers[1][0]),))

        nd, nt = data.shape[0], tmpl.shape[0]
        pairs = nd * nt
        lo, hi, binsize, nbins = hier_window(n, window, binsize)
        if nbins > _MAX_BINS:
            return split_bins(
                lambda w, ud, ut: self.hier_peaks(
                    n, band, data, tmpl, ct0, raw_thr, binsize=binsize, threshold=threshold,
                    window=w, upload_data=ud, upload_tmpl=ut, cascade_band=cascade_band,
                    ct1=ct1, raw_thr1=raw_thr1, slot=slot, async_submit=False),
                lo, hi, binsize, _MAX_BINS, upload_data, upload_tmpl, sparse, async_submit)
        shift = bin_shift(binsize)
        t2 = float(threshold) ** 2 if threshold > 0 else 0.0
        # Half width only for the first tier: a later tier is the full-
        # precision refine kernel, which reads float2.
        half = [i == 0 and _use_c16(b) for i, (b, _, _) in enumerate(tiers)]
        sfx = ["" if i == 0 else str(i) for i in range(len(tiers))]
        # Pairs per threadgroup and tile for the first tier. Every packed launch is
        # ragged (_coarse.coarse_launch): no padded rows or spare outputs.
        if half[0]:
            centry, ppg, ctile, cgroups, ragged = coarse_geometry(
                tiers[0][0], nd, nt, self._simd_width(tiers[0][0]), self._coarse_layout)
        else:
            centry, ppg, ctile, cgroups, ragged = "fusedTierB", 1, 1, pairs, False

        # In flight, a result owns its buffers: the slot is part of the key.
        slot = slot if async_submit else None
        key = (n, tuple(b for b, _, _ in tiers), nd, nt, nbins, centry)
        key += (shared_key(data, self), shared_key(tmpl, self), slot)
        upload_data, upload_tmpl, dsig, tsig = self._input_uploads(
            key, data, tmpl, upload_data, upload_tmpl)
        bufs = self._hier.get(key)
        if bufs is None:
            incoming = [b for a in (data, tmpl)
                        if (b := shared_buffer(a, self)) is not None]
            estimate = 8*n*(nd+nt) + nd*nt*12*nbins
            estimate += sum((4 if h else 8)*b*(nd+nt) + 16*nd*nt + 12
                            for (b, _, _), h in zip(tiers, half))
            estimate -= sum(a.nbytes for a in (data, tmpl)
                            if shared_buffer(a, self) is not None)
            self._cache_room(estimate, incoming=incoming)
            bufs = {
                "data":  shared_buffer(data, self) or _Buffer(self, nd * n * 8),
                "tmpl":  shared_buffer(tmpl, self) or _Buffer(self, nt * n * 8),
                "idx":   _Buffer(self, nd * nt * nbins * 4),
                "val":   _Buffer(self, nd * nt * nbins * 8),
            }
            for i, ((b, _, _), h) in enumerate(zip(tiers, half)):
                cb = 4 if h else 8
                bufs["cdata" + sfx[i]] = _Buffer(self, nd * b * cb)
                bufs["ct" + str(i)] = _Buffer(self, nt * b * cb)
                bufs["cidx" + sfx[i]] = _Buffer(self, pairs * 4)
                bufs["cval" + sfx[i]] = _Buffer(self, pairs * 8)
                # Compacted survivors and the indirect threadgroup count:
                # args is [groupsX, 1, 1] and the compaction bumps [0]
                # atomically, so the count stays on the device.
                bufs["surv" + sfx[i]] = _Buffer(self, pairs * 4)
                bufs["args" + sfx[i]] = _Buffer(self, 12)
            self._hier[key] = bufs
            # Fresh buffers hold nothing, whatever the caller's dirty flags
            # say. Trusting them here is exactly how the Vulkan path once
            # served a previous call's data out of a newly allocated buffer,
            # and every index came back -1.
            upload_data = upload_tmpl = True
        self._cache_touch("hier", key)
        self._claim(bufs["idx"])                 # an earlier result still reading these outputs
        shared_data = shared_buffer(data, self) is not None
        if upload_data:
            write_input(bufs["data"], data)
            if not shared_data:
                for i, ((b, _, _), h) in enumerate(zip(tiers, half)):
                    bufs["cdata" + sfx[i]].write(
                        _pack_half2(data[:, :b]) if h else
                        np.ascontiguousarray(data[:, :b], np.complex64))
            self._uploaded["data"][key] = dsig
        if upload_tmpl:
            write_input(bufs["tmpl"], tmpl)
            for i, ((_, ct, _), h) in enumerate(zip(tiers, half)):
                bufs["ct" + str(i)].write(_pack_half2(ct) if h else
                                          np.ascontiguousarray(ct, np.complex64))
            self._uploaded["tmpl"][key] = tsig

        out = nd * nt * nbins
        for i in range(len(tiers)):
            bufs["args" + sfx[i]].write(np.array([0, 1, 1], dtype=np.uint32))
        if len(tiers) > 1:
            # Tier 1 visits only tier 0's survivors; every other pair must
            # read as dismissed to the compaction after it.
            bufs["cval1"].write(np.zeros(pairs * 2, dtype=np.float32))
        if not sparse:
            # Dense: every unrefined pair must read as dismissed. Sparse reads only the
            # listed pairs, every bin of which the refine writes, so it skips this fill.
            bufs["idx"].write(np.full(out, -1, dtype=np.int32))
            bufs["val"].write(np.zeros(out * 2, dtype=np.float32))

        compact = self.pipeline(tiers[0][0], "compactPairs")
        # Every pipeline before the encoder opens: a build failure raised with an encoder
        # open aborts the process (an encoder released without endEncoding).
        coarse0 = self.pipeline(tiers[0][0], centry)
        refine = self.pipeline(n, "refineListed", nbins == 1)
        # Fused forward (forward_tier0.slang): when this call reads the spectra a deferred
        # forward is about to write, that forward writes only the bands the tiers read, and
        # the refine's blocks are recomputed in full (markBlocks + seriesForwardListed).
        fwd = None
        # The band forward (forward_tier0) when it moves fewer bytes than the full one for
        # this call shape, by its refine-block fraction measured last time (finish, below).
        top = max(b for b, _, _ in tiers)
        band_ok = (shared_data and half[0] and not any(half[1:]) and len(tiers) <= 2
                   and _fused_forward_enabled())
        if band_ok and band_forward_wanted(
                n, top, self.__dict__.get("_band_f", {}).get((n, top, nd, nt))):
            fwd = self._claim_forward(bufs["data"], nd)
            if fwd is not None:
                try:
                    fpso = (self.pipeline(n, "forwardTier0"), self.pipeline(n, "seriesForwardListed"),
                            self.pipeline(n, "markBlocks"))
                except (MetalError, UnsupportedSize, OSError):
                    self._lazy_fwd = list(getattr(self, "_lazy_fwd", None) or ()) + [fwd]
                    fwd = None
            if fwd is not None:
                _FUSED_FORWARDS[0] += 1
                if "flags" not in bufs:
                    bufs["flags"] = _Buffer(self, nd * 4)
                    bufs["blist"] = _Buffer(self, nd * 4)
                    bufs["bargs"] = _Buffer(self, 12)
                bufs["flags"].write(np.zeros(nd, np.uint32))
                bufs["bargs"].write(np.array([0, 1, 1], dtype=np.uint32))
        cmd = self._command_buffer()
        enc = self.o.call(cmd, b"computeCommandEncoder")

        def use(*names):
            return [bufs[nm] for nm in names]

        def bits(x):
            return int(np.float32(x).view(np.uint32))

        if fwd is not None:
            # series, starts as the deferred forward bound them; bands straight into the
            # tiers' inputs (band1 unused, and bound to cdata, for a one-tier chain).
            _, _, (series_b, starts_b, _), _, (size, code), _ = fwd
            b1 = tiers[1][0] if len(tiers) > 1 else 0
            self._dispatch(enc, fpso[0], (size, tiers[0][0], b1, code),
                           [series_b, starts_b, bufs["cdata"],
                            bufs["cdata1"] if len(tiers) > 1 else bufs["cdata"]],
                           n // _radix(n), groups=nd)
        elif shared_data:
            pack = self.pipeline(4096, "packCoarse")
            for i, ((b, _, _), h) in enumerate(zip(tiers, half)):
                self._dispatch(enc, pack, (n, b, nd*b, int(h)),
                               use("data", "cdata" + sfx[i]),
                               256, groups=(nd*b + 255)//256)

        for i, ((b, _, thr), h) in enumerate(zip(tiers, half)):
            cs, ce, csp, csh = coarse_span(n, b, lo, hi)
            span = (cs, ce, csp, csh & 0xFFFFFFFF)
            if i == 0:
                coarse = coarse0
                # A ragged build reads the data row count from the binsize slot
                # (coarse_launch), which the one-bin coarse role does not otherwise use.
                # Tiled fp16 builds whose pair fits one SIMD group take the gate threshold
                # (magnitude, > 0) in the last slot and report only the gate's decision and
                # bound (tierb.slang peakTwoGate: no election; tier 0's index has no
                # reader). A threshold of 0 is passed as the smallest normal float, which
                # passes the same pairs (a nonzero maximum). 0 elects every pair
                # (peakTwoWave): the raw (unbounded) build, and every other build, which
                # reads the slot as a squared seed.
                gate = (h and ctile > 1 and b // _radix(b) <= self._simd_width(b)
                        and os.environ.get("MF_VK_C16_BOUND", "1") != "0")
                cparams = (nt, span[0], span[1], nd if ragged else span[2], *span[3:], 1,
                           bits(max(float(thr), 1.1754944e-38)) if gate else 0)
                self._dispatch(enc, coarse, cparams,
                               use("cdata", "ct0", "cidx", "cval"),
                               b // _radix(b) * ppg, groups=cgroups)
            else:
                # The listed refine at this band over the previous tier's
                # survivors; one bin, so cval holds each listed pair's maximum.
                # nbins = 0 asks a single-bin build at a gate band (<= 1024) for the gate
                # decision only (the window's maximum |v|; tierb.slang gateOnly): the
                # compaction below is all that reads it. Other builds read nbins as the bin
                # count: always 1.
                listed = self.pipeline(b, "refineListed", True)
                single = b <= 1024 and (b, "refineListed", True) in self._pipelines
                self._dispatch(enc, listed, (nt, *span, 0 if single else 1, 0),
                               use("cdata" + sfx[i], "ct" + str(i), "cidx" + sfx[i],
                                   "cval" + sfx[i], "surv" + sfx[i - 1]),
                               b // _radix(b), indirect=bufs["args" + sfx[i - 1]])
            # A later tier's compaction walks every pair, and the pairs tier 0 dismissed hold the
            # zeros written above: at a threshold of 0 they would pass (!(0 < 0)). The smallest
            # normal float dismisses them and passes every pair the tier saw with a nonzero
            # maximum (tests/test_tier_conformance.py).
            self._dispatch(enc, compact, (pairs, bits(thr if i == 0 else max(thr, 1.1754944e-38)),
                                          nbins),
                           use("cval" + sfx[i], "surv" + sfx[i], "args" + sfx[i]),
                           256, groups=(pairs + 255) // 256)

        last = sfx[-1]
        if fwd is not None:
            # The refine reads full spectra of its survivors' blocks only: recompute those.
            self._dispatch(enc, fpso[2], (nt,),
                           [bufs["surv" + last], bufs["args" + last], bufs["flags"],
                            bufs["blist"], bufs["bargs"]], 256, groups=(pairs + 255) // 256)
            self._dispatch(enc, fpso[1], (size, code),
                           [series_b, starts_b, bufs["data"], bufs["blist"]],
                           n // _radix(n), indirect=bufs["bargs"])
        self._dispatch(enc, refine,
                       (nt, lo, hi, binsize, shift & 0xFFFFFFFF, nbins, bits(t2)),
                       use("data", "tmpl", "idx", "val", "surv" + last),
                       n // _radix(n), indirect=bufs["args" + last])
        self.o.call(enc, b"endEncoding", restype=None)

        def finish():
            count = int(bufs["args" + last].read(np.uint32, 1)[0])
            self.last_refinements = count
            if len(tiers) > 1:
                self.last_tier1_survivors = int(bufs["args"].read(np.uint32, 1)[0])
            if band_ok:
                # This shape's refine-block fraction, for its next call's band/full choice
                # and for the forward pricing (gatechain).
                f = refine_block_fraction(bufs["surv" + last].view(np.uint32, count), nt, nd)
                self.__dict__.setdefault("_band_f", {})[(n, top, nd, nt)] = f
                from . import gatechain as _gc
                _gc.note_refine_blocks(n, top, f)
            if sparse:
                from . import _SparsePeaks
                rows = np.sort(bufs["surv" + last].view(np.uint32, count).astype(np.int64))
                ri = bufs["idx"].view(np.int32, out).reshape(pairs, nbins)[rows]
                k, b = np.nonzero(ri >= 0)
                vals = bufs["val"].view(np.complex64, out).reshape(pairs, nbins)
                return _SparsePeaks((nd, nt, nbins), rows[k] * nbins + b, ri[k, b],
                                    vals[rows[k], b])
            idx = bufs["idx"].read(np.int32, out).reshape(nd, nt, nbins)
            val = bufs["val"].read(np.complex64, out).reshape(nd, nt, nbins)
            return idx, val
        return self._commit(cmd, "hier" if len(tiers) == 1 else "hier_cascade",
                            async_submit=async_submit, finish=finish, owner=bufs["idx"])

    def _check_completed(self, cmd):
        """A command buffer that did not complete, said so.

        The GPU reports failure by status rather than by raising, so without
        this a kernel that never ran returns whatever the output buffer
        happened to hold -- zeros, or the previous call's answer.
        """
        status = int(self.o.call(cmd, b"status", restype=ctypes.c_ulong))
        if status == 4:                       # MTLCommandBufferStatusCompleted
            return
        err = self.o.call(cmd, b"error")
        raise MetalError("dispatch did not complete (status %d): %s"
                         % (status, describe_error(
                             self.o, ctypes.c_void_p(err)) if err
                            else "no error object"))

    def _evict_record(self, kind, key, keep_storage=None):
        if kind == "exec":
            return self._exec_evict(key)
        # In-flight results read these buffers when they are collected.
        self._drain()
        batch = self._record_tables()[kind].pop(key)
        for buf in self._record_buffers(batch):
            buf.destroy()
        for resident in self._uploaded.values():
            resident.pop(key, None)

    def clear_cache(self):
        self._drain()
        self.cancel_forward()
        self._exec_clear()
        for table in self._record_tables().values():
            for record in table.values():
                for buf in self._record_buffers(record):
                    buf.destroy()
            table.clear()
        self._uploaded = {"data": {}, "tmpl": {}}
        self._cache_order = {}

    def destroy(self):
        if getattr(self, "device", None) is None:
            return
        self.cancel_forward()
        dev = getattr(self, "_device_state", None)
        if dev is not None and self in dev.pending_contexts:
            self.settle_writes()
        self.clear_cache()
        if getattr(self, "_signal_event", None) is not None:
            self.o.call(self._signal_event, b"release", restype=None)
            self._signal_event = None
        shared = dev is not None
        if not shared:
            # A context that owns its device (built without _Device) owns its pipelines.
            for pipeline in self._pipelines.values():
                self.o.call(pipeline, b"release", restype=None)
            self._pipelines.clear()
        if self.queue:
            self.o.call(self.queue, b"release", restype=None)
            self.queue = None
        if not shared:
            self.o.call(self.device, b"release", restype=None)
        self.device = None

    def __del__(self):
        """Release the device buffers when the context is dropped.

        Metal does not hold the file descriptors Vulkan does, so this is not
        the leak that exhausted RLIMIT_NOFILE -- but a dropped context still
        held its batch and hierarchical buffers until the process ended, and
        the two backends should not differ on whether going out of scope
        frees anything.
        """
        try:
            self.destroy()
        except Exception:
            pass
