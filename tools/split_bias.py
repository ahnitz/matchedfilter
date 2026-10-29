#!/usr/bin/env python3
"""Each plan's false dismissal on draws it was not made from: the budget's calibration.

A plan's structure (its chain's split of the budget between tiers, and the direct refine's
half-width where the cost model prices one) is searched on half the gate model's detections
and its thresholds fitted on the other half (gatechain.plan_chain), so that its dismissal
has mean fd and the tail gatemodel.fit_order sets, with no correction for the search. This
measures that. Per profile, from --seeds independent model simulations, it makes every
chain's plan as chain_thresholds does, picks a chain as choose_chain does and runs it with
that chain's plan (as a filter does), and judges each on
--check independent detections of the same simulation (signal_draws at other seeds): the
fraction some tier dismisses or the direct refine's window misses (the fine maximum further
than the half-width from the last tier's coarse maximum), over fd.

Every (profile, model seed) is its own simulation and every profile has its own check
draws. One seed shared by every profile, as the gate model's own seed is, gives every
profile the same underlying noise, so their plans share one draw's luck and a mean over
profiles is not a mean over draws.

The cost model: with none, the operation count (no direct refine); --cost FILE takes the
models stored in an MF_COST_FILE (this n's, at 64 templates), and --taps L also prices a
direct refine of L taps at the stored ticks per lag x tap (HierarchicalFilter._direct_price),
so the plans choose half-widths and their windows' misses are counted.

The summary, per fd, kind (every chain's plan, or the pick) and tier count, and pooled:

- the mean over plans and its standard error: the model's part from the seed-to-seed
  scatter of each profile's mean, the check's part bounded as if all of a profile's plans
  shared one check error;
- the sd over plans and the check's own binomial sd within it, and the share of plans
  above 1.25 fd (decision D1's tail: at most 5%) with gatemodel.fit_order's own;
- the worst plan, the mean of each seed's worst, and the worst (profile, chain) averaged
  over seeds;
- with a direct refine, the plans with a window, the mean share of the losses their windows
  miss, and the plans whose fit half left their window no room (refined by transform); and
  the plans grouped by their window's share of the search half's budget (a grouping made
  before the fit, so it selects nothing on the outcome).

  python tools/split_bias.py --fd 1e-2 1e-3 --jobs 8
  python tools/split_bias.py --n 4096 --fd 1e-3 --seeds 10 --json rows.json
  python tools/split_bias.py --fd 1e-3 --cost costs.json --taps 256 --jobs 8
"""
import argparse
import json
import math
import multiprocessing as mp
import os
import sys
import time
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _d in (os.path.join(ROOT, "tools"), os.path.join(ROOT, "tests"), ROOT):
    if _d not in sys.path:
        sys.path.insert(0, _d)

#: Check detections per simulation: a 2M-detection one holds about 0.7 GB at n = 2048.
_CHUNK = 2000000 * 2048


def _clear(gc):
    """Drop the gate model's caches: a worker makes many simulations, each held otherwise."""
    for c in (gc._SIGNAL_CACHE, gc._SIGNAL_RECORDS, gc._NOISE_RECORDS, gc._NOISE_CACHE,
              gc._KEPT, gc._CAND_CACHE, gc._PLAN_CACHE, gc._SIMILAR):
        c.clear()


