#!/usr/bin/env python3
"""Interleave isolated builds on a real run_series fixture, with output checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np


def worker(fixture, variant):
    import matchedfilter as mf
    from matchedfilter import _core
    with np.load(fixture, allow_pickle=False) as z:
        d = {k: z[k] for k in z.files}
    n = int(d['n_fft'])
    nt = variant['templates'] or int(d['nbatch'])
    if not 1 <= nt <= int(d['nbatch']):
        raise ValueError('template count must fit the capture')
    d['series'] = d['series'] * np.float32(variant['scale'])
    p = mf.HierarchicalFilter(n, 1, nt, snr=float(d['threshold']),
                             fd=float(d['fd']), band=1024, taps=8)
    p.set_reference(d['reference'])
    p.set_templates(d['templates'][:nt])
    if float(d['first_stage']) > 0:
        p.set_first_stage(float(d['first_stage']))
    args = (d['series'], d['starts'], d['win_start'], d['win_end'])
    kw = dict(binsize=n, threshold=float(d['threshold']), raw=True)
    for _ in range(3):
        idx, val = p.run_series(*args, **kw)
    idx0, val0 = idx.copy(), val.copy()
    if variant['scale'] == 1:
        np.testing.assert_array_equal(idx0[:, :, 0], d['index'][:, :nt])
        np.testing.assert_allclose(val0[:, :, 0], d['value'][:, :nt], rtol=1e-5, atol=1e-5)
    print(json.dumps(dict(core_sha256=hashlib.sha256(Path(_core.__file__).read_bytes()).hexdigest(),
                          backend=mf.backend(), affinity=sorted(os.sched_getaffinity(0)),
                          environment={k: v for k, v in os.environ.items() if k.startswith('MF_')},
                          config=list(p.config), peaks=int((idx0 >= 0).sum()),
                          index=idx0.tolist(), real=val0.real.tolist(), imag=val0.imag.tolist())), flush=True)
    for line in sys.stdin:
        if line.strip() != 'run':
            raise ValueError('expected run')
        c0 = time.thread_time_ns()
        t0 = time.perf_counter_ns()
        idx, val = p.run_series(*args, **kw)
        wall = (time.perf_counter_ns() - t0) / 1e6
        cpu = (time.thread_time_ns() - c0) / 1e6
        np.testing.assert_array_equal(idx, idx0)
        np.testing.assert_array_equal(val, val0)
        print(json.dumps([wall, cpu]), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('baseline', type=Path)
    ap.add_argument('candidate', type=Path)
    ap.add_argument('fixture', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--rounds', type=int, default=31)
    ap.add_argument('--templates', type=int, default=0, help='0 uses the full captured bank')
    ap.add_argument('--scale', type=float, default=1., help='scale the input to vary refinement load')
    ap.add_argument('--candidate-env', action='append', default=[], metavar='MF_NAME=VALUE',
                    help='diagnostic native override applied only to the candidate worker')
    a = ap.parse_args()
    if a.rounds < 1:
        ap.error('--rounds must be positive')
    if a.templates < 0 or not np.isfinite(a.scale) or a.scale <= 0:
        ap.error('templates must be nonnegative and scale finite and positive')
    variant = dict(templates=a.templates, scale=a.scale)
    overrides = {}
    for item in a.candidate_env:
        key, sep, value = item.partition('=')
        if not sep or not key.startswith('MF_'):
            ap.error('--candidate-env requires MF_NAME=VALUE')
        overrides[key] = value
    workers, metadata = [], []
    samples = [[], []]
    try:
        for i, root in enumerate((a.baseline, a.candidate)):
            env = dict(os.environ, PYTHONPATH=str(root.resolve()))
            for key in ('MF_PBMAX', 'MF_HMF_PROF', 'MF_DGROUP'):
                env.pop(key, None)
            if i:
                env.update(overrides)
            p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                  '--worker', str(a.fixture.resolve()), json.dumps(variant)],
                                 env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            workers.append(p)
            metadata.append(json.loads(p.stdout.readline()))
        np.testing.assert_array_equal(metadata[0]['index'], metadata[1]['index'])
        for key in ('real', 'imag'):
            np.testing.assert_allclose(metadata[0][key], metadata[1][key], rtol=1e-5, atol=1e-5)
        for r in range(a.rounds):
            for i in ((0, 1) if r % 2 == 0 else (1, 0)):
                workers[i].stdin.write('run\n')
                workers[i].stdin.flush()
                samples[i].append(json.loads(workers[i].stdout.readline()))
        ratios = np.array(samples[0])[:, 0] / np.array(samples[1])[:, 0]
        for m in metadata:
            for key in ('index', 'real', 'imag'):
                del m[key]
        result = dict(metadata=metadata, variant=variant, candidate_env=overrides,
                      samples_wall_cpu_ms=samples,
                      fixture_sha256=hashlib.sha256(a.fixture.read_bytes()).hexdigest(),
                      median_ms=[float(np.median(np.array(s)[:, 0])) for s in samples],
                      paired_median_speedup=float(np.median(ratios)),
                      wins=int((ratios > 1).sum()), rounds=a.rounds)
        a.output.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
    finally:
        for p in workers:
            p.stdin.close()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.terminate()
                p.wait()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--worker':
        worker(sys.argv[2], json.loads(sys.argv[3]))
    else:
        main()
