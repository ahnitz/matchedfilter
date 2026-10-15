# Gate execution order, 2026-10-15

Baseline is commit `702e6af8`, including Q15 tail packing. Its native hash is
`b7fc2583ceea69e842eff7e35b25e0c9e17f77c72ebeb37f2e5164cadd71ede7`.
The final selective implementation's native hash is
`229966af7e7dec8624e26a292ed00adb1f61e9870a355d212f510984cce4c68f`.
Python scheduling and profiling also changed; their hashes are retained in
[final-build-identity.json](final-build-identity.json).

All timing used one idle physical core (CPU 4) on an AMD Ryzen AI Max+ 395,
AVX3 unless a control explicitly names AVX2/SSE4. Test jobs were stopped during
timing. BLAS/OpenMP/MKL thread counts were one. No GPU or ARM timing was done.

## Files

- [selectivity.json](selectivity.json): diagnostic counts over two segments,
  including warmup, aggregated globally and by template count. The probe checks
  float512 on every Q15 survivor but retains the original filtering decisions.
  Baseline/probe output hashes match. These instrumented timings are not used.
- [selectivity-probe.patch](selectivity-probe.patch): the diagnostic against
  `702e6af8`; compile with `CFLAGS=-DAP_GATE_ORDER_PROBE` to enable it.
- [initial-prototype.patch](initial-prototype.patch): the always-enabled native
  prototype, before model selection, shared preparation and input counters.
- [prototype-ladder-8seg-abba.json](prototype-ladder-8seg-abba.json): separate
  prototype comparison, eight segments per process, ABBA, first segment excluded.
  Its fine/segment speedups were 1.039x/1.035x. Stage metrics are omitted because
  that prototype still used the old assumption that gates run in band order.
- [final-ladder-24seg-baab.json](final-ladder-24seg-baab.json): final selective
  build, 24 segments per process, BAAB, first segment excluded. Exact commands,
  configuration, package/build/input/output hashes, per-process timings and gate
  input counts are retained. Original full report paths remain as provenance.
- [fallback-controls.json](fallback-controls.json): 27 grouped-series cases,
  template counts 80/128/254, groups 1/3/32, three CPU targets. Eleven alternating
  rounds at approximately 30 ms per sample, with raw samples and output hashes.
  These low-level plans keep ordinary gate order and test fallback overhead.

- [avx3-reversed-controls.json](avx3-reversed-controls.json): repeat all nine AVX3
  controls with build positions reversed, 15 rounds at about 50 ms per sample.
  `final_speedup` inverts the raw harness ratio to mean baseline time / final time.

Fallback-control medians were 0.991x/1.000x/1.001x on AVX3/AVX2/SSE4. The reversed
AVX3 repeat's median was 0.998x. Original slow controls at 254 templates/group 1
and group 3 measured 0.978x/0.980x, then 0.997x/0.997x in the repeat. Another
case, 128/group 3, measured 0.974x in the repeat. Individual small-shape fluctuations
are retained; these measurements cannot guarantee parity for every fallback case.

Do not pool prototype and final timings. The historical ladder driver defaulted
its baseline label to `b3c1b022`; these artifacts correct the label to the actual
explicitly supplied `702e6af8` binary. The driver now accepts `--baseline-commit`
so future comparisons record that label directly.

## Final ladder result

The cap401 top-id-4 bank has 4,698 fine templates in 27 middle groups, H1 profiles,
two detectors, N2048, chain 256/512/1024, Q15 on, threshold 6 and dismissal budget
0.001. Input is deterministic seeded synthetic data colored by the real profiles.
This is a representative API workload, not a complete PyCBC production run.

| Metric | Baseline | Final | Less time |
|---|---:|---:|---:|
| Fine, ms/segment | 286.620 | 276.709 | 3.5% |
| Whole segment, ms | 350.702 | 340.601 | 2.9% |

Each value averages two fresh processes over 23 steady segments. Baseline fine
means are 285.181 and 288.060 ms; final means are 276.746 and 276.672 ms. All four
output hashes agree, as do inputs to the 1024 gate and final refinement. The
cost-file hash is unchanged before and after the comparison. New scheduling
reduces float256 inputs from 292,381 to 17,619 per segment, while increasing
float512 inputs from 197,447 to 292,381. Q15 work and its measured time are unchanged.

The diagnostic observed float512 passing 5.8% of Q15 survivors over its two
segments. The final long comparison observed 6.0% over its steady segments;
these are different input sets and are reported separately.

## Reproduction

Use immutable, separately built Python package directories; the package path
must contain `matchedfilter` and its native extension. From the repository root:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python docs/measurements/cpu-q15-tail-20261014/ladder_builds.py \
  --baseline BASELINE/python --candidate FINAL/python \
  --baseline-commit 702e6af8 \
  --baseline-sha b7fc2583ceea69e842eff7e35b25e0c9e17f77c72ebeb37f2e5164cadd71ede7 \
  --candidate-sha 229966af7e7dec8624e26a292ed00adb1f61e9870a355d212f510984cce4c68f \
  --bank BANK.hdf --profiles PROFILES.npz --cost-file COSTS.json \
  --harness tools/profile_cpu_ladder.py --cpu 4 --segments 24 --order BAAB \
  --output-dir ladder-24

OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
taskset -c 4 python tools/bench_q15_tails.py BASELINE/python FINAL/python \
  --output controls.json --isas AVX3 AVX2 SSE4 --kinds series \
  --templates 80 128 254 --groups 1 3 32 --rounds 11 --sample-ms 30
```

Use hashes from your own binaries if a different toolchain or build path changes
them. The bank is `fir_three_level_modern_v1_bottomup_cap401.hdf`; profiles are
`ladder_profiles_H1.npz`. The main comparison uses the existing fixed cost table,
whose hash is in the artifact. Selection on a different calibrated machine may
retain ordinary order; that is an intended fallback.

To reproduce selectivity, use a disposable checkout of `702e6af8`, apply only
`selectivity-probe.patch`, and build with `CFLAGS=-DAP_GATE_ORDER_PROBE` plus the
normal Highway configuration. Run `tools/profile_cpu_ladder.py` with the same
bank/profiles, `--target AVX3 --runs 1 --segments 2 --q15 1`. Sum `ORDER_PROBE`
JSON lines on stderr and compare the final output hash with the unmodified build.
