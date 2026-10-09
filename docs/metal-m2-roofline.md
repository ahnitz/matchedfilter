# Metal on the Apple M2: roofline, bench and what binds

Written 2026-10-08 by the Metal track of docs/gpu-parity-plan.md. Machine: Mac mini, Apple M2,
10-core GPU, 24 GB unified memory, macOS 26, Metal compiled at run time from the shipped `.metal`
sources (Command Line Tools only). All numbers are min of repeats on an idle machine (load
average 2-4 from system daemons), warm, with outputs checked against the CPU.

Sections 1-8 are phase 1, measured on the old generic bench data. **Phase 2 (section 0) is on
realistic data and supersedes their bench numbers.**

## 0. Phase 2: realistic data, pure paths

Bench: `tools/ladder.py --bank bank3.hdf --profiles ladder_profiles_H1.npz --tops 1 --pure
--check cpu` (per-top |h|^2/S from the production job, so the gates refine ~0.2% of pairs as in
production rather than ~75%). Steady state is reached only after the chain trials of the first
3-4 segments (fine per segment, ms: 1079, 204, 176, 118, 101, 109, 108, 107, 104, 108), so
steady numbers below are per segment from segments >= 5 of a 10-segment run (`scratch` per-call
timer around filter_series_many), and the ladder's own averages are given beside them.

| stage, ms per segment | CPU, 1 core (NEON) | GPU at phase-2 start (main + shared device) | GPU now | GPU / core |
|---|---:|---:|---:|---:|
| middle (27 templates, 2^20 samples, x2 detectors) | 137 | 73 | **23** | 6x |
| fine (54 banks x 2 detectors, filter_series_many) | 1700 | ~100 | ~105 (steady) | **16x** |
| follow-ups (~25 single-template calls) | ~10 | ~15 | ~10 | 1x |

Ladder averages, 7 steady segments: GPU middle 0.16 s, fine 1.01 s, asym 0.07 s; CPU middle
0.96 s, fine 11.91 s, asym 0.07 s. Check: 557 calls, 0 peaks on one side only, 6 gate-margin
peaks, SNR to 2.6e-5.

Realistic data moved the fine stage's chain from (64, 256) to (256, 512), and with it the kernel
mix:

| kernel (realistic data) | device ms | share | now | target | note |
|---|---:|---:|---:|---|---|
| coarse16 band 256, 2 pairs/group | 1.24 | 60% of fine | **81% of FMA** | >=50% | meets; the packing the runtime picks (2 pairs at band 256) runs clean under realistic gating (8-segment check: no hang, identical peaks); 1/2/4/8/16 pairs agree bit-for-bit in the hardware tests (synthetic gating) |
| refineListed n=512 (2nd tier) | 0.33 | 16% | 29% of FMA | below | next kernel |
| seriesForward n=2048 | 0.25 | 12% | 69% of BW | >=70% | at target (0.266 -> 0.248 ms, split staging) |
| refineListed n=2048 one-bin | 0.17 | 8% | 71% of BW | >=70% | meets |
| full_series n=8192 (middle) | 6.58 per call | 89% of middle | 29% of FMA (was 22%) | below | split staging, see below |
| seriesForward n=8192 (middle) | 0.81 | 11% | 68% of BW | ~target | |

**Where the time goes now.** The fine stage is device-bound: a GPU timeline of one steady
filter_series_many (162 command buffers on 54 contexts) shows the GPU busy 94.5 of 101.4 ms (the
union of command-buffer intervals). The middle is near device-bound (7.5 ms device of 8.8 ms per
call). The follow-ups are host-bound (GPU 1.2 ms of ~8-10 ms; ~0.3-0.5 ms of Python per job).

Note on `--timing` on Metal: contexts run on separate queues concurrently, so the summed
per-command-buffer device time over-counts (fine: 586 ms summed against 94.5 ms of GPU busy in
one segment). Use the busy union, not the sum, for utilization.

### Phase 2 changes, measured (all checked against the CPU)

| change | before | after |
|---|---:|---:|
| One Metal device per process (`_Device`): pipelines compiled once, buffers bind across plans by offset (`shared_views`); before, a fine bank wrapping a row of the middle's device output in a second buffer waited **~60 ms** before its GPU work started | fine 6.05 s over 3 steady segments (generic data, `--pure`), 60 ms from commit to GPU start per call | the ~60 ms stall is gone (timeline); not re-measured on generic data -- realistic-data steady is ~0.1 s/segment |
| SPLIT_STAGE exchange (Metal builds where staging holds half a transform): full_series_8192 | 4.24 ms | 3.05 ms (bit-identical) |
| same, forward_2048 | 0.266 ms | 0.244 ms |
| Middle: device-side zeroing (blit fills), groups left in flight and settled once, stable length sort so groups are contiguous rows (a swapped tie forced a 5 ms scatter copy) | 16.0 ms/call | 8.8 ms/call |
| Follow-ups: grouped (all bin counts) calls defer in filter_series_many | 10.3 ms/batch | 7.7 ms/batch |
| ragged follow-up results split back per bin count (peak order identical to per-count calls) | test failure on main | fixed |

