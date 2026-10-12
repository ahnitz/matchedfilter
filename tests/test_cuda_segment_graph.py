"""CUDA segment graphs (SegmentPlan._run_cuda): a recurring fine-stage job set runs as one
captured CUDA graph. A replay must return exactly what filter_series_many returns, with the
data rewritten in place between segments, and anything that invalidates the graph -- a new
allocation, a freed buffer, another job set -- must fall back to the full path.
"""
import gc

import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank, _cuda
from matchedfilter.time_domain import SegmentPlan
from test_time_domain import _whitened_inspiral_bank

pytestmark = pytest.mark.skipif(not _cuda.enumerate_devices()[0], reason="no NVIDIA CUDA device")


def _banks(monkeypatch, nbanks=3, seed=81):
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    rng = np.random.default_rng(seed)
    banks = []
    for _ in range(nbanks):
        counts = list(rng.integers(200, 400, 33))
        taps, w, df = _whitened_inspiral_bank(rng, counts)
        b = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                 false_dismissal=1e-3, device="cuda:0", fft_lengths=[2048],
                                 binsize=2048)
        b.set_reference(w, delta_f=df)
        banks.append(b)
    return rng, banks


def _fill(rng, rows, S, loud=False):
    for r in rows:
        X = np.fft.fft(rng.standard_normal(S))
        X[S // 2:] = 0
        r[:] = (np.fft.ifft(X) * 2).astype(np.complex64)
        if loud:                               # a few bright samples: peaks in every bank
            r[rng.integers(5000, S - 5000, 6)] += 40.0


def _same(a, b):
    assert len(a) == len(b)
    for r1, r2 in zip(a, b):
        for f in r1._fields:
            np.testing.assert_array_equal(getattr(r1, f), getattr(r2, f))


def test_segment_graph_replays_exactly(monkeypatch):
    rng, banks = _banks(monkeypatch)
    S = 1 << 17
    rows = banks[0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, b in enumerate(banks)]
    plan = SegmentPlan()
    peaks = 0
    for seg in range(6):
        _fill(rng, rows, S, loud=seg % 2 == 1)        # rewritten in place
        got = plan.run(jobs)
        want = [b.filter_series(x, **kw) for b, x, kw in jobs]
        _same(want, got)
        peaks += sum(len(r.snr) for r in got)
    assert peaks > 0


def test_freed_buffer_invalidates_the_graph(monkeypatch):
    """A new series allocation each segment (the old one freed, its address free to reuse):
    the signature or the freed-buffer generation must stop every stale replay."""
    rng, banks = _banks(monkeypatch, nbanks=2, seed=82)
    S = 1 << 17
    plan = SegmentPlan()
    for seg in range(5):
        rows = banks[0].empty_shared((len(banks), S))
        _fill(rng, rows, S, loud=True)
        jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, b in enumerate(banks)]
        got = plan.run(jobs)
        _same([b.filter_series(x, **kw) for b, x, kw in jobs], got)
        del rows, jobs
        gc.collect()


def test_other_job_set_falls_back(monkeypatch):
    rng, banks = _banks(monkeypatch, nbanks=2, seed=83)
    S = 1 << 17
    rows = banks[0].empty_shared((len(banks), S))
    plan = SegmentPlan()
    a = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, b in enumerate(banks)]
    b2 = [(b, rows[i], dict(windows=slice(9000, S - 9000))) for i, b in enumerate(banks)]
    for jobs in (a, a, a, b2, a, b2, b2, b2):
        _fill(rng, rows, S, loud=True)
        _same([b.filter_series(x, **kw) for b, x, kw in jobs], plan.run(jobs))


def test_folded_job_sets_match_separate_calls(monkeypatch):
    """Several top templates' job sets folded into one SegmentPlan request (one graph per
    segment, as ladder LADDER_FOLD_TOPS) give exactly the per-call results of every job, on
    the capture run and on replays alike. Two sets of banks stand for two top templates;
    each set's rows are rewritten in place every segment."""
    rng, banks_a = _banks(monkeypatch, nbanks=2, seed=84)
    _, banks_b = _banks(monkeypatch, nbanks=3, seed=85)
    S = 1 << 17
    rows_a = banks_a[0].empty_shared((len(banks_a), S))
    rows_b = banks_b[0].empty_shared((len(banks_b), S))
    jobs = ([(b, rows_a[i], dict(windows=slice(3000, S - 3000))) for i, b in enumerate(banks_a)]
            + [(b, rows_b[i], dict(windows=slice(5000, S - 5000))) for i, b in enumerate(banks_b)])
    plan = SegmentPlan()
    for seg in range(6):
        _fill(rng, rows_a, S, loud=True)
        _fill(rng, rows_b, S, loud=seg % 2 == 0)
        got = plan.run(jobs)
        _same([b.filter_series(x, **kw) for b, x, kw in jobs], got)


