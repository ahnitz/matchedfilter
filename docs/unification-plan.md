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
- **One gate per machine at a time.** `tools/gate.py` takes an exclusive per-user lock,
  `/tmp/mf-gate-<uid>.lock`, and a second gate waits for it.
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
- the measured twiddle source (done on the M2; Metal also measures its packing);
- the result-ownership audit, applied to Vulkan;
- interleaved timing (done).

**Conformance:** one test suite parametrized over every backend replaces the per-backend
copies, so a rule cannot drift on one platform again. First part done:
`test_coarse_conformance.py` runs every coarse layout of the machine's backend.

## Kernel specialization inventory (2026-10-15)

The kernels are mostly shared. Slang source is 2,703 lines, and about 88% of it compiles
unchanged to SPIR-V, PTX and Metal. About 315 lines sit in backend-specific blocks:

- **Metal (about 210):** `peakTwoGate` (a gate-only election), SIMD-group barriers, and
  fail-open tests by integer bit checks (Metal compiles with fast math).
- **Vulkan (about 40):** specialization constants and the row-window binding.
- **CUDA (about 35):** constants declared as statics, and dispatch details.

There are 4 raw target intrinsics. Native CUDA kernels outside Slang total 463 lines
(`coarse_tc.cu` tensor-core gate, `followup.cu`); these are kept as explicit exceptions.

The duplication is in the hosts: about 8.6k lines across `_vkcompute`, `_cudacompute` and
`_mtlcompute`, which stage 1 addresses. The kernel-side cleanup lands in stages 3 and 5:
- `peakTwoGate` (about 25% of band-256 gate time on the M2) becomes a knob measured on every
  backend;
- the integer fail-open tests become universal;
- constants use one mechanism: Vulkan specialization constants, Metal function constants
  (check what Slang emits), and a small set of CUDA variants.

## Order

Stage 0, then stage 1, then stage 4 (probes), then stage 2, then stage 3, then stage 5.
Stage 5's lessons land inside the stages that touch them. Each stage merges in gated steps.

## Log

- 2026-10-15: plan recorded. Main at fd7ec6a4 (green). Stage 0 item 1 diagnosed.
- 2026-10-15: **Stage 0 done.**
  - Ragged-split replay fixed (b1f17b2e, caf7f440). The n=4096 test27 replay check went
    from 0 to 7 replays, exact against the CPU.
  - The paired CPU trials (afe10030, cherry-picked from 725267ed) are merged. Gate passed;
    full suite on M2 (1826); CUDA L40S tests and checks pass.
  - Main at caf7f440.
  - `tools/gate.py` now holds a per-machine lock (`--lock`, default `/tmp/mf-gate-<uid>.lock`).
    A second gate waits instead of overlapping.
- 2026-10-15: **Stage 1a (one launch rule).**
  - Untiled packed coarse launches are ragged on CUDA and Metal too: kernel RAGGED GROUPS
    on every target, and `_coarse.coarse_launch` as the single rule.
  - CUDA's row padding (`padded_rows`, padded offsets) and Metal's padded rows and slots
    are gone.
  - Fixed on the way: Metal's gate-only path keyed on "ragged" to mean "tiled"; it now
    tests `ctile > 1`.
  - New `test_coarse_ragged_groups.py` covers every backend. Vulkan SPIR-V is unchanged.
  - L40S: 41 + 131 tests pass, checks exact. M2: 1829 pass, checks exact. Paired
    throughput is measured once at the end of stage 1.
- 2026-10-15: **Stage 1b (one coarse-choice engine).**
  - `_coarse.stored_measured_choice` handles the memo, cost-file key with kernel id,
    stored lock, unmeasurable fallback and deterministic tie-break.
  - `_coarse.time_staged` handles staged screen and full timing, interleaved, with a paired
    confirmation of each stage's best.
  - Vulkan, CUDA and Metal supply only candidates, labels and a single-dispatch timer.
  - Fixed on the way: CUDA candidates hold unhashable ctypes handles, so the engine
    raised TypeError on CUDA (found by the L40S run). The CUDA host now passes indices.
- 2026-10-15: **Stage 1c (result ownership on every backend).**
  - `InputUploads._track(fn, owner=)` and `_claim(owner)`: a call that reuses a record's
    output buffers first collects the in-flight result reading them.
  - Vulkan and Metal claim at each record reuse (hierarchical, flat, grouped), before
    inputs are written. CUDA keeps its equivalent (`_dispatch_result`).
  - Found by probe: on Vulkan, an async result read after a same-shaped call returned that
    call's peaks. `tests/test_async_result_ownership.py` runs on any backend; 2 of its 4
    cases fail without the claim.
- 2026-10-15: **Stage 1 merged (main c805ac16; gates passed on c2b5ee06 and 423f30a7).**
  Paired against caf7f440 (the last main before stage 1), with settled trial locks:
  - **dev2 8060S:** batched 1.39-1.41e8 -> 1.40-1.43e8, pipelined 1.38-1.41e8 ->
    1.43-1.45e8 templates in real time (rounds 2-4). Fine-stage device time unchanged
    (0.059-0.061 s).
  - **M2:** each round's pair is within 1% (e.g. 3.88e7 vs 3.86e7 batched, 3.87e7 vs 3.87e7
    pipelined).
  - **L40S:** device time unchanged (fine stage 0.074-0.094 s in both trees). Wall
    throughput is host-bound and trial-noisy in both trees.
  - **dev4:** not measured; it is shared under load 16 (stage 1 changed only host code there).
  - **Next:** stage 2.1 (deterministic close calls), 2.2 (static compiler statistics),
    stage 4 probes, then 2.3 (the model, verified against timing).
