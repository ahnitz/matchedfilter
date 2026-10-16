# Reduced-precision gates: one error model

Three first tiers run in reduced precision. Each gates on an estimate of a pair's coarse maximum
that never falls below the exact (FP32) maximum by more than its margin allows. Every survivor
is then refined exactly, in FP32, so a gate can only add work, never change a reported peak.
This page states the three bounds side by side; each kernel's own page has the derivation and
the measurements.

| Gate | Where | Estimate the gate compares | Margin | Page |
|---|---|---|---|---|
| Q15 screen | CPU, x86 (in front of the FP32 tier) | the int16 transform's maximum plus a margin | **absolute**: 5 sqrt(N) LSB of the int16 output | [cpu-q15-gate.md](cpu-q15-gate.md), `src/q15.h` |
| FP16 gate | CPU, ARM with FP16 vectors (replaces the FP32 tier) | B = \|y16(k')\| (1 + 3u) + κ u rms(y) | κ = 16 (`GATE16_KAPPA`) | [cpu-neon-fp16-gate.md](cpu-neon-fp16-gate.md), `src/gate16.cc` |
| fp16 coarse tier | GPU (Vulkan, CUDA, Metal; Slang) | B = \|c16\| (1 + 3u) + κ u rms(y) | κ per band, 12.7 / 15.5 at bands 256 / 512 (`C16_KAPPA`, `tools/coarse_layout.py`; Apple builds use their own σ table) | `src/gpu/tierb.slang` (c16Bound) |
| tensor-core gate | GPU, CUDA (sm_80+) | as the fp16 tier | κ 7.0 / 10.5 at bands 256 / 512 (`COARSE_TC_SIGMA`, `tools/build_ptx.py`) | `src/gpu/coarse_tc.cu` |

u = 2^-11 throughout; rms(y) is the pair's output rms over all lags (Parseval).

## The two forms

- **Relative (fp16).** fp16 rounding is relative to the values, so the bound has two parts:
  - (1 + 3u) is proven, not fitted. Choosing the lag on fp16 powers can pick a lag whose
    value is below the true maximum by at most that factor.
  - κ u rms(y) covers the transform's own rounding. It scales with the pair's energy, not
    with its peak.
- **Absolute (Q15).** int16 rounding is absolute. The screen's error is a sum of independent
  roundings with rms 0.44-0.47 sqrt(N) LSB, the same for noise and loud injections. So the
  margin is a fixed 5 sqrt(N), about 10.7 rms, with no peak-proportional term.

## How each constant was set

- **From measurement, never swept until tests pass.** Each κ (and the Q15 margin) is set so
  the margin is at least twice the worst error measured over the `tools/gate_margin.py`
  families: noise, profile, injection, loud transient, full scale. That is the merge gate's
  criterion: margin use < 0.5.
- **Measurement tools:**
  - `tools/gate16_error.py` for the CPU fp16 gate;
  - `tools/metal_c16_sigma.py` and `tools/coarse_layout.py` for the GPU fp16 tier;
  - `tools/cuda_tc_sigma.py` for the tensor-core gate;
  - `tools/gate_margin.py` for all of them (`--gate q15 gpu-c16 cpu-g16`).

## What checks it

- **`tools/gate_margin.py --loud`** (every merge, in `tools/gate.py`): margin use and the
  loud-injection fail-open, per gate.
- **`tests/test_tier_conformance.py`:** each CPU tier kind (FP32, Q15, FP16 on ARM) and the
  machine's GPU, at thresholds in wide gaps of the exact maxima, refines exactly the pairs
  above them and reports the same peaks.
- **`tests/test_coarse_conformance.py`:** the same exact-decision check for every GPU coarse
  layout a device can choose, single calls and grouped.
- **Fail-open on overflow:** an fp16 value that overflows to inf or NaN passes the gate
  (comparisons are written `!(x < thr)`). This is checked by the transient and overflow
  cases of both conformance suites and by `tests/test_gpu_loud_overflow.py`.
