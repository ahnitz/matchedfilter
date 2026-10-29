# The forward a chain's calls take, measured per device (2026-10-29)

The cost model priced a GPU chain's forward from a fit: the band forward at widest band B as
`forward * (1/2 + B/2n)` (one point, 0.74 measured against 0.75 on the 8060S), plus `f *
forward` of recompute at a refine-block fraction f measured by earlier calls and averaged with
weight 1/2 (`note_refine_blocks`). `forward` was `block`, the per-block cost the calibration
measured with the band forward of the first tier's band. All three were wrong in the same
direction. Timed on the 8060S at n = 2048, the full forward costs 58.7 per block more than
that head (`block` 48.7), the band forward 3.4 to 10.9 more from B = 128 to 1024. And the
calibration's refine term, measured on band-fed calls, already holds the recompute it then
added a second time.

Now the GPU calibration times the feeds in the same rounds as the head: the chain (b0, B) at
a threshold nothing passes runs what the head runs but for its forward, the band forward at B;
the head with the full forward forced (a context's `feed_forced`) is the full feed. A first
tier priced alone (`dense[b]`) no longer carries the band forward at b. The model takes, per
chain, the feed the backend takes (`gatechain.band_forward_wanted` on the chain's modelled refine
probability, what the call itself reads), so nothing a call measured enters a choice. Deleted:
`forward_cost`, `note_refine_blocks`, `measured_refine_blocks` and its running mean,
`refine_block_fraction`, and `model_f` (the proposal-only credit at the model's fraction).

| test27 ladder, 8060S, 27 tops x 28 segments, fresh cost files | steady wall (s), 3 runs | mean |
|---|---|---|
| before (05e96062) | 10.53, 9.89, 9.74 | 10.05 |
| measured feeds | 10.12, 9.18, 9.63 | 9.64 (0.96x; fine stage 0.94x) |

Paired by run, the new pricing was faster in each (0.961, 0.928, 0.989; load 2-4). The chain
choices moved in 4 of 174 n = 2048 plans, to (256,). The calibration takes 0.0-0.35 s longer
per transform size (8.3 against 8.2 s at n = 2048, 6.1 against 5.7 at 4096, two runs each
under load).

# One false-dismissal budget per plan, 2026-10-29

Every number that steered a plan's dismissal now traces to fd and one stated per-plan
tolerance, roadmap decision D1: plans dismiss fd on average (pooled within 2% on 16M
check draws), at most 5% of plans dismiss more than 1.25 fd, and no more draws than
before. Gone:

- `_SPLIT_TOLERANCE_Z`, the 0.75 cut for the split search's selection bias. It left
  multi-tier plans at 0.95-0.98 of fd when priced by the operation count. Priced by a
  machine's costs, the bias it was cut for is larger (below: the CPU plans dismissed 1.04
  of fd by their tiers at n = 2048).
- `_LOCALISE_SHARE`, 5% of fd the direct refine's window could miss on top of the
  budget, and the plan's extra coarse sample of window.
- The draw count 200/fd with its 20,000 floor and 3,000,000 cap, `_GROW` (the 4x cap on
  the simulation at a large snr), and the `K < 8` refusals.
- The finer split grid, `gatechain.direct_halfwidth`, and the per-band direct prices built
  from single-tier plans.

## The construction

The model's detections (draws whose fine window maximum reaches snr) fall into two
independent halves, the even and the odd ones (`gatechain._halves`).

- **The search half decides the structure** (`plan_chain`, `_chain_candidates`). It tries
  every split of its budget of K = round(fd (M + 1)) - 1 dismissed detections between the
  tiers. Where the cost model prices a direct refine, it also tries every half-width at
  which a different set of the detections falls outside the window (`_halfwidths`), the
  window's misses counted against the same K. The cheapest candidate wins. Every choice
  among plans ranks the searched plans: the chain `choose_chain` picks, its tie-break, the
  block size `price_block_sizes` picks and the model's screen setting.
- **The fit half sets the thresholds** (`_fit`). It moves every tier of the searched
  thresholds by one shift s, the j-th smallest over the fit half of the shift at which
  each detection is first dismissed. A detection the window misses is dismissed at any
  shift. So j - 1 of the fit half are dismissed.

Given the search half, the fit half is independent of everything chosen from it, and the
shift's score is continuous. So a plan's dismissal on fresh draws is the j-th smallest of
M uniforms: mean j / (M + 1), and above r fd with probability P(Binomial(M, r fd) <= j - 1)
(`gatemodel.plan_tail`). The draw count follows: M + 1 = round(j / fd) per half, j the
smallest with P(plan > 1.25 fd) <= 5% (`gatemodel.fit_order`). The model draws
2 (round(j / fd) - 1) detections (`gatemodel._nsamp_for`), and the simulation runs until it
holds them. It is extended in place for a larger request: a row's draws, its arrival
included, depend only on its row.

| fd | j | P(plan > 1.25 fd) | detections | draws at snr 5.5 (fdr_audit profiles) | before (200/fd, floor 20,000) |
|---|---|---|---|---|---|
| 5e-2 | 45 | 0.0498 | 1,798 | about 3,100 | 20,000 |
| 1e-2 | 47 | 0.0500 | 9,398 | 14,700-19,200, median 16,500 | 20,000 |
| 1e-3 | 48 | 0.0491 | 95,998 | 149,000-194,000, median 167,000 | 200,000 |
| 1e-4 | 48 | 0.0492 | 959,998 | about 1.67M | 2,000,000 |

A budget whose tail bound needs more than `_MAX_DETECTIONS` refuses: 1.75M, the
detections the old 3M-draw cap held, about 0.7-0.9 GB of records. That is fd below 5.5e-5.
Before, fd from 4.6e-6 to 5.5e-5 ran on 8-96 dismissed draws (a per-plan sd of 0.10-0.33
of fd).

The cost is the per-plan spread. Each plan rests on half the draws, so its sd is about
fd / sqrt(j) = 0.14 fd. Before, it was 0.09 at fd 1e-2 and 1e-3, and 0.04 at 5e-2, where
the floor gave K about 580, about a mean that was off target. Now 5% of plans exceed
1.25 fd, as D1 allows. Keeping the old spread at fd 1e-3 would take j about 115 per half:
2.4 times today's detections, twice the old draw count. D1 does not ask for it.

The split grid is `_SPLIT`, 9 shares. A search on 19 shares (19 x 19 for three tiers) gave
fitted plans whose modelled cost is within 0.05% of the 9-share grid's on average over
every given chain, and within 0.4 ± 0.3% for the pick. That was 5 profiles x 10 model
seeds, n = 2048 and 4096, fd 1e-3, Zen 5 costs, with and without a direct refine. The fit
moves every tier's threshold, so the split's fine structure matters little.

### The direct refine's window

The direct refine finds a detection's fine peak iff the peak lies within the half-width of
the last tier's coarse maximum (`_distances`). The positions come from `signal_draws(...,
lags_too=True)`, which now reports them as block lags, as `hmf.c` compares them. Its
misses are dismissals, so a cheaper refine buys a smaller tier share of the budget. The
cost model prices the window per lag (`CostModel.with_direct(ticks per lag)`,
`HierarchicalFilter._direct_price`). The model counts a fine peak outside the window as
missed. The engine is never worse: a window whose maximum lies on its edge takes the
transform (`refine_direct_pair`), so its misses are a subset of the model's.

The fit cannot move a whole-number window, so the window's misses are fixed by the search.
Where they alone reach j on the fit half, the plan refines by transform and the tiers take
the whole budget. That branch is chosen on the fit half, so it is not covered by the fit's
exactness. Nor was it rare where it mattered: the search could spend the whole budget on a
window, chosen where its misses on the search half just fit. Run once without a limit
(n = 2048, fd 1e-2, Zen 5 costs, 256 taps), every one of the 17 plans (of 7,500) whose
window took over 0.9 of the search half's budget fell back, and they dismissed 1.14 fd on
average (18% of them above 1.25 fd).

`gatemodel.window_allowance` closes it. A window is offered only where the predictive
probability of the branch is at most the share of the tail bound the fit leaves,
`_TAIL_SHARE - plan_tail(fd, M)`. The predictive probability is the BetaBinomial(M,
m + 1/2, M - m + 1/2) chance that the window misses j of M fresh detections, given that
it misses m of the search half: the binomial under the Jeffreys posterior of its miss
rate. A plan then exceeds 1.25 fd with probability at most 5%, the branch included, and
its mean moves by at most that probability (at most 0.002) times the branch's dismissal.

| fd | the fit's tail | room | allowance (of K) |
|---|---|---|---|
| 1e-1 | 0.0487 | 0.0013 | 19 of 42 |
| 5e-2 | 0.0498 | 0.0002 | 17 of 44 |
| 1e-2 | 0.0500 | 0.00003 | 15 of 46 |
| 1e-3 | 0.0491 | 0.0009 | 21 of 47 |
| 1e-4 | 0.0492 | 0.0008 | 21 of 47 |

The room depends on how close fit_order's whole j lands to 5%, so the allowance moves a
little with fd. The chosen chains' windows never come near it. Their windows take at most
0.11-0.30 of the search half's budget, and 3-7% of their realised dismissals. Of every
chain's plans, 45-48% take a window, missing 5-11% of their dismissals. After the change,
no plan in the measurement below fell back.

The noise blocks are the simulation's first 20,000 rows' noise (`_NOISE_BLOCKS`), and the
search's costs read them. So where those rows hold the fit half's detections, the fit half
is not strictly independent of the structure. At fd 1e-2 that is every detection. Measured
with noise blocks from an independent simulation instead (n = 4096, fd 1e-2, Zen 5 costs,
256 taps), every chain's plans dismissed 1.000 ± 0.005 of fd (shared noise: 0.999) and
the picks 1.006 ± 0.008 (1.013 ± 0.008). The difference is within its error, so the
noise blocks stay free.

A pinned chain runs without the Q15 screen (`_arm_q15`), and its thresholds are now priced
that way (`CostModel.unscreened`). A pinned one-tier chain's tier then reports its lag, so
its window is priced; before, the model priced a screen that never ran.

## Measured

`tools/split_bias.py` at 5f8fcd84, dev2, cores 22-27, GPU hidden, load 5-15. The setup:

- the 10 `fdr_audit` profiles, snr 5.5, window 3n/32..n - 3n/32;
- 30 model seeds per profile;
- per profile, 4M independent check detections at fd 1e-2 and 16M at 1e-3;
- every chain of one to three usable bands, plus the pick (choose_chain's rule, run with
  that chain's chain_thresholds plan);
- priced by the operation count, or by the Zen 5 cost file with a 256-tap direct refine
  (`--cost`, `--taps`).

"se" is the standard error of the mean: the model's part from the seed-to-seed scatter of
each profile's mean, and the check's part. D1's tail is the share of plans above 1.25 fd;
fit_order's own is 0.050 at 1e-2 and 0.049 at 1e-3.

| n | fd | priced by | every chain's plans | mean ± se | sd | > 1.25 fd | worst | picks: mean ± se | > 1.25 fd |
|---|---|---|---|---|---|---|---|---|---|
| 2048 | 1e-2 | operation count | 7500 | 0.999 ± 0.005 | 0.140 | 0.041 | 1.53 | 0.998 ± 0.008 | 0.043 |
| 2048 | 1e-3 | operation count | 7500 | 1.005 ± 0.005 | 0.143 | 0.053 | 1.59 | 1.006 ± 0.008 | 0.057 |
| 4096 | 1e-2 | operation count | 12300 | 1.000 ± 0.005 | 0.147 | 0.050 | 1.66 | 1.006 ± 0.008 | 0.037 |
| 4096 | 1e-3 | operation count | 12300 | 0.998 ± 0.005 | 0.144 | 0.050 | 1.65 | 0.996 ± 0.009 | 0.047 |
| 2048 | 1e-2 | Zen 5, 256-tap direct refine | 7500 | 1.000 ± 0.005 | 0.139 | 0.043 | 1.53 | 1.001 ± 0.008 | 0.043 |
| 2048 | 1e-3 | Zen 5, 256-tap direct refine | 7500 | 1.005 ± 0.005 | 0.144 | 0.055 | 1.64 | 1.006 ± 0.009 | 0.057 |
| 4096 | 1e-2 | Zen 5, 256-tap direct refine | 12300 | 0.999 ± 0.005 | 0.146 | 0.050 | 1.66 | 1.013 ± 0.008 | 0.037 |
| 4096 | 1e-3 | Zen 5, 256-tap direct refine | 12300 | 0.997 ± 0.005 | 0.143 | 0.048 | 1.65 | 1.000 ± 0.009 | 0.050 |

By tier count, every chain's plans average 0.996-1.006 of fd. The picks, 47-167 plans per
tier count, average 0.969-1.025, within 1.8 of their standard errors (0.011-0.025). The
operation-count rows reproduce b892cf60's run (before the window allowance) row for row,
15,600 of 15,600 at n = 2048 and 25,200 of 25,200 at 4096: a plan without a window does
not change.

The tail shares are 0.037-0.057. Plans made from one simulation share its fit half, so the
share's error is that of about 300 independent plans, ± 0.013. Grouped by the window's
share of the search half's budget, a grouping made before the fit, every group's mean lies
within 2.3% of fd:

| n | fd | window's share | plans (tiers) | mean ± se (plans as independent) | > 1.25 fd | refined by transform |
|---|---|---|---|---|---|---|
| 2048 | 1e-2 | none | 4015 (tiers 1,2,3) | 1.008 ± 0.002 | 0.048 | 0 |
| 2048 | 1e-2 | (0.00, 0.25] | 2050 (tiers 2,3) | 0.997 ± 0.003 | 0.038 | 0 |
| 2048 | 1e-2 | (0.25, 0.50] | 163 (tiers 2,3) | 0.994 ± 0.010 | 0.049 | 0 |
| 2048 | 1e-3 | none | 4268 (tiers 1,2,3) | 1.007 ± 0.002 | 0.049 | 0 |
| 2048 | 1e-3 | (0.00, 0.25] | 2292 (tiers 2,3) | 1.002 ± 0.003 | 0.061 | 0 |
| 2048 | 1e-3 | (0.25, 0.50] | 206 (tiers 2,3) | 0.996 ± 0.010 | 0.053 | 0 |
| 4096 | 1e-2 | none | 6549 (tiers 1,2,3) | 0.995 ± 0.002 | 0.045 | 0 |
| 4096 | 1e-2 | (0.00, 0.25] | 3531 (tiers 1,2,3) | 1.008 ± 0.002 | 0.056 | 0 |
| 4096 | 1e-2 | (0.25, 0.50] | 149 (tiers 1,2,3) | 1.023 ± 0.013 | 0.101 | 0 |
| 4096 | 1e-3 | none | 6825 (tiers 1,2,3) | 0.995 ± 0.002 | 0.043 | 0 |
| 4096 | 1e-3 | (0.00, 0.25] | 3680 (tiers 1,2,3) | 0.996 ± 0.002 | 0.051 | 0 |
| 4096 | 1e-3 | (0.25, 0.50] | 674 (tiers 1,2,3) | 1.007 ± 0.005 | 0.049 | 0 |

One group stands out: windows taking 0.25-0.50 of the budget at n = 4096 and fd 1e-2, with
10% of 149 plans above 1.25 fd. Its plans come from 67 simulations. Over those, the mean is
1.018 ± 0.018 and the share above 1.25 fd 0.080 ± 0.027, which agrees with 0.05. With
independent noise blocks (above) the same group gave 1.023 and 0.088.

## End to end

`tools/fdr_audit.py --n 2048 4096 --q15 --inj 20000` (fd 1e-2, snr 5.5, 10 profiles x 4
chains, each against the plan's own modelled dismissal on independent model detections,
two-sided):

- Whole block: 0 of 150 cases off their plan. Pooled, fp32 chains miss 1.036 ± 0.011 of
  the budget and Q15 chains 0.965; 1 Q15 case is under its plan, reported and not failed.
- Window 192..1856: 0 of 150 off their plan. Pooled, fp32 0.998 ± 0.011 and Q15 0.920; 3
  Q15 cases are under their plans.

The binomial error leaves out the plans' own scatter, 0.14 fd each. All of fdr_audit's
plans come from the gate model's one seed, so the pooled means carry that seed's luck.

## What the production plans dismissed, and what meeting fd costs

Before, the CPU's plans exceeded the budget. HierarchicalFilter's own flow was run at the
model seeds 1001-1030 (bench_setup's hier mode): FIR taps, the direct refine, dev2 costs,
fd 1e-3, snr 5.5, the O2 reference at n = 2048 and the inspiral profile at 4096. Each plan
was judged on 2M independent detections, and costed with one cost model on one 200,000-
block noise sample:

| n | before: dismissal (tiers) | after | modelled cost, after / before |
|---|---|---|---|
| 2048 | 1.079 ± 0.012 (1.044) | 1.017 ± 0.022 (0.943) | 1.022 ± 0.007 |
| 4096 | 1.021 ± 0.015 (0.971) | 0.983 ± 0.032 (0.782) | 0.920 ± 0.009 |

Before, the tiers alone dismissed 1.044 fd at n = 2048 (0.971 at 4096), and the window
added 3.5-5%. z 0.75 was measured on plans priced by the operation count. Priced by a
machine's costs, the split search selected more here than z cut.

The ladder (`tools/ladder.py`, test27's `fir_three_level_modern_v1_bottomup_cap401` bank,
`--tops 1 --segments 8`, CPU), throughput after / before:

- dev1 (Zen 3), paired `ab_ladder.py`, 6 rounds at the production model seed, load 1:
  0.983 batched and 0.981 pipelined. Every batched round was lower, by 0.2-2.4%.
- dev1, 8 model seeds (seed injected into the simulations), two runs per tree per seed in
  ABBA order on two cores, load 3-12: median 0.976, mean 0.986 ± 0.021, range
  0.919-1.116. The 0.919 is a seed whose plan for one window took chain (256, 512) at a
  refine reach of 0.0085. Both trees rank (256, 512) first at every seed, within the 5%
  tie that otherwise keeps (256, 512, 1024): a cost-model question, not this change's.
- dev2 (Zen 5), paired `ab_ladder.py` under load 14-52 (at b892cf60): 0.922 batched and
  1.018 pipelined, rounds spreading 5.7e6-1.0e7.
- dev1, the 8 seeds run concurrently, both trees side by side on 8 cores: 0.705-0.994,
  median 0.878. Confounded, not a measurement of this change. The middle stage, which
  the change does not touch, ran 8-57% slower in the new tree too (median 30%). Its
  shorter setup put its steady segments under the old tree's setup on the neighbouring
  cores.
- dev2 (Zen 5), production seed, sequential runs, load 8: 1.064e7 and 1.039e7 before,
  1.008e7 and 0.995e7 after. The fine stage took 1.63-1.66 s and 1.73-1.75 s.
  Accounting: the n = 2048 window 192..1856 plan's tier-2 and tier-3 thresholds fell from
  4.81 and 5.49 to 4.68 and 5.35, and its refine reach rose from 2.0e-4 to 4.5e-4. The
  direct refine took 956 pairs and 12,428 lags in place of 580 and 9,860. That is one
  plan's draw from its 0.14 spread.
- The ladder's plans, judged on 2M independent detections of their captured reference
  profiles (8 seeds): window 192..1856 before 1.029 ± 0.034, after 0.997 ± 0.041; window
  128..1920 before 1.032 ± 0.032, after 0.972 ± 0.040.

Meeting the budget where the plans exceeded it costs about 1.5-2.5% of the CPU ladder's
throughput on this bank. A caller who wants the old throughput can set a larger fd.

## Setup

The model's decision setup in a fresh process at fd 1e-3 (bench_setup.py: choose_chain
with a cost file; HierarchicalFilter._resolve with FIR taps), paired by repeat, 5 repeats,
after / before:

| host | load | choose_chain 2048 | 4096 | HierarchicalFilter 2048 | 4096 |
|---|---|---|---|---|---|
| dev2, core 21 | 6-8 | 1.147 -> 0.785 s (0.685) | 2.136 -> 1.491 s (0.697) | 1.173 -> 0.833 s (0.710) | 2.182 -> 1.588 s (0.725) |
| dev2, core 21 (at b892cf60) | 15-17 | 2.008 -> 1.047 s (0.506) | 3.440 -> 1.942 s (0.568) | 1.965 -> 1.101 s (0.564) | 3.371 -> 2.086 s (0.619) |
| dev1, core 4 (at b892cf60) | 1-2 | 2.169 -> 1.482 s (0.693) | 4.121 -> 2.954 s (0.709) | 2.253 -> 1.555 s (0.708) | 4.200 -> 2.975 s (0.699) |

The changes that remove work:

- fewer draws;
- the noise alone recorded only for the model's 20,000 noise blocks (a third of a row's
  simulation);
- one split grid;
- no single-tier plans per band to price the direct refine.

## Tests

What changed in the tests, and why none is a fitted margin:

- `test_gate_model.test_quantile_placement_uses_the_conditional_distribution`: the gate
  is the fit half's j-th smallest coarse maximum, exactly. It was the floor(fd M)-th of
  all kept draws.
- `test_gate_model.test_the_tail_and_the_window_allowance_are_their_distributions`
  (new): plan_tail and window_allowance against scipy's binomial and beta-binomial,
  including that one more miss would break the room.
- `test_gate_chain.test_plan_chain_matches_the_plain_split_search`: the plain search,
  now on the search half, plus the shift fit on the other. Thresholds, reach and cost
  are equal exactly.
- `test_direct_refine.test_halfwidth_shares_the_budget` (was
  `test_halfwidth_from_the_model`). On the fit half, tier dismissals and window misses
  together are exactly j - 1. The window's misses on the search half are its plan's and
  within the allowance. A plan with a window dismisses less by its tiers than the same
  chain without one.
- `test_direct_refine.test_a_plans_window_misses_no_more_than_the_allowance` and
  `test_windows_miss_no_more_than_the_allowance` (new). On an f^-1 profile, a one-tier
  chain at band 1024 searched against the whole budget takes a window missing 31 of
  4,699; the test fails on that break (allowance 15). `_halfwidths` starts at the
  smallest window within the allowance.
- `test_gate_draws`: the C search equals the Python one with window sets. `signal_draws`
  holds exactly the detections asked for, a smaller request is a larger one's prefix in
  any order, and its maxima lie where the engine searches.
- `test_fdr_calibration`: the engine and the true coarse statistic are tested two-sided
  against the plan's own modelled dismissal on 200,000 independent model detections
  (seed 977), not against fd. The plan's own scatter (0.14 fd) would otherwise dominate
  the binomial counts. The budget claim is a new test,
  `test_plans_dismiss_the_budget_on_average`: 100 model seeds per profile, every chain's
  plan and the pick judged on 1M independent detections. Their means are within 3.5
  standard errors of fd, and the share above 1.25 fd within 3.5 of fit_order's, both
  over simulations, since one simulation's plans share a fit half. It fails on the
  deliberate break of fitting on the search half: multi-tier plans then dismiss 1.087
  and 1.055 of fd, 8.3 and 4.8 standard errors.
- `tools/fdr_audit.py` tests each case against its plan's modelled dismissal: a
  two-sample binomial against max(1M, 10 x injections) model detections. It reports the
  pooled misses over the budget.

No threshold, tolerance or seed was chosen to make a test pass:

- every exact test compares two computations of one order statistic or distribution;
- the statistical tests use the binomial counts and standard errors the construction
  states.

Thresholds change everywhere: the new fit, the new draw count, and the window inside the
budget. No golden in the repository stores thresholds. A recorded `tools/unify_golden.py`
directory does, so re-record it.

# The split bias does not depend on fd, and the cut is twice its size, 2026-10-27

The entry below left one question open: at fd 1e-3 multi-tier plans dismissed 0.95 and
0.96 of the budget, at 1e-2 0.99 and 1.01, from one model seed and one check seed.
Measured again with 30 independent model seeds per profile and large independent
checks, the selection bias is the same at fd 1e-2 and 1e-3, at n = 2048 and 4096. The
difference was one seed's luck.

The bias is about half the size 3390d4f3 measured, though. With no cut, two-tier plans
dismiss 1.02-1.03 of the budget and three-tier plans 1.03-1.04, not 1.050 and 1.085. At
`_SPLIT_TOLERANCE_Z = 0.75` they dismiss 0.95-0.97 of the budget, not 1.0. The 3390d4f3
no-cut numbers reproduce exactly at its seeds, and its model seed (13, the gate model's
own) sat about one standard deviation high (below). z stays 0.75 here: the value is a
separate decision (the last paragraph).

Method (`tools/split_bias.py`, at d285f692 on dev2, one process per core on cores 24-31,
GPU hidden, load 4-14; fd 1e-2 and 1e-3 ran as its scratch predecessor, whose rows the
tool reproduces exactly: 3120 of 3120 for f^0 at fd 1e-2, n = 2048):

- Profiles: `tools/fdr_audit.default_profiles()` (10), snr 5.5, window 3n/32..n - 3n/32
  (192..1856 at n = 2048, 384..3712 at 4096).
- Plans: every chain of one to three usable bands (25 at n = 2048, 41 at 4096), with
  thresholds from `gatechain.plan_chain` as `chain_thresholds` makes them with no cost
  model, at z = 0, 0.5, 0.75 and 1. Also the chain `choose_chain` picks with no cost
  model (the operation count): its own selection among chains adds to the bias.
- Model draws: 30 simulations per profile, each with its own seed, at the model's draw
  counts (`gatechain.model_draws`). K, the dismissed count, is 100-131 at fd 1e-2 and
  1e-3 (mean 115) and 526-646 at 0.05, where the 20k-draw floor of
  `gatemodel._nsamp_for` holds.
- Check draws: per profile, its own independent `signal_draws`. 4M draws at fd 1e-2 and
  0.05 (2.1-2.6M kept) and 16M at 1e-3 (8.4-10.4M kept, about 9,000 dismissed).
- Standard errors of a mean: the model's part from the seed-to-seed scatter of each
  profile's mean; the check's part bounded as if every plan of a profile shared one
  check error.

Mean realised dismissal over fd, every chain's plan:

| n | fd | 1 tier | 2 tiers, no cut | 3 tiers, no cut | 2 tiers, z 0.75 | 3 tiers, z 0.75 | mean on budget at z (2 / 3 tiers) |
|---|---|---|---|---|---|---|---|
| 2048 | 1e-2 | 1.007 ± 0.003 | 1.025 ± 0.004 | 1.037 ± 0.004 | 0.957 ± 0.004 | 0.967 ± 0.004 | 0.28 / 0.40 |
| 2048 | 1e-3 | 1.003 ± 0.004 | 1.024 ± 0.004 | 1.035 ± 0.005 | 0.954 ± 0.004 | 0.966 ± 0.005 | 0.26 / 0.38 |
| 4096 | 1e-2 | 1.006 ± 0.003 | 1.028 ± 0.004 | 1.042 ± 0.004 | 0.959 ± 0.004 | 0.972 ± 0.004 | 0.30 / 0.44 |
| 4096 | 1e-3 | 1.006 ± 0.004 | 1.025 ± 0.004 | 1.034 ± 0.005 | 0.955 ± 0.004 | 0.964 ± 0.004 | 0.27 / 0.37 |
| 2048 | 5e-2 | 1.002 ± 0.002 | 1.008 ± 0.002 | 1.011 ± 0.002 | 0.977 ± 0.002 | 0.981 ± 0.002 | 0.20 / 0.27 |

The z columns are interpolated between the measured z values, ± 0.04-0.05. The
difference between fd 1e-3 and 1e-2 at z 0.75 is -0.003 ± 0.006 (two tiers) and
-0.002 ± 0.006 (three) at n = 2048, and -0.004 ± 0.005 and -0.008 ± 0.006 at 4096. Every
subset of chains gives the same picture: at fd 1e-2 and n = 2048 the 20 multi-tier chains
range from 0.945 to 0.980 at z 0.75. At fd 0.05, where K is five times larger, the bias
in standard errors may be a little smaller (0.20 and 0.27 against 0.26-0.30 and
0.37-0.44). That is 1 to 2.5 standard errors of the difference, and below 1% of the
budget.

The chain `choose_chain` picks, multi-tier picks only (the single-tier picks dismiss
0.99-1.02 of the budget):

| n | fd | multi-tier picks | no cut | z 0.5 | z 0.75 | all picks, z 0.75 | mean on budget at z |
|---|---|---|---|---|---|---|---|
| 2048 | 1e-2 | 214 of 300 | 1.050 ± 0.007 | 1.005 ± 0.007 | 0.979 ± 0.007 | 0.988 ± 0.006 | 0.54 |
| 2048 | 1e-3 | 231 of 300 | 1.042 ± 0.006 | 0.997 ± 0.006 | 0.975 ± 0.006 | 0.983 ± 0.005 | 0.47 |
| 4096 | 1e-2 | 214 of 300 | 1.049 ± 0.007 | 1.004 ± 0.006 | 0.983 ± 0.006 | 0.993 ± 0.005 | 0.55 |
| 4096 | 1e-3 | 230 of 300 | 1.034 ± 0.006 | 0.988 ± 0.005 | 0.963 ± 0.005 | 0.969 ± 0.005 | 0.37 |
| 2048 | 5e-2 | 205 of 300 | 1.013 ± 0.003 | 0.992 ± 0.003 | 0.981 ± 0.003 | 0.990 ± 0.002 | 0.30 |

Per-plan scatter at z 0.75 (the worst plan carries its check's binomial sd; "one seed's
worst" is the mean over seeds of the worst plan made from one seed per profile; the
worst pair is the (profile, chain) with the largest mean over its 30 seeds):

| n | fd | tiers | plans | sd ± se | check sd | worst plan | one seed's worst (of) | worst pair |
|---|---|---|---|---|---|---|---|---|
| 2048 | 1e-2 | 1 | 1500 | 0.093 ± 0.002 | 0.007 | 1.335 ± 0.008 | 1.224 ± 0.008 (50) | 1.051 ± 0.017 |
| 2048 | 1e-2 | 2 | 3000 | 0.091 ± 0.002 | 0.006 | 1.279 ± 0.007 | 1.188 ± 0.008 (100) | 1.007 ± 0.014 |
| 2048 | 1e-2 | 3 | 3000 | 0.092 ± 0.003 | 0.006 | 1.348 ± 0.008 | 1.191 ± 0.010 (100) | 1.039 ± 0.019 |
| 2048 | 1e-3 | 1 | 1500 | 0.090 ± 0.002 | 0.010 | 1.329 ± 0.012 | 1.217 ± 0.009 (50) | 1.042 ± 0.014 |
| 2048 | 1e-3 | 2 | 3000 | 0.088 ± 0.002 | 0.010 | 1.258 ± 0.012 | 1.173 ± 0.008 (100) | 0.997 ± 0.017 |
| 2048 | 1e-3 | 3 | 3000 | 0.088 ± 0.002 | 0.010 | 1.278 ± 0.012 | 1.172 ± 0.009 (100) | 1.022 ± 0.017 |
| 4096 | 1e-2 | 1 | 1800 | 0.092 ± 0.002 | 0.007 | 1.322 ± 0.007 | 1.235 ± 0.009 (60) | 1.057 ± 0.017 |
| 4096 | 1e-2 | 2 | 4500 | 0.092 ± 0.002 | 0.006 | 1.315 ± 0.007 | 1.193 ± 0.010 (150) | 1.037 ± 0.015 |
| 4096 | 1e-2 | 3 | 6000 | 0.092 ± 0.002 | 0.006 | 1.321 ± 0.007 | 1.213 ± 0.009 (200) | 1.071 ± 0.015 |
| 4096 | 1e-3 | 1 | 1800 | 0.092 ± 0.001 | 0.010 | 1.410 ± 0.012 | 1.231 ± 0.010 (60) | 1.054 ± 0.017 |
| 4096 | 1e-3 | 2 | 4500 | 0.090 ± 0.002 | 0.010 | 1.365 ± 0.012 | 1.196 ± 0.009 (150) | 1.003 ± 0.016 |
| 4096 | 1e-3 | 3 | 6000 | 0.090 ± 0.002 | 0.010 | 1.314 ± 0.012 | 1.204 ± 0.008 (200) | 1.019 ± 0.016 |

The sd is 0.09 at every n, fd and tier count, the single tier's included. That is
1/sqrt(K + 1) for K = 115 (0.093): the counting noise of the draws a budget rests on.
Averaged over its 30 seeds no (profile, chain) dismisses more than 1.071 of the budget,
so the tail is the model's finite draws, not plans that are systematically off. At fd
0.05 (K about 580) the sd is 0.040 and the worst plan of 1500-3000 is 1.10-1.13.

Why 3390d4f3 measured a larger bias: it used the gate model's own seed for every
profile, and one seed gives every profile the same underlying noise (`_simulate` draws
the same normals, scaled by each profile's power), so a mean over the profiles is close
to one draw. At model seed 13 and its check (200k draws at seed 977, fd 1e-2),
3390d4f3's three chains give its numbers: 1.050 ± 0.024 and 1.085 ± 0.029 with no cut,
exactly, and 0.985 and 1.012 at z 0.75 (1.008 at 3390d4f3); that ± (the sd over plans /
sqrt(plans)) treats the plans as independent. The previous entry's six chains give its
numbers exactly: 1.032, 0.991 and 1.012 for one, two and three tiers at z 0.75. Over
seeds 14 to 29, each also shared by every profile, the six chains' means with no cut are
1.004, 1.029 and 1.045 (seed 13: 1.032, 1.060 and 1.085), with sds over seeds of 0.026,
0.025 and 0.037. A one-seed measurement of the bias is uncertain by 0.3 to 0.4 in z, and
seed 13 sat about one sd high. Over every chain, on the independent checks, seed 13 is
not high: its multi-tier plans dismiss 0.953 and 0.959 of the budget at fd 1e-2 and
0.950 and 0.966 at 1e-3, at z 0.75. Every job uses seed 13, so its plans share that one
draw's luck.

The value of z is left at 0.75. No function of fd or K is called for: in standard errors
of the count the bias is the same at fd 1e-2 and 1e-3, where K is the same, and at most
slightly smaller at 0.05, where K is five times larger. At 0.75 the plans
`chain_thresholds` makes for a given chain dismiss 3-5% less than the budget (2% at fd
0.05), and the chain `choose_chain` picks 2-4% less. The two want different values:
about 0.3 (two tiers) and 0.4 (three) for a given chain, and about 0.5 for the pick. At
z 0.5 the multi-tier picks average 0.988-1.005 of the budget and given chains
0.978-0.995; the worst plan rises by up to 0.04, and one seed's worst by 0.023-0.030 at
fd 1e-2 and 1e-3 (1.214 against 1.188 for two tiers at n = 2048, fd 1e-2). Which of them
z should target is not decided.

# The budget split's selection bias and per-plan scatter, 2026-10-27

A multi-tier chain searches threshold splits on the draws it is judged on and keeps
the cheapest, so its dismissal on fresh draws exceeds the budget. 3390d4f3 cut each
multi-tier budget by `gatechain._SPLIT_TOLERANCE_Z = 0.75` standard errors of the
dismissed count, the measured size of that bias, in place of the one-sided 95% cut
(1.645), which left multi-tier plans at 0.92 of the budget. The comment at
`_SPLIT_TOLERANCE_Z` and the commit message hold the measurement (200k independent
draws, n = 2048, fd 1%, 10 profiles, 30 plans). That measurement used one model seed
for every profile; over 30 independent seeds the bias is half as large, and at 0.75
multi-tier plans dismiss 0.95-0.97 of the budget (the entry above).

The mean is then on budget, but each plan's realised dismissal scatters about it.
Measured at 33e22fa7 on dev2 (one pinned core, GPU hidden, load 5-7; 28 s at fd 1e-2 and
4 min 54 s at 1e-3):

- Profiles: `tools/fdr_audit.default_profiles()` (10), each at n = 2048, snr 5.5,
  window 192..1856.
- Chains: (256), (512), (256, 512), (256, 1024), (128, 512) and (256, 512, 1024),
  where every band is usable.
- Thresholds from `gatechain.chain_thresholds` on the model's own draws (seed 13), with
  no cost model, so the split is chosen on the operation count (the commit found flop and
  calibrated costs give the same bias).
- Each plan judged on N independent `signal_draws` (seed 977): the fraction of the kept
  draws (fine maximum at least snr) that some tier dismisses, over fd.

| fd | N | tiers | plans | mean | median | p90 | max | sd | check noise sd |
|---|---|---|---|---|---|---|---|---|---|
| 1e-2 | 200,000 | 1 | 20 | 1.032 | 1.049 | 1.150 | 1.207 | 0.106 | 0.029 |
| 1e-2 | 200,000 | 2 | 30 | 0.991 | 0.993 | 1.097 | 1.283 | 0.101 | 0.029 |
| 1e-2 | 200,000 | 3 | 10 | 1.012 | 1.002 | 1.109 | 1.131 | 0.077 | 0.029 |
| 1e-3 | 2,000,000 | 1 | 20 | 0.997 | 1.012 | 1.115 | 1.134 | 0.086 | 0.029 |
| 1e-3 | 2,000,000 | 2 | 30 | 0.950 | 0.943 | 1.050 | 1.133 | 0.078 | 0.029 |
| 1e-3 | 2,000,000 | 3 | 10 | 0.959 | 0.943 | 1.068 | 1.077 | 0.074 | 0.029 |

The check's own counting noise (last column) is small beside the spread, so the spread
is the plans'. It is the same for one tier, which has no split search, as for two and
three, and about what counting the ~100 dismissed draws a budget rests on gives
(`gatemodel._nsamp_for`; 1/sqrt(100) = 0.1). So it comes from the finite model draws,
not from the split search: a larger multi-tier cut would move those plans' mean below
the budget without narrowing the spread, and more model draws would narrow it.

Two observations are not settled by this run. The worst plan is 1.28 of the budget at fd
1e-2 and 1.13 at 1e-3, and no plan exceeds 1.3. At fd 1e-3 the multi-tier plans average
0.95 and 0.96 of the budget, where at 1e-2 they average 0.99 and 1.01; the cut was
measured at 1e-2 only. The plans of one profile share its model draws and its check
draws, so the 40 multi-tier plans are not independent, and one model seed and one check
seed cannot say whether that difference is real. (Settled in the entry above: it was one
seed's luck, and the bias does not depend on fd.)

The script, for re-running it (from the repository root, `PYTHONPATH=python`):

```python
# split_spread.py FD NDRAWS: per-plan realised dismissal / fd on independent draws, at the shipped
# z, for 1-, 2- and 3-tier chains; with the binomial noise of the check itself.
import sys, numpy as np
sys.path.insert(0, "tools")
from fdr_audit import profile, default_profiles
from matchedfilter import gatechain as gc
n, snr, win = 2048, 5.5, (192, 1856)
fd, N = float(sys.argv[1]), int(sys.argv[2])
chains = [(256,), (512,), (256, 512), (256, 1024), (128, 512), (256, 512, 1024)]
res = {1: [], 2: [], 3: []}; noise = {1: [], 2: [], 3: []}
for name in default_profiles():
    p = gc._norm_profile(profile(name, n), n)
    bands = gc.usable_bands(p, n)
    ev = gc.signal_draws(p, n, bands, snr, N, seed=977, window=win)
    keep = ev[1][:, 0] >= snr
    for chain in chains:
        if not set(chain) <= set(bands):
            continue
        pl = gc.chain_thresholds(p, n, snr, fd, chain, window=win)
        if pl is None:
            continue
        ok = keep.copy()
        for b, t in zip(chain, pl["thresholds"]):
            ok &= ev[0][:, bands.index(b)] >= t
        lost = keep.sum() - ok.sum()
        res[len(chain)].append(lost / keep.sum() / fd)
        noise[len(chain)].append(np.sqrt(fd * keep.sum()) / (fd * keep.sum()))
