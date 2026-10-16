# Next phase: converging the CPU and GPU paths

Review of main at 147bb4a2 (2026-10-16), and the plan that follows from it. The phase before
this one (docs/unification-plan.md) shared the coarse tier: one launch rule, one measured
choice engine and one conformance suite. Most of the remaining divergence is above the kernels:
which host path each backend takes through a call, and which optimisations exist on only one
backend.

## Ground rules

Same as the previous phase:

- **No performance loss.** Each step is checked with a paired ladder on every backend it
  touches: 8060S (dev2), M2 and L40S. Both trees use one cost file whose trials are already
  settled (a seed taken after one run measures trial exploration, not code). Device time is
  logged next to throughput.
- **Exactness before every merge:** the dev2 gate, the M2 suite and both ladder checks, and
  the L40S suite, cval.sh and conformance, each run as a foreground step.
- **One step per commit, merged in gated groups.** CI must be green after each push.

## How the review was done

- **Production coverage:** the line coverage of the production ladder (tools/ladder.py,
  test27 bank and profiles), measured on the 8060S (batched, pipelined and CPU) and on the M2
  (batched).
- **Divergence:** a per-backend comparison of the public methods and capability flags of
  the three `Context` classes, and the shared code that branches on them.
- **Paired measurements** wherever a finding claimed a cost.

## Findings

### 1. Production takes different host paths per backend

| | Vulkan | CUDA | Metal |
|---|---|---|---|
| Hierarchical call over several window groups | one grouped dispatch (row windows, `_gpuhost.hier_peaks_grouped`) | one grouped call, own 77-line implementation (a launch per group) | **per-group path**: a submission per window group, padded |
| Follow-ups | on the device (`_vkfollowup`, 396 lines) | on the device (`_cudafollowup`, 246 lines; different design) | **on the host** (`peaks_items`, 90% covered in production) |
| Forward of the fine series | band-only forward when it moves fewer bytes (measured rule) | full forward | fused tier-0 forward, always on (`MF_METAL_FWD_TIER0`) |
| Segment replay (`SegmentPlan`) | recorded command buffers (`replay_fused`, capture) | CUDA graphs (`SegmentGraph`) | none |

### 2. Dead and obsolete code in the paths that run

- **Padding to 16 pairs** (`__init__.py`, the per-group path: `pad_unit`, `count_p`, the
  `pads_coarse_groups` flag). Every coarse launch has been ragged since the previous phase, so
  the copies of the last block are wasted work.
  - Vulkan and CUDA never reach this path in production.
  - Metal does: 210,000 blocks dispatched for 198,928, over 1,296 dispatches (+5.6%).
  - Paired on the M2 (rounds 1-4), padding removed: pipelined 2.486-2.493e7 against
    2.417-2.458e7 (+1.4-3%); batched 2.649-2.71e7 against 2.638-2.658e7 (0 to +2.6%).
- **Capability flags:**
  - `supports_device_followups` is read nowhere.
  - `pads_coarse_groups` exists only to opt out of the padding.
  - `supports_ragged_bins` (Metal only) and `supports_ragged_hier` (Vulkan only) name two
    halves of one capability.
- **`src/gpu/draft/`:** 500 lines of archived shaders that are neither built nor dispatched.

### 3. `SegmentPlan` has no production consumer

- It is 476 lines in `time_domain.py`, plus the Vulkan capture/replay internals and CUDA's
  `SegmentGraph`.
- pycbc (pycbc-work/apogee, `matched_filter_ratio.py`) calls `filter_series` once per
  bank. The ladder uses `SegmentPlan` only under `LADDER_REPLAY`, and the gate's replay step
  tests it.
- Its measured gain is real: Vulkan 15.8 → 14.7 ms per segment, plus CUDA graphs.
- The pycbc integration has not yet decided whether to use it, and it is the largest
  backend-specific subsystem left.

### 4. The orchestration functions are long because they hold every path

| Function | Lines | Covered on 8060S | Covered on M2 |
|---|---|---|---|
| `MatchedFilter._run_series_gpu` | 421 | 48% | per-group branch covered |
| `TimeDomainFilterBank.filter_series` | 337 | 68% | — |

Each backend uses a different subset of their branches. That subset is the real code
divergence, and it does not show up as copied text.

### 5. CPU and GPU reduced-precision gates are consistent but documented apart

- The CPU fp16 gate (`gate16.cc`, ARM) and the GPU fp16 tier (`tierb.slang`) use the same
  bound, `|y|(1+3u) + κ·u·rms(y)`. Each κ is measured separately.
- The Q15 screen (x86) has its own bound.
- `tools/gate_margin.py` covers all three (`q15`, `gpu-c16`, `cpu-g16`), but the conformance
  suite (exact gate decisions per layout) covers only the GPU backends.

### 6. Already converged (no work proposed)

- The kernels: about 88% of the Slang source is shared.
- The coarse tier: the launch rule, the measured choice with its re-check, the layout
  names, and the conformance suite.
- Result ownership, the async contract, cost-file handling, and the windowing helpers
  (`_gpuhost`).

## Plan

Ordered by value over risk. Each step lists its evidence, its change and its acceptance
check.

### Step 1: delete what nothing needs (low risk)

1. **Remove the padding.** Delete `pad_unit`/`count_p` and the `pads_coarse_groups` flag.
   - Expected: Metal +1.4-3% pipelined (measured above); Vulkan and CUDA unchanged.
   - Accept: M2 paired ladder at least equal, and every gate.
