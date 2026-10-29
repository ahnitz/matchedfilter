# A/A rounds: the paired rule's error and power on the CPU, 2026-10-29

This is step 7a of the 2026-10-29 roadmap. It measures, on the CPU and on the job's own
calls:

- the null distribution of one paired round's ratio;
- the false-switch rate of the current rule;
- the error and power of candidate rules.

The aim is that the error rate and the minimum gain of measured choices can be set from
these data. The user's provisional decision D8 says they must be "no looser than the current
measured false-switch rate". This page supports that decision and decides nothing.

The library was at f634aeae: a7df139e plus the A/A diagnostic. The evidence and its
provenance are in [measurements/trial-aa-20261029](measurements/trial-aa-20261029/README.md),
and `tools/trial_power.py` regenerates every number here from it. GPU trials are not
covered; they come in wave 2.

## Summary

- **The noise is set by the machine's state.** The robust sd of an equal arm's log ratio
  per round was:
  - 0.008 for one process on a quiet dev1;
  - 0.024 with eight of these jobs on dev1, and 0.064 in eight concurrent production-length
    ladders;
  - 0.07-0.09 on dev2, whose cores' SMT siblings were busy (load 11-38).

  Within one condition it shows no trend with the 1-minute load. Longer rounds are noisier,
  not quieter.
- **A process's first rounds are noisier, and they favour the arm run later.** In round 1,
  an equal arm beat the 5% tie in 33-45% of rounds on dev2 and in the dev1 ladders, against
  17-28% later; on the dev1 replay the figures are 8% against 2-3%. In the short ladders the
  A/A arm, run last, was 4-8% faster in round 1. Production contests are exactly these
  rounds: on most banks the CPU's challengers are 1.1-2.2x slower, so elimination ends the
  contest at round 3.
- **The current rule's false-switch rate follows the noise.** With its confirmation, for
  the two distinct challengers a CPU bank trial has, the rate per contest was:

  | condition | rate per contest |
  |---|---|
  | loaded dev2 | 1.2e-3 to 3.5e-3 |
  | the ladders | 1.3e-3 (dev2), 4.1e-4 (dev1) |
  | dev1 replay | 1.9e-10 |
  | dev1 with one process | below 1e-12 |

  Its power is at most 0.11 for a 5% gain and 0.60-1.0 for a 10% gain. On the logged A/A
  sequences, one contest (before confirmation) switched in 4 of 232 ten-round windows on
  dev2 and 0 of 225 on dev1, as the model predicts.
- **An exact sign test has an error rate that does not depend on the noise.** It is a
  group-sequential test of "at least delta faster", computed by DP for the cap, with Holm
  over the live arms. Re-testing a fixed-n sign test every round gives 0.051, 0.099 and
  0.145 at caps 10, 20 and 40 for a nominal 0.05, reproducing the critique; the
  group-sequential boundary holds 0.05.
- **Two settings meet D8 at the current overhead (3 rounds for a clear loser, cap 20):**
  - delta 3% at alpha 3e-3 is no looser than the current rule under every measured null;
  - delta 2% at alpha 1e-2 is no looser than the current rule's worst rate, and has at least
    the current rule's power under every measured null (to within 0.002).

  The recommendation at the end gives the details.
- **A larger error is outside this test's reach.** The pooled bank trial lets the first
  bank it plays decide for the whole job. Replays started at other banks locked q15=0 or
  q15=1 in 28 of 323 (dev2) and 15 of 323 (dev1) runs, and in 8 and 4 of 81 solo runs. On
  that bank those arms really were 10-50% faster. On the job as a whole the screen pays:
  2026-10-26 measured Q15 off 18-46% slower.

## The diagnostic

With `MF_TRIAL_AA_LOG=<file>`, `_choice.Choice.play` runs the preference a second time in
every round as one more arm (the A/A arm). It is settled and timed like a candidate and
placed after the candidates, so it comes first when the order reverses. Its result is
dropped and its time is never a sample. Each round's record holds:

- the runs, in order;
- every candidate's time, and the run it shares where two candidates ran alike;
- the A/A arm's time;
- the 1-, 5- and 15-minute load;
- the round's work;
- the contest's state after the round.

Each lock is recorded too.

x = log(t_AA / t_pref) is what an equal challenger sees in that round. Two checks show the
A/A arm stands in for a real challenger:

- Real challengers' within-contest spread matches it. Over the replays' three-round contests
  on one bank, the A/A arm had 0.173 on dev2, against 0.153 for n=4096 and 0.166 for q15=0.
  On dev1 it had 0.032, against 0.031 and 0.027.
- It runs at the round's far end, so its ratio spans the whole round. It is the noisiest a
  challenger can see.

No decision changes. There are three checks:

- `tests/test_choice.py` plays 65 contests with and without the arm, on a clock that gives
  each arm's runs the same times in both. They cover clear wins and their confirmation,
  equal arms, elimination, the cap, the budget, and 60 random contests. Every call's
  result, live set, confirmation, winner and samples are identical. The test fails on each
  of six deliberate breaks:
  - the A/A time as the preference's sample;
  - the A/A time averaged into it;
  - the A/A arm as a candidate;
  - the A/A arm moved next to the preference;
  - the A/A arm unsettled;
  - the order's parity counting it.
- 12 seeded cap67 replays with the arm and 12 without, on dev2 and on dev1, gave identical
  locks, block sizes, chains and Q15 settings. Every cost record other than the lock equals
  the seed. These contests are clear, so this check is weak on its own.
- All 9005 logged rounds (1247 trials) were fed, the A/A time left out, to a fresh `Choice`
  with the logged schedule. After every round its winner, dropped arms and confirmation
  matched the log.

A first version resolved arm configurations for the log while holding the trial lock. A
plan's `arm_config` takes that lock, so it deadlocked a seeded replay. The shipped version
records which run each candidate shares inside the loop. The fake subjects of
`tests/test_joint_trials.py` assert that no round resolves an arm under the lock, and a real
bank's trial runs with the log on to its lock.

## What was collected

| group | sets | rounds | contests | load (1-min) | preference's time per round |
|---|---|---|---|---|---|
| dev2 replay | cap67 replay: full, per-bank offsets, `MF_TRIAL_ROUNDS=40` | 3911 | 523 | 11-21 | 0.6-86 ms, median 5.7 |
| dev2 ladder | test27 CPU ladder: production length (default and `MF_TRIAL_ROUNDS=100`) and its first segments | 291 | 32 | 17-38 | 14-80 ms, median 23 |
| dev2 replay solo | offsets, one process at a time | 334 | 97 | 13-30 | median 3.6 ms |
| dev1 replay | as dev2 | 3610 | 497 | 1.4-8.1 | 1.1-50 ms, median 9.6 |
| dev1 ladder | as dev2 | 576 | 64 | 6.8-8.2 | 29-89 ms, median 51 |
| dev1 replay solo | as dev2 | 283 | 89 | 1.2-7.2 | median 6.5 ms |

A cap67 replay round is one bank's call. A ladder round is two banks' fine jobs of one
segment batch (`_ROUND_BANKS`). On dev2 the cores used, 28-31, are the SMT siblings of cores
12-15. Another workstream was assigned those cores, and other processes ran on them during
the collection; one was seen at 93% CPU on core 14 during the ladders. On dev1 the load was
almost all these jobs.

## The null

