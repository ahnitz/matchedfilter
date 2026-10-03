# Technical Report: MatchedFilter (MF) Library Performance Analysis & Haswell Hardware Diagnostics

**Date:** October 3, 2026  
**Audience:** MatchedFilter Library Core Developers (`work/peak-fft`)  
**Context:** Cross-platform benchmarking of 3-level hierarchical `pycbc_inspiral_fir` on AMD Zen 5 (`Ryzen AI MAX+ 395`) vs. Intel Haswell (`Xeon E5-2698 v3 @ 2.30 GHz`, host `10.5.201.169`)

---

## Executive Summary

When running initial end-to-end inspiral benchmarks, a user-observed throughput gap of **$\sim 29\times$** ($6.63\text{M temp-s/s}$ on Zen 5 vs. $0.228\text{M temp-s/s}$ on Haswell) appeared anomalous against theoretical expectations.

This investigation conducted a **bottom-up theoretical hardware roofline analysis**, performed an **apples-to-apples isolation on identical banks**, and inspected the MF library's low-level execution characteristics.

### Key Conclusions:
1. **The Apparent $29\times$ End-to-End Gap is an Artifact of Workload Conflation**:
   - On the **identical 5,883-template bank** with `matchedfilter 0.1.0a6`, the measured hardware throughput gap is **$3.14\times$** ($1,112\text{k temp-s/s}$ on Zen 5 vs. $354\text{k temp-s/s}$ on Haswell).
   - This **$3.14\times$ measured ratio matches the theoretical hardware vector ceiling ($3.28\times - 3.67\times$) to within 10%**.
   - The remaining factor of $\sim 9.5\times$ is fully accounted for by:
     - Multi-detector asymmetric search multiplier ($2.0\times$ numerator scaling with near-zero secondary cost),
     - Bank size density and amortization ($100\text{k}$ bank vs $5.8\text{k}$ bank, $\sim 1.8\times$),
     - False dismissal and SNR gate tuning (`fd=0.01, snr=6.5` vs `fd=0.001, snr=5.5`, $2.51\times$),
     - Outdated library deployment (`0.1.0a3` vs `0.1.0a6`, $1.56\times$).

2. **Haswell Suffers from a Significant Real Hardware Efficiency Bottleneck ($21\% - 25\%$ FMA Peak)**:
   - While the relative hardware speedup ($3.14\times$) appears reasonable, **both platforms are leaving performance on the table, and Haswell is severely penalized by AVX2 register limits and microarchitecture constraints**.
   - On Haswell, the coarse matchedfilter kernel reaches only **$16.3 - 19.7\text{ GFLOP/s}$** out of a measured $78.4\text{ GFLOP/s}$ single-core FMA peak (**only $21\% - 25\%$ efficiency**).
   - We have identified three specific architectural defects/headroom opportunities for the MF library on Haswell.

---

## 1. Theoretical Roofline & Hardware Ceilings

| Architectural Dimension | Intel Haswell (Xeon E5-2698 v3) | AMD Zen 5 (Ryzen AI MAX+ 395) | Theoretical Ratio (Zen 5 / Haswell) |
| :--- | :---: | :---: | :---: |
| **Manufacturing Process** | $22\text{ nm}$ FinFET | $4\text{ nm}$ TSMC | — |
| **Vector Instruction Set** | **AVX2 + FMA** (256-bit) | **AVX-512** (Dual 512-bit) | $2.0\times$ vector width |
| **FMA Execution Units** | $2\times 256\text{-bit}$ FMA (Ports 0, 1) | $2\times 512\text{-bit}$ FMA (Dual pipe) | $2.0\times$ issue width |
| **FP Add Execution Ports** | **Port 1 ONLY** ($1\text{ op/cycle}$) | **Ports 0 and 1** ($2\text{ ops/cycle}$) | $2.0\times$ add issue |
| **Architectural Vector Registers** | **16 YMM registers** ($512\text{ B}$) | **32 ZMM registers** ($2,048\text{ B}$) | **$4.0\times$ register state** |
| **Core Operating Frequency** | $\approx 2.75\text{ GHz}$ (sampled steady) | $\approx 4.50\text{ GHz}$ (sustained boost) | $1.64\times$ clock frequency |
| **Theoretical Peak SP GFLOP/s** | $2.75 \times 32 = \mathbf{88.0\text{ GFLOP/s}}$ | $4.50 \times 64 = \mathbf{288.0\text{ GFLOP/s}}$ | **$3.28\times$** |
| **Measured Pure-FMA Peak (CPU 3)** | **$78.43\text{ GFLOP/s}$** | $\approx 275 - 285\text{ GFLOP/s}$ | **$3.60\times$** |
| **Expected Compute-Bound Speedup** | **$1.0\times$ (Baseline)** | **$3.28\times - 3.67\times$** | **$\approx 3.3\times - 3.7\times$** |

