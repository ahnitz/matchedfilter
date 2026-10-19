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

There are 4 raw target intrinsics. The one native CUDA kernel outside Slang is
`coarse_tc.cu` (the tensor-core gate, 285 lines), kept as an explicit exception.

The duplication is in the hosts: about 8.6k lines across `_vkcompute`, `_cudacompute` and
`_mtlcompute`, which stage 1 addresses. The kernel-side cleanup lands in stages 3 and 5:
- `peakTwoGate` (about 25% of band-256 gate time on the M2) becomes a knob measured on every
  backend;
- the integer fail-open tests become universal;
- constants use one mechanism: Vulkan specialization constants, Metal function constants
  (check what Slang emits), and a small set of CUDA variants.

## Stage U: true unification (revises stage 1; 2026-10-18)

Stage 1 moved some helpers into `_gpuhost`, but the host logic still exists three times
(`_vkcompute` 3,544 lines, `_cudacompute` 2,023, `_mtlcompute` 2,070, with 43/40/36
methods and different method sets). That is why one backend can lack what another has:
25 capability flags in the shared layers mark implementation gaps, not hardware
differences, and 31 references name a backend (e.g. `gatechain._BAND_FORWARD =
{"vulkan", "metal"}`). Measured consequences on 2026-10-18: real-series input existed on
Vulkan only; CUDA launches each leaf call separately (1,380 launches per pass, 4.7% of the
L40S roofline) while Vulkan fuses them into ~96 submissions.

**Rule.** Decisions use queried hardware features and measured rates, never the API's
name. The APIs differ only in mechanics, which live in a thin driver.

**Design.**
1. **Driver (the only per-API code, ~500-800 lines each):**
   - buffers: allocate (device-local, host-visible, host-mapped), map, offset views,
     fill, copy;
   - kernels: load an artifact with constants; report its compiler statistics;
   - command lists: dispatch, indirect dispatch, barrier, fill, copy, timestamp, recorded
     once into the native replayable form (Vulkan command buffer, CUDA graph, Metal
     encoding);
   - submit and wait: fences or events, and ordering one submission after another;
   - a feature query: unified memory, shared memory, subgroup sizes, workgroup limits,
     indirect dispatch, queues, fp16/int16 rates, cooperative-matrix units, timestamps,
     buffer alignment.
2. **One executor** for every operation (forward, flat peaks, full and continuous
   correlation, hierarchical tiers including cascade, grouped and band forward, follow-up
   items, zeroing) and every mechanism (record caches, slots, fused batches, call-plan
   replay, async with host settles, result ownership).
3. **Decisions from features:** no indirect dispatch selects device-count kernels;
   unified memory decides buffer placement; band forward follows its bytes model.
4. **Kernels:** target switches only for intrinsics, inside helpers; other variants
   become options set from features.

**No regressions.**
- **Baselines (U0)** on dev2 8060S, dev3 Renoir, dev4 Iris Xe, L40S and M2: throughput,
  roofline, submissions per pass, host time, gate results.
- **One operation per change**, all three drivers at once, old copies deleted in the same
  commit. Acceptance: bit-identical outputs against the old implementation (differential
  harness, same process); paired throughput within ~2% or better on every device;
  structural counters no worse; full gate plus the M2 and L40S suites.
- **The best existing implementation becomes the shared one** (Vulkan's fused batches
  and replay; CUDA's result ownership; Metal's fused band forward where features allow).

**Phases.**
- U0: baselines, feature matrix, differential harness.
- U1: driver interface, three drivers, driver conformance tests (no behaviour change).
- U2: port operations, each merged separately: forward, full correlation, continuous
  correlation, flat peaks and follow-ups, hierarchical tiers, then batching, replay and
  async.
- U3: delete flags made universal and every API-name check.
- U4: kernel sources: switches become options; cooperative matrix becomes a feature.
- U5: dead code and documentation.

