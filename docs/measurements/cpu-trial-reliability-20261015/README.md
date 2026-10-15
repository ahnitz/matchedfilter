# CPU trial reliability, 2026-10-15

**Integration status:** the final source passes the full test suite, but its final
hardware gate fails the replay requirement for a selected 4096-point GPU layout.
The same failure reproduces on baseline `539266ed` with identical trial locks:
54 synchronous jobs, no GPU trace, zero segment replays, and CPU/GPU output
agreement. This branch is not merge-ready; the GPU replay issue and authenticated
GitHub CI dispatch remain outstanding.

Base: `539266ed`. Timing host: dev1, Ryzen 5950X / AVX2, CPU 6,
`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`.
The test27 cap401 ladder uses top id 4, 4,698 fine templates, two detectors,
and synthetic input colored by the H1 profiles. It is not a full PyCBC job.

## Cold starts

The ten independent fresh-cost-file starts in [study-v1/summary.json](study-v1/summary.json)
selected Q15 **on 10/10 times**. Each used one calibration process and one
accepted steady process (six segments per process, two nominal warmup segments).
The second process changed no trial lock and recorded **zero** CPU trial calls
or seconds after its steady boundary. Accepted throughput ranged from
4.9185e6 to 4.9523e6 templates in real time (median 4.9393e6).

First-process nominal steady windows contained 23.09–26.39 seconds of CPU trial
work. Those timings are deliberately excluded from accepted throughput. The
change does not make the first process cheap; it makes the comparisons comparable,
bounds the number of rounds, persists progress, and identifies contaminated timing.
The historical ladder's printed warmup total sums overlapping stage/wall/CPU
counters; use the raw `prep` and `segment` fields when assessing startup wall time.

The ten-start prototype stored block medians in seconds. Final code normalizes
both arms by the same batch-work count to preserve the optional steady-recheck
units. This leaves every paired ratio unchanged. The normalized source gets its own
additional cold-start confirmation and is used for the forced-lock throughput
comparison. A final three-candidate decision fix ensures that a noisy lowest median
cannot hide another consistently faster challenger; it receives another independent
cold-start confirmation. That helper never runs in the forced-lock timing controls.
Source hashes distinguish these versions; no kernel code changed.

Raw per-process reports and final cost files are in `study-v1/`.
[cold-study-analysis.json](cold-study-analysis.json) summarizes the ten starts.
The bounded driver is [tools/cpu_trial_check.py](../../../tools/cpu_trial_check.py):

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  taskset -c 6 python tools/cpu_trial_check.py \
  --bank BANK.hdf --profiles PROFILES.npz --out NEW_DIRECTORY --starts 10
```

## Controls and validation

[throughput-study.py](throughput-study.py) retains the exact experiment driver and
its historical dev1 paths. It uses a separate baseline tree from `539266ed` and
the frozen normalized Python source (before the final three-candidate decision
fix), with the **same native extension** in both.
Each process starts with an identical copied cost file, forcing Q15 on or off.
Every resulting trial-lock dictionary must equal the input before any throughput
is attributed to code. Four alternating rounds run each arm at each Q15 setting,
with ten segments per process and the first two excluded.

[dev2-full-gate.log](dev2-full-gate.log) records the complete hardware gate:
1,946 tests passed and 165 individual tests skipped; all gate stages ran, including
batched and pipelined CPU/GPU agreement, replay, dismissal margins, five
reproducibility repetitions, and five follow-up repetitions. The final telemetry
normalization and two additional output-equivalence tests also receive a fresh
full-suite run. Focused paired-trial tests pass on AVX3, AVX2, and SSE4.

The CPU chain scheduler was audited, not redesigned. It still pools unrelated
calls and has heterogeneous candidate feasibility. The limitations and follow-up
are documented in [gate-model.md](../../gate-model.md#cpu-paired-trials-and-bounded-measurement-2026-10-15).

## Forced-lock throughput result

| Q15 lock | Baseline mean throughput | Candidate mean throughput | Median paired candidate / baseline |
|---|---:|---:|---:|
| on | 4.9261e6 | 4.9064e6 | 0.99799 |
| off | 3.9225e6 | 3.9264e6 | 0.99838 |

Median paired throughput was approximately **0.2% lower** for the candidate in
both controls. Individual ratios ranged from 0.9879 to 1.0152 across the two
settings; the record does not establish zero overhead. With identical remaining
locks, Q15 on improved the candidate's mean whole-ladder throughput **24.96%**
over Q15 off. The intended benefit is selecting that configuration reliably.
All sixteen runs reported the same 907 fine triggers and 181 follow-up calls;
this is count equality, not an assertion of bitwise output identity.

[throughput-analysis.json](throughput-analysis.json) contains the paired ratios.
[paired-throughput-v1/summary.json](paired-throughput-v1/summary.json) retains
all trial-lock dictionaries, native hashes, timings, and counts. Every run used
the same native SHA256 (`a126c02a12c0a5092dfc528493d180d8773fd2e6779c4ae1c37fbafd00f16d7d`).

## Final-code confirmation

[final-v2-cold-confirmation/summary.json](final-v2-cold-confirmation/summary.json)
records an additional independent fresh-cost-file start of the exact final Python
source. It selected Q15 on, settled in two processes, and measured zero CPU trial
work after the second process's steady boundary. The source hashes on dev1 match
[final-source-sha256.txt](final-source-sha256.txt) exactly. The earlier normalization
confirmation is retained separately in `final-cold-confirmation/`.

## Final gate replay blocker

[gpu-replay-baseline-control.json](gpu-replay-baseline-control.json) compares the
unchanged baseline and candidate with copies of the failing gate's exact cost
file. Trial locks remained identical. Both report 1,002 fine triggers, 206
follow-up calls, zero segment replays, zero capture failures, and zero one-sided
CPU/GPU peaks (maximum SNR difference 1.59e-5). Debug output says `devices 0 sync
jobs 54 untraced 0`: the selected GPU configuration does not produce a replayable
trace. The earlier passing gate selected a 2048-point GPU configuration; the
failing one selected 4096. The gate's suggestion that trials had not locked is
not the cause: the relevant block and chain locks are present.

This is a baseline GPU limitation, not evidence that the CPU trial patch is
merge-ready. No candidate was removed and no lock was changed to make the gate
pass. The final gate log and both debug reproductions are retained alongside
this report for the GPU implementation owner.

The final-source gate is [dev2-final-full-gate.log](dev2-final-full-gate.log):
**1,949 passed, 165 individual tests skipped**; batched/pipelined agreement,
margin, all five reproducibility runs, and all five follow-up runs passed.
Only replay failed, as reproduced above. [validation.json](validation.json)
records the final status. GitHub CI could not be dispatched because neither the
CLI nor browser was authenticated; no merge was performed.
