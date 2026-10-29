"""The gate model's false dismissal is calibrated, in both directions, over many profiles.

Earlier tests checked only that dismissal was not significantly ABOVE its budget, at budgets
of 0.1-0.2% with ~1000 detections (an expected 1-2 misses): a model 100x too conservative
passed them. Too conservative is not free -- a gate below what its budget allows passes
pairs it could have dismissed -- and it hid two model errors (2026-10-26): each tier's
coarse maximum was simulated only around the signal while the engine searches the whole
window (on a flat profile at n = 4096 the 1% gates dismissed none of 2000 detections), and
signals were simulated only at whole-sample arrival times.

Two claims, each tested two-sided with a budget large enough that a run has dozens of misses:

  * the process dismisses what the model says a plan dismisses: the model's single-tier gate
    against the true coarse statistic, simulated directly in NumPy (fast, many profiles), and
    the C engine end to end (single and multi-tier chains, whole-block and windowed
    searches), each against the plan's dismissal on independent model draws (_modelled). A
    plan's own dismissal scatters about fd (gatemodel.fit_order: sd about fd / sqrt(45)), so
    a test against fd itself would mostly measure that scatter;
  * the plans dismiss fd on average, with the scatter fit_order states: over many model
    simulations, each plan judged on draws it was not made from
    (test_plans_dismiss_the_budget_on_average; tools/split_bias.py at production size).

Signals arrive at uniformly random times; a detection is the fine search's block peak at or
above snr at the signal (within 64 samples of its arrival).
"""
import zlib

import numpy as np
import pytest

import matchedfilter as mf
import matchedfilter._core as _core
from matchedfilter import gatechain as gc, gatemodel as gm
from spectral_profiles import SHAPE_NAMES, binomtest, make_spectral_profile

SNR = 5.5
#: Two-sided binomial p-value below which a count is off budget. With ~40 cases a run, a
#: calibrated model fails one by chance about once in 25 runs at 1e-3; the errors these
#: tests exist for gave p < 1e-12.
ALPHA = 1e-3


