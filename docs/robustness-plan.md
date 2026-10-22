# Cleanup, robustness and CI plan (2026-10-21)

Status: adopted 2026-10-21; decisions recorded at the end. Progress is logged in the Log section. It was built in four passes:

1. Seven read-only surveys, which produced 102 findings, each with file:line evidence, plus a completeness critic.
2. Three independent drafts: robustness-first, simplicity-first and CI-cost-first.
3. A judged synthesis of the drafts.
4. Two rounds of adversarial critique and revision (fact-check, CI design, sequencing, end-state quality, a skeptic, and a simulated dry run).

I then checked the four most consequential bug claims myself, cut machinery that does not pay for itself (see "Cuts" below), and condensed the result. The full step specifications (files, line numbers, test cases) are kept with the plan's working files, and each step will be written out in full when it starts.

## Why

- **CI is slow, and some of its coverage isn't real.**
  - It takes 38 min wall time and about 229 job-minutes per push.
  - About 105 of those minutes are the whole suite re-run once per CPU target inside each of the five Python jobs, one re-run per job repeating the default target.
  - One of the CPU target switches is undone part-way through the suite, so the SSE4 and AVX2 re-runs test their target only up to that point.
  - The weekly Benchmark workflow has been red on every platform for two runs unseen, because a pipe through `tee` hides the failure.
- **Real bugs, reproduced on main (31e37afd):**
  - An invalid `MF_ISA` prints an error, then the next kernel call segfaults.
  - `set_target(None)` drops `MF_ISA`: under `MF_ISA=SSE4` it switches back to AVX3.
  - A damaged `MF_COST_FILE` is silently wiped at the next write. Every record is lost.
  - Hierarchical `set_data` keeps the caller's array: zeroing it after `set_data` turns a peak of |v| = 79816 into none at all.
  - Several C entry points have range checks that overflow.
  - Two threads using one filter object corrupt memory silently.
  - `MF_DEVICE` leaks into the library's own CPU plans.
- **The code still has historical layers.**
  - `__init__.py` is 3.7k lines and `time_domain.py` 3k; together they hold 147 function-level imports that work around cycles.
  - There are 42 `MF_*` variables, parsed several different ways, some of them no-ops.
  - Tools import names that no longer exist, and some docs describe removed mechanisms.

## Milestones

| Milestone | Goal | Exit criterion | Push CI (wall) |
|---|---|---|---|
| A. Honest CI | A failure is always visible; no wasted runs | Every step fails where it broke; releases need green CI | 38 → ~29 min |
| B. Real bugs fixed | No silent data loss or memory errors | Each bug has a test that fails on 31e37afd | → ~18 min |
| C. Tests that discriminate | Every test can fail on the bug it guards; nightly sanitizers | Trial tests bounded by the trial's own limit; ASan/UBSan nightly green | → ~13–16 min |
| D. Fewer things | Delete dead paths, knobs, tools; one config registry | Every `MF_*` registered and documented; every tool imports | ~12–15 min |
| E. One-way layers | Modules in layers; stage C step 4 | No upward imports; `__init__` is re-exports only | unchanged |

After E come the CPU optimisations (tier 1, middle, forward), each as one `Choice` or priced value in one module.

## Target CI

- **On every push (~13–16 min wall, ~85–100 job-min).** Everything runs in parallel.
  - **x86 tests:** seven jobs, one suite each:
    - the widest target on 3.10, 3.11, 3.12, 3.13 and 3.14;
    - `MF_ISA=SSE4` on the oldest Python, with the numpy floor;
    - `MF_ISA=AVX2` on 3.14.

    Each job prints its ISA and backend, and a mismatch fails the job.
  - **The 3.12 job is also the sdist test.** It builds the sdist, checks it against the tracked files, installs from it and runs the tests.
  - **Linux arm64 (NEON).** This is new; arm64 is tested today only on macOS and in the weekly benchmark.
  - **Static checks:** regenerate both codelet files and diff them, plus ruff's undefined-name rules.
  - **Metal:** compile the committed `.metal` sources, cached, instead of rebuilding every kernel from Slang each run; then run the suite and the CPU-against-GPU kernel run.
  - **Wheels:** manylinux and macOS wheels run a smoke subset. The full wheel suites move to the weekly rehearsal and to release.
- **Nightly (~65–100 job-min):**
  - an ASan/UBSan build running the full suite, on x86 and on arm64;
  - musllinux wheels with the full suite;
  - the full suite in reverse module order, to catch tests that depend on order.
- **Weekly:**
  - benchmarks on Linux x86 and arm64, macOS CPU, and Metal, the Metal one moved off the push path where it took 14.4 min;
  - a full release rehearsal (all wheels, full suites) that never publishes.
- **Release:** refused unless CI for that exact SHA is green. Wheels build in parallel: about 35–45 min, against 80–92 today.
- **Loud by construction:**
  - every workflow runs under bash with pipefail; a tolerated diagnostic prints a `::warning`;
  - every job has a timeout, and pytest's `faulthandler_timeout = 600` dumps a hung test's stack;
  - strict markers;
  - one `::error` annotation per failed test, including inside the cibuildwheel containers;
  - a skip table in every job's summary;
  - `gate.py` gains a `ci` check (main's latest run and every workflow's latest scheduled run are green), so a red schedule blocks the next merge.

## Steps

Each step is one push, behind the usual gate:

- the dev2 suite and `gate.py`;
- the GPU machines for GPU-touching steps;
- paired ladders on dev1 and dev2 for hot-path steps;
- green CI afterwards.

A step that changes C or workflows is first pushed to a `ci/<topic>` branch and must be green there before main.

**A. Honest CI**

- **A1. Workflow hygiene.**
  - Applies: pipefail, timeouts, faulthandler, strict markers, pinned images and SHA-pinned actions, single-thread environment variables at workflow level, and `environment-pass` for `GITHUB_ACTIONS` and `MF_ISA` inside cibuildwheel.
  - The per-CPU-target loop skips the default target.
  - The advisory benchmarks leave the push path.
  - Verify: a planted `false | tee` fails its step on a `ci/` branch.
- **A2. CI status tool.** `tools/ci_status.py` reads the public API and prints a verdict per job for a SHA or branch, plus the latest scheduled runs. `gate.py` gains a `ci` check, and `release.yml` refuses a SHA whose CI is not green. Verify: offline tests on recorded API responses (the 10-19 red Benchmark run, a green CI run, a red one, a cancelled one).
- **A3. Safety nets before behaviour changes.**
  - `test_consumer_contract.py` replays the calls pycbc_inspiral_fir makes (imports, window forms, `template_spectra`, `template_valid`) on the committed bank slice.
  - `test_public_api.py` pins the public names.
  - A float64 check of the SNR the bank path reports, for both engines and both refines.
  - `tools/sanitize.sh`, the local ASan/UBSan recipe.

