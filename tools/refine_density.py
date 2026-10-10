#!/usr/bin/env python3
"""Measured against modelled refine density, per (n, chain), on the realistic ladder workload.

Runs tools/ladder.py with the given arguments and, at exit, for every hierarchical plan: the
pairs it ran, the fraction it refined, and the fraction the gate model predicts for its chain
(gatechain.chain_thresholds' refine reach, from noise draws of the plan's own reference).

    python tools/refine_density.py --bank BANK --profiles PROFILES --device cpu --tops 2 --segments 4

See docs/gate-model.md ("Refine density on realistic data").
"""
import atexit, os, sys, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "python"))
import numpy as np
import matchedfilter as mf

PLANS = []
_orig = mf.HierarchicalFilter.__init__


def _init(self, *a, **k):
    _orig(self, *a, **k)
    PLANS.append(self)


mf.HierarchicalFilter.__init__ = _init


def report():
    g = mf._gatechain
    agg = {}
    for p in PLANS:
        if p._chain is None or p._pending_ref is None:
            continue
        pairs, ref = p.stats
        if not pairs:
            continue
        pl = g.chain_thresholds(p._pending_ref, p.n, p._fs_snr or p.snr, p.fd, p._chain,
                                cost=p._cost_model(), window=p.search_window)
        a = agg.setdefault((p.n, tuple(p._chain)), [0, 0, 0.0, 0.0])
        a[0] += pairs; a[1] += ref; a[2] += pairs * pl["reach"][-1]
        ts = p.tier_stats
        if ts:
            a[3] += ts[0][1]
    for k, (pairs, ref, mod, t1) in sorted(agg.items()):
        print("[obs] n=%d chain=%s pairs=%d refine measured %.5f modelled %.5f excess %.5f  tier0-pass %.4f"
              % (k[0], k[1], pairs, ref / pairs, mod / pairs, (ref - mod) / pairs, t1 / pairs), file=sys.stderr)


atexit.register(report)
sys.argv = [os.path.join(HERE, "ladder.py")] + sys.argv[1:]
runpy.run_path(os.path.join(HERE, "ladder.py"), run_name="__main__")
