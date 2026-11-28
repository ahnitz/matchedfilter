"""gatechain.plan_chain prices a chain's candidate plans on a CostModel in C
(_core.plan_best). The Python loop it replaced is kept in plan_chain (gatechain._C_PRICING
False) and must choose the same plan at the same cost, to the bit, whatever the model
prices: a Q15 screen, shared screeners' ratio, a direct refine."""
import pathlib
from collections import OrderedDict

import numpy as np
import pytest

from matchedfilter import gatechain as gc
from matchedfilter import _gatedraws as gd

DATA = pathlib.Path(__file__).parent / "data"
N, SNR = 2048, 6.0
BANDS = (64, 128, 256, 512, 1024)


def _model(screen, ratios, direct, feed=False):
    sparse = {b: [(0.0098, 600.0 * b / 128), (0.05, 420.0 * b / 128), (0.104, 300.0 * b / 128)]
              for b in BANDS}
    screens = None
    if screen:
        screens = {b: {"dense": 0.45 * d, "recheck": 0.5 * d,
                       "excess": [(0.001, 0.0013), (0.01, 0.0118), (0.1, 0.104)],
                       "sparse": [(0.0098, 520.0 * b / 128), (0.104, 280.0 * b / 128)]}
                   for b, d in ((64, 30.7), (128, 57.5), (256, 140.1), (512, 378.3))}
    cost = gc.CostModel(N, {64: 30.7, 128: 57.5, 256: 140.1, 512: 378.3, 1024: 876.6}, sparse,
                        [(0.0098, 3388.0), (0.104, 2889.0)], block=3306.0, screen=screens,
                        # a GPU's feeds: the band forward at each widest band, the full one
                        feed=({"band": {64: 0.0, 128: -500.0, 256: -380.0, 512: -410.0, 1024: 290.0},
                               "full": 1390.0} if feed else None))
    if ratios:
        cost = cost.with_tier0_cluster({64: 0.55, 128: 0.7, 256: 0.6})
    if direct:
        cost = cost.with_direct(9.0, fraction=0.8, base=40.0, multi_frac=0.3)
    return cost


@pytest.fixture
def empty_model(monkeypatch):
    for c in ("_SIGNAL_CACHE", "_NOISE_CACHE", "_CAND_CACHE", "_CHOICE_CACHE", "_PLAN_CACHE",
              "_SIGNAL_RECORDS", "_NOISE_RECORDS", "_KEPT", "_LOCAL_WINDOWS"):
        monkeypatch.setattr(gd if hasattr(gd, c) else gc, c, OrderedDict())
    monkeypatch.setattr(gd, "_SIMILAR", {})
    monkeypatch.setattr(gd, "_SIMILAR_COUNT", {})


@pytest.mark.parametrize("screen, ratios, direct", [(False, False, False), (True, False, False),
                                                    (True, True, False), (False, False, True),
                                                    (True, True, True)])
def test_the_plans_are_the_python_loops(screen, ratios, direct, empty_model, monkeypatch):
    p = np.load(DATA / "reference_profile_o2_h1l1_2048.npy").astype(np.float64)
    cost = _model(screen, ratios, direct)
    plans = {}
    for in_c in (True, False):
        monkeypatch.setattr(gc, "_C_PRICING", in_c)
        for c in (gc._CHOICE_CACHE, gc._PLAN_CACHE, gc._CAND_CACHE, gd._SIMILAR):
            c.clear()
        best, every = gc.choose_chain(p, N, SNR, 1e-3, cost=cost, max_tiers=3, ntemplates=96)
        plans[in_c] = [(tuple(d["chain"]), d["cost"], tuple(d["search"]["thresholds"]),
                        tuple(d["search"]["reach"]), d["search"]["halfwidth"], d["q15"])
                       for d in every]
    assert plans[True] == plans[False] and len(plans[True]) >= 5
    multi = [d for d in plans[True] if len(d[0]) > 1]
    assert multi                                          # chains the C routine priced
    if screen:
        assert any(d[5] for d in multi)                  # some take the screen
    if direct:
        assert any(d[4] is not None for d in multi)      # some refine in a window


@pytest.mark.parametrize("forced", ["", "0", "1"])
@pytest.mark.parametrize("ratios, direct", [(False, False), (True, False), (False, True),
                                            (True, True)])
