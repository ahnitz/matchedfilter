# Cross-platform review: what is common, what transfers, what to unify

Second review, at main 52ccea74 (2026-10-13), rebased onto beff0a71 (which merged the CPU
streaming stores and the ARM platform FFT). The first (c28daf1, 2026-10-09) is summarised in
§9 with the status of each of its items.

Since then each backend gained mechanisms of its own: Vulkan async segment replay, per-segment
vectorised follow-ups, Metal fused-batch chunk 2, Metal SIMD-scoped exchange barriers,
`forward_tier0.slang` (Metal only), CUDA stream spread and host-input buffers, CPU streaming
stores past the LLC and ARM vDSP pricing (merged in 6b15bb83..beff0a71), one shared trial
decision rule.
This review asks of each one: which backends have it, should the others, and is the code
that implements it written once.

The organising rule is unchanged. A choice generalises when the property deciding it is
queryable (subgroup width, shared memory, SM/CU count, cache size, memory heaps), or when it is
measured through the shared rule (`gatechain.measured_choice`) and kept in `MF_COST_FILE`. A
constant measured on one box, or a per-backend env default, is a per-machine special case.

Measurement conditions on dev2 (8060S, Zen 5) for everything quoted here: `tools/ladder.py`,
fir_three_level_modern_v1_bottomup_cap401 bank, `--profiles` H1, top 1, one primed
`MF_COST_FILE` (36 + 36 segments, all trials locked, no ladder warning) copied fresh into each
run, `--roofline`, alternating rounds, `OMP_NUM_THREADS=1` (and BLAS vars). The host was at
load 45-55 from other agents' suites and the GPU held 600-740 MHz (APU power cap) throughout,
so absolute numbers are low and only alternating-round comparisons are meaningful.

## 1. Matrix

Key: **Y** has it; **A** applicable, missing; **N/A** not applicable (reason in §2);
**?** needs a measurement; **br** on a branch, not main.

| Mechanism | Vulkan | CUDA | Metal | CPU | Decided by |
|---|---|---|---|---|---|
| Fused batch: submissions collected and committed in chunks | Y, chunk 16 | N/A (graphs, streams) | Y, chunk 2 | N/A | **two constants**, each measured on one box → one measured choice (§2.1, §5.3) |
| Phase-major recording (one barrier per phase across items) | Y | N/A (independent streams) | A (item-major encoders) | N/A | structural |
| Interleave depth of a fused batch | Y | N/A | A | N/A | measured per batch shape, **own rule** (§2.8) |
| SIMD/subgroup-scoped exchange barriers | A | A | Y (split-stage exchange only) | N/A | `TB <= subgroup size` (queried: spec constant 74 / `threadExecutionWidth` / warpSize) |
| Tier-0 gate as a bound, no lag election (`peakTwoGate`) | A | A | Y | Y (NEON fp16 gate is the same idea) | none: the consumer reads pass/fail only |
| Later tiers report the window maximum only | A | A | Y | n/a | none |
| No separate pack pass for the fp16 tier | Y (coarse reads fp32 bands, rounds in-kernel: `mfDataStride`) | **A** (pack_coarse 2.1 ms of ~25 ms fine device, CUDA table) | Y (`forward_tier0`: forward writes packed band 0) | N/A | two designs for one job (§2.3) |
| Band-only forward + survivor recompute | Y (fp32 band, by bytes model with measured f) | A | Y (inside `forward_tier0`, **always on**) | N/A | Vulkan: derived; Metal: env switch (§2.3) |
| Segment record/replay | Y (SegmentPlan, async, 2 in flight) | Y (segment graph, 2 in flight) | A (no SegmentPlan path) | N/A | structural |
| Replay contract (`SegmentPlan.run/submit`, slot halves, chain-trial guard) | Y | Y | - | - | shared in `time_domain.SegmentPlan` |
| Streams/queues spread across (context, slot) | lockstep phases instead | Y (8 fork streams) | A? (one batch queue) | N/A | CUDA: measured 8/16 vs 4 |
| Host-input buffers (host rewrites, device reads once) | N/A today (APU: one heap; dGPU: writes already go to ReBAR) | Y (`cuMemAdvise` host-preferred) | N/A (unified memory, `host_view`) | N/A | memory heaps (queryable) |
| Device follow-ups (select + layout + refineItems) | Y (host select, device refine) | Y (device select, layout, refine in the graph) | A (host path) | N/A | structural |
| Follow-up result assembly | Y, vectorised `_vkfollowup._assemble` | Y, `_gpuhost.read_followup_items` (vectorised on `parity/cuda-hostparse`) | host path | host path | **two implementations of one ordering rule** (§2.6) |
| Zeroing recordings reused per segment | br (`vk/replay-reads` c85d69a1) | N/A (one 2-D memset, captured) | A (per-row blit fills each call) | N/A | structural |
| GPU vs CPU for single-template calls | Y | Y | Y | - | shared code; **bare-median rule, per process** → fixed (§5.1) |
| Clock-reference calibration (`_ClockRef`) | Y (reference call) | Y (NVML clock) | Y (reference call) | N/A | shared; clock read where an API gives it |
| Chain / block-size / Q15 trials | Y | Y | Y | Y | `measured_choice`, ordered, in `MF_COST_FILE` |
| Coarse variant | spec-constant rule | Y, timed once, stored | rule (`threadExecutionWidth`) | Y (chain trials) | CUDA: a price (isolated, exact) |
| Platform FFT priced in the cost model | N/A | N/A | N/A | Y ARM vDSP; **A x86** (FFTW/MKL) | price per n (exact to fp32 rounding) |
| Streaming stores past the LLC (middle output copy) | N/A | N/A | N/A | Y x86+ARM | LLC size from the OS |
| Roofline peaks | formula: CUs x 128 x 2 x max sclk (sysfs) | formula: SMs x lanes(cc) x 2 x clock attr | formula: cores x 128 x 2 x vendor clock (table) | formula; bandwidth **measured** | §2.9 |

