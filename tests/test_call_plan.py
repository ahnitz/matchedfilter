"""Call plans (MatchedFilter._replay_call_plan): a repeated deferred fine call resubmits its
recorded records. A replay must return exactly what the full call returns, and anything that
changes the call -- data rewritten in place, a new allocation (perhaps at the same address),
new calibration, evicted records -- must either still be exact or fall back to the full path.
"""
import gc

import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from test_time_domain import _whitened_inspiral_bank


def _setup(monkeypatch, nbanks=2, seed=71):
    from conftest import usable_gpu
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(seed)
    banks = []
    for _ in range(nbanks):
        counts = list(rng.integers(200, 400, 33))
        taps, w, df = _whitened_inspiral_bank(rng, counts)
        b = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                 false_dismissal=1e-3, device=dev, fft_lengths=[2048], binsize=2048)
        b.set_reference(w, delta_f=df)
        banks.append((b, w, df))
    if not getattr(banks[0][0]._groups[0].plan._gpu, "supports_replay", False):
        pytest.skip("this backend records no call plans")
    return rng, banks


def _fill(rng, rows, S):
    for r in rows:
        X = np.fft.fft(rng.standard_normal(S))
        X[S // 2:] = 0
        r[:] = (np.fft.ifft(X) * 2).astype(np.complex64)


def _replays(banks):
    return sum(getattr(g.plan, "call_plan_replays", 0) for b, _, _ in banks for g in b._groups)


def _check(jobs):
    got = [f.result() for f in TimeDomainFilterBank.filter_series_many(jobs, wait=False)]
    want = [b.filter_series(x, **kw) for b, x, kw in jobs]       # synchronous: never replayed
    for r1, r2 in zip(want, got):
        for f in r1._fields:
            np.testing.assert_array_equal(getattr(r1, f), getattr(r2, f))
    return sum(len(r.snr) for r in got)


def test_replayed_calls_match_full_calls(monkeypatch):
    rng, banks = _setup(monkeypatch)
    S = 1 << 17
    rows = banks[0][0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, (b, _, _) in enumerate(banks)]
    total = 0
    for _ in range(4):
        _fill(rng, rows, S)                 # rewritten in place: replays read the new data
        total += _check(jobs)
    assert _replays(banks) > 0, "a recurring deferred call was never replayed"
    assert total >= 3


def test_new_allocation_each_segment(monkeypatch):
    """A fresh device allocation per segment (the old one dropped, so its address may be
    reused): never a stale replay."""
    rng, banks = _setup(monkeypatch, seed=72)
    S = 1 << 17
    for _ in range(4):
        rows = banks[0][0].empty_shared((len(banks), S))
        _fill(rng, rows, S)
        _check([(b, rows[i], dict(windows=slice(3000, S - 3000)))
                for i, (b, _, _) in enumerate(banks)])
        del rows
        gc.collect()


def test_recalibration_and_eviction_invalidate(monkeypatch):
    rng, banks = _setup(monkeypatch, seed=73)
    S = 1 << 17
    rows = banks[0][0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, (b, _, _) in enumerate(banks)]
    for seg in range(6):
        _fill(rng, rows, S)
        if seg == 2:                         # a new reference SHAPE: new band fractions
            for b, w, df in banks:
                b.set_reference(w * np.linspace(2.0, 0.2, w.size) ** 2, delta_f=df)
        if seg == 4:                         # every record evicted
            for b, _, _ in banks:
                for g in b._groups:
                    g.plan._gpu.clear_cache()
        _check(jobs)
    assert _replays(banks) > 0


def test_threshold_and_window_changes(monkeypatch):
    rng, banks = _setup(monkeypatch, seed=74)
    S = 1 << 17
    rows = banks[0][0].empty_shared((len(banks), S))
    for seg in range(6):
        _fill(rng, rows, S)
        thr = 4.5 if seg % 2 == 0 else 5.5
        w0 = 3000 if seg < 3 else 5000
        _check([(b, rows[i], dict(windows=slice(w0, S - w0), threshold=thr))
                for i, (b, _, _) in enumerate(banks)])


def test_explicit_gate_thresholds_invalidate(monkeypatch):
    """set_coarse_threshold recalibrates without dirtying templates: only the plan's state
    check stands between a replay and the old thresholds' records."""
    from conftest import usable_gpu
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(75)
    counts = list(rng.integers(200, 400, 33))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                false_dismissal=1e-3, device=dev, fft_lengths=[2048], binsize=2048,
                                coarse_band_hz=(256.0,))
    bank.set_reference(w, delta_f=df)
    if not getattr(bank._groups[0].plan._gpu, "supports_replay", False):
        pytest.skip("this backend records no call plans")
    S = 1 << 17
    rows = bank.empty_shared((1, S))
    jobs = [(bank, rows[0], dict(windows=slice(3000, S - 3000)))]
    seen, prev = set(), None
    for seg, thr in enumerate((0.0, 0.0, 0.0, 1e30, 1e30, 1e30, 0.0, 0.0)):
        _fill(rng, rows, S)
        if thr != prev:                     # set only on a change: repeats replay
            for g in bank._groups:
                g.plan.set_coarse_threshold(thr)
            prev = thr
        n = _check(jobs)
        seen.add((thr, n > 0))
    assert (1e30, False) in seen and (0.0, True) in seen, seen
    assert _replays([(bank, w, df)]) > 0
