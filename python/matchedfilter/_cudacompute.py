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
import struct
import os
import pathlib
import threading

import numpy as np

from ._coarse import TILE_PROBE
from . import _config, _cuda, _gputime
from ._cuda import check_cuda
from ._errors import UnsupportedSize
from ._gpu_cache import InputUploads
from ._gpuexec import Arg, Executor, settle as _settle
from ._shared import empty_shared, shared_buffer, _Borrowed
from ._gpuhost import MAX_BINS, bin_shift


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
        self.cuda = cuda
        self.ctx = ctypes.c_void_p()
        check_cuda(cuda.cuDevicePrimaryCtxRetain(ctypes.byref(self.ctx), device),
                   "cuDevicePrimaryCtxRetain")       # held for the process lifetime
        self.modules = {}
        self.pipelines = {}
        # Events after writes left in flight (correlate_series(wait=False)): every Context's
        # streams order their work after them; settle_writes() waits on them for the host.
        self.pending_writes = []
        self.occupancy = {}
        self.labels = {}
        self.c16_flags = {}         # coarse module stem -> [mf_c16_raw address, value]
        self.tc_persistent = {}     # persistent coarse kernel -> grid cap (blocks)


_DEVICE_SHARED = {}


def settle_all():
    """Wait for every write left in flight on any CUDA device (a host read follows)."""
    for shared in list(_DEVICE_SHARED.values()):
        pend = shared.__dict__.get("pending_writes") or []
        if pend:
            check_cuda(shared.cuda.cuCtxSetCurrent(shared.ctx), "cuCtxSetCurrent")
        _settle(pend)


class _Write:
    """A write left in flight (Executor._writes): an event recorded after it."""
    __slots__ = ("cuda", "event")

    def __init__(self, cuda, event):
        self.cuda, self.event = cuda, event

    def done(self):
        """Whether it has finished (the event is then freed)."""
        if self.event is not None and self.cuda.cuEventQuery(self.event) == 0:
            self.cuda.cuEventDestroy_v2(self.event)
            self.event = None
        return self.event is None

    def settle(self):
        if self.event is not None:
            check_cuda(self.cuda.cuEventSynchronize(self.event), "cuEventSynchronize")
            self.cuda.cuEventDestroy_v2(self.event)
            self.event = None


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


_MAX_BINS = MAX_BINS          # _gpuhost.MAX_BINS: one limit for every backend
# Sparse readback: peak records copied back with the count, before a second round trip.
_SPARSE_HOST = 4096
# The primary context this thread last made current (handles are stable: _DeviceShared retains
# each device's primary context for the process lifetime). cuCtxSetCurrent per call measured
# ~75 us of host time per fine-stage forward on the L40S.
_BOUND = threading.local()



#: Blocks per SM for the persistent tensor-core coarse gate: its block setup (DFT matrices)
#: amortises over the slots each warp loops through. Measured on the L40S at 131k pairs:
#: 4-8 best; 16 within 5%.
_TC_BLOCKS_PER_SM = 8

_PREFETCH = True
# CUDA graphs for the hierarchical launch sequences.
_GRAPHS = True

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


_shift = bin_shift


#: The per-row window table argument every fusedTierB and refineListedBounded launch ends with
#: (tierb.slang ROWWIN_PARAM): read only under a window start of ROWWIN_ON, so null otherwise.
_NOROW = ctypes.c_void_p(0)


def _u32(x):
    return ctypes.c_uint32(int(x) & 0xFFFFFFFF)


def _i32(x):
    return ctypes.c_int32(int(x))


def _f32bits(x):
    return ctypes.c_uint32(int(np.float32(x).view(np.uint32)))


def _ptr(v):
    return ctypes.c_uint64(int(v))


def _param_ptrs(params):
    """cuLaunchKernel's argument array: the address of each parameter (kept alive by the
    caller with params)."""
    return (ctypes.c_void_p * len(params))(*[ctypes.addressof(p) for p in params])


_PACK_U64 = struct.Struct("Q").pack_into
_WORDS = {}


def _pack_words(k):
    """pack_into for k uint32 words (an Arg(words=k)), made once per k."""
    f = _WORDS.get(k)
    if f is None:
        f = _WORDS[k] = struct.Struct("%dI" % k).pack_into
    return f


def _uint4(*v):
    """A Slang ``uniform uint4``: ONE 16-byte kernel parameter, not four u32s."""
    return (ctypes.c_uint32 * 4)(*(int(x) & 0xFFFFFFFF for x in v))


