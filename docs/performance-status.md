# Performance status

As of 2026-10-13, main at cd152843. One page per question: how fast each platform runs the
standard workload, what fraction of its theoretical throughput that is, and what binds it.
Every number below was reported with a gated commit or a parked-platform doc; the source is
given with each. Where no gated number exists, the cell says so rather than estimate.

## The workload and the metric

- Workload: `tools/ladder.py`, the standalone three-level search (top → middle correlation →
  fine hierarchical filter → single-template follow-ups) on a production three-level FIR
  bank, top 1, with `--profiles` H1 (per-top reference spectra; without them the gates refine
  ~75% of pairs instead of production's ~0.2%).
- Segment time: steady wall time per 512 s segment, after the warm-up segments, from a primed
  `MF_COST_FILE` so every arm runs the same layout, chain and screen.
- Fraction: `ladder --roofline` = roofline time / steady wall per segment. Roofline time is the
  sum over stages of max(flops / peak flops at the stage's precision, bytes / peak bandwidth)
  (`python/matchedfilter/_roofline.py`).

## Per platform

| Platform | Segment | Fraction | What binds | Conditions | Source |
|---|---:|---:|---|---|---|
| Vulkan, Radeon 8060S (gfx1151) | ~15.5 ms | 40.9% | host: ~10 ms of host CPU per segment; host and device now overlap (follow-ups on a side queue) | async segment replay, two segments in flight, n=2048; quiet host (load ~5, sclk ~2.2 GHz); 3 alternating rounds | 3c2ec61d; [Vulkan roofline](vulkan-8060s-roofline.md) |
| Metal, Apple M2 (10-core GPU) | ~92 ms | 34.4% | device, GPU ~90% busy: tier-0 gate 40.8 ms of device time per segment, the largest stage (its FFT at 66% of peak); remaining levers measured at a few % each. Parked. | bank3, H1, fused-batch chunk 2 | [Metal roofline §0d](metal-m2-roofline.md) |
| CUDA, NVIDIA L40S | ~11.4 ms | no gated fraction | latency/launch: small grids per launch on 142 SMs | segment graph, two in flight, 8 fork streams, 20 segments | 6e299074; [CUDA roofline](cuda-l40s-roofline.md) |
| ARM CPU, one M2 performance core | ~960 ms | 41.7% | the Q15 screen (467 ms, 51% of the int16 peak; issue-bound, ~80% of peak at perfect issue). Parked. | bank3, H1, shared cost file | dfafc04e; [ARM NEON gate, "Where the ARM CPU is parked"](cpu-neon-fp16-gate.md) |
| x86 CPU, one Zen 5 core | see below | no gated fraction | the Q15 screen | dev2, shared host | 0b6f7885, 16a28f65, 6b15bb83 |
| x86 CPU, one Haswell core (E5-2698 v3) | ~2.5 s | no gated fraction | | turbo off (2.3 GHz basis) | 16a28f65, 6b15bb83 |

Zen 5 details (one core, dev2):
- At load ~12: 468-477 ms per segment after the sparse CPU output (16a28f65).
- The Q15 screen's fused window maximum on 512-bit targets (0b6f7885), measured under heavy
  load (segments 951-1257 ms): Q15 stage -13%, segment -6.5%, every pair faster.

Haswell: 2501-2573 ms per segment (16a28f65); 2505-2518 ms with the streaming-store middle
copy (6b15bb83, -2.5%).

## Caveats

- **dev2 is shared.** Other agents' suites and live searches put it at load 30-55 for most of
  the measurements. The 8060S shares its power with the CPU and drops to ~600 MHz under that
  load (from up to 2.9 GHz), so the same build reads anywhere from the quiet 15.5 ms to several
  times that. Compare only alternating rounds taken together.
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
