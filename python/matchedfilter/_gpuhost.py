"""Backend-neutral host logic shared by the Vulkan, CUDA and Metal GPU backends.

Everything here is pure Python/NumPy over plain integers and arrays: what to dispatch and
how results are laid out, never how. Each backend keeps its own submission mechanism
(command buffers and fences, streams and graphs, Metal command buffers) and calls these
helpers for the parts that must agree across backends.
"""

from collections import OrderedDict
import ctypes
import itertools

import numpy as np

from ._errors import UnsupportedSize
from ._windows import (
    coarse_lags, _merge_window_bins, _normalize_windows, _window_bin_phases, _window_layout)
from ._results import FilterResults, _EMPTY_FILTER_RESULTS
from ._shared import _same_device, containing, containing_samples, shared_buffer, sparsified
from .device import parse as _parse_device

#: Most bins one peak kernel dispatch reduces into (the kernels' compiled limit).
MAX_BINS = 2048


def address(ptr):
    """A host pointer as an integer, from a ctypes pointer or an integer."""
    return int(ptr.value if hasattr(ptr, "value") else ptr)


class MappedBuffer:
    """Host access to a device buffer whose memory the host sees at `ptr` for `nbytes`
    (a Vulkan buffer mapped for its lifetime, a Metal shared-storage buffer). A backend's
    buffer class creates and frees the memory and inherits the access from here; it must
    have a `_bytes` slot or a `__dict__`."""
    __slots__ = ()

    def write(self, array):
        """Copy an array to the start of the buffer."""
        flat = np.ascontiguousarray(array)
        ctypes.memmove(self.ptr, flat.ctypes.data, flat.nbytes)

    def read(self, dtype, count):
        """A copy of the first count elements."""
        out = np.empty(count, dtype=dtype)
        ctypes.memmove(out.ctypes.data, self.ptr, out.nbytes)
        return out

    def view(self, dtype, count):
        """The first count elements in place, without a copy (valid while the buffer lives).
        The bytes are wrapped once: a result reads several views per call."""
        raw = getattr(self, "_bytes", None)
        if raw is None:
            from ._shared import _Storage
            raw = self._bytes = _Storage(address(self.ptr), self.nbytes).array(np.uint8,
                                                                              (self.nbytes,))
        return raw[:count * np.dtype(dtype).itemsize].view(dtype)

    def read_into(self, out):
        """Copy the start of the buffer into a caller's contiguous array, and return it."""
        ctypes.memmove(out.ctypes.data, self.ptr, min(self.nbytes, out.nbytes))
        return out



class Arg:
    """A value a recording binds per run (_x_run's binds), not when it is recorded.

    A buffer: a caller's output or input that may lie elsewhere on every call. A record
    keyed on it would re-upload its other inputs whenever it moved, and could replay one
    call's binding into another's memory (handles are not identities).

    words=k: k uniform words (a search window, a threshold) that change between calls on
    the same buffers: one record serves every window."""
    __slots__ = ("name", "words")

    def __init__(self, name, words=0):
        self.name, self.words = name, words



