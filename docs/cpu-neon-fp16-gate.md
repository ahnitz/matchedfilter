# The FP16 first gate on ARM NEON (src/gate16.cc)

Written 2026-10-09 by the Metal track (phase 5). Machine: Mac mini, Apple M2 (empire). The gate
is built only where Highway reports FP16 vector arithmetic on AArch64 (every Apple silicon
core); x86 and other ARM builds compile stubs and run the FP32 path unchanged.

## What and why

The hierarchical filter's tier 0 correlates every (block, template) pair at its coarse band. On
the M2 CPU fine stage it was the largest single cost (36% of samples). NEON runs an FP16 FMA on
8 lanes in the time FP32 runs 4 (measured on one performance core: 143 against 72 GFLOP/s), and
a gate only has to decide "maybe": every survivor is still refined exactly, in FP32.

- **Kernel.** The same element transform the FP32 pair-batched path runs (`elemfft-inl.h`, the
  generated codelets, the fused product loader `efft_prod_broadcast`), compiled a second time
  with the lane type FP16, so 8 templates share a vector instead of 4.
- **Storage.** Coarse spectra are stored in FP16 at ingest (templates conjugated, laid out
  [group][element][lane]; data per slot). Each spectrum is scaled by a power of two so its
  largest component is below 1. Products are then at most 1 and an m-point transform at most
  m, inside FP16's range, and the scale is exact to undo.
- **Dispatch.** `hmf.c` creates the gate for tier 0 when `ap_gate16_available()`. It feeds the
  gate in `refresh_template` and `set_data`, and calls `ap_gate16_run` instead of `ap_mf_run`
  for tier 0. Later tiers and the refine are unchanged.
- **Switches.**
  - `MF_GATE16=0` keeps the FP32 path, which remains a measured candidate.
  - `cpu_gate_kind()` puts the gate kind in the CPU cost-cache keys (`calibrate_costs`,
    `price_block_sizes`, the chain choice), so cached costs of one gate never price the other.
- **Scan.**
  - **All-lag power.** Computed by Parseval from FP32 |D|^2 and |T|^2, which are kept at
    ingest from the rounded FP16 values: m FMAs per pair group, in independent sums.
  - **Window maximum.** Found on FP16 powers |a y|^2, with a = 2^q chosen from that power so
    nothing overflows or reaches subnormals. Lags are tracked in int16, in two interleaved
    chains.
  - **Value.** The chosen lag's value is re-read in FP32.

## The bound, and why the dismissal budget is unchanged

For every pair the gate reports an UPPER BOUND on the FP32 gate's coarse maximum:

    B = |y16(k')| (1 + 3u) + kappa u rms(y),     u = 2^-11,  kappa = 16

The hierarchical filter compares B with the tier threshold. Every pair the FP32 gate passes
then passes here, so the survivors of the FP16 gate are a superset of the FP32 gate's. The
false-dismissal rate is therefore at most that of the FP32 gate plus the probability that the
bound fails, which is the measured tail below. The price is a few more refinements.

- **(1 + 3u): choosing the lag on FP16 powers. This is proven, not fitted.**
  - Each FP16 power is within a factor (1 ± u)^2 of the FP16 transform's |y|^2: one exact
    power-of-two scale, one product, one FMA.
  - So the chosen lag k' satisfies |y16|max <= |y16(k')| (1+u)/(1-u) < |y16(k')| (1+3u).
  - This term grows with the peak, which the rms term does not.
  - Without it, a build that chose the lag in FP16 measured e = -15.1 on loud transients,
    close to kappa: the lag-choice error scales with peak/rms, so no fixed kappa would bound it.
- **kappa u rms(y): the transform's own rounding error.**
  - rms is taken over ALL m lags, so an out-of-window glitch, which raises the error
    everywhere, raises the bound with it.
  - kappa is set from measurement. It was not swept until the tests passed.

### Measured error (tools/gate16_error.py)

The fine bank is the ladder's largest, with H1 profiles and the chain pinned. Every (block,
template) pair is dumped through `MF_HMF_DUMP` with tier thresholds 0, and the error is
normalised as

    e = (B with kappa=0  -  |y32|max) / (u rms)

The bound fails only where e < -kappa.

**Transform error alone.** The earlier build scanned in FP32, so the lag choice was exact and
B with kappa=0 was the plain |y16|max.

| case | pairs | max \|e\| | note |
|---|---|---|---|
| chain (256,512), seed 5 | 1.28M | 9.98 | mean -0.48, std 1.81, max relative error 2.0e-3 |
| + loud out-of-window transients | 638k | 12.87 | 7.1 std; max relative error 5.7e-3 |
| chain (64,256) | 479k | 8.16 | |
| chain (1024) | 479k | 9.82 | |