**U1 design (from reading the three hosts, 2026-10-18).**
- **Kernel interfaces differ per target today, so they are unified first (U1a).** The same
  Slang entry points compile to different signatures and constants:
  - Vulkan specializes `mfDataStride`, `mfRowWindows`, `mfDataScaleBits`, `mfCoarseTwt`,
    `mfAccurateTrig` and `mfSubgroupSize` (specialization constants); CUDA and Metal compile
    most of them to fixed values (twiddle.slang), so their hosts compensate: a pack kernel
    copies each band where Vulkan reads it in place through the stride;
  - row windows are a binding plus a constant on Vulkan, a table pointer argument plus a
    sentinel window start (ROWWIN_ON) on CUDA;
  - survivor-listed kernels use indirect dispatch on Vulkan and Metal, grid-stride loops
    reading the count from device memory on CUDA.
  Target: one signature per entry point on every target, and one constants mechanism:
  Vulkan specialization constants; Metal's runtime MSL compile with the same values as
  definitions; CUDA by runtime NVRTC compile with definitions (cached), or launch arguments
  where a value varies per call. Listed kernels take both forms (indirect dispatch where the
  device has it, a grid-stride launch elsewhere), chosen by the feature.
- **Decisions keyed on vendor or API today** (to become probed features): `_accurate_trig =
  vendorID == Intel` (Vulkan), `gatechain._BAND_FORWARD = {"vulkan", "metal"}`, the c16 bound
  flags per API in gatechain.
- **The executor's command list** generalises Vulkan's captured, phased recordings (fused
  batches already re-emit captured work phase by phase across calls): operations are
  fill, set-indirect-args, dispatch, dispatch-indirect, copy (readback on a discrete
  device; nothing on unified memory), barrier and phase. A driver emits a list natively:
  a Vulkan command buffer, a CUDA graph or stream launches, a Metal command buffer.
  Fusion, interleave, replay and async then exist once, for every backend.
- **Incremental port.** Each backend's Context becomes driver primitives plus a shared
  executor class it inherits; an operation is ported by deleting the backend's own method so
  the shared one runs. The first slice is the forward transform (its kernel interface is
  already one since eb4aa070), then the order of U2.

**Risks.** Python per-call overhead (replay native recordings; host time per call is an
acceptance metric); Metal command buffers are one-shot (re-encode as today); discrete vs
unified memory (keep the L40S prefetch path as a feature decision); testing reach (L40S
via condor, M2); new GPU features pause during U1-U3 except fixes.

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
- 2026-10-15: **Stage 2 for GPU coarse choices: closed without a model.**
  - The coarse choice costs 0.49 s per process on the 8060S (all six bands, 12-50
    candidates each) and 1.68 s on the M2.
  - The conformance suite shows every layout returns the same peaks and values. So a
    coarse choice affects speed only, and the cost file is only a cache for it.
  - An accounting shortlist would save under 2 s per process. It is not worth its code, so
    it is not built.
  - Cost tables still matter on the CPU, for a different reason. The chain choice already
    has a close-call rule (`pick_stable`: within `TIE` of the cheapest, the canonical
    chain). But `plan_chain` sets each tier's threshold from the calibrated prices. Two
    processes that calibrate differently therefore trigger differently near threshold,
    each within the false-dismissal budget. Making the split insensitive to price noise is
    a change to the gating's semantics. It belongs with the gate-model owner and is not
    part of this cleanup.
- 2026-10-15: **Vulkan: one record builder (ba3b9cea).**
  - `_make_hier` and `_make_hier_cascade` (430 lines, two buffer-naming schemes) are now
    one loop over the tiers. Tier i writes `cidx<i>`/`cval<i>` from `ct<i>`. The last
    tier's survivors are `surv`/`args`, and every reader takes those.
  - `hier_peaks`' two branches are now one. The three copies of the coarse span are now
    `_gpuhost.coarse_span`. Net -318 lines.
  - Paired dev2 ladder: the new tree is at least as fast. In rounds 3-4, batched
    1.38-1.41e8 against 1.31e8. The base process had stored a bad coarse choice; see the
    next entry.
- 2026-10-15: **Open: a stored coarse choice can be badly wrong, and it persists.**
  - The base process of that ladder stored the untiled `tierb_256_c16p2w@32` at band 256.
    Untiled layouts measure 1.54-1.76 ns per pair there and tiled ones 1.06-1.10, so it
    ran the fine stage at 0.077 s against 0.058 s.
  - Eleven fresh processes did not repeat it: six bare and five inside the ladder. All
    chose a tiled layout at subgroup 64.
  - The base was the first process after a gate run, so a clock or power transition on
    the APU during the measurement is the likely cause. MF_COST_FILE then kept the choice
    for every later run.
  - Proposal: each process re-checks a stored choice once. It runs a short paired timing
    against the best stored layout of the other stage, and re-measures if the stored
    choice loses by more than the close-call margin. A bad choice then costs one process,
    not every process after it.
