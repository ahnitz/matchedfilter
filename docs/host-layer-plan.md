# Host-layer plan: the library is never the slowdown

Status: active. Started 2026-11-27. The log at the end records what has landed.

## Requirement

On every device, the time of a pass over the data is spent in compute kernels:
compiled SIMD code on a CPU, device kernels on a GPU. The library's own host-side
work (Python orchestration, bookkeeping, allocation, waits) is a small and fixed
cost per pass. It does not grow with the number of rows, banks, templates or plans.

The measure is the compute fraction: compute time divided by steady wall time, taken
from uninstrumented runs. On a GPU, compute time is the device-busy time from the
backend's own timers. On a CPU it is the time inside the extension's kernels. Time
spent in a caller's hooks is the caller's and is reported separately.

## Where it stands (2026-11-27)

- Pulsar dense pass on a Quadro RTX 6000: the device is busy about 1% of the pass.
  The rest is Python work per (row, parent) inside the library.
- PyCBC job on the Radeon 8060S: about a quarter of the steady time is the device.
- CPU paths: about three quarters in the C kernel for the pulsar pass; the PyCBC job
  is not yet measured this way.

The baseline for every consumer and device is phase 0.

## Principle

Everything that does not depend on the values of the data is decided once, at setup.
A pass then executes a plan that already exists. There is one mechanism for this,
used by every entry point and every device, and each phase removes the code it
replaces. No path is kept beside its replacement.

## Design

1. **One job description.** A caller describes a whole pass: the hierarchy, the rows
   (channels), the windows, the detection statistic and the false-dismissal budget.
   The low-level entry points build a one-node job and take the same path.
2. **A compiled plan.** Setup resolves the buffer layout (one arena per plan, rows
   contiguous), the kernel for each step, the order of steps and the window geometry.
   The plan is a flat table of numbers. It holds no Python object per row, per bank
   or per template.
3. **Two executors of one table.** The CPU executor is one call into C that walks the
   table. The GPU executor is one recorded command list, replayed with the pass's
   data bound, through the shared command list all backends use. A backend differs
   from another only by properties it reports.
4. **Data-dependent work stays below Python.** Survivor lists, window-bin merging and
   peak collection run in C or on the device. Python receives the peaks in their final
   order. Work a caller decides in its own code, such as PyCBC's follow-up filtering
   from a hook, enters at a callback boundary as a one-step plan.
5. **Tuning chooses among plans.** A trial runs alternative plans on the first passes
   of real data, because synthetic setup trials have mispriced production calls. No
   decision is taken inside the execution of a plan.
6. **Accounting is part of the result.** Every pass reports compute time and host
   time. Benchmarks print the compute fraction and the merge gate checks it.

## What exists to grow from

A study of the code at 45328962 found that the CPU leaf path already has the right
shape: `ap_hmf_sparse_job` with `ap_hmf_run_series_batch_sparse` is an array of jobs
walked by one C call, and `td_followup_batch` does layout, merging and compaction in
C. Both are rebuilt from Python tuples on every call. On a production capture the
PyCBC pass on a CPU is one leaf call per chunk and 92 to 96% of its time is in C.
The table of phase 1 is these structures made persistent and extended to the
correlation and root steps, not a new layer beside them. On a GPU the structures to
grow are the shared `CommandList` and the call-plan replay, which today exist per
context and per plan instead of per pass.

A search with hooks runs one executor call per chunk and then the hooks. A consumer
without hooks can run one call per pass.

## Phases

| Phase | Lands | Removed in the same merge |
|---|---|---|
| 0 | Baseline accounting for each consumer and device; the compute-fraction metric in the benchmarks and the gate | none |
| 1 | The plan table and the C executor for the CPU correlation and leaf paths | Python loops per row and per bank on the CPU |
| 2 | The GPU executor on the same table, on Vulkan, CUDA and Metal; a plan's buffer arena | GPU paths per row, a context per plan, buffers allocated during a pass |
| 3 | A whole hierarchy pass (root, inner nodes, leaves) as one plan; a complex series at the root | Host orchestration between stages |
| 4 | The detection statistic as a plan step; plans reused across bank pieces of one shape | none |

