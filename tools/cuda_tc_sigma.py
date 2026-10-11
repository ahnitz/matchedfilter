#!/usr/bin/env python3
"""The tensor-core coarse gate (src/gpu/coarse_tc.cu): exactness, rounding error and speed.

With the bound off (mf_c16_raw = 1) the kernel reports the fp16-path value at its elected lag.
Against float64 it measures, per band and per gate_margin family:
  - lag agreement with the exact maximum (ties within the error aside),
  - err = |y16[lag] - y[lag]| / (u rms), u = 2^-11, rms^2 = sum_j |x_j|^2 (the Slang tier's
    units, tools/coarse_layout.py C16_SIGMA): its standard deviation is sigma_B, and
    kappa_B = z(C16_FAIL) sigma_B goes into the build (tools/build_ptx.py COARSE_TC_SIGMA);
  - device ns per pair on 16384 synthetic pairs (min of 5), next to the Slang variants'.

    python tools/cuda_tc_sigma.py [--pairs 8192]
"""
import argparse
import ctypes
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "tests"))
from matchedfilter import _cudacompute as cc          # noqa: E402

U = 2.0 ** -11
GRID_PER_SM = 16           # persistent warps: blocks per SM


def launch(ctx, fn, wpb, band, D, T, raw=True):
    """(|value|, lag, complex value) per template of the one data row D, bound off or on."""
    nt = T.shape[0]
    rows = D.shape[0]
    bufs = [cc._Buffer(ctx, rows * band * 4), cc._Buffer(ctx, nt * band * 4),
            cc._Buffer(ctx, rows * nt * 4), cc._Buffer(ctx, rows * nt * 8)]
    try:
        st = ctx.stream
        bufs[0].write(cc._pack_half2(D), st)
        bufs[1].write(cc._pack_half2(T), st)
        ent = ctx._c16_flags[ctx._labels[fn.value]]
        v = ctypes.c_uint32(1 if raw else 0)
        cc.check_cuda(ctx.cuda.cuMemcpyHtoD_v2(ent[0], ctypes.byref(v), 4), "flag")
        ent[1] = int(raw)
        slots = rows * ((nt + 1) // 2)
        ctx._launch(fn, min(-(-slots // wpb), ctx.sm_count * GRID_PER_SM), 32 * wpb,
                    [bufs[0].dptr, bufs[1].dptr, bufs[2].dptr, bufs[3].dptr,
                     cc._u32(nt), cc._u32(0), cc._u32(band), cc._u32(rows),
                     cc._i32(0), cc._u32(1), cc._u32(0)], stream=st)
        ctx._sync(st)
        idx = bufs[2].read(np.int32, rows * nt)
        val = bufs[3].read(np.complex64, rows * nt)
    finally:
        for b in bufs:
            b.destroy()
    return idx.reshape(rows, nt), val.reshape(rows, nt)


def tc_kernel(ctx, band, wpb):
    stem = "coarse_tc_%d_w%d" % (band, wpb)
    return ctx._load(stem, cc._PTX_DIR / (stem + ".ptx"), "fusedTierB", 32 * wpb)


def time_kernel(ctx, fn, wg, nblocks, args, reps=5):
    e0, e1 = ctx._new_event_timed(), ctx._new_event_timed()
    ms = ctypes.c_float()
    best = 1e30
    for _ in range(reps):
        cc.check_cuda(ctx.cuda.cuEventRecord(e0, ctx.stream), "rec")
        ctx._launch(fn, nblocks, wg, args, stream=ctx.stream)
        cc.check_cuda(ctx.cuda.cuEventRecord(e1, ctx.stream), "rec")
        cc.check_cuda(ctx.cuda.cuEventSynchronize(e1), "sync")
        ctx.cuda.cuEventElapsedTime(ctypes.byref(ms), e0, e1)
        best = min(best, ms.value)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bands", type=int, nargs="+", default=[256, 512])
    ap.add_argument("--reps", type=int, default=8, help="family draws per band (x 128 templates)")
    args = ap.parse_args()
    from test_gpu_c16_bound import _families
    ctx = cc.Context(0)
    for band in args.bands:
        fn, wg = tc_kernel(ctx, band, 4), 128
        errs, lagbad, n, fam_sig = [], 0, 0, {}
        for rep in range(args.reps):
            rng = np.random.default_rng(99 + 7 * rep + band)
            for fi, (D, T) in enumerate(_families(band, rng, 128)):
                y = np.fft.ifft(D * np.conj(T), axis=1) * band
                T = T * (8.0 / np.abs(y).max(axis=1))[:, None]
                D16 = D.astype(np.complex64)
                T16 = T.astype(np.complex64)
                # The exact transform of what the kernel reads: the fp16-rounded inputs.
                Dh = (D16.real.astype(np.float16).astype(np.float64)
                      + 1j * D16.imag.astype(np.float16).astype(np.float64))
                Th = (T16.real.astype(np.float16).astype(np.float64)
                      + 1j * T16.imag.astype(np.float16).astype(np.float64))
                x = Dh * np.conj(Th)
                ye = np.fft.ifft(x, axis=1) * band
                rms = np.sqrt((np.abs(x) ** 2).sum(axis=1))
                idx, val = launch(ctx, fn, 4, band, D16, T16, raw=True)
                lag = idx[0]
                exact_lag = np.abs(ye).argmax(axis=1)
                e = np.abs(val[0] - ye[np.arange(ye.shape[0]), lag]) / (U * rms)
                # A different lag is only acceptable within the error: the magnitudes tie.
                diff = lag != exact_lag
                tie = np.abs(np.abs(ye[np.arange(128), lag]) - np.abs(ye[np.arange(128), exact_lag])) \
                    <= 4 * U * rms * 8
                lagbad += int((diff & ~tie).sum())
                errs.extend(e.tolist())
                fam_sig.setdefault(fi, []).extend(e.tolist())
                n += e.size
        errs = np.asarray(errs)
        sig = {f: float(np.std(v)) for f, v in fam_sig.items()}
        print("band %4d: %d pairs, lag mismatches beyond a tie %d, err (u rms) mean %.3f std %.3f "
              "max %.3f; std per family %s" % (band, n, lagbad, errs.mean(), errs.std(), errs.max(),
                                               {k: round(v, 3) for k, v in sig.items()}))
        # Speed: 16384 pairs as 512 rows x 32 templates, like _time_coarse.
        P, ntm = 16384, 32
        ndm = P // ntm
        rng = np.random.default_rng(0)
        x = (rng.standard_normal((ndm, band)) + 1j * rng.standard_normal((ndm, band))) * 0.1
        bufs = [cc._Buffer(ctx, ndm * band * 4), cc._Buffer(ctx, ntm * band * 4),
                cc._Buffer(ctx, P * 4), cc._Buffer(ctx, P * 8)]
        bufs[0].write(cc._pack_half2(x), ctx.stream)
        bufs[1].write(cc._pack_half2(x[:ntm]), ctx.stream)
        for wpb in (2, 4):
            f, w = tc_kernel(ctx, band, wpb), 32 * wpb
            t = time_kernel(ctx, f, w, min(-(-(ndm * ntm // 2) // wpb), ctx.sm_count * GRID_PER_SM),
                            [bufs[0].dptr, bufs[1].dptr, bufs[2].dptr, bufs[3].dptr,
                             cc._u32(ntm), cc._u32(0), cc._u32(band), cc._u32(ndm),
                             cc._i32(0), cc._u32(1), cc._u32(0)])
            # Flops of the matrix formulation actually issued (tensor-core MACs x 2):
            # stage 1: 4 real 16 x M x M products; stage 2: 4 real 16 x 16 x M; plus the
            # nothing else (the elected value comes from the accumulators).
            mac = 4 * 16 * (band // 16) * (band // 16) + 4 * 16 * 16 * (band // 16)
            tf = 2 * mac * P / (t * 1e-3) / 1e12
            print("  wpb %d: %.3f ns/pair, %.1f TFLOP/s tensor (dense fp16 peak 362 TF on L40S)"
                  % (wpb, t * 1e6 / P, tf))
        for b in bufs:
            b.destroy()


if __name__ == "__main__":
    main()
