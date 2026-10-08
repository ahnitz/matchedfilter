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

What binds, in order:

1. **Host time is 2/3 of the fine stage's wall time.** 0.075 s wall against 0.025 s device.
   Each fine call costs ~0.47 ms of host Python on top of ~0.23 ms of device work: layout,
   records, about 13 launch calls through ctypes, readback copy and peak packing. Nothing
   overlaps, because each `filter_series` waits for its own result.
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
