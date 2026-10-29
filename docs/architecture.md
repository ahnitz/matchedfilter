# Architecture

This page describes the library as it is at revision `33e22fa7` (2026-10-27): what the
public API is, how the code is layered, and the models and measured choices that decide
what a hierarchical call runs. Every statement names the module or function it describes,
so it can be checked against the code. Where the code and this page disagree, the code is
right and this page needs fixing. The dated documents in this directory record how the
design got here; [the index](README.md) separates them from the reference pages.

Several parts are being changed in parallel with this page: import cleanup, the
environment switches, the GPU cost model and the simulation kernel. The sections on them
describe the concepts and link to the code rather than restating internals.

## Public API

The package root, [`python/matchedfilter/__init__.py`](../python/matchedfilter/__init__.py),
defines `__all__` and re-exports the classes from the modules that implement them. The
three filter classes keep `__module__ = "matchedfilter"`, so their reprs and pickle paths
are `matchedfilter.*`.

| Name | Defined in | What it is |
|---|---|---|
| `MatchedFilter` | `_filter` | Flat peak-only filter: per (data, template) pair, the largest correlation sample in each output bin of a search window. |
| `CorrelationFilter` | `_filter` | The same spectral product, returning every complex lag. |
| `HierarchicalFilter` | `_hierarchical` | A `MatchedFilter` subclass that gates pairs with a chain of coarse tiers and refines the survivors. |
| `TimeDomainFilterBank`, `FilterResults`, `template_spectra`, `template_valid` | `time_domain` (`FilterResults` in `_results`) | A bank built from time-domain FIR taps: it partitions templates by length, chooses block sizes and filters continuous series. |
| `taps_to_spectra` | `__init__` | FIR taps to frequency-domain spectra, in C. |
| `devices`, `Device` | `device` | Device enumeration and the `"cpu"`, `"gpu"`, `"gpu:<n>"`, `"cuda"`, `"auto"` spellings (`device.parse`; `"cuda"` is an alias of `"gpu"`, whatever the backend). |
| `backend`, `targets`, `set_target` | `__init__` over `_core` | The CPU SIMD target in use, the targets the build and CPU support, and a way to narrow them. |
| `get_autotune_state`, `clear_autotune_cache` | `__init__` | A snapshot of the process's chain choices and joint trials, and a reset of every workload choice (see [Measured choices](#measured-choices)). |
| `PEAK_DTYPE` | `_results` | The structured `(index, value)` peak record. |
| `UnsupportedSize` | `_errors` | Raised when a device cannot run a transform length. |
| `include_dir` | `__init__` | The directory holding `matchedfilter.h`, for C callers. |

Outside `__all__`: `choose_threshold` (the single-tier gate, `gatemodel.gate_for`) and
`matchedfilter.search.HierarchicalSearch`, a tree of filters run over input blocks with
hooks (see [the search design](hierarchical-search-design.md)).

All filters take frequency-domain `complex64` spectra, the unnormalised forward transform
of each segment in natural order (`set_data`, `set_templates`), or time series through
`run_series` and `run_blocks` (`MatchedFilter.run_series`, `MatchedFilter.run_blocks`). The
default device is the CPU: `device.parse(None)` reads `MF_DEVICE` and otherwise returns the
CPU device. [The usage guide](usage.md) documents shapes, normalisation, windows and output
lifetime.

## Layers

### Python modules

The package's modules form layers, and a module imports only from its own layer or the
layers below it. `tests/test_layers.py` holds the table (`LAYERS`) and fails on an upward
import; its allowlist (`UPWARD`) has been empty since 2026-10-22. From the bottom:

| Layer | What lives there (examples; `LAYERS` is the full list) |
|---|---|
| extension | `_core`, the compiled C extension, below every Python module |
| foundation | `_config` (environment registry), `_choice` (measured choices), `_settings` (tunable dimensions), `_costfile` (`MF_COST_FILE`), `_results`, `_windows`, `_gpu_cache`, `_gputime`, `_coarse`, `_shared`, `_kernel_id`, `_execution_policy` |
| platform | `device`, `_vulkan`, `_cuda`, `_metal` (enumeration only), `_vksubgroup` |
| models | `gatemodel`, `gatechain` (gate model, chain planning, cost model), `_chains`, `_prices`, `_trial` |
| gpu host | `_gpuhost`, `_gpuhier`, `_gpuexec` |
| backends | `_vkcompute`, `_cudacompute`, `_mtlcompute` |
| workloads | `_filter`, `_hierarchical`, `time_domain`, `_layout`, `_calibration`, `search`, `_roofline`, `__init__` |
| applications | `benchmark`, `tutorial`, `demo`, `precision` |

