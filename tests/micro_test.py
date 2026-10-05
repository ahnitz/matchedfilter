import os
import sys
import time
import numpy as np
import h5py

import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank

def run_test():
    bank_path = "/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/run/fir_three_level_701taps.hdf"
    with h5py.File(bank_path, "r") as f:
        taps = f["fir_data/0/taps"][:64]
        counts = f["fir_data/0/actual_tap_count"][:64]

    ref_w = np.zeros(2048, dtype=np.float32)
    ref_w[20:480] = 1.0

    print("=== Initializing Banks ===")
    b1 = TimeDomainFilterBank(
        taps, counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine='hier', threshold=6.0, execution_rate=1,
    )
    b1.set_reference(ref_w, delta_f=1.0)

    b2 = TimeDomainFilterBank(
        taps, counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine='hier', threshold=6.0, execution_rate=2,
    )
    b2.set_reference(ref_w, delta_f=1.0)

    p1 = b1._groups[0].plan
    p2 = b2._groups[0].plan
    print(f"D=1 Plan: N={p1.n}, coarse_band={p1._mf.config()[0]}, coarse_thr={p1._mf.coarse_threshold(6.0):.3f}")
    print(f"D=2 Plan: N={p2.n}, coarse_band={p2._mf.config()[0]}, coarse_thr={p2._mf.coarse_threshold(6.0):.3f}")

    # --- Test 1: Pure Noise Rejection (131k samples / 64 seconds) ---
    N = 131072
    np.random.seed(42)
    noise = (np.random.randn(N) + 1j * np.random.randn(N)).astype(np.complex64) / (np.sqrt(2.0) * 12000.0)
    valid_slice = slice(2048, N - 2048)

    # Warmup
    b1.filter_series(noise[:8192], valid_slice=slice(2048, 6144))
    b2.filter_series(noise[:8192], valid_slice=slice(2048, 6144))

    print("\n--- Test 1: Pure Noise (N=131072, 64 templates) ---")
    t0 = time.perf_counter()
    res1_noise = b1.filter_series(noise, valid_slice=valid_slice)
    t1_noise = time.perf_counter() - t0

    t0 = time.perf_counter()
    res2_noise = b2.filter_series(noise, valid_slice=valid_slice)
    t2_noise = time.perf_counter() - t0

    print(f"D=1: {t1_noise*1000:.2f} ms, triggers: {len(res1_noise.template_indices)}")
    print(f"D=2: {t2_noise*1000:.2f} ms, triggers: {len(res2_noise.template_indices)}")
    assert len(res1_noise.template_indices) == 0, f"D=1 noise triggers > 0: {len(res1_noise.template_indices)}"
    assert len(res2_noise.template_indices) == 0, f"D=2 noise triggers > 0: {len(res2_noise.template_indices)}"
    assert t2_noise * 1000 < 20.0, f"D=2 runtime exceeded 20 ms: {t2_noise*1000:.2f} ms"
    print("PASS: Pure noise triggers = 0 for both D=1 and D=2, and D=2 runtime <= 20 ms!")

    # --- Test 2: Injected Signal Recovery & Fidelity ---
    print("\n--- Test 2: Injected Signals ---")
    data = noise.copy()
    injections = [
        (5, N // 4, 12.0),
        (12, N // 2, 12.0),
        (20, 3 * N // 4, 12.0),
    ]

    for tmpl_id, inj_samp, target_snr in injections:
        cnt = int(counts[tmpl_id])
        t_arr = taps[tmpl_id, :cnt]
        half = cnt // 2
        s_start = inj_samp - half
        norm_sq = np.sum(t_arr**2)
        signal = (t_arr / norm_sq) * target_snr
        data[s_start : s_start + cnt] += signal

    t0 = time.perf_counter()
    res1 = b1.filter_series(data, valid_slice=valid_slice)
    t1 = time.perf_counter() - t0

    t0 = time.perf_counter()
    res2 = b2.filter_series(data, valid_slice=valid_slice)
    t2 = time.perf_counter() - t0

    print(f"D=1: {t1*1000:.2f} ms, triggers: {len(res1.template_indices)}")
    print(f"D=2: {t2*1000:.2f} ms, triggers: {len(res2.template_indices)}")
    print(f"Speedup: {t1/t2:.2f}x")

    # Check each injection is recovered in D=2
    for tmpl_id, inj_samp, target_snr in injections:
        match_d1 = np.where((res1.template_indices == tmpl_id) & (np.abs(res1.sample_indices - inj_samp) <= 2))[0]
        match_d2 = np.where((res2.template_indices == tmpl_id) & (np.abs(res2.sample_indices - inj_samp) <= 2))[0]
        assert len(match_d1) > 0, f"Injection tmpl={tmpl_id} not recovered in D=1"
        assert len(match_d2) > 0, f"Injection tmpl={tmpl_id} not recovered in D=2"
        snr1 = abs(res1.snr[match_d1[0]])
        snr2 = abs(res2.snr[match_d2[0]])
        diff = abs(snr1 - snr2)
        samp1 = res1.sample_indices[match_d1[0]]
        samp2 = res2.sample_indices[match_d2[0]]
        print(f"Inj tmpl={tmpl_id}: D=1 samp={samp1} SNR={snr1:.3f} | D=2 samp={samp2} SNR={snr2:.3f} | SNR diff={diff:.4f}")
        assert diff < 0.2, f"SNR difference too large: {diff}"

    print("\nALL STANDALONE MICRO-TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    run_test()