### Phase 2 task list status
1. Middle n=8192 kernel: 22% -> 29% of FMA (split staging). Still the largest kernel below target.
2. filter_series_many on Metal: works and batches; one command buffer per bank-call (1.5 per
   call), no extra submissions. The device is ~93% busy during the fine stage, so a fused
   single-command-buffer submission (task 6) can buy at most the remaining ~7%; not done.
3. Pure-GPU follow-ups: one submission per call and now deferred across the batch; fusing all
   follow-ups into one submission is the remaining step (host Python per job binds).
4. Objective-C messages per dispatch: not reduced. The fine stage is device-bound and the
   middle near it, so this only matters for the follow-ups, where Python layout work per job
   is as large.
5. Shared device per process: done (it was the largest single win of phase 2).
6. Fused multi-bank submission: not done; see 2.

CPU (NEON): not worked on in this phase. The CPU path runs the flat filter at ~38 GFLOP/s on one
M2 performance core (~34% of an estimated 112 GFLOP/s peak); no NEON change was made or measured.

Known issue, not Metal's: GPU cost calibration takes ~28 s on first use per process without
`MF_COST_FILE` (a test that builds a GPU bank spends 30 s in it) and is clock-dependent, so
block-size and chain choices can differ run to run; tests comparing devices peak-for-peak must
pin `fft_lengths`.

## 1. Ceilings, measured

`tools/metal_roofline.py` measures them the same way it times kernels (device time from
`GPUStartTime`/`GPUEndTime`):

| resource | measured | vendor figure | note |
|---|---:|---:|---|
| FP32 FMA | 1554 GFLOP/s | 3.6 TFLOP/s | 32 independent chains, 1024-thread groups; it plateaus here |
| FP32 add (no FMA) | 777 GFLOP/s | -- | the rate a radix butterfly is bounded by |
| copy (read + write) | 93.4 GB/s | 100 GB/s | 256 MB float4 copy |
| read | 94-98 GB/s | | |

The FMA probe reaches 43% of the advertised 3.6 TFLOP/s and does not rise with more chains or
iterations (1494 at 16 chains, 1554 at 32, identical over 0.4 s and 5.7 s dispatches), so 1.55
TFLOP/s is what a compute kernel can expect. Clock and power state could not be read:
`powermetrics` needs root, and `ioreg` (`IOAccelerator` `PerformanceStatistics`) reports only
"Device Utilization %" (96% during the sweep), no frequency. Unlike the shared-power AMD APU, the
measured ceiling did not move between a cold run and a 170 s sustained run, so there is no sign of
down-clocking under these loads, but that is inferred, not observed.

Targets (user, section 6 of the plan): compute-bound kernels >= 50% of peak, memory-bound >= 70% of
bandwidth. Fractions below are given against the MEASURED ceilings (and against the spec where it
matters).

## 2. Per-kernel roofline at the bench's production shapes

`python tools/metal_roofline.py --bank bank3.hdf --reps 20` (top template 4, 27 middle templates,
the largest fine bank: 254 templates of 15-399 taps, n=2048, chain (64, 256)). Each kernel the
library encodes for one ladder call is captured and replayed alone. Work model: 5 n log2 n per
transform + 6 n product + 3 n magnitude/max; bytes = unique rows read once + outputs once (a lower
bound; "per-pair" counts every row read per pair).

| stage | kernel | groups | device ms | share | GFLOP/s | of FMA (meas / spec) | GB/s unique | of BW | bound | roofline |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| middle | fullCorrelationSeries n=8192 (lds32) | 3856 | 6.56 | 71% | 342 | 22% / 10% | 17.9 | 19% | compute | 22% |
| middle | fullCorrelationSeries n=4096 | 4356 | 1.79 | 19% | 657 | 42% / 18% | 45.7 | 49% | memory | 49% |
| middle | seriesForward n=8192 | 241 | 0.55 | 6% | 234 | 15% / 7% | 57.6 | 62% | memory | 62% |
| middle | seriesForward n=4096 | 396 | 0.34 | 4% | 283 | 18% / 8% | 75.5 | 81% | memory | 81% |
| fine | coarse16 band 64, 8 pairs/group | 14860 | 0.31 | 44% | 961 | **62%** / 27% | 5.6 | 6% | compute | **62%** |
| fine | seriesForward n=2048 | 468 | 0.28 | 41% | 187 | 12% / 5% | 54.3 | 58% | memory | 58% |
| fine | compactPairs | 930 | 0.033 | 5% | -- | -- | 57.7 | 62% | memory | 62% |
| fine | packCoarse | 587 | 0.026 | 4% | -- | -- | 87.8 | 94% | memory | 94% |
| fine | refineListed n=256 (tier 2) | 350 | 0.026 | 4% | 170 | 11% | 48.0 | 52% | memory | 52% |
| fine | refineListed n=2048 one-bin | 4 | 0.019 | 3% | 27 | 2% | 6.8 | 7% | (launch) | 7% |
| asym | fusedTierB n=2048, 1 template | 38 | 0.076 | 74% | 66 | 4% | 9.0 | 10% | (size) | 10% |
| asym | seriesForward n=2048 | 38 | 0.027 | 26% | 160 | 10% | 46.5 | 50% | (size) | 50% |