print("z=%.2f fd=%g draws=%d" % (gc._SPLIT_TOLERANCE_Z, fd, N))
for k in (1, 2, 3):
    r = np.sort(np.array(res[k]))
    if not r.size:
        continue
    print("tiers %d: %3d plans  mean %.3f  median %.3f  p90 %.3f  max %.3f  share>1.25 %.2f  share>1.5 %.2f  | check noise sd ~%.3f  observed sd %.3f"
          % (k, r.size, r.mean(), np.median(r), np.quantile(r, 0.9), r.max(), np.mean(r > 1.25), np.mean(r > 1.5),
             np.median(noise[k]), r.std()))
```

# One simulation for signal and noise, 2026-10-26

The gate model is one simulation (`gatechain._simulate`, `_core.simulate`). Each
draw is a block's n bins with variance p_k. The fine statistic is their n-point
transform, and band b's statistic is the b-point transform of bins [0, b). A
signal arriving at a uniformly random time (16 sub-sample phases) is added
through linearity. Every maximum is taken over the whole searched window, as the
engine takes it.

- `signal_draws` reads each statistic's running-maximum records outward from
  the signal, so any window is two lookups, with the engine's coarse alignment.
- `noise_block_maxima` reads the same draws without the signal.

The two are one model of one noise, and the tests check that they agree.

This replaces the local lag window, the Cholesky neighbourhood draws and the
pairing with noise from elsewhere in the window. The local window missed remote
coarse maxima: in the 1% sweeps the flat profile's gates dismissed nothing, and a
bimodal profile's side lobes reached 1.74x its budget.

The sweeps through the C engine (fd 1%, 14 profiles x 4 chains, n = 2048 and
4096) are on budget. The one flagged case (inspiral, single tier, n = 2048) is
the model's own ±10% sampling: its gate is +1.4 sd over model seeds.

Only draws whose fine statistic reaches snr somewhere in the block hold records.
Where few do, as at snr = 1000, the simulation runs longer, up to 4x, until
half its draws' worth are kept.

# Retiring the accuracy table, 2026-09-26

`choose_threshold` now calls `gatemodel.gate_for` directly. The model uses
the complete reference power profile, the coarse grid and the correlated
coarse/fine Gaussian noise. ACC, ACC2, ACC2R and THR lookups are gone, along
with their files, margin placement, SNR envelopes and obsolete producers.
There is no accuracy-table fallback. Unresolvable budgets refuse; an
explicit band and coarse threshold still bypass model calculation.

The single-band functions here (`gate_for`, `dismissal`) are the one-tier
case of the gate-chain model in `gatechain`, computed from the same joint
draws. `MF_ACCURACY`, `MF_THRESHOLD`, `MF_COST` and the `tuning` argument are
gone.

## The full-band blocker was a reference mismatch

At n=4096, band=2048, SNR=5 and fd=.001, the inspiral reference produces a
gate of **4.654114**. Modelled dismissal is **.00099356**; 100,000 independent
filter injections measured **.00101235**. This is not a quantile-placement
failure.

The old test ran sixteen different template profiles against that one
reference. The matched bank loses **0 of 48** fixed-seed noise triggers;
the heterogeneous bank loses **7 of 78**. Both retain all spectral power,
but the coarse step is still two fine samples: odd-lag peaks scallop.
Full spectral coverage does not imply identical coarse and fine maxima.

| Template power-law exponent | Own fd=.001 gate | Model dismissal at 4.654114 |
|---|---:|---:|
| −7/3 | 4.6541 | .000994 |
| −2 | 4.4227 | .00919 |
| −5/3 | 4.0665 | .04396 |
| −4/3 | 3.6491 | .12263 |

The replacement tests distinguish matching references, heterogeneous banks,
and deterministic loss between coarse-grid lags. They do not replace a
budget assertion with a permissive gate. The model's gate is unchanged by
this diagnosis. Reference groups or an explicitly validated common gate
are necessary for heterogeneous banks.

## Resolution and limitations

Samples have per-component noise variance one. They are conditioned on the
fine maximum crossing SNR before the coarse quantile is taken. fd=.01,
.001 and .0001 request 20,000, 200,000 and 2,000,000 draws respectively.
Roughly half survive conditioning, leaving approximately 100 tail events:
roughly 10% relative counting uncertainty, not an exact probability bound.
Budgets with fewer than eight conditional tail observations are refused.
Obviously unresolvable requests are rejected before allocating samples.

The covariance calculation and sampling run at plan preparation, not in the
filter loop. An LRU cache is capped at 64 entries **and 64 MiB**. Its key
includes normalized profile bytes, exact SNR, band, length, draw count and
seed. This fixes the previous omitted-seed and rounded-SNR cache aliases.
The recovered fraction is clamped against floating-point overshoot at one,
preventing a negative out-of-band variance at full coverage.

(Superseded 2026-10-26: the model now takes whole-window maxima; see the top.)
The model samples a local lag window. It is validated closely for the
recorded profiles and bands, not universally exact for every spectrum or
noise population. At band 128, n=4096, fd=.001, the inspiral-profile gate
2.5550 dismissed **0 of 100,000** trial injections. This is consistent with the local approximation omitting remote coarse
maxima; that mechanism has not been separately isolated here. This
conservatism can cost throughput. The tests assert budget compliance there,
not falsely claim two-sided 10% agreement. Non-Gaussian noise and template
profiles unlike the reference are outside the calibration assumptions.

An old strict xfail asserted that *measured* dismissal must fall when the
band widens, despite choosing a different gate for each band. That is not
an invariant: one gate can underspend its budget. Its replacement tests
that every band respects the requested budget, with sufficient counts.

## Independent 1e-4 measurement

At n=1024, band=256, SNR=5.5, the benchmark reference gave gate **4.1241884**.
With a seed independent of the model and 1.5 million requested injections:

- fine detections: **860,549**;
- dismissed: **82**;
- measured FDR: **9.5288e-5**;
- model FDR at that gate: **9.9967e-5**.

Reproduce with:

```sh
OPENBLAS_NUM_THREADS=1 PYTHONPATH=python python tools/audit_gate_model.py \
  --n 1024 --band 256 --snr 5.5 --fd .0001 --trials 1500000 --seed 417
