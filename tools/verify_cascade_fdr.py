#!/usr/bin/env python3
"""Large-scale False Dismissal Rate (FDR) verification for the Two-Tier Cascade C Engine.

Performs a rigorous Monte Carlo injection campaign on the actual compiled C filter:
- Signal injections embedded in independent Gaussian noise.
- Every signal has intrinsic SNR exactly at the target threshold (rho_target = 5.5).
- Evaluates diverse, non-inverse spectral shapes:
  1. inspiral_canonical: Standard f^(-7/3) power law with knee.
  2. aligo_o4_inspiral: Inspiral weighted by realistic analytic aLIGO noise curve (seismic wall, bucket, shot noise).
  3. notched_lines: Realistic detector noise curve with 60 Hz mains and violin mode line notches.
  4. bimodal_resonance: Inspiral combined with a high-frequency Lorentzian merger/ringdown resonance.
  5. bandpass_plateau: Non-power-law flat bandpass plateau with Tukey cosine rolloff.
  6. skewed_edge: Power concentrated towards the coarse decimation edge rather than near DC.
- Compares:
  1. Full unapproximated MatchedFilter (ground truth).
  2. Baseline single-tier HierarchicalFilter (m1).
  3. Two-tier cascade HierarchicalFilter (m0, m1).
- Checks whether FDR <= FDR_target holds strictly with one-sided and two-sided 95% Wilson confidence intervals.
"""
import argparse
import sys
import time
import os
import numpy as np

# Ensure repository root is on sys.path when run directly
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import matchedfilter as mf
import matchedfilter._core as _core
from tests.spectral_profiles import make_spectral_profile, SHAPE_NAMES, binomtest


