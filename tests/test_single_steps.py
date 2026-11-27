"""Single-template calls run as single-template steps of the step table (_core.HMFTable):
a template group's step is compiled once and every call binds its template, series, windows,
bin size and threshold; the group's store of template spectra gives the same peaks, to the
bit, whether a spectrum is made, found or made again after its slot was given up; and the
peaks are those of the follow-up path the steps replaced (td_followup_batch, 3ec9157d)."""
import hashlib

import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank, _batches, _core


@pytest.fixture(autouse=True)
def _decisions_fixed(monkeypatch):
    """One chain and screen per plan, whichever path runs it."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")


def _bank(engine="hier", fft_lengths=None):
    """A bank of 24 complex chirps, whose lengths put them in more than one template group
    unless one block length is given."""
    rng = np.random.default_rng(41)
    counts = rng.integers(150, 1500, size=24)
    taps = np.zeros((24, int(counts.max())), dtype=np.complex64)
    for i, c in enumerate(counts):
        t = np.arange(c) / 2048.0
        row = np.exp(2j * np.pi * ((30 + 7 * i) * t + 0.5 * (150 + 11 * i) * t * t)) * np.hanning(c)
        taps[i, :c] = row / np.linalg.norm(row)
    bank = TimeDomainFilterBank(taps, counts, engine=engine, threshold=3.6, false_dismissal=1e-2,
                                device="cpu", binsize=2048, fft_lengths=fft_lengths)
    if engine == "hier":
        f = np.arange(16385) / 16.0
        bank.set_reference(np.where((f >= 24) & (f <= 850), np.maximum(f, 1.0) ** (-7 / 3), 0.0),
                           delta_f=1.0 / 16.0)
    return bank


def _series():
    """A complex series, and its real lane and a contiguous real copy of it."""
    rng = np.random.default_rng(42)
    x = (rng.standard_normal(1 << 18) + 1j * rng.standard_normal(1 << 18)).astype(np.complex64)
    return x, x.real, np.ascontiguousarray(x.real)


def _calls():
    """Follow-ups of every kind a step binds: narrow windows (time-domain correlation) and
    wide ones (transforms), a window list, the whole series, bin sizes, thresholds, the three
    series kinds, and templates given again."""
    out = []
    for k in range(30):
        c = 20000 + 7000 * k
        windows = (slice(c - 40, c + 40) if k % 4 == 0 else
                   [(c - 9000, c - 2000), (c - 1500, c + 9000)] if k % 4 == 1 else
                   None if k == 2 else slice(c - 10250, c + 10250))
        out.append((k % 3, dict(windows=windows, binsize=(205, 61, None)[k % 3],
                                threshold=(0.0, 2.5, None)[k % 5 % 3],
                                template_index=(3 * k) % 24 if k < 20 else 5)))
    return out


def _digest(results):
    h = hashlib.sha256()
    for r in results:
        for field in r._fields:
            h.update(np.ascontiguousarray(getattr(r, field)).tobytes())
    return h.hexdigest()


def _same(a, b):
    for field in a._fields:
        x, y = getattr(a, field), getattr(b, field)
        assert x.dtype == y.dtype and x.tobytes() == y.tobytes(), field


def test_a_template_or_window_is_bound_not_compiled(monkeypatch):
    """A group's step is compiled at its first call; calls with other templates of the group,
    other windows, bin sizes, thresholds and series run it, each binding its own. A batch over
    two groups compiles one table of two steps, which a batch over the same groups with other
    templates and windows runs again."""
    made, runs = [], []
    table_type = _core.HMFTable

    class CountedTable:
        """_core.HMFTable, counting the tables made (by their single-template steps) and the
        calls each run binds."""
        def __init__(self, *args):
            self.table = table_type(*args)
            made.append(len(args[3]))

        def run(self, series, calls=()):
            runs.append(len(calls))
            return self.table.run(series, calls)
    monkeypatch.setattr(_core, "HMFTable", CountedTable)
    bank = _bank("flat")
    series = _series()
    groups = [g for g in bank._groups if len(g.template_indices) > 1]
    assert len(groups) >= 2, "the bank must have two groups of several templates"
    g, other = groups[0], groups[1]
    for k, ti in enumerate(g.template_indices):
        bank.filter_series(series[k % 3], windows=slice(30000 + 900 * k, 52000 + 700 * k),
                           binsize=(205, 61)[k % 2], threshold=(0.0, 2.0)[k % 2],
                           template_index=int(ti))
    assert made == [1]
    assert runs == [1] * len(g.template_indices)
    table = g._single_table
    bank.filter_series(series[0], windows=[(1000, 9000), (12000, 30000)], binsize=64,
                       threshold=0.0, template_index=int(g.template_indices[-1]))
    assert g._single_table is table and made == [1]

    # a batch over two groups: one table, run again by another batch over the same groups
    for k in range(2):
        jobs = [(bank, series[0], dict(windows=slice(40000 + 5000 * k, 60000 + 5000 * k),
                                       binsize=205, threshold=0.0,
                                       template_index=int(grp.template_indices[k])))
                for grp in (g, other)]
        TimeDomainFilterBank.filter_series_many(jobs)
    assert made == [1, 2]
    assert runs[-2:] == [2, 2]


def test_the_spectrum_store_does_not_change_the_peaks():
    """A call gives the same peaks to the bit whether its template's spectrum is made (a cold
    store), found in the group's store, or made again after its slot went to another template
    (a store of two slots); and a run with more templates than slots makes the rest in the
    scratch, with the peaks of a store that holds them all."""
    bank = _bank()
    x = _series()[0]
    g = max(bank._groups, key=lambda grp: len(grp.template_indices))
    rows = range(min(6, len(g.template_indices)))
    assert len(rows) > 2, "the group must have more templates than the small store has slots"
    calls = [(0, x, r, (20000 + 3000 * r, 45000 + 3000 * r), 205, True, 0.0) for r in rows]
    step = _batches._single_step(bank, g)

    def stored(slots):
        """The group's step with an empty store of its own, of this many slots."""
        nt = len(g.template_indices)
        index = np.zeros(nt + 3 * slots + 2, np.int64)
        index[:nt + slots] = -1
        return step[:8] + (index, np.empty((slots, g.n), np.complex64))
    full = len(rows)
    cold = [_core.HMFTable((), (), 0, (stored(full),)).run((), (c,)) for c in calls]
    warm = _core.HMFTable((), (), 0, (stored(full),))
    small = _core.HMFTable((), (), 0, (stored(2),))
    for _ in range(2):
        for c, want in zip(calls, cold):
            assert warm.run((), (c,))[:6] == want[:6]
            assert small.run((), (c,))[:6] == want[:6]

    # one run of every call: two slots and the scratch, against the full store
    together = _core.HMFTable((), (), 0, (stored(full),)).run((), calls)
    assert _core.HMFTable((), (), 0, (stored(2),)).run((), calls)[:6] == together[:6]


