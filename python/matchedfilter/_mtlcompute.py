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
from ._shared import empty_shared, shared_buffer
from ._gpuhost import MAX_BINS

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
from ._gpu_cache import InputUploads
from ._gpuexec import Arg, Executor, register_fusion, settle as _settle


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
    """A shared-storage buffer, mapped for the lifetime of the object. Slotted: a search
    holds thousands, and every full garbage collection walks them."""
    __slots__ = ("ctx", "nbytes", "handle", "ptr", "_bytes", "__dict__")

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
        """The first `count` elements as a NumPy view of the buffer (no copy). The bytes are
        wrapped once: a result reads several views per call."""
        raw = getattr(self, "_bytes", None)
        if raw is None:
            raw = self._bytes = np.frombuffer((ctypes.c_ubyte * self.nbytes).from_address(
                self.ptr.value if hasattr(self.ptr, "value") else self.ptr), np.uint8)
        return raw[:count * np.dtype(dtype).itemsize].view(dtype)

    def read_into(self, out):
        """Zero-copy direct read into caller-provided contiguous array."""
        ctypes.memmove(out.ctypes.data, self.ptr, min(self.nbytes, out.nbytes))
        return out

    def destroy(self):
        if self.handle:
            self.ctx.o.call(self.handle, b"release")
            self.handle = None


class _Section:
    """Bytes [offset, offset + nbytes) of a _Buffer (Context._x_section)."""
    __slots__ = ("base", "handle", "offset", "nbytes", "ptr")

    def __init__(self, base, offset, nbytes):
        self.base, self.handle, self.offset, self.nbytes = base, base.handle, offset, nbytes
        self.ptr = (base.ptr.value if hasattr(base.ptr, "value") else base.ptr) + offset

    def write(self, array):
        flat = np.ascontiguousarray(array)
        ctypes.memmove(self.ptr, flat.ctypes.data, min(flat.nbytes, self.nbytes))

    def view(self, dtype, count):
        dtype = np.dtype(dtype)
        return self.base.view(np.uint8, self.offset + count * dtype.itemsize)[self.offset:].view(dtype)

    def destroy(self):
        pass                                    # the base buffer owns the memory


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
        #: Writes left in flight (a run with wait=False; Executor._writes), as _Write tokens.
        #: Each context signals its own MTLSharedEvent after them (one event per queue: a
        #: shared one could be set back by a later, lower signal from another queue).
        #: Contexts have their own queues, so another context's command buffer waits on
        #: those events on the GPU (Context._new_cmd) -- no host wait between the stages.
        self.pending_writes = []
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
        for c in _writers(self.dev):
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
        """Commit the current buffer."""
        if self.cmd is None:
            return
        cmd, self.cmd, self.count = self.cmd, None, 0
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


register_fusion(fused)


def settle_all():
    """Wait for every write left in flight on any Metal device (a host read follows)."""
    for dev in _DEVICES.values():
        _settle(dev.pending_writes)


class _Write:
    """A write left in flight (Executor._writes): a command buffer of `ctx` that signals
    its event. Settling waits for everything that context has in flight and releases the
    host memory those commands read in place."""
    __slots__ = ("ctx",)

    def __init__(self, ctx):
        self.ctx = ctx

    def settle(self):
        try:
            self.ctx._drain()
        finally:
            self.ctx._keep_until_done.clear()


def _writers(dev):
    """The contexts with writes left in flight on `dev`, once each."""
    return list({id(w.ctx): w.ctx for w in dev.pending_writes}.values())


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

    def listed(self, kernel, count, max_groups, buffers, words=(), offsets=None):
        # Indirect, sized by the count a kernel wrote; gridSize is the upper bound, so each
        # threadgroup takes one item.
        flat = []
        for w in words:
            flat.extend(w if isinstance(w, tuple) else (w,))
        self.ops.append((kernel, ("indirect", count), list(buffers), offsets,
                         flat + [int(max_groups)]))

    def fill(self, buf, word, offset=0, nbytes=None, rows=1, pitch=0):
        if word not in (0, 0xFFFFFFFF):
            raise ValueError("a fill is a byte pattern: 0 or 0xFFFFFFFF")
        self.ops.append(("fill", buf, 0xFF if word else 0, offset,
                         buf.nbytes - offset if nbytes is None else nbytes, rows, pitch))

    def update(self, buf, words):
        # Shared storage: written by the host as the run is encoded. A record's earlier run
        # has been collected by then (_claim), so nothing in flight still reads it.
        self.ops.append(("update", buf, np.asarray(words, np.uint32)))

    def readback(self, buf, nbytes):
        pass                        # shared storage: the host reads it after the run

    def end(self):
        return self.label, self.ops


