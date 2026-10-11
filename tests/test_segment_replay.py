"""SegmentPlan replay on Vulkan (MF_SEGMENT_REPLAY): every replayed segment must equal the
same jobs run call by call, under the conditions that broke replay before -- several job sets
sharing the device, recordings evicted between segments, and inputs reallocated (an address
may come back as a different allocation)."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from matchedfilter.time_domain import SegmentPlan

from test_call_plan import _setup, _fill


def _want(jobs):
    return [b.filter_series(x, **kw) for b, x, kw in jobs]     # synchronous: never replayed


def _same(got, want):
    for r1, r2 in zip(want, got):
        for f in r1._fields:
            np.testing.assert_array_equal(getattr(r1, f), getattr(r2, f))


def _loud(rng, rows, S):
    _fill(rng, rows, S)
    for r in rows:
        r[rng.integers(8000, S - 8000, 6)] += 25.0               # peaks to find


@pytest.fixture
def replay_on(monkeypatch):
    monkeypatch.setenv("MF_SEGMENT_REPLAY", "1")


def test_replay_matches_calls(monkeypatch, replay_on):
    rng, banks = _setup(monkeypatch, nbanks=2, seed=81)
    S = 1 << 17
    rows = banks[0][0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, (b, _, _) in enumerate(banks)]
    plan = SegmentPlan()
    peaks = 0
    for seg in range(6):
        _loud(rng, rows, S)
        got = plan.run(jobs)
        _same(got, _want(jobs))
        peaks += sum(len(r.snr) for r in got)
    assert plan.replays >= 3, plan.replays
    assert peaks > 0


def test_replay_with_job_sets_sharing_the_device_and_evictions(monkeypatch, replay_on):
    """Two job sets (two tops) alternate on one device with a small fused-recording cache:
    each set's recordings are evicted and rebuilt by the other's. A replay that submits a
    fused recording whose constituents were freed, or reads a dispatch's freed result
    buffers, shows up here as wrong results or a device fault."""
    monkeypatch.setenv("MF_GPU_FUSE_CACHE", "2")
    rng, banks = _setup(monkeypatch, nbanks=4, seed=82)
    S = 1 << 17
    sets = []
    for k in range(2):
        rows = banks[0][0].empty_shared((2, S))
        sets.append((rows, [(b, rows[i], dict(windows=slice(3000, S - 3000)))
                            for i, (b, _, _) in enumerate(banks[2 * k:2 * k + 2])], SegmentPlan()))
    for seg in range(8):
        for rows, jobs, plan in sets:
            _loud(rng, rows, S)
            _same(plan.run(jobs), _want(jobs))


def test_replay_with_inputs_reallocated(monkeypatch, replay_on):
    """A new series allocation every segment, the old one dropped first: its address may be
    handed out again for the new one. A replay keyed on the address would run recordings
    bound to the freed allocation."""
    import gc
    rng, banks = _setup(monkeypatch, nbanks=2, seed=83)
    S = 1 << 17
    plan = SegmentPlan()
    rows = None
    for seg in range(8):
        rows = None
        gc.collect()
        rows = banks[0][0].empty_shared((len(banks), S))
        jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000)))
                for i, (b, _, _) in enumerate(banks)]
        _loud(rng, rows, S)
        _same(plan.run(jobs), _want(jobs))


def test_two_segments_in_flight(monkeypatch, replay_on):
    """Two SegmentPlans on their own slot halves, each segment submitted before the previous
    one is collected (SegmentPlan.submit), on alternating input buffers: every replayed
    segment equals its calls run one at a time."""
    rng, banks = _setup(monkeypatch, nbanks=2, seed=84)
    S = 1 << 17
    sets = [banks[0][0].empty_shared((len(banks), S)) for _ in range(2)]
    plans = [SegmentPlan(slot_half=0), SegmentPlan(slot_half=1)]
    pending = None
    for seg in range(10):
        rows = sets[seg % 2]
        _loud(rng, rows, S)
        jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000)))
                for i, (b, _, _) in enumerate(banks)]
        want = _want(jobs)
        handle = plans[seg % 2].submit(jobs)
        if pending is not None:
            _same(pending[0].result(), pending[1])
        pending = (handle, want)
    _same(pending[0].result(), pending[1])
    assert sum(p.replays for p in plans) >= 6, [p.replays for p in plans]


def test_eviction_while_a_replay_is_in_flight(monkeypatch, replay_on):
    """Every record released (clear_cache) after a replay is submitted and before it is
    collected: the release reads the replay's results first, so collecting it later reads
    them from host memory, not from freed result buffers."""
    rng, banks = _setup(monkeypatch, nbanks=2, seed=85)
    S = 1 << 17
    rows = banks[0][0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, (b, _, _) in enumerate(banks)]
    plan = SegmentPlan()
    for seg in range(3):
        _loud(rng, rows, S)
        _same(plan.run(jobs), _want(jobs))
    _loud(rng, rows, S)
    want = _want(jobs)
    handle = plan.submit(jobs)
    assert plan.replays >= 1
    ctxs = {id(g.plan._gpu): g.plan._gpu for b, _, _ in jobs for g in b._groups}
    for ctx in ctxs.values():
        ctx.clear_cache()
    _same(handle.result(), want)
    _loud(rng, rows, S)                  # and the plan recovers: a new trace, then replays
    _same(plan.run(jobs), _want(jobs))


@pytest.mark.parametrize("ahead", ["1", "2"])
def test_replay_when_a_segment_reuses_a_slot(monkeypatch, replay_on, ahead):
    """Fewer slots than batches in a segment (a short queue, long series in small batches):
    a later batch reuses an earlier batch's slot, and with it the recording's result buffers.
    Run call by call, the earlier result is read before the reuse; a replay runs both and
    reads after -- the earlier batch's peaks are gone unless the trace refuses to replay."""
    monkeypatch.setenv("MF_GPU_QUEUE_AHEAD", ahead)
    rng, banks = _setup(monkeypatch, nbanks=2, seed=86)
    for b, _, _ in banks:
        for g in b._groups:
            g.plan._series_batch_bytes = 1 << 20          # several batches per call
    S = 1 << 18
    rows = banks[0][0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, (b, _, _) in enumerate(banks)]
    plan = SegmentPlan()
    for seg in range(5):
        _loud(rng, rows, S)
        _same(plan.run(jobs), _want(jobs))


def test_replay_after_other_calls_on_the_same_plans(monkeypatch, replay_on):
    """Between segments, other calls on the same fine banks -- host follow-ups: one template
    over a short window -- reuse slot 0's block starts and spectra. A replay must not run
    on the starts they left (the blocks of their window, not the segment's)."""
    rng, banks = _setup(monkeypatch, nbanks=2, seed=87)
    S = 1 << 17
    rows = banks[0][0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, (b, _, _) in enumerate(banks)]
    plan = SegmentPlan()
    for seg in range(6):
        _loud(rng, rows, S)
        want = _want(jobs)
        _same(plan.run(jobs), want)
        for i, (b, _, _) in enumerate(banks):          # follow-up-like calls in between
            c0 = int(rng.integers(20000, S - 20000))
            b.filter_series(rows[i], windows=slice(c0 - 4000, c0 + 4100), binsize=61,
                            threshold=0.0, template_index=int(rng.integers(0, 10)))
    assert plan.replays >= 3, plan.replays
