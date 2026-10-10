# CUDA on the L40S: per-kernel roofline at the bench's production shapes

Measured 2026-10-08 on one NVIDIA L40S (Ada, sm_89, 142 SMs), driver 570.133 (CUDA 12.8), in
condor job 48964973 on OG-NODE-10-5-174-98. The job had 8 cores of an AMD EPYC 9845. The
second L40S in that node belonged to another job and was ~60% busy throughout. Branch
`parity/cuda`.

## Ceilings: measured, not taken from the data sheet

| ceiling | data sheet | measured (tools/cuda_ceilings.cu) |
|---|---:|---:|
| fp32 FMA | 91.6 TFLOPS (2.52 GHz boost) | **72.7 TFLOPS** (8 independent FMA chains, 142x16 blocks) |
| DRAM | 864 GB/s | **623 GB/s** (device-to-device float4 stream, 1 GB) |

Percentages below are against the measured values.

## How to regenerate

    MF_NVRTC=.../libnvrtc.so.12 python tools/cuda_roofline.py --build-ceilings   # once, needs NVRTC 12.8
    python tools/cuda_roofline.py --bank bank3.hdf --segments 3 --json out.json

The script runs `tools/ladder.py`'s own call pattern: top 1 of the production three-level
bank, `--resident`, steady segments only. It uses `MF_GPU_TIMING=1` and records every
launch, so each kernel is measured at exactly the shapes the bench gives it.

Things the table does not have:
- **Hardware counters.** ncu cannot run on this node (`RmProfilingAdminOnly=1`).
- **Measured bytes and flops.** These come from an analytic model, given as a range:
  - min: unique data touched, with reused inputs assumed to stay in L2;
  - max: every per-pair load counted as DRAM traffic.
- **Refine rates.** The refine kernels are grid-stride over a device-side survivor count, so
  the grid is not their work. With no survivor attribution, their rate cells are blank.

Registers, static shared memory, spill (local) bytes and theoretical occupancy come from
`cuFuncGetAttribute` and `cuOccupancyMaxActiveBlocksPerMultiprocessor`.

## The table (ladder --resident, 2 detectors x 2 steady segments, 4698 fine templates)

| kernel | calls | device ms | us/call | mean grid | TFLOPS | %fp32 | GB/s (min-max) | %bw (min) | regs | smem | spill B | occ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| readback (D2H, pinned) | 436 | 5.61 | 12.9 | | | | | | | | | |
| forward_2048 (series FFT) | 154 | 4.55 | 29.5 | 301 | 1.19 | 1.6 | 335 | 54 | 80 | 8 KB | 0 | 0.50 |
| tier1_256 (2nd coarse tier, listed) | 312 | 3.83 | 12.3 | 875 | | | | | 127 | 2 KB | 288 | 0.17 |
| tierb_64_c16p16 (coarse gate, fp16) | 312 | 3.82 | 12.2 | 1794 | 0.37 | 0.5 | 39-75 | 6 | 64 | 4 KB | 0 | 0.67 |
| refine_2048 (listed refine) | 312 | 2.82 | 9.0 | 307 | | | | | 128 | 8 KB | 288 | 0.33 |
| compact | 648 | 2.66 | 4.1 | 104 | | | | | 12 | 0 | 0 | 1.00 |
| full_series_16384_lds32 (middle) | 4 | 2.34 | 586 | 681 | 1.45 | 2.0 | 152-457 | 24 | 64 | 32 KB | 24 | 0.67 |
| pack_coarse | 436 | 2.11 | 4.8 | 143 | | | | | 12 | 0 | 0 | 1.00 |
| upload (H2D) | 195 | 1.24 | 6.4 | | | | | | | | | |
| tierb_2048 (asym, flat) | 51 | 1.17 | 23.0 | 13 | 0.07 | 0.1 | 0-18 | 0 | 96 | 8 KB | 288 | 0.42 |
| forward_16384 | 4 | 0.22 | 55 | 30 | 0.64 | 0.9 | 142 | 23 | 64 | 32 KB | 32 | 0.67 |

The stage totals (device time, s), against the ladder's wall time:

| stage | device | wall |
|---|---:|---:|
| middle | 0.0026 | 0.026 |
| fine | 0.025 | 0.075-0.092 |
| asym | 0.005 | 0.017-0.021 |

### Reading the table

