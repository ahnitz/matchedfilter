# Documentation

Start with the [usage guide](usage.md) for installation, array shapes,
filter setup, and examples. The [repository README](../README.md) is the
short introduction. Every document in this directory is listed below, once;
`tests/test_docs.py` checks that.

## Using the library

- [Usage guide](usage.md)
- [Environment variables](environment.md) (generated from `python/matchedfilter/_config.py`)
- [Python support](python-support.md)
- [Full correlation output](full-correlation.md)
- [Hierarchical filtering](hierarchical.md) and [calibration](gate-model.md)
- [CPU/GPU parity](cpu-gpu-parity.md)
- [GPU arrays and forward transforms](gpu-forward-and-arrays.md)

## How it works

- [Batched matched filter design](design.md) and [the SIMD layer](simd.md)
- [Hierarchical search design](hierarchical-search-design.md)
- [The resolved plan](resolved-plan.md): what a hierarchical filter settles before it runs, and what it guarantees with and without a shared cost file
- [Reduced-precision gates: one error model](reduced-precision-gates.md)
- [The CPU direct refine](cpu-direct-refine.md)
- CPU first tiers: [x86 Q15 screen](cpu-q15-gate.md), [ARM NEON FP16 gate](cpu-neon-fp16-gate.md)
- [Gate execution order](cpu-gate-order.md): defer float rechecks until a more selective gate has run (superseded: the Q15 screen is now the first tier's gate).
- [Q15 tail packing](cpu-q15-tail-packing.md): fill partial AVX-512 template batches
  with independent data blocks while preserving exact screen decisions.
- [CPU survivor processing](cpu-survivor-performance.md): paired kernel and ladder
  measurements for pooled inputs, the Q15 maximum, and survivor compaction.
- [Avoiding CPU work](cpu-work-avoidance.md): preparing later tiers only when needed,
  Q15 lane packing, and measurements that reject a shared-subspace screening approach.

## Performance

- [Performance status](performance-status.md): segment time, roofline fraction and what
  binds, per platform, as of the alpha
- Per-platform roofline studies: [Vulkan on the Radeon 8060S](vulkan-8060s-roofline.md),
  [Metal on the Apple M2](metal-m2-roofline.md), [CUDA on the NVIDIA L40S](cuda-l40s-roofline.md)
- [Cross-platform review](cross-platform-review.md): which mechanisms each backend has and
  what transfers

## Development

- [Tooling map](../tools/README.md)
- [Test coverage](testing-coverage.md)
- [Physical Apple GPU testing](macos-test-machine.md)
- [Documentation style](writing-guide.md)
- [How to optimise a kernel here](optimization-method.md), with
  [Zen 5 instruction notes](machine-notes.md) (measured; a starting point, not truth)

## Plans

- [Cleanup, robustness and CI plan](robustness-plan.md) (2026-10-21, active, with its log)
- [Unification plan](unification-plan.md) (2026-10, with its log)
- [Converging the CPU and GPU paths](convergence-plan.md) (2026-10-17)
- [Hierarchical search memory and interface plan](search-memory-plan.md) (2026-10-17)
- [GPU coarse stage: what was done and what next](gpu-coarse-plan.md) (2026-10-16)
- [GPU parity plan](gpu-parity-plan.md) (2026-10-08, with its log)

## History

Studies, audits and retired plans. They record experiments and the evidence behind
implementation choices, and can describe earlier APIs, rejected approaches, and
historical test counts. Use the sections above for supported behavior. Benchmark
results apply to their recorded hardware, workload, and code revision.

- 2026-10-13: [CPU and GPU timings at every supported size](local-device-timings.md)
- 2026-10: [CPU levers](cpu-levers.md), [CPU levers against the consumer](cpu-levers-consumer.md),
  [CPU structural plan](cpu-structural-plan.md), [CPU optimization plan](CPU_OPTIMIZATION_PLAN.md),
  [Haswell coarse-kernel plan](coarse-kernel-plan-haswell.md),
  [Haswell series grouping](haswell-series-grouping.md),
  [Haswell library replay](haswell-library-replay.md),
  [Haswell performance report](MF_LIBRARY_HASWELL_PERFORMANCE_REPORT.md),
  [run_series planning review](planning_review_run_series.md)
- 2026-09-26 audits: [library cleanup and calibration contract](audit-cleanup.md),
  [binary kernels](binary-kernel-audit.md),
  [calibration regression coverage](calibration-regression-coverage.md),
  [class layout and series scheduling](class-execution-audit.md) and
  [its changes](class-execution-changes.md), [execution and dead code](execution-audit.md),
  [further optimization](optimization-followup.md), [GPU peak race](peak-race-cleanup.md)
- 2026-09-26 studies: [a narrower coarse pass](coarse-narrow.md),
  [CPU coarse-stage broadcasts](cpu-coarse-broadcast.md),
  [CPU int16 and SWAR](cpu-int16-swar-study.md), [CPU peak scan](cpu-peak-scan-study.md),
  [Vulkan cached inputs](gpu-cache-correctness.md),
  [large one-bin GPU kernels](gpu-onebin-kernels.md),
  [GPU timing regression](gpu-performance-regression.md)
- Retired plans and notes: [CPU plan](cpu-plan.md), [GPU handover](gpu-handover.md),
  [GPU notes](gpu-notes.md), [roadmap](roadmap.md), [tooling cleanup](tooling-cleanup.md),
  [iteration plan](iteration-plan.md)
- Measurements: [HIP versus Vulkan on the 8060S](measurements/hip-vulkan-20260927.md),
  [Metal on the M2](measurements/metal-2026-09-26.md),
  [M2 and Zen 5 teaser](measurements/m2-teaser-headroom.md), teaser fleets
  ([09-26](measurements/teaser-fleet-20260926.md), [09-27](measurements/teaser-fleet-20260927.md),
  [09-28](measurements/teaser-fleet-20260928.md), [10-03](measurements/teaser-fleet-20261003.md),
  [10-13](measurements/teaser-fleet-20261013.md),
  [10-20](measurements/teaser-fleet-20261020.md)),
  and the PyCBC fleet benchmarks under `measurements/pycbc-*`; `plans/` and `audits/`
  hold the evidence of the plans and audits above.

Keep reproducible methods, measured results, and explanations of decisions
in the repository. Put conversation transcripts, temporary status reports,
agent handoffs, and machine access instructions in the ignored `.local/`
directory or outside the checkout. Git history preserves superseded work;
an extra tracked scratch file is not needed to preserve it.
