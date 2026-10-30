# Tooling map

The library does not import `tools/` at runtime. These programs build shipped
artifacts, regenerate measured calibration, benchmark public calls, or record
research experiments. Run them from the repository root with the package
installed (`pip install -e .`). Some GPU tools need a physical GPU and Slang;
some calibration tools need separately captured data.

| Purpose | Maintained entry points | Where they run |
|---|---|---|
| Shipped kernels | `kernel_variants.py`, `metal_probe.py` | CI checks every shipped kernel and manifest against the generator and probes Metal binaries |
| Website and figure | `build_report.py`, `teaser_figure.py`, `teaser_fleet.py` | Benchmark workflow builds the site; figure is regenerated deliberately |
| Public performance | `python -m matchedfilter.benchmark`, `bench_series_workloads.py`, `bench_device_paths.py` | Spectral and series benchmarks; `bench_series_workloads.py --quick` runs in benchmark CI |
| Targeted diagnosis | `audit_class_execution.py`, `bench_class_changes.py`, `bench_pairbatch.py`, `bench_stages.py`, `audit_kernel_binaries.py` | Run when investigating a specific scheduling or kernel cost |
| Survivor batching | `bench_survivor_batches.py` | Alternate two native builds over pooled pair lists and full two-tier hierarchical calls; verify peak and count digests |
| Q15 template tails | `bench_q15_tails.py` | Alternate two builds over direct Q15 screens and grouped hierarchical series calls; verify masks, statistics, peaks, and survivor counts |
| CPU ladder profile | `profile_cpu_ladder.py` | Fix chain and thresholds, compare Q15 off/on or separate builds, and record stage costs and result hashes; requires a real bank and matching profiles |
| Job setup | `setup_capture.py`, `setup_replay.py`, `setup_breakdown.py`, `setup_decisions_diff.py` | Capture a job's banks and references, replay its matchedfilter setup, charge its time by part, and diff two replays' decisions |
| Measured-choice statistics | `trial_power.py` | Read A/A logs (`MF_TRIAL_AA_LOG`): the null of a paired round's ratio, the paired rule's false-switch rate, and the error and power of candidate rules against the cap (docs/trial-statistics.md) |
| Gate validation | `fdr_audit.py`, `split_bias.py`, `audit_gate_model.py`, `audit_threshold.py`, `make_psd_profiles.py` | Measure gate chains' dismissal by injection against the flat filter, two-sided (`fdr_audit.py`, run by the gate), and the budget split's selection bias on independent model draws (`split_bias.py`); not part of normal installation |
| Measured choices at production length | `prodlen.py` | Fresh ladder processes of two trees in ABBA order, with no MF_COST_FILE, as production runs: each measured decision's lock (a coordinate search counted once), the fine batch it locked at and how long it was open; steady, total, user and system time; run before merging a change to how choices are measured |

For a quick CPU/GPU overlap-save comparison with output validation:

```bash
python tools/bench_series_workloads.py --quick --reps 5 --json series.json
```

To vet a change to the measured choices at production length (27 tops x 28 segments, each
process fresh with no MF_COST_FILE, as a production job starts), against a baseline tree:

```bash
python tools/prodlen.py run --base ../main --new . --processes 4 --out .local/prodlen \
    --bank BANK.hdf --profiles PROFILES.npz --device gpu:0 --cores 12-15
python tools/prodlen.py summarise .local/prodlen
```

Each process runs its own tree's `ladder.py` (`--pipeline --pure`), pinned to `--cores`
(required), through the tool's hook, which logs every batch and every measured choice's
creation, rounds (with their timings) and lock. Per process the summary lists every decision:
a measured choice, with a coordinate search's passes (`... around <arm>`) counted as one
decision, its last pass's lock. For each it gives the lock and the fine batch it locked at,
the fine batches it was open in, the batches it played and how many of them ran a non-default
configuration; then the model-priced chain and block-size picks, the steady wall and its
per-top series, total, user and system time, and the load. Pooled, it gives the median ratios
(also per ABBA pair), each tree's non-default decisions (one per search, however many passes
locked it) and the processes they were in, searches left open, and each offline kernel
screen's picks. Its CHECK lines confirm that each process completed, ran its own tree and one
fine batch and one follow-up batch per segment, and that the hook and the library's
MF_AUTOTUNE log saw the same locks. The tool exits 1 if a check fails. Read the times with the
load range: in a main-against-main run on dev2 (2026-10-29) the load rose from 8 to 20 and one
tree's two processes took 402 s and 898 s. Read the decisions per process: in a second such
run, of four processes of one library one locked GPU-BATCH fuse=0 (in fine batch 16 of 756)
and another VK-SUBGROUP 32.

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