def test_single_template_peaks_are_the_follow_up_paths(monkeypatch):
    """The peaks of single-template calls, one at a time and as one batch, on an ungated bank
    of three block lengths and a gated bank of one, are those the follow-up path the steps
    replaced gave (td_followup_batch at 3ec9157d), to the bit and in order: compared as digests
    recorded there, on the kernel backend they were recorded with. (A gated bank's block
    lengths are a measured choice, so it is given one.)"""
    if _core.backend() != "AVX3_DL":
        pytest.skip("digests recorded with the AVX3_DL backend; this one is %s" % _core.backend())
    want = {"hier": ("3f03c1564e63096a626b8b655893e8db1158249afe112380f4d459a8ba65b7eb",
                     "3f03c1564e63096a626b8b655893e8db1158249afe112380f4d459a8ba65b7eb"),
            "flat": ("1829df09dac94d291a06d4d76097de8d7c2775e85940a14dfdc3cf5fa210e5eb",
                     "1829df09dac94d291a06d4d76097de8d7c2775e85940a14dfdc3cf5fa210e5eb")}
    series = _series()
    for engine, (one, many) in want.items():
        bank = _bank(engine, [4096] if engine == "hier" else None)
        calls = _calls()
        assert _digest([bank.filter_series(series[s], **kw) for s, kw in calls]) == one, engine
        jobs = [(bank, series[s], kw) for s, kw in calls]
        assert _digest(TimeDomainFilterBank.filter_series_many(jobs)) == many, engine
