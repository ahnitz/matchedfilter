# Six-machine teaser comparison

Measured September 26, 2026 (September 27 UTC), using library revision
`fe7371d`, with Intel GPU results rerun after the twiddle and indirect-dispatch
fixes in `8ae8c79` described below. All timing blocks are preserved in the recorded JSON.

![CPU and GPU throughput on six machines](../assets/teaser-fleet.svg)

[Machine-readable results](teaser-fleet-20260926.json) include hardware,
backend, software versions, CPU affinity, load averages, correctness checks,
every timing block, automatic hierarchical configurations, and refinement
fractions. Bars show median throughput; whiskers show the timing-block
10th–90th percentiles, not statistical confidence intervals.

## Workload and timing

Each call processes **16 data spectra × 512 templates × 4096 points** with
the same Gaussian noise and matched-profile bank, a full lag window, and
SNR threshold 5.5. These are warm public `run()` calls, not `run_series()`
or isolated kernel times. CPU calls use one thread. Linux processes are
pinned to CPU 0, except gravity-dev2 uses CPU 2; macOS schedules its thread.
Setup, calibration, template preparation, and input upload are excluded.
Full correlation reuses output storage; GPU calls include synchronization.

After 0.5 seconds of warmup, each mode records nine blocks of at least
50 ms. Cases with substantial variability were repeated with 21 blocks:
gravity-dev2 GPU, gravity-dev3 GPU, and sugwg-login2 CPU. The reported
median uses **all collected blocks**, rather than the fastest run. The JSON
records each run's block count and median. There is residual variability in
short hierarchical GPU calls and the virtualized server.

FFTW is an inverse-FFT-only baseline, one thread, with PATIENT planning
capped at 15 seconds. The x86 wheel uses FFTW 3.3.5 with SSE2/AVX; M2 uses
FFTW 3.3.10 with NEON through its aligned C API. Thus FFTW bars include
implementation/build differences as well as hardware differences. GPU
FFT-only references are rocFFT on gravity-dev2 and MLX on empire, with
eight queued batches per synchronization and timings divided by eight.
No reference includes a NumPy output copy. rocFFT is unavailable on
gravity-dev3; its filter measurements are still valid.

## CPU timings

Milliseconds per batch; smaller is faster.

| CPU | FFTW | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Ryzen 9 5950X | 63.87 | 51.43 | 36.48 | 3.36 | 4.17 | 7.99 |
| Ryzen AI Max+ 395 | 78.32 | 36.37 | 24.68 | 1.88 | 3.01 | 4.64 |
| Ryzen 5 5500U | 88.12 | 73.98 | 51.78 | 5.10 | 6.56 | 15.55 |
| Core i5-13500H | 44.36 | 54.95 | 34.27 | 3.33 | 4.13 | 8.28 |
| Apple M2 | 252.09 | 69.19 | 60.83 | 6.95 | 8.26 | 14.27 |
| Xeon Platinum 8260 guest | 149.55 | 124.31 | 79.36 | 5.48 | 7.33 | 12.52 |

The Xeon is exposed through a virtual machine. Its CPU topology and cache
inventory do not describe an isolated physical core; these numbers measure
the available guest environment. The laptop Intel run is pinned to CPU 0.
No frequency governor or system configuration was changed.

## GPU timings

| GPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Radeon 8060S | 2.62 | 1.587 | 0.770 | 0.132 | 0.167 | 0.206 |
| Radeon integrated graphics, 5500U | unavailable | 15.954 | 10.168 | 1.958 | 2.147 | 1.744 |
| Iris Xe, Core i5-13500H | unavailable | 23.916 | 9.732 | 6.382 | 5.588 | 23.045 |
| M2, 10 GPU cores | 11.72 | 6.314 | 3.928 | 0.855 | 1.378 | 2.302 |

The Ryzen 9 5950X and Xeon guest expose no physical GPU. Software rendering
is excluded. Iris Xe now passes numerical validation without relaxing the
existing `1e-5` tolerance. Its rerun measured full-output error `1.46e-7`
and peak/refinement error `6.07e-8` against the independent reference.
No FFT-only reference was available on that device.

### Intel corrections

