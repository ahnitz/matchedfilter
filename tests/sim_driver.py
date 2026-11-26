"""A simulated GPU driver for the driver conformance suite (tests/test_driver_conformance.py).

A Context with the primitives the Vulkan, CUDA and Metal drivers provide (the _gpuexec
module docstring), over the shared executor (_gpuexec.Executor), the shared in-flight
results (_gpu_cache.InputUploads) and the shared allocation pool (_gpuhost.BufferPool). Its
device memory is host memory, and it runs submitted work lazily: a run executes only when
something waits on it, or when a run that must follow it executes. A run that nothing orders
after an earlier write therefore reads what its buffers held before that write, every time:
an ordering or settling fault in the shared layers, or in the driver contract itself, fails
deterministically here, where on a device it fails only when timing exposes it.

What it models:
  * one queue per (context, slot); two pieces of work on one queue execute in submission
    order only where a barrier lies between them (Vulkan's rule; CUDA and Metal order a
    queue without one, so the model is the strictest of the three);
  * pending writes (Executor._writes): every later run on the device, on any queue, follows
    them; settle_writes and settle_until execute them;
  * _x_after_readers (the next run of the context follows every unfinished run on the
    device), _x_idle (this context's runs), uploads ordered before later work on their slot;
  * recordings bound per run: up to 8 bindings kept per recording, a one-off recording past
    that, which must be freed once its run has finished (live_recordings counts them);
  * allocations recycled through BufferPool (allocations counts the ones it had to make);
  * host access at any time: a read sees whatever has executed. A run that executes on a
    buffer freed before it, a host write to a buffer an unfinished run binds, a free of a
    buffer an unfinished run binds and a release of a recording under its run raise
    SimHazard.

What it does not model: concurrency (one run executes at a time, and the dispatches of one
list in order, so ordering inside a list is not checked), kernels other than the two it
implements (forward and fwd_listed, the shipped kernels' arithmetic in NumPy), device time
(a run's time is the host's), cross-context fusion (_gpuexec.fused is not registered: a
fused batch is the unfused runs), memory limits, and anything about a real API (queue
counts, descriptor sets, graphs, command buffer reuse rules).

Faults (Context(faults=...)) reproduce driver bugs that occurred, so the suite can show that
its tests catch them (FAULTS).
"""
import ctypes
import itertools
import time
from collections import OrderedDict

import numpy as np

from matchedfilter._errors import UnsupportedSize
from matchedfilter._gpuexec import Arg, Executor
from matchedfilter._gpu_cache import InputUploads
from matchedfilter._gpuhost import BufferPool, CommandList, DeviceProps, MappedBuffer, Section
from matchedfilter._shared import BUFFER_SERIALS, empty_shared

#: Faults a simulated context can be given, each a driver bug that happened.
FAULTS = {
    "submit_not_pending":
        "_x_submit(pending=True) leaves its run unknown to settle_writes and to other queues "
        "(Metal and CUDA before 05fb2378: the device root's series read before it was "
        "written)",
    "run_ignores_slot":
        "_x_run(wait=False) runs on the main queue whatever its slot (Vulkan at 05fb2378)",
    "drops_pre_frees":
        "_x_run(wait=False) never frees the one-off recordings of its deferred work "
        "(Vulkan at 05fb2378)",
    "no_pool":
        "freed allocations are released, not recycled (Metal, and CUDA's shared arrays, at "
        "05fb2378; Vulkan before d9173faf)",
    "ctypes_per_call":
        "a ctypes array type made per submission (Vulkan and CUDA before 9e09963f, Metal "
        "before 7f8fbc59)",
    "update_at_encode":
        "a list's update words are written by the host when the run is submitted, not in "
        "order with the list's work (Metal at 05fb2378)",
    "time_no_sample_inf":
        "_x_time returns infinity when no run recorded a time (Metal at 05fb2378)",
}


class SimHazard(AssertionError):
    """A use of memory or a recording that the driver contract forbids: by a caller (a free
    or host write under a run in flight) or by the driver (a run that executes on freed
    memory)."""


