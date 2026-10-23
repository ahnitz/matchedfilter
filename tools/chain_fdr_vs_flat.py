#!/usr/bin/env python3
"""The hierarchical chain's false dismissal against the flat filter, by injection.

Signals at intrinsic SNR `--snr` in unit Gaussian noise, at random lags; a flat detection
is |z| >= snr at full resolution, and the chain misses one when its reported peak for that
block is absent or below snr. Two chains run on the same data with the gate model's
thresholds (gatechain.chain_thresholds): FP32 tiers, and the Q15 screen as the first tier
and every tier before the last (where this back end has one). Each must stay within the budget; every
detection both report must carry the flat filter's value.

  python tools/chain_fdr_vs_flat.py --n 2048 --chain 256,512,1024 --inj 400000
"""
import argparse
import os
import sys
import time

import numpy as np

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo not in sys.path:
    sys.path.insert(0, repo)

import matchedfilter as mf
import matchedfilter._core as _core
from tests.spectral_profiles import make_spectral_profile, SHAPE_NAMES


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--n", type=int, default=2048)
    ap.add_argument("--chain", default="256,512,1024")
    ap.add_argument("--snr", type=float, default=6.0)
    ap.add_argument("--fd", type=float, default=1e-3)
    ap.add_argument("--inj", type=int, default=200000)
    ap.add_argument("--shape", default="aligo_o4_inspiral", choices=SHAPE_NAMES)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    n, chain, B = a.n, tuple(int(x) for x in a.chain.split(",")), 64
    power = make_spectral_profile(a.shape, n)
    thr = [float(x) for x in mf._gatechain.chain_thresholds(power, n, a.snr, a.fd, chain)["thresholds"]]
    h = np.sqrt(power).astype(np.complex64)
    h /= np.sqrt((np.abs(h) ** 2).sum())
    hc = np.conj(h)
    flat = mf.MatchedFilter(n, ndata=B, ntemplates=1)
    flat.set_templates(hc[None, :])

    def chain_filter(q15):
        e = _core.HMF(n, B, 1, list(chain), 8)
        e.set_reference(power)
        e.set_thresholds(thr)
        e.set_template(0, hc)
        if not e.set_q15(q15) and q15:
            return None
        return e

    engines = {"FP32 tiers": chain_filter(False), "Q15 tiers": chain_filter(True)}
    engines = {k: e for k, e in engines.items() if e is not None}
    peaks = {k: np.empty((B, 1), mf.PEAK_DTYPE) for k in engines}
    cnt = np.empty(B, np.int32)
    ei, ev, em = np.empty(0, np.int64), np.empty(0, np.complex64), np.empty(0, np.float32)
    rng = np.random.default_rng(a.seed)
    k = np.arange(n)
    det = 0
    miss = dict.fromkeys(engines, 0)
    mismatch = dict.fromkeys(engines, 0)
    t0 = time.time()
    for it in range(a.inj // B):
        lag = rng.uniform(n // 4, 3 * n // 4, B)
        D = (a.snr * h[None, :] * np.exp(2j * np.pi * lag[:, None] * k[None, :] / n)
             + (rng.standard_normal((B, n)) + 1j * rng.standard_normal((B, n)))).astype(np.complex64)
        flat.set_data(D)
        zf = np.abs(flat.run(binsize=n, threshold=0.0)["value"][:, 0, 0])
        hit = zf >= a.snr
        det += int(hit.sum())
        for name, e in engines.items():
            for d in range(B):
                e.set_data(d, D[d])
            e.run(0, B, 0, 1, n, a.snr, 0, n, ei, ev, em, cnt, peaks[name])
            p = peaks[name][:, 0]
            got = (p["index"] >= 0) & (np.abs(p["value"]) >= a.snr)
            miss[name] += int((hit & ~got).sum())
            both = hit & got
            mismatch[name] += int((np.abs(np.abs(p["value"][both]) - zf[both]) > 1e-3 * zf[both]).sum())
        if (it + 1) % 1000 == 0:
            print("  %d injections, %d flat detections, %.0f s" % ((it + 1) * B, det, time.time() - t0), flush=True)
    print("n=%d chain=%s shape=%s snr=%.1f budget=%.0e thresholds=%s"
          % (n, chain, a.shape, a.snr, a.fd, ["%.3f" % x for x in thr]))
    print("flat detections: %d of %d injections" % (det, a.inj // B * B))
    ok = True
    for name in engines:
        fd = miss[name] / max(det, 1)
        print("  %-17s misses %6d  FD %.5f (%.2fx budget)  value mismatches %d"
              % (name, miss[name], fd, fd / a.fd, mismatch[name]))
        ok &= mismatch[name] == 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
