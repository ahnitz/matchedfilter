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
