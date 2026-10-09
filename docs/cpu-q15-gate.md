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
Haswell, dev3, dev4 not measured (haswell at load 35 and without a build env).
