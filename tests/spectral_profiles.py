"""Spectral power profiles for False Dismissal Rate (FDR) and cascade filter verification.

Provides diverse, non-inverse spectral shapes:
1. inspiral_canonical: Standard f^(-7/3) power law with low-frequency knee.
2. aligo_o4_inspiral: Inspiral weighted by realistic analytic aLIGO noise curve (seismic wall, bucket, shot noise).
3. notched_lines: Realistic detector noise curve with 60 Hz mains and violin mode line notches.
4. bimodal_resonance: Inspiral combined with a high-frequency Lorentzian merger/ringdown resonance.
5. bandpass_plateau: Non-power-law flat bandpass plateau with Tukey cosine rolloff.
6. skewed_edge: Power concentrated towards the coarse decimation edge rather than near DC.
"""
import numpy as np


SHAPE_NAMES = [
    'inspiral_canonical',
    'aligo_o4_inspiral',
    'notched_lines',
    'bimodal_resonance',
    'bandpass_plateau',
    'skewed_edge',
]


def make_spectral_profile(shape_name, n):
    """Generate normalized one-sided reference power profile (|h|^2 / S_n)."""
    p = np.zeros(n, dtype=np.float32)
    k = np.arange(1, n // 2, dtype=np.float64)
    nyq = n // 2

    if shape_name == 'inspiral_canonical':
        knee = max(2.0, 0.0150 * n)
        p[1:nyq] = (k ** (-7.0 / 3.0) / ((knee / k) ** 4 + 1.0)).astype(np.float32)

    elif shape_name == 'aligo_o4_inspiral':
        # Inspiral weighted by analytic aLIGO noise PSD:
        # Sn(x) ~ x^(-14) [seismic wall] + 1.0 [thermal/radiation bucket] + x^2 [optical shot noise]
        x = k / max(1.0, 0.08 * nyq)
        sn = x ** (-14) + 1.0 + x ** 2
        p[1:nyq] = (k ** (-7.0 / 3.0) / sn).astype(np.float32)

    elif shape_name == 'notched_lines':
        # aLIGO noise-weighted inspiral with narrow line notches (simulating 60 Hz mains and violin modes)
        x = k / max(1.0, 0.08 * nyq)
        sn = x ** (-14) + 1.0 + x ** 2
        p_raw = k ** (-7.0 / 3.0) / sn
        n1 = max(1, int(0.04 * nyq))
        n2 = max(1, int(0.08 * nyq))
        p_raw[max(0, n1 - 2):n1 + 3] *= 0.01
        p_raw[max(0, n2 - 2):n2 + 3] *= 0.01
        p[1:nyq] = p_raw.astype(np.float32)

    elif shape_name == 'bimodal_resonance':
        # Inspiral base plus high-frequency Lorentzian merger/ringdown resonance
        x = k / max(1.0, 0.08 * nyq)
        sn = x ** (-14) + 1.0 + x ** 2
        p_raw = k ** (-7.0 / 3.0) / sn
        res_bin = int(0.20 * nyq)
        lorentzian = 1.0 / (1.0 + ((k - res_bin) / 8.0) ** 2)
        p_raw += 0.05 * p_raw.max() * lorentzian
        p[1:nyq] = p_raw.astype(np.float32)

    elif shape_name == 'bandpass_plateau':
        # Non-power-law: flat bandpass plateau with Tukey cosine taper edges
        k_lo = int(0.02 * nyq)
        k_hi = int(0.20 * nyq)
        plateau = np.zeros(len(k), dtype=np.float64)
        w = max(2.0, 0.2 * (k_hi - k_lo))
        for i, ki in enumerate(k):
            if k_lo <= ki <= k_hi:
                if ki < k_lo + w:
                    plateau[i] = 0.5 * (1 - np.cos(np.pi * (ki - k_lo) / w))
                elif ki > k_hi - w:
                    plateau[i] = 0.5 * (1 + np.cos(np.pi * (ki - (k_hi - w)) / w))
                else:
                    plateau[i] = 1.0
        p[1:nyq] = plateau.astype(np.float32)

    elif shape_name == 'skewed_edge':
        # Power rises towards the coarse band edge, stressing decimation aliasing
        peak_bin = int(0.12 * nyq)
        p_raw = (k / peak_bin) ** 2.0 * np.exp(-((k - peak_bin) / (0.05 * nyq)) ** 2)
        p[1:nyq] = p_raw.astype(np.float32)

    else:
        raise ValueError(f"Unknown spectral shape: {shape_name}. Available: {SHAPE_NAMES}")

    tot = float(p.sum())
    if tot <= 0:
        raise ValueError(f"Profile {shape_name} has non-positive sum: {tot}")
    return p / tot
