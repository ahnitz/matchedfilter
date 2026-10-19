"""An asynchronous result's own statistics survive early collection, on every backend.

Pending (_gpu_cache) materialises a result once, possibly early -- a drain from timings(), a
cache eviction, a slot reuse -- and in any order. The statistics a collection leaves on the
context (last_refinements, last_tier1_survivors) must be each result's own whenever its
caller reads it: read stale, a deferred hierarchical call counted 0 refinements and marked
itself empty. (Result lifetime under eviction, clear and reuse: tests/test_gpu_flat_results.py
and test_gpu_hier_plan.py.) Deferred work (_gpuexec._pending) runs with the next work on its
slot, in order, and is never restaged under itself."""
import numpy as np
import pytest

from matchedfilter._gpu_cache import InputUploads


class _Ctx(InputUploads):
    last_refinements = last_tier1_survivors = 0


def test_early_collection_preserves_stats():
    ctx = _Ctx()
    current = [7, 3]

    def readback():
        ctx.last_refinements, ctx.last_tier1_survivors = current
        return current[0]

    result = ctx._track(readback)
    ctx._drain()                                 # collected early, e.g. by an eviction
    current[:] = [2, 1]
    ctx.last_refinements, ctx.last_tier1_survivors = current
    assert result() == 7                         # the original result keeps its own counters
    assert (ctx.last_refinements, ctx.last_tier1_survivors) == (7, 3)


def test_a_result_reading_reused_outputs_is_collected_first():
    """_claim: a call about to reuse a result's output buffers collects that result first."""
    ctx = _Ctx()
    owner = object()
    seen = []
    result = ctx._track(lambda: seen.append("first") or "first", owner=owner)
    ctx._claim(owner)
    assert seen == ["first"]
    assert result() == "first" and seen == ["first"]      # materialised once


def test_a_staged_forward_deferred_twice_runs_the_first_before_restaging():
    """A deferred forward runs with the next work on its slot, after its starts were
    uploaded. Deferring the same recording again before then would rewrite those starts
    under it: the first run is made (and waited for) before the second is staged."""
    import matchedfilter as mf
    from conftest import usable_gpu
    device = usable_gpu()
    if device is None:
        pytest.skip("requires a GPU")
    plan = mf.MatchedFilter(1024, ndata=2, ntemplates=1, device=device)
    ctx = plan._gpu
    rng = np.random.default_rng(3)
    series = plan.empty_shared((8 * 1024,))
    series[:] = (rng.standard_normal(series.shape)
                 + 1j * rng.standard_normal(series.shape)).astype(np.complex64)
    spec = [plan.empty_shared((2, 1024)) for _ in range(2)]
    starts = [np.array([0, 1024], np.uint32), np.array([3000, 5000], np.uint32)]
    staged = ctx.stage_host_inputs
    ctx.stage_host_inputs = True                 # every backend stages the starts here
    try:
        for s, st in zip(spec, starts):
            ctx.forward(1024, series, st, s, defer=True, slot=0)
        ctx.peaks(1024, spec[1], np.ones((1, 1024), np.complex64), binsize=1024, slot=0)
    finally:
        ctx.stage_host_inputs = staged
    for s, st in zip(spec, starts):
        ref = np.fft.fft(np.stack([series[a:a + 1024] for a in st]), axis=1) / 1024
        np.testing.assert_allclose(s, ref, rtol=0, atol=1e-5 * np.abs(ref).max())


@pytest.mark.parametrize("consumer", ["own slots", "unslotted"])
def test_deferred_forwards_on_several_slots_run_before_their_consumers(consumer):
    """Forwards deferred on slots 0 (two of them) and 4 run before a waited call on their
    slot reads them -- a waited peaks call shares one record across slots but still runs on
    its slot -- and an unslotted call first runs the deferred work that writes what it
    reads. A waited flat call once dropped its slot, ran unslotted, took nothing, and read
    unwritten spectra."""
    import matchedfilter as mf
    from conftest import usable_gpu
    device = usable_gpu()
    if device is None:
        pytest.skip("requires a GPU")
    n = 4096
    plan = mf.MatchedFilter(n, ndata=4, ntemplates=1, device=device)
    ctx = plan._gpu
    rng = np.random.default_rng(5)
    series = plan.empty_shared((40 * n,))
    series[:] = (rng.standard_normal(series.shape)
                 + 1j * rng.standard_normal(series.shape)).astype(np.complex64)
    spec = [plan.empty_shared((4, n)) for _ in range(3)]
    starts = [np.arange(4, dtype=np.uint32) * n, np.arange(4, dtype=np.uint32) * n + 7 * n,
              np.arange(4, dtype=np.uint32) * n + 17 * n]
    for s, st, slot in zip(spec, starts, (0, 0, 4)):
        ctx.forward(n, series, st, s, defer=True, slot=slot)
    h = np.ones((1, n), np.complex64)
    if consumer == "own slots":
        for slot, s in ((0, spec[1]), (4, spec[2])):
            ctx.peaks(n, s, h, binsize=n, slot=slot)
    else:
        ctx.peaks(n, spec[0], h, binsize=n)
        ref = np.fft.fft(np.stack([series[a:a + n] for a in starts[0]]), axis=1) / n
        np.testing.assert_allclose(spec[0], ref, rtol=0, atol=1e-5 * np.abs(ref).max())
        for slot, s in ((0, spec[1]), (4, spec[2])):     # the rest, for their consumers
            ctx.peaks(n, s, h, binsize=n, slot=slot)
    assert not ctx._pending()
    for s, st in zip(spec, starts):
        ref = np.fft.fft(np.stack([series[a:a + n] for a in st]), axis=1) / n
        np.testing.assert_allclose(s, ref, rtol=0, atol=1e-5 * np.abs(ref).max())