```

The standard suite now runs a real `_bench_hier` point at fd=1e-4 and checks
quantile placement at all three budgets. The benchmark already swept 1e-4;
it can now produce actual timings rather than table-coverage refusals.
Its noise-only timing rows report **requested** FDR, not measured signal
loss. `audit_gate_model.py` reports empirical counts and Wilson intervals.

## Cost migration and performance

> **Historical.** The cost tables described in this section were retired when
> configurations became gate chains: tier costs are now calibrated in-process
> on the running machine (see [the hierarchical filter](hierarchical.md)), and
> `MF_COST`, the cost files and their tools no longer exist. The section is
> kept as the record of the gate-model migration.

Cost measurements remain hardware-specific. The obsolete gate-scale axis
had inconsistent provenance across generations and cannot be interpreted
as an absolute gate for this model. Migration retains each cell's measured
baseline (the scale nearest one), with its numeric cost unchanged, and
removes the scale column. At that migration, the format was:

```
COST n band U K snr f beff relative_cost
```

Old ten-field cost files are rejected with a regeneration instruction.
Current CPU and GPU retunes use an explicit
`# format cost-fd-pairs-v1` header and place `fd` and `pairs` between
`snr` and `f`; this distinguishes eleven-field rows from the obsolete
scale rows. Older custom cost files can keep nine fields.
Cost SNR coverage is resolved per configuration, so a sparsely measured SNR
cannot hide competing bands. Costs only rank bands; they never change a gate.
At the gate-model migration the cost table was an approximate ranking without
a budget or batch-shape axis. Both shipped retunes now measure those axes.
Retuning for a workload remains useful; neither table claims globally optimal
band selection.

