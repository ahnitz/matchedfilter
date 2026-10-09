"""Replica isolation test for Stage 1: Top Stage Critical-Rate IFFT.

Validates that evaluating the positive-frequency analytic spectrum [0, N/2)
using an N/2-point IFFT produces the exact even samples of the full-rate
analytic N-point IFFT with < 1e-6 relative difference, and measures the speedup.
"""
import numpy as np
import pytest


@pytest.mark.parametrize("f_high", [400.0, 600.0, 800.0, 1000.0])
def test_top_critical_rate_exact_parity(f_high):
    """Verify that N/2 IFFT matches full N IFFT even samples to float32 precision."""
    sample_rate = 2048.0
    duration = 512.0  # 512-second segment
    N = int(sample_rate * duration)  # 2^20 = 1048576
    K = N // 2  # 2^19 = 524288
    delta_f = 1.0 / duration

    kmin = int(20.0 / delta_f)
    kmax = int(f_high / delta_f)
    assert kmax <= K, f"f_high={f_high} exceeds critical half-band {sample_rate/2} Hz"

    rng = np.random.default_rng(12345)
    # Generate frequency-domain correlation product in active band [kmin, kmax)
    active_len = kmax - kmin
    corr_active = (rng.standard_normal(active_len) + 1j * rng.standard_normal(active_len)).astype(np.complex64)

    # 1. Full-rate N-point IFFT
    Q_full = np.zeros(N, dtype=np.complex64)
    Q_full[kmin:kmax] = corr_active
    q_full = np.fft.ifft(Q_full) * N

    # 2. Critical-rate N/2-point IFFT
    Q_crit = np.zeros(K, dtype=np.complex64)
    Q_crit[kmin:kmax] = corr_active
    q_crit = np.fft.ifft(Q_crit) * K

    # Parity check against even samples
    max_ref = np.max(np.abs(q_full))
    max_diff = np.max(np.abs(q_full[0::2] - q_crit))
    rel_diff = max_diff / max_ref

    assert rel_diff < 1e-6, f"Relative difference {rel_diff:.3e} exceeds 1e-6 at f_high={f_high}"


def test_top_critical_rate_noise_normalization():
    """Verify that critical-rate IFFT preserves exact unit noise variance."""
    N = 1048576
    K = N // 2
    delta_f = 2048.0 / N
    kmin = int(20.0 / delta_f)
    kmax = int(800.0 / delta_f)

    rng = np.random.default_rng(999)
    # Unit Gaussian noise spectrum
    Q_crit = np.zeros(K, dtype=np.complex64)
    n_bins = kmax - kmin
    # Unit normalized flat spectrum
    Q_crit[kmin:kmax] = (rng.standard_normal(n_bins) + 1j * rng.standard_normal(n_bins)).astype(np.complex64)

    q_crit = np.fft.ifft(Q_crit) * (K / np.sqrt(n_bins))

    var_re = np.var(np.real(q_crit))
    var_im = np.var(np.imag(q_crit))

    assert 0.90 < var_re < 1.10, f"Real variance {var_re} not normalized"
    assert 0.90 < var_im < 1.10, f"Imag variance {var_im} not normalized"


def test_top_critical_rate_speedup_benchmark():
    """Benchmark full N vs critical N/2 IFFT on dev2."""
    N = 1048576
    K = N // 2
    rng = np.random.default_rng(42)
    Q_full = np.zeros(N, dtype=np.complex64)
    Q_full[100:int(N*800/2048)] = (rng.standard_normal(int(N*800/2048) - 100) + 1j * rng.standard_normal(int(N*800/2048) - 100)).astype(np.complex64)
    Q_crit = Q_full[:K].copy()

    from conftest import interleaved_speedup
    speedup, t_full, t_crit = interleaved_speedup(lambda: np.fft.ifft(Q_full),
                                                  lambda: np.fft.ifft(Q_crit))
    print(f"\n[Step 1 Benchmark] Full N={N}: {t_full*1000:.2f} ms | Critical N/2={K}: {t_crit*1000:.2f} ms | Speedup: {speedup:.2f}x")
    assert speedup >= 1.5, f"Expected at least 1.5x speedup, got {speedup:.2f}x"
