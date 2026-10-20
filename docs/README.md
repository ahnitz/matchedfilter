# Documentation

Start with the [usage guide](usage.md) for installation, array shapes,
filter setup, and examples. The [repository README](../README.md) is the
short introduction.

## Current behavior

- [Full correlation output](full-correlation.md)
- [Hierarchical filtering](hierarchical.md) and [calibration](gate-model.md)
- [CPU/GPU parity](cpu-gpu-parity.md)
- [GPU arrays and forward transforms](gpu-forward-and-arrays.md)
- [Python support](python-support.md)

## Performance

- [Performance status](performance-status.md): segment time, roofline fraction and what
  binds, per platform, as of the alpha
- Per-platform roofline studies: [Vulkan on the Radeon 8060S](vulkan-8060s-roofline.md),
  [Metal on the Apple M2](metal-m2-roofline.md), [CUDA on the NVIDIA L40S](cuda-l40s-roofline.md)
- CPU first tiers: [x86 Q15 screen](cpu-q15-gate.md), [ARM NEON FP16 gate](cpu-neon-fp16-gate.md)
- [Gate execution order](cpu-gate-order.md): defer float rechecks until a more selective gate has run.
- [Q15 tail packing](cpu-q15-tail-packing.md): fill partial AVX-512 template batches
  with independent data blocks while preserving exact screen decisions.
- [CPU survivor processing](cpu-survivor-performance.md): paired kernel and ladder
  measurements for pooled inputs, the Q15 maximum, and survivor compaction.
- [Avoiding CPU work](cpu-work-avoidance.md): preparing later tiers only when needed,
  Q15 lane packing, and measurements that reject a shared-subspace screening approach.
- [Cross-platform review](cross-platform-review.md): which mechanisms each backend has and
  what transfers
- [GPU parity plan](gpu-parity-plan.md) (2026-10-08 plan and its log)

## Development

- [Tooling map](../tools/README.md)
- [Test coverage](testing-coverage.md)
- [Physical Apple GPU testing](macos-test-machine.md)
- [Documentation style](writing-guide.md)

## Research and measurements

Studies and plans added since 2026-09-26:
[CPU levers](cpu-levers.md), [CPU levers against the consumer](cpu-levers-consumer.md),
[CPU structural plan](cpu-structural-plan.md), [CPU optimization plan](CPU_OPTIMIZATION_PLAN.md),
[Haswell coarse-kernel plan](coarse-kernel-plan-haswell.md),
[Haswell series grouping](haswell-series-grouping.md),
[Haswell library replay](haswell-library-replay.md),
[Haswell performance report](MF_LIBRARY_HASWELL_PERFORMANCE_REPORT.md),
[run_series planning review](planning_review_run_series.md).
Measurements: [HIP versus Vulkan on the 8060S](measurements/hip-vulkan-20260927.md),
[Metal on the M2](measurements/metal-2026-09-26.md),
[M2 and Zen 5 teaser](measurements/m2-teaser-headroom.md), teaser fleets
([09-26](measurements/teaser-fleet-20260926.md), [09-27](measurements/teaser-fleet-20260927.md),
[09-28](measurements/teaser-fleet-20260928.md), [10-03](measurements/teaser-fleet-20261003.md),
[10-13](measurements/teaser-fleet-20261013.md),
[10-20](measurements/teaser-fleet-20261020.md)),
and the PyCBC fleet benchmarks under `measurements/pycbc-*`.

The design studies, `plans/`, `audits/`, and `measurements/` record experiments
and the evidence behind implementation choices. They can describe earlier
APIs, rejected approaches, and historical test counts. Use the current guides
above for supported behavior. Benchmark results apply to their recorded
hardware, workload, and code revision.

Keep reproducible methods, measured results, and explanations of decisions
in the repository. Put conversation transcripts, temporary status reports,
agent handoffs, and machine access instructions in the ignored `.local/`
directory or outside the checkout. Git history preserves superseded work;
an extra tracked scratch file is not needed to preserve it.
