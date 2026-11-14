"""Shared screeners are not built for a wider first band that cannot win.

HierarchicalFilter._choose_chain builds a candidate first band's shared screeners (tier-0
centroids) to price the chains that start there. A wider band shares no better than a
narrower one, so a band that loses even at the best ratio a narrower band found is skipped.
The plan must be the one the full evaluation chooses."""
import numpy as np

import matchedfilter as mf
from matchedfilter import _chains, _hierarchical, gatechain
from spectral_profiles import make_spectral_profile

_BUILD = gatechain.cluster_tier0_candidates


def _plan(prune, monkeypatch, spread, forget=True):
    """(chain, screeners, retention, thresholds) and the bands whose screeners were built, for
    a bank of 96 chirp-like templates on an inspiral-like profile at n = 1024."""
    n, nt = 1024, 96
    power = make_spectral_profile("inspiral_canonical", n).astype(np.float64)
    rng = np.random.default_rng(3)
    k = np.arange(n)
    chirp = (np.maximum(k, 4) / 64.0) ** (-5.0 / 3.0) * (k < n // 2)
    phase = (np.sort(rng.uniform(-1, 1, nt)) * spread)[:, None] * chirp[None, :] \
        + rng.uniform(0, 2 * np.pi, nt)[:, None]
    spectra = (np.sqrt(power)[None, :] * np.exp(1j * phase)).astype(np.complex64)
    built = []

    def spy(spectra, power, n, band, **kw):
        built.append(int(band))
        return _BUILD(spectra, power, n, band, **kw)

    monkeypatch.setattr(gatechain, "cluster_tier0_candidates", spy)
    monkeypatch.setattr(_hierarchical, "_TIER0_PRUNE_WIDER", prune)
    for cache in (gatechain._KEPT, gatechain._CAND_CACHE, gatechain._CHOICE_CACHE,
                  _chains._CHAIN_CHOICE):
        cache.clear()
    if forget:
        _chains._TIER0_FIRST.clear()                  # no band is remembered as the last winner
    hf = mf.HierarchicalFilter(n, 64, nt, snr=6.0, fd=1e-3)
    hf.set_reference(power.astype(np.float32))
    hf.set_templates(np.conj(spectra))
    r = hf._resolve()
    cl = hf._active_tier0_cluster()
    plan = (tuple(hf._chain), None if cl is None else int(cl.specs.shape[0]),
            None if cl is None else round(float(cl.alpha), 4),
            tuple(np.round(r.thresholds, 5)))
    return plan, built


def test_a_wider_band_that_cannot_win_is_not_clustered(monkeypatch):
    pruned, built = _plan(True, monkeypatch, spread=3.0)
    full, built_all = _plan(False, monkeypatch, spread=3.0)
    assert pruned == full
    assert pruned[1] is not None                      # the plan uses shared screeners
    assert set(built) < set(built_all)                # a band was skipped
    skipped = set(built_all) - set(built)
    assert all(any(b < s for b in built) for s in skipped)   # each for a narrower one built


def test_bands_that_can_win_are_still_clustered(monkeypatch):
    """Templates too far apart to share: no band finds screeners, so none bounds another and
    every candidate band is still built."""
    pruned, built = _plan(True, monkeypatch, spread=12.0)
    full, built_all = _plan(False, monkeypatch, spread=12.0)
    assert pruned == full
    assert built == built_all and len(built) >= 2


def test_the_band_that_won_last_is_clustered_first(monkeypatch):
    """A plan like the last one builds the last one's winning band first, which lets the
    wider band be skipped whichever of them has the lower bound. The plan is the same."""
    first, built_first = _plan(True, monkeypatch, spread=3.0)
    again, built_again = _plan(True, monkeypatch, spread=3.0, forget=False)
    assert again == first
    assert first[1] is not None and built_again[0] == first[0][0]    # the winner, first
    assert set(built_again) <= set(built_first)
    # and the other way round: told the wider band won last, it is built first -- and the
    # narrower one after it still wins
    wider = max(built_first + [2 * first[0][0]])
    for key in list(_chains._TIER0_FIRST):
        _chains._TIER0_FIRST[key] = wider
    told, built_told = _plan(True, monkeypatch, spread=3.0, forget=False)
    assert told == first
    assert built_told[0] == wider and first[0][0] in built_told