Reading it:
- The fine stage's dominant kernel, the half-width coarse gate, was at 9% of FMA (2.16 ms) before
  this pass and is at **62%** (0.31 ms) after packing pairs into SIMD groups (section 4). It meets
  the compute target.
- The middle stage's n=8192 correlation is the largest kernel on the bench and is at 22% of FMA. It
  runs the 32 KB "portable" staging variant (the tuned 64 KB one cannot build on Apple; see the
  falsified list). It is the next kernel to work on.
- The forward transforms at n=2048 are short (1-2 blocks of 2048 points per window, 468 groups):
  58-62% of bandwidth on a 0.28 ms kernel, with launch and tail effects included.
- The single-template follow-up kernels (38 groups) cannot fill a 10-core GPU; their fraction is a
  statement about the call size, not the kernel.

## 3. The bench: CPU (one core) against the M2 GPU

`python tools/ladder.py --bank bank3.hdf --device {cpu,gpu:0} --tops 1 --segments 4 [--timing]`,
steady segments (3), seconds; the CPU column is the library's single-threaded CPU path on one M2
performance core.

| stage | CPU 1 core | GPU at ad4462b+7539192 (main) | GPU after this track | GPU / core | device / wall (after) |
|---|---:|---:|---:|---:|---:|
| middle | 0.45 | 0.32 | **0.19** | 2.4x | 0.077 / 0.19 |
| fine | 1.04 | 0.55 | **0.26** | 4.0x | 0.13 / 0.26 |
| asym | 0.01 | 0.045 | **0.028** | 0.36x | 0.003 / 0.028 |
| total | 1.50 | 0.92 | **0.48** | 3.1x | |

Check (`--check cpu`, 2 segments): SNR agrees to 1.9e-5 relative. 1 peak is only on the CPU and
12 only on the GPU, all noise peaks of SNR 6.0-6.8 at the threshold: the CPU autotuner picks
3-tier chains (e.g. 64, 128, 1024) and the GPU is capped at 2 tiers with a chain priced by the CPU
cost model (64, 256), so they gate noise differently (plan item E1). With both pinned to (64, 256)
(`scratch` harness, `coarse_band_hz=(64, 256)`), the peak sets are identical over 123 calls and
the SNR agrees to 2.7e-5.

Templates-in-real-time on the GPU after this pass: middle 5.5e7, fine 4.1e7, total 2.2e7.

## 4. What changed, measured before/after (each verified on the bench with the CPU check)

| change | where it bit | before | after |
|---|---|---:|---:|
| 2-tier chains real (were one tier at the 2nd band with its threshold) | correctness | -- | identical peaks to CPU under a common chain |
| async submission real + pipelining enabled on Metal (K=8 slots) | fine, 3 subs/call overlap | 0.57 s (K=1) | 0.47 s |
| coarse gate: 8 pairs per threadgroup (band 64 = 4 threads/pair; SIMD is 32) | tierb_64_c16 kernel | 2.16 ms | 0.31 ms |
|  | fine stage, wall | 0.47 s | 0.29 s |
| middle output written in place (newBufferWithBytesNoCopy over a page-aligned result) + run lists instead of S-long masks | middle call | 47 ms | 20 ms |
| GPU correlation cost priced over ~2^19 samples, not 8 blocks (submit cost made the n=8192/16384 choice flip; 16384 is 2.3x slower) | middle stage | 0.27-0.36 s | 0.18-0.19 s |
| one submission for all bin counts of a follow-up (ragged grouped bins) | asym call | 1.13 ms | 0.52 ms |
| series read in place when page-aligned; kernel-file stats cached | fine call | 2.17 ms | 2.03 ms |

## 5. Device ns/pair against pairs per call

`scratch` sweep, n=2048, 254 templates, synthetic noise (so the hierarchical refine rate is higher
than on the bank), one submission per call:

