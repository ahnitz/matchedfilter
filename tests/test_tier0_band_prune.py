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


def test_the_floor_a_wider_band_inherits_from_the_narrower_ones():
    """Every narrower band that was clustered to the end bounds the wider band's ratio from
    below, so the largest of them binds; one cut short does not, beyond the smallest found."""
    floor = _hierarchical._narrower_bands_floor
    ratios = {64: 0.2, 128: 0.35}
    assert floor(ratios, {64, 128}, 256) == 0.35
    assert floor(ratios, {64}, 256) == 0.2            # 128 was cut short: it might reach less
    assert floor(ratios, {128}, 256) == 0.35
    assert floor(ratios, set(), 256) == 0.2           # none complete: the smallest found
    assert floor(ratios, {64, 128}, 128) == 0.2       # only the bands narrower than it
    assert floor(ratios, {64, 128}, 64) is None       # nothing narrower
    assert floor({256: 0.5}, {256}, 128) is None


def _second_profile(rule, monkeypatch, spread):
    """A plan given _plan's bank and reference, then a second profile with a quarter of the
    power below bin 64: the second profile's (chain, screeners, thresholds) and the bands
    whose screeners were built for the first and for the second."""
    n, nt = 1024, 96
    power = make_spectral_profile("inspiral_canonical", n).astype(np.float64)
    rng = np.random.default_rng(3)
    k = np.arange(n)
    chirp = (np.maximum(k, 4) / 64.0) ** (-5.0 / 3.0) * (k < n // 2)
    phase = (np.sort(rng.uniform(-1, 1, nt)) * spread)[:, None] * chirp[None, :] \
        + rng.uniform(0, 2 * np.pi, nt)[:, None]
    spectra = (np.sqrt(power)[None, :] * np.exp(1j * phase)).astype(np.complex64)
    other = power.copy()
    other[np.minimum(k, n - k) < 64] *= 0.25
    built = []

    def spy(spectra, power, n, band, **kw):
        built.append(int(band))
        return _BUILD(spectra, power, n, band, **kw)

    monkeypatch.setattr(gatechain, "cluster_tier0_candidates", spy)
    if not rule:
        monkeypatch.setattr(mf.HierarchicalFilter, "_tier0_seen_elsewhere", lambda self, band: None)
    for cache in (gatechain._KEPT, gatechain._CAND_CACHE, gatechain._CHOICE_CACHE,
                  _chains._CHAIN_CHOICE, _chains._TIER0_FIRST):
        cache.clear()
    hf = mf.HierarchicalFilter(n, 64, nt, snr=6.0, fd=1e-3)
    hf.set_reference(power.astype(np.float32))
    hf.set_templates(np.conj(spectra))
    hf._resolve()
    first, built[:] = list(built), []
    hf.use_profile("b")
    hf.set_reference(other.astype(np.float32))
    r = hf._resolve()
    cl = hf._active_tier0_cluster()
    plan = (tuple(hf._chain), None if cl is None else int(cl.specs.shape[0]),
            tuple(np.round(r.thresholds, 5)))
    return plan, first, built


def test_a_band_another_profile_saw_lose_its_sharing_is_not_clustered_again(monkeypatch):
    """The first profile clustered the 128 band to the end. Under the second, once a band
    has won, 128 is priced one ratio step better than it shared for the first profile: it
    still loses, so its screeners are not built again. The plan is the one built with them."""
    plan, first, built = _second_profile(True, monkeypatch, spread=3.0)
    full, first_all, built_all = _second_profile(False, monkeypatch, spread=3.0)
    assert plan == full and first == first_all
    assert plan[1] is not None                        # the second profile shares screeners
    assert 128 in first and 128 in built_all and 128 not in built
    assert built == [b for b in built_all if b != 128]


def test_a_band_that_could_still_win_under_the_second_profile_is_clustered(monkeypatch):
    """Templates further apart share less at every band, and one step better at 128 would
    win: the band is clustered under the second profile as it would be without the rule."""
    plan, first, built = _second_profile(True, monkeypatch, spread=5.0)
    full, first_all, built_all = _second_profile(False, monkeypatch, spread=5.0)
    assert plan == full
    assert 128 in built and built == built_all