class CommandList:
    """A command list: what a recording runs, in one form every backend takes.

    `_gpuexec` builds it through ctx._x_list(label, once) with the methods below, and end()
    hands it to the backend's _x_record, which makes the backend's native recording. The
    operations are one integer array (`ops`); everything that is an object -- a kernel, a
    buffer, an Arg bound per run, a stamp's name, an update's words -- is an index into the
    list's own tables. The list holds no API handle or enumerant: a kernel is whatever the
    backend's _x_kernel returned and a buffer whatever it allocated, and only the backend's
    emitter turns them into API calls. So the collector tracks a list's few tables, not an
    object per command.

    Operations and their meaning (and what each backend does with them today):

      DISPATCH kernel, groups, buffers, words[, offsets]
          run `kernel` over `groups` workgroups with `buffers` bound in order (each from its
          byte offset) and `words` as uniforms. Vulkan: bind pipeline, a descriptor set,
          push constants, vkCmdDispatch. CUDA: one launch, its parameters packed. Metal:
          a compute encoder's pipeline, buffers and bytes, dispatchThreadgroups.
      LISTED kernel, count, max_groups, buffers, words[, offsets]
          `kernel` over a list whose length a kernel wrote to `count` (a buffer), at most
          `max_groups` workgroups. Vulkan, Metal: an indirect dispatch on `count`. CUDA: a
          resident grid that strides over the list (max_groups appended as a word).
      BARRIER
          every earlier write before every later access. Vulkan: a pipeline barrier.
          CUDA: nothing (a stream is ordered). Metal: nothing (encoders are serial).
      STAMP name
          a phase boundary: the commands since the previous stamp are phase `name`. Fused
          batches interleave recordings phase by phase (Vulkan); a profiling run timestamps
          it. CUDA and Metal: nothing today.
      FILL buffer, word, offset, nbytes, rows, pitch
          set `rows` runs of `nbytes` bytes (None: to the end) every `pitch` bytes from
          `offset` to `word`. Vulkan: vkCmdFillBuffer per row. CUDA: memset per row.
          Metal: a blit fill (a byte pattern: 0 or 0xFFFFFFFF).
      UPDATE buffer, words
          write `words` to the start of `buffer` in stream order. Vulkan: vkCmdUpdateBuffer.
          CUDA: a copy from a word slot. Metal: a host write as the run is encoded.
      READBACK buffer, nbytes
          the host reads `nbytes` of `buffer` after the run. CUDA: a copy into page-locked
          memory. Vulkan, Metal: nothing (host-visible memory).

    An Arg (a buffer or k words bound per run) is stored as a negative index, -(i + 1) into
    `args`. Words are tagged: (0, value), (1, n, v0..vn-1) for a vector uniform, (2, arg, k)
    for an Arg's k words."""

    DISPATCH, LISTED, BARRIER, STAMP, FILL, UPDATE, READBACK = range(1, 8)
    __slots__ = ("label", "once", "ops", "kernels", "buffers", "args", "data", "_record",
                 "_index")

    def __init__(self, label, once=False, record=None):
        import array
        self.label, self.once, self._record = label, once, record
        self.ops = array.array("q")
        self.kernels, self.buffers, self.args, self.data = [], [], [], []
        self._index = {}                     # id(object) -> table index while building

    def _ref(self, table, obj, tag):
        key = (tag, id(obj))
        i = self._index.get(key)
        if i is None:
            i = self._index[key] = len(table)
            table.append(obj)
        return i

    def _buffer(self, b):
        if isinstance(b, Arg):
            return -(self._ref(self.args, b, "a") + 1)
        return self._ref(self.buffers, b, "b")

    def _words(self, words):
        out = [len(words)]
        for w in words:
            if isinstance(w, Arg):
                out += (2, self._ref(self.args, w, "a"), int(w.words))
            elif isinstance(w, tuple):
                out += (1, len(w)) + tuple(int(x) for x in w)
            else:
                out += (0, int(w))
        return out

    def _launch(self, code, kernel, head, buffers, words, offsets):
        buffers = list(buffers)
        self.ops.extend([code, self._ref(self.kernels, kernel, "k")] + head + [len(buffers)]
                        + [self._buffer(b) for b in buffers]
                        + ([1] + [int(o) for o in offsets] if offsets is not None else [0])
                        + self._words(words))

    def dispatch(self, kernel, groups, buffers, words=(), offsets=None):
        self._launch(self.DISPATCH, kernel, [int(groups)], buffers, words, offsets)

    def listed(self, kernel, count, max_groups, buffers, words=(), offsets=None):
        self._launch(self.LISTED, kernel, [self._buffer(count), int(max_groups)], buffers,
                     words, offsets)

    def barrier(self):
        self.ops.append(self.BARRIER)

    def stamp(self, name):
        self.ops.extend((self.STAMP, self._ref(self.data, name, "s")))

    def fill(self, buf, word, offset=0, nbytes=None, rows=1, pitch=0):
        self.ops.extend((self.FILL, self._buffer(buf), int(word) & 0xFFFFFFFF, int(offset),
                         -1 if nbytes is None else int(nbytes), int(rows), int(pitch)))

    def update(self, buf, words):
        self.data.append(tuple(int(w) & 0xFFFFFFFF for w in words))
        self.ops.extend((self.UPDATE, self._buffer(buf), len(self.data) - 1))

    def readback(self, buf, nbytes):
        self.ops.extend((self.READBACK, self._buffer(buf), int(nbytes)))

    def end(self):
        """The backend's native recording of this list (its _x_record). The list lets go of
        it: a native that keeps its list would otherwise hold the context through it, a
        cycle that only the collector frees."""
        record, self._record, self._index = self._record, None, None
        return record(self)

    def arg_names(self):
        """The names of the Args the list binds, sorted."""
        return sorted({a.name for a in self.args})

    def has_stamps(self):
        return any(op[0] == "stamp" for op in self.decode())

    def decode(self):
        """The list's operations as the calls that built it, in order: (name, arguments)
        with the objects that were passed (method names as above, lower case)."""
        ops, i, n = self.ops, 0, len(self.ops)
        buf = lambda k: self.args[-k - 1] if k < 0 else self.buffers[k]
        while i < n:
            code = ops[i]
            if code in (self.DISPATCH, self.LISTED):
                kernel = self.kernels[ops[i + 1]]
                if code == self.DISPATCH:
                    head, i = (ops[i + 2],), i + 3
                else:
                    head, i = (buf(ops[i + 2]), ops[i + 3]), i + 4
                nb = ops[i]
                buffers = [buf(k) for k in ops[i + 1:i + 1 + nb]]
                i += 1 + nb
                offsets = None
                if ops[i]:
                    offsets = list(ops[i + 1:i + 1 + nb])
                    i += 1 + nb
                else:
                    i += 1
                nw, words = ops[i], []
                i += 1
                for _ in range(nw):
                    tag = ops[i]
                    if tag == 0:
                        words.append(ops[i + 1])
                        i += 2
                    elif tag == 1:
                        words.append(tuple(ops[i + 2:i + 2 + ops[i + 1]]))
                        i += 2 + ops[i + 1]
                    else:
                        words.append(self.args[ops[i + 1]])
                        i += 3
                name = "dispatch" if code == self.DISPATCH else "listed"
                yield (name, kernel) + head + (buffers, words, offsets)
            elif code == self.BARRIER:
                yield ("barrier",)
                i += 1
            elif code == self.STAMP:
                yield ("stamp", self.data[ops[i + 1]])
                i += 2
            elif code == self.FILL:
                nb = ops[i + 4]
                yield ("fill", buf(ops[i + 1]), ops[i + 2], ops[i + 3], None if nb < 0 else nb,
                       ops[i + 5], ops[i + 6])
                i += 7
            elif code == self.UPDATE:
                yield ("update", buf(ops[i + 1]), list(self.data[ops[i + 2]]))
                i += 3
            elif code == self.READBACK:
                yield ("readback", buf(ops[i + 1]), ops[i + 2])
                i += 3
            else:
                raise ValueError("unknown command-list operation %d" % code)

    def replay_into(self, target):
        """Make the same calls on `target` (a backend's own list): its native form, built
        exactly as if the callers had called it."""
        for op in self.decode():
            name, args = op[0], op[1:]
            if name in ("dispatch", "listed"):
                getattr(target, name)(*args[:-3], args[-3], args[-2], args[-1])
            else:
                getattr(target, name)(*args)
        return target


def binding_key(value):
    """The identity of a value an Arg is bound to, for caching what a recording binds: an
    allocation's serial and offset (a view of a shared array), a buffer's serial, a section's
    base serial, offset and size, or the value itself (words). Serials are never reused, so
    a key cannot name a later allocation at a freed one's address or handle."""
    owner = getattr(value, "owner", None)
    if owner is not None and getattr(owner, "serial", None) is not None:
        return ("view", owner.serial, int(getattr(value, "offset", 0)))
    serial = getattr(value, "serial", None)
    if serial is not None:
        return ("buffer", serial)
    base = getattr(value, "base", None)
    if base is not None and getattr(base, "serial", None) is not None:
        return ("section", base.serial, int(value.offset), int(value.nbytes))
    return value