## 2. Per mechanism

### 2.1 Fused-batch chunk size

- **Vulkan** (`_vkcompute._FusedBatch.chunk = MF_GPU_FUSE_CHUNK or 16`) and **Metal**
  (`_mtlcompute._FusedBatch.chunk = MF_GPU_FUSE_CHUNK or 2`) implement the same protocol (the
  Metal class says so) with two hard defaults. Metal's 2 was measured on the M2 (16: 100.8,
  4: 95.8, 2: 92.6, 1: 93.6 ms/segment). Vulkan's 16 predates the measurement and has never
  been swept against the shared ladder.
- **What the chunk trades.** A smaller chunk starts the device sooner (it sat idle while the
  host filled 16 submissions on the M2). A larger one puts more items in each phase of a
  Vulkan recording, so more independent dispatches share each global barrier, and makes
  fewer, larger submissions (50-150 µs of driver CPU each on RADV, §14 of the Vulkan doc).
  Neither side is a queryable property: the optimum depends on host speed against device
  speed. So it is a measured choice, not a constant per backend.
- **Under segment replay the chunk barely matters on Vulkan**: a replay resubmits every
  fused recording of the segment as one submission (`replay_fused`); the chunk only shapes
  how the recordings were cut. It matters on the batched and `--pipeline` paths, and on
  Metal, which has no replay.
- **Measured on dev2** (§5.3): pipelined, chunk 2 is 10-25% slower than 16 in every round
  and costs 18% more host CPU; batched, 2/4/16 are inside the load noise. So the 8060S's
  optimum (16) is the opposite of the M2's (2). Two hard defaults are each right on one box
  and wrong on the other: the chunk is now one measured choice (§5.3).

### 2.2 SIMD-scoped barriers in the exchange

- Metal (e09794c2): in the split-stage exchange, a level whose blocks of TB threads fit in
  one SIMD group reads only columns that SIMD group wrote, so its barriers become
  `simdgroup_barrier(mem_threadgroup)`; the first barrier after a wider level stays
  threadgroup-wide. M2: full_series_8192 6.81 → 6.01 ms, segment -1%.
- **The argument is not Metal's.** It needs only "stage column = thread" and subgroups made of
  consecutive local invocation ids. It holds for the chunked exchange too (the one SPIR-V and
  PTX use): same column = thread layout, same TB-per-level structure.
- **Slang allows it on every target**: `GroupMemoryBarrierWithWaveSync()` lowers (checked
  with slangc 2026.12 on a probe kernel) to `OpControlBarrier Subgroup Subgroup
  AcquireRelease|WorkgroupMemory|...` (0x948) on SPIR-V, `__syncwarp()` on CUDA and
  `simdgroup_barrier(mem_flags::mem_threadgroup)` on Metal. The hand-written
  `__target_intrinsic(metal, ...)` can become that one intrinsic. (Recheck on the pinned
  2026.18.2 when the source is regenerated.)
- Caveats per target:
  - **Vulkan**: consecutive-id subgroups are what RADV, NVIDIA and Intel do, but the spec does
    not promise it without `VK_EXT_subgroup_size_control` (`requiredSubgroupSize` +
    `REQUIRE_FULL_SUBGROUPS`). The kernels already assume the subgroup size through spec
    constant 74; pin it at pipeline creation and the assumption is explicit. On RDNA a
    one-wave workgroup's `s_barrier` is already free, so the gain is only in multi-wave
    workgroups (WG 256 at n=2048 = 4 waves): the forward, refine and middle kernels, not the
    band-256 coarse.
  - **CUDA**: `__syncwarp` is right for warp-confined levels on sm_70+ (independent thread
    scheduling makes the barrier necessary, not optional).
- Expected value: Metal saw 12% on the one kernel it applied to. For Vulkan and CUDA it is a
  rebuild of shared source plus `--check cpu`; measure per kernel with the replay benches.
  **Request (kernel track, after the slangc regeneration lands): §6 R2.**

### 2.3 forward_tier0, band forward, pack removal: three designs for one job

The fp16 tier 0 needs its band packed to half2, the next tier needs its band in fp32, and only
refine-survivor blocks need the full spectrum. The three backends do this three ways:

