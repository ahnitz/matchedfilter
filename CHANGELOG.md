# Changelog

Alpha releases may change the API. Pin a version for reproducible work.

## Unreleased

### Added

- An AVX back end for CPUs with AVX but not AVX2 (Sandy and Ivy Bridge), which ran the
  4-lane SSE4 kernels because Highway has no AVX1 target. The float kernels (transforms,
  products, peak scans) run at 8 lanes on 256-bit AVX without FMA (src/simd-avx1.h,
  src/kernel_avx1.cc). The Q15 screen and the integer helpers stay SSE4's. It is
  selected automatically, `targets()` lists it as `AVX`, and `MF_ISA=SSE4` keeps the
  4-lane kernels. Results match the other ISAs to fp32 rounding (peaks identical, |snr|
  within 5e-7). Fine-stage call on an Ivy Bridge E5-2660 v2: x1.59 at n=1024, x1.32 at
  2048, x1.40 at 4096, x1.25 at 16384.
- CPython 3.15: release wheels (Linux x86-64 manylinux and musllinux, macOS arm64) and CI
  test jobs. Wheels build with cibuildwheel 4.3.4.
- tests/test_lint.py: the library is pyflakes-clean, and stays so. pyflakes reported 143
  warnings in python/matchedfilter (imports left behind when code moved between modules,
  re-exports of private names, locals computed and dropped; none was a live bug), now 0,
  and the test fails on any new one. It skips where pyflakes is not installed; CI installs
  it with the test extra. tools/, tests/ and examples/ lost their dead imports and locals
  too.

### Changed

- One generator for every GPU kernel, `tools/kernel_variants.py`: the table of every Vulkan,
  Metal and CUDA artifact, the facts each is built with and the one way each is compiled
  (`build_spirv.py` and `build_ptx.py` run it; `build_forward.py` is gone). A rebuild
  reproduces all 275 SPIR-V, 290 Metal and 309 PTX artifacts byte for byte. Each backend's
  manifest has one schema (Metal has its own instead of columns in the SPIR-V one), and the
  hosts read every kernel fact from it through `matchedfilter._kernels`: the 32 KB builds,
  Vulkan's bindings and push-constant bytes, Metal's and CUDA's group sizes and the coarse
  candidates' memory. That last was a formula overstating the fp16 builds' memory about
  twice, so a 64 KB device now also tries the coarse packings that fit (band 1024 at 16
  pairs). Metal ships one survivor compaction each, as Vulkan and CUDA do, in place of 30
  per-length builds that differed only in their `#line` names. Vulkan's and CUDA's kernel
  identities are unchanged; Metal's moves once. CI checks the kernels and manifests against
  the generator.
- A GPU chain's forward is priced from the feeds the calibration times -- the band forward
  at each widest band and the full forward, per block -- taking the feed the backend's own
  rule takes for the chain, in place of a one-point fit of the band forward
  (`forward * (1/2 + B/2n)`) plus a recompute at a running mean of earlier calls'
  refine-block fractions, which the refine term already held. test27 ladder on the 8060S:
  0.96x the steady time (fine stage 0.94x, three runs each). A stored GPU cost model is
  measured afresh once.
- A GPU batch is always fused, in lockstep, and the `gpu-batch` device trial that chose
  fusion and the fused interleave depth is gone. Pinned at production length (test27 ladder,
  2-3 runs an arm), unfused batches were 3-17% slower on the 8060S, RENOIR and Iris Xe and
  the depth-3 interleave no faster; the trial had locked unfused on replays of short runs
  on an idle device, where it timed 6-15% faster.
- Block size and the Q15 screen are decided by one joint trial on real calls, on the CPU
  and GPU alike, in place of three separate trials, and the gate chain is no longer timed:
  each plan runs its model chain (`MF_CHAIN_FORCE` pins one for measurement). The trial's
  arms are complete configurations: the default (the smallest block size, each plan's model
  chain and the model's screen setting) and one-step deviations from it (another block size,
  the model's priced layout, the screen off or on). They are timed in paired rounds on the
  same jobs of two of a batch's banks and pooled as ratios to the default. Arms that can no
  longer win leave the rounds, and a winner other than the default must win again alone
  against it before it locks. The old chain trial locked one chain for plans of every
  profile, which ran 2-14% slower per call (dev1, dev2, Haswell, Ivy Bridge). On the test67
  leaves at their mean of 12 calls per bank, total CPU is 4.6% lower on dev2 and 6.0% lower
  on dev1. `MF_TRIAL_ROUNDS` replaces `MF_BLOCK_TRIALS` and `MF_CHAIN_TRIALS`, and
  `MF_CHAIN_MARGIN` is gone (all three now warn); `tools/migrate_cost_file.py` removes the
  superseded trial records from a cost file. `HierarchicalFilter.autotune_info` reports
  status `model` when no trial ran.
- Block sizes are chosen on real calls in every run, not only with MF_COST_FILE: the first
  reference's banks run each candidate size in paired rounds and the search locks the fastest,
  pooled over its banks. Candidates are the smallest single sizes, smallest first (a tie keeps
  the smallest), then the model's layout. The model alone misjudged sizes under production load:
  fresh processes on a loaded Haswell node put up to 231 of test67's 323 banks on 4096, which
  ran 1.6-1.95x slower than 2048. Banks built after the lock skip block-size pricing. CPU leaves
  of a search run as one filter_series_many batch (the results are the same).
- Hierarchical CPU choices hold under changing machine load. The cost calibration times every
  quantity round-robin (each timed call after an untimed one on the same plan) and keeps each
  one's minimum: under a dynamic load the calibrated costs spread up to 4.7x between
  processes, now under 1.2%, so block size, chain and tier thresholds stop moving with the
  load. Two pricing errors that sent single-tier band-256 chains to the transform refine at
  ~2x the best chain's cost are fixed: the direct refine's window is priced with the draws
  the chain runs with (a tenth of them gave 2 coarse samples against 62), and a one-tier
  chain behind the Q15 screen, which reports no lag, is priced with the transform refine.
  A close call between the screen and the float first tier takes the screen (within TIE).
  test27 full job, both variants together on one node: Haswell steady 0.84 -> 1.21 M
  templates in real time (fine stage 1.01 -> 1.59 M, job 3331 -> 2565 s), Ivy Bridge
  0.23 -> 0.31 M (job 11365 -> 9163 s); dev2 unchanged (its choices were already right).
  Triggers move only near threshold (the tier thresholds follow the chosen chain, within
  the false-dismissal budget): Haswell 5 of 27,501 H1 and 28-36 of 30,414 L1, max snr 6.13.
- The gate model's simulations draw from a counter-based generator (src/gauss.cc:
  Threefry-2x32 and Box-Muller, identical for any vector width; AVX2 and AVX-512 agree bit
  for bit, SSE4 to the last ulp of its log and sincos), so their draws, and the thresholds
  they place, differ from before within the simulation's own error (thresholds +-1.4%).
- One false-dismissal budget per plan, met by construction (docs/gate-model.md,
  2026-10-29). A plan's structure is searched on half of the gate model's detections:
  the split of fd between its tiers and, on the CPU, the direct refine's window. Its
  thresholds are fitted on the other half, every tier moved by one shift that leaves
  j - 1 of that half dismissed (`gatechain.plan_chain`). The fit half is independent of
  everything the search chose, so every plan dismisses fd on average, with no correction
  for the search, the chain `choose_chain` picks included.
  - `_SPLIT_TOLERANCE_Z` is gone. It was the 0.75 cut, and with costs from a real machine
    the bias it cut was larger: the CPU's plans dismissed 1.02-1.08 of fd, tiers and
    window together.
  - On independent draws (`tools/split_bias.py`: 10 profiles x 30 model seeds, fd 1e-2
    and 1e-3, n = 2048 and 4096, priced by operation count and by Zen 5 costs with a
    direct refine) every chain's plans average 0.997-1.005 of fd and the picks
    0.998-1.013.
  - Each plan rests on half the draws, so its sd is 0.14 fd (0.09 before), and 5% of
    plans dismiss more than 1.25 fd, the tolerance decision D1 sets
    (`gatemodel.fit_order`).
  - Thresholds change everywhere.
  - Meeting fd where the plans exceeded it costs CPU throughput: on test27's bank
    (`tools/ladder.py`), 0.98 on dev1 at the production model seed (paired), and a median
    of 0.976 over 8 model seeds.
