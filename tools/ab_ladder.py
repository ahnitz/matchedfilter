#!/usr/bin/env python
"""Paired ladder: two source trees on the same data, the same settled measured choices, in
alternating order.

    python tools/ab_ladder.py --base ../tree-a --new ../tree-b -- --bank B.hdf --profiles P.npz \\
        --device gpu:0 --tops 1 --pure --segments 8

Everything after `--` goes to tools/ladder.py. The method:

  * One cost file is settled first: `--settle` runs of each mode (batched and --pipeline) on
    the base tree, so the measured choices and trials have locked. A seed taken after a
    single run makes every later run re-explore its trials, which measures the exploration,
    not the code (it once read 2.3e6 templates in real time where the settled value was 1.4e8).
  * Every run then starts from a copy of that seed, so both trees run the same choices and
    neither run's measurements leak into the next.
  * --seed-per-tree settles one seed per tree instead, each on its own tree: for a change to
    what the choices themselves are (pricing, candidates), which a shared seed would hide.
  * Rounds alternate the order (base first, then new first), after `--warmup` unrecorded
    runs of each tree.

Each line reports the throughput (templates in real time), the host CPU time and, with
--timing, the fine stage's device time, for both modes; the summary gives each tree's range over the rounds.
Single-threaded (OMP_NUM_THREADS=1 and the BLAS variables) as every benchmark here.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

PATTERNS = {"tp": r"^throughput: ([0-9.e+]+)", "fine_dev": r"fine: device ([0-9.]+)s",
            "host": r"host: cpu ([0-9.]+)s"}


def run(tree, ladder_args, cost, extra, python, timing=False):
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               VECLIB_MAXIMUM_THREADS="1", PYTHONPATH=os.path.join(tree, "python"),
               MF_COST_FILE=cost)
    p = subprocess.run([python, os.path.join(tree, "tools", "ladder.py")] + ladder_args + extra
                       + (["--timing"] if timing and "--timing" not in ladder_args else []),
                       cwd=tree, env=env, capture_output=True, text=True)
    out = {}
    for k, pat in PATTERNS.items():
        m = re.search(pat, p.stdout, re.M)
        out[k] = float(m.group(1)) if m else None
    if p.returncode != 0 or out["tp"] is None:
        sys.exit("ladder failed in %s (rc %d):\n%s" % (tree, p.returncode, p.stderr[-2000:]))
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--" not in argv:
        sys.exit("usage: ab_ladder.py [options] -- <ladder.py arguments>")
    k = argv.index("--")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--warmup", type=int, default=1)
    ap.add_argument("--settle", type=int, default=3,
                    help="runs of each mode that settle the shared cost file (default 3)")
    ap.add_argument("--seed-cost", default=None,
                    help="an already settled cost file to start from instead of settling")
    ap.add_argument("--seed-per-tree", action="store_true",
                    help="settle a cost file per tree on that tree (a change to the choices)")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--timing", action="store_true",
                    help="device timers on (fine-stage device time per run). They change what "
                         "a host-bound backend is limited by (on an M2 they hid a 14%% host "
                         "saving), so throughput is compared without them by default")
    args = ap.parse_args(argv[:k])
    ladder = argv[k + 1:]
    trees = {"base": os.path.abspath(args.base), "new": os.path.abspath(args.new)}
    work = tempfile.mkdtemp(prefix="ab-ladder-")
    seeds = {name: os.path.join(work, "seed_%s.json" % name) for name in trees}
    if args.seed_cost:
        for name in trees:
            shutil.copy(args.seed_cost, seeds[name])
    else:
        for name in (trees if args.seed_per_tree else ["base"]):
            for _ in range(args.settle):
                for extra in ([], ["--pipeline"]):
                    run(trees[name], ladder, seeds[name], extra, args.python)
        if not args.seed_per_tree:
            shutil.copy(seeds["base"], seeds["new"])

    def one(name, extra):
        cost = os.path.join(work, "%s.json" % name)
        shutil.copy(seeds[name], cost)
        return run(trees[name], ladder, cost, extra, args.python, args.timing)

    for _ in range(args.warmup):
        for name in trees:
            one(name, [])
    got = {(n, m): [] for n in trees for m in ("batched", "pipeline")}
    for r in range(args.rounds):
        order = ["base", "new"] if r % 2 == 0 else ["new", "base"]
        for name in order:
            line = []
            for mode, extra in (("batched", []), ("pipeline", ["--pipeline"])):
                o = one(name, extra)
                got[name, mode].append(o)
                line.append("%s %.4g (fine dev %s, host %s)" % (mode, o["tp"], o["fine_dev"], o["host"]))
            print("round %d %-4s | %s" % (r + 1, name, " | ".join(line)), flush=True)
    print("summary (throughput range over %d rounds):" % args.rounds)
    for mode in ("batched", "pipeline"):
        b = [o["tp"] for o in got["base", mode]]
        n = [o["tp"] for o in got["new", mode]]
        print("  %-8s base %.4g-%.4g  new %.4g-%.4g  median ratio new/base %.3f"
              % (mode, min(b), max(b), min(n), max(n),
                 sorted(n)[len(n) // 2] / sorted(b)[len(b) // 2]))
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
