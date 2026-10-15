#!/usr/bin/env python3
"""Alternate immutable native builds on pooled batches and full two-tier HMF calls.

Each build directory must contain its own matchedfilter package and native extension.
For example: python tools/bench_survivor_batches.py baseline/python candidate/python
    --output survivors.json --isas AVX3 AVX2 SSE4
On Linux, optionally prefix the command with taskset -c <idle physical CPU>.

The workers alternate on the same CPU affinity. No library is compiled; correctness
compares selected peak fields and counts, excluding ABI padding. Whole hierarchical
calls use n=4096, two coarse tiers and measured survivor densities. This isolates
survivor processing; bench_cpu_broadcast.py complements it with dense public calls.
"""
import argparse
import ctypes as C
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import struct
import subprocess
import sys
import time


class Peak(C.Structure):
    _fields_ = [("index", C.c_long), ("re", C.c_float), ("im", C.c_float),
                ("magnitude", C.c_float)]


def worker():
    import numpy as np
    import matchedfilter as mf
    from matchedfilter import _core
    lib = C.CDLL(_core.__file__)
    V, I, Z, F = C.c_void_p, C.c_int, C.c_size_t, C.c_float
    signatures = {
        "ap_mf_create_pairbatch": ([Z, I, I], V),
        "ap_mf_destroy": ([V], None),
        "ap_mf_set_template": ([V, I, V], I),
        "ap_mf_set_data": ([V, I, V], I),
        "ap_mf_run_pairs_pooled": ([V, I, V, V, I, I, Z, F, V, V, Z, Z, I], I),
        "ap_lane_width": ([], I),
    }
    for name, (args, result) in signatures.items():
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = args, result
    plans = {}

    def setup(cfg):
        n, nt, nd = cfg["n"], cfg["nt"], 8
        rng = np.random.default_rng(n + nt)
        noise = lambda shape: (rng.normal(size=shape) + 1j*rng.normal(size=shape)).astype(np.complex64)
        if cfg["kind"] == "pooled":
            width = lib.ap_lane_width()
            mode = cfg["mode"]
            t0, d0 = (3 if mode == "same_sparse" else 0), 1
            data, templates = noise((nd + d0, n)), noise((nt + t0, n))
            p = lib.ap_mf_create_pairbatch(n, nd + d0, nt + t0)
            if not p:
                raise RuntimeError(f"No pair-batched plan: {cfg}")
            for t, row in enumerate(templates):
                assert lib.ap_mf_set_template(p, t, row.ctypes.data) == 0
            for d, row in enumerate(data):
                assert lib.ap_mf_set_data(p, d, row.ctypes.data) == 0
            if mode == "dense":
                ts = np.tile(np.arange(nt, dtype=np.int32), nd)
                ds = np.repeat(np.arange(nd, dtype=np.int32), nt)
            elif mode == "same_sparse":
                selection = np.sort(rng.choice(nt, max(1, nt // 4), replace=False)).astype(np.int32)
                ts = np.tile(selection, nd)
                ds = np.repeat(np.arange(nd, dtype=np.int32), len(selection))
            elif mode == "mixed":
                ts = rng.integers(0, nt, max(nt, 2 * width + 3), dtype=np.int32)
                ds = np.arange(len(ts), dtype=np.int32) % nd
            else:
                count = min(nt, width + 3)
                ts = np.arange(nt - count, nt, dtype=np.int32)
                ds = np.full(len(ts), 3, dtype=np.int32)
            lo, hi, binsize = (3, n - 5, 17) if mode == "tail" else (0, n, n)
            nb = (hi - lo + binsize - 1) // binsize
            out = (Peak * (nd * nt * nb))()
            counts = np.zeros(nd * nt, dtype=np.int32)
            args = (p, d0, ds.ctypes.data, ts.ctypes.data, len(ts), t0, binsize,
                    0., out, counts.ctypes.data, lo, hi, nt)
            def run():
                return lib.ap_mf_run_pairs_pooled(*args)
            def digest():
                h = hashlib.sha256()
                for d, t in zip(ds, ts):
                    row = int(d) * nt + int(t)
                    h.update(struct.pack("<i", int(counts[row])))
                    for b in range(nb):
                        pk = out[row * nb + b]
                        h.update(struct.pack("<qfff", pk.index, pk.re, pk.im, pk.magnitude))
                return h.hexdigest()
            # Hold the index lists/inputs referenced by native pointers throughout timing.
            hold = (p, data, templates, ts, ds, out, counts)
            return run, digest, {"pairs": len(ts), "width": width}, hold

        data = noise((nd, n))
        templates = noise((nt, n)) / np.float32(np.sqrt(2 * n))
        chain = cfg["chain"]
        maxima = []
        for band in chain:
            products = (data[:, None, :band].astype(np.complex128)
                        * templates[None, :, :band].conj().astype(np.complex128)
                        * np.sqrt(n / band))
            maxima.append(np.max(np.abs(np.fft.ifft(products, axis=-1) * band), axis=-1))
        thr0 = float(np.quantile(maxima[0], 1 - cfg["survival"]))
        admitted = maxima[0] >= thr0
        # Ten percent of tier-0 survivors get a full n-point refine.
        thr1 = float(np.quantile(maxima[1][admitted], .9))
        p = _core.HMF(n, nd, nt, chain, nd, n)
        p.set_reference(np.ones(n, dtype=np.float32))
        p.set_template_batch(0, templates)
        p.set_data_batch(0, data)
        p.set_thresholds([thr0, thr1])
        idx = np.zeros((nd, nt, 1), dtype=np.int64)
        val = np.zeros((nd, nt, 1), dtype=np.complex64)
        mag = np.zeros((nd, nt, 1), dtype=np.float32)
        counts = np.zeros((nd, nt), dtype=np.int32)
        def run():
            return p.run(0, nd, 0, nt, n, 0., 0, n, idx, val, mag, counts)
        def digest():
            return hashlib.sha256(idx.tobytes() + val.tobytes() + mag.tobytes() + counts.tobytes()).hexdigest()
        run()
        detail = {"thresholds": [thr0, thr1],
                  "passed": [row[1] for row in p.tier_stats()], "pairs": nd * nt}
        return run, digest, detail, (p, data, templates)

    for line in sys.stdin:
        cfg, reps = json.loads(line)
        key = json.dumps(cfg, sort_keys=True)
        if key not in plans:
            plans[key] = setup(cfg)
        run, digest, detail, hold = plans[key]
        run()
        started = time.perf_counter()
        for _ in range(reps):
            if run() < 0:
                raise RuntimeError("native run failed")
        seconds = (time.perf_counter() - started) / reps
        print(json.dumps({"seconds": seconds, "digest": digest(), "detail": detail,
                          "backend": mf.backend()}), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline")
    p.add_argument("candidate")
    p.add_argument("--output", required=True)
    p.add_argument("--isas", nargs="+", default=["AVX3", "AVX2", "SSE4"])
    p.add_argument("--sizes", nargs="+", type=int, default=[128, 256, 512])
    p.add_argument("--templates", nargs="+", type=int, default=[37, 128, 512])
    p.add_argument("--kinds", nargs="+", choices=["pooled", "hier"], default=["pooled", "hier"])
    p.add_argument("--modes", nargs="+", choices=["same_sparse", "dense", "mixed", "tail"],
                   default=["same_sparse", "dense", "mixed", "tail"])
    p.add_argument("--survivals", nargs="+", type=float, default=[.05, .25])
    p.add_argument("--rounds", type=int, default=7)
    p.add_argument("--sample-ms", type=float, default=15.)
    a = p.parse_args()
    if a.rounds < 1 or not math.isfinite(a.sample_ms) or a.sample_ms <= 0:
        p.error("rounds and sample-ms must be positive")
    if any(n < 64 or n > 2048 or n & (n - 1) for n in a.sizes):
        p.error("sizes must be powers of two from 64 through 2048")
    if any(nt < 1 for nt in a.templates):
        p.error("templates must be positive")
    if any(not 0 < s < 1 for s in a.survivals):
        p.error("survivals must lie strictly between zero and one")
    for root in (a.baseline, a.candidate):
        if not (Path(root) / "matchedfilter" / "__init__.py").is_file():
            p.error(f"build directory must contain the matchedfilter package: {root}")
    output = Path(a.output).resolve()
    if not output.parent.is_dir():
        p.error(f"output directory does not exist: {output.parent}")
    worker_path = str(Path(__file__).resolve())
    cases = []
    if "pooled" in a.kinds:
        cases += [dict(kind="pooled", n=n, nt=nt, mode=mode)
                  for n in a.sizes for nt in a.templates for mode in a.modes]
    if "hier" in a.kinds:
        cases += [dict(kind="hier", n=4096, nt=nt, chain=chain, survival=survival)
                  for nt in a.templates for chain in ([128, 256], [256, 512])
                  for survival in a.survivals]
    results = []
    for isa in a.isas:
        workers = []
        try:
            for root in (a.baseline, a.candidate):
                env = dict(os.environ, PYTHONPATH=str(Path(root).resolve()), MF_ISA=isa,
                           MF_AUTOTUNE="0", MF_GATE16="0", OPENBLAS_NUM_THREADS="1")
                workers.append(subprocess.Popen([sys.executable, worker_path, "--worker"], env=env,
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True))
            def ask(i, cfg, reps):
                workers[i].stdin.write(json.dumps([cfg, reps]) + "\n")
                workers[i].stdin.flush()
                line = workers[i].stdout.readline()
                if not line:
                    raise RuntimeError(f"{isa} worker {i} exited for {cfg}")
                return json.loads(line)
            for cfg in cases:
                initial = [ask(i, cfg, 2) for i in (0, 1)]
                reps = max(3, min(2000, int(a.sample_ms / 1000 / max(x["seconds"] for x in initial))))
                samples, digests = [[], []], set(x["digest"] for x in initial)
                for round_ in range(a.rounds):
                    for i in ((0, 1) if round_ % 2 == 0 else (1, 0)):
                        got = ask(i, cfg, reps)
                        samples[i].append(got["seconds"])
                        digests.add(got["digest"])
                if len(digests) != 1:
                    raise AssertionError(f"Selected peak mismatch: {isa} {cfg}")
                row = dict(cfg, isa=isa, repetitions=reps, samples=samples,
                           baseline_us=statistics.median(samples[0]) * 1e6,
                           candidate_us=statistics.median(samples[1]) * 1e6,
                           speedup=statistics.median([x / y for x, y in zip(*samples)]),
                           digest=next(iter(digests)), detail=initial[0]["detail"])
                results.append(row)
                output.write_text(json.dumps(results, indent=2) + "\n")
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
