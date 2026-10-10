# Q15 coarse screen (x86 CPU first tier)

Replaces `src/int16_coarse.h` / `MF_COARSE_INT16` (AVX2-only, N 256/512, 8 int16
lanes in a `__m128i`, so no lane advantage over float; its conj sign had been
fixed, its 0.55% error was never budgeted).

## What it is

`src/q15-inl.h` + generated `src/codelets-q15-inl.h` (`src/gen_q15.py`): the
pair-batched coarse transform of conj(d*t) in int16 Q15, split-radix codelets,
four-step N = M1*M2 for N = 64..1024, Highway-generic with **twice the float
lane count** (16 pairs on AVX2, 32 on AVX-512BW). Inputs are quantised once per
template and once per data block (`matchfilt.c`) so that
`|d_q|_2 |t_q|_2 / 2^15 + 1.5N <= 30000`, which bounds every intermediate (each
is a unit-weight partial sum of products); adds saturate.

It is a **screen, not a replacement**. A pair is rejected only if its int16
maximum plus the error margin stays below the tier threshold; every other pair
is re-run by the float tier (pooled, `hmf.c`). Survivors, peaks and triggers
are the float path's; the screen can only cost time, never change a result.

## Accuracy evidence

* Error of the screen statistic vs float64, in Q units, 40,960 pairs per N
  (noise data; random and ladder-profile-shaped templates):

  | N | rms | max | margin 5 sqrt(N) |
  |---|---|---|---|
  | 64 | 3.71 | 17.2 | 40 |
  | 128 | 5.29 | 24.5 | 57 |
  | 256 | 7.32 | 32.1 | 80 |
  | 512 | 10.34 | 46.3 | 113 |
  | 1024 | 14.34 | 60.7 | 160 |

  rms = 0.46 sqrt(N) (sum of independent Q15 roundings); max seen 4.6 rms. The
  margin is ~10.7 rms, derived from the rms, not swept against pass/fail. A
  first provisional margin of 2 sqrt(N) was found *too small* by this
  measurement (max/margin 1.0-1.08) and replaced.
* The mag^2 estimate's own rounding (+1 LSB) and the float tier's (1e-4 rel.)
  are added on the conservative side in `ap_mf_q15_screen`.
* Because survivors are re-run in float, the false-dismissal budget is the
  float chain's; it adds dismissals only if a Q15 error exceeds 10.7 rms.
  Caveat: the margin is statistical (roundings modelled independent); a
  worst-case deterministic bound (~N LSB) is too loose to use. Adversarially
  constructed inputs could in principle exceed it; noise-dominated data cannot
  in any practical sense.
* Tests (`tests/test_coarse_q15.py`): no pair with float max >= thr is ever
  rejected (N 64..1024, injections, partial windows/lane groups); hierarchical
  results bit-identical with the screen on/off for chains (256,), (512,),
  (128, 512). On the ladder, fine triggers identical (490) on/off at a fixed chain.

## Selection

Not a default and not an env switch: `HierarchicalFilter` alternates the
screen on/off on real calls per (n, snr, fd, chain), and every plan adopts the
faster once both sides have `MF_CHAIN_TRIALS` samples (`MF_AUTOTUNE=0` keeps
float). Available wherever the back end has it (`ap_q15_lanes`).

## Measured (ladder, test27 bank + H1 profiles, 1 top x 6 segments, steady, pinned)

dev1 (Ryzen 9 5950X, AVX2, load < 1), 3 interleaved reps, autotune on:
fine 3.24-3.25 s -> 2.73-2.74 s (**1.19x**); trial locks q15=True every time
(1.95e-7 -> 1.63e-7 s/pair). Tier 0 (band 256): 437 -> 330 cycles/pair; the
screen 288 cycles/pair; 6.8% of pairs re-run in float (float tier passes 4.5%).
Standalone kernel (dev2 Zen 5, loaded): 1.6-2.3x over the float pair kernel.

### All hosts (2026-10-09, base = main 46fe361 before the screen, steady fine stage, 2 interleaved reps each)

| host | CPU | base | screen | gain | note |
|---|---|---|---|---|---|
| dev1 | Ryzen 9 5950X (Zen 3, AVX2) | 3.24 s | 2.73 s | 1.19x | load < 1 |
| dev3 | Ryzen 5 5500U (Zen 2, AVX2) | 4.49-4.51 s | 3.93-3.94 s | 1.14x | load < 1 |
| dev4 | i5-13500H (Raptor Lake P-core, AVX2) | 2.84-2.85 s | 2.63 s | 1.08x | load < 1 |
| haswell | Xeon E5-2698 v3 | 11.24-11.49 s | 9.15-9.48 s | 1.22x | shared node, load ~38/64 |
| dev2 | Ryzen AI Max+ 395 (Zen 5, AVX-512) | -- | -- | -- | load 20-40 all day; only the standalone kernel figure above |

Fine triggers identical with and without the screen on every host. The trial chose the screen on every run.
Warm-up grows 5-18 s, from the screen's cost calibration plus its trials (calibration only runs once per process, or is
read from MF_COST_FILE).

### Pricing (MF_AUTOTUNE=0)

