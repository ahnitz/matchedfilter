"""The plans dismiss fd on average, with the scatter gatemodel.fit_order states: over many model
simulations, each plan judged on draws it was not made from (see test_fdr_calibration's
docstring; tools/split_bias.py checks the same at production size)."""
import numpy as np
import pytest

from matchedfilter import gatechain as gc, gatemodel as gm
from fdr_support import SNR, profile


def _plan_seeds(name, n, fd, seeds, cost=None):
    """Per model seed, every chain's plan (plan_chain) and the pick among them (choose_chain's
    rule), each judged on 1M detections of one independent check simulation: rows of
    (seed, kind, tiers, realised dismissal / fd, half-width)."""
    power = profile(name, n)
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

