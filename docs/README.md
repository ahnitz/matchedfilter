# Documentation

Start with the [usage guide](usage.md) for installation, array shapes, filter setup and
examples, and the [architecture](architecture.md) for how the library is built: its API,
layers, gate model, cost models and measured choices. The [repository README](../README.md)
is the short introduction.

The documents here are of two kinds:

- **Reference** pages describe the library as it is now. When the code changes, they are
  corrected.
- **Dated logs and history** record a study, an audit, a plan with its log, or a
  measurement, at the date and revision they name. They explain why the code is the way it
  is, and they can describe earlier APIs, rejected approaches and retired switches. They
  are not rewritten; a reference page or a later log supersedes them. Their benchmark
  results apply to their recorded hardware, workload and revision.

Every document in this directory is listed below, once; `tests/test_docs_index.py` checks
that and that every link resolves.

## Reference

### Using the library

- [Usage guide](usage.md): inputs and normalisation, output bins, full correlation, series,
  devices, hierarchical filtering and measured choices.
- [Environment variables](environment.md): every variable the package reads, generated from
  `python/matchedfilter/_config.py`.
- [Python support](python-support.md): supported Python and NumPy versions, with the dates
  versions were added and dropped.
- [Full correlation output](full-correlation.md): `CorrelationFilter`, its two-stage GPU
  path above 2^16, and the memory cost of keeping every lag.
- [Testing Metal on physical Apple hardware](macos-test-machine.md): the procedure, and why
  the CI's paravirtual GPU is not enough.

### How it works

- [Architecture](architecture.md): the public API, the layers, the gate model, cost models,
  measured choices, configuration, and tests and gates, at a named revision.
- [Batched matched filter design](design.md): the fused product, the stored layout and why
  the input is frequency domain.
- [The SIMD layer](simd.md): one kernel source over Highway, the targets a build holds, and
  runtime dispatch.
- [The hierarchical filter](hierarchical.md): gate chains, how the chain and thresholds are
  chosen, and their limits.
- [The resolved plan](resolved-plan.md): what a hierarchical filter settles before it runs,
  and what it guarantees with and without a shared cost file.
- [Reduced-precision gates](reduced-precision-gates.md): the Q15 and FP16 tiers' error
  models, and what checks them.
- [The CPU direct refine](cpu-direct-refine.md): refining survivors by direct correlation
  near the coarse peak, and when it does not apply.
- [Q15 coarse screen](cpu-q15-gate.md): the x86 first tier in int16, with its measurements
  since 2026-10-09.
- [FP16 first gate on ARM NEON](cpu-neon-fp16-gate.md): the ARM first tier in half
  precision, with its 2026-10-09 measurements.
- [Hierarchical search design](hierarchical-search-design.md): `search.HierarchicalSearch`;
  phase 1 is implemented, later phases are proposals (status 2026-10-17).

### Development

- [Tooling map](../tools/README.md): every tool under `tools/` and what it is for.
- [Documentation style](writing-guide.md): the checklist for editing these pages.
- [How to optimise a kernel here](optimization-method.md): account first, find the binding
  constraint, verify every speedup.

## Dated logs and history

### Plans and their logs

- [Gate model and measured choices log](gate-model.md) (2026-09-26 to 2026-10-29; the
  newest sections lead, the rest run in date order from 2026-09-26): one false-dismissal
  budget per plan (search on half the draws, fit on the other), the one simulation, the
  budget split's selection bias and per-plan scatter, the retired tables, chain and
  block-size trials, and the joint trial.
