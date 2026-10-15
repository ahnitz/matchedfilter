# CPU work avoidance after the survivor pass

This assessment starts from `c5994d1e`. It separates measured results, arithmetic
estimates, and unimplemented experiments. The workload is the cap401 bank's top
template **id 4**, with 4,698 fine templates in 27 middle banks, matching H1 profiles,
N=2048 and chain 256/512/1024. The representative ladder uses synthetic data colored
by those real profiles; it is not the distinct captured-call replay fixture.
See [the completed survivor pass](cpu-survivor-performance.md) for its measurements.

The proposed **Q15 template-tail experiment** is now implemented and evaluated in
[Q15 tail packing](cpu-q15-tail-packing.md). The section below retains the original
padding estimate and its assumptions. A broader change to Q15 cache layout remains
a separate experiment.
Shared-subspace rejection has now failed a feasibility probe on this bank and should
not proceed to native implementation on the strength of its optimistic oracle.

## Completed: reorder decisions before adding new kernels

[Delayed Q15 rechecking](cpu-gate-order.md) evaluates the existing 512 gate before
rechecking Q15 survivors at 256 when the measured-cost model favors that order.
The final gate remains last and every accepted pair still passes all original
thresholds. On the representative Zen 5 ladder this avoids 94% of 256 rechecks,
pays for more 512 checks, and reduces whole-segment time 2.9%. This is distinct
from the earlier tail-packing and lazy-ingestion changes.

## Completed: prepare later tiers only for blocks that reach them

The previous engine skipped later-tier transforms for rejected pairs, but prepared
every block's input layout for every tier before any rejection took place.
`ap_hmf_run_series` now prepares tier 0 immediately and marks the plan's owned spectra
as pending for later tiers. Each later tier prepares a data slot once, when its first
incoming survivor needs it. Overwriting a series slot invalidates that tier's copy.

The public spectral setter still copies every coarse tier immediately. A pending-slot
count lets ordinary eager callers skip the survivor readiness walk altogether. This
preserves the existing input-copy behavior and avoids retaining new caller-owned
pointers. The full-refinement input policy, thresholds, Q15 arithmetic, and output
geometry are unchanged.

An occupancy replay of the first steady segment counted the exact required blocks:

| Coarse band | Previously prepared blocks | Needed blocks | Copies avoided |
|---|---:|---:|---:|
| 512 | 24,866 | 14,473 | 10,393 (41.8%) |
| 1024 | 24,866 | 2,947 | 21,919 (88.1%) |

The replay's tier survivor counts match the ordinary run. Those skipped copies
represent about 444 MB of logical reads and writes per segment, before alternate
layouts; this is not a measurement of DRAM traffic or bandwidth.

The [paired measurement](measurements/cpu-work-avoidance-20261014/lazy-ingest.json)
compares `c5994d1e` with the changed engine on a Ryzen AI Max+ 395, AVX3, pinned to
one core. Four fresh processes run baseline/candidate/candidate/baseline, each with
one warm and seven measured segments; other agent CPU jobs were idle. The chain,
Q15 choice, thresholds, real taps, profiles, and seed are fixed.

| Build | Fine stage, ms/segment | Whole segment, ms |
|---|---:|---:|
| Baseline | 301.777, 300.248 | 367.666, 364.486 |
| Prepare on demand | 289.626, 290.398 | 353.500, 355.625 |

The means fall **3.65% for the fine stage and 3.15% for the whole segment**. All
fine and follow-up output hashes agree exactly. Separate alternating public spectral
controls cover 36 cases across AVX3, AVX2 and SSE4; median ratios are within 0.6% of
unchanged, with identical output hashes. These are measurements on this host and
workload, not speed guarantees for other hardware or survival rates.

Some ingestion time moves from the unaccounted forward/ingestion remainder into
the later-tier counters. Their combined time falls from 125.97 to 117.64 ms; using
the remainder alone would overstate the saving. Regression tests cover reused
slots, repeated and clipped windows, zero-padded tails, real/complex/strided input,
independently rejecting later tiers, and public indexed/batch setters after series
calls. The measurement JSON records reproduction commands and build/input hashes.
The final regression selection passes 268 tests on each of AVX3, AVX2 and SSE4
(63 skips per target), and all 20 documentation tests pass.

