# CPU levers: what is left, by stage

> **Superseded ranking — read `docs/cpu-levers-consumer.md` first.** This plan was built
> on synthetic calls at n = 4096. Measured against the real consumer (`pycbc_inspiral_fir`,
> ntest3 settings, three hosts), the library runs at n = 2048 with cascades on 63–90% of
> hierarchical time, and tier-1 — dismissed below as "nothing to fix" — runs 2.4–6.7× over
> its full-lane ideal. Items 1, 3, 4, 5 (as 4096), 6, 7 and 8 below have no value for that
> consumer. The dispatch mechanics (section 1) and the non-power-of-2 analysis remain correct.

Measured assessment of the remaining CPU optimisation opportunities, organised by
execution stage and by the `run_series` interface callers actually use. Everything
quantified here was measured against HEAD `2a33e8f` unless stated otherwise.

**Short version.** The coarse stage is the better target at every operating point: it
is 50-86% of single-tier runtime, and a 1.3x coarse win is worth 1.16-1.27x end to end
against 1.05-1.13x for an equivalent refine win. Dispatch hinges on **template count
and band, and on nothing else** -- not the overlap-save window, not the series group.
Two eligibility constants disagree with each other, one selector blind spot is worth
1.31x, and the refine stage is blocked four ways at once. Non-power-of-2 bands are
structurally impossible and already superseded by the cascade.

---

## 1. How dispatch actually works

This is the spine of everything below, and it is easy to misread. The hierarchical plan
builds its coarse stage as a *native pair-batched plan* when it can, `hmf.c:61`:

```c
size_t pblim = pbmax ? (size_t)atol(pbmax)
                     : (ap_lane_width() >= 16 ? 1024u : 512u);
if (ntmpl >= 16 && band <= pblim)
    p->coarse = ap_mf_create_pairbatch(band, p->nd, ntmpl);
```

and `run_pairs` short-circuits on that plan *before any eligibility test runs*,
`matchfilt.c:439`:

```c
if (p->pb) return run_pairs_pb(p, d0, nd, t0, nt, tsel, nsel, ...);
/* only plans WITHOUT p->pb reach the gate below */
if (p->allow_pair_alt && !tsel && nd>=4 && nt>=16 && t0%p->w==0
    && 4*nt >= 3*((nt+p->w-1)/p->w)*p->w
    && end-start >= p->n/2 && binsize >= end-start) { ... }
```

So there are three dispatches, and which one a stage gets is decided at **plan
construction**, from the band and the template count:

| Stage | Plan | Size | AVX2 (AP_W 8) | AVX-512 (AP_W 16) |
|---|---|---|---|---|
| coarse / tier-0 | `p->coarse` | 256, 512 | native pb | native pb |
| coarse / tier-0 | `p->coarse` | 1024 | **alt -- loses 1.11x** | native pb, 1.44x |
| tier-1 | `p->coarse` | 512, 1024 | native pb (same plan) | native pb |
| tier-1 | `p->coarse` | 2048 | balanced | balanced |
| refine | `p->full` | 4096 | balanced, blocked 4 ways | balanced, blocked 4 ways |

Two consequences worth stating plainly:

- The `!tsel && nd>=4` gate **never touches the coarse stage or tier-1** at ordinary
  bands, because those run on a native pair-batched plan.
- The refine stage never reaches the gate either, because at n=4096 it fails the size
  caps first.

### Correction to the first version of this assessment

An earlier draft listed "relax `!tsel && nd>=4`" as a lever worth +6-16%, reasoning that
tier-1 passes a survivor list with `nd=1`. **That is withdrawn.** Tier-1 runs on
`p->coarse`, which is a native pair-batched plan at bands <= `pblim`, and
`run_pairs_pb` accepts `tsel` and any `nd` (`matchfilt.c:322`). Tier-1 already has the
fast path. Relaxing the gate buys nothing on its own; it matters only as one of four
things that must clear together for the refine stage.

The prediction that falsified it: narrow overlap-save windows were expected to fail
`end-start >= n/2` and lose the pair path. Measured across windows from the full
transform down to a quarter, the gain held at 1.36-1.52x with no trend. The gate was
never being consulted.

