#!/usr/bin/env python3
"""Compile Slang shaders to PTX for the native CUDA Driver backend.

Generates PTX blobs in python/matchedfilter/ptx/ alongside spirv/ and metal/.
"""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "python" / "matchedfilter" / "ptx"

KERNEL = ROOT / "src" / "gpu" / "tierb.slang"
COARSE_KERNEL = ROOT / "src" / "gpu" / "coarse_tile.slang"
PACK_KERNEL = ROOT / "src" / "gpu" / "pack_coarse.slang"
SERIES_KERNEL = ROOT / "src" / "gpu" / "series_forward.slang"
# CUDA's refine: a grid-stride entry reading the survivor count on the device
# (no indirect dispatch on CUDA). Appended to tierb.slang, as series_forward is.
REFINE_KERNEL = ROOT / "src" / "gpu" / "refine_bounded.slang"


def kernel_text():
    """tierb.slang as every target builds it (MF_CUDA selects its CUDA choices, MF_UNROLL)."""
    return KERNEL.read_text()
def _coarse_prelude(n, cap, ppg, table=True):
    """The packed coarse kernel's build-time inputs, exactly as the SPIR-V build makes them
    (build_spirv.coarse_prelude): the fp16 error bound's C16_KAPPA, the bank-conflict-free
    exchange layout and the fp16 twiddle table. Without it the CUDA coarse tier reported
    B = |c16|(1+3u) with no rounding term (C16_KAPPA defaulting to 0).

    table=False leaves out the fp16 twiddle table (the kernel then runs the twiddle
    recurrence). Both are built, the table variant with a "w" suffix, and the measured
    coarse choice (_cudacompute._coarse_kernel) picks: on the L40S the table cost band 1024's
    tiled build ~40% and band 512's ~10%, and was even at 64-256."""
    import sys as _sys
    _sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import build_spirv
    text = build_spirv.coarse_prelude(n, cap, ppg)
    if not table:
        text = text[:text.index("static const uint COARSE_TWT_DATA")]
    return text


COARSE_TC_KERNEL = ROOT / "src" / "gpu" / "coarse_tc.cu"
#: Tensor-core coarse gate builds: bands (B = 16 M, M a multiple of 16) and warps per block.
COARSE_TC_BANDS = (256, 512)
COARSE_TC_WPB = (2, 4)
#: The tensor-core coarse transform's error at the elected lag, in u rms(y) units, measured
#: on the L40S with the bound off (tools/cuda_tc_sigma.py: 8192 pairs per band over the
#: gate_margin families; |error| mean 0.76 / 0.71, std 0.40 / 0.39, max 3.31 / 5.19 at bands
#: 256 / 512). The error magnitude is not Gaussian (its tail is heavier than a Rayleigh fit),
#: so sigma is not its std: it is set so that kappa = z(C16_FAIL) sigma is at least twice the
#: largest error seen, the margin-use < 0.5 criterion of tools/gate_margin.py, rounded up to
#: 0.1: kappa 7.0 / 10.5. Smaller than the Slang tier's (12.7 / 15.5 from C16_SIGMA): the
#: tensor-core products accumulate in fp32.
COARSE_TC_SIGMA = {256: 1.0, 512: 1.5}


def nvrtc_ptx(nvrtc, cuda_path, source, name, defines, arch="compute_80"):
    """CUDA C -> PTX through NVRTC (the library slangc uses). compute_80: mma.sync m16n8k16."""
    import ctypes
    lib = ctypes.CDLL(str(nvrtc))
    prog = ctypes.c_void_p()
    if lib.nvrtcCreateProgram(ctypes.byref(prog), source.encode(), name.encode(), 0, None, None):
        raise RuntimeError("nvrtcCreateProgram failed")
    opts = [("--gpu-architecture=%s" % arch).encode(), b"-std=c++14"]
    if cuda_path:
        opts.append(("-I" + str(pathlib.Path(cuda_path) / "include")).encode())
    opts += [("-D%s=%s" % kv).encode() for kv in defines.items()]
    arr = (ctypes.c_char_p * len(opts))(*opts)
    rc = lib.nvrtcCompileProgram(prog, len(opts), arr)
    size = ctypes.c_size_t()
    lib.nvrtcGetProgramLogSize(prog, ctypes.byref(size))
    log = ctypes.create_string_buffer(size.value)
    lib.nvrtcGetProgramLog(prog, log)
    if rc:
        raise RuntimeError("nvrtc %s %s:\n%s" % (name, defines, log.value.decode()))
    lib.nvrtcGetPTXSize(prog, ctypes.byref(size))
    ptx = ctypes.create_string_buffer(size.value)
    lib.nvrtcGetPTX(prog, ptx)
    return ptx.value


