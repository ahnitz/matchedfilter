"""The gate model's false dismissal is calibrated, in both directions, over many profiles.

Earlier tests checked only that dismissal was not significantly ABOVE its budget, at budgets
of 0.1-0.2% with ~1000 detections (an expected 1-2 misses): a model 100x too conservative
passed them. Too conservative is not free -- a gate below what its budget allows passes
pairs it could have dismissed -- and it hid two model errors (2026-10-26): each tier's
coarse maximum was simulated only around the signal while the engine searches the whole
window (on a flat profile at n = 4096 the 1% gates dismissed none of 2000 detections), and
signals were simulated only at whole-sample arrival times.

Here the budget is large enough that a run has dozens of misses, and the count is tested
two-sided. Two levels:

  * the model's single-tier gate against the true coarse statistic, simulated directly in
    NumPy (fast, many profiles): the share of true detections below the gate is the budget;
  * the C engine end to end, single and multi-tier chains, whole-block and windowed searches.

Signals arrive at uniformly random times; a detection is the fine search's block peak at or
above snr at the signal (within 64 samples of its arrival).
"""
import zlib

import numpy as np
import pytest

import matchedfilter as mf
import matchedfilter._core as _core
from matchedfilter import gatechain as gc, gatemodel as gm
from tests.spectral_profiles import SHAPE_NAMES, binomtest, make_spectral_profile

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
    coarse statistic falls below it is the budget, neither more nor (much) less."""
    n, fd = 1024, 0.05
    power = _profile(name, n)
    band = n // band_frac
    if band not in gc.usable_bands(power, n):
        pytest.skip("band %d holds none of %s's power" % (band, name))
    gate = gm.gate_for(power, n, band, SNR, fd)
    assert gate is not None
    true = _true_coarse(power, n, band, 6000, seed=zlib.crc32(("%s|%d" % (name, band)).encode()))
    below = int(np.count_nonzero(true < gate))
    p = binomtest(below, true.size, p=fd, alternative="two-sided").pvalue
    assert p >= ALPHA, ("%s band %d: gate %.3f dismisses %d of %d true detections (%.4f), "
                        "budget %.3f" % (name, band, gate, below, true.size, below / true.size, fd))


def _engine_misses(power, n, chain, fd, inj, window=None, seed=11):
    plan = gc.chain_thresholds(power, n, SNR, fd, chain, window=window)
    assert plan is not None
    thr = [float(x) for x in plan["thresholds"]]
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
    return thr, det, miss


@pytest.mark.parametrize("name", ["f^-1", "f^0", "f^1", "inspiral_canonical", "notched_lines",
                                  "bandpass_plateau", "skewed_edge"])
@pytest.mark.parametrize("chain", [(1024,), (256, 1024), (128, 512, 1024)])
def test_the_engine_dismisses_its_budget(name, chain):
    """End to end through the C engine: misses among detections are the chain's budget, two-
    sided. (A multi-tier chain's budget is cut by a one-sided 95% binomial tolerance on the
    draws, so its expected share sits a little under fd; the test allows for that.)"""
    n, fd = 2048, 0.05
    power = _profile(name, n)
    if not set(chain) <= set(gc.usable_bands(power, n)):
        pytest.skip("a band of %s holds none of %s's power" % (chain, name))
    thr, det, miss = _engine_misses(power, n, chain, fd, 2500)
    p = binomtest(miss, det, p=fd, alternative="two-sided").pvalue
    p_tol = binomtest(miss, det, p=0.85 * fd, alternative="two-sided").pvalue if len(chain) > 1 else 0.0
    assert max(p, p_tol) >= ALPHA, ("%s %s: thresholds %s miss %d of %d detections (%.4f), budget %.3f"
                                    % (name, chain, [round(t, 3) for t in thr], miss, det, miss / det, fd))


@pytest.mark.parametrize("name", ["f^0", "inspiral_canonical"])
def test_a_windowed_search_dismisses_its_budget(name):
    """A search over part of the block (search_window): the gates are set for the window's
    noise, and dismiss the budget of signals inside it."""
    n, fd = 2048, 0.05
    power = _profile(name, n)
    thr, det, miss = _engine_misses(power, n, (256, 1024), fd, 2500, window=(512, 1536))
    p = max(binomtest(miss, det, p=f, alternative="two-sided").pvalue for f in (fd, 0.85 * fd))
    assert p >= ALPHA, ("%s windowed: thresholds %s miss %d of %d detections (%.4f), budget %.3f"
                        % (name, [round(t, 3) for t in thr], miss, det, miss / det, fd))


def test_window_noise_lifts_every_kept_draw_to_the_windows_maximum():
    """Each kept draw's coarse maximum is at least its paired noise maximum over the rest of
    the window, per tier (one noise row for all of a draw's tiers): the engine tests the
    maximum over the window. The rest leaves out the draw's own lags, which hold the signal."""
    n = 2048
    power = _profile("f^0", n)
    bands = gc.usable_bands(power, n)
    sig = gc.signal_draws(power, n, bands, SNR, 20000)
    noise = gc.rest_noise(power, n, bands)
    whole = gc.noise_block_maxima(power, n, bands)
    assert (noise <= whole + 1e-6).all() and (noise < whole).any()   # fewer lags, smaller maxima
    chain = (256, 1024)
    S = gc.kept_draws(sig, bands, chain, SNR, noise)
    cols = [bands.index(b) for b in chain]
    keep = np.flatnonzero(sig[1][:, cols].max(1) >= SNR)
    np.testing.assert_array_less(noise[keep % noise.shape[0]][:, cols] - 1e-6, S)
    local = gc.kept_draws(sig, bands, chain, SNR)
    assert (S >= local).all() and (S > local).any()
