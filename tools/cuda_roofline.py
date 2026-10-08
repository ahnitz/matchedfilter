#!/usr/bin/env python3
"""Per-kernel roofline of the CUDA backend at the bench's production shapes.

Runs tools/ladder.py's call pattern (1 top, N segments, --resident) on a CUDA
device with MF_GPU_TIMING=1 and a launch recorder, so every kernel is measured at
exactly the shapes the bench gives it. Per kernel label it reports device time,
work (flops) and DRAM traffic from an analytic model, achieved rate against the
MEASURED ceilings (an FMA loop and a device-to-device stream, tools/cuda_ceilings.cu),
and registers / static shared / spill bytes / theoretical occupancy from the driver.

Hardware counters (ncu) need admin rights on most clusters
(RmProfilingAdminOnly=1); this script needs none. Its traffic figures are a model:
"min" is the unique data a kernel must touch (inputs reused across templates are
assumed to stay in L2), "max" counts every per-pair load as DRAM traffic.

    python tools/cuda_roofline.py --bank BANK.hdf [--segments 2] [--json out.json]
    python tools/cuda_roofline.py --build-ceilings     # recompile the ceiling PTX (needs NVRTC)
"""
import argparse
import ctypes
import json
import math
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "python"))
CEIL_SRC = HERE / "cuda_ceilings.cu"
CEIL_PTX = HERE / "cuda_ceilings.ptx"


def build_ceilings():
    lib = ctypes.CDLL(os.environ.get("MF_NVRTC", "libnvrtc.so.12"))
    prog = ctypes.c_void_p()
    src = CEIL_SRC.read_bytes()
    assert lib.nvrtcCreateProgram(ctypes.byref(prog), src, b"ceilings.cu", 0, None, None) == 0
    opts = (ctypes.c_char_p * 1)(b"--gpu-architecture=compute_75")
    rc = lib.nvrtcCompileProgram(prog, 1, opts)
    size = ctypes.c_size_t()
    lib.nvrtcGetProgramLogSize(prog, ctypes.byref(size))
    log = ctypes.create_string_buffer(size.value)
    lib.nvrtcGetProgramLog(prog, log)
    if rc:
        raise SystemExit(log.value.decode())
    lib.nvrtcGetPTXSize(prog, ctypes.byref(size))
    ptx = ctypes.create_string_buffer(size.value)
    lib.nvrtcGetPTX(prog, ptx)
    CEIL_PTX.write_bytes(ptx.value)
    print("wrote", CEIL_PTX)


def ceilings(ctx):
    """Measured fp32 FMA rate (flop/s) and device-to-device stream bandwidth (byte/s)."""
    from matchedfilter import _cudacompute as cc
    fma = ctx._load("ceil_fma", CEIL_PTX, "fmaPeak", 256)
    cp = ctx._load("ceil_copy", CEIL_PTX, "copyStream", 256)
    out = cc._Buffer(ctx, 4 * 256 * 4096)
    blocks, threads, iters = ctx.sm_count * 16, 256, 4096
    best_f = 0.0
    for _ in range(5):
        e0, e1 = ctx._event(), ctx._event()
        ctx.cuda.cuEventRecord(e0, ctx.stream)
        ctx._launch(fma, blocks, threads, [out.dptr, ctypes.c_int(iters), ctypes.c_float(0.999),
                                           ctypes.c_float(1e-3)])
        ctx.cuda.cuEventRecord(e1, ctx.stream)
        ctx._sync()
        ms = ctypes.c_float()
        ctx.cuda.cuEventElapsedTime(ctypes.byref(ms), e0, e1)
        best_f = max(best_f, blocks * threads * iters * 8 * 2 / (ms.value * 1e-3))
    nbytes = 1 << 30
    a, b = cc._Buffer(ctx, nbytes), cc._Buffer(ctx, nbytes)
    n4 = nbytes // 16
    best_b = 0.0
    for _ in range(5):
        e0, e1 = ctx._event(), ctx._event()
        ctx.cuda.cuEventRecord(e0, ctx.stream)
        ctx._launch(cp, ctx.sm_count * 8, 256, [a.dptr, b.dptr, ctypes.c_size_t(n4)])
        ctx.cuda.cuEventRecord(e1, ctx.stream)
        ctx._sync()
        ms = ctypes.c_float()
        ctx.cuda.cuEventElapsedTime(ctypes.byref(ms), e0, e1)
        best_b = max(best_b, 2 * nbytes / (ms.value * 1e-3))
    a.destroy(); b.destroy(); out.destroy()
    return best_f, best_b


