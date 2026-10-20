# Package simplification, 2026-10-20

Baseline: `901799aed375e993937663e4e65d41931344379d`. This change prioritizes
unchanged or improved performance, then less code, then lower memory use.

The patch removes unused generated `fft16_44`/`fft32_84` codelets and obsolete
CUDA/Vulkan helpers, avoids discarded spectrum generation when a GPU
single-template plan is reused, and removes redundant window-intersection
masks. The cache now uses executor record keys directly instead of wrapping
them in `("exec", key)`. The unused record-kind registry, forwarding eviction
hook and `keep_storage` argument are gone.

There are 616 fewer runtime/generated source lines. No cache budget, numerical
kernel, gate threshold, allocation-ownership rule or eviction policy changes.
The window and cache changes remove temporary allocations without introducing
new retained state.

## Correctness

- GCC 15.3.1 rebuilt the complete native extension byte-for-byte identically to
  baseline, including the same kernel object. The generated FFT header also
  matches its generator.
- CPU-only full suite: 1,369 passed, 735 skipped.
- Physical Radeon 8060S focused GPU suite: 143 passed, 6 skipped.
- Cache tests cover exact LRU eviction under byte/entry pressure, held records,
  all-held temporary over-budget operation, incoming shared allocations, and
  caller-held storage becoming chargeable after release.
- Twelve physical-GPU comparison cases have identical peaks, work counters,
  normalized cache order and allocation/release/wait operation traces.

The CPU-only suite disabled Vulkan to avoid explicitly selected software
devices. The separate physical-GPU run exercised Vulkan cache/lifecycle paths.
CUDA and Metal hardware were not available.

## Measurements

Host: Ryzen AI MAX+ 395 / Radeon 8060S, CPython 3.13.5, NumPy 2.5.3.
CPU benchmarks pin core 6 and limit numerical-library workers to one.

| Scope | Result |
|---|---|
| Useful nonempty window layout construction | 44–55% less time |
| Repeated-template setup, real spectrum generation and mocked GPU plan | 8.970 to 0.737 microseconds |
| CPU production-leaf replay: 72 captures, 10,800 calls per arm | Paired aggregate time ratio 0.999997; exact outputs/counters |
| Cache touch, ordinary tuple key | 107.57 to 89.67 ns |
| Cache touch, nested hierarchical key | 172.76 to 158.30 ns |
| Cache room without eviction | Paired time ratio 0.9954 |
| Tested eviction/hold/shared-buffer bookkeeping | Paired ratios 0.8548–0.9893 |
| Physical GPU calls, twelve hit/entry-pressure/byte-pressure cases | No consistent throughput regression |

Cache bookkeeping uses 21 paired ABBA/BAAB rounds, real accounting/eviction
methods and mocked driver primitives. These are host-overhead results, not
hardware-GPU throughput claims. Cached CPU leaf calls already avoid window
setup, so the CPU replay is an unchanged-throughput control.

The GPU comparison uses the same live plans, compiled pipelines, thresholds and
settled choices for both arms. It alternates ABBA/BAAB order and verifies exact
outputs and operation counts outside the timed batches. An initial eleven-round
run was followed by a longer fifteen-round, 400-call-per-sample control for cache
hits. The longer control's candidate/baseline ratios were 0.9895 (flat spectral),
0.9938 (flat series), 0.9912 (hierarchical spectral), and 1.0008 (hierarchical
series). Small pressure-case differences straddled parity across rounds.
The initial apparent 1.4% hierarchical-series gain disappeared in the longer
control and is not claimed as a speedup.

Flattening cache keys removes a 56-byte wrapper per retained record on this
CPython build: 14 KiB at 256 records per context. The full-window traced
allocation peak falls from 54,642 to 48,456 bytes. Neither is an RSS claim.

Raw measurements, reproducible comparison scripts, build identities and logs
are retained in the session's `research/mf-simplify-20261020/` handoff directory.
