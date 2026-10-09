# GPU parity plan: tested, correct, and at its hardware's performance

Written 2026-10-08 after an audit of the GPU code against the CPU code (two review agents plus
measurement on the Radeon 8060S, gfx1151, RADV). The CPU path has had months of work:
- cost models calibrated on the machine;
- autotuned chains;
- an execution policy per machine;
- a production replica (test27) as the consumer;
- every rule checked against its consumer.

The GPU has had serious work on individual kernels (docs/gpu-coarse-plan.md: coarse kernels at
11-24% of fp32 peak, with a falsified list). It has had almost none on the pipeline that feeds
those kernels, on tuning, or on the consumer. **Parity means the same method applied end to end:
account first, find the binding constraint, delete work, and verify every speedup on the real
consumer.**

## 1. Where it stands (measured today)

The library alone: a fine-stage bank of 200 templates (200-400 taps), n=2048, an analytic 2^20
series, threshold 5, FD 1e-3. Each column is one Zen 5 core or the whole GPU. Min of 3.

| call                                   | CPU 1 core | GPU      | GPU / core |
|----------------------------------------|-----------:|---------:|-----------:|
| hier, whole series (200 tmpl)          | 10.2 ms    | 1.3 ms   | 7.8x       |
| hier, whole series (1000 tmpl)         | 52.6 ms    | 4.3 ms   | 12x        |
| flat, whole series (1000 tmpl)         | 797 ms     | 22.9 ms  | 35x        |
| hier, 64 windows of 4096 (fine stage as pycbc calls it) | 3.8 ms | 5.3 ms | **0.7x** |
| hier, 1 window                         | 0.07 ms    | 0.24 ms  | **0.3x**   |
| single-template asym call (before fix) | 0.21 ms    | 13.9 ms  | **0.015x** |
| single-template asym call (after fix)  | 0.21 ms    | 1.06 ms  | 0.2x       |
| middle stage, 8 captured banks, 210 filters x 2^20 | 423 ms | 283 ms | 1.5x (kernels ~29 ms) |

The production replica: test27 short span, the CPU job against `PYCBC_RATIO_DEVICE=gpu:0`,
run as a concurrent pair on idle cores without a profiler.

| stage                        | CPU job | GPU job, before | GPU job, after 381a8e6 |
|------------------------------|--------:|----------------:|-----------------------:|
| Fine FIR (the middle is on the CPU in both, ~7 s; plus the fine stage) | 44.9-51.3 s | 58.2 s | 36.7 s |
| Asymmetric follow-up         | 1.26 s  | 25.0 s          | 11.6 s                 |
| Total                        | 83.5 s  | 121.5 s         | 86.9 s                 |

Triggers agree. SNR matches to 7e-6 relative on common triggers, and 1-5 borderline triggers
differ per detector (gate outcomes at the margin). The CPU job's triggers are identical before
and after the change.

**After this pass the GPU job is on par with one CPU core.** Its fine stage is faster
(~29 s against ~38 s once the middle is removed), but the follow-up is 9x slower. The GPU wins
whole-series kernels by 8-35x and still loses every small-call shape. The binding constraint is
per-call host work (copies, submissions and recordings), not the kernels.

Measurement trap: py-spy `--native` sampling inflates a GPU job 3x (253 s against 87 s; 20% of
samples in `ioctl`), against 7% on a CPU job. Profile GPU jobs with the library's own timers
(C1), not a sampler.

Rooflines for scale (gfx1151):
- ~14.8 TFLOPS fp32 (twice that for packed fp16);
- ~256 GB/s LPDDR5X, shared with the CPU.

Measured kernel rates:
- flat inverse FFTs: ~3.5 TFLOPS, ~23% of peak;
- hier coarse: ~0.4 TFLOPS effective, because the whole call includes compaction and refine;
- middle-stage kernels: ~29 ms for 210 x 2^20 outputs (1.76 GB written), about 60 GB/s
  effective.

