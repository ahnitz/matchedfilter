# Full-correlation mode: implementation plan

The prototype establishes that emitting all lags is worthwhile. This plan is
for a production flat mode covering every power of two from 2^10 through
2^22 on CPU and GPU. It does not change the supported sizes, results, or
signatures of the existing peak-only flat and hierarchical modes.

## Public contract

Add `CorrelationFilter(n, ndata=1, ntemplates=1, device=None)`. It shares the
existing `set_data`, `set_templates`, `empty_shared`, device selection, bank
readiness checks, and memory-limit vocabulary. `run(data=None,
templates=None, out=None)` returns a C-contiguous complex64 array of shape
`(selected_data, selected_templates, n)` in natural lag order. The calculation
is the unnormalised inverse of `data * conj(template)`; sample zero and every
other lag match the current flat filter's reported complex values. Data and
template selectors use the existing `(start, count)` convention.

`run_series(series, starts, templates=None, out=None)` returns
`(blocks, selected_templates, n)`. It uses the same block starts, zero padding,
and forward-transform normalization as today's `MatchedFilter.run_series`,
and it consumes the plan's data slots under the same rule. There are no
`binsize`, `threshold`, or peak-search window arguments in this mode: they do
not describe a full inverse transform. A separate class keeps `run()`
consistent within each mode and avoids an output flag whose other arguments
become meaningless. Hierarchical filtering remains peak-only because a
screened-out pair has no full result to return.

`out` is optional, must be writable C-contiguous complex64 with the exact
result shape, and is returned by identity. On GPU, a result from
`empty_shared()` permits direct output without a host copy. A plain NumPy
`out` (including a memmap) is supported through bounded staging and an
explicit copy. Without `out`, allocate a fresh owned result when it is at
most 512 MiB; above that, raise before allocating and explain the required
size and how to select smaller data/template ranges or pass `out`. Returning
a fresh result avoids the prototype's lifetime and overwrite trap. The
512 MiB default is a guard against accidental multi-terabyte results, not
a limit on transforms or caller-provided storage. The guard and error text
need tests.

At n=2^22, one pair produces 32 MiB; 128×512 pairs would produce 2 TiB.
Supporting that length means a small bank or bounded sub-runs are possible,
not that every bank shape fits memory. Use the existing selectors to stream
rows/tiles into caller storage without changing their output order.

## Shared execution structure

Extract only the common, tested pieces from the present class: bank/selector
validation, readiness checks, device context and input residency, pair-tile
calculation, series block gather/forward, and result ownership. Keep the
peak reduction and full-output writer as separate final stages. On CPU, both
use the same staged spectral layout and stage-A fused product; the full mode
uses stage B followed by ordered complex stores. On GPU, both use the same
Tier-B transform body and input uploads; the full mode writes ordered lags
instead of scanning peaks. Avoid a broad rewrite of the tuned peak loop.

Batch by the minimum of (a) backend dispatch limits, (b) a bounded scratch
budget, (c) address/index limits, and (d) the number of complete pairs that
fit the current output staging buffer. Direct shared output needs no second
full-sized staging allocation. Ordinary host `out` uses a bounded staging
buffer and copies each completed tile to its final location. Cache command
recordings and scratch by shape, count them in the existing cache budget,
and invalidate uploads when a setter changes either bank. The public output
never becomes an unaccounted persistent cache allocation.

## Transform sizes

* CPU 2^10–2^20: finish the prototype across every size, including the
  small pair-batch and non-group-major cases. For 2^21 and 2^22 extend the
  element transform from 1024 to 2048 points (for example a 64×32 split),
  then measure its split and memory behavior before tuning. Audit `size_t`
  multiplication, allocation, and Python buffer-length checks at 2^22.
* GPU 2^10–2^16: ship a full-output entry for every existing Tier-B size on
  both Vulkan and Metal. Preserve the device-specific shared-memory variants
  and test compilation of the shipped binaries.
* GPU 2^17–2^22: implement the two-stage, global-scratch decomposition
  modelled in `tools/gpu_tierc_model.py`. Extend its `(N1,N2)` table through
  `(2048,1024)` and `(2048,2048)`. Stage one fuses the spectral product into
  its loads and writes transposed twiddle-adjusted scratch; stage two writes
  natural lag order. Full output needs no global peak reduction, which makes
  this a simpler Tier-C target than extending peak-only filtering. Compare
  direct strided stores with a coalesced transpose before choosing the final
  layout. Cap in-flight pairs by scratch/output bytes and by shader indexing;
  one 2^22 pair already needs 32 MiB scratch plus 32 MiB output.
* GPU `run_series` above 2^16 also needs a two-stage forward transform.
  Generalize the same decomposition for forward sign and the existing 1/n
  series normalization, then run the correlation stages without a host
  spectrum round trip. Metal's 32 KiB threadgroup limit and Vulkan device
  limits get separate compiled variants and capability checks.

## Correctness and performance gates

1. An independent complex FFT reference checks **all thirteen lengths**
   2^10–2^22 on CPU, Vulkan, and Metal where available. Small lengths cover
   multiple data/template pairs and every output element. Large lengths
   cover at least one complete pair against the reference, with memory-heavy
   cases in a dedicated CI job. Analytic impulses, circular shifts, complex
   phases, DC/Nyquist, and zero inputs pin lag order, conjugation, scale, and
   boundary behavior. Use mixed absolute/relative tolerances derived from
   measured fp32 error; never compare only magnitudes or sampled lags.
2. Check equivalence of a full bank against stitched data/template sub-runs,
   and of one series batch against one block at a time. Exercise odd bank
   dimensions, batch boundaries, partial input banks, changed/reused inputs,
   repeat calls, `out` identity and overwrite behavior, memmap and shared
   output, invalid dtype/shape/strides, size overflow, and allocation guard.
   Verify the peak-only flat result points to the corresponding full-output
   value, but retain the independent FFT as the primary oracle.
3. Verify the Tier-B/Tier-C transition at 2^16→2^17, the old CPU limit at
   2^20→2^21, and the maximum at 2^22. Check fallback/unsupported-device
   errors rather than silently moving GPU work to CPU. Run actual Radeon
   Vulkan tests here and actual Metal tests in macOS CI.
4. Keep the existing peak suite and benchmark matrix green. Use paired,
   interleaved timing on n=2048, 4096, 8192 and boundary sizes to catch a
   peak-path regression. Report separately: GPU transform-plus-output-write
   with resident inputs; fresh host-array delivery; and caller-provided
   shared output. Compare CPU/FFTW/MKL product-plus-inverse on identical
   complex64 spectra. Do not promise that a 2^22 GPU transform is faster
   until the new two-stage kernel is measured.

Land in reviewable stages: common API/CPU path and tests; Tier-B Vulkan and
Metal; Tier-C correlation and large-size CPU; Tier-C series forward; then
full-range CI, docs, and benchmarks. Each stage keeps existing peak behavior
and its performance checks intact. The public size promise should be made
only after the last stage passes on the relevant backends.
