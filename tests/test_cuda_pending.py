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


def test_early_collection_preserves_stats_and_replay_reader(ctx):
    rec = {}
    current = [7, 3]

    def readback(sort=True):
        ctx.last_refinements, ctx.last_tier1_survivors = current
        return current[0]

    readback.sparse_dev = (100, 200)
    result = ctx._dispatch_result(rec, readback, True)
    replay = ctx._last_dispatch
    ctx._drain()
    current[:] = [2, 1]
    assert replay(sort=False) == 2             # a graph replay must read new output
    assert replay.sparse_dev == (100, 200)
    assert result.sparse_dev == (100, 200)
    assert result() == 7                       # original result keeps its own counters
    assert (ctx.last_refinements, ctx.last_tier1_survivors) == (7, 3)


def test_capture_does_not_drain_work_that_has_not_executed(ctx, monkeypatch):
    monkeypatch.setattr(cc, "_SEG", {})
    calls = []
    reader = lambda: calls.append(1)
    result = ctx._dispatch_result({}, reader, True)
    ctx._drain()
    assert calls == [] and result is reader and ctx._last_dispatch is reader


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


def test_capture_materializes_earlier_results_from_other_contexts(ctx):
    result = _submit(ctx)
    # The graph's entry context need not be the one holding the earlier result.
    def begin(*args):
        assert result.done and not ctx._inflight
        raise RuntimeError("capture reached")

    entry = SimpleNamespace(dev_idx=ctx.dev_idx, _bind=lambda: None,
                            settle_writes=lambda: None,
                            cuda=SimpleNamespace(cuCtxSynchronize=lambda: 0,
                                                 cuStreamBeginCapture_v2=begin))
    graph = object.__new__(cc.SegmentGraph)
    graph.ctx, graph.cuda, graph.streams, graph.exec = entry, entry.cuda, [None], None
    with pytest.raises(RuntimeError, match="capture reached"):
        graph.capture(lambda: None)
    assert result()[0].item() == 1


@pytest.fixture
def segment(ctx, monkeypatch):
    """A traced SegmentPlan using real readers/cache/graph ownership, with fake launches."""
    from matchedfilter.time_domain import SegmentPlan
    monkeypatch.setattr(cc, "_SEG", {})
    reader = _submit(ctx)
    records = tuple(cc._SEG["records"].values())
    monkeypatch.setattr(cc, "_SEG", None)
    host = next(iter(ctx._batches.values()))["host"]
    monkeypatch.setattr(cc, "_SEG_LAST", [None])
    monkeypatch.setattr(cc, "_SEG_INFLIGHT", set())
    monkeypatch.setattr(cc, "_SEG_RESULTS", set())
    monkeypatch.setattr(cc, "_SEG_TIMING", False)
    ctx._after_writes = lambda stream: None
    ctx._new_event = lambda: ctypes.c_void_p(2)
    launches = []

    def launch(*args):
        launches.append(None)
        host.view(np.int32, 1)[0] = len(launches)
        host.view(np.complex64, 1, offset=4)[0] = complex(len(launches), -len(launches))
        return 0

    ctx.cuda.cuGraphLaunch = launch
    ctx.cuda.cuEventRecord = ctx.cuda.cuEventSynchronize = lambda *a: 0
    ctx.cuda.cuStreamWaitEvent = ctx.cuda.cuGraphExecDestroy = lambda *a: 0
    graph = object.__new__(cc.SegmentGraph)
    graph.ctx, graph.cuda, graph.streams = ctx, ctx.cuda, [ctypes.c_void_p(1)]
    graph.exec, graph.stale, graph.prefetch = ctypes.c_void_p(1), False, []
    graph.records, graph.ptrs = records, (host.ptr,)
    cc._SEG_LIVE.add(graph)
    dispatch = SimpleNamespace(trace={"shape": (1, 1, 1), "order": None,
                                      "groups": [(0, 1, reader)]})
    group = SimpleNamespace(template_indices=np.array([0]))
    plan = SegmentPlan()
    plan._cuda_context = lambda jobs: ctx
    plan._signature = lambda jobs: ()
    plan._graph = graph
    plan._trace = {"sig": ((), None, None),
                   "jobs": [([(dispatch, np.array([0]), group, None, 1024)], None)]}
    monkeypatch.setenv("MF_CUDA_SEGMENT_GRAPH", "1")
    yield plan, graph, host
    graph.release()


@pytest.mark.parametrize("change", ["clear", "evict", "reuse", "relaunch", "release",
                                    "free", "wait_then_clear", "other_graph"])
def test_segment_submission_survives_record_lifetime_changes(ctx, segment, change):
    plan, graph, host = segment
    first = plan.submit([])
    if change == "clear":
        ctx.clear_cache()
    elif change == "evict":
        ctx._evict_record("flat", next(iter(ctx._batches)))
    elif change == "reuse":
        _submit(ctx)
    elif change == "relaunch":
        second = plan.submit([])
        assert second.result()[0].sample_indices.tolist() == [2]
    elif change == "release":
        graph.release()
    elif change == "free":
        cc._seg_freed(host.ptr, host.nbytes)
        host.destroy()
    elif change == "wait_then_clear":
        graph.wait()                         # device completion alone must retain the owner
        ctx.clear_cache()
    else:
        other = object.__new__(cc.SegmentGraph)
        other.__dict__.update({k: v for k, v in graph.__dict__.items() if k != "_result"})
        assert other.launch()                # distinct graph, the same output records
        other.release()
    out = first.result()[0]
    assert out.sample_indices.tolist() == [1]
    assert out.snr.tolist() == [1 - 1j]
    assert first.result()[0] is out
    assert not cc._SEG_RESULTS and not ctx._segment_results


def test_segment_result_releases_ownership_when_collected(segment, ctx):
    plan, graph, _ = segment
    first = plan.submit([])
    assert first.result()[0].sample_indices.tolist() == [1]
    assert not cc._SEG_RESULTS and not ctx._segment_results
    second = plan.submit([])
    assert second.result()[0].sample_indices.tolist() == [2]
    assert first.result()[0].sample_indices.tolist() == [1]


def test_segment_replay_preserves_an_ordinary_pending_dispatch(segment, ctx):
    plan, _, _ = segment
    ordinary = _submit(ctx)                  # same record, ordinary dispatch writes 2
    replay = plan.submit([])                 # first graph launch writes 1
    assert ordinary()[0].item() == 2
    assert replay.result()[0].sample_indices.tolist() == [1]


def test_segment_rechecks_validity_after_collecting_shared_records(segment, ctx):
    _, graph, _ = segment
    calls = []

    def finish():
        calls.append(None)
        graph.stale = True

    token = graph.records[0][1]
    ctx.__dict__.setdefault("_pending_records", {})[token] = finish
    assert not graph.launch()
    assert calls == [None]
    ctx._pending_records.pop(token)


def test_record_rechecks_cache_after_collecting_a_segment(segment, ctx):
    from matchedfilter.time_domain import _SegmentResult
    _, graph, host = segment
    # A replay collector can run host follow-ups which evict the record being requested.
    graph.track_result(_SegmentResult(ctx.clear_cache))
    result = _submit(ctx)
    assert not host.alive
    assert result()[0].item() == 2