**B. Real bugs** (each with a test that fails on 31e37afd)

- **B1. Cost file never loses data.**
  - A damaged file is moved aside with a warning, and an unreadable one is never replaced.
  - One atomic rewrite helper is shared with `migrate_cost_file.py`.
  - Cost models and one-shot prices are first-writer-wins.
  - Legacy record names are reported once.
- **B2. The test session leaves your environment alone.**
  - It scrubs `MF_*` except `MF_ISA` and the tool variables.
  - The header prints ISA, backend and devices.
  - `clear_autotune_cache` clears what its docstring says.
  - A `--reverse-modules` option checks order dependence.
- **B3. `MF_ISA` is a real restriction.**
  - It is applied at import, and `set_target(None)` restores it.
  - An invalid value raises `ValueError` at import, not `ImportError`, which pycbc would report as "not installed".
  - Lazily built sub-plans use the parent plan's backend.
  - Verify: the suite under each of the three targets, bit-identical goldens, paired ladders.
- **B4. Restructure the push gate:**
  - the seven-job matrix, the arm64 job, the sdist folded into the 3.12 job;
  - the Metal job tests the committed kernels;
  - wheel smoke tests;
  - the Q15 codelet check.

  B3 must land first, otherwise the forced-target jobs keep testing the wrong thing. B4a, which strips build paths and a sync-conflict copy from the shipped Metal sources, lands just before, so the Metal kernel id changes once.
- **B5. Hierarchical `set_data` copies the data,** in C as the flat filter does: 8n bytes per row and one memcpy per call.
- **B6. Every C entry point validates its arguments.**
  - Range checks cannot overflow.
  - Size checks use division instead of products.
  - Thresholds must be finite.
  - Every error path sets an exception.
  - One boundary test covers every `_core` entry point, with sentinel outputs that must stay untouched.
- **B7. One filter per thread.**
  - A busy flag makes a second thread get `RuntimeError` instead of corrupting memory.
  - Constructors and lazy allocations either succeed completely or free what they took.
- **B8. Internal CPU plans name the CPU,** so `MF_DEVICE` cannot move them.
- **B9. One series group** for a plan, its calibration and its block pricing. Calibration is stored under the group the C plan actually ran, not the requested one.

**C. Tests that discriminate**

- **C1. Skips are visible.**
  - Every job prints a skip table.
  - A GPU job fails if GPU tests skip, as `--require-coarse-gpu` already does on Metal.
  - A probe failure is its own skip reason, so "no GPU" and "GPU broken" read differently.
- **C2. Releases build in parallel from one reusable wheel workflow,** with a weekly rehearsal and a nightly musl build.
- **C3. Trial tests stop restating schedules.**
  - `Choice.limit` gives the most calls after which a contest must have locked.
  - Loops drive "until a winner, at most `limit + 1`".
  - The cross-process test cannot pass on a trial that never advances.
  - The 218 s reproducibility test and the 84 s block-switching test get cheaper without losing what they check.
- **C4. No timing outside the `performance` marker.**
  - Tests that cannot fail are rewritten or deleted.
  - The FDR tool and its CI job become one test that also counts at the production budget.
  - `test_regression_suite.py` dissolves into the files it overlaps.
- **C5. Nightly ASan/UBSan** on x86 and arm64, and a reverse-order run. Suppressions live in one committed file, each with its reason.
- **C6. GPU tests force real layouts** through `MF_COARSE_LAYOUT`.
  - The no-op per-backend coarse knobs are deleted.
  - The Metal sigma tool is repaired, since it is the only way to re-derive a compiled-in constant.
- **C7. One writer per open contest.** A second process sampling the same open contest prints a warning.

**D. Fewer things**

- **D1. Measure, then delete the default-off CPU layouts** (`MF_BBLK` stage-B blocking, `MF_ILAY=0`) on dev1 and the M2. A layout that wins anywhere becomes a measured candidate in the CPU phase instead. Then one gcov and coverage.py run drives further dead-code deletion.
- **D2. One configuration registry.**
  - `_config.py` lists every `MF_*` variable: kind, type, default, when it is read, and its doc.
  - Every variable gets one parse rule: unset or empty means the default, 0/false/no/off and 1/true/yes/on mean what they say, anything else raises. The rule lands one variable per commit, each with a CHANGELOG line.
  - Removed names and near misses warn at import.
  - `docs/environment.md` is generated from the registry, and a test checks that code, C and docs agree.
- **D3. Tools and docs say what is true.**
  - A repository test imports every tool and example and resolves their names.
  - Broken tools are fixed and dead ones pruned.
  - `docs/README` lists current references and historical logs separately.
- **D4. Wheels carry only loadable artifacts.** No PTX on macOS, no MSL on Linux. CUDA stops offering 8 coarse builds it cannot load. A reachability test lists every shipped kernel file.

**E. One-way layers** (behaviour-neutral moves; each checked by a move comparator and a layer test)

- **E0. A half-page design note on the resolved plan:** what it holds, what it guarantees with and without a shared cost file, and what is public.
- **E1. Guards before any move:**
  - a layer test, whose allowlist is seeded from today's 147 function-level imports and shrinks with each move;
  - `tools/check_move.py`, deleted after E3.
- **E2. Foundation modules:** `_costfile`, the decision rules in `_choice`, and `_results`.
- **E4. `_chains`** owns the chain and Q15 trials. The side tables disappear, and the tests drive it with injected timings.
- **E5. `_layout` and `_prices`:** bank layouts in one module, one helper for the four price-once copies, and a reset scope declared by each `Choice` kind.
- **E6. Stage C step 4:** one `resolve()` per filter replaces today's six resolution sites. A persisted record is added only if a divergence remains after B1.
- **E7. One window parser** for the bank and `HierarchicalSearch`. Optional; see decisions.
- **E3, last.** The filter classes move out of `__init__`, which becomes about 150 lines of re-exports. Public `__module__` values and pickle paths stay.

## Cuts I made to the agents' final plan

- **Premerge proofs.** The agents built `ci_status` staleness rules, ack flags, a run cache and a premerge mode. I keep a small `ci_status` and a procedure: risky changes go to a `ci/<topic>` branch first.
- **Skip allowlists and a CI time budget.** The agents proposed per-job and per-host skip allowlists (`tests/ci_policy.py`) and a time-budget table. I keep the printed skip table and require-GPU flags on GPU jobs. Allowlists of regexes are upkeep that blocks merges for cosmetic changes.
- **C switches as plan options (deferred).** The agents' step routes every C switch through an options struct passed to every entry point, so the shipped C library reads only `MF_ISA`. That is a large change for C header users who don't exist yet. The registry covers the Python side.
- **Allocation fault injection (decide at B7).** I keep the NULL checks and all-or-nothing allocation, and decide on the private countdown hook when B7 starts.

