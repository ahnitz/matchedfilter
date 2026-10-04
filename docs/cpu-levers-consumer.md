# CPU levers, re-assessed against the real consumer

This supersedes the **ranking** in `docs/cpu-levers.md`. That plan was built from
synthetic `HierarchicalFilter` calls at n = 4096. The library's actual consumer,
`pycbc_inspiral_fir` run with `ntest3.sh` settings, drives it differently enough that
several of its top items do not apply and its biggest lever was missed. The dispatch
analysis in `cpu-levers.md` §1 and the non-power-of-2 conclusion remain correct.

Everything here was measured with the real consumer, single core, on three hosts:
HEAD `4801290` (CPU code identical to `2a33e8f`), apogee `a55a21461`, ntest3 arguments
on a 3,000 s span (1000000000–1000003000), bank `fir_three_level_701taps.hdf`.

---

## 1. How the consumer actually drives the library

```
pycbc_inspiral_fir
 ├─ UpperReferenceBatch  ->  TimeDomainFilterBank(engine='corr')
 │                              CorrelationFilter.correlate_series_continuous   (full output)
 └─ MatchedFilterRatioControl -> TimeDomainFilterBank(engine='hier').filter_series
                                    HierarchicalFilter.run_series               (peaks)
```

| Property | Primary (fine) stage | Upper stage |
|---|---|---|
| FFT length n | **2048 for all 86,649 templates** | 8192 (362), 16384 (235) |
| Tap counts | 151–701, only 7 distinct values | 3001–6001 |
| Templates per group | median ~140–167, up to 254 | median 17, max 23 |
| Blocks per call | ~460–544 (512 s segments) | — |
| Valid fraction | 0.70 (30% of work is overlap) | 0.63 |
| Coarse bands in play | 128, 256, 512 | n/a |
| Threshold / fd | **6.0** (asym primary) / 1e-3 | n/a |

None of the plan's measurements used n = 2048, threshold 6.0, or FIR-shaped templates.

## 2. Where the time goes

Single-core, consumer-attributed. dev2 = Ryzen AI MAX+ 395 (Zen 5, AVX-512, shared, load
9–28). dev1 = Ryzen 9 5950X (Zen 3, AVX2, idle). Haswell = 2×E5-2698 v3 (AVX2, 256 KB L2
per core, shared node at load ~40; the production-like host).

| | dev2 | dev1 | Haswell |
|---|---|---|---|
| Wall time, 3,000 s span | 175 s | 216 s | 884 s |
| **Library share of wall** | 72% | 79% | 74% |
| ↳ hierarchical `run_series` | 60.3% | 68.1% | 61.9% |
| ↳ upper `correlate_series_continuous` | 8.0% | 9.0% | 10.0% |
| ↳ `filter_series` wrapper + followup | 3.5% | 1.8% | 2.5% |
| Hierarchical split: tier-0 | 40.4% | 40.8% | 45.9% |
| ↳ **tier-1** | **28.2%** | **19.1%** | **15.0%** |
| ↳ refine (n = 2048) | 8.9% | 22.1% | 20.1% |
| ↳ outside kernels (forward FFT, scaling, Python) | 21.9% | 17.2% | 18.5% |
| **Cascade share of hierarchical time** | 90% | 78% | 63% |
| Dominant config | (256, 512) | (128, 256) | (128, 256) |

**Cascades are the main path on every host**, including the production-like one. A
replay of real captured groups confirms that is the right choice (§4, item 4).

## Combined potential

Rebuilt from the measured stage shares of §2, applying each lever only to the stage it
touches. PyCBC's own time (22–32% of the run) is unchanged. Speedup = old time / new time.

| Host | Tier-1 staging alone | Everything: conservative | central | optimistic |
|---|---|---|---|---|
| **Haswell** (production-like), whole run | 1.05× | 1.17× | **1.24×** | 1.30× |
| ↳ library time only | 1.07× | 1.25× | 1.36× | 1.47× |
| dev1, whole run | 1.07× | 1.21× | **1.29×** | 1.37× |
| ↳ library time only | 1.09× | 1.28× | 1.42× | 1.54× |
| dev2 (AVX-512), whole run | 1.16× | 1.18× | **1.22×** | 1.24× |
| ↳ library time only | 1.25× | 1.29× | 1.35× | 1.40× |

"Everything" = tier-1 staging + Q15 with an N = 128 variant (AVX2 only; dev2 would need a
port) + refine pair path at 2048 + forward-FFT batching + upper-stage N. Assumptions per
scenario (conservative / central / optimistic): tier-1 left at 1.5× / 1.2× / 1.1× of its
ideal; Q15 kernel gain 1.3× / 1.4× / 1.5×; refine 1.3× / 1.5× / 1.8×; forward path 1.1× /
1.2× / 1.3×; upper stage as measured per host. Not modelled, and only in the favourable
direction: groups switching to cascades once tier-1 is cheap, and Q15 on tier-1.