- 2026-10-15: **Stage 2.1 (close calls follow the preference).**
  - `confirm_fastest` returns `Timings` with `.close`: contenders whose paired ratio to the
    fastest is within max(0.5%, 3 MAD of the per-round ratios).
  - `stored_measured_choice` then takes the backend's fixed preference among them, so a
    difference the measurement cannot resolve no longer flips with the noise. A resolved
    difference still picks the fastest.
- 2026-10-15: **Stage 2 feasibility study (8060S, band 256, 22 coarse candidates).**
  RADV static statistics against paired timings:
  - Issue count per pair (instructions x waves per group / pairs per group) ranks them at
    Spearman 0.95. It gets the structure right: one pair per group is worst, packed untiled
    is in the middle, tiled is best.
  - **The model alone would lose performance.** It ranks p4t8 best (131 issue cycles per
    pair), but p4t8 measures 1.557 ns per pair against 1.17 for its neighbours, 33% slower.
    Neither VGPRs nor code size explains it.
  - The top five candidates are within 3% (1.174-1.208), inside any static model's error.

  **Revised stage 2 end state.** Accounting shortlists, before building where it can
  (one pair per group and the losing twiddle source are clearly slower). A short paired
  timing of the shortlist decides, and close calls go to the preference.
  `MF_COST_FILE` becomes an optional cache rather than a correctness or reproducibility
  requirement. "No timing at all" contradicts "no performance lost" on this evidence.
- 2026-10-15: **Stage 5 lesson: gate-only coarse election on every backend.**
  - `peakTwoGate` (Metal-only until now) reports each pair's pass and bound without
    electing a lag: nothing reads tier 0's index, and the compaction reads only the values.
  - Vulkan and CUDA tiled builds whose pair fits one subgroup now take it, through the
    threshold in the last push slot (`_gate_bits`, Metal's rule). CUDA's tensor-core gate
    keeps its own reporting.
  - 8060S band 256, interleaved: 0.905-0.918x the time per pair at the tiled layouts.
  - dev2: 209 tests pass, `gate_margin --loud` all ok, both checks exact.
- 2026-10-15: **Stage 3 finding.** Slang 18 rejects specialization constants in
  `numthreads`, but sizes `groupshared` arrays from them. Pairs per group as a runtime knob
  therefore needs a SPIR-V `WorkgroupSize` spec-constant patch (Vulkan), dispatch-time
  threads (Metal) and dynamic shared memory (CUDA). That is a kernel refactor for
  package-size and maintenance gains, not speed, and is deferred behind stage 5's speed
  lessons.
  - The 96 MB of committed artifacts costs git-history churn on every kernel change.
    Building them in CI instead is a process change to propose, not one to make
    unilaterally.
- 2026-10-15: **Stage 5 lesson: the measured twiddle source on Metal.**
  - Metal's coarse builds now carry the fp16 twiddle table. Its use is the
    `MF_COARSE_TWT` library macro (a "w" entry), and tiled `filterTwo` reads the same
    runtime constant on every backend.
  - The Metal tile choice measures (tile, twt) pairs.
  - M2, separate processes: the table is 5-6% faster untiled (band 128: 8.69 -> 8.17-8.20
    ns; band 1024: 57.8 -> 54.9) and 1.4% at band 512 t2, but 3-6% slower at t4/t8. Hence
    the per-candidate choice.
  - Vulkan tiled builds unchanged: 0.999x on the 8060S.
  - M2 end to end, paired against main 8d6320e3 (rounds 2-4): batched 3.873-3.880e7 ->
    3.915-3.934e7 (+1.1-1.4%), pipelined 3.637-3.670e7 -> 3.713-3.719e7 (+1.3-2%).
    Gate passed (a48a482f).
  - 7447cc03 and a48a482f are held for L40S validation (cluster unreachable 2026-10-15).
- 2026-10-15: **Stage 5 lesson: Metal measures its packing too.**
  - The Metal coarse layout is one measured choice over (pairs per threadgroup, tile,
    twiddle source), as on Vulkan. The SIMD-fill packing rule is now only the default when
    nothing is measured.
  - Why: the rule missed both ways on the M2. Band 512 untiled runs best at two pairs per
    threadgroup (25.8 ns per pair, against 26.5 at one); band 1024 at one (52.7, against
    54.8). One pair fills the SIMD group at both bands.
  - M2 choices: band 64 p8t2w, 128 p4 untiled w (5.5 ns; the p4 tiles are 11-15 ns),
    256 p2t2w, 512 p1t2, 1024 p1 untiled w.
  - M2 end to end, paired against a48a482f (rounds 2-4): batched equal (3.92-3.93e7 both),
    pipelined 3.72 -> 3.74e7. Suite 1834 passed, margin ok, both checks 0/0 one-sided
    (cbbbed5e).
- 2026-10-15: **Stage 5: one coarse conformance suite.**
  - Every backend names a coarse layout one way (`_coarse.layout_label`: build stem, "w"
    for the fp16 twiddle table, "@<size>" for a required subgroup size), lists them
    (`Context.coarse_layouts`) and takes `MF_COARSE_LAYOUT` as a forced, untimed choice.
  - `test_coarse_conformance.py` forces each layout through `hier_peaks`. The gate must
    make the exact statistic's decisions at thresholds in wide gaps of the float64 maxima.
    An overflowing row and gate_margin's transient (K = 1, 32) must pass.
  - Layouts covered: 8060S 12-50 per band; M2 4-18. A 1.5x mis-scaled tiled gate
    threshold fails it at the first tiled layout.
  - It replaces four per-backend test files or tests. The Vulkan test file is now only
    the direct-kernel tail check, and the 8060S tile tests drop from 200 s to 7 s.
  - Gate passed on 2af3bfa7; M2 suite 1829 passed.
