#!/usr/bin/env python
"""Record every model decision a cold start makes, and how long the models took.

    tools/cold_decisions.py --out RECORD.json [--cost-file SEED.json] -- <ladder.py arguments>
    tools/cold_decisions.py --compare A.json B.json

Runs tools/ladder.py in this process with the gate and cost models wrapped: every call to
price_block_sizes, choose_chain and chain_thresholds (whose plans carry the direct refine's
half-width) is recorded with a
digest of its arguments and its full result, in call order, with its own time. Comparing
two records (an old and a new tree on the same inputs) shows whether a change to how the
models compute moved any decision.

Measured inputs must be fixed for the comparison to mean anything: run with MF_AUTOTUNE=0
(no trials) and a settled cost file (--cost-file is copied, so the seed is never written),
so calibration is read rather than timed. Everything recorded is then a pure function of the
bank, the reference spectra and the cost file.
"""
import argparse
import hashlib
import json
import os
import runpy
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
WRAPPED = ("price_block_sizes", "choose_chain", "chain_thresholds", "device_costs")


def _digest(x):
    """A stable, compact description of an argument or result."""
    if isinstance(x, np.ndarray):
        a = np.ascontiguousarray(x)
        return "nd%s:%s" % (a.shape, hashlib.sha1(a.tobytes()).hexdigest()[:16])
    if isinstance(x, (list, tuple)):
        return [_digest(v) for v in x]
    if isinstance(x, dict):
        return {str(k): _digest(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (np.floating, float)):
        return float(x).hex()
    if isinstance(x, (np.integer, int, bool, str)) or x is None:
        return x.item() if hasattr(x, "item") else x
    if hasattr(x, "__dict__"):                        # cost models: their fields
        return {"type": type(x).__name__, **{k: _digest(v) for k, v in sorted(vars(x).items())
                                             if not callable(v)}}
    return repr(x)


def record(out, cost_file, ladder_args):
    sys.path.insert(0, str(ROOT / "python"))
    os.environ.setdefault("MF_AUTOTUNE", "0")
    tmp = None
    if cost_file:
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        shutil.copy(cost_file, tmp)
        os.environ["MF_COST_FILE"] = tmp
    from matchedfilter import gatechain
    calls, depth = [], [0]

    def wrap(name, fn):
        def w(*a, **k):
            depth[0] += 1
            t = time.perf_counter()
            try:
                r = fn(*a, **k)
            finally:
                depth[0] -= 1
            dt = time.perf_counter() - t
            calls.append(dict(fn=name, depth=depth[0], seconds=dt,
                              args=_digest(list(a)), kwargs=_digest(k), result=_digest(r)))
            return r
        return w
    from matchedfilter import _calibration
    for name in WRAPPED:
        home = _calibration if hasattr(_calibration, name) else gatechain
        setattr(home, name, wrap(name, getattr(home, name)))
    t0 = time.perf_counter()
    sys.argv = ["ladder.py"] + ladder_args
    try:
        runpy.run_path(str(ROOT / "tools" / "ladder.py"), run_name="__main__")
    finally:
        total = time.perf_counter() - t0
        own = {}
        for c in calls:
            if c["depth"] == 0:
                own[c["fn"]] = own.get(c["fn"], 0.0) + c["seconds"]
        Path(out).write_text(json.dumps(dict(total_seconds=total, top_level_seconds=own,
                                             calls=calls), indent=1))
        if tmp:
            os.unlink(tmp)
        print("cold_decisions: %d calls, %.1f s in top-level model calls %s, %.1f s total -> %s"
              % (len(calls), sum(own.values()), {k: round(v, 2) for k, v in own.items()},
                 total, out), file=sys.stderr)


def compare(a, b):
    A, B = json.loads(Path(a).read_text()), json.loads(Path(b).read_text())

    def decisions(rec):
        # What each top-level call decided, keyed by what it was asked; repeated questions
        # must get the same answer within a record too.
        out = {}
        for c in rec["calls"]:
            if c["depth"] != 0:
                continue
            k = json.dumps([c["fn"], c["args"], c["kwargs"]], sort_keys=True)
            out.setdefault(k, set()).add(json.dumps(c["result"], sort_keys=True))
        return out
    da, db = decisions(A), decisions(B)
    only_a, only_b = set(da) - set(db), set(db) - set(da)
    differ = [k for k in set(da) & set(db) if da[k] != db[k]]
    for name, rec in (("A", A), ("B", B)):
        print("%s: %.1f s total, model calls %s" % (
            name, rec["total_seconds"], {k: round(v, 2) for k, v in rec["top_level_seconds"].items()}))
    print("questions: %d in A, %d in B; asked only in A %d, only in B %d; answered differently %d"
          % (len(da), len(db), len(only_a), len(only_b), len(differ)))
    for k in differ[:5]:
        print("  differs:", k[:200])
    return 0 if not differ else 1


def main():
    argv = sys.argv[1:]
    if argv[:1] == ["--compare"]:
        sys.exit(compare(argv[1], argv[2]))
    if "--" not in argv:
        sys.exit(__doc__)
    i = argv.index("--")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cost-file", default=None)
    args = ap.parse_args(argv[:i])
    record(args.out, args.cost_file, argv[i + 1:])


if __name__ == "__main__":
    main()