def _law(n, e):
    p = np.zeros(n)
    k = np.arange(1, n // 2)
    p[1:n // 2] = k.astype(float) ** e
    return p / p.sum()


def _profile(name, n):
    if name.startswith("f^"):
        return _law(n, float(name[2:]))
    p = make_spectral_profile(name, n).astype(np.float64)
    return p / p.sum()


PROFILES = ["f^-2", "f^-1", "f^0", "f^1"] + list(SHAPE_NAMES)


#: Independent model detections a plan's modelled dismissal is counted on (_modelled): at a
#: budget of 5% about 10,000 dismissed, 1% of its count's sd beside a test's ~10%.
_MODELLED = 200000


def _modelled(power, n, chain, thresholds, window=None):
    """The share of _MODELLED detections of an independent model simulation (seed 977, not
    the plans' 13) that some tier of chain with these thresholds dismisses."""
    bands = gc.usable_bands(power, n)
    C, F = gc.signal_draws(power, n, bands, SNR, _MODELLED, seed=977, window=window)
    det = F[:, 0] >= SNR
    lost = np.zeros(int(det.sum()), bool)
    for b, t in zip(chain, thresholds):
        lost |= C[det, bands.index(b)] < t
    return float(lost.mean())


def _true_coarse(power, n, band, draws, seed):
    """For signals at uniformly random arrival times that the fine search detects: the band's
    coarse statistic maximised over every coarse lag of the block, as the engine computes it
    (its band of the product over sqrt of the band's power)."""
    rng = np.random.default_rng(seed)
    h = np.sqrt(power)
    k = np.arange(n)
    R, fb = n // band, power[:band].sum()
    out = []
    for start in range(0, draws, 2000):
        m = min(2000, draws - start)
        t0 = rng.uniform(n / 4, 3 * n / 4, m)
        d = SNR * h * np.exp(-2j * np.pi * np.outer(t0, k) / n)
        d += rng.standard_normal((m, n)) + 1j * rng.standard_normal((m, n))
        fine = np.abs(np.fft.ifft(d * h, axis=1) * n)
        at = fine.argmax(1)
        ok = (fine[np.arange(m), at] >= SNR) & (np.abs(((at - t0 + n / 2) % n) - n / 2) <= 64)
        q = np.zeros((m, n), complex)
        q[:, :band] = d[:, :band] * h[:band]
        coarse = np.abs(np.fft.ifft(q, axis=1) * n)[:, ::R].max(1) / np.sqrt(fb)
        out.append(coarse[ok])
    return np.concatenate(out)


@pytest.mark.parametrize("name", PROFILES)
@pytest.mark.parametrize("band_frac", [2, 8])
def test_the_single_tier_gate_dismisses_its_budget_of_true_detections(name, band_frac):
    """gatemodel.gate_for's gate, against the true process: the share of detections whose
    coarse statistic falls below it is the gate's modelled dismissal, neither more nor
    (much) less."""
    n, fd = 1024, 0.05
    power = _profile(name, n)
    band = n // band_frac
    if band not in gc.usable_bands(power, n):
        pytest.skip("band %d holds none of %s's power" % (band, name))
    gate = gm.gate_for(power, n, band, SNR, fd)
    assert gate is not None
    want = _modelled(power, n, (band,), (gate,))
    true = _true_coarse(power, n, band, 6000, seed=zlib.crc32(("%s|%d" % (name, band)).encode()))
    below = int(np.count_nonzero(true < gate))
    p = binomtest(below, true.size, p=want, alternative="two-sided").pvalue
    assert p >= ALPHA, ("%s band %d: gate %.3f dismisses %d of %d true detections (%.4f), "
                        "modelled %.4f (budget %.3f)"
                        % (name, band, gate, below, true.size, below / true.size, want, fd))


def _engine_misses(power, n, chain, fd, inj, window=None, seed=11):
    """(thresholds, detections, misses, modelled dismissal) of chain_thresholds' plan run
    through the C engine on inj injections."""
    plan = gc.chain_thresholds(power, n, SNR, fd, chain, window=window)
    assert plan is not None
    thr = [float(x) for x in plan["thresholds"]]
    want = _modelled(power, n, chain, thr, window)
    w0, w1 = window or (0, n)
    h = np.sqrt(power).astype(np.complex64)
    full = mf.MatchedFilter(n, 1, 1)
    full.set_templates(np.conj(h)[None, :])
    hm = _core.HMF(n, 1, 1, list(chain), 8)
    hm.set_reference(power.astype(np.float32))
    hm.set_thresholds(thr)
    hm.set_template(0, np.conj(h))
    pk = np.empty((1, 1), dtype=mf.PEAK_DTYPE)
    cnt = np.empty(1, np.int32)
    ei, ev, mb = np.empty(0, np.int64), np.empty(0, np.complex64), np.empty(0, np.float32)
    rng = np.random.default_rng(seed)
    k = np.arange(n)
    det = miss = 0
    for _ in range(inj):
        # the engine reports a signal arriving at `lag` at n - lag: keep it inside the window
        lag = n - rng.uniform(w0 + 64, w1 - 64)
        d = (SNR * h * np.exp(2j * np.pi * lag * k / n)).astype(np.complex64)
        d += rng.standard_normal(n, dtype=np.float32) + 1j * rng.standard_normal(n, dtype=np.float32)
        full.set_data(d[None, :])
        r = full.run(binsize=n, threshold=SNR)
        at = int(r["index"][0, 0, 0])
        if abs(r["value"][0, 0, 0]) < SNR or abs(((at + lag + n / 2) % n) - n / 2) > 64:
            continue
        det += 1
        hm.set_data(0, d)
        hm.run(0, 1, 0, 1, n, SNR, w0, w1, ei, ev, mb, cnt, pk)
        miss += pk[0, 0]["index"] < 0 or abs(pk[0, 0]["value"]) < SNR
    return thr, det, miss, want


@pytest.mark.parametrize("name", ["f^-1", "f^0", "f^1", "inspiral_canonical", "notched_lines",
                                  "bandpass_plateau", "skewed_edge"])
@pytest.mark.parametrize("chain", [(1024,), (256, 1024), (128, 512, 1024)])
def test_the_engine_dismisses_its_budget(name, chain):
    """End to end through the C engine: misses among detections are what the model says the
    chain's plan dismisses, two-sided, multi-tier chains included."""
    n, fd = 2048, 0.05
    power = _profile(name, n)
    if not set(chain) <= set(gc.usable_bands(power, n)):
        pytest.skip("a band of %s holds none of %s's power" % (chain, name))
    thr, det, miss, want = _engine_misses(power, n, chain, fd, 2500)
    p = binomtest(miss, det, p=want, alternative="two-sided").pvalue
    assert p >= ALPHA, ("%s %s: thresholds %s miss %d of %d detections (%.4f), modelled %.4f "
                        "(budget %.3f)" % (name, chain, [round(t, 3) for t in thr], miss, det,
                                           miss / det, want, fd))


@pytest.mark.parametrize("name", ["f^0", "inspiral_canonical"])
def test_a_windowed_search_dismisses_its_budget(name):
    """A search over part of the block (search_window): the gates are set for the window's
    noise, and dismiss what the model says they dismiss of signals inside it."""
    n, fd = 2048, 0.05
    power = _profile(name, n)
    thr, det, miss, want = _engine_misses(power, n, (256, 1024), fd, 2500, window=(512, 1536))
    p = binomtest(miss, det, p=want, alternative="two-sided").pvalue
    assert p >= ALPHA, ("%s windowed: thresholds %s miss %d of %d detections (%.4f), modelled "
                        "%.4f (budget %.3f)" % (name, [round(t, 3) for t in thr], miss, det,
                                                miss / det, want, fd))


def _plan_seeds(name, n, fd, seeds, cost=None):
    """Per model seed, every chain's plan (plan_chain) and the pick among them (choose_chain's
    rule), each judged on 1M detections of one independent check simulation: rows of
    (seed, kind, tiers, realised dismissal / fd, half-width)."""
    power = _profile(name, n)
    bands = gc.usable_bands(power, n)
    C, F = gc.signal_draws(power, n, bands, SNR, 1000000, seed=977, window=None)
    det = F[:, 0] >= SNR
    check = C[det]
    rows = []
    for s in range(seeds):
        sig, lags = gc.signal_draws(power, n, bands, SNR, gc.model_draws(fd)[0], seed=1000 + s,
                                    lags_too=True)
        noise = gc.noise_block_maxima(power, n, bands, seed=1000 + s)
        plans = {}
        for chain in gc.enumerate_chains(n, 3, bands=bands):
            pl = gc.plan_chain(sig, noise, bands, list(chain), fd, cost, n, SNR, lags=lags)
            if pl is not None:
                plans[tuple(chain)] = pl
        best = gc.pick_stable(sorted(plans.values(), key=lambda d: d["cost"]), lambda d: d["cost"],
                              lambda d: (gc._flop_cost(d["chain"], d["search"]["reach"], n), d["chain"]))
        for kind, pl in [("chain", q) for q in plans.values()] + [("pick", best)]:
            lost = np.zeros(check.shape[0], bool)
            for b, t in zip(pl["chain"], pl["thresholds"]):
                lost |= check[:, bands.index(b)] < t
            rows.append((s, kind, len(pl["chain"]), lost.mean() / fd))
        for c in (gc._SIGNAL_CACHE, gc._SIGNAL_RECORDS, gc._NOISE_RECORDS, gc._NOISE_CACHE,
                  gc._KEPT, gc._CAND_CACHE):
            c.clear()
        gc._SIMILAR.clear()
    return rows


@pytest.mark.parametrize("name", ["f^0", "inspiral_canonical"])
def test_plans_dismiss_the_budget_on_average(name):
    """Each plan's structure is searched on half the model's detections and its thresholds
    fitted on the other half (gatechain.plan_chain): over 100 model simulations, every chain's
    plan and the pick among chains (a choice of its own) dismiss fd on fresh detections on
    average, within 3.5 standard errors of the mean over simulations, multi-tier plans
    included; and the share of plans above 1.25 fd is gatemodel.fit_order's, within 3.5
    standard errors of its mean over simulations. Fitted on the half they were searched on,
    multi-tier plans dismiss 5-9% more (the selection bias of choosing the cheapest split on
    those draws; 4.8 and 8.3 standard errors here, 2026-10-29)."""
    n, fd = 1024, 0.05
    rows = _plan_seeds(name, n, fd, 100)
    j = gm.fit_order(fd)
    tail = gm.plan_tail(fd, int(round(j / fd)) - 1)
    for kind, multi in (("chain", False), ("chain", True), ("pick", None)):
        sel = [r for r in rows if r[1] == kind and (multi is None or (r[2] > 1) == multi)]
        per = np.array([np.mean([r[3] for r in sel if r[0] == s]) for s in sorted({r[0] for r in sel})])
        mean, se = per.mean(), per.std(ddof=1) / np.sqrt(per.size)
        assert abs(mean - 1.0) < 3.5 * se, (kind, multi, mean, se)
    # a simulation's plans share its fit half: the share above 1.25 fd is judged over them
    over = np.array([np.mean([r[3] > gm._TAIL_RATIO for r in rows if r[1] == "chain" and r[0] == s])
                     for s in sorted({r[0] for r in rows})])
    se = over.std(ddof=1) / np.sqrt(over.size)
    assert abs(over.mean() - tail) < 3.5 * se, (over.mean(), se, tail)


def _ks_p(a, b):
    """Two-sample Kolmogorov-Smirnov p-value (asymptotic)."""
    a, b = np.sort(a), np.sort(b)
    x = np.concatenate([a, b])
    d = np.abs(np.searchsorted(a, x, "right") / a.size - np.searchsorted(b, x, "right") / b.size).max()
    en = np.sqrt(a.size * b.size / (a.size + b.size))
    lam = (en + 0.12 + 0.11 / en) * d
    if lam < 0.3:          # the series below does not converge; Q(0.3) = 1 - 1e-5
        return 1.0
    j = np.arange(1, 101)
    return float(min(1.0, max(0.0, 2 * np.sum((-1.0) ** (j - 1) * np.exp(-2 * j * j * lam * lam)))))


def _all_alike(ps, what):
    """Every comparison's p-value above ALPHA, Bonferroni-corrected for their number."""
    worst = min(ps, key=ps.get)
    assert ps[worst] * len(ps) > ALPHA, (what, worst, ps[worst], len(ps))


@pytest.mark.parametrize("window", [None, (192, 1856), (300, 900)])
@pytest.mark.parametrize("name", ["f^0", "f^-1", "bimodal_resonance"])
def test_signal_draws_noise_is_the_noise_simulation(name, window):
    """The signal simulation's draws without a signal are noise_block_maxima's statistics: one
    simulation, so over the whole block the same numbers (to rounding), and over a window (around a random
    point, against lags from 0) the same distribution."""
    n = 2048
    power = _profile(name, n)
    bands = gc.usable_bands(power, n)
    C, F = gc.signal_draws(power, n, bands, 0.0, 20000, window=window)
    whole = gc.noise_block_maxima(power, n, bands, window=window)
    if window is None:      # the same draws (the signal's path adds its zero response: rounding)
        np.testing.assert_allclose(C, whole, rtol=1e-6)
    _all_alike({b: _ks_p(C[:, i], whole[:, i]) for i, b in enumerate(bands)}, (name, window))
    assert (C >= 0).all() and F.shape == C.shape


@pytest.mark.parametrize("window", [(100, 900), (37, 1000), None])
@pytest.mark.parametrize("name", ["f^0", "f^-1", "inspiral_canonical"])
def test_signal_draws_match_a_direct_simulation(name, window):
    """signal_draws' window maxima against the statistics computed directly in NumPy: per draw
    a block's bins with variance p_k plus a signal at a uniformly random real-valued time in
    the window, the fine maximum over the window's lags of the n-point correlation and each
    band's over its coarse lags of the b-point correlation of bins [0, b); windows aligned
    with the coarse grids or not, spans a multiple of their steps or not. Jointly, not only
    each statistic alone: a gate acts on the coarse maxima of the draws the fine stage keeps,
    and the fine and coarse statistics share their noise: drawn independently, every marginal
    would still match. signal_draws holds only the draws whose fine statistic reaches snr
    somewhere in the block (no window keeps the others): the direct draws are taken alike."""
    n, M = 1024, 6000
    w0, w1 = window or (0, n)
    power = _profile(name, n)
    p = power / power.sum()
    bands = gc.usable_bands(power, n)
    C, F = gc.signal_draws(power, n, bands, SNR, M, window=window)
    rng = np.random.default_rng(zlib.crc32(("%s|%s" % (name, window)).encode()))
    k = np.arange(n)
    w = (rng.standard_normal((M, n)) + 1j * rng.standard_normal((M, n))) * np.sqrt(p)
    t0 = rng.uniform(w0, w1, M)
    x = w + SNR * p * np.exp(-2j * np.pi * np.outer(t0, k) / n)
    corr = np.abs(np.fft.ifft(x, axis=1) * n)
    some = corr.max(1) >= SNR
    fine = corr[:, w0:w1].max(1)
    ps = {"fine": _ks_p(F[:, 0], fine[some])}
    for i, b in enumerate(bands):
        R = n // b
        c0, c1 = (w0 // R - 1 if w0 else 0), min(-(-w1 // R) + 1, b)
        z = np.abs(np.fft.ifft(x[:, :b], axis=1) * b)[:, c0:c1].max(1) / np.sqrt(p[:b].sum())
        ps[b] = _ks_p(C[:, i], z[some])
        ps[(b, "kept")] = _ks_p(C[F[:, 0] >= SNR, i], z[fine >= SNR])
    _all_alike(ps, (name, window))
