"""Shared screeners are not built for a wider first band that cannot win.

HierarchicalFilter._choose_chain builds a candidate first band's shared screeners (tier-0
screeners) to price the chains that start there. A wider band shares no better than a
narrower one, so a band that loses even at the best ratio a narrower band found is skipped.
The plan must be the one the full evaluation chooses."""
import numpy as np

import matchedfilter as mf
from matchedfilter import _screeners
from matchedfilter import _calibration, _chains, _hierarchical, gatechain
from spectral_profiles import make_spectral_profile

_BUILD = _screeners.cluster_tier0_candidates


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

    monkeypatch.setattr(_screeners, "cluster_tier0_candidates", spy)
    monkeypatch.setattr(_hierarchical, "_TIER0_PRUNE_WIDER", prune)
    # Which bands can win is the cost model's call, and a machine's own model decides it its
    # own way (on one CI runner no wider band was ever a candidate, so none could be skipped):
    # these tests are about particular outcomes, so they price on a fixed model (a Zen 5
    # core's at n = 1024, without the Q15 screen) and without the timed direct refine.
    fixed = gatechain.CostModel(
        n, {64: 34.28, 128: 64.01, 256: 145.7, 512: 351.4},
        {64: [(0.008301, 307.1), (0.09961, 146.4)], 128: [(0.008301, 307.1), (0.09961, 146.4)],
         256: [(0.008301, 576.2), (0.09961, 258.3)], 512: [(0.008301, 996.2), (0.09961, 561.0)]},
        [(0.008301, 2150.0), (0.09961, 2050.0)], block=2094.0)
    monkeypatch.setattr(_calibration, "calibrate_costs", lambda *a, **kw: fixed)
    monkeypatch.setattr(mf.HierarchicalFilter, "_direct_price", lambda self, *a, **kw: None)
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
            tuple(np.round(r.thresholds, 5)),
            tuple(b for b, c in sorted(hf._tier0_clusters.items()) if c is not None))
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
    # whatever was built on the way, the plan holds the winning band's screeners alone
    assert first[4] == (first[0][0],)


def test_the_floor_a_wider_band_inherits_from_the_narrower_ones():
    """Every narrower band whose ratio is what it can share bounds the wider band's from
    below, so the largest of them binds; one cut short does not, beyond the smallest found."""
    floor = _hierarchical._narrower_bands_floor
    ratios = {64: 0.2, 128: 0.35}
    assert floor(ratios, {64, 128}, 256) == 0.35
    assert floor(ratios, {64}, 256) == 0.2            # 128 was cut short: it might reach less
    assert floor(ratios, {128}, 256) == 0.35
    assert floor(ratios, set(), 256) == 0.2           # none whole: the smallest found
    assert floor(ratios, {64, 128}, 128) == 0.2       # only the bands narrower than it
    assert floor(ratios, {64, 128}, 64) is None       # nothing narrower
    assert floor({256: 0.5}, {256}, 128) is None



def test_a_band_stopped_by_a_limit_does_not_bound_a_wider_one():
    """A band's ratio counts as what it can share only if every pass ran and its screeners
    stayed above the least a band keeps."""
    from types import SimpleNamespace

    def cand(count):
        return SimpleNamespace(offsets=np.zeros(count + 1, np.int32))

    freely = _hierarchical._shares_freely
    assert freely([cand(40), cand(24), None], True, 8)
    assert not freely([cand(40), cand(24)], False, 8)          # a pass was cut short
    assert not freely([cand(40), cand(8)], True, 8)            # stopped at the least
    assert not freely([None, None], True, 8)                   # nothing was shared


def test_the_band_order_memory_is_bounded(monkeypatch):
    """The memory of which band won holds the last few references: an older one is dropped."""
    monkeypatch.setattr(_chains, "_TIER0_FIRST_MAX", 1)
    plan, _ = _plan(True, monkeypatch, spread=3.0)
    assert len(_chains._TIER0_FIRST) == 1
    (key, won), = _chains._TIER0_FIRST.items()
    assert won == plan[0][0]
    _chains._TIER0_FIRST["another reference"] = 64
    _chains._TIER0_FIRST.move_to_end(key)                       # the plan's is the newer one
    again, _ = _plan(True, monkeypatch, spread=3.0, forget=False)
    assert again == plan and list(_chains._TIER0_FIRST) == [key]


def test_a_plan_does_not_depend_on_the_bank_planned_before_it(monkeypatch):
    """Banks of one reference follow one another (a top template's leaf banks), and each
    takes the band the last one's screeners won at as the first to build. Its plan is the
    one it has when planned first: for every ordered pair of three banks that share tightly,
    loosely and not at all."""
    spreads = (2.0, 5.0, 12.0)
    alone = {s: _plan(True, monkeypatch, spread=s)[0] for s in spreads}
    assert len({plan[:2] for plan in alone.values()}) >= 2                # not one plan thrice
    for before in spreads:
        for after in spreads:
            if before != after:
                _plan(True, monkeypatch, spread=before)
                plan, _ = _plan(True, monkeypatch, spread=after, forget=False)
                assert plan == alone[after], (before, after)
