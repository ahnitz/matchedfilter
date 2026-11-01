"""Unit tests for analytic pair-cost lower bounds and block-size candidate pruning."""
import copy
import functools
import json
import pathlib
from collections import OrderedDict

import numpy as np
import pytest

from matchedfilter import _calibration as cal
from matchedfilter import gatechain as gc

DATA = pathlib.Path(__file__).parent / "data"


def _zen5_model_2048():
    rec = json.loads((DATA / "cost_model_2048_zen5.json").read_text())
    return gc.CostModel.from_dict(rec["model"])


def _scaled_model(cm_2048, n):
    scale = float(n) / 2048.0
    bands = gc.candidate_bands(n)
    dense = {}
    sparse = {}
    screen = {}
    for b in bands:
        b_src = min(b, 1024)
        factor = float(b) / float(b_src)
        dense[b] = cm_2048.dense[b_src] * factor
        if b_src in cm_2048._sparse:
            sparse[b] = [(f, v * factor) for f, v in cm_2048._sparse[b_src]]
        if b_src in cm_2048.screen and b <= 1024:
            sc = cm_2048.screen[b_src]
            screen[b] = {
                "dense": sc["dense"] * factor,
                "recheck": sc["recheck"],
                "excess": list(sc["excess"]),
            }
    refine = [(f, v * scale) for f, v in cm_2048._refine]
    return gc.CostModel(n, dense, sparse, refine, block=cm_2048.block * (scale ** 1.15), screen=screen)