## Every tool

Each program here, by what it is for; its docstring has the detail. `tests/test_docs_index.py`
checks that this list names every tool, and `tests/test_repository_tools.py` that each one
imports and resolves its names.

**Builds and shipped artifacts**: `kernel_variants.py` (every GPU kernel variant of every
backend, its build and its manifest; `build_spirv.py` and `build_ptx.py` run it for Vulkan and
Metal, and for CUDA); `precompile_metal.sh` (Metal libraries); `kernel_build_id.py` (restamps
the kernel identities after an external compile); `coarse_layout.py` (the fp16 coarse kernel's build-time layout);
`gen_environment_doc.py` (docs/environment.md); `check_wheels.py` (release wheels);
`make_bank_subset.py` (the test bank slice).

**Merge gate and CI**: `gate.py` (every pre-merge check), `ci_status.py` (Actions
verdicts), `sanitize.sh` and `sanitize_report.py` (ASan/UBSan runs and their
annotations), `migrate_cost_file.py` (cost-file format migration).

**Production-like benchmarks**: `ladder.py`, `ab_ladder.py`, `prodlen.py`, `ladder_diff.py`,
`ladder_coverage.py`, `ladder_profiles.py`, `profile_cpu_ladder.py`, `hier_bench.py`,
`hier_all.sh`, `search_bench.py`, `scoreboard.py`, `health.py`.

**Public-API benchmarks and figures**: `bench_series_workloads.py`, `bench_device_paths.py`,
`teaser_figure.py`, `teaser_fleet.py`, `teaser_labels.py`, `teaser_web.py`, `build_report.py`.

**Comparing two builds**: `compare_builds.py`, `compare_captured_series.py`,
`bench_class_changes.py`, `bench_cpu_broadcast.py`, `bench_q15_tails.py`,
`bench_survivor_batches.py`.

**Targeted CPU measurements**: `bench_stages.py`, `bench_pairbatch.py`,
`bench_refine_density.py`, `bench_cpu_peak_native.py`, `bench_captured_series.py`,
`perf_counters.py`, `cpu_trial_check.py`, `cold_decisions.py`, `cost_model_ablation.py`,
`real_probe_study.py`, `replay_captured_groups.py`, `replay_partitions.py`,
`audit_class_execution.py`, `audit_execution_contracts.py`, `audit_kernel_binaries.py`.

**A job's setup**: `setup_capture.py` (record a job's banks, references and first calls),
`setup_replay.py` (rebuild the setup in one process: time and a digest of the decisions),
`setup_breakdown.py` (the setup's time by part), `setup_decisions_diff.py` (two replays'
decisions compared).

**Gate accuracy and bounds**: `gate_margin.py` (every narrow first tier), `gate16_error.py`,
`gate16_check.py`, `coarse_precision.py`, `coarse_fixed.py`, `fdr_audit.py` (every profile
and chain against the flat filter, two-sided; `--device` adds the device's own filter, the
GPU fp16 tier), `split_bias.py` (each plan's dismissal on model draws it was
not made from: the check that plans dismiss fd on average with gatemodel.fit_order's tail,
direct refine windows included), `audit_gate_model.py`,
`audit_threshold.py`, `audit_gpu_bands.py`;
`make_psd_profiles.py` writes the pycbc noise-curve test profiles (`tests/data/psd_model_profiles.npz`).

**GPU devices**: `gpu_features.py`, `gpu_roofline.py`, `cuda_roofline.py`,
`metal_roofline.py`, `metal_probe.py`, `metal_bank_probe.py`, `bench_pack_indexing.py`,
`verify_cuda.py`, `unify_golden.py` and `unify_baseline.sh` (GPU host exactness).

**Research records** (how a kernel was derived; kept because a design note cites them):
`gpu_decomposition.py`, `gpu_regmodel.py`, `gpu_output_order.py`, `gpu_tierc_model.py`,
`gpu_hier_reference.py` (also the tests' numpy reference), `stream_search.py`, and the
`int8/` and `narrow_cpu/` studies.

Removed 2026-10-22, as measuring what the library no longer has: `band_select.py` and
`calibrate_cascade.py` (prototypes the gate model replaced), `coarse_stage_value.py` and
`bench_coarse_quality.py` (the even/odd coarse split, since removed).
