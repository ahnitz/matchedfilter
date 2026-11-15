"""The planner's signal table drawn from the samples' joint law (matchedfilter._signal_law,
MF_SIGNAL_LAW=1) against the simulation it stands in for: the bands' dismissal curves, a
chain's joint dismissal, a retention, where the maxima lie, and the plan that comes out."""
import pathlib
from collections import OrderedDict

import numpy as np
import pytest

from matchedfilter import gatechain as gc

DATA = pathlib.Path(__file__).parent / "data"
N, SNR, COUNT = 2048, 6.0, 300000


def _profile():
    p = np.load(DATA / "reference_profile_o2_h1l1_2048.npy").astype(np.float64)
    return p / p.sum()


@pytest.fixture
def empty_model(monkeypatch):
    for c in ("_SIGNAL_CACHE", "_NOISE_CACHE", "_CAND_CACHE", "_CHOICE_CACHE", "_PLAN_CACHE",
              "_SIGNAL_RECORDS", "_NOISE_RECORDS", "_KEPT", "_LOCAL_WINDOWS"):
        monkeypatch.setattr(gc, c, OrderedDict())
    monkeypatch.setattr(gc, "_SIMILAR", {})
    monkeypatch.setattr(gc, "_SIMILAR_COUNT", {})


def _table(monkeypatch, law, p, bands, window, alphas=None, seed=4242, count=COUNT):
    """The detections of one table: (C, F, fine lags, coarse lags), from the law or simulated."""
    monkeypatch.setenv("MF_SIGNAL_LAW", "1" if law else "0")
    for c in (gc._SIGNAL_CACHE, gc._SIGNAL_RECORDS, gc._SIMILAR):
        c.clear()
    (C, F), (fat, cat) = gc._signal_table(p, N, bands, SNR, count, seed=seed, window=window,
                                          lags_too=True, alphas=alphas)
    if isinstance(C, gc._Beside):
        C, cat = C.full(), cat.full()
    det = np.asarray(F[:, 0]) >= SNR
    return (np.asarray(C)[det], np.asarray(F[:, 0])[det], np.asarray(fat)[det].astype(np.int64),
            np.asarray(cat)[det].astype(np.int64))


@pytest.fixture
def setting(empty_model):
    p = _profile()
    bands = gc.usable_bands(p, N)
    return p, bands, gc.local_window(p, N, bands, None)


def test_each_bands_dismissal_curve_is_the_simulations(setting, monkeypatch):
    """At the thresholds where the simulation dismisses 0.1%, 1% and 10% of detections, the
    law's table dismisses the same shares, to the counts' own scatter."""
    p, bands, window = setting
    sim = _table(monkeypatch, False, p, bands, window)[0]
    law = _table(monkeypatch, True, p, bands, window)[0]
    for i in range(len(bands)):
        for share, slack in ((1e-3, 0.35), (1e-2, 0.12), (1e-1, 0.04)):
            got = float((law[:, i] < np.quantile(sim[:, i], share)).mean())
            assert abs(got / share - 1.0) < slack, (bands[i], share, got)


def test_a_chains_dismissal_needs_nothing_more(setting, monkeypatch):
    """Two and three bands at once: the draws that some tier of a chain dismisses are the
    simulation's share, from the same table as the single bands."""
    p, bands, window = setting
    sim = _table(monkeypatch, False, p, bands, window)[0]
    law = _table(monkeypatch, True, p, bands, window)[0]
    for chain in ((0, 1), (1, 2), (0, 1, 2), (1, 2, 3)):
        lost_sim, lost_law = np.zeros(len(sim), bool), np.zeros(len(law), bool)
        for c in chain:
            t = np.quantile(sim[:, c], 5e-3)
            lost_sim |= sim[:, c] < t
            lost_law |= law[:, c] < t
        assert abs(lost_law.mean() / lost_sim.mean() - 1.0) < 0.12, chain


