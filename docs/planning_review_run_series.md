# Comprehensive Architectural Review: Batch Planning & Execution in `run_series`

## Executive Summary
In matched filtering for gravitational wave searches, `run_series()` provides the primary execution boundary for streaming time series against template banks. This audit analyzes the current layout planning, batch sizing, cache residency, and dispatch mechanisms across both CPU (`src/hmf.c`, `src/matchfilt.c`, `_series.py`) and GPU (`_run_series_gpu`, `_execution_policy.py`) implementations.

---

## 1. Current Architecture Overview

### 1.1 Layout Planning & Window Grouping (`_series.py`)
- **Automatic Layout (`_automatic_series_layout`)**: Partitions a contiguous time series into blocks using the filter's overlap-save `valid=(lo, hi)` window:
  - Block step size: $\Delta = hi - lo$.
  - Search window: $[lo, hi)$ per block, clipped at the end of the series.
- **SeriesLayout & Window Grouping**:
  - Validates contiguous buffers and offset ranges.
  - Detects non-uniform search windows (common at time series boundaries).
  - Groups identical windows to allow batching within homogenous search intervals.

### 1.2 CPU Hierarchical Execution (`src/hmf.c`)
- **Group Sizing (`dgroup`)**:
  - Set during plan construction via `series_group` parameter (default 8), bounded by:
    $$\text{grp} \times 2 \times n \times \text{sizeof(float)} \le 4\text{ MB (L3 cache bound)}$$
- **Data Ingestion & Transform**:
  - Loops over $j = 0 \dots g-1$ blocks sequentially.
  - Scales by $1/n$ during copy into `p->fwd`.
  - Executes scalar 1D forward FFT via `ap_fft(p->full_fft, p->fwd, sp, AP_FORWARD)`.
  - Ingests only the coarse band into `p->coarse`. Full spectrum is retained lazily in `p->dspec[d]` and only transferred to `p->full` when a pair crosses the coarse threshold.
- **Execution**:
  - Calls `ap_mf_run(p->coarse, 0, g, t0, nt, cspan, minev, p->cebuf, ...)` to evaluate all $g \times nt$ coarse pairs in one vectorized pass.
  - For pairs where the coarse peak exceeds threshold, executes refinement `ap_mf_run_sel(p->full, ...)`.

### 1.3 GPU Series Scheduling (`_run_series_gpu`)
- **Memory Batch Budgeting**:
  - Dynamically calculates batch size based on a 64 MB staging budget:
    $$\text{batch} = \min\left(n_{\text{blk}}, 65535, \frac{\text{pair\_limit}}{nt}, \frac{\text{budget}}{8n + 4 + 12 \cdot nt \cdot n_{\text{bins}}}\right)$$
  - Employs device-shared buffers to avoid host-device copying when series is already in shared memory.

---

## 2. Identified Bottlenecks & Optimization Opportunities

### Bottleneck 1: L2 vs L3 Cache Oversubscription in CPU `dgroup`
- **Current Behavior**:
  `dgroup` in `src/hmf.c` clamps held spectra to a fixed 4 MB limit (targeted at L3 cache).
- **The Problem**:
  Coarse matched filtering requires rapid random and strided reads across both data spectra ($g \times 2m$ floats) and template banks ($nt \times 2m$ floats).
  - On older architectures like Haswell (`genuineintel-family6-model63`), private L2 cache is only **256 KB/core**. Holding $g=8$ spectra of length $n=4096$ requires $8 \times 4096 \times 8 = 256\text{ KB}$, leaving 0 KB in L2 for templates or coarse working buffers. This causes constant L2 cache evictions into L3.
  - On modern architectures like Zen 4/Zen 5 (`model112`, `model116`) and Raptor Lake (`model186`), private L2 cache is **1 MB to 2 MB/core**. A group size of $g=8$ underutilizes L2, whereas $g=16$ or $g=32$ would maintain L2 residency while cutting template reload overhead by 50–75%.
- **Optimal Strategy**:
  - Dynamic `dgroup` sizing keyed to per-core L2 cache capacity:
    $$g_{\text{optimal}} = \max\left(1, \min\left(32, \frac{0.6 \times \text{L2\_Capacity}}{2 \times n \times 4 + 2 \times m \times nt \times 4}\right)\right)$$
  - For Haswell ($n=4096, m=1024, nt=64$): $g=4$ (as reflected in `execution-policy.json`).
  - For Zen 5 / Raptor Lake: $g=16$.