| | forward writes | tier 0 reads | full spectrum | choice |
|---|---|---|---|---|
| Vulkan | `seriesForwardBands`: one fp32 band of max(B0, B1) | the fp32 band, stride `mfDataStride`, rounds to half in-kernel (no pack pass) | `markBlocks` + `seriesForwardListed` for survivor blocks | band iff measured refine-block fraction f < (n - B)/2n, else full forward |
| Metal | `forwardTier0`: B0 packed half2 + B1 fp32 | packed band 0 | the same `markBlocks` + `seriesForwardListed` | **always** when the consumer qualifies (`MF_METAL_FWD_TIER0`, default on) |
| CUDA | full fp32 spectrum | `pack_coarse` pass → packed | the full forward | none |

What this means:
- **Measuring forward_tier0 on Vulkan answers the wrong question.** On Vulkan the pack pass is
  already gone (§6 of the Vulkan doc), so forward_tier0 can only change bytes: per block it
  writes 4·B0 + 8·B1 against 8·max(B0, B1) for Vulkan's band, i.e. **4·B0 more** (1 KB per
  block at the (256, 512) chain, ~24 MB per ladder segment), and saves 4·B0 per group read in
  coarse0, where a group reads its data slice once for 8+ pairs. It is a loss or a wash on
  Vulkan by the bytes, before any timing. It was not built into the Vulkan host for that
  reason.
- **Metal's always-on choice is the gap.** At a refine-heavy chain, f approaches 1 and the
  recompute costs another forward of most blocks. Vulkan measured exactly this: (256,) with
  173k refined pairs correctly stays full. Empire's steady segments ran (256,) with ~150k
  refines per segment (d09e07be). Metal should take Vulkan's rule: per call shape, use the band
  forward iff the measured f is below the bytes break-even (for forward_tier0 the break-even is
  f < (8n - 4·B0 - 8·B1) / (2·8n)).
- **Metal could also try Vulkan's layout** (one fp32 band, in-kernel rounding: it is a
  specialization of the coarse build, `mfDataStride`), which writes fewer bytes. On a 93 GB/s
  device the 4·B0 bytes per block may matter more than on the 8060S. Measure both.
- **CUDA has neither**, and its table puts `pack_coarse` at 436 calls, 2.11 ms against
  4.55 ms for the forward: about 10% of fine device time and one launch per call on a
  launch-bound device. Both remedies are shared Slang (`forward_tier0.slang` already compiles
  with `-target cuda`; `series_bands.slang` too). **Request: §6 R1.**
- **Unification:** one host rule, `band_forward_pays(n, written_bytes_per_block, f)` in
  `_gpuhost`, used by all three; one kernel family (`forwardTier0` with B0 = 0 is
  `seriesForwardBands`). Not done here: the Metal side can only be measured on empire.

### 2.4 Segment replay / graphs

- CUDA (segment graph, prelude captured, device follow-ups, 8 fork streams) and Vulkan
  (SegmentPlan async, two in flight, recorded fused batches resubmitted) share the contract in
  `time_domain.SegmentPlan` (signature, slot halves, trace-the-second-run, no replay while a
  chain trial is open). That part is already one implementation.
- **Metal has no replay path**: `SegmentPlan` falls through to `filter_series_many`.
  - Metal command buffers are single-use, and indirect command buffers hold compute
    dispatches but no blits or waits. So a recorded replay as on Vulkan is not available.
  - What is available is the host half of the Vulkan gain. The Vulkan replay saved host CPU
    (33-38 → 24-26 ms per segment, 52ccea74) by not rebuilding layouts, keys and descriptor
    work per call. A Metal trace could store per dispatch (pso, buffers, offsets, grid,
    threadgroup) and re-encode from that list each segment, skipping the Python layout code.
    Encoding costs ~1-3 µs per dispatch in Objective-C messages, which is not avoided.
  - Expected value: the M2 segment is 93 ms with the GPU 89% busy; idle per segment is
    2.5 ms (middle) + 4.8 (fine) + 6.1 (follow-ups) (6840d85c). The follow-up idle is the
    larger target and is better addressed by device follow-ups (§2.6). **Medium, Metal
    agent: §6 R4.**

### 2.5 Host-input buffers

- CUDA: `empty_shared(input=True)` → managed memory advised host-preferred + accessed-by, so
  the host's per-segment write does not fault pages back and the kernels read once over the
  bus.
- Vulkan: `host_input` is accepted and ignored. That is correct for the memory types it picks:
  a host-written buffer is DEVICE_LOCAL|HOST_VISIBLE (ReBAR, write-combined) when the device has
  it, so the host write already goes straight to device memory, and on the APU there is one
  heap. There is no migration to avoid. The one case left is a dGPU without ReBAR (host-visible
  memory only in system RAM), where the current choice is already the host-memory one. N/A.
- Metal: unified memory, and `host_view` already maps caller memory in place. N/A.
- The flag is now part of the shared `empty_shared` API with a per-backend meaning. That is the
  right shape: a hint, honoured where the memory model has the distinction.

