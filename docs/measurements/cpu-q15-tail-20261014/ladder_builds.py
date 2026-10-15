#!/usr/bin/env python3
"""Four quiet, fresh-process ladder runs in ABBA or reversed BAAB order.

Scheduling quiet cores is the caller's responsibility. --dry-run prints commands only.
The driver records exact commands, immutable build hashes, file hashes and raw report
paths, and rejects output-hash or native-build changes. Eight segments means one warm
segment followed by seven measured steady segments. No native build is performed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--baseline', type=Path, required=True)
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--bank', type=Path, required=True)
p.add_argument('--profiles', type=Path, required=True)
p.add_argument('--cost-file', type=Path, required=True)
p.add_argument('--output-dir', type=Path, required=True)
p.add_argument('--harness', type=Path, required=True)
p.add_argument('--baseline-commit', default='b3c1b022')
p.add_argument('--baseline-sha', default='ce7076733a62db4c115c9ce4572950b5460e19a30cc317d2eeb19e3dae6c2d0f')
p.add_argument('--candidate-sha')
p.add_argument('--cpu', type=int, default=4)
p.add_argument('--target', default='AVX3')
p.add_argument('--segments', type=int, default=8)
p.add_argument('--dry-run', action='store_true')
p.add_argument('--order', choices=['ABBA','BAAB'], default='ABBA')
a = p.parse_args()
if a.segments < 2 or a.cpu < 0:
    p.error('segments must be at least 2 and cpu must be nonnegative')
for path in (a.bank,a.profiles,a.cost_file,a.harness):
    if not path.is_file(): p.error(f'file does not exist: {path}')
roots = {'baseline':a.baseline.resolve(),'candidate':a.candidate.resolve()}
for label,root in roots.items():
    if not (root/'matchedfilter/__init__.py').is_file(): p.error(f'not a build directory: {root}')
order = [{'A':'baseline','B':'candidate'}[x] for x in a.order]
commands=[]
for i,label in enumerate(order):
    out=a.output_dir.resolve()/f'{i}-{label}.json'
    command=['taskset','-c',str(a.cpu),sys.executable,str(a.harness.resolve()),
             '--bank',str(a.bank.resolve()),'--profiles',str(a.profiles.resolve()),
             '--target',a.target,'--runs','1','--segments',str(a.segments),'--q15','1','--output',str(out)]
    commands.append((label,out,command))
if a.dry_run:
    print(json.dumps([dict(variant=label,PYTHONPATH=str(roots[label]),MF_COST_FILE=str(a.cost_file.resolve()),command=command)
                      for label,_,command in commands],indent=2))
    raise SystemExit

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
cores={}
for label,root in roots.items():
    files=list((root/'matchedfilter').glob('_core*.so'))
    if len(files)!=1: raise RuntimeError(f'need exactly one native extension in {root}: {files}')
    cores[label]=digest(files[0])
for label,want in [('baseline',a.baseline_sha),('candidate',a.candidate_sha)]:
    if want and cores[label]!=want: raise RuntimeError(f'{label} core hash differs: {cores[label]} != {want}')
a.output_dir.mkdir(parents=True,exist_ok=True)
report=dict(baseline_commit=a.baseline_commit,order=order,cpu=a.cpu,target=a.target,segments=a.segments,
            steady_segments=a.segments-1,builds={k:dict(path=str(roots[k]),core_sha256=cores[k]) for k in roots},
            cost_file=str(a.cost_file.resolve()),cost_file_sha256_before=digest(a.cost_file),rows=[])
expected=None
for i,(label,out,command) in enumerate(commands):
    env=dict(os.environ,PYTHONPATH=str(roots[label]),MF_COST_FILE=str(a.cost_file.resolve()),
             OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MF_GATE16='0')
    for key in ('MF_HMF_PROF','MF_HMF_TRACE','MF_HMF_DUMP'): env.pop(key,None)
    log=a.output_dir/f'{i}-{label}.log'
    print(f'Starting {i+1}/4 {label}',flush=True)
    with log.open('w') as stream:
        subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
    full=json.loads(out.read_text())
    if full['core_sha256']!=cores[label]: raise AssertionError('build changed during comparison')
    run=full['runs'][0]; r=run['report']; steady=r['steady_calls']['segment']
    if steady!=a.segments-1: raise AssertionError(f'unexpected steady segment count {steady}')
    identity=(run['output_sha256'],full['bank_sha256'],full['profiles_sha256'])
    if expected is None: expected=identity
    elif identity!=expected: raise AssertionError(f'input/output mismatch at {i}: {identity} != {expected}')
    row=dict(variant=label,command=command,report=str(out),log=str(log),core_sha256=cores[label],
             output_sha256=run['output_sha256'],
             times_ms={k:1000*v/steady for k,v in r['steady_s'].items()},
             native_stages_ms={s['stage']:1000*s['measured_s'] for s in r['roofline']['stages']},
             stage_counts={s['stage']:s['count'] for s in r['roofline']['stages']})
    report['rows'].append(row)
    (a.output_dir/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"Completed {label}: fine={row['times_ms']['fine']:.3f}ms segment={row['times_ms']['segment']:.3f}ms output={run['output_sha256']}",flush=True)
report.update(all_output_hashes_identical=True,bank_sha256=expected[1],profiles_sha256=expected[2],
              cost_file_sha256_after=digest(a.cost_file),comparison={})
for section in ('times_ms','native_stages_ms'):
    means={label:{k:statistics.mean(r[section][k] for r in report['rows'] if r['variant']==label)
                  for k in report['rows'][0][section]} for label in roots}
    report['comparison'][section]={k:dict(baseline=means['baseline'][k],candidate=means['candidate'][k],
        speedup=means['baseline'][k]/means['candidate'][k]) for k in means['baseline'] if means['candidate'][k]>0}
(a.output_dir/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['comparison'],indent=2))
