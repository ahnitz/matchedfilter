# Tooling map

The library does not import `tools/` at runtime. These programs build shipped
artifacts, regenerate measured calibration, benchmark public calls, or record
research experiments. Run them from the repository root with the package
installed (`pip install -e .`). Some GPU tools need a physical GPU and Slang;
some calibration tools need separately captured data.

| Purpose | Maintained entry points | Where they run |
|---|---|---|
| Shipped kernels | `build_spirv.py`, `build_forward.py`, `metal_probe.py` | CI checks generated SPIR-V/Metal sources and probes Metal binaries |
| Website and figure | `build_report.py`, `teaser_figure.py` | Benchmark workflow builds the site; figure is regenerated deliberately |
| Public performance | `python -m matchedfilter.benchmark`, `bench_series_workloads.py`, `bench_device_paths.py` | Spectral and series benchmarks; `bench_series_workloads.py --quick` runs in benchmark CI |
| Targeted diagnosis | `audit_class_execution.py`, `bench_class_changes.py`, `bench_pairbatch.py`, `bench_stages.py`, `audit_kernel_binaries.py` | Run when investigating a specific scheduling or kernel cost |
| Calibration and validation | `hmf_tune.py`, `regen/cost_cpu.py`, `regen/cost_gpu.py`, `audit_gate_model.py`, `audit_selection.py`, `audit_threshold.py`, `score_*.py` | Regenerate or check measured coarse-gate tables; not part of normal installation |

For a quick CPU/GPU overlap-save comparison with output validation:

```bash
python tools/bench_series_workloads.py --quick --reps 5 --json series.json
```

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