## 2. Done in this pass

| item | change | effect |
|------|--------|--------|
| "GPU readback cliff" | Not the GPU. A NumPy boolean-mask copy over rows 8 MiB apart thrashed one cache set. Fixed with `np.copyto(where=)` (5ffed3e). | 16->24 templates 2.1 s -> 70 ms; GPU banks price their own layout again |
| GPU correlation layout | Device-aware cost calibration (`corr,n,device` in the cost file) | 350 -> 270 ms on the captured banks |
| Packed (Hermitian) templates on GPU | Were zero-padded, losing the Nyquist bin: 3e-3 SNR error. Now unpacked to the full spectrum, and re-unpacked if `set_hermitian` changes after setting. | 1.3e-6, same as unpacked; new test |
| Single-template GPU plans | One reused plan per group instead of one Vulkan context (~9 ms) per template | 13.9 -> 10.2 ms |
| Windowed GPU series calls (381a8e6) | Upload only the span the blocks read, not the whole 8 MB series per call; pools sized by capacity, so a different block count no longer reallocates every buffer and discards every recording | asym 10.2 -> 1.06 ms; 1 window 410 -> 242 us |
| test hygiene | `test_gate_model._gpu` checked a nonexistent `software` attribute (llvmpipe counted as a GPU) | now `is_software` |

## 3. Workstreams

Ordered by what binds on the consumer. Each step has an acceptance check, and each performance
step is verified on the test27 replica (GPU job vs CPU job, concurrent pair), not on a synthetic
call.

### A. Correctness first (P0). Nothing below is worth timing on a path that can be wrong

- A1. **Intermittent wrong coarse value.** One full-suite run on 2026-10-08 produced one wrong
  value in 17524 on `tierb_1024_c16p2t2.spv`: 3.92 where the CPU gives 5.34. It never reproduced:
  - 40 isolated runs;
  - 4 GPU-heavy sessions;
  - 3360 reruns of every band-1024 variant;
  - 3600 under concurrent load.

  Next steps:
  - run the suite under the Khronos validation layer with synchronization validation;
  - review that kernel's barriers (LDS reuse across the tile loop, the PPG packing);
  - check host-write -> device-read visibility for inputs written to write-combined memory
    without a flush or barrier;
  - run a soak test of 10^5 dispatches that compares every output against the CPU.

  Accept: a found cause plus a regression test, or a 10^6-dispatch soak with zero mismatches and
  validation-clean runs.
- A2. **Vulkan multi-queue safety.** Eviction waits only on queue 0 (`_vkcompute.py` ~2006,
  ~2030) while pipelined slots submit to queues 1-3, so a recording can be freed while in flight.
  Wait on every slot's fence, or `vkDeviceWaitIdle` on eviction. Accept: a test that forces
  eviction under K=8 pipelining, clean under synchronization validation.
- A3. **`except TypeError` retries can double-dispatch.** If a backend raises TypeError after
  submitting, the retry submits again. Replace the signature probing with a capability attribute
  per backend.
