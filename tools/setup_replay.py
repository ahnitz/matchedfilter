#!/usr/bin/env python
"""A job's matchedfilter setup, replayed from a capture (tools/setup_capture.py).

    python tools/setup_replay.py CAPDIR [--refs N] [--decisions OUT.json] [--profile OUT.prof]

Every captured bank, in job order, is built, given its reference and run twice on its
reference's captured series; the first call's time beyond the second is setup done inside
the call. Prints the setup (construction, set_reference and that excess) in wall and thread
CPU seconds, per reference, and a digest of every bank's decisions -- block sizes, chains,
Q15 and tier thresholds -- so a change can be checked to decide alike
(tools/setup_decisions_diff.py compares two --decisions files). Decisions depend on the
timed calibration; set MF_COST_FILE and MF_AUTOTUNE=0 to compare trees on the same costs.
"""
import argparse
import cProfile
import glob
import hashlib
import json
import pickle
import time

import matchedfilter.time_domain as td


def load(capdir, nrefs=None):
    """(references, call files by reference, banks) of a capture, banks limited to nrefs."""
    refs = {int(f[-7:-4]): pickle.load(open(f, "rb")) for f in sorted(glob.glob(capdir + "/ref*.pkl"))}
    calls = {int(f[-7:-4]): f for f in sorted(glob.glob(capdir + "/call_ref*.pkl"))}
    banks = [pickle.load(open(f, "rb")) for f in sorted(glob.glob(capdir + "/bank*.pkl"))]
    banks = [b for b in banks if (nrefs is None or b[0] < nrefs) and b[0] in calls]
    return refs, calls, banks


def decisions(bank):
    """A bank's block sizes and, per hierarchical plan, (chain, Q15 on, thresholds)."""
    groups = getattr(bank, "_groups", None) or []
    plans = [g.plan for g in groups if getattr(g, "is_hier", False) and getattr(g, "plan", None) is not None]
    return [sorted({g.n for g in groups}) or None,
            [(list(p._mf.chain()), int(p._mf.q15_stats()[0]), [round(float(x), 5) for x in p._mf.thresholds()])
             for p in plans if getattr(p, "_mf", None) is not None]]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("capdir")
    ap.add_argument("--refs", type=int, default=None, help="replay only the first N references")
    ap.add_argument("--decisions", help="write every bank's decisions here (JSON)")
    ap.add_argument("--profile", help="write a cProfile of the replay here")
    a = ap.parse_args()
    refs, calls, banks = load(a.capdir, a.refs)
    prof = cProfile.Profile() if a.profile else None
    per, dec, cache, wall, cpu = {}, [], {}, 0.0, 0.0
    t_all = time.perf_counter()
    if prof:
        prof.enable()
    for ri, args, kw in banks:
        if ri not in cache:
            cache = {ri: pickle.load(open(calls[ri], "rb"))}
        ser, ca, ck = cache[ri]
        kw = dict(kw); kw["device"] = None
        t0, c0 = time.perf_counter(), time.thread_time()
        b = td.TimeDomainFilterBank(*args, **kw)
        b.set_reference(*refs[ri][0], **refs[ri][1])
        try:
            b.filter_series(ser, *ca, **ck)
            t1, c1 = time.perf_counter(), time.thread_time()
            b.filter_series(ser, *ca, **ck)        # the steady call
            t2, c2 = time.perf_counter(), time.thread_time()
        except Exception as e:                  # a bank the build cannot run is reported, not fatal
            print("call failed for a bank on reference %d: %s" % (ri, e))
            continue
        w, c = (t1 - t0) - (t2 - t1), (c1 - c0) - (c2 - c1)
        per[ri] = per.get(ri, 0.0) + w
        wall += w; cpu += c
        dec.append([ri] + decisions(b))
    if prof:
        prof.disable(); prof.dump_stats(a.profile)
    print("refs %d banks %d: setup (beyond steady calls) %.1f s wall, %.1f s CPU; replay %.1f s; per ref %s"
          % (len(per), len(dec), wall, cpu, time.perf_counter() - t_all, " ".join("%.1f" % per[r] for r in sorted(per))))
    print("DIGEST", hashlib.md5(json.dumps(dec).encode()).hexdigest()[:12])
    if a.decisions:
        json.dump(dec, open(a.decisions, "w"))


if __name__ == "__main__":
    main()
