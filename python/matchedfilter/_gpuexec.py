"""GPU operations written once, over a thin per-API driver (stage U, docs/unification-plan.md).

A backend Context (Vulkan, CUDA, Metal) inherits Executor and supplies only driver
primitives -- how to allocate, record, submit and read back on its API. Every decision an
operation makes uses what the driver reports about the hardware, never which API it is, so
a change made here reaches every GPU at once.

Driver primitives (a Context provides each):

  _x_kernel(name, n)        the compiled kernel `name` at transform length n, or raise
                            UnsupportedSize: an opaque handle the context's command lists take.
                            Names: "full" (fullCorrelation), "tc1"/"tc2" (the two stages of
                            the two-stage full correlation).
  _x_tierc(n)               (n1, n2): the two-stage transform's split at n (UnsupportedSize
                            if there is none).
  _x_alloc(nbytes, readback=False)
                            a device buffer the context owns (write(array), read_into(out),
                            destroy(), nbytes). readback: the host reads it.
  _x_list(label)            a command list being recorded:
                              dispatch(kernel, groups, buffers, words=(), offsets=None)
                                buffers are bound in order; words are the kernel's uniform
                                parameters, as uint32 (a float or signed value as its bits);
                              barrier()      later work sees earlier writes;
                              end()          -> (native, resources): what _x_run submits,
                                             and what _x_release frees.
  _x_run(native, wait)      submit a recorded list; wait=False leaves it in flight as a
                            pending write (device work is ordered after it, a host reader
                            waits through settle_writes).
  _x_release(native, resources)
                            free a recording (after its work has finished).
  _x_read(buf, out)         copy a device buffer into a host array (synchronously).

Features a driver reports (attributes): max_dispatch_x (the most groups one dispatch takes),
storage_offset_alignment (a bound buffer's offset must be a multiple of this).
"""
import numpy as np

from ._errors import UnsupportedSize
from ._shared import shared_view


class Record:
    """A cached recording of one operation shape: the buffers it binds (`owned` are the
    context's, freed with it; the rest are callers' shared allocations) and the driver's
    native recording and resources."""
    __slots__ = ("buffers", "owned", "native", "resources")

    def __init__(self):
        self.buffers, self.owned, self.native, self.resources = {}, set(), None, None


class Executor:
    """The operations every GPU backend runs, written once. See the module docstring for
    the driver primitives a backend supplies."""

    #: Working bytes one full-correlation dispatch may take before it is tiled.
    _FULL_BUDGET = 64 * 1024 * 1024
    #: correlate takes wait=False on every backend (CorrelationFilter.run(wait=False)).
    async_correlate = True

    # ---- records ------------------------------------------------------------------------
    def _exec_table(self):
        table = self.__dict__.get("_exec_records")
        if table is None:
            table = self._exec_records = {}
        return table

    def _exec_buffer(self, rec, name, view=None, nbytes=0, readback=False):
        """Bind `view` -- an array's place in device memory (a caller's shared allocation, or
        a view into one at an allowed offset; shared_view) -- or, without one, a buffer of the
        context's own of nbytes."""
        buf = view
        if buf is None:
            buf = self._x_alloc(nbytes, readback=readback)
            rec.owned.add(name)
        rec.buffers[name] = buf
        return buf

    def _exec_evict(self, key):
        """Drop one executor record: its in-flight results are collected first, then the
        driver frees its recording and the buffers it owns."""
        self._drain()
        rec = self._exec_table().pop(key, None)
        if rec is None:
            return
        self._x_release(rec.native, rec.resources)
        for name in rec.owned:
            rec.buffers[name].destroy()
        for resident in self._uploaded.values():
            resident.pop(key, None)

    def _exec_clear(self):
        """Evict every executor record (clear_cache)."""
        for key in list(self._exec_table()):
            self._exec_evict(key)

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
        tierc = n > 65536
        split = self._x_tierc(n) if tierc else None
        groups = max(split) if tierc else 1
        ov = shared_view(out, self)
        direct = ov is not None
        working = nd * nt * 8 * n * ((1 if direct else 2) if tierc else (0 if direct else 1))
        if working <= self._FULL_BUDGET and nd * nt * groups <= self.max_dispatch_x:
            self._correlate_tile(n, data, tmpl, out, upload_data, upload_tmpl, split,
                                 wait or not direct, ov)
            return out
        per_pair = 8 * n * (2 if tierc else 1)
        tile = min(nt, max(1, self._FULL_BUDGET // per_pair),
                   max(1, self.max_dispatch_x // groups))
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
            self._cache_room(estimate, incoming=views)
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
            rec.native, rec.resources = lst.end()
            table[key] = rec
            uploads = (True, True, *uploads[2:])
        self._cache_touch("exec", key)
        if (uploads[0] and "data" in rec.owned) or (uploads[1] and "tmpl" in rec.owned):
            self.settle_writes()       # a call left in flight may still read these inputs
        self._write_uploads(key, uploads, rec.buffers["data"], data, rec.buffers["tmpl"], tmpl)
        self._x_run(rec.native, wait)
        if "out" in rec.owned:
            self._x_read(rec.buffers["out"], out)
