#!/usr/bin/env python3
"""Per-kernel roofline on a Metal device, at the bench's production shapes.

Each stage of tools/ladder.py (middle correlation, fine hierarchical bank, single-template
follow-up) is run once through the library on the device, with every kernel the library
encodes captured at Context._dispatch. Each captured kernel is then replayed ALONE, in its own
command buffer, against the same buffers and parameters, and timed on the device
(GPUStartTime/GPUEndTime, min of --reps). Work per kernel is modelled from its parameters:

  flops   the algorithmic count: 5 n log2 n per transform, 6 n per complex product, 3 n
          per magnitude and running maximum. It omits twiddles, address arithmetic and
          barriers, so it understates what the ALUs do.
  bytes   unique DRAM traffic, a lower bound: every input row read once, every output
          written once. Rows a kernel re-reads per pair (the data row against each template)
          are expected to hit the cache; the per-pair figure is reported beside it.

The ceilings are measured on the device the same way (sustained FMA and add chains, a
float4 copy and a read), and quoted beside the vendor figures: on the M2 the measured FMA
rate is well under the 3.6 TFLOP/s spec, and the fraction of each is shown. A kernel's
attainable time is max(flops / compute ceiling, unique bytes / bandwidth); achieved/attainable
is the roofline fraction, and the larger term names the binding resource.

    python tools/metal_roofline.py --bank BANK.hdf [--reps 20] [--json out.json]

Only Metal: the replay drives Metal command buffers directly.
"""
import argparse
import ctypes
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))
import ladder                                          # noqa: E402
import gpu_roofline                                    # noqa: E402
from matchedfilter import TimeDomainFilterBank         # noqa: E402
from matchedfilter import _mtlcompute as M             # noqa: E402

SPEC = dict(fma=3.6e12, bw=100e9)
#: Arrays whose memory captured buffers alias (written in place); kept for replays.
_KEEP = []


# ---- device-timed execution --------------------------------------------------------------
def _timed(ctx, encode):
    """Run encode(enc) in its own command buffer; device seconds."""
    o = ctx.o
    with o.autorelease_pool():
        cmd = o.call(ctx.queue, b"commandBuffer")
        enc = o.call(cmd, b"computeCommandEncoder")
        encode(enc)
        o.call(enc, b"endEncoding", restype=None)
        o.call(cmd, b"commit", restype=None)
        o.call(cmd, b"waitUntilCompleted", restype=None)
        ctx._check_completed(cmd)
        t0 = o.call(cmd, b"GPUStartTime", restype=ctypes.c_double)
        t1 = o.call(cmd, b"GPUEndTime", restype=ctypes.c_double)
    return t1 - t0