- The CPU direct refine's window is inside the budget. The detections it misses count as
  dismissals, and the split search tries every half-width that misses a different set,
  priced per lag, beside the whole-block refine.
  - `CostModel.with_direct` takes ticks per lag.
  - A window may miss at most `gatemodel.window_allowance` of the search half's
    detections (15-21 of the about 47 dismissals the budget allows). Within that, the
    chance that the fit half leaves the window no room, and the plan refines by
    transform, is at most what D1's tail leaves.
  - `_LOCALISE_SHARE` (up to 5% of fd on top of the budget) and the window's extra
    coarse sample are gone.
  - A pinned chain's thresholds are priced without the Q15 screen it runs without.
  - Explicit thresholds refine by transform.
- The gate model's draw count is a function of fd and D1's tolerance only: 2 (round(j / fd) - 1)
  detections, j = 47 at fd 1e-2 and 48 at 1e-3, simulated until reached at any snr.
  - At fd 1e-3 that is a median of 167,000 draws (200,000 before), at 1e-2 16,500
    (20,000).
  - 200/fd with its 20,000 floor, the 3,000,000 cap, `_GROW` and the K < 8 refusals are
    gone.
  - A budget below fd 5.5e-5 now refuses. Before, such budgets ran on 8-96 dismissed
    draws.
  - `choose_chain` and `chain_thresholds` take `nsamp` as detections.
  - `tools/fdr_audit.py` tests each case against its plan's modelled dismissal
    (two-sided, against independent model draws) and reports the pooled misses over the
    budget.
  - `tools/split_bias.py` has no z and counts the direct refine's misses (`--cost`,
    `--taps`).

### Removed

- `MF_GPU_FUSE_INTERLEAVE` (the fused interleave depth is gone).
- `gatechain.direct_halfwidth`: a plan carries its direct refine's half-width
  (`chain_thresholds(...)["halfwidth"]`), chosen with its thresholds against one budget.
- 52 shipped GPU kernels that nothing could run or nothing chose, 14.7 MB of 115 MB: CUDA's
  tensor-core coarse gate (`src/gpu/coarse_tc.cu`, four PTX builds; the measured coarse
  choice never picked it on the L40S, where it ran 25-40% slower than the Slang layouts),
  the fp32 tiled coarse kernel (`coarse_tile.slang`, nine builds no host loaded), three
  SPIR-V modules no build makes (over 1024 invocations), and 36 PTX modules over the 48 KB
  of static shared memory CUDA allows a block, which no NVIDIA GPU can launch (their
  lengths run the 32 KB staging builds, as they did). Results are unchanged. One choice
  changes on CUDA: the band-8192 coarse candidates no longer include `tierb_8192_c16p2`
  and `tierb_8192_c16p2w`. Those 64 KB modules could not load and had no 32 KB build, so
  timing the band-8192 coarse layouts raised `UnsupportedSize`; it now times the two
  layouts that load. Devices with tensor cores also lose the two `tc` coarse candidates
  at bands 256 and 512 (the deleted gate).
- `MF_ILAY` and the strided ([n1][k2]) intermediate layout of the CPU transform that
  `MF_ILAY=0` selected. Paired rounds on Zen 5 (2026-10-27) covered the AVX3, AVX2, AVX
  and SSE4 kernels, n = 256 to 2^20, and the peak (one bin, many bins, unthresholded),
  full-output and continuous correlation calls. The strided layout was 5-7% slower than
  the contiguous one at the median on every ISA and up to 1.36x slower (2^20). It was never
  faster by the 5% a measured choice needs: its best case was 4.8% (n = 4096, SSE4), which a
  16-round re-measure put at 1.00. Outputs were bit-identical. On the CPU ladder (test27
  bank, AVX3) it was 0.5-6.4% slower per round. Zen 3 had it slower at every length
  (2026-10-22). An Apple M2 measured it 4-9% faster at n >= 2^18 (2026-10-22), which was not
  re-measured. Without it, results are bit-identical on every ISA.
  Removing the branch changed GCC's inlining: stage A's untabled 32-point path, which no
  plan with its twiddle table takes, was inlined into the tabled one (12.2 -> 15.2 KB on
  AVX2, 13.5 -> 16.9 KB on AVX) and the AVX n = 1024 one-bin call ran 1.14x slower. That
  path is now its own out-of-line function, and the hot one is 7.8 and 8.5 KB. Paired on
  Zen 5, the AVX and AVX2 calls at n = 1024 are 1.03-1.04x the old build's and level
  elsewhere (n = 512, 4096), and AVX3 is unchanged: the remainder is code placement, as the
  fine stage's frontend bound makes it (the old ladder ratios were measured before this fix).
- `MF_METAL_IEEE` (no tool, test or CI job set it, and `=none` let the survivor compaction
  drop a NaN coarse value), `MF_TC_KAPPA` (a hand-set tensor-core bound constant in place
  of the one built from the measured sigma) and `MF_CAPTURE` (nothing read it). Setting
  any of them, or `MF_GATE_CACHE_FILE`, now warns that it was removed and why.
- The package root's re-exports of private names (33, from `_filter`, `_hierarchical`,
  `_choice` and `_results`, and the `_gatechain` alias) and `time_domain`'s re-exports from
  `_layout` and `_windows`. Private names are reached in their own modules and may move
  (docs/robustness-plan.md, decision 5); the public names are unchanged
  (tests/test_public_api.py).

### Performance

- Setup of a hierarchical search: test27's 614 leaf banks over 27 references in one process,
  matchedfilter's share (beyond the banks' steady calls): dev2 22.9-29.9 -> 7.5 s,
  Haswell 209 -> 63-94 s, Ivy Bridge 239-426 -> 157-170 s. The reference's signature is
  memoised by memory (a full-resolution reference was hashed per bank); the calibration's
  threshold searches count passes on 32 blocks and its calls are 128 blocks; the simulations
  draw 7-39x faster (above), run in single precision, reduce each transformed block in one
  pass (_core.row_peaks), and the plan search, gate features and kept draws are memoised or
  linear where they were quadratic.
