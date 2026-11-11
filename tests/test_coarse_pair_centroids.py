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




@pytest.mark.parametrize("target_isa", mf.targets())
def test_pair_scores_match_a_direct_evaluation(target_isa):
    """_core.tier0_pair_scores (src/tier0.cc) returns, for every pair a < b of a chunk whose
    variances agree within 15%, the largest |sum_k conj(U_a) U_b S_s|^2 over the shifts and the
    first shift reaching it; every other entry is 0. A chunk of 21 templates is not a whole
    number of vectors on any target, so the padding is exercised too."""
    mf.set_target(target_isa)
    try:
        rng = np.random.default_rng(77)
        mc, L, R = 21, 96, 3
        U = (rng.standard_normal((mc, L)) + 1j * rng.standard_normal((mc, L))) / np.sqrt(2 * L)
        U[1::3] = 0.95 * U[0] + 0.05 * U[1::3]                   # a few strongly coherent pairs
        U[5] *= 1.5                                               # variance 2.25x: never scored
        dls = np.arange(-R, R + 1)
        order = np.argsort(np.abs(dls), kind="stable")
        S = np.exp(-2j * np.pi * dls[order, None] * np.arange(L)[None, :] / (L * R))
        v = np.sum(np.abs(U) ** 2, axis=1)
        Ur, Ui = (np.ascontiguousarray(x, np.float32) for x in (U.real, U.imag))
        Sr, Si = (np.ascontiguousarray(x, np.float32) for x in (S.real, S.imag))
        r2 = np.full((mc, mc), -7.0, np.float32)
        bs = np.full((mc, mc), -7, np.int32)
        _core.tier0_pair_scores(Ur, Ui, Sr, Si, v.astype(np.float64), r2, bs)
    finally:
        mf.set_target(None)

    U64 = Ur.astype(np.float64) + 1j * Ui
    S64 = Sr.astype(np.float64) + 1j * Si
    G = np.abs(np.einsum("ak,sk,bk->sab", U64.conj(), S64, U64)) ** 2
    for a in range(mc):
        for b in range(mc):
            scored = b > a and min(v[a], v[b]) >= 0.85 * max(v[a], v[b])
            if not scored:
                assert r2[a, b] == 0 and bs[a, b] == 0, (a, b)
                continue
            g = G[:, a, b]
            assert r2[a, b] == pytest.approx(g.max(), rel=1e-5), (a, b)
            # the first shift reaching the largest score, wherever the largest is clear
            top = np.sort(g)[-2:]
            if top[1] - top[0] > 1e-4 * top[1]:
                assert bs[a, b] == int(np.argmax(g)), (a, b)


