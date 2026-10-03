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
| Ryzen 9 5950X | 63.96 | 51.71 | 34.37 | 3.82 | 4.95 | 7.73 |
| Ryzen AI Max+ 395 | 91.13 | 43.24 | 24.66 | 1.95 | 4.31 | 6.31 |
| Ryzen 5 5500U | 88.22 | 75.71 | 51.67 | 6.14 | 8.66 | 14.33 |
| Core i5-13500H | 44.57 | 55.88 | 35.36 | 4.66 | 5.62 | 8.16 |
| Apple M2 | 252.86 | 68.74 | 57.78 | 6.19 | 8.14 | 12.64 |
| Xeon Platinum 8260 (VM) | unavailable | 127.20 | 78.89 | 6.68 | 12.36 | 14.87 |
| Xeon E5-2698 v3 (Haswell) | unavailable | 199.11 | 120.00 | 18.26 | 18.76 | 28.88 |

Hierarchical columns are at SNR 5.5. At `fd=1e-3`, varying the threshold:

| CPU | 5.0 | 5.5 | 5.75 | 6.0 | 6.5 |
|---|---:|---:|---:|---:|---:|
| Ryzen 9 5950X | 12.08 | 4.95 | 4.65 | 3.69 | 1.91 |
| Ryzen AI Max+ 395 | 8.17 | 4.31 | 3.57 | 1.73 | 1.13 |
| Ryzen 5 5500U | 23.80 | 8.66 | 6.23 | 5.82 | 3.00 |
| Core i5-13500H | 10.79 | 5.62 | 3.85 | 4.50 | 3.18 |
| Apple M2 | 18.46 | 8.14 | 7.49 | 6.07 | 3.35 |
| Xeon Platinum 8260 (VM) | 22.35 | 12.36 | 10.12 | 6.62 | 4.76 |
| Xeon E5-2698 v3 (Haswell) | 46.56 | 18.76 | 15.77 | 14.93 | 7.68 |

## GPU timings

| GPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Radeon 8060S (RADV GFX1151) | 2.60 | 1.53 | 0.78 | 0.21 | 0.25 | 0.28 |
| Radeon integrated, 5500U | unavailable | 15.92 | 10.19 | 1.79 | 2.58 | 3.18 |
| Iris Xe, Core i5-13500H | unavailable | 23.59 | 9.86 | 2.00 | 3.30 | 4.11 |
| M2, 10 GPU cores | 11.72 | 6.32 | 3.94 | 1.44 | 2.80 | 3.92 |

The Ryzen 9 5950X, the Xeon guest and the Haswell node expose no physical
GPU; software rendering is excluded. rocFFT is unavailable on gravity-dev3, and no FFT-only
reference is available on Iris Xe.

## What changed since September 28 (`eecb43c`)

Same reference profile and same workload on both dates, highlighting the impact
of the first-principles table-free candidate selection, AVX-512 register-matched
autotuning, and the autotune fixture isolation fix:

1. **Strict FDR Budget Monotonicity ($T(\text{FDR } 0.01) < T(\text{FDR } 0.001) < T(\text{FDR } 0.0001)$):**
   - In prior measurements, FDR 0.01 was slower than FDR 0.001 on several nodes because validation fixtures (6 pairs with injected signal) polluted the empirical autotuner cache with a fine coarse-cascade trial, causing the 8,192-pair production benchmark to lock into an over-segmented `(128, 512, 8)` band whose low gate triggered excessive refinement in noise.
   - Keying `_autotune_cache_key` on batch size / `pairs` and clearing the autotuner cache after validation completely resolved this anomaly: at headline SNR 5.5, FDR 0.01 is now strictly faster than FDR 0.001 across all 7 machines and all devices (e.g., Ryzen AI Max+ 395 CPU runs at 1.95 ms @ 0.01 vs 4.31 ms @ 0.001; Ryzen 9 5950X runs at 3.82 ms @ 0.01 vs 4.95 ms @ 0.001).

2. **Haswell (Xeon E5-2698 v3) gains dramatically across all filter modes:**
   - Full output: 303.35 ms → **199.11 ms** (+34.4% speedup)
   - Peak only: 132.75 ms → **120.00 ms** (+9.6% speedup)
   - Hierarchical 0.01 @ SNR 5.5: 39.48 ms → **18.26 ms** (**2.16x faster, +53.7% speedup**)
   - Hierarchical 0.001 @ SNR 5.5: 68.50 ms → **18.76 ms** (**3.65x faster, +72.6% speedup**)
   - Hierarchical 0.001 @ SNR 5.75: 66.26 ms → **15.77 ms** (**4.20x faster, +76.2% speedup**)
   - Hierarchical 0.0001 @ SNR 5.5: 47.75 ms → **28.88 ms** (+39.5% speedup)
   - Hierarchical 0.001 @ SNR 6.5: 18.02 ms → **7.68 ms** (**2.35x faster, +57.4% speedup**)

3. **Iris Xe GPU (Intel Core i5-13500H) resolves refinement bottleneck:**
   - Hierarchical 0.01 @ SNR 5.5: 5.49 ms → **2.00 ms** (**2.75x faster, +63.6% speedup**)
   - Hierarchical 0.001 @ SNR 5.5: 23.01 ms → **3.30 ms** (**7.0x faster, +85.7% speedup**)
   - Hierarchical 0.001 @ SNR 5.75: 24.85 ms → **2.27 ms** (**10.9x faster, +90.9% speedup**)
   - Hierarchical 0.0001 @ SNR 5.5: 23.54 ms → **4.11 ms** (**5.7x faster, +82.5% speedup**)

4. **Substantial gains across modern laptop & desktop CPUs at headline SNR 5.5 (fd=1e-3):**
   - Apple M2 CPU: 13.17 ms → **8.14 ms** (+38.2% speedup)
   - Ryzen 5 5500U: 12.04 ms → **8.66 ms** (+28.1% speedup)
   - Ryzen 9 5950X: 7.04 ms → **4.95 ms** (+29.7% speedup)
   - Core i5-13500H CPU: 6.13 ms → **5.62 ms** (+8.3% speedup)

5. **Cluster VM Full Output throughput:**
   - Xeon Platinum 8260 VM: Full output 155.19 ms → **127.20 ms** (+18.0% faster)

## Reproducing the chart

To regenerate the figure from the recorded data:

```bash
python tools/teaser_fleet.py --compare docs/measurements/teaser-fleet-20261003.json \
                             --out docs/assets/teaser-fleet.svg
```