def _seeds(fd, n, pi, j=None, chunk=None):
    """A model replicate's seed (j) or a check chunk's (chunk). Within one n and fd every
    profile index pi < 20, replicate and chunk has its own, and none is the gate model's own
    seed (gatechain._SEED)."""
    base = 10000 * int(round(-math.log10(fd))) + 1000 * (n // 1024) + pi
    return 100000 + base + 20 * j if j is not None else 700000 + base + 100 * chunk


def _cost_model(a, n):
    """The cost model the plans are priced with (None: the operation count)."""
    if not a["cost"]:
        return None
    from matchedfilter import gatechain as gc
    with open(a["cost"]) as f:
        rec = json.load(f)
    keys = [k for k in rec if k.startswith("%d,64," % n)]
    if not keys:
        raise SystemExit("no %d-point cost model at 64 templates in %s" % (n, a["cost"]))
    cm = gc.CostModel.from_dict(rec[sorted(keys)[0]])
    if a["taps"]:
        lagtap = [v["value"] for k, v in rec.items() if k.startswith("choice|direct-lagtap|")]
        if not lagtap:
            raise SystemExit("no direct-lagtap price in %s" % a["cost"])
        L = 32.0 * max(1, int(round(a["taps"] / 32.0)))
        cm = cm.with_direct(lagtap[0] * L + 4.0)     # HierarchicalFilter._direct_price
    return cm


def run_case(job):
    """One (profile, n, fd): every plan's row (thresholds, half-width, check counts)."""
    name, pi, n, fd, a = job
    from fdr_audit import profile
    from matchedfilter import gatechain as gc
    snr = a["snr"]
    win = tuple(a["window"]) if a["window"] else (3 * n // 32, n - 3 * n // 32)
    p = gc._norm_profile(profile(name, n), n)
    bands = gc.usable_bands(p, n)
    chains = gc.enumerate_chains(n, a["max_tiers"], bands=bands)
    cost = _cost_model(a, n)
    step = _CHUNK // n
    cols, dcols = [], []
    for c in range(max(1, -(-a["check"] // step))):
        (C, F), (fat, cat) = gc.signal_draws(p, n, bands, snr, min(step, a["check"] - c * step),
                                             seed=_seeds(fd, n, pi, chunk=c), window=win,
                                             lags_too=True)
        keep = F[:, 0] >= snr
        cols.append([np.ascontiguousarray(C[keep, i]) for i in range(len(bands))])
        # each band's distance from its coarse maximum to the fine one, in its coarse samples
        dcols.append([(np.abs(fat[keep] - cat[keep, i]) / (n // b)).astype(np.float32)
                      for i, b in enumerate(bands)])
        del C, F, fat, cat, keep
        _clear(gc)
    check = [np.concatenate([part[i] for part in cols]) for i in range(len(bands))]
    dist = [np.concatenate([part[i] for part in dcols]) for i in range(len(bands))]
    del cols, dcols
    kept = int(check[0].size)

    def judge(kind, s, j, pl):
        chain, th, hw = pl["chain"], pl["thresholds"], pl["halfwidth"]
        bad = np.zeros(kept, bool)
        for b, t in zip(chain, th):
            bad |= check[bands.index(b)] < t
        tiers = int(np.count_nonzero(bad))
        window = 0
        if hw is not None:
            out = dist[bands.index(chain[-1])] > hw
            window = int(np.count_nonzero(out))
            bad |= out
        return dict(kind=kind, profile=name, n=n, fd=fd, seed=s, rep=j, chain=list(chain),
                    thresholds=[float(t) for t in th], halfwidth=hw,
                    search_halfwidth=pl["search"]["halfwidth"],
                    search_share=pl["search"]["missed"] / max(pl["search"]["K"], 1), kept=kept,
                    lost=int(np.count_nonzero(bad)), lost_tiers=tiers, lost_window=window)

    rows = []
    for j in range(a["seeds"]):
        s = _seeds(fd, n, pi, j=j)
        sig, lags = gc.signal_draws(p, n, bands, snr, gc.model_draws(fd)[0], seed=s, window=win,
                                    lags_too=True)
        noise = gc.noise_block_maxima(p, n, bands, nsim=gc.model_draws(fd)[1], seed=s, window=win)
        picks, given = [], {}
        for chain in chains:
            for prune in (False, True):
                pl = gc.plan_chain(sig, noise, bands, list(chain), fd, cost, n, snr, prune=prune,
                                   lags=lags)
                if pl is None:
                    continue
                if prune:
                    picks.append(pl)
                else:
                    given[tuple(chain)] = pl
                    rows.append(judge("chain", s, j, pl))
        # the pick as _choose_chain makes it, run with the plan chain_thresholds makes for it
        picks.sort(key=lambda d: d["cost"])
        best = gc.pick_stable(picks, lambda d: d["cost"],
                              lambda d: (gc._flop_cost(d["chain"], d["search"]["reach"], n), d["chain"]))
        if best is not None and tuple(best["chain"]) in given:
            rows.append(judge("pick", s, j, given[tuple(best["chain"])]))
        _clear(gc)
    for r in rows:
        r["r"] = r["lost"] / r["kept"] / fd
    return rows


def summarise(rows, fd):
    """Mean, its standard error, sd, tail share and worst over `rows` (one fd, kind and tier
    count, or pooled)."""
    r = np.array([x["r"] for x in rows])
    csd = np.array([math.sqrt(max(x["lost"], 1) * (1 - x["lost"] / x["kept"])) / x["kept"] / fd for x in rows])
    by_p = defaultdict(lambda: defaultdict(list))
    for x in rows:
        by_p[x["profile"]][x["rep"]].append(x["r"])
    var = 0.0
    for name, reps in by_p.items():
        w = sum(map(len, reps.values())) / r.size
        u = np.array([np.mean(v) for v in reps.values()])
        cs = np.mean([c for c, x in zip(csd, rows) if x["profile"] == name])
        var += w * w * ((u.var(ddof=1) / u.size if u.size > 1 else 0.0) + cs * cs)
    seed_worst = defaultdict(float)
    by_pc = defaultdict(list)
    for x in rows:
        seed_worst[x["rep"]] = max(seed_worst[x["rep"]], x["r"])
        by_pc[(x["profile"], tuple(x["chain"]))].append(x["r"])
    sw = np.array(list(seed_worst.values()))
    pc = max((np.mean(v), np.std(v, ddof=1) / math.sqrt(len(v)) if len(v) > 1 else 0.0, k)
             for k, v in by_pc.items())
    i = int(np.argmax(r))
    win = [x for x in rows if x["halfwidth"] is not None]
    return dict(plans=r.size, mean=r.mean(), se=math.sqrt(var), sd=r.std(), check_sd=csd.mean(),
                over=float(np.mean(r > 1.25)), worst=r[i], worst_sd=csd[i], seed_worst=sw.mean(),
                seed_worst_se=sw.std(ddof=1) / math.sqrt(sw.size) if sw.size > 1 else 0.0,
                per_seed=r.size / sw.size, pc_worst=pc, windows=len(win),
                window_share=float(np.mean([x["lost_window"] / max(x["lost"], 1) for x in win])) if win else 0.0,
                fallback=sum(x["halfwidth"] is None and x["search_halfwidth"] is not None for x in rows))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--n", type=int, default=2048)
    ap.add_argument("--fd", type=float, nargs="+", default=[1e-2, 1e-3])
    ap.add_argument("--snr", type=float, default=5.5)
    ap.add_argument("--window", default=None,
                    help="START,END: search lags [START, END) (default 3n/32 to n - 3n/32: 192,1856 at 2048)")
    ap.add_argument("--profiles", default=None, help="comma-separated (default: fdr_audit's default profiles)")
    ap.add_argument("--seeds", type=int, default=30, help="model simulations per profile (at most 50)")
    ap.add_argument("--check", type=int, default=None,
                    help="check detections per profile (default max(4M, 16000 / fd): 16,000 dismissed at 1e-3)")
    ap.add_argument("--cost", default=None, help="an MF_COST_FILE whose cost models price the plans")
    ap.add_argument("--taps", type=int, default=0, help="with --cost: price a direct refine of this many taps")
    ap.add_argument("--max-tiers", type=int, default=3)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--json", default=None, help="write every plan's row here")
    a = ap.parse_args(argv)
    from fdr_audit import default_profiles
    every = default_profiles()
    names = a.profiles.split(",") if a.profiles else every
    unknown = [nm for nm in names if nm not in every]
    if unknown or len(every) > 20 or a.seeds > 50:
        ap.error("profiles must be among fdr_audit's %d defaults, and --seeds at most 50 (_seeds)"
                 % len(every))
    if a.taps and not a.cost:
        ap.error("--taps prices a direct refine in a cost model: give --cost")
    win = None if a.window is None else [int(x) for x in a.window.split(",")]
    jobs, ncheck = [], {}
    for fd in a.fd:
        ncheck[fd] = a.check or int(max(4e6, 1.6e4 / fd))
        opts = dict(snr=a.snr, window=win, seeds=a.seeds, max_tiers=a.max_tiers, check=ncheck[fd],
                    cost=a.cost, taps=a.taps)
        jobs += [(nm, every.index(nm), a.n, fd, opts) for nm in names]
    t0 = time.time()
    if a.jobs > 1:
        with mp.get_context("spawn").Pool(a.jobs) as pool:
            parts = pool.map(run_case, jobs, chunksize=1)
    else:
        parts = [run_case(j) for j in jobs]
    rows = [r for part in parts for r in part]
    from matchedfilter import gatemodel as gm
    print("n %d, snr %.2f, %d profiles x %d model seeds, cost %s%s (%.0f s)"
          % (a.n, a.snr, len(names), a.seeds, a.cost or "operation count",
             ", direct refine of %d taps" % a.taps if a.taps else "", time.time() - t0))
    print("realised dismissal / fd on independent draws; se: the mean's; check sd: binomial, per plan;"
          " >1.25: share of plans")
    for fd in a.fd:
        kept = [r["kept"] for r in rows if r["fd"] == fd]
        j = gm.fit_order(fd)
        tail = gm.plan_tail(fd, int(round(j / fd)) - 1)   # P(plan > 1.25 fd)
        print("fd %g, %d check detections per profile (%d to %d kept); fit order %d, model's >1.25 %.3f"
              % (fd, ncheck[fd], min(kept), max(kept), j, tail))
        for kind in ("chain", "pick"):
            groups = [("tiers %d" % k, [r for r in rows if r["fd"] == fd and r["kind"] == kind
                                        and len(r["chain"]) == k]) for k in range(1, a.max_tiers + 1)]
            groups.append(("pooled", [r for r in rows if r["fd"] == fd and r["kind"] == kind]))
            for label, sel in groups:
                if not sel:
                    continue
                s = summarise(sel, fd)
                print("  %-5s %-8s: %5d plans  mean %.3f +- %.3f  sd %.3f (check %.3f)  >1.25 %.3f  "
                      "worst %.3f +- %.3f  seed-worst %.3f +- %.3f (of %.0f)  worst over seeds %s %.3f +- %.3f"
                      "%s"
                      % (kind, label, s["plans"], s["mean"], s["se"], s["sd"], s["check_sd"], s["over"],
                         s["worst"], s["worst_sd"], s["seed_worst"], s["seed_worst_se"], s["per_seed"],
                         "%s %s" % (s["pc_worst"][2][0], ",".join(map(str, s["pc_worst"][2][1]))),
                         s["pc_worst"][0], s["pc_worst"][1],
                         ("  windows %d (miss %.3f of the losses), to transform %d"
                          % (s["windows"], s["window_share"], s["fallback"])) if a.taps else ""))
    if a.taps:
        print("by the window's share of the search half's budget (every chain's plan and the pick):")
        for fd in a.fd:
            for lo, hi in ((-1, 0), (0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.01)):
                sel = [r for r in rows if r["fd"] == fd and r["search_halfwidth"] is not None
                       and lo < r["search_share"] <= hi] if lo >= 0 else \
                      [r for r in rows if r["fd"] == fd and r["search_halfwidth"] is None]
                if sel:
                    x = np.array([r["r"] for r in sel])
                    print("  fd %g %-12s %6d plans  mean %.3f +- %.3f (plans as independent)  >1.25 %.3f  "
                          "to transform %d" % (fd, "no window" if lo < 0 else "(%.2f, %.2f]" % (lo, min(hi, 1)),
                                               x.size, x.mean(), x.std() / math.sqrt(x.size),
                                               float(np.mean(x > 1.25)),
                                               sum(r["halfwidth"] is None for r in sel if lo >= 0)))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(rows, f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
