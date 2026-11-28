"""Every-template CPU calls run as compiled leaf steps (_batches._compile_steps and
_core.HMFTable): gated steps for a hierarchical bank's calls, flat steps for a flat bank's and
for calls below a hierarchical bank's threshold. The steps of a call shape are compiled once and
reused, a window list given again as a new list reuses them, and their peaks are, to the bit and
in order, those of the call-at-a-time path (each template group's plan run_series, assembled in
Python)."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank, _batches


@pytest.fixture(autouse=True)
def _decisions_fixed(monkeypatch):
    """One chain and screen per plan, whichever path runs it."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")


def _profile(n_bins=16385, delta_f=1.0 / 16.0):
    f = np.arange(n_bins, dtype=np.float64) * delta_f
    return np.where((f >= 24.0) & (f <= 850.0), np.maximum(f, 1.0) ** (-7.0 / 3.0), 0.0), delta_f


def _bank(rng, n_templates=20, complex_taps=False, binsize=None, engine="hier"):
    counts = rng.integers(150, 1500, size=n_templates)
    taps = np.zeros((n_templates, int(counts.max())),
                    dtype=np.complex64 if complex_taps else np.float32)
    for i, c in enumerate(counts):
        t = np.arange(c) / 2048.0
        phase = 2 * np.pi * ((30 + 7 * i) * t + 0.5 * (150 + 11 * i) * t * t)
        row = (np.exp(1j * phase) if complex_taps else np.cos(phase)) * np.hanning(c)
        taps[i, :c] = row / np.linalg.norm(row)
    bank = TimeDomainFilterBank(taps, counts, engine=engine, threshold=3.6,
                                false_dismissal=1e-2, device="cpu", binsize=binsize)
    w, df = _profile()
    bank.set_reference(w, delta_f=df)
    return bank


def _same(a, b):
    for field in a._fields:
        x, y = getattr(a, field), getattr(b, field)
        assert x.dtype == y.dtype and x.shape == y.shape, field
        assert x.tobytes() == y.tobytes(), field


def test_a_call_shape_compiles_once_and_a_new_window_list_reuses_it(monkeypatch):
    rng = np.random.default_rng(5)
    bank = _bank(rng)
    x = rng.standard_normal(1 << 17).astype(np.float32)
    compiled = []
    compile_steps = _batches._compile_steps
    monkeypatch.setattr(_batches, "_compile_steps",
                        lambda *a, **k: compiled.append(1) or compile_steps(*a, **k))
    first = bank.filter_series(x, windows=[(4000, 50000), (60000, 120000)])
    again = bank.filter_series(x, windows=[(4000, 50000), (60000, 120000)])
    assert len(compiled) == 1
    _same(first, again)
    bank.filter_series(x, windows=[(4000, 50000), (60000, 110000)])
    assert len(compiled) == 2
    bank.filter_series(x.copy(), windows=[(4000, 50000), (60000, 120000)])
    assert len(compiled) == 2                   # another series of the same kind: no compile


def test_compiled_steps_give_the_call_at_a_time_peaks(monkeypatch):
    """Every template group, bin count, window list and series kind of a batch, against the
    same calls made one at a time through each plan's run_series."""
    rng = np.random.default_rng(11)
    real_bank, lane_bank = _bank(rng, binsize=700), _bank(rng, complex_taps=True)
    S = 1 << 17
    x = rng.standard_normal(S).astype(np.float32)
    z = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
    jobs = [(real_bank, x, dict(windows=[(3000, 41000), (47000, 101000)], binsize=300)),
            (real_bank, x[::-1].copy(), dict()),
            (lane_bank, z, dict(windows=slice(9000, 120000))),
            (lane_bank, z.real, dict(windows=[(20000, 30000), (31000, 90000)], binsize=512)),
            (real_bank, x, dict(threshold=4.0))]
    got = TimeDomainFilterBank.filter_series_many(jobs)
    assert sum(len(r.snr) for r in got) > 50
    monkeypatch.setattr(_batches, "_cpu_sparse_batch", lambda *a, **k: set())
    want = [bank.filter_series(series, **kw) for bank, series, kw in jobs]
    for g, w in zip(got, want):
        _same(g, w)


def test_a_plans_batch_times_from_table_runs_are_its_own(monkeypatch):
    """The batch times the step table records for a plan (a gated call's steps) are in its
    performance_stats, as if each had been recorded when it ran: folded into a plan that had
    recorded batches of its own, the stats are those of recording them all one by one, ring
    of the last _MAX_BATCH_TIMINGS included."""
    from matchedfilter import MatchedFilter
    times = [(k % 37 + 1) / 1024.0 for k in range(300)]
    one_by_one, folded = MatchedFilter(64), MatchedFilter(64)
    for f in (one_by_one, folded):
        for t in times[:20]:
            f._record_batch_time(t)
    for t in times[20:]:
        one_by_one._record_batch_time(t)
    pending = folded._step_stats
    for k, t in enumerate(times[20:]):
        pending[6 + k % MatchedFilter._MAX_BATCH_TIMINGS] = t
        pending[1] += t
        pending[2] = t if k == 0 else min(pending[2], t)
        pending[3] = t if k == 0 else max(pending[3], t)
        pending[0] = k + 1
    assert folded.performance_stats == one_by_one.performance_stats

    # a gated call: each of its steps one batch of its plan
    bank = _bank(np.random.default_rng(12))
    x = np.random.default_rng(13).standard_normal(1 << 17).astype(np.float32)
    plans = {id(g.plan): g.plan for g in bank._groups}
    before = {k: p.performance_stats["timed_calls"] for k, p in plans.items()}
    bank.filter_series(x, windows=[(5000, 60000), (70000, 120000)])
    after = {k: p.performance_stats["timed_calls"] for k, p in plans.items()}
    assert all(after[k] > before[k] for k in plans)