Only tier-1 staging has both a measured mechanism and no outside dependency. Q15's gain is
the repo's claim and needs accuracy validation; the refine pair path at 2048 has never been
measured. For comparison, the original plan's items move ntest3 by ≈0%.

## 3. Corrections to `cpu-levers.md`

| `cpu-levers.md` said | For this consumer |
|---|---|
| A single coarse stage is the common case; tier-1 is the minority | Cascades are 63–90% of hierarchical time |
| Tier-1 "already on the fast path — nothing to fix" | Tier-1 runs **2.4–6.7× over its full-lane ideal** (§4, item 1) |
| Q15 is the largest single number (1.16–1.27×) | AVX2-only, and does not cover N = 128 — tier-0 of the dominant cascade |
| Unblock the refine with a 64×64 element (4096) | The refine is at **2048**, already an element size; the blockers are the caps and lane filling |
| Hoist `getenv` (<1%) | Measured **0%**: +200 environment variables changed nothing |

Plan items with **no value for this consumer** (still correct, just irrelevant here):
AVX2 `alt_max_n` (band 1024 never occurs at n = 2048) · the `ntmpl >= 16` cliff (≤ 0.8% of
templates) · raising caps to 2048 for tier-1 (b1 ≤ 512) · quad batching at N = 64 ·
widening cascade candidates (the autotuner lands within 0–1.8% of the best already).

## 4. Re-ranked levers

Values are end-to-end shares of single-core wall time. Each states its assumptions.

### 1. Tier-1 staging — the largest confident lever

Tier-1 runs on the pair kernel, but how survivors are fed to it is expensive. Measured on
real captured groups (T = 209), tier-1 cycles against an ideal of survivors × the full-lane
per-pair cost at b1:

| Cascade | Survivors / block | dev1 (AVX2) | Haswell (AVX2) | dev2 (AVX-512) |
|---|---|---|---|---|
| (128, 256) | 28.5–31.5 | **2.36–2.38×** | **2.44–2.61×** | 3.61–4.95× |
| (256, 512) | 3.4–4.0 | 2.98–3.06× | 4.19–6.41× | 5.99–6.72× |

With ~30 survivors per block the lanes are ~94% full, yet tier-1 is still 2.4× over ideal.
So **most of the excess is staging, not occupancy**. In `run_pairs_pb`'s `tsel` path, per
batch of `W` lanes:

- `memset` of both staging buffers (`2 × n × W × 4` bytes) before **every** batch, full or not;
- a **strided gather** of each survivor from the lane-interleaved template store
  (`src[k*W]`): one float per 32-byte (AVX2) or 64-byte (AVX-512) stride, i.e. 8× / 16× read
  amplification;
- a per-block broadcast of the data spectrum across lanes (`ebr`/`ebi`), repeated for every
  block that has survivors;
- partial lanes when survivors per block < `W` (the (256, 512) case: 21–50% occupancy).

The staging arithmetic for (128, 256) on AVX2 (~336 KB of traffic per block against ~4 µs of
kernel work) predicts ~2.6×, matching the measurement.

**Fix direction:** gather survivors from a template-major copy (contiguous, no
amplification); skip the `memset` for full batches and zero only the empty lanes otherwise;
pool survivors across the `g` blocks of one `ap_hmf_run` call into full batches with
per-lane data (the non-broadcast `efft_prod` already takes per-lane data), which also
removes the per-block broadcast.

**Value**, assuming tier-1 reaches 1.2× of ideal: **≈5% of wall on Haswell, 6% on dev1,
14% on dev2** (from the run-wide stage shares in §2; see "Combined potential" above). It grows further because cheaper
cascades will win the groups that currently lock single-tier (37% of Haswell's
hierarchical time).

### 2. Q15 — sign fix, then extend its reach

The defect (`int16_coarse.h:218`) still stands. For this consumer the kernel reaches tier-0
of single-tier (256), and tier-1 at 256 or 512. It does **not** reach N = 128, tier-0 of the
dominant (128, 256) cascade (36–38% of those calls), and it doesn't exist on AVX-512.

**Value on Haswell**, assuming the repo's 1.3–1.5× (taken as 1.4×; not measured here):
≈6% of wall as the kernel stands, ≈10% with an N = 128 variant. dev1 is similar; dev2 gets
nothing without an AVX-512 port. Fixing the sign is free. Enabling it needs accuracy
validation, and it changes relative stage costs (see the interaction note below).

### 3. Refine at n = 2048 — prototype first

The refine is 20–22% of hierarchical time on both AVX2 hosts (25–26% of each (128, 256)
call). It runs one pair at a time on the balanced path because `ap_create_pairbatch` and
`pairbatch_size` cap at 1024 — but 2048 is already an element size (64×32), so no new
codelet is needed. Survivors are ~2–5 per block, so lanes only fill if refines are **pooled
across the `g` blocks of a call** (~18–40 per call → 2–5 full AVX2 batches).