- 2026-10-15: **Stored coarse choices are re-checked (512f609b, b8dc6eb6).**
  - The two runners-up are stored in the choice's record. Each process times the stored
    choice against them once, and re-measures everything if a runner-up is faster beyond
    the noise.
  - Planted test: the stored choice was set to `tierb_256_c16p2w@32`. The next process
    replaced it with p4t2w@64, and the one after kept it after a 0.05 s re-check.
  - The first version broke when a tiled choice had no untiled sibling in the re-check
    set: Vulkan's staging never timed it, and `test_reproducible_choices` raised a
    KeyError. Now a tile is skipped only when its untiled sibling lost, and a re-check
    that does not time the choice re-measures.
- 2026-10-15: **Vulkan: one recording helper (65a7eb0a); per-call cost restored (fe15c4ba).**
  - `_Recording` replaces the allocate/begin/bind/push/dispatch/barrier/end code that
    eleven recordings each repeated (-119 lines).
  - Paired dev2 ladder, both trees on one settled cost file: device time identical, but
    the new tree was 2.0-2.5% slower. The cause was host time in `hier_peaks`: the merged
    tier path built its key with generator expressions, 1.7 us of a 43 us call. Plain
    tuples restore the base's call count.
  - Re-paired against 91f7e189: pipelined equal (1.384-1.453e8 against
    1.387-1.441e8); batched within 1% in rounds 1, 3 and 4.
  - Lesson: paired ladders need trials settled in the shared seed file. A seed taken
    after one run measured trial exploration (2.3e6 templates in real time) rather than
    the code.
- 2026-10-18: **Stage U adopted** (see "Stage U: true unification"). Starts from 912b01ac
  (gate passed on dev2; M2 suite 1854 passed; L40S suite 1889 passed). U0 begun.

- 2026-10-18: **U0 baselines recorded; U2.1 full correlation runs on the shared executor.**
  - U0, `MF_CHAIN_FORCE=2048:256,512`, three rounds each, in M templates in real time:
    - dev2 8060S: 165.5 / 190.0 / 187.9;
    - dev3 Renoir: 26.2 / 26.9 / 27.0;
    - M2: 35.7 / 35.9 / 35.6;
    - L40S: 96.9 / 98.0 / 81.9;
    - dev4 Iris Xe: about 3.25 (r1 was the cold shader-cache run, so only r2 and r3 exist).
  - `_roofline` gives NaN peaks for a device without a known shader-core count (Intel)
    instead of raising.
  - `_gpuexec.Executor.correlate` replaces three per-API copies, deleted in the same
    change. The per-API code that remains is driver primitives (`_x_kernel`, `_x_alloc`,
    `_x_list`, `_x_run`, `_x_release`, `_x_read`). The tiling rule tests reported limits
    (`max_dispatch_x`, `storage_offset_alignment`); it does not branch on the API.
    `async_correlate` holds on every backend.
  - Goldens are bit-identical: 71/71 on dev2 (Vulkan), M2 (Metal) and L40S (CUDA).
  - Suites: dev2 1979 passed; M2 154 focused tests passed; L40S 76 focused tests passed.
  - Host CPU per call is lower on every backend:
    - Vulkan: 19.1-19.6 -> 18.2-18.3 us (shared, n=4096).
    - CUDA: 24.4 -> 23.5 us shared, 86-88 -> 84 us host, 41 -> 38 us two-stage.
    - Metal: 79 -> 76 us shared.
  - Two costs found and removed on the way:
    - CUDA rebuilt the ctypes launch parameters on every call; `_CudaList` now builds
      them when it records.
    - `shared_view` looked an allocation up twice; it now does it once.
  - Metal wall time per call is 240-315 us against 17-20 us of device time, identical
    in both trees. It is submit-to-completion latency, and the latency is bimodal: both
    trees show both modes. M2 search throughput is unchanged (35.4-35.7 against
    35.5-36.0 M, paired).
