# Test coverage

What checks a change, where each check runs, and how to run the opt-in ones.

## The suite

`python -m pytest tests` runs on the CPU and on every GPU backend the machine has; tests
of a backend that is absent skip and say so. The suite needs NumPy and pytest only. Run
it single-threaded (`OMP_NUM_THREADS=1`), since the library's choices are per thread.

By area, the tests check:

- **Results against references.** Flat filtering against a NumPy correlation; the
  hierarchical filter against the flat one; every SIMD target the build holds against the
  others; each GPU backend against the CPU; compiled planner routines against the NumPy
  code they replaced, bit for bit.
- **The gate model.** A plan's false-dismissal rate against its budget by injection, per
  profile and chain; the planner's decisions under a shared cost file; the reduced-precision
  tiers against their own statistic.
- **State and lifetime.** Data, template and reference changes between calls; cached device
  inputs after each kind of change; empty and zero-padded series; ownership of arrays a
  filter is given; one filter object per thread.
- **Boundaries.** Malformed shapes, ranges and dtypes are refused before native code runs;
  arguments a bank or filter cannot run are refused by name when it is built; native
  routines are checked against output overruns.
- **Edges and combinations.** The ends of a series, separate windows in one cascade, a
  reference taken away, and randomly drawn banks, series and calls checked against the
  bank's own ungated answer (`tests/test_edge_paths.py`).
- **Transfer counts.** GPU uploads and submissions are counted with host doubles, so the
  checks run without GPU hardware. They are deterministic; no wall-clock limit is embedded
  in the default suite.
- **Packaging and tools.** The public API's names, the shipped kernels against their
  manifests, the documentation index, every tool's imports, and the benchmark and site
  builders.

## Continuous integration

Each push runs the suite on Linux x86-64 (the widest target and forced narrower ones),
Linux arm64 and macOS arm64, across the supported Python versions. One job builds the
source archive, compares it with the tracked files, installs it and runs its bundled tests
from a directory outside the checkout, so a missing fixture or build input fails there.
The Nightly workflow adds AddressSanitizer and UndefinedBehaviorSanitizer runs, in shards
balanced by `tests/durations.json`. Timing benchmarks on shared runners are recorded for
comparison over time and never fail a job.

## The merge gate

`python tools/gate.py` runs every pre-merge check this machine can run and reports each as
ok, FAIL or skip: the suite, the production ladder against the CPU reference (given a bank
and profiles), the narrow gates' margins, the false-dismissal audit against the flat filter
(`tools/fdr_audit.py`), reproducible choices under a shared cost file, and the state of CI.
A skipped check is reported as skipped, never as passed.

## Performance regression checks

The default suite checks correctness and structural costs (upload reuse, cache bounds,
submission counts). Run the opt-in timing suite on an otherwise idle machine:

```bash
python -m pytest tests/test_performance.py --run-performance -q
```

It covers the CPU and available GPU devices:

- Flat and hierarchical cached `run()` at 2,048, 4,096 and 8,192 points with 16 data rows
  × 128 templates, and 128 × 512 at 4,096 points. The peak threshold is 5.5; hierarchical
  runs use an explicit band of 256 and a coarse threshold of 4.0.
- Automatic peak `run_series()` at those three lengths, with 43 blocks and 128 templates.
  It may cost at most 1.5 times the explicit-block reference.
- Continuous full output at 32,768 points, six templates and a 1,048,576-sample series. It
  may cost at most 1.5 times explicit blocks plus assembly.
- Vulkan irregular windows at 4,096 points, 128 blocks and 32 templates. Grouped submission
  must take at most half the separate-submission time.

Warm calls exclude setup, check results before timing, and alternate the compared paths.
The relative limits allow noise and catch substantial overhead. They cannot catch a
slowdown shared by both paths. For that, record a baseline on the known-good revision and
compare the candidate in the same environment:

```bash
python -m pytest tests/test_performance.py --run-performance \
  --performance-record=.local/performance-baseline.json -q
python -m pytest tests/test_performance.py --run-performance \
  --performance-baseline=.local/performance-baseline.json -q
```

The comparison fails if any measured workload is over 25% slower. Host, device, ISA,
Python and NumPy identities must match, and a workload missing from the baseline fails.
Recording writes only after a successful run and refuses to overwrite the baseline being
compared against. Keep baselines in ignored local storage or CI artifacts, and refresh
them only after reviewing a deliberate change. Unavailable GPU cases skip explicitly.

## What the tests do not show

- Metal kernels execute only on macOS; on Linux the Metal host logic runs against
  submission doubles. The CI's paravirtual Apple GPU is not physical hardware
  ([testing Metal on physical Apple hardware](macos-test-machine.md)).
- Vulkan and CUDA are tested where a GPU is present, which no CI runner has: on Linux CI
  the three backends' host code is covered only through submission doubles.
- Not every line runs. In a line-coverage run of the suite without a GPU (2026-11-24) the
  C kernels executed 91% of their lines; what did not run was mostly allocation-failure
  cleanup and fallbacks for plan layouts the test machine's targets do not use.
- The ladder checks of the merge gate need a production-like bank and noise profiles,
  which are not in the repository.
