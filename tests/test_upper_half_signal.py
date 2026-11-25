"""Signals with most of their power in the upper half of the spectrum, which the hierarchical
gates' bands do not reach.

A band that holds a small share of the signal gates mostly on noise, and its thresholds rest
on the largest of its noise over the coarse lags the signal law does not draw. Before
2026-11-24 the law took those lags as independent noise; a band whose power does not fill
its bins has strongly correlated lags, whose largest value is much smaller, so the
thresholds came out too high: a complex bank with nine tenths of its power at negative
frequencies dismissed 38% of the signals at the calibration strength against a budget of
1%. The law now reads that maximum from the noise simulation, and such banks run within the
budget (slowly: most pairs pass).
"""
import math
from collections import OrderedDict

import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from matchedfilter import gatechain as gc
from matchedfilter import _gatedraws as gd

N, L, T = 1024, 129, 4
SNR, FD = 5.5, 0.01


def _two_lobe_bank(upper, f0=0.2):
    """T taps sharing one magnitude spectrum: a Hann-windowed tone at +f0 cycles/sample with
    1 - upper of the power and one at -f0 with `upper`, at random phases; and their power
    spectrum on N bins, the reference that describes each of them."""
    rng = np.random.default_rng(3)
    j = np.arange(L) - L // 2
    taps = np.empty((T, L), np.complex128)
    for k in range(T):
        a, b = rng.uniform(0, 2 * np.pi, 2)
        taps[k] = np.hanning(L) * (np.sqrt(1 - upper) * np.exp(2j * np.pi * f0 * j + 1j * a)
                                   + np.sqrt(upper) * np.exp(-2j * np.pi * f0 * j + 1j * b))
    taps /= np.linalg.norm(taps, axis=1)[:, None]
    spectra = np.abs(np.fft.fft(np.roll(np.pad(taps, ((0, 0), (0, N - L))), -(L // 2), 1),
                                axis=1)) ** 2
    return taps.astype(np.complex64), spectra.mean(0)


def _binomial_bound(count, rate, tail=1e-3):
    """The smallest m with P(X >= m) <= tail for X binomial(count, rate)."""
    p_ge, m = 1.0, 0
    while p_ge > tail:
        p_ge -= math.comb(count, m) * rate ** m * (1 - rate) ** (count - m)
        m += 1
    return m


def _misses_at_the_calibration_strength(taps, reference, samples=1 << 20):
    """(signals the flat engine keeps, of those the hierarchical engine reports none for):
    one signal of strength SNR every two blocks, each counted on its own template's pairs,
    in complex noise of unit variance per component (the gate model's units)."""
    rng = np.random.default_rng(11)
    x = (rng.standard_normal(samples) + 1j * rng.standard_normal(samples)).astype(np.complex64)
    centres = np.arange(2 * N, samples - 2 * N, 2 * N) + rng.integers(-200, 200)
    which = rng.integers(T, size=centres.size)
    for c, t in zip(centres, which):
        x[c - L // 2:c - L // 2 + L] += SNR * taps[t] * np.exp(1j * rng.uniform(0, 2 * np.pi))
    found = {}
    for engine in ("flat", "hier"):
        bank = TimeDomainFilterBank(taps, engine=engine, fft_lengths=[N], threshold=SNR,
                                    false_dismissal=FD)
        if engine == "hier":
            bank.set_reference({N: reference})
        r = bank.filter_series(x, windows=[(N, samples - N)])
        found[engine] = (np.asarray(r.template_indices), np.asarray(r.sample_indices))

    def near(engine, c, t):
        ti, si = found[engine]
        return bool(np.any((ti == t) & (np.abs(si - c) < 400)))

    kept = [(c, t) for c, t in zip(centres, which) if near("flat", c, t)]
    return len(kept), sum(not near("hier", c, t) for c, t in kept)


@pytest.mark.parametrize("upper", [0.9, 1.0])
def test_a_bank_at_negative_frequencies_is_gated_within_the_budget(upper):
    taps, reference = _two_lobe_bank(upper)
    kept, missed = _misses_at_the_calibration_strength(taps, reference)
    assert kept > 200
    # the budget allows a binomial(kept, FD) count; the old law missed 38% at upper = 0.9
    assert missed < _binomial_bound(kept, FD), (missed, kept)


def test_a_bank_at_positive_frequencies_agrees_with_the_flat_engine():
    taps, reference = _two_lobe_bank(0.0)
    kept, missed = _misses_at_the_calibration_strength(taps, reference)
    assert kept > 200
    assert missed < _binomial_bound(kept, FD), (missed, kept)


@pytest.mark.parametrize("complex_series", [False, True])
@pytest.mark.parametrize("complex_taps", [False, True])
def test_flat_dif_and_corr_take_every_combination_of_series_and_taps(complex_series, complex_taps):
    rng = np.random.default_rng(5)
    taps = rng.standard_normal((3, 65)) + (1j * rng.standard_normal((3, 65)) if complex_taps else 0)
    taps = (taps / np.linalg.norm(taps, axis=1)[:, None]).astype(
        np.complex64 if complex_taps else np.float32)
    x = rng.standard_normal(1 << 14) + (1j * rng.standard_normal(1 << 14) if complex_series else 0)
    x = x.astype(np.complex64 if complex_series else np.float32)
    corr = TimeDomainFilterBank(taps, engine="corr", fft_lengths=[1024]).correlate_series(x)
    inner = slice(1024, x.size - 1024)
    for t in range(3):
        # z[s] = sum_k conj(taps[k]) x[s + k - c], c the centre tap
        direct = np.correlate(x.astype(np.complex128), taps[t].astype(np.complex128),
                              mode="full")[64 - 32:64 - 32 + x.size]
        assert np.max(np.abs(corr[t, inner] - direct[inner])) < 1e-4 * np.max(np.abs(direct))
    peaks = {}
    for engine in ("flat", "dif"):
        r = TimeDomainFilterBank(taps, engine=engine, fft_lengths=[1024], threshold=3.5,
                                 binsize=256).filter_series(x)
        peaks[engine] = set(zip(r.template_indices.tolist(), r.sample_indices.tolist()))
    assert peaks["flat"] and peaks["flat"] == peaks["dif"]


@pytest.fixture
def empty_model(monkeypatch):
    for c in ("_SIGNAL_CACHE", "_NOISE_CACHE", "_SIGNAL_RECORDS", "_NOISE_RECORDS",
              "_LOCAL_WINDOWS"):
        monkeypatch.setattr(gd, c, OrderedDict())
    for c in ("_KEPT", "_PLAN_CACHE"):
        monkeypatch.setattr(gc, c, OrderedDict())
    monkeypatch.setattr(gd, "_SIMILAR", {})
    monkeypatch.setattr(gd, "_SIMILAR_COUNT", {})


def test_the_law_dismisses_as_the_simulation_on_a_band_of_correlated_lags(empty_model, monkeypatch):
    """Band 512 of a two-lobe profile with three quarters of its power above N / 2 holds a
    quarter of the signal in 17 of its 512 bins, so its 258 coarse lags in the planner's
    window are strongly correlated. At the threshold where the simulation dismisses 5% of
    the detections, the law's table dismisses the same share, to the two tables' scatter
    (about 5% of the share each at 20,000 detections). The independent-noise law dismissed
    a fraction of a percent there."""
    _, reference = _two_lobe_bank(0.75)
    p = gd._norm_profile(reference, N)
    bands = gd.usable_bands(p, N)
    window = gd.local_window(p, N, bands, None)
    i = bands.index(512)
    shares = []
    for law in ("0", "1"):
        monkeypatch.setenv("MF_SIGNAL_LAW", law)
        gd._SIGNAL_CACHE.clear()
        (C, F), _ = gd._signal_table(p, N, bands, SNR, 20000, seed=21, window=window,
                                     lags_too=True)
        shares.append(np.asarray(gc.kept_draws((C, F), bands, (512,), SNR))[:, 0])
    simulated, law = shares
    g = np.quantile(simulated, 0.05)
    assert abs(float((law < g).mean()) / 0.05 - 1.0) < 0.25