### Bottleneck 2: Window Grouping Destroys Stream Temporal Locality
- **Current Behavior**:
  In `_series.py`, `SeriesLayout.group()` reorders blocks across different search windows using:
  ```python
  self.order = np.lexsort((high, low))
  ```
- **The Problem**:
  In continuous real-time searches, data blocks are sequential in time ($t_0, t_0+\Delta, t_0+2\Delta, \dots$). Sorting solely on `(high, low)` shuffles block order whenever edge windows differ. When `ap_hmf_run_series` then reads from `series+2*s0`, it performs out-of-order, non-contiguous jumps across memory, thrashing the hardware prefetcher and CPU TLB.
- **Optimal Strategy**:
  Preserve temporal locality by sorting stably on `(low, high, starts)`:
  ```python
  self.order = np.lexsort((starts, high, low))
  ```
  Within each identical window group, blocks remain in strictly ascending memory order.

### Bottleneck 3: Ragged-Edge Block Invocation Split
- **Current Behavior**:
  In `MatchedFilter.run_series`, when the final clipped block at the series tail has fewer valid bins than earlier blocks, `run_series` splits execution into two separate passes:
  ```python
  main = self.run_series(ser, st[:-1], ws[:-1], we[:-1], ...)
  tail = self.run_series(ser, st[-1:], ws[-1:], we[-1:], ...)
  ```
  It then allocates a new output array and copies `main` and `tail` into it.
- **The Problem**:
  This doubles API and kernel invocation overhead, invalidates reusable result buffers (`_spbuf`), and forces unnecessary array memory copies for a single ragged block.
- **Optimal Strategy**:
  Pad the search window of the ragged block to the standard width, perform the correlation in a single batch pass, and mask out out-of-bounds bins in the result array in-place.

### Bottleneck 4: Serial Scalar Forward FFT Transforms on CPU
- **Current Behavior**:
  In `ap_hmf_run_series`, forward FFTs across the $g$ blocks are performed sequentially:
  ```c
  for(int j=0; j<g; j++){
      ...
      ap_fft(p->full_fft, p->fwd, sp, AP_FORWARD);
  }
  ```
- **The Problem**:
  `ap_fft` is a 1D scalar transform. The CPU executes $g$ independent forward transforms sequentially.
- **Optimal Strategy**:
  Batch forward FFTs across the $g$ blocks using Google Highway SIMD vectorization. A 4-way or 8-way parallel forward transform computes butterflies across SIMD lanes simultaneously, yielding an estimated 1.25x–1.35x speedup in forward data transformation.

### Bottleneck 5: GPU Batch Budget vs Large Template Banks
- **Current Behavior**:
  In `_run_series_gpu`, batch height is bounded by `budget // (8*n + 4 + 12*nt*nb)` with a 64 MB budget.
- **The Problem**:
  For large banks ($nt = 2048$ templates), the denominator becomes large, causing `batch` to collapse to 1 or 2 blocks per dispatch. Launching GPU compute pipelines for 1–2 blocks underutilizes GPU compute units (CUs) and increases kernel dispatch latency.
- **Optimal Strategy**:
  Implement 2D tiling (tiling across both blocks $B$ and templates $T$). Rather than forcing all templates into every block dispatch, split the template bank into chunks of $T_{\text{tile}} = 256$ templates and run $B = 16$ blocks concurrently. This ensures high GPU compute occupancy regardless of bank size.

---

## 3. Summary & Recommended Roadmap

| Bottleneck | Affected Targets | Expected Gain | Implementation Complexity |
|---|---|---:|---|
| **L2-tailored `dgroup`** | All CPU architectures | 1.10x–1.25x | Low (tune in `execution-policy.json`) |
| **Stable `(low, high, starts)` sorting** | CPU & GPU series | 1.05x–1.10x | Low (one line in `_series.py`) |
| **Ragged-edge single-pass unification** | `run_series` tail | 1.03x–1.08x | Medium (`_series.py` & `__init__.py`) |
| **Batched Forward FFT (SIMD)** | CPU `hmf.c` | 1.15x–1.20x | Medium (`src/fft.c`) |
| **2D GPU Block-Template Tiling** | GPU large banks | 1.30x–1.60x | High (`_run_series_gpu` & shaders) |
