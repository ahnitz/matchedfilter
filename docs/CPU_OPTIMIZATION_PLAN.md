# CPU Optimization Plan & Execution Tracking

**Date**: 2026-10-04  
**Workspace**: `/home/ahnitz/projects/claude/searchdev`  
**Target Repository**: `work/peak-fft`  
**Validation Environments**: Remote testbeds `dev1` (Ryzen 9 5950X Zen 3), `dev3`, `dev4`, `haswell` (OG-NODE-10-5-201-169 via su2)  
**Safety Policy**: Zero heavy benchmarks on `dev2` (local host running active search jobs). Zero regressions in numerical fidelity and FDR monotonicity.

---

## 1. Objectives & Ranked Levers

Based on empirical profiling documented in `work/peak-fft/docs/cpu-levers.md`:

### Lever 1: Eliminate Band 1024 AVX2 Regression (`alt_max_n` Alignment)
- **Problem**: `pblim` in `hmf.c:62` correctly limits native pairbatch to 512 on AVX2. However, `alt_max_n` in `matchfilt.c:106` was set to 1024 on AVX2 (`(!strcmp(isa,"AVX3") || !strcmp(isa,"AVX2")) ? 1024u : 512u`). At band 1024 on AVX2, the alternate pair path is 1.11x slower than balanced (3.78 ms vs 3.39 ms).
- **Fix**: Update `alt_max_n` to 1024 only for AVX3 (AVX-512) where lane width $\ge 16$, and 512 for AVX2 and narrower backends.
- **Expected Impact**: +10% speedup for band 1024 coarse pass on AVX2 architectures.

### Lever 8: Hoist `getenv` Out of `binmax_prod_batch`
- **Problem**: `binmax_prod_batch` in `src/balanced-inl.h` calls `getenv("MF_COARSE_INT16")` on every single invocation in the inner batch loop across all templates.
- **Fix**: Cache `coarse_int16` flag on the plan struct (`BP`) during plan creation (`p->coarse_int16 = ...`), avoiding repeated libc environment lookups.
- **Expected Impact**: Reduces per-pair call overhead and libc contention.

### Lever 2: Correct Complex Conjugate Product Sign in Q15 Int16 Kernel
- **Problem**: `src/int16_coarse.h` computes $d \cdot \text{conj}(t)$ instead of $\text{conj}(d \cdot t)$ as used in standard matched filtering (`codelets-inl.h:9179`).
- **Fix**: Correct the real and imaginary FMA operations in `src/int16_coarse.h`:
  - `p_r = (d_r * t_r - d_i * t_i) * vscale` via `_mm256_fmsub_ps`
  - `p_i = -(d_r * t_i + d_i * t_r) * vscale` via `_mm256_fnmsub_ps`
- **Expected Impact**: Restores exact mathematical alignment between Q15 coarse kernel and FP32 reference. Re-enable and verify `tests/test_coarse_q15.py`.

### Lever 3: Widen Cascade Candidate Search Space in Python Selector
- **Problem**: `candidate_configs` in `python/matchedfilter/__init__.py` derives cascade candidates strictly by halving/quartering the single-tier winner `b_single` (`b0 in [b_single // 2, b_single // 4]`). At SNR 5.5, single-tier cost selects 512, which makes the optimal 512+2048 cascade structurally unreachable.
- **Fix**: Permit candidate evaluation of wider two-tier configurations where `b1` can be greater than `b_single` (e.g. `(512, 1024)`, `(512, 2048)`), verifying FDR gate budget satisfaction.
- **Expected Impact**: Up to 1.31x speedup at SNR 5.5 on CPU searches.

### Lever 4: Template Count Threshold (`ntmpl >= AP_W`)
- **Problem**: Plans require `ntmpl >= 16` to instantiate pairbatch. On AVX2 (`AP_W = 8`), batches of 8 templates fall back to balanced despite filling a full SIMD vector.
- **Fix**: Check `ntmpl >= ap_lane_width()` where appropriate.

---

## 2. Step-by-Step Implementation & Verification Plan

1. **Implement Core C/C++ Fixes in `work/peak-fft`**:
   - `src/matchfilt.c`: Align `alt_max_n` with `pblim` (512 on AVX2, 1024 on AVX3).
   - `src/balanced-inl.h`: Hoist `getenv("MF_COARSE_INT16")` into plan struct `BP`.
   - `src/int16_coarse.h`: Correct complex product signs to $\text{conj}(d \cdot t)$.
2. **Implement Python Selector Enhancement in `python/matchedfilter/__init__.py`**:
   - Widen cascade candidate generation in `candidate_configs` to explore higher tier-1 bands when resolving FDR budget.
3. **Remote Deployment & Unit Test Suite**:
   - Sync modified source tree to remote testbed `dev1` (Ryzen 9 5950X Zen 3).
   - Build wheel / compile native extension in remote venv (`/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/venv`).
   - Run `pytest` across affected suites (`tests/test_pairbatch_policy.py`, `tests/test_cascade.py`, `tests/test_coarse_q15.py`, `tests/test_api.py`, `tests/test_gate_model.py`).
4. **End-to-End PyCBC Benchmark & Fidelity Verification**:
   - Run slice test on Haswell (`run_haswell_slice_90750e6.sh`) or `dev1`.
   - Measure `Fine FIR Filtering (Primary)` runtime before and after changes.
   - Run `compare_fidelity.py` against reference HDF triggers to guarantee >95% recall, bounded SNR difference std dev, and zero regressions.
5. **Final Comprehensive Report Delivery**:
   - Document verification record, performance measurements, and known issues.
