# Six-machine teaser comparison

Measured September 26, 2026 (September 27 UTC), using library revision
`fe7371d`. All results here are fresh measurements. The older saved teaser
is not mixed into this comparison.

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

| Machine / CPU | FFTW | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| gravity-dev1 / Ryzen 9 5950X | 63.87 | 51.43 | 36.48 | 3.36 | 4.17 | 7.99 |
| gravity-dev2 / Ryzen AI Max+ 395 | 78.32 | 36.37 | 24.68 | 1.88 | 3.01 | 4.64 |
| gravity-dev3 / Ryzen 5 5500U | 88.12 | 73.98 | 51.78 | 5.10 | 6.56 | 15.55 |
| gravity-dev4 / Core i5-13500H | 44.36 | 54.95 | 34.27 | 3.33 | 4.13 | 8.28 |
| empire / Apple M2 | 252.09 | 69.19 | 60.83 | 6.95 | 8.26 | 14.27 |
| sugwg-login2 / Xeon Platinum 8260 guest | 149.55 | 124.31 | 79.36 | 5.48 | 7.33 | 12.52 |

The Xeon is exposed through a virtual machine. Its CPU topology and cache
inventory do not describe an isolated physical core; these numbers measure
the available guest environment. The laptop Intel run is pinned to CPU 0.
No frequency governor or system configuration was changed.

## GPU timings

| Machine / GPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| gravity-dev2 / Radeon 8060S | 2.62 | 1.587 | 0.770 | 0.132 | 0.167 | 0.206 |
| gravity-dev3 / Radeon integrated graphics, 5500U | unavailable | 15.954 | 10.168 | 1.958 | 2.147 | 1.744 |
| empire / M2, 10 GPU cores | 11.72 | 6.314 | 3.928 | 0.855 | 1.378 | 2.302 |

gravity-dev1 and sugwg-login2 expose no physical GPU. Software rendering is
excluded. **gravity-dev4's Iris Xe fails numerical validation**, so its
GPU timings are withheld. This is not a claim that its GPU is unavailable.

The independent check found relative full-output error `1.685e-5` against
the existing `1e-5` tolerance. Existing tests independently reproduce the
problem at 4096 points and in the 2048-point bank/peak-parity test; the
latter reaches about `7.06e-5`. CPU checks pass. Investigation of Intel
Vulkan arithmetic is a follow-up; no tolerance was relaxed and no kernel
was changed to obtain this chart.

## Interpretation

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