class BindingCache:
    """A recording's instances per binding of its Args: what a backend made for one set of
    bound values (a command buffer, a graph, an encode plan), the most recently used `limit`
    kept, keyed by binding_key so a key never outlives what it names. Each entry holds the
    values it binds, so nothing it names can be freed while it is kept.

    The backend passes make(binds) -> instance and free(instance, done) to each call, so the
    cache holds no reference to its owner (a bound method kept here made every recording a
    reference cycle, freed only by the collector: 18 GB of device memory held in a pycbc
    job). get() returns (instance, release): release() frees a one-off instance once its run
    has finished (None for a kept one). A `once` recording is made for its one run; past
    `limit` a transient run (one that is waited for) gets a one-off instance rather than
    evicting a kept one, whose eviction would wait for every queue."""
    __slots__ = ("limit", "entries")

    def __init__(self, limit=8):
        self.limit = limit
        self.entries = OrderedDict()         # key -> (instance, held values)

    def get(self, names, binds, make, free, once=False, transient=False):
        values = tuple(binds[name] for name in names)
        bound = dict(zip(names, values))
        if once:
            inst = make(bound)
            return inst, lambda: free(inst, True)
        key = tuple(binding_key(v) for v in values)
        entry = self.entries.pop(key, None)
        if entry is None:
            if transient and len(self.entries) >= self.limit:
                inst = make(bound)
                return inst, lambda: free(inst, True)
            if len(self.entries) >= self.limit:
                self.evict(next(iter(self.entries)), free)
            entry = (make(bound), values)
        self.entries[key] = entry           # most recently used last
        return entry[0], None

    def evict(self, key, free, done=False):
        """Free the instance kept under key (done: its runs are known to have finished)."""
        inst, _ = self.entries.pop(key)
        free(inst, done)

    def clear(self, free, done=False):
        """Free every kept instance."""
        for key in list(self.entries):
            self.evict(key, free, done)

    def __len__(self):
        return len(self.entries)


#: Phases of forward and hierarchical recordings, in execution order. A fused batch runs
#: every recording's work for a phase, then one barrier, then the next phase: the
#: dispatches of a phase are independent across recordings and overlap on the device.
#: A phase is ONE step of each recording: a fused batch emits every item's work for a phase
#: and then the barrier, so a recording's barrier only separates its phases. Steps that
#: depend on each other within a call (marking survivor blocks, then recomputing them) are
#: therefore separate phases.
FUSED_PHASES = ("forward", "fill", "pack", "coarse0", "compact0", "coarse1", "compact1",
                "refine_td", "mark", "recompute", "refine", "peaks")


def list_phases(commands):
    """A list's phases for fused batches: per STAMP-ended segment of its operations, in
    order, (phase name, its work operations' indices, its barriers' indices) -- the indices
    counting the list's operations from 0 -- or None when the list cannot be fused: a phase
    with a barrier between two of its commands (a batch keeps a phase's barriers for its
    end, so it would run them unordered), or a phase a batch does not know (FUSED_PHASES).
    Operations after the last stamp belong to no phase. Stamps name phases as recorded,
    except that the first coarse stamp is coarse0 and later ones coarse1, and compact is
    compact0."""
    out, cur, coarse = [], [], 0
    for k, op in enumerate(commands.decode()):
        if op[0] != "stamp":
            if op[0] != "readback":
                cur.append((op[0] == "barrier", k))
            continue
        label = op[1]
        if label.startswith("coarse"):
            name = "coarse%d" % min(coarse, 1)
            coarse += 1
        elif label == "compact":
            name = "compact0"
        else:
            name = label
        kinds = [b for b, _ in cur]
        if any(b and not all(kinds[i + 1:]) for i, b in enumerate(kinds)):
            return None
        if name not in FUSED_PHASES and name != "start":
            return None
        out.append((name, [k2 for b, k2 in cur if not b], [k2 for b, k2 in cur if b]))
        cur = []
    return out


def fusion_plan(items):
    """The steps of one fused submission over `items`, each a {phase: (has work, has a
    barrier)} for one recording: for each phase in FUSED_PHASES order, ("work", item index,
    phase) for every item with work in it, then ("barrier", phase) once if any item has a
    barrier there -- every list barrier is the same (CommandList.BARRIER), so one serves
    them all. Each backend's fused emitter carries the steps out: Vulkan records them into
    one command buffer."""
    steps = []
    for phase in FUSED_PHASES:
        barrier = False
        for i, phases in enumerate(items):
            got = phases.get(phase)
            if got is None:
                continue
            if got[0]:
                steps.append(("work", i, phase))
            barrier = barrier or got[1]
        if barrier:
            steps.append(("barrier", phase))
    return steps


#: ctypes array types the backends build calls with, made once (carray).
_CARRAYS = {}


def carray(ctype, n):
    """The ctypes array type ctype * n, made once for the process.

    ctypes keeps an array type only while something holds it, and a type is a reference
    cycle (it and its dict): each collection freed the call path's types, and the next calls
    made them again -- about 3,600 array types per top template of a pycbc GPU job, 1.4
    million objects of cyclic garbage over the job, which drove most of its collections.
    The lengths a call path uses (bindings, push-constant words, command counts) are few;
    a byte view of an allocation does not come here."""
    t = _CARRAYS.get((ctype, n))
    if t is None:
        t = _CARRAYS[(ctype, n)] = ctype * n
    return t


