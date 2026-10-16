"""CUDA result lifetime without a device: real dispatch/cache/readback code, host-backed
allocations whose reads fail after destroy. Completing a device copy does not make its
pinned result safe to free while an async collector still needs it."""
import ctypes
from types import SimpleNamespace

import numpy as np
import pytest

from matchedfilter import _cudacompute as cc


class _Buffer(cc._Buffer):
    def __init__(self, ctx, nbytes):
        self.ctx, self.nbytes = ctx, int(nbytes)
        self._raw = ctypes.create_string_buffer(max(self.nbytes, 1))
        self.ptr = self.handle = ctypes.addressof(self._raw)
        self.dptr = ctypes.c_uint64(self.ptr)
        self.alive = True

    def write(self, array, stream=None):
        assert self.alive

    def destroy(self):
        self.alive = False
        self.ptr = self.handle = 0
        self.dptr.value = 0


class _Pinned(cc._Pinned):
    def __init__(self, ctx, nbytes):
        self.ctx, self.nbytes = ctx, int(nbytes)
        self._raw = ctypes.create_string_buffer(max(self.nbytes, 1))
        self.ptr = self.handle = ctypes.addressof(self._raw)
        self.alive = True

    def view(self, *args, **kwargs):
        assert self.alive, "read of freed pinned result"
        return super().view(*args, **kwargs)

    def destroy(self):
        self.alive = False
        self.ptr = self.handle = 0


@pytest.fixture
def ctx(monkeypatch):
    monkeypatch.setattr(cc, "_Buffer", _Buffer)
    monkeypatch.setattr(cc, "_Pinned", _Pinned)
    c = object.__new__(cc.Context)
    c.ctx = ctypes.c_void_p()                 # no driver calls in the destructor
    c.dev_idx = 0
    c.cuda = SimpleNamespace(cuCtxSynchronize=lambda: 0)
    c._bind = lambda: None
    c._sync = lambda stream=None: None
    c.get_stream = lambda slot=None: ctypes.c_void_p(1)
    c._after_forwards = lambda stream: None
    c.pipeline = lambda *a, **kw: (None, 1)
    c._uploaded = {"data": {}, "tmpl": {}}
    c._residents = {}
    c._batches = {}
    c.last_refinements = c.last_tier1_survivors = 0
    c._copy_d2h = lambda dst, src, size, *a: ctypes.memmove(dst, src, size)
    launches = []

    def launch(fn, pairs, wg, params, **kwargs):
        # Distinct output per dispatch; these tests concern lifetime, not the FFT.
        launches.append(None)
        count = pairs * params[9].value
        idx = np.ctypeslib.as_array((ctypes.c_int32 * count).from_address(params[2].value))
        val = np.ctypeslib.as_array((ctypes.c_float * (2 * count)).from_address(params[3].value))
        idx[:] = len(launches)
        val.view(np.complex64)[:] = complex(len(launches), -len(launches))

    c._launch = launch
    yield c
    c.clear_cache()


def _submit(ctx, rows=1, slot=0, grouped=False):
    data = np.zeros((rows, 1024), np.complex64)
    if grouped:
        return ctx.peaks_grouped(1024, data, data[:1], [(0, 1024, 0, rows)],
                                 1024, 0.0, slot=slot, async_submit=True)
    return ctx.peaks(1024, data, data[:1], slot=slot, async_submit=True)


@pytest.mark.parametrize("grouped", [False, True])
@pytest.mark.parametrize("release", ["evict", "clear"])
def test_result_survives_pinned_buffer_release(ctx, grouped, release):
    ctx.cache_limit_bytes = 1                 # next slot evicts this dispatch
    first = _submit(ctx, grouped=grouped)
    host = next(iter(ctx._batches.values()))["host"]
    if release == "evict":
        second = _submit(ctx, slot=1, grouped=grouped)
        assert second()[0].item() == 2
    else:
        ctx.clear_cache()
    assert not host.alive
    idx, val = first()
    assert idx.item() == 1 and val.item() == 1 - 1j
    assert first()[0] is idx                    # materialized once, including early drain
    assert not ctx._inflight and not ctx._pending_records


@pytest.mark.parametrize("rows", [1, 2])
def test_reusing_or_growing_a_record_keeps_its_pending_result(ctx, rows):
    first = _submit(ctx)
    second = _submit(ctx, rows=rows)
    assert first()[0].tolist() == [[[1]]]
    assert (second()[0] == 2).all()


def test_early_collection_preserves_stats(ctx):
    rec = {}
    current = [7, 3]

    def readback(sort=True):
        ctx.last_refinements, ctx.last_tier1_survivors = current
        return current[0]

    readback.sparse_dev = (100, 200)
    result = ctx._dispatch_result(rec, readback, True)
    ctx._drain()
    current[:] = [2, 1]
    assert result.sparse_dev == (100, 200)
    assert result() == 7                       # original result keeps its own counters
    assert (ctx.last_refinements, ctx.last_tier1_survivors) == (7, 3)


@pytest.mark.parametrize("count", [2, 8])
def test_sparse_readback_and_hierarchical_counts_survive_eviction(ctx, monkeypatch, count):
    monkeypatch.setattr(cc, "_SPARSE_HOST", 4)     # eight peaks need a second readback
    rec = {"idx": _Buffer(ctx, 32), "val": _Buffer(ctx, 64)}
    ctx._batches["sparse"] = rec
    collect = ctx._tail(rec, 8, (2, 2, 2), None, True, ncounts=2, enqueue=False)
    hp = rec["sp_host"]
    hp.view(np.uint32, 1)[0] = count
    hp.view(np.uint32, 2, offset=16)[:] = [5, 7]
    records = np.arange(count * 4, dtype=np.uint32).reshape(count, 4)
    records[:, 0] = np.arange(count)
    records[:, 1] = 42
    records[:, 2:4] = np.asarray([3, 4], np.float32).view(np.uint32)
    ctypes.memmove(rec["sp_list"].ptr, records.ctypes.data, records.nbytes)
    ctypes.memmove(hp.ptr + 32, records.ctypes.data, min(count, 4) * 16)

    def readback():
        result, counts = collect()
        ctx.last_refinements, ctx.last_tier1_survivors = map(int, counts)
        return result

    result = ctx._dispatch_result(rec, readback, True)
    ctx._evict_record("flat", "sparse")
    assert not hp.alive
    ctx.last_refinements = ctx.last_tier1_survivors = 0
    indices, values = result().dense()
    assert (indices.reshape(-1)[:count] == 42).all()
    assert (values.reshape(-1)[:count] == 3 + 4j).all()
    assert (ctx.last_refinements, ctx.last_tier1_survivors) == (5, 7)


