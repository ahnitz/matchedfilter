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
and `tools/trial_power.py` regenerates every number here from it. GPU trials are on
[their own page](trial-statistics-gpu.md).

## Summary

- **The noise is set by the machine's state.** The robust sd of an equal arm's log ratio
  per round was:
  - 0.008 for one process on a quiet dev1;
  - 0.024 with eight of these jobs on dev1, and 0.064 in eight concurrent production-length
    ladders;
  - 0.032-0.044 on dev2 at load 3-8, and 0.070-0.086 at load 11-38, when the cores' SMT
    siblings were busy.

  Within one condition it shows no trend with the 1-minute load. In the loaded groups longer
  rounds are noisier, not quieter. Even at low load, an equal arm beats the 5% tie in 19-23%
  of dev2's rounds, against 4% on dev1's replay.
- **A process's first rounds are noisier, and they favour the arm run later.** In round 1,
  an equal arm beat the 5% tie in 31-51% of rounds on dev2 and in the dev1 ladders, against
  4-28% later; on the dev1 replay the figures are 8% against 2-3%. In the short ladders the
  A/A arm, run last, was 3-8% faster in round 1. Production contests are exactly these
  rounds: on most banks the CPU's challengers are 1.1-2.2x slower, so elimination ends the
  contest at round 3.
- **The current rule's false-switch rate follows the noise.** With its confirmation, for
  the two distinct challengers a CPU bank trial has, the rate per contest was
  ([report](measurements/trial-aa-20261029/report.md), "The current rule's false-switch
  rate"):

  | condition | rate per contest | with the contest effect |
  |---|---|---|
  | loaded dev2 replay | 2.7e-4 to 9.1e-4 | 0.044-0.057 |
  | loaded dev2 ladder | 4.7e-4 | 0.018 |
  | dev2 at load 3-8 | 6.4e-7 to 2.7e-5 | up to 3.4e-4 |
  | dev1 ladder | 5.0e-4 | 5.0e-4 |
  | dev1 replay | 4.7e-11 | 1.8e-8 |
  | dev1 with one process | below 1e-12 | below 1e-12 |

  Its power is 0.02-0.07 for a 5% gain and 0.57-1.0 for a 10% gain. On the logged A/A
  sequences, one contest (before confirmation) switched in 4 of 232 ten-round windows on
  the dev2 replay, where the model expects 5.0.
- **An exact sign test has an error rate that does not depend on the noise's spread.** It
  is a group-sequential test of "at least delta faster", computed by DP for the cap, with
  Holm over the live arms. Re-testing a fixed-n sign test every round gives 0.051, 0.099
  and 0.145 at caps 10, 20 and 40 for a nominal 0.05, reproducing the critique; the
  group-sequential boundary holds 0.05.
- **D8 keeps the current rule.** D8 admits a replacement only if it is no looser than the
  current rule's measured false-switch rate. No sign test tried (delta 0-5%, alpha 1e-4 to
  5e-2, caps 20-40) is no looser than it under every group's null and also keeps its power
  at 5% and 10%; none is no looser under every group once the contest effect is added; and
  the ones that keep its power cost 10-18 rounds at gain 0 against its 4.4. The current
  rule's numbers (TIE 5%, the 75% share, minimum 5 and cap 10, confirmation) therefore stay,
  now with their measured error and power above, instead of standing without a measurement.
- **A larger error is outside this test's reach.** The pooled bank trial lets the first
  bank it plays decide for the whole job. Replays started at other banks locked q15=0 or
  q15=1 in 28 of 323 (dev2) and 15 of 323 (dev1) runs, and in 8, 7 (dev2 at low load) and 4
  of 81 solo runs. On that bank those arms really were faster: their median ratio to the
  default was 0.37-0.91. On the job as a whole the screen pays: 2026-10-26 measured Q15 off
  18-46% slower.

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

