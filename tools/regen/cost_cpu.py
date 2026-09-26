"""Measure CPU configuration costs at each false-dismissal budget.

The table only ranks configurations. Accuracy remains the responsibility of
the reference-profile gate model. Measurements use warm public-API calls on a
bank of distinct templates, with every band timed on the same data.

Run with OPENBLAS_NUM_THREADS=1 PYTHONPATH=python python tools/regen/cost_cpu.py
The JSON file is written after each group so an interrupted sweep can resume.
"""
import argparse
import json
import platform
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import matchedfilter as mf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
from test_api import inspiral_power  # noqa: E402
from hmf_tune import bands_for  # noqa: E402


def _values(value, typ):
    return [typ(part) for part in value.split(',')]


def _cpu_name():
    try:
        for line in Path('/proc/cpuinfo').read_text().splitlines():
            if line.startswith('model name'):
                return line.split(':', 1)[1].strip()
    except OSError:
        pass
    if sys.platform == 'darwin':
        for key in ('machdep.cpu.brand_string', 'hw.model'):
            try:
                name = subprocess.check_output(['sysctl', '-n', key], text=True).strip()
            except (OSError, subprocess.CalledProcessError):
                continue
            if name:
                return name
    return platform.processor() or platform.machine() or 'unknown'


def _power(n, profile):
    if profile == 'pycbc':
        if n != 4096:
            raise ValueError('PyCBC asset has n=4096')
        return np.load(ROOT / 'tests/data/reference_profile_pycbc.npy')
    return np.asarray(inspiral_power(n, exponent=float(profile)), dtype=np.float32)


def _measure_group(n, snr, fd, profile, nd, nt, bands, rounds, seed=1):
    power = _power(n, profile)
    rng = np.random.default_rng(seed + 18)
    phases = rng.random((nt, n), dtype=np.float32)
    templates = (np.sqrt(power)[None, :] *
                 np.exp((2j * np.pi * phases).astype(np.complex64))).astype(np.complex64)
    templates /= np.linalg.norm(templates, axis=1, keepdims=True)
    rng = np.random.default_rng(seed)
    data = (rng.standard_normal((nd, n)) +
            1j * rng.standard_normal((nd, n))).astype(np.complex64)
    plans = []
    try:
        for band in bands:
            plan = mf.HierarchicalFilter(n, nd, nt, snr=snr, fd=fd,
                                         band=band, taps=8, device='cpu')
            plans.append((band, plan))
            plan.set_reference(power)
            plan.set_data(data)
            plan.set_templates(templates)
            plan.run(binsize=n, threshold=snr)
        samples = {band: [] for band in bands}
        for round_number in range(rounds):
            order = plans[round_number % len(plans):] + plans[:round_number % len(plans)]
            if round_number % 2:
                order = order[::-1]
            for band, plan in order:
                end = time.perf_counter() + .015
                while time.perf_counter() < end:
                    plan.run(binsize=n, threshold=snr)
                start = time.perf_counter()
                count = 0
                while count < 2 or time.perf_counter() - start < .025:
                    plan.run(binsize=n, threshold=snr)
                    count += 1
                samples[band].append((time.perf_counter() - start) * 1000 / count)
        rows = []
        for band, plan in plans:
            fraction, beff = mf._band_features(power, band)
            rows.append(dict(n=n, snr=snr, fd=fd, profile=profile, ndata=nd,
                             ntemplates=nt, band=band,
                             ms=float(np.median(samples[band])),
                             blocks_ms=samples[band], fraction=fraction,
                             beff=beff, refine_rate=plan.refine_rate,
                             gate=plan._coarse_value(band)))
        return rows
    finally:
        # Drop plans before the next group, particularly at the large lengths.
        plans.clear()