class _Device:
    """The simulated device: its allocation pool, unfinished runs and pending writes."""

    #: A simulated device is never closed: a buffer made on it can always be freed.
    open = True

    def __init__(self):
        self.buffers = BufferPool()
        self.pending_writes = []
        self.jobs = []                  # unfinished runs, in submission order
        self.allocations = 0            # allocations made (pool misses)
        self.live_recordings = 0        # recordings bound and not yet freed
        self.handles = itertools.count(1)
        self.collector = None


class _Buffer(MappedBuffer):
    """Device memory: a byte array from the device's pool, or a new one."""
    __slots__ = ("ctx", "nbytes", "capacity", "mem", "ptr", "handle", "serial", "alive",
                 "_bytes", "_kind", "__weakref__")

    def __init__(self, ctx, nbytes, readback=False, upload=False):
        dev = ctx._device_state
        self.ctx, self.nbytes = ctx, max(int(nbytes), 4)
        self.capacity = dev.buffers.size_class(self.nbytes)
        self._kind = (bool(readback), bool(upload))
        mem = None if "no_pool" in ctx.faults else dev.buffers.take(self._kind, self.capacity)
        if mem is None:
            mem = np.zeros(self.capacity, np.uint8)
            dev.allocations += 1
            if "no_pool" not in ctx.faults:
                dev.buffers.note_made(self.capacity)
        self.mem, self.ptr = mem, mem.ctypes.data
        self.handle, self.serial, self.alive, self._bytes = next(dev.handles), next(
            BUFFER_SERIALS), True, None

    def write(self, array):
        self.ctx._check_unbound(self, "written by the host")
        MappedBuffer.write(self, array)

    def read_into(self, out, offset=0):
        ctypes.memmove(out.ctypes.data, self.ptr + offset, min(self.nbytes - offset, out.nbytes))
        return out

    def destroy(self, idle=False):
        """Give the allocation back to the pool (the caller guarantees no run uses it)."""
        if not self.alive:
            return
        self.alive = False
        if "no_pool" not in self.ctx.faults:
            self.ctx._device_state.buffers.give(self._kind, self.capacity, self.mem, self.ptr,
                                                lambda res: None)


def _place(binding, binds):
    """(base buffer, byte offset) of a binding: a buffer, a section, a shared view or an Arg."""
    if isinstance(binding, Arg):
        binding = binds[binding.name]
    owner = getattr(binding, "owner", None)
    if owner is not None:                       # a shared view (_shared._Borrowed)
        return owner.buffer, binding.offset
    base = getattr(binding, "base", None)
    if base is not None:                        # a section (_gpuhost.Section)
        return base, binding.offset
    return binding, 0


def _words(words, binds):
    out = []
    for w in words:
        if isinstance(w, Arg):
            v = binds[w.name]
            out.extend(v if isinstance(v, tuple) else (v,))
        elif isinstance(w, tuple):
            out.extend(w)
        else:
            out.append(w)
    return [int(w) & 0xFFFFFFFF for w in out]


def _array(place, dtype, count):
    buf, offset = place
    if not buf.alive:
        raise SimHazard("a run executed on a freed buffer (serial %d)" % buf.serial)
    dtype = np.dtype(dtype)
    if offset + count * dtype.itemsize > buf.nbytes:
        raise SimHazard("a run reached past the end of a %d-byte buffer" % buf.nbytes)
    return buf.mem[offset:offset + count * dtype.itemsize].view(dtype)