- A4. **CUDA k=2 chains silently wrong** (`_cudacompute.py` ~589-593), **CUDA grouped
  `run_series` broken** (~476-506), **Metal k=2 collapsed to k=1** (`_mtlcompute.py` ~965-970).
  There is no hardware here. Until they are fixed and tested on hardware, those paths must raise
  `UnsupportedSize` (or the backend's `_MAX_TIERS` must say 1), not run a different computation.
  Accept: a mocked-backend unit test that a 2-tier chain is either executed or refused on each
  backend.
- A5. **Device ordinal mapping** on mixed backends (`device.py` 143-162): a `gpu:N` index must
  name the same device in `devices()` and in the backend Context. Add a test with a fake
  enumeration.
- A6. **Gate-margin differences between CPU and GPU.** 2-4 peaks of ~1400 differ on whole-series
  runs, and 1-5 triggers on the replica. Expected from rounding at the coarse gate, but it must
  be bounded. Measure the GPU's signal dismissal with the same audit as the CPU's
  (0.087-0.091% against a 0.1% budget). Accept: the GPU's dismissal is within budget.

### B. Test parity: every CPU guarantee has a GPU twin

Today several GPU tests compare the GPU only with itself, tolerances are looser (2e-4 to 3e-4
against ~1e-6 achieved), and skips hide regressions.

- B1. A device-parametrized `TimeDomainFilterBank.filter_series` suite (cpu, gpu:0) comparing
  against the CPU:
  - flat, hier and hetero banks;
  - `template_index`;
  - the threshold fallback;
  - windows (1, many, touching, at the edges);
  - cost-chosen block size;
  - packed templates (done).
- B2. Public `run()` at n=64..512 and 32768/65536 against a float64 reference on GPU.
- B3. Two-tier GPU chains: the public API end to end, and a pinned 3-tier chain on GPU must
  raise.
- B4. Pipelining with more than K=8 batches in flight. Eviction mid-series: tierc, full and
  forward recordings.
- B5. Two-stage correlation: multi-pair and the tiled split.
- B6. GPU `run_series` automatic layout, `run_blocks(out=)` and `scales=`.
- B7. Hygiene:
  - turn `UnsupportedSize -> skip` and `ValueError -> skip` into explicit expected-unsupported
    lists, so a newly broken size fails;
  - make `test_vk_cascade::test_gpu_series_pipelined` check values, not shapes;
  - tighten tolerances to what is achieved, with a stated margin.
- B8. A GPU leg of the standard ladder (notes/std_ladder.py) and an opt-in replica job, run
  periodically like the CPU ladder.

### C. Measurement: the GPU's equivalent of the tick counters

The CPU work rests on cycle accounting per stage. The GPU has none, so every GPU decision so far
was made from wall time.

- C1. Timestamp queries (`vkCmdWriteTimestamp`) around each dispatch in a recording, exposed like
  `tier_stats`: per-kernel device time, plus host time per call split into upload, record, submit,
  wait and readback. Accept: per call, the parts sum to within 5% of the call's wall time.
- C2. A per-kernel roofline table at production shapes (bytes and flops per kernel against
  14.8 TFLOPS / 256 GB/s), regenerated by a script, like `docs/local-device-timings.md`.
- C3. GPU `tier_stats` (survivors per tier). The gate model's chain choice needs it, and on the
  GPU it is None today.

### D. Performance, ranked by measured consumer share

- D1. **Asymmetric follow-up.** It was 25 s of a 121 s job; it is now 11.6 s, against the CPU's
  1.26 s, and is the largest remaining GPU loss. Production makes thousands of calls, each with one template and one ~61k-sample
  window, threshold 0, and 1000 bins of 61 samples. Each call is still about 3 host round trips:
  bins are split by count into separate `run_series` calls, each a submit plus a wait.
  - Library: one submission per call. Pass per-block bin bounds in a buffer instead of push
    constants, so one recording serves every window.
  - Then a batched entry that takes a list of (template, window) pairs and returns all their
    bins in one submission. That is the widest description of the work, so the library can
    choose execution ([[pycbc-library-boundary]]). pycbc would hand over a group's candidates
    at once instead of looping.

  Target: GPU follow-up at or below the CPU's 1.25 s.
- D2. **Fine stage on windows.** At 0.7x one core, the GPU loses because each window is its own
  dispatch and submission (2 submits per window). Fix:
  - a grouped hierarchical path, which the flat filter already has (`peaks_grouped`), taking
    per-block window bounds from a buffer;
  - one submission per batch of windows;
  - recordings keyed on shape, not on window positions or thresholds (thresholds become
    push-constant or buffer data).

  Target: per-window cost at the kernel's per-block cost. At 64 windows that is <1 ms against
  5.3 ms now.
- D3. **Device-resident middle -> fine pipeline.** The middle stage writes 210 x 2^20 complex
  outputs (1.76 GB) to host memory: ~250 ms of host copies against ~29 ms of kernels, and the fine
  stage then copies spans back. pycbc's middle bank takes no device (`pycbc_inspiral_fir`
  `UpperReferenceBatch` builds `engine='corr'` without `device=`), so today the middle never runs
  on the GPU in production.
  - Library: `correlate_series(out=)` into a GPU-shared allocation (`empty_shared`, the existing
    DLPack and shared-buffer path). `filter_series` already skips the upload when the series is
    a shared buffer (`source_shared`).
  - pycbc is not changed now (user direction 2026-10-08). The library provides the
    device-resident API, and the standalone bench (G) exercises it the way pycbc will.
  - Also: `CorrelationFilter._full_output` uses write-combined memory without `readback=True`.
    Kernel 2.2 ms against copy 64 ms.

  Target: middle stage on GPU at kernel time plus the consumer's reads.
