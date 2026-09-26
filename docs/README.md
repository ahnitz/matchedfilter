# Documentation

Start with the [usage guide](usage.md) for installation, array shapes,
filter setup, and examples. The [repository README](../README.md) is the
short introduction.

## Current behavior

- [Full correlation output](full-correlation.md)
- [Hierarchical filtering](hierarchical.md) and [calibration](gate-model.md)
- [CPU/GPU parity](cpu-gpu-parity.md)
- [GPU arrays and forward transforms](gpu-forward-and-arrays.md)
- [Python support](python-support.md)

## Development

- [Tooling map](../tools/README.md)
- [Test coverage](testing-coverage.md)
- [Physical Apple GPU testing](macos-test-machine.md)
- [Documentation style](writing-guide.md)

## Research and measurements

The design studies, `plans/`, `audits/`, and `measurements/` record experiments
and the evidence behind implementation choices. They can describe earlier
APIs, rejected approaches, and historical test counts. Use the current guides
above for supported behavior. Benchmark results apply to their recorded
hardware, workload, and code revision.

Keep reproducible methods, measured results, and explanations of decisions
in the repository. Put conversation transcripts, temporary status reports,
agent handoffs, and machine access instructions in the ignored `.local/`
directory or outside the checkout. Git history preserves superseded work;
an extra tracked scratch file is not needed to preserve it.