- [A/A rounds: the paired rule's error and power on the CPU](trial-statistics.md)
  (2026-10-29): the null of a paired round measured with an A/A arm (`MF_TRIAL_AA_LOG`) on
  dev2 and dev1, the current rule's false-switch rate, and the error and power of
  group-sequential sign, t and Wilcoxon rules, as support for the D8 decision.
- [Cleanup, robustness and CI plan](robustness-plan.md) (adopted 2026-10-21, with its log).
- [Unification plan](unification-plan.md) (started 2026-10-15, with its log): the shared GPU
  host layer, accounting instead of cost tables, knobs instead of variants.
- [Converging the CPU and GPU paths](convergence-plan.md) (2026-10-16).
- [Hierarchical search memory and interface plan](search-memory-plan.md) (2026-10-17).
- [GPU coarse stage: what was done and what next](gpu-coarse-plan.md) (2026-09-25 to
  2026-10-16).
- [GPU parity plan](gpu-parity-plan.md) (2026-10-08, with its log).

### Performance snapshots and platform studies

- [Performance status](performance-status.md) (2026-10-20, at 30486ecb): segment time,
  roofline fraction and what binds, per platform.
- [Vulkan on the Radeon 8060S](vulkan-8060s-roofline.md) (2026-10-09 to 2026-10-13):
  ceilings, accounting and the coarse kernels.
- [Metal on the Apple M2](metal-m2-roofline.md) (2026-10-08): roofline, bench and what binds.
- [CUDA on the NVIDIA L40S](cuda-l40s-roofline.md) (2026-10-08): per-kernel roofline.
- [Cross-platform review](cross-platform-review.md) (2026-10-13): which mechanisms each
  backend had and what transfers.
- [CPU and GPU timings at every supported size](local-device-timings.md) (2026-09-26, at
  bdfdad6).
- [Zen 5 instruction notes](machine-notes.md) (2026-09-22): measured issue rates; a
  starting point, not truth.

### CPU studies

- [Gate execution order](cpu-gate-order.md) (2026-10-15; superseded 2026-10-22, when the Q15
  screen became the first tier's gate).
- [Q15 tail packing](cpu-q15-tail-packing.md) (2026-10-14): filling partial AVX-512 template
  batches with independent data blocks.
- [CPU survivor processing](cpu-survivor-performance.md) (2026-10-14): pooled inputs, the
  Q15 maximum and survivor compaction.
- [Avoiding CPU work](cpu-work-avoidance.md) (2026-10-14 to 2026-10-22): preparing later
  tiers only when needed, Q15 lane packing, and a rejected shared-subspace screen.
- [CPU levers](cpu-levers.md) and [CPU levers against the consumer](cpu-levers-consumer.md)
  (2026-10-04).
- [A reduced-rate analytic engine](cpu-structural-plan.md) (2026-10-04).
- [CPU optimization plan and tracking](CPU_OPTIMIZATION_PLAN.md) (2026-10-04).
- [Haswell performance report](MF_LIBRARY_HASWELL_PERFORMANCE_REPORT.md) (2026-10-03).
- [run_series planning review](planning_review_run_series.md) (2026-09-28).
- [Haswell coarse-kernel plan](coarse-kernel-plan-haswell.md) (2026-09-27).
- [Haswell series grouping and shared execution policy](haswell-series-grouping.md)
  (2026-09-26 to 2026-09-27, exploratory branch).
- [Haswell library-only replay](haswell-library-replay.md) (2026-09-26).
- [A narrower coarse pass](coarse-narrow.md) (2026-09-21 to 2026-09-26).
- [CPU coarse-stage broadcasts](cpu-coarse-broadcast.md) (2026-09-26).
- [CPU int16 and SWAR](cpu-int16-swar-study.md) (2026-09-26).
- [CPU peak scan and codelets](cpu-peak-scan-study.md) (2026-09-26).

### GPU studies

- [GPU forward FFT and shared array storage](gpu-forward-and-arrays.md) (2026-09-26): the
  GPU series forward and host-visible arrays, as built before the shared GPU host layer.
- [Vulkan cached inputs: stale data across windows](gpu-cache-correctness.md) (2026-09-26).
- [Large one-bin GPU kernels](gpu-onebin-kernels.md) (2026-09-26).
- [GPU timing regression and benchmark correction](gpu-performance-regression.md)
  (2026-09-26).

### Audits, 2026-09-26

- [CPU/GPU parity audit](cpu-gpu-parity.md): the parity of the public operations then, and
  the bugs fixed.
- [Coverage follow-up: state transitions and transfer costs](testing-coverage.md), including
  the opt-in performance checks.
- [Library cleanup and calibration contract](audit-cleanup.md).
- [Calibration and optimization regression coverage](calibration-regression-coverage.md).
- [Binary kernels](binary-kernel-audit.md).
- [Class layout and series scheduling](class-execution-audit.md) and
  [its changes](class-execution-changes.md).
- [Execution and dead code](execution-audit.md).
- [Further optimization](optimization-followup.md).
- [GPU peak race](peak-race-cleanup.md).

### Retired plans and notes

- [Historical CPU optimization results](cpu-plan.md) (2026-09-25 to 2026-09-26).
- [Historical GPU implementation findings](gpu-handover.md) (2026-09-25 to 2026-10-13).
- [GPU notes](gpu-notes.md) (2026-09-23 to 2026-10-16).
- [What is left, and what is closed](roadmap.md) (2026-09-21 to 2026-09-26).
- [CPU dispatch and tool cleanup](tooling-cleanup.md) (2026-09-26).
- [Iteration plan](iteration-plan.md) (2026-09-24 to 2026-09-26).

### Measurements

- [HIP versus Vulkan on the 8060S](measurements/hip-vulkan-20260927.md) (2026-09-27).
- [Metal on the M2](measurements/metal-2026-09-26.md) (2026-09-26).
- [M2 and Zen 5 teaser](measurements/m2-teaser-headroom.md) (2026-09-26).
- [Continuous run_series output](measurements/continuous-series-2026-09-26.md) (2026-09-26).
- [CPU cost retune](measurements/cpu-cost-retune-2026-09-26.md) and
  [Radeon 8060S cost retune](measurements/gpu-cost-retune-2026-09-26.md) (2026-09-26; the
  cost tables they retuned were retired).
- [Library path profile](measurements/library-profile-2026-09-26.md) (2026-09-26).
- [Package simplification](measurements/package-simplification-20261020.md) (2026-10-20).
- Teaser fleets: [09-26](measurements/teaser-fleet-20260926.md),
  [09-27](measurements/teaser-fleet-20260927.md), [09-28](measurements/teaser-fleet-20260928.md),
  [10-03](measurements/teaser-fleet-20261003.md), [10-13](measurements/teaser-fleet-20261013.md),
  [10-20](measurements/teaser-fleet-20261020.md).
- Measurement directories, each with its README: [gate execution order](measurements/cpu-gate-order-20261015/README.md),
  [Q15 tail packing](measurements/cpu-q15-tail-20261014/README.md),
  [CPU trial reliability](measurements/cpu-trial-reliability-20261015/README.md),
  [A/A rounds of the CPU joint trial](measurements/trial-aa-20261029/README.md),
  [shared-subspace screening](measurements/cpu-work-avoidance-20261014/README.md),
  and the PyCBC fleet benchmarks of 2026-09-27 and 09-28:
  [alpha6](measurements/pycbc-alpha6-fleet-20260927/README.md),
  [hdev](measurements/pycbc-hdev-fleet-20260927/README.md),
  [hdev 5e56728](measurements/pycbc-hdev-5e56728-fleet-20260927/README.md),
  [hdev c38f24f](measurements/pycbc-hdev-c38f24f-fleet-20260927/README.md),
  [main ce9c828](measurements/pycbc-main-ce9c828-fleet-20260927/README.md),
  [main eecb43c](measurements/pycbc-main-eecb43c-fleet-20260928/README.md)
  (some also hold a RUNBOOK or REPRODUCE file).

### Plans and audits directories

- [Full-correlation implementation plan](plans/full-correlation-implementation.md) and
  [prototype](plans/full-correlation-prototype.md) (2026-09-26; implemented).
- [GPU plan](plans/gpu.md) and [GPU integration plan](plans/gpu-integration.md)
  (2026-09-23; done).
- [macOS on the GPU](plans/macos.md) (2026-09-24).
- [Library health audit](audits/library-health-2026-09-26.md) and
  [GPU teaser throughput investigation](audits/gate-model-2026-09-26/gpu-throughput-investigation.md)
  (2026-09-26); the other directories under `audits/` hold the raw evidence of the audits
  above.

Keep reproducible methods, measured results, and explanations of decisions
in the repository. Put conversation transcripts, temporary status reports,
agent handoffs, and machine access instructions in the ignored `.local/`
directory or outside the checkout. Git history preserves superseded work;
an extra tracked scratch file is not needed to preserve it.
