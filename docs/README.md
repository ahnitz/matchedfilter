# Documentation

Start with the [usage guide](usage.md) for installation, array shapes, filter setup and
examples, and the [architecture](architecture.md) for how the library is built: its API,
layers, gate model, cost models and measured choices. The [repository README](../README.md)
is the short introduction.

These pages describe the library as it is now; when the code changes, they are corrected.
Every document in this directory is listed below, once; `tests/test_docs_index.py` checks
that and that every link resolves.

Studies, audits, plans and measurement logs written during development were removed from
the tree before the first release. They remain in the repository history at the tag
`pre-release-history`.

## Using the library

- [Usage guide](usage.md): inputs and normalisation, output bins, full correlation, series,
  devices, hierarchical filtering and measured choices.
- [Environment variables](environment.md): every variable the package reads, generated from
  `python/matchedfilter/_config.py`.
- [Python support](python-support.md): supported Python and NumPy versions, with the dates
  versions were added and dropped.
- [Full correlation output](full-correlation.md): `CorrelationFilter`, its two-stage GPU
  path above 2^16, and the memory cost of keeping every lag.
- [Testing Metal on physical Apple hardware](macos-test-machine.md): the procedure, and why
  the CI's paravirtual GPU is not enough.

## How it works

- [Architecture](architecture.md): the public API, the layers, the gate model, cost models,
  measured choices, configuration, and tests and gates, at a named revision.
- [Batched matched filter design](design.md): the fused product, the stored layout and why
  the input is frequency domain.
- [The SIMD layer](simd.md): one kernel source over Highway, the targets a build holds, and
  runtime dispatch.
- [The hierarchical filter](hierarchical.md): gate chains, how the chain and thresholds are
  chosen, and their limits.
- [Fraction of theoretical throughput](roofline.md): the roofline report's model, what it
  counts and the assumptions behind it, the same on every device.
- [The resolved plan](resolved-plan.md): what a hierarchical filter settles before it runs,
  and what it guarantees with and without a shared cost file.
- [Reduced-precision gates](reduced-precision-gates.md): the Q15 and FP16 tiers' error
  models, and what checks them.
- [The CPU direct refine](cpu-direct-refine.md): refining survivors by direct correlation
  near the coarse peak, and when it does not apply.
- [Q15 coarse screen](cpu-q15-gate.md): the x86 first tiers in int16: how they gate, how they are
  chosen, and what was measured.
- [FP16 first gate on ARM NEON](cpu-neon-fp16-gate.md): the ARM first tier in half
  precision: its statistic, error model and timing.
- [Hierarchical search design](hierarchical-search-design.md): `search.HierarchicalSearch`;
  what is implemented, and the later phases that are proposals.

## Development

- [Tooling map](../tools/README.md): every tool under `tools/` and what it is for.
- [Documentation style](writing-guide.md): the checklist for editing these pages.
- [How to optimise a kernel here](optimization-method.md): account first, find the binding
  constraint, verify every speedup.
- [Test coverage](testing-coverage.md): what the tests cover by area, and the performance
  regression checks.
- [Host-layer plan](host-layer-plan.md): the active plan for making a pass execute a plan
  compiled at setup, its phases and its log.

## Measurements

- [Hardware comparison](measurements/teaser-fleet-20261020.md) (2026-10-20, at `4fd8b0d4`):
  CPU and GPU timings across eight machines, the figures the README and the project page
  show. `measurements/` also holds the recorded results those pages are built from.