class _Kernel:
    """A shipped kernel's arithmetic: forward (seriesForward) and fwd_listed
    (seriesForwardListed), src/gpu/series_forward.slang and series_bands.slang."""

    def __init__(self, name, n):
        self.name, self.n = name, n

    def _block(self, series, start, nser, code):
        n = self.n
        x = np.zeros(n, np.complex64)
        m = int(min(max(nser - start, 0), n)) if start < nser else 0
        if m:
            if code == 0:
                x[:m] = _array(series, np.complex64, start + m)[start:]
            else:
                lane, stride = code >> 2, code & 3
                idx = lane + stride * np.arange(start, start + m)
                x[:m] = _array(series, np.float32, int(idx[-1]) + 1)[idx]
        return (np.fft.fft(x.astype(np.complex128)) / n).astype(np.complex64)

    def run(self, groups, places, words, listed):
        n = self.n
        if self.name == "forward":
            series, starts, spectra = places
            nser, code = words[0], words[1]
            st = _array(starts, np.uint32, groups)
            out = _array(spectra, np.complex64, groups * n).reshape(groups, n)
            for g in range(groups):
                out[g] = self._block(series, int(st[g]), nser, code)
        else:
            series, starts, spectra, blocks, args = places
            nser, code = words[0], words[1]
            count = int(_array(args, np.uint32, 1)[0])
            rows = _array(blocks, np.uint32, count)
            for item in range(count):
                row = int(rows[item])
                st = int(_array(starts, np.uint32, row + 1)[row])
                _array(spectra, np.complex64, (row + 1) * n)[row * n:] = self._block(
                    series, st, nser, code)


class _List:
    """A command list being recorded (_gpuexec's _x_list interface)."""

    def __init__(self, ctx, label, once):
        self.ctx, self.label, self.once, self.ops = ctx, label, once, []

    def dispatch(self, kernel, groups, buffers, words=(), offsets=None):
        self.ops.append(("dispatch", kernel, int(groups), list(buffers), list(words), offsets))

    def listed(self, kernel, count, max_groups, buffers, words=(), offsets=None):
        self.ops.append(("listed", kernel, count, list(buffers), list(words) + [int(max_groups)],
                         offsets))

    def barrier(self):
        self.ops.append(("barrier",))

    def stamp(self, name):
        self.ops.append(("stamp", name))

    def fill(self, buf, word, offset=0, nbytes=None, rows=1, pitch=0):
        if isinstance(buf, Arg):
            raise TypeError("a fill takes a buffer or view, not an Arg")
        self.ops.append(("fill", buf, int(word) & 0xFFFFFFFF, offset, nbytes, rows, pitch))

    def update(self, buf, words):
        if isinstance(buf, Arg):
            raise TypeError("an update takes a buffer or view, not an Arg")
        self.ops.append(("update", buf, np.asarray([int(w) & 0xFFFFFFFF for w in words],
                                                   np.uint32)))

    def readback(self, buf, nbytes):
        pass                            # host memory: the host reads it after the run

    def end(self):
        return _Native(self.ctx, self.label, self.ops, self.once)


class _Native:
    """A recorded list: an instance per binding of its Args, the last 8 kept, a one-off
    instance past that for a run that frees it when finished (as Vulkan records them)."""
    BINDINGS = 8

    def __init__(self, ctx, label, ops, once):
        self.ctx, self.label, self.ops, self.once = ctx, label, ops, once
        names = set()
        for op in ops:
            if op[0] in ("dispatch", "listed"):
                names.update(b.name for b in op[3] if isinstance(b, Arg))
                names.update(w.name for w in op[4] if isinstance(w, Arg))
        self.args = sorted(names)
        self.kept = OrderedDict()
        self.released = False
        self.first_barrier = bool(ops) and ops[0][0] == "barrier"
        self.last_barrier = bool(ops) and ops[-1][0] == "barrier"
        self.any_barrier = any(op[0] == "barrier" for op in ops)

    def instance(self, binds, transient):
        """Bind it: returns a release for a one-off instance (None for a kept one)."""
        if self.released:
            raise SimHazard("a released recording was run")
        dev = self.ctx._device_state
        key = tuple(id(binds[a]) if not isinstance(binds[a], tuple) else binds[a]
                    for a in self.args)
        if self.once or (key not in self.kept and transient and len(self.kept) >= self.BINDINGS):
            dev.live_recordings += 1
            freed = []

            def release():
                if not freed:
                    freed.append(True)
                    dev.live_recordings -= 1
            return release
        if key in self.kept:
            self.kept.move_to_end(key)
        else:
            if len(self.kept) >= self.BINDINGS:
                self.kept.popitem(last=False)
                dev.live_recordings -= 1
            self.kept[key] = tuple(binds[a] for a in self.args)  # holds what it binds
            dev.live_recordings += 1
        return None

    def release(self):
        self.ctx._device_state.live_recordings -= len(self.kept)
        self.kept.clear()
        self.released = True


