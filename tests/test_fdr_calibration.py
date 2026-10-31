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

from matchedfilter import gatechain as gc, gatemodel as gm
from spectral_profiles import binomtest
from fdr_support import ALPHA, PROFILES, SNR, modelled, profile


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
    power = profile(name, n)
    band = n // band_frac
    if band not in gc.usable_bands(power, n):
        pytest.skip("band %d holds none of %s's power" % (band, name))
    gate = gm.gate_for(power, n, band, SNR, fd)
    assert gate is not None
    want = modelled(power, n, (band,), (gate,))
    true = _true_coarse(power, n, band, 6000, seed=zlib.crc32(("%s|%d" % (name, band)).encode()))
    below = int(np.count_nonzero(true < gate))
    p = binomtest(below, true.size, p=want, alternative="two-sided").pvalue
    assert p >= ALPHA, ("%s band %d: gate %.3f dismisses %d of %d true detections (%.4f), "
                        "modelled %.4f (budget %.3f)"
                        % (name, band, gate, below, true.size, below / true.size, want, fd))



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
    power = profile(name, n)
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
    power = profile(name, n)
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
