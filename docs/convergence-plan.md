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

## Log

- 2026-10-16: **Step 0: `SegmentPlan` removed** (1dc65f36). Its only users were the gate's
  replay step and an opt-in ladder mode.
  - Removed: 2,817 lines, including the Vulkan prelude-capture and replay machinery, CUDA's
    `SegmentGraph` and every hook it had in CUDA's copy, launch and stream paths, the per-call
    trace bookkeeping in `MatchedFilter`, slot halves, and CUDA's device follow-ups (reachable
    only through it).
  - The gate's replay step became `settled`: the same check after the trials have locked.
- 2026-10-16: **Step 1: padding and drafts removed** (475c0ab7). Paired, steps 0-1 together
  against 693b6a0b:
  - M2: batched +3.8%, pipelined +4.5%; fine-stage device time 0.43 -> 0.40 s, from the
    padded blocks Metal no longer dispatches.
  - 8060S: batched +0.5%, pipelined +3.6%; host time 0.20-0.21 -> 0.195-0.199 s, from the
    removed hooks.
  - L40S: batched +0.4%, pipelined +4.8%.
  - Pushed as 21afa4f9, CI green.
  - `tools/ab_ladder.py` added: the paired-ladder method as a tool.
- 2026-10-16: **A Metal host-time saving that lost throughput.** Memoising Metal's coarse
  geometry cut host time 14% but cost pipelined throughput 1.3% (six rounds, repeated).
  Reverted.
  - cProfile had made the M2 look host-bound: 3.5e7 templates in real time under the
    profiler against 4.08e7 without it.
  - On the M2, less host work does not mean more throughput.
- 2026-10-16: **Step 2: CUDA joins the shared grouped path; Metal stays per group**
  (6e041aaa).
  - CUDA and the tensor-core gate read per-row windows from a trailing table argument, under
    a window start of `ROWWIN_ON`. Vulkan's SPIR-V is byte-identical.
  - CUDA's own grouped implementation (147 lines) is gone. On the L40S the fine stage's device
    time fell 12% (0.072-0.078 -> 0.063-0.068 s).
  - Metal's grouped call was faster in isolation (device 99 against 145, wall 3x) but 6-10%
    slower in the ladder. The work counts were identical, and Metal's command-buffer times
    overlap, so its device timer cannot say why. Metal keeps a call per group, and its
    kernels keep their signature.
  - The per-group loop is not deletable after all. It is also the path for one window group
    and for shapes past the grouped limits.
- 2026-10-16: **Step 4: one band-forward rule for Vulkan and Metal** (fa74eff2).
  `_gpuhost.band_forward_wanted` with the measured refine-block fraction, one switch
  (`MF_BAND_FORWARD`), and Metal priced as it runs.
  - M2: 1.000 / 1.004 for the rule; 0.998 / 0.999 for the pricing (a seed per tree).
  - CUDA's band forward needs new kernels. It is left for when the forward's share of a CUDA
    segment justifies them.
- 2026-10-16: **Step 6: one tier conformance suite** (d29d0a30): CPU FP32, Q15 and FP16
  (ARM), and the GPU, at exact gate decisions.
  - It found a Metal bug on main: in a cascade, a tier-1 threshold of 0 passed the pairs tier 0
    had dismissed. Fixed on Metal and CUDA.
  - `docs/reduced-precision-gates.md` documents the three bounds.
- 2026-10-16: **Step 5: `_run_series_gpu` split into its stages** (31310ebf): `_series_call`
  (everything decided before dispatch), `_series_grouped` and `_series_by_group` (the two
  dispatch shapes), `_series_submit`, `_series_deferred`, and `_SeriesOutput` (where batches
  land). The 381-line function is now 22 lines.
  - Found on the M2: deferred results kept the call's state, and with it a host array's
    view owner, until collected. A later call then found its series unregistered. The owner
    now lives for the call, as it did before the split.
  - Paired: M2 1.000 / 1.024, L40S 1.052 / 1.010. Two 8060S pairings gave 1.001 / 0.989.
    Their seeds settled at about 1.0e8 against 1.43e8 for another seed on the same tree.
    On one settled 1.43e8 seed, host time per series call was the same in both trees
    (1978-2050 us against 2006-2035 us, 162 calls). Throughput medians were 1.44e8 against
    1.43e8. The split costs nothing measurable.