def _write_table(path, records, cpu, commit):
    groups = {}
    for row in records:
        key = (row['n'], row['snr'], row['fd'], row['profile'],
               row['ndata'], row['ntemplates'])
        groups.setdefault(key, {})[row['band']] = row
    lines = [
        '# matchedfilter CPU COST table -- FDR and batch-aware relative costs',
        '# format cost-fd-pairs-v1',
        '# cpu     ' + cpu,
        '# commit  ' + commit,
        '# Warm public-API cost relative to the widest band for this profile and shape.',
        '# The reference-profile gate model computes accuracy independently.',
        '# U=2 and K=8 are retained as configuration metadata; taps are inert.',
        '# COST n band U K snr fd pairs f beff relative_cost',
    ]
    for key in sorted(groups, key=lambda group: tuple(map(str, group))):
        by_band = groups[key]
        base = by_band[max(by_band)]['ms']
        for band, row in sorted(by_band.items()):
            lines.append('COST %d %d 2 8 %.2f %.6g %d %.6f %.3f %.6f' %
                         (row['n'], band, row['snr'], row['fd'],
                          row['ndata'] * row['ntemplates'], row['fraction'],
                          row['beff'], row['ms'] / base))
    path.write_text('\n'.join(lines) + '\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=ROOT / 'python/matchedfilter/cost.txt')
    ap.add_argument('--measurements', type=Path,
                    default=ROOT / 'docs/measurements/cpu-cost-2026-09-26.json')
    ap.add_argument('--sizes', default='1024,2048,4096,8192,16384,32768,65536,131072,262144')
    ap.add_argument('--snrs', default='5,5.5,6,6.5')
    ap.add_argument('--fds', default='.01,.001,.0001')
    ap.add_argument('--profiles', default='-2.3333333333333335,-2,-1.6666666666666667,-1.3333333333333333')
    ap.add_argument('--shape', default='8x64')
    ap.add_argument('--teaser-shape', default='16x1024')
    ap.add_argument('--rounds', type=int, default=5)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--include-pycbc', action='store_true')
    ap.add_argument('--repair-outliers', action='store_true',
                    help='remeasure groups with any timing-block spread above 25%%')
    args = ap.parse_args(argv)
    sizes = _values(args.sizes, int)
    snrs = _values(args.snrs, float)
    fds = _values(args.fds, float)
    profiles = args.profiles.split(',')
    shape = tuple(map(int, args.shape.split('x')))
    teaser_shape = tuple(map(int, args.teaser_shape.split('x')))
    if args.rounds < 3 or any(v < 1 for v in shape + teaser_shape):
        ap.error('need at least three rounds and positive shape dimensions')
    cpu = _cpu_name()
    commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'],
                                     cwd=ROOT, text=True).strip()
    records = []
    if args.measurements.exists():
        records = json.loads(args.measurements.read_text())['records']
    requested = {(n, snr, fd, profile, nd, nt)
                 for n in sizes for snr in snrs for fd in fds
                 for profile in profiles + (['pycbc'] if args.include_pycbc and n == 4096 else [])
                 for nd, nt in ([shape, teaser_shape] if n == 4096 else [shape])}
    if args.repair_outliers:
        redo = {(row['n'], row['snr'], row['fd'], row['profile'],
                 row['ndata'], row['ntemplates']) for row in records
                if max(row['blocks_ms']) / min(row['blocks_ms']) > 1.25
                and (row['n'], row['snr'], row['fd'], row['profile'],
                     row['ndata'], row['ntemplates']) in requested}
        if redo:
            print('remeasuring %d noisy groups' % len(redo), flush=True)
            records = [row for row in records if (row['n'], row['snr'], row['fd'],
                row['profile'], row['ndata'], row['ntemplates']) not in redo]
    done = {(row['n'], row['snr'], row['fd'], row['profile'],
             row['ndata'], row['ntemplates']) for row in records}
    for n in sizes:
        bands = [band for band in bands_for(n) if band < n]
        for snr in snrs:
            for fd in fds:
                these_profiles = profiles + (['pycbc'] if args.include_pycbc and n == 4096 else [])
                for profile in these_profiles:
                    shapes = [shape]
                    if n == 4096 and teaser_shape != shape:
                        shapes.append(teaser_shape)
                    for nd, nt in shapes:
                        key = (n, snr, fd, profile, nd, nt)
                        if key in done:
                            continue
                        rows = _measure_group(*key, bands, args.rounds, args.seed)
                        records.extend(rows)
                        done.add(key)
                        args.measurements.parent.mkdir(parents=True, exist_ok=True)
                        args.measurements.write_text(json.dumps(dict(cpu=cpu, commit=commit,
                            seed=args.seed,
                            records=records), indent=2) + '\n')
                        print('n=%d snr=%g fd=%g profile=%s shape=%dx%d best=%d' %
                              (n, snr, fd, profile, nd, nt,
                               min(rows, key=lambda row: row['ms'])['band']), flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    _write_table(args.out, records, cpu, commit)
    print('wrote', args.out, flush=True)


if __name__ == '__main__':
    main()