x = log(t_AA / t_pref) is what an equal challenger sees in that round. Real challengers'
within-contest spread of the log ratio is close to the A/A arm's on dev2: 0.169 for the
A/A arm on the replay, against 0.147 (n=4096) and 0.183 (q15=0); at low load 0.075 against
0.064 and 0.072. On dev1 some real arms are noisier than the A/A arm: q15=0 on the replay
(0.062 against 0.031) and n=4096 on the ladder (0.160 against 0.079). There the A/A null
may understate a real arm's noise, and dev1's rates are the less certain.

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
- All 9494 logged rounds (1361 trials) were fed, the A/A time left out, to a fresh `Choice`
  with the logged schedule. After every round its winner, dropped arms and confirmation
  matched the log, and every lock matched. With the A/A time put in the preference's place,
  640 rounds disagree, so the check discriminates (`harness/refeed_evidence.py`).

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
| dev2 ladder, low load | as the dev2 ladder: 2 production-length runs at `MF_TRIAL_ROUNDS=100`, 24 short ones one at a time | 174 | 26 | 4.9-8.2 | 11-23 ms, median 18 |
| dev2 replay solo, low load | as the dev2 replay solo | 315 | 95 | 3.2-6.8 | median 2.6 ms |
| dev1 replay | as dev2 | 3610 | 497 | 1.4-8.1 | 1.1-50 ms, median 9.6 |
| dev1 ladder | as dev2 | 576 | 64 | 6.8-8.2 | 29-89 ms, median 51 |
| dev1 replay solo | as dev2 | 283 | 89 | 1.2-7.2 | median 6.5 ms |

A cap67 replay round is one bank's call. A ladder round is two banks' fine jobs of one
segment batch (`_ROUND_BANKS`). On dev2 the cores used, 28-31, are the SMT siblings of cores
12-15. Another workstream was assigned those cores, and other processes ran on them during
the main collection; one was seen at 93% CPU on core 14 during the ladders. The low-load
sets ran an hour later, when the load (3-8) was mostly another workstream's four processes
on cores 24-27. On dev1 the load was almost all these jobs.

## The null

| group | sd | robust sd | P(x < log 0.95) [95% CI] | rounds 1 / 2 / 3 | later rounds, odd / even |
|---|---|---|---|---|---|
| dev2 replay | 0.170 | 0.077 | 0.273 [0.259, 0.287] | 0.396 / 0.228 / 0.317 | 0.279 / 0.217 |
| dev2 ladder | 0.178 | 0.070 | 0.261 [0.212, 0.316] | 0.406 / 0.406 / 0.344 | 0.208 / 0.192 |
| dev2 replay solo | 0.132 | 0.086 | 0.356 [0.305, 0.41] | 0.449 / 0.303 / 0.449 | 0.171 / 0.188 |
| dev2 ladder, low load | 0.051 | 0.044 | 0.19 [0.134, 0.256] | 0.308 / 0.077 / 0.308 | 0.146 / 0.167 |
| dev2 replay solo, low load | 0.074 | 0.032 | 0.232 [0.186, 0.282] | 0.511 / 0.114 / 0.159 | 0.107 / 0.043 |
| dev1 replay | 0.030 | 0.024 | 0.037 [0.031, 0.044] | 0.079 / 0.027 / 0.052 | 0.024 / 0.029 |
| dev1 ladder | 0.085 | 0.064 | 0.247 [0.212, 0.284] | 0.328 / 0.172 / 0.156 | 0.260 / 0.260 |
| dev1 replay solo | 0.024 | 0.008 | 0 [0, 0.013] | 0 / 0 / 0 | 0 / 0 |

P(x < log 0.95) is the share of rounds that an equal challenger wins under the current rule.

**Load and work.** Within each group the 1-minute load shows no trend: for example, the
dev2 replay's robust sd ranges 0.064-0.092 across its load quintiles (11-21). The large
differences are between conditions:

- one process on dev1 against eight;
- the replay's short calls against the ladder's batches on the same eight dev1 cores;
- dev2 at load 3-8 against dev2 with busy SMT siblings: the robust sd halves (0.032-0.044
  against 0.070-0.086), but an equal arm still wins 19-23% of rounds.

By round length, noise grows. On the dev2 replay the robust sd is 0.064 below 2.6 ms and
0.115 above 12 ms. On the dev2 ladder it is 0.039 at 14-19 ms and 0.19 at 31-80 ms. On the
dev1 ladder it is 0.065 against 0.094. At low load on dev2 it shows no trend either way
(0.025-0.058 across the quintiles of both groups). A larger round does not buy precision
here.