- 2026-10-16: **Step 3: one device follow-up design; CUDA executor** (41ef1d9f).
  - Step 0 had removed CUDA's follow-ups along with `SegmentPlan`. That left Vulkan's as
    the only design, so step 3 shared it rather than merging two designs.
  - `_gpuhost.followup_layout` lays a batch out as `refineItems` entries.
    `assemble_followups` orders the results as `_items_batch` does. Each backend offers
    `Context.followup_executor()`.
  - Vulkan keeps its recording and submission (`_vkfollowup`: 392 -> 241 lines).
    `_cudafollowup` (138 lines) does one table upload, then per group a forward and one
    `refineItems` launch, then one readback.
  - Measured share first, as planned. Host follow-ups were about 6% of an M2 segment and
    16-20% of a pipelined L40S segment. Vulkan's device follow-ups gain 7% over its host
    path on the 8060S.
  - L40S, paired on settled seeds: pipelined 1.249, batched 1.029. The follow-up stage fell
    from 0.05-0.06 s to 0.03 s per segment.
  - 8060S: 0.990 / 1.015. Follow-up batches cost the same host time in both trees
    (median 2.43 ms against 2.37 ms per 40-job batch).
  - Metal keeps the host path.
  - Removed with it, all unreachable since step 0: `followup.cu` and its PTX,
    `read_followup_items`, the item-record constants, `FollowupSpec`'s capacities and
    `supports_device_followups`. `MF_VK_DEVICE_FOLLOWUPS` became `MF_DEVICE_FOLLOWUPS`.
  - The call-plan follow-up tests now also run on CUDA.
- 2026-10-16: **Production coverage as a tool** (`tools/ladder_coverage.py`), run after
  steps 3 and 5 on the 8060S (batched and pipelined), M2, L40S and CPU.
  - 224 functions (2,331 statements) are reached by no backend's production ladder.
  - Most are expected:
    - public API the ladder does not call (`run`, `set_data`, `CorrelationFilter`, flat
      peaks);
    - calibration and trial code a settled seed skips;
    - tier-C block lengths;
    - error and teardown paths.
  - One group has no consumer at all: `FollowupSpec`, `filter_series_many(followups=)`,
    `_run_followups`, `run_followups`, and the `time_domain.FollowUp` alias. They were
    `SegmentPlan`'s interface. pycbc does not call them, and neither does the ladder (it
    passes single-template jobs to `filter_series_many`). Only `tests/test_followup_spec.py`
    reaches them.
  - That group is a deletion candidate. It is left in place because removing it changes a
    public keyword.
- 2026-10-16: **The follow-up rule removed** (at the user's decision): `FollowupSpec`,
  `filter_series_many(followups=)`, `_run_followups`, `run_followups` and `FollowUp`. The
  batched-calls test moved to `tests/test_followup_batch.py`.
- 2026-10-16: **CI red on 86ca1d35 (Metal, paravirtual GPU):**
  `test_fused_forward_matches_separate` asserted that the band forward and the separate
  forward give identical peak lists. One peak swapped between them (1036 peaks).
  - They are different float paths. On the M2 (three seeds) both match the CPU reference's
    peak set exactly, with SNRs within 1.4-1.9e-5. The closest reference peaks sit 5e-5 to
    1.6e-3 from the threshold.
  - Exact equality between the two paths is not a property of either. The test now checks
    each path against the CPU reference. A one-sided peak is allowed only within 1e-4 of
    the threshold, or as a lag tie inside a bin. A missed loud peak, a spurious peak, or an
    SNR off by 1e-3 fails (checked by mutation).
- **Measurement lessons.**
  - A shared seed hides a change to pricing or candidates; use `--seed-per-tree`.
  - Metal's device timer overstates time when command buffers overlap.
  - Never run tests on the machine under measurement.
  - Seeds settled the same way on the same tree reach different throughput: 1.0e8 to
    1.43e8 on the 8060S. One reached a 1.85 s fine stage. Compare host time per call when a
    pairing's sign depends on the seed.

## Assessment (2026-10-16)

- **Done:** every step (0-6) is merged.
- **Divergence removed:**
  - `SegmentPlan` and its backend machinery: 2,817 lines.
  - Padding and drafts.
  - CUDA's own grouped hierarchical path (CUDA now uses the shared one).
  - Two band-forward rules and switches, now one.
  - Two follow-up designs, now one shared layout with two thin executors.
  - The 381-line series function, now split into named stages.
  - One tier conformance suite now covers CPU f32/q15/f16 and every GPU. It found a Metal
    tier-1 bug that was on main.
- **Performance:**
  - Steps 0-1: up to +4.8% pipelined.
  - Step 2: L40S fine stage -12% device time.
  - Step 3: L40S pipelined +25%.
  - Nothing measured a loss that survived a direct host-time check.
- **Divergence that remains, by measurement:**
  - Metal runs a call per window group: the grouped call was 6-10% slower in its ladder.
  - Metal follow-ups run on the host: about 6% of its segment.
  - CUDA has no band-only forward (new kernels, unpriced).
- **The largest open issue is not divergence but seed variance.** Measured choices settle
  at throughputs 30% apart on the same tree and machine. Tightening how trials lock would be
  worth more than any remaining step here.