| group | sd | robust sd | P(x < log 0.95) [95% CI] | rounds 1 / 2 / 3 | later rounds, odd / even |
|---|---|---|---|---|---|
| dev2 replay | 0.170 | 0.077 | 0.273 [0.259, 0.287] | 0.396 / 0.228 / 0.317 | 0.279 / 0.217 |
| dev2 ladder | 0.178 | 0.070 | 0.261 [0.212, 0.316] | 0.406 / 0.406 / 0.344 | 0.208 / 0.192 |
| dev2 replay solo | 0.132 | 0.086 | 0.356 [0.305, 0.41] | 0.449 / 0.303 / 0.449 | 0.171 / 0.188 |
| dev1 replay | 0.030 | 0.024 | 0.037 [0.031, 0.044] | 0.079 / 0.027 / 0.052 | 0.024 / 0.029 |
| dev1 ladder | 0.085 | 0.064 | 0.247 [0.212, 0.284] | 0.328 / 0.172 / 0.156 | 0.260 / 0.260 |
| dev1 replay solo | 0.024 | 0.008 | 0 [0, 0.013] | 0 / 0 / 0 | 0 / 0 |

P(x < log 0.95) is the share of rounds that an equal challenger wins under the current rule.

**Load and work.** Within each group the 1-minute load shows no trend: for example, the
dev2 replay's robust sd ranges 0.064-0.092 across its load quintiles (11-21). The large
differences are between conditions:

- one process on dev1 against eight;
- the replay's short calls against the ladder's batches on the same eight dev1 cores;
- dev2's busy SMT siblings.

By round length, noise grows. On the dev2 replay the robust sd is 0.064 below 2.6 ms and
0.115 above 12 ms. On the dev2 ladder it is 0.039 at 14-19 ms and 0.19 at 31-80 ms. On the
dev1 ladder it is 0.065 against 0.094. A larger round does not buy precision here.

**Order.** On the loaded dev2 replay the A/A arm was 1.9% faster when it ran after the
preference and 0.2% slower when it ran before it. On the dev2 and dev1 ladders it was
0.4-0.9% faster in both positions, and on the dev1 replay within ±0.3%. So the paired
design's alternation cancels the average, but each round leans.

**Dependence.**

- Successive rounds correlate weakly (lag 1: -0.12 to 0.15).
- On dev2, contest means vary 1.06-1.55x what independent rounds give, which is a contest
  effect of sd 0.03-0.05. On dev1 it is 0.007 (replay) or none.
- The rates below assume independent rounds. The full report also gives each rate with that
  contest effect added; this counts it twice, so it is an upper bound.

## The current rule's false-switch rate

The current rule is TIE 5%, a 75% share, minimum 5 and cap 10, with exact elimination and
confirmation. The DP is checked against the library's own `paired_choice` and
`can_still_win` over every win/loss history (`tests/test_trial_power.py`). The first contest
draws rounds 1-3 from their own samples and later rounds by parity. The confirmation draws
from later rounds.

| group | one contest, m=1 | confirmed, m=1 | confirmed, m=2 | at the CI's upper end | with the contest effect |
|---|---|---|---|---|---|
| dev2 replay | 0.026 | 6.2e-4 | 1.2e-3 | 1.8e-3 | 0.044 |
| dev2 ladder | 0.032 | 6.6e-4 | 1.3e-3 | 5.0e-3 | 0.019 |
| dev2 replay solo | 0.030 | 1.8e-3 | 3.5e-3 | 0.011 | 0.076 |
| dev1 replay | 1.1e-5 | 9.5e-11 | 1.9e-10 | 7.3e-10 | 3.7e-8 |
| dev1 ladder | 0.013 | 2.0e-4 | 4.1e-4 | 1.3e-3 | 4.1e-4 |
| dev1 replay solo | <1e-12 | <1e-12 | <1e-12 | <1e-12 | <1e-12 |

m = 2 is the most common number of distinct challengers in a CPU bank round: n=4096 and
q15=0. n=model and q15=1 usually run the default's configuration.

On the logged sequences in their order (windows of the long contests), one contest switched:

- on the dev2 replay, in 4 of 232 ten-round and 4 of 110 twenty-round windows (the model:
  0.026 per contest);
- on the dev1 replay, in 0 of 225 and 0 of 108;
- in the ladders, in 0 of 20 and 0 of 40 ten-round windows.

