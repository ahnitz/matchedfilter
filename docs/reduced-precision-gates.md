# Reduced-precision gates: one error model

Every tier of a chain is a screener, and what it answers to is the chain's false-dismissal
budget against the flat filter, not the decisions of an FP32 tier at the same band: any
screener that keeps the chain within that budget is acceptable. Every survivor is refined
exactly, in FP32, so each reported peak is the flat filter's; which pairs reach the refine is
what the budget governs.

**The Q15 screen is the first tier itself** (since 2026-10-22). It gates on its own int16
maximum, with no margin and no FP32 run of the tier behind it, at the threshold the gate model
sets for the tier. Its rounding (rms 0.46 sqrt(N) LSB, about 0.2% of the threshold at the
production bands) is small beside the band's own loss. Measured against the flat filter by
injection (`tools/chain_fdr_vs_flat.py`, since folded into `tools/fdr_audit.py`: n = 2048, chain 256/512/1024, SNR 6, fd 1e-3, 400k
injections per profile), the
chain dismisses 168 and 184 of ~228,600 flat detections with the gate, against 171 and 185
with the FP32 first tier. On 221,607 captured production pairs the gate passes 1.00x as many
pairs as the FP32 tier would, where the screen with its 5 sqrt(N) margin passed 1.37x at band
256 (1.62x and 2.35x had it run at 512 and 1024).

The tiers between the first and the last gate the same way, on their survivor lists
(`ap_mf_q15_pairs`; [cpu-q15-gate.md](cpu-q15-gate.md)).

The FP16 gates below still report an upper bound of the FP32 maximum and so pass a superset of
its pairs; they could be calibrated the same way. This page states their bounds and the Q15
screen's error side by side; each kernel's own page has the derivation and the measurements.

| Gate | Where | Estimate the gate compares | Margin | Page |
|---|---|---|---|---|
| Q15 screen | CPU, x86 (the first tier) | the int16 transform's maximum | none in the chain; `ap_mf_q15_screen` alone keeps a 5 sqrt(N) LSB margin by default (`ap_mf_set_q15_margin`) | [cpu-q15-gate.md](cpu-q15-gate.md), `src/q15.h` |
| FP16 gate | CPU, ARM with FP16 vectors (replaces the FP32 tier) | B = \|y16(k')\| (1 + 3u) + κ u rms(y) | κ = 16 (`GATE16_KAPPA`) | [cpu-neon-fp16-gate.md](cpu-neon-fp16-gate.md), `src/gate16.cc` |
| fp16 coarse tier | GPU (Vulkan, CUDA, Metal; Slang) | B = \|c16\| (1 + 3u) + κ u rms(y) | κ per band, 12.7 / 15.5 at bands 256 / 512 (`C16_KAPPA`, `tools/coarse_layout.py`; Apple builds use their own σ table) | `src/gpu/tierb.slang` (c16Bound) |

u = 2^-11 throughout; rms(y) is the pair's output rms over all lags (Parseval). CUDA's
tensor-core gate, a fifth row until 2026-10-29, was never chosen and is deleted
([cuda-l40s-roofline.md](cuda-l40s-roofline.md), Phase 7).

## The two forms

- **Relative (fp16).** fp16 rounding is relative to the values, so the bound has two parts:
  - (1 + 3u) is proven, not fitted. Choosing the lag on fp16 powers can pick a lag whose
    value is below the true maximum by at most that factor.
  - κ u rms(y) covers the transform's own rounding. It scales with the pair's energy, not
    with its peak.
- **Absolute (Q15).** int16 rounding is absolute. The screen's error is a sum of independent
  roundings with rms 0.44-0.47 sqrt(N) LSB, the same for noise and loud injections. Where the
  screen must pass every pair the FP32 maximum could pass (`ap_mf_q15_screen` with its margin
  on), the margin is a fixed 5 sqrt(N), about 10.7 rms, with no peak-proportional term. As the
  chain's first tier it uses no margin; the error is part of its statistic.
- **Range.** Inputs are quantised so that no intermediate of the int16 transform can overflow
  (`docs/cpu-q15-gate.md`), and the final |z|^2 saturates upward, so a loud pair always passes.

## How each constant was set

- **From measurement, never swept until tests pass.** Each κ (and the Q15 margin) is set so
  the margin is at least twice the worst error measured over the `tools/gate_margin.py`
  families: noise, profile, injection, loud transient, full scale. That is the merge gate's
  criterion: margin use < 0.5.
- **Measurement tools:**
  - `tools/gate16_error.py` for the CPU fp16 gate;
  - `tools/c16_sigma.py` and `tools/coarse_layout.py` for the GPU fp16 tier;
  - `tools/gate_margin.py` for all of them (`--gate q15 gpu-c16 cpu-g16`).

## What checks it

- **`tools/gate_margin.py --loud`** (every merge, in `tools/gate.py`): margin use and the
  loud-injection fail-open, per gate.
- **The chain against the flat filter, by injection** (`tools/fdr_audit.py --q15`, every
  merge in `tools/gate.py`): every profile and chain, FP32 and Q15 tiers, two-sided against
  the budget. This is the acceptance test for any first tier, Q15 included.
- **`tests/test_tier_conformance.py`:** each CPU tier kind (FP32, Q15, FP16 on ARM) and the
  machine's GPU, at thresholds in wide gaps of the exact maxima, refines exactly the pairs
  above them and reports the same peaks.
- **`tests/test_coarse_conformance.py`:** the same exact-decision check for every GPU coarse
  layout a device can choose, single calls and grouped.
- **Fail-open on overflow:** an fp16 value that overflows to inf or NaN passes the gate
  (comparisons are written `!(x < thr)`). This is checked by the transient and overflow
  cases of both conformance suites and by `tests/test_gpu_loud_overflow.py`.