---

## 2. Assessment

Ranked by expected end-to-end value weighted by confidence and divided by effort.
"Confidence" is in the *mechanism*, not in the exact multiplier.

| # | Lever | Stage | End-to-end | Confidence | Effort | Basis |
|---|---|---|---|---|---|---|
| 1 | Make `alt_max_n` agree with `pblim` (512 on AVX2) | coarse | +10% at band 1024 | high | one token | 3-way A/B: balanced beats both pair variants |
| 2 | Q15 sign fix, then decide on enabling | coarse | 1.16-1.27x | high (defect) | small | defect proven; 1.3x is the repo's number |
| 3 | Widen the cascade candidate list | selection | up to 1.31x | high | small, Python | clean A/B at snr 5.5; 4 other SNRs already optimal |
| 4 | Document / revisit the `ntmpl >= 16` cliff | batching | 1.43x if callers trip it | high | small | sharp measured step at exactly 16 |
| 5 | Unblock the refine stage (all four conditions) | refine | 0-19% | low | new codelet | biggest blocked prize, least certain |
| 6 | Raise `pblim` / caps to 2048 for tier-1 | tier-1 | 0-8% | medium | guards, then measure | extrapolation ambiguous, 1.0-1.4x |
| 7 | Quad batching at N=64 | coarse | 0% today | low | high | real 48-68% hole at a size nothing selects |
| 8 | Hoist `getenv` out of `binmax_prod_batch` | coarse | <1% | high | trivial | same mistake the file fixed once already |
| -- | Non-power-of-2 bands | coarse | <=24% | don't | very high | structurally impossible; cascade already beats it |

---

## 3. Where the time goes