- **No kernel is near its target** (compute-bound >= 50% of fp32, memory-bound >= 70% of
  bandwidth). The best are:
  - the series forward FFT, at 54% of stream bandwidth (it is memory-bound);
  - the middle correlation, at 24-73% depending on how much of its output traffic is real.

  The fine stage's kernels are neither compute- nor bandwidth-bound. They are
  **latency/launch-bound**: 4-30 us per launch at grids of 100-1800 blocks, across 142 SMs.
  An L40S needs roughly 142 x 4-8 resident blocks, and several waves of them, before
  launch and tail costs stop dominating.
- **The fine stage is about 13 launches per call, and each is small.** One fine call is one
  submission: about 80k (data, template) pairs, median 82k, range 35k-119k, over three
  window groups. Its launches are:
  - pack;
  - coarse;
  - compact;
  - tier-1;
  - compact;
  - refine;
  - fills and readbacks.

  Device time per call is ~0.23 ms. About 0.06 ms of that is fills and copies.
- **Spills.** Every 256-thread refine/tier-1/flat build at n >= 2048 spills 288 B per thread.
  They use 127-128 registers, the cap the JIT gets at 512 threads per block. The 32768-point
  single-block middle kernel spilled 504 B per thread (3.2 ms per call). The middle stage now
  avoids it by pricing on the device; see Optimisations.
- **Occupancy.** It is low for the refine family (0.17-0.33) and for the old one-pair-per-block
  coarse gate (0.04 at band 64, with 4-thread blocks). The gate now runs 16 pairs per block
  (0.67).

## Saturation: device ns/pair against pairs per call

`HierarchicalFilter.run_series` on a resident series, 200 templates, min of 5,
`MF_GPU_TIMING=1`:

| pairs/call | n=4096 (128,512) device ns/pair | wall ns/pair | n=2048 (256) device ns/pair | wall ns/pair |
|---:|---:|---:|---:|---:|
| 1,600 | 37.4 | 167 | 27.7 | 134 |
| 6,400 | 18.6 | 48 | 7.5 | 34 |
| 25,600 | 3.1 | 11.2 | 2.6 | 9.5 |
| 102,400 | 1.6 | 4.0 | 1.7 | 4.2 |
| 204,800 | 1.4 | 2.9 | 1.4 | 3.1 |
| 600,000 | 1.3 | 2.7 | 1.3 | 2.7 |

- **Saturation is about 200k pairs per call.** Production fine calls (80k) run at ~2.9 device
  ns/pair in the ladder, ~2x saturated.
- **Wall per pair stays about 2x device per pair even when saturated.** Every call syncs at
  its end, so host work (Python dispatch, readback unpacking) is not overlapped with device
  work.