The first Iris Xe run failed full-output validation at `1.685e-5`; an
independent peak test reached `7.06e-5`. Twiddle recurrences amplified the
native sine/cosine approximation error. A Vulkan specialization selects
range-reduced polynomial twiddles on Intel; other vendors and Metal retain
native trigonometry. Full correlation correctness was checked at every
supported power of two from 1,024 through 4,194,304.

A separate synchronization error made hierarchical indirect dispatch read a
stale survivor count. The argument buffer now declares transfer-destination
usage, and barriers cover both transfer fills and compute writes before
indirect-command reads. Covering the transfer fill matters even after
compaction: when no pairs survive, the zero count has no shader write.
Regression tests alternate all and zero survivors with reused plans and
several bin sizes. The Intel full-output/parity/regression run passed 116
tests. The original failed validation remains recorded in the JSON history.

### Performance checks after the fixes

Warm full-output, peak, and hierarchical calls were compared before/after at
2,048, 4,096, and 8,192 points, retaining the 16 × 512 batch. M2 medians
changed by under 0.4% in seven of nine cases; 2,048-point full output was
4.2% slower and hierarchy 1.4% faster in this single comparison. Radeon
showed run-to-run variation, including a 10% difference in 4,096-point full
output. Repeating in reversed order put all nine changes between 2.5%
faster and 2.6% slower, with no consistent broad slowdown. These checks
exclude setup and do not establish a sub-percent regression bound.

## Interpretation

- Iris Xe now has valid full and peak results, but hierarchy remains a
  performance target: the `fd=0.0001` automatic configuration takes
  23.04 ms, versus 9.73 ms for flat peaks. This release corrects accuracy
  and dispatch behavior; it does not claim optimal Intel GPU tuning.

- The Ryzen AI Max+ CPU peak path is about **2.47× faster than M2** in this
  fresh run. The 5950X and i5-13500H also beat M2 on that path, while M2
  beats the 5500U for full correlation. Single-thread rankings depend on
  the output mode, not just the processor name.
- Radeon 8060S is about **5.10× faster than M2 GPU** for peaks, while M2 is
  about **2.59× faster than the 5500U GPU**. These are public-call ratios.
- Full output does not always beat FFTW: on the Intel laptop it takes
  54.95 ms against FFTW's 44.36 ms, despite the peak-only path winning.
  The full path performs the product as well as the FFT; this remains a
  useful optimization target rather than a universal speedup claim.
- Hierarchical bars use the shipped automatic choices. CPU bands are
  512/512/1024; Radeon bands are 512/512/1024, while Metal uses 256 throughout.
  The stricter budget can run faster when it selects a larger coarse band
  and avoids more refinements, as on the 5500U GPU. Metal coarse arithmetic
  is FP32; Radeon uses the existing half-width coarse path with FP32
  refinement. These bars compare complete algorithms, not equal work.

The [work and traffic accounting](m2-teaser-headroom.md) explains why
peak-only output can beat a memory-heavy full transform and why a hierarchy
should not be credited with FLOPs it avoided. This measurement checks
numerical correctness, including a strong injected match, but does not
remeasure statistical false-dismissal rates for each device.

## Reproduction

Install the same source revision and optional NumPy, pyFFTW, and matplotlib
dependencies into a project-local environment. Run CPU and GPU separately
so a GPU capability or correctness failure cannot discard CPU results:

```bash
python tools/teaser_fleet.py --device cpu --cpu 0 --revision fe7371d --out cpu.json
python tools/teaser_fleet.py --device gpu --cpu 0 --revision fe7371d --out gpu.json
```

Omit `--cpu` on macOS. Use `--reps 21` for a longer measurement. No hardware
GPU produces an explicit empty report; a correctness failure records the
reason and exits unsuccessfully. To redraw the recorded combined chart:

```bash
python tools/teaser_fleet.py --compare docs/measurements/teaser-fleet-20260926.json --out comparison.svg
```

The source/runtime, dependencies, caches, temporary files, and results were
kept in dedicated benchmark folders, reusing the existing project on M2.
During setup, the Python installer also created two external launcher
symlinks; those exact links were verified and removed immediately after
discovery. No global package installation or system tuning was performed.