Interleaved 8×32 timing on the same native build selected the same bands in
five checked cases. The comparison separates a changed gate from changed
selection. Full records and the harness are in
[audits/gate-model-2026-09-26](audits/gate-model-2026-09-26).

| n / SNR (fd=.001) | Old table gate (ms) | Model gate (ms) |
|---|---:|---:|
| 1024 / 5 | .0372 | .0393 |
| 4096 / 5 | .2055 | .2652 |
| 4096 / 6 | .1063 | .0990 |
| 16384 / 5 | 2.4205 | 2.8655 |
| 16384 / 6 | 1.6887 | 1.3624 |

These are not zero-cost changes: where the new gate admits more pairs, the
filter performs more refinement. No execution kernel changed in this
migration. Cold selection at fd=.001 cost .13–.14 seconds in these cases;
warm selection cost .09–.41 milliseconds. Tighter budgets increase cold
sampling cost. Comparing unsafe table gates solely on throughput would
hide the accuracy correction this task was requested to make.

## Teaser

The regenerated [teaser](assets/teaser.svg) uses the same matched-profile
bank for flat and hierarchical paths. The old heterogeneous bank did not
satisfy the reference contract. It now includes fd=.01, .001 and .0001 as
overlapping hierarchical bars: every boundary marks total throughput.
[Raw measurements](assets/teaser.json) include selected bands and refine rates.

