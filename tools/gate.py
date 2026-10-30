#!/usr/bin/env python
"""The merge gate: every check a change must pass before it goes to main, in one command.

    python tools/gate.py                       # every check this machine can run
    python tools/gate.py --quick               # one suite run, short loops
    python tools/gate.py --bank B.hdf --profiles P.npz   # include the ladder checks

Checks, in order (each reports ok / FAIL / skip, and the gate fails on any FAIL):

  suite        the full pytest suite, single-threaded, `--runs` times
  check        `tools/ladder.py --check cpu`: the device against the CPU reference,
               batched and with --pipeline; 0 peaks on one side only
  settled      the same check, pipelined, after priming a fresh MF_COST_FILE (`--prime`
               segments) so the trials have locked: the steady state a search runs in
  margin       `tools/gate_margin.py --loud`: a narrow gate that promises a bound has no false
               dismissals, one on its own statistic (the GPU fp16 tier) tracks the exact
               maximum to 2^-6, and a loud injection fails open
  fdr          `tools/fdr_audit.py`: every profile and chain at n = 2048 and 4096, over the
               whole block and a window, FP32 and Q15 tiers, dismisses its budget against
               the flat filter, two-sided (`--fdr-inj` injections a case)
  repro        tests/test_reproducible_choices.py, `--loops` times: processes sharing a
               cost file make the same choices
  followups    test_call_plan + test_followup_batch, `--loops` times (a past race)
  ci           tools/ci_status.py --schedules: main's latest run of every workflow, and
               every scheduled workflow's latest scheduled run, are green (a red schedule
               clears with a green ci/** proof of its fix); unknown (API unreachable,
               a run in progress) is reported as skip, never as ok

The ladder checks need a production-like bank and noise profiles, which are not in the
repository; they run when --bank/--profiles (or MF_GATE_BANK/MF_GATE_PROFILES) are given and
are skipped otherwise. A skipped check is reported as such, never as a pass. GPU checks run
on --device (default: the first usable GPU, else the CPU only).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THREADS = {k: "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                            "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")}


def _env(**extra):
    env = dict(os.environ, **THREADS)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(ROOT / "python"), env.get("PYTHONPATH")) if p)
    env.update({k: str(v) for k, v in extra.items()})
    return env


def _run(cmd, env=None, log=None):
    t0 = time.time()
    p = subprocess.run(cmd, cwd=ROOT, env=env or _env(), capture_output=True, text=True)
    if log is not None:
        Path(log).write_text(p.stdout + p.stderr)
    return p.returncode, p.stdout + p.stderr, time.time() - t0


def _usable_gpu():
    code = ("import sys; sys.path.insert(0, 'tests'); from conftest import usable_gpu; "
            "print(usable_gpu() or '')")
    rc, out, _ = _run([sys.executable, "-c", code])
    dev = out.strip().splitlines()[-1] if rc == 0 and out.strip() else ""
    return dev or None


class Gate:
    def __init__(self, logdir):
        self.results = []
        self.logdir = Path(logdir)
        self.logdir.mkdir(parents=True, exist_ok=True)

    def record(self, name, status, detail):
        self.results.append((name, status, detail))
        print("%-10s %-5s %s" % (name, status, detail), flush=True)

    @property
    def failed(self):
        return any(s == "FAIL" for _, s, _ in self.results)


def suite(g, runs):
    for i in range(runs):
        rc, out, dt = _run([sys.executable, "-m", "pytest", "-q", "tests", "-p", "no:cacheprovider"],
                           log=g.logdir / ("suite_%d.log" % i))
        tail = out.strip().splitlines()[-1] if out.strip() else ""
        failed = [l for l in out.splitlines() if l.startswith(("FAILED", "ERROR"))]
        g.record("suite", "ok" if rc == 0 else "FAIL",
                 "run %d/%d: %s (%.0fs)%s" % (i + 1, runs, tail, dt,
                                               "" if rc == 0 else "; " + "; ".join(failed[:5])))


def _ladder(args, device, extra, env=None, tag=""):
    out_json = Path(tempfile.mkstemp(suffix=".json", dir=args.logdir)[1])
    cmd = [sys.executable, "tools/ladder.py", "--bank", args.bank, "--profiles", args.profiles,
           "--device", device, "--tops", "1", "--pure", "--out", str(out_json)] + extra
    rc, out, dt = _run(cmd, env=env, log=Path(args.logdir) / ("ladder%s.log" % tag))
    try:
        report = json.loads(out_json.read_text())
    except (OSError, ValueError):
        report = None
    return rc, report, dt


def _check_ok(report):
    c = (report or {}).get("check")
    if not c:
        return False, "no check in report"
    ok = c.get("peaks_reference_only", 1) == 0 and c.get("peaks_device_only", 1) == 0
    return ok, "%d calls, one-sided %d/%d, max SNR diff %.1e" % (
        c.get("calls", 0), c.get("peaks_reference_only", -1), c.get("peaks_device_only", -1),
        c.get("max_snr_diff", float("nan")))


def check(g, args, device):
    for mode, extra in (("batched", []), ("pipeline", ["--pipeline"])):
        rc, report, dt = _ladder(args, device, ["--segments", "4", "--check", "cpu"] + extra,
                                 tag="_" + mode)
        ok, detail = _check_ok(report)
        g.record("check", "ok" if rc == 0 and ok else "FAIL", "%s: %s (%.0fs)" % (mode, detail, dt))


def settled(g, args, device):
    cost = Path(args.logdir) / "settled_costs.json"
    cost.unlink(missing_ok=True)
    env = _env(MF_COST_FILE=cost)
    rc, report, dt = _ladder(args, device, ["--segments", str(args.prime), "--pipeline"], env=env,
                             tag="_prime")
    if rc != 0:
        g.record("settled", "FAIL", "prime run failed (%.0fs)" % dt)
        return
    rc, report, dt = _ladder(args, device, ["--segments", "12", "--pipeline", "--check", "cpu"],
                             env=env, tag="_settled")
    ok, detail = _check_ok(report)
    g.record("settled", "ok" if rc == 0 and ok else "FAIL", "%s (%.0fs)" % (detail, dt))


def margin(g, args, device):
    gates = ["q15"] + (["gpu-c16"] if device else [])
    if args.cpu_g16:
        gates.append("cpu-g16")
    cmd = [sys.executable, "tools/gate_margin.py", "--gate"] + gates + ["--loud"]
    if device:
        cmd += ["--device", device]
    rc, out, dt = _run(cmd, log=g.logdir / "margin.log")
    last = out.strip().splitlines()[-1] if out.strip() else ""
    g.record("margin", "ok" if rc == 0 else "FAIL", "%s: %s (%.0fs)" % (" ".join(gates), last, dt))


def fdr(g, args, device=None):
    """The gate model's budget end to end, whole block and windowed, and on the device (its
    own hierarchical filter beside the CPU's: the GPU fp16 tier's dismissal, one process)."""
    jobs = str(max(1, min(8, (os.cpu_count() or 2) - 2)))
    parts, rc_all, t_all = [], 0, 0.0
    runs = [("block", []), ("window", ["--window", "192,1856"])]
    if device:
        runs.append(("device", ["--device", device, "--jobs", "1"]))
    for tag, extra in runs:
        cmd = [sys.executable, "tools/fdr_audit.py", "--n", "2048", "4096", "--q15", "--inj",
               str(args.fdr_inj), "--jobs", jobs] + extra
        rc, out, dt = _run(cmd, log=g.logdir / ("fdr_%s.log" % tag))
        last = out.strip().splitlines()[-1] if out.strip() else "no output"
        parts.append("%s: %s" % (tag, last))
        rc_all |= rc
        t_all += dt
    g.record("fdr", "ok" if rc_all == 0 else "FAIL", "; ".join(parts) + " (%.0fs)" % t_all)


def loop(g, name, tests, n):
    fails = 0
    for i in range(n):
        rc, _, _ = _run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"] + tests,
                        log=g.logdir / ("%s_%d.log" % (name, i)))
        fails += rc != 0
    g.record(name, "ok" if fails == 0 else "FAIL", "%d/%d runs failed" % (fails, n))


def ci(g):
    rc, out, dt = _run([sys.executable, "tools/ci_status.py", "--schedules"],
                       log=g.logdir / "ci.log")
    lines = [l for l in out.strip().splitlines() if l and not l.startswith("(")]
    bad = [" ".join(l.split()[:3]) for l in lines if l.startswith(("red", "unknown"))]
    status = {0: "ok", 1: "FAIL"}.get(rc, "skip")
    g.record("ci", status, ("%d runs and schedules green" % len(lines)) if rc == 0
             else "; ".join(bad[:6]) + " (tools/ci_status.py --schedules)")


def _machine_lock(path):
    """Hold an exclusive lock on path for this process's life, waiting while another gate
    holds it. Gates on one machine share its GPU and cores: two at once slowed each other
    2-3x and could fail the timing-sensitive steps (repro, followups), so every gate --
    whoever starts it -- runs alone."""
    import fcntl
    f = open(path, "a+")
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("gate: waiting for another gate on this machine (%s)" % path, flush=True)
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    return f


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device", default="auto",
                    help="GPU to gate (gpu:0, ...), 'cpu' for CPU only, or 'auto' (default)")
    ap.add_argument("--bank", default=os.environ.get("MF_GATE_BANK"))
    ap.add_argument("--profiles", default=os.environ.get("MF_GATE_PROFILES"))
    ap.add_argument("--runs", type=int, default=1, help="full-suite runs (default 1)")
    ap.add_argument("--loops", type=int, default=5, help="runs of each flake-prone test (default 5)")
    ap.add_argument("--prime", type=int, default=40,
                    help="segments that prime the settled check's fresh cost file (default 40)")
    ap.add_argument("--cpu-g16", action="store_true", help="also gate the CPU fp16 tier (ARM)")
    ap.add_argument("--fdr-inj", type=int, default=20000,
                    help="injections a case in the fdr check (default 20000; --quick 4000)")
    ap.add_argument("--quick", action="store_true", help="one suite run, 2 loops, no settled check")
    ap.add_argument("--only", nargs="+",
                    choices=["suite", "check", "settled", "margin", "fdr", "repro", "followups", "ci"])
    ap.add_argument("--logdir", default=None)
    ap.add_argument("--lock", default="/tmp/mf-gate-%d.lock" % os.getuid(),
                    help="per-machine lock file (fixed, not TMPDIR, so every session shares "
                         "it); a gate waits for any other holding it")
    args = ap.parse_args(argv)
    if args.quick:
        args.runs, args.loops, args.fdr_inj = 1, 2, 4000
    args.logdir = args.logdir or tempfile.mkdtemp(prefix="mf-gate-")
    lock = _machine_lock(args.lock)
    g = Gate(args.logdir)

    device = _usable_gpu() if args.device == "auto" else (None if args.device == "cpu" else args.device)
    rc, out, _ = _run(["git", "rev-parse", "--short", "HEAD"])
    print("gate: %s on %s, device %s, logs %s" % (out.strip(), os.uname().nodename, device or "cpu only",
                                                  args.logdir), flush=True)
    want = set(args.only or ["suite", "check", "settled", "margin", "fdr", "repro", "followups", "ci"])
    if args.quick and not args.only:
        want.discard("settled")

    if "suite" in want:
        suite(g, args.runs)
    ladder = bool(args.bank and args.profiles)
    for name, fn in (("check", check), ("settled", settled)):
        if name not in want:
            continue
        if not device:
            g.record(name, "skip", "no GPU to compare against the CPU")
        elif not ladder:
            g.record(name, "skip", "needs --bank/--profiles (MF_GATE_BANK/MF_GATE_PROFILES)")
        else:
            fn(g, args, device)
    if "margin" in want:
        margin(g, args, device)
    if "fdr" in want:
        fdr(g, args, device)
    if "repro" in want:
        loop(g, "repro", ["tests/test_reproducible_choices.py"], args.loops)
    if "followups" in want:
        loop(g, "followups", ["tests/test_call_plan.py", "tests/test_followup_batch.py"], args.loops)
    if "ci" in want:
        ci(g)

    print("gate: %s" % ("FAILED" if g.failed else "passed (%d skipped)"
                       % sum(s == "skip" for _, s, _ in g.results)), flush=True)
    return 1 if g.failed else 0


if __name__ == "__main__":
    sys.exit(main())
