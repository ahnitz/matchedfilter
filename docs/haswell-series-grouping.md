# Haswell CPU exploration and shared execution policy

Work started 2026-09-26 and continued 2026-09-27. This is exploratory work on
`codex/haswell-cpu-optimization`, not a change merged into main.

## Measured finding

The og-node-169 real-data fixture spends 92% of its recorded native regions
in coarse filtering. Those counters exclude forward FFT and some preparation.
Only 2.23% of pairs reach refinement. The CPU is an Intel Xeon E5-2698 v3,
Haswell-EP, running AVX2 on logical CPU 3. See `haswell-library-replay.md` for
the fixture and original baseline.

Eight-block grouping activates the pair-batched alternate for a 1024-point
coarse transform. Four-block grouping keeps the balanced transform, which is
faster for this series workload. This is a scheduling/layout choice: the
coarse band, U metadata, threshold, and calibration remain unchanged.

An initial general flat-filter dispatch change was rejected. Synthetic cases
showed inconsistent regressions, including fresh-process regressions around
8%. The retained experiment changes only hierarchical series grouping for
the measured 4096/1024, 32–64-template shape; ordinary flat filtering and
direct hierarchical run batches keep their existing dispatch.

## Results

All raw reports and reproduction scripts are in
`docs/audits/haswell-series-grouping-2026-09-27/`.

| Experiment | Baseline median | Candidate median | Paired median speedup |
|---|---:|---:|---:|
| Native grouping prototype, 41 rounds | 81.970 ms | 64.776 ms | 1.267x, 41/41 wins |
| Shared policy implementation, 31 rounds | 84.735 ms | 64.088 ms | 1.326x, 26/31 wins |

Both reproduce the 28 captured peaks, with identical indices and complex
values within rtol=atol=1e-5. Every timed call also has to reproduce its own
warm output exactly. Separate processes are interleaved and retain their plans.
The comparator records loaded binary hashes, raw times, and thread CPU times.

Variants using 32, 37 and 64 templates, each with input scales 0.5, 1 and 2,
all improved in paired median time. Speedups span 1.055–1.428x. Scale 0.5
produces no final peaks; scale 2 produces a peak for every pair. The smaller
gain with high refinement load is expected. These variants verify scheduling
behavior, not the statistical false-dismissal rate.

The full PyCBC search was run in baseline/candidate/candidate/baseline order
with the native grouping prototype. Setup and segment zero are excluded,
using the existing summarizer and 8,848,032 template-seconds denominator:

| Run | Steady loop | Throughput, template-seconds/s |
|---|---:|---:|
| Baseline 1 | 39.869 s | 221,927 |
| Candidate 1 | 32.675 s | 270,786 |
| Candidate 2 | 34.165 s | 258,983 |
| Baseline 2 | 39.241 s | 225,479 |

The ratio of mean loop times is 1.184x (15.5% less time), about 19% greater
throughput. All four runs have exactly the same 4,386 template/time trigger
identities. Candidate maximum SNR difference from baseline 1 is 2.3842e-6;
maximum chi-square difference is 7.6294e-5. PSD-variation fields also vary
between repeated baseline runs; candidate differences remain within that
observed spread. See the per-field report rather than treating full outputs
as bitwise identical. The table-driven version was separately verified on
the captured workload; the full-search figures above belong to the equivalent
native grouping prototype.

This is a shared host. Preserve raw timing variation and use paired trials;
do not turn one favorable timing into a universal regression threshold.

## General mechanism: CPU, Vulkan and Metal

There are no Haswell checks in the native engine. `execution-policy.json`
contains measured rows; `_execution_policy.py` matches device, backend,
operation, transform/coarse sizes and template-count range. Exact device
names precede architecture keys, which precede an explicitly provided generic
row. Equally specific overlapping rows are errors. Unknown or invalid fields
are rejected. `MF_EXECUTION_POLICY` selects another file for experiments;
restart the process after editing a file because loaded tables are cached.

The first supported option is `series_group`, a number of time-series blocks:

* CPU hierarchical plans pass it to the native constructor, which bounds
  working memory. Legacy C callers keep group eight; an additional constructor
  permits an explicit group. `MF_DGROUP` remains the diagnostic override.