Power with confirmation, cap 10:

| gain | 2% | 5% | 10% |
|---|---|---|---|
| worst group | 0.000 | 0.064 | 0.60 |
| best group | 0.007 | 0.112 | 1.000 |

A 5% gain sits on the tie, so the rule finds it about one time in ten. Raising the cap to 40
lifts the 10% power under the dev2 ladder null from 0.67 to 0.92, and leaves the 5% power
below 0.1.

## Candidate rules

Each candidate tests "the challenger is at least delta faster". It stops at the first look
that rejects, at the cap, or when no later boundary can be reached (exact futility).

- **Exact sign test, group-sequential.** It counts rounds with a ratio below 1 - delta. It
  uses one nominal level at every look from round 5, the largest whose overall error at the
  null's boundary (p = 1/2) is within alpha, computed by DP for the cap. Its error does not
  depend on the noise. It needs ceil(log2(m / alpha)) straight wins, so some (alpha, cap)
  pairs have no test.
- **Holm over the live arms.** The test uses alpha / m for the first rejection, the only one
  a choice makes. Confirmation is then not needed.
- **Paired t and Wilcoxon signed-rank on the log ratios.** They use one nominal level at
  every look, calibrated by simulating 100,000 null contests. On dev2's heavy-tailed null
  neither beats the sign test at the same alpha. At delta 2%, alpha 1e-2, cap 20, the 10%
  power on the dev2 replay is 0.55 (t) and 0.54 (Wilcoxon), against 0.68 for the sign test
  with Holm; on the dev2 ladder it is 0.65 and 0.72, against 0.81. On dev1 they are a little
  stronger: at 5% on the replay, 0.91 against 0.87; at 10% on the ladder, 0.89 against 0.83.
  Without a futility boundary both run to the cap at gain 0, and their rates far below 1e-3
  cannot be verified by simulation.

The D8 table puts each sign test against the current rule's measured rate under every
group's null ("every") and against the worst group's rate, 3.5e-3 ("worst"). Power is given
as worst group / best group. "Lost" is the number of rounds a challenger runs when it loses
every round, which is the usual case on the CPU.

| rule | every | worst | power 2% | power 5% | power 10% | rounds at 0 / 5% | lost |
|---|---|---|---|---|---|---|---|
| current (with confirmation) | - | - | 0.000 / 0.007 | 0.064 / 0.112 | 0.60 / 1.00 | 4.4 / 5.4 | 3 |
| sign, delta 0, alpha 1e-3, cap 20 | no | yes | 0.004 / 0.98 | 0.073 / 0.98 | 0.55 / 1.00 | 6.5 / 14.0 | 3 |
| sign, delta 1%, alpha 3e-3, cap 20 | no | yes | 0.002 / 0.75 | 0.083 / 0.99 | 0.56 / 1.00 | 5.6 / 12.8 | 3 |
| sign, delta 2%, alpha 1e-2, cap 20 | no | yes | 0.001 / 0.008 | 0.087 / 1.00 | 0.68 / 1.00 | 6.8 / 13.0 | 4 |
| sign, delta 2%, alpha 3e-3, cap 20 | no | yes | 0.000 / 0.003 | 0.039 / 0.99 | 0.50 / 1.00 | 5.2 / 13.4 | 3 |
| sign, delta 2%, alpha 1e-4, cap 20 | yes | yes | 0.000 / 0.000 | 0.004 / 0.88 | 0.18 / 0.99 | 3.7 / 16.1 | 2 |
| sign, delta 2%, alpha 1e-4, cap 40 | yes | yes | 0.000 / 0.000 | 0.013 / 1.00 | 0.67 / 1.00 | 11.8 / 26.4 | 7 |
| sign, delta 3%, alpha 3e-3, cap 20 | yes | yes | 0.000 / 0.000 | 0.014 / 0.99 | 0.43 / 1.00 | 4.8 / 12.3 | 3 |
| sign, delta 3%, alpha 3e-3, cap 40 | yes | yes | 0.000 / 0.000 | 0.027 / 1.00 | 0.90 / 1.00 | 15.2 / 27.1 | 10 |
| sign, delta 5%, alpha 3e-3, cap 20 | yes | yes | 0.000 / 0.000 | 0.000 / 0.003 | 0.15 / 0.99 | 4.5 / 6.5 | 3 |

