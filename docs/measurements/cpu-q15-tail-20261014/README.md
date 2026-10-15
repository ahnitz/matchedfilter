# Q15 tail-packing measurements, 2026-10-14–15

The final build reduces Q15 time **4.3%**, fine-stage time **2.1%**, and whole-segment
time **1.8%** on the representative AVX3 ladder, with identical outputs. Its native
SHA-256 is `b7fc2583ceea69e842eff7e35b25e0c9e17f77c72ebeb37f2e5164cadd71ede7`.
It isolates tail scheduling and keeps ordinary data preparation in its original
position and inlined. Earlier prototypes below are separate experiments.

All timed runs used CPU 4 on an AMD Ryzen AI Max+ 395 (Zen 5), with other agents'
CPU jobs idle. Final checks completed on 2026-10-15 in America/New_York. No GPU
or ARM performance was tested. Baseline is commit `b3c1b022`, native SHA-256
`ce7076733a62db4c115c9ce4572950b5460e19a30cc317d2eeb19e3dae6c2d0f`.

## Final evidence

- [final-ladder-24seg-baab.json](final-ladder-24seg-baab.json): four fresh processes
  in candidate, baseline, baseline, candidate order, 24 segments each: one warm,
  23 steady. Includes exact commands, configuration, build/input/output hashes,
  per-process timings, survivor counts and observed plans.
- [final-screen-series-matrix.json](final-screen-series-matrix.json): 240 cases
  with raw alternating samples, digests, native hashes, affinity and survivor
  counts. Eight template counts, five groups, two paths and three ISAs; seven
  rounds at about 20 ms per build/sample. All output comparisons pass.
- [final-sse4-reversed.json](final-sse4-reversed.json): eight SSE4 series controls,
  15 rounds at about 30 ms per sample, with build arguments reversed. Invert its
  raw `speedup` to express baseline time / final time.
- [final-avx3-outliers.json](final-avx3-outliers.json) and
  [final-sse4-outlier.json](final-sse4-outlier.json): fresh-process reversed-position
  repeats of slower matrix cases, 15 rounds at about 50 ms per sample. These add
  `final_speedup`, the reciprocal of the raw harness ratio.
- [final-sse4-aa.json](final-sse4-aa.json): identical-baseline control for 162
  templates/group 4. [final-sse4-confirm.json](final-sse4-confirm.json) repeats
  that case with baseline/final arguments in normal order. Both use 15 rounds
  at about 50 ms per sample.
- [exactness-final.json](exactness-final.json): commands, hashes and digests for
  143,360 screen and 288 hierarchical comparisons across AVX3/AVX2/SSE4. All match.
- [ladder_builds.py](ladder_builds.py): portable fresh-process ladder driver.
  Large full process reports are not duplicated here; summaries retain their
  original local paths as provenance.

The synthetic series matrix uses `N=2048`, chain `(256,512,1024)`, 32 overlapping
complex blocks, thresholds `(4.1,4.76,5.48)`, and one injected peak in the final
template. Direct screen cases use band 256, threshold 4.1, and the requested group
as the number of data rows. The production screen without diagnostic statistics
is timed; pass masks and statistics are checked outside timing. Series peaks and
counts must match exactly. Timings exclude setup and warm quantization.

## Final real-bank ladder

The workload is cap401 top 4 with matching H1 profiles: 4,698 fine templates in
27 initial fine plans, two detectors, 512-second input segments at 2048 Hz, and
376 seconds analyzed per segment. It fixes `N=2048`, chain `(256,512,1024)`,
threshold 6, false-dismissal budget 0.001, Q15 enabled, and autotuning disabled.
Seed 1 supplies deterministic synthetic input. This is an API workload using a
real bank and profiles, not a full PyCBC production-job timing.

| Stage | Baseline → final, ms/segment | Less time |
|---|---:|---:|
| Q15 | 136.687 → 130.749 | 4.3% |
| Fine | 295.241 → 288.938 | 2.1% |
| Whole segment | 359.926 → 353.458 | 1.8% |

Each cell averages the two processes for that build after excluding each warm
segment. Baseline fine means are 295.025 and 295.457 ms; final means are 288.908
and 288.968 ms. All four output hashes and native stage counts match. The fixed
cost file's hash is unchanged before/after the comparison.