def test_a_retention_is_the_simulations(setting, monkeypatch):
    """A band under a shared screener's retention keeps that share of the signal and of the
    noise it has in common with the rest: its column is the simulation's, the others and
    the fine maxima are the plain table's own arrays."""
    p, bands, window = setting
    alphas = (1.0, 0.97) + (1.0,) * (len(bands) - 2)
    sim = _table(monkeypatch, False, p, bands, window, alphas=alphas)[0]
    law = _table(monkeypatch, True, p, bands, window, alphas=alphas)[0]
    plain = _table(monkeypatch, True, p, bands, window)[0]
    for share, slack in ((1e-2, 0.15), (1e-1, 0.05)):
        got = float((law[:, 1] < np.quantile(sim[:, 1], share)).mean())
        assert abs(got / share - 1.0) < slack, (share, got)
    assert float(np.median(law[:, 1])) < float(np.median(plain[:, 1]))      # it lowers the band
    # held beside the plain draws: row for row the same draws, one column of its own
    monkeypatch.setenv("MF_SIGNAL_LAW", "1")
    (C, F), _ = gc._signal_table(p, N, bands, SNR, COUNT, seed=4242, window=window, lags_too=True,
                                 alphas=alphas)
    (Cp, Fp), _ = gc._signal_table(p, N, bands, SNR, COUNT, seed=4242, window=window, lags_too=True)
    assert isinstance(C, gc._Beside) and C.plain is Cp and sorted(C.own) == [1]


def test_the_maxima_lie_where_the_simulations_do(setting, monkeypatch):
    """The refine's half-width is read from how far a band's coarse maximum lies from the fine
    one: the share of draws more than one and more than two coarse lags apart."""
    p, bands, window = setting
    sim = _table(monkeypatch, False, p, bands, window)
    law = _table(monkeypatch, True, p, bands, window)
    for i, b in enumerate(bands[1:], 1):               # the half-width is the last band's
        step = N // b
        for reach in (1, 2):
            far_sim = float((np.abs(sim[2] - sim[3][:, i]) > reach * step).mean())
            far_law = float((np.abs(law[2] - law[3][:, i]) > reach * step).mean())
            assert abs(far_law - far_sim) < max(0.35 * far_sim, 4e-4), (b, reach, far_sim, far_law)


