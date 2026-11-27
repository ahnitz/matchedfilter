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
