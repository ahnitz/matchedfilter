"""The gate model draws its signals in a window local to the signal (_gatedraws.local_window)
and its noise in the window searched. These tests hold the two things that rests on: the
local window is derived from the profile and wide enough, and a plan made on it keeps its
false-dismissal budget on independent draws of the window the search really covers."""
import pathlib
from collections import OrderedDict

import numpy as np
import pytest

from matchedfilter import gatechain as gc
from matchedfilter import _gatedraws as gd
from matchedfilter import gatemodel as gm

DATA = pathlib.Path(__file__).parent / "data"
CHECK_SEED = 1013                     # not the model's (_gatedraws._SEED)


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
    # the shapes an earlier local window failed on: side lobes far from the
    # peak, line notches that ring for hundreds of lags, and no localised power at all
    "bimodal": lambda: (_shape("bimodal_resonance"), 2048),
    "notched lines": lambda: (_shape("notched_lines"), 2048),
    "flat": lambda: (np.ones(2048), 2048),
}


@pytest.fixture
def empty_model(monkeypatch):
    for c in ("_SIGNAL_CACHE", "_NOISE_CACHE", "_CAND_CACHE", "_CHOICE_CACHE", "_PLAN_CACHE",
              "_SIGNAL_RECORDS", "_NOISE_RECORDS", "_KEPT", "_LOCAL_WINDOWS"):
        monkeypatch.setattr(gd if hasattr(gd, c) else gc, c, OrderedDict())
    monkeypatch.setattr(gd, "_SIMILAR", {})
    monkeypatch.setattr(gd, "_SIMILAR_COUNT", {})


