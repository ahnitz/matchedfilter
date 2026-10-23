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
is a unit-weight partial sum of products, and the codelets scale each component
before adding, so no sum of re and im forms first). The transform's adds therefore
wrap: within the contract they equal saturating adds bit for bit, and are cheaper
(Zen 5: 72.7 to 69.2 TSC ticks per pair at N = 256). The final |z|^2 sum saturates.

For partial AVX-512 N256 template groups, [tail packing](cpu-q15-tail-packing.md)
uses the spare lanes for additional data blocks with the same search window.
Each useful lane retains the original quantized operands and arithmetic.

**Since 2026-10-22 the screen is the first tier itself** (`hmf.c`,
[reduced-precision-gates.md](reduced-precision-gates.md)): a pair passes when its
int16 maximum reaches the tier's threshold, with no margin and no float run of the
tier behind it. Survivors' peaks are still refined exactly. What it answers to is
the chain's false-dismissal budget against the flat filter, as every tier does.

**The tiers between the first and the last gate the same way on their survivor lists**
(`ap_mf_q15_pairs`, `q15_screen_perm`). A batch takes its lanes from one slab of QW data
blocks and two adjacent groups of QW templates. Inside the product codelets (`*_prod_perm`),
each lane's operands are looked up in vectors the screen already has: the templates' own
prepacked groups, and each block's data laid out across its slab (built eight blocks at a
time, `q15_slab8`). There is no gather pass, and a lane's maximum is bit-identical to the one
the dense screen gives the same pair (`tests/test_q15_pairs.py`). The last tier stays FP32,
because the direct refine reads its coarse lag. On the production replica (n = 2048,
256/512/1024) tier 1 costs 509 ticks per input against 753 for FP32 (-32%), and the gated
work drops 8.8%.

Before that it was a **screen in front of the float tier**: a pair was rejected only
if its int16 maximum plus the error margin stayed below the tier threshold, and
every other pair was re-run by the float tier, so survivors, peaks and triggers were
the float path's. The sections below describe that design and its measurements;
the margin still applies to `ap_mf_q15_screen` called on its own
(`ap_mf_set_q15_margin`).

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

`HierarchicalFilter` measures screen on/off on identical input calls, pooled per
(n, snr, fd, chain, device). Each arm gets an untimed settling call, followed by
one timed call; the arm order reverses on the next round. Decisions use paired
ratios, so a large group is not compared with a small group's cost per pair.
There are at least `max(5, MF_CHAIN_TRIALS)` complete rounds (six by default),
and at most twice that many. A challenger needs at least 75% of the rounds to
beat the model by more than the existing 5% tie margin. An unresolved contest
at the cap keeps the model; this is an uncertainty fallback, not proof of a win.

Complete rounds and the final lock persist in `MF_COST_FILE`. Existing locks
remain authoritative, including locks written by earlier versions; a fresh
cost file is needed to reassess an old wrong lock. `MF_AUTOTUNE=0` retains the
cost-model screen choice. Availability follows the backend (`ap_q15_lanes`).
Replayed calls count as calibration work, including in native work counters.

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

## Fused window maximum: when a pass's working set leaves L1 (2026-10-13)

The four-step screen's pass 2 used to write every output back to its scratch and a third
loop re-read the scratch for the window maximum. `qsr{8,16,32}_twmax` (gen_q15.py) take the
maximum inside pass 2 instead; same Q_MUL squares, so the statistic is bit-identical.

Counters (tools/perf_counters.py), N = 256, the ladder's band:

| machine, target | batch working set / L1D | vector regs | IPC, L1 miss (separate) | fused vs separate |
|---|---|---|---|---|
| Zen 5, AVX-512 (32 lanes) | 67 KB / 48 KB | 32 | 1.4-2.7, 28-30% | 12-32% fewer cycles |
| Apple M2, NEON | fits / 128 KB | 32 | -- | +51 ms/segment (slower; ARM agent) |
| Zen 3, AVX2 (16 lanes) | 33 KB / 32 KB | 16 | 3.5, 7% | 11% slower (IPC 3.5 -> 3.0: spills) |

**Transferable rule:** fusing a reduction into a transform's last pass pays only when the
batch's working set overflows L1D *and* the register file can hold the extra live values
without spilling. Neither condition alone decides: the M2 has the registers but nothing to
save; Zen 3 overflows (barely, 7% misses) but spills. The selection computes the working
set from N, the lanes and the template group (`ap_q15_batch_bytes`), compares it with L1D
from the OS (`ap_l1d_bytes`: sysconf, sysfs, sysctl), and compiles the fused codelets only
on 32-register targets (`AP_Q15_VREGS32`). With L1D unknown, the 512-bit width stands in.

### N = 256 fixed-stride routing and broad windows

The N = 256 fixed-stride branch bypassed the selection above and always ran a separate
pass 2 and maximum. The earlier N = 256 fused measurements therefore did not describe
the committed dispatch. Pass 1 now keeps its constant strides while pass 2 reaches the
same cache/register policy; AVX2 and SSE4 retain the separate maximum.

For a window containing `[32, 224)`, every 16-point row includes output indices 2..13.
The generated `qsr16_twmax_middle` reduces those twelve outputs without tests, retaining
four edge tests for the exact clipped window. Other windows use the general codelet.
This covers the ladder's actual coarse windows (starts 17..23, ends 232..238), rather
than assuming its valid region starts at N/4.

Against ff5911cd on a Ryzen AI Max+ 395 (Zen 5), AVX3 pinned to one core, warm Q15
calls with 32 data blocks, 80/128/254 templates and window `[20, 236)` improved
1.015–1.031x over nine alternating rounds. A paired counter run at 128 templates
measured about 2% fewer cycles (median 126.0 to 122.6 per pair) and fewer instructions
(498.3 to 439.1); L1 misses were essentially unchanged. On a representative ladder workload
(synthetic PSD-colored data with real bank/profiles, cap 401, one top bank [id 4],
4698 fine templates across 27 middle banks, chain 256/512/1024, Q15 enabled), screen time
fell from 136.16/138.44 to 132.19/134.15 ms per segment, about 3%. The larger historical
12–32% figure above was not reproduced against the fixed-stride baseline.

The fixed-point arithmetic and `5 sqrt(N)` margin are unchanged. Before/after screen
statistics and decisions matched bit for bit across N = 64..1024, full/clipped/single-lag
windows and partial lane groups on AVX3, AVX2 and SSE4. The window regression in
`tests/test_coarse_q15.py` also compares each clipped maximum with the maximum of its
individual single-lag statistics, including the specialized dispatch boundaries.

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