| pairs/call | hier device ns/pair | hier wall ns/pair | flat device ns/pair | flat wall ns/pair |
|---:|---:|---:|---:|---:|
| 254 | 575 | 2567 | 419 | 2086 |
| 1016 | 246 | 722 | 319 | 719 |
| 4064 | 225 | 344 | 292 | 415 |
| 16256 | 222 | 262 | 288 | 319 |
| 65024 | 136 | 146 | 285 | 294 |
| 260096 | 131 | 134 | 285 | 287 |

One CPU core on the same shapes: flat 3478 ns/pair, hierarchical 1750 ns/pair. At saturation the GPU
is **12x (flat) and 13x (hier)** a core; at 254 pairs per call it is slower than a core (wall), and
4.4x worse on the device than at saturation. The ladder's fine calls are ~1000-4000 pairs per
submission (one window's blocks x one bank), right on the knee.

## 6. What prevents 10-100x a core on the M2

1. **The hardware ratio is ~14x, not 100x.** Measured GPU FMA is 1.55 TFLOP/s; one M2 performance
   core peaks at ~112 GFLOP/s (4 x 128-bit FMA at 3.5 GHz). The CPU path runs the flat filter at
   ~38 GFLOP/s (34% of a core) and the GPU at ~460 GFLOP/s (30% of measured FMA), hence 12x. Even
   at 100% of measured peak on the GPU and the CPU's current efficiency, the ratio would be ~40x;
   at equal efficiency it is ~14x. 100x a core is not available on this part; ~10-15x is the
   realistic target, and the saturated kernels are already there.
2. **Call size.** The bench's calls are too small to saturate: per-call device time is 3-5x the
   saturated rate below ~16k pairs, and each submission costs ~0.15-0.25 ms of commit-to-start and
   completion latency (timeline: commit -> GPU start 75 us, GPU end -> host has result ~100 us).
   The structural fix is the plan's D1/D2: one submission for many windows and many banks
   (the ladder calls 54 fine banks x 2 detectors per segment separately; batching them would put a
   segment's fine stage in a few submissions of ~250k pairs).
3. **Host work per call.** After this pass the fine stage is 50% host (0.13 s device of 0.26 s), the
   middle 60% host (fresh 226 MB result arrays page-fault on first touch, ~10 ms per call, plus
   zeroing outside the windows; a caller passing `out=` avoids it), and the follow-up 90% host.
   The ctypes Objective-C messaging is ~5 us per message and ~60 messages per call.
4. **One kernel below target:** the middle's n=8192 correlation at 22% of FMA.

## 7. Falsified (keep)

- **Radix-32 full-series kernel at n=8192** (256 threads x 32 points, 32 KB staging): 11.3 ms against
  4.2 ms for the shipped radix-16 portable variant, bit-identical output. More registers per
  thread costs more than the halved exchange levels buy on Apple.
- **64 KB staging on Apple:** the tuned Vulkan staging for n>=8192 cannot create a pipeline
  ("Threadgroup memory size (65536) exceeds ... 32768"); confirmed on hardware. The runtime already
  picks the 32 KB build; there is no Apple host on which the two can be compared.
- **More than 8 coarse pairs per group at band 64:** 16 and 32 pairs per group are 0.319 and 0.344 ms
  against 0.310 ms for 8 (and 1.06 / 0.55 ms for 2 / 4). Filling one 32-lane SIMD group is enough;
  the rule picks the smallest packing that does.
- **"SIMD-32 assumptions" in the kernels** (audit item): the wave intrinsics are used only with one
  pair per group and reduce through threadgroup atomics, so they are correct for any SIMD width;
  the Metal compaction uses the non-wave path. No defect; the real cost of SIMD-32 was occupancy
  (fixed above), not correctness.
- **Pipelining alone as the fine-stage fix:** K=8 in flight bought 17% (0.57 -> 0.47 s); the kernel
  packing bought the rest. The submission latency is hidden only while the host is slower than the
  device.
- **Workspace churn (Vulkan finding 2):** on Metal the steady segments allocate ~86 buffers / 14 MB
  per segment (single-template plans and new bin-count shapes), with no evictions; at Metal's
  allocation cost this is under 2 ms of a 150 ms segment. Not a lever here.

## 8. Next steps, ranked by bench share

1. Batch windows and banks into one submission (D1/D2): the fine stage is 162 submissions per 3
   segments at the knee of the ns/pair curve.
2. The middle's n=8192 correlation kernel (22% of FMA, 71% of the middle's device time).
3. GPU chain choice from GPU costs (E1) and more than 2 tiers on GPU: the hierarchical Metal path
   now generalises to N tiers internally; `HierarchicalFilter` passes at most 2.
4. Host: a compiled (not ctypes) encoder, or fewer Objective-C messages per dispatch (argument
   buffers), once batching has reduced the call count.
