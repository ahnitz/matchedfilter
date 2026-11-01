"""Unit and statistical false-dismissal tests for Tier-0 coarse template pair centroids."""
import math
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core, _hierarchical
from matchedfilter import gatechain as gc
from spectral_profiles import binomtest, make_spectral_profile


def _make_profile(profile_name, n):
    """Return normalized length-``n`` expected filter-output power profile.

    Parameters
    ----------
    profile_name : str
        Either ``"inspiral_canonical"`` (``k0 == 0``) or ``"deadzone_bandpass"`` (``k0 > 0``).
    n : int
        Full fine FFT block length.

    Returns
    -------
    numpy.ndarray
        Normalized nonnegative float64 profile of shape ``(n,)``.
    """
    if profile_name == "deadzone_bandpass":
        p = np.zeros(n, dtype=np.float64)
        p[160:240] = np.hanning(80) + 0.2
        return p / p.sum()
    p_raw = make_spectral_profile(profile_name, n).astype(np.float64)
    return p_raw / p_raw.sum()


def _make_colored_correlated_bank(n, nt, band, profile_name="inspiral_canonical", seed=2026):
    """Construct a colored PSD and correlated template bank with lag and phase shifts.

    Parameters
    ----------
    n : int
        Full fine FFT block length.
    nt : int
        Number of templates (even count of correlated pairs).
    band : int
        Target Tier-0 coarse band length ``b0``.
    profile_name : str, optional
        Spectral profile name for expected filter-output power (default ``"inspiral_canonical"``).
    seed : int, optional
        Random generator seed (default ``2026``).

    Returns
    -------
    tuple
        ``(power, psd, templates)`` where ``power`` has shape ``(n,)``, ``psd`` has shape
        ``(n,)`` (per-quadrature noise variance per bin), and ``templates`` has shape ``(nt, n)``
        normalized so ``sum_k psd[k] * |templates[t, k]|^2 == 1``.
    """
    rng = np.random.default_rng(seed)
    power = _make_profile(profile_name, n)

    # Strongly colored positive PSD varying by >50x across frequency bins
    freqs = np.linspace(0.0, 1.0, n, endpoint=False)
    psd = 0.2 + 12.0 * (1.0 - np.sin(np.pi * np.minimum(freqs, 0.5))) ** 2 + 4.0 * freqs ** 2

    # Base waveform amplitude matching expected output power = psd * |H|^2
    base_amp = np.sqrt(power / psd)
    k = np.arange(n, dtype=np.float64)
    step_r = n // band

    templates = np.empty((nt, n), dtype=np.complex64)
    for pair_idx in range(nt // 2):
        # Distinct quadratic chirp phase per pair so pairs are mutually well-separated
        chirp_phase = (
            rng.uniform(0.0, 2.0 * np.pi)
            + 28.0 * pair_idx * (k / (n / 2.0)) ** 2
            + 12.0 * pair_idx * (k / (n / 2.0)) ** 3
        )
        base_spec = base_amp * np.exp(1j * chirp_phase)

        # Member A: slight spectral tilt so paired members have distinct in-band fractions
        tilt_a = 1.0 + 0.12 * ((k / (n / 2.0)) - 0.5)
        spec_a = base_spec * tilt_a
        norm_a = math.sqrt(float(np.sum(psd * (spec_a.real ** 2 + spec_a.imag ** 2))))
        templates[2 * pair_idx] = (spec_a / norm_a).astype(np.complex64)

        # Member B: integer fine-lag shift in [-R, +R], global phase rotation, and slight phase drift
        dl = int((pair_idx % 5 - 2) * max(1, step_r // 2))
        dl = max(-step_r, min(step_r, dl))
        phi0 = rng.uniform(-np.pi, np.pi)
        drift = 0.18 * np.sin(2.0 * np.pi * k / max(band, 1))
        tilt_b = 1.0 - 0.10 * ((k / (n / 2.0)) - 0.5)
        spec_b = (
            base_spec
            * tilt_b
            * np.exp(1j * (phi0 + drift) + (2j * np.pi * dl / n) * k)
        )
        norm_b = math.sqrt(float(np.sum(psd * (spec_b.real ** 2 + spec_b.imag ** 2))))
        templates[2 * pair_idx + 1] = (spec_b / norm_b).astype(np.complex64)

    return power, psd, templates


def test_uncorrelated_bank_leaves_tier0_unclustered(monkeypatch):
    """Orthogonal/uncorrelated templates do not cluster and run standard Tier-0 evaluation."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    n, nd, nt = 2048, 4, 16
    rng = np.random.default_rng(101)
    power = _make_profile("inspiral_canonical", n)

    # Independent random phases per bin produce near-zero cross-template coherence
    amp = np.sqrt(power)
    phases = rng.uniform(0.0, 2.0 * np.pi, size=(nt, n))
    templates = (amp[None, :] * np.exp(1j * phases)).astype(np.complex64)

    assert gc.cluster_tier0_templates(templates, power, n, 128) is None

    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    hf = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=5.5, fd=0.01)
    hf.set_reference(power)
    hf.set_templates(templates)
    data = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    hf.set_data(data)
    hf.run(binsize=n // 4, threshold=5.5)

    assert hf._mf.tier0_cluster_count() == 0
    assert hf.work_counts()["checked"][0] == nd * nt


@pytest.mark.parametrize("profile_name", ["inspiral_canonical", "deadzone_bandpass"])
@pytest.mark.parametrize("use_q15", [False, True])
def test_correlated_bank_halves_tier0_work_and_preserves_peaks(profile_name, use_q15, monkeypatch):
    """Correlated pairs merge 2-to-1, halve Tier-0 work, and match flat peak reconstruction."""
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    n, nd, nt = 2048, 6, 16
    chain = (128, 512)
    power, psd, templates = _make_colored_correlated_bank(
        n, nt, chain[0], profile_name=profile_name, seed=303
    )

    # Verify cluster synthesis merges all 8 correlated pairs and pads by 1 coarse lag
    k0 = gc.band_offset(power, n, chain[0])
    if profile_name == "deadzone_bandpass":
        assert k0 > 0
    cl = gc.cluster_tier0_templates(templates, power, n, chain[0], k0=k0)
    assert cl is not None
    assert cl.specs.shape == (nt // 2, chain[0])
    assert cl.lag_pad >= 1
    assert cl.ratio == pytest.approx(0.5)

    # Generate colored noise blocks and inject strong signals into shifted second-member templates
    rng = np.random.default_rng(404)
    noise_scale = np.sqrt(psd)
    data = (
        (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))) * noise_scale[None, :]
    ).astype(np.complex64)
    k = np.arange(n, dtype=np.float64)
    injections = [(0, 1, 500), (2, 7, 1100), (4, 15, 1620)]
    for d_idx, t_idx, arrival_lag in injections:
        data[d_idx] += (
            11.0 * psd * templates[t_idx] * np.exp((-2j * np.pi * arrival_lag / n) * k)
        ).astype(np.complex64)

    flat = mf.MatchedFilter(n, ndata=nd, ntemplates=nt)
    flat.set_templates(templates)
    flat.set_data(data)
    ref = flat.run(binsize=n // 4, threshold=6.5)

    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    hf = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=5.5, fd=1e-3)
    hf.set_reference(power)
    hf.set_templates(templates)
    hf.set_data(data)
    hf._execution_plan()
    assert hf._mf.tier0_cluster_count() == nt // 2
    if use_q15:
        if not hf._mf.set_q15(True) or not hf._mf.q15_stats()[0]:
            pytest.skip("no Q15 screen available for Tier-0 band")

    res = hf.run(binsize=n // 4, threshold=6.5)
    wc = hf.work_counts()
    assert wc["pairs"] == nd * nt
    assert wc["checked"][0] == nd * (nt // 2)

    # Verify all injected peaks are recovered identically to the flat filter
    for d_idx, t_idx, _ in injections:
        got_row = res[d_idx, t_idx]
        ref_row = ref[d_idx, t_idx]
        valid = ref_row["index"] >= 0
        assert valid.any()
        np.testing.assert_array_equal(got_row["index"][valid], ref_row["index"][valid])
        np.testing.assert_allclose(got_row["value"][valid], ref_row["value"][valid], rtol=1e-5, atol=1e-5)

    # Verify sub-slice template execution cleanly syncs and matches unclustered Tier-0 rows
    sub_res = hf.run(binsize=n // 4, threshold=6.5, templates=(1, 7))
    for d_idx, t_idx, _ in [(0, 1, 500), (2, 7, 1100)]:
        got_sub = sub_res[d_idx, t_idx - 1]
        ref_row = ref[d_idx, t_idx]
        valid = ref_row["index"] >= 0
        np.testing.assert_array_equal(got_sub["index"][valid], ref_row["index"][valid])


@pytest.mark.parametrize("profile_name", ["inspiral_canonical", "deadzone_bandpass"])
def test_centroid_coarse_noise_unit_variance(profile_name):
    """Precomputed pair centroids preserve unit per-quadrature coarse noise variance on colored PSDs."""
    n, nt, b0 = 2048, 12, 128
    power, psd, templates = _make_colored_correlated_bank(
        n, nt, b0, profile_name=profile_name, seed=505
    )
    k0 = gc.band_offset(power, n, b0)
    cl = gc.cluster_tier0_templates(templates, power, n, b0, k0=k0)
    assert cl is not None

    # Simulate colored noise spectra (unit per-quadrature variance after template match)
    rng = np.random.default_rng(606)
    nblocks = 1500
    noise_scale = np.sqrt(psd)
    d_full = (rng.standard_normal((nblocks, n)) + 1j * rng.standard_normal((nblocks, n))) * noise_scale[None, :]
    d_band = np.zeros((nblocks, b0), dtype=np.complex128)
    k_lo, k_hi = gc._band_slice(n, b0, k0)
    length = k_hi - k_lo
    if k0 == 0:
        d_band[:, :length] = d_full[:, :length]
    else:
        u0 = k_lo & (b0 - 1)
        first = min(length, b0 - u0)
        if first > 0:
            d_band[:, u0:u0 + first] = d_full[:, k_lo:k_lo + first]
        if length > first:
            d_band[:, :length - first] = d_full[:, k_lo + first:k_hi]

    # Coarse matched filter output in C: b0 * ifft(d_band * conj(spec))
    all_vars = []
    for ci in range(cl.specs.shape[0]):
        prod = d_band * np.conj(cl.specs[ci].astype(np.complex128))[None, :]
        corr = b0 * np.fft.ifft(prod, axis=1)
        var_re = float(np.var(corr.real))
        var_im = float(np.var(corr.imag))
        assert 0.88 <= var_re <= 1.12
        assert 0.88 <= var_im <= 1.12
        all_vars.extend([var_re, var_im])
    assert float(np.mean(all_vars)) == pytest.approx(1.0, abs=0.03)


@pytest.mark.parametrize("use_q15", [False, True])
def test_correlated_bank_fdr_respects_budget_interior_and_edges(use_q15, monkeypatch):
    """Clustered Tier-0 gates respect the false-dismissal budget across interior and window-edge lags."""
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    n, nt = 2048, 16
    snr = 5.5
    fd = 0.05
    chain = (128, 512)
    win = (256, 1792)
    power, psd, templates = _make_colored_correlated_bank(n, nt, chain[0], seed=707)

    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    hf = mf.HierarchicalFilter(
        n, ndata=1, ntemplates=nt, snr=snr, fd=fd, search_window=win
    )
    hf.set_reference(power)
    hf.set_templates(templates)
    hf._execution_plan()
    assert hf._mf.tier0_cluster_count() == nt // 2
    if use_q15:
        if not hf._mf.set_q15(True) or not hf._mf.q15_stats()[0]:
            pytest.skip("no Q15 screen available for Tier-0 band")

    flat = _core.MF(n, 1, nt)
    flat.set_template_batch(0, templates)

    rng = np.random.default_rng(808)
    noise_scale = np.sqrt(psd)
    k = np.arange(n, dtype=np.float64)
    step_r = n // chain[0]
    w0, w1 = win

    idx_f = np.empty(nt, dtype=np.int64)
    val_f = np.empty(nt, dtype=np.complex64)
    mag_f = np.empty(nt, dtype=np.float32)
    cnt_f = np.empty(nt, dtype=np.int32)

    det = 0
    miss = 0
    n_trials = 1600
    for trial in range(n_trials):
        t_idx = int(trial % nt)
        # Half of injections placed near window boundaries [w0 + 2, w0 + 2*R] / [w1 - 2*R, w1 - 2]
        if trial % 4 == 0:
            lag = float(rng.uniform(w0 + 2, w0 + 2 * step_r))
        elif trial % 4 == 1:
            lag = float(rng.uniform(w1 - 2 * step_r, w1 - 2))
        else:
            lag = float(rng.uniform(w0 + 32, w1 - 32))

        sig = snr * psd * templates[t_idx] * np.exp((-2j * np.pi * lag / n) * k)
        noise = (rng.standard_normal(n) + 1j * rng.standard_normal(n)) * noise_scale
        d = (sig + noise).astype(np.complex64)

        flat.set_data(0, d)
        flat.run(0, 1, t_idx, 1, w1 - w0, snr, w0, w1, idx_f[:1], val_f[:1], mag_f[:1], cnt_f[:1])
        at = int(idx_f[0])
        if at < 0 or float(mag_f[0]) < snr or abs(at - lag) > 32:
            continue

        det += 1
        hf.set_data(d[None, :])
        res = hf.run(binsize=w1 - w0, threshold=snr, window=win)
        pk = res[0, t_idx, 0]
        if int(pk["index"]) < 0 or abs(complex(pk["value"])) < snr:
            miss += 1

    assert det >= 600
    # Conservative alpha calibration keeps empirical FDR at or below the target budget
    pval_high = binomtest(miss, det, p=fd, alternative="greater").pvalue
    assert pval_high >= 1e-3, (
        f"empirical FDR {miss}/{det} = {miss / det:.4f} exceeded budget {fd:.3f} (p={pval_high:.2e})"
    )


def test_kill_switch_and_fallback_transitions(monkeypatch):
    """Module kill-switch, pinned chains, explicit thresholds, and single-template edits disable clustering."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    n, nd, nt = 2048, 2, 16
    power, _, templates = _make_colored_correlated_bank(n, nt, 128, seed=909)
    rng = np.random.default_rng(910)
    data = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)

    # 1. Kill switch off disables Tier-0 clustering completely
    monkeypatch.setattr(_hierarchical, "_TIER0_PAIR_CENTROID", False)
    hf_off = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=5.5, fd=0.01)
    hf_off.set_reference(power)
    hf_off.set_templates(templates)
    hf_off.set_data(data)
    res_off = hf_off.run(binsize=n // 4, threshold=5.5)
    assert hf_off._mf.tier0_cluster_count() == 0
    assert hf_off.work_counts()["checked"][0] == nd * nt

    # 2. Pinned chains and explicit coarse thresholds run unclustered per-template Tier 0
    monkeypatch.setattr(_hierarchical, "_TIER0_PAIR_CENTROID", True)
    hf_pin = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, chain=(128, 512), snr=5.5, fd=0.01)
    hf_pin.set_reference(power)
    hf_pin.set_templates(templates)
    hf_pin.set_coarse_threshold((3.5, 4.0))
    hf_pin.set_data(data)
    hf_pin.run(binsize=n // 4, threshold=5.5)
    assert hf_pin._mf.tier0_cluster_count() == 0
    assert hf_pin.work_counts()["checked"][0] == nd * nt

    # 3. Unpinned plans cluster Tier 0; single-row template edits and Hermitian packing revert cleanly
    hf_on = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=5.5, fd=0.01)
    hf_on.set_reference(power)
    hf_on.set_templates(templates)
    hf_on.set_data(data)
    hf_on.run(binsize=n // 4, threshold=5.5)
    assert hf_on._mf.tier0_cluster_count() == nt // 2

    hf_on.set_templates(templates[0], index=0)
    res_edit = hf_on.run(binsize=n // 4, threshold=5.5)
    assert hf_on._mf.tier0_cluster_count() == 0
    assert res_edit.shape == res_off.shape
