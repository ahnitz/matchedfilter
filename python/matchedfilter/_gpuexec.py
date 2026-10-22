"""GPU operations written once, over a thin per-API driver (stage U, docs/unification-plan.md).

A backend Context (Vulkan, CUDA, Metal) inherits Executor and supplies only driver
primitives -- how to allocate, record, submit and read back on its API. Every decision an
operation makes uses what the driver reports about the hardware, never which API it is, so
a change made here reaches every GPU at once. The operations: full and continuous
correlation, the forward transform, flat peaks and follow-up items (here), the hierarchical
search (_gpuhier), and deferred work: a forward held for the next run on its slot, which runs
it first in the same submission or, a hierarchical call, claims it (_pending, _take,
_exec_claim).

Driver primitives (a Context provides each):

  _x_kernel(name, n, consts=None)
                            the compiled kernel `name` at transform length n, or raise
                            UnsupportedSize: an opaque handle the context's command lists take.
                            consts: build-time constants (twiddle.slang) -- stride (a data
                            row stride in elements, 0 the kernel's own length), scale (the
                            fp16 tier's data scale exponent), rowwin (per-row windows), and a
                            coarse kernel's layout (sg, ppg, tile, twt). Names: peaks/peaks1
                            (fusedTierB, one bin), gate (fusedTierB as a gate tier), coarse
                            (the fp16 role), tier/tier1 and refine/refine1 (the bounded
                            listed refine), compact, compactl, compact_peaks, mark, pack,
                            forward, fwd_tier0, fwd_bands, fwd_listed, full, series, and the
                            two-stage tc1/tc2/tcs2/tf1/tf2.
  _x_has_c16(band), _x_has_kernel(name, n)
                            whether an fp16 coarse build, or an optional kernel (tier1: a
                            one-bin build; fwd_tier0) was shipped for this target.
  _x_coarse_candidates(band)
                            the coarse layouts (sg, ppg, tile, twt[, driver kind]) the device
                            can run at this band, for the measured choice (_gpuhier).
  _x_time(native, binds, reps)
                            the least device time of reps runs, in seconds.
  _x_tierc(n)               (n1, n2): the two-stage transform's split at n (UnsupportedSize
                            if there is none).
  _x_alloc(nbytes, readback=False, upload=False)
                            a device buffer the context owns (write(array), read_into(out),
                            destroy(), nbytes). readback: the host reads it; upload: the host
                            writes it before every run, through _x_upload.
  _x_section(buf, offset, nbytes)
                            a view of bytes [offset, offset + nbytes) of an _x_alloc buffer,
                            bound, filled, updated and counted like a buffer (offset: a
                            multiple of storage_offset_alignment). A record's small words
                            share one buffer, so they move in one copy each way.
  _x_upload(buf, array, slot)
                            write an upload buffer, ordered before the next work on `slot`.
  _x_list(label, once=False)
                            a command list being recorded (once: run once, then freed):
                              dispatch(kernel, groups, buffers, words=(), offsets=None)
                                buffers are bound in order, each a device buffer or view or
                                an Arg (bound per run); offsets (bytes) add to each binding's.
                                words are the kernel's uniform parameters in declaration
                                order: a uint32 (a float or signed value as its bits), a
                                tuple of them for a vector parameter (a uint4), or an Arg
                                with words=k: k scalar parameters bound per run (binds[name]
                                is then a tuple of k uint32);
                              listed(kernel, count, max_groups, buffers, words=())
                                a bounded kernel over a list whose length a kernel wrote to
                                count[0]: indirect where the device dispatches that way,
                                else a resident grid striding over it; the driver appends
                                the kernel's gridSize word;
                              barrier()      all earlier work before all later work, memory
                                             and indirect arguments included;
                              stamp(name)    a phase boundary: the work since the previous
                                             stamp is phase `name` (fused batches interleave
                                             recordings phase by phase, a phase's commands
                                             unordered: dependent work needs its own phase;
                                             MF_GPU_PROFILE times it);
                              fill(buf, word, offset=0, nbytes=None, rows=1, pitch=0)
                                             set every 32-bit word of bytes [offset,
                                             offset + nbytes) of a buffer or view (nbytes
                                             None: to its end) to word (0 or 0xFFFFFFFF: a
                                             byte pattern), in each of `rows` rows `pitch`
                                             bytes apart (offset, nbytes, pitch: multiples
                                             of 4);
                              update(buf, words) write a few words, in order with the work;
                              readback(buf, nbytes)
                                             the host reads the first nbytes of `buf` after
                                             the run (a copy into host memory on a device
                                             that does not share it; nothing where it does);
                              end()          -> native: what _x_run runs and _x_release frees.
  _x_run(native, wait, binds=None, slot=None, pre=())
                            run a recorded list, binding each Arg to binds[name] (a view), on
                            the queue or stream of pipelining slot `slot`, after `pre`
                            ((native, binds) deferred for it) in the same submission;
                            wait=False leaves it in flight as a pending write (device work is
                            ordered after it, a host reader waits through settle_writes).
  _x_submit(native, binds, slot, pre=())
                            _x_run, returning wait(): a call that blocks until it has finished
                            (a result read later).
  _x_prefetch(view, offset, nbytes, slot)
                            start moving a span of a shared allocation to the device ahead of
                            the kernel that reads it (memory that migrates).
  _x_after_readers()        order the next run after earlier device work on this device that
                            may still read what it rewrites (another context's queue).
  _x_release(native, done=False)
                            free a recording (done: its runs are known to have finished).
  _x_idle()                 wait for every run this context submitted (its own queues or
                            streams: not other contexts' work on the device).
  _x_free(buf)              free an _x_alloc buffer no run of this context still uses (a
                            driver whose frees synchronize the device keeps it for reuse).
  _x_read(buf, out, offset=0)
                            copy bytes of a readback buffer from `offset` into a host array,
                            after the run that wrote them has finished.
  _x_timings()              finish every measurement still outstanding into timing_log.
  _x_peaks(out)             the device's theoretical peaks for _roofline.gpu_peaks: out (the
                            device, name, backend) updated with flops per precision, bandwidth
                            and the formulas they come from.
  _x_view(buf, dtype, count)
                            the first count elements of a readback buffer as a host array,
                            read in place where the host sees that memory (valid until the
                            buffer's next run: gather from it, do not keep it), else a copy.

Features a driver reports (attributes): max_dispatch_x (the most groups one dispatch takes),
storage_offset_alignment (a bound buffer's offset must be a multiple of this),
stage_host_inputs (shared allocations migrate between host and device: kernels must not read
small host-written inputs from them, which are uploaded into device memory instead, and spans
a kernel will read are prefetched), inplace_feed (kernels are specialized when created, so
the hierarchical tiers read the spectra in place at a stride and scale; else packed bands),
subgroup_size, kernel_family (whose kernel identity stored measured choices belong to).
"""
import time
import weakref

import numpy as np

from ._errors import UnsupportedSize
from ._gpuhier import HierOps
from ._gpuhost import MAX_BINS, bin_shift, plan_items, split_items
from ._shared import shared_view


#: Drivers whose devices batch submissions across contexts (register_fusion).
_FUSERS = []


def register_fusion(begin):
    """A driver's fused(): begin collecting on its devices; returns a close."""
    _FUSERS.append(begin)


