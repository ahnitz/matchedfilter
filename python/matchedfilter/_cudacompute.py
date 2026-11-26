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
import gzip
import re
import struct
import threading
import weakref

import numpy as np

from . import _config, _cuda, _gputime, _kernels
from ._cuda import check_cuda
from ._errors import UnsupportedSize
from ._gpu_cache import InputUploads
from ._gpuhost import CommandList
from ._gpuexec import Arg, Executor, settle as _settle
from ._shared import empty_shared, _Borrowed, _Storage
from ._gpuhost import DeviceProps, Section, carray, hier_peaks_grouped
from . import _peaks as _pk
from ._coarse import candidates
from ._kernels import KernelRoles


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

    def __init__(self, cuda, device, ctx=None):
        """The state of `device`'s primary context, retained for the process lifetime; or,
        given `ctx` (a context of its own, where the driver has no primary context), the
        state of that one context alone."""
        self.cuda = cuda
        if ctx is None:
            self.ctx = ctypes.c_void_p()
            check_cuda(cuda.cuDevicePrimaryCtxRetain(ctypes.byref(self.ctx), device),
                       "cuDevicePrimaryCtxRetain")       # held for the process lifetime
        else:
            self.ctx = ctx
        self.modules = {}
        self.pipelines = {}
        # Events after writes left in flight (correlate_series(wait=False)): every Context's
        # streams order their work after them; settle_writes() waits on them for the host.
        self.pending_writes = []
        self.occupancy = {}
        self.labels = {}

    @property
    def _device_state(self):
        """Itself: what a context's _device_state is, so _pools and _shared._same_device
        treat a buffer released through the device like one held by a live context."""
        return self

    @property
    def open(self):
        """Whether the context this state belongs to is still open (the primary context is
        retained for the process; a context of its own is open until destroyed), so a buffer
        made on it can be freed. Not the device's index, which is 0 on the first device."""
        return bool(self.ctx.value)

    def _bind(self):
        """Make the device's primary context current (a buffer freed after its context)."""
        if getattr(_BOUND, "ctx", None) != self.ctx.value:
            check_cuda(self.cuda.cuCtxSetCurrent(self.ctx), "cuCtxSetCurrent")
            _BOUND.ctx = self.ctx.value


class _Owned:
    """A buffer's link to its context: weakly to the context (its streams, timers and the
    function table a test may wrap) and strongly to the device state it frees through (the
    primary context, or the one context of a driver without one; the function table and the
    pools). A context holds its buffers through its records, so a buffer that held the
    context made every context a reference cycle, freed only by a full collection -- with its
    recordings and device memory -- however long after the plan was dropped."""
    __slots__ = ()

    def _own(self, ctx):
        self._dev = ctx._device_state
        self._ctx = weakref.ref(ctx)

    @property
    def ctx(self):
        """The live context, else the device state it was made on."""
        c = self._ctx()
        return c if c is not None else self._dev


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


_PTX_DIR = _kernels.folder("cuda")

_CUDA_ERROR_UNSUPPORTED_PTX_VERSION = 222
_PTX_VERSION = re.compile(rb"^\.version (\d+)\.(\d+)$", re.M)