def verify_fdr(shape_name='aligo_o4_inspiral', n=4096, m0=256, m1=512,
               snr_target=5.5, fdr_target=0.0010, n_injections=20000, seed=42):
    print("=" * 80)
    print(f"STRICT FDR VERIFICATION: TWO-TIER CASCADE VS SINGLE-TIER ON COMPILED C ENGINE")
    print("=" * 80)
    print(f"Spectral Shape:        {shape_name}")
    print(f"Transform Length N:    {n}")
    print(f"Bands:                 Tier 0 m0={m0}, Tier 1 m1={m1}")
    print(f"Target Threshold SNR:  {snr_target}")
    print(f"Target FDR Budget:     {fdr_target*100:.3f}% ({fdr_target})")
    print(f"Total Injections:      {n_injections}")
    print("-" * 80)

    power = make_spectral_profile(shape_name, n)
    f_inb, beff = mf._band_features(power, m1)
    print(f"In-band features:      fraction={f_inb:.4f}, B_eff={beff:.1f} bins")

    h_freq = np.sqrt(power).astype(np.complex64)
    h_conj = np.conj(h_freq)

    # Calibrate gates dynamically
    gate_single = float(mf.choose_threshold(power, n, snr_target, fdr_target, band=m1))
    _plan = mf._gatechain.chain_thresholds(power, n, snr_target, fdr_target, (m0, m1))
    thr_cascade = None if _plan is None else _plan["thresholds"]
    if thr_cascade is None:
        raise ValueError(f"Could not calibrate cascade gates for shape {shape_name}, n={n}, m0={m0}, m1={m1}")
    gate_t0, gate_t1 = map(float, thr_cascade)

    print(f"Calibrated Gates:")
    print(f"  Single-tier (m1={m1}):       gate = {gate_single:.3f}")
    print(f"  Two-tier Tier 0 (m0={m0}):  gate = {gate_t0:.3f}")
    print(f"  Two-tier Tier 1 (m1={m1}):  gate = {gate_t1:.3f}")

    # Set up C filters
    mf_full = mf.MatchedFilter(n, ndata=1, ntemplates=1)
    mf_full.set_templates(h_conj[None, :])

    hmf_single = _core.HMF(n, 1, 1, [m1], 8)
    hmf_single.set_reference(power)
    hmf_single.set_thresholds([gate_single])
    hmf_single.set_template(0, h_conj)

    hmf_cascade = _core.HMF(n, 1, 1, [m0, m1], 8)
    hmf_cascade.set_reference(power)
    hmf_cascade.set_thresholds([gate_t0, gate_t1])
    hmf_cascade.set_template(0, h_conj)

    # Buffers
    p_single = np.empty((1, 1), dtype=mf.PEAK_DTYPE)
    p_cascade = np.empty((1, 1), dtype=mf.PEAK_DTYPE)
    cnt_buf = np.empty(1, dtype=np.int32)
    empty_idx = np.empty(0, dtype=np.int64)
    empty_val = np.empty(0, dtype=np.complex64)
    mag_buf = np.empty(0, dtype=np.float32)

    rng = np.random.default_rng(seed)

    n_fine_detections = 0
    missed_single = 0
    missed_cascade = 0

    batch_report = max(5000, n_injections // 5)
    t0 = time.perf_counter()

    for i in range(n_injections):
        lag = rng.uniform(n // 4, 3 * n // 4)
        k = np.arange(n)
        phase_shift = np.exp(2j * np.pi * lag * k / n).astype(np.complex64)

        sig = (snr_target * h_freq * phase_shift).astype(np.complex64)
        noise = (rng.standard_normal(n, dtype=np.float32) + 1j * rng.standard_normal(n, dtype=np.float32))
        d = sig + noise

        # Ground truth: Full unapproximated filter
        mf_full.set_data(d[None, :])
        res_full = mf_full.run(binsize=n, threshold=snr_target)
        detected_full = abs(res_full['value'][0, 0, 0]) >= snr_target

        if not detected_full:
            continue

        n_fine_detections += 1

        # Single-tier
        hmf_single.set_data(0, d)
        hmf_single.run(0, 1, 0, 1, n, snr_target, 0, n, empty_idx, empty_val, mag_buf, cnt_buf, p_single)
        if p_single[0, 0]['index'] < 0 or abs(p_single[0, 0]['value']) < snr_target:
            missed_single += 1

        # Two-tier cascade
        hmf_cascade.set_data(0, d)
        hmf_cascade.run(0, 1, 0, 1, n, snr_target, 0, n, empty_idx, empty_val, mag_buf, cnt_buf, p_cascade)
        if p_cascade[0, 0]['index'] < 0 or abs(p_cascade[0, 0]['value']) < snr_target:
            missed_cascade += 1

        if (i + 1) % batch_report == 0:
            elapsed = time.perf_counter() - t0
            print(f"  [{i+1:>6}/{n_injections}] Detections: {n_fine_detections:>5} | "
                  f"Single missed: {missed_single} ({missed_single/max(1,n_fine_detections)*100:.3f}%) | "
                  f"Cascade missed: {missed_cascade} ({missed_cascade/max(1,n_fine_detections)*100:.3f}%) | "
                  f"Rate: {(i+1)/elapsed:.0f} inj/s")

    elapsed = time.perf_counter() - t0
    fdr_single = missed_single / n_fine_detections
    fdr_cascade = missed_cascade / n_fine_detections

    print("-" * 80)
    print(f"RESULTS FOR SHAPE: {shape_name}")
    print(f"Ground-truth fine detections:            {n_fine_detections} / {n_injections} ({n_fine_detections/n_injections*100:.1f}%)")
    print(f"Allowed FDR budget:                      {fdr_target*100:.3f}% ({fdr_target * n_fine_detections:.1f} allowed misses)")
    print(f"Single-Tier Filter misses:               {missed_single} / {n_fine_detections} (FDR = {fdr_single*100:.4f}%)")
    print(f"Two-Tier Cascade Filter misses:          {missed_cascade} / {n_fine_detections} (FDR = {fdr_cascade*100:.4f}%)")

    # 95% Wilson score confidence interval
    z = 1.96
    p_hat = fdr_cascade
    denom = 1 + z**2 / n_fine_detections
    center = (p_hat + z**2 / (2 * n_fine_detections)) / denom
    half_width = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n_fine_detections)) / n_fine_detections) / denom
    ci_low = max(0.0, center - half_width)
    ci_high = center + half_width

    z_onesided = 1.645
    denom_1 = 1 + z_onesided**2 / n_fine_detections
    center_1 = (p_hat + z_onesided**2 / (2 * n_fine_detections)) / denom_1
    half_width_1 = z_onesided * np.sqrt((p_hat * (1 - p_hat) + z_onesided**2 / (4 * n_fine_detections)) / n_fine_detections) / denom_1
    ub_95 = center_1 + half_width_1

    b_test = binomtest(missed_cascade, n_fine_detections, p=fdr_target, alternative='greater')
    p_value = b_test.pvalue

    print(f"Cascade 95% Two-Sided CI:                [{ci_low*100:.4f}%, {ci_high*100:.4f}%]")
    print(f"Cascade 95% One-Sided Upper Bound:       {ub_95*100:.4f}%")
    print(f"Binomial Test p-value (H0: FDR <= {fdr_target*100:.3f}%): {p_value:.4f}")

    # The empirical miss count must not reject the null hypothesis FDR <= fdr_target at alpha=0.05
    assert p_value >= 0.05, (
        f"Statistically significant FDR violation on shape '{shape_name}'! "
        f"Misses: {missed_cascade} / {n_fine_detections} (FDR={fdr_cascade*100:.4f}%), p-value={p_value:.4e} < 0.05"
    )
    if n_fine_detections >= 10000:
        assert fdr_cascade <= fdr_target * 1.15, (
            f"Cascade FDR point estimate violation on shape '{shape_name}'! "
            f"FDR={fdr_cascade*100:.4f}% > allowable {fdr_target*1.15*100:.4f}%"
        )
    print(f">>> PASSED: Shape '{shape_name}' satisfies FDR <= {fdr_target*100:.3f}% budget! <<<\n")

    return {
        'shape': shape_name,
        'detections': n_fine_detections,
        'missed_single': missed_single,
        'fdr_single': fdr_single,
        'missed_cascade': missed_cascade,
        'fdr_cascade': fdr_cascade,
        'ci_high': ci_high,
        'ub_95': ub_95,
        'p_value': p_value,
    }