def fused():
    """Begin a fused batch on every device of every loaded driver that batches submissions
    (filter_series_many); returns a callable that closes them."""
    closes = [begin() for begin in _FUSERS]

    def close():
        for c in closes:
            c()
    return close


def settle(pend):
    """Settle a device's writes left in flight (Executor._writes), oldest first."""
    while pend:
        pend.pop(0).settle()


def _allocation(buf):
    """The identity of the device allocation a buffer or view lies in."""
    owner = getattr(buf, "owner", None)
    return id(owner.buffer if owner is not None else buf)


class Record:
    """A cached recording of one operation shape: the buffers it binds (`owned` are the
    context's, freed with it; the rest are callers' shared allocations) and the driver's
    native recording."""
    __slots__ = ("buffers", "owned", "native")

    def __init__(self):
        self.buffers, self.owned, self.native = {}, set(), None


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


_OUT, _STARTS, _SERIES, _SPECTRA = Arg("out"), Arg("starts"), Arg("series"), Arg("spectra")


#: How a sparse result can be read (flat peaks: compacted on the device or read dense and
#: scanned on the host; hierarchical: the survivors' rows gathered on the host, or the hits
#: compacted on the device), the first the preference.
SPARSE_WAYS = {"flat": ("compact", "dense"), "hier": ("rows", "compact")}
#: The sparse-way choice (_choice.Choice, online, per call shape): after one dropped call
#: (it may build the record), three timed calls of each way; the lower median is used
#: (tie 0: the effect is the whole call's), and the trial repeats every 256 calls, so a
#: choice made under other load does not stick.
_SPARSE_SCHEDULE = dict(warmup=1, minimum=3, tie=0.0, z=0.0, retrial=256)


class _Records(dict):
    """The executor's records, counting every one built (Executor.built)."""
    __slots__ = ("built",)

    def __init__(self):
        super().__init__()
        self.built = 0

    def __setitem__(self, key, rec):
        self.built += 1
        super().__setitem__(key, rec)


