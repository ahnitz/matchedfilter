# Library path profile, 2026-09-26

These are warm public calls on the local Ryzen AI MAX+ 395 / Radeon 8060S.
They are workload measurements, not portable speed guarantees. Setup and
template loading are outside the timed regions; the series and CPU layout
drivers alternate variants to reduce clock-drift bias.

## Automatic overlap-save peak output

`tools/bench_series_workloads.py --reps 5` used 43 blocks, 128 templates and
one peak per valid block. Times are milliseconds per whole series:

| n | CPU automatic | CPU explicit | GPU automatic | GPU explicit |
|---:|---:|---:|---:|---:|
| 2,048 | 9.62 | 9.51 | 0.327 | 0.315 |
| 4,096 | 18.30 | 18.30 | 0.644 | 0.632 |
| 8,192 | 35.67 | 36.23 | 1.593 | 1.573 |

Automatic GPU layout adds about 10–20 µs per series here. At 4,096 points,
`cProfile` put most wall time in Vulkan queue submission/completion (113 ms
of 142 ms over 200 profiled calls). Index-coordinate conversion cost about
10 µs and layout validation about 20 µs per profiled call; instrumentation
inflates these small Python costs. Reusing precomputed block arrays did not
produce a stable timing gain across alternating trials, so no layout cache
was added. The extra automatic-call time is real but is a small share of
whole-call latency on this batch.

## Irregular windows multiply GPU dispatches

`tools/audit_class_execution.py --suite layout --rounds 3` compared 128
blocks of 1,024 points against 32 templates. All calls computed the same
number of output bins; only the number of distinct valid windows changed.

| Distinct windows | CPU ms/series | GPU ms/series |
|---:|---:|---:|
| 1 | 1.52 | 0.234 |
| 2 | 1.54 | 0.359 |
| 16 | 1.55 | 1.174 |
| 128 | 3.24 | 7.975 |

The original GPU series executor submitted each window group separately. The
128-window case was roughly 34 times the one-window GPU time; Python validation
itself was only about 0.01–0.015 ms.

The flat Vulkan path now records distinct window dispatches together. Each
bounded batch performs one forward FFT dispatch, followed by the correlation
dispatches, in one submission. It uses the existing kernels and descriptor
offsets; it adds no shader variants or asynchronous public API. Uniform windows,
Metal, hierarchical filtering, and requests above the kernel's bin capacity use
the existing paths. Cache eviction can require an earlier forward submission;
correctness does not depend on retaining a cache entry.

Warm alternating comparisons on the same Radeon 8060S, with 128 blocks and 32
templates, gave the following whole-call medians (milliseconds):

| n | Distinct windows | Separate submissions | Grouped submission |
|---:|---:|---:|---:|
| 1,024 | 128 | 9.109 | 0.429 |
| 2,048 | 2 | 0.415 | 0.347 |
| 2,048 | 16 | 1.390 | 0.373 |
| 2,048 | 128 | 9.782 | 0.515 |
| 4,096 | 2 | 0.650 | 0.592 |
| 4,096 | 16 | 1.729 | 0.609 |
| 4,096 | 128 | 10.111 | 0.750 |
| 8,192 | 128 | 11.595 | 1.678 |

These improvements apply to irregular explicit blocks (`run_blocks` and its
compatible `run_series` form). Automatic overlap-save already uses repeated
windows, so these ratios do not describe an improvement to that workload.
Single-window calls execute the same code as before; their alternating timings
also show how short GPU measurements vary with clocks and load.

Reproduce with `tools/audit_class_execution.py --device gpu --suite submissions
--rounds 7 --json .local/submissions.json` after creating `.local/`. The driver
checks indices and complex values before timing. Tests cover changed input and
templates, shared template memory, selected template ranges, caller order,
zero-padded tails, small memory budgets, cache eviction, and the warm submission
count.

## Full output: storage choice dominates CPU access

For `CorrelationFilter.run()` at 4,096 points, 8 data × 64 templates produce
16 MiB of complex64 output. A preallocated output was timed for the GPU call,
then an in-place NumPy scale; medians from six warm samples:

| Output storage | GPU call ms | NumPy scale ms | Combined ms |
|---|---:|---:|---:|
| Ordinary NumPy array | 2.29 | 0.36 | 2.62 |
| Default GPU shared allocation | 0.89 | 77.87 | 78.77 |
| GPU shared allocation with `readback=True` | 2.77 | 0.33 | 3.09 |

The default Vulkan shared memory favors GPU writes and uncached CPU reads;
using NumPy on it is a severe trap. The public `empty_shared(...,
readback=True)` option now exposes the host-cached allocation already used by
automatic continuous output. Keeping the default unchanged preserves the
fast GPU-write path. Which of ordinary NumPy output or host-cached shared
output wins depends on size and downstream access: at 8,192 points (32 MiB),
their call-plus-scale times were 6.59 and 4.96 ms respectively. Applications
should time the complete consumer step, not only `run()`.

## Spectral flat and hierarchical filtering

`tools/bench_device_paths.py --n 2048 4096 8192 --data 16 --templates 128
--rounds 5` gave these milliseconds per batch (noise, threshold 5.5):

| n | CPU flat | CPU hierarchical | GPU flat | GPU hierarchical |
|---:|---:|---:|---:|---:|
| 2,048 | 2.44 | 0.271 | 0.205 | 0.069 |
| 4,096 | 4.97 | 0.975 | 0.291 | 0.094 |
| 8,192 | 11.85 | 3.305 | 0.644 | 0.163 |

The selected bands were 256, 1,024 and 2,048 respectively. Refinement rates
were about 3–9% on this synthetic workload, and differ between CPU and GPU
coarse implementations. Hierarchical savings depend on the actual template
population and refine rate. `tools/bench_stages.py 4096 16 128` estimated a
0.096 ms fixed GPU hierarchical cost at zero refinement, about 43% of its
0.223 ms flat call; the fitted line is approximate because short GPU timings
were noisy. At 100% refinement, hierarchical took 0.248 ms and lost to flat.

One further inversion is repeatable on CPU at 2,048 points: with 8 × 64
pairs, a full-output call took 0.672 ms while peak-only took 0.796 ms. At
16 × 128 pairs they were approximately equal (3.51 vs 3.52 ms). Avoiding full
stores is not always enough to pay for the peak scan at small transforms.
This is a candidate for kernel profiling if small CPU batches matter.

A follow-up tried an unconditional vector select in the 2,048-point single-peak
scan. Clean baseline/candidate builds produced identical outputs and some
zero-threshold wins, but the high-threshold workload slowed by about 3–6%
across AVX-512, AVX2, and SSE4 in pinned, alternating measurements. The candidate
was rejected; no CPU kernel or dispatch change is enabled. The saved-baseline
performance tests now cover both flat and hierarchical calls in this size range.

## Next measurements

1. Measure whether hierarchical and Metal irregular-window workloads justify
   extending command batching to those executors.
2. Profile the 2,048-point CPU peak scan against full output with hardware
   counters and varied bin counts. The difference changes with bank shape.
3. Benchmark full-output storage with the caller's actual consumption pattern;
   GPU-only chaining, NumPy scaling and copying have different winners.
