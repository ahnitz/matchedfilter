# Performance status

As of 2026-10-20, main at 30486ecb: the baseline after the backend unification (stage U,
[unification plan](unification-plan.md)). One page per question: how fast each platform runs
the standard workload, what fraction of its theoretical throughput that is, and what binds
it. Every number below was measured for this page by the procedure in "Method"; platforms
not re-measured say so and give their source.

## The workload and the metric

- Workload: `tools/ladder.py`, the standalone three-level search (top → middle correlation →
  fine hierarchical filter → single-template follow-ups) on the production three-level FIR
  bank (`fir_three_level_modern_v1_bottomup_cap401.hdf`, 4698 fine templates), top 1, with
  `--profiles` H1 (per-top reference spectra; without them the gates refine ~75% of pairs
  instead of production's ~0.2%).
- Throughput: templates in real time, `ladder.py`'s headline (fine templates × analysed
  seconds × 2 detectors / steady wall).
- Segment time: steady wall time per 512 s segment, after the 2 warm-up segments.
- Fraction: `ladder --roofline` = roofline time / steady wall per segment. Roofline time is
  the sum over stages of max(flops / peak flops at the stage's precision, bytes / peak
  bandwidth) (`python/matchedfilter/_roofline.py`).

## Method

Per platform, `ladderbench.sh` from a fresh `MF_COST_FILE`: three runs of each mode (batched
and `--pipeline`) settle the measured choices (chain trials, layouts, the Vulkan subgroup
size, fused batches); then three alternating plain rounds of each mode give the throughput
(median, range in parentheses), and one `--roofline` run of each mode gives the work counts.
20 segments per run, single-threaded (`OMP_NUM_THREADS=1` and the BLAS variables), Linux
runs pinned to one CPU. Chains are each machine's own measured choice (no `MF_CHAIN_FORCE`),
so platforms run different gate chains; the chain is given with each row. The three plain
rounds agreed to within 1% everywhere except the M2 GPU (8%) and the loaded Haswell node
(4%).

Revisions: 4de7d2ec (gravity-dev3, gravity-dev4, Haswell), 9226028c (Apple M2) and 30486ecb
(gravity-dev2). They differ only in error paths, tests and where the Metal
driver defines its peak model; no measured code path changed between them.

## Per platform