def test_banks_with_compiled_steps_are_freed_without_the_cyclic_collector():
    """The first bank of a batch keeps the batch's compiled steps; the steps must not hold
    the banks, or a dead leaf bank waits in a reference cycle for the collector (in a PyCBC
    job, hundreds of MB of dead banks at a time)."""
    import gc
    import weakref
    rng = np.random.default_rng(14)
    first, second = _bank(rng), _bank(rng, complex_taps=True)
    x = rng.standard_normal(1 << 17).astype(np.float32)
    got = TimeDomainFilterBank.filter_series_many(
        [(first, x, dict(windows=[(4000, 50000)])), (second, x, dict())])
    assert sum(len(r.snr) for r in got) > 0
    assert len(first.__dict__["_compiled_steps"]) == 1
    refs = [weakref.ref(first), weakref.ref(second)]
    gc.disable()
    try:
        del first, second, got
        assert [r() is None for r in refs] == [True, True]
    finally:
        gc.enable()


def test_flat_steps_give_the_call_at_a_time_peaks(monkeypatch):
    """A flat bank's calls and a hierarchical bank's calls below its threshold, of every series
    kind (complex, real, a real lane of a complex series), with and without window bins, run
    as flat steps of the table (none goes through a plan's run_series) and give the peaks of
    the same calls made one at a time through each group's ungated plan."""
    from matchedfilter import time_domain
    rng = np.random.default_rng(15)
    flat_bank, hier_bank = _bank(rng, engine="flat", binsize=400), _bank(rng, complex_taps=True)
    S = 1 << 17
    x = rng.standard_normal(S).astype(np.float32)
    z = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
    jobs = [(flat_bank, z, dict(windows=[(3000, 41000), (47000, 101000)], threshold=4.0)),
            (flat_bank, x, dict(binsize=300, threshold=3.0)),
            (hier_bank, z.imag, dict(windows=slice(9000, 120000), threshold=2.5)),
            (hier_bank, z, dict(windows=[(20000, 30000), (31000, 90000)], binsize=512,
                                threshold=0.0)),
            (hier_bank, x, dict(windows=[(20000, 70000)], threshold=3.0))]
    peaks_job = time_domain._PeaksJob
    general = []
    monkeypatch.setattr(time_domain, "_PeaksJob",
                        lambda *a: general.append(1) or peaks_job(*a))
    got = TimeDomainFilterBank.filter_series_many(jobs)
    assert not general                          # no call took filter_series' general loop
    assert [len(r.snr) > 0 for r in got] == [True] * len(jobs)
    flat_steps = [len(c.flat_plans) for c in flat_bank.__dict__["_compiled_steps"].values()]
    assert flat_steps and all(n > 0 for n in flat_steps)
    monkeypatch.setattr(_batches, "_cpu_sparse_batch", lambda *a, **k: set())
    want = [bank.filter_series(series, **kw) for bank, series, kw in jobs]
    for g, w in zip(got, want):
        _same(g, w)


def test_flat_steps_compile_once_and_free_their_bank_without_the_collector(monkeypatch):
    """A flat bank's call shape compiles once; its plans' stats count the steps' batches; and
    the bank, which keeps the steps, dies without the cyclic collector."""
    import gc
    import weakref
    rng = np.random.default_rng(16)
    bank = _bank(rng, engine="flat")
    x = rng.standard_normal(1 << 17).astype(np.float32)
    compiled = []
    compile_steps = _batches._compile_steps
    monkeypatch.setattr(_batches, "_compile_steps",
                        lambda *a, **k: compiled.append(1) or compile_steps(*a, **k))
    plans = {id(g.plan): g.plan for g in bank._groups}
    before = {k: p.performance_stats["timed_calls"] for k, p in plans.items()}
    first = bank.filter_series(x, windows=[(4000, 50000)], threshold=3.0)
    again = bank.filter_series(x, windows=[(4000, 50000)], threshold=3.0)
    assert len(compiled) == 1 and len(first.snr) > 0
    _same(first, again)
    after = {k: p.performance_stats["timed_calls"] for k, p in plans.items()}
    assert all(after[k] == before[k] + 2 for k in plans)
    ref = weakref.ref(bank)
    gc.disable()
    try:
        del bank, plans
        assert ref() is None
    finally:
        gc.enable()