class BufferPool:
    """Device allocations a backend's buffers give back when freed, for its next buffers of
    the same kind and size class to take, instead of freeing and allocating again.

    A pycbc job builds a search per top template, and every search builds its plans'
    series sources, spectra pools, slots and outputs afresh: on the 8060S that was 118,545
    vkAllocateMemory/vkMapMemory and as many frees in the 171,828-template job, most of it
    6-8 MB series and spectra buffers (about 2 GB of them per top template), about 15 s of
    a 116 s job (2026-11-25). Allocations are pooled by the backend's kind key (memory type,
    usage) and size class (the smallest m * 2^k of m in 4..7 that holds the request: at
    most 25% over it).

    No constant bounds the pool: allocations live and idle together never exceed the most
    the backend ever had live at once (peak_live), so a pooled process never holds more
    device memory than it needed at its peak without the pool. Past that the idle
    allocations given back longest ago are freed.

    What a backend must guarantee to give an allocation back: no submitted work still uses
    it, the guarantee it already gives before freeing one. A recycled allocation keeps its
    old contents (`poison`, for tests, fills it with 0xFF bytes instead); its handle and host
    address are the old ones, so its buffer object takes a new serial (BUFFER_SERIALS).
    """

    #: Fill a recycled allocation with 0xFF bytes (float NaN) before it is handed out: for
    #: tests that look for readers of memory nobody wrote.
    poison = False

    def __init__(self):
        self.live_bytes = self.idle_bytes = self.peak_live = 0
        self.made = self.reused = self.freed = 0
        self._free = {}                  # (kind, capacity) -> {token: (res, ptr, release)}
        self._age = OrderedDict()        # token -> (kind, capacity), oldest first
        self._tokens = itertools.count()

    @staticmethod
    def size_class(nbytes):
        """The capacity an allocation of nbytes is made at: at least 256 bytes, else the
        smallest m * 2^k (m in 4..7) at or above nbytes."""
        n = max(int(nbytes), 256)
        k = max(0, n.bit_length() - 3)
        m = -(-n >> k)          # ceil(n / 2^k), in 4..8
        return m << k

    def take(self, kind, capacity):
        """An idle allocation (the backend's resources) of this kind and capacity, the one
        given back last, or None: the backend then makes one and calls note_made()."""
        free = self._free.get((kind, capacity))
        if not free:
            return None
        token, (res, ptr, _) = free.popitem()
        del self._age[token]
        self.idle_bytes -= capacity
        self.live_bytes += capacity
        self.reused += 1
        if self.poison and ptr:
            ctypes.memset(ptr, 0xFF, capacity)
        return res

    def note_made(self, capacity):
        """The backend made a new allocation of this capacity."""
        self.made += 1
        self.live_bytes += capacity
        self.peak_live = max(self.peak_live, self.live_bytes)
        self._trim()

    def give(self, kind, capacity, res, ptr, release):
        """Keep an allocation the backend is done with (res, its host address ptr; release(res)
        frees it), freeing the oldest idle ones past the peak."""
        self.live_bytes -= capacity
        token = next(self._tokens)
        self._free.setdefault((kind, capacity), {})[token] = (res, ptr, release)
        self._age[token] = (kind, capacity)
        self.idle_bytes += capacity
        self._trim()

    def _trim(self):
        while self._age and self.live_bytes + self.idle_bytes > self.peak_live:
            old, key = self._age.popitem(last=False)
            r, _, rel = self._free[key].pop(old)
            self.idle_bytes -= key[1]
            self.freed += 1
            rel(r)

    def clear(self):
        """Free every idle allocation."""
        for free in self._free.values():
            for res, _, release in free.values():
                release(res)
        self._free.clear()
        self._age.clear()
        self.idle_bytes = 0


class Section:
    """Bytes [offset, offset + nbytes) of a device buffer (a context's _x_section). The base
    buffer owns the memory; the section has the base's handle and its own host pointer."""
    __slots__ = ("base", "handle", "offset", "nbytes", "ptr")

    def __init__(self, base, offset, nbytes):
        self.base, self.handle, self.offset, self.nbytes = base, base.handle, offset, nbytes
        self.ptr = address(base.ptr) + offset

    def write(self, array):
        """Copy an array to the start of the section, up to the section's size."""
        flat = np.ascontiguousarray(array)
        ctypes.memmove(self.ptr, flat.ctypes.data, min(flat.nbytes, self.nbytes))

    def view(self, dtype, count):
        """The section's first count elements in place, read through the base buffer."""
        dtype = np.dtype(dtype)
        whole = self.base.view(np.uint8, self.offset + count * dtype.itemsize)
        return whole[self.offset:].view(dtype)

    def destroy(self, idle=False):
        """Nothing to free: the base buffer owns the memory."""


def bin_shift(binsize):
    """log2(binsize) when binsize is a power of two, else -1 (the kernels divide)."""
    binsize = int(binsize)
    return binsize.bit_length() - 1 if binsize & (binsize - 1) == 0 else -1