**Order.** On the loaded dev2 replay the A/A arm was 1.9% faster when it ran after the
preference and 0.2% slower when it ran before it; at low load on dev2 it was 1.4-2.8%
faster after it and within 0.2% before it. On the loaded dev2 and dev1 ladders it was
0.4-0.9% faster in both positions, and on the dev1 replay within ±0.3%. So the paired
design's alternation cancels the average, but each round leans.

**Dependence.**

- Successive rounds correlate weakly (lag 1: -0.12 to 0.15).
- On the loaded dev2, contest means vary 1.06-1.55x what independent rounds give, which is
  a contest effect of sd 0.03-0.05. At low load on dev2 it is 0.014 (ladder) or none; on
  dev1 it is 0.007 (replay) or none.
- The rates below assume independent rounds. The full report also gives each rate with that
  contest effect added; this counts it twice, so it is an upper bound.

## The current rule's false-switch rate

The current rule is TIE 5%, a 75% share, minimum 5 and cap 10, with exact elimination and
confirmation. The DP is checked against the library's own `paired_choice` and
`can_still_win` over every win/loss history (`tests/test_trial_power.py`), and its
composition for two challengers with confirmation against 200,000 contests played by the
library's `Choice` (`harness/mc_choice.py`). The first contest draws rounds 1-3 from their
own samples and later rounds by parity. The confirmation draws from later rounds.

| group | one contest, m=1 | confirmed, m=1 | confirmed, m=2 | at the CI's upper end | with the contest effect |
|---|---|---|---|---|---|
| dev2 replay | 0.026 | 4.6e-4 | 9.1e-4 | 2.0e-3 | 0.044 |
| dev2 ladder | 0.032 | 2.4e-4 | 4.7e-4 | 8.2e-3 | 0.018 |
| dev2 replay solo | 0.030 | 1.4e-4 | 2.7e-4 | 0.015 | 0.057 |
| dev2 ladder, low load | 5.2e-3 | 1.3e-5 | 2.7e-5 | 3.7e-3 | 3.4e-4 |
| dev2 replay solo, low load | 2.0e-3 | 3.2e-7 | 6.4e-7 | 1.1e-3 | 6.4e-7 |
| dev1 replay | 1.1e-5 | 2.3e-11 | 4.7e-11 | 9.0e-10 | 1.8e-8 |
| dev1 ladder | 0.013 | 2.5e-4 | 5.0e-4 | 4.7e-3 | 5.0e-4 |
| dev1 replay solo | <1e-12 | <1e-12 | <1e-12 | 2.2e-7 | <1e-12 |

m = 2 is the most common number of distinct challengers in a CPU bank round: n=4096 and
q15=0. n=model and q15=1 usually run the default's configuration.

On the logged sequences in their order (windows of the long contests, which are later
rounds), one contest switched:

- on the dev2 replay, in 4 of 232 ten-round and 4 of 110 twenty-round windows (the model
  of later rounds: 0.018 per contest);
- on the dev2 ladder at low load, in 1 of 10 ten-round windows (two processes' 51-round
  contests; the model: 0.003);
- on the dev1 replay, in 0 of 225 and 0 of 108;
- in the loaded ladders, in 0 of 20 (dev2) and 0 of 40 (dev1) ten-round windows.

Power with confirmation, cap 10:

| gain | 2% | 5% | 10% |
|---|---|---|---|
| worst group | 0.000 | 0.023 | 0.57 |
| best group | 0.003 | 0.074 | 0.998 |

A 5% gain sits on the tie, so the rule finds it about one time in ten. Raising the cap to 40
lifts the 10% power under the dev2 ladder null from 0.67 to 0.92 (dev1 ladder: 0.76 to
0.94), and leaves the 5% power below 0.1.

## Candidate rules

Each candidate tests "the challenger is at least delta faster". It stops at the first look
that rejects, at the cap, or when no later boundary can be reached (exact futility).

- **Exact sign test, group-sequential.** It counts rounds with a ratio below 1 - delta. It
  uses one nominal level at every look from round 5, the largest whose overall error at the
  null's boundary (p = 1/2) is within alpha, computed by DP for the cap. Its error does not
  depend on the spread of the noise, only on the rounds' median staying above 1 - delta,
  which the order's lean can move by 1-3% on dev2. It needs ceil(log2(m / alpha)) straight
  wins, so some (alpha, cap) pairs have no test.