- 2026-10-18: **U2.2 continuous correlation runs on the shared executor.**
  - The three copies are deleted, along with CUDA's `_full_inputs`, `_scratch`, `_tiles`
    and the `_full_batches`/`_tierc_batches` tables.
  - New in the driver interface:
    - `Arg`: buffers bound per run. `out` and `starts` move between calls (Metal wraps a
      caller's array per call with `host_view`), so the record is keyed on inputs only.
      Templates are not re-uploaded when only the output moves, and no recording replays
      a stale binding.
      - Vulkan bakes bindings into descriptor sets: a command buffer per binding, the
        last 8 kept, each holding its views.
      - CUDA keeps a persistent parameter per Arg and sets it per run.
      - Metal re-encodes on every run.
    - `upload=True` buffers.
    - The `stage_host_inputs` feature: CUDA's managed allocations migrate pages, so small
      host-written inputs (block starts) go through pinned staging into device memory.
      It is a feature, not an API check.
    - `_x_after_readers`.
    - Uniform words grouped as the kernel declares them: a vector is one tuple, so CUDA's
      `uint4` is one parameter on every path that passes one.
  - The two-stage form tiles its scratch by runs of whole data rows. This was CUDA's
    rule, now everywhere; each run's starts are an uploaded copy.
  - Vulkan binds template sub-ranges in place instead of copying them. Device time is
    identical (dev2: 33.2-33.4 us per middle call either way).
  - Goldens bit-identical on dev2. Two-stage continuous against CPU: 1.8e-6 relative
    (dev2), 2.7e-6 (M2), 7.0e-7 (L40S), one run or three.
  - Per call (correlate_continuous, root and middle shapes):
    - dev2: device time identical; host CPU equal or lower (22.9-25.1 against
      22.5-29.0 us).
    - L40S: wall 53-57 against 54-56 us middle, 109-117 against 110-111 us root
      (device time noisy on both).
  - Paired dev2 search: 184-206 against 181-204 M.
  - Found on the way: the U2.1 L40S check ran two test files only, and
    `test_cuda_parity::test_correlate_tiles_into_host_output` failed at c5017af3 (it
    patched CUDA internals). It is replaced by
    `test_gpu_host_output_tiles_within_the_staging_budget`, which runs on every GPU.
    Every port's L40S check now runs the full suite.
  - **Open:** before an in-place output is rewritten with the call left in flight,
    CUDA synchronizes the device: readers on other contexts' streams. Vulkan (several
    queues under `filter_series_many`) and Metal (one queue per context) add no wait.
    Whether a reader on another queue can still be running there is unverified; it is
    unchanged by the port.
- 2026-10-18: **U2.3 forward transform runs on the shared executor.**
  - `Executor.forward` (with `forward_valid`, `forward_replay` and `_forward_fused`)
    replaces three implementations.
  - Deleted with them:
    - Vulkan's two-stage path and its per-slot persistent scratch;
    - Metal's `_forwards` table and persistent scratch;
    - CUDA's host-array fallback and `_small_input`.
  - Two-stage scratch is owned by the record.
  - Block starts are bound in place unless they lie outside device memory, or the device
    stages host-written inputs. In those cases they are uploaded per call, on the slot's
    stream (`_x_upload`). Records are keyed by slot, as `_small_input` was, so slots that
    share a CUDA stream keep their own staged starts. A span is prefetched on migrating
    memory (`_x_prefetch`).
  - New list op `stamp(name)`: Vulkan captures stamped lists, so fused batches still take
    the forward (96 fused submissions per pass on dev2, as before).
  - Deferral stays a driver hook, `_x_defer`, until its consumers are ported:
    - Vulkan: the pending command buffer and `_fwd_src`;
    - Metal: the lazy forward a hierarchical call claims as forwardTier0. Claims per M2
      bench run: 16,411 against 16,413 before;
    - CUDA: an immediate launch plus the per-stream event.
    The source tuple now names the bound starts and the row within them, and Vulkan folds
    a view's offset into its absolute band offsets.
  - Goldens bit-identical on dev2, dev3, dev4, M2 and L40S.
  - Suites: dev2 1980 passed; M2 1855 passed (docs present).
  - Focused tests: dev3/dev4 177 each; L40S 145, including test_docs with docs present.
    The L40S U2.2 shards' 6 failures were test_docs without a docs directory.
  - M2 paired search: 35.10-35.16 against 35.13-35.39 M; stage times equal to the ms.
  - dev2 and L40S paired search: pending. dev2 was loaded by other sessions (load
    average 3-9; a 87 M round was that load). Counted on a clean run: no re-recording or
    binding eviction in steady state, only `destroy` clean-up.
