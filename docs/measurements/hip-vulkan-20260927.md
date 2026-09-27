# HIP versus Vulkan on Radeon 8060S

Measured September 27, 2026 UTC, against library revision `06660a9`.
The production backend remains **Slang → SPIR-V → Vulkan/RADV**.
These HIP prototypes did not improve the important batched workloads.
This is a comparison of specific implementations, not a proof that HIP is
inherently slower or that the Vulkan kernels are optimal.

[Raw timing blocks and compiler statistics](hip-vulkan-20260927.json).

## Workload and controls

The device is Radeon 8060S (`gfx1151`) in Ryzen AI Max+ 395. HIP 6.4.43484
uses Clang 19; Slang is 2026.18.2. Linux host execution was pinned to CPU 2.

Two kernels were compared:

- FP32 fused product, 4,096-point inverse transform, and one full-window
  peak per pair. Radix 16, 256 threads, and 16 KiB shared staging match the
  shipped `tierb_4096.spv`.
- The 512-point FP16 coarse stage, using packed pairs and four-template
  tiling, 32 threads, and 2 KiB shared staging. It matches
  `tierb_512_c16t4.spv`, not the older FP32 tiled coarse kernel.

Both backends reuse resident data, templates, and outputs. Compilation,
allocation, upload, validation, and result copies are excluded. Timings
include host dispatch and the completion wait; **these are not GPU timestamp
measurements or public filter-class timings**. The coarse measurement is
one coarse kernel, not an entire hierarchical call.

Each comparison uses ordinary HIP launches, captured HIP graphs, and cached
Vulkan command buffers, with one or 32 ordered executions before waiting.
Vulkan barriers order repeated output writes. There is 0.4 s of warmup,
followed by 11 timing blocks of at least 40 ms. Backend order is reversed
for a second round. Reported medians combine all 22 blocks. Times for 32
executions are divided by 32; this amortizes submission overhead but does
not remove it completely.

The first HIP version compiled Slang's CUDA output with a small compatibility
header. A second version replaced generated loop/control-flow scaffolding
with fixed-size HIP loops while retaining the butterfly arithmetic, radix,
shared-memory capacity, reductions, and template reuse. Explicit inlining
alone did not change the first version's resource usage. Neither version is
an extensively tuned HIP implementation. Prototype sources and builds remain
in the local `.local/hip-compare` investigation directory, outside the library
and wheel contents.

## Results

Milliseconds per batch, using 32 executions per completion wait. HIP below
is the revised direct-loop version, with graph submission.

| Kernel | Data × templates | Vulkan | HIP | Vulkan advantage |
|---|---:|---:|---:|---:|
| FP32 peaks, n=4096 | 16 × 512 | 0.650 | 1.314 | 2.02× |
| FP32 peaks, n=4096 | 64 × 512 | 2.492 | 5.203 | 2.09× |
| FP16 coarse, band=512 | 16 × 512 | 0.0454 | 0.1709 | 3.77× |
| FP16 coarse, band=512 | 64 × 512 | 0.1615 | 0.5903 | 3.65× |

The direct Slang-to-HIP route was slower still: approximately 2.808 ms for
medium-batch peaks and 0.384 ms for medium-batch coarse execution. Rewriting
the fixed-size control flow mattered, so using only that initial route
would have overstated the disadvantage of a HIP implementation.

For a tiny **1 × 4** peak batch, a synchronous ordinary HIP launch took
13.4 µs versus Vulkan's 29.0 µs. With 32 executions per wait, those became
7.5 µs and 8.0 µs per execution. This exposes host/submission overhead,
including differences between the prototype host wrappers; it is not evidence
that changing the production API to HIP would halve its latency.

HIP graphs made little difference to the medium and large kernel timings.
Explicit wave32/WGP compiler settings produced essentially the same results;
code-object inspection confirmed the default peak build already used wave32.
HIP mapped noncoherent allocations also left medium-batch times essentially
unchanged: 1.313 ms for peaks and 0.170 ms for coarse execution. This did not
exhaust every possible allocation/cache policy.

## Correctness and compiler findings

Every timed case was checked against complex128 inverse transforms of the
same input spectra. Flat checks cover both the maximum magnitude and the
complex value at each returned lag; near-equal maxima may choose different
indices after FP32 rounding. The largest checked relative error stayed below
the existing `1e-5` tolerance. The coarse check compares magnitudes against
the reference with the same quantized input: observed errors were below
0.15% in both backends. FP16 coarse indices can differ near ties, so this
check does not establish identical screening decisions or recalibrate
false-dismissal probabilities.

RADV reported no scratch allocation for either production kernel. The
initial HIP builds reported 264 bytes/thread of private memory for peaks and
452 bytes/thread for coarse execution. The revised peak port eliminated its
private allocation; the revised coarse port still used 432 bytes/thread.
Private allocation is not synonymous with register spilling: it can also
come from addressable arrays and stack state. The coarse port therefore has
an identifiable remaining optimization target, and its deficit is not a
limit on what a tuned HIP kernel could achieve.

## Decision

Keep Slang → Vulkan. There is no measured batched-throughput benefit here
that justifies adding and maintaining a HIP backend. Continue investigating
Vulkan submission overhead for small batches and kernel register/shared-memory
use where profiling shows a bottleneck. These measurements do not establish
absolute hardware optimality.
