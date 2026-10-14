# Changelog

Alpha releases may change the API. Pin a version for reproducible work.

## Unreleased

### Performance

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