The cost calibrations run hierarchical plans, so they live in `_calibration` (workloads),
above the model they feed. When the package loads, `_calibration` binds its `calibrate_costs`
to the public name `gatechain.calibrate_costs`: one function, whichever name plans, tools and
tests call. A model is cached and stored under the calls it was measured with (blocks,
rounds, seed) as well as n, templates and series group, so a calibration with other calls
never hands its model to a default one.

### The C engine (`src/`)

The CPU engine is C and C++ compiled into `_core`. Kernels are written once against the
`V_*` macros of `src/simd-inl.h`, which bind to Google Highway; `src/kernel.cc` includes
Highway's `foreach_target.h`, so one build holds a copy per SIMD target and
`HWY_DYNAMIC_DISPATCH` picks one at run time ([the SIMD layer](simd.md)). `MF_ISA` and
`set_target` narrow the choice.

| File | Role |
|---|---|
| `dispatch.c` | The public C API over whichever kernel the runtime dispatch selected. |
| `matchfilt.c` | The flat batched filter: ingest rearranges and conjugates, then the D x T pair loop with the product fused into the inverse transform ([design](design.md)). |
| `hmf.c` | The hierarchical engine: the tiers of a chain on survivor lists, then the refine. It takes thresholds from the caller and holds no statistical model. |
| `balanced-inl.h`, `elemfft-inl.h`, `product-inl.h`, `codelets-inl.h` | The width-generic four-step transform and its codelets; `codelets-inl.h` is generated by `src/gen.py`. |
| `q15-inl.h`, `q15.h`, `codelets-q15-inl.h` | The int16 (Q15) coarse screen; its codelets are generated by `src/gen_q15.py`. |
| `gate16.cc` | The FP16 first gate on ARM NEON with FP16 arithmetic; stubs elsewhere. |
| `td-inl.h` | The direct (time-domain) refine: correlation at a few lags around a survivor's coarse peak. |
| `kernel_avx1.cc`, `simd-avx1.h` | The `AVX` back end: SSE4's kernels with the float paths at 8 lanes, for CPUs with AVX but not AVX2. |
| `gauss.cc` | Counter-based normal draws for the gate model's simulation, identical on every ISA. |
| `fft_accel.c` | The block forward through the platform FFT where one exists (vDSP on macOS); absent elsewhere. |

CI checks that the generated codelet headers match their generators (`generated-files` job
in `.github/workflows/ci.yml`).

### The extension boundary (`python/matchedfilter/_core.c`)

`_core.c` wraps the engine for Python: the plan types `MF` (flat), `HMF` (hierarchical)
and `Root` (the root stage of `search.HierarchicalSearch`), and module functions. Besides
the target controls (`targets`, `set_target`, `backend`), the gate model's inner loops are
here: `simulate` (the one simulation, below), `records_within`, `chain_candidates` (the
threshold-split search; the Python recursion in `gatechain._chain_candidates` is its
reference, selected by `gatechain._C_SEARCH`), and `gauss_fill`. Buffers are checked at
the boundary independently of the Python API. `MF` and `HMF` share one implementation of
ingest, `run` and `run_series` (`bind_set`, `bind_set_batch`, `bind_run`,
`bind_run_series`, reading a `filter_view` of the object); every buffer a binding takes is
released on every path, which `tests/test_native_buffers.py` checks by reference count.

### GPU kernels

GPU kernels are written in Slang (`src/gpu/*.slang`). They are compiled ahead of time and shipped:
SPIR-V and Metal sources by `tools/build_spirv.py`, PTX by `tools/build_ptx.py`, into
`python/matchedfilter/spirv/`, `metal/` and `ptx/`. No PTX module declares more than the 48 KB
of static shared memory CUDA allows a block (such a module launches on no NVIDIA GPU, so
`build_ptx` does not ship it); where a kernel's staging is the reason, its 32 KB staging build
(`_lds32`) serves that length. `_kernel_dirs.shipped` decides which
directories a platform's wheel carries (SPIR-V everywhere, PTX off macOS, Metal on macOS).
`_kernel_id` gives each backend's shipped programs an identity, which the stored kernel
choices include in their keys, so a build with other kernels measures afresh.