def test_the_tables_contract(setting, monkeypatch):
    p, bands, window = setting
    monkeypatch.setenv("MF_SIGNAL_LAW", "1")
    (C, F), (fat, cat) = gc._signal_table(p, N, bands, SNR, 5000, seed=7, window=window, lags_too=True)
    assert C.shape == (5000, len(bands)) and C.dtype == np.float32 and F.shape == C.shape
    assert fat.shape == (5000,) and cat.shape == C.shape and fat.dtype == cat.dtype == np.int32
    assert np.all(F[:, 0] >= SNR)                       # every row is a detection
    assert not C.flags.writeable and not fat.flags.writeable
    assert window[0] <= fat.min() and fat.max() < window[1]
    for i, b in enumerate(bands):
        assert np.all(cat[:, i] % (N // b) == 0)        # a coarse lag times the band's step
    again = gc._signal_table(p, N, bands, SNR, 5000, seed=7, window=window)
    gc._SIGNAL_CACHE.clear()
    fresh = gc._signal_table(p, N, bands, SNR, 5000, seed=7, window=window)
    other = gc._signal_table(p, N, bands, SNR, 5000, seed=8, window=window)
    assert np.array_equal(again[0], C) and np.array_equal(fresh[0], C)       # the seed's draws
    assert not np.array_equal(other[0], C)


def test_the_plan_is_the_simulations(setting, monkeypatch):
    """Planned on the law's table: the simulation's chain, thresholds within a tenth, and a
    cost within what a table's own draws move it (3-4% from seed to seed for either)."""
    p, bands, window = setting
    cost = gc.CostModel(
        N, {64: 30.7, 128: 57.5, 256: 140.1, 512: 378.3, 1024: 876.6},
        {b: [(0.0098, 600.0 * b / 128), (0.104, 300.0 * b / 128)] for b in (64, 128, 256, 512, 1024)},
        [(0.0098, 3388.0), (0.104, 2889.0)], block=3306.0)
    plans = {}
    for law in (False, True):
        monkeypatch.setenv("MF_SIGNAL_LAW", "1" if law else "0")
        for c in (gc._SIGNAL_CACHE, gc._SIGNAL_RECORDS, gc._SIMILAR, gc._CHOICE_CACHE, gc._PLAN_CACHE,
                  gc._CAND_CACHE, gc._KEPT, gc._NOISE_CACHE):
            c.clear()
        plans[law] = gc.choose_chain(p, N, SNR, 1e-3, cost=cost, max_tiers=3, ntemplates=96)[0]
    assert tuple(plans[True]["chain"]) == tuple(plans[False]["chain"])
    assert np.max(np.abs(np.array(plans[True]["thresholds"]) - np.array(plans[False]["thresholds"]))) < 0.1
    assert abs(plans[True]["cost"] / plans[False]["cost"] - 1.0) < 0.10


def test_a_window_too_wide_for_the_law_is_simulated(setting, monkeypatch):
    """The law takes the samples away from the signal as independent noise, so it stands in
    only for a window of at most half the block (the planner's own window, where a profile's
    correlations die out inside the block). A wider window is simulated: the whole block,
    which is also what the planner asks for under a profile whose correlations span it."""
    from matchedfilter import _signal_law
    p, bands, window = setting
    drawn, simulated = [], []
    law, simulate = _signal_law.signal_table, gc._simulate
    monkeypatch.setattr(_signal_law, "signal_table",
                        lambda *a, **k: drawn.append(a[7][:2]) or law(*a, **k))
    monkeypatch.setattr(gc, "_simulate", lambda *a, **k: simulated.append(a[1]) or simulate(*a, **k))
    monkeypatch.setenv("MF_SIGNAL_LAW", "1")
    assert gc._law_applies(N, window) and not gc._law_applies(N, (0, N))
    assert not gc._law_applies(N, (N // 4 - 1, 3 * N // 4))            # just over half
    gc._signal_table(p, N, bands, SNR, 2000, seed=3, window=window)
    assert drawn == [window] and not simulated
    gc._signal_table(p, N, bands, SNR, 2000, seed=3, window=(0, N))
    assert drawn == [window] and simulated
    # a steep red profile's own window is the whole block
    red = 1.0 / np.arange(1, N + 1) ** 2.0
    red[N // 2:] = 0.0
    red /= red.sum()
    wide = gc.local_window(red, N, gc.usable_bands(red, N), None)
    assert not gc._law_applies(N, wide)
    monkeypatch.setenv("MF_SIGNAL_LAW", "0")
    assert not gc._law_applies(N, window)


def test_three_profiles_planned_in_turn_are_drawn_once_each(setting, monkeypatch):
    """A job's banks alternate between profiles (two top templates' banks under two detectors
    plan on three that are not alike). Three profiles' draws are held, so going round them
    again draws nothing and reads the same tables."""
    from matchedfilter import _signal_law
    p, bands, window = setting
    monkeypatch.setattr(_signal_law, "_DRAWS", OrderedDict())
    drawn = []
    draw = _signal_law._draw
    monkeypatch.setattr(_signal_law, "_draw", lambda *a, **k: drawn.append(1) or draw(*a, **k))
    monkeypatch.setenv("MF_SIGNAL_LAW", "1")
    tilt = np.linspace(0.3, 3.0, N)
    profiles = [p, p * tilt / (p * tilt).sum(), p / tilt / (p / tilt).sum()]
    tables = []
    for _ in range(2):
        for q in profiles:
            for c in (gc._SIGNAL_CACHE, gc._SIGNAL_RECORDS):
                c.clear()                               # the table is read from the held draws
            tables.append(np.array(gc._signal_table(q, N, bands, SNR, 3000, seed=5, window=window)[0]))
    assert len(drawn) == 3
    for first, again in zip(tables[:3], tables[3:]):
        assert np.array_equal(first, again)
    assert not np.array_equal(tables[0], tables[1]) and not np.array_equal(tables[0], tables[2])