def coarse_span(n, band, lo, hi, lag_pad=0):
    """A gate tier's window in band samples, (start, end, span, shift): the caller's window
    [lo, hi) at n, widened by one band sample (plus lag_pad when clustered) at each end (as
    hmf.c), so a signal near either end has coarse samples on both sides.
    The tier reduces it to ONE bin, so the reported peak is the window's maximum -- all a
    gate needs. shift is bin_shift(span) (-1 when span is not a power of two)."""
    lp = int(lag_pad)
    if lp > 0:
        r = n // band
        lo_i, hi_i = int(lo), int(hi)
        if lo_i < lp * r or hi_i + lp * r > n:
            cstart, cend = 0, band
        else:
            pad = 1 + lp
            c0 = lo_i // r
            cstart = c0 - pad if c0 > pad else 0
            cend = max(cstart + 1, min(band, -(-hi_i // r) + pad))
    else:
        cstart, cend = coarse_lags(n, band, lo, hi)
    cspan = cend - cstart
    return cstart, cend, cspan, bin_shift(cspan)


def plan_items(items, binsize, align_words=1, max_bins=MAX_BINS, phase=None):
    """Output layout of a peaks_items submission.

    items are (lo, hi, a, b, t): rows a:b against template t over [lo, hi). Each item's
    (b - a, nbins) results start at a multiple of align_words 4-byte words -- a backend
    that selects them by descriptor offset passes its storage-offset alignment, one that
    uses pointers passes 1. phase: the rows' bin phases (or None), which count toward an
    item's bins (the most any of its rows needs). Returns (offsets, nbins per item, total
    words)."""
    offs, nbs, size = [], [], 0
    for lo, hi, a, b, t in items:
        top = 0 if phase is None or b <= a else int(np.max(phase[a:b]))
        nb = -(-(hi - lo + top) // binsize)
        if nb > max_bins:
            raise UnsupportedSize("an item's window exceeds the kernel bin limit")
        offs.append(size)
        nbs.append(nb)
        size += -(-((b - a) * nb) // align_words) * align_words
    return offs, nbs, size


def split_items(items, offs, nbs, indices, values, copy=False):
    """Per item (idx, val) shaped (b - a, 1, nbins) from the flat readback of plan_items.
    copy=True when the flat arrays are a reused host buffer."""
    out = []
    for (lo, hi, a, b, t), off, nb in zip(items, offs, nbs):
        c = (b - a) * nb
        i = indices[off:off + c].reshape(b - a, 1, nb)
        v = values[off:off + c].reshape(b - a, 1, nb)
        out.append((i.copy(), v.copy()) if copy else (i, v))
    return out


# ---- hierarchical calls: the argument contract every backend's hier_peaks shares ----------

def hier_tiers(n, band, ct0, raw_thr, cascade_band=None, ct1=None, raw_thr1=None):
    """Normalise a hier_peaks/hier_peaks_grouped chain to (band, ct0, raw_thr, cascade_band,
    ct1, raw_thr1) in the keyword convention.

    band/ct0/raw_thr may each be a (tier0, tier1) pair; a two-tier chain is then tier 0 =
    cascade_band with ct0/raw_thr and tier 1 = band with ct1/raw_thr1. An incomplete
    cascade raises: running one tier with another tier's threshold would be a different
    computation, not a slower one."""
    if isinstance(band, (tuple, list)):
        cascade_band, band = band[0], band[1]
    if isinstance(ct0, (tuple, list)):
        ct0, ct1 = ct0[0], ct0[1]
    if isinstance(raw_thr, (tuple, list)):
        raw_thr, raw_thr1 = raw_thr[0], raw_thr[1]
    if cascade_band is not None and (ct1 is None or raw_thr1 is None):
        raise ValueError("a two-tier cascade needs ct1 and raw_thr1")
    return band, ct0, raw_thr, cascade_band, ct1, raw_thr1


def hier_window(n, window, binsize):
    """(lo, hi, binsize, nbins) of a hierarchical call: the window clamped to [0, n],
    binsize defaulting to n (one bin)."""
    lo, hi = (0, n) if window is None else (int(window[0]), int(window[1]))
    lo, hi = max(0, min(lo, n)), max(0, min(hi, n))
    if lo >= hi:
        raise ValueError("empty window (%d, %d)" % (lo, hi))
    binsize = n if binsize is None else int(binsize)
    return lo, hi, binsize, -(-(hi - lo) // binsize)


def split_bins(call, lo, hi, binsize, max_bins, upload_data, upload_tmpl, sparse, async_submit):
    """A window wider than max_bins bins, as consecutive sub-windows of max_bins bins.

    call(window, upload_data, upload_tmpl) returns one sub-window's dense (idx, val); inputs
    upload with the first only. The result honours sparse and async_submit exactly as one
    call would (a collector when async_submit)."""
    span = max_bins * binsize
    pi, pv = [], []
    for a in range(lo, hi, span):
        i2, v2 = call((a, min(a + span, hi)), upload_data, upload_tmpl)
        pi.append(i2)
        pv.append(v2)
        upload_data = upload_tmpl = False             # already on the device
    res = sparsified((np.concatenate(pi, axis=2), np.concatenate(pv, axis=2)), sparse)
    return (lambda: res) if async_submit else res


def grouped_windows(groups, n, nd, binsize, max_bins=MAX_BINS, nbins=None, phase=None):
    """Validated (lo, hi, a, b) groups of a grouped call, as ints, and their common bin count
    (the first group's, or nbins if larger; no group may need more). phase: the rows' bin
    phases ([nd], or None), which count toward a row's bins (ap_bin_count)."""
    groups = tuple((int(lo), int(hi), int(a), int(b)) for lo, hi, a, b in groups)
    binsize = int(binsize)
    top = (lambda a, b: 0) if phase is None else (lambda a, b: int(np.max(phase[a:b])))
    need = lambda lo, hi, a, b: (hi - lo + top(a, b) + binsize - 1) // binsize
    nb = need(*groups[0])
    if nbins is not None:
        nb = max(nb, int(nbins))
    if nb > max_bins:
        raise ValueError("grouped dispatch exceeds the kernel bin limit")
    for lo, hi, a, b in groups:
        if not (0 <= lo < hi <= n) or not (0 <= a < b <= nd):
            raise ValueError("invalid group (%d, %d, %d, %d)" % (lo, hi, a, b))
        if need(lo, hi, a, b) > nb:
            raise ValueError("grouped windows must not exceed the first group's bin count")
    return groups, nb


_ROW_WINDOWS = {}


def grouped_row_windows(groups, n, nd, binsize, max_bins=MAX_BINS, nbins=None, phase=None):
    """The per-row form of a grouped call, for a backend whose hier_peaks takes row_windows:
    (groups, nb, win, (lo0, hi0)).

    win is uint32 [lo, hi, bin phase] per data row (tierb.slang ROWWIN_WORDS), phase the
    rows' bin phases ([nd], or None for 0: run_series' bin_phase); (lo0, hi0) is the
    recording's window, nb bins from the first group's start (clipped to n), which the
    per-row windows narrow on the device. A series call repeats the same few group layouts,
    so results are memoised (win is read-only)."""
    key = (tuple(tuple(g) for g in groups), n, nd, int(binsize), max_bins, nbins,
           None if phase is None else bytes(memoryview(np.ascontiguousarray(phase, np.uint32))))
    hit = _ROW_WINDOWS.get(key)
    if hit is not None:
        return hit
    groups, nb = grouped_windows(groups, n, nd, binsize, max_bins, nbins, phase)
    win = np.zeros(3 * nd, np.uint32)
    for lo, hi, a, b in groups:
        win[3 * a:3 * b:3] = lo
        win[3 * a + 1:3 * b:3] = hi
    if phase is not None:
        win[2::3] = np.asarray(phase, np.uint32)
    win.flags.writeable = False
    binsize = int(binsize)
    lo0 = groups[0][0]
    hi0 = min(n, lo0 + nb * binsize)
    if -(-(hi0 - lo0) // binsize) != nb:
        lo0, hi0 = max(0, n - nb * binsize), n
    if len(_ROW_WINDOWS) > 4096:
        _ROW_WINDOWS.clear()
    hit = _ROW_WINDOWS[key] = (groups, nb, win, (lo0, hi0))
    return hit


#: A window start that tells the coarse and refine kernels to read each data row's window from
#: their row-window table (tierb.slang ROWWIN_ON): CUDA and Metal, which have no
#: specialization constant for it.
ROWWIN_ON = 0xFFFFFFFF

_BAND_WINDOWS = {}


def band_windows(rowwin, n, band, lag_pad=0):
    """Per-row windows [lo, hi) in samples of an n-point transform, mapped onto a coarse band
    as coarse_span maps one window: band samples [lo // R - 1, ceil(hi / R) + 1) with R = n // band,
    widened by lag_pad when clustered (full [0, band) where cyclic wrap could clip a shifted
    member peak, matching hmf.c), clamped to the band, at least one sample. The coarse and
    listed tiers read these as they are. Mapped in the kernel instead, the same arithmetic
    made the band-256 coarse kernel 1.47x slower at SIMD16 on an Iris Xe. Memoised per table
    (grouped_row_windows' tables are memoised and read-only), as a call per segment maps the
    same few."""
    lp = int(lag_pad)
    key = (id(rowwin), n, band, lp) if lp else (id(rowwin), n, band)
    hit = _BAND_WINDOWS.get(key)
    if hit is not None and hit[0] is rowwin:
        return hit[1]
    w = np.asarray(rowwin, np.uint32).reshape(-1, 3)[:, :2].astype(np.int64)
    if lp > 0:
        r = n // band
        pad = 1 + lp
        lo, hi = w[:, 0], w[:, 1]
        c0 = lo // r
        cs = np.where(c0 > pad, c0 - pad, 0)
        ce = np.maximum(cs + 1, np.minimum(band, -(-hi // r) + pad))
        wrap = (lo < lp * r) | (hi + lp * r > n)
        cs = np.where(wrap, 0, cs)
        ce = np.where(wrap, band, ce)
    else:
        cs, ce = coarse_lags(n, band, w[:, 0], w[:, 1])
    # A coarse tier is one bin: its rows' bin phase is 0.
    out = np.ascontiguousarray(np.stack([cs, ce, np.zeros_like(cs)], 1).astype(np.uint32))
    if len(_BAND_WINDOWS) > 4096:
        _BAND_WINDOWS.clear()
    _BAND_WINDOWS[key] = (rowwin, out)
    return out


def hier_peaks_grouped(ctx, n, band, data, tmpl, ct0, raw_thr, groups, binsize, threshold,
                       upload_tmpl=True, cascade_band=None, ct1=None, raw_thr1=None,
                       slot=None, async_submit=False, sparse=False, nbins=None, max_bins=MAX_BINS,
                       handle_out=None, refine_reach=None, phase=None, band_offsets=None,
                       direct=None, tier0_cluster=None):
    """hier_peaks_grouped for any backend whose hier_peaks accepts row_windows: one
    recording, each tier a single dispatch over all rows, per-row windows in the kernels.

    groups holds (lo, hi, a, b): rows a..b of data searched over [lo, hi). Output bins
    follow the first group's bin count (or nbins). phase: the rows' bin phases (run_series'
    bin_phase), which the refine's row table carries."""
    if shared_buffer(data, ctx) is None:
        raise ValueError("grouped spectra must be GPU-shared (a forward batch)")
    groups, nb, win, window = grouped_row_windows(groups, n, data.shape[0], binsize,
                                                  max_bins, nbins, phase)
    extra = {} if handle_out is None else {"handle_out": handle_out}
    if band_offsets is not None:
        extra["band_offsets"] = band_offsets
    if tier0_cluster is not None:
        extra["tier0_cluster"] = tier0_cluster
    return ctx.hier_peaks(n, band, data, tmpl, ct0, raw_thr, binsize=int(binsize),
                          threshold=threshold, window=window, upload_data=False, nbins=nb,
                          upload_tmpl=upload_tmpl, cascade_band=cascade_band, ct1=ct1,
                          raw_thr1=raw_thr1, slot=slot, async_submit=async_submit,
                          sparse=sparse, row_windows=(groups, win), refine_reach=refine_reach,
                          direct=direct, **extra)


def window_results(hit, counts, starts, idx, val, template, n, by_count=True):
    """FilterResults of one follow-up window, as _batches._items_batch orders them:
    the (block, bin) pairs where ``hit`` holds, by the block's bin count, then block, then bin
    -- the order filter_series' one call per bin count gives -- or, by_count False (a window
    whose blocks carry bin phases: filter_series makes one call), by block, then bin.

    hit: (blocks, nbins) bool; counts: bins per block; starts: block start samples; idx/val:
    (blocks, nbins) peak lag and value; template: the global template index; n: block length.
    The one ordering rule every device follow-up path assembles with."""
    bi, bn = np.nonzero(hit)
    if not bi.size:
        return _EMPTY_FILTER_RESULTS
    if by_count:
        o = np.argsort(np.asarray(counts)[bi], kind="stable")
        bi, bn = bi[o], bn[o]
    st = np.asarray(starts, dtype=np.int64)[bi]
    return FilterResults(
        template_indices=np.full(bi.size, template, dtype=np.int64),
        sample_indices=st + np.asarray(idx)[bi, bn].astype(np.int64),
        snr=np.asarray(val)[bi, bn].astype(np.complex64),
        block_starts=st,
        block_lengths=np.full(bi.size, n, dtype=np.int64))


# ---- device follow-ups ---------------------------------------------------------------------
# A batch of threshold-0 single-template calls (a search's follow-ups) as listed entries
# for the refineItems kernel (src/gpu/refine_bounded.slang): per work group -- one
# (template group, binsize, series allocation) -- the rows to forward (block starts as offsets
# into the allocation) and one entry per row (row, local template, window start, window end,
# output slot). The host lays the blocks out with TimeDomainFilterBank._window_layout, so the
# windows are the host path's by construction, and assemble_followups orders the results as
# _items_batch does. The executor runs them (Executor.submit_followups): the forward of each
# group's rows, refineItems over its entries, and one wait.

class FollowupUnsupported(Exception):
    """Device follow-ups cannot take this batch; the caller runs it on the host."""


def _gpu_ctx_of(bank, g):
    """Return a GPU executor context on ``g``'s device without loading full bank spectra."""
    ctx = bank.__dict__.get("_followup_gpu_ctx")
    if ctx is not None:
        return ctx
    bank._groups
    plan = g._plan
    if plan is not None:
        return getattr(plan, "_gpu", None)
    if g.device is None or _parse_device(g.device).kind != "gpu":
        return None
    return getattr(g.get_single_plan(0), "_gpu", None)


def _followup_owner_ctx(bank, g):
    """Return the device's live follow-up GPU context or attach a fresh sibling to ``bank``."""
    pctx = _gpu_ctx_of(bank, g)
    if pctx is None:
        return None
    holder = getattr(pctx, "_device_state", None)
    if holder is not None:
        ref = holder.__dict__.get("followup_owner")
        owner = ref() if ref is not None else None
        if owner is not None:
            return owner
    ctx = bank.__dict__.get("_followup_gpu_ctx")
    if ctx is None:
        ctx = type(pctx)(_parse_device(g.device).index)
        bank._followup_gpu_ctx = ctx
    return ctx


def _followup_job_ok(bank, g, ser, bstarts):
    """Return True when ``(bank, g, ser, bstarts)`` is eligible for ``submit_followups``."""
    if not isinstance(ser, np.ndarray):
        return False
    if bstarts.size and int(bstarts.max()) + g.n > ser.size:
        return False
    ctx = _gpu_ctx_of(bank, g)
    if ctx is None:
        return False
    if ser.dtype == np.complex64:
        return containing(np.ascontiguousarray(ser), ctx) is not None
    if ser.dtype == np.float32:
        return containing_samples(ser, ctx) is not None
    return False


def followup_layout(jobs, ctx, max_rows=None):
    """(groups, layout) for single-template follow-up jobs [(bank, series, kwargs)], each a
    filter_series(series, windows=, binsize=, threshold=0, template_index=) call.

    groups: one dict per coalesced work group (n, bs, series allocation, layout code) with
    tstage (compact complex64 upload rows), n, bs, alloc, code, nser, rows, entries, and nbins.
    A real series is read in place: contiguous floats, or one lane of a complex row.
    layout: per job (group, starts, window starts, window ends, first entry, template group,
    local template, global template, windows, phases). Raises FollowupUnsupported when a job
    is not such a call, is not on ctx's device, has a series that is not device memory, has a
    block reading past its series (the host path pads with zeros), or a group passes max_rows."""
    groups = {}
    cold_by_group = {}
    layout = []
    for (bank, ser, kw) in jobs:
        kw = kw or {}
        ti = kw.get("template_index")
        if ti is None or kw.get("threshold") is None or float(kw["threshold"]) != 0.0 \
                or set(kw) - {"windows", "binsize", "threshold", "template_index"}:
            raise FollowupUnsupported("not a threshold-0 single-template call")
        bank._groups
        if ti < 0 or ti >= bank.n_templates:
            raise FollowupUnsupported("template_index out of range")
        g, tl = bank._template_map[ti]
        aligned = kw.get("binsize") is not None or bank.binsize is not None
        bs = int(kw["binsize"]) if kw.get("binsize") is not None else (bank.binsize or g.n)
        if bs < 1:
            raise FollowupUnsupported("invalid binsize")
        S = len(ser)
        w_arg = kw.get("windows")
        if w_arg is None or (
            type(w_arg) is slice and (w_arg.step is None or w_arg.step == 1)
            and (w_arg.start is None or type(w_arg.start) is int)
            and (w_arg.stop is None or type(w_arg.stop) is int)
        ):
            v0, v1 = (0, S) if w_arg is None else w_arg.indices(S)[:2]
            if v1 <= v0:
                W = np.empty((0, 2), dtype=np.int64)
                st = ws = we = np.empty(0, dtype=np.int64)
                ph = np.zeros(0, dtype=np.uint32)
            else:
                W = np.array([[v0, v1]], dtype=np.int64)
                step = g.n_valid
                c_bad = g.c_bad
                fidx = max(0, (v0 - c_bad) // step)
                st = np.arange(fidx * step, min(S, v1 - c_bad), step, dtype=np.int64)
                if st.size:
                    bvt0 = st + c_bad
                    rs = np.maximum(v0, bvt0)
                    re = np.minimum(v1, bvt0 + step)
                    ws = rs - st
                    we = re - st
                    ph = (((rs - v0) % bs).astype(np.uint32)
                          if aligned else np.zeros(st.size, dtype=np.uint32))
                else:
                    ws = we = st
                    ph = np.zeros(0, dtype=np.uint32)
        else:
            W = _normalize_windows(w_arg, S)
            st, ws, we = _window_layout(g, W, S)
            # The window's bins (filter_series): each block's bins numbered from its window's grid.
            ph = _window_bin_phases(W, st, ws, bs) if aligned else None
            ph = np.zeros(st.size, np.uint32) if ph is None else ph
        pctx = _gpu_ctx_of(bank, g)
        if pctx is None or not _same_device(pctx, ctx):
            raise FollowupUnsupported("not a plan on this device")
        ser = np.asarray(ser)
        if ser.dtype == np.complex64:
            c = containing(np.ascontiguousarray(ser), ctx)
            if c is None:
                raise FollowupUnsupported("series not device-resident")
            alloc, base, code, nser = c[0], c[1], 0, c[0].size
        elif ser.dtype == np.float32:
            c = containing_samples(ser, ctx)
            if c is None:
                raise FollowupUnsupported("series not device-resident")
            alloc, foff, stride = c
            if stride == 1:                 # floats, by their index in the allocation
                base, code, nser = foff, 1, 2 * alloc.size
            else:                           # one lane of complex samples
                base, code, nser = foff >> 1, ((foff & 1) << 2) | 2, alloc.size
        else:
            raise FollowupUnsupported("series is neither complex64 nor float32")
        if st.size and int(st.max()) + g.n > ser.size:
            raise FollowupUnsupported("a block reads past the series")
        k = int(st.size)
        if k == 0:
            layout.append((None, st, ws, we, 0, g, tl, ti, W, ph))
            continue
        # Coalesce across leaf template groups sharing (n, binsize, series allocation, layout):
        # a two-detector segment becomes two groups instead of one per active leaf bank.
        gw = groups.setdefault((g.n, bs, id(alloc), code), dict(
            n=g.n, bs=bs, alloc=alloc, code=code, nser=nser, rows=[], entries=[],
            nent=0, tmap={}, trows=[]))
        first = gw["nent"]
        if max_rows is not None and first + k > max_rows:
            raise FollowupUnsupported("too many rows")
        tkey = (id(g), int(tl))
        tslot = gw["tmap"].get(tkey)
        if tslot is None:
            tslot = len(gw["trows"])
            gw["tmap"][tkey] = tslot
            hcache = g.__dict__.setdefault("_followup_host_spec", OrderedDict())
            tl_i = int(tl)
            sp = hcache.get(tl_i)
            if sp is not None:
                hcache.move_to_end(tl_i)
                gw["trows"].append(sp)
            else:
                gw["trows"].append(None)
                cold_g = cold_by_group.get(id(g))
                if cold_g is None:
                    cold_g = cold_by_group[id(g)] = (g, OrderedDict())
                cold_g[1].setdefault(tl_i, []).append((gw, tslot))
        gw["rows"].append(np.asarray(st, np.int64) + base)
        ent = np.empty((k, 6), np.int64)               # refineItems' six words
        ent[:, 0] = first + np.arange(k)
        ent[:, 1] = tslot
        ent[:, 2] = np.minimum(np.asarray(ws, np.int64), g.n)
        ent[:, 3] = np.minimum(np.asarray(we, np.int64), g.n)
        ent[:, 4] = ent[:, 0]
        ent[:, 5] = ph
        gw["entries"].append(ent)
        gw["nent"] = first + k
        layout.append((gw, st, ws, we, first, g, tl, ti, W, ph))

    # Batch-transform all uncached template spectra per group in one C SIMD pass.
    for g, tl_map in cold_by_group.values():
        tls = list(tl_map.keys())
        specs = np.ascontiguousarray(g.full_spectra(tls), dtype=np.complex64)
        hcache = g._followup_host_spec
        for row_k, tl_i in enumerate(tls):
            sp = specs[row_k]
            hcache[tl_i] = sp
            for gw_ref, slot_idx in tl_map[tl_i]:
                gw_ref["trows"][slot_idx] = sp
        while len(hcache) > 512:
            hcache.popitem(last=False)

    out = list(groups.values())
    for gw in out:
        e = (np.concatenate(gw["entries"]) if gw["entries"] else np.empty((0, 6), np.int64))
        gw["rows"] = (np.concatenate(gw["rows"]) if gw["rows"]
                      else np.empty(0, np.int64)).astype(np.uint32)
        gw["entries"] = e.astype(np.uint32)
        nbins = max(1, int(((e[:, 3] - e[:, 2] + e[:, 5] + gw["bs"] - 1) // gw["bs"]).max())
                    if e.size else 1)
        nbins = 1 << (nbins - 1).bit_length()
        if nbins > MAX_BINS:
            raise FollowupUnsupported("window has too many bins")
        gw["nbins"] = nbins
        trows = gw["trows"]
        gw["tstage"] = (np.ascontiguousarray(np.stack(trows, axis=0), dtype=np.complex64)
                        if trows else np.empty((0, gw["n"]), dtype=np.complex64))
    return out, layout


def assemble_followups(layout, read):
    """Each job's FilterResults from a device run of followup_layout's groups, ordered as
    _batches._items_batch orders them. read(group) gives the group's (idx, val),
    each (entries, nbins), read once per group."""
    reads = {}
    empty = None
    out = []
    for gw, st, ws, we, first, g, tl, ti, W, ph in layout:
        if gw is None:
            if empty is None:
                z64 = np.empty(0, dtype=np.int64)
                empty = FilterResults(z64, z64, np.empty(0, dtype=np.complex64), z64, z64)
            out.append(empty)
            continue
        r = reads.get(id(gw))
        if r is None:
            idx_g, val_g = read(gw)
            r = reads[id(gw)] = (idx_g, val_g, np.arange(gw["nbins"])[None, :])
        k = int(st.size)
        idx = r[0][first:first + k]
        val = r[1][first:first + k]
        bs = gw["bs"]
        has_ph = bool(ph.any())
        if has_ph:
            counts = ((np.asarray(we, np.int64) - np.asarray(ws, np.int64)
                       + ph.astype(np.int64) + bs - 1) // bs)
        else:
            counts = (np.asarray(we, np.int64) - np.asarray(ws, np.int64) + bs - 1) // bs
        hit = (idx >= 0) & (r[2] < counts[:, None])
        res = window_results(hit, counts, st, idx, val, ti, g.n, by_count=not has_ph)
        if has_ph:
            # A bin a block edge cut is two partial bins: one per window bin (filter_series).
            res = FilterResults(*_merge_window_bins(W, bs, *res))
        out.append(res)
    return out


def submit_followups(jobs):
    """A collector giving the FilterResults of single-template follow-up jobs, submitted on
    the jobs' device without waiting (Executor.submit_followups); or None (not a GPU, or a
    batch outside what the device path takes: the caller runs the jobs on the host)."""
    if not jobs:
        return lambda: []
    try:
        bank, _, kw = jobs[0]
        bank._groups
        kw = kw or {}
        ti = kw.get("template_index")
        if ti is None or ti < 0 or ti >= bank.n_templates:
            return None
        if kw.get("threshold") is None or float(kw["threshold"]) != 0.0:
            return None
        g, _ = bank._template_map[ti]
        ctx = _followup_owner_ctx(bank, g)
        if ctx is None:
            return None
        return ctx.submit_followups(jobs)
    except (FollowupUnsupported, KeyError, IndexError, TypeError):
        return None