class _Job:
    """One submission: (native, binds) items run in order, after the runs it follows."""

    def __init__(self, ctx, queue, items, follows):
        self.ctx, self.queue, self.items, self.follows = ctx, queue, items, follows
        self.done = self.running = False
        self.frees = []
        self.places = set()
        for native, binds in items:
            if native == "upload":
                self.places.add(id(binds[0]))
                continue
            for op in native.ops:
                if op[0] in ("dispatch", "listed"):
                    self.places.update(id(_place(b, binds)[0]) for b in op[3])
                elif op[0] in ("fill", "update"):
                    self.places.add(id(_place(op[1], binds)[0]))
        self.starts_barrier = items[0][0] == "upload" or items[0][0].first_barrier
        self.ends_barrier = items[-1][0] == "upload" or items[-1][0].last_barrier
        self.any_barrier = any(n == "upload" or n.any_barrier for n, _ in items)

    def uses(self, native):
        return any(n is native for n, _ in self.items)

    def run(self):
        """Execute this run, after every run it follows (once)."""
        if self.done:
            return
        if self.running:
            raise SimHazard("runs that follow each other")
        self.running = True
        for job in self.follows:
            job.run()
        t0 = time.perf_counter()
        for native, binds in self.items:
            if native == "upload":
                buf, data = binds
                ctypes.memmove(buf.ptr, data.ctypes.data, min(buf.nbytes, data.nbytes))
                continue
            for op in native.ops:
                self.ctx._execute(op, binds)
        self.done, self.running = True, False
        dev = self.ctx._device_state
        dev.jobs.remove(self)
        label = self.items[-1][0]
        if self.ctx._timing and label != "upload":
            self.ctx.timing_log.append((label.label, (time.perf_counter() - t0) * 1e3 + 1e-6))

    def finish(self):
        """Run it and free what it held (a run waited for, or a pending write settled)."""
        self.run()
        frees, self.frees = self.frees, []
        for free in frees:
            free()


class _Write:
    """A pending write (Executor._writes): settling executes its run."""
    __slots__ = ("job",)

    def __init__(self, job):
        self.job = job

    def settle(self):
        self.job.finish()


def stated_props(**values):
    """A DeviceProps of stated values: the simulated device's, with `values` in place of
    any of them (a test's driver that is not made by a driver's own __init__)."""
    props = dict(name="simulated GPU", artifact_family="sim", max_group_memory=32768,
                 max_threads=1024, indirect_dispatch=True, runtime_specialization=False,
                 load_time_constants=True,
                 max_dispatch_x=2 ** 31 - 1, max_binding_bytes=None, offset_alignment=16,
                 subgroup_size=32, subgroup_range=None, unified_memory=True,
                 managed_inputs=False, offset_views=False, host_pointer_views=False,
                 shared_queue=False, fp16=True, cache_budget=512 * 1024 * 1024,
                 memory_budget=None, device_root=False)
    props.update(values)
    return DeviceProps(**props)