def _ptx_for_driver(ptx, cuda):
    """A PTX module's text declared as the newest PTX version the driver reads.

    From CUDA 11 on, a driver of release M.m reads PTX up to version (M - 4).m, in some
    releases one minor version less (12.8 reads 8.7); the lower of the two is declared.

    Parameters
    ----------
    ptx : bytes
        The module's text.
    cuda : ctypes.CDLL
        The bound CUDA driver library.

    Returns
    -------
    bytes or None
        The text with its ``.version`` line lowered, or None where the driver's version is
        unknown or already reads the module's.
    """
    version = ctypes.c_int()
    if cuda.cuDriverGetVersion(ctypes.byref(version)) != 0 or version.value < 11000:
        return None
    reads = (version.value // 1000 - 4, max(version.value % 1000 // 10 - 1, 0))
    found = _PTX_VERSION.search(ptx)
    if found is None or (int(found.group(1)), int(found.group(2))) <= reads:
        return None
    return ptx[:found.start()] + b".version %d.%d" % reads + ptx[found.end():]


# The primary context this thread last made current (handles are stable: _DeviceShared retains
# each device's primary context for the process lifetime). cuCtxSetCurrent per call measured
# ~75 us of host time per fine-stage forward on the L40S.
_BOUND = threading.local()


_PREFETCH = True
# CUDA graphs for the hierarchical launch sequences.
_GRAPHS = True

# cuMemAdvise enums
_ADVISE_PREFERRED_LOCATION = 3
_ADVISE_ACCESSED_BY = 5
_CPU_DEVICE = -1


#: The per-row window table argument every fusedTierB and refineListedBounded launch ends with
#: (tierb.slang ROWWIN_PARAM): read only under a window start of ROWWIN_ON, so null otherwise.
_NOROW = ctypes.c_void_p(0)


def _u32(x):
    return ctypes.c_uint32(int(x) & 0xFFFFFFFF)


def _param_ptrs(params):
    """cuLaunchKernel's argument array: the address of each parameter (kept alive by the
    caller with params)."""
    return carray(ctypes.c_void_p, len(params))(*[ctypes.addressof(p) for p in params])


_PACK_U64 = struct.Struct("Q").pack_into
_WORDS = {}


def _pack_words(k):
    """pack_into for k uint32 words (an Arg(words=k)), made once per k."""
    f = _WORDS.get(k)
    if f is None:
        f = _WORDS[k] = struct.Struct("%dI" % k).pack_into
    return f


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
    holder = ctx._device_state
    pools = holder.__dict__.get("pools")
    if pools is None:
        pools = holder.pools = (_Pool(1 << 30), _Pool(256 << 20))       # device, page-locked
    return pools


class _Buffer(_Owned):
    """Device memory: cuMemAlloc'd, or reused from the device's pool (_Pool). Slotted, as
    are the other buffer kinds: a search holds thousands, which the garbage collector walks
    at every full collection."""
    __slots__ = ("_ctx", "_dev", "nbytes", "dptr", "_size", "ptr", "handle")

    def __init__(self, ctx, nbytes):
        self._own(ctx)
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

    def read_into(self, out, offset=0, stream=None):
        """Read the buffer's bytes from ``offset`` into a caller-provided contiguous array
        (synchronous), on ``stream`` (default: the context's)."""
        if not out.flags.c_contiguous:
            raise ValueError("read_into needs a C-contiguous array")
        to_copy = min(self.nbytes - offset, out.nbytes)
        if to_copy > 0:
            st = self.ctx.stream if stream is None else stream
            self.ctx._copy_d2h(out.ctypes.data, self.dptr.value + offset, to_copy, st,
                               "readback")
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


class _HostBuffer(_Owned):
    """Host-visible allocation for empty_shared: CUDA managed (unified) memory.

    One address valid on host and device. A ``readback`` allocation (an output
    the host will read) is advised to live in host memory and be mapped by the
    device, so a GPU write goes straight over the bus instead of migrating pages
    to the GPU and back on every call.
    """

    def __init__(self, ctx, nbytes, readback=False, host_input=False):
        self._own(ctx)
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


class _Pinned(_Owned):
    """Page-locked host staging for asynchronous readback (cuMemAllocHost)."""
    __slots__ = ("_ctx", "_dev", "nbytes", "_size", "ptr", "handle", "_raw")

    def __init__(self, ctx, nbytes):
        self._own(ctx)
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
        # an array-interface view: a ctypes byte array per size is a new ctypes type each
        # (_shared._Storage)
        self._raw = _Storage(self.ptr, self.nbytes).array(np.uint8, (self.nbytes,))

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


class _GraphCache(_Owned):
    """Instantiated CUDA graphs of one record, LRU-bounded; destroyed with the record."""
    nbytes = 0          # host-side handles: nothing for the cache budget

    def __init__(self, ctx, limit=8):
        self._own(ctx)                         # the context holds it through its records
        self.limit, self.items, self.seen = limit, {}, {}

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


class _Staged(_Owned):
    """A device buffer the host rewrites before every run (_x_alloc(upload=True)). The values
    go through page-locked staging in one asynchronous copy on the context's stream: a copy
    from managed memory costs ~144 us, and a kernel reading a host-written managed page
    faults it over (132 us a forward launch on the L40S, 15 us from device memory)."""
    __slots__ = ("_ctx", "_dev", "nbytes", "device", "pinned", "dptr")

    def __init__(self, ctx, nbytes):
        self._own(ctx)
        self.nbytes = max(int(nbytes), 4)
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


class _Section(Section):
    """A section of a device buffer with its own device pointer; the host reads it through
    the base buffer's mirror (Section.view)."""
    __slots__ = ("dptr",)

    def __init__(self, base, offset, nbytes):
        self.base, self.offset, self.nbytes = base, offset, nbytes
        self.dptr = ctypes.c_uint64(base.dptr.value + offset)
        self.ptr = self.handle = self.dptr.value

    def write(self, array, stream=None):
        raise TypeError("a section is written through its base buffer")


class _WordSlots:
    """Page-locked slots for the words of list update ops (_CudaList.update), carved from
    shared 4 KiB chunks and reused by size. A page-locked allocation each cost a
    cuMemAllocHost and a pinned page per update."""
    CHUNK = 4096

    def __init__(self, ctx):
        self._ctx = weakref.ref(ctx)           # the context holds its slots
        self.chunks, self.free = [], {}
        self.at, self.end = 0, 0

    @property
    def ctx(self):
        return self._ctx()

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


class _Readback(_Owned):
    """A device buffer the host reads (_x_alloc(readback=True)): a list's readback op copies
    a prefix of it into page-locked memory on the stream, so the host reads it after the
    run's one synchronization (a range past that prefix is copied when it is read)."""
    __slots__ = ("_ctx", "_dev", "nbytes", "device", "dptr", "pinned", "mirrored")

    def __init__(self, ctx, nbytes):
        self._own(ctx)
        self.nbytes = max(int(nbytes), 4)
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

    A kernel is (function, threads, leading buffers, trailing buffers[, extra words]): its
    first buffers, then its uniforms, then -- the per-row window table (tierb.slang
    ROWWIN_PARAM) -- the trailing ones, null where the caller binds none, and any trailing
    per-kernel specialization words (CUDA data stride and fp16 scale)."""

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
        extra = kernel[4] if len(kernel) > 4 else ()
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
        for x in extra:
            fields.append(("I", (int(x) & 0xFFFFFFFF,), None, 1))
        places, params, end = [], [], 0
        for fmt, _, _, count in fields:
            size = struct.calcsize(fmt)
            align = min(size // count, 16)
            end = -(-end // align) * align
            places.append(end)
            params += [end + i * (size // count) for i in range(count)]
            end += size
        block = carray(ctypes.c_char, max(end, 8))()
        base = ctypes.addressof(block)
        for (fmt, values, slot, _), at in zip(fields, places):
            struct.pack_into(fmt, block, at, *values)
            if slot is not None:            # (block, offset, name, byte offset or -words)
                self.args.append((block, at, slot[0], slot[1]))
        ptrs = carray(ctypes.c_void_p, len(params))(*[base + at for at in params])
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
        vals = carray(ctypes.c_uint32, len(words))(*[int(w) & 0xFFFFFFFF for w in words])
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


class Context(KernelRoles, Executor, InputUploads):
    """One NVIDIA CUDA device context, stream, and loaded PTX pipelines."""

    cache_limit_bytes = 1024 * 1024 * 1024
    _profile = False                # MF_GPU_PROFILE (with MF_GPU_TIMING): per-kernel times
    _in_run = None                  # inside a timed run: its kernels' and copies' regions
    #: The root kernels are verified on this backend (DeviceProps.device_root).
    device_root = True

    @property
    def timing(self):
        """Device timers on. ``_timing`` is the attribute shared with the Vulkan backend:
        _calibration.calibrate_costs_gpu switches it on around its measurement runs."""
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
        self.device_name = self.name        # what every driver calls it
        self.sm_count = self._attr(_cuda._CUDA_DEVICE_ATTR_MULTIPROCESSOR_COUNT) or 1
        self.cc = (self._attr(_cuda._CUDA_DEVICE_ATTR_COMPUTE_CAPABILITY_MAJOR),
                   self._attr(_cuda._CUDA_DEVICE_ATTR_COMPUTE_CAPABILITY_MINOR))
        # A block's limits, what the coarse candidates are held to (_coarse.candidates).
        self.max_invocations = self._attr(_cuda._CUDA_DEVICE_ATTR_MAX_THREADS_PER_BLOCK) or 1024
        self.max_shared_memory = (self._attr(_cuda._CUDA_DEVICE_ATTR_MAX_SHARED_MEMORY_PER_BLOCK)
                                  or 48 * 1024)

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
        # _shared._same_device: Contexts with one _device_state exchange buffers freely. A
        # context without the primary context has a state of its own (shared with none).
        if self._using_primary_ctx:
            shared = _DEVICE_SHARED.get(index)
            if shared is None:
                shared = _DEVICE_SHARED[index] = _DeviceShared(self.cuda, self.device.value)
        else:
            shared = _DeviceShared(self.cuda, self.device.value, self.ctx)
        self._device_state = shared
        self._modules, self._pipelines = shared.modules, shared.pipelines
        self._occupancy, self._labels = shared.occupancy, shared.labels
        self._shared_modules = self._using_primary_ctx
        props = shared.__dict__.get("props")
        if props is None:
            props = shared.props = self._device_props()
        self.props = props
        self._uploaded = {"data": {}, "tmpl": {}}

    # ---- device plumbing -----------------------------------------------------
    def _device_props(self):
        """The device's properties (_gpuhost.DeviceProps): its name and block limits as the
        driver reports them; the rest stated for every CUDA device."""
        return DeviceProps(
            name=self.name, artifact_family="cuda",
            max_group_memory=self.max_shared_memory, max_threads=self.max_invocations,
            # A resident grid strides over a listed op's items; constants are launch
            # parameters.
            indirect_dispatch=False, runtime_specialization=False, load_time_constants=False,
            # The most blocks one launch takes (gridDim.x), no per-binding limit below
            # the allocation, and a bound view's alignment for the widest element a
            # kernel reads (float2).
            max_dispatch_x=2 ** 31 - 1, max_binding_bytes=None, offset_alignment=16,
            subgroup_size=32, subgroup_range=None,          # the warp
            # Device memory is separate from host memory (residency matters for pricing);
            # shared allocations are managed memory, which migrates between the two.
            unified_memory=False, managed_inputs=True,
            # Unified addressing: a view inside a shared allocation is a device pointer.
            offset_views=True, host_pointer_views=False, shared_queue=False,
            fp16=True, cache_budget=self.cache_limit_bytes, memory_budget=None,
            device_root=self.device_root)

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
        """Read the timing events pending under key: wait for each region's end event, add the
        regions' elapsed times, and append (label, milliseconds) per run to timing_log, and per
        kernel when profiling. A run's time is the sum of its kernels' and copies' regions, not
        its first-to-last interval, which also held the host's gaps between launches.
        last_gpu_time is the total in seconds.
        """
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
    def _kernel_function(self, rec):
        """(function, threads per block) of a resolved kernel record (_kernels.resolve),
        loaded once per context."""
        key = ("record", rec["file"])
        got = self._pipelines.get(key)
        if got is None:
            got = self._pipelines[key] = self._load_record(rec)
        return got

    def _load_record(self, rec):
        """(function, threads per block) of a manifest record: its entry point at the block
        size it was built for."""
        wg = int(rec["local_size"][0])
        fn = rec["file"]
        stem = fn[:-len(".ptx.gz")] if fn.endswith(".ptx.gz") else fn[:-len(".ptx")]
        return self._load(stem, _PTX_DIR / fn, rec["entry"], wg), wg

    def _load(self, stem, ptx_file, fn_name, wg):
        """Load (once) a PTX module and return one of its functions."""
        mkey = stem
        if mkey not in self._modules:
            self._bind()
            mod = ctypes.c_void_p()
            raw = ptx_file.read_bytes()
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            ptx_bytes = raw + b"\0"
            # A block of wg threads must fit the SM's 64K-register file, or the
            # launch fails with CUDA_ERROR_LAUNCH_OUT_OF_RESOURCES: cap the JIT's
            # allocation at 65536 / wg (64 at 1024 threads, 128 at 512).
            cap = min(255, (65536 // max(wg, 1)) // 8 * 8)

            def load(ptx):
                if cap < 255 and hasattr(self.cuda, "cuModuleLoadDataEx"):
                    options = (ctypes.c_int * 1)(0)  # CU_JIT_MAX_REGISTERS
                    values = (ctypes.c_void_p * 1)(ctypes.c_void_p(cap))
                    check_cuda(
                        self.cuda.cuModuleLoadDataEx(ctypes.byref(mod), ptx, 1, options, values),
                        f"cuModuleLoadDataEx({stem})",
                    )
                else:
                    check_cuda(
                        self.cuda.cuModuleLoadData(ctypes.byref(mod), ptx),
                        f"cuModuleLoadData({stem})",
                    )
            try:
                load(ptx_bytes)
            except _cuda.CudaError as exc:
                # A driver older than the toolkit that built the kernels refuses their PTX
                # version. The kernels use nothing newer than their sm_75 target, so they are
                # offered again as the newest version this driver reads.
                older = _ptx_for_driver(ptx_bytes, self.cuda)
                if exc.code != _CUDA_ERROR_UNSUPPORTED_PTX_VERSION or older is None:
                    raise
                load(older)
            self._modules[mkey] = mod
        hfunc = ctypes.c_void_p()
        check_cuda(
            self.cuda.cuModuleGetFunction(ctypes.byref(hfunc), self._modules[mkey],
                                          fn_name.encode("utf-8")),
            f"cuModuleGetFunction({fn_name})",
        )
        self._labels[hfunc.value] = stem          # its module, for every Context on the device
        return hfunc

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


    # ---- flat ------------------------------------------------------------------

    # ---- full correlation --------------------------------------------------------
    # ---- driver primitives (_gpuexec) -----------------------------------------------------
    #: Tiers read full or band-only fp32 spectra directly in place via per-launch data stride
    #: and fp16 scale entry parameters (twiddle.slang), matching Vulkan and Metal without
    #: packCoarse or intermediate band allocations.
    inplace_feed = True

    def _x_kernel(self, name, n, consts=None):
        """The compiled kernel `name` at transform length n: the driver primitive `_x_kernel`
        (_gpuexec's module docstring lists the names and the build-time constants in consts).
        The build is the role table's (_kernels.resolve, under this device's limits). Returns
        (function, block size[, lead, trail, extra]): the PTX module's entry point and its
        block size, and for the tiered kernels how a launch orders its parameters -- the
        first `lead` buffers, the uniform words, the remaining buffers (`trail` of them
        optional), then `extra`, the data stride and fp16 scale passed as arguments.

        Raises UnsupportedSize where no build of the kernel was shipped that this device can run,
        and ValueError for a name that is not a kernel.
        """
        c = consts or {}
        rec = self._kernel_record(name, n, {k: c[k] for k in ("ppg", "tile", "twt", "gate") if k in c})
        fn, wg = self._kernel_function(rec)
        stride = int(c.get("stride") or 0)
        scale = (int(np.float32(2.0 ** int(c["scale"])).view(np.uint32))
                 if c.get("scale") else 0x3F800000)
        if name in ("peaks", "peaks1", "gate", "coarse"):
            return fn, wg, 4, 1, (stride, scale)
        if name in ("tier1_c16", "tier", "tier1", "refine", "refine1"):
            return fn, wg, 6, 1, (stride, scale)
        if name == "refine_td":
            return fn, wg, 11, 1
        return fn, wg

    def hier_peaks_grouped(self, *args, **kwargs):
        return hier_peaks_grouped(self, *args, **kwargs)

    def _x_coarse_candidates(self, band):
        """Every coarse layout (subgroup 0: the warp, ppg, tile, twt) at this band
        (_coarse.candidates): each shipped build this device's block limits hold
        (MAX_THREADS_PER_BLOCK, MAX_SHARED_MEMORY_PER_BLOCK), its twiddles computed or from
        the fp16 table (the "w" builds)."""
        props = self.props
        return candidates(band, lambda ppg, tile, twt: _kernels.coarse_record(
                              props, band, ppg, tile, bool(twt)),
                          lambda tile: (0, 1), self.max_invocations, self.max_shared_memory)

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
        return min(times) if times else 0.0     # 0.0: no run recorded a time (_choice.no_time)

    def _x_tierc(self, n):
        split = _kernels.two_stage(self.props.artifact_family, n)
        if split is None:
            raise UnsupportedSize("no two-stage kernels for n=%d" % n)
        return split

    def _x_alloc(self, nbytes, readback=False, upload=False):
        if upload:
            return _Staged(self, nbytes)
        return _Readback(self, nbytes) if readback else _Buffer(self, nbytes)

    def _x_list(self, label, once=False):
        """The shared command list (_gpuhost.CommandList); _x_record makes it a native one."""
        return CommandList(label, once, record=self._x_record)

    def _x_record(self, commands):
        """The native recording of a shared command list: today's launch-parameter list
        (_CudaList), built from the list's calls as they were made."""
        return commands.replay_into(_CudaList(self, commands.label)).end()

    def _x_run(self, native, wait, binds=None, slot=None, pre=()):
        stream = self._x_launch(native, binds, slot, pre)
        if wait:
            self._sync(stream)
        else:
            self._pend_write(stream)

    def _x_submit(self, native, binds, slot, pre=(), pending=False):
        """_x_run left in flight, returning wait(). With pending=True (the caller's choice: an
        unslotted run other work depends on) it is a pending write like a run with
        wait=False: another stream is ordered after it and a host reader settles it (a device
        root's series is read by the middle stage and, after settle_writes, by the host;
        without it a host read after settle_writes saw the unwritten series every time on an
        RTX 6000). Otherwise only its stream is ordered after it, and it is read through its
        wait(): a slotted leaf call made pending ordered every later launch on the device's
        other streams after the leaf calls in flight -- search_bench's steady pass took 1.55 s
        against 1.28 s (means of four runs each on the RTX 6000, alternated; three of the
        pairs 19-31% apart, one tied)."""
        stream = self._x_launch(native, binds, slot, pre)
        if pending:
            self._pend_write(stream)
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
        """Issue a recording's operations on stream, in order: kernel launches, 32-bit fills (one
        row, or rows at a pitch), host-to-device updates and device-to-host readbacks.
        """
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
        """Theoretical peaks (_roofline.gpu_peaks) from the driver's attributes
        (_peaks.cuda_gpu_peaks); a peak the attributes do not determine is reported unknown."""
        a = self._attr
        # MULTIPROCESSOR_COUNT, CLOCK_RATE (kHz), MEMORY_CLOCK_RATE (kHz),
        # GLOBAL_MEMORY_BUS_WIDTH, COMPUTE_CAPABILITY_MAJOR/MINOR
        return _pk.cuda_gpu_peaks(out, a(16), a(13), a(36), a(37), (a(75), a(76)))

    def _word_slots(self):
        slots = self.__dict__.get("_slots")
        if slots is None:
            slots = self._slots = _WordSlots(self)
        return slots

    def destroy(self):
        """Release what this context holds: cached recordings and buffers, its slots, the modules
        it loaded itself, timing events, streams, and the CUDA context (the device's primary
        context is released, an owned one destroyed). Safe to call twice.
        """
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
            for label, e0, e1 in pending:
                for _, r0, r1 in (e1 if e0 is None else ((label, e0, e1),)):
                    self._event_pool.extend((r0, r1))
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