Batching across rows and banks, and buffer management, are delivered by phases 1 and
2. The branches `pulsar/complex-batching` and `unify-buffer-pool2` are retired; the
tests of the first are kept.

## Gate for every merge

- Identical triggers for the PyCBC job on CPU, and on each GPU backend it runs on.
- The compute fraction of every benchmark does not fall.
- No rate regression on one CPU core, on the Quadro RTX 6000, and on the other GPU
  models of the cluster.
- The full suites on CPU and GPU, and CI.

## Consumers the plan must serve alike

- PyCBC (`pycbc_inspiral_fir`): real series from one-sided spectra, gated leaves,
  hooks for signal-consistency tests.
- The binary-pulsar search: complex series, short complex taps along frequency,
  parent filters whose output gates their leaves, a summed-power statistic.

Neither gets a mode of its own. A consumer hands over the widest description and the
library chooses the execution.

## Risks

- The host layer of a library with about 4,900 tests is replaced. Phase 1 is large.
- Data-dependent dispatch on a device depends on what the backend supports. That is a
  reported property; the fallback needs care.
- The baseline may show a cause this plan does not anticipate. The phases are revised
  if so, and the revision is logged here.

## Log

- 2026-11-27: plan recorded. Phase 0 accounting started.
- 2026-11-27: design study. The CPU table grows from the sparse-job batch and the
  follow-up batch. Design points 4 and 5 reworded: caller-decided follow-ups stay at a
  callback boundary, and trials run alternative plans on first passes. The PyCBC CPU
  pass is already 92 to 96% in C on a capture, so phase 1's gain on a CPU is the
  correlation path (the pulsar pass, 76% in C) and the table phase 2 needs. Conversion
  order for phase 1: golden outputs and removal of the tiled cascade that production
  never runs; gated leaf steps; single-template steps; flat steps; correlation steps;
  one table per search chunk.
