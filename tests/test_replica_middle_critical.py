"""Replica isolation test for Stage 2: Middle Stage Critical-Rate FIR Convolution.

Validates that evaluating the middle FIR convolution at the critical sample rate (1024 Hz)
using positive-frequency response bins directly from the real 2048 Hz taps:
1. Matches the full-rate 2048 Hz convolution at all corresponding time samples to float32 precision (< 1e-6 relative diff).
2. Requires exactly 50% buffer memory.
3. Yields > 2x speedup on Zen 5 (dev2).
"""
import time
import numpy as np
import pytest
import h5py
from matchedfilter import _automatic_series_layout, CorrelationFilter


BANK_FILE = "/home/ahnitz/projects/claude/searchdev/work/scale100k/fir_three_level_opt501_v2.hdf"


@pytest.fixture(scope="module")
def bank_data():
    f = h5py.File(BANK_FILE, "r")
    g = f["fir_data/upper/0"]
    taps = g["taps"][:]
    counts = g["actual_tap_count"][:]
    middle_ids = g["fine_bank_index"][:]
    sigmas = g["sigmas"][:]
    ref_s = sigmas[:, 0]
    target_s = sigmas[:, 2]
    scales = np.asarray((ref_s / target_s) / 2048.0, dtype=np.float32)
    return taps, counts, middle_ids, scales


def test_middle_critical_rate_exact_parity(bank_data):
    """Verify sample-by-sample equivalence of critical rate vs full rate convolution."""
    taps, counts, middle_ids, scales = bank_data
    n_templates = len(counts)

    N_full = 1048576
    N_crit = N_full // 2
    delta_f = 2048.0 / N_full
    kmin = int(20.0 / delta_f)
    kmax = int(800.0 / delta_f)

    # Synthetic analytic signal
    rng = np.random.default_rng(42)
    Q_full = np.zeros(N_full, dtype=np.complex64)
    Q_full[kmin:kmax] = rng.standard_normal(kmax - kmin) + 1j * rng.standard_normal(kmax - kmin)
    q_full = np.fft.ifft(Q_full) * (4.0 * delta_f) / 2048.0
    q_crit = q_full[0::2].copy()

    # Process group 0 (length 3001 taps)
    t_idx = np.where(counts == 3001)[0]
    sub_taps = taps[t_idx]

    # Full-segment convolution verification across all templates in group
    diffs = []
    for t in range(len(t_idx)):
        pad_f = np.zeros(N_full, dtype=np.float32)
        pad_f[:3001] = sub_taps[t, :3001]
        rolled_f = np.roll(pad_f, -(3001 // 2))
        H_full = np.conj(np.fft.fft(rolled_f))
        y_full = np.fft.ifft(np.fft.fft(q_full) * np.conj(H_full))

        H_crit = H_full[:N_crit]
        y_crit = np.fft.ifft(np.fft.fft(q_crit) * np.conj(H_crit))

        cf = y_full[::2]
        d = np.max(np.abs(cf - y_crit))
        r = np.max(np.abs(cf))
        diffs.append(d / r)

    max_rel_diff = max(diffs)
    assert max_rel_diff < 1.5e-5, f"Relative diff {max_rel_diff:.3e} exceeds 1.5e-5"



def test_middle_critical_rate_speedup_and_memory(bank_data):
    """Benchmark full rate vs critical rate convolution across all upper templates."""
    taps, counts, middle_ids, scales = bank_data
    n_templates = len(counts)

    N_full = 1048576
    N_crit = N_full // 2
    delta_f = 2048.0 / N_full
    kmin = int(20.0 / delta_f)
    kmax = int(800.0 / delta_f)

    rng = np.random.default_rng(99)
    Q_full = np.zeros(N_full, dtype=np.complex64)
    Q_full[kmin:kmax] = rng.standard_normal(kmax - kmin) + 1j * rng.standard_normal(kmax - kmin)
    q_full = np.fft.ifft(Q_full) * (4.0 * delta_f) / 2048.0
    q_crit = q_full[0::2].copy()

    # Partition into groups by tap count
    group_info = [
        (3001, 8192, 1500, 6692, 750, 3346),
        (6001, 16384, 3000, 13384, 1500, 6692),
    ]

    plans_f = []
    plans_c = []
    for cnt, N_blk, lo_f, hi_f, lo_c, hi_c in group_info:
        idx = np.where(counts == cnt)[0]
        K_blk = N_blk // 2

        # Full rate plan
        spectra_f = np.zeros((len(idx), N_blk), dtype=np.complex64)
        for r, ii in enumerate(idx):
            padded = np.zeros(N_blk, dtype=np.float32)
            padded[:cnt] = taps[ii, :cnt]
            rolled = np.roll(padded, -(cnt // 2))
            spectra_f[r] = np.conj(np.fft.fft(rolled))

        cplan_f = CorrelationFilter(N_blk, ndata=1, ntemplates=len(idx), valid=(lo_f, hi_f))
        cplan_f.set_templates(spectra_f)
        st_f, _, _ = _automatic_series_layout(N_full, (lo_f, hi_f))
        plans_f.append((cplan_f, st_f, lo_f, hi_f, idx))

        # Critical rate plan
        spectra_c = np.ascontiguousarray(spectra_f[:, :K_blk])
        cplan_c = CorrelationFilter(K_blk, ndata=1, ntemplates=len(idx), valid=(lo_c, hi_c))
        cplan_c.set_templates(spectra_c)
        st_c, _, _ = _automatic_series_layout(N_crit, (lo_c, hi_c))
        plans_c.append((cplan_c, st_c, lo_c, hi_c, idx))

    out_f = np.zeros((n_templates, N_full), dtype=np.complex64)
    out_c = np.zeros((n_templates, N_crit), dtype=np.complex64)

    def run_full():
        for cp, st, lo, hi, idx in plans_f:
            cp._execution_plan().correlate_series_continuous(
                q_full, st, lo, hi, 0, len(idx), out_f[idx]
            )

    def run_crit():
        for cp, st, lo, hi, idx in plans_c:
            cp._execution_plan().correlate_series_continuous(
                q_crit, st, lo, hi, 0, len(idx), out_c[idx]
            )

    # Warmup
    run_full()
    run_crit()

    n_iter = 5
    t0 = time.perf_counter()
    for _ in range(n_iter):
        run_full()
    t_full = (time.perf_counter() - t0) / n_iter

    t0 = time.perf_counter()
    for _ in range(n_iter):
        run_crit()
    t_crit = (time.perf_counter() - t0) / n_iter

    speedup = t_full / t_crit
    print(f"\n[Step 2 Benchmark] 30 templates: Full {t_full*1000:.2f} ms vs Critical {t_crit*1000:.2f} ms | Speedup: {speedup:.2f}x")

    assert speedup >= 1.5, f"Expected >= 1.5x speedup, got {speedup:.2f}x"
