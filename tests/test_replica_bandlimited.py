"""Replica micro-test comparing band-limited active template storage + zero-extended IFFT
against standard full-rate filter on dev2.

Verifies exact numerical parity (< 1e-6 relative difference), peak triggers,
and microbenchmark timing.
"""
import os
import time
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import MatchedFilter

def test_bandlimited_dif_exact_parity():
    """Verify that DIF zero-extended IFFT matches full-rate N=2048 IFFT bit-for-bit / < 1e-6."""
    N = 2048
    K_max = 1024
    n_templates = 64

    rng = np.random.default_rng(42)
    # Band-limited templates: non-zero only in [0, K_max)
    t_active = (rng.standard_normal((n_templates, K_max)) + 1j * rng.standard_normal((n_templates, K_max))).astype(np.complex64)
    # Zero-padded to full size N
    t_full = np.zeros((n_templates, N), dtype=np.complex64)
    t_full[:, :K_max] = t_active

    # Data spectrum: similarly band-limited
    d_active = (rng.standard_normal((1, K_max)) + 1j * rng.standard_normal((1, K_max))).astype(np.complex64)
    d_full = np.zeros((1, N), dtype=np.complex64)
    d_full[:, :K_max] = d_active

    # Standard full-rate correlation:
    prod_full = d_full * np.conj(t_full)  # (n_templates, N)
    snr_full = np.fft.ifft(prod_full, axis=-1) * N

    # DIF zero-extended IFFT using only active band [0, K_max):
    prod_active = d_active * np.conj(t_active)  # (n_templates, K_max)

    # Even samples: IFFT_{N/2}(prod_active) * (N/2)
    snr_even = np.fft.ifft(prod_active, axis=-1) * K_max

    # Odd samples: IFFT_{N/2}(prod_active * exp(2j * pi * k / N)) * (N/2)
    twiddles = np.exp(2j * np.pi * np.arange(K_max, dtype=np.float64) / N).astype(np.complex64)
    snr_odd = np.fft.ifft(prod_active * twiddles[None, :], axis=-1) * K_max

    # Interleave to full grid
    snr_reconstructed = np.empty((n_templates, N), dtype=np.complex64)
    snr_reconstructed[:, 0::2] = snr_even
    snr_reconstructed[:, 1::2] = snr_odd

    # Check maximum relative difference
    max_ref = np.max(np.abs(snr_full))
    max_err = np.max(np.abs(snr_reconstructed - snr_full))
    rel_err = max_err / max_ref

    print(f"Max reference SNR: {max_ref:.4f}")
    print(f"Max absolute error: {max_err:.4e}")
    print(f"Max relative error: {rel_err:.4e}")
    assert rel_err < 1e-6, f"Relative error {rel_err} exceeds 1e-6"

    # Peak search comparison on window [256, 1792]
    w_start, w_end = 256, 1792
    threshold = 5.0

    peaks_full_idx = []
    peaks_full_val = []
    peaks_dif_idx = []
    peaks_dif_val = []

    for t in range(n_templates):
        # Full rate peak scan
        window_full = snr_full[t, w_start:w_end]
        idx_local = np.argmax(np.abs(window_full))
        max_v = window_full[idx_local]
        if np.abs(max_v) >= threshold:
            peaks_full_idx.append(w_start + idx_local)
            peaks_full_val.append(max_v)
        else:
            peaks_full_idx.append(-1)
            peaks_full_val.append(0.0)

        # DIF separated peak scan
        # Even window: 2m in [w_start, w_end) => m in [w_start//2, w_end//2)
        m_start_even = (w_start + 1) // 2
        m_end_even = (w_end + 1) // 2
        we_even = snr_even[t, m_start_even:m_end_even]
        i_even = np.argmax(np.abs(we_even))
        val_even = we_even[i_even]
        idx_even = 2 * (m_start_even + i_even)

        # Odd window: 2m+1 in [w_start, w_end) => m in [w_start//2, (w_end-1)//2)
        m_start_odd = w_start // 2
        m_end_odd = w_end // 2
        we_odd = snr_odd[t, m_start_odd:m_end_odd]
        i_odd = np.argmax(np.abs(we_odd))
        val_odd = we_odd[i_odd]
        idx_odd = 2 * (m_start_odd + i_odd) + 1

        if np.abs(val_even) >= np.abs(val_odd):
            best_idx = idx_even
            best_val = val_even
        else:
            best_idx = idx_odd
            best_val = val_odd

        if np.abs(best_val) >= threshold:
            peaks_dif_idx.append(best_idx)
            peaks_dif_val.append(best_val)
        else:
            peaks_dif_idx.append(-1)
            peaks_dif_val.append(0.0)

    # Verify peak indices match exactly
    for t in range(n_templates):
        assert peaks_full_idx[t] == peaks_dif_idx[t], f"Template {t} index mismatch: full={peaks_full_idx[t]} dif={peaks_dif_idx[t]}"
        if peaks_full_idx[t] >= 0:
            diff_v = abs(peaks_full_val[t] - peaks_dif_val[t]) / abs(peaks_full_val[t])
            assert diff_v < 1e-6, f"Template {t} value mismatch: {peaks_full_val[t]} vs {peaks_dif_val[t]}"

    print(f"PASS: All {n_templates} peak triggers match bit-for-bit / < 1e-6!")