## Deferred, with reasons

- **A compile-time guard for pathological driver compiles** (dev4's Intel ANV). It needs a design: a worker thread or a child process, deadlines, and expiring records keyed by driver version.
- **Vulkan via lavapipe in CI.** Hierarchical cost calibration took over 9 minutes in one lavapipe test, so the job needs its own design. The first candidate is a nightly flat-path job.
- **Per-push sanitizer subset.** Decided once the nightly has measured its time.
- **GPU kernel-table work (unification stage 3)** and datacenter GPU throughput. Out of scope for now.
- **Merging concurrent contest samples.** C7 only warns; this returns if concurrent writers turn out to be supported.

## Decisions (2026-10-21)

1. **Python 3.10 is dropped.** The minimum Python is 3.11. The numpy floor becomes 1.23.2, the first release with Python 3.11 wheels; pycbc's runtime asks for numpy 1.16 or newer, and production runs 2.2.3. The SSE4 job installs exactly the floor version, so the floor is tested.
2. **Hierarchical `set_data` copies in C** (B5).
3. **`MF_TRIAL_RECHECK` is deleted,** with `Choice.observe` and the steady re-check.
4. **One PyPI release after milestone D,** with the behaviour changes batched in CHANGELOG.
5. **The public surface** is the package root, `time_domain`, `search`, `device`, `precision`, and gatechain's documented `chain_thresholds`, `calibrate_costs`, `choose_chain` and `direct_halfwidth`. Private names may move without re-exports.
6. **E7 is adopted:** `HierarchicalSearch` uses the bank's window parser.
7. **Concurrent writers to one `MF_COST_FILE` are not supported;** C7's warning is enough. Production does not set `MF_COST_FILE`. The long-term goal is to need no cost file at all, with no performance loss (unification stage 2's direction). New persisted state therefore needs a strong reason.
8. **A read-only GitHub token** is set up on the dev hosts for `ci_status`.

## Log

- 2026-10-21: plan adopted.
- 2026-10-21: **A1 merged (94a2b50b, 8a33d64a).**
  - What changed: workflows under bash with pipefail; timeouts on every job; pinned images and actions; strict pytest config with a 600 s faulthandler dump; the session checks MF_ISA against the backend; the duplicate default-target re-run is gone; the advisory benchmarks left CI; Python 3.10 is dropped.
  - Proof run (ci/a1): all green; Metal 21 min (was 36), longest test job 28 min (was 38).
  - The weekly benchmark, unmasked, no longer crashed but ran past its 60-min timeout on every platform: the hierarchical table trials every (n, budget, SNR) cell. Its sweep is bounded to seven lengths with a 120-min timeout. Making that table cheaper is a benchmark-tool item.