def ceilings(reps=10):
    p = gpu_roofline.Probe()
    ctx = p.ctx
    threads, groups, iters = 1024, 4096, 4096
    out = M._Buffer(ctx, threads * groups * 4)
    res = {}
    for op in ("fma", "add"):
        best = 0.0
        for w in (16, 32):
            pso = p.pipeline(gpu_roofline.chain_src(w, op))

            # chain_src binds out at 0 and iters at 1, not the library's layout
            def run(e, pso=pso):
                o = ctx.o
                o.call(e, b"setComputePipelineState:", restype=None, args=(pso,),
                       argtypes=(ctypes.c_void_p,))
                o.call(e, b"setBuffer:offset:atIndex:", restype=None, args=(out.handle, 0, 0),
                       argtypes=(ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong))
                v = ctypes.c_uint32(iters)
                o.call(e, b"setBytes:length:atIndex:", restype=None, args=(ctypes.byref(v), 4, 1),
                       argtypes=(ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong))
                o.call(e, b"dispatchThreadgroups:threadsPerThreadgroup:", restype=None,
                       args=(M._MTLSize(groups, 1, 1), M._MTLSize(threads, 1, 1)),
                       argtypes=(M._MTLSize, M._MTLSize))
            t = min(_timed(ctx, run) for _ in range(reps))
            best = max(best, threads * groups * iters * w * (2 if op == "fma" else 1) / t)
        res[op] = best
    nf4 = (256 << 20) // 16
    src, dst = M._Buffer(ctx, nf4 * 16), M._Buffer(ctx, nf4 * 16)
    pso = p.pipeline(gpu_roofline.COPY)

    def copy(e):
        o = ctx.o
        o.call(e, b"setComputePipelineState:", restype=None, args=(pso,), argtypes=(ctypes.c_void_p,))
        for i, b in enumerate((src, dst)):
            o.call(e, b"setBuffer:offset:atIndex:", restype=None, args=(b.handle, 0, i),
                   argtypes=(ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong))
        o.call(e, b"dispatchThreadgroups:threadsPerThreadgroup:", restype=None,
               args=(M._MTLSize(nf4 // 256, 1, 1), M._MTLSize(256, 1, 1)),
               argtypes=(M._MTLSize, M._MTLSize))
    res["bw"] = 2 * nf4 * 16 / min(_timed(ctx, copy) for _ in range(reps))
    res["device"] = ctx.name
    for b in (out, src, dst):
        b.destroy()
    ctx.destroy()
    return res


# ---- capture -------------------------------------------------------------------------------
class Capture:
    """Record every kernel a Metal context encodes while active."""

    def __init__(self):
        self.records = []
        self._orig = M.Context._dispatch

    def __enter__(self):
        rec, orig = self.records, self._orig

        def dispatch(ctx, enc, pso, params, buffers, tg, groups=None, indirect=None, offsets=None):
            rec.append(dict(ctx=ctx, pso=pso, params=tuple(params), buffers=list(buffers), tg=tg,
                            groups=groups, indirect=indirect, offsets=offsets,
                            name=getattr(ctx, "pipeline_names", {}).get(pso, ("?", 0, "?"))))
            return orig(ctx, enc, pso, params, buffers, tg, groups, indirect, offsets)
        M.Context._dispatch = dispatch
        return self

    def __exit__(self, *exc):
        M.Context._dispatch = self._orig


def replay(records, reps):
    """Device seconds per record (min over reps), each kernel alone in its command buffer."""
    best = [math.inf] * len(records)
    groups = [None] * len(records)
    for _ in range(reps):
        for i, r in enumerate(records):
            ctx = r["ctx"]
            if r["name"][2] == "compactPairs":
                r["buffers"][2].write(np.array([0, 1, 1], np.uint32))

            def enc(e, r=r):
                M.Context._dispatch(ctx, e, r["pso"], r["params"], r["buffers"], r["tg"],
                                    r["groups"], r["indirect"], r["offsets"])
            best[i] = min(best[i], _timed(ctx, enc))
            groups[i] = (int(r["indirect"].read(np.uint32, 1)[0]) if r["indirect"] is not None
                         else r["groups"])
    return best, groups


# ---- work model ----------------------------------------------------------------------------
def fft_flops(n):
    return 5 * n * math.log2(n)


def work(r, groups):
    """(flops, unique bytes, per-pair bytes) for one captured kernel."""
    stem, n, entry = r["name"]
    p = r["params"]
    if entry == "seriesForward":
        return groups * fft_flops(n), 2 * groups * n * 8, 2 * groups * n * 8
    if entry == "packCoarse":
        _, band, count, packed = p
        return 0, count * (8 + (4 if packed else 8)), count * (8 + (4 if packed else 8))
    if entry == "compactPairs":
        pairs = p[0]
        return 0, pairs * 8 + groups * 0, pairs * 8
    nt = p[0]
    cb = 4 if entry.startswith("coarse16") else 8
    if entry.startswith("coarse16") or entry in ("fusedTierB", "refineListed"):
        nbins = p[5]
        # coarse16pK packs K pairs per threadgroup (padded to whole groups).
        ppg = int(entry[len("coarse16p"):]) if entry.startswith("coarse16p") else 1
        pairs = groups * ppg
        listed = entry == "refineListed"
        total = r["groups"] if not listed else None
        flops = pairs * (6 * n + fft_flops(n) + 3 * n)
        if listed:
            # A listed pair reads its data row and template row; rows are shared, so the
            # unique count is bounded by the bank and by the pairs actually listed.
            nd_rows = r["buffers"][0].nbytes // (n * cb)
            nt_rows = r["buffers"][1].nbytes // (n * cb)
            uniq = min(pairs, nd_rows) * n * cb + min(pairs, nt_rows) * n * cb + pairs * nbins * 12
        else:
            nd = -(-total * ppg // nt)
            uniq = (nd + nt) * n * cb + pairs * nbins * 12
        return flops, uniq, pairs * (2 * n * cb + nbins * 12)
    if entry in ("fullCorrelationSeries", "fullCorrelation"):
        pairs = groups
        valid = (p[3] - p[2]) if entry == "fullCorrelationSeries" else n
        nd = pairs // nt
        flops = pairs * (6 * n + fft_flops(n))
        return flops, (nd + nt) * n * 8 + pairs * valid * 8, pairs * (2 * n * 8 + valid * 8)
    return 0, 0, 0


def table(records, times, groups, ceil, stage):
    agg = defaultdict(lambda: dict(calls=0, t=0.0, flops=0.0, uniq=0.0, pp=0.0, groups=0))
    for r, t, g in zip(records, times, groups):
        stem, n, entry = r["name"]
        key = "%s (%s)" % (entry, stem)
        f, u, pp = work(r, g)
        a = agg[key]
        a["calls"] += 1
        a["t"] += t
        a["flops"] += f
        a["uniq"] += u
        a["pp"] += pp
        a["groups"] += g
    rows = []
    total = sum(a["t"] for a in agg.values())
    for key, a in sorted(agg.items(), key=lambda kv: -kv[1]["t"]):
        t_c = a["flops"] / ceil["fma"]
        t_m = a["uniq"] / ceil["bw"]
        bound = "compute" if t_c >= t_m else "memory"
        rows.append(dict(
            stage=stage, kernel=key, calls=a["calls"], groups=a["groups"], device_ms=a["t"] * 1e3,
            share=a["t"] / total if total else 0.0,
            gflops=a["flops"] / a["t"] / 1e9 if a["t"] else 0.0,
            gbs_unique=a["uniq"] / a["t"] / 1e9 if a["t"] else 0.0,
            gbs_per_pair=a["pp"] / a["t"] / 1e9 if a["t"] else 0.0,
            of_fma_measured=a["flops"] / a["t"] / ceil["fma"] if a["t"] else 0.0,
            of_fma_spec=a["flops"] / a["t"] / SPEC["fma"] if a["t"] else 0.0,
            of_bw=a["uniq"] / a["t"] / ceil["bw"] if a["t"] else 0.0,
            bound=bound, roofline=max(t_c, t_m) / a["t"] if a["t"] else 0.0))
    return rows


# ---- production shapes ---------------------------------------------------------------------
def stages(bank, reps, nfine=1):
    """Capture and replay the ladder's three stages for its largest top template."""
    args = argparse.Namespace(seg_samples=1 << 20, start_pad=120.0, end_pad=16.0, pad=4096,
                              threshold=6.0, fd=1e-3, peak_window=1.0, asym_threshold=6.0,
                              asym_bin_width=0.03, asym_num_bins=1000, fft_length=0)
    top = ladder.load_tops(bank, 1)[0]
    rng = np.random.default_rng(1)
    amp = np.sqrt(ladder.profile())
    S = args.seg_samples
    a0, a1 = int(args.start_pad * ladder.RATE), S - int(args.end_pad * ladder.RATE)
    probe = TimeDomainFilterBank(top["mid_taps"], tap_counts=top["mid_counts"], engine="corr")
    y = probe.correlate_series(ladder.analytic_series(rng, 1 << 18, amp))[:, 1 << 15:-(1 << 15)]
    scale = (1.0 / np.sqrt(np.mean(np.abs(y) ** 2, axis=1) / 2)).astype(np.float32)
    mid = TimeDomainFilterBank(top["mid_taps"] * scale[:, None], tap_counts=top["mid_counts"],
                               engine="corr", device="gpu:0")
    xm = probe.correlate_series(ladder.analytic_series(rng, 1 << 18, amp)) * scale[:, None]
    ser = ladder.analytic_series(rng, S, amp)
    win = slice(max(0, a0 - args.pad), min(S, a1 + args.pad))
    mid.correlate_series(ser, windows=win)                       # plans, pipelines
    with Capture() as cap:
        mids = mid.correlate_series(ser, windows=win)
    # The middle writes in place: its captured output buffer is this array's memory.
    _KEEP.append(mids)
    out = {"middle": cap.records}
    # The fine banks with the most templates: the bench's dominant shape.
    order = sorted(range(len(top["fine"])), key=lambda i: -top["fine"][i][1].shape[0])[:nfine]
    out["fine"], out["asym"] = [], []
    bs = max(1, int(round(args.asym_bin_width * ladder.RATE)))
    half = (args.asym_num_bins // 2) * bs
    meta = dict(top=top["top"], middle_templates=int(top["mid_taps"].shape[0]))
    for row in order:
        m, taps, c = top["fine"][row]
        pf = TimeDomainFilterBank(taps, tap_counts=c, engine="corr")
        yf = pf.correlate_series(xm[row])[:, 1 << 15:-(1 << 15)]
        taps = taps / np.sqrt(np.mean(np.abs(yf) ** 2, axis=1) / 2)[:, None].astype(np.float32)
        b = TimeDomainFilterBank(taps, tap_counts=c, engine="hier", threshold=args.threshold,
                                 false_dismissal=args.fd, device="gpu:0",
                                 binsize=int(args.peak_window * ladder.RATE))
        b.set_reference(ladder.profile(), delta_f=ladder.DF)
        b.filter_series(mids[row], windows=slice(a0, a1))
        with Capture() as cap:
            r = b.filter_series(mids[row], windows=slice(a0, a1))
        out["fine"] += cap.records
        meta.setdefault("fine_banks", []).append(dict(
            middle=int(m), templates=int(taps.shape[0]), taps=(int(c.min()), int(c.max())),
            chains=[g.plan.config for g in b._groups], n=[g.n for g in b._groups],
            triggers=int(len(r.snr))))
        c0 = int(r.sample_indices[np.argmax(np.abs(r.snr))]) if len(r.snr) else (a0 + a1) // 2
        ti = int(r.template_indices[np.argmax(np.abs(r.snr))]) if len(r.snr) else 0
        kw = dict(windows=slice(max(0, c0 - half), min(S, c0 + half)), binsize=bs,
                  threshold=0.0, template_index=ti)
        b.filter_series(mids[row], **kw)
        with Capture() as cap:
            b.filter_series(mids[row], **kw)
        out["asym"] += cap.records
    res = {}
    for stage, recs in out.items():
        times, groups = replay(recs, reps)
        res[stage] = (recs, times, groups)
    return res, meta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--fine-banks", type=int, default=1)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    ceil = ceilings()
    print("device %s: measured FMA %.0f GFLOP/s (spec %.0f), add %.0f GFLOP/s, copy %.1f GB/s (spec %.0f)"
          % (ceil["device"], ceil["fma"] / 1e9, SPEC["fma"] / 1e9, ceil["add"] / 1e9,
             ceil["bw"] / 1e9, SPEC["bw"] / 1e9))
    res, meta = stages(a.bank, a.reps, a.fine_banks)
    print("shapes:", json.dumps(meta, default=str))
    rows = []
    for stage, (recs, times, groups) in res.items():
        rows += table(recs, times, groups, ceil, stage)
    hdr = ("| stage | kernel | calls | groups | device ms | share | GFLOP/s | of FMA (meas/spec) "
           "| GB/s unique | GB/s per-pair | of BW | bound | roofline |")
    print(hdr)
    print("|" + "---|" * 13)
    for r in rows:
        print("| %s | %s | %d | %d | %.3f | %.0f%% | %.0f | %.0f%% / %.0f%% | %.1f | %.1f | %.0f%% | %s | %.0f%% |"
              % (r["stage"], r["kernel"], r["calls"], r["groups"], r["device_ms"], 100 * r["share"],
                 r["gflops"], 100 * r["of_fma_measured"], 100 * r["of_fma_spec"], r["gbs_unique"],
                 r["gbs_per_pair"], 100 * r["of_bw"], r["bound"], 100 * r["roofline"]))
    if a.json:
        Path(a.json).write_text(json.dumps(dict(ceilings=ceil, shapes=meta, rows=rows), indent=1,
                                           default=str))


if __name__ == "__main__":
    main()
