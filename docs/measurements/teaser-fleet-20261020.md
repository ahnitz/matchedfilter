# Hardware comparison at revision 30486ecb

Measured October 20, 2026 (UTC), on `main` after the backend unification (stage U),
at revisions `4de7d2ec`–`30486ecb`: those differ only in error paths, tests and where
the Metal driver defines its peak model, and no timed code path changed between them.
This recalculates [the October 13 comparison](teaser-fleet-20261013.md); earlier
pages are kept for history. Every timing block is in the recorded JSON.

**One change of method.** Every report here ran from a fresh `MF_COST_FILE` per host
and device, so measured choices (layouts, chains, the Vulkan subgroup size) settle as
they do for a user with a cost file. Earlier pages ran without one. On Vulkan the
subgroup size is measured only where it can be kept, so without a cost file the Iris
Xe builds at its reported 32: full output then took 124.6 ms and peak-only 151.7 ms at
16 × 512, against 24.2 and 5.1 ms here (subgroup 8). Other machines are unaffected.

Entries marked **†** are carried over unchanged from an earlier JSON, with their
original date and revision, and are labelled as such in the figures and on the
interactive page:

- NVIDIA L40S (GPU, 16 × 512 and 512 × 512) from October 13 at `2b3cac13`, and the
  EPYC 9845 CPU of that node from October 3: the node is reached through a condor GPU
  job, which was not submitted for this page.
- NVIDIA A100 80GB and A40 from October 4 at `2a33e8f`: their login host did not
  accept this session's key.
- Xeon Platinum 8260 (sugwg-login2) from October 3: a login node, not used for
  benchmarks.
- Ryzen 9 5950X (gravity-dev1) from October 13 at `2b3cac13`: re-measured on
  October 20, but another user's jobs held every core (load ~20) and the CPU rows came
  out 6–21× slower than on October 13 (full output 343.8 ms, FFTW 588.4 ms); those
  reports are not used.

Entries marked **‡** are the Haswell node, a shared cluster node at load 29–42
throughout, as on earlier pages; its full-output and peak-only rows are indicative
only. Its environment no longer imports pyFFTW, so it has no FFT-only reference.

![CPU and GPU throughput, 16 data × 512 templates](../assets/teaser-fleet.svg)

[Machine-readable results, 16 × 512](teaser-fleet-20261020.json) and
[512 × 512](gpu-fleet-512x512-20261020.json) include hardware, backend,
software versions, CPU affinity, load averages, correctness checks, every
timing block, the gate chain each hierarchical row selected, and refinement
fractions. Bars show median throughput; whiskers show the timing-block
10th–90th percentiles, not statistical confidence intervals.

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
correlation reuses output storage; GPU calls include synchronization. All
reports come from `tools/teaser_fleet.py`.

## Environment

| Host | Devices | Measured (UTC) | Revision | Load | Python | Notes |
|---|---|---|---|---|---|---|
| gravity-dev2 | CPU, GPU | 2026-10-20 04:37–04:45 | `30486ecb` | 0.6–1.2 | 3.13.5 | |
| gravity-dev3 | CPU, GPU | 2026-10-20 03:46–04:00 | `4de7d2ec` | 0.0–1.1 | 3.13.15 | native library built on gravity-dev2 (same sources); no ROCm, so no rocFFT reference |
| gravity-dev4 | CPU, GPU | 2026-10-20 03:47–03:57 | `4de7d2ec` | 0.0–1.2 | 3.13.15 | native library built on gravity-dev2 (same sources); no rocFFT reference |
| empire-m2 | CPU, GPU | 2026-10-20 03:47–03:57 | `9226028c` | 1.8–2.4 | 3.13.3 | |
| haswell | CPU | 2026-10-20 03:58–04:14 | `30486ecb` | 29.6–33.3 | 3.11.0 | shared cluster node; no pyFFTW |

Hosts without a physical GPU (gravity-dev1, sugwg-login2, Haswell) have no GPU
rows; software rendering is excluded.

## 16 data × 512 templates (8,192 pairs)

Milliseconds per batch; smaller is faster. Hierarchical columns are at SNR 5.5.

| CPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Ryzen 9 5950X (CPU) † | 63.82 (FFTW) | 52.95 | 34.42 | 2.20 | 4.48 | 5.53 |
| Ryzen AI Max+ 395 (CPU) | 68.42 (FFTW) | 33.87 | 19.77 | 1.02 | 2.22 | 3.25 |
| Ryzen 5 5500U (CPU) | 88.20 (FFTW) | 74.66 | 49.55 | 3.46 | 7.25 | 11.42 |
| Core i5-13500H (CPU) | 45.63 (FFTW) | 56.04 | 36.02 | 2.08 | 3.73 | 6.66 |
| Apple M2 (CPU) | 251.75 (FFTW) | 68.79 | 57.84 | 3.22 | 5.38 | 7.41 |
| Xeon Platinum 8260 (CPU) † | unavailable | 127.20 | 78.89 | 6.68 | 12.36 | 14.87 |
| Xeon CPU E5-2698 v3 @ 2.30GHz (CPU) ‡ | unavailable | 217.90 | 109.43 | 6.03 | 12.74 | 25.19 |
| EPYC 9845 (CPU) † | unavailable | 41.96 | 29.64 | 2.52 | 4.67 | 5.48 |

| GPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Radeon 8060S (GPU) | 2.54 (rocFFT) | 1.48 | 0.40 | 0.13 | 0.15 | 0.16 |
| Radeon Graphics — Ryzen 5 5500U (GPU) | unavailable | 16.84 | 8.49 | 2.00 | 1.92 | 2.06 |
| Iris Xe Graphics (GPU) | unavailable | 24.22 | 5.13 | 0.82 | 1.05 | 1.67 |
| Apple M2 (GPU) | 12.11 (MLX) | 6.32 | 3.68 | 0.61 | 0.80 | 1.09 |
| NVIDIA L40S (GPU) † | 0.81 (cuFFT) | 0.41 | 0.22 | 0.09 | 0.15 | 0.15 |

At `fd=1e-3`, varying the SNR threshold:

| CPU | 5.0 | 5.5 | 5.75 | 6.0 | 6.5 |
|---|---:|---:|---:|---:|---:|
| Ryzen 9 5950X (CPU) † | 10.15 | 4.48 | 2.53 | 1.97 | 1.12 |
| Ryzen AI Max+ 395 (CPU) | 4.94 | 2.22 | 1.22 | 0.87 | 0.60 |
| Ryzen 5 5500U (CPU) | 16.57 | 7.25 | 4.03 | 2.84 | 1.55 |
| Core i5-13500H (CPU) | 9.27 | 3.73 | 2.36 | 1.76 | 1.02 |
| Apple M2 (CPU) | 11.37 | 5.38 | 3.57 | 2.85 | 1.65 |
| Xeon Platinum 8260 (CPU) † | 22.35 | 12.36 | 10.12 | 6.62 | 4.76 |
| Xeon CPU E5-2698 v3 @ 2.30GHz (CPU) ‡ | 31.58 | 12.74 | 7.01 | 5.16 | 4.63 |
| EPYC 9845 (CPU) † | 7.59 | 4.67 | 3.13 | 2.34 | 1.56 |

| GPU | 5.0 | 5.5 | 5.75 | 6.0 | 6.5 |
|---|---:|---:|---:|---:|---:|
| Radeon 8060S (GPU) | 0.20 | 0.15 | 0.14 | 0.13 | 0.12 |
| Radeon Graphics — Ryzen 5 5500U (GPU) | 2.81 | 1.92 | 1.85 | 1.67 | 0.67 |
| Iris Xe Graphics (GPU) | 2.09 | 1.05 | 0.92 | 0.86 | 0.58 |
| Apple M2 (GPU) | 1.30 | 0.80 | 0.64 | 0.59 | 0.47 |
| NVIDIA L40S (GPU) † | 0.17 | 0.15 | 0.14 | 0.09 | 0.09 |

## 512 data × 512 templates (262,144 pairs)

![CPU and GPU throughput, 512 data × 512 templates](../assets/gpu-fleet-512x512.svg)

The RENOIR and Iris Xe GPUs and the i5-13500H CPU are new at this size.

| CPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Ryzen AI Max+ 395 (CPU) | 2194.12 (FFTW) | 1075.82 | 646.77 | 44.80 | 89.43 | 118.11 |
| Apple M2 (CPU) | 8131.43 (FFTW) | 2201.46 | 1852.38 | 111.75 | 196.22 | 255.04 |
| Ryzen 9 5950X (CPU) † | 2034.42 (FFTW) | 1624.83 | 1088.13 | 83.69 | 159.88 | 201.14 |
| Ryzen 5 5500U (CPU) | 2837.37 (FFTW) | 2358.35 | 1572.04 | 113.73 | 238.00 | 391.78 |
| Xeon CPU E5-2698 v3 @ 2.30GHz (CPU) ‡ | unavailable | 7136.06 | 4167.79 | 243.02 | 441.84 | 784.28 |
| Core i5-13500H (CPU) | 1459.29 (FFTW) | 1862.81 | 1186.64 | 75.65 | 135.11 | 224.90 |

| GPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| NVIDIA A100 80GB PCIe (GPU) † | 10.41 (cuFFT) | 20.18 | 14.84 | 7.54 | 14.05 | 14.55 |
| NVIDIA L40S (GPU) † | 26.19 (cuFFT) | 12.16 | 6.02 | 1.18 | 1.78 | 1.98 |
| NVIDIA A40 (GPU) † | 30.68 (cuFFT) | 39.75 | 16.88 | 9.44 | 17.79 | 18.42 |
| Radeon 8060S (GPU) | 79.41 (rocFFT) | 10.78 | 10.38 | 1.37 | 2.00 | 2.39 |
| Apple M2 (GPU) | 370.88 (MLX) | 186.00 | 106.78 | 8.34 | 13.01 | 22.37 |
| Radeon Graphics — Ryzen 5 5500U (GPU) | unavailable | 233.31 | 233.92 | 32.98 | 36.34 | 42.45 |
| Iris Xe Graphics (GPU) | unavailable | 753.38 | 158.70 | 23.09 | 31.39 | 47.72 |

At `fd=1e-3`, varying the SNR threshold:

| CPU | 5.0 | 5.5 | 5.75 | 6.0 | 6.5 |
|---|---:|---:|---:|---:|---:|
| Ryzen AI Max+ 395 (CPU) | 178.30 | 89.43 | 52.91 | 34.59 | 23.67 |
| Apple M2 (CPU) | 413.24 | 196.22 | 126.48 | 94.49 | 59.41 |
| Ryzen 9 5950X (CPU) † | 355.67 | 159.88 | 99.28 | 67.34 | 43.03 |
| Ryzen 5 5500U (CPU) | 571.68 | 238.00 | 134.03 | 90.70 | 52.88 |
| Xeon CPU E5-2698 v3 @ 2.30GHz (CPU) ‡ | 1067.71 | 441.84 | 265.06 | 182.69 | 169.28 |
| Core i5-13500H (CPU) | 325.78 | 135.11 | 85.56 | 62.41 | 38.35 |

| GPU | 5.0 | 5.5 | 5.75 | 6.0 | 6.5 |
|---|---:|---:|---:|---:|---:|
| NVIDIA A100 80GB PCIe (GPU) † | 15.73 | 14.05 | 7.99 | 7.50 | 7.21 |
| NVIDIA L40S (GPU) † | 2.66 | 1.78 | 1.21 | 0.97 | 0.92 |
| NVIDIA A40 (GPU) † | 19.39 | 17.79 | 9.77 | 9.44 | 9.18 |
| Radeon 8060S (GPU) | 3.35 | 2.00 | 1.93 | 1.33 | 0.83 |
| Apple M2 (GPU) | 31.21 | 13.01 | 9.19 | 7.62 | 4.42 |
| Radeon Graphics — Ryzen 5 5500U (GPU) | 65.30 | 36.34 | 33.04 | 32.01 | 15.03 |
| Iris Xe Graphics (GPU) | 61.65 | 31.39 | 24.75 | 21.73 | 10.71 |

## Change since the previous measurement

Milliseconds per batch, previous → now, for the entries re-measured on both
dates (hierarchical columns at SNR 5.5). The baselines are the October 13 JSONs;
entries carried over there (gravity-dev3 GPU, gravity-dev4) compare with October 3
at `50597f3`. The Haswell node was loaded on both dates, so its changes are not
attributable to the library.

16 × 512:

| Hardware | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|
| Ryzen AI Max+ 395 (CPU) | 34.81 → 33.87 | 21.71 → 19.77 | 1.08 → 1.02 | 2.35 → 2.22 | 3.56 → 3.25 |
| Radeon 8060S (GPU) | 1.50 → 1.48 | 0.39 → 0.40 | 0.12 → 0.13 | 0.14 → 0.15 | 0.15 → 0.16 |
| Ryzen 5 5500U (CPU) | 74.21 → 74.66 | 50.74 → 49.55 | 3.69 → 3.46 | 7.16 → 7.25 | 11.37 → 11.42 |
| Radeon Graphics — Ryzen 5 5500U (GPU) | 15.92 → 16.84 | 10.19 → 8.49 | 1.79 → 2.00 | 2.58 → 1.92 | 3.18 → 2.06 |
| Core i5-13500H (CPU) | 55.88 → 56.04 | 35.36 → 36.02 | 4.66 → 2.08 | 5.62 → 3.73 | 8.16 → 6.66 |
| Iris Xe Graphics (GPU) | 23.59 → 24.22 | 9.86 → 5.13 | 2.00 → 0.82 | 3.30 → 1.05 | 4.11 → 1.67 |
| Apple M2 (CPU) | 69.65 → 68.79 | 58.46 → 57.84 | 3.26 → 3.22 | 5.46 → 5.38 | 7.55 → 7.41 |
| Apple M2 (GPU) | 6.32 → 6.32 | 3.68 → 3.68 | 0.63 → 0.61 | 0.82 → 0.80 | 1.04 → 1.09 |
| Xeon CPU E5-2698 v3 @ 2.30GHz (CPU) ‡ | 268.27 → 217.90 | 134.49 → 109.43 | 7.56 → 6.03 | 18.02 → 12.74 | 24.85 → 25.19 |

512 × 512:

| Hardware | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|
| Ryzen AI Max+ 395 (CPU) | 1119.53 → 1075.82 | 726.77 → 646.77 | 46.86 → 44.80 | 89.12 → 89.43 | 119.33 → 118.11 |
| Radeon 8060S (GPU) | 11.12 → 10.78 | 10.97 → 10.38 | 1.40 → 1.37 | 2.15 → 2.00 | 2.60 → 2.39 |
| Apple M2 (CPU) | 2221.52 → 2201.46 | 1867.55 → 1852.38 | 113.83 → 111.75 | 199.64 → 196.22 | 260.54 → 255.04 |
| Apple M2 (GPU) | 186.45 → 186.00 | 106.73 → 106.78 | 9.18 → 8.34 | 13.71 → 13.01 | 21.94 → 22.37 |
| Ryzen 5 5500U (CPU) | 2346.56 → 2358.35 | 1625.38 → 1572.04 | 121.05 → 113.73 | 243.25 → 238.00 | 395.42 → 391.78 |
| Xeon CPU E5-2698 v3 @ 2.30GHz (CPU) ‡ | 6553.96 → 7136.06 | 3730.78 → 4167.79 | 310.33 → 243.02 | 542.61 → 441.84 | 784.25 → 784.28 |

Rows slower than before, beyond their timing-block spread:

- Radeon 8060S, the 16 × 512 hierarchical calls (0.12–0.16 ms each): 4–11% slower on
  the same chains. A paired run of the October 13 code (`2b3cac13`) and this one, same
  timing script, alternating, put the steady call at 0.119–0.124 ms against
  0.127–0.130 ms: about 7 µs of host time per call. The 512 × 512 calls and the
  pipelined search are not slower (the stage U paired ladders; [performance
  status](../performance-status.md)), so it is a fixed per-call cost that only tiny
  calls show; where it is spent is not yet located.
- RENOIR GPU, full output at 16 × 512: 15.92 → 16.84 ms (against October 3); its
  peak-only calls are 17% faster.
- RENOIR GPU at `fd=1e-2` and the M2 GPU at `fd=1e-4` changed gate chain: the RENOIR
  locked `(1024)` where its other budgets run two-tier chains, the M2 `(1024, 2048)`
  instead of `(512, 1024)`. These are the chain trials' outcomes on this run; the
  same machines' other budgets are faster.

## Reproducing the charts

```bash
python tools/teaser_fleet.py --compare docs/measurements/teaser-fleet-20261020.json \
                             --out docs/assets/teaser-fleet.svg
python tools/teaser_fleet.py --compare docs/measurements/gpu-fleet-512x512-20261020.json \
                             --out docs/assets/gpu-fleet-512x512.svg
```

The README figure is drawn from the gravity-dev2 512 × 512 reports without
re-measuring:

```bash
python tools/teaser_figure.py --from-fleet dev2_cpu_512.json dev2_gpu_512.json \
                              --out docs/assets/teaser.svg
```

Each report was taken as

```bash
MF_COST_FILE=fresh.json python tools/teaser_fleet.py --device cpu|gpu --data 512|16 \
    --host HOST --cpu N --revision REV --out report.json
```