- 2026-10-21: **A2: tools/ci_status.py**, a `ci` check in tools/gate.py, and the release `ci-green` job.
  - ci_status: public API; verdicts green/red/unknown; failed jobs with their steps and annotations; schedules judged by their latest run and staleness; a red schedule cleared by a green ci/** proof of its fix.
  - The release's ci-green job is exercised only by a real release or a dispatch.
- 2026-10-21: **A3: safety nets before behaviour changes.**
  - tests/test_consumer_contract.py replays pycbc_inspiral_fir's calls (imports, the search construction with its leaf options, BlockInput, the three hooks and the context attributes they read, refilter, pad, timings, the chisq bank's template_valid and template_spectra), and a degenerate-PSD reference.
  - tests/test_public_api.py pins `__all__` (gaining include_dir and UnsupportedSize) and the public submodules (decision 5).
  - tests/test_bank_path_precision.py compares every reported |SNR| with a float64 direct correlation at its lag, through three chains with and without the direct refine, on the flat filter and on a usable GPU. The observed worst case is 8e-7, the bound 1e-5; a planted 1e-3 error in the direct refine's taps fails it (3.1e-3).
  - tools/sanitize.sh, the ASan/UBSan recipe. No dev host has the sanitizer runtimes installed (the libasan and libubsan packages), so it is first exercised by the nightly CI job (C5).
- 2026-10-21: **B1: MF_COST_FILE never loses data.** Reads distinguish missing, damaged and unreadable files. A damaged file is kept aside and reported; an unreadable one is never written. `_update_cost` returns the record it wrote. `_store_first` makes cost models and the one-shot prices (q15-tier0, cpu-fft, direct-lagtap, corr3/corr-pfft) first-writer-wins. Legacy trial records are reported once. The migrate tool writes under the library's lock, atomically. All ten new tests fail on 7acdc7f5.
- 2026-10-21: **B2: the test session leaves the developer's environment alone.**
  - conftest removes every MF_* variable before collection, except MF_ISA, the tool paths and `--keep-mf-env NAME`. The header names what was removed and kept, the CPU backend and targets, the devices and numpy.
  - `clear_autotune_cache` clears what its docstring says; the autouse fixture no longer swallows errors.
  - Every run prints a skip table (a ::notice on Actions). `--reverse-modules` reverses module order.
  - Forward and reversed suites both pass: 2155 passed, 141 skipped.
- 2026-10-21: **B3: MF_ISA restricts the process; plans keep their kernel.**
  - kernel.cc: MF_ISA is the baseline that `ap_set_target(NULL)` restores. A failed `ap_set_target` restores the previous selection. `ap_isa_init` lets the extension raise ValueError at import.
  - dispatch.c: `*_like` and `*_on` variants run on a plan's back end. matchfilt.c and hmf.c build lazy sub-plans and run their direct correlation, real split and root merge with them.
  - Tools that pick a target refuse a conflicting MF_ISA. The benchmark's backend comparison names the targets it could not compare.
  - tests/test_isa_selection.py: three in-process tests fail on the old library. The invalid-MF_ISA crash and the dropped restriction were reproduced by hand on it.
- 2026-10-22: **B4a: Metal sources without build paths.** One `write_msl` helper in tools/build_spirv.py normalises every Metal emitter's output, including the tier-C, coarse and forward emitters that skipped it. The 80 committed sources that named /home/... paths are stripped (only `#line` strings and trailing newlines change), the sync-conflict copy is deleted, and the Metal build id is restamped. test_kernels_ship fails on any absolute path or conflict copy in the installed kernel directories.
- 2026-10-22: **B4: the push gate runs one suite per job.**
  - Six x86 test jobs, each running the suite once:
    - the widest target on 3.11–3.14, the 3.12 job also building, checking and testing the sdist;
    - MF_ISA=SSE4 on 3.11 with numpy 1.23.2, the floor;
    - MF_ISA=AVX2 on 3.14.
  - A Linux arm64 test job.
  - The generated-files job also diffs the Q15 codelets.
  - The Metal job compiles the committed sources with tools/precompile_metal.sh (the release's script), cached, instead of fetching slangc and rebuilding every kernel.
  - The CI wheels run a smoke subset; the release keeps the full suite.
  - MANIFEST.in ships CHANGELOG.md, examples/, src/gpu/*.cu and the tool scripts and sources the sdist lacked.
- 2026-10-22: **B5: hierarchical plans own their data.**
  - `ap_hmf_set_data` copies into plan memory, and the header documents the copy for both setters. The Python layer holds copies for replay.
  - tests/test_data_ownership.py: the two hierarchical cases fail on 542aeed1.
  - test_lazy_tier_ingest's eager-copy test asserted the old behaviour, that a refine reads a buffer mutated after set_data. It now asserts that the data is read as set.
  - The ladder runs the series path, which already used plan memory.
- 2026-10-22: **B6: C entry points validate their arguments.**
  - `ap_range_ok` (transform.h) replaces 17 range checks that formed lo + count in int (matchfilt.c, hmf.c, _core.c q15_screen). `buf_holds` replaces the size products of caller counts (set_taps' stride, taps_to_spectra, gate16_bound).
  - The public run methods refuse NaN thresholds. MF and HMF refuse a second `__init__`. forward_cost refuses an unsupported size and reports a failed allocation.
  - tests/test_core_boundary.py: every case fails on 542aeed1.
  - Left for later, with nothing found to depend on them: an exception on every -1 setter path, checked Py_BuildValue results, taps_to_spectra's copy-back into a converted out, and the scales check of CorrelationFilter.run.
- 2026-10-22: **B7: one filter per thread, all-or-nothing allocation.**
  - Every method of _core's MF, HMF and Root objects is wrapped (GUARDED): the busy flag is read and set with the GIL held, so a concurrent call raises RuntimeError. `_busy` is exposed read-only for the test. The full suite passes, so the library never shares one object between threads.
  - matchfilt.c's lazy scratch allocations (`alloc_pair`; the DIF plan with its two buffers) allocate all or nothing. Before, a guard on the first pointer took a half-allocated set as ready.
  - Decided at B7: no fault-injection hook, to avoid test-only C code. The allocation fix is by construction and is exercised under the sanitizers (C5).
- 2026-10-22: **B8: internal CPU plans name the CPU.** time_domain's single-template CPU plan and the correlation price probe pass `device='cpu'`. With None, MF_DEVICE moved them. tests/test_cpu_plans_name_the_cpu.py fails on 542aeed1.
- 2026-10-22: **B9a: cost models keyed by the series group that ran.**
  - The C helper `ap_hmf_effective_group` (MF_DGROUP, then the 4 MB cap) is what the plan applies and `_core.series_group` exposes. `calibrate_costs` keys its cache and record by it. tests/test_series_group_key.py.
  - **B9b deferred to the CPU phase.** The plan resolves its execution-policy row with its chain's last band, the cost model with band 0. On Haswell-EP at n=4096, the one row, the plan therefore runs at group 4 while the cost model is calibrated at 16. Making the row band-independent changes Haswell's chain choice and needs Haswell paired ladders. The CPU phase replaces the frozen row with a measured Choice for the series group anyway, so the fix belongs there.
- 2026-10-22: **C1: skips are visible.**
  - Every run prints its skips grouped by reason (B2).
  - The GPU probe records why each enumerated GPU was rejected. `usable_gpu_reason()` names the device and error, so "no GPU" and "a GPU that failed its probe" read differently. The 14 test files that skipped with a bare "no usable GPU" use it.
  - The Metal job already fails rather than skips its coarse GPU tests (`--require-coarse-gpu`).
- 2026-10-22: **C3a: MF_TRIAL_RECHECK deleted (decision 3).**
  - Removed: `Choice.observe`, the steady flags and paths in the trial loop, `_chain_steady`, `_chain_monitor`, `_trial_monitor`, `_BlockTrials.observe`, and gatechain's recheck_enabled, observe_steady, steady_disagrees and RECHECK_*. Five tests went with them. Records no longer carry `rechecked`.
  - `_fuse_begin`'s "a trial is trying" now means any open chain or block trial in the batch.
- 2026-10-22: **C3b: trial tests bounded by the trial's own limit.**
  - `Choice.limit` is the most calls after which a contest has locked, whatever the timings: its budget of attempts, else every candidate sampled to the cap after its warm-up (rounds, for a paired contest). test_choice proves the bound on contests that never resolve.
  - test_followup_batch and test_gate_chain's trial test drive until the choice locks, up to its limit, instead of restating its schedule.
  - Not done here: making the two slowest tests cheaper (test_reproducible_choices, 218 s on a loaded host; test_switching_layouts_is_exact_and_locks, 84 s). Deferred to C4 with the other test-cost work.
- 2026-10-22: **C4: tests that fail on the bug they guard.**
  - Deleted 28 tests that could not fail:
    - toggles of the removed MF_BRACKET and MF_GCAL;
    - a constant-arithmetic memory "benchmark";
    - test_replica_top_critical.py, which never imported the library;
    - the temporary-data smoke test that B5's ownership test supersedes;
    - test_regression_suite's 16 `is not None` smoke cases, its duplicate calibration probe, its two tests of the maintainer's local banks, and its 360-line standalone benchmark.
  - The rest of that file is tests/test_search_contracts.py.
  - Timing turned into counts: Python calls per run() (sys.setprofile) are equal at 1, 16 and 64 pairs; an equal set_reference reloads nothing. Chain ranking and cost relations use a committed cost model (tests/data/cost_model_2048_zen5.json), and the live calibration keeps structural checks.
  - The tautological half of the cascade subset test is gone.
  - The fdr-verification CI job is gone; it duplicated test_fdr_multishape at low power. tools/verify_cascade_fdr.py stays as the large-sample audit tool.
- 2026-10-22: **C5: nightly workflow.** .github/workflows/nightly.yml runs at 03:17 UTC, and on ci/nightly/** pushes and dispatch:
  - the suite under ASan and UBSan with tools/sanitize.sh, on x86_64 and arm64;
  - the suite in reverse module order;
  - the cp312 musllinux wheel with its full suite (from C2).

  tools/ci_status.py --schedules picks it up from its cron line, so a red nightly fails gate.py's 'ci' check.
- 2026-10-22: **C7: a second writer is said.** Choice._save, under the cost-file lock, compares the open record on file with how far along (attempts, samples) this process last read or wrote it. A record further along means another process is sampling the same contest; it warns once per contest and writes as before. A record of another trial method, which this choice replaces rather than continues, is not a second writer (the paired CPU block trial replacing unpaired history showed this). docs/environment.md states the rule.
- 2026-10-22: **C4 sdist fix.** The C4 fixture tests/data/cost_model_2048_zen5.json was not in the sdist (MANIFEST.in named only .npy and .npz there); the sdist CI check caught it.
- 2026-10-22: **First nightly proof.** The reverse-order run failed in test_cost_file_concurrency: the spawned first writer did not signal within 15 s on the runner. It passes reversed locally, with no environment or threads leaked from earlier modules. The wait is now 120 s and fails at once with the writer's exit code if it dies, so a recurrence says whether it was slow or broken.
- 2026-10-22: **C2: one wheel workflow.** .github/workflows/wheels.yml (workflow_call) builds pyproject's [tool.cibuildwheel] list, narrowed by a select pattern, one wheel per job; tools/check_wheels.py --matrix derives the matrix and also checks a directory holds every promised wheel. Callers:
  - ci.yml: the cp314 manylinux and macOS wheels, smoke-tested, with the header check;
  - nightly.yml: the cp312 musllinux wheel with the full suite;
  - release.yml: all 12 wheels in parallel, each with the full suite, Metal precompiled; a `complete` job checks the set before publish.

  release.yml rehearses every Monday at 04:41 UTC (it never publishes on a schedule or a push), and a ci/release/** push proves it; ci_status --schedules counts the rehearsal like the nightly.
- 2026-10-22: **Weekly benchmark still over its limit.** The ci/bench/a1 and ci/bench/b4 proofs had failed and were not followed up: macOS hit the 2-hour limit, linux-arm64 lost its runner at 114 min, linux-x86_64 was cancelled at 58 min. Timed on a Zen 5 desktop, one target:
  - the flat table takes seconds at every length (3–4 s at n = 2^18 and 2^20, 1.2 GB);
  - the hierarchical table is the whole cost: 15 cells per length at about 6 s a cell at n = 4096 and about 30 s at n = 65536, mostly calibration.

  The benchmark gains --hier-n, and the workflow runs the hierarchical table at 1024 and 16384 (about 4 min per target here). Open for the CPU phase: about 30 s to calibrate one hierarchical plan at n = 65536 with no cost file is a user-facing cost, not only a benchmark one.
- 2026-10-22: **D1: MF_BBLK deleted; MF_ILAY kept as a candidate.** Flat-kernel A/B, three interleaved rounds, medians against the default (and the production ladder on dev1, four rounds):

  | variant | Zen 3 (dev1) | Zen 5 (dev2) | M2 |
  |---|---|---|---|
  | MF_ILAY=0 | +7% / +7% / +18% at 4096 / 2^18 / 2^20 | +9% / +2% / +14% | +3% at 4096, **-9% at 2^18, -4% at 2^20** |
  | MF_BBLK=2 | +3% / +5% / +3% | +8% / +3% / +7% | +4-7% at every length |
  | MF_BBLK=4 | +5% / +3% / +1% | — | +5-6% |
  | dev1 ladder (segment median) | ILAY=0 +1.3%, BBLK=2 -0.4%: noise | | |

  Stage-B blocking loses everywhere and is removed (balanced-inl.h, -66 lines; timings unchanged). The strided layout wins on the M2 at large n, so per the rule it becomes a measured candidate in the CPU phase rather than a deletion; MF_ILAY stays until then.
- 2026-10-22: **D2a: the registry.** python/matchedfilter/_config.py lists every environment variable (section, side, default, doc; siblings documented in one row point at it with `row`), the shader macro names that are not variables, and the removed names with reasons. docs/environment.md is generated from it (tools/gen_environment_doc.py). tests/test_config_registry.py checks three things: every MF_* literal in the package and C is registered, every registered name is read by the side it says, and the document is current. It found MF_METAL_COARSE_TILE and _TWT documented but read by nothing; the document now says only what exists. No behaviour changes yet: the parse rule lands one variable per commit (D2b), with a shared C helper so the C-read flags follow it too (today MF_HMF_PROF, MF_CORR_NO_STREAM and MF_GATE16_DEBUG count any value, even 0, as on).
- 2026-10-22: **Reverse-order failure found.** The writer diagnostic showed the cause. tools/migrate_cost_file.py's main(), run in-process by its test, inserted `tools/../python` into sys.path for the rest of the session. Every later spawned process imported that unbuilt source tree and died. This happened in reverse order only, and only where the tree has no built extension (CI; locally it has one, so nothing reproduced). The tool now falls back to the source tree only when the package is not importable, and conftest restores sys.path after every test.
- 2026-10-22: **Sanitizers in shards.** The first nightly's ASan/UBSan jobs reached the 90-minute limit on both architectures with no sanitizer report. conftest gains `--shard K/N` (whole modules, sorted and dealt in turn; tests/test_shard.py), and the nightly runs four shards per architecture with a 75-minute limit.
- 2026-10-22: **D2b: one parse rule.** _config gains kind and value per variable, `parse`/`get` (unset or empty: the default; flags 0/false/no/off and 1/true/yes/on; numbers must parse; else ValueError naming the variable) and `check_environment()`. The package runs check_environment() before _core is imported: an invalid value fails the import, and a removed or unknown MF_* name warns (unknown names get the nearest name). Every Python read goes through `_config.get`. src/env.h gives the C the same rule (ap_env_flag, ap_env_int, ap_env_text). Tool, build and test variables are registered in their own section; the tools keep parsing them themselves. Done together rather than one variable per commit: the change is the same for each, and the CHANGELOG lists every variable whose meaning changed.

  Found on the way: the package reads nothing named MF_METAL_COARSE_TILE, but tests/test_gpu_loud_overflow.py parametrizes Metal tiles with it and tools/metal_c16_sigma.py sets it. Those Metal cases ran one layout under several names. This is now part of C6, which forces layouts through MF_COARSE_LAYOUT.
- 2026-10-22: **D3a: every tool and example imports and resolves its names.** tests/test_repository_tools.py imports each file of tools/ and examples/ in one interpreter started outside the checkout, restoring sys.path, sys.argv and the helpers each loads from tools/ or tests/. pyflakes (now in the test extra) checks for undefined names. Each case was checked to fail on the old file. It found six broken tools:
  - audit_threshold.py imported hmf_tune, folded into tests/_gatelib.py in b3a8117f;
  - score_fdr.py, bench_stages.py and bench_coarse_quality.py found tests/ only from the checkout root;
  - verify_cuda.py and bench_pack_indexing.py ran their whole body on import (now main()).

  audit_class_execution.py's `del f` inside loops whose lambdas close over f read as an undefined name; it is now `f = None`. No tool imports a third-party module but numpy at module level.
- 2026-10-22: **First sanitized pass.** In four shards, x86_64 ran the whole suite under ASan and UBSan clean (32-58 minutes a shard); every arm64 quarter reached 75 minutes. x86_64 now runs six shards and arm64 twelve.
- 2026-10-22: **arm64 sanitizers time out at every size.** In twelfths, every arm64 shard still reached 75 minutes while x86_64 sixths took 21-70. A twelfth of the suite that never finishes is not a sizing problem: something on arm64 (the sanitized build of Highway's arm targets, or a hang) takes the whole limit. The step now stops itself at 65 minutes and reports the build time and the tail of its output as an error annotation; sanitize.sh prints build and run times.
- 2026-10-22: **The arm64 time was the build.** The reporting step showed every arm64 shard still building when it stopped at 65 minutes. On x86_64 the build took 13-19 minutes of every shard. Timed locally (gcc, src/kernel.cc, which is the whole build: every other file takes about 10 s):

  | flags | compile time |
  |---|---|
  | plain | 30 s |
  | ASan+UBSan | 679 s |
  | without use-after-scope | 225 s |
  | ASan alone | 613 s |
  | UBSan alone | 126 s |
  | ASan+UBSan at -O1 | 390 s |

  The sanitized build drops use-after-scope checking (every other check stays, at the shipped -O3). The nightly builds once per architecture (sanitize-build, 150-minute limit, an artifact) and the shards test that build (sanitize.sh --keep DIR --build-only, then --prebuilt DIR).
- 2026-10-22: **D3b: the docs index lists everything.** docs/README.md linked 36 of the 71 documents; environment.md, the active plans, the search design and the SIMD layer were among the missing. It now lists every document once: using the library, how it works, performance, development, plans, and a dated history of studies, audits and retired plans. tests/test_docs_index.py checks that every docs/*.md is listed and every link resolves.
- 2026-10-22: **The arm64 build was use-after-scope.** Without that check the sanitized build took 259 s on the arm64 runner and 212 s on x86_64. With it, on arm64 it had not finished in 65 minutes.
- 2026-10-22: **D4a: a wheel carries the kernels its platform loads.** python/matchedfilter/_kernel_dirs.py names them: SPIR-V everywhere, PTX off macOS, Metal on macOS only. setup.py's build_py leaves the others out of a wheel; the sdist keeps all. That is 93 MB of PTX off the macOS wheel, and 8.7 MB of Metal off each Linux wheel; the Linux wheel built here is 20.7 MB. Tests that check committed kernels statically (test_metal, test_cuda, test_kernel_id, test_spirv, the Metal layout checks) read the checkout's copy where the install has none, so Linux CI still checks the Metal sources. The full suite passes against an installed Linux wheel. Open: the CUDA coarse builds a device cannot load (needs a CUDA device; with C6) and the reachability test (every shipped kernel file is one some backend can ask for).
- 2026-10-22: **Sanitized suite clean on dev2; an intermittent CI-only abort.**
  - With libasan and libubsan now on dev2, the whole suite ran clean under ASan and UBSan in six shards of 3.5-10 minutes, including the Vulkan host paths CI cannot reach.
  - sanitize.sh now finds the real runtime through a probe program's ldd. On Fedora, -print-file-name=libasan.so names a linker script, which LD_PRELOAD ignored, so every run aborted at start.
  - On CI, x86_64 shards aborted (rc 134) twice in the forced pair-batch tests (MF_PBMAX=1024: test_forced_cpu_pair_batch, test_continuous_forced_pair_batch_and_fir_bank) and passed in two other runs. No sanitizer report or message preceded the aborts. The tests pass locally under ASan, for every target and in their shard. ASan now runs with handle_abort=1, so a recurrence prints the native stack.
- 2026-10-22: **D4a proofs.** The release rehearsal is green with the platform-filtered wheels, and the macOS wheel passes the full suite on the M2. The macOS release wheels first failed in test_measured_choice, which read ptx/manifest.json from the install; that is fixed. One CI run's Metal job reported a paravirtual GPU hang (kIOGPUCommandBufferCallbackErrorHang) one commit after a green run whose only change was that test; re-proving.
- 2026-10-22: **C6: GPU tests force real layouts.**
  - conftest's forced_coarse_layouts names, per band, the first of the device's own layouts (ctx.coarse_layouts, parsed by the new _coarse.parse_label) that a test asks for. The tests force it through MF_COARSE_LAYOUT, which raises for a name the device lacks.
  - test_gpu_loud_overflow and test_vk_hier_grouped (tiles), the packed-coarse partial-group test on Metal and the untiled-packing test on Vulkan (now required to run at least two packings) use it.
  - Before, the Metal tile cases ran one layout under five names, and a Vulkan tile the device lacked fell back to untiled without saying so.
  - Removed: MF_VK_COARSE_PPG/_TILE/_SUBGROUP/_TWT, MF_METAL_COARSE_PPG and _coarse.forced_tile.
  - MF_VK_C16_BOUND=0 is MF_COARSE_RAW=1 on every backend; the old names are in the removed list and warn.
- 2026-10-22: **C6: the sigma tool repaired.** tools/metal_c16_sigma.py had three faults:
  - it iterated tiles through a variable nothing read;
  - it printed res["0"] from keys "1".."8" (a KeyError);
  - it read buffers through ctx._hier, which no longer exists.

  tools/c16_sigma.py dispatches each of the device's coarse layouts directly, as the host's coarse timer does, on any backend. It reproduces the tables:
  - Vulkan on the 8060S: sigma 1.46-1.49 / 1.79-1.81 / 2.12-2.15 at bands 64 / 256 / 1024 over 36-50 layouts each (C16_SIGMA 1.6 / 1.8 / 2.5);
  - Metal on the M2: 1.72-1.78 at 256 over 16 layouts (C16_SIGMA_APPLE 1.8).

  Gates: the full suite on dev2 (Vulkan) and on the M2 (Metal). The CUDA changes are the rename only and were not run on a CUDA device.
- 2026-10-22: **D3c: the tools map lists every tool; dead ones pruned.** tools/README.md described 30 of 85 tools. It now has a complete index by purpose (builds, gate and CI, production-like benchmarks, public benchmarks, build comparisons, CPU measurements, gate accuracy, GPU devices, research records), and tests/test_docs_index.py checks every tools/*.py and *.sh is named. Four tools were removed because they measure what the library no longer has: band_select.py and calibrate_cascade.py (prototypes the gate model replaced), coarse_stage_value.py and bench_coarse_quality.py (the even/odd coarse split, since removed; two of them ran their whole study on import, ignoring --help).
- 2026-10-22: **arm64 sanitizer shards run.** With the one-build workflow the arm64 shards run their tests. One failed by a subprocess timeout: test_reproducible_choices' first process timed out at 900 s under ASan. Its first process takes 50 s here (cold calibration of the cost models; later ones about 7 s), so the time is calibration, not the data: shrinking segments or templates only added processes. Subprocess time limits in the tests now scale by TEST_TIMEOUT_SCALE, which tools/sanitize.sh sets to 10 (conftest.scaled). The 50 s cold start is a user-facing cost: it joins the n=65536 calibration finding for the CPU phase.
- 2026-10-22: **D1b: the coverage pass.** One gcov build ran the suite under each x86 target (AVX3, AVX2, SSE4). A sys.monitoring plugin recorded the Python lines (coverage.py is not installed here).
  - Of 435 C functions, 47 never ran on any target. Of these, the ARM FP16 gate and the platform FFT acceleration run on their platforms (arm64 CI, macOS), and the unused generated codelets are static inline (the compiler drops them).
  - The rest sit behind public C entry points that nothing in the package calls. They are listed below for a decision, not deleted.
  - MF_GMAJOR=0 measured slower at every length on Zen 5 (+18% at 4096, +25% at 2^18), the M2 (+12% to +50%) and dev1 (loaded at the time; still slower in every pair). It is removed with the row-major stage A it forced (balanced-inl.h); the geometry-driven unfused product in matchfilt.c stays. The fallback test now runs the product on every target at 1024 and 4096.
  - Python: three functions nothing calls are deleted (_vkcompute._global_barrier, _shared.shared_key, search._search_leaves). The other never-run code is backend-specific (Metal, CUDA), benchmark or command-line code, or called but untested.

  Public C entry points the package never calls, for a decision: ap_binmax_split, ap_binmax_prod, ap_interp_max, ap_series_buf, ap_series_stride (and the series-store mode they enable), ap_mf_run_sel, ap_nbins, ap_root_merge, ap_real_split, ap_mf_ndata, ap_hmf_get_real_series, ap_hmf_get_hermitian.
- 2026-10-22: **The CI-only x86 crash is a segfault.** With handle_abort the next failure showed "Fatal Python error: Segmentation fault" in test_continuous_forced_pair_batch_and_fir_bank on an Intel AVX-512 runner (AVX3); dev2's AVX-512 is AMD Zen 5. pytest's faulthandler replaces ASan's SEGV handler, so ASan printed nothing. sanitize.sh now sets allow_user_segv_handler=0, so the next one prints ASan's report.
- 2026-10-22: **E0 and E1.**
  - docs/resolved-plan.md describes the resolved plan: what it holds, the seven places it is resolved today, its guarantees with and without a cost file, and what is public.
  - tests/test_layers.py places every module in seven layers (foundation, platform, models, GPU host, backends, workloads, applications). It fails on any new upward import, `from . import name` of the root's names included, and on any allowlist entry no longer needed. Its allowlist was computed, not written by hand: 13 upward edges (the plan's estimate counted 147 function-level imports, most of them downward).
  - tools/check_move.py checks that every definition at a base revision is still in the package with an identical syntax tree, wherever it moved (tests/test_check_move.py).
- 2026-10-22: **E2: the foundation modules.**
  - _costfile: the cost file's read, lock, atomic write, update and first-writer store, from gatechain.
  - _choice: the decision rules (TIE, CHOICE_Z, sample_spread, paired_choice, measured_choice), from gatechain.
  - _results: PEAK_DTYPE, _SparsePeaks and _Deferred, from the package root.

  Each was moved verbatim (tools/check_move.py: no definition changed but the import lines that point at the new modules). The old homes import the names back. Upward edges: 13 -> 9 (_choice -> gatechain, and _gpuexec, _gpuhier and _shared -> the root, are gone). The layer test now treats the compiled _core as the lowest layer; `from . import _core` had counted as an import of the root.
- 2026-10-22: **E4a: the chain trials in _chains.**
  - The chain-trial and Q15-trial machinery moved verbatim from the package root to _chains (models layer): keys, the trial's Choice, the GPU batch schedule (next, pending, batch), the stored lock, the tables and constants. _CHAIN_WARM_BATCHES came from time_domain.
  - _AUTOTUNE_LOCK, _log_autotune and _autotune_enabled moved to _choice.
  - The root refers to the tables as _chains.NAME, so a test that replaces one is seen everywhere. Tests and tools that patched or read them through the root now go through mf._chains.
  - Upward edges: 9 -> 7 (_choice and _vksubgroup no longer reach into the root). Still to come in E4: folding the side tables (_CHAIN_PLACED, _CHAIN_BATCH_RUN) into the trial, with tests driven by injected timings.
- 2026-10-22: **E4b: the side tables are the trial's own.** _CHAIN_PLACED and _CHAIN_BATCH_RUN were keyed like the trial and cleared with it. They are now attributes of _chains.ChainTrial (a _choice.Choice): placed (the plans on each candidate of a CPU trial) and batch_run (a GPU trial's current run of batches). A test checks that the trial owns them and that clearing the trials drops them. The chain trial tests already drive it with injected timings (_chain_trial_batch).
- 2026-10-22: **E5a: one price-once rule.** _prices.price_once holds the rule four copies spelled out: this process's memo, else a valid record on file, else measure and store first-writer-wins. _cpu_forward_platform, _q15_tier0_fp16 and _direct_lagtap move to _prices (models layer) and use it, as does time_domain._corr_block_costs (which also co-decides the platform-FFT mode).
  - Fixed on the way: _direct_lagtap had no memo, so without a cost file it re-timed the direct refine on every call.
  - Fixed on the way: the correlation price accepted any stored record, so a malformed one raised; it is now replaced.
  - tests/test_prices.py covers the rule: memo, file, first writer, invalid record, failed price.
- 2026-10-22: **E5b: each Choice kind declares its reset scope.** _choice.SCOPES names every kind: workload (single-device, single-batch, fused-batch), which clear_autotune_cache forgets; or machine (sparse-way, vk-subgroup, coarse, gateway, interleave), which outlive it. _choice.choice refuses an undeclared kind, and reset(scope=...) replaces clear_autotune_cache's hard-coded list of three kinds. Tests declare their own kinds.
- 2026-10-22: **E5c: the bank's layout planning in _layout.** The template partition, the transform-size layout, the batch target, and the continuous correlation's block prices with their memo moved verbatim from time_domain to _layout (workloads layer; check_move: no definition changed). time_domain imports the names back. The test that patched the price memo patches _layout.
- 2026-10-22: **E6: one resolve().**
  - HierarchicalFilter._resolve computes the resolved plan once (an immutable _Resolved: chain, thresholds, refine reach, band fractions, Q15 recheck order, direct half-width) and again only after an input changes. Every setter that changes one drops it.
  - The CPU plan applies it once per plan and resolution; the GPU path (_gpu_calibration) reads it. The call-plan replay keys on it.
  - This replaces the _thr_applied flag, the GPU's separately keyed _gcal, and the Q15 order and direct half-width computed inside _execution_plan. That _gcal key left out the reference and relied on set_reference clearing it.
  - A persisted record was not added: no divergence remains to need one.
- 2026-10-22: **E7: one window parser.** HierarchicalSearch's refilter checked its windows against the parent's support with its own lenient parser. That parser accepted a bare [a, b] pair, did not merge overlapping windows, and took negative ints in pairs literally. It then handed the same windows to bank.filter_series, which parses them strictly, so the check and the call could disagree. refilter now uses the bank's parser (time_domain._normalize_windows), and search's copy is deleted.
- 2026-10-22: **E3: the filters leave __init__.**
  - MatchedFilter, CorrelationFilter and their helpers moved to _filter; HierarchicalFilter, _Resolved and theirs moved to _hierarchical (workloads layer).
  - __init__ is down from 3384 lines to 214: the public functions (taps_to_spectra, backend, targets, set_target, devices, include_dir, choose_threshold, get_autotune_state, clear_autotune_cache) and re-exports.
  - The public classes keep __module__ = "matchedfilter", so reprs and pickle paths are unchanged. The private names stay importable from the root, so lookups through it (and tests' patches of root names) work as before.
  - The six isinstance(self, HierarchicalFilter) checks in MatchedFilter's shared code became a class attribute (_is_hierarchical), so _filter needs no import of _hierarchical and the hot path adds no call.
  - Remaining for the exit criterion: the 7 upward edges in tests/test_layers.py.
- 2026-10-22: **E: no upward imports.** The last seven upward edges are gone; tests/test_layers.py's allowlist is empty:
  - device and _vksubgroup call _core and _kernel_id directly;
  - FilterResults and _EMPTY_FILTER_RESULTS moved to _results (FilterResults keeps __module__ matchedfilter.time_domain, so pickles load), and the window parser and block layout to a new foundation module _windows;
  - the device peak tables the backends report moved from _roofline to a new foundation module _peaks;
  - the cost calibrations that run hierarchical plans (calibrate_costs, calibrate_costs_gpu, device_costs, price_block_sizes and their clock reference) moved from gatechain to _calibration (workloads). Inside it gatechain's names are qualified (_gc.NAME), so patches of gatechain still apply. gatechain.calibrate_costs stays public as a documented entry point that _calibration registers itself behind, not as an upward import.
- 2026-10-22: **E complete.**
  - __init__ is 214 lines of public functions and re-exports.
  - No module imports upward, with an empty allowlist that test_layers keeps empty.
  - tools/check_move.py, which checked every E move, is deleted as planned.
  - Modules added in E: _costfile, _results, _windows, _peaks (foundation); _chains, _prices (models); _layout, _filter, _hierarchical, _calibration (workloads).
- 2026-10-22: **D4b, measured on Vulkan.** A plugin wrapping Vulkan's _build_pipeline recorded the SPIR-V each pipeline came from over the full suite on the 8060S: 212 of 281 shipped files.
  - The other 69 are variants this device does not select: _lds32 builds for 32 KB of shared memory, tier-C files (tc_*) for n above 65536, and packings past its limits.
  - Also among them: forward_bands_* and pack_coarse, which the backend requests (_vkcompute's fwd_bands and pack) but no test drives here. A test gap, not dead files.
  - No shipped SPIR-V file is unreachable by name.
  - Still open, on a CUDA device: the CUDA coarse builds a device cannot load, and the same measurement for PTX. Metal's files are checked against its manifest by test_metal.
- 2026-10-22: **A nightly crash left no report.** x86 shard 4/6 (Intel AVX3) aborted at rc=134, 48 s in, with no sanitizer report and no test named. Shard 4/6 ran clean twice on dev2 (Zen 5 AVX3) under the same build.
  - ASan wrote its report to fd 2, which pytest captures into a temporary file during each test, so the abort lost it. ASan and UBSan now write to log_path files, which sanitize.sh prints after the run.
  - The -q log named no test, so the gdb re-run had nothing to run. The shards now run -v, and sanitize_report's --crashing-test falls back to the last node id with no outcome (tests/test_sanitize_report.py).
  - sanitize.sh put its own -q before the caller's arguments, which cancels a -v. It now passes the caller's verbosity unchanged.
- 2026-10-22: **The x86 sanitizer crash, reported.** With the reports kept, shard 5/6 showed ASan's SEGV in fft() (balanced-inl.h:941, the small-plan path) from series_spectra / ap_mf_correlate_series, and the gdb re-run reproduced it in one test. The faulting instruction is `vmovaps %zmm0,-0x80(%r15)`: an aligned 64-byte store to the stack array t[AP_W], which the compiler aligned to 64 bytes. A general-protection fault from a misaligned aligned store is what ASan reports as a SEGV on an unknown address.
  - Suspect: ASan's fake stack frames (use-after-return detection) do not keep 64-byte-aligned locals aligned on CI's gcc 13 (GCC PR 110027); Fedora's gcc 15 does (a local probe), which is why dev2 passed.
  - sanitize.sh now probes the toolchain: an over-aligned local checked in nested frames under the sanitizer's defaults. Where it is misaligned, use-after-return detection is off for the run, with a notice; every other check stays. If the probe passes on CI, the misalignment is ours.
  - The annotation now leads with the crashing test, drops interpreter frames from the stack, and carries the gdb re-run's stack and registers (they were cut at the annotation's limit).
  - The next nightly settled it: the crashing test is test_automatic_series.py::test_continuous_forced_pair_batch_and_fir_bank (the earlier CI-only segfault), and under gdb the store's base register r15 = 0x7ffff4d019e0 lies outside the thread's stack (rsp 0x7fffffffb500), in ASan's fake stack; the store address r15-0x80 is 32-byte aligned, not 64. The first probe missed it: the compiler knew t was 64-byte aligned and folded the test to 0. The probe now reads the address through a volatile.
