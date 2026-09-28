# Six-machine teaser comparison

Measured September 27, 2026, at library revision `ce9c828` (current `main`).
This recalculates [the September 26 comparison](teaser-fleet-20260926.md),
which was taken at revision `fe7371d`; that page is kept for history.
All timing blocks are preserved in the recorded JSON.

![CPU and GPU throughput on six machines](../assets/teaser-fleet.svg)

[Machine-readable results](teaser-fleet-20260927.json) include hardware,
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
6.0 and 6.5. The static chart above shows 5.5; the interactive
[hardware comparison page](https://ahnitz.github.io/matchedfilter/comparison.html)
selects among them. The threshold is not a detail: a higher one admits a
higher coarse gate, so fewer pairs survive to refinement. These are warm
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
| Ryzen 9 5950X | 63.57 | 50.70 | 35.52 | 3.86 | 7.03 | 7.98 |
| Ryzen AI Max+ 395 † | 96.18 | 50.28 | 26.27 | 3.52 | 4.84 | 10.73 |
| Ryzen 5 5500U | 87.92 | 74.21 | 52.30 | 6.03 | 12.33 | 14.25 |
| Core i5-13500H | 44.49 | 57.23 | 36.42 | 4.74 | 6.06 | 7.16 |
| Apple M2 | 251.87 | 68.99 | 60.62 | 6.34 | 14.43 | 16.07 |
| Xeon Platinum 8260 (VM) ‡ | 214.52 | 157.93 | 81.58 | 6.85 | 11.61 | 14.05 |

Hierarchical columns are at SNR 5.5. At `fd=1e-3`, varying the threshold:

| CPU | 5.0 | 5.5 | 5.75 | 6.0 | 6.5 |
|---|---:|---:|---:|---:|---:|
| Ryzen 9 5950X | 10.24 | 7.03 | 6.50 | 3.77 | 3.14 |
| Ryzen AI Max+ 395 † | 11.29 | 4.84 | 3.54 | 2.53 | 1.68 |
| Ryzen 5 5500U | 18.91 | 12.33 | 11.49 | 5.83 | 4.44 |
| Core i5-13500H | 9.82 | 6.06 | 5.67 | 4.55 | 3.86 |
| Apple M2 | 20.03 | 14.43 | 13.72 | 6.05 | 5.05 |
| Xeon Platinum 8260 (VM) ‡ | 22.30 | 11.61 | 10.68 | 6.32 | 4.68 |

A factor of 2.5-4 across the range on every machine. The band the gate
selects can change with it as well: on this reference `fd=1e-3` moves from
band 1024 at SNR 5.5 to band 512 by 6.5.

## GPU timings

| GPU | FFT only | Full | Peak | Hier. 0.01 | Hier. 0.001 | Hier. 0.0001 |
|---|---:|---:|---:|---:|---:|---:|
| Radeon 8060S (RADV GFX1151) | 2.81 | 1.60 | 0.80 | 0.15 | 0.18 | 0.21 |
| Radeon integrated, 5500U | unavailable | 16.00 | 10.18 | 2.04 | 1.77 | 1.98 |
| Iris Xe, Core i5-13500H | unavailable | 24.05 | 9.72 | 5.50 | 22.88 | 27.23 |
| M2, 10 GPU cores | 11.68 | 6.32 | 3.93 | 1.40 | 2.76 | 3.91 |

gravity-dev2's GPU rows are **not** affected by the contention marked on its
CPU row: rocFFT reproduces to 0.5%.

The Ryzen 9 5950X and the Xeon guest expose no physical GPU; software
rendering is excluded. rocFFT is unavailable on gravity-dev3, and no FFT-only
reference is available on Iris Xe. Those gaps are the same as on September 26.

## What changed since `fe7371d`

Two things changed at once -- the revision and the reference profile -- so
they have to be separated before anything is claimed.

**The non-hierarchical columns are comparable**, because they do not depend on
the reference at all. The fixed FFTW and rocFFT references are the control:
they contain no matchedfilter code, so a steady baseline means the machine was
steady. On the uncontended machines they reproduce to within 0.8%, and against
that control full output and peak-only are flat:

    FFTW change       5950X +0.7%   5500U -0.5%   i5-13500H +0.5%   M2 +0.2%
    Full / Peak CPU   within about 2% on every uncontended host

**The hierarchical columns are NOT comparable to the September 26 page**, and
no percentage should be read across the two. They are slower here, but that is
the broader captured reference doing more refinement, not a regression: the
gate that looked cheap on a 180-bin synthetic profile has to work harder on a
233-bin real one. This page is the new baseline for hierarchical timings.

The September 26 page, measured entirely on the synthetic profile, remains the
valid like-for-like record of what the revision alone changed.

Two rows carry qualifications, and neither is a property of this revision:

**† gravity-dev2 CPU was contended.** An unrelated eight-process workload
saturated the host throughout. Its FFTW baseline is **96.18 ms against 78.32
ms** recorded on an idle machine. The cause is memory bandwidth, not cores:
pinning the measurement to a fully idle core pair did not help, and lowering
the competing job's scheduling priority to nice 19 did not either, because
neither frees bandwidth. Its CPU numbers are valid for a loaded host and must
not be read as hardware. **Its GPU rows are unaffected** -- rocFFT reproduces
to 0.5%, since the Radeon has its own memory.

**‡ sugwg-login2 is a virtualized guest.** Its FFTW baseline moved 2.7%
between runs here, but 32% against September 26, so the guest's own timing
stability bounds what can be read from that row.

## Interpretation

- **The detection threshold matters as much as the budget.** At `fd=1e-3`
  the same machine spans a factor of 2.5-4 between SNR 5.0 and 6.5, and the
  band the gate selects can change within that range. A single fixed
  threshold was hiding a dimension the reader should choose, which is why
  the comparison page now exposes it.

- **On a real reference the hierarchy still wins by a wide margin, but by
  less than the synthetic curve suggested.** At SNR 5.5, `fd=1e-2` runs
  3.86 ms against 35.52 ms for flat peaks on the 5950X -- a 9x gap where the
  synthetic profile implied closer to 11x.

- Iris Xe hierarchy remains a performance target rather than a result: at
  SNR 5.5 its `fd=1e-3` and `fd=1e-4` configurations take 22.88 and 27.23 ms
  against 9.72 ms for flat peaks, so screening costs more than not screening
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
python tools/teaser_fleet.py --device cpu --cpu 0 --revision ce9c828 --out cpu.json
python tools/teaser_fleet.py --device gpu --cpu 0 --revision ce9c828 --out gpu.json
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
python tools/teaser_fleet.py --compare docs/measurements/teaser-fleet-20260927.json \
  --out docs/assets/teaser-fleet.svg
```

Do not run a teaser measurement and another pinned benchmark on the same CPU
concurrently: an earlier attempt here overlapped a teaser run with a PyCBC
search on CPU 0 and both had to be discarded.

The source/runtime, dependencies, caches, temporary files, and results were
kept in dedicated benchmark folders, reusing the existing project on M2. No
global package installation or system tuning was performed.