## Final controls and uncertainty

At AVX3 group 32, the six targeted tails improve 1.107–1.204x in the direct screen
and 1.039–1.065x in full synthetic series calls. AVX2/SSE4 series matrix medians
are 1.002x/0.998x. Several-percent differences in individual small-group cases
shift between fresh processes; those raw results are retained.

The matrix's slow AVX3 controls, 80/group 2, 131/group 2, and 128/group 3, measured
0.964x, 0.970x and 0.979x. Their reversed repeats measured 1.008x, 1.000x and
1.028x, while three other repeated controls measured 0.975–0.980x. SSE4
162/group 4 measured 0.980x, 0.979x and 1.003x across the matrix, reversed repeat
and normal-order confirmation. Two identical-baseline workers measured 0.999x.
The eight-case reversed SSE4 control ranged 0.988–1.008x, with mixed signs.

These data support the representative ladder gain and removal of the prototype's
broad SSE4 regression. They do not prove unchanged performance for every fallback
shape. No narrow-ISA speedup is claimed. Few process replicates are not confidence
intervals, and results do not generalize automatically to other CPU families.

## Rejected and intermediate prototypes

The native hash `d34eeb724467379ace31d78b108c8a9f8bc3cd9c6c8fceb1127d62213aa3e1bf`
identifies a rejected prototype with a larger scheduling loop. Its targeted AVX3
gain and ladder improvement were outweighed by a repeated 1–4% SSE4 series
slowdown, including aligned controls. Retained files:

- [screen-series-matrix.json](screen-series-matrix.json): initial 240-case matrix.
- [ladder-8seg-abba.json](ladder-8seg-abba.json): 8 segments/process, ABBA.
- [ladder-24seg-baab.json](ladder-24seg-baab.json): 24 segments/process, BAAB.
- [sse4-reversed.json](sse4-reversed.json): reversed-position confirmation, all
  eight cases slower (0.963–0.987x baseline/prototype speedup).

An intermediate helper-isolation build, hash
`81da5fb5b0ddea827a24ebb115883b42b829f2b9d82d68e76e55407a20f82553`, reduced the
SSE4 shift to 0.991–0.996x but retained bulk data preparation. Its raw samples
are in [isolated-sse4-control.json](isolated-sse4-control.json). Restoring ordinary
preparation placement and explicit inlining produced the final build.

**Measurements from different binaries or segment counts are not pooled.**

## Reproduction

Use separately built, immutable package directories containing `matchedfilter`
and its native extension. The external bank is
`fir_three_level_modern_v1_bottomup_cap401.hdf`; profiles are `ladder_profiles_H1.npz`.
Run from the repository root, on an otherwise idle physical core.

```sh
taskset -c 4 python tools/bench_q15_tails.py BASELINE/python FINAL/python \
  --output matrix.json --isas AVX3 AVX2 SSE4 --rounds 7 --sample-ms 20

python docs/measurements/cpu-q15-tail-20261014/ladder_builds.py \
  --baseline BASELINE/python --candidate FINAL/python \
  --candidate-sha b7fc2583ceea69e842eff7e35b25e0c9e17f77c72ebeb37f2e5164cadd71ede7 \
  --bank BANK.hdf --profiles PROFILES.npz --cost-file COSTS.json \
  --harness tools/profile_cpu_ladder.py --cpu 4 --segments 24 --order BAAB \
  --output-dir ladder-24

taskset -c 4 python tools/bench_q15_tails.py FINAL/python BASELINE/python \
  --output sse4-reversed.json --isas SSE4 --kinds series \
  --templates 80 128 193 254 --groups 4 32 --rounds 15 --sample-ms 30
```

The last command intentionally reverses the build arguments; invert the harness
ratio. `--verify-only` runs untimed matrix comparisons. The ladder driver pins
the known baseline hash by default; `--dry-run` prints commands without executing.
Use the hash of your own rebuilt final binary if it differs because of toolchain
or build-path differences. Synthetic tail gains alone are insufficient for
acceptance; compare the representative workload and retained fallback controls.
