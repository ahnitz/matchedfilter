# Review of optimisation rounds 1-6 (f8fe1443..a52ced2e)

Six optimisation rounds landed on main between f8fe1443 and a52ced2e, from 2026-10-29 to
2026-11-01: 40 commits from parallel AI-assisted branches, merged per round
(`perf/cpu-speedups`, `perf/round2-speedups` .. `perf/round6-speedups`). They were checked
with test subsets and short ladders (2 tops); the merge gate (`tools/gate.py`), the fleet
suites and CI were not run between rounds, and CI was red from 04b1b455 on. This page
records what was measured afterwards at production length, what was changed as a result,
and where each new constant comes from. The author's own answers to the review questions
are the source for the "chosen" entries below.

## Production-length measurements

All on dev2 (Zen 5 9950X, Radeon 8060S), `tools/ladder.py --tops 27 --segments 28
--pipeline --pure` on the test27 bank and profiles, cold cost file per run, single thread
pinned to cores 12-15, runs alternating slot order. "Steady" is the 27 segments after the
first, summed; "prep" is plan construction before the first segment.

### Rounds 1-6 together (f8fe1443 against a52ced2e)

GPU, four pairs (the first pair ran under load 12 and is left out):

| | prep | first segment | steady | fine triggers |
|---|---|---|---|---|
| f8fe1443 | 127-167 s | 19.3-22.5 s | 9.95-10.42 s | 37703-37725 |
| a52ced2e | 131-181 s | 39.9-41.8 s | 8.04-9.82 s | 37827-37828 |

Steady time fell 14% (mean 10.25 to 8.80 s); the first segment doubled (+20 s), and prep
scatters by 50 s between runs of one tree, so whole-job time did not measurably improve.
Fine triggers rose 0.3%, from the tier-0 centroids (below).

CPU, two pairs (each tree reproduced to 0.5 s):

| | prep | first segment | steady | of which fine | of which middle | whole job |
|---|---|---|---|---|---|---|
| f8fe1443 | 63.6-63.8 s | 12.6 s | 145.5 s | 112.4-112.8 s | 28.7-29.0 s | 222 s |
| a52ced2e | 80.3-80.8 s | 9.7 s | 91.8-91.9 s | 62.9-63.0 s | 26.7-26.8 s | 182 s |

Steady time fell 37% and the whole job 18%. With the centroids off, a52ced2e's steady time
is 119.2 s (below), so the kernels and batching alone cut it 18% and the centroids the rest.

### Tier-0 pair centroids, on against off (a52ced2e)

`_hierarchical._TIER0_PAIR_CENTROID = False` turns them off without a rebuild.

| | prep | first segment | steady | of which fine | whole job |
|---|---|---|---|---|---|
| GPU, off (3 runs) | 68.3-68.7 s | 9.6-10.4 s | 9.33-9.73 s | 6.82-6.94 s | 88-89 s |
| GPU, on (2 runs) | 64.1-67.2 s | 35.5-36.4 s | 9.62-9.70 s | 6.02-6.12 s | 110-113 s |
| CPU, off (2 runs) | 59.7-60.3 s | 10.6 s | 119.1-119.3 s | 89.6-90.1 s | 189-190 s |
| CPU, on (2 runs) | 80.9-81.0 s | 9.7 s | 92.1-92.3 s | 63.1-63.2 s | 183 s |

On the CPU the centroids cut the fine stage 30% and steady time 23%, for 21 s more setup
(clustering and threshold solves per plan, not kept in the cost file): the whole job is
3.5% faster, and they break even after about 21 segments. On the GPU they cut the fine
stage 12%, the asymmetric follow-ups grew by as much (1.3 to 2.3 s), steady time did not
move, and the first segment took 26 s more: a net loss. The cost model chooses them on both
devices; the choice is never played in a trial. Autotune CHAIN decisions per job grew from
126 to 335 (CPU) and 248 to 440 (GPU) with them on.

## Correctness

The merge gate on a52ced2e (dev2) passed: suite, check, settled, margin, fdr (0 off the
plan; Q15 under it in 1, 3 and 1 cases of block, window and device), repro, followups.