- D4. **Kernel efficiency at production shapes.** After D1-D3 the kernels become the binding
  constraint. Measure them with C1 and C2 and take the next round of docs/gpu-coarse-plan.md
  (register pressure at 216 VGPR, scalar fp16 from `cmul`), now ranked by consumer share. Also
  check the wave32 assumptions in kernels that run on a wave64 device.
- D5. **Host overheads.**
  - One Vulkan context per plan: a bank has dozens of plans, each with its own instance, device
    and queues. Share one context per physical device, which needs A2 first.
  - One descriptor pool per set.
  - K x 64 MiB spectra pools per plan.
  - Per-call template copies.
  - `_cache_bytes` misses outputs and scratch, so the cache budget is wrong.

### E. Tuning to the hardware: the GPU's version of the autotuner

- E1. GPU chain choice. Today `_MAX_TIERS['gpu']=2` is hard-coded, autotune trials are off on GPU
  (`__init__.py` ~1783), and the GPU's chain comes from the CPU cost model. Calibrate a GPU
  `CostModel` from C1's per-kernel timings (the same `calibrate_costs` interface, keyed by device
  in `MF_COST_FILE`) and enable trials. Fix the policy band mismatch (band 0 against chain[-1]).
- E2. GPU rows in `execution-policy.json`: `series_group`, queue depth K (`MF_GPU_QUEUE_AHEAD`),
  batch bytes and PPG/tile choices, each with evidence, like the Haswell row. No hard-coded
  exclusions ([[no-disabled-paths-fix-the-autotuner]]).
- E3. Block sizes for the fine stage priced on the device (done for the middle stage in
  5ffed3e), and the coarse band and cascade choice through the gate model with GPU costs.
- E4. Don't overtune to one GPU. Validate every rule on llvmpipe (correctness) and, when
  available, on one NVIDIA (CUDA) and one Apple (Metal) machine.

### F. Cleanup

- Dead coarse-tile path, non-c16 branches, `fused=`.
- Stale comments, and `docs/cpu-gpu-parity.md` (2026-09-26), which predates this audit.
- Metal "async", which is synchronous.
- The CUDA refine reads the survivor count back to the host between dispatches.

## 4. Scope set by the user (2026-10-08)

- **Library only.** A GPU job is an eventual target, but pycbc is not changed now. Everything
  pycbc would need goes into the library and is exercised by the standalone bench (G):
  - device-resident series between stages;
  - one batched call for (template, window) pairs;
  - batched windows for the fine stage.

  Integrating later should then be a thin change on the pycbc side.
- **Every backend to the same level.** Vulkan (Radeon 8060S, here), CUDA and Metal each get the
  same correctness, tests, timers, device-calibrated costs, autotuning and policy rows as the
  CPU. CUDA and Metal are not refused; they are brought up to the same level.
- **The individual kernels are well below optimal too.** Kernel work is not deferred until the
  host side is done; it runs in parallel (section 6).

