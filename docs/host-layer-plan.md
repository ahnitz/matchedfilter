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
- 2026-11-27: accounting corrections from the phase 0 baseline. A GPU plan's resolution in
  its first call (`HierarchicalFilter._gpu_calibration`) is booked as setup, not leaf, in
  `HierarchicalSearch.timings`; Vulkan records each submission's device interval, so
  `_gputime.busy` reads the device-busy time there; `tools/search_bench.py` reads it after
  collecting the contexts' logs, prints the device compute fraction and the setup passes by
  stage. On the three capture tops (Radeon 8060S) the setup passes' leaf went from 2.58-2.68 s
  to 1.61-1.63 s and setup from 1.17-1.24 s to 2.16-2.20 s (sum 3.75-3.92 s either way);
  device busy 0.142-0.144 s a pass, 70-74% of the steady wall, equal to the submissions'
  summed device time; peaks identical.
- 2026-11-27: conversion step 4, flat steps. The other every-template CPU calls, a flat bank's
  and a hierarchical bank's below its threshold, are flat steps of `_core.HMFTable`: a
  template group's blocks of one bin count on its ungated `MatchedFilter`, run with
  `ap_mf_run_series` in the table's run (a real series widened to complex there, over the
  samples the blocks read), assembled with the gated steps' assembly. Goldens 0 differ. On the
  CPU, filter_series' loop over groups and bin counts and its Python assembly now run only for
  what the steps decline: plans in a trial or wrapped, correlation and band-limited plans, the
  one-template plan of a single-template fallback; the tiled cascade's
  `_assemble_leaf_results` remains until step 6, and the GPU's calls until phase 2.
- 2026-11-27: conversion step 5, correlation steps. A CPU correlation call is correlation steps
  of `_core.HMFTable`, run by `run_corr`: a step is a template group's run of output rows (the
  plan, the input slot of a real or complex series, the blocks a window reaches and their
  bounds, the output slot and first row, or rows through a scratch for a group interleaved in
  the bank's order), with the runs it zeroes and, for a scaled call, its rows' scale entries
  and runs as side tables; zeroing and scaling (numpy's complex-by-real product) are in C.
  `correlate_series` is one C call for every group, `correlate_series_channels` one for every
  channel and group, the untiled middle correlations of `correlate_and_filter_many` one for
  consecutive CPU jobs, and the tiled cascade's per-chunk middle calls the same steps (one C
  call per template batch, every detector; the kernel's streaming mirror a run-time choice).
  Compiled once per call shape (`_batches._compile_corr_steps`), kept by the first call's bank.
  `HierarchicalSearch.timings["inner_compute"]` is the inner stage's compute side (99.0% of
  inner on the three capture tops). Goldens (with new cases: complex series on interleaved
  groups, the cascade in each retain mode) 0 differ. Binary-pulsar dense pass on one dev2 core
  (load about 5): 3d 29.1-30.5 -> 25.3-26.0 ms a pass, 86.6-87.3% -> 96.1-96.8% inside the
  extension; 5d 379-403 -> 366-374 ms, 91.1-91.4% -> 97.2-97.5%. The PyCBC job is unchanged
  (it was already one middle call per chunk and detector). CORR and leaf steps of a chunk are
  still two tables and two C calls: one table per chunk is step 6.
- 2026-11-27: GPU step 1, item 1: a plan's pipelining slot gets its spectra and starts when a
  call first uses it (`_series_submit`), not eight slots at the first call. On the Vulkan
  PyCBC job peak live device memory 3,240 MB to 1,133 MB (none untouched, against 2,129 MB),
  allocations 74,511 to 46,595; triggers and GPU and CPU goldens identical to d6e7a585.
- 2026-11-27: GPU step 1, item 3: orderly teardown. `_gpuroot.release_roots` (atexit) releases
  the process's device roots while every module is intact; `_Allocation.__del__` leaves an
  allocation still held at finalization to the process's end. The four "Exception ignored" at
  the end of every Vulkan PyCBC job are gone; goldens and triggers identical.
- 2026-11-27: GPU step 1, item 2 (chain choice priced once per bank shape) not landed: on the
  Vulkan job the choice's key without the template count is still distinct for 22,870 of
  24,294 misses (128 profiles x windows x first bands x tier-0 clusters); the CPU's 1,012
  come from the similarity store sharing choices across profiles, which on a GPU holds the
  count in its key. Exact reuse saves 0.25 s of 8.9 s; the 7 s needs count-free similarity
  reuse, which moves which profile a plan's choice is drawn from: a behaviour change, for a
  decision (notes/host-layer/phase2-design-study.md, Step 1 results).
