# Changelog

Alpha releases may change the API. Pin a version for reproducible work.

## 0.1.0a2 (unreleased)

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