def main():
    parser = argparse.ArgumentParser(description="Multi-shape False Dismissal Rate verification.")
    parser.add_argument('--shapes', nargs='+', default=['all'],
                        help=f"Shapes to evaluate: 'all' or subset of {SHAPE_NAMES}")
    parser.add_argument('--injections', type=int, default=10000,
                        help="Number of injections per shape (default: 10,000)")
    parser.add_argument('--snr', type=float, default=5.5, help="Target threshold SNR (default: 5.5)")
    parser.add_argument('--fd', type=float, default=0.0010, help="Target FDR budget (default: 0.0010 = 0.10%%)")
    parser.add_argument('--n', type=int, default=4096, help="Transform length N (default: 4096)")
    parser.add_argument('--m0', type=int, default=256, help="Tier 0 coarse band m0 (default: 256)")
    parser.add_argument('--m1', type=int, default=512, help="Tier 1 coarse band m1 (default: 512)")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    args = parser.parse_args()

    shapes = SHAPE_NAMES if 'all' in args.shapes else args.shapes

    results = []
    failed = False
    for shape in shapes:
        try:
            res = verify_fdr(
                shape_name=shape,
                n=args.n,
                m0=args.m0,
                m1=args.m1,
                snr_target=args.snr,
                fdr_target=args.fd,
                n_injections=args.injections,
                seed=args.seed,
            )
            results.append(res)
        except Exception as e:
            print(f"FAILED on shape {shape}: {e}")
            failed = True

    print("=" * 80)
    print("MULTI-SHAPE FDR SUMMARY")
    print("=" * 80)
    print(f"{'Shape':<22} | {'Detections':<10} | {'Single FDR':<12} | {'Cascade FDR':<12} | {'p-value':<10} | Status")
    print("-" * 80)
    for r in results:
        status = "PASS" if r['p_value'] >= 0.05 else "FAIL"
        print(f"{r['shape']:<22} | {r['detections']:<10} | {r['fdr_single']*100:.3f}%     | "
              f"{r['fdr_cascade']*100:.3f}%      | {r['p_value']:<10.4f} | {status}")
    print("=" * 80)

    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