class Executor(HierOps):
    """The operations every GPU backend runs, written once. See the module docstring for
    the driver primitives a backend supplies."""

    #: Working bytes one full-correlation dispatch may take before it is tiled.
    _FULL_BUDGET = 64 * 1024 * 1024
    #: Peak records a sparse result reads back with the count; more take a second read.
    _SPARSE_FIRST = 4096
    #: See the module docstring (a driver feature).
    stage_host_inputs = False

    # ---- records ------------------------------------------------------------------------
    def _exec_table(self):
        table = self.__dict__.get("_exec_records")
        if table is None:
            table = self._exec_records = _Records()
        return table

    def built(self):
        """How many recordings this context has built (records, and a driver's own, e.g.
        CUDA graphs): a call that built one ran setup, not steady-state work, and a timing
        that is to stand for steady state (a block-size trial) leaves it out."""
        return self._exec_table().built + self.__dict__.get("_x_built", 0)

    def _exec_buffer(self, rec, name, view=None, nbytes=0, readback=False, upload=False):
        """Bind `view` -- an array's place in device memory (a caller's shared allocation, or
        a view into one at an allowed offset; shared_view) -- or, without one, a buffer of the
        context's own of nbytes."""
        buf = view
        if buf is None:
            buf = self._x_alloc(nbytes, readback=readback, upload=upload)
            rec.owned.add(name)
        rec.buffers[name] = buf
        return buf

    # ---- deferred work ------------------------------------------------------------------
    def _pending(self):
        """slot -> [(native, binds, source)]: recorded work held for the next run on that slot
        (a deferred forward), which runs it first in the same submission -- or which a
        hierarchical call may claim and replace (_exec_claim)."""
        table = self.__dict__.get("_exec_pend")
        if table is None:
            table = self._exec_pend = {}
        return table

    def _defer(self, native, binds, slot, source):
        self._pending().setdefault(slot, []).append((native, binds, source))

    def _take(self, slot, reads=None):
        """The work held for `slot`, removed, for a run on `slot` to submit first. An
        unslotted run also needs other slots' work that writes what it reads (reads: the
        allocations it binds; None: unknown, so all of it): each such slot's work, up to its
        last item the run reads, runs now on its own slot -- where its staged inputs were
        written -- as pending writes the run is ordered after. The rest stays deferred for
        its own consumer (which may claim it): a middle-stage correlation once flushed every
        leaf forward, and its host reads then waited for them."""
        table = self._pending()
        if not table:
            return ()
        work = [(native, binds) for native, binds, _ in table.pop(slot, ())]
        if slot is None:
            for other in list(table):
                items = table[other]
                cut = len(items)
                if reads is not None:
                    hit = [i for i, (_, _, src) in enumerate(items)
                           if src is None or _allocation(src[7]) in reads]
                    if not hit:
                        continue
                    cut = hit[-1] + 1
                run, keep = items[:cut], items[cut:]
                if keep:
                    table[other] = keep
                else:
                    del table[other]
                *pre, (native, binds, _) = run
                self._x_run(native, False, binds, other, pre=[(n, b) for n, b, _ in pre])
        return work

    @staticmethod
    def _reads(rec, binds):
        """The allocations a run of `rec` binds (its buffers and the per-run ones)."""
        out = {_allocation(b) for b in rec.buffers.values()}
        out.update(_allocation(b) for b in (binds or {}).values() if not isinstance(b, tuple))
        return out

    def _take_items(self):
        """The work every follow-up item slot (("items", i)) holds, in item order."""
        table = self._pending()
        keys = sorted((k for k in table if isinstance(k, tuple) and k and k[0] == "items"),
                      key=lambda k: k[1:])
        return [(native, binds) for k in keys for native, binds, _ in table.pop(k)]

    def _exec_claim(self, slot, data, nd):
        """A hierarchical call taking the deferred forward that writes `data` (all nd rows,
        from row 0), to run its own feed in its place: (series, starts, row, count, nser,
        code) of that forward, or None. data None (a replay): drop the slot's forward, which
        the replayed record's own feed stands in for."""
        table = self._pending()
        key = slot if slot in table else (next(iter(table)) if slot is None and len(table) == 1
                                          else None)
        work = table.get(key)
        if not work:
            return None
        for i, (native, binds, source) in enumerate(work):
            if data is None:
                hit = True
            elif source is None:
                continue
            else:
                n, series, starts, row, count, nser, code, spectra, address = source[:9]
                hit = (address == data.ctypes.data and count == nd and row == 0)
            if hit:
                del work[i]
                if not work:
                    del table[key]
                if data is None:
                    return None
                # The claimer binds the forward record's staged starts: that record stays
                # until the claimer has run (_exec_hold; a tiny cache budget once evicted it
                # while the claimer was recorded, and its kernels read freed memory).
                if len(source) > 9:
                    self.__dict__.setdefault("_exec_hold", set()).add(source[9])
                return (series, starts, row, count, nser, code)
        return None

    def _exec_run_holding(self, native):
        """Run now, and wait for, the deferred work of every slot that holds a run of
        `native`: an input of that recording is about to be rewritten."""
        for slot, work in list(self._pending().items()):
            if any(nat is native for nat, _, _ in work):
                del self._pending()[slot]
                *pre, (nat, binds, _) = work
                self._x_run(nat, True, binds, slot, pre=[(n, b) for n, b, _ in pre])

    def cancel_forward(self, slot=None):
        """Drop deferred forwards that will not run: every slot's, or one slot's."""
        table = self._pending()
        if slot is None:
            table.clear()
        else:
            table.pop(slot, None)

    def _exec_run(self, native, wait, binds, slot, rec=None):
        """Run a recorded list on `slot`, after the work deferred for it (one submission).
        rec: the record it belongs to (what an unslotted run reads, _take)."""
        reads = None if rec is None or slot is not None else self._reads(rec, binds)
        self._x_run(native, wait, binds, slot, pre=self._take(slot, reads))

    def _exec_submit(self, native, binds, slot, rec=None):
        """_exec_run, left running: returns wait() (_x_submit)."""
        reads = None if rec is None or slot is not None else self._reads(rec, binds)
        return self._x_submit(native, binds, slot, pre=self._take(slot, reads))

    def _exec_evict(self, key, done=False):
        """Drop one executor record: its in-flight results are collected first, then the
        driver frees its recording and the buffers it owns (done: this context is idle)."""
        self._drain()
        rec = self._exec_table().pop(key, None)
        if rec is None:
            return
        # Work still deferred from this record runs now: it writes spectra a caller reads.
        for slot, work in list(self._pending().items()):
            mine = [(nat, b) for nat, b, _ in work if nat is rec.native]
            if mine:
                self._pending()[slot] = [w for w in work if w[0] is not rec.native]
                if not self._pending()[slot]:
                    del self._pending()[slot]
                for nat, b in mine:
                    self._x_run(nat, True, b, slot)
        self._x_release(rec.native, done)        # waits for the record's runs unless done
        for name in rec.owned:
            self._x_free(rec.buffers[name])
        for resident in self._uploaded.values():
            resident.pop(key, None)

    def _exec_room(self, estimate, incoming=()):
        """Room for a new record: at most cache_limit_entries records (the least recently
        used evicted first), then the byte budget (_cache_room)."""
        table, order = self._exec_table(), getattr(self, "_cache_order", {})
        hold = self.__dict__.get("_exec_hold", ())
        while len(table) >= self.cache_limit_entries:
            key = next((k for k in order if k not in hold), None)
            if key is None:
                break
            order.pop(key)
            self._exec_evict(key)
        self._cache_room(estimate, incoming=incoming)

    def _exec_clear(self):
        """Evict every executor record (clear_cache, a dropped layout): one wait for this
        context's work, then every record freed as finished. A wait per record was a
        device-wide synchronization each (CUDA's shared primary context, Vulkan's shared
        queues): a context of 300 records stalled every other plan's pipeline 300 times."""
        table = self._exec_table()
        if not table:
            return
        self._drain()
        self._x_idle()
        for key in list(table):
            # Deferred work of an evicted record runs (waited) before it is freed.
            self._exec_evict(key, done=True)

    def _exec_upload(self, rec, key, uploads, data, tmpl, slot):
        """Write the inputs _input_uploads found stale into the record's own buffers (a
        shared input is read in place: nothing to write), ordered on `slot`."""
        for i, (name, array) in enumerate((("data", data), ("tmpl", tmpl))):
            if uploads[i] and name in rec.owned:
                self._x_upload(rec.buffers[name], np.ascontiguousarray(array, np.complex64),
                               slot)
            if uploads[i]:
                self._uploaded[name][key] = uploads[2 + i]

    def _exec_owned_buffers(self):
        for rec in self.__dict__.get("_exec_records", {}).values():
            for name in rec.owned:
                yield rec.buffers[name]

    # ---- full correlation ---------------------------------------------------------------
    def correlate(self, n, data, tmpl, out, *, upload_data=True, upload_tmpl=True, wait=True):
        """Full circular correlation of every (data, template) pair, unnormalised, in natural
        lag order: out[d, t, lag]. Tiled when one dispatch would need more working storage
        than _FULL_BUDGET or more groups than the device takes.

        wait=False, with `out` in device memory and one tile: left in flight (a pending
        write: device consumers are ordered after it, a host reader settles first)."""
        nd, nt = data.shape[0], tmpl.shape[0]
        if out.shape != (nd, nt, n):
            raise ValueError('full output shape does not match the banks')
        limit = getattr(self, "max_binding_bytes", None)
        row = nt * n * 8
        if limit and out.nbytes > limit and nd > 1 and row <= limit:
            # One binding spans at most `limit` bytes (Vulkan's maxStorageBufferRange): runs
            # of whole data rows, each a contiguous slice of `out`.
            rows = max(1, limit // row)
            for d0 in range(0, nd, rows):
                d1 = min(d0 + rows, nd)
                self.correlate(n, data[d0:d1], tmpl, out[d0:d1], upload_data=upload_data,
                               upload_tmpl=upload_tmpl, wait=True)
            return out
        tierc = n > 65536
        split = self._x_tierc(n) if tierc else None
        groups = max(split) if tierc else 1
        ov = shared_view(out, self)
        direct = ov is not None
        working = nd * nt * 8 * n * ((1 if direct else 2) if tierc else (0 if direct else 1))
        if (working <= self._FULL_BUDGET and nd * nt * groups <= self.max_dispatch_x
                and not (limit and out.nbytes > limit)):
            self._correlate_tile(n, data, tmpl, out, upload_data, upload_tmpl, split,
                                 wait or not direct, ov)
            return out
        per_pair = 8 * n * (2 if tierc else 1)
        tile = min(nt, max(1, self._FULL_BUDGET // per_pair),
                   max(1, self.max_dispatch_x // groups),
                   max(1, limit // (8 * n)) if limit else nt)
        for d in range(nd):
            for t0 in range(0, nt, tile):
                t1 = min(t0 + tile, nt)
                o = out[d:d + 1, t0:t1]
                self._correlate_tile(n, data[d:d + 1], tmpl[t0:t1], o, upload_data, upload_tmpl,
                                     split, True, shared_view(o, self))
        return out

    def _correlate_tile(self, n, data, tmpl, out, upload_data, upload_tmpl, split, wait, ov):
        nd, nt = data.shape[0], tmpl.shape[0]
        dv, tv = shared_view(data, self), shared_view(tmpl, self)
        # Keyed on the bytes the recording binds in place (an array's address where it is
        # bound as a view), else None (the record's own buffer, written by upload).
        key = ("full", n, nd, nt, dv is not None and data.ctypes.data,
               tv is not None and tmpl.ctypes.data, ov is not None and out.ctypes.data)
        uploads = self._input_uploads(key, data, tmpl, upload_data, upload_tmpl)
        table = self._exec_table()
        rec = table.get(key)
        if rec is None:
            views = [v for v in (dv, tv, ov) if v is not None]
            estimate = (sum(a.nbytes for a, v in ((data, dv), (tmpl, tv), (out, ov)) if v is None)
                        + (nd * nt * n * 8 if split else 0))
            self._exec_room(estimate, incoming=views)
            rec = Record()
            bd = self._exec_buffer(rec, "data", dv, data.nbytes)
            bt = self._exec_buffer(rec, "tmpl", tv, tmpl.nbytes)
            bo = self._exec_buffer(rec, "out", ov, out.nbytes, readback=True)
            lst = self._x_list("full")
            if split:
                scratch = self._exec_buffer(rec, "scratch", nbytes=nd * nt * n * 8)
                lst.dispatch(self._x_kernel("tc1", n), nd * nt * split[0], [bd, bt, scratch], (nt,))
                lst.barrier()
                lst.dispatch(self._x_kernel("tc2", n), nd * nt * split[1], [scratch, bo])
            else:
                lst.dispatch(self._x_kernel("full", n), nd * nt, [bd, bt, bo], (nt,))
            lst.barrier()
            if "out" in rec.owned:
                lst.readback(bo, out.nbytes)
            rec.native = lst.end()
            table[key] = rec
            uploads = (True, True, *uploads[2:])
        self._cache_touch(key)
        if (uploads[0] and "data" in rec.owned) or (uploads[1] and "tmpl" in rec.owned):
            self.settle_writes()       # a call left in flight may still read these inputs
        self._write_uploads(key, uploads, rec.buffers["data"], data, rec.buffers["tmpl"], tmpl)
        self._exec_run(rec.native, wait, None, None, rec)
        if "out" in rec.owned:
            self._x_read(rec.buffers["out"], out)

    # ---- continuous correlation ---------------------------------------------------------
    def correlate_continuous(self, n, data, tmpl, starts, out, lo, hi, *, upload_data=True,
                             upload_tmpl=True, async_submit=False):
        """Full correlation of each data block with every template, lags [lo, hi) written at
        the block's absolute series offset: out[t, starts[d] + lag] (template-major).

        out (templates, samples) and starts (one per data block) lie in device memory -- a
        shared allocation or a view inside one -- and are bound per call, so the record (and
        its uploaded templates) does not follow them. async_submit: left in flight, a pending
        write (device consumers are ordered after it, a host reader settles first)."""
        nd, nt = data.shape[0], tmpl.shape[0]
        ov, sv = shared_view(out, self), shared_view(starts, self)
        if ov is None or out.ndim != 2 or out.shape[0] != nt or starts.shape != (nd,):
            raise ValueError('continuous output must be a shared GPU buffer of every template')
        length = out.shape[1]
        limit = getattr(self, "max_binding_bytes", None)
        if limit and out.nbytes > limit and nt > 1 and length * 8 <= limit:
            # One binding spans at most `limit` bytes: groups of whole templates, each a
            # contiguous run of `out`'s rows (see correlate).
            group = max(1, limit // (length * 8))
            for t0 in range(0, nt, group):
                t1 = min(t0 + group, nt)
                self.correlate_continuous(n, data, tmpl[t0:t1], starts, out[t0:t1], lo, hi,
                                          upload_data=upload_data, upload_tmpl=upload_tmpl,
                                          async_submit=False)
            return out
        if limit and out.nbytes > limit:
            raise ValueError("continuous output of %d bytes per template exceeds this device's "
                             "%d-byte binding limit: correlate a shorter series" % (length * 8, limit))
        split = self._x_tierc(n) if n > 65536 else None
        # The two-stage form needs per-pair scratch: runs of whole data rows bound it (a row
        # past the budget is one run). Each run's starts are its own uploaded copy.
        rows = max(1, min(nd, self._FULL_BUDGET // (nt * n * 8))) if split else nd
        runs = [(d0, min(d0 + rows, nd)) for d0 in range(0, nd, rows)]
        # Block starts are uploaded where they lie outside device memory, where the device
        # stages host-written inputs, or per run (each run's starts from its first row).
        staged = self.stage_host_inputs or sv is None or len(runs) > 1
        dv, tv = shared_view(data, self), shared_view(tmpl, self)
        key = ("series", n, nd, nt, length, lo, hi, dv is not None and data.ctypes.data,
               tv is not None and tmpl.ctypes.data, staged)
        uploads = self._input_uploads(key, data, tmpl, upload_data, upload_tmpl)
        table = self._exec_table()
        rec = table.get(key)
        if rec is None:
            estimate = (sum(a.nbytes for a, v in ((data, dv), (tmpl, tv)) if v is None)
                        + (rows * nt * n * 8 if split else 0))
            self._exec_room(estimate, incoming=[v for v in (dv, tv) if v is not None])
            rec = Record()
            bd = self._exec_buffer(rec, "data", dv, data.nbytes)
            bt = self._exec_buffer(rec, "tmpl", tv, tmpl.nbytes)
            scratch = (self._exec_buffer(rec, "scratch", nbytes=rows * nt * n * 8)
                       if split else None)
            words = (nt, length, lo, hi)
            lst = self._x_list("continuous")
            lst.barrier()                 # earlier readers of `out` finish first
            for i, (d0, d1) in enumerate(runs):
                bs = (self._exec_buffer(rec, "starts%d" % i, nbytes=(d1 - d0) * 4, upload=True)
                      if staged else _STARTS)
                if split:
                    lst.dispatch(self._x_kernel("tc1", n), (d1 - d0) * nt * split[0],
                                 [bd, bt, scratch], (nt,), offsets=[d0 * n * 8, 0, 0])
                    lst.barrier()
                    lst.dispatch(self._x_kernel("tcs2", n), (d1 - d0) * nt * split[1],
                                 [scratch, bs, _OUT], (words,))
                else:
                    lst.dispatch(self._x_kernel("series", n), nd * nt, [bd, bt, bs, _OUT],
                                 (words,))
                lst.barrier()
            rec.native = lst.end()
            table[key] = rec
            uploads = (True, True, *uploads[2:])
        self._cache_touch(key)
        if staged or (uploads[0] and "data" in rec.owned) or (uploads[1] and "tmpl" in rec.owned):
            self.settle_writes()          # a call left in flight may still read these inputs
        self._write_uploads(key, uploads, rec.buffers["data"], data, rec.buffers["tmpl"], tmpl)
        if staged:
            for i, (d0, d1) in enumerate(runs):
                self._x_upload(rec.buffers["starts%d" % i], starts[d0:d1], None)
        if async_submit:
            self._x_after_readers()
        self._exec_run(rec.native, not async_submit,
                       {"out": ov} if staged else {"out": ov, "starts": sv}, None, rec)
        return out

    # ---- device timers ------------------------------------------------------------------
    def timings(self):
        """The timing log (MF_GPU_TIMING=1; _gputime), outstanding measurements settled: a
        (label, device ms) per submission of a recorded list -- its _x_list label; the device
        time it kept busy, including work submitted ahead of it in the same submission, and
        never the host's (CUDA, issuing a timed run launch by launch, sums its kernels and
        copies) -- and with MF_GPU_PROFILE=1 also ("k:<phase or kernel>", device ms) inside
        it (count those only once: they lie within the submission's)."""
        self._x_timings()
        return self.timing_log

    # ---- writes left in flight ----------------------------------------------------------
    def _writes(self):
        """The device's writes left in flight (a run with wait=False), oldest first: driver
        tokens, each with settle() -- wait for that run and free what it held. Device work
        is ordered after them by the driver; a host reader settles them."""
        holder = getattr(self, "_device_state", None) or self
        pend = holder.__dict__.get("pending_writes")
        if pend is None:
            pend = holder.pending_writes = []
        return pend

    def settle_writes(self):
        """Wait for every write left in flight on this device."""
        settle(self._writes())

    def write_token(self):
        """A token for the writes left in flight so far on this device (the newest one), for
        settle_until: None when nothing is in flight."""
        pend = self._writes()
        return pend[-1] if pend else None

    def settle_until(self, token):
        """Wait for the writes in flight up to and including token (write_token()), not
        later ones. Each earlier write is waited on too (runs may complete out of order). A
        token already settled is a no-op."""
        pend = self._writes()
        if token is None or all(w is not token for w in pend):
            return
        while pend:
            w = pend.pop(0)
            w.settle()
            if w is token:
                break

    # ---- device zeroing -----------------------------------------------------------------
    def zero_columns(self, dest, a, b):
        """Zero dest[:, a:b] of a device-shared 2-D array on the device. Collected, and run by
        zero_columns_done() as fills behind a barrier, so they land after the correlation
        writes they may overlap. A host memset of a middle stage's complement is ~60 MB a
        call; the device clears it in ~0.3 ms."""
        sb = shared_view(dest, self, align=4)
        if sb is None or dest.ndim != 2 or b <= a or not dest.flags.c_contiguous:
            raise ValueError("zero_columns needs a device-shared 2-D array and a nonempty range")
        offset, nbytes = a * dest.itemsize, (b - a) * dest.itemsize
        if (sb.offset + offset) % 4 or nbytes % 4:
            raise ValueError("zero_columns ranges must be 4-byte aligned")
        self.__dict__.setdefault("_zero_ranges", []).append(
            (sb, dest.ctypes.data, offset, nbytes, dest.shape[0], dest.strides[0]))

    def zero_columns_done(self, wait=True):
        """Run the collected zero_columns ranges, and wait for them, for this context's other
        work and for every write left in flight on the device -- or, wait=False, leave them
        in flight as a pending write (device consumers are ordered after it)."""
        ranges, self._zero_ranges = self.__dict__.get("_zero_ranges") or [], []
        if ranges:
            # A middle stage zeroes the same ranges every segment: the recording is kept,
            # keyed on the bytes it fills (its views hold their allocations, so the
            # addresses stay theirs while it does).
            key = ("zero",) + tuple(r[1:] for r in ranges)
            table = self._exec_table()
            rec = table.get(key)
            if rec is None:
                self._exec_room(0, incoming=[r[0] for r in ranges])
                rec = Record()
                lst = self._x_list("zero")
                lst.barrier()
                for i, (sb, _, offset, nbytes, rows, pitch) in enumerate(ranges):
                    rec.buffers["dest%d" % i] = sb
                    lst.fill(sb, 0, offset=offset, nbytes=nbytes, rows=rows, pitch=pitch)
                lst.barrier()
                rec.native = lst.end()
                table[key] = rec
            self._cache_touch(key)
            self._exec_run(rec.native, wait, None, None, rec)
        if wait:
            self.settle_writes()
            self._x_idle()

    # ---- forward transform --------------------------------------------------------------
    def forward(self, n, series, starts, spectra, *, defer=False, slot=None, fused=False,
                rows=None, real=None, handle_out=None):
        """Gather a block of n samples of `series` at each start (zero past its end) and
        forward-transform it, normalised by 1/n, into a row of `spectra`.

        rows=(r0, count): only rows r0..r0+count of starts and spectra, so several series can
        fill one spectra workspace. real=(lane, stride, length): series is complex64 storage
        holding a real series of `length` samples, sample i at float lane + stride * i (one
        lane of a packed complex row: stride 2; a real series: stride 1); starts and length
        count samples. defer: held for the next work on `slot`, which runs it first; else run
        and waited for. handle_out (a list) receives a handle forward_replay takes. `fused`
        is accepted for the callers that pass it; it does not change the work."""
        two = n > 65536
        if two and (rows is not None or real is not None):
            raise UnsupportedSize("row ranges and real series need the one-stage forward")
        r0, count = rows if rows is not None else (0, spectra.shape[0])
        nser, code = ((int(real[2]), (int(real[0]) << 2) | int(real[1])) if real is not None
                      else (int(series.size), 0))
        sv, pv = shared_view(series, self), shared_view(spectra, self)
        if sv is None or pv is None:
            raise ValueError("forward buffers must belong to this GPU context")
        # Block starts are bound where they lie, unless they lie outside device memory or
        # the device stages host-written inputs: then they are uploaded every call.
        stv = shared_view(starts, self)
        staged = self.stage_host_inputs or stv is None
        if not staged and (r0 * 4) % self.storage_offset_alignment:
            raise ValueError("forward row offsets must be multiples of %d"
                             % (self.storage_offset_alignment // 4))
        if self.stage_host_inputs and count:
            st = starts[r0:r0 + count]
            lo = int(min(int(st.min()), series.size))
            hi = int(min(series.size, int(st.max()) + n))
            if hi > lo:
                self._x_prefetch(sv, lo * series.itemsize, (hi - lo) * series.itemsize, slot)
        # Keyed by slot: a pipelined slot is reused only after its previous work completed,
        # so its staged starts are never rewritten under a run in flight.
        key = ("forward", n, nser, code, r0, count, slot, two, staged)
        table = self._exec_table()
        rec = table.get(key)
        if rec is None:
            self._exec_room(count * n * 8 if two else 0,
                             incoming=[v for v in (sv, stv, pv) if v is not None])
            rec = Record()
            bs = (self._exec_buffer(rec, "starts", nbytes=count * 4, upload=True) if staged
                  else _STARTS)
            soff = 0 if staged else r0 * 4
            lst = self._x_list("forward")
            if two:
                split = self._x_tierc(n)
                scratch = self._exec_buffer(rec, "scratch", nbytes=count * n * 8)
                lst.dispatch(self._x_kernel("tf1", n), count * split[0], [_SERIES, bs, scratch],
                             (int(series.size),), offsets=[0, soff, 0])
                lst.barrier()
                lst.dispatch(self._x_kernel("tf2", n), count * split[1], [scratch, _SPECTRA])
                lst.barrier()
            else:
                lst.stamp("start")
                lst.dispatch(self._x_kernel("forward", n), count, [_SERIES, bs, _SPECTRA],
                             (nser, code), offsets=[0, soff, r0 * n * 8])
                lst.barrier()
                lst.stamp("forward")
            rec.native = lst.end()
            table[key] = rec
        self._cache_touch(key)
        binds = {"series": sv, "spectra": pv}
        if staged:
            # A run of this record still deferred reads the starts about to be rewritten.
            self._exec_run_holding(rec.native)
            self._x_upload(rec.buffers["starts"], starts[r0:r0 + count], slot)
            bst, row = rec.buffers["starts"], 0
        else:
            binds["starts"] = bst = stv
            row = r0
        source = None if two else (n, sv, bst, row, count, nser, code, pv,
                                   spectra.ctypes.data + r0 * n * 8, key)
        if handle_out is not None:
            handle_out.append((key, rec, binds, source))
        if defer:
            self._defer(rec.native, binds, slot, source)
        else:
            self._exec_run(rec.native, True, binds, slot, rec)

    def _forward_fused(self, n, series, starts, spectra, *, defer=False, slot=None):
        return self.forward(n, series, starts, spectra, defer=defer, slot=slot, fused=True)

    def forward_valid(self, h):
        """Whether a forward handle (forward(handle_out=)) still names its cached record."""
        return self._exec_table().get(h[0]) is h[1]

    def forward_replay(self, h, slot):
        """Queue a forward again from its handle; False if its record is gone."""
        if not self.forward_valid(h):
            return False
        self._cache_touch(h[0])
        self._defer(h[1].native, h[2], slot, h[3])
        return True

    # ---- flat peaks ---------------------------------------------------------------------
    def peaks(self, n, data, tmpl, binsize=None, threshold=0.0, window=None, upload_data=True,
              upload_tmpl=True, slot=None, async_submit=False, sparse=False, nbins=None):
        """The peak of every (data row, template) correlation in each bin of the search window.

        Returns (idx, val), each shaped (data rows, templates, bins): the sample index of a
        bin's largest |value| and that complex value, or -1 and 0 where it does not exceed
        `threshold` -- or, sparse=True, a _SparsePeaks of the bins that do. Bins are
        `binsize` samples from the window's start (the last may be short). async_submit:
        returns a callable giving that result, while the work runs (on `slot`)."""
        lo, hi = (0, n) if window is None else (int(window[0]), int(window[1]))
        lo, hi = max(0, min(lo, n)), max(0, min(hi, n))
        if lo >= hi:
            raise ValueError("empty window (%d, %d)" % (lo, hi))
        binsize = n if binsize is None else int(binsize)
        if binsize < 1:
            raise ValueError("binsize must be >= 1")
        nbins = -(-(hi - lo) // binsize) if nbins is None else int(nbins)
        if nbins > MAX_BINS:
            # Bins are contiguous in the window: splitting the window on a bin boundary
            # splits the bins exactly, and the pieces concatenate.
            span = MAX_BINS * binsize
            parts = []
            for a in range(lo, hi, span):
                parts.append(self.peaks(n, data, tmpl, binsize=binsize, threshold=threshold,
                                        window=(a, min(a + span, hi)), upload_data=upload_data,
                                        upload_tmpl=upload_tmpl, slot=slot))
                upload_data = upload_tmpl = False
            res = (np.concatenate([p[0] for p in parts], axis=2),
                   np.concatenate([p[1] for p in parts], axis=2))
            if sparse:
                from ._shared import sparse_from_dense
                res = sparse_from_dense(*res)
            return (lambda: res) if async_submit else res
        return self._flat(n, data, tmpl, ((lo, hi, 0, data.shape[0]),), nbins, binsize,
                          threshold, upload_data, upload_tmpl, slot, async_submit, sparse)

    def peaks_grouped(self, n, data, tmpl, groups, binsize, threshold, *, upload_tmpl=True,
                      slot=None, async_submit=False, sparse=False, nbins=None):
        """peaks over row ranges of one spectra batch, each with its own window, in one
        submission. groups holds (lo, hi, a, b): rows a..b are searched over [lo, hi).
        Every group's result has `nbins` bins (default: the most any group needs); a
        shorter window leaves its last bins empty."""
        nd = data.shape[0]
        binsize = int(binsize)
        groups = tuple((int(lo), int(hi), int(a), int(b)) for lo, hi, a, b in groups)
        for lo, hi, a, b in groups:
            if not (0 <= lo < hi <= n) or not (0 <= a < b <= nd):
                raise ValueError("invalid group (%d, %d, %d, %d)" % (lo, hi, a, b))
        need = max(-(-(hi - lo) // binsize) for lo, hi, _, _ in groups)
        nbins = need if nbins is None else int(nbins)
        if nbins < need:
            raise ValueError("nbins must cover every grouped window's bins")
        if nbins > MAX_BINS:
            raise ValueError("grouped dispatch exceeds the kernel bin limit")
        return self._flat(n, data, tmpl, groups, nbins, binsize, threshold, True, upload_tmpl,
                          slot, async_submit, sparse)

    def _flat(self, n, data, tmpl, groups, nbins, binsize, threshold, upload_data, upload_tmpl,
              slot, async_submit, sparse):
        if not sparse:
            return self._flat_run(n, data, tmpl, groups, nbins, binsize, threshold,
                                  upload_data, upload_tmpl, slot, async_submit, False)
        # A sparse result is gathered on the device (compaction: the host reads the count
        # and the records) or read dense and scanned on the host. Which is cheaper depends on
        # how many bins clear the threshold and on what a byte of readback costs here (a
        # bus, or nothing on unified memory): measured per call shape.
        from . import _choice
        shape = (n, data.shape[0], tmpl.shape[0], nbins, binsize, len(groups))
        way, record = _choice.choice("sparse-way", ("flat",) + shape, SPARSE_WAYS["flat"],
                                     scope=self.__dict__, **_SPARSE_SCHEDULE).next()
        timed = record is not None and not async_submit
        t0 = time.perf_counter()
        res = self._flat_run(n, data, tmpl, groups, nbins, binsize, threshold, upload_data,
                             upload_tmpl, slot, async_submit, way == "compact")
        if way == "dense":
            from ._shared import sparsified
            res = sparsified(res, True)
        if timed:
            record(time.perf_counter() - t0)
        return res

    def _flat_run(self, n, data, tmpl, groups, nbins, binsize, threshold, upload_data,
                  upload_tmpl, slot, async_submit, sparse):
        nd, nt = data.shape[0], tmpl.shape[0]
        shift = (binsize.bit_length() - 1) if binsize & (binsize - 1) == 0 else -1
        t2 = float(threshold) ** 2 if threshold > 0 else 0.0
        t2bits = int(np.float32(t2).view(np.uint32))
        # A result in flight owns its slot's buffers; a waited call shares one record across
        # slots, but still runs on its slot (after the work deferred there).
        kslot = slot if async_submit else None
        rows = tuple((a, b) for _, _, a, b in groups)
        # Each group's results start at its rows' place in (rows, templates, bins) where that
        # offset is a bound view's alignment; else every group is packed, aligned, and the
        # host gathers the rows.
        unit = max(1, self.storage_offset_alignment // 4)
        natural = all((a * nt * nbins) % unit == 0 for a, _ in rows)
        if natural:
            offsets, size = [a * nt * nbins for a, _ in rows], nd * nt * nbins
        else:
            offsets, size = [], 0
            for a, b in rows:
                offsets.append(size)
                size += -(-((b - a) * nt * nbins) // unit) * unit
        covered = np.zeros(nd, bool)
        for a, b in rows:
            covered[a:b] = True
        dv, tv = shared_view(data, self), shared_view(tmpl, self)
        key = ("flat", n, nd, nt, nbins, rows, kslot, sparse, dv is not None and data.ctypes.data,
               tv is not None and tmpl.ctypes.data)
        uploads = self._input_uploads(key, data, tmpl, upload_data, upload_tmpl)
        table = self._exec_table()
        rec = table.get(key)
        if rec is None:
            estimate = (sum(a.nbytes for a, v in ((data, dv), (tmpl, tv)) if v is None)
                        + size * (28 if sparse else 12) + 16)
            self._exec_room(estimate, incoming=[v for v in (dv, tv) if v is not None])
            rec = Record()
            bd = self._exec_buffer(rec, "data", dv, data.nbytes)
            bt = self._exec_buffer(rec, "tmpl", tv, tmpl.nbytes)
            bi = self._exec_buffer(rec, "idx", nbytes=size * 4, readback=True)
            bv = self._exec_buffer(rec, "val", nbytes=size * 8, readback=True)
            lst = self._x_list("flat")
            if sparse:
                cnt = self._exec_buffer(rec, "count", nbytes=16, readback=True)
                out = self._exec_buffer(rec, "list", nbytes=size * 16, readback=True)
                lst.fill(cnt, 0)
            if not natural or not covered.all():
                lst.fill(bi, 0xFFFFFFFF)          # bins no dispatch writes: empty
                lst.fill(bv, 0)
            lst.barrier()
            kernel = self._x_kernel("peaks1" if nbins == 1 else "peaks", n)
            for g, ((a, b), off) in enumerate(zip(rows, offsets)):
                lst.dispatch(kernel, (b - a) * nt, [bd, bt, bi, bv], (Arg("w%d" % g, 7),),
                             offsets=[a * n * 8, 0, off * 4, off * 8])
            lst.barrier()
            if sparse:
                # The bins that cleared the threshold, gathered on the device: the host
                # reads the count and those records, not the dense table.
                lst.dispatch(self._x_kernel("compact_peaks", n), (size + 255) // 256,
                             [bi, bv, cnt, out], (size, size))
                lst.barrier()
                lst.readback(cnt, 4)
                lst.readback(out, min(size, self._SPARSE_FIRST) * 16)
            else:
                lst.readback(bi, size * 4)
                lst.readback(bv, size * 8)
            rec.native = lst.end()
            table[key] = rec
            uploads = (True, True, *uploads[2:])
        self._cache_touch(key)
        self._claim(rec.buffers["idx"])          # an earlier result still reading these
        self._exec_upload(rec, key, uploads, data, tmpl, slot)
        binds = {"w%d" % g: (nt, lo, hi, binsize, shift & 0xFFFFFFFF, nbins, t2bits)
                 for g, (lo, hi, _, _) in enumerate(groups)}
        wait = self._exec_submit(rec.native, binds, slot, rec) if async_submit else None
        if wait is None:
            self._exec_run(rec.native, True, binds, slot, rec)
        shape = (nd, nt, nbins)

        def result():
            if wait is not None:
                wait()
            if sparse:
                return self._flat_sparse(rec, shape, rows, offsets, natural)
            return self._flat_dense(rec, shape, rows, offsets, natural, size)
        return self._track(result, owner=rec.buffers["idx"]) if async_submit else result()

    def _flat_dense(self, rec, shape, rows, offsets, natural, size):
        nd, nt, nb = shape
        idx = np.empty(size, np.int32)
        val = np.empty(size, np.complex64)
        self._x_read(rec.buffers["idx"], idx)
        self._x_read(rec.buffers["val"], val)
        if natural:
            return idx.reshape(shape), val.reshape(shape)
        oi = np.full(shape, -1, np.int32)
        ov = np.zeros(shape, np.complex64)
        for (a, b), off in zip(rows, offsets):
            count = (b - a) * nt * nb
            oi[a:b] = idx[off:off + count].reshape(b - a, nt, nb)
            ov[a:b] = val[off:off + count].reshape(b - a, nt, nb)
        return oi, ov

    def _flat_sparse(self, rec, shape, rows, offsets, natural):
        from ._results import _SparsePeaks
        nd, nt, nb = shape
        head = np.empty(1, np.uint32)
        self._x_read(rec.buffers["count"], head)
        c = int(head[0])
        recs = np.empty((c, 4), np.uint32)
        self._x_read(rec.buffers["list"], recs)
        # Atomics fill the list in no fixed order. Positions are unique, so they are put in
        # order through a table of positions (linear) rather than sorted (c log c compares:
        # ~2 ms at 24k records).
        pos = recs[:, 0].astype(np.int64)
        if not natural:                           # packed groups: back to row positions
            starts = np.asarray(offsets, np.int64)
            g = np.searchsorted(starts, pos, side="right") - 1
            first = np.asarray([a for a, _ in rows], np.int64) * nt * nb
            pos = pos - starts[g] + first[g]
        where = np.full(nd * nt * nb, -1, np.int32)
        where[pos] = np.arange(c, dtype=np.int32)
        order = where[where >= 0]
        flat, recs = pos[order], recs[order]
        val = recs[:, 2:4].copy().view(np.float32).view(np.complex64).reshape(-1)
        return _SparsePeaks(shape, flat, recs[:, 1].view(np.int32), val)

    # ---- follow-up items ----------------------------------------------------------------

    def peaks_items(self, n, data, tmpl, items, binsize, threshold, *, async_submit=False):
        """One submission over follow-up items (lo, hi, a, b, t): rows a:b of data against
        template row t, searched over [lo, hi) in bins of binsize. Returns per item (idx, val)
        shaped (b - a, 1, nbins), or with async_submit a callable giving that list. Data and
        templates are device allocations, bound in place at each item's rows: nothing is
        copied, and the outputs come back in one read."""
        dv, tv = shared_view(data, self), shared_view(tmpl, self)
        if dv is None or tv is None:
            raise ValueError("item spectra and templates must be shared allocations")
        binsize = int(binsize)
        shift = bin_shift(binsize) & 0xFFFFFFFF
        t2bits = int(np.float32(float(threshold) ** 2 if threshold > 0 else 0).view(np.uint32))
        offs, nbs, size = plan_items(items, binsize, max(1, self.storage_offset_alignment // 4),
                                     MAX_BINS)
        # Outputs per DEVICE: follow-ups run on a single-template plan per bank, each its own
        # context, and outputs per context meant an allocation on nearly every call. One
        # result may be pending: its outputs are about to be reused.
        holder = getattr(self, "_device_state", None) or self
        prior = holder.__dict__.pop("items_inflight", None)
        if prior is not None:
            prior()
        out = holder.__dict__.get("items_out")
        if out is None or out[0].nbytes < max(size, 1) * 4:
            cap = max(size, 1, 2 * (out[0].nbytes // 4 if out else 0))
            if out is not None:
                for b in out:
                    b.destroy()
            out = holder.items_out = (self._x_alloc(cap * 4, readback=True),
                                      self._x_alloc(cap * 8, readback=True))
        bi, bv = out
        lst = self._x_list("items", once=True)
        for (lo, hi, a, b, t), off, nb in zip(items, offs, nbs):
            if b <= a:
                continue
            lst.dispatch(self._x_kernel("peaks1" if nb == 1 else "peaks", n), b - a,
                         [dv, tv, bi, bv], (1, lo, hi, binsize, shift, nb, t2bits),
                         offsets=[a * n * 8, t * n * 8, off * 4, off * 8])
        lst.barrier()
        lst.readback(bi, size * 4)
        lst.readback(bv, size * 8)
        native = lst.end()
        wait = self._x_submit(native, {}, None, pre=self._take_items())

        def result():
            wait()
            idx = np.empty(size, np.int32)
            val = np.empty(size, np.complex64)
            self._x_read(bi, idx)
            self._x_read(bv, val)
            self._x_release(native, done=True)
            return split_items(items, offs, nbs, idx, val)
        if not async_submit:
            return result()
        pending = self._track(result)
        holder.items_inflight = pending
        return pending

    # ---- device follow-ups --------------------------------------------------------------
    def submit_followups(self, jobs):
        """A collector giving the FilterResults of single-template follow-up jobs [(bank,
        series, kwargs)] (_gpuhost.followup_layout), submitted without waiting. Per group:
        a forward of its rows from its series allocation, then refineItems over its entries
        -- both listed over the row count, so a group's record (per shape and place in the
        batch) is replayed whatever its rows; its tables are uploaded per run, its series,
        templates and words bound per run. Every group goes in one submission. Raises
        FollowupUnsupported when the jobs cannot all run here."""
        # One context per device owns the follow-up records: every single-template plan is
        # its own context, and records per context were rebuilt whenever a batch's first job
        # moved to another template group. The owner passes on when it is destroyed.
        holder = getattr(self, "_device_state", None) or self
        ref = holder.__dict__.get("followup_owner")
        owner = ref() if ref is not None else None
        if owner is None:
            owner = self
            holder.followup_owner = weakref.ref(self)
        return owner._submit_followups(jobs, holder)

    def _submit_followups(self, jobs, holder):
        from ._gpuhost import FollowupUnsupported, assemble_followups, followup_layout
        groups, layout = followup_layout(jobs, self)
        if not groups:
            return lambda: []
        prior = holder.__dict__.pop("followups_inflight", None)
        if prior is not None:
            prior()                       # its records' tables and outputs are rewritten below
        runs, places = [], {}
        for gw in groups:
            n, nbins, m = gw["n"], gw["nbins"], int(gw["rows"].size)
            tv, sv = shared_view(gw["plan"]._gtmpl, self), shared_view(gw["alloc"], self)
            if tv is None or sv is None or not self._x_has_kernel("items", n) or n > 65536:
                raise FollowupUnsupported("templates or series outside this device's reach, "
                                          "or no refineItems build for n=%d" % n)
            cap = 1 << max(6, (max(m, 1) - 1).bit_length())
            shape = (n, nbins, cap)
            place = places[shape] = places.get(shape, -1) + 1
            rec, offs = self._followup_record(("followups",) + shape + (place,), n, nbins, cap)
            tab = np.zeros(offs[-1] // 4, np.uint32)
            tab[offs[0] // 4:offs[0] // 4 + m] = gw["rows"]
            tab[offs[1] // 4:offs[1] // 4 + 5 * m] = gw["entries"].ravel()
            tab[offs[2] // 4:offs[2] // 4 + cap] = np.arange(cap, dtype=np.uint32)
            tab[offs[3] // 4:offs[3] // 4 + 3] = (m, 1, 1)
            self._x_upload(rec.buffers["tab"], tab, None)
            bs = gw["bs"]
            binds = {"series": sv, "tmpl": tv, "fwd": (gw["nser"], gw["code"]),
                     "items": (int(gw["plan"]._gtmpl.shape[0]), bs,
                               bin_shift(bs) & 0xFFFFFFFF, nbins, 0)}
            runs.append((rec, binds, gw))
        reads = set()
        for rec, binds, _ in runs:
            reads |= self._reads(rec, binds)
        *first, (rec, binds, _) = runs
        wait = self._x_submit(rec.native, binds, None,
                              pre=list(self._take(None, reads))
                              + [(r.native, b) for r, b, _ in first])
        done = []

        def read(gw):
            m, nbins = gw["rows"].size, gw["nbins"]
            r = gw["_rec"]
            return (np.array(self._x_view(r.buffers["idx"], np.int32, m * nbins)).reshape(m, nbins),
                    np.array(self._x_view(r.buffers["val"], np.complex64, m * nbins))
                    .reshape(m, nbins))

        def collect():
            """Wait for the submission and assemble every job's results (once)."""
            if not done:
                try:
                    wait()
                finally:
                    if holder.__dict__.get("followups_inflight") is collect:
                        holder.followups_inflight = None
                for r, _, gw in runs:
                    gw["_rec"] = r
                done.append(assemble_followups(layout, read))
            return done[0]
        holder.followups_inflight = collect
        return collect

    def _retire(self):
        """This context is being destroyed (a driver's destroy): the device's follow-ups
        finish, and their ownership passes to the next context that runs them."""
        holder = getattr(self, "_device_state", None) or self
        ref = holder.__dict__.get("followup_owner")
        if ref is not None and ref() is self:
            prior = holder.__dict__.pop("followups_inflight", None)
            if prior is not None:
                prior()
            del holder.followup_owner

    def _followup_record(self, key, n, nbins, cap):
        """(record, table offsets) of a follow-up group (submit_followups): its tables --
        rows, entries, the identity list the listed forward walks, and the row count as
        indirect arguments -- share one upload buffer."""
        align = max(16, int(self.storage_offset_alignment))
        offs, at = [], 0
        for nbytes in (4 * cap, 20 * cap, 4 * cap, 16):
            offs.append(at)
            at = -(-(at + nbytes) // align) * align
        offs.append(at)
        table = self._exec_table()
        rec = table.get(key)
        if rec is None:
            self._exec_room(cap * n * 8 + cap * nbins * 12 + align)
            rec = Record()
            tab = self._exec_buffer(rec, "tab", nbytes=at, upload=True)
            spec = self._exec_buffer(rec, "spec", nbytes=cap * n * 8)
            # Peak values, then indices, in one buffer: one readback.
            vbytes = -(-cap * nbins * 8 // align) * align
            out = self._exec_buffer(rec, "out", nbytes=vbytes + cap * nbins * 4, readback=True)
            bv = rec.buffers["val"] = self._x_section(out, 0, cap * nbins * 8)
            bi = rec.buffers["idx"] = self._x_section(out, vbytes, cap * nbins * 4)
            rows, ent, ids, args = (self._x_section(tab, o, b) for o, b in
                                    zip(offs, (4 * cap, 20 * cap, 4 * cap, 16)))
            lst = self._x_list("followups")
            lst.barrier()                 # after writes in flight to the series (a middle stage)
            lst.listed(self._x_kernel("fwd_listed", n), args, cap,
                       [Arg("series"), rows, spec, ids, args], (Arg("fwd", 2),))
            lst.barrier()
            lst.listed(self._x_kernel("items", n), args, cap,
                       [spec, Arg("tmpl"), bi, bv, ent, args], (Arg("items", 5),))
            lst.barrier()
            lst.readback(out, vbytes + cap * nbins * 4)
            rec.native = lst.end()
            table[key] = rec
        self._cache_touch(key)
        return rec, offs

    # ---- grouped hierarchical calls -----------------------------------------------------
    def hier_peaks_grouped(self, n, band, data, tmpl, ct0, raw_thr, groups, binsize,
                           threshold, *, upload_tmpl=True, cascade_band=None, ct1=None,
                           raw_thr1=None, slot=None, async_submit=False, sparse=False,
                           nbins=None, handle_out=None, refine_reach=None):
        """Hierarchical peaks over row ranges of one spectra batch, each with its own window:
        one recording, every tier one dispatch over all rows, each row's window read from a
        table on the device (_gpuhost.hier_peaks_grouped). groups holds (lo, hi, a, b): rows
        a..b searched over [lo, hi). Output bins follow the first group's bin count (or
        nbins)."""
        from ._gpuhost import hier_peaks_grouped
        return hier_peaks_grouped(self, n, band, data, tmpl, ct0, raw_thr, groups, binsize,
                                  threshold, upload_tmpl=upload_tmpl, cascade_band=cascade_band,
                                  ct1=ct1, raw_thr1=raw_thr1, slot=slot,
                                  async_submit=async_submit, sparse=sparse, nbins=nbins,
                                  max_bins=MAX_BINS, handle_out=handle_out,
                                  refine_reach=refine_reach)
