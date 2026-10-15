#!/usr/bin/env python3
"""Compare immutable builds on Q15 template tails and grouped hierarchical series.

Each build path contains its own matchedfilter package and native extension. Run on
one idle physical core; workers inherit the same affinity and execute alternately:

  taskset -c 0 python tools/bench_q15_tails.py baseline/python candidate/python \
      --output tails.json --isas AVX3 AVX2 SSE4

The screen case times the production call without diagnostic statistics, then checks
both pass masks and statistics outside the timer. The series case uses N=2048, chain
256/512/1024, Q15 enabled, fixed thresholds, and 32 overlapping complex input blocks.
One injected tail-template peak makes output comparison nontrivial. Its group argument
controls native series batching. Peak fields and counts must match
exactly between builds. --verify-only executes correctness checks without timing.

Defaults include cap401 tails and aligned/nearly full controls. Timing is diagnostic;
use profile_cpu_ladder.py with the real bank and H1 profiles for the acceptance result.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time


def worker():
    import numpy as np
    import matchedfilter as mf
    from matchedfilter import _core

    backend = mf.backend()  # Apply MF_ISA before creating any native plans.
    identity = dict(package=mf.__file__, backend=backend, core=str(_core.__file__),
                    core_sha256=hashlib.sha256(Path(_core.__file__).read_bytes()).hexdigest(),
                    affinity=sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
                    python=sys.version, numpy=np.__version__)
    cached_key, cached = None, None

    def setup(cfg):
        nt, group = cfg["templates"], cfg["group"]
        rng = np.random.default_rng(8137 + nt)

        def noise(shape):
            return (rng.standard_normal(shape) + 1j * rng.standard_normal(shape)).astype(np.complex64)

        if cfg["kind"] == "screen":
            band = 256
            data, templates = noise((group, band)), noise((nt, band))
            templates /= np.linalg.norm(templates, axis=1, keepdims=True)
            plan = _core.MF(band, group, nt)
            lanes = plan.q15_lanes()
            if not lanes:
                raise RuntimeError(f"Q15 unsupported on {backend}")
            plan.set_data_batch(0, data)
            plan.set_template_batch(0, templates)
            passed = np.empty(group * nt, np.uint8)
            checked = np.empty_like(passed)
            stat = np.empty(group * nt, np.float32)
            empty_stat = np.empty(0, np.float32)

            def run():
                return plan.q15_screen(0, group, 0, nt, 4.1, 24, 232, passed, empty_stat)

            def digest():
                count = plan.q15_screen(0, group, 0, nt, 4.1, 24, 232, checked, stat)
                if count != int(passed.sum()) or not np.array_equal(checked, passed):
                    raise AssertionError("Q15 diagnostics changed the pass mask")
                return hashlib.sha256(passed.tobytes() + stat.tobytes()).hexdigest()

            run()
            detail = dict(pairs=group * nt, q15_lanes=lanes, template_tail=nt % lanes,
                          q15_passed=int(passed.sum()), threshold=4.1, window=[24, 232],
                          diagnostic_statistics_timed=False)
            return run, digest, detail

        n, blocks = 2048, cfg["blocks"]
        starts = np.arange(blocks, dtype=np.uintp) * 1664
        source = noise(int(starts[-1]) + n)
        templates = noise((nt, n))
        templates *= np.float32(np.sqrt(n)) / np.linalg.norm(templates, axis=1, keepdims=True)
        source[:n] += (24. * np.roll(np.fft.ifft(templates[-1]), 1024)).astype(np.complex64)
        lo = np.full(blocks, 192, np.uintp)
        hi = np.full(blocks, 1856, np.uintp)
        chain, thresholds = [256, 512, 1024], [4.1, 4.76, 5.48]
        plan = _core.HMF(n, 1, nt, chain, group, n)
        if not plan.set_q15(True):
            raise RuntimeError(f"Q15 unsupported on {backend}")
        if plan.series_group() != group:
            raise RuntimeError(f"native series group {plan.series_group()} != requested {group}")
        plan.set_reference(np.ones(n, np.float32))
        plan.set_template_batch(0, templates)
        plan.set_thresholds(thresholds)
        shape = (blocks, nt, 1)
        index = np.zeros(shape, np.int64)
        value = np.zeros(shape, np.complex64)
        magnitude = np.zeros(shape, np.float32)
        counts = np.zeros((blocks, nt), np.int32)

        def run():
            return plan.run_series(source, starts, lo, hi, 0, nt, n, 0.,
                                   index, value, magnitude, counts)

        def digest():
            return hashlib.sha256(index.tobytes() + value.tobytes()
                                  + magnitude.tobytes() + counts.tobytes()).hexdigest()

        run()
        if not counts[0, -1]:
            raise AssertionError("injected tail-template peak was not retained")
        detail = dict(pairs=blocks * nt, blocks=blocks, actual_group=plan.series_group(),
                      q15_passed=plan.q15_stats()[1], tier_passed=[x[1] for x in plan.tier_stats()],
                      peaks=int(counts.sum()), chain=chain, thresholds=thresholds,
                      window=[192, 1856], hop=1664, injected_template=nt - 1, injected_snr=24.)
        return run, digest, detail

    for line in sys.stdin:
        request = json.loads(line)
        if request.get("identity"):
            print(json.dumps(identity), flush=True)
            continue
        cfg, reps = request["case"], request["reps"]
        key = json.dumps(cfg, sort_keys=True)
        if key != cached_key:
            cached = setup(cfg)
            cached_key = key
        run, digest, detail = cached
        if run() < 0:
            raise RuntimeError(f"native warm/check call failed: {cfg}")
        seconds = None
        if reps:
            started = time.perf_counter()
            for _ in range(reps):
                if run() < 0:
                    raise RuntimeError(f"native timed call failed: {cfg}")
            seconds = (time.perf_counter() - started) / reps
        print(json.dumps(dict(seconds=seconds, digest=digest(), detail=detail)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--isas", nargs="+", default=["AVX3", "AVX2", "SSE4"])
    parser.add_argument("--templates", nargs="+", type=int, default=[80, 103, 131, 140, 162, 193, 128, 254])
    parser.add_argument("--groups", nargs="+", type=int, default=[1, 2, 3, 4, 32])
    parser.add_argument("--kinds", nargs="+", choices=["screen", "series"], default=["screen", "series"])
    parser.add_argument("--blocks", type=int, default=32)
    parser.add_argument("--rounds", type=int, default=7)
    parser.add_argument("--sample-ms", type=float, default=20.)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if any(x < 1 for x in args.templates + args.groups) or args.blocks < 1 or args.rounds < 1:
        parser.error("templates, groups, blocks, and rounds must be positive")
    if any(x > args.blocks for x in args.groups) and "series" in args.kinds:
        parser.error("series groups must not exceed --blocks")
    if not math.isfinite(args.sample_ms) or args.sample_ms <= 0:
        parser.error("sample-ms must be finite and positive")
    for root in (args.baseline, args.candidate):
        if not (root / "matchedfilter" / "__init__.py").is_file():
            parser.error(f"build path must contain the matchedfilter package: {root}")
    if not args.output.resolve().parent.is_dir():
        parser.error("output parent directory must exist")
    worker_path = str(Path(__file__).resolve())
    cases = [dict(kind=kind, templates=nt, group=group, blocks=args.blocks)
             for kind in args.kinds for nt in args.templates for group in args.groups]
    report = dict(schema_version=1, baseline=str(args.baseline.resolve()),
                  candidate=str(args.candidate.resolve()), verify_only=args.verify_only,
                  rounds=args.rounds, sample_ms=args.sample_ms,
                  case_seed="8137 + templates", workers={}, results=[])
    for isa in args.isas:
        workers = []
        try:
            for root in (args.baseline, args.candidate):
                env = dict(os.environ, PYTHONPATH=str(root.resolve()), MF_ISA=isa,
                           MF_AUTOTUNE="0", MF_GATE16="0", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
                for key in ("MF_HMF_PROF", "MF_HMF_TRACE", "MF_HMF_DUMP"):
                    env.pop(key, None)
                workers.append(subprocess.Popen([sys.executable, worker_path, "--worker"], env=env,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True))

            def ask(i, request):
                workers[i].stdin.write(json.dumps(request) + "\n")
                workers[i].stdin.flush()
                line = workers[i].stdout.readline()
                if not line:
                    raise RuntimeError(f"{isa} worker {i} exited: {request}")
                return json.loads(line)

            identities = [ask(i, {"identity": True}) for i in (0, 1)]
            if any(x["backend"] != isa for x in identities):
                raise RuntimeError(f"workers did not select {isa}: {identities}")
            report["workers"][isa] = identities
            for cfg in cases:
                checks = [ask(i, dict(case=cfg, reps=0)) for i in (0, 1)]
                if checks[0]["digest"] != checks[1]["digest"] or checks[0]["detail"] != checks[1]["detail"]:
                    raise AssertionError(f"Output or survivor-count mismatch: {isa} {cfg}: {checks}")
                row = dict(cfg, isa=isa, digest=checks[0]["digest"], detail=checks[0]["detail"])
                if not args.verify_only:
                    pilots = [ask(i, dict(case=cfg, reps=2)) for i in (0, 1)]
                    seconds = max(x["seconds"] for x in pilots)
                    reps = max(3, min(10000, math.ceil(args.sample_ms / 1000 / seconds)))
                    samples = [[], []]
                    digests = {x["digest"] for x in pilots}
                    for round_ in range(args.rounds):
                        for i in ((0, 1) if round_ % 2 == 0 else (1, 0)):
                            got = ask(i, dict(case=cfg, reps=reps))
                            samples[i].append(got["seconds"])
                            digests.add(got["digest"])
                    if digests != {row["digest"]}:
                        raise AssertionError(f"Output changed during timing: {isa} {cfg}")
                    row.update(repetitions=reps, samples=samples,
                               baseline_us=statistics.median(samples[0]) * 1e6,
                               candidate_us=statistics.median(samples[1]) * 1e6,
                               speedup=statistics.median([x / y for x, y in zip(*samples)]))
                report["results"].append(row)
                args.output.write_text(json.dumps(report, indent=2) + "\n")
                print(json.dumps(row), flush=True)
        finally:
            for proc in workers:
                proc.stdin.close()
                proc.wait()


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        worker()
    else:
        main()