def test_a_gpus_feed_is_priced_as_the_python_loop_prices_it(forced, ratios, direct, empty_model,
                                                           monkeypatch):
    """A GPU's cost model prices each chain's feed (CostModel.feed_delta: the band forward or
    the full one, by the chain's refine fraction, or as MF_BAND_FORWARD forces it). The C
    routine prices it too (it, not the loop, priced the multi-tier chains), to the bit: the
    same plans at the same costs as the Python loop."""
    from matchedfilter import _core
    monkeypatch.setenv("MF_BAND_FORWARD", forced)
    p = np.load(DATA / "reference_profile_o2_h1l1_2048.npy").astype(np.float64)
    cost = _model(False, ratios, direct, feed=True)
    in_routine = []
    plan_best = _core.plan_best

    def counted(*args):
        in_routine.append(args[-1])
        return plan_best(*args)
    monkeypatch.setattr(gc._core, "plan_best", counted)
    plans = {}
    for in_c in (True, False):
        monkeypatch.setattr(gc, "_C_PRICING", in_c)
        for c in (gc._CHOICE_CACHE, gc._PLAN_CACHE, gc._CAND_CACHE, gd._SIMILAR):
            c.clear()
        best, every = gc.choose_chain(p, N, SNR, 1e-3, cost=cost, max_tiers=3, ntemplates=96)
        plans[in_c] = [(tuple(d["chain"]), d["cost"], tuple(d["search"]["thresholds"]),
                        tuple(d["search"]["reach"]), d["search"]["halfwidth"])
                       for d in every]
    assert plans[True] == plans[False] and len(plans[True]) >= 5
    # the choice without the feed comes first; the per-count ones price it
    assert in_routine and any(f is not None for f in in_routine)
    # the feed is in the costs: the same choice without it prices the chains differently
    monkeypatch.setattr(gc, "_C_PRICING", True)
    for c in (gc._CHOICE_CACHE, gc._PLAN_CACHE, gc._CAND_CACHE, gd._SIMILAR):
        c.clear()
    _, bare = gc.choose_chain(p, N, SNR, 1e-3, cost=_model(False, ratios, direct), max_tiers=3,
                              ntemplates=96)
    assert {tuple(d["chain"]): d["cost"] for d in bare} != {c[0]: c[1] for c in plans[True]}


def test_a_table_too_long_for_the_routine_is_priced_in_python(empty_model, monkeypatch):
    cost = _model(False, False, False)
    assert gc._pricing_tables(cost, (64, 256), False, 0.0, 0.0, 0, 1.0, None) is not None
    cost._refine = sorted((0.001 * (i + 1), 3000.0 - i) for i in range(70))
    assert gc._pricing_tables(cost, (64, 256), False, 0.0, 0.0, 0, 1.0, None) is None


def test_banks_that_price_apart_share_one_search(empty_model, monkeypatch):
    """Two GPU banks whose models differ only in what prices a pair -- the template count
    the feed is spread over, a group's direct-refine fraction -- search the same draws: the
    second choice prepares no chain's search again (_prepare_chain, the halves and distances
    of the draws), and both choose what they choose with nothing kept."""
    p = np.load(DATA / "reference_profile_o2_h1l1_2048.npy").astype(np.float64)
    a = _model(False, True, True, feed=True)
    b = a.with_direct(9.0, fraction=0.55, base=40.0, multi_frac=0.3)

    def choose(cost, nt):
        best, every = gc.choose_chain(p, N, SNR, 1e-3, cost=cost, max_tiers=3, ntemplates=nt)
        return [(tuple(d["chain"]), d["cost"], tuple(d["search"]["thresholds"]),
                 tuple(d["search"]["reach"]), d["search"]["halfwidth"],
                 tuple(d["thresholds"])) for d in every]

    prepared = []
    real = gc._prepare_chain
    monkeypatch.setattr(gc, "_prepare_chain", lambda *a, **k: prepared.append(1) or real(*a, **k))
    kept = [choose(a, 96)]
    first = len(prepared)
    kept += [choose(a, 97), choose(b, 96)]
    assert first > 0 and len(prepared) == first          # the later choices prepared nothing

    class Never(OrderedDict):
        def __setitem__(self, key, value):
            pass
    monkeypatch.setattr(gc, "_PREP_CACHE", Never())
    for c in (gc._CHOICE_CACHE, gc._PLAN_CACHE, gc._CAND_CACHE, gd._SIMILAR):
        c.clear()
    alone = [choose(a, 96), choose(a, 97), choose(b, 96)]
    assert kept == alone and kept[0] != kept[1] and kept[0] != kept[2]


