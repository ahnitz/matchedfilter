#!/usr/bin/env python3
"""Mixture Training and Calibration for Two-Tier Coarse Cascade.

Evaluates and optimizes the cascade thresholds (gamma_0, gamma_1) using:
1. Signals exactly at target SNR threshold (rho = rho_target) + noise
   to guarantee False Dismissal Rate (FDR) <= FDR_target.
2. Large-scale pure noise samples to measure noise escalation rates
   (p_pass0, p_pass1) and minimize total runtime cost per pair.
"""
import sys
import time
import numpy as np
import matchedfilter as mf


def inspiral_power(n, exponent=-7 / 3.0, knee_frac=0.0150):
    p = np.zeros(n, dtype=np.float64)
    k = np.arange(1, n // 2).astype(np.float64)
    p[1:n // 2] = (k ** exponent / ((knee_frac * n / k) ** 4 + 1.0))
    return p / p.sum()


def simulate_mixture(n=4096, m0=256, m1=1024, snr_target=5.5, fdr_target=0.0010,
                     n_signals=20000, n_noise=50000, seed=42):
    rng = np.random.default_rng(seed)
    power = inspiral_power(n)
    h_full = np.sqrt(power).astype(np.complex64)
    
    f0 = float(power[:m0].sum())
    f1 = float(power[:m1].sum())
    h0 = (h_full[:m0] / np.sqrt(f0)).astype(np.complex64)
    h1 = (h_full[:m1] / np.sqrt(f1)).astype(np.complex64)
    
    scale0 = m0 / np.sqrt(f0)
    scale1 = m1 / np.sqrt(f1)
    
    print(f"=== MIXTURE CALIBRATION: n={n}, m0={m0}, m1={m1} ===")
    print(f"Target SNR: {snr_target}, Target FDR: {fdr_target*100:.3f}%")
    print(f"Energy in band m0: {f0*100:.2f}%, in band m1: {f1*100:.2f}%")
    
    # ------------------------------------------------------------------
    # Step 1: Signals EXACTLY at SNR threshold + noise
    # ------------------------------------------------------------------
    print(f"\n[1/3] Simulating {n_signals} signals exactly at SNR={snr_target} + noise...")
    t0 = time.perf_counter()
    
    # Pre-allocate arrays
    sig_fine_max = np.empty(n_signals, dtype=np.float32)
    sig_t0_max = np.empty(n_signals, dtype=np.float32)
    sig_t1_max = np.empty(n_signals, dtype=np.float32)
    
    # Vectorized batch processing
    batch_size = 1000
    for b in range(0, n_signals, batch_size):
        cur_batch = min(batch_size, n_signals - b)
        lags = rng.integers(0, n, size=cur_batch)
        k = np.arange(n)
        phases = np.exp(-2j * np.pi * np.outer(lags, k) / n).astype(np.complex64)
        
        # Signal at exactly snr_target
        sig = snr_target * h_full[None, :] * phases
        # Complex standard normal noise
        noise = (rng.standard_normal((cur_batch, n), dtype=np.float32) 
                 + 1j * rng.standard_normal((cur_batch, n), dtype=np.float32))
        d = sig + noise
        
        # Fine stage (IFFT of d * conj(h_full))
        # Note: np.fft.ifft default normalizes by 1/n, so we multiply by n
        z_fine = np.fft.ifft(d * np.conj(h_full)[None, :], axis=-1) * n
        sig_fine_max[b:b+cur_batch] = np.abs(z_fine).max(axis=-1)
        
        # Tier 0 (m0 points)
        z0 = np.fft.ifft(d[:, :m0] * np.conj(h_full[:m0])[None, :], axis=-1) * scale0
        sig_t0_max[b:b+cur_batch] = np.abs(z0).max(axis=-1)
        
        # Tier 1 (m1 points)
        z1 = np.fft.ifft(d[:, :m1] * np.conj(h_full[:m1])[None, :], axis=-1) * scale1
        sig_t1_max[b:b+cur_batch] = np.abs(z1).max(axis=-1)
        
    print(f"    Done in {time.perf_counter()-t0:.2f}s")
    
    # Filter to cases where fine stage detects (rho >= snr_target)
    kept_mask = sig_fine_max >= snr_target
    n_kept = int(kept_mask.sum())
    print(f"    Signals triggering fine detector (rho >= {snr_target}): {n_kept} / {n_signals} ({n_kept/n_signals*100:.1f}%)")
    
    t0_kept = sig_t0_max[kept_mask]
    t1_kept = sig_t1_max[kept_mask]
    
    # ------------------------------------------------------------------
    # Step 2: Pure noise simulations
    # ------------------------------------------------------------------
    print(f"\n[2/3] Simulating {n_noise} pure noise realizations...")
    t0 = time.perf_counter()
    noise_t0_max = np.empty(n_noise, dtype=np.float32)
    noise_t1_max = np.empty(n_noise, dtype=np.float32)
    
    for b in range(0, n_noise, batch_size):
        cur_batch = min(batch_size, n_noise - b)
        noise = (rng.standard_normal((cur_batch, n), dtype=np.float32) 
                 + 1j * rng.standard_normal((cur_batch, n), dtype=np.float32))
        
        z0 = np.fft.ifft(noise[:, :m0] * np.conj(h_full[:m0])[None, :], axis=-1) * scale0
        noise_t0_max[b:b+cur_batch] = np.abs(z0).max(axis=-1)
        
        z1 = np.fft.ifft(noise[:, :m1] * np.conj(h_full[:m1])[None, :], axis=-1) * scale1
        noise_t1_max[b:b+cur_batch] = np.abs(z1).max(axis=-1)
        
    print(f"    Done in {time.perf_counter()-t0:.2f}s")
    
    # Relative execution costs of the stages (micro-benchmarked on CPU)
    # Tier 0 (m0=256): ~0.16 us
    # Tier 1 (m1=1024): ~0.82 us
    # Fine (n=4096): ~8.00 us
    cost0 = 0.16
    cost1 = 0.82
    cost_fine = 8.00
    
    # ------------------------------------------------------------------
    # Step 3: Optimal Threshold Optimization (Minimizing Cost at FDR <= fdr_target)
    # ------------------------------------------------------------------
    print("\n[3/3] Optimizing thresholds (gamma_0, gamma_1) to minimize cost at FDR <= target...")
    
    # Baseline single-tier (m1 only):
    # Quantile of t1_kept at fdr_target
    gamma1_baseline = np.quantile(t1_kept, fdr_target)
    p_pass1_base = np.mean(noise_t1_max >= gamma1_baseline)
    cost_base = cost1 + p_pass1_base * cost_fine
    print(f"\n  Baseline Single-Tier (m1={m1} only):")
    print(f"    gamma_1:           {gamma1_baseline:.3f}")
    print(f"    Noise pass to fine: {p_pass1_base*100:.2f}%")
    print(f"    Expected cost/pair: {cost_base:.3f} us")
    
    # Grid search over candidate gamma0 and gamma1
    # gamma0 can range from low to high percentiles of t0_kept
    q_vals = np.linspace(0.0001, fdr_target * 0.8, 40)
    best_cost = float('inf')
    best_res = None
    
    # Also consider a safe conservative allocation: fd0 = 0.4 * fdr_target, fd1 = 0.6 * fdr_target
    for q0 in q_vals:
        g0 = np.quantile(t0_kept, q0)
        fd0 = np.mean(t0_kept < g0)
        if fd0 >= fdr_target:
            continue
            
        # Surviving signals
        surv_mask = t0_kept >= g0
        t1_surv = t1_kept[surv_mask]
        
        # We want P(dismissed at 0 OR dismissed at 1) <= fdr_target
        # P(dismissed) = fd0 + P(t0 >= g0 AND t1 < g1)
        # So we want P(t1 < g1 | t0 >= g0) * (1 - fd0) <= fdr_target - fd0
        rem_budget = fdr_target - fd0
        cond_target = rem_budget / (1.0 - fd0)
        cond_target = max(min(cond_target, 0.999), 1e-6)
        
        g1 = np.quantile(t1_surv, cond_target)
        
        # Verify actual joint FDR
        joint_dismissal = np.mean((t0_kept < g0) | (t1_kept < g1))
        
        # Evaluate noise pass rates
        noise_pass0 = noise_t0_max >= g0
        p_pass0 = np.mean(noise_pass0)
        p_pass1_joint = np.mean(noise_pass0 & (noise_t1_max >= g1))
        
        exp_cost = cost0 + p_pass0 * cost1 + p_pass1_joint * cost_fine
        
        if joint_dismissal <= fdr_target * 1.10 and exp_cost < best_cost:
            best_cost = exp_cost
            best_res = {
                'gamma0': g0,
                'gamma1': g1,
                'joint_fdr': joint_dismissal,
                'p_pass0': p_pass0,
                'p_pass1': p_pass1_joint,
                'cost': exp_cost,
                'speedup': cost_base / exp_cost
            }
            
    if best_res is None:
        # Fallback to conservative split
        g0 = np.quantile(t0_kept, fdr_target * 0.3)
        g1 = np.quantile(t1_kept, fdr_target * 0.7)
        joint_dismissal = np.mean((t0_kept < g0) | (t1_kept < g1))
        p_pass0 = np.mean(noise_t0_max >= g0)
        p_pass1_joint = np.mean((noise_t0_max >= g0) & (noise_t1_max >= g1))
        exp_cost = cost0 + p_pass0 * cost1 + p_pass1_joint * cost_fine
        best_res = {
            'gamma0': g0,
            'gamma1': g1,
            'joint_fdr': joint_dismissal,
            'p_pass0': p_pass0,
            'p_pass1': p_pass1_joint,
            'cost': exp_cost,
            'speedup': cost_base / exp_cost
        }
            
    print("\n  Optimal Two-Tier Cascade Configuration:")
    print(f"    gamma_0 (m0={m0}):    {best_res['gamma0']:.3f}")
    print(f"    gamma_1 (m1={m1}):    {best_res['gamma1']:.3f}")
    print(f"    Measured joint FDR:   {best_res['joint_fdr']*100:.3f}% (target: {fdr_target*100:.2f}%)")
    print(f"    Noise pass Tier 0:    {best_res['p_pass0']*100:.2f}% (rejection: {(1-best_res['p_pass0'])*100:.2f}%)")
    print(f"    Noise pass to fine:   {best_res['p_pass1']*100:.2f}%")
    print(f"    Expected cost/pair:   {best_res['cost']:.3f} us (vs baseline {cost_base:.3f} us)")
    print(f"    --> NET CASCADE SPEEDUP: {best_res['speedup']:.2f}x")
    
    return best_res


def run_sweep():
    configs = [
        (4096, 256, 1024, 5.5, 0.0010),
        (4096, 256, 1024, 6.0, 0.0010),
        (4096, 256, 1024, 5.5, 0.0100),
        (8192, 256, 2048, 5.5, 0.0010),
        (8192, 512, 2048, 5.5, 0.0010),
    ]
    print("\n" + "=" * 80)
    print(f"{'Config (n, m0, m1, snr, fdr)':<32} | {'g0':<6} | {'g1':<6} | {'Pass T0':<8} | {'Cost':<9} | {'Speedup':<8}")
    print("=" * 80)
    for n, m0, m1, snr, fdr in configs:
        res = simulate_mixture(n, m0, m1, snr, fdr, n_signals=15000, n_noise=30000)
        lbl = f"({n}, {m0}, {m1}, {snr}, {fdr*100:.1f}%)"
        print(f"--> SUMMARY: {lbl:<28} | {res['gamma0']:<6.3f} | {res['gamma1']:<6.3f} | {res['p_pass0']*100:<7.1f}% | {res['cost']:<6.3f} us | {res['speedup']:<6.2f}x")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--sweep':
        run_sweep()
    else:
        simulate_mixture()