def build_coarse_tc(nvrtc, outdir):
    """The tensor-core coarse gate (src/gpu/coarse_tc.cu): one PTX per band and warps per
    block, timed by the backend against the Slang coarse variants."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from statistics import NormalDist
    import coarse_layout
    z = NormalDist().inv_cdf(1.0 - coarse_layout.C16_FAIL)
    cuda_path = os.environ.get("MF_CUDA_PATH")
    src = COARSE_TC_KERNEL.read_text()
    for band in COARSE_TC_BANDS:
        for wpb in COARSE_TC_WPB:
            out = outdir / ("coarse_tc_%d_w%d.ptx" % (band, wpb))
            kappa = os.environ.get("MF_TC_KAPPA") or "%.4ff" % (z * COARSE_TC_SIGMA[band])
            out.write_bytes(nvrtc_ptx(nvrtc, cuda_path, src, "coarse_tc.cu",
                                      dict(BAND=band, WPB=wpb, KAPPA=kappa)))
            print("  coarse_tc band=%d wpb=%d kappa=%s" % (band, wpb, kappa), flush=True)


COMPACT_PEAKS_KERNEL = ROOT / "src" / "gpu" / "compact_peaks.slang"

TIER_B = (64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536)
RADIX = {32768: 32, 65536: 64}

PORTABLE_CAP = 4096  # complex = 32 KB
LDS_CAP = {
    64: 512, 128: 512, 256: 512, 512: 512,
    1024: 512, 2048: 1024, 4096: 2048, 8192: 8192, 16384: 8192,
    32768: 8192, 65536: 8192,
}

COARSE_BANDS = {256: 16, 512: 16, 1024: 16}
COARSE_TILE_T = {128: 2, 256: 2, 512: 4, 1024: 2}

STEMS = {
    "fusedTierB": "tierb",
    "compactPairs": "compact",
    "refineListed": "refine",
    "fullCorrelation": "full",
    "fullCorrelationSeries": "full_series",
}

ENTRY = "fusedTierB"
ENTRIES = ("fusedTierB", "compactPairs", "refineListed")


def lds_bytes(n, cap):
    r = RADIX.get(n, 16)
    wg = n // r
    ch = min(max(cap // wg, 1), r)
    return ch * wg * 8


def find_slangc(explicit=None):
    candidates = [
        explicit,
        os.environ.get("MF_SLANGC"),
        str(ROOT / "third_party" / "slang" / "bin" / "slangc"),
    ]
    for c in candidates:
        if c and pathlib.Path(c).is_file():
            return str(c)
    return None


def find_nvrtc():
    candidates = [
        os.environ.get("MF_NVRTC"),
        "/home/ahnitz/miniconda3/lib/python3.13/site-packages/nvidia/cuda_nvrtc/lib/libnvrtc.so.12",
        "/usr/lib/x86_64-linux-gnu/libnvrtc.so",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return str(c)
    return None


def find_cuda_path():
    candidates = [
        os.environ.get("MF_CUDA_PATH"),
        "/home/ahnitz/miniconda3/lib/python3.13/site-packages/nvidia/cuda_runtime",
        "/usr/local/cuda",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return str(c)
    return None


def compile_ptx(slangc, nvrtc, env, src_text, out_path, entry, extra_flags=()):
    src_file = out_path.with_suffix(".temp.slang")
    src_file.write_text(src_text)
    cmd = [
        slangc, str(src_file), "-I", str(KERNEL.parent),
        "-target", "ptx", "-entry", entry, "-stage", "compute", "-O3",
        "-DSLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT=1", "-DMF_CUDA=1",
    ]
    if nvrtc:
        cmd.extend(["-nvrtc-path", str(nvrtc)])
    cmd.extend(extra_flags)
    cmd.extend(["-o", str(out_path)])
    
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    src_file.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise RuntimeError("slangc failed for %s (%s):\n%s" % (out_path.name, entry, proc.stderr))
    return out_path


def compile_tierb(slangc, nvrtc, env, n, outdir, entry=ENTRY, cap=None, suffix="", coarse16=0, ppg=1, tile=1, single_bin=0, table=None):
    if coarse16 and table is None:
        compile_tierb(slangc, nvrtc, env, n, outdir, entry, cap, suffix + "w", coarse16, ppg,
                      tile, single_bin, table=True)
        table = False
    cap = LDS_CAP[n] if cap is None else cap
    r = RADIX.get(n, 16)
    wg = (n // r) * ppg if entry in ("fusedTierB", "refineListed") else (n // r)
    extra_flags = ["-Xnvrtc", "-maxrregcount=64"] if wg >= 1024 else []
    text = (
        "#define NLEN %d\n#define LDS_CAP %d\n#define COARSE16 %d\n"
        "#define PPG %d\n#define TILE_T %d\n#define RADIX %d\n#define SINGLE_BIN %d\n"
        "#define SLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT 1\n"
        "#define TARGET_CUDA 1\n"
        % (n, cap, coarse16, ppg, tile, r, single_bin)
        + (_coarse_prelude(n, cap, ppg, table=bool(table)) if coarse16 else "")
        + kernel_text()
    )
    name = "%s_%d%s.ptx" % (STEMS[entry], n, suffix)
    ptx = outdir / name
    if entry == "refineListed":
        text += "\n" + REFINE_KERNEL.read_text()
        entry = "refineListedBounded"
    return compile_ptx(slangc, nvrtc, env, text, ptx, entry, extra_flags=extra_flags)


FULL_TIER_C = tuple(1 << k for k in range(17, 23))
TIER_C_ENTRIES = (("corr1", "tcStage1"), ("corr2", "tcFullStage3"),
                  ("corr_series2", "tcFullSeriesStage3"),
                  ("fwd1", "tcForwardStage1"), ("fwd2", "tcForwardStage3"))


def tierc_split(n):
    """The same n = n1 * n2 split build_spirv.py uses (n2 the largest power of two
    with 2*n2^2 <= n), so every backend runs the same decomposition."""
    n2 = 1
    while n2 * n2 * 2 <= n:
        n2 *= 2
    return n // n2, n2


def build_compact_peaks(slangc, nvrtc, env, outdir):
    """The sparse peak readback kernel (CUDA only)."""
    text = "#define SLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT 1\n" + COMPACT_PEAKS_KERNEL.read_text()
    return compile_ptx(slangc, nvrtc, env, text, outdir / "compact_peaks.ptx", "compactPeaks")


def build_full_tierc(slangc, nvrtc, env, outdir):
    """Two-stage (Tier C) correlation and series-forward kernels past 65536."""
    entries = {}
    for n in FULL_TIER_C:
        n1, n2 = tierc_split(n)
        info = {"n1": n1, "n2": n2}
        for role, entry in TIER_C_ENTRIES:
            sub = n2 if role.endswith("1") else n1
            r = RADIX.get(sub, 16)
            text = (
                "#define NLEN %d\n#define TC_N %d\n#define LDS_CAP %d\n#define RADIX %d\n"
                "#define SLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT 1\n#define TARGET_CUDA 1\n"
                % (sub, n, min(LDS_CAP[sub], PORTABLE_CAP), r)
                + kernel_text()
            )
            ptx = outdir / ("tc_%s_%d.ptx" % (role, n))
            extra = ["-Xnvrtc", "-maxrregcount=64"] if sub // r >= 1024 else []
            compile_ptx(slangc, nvrtc, env, text, ptx, entry, extra_flags=extra)
            info[role] = dict(file=ptx.name, local_size=[sub // r, 1, 1])
        entries[str(n)] = info
        print("  full Tier C n=%d split=%dx%d" % (n, n1, n2), flush=True)
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slangc", default=None)
    ap.add_argument("--only", choices=("all", "tierc", "refine", "coarse", "compact", "tc"), default="all",
                    help="rebuild only the two-stage kernels (and their manifest entry), "
                         "or only the refine family")
    args = ap.parse_args()

    slangc = find_slangc(args.slangc)
    if not slangc:
        print("slangc not found", file=sys.stderr)
        return 1

    nvrtc = find_nvrtc()
    cuda_path = find_cuda_path()
    env = dict(os.environ)
    if cuda_path:
        env["CUDA_PATH"] = cuda_path

    OUT.mkdir(parents=True, exist_ok=True)
    if args.only == "tierc":
        manifest = json.loads((OUT / "manifest.json").read_text())
        manifest["full_tierc"] = build_full_tierc(slangc, nvrtc, env, OUT)
        (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        return 0
    if args.only == "compact":
        build_compact_peaks(slangc, nvrtc, env, OUT)
        return 0
    if args.only == "tc":
        build_coarse_tc(nvrtc, OUT)
        return 0
    if args.only == "coarse":
        for n in (64, 128, 256):
            for _p in (8, 16):
                compile_tierb(slangc, nvrtc, env, n, OUT, entry="fusedTierB", suffix="_c16p%d" % _p,
                              coarse16=1, ppg=_p)
            _t = COARSE_TILE_T.get(n, 1)
            if _t > 1:
                compile_tierb(slangc, nvrtc, env, n, OUT, entry="fusedTierB", coarse16=1, ppg=8,
                              tile=_t, suffix="_c16p8t%d" % _t)
            print("  coarse n=%d" % n, flush=True)
        return 0
    if args.only == "refine":
        for n in TIER_B:
            compile_tierb(slangc, nvrtc, env, n, OUT, "refineListed")
            if lds_bytes(n, LDS_CAP[n]) > lds_bytes(n, PORTABLE_CAP):
                compile_tierb(slangc, nvrtc, env, n, OUT, "refineListed",
                              cap=PORTABLE_CAP, suffix="_lds32")
            if n >= 4096:
                compile_tierb(slangc, nvrtc, env, n, OUT, "refineListed",
                              suffix="_onebin", single_bin=1)
                if lds_bytes(n, LDS_CAP[n]) > lds_bytes(n, PORTABLE_CAP):
                    compile_tierb(slangc, nvrtc, env, n, OUT, "refineListed", cap=PORTABLE_CAP,
                                  suffix="_onebin_lds32", single_bin=1)
            print("  refine n=%d" % n, flush=True)
        return 0
    manifest = dict(entry=ENTRY, kernel=KERNEL.name, modules={})

    # 1. Coarse tile kernels
    for band, rpt in COARSE_BANDS.items():
        src_text = "#define NBAND %d\n#define RPT %d\n#define SLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT 1\n" % (band, rpt) + COARSE_KERNEL.read_text()
        ptx = OUT / ("coarse_%d.ptx" % band)
        compile_ptx(slangc, nvrtc, env, src_text, ptx, "coarseTile")
        print("  coarse band=%-4d %-16s %5d bytes" % (band, ptx.name, ptx.stat().st_size))

    # 2. Pack coarse
    pack_ptx = OUT / "pack_coarse.ptx"
    pack_text = "#define SLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT 1\n" + PACK_KERNEL.read_text()
    compile_ptx(slangc, nvrtc, env, pack_text, pack_ptx, "packCoarse")
    print("  pack_coarse %5d bytes" % pack_ptx.stat().st_size)

    # 3. Compact pairs (single kernel for n=64)
    comp_ptx = OUT / "compact.ptx"
    compile_tierb(slangc, nvrtc, env, 64, OUT, "compactPairs")
    (OUT / "compact_64.ptx").replace(comp_ptx)

    # 4. Loop over lengths
    for n in TIER_B:
        info = {}
        ptx = compile_tierb(slangc, nvrtc, env, n, OUT)
        info["file"] = ptx.name
        info["bytes"] = ptx.stat().st_size
        r = RADIX.get(n, 16)
        wg = n // r
        info["local_size"] = [wg, 1, 1]

        if lds_bytes(n, LDS_CAP[n]) > lds_bytes(n, PORTABLE_CAP):
            small = compile_tierb(slangc, nvrtc, env, n, OUT, cap=PORTABLE_CAP, suffix="_lds32")
            info["portable"] = dict(file=small.name, lds_bytes=lds_bytes(n, PORTABLE_CAP))

        if n >= 1024:
            full = compile_tierb(slangc, nvrtc, env, n, OUT, "fullCorrelation")
            full_series = compile_tierb(slangc, nvrtc, env, n, OUT, "fullCorrelationSeries")
            info["full"] = dict(file=full.name)
            info["full_series"] = dict(file=full_series.name)
            if lds_bytes(n, LDS_CAP[n]) > lds_bytes(n, PORTABLE_CAP):
                portable = compile_tierb(slangc, nvrtc, env, n, OUT, "fullCorrelation",
                                         cap=PORTABLE_CAP, suffix="_lds32")
                portable_series = compile_tierb(slangc, nvrtc, env, n, OUT, "fullCorrelationSeries",
                                                cap=PORTABLE_CAP, suffix="_lds32")
                info["full"]["portable"] = dict(file=portable.name)
                info["full_series"]["portable"] = dict(file=portable_series.name)

        ref = compile_tierb(slangc, nvrtc, env, n, OUT, "refineListed")
        info["refine"] = dict(file=ref.name)
        if lds_bytes(n, LDS_CAP[n]) > lds_bytes(n, PORTABLE_CAP):
            rsmall = compile_tierb(slangc, nvrtc, env, n, OUT, "refineListed",
                                   cap=PORTABLE_CAP, suffix="_lds32")
            info["refine"]["portable"] = dict(file=rsmall.name, lds_bytes=lds_bytes(n, PORTABLE_CAP))

        if n >= 4096:
            for entry, target in (("fusedTierB", info), ("refineListed", info["refine"])):
                one = compile_tierb(slangc, nvrtc, env, n, OUT, entry, suffix="_onebin", single_bin=1)
                target["one_bin"] = dict(file=one.name)
                if lds_bytes(n, LDS_CAP[n]) > lds_bytes(n, PORTABLE_CAP):
                    small = compile_tierb(slangc, nvrtc, env, n, OUT, entry, cap=PORTABLE_CAP,
                                          suffix="_onebin_lds32", single_bin=1)
                    target["one_bin"]["portable"] = dict(file=small.name)

        # Coarse fp16 variants
        for centry in (("fusedTierB",) if RADIX.get(n, 16) == 16 else ()):
            compile_tierb(slangc, nvrtc, env, n, OUT, entry=centry, suffix="_c16", coarse16=1)
            # p8/p16 fill a 32/64-thread block at the small bands (WG = n/16 is 4 at
            # band 64); the CUDA host picks the variant with the best occupancy.
            for _p in (2, 4) + ((8, 16) if n <= 256 else ()):
                compile_tierb(slangc, nvrtc, env, n, OUT, entry=centry, suffix="_c16p%d" % _p, coarse16=1, ppg=_p)
            _t = COARSE_TILE_T.get(n, 1)
            if _t > 1:
                for _p in (1, 2, 4) + ((8,) if n <= 256 else ()):
                    compile_tierb(slangc, nvrtc, env, n, OUT, entry=centry, coarse16=1,
                                  ppg=_p, tile=_t,
                                  suffix="_c16%st%d" % ("p%d" % _p if _p > 1 else "", _t))

        # Forward transforms
        cap = min(LDS_CAP[n], PORTABLE_CAP)
        fwd_text = (
            f"#define NLEN {n}\n#define RADIX {r}\n#define LDS_CAP {cap}\n"
            f"#define SLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT 1\n"
            + kernel_text() + "\n" + SERIES_KERNEL.read_text()
        )
        fwd_ptx = OUT / f"forward_{n}.ptx"
        extra = ["-Xnvrtc", "-maxrregcount=64"] if wg >= 1024 else []
        compile_ptx(slangc, nvrtc, env, fwd_text, fwd_ptx, "seriesForward", extra_flags=extra)

        manifest["modules"][str(n)] = info
        print("  n=%-6d %-16s %5d bytes  wg=%-4d" % (n, ptx.name, info["bytes"], wg))

    manifest["full_tierc"] = build_full_tierc(slangc, nvrtc, env, OUT)
    build_compact_peaks(slangc, nvrtc, env, OUT)
    build_coarse_tc(nvrtc, OUT)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Wrote PTX manifest: %s" % (OUT / "manifest.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
