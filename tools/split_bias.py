#!/usr/bin/env python3
"""The budget split's selection bias: each plan's dismissal on draws it was not chosen on.

A multi-tier chain's thresholds come from a split search on the gate model's draws
(gatechain.plan_chain). The search keeps the cheapest split, which favours splits whose
dismissal those draws understate, and gatechain._SPLIT_TOLERANCE_Z cuts the budget by the
size of that bias. This measures the bias. Per profile, from --seeds independent model
simulations and at each split tolerance in --z, it makes every chain's plan as
chain_thresholds does, and the pick choose_chain makes with no cost model (the operation
count). It judges each plan on --check independent draws of the same simulation
(signal_draws at other seeds): the fraction of the kept draws (fine maximum at least snr)
that some tier dismisses, over fd.

Every (profile, model seed) is its own simulation and every profile has its own check
draws. One seed shared by every profile, as the gate model's own seed is, gives every
profile the same underlying noise, so their plans share one draw's luck and a mean over
profiles is not a mean over draws.

The summary, per fd, z and tier count:

- the mean over plans and its standard error: the model's part from the seed-to-seed
  scatter of each profile's mean, the check's part bounded as if all of a profile's plans
  shared one check error;
- the sd over plans and the check's own binomial sd within it;
- the worst plan, the mean of each seed's worst, and the worst (profile, chain) averaged
  over seeds;
- the z at which the mean is fd, interpolated between the measured ones.

  python tools/split_bias.py --fd 1e-2 1e-3 --jobs 8            # the 2026-10-27 measurement
  python tools/split_bias.py --n 4096 --fd 1e-3 --seeds 10 --json rows.json
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

#: Check draws per simulation: a 16M-draw one holds about 20 GB at n = 2048.
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


def run_case(job):
    """One (profile, n, fd): every plan's row (thresholds, check counts, realised / fd)."""
    name, pi, n, fd, a = job
    from fdr_audit import profile
    from matchedfilter import gatechain as gc
    from matchedfilter import gatemodel as gm
    snr = a["snr"]
    win = tuple(a["window"]) if a["window"] else (3 * n // 32, n - 3 * n // 32)
    p = gc._norm_profile(profile(name, n), n)
    bands = gc.usable_bands(p, n)
    chains = gc.enumerate_chains(n, a["max_tiers"], bands=bands)
    step = _CHUNK // n
    cols = []
    for c in range(max(1, -(-a["check"] // step))):
        sig = gc.signal_draws(p, n, bands, snr, min(step, a["check"] - c * step),
                              seed=_seeds(fd, n, pi, chunk=c), window=win)
        keep = sig[1][:, 0] >= snr
        cols.append([np.ascontiguousarray(sig[0][keep, i]) for i in range(len(bands))])
        del sig, keep
        _clear(gc)
    check = [np.concatenate([part[i] for part in cols]) for i in range(len(bands))]
    del cols
    kept = int(check[0].size)

    def lost(chain, thresholds):
        bad = np.zeros(kept, bool)
        for b, t in zip(chain, thresholds):
            bad |= check[bands.index(b)] < t
        return int(np.count_nonzero(bad))

    rows = []
    shipped = gc._SPLIT_TOLERANCE_Z
    try:
        for j in range(a["seeds"]):
            s = _seeds(fd, n, pi, j=j)
            sig = gc.signal_draws(p, n, bands, snr, gm._nsamp_for(fd), seed=s, window=win)
            noise = gc.noise_block_maxima(p, n, bands, nsim=gc.model_draws(fd)[1], seed=s, window=win)
            for z in a["z"]:
                gc._SPLIT_TOLERANCE_Z = z
                picks = []
                for chain in chains:
                    for prune in (False, True):
                        pl = gc.plan_chain(sig, noise, bands, list(chain), fd, None, n, snr, prune=prune)
                        if pl is None:
                            continue
                        if prune:
                            picks.append(pl)
                            continue
                        rows.append(dict(kind="chain", profile=name, n=n, fd=fd, seed=s, rep=j, z=z,
                                         chain=list(chain), thresholds=[float(t) for t in pl["thresholds"]],
                                         kept=kept, lost=lost(chain, pl["thresholds"])))
                # the pick as _choose_chain makes it with no cost model
                picks.sort(key=lambda d: d["cost"])
                best = gc.pick_stable(picks, lambda d: d["cost"],
                                      lambda d: (gc._flop_cost(d["chain"], d["reach"], n), d["chain"]))
                if best is not None:
                    rows.append(dict(kind="pick", profile=name, n=n, fd=fd, seed=s, rep=j, z=z,
                                     chain=list(best["chain"]), thresholds=[float(t) for t in best["thresholds"]],
                                     kept=kept, lost=lost(best["chain"], best["thresholds"])))
            _clear(gc)
    finally:
        gc._SPLIT_TOLERANCE_Z = shipped
    for r in rows:
        r["r"] = r["lost"] / r["kept"] / fd
    return rows


def summarise(rows, fd):
    """Mean, its standard error, sd and worst over `rows` (one fd, z, kind and tier count)."""
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
    return dict(plans=r.size, mean=r.mean(), se=math.sqrt(var), sd=r.std(), check_sd=csd.mean(),
                worst=r[i], worst_sd=csd[i], seed_worst=sw.mean(),
                seed_worst_se=sw.std(ddof=1) / math.sqrt(sw.size) if sw.size > 1 else 0.0,
                per_seed=r.size / sw.size, pc_worst=pc)


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
                    help="check draws per profile (default max(4M, 16000 / fd): about 9000 dismissed draws at 1e-3)")
    ap.add_argument("--z", type=float, nargs="+", default=[0.0, 0.5, 0.75, 1.0])
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
    win = None if a.window is None else [int(x) for x in a.window.split(",")]
    jobs, ncheck = [], {}
    for fd in a.fd:
        ncheck[fd] = a.check or int(max(4e6, 1.6e4 / fd))
        opts = dict(snr=a.snr, window=win, seeds=a.seeds, z=sorted(set(a.z)), max_tiers=a.max_tiers,
                    check=ncheck[fd])
        jobs += [(nm, every.index(nm), a.n, fd, opts) for nm in names]
    t0 = time.time()
    if a.jobs > 1:
        with mp.get_context("spawn").Pool(a.jobs) as pool:
            parts = pool.map(run_case, jobs, chunksize=1)
    else:
        parts = [run_case(j) for j in jobs]
    rows = [r for part in parts for r in part]
    from matchedfilter import gatechain as gc
    print("n %d, snr %.2f, %d profiles x %d model seeds, shipped z %.2f (%.0f s)"
          % (a.n, a.snr, len(names), a.seeds, gc._SPLIT_TOLERANCE_Z, time.time() - t0))
    print("realised dismissal / fd on independent draws; se: the mean's; check sd: binomial, per plan")
    for fd in a.fd:
        kept = [r["kept"] for r in rows if r["fd"] == fd]
        print("fd %g, %d check draws per profile (%d to %d kept)" % (fd, ncheck[fd], min(kept), max(kept)))
        for kind in ("chain", "pick"):
            means = defaultdict(dict)
            for z in sorted(set(a.z)):
                for k in range(1, a.max_tiers + 1):
                    sel = [r for r in rows if r["fd"] == fd and r["z"] == z and r["kind"] == kind
                           and len(r["chain"]) == k]
                    if not sel or (k == 1 and kind == "chain" and z != min(a.z)):
                        continue
                    s = summarise(sel, fd)
                    means[k][z] = s["mean"]
                    print("  %-5s z %.2f tiers %d: %5d plans  mean %.3f +- %.3f  sd %.3f (check %.3f)  "
                          "worst %.3f +- %.3f  seed-worst %.3f +- %.3f (of %.0f)  worst over seeds %s %.3f +- %.3f"
                          % (kind, z, k, s["plans"], s["mean"], s["se"], s["sd"], s["check_sd"], s["worst"],
                             s["worst_sd"], s["seed_worst"], s["seed_worst_se"], s["per_seed"],
                             "%s %s" % (s["pc_worst"][2][0], ",".join(map(str, s["pc_worst"][2][1]))),
                             s["pc_worst"][0], s["pc_worst"][1]))
            for k in sorted(means):
                pts = sorted(means[k].items())
                cross = [z0 + (1 - m0) * (z1 - z0) / (m1 - m0) for (z0, m0), (z1, m1) in zip(pts, pts[1:])
                         if (m0 - 1) * (m1 - 1) <= 0 and m1 != m0]
                if cross:
                    print("  %-5s tiers %d: mean 1 at z %.2f" % (kind, k, cross[0]))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(rows, f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