## Q15 tail tiles: quantified opportunity, not a measured speedup

The [current screen](../src/q15-inl.h) places 32 templates for one data block in an
AVX3 vector. [Its caller](../src/matchfilt.c) iterates template groups outside data
blocks. Each partial template group therefore computes the same unused lanes for
every block. The ordinary [series policy](../python/matchedfilter/__init__.py) uses
32 data blocks at N=2048, although actual calls can be smaller or overridden.

For a template count T and a data count D divisible by four:

```
current vector-transform calls = D * ceil(T / 32)
4-data x 8-template calls       = (D / 4) * ceil(T / 8)
```

The second expression is also achievable by keeping complete 32-template groups
unchanged and handling only a profitable tail with 2-data x 16-template and/or
4-data x 8-template tiles. For example, a 17..24-template remainder can use a
16-template tile and an 8-template tile. A 25..31-template remainder has no padding
saving and can retain the current kernel. This tail-first experiment avoids changing
the dispatch and packing of the bulk of the bank.

The latest recorded profile contains these 27 template counts, in plan order:

```
214 183 169 179 178 224 131 121 210 194 215 103 187 219
187 159 196 159 254 140 156 156 173 156 193 80 162
```

They sum to 4,698. The [padding calculation and provenance](measurements/cpu-work-avoidance-20261014/q15-tile-padding.json)
retain every plan and its contribution. Summing executed work, rather than averaging
bank percentages, gives the following for **one full 32-block group per bank**:

| Quantity | Current | Tail tiles |
|---|---:|---:|
| Useful data/template pairs | 150,336 | 150,336 |
| Vector-transform calls | 5,056 | 4,800 |
| Executed lane pairs | 161,792 | 153,600 |
| Unused lane pairs | 11,456 | 3,264 |

This is **5.063% fewer vector transforms**, or an ideal padding-only kernel speedup
of 1.0533x before dispatch/packing overhead. Sixteen of the 27 banks benefit. Individual
examples are 103 templates (128 to 104 padded slots, 18.75% less work), 80 (96 to 80,
16.67%), 131 (160 to 136, 15%), and 140 (160 to 144, 10%). At 128 or 254 templates,
the total transform count does not improve; those are important controls.

This calculation assumes the same number of complete data groups per bank. The profile
records plan template counts, not each bank's actual distribution of group lengths
and clipped edge windows. It is therefore not an exact segment-level work count.
Applying 5.063% to roughly 135 ms of screen time gives an optimistic **6.8 ms per
segment, around 2% of whole-segment time**, before overhead and unaffected screen work.
That is a scale estimate, not a measured performance result.

Small data groups need a fallback. Forcing every group into a four-data tile would
increase aggregate vector calls by 3.80x, 1.90x and 1.27x at D=1, 2 and 3 respectively.
Use only complete data tiles, with a suitable two-data or original one-data path for
the remainder. Do not combine blocks with different valid windows merely to fill lanes.

### First experiment and acceptance criteria

1. Keep all complete template groups on the existing implementation. Add a private
   N256 tail experiment whose vector lanes carry independent existing pairs. Load the
   same quantized template/data values and retain the order of Q15 multiplications,
   saturated additions, twiddles, squares, thresholds and the current error margin.
2. Exercise template counts 80, 103, 131, 140, 162 and 193, plus controls 128/254.
   Include arbitrary template offsets, all tail sizes, data groups 1..5 and 31..33,
   and full, realistic `[20,236)`, clipped and single-lag windows. Require exact Q15
   statistics and pass masks, and exact final outputs/counts against the current path.
3. Measure alternating warm calls with fixed total work, ingestion excluded; then run
   the representative ladder and captured-call controls with output hashes. Report
   actual vector calls, cycles, cache misses and any extra packing cost separately.
   A saving confined to selected synthetic tails is insufficient if the aggregate
   ladder does not improve. Require the implementation to fall back without a material
   regression on small groups, controls, AVX2 and SSE4.