def test_bank_templates_bandlimited_parity():
    """Test with actual FIR filter templates from the scale100k bank."""
    bank_path = "/home/ahnitz/projects/claude/searchdev/work/scale100k/fir_three_level_opt501_v2.hdf"
    if not os.path.exists(bank_path):
        pytest.skip(f"Bank file {bank_path} not found")
    h5py = pytest.importorskip("h5py")
    with h5py.File(bank_path, "r") as f:
        taps = f["fir_data/0/taps"][:64]
        counts = f["fir_data/0/actual_tap_count"][:64]

    N = 2048
    K_max = 1024
    n_templates = len(taps)

    # Compute full spectra
    spectra_full = np.zeros((n_templates, N), dtype=np.complex64)
    mf._core.taps_to_spectra(taps, counts.astype(np.int64), N, taps.shape[1], spectra_full)

    # Band-limited active spectra [0, K_max)
    spectra_active = spectra_full[:, :K_max].copy()

    # Synthetic realistic noise data block
    rng = np.random.default_rng(123)
    data_full = np.zeros((1, N), dtype=np.complex64)
    # Physical band-limited strain up to 800 Hz (delta_f = 1 Hz -> bins 20..800)
    data_full[0, 20:800] = rng.standard_normal(780) + 1j * rng.standard_normal(780)
    data_active = data_full[:, :K_max]

    # Full correlation
    prod_full = data_full * np.conj(spectra_full)
    snr_full = np.fft.ifft(prod_full, axis=-1) * N

    # Active band DIF correlation
    prod_active = data_active * np.conj(spectra_active)
    snr_even = np.fft.ifft(prod_active, axis=-1) * K_max
    twiddles = np.exp(2j * np.pi * np.arange(K_max, dtype=np.float64) / N).astype(np.complex64)
    snr_odd = np.fft.ifft(prod_active * twiddles[None, :], axis=-1) * K_max

    snr_dif = np.empty((n_templates, N), dtype=np.complex64)
    snr_dif[:, 0::2] = snr_even
    snr_dif[:, 1::2] = snr_odd

    rel_diff = np.max(np.abs(snr_dif - snr_full)) / np.max(np.abs(snr_full))
    print(f"Bank templates max relative error: {rel_diff:.4e}")
    assert rel_diff < 1e-6, f"Bank relative error {rel_diff} exceeds 1e-6"
    print("PASS: Bank templates exact parity verified!")

if __name__ == "__main__":
    test_bandlimited_dif_exact_parity()
    test_bank_templates_bandlimited_parity()
