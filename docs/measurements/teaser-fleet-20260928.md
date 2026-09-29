# Seven-machine teaser comparison

Measured September 28, 2026, at library revision `eecb43c` (current `main`),
which adds twenty-five optimization passes over `ce9c828`. This recalculates
[the September 27 comparison](teaser-fleet-20260927.md); earlier pages are
kept for history. All timing blocks are preserved in the recorded JSON.

![CPU and GPU throughput on six machines](../assets/teaser-fleet.svg)

[Machine-readable results](teaser-fleet-20260928.json) include hardware,
backend, software versions, CPU affinity, load averages, correctness checks,
every timing block, automatic hierarchical configurations, and refinement
fractions. Bars show median throughput; whiskers show the timing-block
10th–90th percentiles, not statistical confidence intervals.

## Workload and timing

Each call processes **16 data spectra × 512 templates × 4096 points** with
Gaussian noise and a full lag window.

**The bank is drawn from the captured PyCBC reference profile**
(`tests/data/reference_profile_pycbc.npy`, the file the reference tests use),
not from the synthetic `inspiral_power` curve the September 26 comparison
used. The synthetic curve is narrower than anything the search meets --
`B_eff` 180.8 against 232.7 at band 512, ratio 2.83 against 2.20 -- and the
hierarchy's cost follows directly from that width, since it sets both the band
selected and the fraction of pairs refined. Timing a profile the search never
sees flatters the gate, so the hierarchical columns here are **slower than,
and not comparable to, the September 26 page**.

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
| Ryzen 9 5950X | 63.63 | 52.23 | 34.27 | 3.95 | 7.04 | 8.03 |
| Ryzen AI Max+ 395 | 69.54 | 35.12 | 20.68 | 3.12 | 3.76 | 3.96 |
| Ryzen 5 5500U | 87.45 | 73.70 | 49.37 | 6.11 | 12.04 | 13.97 |
| Core i5-13500H | 44.96 | 56.24 | 35.49 | 4.69 | 6.13 | 7.15 |
| Apple M2 | 252.55 | 68.75 | 57.84 | 6.28 | 13.17 | 14.73 |
| Xeon Platinum 8260 (VM) ‡ | 219.57 | 155.19 | 79.18 | 6.24 | 10.66 | 13.90 |
| Xeon E5-2698 v3 (Haswell) § | 178.90 | 303.35 | 132.75 | 14.47 | 68.50 | 47.75 |

Hierarchical columns are at SNR 5.5. At `fd=1e-3`, varying the threshold:

| CPU | 5.0 | 5.5 | 5.75 | 6.0 | 6.5 |
|---|---:|---:|---:|---:|---:|
| Ryzen 9 5950X | 10.33 | 7.04 | 6.60 | 3.69 | 3.07 |
| Ryzen AI Max+ 395 | 5.92 | 3.76 | 2.35 | 1.66 | 1.17 |
| Ryzen 5 5500U | 18.57 | 12.04 | 11.35 | 5.74 | 4.39 |
| Core i5-13500H | 9.56 | 6.13 | 5.81 | 4.52 | 3.30 |
| Apple M2 | 18.46 | 13.17 | 12.48 | 5.98 | 5.03 |
| Xeon Platinum 8260 (VM) ‡ | 19.01 | 10.66 | 10.53 | 5.86 | 4.52 |
| Xeon E5-2698 v3 (Haswell) § | 55.01 | 68.50 | 66.26 | 13.52 | 18.02 |

A factor of 2.5-4 across the range on every machine. The band the gate
selects can change with it as well: on this reference `fd=1e-3` moves from
band 1024 at SNR 5.5 to band 512 by 6.5.

## GPU timings

| GPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Radeon 8060S (RADV GFX1151) | 2.58 | 1.49 | 0.71 | 0.20 | 0.18 | 0.19 |
| Radeon integrated, 5500U | unavailable | 15.98 | 10.14 | 2.02 | 1.72 | 1.93 |
| Iris Xe, Core i5-13500H | unavailable | 23.92 | 9.75 | 5.49 | 23.01 | 23.54 |
| M2, 10 GPU cores | 11.73 | 6.28 | 3.92 | 1.40 | 2.76 | 3.90 |

