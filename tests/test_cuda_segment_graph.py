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
    assert plan.replays >= 3, (plan.replays, plan.capture_failures)
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