- 2026-11-27: golden outputs (`tools/golden.py`): every result a caller is handed, on the
  three capture tops (one with follow-ups and an envelope, one with split windows, one with
  an injection job's windows), a small search and the low-level entry points, from a seeded
  cost file with `MF_AUTOTUNE=0`. Two fresh runs of eda1da1a record the same 19,868 arrays,
  and so does the run that seeded the cost file.
- 2026-11-27: the tiled cascade of `correlate_and_filter_many` is not removed: production
  reaches it. A full-data job never does (one middle row of two detectors over a 512-second
  segment's analysed span is about 10 MB, over the 4 MB cap), but an injection job with an
  injection window (`--injection-window 4.5`, as PyCBC's search configuration sets) searches
  each block in a few seconds around each injection, and a top with at most four leaves live
  there fits the cap. On the first capture top with one 9-second window per block it runs in
  all six chunks with four leaves live, and not with eight. It is kept. Tiled execution (middle
  correlation and leaf filtering interleaved per time tile, so the middle rows stay in
  cache) is functionality; what is debt is its separate Python compiler. On the
  injection-window shapes its time in C equals the ordinary path's and results are
  identical on two machines; the two paths differ by under 1% either way, from Python
  preparation the cascade caches and the ordinary path redoes.
- 2026-11-27: tiling becomes a schedule of the one table. The cascade's compiled form
  holds the same information as the step table (leaf jobs, correlation calls per chunk,
  zeroing runs, scales, assembly records, a compile key); what is its own is an ordering
  of steps and buffer roles (a scratch slot per tile, a carry slot for collars, copy
  steps). The 4 MB cap is a disabled path standing in for a tuning decision: forced
  tiling was slower on full-data shapes because the cascade calls the per-block product
  kernel on at most 8 templates per chunk and copies through a scratch, not because
  tiling is. Revised conversion order for phase 1: (1) goldens, done; (2) gated leaf
  steps, with the cascade's leaf binding on the same compiler; (3) single-template
  steps; (4) flat steps; (5) correlation steps, including the cascade's per-chunk
  middle calls, with zeroing and scales in C; (6) one table per search chunk with
  tiling as a schedule, which deletes the cascade's Python compiler in the same merge
  and replaces the cap by a measured choice between the tiled and untiled schedules.
  Before step 6 the goldens gain the retain modes of `correlate_and_filter_many` and
  record every tiling case under both schedules.
- 2026-11-27: conversion step 2, gated leaf steps. `_core.HMFTable` keeps a call shape's
  `ap_hmf_sparse_job`s, compiled once by `_batches._compile_leaf_steps`, and its `run` sets
  plan modes, clusters by shared cache lines, runs each phase and assembles one peak arena;
  the tiled cascade runs its slabs through the same table (`run_slices`). Goldens 0 differ
  from a9f56245. Steady passes on the three capture tops 1.4-2.0% faster, injection-window
  cases 0.4-3.6% faster; the leaf stage's Python share went from 3.6% to 1.7%.
  `HierarchicalSearch.timings["leaf_compute"]` is the leaf stage's compute side.
- 2026-11-27: conversion step 3, single-template steps. A single-template CPU call (a search's
  refilter) is a single-template step of `_core.HMFTable`: a template group's step is compiled
  once and kept by the group, and a call binds its template row, series, windows, bin size and
  threshold; the follow-up kernel runs in the table's run. The per-group Python cache of taps
  and spectra became the group's store of spectra in the extension (256 slots at most), shared
  by every table compiled from the group; `_core.td_followup_batch` is removed. Goldens 0 differ
  from 3ec9157d. About 7,000 fewer instructions a follow-up; the Python of one 0.8-1.6 us less
  (4.0 us in `filter_series`, 16 us in `PeaksContext.refilter`, whose own checks are now most of
  it). `HierarchicalSearch.timings["hooks_compute"]` is the compute side of the hooks' calls;
  on the first capture top with follow-ups it is 75% of the hooks.
- 2026-11-27: phase 0 baseline, compute over steady wall with hooks excluded. One CPU
  core: pulsar pass 86% and 92% (3D and 5D shapes), PyCBC job 93%, search benchmark 97%.
  Radeon 8060S (Vulkan): pulsar pass 51 to 68%, of which about 60% of the device time is
  zero fills; PyCBC job 25%; search benchmark about 77%. Quadro RTX 6000 (CUDA): pulsar
  pass 29 to 32%, 18 to 21% counting kernels only, with 367 submissions and 358 small
  uploads per pass of the 3D shape. Causes: Python work per row and bank in the
  correlation path; dispatch and allocation per call in the GPU leaf (about 37,000 buffer
  allocations in a PyCBC job); device time that is not compute. On a GPU the per-plan
  setup (`HierarchicalFilter._gpu_calibration`, 20.4 s over 1,994 plans) runs inside the
  first leaf call and is booked as leaf time; the PyCBC job's steady time without it is
  10.2 s against 31.3 s on one CPU core. To correct in the accounting: that booking, the
  Vulkan device-busy counter that reads zero in the search benchmark, and the leaf split
  of `tools/job_bench.py`.
- 2026-11-27: a gated leaf run records each step's batch time into its plan's stats in the
  extension (`MatchedFilter.performance_stats` folds them in when read), so a run does no
  Python per step; a GPU bank's single-template call that runs on the CPU goes to the group's
  single-template step directly. Goldens 0 differ.
- 2026-11-27: the real PyCBC CPU job after step 3. A group's store of spectra had been
  allocated whole at its first follow-up (1.4 GB of address space over the job, faulted in
  huge pages, 2.5 s slower); slots are now allocated when a template takes one
  (`_core.SpectrumStore`). Peak memory then still differed between trees by 80 to 180 MB,
  and sampling it through the job showed why: both trees held 130 to 280 MB of dead leaf
  banks a top until the cyclic collector ran, so the peak followed the collector's timing.
  The cycle was step 2's: the compiled leaf steps a bank keeps held the banks of their batch.
  They hold them by weak reference now, and the job's peak is 1.6 GB, as before step 2,
  against 4.2 GB.