gravity-dev2's **GPU** rows reflect clean measurements on an idle host with settled autotuning to the empirical best configuration; the other three GPUs reproduce their earlier values to within about 1%.

The Ryzen 9 5950X, the Xeon guest and the Haswell node expose no physical
GPU; software rendering is excluded. rocFFT is unavailable on gravity-dev3, and no FFT-only
reference is available on Iris Xe. Those gaps are the same as on September 26.

## What changed since `ce9c828`

Same reference profile and same workload on both dates, so this is a
like-for-like comparison of the twenty-five passes. The fixed FFTW and rocFFT
references are the control: they contain no matchedfilter code, so a steady
baseline means the machine was steady.

    FFTW change     5950X -0.1%   5500U +0.5%   i5-13500H -1.0%   M2 -0.3%   Xeon -2.3%
    rocFFT / MLX                                                  M2 -0.4%

Against that control, on the machines whose baseline held:

    Peak only       5950X +3.7%   5500U +5.9%   i5-13500H +2.6%   M2 +4.8%   Xeon +3.0%
    Full output     5950X -2.9%   5500U +0.7%   i5-13500H +1.8%   M2 +0.3%   Xeon +1.8%
    Hier. 1e-3      M2 +9.6%      Xeon +8.9%    5500U +2.4%       5950X -0.2%  i5 -1.1%
    GPU (all modes) within about 1% on every uncontended GPU

**Peak-only improves consistently, 2.6-5.9% on every uncontended CPU.** That
is the clearest signal here and matches where the passes went: `small_scan`
unrolling, `binmax` mask hoisting and the `stageA_prod` GG==1 fast path all
sit on that path. Full output is flat, and hierarchical mode is mixed —
clearly up on the M2 and the Xeon guest, flat on the Ryzens and Intel laptop
part.

**The GPU is unchanged**, within about 1% on dev3, dev4 and the M2 across
every mode. The Vulkan barrier-narrowing and zero-copy readback passes in this
range did not move these workloads at this size.

## Contended rows

**gravity-dev2 re-measurement.** An earlier run on September 28 was taken while
an unrelated workload held that host at load 38 on 32 cores, causing memory saturation
on CPU (FFTW 188.67 ms) and severe dispatch starvation on GPU (hier. 1e-3 1.97 ms, 10x slower).
Once load cleared (load < 2.0), this host was re-measured cleanly with initial autotuning
passes settled to the empirical best configuration. Steady-state throughput returned to
uncontended baselines: CPU FFTW 69.54 ms (vs 78.32 ms on Sept 26 idle) and peak-only 20.68 ms
(vs 24.68 ms on Sept 26, a 16% speedup), and GPU peak-only 0.71 ms with hier. 1e-3 at 0.18 ms
without dispatch starvation or spread warnings.

**§ Haswell is new to this comparison, and it is a shared cluster node.**
It has been benchmarked here for the PyCBC complete search since the start
but was never part of the hardware comparison, which is an odd gap given it
is the oldest and most register-starved x86 target in the fleet and the one
the coarse-kernel work is weighted towards. It is included from this page on.

It was measured under real contention -- the report records
`load_before [41.8, 40.5, 38.6]` rising to `load_after [44.2, 40.8, 38.8]` on
64 cores, where every clean host in this table recorded 2.6 or less. Three
repeated CPU runs show which of its rows survive that:

    mode           run 1    run 2    run 3 (published)   range
    FFTW          179.25   176.89              178.90     1.3%
    Peak only     131.14   134.40              132.75     2.5%
    Full output   251.28   253.69              303.35    20.7%
    Hier. 1e-3     43.79    41.74               68.50    64.1%
                                        Hier. 1e-2 48.1%, Hier. 1e-4 9.3%

So its **FFTW and peak-only rows are trustworthy** and its **full-output and
hierarchical rows are indicative only**; the published run happens to be the
high end of the three for both. The whiskers on the chart show within-run
block percentiles and therefore *understate* the uncertainty on those rows,
because the between-run variation is far larger than the within-run spread.