def _size_class(nbytes):
    """The allocation a request of nbytes takes from a pool (_Pool): 4 KiB, or nbytes rounded
    up to a quarter of its power of two (at most 25% more)."""
    if nbytes <= 4096:
        return 4096
    step = 1 << (int(nbytes).bit_length() - 3)
    return -(-int(nbytes) // step) * step


class _Pool:
    """Allocations of one kind (device or page-locked) freed while their context was idle,
    kept by size class for the next allocation on the device. cuMemFree and cuMemFreeHost
    synchronize the device: a dropped plan's context, freed between a search's calls, made
    ~300 of them, each a stall of every pipeline on the device (L40S: a fifth of the fine
    stage). Holds at most `cap` bytes; past that a free goes to the driver."""

    def __init__(self, cap):
        self.cap, self.held, self.free = cap, 0, {}

    def take(self, size):
        lst = self.free.get(size)
        if lst:
            self.held -= size
            return lst.pop()
        return None

    def give(self, size, ptr):
        if self.held + size > self.cap:
            return False
        self.free.setdefault(size, []).append(ptr)
        self.held += size
        return True


def _pools(ctx):
    holder = getattr(ctx, "_device_state", None) or ctx
    pools = holder.__dict__.get("pools")
    if pools is None:
        pools = holder.pools = (_Pool(1 << 30), _Pool(256 << 20))       # device, page-locked
    return pools


class _Buffer:
    """Device memory: cuMemAlloc'd, or reused from the device's pool (_Pool). Slotted, as
    are the other buffer kinds: a search holds thousands, which the garbage collector walks
    at every full collection."""
    __slots__ = ("ctx", "nbytes", "dptr", "_size", "ptr", "handle")

    def __init__(self, ctx, nbytes):
        self.ctx = ctx
        self.nbytes = int(nbytes)
        self.dptr = ctypes.c_uint64(0)
        self._size = 0
        if self.nbytes > 0:
            self._size = _size_class(self.nbytes)
            ptr = _pools(ctx)[0].take(self._size)
            if ptr is not None:
                self.dptr.value = ptr
            else:
                ctx._bind()
                check_cuda(
                    self.ctx.cuda.cuMemAlloc_v2(ctypes.byref(self.dptr), self._size),
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

    def destroy(self, idle=False):
        """Free it; idle: no work of its context runs (it goes back to the pool)."""
        if self.dptr.value:
            if not (idle and _pools(self.ctx)[0].give(self._size, self.dptr.value)):
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

    def __init__(self, ctx, nbytes, readback=False, host_input=False):
        self.ctx = ctx
        self.nbytes = max(int(nbytes), 4)
        self.dptr = ctypes.c_uint64(0)
        self.managed = hasattr(self.ctx.cuda, "cuMemAllocManaged")
        self.host_input = False
        ctx._bind()
        if self.managed:
            check_cuda(
                self.ctx.cuda.cuMemAllocManaged(ctypes.byref(self.dptr), self.nbytes, 1),
                "cuMemAllocManaged",
            )
            # host_input: an input the host rewrites every call and the device reads once
            # (a segment's series). Kept in host memory and mapped by the device: the host
            # writes it without faulting pages back from the device, no migration is issued
            # before the kernels, and the kernels read it over the bus once.
            if host_input and hasattr(self.ctx.cuda, "cuMemAdvise"):
                cu = self.ctx.cuda
                if (cu.cuMemAdvise(self.dptr.value, self.nbytes, _ADVISE_PREFERRED_LOCATION,
                                   _CPU_DEVICE) == 0
                        and cu.cuMemAdvise(self.dptr.value, self.nbytes, _ADVISE_ACCESSED_BY,
                                           self.ctx.device.value) == 0):
                    self.host_input = True
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
    __slots__ = ("ctx", "nbytes", "_size", "ptr", "handle", "_raw")

    def __init__(self, ctx, nbytes):
        self.ctx = ctx
        self.nbytes = max(int(nbytes), 16)
        self._size = _size_class(self.nbytes)
        ptr = _pools(ctx)[1].take(self._size)
        if ptr is None:
            p = ctypes.c_void_p()
            ctx._bind()
            check_cuda(ctx.cuda.cuMemAllocHost_v2(ctypes.byref(p), self._size), "cuMemAllocHost")
            ptr = p.value
        self.ptr = ptr
        self.handle = ptr
        self._raw = np.frombuffer((ctypes.c_ubyte * self.nbytes).from_address(self.ptr), np.uint8)

    def view(self, dtype, count, offset=0):
        size = np.dtype(dtype).itemsize
        return self._raw[offset:offset + count * size].view(dtype)

    def destroy(self, idle=False):
        """Free it; idle: no copy of its context reads or writes it (back to the pool)."""
        if self.ptr:
            if not (idle and _pools(self.ctx)[1].give(self._size, self.ptr)):
                self.ctx._bind()
                self.ctx.cuda.cuMemFreeHost(ctypes.c_void_p(self.ptr))
            self.ptr = 0
            self.handle = 0

    def __del__(self):
        try:
            self.destroy()
        except Exception:
            pass


class _GraphCache:
    """Instantiated CUDA graphs of one record, LRU-bounded; destroyed with the record."""
    nbytes = 0          # host-side handles: nothing for the cache budget

    def __init__(self, ctx, limit=8):
        self.ctx, self.limit, self.items, self.seen = ctx, limit, {}, {}

    def get(self, key):
        ex = self.items.pop(key, None)
        if ex is not None:
            self.items[key] = ex
        return ex

    def put(self, key, ex):
        self.items[key] = ex
        while len(self.items) > self.limit:
            old = self.items.pop(next(iter(self.items)))
            self.ctx.cuda.cuGraphExecDestroy(old)

    def destroy(self):
        for ex in self.items.values():
            if ex.value:
                self.ctx.cuda.cuGraphExecDestroy(ex)
        self.items.clear()


class _Staged:
    """A device buffer the host rewrites before every run (_x_alloc(upload=True)). The values
    go through page-locked staging in one asynchronous copy on the context's stream: a copy
    from managed memory costs ~144 us, and a kernel reading a host-written managed page
    faults it over (132 us a forward launch on the L40S, 15 us from device memory)."""
    __slots__ = ("ctx", "nbytes", "device", "pinned", "dptr")

    def __init__(self, ctx, nbytes):
        self.ctx, self.nbytes = ctx, max(int(nbytes), 4)
        self.device, self.pinned = _Buffer(ctx, self.nbytes), _Pinned(ctx, self.nbytes)
        self.dptr = self.device.dptr

    def write(self, array, stream=None):
        array = np.ascontiguousarray(array)
        count = min(self.nbytes, array.nbytes)
        if count:
            ctypes.memmove(self.pinned.ptr, array.ctypes.data, count)
            self.ctx._copy_h2d(self.dptr.value, self.pinned.ptr, count, stream, "upload")

    def destroy(self, idle=False):
        self.device.destroy(idle)
        self.pinned.destroy(idle)


class _Section:
    """Bytes [offset, offset + nbytes) of a device buffer (Context._x_section): its own
    device pointer; the host reads it through the base buffer's mirror."""
    __slots__ = ("base", "dptr", "nbytes", "ptr", "handle", "offset")

    def __init__(self, base, offset, nbytes):
        self.base, self.offset, self.nbytes = base, offset, nbytes
        self.dptr = ctypes.c_uint64(base.dptr.value + offset)
        self.ptr = self.handle = self.dptr.value

    def view(self, dtype, count):
        dtype = np.dtype(dtype)
        return self.base.view(np.uint8, self.offset + count * dtype.itemsize)[self.offset:].view(dtype)

    def write(self, array, stream=None):
        raise TypeError("a section is written through its base buffer")

    def destroy(self, idle=False):
        pass                                    # the base buffer owns the memory


class _WordSlots:
    """Page-locked slots for the words of list update ops (_CudaList.update), carved from
    shared 4 KiB chunks and reused by size. A page-locked allocation each cost a
    cuMemAllocHost and a pinned page per update."""
    CHUNK = 4096

    def __init__(self, ctx):
        self.ctx, self.chunks, self.free = ctx, [], {}
        self.at, self.end = 0, 0

    def take(self, nbytes):
        size = -(-max(int(nbytes), 16) // 16) * 16
        lst = self.free.get(size)
        if lst:
            return lst.pop(), size
        if self.at + size > self.end:
            chunk = _Pinned(self.ctx, max(self.CHUNK, size))
            self.chunks.append(chunk)
            self.at, self.end = chunk.ptr, chunk.ptr + chunk.nbytes
        ptr, self.at = self.at, self.at + size
        return ptr, size

    def give(self, ptr, size):
        self.free.setdefault(size, []).append(ptr)

    def destroy(self):
        for chunk in self.chunks:
            chunk.destroy(idle=True)          # after the context's work (Context.destroy)
        self.chunks, self.free = [], {}
        self.at = self.end = 0


class _Readback:
    """A device buffer the host reads (_x_alloc(readback=True)): a list's readback op copies
    a prefix of it into page-locked memory on the stream, so the host reads it after the
    run's one synchronization (a range past that prefix is copied when it is read)."""
    __slots__ = ("ctx", "nbytes", "device", "dptr", "pinned", "mirrored")

    def __init__(self, ctx, nbytes):
        self.ctx, self.nbytes = ctx, max(int(nbytes), 4)
        self.device = _Buffer(ctx, self.nbytes)
        self.dptr = self.device.dptr
        self.pinned, self.mirrored = None, 0

    def mirror(self, nbytes):
        nbytes = min(int(nbytes), self.nbytes)
        if self.pinned is None or self.pinned.nbytes < nbytes:
            if self.pinned is not None:
                self.pinned.destroy()
            self.pinned = _Pinned(self.ctx, nbytes)
        self.mirrored = nbytes
        return self.pinned

    def view(self, dtype, count):
        """The first count elements: the page-locked mirror in place where the run copied
        that far, else a copy."""
        dtype = np.dtype(dtype)
        if count * dtype.itemsize <= self.mirrored:
            return self.pinned.view(dtype, count)
        return self.read_into(np.empty(count, dtype))

    def read_into(self, out, offset=0):
        dst, count = out.ctypes.data, out.nbytes
        inside = max(0, min(count, self.mirrored - offset))
        if inside:
            ctypes.memmove(dst, self.pinned.ptr + offset, inside)
        if count > inside:
            self.ctx._bind()
            check_cuda(self.ctx.cuda.cuMemcpyDtoH_v2(dst + inside,
                                                     self.dptr.value + offset + inside,
                                                     count - inside), "cuMemcpyDtoH")
        return out

    def destroy(self, idle=False):
        self.device.destroy(idle)
        if self.pinned is not None:
            self.pinned.destroy(idle)
            self.pinned = None


class _CudaList:
    """A command list (_gpuexec's driver interface): launches, fills and copies in order on
    one stream, so a barrier is the stream's own ordering. Each launch's parameters are
    built when it is recorded; an Arg is a parameter whose value _x_run sets (cuLaunchKernel
    copies them at launch, so the next run may change it while this one is in flight).

    A kernel is (function, threads, leading buffers, trailing buffers): its first buffers,
    then its uniforms, then -- the per-row window table (tierb.slang ROWWIN_PARAM) -- the
    trailing ones, null where the caller binds none."""

    def __init__(self, ctx, label):
        self.ctx, self.label, self.ops, self.args = ctx, label, [], []

    def _launch_op(self, kernel, groups, buffers, words, offsets):
        """A launch, its parameters packed into one host block at their natural alignment:
        two Python objects a launch, not one per parameter (a record's ctypes objects are
        what the garbage collector walks: a search held ~100k of them, and collecting them
        cost the L40S more time than its kernels). An Arg's slots are patched per run."""
        fn, wg = kernel[0], kernel[1]
        lead = kernel[2] if len(kernel) > 2 else len(buffers)
        trail = kernel[3] if len(kernel) > 3 else 0
        offs = offsets or [0] * len(buffers)
        fields = []                # (struct format, values, Arg slot or None, parameters)

        def pointer(b, o):
            if isinstance(b, Arg):
                fields.append(("Q", (0,), (b.name, int(o)), 1))
            else:
                fields.append(("Q", (int(b.dptr.value) + int(o),), None, 1))
        for b, o in zip(buffers[:lead], offs[:lead]):
            pointer(b, o)
        for w in words:
            if isinstance(w, Arg):         # k uniform words bound per run, one parameter each,
                fields.append(("%dI" % w.words, (0,) * w.words, (w.name, -w.words), w.words))
            elif isinstance(w, tuple):     # a vector uniform (uint4) is ONE parameter
                fields.append(("4I", tuple(int(x) & 0xFFFFFFFF for x in w)
                               + (0,) * (4 - len(w)), None, 1))
            else:
                fields.append(("I", (int(w) & 0xFFFFFFFF,), None, 1))
        rest = list(zip(buffers[lead:], offs[lead:]))
        for b, o in rest:
            pointer(b, o)
        fields += [("Q", (0,), None, 1)] * max(0, trail - len(rest))   # no row-window table
        places, params, end = [], [], 0
        for fmt, _, _, count in fields:
            size = struct.calcsize(fmt)
            align = min(size // count, 16)
            end = -(-end // align) * align
            places.append(end)
            params += [end + i * (size // count) for i in range(count)]
            end += size
        block = (ctypes.c_char * max(end, 8))()
        base = ctypes.addressof(block)
        for (fmt, values, slot, _), at in zip(fields, places):
            struct.pack_into(fmt, block, at, *values)
            if slot is not None:            # (block, offset, name, byte offset or -words)
                self.args.append((block, at, slot[0], slot[1]))
        ptrs = (ctypes.c_void_p * len(params))(*[base + at for at in params])
        return ("launch", fn, wg, int(groups), block, ptrs)

    def dispatch(self, kernel, groups, buffers, words=(), offsets=None):
        self.ops.append(self._launch_op(kernel, groups, buffers, words, offsets))

    def listed(self, kernel, count, max_groups, buffers, words=(), offsets=None):
        # No indirect dispatch: a resident grid strides over the list (its gridSize word).
        grid = self.ctx._refine_grid(kernel[0], kernel[1], int(max_groups))
        self.ops.append(self._launch_op(kernel, grid, buffers, list(words) + [grid], offsets))

    def barrier(self):
        pass

    def stamp(self, name):
        pass

    def fill(self, buf, word, offset=0, nbytes=None, rows=1, pitch=0):
        self.ops.append(("fill", buf, int(word) & 0xFFFFFFFF, offset,
                         buf.nbytes - offset if nbytes is None else nbytes, rows, pitch))

    def update(self, buf, words):
        ptr, size = self.ctx._word_slots().take(4 * len(words))
        vals = (ctypes.c_uint32 * len(words))(*[int(w) & 0xFFFFFFFF for w in words])
        ctypes.memmove(ptr, vals, 4 * len(words))
        self.ops.append(("update", buf, ptr, 4 * len(words), size))

    def readback(self, buf, nbytes):
        self.ops.append(("readback", buf, buf.mirror(nbytes)))

    def end(self):
        return _CudaNative(self.label, self.ops, self.args, self.ctx.__dict__.get("_slots"))


class _CudaNative:
    """A recorded list: its launches, and the per-run parameters (Arg) they read; replayed as
    a CUDA graph per binding (Context._x_launch). Owns its updates' word slots (_WordSlots)."""
    __slots__ = ("label", "ops", "args", "graphs", "slots")

    def __init__(self, label, ops, args, slots=None):
        self.label, self.ops, self.args, self.graphs, self.slots = label, ops, args, None, slots

    def destroy(self):
        if self.graphs is not None:
            self.graphs.destroy()
            self.graphs = None
        for op in self.ops:
            if op[0] == "update":
                self.slots.give(op[2], op[4])


class Context(Executor, InputUploads):
    """One NVIDIA CUDA device context, stream, and loaded PTX pipelines."""

    max_grouped_bins = _MAX_BINS
    cache_limit_bytes = 1024 * 1024 * 1024
    _profile = False                # MF_GPU_PROFILE (with MF_GPU_TIMING): per-kernel times
    _in_run = None                  # inside a timed run: its kernels' and copies' regions
    # Unified addressing: a view inside a shared allocation is a device pointer.
    shared_views = True
    # Device memory is separate from host memory (residency matters for pricing).
    discrete = True

    @property
    def timing(self):
        """Device timers on. ``_timing`` is the attribute shared with the Vulkan backend:
        gatechain.calibrate_costs_gpu switches it on around its measurement runs."""
        return self._timing

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
        _BOUND.ctx = self.ctx.value if self._using_primary_ctx else None
        for _ in range(4):
            s = ctypes.c_void_p()
            check_cuda(self.cuda.cuStreamCreate(ctypes.byref(s), 1), "cuStreamCreate")
            self.streams.append(s)
        self.stream = self.streams[0]

        # The shared timing contract (_gputime): register, keep (label, device_ms).
        self._timing = _gputime.enabled()
        # MF_GPU_PROFILE=1 as well: each kernel and copy of a run is also logged, as
        # ("k:<name>", device_ms).
        self._profile = self._timing and _config.get("MF_GPU_PROFILE")
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
        # _shared._same_device: Contexts with one _device_state exchange buffers freely.
        self._device_state = shared
        if shared is not None:
            self._modules, self._pipelines = shared.modules, shared.pipelines
            self._occupancy, self._labels = shared.occupancy, shared.labels
            self._c16_flags = shared.c16_flags
            self._tc_persistent = shared.tc_persistent
            self._shared_modules = True
        else:
            self._modules, self._pipelines, self._occupancy, self._labels = {}, {}, {}, {}
            self._c16_flags = {}
            self._tc_persistent = {}
            self._shared_modules = False
        self._uploaded = {"data": {}, "tmpl": {}}

    # ---- device plumbing -----------------------------------------------------
    def _attr(self, attr):
        v = ctypes.c_int(0)
        self.cuda.cuDeviceGetAttribute(ctypes.byref(v), attr, self.device.value)
        return v.value

    def clock_mhz(self):
        """The device's current SM clock in MHz (NVML), or None where it cannot be read.

        gatechain._ClockRef scales calibration timings by it: on the L40S the clock holds at
        2520 MHz under load, and the timed reference call it otherwise uses (~60 us) varied
        1.4-2x after a host pause, which spread the calibrated costs by +-30%."""
        reader = self.__dict__.get("_clock_reader", False)
        if reader is False:
            reader = None
            try:
                buf = ctypes.create_string_buffer(32)
                if self.cuda.cuDeviceGetPCIBusId(buf, len(buf), self.device.value) == 0:
                    reader = _cuda.nvml_sm_clock(buf.value)
            except (AttributeError, OSError):
                reader = None
            self._clock_reader = reader
        return reader() if reader is not None else None

    def _bind(self):
        ctx = getattr(self, "ctx", None)
        if ctx and ctx.value:
            if self._using_primary_ctx and getattr(_BOUND, "ctx", None) == ctx.value:
                return
            check_cuda(self.cuda.cuCtxSetCurrent(ctx), "cuCtxSetCurrent")
            _BOUND.ctx = ctx.value if self._using_primary_ctx else None

    def get_stream(self, slot=None):
        # Integer slots spread over the streams; any other slot (e.g. a follow-up items
        # allocation) runs on the default stream, ordered with peaks_items.
        if isinstance(slot, int) and self.streams:
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
        if self._in_run is not None:             # a kernel or copy of a timed run
            self._in_run.append((label, token, e1))
            return
        self._pending_events.setdefault(stream.value, []).append((label, token, e1))

    def _sync(self, stream=None):
        """Wait for ``stream``; resolve its timed regions into timing_log."""
        st = self.get_stream(None) if stream is None else stream
        check_cuda(self.cuda.cuStreamSynchronize(st), "cuStreamSynchronize")
        self._resolve(st.value)

    def _resolve(self, key):
        pending = self._pending_events.pop(key, None)
        if pending:
            total = 0.0
            ms = ctypes.c_float(0.0)
            for label, e0, e1 in pending:
                # A run is the sum of its kernels' and copies' regions: the device's busy
                # time. Issued launch by launch from Python, its first-to-last interval also
                # held the host's gaps between launches -- the GPU cost calibration then
                # priced the L40S's blocks 25% low and chose a slower search (4-11% leaf).
                regions = e1 if e0 is None else [(label, e0, e1)]
                run = 0.0
                for name, r0, r1 in regions:
                    check_cuda(self.cuda.cuEventSynchronize(r1), "cuEventSynchronize")
                    check_cuda(self.cuda.cuEventElapsedTime(ctypes.byref(ms), r0, r1),
                               "cuEventElapsedTime")
                    if e0 is None and self._profile:
                        self.timing_log.append(("k:" + name, float(ms.value)))
                    run += float(ms.value)
                    self._event_pool.extend((r0, r1))
                self.timing_log.append((label, run))
                total += run
            self.last_gpu_time = total * 1e-3

    def _x_timings(self):
        if self._pending_events:
            self._bind()
            for key in list(self._pending_events):
                self._resolve(key)

    def _copy_h2d(self, dst, src, nbytes, stream, label):
        st = self.get_stream(None) if stream is None else stream
        tok = self._mark(st)
        check_cuda(self.cuda.cuMemcpyHtoDAsync_v2(dst, src, nbytes, st), "cuMemcpyHtoDAsync")
        self._close(tok, st, label)

    def _copy_d2h(self, dst, src, nbytes, stream, label):
        st = self.get_stream(None) if stream is None else stream
        tok = self._mark(st)
        check_cuda(self.cuda.cuMemcpyDtoHAsync_v2(dst, src, nbytes, st), "cuMemcpyDtoHAsync")
        self._close(tok, st, label)

    def _fill32(self, dptr, value, count, stream):
        if count > 0:
            check_cuda(self.cuda.cuMemsetD32Async(dptr, value, count, stream), "cuMemsetD32Async")

    def _prefetch(self, buf, offset, nbytes, stream):
        """Migrate a managed span to this device ahead of the kernel that reads it.

        Host-written managed pages would otherwise be faulted in page by page by the
        kernel itself; already-resident pages make this nearly free."""
        if (_PREFETCH and isinstance(buf, _Borrowed) and getattr(buf.owner.buffer, "managed", False)
                and not getattr(buf.owner.buffer, "host_input", False) and nbytes > 0 and hasattr(self.cuda, "cuMemPrefetchAsync")):
            self.cuda.cuMemPrefetchAsync(buf.dptr.value + offset, nbytes, self.device.value, stream)

    # ---- kernels -------------------------------------------------------------
    def _stem(self, n, entry, one_bin=False, c16=False, ppg=1, tile=1, twt=False):
        if entry == "packCoarse":
            return "pack_coarse"
        if entry == "compactPairs":
            return "compact"
        if entry == "compactListed":
            return "compactl"
        if entry == "markBlocks":
            return "markblocks"
        if entry in ("seriesForwardBands", "seriesForwardListed", "forwardTier0"):
            return {"seriesForwardBands": "forward_bands", "seriesForwardListed": "forward_listed",
                    "forwardTier0": "forward_tier0"}[entry] + f"_{n}"
        if entry == "seriesForward":
            return f"forward_{n}"
        if entry == "refineItems":
            return f"items_{n}"
        if entry == "coarseTile":
            return f"coarse_{n}"
        if c16:
            p_s = f"p{ppg}" if ppg > 1 else ""
            t_s = f"t{tile}" if tile > 1 else ""
            return f"tierb_{n}_c16{p_s}{t_s}{'w' if twt else ''}"
        if entry == "refineListed":
            one = f"refine_{n}_onebin"
            return one if (one_bin and (_PTX_DIR / f"{one}.ptx").is_file()) else f"refine_{n}"
        if entry == "fullCorrelation":
            return f"full_{n}"
        if entry == "fullCorrelationSeries":
            return f"full_series_{n}"
        if one_bin and n >= 4096:
            return f"tierb_{n}_onebin"
        return f"tierb_{n}"

    def pipeline(self, n, entry="fusedTierB", one_bin=False, c16=False, ppg=1, tile=1, twt=False,
                 gate=False):
        """Retrieve or load the compiled PTX kernel function: (function, threads per block).
        twt: the coarse build with the fp16 twiddle table (tools/build_ptx.py)."""
        key = (n, entry, one_bin, c16, ppg, tile, twt, gate)
        if key in self._pipelines:
            return self._pipelines[key]

        r = _radix(n)
        wg = (n // r) * ppg if entry in ("fusedTierB", "refineListed") else (
            256 if entry in ("compactPairs", "compactListed", "markBlocks", "packCoarse") else (
                64 if entry == "coarseTile" else (n // r)
            )
        )

        stem = self._stem(n, entry, one_bin=one_bin, c16=c16, ppg=ppg, tile=tile, twt=twt)
        if gate:                                 # the one-bin build's gate-only variant
            stem += "_gate"
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
        mkey = stem
        if mkey not in self._modules:
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
            self._modules[mkey] = mod
            g, size = ctypes.c_uint64(), ctypes.c_size_t()
            if self.cuda.cuModuleGetGlobal_v2(ctypes.byref(g), ctypes.byref(size), mod,
                                              b"mf_c16_raw") == 0:
                self._c16_flags[mkey] = [g.value, 0]          # zero-initialized: bound on
        hfunc = ctypes.c_void_p()
        check_cuda(
            self.cuda.cuModuleGetFunction(ctypes.byref(hfunc), self._modules[mkey],
                                          fn_name.encode("utf-8")),
            f"cuModuleGetFunction({fn_name})",
        )
        self._labels[hfunc.value] = stem          # its module, for every Context on the device
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

    def _launch(self, hfunc, grid_dim, block_dim, params, shared_mem=0, stream=None, label=None,
                param_ptrs=None):
        """Launch hfunc; param_ptrs, when given, is _param_ptrs(params) built beforehand."""
        if (grid_dim if not isinstance(grid_dim, tuple) else grid_dim[0]) <= 0:
            return
        if param_ptrs is None:
            param_ptrs = _param_ptrs(params)
        gx, gy, gz = grid_dim if isinstance(grid_dim, tuple) else (grid_dim, 1, 1)
        bx, by, bz = block_dim if isinstance(block_dim, tuple) else (block_dim, 1, 1)
        st = self.get_stream(None) if stream is None else stream
        tok = self._mark(st)
        check_cuda(
            self.cuda.cuLaunchKernel(hfunc, gx, gy, gz, bx, by, bz, shared_mem, st,
                                     param_ptrs, None),
            "cuLaunchKernel",
        )
        if tok is not None:
            self._close(tok, st, label or self._labels.get(hfunc.value, "kernel"))

    def empty_shared(self, shape, dtype=np.complex64, *, readback=False, host_input=False):
        def factory(ctx, size):
            return _HostBuffer(ctx, size, readback=readback, host_input=host_input)
        return empty_shared(self, factory, shape, dtype)

    def _compact_peaks(self):
        key = ("compactPeaks",)
        if key not in self._pipelines:
            f = _PTX_DIR / "compact_peaks.ptx"
            if not f.is_file():
                raise UnsupportedSize("compact_peaks.ptx not built")
            self._pipelines[key] = (self._load("compact_peaks", f, "compactPeaks", 256), 256)
        return self._pipelines[key]

    # ---- flat ------------------------------------------------------------------

    # ---- full correlation --------------------------------------------------------
    # ---- driver primitives (_gpuexec) -----------------------------------------------------
    #: The most blocks one launch takes (gridDim.x), and the byte alignment of a bound view:
    #: a device pointer plus offset, aligned for the widest element a kernel reads (float2).
    max_dispatch_x = 2 ** 31 - 1
    max_binding_bytes = None        # no per-binding limit below the allocation
    storage_offset_alignment = 16
    #: Shared allocations are managed memory, which migrates between host and device.
    stage_host_inputs = True
    #: Kernels are prebuilt PTX with their row length fixed: a stride read from a module
    #: constant made the refine and tier kernels 12-39% slower on an L40S (twiddle.slang), so
    #: the tiers read packed bands (_gpuhier "pack" feed) rather than the spectra in place.
    inplace_feed = False
    #: Whose kernel identity stored measured choices are tied to (gatechain.gpu_kernel_id).
    kernel_family = "cuda"
    #: The warp.
    subgroup_size = 32

    def _x_kernel(self, name, n, consts=None):
        c = consts or {}
        if c.get("stride"):
            raise UnsupportedSize("CUDA kernels read their own row length (inplace_feed)")
        if name in ("peaks", "peaks1", "gate"):
            fn, wg = self.pipeline(n, "fusedTierB", one_bin=(name == "peaks1"))
            return fn, wg, 4, 1
        if name == "coarse":
            if len(c.get("layout", ())) > 4:                 # the tensor-core gate
                fn, wg = self._tc_kernel(n, c["ppg"])
            else:
                fn, wg = self.pipeline(n, "fusedTierB", c16=True, ppg=c["ppg"], tile=c["tile"],
                                       twt=bool(c.get("twt")))
            self._c16_bound_flag(fn)
            return fn, wg, 4, 1
        if name in ("tier", "tier1", "refine", "refine1"):
            fn, wg = self.pipeline(n, "refineListed", one_bin=name.endswith("1"),
                                   gate=bool(c.get("gate")))
            return fn, wg, 6, 1
        if name == "compact_peaks":
            return self._compact_peaks()
        entries = {"compact": "compactPairs", "compactl": "compactListed", "mark": "markBlocks",
                   "pack": "packCoarse", "fwd_tier0": "forwardTier0",
                   "fwd_bands": "seriesForwardBands", "fwd_listed": "seriesForwardListed",
                   "full": "fullCorrelation", "series": "fullCorrelationSeries",
                   "forward": "seriesForward", "items": "refineItems"}
        if name in entries:
            return self.pipeline(n, entries[name])
        role = {"tc1": "corr1", "tc2": "corr2", "tcs2": "corr_series2",
                "tf1": "fwd1", "tf2": "fwd2"}[name]
        fn, wg, _, _ = self._tierc(n, role)
        return fn, wg

    def _tc_kernel(self, band, wpb):
        """The tensor-core coarse gate (src/gpu/coarse_tc.cu): one warp per 2-template ragged
        slot, wpb warps per block, persistent (its grid capped, _x_coarse_groups)."""
        f = _PTX_DIR / ("coarse_tc_%d_w%d.ptx" % (band, wpb))
        fn = self._load(f.stem, f, "fusedTierB", 32 * wpb)
        self._tc_persistent[fn.value] = self.sm_count * _TC_BLOCKS_PER_SM
        return fn, 32 * wpb

    def _x_coarse_groups(self, kernel, groups):
        """A persistent kernel's grid is capped: its warps loop over slots."""
        cap = self._tc_persistent.get(kernel[0].value)
        return min(groups, cap) if cap else groups

    @staticmethod
    def _x_has_c16(band):
        return (_PTX_DIR / f"tierb_{band}_c16.ptx").is_file()

    @staticmethod
    def _x_has_kernel(name, n):
        if name == "tier1":
            return (_PTX_DIR / f"refine_{n}_onebin.ptx").is_file()
        if name == "fwd_tier0":
            return (_PTX_DIR / f"forward_tier0_{n}.ptx").is_file()
        if name == "items":
            return (_PTX_DIR / f"items_{n}.ptx").is_file()
        if name == "tier1gate":
            return (_PTX_DIR / f"refine_{n}_onebin_gate.ptx").is_file()
        raise ValueError(name)

    def _x_coarse_candidates(self, band):
        """Every coarse layout (subgroup 0: the warp, ppg, tile, twt) shipped at this band --
        a missing build is skipped -- then the tensor-core gate, a fifth field marking it
        ("tc"), on devices with tensor cores (compute capability 8.0 or later)."""
        cands = []
        for tile in (1,) + TILE_PROBE:
            for ppg in (1, 2, 4, 8, 16):
                if ppg > 1 and band // 16 * ppg > 1024:
                    continue
                for twt in (0, 1):
                    if (_PTX_DIR / (self._stem(band, "fusedTierB", c16=True, ppg=ppg, tile=tile,
                                               twt=bool(twt)) + ".ptx")).is_file():
                        cands.append((0, ppg, tile, twt))
        for wpb in (2, 4):
            if (_PTX_DIR / ("coarse_tc_%d_w%d.ptx" % (band, wpb))).is_file() and self.cc >= (8, 0):
                cands.append((0, wpb, 2, 0, "tc"))
        return cands

    def _x_time(self, native, binds, reps):
        """The least device time of `reps` runs (stream events), after one warm-up run."""
        self._bind()
        stream = self.get_stream(None)
        e0, e1 = self._new_event_timed(), self._new_event_timed()
        times = []
        try:
            for rep in range(reps + 1):
                check_cuda(self.cuda.cuEventRecord(e0, stream), "cuEventRecord")
                self._enqueue(native, binds, stream, graph=False)
                check_cuda(self.cuda.cuEventRecord(e1, stream), "cuEventRecord")
                self._sync(stream)
                ms = ctypes.c_float()
                check_cuda(self.cuda.cuEventElapsedTime(ctypes.byref(ms), e0, e1),
                           "cuEventElapsedTime")
                if rep:
                    times.append(ms.value * 1e-3)
        finally:
            self.cuda.cuEventDestroy_v2(e0)
            self.cuda.cuEventDestroy_v2(e1)
        return min(times)

    def _x_tierc(self, n):
        return self._tierc(n, "corr1")[2:]

    def _x_alloc(self, nbytes, readback=False, upload=False):
        if upload:
            return _Staged(self, nbytes)
        return _Readback(self, nbytes) if readback else _Buffer(self, nbytes)

    def _x_list(self, label, once=False):
        return _CudaList(self, label)

    def _x_run(self, native, wait, binds=None, slot=None, pre=()):
        stream = self._x_launch(native, binds, slot, pre)
        if wait:
            self._sync(stream)
        else:
            self._pend_write(stream)

    def _x_submit(self, native, binds, slot, pre=()):
        stream = self._x_launch(native, binds, slot, pre)
        return lambda: self._sync(stream)

    def _x_launch(self, native, binds, slot, pre=()):
        """Issue the deferred work, then a recorded list, on the slot's stream, after writes
        left in flight (a series a middle stage is still writing)."""
        self._bind()
        stream = self.get_stream(slot)
        self._after_writes(stream)
        regions = [] if self._timing else None  # its kernels' and copies' timed regions
        self._in_run = regions
        try:
            for nat, b in pre:
                self._enqueue(nat, b, stream)
            self._enqueue(native, binds, stream)
        finally:
            self._in_run = None
        if regions:
            self._pending_events.setdefault(stream.value, []).append(
                (native.label, None, regions))
        return stream

    def _enqueue(self, native, binds, stream, graph=True):
        """A recorded list's operations on `stream`: replayed as a CUDA graph per binding once
        a binding recurs (a hierarchical call is ~20 launches, fills and copies, ~200 us of
        host time issued one by one through ctypes, one call as a graph); issued directly
        with device timers on (MF_GPU_TIMING needs per-kernel events), on a binding's first
        use, or where capture failed once."""
        values = []
        for block, at, name, off in native.args:
            if off < 0:                         # the -off words of a per-run word Arg
                v = binds[name]
                _pack_words(-off)(block, at, *v)
            else:                               # a buffer bound per run, at a byte offset
                v = binds[name].dptr.value + off
                _PACK_U64(block, at, v)
            values.append(v)
        if not graph or self._timing or not _GRAPHS or len(native.ops) < 4:
            self._issue(native.ops, stream)
            return
        if native.graphs is None:
            native.graphs = _GraphCache(self)
        graphs = native.graphs
        gkey = (tuple(values), stream.value)
        ex = graphs.get(gkey)
        if ex is None:
            seen = graphs.seen.get(gkey, 0)
            graphs.seen[gkey] = seen + 1
            if seen != 1:                       # first use, or a capture that failed: direct
                self._issue(native.ops, stream)
                return
            cu = self.cuda
            check_cuda(cu.cuStreamBeginCapture_v2(stream, 2), "cuStreamBeginCapture")  # relaxed
            graph = ctypes.c_void_p()
            failed = False
            try:
                self._issue(native.ops, stream)
            except _cuda.CudaError:
                failed = True                   # e.g. an operation that cannot be captured
            finally:
                rc = cu.cuStreamEndCapture(stream, ctypes.byref(graph))
            if rc != 0 or failed:
                if graph.value:
                    cu.cuGraphDestroy(graph)
                self._issue(native.ops, stream)  # the capture recorded only: run directly
                return
            ex = ctypes.c_void_p()
            check_cuda(cu.cuGraphInstantiateWithFlags(ctypes.byref(ex), graph, 0),
                       "cuGraphInstantiateWithFlags")
            cu.cuGraphDestroy(graph)
            graphs.put(gkey, ex)
            self._x_built = self.__dict__.get("_x_built", 0) + 1      # Executor.built
        check_cuda(self.cuda.cuGraphLaunch(ex, stream), "cuGraphLaunch")

    def _issue(self, ops, stream):
        for op in ops:
            kind = op[0]
            if kind == "launch":
                _, fn, wg, groups, params, param_ptrs = op
                self._launch(fn, groups, wg, params, stream=stream, param_ptrs=param_ptrs)
            elif kind == "fill":
                _, buf, word, offset, nbytes, rows, pitch = op
                dptr = buf.dptr.value + offset
                if rows == 1:
                    self._fill32(dptr, word, nbytes // 4, stream)
                else:
                    check_cuda(self.cuda.cuMemsetD2D32Async(dptr, pitch, word, nbytes // 4, rows,
                                                            stream), "cuMemsetD2D32Async")
            elif kind == "update":
                self._copy_h2d(op[1].dptr.value, op[2], op[3], stream, "upload")
            else:
                buf, pin = op[1], op[2]
                self._copy_d2h(pin.ptr, buf.dptr.value, buf.mirrored, stream, "readback")

    def _x_upload(self, buf, array, slot):
        buf.write(array, self.get_stream(slot))

    def _x_prefetch(self, view, offset, nbytes, slot):
        self._prefetch(view, offset, nbytes, self.get_stream(slot))

    def _x_after_readers(self):
        # Streams of different Contexts share no order: readers of an output this run
        # rewrites (last segment's fine stage) may still be running on theirs.
        self._bind()
        check_cuda(self.cuda.cuCtxSynchronize(), "cuCtxSynchronize")

    def _x_release(self, native, done=False):
        if not done:
            self._x_idle()
        native.destroy()

    @staticmethod
    def _x_free(buf):
        buf.destroy(idle=True)

    @staticmethod
    def _x_section(buf, offset, nbytes):
        return _Section(buf, offset, nbytes)

    def _x_idle(self):
        # This context's streams only: cuCtxSynchronize waits for every Context on the shared
        # primary context, and a per-record wait of that kind drained their pipelines.
        self._bind()
        for s in self.streams:
            if s.value:
                check_cuda(self.cuda.cuStreamSynchronize(s), "cuStreamSynchronize")

    @staticmethod
    def _x_read(buf, out, offset=0):
        buf.read_into(out, offset)

    @staticmethod
    def _x_view(buf, dtype, count):
        return buf.view(dtype, count)

    def _pend_write(self, stream):
        e = self._new_event()
        check_cuda(self.cuda.cuEventRecord(e, stream), "cuEventRecord")
        self._writes().append(_Write(self.cuda, e))

    def _after_writes(self, stream):
        """Order ``stream`` after writes left in flight (dropping those already complete)."""
        pend = self._writes()
        if not pend:
            return
        pend[:] = [w for w in pend if not w.done()]
        for w in pend:
            check_cuda(self.cuda.cuStreamWaitEvent(stream, w.event, 0), "cuStreamWaitEvent")


    # ---- hierarchical ---------------------------------------------------------------

    def _c16_bound_flag(self, fn):
        """Set the coarse module's fp16 bound switch (mf_c16_raw, Vulkan's constant 77):
        the bound applies unless MF_VK_C16_BOUND=0 asks for the raw fp16 maximum, which
        only the bound's own margin measurements and the physics checks use."""
        ent = self._c16_flags.get(self._labels.get(fn.value))
        if ent is None:
            return
        raw = 0 if _config.get("MF_VK_C16_BOUND") else 1
        if ent[1] != raw:
            self._bind()
            check_cuda(self.cuda.cuCtxSynchronize(), "cuCtxSynchronize")
            v = ctypes.c_uint32(raw)
            check_cuda(self.cuda.cuMemcpyHtoD_v2(ent[0], ctypes.byref(v), 4), "cuMemcpyHtoD")
            ent[1] = raw

    def _new_event_timed(self):
        e = ctypes.c_void_p()
        check_cuda(self.cuda.cuEventCreate(ctypes.byref(e), 0), "cuEventCreate")
        return e

    def _refine_grid(self, fn, wg, pairs):
        return max(1, min(pairs, self._blocks_per_sm(fn, wg) * self.sm_count))

    # ---- lifetime ----------------------------------------------------------------
    def clear_cache(self):
        self._drain()
        self._exec_clear()
        self._bind()
        if self.ctx.value:
            self.cuda.cuCtxSynchronize()
        self._uploaded = {"data": {}, "tmpl": {}}
        self._cache_order = {}

    def _x_peaks(self, out):
        """Theoretical peaks (_roofline.gpu_peaks): driver attributes plus a stated formula."""
        from . import _roofline as _rl
        a = self._attr
        sms, khz = a(16), a(13)              # MULTIPROCESSOR_COUNT, CLOCK_RATE (kHz)
        mem_khz, bus = a(36), a(37)          # MEMORY_CLOCK_RATE (kHz), GLOBAL_MEMORY_BUS_WIDTH
        cc = (a(75), a(76))
        # FP32 lanes per SM by compute capability (CUDA C Programming Guide, arithmetic
        # instruction throughput); vector fp16 runs at the fp32 rate from 8.6 on.
        fp32 = {(7, 0): 64, (7, 5): 64, (8, 0): 64, (8, 6): 128, (8, 7): 128, (8, 9): 128,
                (9, 0): 128}.get(cc, 128)
        fp16 = {(7, 0): 128, (7, 5): 128, (8, 0): 256}.get(cc, fp32)
        ghz = khz / 1e6
        out.update(sms=sms, cc=cc, clock_ghz=ghz,
                   flops=dict(fp32=sms * fp32 * 2 * ghz * 1e9, fp16=sms * fp16 * 2 * ghz * 1e9,
                              int16=sms * fp32 * 2 * ghz * 1e9),
                   bandwidth=2 * mem_khz * 1e3 * bus / 8,
                   formula="%d SMs x %d fp32 lanes (fp16 %d) x 2 x %.3f GHz boost; int16 at the "
                           "fp32 rate; tensor cores not counted" % (sms, fp32, fp16, ghz),
                   bandwidth_formula="2 x %.0f MHz memory clock x %d-bit bus / 8" % (mem_khz / 1e3, bus))
        out["measured"] = _rl._MEASURED.get("L40S") if "L40S" in (out["name"] or "") else None
        return out

    def _word_slots(self):
        slots = self.__dict__.get("_slots")
        if slots is None:
            slots = self._slots = _WordSlots(self)
        return slots

    def destroy(self):
        if not getattr(self, "ctx", None) or not self.ctx.value:
            return
        self._retire()
        self._bind()
        self.clear_cache()
        if self.__dict__.get("_slots") is not None:
            self._slots.destroy()
            self._slots = None
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
        _BOUND.ctx = None
        self.ctx.value = 0

    def __del__(self):
        try:
            self.destroy()
        except Exception:
            pass
