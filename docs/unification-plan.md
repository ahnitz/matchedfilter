# Unification plan: one design, informed by every device

Started 2026-10-15. This plan has three goals: make the library smaller and more uniform
across CPU, Vulkan, CUDA and Metal; make every backend at least as fast as today, by giving
every device every lesson; and replace persisted cost tables with accounting. The log at the
end records progress.

## Ground rules

- **No performance given up.** Every phase is judged by paired ladders on all five
  machines, with interleaved runs and identical trial locks:
  - dev1: Ryzen 5950X, AVX2 CPU;
  - dev2: Radeon 8060S, Vulkan RDNA;
  - dev4: Iris Xe, Vulkan Intel, measured when not shared;
  - L40S: CUDA;
  - M2: Metal and ARM CPU.

  Each must be within noise (about 2%) of the previous main, or faster.
- **Exact results.** The `--check cpu` ladders, `gate_margin --loud`, the full gate on dev2,
  and CI must all be green before every merge.
- **One gate on dev2 at a time.** Use `scratchpad gate_run.sh`, which refuses to start while
  another gate is running.
- **Merging means fast-forwarding origin/main.** After the C code changes, refresh
  `work/mf-dev-main` and rebuild it.
- **Hardware properties, not device names.** A decision may use an API limit, a compiler
  statistic, a probed rate or the running workload. It never uses a device name.

## Stage 0: stable point

1. **Replay of ragged layouts.** When a segment's blocks have several bin counts, the fine
   stage makes one traced GPU call and splits its result per bin count
   (`_RaggedSplit.deferred`). The parts carry no trace, so the segment is never replayed.
   This happens at n=4096 on test27, so any gate whose GPU block trial locks 4096 fails its
   replay step. The fix carries the trace on the parts, has the replay apply the same
   split, and adds a test that forces a ragged layout.
2. **Merge the paired CPU trials** (725267ed, `work/mf-cpu-trial-reliability`): rebase,
   gate, CUDA, Metal, CI.
3. **Tidy up:** the merged `perf/coarse-seeded-peak` branch, stale scratch trees, and a
   gate lock shared by all agents.

## Stage 1: one shared GPU host layer

`_vkcompute` (4.1k lines), `_cudacompute` (2.5k) and `_mtlcompute` (2.0k) each implement
the same host logic separately:
- record and storage caches;
- slot rotation;
- ownership of async results;
- launch geometry;
- replay tracing;
- the coarse layout choice.

They also disagree on rules:
- uneven pair counts are ragged groups on Vulkan but padded on CUDA and Metal;
- host-mapped row windows exist on Vulkan only;
- the result-lifecycle fixes are CUDA only.

**Work:** move these into `_gpuhost`, behind a backend interface of compile, dispatch,
read back and timer. Apply one geometry rule (ragged groups) and one ownership rule on
all three backends.

**Measure:** lines removed, paired throughput on all GPUs, and the shared conformance
tests from stage 5.

## Stage 2: accounting replaces cost tables

Today `MF_COST_FILE` holds about 25 unit costs (correlation, transform, tier and Q15 cost
per size) and about 60 discrete choices:
- GPU: coarse layout, subgroup, interleave;
- CPU and workload: block candidates, block, chain, Q15 and direct-refine trials.

It serves two purposes: speed (no re-measuring) and reproducibility (every process makes
the same choices). A deterministic choice gives reproducibility without a file.

Each choice moves to the first rung of this ladder that decides it:

1. **Limits, with no timing.** These say whether a candidate can run at all:
   - API limits;
   - compiler statistics for the built kernel: Vulkan pipeline executable properties
     (instruction count, registers, spills); CUDA's kernel register count and local memory;
     Metal's maximum threads and static threadgroup memory.
2. **An accounting model, with no table.** Predicted time is the largest of ALU, shared
   memory and memory time, plus barriers:
   - the kernel's operation, byte and barrier counts are recorded in the manifests at
     build time;
   - the device's rates come from probes run once per process and never persisted
     (stage 4).

   CPU unit costs become per-device rates multiplied by per-tier counts. Survivor densities
   already come analytically from the reference profile. Chain, Q15 and block-size choices
   follow from the gate model's priced plans.
3. **Close calls.** A margin predicted below the noise picks deterministically, with no
   timing. A measured choice there is itself noise; the L40S coarse layouts flip run to run.
4. **Measurement verifies; it is not the source of truth.** An `MF_AUTOTUNE=verify` mode
   and a gate step time the model's choice against the exhaustive best. A miss means the
   model lacks a term; fix the model, never add a table entry.

**Acceptance:** on every machine, the model's choices are within about 2% of today's best
measured choice, for every band and size and for test27 end to end. The model must also
reproduce every known pathology:
- subgroup 32 on the Iris Xe;
- Intel 64-bit table loads (8.7x);
- SIMD16 spills;
- half-empty wave32 groups at one pair per group;
- Intel tiled builds 4x slower;
- the Q15 screen worth +20% on dev1;
- `C16_KAPPA`-driven survivor rates.

**Limits:**
- Driver code-generation surprises (row-window mode 2, 1.47x from 8 instructions) cannot be
  predicted. The policy is to delete fragile variants, not to tune around them.
- Survivor densities and APU clock state are measured online, during the run.
- `C16_KAPPA` stays a validated build constant.

**End state:** no persisted choices. `MF_COST_FILE` becomes an optional cache and record.

## Stage 3: kernel knobs instead of kernel copies

There are 837 compiled artifacts, 96 MB in total (PTX alone is 80 MB). Most variants differ
only in pairs per group, tile, band, twiddle source or row windows.

**Work:** turn these into runtime knobs:
- Vulkan: specialization constants and workgroup size;
- Metal: function constants;
- CUDA: a much smaller variant set, or NVRTC.

Every knob is then offered to the stage 2 model on every device.

**Target:** at least 5x fewer artifacts, with no slowdown.

## Stage 4: hardware probes

Measure once per process:
- fp16 and fp32 issue rate;
- shared-memory and global bandwidth;
- barrier cost;
- constant-table load cost;
- fp16 subnormal flushing;
- APU power sharing.

The probes are inputs to stage 2 and replace the device stories in comments. They are built
before stage 2 needs them.

## Stage 5: cross-platform lessons and one conformance suite

**Lessons to carry to every device:**
- ragged groups;
- the one-pass election (done);
- the measured twiddle source (not yet measured on the M2);
- the result-ownership audit, applied to Vulkan;
- interleaved timing (done).

**Conformance:** one test suite parametrized over every backend replaces the per-backend
copies, so a rule cannot drift on one platform again.

## Order

Stage 0, then stage 1, then stage 4 (probes), then stage 2, then stage 3, then stage 5.
Stage 5's lessons land inside the stages that touch them. Each stage merges in gated steps.

## Log

- 2026-10-15: plan recorded. Main at fd7ec6a4 (green). Stage 0 item 1 diagnosed.