### The GPU host layer and backends

GPU operations are written once, above a thin per-API driver:

- `_gpuexec.Executor` holds every operation: full and continuous correlation, the forward
  transform, flat peaks, follow-up items and deferred forwards. Each decision it makes
  uses what the driver reports about the hardware, never which API it is.
- `_gpuhier.HierOps`, a base of `Executor`, is the hierarchical search: one recording per
  call shape runs the feed, tier 0, a second tier, the refine and the readback on the
  device, with no counts read back between stages.
- `_gpuhost` is pure host logic shared by every backend (windows, bin shifts, the band
  forward rule `band_forward_wanted`); `_gpu_cache` holds input residency and in-flight
  results; `_shared` provides host-visible allocations with DLPack lifetimes; `_gputime`
  collects device time under `MF_GPU_TIMING=1`.
- Each backend's `Context` (`_vkcompute.Context`, `_cudacompute.Context`,
  `_mtlcompute.Context`) inherits `Executor` and `InputUploads` and supplies only driver
  primitives: allocate, record, submit, read back. All three call their APIs through
  `ctypes` with no compiled host code.

`_filter._compute_module` picks the driver from `Device.backend`: Metal on Apple, CUDA on
NVIDIA, Vulkan otherwise. `device.devices` lists the CPU first, then Metal devices, CUDA
devices, and Vulkan devices; a Vulkan entry for an NVIDIA GPU is skipped when CUDA lists
it. Software Vulkan devices are listed but flagged, and a bare `"gpu"` skips them.
`HierarchicalFilter._MAX_TIERS` limits GPU chains to two tiers and CPU chains to eight.

## A hierarchical call, end to end

