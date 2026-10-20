# Hardware comparison at revision 4fd8b0d4

Measured October 20, 2026 (UTC), at revision `4fd8b0d4` on `main`: the code after the
backend unification (stage U) and the Vulkan binding-limit fix below. This recalculates
[the October 13 comparison](teaser-fleet-20261013.md); earlier pages are kept for
history. Every run's timing blocks are in the recorded JSON.

**A correction.** On Radeon GPUs (RADV: the 8060S and the RENOIR) a full correlation
whose output reached 4 GiB wrote nothing and returned normally: one Vulkan storage
binding spans less than 4 GiB (`maxStorageBufferRange`). Every 512 × 512 full-output row
for those GPUs on earlier pages timed that no-op (8060S: 11.12 ms on October 13, where
writing the 8.6 GB takes 47.7 ms at its bandwidth). `4fd8b0d4` splits such work, and this
page's numbers are the first correct ones. Iris Xe and Apple M2 wrote every pair before
the fix (checked at 4.29 and 8.59 GB); CUDA has no such limit.

## Method

Each host and device ran `tools/teaser_fleet.py` **three times, each run its own process
from its own fresh `MF_COST_FILE`** (a run's 512 × 512 and 16 × 512 reports share it), and
`teaser_fleet.py --merge` combined them: a row is the **median of the three runs'**
medians, its whiskers span every run's timing blocks, and each run's time and gate chain
are kept under `runs`. Within a run a row is the median of 9 timing blocks of at least
50 ms of back-to-back calls, after at least 0.8 s of warm-up. One run times one outcome of
the measured choices; across runs the same row moved by up to 2× where a chain trial
locked a different chain (RENOIR GPU) or where the host was loaded (Haswell), and on the
Iris Xe one run of three was 50–70% slower on most hierarchical rows with identical
choices. The median of three keeps such a run out of the tables; the spread stays in the
JSON.

**Every timed row is checked**, at the timed size, against numpy on sampled pairs: all
lags of full output, and for peak-only and hierarchical rows every reported peak's lag and
value (`teaser_figure._check_timed`). A wrong result fails the row instead of becoming a
bar; this check would have caught the no-op above. Every row on this page passed.

Earlier pages ran without a cost file, so measured choices that are kept only in one
fell back to their defaults. On Vulkan that is the subgroup size: without a cost file the
Iris Xe builds at its reported 32, and full-output and peak-only calls ran 5–30× slower
(124.6 and 151.7 ms at 16 × 512 against 24.3 and 5.1 ms here).

Entries marked **†** are carried over unchanged from an earlier JSON, with their
original date and revision, and are labelled as such in the figures and on the
interactive page:

- NVIDIA L40S (GPU) from October 13 at `2b3cac13`, and the EPYC 9845 CPU of that node
  from October 3: the node is reached through a condor GPU job, which was not submitted
  for this page. **Its 512 × 512 full-output row (12.16 ms) is from CUDA, which has no
  binding limit, and is plausible (706 GB/s).**
- NVIDIA A100 80GB and A40 from October 4 at `2a33e8f`: their login host did not
  accept this session's key.
- Xeon Platinum 8260 (sugwg-login2) from October 3: a login node, not used for
  benchmarks.
- Ryzen 9 5950X (gravity-dev1) from October 13 at `2b3cac13`: re-measured on
  October 20, but another user's jobs held every core (load ~20) and its rows came out
  6–21× slower (full output 343.8 ms, FFTW 588.4 ms at 16 × 512); not used.

Entries marked **‡** are the Haswell node, a shared cluster node at load 29–40
throughout; its runs differ by up to 2× and its rows are indicative only. Its
environment no longer imports pyFFTW, so it has no FFT-only reference.

![CPU and GPU throughput, 16 data × 512 templates](../assets/teaser-fleet.svg)

[Machine-readable results, 16 × 512](teaser-fleet-20261020.json) and
[512 × 512](gpu-fleet-512x512-20261020.json) include hardware, backend,
software versions, CPU affinity, load averages, correctness checks, every
run's timing blocks, the gate chain each hierarchical row selected in each run, and
refinement fractions. Bars show the median of the runs; whiskers show the 10th–90th
percentiles of all runs' timing blocks, not statistical confidence intervals.

## Workload and timing

Each call processes **16 or 512 data spectra × 512 templates × 4096 points**
with Gaussian noise and a full lag window, with the bank drawn from the
captured PyCBC reference profile (`tests/data/reference_profile_pycbc.npy`).
Hierarchical rows are recorded at SNR thresholds 5.0, 5.5, 5.75, 6.0 and
6.5; the static charts and the main tables show 5.5. These are warm public
`run()` calls, not `run_series()` or isolated kernel times. CPU calls use
one thread; Linux processes are pinned to one CPU (gravity-dev2, -dev3 and
-dev4 use CPU 2, Haswell CPU 50); macOS schedules its thread. Setup,
calibration, template preparation and input upload are excluded. Full
correlation reuses output storage; GPU calls include synchronization.

## Environment

| Host | Devices | Measured (UTC) | Load | Python | Notes |
|---|---|---|---|---|---|
| gravity-dev2 | CPU, GPU | 2026-10-20 05:24–05:49 | 0.3–1.4 | 3.13.5 | |
| gravity-dev3 | CPU, GPU | 2026-10-20 05:21–06:02 | 0.0–1.2 | 3.13.15 | native library built on gravity-dev2 (same sources); no ROCm, so no rocFFT reference |
| gravity-dev4 | CPU, GPU | 2026-10-20 05:21–05:54 | 0.1–1.2 | 3.13.15 | native library built on gravity-dev2 (same sources); no rocFFT reference |
| empire-m2 | CPU, GPU | 2026-10-20 05:22–05:52 | 2.0–4.8 | 3.13.3 | |
| haswell | CPU | 2026-10-20 05:24–06:11 | 28.8–40.4 | 3.11.0 | shared cluster node; no pyFFTW |

Hosts without a physical GPU (gravity-dev1, sugwg-login2, Haswell) have no GPU
rows; software rendering is excluded.

## 16 data × 512 templates (8,192 pairs)

Milliseconds per batch; smaller is faster. Hierarchical columns are at SNR 5.5.

| CPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Ryzen 9 5950X (CPU) † | 63.82 (FFTW) | 52.95 | 34.42 | 2.20 | 4.48 | 5.53 |
| Ryzen AI Max+ 395 (CPU) | 69.61 (FFTW) | 33.69 | 19.72 | 1.02 | 2.22 | 3.23 |
| Ryzen 5 5500U (CPU) | 88.61 (FFTW) | 73.11 | 48.98 | 3.49 | 7.13 | 8.77 |
| Core i5-13500H (CPU) | 45.13 (FFTW) | 55.37 | 35.50 | 2.04 | 3.62 | 6.57 |
| Apple M2 (CPU) | 251.54 (FFTW) | 68.79 | 57.74 | 3.20 | 5.35 | 7.39 |
| Xeon Platinum 8260 (CPU) † | unavailable | 127.20 | 78.89 | 6.68 | 12.36 | 14.87 |
| Xeon CPU E5-2698 v3 @ 2.30GHz (CPU) ‡ | unavailable | 199.13 | 111.25 | 6.28 | 19.42 | 23.17 |
| EPYC 9845 (CPU) † | unavailable | 41.96 | 29.64 | 2.52 | 4.67 | 5.48 |

| GPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Radeon 8060S (GPU) | 2.54 (rocFFT) | 1.48 | 0.40 | 0.13 | 0.15 | 0.16 |
| Radeon Graphics — Ryzen 5 5500U (GPU) | unavailable | 18.38 | 8.21 | 1.81 | 1.88 | 2.15 |
| Iris Xe Graphics (GPU) | unavailable | 24.26 | 5.08 | 0.69 | 1.07 | 1.61 |
| Apple M2 (GPU) | 11.92 (MLX) | 6.33 | 3.68 | 0.60 | 0.79 | 1.07 |
| NVIDIA L40S (GPU) † | 0.81 (cuFFT) | 0.41 | 0.22 | 0.09 | 0.15 | 0.15 |

At `fd=1e-3`, varying the SNR threshold:

| CPU | 5.0 | 5.5 | 5.75 | 6.0 | 6.5 |
|---|---:|---:|---:|---:|---:|
| Ryzen 9 5950X (CPU) † | 10.15 | 4.48 | 2.53 | 1.97 | 1.12 |
| Ryzen AI Max+ 395 (CPU) | 4.85 | 2.22 | 1.24 | 0.86 | 0.59 |
| Ryzen 5 5500U (CPU) | 16.60 | 7.13 | 4.05 | 2.84 | 1.56 |
| Core i5-13500H (CPU) | 9.16 | 3.62 | 2.32 | 1.75 | 1.02 |
| Apple M2 (CPU) | 11.33 | 5.35 | 3.56 | 2.82 | 1.65 |
| Xeon Platinum 8260 (CPU) † | 22.35 | 12.36 | 10.12 | 6.62 | 4.76 |
| Xeon CPU E5-2698 v3 @ 2.30GHz (CPU) ‡ | 30.85 | 19.42 | 7.00 | 5.15 | 3.21 |
| EPYC 9845 (CPU) † | 7.59 | 4.67 | 3.13 | 2.34 | 1.56 |

| GPU | 5.0 | 5.5 | 5.75 | 6.0 | 6.5 |
|---|---:|---:|---:|---:|---:|
| Radeon 8060S (GPU) | 0.18 | 0.15 | 0.14 | 0.13 | 0.12 |
| Radeon Graphics — Ryzen 5 5500U (GPU) | 2.77 | 1.88 | 1.93 | 1.54 | 0.48 |
| Iris Xe Graphics (GPU) | 2.09 | 1.07 | 0.93 | 0.72 | 0.58 |
| Apple M2 (GPU) | 1.29 | 0.79 | 0.62 | 0.57 | 0.47 |
| NVIDIA L40S (GPU) † | 0.17 | 0.15 | 0.14 | 0.09 | 0.09 |

## 512 data × 512 templates (262,144 pairs)

![CPU and GPU throughput, 512 data × 512 templates](../assets/gpu-fleet-512x512.svg)

The RENOIR and Iris Xe GPUs and the i5-13500H CPU are new at this size.

| CPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Ryzen AI Max+ 395 (CPU) | 2198.67 (FFTW) | 1086.96 | 637.22 | 45.60 | 90.43 | 119.47 |
| Apple M2 (CPU) | 8133.99 (FFTW) | 2198.06 | 1851.29 | 111.74 | 196.17 | 255.85 |
| Ryzen 9 5950X (CPU) † | 2034.42 (FFTW) | 1624.83 | 1088.13 | 83.69 | 159.88 | 201.14 |
| Ryzen 5 5500U (CPU) | 2809.35 (FFTW) | 2352.72 | 1583.48 | 114.51 | 240.90 | 297.32 |
| Xeon CPU E5-2698 v3 @ 2.30GHz (CPU) ‡ | unavailable | 6868.63 | 3831.52 | 222.61 | 416.89 | 773.98 |
| Core i5-13500H (CPU) | 1451.63 (FFTW) | 1794.27 | 1166.41 | 73.92 | 132.19 | 220.20 |

| GPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| NVIDIA A100 80GB PCIe (GPU) † | 10.41 (cuFFT) | 20.18 | 14.84 | 7.54 | 14.05 | 14.55 |
| NVIDIA L40S (GPU) † | 26.19 (cuFFT) | 12.16 | 6.02 | 1.18 | 1.78 | 1.98 |
| NVIDIA A40 (GPU) † | 30.68 (cuFFT) | 39.75 | 16.88 | 9.44 | 17.79 | 18.42 |
| Radeon 8060S (GPU) | 79.26 (rocFFT) | 47.65 | 10.45 | 1.37 | 2.00 | 2.40 |
| Apple M2 (GPU) | 371.92 (MLX) | 186.67 | 106.90 | 8.49 | 13.29 | 22.38 |
| Radeon Graphics — Ryzen 5 5500U (GPU) | unavailable | 517.00 | 243.31 | 33.06 | 36.67 | 44.10 |
| Iris Xe Graphics (GPU) | unavailable | 753.69 | 156.60 | 19.81 | 31.13 | 47.61 |

At `fd=1e-3`, varying the SNR threshold:

| CPU | 5.0 | 5.5 | 5.75 | 6.0 | 6.5 |
|---|---:|---:|---:|---:|---:|
| Ryzen AI Max+ 395 (CPU) | 179.28 | 90.43 | 53.93 | 34.10 | 23.72 |
| Apple M2 (CPU) | 414.07 | 196.17 | 126.46 | 94.60 | 59.24 |
| Ryzen 9 5950X (CPU) † | 355.67 | 159.88 | 99.28 | 67.34 | 43.03 |
| Ryzen 5 5500U (CPU) | 576.89 | 240.90 | 135.05 | 90.91 | 52.90 |
| Xeon CPU E5-2698 v3 @ 2.30GHz (CPU) ‡ | 1099.66 | 416.89 | 264.71 | 182.53 | 136.12 |
| Core i5-13500H (CPU) | 318.05 | 132.19 | 84.53 | 61.35 | 37.82 |

| GPU | 5.0 | 5.5 | 5.75 | 6.0 | 6.5 |
|---|---:|---:|---:|---:|---:|
| NVIDIA A100 80GB PCIe (GPU) † | 15.73 | 14.05 | 7.99 | 7.50 | 7.21 |
| NVIDIA L40S (GPU) † | 2.66 | 1.78 | 1.21 | 0.97 | 0.92 |
| NVIDIA A40 (GPU) † | 19.39 | 17.79 | 9.77 | 9.44 | 9.18 |
| Radeon 8060S (GPU) | 3.35 | 2.00 | 1.81 | 1.32 | 0.81 |
| Apple M2 (GPU) | 31.41 | 13.29 | 9.34 | 7.77 | 4.52 |
| Radeon Graphics — Ryzen 5 5500U (GPU) | 63.86 | 36.67 | 33.08 | 32.04 | 10.53 |
| Iris Xe Graphics (GPU) | 61.74 | 31.13 | 24.55 | 17.98 | 11.25 |

## Change since the previous measurement

Milliseconds per batch, previous → now, for the entries re-measured on both
dates (hierarchical columns at SNR 5.5). The baselines are the October 13 JSONs
(single runs); entries carried over there (gravity-dev3 GPU, gravity-dev4) compare with
October 3 at `50597f3`. The Haswell node was loaded on both dates, so its changes are
not attributable to the library. **The Radeon 8060S 512 × 512 full-output change
(11.12 → 47.65 ms) is the correction above, not a slowdown.**

16 × 512:

| Hardware | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|
| Ryzen AI Max+ 395 (CPU) | 34.81 → 33.69 | 21.71 → 19.72 | 1.08 → 1.02 | 2.35 → 2.22 | 3.56 → 3.23 |
| Radeon 8060S (GPU) | 1.50 → 1.48 | 0.39 → 0.40 | 0.12 → 0.13 | 0.14 → 0.15 | 0.15 → 0.16 |
| Ryzen 5 5500U (CPU) | 74.21 → 73.11 | 50.74 → 48.98 | 3.69 → 3.49 | 7.16 → 7.13 | 11.37 → 8.77 |
| Radeon Graphics — Ryzen 5 5500U (GPU) | 15.92 → 18.38 | 10.19 → 8.21 | 1.79 → 1.81 | 2.58 → 1.88 | 3.18 → 2.15 |
| Core i5-13500H (CPU) | 55.88 → 55.37 | 35.36 → 35.50 | 4.66 → 2.04 | 5.62 → 3.62 | 8.16 → 6.57 |
| Iris Xe Graphics (GPU) | 23.59 → 24.26 | 9.86 → 5.08 | 2.00 → 0.69 | 3.30 → 1.07 | 4.11 → 1.61 |
| Apple M2 (CPU) | 69.65 → 68.79 | 58.46 → 57.74 | 3.26 → 3.20 | 5.46 → 5.35 | 7.55 → 7.39 |
| Apple M2 (GPU) | 6.32 → 6.33 | 3.68 → 3.68 | 0.63 → 0.60 | 0.82 → 0.79 | 1.04 → 1.07 |
| Xeon CPU E5-2698 v3 @ 2.30GHz (CPU) ‡ | 268.27 → 199.13 | 134.49 → 111.25 | 7.56 → 6.28 | 18.02 → 19.42 | 24.85 → 23.17 |

512 × 512:

| Hardware | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|
| Ryzen AI Max+ 395 (CPU) | 1119.53 → 1086.96 | 726.77 → 637.22 | 46.86 → 45.60 | 89.12 → 90.43 | 119.33 → 119.47 |
| Radeon 8060S (GPU) | 11.12 → 47.65 | 10.97 → 10.45 | 1.40 → 1.37 | 2.15 → 2.00 | 2.60 → 2.40 |
| Apple M2 (CPU) | 2221.52 → 2198.06 | 1867.55 → 1851.29 | 113.83 → 111.74 | 199.64 → 196.17 | 260.54 → 255.85 |
| Apple M2 (GPU) | 186.45 → 186.67 | 106.73 → 106.90 | 9.18 → 8.49 | 13.71 → 13.29 | 21.94 → 22.38 |
| Ryzen 5 5500U (CPU) | 2346.56 → 2352.72 | 1625.38 → 1583.48 | 121.05 → 114.51 | 243.25 → 240.90 | 395.42 → 297.32 |
| Xeon CPU E5-2698 v3 @ 2.30GHz (CPU) ‡ | 6553.96 → 6868.63 | 3730.78 → 3831.52 | 310.33 → 222.61 | 542.61 → 416.89 | 784.25 → 773.98 |

Rows slower than before, beyond their spread:

- Radeon 8060S, the 16 × 512 hierarchical calls (0.12–0.16 ms each): 4–11% slower on
  the same chains. A paired run of the October 13 code (`2b3cac13`) and this one, same
  timing script, alternating, put the steady call at 0.119–0.124 ms against
  0.127–0.130 ms: about 7 µs of host time per call. The 512 × 512 calls and the
  pipelined search are not slower (the stage U paired ladders; [performance
  status](../performance-status.md)), so it is a fixed per-call cost that only tiny
  calls show; where it is spent is not yet located.
- RENOIR GPU, full output at 16 × 512: 15.92 → 18.38 ms against a single October 3
  run; its own three runs here are 16.88, 18.38 and 18.42 ms with the same choices, so
  the difference is within this machine's run-to-run spread. Its peak-only calls are
  19% faster.

## Open: chain trials that lock a slower chain

On the RENOIR GPU some budgets locked different chains in different runs, up to 2× apart
at the same row: `fd=1e-2` at SNR 5.75 locked `(256, 512)` (16.0 ms at 512 × 512),
`(256, 2048)` (23.3 ms) and `(1024, 2048)` (31.9 ms) in the three runs. A trial that
picks a chain twice as slow is not a near-tie, so the trial's samples or their
conditions (this APU's clocks) mislead it. The medians above are from the runs as they
locked; the per-run chains are in the JSON.

## Reproducing the charts

```bash
python tools/teaser_fleet.py --compare docs/measurements/teaser-fleet-20261020.json \
                             --out docs/assets/teaser-fleet.svg
python tools/teaser_fleet.py --compare docs/measurements/gpu-fleet-512x512-20261020.json \
                             --out docs/assets/gpu-fleet-512x512.svg
```

Each report is three runs merged; one run is

```bash
MF_COST_FILE=fresh_run_k.json python tools/teaser_fleet.py --device cpu|gpu --data 512|16 \
    --host HOST --cpu N --revision REV --out run_k.json
python tools/teaser_fleet.py --merge run_1.json run_2.json run_3.json --out report.json
```

The README figure is drawn from the gravity-dev2 512 × 512 reports without
re-measuring:

```bash
python tools/teaser_figure.py --from-fleet dev2_cpu_512.json dev2_gpu_512.json \
                              --out docs/assets/teaser.svg
```
