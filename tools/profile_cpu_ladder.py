#!/usr/bin/env python3
"""Profile the CPU search ladder at fixed chain, block size, bins, and thresholds.

Uses real bank taps and matching reference profiles with deterministic generated
input. Each run rebuilds the banks, excludes one warm segment, and measures the
remaining segments through public filtering calls. Q15 alternates off/on unless
--q15 pins it; results, including followups, must be bitwise identical across runs.
No result arrays are saved. Setup and validation are outside the steady timers.

Example (pin an otherwise idle physical core):
  PYTHONPATH=python taskset -c 4 python tools/profile_cpu_ladder.py \
      --bank BANK.hdf --profiles PROFILES.npz --output profile.json

For build comparisons run separate processes with each build's PYTHONPATH, in
alternating order, and compare output_sha256. The package is imported before
ladder.py so its source-tree import path cannot override the selected build.
The reported "forward" counter includes ingestion and bookkeeping. Clearing
rejected rows can move between that counter and Q15; compare their sum as well
as whole fine/segment time when evaluating changes to survivor processing.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

import numpy as np


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--profiles", type=Path, required=True,
                        help="matching per-top reference profiles from ladder_profiles.py")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target", default=None, help="CPU target, e.g. AVX3, AVX2, SSE4")
    parser.add_argument("--runs", type=int, default=4)
    parser.add_argument("--segments", type=int, default=4,
                        help="segments per run, including one excluded warm segment")
    parser.add_argument("--q15", type=int, choices=[0, 1], default=None,
                        help="pin Q15 off/on; otherwise alternate it across runs")
    cli = parser.parse_args()
    if cli.runs < 1 or cli.segments < 2:
        parser.error("--runs must be positive and --segments must be at least 2")

    os.environ.update(MF_AUTOTUNE="0", MF_CHAIN_FORCE="256,512,1024")
    os.environ.pop("MF_HMF_PROF", None)  # per-row instrumentation distorts this workload
    import matchedfilter as mf
    from matchedfilter import _core
    if cli.target is not None:
        want = os.environ.get("MF_ISA")
        if want and want.upper() != cli.target.upper():
            raise SystemExit("--target %s conflicts with MF_ISA=%s, which restricts the process "
                             "to its target: unset MF_ISA or drop --target" % (cli.target, want))
        mf.set_target(cli.target)
    spec = importlib.util.spec_from_file_location("ladder", Path(__file__).with_name("ladder.py"))
    ladder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ladder)

    args = SimpleNamespace(
        seg_samples=1 << 20, start_pad=120.0, end_pad=16.0,
        profiles=str(cli.profiles), asym_bin_width=0.03, asym_num_bins=1000,
        roofline=True, threshold=6.0, fd=1e-3, peak_window=1.0, fft_length=2048,
        pad=4096, segments=cli.segments, warmup=1, asym_threshold=6.0,
        depth=1, pregen=True, pipeline=False, overlap=False, no_batch=False,
        shared_input=False,
    )
    tops = ladder.load_tops(cli.bank, 1)
    original = mf.HierarchicalFilter._new_cpu_plan
    choice = False
    observed = []

    def new_plan(self, chain):
        plan = original(self, chain)
        self._q15 = bool(choice and plan.set_q15(True))
        if not choice:
            plan.set_q15(False)
        if choice and not self._q15:
            raise RuntimeError("Q15 unavailable for the selected CPU target")
        observed.append((self.n, self.ntemplates, tuple(chain), self._q15))
        return plan

    output = dict(
        package=mf.__file__, target=mf.backend(), core_sha256=sha256(_core.__file__),
        affinity=sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
        environment={k: v for k, v in os.environ.items() if k.startswith(("MF_", "LADDER_"))},
        bank=str(cli.bank), bank_sha256=sha256(cli.bank),
        profiles=str(cli.profiles), profiles_sha256=sha256(cli.profiles),
        args=vars(args), seed=1, runs=[],
    )
    expected = None
    mf.HierarchicalFilter._new_cpu_plan = new_plan
    try:
        for rep in range(cli.runs):
            choice = bool(cli.q15) if cli.q15 is not None else bool(rep % 2)
            observed.clear()
            start = time.perf_counter()
            report, results = ladder.run_device("cpu", tops, args, output["seed"])
            arrays = {str(k): (v.template_indices.copy(), v.sample_indices.copy(), v.snr.copy())
                      for k, v in results.items()}
            if expected is None:
                expected = arrays
            same = arrays.keys() == expected.keys() and all(
                all(np.array_equal(x, y) for x, y in zip(values, expected[key]))
                for key, values in arrays.items())
            if not same:
                raise AssertionError("Q15 changed ladder outputs")
            digest = hashlib.sha256()
            for key, values in sorted(arrays.items()):
                digest.update(key.encode())
                for value in values:
                    digest.update(value.tobytes())
            row = dict(rep=rep, q15=choice, total_wall=time.perf_counter() - start,
                       bitwise_equal=same, output_sha256=digest.hexdigest(),
                       observed_plans=observed.copy(), report=report)
            output["runs"].append(row)
            cli.output.write_text(json.dumps(output, indent=2, default=float) + "\n")
            print(f"run {rep}: Q15={choice}, steady={report['steady_s']}, "
                  f"output={row['output_sha256']}", flush=True)
    finally:
        mf.HierarchicalFilter._new_cpu_plan = original


if __name__ == "__main__":
    main()
