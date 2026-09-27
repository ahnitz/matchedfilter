# M2 and Zen 5: the same teaser workload

September 26, 2026. Matchedfilter implementation `100e5cb`; the teaser driver
now supports Metal/MLX and records Metal device times separately from public
API times. Each batch contains 16 data spectra × 512 templates × 4096 points,
Gaussian noise, the same matched-profile template bank, a full window, and
final threshold 5.5. CPU calls use one thread. Setup and input upload are
excluded; full output reuses device-accessible storage without a NumPy copy.

The M2 is a Mac mini with a 10-core GPU and 24 GiB memory. M2 figures below
are fresh measurements. AMD figures are the existing stable
[`teaser.json`](../assets/teaser.json) reference on Ryzen AI Max+ 395 / Radeon
8060S. Fresh AMD runs encountered load averages around 27 and large timing
changes: full CPU output ranged from 61–97 ms across runs, versus the saved
35.46 ms, and GPU peaks ranged from 1.47–5.35 ms across timing blocks versus
the saved 0.766 ms median. Pinning this benchmark to an idle logical CPU did
not remove contention. Those runs are not substituted for the stable reference
or used to claim a hardware regression.

## Public-call timings

| Output | M2 CPU, ms | Zen 5 CPU, ms | M2 GPU, ms | Radeon 8060S, ms |
|---|---:|---:|---:|---:|
| Full correlation | 68.93 | 35.46 | 6.310 | 1.548 |
| Peak only | 60.36 | 23.07 | 3.923 | 0.766 |
| Hierarchical, fd=0.01 | 6.941 | 1.719 | 0.856 | 0.124 |
| Hierarchical, fd=0.001 | 8.252 | 2.353 | 1.375 | 0.165 |
| Hierarchical, fd=0.0001 | 14.272 | 4.460 | 2.302 | 0.187 |

FFT-only references: FFTW takes **252.31 ms on M2** and **70.51 ms on Zen 5**;
MLX takes **11.73 ms on M2 GPU**, while rocFFT takes **2.56 ms on Radeon**.
The GPU references are different engines. The M2 FFTW plan was inspected
and contains `t2bv_32_neon` and `n1bv_128_neon`; planning remains capped at
15 seconds, as in the saved AMD reference.

The previous M2 optimization report used 128×512 pairs, eight times this
batch size. Its absolute milliseconds cannot be compared directly with these
teaser results. In this matched workload the saved Zen 5 CPU peak path is
2.62× faster, and the Radeon GPU peak path is 5.12× faster.

Hierarchical settings are automatically selected per device. CPU uses band
512 for the first two budgets; M2 uses 1024 for the strictest budget, while
the saved Zen 5 run used 512. Metal uses band 256 for all three budgets;
Radeon uses 512, 512, and 1024. Metal coarse arithmetic is FP32; Vulkan uses
the existing half-width coarse specialization and FP32 refinement. These
are end-to-end algorithm comparisons, not identical refinement workloads.

## Work removed by each restriction

Use `P=8192`, `N=4096` and the conventional complex-FFT estimate
`F_fft(n)=5 n log2(n)`. Complex multiplication adds `6n` operations and
squared magnitudes add `3n`. This is an algorithmic work estimate, not a
count of emitted instructions: it omits address arithmetic, shuffles,
comparisons, twiddle generation, barriers, and compaction, and optimized FFT
factorizations need not execute exactly this number of operations.

- Full: `P × (F_fft(N)+6N)` = **2.215 GFLOP**, plus **268.44 MB** of output.
- Peaks: `P × (F_fft(N)+9N)` = **2.315 GFLOP**, with only about **0.10 MB**
  of index/value payload. There is no full correlation write/read cycle.
- Hierarchical: `P × (F_fft(B)+9B) + rP × (F_fft(N)+9N)`, where `B` is the
  selected band and `r` is the measured refinement fraction. Cached input and
  template preparation is excluded, consistently with the timed calls.

For Metal, actual estimated work at the three budgets is **0.212, 0.541,
and 1.137 GFLOP**, with refinement fractions **4.71%, 18.95%, and 44.69%**.
For M2 CPU it is **0.246, 0.296, and 0.531 GFLOP**, with fractions **0.85%,
2.99%, and 1.54%**. The final fraction falls because the selected coarse
transform doubles in size. Crediting each hierarchical call with 8192 full
FFTs would confuse avoided work with hardware utilization.

## Hardware reference points

| Resource | M2 | Ryzen AI Max+ 395 / Radeon 8060S |
|---|---:|---:|
| One CPU core, illustrative FP32 FMA peak | ≈112 GFLOP/s | up to 326.4 GFLOP/s |
| GPU FP32 FMA peak | 3.6 TFLOP/s | up to 29.7 TFLOP/s with dual issue; 14.8 without |
| Whole-system memory interface | 100 GB/s | 256 GB/s |

