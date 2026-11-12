#!/usr/bin/env python3
"""The hierarchical chain's false dismissal against the flat filter, by injection, two-sided.

Each case is a reference profile, a chain and a block size n. Signals of intrinsic SNR
`--snr` arrive at uniformly random real-valued times in the searched window, in unit
Gaussian noise. A detection is a block whose flat (full-resolution) peak in the window is
at least snr: the condition the gate model sets its budget on. The chain, at the gate model's
thresholds (gatechain.chain_thresholds), misses a detection when it reports no peak for that
block or one below snr. Every detection both filters report must carry the flat filter's
value.

A plan's own dismissal scatters about fd by construction (its thresholds are fitted on
gatemodel.fit_order's j-th of the model's draws: sd about fd / sqrt(j), with j about 47),
so a case is tested against what the model says its plan dismisses: the share of --check
detections of an independent model simulation that the plan's tiers dismiss. The two counts
are compared two-sided (the engine's misses among all the misses, binomial at the engine's
share of the detections). A model that dismisses too much fails, and so does one that
dismisses far too little: such gates pass work the budget would have dismissed, and a 100x
too conservative model once hid two model errors. That the plans dismiss fd on average is
the model's own claim, measured by tools/split_bias.py; the summary adds the pooled misses
of every case over their budget, which shows it end to end to the scatter of a few dozen
plans. With --q15 the same chains also run with the Q15 screen as every tier but the last,
where this back end has one. The gate model leaves the Q15 statistic's rounding out (about
0.01 in snr: it lifts a tier's maxima a little), so a Q15 chain may dismiss less than its
plan where a gate sits within that of snr: such a case is reported ("under") but fails only
with --strict-q15. Dismissing more than the plan always fails.

  python tools/fdr_audit.py                                  # the default sweep
  python tools/fdr_audit.py --n 4096 --fd 1e-3 --inj 200000 --profiles aligo_o4_inspiral
  python tools/fdr_audit.py --chains auto --window 192,1856  # what chain selection picks
  python tools/fdr_audit.py --chains 256,512,1024 --q15 --json out.json
  python tools/fdr_audit.py --bank 16 --q15                  # tier-0 pair centroids too
  python tools/fdr_audit.py --bank 64 --group 8 --q15        # centroids of eight, as in production

With --bank NT each case is a bank of NT templates of the profile's output power, in groups
of four (--group: another size) whose members differ by up to a coarse lag, a phase and a small chirp, at the
reference's power: what tier-0 pair centroids
(gatechain.cluster_tier0_candidates) merge. The library's own HierarchicalFilter runs it at
the case's chain (MF_CHAIN_FORCE, which leaves clustering to the model, as in production),
with the centroids ("t0c") and without ("flat0"), each at its own plan's thresholds, and each
injection is of one template, searched by that template's row. A clustered plan's thresholds
are solved for the cluster's conservative retention alpha; its modelled dismissal draws each
member at its own retention (member_alphas), so a member alpha the engine does not attain,
or a model that misprices them, is off the plan. Multi-tier chains only: a centroid is a
tier-0 gate.

Profiles: power laws "f^E" (power k^E in bins 1 .. n/2 - 1), "inspiral" (k^-7/3 with a
low-frequency knee), and the shapes of tests/spectral_profiles.py. Chains: comma-separated
bands, ";" between chains, "default" for n/2; n/8,n/2; n/8,n/4,n/2; n/16,n/4, or "auto" for
gatechain.choose_chain's pick under this machine's calibrated costs. Exit status 1 when any
case is off its plan (p < --alpha after a Bonferroni correction over the cases) or a value
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


def modelled(power, n, chain, thresholds, snr, window, count, seed=9770, alpha0=1.0, alpha1=1.0):
    """(dismissed, detections): of `count` detections of a model simulation independent of
    the plans' (seeds seed, seed + 1, ...: 2M detections each), those some tier of chain at
    these thresholds dismisses. alpha0 / alpha1: the signal's retention at the first / second
    tier (a tier-0 centroid's / tier-1 sub-centroid's member's)."""
    from matchedfilter import gatechain as gc
    bands = gc.usable_bands(power, n)
    b1 = chain[1] if len(chain) >= 2 else None
    alphas = (None if alpha0 >= 1.0 and alpha1 >= 1.0 else
              tuple(alpha0 if b == chain[0] else (alpha1 if b == b1 else 1.0) for b in bands))
    lost = total = 0
    step = 2000000
    for c in range(-(-int(count) // step)):
        C, F = gc.signal_draws(power, n, bands, snr, min(step, int(count) - c * step), seed=seed + c,
                               window=window, alphas=alphas)
        det = F[:, 0] >= snr
        bad = np.zeros(int(det.sum()), bool)
        for b, t in zip(chain, thresholds):
            bad |= C[det, bands.index(b)] < t
        lost += int(bad.sum())
        total += int(det.sum())
    return lost, total


def run_profile(job):
    """Every case of one (profile, n): (profile, n, chains, args) -> their rows."""
    name, n, chains, a = job
    return [run_case((name, n, chain, a)) for chain in chains]


def run_case(job):
    """One case: (profile, n, chain, args) -> its row."""
    name, n, chain, a = job
    if a.get("bank"):
        return run_bank_case(job)
    import matchedfilter as mf
    import matchedfilter._core as _core
    from matchedfilter import gatechain as gc
    power = profile(name, n)
    win = None if a["window"] is None else tuple(a["window"])
    ws, we = (0, n) if win is None else win
    row = dict(profile=name, n=n, snr=a["snr"], fd=a["fd"], window=[ws, we])
    if chain is None:
        from matchedfilter import _calibration
        # a device's chains as the library plans them there (a GPU records two tiers)
        tiers = mf.HierarchicalFilter._MAX_TIERS.get("gpu", 3) if a.get("device") else 3
        best, _ = gc.choose_chain(power, n, a["snr"], a["fd"], cost=_calibration.calibrate_costs(n, 64),
                                  window=win, max_tiers=tiers)
        if best is None:
            return dict(row, chain=None, error="no chain")
        chain = tuple(best["chain"])
    plan = gc.chain_thresholds(power, n, a["snr"], a["fd"], chain, window=win)
    row["chain"] = list(chain)
    if plan is None:
        return dict(row, error="no plan")
    thr = [float(x) for x in plan["thresholds"]]
    row["thresholds"] = thr
    row["model_lost"], row["model_detections"] = modelled(power, n, chain, thr, a["snr"], win,
                                                          a["check"] or max(1000000, 10 * a["inj"]))
    qm = row["model_lost"] / row["model_detections"]
    h = np.sqrt(power).astype(np.complex64)
    hc = np.conj(h)
    flat = mf.MatchedFilter(n, ndata=_B, ntemplates=1)
    flat.set_templates(hc[None, :])

    def engine(q15):
        e = _core.HMF(n, _B, 1, list(chain), 8)
        e.set_band_offsets(list(plan["offsets"]))
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
    gpu = None
    if a.get("device") and len(chain) <= mf.HierarchicalFilter._MAX_TIERS.get("gpu", 3):
        # The device's own hierarchical filter at the same chain and thresholds: on a GPU its
        # first tier is the fp16 coarse gate (its bound, or the raw maximum with
        # MF_COARSE_RAW=1), so its misses are that gate's dismissal against the flat filter.
        gpu = mf.HierarchicalFilter(n, _B, 1, snr=a["snr"], fd=a["fd"], chain=tuple(chain),
                                    device=a["device"])
        gpu.set_reference(power.astype(np.float32))
        gpu.set_templates(hc[None, :])
        gpu._thresholds = lambda required=True, _t=tuple(thr): _t
        engines["device"] = gpu
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
            if e is gpu:
                gpu.set_data(D)
                p = gpu.run(window=(ws, we), binsize=we - ws, threshold=a["snr"])[:, 0, 0]
            else:
                for d in range(_B):
                    e.set_data(d, D[d])
                e.run(0, _B, 0, 1, we - ws, a["snr"], ws, we, ei, ev, em, cnt, peaks[key])
                p = peaks[key][:, 0]
            got = (p["index"] >= 0) & (np.abs(p["value"]) >= a["snr"])
            miss[key] += int((hit & ~got).sum())
            both = hit & got
            mismatch[key] += int((np.abs(np.abs(p["value"][both]) - zf[both]) > 1e-3 * zf[both]).sum())
    row["detections"] = det
    row["model"] = qm / a["fd"]
    row["engines"] = {}
    for key in engines:
        # the engine's misses among both counts' misses, at its share of the detections: the
        # two-sample comparison of a binomial rate with one counted on the model's draws
        both = miss[key] + row["model_lost"]
        share = det / float(det + row["model_detections"])
        pv = binom_two_sided(miss[key], both, share) if both else 1.0
        row["engines"][key] = dict(misses=miss[key], ratio=miss[key] / max(det, 1) / a["fd"],
                                   to_model=miss[key] / max(det, 1) / qm if qm > 0 else float("nan"),
                                   p=pv, mismatches=mismatch[key])
    return row


def bank_spectra(power, n, nt, band, seed, chirp=3.0, group=4):
    """(nt, n) template signal spectra of output power `power`, in groups of `group`: the
    profile's signal delayed by a group's own multiple of group * n / nt samples, each member
    delayed further by up to a coarse lag of `band` either way, turned by a random phase, and
    given a quadratic phase of up to `chirp` radians at n / 2 either way. A delay alone a
    centroid's lag alignment undoes, a chirp it cannot, so a centroid of up to `group` members
    (gatechain.cluster_tier0_candidates) retains each differently. Every template keeps the
    reference's power: the gate model assumes the bank's band fractions are the reference's
    (a spectral tilt of k^0.15 put plans with and without centroids 3-20x off on power-law
    profiles), and a large chirp spreads the template in time, losing flat-filter SNR (28
    radians lost 4.5% of the detections at n=2048)."""
    rng = np.random.default_rng(seed)
    k = np.arange(n)
    x = (k / (n / 2.0)) ** 2
    amp = np.sqrt(power)
    out = np.empty((nt, n), np.complex64)
    for t in range(nt):
        delay = (t // group) * group * (n // nt) + rng.uniform(-1, 1) * (n // band)
        ph = -2 * np.pi * delay * k / n + chirp * rng.uniform(-1, 1) * x + rng.uniform(0, 2 * np.pi)
        out[t] = amp * np.exp(1j * ph)
    return out


def run_bank_case(job):
    """One --bank case: (profile, n, chain, args) -> its row, with an entry per filter and
    tier-0 setting (t0c: the model's centroids, flat0: none) and per statistic."""
    name, n, chain, a = job
    import matchedfilter as mf
    from matchedfilter import _hierarchical
    power = profile(name, n)
    win = None if a["window"] is None else tuple(a["window"])
    ws, we = (0, n) if win is None else win
    nt = int(a["bank"])
    row = dict(profile=name, n=n, snr=a["snr"], fd=a["fd"], window=[ws, we], chain=list(chain),
               bank=nt)
    if len(chain) < 1:
        return dict(row, error="empty chain")
    H = bank_spectra(power, n, nt, chain[0], [a["seed"], n, sum(map(ord, name))],
                     group=int(a.get("group") or 4))
    os.environ["MF_CHAIN_FORCE"] = "%d:%s" % (n, ",".join(map(str, chain)))
    os.environ["MF_AUTOTUNE"] = "0"
    flat = mf.MatchedFilter(n, ndata=_B, ntemplates=nt)
    flat.set_templates(np.conj(H))
    filters, plans = {}, {}
    devices = [("cpu", None)] + ([("device", a["device"])] if (a.get("device") and len(chain) >= 2) else [])
    for t0, on in (("t0c", True), ("flat0", False)):
        _hierarchical._TIER0_PAIR_CENTROID = on
        try:
            for dname, dev in devices:
                for stat in (("fp32", "q15") if dname == "cpu" and a["q15"] else ("fp32",)):
                    hf = mf.HierarchicalFilter(n, _B, nt, snr=a["snr"], fd=a["fd"], search_window=win,
                                               **({} if dev is None else dict(device=dev)))
                    try:
                        hf.set_reference(power.astype(np.float32))
                        hf.set_templates(np.conj(H))
                        r = hf._resolve()
                    except ValueError as e:            # no coarse pass for this profile
                        return dict(row, error=str(e).split(":")[0])
                    if dname == "cpu":
                        hf._execution_plan()
                        hf._set_q15(stat == "q15")
                        if bool(hf._q15) != (stat == "q15"):
                            continue                  # no Q15 screen for this chain here
                    if tuple(hf._chain) != tuple(chain):
                        return dict(row, error="MF_CHAIN_FORCE not honoured: %s" % (hf._chain,))
                    cl = hf._active_tier0_cluster()
                    cl1 = hf._active_tier1_cluster() if cl is not None else None
                    key = "%s %s %s" % (t0, "cpu" if dname == "cpu" else "dev", stat)
                    filters[key] = hf
                    plans[key] = dict(thresholds=[float(x) for x in r.thresholds],
                                      clusters=0 if cl is None else int(cl.specs.shape[0]),
                                      largest=0 if cl is None else int(np.diff(cl.offsets).max()),
                                      alpha=None if cl is None else float(cl.alpha),
                                      member_alphas=None if cl is None or cl.member_alphas is None
                                      else [float(x) for x in cl.member_alphas],
                                      member_alphas1=None if cl1 is None
                                      else [float(x) for x in cl1.member_alphas])
        finally:
            _hierarchical._TIER0_PAIR_CENTROID = True
    # each plan's modelled dismissal: templates injected uniformly, member t at its retention
    count = a["check"] or max(1000000, 10 * a["inj"])
    for key, pl in plans.items():
        al = pl["member_alphas"] or [pl["alpha"] or 1.0] * nt
        al1 = pl["member_alphas1"] or [1.0] * nt
        pairs = [(round(x, 4), round(y, 4)) for x, y in zip(al, al1)]
        lost = tot = 0
        for v, v1 in sorted(set(pairs)):
            w = sum(1 for q in pairs if q == (v, v1))
            l_, t_ = modelled(power, n, chain, pl["thresholds"], a["snr"], win,
                              max(100000, count * w // nt), alpha0=min(1.0, v),
                              alpha1=min(1.0, v1))
            lost += l_ * w / t_
            tot += w
        pl["model"] = lost / tot          # the plan's modelled dismissal, a share
    rng = np.random.default_rng([a["seed"], n, nt, sum(map(ord, name))])
    k = np.arange(n)
    det = 0
    miss = dict.fromkeys(filters, 0)
    mismatch = dict.fromkeys(filters, 0)
    rows_ = np.arange(_B)
    for _ in range(max(1, a["inj"] // _B)):
        which = rng.integers(0, nt, _B)
        lag = rng.uniform(ws, we, _B)
        D = (a["snr"] * H[which] * np.exp(2j * np.pi * (n - lag)[:, None] * k[None, :] / n)
             + (rng.standard_normal((_B, n)) + 1j * rng.standard_normal((_B, n)))).astype(np.complex64)
        flat.set_data(D)
        zf = np.abs(flat.run(binsize=we - ws, threshold=0.0, window=(ws, we))["value"][rows_, which, 0])
        hit = zf >= a["snr"]
        det += int(hit.sum())
        for key, hf in filters.items():
            hf.set_data(D)
            p = hf.run(window=(ws, we), binsize=we - ws, threshold=a["snr"])[rows_, which, 0]
            got = (p["index"] >= 0) & (np.abs(p["value"]) >= a["snr"])
            miss[key] += int((hit & ~got).sum())
            both = hit & got
            mismatch[key] += int((np.abs(np.abs(p["value"][both]) - zf[both]) > 1e-3 * zf[both]).sum())
    row["detections"] = det
    row["engines"] = {}
    for key, pl in plans.items():
        qm = pl["model"]
        mdet = count
        mlost = int(round(qm * mdet))
        both = miss[key] + mlost
        share = det / float(det + mdet)
        pv = binom_two_sided(miss[key], both, share) if both else 1.0
        row["engines"][key] = dict(pl, misses=miss[key], ratio=miss[key] / max(det, 1) / a["fd"],
                                   to_model=miss[key] / max(det, 1) / qm if qm > 0 else float("nan"),
                                   plan=qm / a["fd"], p=pv, mismatches=mismatch[key])
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
                    help="a Q15 or centroid chain dismissing less than its plan fails too")
    ap.add_argument("--check", type=int, default=0,
                    help="model detections a plan's dismissal is counted on (default max(1M, 10 x --inj))")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--device", default=None,
                    help="also run the device's hierarchical filter (gpu:0: the fp16 coarse gate)")
    ap.add_argument("--bank", type=int, default=0,
                    help="NT: audit banks of NT templates in groups of --group near-duplicates through "
                         "HierarchicalFilter, tier-0 pair centroids on and off (see above)")
    ap.add_argument("--group", type=int, default=4,
                    help="near-duplicates per group of a --bank (default 4). Production plans "
                         "cluster 6 to 8 templates: --bank 64 --group 8 audits that size (the model "
                         "forms clusters above four only when at least eight remain). A 64-template "
                         "case holds about 11 GB at n=2048: run one profile per process")
    ap.add_argument("--alpha", type=float, default=1e-3, help="family-wise level over the cases")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--json", default=None, help="write every row here")
    a = ap.parse_args(argv)
    names = a.profiles.split(",") if a.profiles else default_profiles()
    win = None if a.window is None else [int(x) for x in a.window.split(",")]
    opts = dict(snr=a.snr, fd=a.fd, inj=a.inj, window=win, q15=a.q15, seed=a.seed, check=a.check,
                device=a.device, bank=a.bank, group=a.group)
    # one job per (profile, n): its chains share the model's check draws
    jobs = [(nm, n, chains_for(a.chains, n), opts) for n in a.n for nm in names]
    t0 = time.time()
    if a.jobs > 1:
        with mp.get_context("spawn").Pool(a.jobs) as pool:
            rows = [r for part in pool.map(run_profile, jobs, chunksize=1) for r in part]
    else:
        rows = [r for j in jobs for r in run_profile(j)]
    tests = sum(len(r.get("engines", {})) for r in rows)
    level = a.alpha / max(tests, 1)
    bad = under = 0
    print("snr %.2f fd %g, %d injections a case, window %s; off the plan's modelled dismissal at "
          "p < %.1e (%g over %d tests)" % (a.snr, a.fd, a.inj, win or "whole block", level, a.alpha, tests))
    print("per case: misses / budget, and / the plan's modelled dismissal (plan: that over the budget)")
    for r in rows:
        head = "  n=%-5d %-18s %-20s" % (r["n"], r["profile"], ",".join(map(str, r["chain"] or ["?"])))
        if "error" in r:
            print(head, r["error"])
            continue
        for key, e in r["engines"].items():
            off = e["p"] < level
            # dismissing less than the plan: Q15 rounding, or a centroid's model (its draws
            # leave out the lag_pad lags the engine also searches); both cost work, not signals
            low = (off and e["to_model"] < 1 and (key.endswith("q15") or key.startswith("t0c"))
                   and not a.strict_q15)
            fail = (off and not low) or e["mismatches"]
            bad += bool(fail)
            under += bool(low)
            clus = ("  %d centroids, alpha %.2f (members %.2f-%.2f)" % (
                e["clusters"], e["alpha"], min(e["member_alphas"] or [e["alpha"]]),
                max(e["member_alphas"] or [e["alpha"]])) if e.get("clusters") else "")
            print("%s %-4s thr [%s] det %6d miss %5d  %.2fx budget  %.2fx plan (plan %.2fx)  p %.3g%s%s%s" % (
                head, key, ",".join("%.2f" % t for t in e.get("thresholds", r.get("thresholds"))),
                r["detections"], e["misses"], e["ratio"], e["to_model"], e.get("plan", r.get("model")),
                e["p"], clus, "  mismatches %d" % e["mismatches"] if e["mismatches"] else "",
                "  <-- OFF" if fail else "  (under the plan)" if low else ""), flush=True)
    keys = sorted({k for r in rows for k in r.get("engines", {})}, key=lambda k: (k.endswith("q15"), k))
    for key in keys:
        ok = [r for r in rows if key in r.get("engines", {})]
        if ok:
            m = sum(r["engines"][key]["misses"] for r in ok)
            d = sum(r["detections"] for r in ok)
            print("pooled %s: %d misses of %d detections over %d cases: %.3fx the budget "
                  "(+- %.3f binomial; plans scatter about fd / sqrt(47) each)"
                  % (key, m, d, len(ok), m / d / a.fd, math.sqrt(max(m, 1)) / d / a.fd))
    print("%d of %d off the plan or mismatched, %d Q15 or centroid chains under it (%.0f s)"
          % (bad, tests, under, time.time() - t0))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(rows, f, indent=1)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