### 2.6 Follow-ups: device work and result assembly

- Device work: CUDA selects, lays out and refines on the device inside the graph
  (`followup.cu` + `refineItems`); Vulkan selects on the host and runs forward + `refineItems`
  as one fixed recording per template group (`_vkfollowup`); Metal runs follow-ups on the host
  path (single-template calls, each now a GPU-or-CPU choice, §5.1).
  - `refineItems` is shared Slang already. The selection kernels (`followup.cu`) are CUDA C, not
    Slang, so Vulkan cannot take them.
  - Metal: the `_vkfollowup` design (fixed recording per group, rows written by the host)
    maps onto Metal as one encoder per group with indirect dispatch
    (`dispatchThreadgroupsWithIndirectBuffer`). With 6.1 ms of device idle in the M2
    follow-ups, this is the Metal follow-up lever. **§6 R4.**
- Assembly: two implementations of the same ordering rule (hits by bin count, then block,
  then bin, per item), both vectorised now:
  - `_vkfollowup.Executor._assemble` (52ccea74),
  - `_gpuhost.read_followup_items` (CUDA; vectorised on `parity/cuda-hostparse`, not merged).
  
  After that branch merges, `_assemble` should call one shared per-item routine (the
  layout-and-hits part of `read_followup_items` taking `(st, ws, we, idx, val)`), so a fix to
  the ordering lands once. Not done here: it edits the file the CUDA host-parse agent owns.
  **§6 R5 (coordinator).**
- Selection: `FollowupSpec.select` (host) and `followup.cu` (device) must agree exactly. That
  test exists for CUDA. A Slang port of the select kernel would give Vulkan and Metal the
  device selection and remove the host round trip on Vulkan's replay.

### 2.7 Zero-fill recordings

- Vulkan records `zero_columns_done` afresh every call (allocate, one `vkCmdFillBuffer` per
  row, free). The Vulkan replay agent keeps those recordings on `vk/replay-reads` (c85d69a1),
  keyed on the allocations held by the entry (not on handles, which avoids the ABA class).
- CUDA: one `cuMemsetD2D32Async`, captured into the graph. N/A.
- Metal: one `fillBuffer:range:value:` per row per call into a blit encoder, with no reuse API
  for blits. The transferable part is CUDA's: **one strided 2-D clear** instead of N per-row
  fills. On Vulkan that is a single compute dispatch (a `zero2d` kernel in shared Slang); on
  Metal the same kernel in a compute encoder. Small host saving per call (rows x message
  cost); low priority.

### 2.8 Measured choices: pricing against trials, and the one rule

`measured_choice` is the shared rule (model stands unless beaten past TIE and 2 standard
errors; unclear → more samples to a cap; persisted). Its doc, and a44346bb on `arm-cpu2`, set
the split: **price** a candidate in isolation when results are equal and it affects one part
(a kernel variant, a transform); **trial** whole batches when it interacts with the rest.

Every measured choice in the tree, and its rule:

| Choice | Backend | Kind | Rule | Persisted |
|---|---|---|---|---|
| block size | all | trial (batch) | `measured_choice` | Y |
| chain (CPU per call, GPU per batch) | all | trial | `measured_choice` | Y |
| Q15 screen | CPU | trial (call) | `measured_choice` | Y |
| platform FFT (vDSP) block forward, middle | ARM | price | cheaper of two timings | Y |
| CUDA coarse variant | CUDA | price | min of 3 | Y |
| Vulkan band/full forward | Vulkan | derived | bytes model with measured f | n/a |
| **interleave depth** | Vulkan | trial (device timestamps per batch) | **own rule**: min of medians with a 5% margin, fixed 5 samples | Y |
| **GPU or CPU for single-template calls** | all GPU | trial (call) | **own rule**: min of medians after 3 samples | **N** |
| **fused chunk** | Vulkan, Metal | none | **constant per backend** | - |
| Metal forward_tier0 | Metal | none | env default on | - |
| CUDA segment streams / spread | CUDA | none | constant 8 (measured once) | - |

The three bold rows were where the rule was not shared. §5 puts all three on
`measured_choice` (the fused chunk as a new ordered calibration). Metal forward_tier0 and the
CUDA stream count stay as they are: the first should become derived (§2.3, R3); the second is a
CUDA-only structure with a measured flat optimum (8 = 16).

### 2.9 Roofline peak formulas

All four have the same shape, units x lanes x 2 x clock, and state their formula. Differences
that make fractions not comparable across platforms:
- **Bandwidth basis differs.** CPU: one core's streaming copy, measured. GPUs: vendor
  formula (CUDA from attributes, Vulkan from a per-arch table, `_AMD_MEM = {gfx1151: ...}`, NaN
  for any other AMD GPU; Metal from a chip table). Measured ceilings exist for every GPU
  (`_MEASURED`: 198 vs 256 GB/s on the 8060S, 623 vs 864 on the L40S, 93.4 vs 102 on the M2)
  but are "not used". So a GPU fraction is against a 1.3-1.4x higher ceiling than a CPU
  fraction.
  - Proposal: one basis. Either measure a device-to-device copy on every GPU at ladder start
    (as the CPU does: 2-3 small dispatches, no table needed, works on any Vulkan device), or
    report both and compare on the measured one.