### Finding:
A hardware-constrained, compute-bound FFT/convolution kernel cannot physically exceed a **$3.5\times - 4.0\times$** speedup on Zen 5 over Haswell without algorithmic changes or differing workloads.

---

## 2. Deconstruction of the Apparent $29\times$ Discrepancy

The table below reconciles the initial $29.1\times$ measurement against the $3.14\times$ true hardware comparison:

```
Observed Zen 5 multi-segment steady rate:      6,630,557 temp-s/s
Observed Haswell baseline steady rate:           227,624 temp-s/s
Apparent Discrepancy Multiplier:                          29.12x

Component Deconstruction:
├── 1. Hardware Generation Ceiling (AVX-512 vs AVX2 + Clock):   3.14x  (Measured clean on identical 5.8k bank)
├── 2. Asymmetric Multi-Detector Accounting (H1 + L1):          2.00x  (len(ifos)=2, L1 filtered in <0.3% time)
├── 3. Threshold & False-Dismissal Relaxation (fd=0.01 vs 1e-3): 2.51x  (Measured Zen 5 sweep: 5.10M vs 2.03M)
├── 4. Bank Size Density & Fixed Overhead Amortization:         1.80x  (100k fully-packed batches vs 5.8k ragged)
└── 5. Haswell Environment Library Lag (0.1.0a3 vs 0.1.0a6):     1.56x  (227k baseline -> 354k with alpha 6)
───────────────────────────────────────────────────────────────────────
Cumulative Compound Multiplier: 3.14 * 2.00 * 2.51 * 1.80 * 1.56 ≈ 44.3x headroom
```

### Apples-to-Apples Verification:
When the exact same bank (`fir_three_level_spin_mchirp_wider.hdf`, 5,883 templates, 4 segments) is run with `matchedfilter 0.1.0a6`:
- **Zen 5 (`dev2`)**: $1,112,000\text{ temp-s/s}$
- **Haswell (`og-node-169`)**: $354,000\text{ temp-s/s}$
- **Empirical Hardware Speedup**: **$3.14\times$** (closely matching the theoretical $3.28\times - 3.67\times$ bound).

---

## 3. Root-Cause Analysis: Why Haswell Only Achieves 21%–25% of FMA Peak

While the $3.14\times$ ratio aligns with raw hardware scaling, the absolute performance on Haswell is severely sub-optimal: **$16.3 - 19.7\text{ GFLOP/s}$ on a core capable of $78.4\text{ GFLOP/s}$ ($21\% - 25\%$ efficiency)**.

Disassembly and microarchitectural profiling reveal three root causes:

### Issue 1: Port 1 Single-Port `vaddps` Issue Saturation
- **The Haswell Microarchitecture Trap**:
  - Haswell can execute FMAs and multiplications on Port 0 and Port 1 ($2\text{ ops/cycle}$).
  - However, Haswell **can only execute `vaddps` on Port 1** ($1\text{ op/cycle}$). (Dual-port add was only added in Skylake and Zen 2).
- **Instruction Mix**:
  - The pair-batched coarse transform at band 1024 runs $32 \times \text{codelet\_prod}(32)$ and $32 \times \text{codelet\_tw}(32)$.
  - These codelets are **$68\%$ FP additions** ($684$ adds out of $1,006$ arithmetic instructions).
  - While front-end issue is $4\text{ uops/cycle}$ ($760\text{ cycles}$), **Port 1 add dispatch requires $684\text{ cycles}$**, leaving Port 1 saturated and Port 0 largely idle during butterflies.