- 2026-11-27: conversion step 6, part A: one table per CPU search chunk. One compiler
  (`_batches._compile_steps`) makes every CPU table: correlation calls first (series slots and
  output slots), then leaf calls; `HMFTable.run` runs the correlation steps, then the leaf
  steps, in one C call. `correlate_and_filter_many` runs its correlations and the leaf calls
  that read them as one table wherever it tiles no cohort (`_untiled_batch`). A CPU search
  whose inner nodes filter leaves only compiles each chunk shape once (key: series length,
  channels, pads, every leaf's windows and needed spans, each inner node's slot state,
  `_InnerBatch.support_key`) and keeps it (`HierarchicalSearch._cpu_chunk`, eight shapes): a
  kept chunk makes no walk and builds no job, binds the root outputs and runs; shapes that do
  not fit one table (the tiled cascade's cohorts, jobs the steps do not take) are remembered as
  declined and go the general way. Not folded in: the root (`Root.real` per channel stays
  before the table; on_series reads it before the walk), and inner nodes with inner children
  (their children read a lane through a copy the walk makes, so such searches keep the walk).
  Goldens 20,039 arrays, 0 differ from ac35c8b2. Capture top 1: 7.816 -> 7.757 billion
  instructions a steady pass; capture tops' Python share of inner + leaf 1.5% -> 0.4%.
- 2026-11-27: conversion step 6, part B: tiling is a schedule of the one table. The cascade's
  execution is `HMFTable` schedule ops (correlation step ranges into a scratch slot, leaf
  block ranges as one batch, stale-scratch and margin zeroing, scaling, copies to the output,
  collars to a carry slot, copies around the last leaf batch's peaks for `retain_radius > 0`)
  run by `hmf_run_schedule` in the table's one C call; the leaf steps it runs (phase -1)
  gather their slices' peaks and are assembled with the others. `_batches._cascade_steps` and
  `_cohort_schedule` compile it from the same steps (`_compile_steps(scheduled=...,
  schedule=...)`); the Python run loop and its helpers, `_assemble_leaf_results` and
  `HMFTable.run_slices` are deleted. A CPU search keeps tiled chunks as it keeps untiled ones.
  Goldens (24,593 arrays, every tiling case under both schedules) 0 differ from ac35c8b2, and
  the two schedules agree on 4,550 arrays. Injection-window cases 6-12% faster a steady pass
  than with part A's tiled cascade (both tiled: against the untiled schedule they tie, part C1),
  their inner + leaf Python share 18.5-28% -> 4-13%. Not folded in: inner nodes with inner
  children (a lane copy step would do it) and the root.
- 2026-11-28: conversion step 6, part C1: where the middle output is written whole, the tiled
  schedule writes it with the untiled correlation steps restricted to each time tile's blocks
  (every run of a group's templates that is one run of the output, the same kernel path) and
  its leaf slabs read it in place; the scratch, copies, collars and the kernel's streaming
  mirror are gone from that mode. Goldens and both schedules 0 differ. Forced on the full-data
  shapes it loses at every tile size: capture tops 1.28-1.58x the untiled pass (1 to 32 MB
  tiles), the real PyCBC CPU job +5% (32 MB) to +15% (4 MB), against 1.05-1.16x for the old
  eight-template scratch schedule. The cycles go to DRAM: L1D fills from DRAM 4-7x untiled's,
  because each tile re-reads every leaf bank's templates (time-major order), while what tiling
  saves is the leaves' read of the middle output, about 2-3% of the pass (a one-row-at-a-time
  order, which keeps the leaf templates, saves 4% of the leaf stage and loses 50% in the
  middle stage re-reading the block spectra). On the injection-window shapes the tiled
  schedule ties the untiled one: inj1, inj4 and the synthetic search within 2.5%, inj2 9% and
  0.4% slower in two runs (their pass-to-pass noise is about 5%); the new tiled schedule is
  within noise of the old there (-4% to +3%). At these shapes on this machine tiling does not
  pay; it was the idea, not the kernel. Part C2 (the cap as a measured choice) waits for that
  reading.
- 2026-11-28: conversion step 6, part C2: untiled is the default schedule everywhere. The 4 MB
  cap (`auto_cohort_cap`) and `TimeDomainFilterBank._TILE_BYTES` are deleted; no shape is
  decided by a size threshold. The tiled schedule stays a schedule of the same table, an
  explicit choice of `correlate_and_filter_many(..., tile_bytes=B)`; a search never tiles.
  Why not the default, from part C1's table (dev2, one core, tiling forced, ratio to the
  untiled pass of the same tree; instructions within 1.4% in every arm, so the differences are
  cycles):

  | shape | in-place 1 / 4 / 16 / 32 MB | scratch 4 / 16 MB | DRAM fills (in-place) |
  |---|---|---|---|
  | capture top 1 | 1.50 / 1.48 / 1.53 / 1.30 | 1.09 / 1.16 | 4.2-6.7x |
  | capture top 2 | 1.55 / 1.58 / 1.58 / 1.35 | 1.14 / 1.14 | 5.2-7.5x |
  | capture top 3 | 1.51 / 1.47 / 1.48 / 1.28 | 1.05 / 1.13 | 4.3-6.8x |
  | real PyCBC CPU job | 4 MB 1.15, 32 MB 1.05 | | 2.2x, 1.5x |
  | injection windows (inj1, inj2, inj4, synthetic) | | the default until now: ties untiled (-2% to +9%, noise about 5%) | |

  Time-major tiles re-read every leaf bank's templates per tile; the leaves' read of the
  middle output from memory, which is what tiling saves, is 2-3% of a full-data pass here.
  One tiled schedule is kept, the scratch one (time tiles of up to 8 templates, collars, the
  rows copied to the output), which serves every retain mode; C1's in-place variant for a
  written output is deleted again (_batches.py 2169 -> 2098 lines, _core.c +17 for the copy
  op it needs; the kernel's streaming mirror stays deleted, the copy op replaces it). Forced,
  this schedule costs 1.06-1.27x the untiled chunks on the capture tops (1, 4, 16, 32 MB:
  1.26/1.07/1.08/1.08, 1.27/1.07/1.09/1.09, 1.22/1.06/1.13/1.13; `tools/schedule_bench.py`,
  chunk time only) and 1.00-1.06x on the injection-window chunks, against 1.28-1.58x of a
  whole pass for the in-place variant: the simpler arrangement is also the faster one. A
  trial between the schedules is not built. It would be added when a shape or machine where
  tiling wins is found: `tools/golden.py schedules` checks that both schedules give the same
  results (the first capture top's chunks, plain and with injection windows, and the entry
  points' cascade cases), and `tools/schedule_bench.py` times them on a capture's chunks with
  a perf recipe for instruction, cycle and memory-fill counts; the cluster's Xeons and older
  CPUs (other cache shapes; an earlier slab-grouping change helped Ivy Bridge and not dev2)
  are where to run it first.
  The default before and after (the injection-window chunks were tiled by the cap and now run
  untiled; dev2 core 13, alternated, 3 rounds at load 3.0-3.4): inj1 0.995, inj2 0.970, inj4
  1.013, synthetic search 0.974, injstd 1.001 of the old wall, instructions 0.993-1.000,
  cycles 0.98-1.04; capture tops 1.001-1.003 (load 4.1-6.6). Real PyCBC CPU job, seeded: old
  70.94/69.85/70.75 s, new 70.43/72.14/70.17 s, triggers identical.
  Part C3: direct `correlate_and_filter_many` calls with `tile_bytes` compile their schedule
  on every call (8-13 ms a full-data chunk, against about 110 ms to run it); with tiling
  explicit-only their callers are tools/ladder.py (`LADDER_TILE_BYTES`), the tests and
  golden.py (schedule_bench.py compiles once and reruns); PyCBC never calls it directly. No
  kept plan is added for them.
- 2026-11-27: GPU step 2, one buffer arena per device for a search's scratch
  (`_gpuhost.Arena`): a search's run leases it, its plans' record buffers and slot spectra and
  starts are sections laid out as first asked, the search keeps the lease between runs, and
  the next search's lease reuses the blocks after releasing what the previous one's plans
  built on them. Every section has a serial of its own. Device-only scratch everywhere;
  host-read, host-written and host-addressed buffers only where the host sees device memory
  in place (not CUDA). Vulkan PyCBC job: 46,595 device buffers to 4,742, peak live 1,133 to
  1,116 MB, wall median 51.1 to 49.4 s, leaf 8.4 to 6.8 s; triggers and GPU and CPU goldens
  identical; host peak RSS 5-15 MB higher, equal with a collection forced after each search
  (collector timing). In the same job the GPU cost model's feed is 0 for every chosen chain,
  and no choice changes with the template count dropped or rounded
  (notes/host-layer/phase2-design-study.md, Step 2 results).
- 2026-11-28: arena fixes after cross-hardware verification. Metal orders work per MTLBuffer
  (hazard tracking), so packed sections of shared blocks made plans' runs wait for each other
  (M2 search_bench 0.926 against main's 0.845 s a pass): a device now reports
  `allocation_hazards` and the arena gives each section a block of its own there (0.844 s,
  peak currentAllocatedSize 2,874 against 4,344 MiB, peaks bit-identical); untracked blocks
  ordered by the driver were measured and not taken (2.2% slower). The recycle tests check
  each property through the device on every arena (they failed on CUDA, whose arena holds no
  host arrays) (notes/host-layer/phase2-design-study.md, Arena fixes).