`tools/fdr_audit.py` never ran the centroids: its banks had one template and its chains
were pinned, and clustering needs four templates and a model-chosen chain. `--bank NT` now
audits banks of near-duplicate templates through HierarchicalFilter with the centroids on
and off. Each bank holds 16 templates in groups of four, which differ by delays within a coarse
lag, phases and chirps of up to 3 radians, all at the reference's power. Across every
profile and multi-tier default chain at n=2048 and 4096 (fd 0.01, 20,000 injections a
case), nothing is off its plan:

| | cases | off the plan | pooled dismissal, centroids off | centroids on |
|---|---|---|---|---|
| CPU, FP32 and Q15 | 216 | 0 | 0.99x, 0.94x the budget | 0.55x, 0.51x |
| GPU (device filter, two tiers) | 144 | 0 | 0.97x | 0.56x |

The centroids never dismiss more than their plan, and in 27 CPU and 15 GPU chains they
dismiss well below it, down to 0.29x. Their thresholds are solved for one conservative
retention (members' mean less half their spread), and the model's draws leave out the
`lag_pad` lags the engine also searches. That costs tier-1 work, not signals: about half
the budget goes unused, which is room for cheaper chains. The gate's fdr stage now runs
`--bank 16`.

Two limits found on the way. A bank whose templates depart from the reference profile is
off the plan with or without centroids: a spectral tilt of k^0.15 either way put both 3-20x
over the budget on power-law profiles, and k^0.4 1.7x on the inspiral profile. The gate
model assumes every template has the reference's band fractions. And strongly chirped
templates lose flat-filter SNR (a 28-radian chirp lost 4.5% of detections), so the audit's
bank tells groups apart by delays and keeps its chirps small.

## Changes made in review

- CI fixes for every failure open on a52ced2e (CPU-only runners, Python 3.14, linux-arm64,
  macOS, Metal). Three were timing-dependent decisions (autotune trials, block-size pricing,
  the timed direct refine) making two runs of one call differ; one was the direct-refine
  price reading 0 under macOS's 1 us clock step, so the direct refine never ran on Apple
  CPUs; the rest compared values bit-exactly across paths Metal compiles with fast math, or
  that macOS transforms through Accelerate.
- set_input_psd reverted (no caller, undocumented public API, unaudited, failing on
  linux-arm64). Production behaviour is unchanged.
- An AVX3 CI job: with HWY_AVX3_DL enabled, an AVX-512 runner's widest job runs AVX3_DL, so
  plain AVX3 had no coverage. AVX3_DL itself is covered only on runners that have it, and
  every merge gate on dev2.
- `tools/fdr_audit.py --bank`.

## Constants and their origin

Measured means swept on named hardware; derived means it follows from arithmetic on a
property the code reads; chosen means picked by hand and not swept.

| Constant | Where | Origin |
|---|---|---|
| 4-template middle batch (`kt_step = 4`) for n in [2048, 4096], `p->w >= 16` | src/matchfilt.c (2e5d1077, b4c53a34) | n bounds and width measured on dev2 Zen 5, su2 Haswell and Ivy Bridge; the `9 * spec_bytes <= 7/8 * L2` guard derived from footprint |
| Non-temporal stores above LLC / 2 (was 3/4) | src/matchfilt.c (b4c53a34) | chosen; measured only as part of b4c53a34 |
| Forward pair-batches at 1k/2k on 16-lane SIMD, later 8-lane with Q15 and 4-lane on aarch64 | src/hmf.c (a9ce9327, 666e0196, 49eb4586) | measured on dev2, su2 and an M2 |
| Sparse Q15 at `nfire >= ql/2 + 1` | src/hmf.c (aa2e481d) | derived from lane counts (where FP32 needs a second batch); the crossover not swept |
| Series slab 512 KB (dgroup 32 at n=2048) | src/hmf.c (5ace882a, 304c5e8d) | measured on dev2 and 256 KB-L2 Xeons |
| Centroid alpha `floor((mean - 0.5 sd) * 50) / 50` | gatechain.py (fe86f0ed) | chosen (cache-key quantisation and a conservative margin) |
| Centroid ratio rounded to 0.05 | gatechain.py (fe86f0ed) | chosen |
| Centroid matching: 48-template chunks, top-8 candidates | gatechain.py (5d02d1e3, 3f5fd63b) | chosen from L2 footprint, timed on dev2 only |
| Pass-2 merge floor `max(0.84, rho_min - 0.05)`, alpha floor `0.88-0.93` | gatechain.py (88781d6e) | chosen |
| Direct-refine price rounds of 100,000 ticks | src/hmf.c (review) | derived: puts a 1 us clock step under 1% of a round |

## Follow-up: the centroids' setup and their unused budget (2026-11-02)

### Setup

Where the CPU job's 21 s of centroid setup went (cProfile, test27, 27 tops): the pair scorer
in `cluster_tier0_candidates`, a plain C loop built for the SSE4 baseline, 12.4 s; the
rest of the clustering 6 s; and half of all clusterings were of band 512 at n=2048, which
no plan chose.

- The scorer is a Highway kernel (src/tier0.cc): a 48-template chunk 1.28 -> 0.23 ms on
  dev2 (AVX-512), 0.38 ms with AVX2, 0.82 ms with SSE4; same scores and winning shifts.
- A band is admitted by a bound at the k <= 4 floor (ratio 0.25); band 512 passed it (47.7
  against a winner of 51.7) and then cost 79-89. Pass 2 merges pairs of Pass-1 centroids,
  so after Pass 1 the k <= 4 bank's ratio is at least half the Pass-1 one (0.30 there,
  bound 57): Pass 2, and pricing any candidate whose own ratio's bound cannot win, are
  skipped. The bounds price only the chains from that band (`choose_chain(first=b)`).

