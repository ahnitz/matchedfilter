"""Unit and statistical tests for per-template whitened coarse variance equalization."""
import math
import os
import sys
import time
import pathlib

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import gatechain as gc
from spectral_profiles import binomtest


def _locate_tools_dir():
    """Locate repository ``tools/`` directory for the NumPy coarse-pass reference mirror.

    Returns
    -------
    pathlib.Path or None
        Path to ``tools/`` when running from a source checkout, else ``None``.
    """
    here = pathlib.Path(__file__).resolve().parent
    for base in (here.parent, here.parent.parent):
        cand = base / "tools"
        if (cand / "gpu_hier_reference.py").is_file():
            return cand
    return None


_TOOLS_DIR = _locate_tools_dir()
if _TOOLS_DIR is not None and str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
import gpu_hier_reference as hier_ref


def _make_input_psd(n, sample_rate, psd_kind):
    """Build a one-sided length-``n`` per-quadrature input noise PSD array.

    Parameters
    ----------
    n : int
        Full fine FFT block length.
    sample_rate : float
        Sampling rate in Hz.
    psd_kind : str
        ``"white"`` for unit flat PSD or ``"colored_f_minus_2"`` for LIGO-like colored PSD.

    Returns
    -------
    numpy.ndarray
        Float64 array of shape ``(n,)`` positive on ``0 .. n // 2`` and zero above Nyquist.
    """
    psd = np.zeros(n, dtype=np.float64)
    if psd_kind == "white":
        psd[:n // 2 + 1] = 1.0
        return psd

    freqs = np.arange(n, dtype=np.float64) * (sample_rate / float(n))
    f_safe = np.maximum(freqs[:n // 2 + 1], 20.0)
    psd[:n // 2 + 1] = (
        (35.0 / f_safe) ** 6
        + (100.0 / f_safe) ** 2
        + 1.0
        + (f_safe / 180.0) ** 2
    )
    return psd


def _make_heterogeneous_bank(n, nt, sample_rate, bank_kind, psd, seed=101):
    """Construct a heterogeneous unit-variance template bank under ``psd``.

    Parameters
    ----------
    n : int
        Full fine FFT block length.
    nt : int
        Number of templates in the bank.
    sample_rate : float
        Sampling rate in Hz.
    bank_kind : str
        ``"f_final_80_450"`` for cutoffs spanning ``[80, 450] Hz``, ``"exponents_-3.0_-0.5"``
        for power-law slopes spanning ``[-3.0, -0.5]``, or ``"cbc_2048"`` for a realistic
        2048 Hz BBH+NSBH+BNS bank spanning ``[42, 920] Hz``.
    psd : numpy.ndarray
        Length-``n`` per-quadrature noise PSD on ``0 .. n // 2``.
    seed : int, optional
        Random generator seed (default ``101``).

    Returns
    -------
    tuple
        ``(templates, mean_profile)`` where ``templates`` is ``complex64`` of shape ``(nt, n)``
        normalized so ``sum_k psd[k] * |templates[t, k]|^2 == 1`` and ``mean_profile`` is
        ``float32`` of shape ``(n,)``.
    """
    rng = np.random.default_rng(seed)
    freqs = np.arange(n, dtype=np.float64) * (sample_rate / float(n))
    k = np.arange(n, dtype=np.float64)
    templates = np.zeros((nt, n), dtype=np.complex64)

    # Assign per-template cutoff frequencies and spectral slopes by bank family
    if bank_kind == "f_final_80_450":
        f_finals = np.geomspace(80.0, 450.0, nt)
        exponents = np.full(nt, -7.0 / 3.0)
    elif bank_kind == "exponents_-3.0_-0.5":
        f_finals = np.full(nt, 0.44 * sample_rate)
        exponents = np.linspace(-3.0, -0.5, nt)
    elif bank_kind == "cbc_1024":
        n_bbh = max(4, nt * 3 // 16)
        f_finals = np.concatenate([
            np.geomspace(42.0, 85.0, n_bbh),
            np.geomspace(180.0, 480.0, nt - n_bbh),
        ])
        exponents = np.full(nt, -7.0 / 3.0)
    else:
        raise ValueError("unknown bank_kind: %r" % (bank_kind,))

    # Synthesize chirp-phased over-whitened templates normalized against psd
    for t in range(nt):
        mask = (freqs >= 20.0) & (freqs <= f_finals[t]) & (k < n // 2)
        fk = freqs[mask]
        if bank_kind in ("cbc_1024", "f_final_80_450"):
            h_strain = (fk / 100.0) ** (-7.0 / 6.0) / ((30.0 / fk) ** 2 + 1.0)
            amp = np.zeros(n, dtype=np.float64)
            amp[mask] = h_strain / np.maximum(psd[mask], 1e-30)
        else:
            p_t = np.zeros(n, dtype=np.float64)
            p_t[mask] = (fk ** exponents[t]) / ((25.0 / fk) ** 4 + 1.0)
            p_t /= p_t.sum()
            amp = np.sqrt(p_t / np.maximum(psd, 1e-30))
        phase = 18.0 * (t + 1) * (freqs / sample_rate) ** 2 + rng.uniform(0.0, 2.0 * np.pi)
        spec = amp * np.exp(1j * phase)
        norm = math.sqrt(float(np.sum(psd * (spec.real ** 2 + spec.imag ** 2))))
        templates[t] = (spec / norm).astype(np.complex64)

    mean_profile = (
        psd[None, :] * (templates.real.astype(np.float64) ** 2 + templates.imag.astype(np.float64) ** 2)
    ).mean(axis=0)
    mean_profile = (mean_profile / mean_profile.sum()).astype(np.float32)
    return templates, mean_profile


def _draw_colored_blocks(nblocks, n, psd, rng):
    """Draw stationary frequency-domain complex Gaussian noise blocks with variance ``psd``.

    Parameters
    ----------
    nblocks : int
        Number of blocks to generate.
    n : int
        Full fine FFT block length.
    psd : numpy.ndarray
        Length-``n`` per-quadrature variance array.
    rng : numpy.random.Generator
        Random number generator.

    Returns
    -------
    numpy.ndarray
        Complex64 array of shape ``(nblocks, n)``.
    """
    active = psd > 0.0
    k_active = int(np.count_nonzero(active))
    out = np.zeros((nblocks, n), dtype=np.complex64)
    scale = np.sqrt(psd[active])
    draws = (
        rng.standard_normal((nblocks, k_active))
        + 1j * rng.standard_normal((nblocks, k_active))
    ) * scale[None, :]
    out[:, active] = draws.astype(np.complex64)
    return out


def _coarse_grid_series(data_blocks, template_spec, band, scale_frac):
    """Compute normalized complex coarse correlation grid ``(nblocks, band)`` for one template.

    Parameters
    ----------
    data_blocks : numpy.ndarray
        Complex64 frequency-domain blocks of shape ``(nblocks, n)``.
    template_spec : numpy.ndarray
        Complex64 template spectrum of shape ``(n,)`` (or ``(b,)`` centroid spectrum).
    band : int
        Coarse FFT band length.
    scale_frac : float
        Normalization fraction ``f`` applied as ``1 / sqrt(f)``.

    Returns
    -------
    numpy.ndarray
        Complex128 coarse correlation array of shape ``(nblocks, band)``.
    """
    prod = data_blocks[:, :band].astype(np.complex128) * np.conj(
        template_spec[:band].astype(np.complex128)
    )[None, :]
    return np.fft.ifft(prod, axis=1) * (float(band) / math.sqrt(float(scale_frac)))


def test_set_reference_without_input_psd_preserves_shared_scaling(tmp_path, monkeypatch):
    """Verify backward-compatible shared 1/sqrt(ref_f) scaling when set_input_psd is not used."""
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_AUTOTUNE", "0")

    n, nd, nt = 4096, 64, 16
    sample_rate = 1024.0
    psd = _make_input_psd(n, sample_rate, "colored_f_minus_2")
    templates, mean_profile = _make_heterogeneous_bank(
        n, nt, sample_rate, "exponents_-3.0_-0.5", psd, seed=17
    )
    rng = np.random.default_rng(18)
    data = _draw_colored_blocks(nd, n, psd, rng)

    # Confirm shared set_reference leaves heterogeneous coarse noise std spread wide (>1.15 / <0.85)
    ref_f = float(mean_profile[:256].sum())
    shared_stds = [
        float(_coarse_grid_series(data, templates[t], 256, ref_f).real.std())
        for t in range(nt)
    ]
    assert max(shared_stds) > 1.15
    assert min(shared_stds) < 0.85

    # Verify C coarse dump under set_reference matches shared ref_f scaling bit-for-bit
    dump_path = tmp_path / "shared_ref_dump.bin"
    monkeypatch.setenv("MF_HMF_DUMP", str(dump_path))
    hf = mf.HierarchicalFilter(n, ndata=4, ntemplates=nt, snr=5.0, fd=0.01, chain=(256,))
    hf.set_reference(mean_profile)
    hf.set_templates(templates)
    hf.set_data(data[:4])
    hf._ensure()
    hf._mf.set_q15(False)
    hf._q15 = False
    res_shared = hf.run(binsize=n, threshold=5.0)
    k0 = int(hf._mf.band_offsets()[0])
    del hf
    monkeypatch.delenv("MF_HMF_DUMP", raising=False)

    assert dump_path.exists() and dump_path.stat().st_size > 0
    recs = np.frombuffer(dump_path.read_bytes(), dtype=np.float32).reshape(-1, 8)
    f_shared = hier_ref.band_fraction(mean_profile, 256, k0=k0)
    for row in recs:
        d_idx, t_idx = int(row[6]), int(row[7])
        even_max, odd_max = hier_ref.coarse_peak(data[d_idx], templates[t_idx], 256, f_shared, k0=k0)
        assert even_max == pytest.approx(float(row[0]), rel=1e-5)
        if row[1] > 0.0:
            assert odd_max == pytest.approx(float(row[1]), rel=1e-5)

    # Enabling and then clearing set_input_psd(False) restores exact shared set_reference output
    hf_toggle = mf.HierarchicalFilter(
        n, ndata=4, ntemplates=nt, snr=5.0, fd=0.01, chain=(256,)
    )
    hf_toggle.set_reference(mean_profile)
    hf_toggle.set_input_psd(psd.astype(np.float32))
    hf_toggle.set_templates(templates)
    hf_toggle.set_input_psd(False)
    hf_toggle.set_data(data[:4])
    hf_toggle._ensure()
    hf_toggle._mf.set_q15(False)
    hf_toggle._q15 = False
    res_restored = hf_toggle.run(binsize=n, threshold=5.0)
    np.testing.assert_array_equal(res_restored, res_shared)

    # Validate input_psd error checking on invalid shapes, negative bins, NaNs, and zero sum
    with pytest.raises(ValueError):
        hf_toggle.set_input_psd(np.ones(n - 3, dtype=np.float32))
    with pytest.raises(ValueError):
        bad_neg = psd.astype(np.float32).copy()
        bad_neg[10] = -1.0
        hf_toggle.set_input_psd(bad_neg)
    with pytest.raises(ValueError):
        bad_nan = psd.astype(np.float32).copy()
        bad_nan[5] = np.nan
        hf_toggle.set_input_psd(bad_nan)
    with pytest.raises(ValueError):
        hf_toggle.set_input_psd(np.zeros(n, dtype=np.float32))


@pytest.mark.parametrize("bank_kind", ["f_final_80_450", "exponents_-3.0_-0.5"])
@pytest.mark.parametrize("psd_kind", ["white", "colored_f_minus_2"])
def test_per_template_unit_coarse_noise_variance_across_banks(
    bank_kind, psd_kind, tmp_path, monkeypatch
):
    """Every template t has unit coarse noise std (1.00 +- 0.02) on white and colored inputs."""
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_AUTOTUNE", "0")

    n, nd, nt = 4096, 80, 24
    sample_rate = 2048.0
    psd = _make_input_psd(n, sample_rate, psd_kind)
    templates, _ = _make_heterogeneous_bank(n, nt, sample_rate, bank_kind, psd, seed=202)
    rng = np.random.default_rng(303)
    data = _draw_colored_blocks(nd, n, psd, rng)

    # Run CPU FP32 with pinned 1-tier chain and MF_HMF_DUMP to verify C engine 1 / sqrt(f_{t, b}) scaling
    dump_path = tmp_path / ("dump_%s_%s.bin" % (bank_kind, psd_kind))
    monkeypatch.setenv("MF_HMF_DUMP", str(dump_path))
    hf_fp32 = mf.HierarchicalFilter(
        n, ndata=8, ntemplates=nt, snr=5.0, fd=0.01, chain=(256,)
    )
    if psd_kind == "white":
        hf_fp32.set_input_psd()
    else:
        hf_fp32.set_input_psd(psd.astype(np.float32))
    hf_fp32.set_templates(templates)
    hf_fp32.set_data(data[:8])
    hf_fp32._ensure()
    hf_fp32._mf.set_q15(False)
    hf_fp32._q15 = False
    res_fp32 = hf_fp32.run(binsize=n, threshold=5.0)
    k0 = int(hf_fp32._mf.band_offsets()[0])
    del hf_fp32
    monkeypatch.delenv("MF_HMF_DUMP", raising=False)

    assert dump_path.exists() and dump_path.stat().st_size > 0
    recs = np.frombuffer(dump_path.read_bytes(), dtype=np.float32).reshape(-1, 8)
    for row in recs:
        d_idx, t_idx = int(row[6]), int(row[7])
        pow_t = psd * (templates[t_idx].real.astype(np.float64) ** 2 + templates[t_idx].imag.astype(np.float64) ** 2)
        f_t = hier_ref.band_fraction(pow_t, 256, k0=k0)
        even_max, odd_max = hier_ref.coarse_peak(data[d_idx], templates[t_idx], 256, f_t, k0=k0)
        assert even_max == pytest.approx(float(row[0]), rel=1e-5)
        if row[1] > 0.0:
            assert odd_max == pytest.approx(float(row[1]), rel=1e-5)

    # Assert every individual template t in 0..nt-1 has per-quadrature coarse std == 1.00 +- 0.02
    for t_idx in range(nt):
        pow_t = psd * (templates[t_idx].real.astype(np.float64) ** 2 + templates[t_idx].imag.astype(np.float64) ** 2)
        f_t = hier_ref.band_fraction(pow_t, 256, k0=k0)
        even_tmpl, _ = hier_ref.coarse_templates(templates[t_idx], 256, f_t, k0=k0)
        wrapped_data = np.stack([hier_ref._wrap_band(d_row, 256, k0) for d_row in data])
        coarse_z = _coarse_grid_series(wrapped_data, even_tmpl, 256, 1.0)
        assert float(coarse_z.real.std()) == pytest.approx(1.0, abs=0.02)
        assert float(coarse_z.imag.std()) == pytest.approx(1.0, abs=0.02)

    # Verify Q15 mode runs cleanly with set_input_psd and preserves all detections above threshold
    hf_q15 = mf.HierarchicalFilter(n, ndata=8, ntemplates=nt, snr=5.0, fd=0.01)
    if psd_kind == "white":
        hf_q15.set_input_psd()
    else:
        hf_q15.set_input_psd(psd.astype(np.float32))
    hf_q15.set_templates(templates)
    hf_q15.set_data(data[:8])
    res_q15 = hf_q15.run(binsize=n, threshold=5.0)
    assert res_q15.shape == res_fp32.shape


def test_tier0_pair_centroids_and_hermitian_unit_variance_with_input_psd(monkeypatch):
    """Tier-0 pair centroids and Hermitian-packed templates maintain unit coarse noise variance."""
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_AUTOTUNE", "0")

    n, nd, nt = 4096, 80, 24
    band = 256
    sample_rate = 1024.0
    psd = _make_input_psd(n, sample_rate, "colored_f_minus_2")
    rng = np.random.default_rng(404)

    # Construct correlated pairs spanning heterogeneous f_final cutoffs in [80, 450] Hz
    freqs = np.arange(n, dtype=np.float64) * (sample_rate / float(n))
    k = np.arange(n, dtype=np.float64)
    f_finals = np.geomspace(80.0, 450.0, nt // 2)
    templates = np.zeros((nt, n), dtype=np.complex64)
    step_r = n // band
    for pair_idx, ff in enumerate(f_finals):
        mask = (freqs >= 20.0) & (freqs <= ff) & (k < n // 2)
        fk = freqs[mask]
        p_pair = np.zeros(n, dtype=np.float64)
        p_pair[mask] = (fk ** (-7.0 / 3.0)) / ((25.0 / fk) ** 4 + 1.0)
        p_pair /= p_pair.sum()
        amp = np.sqrt(p_pair / np.maximum(psd, 1e-30))
        base_phase = 16.0 * (pair_idx + 1) * (freqs / sample_rate) ** 2 + rng.uniform(0.0, 2.0 * np.pi)
        spec_a = amp * np.exp(1j * base_phase)
        norm_a = math.sqrt(float(np.sum(psd * (spec_a.real ** 2 + spec_a.imag ** 2))))
        templates[2 * pair_idx] = (spec_a / norm_a).astype(np.complex64)

        dl = int((pair_idx % 3 - 1) * (step_r // 2))
        phi0 = rng.uniform(-np.pi, np.pi)
        spec_b = spec_a * (1.0 - 0.08 * (freqs / sample_rate)) * np.exp(1j * phi0 + (2j * np.pi * dl / n) * k)
        norm_b = math.sqrt(float(np.sum(psd * (spec_b.real ** 2 + spec_b.imag ** 2))))
        templates[2 * pair_idx + 1] = (spec_b / norm_b).astype(np.complex64)

    bar_p, _ = gc.compute_psd_template_model(templates, psd, n)
    cl = gc.cluster_tier0_templates(templates, bar_p, n, band, input_psd=psd)
    assert cl is not None
    assert cl.specs.shape == (nt // 2, band)
    assert cl.member_alphas is not None and cl.member_alphas.shape == (nt,)

    # Verify every merged Tier-0 centroid spectrum has coarse noise std == 1.00 +- 0.02
    data = _draw_colored_blocks(nd, n, psd, rng)
    for c_idx in range(cl.specs.shape[0]):
        c_grid = _coarse_grid_series(data, cl.specs[c_idx], band, 1.0)
        assert float(c_grid.real.std()) == pytest.approx(1.0, abs=0.02)
        assert float(c_grid.imag.std()) == pytest.approx(1.0, abs=0.02)

    # Confirm HierarchicalFilter activates Tier-0 pair centroids with set_input_psd in FP32 and Q15
    monkeypatch.setenv("MF_CHAIN_FORCE", "256,1024")
    for use_q15 in (False, True):
        hf = mf.HierarchicalFilter(n, ndata=8, ntemplates=nt, snr=5.5, fd=0.01)
        hf.set_input_psd(psd.astype(np.float32))
        hf.set_templates(templates)
        hf.set_data(data[:8])
        hf._ensure()
        if not use_q15:
            hf._mf.set_q15(False)
            hf._q15 = False
        hf.run(binsize=n, threshold=5.5)
        nc_t0 = hf._mf.tier0_cluster_count()
        assert nt // 4 <= nc_t0 <= nt // 2
        assert hf.work_counts()["checked"][0] == 8 * nc_t0

    # Verify Hermitian-packed (n // 2) real-data mode with two-sided PSD weighting
    psd_two_sided = np.zeros(n, dtype=np.float32)
    psd_two_sided[:n // 2 + 1] = psd[:n // 2 + 1].astype(np.float32)
    psd_two_sided[n // 2 + 1:] = psd[1:n // 2][::-1].astype(np.float32)
    packed_templates = np.ascontiguousarray(templates[:, :n // 2])

    hf_herm = mf.HierarchicalFilter(n, ndata=8, ntemplates=nt, snr=5.5, fd=0.01)
    hf_herm.set_hermitian(True)
    hf_herm.set_input_psd(psd_two_sided[:n // 2 + 1])
    hf_herm.set_templates(packed_templates)
    hf_herm.set_data(data[:8])
    res_herm = hf_herm.run(binsize=n, threshold=5.5)
    assert res_herm.shape == (8, nt, 1)


def test_heterogeneous_bank_survivor_reduction_speedup_and_fdr_compliance(monkeypatch):
    """Per-template PSD normalization cuts survivors >=25%, speeds up filtering, and obeys FDR."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")

    n, nt, nblocks = 4096, 128, 1024
    sample_rate = 1024.0
    snr = 5.0
    fd = 0.01
    psd = _make_input_psd(n, sample_rate, "colored_f_minus_2")
    psd[0] = psd[1]
    psd[n // 2] = 0.0
    templates, mean_profile = _make_heterogeneous_bank(
        n, nt, sample_rate, "cbc_1024", psd, seed=42
    )
    rng = np.random.default_rng(43)
    noise_blocks = _draw_colored_blocks(nblocks, n, psd, rng)

    # Measure survivor counts and warm streaming wall time: shared set_reference vs set_input_psd
    hf_ref = mf.HierarchicalFilter(n, ndata=nblocks, ntemplates=nt, snr=snr, fd=fd)
    hf_ref.set_reference(mean_profile)
    hf_ref.set_templates(templates)
    hf_ref.set_data(noise_blocks)
    hf_ref.run(binsize=n, threshold=snr)
    wc_ref = hf_ref.work_counts()

    hf_psd = mf.HierarchicalFilter(n, ndata=nblocks, ntemplates=nt, snr=snr, fd=fd)
    hf_psd.set_input_psd(psd.astype(np.float32))
    hf_psd.set_templates(templates)
    hf_psd.set_data(noise_blocks)
    hf_psd.run(binsize=n, threshold=snr)
    wc_psd = hf_psd.work_counts()

    # Interleave timed repetitions to cancel background CPU frequency drift
    times_ref = []
    times_psd = []
    for _ in range(9):
        hf_ref.set_data(noise_blocks)
        t0 = time.perf_counter()
        hf_ref.run(binsize=n, threshold=snr)
        times_ref.append((time.perf_counter() - t0) * 1e3)

        hf_psd.set_data(noise_blocks)
        t0 = time.perf_counter()
        hf_psd.run(binsize=n, threshold=snr)
        times_psd.append((time.perf_counter() - t0) * 1e3)

    assert wc_psd["passed"][0] <= 0.82 * wc_ref["passed"][0]
    assert sum(wc_psd["passed"]) <= 0.83 * sum(wc_ref["passed"])
    assert wc_psd["refined"] < wc_ref["refined"]
    assert float(np.median(times_psd)) < float(np.median(times_ref))

    # Also verify >=30% survivor reduction with k<=4 centroids (and >=40% unclustered) at snr=5.5
    hf_ref_55 = mf.HierarchicalFilter(n, ndata=nblocks, ntemplates=nt, snr=5.5, fd=fd)
    hf_ref_55.set_reference(mean_profile)
    hf_ref_55.set_templates(templates)
    hf_ref_55.set_data(noise_blocks)
    hf_ref_55.run(binsize=n, threshold=5.5)

    hf_psd_55 = mf.HierarchicalFilter(n, ndata=nblocks, ntemplates=nt, snr=5.5, fd=fd)
    hf_psd_55.set_input_psd(psd.astype(np.float32))
    hf_psd_55.set_templates(templates)
    hf_psd_55.set_data(noise_blocks)
    hf_psd_55.run(binsize=n, threshold=5.5)
    assert hf_psd_55.work_counts()["passed"][0] <= 0.70 * hf_ref_55.work_counts()["passed"][0]

    # Verify empirical FDR <= fd across 3,840 uniform injections (>2,000 detections) in Q15 & FP32
    inj_snr = 5.5
    batch_b = 64
    n_batches = 60
    flat = mf.MatchedFilter(n, ndata=batch_b, ntemplates=nt)
    flat.set_templates(templates)

    hf_q15 = mf.HierarchicalFilter(n, ndata=batch_b, ntemplates=nt, snr=inj_snr, fd=fd)
    hf_q15.set_input_psd(psd.astype(np.float32))
    hf_q15.set_templates(templates)

    hf_fp32 = mf.HierarchicalFilter(n, ndata=batch_b, ntemplates=nt, snr=inj_snr, fd=fd)
    hf_fp32.set_input_psd(psd.astype(np.float32))
    hf_fp32.set_templates(templates)
    hf_fp32._ensure()
    hf_fp32._mf.set_q15(False)
    hf_fp32._q15 = False

    rng_inj = np.random.default_rng(777)
    k = np.arange(n // 2, dtype=np.float64)
    noise_scale = np.sqrt(psd[:n // 2])
    det = 0
    miss_q15 = 0
    miss_fp32 = 0

    for batch_idx in range(n_batches):
        inj_data = np.zeros((batch_b, n), dtype=np.complex64)
        t_ids = (batch_idx * batch_b + np.arange(batch_b)) % nt
        lags = rng_inj.uniform(0.0, float(n), size=batch_b)
        for j in range(batch_b):
            t_idx = int(t_ids[j])
            sig = (
                inj_snr
                * psd[:n // 2]
                * templates[t_idx, :n // 2]
                * np.exp((-2j * np.pi * lags[j] / float(n)) * k)
            )
            nz = (
                rng_inj.standard_normal(n // 2)
                + 1j * rng_inj.standard_normal(n // 2)
            ) * noise_scale
            inj_data[j, :n // 2] = (sig + nz).astype(np.complex64)

        flat.set_data(inj_data)
        flat_vals = flat.run(binsize=n, threshold=0.0)["value"]
        hf_q15.set_data(inj_data)
        res_q15 = hf_q15.run(binsize=n, threshold=inj_snr)
        hf_fp32.set_data(inj_data)
        res_fp32 = hf_fp32.run(binsize=n, threshold=inj_snr)

        for j in range(batch_b):
            t_idx = int(t_ids[j])
            f_val = complex(flat_vals[j, t_idx, 0])
            if abs(f_val) < inj_snr:
                continue
            det += 1
            pk_q15 = res_q15[j, t_idx, 0]
            if int(pk_q15["index"]) < 0 or abs(complex(pk_q15["value"])) < inj_snr:
                miss_q15 += 1
            else:
                assert abs(complex(pk_q15["value"])) == pytest.approx(abs(f_val), rel=1e-5)

            pk_fp32 = res_fp32[j, t_idx, 0]
            if int(pk_fp32["index"]) < 0 or abs(complex(pk_fp32["value"])) < inj_snr:
                miss_fp32 += 1
            else:
                assert abs(complex(pk_fp32["value"])) == pytest.approx(abs(f_val), rel=1e-5)

    assert det >= 2000
    assert binomtest(miss_q15, det, p=fd, alternative="greater").pvalue >= 1e-3
    assert binomtest(miss_fp32, det, p=fd, alternative="greater").pvalue >= 1e-3


def test_time_domain_filter_bank_input_psd_integration(monkeypatch):
    """TimeDomainFilterBank supports input_psd and set_input_psd without requiring set_reference."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")

    n = 4096
    nt = 64
    tap_len = 512
    sample_rate = 1024.0
    snr = 5.0
    psd_full = _make_input_psd(n, sample_rate, "colored_f_minus_2")
    psd_full[0] = psd_full[1]
    psd_full[n // 2] = 0.0
    psd_rfft = psd_full[:n // 2 + 1].astype(np.float32)
    delta_f = sample_rate / float(n)

    # Build heterogeneous real FIR chirp templates spanning [42, 480] Hz normalized under psd
    templates_f, mean_profile = _make_heterogeneous_bank(
        n, nt, sample_rate, "cbc_1024", psd_full, seed=515
    )
    taps_list = []
    tap_counts = []
    window_fn = np.hanning(tap_len)
    for t_idx in range(nt):
        ir_full = np.fft.irfft(np.conj(templates_f[t_idx, :n // 2 + 1]), n=n)
        centered = np.roll(ir_full, tap_len // 2)[:tap_len] * window_fn
        # Renormalize truncated FIR taps so analytic unit-PSD noise gives unit quadrature std
        buf = np.zeros(n, dtype=np.float64)
        buf[:tap_len] = centered
        spec = np.conj(np.fft.fft(np.roll(buf, -(tap_len // 2))))
        norm = math.sqrt(float(np.sum(psd_full[:n // 2 + 1] * (spec[:n // 2 + 1].real ** 2 + spec[:n // 2 + 1].imag ** 2))))
        taps_list.append((centered / norm).astype(np.float32))
        tap_counts.append(tap_len)

    # Generate continuous one-sided analytic colored noise series matching per-block variance psd
    rng = np.random.default_rng(616)
    series_len = 128 * n
    freqs_ser = np.arange(series_len // 2 + 1, dtype=np.float64) * (sample_rate / float(series_len))
    f_safe_ser = np.maximum(freqs_ser, 20.0)
    psd_ser = (
        (35.0 / f_safe_ser) ** 6
        + (100.0 / f_safe_ser) ** 2
        + 1.0
        + (f_safe_ser / 180.0) ** 2
    )
    spec_ser = np.zeros(series_len, dtype=np.complex128)
    spec_ser[1:series_len // 2] = (
        rng.standard_normal(series_len // 2 - 1)
        + 1j * rng.standard_normal(series_len // 2 - 1)
    ) * np.sqrt(psd_ser[1:series_len // 2] * float(n) * float(series_len))
    series = np.fft.ifft(spec_ser).astype(np.complex64)

    # Compare shared set_reference vs constructor input_psd on TimeDomainFilterBank
    bank_ref = mf.TimeDomainFilterBank(
        taps_list,
        tap_counts=tap_counts,
        tap_sample_rate=sample_rate,
        data_sample_rate=sample_rate,
        engine="hier",
        threshold=snr,
        false_dismissal=0.01,
        fft_lengths=[n],
        pack_templates=False,
    )
    bank_ref.set_reference(mean_profile)
    bank_ref.filter_series(series)
    ref_passed = sum(g.plan.work_counts()["passed"][0] for g in bank_ref._groups)

    for pack in (False, True):
        bank_psd = mf.TimeDomainFilterBank(
            taps_list,
            tap_counts=tap_counts,
            tap_sample_rate=sample_rate,
            data_sample_rate=sample_rate,
            engine="hier",
            threshold=snr,
            false_dismissal=0.01,
            fft_lengths=[n],
            pack_templates=pack,
            input_psd=psd_rfft,
            input_delta_f=delta_f,
        )
        bank_psd.filter_series(series)
        psd_passed = sum(g.plan.work_counts()["passed"][0] for g in bank_psd._groups)
        assert psd_passed <= 0.75 * ref_passed

        # Inject a loud signal for template 5 and verify exact trigger sample and flat SNR match
        inj_series = series.copy()
        inj_sample = 20000
        tap5 = taps_list[5]
        inj_series[inj_sample - tap_len // 2:inj_sample + tap_len // 2] += (
            18.0 / float(np.sum(tap5 * tap5))
        ) * tap5
        res_hier = bank_psd.filter_series(inj_series)
        hit_mask = (res_hier.template_indices == 5) & (np.abs(res_hier.sample_indices - inj_sample) <= 2)
        assert np.any(hit_mask)

    # Also verify set_input_psd("white") works directly without set_reference
    bank_white = mf.TimeDomainFilterBank(
        taps_list[:8],
        tap_counts=tap_counts[:8],
        tap_sample_rate=sample_rate,
        data_sample_rate=sample_rate,
        engine="hier",
        threshold=snr,
        false_dismissal=0.01,
        fft_lengths=[n],
    )
    bank_white.set_input_psd("white")
    white_series = (
        rng.standard_normal(8 * n) + 1j * rng.standard_normal(8 * n)
    ).astype(np.complex64) / math.sqrt(float(n))
    res_w = bank_white.filter_series(white_series)
    assert isinstance(res_w, mf.FilterResults)
