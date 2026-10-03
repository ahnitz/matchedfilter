# Seven-machine teaser comparison

Measured October 3, 2026, at library revision `50597f3` (current `main`),
which introduces first-principles table-free candidate selection, AVX-512
register-matched autotuning, and 32-way template batching. This recalculates
[the September 28 comparison](teaser-fleet-20260928.md); earlier pages are
kept for history. All timing blocks are preserved in the recorded JSON.

![CPU and GPU throughput on seven machines](../assets/teaser-fleet.svg)

[Machine-readable results](teaser-fleet-20261003.json) include hardware,
backend, software versions, CPU affinity, load averages, correctness checks,
every timing block, automatic hierarchical configurations, and refinement
fractions. Bars show median throughput; whiskers show the timing-block
10th–90th percentiles, not statistical confidence intervals.

## Workload and timing

Each call processes **16 data spectra × 512 templates × 4096 points** with
Gaussian noise and a full lag window.

**The bank is drawn from the captured PyCBC reference profile**
(`tests/data/reference_profile_pycbc.npy`, the file the reference tests use).

**Hierarchical rows are recorded at five SNR thresholds** -- 5.0, 5.5, 5.75,
6.0 and 6.5. The static chart above shows 5.5. On the interactive
[hardware comparison page](https://ahnitz.github.io/matchedfilter/comparison.html)
the threshold and the FDR budget sit together in one Hierarchical screening
box, and both are multi-select: a series there is one (budget, threshold)
pair, so several thresholds can be compared side by side, shaded within each
budget's colour. The threshold is not a detail: a higher one admits a higher
coarse gate, so fewer pairs survive to refinement. These are warm
public `run()` calls, not `run_series()` or isolated kernel times. CPU calls
use one thread. Linux processes are pinned to CPU 0, except gravity-dev2 uses
CPU 2; macOS schedules its thread. Setup, calibration, template preparation,
and input upload are excluded. Full correlation reuses output storage; GPU
calls include synchronization. After 0.5 s of warmup each mode records nine
blocks of at least 50 ms, and the reported median uses all collected blocks.

## CPU timings

Milliseconds per batch; smaller is faster.

| CPU | FFTW | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Ryzen 9 5950X | 64.44 | 50.97 | 33.99 | 8.76 | 5.11 | 7.70 |
| Ryzen AI Max+ 395 | 69.54 | 35.25 | 21.67 | 7.53 | 3.61 | 4.51 |
| Ryzen 5 5500U | 88.00 | 74.72 | 50.97 | 12.42 | 8.46 | 14.22 |
| Core i5-13500H | 44.87 | 56.09 | 34.07 | 12.80 | 5.66 | 8.02 |
| Apple M2 | 253.83 | 69.19 | 58.29 | 10.44 | 8.37 | 12.98 |
| Xeon Platinum 8260 (VM) | 219.57 | 128.85 | 79.64 | 12.62 | 11.54 | 15.14 |
| Xeon E5-2698 v3 (Haswell) | 178.90 | 222.95 | 121.68 | 39.48 | 19.14 | 31.22 |

Hierarchical columns are at SNR 5.5. At `fd=1e-3`, varying the threshold:

| CPU | 5.0 | 5.5 | 5.75 | 6.0 | 6.5 |
|---|---:|---:|---:|---:|---:|
| Ryzen 9 5950X | 12.59 | 5.11 | 4.65 | 3.72 | 1.93 |
| Ryzen AI Max+ 395 | 6.22 | 3.61 | 2.53 | 1.80 | 1.16 |
| Ryzen 5 5500U | 23.56 | 8.46 | 6.08 | 5.79 | 2.98 |
| Core i5-13500H | 10.74 | 5.66 | 4.53 | 4.54 | 3.15 |
| Apple M2 | 18.48 | 8.37 | 7.72 | 6.08 | 3.36 |
| Xeon Platinum 8260 (VM) | 22.40 | 11.54 | 10.48 | 6.54 | 4.46 |
| Xeon E5-2698 v3 (Haswell) | 69.36 | 19.14 | 15.22 | 14.52 | 7.52 |

## GPU timings

| GPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Radeon 8060S (RADV GFX1151) | 2.66 | 1.56 | 0.72 | 0.41 | 0.23 | 0.27 |
| Radeon integrated, 5500U | unavailable | 15.93 | 10.21 | 2.69 | 1.67 | 3.48 |
| Iris Xe, Core i5-13500H | unavailable | 23.69 | 9.76 | 2.06 | 3.32 | 4.18 |
| M2, 10 GPU cores | 11.70 | 6.24 | 3.94 | 1.44 | 2.79 | 3.91 |

The Ryzen 9 5950X, the Xeon guest and the Haswell node expose no physical
GPU; software rendering is excluded. rocFFT is unavailable on gravity-dev3, and no FFT-only
reference is available on Iris Xe.

## What changed since September 28 (`eecb43c`)

Same reference profile and same workload on both dates, highlighting the impact
of the first-principles table-free candidate selection and AVX-512 register-matched
autotuning:

1. **Haswell (Xeon E5-2698 v3) gains dramatically across all filter modes:**
   - Full output: 303.35 ms → **222.95 ms** (+26.5% speedup)
   - Peak only: 132.75 ms → **121.68 ms** (+8.3% speedup)
   - Hierarchical 0.001 @ SNR 5.5: 68.50 ms → **19.14 ms** (**3.58x faster, +72.1% speedup**)
   - Hierarchical 0.001 @ SNR 5.75: 66.26 ms → **15.22 ms** (**4.35x faster, +77.0% speedup**)
   - Hierarchical 0.0001 @ SNR 5.5: 47.75 ms → **31.22 ms** (+34.6% speedup)
   - Hierarchical 0.001 @ SNR 6.5: 18.02 ms → **7.52 ms** (**2.4x faster, +58.3% speedup**)

2. **Iris Xe GPU (Intel Core i5-13500H) resolves refinement bottleneck:**
   - Hierarchical 0.001 @ SNR 5.5: 23.01 ms → **3.32 ms** (**6.9x faster, +85.6% speedup**)
   - Hierarchical 0.001 @ SNR 5.75: 24.85 ms → **2.27 ms** (**10.9x faster, +90.9% speedup**)
   - Hierarchical 0.0001 @ SNR 5.5: 23.54 ms → **4.18 ms** (**5.6x faster, +82.2% speedup**)
   - Hierarchical 0.01 @ SNR 5.5: 5.49 ms → **2.06 ms** (**2.7x faster, +62.6% speedup**)

3. **Substantial gains across modern laptop & desktop CPUs at headline SNR 5.5 (fd=1e-3):**
   - Apple M2 CPU: 13.17 ms → **8.37 ms** (+36.4% speedup)
   - Ryzen 5 5500U: 12.04 ms → **8.46 ms** (+29.8% speedup)
   - Ryzen 9 5950X: 7.04 ms → **5.11 ms** (+27.5% speedup)
   - Core i5-13500H CPU: 6.13 ms → **5.66 ms** (+7.8% speedup)

4. **Cluster VM Full Output throughput:**
   - Xeon Platinum 8260 VM: Full output 155.19 ms → **128.85 ms** (+17.0% faster)

## Reproducing the chart

To regenerate the figure from the recorded data:

```bash
python tools/teaser_fleet.py --compare docs/measurements/teaser-fleet-20261003.json \
                             --out docs/assets/teaser-fleet.svg
```
