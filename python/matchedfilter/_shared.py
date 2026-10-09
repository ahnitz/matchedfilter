"""Host-visible GPU allocations, with NumPy/DLPack lifetime ownership.

These arrays export CPU DLPack: a Vulkan/Metal allocation is not a CUDA or
ROCm allocation. Consumers must finish writing before a synchronous filter call.
"""
import bisect
import ctypes
import weakref
import numpy as np

_allocations = weakref.WeakValueDictionary()
# Sorted start addresses, for backends that bind views INSIDE an allocation
# (ctx.shared_views): CUDA unified memory has one address on host and device, so a
# row of a shared (templates, samples) output is itself a valid device pointer.
_starts = []


class _Allocation:
    def __init__(self, buffer):
        self.buffer = buffer
        start = int(buffer.ptr.value if hasattr(buffer.ptr, 'value') else buffer.ptr)
        _allocations[start] = self
        bisect.insort(_starts, start)

    def __del__(self):
        buf = self.buffer
        start = int(buf.ptr.value if hasattr(buf.ptr, 'value') else buf.ptr)
        i = bisect.bisect_left(_starts, start)
        if i < len(_starts) and _starts[i] == start:
            del _starts[i]
        if getattr(buf.ctx, 'device', None):
            buf.destroy()


def _caller_holds(allocation):
    """True while a caller's array (or a view of it) still holds this shared allocation:
    evicting the recordings that borrow it then frees nothing, so a cache budget must not
    count it. Dropped by the caller, only borrowers keep it, and eviction does free it."""
    ref = getattr(allocation, "_storage", None)
    return ref is not None and ref() is not None


class _Borrowed:
    """A descriptor reference; cache eviction must not free its allocation."""
    def __init__(self, allocation, offset=0):
        self.owner = allocation
        self.offset = offset
        self.handle = allocation.buffer.handle
        self.nbytes = allocation.buffer.nbytes - offset
        base = allocation.buffer.ptr
        self.ptr = (base.value if hasattr(base, 'value') else base) + offset if offset else base

    def write(self, array):
        pointer = self.ptr.value if hasattr(self.ptr, 'value') else self.ptr
        if array.ctypes.data != pointer:
            raise ValueError('shared input allocation changed during dispatch')

    def destroy(self):
        pass


def _same_device(a, b):
    """Contexts whose buffers are interchangeable: the same one, or two on one shared
    device (Vulkan contexts share a logical device per process; CUDA contexts on one
    device share its primary context)."""
    if a is b:
        return True
    da = getattr(a, '_device_state', None)
    return da is not None and da is getattr(b, '_device_state', None)


def _containing(address):
    """The live allocation whose range starts at or before ``address``."""
    i = bisect.bisect_right(_starts, address) - 1
    while i >= 0:
        start = _starts[i]
        allocation = _allocations.get(start)
        if allocation is not None:
            return start, allocation
        del _starts[i]           # freed: prune lazily
        i -= 1
    return None, None


def shared_buffer(array, ctx):
    """Recognize a contiguous prefix, including through host DLPack imports.

    A backend declaring ``shared_views`` also gets contiguous views that start
    inside an allocation (e.g. one row of a shared output), with ``offset`` set.
    """
    if not isinstance(array, np.ndarray) or not array.flags.c_contiguous:
        return None
    address = array.ctypes.data
    allocation = _allocations.get(address)
    offset = 0
    if allocation is None and getattr(ctx, 'shared_views', False):
        start, allocation = _containing(address)
        offset = address - start if allocation is not None else 0
    if (allocation is None or not _same_device(allocation.buffer.ctx, ctx)
            or offset + array.nbytes > allocation.buffer.nbytes):
        return None
    return _Borrowed(allocation, offset)


def containing(array, ctx):
    """(whole allocation as a 1-D array, element offset) when `array` lies inside a shared
    allocation usable by ctx -- e.g. one row of a device-resident (templates, samples)
    buffer -- else None. The returned array keeps the allocation alive."""
    if not isinstance(array, np.ndarray) or not array.flags.c_contiguous or array.nbytes == 0:
        return None
    addr, item = array.ctypes.data, array.dtype.itemsize

    def candidates():
        # The allocations that held recent series first: a segment's rows are all in one or
        # two, and scanning every live allocation per call cost ~5 ms a segment.
        for st in list(_recent):
            a = _allocations.get(st)
            if a is not None:
                yield st, a
        yield from list(_allocations.items())
    for start, allocation in candidates():
        nbytes = allocation.buffer.nbytes
        if (start <= addr and addr + array.nbytes <= start + nbytes
                and (addr - start) % item == 0 and _same_device(allocation.buffer.ctx, ctx)):
            whole = _whole.get(start)
            if whole is None or whole.dtype != array.dtype:
                storage = (ctypes.c_ubyte * (nbytes - nbytes % item)).from_address(start)
                storage._allocation = allocation
                whole = np.ndarray(((nbytes - nbytes % item) // item,), dtype=array.dtype,
                                   buffer=storage)
                _whole[start] = whole
            if start in _recent:
                _recent.remove(start)
            _recent.insert(0, start)
            del _recent[4:]
            return whole, (addr - start) // item
    return None


_recent = []


#: One whole-allocation view per allocation, so recordings keyed on it repeat.
_whole = weakref.WeakValueDictionary()


def shared_key(array, ctx):
    buf = shared_buffer(array, ctx)
    return array.ctypes.data if buf is not None else None


def empty_shared(ctx, buffer_type, shape, dtype=np.complex64):
    dtype = np.dtype(dtype)
    if dtype.hasobject:
        raise TypeError('shared arrays cannot contain Python objects')
    # NumPy validates dimensions and overflow before allocating GPU memory.
    shape = tuple(shape) if np.iterable(shape) else (shape,)
    probe = np.empty(shape, dtype=np.dtype('V0'))
    count = probe.size
    if count > np.iinfo(np.intp).max // max(dtype.itemsize, 1):
        raise ValueError('shared array is too large')
    nbytes = count * dtype.itemsize
    buf = buffer_type(ctx, nbytes)
    owner = _Allocation(buf)
    address = buf.ptr.value if hasattr(buf.ptr, 'value') else buf.ptr
    storage = (ctypes.c_ubyte * nbytes).from_address(address)
    storage._allocation = owner
    # Alive while any caller array or view of it is: see _Allocation.caller_holds.
    owner._storage = weakref.ref(storage)
    return np.ndarray(shape, dtype=dtype, buffer=storage)


def write_input(buffer, array):
    # Shared allocations already satisfy the dtype/layout contract. Do not
    # coerce them again: a prepared FFT may not have been submitted yet.
    if isinstance(buffer, _Borrowed):
        buffer.write(array)
    else:
        buffer.write(np.ascontiguousarray(array, np.complex64))
