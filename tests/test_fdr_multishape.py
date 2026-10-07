"""Multi-shape False Dismissal Rate (FDR) test suite for the Two-Tier Cascade.

Verifies that the cascade filter maintains empirical False Dismissal Rate
within the target budget (FDR <= 0.10%) across diverse, non-inverse spectral shapes:
1. inspiral_canonical: Standard f^(-7/3) power law with knee.
2. aligo_o4_inspiral: Inspiral weighted by realistic analytic aLIGO noise curve (seismic wall, bucket, shot noise).
3. notched_lines: Realistic detector noise curve with 60 Hz mains and violin mode line notches.
4. bimodal_resonance: Inspiral combined with a high-frequency Lorentzian merger/ringdown resonance.
5. bandpass_plateau: Non-power-law flat bandpass plateau with Tukey cosine rolloff.
6. skewed_edge: Power concentrated towards the coarse decimation edge rather than near DC.
"""
import os
import sys
from pathlib import Path
import zlib
import pytest
import numpy as np

# Ensure repository root is on sys.path
repo_root = str(Path(__file__).resolve().parent.parent)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import matchedfilter as mf
import matchedfilter._core as _core
from tests.spectral_profiles import make_spectral_profile, SHAPE_NAMES, binomtest


@pytest.mark.parametrize("shape_name", SHAPE_NAMES)
def test_cascade_fdr_multi_shape(shape_name):
    """Verify that two-tier cascade FDR <= fdr_target on each distinct spectral shape."""
    n = 4096
    m0, m1 = 256, 512
    snr_target = 5.5
    fdr_target = 0.0010

    # In fast CI/local test mode, use 1,500 injections per shape (~900 detections).
    # In full verification mode, use FDR_INJECTIONS env var (e.g. 10,000 or 20,000).
    n_injections = int(os.environ.get("FDR_INJECTIONS", "1500"))

    power = make_spectral_profile(shape_name, n)
    h_freq = np.sqrt(power).astype(np.complex64)
    h_conj = np.conj(h_freq)

    _plan = mf._gatechain.chain_thresholds(power, n, snr_target, fdr_target, (m0, m1))
    thr_cascade = None if _plan is None else _plan["thresholds"]
    assert thr_cascade is not None, f"Could not calibrate cascade gates for shape {shape_name}"
    g0, g1 = map(float, thr_cascade)

    mf_full = mf.MatchedFilter(n, ndata=1, ntemplates=1)
    mf_full.set_templates(h_conj[None, :])

    hmf_cascade = _core.HMF(n, 1, 1, [m0, m1], 8)
    hmf_cascade.set_reference(power)
    hmf_cascade.set_thresholds([g0, g1])
    hmf_cascade.set_template(0, h_conj)

    p_cascade = np.empty((1, 1), dtype=mf.PEAK_DTYPE)
    cnt_buf = np.empty(1, dtype=np.int32)
    empty_idx = np.empty(0, dtype=np.int64)
    empty_val = np.empty(0, dtype=np.complex64)
    mag_buf = np.empty(0, dtype=np.float32)

    seed = 1234 + (zlib.crc32(shape_name.encode('utf-8')) % 10000)
    rng = np.random.default_rng(seed)

    n_fine_detections = 0
    missed_cascade = 0

    for _ in range(n_injections):
        lag = rng.uniform(n // 4, 3 * n // 4)
        k = np.arange(n)
        phase_shift = np.exp(2j * np.pi * lag * k / n).astype(np.complex64)

        sig = (snr_target * h_freq * phase_shift).astype(np.complex64)
        noise = (rng.standard_normal(n, dtype=np.float32) + 1j * rng.standard_normal(n, dtype=np.float32))
        d = sig + noise

        # Ground truth check
        mf_full.set_data(d[None, :])
        res_full = mf_full.run(binsize=n, threshold=snr_target)
        if abs(res_full['value'][0, 0, 0]) < snr_target:
            continue

        n_fine_detections += 1

        hmf_cascade.set_data(0, d)
        hmf_cascade.run(0, 1, 0, 1, n, snr_target, 0, n, empty_idx, empty_val, mag_buf, cnt_buf, p_cascade)
        if p_cascade[0, 0]['index'] < 0 or abs(p_cascade[0, 0]['value']) < snr_target:
            missed_cascade += 1

    assert n_fine_detections >= int(0.50 * n_injections), (
        f"Expected >= 50% detection rate for SNR {snr_target}, got {n_fine_detections}/{n_injections}"
    )

    # Statistical test: One-sided binomial test asserting FDR <= fdr_target.
    # Deterministic seeding via zlib.crc32 ensures reproducibility across Python processes.
    # With multiple shapes tested concurrently, Bonferroni-corrected alpha bounds family-wise error.
    alpha = 0.05 / len(SHAPE_NAMES)
    b_test = binomtest(missed_cascade, n_fine_detections, p=fdr_target, alternative='greater')
    p_val = b_test.pvalue
    fdr_empirical = missed_cascade / n_fine_detections

    assert p_val >= alpha, (
        f"FDR violation for shape '{shape_name}'! "
        f"Missed: {missed_cascade} / {n_fine_detections} (FDR={fdr_empirical*100:.3f}%), "
        f"Binomial p-value={p_val:.4e} < {alpha:.4f}"
    )


def test_binomtest_does_not_require_scipy(monkeypatch):
    """Verify that binomtest computes correct values even when scipy is unavailable."""
    monkeypatch.setitem(sys.modules, 'scipy', None)
    monkeypatch.setitem(sys.modules, 'scipy.stats', None)

    # Greater: P(X >= 1) for X ~ Binomial(1000, 0.001) is 1 - 0.999^1000
    res = binomtest(1, 1000, p=0.001, alternative='greater')
    expected = 1.0 - (1.0 - 0.001) ** 1000
    assert abs(res.pvalue - expected) < 1e-12

    # P(X >= 0) is always 1.0
    assert binomtest(0, 1000, p=0.001, alternative='greater').pvalue == 1.0

    # Symmetric two-sided
    res2 = binomtest(10, 10, p=0.5, alternative='two-sided')
    assert abs(res2.pvalue - 2.0 * (0.5 ** 10)) < 1e-12

