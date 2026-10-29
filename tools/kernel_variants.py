#!/usr/bin/env python3
"""The GPU kernel variants: one table of every artifact the build makes for Vulkan (SPIR-V),
Metal (MSL) and CUDA (PTX), the facts each one is built with, and the one way each is
compiled.

Ahead-of-time, at build time, for two reasons. The wheel must carry every backend with no
user choice of wheel and no extra package to install, so the kernels cannot be compiled on
the user's machine -- that would put the Slang toolchain on their critical path. And
compiling once in CI means the shipped blob is the artefact that was tested, rather than
whatever a user's driver happens to produce. slangc is a BUILD dependency only: nothing at
runtime imports slangpy or touches Slang.

Every build writes one manifest (manifest.json, the same schema for every backend) beside
its artifacts: spirv/, metal/ and ptx/. The host reads kernel facts -- which lengths and
layouts were built, workgroup sizes, staging bytes, the two-stage split -- from it and
restates none of them (matchedfilter._kernels).

    python tools/kernel_variants.py build [--backend vulkan,metal,cuda] [--only GLOB]
                                          [--jobs N] [--slangc PATH]
    python tools/kernel_variants.py list [--backend B]   the artifacts a build makes
    python tools/kernel_variants.py check                shipped files and manifests are
                                                         exactly what a build makes

tools/build_spirv.py (Vulkan and Metal) and tools/build_ptx.py (CUDA) are this module's
build for those backends. `list` and `check` need no compiler.
"""
import argparse
import fnmatch
import hashlib
import json
import os
import pathlib
import re
import runpy
import shutil
import struct
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PACKAGE = ROOT / "python" / "matchedfilter"
GPU_SRC = ROOT / "src" / "gpu"
KERNEL = GPU_SRC / "tierb.slang"
#: refine_bounded.slang: refineListedBounded (the listed refine on every target) and
#: refineItems (the follow-up refine over listed entries), appended to tierb.slang.
ITEMS_KERNEL = GPU_SRC / "refine_bounded.slang"

#: Each backend's artifact folder in the package, the slangc target, and the artifact suffix.
BACKENDS = {"vulkan": ("spirv", "spirv", ".spv"),
            "metal": ("metal", "metal", ".metal"),
            "cuda": ("ptx", "ptx", ".ptx")}
MANIFEST_SCHEMA = 2

#: The slangc every checked-in kernel (spirv/, ptx/, metal/) is built with. A different
#: version emits different code (register numbering, scheduling), so a rebuild of unchanged
#: source would not reproduce the shipped kernels and an identical-codegen proof would be
#: meaningless. Official release shader-slang v2026.18.2,
#: slang-2026.18.2-linux-x86_64.tar.gz, sha256
#: 8a097d4365e1cab10265d0b0d77b461b5d30576f99ddc0521a35723c34cad816 (docs/gpu-handover.md).
#: MF_SLANGC_ANY_VERSION=1 builds with another version anyway (for experiments only).
SLANGC_VERSION = "2026.18.2"

# ---- the facts ---------------------------------------------------------------------------

#: One-stage transform lengths: one source specialised by NLEN rather than a blob per
#: hand-written kernel. The host's GPU sizes are these and FULL_TIER_C, read from the
#: manifest (matchedfilter._kernels.sizes). The short lengths are not transform sizes a
#: caller asks for first -- they are COARSE bands. The hierarchical mode's first pass is the
#: ordinary filter at length `band`, so the same kernel has to exist there. The decomposition
#: generalises down without change: at 512 the workgroup is 32 threads, two exchange levels
#: and an innermost radix of 2.
TIER_B = (64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536)

#: Points per thread, which is also the decomposition radix: 16 unless listed. A workgroup
#: is capped at MAX_INVOCATIONS threads and n = WG * R, so 16 points per thread stops at
#: 16384; 32 and 64 are what reach the next two lengths.
#:
#: 131072 would need R=128, or 256 VGPRs of transform state per thread before any working
#: set -- past what the register file will hold, and the point where the four-step has to
#: be split across dispatches instead. That is a second kernel (FULL_TIER_C), not a wider R.
RADIX = {32768: 32, 65536: 64}

#: The most threads a workgroup of any build has: Vulkan guarantees at least 128 and CUDA
#: allows at most 1024 per block, and every target this library runs on allows 1024. No
#: variant is built past it (a module past it cannot launch on CUDA).
MAX_INVOCATIONS = 1024

#: Exchange staging per transform length, in COMPLEX values, measured rather than modelled.
#: The exchange runs R/CH chunks with CH = CAP/WG and each chunk costs two barriers, so too
#: little staging is barrier-bound -- but staging is LDS, and LDS is what caps how many
#: workgroups a CU holds, so too much costs occupancy. The optimum is two chunks almost
#: everywhere.
#:
#: Measured on a Radeon 8060S at threshold 5.5, compute only, against one AVX-512 core
#: (speedup at the chosen value in brackets):
#:
#:     n       4 KB   8 KB  16 KB  32 KB  64 KB
#:     1024    0.81   0.84   0.87   0.84   0.90    -> 4 KB  [60.9x]
#:     2048    1.09   0.93   1.13   1.12   1.19    -> 8 KB  [57.1x]
#:     4096    1.68   1.27   1.13   1.38   1.35    -> 16 KB [44.2x]
#:     8192    8.15   5.16   2.49   2.03   1.83    -> 64 KB [29.2x]
#:     16384  15.92  15.91  12.78   7.56   6.35    -> 64 KB [16.5x]
#:
#: These are THIS device's numbers; Metal has its own column (METAL_CAP).
#: The two widest lengths inherit 16384's staging: CH = CAP/WG = 8 either way, so the
#: exchange runs the same two-barrier chunks against a wider register file. Not measured as
#: an optimum -- it is the value that makes them work, and tuning them wants a quiet machine.
LDS_CAP = {
    64: 512, 128: 512, 256: 512, 512: 512,
    1024: 512, 2048: 1024, 4096: 2048, 8192: 8192, 16384: 8192,
    32768: 8192, 65536: 8192,
}

#: The largest staging that is portable. Apple allows a threadgroup 32 KB, and several of
#: the fastest entries above exceed it -- so every size whose preferred staging does not fit
#: is ALSO emitted at this cap (the "_lds32" builds), and the runtime picks by what the
#: device reports.
#:
#: A software rasteriser will not catch this: llvmpipe reports 32 KB and then runs a 64 KB
#: kernel anyway, so the lavapipe CI path passes where real hardware would fail to create
#: the pipeline.
PORTABLE_CAP = 4096          # complex, = 32 KB

