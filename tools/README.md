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
| CPU ladder profile | `profile_cpu_ladder.py` | Fix chain and thresholds, compare Q15 off/on or separate builds, and record stage costs and result hashes; requires a real bank and matching profiles |
| Job setup | `setup_capture.py`, `setup_replay.py`, `setup_breakdown.py`, `setup_decisions_diff.py` | Capture a job's banks and references, replay its matchedfilter setup, charge its time by part, and diff two replays' decisions |
| Gate validation | `fdr_audit.py`, `split_bias.py`, `audit_gate_model.py`, `audit_threshold.py`, `make_psd_profiles.py` | Measure gate chains' dismissal by injection against the flat filter, two-sided (`fdr_audit.py`, run by the gate), and the budget split's selection bias on independent model draws (`split_bias.py`); not part of normal installation |
| Follow-ups over many groups | `bench_followup_groups.py` | Many leaf banks, one or two single-template calls each (most calls a group's first, as in the PyCBC job): time of a bank's first call against later ones, and resident memory per bank |
| Output identity | `golden.py` | Record every result the library hands a caller (capture tops, hooks with follow-ups, split windows, the low-level entry points) from a seeded cost file, on the CPU or a GPU (`--device`), and compare two records bitwise, order included; run before merging a change that must not change results |
| Middle-to-leaf schedules | `schedule_bench.py` | A capture's chunks (the jobs its search's walk makes) run untiled and tiled at several tile budgets, checked bit for bit, timed in alternating order; the docstring has the perf recipe for instruction, cycle and memory-fill counts. Run on a new machine to see whether tiling pays there (it did not on Zen 5, 2026-11-28) |
| Device memory by role | `gpu_alloc_trace.py` | Run a program (a pycbc job, `search_bench.py`) with every Vulkan allocation traced by role (workspace slots, record buffers, inner rows, templates, ...), whether it was ever touched, and the breakdown at the peak of live memory; run before merging a change to what the GPU paths allocate |
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

To check that a change leaves every result as it was, seed a cost file once, then record
each tree from it (each run reads a private copy, with `MF_AUTOTUNE=0`) and compare:

```bash
python tools/golden.py record base.npz --costs seed.json     # cold: writes seed.json
python tools/golden.py record base2.npz --costs seed.json    # the same tree again
python tools/golden.py compare base.npz base2.npz            # reproducible: "N arrays; 0 differ"
python tools/golden.py record new.npz --costs seed.json      # from the changed tree
python tools/golden.py compare base.npz new.npz
```

On a GPU, give every run `--device gpu:0` and a seed of that device's own (a device's measured
choices are not the CPU's, and a record compares only with records of its device). From one
seed, fresh processes on the Radeon 8060S record identical results (19,868 arrays; three runs,
2026-11-27). Two seeds recorded by two cold runs can differ in the lowest bits of some SNRs,
because the seeds hold different measured choices (coarse kernel layouts, the direct-refine
price): always compare records made from the same seed. Make the seeding run the device's first
run after a build, since it may compile kernels for minutes. `--digest-above N` keeps arrays of
up to N elements whole instead of their digests, to see how two records differ.

To see what a GPU job holds in device memory, and how much of it no kernel ever touched:

```bash
python tools/gpu_alloc_trace.py trace.json tools/search_bench.py research/captures/tops --device gpu:0
```

On the 171,828-template PyCBC job (Radeon 8060S, 2026-11-27) 2,129 MB of the 3,240 MB live at
the peak were never touched: seven of the eight spectra slots each plan made at its first call.
With a slot's buffers made when a call first uses it, 1,133 MB are live at the peak and none of
it is untouched.

The other `bench_*.py`, `audit_*.py`, `gpu_*.py` and `narrow_cpu/` programs are focused
investigations. Their docstrings describe the question they answered. They are not a
stable command-line interface, and some require captures or optional libraries.

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

For comparisons across more machines, `teaser_fleet.py` records CPU and GPU
separately, checks correlation values and peaks before timing, and represents
missing devices explicitly. It also draws the saved
[hardware comparison](../docs/measurements/teaser-fleet-20261020.md):

```bash
python tools/teaser_fleet.py --device cpu --out cpu.json
python tools/teaser_fleet.py --device gpu --out gpu.json
python tools/teaser_fleet.py --compare docs/measurements/teaser-fleet-20261020.json --out comparison.svg
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
annotations), `test_durations.py` (tests/durations.json, the module weights the sharded
runs balance by), `migrate_cost_file.py` (cost-file format migration).

**Production-like benchmarks**: `ladder.py`, `ab_ladder.py`, `prodlen.py`, `ladder_diff.py`,
`ladder_coverage.py`, `ladder_profiles.py`, `profile_cpu_ladder.py`, `hier_bench.py`,
`search_bench.py`, `scoreboard.py`.

**Public-API benchmarks and figures**: `bench_series_workloads.py`, `bench_device_paths.py`,
`teaser_figure.py`, `teaser_fleet.py`, `teaser_labels.py`, `teaser_web.py`, `build_report.py`.

**Comparing two builds**: `compare_builds.py`, `bench_class_changes.py`,
`bench_cpu_broadcast.py`.

**Targeted CPU measurements**: `bench_stages.py`, `bench_pairbatch.py`,
`perf_counters.py`, `cold_decisions.py`, `real_probe_study.py`, `audit_class_execution.py`, `audit_kernel_binaries.py`.

**A search's follow-up calls**: `bench_refilter.py` (replay captured single-template
refilter calls: time per call, first and repeated, and the peaks against the capture).

**A job's setup**: `setup_capture.py` (record a job's banks, references and first calls),
`setup_replay.py` (rebuild the setup in one process: time and a digest of the decisions),
`setup_breakdown.py` (the setup's time by part), `setup_decisions_diff.py` (two replays'
decisions compared).

**Gate accuracy and bounds**: `gate_margin.py` (every narrow first tier),
`gate16_check.py`, `fdr_audit.py` (every profile
and chain against the flat filter, two-sided; `--device` adds the device's own filter, the
GPU fp16 tier), `split_bias.py` (each plan's dismissal on model draws it was
not made from: the check that plans dismiss fd on average with gatemodel.fit_order's tail,
direct refine windows included), `audit_gate_model.py`,
`audit_threshold.py`;
`make_psd_profiles.py` writes the pycbc noise-curve test profiles (`tests/data/psd_model_profiles.npz`).

**GPU devices**: `gpu_features.py`, `gpu_roofline.py`, `cuda_roofline.py`,
`metal_roofline.py`, `metal_probe.py`, `metal_bank_probe.py`, `bench_pack_indexing.py`,
`verify_cuda.py`.

**Research records** (how a kernel was derived):
`gpu_decomposition.py`, `gpu_regmodel.py`, `gpu_output_order.py`, `gpu_tierc_model.py`,
`gpu_hier_reference.py` (also the tests' numpy reference), and the `narrow_cpu/` studies.
