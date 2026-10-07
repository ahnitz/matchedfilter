#!/usr/bin/env python3
"""Measure dismissal at the model's gate using independent filter injections.

Example: python tools/audit_gate_model.py --n 1024 --chain 256 --snr 5.5 \
    --fd .0001 --trials 1500000
         python tools/audit_gate_model.py --n 2048 --chain 256 512 --snr 6 --fd .001

The confidence interval describes binomial counting uncertainty, not model
error or uncertainty about whether a reference represents a template bank.
"""
import argparse
import json
import math

import numpy as np
import matchedfilter as mf
import os
import sys
from matchedfilter import gatechain, gatemodel
from matchedfilter.benchmark import _inspiral_power
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests'))
from _gatelib import measure  # noqa: E402


def wilson(missed, detected):
    if not detected:
        return None
    z = 1.959963984540054
    p = missed / detected
    d = 1 + z*z/detected
    mid = (p + z*z/(2*detected))/d
    half = z*math.sqrt(p*(1-p)/detected + z*z/(4*detected**2))/d
    return max(0., mid-half), min(1., mid+half)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--n', type=int, default=4096)
    ap.add_argument('--chain', type=int, nargs='+', help='bands of the gate chain (default: the model\'s choice)')
    ap.add_argument('--snr', type=float, default=5.5)
    ap.add_argument('--fd', type=float, nargs='+', default=[.01, .001, .0001])
    ap.add_argument('--trials', type=int)
    ap.add_argument('--seed', type=int, default=417)
    ap.add_argument('--profile', help='length-n NumPy power profile')
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args(argv)
    power = np.load(a.profile) if a.profile else _inspiral_power(a.n)
    for fd in a.fd:
        if a.chain:
            chain = tuple(a.chain)
        else:
            best, _ = gatechain.choose_chain(power, a.n, a.snr, fd, cost=gatechain.calibrate_costs(a.n, 64))
            if best is None:
                raise ValueError('no chain with a resolvable gate')
            chain = best["chain"]
        plan = gatechain.chain_thresholds(power, a.n, a.snr, fd, chain)
        if plan is None:
            raise ValueError('budget is below model resolution')
        gate = plan["thresholds"]
        trials = a.trials if a.trials is not None else max(20000, int(200/fd))
        if trials <= 0:
            raise ValueError('trials must be positive')
        rate, detected, _ = measure(a.n, chain, a.snr, trials,
                                    seed=a.seed, power=power, thr=gate, device=a.device)
        missed = round(rate*detected)
        model_fdr = (gatemodel.dismissal(power, a.n, chain[0], a.snr, gate[0], fd_hint=fd)
                     if len(chain) == 1 else fd)
        print(json.dumps(dict(n=a.n, chain=list(chain), snr=a.snr, fd=fd, gate=list(gate),
                              device=a.device, trials_requested=trials,
                              seed=a.seed, detected=detected, missed=missed,
                              measured_fdr=rate, wilson95=wilson(missed, detected),
                              model_fdr=model_fdr)), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