def _diverse_profiles(n):
    f = np.arange(1, n // 2 + 1, dtype=np.float64)
    p_insp = np.zeros(n)
    k_cut = max(1, n // 64)
    p_insp[k_cut:n // 2] = f[k_cut - 1:n // 2 - 1] ** (-7.0 / 3.0)

    p_white = np.zeros(n)
    p_white[1:n // 2] = 1.0

    p_bump = np.zeros(n)
    kc = n // 8
    p_bump[1:n // 2] = np.exp(-0.5 * ((np.arange(1, n // 2) - kc) / max(2.0, n / 128.0)) ** 2)

    p_spike = np.zeros(n)
    p_spike[min(73, n // 4)] = 1.0

    p_comb = np.zeros(n)
    p_comb[8:n // 2:16] = 1.0

    p_hf = np.zeros(n)
    k_hf = max(40, n // 6)
    p_hf[k_hf:n // 2] = f[k_hf - 1:n // 2 - 1] ** (-1.5)

    return [
        ("inspiral", p_insp),
        ("white", p_white),
        ("bump", p_bump),
        ("spike", p_spike),
        ("comb", p_comb),
        ("hf_offset", p_hf),
    ]


@pytest.fixture
def isolated_caches(monkeypatch):
    for name in (
        "_SIGNAL_CACHE", "_NOISE_CACHE", "_CAND_CACHE", "_CHOICE_CACHE",
        "_PLAN_CACHE", "_SIGNAL_RECORDS", "_NOISE_RECORDS", "_PRICE_CACHE",
        "_OFFSET_CACHE", "_BOUND_PRICE_CACHE",
    ):
        monkeypatch.setattr(gc, name, OrderedDict())
    monkeypatch.setattr(gc, "_SIMILAR", {})


def test_pair_cost_lower_bound_is_sound_across_profiles_and_models(isolated_caches):
    cm_base = _zen5_model_2048()
    for n in (512, 2048):
        cm_n = cm_base if n == 2048 else _scaled_model(cm_base, n)
        cm_unscr = cm_n.unscreened()
        cm_dir = cm_n.with_direct(0.5, single_tier=False, fraction=0.4, base=2.0, multi_frac=0.3)
        cm_gpu = copy.copy(cm_n)
        cm_gpu.feed = {"full": 900.0, "band": {b: 120.0 + 0.4 * b for b in gc.candidate_bands(n)}}
        cm_gpu._sig = None
        models = [
            (cm_n, 64),
            (cm_unscr, 32),
            (cm_dir, 32),
            (cm_gpu, 12),
        ]
        windows = [None, (n // 16, n - n // 16), (64, min(n - 16, 112))]

        for pname, prof in _diverse_profiles(n):
            if pname == "hf_offset":
                assert any(gc.band_offset(prof, n, b) > 0 for b in gc.candidate_bands(n))
            for snr, fd in ((4.8, 0.02), (8.0, 0.005)):
                for win in windows:
                    for cm_use, nt_use in models:
                        for mt in (1, 2, 3):
                            best, _ = gc.choose_chain(
                                prof, n, snr, fd, cost=cm_use, max_tiers=mt,
                                window=win, ntemplates=nt_use,
                            )
                            assert best is not None
                            act = best["cost"]

                            lb = gc.pair_cost_lower_bound(
                                prof, n, snr, fd, cm_use, max_tiers=mt,
                                window=win, ntemplates=nt_use,
                            )
                            assert lb is not None
                            assert lb <= act + 1e-9, (n, pname, snr, fd, win, mt, lb, act)

                            # Verify lazy max_cost branch-and-bound preserves soundness and decision
                            gc._BOUND_PRICE_CACHE.clear()
                            gc._SIMILAR.pop(("pair-lb",), None)
                            for k_sim in [k for k in gc._SIMILAR if k and k[0] == "pair-lb"]:
                                del gc._SIMILAR[k_sim]
                            lb_tight = gc.pair_cost_lower_bound(
                                prof, n, snr, fd, cm_use, max_tiers=mt,
                                window=win, ntemplates=nt_use, max_cost=0.5 * lb - 1.0,
                            )
                            assert lb_tight > 0.5 * lb - 1.0
                            assert lb_tight <= act + 1e-9

                            gc._BOUND_PRICE_CACHE.clear()
                            for k_sim in [k for k in gc._SIMILAR if k and k[0] == "pair-lb"]:
                                del gc._SIMILAR[k_sim]
                            lb_loose = gc.pair_cost_lower_bound(
                                prof, n, snr, fd, cm_use, max_tiers=mt,
                                window=win, ntemplates=nt_use, max_cost=act + 1.0,
                            )
                            assert lb_loose <= act + 1e-9


def test_price_block_sizes_prunes_simulations_and_preserves_winner(isolated_caches, monkeypatch):
    cm_2048 = _zen5_model_2048()
    models_by_n = {n: _scaled_model(cm_2048, n) for n in (1024, 2048, 4096, 8192)}
    monkeypatch.setattr(cal, "device_costs", lambda n, device=None, ntemplates=64, group=None: models_by_n[int(n)])

    sim_ns = []
    orig_sim = gc._simulate

    def tracking_sim(p, n, *args, **kwargs):
        sim_ns.append(int(n))
        return orig_sim(p, n, *args, **kwargs)

    monkeypatch.setattr(gc, "_simulate", tracking_sim)

    # Wrap choose_chain with functools.wraps to verify __wrapped__ unwrapping stays active
    orig_choose = gc.choose_chain

    @functools.wraps(orig_choose)
    def wrapped_choose(*args, **kwargs):
        return orig_choose(*args, **kwargs)

    monkeypatch.setattr(gc, "choose_chain", wrapped_choose)

    fine = np.zeros(8193, dtype=np.float64)
    f_grid = np.arange(1, 8193, dtype=np.float64)
    fine[24:4096] = f_grid[23:4095] ** (-7.0 / 3.0)

    # 1. Block-cost-only pruning (max_pair_cost < 0 at small ntemplates=1)
    out_nt1 = cal.price_block_sizes(
        fine, 0.25, 4096.0, 128, 64, 1, 8.0, 0.01, [1024, 2048, 4096, 8192],
    )
    assert out_nt1[0][1] == 1024
    assert 2048 not in sim_ns and 4096 not in sim_ns and 8192 not in sim_ns

    # 2. Analytic pair_cost_lower_bound pruning where max_pair_cost > 0 (block cost alone < best)
    ref_1024 = gc.rebin_profile(fine, 0.25, 4096.0, 1024).astype(np.float32)
    best_1024, _ = orig_choose(ref_1024, 1024, 8.0, 0.01, cost=models_by_n[1024], window=(64, 960), ntemplates=8)
    assert best_1024 is not None
    ref_2048 = gc.rebin_profile(fine, 0.25, 4096.0, 2048).astype(np.float32)
    lb_2048 = gc.pair_cost_lower_bound(ref_2048, 2048, 8.0, 0.01, models_by_n[2048], window=(64, 1984))
    assert lb_2048 is not None and lb_2048 > 0.0
    # Choose nt_mid so 0 < max_pair_cost(n=2048) < lb_2048 (block cost alone cannot prune, pair_lb does)
    nv1 = 1024 - 128 + 1
    nv2 = 2048 - 128 + 1
    b1 = models_by_n[1024].block
    b2 = models_by_n[2048].block
    # Need 0 < ((b1 / nt + best_1024['cost']) * nv2 / nv1 - b2 / nt) < lb_2048
    denom = best_1024["cost"] * (nv2 / nv1)
    assert denom > 0.0
    nt_lo = (b2 - b1 * (nv2 / nv1)) / denom
    nt_hi = (b2 - b1 * (nv2 / nv1)) / max(denom - 0.8 * lb_2048, 1e-6)
    nt_mid = max(1, int(np.ceil(0.5 * (nt_lo + min(nt_hi, nt_lo + 4.0)))))
    # Adjust slightly if integer rounding pushed outside (0, lb_2048)
    while ((b1 / nt_mid + best_1024["cost"]) / nv1) * nv2 - b2 / nt_mid <= 0.0:
        nt_mid += 1

    for cache_name in ("_PRICE_CACHE", "_CHOICE_CACHE", "_SIGNAL_CACHE", "_NOISE_CACHE",
                       "_SIGNAL_RECORDS", "_NOISE_RECORDS", "_BOUND_PRICE_CACHE"):
        getattr(gc, cache_name).clear()
    gc._SIMILAR.clear()
    sim_ns.clear()

    out_pruned = cal.price_block_sizes(
        fine, 0.25, 4096.0, 128, 64, nt_mid, 8.0, 0.01, [1024, 2048, 4096, 8192],
    )
    pruned_sim_ns = list(sim_ns)

    # Compare against unpruned reference winner across all candidate sizes
    unpruned = []
    for n_cand in (1024, 2048, 4096, 8192):
        nvalid = n_cand - 128 + 1
        q = max(n_cand // 32, 1)
        lo = (64 // q) * q
        ref_n = gc.rebin_profile(fine, 0.25, 4096.0, n_cand).astype(np.float32)
        b_plan, _ = orig_choose(ref_n, n_cand, 8.0, 0.01, cost=models_by_n[n_cand],
                                window=(lo, n_cand - lo), ntemplates=nt_mid)
        c_n = (models_by_n[n_cand].block / nt_mid + b_plan["cost"]) / nvalid
        unpruned.append((c_n, n_cand, b_plan["chain"]))
    unpruned.sort()
    ref_winner = gc.pick_stable(unpruned, lambda o: o[0], lambda o: o[1])

    assert out_pruned[0][1] == ref_winner[1]
    assert out_pruned[0][2] == ref_winner[2]
    assert out_pruned[0][0] == pytest.approx(ref_winner[0])
    # Verify max_pair_cost at n=2048 was positive (so pair_cost_lower_bound, not block cost alone, pruned)
    max_pair_2048 = out_pruned[0][0] * nv2 - b2 / nt_mid
    assert 0.0 < max_pair_2048 < lb_2048
    assert 2048 not in pruned_sim_ns and 4096 not in pruned_sim_ns and 8192 not in pruned_sim_ns

    # 3. Verify ahead=1 prices the first dearer candidate (2048) and prunes subsequent ones (4096, 8192)
    for cache_name in ("_PRICE_CACHE", "_CHOICE_CACHE", "_SIGNAL_CACHE", "_NOISE_CACHE",
                       "_SIGNAL_RECORDS", "_NOISE_RECORDS", "_BOUND_PRICE_CACHE"):
        getattr(gc, cache_name).clear()
    gc._SIMILAR.clear()
    sim_ns.clear()

    out_ahead = cal.price_block_sizes(
        fine, 0.25, 4096.0, 128, 64, nt_mid, 8.0, 0.01, [1024, 2048, 4096, 8192], ahead=1,
    )
    assert [o[1] for o in out_ahead] == [1024, 2048]
    assert 1024 in sim_ns and 2048 in sim_ns
    assert 4096 not in sim_ns and 8192 not in sim_ns
