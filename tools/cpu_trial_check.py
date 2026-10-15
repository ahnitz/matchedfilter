#!/usr/bin/env python3
"""Bounded CPU cold-start study; accept timing only after stored trials settle.

Each cold start gets an independent cost file. Runs containing calibration, new
locks, or unfinished records are retained as calibration evidence, never included
in steady throughput. A failure to settle within the budget is a failed study.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def locks(records):
    return {k: {f: v[f] for f in ('winner', 'chain', 'q15', 'rechecked') if f in v}
            for k, v in records.items()
            if k.startswith(('block-trial|', 'chain-trial|', 'q15-trial|'))
            and not k.endswith('|batches')}


def pending(records):
    out = []
    for k, v in records.items():
        if not isinstance(v, dict) or not any(v.get('samples', {}).values()):
            continue
        if k.startswith('block-trial|') and 'winner' not in v:
            out.append(k)
        if k.startswith('q15-trial|') and 'q15' not in v:
            out.append(k)
        if k.startswith('chain-trial|') and k.endswith('|batches') and 'chain' not in records.get(k[:-8], {}):
            out.append(k)
    return sorted(out)


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bank', required=True)
    p.add_argument('--profiles', required=True)
    p.add_argument('--out', type=Path, required=True, help='new study directory (must not exist)')
    p.add_argument('--starts', type=int, default=10)
    p.add_argument('--max-runs', type=int, default=4)
    p.add_argument('--segments', type=int, default=6)
    args = p.parse_args()
    if min(args.starts, args.max_runs) < 1 or args.segments <= 2:
        p.error('positive starts/max-runs and at least three segments required')
    args.out.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               PYTHONPATH=str(root / 'python'), MF_AUTOTUNE='1', MF_TRIAL_RECHECK='0')
    results = []
    for cold in range(args.starts):
        cost = args.out / ('cost-%02d.json' % cold)
        env['MF_COST_FILE'] = str(cost.resolve())
        attempts = []
        for attempt in range(args.max_runs):
            stem = args.out / ('start-%02d-run-%02d' % (cold, attempt))
            before = read(cost)
            cmd = [sys.executable, str(root / 'tools/ladder.py'), '--bank', args.bank,
                   '--profiles', args.profiles, '--device', 'cpu', '--tops', '1', '--pure',
                   '--segments', str(args.segments), '--out', str(stem) + '.json']
            with Path(str(stem) + '.log').open('w') as log:
                run = subprocess.run(cmd, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=900)
            after = read(cost)
            report = read(Path(str(stem) + '.json'))
            stable = (run.returncode == 0 and report.get('steady_valid') is True
                      and locks(before) == locks(after) and not pending(after))
            attempts.append(dict(returncode=run.returncode, stable=stable, before=locks(before),
                                 after=locks(after), pending=pending(after),
                                 trial_work=report.get('cpu_trial_work_in_steady'),
                                 throughput=report.get('templates_in_real_time', {}).get('total')))
            print('start %d run %d: %s' % (cold + 1, attempt + 1, 'steady' if stable else 'calibrating'), flush=True)
            if stable or run.returncode:
                break
        results.append(dict(start=cold, settled=stable, attempts=attempts))
        (args.out / 'summary.json').write_text(json.dumps(results, indent=2))
    return 0 if all(r['settled'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