**Value** if the pair path at 2048 gives 1.5× (never measured; the pair-path gain shrinks
with N): ≈4–5% of wall on the AVX2 hosts, ≈2% on dev2. The same 2048 enablement would let
the per-block forward FFTs of a group be batched too (item 5).

### 4. Autotuner robustness under load — AVX-512 only

Real captured groups, all configs interleaved:

| Config | dev1 | Haswell | dev2 |
|---|---|---|---|
| (256) single | 1.12–1.19× | 1.02–1.03× | 1.24–1.63× |
| (128, 256) | **1.00×** | 1.00–1.04× | 1.42–1.62× |
| (256, 512) | 1.00–1.07× | **1.00–1.02×** | **1.00×** |
| (128) / (512) / (128, 512) | 2.1× / 2.2–2.4× / 1.2–1.3× | ~2.0× / 2.3× / 1.5× | 2.9–3.3× / 1.6–2.1× / 1.3–1.6× |

On AVX2 the top three configs are near-tied, so a noisy lock costs little. On AVX-512 they
are not, and dev2's autotuner, timing under load, locked single-tier (256) for these groups
— **1.24–1.63× slower** than (256, 512). Exploration overhead itself is negligible (excess
over the eventual winner: 0.0% Haswell, 0.4% dev1, 1.8% dev2). The fix is in how a winner is
judged: min-of-k or interleaved timing, so one contended sample can't decide the lock.
Aggregate on dev2 ≈2% of wall.

### 5. Forward-FFT path — small

The C work outside the kernel counters (per-block 2048-point forward FFT, 1/n scaling,
band ingest) is 8–14% of single-tier calls and 3–11% of cascade calls. Batching a group's
`g` forward transforms through the pair path needs the same 2048 enablement as item 3.
≈1.5–2.5% of wall.

### 6. Upper stage FFT length — host-dependent, small

The full-output path has no refine, so the ≥ 50% valid-fraction rule's conservatism buys
nothing there. Forcing n = 32,768 on a real 41-filter upper group: **1.18× on dev1, 1.02× on
Haswell**. ≈1.4% of wall on dev1, ~0 on the production-like host. This is what `adc3544`'s
empirical N tuning did before `90750e6` replaced it with the fixed rule. Worth reviving only
for the `corr` engine.

### Interaction to plan for

Items 1–3 change relative stage costs, and two choosers depend on them. The autotuner
re-measures, so it will follow. But `gate_for_cascade` splits the fd budget by minimising
`b0·log2 b0 + p0·b1·log2 b1 + p0·p1·n·log2 n`, which prices tier-1 as efficient as tier-0
today (it is 2.4–6.7× worse). The model's split happens to be measured-optimal today (next
section), but after the stage costs move, that should be re-checked rather than assumed.

## 5. Checked and ruled out

- **Cascade fd split** (`gate_for_cascade`'s α): swept α = 0.10–0.99 on real data on dev1 and
  Haswell. Every α meets the same fd bound. The model's pick (α = 0.80) is within 0–4% of
  the measured best; cost rises past 0.80.
- **Lazy refine ingestion** (`ap_mf_set_data` outside the counters): 0.15–0.21 ms per call,
  0.6–1.1% (dev1, clean control with the gate made unreachable).
- **Hot-path `getenv`**: +200 environment variables changed call time by +0.0% / −0.2%.
- **Overlap (30% of work)**: n = 4096 roughly breaks even on tier-0 and loses on the refine;
  splitting groups by tap count adds a forward-FFT pass per group that costs more than it
  saves at typical sub-group sizes.
- **Series window and group size** (from `cpu-levers.md` §4): no effect on dispatch.

## 6. Measurement conditions

- Instrumentation: a shim timing `filter_series`, `run_series`, and
  `correlate_series_continuous`, plus per-plan `MF_HMF_PROF` counters (converted at TSC rates
  2994.3 / 3393.6 / 2300 MHz). The kernel counters omit the forward FFT, so "outside kernels"
  is wall minus counters.
- Replays: 8 real primary-pass calls captured mid-run from the consumer (after autotuning
  settled), replayed with every config interleaved; min of 9 reps.
- Each host ran the same library and apogee builds, isolated under
  `~/pycbc-wider-cpu-benchmark-20260926/reassess-20261004/`, with HOME, caches, and the gate
  cache redirected there.
- Load: dev2 and Haswell were shared (their numbers are what a loaded machine sees); dev1
  was idle and carries the clean comparisons. dev2 replay medians are noisy (min/median
  spread up to 50%); its ratios are indicative.
- A dev2 smoke test (2 reps) suggested a 1.9 ms lazy-ingestion cost; the dev1 control
  refuted it, and it is not used here.