CPU estimates use four 128-bit FMAs/cycle at an assumed 3.5 GHz for M2,
and two 512-bit FMAs/cycle at the published 5.1 GHz boost for Zen 5. These
are not measured clocks during the benchmark. The M2 instruction throughput
has [independent microbenchmark evidence](https://jia.je/hardware/2026/07/06/apple-m2/).
AMD documents [512-bit Zen 5 execution](https://www.amd.com/content/dam/amd/en/documents/epyc-business-docs/white-papers/5th-gen-amd-epyc-processor-architecture-white-paper.pdf).
The CPU estimates describe one core, not the entire processor.

Apple's [M2 announcement and architecture diagram](https://www.apple.com/newsroom/2022/06/apple-unveils-m2-with-breakthrough-performance-and-capabilities/)
describe the GPU and memory interface. AMD's [395 specifications](https://www.amd.com/en/products/processors/laptop/ryzen/ai-300-series/amd-ryzen-ai-max-plus-395.html)
give 40 GPU CUs, 2.9 GHz, and 256-bit LPDDR5x-8000. The GPU arithmetic
figures follow from `40 × 64 × 2 FMA operations × 2.9 GHz`, with another
factor of two only when [RDNA dual issue](https://www.amd.com/content/dam/amd/en/documents/radeon-tech-docs/instruction-set-architectures/rdna3-shader-instruction-set-architecture-feb-2023_0.pdf)
is fully usable. The bandwidth is `8000 MT/s × 256 bits / 8`.

Peak-only algorithmic throughput is about **38.4 versus 100.4 GFLOP/s on
CPU**, or **34% versus 31%** of those illustrative FMA peaks. On GPU it is
**0.590 versus 3.021 TFLOP/s**, or **16% versus 10%** of the nominal
dual-issue peaks (20% for Radeon relative to single issue). This does not
show a large M2-specific CPU utilization deficit. Pure FMA percentages are
not FFT efficiency scores: the instruction mix and exchange cost differ.

## Optimistic time model and practical headroom

For full/peak output, estimate `max(arithmetic / peak_FMA, bytes / bandwidth)`.
The traffic estimate assumes each unique input spectrum is read once, giving
17.30 MB of input, plus the output above. Cache residency can change DRAM
traffic, and real kernels can reread inputs. For hierarchy, add the serial
coarse and refinement compute terms, using the measured refinement fraction;
no claim is made that this compute-only estimate includes its memory floor.
Vulkan's coarse term uses its higher half-precision rate.

| Variant | M2 CPU model, ms | M2 GPU model, ms | Zen 5 CPU model, ms | Radeon model, ms |
|---|---:|---:|---:|---:|
| Full | 19.77 | 2.857 | 6.785 | 1.116 |
| Peaks | 20.67 | 0.643 | 7.093 | 0.078 |
| Hierarchical, fd=0.01 | 2.199 | 0.059 | 0.755 | 0.0045 |
| Hierarchical, fd=0.001 | 2.640 | 0.150 | 0.906 | 0.0061 |
| Hierarchical, fd=0.0001 | 4.737 | 0.316 | 1.276 | 0.0095 |

These are optimistic model values, **not proven lower bounds or promised
speedups**. In particular, a tiny hierarchy arithmetic estimate does not mean
its synchronization and compaction can disappear. An instruction-level
roofline would also need operation-mix and cache/traffic measurements.

Metal's measured device times are 5.943 ms full, 3.577 ms peaks, and
0.517/1.024/1.931 ms hierarchical. Roughly **0.34–0.37 ms per call** lies
outside those GPU command durations. At fd=0.01, retaining that host cost
already raises a 0.059 ms compute-only target to roughly 0.40 ms, limiting
the improvement from kernel work alone to about 2.1× before other costs.

The existing Metal arithmetic probe measured **1.57 TFLOP/s FMA**, **0.787
TFLOP/s additions**, and **78.5 GB/s** streaming copy. These synthetic rates
are practical reference measurements, not verified hardware ceilings. Peak
filtering reaches roughly 75% of that addition rate. The full-output
ideal-reuse traffic estimate would take about 3.64 ms at that measured bandwidth, versus 6.31 ms
end-to-end. There is more evidence for a bandwidth/implementation opportunity
in full output than for expecting peak filtering to reach pure FMA peak.

## Demonstrated improvements available without new kernels

Paired nine-round measurements pinned each candidate band while retaining
the same reference, SNR and calibration budget:

| M2 case | Automatic band | Faster measured band | Before → after, ms | Speedup |
|---|---:|---:|---:|---:|
| GPU, fd=0.001 | 256 | 512 | 1.370 → 0.918 | 1.49× |
| GPU, fd=0.0001 | 256 | 512 | 2.307 → 1.128 | 2.05× |
| CPU, fd=0.0001 | 1024 | 512 | 14.324 → 11.463 | 1.25× |

For GPU fd=0.01, bands 256 and 512 tie within measurement variability.
For the stricter GPU budget, band 512 cuts estimated work from 1.137 to
0.416 GFLOP by reducing refinement from 44.69% to 8.20%. For the strict
CPU case it cuts work from 0.531 to 0.416 GFLOP; the observed 1.25× gain
closely tracks the 1.27× work reduction.

The next task is to refresh measured selection costs across representative
batches and profiles, not hardcode the winner of this one teaser. This
comparison does not modify calibration or change the default selection.
These timings do not independently remeasure the requested dismissal rate.

## Reproduction

Run `python tools/teaser_figure.py --out .local/teaser-m2.svg` on the Mac.
Install FFTW with NEON enabled and build pyFFTW against it. The initial
pyFFTW 0.15.1 wheel bundled scalar-only FFTW 3.3.10 and took about 311 ms;
that result must not be presented as an optimized FFTW reference. The driver
now records the FFTW compiler/version/build/alignment and warns about missing
SIMD build tags. pyFFTW's alignment alone is not a reliable NEON indicator.
Its ARM wrapper also appends `FFTW_UNALIGNED` even for aligned arrays, so
the teaser uses that library's aligned single-thread C API on macOS and
validates the result against a double-precision transform before timing.
MLX is the GPU FFT-only reference on macOS, rocFFT on AMD. MLX retains its
own result allocations; neither GPU baseline includes a NumPy copy.

Given two saved reports, produce a common-axis comparison without retiming:

```bash
python tools/teaser_figure.py --compare m2.json amd.json --out comparison.svg
```

The comparison refuses different transform lengths, batch shapes or SNRs.
It labels each report's machine and retains per-device hierarchical choices.
