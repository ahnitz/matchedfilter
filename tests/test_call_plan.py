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
    for seg in range(9):        # batches alternate slot bases: replays from the 3rd stable one
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
    # Sorted: each template group is a contiguous slice, so its work stays in flight.
    counts = sorted(list(rng.integers(200, 400, 20)) + list(rng.integers(1300, 1800, 20)))
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
    # The device may finish call 1 before call 3's copy on a fast GPU, so also check the
    # guard itself. Two staging buffers alternate: call i's copy must first wait for the
    # writes that call i-2 (the last reader of the same buffer) left in flight.
    gpus = {id(g.get_correlation_plan()._gpu): g.get_correlation_plan()._gpu
            for g in bank._groups}
    events = []
    for gpu in gpus.values():
        if hasattr(gpu, "settle_until"):
            orig = gpu.settle_until
            monkeypatch.setattr(gpu, "settle_until",
                                lambda token, orig=orig: events.append(("until", id(token)))
                                or orig(token))
        orig_s = gpu.settle_writes
        monkeypatch.setattr(gpu, "settle_writes",
                            lambda orig=orig_s: events.append(("settle", None)) or orig())
    orig_fill = type(bank)._fill_staging

    def fill(staged, ser):
        events.append(("fill", None))
        return orig_fill(staged, ser)
    monkeypatch.setattr(type(bank), "_fill_staging", staticmethod(fill))
    tokens, cw_tokens = [], []
    for i, (x, o) in enumerate(zip(xs, outs)):
        events.append(("call", i))
        bank.correlate_series(x, windows=slice(3000, S - 3000), out=o, wait=False)
        slots = bank.__dict__.get("_ser_stagings", [])
        tokens.append({id(t) for _, t in (slots[i % len(slots)][1] if slots else [])
                       if t is not None})
        cws = [g.get_correlation_plan().__dict__.get("_continuous_workspaces", [])
               for g in bank._groups]
        cw_tokens.append({id(p[i % len(p)][4]) for p in cws
                          if p and p[i % len(p)] is not None and p[i % len(p)][4] is not None})
    calls = [j for j, e in enumerate(events) if e[0] == "call"] + [len(events)]
    double = len(bank.__dict__.get("_ser_stagings", [])) == 2
    for i, (a, b) in enumerate(zip(calls, calls[1:])):
        part = events[a:b]
        fi = [e[0] for e in part].index("fill")
        before = part[:fi]
        if not double:
            assert sum(e[0] == "settle" for e in before) >= len(gpus), events
        elif i >= 2:
            waited = {e[1] for e in before if e[0] == "until"}
            assert tokens[i - 2] <= waited, (i, tokens[i - 2], events)
            # Each group's continuous workspace likewise waits for its call two back.
            assert cw_tokens[i - 2] <= {e[1] for e in part if e[0] == "until"}, (i, events)
    if double:
        assert any(cw_tokens[:1]) and any(tokens[:1]), "nothing was left in flight"
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


def test_two_segments_in_flight_match_serial(monkeypatch):
    """A pipeline keeping two segments in flight (collecting k-2): every result equals the
    serial call on the same data -- slots, recordings, workspaces and call plans of one
    batch are never rewritten under the other."""
    rng, banks = _setup(monkeypatch, nbanks=3, seed=78)
    S = 1 << 17
    sets = [banks[0][0].empty_shared((len(banks), S)) for _ in range(3)]
    inflight, checked = [], 0
    for seg in range(8):
        rows = sets[seg % 3]
        _fill(rng, rows, S)
        jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000)))
                for i, (b, _, _) in enumerate(banks)]
        inflight.append((jobs, TimeDomainFilterBank.filter_series_many(jobs, wait=False)))
        while len(inflight) > 2 or (seg == 7 and inflight):
            old_jobs, futures = inflight.pop(0)
            got = [f.result() for f in futures]
            want = [b.filter_series(x, **kw) for b, x, kw in old_jobs]
            for r1, r2 in zip(want, got):
                for f in r1._fields:
                    np.testing.assert_array_equal(getattr(r1, f), getattr(r2, f))
            checked += 1
    assert checked == 8
    assert _replays(banks) > 0


