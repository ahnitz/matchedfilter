# Changelog

Alpha releases may change the API. Pin a version for reproducible work.

## Unreleased

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