- **Clock basis differs.** CUDA: `CLOCK_RATE` attribute (boost). Vulkan: max of sysfs
  `pp_dpm_sclk` (Linux amdgpu only; falls back to a constant 2.9 GHz elsewhere). Metal: chip
  table. CPU: `cpuinfo_max_freq`. All are "max sustainable clock" except that the 8060S never
  reaches it under this host's load (600 MHz all run). That is a measurement condition, not a
  formula error, but the ladder should print the measured mean clock next to the fraction
  (it does for Vulkan through sysfs; CUDA could via NVML, which `_ClockRef` already reads).
- **int16 on GPUs is set to fp32 (CUDA, Metal) or 2x fp32 (Vulkan).** No GPU tier runs int16
  arithmetic, so the row is unused; drop it from GPU peaks rather than guess.
- **RDNA detection** is `arch.startswith("gfx11")`. RDNA 4 (gfx12) is also dual-issue; the
  test should be "gfx11 or later".
- CUDA lanes per SM come from a compute-capability table (no API gives them). Acceptable;
  falls back to 128.

### 2.10 Metal-only gate kernels that apply everywhere

Two Metal changes in `tierb.slang` are gated `MF_METAL` though nothing in their argument is
Metal-specific:
- **`peakTwoGate`** (2e1602b6): tier 0 reports the bound B = sqrt(P16max)(1 + 2u) +
  κ·u·rms(y) from packed half2 maxima instead of electing a lag. The compaction reads
  pass/fail only. M2: 1.249 → 1.116 ms (-11%), segment -5%, gate_margin clean.
  - On Vulkan, coarse0 is the largest kernel (4.8 of 10.3 device ms per segment at full
    clock, §14). Vulkan's election is the cheaper wave-shuffle one (`peakTwoWave`), so the
    gain will be smaller than on the M2, but the energy and overflow work it removes is the same.
  - CUDA: tierb_64_c16p16 and tier1_256 are its third and second largest fine kernels.
- **Later tiers report the window maximum only** (e7823ad5): tier 1 -14% on the M2.

Both are shared-source edits followed by regeneration and `gate_margin --gate gpu-c16 --loud`.
**Request: §6 R2.**

### 2.11 Concurrency inside a batch

Each backend gets concurrency between a segment's ~50 bank calls differently:
- Vulkan: phase-major fused recording, one global barrier per phase across all items;
  optional interleave of two halves.
- CUDA: each (context, slot) on one of 8 fork streams in the graph (6e299074: 11.6 → 10.0 ms
  device per segment).
- Metal: the fused batch shares command buffers, but each context encodes its own whole call
  (item-major), with hazard tracking between encoders.

The Vulkan form is the portable one: Metal can encode phase-major in one
`MTLDispatchTypeConcurrent` compute encoder per phase with `memoryBarrierWithScope:` between
phases. That is a restructure of `_mtlcompute`'s fused path, so it is a candidate for the Metal
agent, and should first be checked against the M2's GPU-busy figure (89%): it pays only if
dispatches are small enough to leave the GPU underfilled. Low-medium.

### 2.12 CPU mechanisms

- **Streaming stores past the LLC** (6b15bb83): LLC size from the OS, so it is already a
  queryable-property rule and covers x86 and ARM. GPU N/A (no RFO on GPU stores).
- **Platform FFT priced** (4d6f9c4f..beff0a71): vDSP block forward and middle correlation,
  priced per n.
  The same pricing hook fits x86 with FFTW or MKL when present (FFTW PATIENT is 3.0 µs against
  ~4.4 µs for the engine at 2048 points on the M2 core; the x86 ratio is unmeasured). The
  mechanism (`_core.forward_cost`, keep the cheaper per n, store in `MF_COST_FILE`) is backend-
  neutral; only the library binding is per platform. **§6 R6 (CPU agent).**

## 3. Duplicated code (current)

| What | Where | Proposal |
|---|---|---|
| `_FusedBatch` protocol | `_vkcompute`, `_mtlcompute` (different internals, same contract and same env var) | a shared `fused_chunk(dev)` decision (§5.3) |
| `_COARSE_TILE_T` | `_vkcompute` l.50, `_mtlcompute` l.119, `_cudacompute` l.333 (CUDA lacks 64) | read from the build manifests: the builds define the tile |
| follow-up assembly | `_vkfollowup._assemble`, `_gpuhost.read_followup_items` | one per-item routine in `_gpuhost` (§2.6) |
| band-forward rule | `_vkcompute._band_wanted`; Metal has none | `_gpuhost.band_forward_pays` (§2.3) |
| zero fills | three hand-written | one `zero2d` kernel (§2.7) |
| `_COARSE_TILE = {}` | `_vkcompute` l.128 | dead since the 10-09 review; delete |
| CUDA register cap `65536 // wg` | `_cudacompute` l.1072 | `CU_DEVICE_ATTRIBUTE_MAX_REGISTERS_PER_BLOCK` |