Both filter devices time warm public `run()` calls; GPU readback and result
assembly are included. Baselines time full-batch inverse transforms only.
FFTW uses one thread, unnormalized execution and PATIENT planning capped at
15 seconds. rocFFT operates on initialized resident storage and amortizes
synchronization over eight executes. It is no longer labelled as saturating
memory bandwidth based on an unrelated historical measurement. Historical
Apple M2 constants are not mixed into a fresh model-generated figure.

At fd=1e-4, the 16×1024, n=4096 teaser measures **8.82 ms CPU** and
**.274 ms GPU**, versus flat **46.99 ms** and **1.347 ms**. This is a workload
example, not a general speed guarantee.

## Verification and shared-checkout isolation

Isolated validation: **844 passed, 6 skipped** on the Ryzen AI MAX+ 395 and
Radeon 8060S, with hardware GPU execution enabled. There are no remaining
xfails in that run. Linux CI without GPU hardware retains CPU/model checks;
Apple CI remains responsible for Metal execution.

A concurrent session was editing the class and GPU cache implementation.
Validation used a copy of committed code plus this task's changes, with the
same native extension (SHA-256
`e242d3696275d283950008e6331c485c6057dbe7b9dd960da3f9c6dee958c21d`).
The binary matches the concurrently committed CPU broadcast optimization.
Uncommitted class/cache changes were excluded from both the validation and
teaser timings. The shared checkout was not reset or overwritten.

The teaser was remeasured after competing jobs finished, using sustained
warmup and timing blocks: with the retuned GPU costs, fd=.01 reaches
**83.71 M/s**. See the
[throughput investigation](audits/gate-model-2026-09-26/gpu-throughput-investigation.md)
for historical timing differences and concurrent-workload evidence.

After the concurrent class/cache changes were committed, the combined
working tree passed **892 tests, 6 skipped** on CPU and Radeon 8060S.

## Radeon 8060S cost retune

