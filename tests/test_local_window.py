"""The gate model draws its signals in a window local to the signal (gatechain.local_window)
and its noise in the window searched. These tests hold the two things that rests on: the
local window is derived from the profile and wide enough, and a plan made on it keeps its
false-dismissal budget on independent draws of the window the search really covers."""
import pathlib
from collections import OrderedDict

import numpy as np
import pytest

from matchedfilter import gatechain as gc
from matchedfilter import gatemodel as gm

DATA = pathlib.Path(__file__).parent / "data"
CHECK_SEED = 1013                     # not the model's (gatechain._SEED)


def _psd(name, n=2048):
    z = np.load(DATA / "psd_model_profiles.npz")
    names = [str(x) for x in z["names"]]
    return z["p%d" % n][names.index(name)].astype(np.float64)


def _shape(name, n=2048):
    from spectral_profiles import make_spectral_profile
    return make_spectral_profile(name, n).astype(np.float64)


PROFILES = {
    "o4 broadband": lambda: (_psd("aLIGOAdVO4T1800545|flow=30|fcut=1024"), 2048),
    "o4 low cutoff": lambda: (_psd("aLIGOAdVO4T1800545|flow=30|fcut=200"), 2048),
    "early flow 20": lambda: (_psd("aLIGOEarlyHighSensitivityP1200087|flow=20|fcut=400"), 2048),
    "a+ n 4096": lambda: (_psd("aLIGOAPlusDesignSensitivityT1800042|flow=20|fcut=1024", 4096), 4096),
    "o2 measured": lambda: (np.load(DATA / "reference_profile_o2_h1l1_2048.npy").astype(np.float64), 2048),
    # the shapes an earlier local window failed on (docs/gate-model.md): side lobes far from the
    # peak, line notches that ring for hundreds of lags, and no localised power at all
    "bimodal": lambda: (_shape("bimodal_resonance"), 2048),
    "notched lines": lambda: (_shape("notched_lines"), 2048),
    "flat": lambda: (np.ones(2048), 2048),
}


@pytest.fixture
def empty_model(monkeypatch):
    for c in ("_SIGNAL_CACHE", "_NOISE_CACHE", "_CAND_CACHE", "_CHOICE_CACHE", "_PLAN_CACHE",
              "_SIGNAL_RECORDS", "_NOISE_RECORDS", "_KEPT", "_LOCAL_WINDOWS"):
        monkeypatch.setattr(gc, c, OrderedDict())
    monkeypatch.setattr(gc, "_SIMILAR", {})
    monkeypatch.setattr(gc, "_SIMILAR_COUNT", {})