Production length (dev2, two runs an arm, slot order rotating, one session):

| | main (583e730f) | with these | centroids off |
|---|---|---|---|
| CPU prep | 80.8-81.4 s | 68.3-68.6 s | 60.4-60.5 s |
| CPU steady | 91.4-92.1 s | 91.5-91.9 s | 118.2-118.4 s |
| CPU whole job | 182-183 s | 169-170 s | 189 s |
| GPU first segment | 35.6 s | 22.2-23.3 s | 9.7-10.8 s |
| GPU whole job | 109-110 s | 97-99 s | 88-98 s |

On the CPU the centroids now cost 8 s of setup instead of 21 s, and the job is 10% faster
than without them (3.5% before). Fine triggers are unchanged (37823-37828, the scatter of
runs with live trials).

### Budget

The centroids' plans leave budget unused: 0.55x pooled on the audit's banks. Most of it
is the retention the thresholds are solved for. On the audit bank where it was largest
(skewed_edge, 256,1024) the plan's alpha of 0.98 lowered tier 0's threshold from 5.19 to
4.94 while the engine met its signals almost unattenuated: its dismissal at those
thresholds, 0.0022, is an alpha-1 model's (0.0020). Two parts:

- Members' retentions were each one's overlap at the lag it was aligned at when the
  centroid was built; the engine takes the largest statistic over its padded lags, where a
  blended centroid peaks elsewhere. They are now the peak over the reachable lags: never
  lower, the audit's under-plan chains 27 -> 9, none off, and on test27 six of 120
  clusterings' alpha rose from 0.96 to 0.98.
- The rule collapsing members to one alpha (mean less half the spread, floored to 0.02) is
  the rest. On test27, at each plan's thresholds, the plans dismiss 1.00x their budget at
  their own alpha, 0.76x (0.47-1.06x) under the mixture of their members' retentions, 0.43x
  at alpha 1. The member mean instead (floored to 0.01) cut the fine stage 3% and steady
  time 2.6%, but put some plans at 1.20x under the mixture: not a bound, so not kept.
  Thresholds solved against the members' mixture would meet the budget on average by
  construction. That needs either the simulation to draw a retention per row (what
  set_input_psd's `M_simulate` change did) or one simulation per retention bin (estimated
  15-30 s of setup per job here, for about 2.4 s of steady time): not done.

## Open

- The rest of the centroids' setup (8 s on the CPU, 13 s on the GPU), and the CHAIN decision count with them on.
- The GPU's centroid choice: priced as a gain, a whole-job loss (about 9 s a job on dev2). It should be a
  trial arm, or the GPU price should count the follow-ups it adds.
- Heterogeneous banks against the single-profile gate model, which set_input_psd was
  meant to address. How far production banks' leaves depart from their reference is not
  measured.
- Thresholds solved against the members' mixture of retentions (above).
- Metal rounds a device follow-up batch and the same call alone apart by a few ulp (fast
  math, different kernels); the tests now compare values to 1e-6.