The 8060S now ships a device-specific, FDR- and pair-count-aware cost table.
It ranks bands separately at three budgets and two measured batch sizes;
calibration still comes only from the reference gate model. See the
[retune audit](measurements/gpu-cost-retune-2026-09-26.md), including raw
measurements and independent holdout results. The prior gfx11 family table
remains for other hardware.

## Chain choice: useless tiers and stable ties (2026-10-10)

* **How (64, 256) gets in.** Through the model's candidate list (not reproduced here as the
  winner, but present): for a reference whose power
  sits above bin 64, band 64 is still "usable" (nonzero power), and the budget split gives
  it a threshold at which it passes ~every pair (modelled reach 1.0). Its own cost is tiny
  and the sparse tier-2 price at density 1.0 is a clamped extrapolation of the 1%/10%
  calibration, so the chain could rank near the top. (The order is not narrower-then-wider:
  the GPU prints the cascade as (band, cascade_band); the chain is (64, 256).)
* **Now:** `choose_chain` skips any split in which a tier passes more than
  `_USELESS_PASS = 0.5` of its pairs on to another tier (pinned chains still get thresholds;
  the last tier's pass rate into the refine is left to the cost, since at low snr every
  chain refines most pairs). Trials record a call whose first tier passed more than that
  fraction to the next tier as infinitely slow, so such a chain cannot lock.
  `test_a_tier_that_passes_most_pairs_is_never_chosen` reproduces the (64, ...) candidates
  without the rule.
* **Stable ties.** Candidates within `TIE = 5%` are treated as tied: the model breaks ties on
  the calibration-free flop proxy, trials on (fewer tiers, smaller bands), the block size on
  the smaller n. On dev2's GPU the choice repeated across processes after this, (2048, (256,
  1024)) in every run, as on main.
* **Host cost.** A first attempt charged all of (wall - device) per block; it moved the bank
  to n = 4096 and the fine stage got 1.4x slower, because most of that residue is per call.
  Now `calibrate_costs_gpu` times the same call at two block counts and fits
  host = host_call + host_block * blocks; `price_block_sizes` charges host_block per block
  (a bank makes one call per segment, so host_call does not depend on n) and breaks ties on
  the host term. On the 8060S: host_block 2.1 us at n = 2048 and 5.7 us at 4096, against
  device block work of ~0.3/0.7; with it the n = 2048 margin over 4096 went from ~6% (inside
  the noise that made it flip) to ~30%.

## Host term removed from block-size pricing (2026-10-10)

The per-block host term added in gate/chain-stability is not charged any more. Its fit grows
the series with the block count, so it measured a per-sample staging cost (5/10/20 us per block
at n = 2048/4096/8192 on the 8060S): the same per valid sample at every n, several times the
device terms, and 2x noisy under load. It could only reshuffle near-ties, so neighbouring length
batches of one bank landed on different block sizes run to run. That fragments banks into more
template groups, hence more calls. It is a candidate for the fine-call growth on 437367c
(54 -> 258 calls per segment); the review agent's bisect decides.

dev3 Renoir, Vulkan, load < 1, 3 interleaved processes each, autotune on (2 tops x 6 segments):

| | run 1 | run 2 | run 3 |
|---|---|---|---|
| main 437367c, fine | 2.33 s | 1.80 s | 1.87 s |
| main, layout | 4096 (mixed chains) | 2048 | 2048 + 138 templates at 4096 |
| host term off, fine | 1.90 s | 1.85 s | 1.73 s |
| host term off, layout | 2048 | 2048 | 2048 + 69 templates at 4096 |

### Unused host calibration removed (2026-10-20)

The two measurement batches for that unused host fit have now been removed as
well, along with its model fields and serialization. At the default five
repetitions, this removes twelve calibration-plan calls and ten clock-reference
measurements per uncached GPU cost model. This counts removed work, not a
measured wall-time improvement. Device costs, gate thresholds, and the
smaller-block tie break are unchanged; existing cost files still load, ignoring
their obsolete `host_call` and `host_block` entries.

## Forward priced per chain (2026-10-10)

Vulkan can write only the widest tier's band of each block's spectrum and recompute the
full spectra of blocks with a refined pair (docs/vulkan-8060s-roofline.md section 13); it does
so when the refine-block fraction f < (n - B)/2n. A chain that refines few blocks therefore
pays a cheaper forward, which the cost model did not credit.

* `CostModel.forward` is the full forward per block (on the GPU, `block`: per-block fixed work
  is the forward plus small bookkeeping, and one submission cannot time it apart), and
  `band_forward` is a backend capability (`_BAND_FORWARD = {"vulkan"}`).
* `forward_cost(chain, f)` applies the backend's own byte rule: full, or a band write
  `forward * (1/2 + B/2n)` (same series read, B of n written; 0.75 at B = n/2 against
  2.8/3.8 = 0.74 measured) plus `f * forward` of recompute.
* f: only the measured fraction (`note_refine_blocks`, called by Vulkan's band measurement,
  keyed by (n, widest band)); without one a chain gets no credit. The model's
  1 - (1 - P(refine))^templates was tried first and moved 1757 of 4249 ladder templates to
  n = 8192, making the fine stage 1.4-1.7x slower. The fraction itself is right (refine density
  matches the model within 10-25%, "Refine density on realistic data" on the refine-density
  branch). What failed is that the per-term GPU costs it corrects are noisier than the credit,
  so it tipped near-ties the wrong way. The model's f waits for end-to-end block-size trials.
  Measured values do not enter the choice cache key, so a choice made once stays made within
  a process.
* `choose_chain(..., ntemplates=)` adds each chain's forward change from the full forward
  (already in `block`), shared by the templates; HierarchicalFilter and block-size pricing
  pass their template counts. With few templates a credit can take a total below zero, so
  the tie window is now `lo + TIE * |lo|`. (Adding the whole forward to every chain instead
  widened every relative tie window and, by itself, moved templates to n = 8192.)

Effect: with the model's f, (256, 1024) at n = 2048 (f = 1%) gained the band credit and tied
(256, 512); on the ladder the credit at n = 8192 went the wrong way (above). With measured-only
f, a process's first choices are the base's, and later choices see Vulkan's measured fraction.

## Block-size trials (2026-10-10): built, measured, net loss -- not ready