## 5. Machines

| backend | machine | device | access |
|---------|---------|--------|--------|
| Vulkan  | this host | Radeon 8060S (gfx1151, RDNA 3.5, 40 CU, ~14.8 TF fp32, ~256 GB/s shared) | local |
| Metal   | `empire` | Apple M2, 10 GPU cores (~3.6 TF fp32, ~100 GB/s unified), 24 GB, macOS 26, Metal 4 | ssh |
| CUDA    | sugwg cluster | one GPU held for days through a condor job from `sugwg-login2`, used with `condor_ssh_to_job` | condor |

The cluster has, by count: Quadro RTX 6000 (71), L40S (34), A100 80GB PCIe (27), A40 (26),
H100 (10) and RTX 5000 (6).
- **Primary CUDA device:** an L40S, Ada sm_89, the most numerous modern part and fp32 heavy.
- **Second architecture:** an A100, Ampere sm_80 with HBM. Rules are checked on it before they
  ship, so nothing is tuned to one GPU.
- **Holding the node:** a long-lived job requesting 1 GPU and a few cores, which sleeps and
  keeps a working tree on node-local scratch. Release it when the work pauses. If the job is
  preempted, the work resumes from git; nothing lives only on the node.

## 6. Two tracks, run in concert

The host pipeline and the kernels are developed in parallel, not in sequence. The bench (G) and
the timers (C1) are their shared contract. After each change the bench reports two things:
- device time per kernel;
- host time per call, split into upload, record, submit, wait and readback.

So each track sees when it has become the other's bottleneck.

**Track H, the host pipeline. One implementation shared by the backends where possible.**
- H1. Timers (C1) on every backend: Vulkan timestamp queries, CUDA events, Metal
  `GPUStartTime`/`GPUEndTime` and counter sample buffers.
- H2. One submission per batch of windows (D2), and the batched (template, window) call (D1).
  Recordings keyed on shape; window bounds and thresholds in buffers or push constants.
- H3. A device-resident series path between stages (D3). On Metal and on the shared-memory
  Radeon the host and device share memory, so zero copy is possible; on CUDA, device buffers
  plus pinned staging.
- H4. Overheads (D5): one context per physical device, pooled descriptors and buffers, correct
  `_cache_bytes`.
- H5. Tuning (E): a cost model per device calibrated from H1's timings, autotune trials on the
  GPU, policy rows with evidence, and no hard-coded tier limits.

**Track K, the kernels. Per backend, against a per-kernel roofline (C2).** Kernels in order of
their share of the bench's time:
1. hierarchical coarse;
2. survivor compaction and refine;
3. flat inverse FFT and peak;
4. forward FFT;
5. continuous correlation.

For each kernel on each device:
- record achieved against attainable throughput (flops or bytes);
- record occupancy, register and LDS use, and the instruction mix: RADV shaderstats, Nsight
  Compute, Xcode GPU counters;
- apply the delete-work method of docs/gpu-coarse-plan.md, and keep a falsified list per
  device.

Targets until measured otherwise: compute-bound kernels at >=50% of fp32/fp16 peak, and
memory-bound kernels at >=70% of bandwidth.

Backend-specific work:
- **CUDA:** native kernels, using cuFFT where it wins (measured, not assumed). Fix k=2 chains,
  grouped `run_series`, eviction, and the tiled two-stage correlation. Remove the host readback
  of the survivor count between dispatches (use indirect or device-side launch).
- **Metal:** make k=2 chains real, real async submission, and threadgroup-memory limits (32 KB)
  in the kernel variants. The M2 is SIMD-32, so check the wave assumptions.
- **Vulkan:** register pressure in the coarse kernel (216 VGPR), scalar fp16 from `cmul`, and
  the wave32 assumptions on a wave64 device.

**Loop.** Each iteration:
1. bench on every device;
2. the H1 split says which track binds;
3. that track takes the next item, while the other continues on its own list;
4. a speedup counts only when it is verified on the bench and checked bitwise or to tolerance
   against the CPU.