#: Metal's own column. The exchange runs R/CH chunks with CH = CAP/WG, and each chunk costs
#: two barriers plus a full R-iteration reader pass of which only CH iterations can land --
#: so CH = 16 means one chunk, half the barriers, and no wasted address arithmetic. Apple
#: takes that trade and the Radeon does not: the same widening measured, us/pair at 4096
#: pairs,
#:
#:              Apple M2            Radeon 8060S
#:     n=1024   0.263 -> 0.228      0.0484 -> 0.0555
#:     n=2048   0.599 -> 0.508      0.0499 -> 0.0513
#:     n=4096   1.480 -> 0.736      0.0866 -> 0.1131
#:
#: a 2.01x win at n=4096 on Apple against a 31% loss on the Radeon, which is why this is a
#: separate table and not an edit to the one above. Apple has far less threadgroup memory
#: per core, so a second resident workgroup buys it less than the barriers cost; the Radeon
#: has enough to keep several in flight and would rather have them.
#:
#: Sizes absent here fall back to LDS_CAP. n=4096 at CAP 4096 lands on exactly 32 KB, which
#: is precisely Apple's per-threadgroup limit, so it needs no portable variant.
METAL_CAP = {1024: 1024, 2048: 2048, 4096: 4096}
#: Shared SINGLE_BIN specialization, measured on M2 for flat and refinement. Smaller staging
#: increased barriers and lost; 8192 must fit Apple's 32 KiB.
METAL_SINGLE_BIN_CAP = {256: 512, 512: 512, 1024: 1024, 2048: 2048, 4096: 4096, 8192: 4096}

#: Templates per pair slot built for the COARSE path, at every band and packing. The tile
#: holds the thread's data slice in registers and reuses it across TILE_T templates, so
#: loads per pair fall as 1/TILE_T -- but the registers come out of occupancy, and whether
#: that is affordable depends on the band AND the device. A per-band table tuned on RDNA
#: (2 everywhere, 4 at 512) was 11% slow in the fine stage on GCN at band 256 and 4% slow
#: on the RDNA part itself; band 1024 measured 2.1x worse tiled there. So every tile is
#: built and the host times the shipped builds on its device (_gpuhier._time_coarse_layouts,
#: over each backend's _x_coarse_candidates, which read the built layouts from the manifest).
COARSE_TILES = (2, 4, 8)
#: Tiled builds stop here: these are the bands tiles always shipped at. Above it a tiled pair
#: spans several subgroups on every device, and the CUDA builds alone would add ~48 MB.
MAX_TILED_BAND = 1024

#: Pairs per workgroup of the untiled fp16 coarse builds, per target. A coarse transform of
#: length B runs on B/16 threads -- 4 at band 64 -- so one pair per group leaves most of a
#: subgroup idle at the small bands, and packing pairs fills it; the host chooses among what
#: is built (each backend's _x_coarse_candidates, by measurement).
#:   Vulkan: 2 and 4 at every band whose group stays within MAX_INVOCATIONS; 8 and 16 where
#:     a group of them is at most 128 threads (two wave64s). That is the set committed since
#:     aae09340 (2026-10-08); its script also built 8 and 16 up to 1024 threads -- six
#:     modules at bands 256-2048 that were never committed, so no host could offer them.
#:   Metal: METAL_C16_PPG, up to METAL_C16_MAX_THREADS threads per group (an Apple GPU runs
#:     32-wide SIMD groups).
#:   CUDA: 2 and 4 everywhere, 8 and 16 at bands up to 256 (filling a 32- or 64-thread block,
#:     where WG = n/16 is 4 at band 64); a module past 48 KB of static shared memory or
#:     MAX_INVOCATIONS threads is not built (STATIC_SHARED_MAX).
VK_C16_PPG = (2, 4, 8, 16)
VK_C16_WIDE_PPG_THREADS = 128
METAL_C16_PPG = (2, 4, 8, 16, 32)
METAL_C16_MAX_THREADS = 256


def vk_c16_ppgs(n):
    """The untiled coarse packings the Vulkan build makes at band n (VK_C16_PPG)."""
    wg = n // radix(n)
    return tuple(p for p in VK_C16_PPG
                 if wg * p <= MAX_INVOCATIONS and (p <= 4 or wg * p <= VK_C16_WIDE_PPG_THREADS))


#: Row padding of the fp32 exchange stage, in complex elements. Rows WG apart put every
#: register a thread gathers on the same few banks; two extra elements (16 B) rotate
#: consecutive rows across the 64-bit LDS accesses. Measured on the 8060S, listed one-bin
#: refine, CU-cycles/pair, pad 0 / 1 / 2 / 4 / 8:
#:     n=512    606 / 550 / 547 / 547 / 552
#:     n=1024  1105 /1078 /1041 /1024 /1020
#:     n=2048  2232 /2081 /2126 /2273 /2254
#: One rule rather than a per-length optimum. Applied only where the padded stage stays
#: within the 32 KB portable cap, so no LDS limit or portable variant moves. Vulkan only.
FP32_PAD = 2

#: CUDA allows a block at most 48 KB of STATIC shared memory, on every architecture: more must
#: be dynamic shared memory with a per-kernel opt-in (cudaFuncAttributeMaxDynamicSharedMemorySize),
#: which these kernels do not use, and the JIT rejects a module past it (CUDA_ERROR_INVALID_PTX).
#: A build past it cannot launch on any NVIDIA GPU, so it is not built; where its staging is
#: the reason, the _lds32 build of the same kernel serves (_cudacompute._shipped).
STATIC_SHARED_MAX = 48 * 1024
#: NVRTC's register cap for a 1024-thread block: 64 registers x 1024 threads fill the 64K
#: register file of every NVIDIA SM.
CUDA_WIDE_BLOCK_FLAGS = ("-Xnvrtc", "-maxrregcount=64")

#: Artifact prefix per entry point. Two entries used to be distinguished by `entry == ENTRY`,
#: which silently collides the moment there is a third.
STEMS = {"fusedTierB": "tierb", "compactPairs": "compact", "compactListed": "compactl",
         "refineListed": "refine", "refineItems": "items", "fullCorrelation": "full",
         "fullCorrelationSeries": "full_series"}

#: Two-stage (Tier C) lengths, past the one-stage kernels: n = n1 * n2 across dispatches.
FULL_TIER_C = tuple(1 << k for k in range(17, 23))
TIER_C_ENTRIES = (("corr1", "tcStage1"), ("corr2", "tcFullStage3"),
                  ("corr_series2", "tcFullSeriesStage3"),
                  ("fwd1", "tcForwardStage1"), ("fwd2", "tcForwardStage3"))

#: Every production shader source, fingerprinted in each manifest (test_kernels_ship).
SOURCES = ("tierb.slang", "fft_transform.slang", "series_forward.slang", "series_bands.slang",
           "forward_tier0.slang", "pack_coarse.slang", "twiddle.slang", "refine_bounded.slang",
           "compact_peaks.slang")


def radix(n):
    """Points per thread at one-stage length n (RADIX)."""
    return RADIX.get(n, 16)


def metal_cap(n):
    """Staging capacity for the Metal build of this length."""
    return METAL_CAP.get(n, LDS_CAP[n])


def tierc_split(n):
    """The two-stage split n = n1 * n2: n2 the largest power of two with 2 * n2^2 <= n, the
    same on every backend."""
    n2 = 1
    while n2 * n2 * 2 <= n:
        n2 *= 2
    return n // n2, n2