`time_domain._BlockTrials` builds the model's top block-size layouts (within 30% of its
cheapest; at most 2) at the first reference, while the taps are still held. Each batch of
`filter_series_many` puts every trialling bank on one candidate rank and times the batch from
submission to the last result, per template x series sample. Batches in which a bank
switched layout are not timed. The model's rank runs first. After one clean sample per
rank, the fastest within gatechain.TIE is locked (ties keep the model's choice); the
others are dropped. `tests/test_block_trials.py` checks that a clearly worse rank (1.5-10x)
is never locked, in either order, that ties keep rank 0, and that a bank's switch and lock
work end to end.

Measured on dev3's Renoir (Vulkan, load < 1), 3 interleaved processes, autotune on, 2 tops
x 6 segments, steady fine stage:

| | run 1 | run 2 | run 3 |
|---|---|---|---|
| main | 1.83 s | 1.82 s | 2.29 s |
| branch | 2.67 s | 3.81 s | 2.50 s |

The branch is slower in every run, including runs where it locked rank 0, so the cost is
not the choice itself. The likely cause, not yet proven: building a second layout doubles
each bank's GPU-resident spectra and plans on an iGPU with a small shared budget. The
dropped layout's device storage is evicted only by LRU, so live data is re-uploaded in
steady state. Two further caveats:
- One sample per rank is thin: the locked ranks differed 12-27% on single batches.
- Main itself chooses differently across processes on this host ((2048, (512,)),
  (2048, (256, 512)), mixed 2048/4096), so the baseline is not a fixed point.

Needed before this can ship:
1. Free the dropped layout's device storage explicitly at lock (GPU cache API), or build the
   alternative only for the batches that trial it.
2. Take more than one sample per rank, still within the warm-up: time per bank rather than
   per batch.
3. Then re-measure.

Until then the forward credit stays measured-only.

### Block-size trials, second round (2026-10-10): still a net loss; why

Changes:
- Trial batches run each bank alone, so each bank gives a paired sample: rank r against rank 0
  on the same bank. There are 22-27 samples per rank within the warm-up.
- A lock evicts the dropped layout's device storage, and only if that layout ever ran.
- Banks built after the lock adopt the winner with no trial batch.

dev3 Renoir, load < 1, steady fine stage:

| | main | trials off (MF_BLOCK_TRIAL_RANKS=1) | trials on |
|---|---|---|---|
| run 1 | 2.25 s | 2.32 s | 2.80 s (locked rank 1, paired ratio 0.90) |
| run 2 | 2.32 s | 1.79 s | 3.15 s (locked rank 1, 0.89) |

The machinery costs nothing: with trials off the branch matches main. What the trials lock is
wrong. Rank 1 is "the second-cheapest n per length batch", and that mixes block sizes within
a bank (2596 templates at 2048 and 2102 at 4096 in one run). Timed alone, each bank was ~10%
faster that way. In steady state the banks run fused and concurrently, and the extra
template groups -- more calls, smaller dispatches -- cost more than that.

Two conclusions:
1. Candidates must be whole-bank layouts at one n each (n = 2048, 4096, ...), not per-batch
   rank mixes.
2. A solo per-bank sample does not predict fused steady-state time. A representative sample is
   a whole fused batch, at roughly one per batch. Two or three candidates at three samples each
   do not fit a two-segment warm-up. They fit if the lock is persisted in MF_COST_FILE (keyed by
   device and the bank's candidate set), so a machine pays for the trial once rather than once
   per process. That also makes the choice stable across processes.

Not shippable as is.

### Block-size trials, round 3 (2026-10-11): whole-bank candidates, fused-batch samples, persisted lock

- **Candidates per bank.** The model's own layout is rank 0. After it come the whole bank at each
  of its cheapest single block sizes: sizes every length batch can use, ranked by their summed
  modelled cost. A single size whose partition equals the model's is skipped. There are at most
  3 candidates (`_BLOCK_TRIAL_RANKS`). `price_block_sizes(ahead=)` prices that many sizes past the
  first dearer one so that they exist.
- **Samples.** A sample is one whole `filter_series_many` batch, fused and concurrent as in steady
  state, timed from submission to its last result, per template x series sample. A rank's first
  batch after a switch only settles (it uploads). There are 2 samples per rank. Rank r > 0 wins
  only if its median beats rank 0's by more than gatechain.TIE, so a tie keeps the model's layout.
- **Persisted lock.** The winner is stored in MF_COST_FILE under `choice|block-trial|<device>|<candidate
  set>` (`block-trial|...` before 2026-10-21). A bank whose key is on file adopts it at its first reference with no trial, and only
  layouts that ran are evicted from the device at a lock.
- **Only where the lock can be kept.** Without MF_COST_FILE (or with MF_AUTOTUNE=0) no candidates
  are built and no trial runs. The bank is the model's layout, exactly main's behaviour. A trial in
  every process would cost that process its warm-up and more (the trial process below), for a few
  percent.

dev3 Renoir, Vulkan, load < 1. Each side has its own fresh MF_COST_FILE, the processes are
interleaved, the configuration is 2 tops x 6 segments, and the figure is the steady fine stage.
Main with a cost file is the fair baseline: with persisted cost models it is itself stable,
(2048, (256, 512)) at 1.14-1.26 s, against 1.8-2.3 s and varying layouts without a file.

| process | main | branch |
|---|---|---|
| 1 (branch runs its trial) | 1.26 s | 4.09 s (trial: 8192 at 2.1x, 4096 at 1.08x, locked the model's) |
| 2 | 1.15 s | 1.09 s |
| 3 | 1.14 s | 1.09 s |
| 4 | 1.14 s | 1.09 s |
| 5 | 1.20 s | 1.08 s |

Second set (final code: candidates built only with a cost file), fresh cost files:

| process | main | branch |
|---|---|---|
| 1 (trial) | 1.36 s | 4.39 s (4096 at 2.4x, 8192 at 6x; locked the model's) |
| 2-4 | 1.35 / 1.34 / 1.34 s | 1.34 / 1.34 / 1.35 s |

After the one trial process, the branch is never slower than main (equal in the second set, 4-10% faster in the first), and the
same layout in every process. In both sets the trial confirmed the model's layout; the gain in the
first set comes from the calibrated cost models in that file, not from a different layout.
Where the model is right, trials buy stability and a guard against its mistakes, not speed. The trial costs one process's fine stage once per machine and
candidate set, not once per process.

### Model-f proposals, pooled trials, and persisted chain locks (2026-10-11)

- **Model f proposes, the trial decides.** Block-size trial candidates are ranked with the band-
  forward credit at the model's refine-block fraction (`price_block_sizes(model_f=True)`,
  `CostModel.chain_forward_delta(model_f)`). Rank 0 stays the model's own layout, priced without
  that credit, so model f can only add a candidate. Its own pricing never changes a choice. On the
  dev3 ladder the proposals are the same sizes as without the credit (4096, 8192), and the trial
  keeps the model's 2048 layout.
- **Pooled trials, cheap adoption.**
  - The trial key is the device plus the candidate block sizes. Ranks mean the same in every bank:
    0 is its model layout, k is its k-th proposed size. All banks of a search pool into one trial.
  - Each bank's proposal list is kept in MF_COST_FILE under its model layout. A later process maps
    the lock's rank to the bank's size without pricing proposals, and builds only the winner.
  - Pricing extra sizes (`ahead`) happens only when proposing. Keys per bank fragmented the trial,
    so the first version re-ran trials and paid ~30 s of warm-up in every process.
- **Chain-trial locks are persisted too** (`choice|chain-trial|n|snr|fd|tiers|device` since
  2026-10-21, used only if the stored chain is on the plan's shortlist).

**The unexplained 4-10% gain, isolated.** It was not the block-size layout. In matched processes
with the same layout and the same chain, (2048, (256, 512)), main's steady fine stage was 1.08-1.12 s
and the branch's 0.94-0.96 s. Main runs its chain trials in every process: one candidate needs
MF_CHAIN_TRIALS = 6 calls, and the trials run past the two warm-up segments into the steady ones.
Some processes even lock a different chain, e.g. (256, 1024) at 1.12 s. With the lock on file, no
trial runs and the steady segments are clean.

dev3 Renoir, load ~1. Each side has its own fresh MF_COST_FILE, the processes are interleaved, the
configuration is 2 tops x 6 segments, and the figure is the steady fine stage:

| process | main (block-trials round 3) | branch |
|---|---|---|
| 1 (trials run, files written) | 4.12 s | 4.58 s |
| 2 | 1.09 s | 0.94 s |
| 3 | 1.09 s | 0.95 s |
| 4 | 1.12 s, chain (256, 1024) | 0.96 s |
| 5 | 1.08 s | 0.94 s |

After the first process the branch is 12-15% faster in steady state, and identical from process
to process. The first process of each side carries both kinds of trials, once per machine.

### Every measured choice is per machine (2026-10-11)

`gatechain.stored_choice` / `store_choice` keep a measured choice in MF_COST_FILE next to the
cost models, the chain locks and the block-size locks:
- CUDA's coarse kernel variant, timed at first use per device and band
  (`cuda-coarse|<device>|<band>|<variant set>`).
- Vulkan's fused interleave depth per batch shape (`vk-interleave|<device>|<shape>`).

Metal has no timed choice today. Each choice is valid, but made afresh per process they
differed on noise (variants round differently), so borderline pairs gated differently in 1-3
jobs per segment. With a cost file a machine makes each choice once.
`tests/test_reproducible_choices.py` runs three processes on one cost file, on the CPU and
on gpu:0 where present, and requires identical triggers, layout and chains: the second and
third processes against each other, and against the first process's locked segments.

## CPU paired trials and bounded measurement (2026-10-15)

CPU Q15 and block-size trials now use complete rounds on identical workloads.
Q15 replays the same series call; block-size trials replay the same batch of jobs
at every candidate layout, holding each layout's inner chain and Q15 trials.
Each arm settles before timing, and execution order reverses between rounds.
The decision uses per-round ratios against the model and requires 75% agreement
beyond the existing 5% tie margin. A single contaminated round affecting only one arm cannot
win a five-round trial. Sustained or systematically arm-correlated interference
can still bias the result; this is robust sampling, not a guarantee under arbitrary load.

CPU block trials take at least five complete rounds (or MF_BLOCK_TRIALS if larger)
and cap an ambiguous contest at twice that minimum. Q15 takes at least six by
default and caps at twelve. Complete partial rounds persist between processes.
Old unpaired partial block samples are not valid paired evidence and are restarted;
existing final locks are preserved. No additional candidate is excluded. The GPU
measurement and decision paths retain their existing behavior.

This increases first-run calibration work: each round executes every candidate,
including an untimed settling call. It does not promise that two fixed warmup
segments will suffice. `tools/ladder.py` reports `cpu_trial_work_in_steady` and
`steady_valid`, with a warning if CPU trial work occurs after the first steady
boundary. The counters include Q15 replays, CPU block rounds, and CPU chain calls
(including chain switching); they do not measure all cost-model construction in
initial setup. For multiple tops the first boundary is conservative: later tops'
calibration also invalidates the report.

Use the bounded study driver to keep calibration out of accepted CPU timing:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  taskset -c 6 python tools/cpu_trial_check.py \
  --bank BANK.hdf --profiles PROFILES.npz --out NEW_DIRECTORY --starts 10
```

Each independent start uses a fresh cost file. By default it permits at most four
six-segment processes, retaining every log, report, and lock transition. A run is
accepted only if no CPU trial occurs after the steady boundary, no trial lock
changes during that process, and no persisted trial remains unfinished. Failure
to settle is reported as failure, not silently labelled steady. Compare two code
versions only after comparing their complete trial-lock dictionaries; force the
same locks when measuring execution overhead rather than choice quality.

### Chain-trial audit and remaining limitation

CPU chain trials still pool cost-per-pair observations from different calls and
plan shapes. Their candidate union can grow as plans with different shortlists
join; candidates need not be feasible on every plan. They therefore have the same
comparability risk as the old Q15 trial. Unlike Q15, chains can change borderline
outputs, and switching rebuilds plans, templates, and thresholds. This patch
instruments that calibration work but does not change chain selection, feasibility,
existing usefulness checks, or the shared GPU decision rule. A follow-up should
pair each challenger with a feasible incumbent on the same input and preserve the
candidate union explicitly; normalizing unrelated timings by pair count is not a
substitute. Persisted chain locks and reproducibility behavior remain intact.

Raw cold-start records, frozen-source identities, and controlled timing are in
[the CPU trial measurement record](measurements/cpu-trial-reliability-20261015/README.md).

## Replacing cost planning: feasibility study (2026-10-20)

The current infrastructure contains runtime price calibration, scientific gate
selection, and several persisted execution trials. It also stores device
capability decisions such as accurate GPU trigonometry. Removing price curves
does not remove the need for valid gate thresholds, reproducible resolved plans,
or those capability checks.

Two study tools separate the questions:

* `tools/cost_model_ablation.py` uses captured reference profiles and model
  windows to compare measured-cost planning with the existing `cost=None`
  operation-count proxy. Both price the same accuracy-valid candidates. It
  reports thresholds, candidate counts, shortlist coverage, and setup phases.
  Its regret is a **cost-model estimate**, not a runtime measurement.
* `tools/real_probe_study.py` freezes the prepared production chain and
  thresholds, then tests float-only, ordinary Q15, and delayed-recheck Q15 on
  one native plan. It uses the full template bank and stratified whole native
  groups of real input, validates sparse outputs and native output counts, and
  separately times full calls. A duplicate baseline configuration measures
  timing noise; it is not credited as a policy improvement.

On the retained 72 CPU leaf captures, there is **one distinct reference profile**
and two model windows, `[128,1920)` and `[192,1856)`. These are not 72 independent
gate-model validations. Measurements used one pinned core, one numerical-library
thread, fixed n=2048, production thresholds, and no `MF_HMF_PROF`.

| Experiment | Observation |
|---|---|
| Fresh CPU n=2048 cost model | 1.31 s |
| Signal draws, two windows' noise draws, candidate enumeration | 2.01 s additional setup |
| Global operation-count top five | All start at band 128; exclude the current model's `(256,512,1024)` winner |
| Best operation-count candidate per first band | Five representatives include that winner |
| Same-source, interleaved full leaf replay of the proxy's choice | `(128,256,512)` without Q15 takes 1.304 times the baseline time |
| Outputs in that chain comparison | 207 versus 205 peaks; one capture differs |
| Fixed-science Q15 execution study | All three variants reproduce the prepared bank's 205 peaks exactly |

For the two selected chains, operation-count and current-cost threshold vectors
coincided. Thus the chain replay tests the proxy's selected chain and screen
choice without an additional threshold-allocation difference. In general costs
also select a threshold-budget split; changing them is not just rescheduling an
unchanged decision.

The 32-block pilot took a median 5.0 ms per bank, including switching, warm calls,
validation and selection; 71 of its 72 samples had fewer than ten refinements.
Starting its selector from float-only still chose a Q15 variant in every case,
using the recorded pilot times alone. Distinguishing the two Q15 orders was much
less reliable. Against the fastest of separately measured full-arm medians, the
32-block choices had 0.62% aggregate apparent regret, with ten captures outside
2%. Identical baseline configurations themselves differed by as much as 6.2%
between measurements. These numbers do not establish a small speedup or a
no-regression replacement. The full-arm minimum is also optimistic under noise.

The probe still uses seeded costs to prepare its scientific plan. It does not
remove calibration end to end, and none of these results is a whole-search
benchmark or an independent false-dismissal bound. Larger 64- and 128-block
pilots cost more and did not establish a better selector on this dataset.

The promising replacement is a small, diverse menu of accuracy-valid complete
plans, followed by one bounded real-input trial and an optional saved resolved
plan. That record should contain literal thresholds and compatible execution
settings, not a rank into a changing candidate list. First-band diversity is a
useful starting point; coverage across other profiles, block sizes, devices and
real GPU batch/fusion modes still needs measurement. Rare refinement choices
need more evidence than a small dense-screen pilot supplies.

Production selection remains unchanged in this branch. Only the unused host
calibration described above is removed. This preserves active cost arithmetic
and avoids introducing another production tuning mode before the replacement
has passed cold-start and settled full-search comparisons.

### Block sizes decided on real calls, by absolute rank (2026-10-26; superseded below)

- **Why.** The CPU cost model is calibrated on hot-cache microbenchmarks (64 templates, 32 blocks).
  On a loaded Haswell node real per-stage costs were 1.1-2.4x the calibrated ones, differently per
  block size (later tiers 1.32x at 2048, 2.43x at 4096), so the model priced 4096 at 1.2x 2048
  where it ran 1.6-1.95x, and fresh processes put 0-231 of test67's 323 banks on 4096. Correcting
  the model from the running size's own calls cannot fix that (2048's factors applied to 4096
  predicted 1.41x, against 1.95x on the same calls).
- **What.** The block-size trial runs without MF_COST_FILE: its lock is the process's, pooled over
  every bank of a search, so the first reference's banks settle it. CPU leaves of a search run as
  one filter_series_many batch, where the CPU trial's paired rounds sample.
- **Ranks.** A bank's candidates are the whole bank at its smallest single sizes, smallest first,
  then the model's layout. A rank is the same size for every bank of a trial, a tie keeps the
  smallest size, and the model's layout is kept only when it wins outright. Ranks whose built
  layouts are the same object share their samples (they can only tie). A locked size is built
  without any block-size pricing, so later banks skip the larger sizes' simulations.

## One joint trial for block size, chains and the screen (2026-10-26)

Supersedes the block-size, chain and Q15 trials described above. They were three mechanisms
for one decision. They differed in what a candidate was (model-relative ranks; one chain for
every plan; a screen setting per full chain), in what a sample was (paired rounds; single
unpaired calls; batches; replays inside one call), and in what they pooled. Each of those
differences caused an error that has been measured:

* Candidates relative to the model chose among the model's errors. The block trial's rank 1
  could mean 4096.
* The chain trial pooled plans of every profile into one lock, one chain for all of them.
  Paired on the same input, each plan's own model chain was faster than that lock per steady
  call: dev2 -7%, dev1 -10%, Haswell -11% to -14%, Ivy -2% (test67 leaves).
* The Q15 trial was keyed by the full chain, although the screen concerns only the first
  band. With plans on four chains, four paired Q15 trials opened for what is one decision.

### The mechanism (`_trial`)

One trial per key decides every coupled dimension at once, over complete configurations:

* **Arms.** `default` puts every dimension at its default: the bank's smallest candidate block
  size, each plan's model chain, and the model's screen setting for that chain. It is the
  preference. In the first pass every other arm moves one dimension, and the model fills in
  the rest conditional on it:
  * `n=4096`: the next single block size;
  * `n=model`: the model's own priced layout;
  * `q15=0` and `q15=1`: the screen off or on.

  Chains are not arms: each plan runs its model chain. A pooled chain decision, sampled on a
  search's first banks, picked a chain faster there and 5-10% slower over the rest.

  An instance that cannot take an arm's value runs its default there, for example a chain
  outside a plan's feasible set, or a screen its first band does not have.
* **Resolution.** Each instance (a bank, or a plan used on its own) resolves an arm to its own
  configuration. Arms an instance resolves alike are one configuration, timed once, so they
  can only tie.
* **Rounds.** A sample is a paired round (`Choice.play`, the engine every trial uses). Every
  distinct configuration of the live arms runs the same work back to back, each timed run
  right after an untimed run of the same configuration (on a GPU, replays until no recording
  is built): a GPU batch run second ran 20-30% faster, so every timed run is a second run.
  The order reverses each round. On the CPU the untimed runs cost the cap67 replay at most
  0.35 s more than settling each configuration once (under 0.5% of the job). Rounds pool as ratios to `default` (`paired_choice`),
  so banks and plans of different cost pool into one trial. That pooling is also why a round
  needs only a few banks: it replays two of the batch's trial banks (`_ROUND_BANKS`, rotated
  from round to round over the batch), and the rest of the batch runs once on `default`. A
  test67 batch holds 17 leaf banks. Replaying all of them twice per configuration cost 11 s of
  a 74 s job; two banks per round, settled once, cost 2.6 s.
* **Elimination.** An arm is dropped from later rounds once it can no longer win, that is,
  once its wins plus every round still to come cannot reach the share `paired_choice` needs
  at the cap (`_choice.can_still_win`). The rule is exact: a test enumerates every win/loss
  history against `paired_choice`. Arms that only tie with `default` leave after three
  rounds, and so does a clearly slower arm.
* **Confirmation.** An arm the rule picks over `default` is not locked at once. A fresh
  contest of `default` against it alone must pick it again, or `default` stands. On a loaded
  node a round's ratios swing by +-30% (Haswell at load 55: one arm read 0.65, 1.07, 0.84,
  1.08 and 0.98 of `default`, its true ratio about 1). With seven challengers, one passes the
  75% rule on noise more often than one alone does: an unconfirmed trial on a loaded Ivy
  Bridge locked a fixed chain with the screen off, and ran 18% slower.
* **Passes.** A pass locks at its first confirmed winner, keeps its base on a tie, and stops
  at its cap (`2 x MF_TRIAL_ROUNDS` rounds) or its budget of calls that could not be rounds.
  A pass that locks an arm other than its base opens the next pass around that arm: the arm,
  and the arm with each dimension it has not moved moved too (`n=4096,q15=0`;
  `_trial.current_pass`, `_settings.around`). The trial ends at a pass that keeps its base.
  A first pass that keeps `default` ends it, so only a trial that moved pays a second pass.
  The GPU device trials (`gpu-batch`, `gpu-kernels`) search the same way.
* **Locks.** The trial's end is applied by each instance resolving the winning label,
  including instances made later. A bank made after a lock builds only the winner's layout.
  For a lock that moves no block size, or moves it to a single size, no block size is priced
  at all. Each pass is kept in `MF_COST_FILE` (`choice|joint|<key>`, then
  `choice|joint|<key>|<base>`) when one is set, and an open pass resumes in the next process.

Banks run their rounds in `filter_series_many` (`time_domain._joint_round`), on the CPU and
GPU alike. A plan inside a bank is governed by the bank's trial. A plan used on its own runs
its rounds in `run_series`.

### Why `default` is the smallest size, not the model's layout

The first version made the model's layout the preference. On the test67 replay at 12 calls
per bank (the job's mean) it was 19% slower than main. A tie kept the model's layout, which
put some banks on 4096, and every bank built after the lock paid for block-size pricing.
With the smallest size as the default, a tie keeps the layout that needs no pricing. That is
the rule step 1 of this work had already measured for block sizes.

### Coupling

Before building it, I checked that deciding jointly was needed. Each bank (every fourth bank
of test67) ran 8 complete configurations, paired: {2048, 4096} x {each plan's model chain, one
chain for all} x {Q15 on, off}. On dev2, dev1, Haswell and Ivy no dimension's ranking depended
on another:

* 2048 with per-plan chains and Q15 on was best everywhere.
* The single chain cost +2% to +8.5%.
* Q15 off cost +18% to +46%.
* 4096 cost +50% to +84%.

The one interaction was at 4096 on Haswell, where the single chain beat per-plan chains by
6%. 4096 lost by 50% there, so it changes no decision. The joint form is still the one
mechanism, and it would catch a coupling on a machine where one exists.

### Calls per bank

A test67 job (2048 s of data, dev2) calls each of its 319 leaf banks 12.6 times on average
(median 10, max 66), plus 5 single-template follow-ups. Bank calls took 22.3 s of the 73 s
job, against 4.2 s in `set_reference`. The setup replay tools capture only a bank's first call
per reference; replay at `K = 12` for the production regime.

### Results

test67 replay, all 323 banks, 12 calls each, interleaved with main (5fbcc4fc):

| machine | main | joint | |
|---|---|---|---|
| dev2 (Zen 5) | 21.6, 21.9 s | 20.8, 20.7 s | -4.6% |
| dev1 (Zen 3) | 47.1, 47.3, 47.4 s | 44.4, 44.2, 44.8 s | -6.0% |
| Haswell | RESULTS | | |
| Ivy Bridge | RESULTS | | |

Every bank ends on 2048 with the screen on for every plan (main left two plans' screens off),
and each plan runs its own model chain.

`MF_TRIAL_ROUNDS` replaces `MF_BLOCK_TRIALS` and `MF_CHAIN_TRIALS`. `tools/migrate_cost_file.py`
removes the superseded trial records from a cost file.