Both tracks share the correctness gate: A1-A3, plus the parity suite on every backend.

### G. The standalone ladder: the bench both tracks work from

`bench/ladder` in mf, independent of pycbc and an analogue of the pycbc three-level pipeline:
1. **Inputs:** Gaussian noise (white analytic, and coloured by the reference profile
   `_whitened_inspiral_bank` uses), with optional injections.
2. **Templates:** read directly from the bank files we use (`fir_three_level_modern_v1_*.hdf`:
   top, middle and fine taps and their hierarchy), plus synthetic banks at production sizes.
3. **Stages:**
   - the top reference series;
   - the middle correlation bank;
   - candidate windows from middle peaks above threshold;
   - the fine hierarchical bank on those windows;
   - single-template follow-ups (1000 bins, ~61k-sample windows, threshold 0), in the call
     pattern the replica makes;
   - the chisq-block spectra.
4. **Reports:**
   - templates-in-real-time per stage and per device;
   - the H1 time split;
   - per-kernel roofline fractions;
   - outputs against the CPU (identical peak sets at the gate margin within the dismissal
     audit, SNR to 1e-5).
5. **Scales:**
   - a seconds-long quick mode, for every iteration;
   - a full mode, matching a test27 short span in work.
6. Runs on every backend from one command, and writes JSON that tracks results over time, as
   the CPU ladder does.

The bench's call counts and shapes are checked once against the test27 replica's logs, so it
stays a faithful analogue.

## 7. Order

Track H and Track K run concurrently from step 2.

1. G quick mode plus H1 timers on Vulkan. Get the cluster GPU job and the empire environment
   building mf (CUDA toolkit, Metal toolchain); baseline every backend on the bench.
2. Correctness on all three backends: A1-A5 and B (the parity suite on CUDA and Metal hardware).
3. Track H: H2, then H3, then H4, with H5 once H1 timings exist per device. Track K: kernel 1,
   then kernel 2, on Vulkan and CUDA first, then Metal, each against its roofline.
4. Full-mode bench per device; then GPU rows in the execution policy; then the A100 check.
5. F (cleanup) as fill; refresh docs/cpu-gpu-parity.md and docs/local-device-timings.md to the
   new state.

**Done means:** on every backend, the bench's stages run at their kernel roofline fractions
(targets above) with host overhead under 10% of device time. Outputs match the CPU within the
audited budget. Tuning comes from the device's own calibration.

## 8. Open decisions

- Accept the targets in section 6, or set others?
- Which GPU is the eventual production GPU? The plan tunes on the L40S and checks on the A100.

## 9. The high-level gap: what stands between the GPU and 10-100x (2026-10-08, measured)

For one top template and one segment, the fine stage is ~4.4M (template, block) pairs across
27 banks and two detectors. Today that is 54 calls of ~100k pairs each.

**Device time per pair** (MF_GPU_TIMING, n=2048, threshold 6):
- 44 ns at 10k pairs per call;
- 25 ns at ~137k pairs, the production call size;
- levelling off at ~9 ns only past 0.6M pairs.

Wall time adds 2-3x on top. One Zen 5 core is 55-120 ns/pair, so even saturated the GPU's
device time is only ~6x one core.

**Where the device time goes** (MF_GPU_PROFILE, which timestamps the phases inside a recording):
- the band-128 coarse kernel is ~80% of it: 5 ns/pair saturated, 18 ns at production size;
- the forward FFT costs 1-2.7 us per 2048-point block and gets slower as the series grows,
  which suggests source memory placement;
- compaction, refinement and fills are small.

**Clock.** On the dev host the Radeon is an APU sharing package power with a loaded CPU, and it
held 600 MHz of 2900 (busy 7-27% on production calls, 62-73% on large flat calls). All numbers
above are at roughly 1/4-1/5 clock. They have to be judged in cycles, with sclk and power logged,
or measured on the discrete L40S.