**Shipped build.** FP16 lag choice plus the (1+3u) factor; 638k pairs per case.

| case | most negative e | mean e | 99.99% \|e\| |
|---|---|---|---|
| chain (256,512), seed 5 | -1.62 | +6.7 | 15.3 |
| + transients, seed 3 | -1.87 | +6.8 | 26.1 |
| + transients, seed 11 | -1.98 | +6.8 | 25.4 |
| chain (64,256) | -1.90 | +5.9 | 13.7 |
| chain (1024) | -1.30 | +7.5 | 16.8 |

Positive e is slack: the bound sits above the FP32 maximum.

**How much headroom kappa = 16 has**

- The transform error alone never went beyond 12.9 u rms in about 2.9M pairs. The worst case
  had loud transients and sat 7.1 standard deviations out.
- With the shipped factor, the bound's worst slack is -2 u rms, which is 14 units inside kappa.

**What the margin costs**

- (1+3u) adds 0.15% of the peak.
- kappa u rms adds 0.8% of rms, about 0.3% of a typical coarse maximum.
- Neither moves the pass rate noticeably: the ladder's fine_triggers count is the same in both
  modes (588).

The probability that the bound fails is below the measured resolution (0 in about 3.2M pairs),
far below the dismissal budget's 1e-3.

### Paired false-dismissal audit (tools/verify_cascade_fdr.py)

Run with `--shapes all --injections 20000 --seed 42` in each mode. The figures are misses among
about 11.5k ground-truth fine detections per shape; the budget is 0.1%, about 11.5 misses.

| shape | single FP32 | single FP16 | cascade FP32 | cascade FP16 |
|---|---|---|---|---|
| inspiral_canonical | 15 | 13 | 16 | 16 |
| aligo_o4_inspiral | 14 | 12 | 9 | 9 |
| notched_lines | 14 | 12 | 6 | 6 |
| bimodal_resonance | 22 | 21 | 15 | 14 |
| bandpass_plateau | 8 | 7 | 7 | 7 |
| skewed_edge | 3 | 2 | 2 | 2 |

- **No shape got worse.** FP16 misses are at most the FP32 misses on every shape and tier, as
  the superset argument requires. The few fewer misses are pairs the margin lets through.
- **Two shapes are over budget in both modes.** inspiral_canonical's cascade and
  bimodal_resonance's single tier and cascade miss more than about 11.5. The FP32 gate has
  identical counts there, so this is a property of the thresholds and was not introduced here.

### End-to-end check (tools/gate16_check.py, ladder `--check`)

- **Setup.** The realistic ladder ran on the CPU in one process, FP16 gate then FP32 gate, with
  the same seed: bank3, H1 profiles, 1 top, 8 segments, warm-up 2.
- **Calls.** 558 calls.
- **max_snr_diff.** 0.0.
- **Peaks found by only one mode.** 0 one-sided peaks in either direction (reference-only 0,
  device-only 0).
- **gate_margin_peaks.** 0.

The refine is FP32 in both modes, so every peak is bit-identical.

## Timing

The command was:

    ladder.py --device cpu --profiles ladder_profiles_H1.npz --tops 1 --segments 8 --warmup 2 --pure

It was run with MF_GATE16=1 and with MF_GATE16=0. 4698 fine templates; steady times are over 6
segments.

| gate | steady fine | fine templates-in-real-time | total templates-in-real-time |
|---|---|---|---|
| FP32 | 9.95 s | 2.13e6 | 1.96e6 |
| FP16 | 6.36 s | 3.34e6 | 2.93e6 |

The FP16 gate makes the fine stage 1.56x faster and the whole search 1.49x faster.
gate16_check repeated this independently: 6.29 s against 9.85 s.

**Where the time goes now** (`sample`, 15 s of the FP16 fine stage):

| function | samples |
|---|---|
| FP16 product and loader (codelet_prod_broadcast) | 2348 |
| FP16 twiddle passes (codelet_tw) | 1733 |
| ap_gate16_run (Parseval sums and window scan) | 1396 |
| FP32 refine (codelet_prod) | 570 |
| run_pairs_pooled_pb | 553 |
| gather_template_batch | 503 |

The scan fell from 1995 to 1396 samples with these changes:

- Parseval in place of an FP32 pass over every lag.
- The window maximum found in FP16.
- Independent accumulator chains.

The first FP16 rewrite was slower, at 2578 samples, because one FMA chain was bound by latency.

## Not done / next

- **The scan is still a third of the transform's cost.** Fusing the window scan into the
  transform's final pass, so the outputs are not re-read, is the remaining lever.
- **The over-budget shapes need threshold work.** inspiral_canonical and bimodal_resonance
  exceed budget under both gates; that belongs to the threshold calibration, not to this gate.