@pytest.mark.parametrize("band", ["0", "1"])
@pytest.mark.parametrize("depth", [1, 2])
def test_steady_segments_replay(monkeypatch, band, depth):
    """With chain trials ON (the default), band mode forced either way, and one or two
    segments in flight: after warm-up every fine call of a segment replays its call plan.
    A trial that never locks (its calls bypassed the timed path), slot bases that never
    settle, or a mode that flips every call all show up here as misses, not as host time."""
    import matchedfilter as mf
    # Trials are process-wide per configuration: start from none, as a fresh search does
    # (another test's dead plans hold candidates of the same configuration).
    monkeypatch.setattr(mf, "_CHAIN_TRIALS", {})
    monkeypatch.setattr(mf, "_CHAIN_CHOICE", {})
    monkeypatch.delenv("MF_AUTOTUNE", raising=False)      # trials on
    rng, banks = _setup(monkeypatch, nbanks=2, seed=79)
    monkeypatch.delenv("MF_AUTOTUNE", raising=False)
    monkeypatch.setenv("MF_CHAIN_TRIALS", "2")
    monkeypatch.setenv("MF_VK_BAND_FORWARD", band)
    S = 1 << 17
    sets = [banks[0][0].empty_shared((len(banks), S)) for _ in range(depth + 1)]
    inflight, deltas = [], []
    for seg in range(16):
        rows = sets[seg % (depth + 1)]
        _fill(rng, rows, S)
        jobs = [(b, rows[i], dict(windows=slice(3001, S - 2999), binsize=500))
                for i, (b, _, _) in enumerate(banks)]
        before = _replays(banks)
        inflight.append(TimeDomainFilterBank.filter_series_many(jobs, wait=False))
        deltas.append((_replays(banks) - before, sum(len(b._groups) for b, _, _ in jobs)))
        while len(inflight) > depth:
            [f.result() for f in inflight.pop(0)]
    for fs in inflight:
        [f.result() for f in fs]
    for b, _, _ in banks:
        for g in b._groups:
            tk = getattr(g.plan, "_chain_trial", None)
            assert tk is None, ("a chain trial never locked", g.plan._chain,
                                {c: len(v) for c, v in mf._CHAIN_TRIALS[tk]["samples"].items()},
                                mf._CHAIN_TRIALS[tk]["assigned"])
    assert all(d == want for d, want in deltas[-4:]), deltas


def test_depth_one_keeps_one_set_of_recordings(monkeypatch):
    """A caller that collects each batch before the next (depth 1) must reuse the same slots:
    the hierarchical recordings stop growing after warm-up. Alternating slot bases regardless
    doubled them, which at n=8192 overflowed the recording cache (re-recording every call)."""
    rng, banks = _setup(monkeypatch, nbanks=2, seed=80)
    S = 1 << 17
    rows = banks[0][0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3001, S - 2999), binsize=500))
            for i, (b, _, _) in enumerate(banks)]

    def recordings():
        ctxs = {id(g.plan._gpu): g.plan._gpu for b, _, _ in banks for g in b._groups}
        return sum(len(getattr(c, "_hier", {})) + len(getattr(c, "_hier_cascade", {}))
                   for c in ctxs.values())
    counts = []
    for seg in range(8):
        _fill(rng, rows, S)
        [f.result() for f in TimeDomainFilterBank.filter_series_many(jobs, wait=False)]
        counts.append(recordings())
    assert counts[0] == counts[-1], counts       # the first batch recorded them all
    assert _replays(banks) > 0


