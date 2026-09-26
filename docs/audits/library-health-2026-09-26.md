# Library health audit, 2026-09-26

The production paths are well covered for an alpha library: the test suite
exercises all supported full-correlation lengths, CPU/GPU output parity,
hierarchical calibration refusal, memory limits, cached plans, and series
lifecycle. The full local run passed 986 tests with 5 skips. This audit
adds an independent FFT oracle for automatic continuous output; its existing
tests had primarily compared it with the explicit-block implementation.

## Changes from this audit

- The package metadata now describes the CPU/GPU and full-output capability.
- `valid` rejects fractional and string lag boundaries instead of silently
  truncating or parsing them.
- Two unreferenced Slang prototype drivers were removed. They read
  `occ.slang` and `reg.slang`, neither of which exists in the repository; they
  could not run. Their history remains in Git.
- `tools/bench_series_workloads.py` measures the warm public `run_series` API:
  43-block, 128-template peak workloads at 2,048, 4,096, and 8,192 points,
  plus six-template continuous output at 32,768 points. It checks output
  equality before timing and alternates automatic and explicit-block calls.
  Benchmark CI runs a shorter version and saves JSON separately from the
  existing spectral `run()` report. Shared-runner timings are observations,
  never pass/fail thresholds.

## Remaining choices

1. **Series performance reporting.** The public benchmark page still shows
   spectral `run()` and hierarchical `run()` results, not series results.
   The separate JSON artifact is a useful first step; adding a series chart
   should wait for runs from several hosts and a clear CPU/GPU comparison
   policy. On the local Radeon, automatic peak layout took about 10–20 µs
   more per 43-block series than explicit blocks; the new full continuous
   output was faster than explicit blocks plus stitching. The peak difference
   is likely Python layout/index conversion, but needs profiling before a
   kernel change.
2. **Public API complexity.** `run_series` supports both automatic layout
   (`valid` configured on the filter) and legacy explicit blocks. Both are
   useful, but the index coordinate convention differs: automatic peak calls
   return absolute series positions, explicit calls return block-local lags.
   This is documented and tested. The explicit form now also has the
   `run_blocks` name, so each preferred method has one index convention.
   A future breaking release could remove explicit arguments from
   `run_series` after callers migrate.
3. **Research tooling.** `tools/` contains calibration generators, scoring
   scripts, benchmark drivers and historical experiments. Most are referenced
   by design notes but not by CI. Reference counts alone do not establish
   dead code: calibration scripts remain necessary to regenerate shipped
   tables. A small `tools/README.md` separating maintained commands from
   historical experiments would make this easier to navigate. The archived
   `src/gpu/draft/` sources are not part of the shipped runtime.
4. **End-to-end consumer parity.** The library-level continuous-output tests
   cover the PyCBC-like 43-block six-template geometry, but do not run PyCBC's
   5,000-second trigger fixture. That integration check belongs in the PyCBC
   repository after its caller adopts automatic `run_series`.

The benchmark suite now measures the common spectrum and overlap-save entry
points. It does not enforce a universal speed ratio: batch shape, cache state,
GPU transfer mode, and calibration-dependent refine rate make one ratio
misleading. Review the saved per-workload results when tuning those paths.
The [path profile](../measurements/library-profile-2026-09-26.md) records the
first cross-path measurements and identifies output memory and irregular GPU
window dispatches as workload-sensitive costs.
