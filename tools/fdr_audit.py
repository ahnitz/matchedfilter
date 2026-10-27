#!/usr/bin/env python3
"""The hierarchical chain's false dismissal against the flat filter, by injection, two-sided.

Each case is a reference profile, a chain and a block size n. Signals of intrinsic SNR
`--snr` arrive at uniformly random real-valued times in the searched window, in unit
Gaussian noise. A detection is a block whose flat (full-resolution) peak in the window is
at least snr: the condition the gate model sets its budget on. The chain, at the gate model's
thresholds (gatechain.chain_thresholds), misses a detection when it reports no peak for that
block or one below snr. Every detection both filters report must carry the flat filter's
value.

A case's misses are tested two-sided against the budget (binomial). A model that dismisses
too much fails, and so does one that dismisses far too little: such gates pass work the
budget would have dismissed, and a 100x too conservative model once hid two model errors. A
multi-tier chain's budget is cut by the selection bias of its split search
(gatechain._SPLIT_TOLERANCE_Z): it aims at fd, as a single tier does. With
--q15 the same chains also run with the Q15 screen as every tier but the last, where this
back end has one. The gate model leaves the Q15 statistic's rounding out (about 0.01 in
snr: it lifts a tier's maxima a little), so a Q15 chain may dismiss less than its budget
where a gate sits within that of snr: such a case is reported ("under") but fails only with
--strict-q15. Dismissing more than the budget always fails.

  python tools/fdr_audit.py                                  # the default sweep
  python tools/fdr_audit.py --n 4096 --fd 1e-3 --inj 200000 --profiles aligo_o4_inspiral
  python tools/fdr_audit.py --chains auto --window 192,1856  # what chain selection picks
  python tools/fdr_audit.py --chains 256,512,1024 --q15 --json out.json

Profiles: power laws "f^E" (power k^E in bins 1 .. n/2 - 1), "inspiral" (k^-7/3 with a
low-frequency knee), and the shapes of tests/spectral_profiles.py. Chains: comma-separated
bands, ";" between chains, "default" for n/2; n/8,n/2; n/8,n/4,n/2; n/16,n/4, or "auto" for
gatechain.choose_chain's pick under this machine's calibrated costs. Exit status 1 when any
case is off budget (p < --alpha after a Bonferroni correction over the cases) or a value
disagrees.
"""
import argparse
import json
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _d in (os.path.join(ROOT, "tests"), ROOT):
    if _d not in sys.path:
        sys.path.insert(0, _d)

#: Batch of blocks per engine call.
_B = 64