- **Holm over the live arms.** The test uses alpha / m for the first rejection, the only one
  a choice makes. Confirmation is then not needed.
- **Paired t and Wilcoxon signed-rank on the log ratios.** They use one nominal level at
  every look, calibrated by simulating 100,000 null contests. Neither is better than the
  sign test throughout. At delta 2%, alpha 1e-2, cap 20:
  - the sign test is stronger on the loaded dev2: 10% power on the replay 0.68 against 0.54
    (t) and 0.54 (Wilcoxon), on the ladder 0.81 against 0.66 and 0.72;
  - t and Wilcoxon are stronger on the dev1 ladder (10%: 0.88 and 0.87 against 0.83) and on
    the low-load dev2 ladder (5%: 0.46 and 0.53 against 0.29).

  Without a futility boundary both run every contest to the cap, a clear loser's too (20
  rounds against 3-4), and their rates far below 1e-3 cannot be verified by simulation.

The D8 table in the [report](measurements/trial-aa-20261029/report.md) puts each sign test
against the current rule's measured rate under every group's null ("every") and against the
worst group's rate ("worst"), both also with the contest effect added. "Keeps power" means its
power at 5% and 10% is at least the current rule's under every group's null, with no
tolerance. Its verdict is summarised in the decision below: no rule both meets "every" and
keeps the power, and none meets "every" with the contest effect.

The full table, and the sign, t and Wilcoxon tables per group, are in the report that
`tools/trial_power.py` writes.

**Overhead.** A round's cost is every run but the preference's timed one; each
configuration is settled and timed. It was:

| consumer | dev2 | dev2, low load | dev1 |
|---|---|---|---|
| replay | 0.056 s | 0.030 s (solo) | 0.081 s |
| ladder | 0.20 s | 0.13 s | 0.40 s |

At 3 rounds for a clear loser, the current rule spends about 0.6 s of a loaded dev2 ladder
job. That is within D2's 0.5% of a 319 s test27 job (about 1.5 s). Four rounds spend about
0.8 s; six (cap 30) about 1.2 s; ten (cap 40 at delta 3%) about 2 s, which is over it. On
dev1 a round costs twice as much; its test27 job length was not measured here. A futility
boundary on "slower than the preference" would decouple a loser's rounds from the cap. No
candidate here has one.

## Decision under D8: the current rule stays

The tables in the [report](measurements/trial-aa-20261029/report.md) were regenerated after
two corrections from review: a confirmation's null draws from the later rounds only (it had
mixed a process's first rounds, the noisiest, back in), and a rule keeps the current rule's
power only if it is short nowhere (a 0.002 tolerance with no origin was removed). With them:

- Every exact sign test that keeps the current rule's power at 5% and 10% is looser than the
  current rule under at least one group's null.
- Every test that is no looser under every group loses power the current rule has (for
  example delta 3%, alpha 3e-3, cap 30: 0.034 short at 5% on the dev2 ladder).
- None is no looser under every group with the contest effect added.
- The candidates that keep power need 10-18 rounds at gain 0, against 4.4.

So the current rule is kept. What this step changes is that its factors now have a measured
basis: the false-switch rate and power under every measured null, from the A/A arm, and the
tool that regenerates them (`tools/trial_power.py`) for any new collection.

## Not covered

- GPU trial kinds are not covered here; [the GPU page](trial-statistics-gpu.md) covers the
  three that play rounds (the bank trial on a GPU, the single-template trial and the kernel
  trial). The Vulkan subgroup size is decided from subprocess timings and has no play.
- Standalone `HierarchicalFilter` plan trials run in neither consumer, so none were logged.
- The independent-rounds model's rates below about 1e-3 rest on its tails. The logged
  sequences resolve only about 1/200 per contest. The dev2 contest effect could raise the
  current rule's rate there by up to 30x; that bound counts the effect twice.
- dev2 at low load was sampled once, for 20 minutes, with another workstream's load on
  other cores; it is one more condition, not a quiet machine.