def _production(n):
    return (3 * n // 32, n - 3 * n // 32)


def _extent(p, n):
    """The last lag at which the profile's autocorrelation is at least _LOCAL_TAIL of its peak."""
    r = np.abs(np.fft.ifft(gd._norm_profile(p, n)))
    tail = np.flatnonzero(r[1:n // 2 + 1] >= gd._LOCAL_TAIL * r[0])
    return int(tail[-1]) + 1 if tail.size else 1          # a flat profile's is one sample


def _dismissal(p, n, bands, chain, thresholds, snr, window, ndet, alphas=None):
    """The fraction of independent detections in `window` that some tier of `chain` dismisses
    at `thresholds`, and how many detections it rests on."""
    kw = {} if alphas is None else {"alphas": alphas}
    C, F = gd.signal_draws(p, n, bands, snr, ndet, seed=CHECK_SEED, window=window, **kw)
    det = F[:, 0] >= snr
    miss = np.zeros(int(det.sum()), bool)
    for b, t in zip(chain, thresholds):
        miss |= C[det, bands.index(b)] < t
    return float(miss.mean()), int(det.sum())


# ---- the window ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", list(PROFILES))
def test_the_local_window_covers_the_autocorrelation_and_the_coarsest_step(name):
    p, n = PROFILES[name]()
    bands = gd.usable_bands(p, n)
    step = n // min(bands)
    lo, hi = gd.local_window(p, n, bands, (0, n))
    span = hi - lo
    assert span >= gd._LOCAL_LOBES * _extent(p, n)
    assert span >= gd._LOCAL_LOBES * step
    assert span < 2 * gd._LOCAL_LOBES * max(_extent(p, n), step)       # the next power of two, no more
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
    bands = gd.usable_bands(broad, n)
    spans = [np.diff(gd.local_window(q, n, bands, (0, n)))[0] for q in (broad, low, line)]
    assert spans[0] <= spans[1] <= spans[2]
    assert spans[2] > spans[0]
    assert spans[2] >= gd._LOCAL_LOBES * _extent(line, n) or spans[2] == n


def test_a_window_no_wider_than_the_local_one_is_used_as_it_is():
    p, n = PROFILES["o4 broadband"]()
    bands = gd.usable_bands(p, n)
    lo, hi = gd.local_window(p, n, bands, (0, n))
    span = hi - lo
    for window in ((100, 100 + span), (100, 100 + span // 2), (7, 9)):
        assert gd.local_window(p, n, bands, window) == window
    assert gd.local_window(p, n, bands, (100, 101 + span)) == (lo, hi)
    assert gd.local_window(p, n, bands, None) == (lo, hi)


# ---- one set of draws for every window ------------------------------------------------------

@pytest.mark.usefixtures("simulated")
def test_every_wide_window_of_a_profile_plans_on_one_set_of_signal_draws(empty_model, monkeypatch):
    p, n = PROFILES["o4 broadband"]()
    calls = []
    real = gd._signal_window
    monkeypatch.setattr(gd, "_signal_window", lambda sim, n_, bands, lags: calls.append(lags[:2]) or real(sim, n_, bands, lags))
    chain = (128, 256)
    plans = [gc.chain_thresholds(p, n, 6.0, 1e-2, chain, window=w)
             for w in (_production(n), (0, n), (300, 1500), (64, 1984))]
    assert all(pl is not None for pl in plans)
    bands = gd.usable_bands(p, n)
    assert set(calls) == {gd.local_window(p, n, bands, (0, n))}
    assert len(calls) == 1                               # read once, then held
    # the noise maxima are each window's own, one set a window length
    assert len(gd._NOISE_CACHE) == 4


@pytest.mark.usefixtures("simulated")
def test_a_short_window_is_planned_on_its_own_draws(empty_model, monkeypatch):
    p, n = PROFILES["o4 broadband"]()
    calls = []
    real = gd._signal_window
    monkeypatch.setattr(gd, "_signal_window", lambda sim, n_, bands, lags: calls.append(lags[:2]) or real(sim, n_, bands, lags))
    short = (1000, 1064)
    assert gc.chain_thresholds(p, n, 6.0, 1e-2, (128, 256), window=short) is not None
    assert calls == [short]


@pytest.mark.usefixtures("simulated")
def test_a_retention_keeps_its_draws_and_not_its_simulation(empty_model):
    """A tier-0 retention's band is simulated again beside the plain simulation. Once its
    draws are read the simulation is let go: only the plain profile's records stay."""
    p, n = PROFILES["o4 broadband"]()
    plain = gc.chain_thresholds(p, n, 6.0, 1e-2, (128, 256), window=_production(n))
    kept = gc.chain_thresholds(p, n, 6.0, 1e-2, (128, 256), window=_production(n), tier0_cluster=(0.97, 1))
    assert plain is not None and kept is not None
    assert tuple(kept["thresholds"]) != tuple(plain["thresholds"])
    sims = list(gd._SIGNAL_RECORDS.values()) + [e[1] for k, es in gd._SIMILAR.items()
                                                if k[0] == "signal-records" for e in es]
    assert sims and all(s.get("alphas") is None for s in sims)
    assert len(gd._SIGNAL_CACHE) == 2                    # the plain profile's draws and the retention's
    # asked again, the retention's plan comes from what is held: nothing is simulated
    before = {id(s): s["rows"] for s in sims}
    gc._PLAN_CACHE.clear()
    again = gc.chain_thresholds(p, n, 6.0, 1e-2, (128, 256), window=(0, n), tier0_cluster=(0.97, 1))
    assert again is not None
    assert {id(s): s["rows"] for s in gd._SIGNAL_RECORDS.values()} == before


# ---- the budget -----------------------------------------------------------------------------

CASES = [(name, snr, kind) for name in PROFILES for snr in (5.5, 8.0)
         for kind in ("production", "whole block", "retention")]


@pytest.fixture(scope="module")
def audited():
    """Every case's plan as the library makes it (the model's choice of chain, or the same
    chain with a tier-0 retention), audited on independent draws of the window searched:
    (dismissal / budget, its standard error from the detections counted)."""
    fd = 1e-2
    ndet = 2 * gd.model_draws(fd)[0]
    out = {}
    for name, snr, kind in CASES:
        p, n = PROFILES[name]()
        bands = gd.usable_bands(p, n)
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
    bands = gd.usable_bands(p, n)
    window = _production(n)
    best, _ = gc.choose_chain(p, n, snr, fd, window=window)
    dis, count = _dismissal(p, n, bands, tuple(best["chain"]), best["thresholds"], snr, window,
                            gd.model_draws(fd)[0])
    assert dis / fd <= gm._TAIL_RATIO + 3.0 / np.sqrt(fd * count)


# ---- why the window may not be narrower -----------------------------------------------------

def _plan_on(p, n, bands, chain, snr, fd, signal_window, noise_window):
    nsamp, nsim = gd.model_draws(fd)
    sig, lags = gd.signal_draws(p, n, bands, snr, nsamp, window=signal_window, lags_too=True)
    noise = gd.noise_block_maxima(p, n, bands, nsim=nsim, window=noise_window)
    return gc.plan_chain(sig, noise, bands, list(chain), fd, None, n, snr, lags=lags)


@pytest.mark.parametrize("name", ["o4 broadband", "o4 low cutoff"])
def test_a_window_inside_the_autocorrelation_breaks_the_budget(empty_model, name):
    """The rule is not a convenience. Planned on the signal's own sample -- a window inside
    the autocorrelation -- a gate dismisses several times its budget on the real window,
    while the plan on the local window keeps it, and stays close to the plan made on the
    real window itself."""
    p, n = PROFILES[name]()
    fd, snr, chain = 1e-2, 8.0, (128, 256)
    bands = gd.usable_bands(p, n)
    window = _production(n)
    mid = (window[0] + window[1]) // 2
    ndet = 2 * gd.model_draws(fd)[0]
    narrow = _plan_on(p, n, bands, chain, snr, fd, (mid, mid + 1), window)
    local = _plan_on(p, n, bands, chain, snr, fd, gd.local_window(p, n, bands, window), window)
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
    C, F = gd.signal_draws(p, n, bands, snr, ndet, seed=CHECK_SEED, window=window)
    det = F[:, 0] >= snr
    return np.array([[np.quantile(C[det, i], q) for q in (1e-2, 1e-3)] for i in range(len(bands))])


@pytest.mark.usefixtures("simulated")
@pytest.mark.parametrize("name", list(PROFILES))
@pytest.mark.parametrize("snr", [5.5, 8.0])
def test_the_local_window_never_sets_a_gate_above_the_real_windows(empty_model, name, snr):
    """A gate set too high dismisses more than its budget; one set lower only passes more
    noise. For every band and both budgets the local window's gate is at or below the gate
    the searched window itself gives (to the 0.3% two samples of the same simulation agree
    to), on the production window and on the whole block. The noise far from the signal,
    which the local window leaves out, lowers a narrow band's gate and never raises one."""
    p, n = PROFILES[name]()
    bands = gd.usable_bands(p, n)
    for window in (_production(n), (0, n)):
        local = gd.local_window(p, n, bands, window)
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
    bands = gd.usable_bands(p, n)
    window = _production(n)
    mid = (window[0] + window[1]) // 2
    assert _extent(p, n) > 8
    ratio = _gate_quantiles(p, n, bands, 8.0, (mid - 4, mid + 4)) / _gate_quantiles(p, n, bands, 8.0, window)
    assert ratio.max() > 1.03


@pytest.mark.usefixtures("simulated")
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
    bands = gd.usable_bands(a, n)
    lengths = []
    for p in (a, b):
        best, plans = gc.choose_chain(p, n, 6.0, 1e-3, window=_production(n),
                                      tier0_clusters={128: (0.97, 1), 256: (0.97, 1)})
        assert best is not None
        assert any(len(pl["chain"]) == 1 for pl in plans)
        lengths.append(sorted({v[0][0].shape[0] for v in gd._SIGNAL_CACHE.values()}))
        # the first profile's simulation and draws are let go; what is held for profiles
        # alike stays, as when a long job's caches turn over
        gd._SIGNAL_CACHE.clear()
        gd._SIGNAL_RECORDS.clear()
        gc._CHOICE_CACHE.clear()
        for k in [k for k in gd._SIMILAR if k[0] in ("signal-records", "choice")]:
            del gd._SIMILAR[k]
    assert lengths[0] != lengths[1], "the two profiles' simulations kept the same draws: no test"