def law(n, e):
    p = np.zeros(n)
    k = np.arange(1, n // 2).astype(float)
    p[1:n // 2] = k ** e
    return p / p.sum()


def inspiral(n):
    p = np.zeros(n)
    k = np.arange(1, n // 2).astype(float)
    p[1:n // 2] = k ** (-7 / 3.) / ((0.015 * n / k) ** 4 + 1)
    return p / p.sum()


def profile(name, n):
    """The named reference profile at block size n, normalised to unit sum."""
    if name.startswith("f^"):
        return law(n, float(name[2:]))
    if name == "inspiral":
        return inspiral(n)
    from spectral_profiles import make_spectral_profile
    p = make_spectral_profile(name, n).astype(np.float64)
    return p / p.sum()


def default_profiles():
    from spectral_profiles import SHAPE_NAMES
    return ["f^-2", "f^-1", "f^0", "f^1", "inspiral"] + [s for s in SHAPE_NAMES if s != "inspiral_canonical"]


def chains_for(spec, n):
    """The chains `spec` names at block size n (None for "auto")."""
    if spec == "auto":
        return [None]
    if spec == "default":
        return [(n // 2,), (n // 8, n // 2), (n // 8, n // 4, n // 2), (n // 16, n // 4)]
    return [tuple(int(b) for b in c.split(",")) for c in spec.split(";")]


def binom_two_sided(x, n, p):
    """Two-sided binomial p-value of x successes in n at probability p (outcomes no more
    likely than x)."""
    if n == 0:
        return 1.0
    k = np.arange(n + 1)
    lg = np.array([math.lgamma(i + 1) for i in range(n + 1)])
    pm = np.exp(lg[n] - lg - lg[::-1] + k * math.log(p) + (n - k) * math.log1p(-p))
    return float(min(1.0, pm[pm <= pm[x] * (1 + 1e-9)].sum()))


def run_case(job):
    """One case: (profile, n, chain, args) -> its row."""
    name, n, chain, a = job
    import matchedfilter as mf
    import matchedfilter._core as _core
    from matchedfilter import gatechain as gc
    power = profile(name, n)
    win = None if a["window"] is None else tuple(a["window"])
    ws, we = (0, n) if win is None else win
    row = dict(profile=name, n=n, snr=a["snr"], fd=a["fd"], window=[ws, we])
    if chain is None:
        from matchedfilter import _calibration
        best, _ = gc.choose_chain(power, n, a["snr"], a["fd"], cost=_calibration.calibrate_costs(n, 64),
                                  window=win)
        if best is None:
            return dict(row, chain=None, error="no chain")
        chain = tuple(best["chain"])
    plan = gc.chain_thresholds(power, n, a["snr"], a["fd"], chain, window=win)
    row["chain"] = list(chain)
    if plan is None:
        return dict(row, error="no plan")
    thr = [float(x) for x in plan["thresholds"]]
    row["thresholds"] = thr
    h = np.sqrt(power).astype(np.complex64)
    hc = np.conj(h)
    flat = mf.MatchedFilter(n, ndata=_B, ntemplates=1)
    flat.set_templates(hc[None, :])

    def engine(q15):
        e = _core.HMF(n, _B, 1, list(chain), 8)
        e.set_reference(power.astype(np.float32))
        e.set_thresholds(thr)
        e.set_template(0, hc)
        if not e.set_q15(q15) and q15:
            return None
        return e

    engines = {"fp32": engine(False)}
    if a["q15"]:
        q = engine(True)
        if q is not None:
            engines["q15"] = q
    peaks = {k: np.empty((_B, 1), mf.PEAK_DTYPE) for k in engines}
    cnt = np.empty(_B, np.int32)
    ei, ev, em = np.empty(0, np.int64), np.empty(0, np.complex64), np.empty(0, np.float32)
    rng = np.random.default_rng([a["seed"], n, sum(map(ord, name))])
    k = np.arange(n)
    det = 0
    miss = dict.fromkeys(engines, 0)
    mismatch = dict.fromkeys(engines, 0)
    for _ in range(max(1, a["inj"] // _B)):
        # a signal arriving at t peaks at lag n - t (the engine correlates with the conjugate)
        lag = rng.uniform(ws, we, _B)
        D = (a["snr"] * h[None, :] * np.exp(2j * np.pi * (n - lag)[:, None] * k[None, :] / n)
             + (rng.standard_normal((_B, n)) + 1j * rng.standard_normal((_B, n)))).astype(np.complex64)
        flat.set_data(D)
        if win is None:
            zf = np.abs(flat.run(binsize=n, threshold=0.0)["value"][:, 0, 0])
        else:
            zf = np.abs(flat.run(binsize=we - ws, threshold=0.0, window=win)["value"][:, 0, 0])
        hit = zf >= a["snr"]
        det += int(hit.sum())
        for key, e in engines.items():
            for d in range(_B):
                e.set_data(d, D[d])
            e.run(0, _B, 0, 1, we - ws, a["snr"], ws, we, ei, ev, em, cnt, peaks[key])
            p = peaks[key][:, 0]
            got = (p["index"] >= 0) & (np.abs(p["value"]) >= a["snr"])
            miss[key] += int((hit & ~got).sum())
            both = hit & got
            mismatch[key] += int((np.abs(np.abs(p["value"][both]) - zf[both]) > 1e-3 * zf[both]).sum())
    row["detections"] = det
    row["engines"] = {}
    for key in engines:
        pv = binom_two_sided(miss[key], det, a["fd"])
        row["engines"][key] = dict(misses=miss[key], ratio=miss[key] / max(det, 1) / a["fd"],
                                   p=pv, mismatches=mismatch[key])
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--n", type=int, nargs="+", default=[2048])
    ap.add_argument("--profiles", default=None, help="comma-separated (default: every profile)")
    ap.add_argument("--chains", default="default")
    ap.add_argument("--snr", type=float, default=5.5)
    ap.add_argument("--fd", type=float, default=0.01)
    ap.add_argument("--inj", type=int, default=4000, help="injections per case")
    ap.add_argument("--window", default=None, help="START,END: search lags [START, END) only")
    ap.add_argument("--q15", action="store_true", help="also run the Q15-screened chains")
    ap.add_argument("--strict-q15", action="store_true",
                    help="a Q15 chain dismissing less than its budget fails too")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--alpha", type=float, default=1e-3, help="family-wise level over the cases")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--json", default=None, help="write every row here")
    a = ap.parse_args(argv)
    names = a.profiles.split(",") if a.profiles else default_profiles()
    win = None if a.window is None else [int(x) for x in a.window.split(",")]
    opts = dict(snr=a.snr, fd=a.fd, inj=a.inj, window=win, q15=a.q15, seed=a.seed)
    jobs = [(nm, n, ch, opts) for n in a.n for nm in names for ch in chains_for(a.chains, n)]
    t0 = time.time()
    if a.jobs > 1:
        with mp.get_context("spawn").Pool(a.jobs) as pool:
            rows = pool.map(run_case, jobs)
    else:
        rows = [run_case(j) for j in jobs]
    tests = sum(len(r.get("engines", {})) for r in rows)
    level = a.alpha / max(tests, 1)
    bad = under = 0
    print("snr %.2f fd %g, %d injections a case, window %s; off budget at p < %.1e (%g over %d tests)"
          % (a.snr, a.fd, a.inj, win or "whole block", level, a.alpha, tests))
    for r in rows:
        head = "  n=%-5d %-18s %-20s" % (r["n"], r["profile"], ",".join(map(str, r["chain"] or ["?"])))
        if "error" in r:
            print(head, r["error"])
            continue
        for key, e in r["engines"].items():
            off = e["p"] < level
            low = off and e["ratio"] < 1 and key == "q15" and not a.strict_q15
            fail = (off and not low) or e["mismatches"]
            bad += bool(fail)
            under += bool(low)
            print("%s %-4s thr [%s] det %6d miss %5d  %.2fx  p %.3g%s%s" % (
                head, key, ",".join("%.2f" % t for t in r["thresholds"]), r["detections"], e["misses"],
                e["ratio"], e["p"], "  mismatches %d" % e["mismatches"] if e["mismatches"] else "",
                "  <-- OFF" if fail else "  (under: Q15 rounding)" if low else ""), flush=True)
    print("%d of %d off budget or mismatched, %d Q15 under budget (%.0f s)"
          % (bad, tests, under, time.time() - t0))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(rows, f, indent=1)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