At the time of this estimate, no tail kernel had been implemented or benchmarked.
The [subsequent experiment](cpu-q15-tail-packing.md) measures the cost of constructing
multi-data vectors and compares exact outputs with the original kernel. The broader
cache-layout proposal below remains unimplemented.

### Broader cache-layout experiment, only after the tail result

Applying 4x8 tiles to complete groups could also reuse each template operand across four
data blocks. At N256, the current 32-lane scratch occupies 34 KiB and the packed template
group 32 KiB. A compact eight-template group would reduce the latter to 8 KiB: principal
scratch plus template storage falls from **66 to 42 KiB**. Four data rows and twiddles
add about 7 KiB, so this does **not** by itself prove residency in Zen 5's 48 KiB L1.

Obtaining that footprint requires compact template storage; merely loading eight lanes
from the existing 32-lane rows still touches the original cache lines. Multi-data
broadcast/permutation instructions and tails can also consume the benefit. Measure an
unpadded case such as 128 templates to isolate reuse from padding removal. The current
template-outer/data-inner loop already reuses templates through the cache hierarchy;
the hypothesis is reduced L1 traffic and pressure, not elimination of all template reads.

## Exact known-pass bypass: small, distribution-dependent experiment

`ap_mf_q15_screen` already produces a per-lane integer threshold. Every computed
Q15 squared maximum is nonnegative, so **a threshold no greater than zero guarantees
that lane passes**, independent of the transform. The existing code nevertheless runs
the kernel. Zero/nonfinite scales, zero thresholds and sufficiently large data norms
can produce this case.

When `stat == NULL` and all requested lanes in a batch have nonpositive thresholds,
the caller could emit the same pass bits and count without invoking the transform.
Padding lanes must not influence the decision. Keep the ordinary path when statistics
are requested or any active lane is unresolved. This bypass cannot introduce a new
rejection, change the margin, or supply an approximate statistic; it only recognizes
a decision that the current nonnegative statistic must produce.

First count how often this condition occurs in ordinary, loud-transient and zero-data
workloads. Then compare exact decisions, subranges and counts with the existing screen,
including mixed known-pass/unresolved lanes and subsequent float rechecks. No normal-noise
speedup is assumed: this may primarily avoid wasted Q15 work on unusual data blocks.
No implementation or occurrence-rate measurement is included here.

## Longer-term experiment: stream middle outputs into fine tiles

The consumer can potentially avoid retaining full-segment middle-stage streams by
producing a bounded time tile and immediately processing its fine banks. For scale,
27 complex64 streams for two detectors and 2^20 samples occupy **432 MiB**, before
halos and other buffers. This is a conditional footprint calculation: a real-quadrature
packed path has different storage requirements, and the number of retained streams
depends on the workload.

This would reduce intermediate storage and may improve cache locality, but it does
not remove the fine transforms themselves. It is a larger consumer scheduling change,
distinct from filling unused lanes in the native Q15 tail. The first prototype must
preserve the current block lattice, overlap/halo data, valid windows, event ordering
and data retained for later follow-up. Compare every output and count before measuring
peak resident storage, extra halo work and total segment time. No streaming prototype
or performance gain has been demonstrated in this assessment.

## Shared-subspace rejection: new probe rejects the tested cheap bounds

This was a potentially different use of a shared basis from reconstructing every
template's output. Compute a few basis correlations and reject a template only when
a certified envelope around its projected response stays below the existing threshold;
ambiguous cases would retain the current Q15 path. The [feasibility study](measurements/cpu-work-avoidance-20261014/README.md)
and [raw results](measurements/cpu-work-avoidance-20261014/proxy_bounds.json) now test
that idea on all 4,698 templates, using 32 Gaussian spectral blocks.

| Construction | Additional basis transforms / original transforms | Oracle rejection | Cheap bound rejection |
|---|---:|---:|---:|
| Whole bank, rank 8 | 4.60% | 0% | 0% |
| Whole bank, rank 16 | 9.20% | 25.09% | 0% |
| Cluster target 32, rank 8 | 22.65% | 54.12% | 0% |
| Cluster target 8, rank 2 | 24.44% | 1.47% | 0.144% |