@pytest.mark.parametrize("feed, forced, shared", [
    (None, "", True),                                             # a CPU's model: no feed
    ({"band": dict.fromkeys(BANDS, 0.0), "full": 25.56}, "1", True),  # every plan bands
    ({"band": dict.fromkeys(BANDS, 0.0), "full": 25.56}, "", False),  # the Radeon's feeds
    ({"band": {64: 0.0, 128: 0.0, 256: 0.0, 512: 0.0, 1024: 3000.0}, "full": 20000.0}, "",
     False)])
def test_a_gpu_choice_is_the_counts_own_at_every_template_count(feed, forced, shared, empty_model,
                                                                monkeypatch):
    """A GPU's model prices a feed, a forward's per-block price spread over the template count.
    choose_chain keeps a choice without the count only where no chain's plan takes a priced
    feed, so that it is the count's own at every count; elsewhere it chooses per count. Every
    count, small ones included where a priced feed is large, gets exactly what pricing the
    choice afresh at that count gives: the same plans, costs, thresholds and offsets."""
    monkeypatch.setenv("MF_BAND_FORWARD", forced)
    p = np.load(DATA / "reference_profile_o2_h1l1_2048.npy").astype(np.float64)
    sparse = {b: [(0.0098, 600.0 * b / 128), (0.05, 420.0 * b / 128), (0.104, 300.0 * b / 128)]
              for b in BANDS}
    cost = gc.CostModel(N, {64: 30.7, 128: 57.5, 256: 140.1, 512: 378.3, 1024: 876.6}, sparse,
                        [(0.0098, 3388.0), (0.104, 2889.0)], block=3306.0, feed=feed)
    counts = list(range(1, 25)) + [64, 96, 319]
    pn = gc._norm_profile(p, N)
    c_bands, k0s, bands = gc._cached_band_offsets(pn, gc._gm._profile_sig(pn), N, gc._MIN_BAND)
    nsamp, nsim = gc.model_draws(1e-3)

    def described(choice):
        best, every = choice
        return (tuple(best["chain"]), [(tuple(d["chain"]), d["cost"], d["q15"], d["offsets"],
                                        tuple(d["search"]["thresholds"]), tuple(d["thresholds"]),
                                        d["halfwidth"]) for d in every])
    fresh = {nt: described(gc._choose_chain(pn, N, SNR, 1e-3, cost, 3, gc._MIN_BAND, nsim, None,
                                            nt, nsamp, bands=bands,
                                            offsets_by_band=dict(zip(c_bands, k0s))))
             for nt in counts}
    made = []
    inner = gc._choose_chain
    monkeypatch.setattr(gc, "_choose_chain", lambda *a, **k: made.append(1) or inner(*a, **k))
    for nt in counts:
        assert described(gc.choose_chain(p, N, SNR, 1e-3, cost=cost, max_tiers=3,
                                          ntemplates=nt)) == fresh[nt]
    # shared: one choice for every count; else one without the feed, then one per count
    assert len(made) == (1 if shared else 1 + len(counts))
    if feed is not None and not shared:
        # the feed is priced: some chain's plan, or the choice, moves with the count
        assert len({tuple(fresh[nt][1]) for nt in counts}) > 1


@pytest.mark.parametrize("in_c", [True, False])
def test_a_chain_search_leaves_no_cyclic_garbage(in_c, empty_model, monkeypatch):
    """A chain's candidate search (_chain_candidates, in C or in its Python reference) leaves
    nothing for the collector: the Python search's recursive function referred to itself
    through its closure, holding a copy of the noise columns with it, on every call, also
    where the C search ran instead."""
    import gc as collector
    monkeypatch.setattr(gc, "_C_SEARCH", in_c)
    p = np.load(DATA / "reference_profile_o2_h1l1_2048.npy").astype(np.float64)
    collector.collect()
    collector.disable()
    try:
        collector.set_debug(collector.DEBUG_SAVEALL)
        best, every = gc.choose_chain(p, N, SNR, 1e-3, cost=_model(False, False, False),
                                      max_tiers=3)
        assert best is not None and len(every) >= 5
        del best, every
        collector.collect()
        left = sorted({getattr(o, "__qualname__", type(o).__qualname__)
                       for o in collector.garbage
                       if getattr(o, "__module__", None) == "matchedfilter.gatechain"})
    finally:
        collector.garbage.clear()
        collector.set_debug(0)
        collector.enable()
    assert left == [], left
