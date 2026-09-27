# Haswell CPU exploration and shared execution policy

Work started 2026-09-26 and continued 2026-09-27. This is exploratory work on
`codex/haswell-cpu-optimization`, not a change merged into main.

## Previous full-search checkpoint (`bd66606`)

The branch retains the shared scheduling policy plus AVX2 32x32 coarse-kernel
specializations: constant codelet strides, earlier final-result stores, and
constant twiddle/corner-turn addressing. No int16 path is enabled.

The final full-search ABBA comparison, excluding setup and segment zero:

| Run | Steady loop | Throughput, template-seconds/s |
|---|---:|---:|
| Baseline 1 | 38.692 s | 228,679 |
| Candidate 1 | 28.776 s | 307,476 |
| Candidate 2 | 28.844 s | 306,752 |
| Baseline 2 | 38.845 s | 227,775 |

This is **1.346x throughput / 25.7% less steady-loop time**, using the ratio
of mean loop times. All four runs retain exactly the same **4,386 template/time
trigger identities**. Maximum candidate SNR difference is 2.3842e-6, the same
maximum seen between the repeated baselines. Other field differences are
recorded in `kernel-full-trigger-validation.json`.

On the captured call, scheduling plus unit-stride/earlier-store codelets reduced
86.010 to 56.813 ms (1.513x paired, 39/41 wins); the fixed-address stage then
improved 56.779 to 54.913 ms (1.028x paired, 28/31 wins). The latter is the
version used in the full-search table above. Separate measurements must not
be multiplied and presented as one measured speedup.

Final CPU accuracy selection: **77 passed, 9 GPU skips per ISA** on local
AVX2, AVX-512 and SSE4; **36 passed, 9 GPU skips on Haswell**. Final pinned
Ryzen AVX2 performance checks improve the measured 1024-point cases by
10–12%; 4096-point cases are within about 1.1% of baseline.

**The requested 80% hardware-peak target remains unmet.** See the bottom-up
measurement and its limits below; this checkpoint is not a declaration that
kernel optimization is exhausted.

## In-place stage B and blocked-layout correction

The next experiment consumes the contiguous 32x32 stage-B intermediate directly,
removing its copy into another FFT buffer. Stage A refills that intermediate on
every call. The arithmetic and calibration thresholds are unchanged.

The first exact build (`retained-candidate`) measured **84.809 -> 52.886 ms** on
the captured call (**1.602x**, 41/41 paired wins). Against `bd66606`, it measured
54.798 -> 53.257 ms (**1.029x**, 30/31 wins). Its full-search ABBA times were
38.843 / 27.864 / 29.798 / 38.747 seconds: 1.346x from the ratio of mean times.
The second candidate run was visibly noisier; these results do not establish an
additional full-search gain over the previous checkpoint. All 4,386 trigger
identities matched, and maximum SNR difference remained 2.3842e-6.

Cross-CPU testing rejected the first code organization: it regressed Ryzen AVX2
4096-point transforms by about 6%, despite specializing only 1024. Assembly showed
the generic stage-B frame growing from 32 bytes to 2 KiB. Outlining the new FFT
reduced but did not remove that regression. The final arrangement isolates both
stage-B bodies and selects the one-bin scan specialization outside its loop.
The final local paired AVX2 checks against `bd66606` improve 1024 by 14–25%;
4096 is unchanged to 1.2% faster. AVX-512/SSE4 checks are within 2% of the
previous build. Intermediate rejected measurements are retained
in the audit directory, rather than discarded.

Testing also exposed a pre-existing correctness defect: `stageB_load_many`
assumed the strided intermediate layout even when `MF_ILAY=1`. Thus diagnostic
`MF_BBLK=2/4` settings could report incorrect peaks in the baseline. It now uses
the appropriate element and block strides. The default block-one path did not
have this defect.

With correctness restored, block sizes 2/3/4 were measured against the final
block-one implementation on the capture: 0.922x / 0.941x / 0.919x respectively.
They remain diagnostic options; no new scheduling row enables them.

The standard test suite now covers both intermediate layouts, block sizes 1, 2,
3 and 4 (including a partial final group), every available CPU backend, full
correlation, arbitrary peak bins, repeated execution, and updated input spectra.
Local final-build selection: 85 passed, 33 skips. Neither
this optimization nor the new tests changes calibration acceptance criteria.

Final isolated-dispatch Haswell build: **85.399 -> 52.863 ms**, paired
**1.622x**, 41/41 wins, with 67 tests passing and 31 GPU skips. The direct native
benchmark holds five independent plan allocations and interleaves 21 rounds:

| Threshold pattern | Original | Candidate | Paired speedup |
|---|---:|---:|---:|
| Zero threshold | 3.410 us | 2.670 us | 1.275x |
| Reject all | 3.405 us | 2.646 us | 1.283x |

