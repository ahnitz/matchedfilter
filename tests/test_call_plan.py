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


def test_ragged_split_sparse_matches_dense():
    """_RaggedSplit.parts on a sparse result is the sparse form of the dense per-count split,
    and _SparsePeaks.blocks of one part."""
    from matchedfilter.time_domain import _RaggedSplit
    from matchedfilter import _SparsePeaks
    rng = np.random.default_rng(5)
    idx = np.where(rng.random((7, 3, 4)) < 0.3, rng.integers(0, 99, (7, 3, 4)), -1)
    val = (rng.standard_normal(idx.shape) + 1j).astype(np.complex64) * (idx >= 0)
    flat = np.flatnonzero(idx >= 0)
    sp = _SparsePeaks(idx.shape, flat, idx.reshape(-1)[flat], val.reshape(-1)[flat])
    for m, u in ((np.array([1, 0, 1, 1, 0, 0, 1], bool), 2), (np.ones(7, bool), 4),
                 (np.zeros(7, bool), 3)):
        di, dv = sp.blocks(m, u).dense()
        np.testing.assert_array_equal(di, np.where(idx[m][:, :, :u] >= 0, idx[m][:, :, :u], -1))
        np.testing.assert_array_equal(dv, val[m][:, :, :u])
    bc = np.array([4, 2, 4, 1, 2, 4, 3])
    split = _RaggedSplit(bc)
    for got, (di, dv) in zip(split.parts(sp), split.parts((idx, val))):
        gi, gv = got.dense()
        np.testing.assert_array_equal(gi, np.where(di >= 0, di, -1))
        np.testing.assert_array_equal(gv, dv)


def test_pooled_follow_up_workspaces_in_flight(monkeypatch):
    """Follow-up workspaces come from a per-device pool: two banks' follow-ups, two batches in
    flight at once, each still returns exactly its direct calls' results (a workspace handed
    out again before its results were read would mix them)."""
    monkeypatch.setenv("MF_SINGLE_DEVICE", "bank")
    rng, banks = _setup(monkeypatch, seed=76)
    S = 1 << 17
    rows = banks[0][0].empty_shared((4, S))
    _fill(rng, rows, S)

    def batch():
        jobs = []
        for k in range(12):
            b = banks[k % 2][0]
            c0 = int(rng.integers(20000, S - 20000))
            jobs.append((b, rows[k % 4], dict(windows=slice(c0 - 9000, c0 + 9100), binsize=61,
                                              threshold=0.0,
                                              template_index=int(rng.integers(0, 33)))))
        return jobs
    j1, j2 = batch(), batch()
    f1 = TimeDomainFilterBank.filter_series_many(j1, wait=False)
    f2 = TimeDomainFilterBank.filter_series_many(j2, wait=False)
    got = [f.result() for f in f2 + f1]
    want = [b.filter_series(x, **kw) for b, x, kw in j2 + j1]
    for r1, r2 in zip(want, got):
        for f in r1._fields:
            np.testing.assert_array_equal(getattr(r1, f), getattr(r2, f))


def test_staged_series_in_flight(monkeypatch):
    """correlate_series copies a host series into one bank-level staging buffer: a second
    call while the first is in flight (wait=False) must not overwrite what the first reads."""
    from conftest import usable_gpu
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(77)
    counts = list(rng.integers(200, 400, 20)) + list(rng.integers(1300, 1800, 20))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                false_dismissal=1e-3, device=dev, fft_lengths=[2048, 4096])
    bank.set_reference(w, delta_f=df)
    if len(bank._groups) < 2:
        pytest.skip("one template group: nothing is staged")
    S = 1 << 20                              # long enough that call 1 is still running
    xs = []
    for _ in range(3):
        X = np.fft.fft(rng.standard_normal(S))
        X[S // 2:] = 0
        xs.append((np.fft.ifft(X) * 2).astype(np.complex64))
    outs = [bank.empty_shared((bank.n_templates, S)) for _ in xs]
    # The device may finish call 1 before call 2's copy on a fast GPU, so also check the
    # guard itself: each staging copy settles every group's device first.
    gpus = {id(g.get_correlation_plan()._gpu): g.get_correlation_plan()._gpu
            for g in bank._groups}
    events = []
    for gpu in gpus.values():
        orig = gpu.settle_writes
        monkeypatch.setattr(gpu, "settle_writes",
                            lambda orig=orig: events.append("settle") or orig())
    orig_fill = type(bank)._fill_staging

    def fill(staged, ser):
        events.append("fill")
        return orig_fill(staged, ser)
    monkeypatch.setattr(type(bank), "_fill_staging", staticmethod(fill))
    for x, o in zip(xs, outs):
        events.append("call")
        bank.correlate_series(x, windows=slice(3000, S - 3000), out=o, wait=False)
    calls = [i for i, e in enumerate(events) if e == "call"] + [len(events)]
    for a, b in zip(calls, calls[1:]):
        part = events[a:b]
        assert "fill" in part, events
        before = part[:part.index("fill")]
        assert before.count("settle") >= len(gpus), events
    bank.wait()
    for x, o in zip(xs, outs):
        np.testing.assert_array_equal(o, bank.correlate_series(x, windows=slice(3000, S - 3000)))


def test_follow_up_pool_never_hands_out_a_workspace_in_use():
    """The pool contract, deterministically (on Vulkan follow-ups are collected before
    filter_series_many returns, so no device test can catch a premature return): a checked-
    out workspace is never handed out again until returned; a plan gets its last one back."""
    from matchedfilter import MatchedFilter

    class FakeGPU:
        def empty_shared(self, shape, dtype=np.complex64):
            return np.zeros(shape, dtype)

    gpu = FakeGPU()
    a, b = object.__new__(MatchedFilter), object.__new__(MatchedFilter)
    wa = a._items_checkout(gpu, 256, 100)
    wb = b._items_checkout(gpu, 256, 100)
    assert wa is not wb and wa[0].shape[0] >= 100
    a._items_return(gpu, 256, wa)
    assert b._items_checkout(gpu, 256, 50) is wa       # free again: may be reused
    b._items_return(gpu, 256, wb)
    assert a._items_checkout(gpu, 256, 100) is not wa  # wa is out with b
    assert a._items_checkout(gpu, 256, 300)[0].shape[0] >= 300



def test_band_mode_flip_replays_exact(monkeypatch):
    """Vulkan's band-only forward (option a): a replayed band-mode call resubmits its own
    band forward and recompute records, and a flip of the band/full choice (forced here;
    measured otherwise) never replays a record made for the other mode. Every call matches
    the synchronous full call exactly, before and after each flip."""
    rng, banks = _setup(monkeypatch, seed=73)
    ctx = banks[0][0]._groups[0].plan._gpu
    if not hasattr(ctx, "_band_wanted"):
        pytest.skip("this backend has no band-only forward")
    S = 1 << 17
    rows = banks[0][0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, (b, _, _) in enumerate(banks)]
    seen = []
    for mode in ("1", "1", "1", "0", "0", "1", "1"):
        monkeypatch.setenv("MF_VK_BAND_FORWARD", mode)
        before = _replays(banks)
        _fill(rng, rows, S)
        _check(jobs)
        seen.append((mode, _replays(banks) - before))
    # Replays happened within a mode, and the first call after a flip re-recorded.
    assert any(r for m, r in seen[1:3]), seen
    assert seen[3][1] == 0 and seen[5][1] == 0, seen