## 4. Gaps ranked by expected value per unit of complexity

| # | Gap | Backends | Expected value | Complexity | Who |
|---|---|---|---|---|---|
| 1 | No pack pass and band forward on CUDA (`forward_tier0` or direct band read) | CUDA | ~10% of fine device time (pack 2.11 of ~25 ms) and a launch per call on a launch-bound device | low: shared Slang builds with `-target cuda`; host follows Metal's or Vulkan's path | CUDA agent (R1) |
| 2 | Metal band forward always on: no f rule | Metal | avoids a second forward of most blocks at refine-heavy chains ((256,) on empire) | low: port `_band_wanted` | Metal agent (R3) |
| 3 | `peakTwoGate` and max-only later tiers off Metal | Vulkan, CUDA | -11% / -14% kernel on M2; coarse0 is Vulkan's largest kernel | low-medium: shared source + regen + gate_margin | kernel track after regen (R2) |
| 4 | Measured choices outside the shared rule (single-template device, interleave) | all GPU / Vulkan | reproducible choices; no per-process re-trial; noise-proof | low | **done here (§5.1, §5.2)** |
| 5 | Fused chunk a per-backend constant | Vulkan, Metal | 10-25% pipelined on the 8060S at the wrong value, 9% on the M2 | low-medium | **done here (§5.3)**; Metal confirms (R7) |
| 6 | Subgroup-scoped exchange barriers on Vulkan/CUDA | Vulkan, CUDA | Metal: -12% on one kernel; on RDNA only multi-wave groups | low (one intrinsic) but needs pinned subgroup size | kernel track (R2) |
| 7 | Metal follow-ups on the device | Metal | 6.1 ms of device idle per M2 segment | medium | Metal agent (R4) |
| 8 | Follow-up assembly in one place | Vulkan, CUDA | maintenance (one ordering rule) | low, after hostparse merges | coordinator (R5) |
| 9 | Roofline: one bandwidth basis | all | comparable fractions | low | any |
| 10 | Platform FFT pricing on x86 | CPU x86 | unmeasured; up to the vDSP gain on the forward | medium (binding) | CPU agent (R6) |
| 11 | Metal SegmentPlan (host trace, re-encode) | Metal | host share of 93 ms; follow-ups dominate idle | medium-high | Metal agent (later) |
| 12 | Metal phase-major concurrent encoders | Metal | only if the GPU is underfilled | medium-high | Metal agent (later) |

## 5. Implemented on this pass

Each item is on its own branch from origin/main beff0a71 (pushed): `xplat/single-device-rule`,
`xplat/interleave-rule`, `xplat/fuse-chunk-trial`. All three are host Python; no C or kernel
changes. Gates: see §5.4.

### 5.1 `xplat/single-device-rule`: the single-template GPU-or-CPU choice by the shared rule

`TimeDomainFilterBank._single_device` (shared code, every GPU backend) chose GPU or CPU for
single-template calls by a bare minimum of medians after 3 samples per side, made afresh in
every process. Now:
- `measured_choice` with the bank's own device as the model, decided on whole pairs (the sides
  alternate), up to 5 samples per side when unclear;
- the lock is stored in `MF_COST_FILE` (`single-device|dev|n|blocks`) and reused untimed.

Deterministic tests: a clear CPU win locks and a new process reuses it; a noisy CPU "win"
keeps the GPU after the cap (a bare median picked whichever side the noise favoured). This
changes reproducibility, not speed: the ladder's device follow-ups do not take this path.

### 5.2 `xplat/interleave-rule`: the Vulkan interleave depth by the shared rule

The fused batch's interleave depth (0 or 3, device-timestamped per batch shape) used 5 samples
and a 5% margin of its own. Now `measured_choice` with lockstep (0) as the model: 5 samples
each, then the rule; unclear contests sample to 10 each; still stored per (device, shape).

dev2, batched ladder from the primed file with its interleave locks removed: the mark/recompute
batch shape locked 0 under the shared rule; the same shape had locked 3 under the old rule in
the priming run. At 600 MHz the two depths are within noise of each other (§12 of the Vulkan
doc saw the choice flip with the clock), which is exactly the case where the model should
stand rather than a 5-sample coin flip.

### 5.3 `xplat/fuse-chunk-trial`: the fused chunk as one measured choice (Vulkan and Metal)

**Measurement first** (dev2, one primed cost file copied into each run, alternating rounds;
segment = steady wall per segment; fine = fine-stage wall over the steady segments):

| mode | chunk | round 1 | round 2 | round 3 | host CPU (s) | sclk MHz |
|---|---|---|---|---|---|---|
| `--pipeline`, 16 steady segments | 16 | 49 ms | 55 ms | 62 ms | 0.69 / 0.71 / 0.76 | 1748 / 1387 / 611 |
| | 2 | 66 ms | 68 ms | 68 ms | 0.85 / 0.90 / 0.86 | 612 / 607 / 608 |
| batched, 8 steady segments | 16 | 95 ms (fine 0.32 s) | 101 (0.40) | 81 (0.29) | 0.35 / 0.33 / 0.39 | 607 / 1111 / 600 |
| | 4 | 98 (0.33) | 85 (0.32) | 76 (0.30) | 0.43 / 0.38 / 0.33 | 737 / 608 / 600 |
| | 2 | 106 (0.37) | 89 (0.32) | 81 (0.32) | 0.40 / 0.41 / 0.36 | 629 / 600 / 602 |

