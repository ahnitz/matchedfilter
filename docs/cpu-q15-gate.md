# Q15 coarse screen (x86 CPU first tier)

On x86 the first tiers of a hierarchical chain can run in 16-bit fixed point (Q15) instead
of FP32. An int16 vector holds twice the lanes of a float one, so a call screens 16 pairs
on AVX2 and 32 on AVX-512. This page describes the screen, how it gates, how it is chosen
and what was measured. [Reduced-precision gates](reduced-precision-gates.md) states the
error model it shares with the FP16 gate on ARM.

## What it is

`src/q15-inl.h` with the generated `src/codelets-q15-inl.h` (`src/gen_q15.py`) is the
pair-batched coarse transform of conj(d t) in int16 Q15: split-radix codelets and a
four-step N = M1 M2 transform for N = 64 to 1024, generic over Highway targets.

Inputs are quantised once per template and once per data block (`matchfilt.c`) so that
`|d_q|_2 |t_q|_2 / 2^15 + 1.5 N <= 30000`. That bounds every intermediate: each is a
unit-weight partial sum of products, and the codelets scale each component before adding.
The transform's adds therefore wrap; within the bound they equal saturating adds bit for
bit and cost less (Zen 5: 72.7 to 69.2 TSC ticks per pair at N = 256). The final |z|^2 sum
saturates.

For partial AVX-512 template groups at N = 256, tail packing uses the spare lanes for
further data blocks with the same search window. Each lane keeps its own quantised operands
and arithmetic (`tests/test_q15_tail_packing.py`).

## How it gates

**The screen is the first tier itself** (`hmf.c`). A pair passes when its int16 maximum
reaches the tier's threshold. There is no margin and no float run of the tier behind it.
Survivors' peaks are still refined exactly. Like every tier, the screen answers to the
chain's false-dismissal budget against the flat filter.

**The tiers between the first and the last gate the same way, on their survivor lists**
(`ap_mf_q15_pairs`, `q15_screen_perm`). A batch takes its lanes from one slab of data
blocks and two adjacent groups of templates. Inside the product codelets each lane's
operands are looked up in vectors the screen already holds: the templates' prepacked
groups, and each block's data laid out across its slab (`q15_slab8`). There is no gather
pass, and a lane's maximum is bit-identical to the one the dense screen gives the same pair
(`tests/test_q15_pairs.py`).

The last tier stays FP32, because the direct refine reads its coarse lag.

`ap_mf_q15_screen` called on its own, outside a chain, rejects a pair only if its int16
maximum plus a margin of 5 sqrt(N) stays below the threshold (`ap_mf_set_q15_margin`).

## Accuracy

Error of the screen's statistic against float64, in Q units, over 40,960 pairs per N (noise
data; random and profile-shaped templates):

| N | rms | max | 5 sqrt(N) |
|---|---|---|---|
| 64 | 3.71 | 17.2 | 40 |
| 128 | 5.29 | 24.5 | 57 |
| 256 | 7.32 | 32.1 | 80 |
| 512 | 10.34 | 46.3 | 113 |
| 1024 | 14.34 | 60.7 | 160 |

The rms is 0.46 sqrt(N), a sum of independent Q15 roundings, and the largest error seen is
4.6 rms. The error does not grow with the peak: it is 0.44 to 0.47 sqrt(N) for noise,
profile-shaped inputs, injections reaching 29,000 LSB, loud transients and full-scale
inputs alike.

In a chain the screen's error is part of the statistic the gate model's thresholds are
judged on: `tools/fdr_audit.py --q15` measures every profile and chain against the flat
filter by injection, and the merge gate runs it. The standalone margin of 5 sqrt(N) is 10.7
rms. A tighter 3.12 sqrt(N) was tried and rejected: the worst error used up to 0.63 of it,
and it changed the fine stage's time by less than run-to-run noise.

## Selection

The screen is one dimension of the joint trial (`_trial`): its arms `q15=1` and `q15=0`
run beside the block-size arms, in the same paired rounds. Each plan's chain is the cost
model's under every arm; the chain is not an arm. The default is the cost model's screen
setting for each plan's chain (`CostModel.first_tier`), and decisions use paired ratios to
it. A challenger must beat the default by more than the 5% tie margin in at least 75% of
the rounds, and then win again in fresh rounds alone against the default. An unresolved
contest at the cap of rounds keeps the default.

`MF_AUTOTUNE=0` keeps the cost model's choice. Each pass's lock persists in `MF_COST_FILE`.
The screen is available where the back end has it (`ap_q15_lanes`).

For the model's choice, `calibrate_costs` measures per band the screen alone, the pairs it
passes at a calibration density, and what each pass costs beyond the screen (compaction).
The model prices the screen at every band from 64 to 1024 and every chain.

## The window maximum inside the last pass

The four-step screen's second pass can take the window maximum itself (`qsr{8,16,32}_twmax`
in `gen_q15.py`) rather than store its outputs for a third loop to read. The statistic is
bit-identical either way. Fusing pays only when the batch's working set overflows the L1
data cache and the register file can hold the extra live values without spilling:

| Machine, target | Batch working set / L1D | Vector registers | Fused against separate |
|---|---|---|---|
| Zen 5, AVX-512 (32 lanes) | 67 KB / 48 KB | 32 | fewer cycles |
| Apple M2, NEON | fits in 128 KB | 32 | slower |
| Zen 3, AVX2 (16 lanes) | 33 KB / 32 KB | 16 | 11% slower (spills) |

The dispatch in `src/q15-inl.h` therefore depends on the target's lane count and on the
batch's working set (`ap_q15_batch_bytes`) against the L1 size the OS reports
(`ap_l1d_bytes`).

For a window containing `[32, 224)` at N = 256, every 16-point row includes output indices
2 to 13. The generated `qsr16_twmax_middle` reduces those twelve without tests and keeps
four edge tests for the exact clipped window; other windows use the general codelet. On
Zen 5 (AVX-512, one core, 32 data blocks, window `[20, 236)`) this took about 2% fewer
cycles per pair, and about 3% off the screen's time on a production-shaped ladder.

## Measured gains

Production ladder (one top template, six segments, steady fine stage), the screen in front
of the float tier as first introduced, 2026-10-09:

| Host | CPU | Without | With | Gain |
|---|---|---|---|---|
| dev1 | Ryzen 9 5950X (Zen 3, AVX2) | 3.24 s | 2.73 s | 1.19x |
| dev3 | Ryzen 5 5500U (Zen 2, AVX2) | 4.49-4.51 s | 3.93-3.94 s | 1.14x |
| dev4 | i5-13500H (P-core, AVX2) | 2.84-2.85 s | 2.63 s | 1.08x |
| haswell | Xeon E5-2698 v3 (shared node) | 11.24-11.49 s | 9.15-9.48 s | 1.22x |

Since then the screen became the tier's own gate and the middle tiers gained it. On the
production replica (n = 2048, chain 256/512/1024) a Q15 second tier costs 509 ticks per
input against 753 for FP32, and the gated work drops 8.8%.

These are observations on those machines and that workload, not a promise for others.
