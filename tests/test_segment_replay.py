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


def test_chain_trial_locks_under_segment_replay(monkeypatch, replay_on, tmp_path):
    """A GPU chain trial is judged on whole filter_series_many batches. Replayed segments
    never run one, so a SegmentPlan must not replay while a plan of its job set is in a
    trial (it stalled at one sample in 40 segments, plans held on their traced candidate)."""
    import matchedfilter as mf
    monkeypatch.setattr(mf, "_CHAIN_TRIALS", {})
    monkeypatch.setattr(mf, "_CHAIN_CHOICE", {})
    rng, banks = _setup(monkeypatch, nbanks=2, seed=88)
    monkeypatch.delenv("MF_AUTOTUNE", raising=False)            # trials on
    monkeypatch.setenv("MF_CHAIN_TRIALS", "2")
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    S = 1 << 17
    rows = banks[0][0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, (b, _, _) in enumerate(banks)]
    plan = SegmentPlan()

    def state():
        return [(g.plan._chain_trial, tuple(g.plan._chain or ())) for b, _, _ in jobs
                for g in b._groups]
    compared = 0
    for seg in range(30):
        _loud(rng, rows, S)
        before = state()
        got = plan.run(jobs)
        # Compared once the trial is over: a trial batch may run another candidate than the
        # chain the plans hold afterwards (a lock switches them), and the reference runs now.
        if all(t is None for t, _ in before) and state() == before:
            _same(got, _want(jobs))
            compared += 1
    assert compared >= 5, compared
    trials = [g.plan._chain_trial for b, _, _ in jobs for g in b._groups]
    assert all(t is None for t in trials), "a chain trial never locked under replay"
    assert plan.replays > 0


def _prelude_setup(monkeypatch, seed):
    """Fine banks reading rows a middle ('corr') bank writes on the device each segment, as
    the ladder's middle stage does: the SegmentPlan prelude."""
    from test_time_domain import _corr_bank_taps
    rng, banks = _setup(monkeypatch, nbanks=2, seed=seed)
    dev = banks[0][0].device
    taps, counts = _corr_bank_taps("one", rng)
    mid = TimeDomainFilterBank(taps[:2], tap_counts=counts[:2], engine='corr', device=dev,
                               fft_lengths=[2048])
    S = 1 << 17
    m_in = mid.empty_shared((S,))
    m_out = mid.empty_shared((2, S))
    win = slice(2000, S - 2000)

    def prelude():
        mid.correlate_series(m_in, windows=win, out=m_out, wait=False)
    jobs = [(b, m_out[i], dict(windows=slice(3000, S - 3000))) for i, (b, _, _) in enumerate(banks)]
    return rng, banks, mid, m_in, m_out, prelude, jobs, S


def test_prelude_replayed_from_its_capture(monkeypatch, replay_on):
    """The middle stage (prelude) is captured with the trace and replayed in the same
    submission; every segment equals its calls run one at a time on the middle's output."""
    from matchedfilter import _vkcompute as V
    used = []
    orig = V.replay_fused
    monkeypatch.setattr(V, "replay_fused", lambda *a, **k: used.append(k.get("pre") is not None)
                        or orig(*a, **k))
    rng, banks, mid, m_in, m_out, prelude, jobs, S = _prelude_setup(monkeypatch, 89)
    plan = SegmentPlan()

    def blocks():
        return sum(w["blocks"] for w in getattr(mid, "_corr_work", {}).values())
    steps = []
    for seg in range(8):
        X = np.fft.fft(rng.standard_normal(S)); X[S // 2:] = 0
        m_in[:] = (np.fft.ifft(X) * 2).astype(np.complex64)
        m_in[rng.integers(8000, S - 8000, 6)] += 25.0
        b0 = blocks()
        got = plan.submit(jobs, prelude=prelude, prelude_key=("mid", 0)).result()
        mid.wait()
        steps.append(blocks() - b0)
        b1 = blocks()
        _same(got, _want(jobs))
        assert blocks() == b1                         # (the reference calls are not middle)
    assert plan.replays >= 4 and sum(used) >= 4, (plan.replays, used)
    # The middle's work counters (matchedfilter._roofline) advance the same on a replayed
    # prelude as on a called one.
    assert len(set(steps)) == 1 and steps[0] > 0, steps


def test_prelude_capture_invalidated_by_eviction(monkeypatch, replay_on):
    """The middle's records released between segments (clear_cache on its contexts): the
    captured command buffers are freed, so the replay must call the prelude, not resubmit
    them -- and the results stay exact."""
    from matchedfilter import _vkcompute as V
    used = []
    orig = V.replay_fused
    monkeypatch.setattr(V, "replay_fused", lambda *a, **k: used.append(k.get("pre") is not None)
                        or orig(*a, **k))
    rng, banks, mid, m_in, m_out, prelude, jobs, S = _prelude_setup(monkeypatch, 90)
    plan = SegmentPlan()
    for seg in range(10):
        X = np.fft.fft(rng.standard_normal(S)); X[S // 2:] = 0
        m_in[:] = (np.fft.ifft(X) * 2).astype(np.complex64)
        m_in[rng.integers(8000, S - 8000, 6)] += 25.0
        if seg == 6:
            for g in mid._groups:
                cp = g.get_correlation_plan()
                if cp._gpu is not None:
                    cp._gpu.clear_cache()
            n_before = len(used)
        got = plan.submit(jobs, prelude=prelude, prelude_key=("mid", 0)).result()
        mid.wait()
        _same(got, _want(jobs))
        if seg == 6:
            assert used[n_before:] in ([], [False]), used[n_before:]
    assert any(used), used


def test_replay_of_a_ragged_layout(monkeypatch, replay_on):
    """Blocks with different bin counts (bins narrower than a block, windows clipping the
    blocks) run as one call whose result is split per bin count (_RaggedSplit). The parts
    carry the call's trace, so the segment still replays, and the replay splits the call's
    result the same way: every part equals the call-by-call result."""
    from conftest import usable_gpu
    from test_call_plan import _whitened_inspiral_bank
    from matchedfilter import time_domain as td
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(97)
    banks = []
    for _ in range(2):
        counts = list(rng.integers(200, 400, 33))
        taps, w, df = _whitened_inspiral_bank(rng, counts)
        b = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                 false_dismissal=1e-3, device=dev, fft_lengths=[4096],
                                 binsize=1000)
        b.set_reference(w, delta_f=df)
        banks.append(b)
    if not getattr(banks[0]._groups[0].plan._gpu, "supports_replay", False):
        pytest.skip("this backend records no call plans")
    splits = []
    orig = td._RaggedSplit.deferred
    monkeypatch.setattr(td._RaggedSplit, "deferred",
                        lambda self, d: splits.append(len(self.us)) or orig(self, d))
    S = 1 << 17
    rows = banks[0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=[slice(3011, 61003), slice(70001, S - 2999)]))
            for i, b in enumerate(banks)]
    plan = SegmentPlan()
    peaks = 0
    for seg in range(6):
        _loud(rng, rows, S)
        got = plan.run(jobs)
        _same(got, _want(jobs))
        peaks += sum(len(r.snr) for r in got)
    assert splits and max(splits) > 1, "no ragged split ran: %s" % splits
    assert plan.replays >= 3, plan.replays
    assert peaks > 0