2. **Remove `src/gpu/draft/`.** The shaders stay in git history.
3. **Audit the capability flags.** Each flag must name a real capability difference that
   shared code reads, or it goes:
   - drop `supports_device_followups`;
   - merge `supports_ragged_bins` and `supports_ragged_hier` into one flag;
   - give the CUDA-only extras (`timing`, `kernel_info`, `clock_mhz`) the shared names
     (`timings`) or move them to the roofline tool.

### Step 2: one grouped hierarchical path on every backend

- **Make the shared row-window path universal.** `_gpuhost.hier_peaks_grouped` runs one
  dispatch per tier over every row, each row with its own window (row windows). Vulkan
  uses it; CUDA and Metal get it.
  - The kernel code exists (`tierb.slang` `rowWindow`), but on CUDA and Metal
    `mfRowWindows` is compiled to a static 0 (`twiddle.slang`).
  - Each needs the switch the twiddle source got: a CUDA module constant (like
    `mf_c16_raw`) and a Metal library macro (like `MF_COARSE_TWT`), plus the row-window
    buffer binding.
- **Then delete the per-group GPU path in `_run_series_gpu`.** The CPU keeps its own path.
  CUDA's own `hier_peaks_grouped` (77 lines) goes too.
- **Expected:**
  - Metal does one submission per call instead of one per window group. On CUDA, a deferred
    hierarchical call became one submission per window group: 3× the submissions and
    1.4× slower.
  - Roughly 150-200 lines of host branches disappear.
- **Accept:**
  - conformance plus a new grouped conformance case on all three backends;
  - paired ladders on all three: Metal faster or equal, Vulkan and CUDA equal.

### Step 3: one device follow-up design

- **Split the follow-up code.** Factor what `_vkfollowup` and `_cudafollowup` share into
  `_gpuhost`: the entry lists, the workspace layout, and the assembly identical to
  `_items_batch`. Leave each backend only an executor (Vulkan: one recording, replayed;
  CUDA: enqueue; Metal: one command buffer).
- **Then Metal gets device follow-ups**, and `peaks_items` leaves the production path on
  every backend.
- **Expected:** fewer host round trips for Metal follow-ups, and two designs become one.
  The size of the Metal gain is not measured yet: measure the share of Metal segment time
  spent in follow-ups first, and skip the Metal executor if it is small.
- **Accept:** the follow-up results match the host path exactly (the existing follow-up
  tests, run on every backend), and paired ladders.

### Step 4: one band-only forward rule

- **One decision on every backend.** Vulkan's band forward and Metal's fused tier-0
  forward are the same idea: forward only the coarse bands, then recompute the blocks
  whose pairs survive. Use Vulkan's bytes rule on every backend: bands win when the refined
  block fraction f < (n − B) / 2n, with f measured on the call shape's previous run.
- **One kernel family**: `forward_tier0` / `series_bands`. CUDA gets it as a candidate, not
  a default.
- **Expected:** measured per backend; nothing changes unless the rule picks bands and the
  paired ladder confirms it.
- **Accept:** exact checks, and paired ladders including a case with many refined blocks
  (low threshold) where the full forward must still win.

### Step 5: split the orchestration functions by path

- After steps 2-4, each backend runs the same branch set.
- `_run_series_gpu` and `filter_series` then split into named stages (layout, upload,
  dispatch, collect) that every backend runs. The CPU path stays separate where its
  execution model differs.
- No behaviour change; paired ladders to confirm.
- **Recurring check:** re-run the production coverage measurement after this step. Any
  branch that no backend's production run reaches becomes a deletion candidate, or gets a
  test that justifies keeping it.

### Step 6: one conformance suite across CPU and GPU

- **Extend `test_coarse_conformance`'s exact-decision method to the CPU tiers.** Force the
  Q15 screen, the fp16 gate on ARM, and the plain fp32 gate through the same thresholds in
  wide gaps of the exact maxima, then require the same refined pairs and peaks as the GPU
  layouts.
- **Write one error-model document** for the three reduced-precision gates (the shared
  bound, each κ and how it was measured), referenced from `gate16.cc`, `tierb.slang` and
  the Q15 code.
- **Accept:** the suite runs on dev1 (AVX2), dev2 (AVX-512), the M2 (NEON with fp16) and
  every GPU backend.

### Standing measurement tools

- **Add `tools/ab_ladder.py`**: a paired ladder that seeds one settled cost file per run
  and reports device time with throughput. This session lost hours to two seeding
  mistakes; one script prevents both.
- **Keep the production-coverage measurement as a tool**, run after each step on each
  backend.

## Decisions for you

1. **`SegmentPlan` (finding 3).** Recommended: freeze it (keep it tested, port nothing,
   no new work) until the pycbc integration decides whether it calls it. If the integration
   will not use it, retire it in step 5; that removes the largest backend-specific
   subsystem. The alternative is to port it to Metal now so every backend has replay.
2. **Metal device follow-ups (step 3).** Recommended: measure first and port only if the
   follow-up share of segment time is significant. The shared refactor is worth doing
   either way.
3. **Building the kernel files in CI** (deferred from the previous phase): still your call.
   It does not block anything here.

## Order and effort

| Step | Effort | Validation needed |
|---|---|---|
| 1 | about half a day | — |
| 2 | about 2 days | all three GPUs |
| 4 | about 1-2 days | — |
| 3 | about 2 days, plus Metal if measured worthwhile | — |
| 5 | about 2 days | — |
| 6 | about 1-2 days | dev1 and the M2 |

Order: 1, then 2, then 4, then 3, then 5, then 6. Steps 1 and 6 do not depend on the others.