`calibrate_costs` also measures, per band with a screen: the screen alone (threshold
unreachable), its pass excess over the float tier at the calibration densities, and
the per-pair cost of re-running its survivors. `CostModel.first_tier` picks the
cheaper first tier; `choose_chain` records the choice and a plan built with
autotune off uses it. With autotune on, the on/off trial still decides. Cost files
written by a build without the screen are keyed apart (`,q15`).

### In-situ gap: none on AVX2

The 1.6-2.3x was the Zen 5 / AVX-512 standalone figure. On dev1 (AVX2) the standalone
kernel at the in-situ shape (32 blocks x 343 templates, band 256, window from n/4)
is 1.52-1.58x, against 437/288 = 1.52x in situ, so nothing is lost in the
integration. Two attempts to go further were measured and are not kept:
* fusing the window maximum into pass 2 (no store of pass-2 outputs): the screen got
  slower in situ, 288 -> 373 cycles/pair on dev1 (the per-output mask branch and the
  extra live registers in a 16-register file);
* other factorisations (256 = 8x32 / 32x8, 512 = 16x32): within +-3% of 16x16 / 32x16.
The per-pair threshold work is a vectorised per-lane computation, one per (template
group, block); it is not significant next to ~4.5K cycles per 16-lane call.

### Where the fine stage goes now (dev1, screen on)

Tier 0 (band 256) is 330 of ~420 cycles/pair: the screen 288, plus the float re-run of
6.5% of pairs (the float tier itself passes 4.5%). Tier 1 is 76, tier 2 14, refine 2.
The middle stage (correlation) is 0.39 s against 2.73 s. The next x86 lever is still
the first tier, not refine or forward: (a) the screen kernel's op count on AVX2
(split-radix int16 at ~4.4K cycles per 16-lane 256-point call), (b) the recheck excess
(2 points of the 6.5%, ~9% of tier 0) that a smaller derived margin would cut, and (c)
a cheaper 128-band screened first tier, which the model now prices.

## Margin: 5 sqrt(N) kept; a tighter Gaussian-tail margin rejected (2026-10-09)

A 3.12 sqrt(N) margin was derived from a 4e-11 Gaussian tail (rms 0.46-0.47 sqrt(N),
tails Gaussian to 4 rms on 307k noise pairs). Checked against the merge gate
(`tools/gate_margin.py`, criterion margin use < 0.5) and against 10k pairs per input
family (noise, profile, injection, loud transient, full scale; N = 128..1024):

* the error does not grow with the peak: rms 0.44-0.47 sqrt(N) in every family,
  including injections whose peaks reach 29000 LSB -- no peak-proportional term is
  needed, unlike the fp16 gate whose rounding is relative;
* but the worst error seen is 3.2-4.2 rms per family (4.6 in 307k pairs), so 3.12 sqrt(N)
  (6.6 rms) is used up to 0.63 -- it fails the 2x-headroom rule; the gate needs
  > ~9.2 rms = 4.3 sqrt(N);
* and it bought nothing measurable: screen pass rate 6.5% -> 5.8%, fine stage
  2.73 -> 2.70-2.72 s on dev1, inside run-to-run noise.

So the margin stays 5 sqrt(N) (10.7 rms). Harness, all families, N = 64..1024: 0
dismissals, margin use max 0.31.

## Band-128 screened first tier

Already a candidate: the model prices the screen at every band 64..1024 and every chain.
On the ladder workload it ranks (256,512,1024) first (416 vs 434/457 ticks for the next
two), and no 128-first chain reaches the top six, screened or not; the trials agree.

## dev2

Load stayed high most of the day; one window at load ~8: base 1.71 s -> 1.49 s (1.15x).
A second rep was invalidated by load rising to 18.

## Pricing a bounding first tier on the GPU (gatechain, 2026-10-09)

A first tier that reports an upper bound of the FP32 statistic (Vulkan fp16 coarse with
`MF_VK_C16_BOUND`, docs/vulkan-8060s-roofline.md section 10) passes a superset of the pairs
the gate model's noise draws assume; the extra pairs go straight to the next stage. That is
safe but was unpriced. Now, backend-neutrally:

* `_RAW_GATE_SWITCH` maps a GPU backend to the switch that makes its first tier report the
  raw statistic, and a gate kind (`c16b` for Vulkan). A backend whose kernel gains a bound
  adds a row; Metal and CUDA have none yet, so they price as before (`f32`).
* `calibrate_costs_gpu` measures, per band, the refined-pair count at thresholds placed at
  the calibration densities with the raw gate (in a child process: the switch is baked into
  pipelines and recorded command buffers, so it cannot be flipped within a context), and
  the bounded gate's count at the same thresholds: `CostModel.excess[b]`.
* `CostModel.chain_cost` scales the first stage after tier 0 by `pass_excess(b, reach)`.
  Later tiers are not scaled: the extra pairs sit just under the gate, and a later tier
  rejects them at its modelled rate or better.
* Cost files are keyed by gate kind (`gpu,n,device,c16b`), so a model measured without the
  bound is not reused for one with it.

Measured on the 8060S (n = 2048): bounded / raw pass rate 1.06-1.09 at 1% density and
1.04-1.07 at 10%, rising with band (64 -> 1024). Calibration grows by about 2 s per n.