_STEM = re.compile(r"^(?P<kind>tier1|[a-z_]+?)_(?P<n>\d+)(?P<rest>.*)$")


def model(label, grid, n_survivors=None):
    """(flops, min_bytes, max_bytes) of one launch, from its stem and grid."""
    m = _STEM.match(label)
    if not m:
        return None
    kind, n, rest = m["kind"], int(m["n"]), m["rest"]
    fft = 5 * n * math.log2(n)
    ppg = int(re.search(r"p(\d)", rest).group(1)) if re.search(r"c16p\d", rest) else 1
    tile = int(re.search(r"t(\d)", rest).group(1)) if re.search(r"t\d", rest) else 1
    if kind == "tierb" and "c16" in rest:              # coarse gate, fp16, one bin
        pairs = grid * ppg * tile
        return pairs * (fft + 9 * n), pairs * 8 + grid * n * 4, pairs * n * 8
    if kind == "tierb":                                # flat filter: peak per bin
        pairs = grid
        return pairs * (fft + 9 * n), pairs * 8, pairs * n * 16
    if kind in ("refine", "tier1"):                    # listed refine over survivors
        pairs = n_survivors if n_survivors is not None else grid
        return pairs * (fft + 9 * n), pairs * 16, pairs * n * 16
    if kind == "forward":
        return grid * (fft + 2 * n), grid * n * 16, grid * n * 16
    if kind == "full_series" or kind == "full":
        return grid * (fft + 6 * n), grid * n * 8, grid * n * 24
    if kind == "compact":
        return grid * 256, grid * 256 * 8, grid * 256 * 12
    if kind == "pack_coarse":
        return 0, grid * 256 * 12, grid * 256 * 16
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank")
    ap.add_argument("--device", default="gpu:0")
    ap.add_argument("--segments", type=int, default=2)
    ap.add_argument("--json")
    ap.add_argument("--build-ceilings", action="store_true")
    a = ap.parse_args()
    if a.build_ceilings:
        return build_ceilings()
    os.environ["MF_GPU_TIMING"] = "1"
    import numpy as np
    import ladder
    import matchedfilter as mf
    from matchedfilter import _cudacompute as cc, _gputime

    launches = defaultdict(list)       # label -> [[grid, threads, survivors, function]]
    last = {}                          # "refine"/"tier1" -> the most recent such launch record
    orig_launch = cc.Context._launch

    def launch(self, hfunc, grid, block, params, shared_mem=0, stream=None, label=None):
        lab = label or self._labels.get(hfunc.value, "kernel")
        rec = [grid if not isinstance(grid, tuple) else grid[0],
               block if not isinstance(block, tuple) else block[0], None, hfunc.value]
        launches[lab].append(rec)
        for kind in ("refine", "tier1"):
            if lab.startswith(kind + "_"):
                last[kind] = rec
        return orig_launch(self, hfunc, grid, block, params, shared_mem, stream, label)
    cc.Context._launch = launch
    orig_hier = cc.Context.hier_peaks

    def hier(self, n, band, *args, **kw):
        last.clear()
        res = orig_hier(self, n, band, *args, **kw)
        # The readback has run: the counts belong to this call's refine launches.
        if "refine" in last:
            last["refine"][2] = self.last_refinements
        if "tier1" in last:
            last["tier1"][2] = self.last_tier1_survivors
        return res
    cc.Context.hier_peaks = hier

    class Args:
        pass
    args = Args()
    for k, v in dict(seg_samples=1 << 20, start_pad=120.0, end_pad=16.0, pad=4096, threshold=6.0,
                     fd=1e-3, peak_window=1.0, asym_threshold=6.0, asym_bin_width=0.03,
                     asym_num_bins=1000, segments=a.segments, resident=True, fft_length=0).items():
        setattr(args, k, v)
    tops = ladder.load_tops(a.bank, 1)
    _gputime.collect()                                   # drop setup timings
    t0 = time.perf_counter()
    report, _ = ladder.run_device(a.device, tops, args, 1)
    wall = time.perf_counter() - t0
    # Steady segments only (the ladder's own split): {label: [calls, ms]} summed over stages.
    steady = defaultdict(lambda: [0, 0.0])
    for stage, d in report.get("steady_device_ms", {}).items():
        for lab, (calls, ms) in d.items():
            steady[lab][0] += calls
            steady[lab][1] += ms
    ctx = next(iter(_gputime._CONTEXTS))
    fma, bw = ceilings(ctx)
    smem_attr = ctypes.c_int()
    ctx.cuda.cuDeviceGetAttribute(ctypes.byref(smem_attr), 39, ctx.device.value)   # max threads/SM
    max_threads = smem_attr.value or 1536
    rows = []
    for lab, (calls, ms) in sorted(steady.items(), key=lambda kv: -kv[1][1]):
        recs = launches.get(lab, [])
        total = ms * 1e-3
        info = {}
        if recs:
            fn = ctypes.c_void_p(recs[0][3])
            for name, attr in (("regs", 4), ("smem", 1), ("local", 3)):
                v = ctypes.c_int()
                ctx.cuda.cuFuncGetAttribute(ctypes.byref(v), attr, fn)
                info[name] = v.value
            bps = ctx._blocks_per_sm(fn, recs[0][1])
            info["occupancy"] = min(1.0, bps * recs[0][1] / max_threads)
            info["threads"] = recs[0][1]
        # Work per launch averaged over every recorded launch (all segments share the
        # shapes), scaled to the steady launch count.
        mods = [model(lab, g, sv) for g, _, sv, _ in recs]
        mods = [m for m in mods if m]
        row = dict(label=lab, launches=calls, device_s=total,
                   per_launch_us=total / max(calls, 1) * 1e6,
                   mean_grid=(sum(r[0] for r in recs) / len(recs)) if recs else None, **info)
        if mods and total > 0:
            flops = sum(m[0] for m in mods) / len(mods) * calls
            bmin = sum(m[1] for m in mods) / len(mods) * calls
            bmax = sum(m[2] for m in mods) / len(mods) * calls
            row.update(gflops=flops / total / 1e9, flop_frac=flops / total / fma,
                       gbs_min=bmin / total / 1e9, gbs_max=bmax / total / 1e9,
                       bw_frac_min=bmin / total / bw, bw_frac_max=bmax / total / bw,
                       intensity_min=flops / max(bmax, 1), intensity_max=flops / max(bmin, 1))
            surv = [r[2] for r in recs if r[2] is not None]
            if surv:
                row["mean_survivors"] = sum(surv) / len(surv)
        rows.append(row)
    out = dict(device=ctx.name, sm=ctx.sm_count, cc=ctx.cc, fma_tflops=fma / 1e12, stream_gbs=bw / 1e9,
               wall_s=wall, steady_s=report["steady_s"], tirt=report.get("templates_in_real_time"),
               kernels=rows)
    print("%s: %d SMs sm_%d%d; measured fp32 FMA %.1f TFLOPS, stream %.0f GB/s"
          % (ctx.name, ctx.sm_count, ctx.cc[0], ctx.cc[1], fma / 1e12, bw / 1e9))
    print("steady (2 ifos x %d segments): %s" % (a.segments - 1,
          ", ".join("%s %.3fs" % kv for kv in report["steady_s"].items())))
    hdr = "%-24s %6s %9s %8s %9s %7s %8s %7s %5s %6s %6s %5s" % (
        "kernel", "calls", "device_ms", "us/call", "grid", "TFLOPS", "%fp32", "GB/s", "%bw",
        "regs", "smem", "occ")
    print(hdr)
    for r in rows:
        print("%-24s %6d %9.2f %8.1f %9s %7s %8s %7s %5s %6s %6s %5s" % (
            r["label"][:24], r["launches"], r["device_s"] * 1e3, r["per_launch_us"],
            "%.0f" % r["mean_grid"] if r.get("mean_grid") else "-",
            "%.2f" % (r["gflops"] / 1e3) if "gflops" in r else "-",
            "%.1f" % (100 * r["flop_frac"]) if "flop_frac" in r else "-",
            "%.0f-%.0f" % (r["gbs_min"], r["gbs_max"]) if "gbs_min" in r else "-",
            "%.0f" % (100 * r["bw_frac_min"]) if "bw_frac_min" in r else "-",
            r.get("regs", "-"), r.get("smem", "-"),
            "%.2f" % r["occupancy"] if "occupancy" in r else "-"))
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
