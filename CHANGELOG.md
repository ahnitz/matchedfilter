# Changelog

Alpha releases may change the API. Pin a version for reproducible work.

## Unreleased

### Removed

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
  refinement for surviving pairs. Document that time-domain bins restart at block/window
  intersections, so changing block sizes can change trigger grouping.

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
