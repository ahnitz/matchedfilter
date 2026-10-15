# CPU survivor processing, 2026-10-14

This pass compares the CPU implementation with `ff5911cd` on one Ryzen AI Max+ 395
(Zen 5) core. It changes three pieces of work without changing the gate thresholds,
the Q15 error margin, or the refinement policy:

- Pooled float batches read a shared data spectrum directly. Aligned contiguous
  template runs reuse their existing packed storage. Arbitrary pair lists still
  gather the required inputs.
- The N256 fixed-stride Q15 path reaches the fused maximum selection. A generated
  codelet removes window tests for the twelve interior outputs that are guaranteed
  to be included when the window contains `[32, 224)`.
- Q15 compaction finishes rejected output rows immediately. The subsequent float
  decision loop visits only the compacted survivors, avoiding a second scan of all
  pairs and its per-pair integer division.

## Representative ladder workload

The workload uses `fir_three_level_modern_v1_bottomup_cap401.hdf` and H1 reference
profiles with `tools/ladder.py`: one top bank (id 4), 4,698 fine templates across
27 middle groups, two detectors, 512-second segments with 376 seconds analyzed,
seed 1, n=2048, chain 256/512/1024, threshold 6, and dismissal budget 1e-3.
Inputs are synthetic data colored by the real profiles. This is a public API
workload analogue, not an execution of the entire PyCBC search.

Each fresh process warms one segment and measures three. Q15 is fixed on, autotuning
is disabled, and direct refinement uses the real bank taps. Processes alternate
baseline, pooled+Q15, all changes, then reverse the order. AVX3 is pinned to core 4;
BLAS and OpenMP use one thread. Other checks used separate physical cores on the
same shared machine, so the paired comparisons matter more than absolute timings.

| Build | Fine stage, ms/segment | Whole segment, ms |
|---|---:|---:|
| Baseline | 330.94, 324.70 | 396.39, 390.25 |
| Pooled inputs + Q15 maximum | 315.35, 310.64 | 380.77, 376.59 |
| Plus survivor compaction | 307.14, 311.17 | 374.25, 377.14 |

Across these paired runs, all three changes give 1.060x fine throughput and 1.047x
whole-segment throughput. Fine and follow-up output hashes match exactly across
all six runs. The [measurement summary](measurements/cpu-survivors-20261014/summary.json)
records configuration, build hashes, stage costs, and an additional confirmation pair.
That separate pair improved fine time only 0.5% and whole-segment time 0.6%; the
earlier aggregate is an observed result, not a reliable gain for every run.

A final longer comparison stopped the other test jobs and used seven steady segments
per process, in baseline/candidate/candidate/baseline order:

| Build | Fine stage, ms/segment | Whole segment, ms |
|---|---:|---:|
| Baseline | 321.749, 320.511 | 388.920, 386.531 |
| All changes | 311.578, 310.081 | 379.295, 377.728 |

The means are 321.130 to 310.829 ms for the fine stage and 387.725 to 378.512 ms
for the whole segment: **1.033x fine throughput and 1.024x whole-segment throughput**.
These are the headline results. All fine and follow-up outputs match bit for bit
in this longer comparison as well. The summary retains each experiment separately.

There are 4,337,904 fine pairs per segment. The Q15 screen admits 6.74%, the float
first tier admits 4.55%, and final refinement runs on 0.0187%. Compaction therefore
avoids about 4.05 million visits in the second decision loop. Its incremental
whole-segment gain is smaller than the combined gain: about 0.8% in this run.

Moving rejected-row clearing into compaction also moves that time into the screen
and tier-0 counters. Comparing the remaining unaccounted time alone exaggerates
the benefit. Screen time plus that remainder fell from 207.21 to 202.13 ms per
segment, about 5.08 ms; the output-clearing counter still includes the same work.

## Kernel measurements and limits

Eleven alternating rounds of warm pooled calls, pinned to core 0, compare the
pooled-input change alone. Over n=128/256/512 and 37/128/512 templates, median
AVX3 speedups are 1.25x for scattered templates sharing a data block, 1.67x for
contiguous templates, 1.18x for partial batches, and 1.02x for mixed data blocks.
Two-tier hierarchical calls improve a median 1.02x. Selected peaks and counts
match exactly. Separate n=1024 measurements found no material regression.

The Q15 broad-window kernel improves 1.5–3.1% on this host. See the
[Q15 measurements](cpu-q15-gate.md#n--256-fixed-stride-routing-and-broad-windows)
for the fixed-stride routing issue and unchanged numerical contract. An earlier
general fused prototype did not improve the workload and was replaced.

These measurements do not establish speedups on other processors or GPUs. AVX2
and SSE4 correctness is checked locally, while the fused reduction retains its
cache-size and register-count policy. The library still chooses whether to use
Q15 from measured costs: in a separate set of captured n=4096 calls with a single
1024 tier, forcing Q15 on was slower than leaving it off.

## Reproduce

Build the baseline and candidate into separate package directories, then run:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 0 \
  python tools/bench_survivor_batches.py baseline/python candidate/python \
  --isas AVX3 --rounds 11 --sample-ms 20 --output survivors.json
```

For each alternating ladder run, choose the package through `PYTHONPATH`:

```bash
PYTHONPATH=candidate/python OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  taskset -c 4 python tools/profile_cpu_ladder.py --bank path/to/bank.hdf \
  --profiles path/to/ladder_profiles_H1.npz --target AVX3 --runs 1 --segments 4 \
  --q15 1 --output ladder-candidate.json
```

The profiling tool records output hashes for comparison between builds. Its
default alternating Q15 on/off runs also check output equality within the process.
The externally captured bank and profile files are required for this ladder case.

Regression coverage checks pooled scatter, partial lanes, repeated indices,
clipped windows, all-pass and all-reject screens, reused sparse/dense outputs,
null count buffers, multiple bins, counters, and diagnostic ordering. The final
Q15 margin sweep covers five bands and five input families on all three ISAs:
19,200 pairs, zero observed dismissals, maximum margin use 0.310, and matching
loud-signal results with the screen on and off.