- **The CPU reference is one core** (the library's CPU path is single-threaded). It does
  ~42 ns/pair on the same fine calls: 0.366 s for 108 calls of ~80k pairs.

## GPU vs one CPU core, and what prevents 10-100x

Ladder, 1 top, 3 segments (2 steady), interleaved runs (GPU, CPU, GPU, ...), min of 5, steady
seconds. This is the final state after rebasing onto main at f9717a1, which brought device-priced
chains and block sizes: CUDA now runs the fine banks at n=4096 with a band-256 gate.

The CPU column is one core. The library's CPU path is single-threaded, which I confirmed by
pinning a run with `taskset`.

| stage | CPU 1 core | CUDA --resident | wall ratio | CUDA device time | device-only ratio |
|---|---:|---:|---:|---:|---:|
| middle | 0.216 | 0.0121 | **18x** | 0.003 | ~70x |
| fine | 0.330 | 0.091 | **3.6x** | 0.025 | ~13x |
| asym | 0.011 | 0.016 | 0.7x | 0.004 | ~3x |
| total (TIRT) | 12.6e6 | 59.1e6 | **4.7x** | | |

`--check cpu` on the final state:
- SNR on common peaks within 8e-6;
- asym peak sets identical;
- no CPU-only fine peak above the gate margin (threshold + 0.25);
- 12 GPU-only fine peaks above the margin. These are loud peaks the CPU's own chain dismissed:
  the CPU and GPU now price different chains. The same bank with one pinned chain is
  identical on both devices.

After rebasing onto 16ac4ae, which brought batched `filter_series_many` (now the ladder's
default) and main's device-resident middle buffer, the numbers are min of 5, interleaved:

| ladder mode | middle | fine | asym | TIRT |
|---|---:|---:|---:|---:|
| CPU 1 core | 0.160 | 0.328 | 0.009 | 14.2e6 |
| CUDA, batched (default) | 0.0118 | 0.129 | 0.016 | 45.1e6 |
| CUDA, `--no-batch` | 0.0119 | **0.090** | 0.016 | **60.1e6** |

On CUDA, batching is 1.4x slower, the opposite of Vulkan. A deferred call skips the
one-submission grouped hierarchical path (`hier_peaks_grouped` is used only when not
deferred), so each fine call becomes 3 window submissions. Forward launches go from 168 to
308 per steady stage, and forward device time from 3.9 ms to 25 ms (4 streams overlapping
inflate per-launch event time, but the wall time confirms it). The open item is to make the
grouped hierarchical path deferrable.

What binds, in order:

1. **Host time is ~3/4 of the fine stage's wall time.** 0.091 s wall against 0.025 s
   device. Each fine call costs ~0.6 ms of host Python on top of ~0.23 ms of device work:
   - layout and records;
   - about 13 launch calls through ctypes;
   - readback copy, `nonzero` and peak packing in `filter_series`.

   Nothing overlaps, because each `filter_series` waits for its own result. Device-priced
   chains do not see host cost: the model prices device ns only.
2. **Production calls are below saturation.** At 80k pairs per call the device runs at ~2x
   its saturated ns/pair, and each kernel at 4-30 us is launch- and tail-bound.
3. **Kernel efficiency at saturation is still low.** At 1.3 ns/pair, n=2048 with 200
   templates is ~0.3 TFLOPS-equivalent of FFT work. The gate kernels run at <1% of fp32, the
   forward FFT at 54% of bandwidth, the refine family spills.

The structural fixes, in that order:
- One submission for many banks. The ladder's 27 fine banks of a top over the same middle
  output form ~2.2M pairs, past saturation. The same structural fix the Vulkan track found.
- Asynchronous `filter_series`, so the host of call k+1 overlaps the device work of call k.
- A CUDA graph per record, which replaces ~13 cuLaunchKernel calls with one launch.
- Then the kernels:
  - refine without spills: 128-thread blocks, or the `_lds32` geometry;
  - a coarse gate at full occupancy;
  - forward FFT fused into the coarse pack, deleting a pass over the spectra.

## Optimisations, measured on the bench (all verified with --check cpu)

| change | before | after |
|---|---|---|
| Correct paths at all (bring-up) | bench crashed at the middle stage | runs; check passes (see report) |
| Device-resident middle -> fine (`correlate_series(out=empty_shared)`, row views bound in place) | middle 0.29 s, fine 0.38 s | middle 0.04 s, fine 0.20 s |
| Block starts via pinned staging -> device (not managed memory); managed series span prefetched | forward_4096 139 us/launch | 15-20 us/launch |
| Coarse gate: rows padded to whole PPG groups, PPG/TILE chosen by occupancy (p8/p16 builds) | tierb_64_c16 237 us/launch, occ 0.04 | tierb_64_c16p16 12 us, occ 0.67 |
| Middle block size priced on the device with device-resident output | n=32768: 3.19 ms/launch, 504 B spill | n=16384: 0.59 ms/launch |
| Grouped hierarchical windows: one submission per fine call (was 3) | fine 0.092 s | (included below) |
| Capacity-keyed records, grow-only series pools (no per-call reallocation) | 55/195 record lookups allocated | 15/174 (each plan's first use) |
| Net, ladder --resident (before the rebase) | TIRT 26.5e6 | 60.1e6; fine 0.075 s |
| After the rebase: GPU cost calibration read 0 ns on CUDA (`_timing` switch not honored) | fine 0.16-0.25 s, loud peaks dismissed | fixed: fine 0.09-0.10 s |
| ct0 packed to fp16 on every call by the resident-template cache | 1.59 ms/call host | 1.34 ms/call |
| Final, ladder --resident, min of 5 | | **TIRT 59.1e6** (CPU core 12.6e6) |

## Falsified, or not worth it

- **`cuMemcpyAsync` straight from managed memory** for the block starts: 144 us per copy, worse
  than letting the kernel fault. Pinned staging first: 5.5 us.
- **Host-preferred (`cuMemAdvise`) output for the middle stage.** Every GPU write crosses
  PCIe; 216 MB per call took 33 ms. Device-resident output: 0.6 ms.
- **The 32768-point middle transform on CUDA.** A single-block 32768-point FFT needs the whole
  256 KB register file on sm_89 and spills 504 B per thread. 16384 with more blocks wins
  5.5x. The CPU-side cost model had priced it cheapest only because the calibration's
  output-transfer cost swamped kernel differences.
- **cuFFT.** Not adopted, and not measured against the fused kernels, so this is an argument,
  not a result. The fused kernels never write the spectrum products: product, inverse
  transform and peak search are one kernel, and the coarse gate works on 64-512 point bands.
  cuFFT would materialise each transformed pair's correlation in memory (write plus read,
  ~16 B per sample) instead of reducing it in registers. The one place it could win is the
  forward series FFT, which is already at 54% of bandwidth.

## Not yet done

- No ncu counters (no admin). Achieved occupancy, cache hit rates and stall reasons are
  unmeasured.
- No refine survivor attribution in the grouped path, so refine rows have no rate.
- The A100 check (sm_80) is outstanding. The occupancy-based coarse choice and the
  register cap (65536/threads) are device-queried, not sm_89 constants.

## Phase 2 (2026-10-09): realistic gating, host overhead

All numbers here use the realistic bench data:
`ladder --profiles ladder_profiles_H1.npz --pure`, with per-top reference profiles. The gates
refine ~0.5% of pairs, against ~75% with the old generic profile, so earlier numbers in this
document were partly refine-dominated.

Runs are interleaved (CPU, GPU batched, GPU `--no-batch`), min of 5, steady seconds, on main
1b9b856 plus this branch.

| | middle | fine | asym | TIRT |
|---|---:|---:|---:|---:|
| CPU, 1 core (autotune on) | 0.160 | 1.003 | 0.009 | 6.0e6 |
| CUDA before phase 2, batched / `--no-batch` | 0.012 | 0.184 / 0.159 | 0.020 / 0.022 | 32.7e6 / 36.5e6 |
| CUDA now, batched / `--no-batch` (autotune on) | 0.012 | 0.167 / 0.116 | 0.029 / 0.017 | 33.9e6 / 48.9e6 |
| CUDA now, batched / `--no-batch` (`MF_AUTOTUNE=0`) | 0.012 | **0.055** / 0.063 | 0.029 / 0.016 | **73.4e6** / 76.7e6 |

`--check cpu` passes in all four modes: identical peak sets, SNR within 1.8e-5.

**CUDA against one CPU core:**
- Per job, with steady chains: 12x by templates-in-real-time.
- Middle: 13x. Fine: 18x.
- Asym (follow-ups): 0.3-0.6x. These are small single-template calls; with the default
  `MF_SINGLE_DEVICE=auto` they are measured and moved to the CPU, and `--pure` forbids that.

**Autotune changes the steady segments, not the device code.** With the default
`MF_AUTOTUNE=1`, each fine plan rotates candidate chains on real calls for many calls (2 per
segment per bank). So the bench's "steady" segments still contain trial calls, records for
chains about to be discarded, and pool rebuilds.

What changed in phase 2 (fine stage, `MF_AUTOTUNE=0`, `--no-batch`):

| change | before | after |
|---|---:|---:|
| Sparse peak readback (`compactPeaks` on device; `_SparsePeaks` up to `filter_series`) | 0.159 s | 0.117 s |
| CUDA graphs for `hier_peaks` / `hier_peaks_grouped` (~20 launches -> 1 `cuGraphLaunch`): grouped-call host time 240 -> 45 us | 0.101 s | 0.063 s |
| Deferred calls keep the one-submission grouped path | batched 1.4x slower than `--no-batch` | batched 0.055 vs `--no-batch` 0.063 |

**What binds now.** Fine stage, `MF_AUTOTUNE=0`, `--no-batch`, per fine call:

| | per call |
|---|---:|
| wall | ~0.8 ms |
| device | ~0.33 ms |
| waiting in `_sync` | ~0.24 ms |
| host Python | the rest, spread over many small layers |

The host Python covers `filter_series`, layout, `run_series` and the forward call; that
layering is shared code.

Device time is ~60% the coarse gate. `tierb_1024_c16p2` runs at 65 µs per launch, ~22 TFLOPS
fp16-equivalent: 15-30% of the fp16 rate. The rest is refine, at ~17 µs per launch for a few
hundred survivors: per-block FFT latency, with the 288 B/thread spill still there, plus the
forward FFT.

**Open items:**
- CUDA follow-up items: an equivalent of Vulkan's `peaks_items`, so batched follow-ups are
  one submission per template group. Batched asym is 0.029 s against 0.016 s per call.
- Refine spills and per-block FFT latency.
- A smaller coarse gate cost, by occupancy and by fusing the forward FFT into the gate's pack.
- One fused multi-bank submission per segment. It needs a multi-bank API that skips per-bank
  Python, because host time is now ~60% of wall.

## Phase 3 (2026-10-09): follow-up items, no local arrays, measured coarse variant

### How the bench was run
`ladder --profiles ladder_profiles_H1.npz --pure --segments 4`, with main's default
`--warmup 2`, so 2 steady segments. Runs are interleaved (CPU, main 0bc93f8, this branch),
min of 5, steady seconds.

### Results

| | middle | fine | asym | fine+asym | TIRT (median) |
|---|---:|---:|---:|---:|---:|
| CPU, 1 core | 0.162 | 0.993-0.999 | 0.017 | 1.01 | 4.5e6 |
| main, batched, `MF_AUTOTUNE=0` | 0.012 | 0.028 | 0.039 | ~0.07-0.15 | 76.2e6 |
| this branch, batched, `MF_AUTOTUNE=0` | 0.012 | 0.050 | **0.0155** | 0.065-0.079 | **90.4e6** |
| main, `--no-batch`, `MF_AUTOTUNE=0` | 0.012 | 0.052 | 0.032 | 0.084 | 65.6e6 |
| this branch, `--no-batch`, `MF_AUTOTUNE=0` | 0.012 | 0.045 | 0.029 | 0.073 | 80.8e6 |
| main, batched, autotune on | 0.012 | 0.072 | 0.040 | 0.112 | 53.4e6 |
| this branch, batched, autotune on | 0.012 | 0.067 | 0.015 | 0.082 | 71.5e6 |

**Read fine and asym together on main.** Main's batched fine is sometimes 0.028 s because its
follow-ups fall back to per-call submissions, and those wait for the fine batch: the wait is
billed to asym. Per run, main's fine+asym varied from 0.069 to 0.146 s; this branch's from
0.065 to 0.079 s.

**Batched follow-ups now beat the CPU:** 0.0155 s against 0.017 s for one core.

`--check cpu` passes, with autotune on and off: identical peak sets, SNR within 2.6e-5.

### What changed

| change | effect |
|---|---|
| CUDA `peaks_items` (`items_async`) and `forward(rows=)` (`forward_rows`) | Batched follow-ups no longer fall back to per-call submissions: forwards 43 -> 13 and readbacks 92 -> 26 per stage. Output buffers are per device, not per Context: each bank's follow-up plan is its own Context, so per-Context buffers meant an allocation on almost every call |
| The CUDA build forces `[unroll]` to `[ForceUnroll]` (`tools/build_ptx.py`; shared source unchanged) | Slang had emitted the multi-bin peak loops as plain loops, so `myMag`/`myBin` lived in local memory: 288 B/thread and ~110 local loads. Now 28 B, the kernel context. `tierb_2048` 1.62 -> 0.54 ms, `refine_2048` 1.70 -> 0.63 ms, `tierb_4096` 1.25 -> 0.63 ms, `refine_4096` 1.27 -> 1.12 ms (same shapes, every pair refined) |
| Coarse gate variant chosen by measurement, once per device and band | The occupancy ranking had picked untiled variants. Tiled ones are 1.3-1.5x faster: band 256 71 -> 49 µs, band 1024 364 -> 287 µs at 84k pairs |

### The coarse gate against its target

Coarse gate rates at 84k pairs, best variant per band:

| band | rate |
|---:|---:|
| 128 | 14 TFLOPS |
| 256 | 21 TFLOPS |
| 512 | 15 TFLOPS |
| 1024 | 17 TFLOPS |

That is 10-15% of the packed-fp16 rate (2 x the 72.7 TFLOPS measured fp32 FMA). It is
**not** at the 50% target. The kernel is a radix-16 FFT across register, shared-memory
exchange and barrier stages, with 62-112 registers. Reaching 50% means a different kernel
design: tensor-core or warp-shuffle transforms, and fewer exchange passes. It is the largest
device-side item left.

### What binds now
Per fine call (`--no-batch`, `MF_AUTOTUNE=0`):
- device ~0.27 ms;
- wall ~0.4 ms.

The remainder is host Python, mostly in the shared series path. On the CUDA side the
remaining host costs are the forward call (~55-75 µs), a graphed hierarchical call
(~45 µs), and waits.

### Graph cache and the use-after-free pattern
The CUDA graph cache is keyed on every bound buffer address plus the shapes and parameters.
A freed address that is reused therefore maps to a graph whose captured parameters are
exactly the current buffers, so an address recycled after a free (the ABA case behind main's
fused-recording bug) replays correctly. Graph caches are per record and are destroyed with
it.

## Phase 6 (2026-10-10): arithmetic-intensity accounting on the L40S, band-1024 regression

### Measured workload, one fine segment
Production bank (bank3), `--pure --profiles`, `MF_AUTOTUNE=0`, main 0623b71 + this branch. Counts
from wrapping the backend calls over the two steady segments (`acct.py`), device times from
`ladder --timing` (graphs off while timing, so per-launch overheads are slightly inflated).

- 24,866 data blocks of n = 2048 (the same segment the Vulkan accounting used), 4.34M pairs,
  54 grouped calls (one per bank and detector).
- Chain (512,) on every bank: one fp16 tier at band 512, no second tier.
- Refined pairs: 7,254.

### Per segment

| Phase | Flops | DRAM bytes | Device time | Achieved | Bound |
|---|---|---|---|---|---|
| forward (2048) | 2.8 G | 815 MB (16 KB in + 16 KB out per block) | 1.25 ms | 652 GB/s | **DRAM**, at the 623 GB/s stream ceiling |
| pack_coarse (band rows to half2) | ~0 | ~150 MB (4 KB in, 2 KB out per row) | 0.75 ms | 200 GB/s | launch/latency (162 small launches) |
| coarse0 (band 512, fp16) | ~117 G (27k / pair) | ~50 MB + templates from L2 | 6.65 ms | 17.6 TFLOP/s | **ALU**, 20% of the 87.9 TF half2 rate |
| refine (2048) | 0.9 G | ~25 MB | 1.95 ms | 0.5 TFLOP/s | latency (7k pairs over 54 calls) |
| compact, readback, upload, compact_peaks | – | small | 2.0 ms | – | launch/latency |
| **Total** | **~121 G** | **~1.05 GB** | **~12.5 ms** | | |

- **Ridge points:** 87.9 TF / 0.623 TB/s = 141 flop/B (half2), 117 flop/B (fp32). The segment as
  a whole sits at ~115 flop/B, just left of the ridge, and as on the 8060S the forward is
  ~80% of the DRAM bytes for ~2% of the flops.
- **But the share of TIME differs.** The L40S has 2.4x the 8060S's bandwidth, so the
  DRAM-bound forward is 10% of device time here (1.25 of 12.5 ms), against 38% (4.7 of
  12.5 ms) on the 8060S. The fused forward+coarse0 design (vulkan-8060s-roofline.md §12)
  removes at most the forward and the pack: ~2.0 ms, **~1.19x on device time**, not 1.5x.
  Option (a) alone (write only the tier band, half2, from the forward) removes the pack
  launches and ~40% of the forward's bytes: ~1.25 ms, ~1.1x.
- **The device is not the binding constraint.** Segment wall time is ~28 ms with timers on
  (~15 ms off) against ~12.5 ms of device work: the job is still host-bound, so none of
  these show end to end until per-call host cost falls (gatechain host-cost pricing, the
  remaining host items below).
- **Where the device time is:** coarse0 is 53% of it at 20% of the half2 rate. That, not
  DRAM, is the largest device lever on this part (the warp gate reached 24-34% on the same
  kernel shape, phase 4).

### Band 1024: the twiddle table
The SPIR-V coarse prelude (phase 5 fold) brought the fp16 twiddle table (`COARSE_TWT`) to CUDA.
Measured per variant, ns/pair, same session (table / no table):

| band | best no-table | best table | tiled p2t2 no-table / table |
|---|---|---|---|
| 64 | 0.94 | 0.95 | – |
| 128 | 0.96 | 0.94 | 1.13 / 1.13 |
| 256 | 1.13 | 1.15 | 1.13 / 1.19 |
| 512 | 1.75 | 1.81 | 1.75 / 1.88 |
| 1024 | 4.70 | 4.80 | **4.92 / 6.81** |

The table costs band 1024's tiled build 38%: its table is 32 loads per level per lane, against
2-4 at the smaller bands. `build_ptx.py` now builds both (table variants suffixed `w`) and the
measured coarse choice picks per band; on this part it picks the table only where it is even.
Band 1024's tiled build is then no worse than untiled (4.92 vs 4.70), so nothing is excluded.

### Host costs (steady fine stage, unprofiled perf_counter wraps)

| Item | Host time | Finding |
|---|---|---|
| cyclic GC | one full (gen 2) collection per ~2 segments, **10.9 ms** each | the setup heap (~37k tracked objects: modules, functions, the bank's plans) is rescanned; it is not the per-call code |
| `filter_series` | 265 us/call (177 us with the heap frozen) | 108 calls per segment |
| `hier_peaks_grouped` | 159 us/call (67 us frozen) | the GC pauses landed in its allocations (`_tail` 102 -> 6 us) |
| `forward` / `_prefetch` | 66 / 24 us per call | prefetch is required: `MF_CUDA_PREFETCH=0` made the segment 2.7x slower |
| first-use flat plans (`_gpu_set`) | ~6 ms per segment while new groups get follow-ups | warm-up, bounded by the bank's group count; not a steady cost |

`gc.freeze()` after setup (what an application does once its banks exist; `LADDER_GC_FREEZE=1`
in ladder) measured, min/median of 5 interleaved 4-segment runs:

| | segment, default | segment, frozen |
|---|---|---|
| `MF_AUTOTUNE=0` | 0.112 / 0.133 s | 0.099 / 0.100 s |
| autotune on | 0.140 / 0.141 s | 0.125 / 0.127 s |

10-24% end to end, more than any remaining per-call item. It is a process-wide decision, so it
belongs to the application (pycbc, after building its banks), not to the library.

The prefetch could be skipped for spans the device itself wrote (the middle output), but a
host read of those pages in between (pycbc reads the middle series for other statistics)
migrates them back, and a kernel then faults them in at the 2.7x cost above. Not done.

## Phase 7 (2026-10-10): tensor-core coarse gate

`src/gpu/coarse_tc.cu`, built by `tools/build_ptx.py` (`coarse_tc_<band>_w<warps>.ptx`,
compute_80) and offered to the measured coarse choice next to the Slang variants.

**Design.** Band B = 16 M as a two-stage matrix DFT: A = X . F_M (16 x M by M x M), the twiddle
W_B^(n1 k2) applied to the stage-1 accumulators in registers, then Z = F_16 . C (16 x 16 by
16 x M), each complex product four real `mma.sync.m16n8k16` (fp16 in, fp32 accumulate; a
negated imaginary DFT matrix keeps all four accumulates). Stage-1 operands are read straight
from global memory into the A fragments; the DFT matrices and twiddles stay in registers for
the warp's life (persistent warps, 8 blocks per SM: the block's setup of ~1.5k sincos
amortises over the slots). Only C crosses shared memory (`ldmatrix.trans` for the stage-2 B
operand). The window maximum, its value and the energy for the bound come from the stage-2
accumulators in registers. Same interface and ragged 2-template slots as the Slang coarse
kernel; fails open on a non-finite value. Band 128 (M = 8) does not fit: stage 1's k
dimension is M and the instruction's is 16, so half of every product would be padding --
not built. Band 1024 (M = 64) needs 4 x 8 x 3 x 2 = 192 registers of F_M fragments alone.

**Exactness.** Against float64 on the fp16-rounded inputs, 8192 pairs per band over the
gate_margin families: no elected lag differs except within the error (ties); |error| at the
lag in u rms(y) units mean 0.76 / 0.71, std 0.40 / 0.39, max 3.31 / 5.19 (bands 256 / 512)
-- smaller than the Slang radix-16 tier's (sigma 1.8 / 2.2), as the products accumulate in
fp32. The error magnitude has a heavier tail than a Rayleigh fit, so its kappa is not z x
std: it is set at twice the largest error seen (margin use < 0.5), kappa 7.0 / 10.5
(`COARSE_TC_SIGMA`, `tools/cuda_tc_sigma.py`). `tests/test_cuda_c16_bound.py` checks the
bound covers the exact maximum with margin use < 0.5 on these kernels too.

**Speed** (ns per pair, 131k pairs; the mma.sync m16n8k16 f32-accumulate ceiling measured
on this part: **365 TFLOP/s**):

| band | tensor-core | its tensor rate | Slang best (65k-pair batch) |
|---|---|---|---|
| 256 | 0.73 | 90 TF/s, 25% of 365 | **0.56** (p8 t2) |
| 512 | 1.60 | 123 TF/s, 34% of 365 | **1.14** (p2 t4) |

The tensor units are at 25-34% of their ceiling, but the matrix DFT issues 5x (band 256)
to 9x (band 512) the flops of the radix-16 FFT, and the per-pair scalar work (the D conj(T)
products, the twiddle, the C round trip and the maximum: ~150 instructions per lane per
pair) is the same order as the Slang kernel's whole packed-half2 transform. It loses by
25-40% and the measured choice never picks it; it stays a candidate (no hard exclusion),
where a part with a higher tensor:SIMT ratio, or a fused forward feeding it, may pick it.

**The measured choice's batch.** `_time_coarse` timed 16,384 pairs; a fine-stage call is
~80k (4.34M pairs over 54 calls). At 16k pairs launch and setup costs dominate: the Slang
variants measured 0.94 / 1.69 ns per pair at bands 256 / 512 there, 0.56 / 1.14 at 65k.
The choice now times 65,536 pairs; it picks differently at band 512 (p2 t4 rather than p1 t4).

**κ for the tensor-core gate is empirical.** The Slang tiers' κ = z·σ comes from a measured σ and
an assumed Gaussian tail at the 1e-12 per-pair failure target (`coarse_layout.C16_FAIL`). The
tensor-core error magnitude is visibly heavier-tailed than a Rayleigh fit, so that derivation
does not hold for it. Its κ (7.0 / 10.5) is set at twice the largest error seen in 8192 pairs
per band: it meets the margin-use < 0.5 criterion on what was measured, and carries no proven
per-pair failure rate. The same caveat as the Q15 gate's empirical margin. The kernel is never
chosen on this part, so this bounds nothing in production today.

## Phase 8 (2026-10-10): one CUDA graph per segment's fine stage

**What.** `SegmentPlan` (time_domain) on CUDA: the first run of a job set runs as usual, the second
is captured whole into one CUDA graph (`_cudacompute.SegmentGraph`) -- every bank's forwards,
coarse gates, compactions, refines and readbacks -- and later runs relaunch it with one
`cuGraphLaunch` and one wait, then read each dispatch's results. While capturing:
- every Context's streams resolve to the graph's four fork streams (slot k -> stream k mod 4),
  so independent banks still run concurrently inside the graph;
- per-call graphs are bypassed, cross-stream waits use events recorded in the capture only,
  managed-memory prefetches are recorded and issued by the replay;
- every device and pinned address the captured work touches is collected; freeing or growing
  any of them bumps a generation that makes the graph stale (fallback, re-capture).
Results are read sparse, straight into each job's peak lists in filter_series order.
`ladder` uses it with `LADDER_REPLAY=1` (a measured candidate; the default path is unchanged).

**Correctness.** `tests/test_cuda_segment_graph.py`: replays match filter_series exactly with
data rewritten in place (>=3 replays asserted); a new allocation each segment and an
alternating job set fall back without a stale replay. `ladder --check cpu` exact with
`LADDER_REPLAY=1`, batched and `--pipeline`; `LADDER_VERIFY_REPLAY` reports 0 mismatched jobs
against the per-call path.

**Measured** (production bank, n pinned at 2048 so both runs use the same chain; 10 segments,
8 steady of which 7 replay; `LADDER_GC_FREEZE=1`; `MF_CUDA_BLOCKING_SYNC=1` so host waits sleep
and process CPU counts host work only; 5 interleaved rounds, medians):

| | segment wall | fine stage wall | host CPU per segment |
|---|---|---|---|
| parity/cuda-tc base | 25.3 ms | 12.2 ms | 24.4 ms |
| segment graph | 26.5 ms | 12.3 ms | **18.5 ms** |

Per replayed segment the fine stage's host work is ~1 ms (graph launch, ~0.9 ms of result
parsing for 108 jobs) against ~10 ms of per-call submission before: 54 banks x 2 detectors of
host work became one call's worth. Segment wall does not move: the fine stage is now
device-bound (the graph runs ~9 ms of device work), and the per-call path already hid its host
submission under that device time. The remaining host time per segment is the follow-ups
(~9 ms) and the middle stage (~5 ms).

**Extending it.** `SegmentGraph.capture(run)` captures whatever `run` submits; `SegmentPlan` keys
a graph on the job set's signature. A production job's many top templates x segments of
identical shapes are separate signatures today (one graph each, no re-capture across segments).
Folding several top templates' job sets into one capture, and the follow-ups (`_items_batch`)
into the same graph, are the next steps; both need the follow-up windows to be data (device
arrays the graph reads) rather than host-built per segment.

**Call plans.** This composes with the review agent's call-plan layer rather than replacing it:
the capture run goes through the normal deferred path (call plans included), and a replay skips
the whole Python path. On CUDA the call plans never replay (the backend has no
forward_replay/hier_replay), so for the fine stage the segment graph supersedes them.
