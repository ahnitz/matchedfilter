#!/usr/bin/env python3
"""Measure a GPU's fp16 coarse tier rounding error, for its derived bound (C16_KAPPA).

The bound every fp16 first tier reports (tierb.slang, c16Bound) is

    B = |c16| (1 + 3u) + kappa u rms(y),   u = 2^-11,  rms(y)^2 = sum_j |x_j|^2

(1+3u) is proven; kappa = z(C16_FAIL) * sigma_B, with sigma_B the standard deviation of the
transform's own error at the elected lag in units of u rms(y), per band. The tables in
tools/coarse_layout.py were measured with this: C16_SIGMA on the Radeon 8060S (Vulkan) and
C16_SIGMA_APPLE on the M2 (Metal). It runs every coarse layout the device offers at each
band (tiled and untiled; ctx.coarse_layouts), on the gate_margin families (noise,
profile-shaped, injection, loud transient; full scale is the fail-open path, not error).

Each layout's kernel is dispatched directly, as the host's coarse timer does
(_gpuhier._time_coarse_layouts), with the raw maximum compiled in (MF_COARSE_RAW=1) and
gate 0, and its coarse values are read back against the float64 exact maxima.

    python tools/c16_sigma.py [--backend metal] [--n 64 ... 2048] [--reps 8] [--nt 64]
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
os.environ["MF_COARSE_RAW"] = "1"           # before the package reads it
sys.path.insert(0, str(HERE))
import gate_margin as G  # noqa: E402

U = 2.0 ** -11


def _context(backend):
    import importlib
    module = {"metal": "_mtlcompute", "vulkan": "_vkcompute", "cuda": "_cudacompute"}[backend]
    return importlib.import_module("matchedfilter." + module).Context(0)


def raw_values(ctx, band, layout, D, T):
    """The coarse tier's raw maximum for each pair of D (1, band) with T (nt, band), from
    one dispatch of this layout's kernel."""
    from matchedfilter._coarse import coarse_launch
    from matchedfilter._shared import pack_half2
    nt = T.shape[0]
    rows = D.astype(np.complex64) if ctx.inplace_feed else pack_half2(D.astype(np.complex64))
    data = ctx._x_alloc(rows.nbytes)
    data.write(rows)
    tmpl = ctx._x_alloc(nt * band * 4)
    tmpl.write(pack_half2(T.astype(np.complex64)))
    cidx = ctx._x_alloc(nt * 4)
    cval = ctx._x_alloc(nt * 8, readback=True)
    native = None
    try:
        kernel = ctx._coarse_kernel(band, layout, stride=band if ctx.inplace_feed else 0,
                                    scale=0, rowwin=False)
        slot, groups = coarse_launch(1, nt, layout[1], layout[2], band)
        lst = ctx._x_list("c16 sigma")
        lst.dispatch(kernel, ctx._x_coarse_groups(kernel, groups), [data, tmpl, cidx, cval],
                     (nt, 0, band, slot, band.bit_length() - 1, 1,
                      ctx._gate_bits(0.0, band, layout)))
        native = lst.end()
        ctx._x_time(native, {}, 1)          # (runs it twice: a warm-up, one timed)
        cv = np.asarray(cval.read(np.float32, 2 * nt)).reshape(nt, 2)
    finally:
        if native is not None:
            ctx._x_release(native)
        for b in (data, tmpl, cidx, cval):
            b.destroy()
    return np.hypot(cv[:, 0], cv[:, 1]).astype(np.float64)


def measure(ctx, band, layout, reps, nt):
    """(sigma, the worst residual after (1+3u) in u rms(y), its family, pairs)."""
    es, eb, worst = [], [], (0.0, "")
    for rep in range(reps):
        rng = np.random.default_rng(1000 * band + rep)
        for name, D, T, K in G.families(band, rng, nt):
            if name == "fullscale":
                continue
            raw = raw_values(ctx, band, layout, D, T)
            x = D[0].astype(np.complex128) * np.conj(T.astype(np.complex128))
            rms = np.sqrt((np.abs(x) ** 2).sum(axis=1))
            ok = np.isfinite(raw)
            es.append(((raw - K) / (U * rms))[ok])
            b = ((raw * (1 + 3 * U) - K) / (U * rms))[ok]
            eb.append(b)
            if b.size and b.min() < worst[0]:
                worst = (float(b.min()), name)
    e = np.concatenate(es)
    return float(e.std()), float(np.concatenate(eb).min()), worst[1], int(e.size)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", default="metal", choices=("metal", "vulkan", "cuda"))
    ap.add_argument("--n", type=int, nargs="+", default=[64, 128, 256, 512, 1024, 2048])
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--nt", type=int, default=64)
    a = ap.parse_args(argv)
    from matchedfilter._coarse import parse_label
    ctx = _context(a.backend)
    try:
        for band in a.n:
            res = {}
            for label, layout in zip(ctx.coarse_layouts(band), ctx._x_coarse_candidates(band)):
                if parse_label(label) is None:
                    continue                     # a driver's own gate (CUDA tensor cores)
                res[label] = measure(ctx, band, layout, a.reps, a.nt)
            if not res:
                print("band %5d  no fp16 coarse layout on this device" % band)
                continue
            sig = max(v[0] for v in res.values())
            sigma_b = np.ceil(sig * 10) / 10
            label, (s, low, fam, pairs) = min(res.items(), key=lambda kv: kv[1][1])
            print("band %5d  sigma %.2f..%.2f over %d layouts -> sigma_B %.1f kappa %.1f | "
                  "worst after (1+3u) %.2f (%s, %s), %d pairs each"
                  % (band, min(v[0] for v in res.values()), sig, len(res), sigma_b,
                     7.034 * sigma_b, low, label, fam, pairs), flush=True)
    finally:
        ctx.destroy()
    return 0


if __name__ == "__main__":
    sys.exit(main())