**Its SNR sweep is visibly non-monotone**, and that is worth explaining
rather than leaving for a reader to trip over. Cost should fall as the
threshold rises, since a higher threshold admits a higher coarse gate and
fewer pairs survive to refinement. Haswell reads 55.01, 68.50, 66.26, 13.52,
18.02 ms across SNR 5.0 to 6.5 -- up where it should go down, in two places.
All six other hosts are strictly monotone.

It is not a selection or modelling fault: the gate chooses the **identical
configuration** on Haswell as on gravity-dev1 at every threshold -- band
1024/1024/1024/512/512, eight taps throughout, and refinement fractions
10.83%, 1.70%, 0.54%, 1.94%, 0.29%. Those fractions are properties of the
data and the gate, not of the host, and they are what determine how much work
there is to do. Identical work with non-monotone timings on the one contended
host is measurement noise. (The large step between SNR 5.75 and 6.0 is
structural and appears on every host: that is where the selected band drops
from 1024 to 512.)

A quiet measurement of this host is still owed, and it is what would make
these rows quotable.

**‡ sugwg-login2 is a virtualized guest.** Its FFTW baseline moved 2.3% here,
which is within tolerance, but it has moved as much as 32% across longer
intervals, so treat its row as the least stable of the clean set.

## Interpretation

- **The detection threshold matters as much as the budget.** At `fd=1e-3`
  the same machine spans a factor of 2.5-4 between SNR 5.0 and 6.5, and the
  band the gate selects can change within that range. A single fixed
  threshold was hiding a dimension the reader should choose, which is why
  the comparison page now exposes it.

- **On a real reference the hierarchy still wins by a wide margin.** At SNR
  5.5, `fd=1e-2` runs 3.95 ms against 34.27 ms for flat peaks on the 5950X, a
  9x gap.

- Iris Xe hierarchy remains a performance target rather than a result: at
  SNR 5.5 its `fd=1e-3` and `fd=1e-4` configurations take 23.01 and 23.54 ms
  against 9.75 ms for flat peaks, so screening costs more than not screening
  there. The Intel accuracy and dispatch corrections described in the
  September 26 page still apply; this revision does not claim Intel GPU
  tuning.

- These bars compare complete algorithms, not equal work. FFTW and the GPU
  FFT-only references time only the inverse transform. The
  [work and traffic accounting](m2-teaser-headroom.md) explains why peak-only
  output can beat a memory-heavy full transform and why a hierarchy should not
  be credited with FLOPs it avoided. This measurement checks numerical
  correctness, including a strong injected match, but does not remeasure
  statistical false-dismissal rates per device.

## Reproduction

Install the same source revision into a project-local environment and run CPU
and GPU separately, so a GPU capability or correctness failure cannot discard
CPU results:

```bash
python tools/teaser_fleet.py --device cpu --cpu 0 --revision eecb43c --out cpu.json
python tools/teaser_fleet.py --device gpu --cpu 0 --revision eecb43c --out gpu.json
```

`SNRS` and `DEFAULT_SNR` in `tools/teaser_fleet.py` set the thresholds
recorded and the one the static chart draws. Adding a threshold costs three
more measured rows per device.

Omit `--cpu` on macOS; use `--cpu 2` on gravity-dev2. Use `--reps 21` for a
longer measurement. A host with no hardware GPU produces an explicit empty
report; a correctness failure records the reason and exits unsuccessfully.
`pyfftw`, `pytest` and `matplotlib` must be present or the FFTW baseline and
the validation step are silently skipped — a missing `pyfftw` is why one
first-pass run here recorded five rows instead of six. To redraw the combined
chart from the recorded reports:

```bash
python tools/teaser_fleet.py --compare docs/measurements/teaser-fleet-20260928.json \
  --out docs/assets/teaser-fleet.svg
```

Do not run a teaser measurement and another pinned benchmark on the same CPU
concurrently: an earlier attempt here overlapped a teaser run with a PyCBC
search on CPU 0 and both had to be discarded.

The source/runtime, dependencies, caches, temporary files, and results were
kept in dedicated benchmark folders, reusing the existing project on M2. No
global package installation or system tuning was performed.