def _function(entry):
    """The function an entry's library declares: the coarse builds are fusedTierB's, and the
    listed refine is refine_bounded.slang's on every target (tools/build_spirv.py)."""
    if entry.startswith("coarse16"):
        return "fusedTierB"
    return "refineListedBounded" if entry == "refineListed" else entry


class Context(Executor, InputUploads):
    """A queue and dispatch caches on one process-wide Metal device (see _Device)."""

    max_grouped_bins = _MAX_BINS
    #: shared_buffer() may hand back a view inside an allocation (one row of a device-
    #: resident middle output); every binding adds its offset.
    shared_views = True
    _timing = False

    def _x_peaks(self, out):
        """Theoretical peaks (_roofline.gpu_peaks): the core count plus a stated formula."""
        import re as _re
        from . import _roofline as _rl
        chip = next((k for k in _rl._APPLE_GPU if k in (out["name"] or "")), "M2")
        ghz, cores, bus, mts = _rl._APPLE_GPU[chip]
        try:
            import subprocess
            txt = subprocess.run(["ioreg", "-rc", "AGXAccelerator"], capture_output=True,
                                 text=True).stdout
            m = _re.search(r'"gpu-core-count"\s*=\s*(\d+)', txt)
            if m:
                cores = int(m.group(1))
        except OSError:
            pass
        # 128 fp32 ALUs per core; Apple GPUs before M3 run fp16 at the fp32 rate.
        f = cores * 128 * 2 * ghz * 1e9
        out.update(cores=cores, clock_ghz=ghz, flops=dict(fp32=f, fp16=f, int16=f),
                   bandwidth=bus * mts * 1e6 / 8,
                   formula="%d cores (ioreg gpu-core-count) x 128 ALUs x 2 x %.3f GHz (vendor "
                           "clock); fp16 at the fp32 rate" % (cores, ghz),
                   bandwidth_formula="%d-bit LPDDR x %d MT/s / 8 (vendor figure)" % (bus, mts))
        out["measured"] = _rl._MEASURED.get("Apple %s GPU" % chip)
        return out

    def __init__(self, index=0):
        if sys.platform != "darwin":
            raise MetalError("Metal is only available on macOS")
        self.device = self.queue = None
        self._pipelines = {}
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
        self._uploaded = {"data": {}, "tmpl": {}}

    # ---- kernels ----------------------------------------------------------
    def _library(self, stem, twt=False, macros=()):
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
        if lib_path.is_file() and not raw and not twt and not macros and not _ieee_kernel(stem):
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
        # The build-time constants (twiddle.slang), Vulkan's specialization constants:
        # MF_DATA_STRIDE, MF_DATA_SCALE_BITS and MF_ACCURATE_TRIG from the caller.
        values = dict(macros)
        if twt:
            values["MF_COARSE_TWT"] = 1
        if raw:
            values["MF_C16_RAW"] = 1
        o = self.o
        if values or _ieee_kernel(stem):
            opts = o.call(o.call(o.objc.objc_getClass(b"MTLCompileOptions"), b"alloc"), b"init")
        if values:
            table = o.call(o.call(o.objc.objc_getClass(b"NSMutableDictionary"), b"alloc"), b"init")
            for name, value in values.items():
                num = o.call(o.objc.objc_getClass(b"NSNumber"), b"numberWithUnsignedInt:",
                             args=(int(value) & 0xFFFFFFFF,), argtypes=(ctypes.c_uint32,))
                o.call(table, b"setObject:forKey:", restype=None,
                       args=(num, o.nsstring(name)), argtypes=(ctypes.c_void_p, ctypes.c_void_p))
            o.call(opts, b"setPreprocessorMacros:", restype=None, args=(table,),
                   argtypes=(ctypes.c_void_p,))
            o.call(table, b"release", restype=None)
        if _ieee_kernel(stem):
            # Gates must fail open: a value that overflows fp16 becomes inf, and an
            # inf - inf in the transform becomes NaN. Under the default fast-math the
            # compiler assumes neither exists and a NaN magnitude lost every comparison,
            # dismissing the loudest pair (tools/gate_margin.py --loud). IEEE semantics
            # make NaN and inf compare as the largest bit patterns, so they pass.
            o.call(opts, b"setFastMathEnabled:", restype=None, args=(False,),
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
        if entry == "seriesForwardBands":
            return "forward_bands_%d" % n
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
                           "compactListed": "compactl",
                           "refineListed": "refine",
                           "refineItems": "items",
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
    def pipeline(self, n, entry="fusedTierB", one_bin=False, c16=False, macros=(), gate=False):
        """A compute pipeline for `entry` at length n; macros: (name, value) build-time
        constants (twiddle.slang), one pipeline per set of values. gate: the one-bin build's
        gate-only variant (tierb.slang MF_GATE_ONLY)."""
        macros = tuple(sorted(macros))
        if c16 or entry.startswith("coarse16"):
            entry_name = entry if entry.startswith("coarse16") else "coarse16"
        else:
            entry_name = entry
        fn_name = _function(entry_name)
        single = (_manifest().get("modules", {}).get(str(n), {}).get("metal", {})
                  .get(entry_name, {}).get("one_bin")) if (one_bin and not entry_name.startswith("coarse16")) else None
        if single and gate:
            single = single.get("gate")
        if single and single["lds_bytes"] > self.max_shared_memory:
            single = None
        key = ((n, entry_name, "gate" if gate else True) if single else (n, entry_name)) + (
            (macros,) if macros else ())
        if entry_name.startswith("coarse16") and os.environ.get("MF_VK_C16_BOUND", "1") == "0":
            # The raw-maximum build (_library's MF_C16_RAW) is a different library: a process
            # that switches it (the physics tests) must not reuse the bound pipeline.
            key = key + ("raw",)
        if key in self._pipelines:
            return self._pipelines[key]
        base, twt = _twt_entry(entry_name)
        stem = pathlib.Path(single["msl"]).stem if single else self._stem(n, base)
        lib = self._library(stem, twt=twt, macros=macros)
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
            elif entry_name in ("compactPairs", "compactListed", "markBlocks", "compactPeaks"):
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

    def _x_timings(self):
        self._drain()

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
        for c in (_writers(dev) if dev is not None else ()):
            if c is not self:
                self.o.call(cmd, b"encodeWaitForEvent:value:", restype=None,
                            args=(c._signal_event, c._signal_value),
                            argtypes=(ctypes.c_void_p, ctypes.c_uint64))
        return cmd

    def _command_buffer(self):
        """An OWNED command buffer: retained here, so every path releases it exactly once in
        _commit, after completion (an autoreleased one would die with the pool of the method
        that made it, while still in flight)."""
        cmd = self._new_cmd()
        self.o.call(cmd, b"retain")
        self._cmd_prefix = ""
        return cmd

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
                args=(indirect.handle, getattr(indirect, "offset", 0), _MTLSize(tg, 1, 1)),
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

    # ---- driver primitives (_gpuexec) -----------------------------------------------------
    #: The most threadgroups one dispatch takes, and the byte alignment of a bound view
    #: (setBuffer:offset: for the widest element a kernel reads, float2).
    max_dispatch_x = 2 ** 32 - 1
    max_binding_bytes = None        # no per-binding limit below the allocation
    storage_offset_alignment = 16

    #: Libraries compile at run time, with the build-time constants as macros (twiddle.slang):
    #: the tiers read the spectra in place, at a stride and a data scale (_gpuhier feeds).
    inplace_feed = True
    #: Whose kernel identity stored measured choices are tied to (gatechain.gpu_kernel_id).
    kernel_family = "metal"

    @property
    def subgroup_size(self):
        """The SIMD-group width (threadExecutionWidth of a coarse pipeline; 32 on Apple)."""
        return self._simd_width(256)

    @staticmethod
    def _macros(c):
        """Library macros for a kernel's build-time constants (twiddle.slang)."""
        m = []
        if c.get("stride"):
            m.append(("MF_DATA_STRIDE", int(c["stride"])))
        if c.get("scale"):
            m.append(("MF_DATA_SCALE_BITS",
                      int(np.float32(2.0 ** int(c["scale"])).view(np.uint32))))
        if c.get("rowwin"):
            m.append(("MF_ROW_WINDOWS", 1))
        return tuple(m)

    def _x_kernel(self, name, n, consts=None):
        c = consts or {}
        macros = self._macros(c)
        if name in ("peaks", "peaks1", "gate"):
            return (self.pipeline(n, "fusedTierB", name == "peaks1", macros=macros),
                    n // _radix(n))
        if name == "coarse":
            from ._coarse import coarse_stem
            entry = ("coarse16" + coarse_stem(n, c["ppg"], c["tile"])[len("tierb_%d_c16" % n):]
                     + ("w" if c.get("twt") else ""))
            return self.pipeline(n, entry, macros=macros), n // _radix(n) * c["ppg"]
        if name in ("tier", "tier1", "refine", "refine1"):
            return (self.pipeline(n, "refineListed", name.endswith("1"), macros=macros,
                                  gate=bool(c.get("gate"))), n // _radix(n))
        if name == "compact_peaks":
            return self.pipeline(0, "compactPeaks"), 256
        fixed = {"compact": ("compactPairs", 256), "compactl": ("compactListed", 256),
                 "mark": ("markBlocks", 256), "pack": ("packCoarse", 256)}
        if name in fixed:
            entry, tg = fixed[name]
            return self.pipeline(4096 if name == "pack" else n, entry), tg
        entries = {"fwd_tier0": "forwardTier0", "fwd_bands": "seriesForwardBands",
                   "fwd_listed": "seriesForwardListed", "forward": "seriesForward",
                   "items": "refineItems",
                   "full": "fullCorrelation", "series": "fullCorrelationSeries"}
        if name in entries:
            return self.pipeline(n, entries[name]), n // _radix(n)
        geometry = _manifest().get('full_tierc', {}).get(str(n))
        if geometry is None:
            raise UnsupportedSize('no two-stage full-correlation kernel for n=%d' % n)
        role, entry = {"tc1": ('corr1', 'tcStage1'), "tc2": ('corr2', 'tcFullStage3'),
                       "tcs2": ('corr_series2', 'tcFullSeriesStage3'),
                       "tf1": ('fwd1', 'tcForwardStage1'),
                       "tf2": ('fwd2', 'tcForwardStage3')}[name]
        return self.pipeline(n, entry), geometry[role]['local_size'][0]

    @staticmethod
    def _x_has_c16(band):
        return _shipped("tierb_%d_c16" % band)

    @staticmethod
    def _x_has_kernel(name, n):
        if name == "tier1":
            info = ((_manifest().get("modules", {}).get(str(n)) or {}).get("metal") or {})
            return bool((info.get("refineListed") or {}).get("one_bin"))
        if name == "fwd_tier0":
            return _shipped("forward_tier0_%d" % n)
        if name == "items":
            info = ((_manifest().get("modules", {}).get(str(n)) or {}).get("metal") or {})
            return "refineItems" in info
        if name == "tier1gate":
            info = ((_manifest().get("modules", {}).get(str(n)) or {}).get("metal") or {})
            return bool(((info.get("refineListed") or {}).get("one_bin") or {}).get("gate"))
        raise ValueError(name)

    def _x_coarse_candidates(self, band):
        """Every coarse layout (subgroup 0, ppg, tile, twt) the choice may take at this band:
        the untiled build at every shipped packing that fits a threadgroup, with each twiddle
        source, then the tiles at the packing that fills the SIMD width. The first is the
        default without a measurement."""
        from ._coarse import coarse_stem, shipped_tiles
        w = self._simd_width(band)
        wg = band // _radix(band)
        built = [p for p in (1, 2, 4, 8, 16, 32) if shipped_tiles(band, p, _shipped)]
        tp = next((p for p in built if wg * p >= w), built[-1]) if built else None
        tiles = shipped_tiles(band, tp, _shipped) if tp else ()
        untiled = [(0, p, 1, t) for p in (1, 2, 4, 8, 16, 32)
                   if (p == 1 or _shipped(coarse_stem(band, p, 1))) and wg * p <= 1024
                   for t in (0, 1)]
        tiled = [(0, tp, t, x) for t in tiles for x in (0, 1)]
        first = tiled[:1] or [(0, coarse_ppg(band, 1 << 20, simd_width=w), 1, 0)]
        return first + [c for c in untiled + tiled if c not in first]

    @_autoreleased
    def _x_time(self, native, binds, reps):
        """The least device time (GPUStartTime..GPUEndTime) of `reps` runs, after a warm-up."""
        label, ops = native
        times = []
        for rep in range(reps + 1):
            cmd = self.o.call(self.queue, b"commandBuffer")
            self._x_encode(cmd, ops, binds or {})
            self.o.call(cmd, b"commit", restype=None)
            self.o.call(cmd, b"waitUntilCompleted", restype=None)
            t0 = self.o.call(cmd, b"GPUStartTime", restype=ctypes.c_double)
            t1 = self.o.call(cmd, b"GPUEndTime", restype=ctypes.c_double)
            if rep and isinstance(t0, float) and isinstance(t1, float) and t1 > t0:
                times.append(t1 - t0)
        return min(times) if times else float("inf")

    def _x_tierc(self, n):
        geometry = _manifest().get('full_tierc', {}).get(str(n))
        if geometry is None:
            raise UnsupportedSize('no two-stage full-correlation kernel for n=%d' % n)
        return geometry['n1'], geometry['n2']

    def _x_alloc(self, nbytes, readback=False, upload=False):
        return _Buffer(self, nbytes)

    def _x_list(self, label, once=False):
        return _MtlList(label)

    def _x_encode(self, cmd, ops, binds):
        """Encode a recorded list into a command buffer: serial compute encoders, a blit for
        a fill. Returns the buffers it bound."""
        enc, used = None, []
        for op in ops:
            if op[0] == "update":
                op[1].write(op[2])
                continue
            if op[0] == "fill":
                if enc is not None:
                    self.o.call(enc, b'endEncoding', restype=None)
                    enc = None
                _, buf, byte, offset, nbytes, rows, pitch = op
                base = getattr(buf, "offset", 0) + offset
                blit = self.o.call(cmd, b'blitCommandEncoder')
                fill = self.o.send(None, (ctypes.c_void_p, _NSRange, ctypes.c_ubyte))
                sel = self.o.sel(b"fillBuffer:range:value:")
                for r in range(rows):
                    fill(blit, sel, buf.handle, _NSRange(base + r * pitch, nbytes), byte)
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
            indirect = groups[1] if isinstance(groups, tuple) else None
            if flat:
                self._dispatch(enc, pso, flat, bound, tg,
                               groups=None if indirect is not None else groups,
                               indirect=indirect, offsets=offsets)
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
    def _x_run(self, native, wait, binds=None, slot=None, pre=()):
        label, ops = native
        cmd = self._command_buffer()
        for nat, b in pre:                      # deferred work first, in the same buffer
            self._x_encode(cmd, nat[1], b or {})
        self._x_encode(cmd, ops, binds or {})
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
        self._pend_write()

    def _pend_write(self):
        """This context's write token moved to the newest place on the device's list. One
        token per context: settling one drains the whole context, so a token per run only
        lengthened the list every new command buffer scans (_writers)."""
        token = self.__dict__.get("_write")
        if token is None:
            token = self._write = _Write(self)
        pend = self._writes()
        for i, w in enumerate(pend):
            if w is token:
                del pend[i]
                break
        pend.append(token)

    @_autoreleased
    def _x_submit(self, native, binds, slot, pre=()):
        label, ops = native
        cmd = self._command_buffer()
        for nat, b in pre:
            self._x_encode(cmd, nat[1], b or {})
        self._x_encode(cmd, ops, binds or {})
        return self._commit(cmd, label, async_submit=True)

    @staticmethod
    def _x_upload(buf, array, slot):
        buf.write(array)

    def _x_prefetch(self, view, offset, nbytes, slot):
        pass

    def _x_after_readers(self):
        pass                # no wait added (open question: docs/unification-plan.md log)

    @staticmethod
    def _x_release(native, done=False):
        pass                        # nothing recorded: every run encodes afresh

    def _x_idle(self):
        self._drain()
        self._keep_until_done.clear()   # the host memory those commands read in place

    @staticmethod
    def _x_free(buf):
        buf.destroy()

    @staticmethod
    def _x_section(buf, offset, nbytes):
        return _Section(buf, offset, nbytes)

    @staticmethod
    def _x_read(buf, out, offset=0):
        ctypes.memmove(out.ctypes.data, buf.ptr + offset, out.nbytes)

    @staticmethod
    def _x_view(buf, dtype, count):
        return buf.view(dtype, count)

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

    def clear_cache(self):
        self._drain()
        self.cancel_forward()
        self._exec_clear()
        self._uploaded = {"data": {}, "tmpl": {}}
        self._cache_order = {}

    def destroy(self):
        if getattr(self, "device", None) is None:
            return
        self._retire()
        self.cancel_forward()
        dev = getattr(self, "_device_state", None)
        if dev is not None and any(w.ctx is self for w in dev.pending_writes):
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
