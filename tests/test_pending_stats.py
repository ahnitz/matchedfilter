"""In-flight results restore the per-dispatch statistics their finish left on the context.

A deferred result can be materialised early (timings() drains every context, so do cache
evictions and slot reuse) and in any order; the hierarchical plan reads last_refinements
when it collects the result. Read stale, a deferred call counted 0 refinements, marked itself
empty, and the ladder's --pipeline --timing run lost 95% of its fine triggers on Metal."""
from matchedfilter._gpu_cache import InputUploads


class _Ctx(InputUploads):
    pass


def test_early_drain_keeps_each_results_refinement_count():
    ctx = _Ctx()

    def dispatch(count):
        def finish():
            ctx.last_refinements = count
            return count
        return ctx._track(finish)

    a, b = dispatch(5), dispatch(0)
    ctx._drain()                       # both finished early, b last: the context says 0
    assert ctx.last_refinements == 0
    assert a() == 5 and ctx.last_refinements == 5
    assert b() == 0 and ctx.last_refinements == 0
