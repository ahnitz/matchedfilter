"""Unit tests verifying the one-sided analytic signal properties and reduced-rate transforms."""

import numpy as np
import pytest
import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank


def _generate_chirp(N, fs, f_low=30.0, f_high=750.0, phase_offset=0.0):
    t = np.arange(N) / fs
    duration = N / fs
    phase = 2.0 * np.pi * (f_low * t + 0.5 * (f_high - f_low) / duration * (t ** 2)) + phase_offset
    return np.cos(phase).astype(np.float32)


def test_analytic_signal_frequency_decimation():
    """Verify that an analytic signal with bandwidth in [20, 800) Hz can be decimated losslessly."""
    N2 = 2048
    N1 = 1024
    fs = 2048.0

    s = _generate_chirp(N2, fs, 30.0, 750.0, 0.0)
    h = _generate_chirp(N2, fs, 30.0, 750.0, 0.3)

    S = np.fft.fft(s)
    H = np.fft.fft(h)

    # Positive-frequency product (analytic matched filter)
    prod2 = np.zeros(N2, dtype=np.complex64)
    k_min = int(round(20.0 * N2 / fs))
    k_max = int(round(800.0 * N2 / fs))
    prod2[k_min:k_max] = S[k_min:k_max] * np.conj(H[k_min:k_max])

    z2048 = np.fft.ifft(prod2)

    # Decimated transform: keep positive bins [0, N1)
    prod1 = prod2[:N1]
    z1024 = np.fft.ifft(prod1)

    # Even samples relation: z2048[2n] == 0.5 * z1024[n]
    diff_even = np.abs(z2048[0::2] - z1024 * 0.5)
    rel_even = np.max(diff_even) / np.max(np.abs(z2048))
    assert rel_even < 1e-6, f"Even sample relative error {rel_even} exceeded 1e-6"

    # Odd samples relation via half-sample phase rotation
    rot = np.exp(1j * 2.0 * np.pi * np.arange(N1) / N2)
    odd_fft = np.fft.ifft(prod1 * rot)
    diff_odd = np.abs(z2048[1::2] - odd_fft * 0.5)
    rel_odd = np.max(diff_odd) / np.max(np.abs(z2048))
    assert rel_odd < 1e-6, f"Odd sample relative error {rel_odd} exceeded 1e-6"


def test_one_sided_spectrum_ingest():
    """Verify that one-sided tap spectrum preserves positive-frequency filter power."""
    N_taps = 2048
    N_engine = 1024
    fs = 2048.0

    taps = _generate_chirp(701, fs, 30.0, 750.0, 0.0)
    buf = np.zeros(N_taps, dtype=np.float32)
    buf[:len(taps)] = taps
    buf = np.roll(buf, -(len(taps) // 2))

    spec2048 = np.fft.fft(buf).astype(np.complex64)

    # Positive frequency power in [20, 800) Hz
    k_max = int(round(800.0 * N_taps / fs))
    power_pos = np.sum(np.abs(spec2048[20:k_max]) ** 2)
    # Corresponding negative frequency bins: N_taps - k for k in [20, k_max)
    neg_indices = N_taps - np.arange(20, k_max)
    power_neg = np.sum(np.abs(spec2048[neg_indices]) ** 2)

    # Real taps have exactly equal power in conjugate negative frequency bins
    np.testing.assert_allclose(power_pos, power_neg, rtol=1e-5)

    # When matched against an analytic series with positive support only,
    # retaining spec2048[:N_engine] captures 100% of the relevant positive frequencies
    spec_onesided = spec2048[:N_engine]
    assert len(spec_onesided) == N_engine
    assert np.allclose(spec_onesided[20:k_max], spec2048[20:k_max])


def test_timedomain_filterbank_analytic_n1024():
    """Verify that TimeDomainFilterBank with analytic=True partitions at N=1024 for 1024 Hz data."""
    fs_taps = 2048.0
    fs_data = 1024.0
    taps = _generate_chirp(350, fs_taps, 30.0, 750.0, 0.0)

    bank = TimeDomainFilterBank(
        [taps], tap_counts=[350],
        tap_sample_rate=fs_taps,
        data_sample_rate=fs_data,
        engine='corr',
        analytic=True
    )

    # Effective tap count in 1024 Hz data samples is ceil(350 / 2) = 175 samples
    # For 175 samples, N=1024 gives valid fraction (1024 - 175) / 1024 = 82.9% >= 50%
    assert bank._groups[0].n == 1024
    filt_f = bank.get_filter_f(0)
    assert len(filt_f) == 1024

    # Correlate a 1024 Hz continuous series
    S = 4096
    t = np.arange(S) / fs_data
    phase = 2.0 * np.pi * (50.0 * t + 0.5 * 100.0 * t**2)
    # Analytic signal (complex exp)
    data = np.exp(1j * phase).astype(np.complex64)

    out = bank.correlate_series(data)
    assert out.shape == (1, S)
    assert not np.all(out == 0)