def test_band_mode_allocates_nothing_in_steady_state(monkeypatch):
    """Band-mode storage is keyed on the band width, not on the series/starts buffers the
    records bind: those come from rotating pools, and keying buffers on them allocated a new
    set per call (1339 buffers in 38 steady ladder segments)."""
    rng, banks = _setup(monkeypatch, seed=74)
    from matchedfilter import _vkcompute as V
    monkeypatch.setenv("MF_VK_BAND_FORWARD", "1")
    S = 1 << 17
    pools = [banks[0][0].empty_shared((len(banks), S)) for _ in range(3)]
    made = [0]
    orig = V._Buffer.__init__

    def counting(self, *a, **k):
        made[0] += 1
        orig(self, *a, **k)
    for seg in range(12):
        rows = pools[seg % 3]                   # rotating series allocations
        _fill(rng, rows, S)
        if seg == 6:
            monkeypatch.setattr(V._Buffer, "__init__", counting)
        _check([(b, rows[i], dict(windows=slice(3000, S - 3000)))
                for i, (b, _, _) in enumerate(banks)])
    assert made[0] == 0, "%d buffers allocated in steady state" % made[0]


@pytest.mark.parametrize("new_alloc", [False, True])
def test_device_followups_track_their_buffers(monkeypatch, new_alloc):
    """Vulkan follow-ups (_vkfollowup) replay one recording per template group, bound to the
    series allocations and templates it was made for: rewritten data, or a new allocation each
    segment (perhaps at a freed one's address), must still give each job's direct result."""
    monkeypatch.setenv("MF_SINGLE_DEVICE", "bank")
    rng, banks = _setup(monkeypatch, nbanks=1, seed=81)
    bank = banks[0][0]
    if not getattr(bank._groups[0].plan._gpu, "supports_device_followups", False):
        pytest.skip("backend has no device follow-ups")
    from matchedfilter import _vkfollowup
    calls = []
    orig = _vkfollowup.Executor.submit_jobs
    monkeypatch.setattr(_vkfollowup.Executor, "submit_jobs",
                        lambda self, js: calls.append(len(js)) or orig(self, js))
    S = 1 << 17
    rows = bank.empty_shared((2, S))
    for seg in range(4):
        if new_alloc:
            del rows
            gc.collect()
            rows = bank.empty_shared((2, S))
        _fill(rng, rows, S)
        jobs = []
        for k in range(6):
            c0 = int(rng.integers(20000, S - 20000))
            jobs.append((bank, rows[k % 2], dict(windows=slice(c0 - 3000, c0 + 3100), binsize=61,
                                                 threshold=0.0,
                                                 template_index=int(rng.integers(0, 33)))))
        many = TimeDomainFilterBank.filter_series_many(jobs)
        direct = [b.filter_series(x, **kw) for b, x, kw in jobs]
        for r1, r2 in zip(direct, many):
            for f in r1._fields:
                np.testing.assert_array_equal(getattr(r1, f), getattr(r2, f))
    assert calls, "the device follow-up path was not taken"


def test_device_followups_in_flight(monkeypatch):
    """Vulkan follow-ups are submitted without a wait (filter_series_many(wait=False)): a second
    batch on the same records, submitted before the first is collected, must first finish the
    first (its tables and outputs are rewritten), and both must equal their direct calls."""
    monkeypatch.setenv("MF_SINGLE_DEVICE", "bank")
    rng, banks = _setup(monkeypatch, nbanks=1, seed=82)
    bank = banks[0][0]
    if not getattr(bank._groups[0].plan._gpu, "supports_device_followups", False):
        pytest.skip("backend has no device follow-ups")
    S = 1 << 17
    rows = bank.empty_shared((2, S))
    _fill(rng, rows, S)

    def batch():
        jobs = []
        for k in range(6):
            c0 = int(rng.integers(20000, S - 20000))
            jobs.append((bank, rows[k % 2], dict(windows=slice(c0 - 3000, c0 + 3100), binsize=61,
                                                 threshold=0.0,
                                                 template_index=int(rng.integers(0, 33)))))
        return jobs
    j1, j2 = batch(), batch()
    f1 = TimeDomainFilterBank.filter_series_many(j1, wait=False)
    f2 = TimeDomainFilterBank.filter_series_many(j2, wait=False)
    got = [f.result() for f in f2 + f1]              # second batch collected first
    want = [b.filter_series(x, **kw) for b, x, kw in j2 + j1]
    for r1, r2 in zip(want, got):
        for f in r1._fields:
            np.testing.assert_array_equal(getattr(r1, f), getattr(r2, f))