**Three levers, in order:**
1. **Granularity (structural).** Hand the library a whole segment: all of a top template's fine
   banks, each reading its own middle series, both detectors, in one submission.
   - The GPU forward-transforms every block of every middle series in one dispatch.
   - It runs the coarse tiers over a grouped pair space: each bank's templates against its own
     series' blocks, selected by descriptor offsets as `peaks_grouped` already does for flat
     windows.
   - It compacts and refines once.

   Together with a device-resident middle output (the series never leaves the GPU), that is
   ~4.4M pairs per submission instead of 54 submissions of ~100k. It is a library API (a bank
   set) that pycbc can adopt later. The same structure batches the follow-ups: (template,
   window) items as groups of one template each.
2. **Kernel efficiency.** The coarse kernel is ~1.2k cycles/pair at 600 MHz for ~5k flops. Its
   targets are in section 6. The forward FFT needs its source in device-local memory and a
   multi-block-per-workgroup layout.
3. **Host overhead and round trips.** Per-call recording churn (the cache entry limit against
   chain trials x pipelining slots), per-call uploads, and the idle-latency trap. Batching
   (lever 1) removes most of it.

### Falsified on Vulkan (2026-10-08)

- **Per-call import of caller memory** (`VK_EXT_external_memory_host`, the Vulkan counterpart
  of Metal's `host_view`). The fine stage got 7x slower on the bench: 0.31 -> 2.2 s per
  4 segments.
  - Importing pins an 8 MB series' pages (get_user_pages) and forces a new forward recording
    each call, ~40 ms per call against a ~1-2 ms copy.
  - The middle output import gained nothing either.
  - Zero copy on Vulkan has to come from library-owned device allocations with stable
    addresses: the middle stage writes rows that the fine banks read by offset.
- **Device-owned middle output read in place by the fine banks.**
  - The middle stage allocated 216 MB of device memory per call: middle 0.18 -> 0.74 s.
  - Every new row address keyed a new forward recording, so the fine stage got slower too.
  - Zero copy needs stable addresses and descriptor rebinding instead of new recordings: part
    of the fused segment executor, not a patch to the per-call path.

## 10. State on 2026-10-09 (main da0dc72): measured, fixed, falsified, next

### Measured
The setup:
- realistic ladder (`--profiles ladder_profiles_H1.npz --pure`, 1 top, 10 segments);
- steady = segments 3-10 (`--warmup 2`: plan builds, then chain trials lock);
- `--check cpu` exact (0 one-sided peaks) on every row below;
- host load ~5.

| Stage, s per 8 segments | Radeon 8060S (Vulkan) | 1 Zen 5 core | GPU / core |
|---|---:|---:|---:|
| Middle | 0.13-0.14 | 0.48 | 3.5x |
| Fine | 0.22-0.27 | 3.0 | 11-13x |
| Follow-ups | 0.06 | 0.07 | 1.1x |
| Total | ~0.45 | ~3.5 | ~8x |

Against the whole 16-core CPU (~0.22 s) the GPU is still ~0.5x. By peak arithmetic it should be
~6x (fp32) to ~12x (fp16). The fine stage alone, looped back to back so the clock rises
(~2.6 GHz), is **device-bound**: wall 22-24 ms per segment, device 20-25 ms. So the kernels are now
the limit, not the host. Per-phase device ms per segment at ~2.6 GHz:

| Phase | ms |
|---|---|
| coarse0 | 9.6-10 |
| refine | 1-5.7 (depends on the chain) |
| coarse1 | 0-3.7 |
| forward | 3.4-3.9 |
| pack | 0.7-1.7 |
| fill | 0.1 (was 1.5) |

At ~4.6M pairs per segment in 162 dispatches, coarse0 is ~2.2 ns/pair, ~10% of the fp16 peak by a
flop count. In the ladder (not looped) the GPU sits at 600-1000 MHz and ~11% busy: the governor
does not ramp when the GPU idles between the host's calls.

CUDA (L40S, phase 2, `MF_AUTOTUNE=0`): 12x one core end to end; fine 18x, middle 13x. Host Python is
~60% of the fine stage's wall time.

Metal (M2): the fine stage is device-bound (94% busy), ~85-100 ms per segment, ~16x one core.

### Fixed tonight (each with a test that fails without the fix)
- **Two use-after-free bugs:** GPU page faults and VK_ERROR_DEVICE_LOST in ~1/3 of runs, main
  included.
  - The fused-recording cache was keyed on command-buffer handles, which the driver reuses after
    eviction. It is now keyed on unique recording serials.
  - A plan's pools were replaced under its in-flight deferred calls.
- **Cache budget:** caller-held shared allocations (the ~480 MB middle output) were counted
  against the 512 MB budget, so every fine call evicted and re-recorded. Profiled host time
  went 1.58 -> 0.98 s per 8 segments.
- **Sparse readback** (`_SparsePeaks`) works on every backend, including padded dispatches
  (before, only 112 of 1296 readbacks were sparse). Sparse callers skip the dense clear.
- **Middle stage:** template-group row views of a shared output are written in place
  (descriptor offset), instead of through a workspace and a host copy: 0.23 -> 0.14 s.
  - Two bugs were found on the way: a doubly shrunk descriptor range, and a recording key that
    was None for every view (95/76 one-sided peaks until fixed).
- **Follow-ups:** both detectors' series go in one item submission, and every group is in flight
  before one wait. The old asym time of 1.5-3 s came from the per-call fallback.
- **Vulkan argtypes:** they were set on a function table that gets replaced, so 64-bit sizes were
  passed as masked C ints.
- **Ladder `--warmup`:** chain-trial segments no longer count as steady (they were inflating the
  fine stage ~25%).

### Falsified or parked
- **SegmentPlan replay** (`MF_SEGMENT_REPLAY=1`, off by default) is still not usable on realistic
  data. Most segments are not replayable (synchronous jobs), and with `LADDER_REPLAY` the check
  lost 32 peaks. The fix for host cost is not replay. It is less host work per call, plus kernels
  fast enough that the device bounds the stage.
- **Metal:**
  - SIMD-group barriers in the middle kernel: rare garbage values on the M2, reverted.
  - Coalesced output writes: slower.
  - Smaller staging: ~2x slower.
- **Packing 2-8 listed pairs per threadgroup in the Metal refine:** slower at every packing.

### Next, by track
- **Vulkan kernels** (agent, `kernels/vulkan`):
  - roofline accounting in `docs/vulkan-8060s-roofline.md`;
  - coarse0 toward ≥50% of the fp16 rate;
  - refine, coarse1, and forward toward ≥70% of bandwidth;
  - a listed compact1 (removes the cval1 fill);
  - the tiny edge dispatches (nd 1-16).
- **Host and high level** (coordinator):
  - per-call Python in `filter_series` -> `run_series` -> `_run_series_gpu` (~0.7 ms a call,
    54 calls a segment);
  - fewer dispatches per call (3 window groups -> 1, as `hier_peaks_grouped` does on CUDA);
  - keeping the GPU busy so its clock ramps.
- **CUDA** (agent, phase 3):
  - re-verify calibration;
  - `peaks_items`;
  - the refine spill;
  - the fp16 coarse gate at 15-30% of its rate;
  - host path.
- **Metal and the ARM CPU** (agent, phase 5): the NEON fp16 coarse gate for the CPU path (~1.2x on
  the CPU fine stage), validated against the false-dismissal budget.
- **Calibration:** the clock-reference ranking (`_ClockRef`) needs verifying under CPU load on the
  APU. Chain choice still differs between processes: (256,) vs (256, 512) here, 88 vs 137 ms on
  the M2.
