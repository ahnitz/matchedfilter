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
  - pycbc: pass the device to the middle bank and request device-resident outputs. That is a
    pycbc-side opt-in, not a library hack.
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

## 4. Order

1. A1-A3 (correctness, Vulkan), with B7 hygiene so the suite can see regressions.
2. C1 (instrumentation), because every later decision depends on it.
3. D1 + D2 (one submission per batch of windows), verified on the replica. That turns the GPU job
   from slower than one core into a win.
4. D3 (device-resident middle), which needs a pycbc opt-in.
5. E1-E3 (tuning on the device), then D4 (kernels, by consumer share).
6. B1-B6, B8 alongside; A4-A5 and F as fill.

## 5. Decisions for the user

- Is a GPU job (one GPU per job, or a GPU shared by N jobs) a production target? That decides
  whether D3's pycbc opt-in and the GPU ladder leg are worth maintaining. Throughput should be
  compared as templates-in-real-time per device and per dollar, not as speedup ratios.
- CUDA and Metal: refuse the broken paths now (A4), or keep them until hardware is available?
  This plan defaults to refusing.