* Vulkan and Metal peak-series and continuous-correlation executors use it
  as a batch cap. Their existing memory and dispatch bounds still apply.
* Missing measured coverage leaves the executor's established default intact.
  This is an execution default, never a calibration fallback.

The shipped experimental row is CPU/AVX2, architecture identity
`genuineintel-family6-model63`, n=4096, band=1024, 32–64 templates, group four.
CPU keys come from generic vendor/family/model metadata, without a list of
microarchitecture-specific code branches. GPU keys reuse the existing device
architecture hierarchy. There are no measured GPU rows yet, so GPU defaults
remain unchanged. Both executors consume the same selector and schema; future
options should be added only when an implementation and measurements exist.

Selection happens outside native hot loops. The policy cannot change
calibration, numerical precision, device choice, or capability limits.
Native `series_group()` reports the actual bounded group without changing
the established `(band, taps)` config tuple.

## Validation

* Native grouping prototype on Haswell: 80 passed, 14 GPU-related skips,
  including coarse FDR transfer and series/dispatch regression tests.
* General policy on Haswell: 39 passed, 6 GPU skips.
* Local Ryzen compilation: the earlier grouping candidate passed 32 CPU tests
  per target under AVX3, AVX2 and SSE4. The Haswell policy has no matching row
  on this CPU.
* General policy/device/tuning/accuracy selection: 60 passed, 16 deselected.
* Actual Radeon 8060S GPU series tests plus policy tests: 61 passed.
* Source distribution explicitly includes the execution-policy JSON (verified).
* Final selector validation, including CPU metadata: 18 passed, 2 actual-GPU
  cases deselected in that hardware-independent run.

New tests cover reused layouts after data/template updates, threshold changes,
four/eight-block grouping with ragged windows and partial groups, exact policy
coverage, precedence, ambiguous/invalid rows, native bounds, GPU batch caps
versus memory caps, and actual GPU peak parity. Mock scheduling tests exercise
both Vulkan and Metal on CPU-only CI; hardware GPU tests skip when unavailable.

## Further kernel probes

Against the improved table-driven baseline, 21 paired rounds per option:

| Diagnostic change | Speedup | Wins |
|---|---:|---:|
| FFT first dimension 16 | 0.960x | 2/21 |
| FFT first dimension 64 | 0.932x | 0/21 |
| FFT first dimension 128 | 0.939x | 0/21 |
| Stockham product option | 1.005x | 12/21 |
| Alternate intermediate layout | 1.003x | 14/21 |
| Pair-loop tile 4 | 1.005x | 14/21 |
| Pair-loop tile 16 | 0.995x | 7/21 |

None merits a default change. The FFT split override affects both coarse and
full transforms, so these are whole-workload screens, not isolated codelet
rankings. An isolated AVX2 split-radix-32 product variant improved captured
execution from 64.222 to 61.569 ms, paired median 1.044x, 29/31 wins. It
passed 36 accuracy/series/calibration-transfer tests (9 GPU skips), but is
not yet enabled in branch source: broader performance coverage is pending.

Further experiments against that kernel candidate:

| Change | Paired median speedup | Wins |
|---|---:|---:|
| Precompute full twiddle vectors at n=1024 | 0.986x | 9/31 |
| Map half of codelet additions to FMA with multiplier one | 0.984x | 6/31 |

Both are rejected. Multiplication by one in the second experiment must not
be counted as useful additional FLOPs. Reproduction scripts preserve the
experiments without altering the production codelets.

## Unit-stride codelet checkpoint

The branch now generates separate AVX2 32-point split-radix codelets with
constant element stride one and constant product stride eight. Dispatch
checks those strides; strided product calls and other SIMD widths retain
their prior implementation. The generated source remains reproducible from
`src/gen.py`. This specialization removes runtime addressing from a large
DAG without forcing it inline into every caller.

The actual narrowed branch implementation versus the policy-only package:
**64.627 to 59.539 ms**, paired median **1.094x**, **41/41 wins**. An earlier
broader prototype was 1.060x faster than the split-radix-only candidate.
These are different comparisons, not speedups to multiply mechanically.