Using the same approximate 52,200 useful FLOPs/pair as below, this is
19.55–19.73 GFLOP/s, **24.9–25.2% of the measured FMA peak**, not 80%.
These are cache-resident synthetic inputs and source/assembly operation estimates;
they are not hardware retired-FLOP counters or end-to-end capture throughput.
The first pattern admits a peak; the second avoids peak updates, representing
the common coarse-rejection behavior without claiming to duplicate the fixture.

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
constant element stride one and constant product stride eight. Product dispatch
is limited to the balanced 32x32 geometry; other product shapes and SIMD widths retain
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
(1.016–1.116x). The initial 4096-point cases varied from 0.970–1.004x, and a repeat found
0.954x at 37 templates. Contrary to the initial assumption, those transforms
also use a 32-point product codelet (their split is 128x32). The product route
was therefore narrowed to 32x32 geometry. Final pinned repeats are within
about 1.1% of baseline at 4096.

An earlier-store experiment reduced live output temporaries and measured
1.027x over the broader constant-stride prototype (28/31 wins). It remains
retained after a 1.032x repeat against the narrowed implementation (28/31
wins). Fixing the surrounding stage-A addresses adds 1.028x on Haswell.
A 4x8 Stockham-factorization experiment was slower (0.986x, 5/31 wins).

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

## Native controls and rejected int16 candidates

A same-process native comparison interleaves the original kernel and the
unit-stride/early-store kernel across five simultaneously held scratch-buffer
layouts. Median times are 3.452 and 2.986 microseconds per pair; paired speedup
is 1.160x, with every layout between 1.149 and 1.167x. The approximate 52,200
FLOP count gives 17.5 GFLOP/s, about 22% of the separately measured raw FMA
peak. This control uses a zero threshold and a cache-resident synthetic pair;
it is not a retired-operation count or an end-to-end throughput metric.
Unpaired microbenchmarks varied enough to require this paired control.

The Haswell int16 screen found a 1.257x reuse-only gain for prequantized block
floating point (1.234x including data ingestion), while ordinary Q15/SWAR
variants mostly lost. On the real captured coarse spectra, generated with
matchedfilter's own forward FFT and the same normalization/window rules, the
candidate is only 1.141x faster including ingestion for the main window.
It also changes admission: baseline **337**, candidate **332**, including
**6 rejected baseline admissions** and one extra admission, with maximum
relative magnitude error **0.896%**. It is not enabled.

A rounded-shift experiment still rejects **9 baseline admissions**, admits one
extra pair, and retains the same worst error. It did not reject any of this
fixture's 28 final peaks, which does not establish calibration safety.
Both variants pass the seeded synthetic 0.01/0.001 transfer screen. This is a
concrete example of why that test is a paired guard rather than a population
certification: real spectral distributions expose errors absent from its
synthetic profiles. No calibration threshold was adjusted to conceal these
changes, and no new calibration fallback was introduced.

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

The final isolated-dispatch full-search confirmation took **27.823 s** for
318,007 template-seconds/s, versus the neighboring baseline runs at 38.843 and
38.747 s (about 1.39x). This is one final-build confirmation, not an additional
ABBA experiment. All 4,386 template/time trigger identities matched; maximum SNR
difference was 2.3842e-6. Full field comparisons, including non-identical ancillary
fields, are saved in `kernel-isolated-trigger-validation.json`.


## Arithmetic-port and factorization follow-up

After `c51ef50`, a targeted experiment replaces 23 unary `0-x` operations in
each specialized 32-point codelet with sign-bit XOR. This leaves numerical
magnitudes unchanged, including zero, but zero sign bits may differ. The first
Haswell capture comparison is 52.820 -> 51.977 ms, **1.013x**, 35/41 paired wins.
Local AVX2 checks range from 0.985x to 1.019x across the measured 1024/4096 cases.
The local numerical selections pass 53 tests (28 skips) and 55 adversarial,
peak and series tests (3 skips). Final remote confirmation is recorded below.

The separate 4x8 Stockham stage-B-only factorization is rejected: 52.751 ->
54.413 ms, **0.972x**, 0/31 wins. This is distinct from the earlier experiment
that changed both stage-A and stage-B codelets. Its correctness check passes;
the extra arithmetic and scratch traffic do not pay off in this implementation.

The 8x4 stage-B-only factorization is also rejected: 52.987 -> 54.192 ms,
**0.977x**, 2/31 wins, after passing the same numerical checks. The retained
split-radix formulation remains faster for both tested orderings.