- Pipelined, 2 is slower in every round; at equal clock (round 3, both ~610 MHz) by 10%, with
  18% more host CPU. Part of the gap in rounds 1-2 is the clock: with chunk 16 the APU's GPU
  clock rose, with chunk 2 it never did (more, shorter submissions keep the host busier on a
  shared power budget).
- Batched, the three are inside the run-to-run noise at load 35-55.
- The M2 measured the reverse (2 best, 16 +9%). So the chunk is a host-against-device
  property, not an API one, and both constants were per-machine special cases.

**Change.** `time_domain._FuseChunkTrials`, used by both backends through a new
`fuse_chunk(dev)` in `_vkcompute` and `_mtlcompute`:
- the last of the ordered calibrations: a batch is a sample only when no block-size or chain
  trial of the batch is open and no bank calibrates;
- candidates (2, 16) plus the backend's default, which is the model (Vulkan 16, Metal 2: the
  measured values become priors, not answers); each runs 1 warm batch (the new cut records
  new fused buffers) then 4 samples in a row;
- the sample is the one block-size and GPU chain trials take: the whole `filter_series_many`
  batch from submission to last result, per unit of work;
- `measured_choice`, cap 8, bounded in batches; lock in `MF_COST_FILE`
  (`fuse-chunk|backend|device`), reused by later processes; trials only where a cost file
  keeps the lock;
- a `SegmentPlan` runs its job set batched while its device's chunk trial is open (the guard
  chain trials use), so replay cannot starve the trial;
- `MF_GPU_FUSE_CHUNK` still forces a chunk.

dev2, pipelined ladder from the primed cost file (no fuse-chunk entry): the trial ran after the
other locks and locked 16 within 24 segments (`MF_AUTOTUNE_LOG`: medians 1.67e-11 s/unit at 2
against 3.61e-12 at 16). The chunk-2 samples are 4.6x, far more than the 10-25% wall gap of
the A/B. Not yet explained; the likely cause (unverified) is the fused-recording cache: at 2
a ~50-item batch is cut into ~25 fused recordings, and with several batch shapes in flight
that may exceed `MF_GPU_FUSE_CACHE` (64), so the trial's chunk-2 batches re-record. Either way
the direction agrees with the A/B, and a cache that thrashes at a small chunk is a cost the
trial should see.

Tests (deterministic, fake backend module): a clear win locks, is stored and is reused
untimed; a noisy "win" samples further and the model stands; no trial while another trial is
open, nor without a cost file.

### 5.4 Gates

All three branches merged into one local stack on beff0a71 (`_core` rebuilt for main's C
changes), then:
- `ladder --check cpu`, 4 segments: batched 264 calls, max |Δsnr| 3.4e-5, 0 one-sided peaks,
  0 gate-margin peaks; `--pipeline` 264 calls, 2.97e-5, 0, 0;
- `tools/gate_margin.py --gate q15 gpu-c16 --loud`: exit 0, 46/46 ok;
- `tests/test_measured_choice.py` on each branch alone: 14 / 12 / 14 passed; the GPU
  single-template tests of `test_time_domain.py` on `xplat/single-device-rule`: 4 passed;
- full suite on the stack: the first run was killed externally (SIGTERM) at 80% with no
  failure up to then; the rerun result is in the hand-off report.

## 6. Requests for the owning agents

- **R1 (CUDA agent): remove the pack pass on CUDA.** Build `forward_tier0_<n>` PTX (it compiles
  with `slangc -target cuda`; needs NVRTC) and take Metal's host path in `hier_peaks` when the
  consumer reads exactly its spectra (fp16 tier 0, ≤ 2 tiers): forwardTier0 into the packed
  band 0 + fp32 band 1, `markBlocks` + `seriesForwardListed` before the refine. Use the
  band/full rule of R3, not an always-on switch. Measure: `cuda_roofline.py` pack_coarse and
  forward rows, ladder `LADDER_INFLIGHT` segment ms, 3 alternating rounds; gate with
  `--check cpu` (batched, pipeline) and `gate_margin --gate gpu-c16 --loud`. Alternative to
  compare: the Vulkan direct read (fp32 band, `mfDataStride` as a kernel argument).
- **R2 (kernel track, after the pinned-slangc regeneration lands):**
  (a) drop the `MF_METAL` guard on `peakTwoGate` and on the max-only later tiers so SPIR-V and
  PTX build them; the host passes the gate threshold in `thrBits` exactly as `_mtlcompute`
  does. Vulkan: measure coarse0 CU-cycles per pair (the §3 method of the Vulkan doc) and the
  inflight ladder; CUDA: the roofline table. Gate: `gate_margin --gate gpu-c16 --loud` (0
  dismissals, margin use < 0.5).
  (b) replace `mfSimdBarrier`'s Metal intrinsic with `GroupMemoryBarrierWithWaveSync()` and
  apply the `TB <= subgroup` rule to the chunked exchange too; on Vulkan pin the subgroup size
  with `requiredSubgroupSize` for those pipelines. Measure the forward/refine/middle kernels
  per backend; keep only where faster.