Single coarse stage -- the common configuration. Cycle shares from `MF_HMF_PROF`,
dev1, AVX2, 32x128, n=4096, fd=1e-3. The `gate` column is ~0% throughout, confirming no
tier-1 pass is present; `fill` (the series path's own forward FFT and 1/n scaling) is
1-3%.

| snr | band | coarse | refine | note |
|---|---|---|---|---|
| 5.50 | 256 | 24% | 75% | refine-dominated |
| 5.50 | 512 | 56% | 43% | near the selected band |
| 5.50 | 1024 | 86% | 13% | coarse-dominated |
| 5.75 | 512 | 71% | 28% | |
| 6.00 | 512 | 71% | 28% | |
| 6.50 | 256 | 48% | 50% | |
| 6.50 | 512 | 98% | 0% | gate never fires |

In cascades -- the minority case -- tier-1 is a consistent **15-27%** (512+1024 20%,
256+512 27%/15%/16%, 512+2048 21%).

### Making a stage faster barely moves the band

Re-minimising `total(b) = C(b)/kc + p(b)*F/kf` over the band grid, with `C` and `F`
measured and `p` from the gate model:

| Improvement | snr 5.0 | snr 5.5 | snr 6.0 | band moves? |
|---|---|---|---|---|
| coarse 1.3x | 1.18x | 1.16x | 1.27x | no |
| coarse 1.5x | 1.28x | 1.26x | 1.44x | no |
| refine 1.4x | 1.11x | 1.13x | 1.05x | 512->256 at 6.0 (+2.6%) |
| refine 1.7x | 1.17x | 1.19x | 1.17x | 512->256 at 6.0 (+13.6%) |
| both 1.3 / 1.4 | 1.33x | 1.34x | 1.31x | no |

**Coarse work pays roughly twice what refine work pays** for the same multiplier. The
re-selection effect you would expect -- cheaper refine means you can afford to gate less
aggressively, so the optimal band should drop -- mostly fails to appear, because
consecutive bands are a factor of two apart and the optimum has to move a long way
before it crosses. It fires once, at snr 6.0 with refine >= 1.4x. That is the only place
in this analysis where a finer band grid would earn anything, and it is not enough to
pay for one.

---

## 4. The series interface, and the batching choice

`run_series` collects up to `dgroup` consecutive blocks that share a window and issues
one `ap_hmf_run` with `nd = g`. `dgroup` defaults to 32/16/8 for n <= 512 / <= 1024 /
larger, bounded so the held spectra stay under 4 MB (`hmf.c:58`), overridable with
`MF_DGROUP`.

The natural worry is that overlap-save defeats the fast path: the gate tests
`end-start >= n/2`, and a valid window is by construction smaller than the transform.
**Measured, it does not -- because the gate is never reached.**

| valid | window | frac | pair ON | OFF | gain | gate would say |
|---|---|---|---|---|---|---|
| (0, 4096) | 4096 | 1.000 | 0.0542 | 0.0739 | 1.36x | pass |
| (1024, 4096) | 3072 | 0.750 | 0.0521 | 0.0750 | 1.44x | pass |
| (2048, 4096) | 2048 | 0.500 | 0.0511 | 0.0738 | 1.44x | pass |
| (2049, 4096) | 2047 | 0.500 | 0.0520 | 0.0735 | 1.41x | **refuse** |
| (3072, 4096) | 1024 | 0.250 | 0.0500 | 0.0722 | 1.45x | **refuse** |

ms per block, dev1 AVX2, band 512, 128 templates. The two rows the gate would refuse
gain as much as the rest.

Same for the group size: `dgroup` from 1 to 32 lands within 1.5% (0.0526 / 0.0526 /
0.0520 / 0.0518 / 0.0526 / 0.0518 ms per block), including values below the `nd >= 4`
the gate asks for. Lanes span *templates*, not data, so adding data blocks per call
cannot fill them better; and data-spectrum ingestion is already lazy, so there is little
left for a bigger group to amortise.

### What does decide it: the template count

`ntmpl >= 16` on the pairbatch branch is tested against the *plan's* template count, not
the per-call count. Below it, no pair-batched coarse plan is built at all:

| ntmpl | us/pair | balanced | gain | pairbatch plan? |
|---|---|---|---|---|
| 8 | 0.5515 | 0.5524 | 1.00x | no |
| 12 | 0.5493 | 0.5538 | 1.01x | no |
| 15 | 0.5411 | 0.5444 | 1.01x | no |
| **16** | **0.3822** | 0.5464 | **1.43x** | yes |
| 32 | 0.3684 | 0.5304 | 1.44x | yes |
| 128 | 0.3766 | 0.5176 | 1.37x | yes |
| 256 | 0.3760 | 0.5212 | 1.39x | yes |

A 1.42x step at a single template. Any caller constructing a filter with fewer than 16
templates silently runs the whole coarse stage on the slow path -- and the coarse stage
is 50-86% of runtime. Two things follow:

- **Never build a filter with < 16 templates** if the bank has more; batch them. This is
  the single highest-leverage caller-side choice.
- **Prefer template counts that are multiples of `AP_W`** (8 on AVX2, 16 on AVX-512).
  `p->ntpad` rounds the count up to a multiple of the lane width (`matchfilt.c:116`), so
  17 templates on AVX2 runs 24 lanes' worth -- 29% of the coarse work discarded.
  *Derived from the padding arithmetic, not separately measured.*

The constant 16 is worth a second look on its own: it is a fixed number against a lane
width that varies. On AVX-512 it is exactly one register; on AVX2 two, on SSE4 four. If
the intent was "at least one full register", it should be `AP_W`, which would let AVX2
callers qualify at 8 templates.

---

## 5. Stage: the coarse pass

**Share** 50-86% at the selected band. **Plan** native pairbatch when `ntmpl>=16` and
`band<=pblim`. **Status** on the fast path, with one exception.

A pair batch is exactly `AP_W` pairs -- one register's worth (`balanced-inl.h:1541`) --
with lanes carrying independent (data, template) pairs, which removes the four-step
corner turn. Measured on native AVX2, idle, 21 reps interleaved inside one process:

| N | pair ON | pair OFF | gain | per-butterfly | note |
|---|---|---|---|---|---|
| 64 | 0.159 ms | 0.292 ms | 1.83x | 4.146e-4 | below the selector's floor |
| 128 | 0.273 ms | 0.547 ms | 2.00x | 3.051e-4 | |
| 256 | 0.574 ms | 1.024 ms | 1.78x | 2.803e-4 | most efficient |
| 512 | 1.535 ms | 2.151 ms | 1.40x | 3.330e-4 | |
| 1024 | 3.675 ms | 3.409 ms | **0.93x** | 3.588e-4 | **regression** |

### 5a. Two limits disagree, and the wrong one wins at band 1024 on AVX2

The codebase carries two independent caps on how far the pair path extends, and they do
not agree:

- `hmf.c:62` -- `pblim = AP_W>=16 ? 1024 : `**`512`**
- `matchfilt.c:106` -- `alt_max_n = (AVX3 || AVX2) ? `**`1024`**` : 512`

On AVX2 at band 1024, `pblim` correctly declines to build a pair-batched plan -- and then
`allow_pair_alt` picks it up anyway and loses. A three-way comparison in one process
settles which limit is right (coarse pass only, 4096 pairs, ms):

| band | native pb | alt (default) | balanced | fastest |
|---|---|---|---|---|
| 256 | 0.6192 | 0.6168 | 1.0135 | either pair path |
| 512 | 1.5241 | 1.5309 | 2.1355 | either pair path |
| 1024 | 3.7127 | 3.7767 | **3.3879** | **balanced** |

At band 1024 on AVX2 *both* pair variants lose to balanced -- native by 1.10x, alt by
1.11x. So the pair path genuinely does not suit that size on AVX2, `pblim = 512` is
correct, and `alt_max_n` should match it. On AVX-512 the opposite holds: band 1024 gains
1.44x. The fix is to derive one limit from the other rather than maintain two.

`docs/cpu-plan.md:99` quotes 1.83x at band 1024, but that table's header reads "Ryzen AI
Max+ 395, AVX3" -- the AVX-512 result was extended to the AVX2 arm without being measured
there. The regression reproduces in every batch shape tested: 0.88x / 0.92x / 0.92x /
0.90x at 8x512, 16x256, 8x64, 32x128.

### 5b. The Q15 int16 kernel is still wrong at HEAD

`int16_coarse.h:218` computes `d*conj(t)` where `codelets-inl.h:9179` computes
`conj(d*t)`. The two sign flips do not cancel -- settled empirically rather than argued.
The path is AVX2-only, N in {256, 512}, `nb == 1`, and gated behind `MF_COARSE_INT16`, so
it is **off by default**.

Read its value accordingly. Fixing the sign is a correctness fix that costs nothing and
speeds nothing up by itself. What it unlocks is the option of enabling a kernel the repo
prices at 1.3-1.5x (`docs/coarse-kernel-plan-haswell.md` -- not measured here). Against a
coarse share of 50-86%, that is **1.16-1.27x end to end**, the largest single number in
this document. Enabling it needs its own accuracy validation; N in {256, 512} is exactly
the band range the selector picks, so the opportunity is not hypothetical.

### 5c. Quad batching -- right diagnosis, wrong size

Quad batching would put four `AP_W`-wide groups in flight. The per-butterfly column (log
factor divided out) says where the latency hole is:

| N | AVX2 | vs best | AVX-512 | vs best |
|---|---|---|---|---|
| 64 | 4.146e-4 | **+48%** | 2.352e-4 | **+68%** |
| 128 | 3.051e-4 | +9% | 1.432e-4 | +2% |
| 256 | 2.803e-4 | -- | 1.398e-4 | -- |

The hole is at **64 only** -- 128 is already within 2-9% of optimal, so there is nothing
there for extra ILP to recover. The 48-68% is genuinely inside the kernel, not call
overhead: a fixed-overhead model fitted on 128/256/512 predicts 0.058 ms at N=64 against
0.090 ms measured.

Two things kill it anyway. The buffers are `4 * N * AP_W * 4` bytes, so four streams at
N=64 goes 16 KB -> 64 KB on AVX-512, past the 48 KB L1 -- the naive version spends its own
prize. And `_min_band_for` floors the coarse band at 128, so **64 is never selected**.
Revisit only if a cheaper sub-128 tier-0 becomes attractive.

---

## 6. Stage: the refine pass

**Share** 13-43% at the selected band, up to 75%. **Call**
`ap_mf_run_sel(full, d0+d, 1, t0, nt, firebuf, nfire, ...)` (`hmf.c:403`).
**Status** blocked four ways.

*All four* must clear before any of it is even testable, which is why no single one is a
lever on its own:

1. `ap_create_pairbatch()` refuses N > 1024 (`dispatch.c:43`), so `p->full` is never a
   pairbatch plan.
2. `pairbatch_size()` returns 0 for N > 1024 (`balanced-inl.h:101`), and it sits *above*
   the `MF_PBMAX` read, so no override reaches it. Confirmed: `MF_PBMAX=4096` leaves 2048
   and 4096 untouched.
3. `esupported()` tops out at 2048 (`elemfft-inl.h:20`), so 4096 has no element
   decomposition at all. A 64x64 split would need adding; both halves already exist as
   element sizes.
4. The dispatch gate's `!tsel && nd>=4`, which `hmf.c:403` fails on both counts. Moot
   while 1-3 hold.

The prize is visible with the log factor divided out: on AVX-512 the per-butterfly cost
is 1.40-1.61e-4 across 256-1024 but **2.43e-4 at 4096** -- a 1.7x efficiency gap that is
not the transform getting bigger. How much the pair path would recover is genuinely
uncertain: the gain-ratio trend (2.19 / 1.86 / 1.44 at 256 / 512 / 1024) extrapolates to
~1.1x, while the per-butterfly trend extrapolates to ~1.38x. The two disagree because the
balanced path at 2048 breaks its own declining trend, which is itself worth explaining.

Against a 13-43% share, even the optimistic end is worth only 1.05-1.19x end to end. That
is why this ranks below the coarse work despite being the larger structural problem, and
why it should not be started before items 1-4.

---

## 7. Stage: tier-1 (cascades only)

**Share** 15-27%, when a cascade is used at all. **Plan** `p->coarse` -- the same plan
tier-0 uses. **Status** already on the fast path at band <= `pblim`.

Tier-1 is a coarse pass at band 512-2048 over the survivors of tier-0. Because it runs on
`p->coarse`, it inherits whatever dispatch that plan got -- so at bands 512 and 1024 it is
already pair-batched, with `run_pairs_pb` taking the survivor list directly. **There is
nothing to fix here**; see the correction in section 1.

The one exception is **band 2048**, above every pair-path cap, which runs balanced. In a
512+2048 cascade that is 21% of runtime on the slow path. Raising the caps to 2048 is
cheap to *try* -- `esupported()` already accepts 2048 with `efactor` 64x32 -- but the
working set is `4*N*AP_W*4` = 512 KB on AVX-512 and 256 KB on AVX2, which lands on or past
L2 on several targets. Measure before committing.

---

## 8. Stage: selection

`candidate_configs` picks one single-tier band `b1` from the analytic cost, then only
considers cascades with `b0 in {b1/2, b1/4}`. A configuration whose tier-1 band is larger
than the single-tier winner is unreachable by construction. Clean interleaved A/B, 15
rounds, against the best configuration the library can already express:

| snr | selector picks | ms | best expressible | ms | gap |
|---|---|---|---|---|---|
| 5.00 | (1024, 8) | 2.1757 | 512+1024 | 3.5019 | selector ahead |
| 5.50 | (512, 8) | 1.1085 | 512+2048 | 0.8472 | **1.31x** |
| 6.00 | (512, 8) | 0.5694 | 256+512 | 0.5562 | 1.02x |
| 6.50 | (256, 512, 8) | 0.2695 | 256+512 | 0.2710 | optimal |
| 7.00 | (256, 512, 8) | 0.2206 | 256+1024 | 0.2210 | optimal |

Four of five are already optimal, so this is one blind spot rather than a broken selector
-- but snr 5.5 is a common operating point, and 512+2048 is provably unreachable there
because the analytic cost never picks `b1 = 2048` as the single-tier winner.

### Interaction worth planning for

Items 1 and 2 both change the cost of the coarse stage, which is the input the selector
ranks on. The analytic fallback in `candidate_configs` models coarse cost as
`b*log2(b)` -- it has no notion of a dispatch cliff at `pblim` or of a Q15 kernel that
applies only at 256 and 512. Today that mis-pricing is partly masked because the cliff
sits at 1024 on AVX2 and the selector often picks 512 anyway. Fix 1 without touching the
cost model and the mis-pricing stays; enable Q15 and it gets worse, because 256 and 512
become cheaper than the model believes while 1024 does not. **Whatever changes stage costs
should land together with a cost model that knows about it**, or the selector will keep
choosing on stale relative prices.

### Separate observation

Under load, the runtime autotuner picked *different* configurations for the same snr
across runs -- (512, 1024, 8) and (256, 512, 8) at snr 5.0 and 5.5 in one pass,
single-tier (1024, 8) and (512, 8) in another. Its choice is contention-sensitive: a
measurement hazard for anyone A/B-testing on a shared machine, and possibly a stability
problem in its own right.

---

## 9. Not worth doing

### Non-power-of-2 bands

Four places enforce power-of-two bands -- `__init__.py:1998`, `gatemodel.py:298`,
`hmf.c:335` (`R0 = n/m0`, `cstart0 = start/R0`) and the FFT itself. Removing all four
changes nothing, because the binding constraint is upstream: **band must divide n, and n
is a power of two, so every legal band already is one.** "Divides n" and "is a power of
two" are the same constraint here. The engine rejects n = 768 / 1280 / 1536 / 3072
outright (verified), so a non-power-of-2 band means a mixed-radix codelet family *and* a
non-integer coarse lag grid in `hmf.c`.

Priced anyway, by sweeping the measured cost model over a continuous band: a perfectly
free band is worth 0-16% at the SNRs tested, 24% worst case (snr 6.1, where the free
optimum lands at 351, mid-octave between 256 and 512). Meanwhile the two-tier cascade
already delivers more using only sizes that exist -- 1.32x at snr 5.5 (512 -> 512+2048)
and 1.38x at snr 6.5 (256 -> 256+512). The intermediate operating points are already
reachable as `(b0, b1)` pairs at zero FFT cost.

### Bigger series groups

Measured flat from `dgroup` 1 to 32. Lanes span templates, not data blocks, and data
ingestion is already lazy. The only reason to touch `dgroup` is the 4 MB spectra bound at
long n.

---

## 10. Measurement conditions

n = 4096, inspiral reference profile, fd = 1e-3, 4096 pairs unless stated. Every
pair-path A/B builds both plan sets in one process (`MF_PBMAX` is read only at plan
creation) and alternates their runs, so the ratio is immune to load drift.

- **AVX2 figures** -- dev1, Ryzen 9 5950X (Zen 3, AP_W = 8, no AVX-512), idle at load
  0.19, pinned, 15-21 reps interleaved, min/median spread 1.5%. These are the clean
  numbers and carry the main conclusions.
- **AVX-512 figures** -- dev2, Ryzen AI MAX+ 395 (Zen 5, AP_W = 16), load ~10/32, pinned,
  min of 9 interleaved. Absolute times are inflated; only ratios and per-butterfly
  comparisons are used. The band-1024 three-way comparison was **not** repeated on
  AVX-512 (machine at load 48); the AVX-512 claim there rests on the earlier 1.44x
  native-vs-balanced result.
- **Discarded** -- every run taken while dev2 was above load 40. Contention compressed the
  AVX-512 pair gains from 2.19/1.86/1.44 to 1.56/1.44/1.14 and inverted at least one
  ratio. An earlier separate-process harness was discarded for the same reason.
- **Control caveat** -- `MF_PBMAX=1` disables both the native pairbatch plan and
  `allow_pair_alt`, so it is a clean "no pair path" control but does not separate the two.
  The three-way table in 5a uses `MF_PBMAX=<band>` to isolate them.
- **Resolution limit** -- measured refine rates are quantised by the data-segment count.
  Cycle shares are not affected.

Source references are against HEAD `2a33e8f`.