- 2026-10-18: **Course correction: unify optimizations, not behaviour.**
  - U2.1-U2.3 moved code into `_gpuexec` but preserved each API's behaviour. `_x_defer`
    hides three forward-fusion strategies.
  - From here on, every optimization found on one backend gets one implementation for all
    of them, on by default. An opt-out needs a measurement on that hardware, keyed on the
    measured property and recorded here.
  - Acceptance: correct (goldens, or CPU where results legitimately change) and throughput
    equal or better on all five GPUs.
  - Inventory, to be made universal in this order:
    1. Device peak compaction (CUDA only).
    2. One deferred forward any consumer can claim: fused first tier or band forward by the
       bytes model, on every backend. Replaces `_x_defer`.
    3. One record-once/replay-cheaply mechanism (Vulkan fused batches, Metal collector,
       CUDA graphs), with call-plan replay (Vulkan only) on top.
    4. Coarse band read in place through a stride; Metal/CUDA copy it with pack_coarse.
    5. Per-row windows; Metal is excluded by name, from one 6% measurement.
    6. Wrapping caller memory on unified memory (host_view, Metal only).
    7. Record sizing: CUDA grows by capacity, Vulkan and Metal keep one record per shape.
    8. Vendor/API keys: gatechain `_BAND_FORWARD`, the Intel accurate-trig check.
  - Genuinely hardware, kept as probed features: staging and prefetch on migrating
    memory; indirect dispatch.
  - L40S U2.3 paired search, 4 alternating rounds: 98.6/105.0/101.6/104.0 M against
    110.2/96.6/96.3/110.5 M. Means 102.3 against 103.4; leaf ±8% in both.

### Remaining stage-U work, in order (2026-10-18, revised for "unify optimizations")
Each step: goldens and full suite on dev2 and M2; at milestones (after U2.5, after U2.6 and
after U2.8) all five GPUs, including paired search throughput on quiet machines. Merge to
main only when everything is done, gated and benchmarked.

1. **U2.4 flat peaks** (one record per shape, per-run windows; grouped windows in place or
   packed by alignment; ragged bins everywhere; one-round-trip readback).
   - Device compaction, or a dense read scanned on the host: a measured per-shape choice
     (`Measured`), since unified memory loses on compaction (M2: +40 us few hits, +50% all
     hits).