def _production(n):
    return (3 * n // 32, n - 3 * n // 32)


def _extent(p, n):
    """The last lag at which the profile's autocorrelation is at least _LOCAL_TAIL of its peak."""
    r = np.abs(np.fft.ifft(gc._norm_profile(p, n)))
    tail = np.flatnonzero(r[1:n // 2 + 1] >= gc._LOCAL_TAIL * r[0])
    return int(tail[-1]) + 1 if tail.size else 1          # a flat profile's is one sample


def _dismissal(p, n, bands, chain, thresholds, snr, window, ndet, alphas=None):
    """The fraction of independent detections in `window` that some tier of `chain` dismisses
    at `thresholds`, and how many detections it rests on."""
    kw = {} if alphas is None else {"alphas": alphas}
    C, F = gc.signal_draws(p, n, bands, snr, ndet, seed=CHECK_SEED, window=window, **kw)
    det = F[:, 0] >= snr
    miss = np.zeros(int(det.sum()), bool)
    for b, t in zip(chain, thresholds):
        miss |= C[det, bands.index(b)] < t
    return float(miss.mean()), int(det.sum())


# ---- the window ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", list(PROFILES))
def test_the_local_window_covers_the_autocorrelation_and_the_coarsest_step(name):
    p, n = PROFILES[name]()
    bands = gc.usable_bands(p, n)
    step = n // min(bands)
    lo, hi = gc.local_window(p, n, bands, (0, n))
    span = hi - lo
    assert span >= gc._LOCAL_LOBES * _extent(p, n)
    assert span >= gc._LOCAL_LOBES * step
    assert span < 2 * gc._LOCAL_LOBES * max(_extent(p, n), step)       # the next power of two, no more
    assert lo % step == 0 and span % step == 0 and (span // step) & (span // step - 1) == 0
    assert abs((lo + hi) - n) <= 2 * step                               # centred in the block
    assert 0 <= lo and hi <= n


def test_a_longer_autocorrelation_takes_a_wider_window():
    """A profile cut off at 200 Hz rings longer than the same spectrum to 1024 Hz, and a
    narrow line longer still: the window follows the profile, not a fixed number of samples."""
    n = 2048
    broad, _ = PROFILES["o4 broadband"]()
    low, _ = PROFILES["o4 low cutoff"]()
    assert _extent(low, n) > _extent(broad, n)
    line = np.zeros(n)
    line[40:44] = 1.0                                    # four bins: rings for hundreds of lags
    bands = gc.usable_bands(broad, n)
    spans = [np.diff(gc.local_window(q, n, bands, (0, n)))[0] for q in (broad, low, line)]
    assert spans[0] <= spans[1] <= spans[2]
    assert spans[2] > spans[0]
    assert spans[2] >= gc._LOCAL_LOBES * _extent(line, n) or spans[2] == n


def test_a_window_no_wider_than_the_local_one_is_used_as_it_is():
    p, n = PROFILES["o4 broadband"]()
    bands = gc.usable_bands(p, n)
    lo, hi = gc.local_window(p, n, bands, (0, n))
    span = hi - lo
    for window in ((100, 100 + span), (100, 100 + span // 2), (7, 9)):
        assert gc.local_window(p, n, bands, window) == window
    assert gc.local_window(p, n, bands, (100, 101 + span)) == (lo, hi)
    assert gc.local_window(p, n, bands, None) == (lo, hi)


# ---- one set of draws for every window ------------------------------------------------------

def test_every_wide_window_of_a_profile_plans_on_one_set_of_signal_draws(empty_model, monkeypatch):
    p, n = PROFILES["o4 broadband"]()
    calls = []
    real = gc._signal_window
    monkeypatch.setattr(gc, "_signal_window", lambda sim, n_, bands, lags: calls.append(lags[:2]) or real(sim, n_, bands, lags))
    chain = (128, 256)
    plans = [gc.chain_thresholds(p, n, 6.0, 1e-2, chain, window=w)
             for w in (_production(n), (0, n), (300, 1500), (64, 1984))]
    assert all(pl is not None for pl in plans)
    bands = gc.usable_bands(p, n)
    assert set(calls) == {gc.local_window(p, n, bands, (0, n))}
    assert len(calls) == 1                               # read once, then held
    # the noise maxima are each window's own, one set a window length
    assert len(gc._NOISE_CACHE) == 4


def test_a_short_window_is_planned_on_its_own_draws(empty_model, monkeypatch):
    p, n = PROFILES["o4 broadband"]()
    calls = []
    real = gc._signal_window
    monkeypatch.setattr(gc, "_signal_window", lambda sim, n_, bands, lags: calls.append(lags[:2]) or real(sim, n_, bands, lags))
    short = (1000, 1064)
    assert gc.chain_thresholds(p, n, 6.0, 1e-2, (128, 256), window=short) is not None
    assert calls == [short]


def test_a_retention_keeps_its_draws_and_not_its_simulation(empty_model):
    """A tier-0 retention's band is simulated again beside the plain simulation. Once its
    draws are read the simulation is let go: only the plain profile's records stay."""
    p, n = PROFILES["o4 broadband"]()
    plain = gc.chain_thresholds(p, n, 6.0, 1e-2, (128, 256), window=_production(n))
    kept = gc.chain_thresholds(p, n, 6.0, 1e-2, (128, 256), window=_production(n), tier0_cluster=(0.97, 1))
    assert plain is not None and kept is not None
    assert tuple(kept["thresholds"]) != tuple(plain["thresholds"])
    sims = list(gc._SIGNAL_RECORDS.values()) + [e[1] for k, es in gc._SIMILAR.items()
                                                if k[0] == "signal-records" for e in es]
    assert sims and all(s.get("alphas") is None for s in sims)
    assert len(gc._SIGNAL_CACHE) == 2                    # the plain profile's draws and the retention's
    # asked again, the retention's plan comes from what is held: nothing is simulated
    before = {id(s): s["rows"] for s in sims}
    gc._PLAN_CACHE.clear()
    again = gc.chain_thresholds(p, n, 6.0, 1e-2, (128, 256), window=(0, n), tier0_cluster=(0.97, 1))
    assert again is not None
    assert {id(s): s["rows"] for s in gc._SIGNAL_RECORDS.values()} == before


# ---- the budget -----------------------------------------------------------------------------

CASES = [(name, snr, kind) for name in PROFILES for snr in (5.5, 8.0)
         for kind in ("production", "whole block", "retention")]


@pytest.fixture(scope="module")
def audited():
    """Every case's plan as the library makes it (the model's choice of chain, or the same
    chain with a tier-0 retention), audited on independent draws of the window searched:
    (dismissal / budget, its standard error from the detections counted)."""
    fd = 1e-2
    ndet = 2 * gc.model_draws(fd)[0]
    out = {}
    for name, snr, kind in CASES:
        p, n = PROFILES[name]()
        bands = gc.usable_bands(p, n)
        window = (0, n) if kind == "whole block" else _production(n)
        best, _ = gc.choose_chain(p, n, snr, fd, window=window)
        chain, alphas = tuple(best["chain"]), None
        plan = best
        if kind == "retention":
            plan = gc.chain_thresholds(p, n, snr, fd, chain, window=window, tier0_cluster=(0.97, 1))
            alphas = tuple(0.97 if b == chain[0] else 1.0 for b in bands)
        dis, count = _dismissal(p, n, bands, chain, plan["thresholds"], snr, window, ndet, alphas)
        out[(name, snr, kind)] = (dis / fd, 1.0 / np.sqrt(fd * count))
    return out


def test_plans_keep_the_budget_on_independent_draws_of_the_real_window(audited):
    """A plan's dismissal on fresh draws has mean fd and, by its fit, at most a 5% chance of
    passing 1.25 fd (gatemodel.plan_tail). Audited where the search really looks -- the whole
    production window or block, not the local window the plan was made on -- the plans hold
    both: their mean is within the budget, and those beyond 1.25 budgets (allowing the
    audit's own three standard errors) are no more than the tail allows."""
    ratios = np.array([r for r, _ in audited.values()])
    errors = np.array([e for _, e in audited.values()])
    assert ratios.mean() <= 1.0 + 3.0 * np.sqrt(np.mean(errors ** 2) / ratios.size + (1.0 / gm.fit_order(1e-2)) / ratios.size)
    beyond = int(np.count_nonzero(ratios > gm._TAIL_RATIO + 3.0 * errors))
    assert beyond <= max(1, int(np.ceil(2 * gm._TAIL_SHARE * ratios.size)))
    worst = max(audited, key=lambda k: audited[k][0])
    assert audited[worst][0] < 1.75, "%s dismisses %.2f budgets" % (worst, audited[worst][0])


@pytest.mark.parametrize("kind", ["production", "whole block", "retention"])
def test_no_kind_of_case_spends_more_than_its_budget_on_average(audited, kind):
    ratios = np.array([r for k, (r, _) in audited.items() if k[2] == kind])
    assert ratios.size == 2 * len(PROFILES)
    assert ratios.mean() <= 1.15


def test_the_budget_holds_at_one_in_a_thousand(empty_model):
    """The same audit at fd = 1e-3, where a plan rests on about 96,000 detections."""
    p, n = PROFILES["o4 low cutoff"]()
    fd, snr = 1e-3, 6.0
    bands = gc.usable_bands(p, n)
    window = _production(n)
    best, _ = gc.choose_chain(p, n, snr, fd, window=window)
    dis, count = _dismissal(p, n, bands, tuple(best["chain"]), best["thresholds"], snr, window,
                            gc.model_draws(fd)[0])
    assert dis / fd <= gm._TAIL_RATIO + 3.0 / np.sqrt(fd * count)


# ---- why the window may not be narrower -----------------------------------------------------

def _plan_on(p, n, bands, chain, snr, fd, signal_window, noise_window):
    nsamp, nsim = gc.model_draws(fd)
    sig, lags = gc.signal_draws(p, n, bands, snr, nsamp, window=signal_window, lags_too=True)
    noise = gc.noise_block_maxima(p, n, bands, nsim=nsim, window=noise_window)
    return gc.plan_chain(sig, noise, bands, list(chain), fd, None, n, snr, lags=lags)


@pytest.mark.parametrize("name", ["o4 broadband", "o4 low cutoff"])
def test_a_window_inside_the_autocorrelation_breaks_the_budget(empty_model, name):
    """The rule is not a convenience. Planned on the signal's own sample -- a window inside
    the autocorrelation -- a gate dismisses several times its budget on the real window,
    while the plan on the local window keeps it, and stays close to the plan made on the
    real window itself."""
    p, n = PROFILES[name]()
    fd, snr, chain = 1e-2, 8.0, (128, 256)
    bands = gc.usable_bands(p, n)
    window = _production(n)
    mid = (window[0] + window[1]) // 2
    ndet = 2 * gc.model_draws(fd)[0]
    narrow = _plan_on(p, n, bands, chain, snr, fd, (mid, mid + 1), window)
    local = _plan_on(p, n, bands, chain, snr, fd, gc.local_window(p, n, bands, window), window)
    exact = _plan_on(p, n, bands, chain, snr, fd, window, window)
    d_narrow, _ = _dismissal(p, n, bands, chain, narrow["thresholds"], snr, window, ndet)
    d_local, count = _dismissal(p, n, bands, chain, local["thresholds"], snr, window, ndet)
    assert d_narrow > 3.0 * fd
    assert d_local <= fd * (gm._TAIL_RATIO + 3.0 / np.sqrt(fd * count))
    np.testing.assert_allclose(local["thresholds"], exact["thresholds"], rtol=0.05)


# ---- the invariant: the local window never sets a gate above the real window's --------------

def _gate_quantiles(p, n, bands, snr, window, ndet=60000):
    """Per band, the 1e-2 and 1e-3 quantiles of the detections' coarse maxima in `window`: a
    one-tier gate at budget fd is that band's fd quantile. One simulation serves every
    window (the draws are a row's own), so two windows' quantiles differ by the window alone."""
    C, F = gc.signal_draws(p, n, bands, snr, ndet, seed=CHECK_SEED, window=window)
    det = F[:, 0] >= snr
    return np.array([[np.quantile(C[det, i], q) for q in (1e-2, 1e-3)] for i in range(len(bands))])


@pytest.mark.parametrize("name", list(PROFILES))
@pytest.mark.parametrize("snr", [5.5, 8.0])
def test_the_local_window_never_sets_a_gate_above_the_real_windows(empty_model, name, snr):
    """A gate set too high dismisses more than its budget; one set lower only passes more
    noise. For every band and both budgets the local window's gate is at or below the gate
    the searched window itself gives (to the 0.3% two samples of the same simulation agree
    to), on the production window and on the whole block. The noise far from the signal,
    which the local window leaves out, lowers a narrow band's gate and never raises one."""
    p, n = PROFILES[name]()
    bands = gc.usable_bands(p, n)
    for window in (_production(n), (0, n)):
        local = gc.local_window(p, n, bands, window)
        assert local != window
        q_local = _gate_quantiles(p, n, bands, snr, local)
        q_real = _gate_quantiles(p, n, bands, snr, window)
        assert np.all(q_local <= q_real * 1.003), (bands, q_local / q_real)


@pytest.mark.parametrize("name", ["o4 broadband", "o4 low cutoff", "o2 measured"])
def test_a_window_of_a_few_samples_sets_gates_too_high(empty_model, name):
    """What the rule guards against, and what the test above would catch: in a window of 8
    samples, inside the autocorrelation, some band's gate lies percents above the real
    window's -- at snr 8 the 128 band's by 6-9%, which is several budgets of dismissal."""
    p, n = PROFILES[name]()
    bands = gc.usable_bands(p, n)
    window = _production(n)
    mid = (window[0] + window[1]) // 2
    assert _extent(p, n) > 8
    ratio = _gate_quantiles(p, n, bands, 8.0, (mid - 4, mid + 4)) / _gate_quantiles(p, n, bands, 8.0, window)
    assert ratio.max() > 1.03


# ---- the direct refine: noise far from the signal ------------------------------------------

def _far_cases():
    return [("o2 measured", 6.0), ("o4 broadband", 6.0), ("bimodal", 6.0)]


@pytest.mark.parametrize("name,snr", _far_cases())
def test_far_noise_drawing_the_refine_away_is_charged_as_often_as_it_happens(empty_model, name, snr):
    """The engine's direct refine looks around the last tier's largest coarse value in the
    window (hmf.c refine_direct_pair). Sometimes that is noise far from the signal, and the
    refine misses the signal. Draws in the local window cannot show it, so the plan pairs
    each with the searched window's noise maximum (gatechain._distances, far=). The share of
    detections it charges that way is at least the share for which, in a simulation of the
    searched window itself, the coarse maximum lies outside the local window -- and not
    several times it."""
    p, n = PROFILES[name]()
    bands = gc.usable_bands(p, n)
    window = _production(n)
    local = gc.local_window(p, n, bands, window)
    ndet = 4 * gc.model_draws(1e-3)[0]
    noise = gc.noise_block_maxima(p, n, bands, nsim=gc.model_draws(1e-3)[1], window=window)
    sig, lags = gc.signal_draws(p, n, bands, snr, ndet, window=local, lags_too=True)
    (C, F), (fat, cat) = gc.signal_draws(p, n, bands, snr, ndet, seed=CHECK_SEED, window=window, lags_too=True)
    det = F[:, 0] >= snr
    counted = 0
    for b in (128, 256, 512):
        col, R = bands.index(b), n // b
        charged = gc._distances(sig, lags, bands, (b,), snr, n, noise) >= b
        happens = np.abs(fat[det] - cat[det, col]) > (local[1] - local[0]) + 2 * R
        # without the pairing the local draws show none of them: their coarse maxima lie in
        # the local window, or one coarse sample past an end of it (as the engine searches)
        plain = gc._distances(sig, lags, bands, (b,), snr, n)
        assert np.count_nonzero(plain * R > (local[1] - local[0]) + 2 * R) == 0
        if happens.sum() < 30:
            continue                                   # too rare in this band to count
        counted += 1
        slack = 3.0 * np.sqrt(happens.sum()) / det.sum()
        assert charged.mean() >= happens.mean() - slack, (b, charged.mean(), happens.mean())
        assert charged.mean() <= 3.0 * happens.mean() + slack, (b, charged.mean(), happens.mean())
    assert counted >= 1


@pytest.mark.parametrize("name,snr", _far_cases())
def test_a_plan_with_a_direct_refine_keeps_the_budget_on_the_real_window(empty_model, name, snr):
    """The tiers and the direct refine's window share one budget (plan_chain). Audited on
    independent draws of the searched window -- a detection lost if a tier dismisses it or
    its fine maximum lies beyond the half-width from the last tier's coarse maximum, wherever
    in the window that is -- the plan keeps it."""
    import json
    p, n = PROFILES[name]()
    fd = 1e-3
    bands = gc.usable_bands(p, n)
    window = _production(n)
    rec = json.loads((DATA / "cost_model_2048_zen5.json").read_text())
    direct = gc.CostModel.from_dict(rec["model"]).unscreened().with_direct(0.09 * 256 + 4.0)
    ndet = 4 * gc.model_draws(fd)[0]
    (C, F), (fat, cat) = gc.signal_draws(p, n, bands, snr, ndet, seed=CHECK_SEED, window=window, lags_too=True)
    det = F[:, 0] >= snr
    windows = 0
    for chain in ((256,), (128, 256), (256, 512)):
        pl = gc.chain_thresholds(p, n, snr, fd, chain, cost=direct, window=window)
        lost = np.zeros(int(det.sum()), bool)
        for b, t in zip(chain, pl["thresholds"]):
            lost |= C[det, bands.index(b)] < t
        if pl["halfwidth"] is not None:
            windows += 1
            lost |= np.abs(fat[det] - cat[det, bands.index(chain[-1])]) / (n // chain[-1]) > pl["halfwidth"]
        assert lost.mean() <= fd * (gm._TAIL_RATIO + 3.0 / np.sqrt(fd * det.sum())), (chain, lost.mean() / fd)
    assert windows >= 1, "no chain of the case was planned with a direct refine"


def test_a_retentions_draws_pair_with_the_plain_ones_across_profiles_alike(empty_model):
    """A one-tier chain behind a tier-0 retention is planned on the retention's coarse
    maxima and the plain draws' lags, row for row, so both must be one simulation's. Here a
    second profile, alike enough to borrow results (_similar_get) but simulated on its own
    because the first one's simulation has been let go, is planned after the first. Every
    plan is made, and the second profile's on its own simulation, whose draws number
    otherwise. (An earlier version held a retention's draws for profiles alike apart from the
    plain ones'; when only one of the two was still held it paired two simulations of
    different lengths, and a worker of the showcase search failed on it.)"""
    a = np.load(DATA / "reference_profile_o2_h1l1_2048.npy").astype(np.float64)
    n = 2048
    rng = np.random.default_rng(3)
    b = a * (1.0 + 1e-2 * rng.standard_normal(n))
    bands = gc.usable_bands(a, n)
    lengths = []
    for p in (a, b):
        best, plans = gc.choose_chain(p, n, 6.0, 1e-3, window=_production(n),
                                      tier0_clusters={128: (0.97, 1), 256: (0.97, 1)})
        assert best is not None
        assert any(len(pl["chain"]) == 1 for pl in plans)
        lengths.append(sorted({v[0][0].shape[0] for v in gc._SIGNAL_CACHE.values()}))
        # the first profile's simulation and draws are let go; what is held for profiles
        # alike stays, as when a long job's caches turn over
        gc._SIGNAL_CACHE.clear()
        gc._SIGNAL_RECORDS.clear()
        gc._CHOICE_CACHE.clear()
        for k in [k for k in gc._SIMILAR if k[0] in ("signal-records", "choice")]:
            del gc._SIMILAR[k]
    assert lengths[0] != lengths[1], "the two profiles' simulations kept the same draws: no test"
