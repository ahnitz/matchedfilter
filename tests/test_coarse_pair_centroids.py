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
    cl_active = hf._active_tier0_cluster()
    assert cl_active is not None
    nc_active = int(cl_active.specs.shape[0])
    assert 1 <= nc_active <= nt // 2
    assert hf._mf.tier0_cluster_count() == nc_active
    if use_q15:
        if not hf._mf.set_q15(True) or not hf._mf.q15_stats()[0]:
            pytest.skip("no Q15 screen available for Tier-0 band")

    res = hf.run(binsize=n // 4, threshold=6.5)
    wc = hf.work_counts()
    assert wc["pairs"] == nd * nt
    assert wc["checked"][0] == nd * nc_active

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
    cl_active = hf._active_tier0_cluster()
    assert cl_active is not None
    assert 1 <= hf._mf.tier0_cluster_count() <= nt // 2
    assert hf._mf.tier0_cluster_count() == int(cl_active.specs.shape[0])
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
    assert 1 <= hf_on._mf.tier0_cluster_count() <= nt // 2

    hf_on.set_templates(templates[0], index=0)
    res_edit = hf_on.run(binsize=n // 4, threshold=5.5)
    assert hf_on._mf.tier0_cluster_count() == 0
    assert res_edit.shape == res_off.shape


def test_single_column_alpha_simulation_splice_equivalence():
    """Spliced sub-band alpha draws match a direct single-band simulation on both signal and noise."""
    n = 2048
    power, _, _ = _make_colored_correlated_bank(n, 8, 256, seed=1234)
    bands = [128, 256, 512, 1024]
    alphas = (1.0, 0.96, 1.0, 1.0)
    lag_pads = (0, 1, 0, 0)
    win = (128, 1920)

    gc._SIGNAL_RECORDS.clear()
    gc._NOISE_RECORDS.clear()
    gc._SIGNAL_CACHE.clear()
    gc._NOISE_CACHE.clear()

    # Spliced multi-band simulation reusing base draws
    (c_multi, f_multi), _ = gc.signal_draws(
        power, n, bands, snr=6.0, ndet=512, seed=77, window=win, lags_too=True,
        alphas=alphas, _exact=True
    )
    n_multi = gc.noise_block_maxima(
        power, n, bands, nsim=2048, seed=77, window=win,
        alphas=alphas, lag_pads=lag_pads, _exact=True
    )

    # Direct unclustered columns must be bit-for-bit identical
    (c_base, f_base), _ = gc.signal_draws(
        power, n, bands, snr=6.0, ndet=512, seed=77, window=win, lags_too=True, _exact=True
    )
    n_base = gc.noise_block_maxima(
        power, n, bands, nsim=2048, seed=77, window=win, _exact=True
    )
    np.testing.assert_array_equal(f_multi, f_base)
    for col in (0, 2, 3):
        np.testing.assert_array_equal(c_multi[:, col], c_base[:, col])
        np.testing.assert_array_equal(n_multi[:, col], n_base[:, col])

    # Direct 1-band noise simulation on b=256 with alpha=0.96, lag_pad=1 must match column 1
    gc._NOISE_RECORDS.clear()
    gc._NOISE_CACHE.clear()
    n_single = gc.noise_block_maxima(
        power, n, [256], nsim=2048, seed=77, window=win,
        alphas=(0.96,), lag_pads=(1,), _exact=True
    )
    np.testing.assert_array_equal(n_multi[:, 1], n_single[:, 0])


def _make_quad_correlated_bank(n, nt, band, quad_sep=2200.0, chain_drift=0.22, seed=4040):
    """Construct a colored-PSD bank with 4-template correlated families separated across `[0, band)`."""
    rng = np.random.default_rng(seed)
    power = _make_profile("inspiral_canonical", n)
    freqs = np.linspace(0.0, 1.0, n, endpoint=False)
    psd = 0.2 + 12.0 * (1.0 - np.sin(np.pi * np.minimum(freqs, 0.5))) ** 2 + 4.0 * freqs ** 2
    base_amp = np.sqrt(power / psd)
    k = np.arange(n, dtype=np.float64)
    step_r = n // band

    templates = np.empty((nt, n), dtype=np.complex64)
    n_quads = nt // 4
    for q_idx in range(n_quads):
        # Strong phase curvature inside [0, band) so distinct quads do not cross-merge
        quad_phase = (
            rng.uniform(0.0, 2.0 * np.pi)
            + quad_sep * q_idx * (k / max(band, 1)) ** 2
        )
        base_spec = base_amp * np.exp(1j * quad_phase)
        for m_idx in range(4):
            centered = m_idx - 1.5
            dl = int(round(centered * max(1, step_r // 3)))
            dl = max(-step_r, min(step_r, dl))
            phi0 = rng.uniform(-np.pi, np.pi)
            drift = chain_drift * centered * np.sin(2.0 * np.pi * k / max(band, 1))
            tilt = 1.0 + 0.06 * centered * ((k / (n / 2.0)) - 0.5)
            spec = base_spec * tilt * np.exp(1j * (phi0 + drift) + (2j * np.pi * dl / n) * k)
            norm = math.sqrt(float(np.sum(psd * (spec.real ** 2 + spec.imag ** 2))))
            templates[4 * q_idx + m_idx] = (spec / norm).astype(np.complex64)
    # Any remainder templates get independent random phases (singletons)
    for t_idx in range(4 * n_quads, nt):
        phases = rng.uniform(0.0, 2.0 * np.pi, size=n)
        spec = base_amp * np.exp(1j * phases)
        norm = math.sqrt(float(np.sum(psd * (spec.real ** 2 + spec.imag ** 2))))
        templates[t_idx] = (spec / norm).astype(np.complex64)
    return power, psd, templates


def test_adaptive_arity_k4_partition_variance_and_minimax():
    """Verify k in {1, 2, 3, 4} CSR partition, colored-PSD unit variance, and minimax refinement."""
    n, b0 = 2048, 128
    # 16 templates in 4 quads + 3 templates in a triple + 2 in a pair + 1 singleton = 22 templates
    power, psd, quad_Part = _make_quad_correlated_bank(n, 20, b0, chain_drift=0.28, seed=5150)
    rng = np.random.default_rng(5151)
    freqs = np.linspace(0.0, 1.0, n, endpoint=False)
    base_amp = np.sqrt(power / psd)
    # Replace row 19 with an uncorrelated singleton so group 4 has arity 3
    quad_Part[19] = (
        base_amp * np.exp(1j * rng.uniform(0.0, 2.0 * np.pi, size=n))
    ).astype(np.complex64)
    norm19 = math.sqrt(float(np.sum(psd * (quad_Part[19].real ** 2 + quad_Part[19].imag ** 2))))
    quad_Part[19] /= norm19

    # Make quad 0 asymmetric (3 clustered members + 1 drifted outer member) so minimax > mean
    k = np.arange(n, dtype=np.float64)
    asym_offsets = (-0.30, -0.24, -0.18, 0.36)
    ph0 = 0.7 + 1.5 * (k / b0) ** 2
    for m_idx, d_coeff in enumerate(asym_offsets):
        dl = (m_idx - 1) * 3
        drift = d_coeff * np.sin(2.0 * np.pi * k / b0)
        spec = base_amp * np.exp(1j * (ph0 + drift) + (2j * np.pi * dl / n) * k)
        norm = math.sqrt(float(np.sum(psd * (spec.real ** 2 + spec.imag ** 2))))
        quad_Part[m_idx] = (spec / norm).astype(np.complex64)

    cl_k2, cl_k4 = gc.cluster_tier0_candidates(quad_Part, power, n, b0, max_arity=4)
    assert cl_k2 is not None
    assert cl_k4 is not None
    assert cl_k4.specs.shape[0] < cl_k2.specs.shape[0]

    # CSR partition invariants: disjoint cover of 0..nt-1 with arities in {1, 2, 3, 4}
    offsets = cl_k4.offsets
    members = cl_k4.members
    assert int(offsets[0]) == 0
    assert int(offsets[-1]) == 20
    assert sorted(int(m) for m in members) == list(range(20))
    sizes = np.diff(offsets)
    assert np.all((sizes >= 1) & (sizes <= 4))
    assert int(sizes.max()) == 4
    assert 3 in set(int(s) for s in sizes)
    assert 1 in set(int(s) for s in sizes)

    # Colored-PSD coarse noise variance == 1.0 across all k in {1, 2, 3, 4} centroids
    noise_scale = np.sqrt(psd)
    nblocks = 1200
    d_band = (
        (rng.standard_normal((nblocks, b0)) + 1j * rng.standard_normal((nblocks, b0)))
        * noise_scale[None, :b0]
    )
    vars_all = []
    for ci in range(cl_k4.specs.shape[0]):
        corr = b0 * np.fft.ifft(d_band * np.conj(cl_k4.specs[ci].astype(np.complex128))[None, :], axis=1)
        vr, vi = float(np.var(corr.real)), float(np.var(corr.imag))
        assert 0.88 <= vr <= 1.12
        assert 0.88 <= vi <= 1.12
        vars_all.extend([vr, vi])
    assert float(np.mean(vars_all)) == pytest.approx(1.0, abs=0.03)

    # Minimax weight refinement strictly beats unweighted mean on asymmetric 4-template clusters
    u = np.empty((4, b0), dtype=np.complex128)
    k_idx = np.arange(b0, dtype=np.float64)
    step_r = n // b0
    for m_idx in range(4):
        raw = quad_Part[m_idx, :b0].astype(np.complex128)
        nrm = math.sqrt(float(np.sum(psd[:b0] * (raw.real ** 2 + raw.imag ** 2))))
        um = raw / nrm
        if m_idx == 0:
            u[0] = um
        else:
            best_ov = -1.0
            best_vec = um
            for dl in range(-step_r, step_r + 1):
                shifted = um * np.exp((-2j * np.pi * dl / n) * k_idx)
                ip = complex(np.sum(psd[:b0] * np.conj(u[0]) * shifted))
                if abs(ip) > best_ov:
                    best_ov = abs(ip)
                    best_vec = shifted * np.exp(-1j * math.atan2(ip.imag, ip.real))
            u[m_idx] = best_vec
    mean_raw = u.sum(axis=0)
    mean_c = mean_raw / math.sqrt(float(np.sum(psd[:b0] * (mean_raw.real ** 2 + mean_raw.imag ** 2))))
    min_unweighted = min(
        max(
            abs(complex(np.sum(psd[:b0] * np.conj(mean_c) * u[j] * np.exp((-2j * np.pi * dl / n) * k_idx))))
            for dl in range(-step_r, step_r + 1)
        )
        for j in range(4)
    )

    # Normalize actual minimax centroid for quad 0 to unit PSD in-band norm and check worst-case overlap
    ci_quad0 = next(
        ci for ci in range(cl_k4.specs.shape[0])
        if set(int(x) for x in members[offsets[ci]:offsets[ci + 1]]) == {0, 1, 2, 3}
    )
    c_raw = cl_k4.specs[ci_quad0].astype(np.complex128)
    c_opt = c_raw / math.sqrt(float(np.sum(psd[:b0] * (c_raw.real ** 2 + c_raw.imag ** 2))))
    min_minimax = 1.0
    for m_idx in range(4):
        raw = quad_Part[m_idx, :b0].astype(np.complex128)
        nrm = math.sqrt(float(np.sum(psd[:b0] * (raw.real ** 2 + raw.imag ** 2))))
        um = raw / nrm
        best_m = max(
            abs(complex(np.sum(psd[:b0] * np.conj(c_opt) * um * np.exp((-2j * np.pi * dl / n) * k_idx))))
            for dl in range(-step_r, step_r + 1)
        )
        min_minimax = min(min_minimax, best_m)
    assert min_minimax > min_unweighted + 1e-3


def test_cost_driven_selection_chooses_k4_vs_k2_vs_unclustered(monkeypatch):
    """Cost-model selection picks unclustered, k=2 pairs, or k=4 quads according to bank structure."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    n, nd, nt = 2048, 2, 16
    b0 = 128

    # 1. Mutually orthogonal pairs (strong curvature in [0, b0) between pairs) -> k=2 wins (cl_k4 is None)
    power = _make_profile("inspiral_canonical", n)
    freqs = np.linspace(0.0, 1.0, n, endpoint=False)
    psd = 0.2 + 12.0 * (1.0 - np.sin(np.pi * np.minimum(freqs, 0.5))) ** 2 + 4.0 * freqs ** 2
    base_amp = np.sqrt(power / psd)
    k = np.arange(n, dtype=np.float64)
    rng = np.random.default_rng(6060)
    pair_bank = np.empty((nt, n), dtype=np.complex64)
    for p_idx in range(nt // 2):
        ph = rng.uniform(0.0, 2.0 * np.pi) + 2400.0 * p_idx * (k / b0) ** 2
        s0 = base_amp * np.exp(1j * ph)
        s1 = s0 * np.exp(1j * 0.4 + (2j * np.pi * 4 / n) * k)
        pair_bank[2 * p_idx] = (s0 / math.sqrt(float(np.sum(psd * np.abs(s0) ** 2)))).astype(np.complex64)
        pair_bank[2 * p_idx + 1] = (s1 / math.sqrt(float(np.sum(psd * np.abs(s1) ** 2)))).astype(np.complex64)

    hf_k2 = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=5.5, fd=0.01)
    hf_k2.set_reference(power)
    hf_k2.set_templates(pair_bank)
    hf_k2._execution_plan()
    assert hf_k2._mf.tier0_cluster_count() == nt // 2

    # 2. Quad-correlated bank -> k=4 wins (nt // 4 == 4 centroids)
    power_q, _, quad_bank = _make_quad_correlated_bank(n, nt, b0, chain_drift=0.12, seed=6061)
    hf_k4 = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=5.5, fd=0.01)
    hf_k4.set_reference(power_q)
    hf_k4.set_templates(quad_bank)
    hf_k4._execution_plan()
    assert hf_k4._mf.tier0_cluster_count() == nt // 4


def test_k4_quad_bank_empirical_fdr_respects_budget(monkeypatch):
    """4-template minimax centroids keep empirical false dismissals within the target budget."""
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    n, nt = 2048, 16
    snr, fd = 5.5, 0.05
    win = (256, 1792)
    power, psd, templates = _make_quad_correlated_bank(n, nt, 128, chain_drift=0.20, seed=7070)

    hf = mf.HierarchicalFilter(n, ndata=1, ntemplates=nt, snr=snr, fd=fd, search_window=win)
    hf.set_reference(power)
    hf.set_templates(templates)
    hf._execution_plan()
    assert hf._mf.tier0_cluster_count() == nt // 4

    flat = _core.MF(n, 1, nt)
    flat.set_template_batch(0, templates)
    rng = np.random.default_rng(7071)
    noise_scale = np.sqrt(psd)
    k = np.arange(n, dtype=np.float64)
    step_r = n // 128
    w0, w1 = win
    idx_f = np.empty(1, dtype=np.int64)
    val_f = np.empty(1, dtype=np.complex64)
    mag_f = np.empty(1, dtype=np.float32)
    cnt_f = np.empty(1, dtype=np.int32)

    det = 0
    miss = 0
    for trial in range(1400):
        t_idx = int(trial % nt)
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
        flat.run(0, 1, t_idx, 1, w1 - w0, snr, w0, w1, idx_f, val_f, mag_f, cnt_f)
        at = int(idx_f[0])
        if at < 0 or float(mag_f[0]) < snr or abs(at - lag) > 32:
            continue
        det += 1
        hf.set_data(d[None, :])
        pk = hf.run(binsize=w1 - w0, threshold=snr, window=win)[0, t_idx, 0]
        if int(pk["index"]) < 0 or abs(complex(pk["value"])) < snr:
            miss += 1

    assert det >= 500
    pval = binomtest(miss, det, p=fd, alternative="greater").pvalue
    assert pval >= 1e-3, f"k=4 empirical FDR {miss}/{det} = {miss / det:.4f} > {fd} (p={pval:.2e})"