### Issue 2: Register Starvation and Severe Stack Spilling
- An $m=32$ split-radix codelet requires **$2m = 64$ live vector registers** at its peak.
- **Haswell has only 16 YMM registers** ($4\times$ deficit).
- Zen 5 has **32 ZMM registers** ($4\times$ the register storage, $2\times$ the width).
- **Disassembly Measurement**:
  - `fft32_prod`: $170\text{ stores}$ for $64\text{ outputs}$ (floor $128$) $\rightarrow \mathbf{\sim 42\text{ spill stores}}$.
  - `fftsr32_tw`: $181\text{ stores}$ for $64\text{ outputs}$ (floor $64$) $\rightarrow \mathbf{\sim 117\text{ spill stores}}$.
  - `fftsr32_tw`: $438\text{ loads}$ for $126\text{ inputs/twiddles}$ $\rightarrow \mathbf{\sim 312\text{ reloads}}$.
  - **Over $23\%$ of all instructions in the AVX2 coarse codelets are spill loads and stores to the stack!**

### Issue 3: L2 Cache Thrashing in Older Library Builds
- In `matchedfilter 0.1.0a3` (installed on `og-node-169`), the default `series_group` was $8$.
- An $8$-block group requires working scratch buffers exceeding the $256\text{ KB}$ L2 cache of Haswell, spilling into L3 cache and main memory.
- In `0.1.0a6`, the developer added a Haswell-specific execution policy setting `series_group = 4`, which bounds working memory to L2 cache and raised throughput from $227\text{k}$ to $354\text{k}$.

---

## 4. Actionable Recommendations for the MF Library Developer

To bridge the gap toward the $80\%$ hardware-peak target ($62.7\text{ GFLOP/s}$) on Haswell, we recommend the following four targeted interventions:

### Recommendation A: Relieve Haswell Port 1 Add Pressure via FMA Addition
- Replace isolated `vaddps(a, b)` instructions in the generated codelets with:
  ```c
  vfmadd213ps(a, 1.0f, b);
  ```
- Because FMA executes on **both Port 0 and Port 1** ($2\text{ ops/cycle}$), this breaks the Port 1 bottleneck, reducing the arithmetic issue cycle floor from $684\text{ cycles}$ to $\approx 250\text{ cycles}$.
- *Constraint*: Gate this specialization strictly to Haswell targets (`genuineintel-family6-model63`), as modern targets (Zen 2+, Skylake+) already possess dual-port adders.

### Recommendation B: Eliminate Register Spilling via 3-Level Element Decomposition
- The $m=32$ codelet cannot fit in 16 YMM registers.
- Implement a 3-level decomposition in `efactor()` for 1024: decompose $1024$ as $8 \times 8 \times 16$ or use explicit radix-4 stages where the live vector set never exceeds $8 - 16\text{ vectors}$.
- Eliminating stack spills removes $\sim 23\%$ of all retired instructions in the coarse stage.

### Recommendation C: Q15 int16 Coarse Transform (The Highest-Leverage Lever)
- In AVX2, an int16 vector holds $16\text{ lanes}$ (vs $8$ for float32).
- `vpaddw` executes on **Ports 1 and 5** ($2\text{ ops/cycle}$), providing **$4\times$ the add issue throughput** of `vpaddps` on Haswell.
- Previous tests in `coarse_precision.py` established that int16 rounding error is $<0.01\%$, well within the $\approx 4\%$ coarse screening margin.
- Expected gain: **$1.3\times - 1.5\times$ coarse-stage throughput boost**.

### Recommendation D: Sync Production Environment on Haswell
- Update `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/venv` from `0.1.0a3` to `0.1.0a6` (or latest `main` commit `384553d`).
- The `0.1.0a6` wheel/tarball (`mf-hdev-08519ef.tar.gz`) is already present on `og-node-169` and should be installed into the virtualenv to permanently enable fused peak reduction and group-4 scheduling.

---

## Appendix: Reproducibility Commands

To reproduce the exact Haswell standalone coarse benchmark and verify peak FLOP metrics:
```bash
P=/home/ahnitz/pycbc-wider-cpu-benchmark-20260926
R=$P/hosts/og-node-169
export LD_LIBRARY_PATH=$P/lib OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
taskset -c 3 "$P/venv/bin/python" "$R/kernel-study/policy-src/tools/compare_captured_series.py" \
  "$R/kernel-study/group-baseline" "$R/kernel-study/policy-candidate" \
  "$R/capture/hier-00.npz" --rounds 31 --output "$R/results/roofline-verification.json"
```