def test_device_followups_steady_state_allocates_nothing(monkeypatch):
    """After warm-up, Vulkan follow-ups whose jobs move between template groups and series
    allocations every segment create no workspace, buffer or descriptor pool: a group's
    templates and allocations are rebound in place on a pooled workspace."""
    monkeypatch.setenv("MF_SINGLE_DEVICE", "bank")
    rng, banks = _setup(monkeypatch, nbanks=1, seed=83)
    # Several template groups of one block length (they share workspaces), so jobs move
    # between groups and workspace slots.
    counts = list(rng.integers(200, 400, 33))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                false_dismissal=1e-3, device=banks[0][0].device,
                                fft_lengths=[2048], binsize=2048, max_batch_size=8)
    bank.set_reference(w, delta_f=df)
    ctx = bank._groups[0].plan._gpu
    if not getattr(ctx, "supports_device_followups", False):
        pytest.skip("backend has no device follow-ups")
    from matchedfilter import _vkfollowup, _vkcompute as vkc
    made, on = [], [False]
    for cls in (_vkfollowup._Workspace, vkc._Buffer):
        orig = cls.__init__
        monkeypatch.setattr(cls, "__init__", lambda self, *a, _o=orig, _c=cls, **k:
                            (on[0] and made.append(_c.__name__)) or _o(self, *a, **k))
    S = 1 << 17
    rows = [bank.empty_shared((2, S)) for _ in range(2)]
    groups = {}
    for t in range(33):
        groups.setdefault(id(bank._template_map[t][0]), []).append(t)
    per_group = list(groups.values())
    assert len(per_group) > 1, "the bank should span several template groups"

    def segment(templates):
        jobs = []
        for k, t in enumerate(templates):
            c0 = int(rng.integers(20000, S - 20000))
            jobs.append((bank, rows[k % 2][k % 2 - 1], dict(
                windows=slice(c0 - 3000, c0 + 3100), binsize=61, threshold=0.0,
                template_index=int(t))))
        on[0] = True                                  # the follow-ups only, not the references
        try:
            many = TimeDomainFilterBank.filter_series_many(jobs)
        finally:
            on[0] = False
        for (b, x, kw), r2 in zip(jobs, many):
            r1 = b.filter_series(x, **kw)
            for f in r1._fields:
                np.testing.assert_array_equal(getattr(r1, f), getattr(r2, f))

    for r in rows:
        _fill(rng, r, S)
    # Warm-up: every group at once, in both allocations (the most workspaces a batch takes).
    segment([g[0] for g in per_group] * 2)
    warm = len(made)
    pools = len(getattr(ctx, "_pools", []))
    workspaces = sum(len(ex.workspaces) for ex in _vkfollowup._EXECUTORS.values())
    assert workspaces, "the device follow-up path was not taken"
    for seg in range(6):
        for r in rows:
            _fill(rng, r, S)
        segment([int(rng.choice(g)) for g in rng.permutation(np.array(per_group, object))
                 for _ in range(int(rng.integers(1, 3)))])
    assert made[warm:] == [], made[warm:]
    assert len(getattr(ctx, "_pools", [])) == pools
    assert sum(len(ex.workspaces) for ex in _vkfollowup._EXECUTORS.values()) == workspaces


def test_more_batches_than_slots(monkeypatch):
    """A call with more batches than queue slots: a later batch reuses an earlier one's slot,
    fence and recordings. Replayed from its call plan without collecting the earlier batch
    first, the reused fence was waited for although nothing would ever signal it (the second
    segment hung), and the earlier batch's results were overwritten."""
    monkeypatch.setenv("MF_GPU_QUEUE_AHEAD", "2")
    rng, banks = _setup(monkeypatch, nbanks=2, seed=86)
    for b, _, _ in banks:
        for g in b._groups:
            g.plan._series_batch_bytes = 1 << 20          # several batches per call
    S = 1 << 18
    rows = banks[0][0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, (b, _, _) in enumerate(banks)]
    for _ in range(3):
        _fill(rng, rows, S)
        _check(jobs)