- **R3 (Metal agent): the band/full rule for `forward_tier0`.** Replace `MF_METAL_FWD_TIER0`'s
  default with Vulkan's derived rule: per call shape, the band forward iff the measured
  refine-block fraction f < (8n - 4·B0 - 8·B1)/(16n); first call full. Put the rule in
  `_gpuhost` and have `_vkcompute._band_wanted` call it with its own written bytes. Measure at
  the chain the M2 locks and at (256,) forced (`MF_CHAIN_FORCE`). Also try Vulkan's single fp32
  band with in-kernel rounding (`mfDataStride` as a function constant).
- **R4 (Metal agent): device follow-ups** in the `_vkfollowup` design (one encoder per
  template group, forward + `refineItems`, indirect dispatch on host-written counts), then a
  host-trace SegmentPlan only if the remaining host share justifies it.
- **R5 (coordinator): follow-up assembly.** When `parity/cuda-hostparse` merges, make
  `_vkfollowup._assemble` call the shared per-item layout-and-hits routine from
  `read_followup_items` (or the reverse); one ordering rule.
- **R6 (CPU agent):** the platform-FFT pricing hook for x86 (FFTW or MKL where installed):
  `_core.forward_cost` and the per-n keep-the-cheaper rule are backend-neutral; only the
  binding is per platform. Measure the 2048-point forward first; build only if it beats the
  engine by more than the copy it adds.
- **R7 (Metal agent): confirm the fused-chunk trial on the M2** (`xplat/fuse-chunk-trial`).
  With a primed cost file and no `fuse-chunk` entry, `MF_AUTOTUNE_LOG=1` should print
  `FUSE-CHUNK fuse-chunk|mtlcompute|0 -> 2` within ~12 batches after the chain lock, and the
  ladder segment should match the 92.6 ms of 6840d85c. If the M2 prefers 1 or 4 by more than
  the tie, add it to `_FUSE_CHUNK_CANDIDATES` (each candidate costs ~5 trial batches once per
  machine).

## 6a. Next phase (deferred larger unifications)

1. One band-forward rule and one kernel family across the three GPUs (§2.3; R1, R3).
2. `peakTwoGate`, max-only later tiers and wave-scoped exchange barriers in the SPIR-V and PTX
   builds (§2.2, §2.10; R2), after the pinned-slangc regeneration.
3. One follow-up assembly routine (§2.6; R5) and a Slang port of the follow-up selection, so
   Vulkan and Metal select on the device as CUDA does.
4. Metal device follow-ups, then a host-trace SegmentPlan (§2.4; R4).
5. `hier_peaks` as one shared sequence in `_gpuhost` over per-backend primitives (still three
   copies; §9).
6. Tables the builds already know (`_COARSE_TILE_T` x3) read from the build manifests (§3).
7. One roofline bandwidth basis: a measured device copy on every GPU (§2.9).
8. One `zero2d` kernel for every backend's strided clears (§2.7).

## 7. Areas other agents own (not touched)

- Vulkan host replay reads, zero-recording reuse: `vk/replay-reads`.
- CUDA host parse, `read_followup_items`: `parity/cuda-hostparse`.
- slangc regeneration of every kernel: `regen/slang-2026.18.2`. Every kernel request above
  (R1, R2) waits for it.
- x86 int16 screen.

## 8. Method notes

- Every comparison is alternating rounds with one primed cost file copied into each run, so
  the layout, chain, screen and interleave choices are identical between arms.
- The 8060S ran at 600-740 MHz in every run (APU power shared with a host at load 45-55). A
  host-side lever shows more at this clock than at 2.9 GHz; a device-side lever less.

## 9. The 2026-10-09 review's items, status

- `minStorageBufferOffsetAlignment`, `maxComputeWorkGroupSize`, shared `pack_half2` and sparse
  helpers: merged.
- Clock-reference calibration on Vulkan and CUDA: done (`_ClockRef` is backend-neutral; CUDA
  reads the NVML clock).
- One narrow-gate harness (`tools/gate_margin.py`): done; the GPU large-value bug it found is
  fixed (the gate runs `--loud` in every merge gate).
- Shared host layer (`_gpuhost`): partly (FollowupSpec, item records, hier tiers/windows,
  grouped windows). `hier_peaks` per backend is still three copies.
- Metal `TARGET_THREADS`: replaced by `threadExecutionWidth`. CUDA register cap and
  `_COARSE_TILE` dead dict: still open (§3).
- One Slang source for CUDA: `forward_tier0`, `refineItems` and the series kernels are shared;
  the CUDA coarse gate is still its own (`coarse_tc.cu`, tensor cores, CUDA-only by nature).