- Setup of a hierarchical search, again: a test67 BBH full-data job (323 banks over 19
  references; setup is per job, the same for 3x the data), matchedfilter's setup CPU against
  the release candidate above, interleaved on one node: Haswell 276 -> 185 s, Ivy Bridge
  401 -> 307 s, dev2 45.5 -> 16.7 s. The noise simulation keeps each block's running-maximum
  records, so every template group's search window reads its block maxima from one
  simulation per reference and block size, where each window simulated anew; it runs in one
  C pass (_core.noise_records: draws, the library's transforms, records; within 2.6e-7 of
  NumPy's). The plan search leaves out noise blocks below the lowest first-tier threshold it
  tries (2.8x, candidates identical); the signal simulation evaluates each band on its own
  lags (identical). The cost calibration shares band costs between sizes on one series group,
  reuses its plans and runs 32-block calls: a job's calibration (2048 and 4096) takes 0.8 s on
  Haswell and 1.5-2.5 s on Ivy Bridge, from 6.6-6.9 and 11-12 s (main: 26 and 45-59 s).
  Decisions under one cost file are identical to before on test27 and test67.
- Setup of a hierarchical search, a third pass (test67 BBH job, matchedfilter's setup CPU,
  interleaved with the previous main on one node, two sessions each): Ivy Bridge 309 -> 199 s
  and 246 -> 115 s, Haswell 254 -> 167 s and 176 -> 103 s; dev2 13.4-16.1 -> 8.9-10.6 s.
  Block-size ranking runs a provisional model with a quarter of the noise blocks (the signal
  draws, on which the budget rests, keep their count), and a full model of the same profile
  extends that simulation rather than redoing it. The simulations' generator draws from
  xoshiro128++ within blocks seeded by Threefry (SSE4 4.5 -> 1.9 ns a draw; the stream
  changes: test27 keeps every decision under one cost file, thresholds within 1.2%; test67
  moves one reference's near-tie chain). The signal simulation reads the stream's cached
  prefix for every reference, the plan search runs in C (identical candidates), and the cost
  model's interpolation tables are kept as arrays.
- The gate model's simulation, which places every chain's thresholds, runs about 2.5x
  faster with bit-identical records and draws. On dev2 (one core, load ~60, medians of 5
  interleaved runs), for the inspiral reference at n = 2048 and fd 1e-3: choose_chain 4.91 ->
  1.98 s, the signal simulation (200k draws) 4.81 -> 1.90 s and 38.9 -> 14.6 G
  instructions. That follows a first 14.5% (signal simulation at n = 2048 and 4096, 6.67 ->
  5.70 s, idle core): the keep check's and the records skip's maxima, of non-negative
  squares, are taken as integer maxima of their bit patterns, which order alike and
  vectorise. The noise records were sized for white noise's count of running-maximum
  records, and the inspiral profile's smooth statistics have two to three times as many,
  so the simulation overflowed and ran again with twice the room: two full simulations at
  n = 2048, three at 4096. It now keeps the rows that fit and continues from the first that
  did not. The records scan runs in Highway, a block of 16 values with one comparison
  (src/records.cc). On AVX-512 the Gaussian fill draws two blocks in one 16-lane vector
  (0.68 -> 0.36 ns a draw), rows are filled together with their scale, and the transforms
  read the draws in place. The first step is exact by construction (and matched on 25M
  records); the later ones match its build bit for bit under AVX-512, AVX2, AVX and SSE4
  (499 arrays each).

- The AVX back end (Sandy and Ivy Bridge) has its own block and spectrum loads (scale_load,
  split_store, now in src/loads-inl.h). It had inherited SSE4's, and split_store's vector path
  needs the plan's lane width, 8 for AVX, so it ran its scalar loop there. Identical results.
- At 16 lanes (AVX-512), the fused peak scan at n=1024 runs one instance for blocks with one
  bin and with two, instead of one of each. Each carries the 32-point transform with its
  inlined scan (27 KB), and alternating the two block by block thrashed the instruction cache
  of a stage that is frontend-bound: on Zen 5 26% of dispatch slots got no instructions.
  Cascade Lake and Zen 5 -1..-3% at n=1024 (two sessions each; code layout alone moves this
  stage by up to 8% on Zen 5). 8-lane paths are unchanged; results identical.
- Flat CPU banks above 1024 Hz may take 1024-sample blocks when a 2048 block's working set
  (data and template spectra and the intermediate, 48 KB) fills the L1D. The valid-fraction
  rule then picks 1024 wherever it keeps half of each block valid. Since 2026-10-05 the
  candidates had started at 2048, a leftover of a removed decimation scheme. pycbc's test27
  fine banks (257-297 taps): Haswell -10%, Zen 3 -11%, Ivy Bridge -15%, Zen 5 -9%. An M2
  (128 KB L1D) keeps 2048, where 1024 was 2.6% slower. GPU banks and the hierarchical
  engine (which prices its own block sizes) are unchanged.
- Stage A loads its twiddles from a full table when the table (8N bytes) fits the L1D,
  instead of forming each from two smaller tables (four multiplies and two broadcasts an
  element). Results are bit-identical. Fine-stage call at n = 2048 and 4096: -1 to -5% on Zen 5,
  -3 to -5% on Haswell, -2 to -9% on Ivy Bridge. Past the L1D the table lost (Ivy Bridge
  +18% at 16384, +55% at 65536), so larger transforms keep the factored form.
- Stage B transforms a column of the intermediate where stage A left it, when the column
  is one codelet, instead of copying it to a staging buffer first. The flat engine's
  block loads (series, real series, the DIF loads) take the backend's full-width
  scale_load too. Results are bit-identical.
- The copy of each block's spectrum into the plan's layout (set_data, set_template) and the
  hierarchical engine's scale-and-load of each block's samples run at the machine's vector
  width (backend kernels split_store and scale_load). They were loops in matchfilt.c and
  hmf.c, which are compiled for the SSE4.2 baseline: the copy was scalar, the load 4 lanes.
  Results are bit-identical. pycbc test27 hierarchical: the copy's cycles fall 70% and the
  library's 4.7%.
- AVX-512 transforms transpose their 16x16 corner turn in registers (in-lane unpacks, then
  two rounds of 128-bit block shuffles) instead of the generic four-stage network, which the
  compiler kept as rolled loops through memory: 35 cycles for the pair of 16x16
  transposes against 195 on Zen 5. Results are bit-identical. pycbc's test27 flat fine stage
  takes 22% less time (7.7 to 6.0 s on dev2) and the whole job about 5% less.
- The gate model finds a result it reused for a similar profile again by that profile's own
  signature. Before, every lookup of a segment's reference took the similarity search
  (~1 ms, against ~0.03 ms), and a hierarchical filter looks its plan and chain choice up
  several times per reference. On the O2 production replica (one core, dev2) the run takes
  5% less wall time (73.9 s to 70.2 s); its thresholds and triggers are unchanged.
- The gate model's decision setup in a fresh process at fd 1e-3 takes 0.69-0.73x the
  time. On dev2 at load 6-8, `choose_chain` takes 1.15 -> 0.79 s at n = 2048 and
  2.14 -> 1.49 s at 4096, and a CPU FIR plan's whole decision 1.17 -> 0.83 s and
  2.18 -> 1.59 s. dev1 is 0.69-0.71x. The work removed:
  - fewer draws;
  - the noise alone recorded only for the model's 20,000 noise blocks;
  - one split grid (`_SPLIT`, 9 shares; 19 gave the same plans' costs to 0.05%);
  - no per-band single-tier plans to price the direct refine.

### Fixed

- `gatechain.calibrate_costs` was a wrapper that measured 256-block calls, where plans, tools
  and tests (through `_calibration.calibrate_costs`) measured 32, and cost models were cached
  and stored under n, template count and series group alone: whichever calibration ran first
  in a process, or first into an MF_COST_FILE, set the model every later one returned. The
  public name is now the calibration itself, with its defaults, and a model measured with
  other calls (blocks, rounds, seed, and on a GPU templates) is kept under its own key. Models
  of the default calls keep the key they are stored under.
- The GPU cost calibration priced the same work 0.25-4x differently from one process to the
  next on a Radeon 8060S, enough to rank the n=2048 gate chains (256, 1024) and (256, 512)
  either way round (0.67-1.45x where the first runs 1.06-1.08x the second): 5 production
  ladder processes of 22 picked (256, 1024) or the one-tier (256,). It copied its series
  from the host before every timed call, which left the GPU idle long enough to slow the
  call by a varying amount; took the median of five calls in a row, which slow spells and,
  under CPU load, a power-limited GPU moved; and scaled each call by a reference timed just
  before it, whose clock under load was not the call's. Now, as the CPU calibration already
  does, each configuration's time is its fastest, of 15 rounds of 3 calls taken in turn; the
  series is resident in device memory, as the fine stage's is; and the reference scales the
  calibration as a whole. In 31 of 32 ladder processes since, the model ranked (256, 1024)
  at 1.04-1.10x (256, 512). Calibration at n=2048 takes about 5-8 s (15-26 s under CPU
  load); models stored by the old method are measured again.
- The GPU cost calibration scales every price of a process to a reference call's time on a
  warmed device (the anchor), but under CPU load it timed the anchor on a device still at
  its idle clock. The 0.25 s warm-up was timed from before the reference's first call, which
  records its commands: 0.06 s on an idle Radeon 8060S, 0.4-0.5 s with eight other processes
  on its four cores. In each of 178 processes with 6-12 others on their cores the warm-up had
  run out before it began, and in 17 the anchor read 0.105-0.134 ms against 0.028-0.031,
  which scaled every price of their models 2.8-4.3x, so models at different n no longer
  compared. The warm-up now starts after the first call (the calibration's own warm-up
  too), and the anchor is the warmed device's fastest call: 137-308 warm calls before it in
  42 loaded processes, none cold. Calibration time is unchanged when idle (8.0 s at
  n=2048) and up to 0.6 s longer under that load (21-27 s). Models stored by the old method
  are measured again.
- MF_GPU_PROFILE=1 could lose the Vulkan device (VK_ERROR_DEVICE_LOST) on the first call of a
  profiled run: phase marks were read from queries no submitted run would write.
- The CPU cost calibration failed (KeyError 'recheck') for a size calibrated after a smaller
  one on the same series group, e.g. a bank pricing 1024-sample blocks before 2048: the
  sizes share band costs, and the screen's per-pass cost was timed only when the first
  screen band was still to measure. It is now timed at the first screen band measured.
- A survivor's direct-or-transform refine compared prices each plan timed for itself, so two
  plans of one layout (a padded call and its unpadded call) refined pairs near the boundary
  differently and reported them to different fp32 rounding. The prices are now timed once per
  size and kernel and kept in MF_COST_FILE.
- The macOS arm64 build: gauss.cc dispatched with a qualified name, which a single-target
  build (NEON only) cannot resolve.

### Documentation

- docs/architecture.md, a reference for the library as it is: the public API, the module
  layers, the C engine and the `_core` boundary, the GPU host layer and backends, a
  hierarchical call end to end, the gate model, the cost models, measured choices and what
  MF_COST_FILE holds. docs/README.md classifies every document as reference or dated log.
  Reference pages that still described retired mechanisms (calibration files deciding the
  gates, chain trials, trial samples kept between processes) are corrected; dated logs are
  kept as written.

## 0.1.0a9

### Fixed

- Peak bins are the window's, on every engine, block size and device: a `binsize` (the
  call's or the bank's) numbers each analysis window's bins from the window's start,
  wherever the blocks fall. Before, each block numbered its bins from its own span, so a
  window of exactly 1000 bins of 61 samples (pycbc's asymmetric follow-up) came back as 1021
  peaks at block size 2048 and 1002 at 4096. The hierarchical bank picks its block size by
  a timed trial, so follow-up triggers changed from run to run and did not match the flat
  filter's. Every scan now takes a bin phase per block (CPU kernels, the Vulkan, CUDA and
  Metal shaders, the hierarchical refine), and a bin a block edge cuts comes back as two
  partial bins merged by largest |snr|, the earlier sample on a tie. Without a binsize a bin
  is still the block's span. `run_series` (flat and hierarchical) takes `bin_phase`; phase 0
  is the old behaviour, bit for bit. Flat CPU cost on pycbc's test27 job: follow-up level
  with 0.1.0a8, fine stage +1.5% (half its blocks scan and report two window bins).
- The CPU direct refine applies to a row whose window lies in one bin even when a bin phase
  pads the row with empty bins. Such rows used to take the whole-block transform, which
  differs by fp32 rounding (4e-7) and costs more.
- A coarse tier's window now reaches one coarse sample past the end of the caller's window,
  as it already did before the start, on the CPU (hmf.c), the GPUs (`_gpuhost.coarse_span`,
  `band_windows`) and in the gate model. Without it, a signal in a search window's last R lags
  had a coarse sample on one side only and kept as little as 0.47 of its SNR. With pycbc's
  per-block windows the production chain dismissed 1.40-1.44x its false-dismissal budget
  against the flat filter, and 0.75-0.85x with the fix. `tools/chain_fdr_vs_flat.py --window`
  measures it.
- The gate model no longer hands one profile another's plan. Its exact cache key was a 24-bin,
  1%-quantised signature, and its reuse took any profile within cosine 0.985. An A+ reference
  planned after an O4 one (cosine 0.995) took O4's thresholds and dismissed 2.3-4.6x its
  false-dismissal budget against the flat filter. The key is now the profile to float rounding.
  Reuse also requires every candidate band's signal response, sqrt(f_b) g_b, to agree within
  0.3% (`gatechain._similar_get`). A reference that changes between calls (per-segment PSDs)
  is planned anew more often: about 1-3 s each, then cached.

### Changed

- The CPU Q15 screen is now the first tier's gate: a pair passes when its int16 maximum
  reaches the tier's threshold, with no margin and no float run of the tier behind it
  ([reduced-precision-gates.md](docs/reduced-precision-gates.md)). The chain stays within
  its false-dismissal budget against the flat filter (measured by injection), and on the
  production replica tier 1 sees 25% fewer pairs. Results with the screen on are no longer
  bit-identical to the float first tier's; reported peaks are still exact. The late
  recheck order (`set_q15_recheck_late`, `gatechain.q15_recheck_order`) and the FP16
  tier 0 behind the screen (`set_q15_tier0`, `price_q15_tier0`) are removed: there is no
  recheck left to order or price.
- The tiers between the first and the last also gate on the Q15 screen, over their survivor
  lists (`ap_mf_q15_pairs`): each lane's data and template are looked up in prepacked vectors
  inside the transform, with no gather pass. On the production replica tier 1 costs 32% less
  and the gated stages 8.8% less. The last tier stays FP32 for the direct refine's lag.

- Every `MF_*` environment variable follows one rule (`docs/environment.md`, generated
  from `matchedfilter/_config.py`): unset or empty gives the default; a switch takes
  0/false/no/off or 1/true/yes/on (any case); a number must parse; anything else raises
  `ValueError` naming the variable when the package is imported. Before, each reader had
  its own rule, and some values meant the opposite of what they say:
  - `MF_HMF_PROF`, `MF_CORR_NO_STREAM`, `MF_GATE16_DEBUG` and `MF_GATE16_DEBUG_MAX` were
    on whenever set, `=0` included;
  - `MF_GATE16=abc` turned the FP16 gate off, and `MF_GMAJOR=2` or `MF_ILAY=2` counted as
    on;
  - `MF_AUTOTUNE_LOG=` (empty), `MF_GPU_TIMING=false` and `MF_GPU_PROFILE=no` counted as
    on, and `MF_DIRECT_REFINE`, `MF_GPU_ITEMS`, `MF_DEVICE_FOLLOWUPS` and
    `MF_VK_C16_BOUND` were off only for exactly `0`;
  - a C integer that did not parse (`MF_PBMAX=big`) read as 0.
- An `MF_*` name the package does not know warns at import, with the nearest known name;
  a removed one warns with when and why it was removed.

### Removed

- C entry points nothing called: `ap_binmax_prod`, `ap_interp_max`, `ap_series_buf`,
  `ap_series_stride`, `ap_mf_run_sel`, `ap_nbins`, `ap_root_merge`, `ap_real_split`,
  `ap_mf_ndata`, `ap_hmf_get_real_series`, `ap_hmf_get_hermitian` and
  `ap_hmf_price_q15_tier0`, with the backend series store and interpolated maximum only
  they reached.
- The per-backend coarse layout fields `MF_VK_COARSE_PPG`, `MF_VK_COARSE_TILE`,
  `MF_VK_COARSE_SUBGROUP`, `MF_VK_COARSE_TWT` and `MF_METAL_COARSE_PPG` (and the
  documented `MF_METAL_COARSE_TILE`/`_TWT`, which nothing read): `MF_COARSE_LAYOUT`
  forces a whole layout by name on every backend.
- `MF_VK_C16_BOUND` is renamed `MF_COARSE_RAW`: `MF_COARSE_RAW=1` is what
  `MF_VK_C16_BOUND=0` did, on every GPU backend.
- `tools/metal_c16_sigma.py` is `tools/c16_sigma.py --backend metal|vulkan|cuda`.
- `MF_BBLK` (stage-B blocking of the balanced transform): slower than the default at
  every length measured on Zen 3, Zen 5 and an Apple M2 (1-7%).
- `MF_TRIAL_RECHECK` and the steady-state re-check it switched on (`Choice.observe`,
  `gatechain.recheck_enabled`, `observe_steady`, `steady_disagrees`, `RECHECK_*`): off by
  default, it let one process's steady timing reopen a lock for every later process, so
  processes sharing a cost file could make different choices. A stored lock is final.
- Python 3.10 support: matchedfilter needs Python 3.11 or newer, and numpy 1.23.2 or
  newer (the first numpy with Python 3.11 wheels). Release wheels cover CPython
  3.11-3.14.

- `time_domain.SegmentPlan` (segment replay: Vulkan recorded submissions and CUDA segment
  graphs) and the CUDA device follow-up selection it drove (`src/gpu/followup.cu`). Nothing
  outside the library's own benchmark used it. `filter_series_many` is unchanged, including
  Vulkan's device follow-ups. `MF_SEGMENT_REPLAY`, `MF_CUDA_SEGMENT_GRAPH` and the ladder's
  `LADDER_REPLAY`, `LADDER_FOLD_TOPS` and `LADDER_INFLIGHT` modes are gone. The gate's
  replay step became `settled`: the same check after the trials have locked.
- `filter_series_many(followups=)`, `_gpuhost.FollowupSpec` and its alias
  `time_domain.FollowUp`: the follow-up selection rule that `SegmentPlan` ran on the device.
  Nothing else called them; a search selects its own follow-ups and passes them to
  `filter_series_many` as single-template calls, which run on the device as before.
  `MF_VK_DEVICE_FOLLOWUPS` is now `MF_DEVICE_FOLLOWUPS` (Vulkan and CUDA).

### Performance

- CUDA runs follow-ups (`filter_series_many` with threshold-0 single-template calls) on the
  device: one table upload, per template group a forward and one
  `refineItems` launch, and one readback, as Vulkan does. The batch layout and result
  assembly are shared (`_gpuhost.followup_layout`, `assemble_followups`); each backend keeps
  only its executor. L40S, test27 ladder, paired on settled seeds: pipelined 1.25x, batched
  1.03x; the follow-up stage fell from 0.05-0.06 s to 0.03 s per segment. Results equal the
  host path exactly. Metal keeps the host path: follow-ups are about 6% of its segment.
- Metal fp16 coarse builds carry the fp16 twiddle table, and the tile choice measures each
  tile with each twiddle source. On an Apple M2 the table was 5-6% faster in the untiled
  builds (its bands 128 and 1024) but slower in the tile-4 and tile-8 builds.
- Vulkan and CUDA tiled fp16 coarse builds report each pair's gate decision and bound
  without electing a lag (`peakTwoGate`, Metal's since its tier-0 study): nothing reads
  tier 0's index. Radeon 8060S, band 256, interleaved: 0.91x the time per pair at the
  tiled layouts. The tensor-core gate and untiled builds are unchanged.
- CPU Q15 and block-size trials compare identical workloads in interleaved rounds,
  persist complete rounds across processes, and bound ambiguous contests. The dev1
  ten-start study selected Q15 on 10/10 times; every second process had unchanged
  trial locks and zero CPU trial work after the steady boundary. Calibration is
  more expensive upfront. Forced-lock controls put median paired throughput about
  0.2% below baseline; Q15 on was 25.0% faster than off on this workload.
  Ladder reports now flag tuning in nominal steady windows,
  and `tools/cpu_trial_check.py` separates calibration from accepted measurements.
  See [trial policy and limitations](docs/gate-model.md#cpu-paired-trials-and-bounded-measurement-2026-10-15).
- CPU Q15 screening can defer its float256 recheck until after float512 when
  the scheduling model favors that order on AVX3 N2048 chains. The same gates
  and thresholds remain; the representative Zen 5 ladder uses 3.5% less fine-stage
  time and 2.9% less whole-segment time with identical outputs. Gate work counters
  now record actual inputs, including reordered execution. See
  [gate execution order](docs/cpu-gate-order.md).
- AVX-512 N256 Q15 screens fill partial template batches with independent data
  blocks. A longer paired Zen 5 ladder comparison reduced Q15 time 4.3%, fine-stage
  time 2.1%, and whole-segment time 1.8%, with identical outputs. Small data groups,
  complete template batches, and other CPU targets retain the existing kernel.
  See [Q15 tail packing](docs/cpu-q15-tail-packing.md) for controls and limits.
- CPU hierarchical series calls prepare later-tier data only for blocks with incoming
  survivors. In a paired Zen 5 ladder comparison, fine-stage time fell 3.7% and total
  segment time 3.1%, with identical outputs. A steady segment avoided 41.8% of band-512
  copies and 88.1% of band-1024 copies. Public spectral setters retain their eager copies.
  See [work avoidance and further experiments](docs/cpu-work-avoidance.md).
- CPU survivor processing reuses shared data and packed templates, fuses the N256
  Q15 window maximum when the cache/register policy permits, and skips rejected
  pairs in the subsequent float decision loop. On a pinned Zen 5 core, alternating
  representative ladder runs improved fine throughput 1.033x and whole-segment
  throughput 1.024x with identical outputs. Gains varied across shorter runs on the
  shared host. The Q15 margin and gate thresholds are unchanged. See
  [measurements and reproduction](docs/cpu-survivor-performance.md).
- Sparse analysis-window planning bounds block candidates to each window instead of
  constructing the remaining series for every window. In a local paired benchmark with
  512 narrow windows over 2^26 samples, planning was 3.3x faster with identical layouts;
  whole-series planning was unchanged within measurement noise.
- fp16 coarse tier, untiled builds (every band on an Intel Iris Xe; bands 128 and 1024 on an
  Apple M2): the peak election is one pass over the transform registers -- each thread keeps
  its in-window maximum, that maximum's lowest slot and the register -- instead of holding
  per-register magnitude arrays. A second pass that recomputed the magnitudes was folded back
  into the first by Intel's compiler and spilled just as the arrays did (46 spills, 148 fills
  at SIMD16). Band 256 on the Iris Xe, interleaved against 0.1.0a8 on the same device: at
  subgroup 8, 0.87x the time per pair; at subgroup 16 the spills are gone (2574 -> 1303
  instructions), and its best layout takes 0.71x the time of 0.1.0a8's best (subgroup 8),
  1.41x coarse throughput. The layout measurement now picks subgroup 16 at every coarse band
  there. Same results.
- Vulkan fp16 coarse tier, untiled builds with several pairs per workgroup: any pair count
  keeps the chosen packing (ragged last group; its spare slots compute and write nothing).
  The largest packing that divided the pair count ran every odd count -- 10 of 27 fine
  groups of a test27 segment -- at one pair per workgroup: 1.95x the time per pair on a
  Radeon 8060S (half-empty wave32s), 1.7x at subgroup 16 on an Iris Xe.
- Vulkan coarse tiers with per-row windows (every fine-stage call): the windows are mapped
  onto each coarse band on the host, once per storage set, instead of in the kernel. The
  in-kernel mapping made the band-256 kernel 1.47x slower at subgroup 16 on an Iris Xe (no
  effect at 8), so production never saw the subgroup-16 gain above.

- fp16 coarse tier, untiled builds: the inter-level twiddles come from the build's fp16
  table or from the fp32 recurrence, a measured per-device choice (Vulkan specialization
  constant 80, a fourth field of the coarse layout; CUDA's table "w" builds). The
  recurrence was 13-18% of the band-256 kernel on both a Radeon 8060S and an Iris Xe;
  the table was 7-9% faster on the 8060S and 8.7x slower on the Iris Xe, whose table loads
  are 64-bit global reads. The 8060S now takes the table (band 2048: 38.3 against 41.2 ns
  per pair); the Iris Xe keeps the recurrence. Metal keeps the recurrence.

### Changed

- `clear_autotune_cache()` forgets every workload choice the process made, as its
  docstring now lists: also block-size trials, the single-device, single-batch and
  fused-batch device choices and the model's Q15 shortlist. Machine state (cost models,
  correlation prices, a GPU's kernel choices) is kept.
- Every measured choice (chain, block-size and Q15 trials, the device and fusion choices,
  kernel layouts, subgroup size, interleave, sparse readback) follows one lifecycle,
  `_choice.Choice`, and ends by construction: an unclear contest samples up to a cap, and a
  trial whose samples do not come ends at its budget of attempts, the model's choice standing
  without a clear win. Open trials persist across processes, CPU chain trials included.
- Trial locks are kept in MF_COST_FILE as `choice|<key>` records. Older `block-trial|`,
  `chain-trial|` and `q15-trial|` records are not read: a machine runs those trials once more,
  or `python tools/migrate_cost_file.py costs.json` rewrites the locks.
- One coarse launch rule on every GPU backend (`_coarse.coarse_launch`): untiled builds with
  several pairs per group take ragged groups on CUDA and Metal too (the kernel's spare slots
  compute and write nothing), so neither host pads its data rows or outputs any more.

### Fixed

- CPU cost models are stored under the series group the plans run (after `MF_DGROUP` and
  the 4 MB cap at long transforms), not the one requested: a model calibrated under
  `MF_DGROUP` was stored under the default group's key and adopted at the default.
  Calibrations at n >= 65536, where the cap applies, are re-measured once.
- `MF_DEVICE` no longer moves the library's own CPU plans (a GPU group's CPU plan for
  single-template calls, the correlation price probe) to another device: a
  single-device lock stored under `MF_DEVICE=gpu...` timed a GPU against a GPU; such
  seeds should drop their `single-device` records.
- One filter object per thread: a call on an object while another thread's call on it is
  running raises `RuntimeError` ("use one filter per thread"); it used to corrupt the
  plan's buffers silently. Lazily allocated scratch (series spectra, the DIF forwards,
  the platform-FFT buffers) is allocated all-or-nothing: one failed allocation used to
  leave a half-set state that the next call took as ready and dereferenced.
- C entry points check caller ranges and sizes without overflow: a subrange near the
  int maximum, a tap stride or an output size whose product wrapped used to pass the check
  and read or write out of bounds. A NaN threshold raises `ValueError`; a filter object
  cannot be initialised twice; `_core.forward_cost` refuses a size the engine does not
  support (it returned 1e30 s) and reports a failed allocation as MemoryError.
- `HierarchicalFilter.set_data` (and C `ap_hmf_set_data`) copies the data, as the flat
  filter does: the refine ingests the full spectrum lazily, so a caller that reused its
  buffer after `set_data` changed what the refine read (a loud peak read as none). The
  Python layer also keeps a copy, not the caller's array, for replay into a rebuilt plan.
  Costs 8n bytes per data row and one copy per call.
- Shipped Metal sources no longer name the build machine's paths in `#line` directives,
  and a stray sync-conflict copy is gone. The Metal kernel identity changes once, so
  stored Metal choices are re-measured once.
- `MF_ISA` restricts the process to its target. An invalid value raises `ValueError` at
  import, naming the build's targets; it used to print an error and segfault at the next
  kernel call. `targets()` lists only that target from the start, `set_target(None)`
  restores it (it used to switch back to the widest target), and selecting another target
  raises. A failed `set_target` changes nothing (it used to leave the default selected).
- A plan keeps its kernel for every call: the sub-plans it builds lazily (the real-series
  half transform, the DIF forwards, the pair-batch alternate, the direct refine's
  correlation, the root merge) use the plan's own target, not the one selected when they
  are built.
- MF_COST_FILE never loses data. A damaged file (truncated, not JSON, not a JSON object)
  read as empty and the next write replaced it, losing every stored model and choice: it
  is now kept aside as `<path>.corrupt.<pid>` with a warning. A file that exists but cannot
  be read is never replaced. Cost models and one-shot prices are stored first-writer-wins:
  processes calibrating or pricing at once adopt the first stored result, so they choose
  the same chains and thresholds. A stored record that is not a cost model is reported and
  recalibrated; trial records in the format before 2026-10-21 are reported once, naming
  `tools/migrate_cost_file.py`, which now writes under the library's lock, atomically.
- A GPU chain trial spread over processes too short to take a sample never ended (macOS
  Metal CI): its batch count is kept every batch, and the spent budget keeps the model's
  chain.
- Vulkan and Metal async results own their output buffers until collected. A later call
  of the same shape reused the record and overwrote them, so the earlier result returned
  the later call's peaks; a call now collects the in-flight result first, as CUDA does.
- Segment replay covers ragged layouts. When a call's blocks have several bin counts, its
  result is split per count; the parts now carry the call's trace, and a replay splits the
  replayed result the same way. Before, such segments never replayed: at n=4096 on test27
  (the GPU block size a trial can lock on a Radeon 8060S) the gate's replay check found
  none. With the fix, 7 replays of 10 segments, exact against the CPU.
- Existing Q15 plans retain their SIMD backend after `set_target()`, including lazy
  scratch allocation. Switching to a wider target previously allowed its kernel to
  overwrite buffers sized for the original plan.
- Half-spectrum DIF refinement respects full-rate bin boundaries for odd bin widths
  and clipped windows, returns the correct flat-series output shape, and breaks exact
  peak ties at the earliest lag. Changing Hermitian mode re-ingests existing templates
  with the new normalization and layout.
- Reference caches include the data sample rate and observe in-place reference, template
  and PSD edits when their setter is called again. Weak references and bounded storage
  release retired inputs instead of retaining every PSD from a long search.
- CUDA asynchronous results, including submitted segment graphs, are materialized before
  their cached output buffers are reused or freed. Early collection preserves each
  dispatch's statistics; captured segment replays keep fresh result readers.
- Concurrent `MF_COST_FILE` writers lock the read/merge/replace operation, preserving
  unrelated records written by other processes or threads.
- Coarse layout measurement (Vulkan, CUDA, Metal) times its candidates in interleaved rounds
  and confirms the contenders against the fastest, paired, instead of timing each
  candidate's repetitions back to back. On a shared GPU one burst of other work during the
  untiled stage stored a tiled layout 4.3x slower on an Iris Xe, and MF_COST_FILE kept it.
- Measured GPU kernel choices in `MF_COST_FILE` (coarse layout, tile and subgroup on Vulkan,
  CUDA and Metal; the Vulkan pipeline subgroup and fused-batch interleave) are keyed by the
  compiled artifacts they timed (`gatechain.gpu_kernel_id`), separately for each backend,
  including CUDA-only kernels and compiled Metal libraries. Builders stamp these digests
  into the manifests so startup reads a small identity rather than scanning the kernels.
  A cost file written by another build was reused, so a kernel change that moves the best
  layout -- the Iris Xe's coarse subgroup above -- never reached a machine that already
  had one.

### Documentation

- Clarify that CPU direct refinement searches near the coarse maximum and can miss a
  stronger excursion elsewhere in its bin; `MF_DIRECT_REFINE=0` uses full-bin transform
  refinement for surviving pairs.

## 0.1.0a8

The `v0.1.0a7` tag was not published to PyPI: its macOS arm64 wheel job failed
`test_reproducible_choices[gpu:0]` (a block-size lock reopened with the re-check off; fixed
below), so the publish job did not run. This release includes the 0.1.0a7 changes.

### Performance

- Real-real-complex hierarchies (`pycbc_fir_bank --complex-taps`): `TimeDomainFilterBank`
  takes complex (quadrature) final taps -- the analytic version of each real filter -- and
  filters a REAL middle series with them, same correlation convention as real taps. A CPU
  hierarchical plan reads a real series itself, as a contiguous array or in place as one
  lane (real or imaginary part) of a complex array -- a packed pair of real middle series
  -- and transforms each block at half size into its exact full spectrum (SIMD split).
  test27 full-data job (pycbc_inspiral_fir, 100k BNS bank, complex against the same
  generator's all-real bank, paired): middle stage -40% (two real middle filters as one
  complex one, in pycbc), fine stage -4 to -13% (load noise), total -6 to -10%; injection
  SNRs agree to a median ratio 1.0000 +- 0.007 (5-95%) and the same injections are found.
- CPU direct refine (docs/cpu-direct-refine.md): with one bin per pair, a survivor is
  refined by direct correlation with its real FIR taps at the lags around its last coarse
  tier's maximum -- a window the gate model sets per chain -- instead of a whole-block
  transform. `TimeDomainFilterBank` hands its taps to hierarchical plans at a rate ratio of
  1 (`HierarchicalFilter.set_taps`); the chain choice prices it. Captured
  `pycbc_inspiral_fir` calls: identical peaks, 13.7% less wall on a Zen 5 core, mostly from
  the cheaper chains it unlocks. `MF_DIRECT_REFINE=0` turns it off.
- GPU coarse layout as a measured per-device choice: tile (templates per thread) on Vulkan,
  Metal and CUDA from every shipped build, and on Vulkan the subgroup size and pairs per
  workgroup too, timed once per device and band and kept in `MF_COST_FILE`. The fixed
  per-band tile table is gone. Radeon Vega iGPU (RENOIR, GCN; gravity-dev3): +15% throughput; Intel
  Iris Xe: the coarse kernel 10-17x faster at subgroup 8 than at its default 32; Apple M2:
  untiled wins at bands 128 and 1024.
- Vulkan subgroup size of the remaining pipelines (transforms, refine, follow-ups) as a
  measured per-device choice in `MF_COST_FILE`, each candidate run in a subprocess and
  checked against the default size's triggers. Intel Iris Xe: SIMD32 by default, the
  measured size (8) runs the ladder 4.4-4.7x faster, exact. Required sizes never exceed the device's
  `maxComputeWorkgroupSubgroups` for a pipeline's workgroup (8 on the Iris Xe lost the device
  for the 1024-invocation transforms).

### Fixed

- A block-size lock could still be reopened from one process's steady-state timing with the
  re-check off (its default since 0.1.0a7, as for chain and Q15 locks), so two processes
  sharing an `MF_COST_FILE` could end on different block sizes
  (`test_reproducible_choices[gpu:0]`, 1 of 5 gate runs). The block-size re-check now
  runs only with `MF_TRIAL_RECHECK=1`.
- Vulkan fp16 coarse tier on GPUs that flush fp16 subnormals (Intel Iris Xe): templates or
  data far from unit scale were flushed to zero and every pair dismissed (`gate_margin
  --gate gpu-c16`: the transient family at every band, injections at 256-1024). The tier
  now places its operands by exact powers of two -- templates to a fixed range, data so the
  threshold sits where production banks already do (raised with the band, so the products
  a band-wide transform sums stay in fp16's normal range) -- as the CPU fp16 gate does.
  In-range results are unchanged.
- The tiled fp16 coarse kernel dismissed every pair of an overflowing (very loud) row when
  a pair spans more than one subgroup -- band 1024 on 32-wide subgroups (Intel, NVIDIA) --
  and its error bound overflowed to inf for ordinary pairs there. Every backend now uses
  the integer overflow test Metal had and the scaled energy of the single-subgroup path.

## 0.1.0a7

### Fixed before release

- Two processes sharing an `MF_COST_FILE` could end on different gate chains
  (`test_reproducible_choices[gpu:0]` failed 1 in 5 on the L40S; the macOS Metal
  CI wheel failed it too). Two causes. A stored chain lock was checked against
  the first plan's own feasible chains, and when that plan could not run it the
  process recorded "no lock" and re-trialled for every plan of the key; the lock
  now decides every plan that can run it, the others run their model's chain,
  and a locked key never opens a trial. And the steady-state re-check reopened a
  lock on one process's timing, so the next process could lock another choice;
  it is now opt-in (`MF_TRIAL_RECHECK=1`, see the usage guide), and a stored
  lock is final until the cost file is deleted.

- Re-measure the hardware comparison at `2b3cac13` on gravity-dev1,
  gravity-dev2 (CPU and Radeon 8060S), gravity-dev3 (CPU), Apple M2 (CPU and
  GPU), Haswell (CPU) and the NVIDIA L40S, at 16 × 512 and, new for the CPUs,
  512 × 512. See [teaser-fleet-20261013](docs/measurements/teaser-fleet-20261013.md).
  Entries not re-measured (A100 and A40 from 2026-10-04 at `2a33e8f`; the
  gravity-dev3 GPU, gravity-dev4, sugwg-login2 and the EPYC 9845 CPU from
  2026-10-03 at `50597f3`) are carried over and labelled with their date and
  revision. Haswell ran at load 35-37 and its rows are indicative only. The
  README teaser is redrawn from the gravity-dev2 512 × 512 reports with the
  new `tools/teaser_figure.py --from-fleet`, without re-measuring.

- Add the Haswell node (Xeon E5-2698 v3) to the hardware comparison. It had
  been in the PyCBC fleet benchmark from the start but never the hardware
  comparison, which is an odd gap for the oldest and most register-starved
  x86 target in the fleet. It exposes no GPU, and as a shared cluster node at
  load 41.8-44.2 of 64 cores only its FFTW (1.3%) and peak-only (2.5%) rows
  reproduce across three runs; full output (20.7%) and hierarchical (9-64%)
  are indicative only. Its SNR sweep is non-monotone where all six other
  hosts are monotone; the gate selects the identical band, taps and
  refinement fraction as gravity-dev1 at every threshold, so that is
  measurement noise on a contended host, not a selection fault.
- Re-measure both fleet benchmarks at `main` `eecb43c` (twenty-five
  optimization passes). PyCBC complete search against the previous head
  `ce9c828`: dev3 +7.4%, dev1 +2.3%, dev4/sugwg-login2/Haswell flat. The
  largest gain lands on the smallest, most cache-constrained host. Six-machine
  comparison at `eecb43c`: peak-only improves 2.6-5.9% on every uncontended
  CPU, full output is flat, hierarchical mode is mixed (M2 +9.6%, Xeon +8.9%,
  others flat), and the GPU is unchanged within about 1%. See
  [pycbc-main-eecb43c-fleet-20260928](docs/measurements/pycbc-main-eecb43c-fleet-20260928/README.md)
  and [teaser-fleet-20260928](docs/measurements/teaser-fleet-20260928.md).
  gravity-dev2 was under load 38 throughout and both its rows are labelled;
  the README teaser, which can only be measured on that host, is left at
  `ce9c828` rather than republished three times slow.

- Draw the teaser and fleet banks from the captured PyCBC reference profile
  (`tests/data/reference_profile_pycbc.npy`) instead of the synthetic
  inspiral curve. The synthetic curve is narrower than a real reference
  (`B_eff` 180.8 against 232.7 at band 512), and the hierarchy's cost follows
  from that width, so it flattered the gate. Hierarchical timings are slower
  and are not comparable to earlier pages.
- Record hierarchical rows at SNR thresholds 5.0, 5.5, 5.75, 6.0 and 6.5. The
  threshold spans a factor of 2.5-4 at `fd=1e-3` and can change the band the
  gate selects. On the hardware comparison page the threshold and the FDR
  budget share one Hierarchical screening box and both are multi-select, so a
  series is one (budget, threshold) pair and several can be compared at once.
- Recalculate both fleet measurements at `main` `ce9c828`. The six-machine
  hardware comparison moves to
  [teaser-fleet-20260927](docs/measurements/teaser-fleet-20260927.md); the
  September 26 page is kept for history. Fixed FFTW/rocFFT references
  reproduce within 0.8% on the four uncontended machines, and full-output and
  peak-only are flat within noise. A like-for-like run on the synthetic
  profile, before the reference change above, put the revision's gain in
  hierarchical mode at tight budgets (`fd=1e-4` CPU 15-38%); the published
  page now carries captured-profile numbers, which are slower in absolute
  terms and not comparable across the two profiles.
- Record the PyCBC complete-search fleet benchmark for `ce9c828` in
  [pycbc-main-ce9c828-fleet-20260927](docs/measurements/pycbc-main-ce9c828-fleet-20260927/README.md).
  Against the previously documented head `c38f24f`: Haswell +5.3%, dev4 +4.1%,
  dev3 +3.3%, dev2 +1.1%, sugwg-login2 -0.2%, dev1 -1.2%. The Haswell gain is
  the first measured on that host in this line of work. Correctness for this
  revision is not yet established; the numbers are timing only.

### Known issues

- On CUDA, two processes sharing a cost file can occasionally lock different
  gate chains (seen in 1 of 5 runs of `test_reproducible_choices[gpu:0]` on
  the L40S). Results are correct; only borderline peaks may differ between
  the processes. A fix is in progress.

## 0.1.0a6

- Optimize the Haswell hierarchical coarse path with specialized FFT32
  codelets, reduced intermediate traffic, and fused thresholded peak reduction.
  The measured complete search reaches about 349,000 template-seconds/s/core,
  roughly 1.56x the neighboring original baseline. These are workload-specific
  measurements; see [the evidence and controls](docs/haswell-series-grouping.md).
- Add a shared measured execution-policy table for CPU/GPU scheduling. The
  initial rule selects a smaller series group for the measured Haswell workload;
  uncovered devices retain their existing scheduling defaults.
- Bind balanced product kernels once per bank and avoid counting pair-batched
  peaks twice. Calibration tables and thresholds are unchanged.
- Fix blocked stage-B intermediate indexing and test reused plans, partial
  windows, signed zero, full output, peak counts, and CPU calibration transfer.
  The coarse FDR guard explicitly exercises AVX2 on wider CPU hosts.

## 0.1.0a3

The earlier `v0.1.0a2` tag was not published to PyPI; this release includes
those changes and the subsequent fixes below.

This alpha adds Vulkan and Metal GPU execution, full correlation output,
and consistent overlap-save interfaces alongside the existing CPU peak filters.

### Added

- `CorrelationFilter` returns every complex lag in natural order, with the
  spectral product fused into the inverse FFT. CPU and GPU support powers
  of two from 1,024 through 4,194,304. `run()` supports bank selectors and
  reusable output storage; `empty_shared()` provides GPU-accessible storage.
- GPU flat and hierarchical filtering through `device="gpu"`, using shipped
  Vulkan/SPIR-V or native Metal kernels. Peak transforms support powers of
  two from 64 through 65,536 on GPU, subject to device limits; CPU peaks
  support 64 through 1,048,576. Unsupported requests raise explicitly.
- Automatic overlap-save execution across all three classes. Construct a
  filter with `valid=(lo, hi)` and call `run_series(series)`; block spacing
  follows from the valid interval. Peak filters return block-major peaks
  with absolute series indices. Full correlation writes valid lags directly
  into a reusable, class-owned `(templates, series_length)` result on CPU
  and GPU, without an intermediate cube or a stitching copy.
- `run_blocks()` names explicit starts and per-block peak windows. The older
  explicit-start `run_series()` form remains supported with block-local
  indices. Series execution reuses data slots; call `set_data()` before a
  subsequent spectral `run()`.
- Host-compatible DLPack ingestion, device discovery, bank subranges,
  shared GPU output buffers, and explicit output-lifetime documentation.
- Benchmarks covering supported transform lengths and series workloads,
  FFTW/MKL references, opt-in performance regression tests, and a recorded
  six-machine comparison with selectable output modes, CPU/GPU models, and axis scales.

### Changed

- Hierarchical automatic configuration requires a covering measured
  calibration file. Otherwise callers must supply both a coarse `band`
  and `set_coarse_threshold(value)`. There is no model or default threshold
  fallback; manual thresholds carry no calibrated dismissal guarantee.
- Per-device cost tables choose coarse configurations. The requested
  `snr`/`fd` budget is a calibration condition, not a guarantee for an
  arbitrary template population.
- Full-output automatic allocation is capped at 512 MiB. Select smaller
  bank ranges or supply storage for larger spectral/block results.
- Python 3.9 support is dropped. Wheels target CPython 3.10–3.14 on Linux
  x86-64 and macOS arm64.

### Performance

- Shared batching and cache handling across `run()`, `run_series()`, and
  `run_blocks()`, coarse-template reuse, and grouped GPU submissions for
  irregular windows reduce repeated preparation and submission costs.
- Metal uses specialized single-bin flat/refinement kernels at 2,048–8,192
  points, grouped window submissions, and cached Objective-C wrappers.
- Full output retains fused products and batch reuse; peak-only output
  additionally avoids writing full correlations, while hierarchy can avoid
  most full transforms. Gains depend on hardware, batch shape, and survivor
  rate. See the [recorded comparison](docs/measurements/teaser-fleet-20260926.md)
  rather than treating one GPU/CPU ratio as universal.

### Fixed

- Intel Vulkan twiddle accuracy now meets the existing FP32 tolerance,
  using a device-specific specialization. Other GPUs retain native trig.
- Vulkan hierarchical dispatch synchronizes transfer-filled arguments and
  compacted survivor counts before indirect execution, including first use
  and reused plans switching between all and zero surviving pairs.

- Vulkan contexts now release device resources when filters are dropped;
  destruction is idempotent.
- Raw peak results consistently return `(index, value)` on CPU and GPU.
- Ragged explicit-block windows no longer write beyond the output stride.
  Output dimensions, selectors, buffer ownership, and reuse are validated.
- Coarse-template caching, pinned GPU configurations, reference/threshold
  changes, and data replacement correctly invalidate or reuse cached state.
- Automatic device selection includes Metal. Workgroup, staging-memory,
  and dispatch limits are checked rather than relying on pipeline failure.
- Portable hardware identification and benchmark formatting fix macOS and
  ARM CI failures.

### Known limitations

- This remains an alpha. GPU execution is synchronous; buffers returned from
  reusable storage must be copied if needed after the next call.
- Large full transforms need substantial scratch/output memory and are not
  equally optimized across devices. Device workgroup limits may rule out
  some GPU sizes even when the CPU supports them.
- Hierarchical selection costs are not optimal on every device. The M2
  and Iris Xe measurements identify further improvements for stricter
  dismissal budgets.
- GPU coarse screening may use reduced precision, with FP32 refinement.
  Statistical calibration must be checked against the caller's inputs.

## 0.1.0a1

First alpha: single-threaded batched matched filter with peak-only output,
a hierarchical two-stage variant, and Highway multi-target SIMD dispatch on
the CPU.