def test_pass2_runs_only_when_asked_and_a_skipped_one_is_built_later(monkeypatch):
    """cluster_tier0_candidates asks pass2 with the k <= 2 bank before Pass 2 and skips Pass 2
    when told; a filter that skipped it on the chain choice's bound builds the k <= 4 bank when
    asked again without one, as a direct call would."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    n, nt, b0 = 2048, 16, 128
    power, _, bank = _make_quad_correlated_bank(n, nt, b0, chain_drift=0.12, seed=6061)
    full = gc.cluster_tier0_candidates(bank, power, n, b0, max_arity=4)
    assert full[0] is not None and full[1] is not None
    seen = []
    k2, k4 = gc.cluster_tier0_candidates(bank, power, n, b0, max_arity=4,
                                         pass2=lambda cl: seen.append(cl) or False)
    assert k4 is None and len(seen) == 1 and seen[0] is k2
    np.testing.assert_array_equal(k2.members, full[0].members)

    hf = mf.HierarchicalFilter(n, ndata=2, ntemplates=nt, snr=5.5, fd=0.01)
    hf.set_reference(power)
    hf.set_templates(bank)
    hf._tier0_cand_cache = {}             # set_templates chose a chain, which built them all
    assert hf._tier0_candidates_for_band(b0, pass2=lambda cl: False)[1] is None
    again = hf._tier0_candidates_for_band(b0)
    assert again[1] is not None
    np.testing.assert_array_equal(again[1].members, full[1].members)
    np.testing.assert_array_equal(again[1].specs, full[1].specs)


@pytest.mark.parametrize("target_isa", mf.targets())
@pytest.mark.parametrize("half_span", [0, 3, 7])
def test_tier0_refine_lags_matches_numpy_reference(target_isa, half_span):
    """_core.tier0_refine_lags matches the exact complex128 shifted inner-product search across
    interior and [-R, +R] boundary-clipped coarse lag guesses across all SIMD targets."""
    rng = np.random.default_rng(9090 + half_span)
    npairs, length, R = 29, 99, 16
    prod_ab = rng.standard_normal((npairs, length)) + 1j * rng.standard_normal((npairs, length))
    prod_ab = np.ascontiguousarray(prod_ab, dtype=np.complex128)
    dls_all = np.arange(-R, R + 1, dtype=np.float64)
    k_vec = np.arange(length, dtype=np.float64)
    exp_all = np.ascontiguousarray(
        np.exp((-2j * np.pi / (length * R)) * dls_all[:, None] * k_vec[None, :]),
        dtype=np.complex128,
    )
    pdl = rng.integers(-R, R + 1, size=npairs, dtype=np.int64)
    pdl[:4] = np.array([-R, -R + 1, R - 1, R], dtype=np.int64)

    out_dl = np.full(npairs, -999, dtype=np.int64)
    out_g = np.zeros(npairs, dtype=np.complex128)
    mf.set_target(target_isa)
    try:
        _core.tier0_refine_lags(prod_ab, exp_all, pdl, R, half_span, out_dl, out_g)
    finally:
        mf.set_target(None)

    if half_span == 0:
        ref_dl = pdl.copy()
        ref_g = np.einsum("ij,ij->i", prod_ab, exp_all[pdl + R])
    else:
        ref_abs = np.full(npairs, -1.0, dtype=np.float64)
        ref_dl = pdl.copy()
        ref_g = np.zeros(npairs, dtype=np.complex128)
        for off_val in range(-half_span, half_span + 1):
            cdl = np.clip(pdl + off_val, -R, R)
            g_cur = np.einsum("ij,ij->i", prod_ab, exp_all[cdl + R])
            abs_cur = np.abs(g_cur)
            better = abs_cur > ref_abs
            ref_abs = np.where(better, abs_cur, ref_abs)
            ref_dl = np.where(better, cdl, ref_dl)
            ref_g = np.where(better, g_cur, ref_g)

    np.testing.assert_array_equal(out_dl, ref_dl)
    np.testing.assert_allclose(out_g, ref_g, rtol=1e-13, atol=1e-13)


@pytest.mark.parametrize("use_q15", [False, True])
@pytest.mark.parametrize("use_direct", [False, True])
def test_single_tier_chain_centroids_fft_and_direct_refine(use_q15, use_direct, monkeypatch):
    """Single-tier CPU chains (e.g. (256,) at n=1024) cluster Tier 0 and recover exact flat-filter
    peaks under both whole-block FFT refine and direct time-domain refine."""
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_DIRECT_REFINE", "1" if use_direct else "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "1024:256")
    n, nblocks, nt, tap_len = 1024, 4, 16, 129
    b0 = 256
    rng = np.random.default_rng(31415 + int(use_direct) * 17 + int(use_q15) * 31)

    # Build 4 quad families of compact complex64 time-domain FIR taps sharing positive-band power
    taps = np.zeros((nt, tap_len), dtype=np.complex64)
    idx_t = np.arange(tap_len, dtype=np.float64) - tap_len // 2
    env = np.hanning(tap_len)
    for q in range(nt // 4):
        f0 = 0.08
        chirp = 0.0004 * ((q % 2) * 2 - 1)
        cubic = 0.000008 * (q - 1.5)
        base = env * np.exp(2j * np.pi * (f0 * idx_t + chirp * idx_t ** 2 + cubic * idx_t ** 3))
        for m in range(4):
            shift = m - 1
            rolled = np.zeros(tap_len, dtype=np.complex128)
            src_lo = max(0, -shift)
            src_hi = min(tap_len, tap_len - shift)
            rolled[src_lo + shift : src_hi + shift] = base[src_lo:src_hi] * np.exp(0.15j * m)
            rolled /= np.linalg.norm(rolled)
            taps[4 * q + m] = rolled.astype(np.complex64)

    from matchedfilter.time_domain import template_spectra
    counts = np.full(nt, tap_len, dtype=np.int64)
    filt, _ = template_spectra(taps, counts, n)
    templates = np.conj(filt).astype(np.complex64)
    power = np.mean(np.abs(templates.astype(np.complex128)) ** 2, axis=0)
    power /= power.sum()

    # Build continuous complex series with loud injections in shifted non-anchor members
    step = n // 2
    nseries = (nblocks - 1) * step + n
    series = ((rng.standard_normal(nseries) + 1j * rng.standard_normal(nseries)) / np.sqrt(2.0)).astype(
        np.complex64
    )
    starts = np.arange(nblocks, dtype=np.int64) * step
    ws = np.full(nblocks, 128, dtype=np.int64)
    we = np.full(nblocks, n - 128, dtype=np.int64)
    injections = [(0, 3, 340), (2, 11, 610)]
    for b_idx, t_idx, lag in injections:
        pos = int(starts[b_idx]) + lag - tap_len // 2
        series[pos : pos + tap_len] += (11.5 * taps[t_idx]).astype(np.complex64)

    flat = mf.MatchedFilter(n, ndata=nblocks, ntemplates=nt)
    flat.set_templates(templates)
    ref = flat.run_series(series, starts=starts, win_start=ws, win_end=we,
                          binsize=n - 256, threshold=6.5)

    hf = mf.HierarchicalFilter(n, ndata=nblocks, ntemplates=nt, snr=5.5, fd=1e-2,
                               search_window=(128, n - 128))
    hf.set_reference(power)
    hf.set_templates(templates)
    if use_direct:
        hf.set_taps(taps, counts)
    hf._execution_plan()
    assert tuple(hf._chain) == (b0,)
    cl_active = hf._active_tier0_cluster()
    assert cl_active is not None
    nc_active = int(cl_active.specs.shape[0])
    assert 1 <= nc_active <= nt // 2
    assert hf._mf.tier0_cluster_count() == nc_active
    if use_q15:
        hf._set_q15(True)
        if not hf._q15:
            pytest.skip("no Q15 screen available for Tier-0 band")
    else:
        hf._set_q15(False)

    got = hf.run_series(series, starts=starts, win_start=ws, win_end=we,
                        binsize=n - 256, threshold=6.5)
    wc = hf.work_counts()
    assert wc["checked"][0] == nblocks * nc_active
    if use_direct and hf._resolve().direct_hw is not None:
        assert hf.direct_stats()["pairs"] > 0

    for b_idx, t_idx, _ in injections:
        got_pk = got[b_idx, t_idx, 0]
        ref_pk = ref[b_idx, t_idx, 0]
        assert int(ref_pk["index"]) >= 0
        assert int(got_pk["index"]) == int(ref_pk["index"])
        np.testing.assert_allclose(got_pk["value"], ref_pk["value"], rtol=2e-4, atol=2e-4)


@pytest.mark.parametrize("use_q15", [False, True])
def test_single_tier_centroid_fdr_and_lower_bound(use_q15, monkeypatch):
    """Single-tier clustered chains respect the false-dismissal budget across interior and
    window-edge lags and satisfy pair_cost_lower_bound <= chosen cost."""
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    n, nt = 1024, 16
    snr = 5.5
    fd = 0.05
    chain = (256,)
    win = (128, 896)
    power, psd, templates = _make_colored_correlated_bank(n, nt, chain[0], seed=1707)

    # Verify pair_cost_lower_bound <= chosen 1-tier clustered cost
    cm = gc.CostModel(
        n=n,
        dense={64: 10.0, 128: 16.0, 256: 24.0, 512: 40.0},
        sparse={b: [(1e-3, 18.0), (1e-1, 14.0)] for b in (64, 128, 256, 512)},
        refine=[(1e-4, 95.0), (1e-2, 85.0)],
    ).with_tier0_cluster({256: 0.25}, single_tier=True)
    best, _ = gc.choose_chain(
        power, n, snr=snr, fd=fd, ntemplates=nt, cost=cm, max_tiers=3,
        window=win, tier0_clusters={256: (0.97, 1)}
    )
    lb = gc.pair_cost_lower_bound(power, n, snr, fd, cost=cm, window=win)
    assert lb <= best["cost"] + 1e-9

    monkeypatch.setenv("MF_CHAIN_FORCE", "256")
    hf = mf.HierarchicalFilter(n, ndata=1, ntemplates=nt, snr=snr, fd=fd, search_window=win)
    hf.set_reference(power)
    hf.set_templates(templates)
    hf._execution_plan()
    assert tuple(hf._chain) == chain
    cl_active = hf._active_tier0_cluster()
    assert cl_active is not None
    assert 1 <= hf._mf.tier0_cluster_count() <= nt // 2
    if use_q15:
        if not hf._mf.set_q15(True) or not hf._mf.q15_stats()[0]:
            pytest.skip("no Q15 screen available for Tier-0 band")

    flat = _core.MF(n, 1, nt)
    flat.set_template_batch(0, templates)

    rng = np.random.default_rng(1808 + int(use_q15))
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
    for trial in range(1200):
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

    assert det >= 450
    pval_high = binomtest(miss, det, p=fd, alternative="greater").pvalue
    assert pval_high >= 1e-3, (
        f"empirical 1-tier FDR {miss}/{det} = {miss / det:.4f} exceeded budget {fd:.3f} (p={pval_high:.2e})"
    )


@pytest.mark.parametrize("chain_str", ["256", "256,512", "256,512,1024"])
@pytest.mark.parametrize("use_q15", [False, True])
def test_clustered_tier0_preserves_sparse_c_order_across_interleaved_clusters(
    monkeypatch, chain_str, use_q15
):
    """When multiple Tier-0 clusters with interleaved member indices (e.g. [0, 15], [1, 14], ...)
    fire on the same block, run_series_batch_sparse and FilterResults emit peaks in strict
    (block, template, bin) C-order matching an unclustered reference bank. On a three-tier
    chain the Tier-1 sub-centroids (interleaved too) take the sparse path as well."""
    from matchedfilter.benchmark import _inspiral_power
    from matchedfilter.time_domain import template_spectra

    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", chain_str)
    n, nt, L = 2048, 16, 323
    counts = np.full(nt, L, dtype=np.int64)
    taps = np.zeros((nt, L), dtype=np.complex64)
    # Place correlated pairs at non-adjacent indices (k, nt - 1 - k) with distinct chirp slopes
    # between pairs so Tier-0 clustering merges interleaved non-contiguous row indices.
    for k in range(nt // 2):
        for side, ti in enumerate((k, nt - 1 - k)):
            w = np.zeros(L, dtype=np.complex128)
            w[L // 2] = np.exp(1j * (0.4 * k + 0.03 * side))
            w += 0.14 * np.hanning(L) * np.exp(1j * np.linspace(0, 1.5 + 0.6 * k + 0.02 * side, L)) / np.sqrt(L)
            taps[ti] = w.astype(np.complex64)
    filt, _ = template_spectra(taps, counts, n)
    templates = np.conj(filt)

    ref = _inspiral_power(n).copy()
    ref[n // 2 :] = 0.0
    total = 32768
    p1 = _inspiral_power(total).copy()
    p1[total // 2 :] = 0.0
    p1 /= p1.sum()
    rng = np.random.default_rng(3010)
    W = np.fft.rfft(rng.standard_normal(total))
    S_freq = np.zeros_like(W)
    S_freq[: total // 2] = W[: total // 2] * np.sqrt(p1[: total // 2] * total)
    x = np.fft.irfft(S_freq, n=total)
    x = (x / np.std(x)).astype(np.float64)
    pulse = np.real(np.fft.ifft(p1) * total) * 2.0
    for tau in (4500, 9200, 15100, 21800):
        x += 10.0 * np.roll(pulse, tau)
    x = x.astype(np.float32)

    b_cl = mf.TimeDomainFilterBank(
        taps, counts, tap_sample_rate=2048.0, data_sample_rate=2048.0,
        threshold=6.0, false_dismissal=1e-2, binsize=512, fft_lengths=(n,)
    )
    b_cl.set_reference(ref)
    grp = [g for g in b_cl._groups if g.is_hier][0]
    grp.plan._execution_plan()
    if grp.plan._mf.tier0_cluster_count() == 0:
        # Force clustering on interleaved rows via set_tier0_clusters so C-order is exercised on all ISAs
        k0 = int(gc.band_offset(ref, n, 256))
        cl = gc.tier0_pair_centroids(templates, ref, 256, k0=k0)
        assert cl is not None
        assert any(
            int(cl.offsets[c + 1] - cl.offsets[c]) >= 2
            and int(cl.members[cl.offsets[c + 1] - 1] - cl.members[cl.offsets[c]]) > 1
            for c in range(cl.specs.shape[0])
        )
        grp.plan._mf.set_tier0_clusters(cl.specs, cl.offsets, cl.members, int(cl.lag_pad))
    if chain_str.count(",") == 2:
        assert grp.plan._mf.tier1_cluster_count() > 0
    if use_q15:
        if not grp.plan._mf.set_q15(True) or not grp.plan._mf.q15_stats()[0]:
            pytest.skip("no Q15 screen available for Tier-0 band")
    else:
        grp.plan._mf.set_q15(False)

    monkeypatch.setenv("MF_TIER0_CENTROIDS", "0")
    b_ref = mf.TimeDomainFilterBank(
        taps, counts, tap_sample_rate=2048.0, data_sample_rate=2048.0,
        threshold=6.0, false_dismissal=1e-2, binsize=512, fft_lengths=(n,)
    )
    b_ref.set_reference(ref)
    if use_q15:
        for g in b_ref._groups:
            if g.is_hier:
                g.plan._execution_plan().set_q15(True)

    r_cl = b_cl.filter_series(x, windows=slice(2048, 28672))
    r_ref = b_ref.filter_series(x, windows=slice(2048, 28672))
    assert len(r_cl.template_indices) >= 16
    np.testing.assert_array_equal(r_cl.template_indices, r_ref.template_indices)
    np.testing.assert_array_equal(r_cl.sample_indices, r_ref.sample_indices)
    np.testing.assert_allclose(r_cl.snr, r_ref.snr, rtol=2e-5, atol=2e-4)


def test_finer_alpha_quantization_preserves_high_retention_thresholds():
    """Verify _pack_cluster quantizes Tier-0 retention alpha on a 1/200 (0.005) grid rather than
    1/50 (0.02), keeping >=0.995 retentions above 0.98 and raising Tier-0 thresholds to cut
    Tier-1 survivor reach."""
    n, nt, b0 = 2048, 16, 128
    power, _, templates = _make_quad_correlated_bank(n, nt, b0, chain_drift=0.14, seed=8282)
    cl_k2, cl_k4 = gc.cluster_tier0_candidates(templates, power, n, b0, max_arity=4)
    assert cl_k2 is not None and cl_k4 is not None
    assert cl_k2.alpha > 0.98
    assert cl_k4.alpha >= 0.99

    pl_fine = gc.chain_thresholds(power, n, 5.5, 0.01, (128, 512), tier0_cluster=cl_k4)
    pl_coarse = gc.chain_thresholds(
        power, n, 5.5, 0.01, (128, 512), tier0_cluster=(0.98, cl_k4.lag_pad)
    )
    assert pl_fine is not None and pl_coarse is not None
    assert pl_fine["thresholds"][0] > pl_coarse["thresholds"][0]
    assert pl_fine["reach"][1] < pl_coarse["reach"][1]


def _tier1_bank(n=2048, nt=16, b0=128, b1=512, chain_drift=0.06, seed=9201, power_ratio=1.0):
    """A quad bank whose quads Tier 0 merges to k <= 4 and Tier 1 splits into coherent pairs:
    (power, psd, templates, cl0, cl1 kwargs). power_ratio scales the odd members' amplitude by
    sqrt(power_ratio) (a member weighted variance ratio of power_ratio)."""
    power, psd, templates = _make_quad_correlated_bank(n, nt, b1, chain_drift=chain_drift, seed=seed)
    if power_ratio != 1.0:
        templates = templates.copy()
        templates[1::2] *= np.float32(math.sqrt(power_ratio))
    k0_0 = int(gc.band_offset(power, n, b0))
    cl0 = gc.cluster_tier0_templates(templates, power, n, b0, k0=k0_0, max_arity=4)
    return power, psd, templates, cl0


def _cluster_of(cl):
    out = np.empty(int(cl.members.size), dtype=np.int64)
    for c in range(cl.offsets.size - 1):
        out[cl.members[cl.offsets[c]:cl.offsets[c + 1]]] = c
    return out


def test_tier1_sub_centroids_nest_hold_the_floor_and_match_an_independent_retention():
    """cluster_tier1_from_tier0: a partition nested inside the Tier-0 clusters, merging some
    pairs; every merged member's retention -- recomputed here over every fine lag the centroid's
    padded window reaches, from the band vectors -- is at least alpha_min and at least what the
    builder reports; alpha is the smallest member retention."""
    n, b1 = 2048, 512
    power, _, templates, cl0 = _tier1_bank(n=n, b1=b1)
    assert cl0 is not None and cl0.specs.shape[0] < templates.shape[0]
    k0 = int(gc.band_offset(power, n, b1))
    cl1 = gc.cluster_tier1_from_tier0(templates, power, n, cl0, b1, k0=k0)
    assert cl1 is not None
    nt = templates.shape[0]
    assert sorted(cl1.members.tolist()) == list(range(nt))
    assert cl1.offsets[0] == 0 and cl1.offsets[-1] == nt and np.all(np.diff(cl1.offsets) >= 1)
    sizes = np.diff(cl1.offsets)
    assert np.all(sizes <= 2) and np.any(sizes == 2)
    assert cl0.specs.shape[0] <= cl1.specs.shape[0] < nt
    c0 = _cluster_of(cl0)
    for c in range(cl1.offsets.size - 1):
        assert len(set(c0[cl1.members[cl1.offsets[c]:cl1.offsets[c + 1]]])) == 1

    # Independent retention at every fine lag within the centroid's reach
    p = gc._norm_profile(power.astype(np.float32), n)
    k_lo, k_hi = gc._band_slice(n, b1, k0)
    H = templates[:, k_lo:k_hi].astype(np.complex128) / math.sqrt(p[k_lo:k_hi].sum())
    m_bin = np.mean(np.abs(templates[:, k_lo:k_hi].astype(np.complex128)) ** 2, axis=0)
    W = p[k_lo:k_hi] / np.maximum(m_bin, 1e-6 * m_bin.max())
    k = np.arange(k_lo, k_hi)
    R = n // b1
    reach = min(R, cl1.lag_pad * R)
    u0 = k_lo & (b1 - 1)
    length = k_hi - k_lo
    for c in np.flatnonzero(sizes == 2):
        spec = cl1.specs[c].astype(np.complex128)
        cvec = np.concatenate([spec[u0:u0 + min(length, b1 - u0)], spec[:max(0, length - (b1 - u0))]]) \
            if k0 > 0 else spec[:length]
        v_c = float(np.sum(W * np.abs(cvec) ** 2))
        for t in cl1.members[cl1.offsets[c]:cl1.offsets[c + 1]]:
            v_t = float(np.sum(W * np.abs(H[t]) ** 2))
            ov = max(abs(np.sum(W * cvec.conj() * H[t] * np.exp(-2j * np.pi * tau * k / n)))
                     for tau in range(-reach, reach + 1))
            a_t = min(1.0, ov / v_t)
            assert a_t >= gc.TIER1_ALPHA_MIN - 1e-4
            assert a_t >= float(cl1.member_alphas[t]) - 2e-4
            assert v_c == pytest.approx(0.5 * (v_t + float(np.sum(W * np.abs(H[[m for m in cl1.members[cl1.offsets[c]:cl1.offsets[c + 1]] if m != t][0]]) ** 2))), rel=1e-3)
    assert cl1.alpha <= float(np.min(cl1.member_alphas)) + 1e-9
    assert cl1.alpha >= gc.TIER1_ALPHA_MIN - 1e-3


def test_tier1_floor_splits_pairs_whose_members_lose_too_much():
    """Members with unequal power lose sqrt(v_avg / v_t) at a shared centroid: with a 0.88
    weighted variance ratio no pair keeps the 0.995 floor and none merges, while a lower floor
    merges them and reports the loss."""
    n, b1 = 2048, 512
    power, _, templates, cl0 = _tier1_bank(n=n, b1=b1, power_ratio=0.88)
    assert cl0 is not None
    k0 = int(gc.band_offset(power, n, b1))
    assert gc.cluster_tier1_from_tier0(templates, power, n, cl0, b1, k0=k0) is None
    loose = gc.cluster_tier1_from_tier0(templates, power, n, cl0, b1, k0=k0, alpha_min=0.9)
    assert loose is not None
    merged = loose.members[np.repeat(np.diff(loose.offsets), np.diff(loose.offsets)) == 2]
    assert merged.size > 0
    assert float(np.min(loose.member_alphas[merged])) < gc.TIER1_ALPHA_MIN
    assert loose.alpha == pytest.approx(float(np.min(loose.member_alphas)), abs=1e-3)


@pytest.mark.parametrize("profile_name", ["inspiral_canonical", "deadzone_bandpass"])
def test_tier1_centroid_coarse_noise_unit_variance(profile_name):
    """Tier-1 sub-centroid spectra, as packed for the C plan (wrapped slots when k0 > 0), keep
    unit per-quadrature coarse noise variance on a coloured PSD, as single templates do."""
    n, b0 = 2048, 128
    rng = np.random.default_rng(3131)
    power, psd, templates = _make_colored_correlated_bank(n, 16, b0, profile_name=profile_name, seed=3132)
    # Second members re-made as near-copies of the first so Tier 1 (b1 = 256) merges the pairs
    templates = templates.copy()
    templates[1::2] = templates[0::2] * np.exp(1j * rng.uniform(-np.pi, np.pi, (8, 1))).astype(np.complex64)
    b1 = 256
    k0_0, k0_1 = int(gc.band_offset(power, n, b0)), int(gc.band_offset(power, n, b1))
    if profile_name == "deadzone_bandpass":
        k0_1 = max(k0_1, 136)                       # exercise the wrapped packing
    cl0 = gc.cluster_tier0_templates(templates, power, n, b0, k0=k0_0, max_arity=2)
    assert cl0 is not None
    cl1 = gc.cluster_tier1_from_tier0(templates, power, n, cl0, b1, k0=k0_1)
    assert cl1 is not None and np.any(np.diff(cl1.offsets) == 2)
    k_lo, k_hi = gc._band_slice(n, b1, k0_1)
    length = k_hi - k_lo
    d_full = (rng.standard_normal((1500, n)) + 1j * rng.standard_normal((1500, n))) * np.sqrt(psd)[None, :]
    d_band = np.zeros((1500, b1), dtype=np.complex128)
    if k0_1 == 0:
        d_band[:, :length] = d_full[:, :length]
    else:
        u0 = k_lo & (b1 - 1)
        first = min(length, b1 - u0)
        d_band[:, u0:u0 + first] = d_full[:, k_lo:k_lo + first]
        if length > first:
            d_band[:, :length - first] = d_full[:, k_lo + first:k_hi]
    for c in range(cl1.specs.shape[0]):
        corr = b1 * np.fft.ifft(d_band * np.conj(cl1.specs[c].astype(np.complex128))[None, :], axis=1)
        assert 0.88 <= float(np.var(corr.real)) <= 1.12
        assert 0.88 <= float(np.var(corr.imag)) <= 1.12


def test_chain_thresholds_model_the_tier1_retention():
    """chain_thresholds' tier1_cluster: a lossless Tier-1 bank plans exactly as none, a lossy
    one lowers the Tier-1 threshold (it applies only with a Tier-0 bank)."""
    n = 2048
    power = _make_profile("inspiral_canonical", n)
    chain = (128, 512, 1024)
    base = gc.chain_thresholds(power, n, 5.5, 0.01, chain, tier0_cluster=(0.99, 1))
    same = gc.chain_thresholds(power, n, 5.5, 0.01, chain, tier0_cluster=(0.99, 1),
                               tier1_cluster=(1.0, 0))
    lossy = gc.chain_thresholds(power, n, 5.5, 0.01, chain, tier0_cluster=(0.99, 1),
                                tier1_cluster=(0.95, 1))
    alone = gc.chain_thresholds(power, n, 5.5, 0.01, chain, tier1_cluster=(0.95, 1))
    plain = gc.chain_thresholds(power, n, 5.5, 0.01, chain)
    assert base is not None and same is not None and lossy is not None
    assert list(same["thresholds"]) == list(base["thresholds"])
    assert lossy["thresholds"][1] < base["thresholds"][1]
    assert list(alone["thresholds"]) == list(plain["thresholds"])


def test_hmf_tier1_cluster_api_validates_and_nests():
    """HMF.set_tier1_clusters needs Tier-0 clusters, a partition, nesting inside them and a lag
    padding below the band; clearing or replacing the Tier-0 clusters, a template, the
    reference or the band offsets drops the Tier-1 ones."""
    n, nt, b0, b1 = 2048, 8, 128, 512
    h = _core.HMF(n, 1, nt, [b0, b1])
    rng = np.random.default_rng(5)
    h.set_reference(np.ascontiguousarray(_make_profile("inspiral_canonical", n), dtype=np.float32))
    tm = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    h.set_template_batch(0, tm)
    i32 = lambda x: np.asarray(x, dtype=np.int32)
    s0 = np.zeros((4, b0), np.complex64)
    off0, mem0 = i32([0, 2, 4, 6, 8]), i32([0, 1, 2, 3, 4, 5, 6, 7])
    s1 = lambda nc: (rng.standard_normal((nc, b1)) + 0j).astype(np.complex64)
    off1, mem1 = i32([0, 2, 3, 4, 6, 7, 8]), i32([0, 1, 2, 3, 4, 5, 6, 7])

    assert not h.set_tier1_clusters(s1(6), off1, mem1, 0)           # no Tier-0 clusters
    assert h.set_tier0_clusters(s0, off0, mem0, 0)
    assert not h.set_tier1_clusters(s1(5), i32([0, 1, 3, 4, 6, 8]), mem1, 0)    # [1, 2] crosses
    assert not h.set_tier1_clusters(s1(6), off1, i32([0, 1, 2, 2, 4, 5, 6, 7]), 0)  # duplicate
    assert not h.set_tier1_clusters(s1(6), i32([0, 2, 2, 4, 6, 7, 8]), mem1, 0)  # empty cluster
    assert not h.set_tier1_clusters(s1(6), off1, mem1, b1)            # lag_pad >= m1
    with pytest.raises(ValueError):
        h.set_tier1_clusters(s1(5), off1, mem1, 0)                     # specs of the wrong size
    assert h.tier1_cluster_count() == 0

    def attach():
        assert h.set_tier0_clusters(s0, off0, mem0, 0)
        assert h.set_tier1_clusters(s1(6), off1, mem1, 1)
        assert h.tier1_cluster_count() == 6

    attach()
    h.clear_tier0_clusters()
    assert h.tier0_cluster_count() == 0 and h.tier1_cluster_count() == 0
    attach()
    assert h.set_tier0_clusters(s0, off0, mem0, 0)                     # replaced: Tier 1 dropped
    assert h.tier1_cluster_count() == 0
    attach()
    h.set_template(3, tm[3])
    assert h.tier1_cluster_count() == 0
    h.set_template_batch(0, tm)
    attach()
    h.set_reference(np.ascontiguousarray(_make_profile("deadzone_bandpass", n), dtype=np.float32))
    assert h.tier1_cluster_count() == 0
    h.set_template_batch(0, tm)
    attach()
    h.set_band_offsets([8, 8])
    assert h.tier1_cluster_count() == 0
    attach()
    h.clear_tier1_clusters()
    assert h.tier1_cluster_count() == 0 and h.tier0_cluster_count() == 4


@pytest.mark.parametrize("chain", [(128, 512), (128, 512, 1024)])
@pytest.mark.parametrize("use_q15", [False, True])
def test_tier1_sub_centroids_cut_tier1_work_and_preserve_triggers(chain, use_q15, monkeypatch):
    """HierarchicalFilter attaches Tier-1 sub-centroids inside its Tier-0 clusters (Tier 1 last
    or not), plans Tier 1 at their retention, evaluates fewer Tier-1 pairs than without them,
    and reports exactly the flat filter's triggers -- for the whole bank and for a template
    sub-slice (which runs Tier 1 unclustered)."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", ",".join(map(str, chain)))
    n, nt, nd = 2048, 16, 8
    power, psd, templates, cl0 = _tier1_bank(n=n, b1=chain[1])
    rng = np.random.default_rng(9202)
    data = ((rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n)))
            * np.sqrt(psd)[None, :]).astype(np.complex64)
    k = np.arange(n, dtype=np.float64)
    for d_idx, t_idx, lag in [(0, 1, 350), (2, 6, 900), (5, 13, 1450), (7, 10, 640)]:
        data[d_idx] += (9.5 * psd * templates[t_idx] * np.exp((-2j * np.pi * lag / n) * k)).astype(np.complex64)

    flat = mf.MatchedFilter(n, ndata=nd, ntemplates=nt, device="cpu")
    flat.set_templates(templates)
    flat.set_data(data)
    ref = flat.run(binsize=256, threshold=6.0)

    hf = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=6.0, fd=1e-3, device="cpu")
    hf.set_reference(power)
    hf.set_templates(templates)
    hf.set_data(data)
    plan = hf._execution_plan()
    assert tuple(hf._chain) == chain
    cl0, cl1 = hf._active_tier0_cluster(), hf._active_tier1_cluster()
    assert cl0 is not None and cl1 is not None
    assert plan.tier0_cluster_count() == cl0.specs.shape[0]
    assert plan.tier1_cluster_count() == cl1.specs.shape[0] < nt
    want = gc.chain_thresholds(power, n, 6.0, 1e-3, chain, cost=hf._cost_model(),
                               window=hf.search_window, tier0_cluster=cl0,
                               tier1_cluster=cl1)["thresholds"]
    np.testing.assert_allclose(hf._resolve().thresholds, want, rtol=1e-6)
    if use_q15 and (not plan.set_q15(True) or not plan.q15_stats()[0]):
        pytest.skip("no Q15 screen for this chain on this target")
    plan.set_q15(use_q15)
    # Low thresholds so every block fires at Tier 0 and Tier 1 sees whole clusters
    plan.set_thresholds([0.5] + list(hf._resolve().thresholds[1:]))

    out = hf.run(binsize=256, threshold=6.0)
    np.testing.assert_array_equal(out["index"], ref["index"])
    hit = ref["index"] >= 0
    np.testing.assert_allclose(out["value"][hit], ref["value"][hit], rtol=1e-5, atol=1e-5)
    with_t1 = plan.tier_inputs()[1]

    sub = hf.run(binsize=256, threshold=6.0, templates=(3, 9))
    np.testing.assert_array_equal(sub["index"], ref["index"][:, 3:12])
    assert plan.tier1_cluster_count() == cl1.specs.shape[0]

    plan.clear_tier1_clusters()
    out0 = hf.run(binsize=256, threshold=6.0)
    np.testing.assert_array_equal(out0["index"], ref["index"])
    assert with_t1 < plan.tier_inputs()[1]


def test_no_tier1_sub_centroids_where_a_direct_refine_elects_tier1_lags(monkeypatch):
    """With taps on a two-tier chain the direct refine elects each survivor's own Tier-1 lag:
    no Tier-1 sub-centroids are attached or planned there."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    n, nt = 2048, 16
    power, _, templates, _ = _tier1_bank(n=n, b1=512)
    hf = mf.HierarchicalFilter(n, ndata=1, ntemplates=nt, snr=6.0, fd=1e-3, device="cpu")
    hf.set_reference(power)
    hf.set_templates(templates)
    assert hf._active_tier1_cluster() is not None
    hf.set_taps(np.ones((nt, 33), np.float32))
    plan = hf._execution_plan()
    assert hf._active_tier1_cluster() is None
    assert plan.tier1_cluster_count() == 0
