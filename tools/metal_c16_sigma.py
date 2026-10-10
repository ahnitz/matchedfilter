#!/usr/bin/env python3
"""Measure the Metal fp16 coarse tier's rounding error, for its derived bound (C16_KAPPA).

The bound every fp16 first tier reports (tierb.slang, c16Bound) is

    B = |c16| (1 + 3u) + kappa u rms(y),   u = 2^-11,  rms(y)^2 = sum_j |x_j|^2

(1+3u) is proven; kappa = z(C16_FAIL) * sigma_B, with sigma_B the standard deviation of the
transform's own error at the elected lag in units of u rms(y), per band. Vulkan's sigma was
measured on the Radeon (tools/coarse_layout.py C16_SIGMA); Apple's fp16 arithmetic and the
Metal builds (tiled and untiled) are measured here, on the gate_margin families (noise,
profile-shaped, injection, loud transient, full scale).

The raw fp16 maximum is read with the bound switch off (MF_VK_C16_BOUND=0, compiled into the
Metal library as MF_C16_RAW). Every pair passes (gate 0) and its coarse value is read from
the hier_peaks coarse buffer, against the float64 exact maximum.

    python tools/metal_c16_sigma.py [--n 64 128 256 512 1024 2048] [--reps 8]
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))
os.environ["MF_VK_C16_BOUND"] = "0"
import gate_margin as G  # noqa: E402
from matchedfilter import _mtlcompute as M  # noqa: E402

U = 2.0 ** -11


def raw_values(ctx, N, D, T, nt):
    n = 4096
    rng = np.random.default_rng(0)
    data = (rng.standard_normal((1, n)) * 1e-3).astype(np.complex64)
    data[:, :N] = D
    tmpl = np.zeros((nt, n), np.complex64)
    tmpl[:, :N] = T
    ctx._hier.clear()
    ctx.hier_peaks(n, N, data, tmpl, np.ascontiguousarray(tmpl[:, :N]), 0.0, binsize=n,
                   threshold=0.0)
    (bufs,) = ctx._hier.values()
    cv = bufs["cval"].read(np.float32, 2 * nt).reshape(nt, 2)
    return np.hypot(cv[:, 0], cv[:, 1]).astype(np.float64)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, nargs="+", default=[64, 128, 256, 512, 1024, 2048])
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--nt", type=int, default=64)
    a = ap.parse_args()
    ctx = M.Context(0)
    for N in a.n:
        res = {}
        for tile in ("0", "1"):
            os.environ["MF_METAL_COARSE_TILE"] = tile
            es, eb, worst = [], [], (0.0, "")
            for rep in range(a.reps):
                rng = np.random.default_rng(1000 * N + rep)
                for name, D, T, K in G.families(N, rng, a.nt):
                    if name == "fullscale":
                        continue          # overflow is the fail-open path, not the error
                    raw = raw_values(ctx, N, D, T, a.nt)
                    x = D[0].astype(np.complex128) * np.conj(T.astype(np.complex128))
                    rms = np.sqrt((np.abs(x) ** 2).sum(axis=1))
                    ok = np.isfinite(raw)
                    es.append(((raw - K) / (U * rms))[ok])
                    # what the bound's rms term must cover after the proven (1+3u) factor
                    b = ((raw * (1 + 3 * U) - K) / (U * rms))[ok]
                    eb.append(b)
                    if b.size and b.min() < worst[0]:
                        worst = (float(b.min()), name)
            e = np.concatenate(es)
            res[tile] = (e.std(), np.concatenate(eb).min(), worst[1], e.size)
        sig = max(v[0] for v in res.values())
        kap = 7.034 * np.ceil(sig * 10) / 10
        print("band %5d  sigma untiled %.2f tiled %.2f -> sigma_B %.1f kappa %.1f | after (1+3u) "
              "worst e %.2f (%s) / %.2f (%s), %d pairs"
              % (N, res["0"][0], res["1"][0], np.ceil(sig * 10) / 10, kap, res["0"][1], res["0"][2],
                 res["1"][1], res["1"][2], res["0"][3]), flush=True)


if __name__ == "__main__":
    main()