def lds_bytes(n, cap):
    """Staging the unpadded fp32 kernel declares at length n and staging cap (complex):
    stg[CH * WG * 2] uints with WG = n/R and CH = min(cap/WG, R) -- the kernel's own
    arithmetic (tierb.slang CH). Decides where a portable (_lds32) build is needed."""
    r = radix(n)
    wg = n // r
    ch = min(max(cap // wg, 1), r)
    return ch * wg * 8


def staging_bytes(n, cap, ppg=1, coarse16=0, xstride_f=None, xstride=None, xslot=None):
    """Bytes of tierb.slang's one groupshared array, stg[STGW * PPG] uints, as a build with
    these defines declares it. CAP = min(n, cap), CH = min(max(CAP/WG, 1), R); the fp32 stage
    is CH rows of XSTRIDE_F (default WG) complex values, the fp16 one CH rows of XSTRIDE
    (default WG) words with pairs XSLOT words apart (default CH * XSTRIDE)."""
    r = radix(n)
    wg = n // r
    ch = min(max(min(n, cap) // wg, 1), r)
    if coarse16:
        xs = xstride or wg
        stgw = max(ch * xs if xslot is None else xslot, ch * xs)
    else:
        stgw = ch * (xstride_f or wg) * 2
    return stgw * ppg * 4


def fp32_xstride(n, cap):
    """XSTRIDE_F of the Vulkan fp32 builds: WG + FP32_PAD where the padded stage stays within
    PORTABLE_CAP, else WG."""
    r = radix(n)
    wg = n // r
    ch = min(max(cap // wg, 1), r)
    return wg + FP32_PAD if ch * (wg + FP32_PAD) * 8 <= PORTABLE_CAP * 8 else wg


def metal_split(n, cap, coarse16=0):
    """Whether a Metal build stages its exchange one float per register (SPLIT_STAGE).

    Where the staging holds half a transform (cap < n <= 2 cap: n=8192 at Apple's 32 KB),
    the float2 exchange runs in two chunks; staging one component at a time runs it in one
    pass per component from the same bytes. Measured on an M2, middle-stage
    full_series_8192: 4.24 -> 3.05 ms, bit-identical output.
    """
    return int(not coarse16 and cap < n <= 2 * cap)


def _coarse_layout():
    sys.path.insert(0, str(HERE))
    import coarse_layout
    return coarse_layout


_LAYOUTS = {}


def exchange_layout(n, ppg, cap):
    """(XSTRIDE, XSLOT) of the packed fp16 coarse exchange at band n, ppg pairs per group:
    the bank-conflict-free padding under the RDNA wave64 bank model (tools/coarse_layout.py).
    Vulkan and CUDA builds; Metal keeps the default stride (on the M2 the padded exchange made
    the untiled build slower, 1.24 -> 1.46 ms, and the tiled one no faster, 1.00 -> 0.99)."""
    if (n, ppg, cap) not in _LAYOUTS:
        _LAYOUTS[(n, ppg, cap)] = _coarse_layout().exchange_layout(n, ppg, cap, "rdna_wave64")
    return _LAYOUTS[(n, ppg, cap)]


# ---- one variant ---------------------------------------------------------------------------

class Variant:
    """One artifact: what is compiled (entry, source text or repo file, flags) and the facts
    it is built with (the manifest record's build fields)."""

    def __init__(self, backend, stem, entry, *, text=None, src=None, repo_file=None,
                 include=True, flags=(), facts=None, function=None):
        self.backend = backend
        self.stem = stem
        self.entry = entry                   # the -entry compiled
        self.function = function or entry    # the function the host loads from the module
        self.text = text                     # () -> source text, or None for repo_file
        self.src = src                       # temp source basename (Metal #line names it)
        self.repo_file = repo_file           # a source compiled where it is in src/gpu
        self.include = include
        self.flags = tuple(flags)
        self.facts = dict(facts or {})

    @property
    def file(self):
        return self.stem + BACKENDS[self.backend][2]

    def __repr__(self):
        return "Variant(%s %s)" % (self.backend, self.file)


_TEXT = {}


def source(name):
    """A shader source's text (read once)."""
    if name not in _TEXT:
        _TEXT[name] = (GPU_SRC / name).read_text()
    return _TEXT[name]


# ---- the one prelude builder ----------------------------------------------------------------

def tierb_prelude(backend, n, cap, entry, coarse16=0, ppg=1, tile=1, single_bin=0, gate_only=0,
                  table=True, split=0):
    """The defines a tierb.slang build is specialised by, as each target's build spells them.

    Vulkan: binding-layout macros (MF_TIERB_PEAKS, MF_REFINE_BOUNDED, MF_PAIR_OUT for the
    listed refines), then the shape, then the fp32 stage padding or the coarse prelude
    (bank-conflict-free exchange layout, the fp16 bound's C16_KAPPA, the fp16 twiddle table).
    Metal: MF_METAL, the shape with SPLIT_STAGE, Apple's C16_KAPPA and the twiddle table for a
    coarse build (MF_COARSE_TWT picks it at library compile time), MF_PAIR_OUT for the listed
    refines, MF_GATE_ONLY. CUDA: the shape with SLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT, then
    MF_GATE_ONLY, then the coarse prelude with or without the twiddle table (table: the "w"
    build; the kernel otherwise runs the twiddle recurrence). MF_CUDA, which selects every
    CUDA-only path in the source, is a command-line define (command)."""
    r = radix(n)
    listed = entry in ("refineItems", "refineListed")
    shape = ("#define NLEN %d\n#define LDS_CAP %d\n#define COARSE16 %d\n#define PPG %d\n"
             "#define TILE_T %d\n#define RADIX %d\n#define SINGLE_BIN %d\n"
             % (n, cap, coarse16, ppg, tile, r, single_bin))
    if backend == "vulkan":
        return (("#define MF_PAIR_OUT 1\n" if listed else "")
                + ("#define MF_GATE_ONLY 1\n" if gate_only else "")
                # The binned fusedTierB build reads its row-window table at binding 4, after
                # its own four buffers (tierb.slang gRowWin).
                + ("#define MF_TIERB_PEAKS 1\n" if entry == "fusedTierB" and not coarse16 else "")
                # refine_bounded.slang's own buffers take bindings 0-5 (tierb.slang's
                # row-window table moves past them): the follow-up refine too, so every
                # target binds its buffers in its parameter order.
                + ("#define MF_REFINE_BOUNDED 1\n" if listed else "")
                + shape
                + (coarse_prelude(n, cap, ppg) if coarse16
                   else "#define XSTRIDE_F %d\n" % fp32_xstride(n, cap)))
    if backend == "metal":
        cl = _coarse_layout() if coarse16 else None
        return ("#define MF_METAL 1\n" + shape + "#define SPLIT_STAGE %d\n" % split
                # The derived fp16 bound's kappa from Apple's measured error table
                # (tools/coarse_layout.py C16_SIGMA_APPLE; tools/c16_sigma.py), and the fp16
                # twiddle table for a "w" entry's MF_COARSE_TWT=1 (twiddle.slang).
                + ("#define C16_KAPPA %.4f\n" % cl.c16_kappa(n, cl.C16_SIGMA_APPLE)
                   + cl.twiddle_table_source(n) if coarse16 else "")
                + ("#define MF_PAIR_OUT 1\n" if listed else "")
                + ("#define MF_GATE_ONLY 1\n" if gate_only else ""))
    text = (shape + "#define SLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT 1\n#define TARGET_CUDA 1\n"
            + ("#define MF_GATE_ONLY 1\n" if gate_only else ""))
    if coarse16:
        pre = coarse_prelude(n, cap, ppg)
        text += pre if table else pre[:pre.index("static const uint COARSE_TWT_DATA")]
    return text


def coarse_prelude(n, cap, ppg):
    """Build-time inputs of the packed coarse kernel (see tools/coarse_layout.py): the
    bank-conflict-free exchange padding for (band, PPG), the fp16 bound's C16_KAPPA (the
    Radeon's measured error table) and the fp16 twiddle table."""
    cl = _coarse_layout()
    xs, slot = exchange_layout(n, ppg, cap)
    return ("#define XSTRIDE %d\n#define XSLOT %d\n#define C16_KAPPA %.4f\n"
            % (xs, slot, cl.c16_kappa(n)) + cl.twiddle_table_source(n))


def command(slangc, v, src, out, nvrtc=None):
    """The one slangc command line: every variant of every target is compiled with it."""
    cmd = [slangc, str(src)]
    if v.include:
        cmd += ["-I", str(GPU_SRC)]
    cmd += ["-target", BACKENDS[v.backend][1], "-entry", v.entry, "-stage", "compute", "-O3"]
    if v.backend == "vulkan":
        cmd.append("-DMF_VULKAN=1")
    elif v.backend == "cuda":
        cmd += ["-DSLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT=1", "-DMF_CUDA=1"]
        if nvrtc:
            cmd += ["-nvrtc-path", str(nvrtc)]
    cmd += list(v.flags)
    return cmd + ["-o", str(out)]


# ---- the table --------------------------------------------------------------------------------

def _tierb(backend, n, entry, cap=None, suffix="", coarse16=0, ppg=1, tile=1, single_bin=0,
           gate_only=0, table=True, split=None):
    """A tierb.slang build (refine_bounded.slang appended for the listed refines)."""
    cap = LDS_CAP[n] if cap is None else cap
    if split is None:
        split = metal_split(n, cap, coarse16) if backend == "metal" else 0
    listed = entry in ("refineItems", "refineListed")
    compiled = "refineListedBounded" if entry == "refineListed" else entry
    stem = "%s_%d%s" % (STEMS[entry], n, suffix)
    wg = n // radix(n)
    threads = wg * (ppg if entry in ("fusedTierB", "refineListed", "refineItems") else 1)

    def text():
        body = tierb_prelude(backend, n, cap, entry, coarse16, ppg, tile, single_bin, gate_only,
                             table, split) + source("tierb.slang")
        if listed:
            body += ("\n" if backend == "cuda" else "") + source("refine_bounded.slang")
        return body

    if backend == "vulkan":
        src = "mf_%d_%s%s.slang" % (n, entry, suffix)
    elif backend == "metal":
        src = "mm_%d_%s%s.slang" % (n, entry, suffix)
    else:
        src = stem + ".temp.slang"
    flags = CUDA_WIDE_BLOCK_FLAGS if backend == "cuda" and threads >= MAX_INVOCATIONS else ()
    facts = dict(n=n, cap=cap, ppg=ppg, tile=tile, coarse16=coarse16, single_bin=single_bin,
                 gate_only=gate_only, portable=int(suffix.endswith("_lds32")))
    if backend == "metal":
        facts["split"] = split
    if backend == "cuda" and coarse16:
        facts["twt"] = int(bool(table))
    if backend == "vulkan" and not coarse16:
        facts["xstride_f"] = fp32_xstride(n, cap)
    if backend != "metal" and coarse16:
        facts["xstride"], facts["xslot"] = None, None          # filled lazily (_staging)
    return Variant(backend, stem, compiled, text=text, src=src, flags=flags, facts=facts,
                   function=compiled)


def _compaction(backend, n, add):
    """The survivor compactions, one kernel each on every backend (they use no workgroup
    memory and read no length: built at the first length, the code is the same at every
    one)."""
    for entry, stem in (("compactPairs", "compact"), ("compactListed", "compactl")):
        v = _tierb(backend, n, entry, metal_cap(n) if backend == "metal" else None)
        v.stem = stem
        add(v)


def _band_family(backend, n, add):
    """The one-stage family at n for one target, in build order."""
    portable = lds_bytes(n, LDS_CAP[n]) > lds_bytes(n, PORTABLE_CAP)
    if backend == "metal":
        mcap = metal_cap(n)
        if radix(n) == 16:
            add(_tierb(backend, n, "fusedTierB", mcap, "_c16", coarse16=1))
            for p in METAL_C16_PPG:
                if (n // radix(n)) * p <= METAL_C16_MAX_THREADS:
                    add(_tierb(backend, n, "fusedTierB", mcap, "_c16p%d" % p, coarse16=1, ppg=p))
            # Tiled, ragged builds for Metal too (two templates per lane in one half2
            # register; _mtlcompute.coarse_geometry).
            for t in (COARSE_TILES if n <= MAX_TILED_BAND else ()):
                for p in (1,) + METAL_C16_PPG:
                    if (n // radix(n)) * p <= METAL_C16_MAX_THREADS:
                        add(_tierb(backend, n, "fusedTierB", mcap,
                                   "_c16%st%d" % ("p%d" % p if p > 1 else "", t),
                                   coarse16=1, ppg=p, tile=t))
        for entry in ("fusedTierB", "refineListed",
                      "refineItems") + (("fullCorrelation", "fullCorrelationSeries")
                                        if n >= 1024 else ()):
            add(_tierb(backend, n, entry, mcap))
            # Apple caps threadgroup memory at 32 KB, under what the tuned staging asks for
            # at the top sizes. Without a build that fits, those kernels cannot create a
            # pipeline on ANY Mac -- and the refusal arrives as "Compilation failed".
            if lds_bytes(n, mcap) > lds_bytes(n, PORTABLE_CAP):
                add(_tierb(backend, n, entry, PORTABLE_CAP, "_lds32"))
        if n == TIER_B[0]:
            _compaction(backend, n, add)
        if n in METAL_SINGLE_BIN_CAP:
            for entry in ("fusedTierB", "refineListed"):
                cap = METAL_SINGLE_BIN_CAP[n]
                add(_tierb(backend, n, entry, cap, "_onebin", single_bin=1))
                if entry == "refineListed" and n <= 1024:
                    add(_tierb(backend, n, entry, cap, "_onebin_gate", single_bin=1,
                               gate_only=1))
        return
    if backend == "vulkan" and portable:
        add(_tierb(backend, n, "fusedTierB", PORTABLE_CAP, "_lds32"))
    add(_tierb(backend, n, "fusedTierB"))
    if backend == "cuda" and portable:
        add(_tierb(backend, n, "fusedTierB", PORTABLE_CAP, "_lds32"))
    if n >= 1024:
        for entry in ("fullCorrelation", "fullCorrelationSeries"):
            add(_tierb(backend, n, entry))
        if portable:
            for entry in ("fullCorrelation", "fullCorrelationSeries"):
                add(_tierb(backend, n, entry, PORTABLE_CAP, "_lds32"))
    # Compaction (band-independent: one kernel each, built at the first length): gather the
    # pairs that passed the coarse threshold so the refine runs only those. The refine used
    # to launch a workgroup per pair to have it exit -- 57% of the hierarchical call at
    # 512x512 -- and that cost does not shrink with the band because it is not arithmetic.
    if n == TIER_B[0]:
        _compaction(backend, n, add)
    # The follow-up refine over listed entries, and the listed refine.
    for entry in (("refineItems", "refineListed") if backend == "vulkan"
                  else ("refineListed", "refineItems")):
        add(_tierb(backend, n, entry))
        if portable and (backend == "vulkan" or entry == "refineItems"):
            add(_tierb(backend, n, entry, PORTABLE_CAP, "_lds32"))
    if backend == "cuda" and portable:
        add(_tierb(backend, n, "refineListed", PORTABLE_CAP, "_lds32"))
    # One-bin refine below 4096 as well: the cascade's tier-1 stage and the n=2048 refine run
    # one bin. Listed one-bin refine, CU-cycles/pair, general -> one-bin: n=512 945 -> 677,
    # 1024 1686 -> 1288, 2048 3590 -> 2851. A later gate tier's decision alone (tierb.slang
    # MF_GATE_ONLY) is its own build, measured against the election per device
    # (_gpuhier._played "gateway").
    if 256 <= n < 4096:
        add(_tierb(backend, n, "refineListed", suffix="_onebin", single_bin=1))
        if n <= 1024:
            add(_tierb(backend, n, "refineListed", suffix="_onebin_gate", single_bin=1,
                       gate_only=1))
    # Benchmarked one-bin specialization for the large full-precision kernels. Keep the
    # general kernels for multiple output bins.
    if n >= 4096:
        for entry in ("fusedTierB", "refineListed"):
            add(_tierb(backend, n, entry, suffix="_onebin", single_bin=1))
            if portable:
                add(_tierb(backend, n, entry, PORTABLE_CAP, "_onebin_lds32", single_bin=1))
    # The coarse ROLE, at half width: fusedTierB serves the coarse stage as well as its own,
    # and the coarse stage reads the packed cdata/ct0 -- so it gets a SECOND build rather
    # than a changed one, and the flat/refine paths keep full precision. Only at the lengths
    # a BAND can take (R = 16): a band is always shorter than the transform it gates, so no
    # coarse kernel is ever dispatched at the two widest sizes. The kernel's own #error states
    # the same constraint.
    #
    # The TILE is part of kernel IDENTITY. TILE_T is compiled in, so the base variants MUST
    # be TILE_T=1 and the tiled ones carry their own suffix -- otherwise the host's untiled
    # fallback (taken whenever ntemplates does not divide by the tile) selects a TILED kernel,
    # which walks TILE_T templates from p0 = gid.x*TILE_T past the end of the bank. Spelled
    # exactly as the host spells it (_coarse.coarse_stem): "p1" is omitted.
    if radix(n) != 16:
        return
    wg = n // 16
    if backend == "vulkan":
        untiled, tiled = vk_c16_ppgs(n), (1, 2, 4, 8, 16)
    else:
        untiled = (2, 4) + ((8, 16) if n <= 256 else ())
        tiled = (1, 2, 4) + ((8,) if n <= 256 else ())
    builds = [("_c16", 1, 1)] + [("_c16p%d" % p, p, 1) for p in untiled]
    builds += [("_c16%st%d" % ("p%d" % p if p > 1 else "", t), p, t)
               for t in (COARSE_TILES if n <= MAX_TILED_BAND else ())
               for p in tiled if backend == "cuda" or wg * p <= MAX_INVOCATIONS]
    for suffix, p, t in builds:
        if backend == "cuda":
            # Both twiddle sources: the fp16 table ("w") and the recurrence; the measured
            # coarse choice picks (_gpuhier._time_coarse_layouts). On the L40S the table cost
            # band 1024's tiled build ~40% and band 512's ~10%, and was even at 64-256.
            add(_tierb(backend, n, "fusedTierB", suffix=suffix + "w", coarse16=1, ppg=p, tile=t,
                       table=True))
            add(_tierb(backend, n, "fusedTierB", suffix=suffix, coarse16=1, ppg=p, tile=t,
                       table=False))
        else:
            add(_tierb(backend, n, "fusedTierB", suffix=suffix, coarse16=1, ppg=p, tile=t))


def _forward_family(backend, n, add):
    """The forward transforms at n: the full forward, the band-only forward, the survivor
    recompute and the fused forward + tier-0 bands (series_forward.slang, series_bands.slang,
    forward_tier0.slang), every target, so every device chooses among the same ways of feeding
    the hierarchical tiers. One <=32 KiB staging works on every target. Metal stages its
    exchange per component where that removes a chunk (metal_split)."""
    r = radix(n)
    cap = min(LDS_CAP[n], PORTABLE_CAP)
    wg = n // r
    if backend == "cuda":
        defines = ("#define NLEN %d\n#define RADIX %d\n#define LDS_CAP %d\n"
                   "#define SLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT 1\n" % (n, r, cap))
        split = 0
    else:
        split = metal_split(n, cap) if backend == "metal" else 0
        defines = ("#define NLEN %d\n#define RADIX %d\n#define LDS_CAP %d\n#define SPLIT_STAGE %d\n"
                   % (n, r, cap, split))
    flags = CUDA_WIDE_BLOCK_FLAGS if backend == "cuda" and wg >= MAX_INVOCATIONS else ()
    facts = dict(n=n, cap=cap, ppg=1, tile=1, coarse16=0, single_bin=0, gate_only=0, portable=0)
    if backend == "metal":
        facts["split"] = split

    def fwd():
        return defines + source("tierb.slang") + "\n" + source("series_forward.slang")

    def bands():
        return (fwd() + "\n" + source("series_bands.slang") + "\n"
                + source("forward_tier0.slang"))

    def src(name):
        return (name + ".slang") if backend != "cuda" else None

    add(Variant(backend, "forward_%d" % n, "seriesForward", text=fwd,
                src=src("forward") or "forward_%d.temp.slang" % n, flags=flags, facts=facts))
    todo = [("seriesForwardBands", "forward_bands_%d" % n),
            ("seriesForwardListed", "forward_listed_%d" % n),
            ("forwardTier0", "forward_tier0_%d" % n)]
    if n == TIER_B[0]:
        todo.append(("markBlocks", "markblocks"))
    for entry, stem in todo:
        add(Variant(backend, stem, entry, text=bands, src=src("bands") or stem + ".temp.slang",
                    flags=flags, facts=facts))


def _tierc_family(backend, n, add):
    """The two-stage (Tier C) kernels at n: correlation and series-forward stages, each a
    tierb.slang build at its sub-length."""
    n1, n2 = tierc_split(n)
    for role, entry in TIER_C_ENTRIES:
        sub = n2 if role.endswith("1") else n1
        r = radix(sub)
        if backend == "cuda":
            cap = min(LDS_CAP[sub], PORTABLE_CAP)
            defines = ("#define NLEN %d\n#define TC_N %d\n#define LDS_CAP %d\n#define RADIX %d\n"
                       "#define SLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT 1\n#define TARGET_CUDA 1\n" % (sub, n, cap, r))
            src = "tc_%s_%d.temp.slang" % (role, n)
        else:
            cap = LDS_CAP[sub]
            defines = "#define NLEN %d\n#define TC_N %d\n#define LDS_CAP %d\n" % (sub, n, cap)
            src = "tc_%s_%d.slang" % (role, n)
        flags = (CUDA_WIDE_BLOCK_FLAGS if backend == "cuda" and sub // r >= MAX_INVOCATIONS
                 else ())
        add(Variant(backend, "tc_%s_%d" % (role, n), entry,
                    text=(lambda d=defines: d + source("tierb.slang")), src=src, flags=flags,
                    facts=dict(n=sub, tc_n=n, cap=cap, ppg=1, tile=1, coarse16=0, single_bin=0,
                               gate_only=0, portable=0, role=role, n1=n1, n2=n2)))


def _standalone(backend, stem, entry):
    """pack_coarse.slang / compact_peaks.slang: compiled where they are on Vulkan and Metal,
    from a copy with the structured-buffer define on CUDA."""
    facts = dict(n=0, ppg=1, tile=1, coarse16=0, single_bin=0, gate_only=0, portable=0)
    if backend == "cuda":
        return Variant(backend, stem, entry, src=stem + ".temp.slang", facts=facts,
                       text=lambda: ("#define SLANG_CUDA_STRUCTURED_BUFFER_NO_COUNT 1\n"
                                     + source(stem + ".slang")))
    return Variant(backend, stem, entry, repo_file=GPU_SRC / (stem + ".slang"), include=False,
                   facts=facts)


def variants(backend):
    """Every artifact the build makes for one backend ("vulkan", "metal" or "cuda"), in
    build order."""
    out = []
    add = out.append
    if backend == "cuda":
        add(_standalone(backend, "pack_coarse", "packCoarse"))
    for n in TIER_B:
        _band_family(backend, n, add)
        if backend == "cuda":
            _forward_family(backend, n, add)
    if backend != "cuda":
        add(_standalone(backend, "pack_coarse", "packCoarse"))
        add(_standalone(backend, "compact_peaks", "compactPeaks"))
        for n in TIER_B:
            _forward_family(backend, n, add)
    for n in FULL_TIER_C:
        _tierc_family(backend, n, add)
    if backend == "cuda":
        add(_standalone(backend, "compact_peaks", "compactPeaks"))
        # No module past what CUDA can launch (STATIC_SHARED_MAX, MAX_INVOCATIONS).
        out = [v for v in out if not v.facts.get("n") or (
            local_size(v)[0] <= MAX_INVOCATIONS and _staging(v) <= STATIC_SHARED_MAX)]
    stems = [v.stem for v in out]
    assert len(stems) == len(set(stems)), "two variants of one name"
    return out


# ---- facts derived from the source ---------------------------------------------------------

_NUMTHREADS = re.compile(r"\[numthreads\(\s*([^,\]]+?)\s*,\s*1\s*,\s*1\s*\)\]\s*"
                         r"void\s+(\w+)\s*\(")
_THREADS = {}


def _threads_expr(entry):
    """The [numthreads(x, 1, 1)] expression of an entry point, read from src/gpu."""
    if not _THREADS:
        for path in sorted(GPU_SRC.glob("*.slang")):
            for expr, name in _NUMTHREADS.findall(path.read_text()):
                _THREADS.setdefault(name, expr)
    return _THREADS[entry]


def local_size(v):
    """[x, 1, 1]: the variant's workgroup, its entry's numthreads evaluated at its defines
    (WG = NLEN / RADIX, PPG). The SPIR-V build's reflection is checked against it."""
    n = v.facts.get("n", 0) or 64
    wg = n // radix(n)
    x = eval(_threads_expr(v.entry), {"__builtins__": {}}, {"WG": wg, "PPG": v.facts["ppg"]})
    return [int(x), 1, 1]


def _staging(v):
    """staging_bytes of a tierb.slang-family variant, from its build facts."""
    f = v.facts
    if f.get("coarse16") and v.backend != "metal":
        xs, slot = exchange_layout(f["n"], f["ppg"], f["cap"])
        return staging_bytes(f["n"], f["cap"], f["ppg"], 1, xstride=xs, xslot=slot)
    return staging_bytes(f["n"], f["cap"], f["ppg"], f.get("coarse16", 0),
                         xstride_f=f.get("xstride_f"))


# ---- facts read from the artifact ----------------------------------------------------------

_STORAGE_CLASS = {2: "Uniform", 9: "PushConstant", 12: "StorageBuffer"}


def reflect(blob):
    """Read the host-side contract back out of a compiled SPIR-V module: its local size, its
    descriptors, whether it takes push constants, and the bytes of workgroup memory it
    declares.

    Parsed from the SPIR-V rather than assumed from the Slang source because the two can
    disagree: `uniform uint ntmpl` in the source becomes a PUSH CONSTANT, not a descriptor,
    and a host written against the source would bind a buffer that the module never reads.
    Whatever the compiler decided is the truth, so ask the artefact.
    """
    words = struct.unpack("<%dI" % (len(blob) // 4), blob)
    if words[0] != 0x07230203:
        raise ValueError("not a SPIR-V module")
    names, sets, bindings, variables, types, consts = {}, {}, {}, [], {}, {}
    local_size = None
    i = 5
    while i < len(words):
        op, count = words[i] & 0xFFFF, words[i] >> 16
        if count == 0:
            break
        w = words[i:i + count]
        if op == 5:                                   # OpName
            names[w[1]] = struct.pack("<%dI" % (count - 2), *w[2:]).split(b"\0")[0].decode(
                "utf-8", "replace")
        elif op == 71 and count >= 4:                 # OpDecorate
            if w[2] == 33:
                bindings[w[1]] = w[3]
            elif w[2] == 34:
                sets[w[1]] = w[3]
        elif op == 16 and count >= 6 and w[2] == 17:  # OpExecutionMode LocalSize
            local_size = tuple(w[3:6])
        elif op == 59:                                # OpVariable
            variables.append((w[1], w[2], w[3]))
        elif op in (21, 22):                          # OpTypeInt, OpTypeFloat
            types[w[1]] = w[2] // 8
        elif op == 23:                                # OpTypeVector
            types[w[1]] = ("vec", w[2], w[3])
        elif op == 28:                                # OpTypeArray
            types[w[1]] = ("arr", w[2], w[3])
        elif op == 30:                                # OpTypeStruct
            types[w[1]] = ("struct",) + tuple(w[2:])
        elif op == 32:                                # OpTypePointer
            types[w[1]] = ("ptr", w[2], w[3])
        elif op == 43:                                # OpConstant
            consts[w[2]] = w[3]
        i += count

    def size(t):
        s = types[t]
        if isinstance(s, int):
            return s
        if s[0] == "vec":
            return size(s[1]) * s[2]
        if s[0] == "arr":
            return size(s[1]) * consts[s[2]]
        if s[0] == "struct":
            return sum(size(m) for m in s[1:])
        raise ValueError("no size for SPIR-V type %r" % (s,))

    descriptors, push_bytes, shared = [], 0, 0
    for ptr, vid, storage in variables:
        kind = _STORAGE_CLASS.get(storage)
        if kind == "PushConstant":
            push_bytes += size(types[ptr][2])
        elif kind in ("StorageBuffer", "Uniform") and vid in bindings:
            descriptors.append(dict(name=names.get(vid, ""), kind=kind,
                                    set=sets.get(vid, 0), binding=bindings[vid]))
        elif storage == 4:                            # Workgroup
            shared += size(types[ptr][2])
    descriptors.sort(key=lambda d: (d["set"], d["binding"]))
    return dict(local_size=local_size, descriptors=descriptors, push_bytes=push_bytes,
                shared_bytes=shared)


_PTX_SHARED = re.compile(r"^\s*\.shared\s+(?:\.align\s+\d+\s+)?\.(?:b|u|s|f)(\d+)\s+[\w$]+\[(\d+)\]",
                         re.M)
_MSL_SHARED = re.compile(r"threadgroup\s+array<(\w+),\s*int\((\d+)\)>\s+\w+\s*;")
_MSL_BYTES = {"uint": 4, "int": 4, "float": 4, "half": 2, "uint2": 8, "float2": 8, "half2": 4}


def static_shared(ptx_text):
    """Bytes of static shared memory a PTX module declares: the sum of its .shared arrays."""
    return sum(int(bits) // 8 * int(count) for bits, count in _PTX_SHARED.findall(ptx_text))


def msl_shared(msl_text):
    """Bytes of threadgroup memory a Metal source declares: the sum of its threadgroup arrays."""
    return sum(_MSL_BYTES[t] * int(c) for t, c in _MSL_SHARED.findall(msl_text))


def artifact_facts(v, folder):
    """The facts read from a built artifact: its workgroup memory, and for SPIR-V the reflected
    local size, descriptors and push constants."""
    path = folder / v.file
    if v.backend == "vulkan":
        info = reflect(path.read_bytes())
        return dict(lds_bytes=info["shared_bytes"], local_size=list(info["local_size"]),
                    descriptors=info["descriptors"], push_bytes=info["push_bytes"])
    text = path.read_text()
    return dict(lds_bytes=static_shared(text) if v.backend == "cuda" else msl_shared(text))


# ---- the manifest ---------------------------------------------------------------------------

_KID = runpy.run_path(str(PACKAGE / "_kernel_id.py"))


def source_hashes():
    """Fingerprint all production shader dependencies for freshness checks."""
    return {name: hashlib.sha256((GPU_SRC / name).read_bytes()).hexdigest() for name in SOURCES}


def record(v, folder):
    """The manifest record of one built variant: its build facts, the facts read from the
    artifact, and its identity (the artifact's digest). A tierb.slang-family build whose
    declared staging differs from staging_bytes, or a SPIR-V module whose reflected local
    size differs from local_size, raises: the facts the host reads would be wrong."""
    f = v.facts
    rec = dict(file=v.file, entry=v.function, n=f.get("n", 0), local_size=local_size(v))
    for key in ("tc_n", "n1", "n2", "role"):
        if key in f:
            rec[key] = f[key]
    if f.get("n") and "cap" in f:
        rec["cap"] = f["cap"]
    for key in ("ppg", "tile", "coarse16", "single_bin", "gate_only", "portable", "twt", "split"):
        if key in f:
            rec[key] = f[key]
    got = artifact_facts(v, folder)
    if v.backend == "vulkan" and got["local_size"] != rec["local_size"]:
        raise RuntimeError("%s: reflected local size %s, numthreads gives %s"
                           % (v.file, got["local_size"], rec["local_size"]))
    if got["lds_bytes"] and f.get("n") and "cap" in f and got["lds_bytes"] != _staging(v):
        raise RuntimeError("%s declares %d bytes of workgroup memory; its defines give %d"
                           % (v.file, got["lds_bytes"], _staging(v)))
    rec.update(got)
    rec.update(_KID["record_ids"](folder, v.file))
    return rec


def manifest(backend, folder=None, todo=None):
    """The manifest of one backend's artifacts in folder (the package's by default): every
    variant's record, the two-stage splits, the shader-source fingerprints."""
    folder = PACKAGE / BACKENDS[backend][0] if folder is None else pathlib.Path(folder)
    todo = variants(backend) if todo is None else todo
    kernels = {v.stem: record(v, folder) for v in todo}
    two = {str(n): dict(zip(("n1", "n2"), tierc_split(n))) for n in FULL_TIER_C}
    return dict(schema=MANIFEST_SCHEMA, backend=backend, slangc=SLANGC_VERSION,
                generator="tools/kernel_variants.py", source_hashes=source_hashes(),
                two_stage=two, kernels=kernels)


def write_manifest(backend, folder=None):
    folder = PACKAGE / BACKENDS[backend][0] if folder is None else pathlib.Path(folder)
    text = json.dumps(manifest(backend, folder), indent=1, sort_keys=True) + "\n"
    (folder / "manifest.json").write_text(text)
    return folder / "manifest.json"


# ---- compiling --------------------------------------------------------------------------------

def find_slangc(explicit=None):
    """--slangc, then MF_SLANGC, then third_party/slang, then PATH.

    The env var exists because slangc ships as a tarball rather than a package, so it is
    common for it to live somewhere unpacked rather than installed.
    """
    for candidate in (explicit, os.environ.get("MF_SLANGC"),
                      str(ROOT / "third_party" / "slang" / "bin" / "slangc"),
                      shutil.which("slangc")):
        if candidate and pathlib.Path(candidate).is_file():
            return str(candidate)
    return None


def check_slangc_version(slangc):
    """Refuse a slangc other than SLANGC_VERSION (unless MF_SLANGC_ANY_VERSION=1)."""
    got = subprocess.run([slangc, "-v"], capture_output=True, text=True)
    out = (got.stdout + got.stderr).strip()
    ver = out.splitlines()[0].strip() if out else "?"
    if ver != SLANGC_VERSION and os.environ.get("MF_SLANGC_ANY_VERSION", "0") == "0":
        raise SystemExit("slangc %s is %s; the shipped kernels are built with %s "
                         "(set MF_SLANGC_ANY_VERSION=1 to build anyway)" % (slangc, ver, SLANGC_VERSION))
    return ver


def find_nvrtc():
    """NVRTC for the PTX target: MF_NVRTC, then the usual install locations."""
    for c in (os.environ.get("MF_NVRTC"),
              "/home/ahnitz/miniconda3/lib/python3.13/site-packages/nvidia/cuda_nvrtc/lib/libnvrtc.so.12",
              "/usr/lib/x86_64-linux-gnu/libnvrtc.so"):
        if c and os.path.exists(c):
            return str(c)
    return None


def find_cuda_path():
    """CUDA_PATH for the PTX target: MF_CUDA_PATH, then the usual install locations."""
    for c in (os.environ.get("MF_CUDA_PATH"),
              "/home/ahnitz/miniconda3/lib/python3.13/site-packages/nvidia/cuda_runtime",
              "/usr/local/cuda"):
        if c and os.path.exists(c):
            return str(c)
    return None


def write_msl(msl):
    """Normalise an emitted Metal source in place: #line directives name the file only, not
    the build machine's path to it (so the shipped source, and the Metal kernel identity
    hashed from it, do not depend on where it was built), and one trailing newline."""
    text = re.sub(r'(?m)^(#line\s+\d+\s+)"[^"\n]*/([^/"\n]+)"', r'\1"\2"', msl.read_text())
    msl.write_text(text.rstrip() + "\n")


def compile_metallib(msl):
    """Compile one Metal source when Apple tooling exists; drop stale output."""
    msl.with_suffix(".metallib").unlink(missing_ok=True)
    if not shutil.which("xcrun"):
        return None
    lib, air = msl.with_suffix(".metallib"), msl.with_suffix(".air")
    for cmd in ([["xcrun", "-sdk", "macosx", "metal", "-c", str(msl), "-o", str(air)],
                 ["xcrun", "-sdk", "macosx", "metallib", str(air), "-o", str(lib)]]):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print("  metallib step failed (%s); shipping MSL only"
                  % r.stderr.strip().splitlines()[-1:], file=sys.stderr)
            lib.unlink(missing_ok=True)
            lib = None
            break
    air.unlink(missing_ok=True)
    return lib


def compile_variant(slangc, v, folder, nvrtc=None, env=None):
    """Compile one variant into folder (its file name there). Returns the artifact's path."""
    folder = pathlib.Path(folder)
    out = folder / v.file
    # The source is written beside the output (as every build always has), not to the
    # system temporary directory: a build depends on one filesystem only.
    with tempfile.TemporaryDirectory(prefix=".build-", dir=folder) as tmp:
        if v.repo_file is not None:
            src = v.repo_file
        else:
            src = pathlib.Path(tmp) / v.src
            src.write_text(v.text())
        # In the temporary folder: NVRTC writes its precompiled header (default_program.pch)
        # to the working directory, and parallel compiles there delete each other's.
        proc = subprocess.run(command(slangc, v, src, out, nvrtc), capture_output=True,
                              text=True, env=env, cwd=tmp)
    if proc.returncode != 0:
        raise RuntimeError("slangc failed for %s (%s), exit status %d:\n%s"
                           % (v.file, v.entry, proc.returncode, proc.stderr))
    if v.backend == "metal":
        write_msl(out)
        compile_metallib(out)
    return out


def build(backends, only=None, jobs=1, slangc=None):
    """Compile the variants of each backend (those whose stem matches the glob `only`, or
    all), then write each backend's manifest from every variant's artifact."""
    slangc = find_slangc(slangc)
    if slangc is None:
        print("slangc not found; pass --slangc, set MF_SLANGC or put it on PATH.\n"
              "It ships in the official Slang release:\n"
              "  https://github.com/shader-slang/slang/releases", file=sys.stderr)
        return 1
    check_slangc_version(slangc)
    nvrtc, env = None, None
    if "cuda" in backends:
        nvrtc = find_nvrtc()
        env = dict(os.environ)
        cuda_path = find_cuda_path()
        if cuda_path:
            env["CUDA_PATH"] = cuda_path
    for backend in backends:
        folder = PACKAGE / BACKENDS[backend][0]
        folder.mkdir(parents=True, exist_ok=True)
        todo = [v for v in variants(backend) if only is None or fnmatch.fnmatchcase(v.stem, only)]
        with ThreadPoolExecutor(max(1, int(jobs))) as pool:
            for path in pool.map(lambda v: compile_variant(
                    slangc, v, folder, nvrtc if v.backend == "cuda" else None,
                    env if v.backend == "cuda" else None), todo):
                print("  %s %s" % (backend, path.name), flush=True)
        print("wrote %s (%d kernels built)" % (write_manifest(backend), len(todo)), flush=True)
    return 0


# ---- the CI check -------------------------------------------------------------------------------

def check(package=PACKAGE):
    """Whether each backend's folder holds exactly the artifacts a build makes (no missing and
    no extra file) and a manifest equal to the one the generator writes from them. Prints one
    verdict per backend; returns the number of failures."""
    failures = 0
    for backend, (folder, _, suffix) in BACKENDS.items():
        root = pathlib.Path(package) / folder
        want = {v.file for v in variants(backend)}
        have = {p.name for p in root.iterdir()
                if p.is_file() and p.suffix == suffix}
        missing, extra = sorted(want - have), sorted(have - want)
        stray = sorted(p.name for p in root.iterdir() if p.is_file()
                       and p.suffix not in (suffix, ".json", ".metallib"))
        problems = []
        if missing:
            problems.append("not shipped: %s" % ", ".join(missing))
        if extra:
            problems.append("shipped but no build makes them: %s" % ", ".join(extra))
        if stray:
            problems.append("stray files: %s" % ", ".join(stray))
        if not missing:
            shipped = json.loads((root / "manifest.json").read_text())
            expected = json.loads(json.dumps(manifest(backend, root)))
            if shipped != expected:
                keys = sorted(k for k in set(shipped) | set(expected)
                              if shipped.get(k) != expected.get(k))
                diff = keys
                if "kernels" in keys:
                    a, b = shipped.get("kernels", {}), expected["kernels"]
                    diff = [k for k in keys if k != "kernels"] + sorted(
                        s for s in set(a) | set(b) if a.get(s) != b.get(s))[:20]
                problems.append("manifest.json differs from the generator's: %s"
                                % ", ".join(map(str, diff)))
        print("%s %s: %d artifacts%s" % ("FAIL" if problems else "ok", backend, len(want),
                                         "".join("\n  " + p for p in problems)))
        failures += bool(problems)
    return failures


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("action", choices=("build", "list", "check"))
    ap.add_argument("--backend", default="vulkan,metal,cuda",
                    help="comma-separated: vulkan, metal, cuda")
    ap.add_argument("--only", default=None, help="build only the variants whose stem matches "
                    "this glob (the manifest is still written for every variant)")
    ap.add_argument("--jobs", type=int, default=1, help="compilers run at once")
    ap.add_argument("--slangc", default=None)
    args = ap.parse_args(argv)
    backends = [b for b in args.backend.split(",") if b]
    for b in backends:
        if b not in BACKENDS:
            ap.error("unknown backend %r" % b)
    if args.action == "list":
        for b in backends:
            for v in variants(b):
                print("%s %s" % (b, v.file))
        return 0
    if args.action == "check":
        bad = check()
        print("kernel_variants check: %s" % ("FAIL" if bad else "ok"))
        return 1 if bad else 0
    return build(backends, args.only, args.jobs, args.slangc)


if __name__ == "__main__":
    raise SystemExit(main())
