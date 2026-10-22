# Tooling map

The library does not import `tools/` at runtime. These programs build shipped
artifacts, regenerate measured calibration, benchmark public calls, or record
research experiments. Run them from the repository root with the package
installed (`pip install -e .`). Some GPU tools need a physical GPU and Slang;
some calibration tools need separately captured data.

| Purpose | Maintained entry points | Where they run |
|---|---|---|
| Shipped kernels | `build_spirv.py`, `build_forward.py`, `metal_probe.py` | CI checks generated SPIR-V/Metal sources and probes Metal binaries |
| Website and figure | `build_report.py`, `teaser_figure.py`, `teaser_fleet.py` | Benchmark workflow builds the site; figure is regenerated deliberately |
| Public performance | `python -m matchedfilter.benchmark`, `bench_series_workloads.py`, `bench_device_paths.py` | Spectral and series benchmarks; `bench_series_workloads.py --quick` runs in benchmark CI |
| Targeted diagnosis | `audit_class_execution.py`, `bench_class_changes.py`, `bench_pairbatch.py`, `bench_stages.py`, `audit_kernel_binaries.py` | Run when investigating a specific scheduling or kernel cost |
| Survivor batching | `bench_survivor_batches.py` | Alternate two native builds over pooled pair lists and full two-tier hierarchical calls; verify peak and count digests |
| Q15 template tails | `bench_q15_tails.py` | Alternate two builds over direct Q15 screens and grouped hierarchical series calls; verify masks, statistics, peaks, and survivor counts |
| CPU ladder profile | `profile_cpu_ladder.py` | Fix chain and thresholds, compare Q15 off/on or separate builds, and record stage costs and result hashes; requires a real bank and matching profiles |
| Gate validation | `audit_gate_model.py`, `audit_threshold.py`, `score_fdr.py`, `verify_cascade_fdr.py` | Measure a gate chain's dismissal by injection against the flat filter; not part of normal installation |

For a quick CPU/GPU overlap-save comparison with output validation:

```bash
python tools/bench_series_workloads.py --quick --reps 5 --json series.json
```

To compare survivor processing in two saved builds (each directory contains its own
`matchedfilter` package and native extension):

```bash
python tools/bench_survivor_batches.py baseline/python candidate/python --output survivors.json
```

This covers shared or mixed data blocks, scattered or contiguous templates, partial
batches, and two-tier hierarchical filtering. It reports alternating timing samples
and matching output digests. `bench_cpu_broadcast.py` covers dense public calls.

To isolate Q15 tail packing, including template counts 80, 103, 131, 140, 162,
193 and controls 128/254, with native data groups 1, 2, 3, 4, and 32:

```bash
taskset -c 0 python tools/bench_q15_tails.py baseline/python candidate/python --output tails.json
```

Use `--verify-only` for untimed exact-output checks, or `--kinds screen` to isolate
the coarse screen. The series cases keep the 256/512/1024 chain and thresholds fixed.
The real-bank ladder remains the performance acceptance workload.

To measure the effect of batching distinct Vulkan or Metal windows, with output equality
checked before timing:

```bash
python tools/audit_class_execution.py --device gpu --suite submissions --rounds 7 --json .local/submissions.json
```

Create `.local/` first. This alternates separate and grouped submissions using
the same kernels at 1,024–8,192 points and includes the uniform-window control.

The other `bench_*.py`, `audit_*.py`, `gpu_*.py`, `coarse_*.py`, `int8/`,
`narrow_cpu/`, and experimental data files are focused investigations. Their
docstrings and the linked design notes describe the question they answered.
They are not a stable command-line interface, and some require old captures
or optional libraries. Keep them when a design result cites their method;
remove obsolete programs that cannot run and have no source inputs, as was
done for the two missing-Slang GPU spikes in the library health audit.

The reproducible, user-facing benchmark is `python -m matchedfilter.benchmark`.
It checks numerical output before reporting peak timings, sweeps all supported
peak lengths by default, and reports FFTW/MKL references when installed. The
series workload driver complements it with automatic peak and continuous
output. Shared CI runner timing is recorded for comparison over time, not
used as a pass/fail speed threshold.

The teaser driver also runs on macOS, using FFTW and MLX as FFT-only references.
Use a NEON-enabled FFTW build for the M2 comparison; the driver records the
library's SIMD build tags. To compare two saved teaser runs on common axes:

```bash
python tools/teaser_figure.py --compare m2.json amd.json --out comparison.svg
```

See [the M2/Zen 5 work accounting](../docs/measurements/m2-teaser-headroom.md)
for measured timings, arithmetic and memory estimates, and observed selection
costs that leave room for improvement.

For comparisons across more machines, `teaser_fleet.py` records CPU and GPU
separately, checks correlation values and peaks before timing, and represents
missing devices explicitly. It also draws the saved
[six-machine comparison](../docs/measurements/teaser-fleet-20260928.md):

```bash
python tools/teaser_fleet.py --device cpu --out cpu.json
python tools/teaser_fleet.py --device gpu --out gpu.json
python tools/teaser_fleet.py --compare docs/measurements/teaser-fleet-20260928.json --out comparison.svg
```

`teaser_web.py` and `teaser_labels.py` render the Hardware comparison page
from recorded results, with independent CPU/GPU choices and linear/log axes.
`check_wheels.py` reads the wheels a release ships from pyproject's
`[tool.cibuildwheel]`: `--matrix` prints the one-wheel-per-job build matrix
`.github/workflows/wheels.yml` runs, and given a directory it fails unless every
promised wheel is there (the release checks this before publishing).