Validation: 63 CPU tests passed locally under AVX2, with 6 GPU skips;
36 passed on Haswell with 9 GPU skips. This includes coarse FDR transfer,
layout/partial-group cases, adversarial inputs, and series filtering.
A local Ryzen AVX2 screen improved all measured 512/1024-point balanced cases
(1.016–1.116x). Unaffected 4096-point cases varied from 0.970–1.004x; repeat
measurements are needed before interpreting those small differences.

An earlier-store experiment reduced live output temporaries and measured
1.027x over the broader constant-stride prototype (28/31 wins). It remains
isolated pending measurement against the narrowed branch implementation.

## Bottom-up throughput target

The user requests continued optimization toward at least 80% of the hardware
ceiling. This target is **not achieved**. Track raw FP32 peak separately from
an instruction-mix bound; do not silently redefine the target or count redundant
arithmetic as progress.

Haswell provides two 256-bit FMA pipelines: 32 FP32 FLOPs per core-cycle.
At the nominal 2.3 GHz this is 73.6 GFLOP/s per physical core. This workload
is pinned to one logical CPU; the second SMT thread does not add execution
units. Frequency under AVX load is not assumed from the nominal clock.
See Intel's [Optimization Reference Manual, volume 2](https://cdrdv2-public.intel.com/821614/356477-Optimization-Reference-Manual-V2-050.pdf).

An independent native microbenchmark on CPU 3 measured median **78.432
GFLOP/s**, with 9 samples spanning 72.896–78.681 GFLOP/s. The corresponding
80% target is **62.746 GFLOP/s**. Its hot loop has twelve independent YMM
FMAs, no loads/stores or spills, and 192 real FLOPs per iteration. The saved
assembly verifies that loop. An initial benchmark was compiler-hoisted out
of the timing region; the retained version uses a compiler barrier at function
entry to prevent that. Hardware cycle counters are permission denied;
reported TSC ticks are invariant-clock ticks, not measured core cycles.

A cache-resident native coarse-kernel benchmark (product, 1024-point FFT and
peak scan over [100,924)) measured **3.209 microseconds per pair** for the
split-radix candidate. A straight-line disassembly count gives 5,448 YMM FLOPs
for its product codelet and 3,912 for its plain codelet. Each runs four times
in the balanced 32x32 transform. Adding the source-level twiddle count
(12,288) and magnitude scan (about 2,472) yields approximately **52,200
FLOPs/pair**, or **16.3 GFLOP/s: roughly 21% of measured raw peak**. This is
an instruction/source estimate, not a hardware-retired FLOP measurement;
loop bounds, masked lanes and scan bookkeeping make it approximate.

The captured library call also includes forward transforms, packing, gate
logic and refinement, so dividing only the coarse FFT FLOPs by its full call
time would be misleading. The direct benchmark isolates a concrete kernel
that still has substantial headroom. The instruction inventory shows many
addressing/stack operands in the generated codelets; those are static counts,
not proof that every operand is a register spill. Constant-stride codelet
specialization is the next experiment, alongside scrutiny of dependencies
and the load/shuffle/add execution limits.

## Reproduction

On og-node-169, the installed baseline remains untouched. All experiments live
under `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169`.
`kernel-study/group-baseline` and `kernel-study/policy-candidate` are isolated
package roots. The fixture remains `capture/hier-00.npz`.

```sh
P=/home/ahnitz/pycbc-wider-cpu-benchmark-20260926
R=$P/hosts/og-node-169
export PYTHONPYCACHEPREFIX=$R/cache/pycache TMPDIR=$R/tmp
export LD_LIBRARY_PATH=$P/lib OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
taskset -c 3 "$P/venv/bin/python" "$R/kernel-study/policy-src/tools/compare_captured_series.py" \
  "$R/kernel-study/group-baseline" "$R/kernel-study/policy-candidate" \
  "$R/capture/hier-00.npz" --rounds 31 --output "$R/results/next-policy.json"
```

For kernel probes, compare policy-candidate with itself and supply a candidate-only
diagnostic option, e.g. `--candidate-env MF_N1=64`. The comparison tool also
supports `--templates` and `--scale` workload variants. Scaled variants compare
the builds against each other, not against the original capture's trigger set.