def test_two_segments_in_flight_match_separate_calls(monkeypatch):
    """Two SegmentPlans on disjoint slot halves and double-buffered inputs, segment k launched
    (submit) before k-1 is collected, as ladder LADDER_INFLIGHT: every segment's results equal
    the per-call results on the same data, replays included."""
    rng, banks = _banks(monkeypatch, nbanks=3, seed=86)
    S = 1 << 17
    rows = [banks[0].empty_shared((len(banks), S)) for _ in range(2)]
    plans = [SegmentPlan(slot_half=0), SegmentPlan(slot_half=1)]
    want, pending = {}, None
    for seg in range(10):
        r = rows[seg % 2]
        _fill(rng, r, S, loud=seg % 3 == 1)           # while segment k-1 runs on the device
        jobs = [(b, r[i], dict(windows=slice(3000, S - 3000))) for i, b in enumerate(banks)]
        if pending is not None:
            _same(want[pending[0]], pending[1].result())
        # The per-call reference: synchronous calls share the device's workspaces with the
        # graphs, so only between segments (as an application's other work would be).
        want[seg] = [b.filter_series(x, **kw) for b, x, kw in jobs]
        pending = (seg, plans[seg % 2].submit(jobs))
    _same(want[pending[0]], pending[1].result())
    assert sum(p.replays for p in plans) >= 4, [(p.replays, p.capture_failures) for p in plans]


def test_replays_count_their_work(monkeypatch):
    """A replayed segment graph runs its dispatches and its prelude without the host calls
    that count their work (matchedfilter._roofline): each replay must add what the same
    segment's direct calls add -- the middle bank's counters for the prelude, and every fine
    plan's pairs, tier passes and refines."""
    rng, banks = _banks(monkeypatch, nbanks=2, seed=87)
    S = 1 << 17
    # One tap count: the group's rows are then a contiguous slice of the output, which
    # the middle stage writes in place and leaves in flight (as the ladder's bank does).
    counts = [300] * len(banks)
    taps, _, _ = _whitened_inspiral_bank(rng, counts)
    mid = TimeDomainFilterBank(taps, tap_counts=counts, engine="corr", device="cuda:0")
    assert all(np.array_equal(g.template_indices, np.sort(g.template_indices)) for g in mid._groups)
    inp = mid.empty_shared((S,), input=True)
    rows = mid.empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, b in enumerate(banks)]

    def prelude():
        mid.correlate_series(inp, windows=slice(1000, S - 1000), out=rows, wait=False)

    def snap():
        fine = [g.plan.work_counts() for b in banks for g in b._groups if g.is_hier]
        return ({n: dict(v) for n, v in getattr(mid, "_corr_work", {}).items()},
                getattr(mid, "_corr_in_samples", 0),
                [(c["pairs"], tuple(c["passed"]), c["refined"]) for c in fine])

    def delta(a, b):
        mw = {n: {k: v - a[0].get(n, {}).get(k, 0) for k, v in d.items()} for n, d in b[0].items()}
        fine = [(p1 - p0, tuple(y - x for x, y in zip(s0, s1)), r1 - r0)
                for (p0, s0, r0), (p1, s1, r1) in zip(a[2], b[2])]
        return mw, b[1] - a[1], fine

    plan = SegmentPlan()
    replayed = 0
    for seg in range(6):
        X = np.fft.fft(rng.standard_normal(S))
        X[S // 2:] = 0
        inp[:] = (np.fft.ifft(X) * 2).astype(np.complex64)
        inp[rng.integers(5000, S - 5000, 4)] += 30.0
        s0, r0 = snap(), plan.replays
        got = plan.run(jobs, prelude=prelude, prelude_key="mid")
        s1 = snap()
        replayed += plan.replays > r0
        # The same segment by direct calls, on the same data.
        mid.correlate_series(inp, windows=slice(1000, S - 1000), out=rows)
        want = [b.filter_series(x, **kw) for b, x, kw in jobs]
        _same(want, got)
        s2 = snap()
        assert delta(s0, s1) == delta(s1, s2), seg
    assert replayed >= 2
