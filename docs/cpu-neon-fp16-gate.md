# The FP16 first gate on ARM NEON (src/gate16.cc)

The gate is built only where Highway reports FP16 vector arithmetic on AArch64 (every Apple
silicon core); x86 and other ARM builds compile stubs and run the FP32 path unchanged. The
measurements on this page were made on an Apple M2 (Mac mini).

## What and why

The hierarchical filter's tier 0 correlates every (block, template) pair at its coarse band. On
the M2 it was the fine stage's largest single cost (36% of samples). NEON runs an FP16 FMA on
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
  - `MF_GATE16=0` keeps the FP32 path, for measurement. The two are not a measured choice:
    wherever the gate is built and the switch is not set, plans use it.
  - `cpu_gate_kind()` puts the gate kind in the CPU cost-cache keys (`calibrate_costs`,
    `price_block_sizes`, the chain choice), so cached costs of one gate never price the other.
- **Scan.**
  - **All-lag power.** Computed by Parseval from FP32 |D|^2 and |T|^2, which are kept at
    ingest from the rounded FP16 values: m FMAs per pair group, in independent sums.
  - **Window maximum.** Found on FP16 powers |a y|^2, with a = 2^q chosen from that power so
    nothing overflows or reaches subnormals. Lags are tracked in int16, in two interleaved
    chains.
  - **Value.** The chosen lag's value is re-read in FP32.

## The gate's statistic, and the dismissal budget

The gate reports each pair's FP16 maximum over the searched window, its own statistic, and the
hierarchical filter compares it with the tier threshold, as the GPU's fp16 tier and the x86
Q15 screen do theirs. It tracks the FP32 maximum to a few u rms(y) (u = 2^-11; below). What
that does to the search is the chain's false dismissal against the flat filter, measured by
injection on Apple silicon (CI's macOS arm64 runner; `tools/fdr_audit.py --n 2048 4096 --inj
20000`, 10 profiles x 4 chains, fd 1e-2): no case was off its plan, and the pooled dismissal
was 1.041x the budget (+- 0.011 binomial), as the FP32 path's 1.036x on a Zen 5 in the same
audit.

The gate's error has two parts:

- **(1 + 3u): choosing the lag on FP16 powers.** Each FP16 power is within a factor (1 ± u)^2
  of the FP16 transform's |y|^2 (one exact power-of-two scale, one product, one FMA), so the
  chosen lag's value is below the FP16 maximum by at most (1+u)/(1-u) < 1 + 3u. This grows
  with the peak.
- **u rms(y): the transform's own rounding.** rms is taken over ALL m lags, so an
  out-of-window glitch, which raises the error everywhere, shows in it.

### Measured error

Measured with a tool since removed (it read the pair's all-lag rms from a debug mode of the
gate). The fine bank is the ladder's largest, with H1 profiles and the chain pinned. Every
(block, template) pair is dumped through `MF_HMF_DUMP` with tier thresholds 0, and the error is
normalised as

    e = (|y16|max  -  |y32|max) / (u rms)

**Transform error alone** (the lag chosen in FP32, so the lag choice adds nothing):

| case | pairs | max \|e\| | note |
|---|---|---|---|
| chain (256,512), seed 5 | 1.28M | 9.98 | mean -0.48, std 1.81, max relative error 2.0e-3 |
| + loud out-of-window transients | 638k | 12.87 | 7.1 std; max relative error 5.7e-3 |
| chain (64,256) | 479k | 8.16 | |
| chain (1024) | 479k | 9.82 | |

The transform error never went beyond 12.9 u rms in about 2.9M pairs; the worst case had
loud transients. An earlier design reported an upper bound on the FP32 maximum in place of
the gate's own statistic. It was removed because the bound passed pairs no plan priced:
single-tier chains at bands 1024 and 2048 dismissed 0.15-0.22x their plans.

## Timing

The command was:

    ladder.py --device cpu --profiles ladder_profiles_H1.npz --tops 1 --segments 8 --warmup 2 --pure

It was run with MF_GATE16=1 and with MF_GATE16=0. 4698 fine templates; steady times are over 6
segments.

| gate | steady fine | fine templates-in-real-time | total templates-in-real-time |
|---|---|---|---|
| FP32 | 9.95 s | 2.13e6 | 1.96e6 |
| FP16 | 6.36 s | 3.34e6 | 2.93e6 |

On this workload the FP16 gate made the fine stage 1.56x faster and the whole search 1.49x
faster. `tools/gate16_check.py` repeated it independently: 6.29 s against 9.85 s.