The exact final branch build repeats the sign-negation gain: 53.405 ->
52.395 ms, **1.0137x**, 38/41 wins against `c51ef50`'s isolated-dispatch build.
Haswell's broader selection passes 67 tests with 31 GPU skips. The standard
reused-buffer test now additionally mixes positive and negative zero in the
input and checks both full correlation and absent peaks at threshold zero;
all 12 layout/geometry cases pass on all available local and Haswell backends.
The 80%-of-raw-FMA target is still unmet. The arithmetic change is retained
because it reduces elapsed time, not because it inflates a FLOP-rate metric.
The initially slowest Ryzen case (4096, 128 templates, 0.985x in the screen)
repeated at **1.007x** over 41 paired rounds with 150 calls per sample, so that
small regression did not reproduce.

## DIF dataflow experiments

Two split-radix decimation-in-frequency variants were checked independently
against scalar DFT indexing, then against the 12 standard layout/reuse/zero
cases on Haswell. Both pass correctness but lose to `0ff72cc`:

| Changed stages | Baseline | Candidate | Paired speedup | Wins |
|---|---:|---:|---:|---:|
| B only | 52.239 ms | 54.417 ms | 0.956x | 3/31 |
| A and B | 51.582 ms | 54.697 ms | 0.947x | 1/31 |

Neither dataflow is enabled. The dominant captured lag window is [425,3671)
for 234 of 236 blocks. After conservative coarse mapping, the stage-B scan
still requires most of its 32 outputs, limiting simple output-pruning gains.

## Fused output consumption and integration checks

The next optimization consumes each stage-B FFT output in a generated callback.
The peak-only consumer computes squared magnitude and updates the thresholded
maximum directly, avoiding output stores followed by a separate scan. It applies
to the measured 32x32, eight-lane geometry, a positive threshold, one bin,
contiguous intermediates and stage-B blocking 1. Series capture and other
geometries retain their existing consumers. The generator remains independent
of peak-selection logic, and no calibration threshold or table changes.

The first outlined-consumer Haswell capture comparison was 52.755 -> 46.519 ms,
**1.134x**, 38/41 paired wins against `0ff72cc`. Against the original capture
baseline it was 84.451 -> 46.317 ms, **1.817x**, 41/41 wins. Two complete search
runs measured 25.085 and 25.227 s, or **352,728 and 350,741 template-seconds per
wall second on one physical core**. Neighboring original-baseline runs measured
39.809 and 39.312 s (222,264 and 225,070 template-seconds/s). These exclude setup
and segment zero. All 4,386 template/time trigger identities match; maximum SNR
difference against the original reference is 2.3842e-6. These full-search results
precede the final bank-binding dispatch cleanup, so they are not mislabeled as
measurements of that later binary.

### Why the first implementation was not integration-ready

Adding the helper initially regressed an unthresholded Ryzen AVX2 bank by 5–7%,
even though that call did not use the fused FFT. An identical-build two-worker
control differed by only 0.3%. User-space hardware counters found about 5% more
cycles with only 0.12% more instructions, fewer branch misses and no corresponding
increase in L1 data or instruction misses. Five-layout native controls were
closer to 1%; they did not justify dismissing the Python bank regression.

Two changes address this sensitivity without a CPU-model exception:

* On ELF targets, optional peak-consumer helpers live in a separate text section.
  The measured original AVX2 scan, product loader and entry-point addresses are
  then preserved. Instruction comparisons also match after relocation operands
  are normalized. Unused consumers on other SIMD widths are static and omitted.
* A bank binds the backend's native product kernel once, after its existing
  argument validation. The pair loop calls that binding directly and counts
  returned peak indices. Ordinary internal transform calls retain their checked
  API. This avoids adding selection and repeated argument checks per pair.

The binding is valid only for the life of its transform plan; kernels retain
backend ownership and no public ABI changes. The optional threshold consumer
falls back for multi-bin, stored-series and unsupported layouts. The initial
per-pair dispatch and tail-wrapper variants are rejected; their negative control
results remain in the audit directory.

Tests now compare positive-threshold peak-only output against an independent
full FFT at vector/window boundaries on every available CPU target. The FDR
transfer test explicitly creates an AVX2 plan when available, even on AVX-512
hosts, and compares the positive-threshold consumer at the existing empirical
0.01 and 0.001 rates. The low execution threshold avoids censoring the sampled
magnitudes. This is a paired calibration-transfer check, not a population-rate
certification. GPU-less CI still runs the CPU/reference part.

The raw-FMA 80% target remains unmet. These optimizations reduce elapsed time by
avoiding data movement and dispatch work; raw peak arithmetic utilization is
not an appropriate substitute for the measured search throughput.

The bank-bound final candidate passes the complete local CPU suite: **691 passed,
328 skipped**. The Haswell capture measures 52.053 -> 45.463 ms against
`0ff72cc`, **1.1483x**, 41/41 paired wins. Final complete-search confirmation,
GPU checks, repeated cross-ISA timing controls and hosted CI are being recorded
before declaring the branch ready to merge. The previously measured intermediate
bank-selection build also improves the doubled-amplitude capture (high survivor
fraction) by 3.0%; that measurement is retained with its own binary hash.
