#!/usr/bin/env python3
"""Orchestrate rebuilding cost tables across all available hardware architectures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]

HOSTS = [
    {
        'id': 'haswell',
        'arch': 'genuineintel-family6-model63',
        'model': 'Intel Xeon E5-2698 v3',
        'type': 'ssh_haswell',
        'python': '/home/ahnitz/miniforge3/bin/python3',
        'dir': '/home/ahnitz/bench_mf',
    },
    {
        'id': 'sugwg',
        'arch': 'genuineintel-family6-model85',
        'model': 'Intel Xeon Platinum 8260',
        'type': 'ssh_sugwg',
        'python': '/home/ahnitz/miniforge3/bin/python3',
        'dir': '/home/ahnitz/bench_mf',
    },
    {
        'id': 'gravity-dev1',
        'arch': 'authenticamd-family25-model33',
        'model': 'AMD Ryzen 9 5950X',
        'type': 'ssh_direct',
        'host': 'dev1',
        'python': '/home/ahnitz/miniconda3/bin/python3',
        'dir': '/home/ahnitz/bench_mf',
    },
    {
        'id': 'gravity-dev2',
        'arch': 'authenticamd-family26-model112',
        'model': 'AMD Ryzen AI MAX+ 395',
        'type': 'ssh_direct',
        'host': 'dev2',
        'python': '/home/ahnitz/miniconda3/bin/python3',
        'dir': '/home/ahnitz/bench_mf',
    },
    {
        'id': 'gravity-dev3',
        'arch': 'authenticamd-family23-model104',
        'model': 'AMD Ryzen 5 5500U',
        'type': 'ssh_direct',
        'host': 'dev3',
        'python': '/home/ahnitz/matchedfilter-benchmark-20260926/venv/bin/python',
        'dir': '/home/ahnitz/bench_mf',
    },
    {
        'id': 'gravity-dev4',
        'arch': 'genuineintel-family6-model186',
        'model': 'Intel Core i5-13500H',
        'type': 'ssh_direct',
        'host': 'dev4',
        'python': '/home/ahnitz/matchedfilter-benchmark-20260926/venv/bin/python',
        'dir': '/home/ahnitz/bench_mf',
    },
    {
        'id': 'local-fedora',
        'arch': 'authenticamd-family25-model116',
        'model': 'AMD Ryzen 7 7840U',
        'type': 'local',
        'python': sys.executable,
        'dir': str(ROOT),
    },
]


def make_cmd(host_info, cmd_str):
    htype = host_info['type']
    if htype == 'local':
        return ['bash', '-c', cmd_str]
    elif htype == 'ssh_direct':
        return ['ssh', '-o', 'BatchMode=yes', host_info['host'], cmd_str]
    elif htype == 'ssh_sugwg':
        return ['ssh', '-o', 'BatchMode=yes', '-J', 'its-condor-t1.syr.edu',
                'ahnitz@sugwg-login2.syr.edu', cmd_str]
    elif htype == 'ssh_haswell':
        inner = repr(cmd_str)
        return ['ssh', '-o', 'BatchMode=yes', '-J', 'its-condor-t1.syr.edu',
                'ahnitz@sugwg-login2.syr.edu',
                f'ssh -i ~/.ssh/orangekey -o BatchMode=yes ahnitz@10.5.201.169 {inner}']
    raise ValueError(htype)


def run_host(host_info, sizes='1024,2048,4096,8192,16384,32768'):
    hid = host_info['id']
    arch = host_info['arch']
    hdir = host_info['dir']
    py = host_info['python']

    meas_file = f'{hdir}/docs/measurements/{arch}.json'
    out_table = f'{hdir}/python/matchedfilter/cost-{arch}.txt'

    seed_file = ROOT / 'docs/measurements/seed_large.json'

    # 1. Prepare directory and seed file on remote host
    prep_cmd = f'mkdir -p {hdir}/docs/measurements {hdir}/python/matchedfilter'
    subprocess.run(make_cmd(host_info, prep_cmd), check=True)

    if host_info['type'] != 'local':
        # Copy seed file
        if host_info['type'] == 'ssh_direct':
            scp_cmd = ['scp', '-o', 'BatchMode=yes', str(seed_file),
                       f"{host_info['host']}:{meas_file}"]
        elif host_info['type'] == 'ssh_sugwg' or host_info['type'] == 'ssh_haswell':
            # sugwg and haswell share NFS; copy to sugwg
            scp_cmd = ['scp', '-o', 'BatchMode=yes', '-J', 'its-condor-t1.syr.edu',
                       str(seed_file), f"ahnitz@sugwg-login2.syr.edu:{meas_file}"]
        subprocess.run(scp_cmd, check=True)
    else:
        import shutil
        shutil.copyfile(seed_file, meas_file)

    # 2. Run sweep
    cmd = (f'OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 '
           f'PYTHONPATH={hdir}/python {py} {hdir}/tools/regen/cost_cpu.py '
           f'--sizes={sizes} '
           f'--rounds=3 '
           f'--include-pycbc '
           f'--measurements={meas_file} '
           f'--out={out_table}')

    full_cmd = make_cmd(host_info, cmd)
    t0 = time.time()
    print(f'[{hid}] Starting measurement sweep ({host_info["model"]})...', flush=True)
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    dt = time.time() - t0
    if res.returncode != 0:
        print(f'[{hid}] FAILED after {dt:.1f}s:\n{res.stderr[-500:]}', flush=True)
        return res.returncode, dt, res.stdout, res.stderr

    last_line = res.stdout.strip().splitlines()[-1] if res.stdout.strip() else 'done'
    print(f'[{hid}] SUCCESS in {dt:.1f}s: {last_line}', flush=True)

    # 3. Retrieve files to local repository if remote
    local_meas = ROOT / f'docs/measurements/{arch}.json'
    local_table = ROOT / f'python/matchedfilter/cost-{arch}.txt'
    if host_info['type'] != 'local':
        if host_info['type'] == 'ssh_direct':
            subprocess.run(['scp', '-o', 'BatchMode=yes',
                            f"{host_info['host']}:{meas_file}", str(local_meas)], check=True)
            subprocess.run(['scp', '-o', 'BatchMode=yes',
                            f"{host_info['host']}:{out_table}", str(local_table)], check=True)
        elif host_info['type'] in ('ssh_sugwg', 'ssh_haswell'):
            subprocess.run(['scp', '-o', 'BatchMode=yes', '-J', 'its-condor-t1.syr.edu',
                            f"ahnitz@sugwg-login2.syr.edu:{meas_file}", str(local_meas)], check=True)
            subprocess.run(['scp', '-o', 'BatchMode=yes', '-J', 'its-condor-t1.syr.edu',
                            f"ahnitz@sugwg-login2.syr.edu:{out_table}", str(local_table)], check=True)

    # 4. Score against old generic cost table
    score_out = ROOT / f'docs/measurements/score-{arch}.json'
    score_cmd = [sys.executable, str(ROOT / 'tools/score_cpu_cost_retune.py'),
                 '--measurements', str(local_meas),
                 '--new', str(local_table),
                 '--old', str(ROOT / 'python/matchedfilter/cost.txt'),
                 '--out', str(score_out)]
    sres = subprocess.run(score_cmd, capture_output=True, text=True)
    if sres.returncode == 0:
        summary = json.loads(score_out.read_text())['summary']
        print(f"[{hid}] Score vs generic: median={summary['median_new_vs_old']:.3f}x, "
              f"geomean={summary['geometric_mean_new_vs_old']:.3f}x, "
              f"faster={summary['faster_5pct']}/{summary['cases']}, "
              f"slower={summary['slower_5pct']}/{summary['cases']}", flush=True)

    return res.returncode, dt, res.stdout, res.stderr


def main():
    threads = []
    results = {}

    def worker(h):
        rc, dt, stdout, stderr = run_host(h)
        results[h['id']] = (rc, dt, stdout, stderr)

    for h in HOSTS:
        t = threading.Thread(target=worker, args=(h,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print('\n=== All sweeps and scoring complete ===')
    for h in HOSTS:
        rc, dt, stdout, stderr = results.get(h['id'], (-1, 0, '', ''))
        status = 'OK' if rc == 0 else 'FAIL'
        print(f"{h['id']} ({h['model']}): {status} in {dt:.1f}s")


if __name__ == '__main__':
    main()