The full table, and the sign, t and Wilcoxon tables per group, are in the report that
`tools/trial_power.py` writes.

**Overhead.** A round's cost is every run but the preference's timed one; each
configuration is settled and timed. It was:

| consumer | dev2 | dev1 |
|---|---|---|
| replay | 0.056 s | 0.081 s |
| ladder | 0.20 s | 0.40 s |

At 3 rounds for a clear loser, the current rule spends about 0.6 s of a dev2 ladder job.
That is within D2's 0.5% of a 319 s test27 job (about 1.5 s). Ten rounds (cap 40 at delta
3%) would spend about 2 s, which is over it. A futility boundary on "slower than the
preference" would decouple a loser's rounds from the cap. No candidate here has one.

## Recommendation (for the user's decision under D8)

Replace the 75% share and the confirmation with the exact group-sequential sign test of "at
least delta faster", with Holm over the live arms, at cap 20 (minimum 5, as now):

1. **alpha = 3e-3 per contest.** This is below the current rule's largest measured rate,
   3.5e-3 (dev2, two challengers, with confirmation). It holds at any load, where the
   current rule's rate ranged from below 1e-12 to 3.5e-3 with the noise.
2. **delta = 3%.** Of the deltas tried (0, 1, 2, 3 and 5%), this is the smallest at which
   that test's rate at gain 0 is no larger than the current rule's under every measured
   null. On quiet dev1 the current
   rule's rate is about 1e-10. delta 3% keeps the test at 9.6e-11 there, though not with
   the contest effect added (5.4e-7 against 3.7e-8).

   A smaller delta is not resolvable on a loaded node in any case:
   - the order and first-round leans are 1-2% on dev2, and the A/A arm was up to 8% faster in
     a ladder's first round;
   - the A/A spread alone puts an equal arm below 0.98 in 36-41% of dev2's rounds (22% on
     the dev1 replay).
3. **Cost.** A clear loser stops at round 3, as now. An equal arm runs 4.8 rounds, against
   4.4 now.

Effect: a 5% gain is found 0.014 (loaded dev2) to 0.985 of the time, against 0.06-0.11 now.
A 10% gain is found 0.43-1.0 of the time, against 0.60-1.0. It is better wherever the noise
allows, and worse for 10% gains on the loaded dev2.

If "no looser" means "no looser than the current rule's worst rate", then delta 2% at
alpha 1e-2 (Holm) and cap 20 suits:

- under every measured null it has at least the current rule's power, to within 0.002
  (5%: 0.087-1.0 against 0.064-0.112; 10%: 0.68-1.0 against 0.60-1.0);
- its largest rate is 9.5e-4;
- it costs one more round for a clear loser (4 against 3).

Either way, the relevance problem above, where the first bank decides for the job, is
larger than the statistical errors measured here. It belongs to the step 7 design (which
work a trial samples) or to step 3, not to alpha.

## Not covered

- GPU trial kinds (the device and single-template trials, and the Vulkan subgroup size,
  which is decided from subprocess timings and has no play) are not covered. They come in
  wave 2, when the GPU is free. The diagnostic runs on them, but its GPU path is untested
  here: GPU tests skip with the GPU hidden.
- Standalone `HierarchicalFilter` plan trials run in neither consumer, so none were logged.
- The independent-rounds model's rates below about 1e-3 rest on its tails. The logged
  sequences resolve only about 1/200 per contest. The dev2 contest effect could raise the
  current rule's rate there by up to 30x; that bound counts the effect twice.
