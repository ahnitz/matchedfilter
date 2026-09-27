#!/usr/bin/env python3
"""Replay a captured FIR call using only matchedfilter transforms and filters.

Setup and validation are excluded from timing. Use separate processes with and
without --profile: native phase counters cover only part of run_series.
"""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("fixture", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--repeats", type=int, default=15)
    ap.add_argument("--profile", action="store_true")
    ap.add_argument("--band", type=int, default=1024)
    ap.add_argument("--taps", type=int, default=8)
    a = ap.parse_args()
    if a.repeats < 1:
        ap.error("--repeats must be positive")
    os.environ.pop("MF_HMF_PROF", None)
    if a.profile:
        os.environ["MF_HMF_PROF"] = "1"
    import matchedfilter as mf

    with np.load(a.fixture, allow_pickle=False) as z:
        data = {k: z[k] for k in z.files}
    n, nt = int(data["n_fft"]), int(data["nbatch"])
    threshold = float(data["threshold"])
    args = (data["series"], data["starts"], data["win_start"], data["win_end"])
    kwargs = dict(binsize=n, threshold=threshold, raw=True)
    plans = {
        "hier": mf.HierarchicalFilter(n, 1, nt, snr=threshold,
                                     fd=float(data["fd"]), band=a.band, taps=a.taps),
        "flat": mf.MatchedFilter(n, 1, nt),
    }
    plans["hier"].set_reference(data["reference"])
    if float(data["first_stage"]) > 0:
        plans["hier"].set_first_stage(float(data["first_stage"]))
    outputs = {}
    for name, plan in plans.items():
        plan.set_templates(data["templates"])
        for _ in range(2):
            idx, val = plan.run_series(*args, **kwargs)
        outputs[name] = (idx[:, :, 0].copy(), val[:, :, 0].copy())
    hi, hv = outputs["hier"]
    fi, fv = outputs["flat"]
    ci, cv = data["index"], data["value"]
    fired = hi >= 0
    validation = {
        "capture_peaks": int((ci >= 0).sum()),
        "hier_peaks": int(fired.sum()),
        "flat_peaks": int((fi >= 0).sum()),
        "capture_index_differences": int((hi != ci).sum()),
        "capture_values_match": bool(np.allclose(hv[fired], cv[fired], rtol=1e-5, atol=1e-5)),
        "flat_misses": int(((fi >= 0) & ~fired).sum()),
        "flat_fired_index_differences": int((hi[fired] != fi[fired]).sum()),
        "flat_fired_values_match": bool(np.allclose(hv[fired], fv[fired], rtol=1e-5, atol=1e-5)),
    }
    times = {k: [] for k in plans}
    cpu_times = {k: [] for k in plans}
    for r in range(a.repeats):
        for name in (list(plans) if r % 2 == 0 else list(reversed(plans))):
            c0 = time.thread_time_ns()
            t0 = time.perf_counter_ns()
            idx, val = plans[name].run_series(*args, **kwargs)
            times[name].append((time.perf_counter_ns() - t0) / 1e6)
            cpu_times[name].append((time.thread_time_ns() - c0) / 1e6)
            # Raw buffers are overwritten: check each sample outside timing.
            ei, ev = outputs[name]
            if not (np.array_equal(idx[:, :, 0], ei) and np.array_equal(val[:, :, 0], ev)):
                raise AssertionError("non-repeatable output: " + name)
    from matchedfilter import _core
    result = dict(fixture=str(a.fixture), fixture_sha256=hashlib.sha256(a.fixture.read_bytes()).hexdigest(),
                  package=mf.__file__, version=mf.__version__, backend=mf.backend(),
                  core_sha256=hashlib.sha256(Path(_core.__file__).read_bytes()).hexdigest(),
                  environment={k: v for k, v in os.environ.items() if k.startswith("MF_")},
                  affinity=sorted(os.sched_getaffinity(0)), profile=a.profile,
                  n=n, templates=nt, blocks=len(data["starts"]),
                  config=list(plans["hier"].config), threshold=threshold,
                  fd=float(data["fd"]), stats=list(plans["hier"].stats),
                  validation=validation, samples_ms=times, thread_cpu_ms=cpu_times,
                  median_ms={k: float(np.median(v)) for k, v in times.items()})
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if (validation["capture_index_differences"] or not validation["capture_values_match"]
            or validation["flat_fired_index_differences"] or not validation["flat_fired_values_match"]):
        raise SystemExit("validation failed; result saved")


if __name__ == "__main__":
    main()