2. **U1a one kernel ABI**: data stride, data scale, row windows, twiddle source, fp16 bound,
   accurate trig and subgroup are build-time constants everywhere.
   - Vulkan: specialization constants.
   - Metal: macros when its library compiles (it compiles at runtime).
   - CUDA: launch uniforms (no runtime compiler): stride, scale, row-window table.
   - The row-window table is an entry parameter on every target, Metal included.
   - Listed kernels read their count from device memory and loop: indirect dispatch where
     the device has it, a fixed grid elsewhere.
   - Then every backend reads the coarse band in place (pack_coarse goes) and may use
     per-row windows (a measured choice; Metal's by-name exclusion goes).
3. **U2.5 follow-up items** on the executor (outputs per device, pending item forwards
   taken into the same submission).
4. **U2.6 hierarchical tiers** (single, cascade, grouped/ragged) on the executor.
   - Coarse layout choice measured in one place.
   - Fused forward+tier0 and band forward+recompute: one measured choice on every backend.
5. **U2.7 one deferral model**: pending work per slot in the executor; a consumer runs it
   first or claims it. Replaces `_x_defer`.
6. **U2.8 record once, replay cheaply** (Vulkan fused batches, Metal collector, CUDA
   graphs), with call-plan replay on every backend.
7. **U2.9** zero_columns, pending writes and settle, timings.
8. **U3** delete the capability flags made universal and every API- or vendor-name check
   (gatechain `_BAND_FORWARD`, the Intel accurate-trig check).
9. **U4** kernel-variant cleanup. **U5** dead code and documentation.
10. **Merge**: full suites on dev2, M2, L40S, plus dev3/dev4 focused runs. Goldens. Paired
    search on quiet machines (the dev2 forward-port slow-leaf observation under load must
    be settled here). CI green. Then push, refresh mf-dev-main, and re-gate main.
- 2026-10-18: **U2.4 flat peaks run on the shared executor.**
  - peaks and peaks_grouped are written once; each backend's copy and its helpers are
    deleted (Vulkan _make_batch/_transient_peaks, CUDA _flat_record, Metal _peaks).
  - One record per (shape, slot, inputs). The search window, threshold and bin size are
    per-run words (`Arg(words=k)`), so every window reuses the record and its uploaded
    inputs. Vulkan, which bakes words into command buffers, records one-off command buffers
    past 8 bindings, freed when they finish (as its transient peaks did).
  - Records are bounded by cache_limit_entries, least recently used first (`_exec_room`).
  - Grouped windows write in place when every group's offset meets the device alignment;
    otherwise they are packed and gathered. Ragged bin counts (nbins covering every group,
    Metal only before) work everywhere.
  - Readback is a list op: an asynchronous copy into page-locked memory where the device
    does not share it (CUDA `_Readback`), nothing where it does. Every device gets the
    one-round-trip readback CUDA had.
  - Sparse results: device compaction (CUDA only before) is built for every target. A
    sparse call shape measures compaction against a dense read scanned on the host
    (`Measured`: three warm calls each, re-checked every 256) and keeps the faster. On M2,
    compaction loses: +40 us with few hits, 1.71 against 1.16 ms with every bin a hit.
  - Tests:
    - New: tests/test_gpu_flat_results.py on every GPU (result lifetime under eviction,
      clear and reuse; sparse equals dense, packed and over the first read; upload
      residency).
    - Mocked tests of old flat internals were rewritten against the executor.
  - Goldens bit-identical on dev2 and M2. Suites: dev2 1975 passed; M2 1856 passed.
- 2026-10-19: **U1a + U2.5-2.7: one hierarchical search and one deferral model.**
  - The hierarchical tiers (single, cascade, grouped/ragged), follow-up items and deferred
    forwards run on the executor (`_gpuexec`, `_gpuhier`); each backend's copy is gone.
    The feed follows a driver feature: `inplace_feed` (kernels specialized when created:
    Vulkan, Metal) reads the spectra at a stride and scale; otherwise packed bands (CUDA,
    whose runtime stride/scale cost 12-39% on the L40S). A call claims its deferred forward
    when the bands move fewer bytes (`band_forward_wanted`, now the band feed until a
    fraction is measured) and recomputes its refine blocks. Metal's build-time constants are
    library macros.
  - Deferred work: `_pending` per slot; a run on the slot takes it into its submission, a
    hierarchical call may claim it, an unslotted run first runs the deferred work that
    writes what it binds (`_take(slot, reads)`), a restaged forward runs the earlier one
    first (`_exec_run_holding`).
  - New driver primitives: `_x_view` (counts, survivors and gathered rows read in place),
    `_x_idle` (one wait for a context's own work; a clear frees every record as finished),
    `_x_free` (CUDA keeps idle frees in per-device pools: cuMemFree/cuMemFreeHost
    synchronize the device), `_x_section` (a record's counters share one buffer and its
    row-window tables another: one update, one readback, one upload).
  - Validation found, and the fixes are in: the claim never happened (fractions noted only
    by banded calls); device compaction shared the refine's fused phase and read its output
    half written (the fused capture now refuses a phase with an inner barrier); a waited
    flat call dropped its slot; tuple words became one uint4 on CUDA; CUDA's fp16 bound
    switch missed shared modules and the tensor-core gate; Metal's stems and function names
    of the new kernels.
  - Host cost on the L40S (fine stage 25-45% behind 1ccbbe4b at equal block size): GC of
    twice the objects, and its full collections destroying dropped plans mid-search. Fixed
    with slotted buffers on every backend, packed CUDA launch parameters, pooled CUDA
    update words, the band-feed default (half the records), and block trials that skip
    batches which built a recording and sample ranks in turn (a trial had locked a slower
    leaf from setup-polluted samples).
  - Throughput against 1ccbbe4b (U2.4), paired, MF_CHAIN_FORCE=2048:256,512:
    - dev2 (8060S, quiet): 210-226 against 187-216 M.
    - M2: 37.4-40.0 against 35.6-35.8 M; setup passes 20 s against 38-50 s.
    - L40S (5 warm-up passes): n=2048 91.8 against 91.4 M, n=4096 85.2 against 86.9 M,
      automatic choice 74/83 against 87/73 M (node shared with other jobs).
    - dev3: 24.9-27.7 against 25.4-27.2 M (means 26.4 and 26.3); setup 43 s against 48-65 s.
    - dev4 (Iris Xe): 3.12-3.19 against 3.15-3.27 M.
  - Goldens bit-identical on all five GPUs. Suites: dev2 2013 passed, M2 1904 passed, L40S
    CUDA-path set 143 passed, dev3 238 and dev4 focused sets passed.
  - tests/test_gpu_c16_bound.py checks every coarse layout a GPU may pick, its operands
    placed as a call places them (unplaced, a loud burst left fp16's range on dev4).
  - gatechain: the band forward and the fp16 gate kind are a GPU's (device kind), not a
    backend list; a CPU device's backend name (AVX3) had been taken for a GPU's.
- 2026-10-19: merged to main as a57c884a (U1a + U2.5-2.7, capabilities on the executor, the
  Vulkan trig probe); CI green.
- 2026-10-19: **U2.9, U3, device follow-ups, U5 (on unify).**
  - zero_columns, writes in flight and device timers are the executor's. Zeroing is a list
    fill over rows (one 2-D memset on CUDA, per-row fills on Vulkan and Metal), kept as a
    record. A write in flight is a driver token on the device's list; settle_writes,
    write_token and settle_until are shared, so CUDA and Metal double-buffer the staged series
    and continuous workspaces as Vulkan did. timings(): one (list label, device ms) per
    submission everywhere, per-kernel or per-phase "k:" entries only with MF_GPU_PROFILE; CUDA
    timing keeps graphs on, so calibrations time the production dispatch.
  - Vulkan kept recordings use SIMULTANEOUS_USE (a run left in flight may be resubmitted
    before it finishes), and a run without a slot is left in flight on its own fence instead
    of waited at submission.
  - U3: the universal capability flags are deleted; filter_series_many opens fused batches
    through _gpuexec.fused() (drivers register), with no module-name list.
  - Device follow-ups are written once (Executor.submit_followups): per group a listed
    forward and refineItems, records per shape and place in the batch, one owner context per
    device, one readback per group. Metal gains them (items_<n>.metal); a real series is read
    in place (the old paths took float offsets as complex samples). 64-job batch, forced to
    the device: M2 10.9 -> 4.5 ms; L40S 3.89 -> 3.90 ms (parity).
  - The per-call single-template trial kept every follow-up batch off the device: the batch
    path consulted a one-block shape filter_series never records, so with autotuning no batch
    ever ran batched. _batch_device measures the batched device path against per-call CPU
    plans per batch. Auto mode: M2 29.9 -> 4.5 ms, L40S 35-38 -> 5.5 ms.
  - U5: drivers own their peak models (_x_peaks); _roofline had reported Vulkan's fp16
    coarse tier as fp32 (a module function Vulkan never had). Dead code from the old hosts
    deleted; the audit tools read the executor's records.
- 2026-10-19: **U4 kernel knobs, first one, and the tensor-core gate.**
  - The gate-only report of a later gate tier (tierb.slang gateOnly: the window's maximum,
    no election) was Metal-only. It is compiled for every target; the host asks for it per
    device and band by measurement (HierOps._gate_way, stored). Per pair: 8060S gate 10-13%
    faster, M2 12-18% faster, L40S within 1% (either way); RENOIR tier 1 0.66 -> 0.30 ms a
    call. Both ways give identical peaks (tests/test_gate_way.py forces each).
  - The CUDA tensor-core gate stays CUDA's, as a candidate: it loses by 25-40% on the L40S,
    whose tensor units run 4x its packed-fp16 rate (the matrix DFT issues 5-9x the flops).
    The 8060S's WMMA gives 2x and the M2's simdgroup matrices run on its ordinary ALUs, so
    a cooperative-matrix port could only lose there. The hardware property that decides it is
    that ratio, and no device we have exceeds the L40S's.
  - Fused batches, measured (pinned chain, interleaved rounds): RENOIR fused 24.4 against
    unfused 24.6 M (none); M2 3.19e7 against 2.74e7 (+16%, the Metal collector).
  - The other Metal-only kernel code is hardware-bound, not an optimization to spread:
    SIMD-scoped exchange barriers live in the SPLIT_STAGE builds, which exist because Apple
    caps threadgroup memory at 32 KB (n = 8192), a build no other target needs; the integer
    fail-open tests stand in for IEEE comparisons Metal's fast math does not keep.
    peakTwoGate (tiled gates' pass without election) is compiled for every target already.