GPU (one device; the host's single CPU thread drives it):

| Platform | Throughput, batched / pipelined | Segment (pipelined) | Fraction (pipelined) | Dominant stage | Chain | Conditions |
|---|---:|---:|---:|---|---|---|
| Vulkan, Radeon 8060S (gfx1151) | 1.74e8 (1.72–1.74e8) / 2.17e8 (2.15–2.19e8) | 16.2 ms | 38.9% (batched 31.5%) | forward (memory) | 256,1024 at n=2048; 1024,2048 at n=4096 | gravity-dev2, load ~1.2 |
| Vulkan, Radeon RENOIR (Ryzen 5 5500U) | 2.33e7 / 2.63e7 (2.62–2.63e7) | 134 ms | 20.1% (batched 17.8%) | tier0 b256 (fp16 compute) | 256,512 | gravity-dev3, load ~1 |
| Vulkan, Intel Iris Xe (i5-13500H) | 1.78e7 (1.78–1.79e7) / 1.83e7 | 193 ms | no peak model (no shader-core count for Intel) | — | 256,512 | gravity-dev4, load ~0.9; subgroup 8 measured |
| Metal, Apple M2 (10-core GPU) | 2.95e7 (2.80–3.06e7) / 3.22e7 (3.17–3.24e7) | 108 ms | 28.2% (batched 26.2%) | tier0 b256 (fp16 compute) | 256,512 | empire, load ~2 |
| CUDA, NVIDIA L40S | not re-measured | ~11.4 ms (2026-10-13) | no gated fraction | latency/launch: small grids per launch on 142 SMs | | 6e299074; [CUDA roofline](cuda-l40s-roofline.md) |

CPU (one core):

| Platform | Throughput, batched / pipelined | Segment | Fraction | Dominant stage | Chain | Conditions |
|---|---:|---:|---:|---|---|---|
| x86, Zen 5 (Ryzen AI MAX+ 395) | 1.06e7 / 1.06e7 | 332 ms | 41.7% | q15 b256 (int16 compute) | 256,512,1024 + Q15 | gravity-dev2, CPU 2, load ~1.3 |
| x86, Zen 3 (Ryzen 9 5950X) | not re-measured | | | | | gravity-dev1: another user's jobs held every core (load ~20) on 2026-10-20; the runs taken then were 6–21× slower and are not used |
| x86, Raptor Lake P-core (i5-13500H) | 5.01e6 / 4.99e6 | 712 ms | 42.7% | q15 b256 (int16 compute) | 256,512 + Q15 | gravity-dev4, CPU 2, load ~1.2 |
| x86, Zen 2 (Ryzen 5 5500U) | 3.71e6 / 3.70e6 | 959 ms | 36.6% | q15 b256 (int16 compute) | 256,512,1024 + Q15 | gravity-dev3, CPU 2, load ~1 |
| ARM, Apple M2 performance core | 3.61e6 / 3.61e6 | 979 ms | 38.0% | tier0 b256 (NEON fp16 compute) | 256,512,1024 | empire, load ~2 (macOS schedules the thread) |
| x86, Haswell (E5-2698 v3) | 1.41e6 (1.40–1.46e6) / 1.42e6 | 2515 ms | 40.6% | q15 b256 (int16 compute) | 256,512,1024 + Q15 | shared cluster node, CPU 50, load 29–42 |

Against the previous page (2026-10-13), none of which is a paired comparison: the 8060S
pipelined segment is 16.2 ms (was ~15.5 ms, 40.9%, from 3 alternating rounds of another
protocol; the stage U paired ladders found the current code at parity with the main before
it on this machine); the M2 GPU is 108 ms at 28.2%
(was ~92 ms at 34.4%, measured with fused-batch chunk 2 under the Metal track's own
protocol: not a paired comparison, so the two do not say whether the code got slower); the
Zen 5 core is 332 ms (was 468–477 ms at
load ~12); Haswell is 2.51 s (was 2.50–2.57 s).

## Caveats

- **dev2 is shared.** Other agents' suites and live searches can put it at load 30–60. The
  8060S shares its power with the CPU and drops to ~600 MHz under that load (from up to
  2.9 GHz). These rows were taken with no other search running; a run that overlapped one
  was discarded and repeated.
- **Without `MF_COST_FILE` the Iris Xe runs at the driver's reported subgroup size.** The
  Vulkan subgroup size is measured only where the result can be kept (`_vksubgroup.py`), so
  a process without a cost file builds at the reported 32, which on the Iris Xe makes
  full-output and peak-only calls 5–30× slower than the measured 8 (hardware comparison,
  2026-10-20). Every number here ran from a cost file.
- **The fraction depends on the locked chain.** Different gate chains do different work, and
  the roofline counts the work actually done. A machine whose trials lock another chain
  reports another fraction for the same code. Quote a fraction with the cost file it ran from.
- **CPU and GPU bandwidth bases differ.** The CPU peak bandwidth is one core's measured
  streaming copy; the GPU peaks are data-sheet formulas, above the measured device ceilings
  recorded next to them in `_roofline._MEASURED` (8060S 256 vs 198 GB/s, L40S 864 vs 623,
  M2 102 vs 93.4). A GPU fraction is therefore against a higher ceiling than a CPU fraction.
- **x86 int16 peak.** The x86 int16 peak counts the vector int16 multiply pipes (9add5b40);
  fractions reported before that used a different int16 basis and are not comparable.

## Where to read more

- [Vulkan on the 8060S](vulkan-8060s-roofline.md)
- [Metal on the M2](metal-m2-roofline.md)
- [CUDA on the L40S](cuda-l40s-roofline.md)
- [ARM CPU (NEON FP16 gate, parked state)](cpu-neon-fp16-gate.md) and
  [x86 Q15 screen](cpu-q15-gate.md)
- [Cross-platform review](cross-platform-review.md): which mechanisms each backend has,
  ranked gaps, and requests per backend.
- [Hardware comparison](measurements/teaser-fleet-20261020.md): the public-call
  workloads (16 and 512 data × 512 templates) on every machine, three runs per
  machine and device, each row the median.