These are global rates, including templates that fall back because their cluster is too
small. The oracle gives exact projected maxima for free, hiding their reconstruction
cost. The cheap bound uses a shared basis-energy maximum and coefficient/residual norms.
Splitting the residual bound into 16 frequency regions raises the last row's cheap
rejection only to 0.193%, against 24.44% extra transforms before any bound cost. Whole-bank
rank 8's split oracle rejects just 0.002%. The usable tested bound fails even the necessary
condition that rejected work exceed added basis-transform work.

Do not implement these bounds on this evidence. This does not rule out every possible
proxy: the probe uses full-lag bounds, Gaussian/profile normalization and clusters without
lag alignment. A different proposal must first demonstrate a materially tighter, cheap
bound under the actual clipped windows and account for its own work. The mathematical
modeled bounds also do not substitute for conservative runtime floating-point margins.

## Why a cached shorter FFT does not halve the next tier

The 256, 512 and 1024 tiers use nested frequency prefixes, but the inverse transform of
the shorter prefix is not a reusable half of the ordinary larger FFT. Ignoring scaling
and rounding, write a 2B-point input as `[L,H]`, each half of length B, and let F denote
the unnormalized inverse transform. The larger output satisfies

```
y[2j]   = F_B(L + H)[j]
y[2j+1] = F_B((L - H) * omega)[j],  omega[k] = exp(i*pi*k/B)
```

With `F_B(L)` cached, the even outputs can use `F_B(L) + F_B(H)`. But this still
requires a new `F_B(H)` and the new odd-output transform: **two new B-point transforms**,
just as the ordinary 2B FFT, plus cached-output traffic. The current four-step pass 1
also changes its input stride from 16 at N256 to 32 at N512; it does not expose a shared
prefix subgraph. An identically zero upper half is a separate support-pruning case,
not a general reuse argument.

Retaining 256 complex float values for the approximately 197,000 first-float-tier
survivors per representative segment writes about 404 MB and later reads about as much.
This is traffic without the suggested half-transform saving. Reusing spectral products
instead could save only their multiplications, while paying comparable storage costs.
Coarse normalization differs between tiers, and Q15 quantization/margins depend on N;
even a viable different decomposition would require fresh rounding validation rather
than a bitwise claim from linearity alone. No native prefix-reuse experiment is proposed.

## Prior work that should not be relabeled as new

The older plans concern different workloads and versions; their speed estimates are not
current promises. They nevertheless record experiments that constrain the next search:

- [Structural-plan tested ideas](cpu-structural-plan.md#7-tested-and-ruled-out): dense
  SVD required ranks 10..21 at band 256 against a reconstruction break-even near 8;
  assigned-parent matches had median 0.54; a 64-bin first gate passed 86..99% of pairs.
- [Roadmap bounds and pruning](roadmap.md#stage-a-parseval-bound): Stage-A energy bounds
  were 2.5..4.9 times the true maximum; cheap L1/energy features, sparse FFT and broad
  output pruning were already investigated. A late four-output subtree bound would be
  a distinct test, but it must count whole SIMD-group skips and pay for its reductions;
  no such benefit has been established here.
- [Roadmap even/odd sharing](roadmap.md#sharing-work-between-the-even-and-odd-passes):
  recovering half-grid shifts from an existing transform requires dense interpolation.
  This is related to the prefix-reuse obstacle above.
- [Q15 measurements](cpu-q15-gate.md): alternative factorizations and a smaller margin
  were tried; the margin remains unchanged. The recent middle-window specialization
  provides a modest measured gain, not a reason to promise further instruction-level gains.
- [Consumer levers](cpu-levers-consumer.md) superseded the older synthetic-workload
  ranking in [cpu-levers.md](cpu-levers.md) and [CPU_OPTIMIZATION_PLAN.md](CPU_OPTIMIZATION_PLAN.md).
  The current measured survivor/pooling changes are already recorded in
  [cpu-survivor-performance.md](cpu-survivor-performance.md).
