# A/A rounds on the GPU: the paired rule's error and power, 2026-10-30

This page covers the GPU trials that
[the CPU page](trial-statistics.md) left out. It measures the paired rule's null on three
GPUs, and from that the current rule's false-switch rate and power. It decides nothing new:
under D8 the current rule stays (see the last section). Its main finding concerns the
measurement, not the rule. On two of the three GPUs, the arm played first in a round reads
up to 13-20% slower than the same configuration played later in it. On the third, plays of
1-3 ms timed by the host clock give an equal arm a log ratio of standard deviation
0.25-0.33. Both hide gains of 5-10%.

The library was at 2b595add (main). The evidence and how it was collected are in
[measurements/trial-aa-gpu-20261030](measurements/trial-aa-gpu-20261030/README.md).
`tools/trial_power.py` regenerates every number here from it.

## Summary

- **Three GPU trial kinds play rounds in the test27 ladder:**
  - `joint` is the bank trial over block size (n = 2048, 4096 and the model's choice);
  - `gpu-single` runs a single-template call on the GPU against the CPU;
  - `gpu-kernels` chooses among kernel variants.

  The Vulkan subgroup size is decided from subprocess timings and has no play, so it is not
  covered.
- **The null depends on the device and on the kind.** The table gives the robust sd of an
  equal arm's log ratio per round:

  | | joint | gpu-single | gpu-kernels |
  |---|---|---|---|
  | dev2 (Radeon 8060S, RADV) | 0.093 | 0.138 | 0.053 |
  | dev3 (Radeon Renoir, RADV) | 0.203 | 0.084 | 0.010 |
  | dev4 (Iris Xe, ANV) | 0.041 | 0.233 | 0.005 |

  A play's median time sets most of this. The kernel trial's plays take 82-113 ms on dev3
  and dev4 and are quiet there; on dev2, the fastest GPU, they take 9 ms. The other kinds'
  plays take 6-11 ms on dev3 and dev4, and 1-3 ms on dev2 (joint: median 1.1 ms). A trial
  times its plays by the host clock.
- **On dev3 and dev4 the arm played first in a round is slower.** Every arm gets an
  untimed run right before its timed run (`Choice.play`), so this is not a cold first call.
  The table gives the mean log ratio of the A/A arm (the preference run again) to the
  preference:

  | | A/A played after the preference | A/A played before |
  |---|---|---|
  | dev3 joint | -0.151 | +0.132 |
  | dev3 gpu-single | -0.054 | -0.003 |
  | dev4 gpu-single | -0.200 | +0.137 |
  | dev4 joint | -0.025 | +0.022 |
  | dev2 joint | -0.043 | -0.037 |

  Real challengers show it too. Against the GPU, dev4's CPU arm of `gpu-single` reads
  +0.145 when played first and -0.095 when played second, and dev3's reads +0.183 and
  +0.086. On dev2 the order makes no difference, but the noise is larger: the sd of the
  log ratio is 0.25-0.33 there.
- **It is not a clock ramp.** On dev3, an isolated GPU call after an idle gap ran 1.16x
  slower after 20 ms and 1.54x after 100 ms, and was steady from the second call on. A
  play of four submissions with 1-5 ms of host work between them was steady from the
  second play on, after gaps of up to 500 ms (`harness/drift.py`, `drift2.py`). The ladder's
  rounds are slower first for some other reason, which is not identified here.
- **The current rule's false-switch rate is up to 4.1e-3 per contest on the GPU.** The CPU
  page's worst is 9.1e-4. Alternation hides most of the position effect: the rule needs a
  75% share of rounds, and an arm played first in half of them rarely gets one. Per group,
  with its confirmation (m: the equal challengers the group's trial has):

  | group | false switch per contest | at every sample's 95% upper end | power, 5% gain | power, 10% gain |
  |---|---|---|---|---|
  | dev2 joint | 1.1e-3 | 0.011 | 0.112 | 0.735 |
  | dev2 gpu-single | 6.2e-4 | 0.010 | 0.029 | 0.210 |
  | dev2 gpu-kernels (m = 3) | 1.6e-4 | 0.0021 | 0.041 | 0.598 |
  | dev3 joint | 4.1e-3 | 0.033 | 0.075 | 0.339 |
  | dev3 gpu-single | 1.9e-3 | 0.014 | 0.089 | 0.658 |
  | dev3 gpu-kernels (m = 3) | below 1e-12 | 9.8e-11 | 0.083 | 1.000 |
  | dev4 joint | 5.1e-9 | 1.7e-5 | 0.037 | 0.993 |
  | dev4 gpu-single | 9.1e-4 | 0.012 | 0.081 | 0.340 |
  | dev4 gpu-kernels (m = 3) | below 1e-12 | 2.9e-10 | 0.052 | 1.000 |

  On the logged sequences, a contest without confirmation switched about as often as the
  model expects; for example, 2 of dev3's 20 ten-round joint windows switched where the model
  expects 1.25 ([report](measurements/trial-aa-gpu-20261030/report.md), "The current
  rule's false-switch rate").
- **The power is what the GPU measurement costs.** On the CPU the rule's power is 0.57-1.0
  for a 10% gain. Here it is 0.21-0.34 in three groups: dev2 gpu-single, dev3 joint and dev4
  gpu-single.

## What was collected

On each GPU, one ladder process at a time ran the test27 production bank with the H1
profiles (`tools/ladder.py --device gpu:0 --pipeline --pure`), a fresh cost file, and the
A/A diagnostic on (`MF_TRIAL_AA_LOG`):

| set | what ran | per host |
|---|---|---|
| `gshort` | `--tops 1 --segments 4`: a process's first fine batches, so its first contests | 24 |
| `glad` | `--tops 9 --segments 28` | 4 |
| `gladlong` | as `glad`, at `MF_TRIAL_ROUNDS=100` (contests of up to 51 rounds) | 4 |

There were 96 jobs, all exiting with status 0, giving 3179 records. The 1-minute load at the
jobs' starts and ends was 1.4-3.5 on dev2 (another workstream's processes on other cores),
0.1-4.6 on dev3 and 0.0-0.9 on dev4. The groups are by machine and trial kind, pooled over
the sets, since the kinds' nulls differ more than the sets' do.

## Decision under D8: the current rule stays

D8 admits a replacement only if it is no looser than the current rule's measured
false-switch rate. The report prices exact group-sequential sign tests at several deltas,
alphas and caps, and paired t and Wilcoxon tests. Only one candidate meets that rate in every
group, a sign test with delta 0.015, alpha 1e-4 and cap 30, and it does not keep the current
rule's power: it is 0.33 short at 10% on dev4 gpu-single. So the current rule stays on the
GPU, as it does on the CPU.

What would raise the power is a better measurement, not a different rule. The next steps
are open:

- Find what makes a round's first timed run slow on dev3 and dev4, and remove it or cancel
  it. For the joint trial this is done (see the follow-up below); `gpu-single` is open.
- Make dev2's plays long enough to time, or time them by the device's own timestamps: a
  play of 1-3 ms by the host clock carries noise of the same size as the gains it is meant
  to find. For the joint trial the settle halved it (below).
- Measured GPU choices that move only a few percent are not trustworthy until then. The
  GPU chains of any length (roadmap step I) wait on this: there a model choice that is
  1-2% wrong cost 4-5% of the fine stage, and a trial would not resolve it.

## Follow-up: the joint trial's settle

The joint trial's position effect had a cause the library could remove. Every timed run
already followed an untimed one, but a GPU joint round's untimed run (its settle) replayed
the batch only until it built no more recordings. That was one replay, since Vulkan's fused
batches were not counted as built. Each round replays other banks than the round before
(two of the batch's, rotated), so a round's first use of a configuration rebuilt its
recordings, and the batch then ran 10-25% slower for a replay or two after it had built
everything. Logged run by run on dev3, a configuration's second use in a round was 9-11%
faster than its first. The A/A arm, always a second use, looked fast after the preference
and slow before it. Neither a lead-in run per round nor a palindromic order removed it; a
settle to a steady time did.

The settle now replays until a replay builds nothing and runs within half the tie (2.5%)
of the replay before, at most five replays, and fused batches count as built. Short
ladders, 24 per GPU, before (the `gshort` set above) and after
([settle](measurements/trial-aa-gpu-20261030/settle/README.md)), joint trial only:

| | equal arm's sd | A/A after / before the preference | false switch per contest | power, 10% gain | job wall (s) |
|---|---|---|---|---|---|
| dev2 before | 0.309 | -0.044 / -0.150 | 3.5e-6 | 0.013 | 14.2 |
| dev2 after | 0.154 | -0.042 / +0.004 | 3.2e-9 | 0.980 | 14.1 |
| dev3 before | 0.236 | -0.210 / +0.206 | 0.15 | 0.407 | 41.2 |
| dev3 after | 0.097 | -0.027 / -0.028 | 4.5e-3 | 0.728 | 41.0 |
| dev4 before | 0.024 | -0.012 / -0.018 | 7.4e-10 | 1.000 | 50.8 |
| dev4 after | 0.022 | +0.001 / +0.016 | below 1e-12 | 0.991 | 50.8 |

These are the first contests of a process only, which is why dev3's rate before (0.15) is
far above the whole collection's (4.1e-3). The A/A arm is still a configuration's second use
in its round, so on dev3 it still reads 3% fast either way; real arms are both first uses.
`gpu-single` is not changed. Its call is a single-template follow-up, which in production
pays the device's wake from idle, so what it should time is a policy question; its order
effect stands (dev4: the CPU arm +0.46-0.51 played first, +0.03-0.18 played second).

## Not covered

- The Vulkan subgroup size (no play) and Metal and CUDA trials (no hardware in the fleet
  collection).
- Concurrent GPU jobs. Each host ran one ladder at a time, while production runs one job per
  GPU.