`HierarchicalFilter(n, ndata=1, ntemplates=1, snr=5.5, fd=1e-2, chain=None, device=None,
*, valid=None, max_tiers=3, search_window=None)` holds its inputs. Before it runs, it
settles everything that decides which pairs are refined into one immutable record, the
resolved plan
(`_hierarchical._Resolved`: chain, per-tier thresholds, the model's refine reach, per-tier
band fractions, and the CPU direct refine's half-width), computed by
`HierarchicalFilter._resolve` and dropped by every setter that changes an input
([the resolved plan](resolved-plan.md)).

- **Chain.** A pinned `chain=` is used as given. Otherwise `HierarchicalFilter._choose_chain`
  calls `gatechain.choose_chain` with this device's cost model (`_cost_model`), caches the
  result per (n, snr, fd, tiers, window, profile signature, device, gate kind, direct
  refine) in `_chains._CHAIN_CHOICE`, and runs the model's best chain. `MF_CHAIN_FORCE`
  overrides it for measurement.
- **Thresholds.** `set_coarse_threshold` gives them explicitly (a pinned chain is then
  required). Otherwise `HierarchicalFilter._thresholds` takes them from
  `gatechain.chain_thresholds` for the chain, the reference, `snr` (or `set_first_stage`'s)
  and `fd`. The `threshold` passed to `run` is the final reporting cut, separate from the
  gates.
- **Execution.** On the CPU, `_execution_plan` applies the resolved plan to an `_core.HMF`
  plan, which runs tier 0 on every (block, template) pair, each later tier on the previous
  tier's survivors, and the refine on the last tier's survivors (`src/hmf.c`). On a GPU the
  same chain runs as one recording (`_gpuhier`).
- **Refine.** Survivors are refined by an n-point transform and a peak scan over each bin,
  or, on the CPU with real taps and one bin per pair, by the direct refine around the last
  tier's coarse maximum ([CPU direct refine](cpu-direct-refine.md)). `MF_DIRECT_REFINE=0`
  turns the direct refine off.

`config` reports the chain in use and `refine_rate` the fraction of pairs refined over the
plan's lifetime. On the CPU, `tier_stats` gives each tier's passes and ticks (it is `None`
on a GPU). `autotune_info` says whether the plan's chain is pinned, the model's or forced,
and whether a trial has locked its arm.

## The gate model

The gate model decides, for a chain of bands, the thresholds that meet a false-dismissal
budget, and the noise pass rates that price it. It is computed from the reference profile
(the expected output power per frequency bin, `set_reference`) and the algorithm; nothing
is tabulated. The code is `gatechain` (chains, any number of tiers) and `gatemodel` (the
single-tier case and the draw counts).

### One simulation

The model is one simulation of stationary Gaussian noise with the reference's output
spectrum (`gatechain._simulate`, which calls `_core.simulate`). Each draw is a block's n
bins with variance p_k. The fine statistic is their n-point transform, and band b's
statistic is the b-point transform of bins [0, b), normalised to unit variance per
component, so the tiers and the fine stage share their noise as the filter's do. Every
maximum is taken over the whole searched window, over the lags the engine visits for it
(`gatechain._engine_lags`, mirroring `hmf.c`).

Two readers take their statistics from the same simulation:

- `gatechain.signal_draws` adds a signal of strength `snr` arriving at a uniformly random
  time (16 sub-sample phases, `_NF`) through the transforms' linearity, and returns each
  band's coarse window maximum with the fine window maximum. Only draws whose fine
  statistic reaches `snr` somewhere in the block hold records, and the simulation runs
  longer where few do (at a very large `snr`).
- `gatechain.noise_block_maxima` reads the same draws without the signal: each band's
  noise-only window maximum per block, from which a chain's joint pass rates follow
  (`gatechain._reach`).

`gatechain.kept_draws` selects the draws the fine stage keeps (fine maximum at least
`snr`): the false-dismissal budget is a fraction of those.

Draw counts scale with the budget (`gatemodel._nsamp_for`: 200/fd signal draws, at least
20,000 and at most 3,000,000; `gatechain.model_draws` uses 20,000 noise blocks). About half
the draws are kept, so a chain's budget rests on about 100 dismissed draws for fd between
about 7e-5 and 1e-2. Above 1e-2 the 20,000-draw floor gives more; below 7e-5 the cap gives
fewer. A budget that leaves fewer than 8 dismissed draws is refused
(`gatechain._chain_candidates`, `gatemodel.gate_for`).

Profiles that agree in shape and in every band's signal response share cached simulations
and plans (`gatechain._similar_get`: a cosine of at least `_REUSE_COS` and a gate response
within `_REUSE_RESPONSE`), because a search's banks have nearly one reference.

### Chains and the budget split

`gatechain.enumerate_chains` lists every increasing tuple of up to `max_tiers` power-of-two
bands from 64 to n/2 that hold some of the reference's power (`usable_bands`).
`gatechain.plan_chain` gives each chain the thresholds that meet the budget at the lowest
modelled cost (`_chain_candidates` searches the budget's split between tiers over the
grids `_SPLIT` and `_SPLIT_COARSE`), and `gatechain.choose_chain` prices them all and
returns the best with the list.

- A split in which a tier passes more than `_USELESS_PASS` (half) of its pairs on to
  another tier is skipped when choosing.
- Chains whose costs are within `TIE` (5%, `_choice.TIE`) of the cheapest are tied; the
  tie goes to the cheaper chain on a calibration-free operation count (`_flop_cost`), so the
  choice does not flip with calibration noise (`gatechain.pick_stable`).

### What `fd` means

`fd` is a mean target: the expected fraction of the detections the flat filter makes at
strength `snr` (fine maximum at least `snr`) that the chain dismisses, for signals at that
strength in Gaussian noise with the reference's spectrum. It is not a bound for every plan,
population or noise.

- A single tier's gate is the kept coarse maximum with floor(fd M) of the M kept draws
  below it (`gatemodel.gate_for`; the one-tier branch of `_chain_candidates`), so its
  dismissal on fresh draws averages fd.
- A multi-tier chain searches threshold splits on the same draws it is judged on and keeps
  the cheapest, which favours splits whose dismissal those draws understate. Its budget is
  therefore cut by `_SPLIT_TOLERANCE_Z = 0.75` standard errors of the dismissed count. The
  bias does not depend on fd or n: on independent draws (`tools/split_bias.py`, 10
  profiles x 30 model seeds, fd 1e-2 and 1e-3, n = 2048 and 4096), with no cut two-tier
  plans dismiss 1.02-1.03 of the budget and three-tier plans 1.03-1.04. The cut is about
  twice that, so with it the plans made for a given chain dismiss 0.95-0.97 of the
  budget, and the chain `choose_chain` picks, whose choice among chains adds a selection
  bias of its own, 0.96-0.98. The value 0.75 came from one model seed shared by every profile, which sat
  high; which value z should target is open
  ([the 2026-10-27 log entry](gate-model.md#the-split-bias-does-not-depend-on-fd-and-the-cut-is-twice-its-size-2026-10-27)).
  If the split grids change, measure the bias again with `tools/split_bias.py`.
- Individual plans scatter about the mean. With K of about 115 dismissed draws per plan
  (fd 7e-5 to 1e-2, where `gatemodel._nsamp_for` scales the draws with 1/fd), a plan's
  realised dismissal has a standard deviation of 0.09 of fd, 1/sqrt(K + 1), for one-, two-
  and three-tier plans alike. Of 1500-6000 plans per tier count the worst was 1.26-1.41 of
  the budget, but averaged over 30 model seeds no (profile, chain) dismisses more than
  1.071. The spread comes from the finite draws, not from the split search, so more
  draws, not a larger cut, would narrow it. The gate model's one seed gives every profile
  the same underlying noise, so a job's plans share one draw's luck.
- The CPU direct refine's window may lose a further `gatechain._LOCALISE_SHARE` (5%) of fd
  (`gatechain.direct_halfwidth`; the plan runs its half-width plus one coarse sample,
  `HierarchicalFilter._direct_halfwidth`).

Reduced-precision tiers (the Q15 screen, the FP16 gates) answer to the same budget against
the flat filter; [reduced-precision gates](reduced-precision-gates.md) gives their error
models. `tools/fdr_audit.py` measures a chain's dismissal against the flat filter by
injection, two-sided, and `tools/gate.py` runs it before every merge.

### Refusals

`HierarchicalFilter._choose_chain` raises `ValueError` when no chain can be planned: a
reference with no localised correlation peak (`_hierarchical._uncovered_reference`, every
band's effective bandwidth below `_BEFF_MIN`), a transform size too small for any band of
at least 64 at or below n/2 (n = 64), or a budget the draws cannot resolve
(`_uncovered_message`). A pinned chain with explicit thresholds always runs, with whatever
guarantee those thresholds carry.

## Cost models

A chain's cost is the model's expected cost per (block, template) pair
(`gatechain.CostModel.chain_cost`):

    first_tier(b1) + sum over later tiers i of P(reach tier i) * sparse(b_i, density)
                   + P(reach refine) * refine(density)

where the pass probabilities come from the noise simulation and the per-tier prices are
measured on the machine the job runs on. A `CostModel` holds, per transform size n: `dense`
(a first tier per pair, per band), `sparse` (a later tier per survivor, as a function of
survivor density), `refine` (per refined pair, as a function of density), `block` (fixed
work per block), `screen` (the Q15 screen as the first tier, where the back end has one),
`excess` (a bounding first tier's extra passes), and `forward` with `band_forward` (the
forward's share of `block`, and whether the device can write only the widest band). The
model ranks chains. It cannot change a single tier's gate; for a multi-tier chain it picks
among budget splits that all meet the budget, so different costs can move the thresholds.

- **CPU** (`_calibration.calibrate_costs`). Synthetic analytic noise and whitened random
  templates, at thresholds placed for target survivor densities (`gatechain._CAL_DENSITIES`),
  run through the engine; costs are read from the engine's per-tier tick counters
  (`tier_stats`), not from wall-clock differences. Calls are 32 blocks of
  `gatechain._CAL_TEMPLATES` (64) templates at the plans' own series group. Band costs are
  shared by every n on the same series group. The Q15 screen is priced per band, and
  `CostModel.first_tier` picks the cheaper first tier.
- **GPU** (`_calibration.calibrate_costs_gpu`). The same construction, timed by device
  timestamps around each submission, each time taken relative to a fixed reference call
  (`_calibration._ClockRef`) so that clock changes cancel. A tier's cost is the difference
  between runs that differ in that tier. A second tier's price is the slope of device time
  against first-tier survivors over the calibration densities (`_calibration._sparse_rows`,
  `_GPU_SPARSE_FIT = "slope"`), so a per-call cost cannot be charged to the few survivors of
  one density point.
- **Other prices** (`_prices.price_once`): the CPU platform forward, the direct refine's
  per-lag and per-pair prices, and the continuous correlation's block costs
  (`_layout`). Each is timed once per process, or once per machine with `MF_COST_FILE`,
  where the first record written is the one every process uses.

Cost models are kept per process (`gatechain._COSTS`) and in `MF_COST_FILE` when it is set
(`gatechain._stored_cost_model`; a record that is not a cost model is reported and
recalibrated). A model another process stored first is the one used
(`_costfile._store_first`). `_calibration.price_block_sizes` uses them to price a bank's
layout at each candidate block size; that layout is one arm of the bank's joint trial
(below).

## Measured choices

Where the library cannot predict which of a few candidates is faster on this machine, it
measures them on the job's own calls. One lifecycle serves every such choice:
`_choice.Choice`.

- **Preference.** `candidates[0]` is the preference. It stands unless another candidate is
  clearly faster.
- **Paired rounds.** `Choice.play` runs every live candidate on the same call, back to
  back. Each timed run comes right after an untimed run of the same candidate, so every
  timed run is a second run (a GPU batch run second ran 20-30% faster). The order reverses
  every round. Candidates that would run the call identically run once and share the
  timing.
- **The rule.** `_choice.paired_choice` judges rounds as ratios to the preference. A
  candidate wins when at least 75% of the rounds are faster than the preference by more
  than `TIE` (5%). The preference stands at once when, for every candidate, at least 75% of
  the rounds are not faster by more than `TIE`. Otherwise the contest takes more rounds, up
  to its cap, and at the cap the preference stands. No decision is made before
  `MF_TRIAL_ROUNDS` rounds (default 5, `_choice.MINIMUM`), and the cap is twice that
  (`_choice.rounds`).
- **Exact elimination.** A candidate that can no longer reach the share of wins it needs by
  the cap is dropped from later rounds (`_choice.can_still_win`); a test enumerates every
  win/loss history against `paired_choice` (`tests/test_paired_cpu_trials.py`).
- **Confirmation.** With `confirm=True`, a challenger the rule picks is not locked at once:
  it must win again in fresh rounds alone against the preference, or the preference stands.
- **Budget.** Calls that cannot be rounds count against a budget (`Choice.tick`); when it
  is spent, the contest ends on the rounds it has.
- **Lock.** The winner is locked for the process and, with `MF_COST_FILE`, stored as
  `choice|<store_key>` with its medians. A lock already on file is reused without timing,
  and the first lock written stands: a process that finds another's lock adopts it
  (`Choice.lock`, `Choice._write`). Samples of an open contest are not stored.
- **Scope.** `_choice.SCOPES` declares each kind of choice as `workload` (forgotten by
  `clear_autotune_cache`) or `machine` (a hardware property that outlives it).

Two kinds of choice are first decided offline, because a real call cannot carry their
candidates. The GPU coarse kernel layouts and gate ways per band are ranked on synthetic
dispatches (`_coarse.screen`), and `_coarse.shortlist` keeps the fastest two; the second is
then played on real batches as a kernel slot (below). The Vulkan subgroup size
(`_vksubgroup`) is measured in subprocesses, because a size can lose the device, and decided
by `paired_choice` over the sizes' timings of the same calls.

### Joint trials

`_trial` decides coupled choices together, over complete configurations, with one trial per
key:

- **Arms** are labels in the grammar of `_settings`: `default` (every dimension at its
  default) or `<dim>=<value>[,<dim>=<value>...]` in declaration order (`_settings.compose`,
  `_settings.moves`). `default` is the preference.
- **Instances** resolve an arm to a configuration (`arm_config`), run it (`use_arm`) and
  lock it (`lock_arm`). A `TimeDomainFilterBank` is one (its block-size layouts and its
  plans' screens; its rounds run in `filter_series_many` through `time_domain._joint_round`),
  and so is a `HierarchicalFilter` used on its own (its screen; rounds in `run_series`). A
  plan inside a bank is governed by the bank's trial.
- **The bank's arms** (`TimeDomainFilterBank._joint_arms`): `default` is the bank at its
  smallest candidate block size; `n=<size>` is the next single size; `n=model` is the
  layout `price_block_sizes` prices cheapest; `q15=1` and `q15=0` turn the Q15 screen on or
  off where the first band has one. Each plan runs its model chain under every arm: the
  gate chain is never an arm.
- **Coordinate passes** (`_trial.current_pass`). A first pass offers `default` and the arms
  that move one dimension. A pass that locks an arm other than its base opens the next pass
  around that arm, with each dimension it has not moved moved too (`_settings.around`). The
  search ends at a pass that keeps its base; a first pass that keeps `default` ends it.
- **Passes** are `Choice` contests with confirmation and a budget of
  `_trial.UNROUNDED_BUDGET` calls that could not be rounds. Each pass's lock is stored under
  `_trial.pass_key("joint|" + key, base)`; `_trial.winner` and `_trial.stored_search`
  read the end of a search from the file.

With `MF_AUTOTUNE=0` no timed choice runs on real calls (the joint trials, the GPU device
trials and single-template side below, and the Vulkan subgroup size): a bank builds the
model's priced layout, every plan keeps the model's chain and screen setting, and batch
dimensions take their locks or defaults. Cost calibration and the offline kernel screens
still run.

### Tunable dimensions and the settings store

`_settings.DIMS` declares every dimension a trial can move, with how its values parse and
print, its default and its scope:

- **subject** dimensions are resolved by each instance: a bank's block size `n` and a plan's
  screen `q15`;
- **batch** dimensions are read by the code they steer while a batch runs: a GPU batch's
  fusion `fuse` and Vulkan interleave depth `interleave`, where a GPU batch's follow-ups run
  (`single`), and where a lone single-template call runs (`side`);
- **kernel slots** `kern:<what>:<band>` carry a call's default kernel and its alternative
  (`_settings.slot`): the coarse layout, the gate way and the sparse readback.

`_settings.setting` answers a batch dimension: the arm a running trial plays, else the lock
of a device set holding the device, else the default. The GPU device trials that decide
them (`gpu-batch`, `gpu-single`, `gpu-kernels`; `time_domain._gpu_trials`) use the same
paired `Choice` and coordinate passes (`_trial.current_pass`). The single-template side
(`single-device`, `time_domain._single_choice`) is one paired `Choice` between two
candidates, the default and the CPU, with confirmation.

### What `MF_COST_FILE` holds

`_costfile` is the one reader and writer of the file: a writer lock on a `.lock` sidecar,
then an atomic replace, so unlocked readers never see a partial file. Its records, by key
prefix:

- cost models, keyed by n, template count, series group and gate kind on the CPU, and by
  n, device, gate kind and fit on a GPU, with the calls measured appended when they are not
  the defaults (`_calibration.calibrate_costs`, `calibrate_costs_gpu`);
- prices: `cpu-fft`, `corr3`, `corr-pfft`, `choice` + `direct-lagtap` and `direct-pair`
  (`_prices`, `_layout`);
- joint-trial passes: `choice` + `joint` + `bank` or `plan` (`_trial.Trial`);
- GPU device trials and the single-template side: `choice` + `gpu-batch`, `gpu-single`,
  `gpu-kernels` and `single-device` (`time_domain`);
- kernel shortlists and the Vulkan subgroup size: `choice` + `coarse`, `gateway` and
  `vk-subgroup` (`_coarse.shortlist`, `_vksubgroup`).

The parts of a key are joined by `|` (cost models and some prices by `,`); the formats
belong to the code that writes them. Records of the trial format before
2026-10-21 are reported and ignored (`_costfile._LEGACY_PREFIXES`);
`tools/migrate_cost_file.py` removes them.

With a shared file, every process sharing it makes the same choices and reports the same
peaks; `tests/test_reproducible_choices.py` checks two processes, and `tools/gate.py` runs
it repeatedly. Without one, each process measures afresh, and two processes can choose
differently on timing noise; every choice still meets the budget, but pairs near a gate can
be refined in one process and not in another.

## Configuration

Every environment variable the package, the C extension and the tools read is declared
once, in the registry [`python/matchedfilter/_config.py`](../python/matchedfilter/_config.py)
(`VARS`): its kind, default, which side reads it, its section and what it does. The
sections are `config` (user configuration), `diagnostic` (output only), `override`
(changes what runs, for measurement and tests) and `tools`. `_config.check_environment`
runs at import, before `_core` reads anything: it raises on a malformed value and warns
about a removed or unknown `MF_*` name. The C side reads flags with the same rule
(`src/env.h`). [Environment variables](environment.md) is generated from the registry by
`tools/gen_environment_doc.py`, and
`tests/test_config_registry.py` checks that every `MF_*` name the code reads is registered,
that every registered name is read, and that the document is current. This page does not
list the variables; the registry is the source of truth.

Execution scheduling rows (series groups per device and shape) come from
`python/matchedfilter/execution-policy.json` through `_execution_policy`; they select
scheduling only, never calibration or device capability.

## Testing and gates

The test suite is `tests/`, run with pytest. Tests and benchmarks run single-threaded
(`OMP_NUM_THREADS=1` and the BLAS equivalents, as CI sets them). `tests/conftest.py`
removes every `MF_*` variable from the environment before collection except `MF_ISA` and
the tool paths (`--keep-mf-env NAME` keeps another), probes for a usable GPU
(`conftest.usable_gpu`) so GPU tests skip cleanly without one, and adds `--shard K/N`,
`--reverse-modules` and the opt-in `--run-performance` checks. CI also runs the suite with
`MF_ISA` forced to SSE4, AVX and AVX2, so a change to the CPU kernels should be tested under
those targets locally as well.

Some suites pin contracts the rest of the code relies on:

| Test | What it pins |
|---|---|
| `test_search_contracts.py` | Search-level behaviour per engine: noise and injections, lazy template loading, the gate chain's thresholds, autotuning. |
| `test_fdr_calibration.py`, `test_gate_model.py`, `test_gate_chain.py`, `test_gate_draws.py` | The gate model's dismissal and the simulation's draws. |
| `test_tier_conformance.py`, `test_coarse_conformance.py` | Every CPU tier kind and every GPU coarse layout refines exactly the pairs above thresholds placed in gaps of the exact maxima. |
| `test_choice.py`, `test_paired_cpu_trials.py`, `test_joint_trials.py` | The measured-choice rule and the joint trial. |
| `test_reproducible_choices.py` | Two processes sharing a cost file choose alike. |
| `test_layers.py`, `test_config_registry.py`, `test_docs_index.py` | The import layers, the environment registry, and this directory's index. |

`tools/gate.py` is the merge gate, one command for every check a change must pass. Its
stages, in order: `suite` (the full suite), `check` and `settled` (`tools/ladder.py --check
cpu`, the GPU against the CPU, fresh and after the trials have locked; these need a GPU
and a production-like bank and profiles, and are skipped without them), `margin`
(`tools/gate_margin.py --loud`), `fdr` (`tools/fdr_audit.py`), `repro`
(`test_reproducible_choices.py`, repeated), `followups` (`test_call_plan.py` and
`test_followup_batch.py`, repeated) and `ci` (`tools/ci_status.py --schedules`: main's and
the scheduled workflows' latest runs are green). A skipped stage is reported as skipped,
never as a pass.

The CI workflows are in `.github/workflows/`:

| Workflow | Runs |
|---|---|
| `ci.yml` | On pushes to main and `ci/**` proof branches and on pull requests: the suite on Python 3.11-3.15 across the SSE4, AVX, AVX2 and widest targets (one job from the sdist), Linux arm64, the generated-codelet check, a wheel smoke test, and Metal on a macOS runner. |
| `nightly.yml` | The suite under AddressSanitizer and UndefinedBehaviorSanitizer (x86 and arm64), the suite in reverse module order, and the musllinux wheel with its full suite. |
| `benchmark.yml` | The benchmark on each platform, weekly, by hand and on `ci/bench/**` branches; the documentation site is built on every run and published from main. |
| `release.yml` | On a published release: requires a green CI run of the commit, builds and tests every wheel and the sdist, and publishes; weekly, a rehearsal without upload. |
| `wheels.yml` | The reusable wheel build the others call. |

The standard performance workload is `tools/ladder.py`, the three-level search on a real
bank; [the tooling map](../tools/README.md) lists every tool.

## Where to read next

- [Using matchedfilter](usage.md) for the API in practice.
- [The hierarchical filter](hierarchical.md), [the resolved plan](resolved-plan.md) and
  [reduced-precision gates](reduced-precision-gates.md) for the gating contract.
- [Environment variables](environment.md), generated from the registry.
- [The documentation index](README.md) for every other document, reference or dated.
