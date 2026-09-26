"""Score CPU cost selection against measured bands in a sweep JSON file."""
import argparse
import json
from pathlib import Path

import numpy as np
import matchedfilter as mf

from regen.cost_cpu import _power


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--measurements', type=Path, required=True)
    ap.add_argument('--new', type=Path, required=True)
    ap.add_argument('--old', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(argv)
    records = json.loads(args.measurements.read_text())['records']
    newer = mf._load_tuning(str(args.new))
    older = mf._load_tuning(str(args.old))
    groups = {}
    for row in records:
        key = (row['n'], row['snr'], row['fd'], row['profile'],
               row['ndata'], row['ntemplates'])
        groups.setdefault(key, {})[row['band']] = row['ms']
    cases = []
    for (n, snr, fd, profile, nd, nt), times in groups.items():
        power = _power(n, profile)
        new_band = mf._cost_candidates(power, n, snr, newer, fd, nd*nt)[0]['band']
        old_band = mf._cost_candidates(power, n, snr, older, fd, nd*nt)[0]['band']
        if new_band not in times or old_band not in times:
            raise ValueError('selected band was not measured: %s' %
                             ((n, snr, fd, profile, nd, nt, new_band, old_band),))
        fastest = min(times, key=times.get)
        cases.append(dict(n=n, snr=snr, fd=fd, profile=profile,
                          ndata=nd, ntemplates=nt, fastest=fastest,
                          new_band=new_band, old_band=old_band,
                          best_ms=times[fastest], new_ms=times[new_band],
                          old_ms=times[old_band],
                          new_vs_old=times[new_band]/times[old_band],
                          new_regret=times[new_band]/times[fastest]))
    ratios = np.array([row['new_vs_old'] for row in cases])
    summary = dict(cases=len(cases), median_new_vs_old=float(np.median(ratios)),
                   geometric_mean_new_vs_old=float(np.exp(np.log(ratios).mean())),
                   faster_5pct=int(np.sum(ratios < .95)),
                   slower_5pct=int(np.sum(ratios > 1.05)),
                   worst_regression=max(cases, key=lambda row: row['new_vs_old']),
                   largest_gain=min(cases, key=lambda row: row['new_vs_old']))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(dict(summary=summary, cases=cases), indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