class Context(Executor, InputUploads):
    """A simulated GPU context (see the module docstring): the driver primitives over host
    memory, run lazily. Contexts made with the same `device` share one simulated device."""

    inplace_feed = True
    #: No root kernels: a simulated device keeps the host root.
    device_root = False

    def __init__(self, index=0, device=None, faults=()):
        unknown = set(faults) - set(FAULTS)
        if unknown:
            raise ValueError("unknown faults %s" % sorted(unknown))
        self.faults = frozenset(faults)
        self._device_state = device if device is not None else _Device()
        self.device = "sim"
        self.device_name = self.name = "simulated GPU"
        # The simulated device's properties: stated, one record per simulated device.
        props = self._device_state.__dict__.get("props")
        if props is None:
            props = self._device_state.props = stated_props(
                name=self.device_name, cache_budget=self.cache_limit_bytes,
                device_root=self.device_root)
        self.props = props
        self._timing = False
        self.timing_log = []
        self._uploaded = {"data": {}, "tmpl": {}}
        self._last_after_readers = False
        self._queues = {}

    # ---- execution ------------------------------------------------------------------
    def _execute(self, op, binds):
        kind = op[0]
        if kind in ("barrier", "stamp"):
            return
        if kind == "fill":
            _, buf, word, offset, nbytes, rows, pitch = op
            base, boff = _place(buf, binds)
            size = (getattr(buf, "nbytes", base.nbytes) - offset) if nbytes is None else nbytes
            for r in range(rows):
                _array((base, boff + offset + r * pitch), np.uint32, size // 4)[:] = word
        elif kind == "update":
            if "update_at_encode" not in self.faults:
                _array(_place(op[1], binds), np.uint32, op[2].size)[:] = op[2]
        else:
            _, kernel, groups, buffers, words, offsets = op
            places = []
            for i, b in enumerate(buffers):
                base, boff = _place(b, binds)
                places.append((base, boff + (offsets[i] if offsets else 0)))
            if kind == "listed":
                count = _place(groups, binds)
                groups = int(_array(count, np.uint32, 1)[0])
            kernel.run(groups, places, _words(words, binds), kind == "listed")

    def _submit(self, items, slot):
        """A new run of items on (self, slot), after what the contract orders it after."""
        if "ctypes_per_call" in self.faults:
            # a length no other code holds a type of, so the type dies with the call
            ctypes.sizeof((ctypes.c_uint32 * (7919 + len(items)))())
        dev = self._device_state
        job = _Job(self, slot, items, [])
        queue = self._queues.setdefault(slot, [])
        queue[:] = [j for j in queue if not j.done]
        follows = []
        barrier = job.starts_barrier
        for earlier in reversed(queue):
            if barrier or earlier.ends_barrier:
                follows.append(earlier)
            barrier = barrier or earlier.any_barrier
        follows.extend(w.job for w in dev.pending_writes if not w.job.done)
        if self._last_after_readers:
            follows.extend(dev.jobs)
            self._last_after_readers = False
        job.follows = list({id(j): j for j in follows}.values())
        queue.append(job)
        dev.jobs.append(job)
        if "update_at_encode" in self.faults:
            for native, binds in items:
                for op in (native.ops if native != "upload" else ()):
                    if op[0] == "update":
                        _array(_place(op[1], binds), np.uint32, op[2].size)[:] = op[2]
        return job

    def _bind_items(self, native, binds, pre, transient, job_frees):
        items, frees = [], []
        for nat, b in pre:
            release = nat.instance(b or {}, True)
            items.append((nat, b or {}))
            if release is not None:
                frees.append(release)
        release = native.instance(binds or {}, transient)
        items.append((native, binds or {}))
        if release is not None:
            job_frees.append(release)
        return items, frees

    def _check_unbound(self, buf, what):
        for job in self._device_state.jobs:
            if id(buf) in job.places:
                raise SimHazard("a buffer %s while a run in flight binds it" % what)

    # ---- driver primitives ----------------------------------------------------------
    def _x_kernel(self, name, n, consts=None):
        from matchedfilter._kernels import ROLES
        if name not in ROLES:
            raise ValueError("no GPU kernel %r" % (name,))
        if (name in ("forward", "fwd_listed") and 64 <= n <= 65536 and n & (n - 1) == 0
                and not (consts or {}).get("gate")):
            return _Kernel(name, n)
        raise UnsupportedSize("the simulated driver has no %s kernel at n=%d" % (name, n))

    @staticmethod
    def _x_has_c16(band):
        return False

    #: The optional kernels a driver is asked about (_x_has_kernel); none is simulated.
    _OPTIONAL = ("compactc", "tier1", "tier1_c16", "fwd_tier0", "items", "tier1gate",
                 "refine_td")

    def _x_has_kernel(self, name, n):
        if name not in self._OPTIONAL:
            raise ValueError(name)
        return False

    @staticmethod
    def _x_coarse_candidates(band):
        return []

    def _x_time(self, native, binds, reps):
        times = []
        for rep in range(reps + 1):
            job = self._submit([(native, binds or {})], None)
            t0 = time.perf_counter()
            job.finish()
            if rep:
                times.append(time.perf_counter() - t0 + 1e-9)
        if not times and "time_no_sample_inf" in self.faults:
            return float("inf")
        return min(times) if times else 0.0

    @staticmethod
    def _x_tierc(n):
        raise UnsupportedSize("the simulated driver has no two-stage transform")

    def _x_alloc(self, nbytes, readback=False, upload=False):
        return _Buffer(self, nbytes, readback, upload)

    @staticmethod
    def _x_section(buf, offset, nbytes):
        return Section(buf, offset, nbytes)

    def _x_upload(self, buf, array, slot):
        data = np.ascontiguousarray(array).copy()
        base, offset = _place(buf, {})
        target = base if not offset else Section(base, offset, buf.nbytes)
        self._submit([("upload", (target, data))], slot)

    def _x_list(self, label, once=False):
        """The shared command list (_gpuhost.CommandList), as every backend takes it."""
        return CommandList(label, once, record=self._x_record)

    def _x_record(self, commands):
        """The native recording of a shared list: the simulated list built from its calls."""
        return commands.replay_into(_List(self, commands.label, commands.once)).end()

    def _x_run(self, native, wait, binds=None, slot=None, pre=()):
        frees = []
        items, pre_frees = self._bind_items(native, binds, pre, wait, frees)
        queue = None if (not wait and "run_ignores_slot" in self.faults) else slot
        job = self._submit(items, queue)
        job.frees = frees + ([] if (not wait and "drops_pre_frees" in self.faults)
                             else pre_frees)
        if wait:
            job.finish()
        else:
            self._writes().append(_Write(job))

    def _x_submit(self, native, binds, slot, pre=(), pending=False):
        frees = []
        items, pre_frees = self._bind_items(native, binds, pre, True, frees)
        job = self._submit(items, slot)
        job.frees = frees + pre_frees
        if pending and "submit_not_pending" not in self.faults:
            self._writes().append(_Write(job))
        return job.finish

    def _x_prefetch(self, view, offset, nbytes, slot):
        pass

    def _x_after_readers(self):
        self._last_after_readers = True

    def _x_release(self, native, done=False):
        for job in list(self._device_state.jobs):
            if job.uses(native):
                if done:
                    raise SimHazard("a recording released (done=True) under its run")
                job.run()
        native.release()

    def _x_idle(self):
        for job in [j for j in self._device_state.jobs if j.ctx is self]:
            job.run()

    def _x_free(self, buf):
        self._check_unbound(buf, "freed")
        buf.destroy()

    @staticmethod
    def _x_read(buf, out, offset=0):
        base, boff = _place(buf, {})
        ctypes.memmove(out.ctypes.data, base.ptr + boff + offset, out.nbytes)

    @staticmethod
    def _x_view(buf, dtype, count):
        return buf.view(dtype, count)

    def _x_timings(self):
        self._x_idle()

    @staticmethod
    def _x_peaks(out):
        out.update(formulas="simulated: no peaks")
        return out

    # ---- what the shared layers call besides primitives -------------------------------
    def empty_shared(self, shape, dtype=np.complex64, *, readback=False, host_input=False):
        return empty_shared(self, lambda ctx, nbytes: _Buffer(ctx, nbytes, readback), shape,
                            dtype)

    def clear_cache(self):
        self._exec_clear()

    def destroy(self):
        if self.device is None:
            return
        self._x_idle()
        self.clear_cache()
        self.device = None
