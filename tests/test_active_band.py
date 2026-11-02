"""Tests for contiguous active-band [k0, k0 + B) cyclic slot wrapping.

When a reference signal-power profile has zero or negligible weight below a
seismic or bandpass low-frequency cutoff, coarse FFT tiers anchored at DC cover
few or zero active bins. Wrapping fine bins k in [k0, min(k0 + B, n // 2)) into
cyclic slots u = k & (B - 1) makes a standard B-point backward FFT evaluate the
exact narrowband correlation at every coarse lag l * (n // B) with zero twiddles
and zero coarse-kernel modifications.
"""

import pathlib
import sys

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank, _core, gatechain
from matchedfilter._gpuhier import CLAIMS
from matchedfilter.time_domain import template_spectra
from conftest import usable_gpu, usable_gpu_reason
from test_api import inspiral_power, noise, template_with_power


def _seismic_wall_power(n, f_low_hz=25.0, sample_rate_hz=2048.0, exponent=-7.0 / 3.0):
    """Build a normalized one-sided inspiral signal-power profile with a low-frequency cutoff.

    Parameters
    ----------
    n : int
        Fine FFT length.
    f_low_hz : float, optional
        Low-frequency cutoff in Hz below which signal power vanishes (default 25.0).
    sample_rate_hz : float, optional
        Time-series sample rate in Hz (default 2048.0).
    exponent : float, optional
        Power-law exponent above ``f_low_hz`` (default -7/3).

    Returns
    -------
    power : numpy.ndarray
        Normalized float32 one-sided power array of shape ``(n,)``.
    """
    power = np.zeros(n, dtype=np.float32)
    k_low = max(1, int(round(f_low_hz * n / sample_rate_hz)))
    bins = np.arange(k_low, n // 2, dtype=np.float64)
    # Apply a smooth roll-on above k_low followed by f^exponent decay.
    roll = 1.0 - np.exp(-((bins - k_low + 1.0) / 6.0) ** 2)
    power[k_low:n // 2] = (roll * (bins ** exponent)).astype(np.float32)
    return power / power.sum()


def _seismic_bank_inputs(rng, n, nt, f_low_hz, max_taps=384, rate=2048.0):
    """Build unit-norm FIR taps and matching frequency-domain templates above ``f_low_hz``.

    Parameters
    ----------
    rng : numpy.random.Generator
        Random number generator.
    n : int
        Fine FFT length.
    nt : int
        Number of templates.
    f_low_hz : float
        Low-frequency cutoff in Hz.
    max_taps : int, optional
        FIR tap count per template (default 384).
    rate : float, optional
        Sample rate in Hz (default 2048.0).

    Returns
    -------
    taps : numpy.ndarray
        Float32 FIR taps of shape ``(nt, max_taps)``.
    counts : numpy.ndarray
        Int64 tap counts of shape ``(nt,)``.
    spec : numpy.ndarray
        Complex64 frequency-domain templates of shape ``(nt, n)`` matching ``template_spectra``.
    reference : numpy.ndarray
        Normalized length-``n`` one-sided reference power array.
    ref_one_sided : numpy.ndarray
        One-sided reference array of length ``n // 2 + 1`` for ``TimeDomainFilterBank``.
    """
    counts = np.full(nt, max_taps, dtype=np.int64)
    reference = _seismic_wall_power(n, f_low_hz=f_low_hz, sample_rate_hz=rate)
    freqs_ref = np.arange(n // 2 + 1) * (rate / n)
    ref_one_sided = np.zeros(n // 2 + 1, dtype=np.float32)
    ref_one_sided[:n // 2] = reference[:n // 2]
    taps = np.zeros((nt, max_taps), dtype=np.float32)
    for t in range(nt):
        ff = np.fft.rfftfreq(max_taps, 1.0 / rate)
        amp = np.sqrt(np.interp(ff, freqs_ref, ref_one_sided))
        h = np.fft.irfft(amp * np.exp(2j * np.pi * rng.random(ff.size)), max_taps)
        taps[t] = (h / np.linalg.norm(h)).astype(np.float32)
    filt, _ = template_spectra(taps, counts, n)
    spec = np.conj(filt)
    return taps, counts, spec, reference, ref_one_sided


def _analytic_series_with_injections(rng, length, taps, injections):
    """Synthesize a unit-SNR analytic complex64 noise series with matched FIR injections.

    Parameters
    ----------
    rng : numpy.random.Generator
        Random number generator.
    length : int
        Series length in samples.
    taps : numpy.ndarray
        FIR tap array of shape ``(nt, max_taps)``.
    injections : list of tuple
        Tuples ``(template_index, sample_start, snr_amplitude)`` to add into the series.

    Returns
    -------
    series : numpy.ndarray
        Complex64 analytic time series of shape ``(length,)``.
    """
    raw_fft = np.fft.fft(rng.standard_normal(length))
    raw_fft[length // 2:] = 0.0
    series = (np.fft.ifft(raw_fft) * 2.0).astype(np.complex64)
    tap_len = taps.shape[1]
    for tmpl_idx, start_sample, amp in injections:
        # Reverse taps so cross-correlation peaks at start_sample + tap_len - 1.
        waveform = amp * taps[tmpl_idx][::-1].astype(np.complex64)
        raw_inj = np.fft.fft(waveform, n=tap_len)
        raw_inj[tap_len // 2:] = 0.0
        series[start_sample:start_sample + tap_len] += (np.fft.ifft(raw_inj) * 2.0).astype(
            np.complex64
        )
    return series


def test_cyclic_slot_wrapping_identity():
    """Verify B * IFFT_B(D_wrap * conj(H_wrap)) equals fine bandpass correlation at l * (n // B)."""
    rng = np.random.default_rng(17)
    cases = [
        (4096, 64, 96),
        (4096, 128, 136),
        (4096, 256, 192),
        # Partial clamp near Nyquist where k0 + B exceeds n // 2.
        (4096, 256, 1904),
    ]
    for n, band, k0 in cases:
        stride = n // band
        khi = min(k0 + band, n // 2)

        # Construct arbitrary complex data and template spectra with sub-sample phase ramp.
        data = rng.standard_normal(n) + 1j * rng.standard_normal(n)
        tmpl = rng.standard_normal(n) + 1j * rng.standard_normal(n)
        subsample_shift = 317.37
        data = data * np.exp(-2j * np.pi * np.arange(n) * subsample_shift / n)

        # Compute exact fine bandpass correlation restricted to [k0, khi).
        prod_fine = np.zeros(n, dtype=np.complex128)
        prod_fine[k0:khi] = data[k0:khi] * np.conj(tmpl[k0:khi])
        fine_corr = np.fft.ifft(prod_fine) * n

        # Wrap [k0, khi) into cyclic slots u = k & (band - 1) and run B-point backward FFT.
        data_wrap = np.zeros(band, dtype=np.complex128)
        tmpl_wrap = np.zeros(band, dtype=np.complex128)
        slots = np.arange(k0, khi) & (band - 1)
        data_wrap[slots] = data[k0:khi]
        tmpl_wrap[slots] = tmpl[k0:khi]
        coarse_corr = np.fft.ifft(data_wrap * np.conj(tmpl_wrap)) * band

        assert np.allclose(coarse_corr, fine_corr[::stride], rtol=1e-12, atol=1e-12)


def test_band_offset_preserves_dc_profiles_and_unlocks_seismic_wall_tiers():
    """Verify band_offset returns 0 for DC-peaked profiles and unlocks small tiers above f_low."""
    n = 4096

    # Monotone DC-inclusive power laws peak near DC and keep k0 == 0 across all candidate bands.
    bins = np.arange(1, n // 2, dtype=np.float64)
    for exp in (-2.0, -1.0, 0.0):
        plaw = np.zeros(n, dtype=np.float32)
        plaw[1:n // 2] = (bins ** exp).astype(np.float32)
        plaw /= plaw.sum()
        for band in (64, 128, 256, 512, 1024):
            assert gatechain.band_offset(plaw, n, band) == 0

    # Smooth inspiral_power(4096) keeps k0 == 0 for every band above its ~61-bin low-frequency knee.
    canonical = inspiral_power(n)
    for band in (128, 256, 512, 1024):
        assert gatechain.band_offset(canonical, n, band) == 0

    # Seismic-wall profiles at f_low = 20, 25, 35 Hz select 8-bin-aligned k0 > 0 with major gain.
    for f_low, n_fft in ((25.0, 4096), (35.0, 4096), (20.0, 8192)):
        prof = _seismic_wall_power(n_fft, f_low_hz=f_low, sample_rate_hz=2048.0)
        k0_64 = gatechain.band_offset(prof, n_fft, 64)
        assert k0_64 > 0 and k0_64 % 8 == 0
        assert float(prof[k0_64:k0_64 + 64].sum()) > float(prof[:64].sum()) + 0.25

        tiers = gatechain.usable_bands(prof, n_fft)
        assert 64 in tiers and 128 in tiers


def test_hmf_dump_matches_reference_mirror_with_nonzero_k0(tmp_path, monkeypatch):
    """Verify the C engine's dumped coarse maxima match the Python reference mirror when k0 > 0."""
    here = pathlib.Path(__file__).resolve().parent
    tools_dir = here.parent / "tools"
    if not (tools_dir / "gpu_hier_reference.py").is_file():
        pytest.skip("tools/ directory is not present beside tests/")
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import gpu_hier_reference as ref

    n, nd, nt = 4096, 4, 8
    rng = np.random.default_rng(29)
    reference = _seismic_wall_power(n, f_low_hz=80.0)
    templates = np.stack([
        template_with_power(n, _seismic_wall_power(n, f_low_hz=80.0, exponent=exp))
        for exp in np.linspace(-7.0 / 3.0, -5.0 / 3.0, nt)
    ])
    data = noise((nd, n), rng)
    data[0] += (9.0 * templates[2]
                * np.exp(2j * np.pi * np.arange(n) * 315 / n)).astype(np.complex64)

    dump = tmp_path / "dump_k0.bin"
    monkeypatch.setenv("MF_HMF_DUMP", str(dump))
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "128")

    hf = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=5.0, fd=1e-2)
    hf.set_reference(reference)
    hf.set_data(data)
    hf.set_templates(templates)
    hf._ensure()
    hf._mf.set_q15(False)
    hf._q15 = False
    hf.run(binsize=n, threshold=5.0)
    band = hf.config[0]
    k0 = hf.band_offsets[0]
    assert band == 128 and k0 > 0
    del hf

    assert dump.exists() and dump.stat().st_size > 0
    recs = np.frombuffer(dump.read_bytes(), dtype=np.float32).reshape(-1, 8)
    frac = ref.band_fraction(reference, band, k0=k0)
    for row in recs:
        d, t = int(row[6]), int(row[7])
        even, odd = ref.coarse_peak(data[d], templates[t], band, frac, k0=k0)
        assert even == pytest.approx(row[0], rel=1e-5)
        if row[1] > 0:
            assert odd == pytest.approx(row[1], rel=1e-5)


def test_cpu_active_band_parity_across_targets_and_modes(monkeypatch):
    """Verify CPU HierarchicalFilter parity with MatchedFilter across ISAs, Q15, and series modes."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")

    n, nt = 4096, 10
    rng = np.random.default_rng(41)
    # Use f_low = 260 Hz (k_low = 520) so both 128 and 512 select non-zero active-band offsets.
    taps, counts, spec, reference, _ = _seismic_bank_inputs(rng, n, nt, f_low_hz=260.0)

    series_len = 16384
    series_c = _analytic_series_with_injections(
        rng, series_len, taps, [(3, 4900, 20.0), (7, 9400, 20.0)]
    )
    starts = np.array([4096, 6144, 8192], dtype=np.uint32)
    nd = len(starts)
    ws = np.full(nd, 512, dtype=np.uint32)
    we = np.full(nd, n - 512, dtype=np.uint32)
    win = (512, n - 512)
    blocks = np.stack(
        [(np.fft.fft(series_c[s:s + n]) / n).astype(np.complex64) for s in starts]
    )

    # Check every compiled CPU SIMD target in both FP32 and Q15 tier-0 modes.
    default_target = _core.backend()
    try:
        for target in _core.targets():
            _core.set_target(target)
            exact = mf.MatchedFilter(n, ndata=nd, ntemplates=nt)
            exact.set_data(blocks)
            exact.set_templates(spec)
            ref_idx, ref_val = exact.run(window=win, binsize=256, threshold=5.5, raw=True)
            assert np.any(ref_idx[0, 3] >= 0) and np.any(ref_idx[2, 7] >= 0)

            for use_q15 in (False, True):
                hf = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=5.5, fd=1e-2)
                hf.set_reference(reference)
                hf.set_data(blocks)
                hf.set_templates(spec)
                hf._ensure()
                hf._set_q15(use_q15)
                idx, val = hf.run(window=win, binsize=256, threshold=5.5, raw=True)

                assert hf.config == (128, 512)
                assert hf.band_offsets[0] > 0 and hf.band_offsets[1] > 0

                # Every reported survivor is MatchedFilter's peak, at its value to fp32 rounding
                # (the two refine through different transforms on some targets), and the
                # injections survive. A wrong active-band offset is off by far more.
                got_mask = idx >= 0
                assert np.array_equal(idx[got_mask], ref_idx[got_mask])
                np.testing.assert_allclose(val[got_mask], ref_val[got_mask], rtol=1e-5, atol=1e-6)
                assert np.any(idx[0, 3] >= 0) and np.any(idx[2, 7] >= 0)
    finally:
        _core.set_target(default_target)

    # Explicit coarse thresholds bypass the model (band_offsets == zeros); clearing them restores
    # model-calibrated active-band offsets.
    hf_pin = mf.HierarchicalFilter(
        n, ndata=nd, ntemplates=nt, snr=5.5, fd=1e-2, chain=(128, 512), search_window=win
    )
    hf_pin.set_reference(reference)
    hf_pin.set_data(blocks)
    hf_pin.set_templates(spec)
    hf_pin.run(window=win, binsize=256, threshold=5.5)
    assert hf_pin.band_offsets[0] > 0 and hf_pin.band_offsets[1] > 0
    hf_pin.set_coarse_threshold((1.5, 2.0))
    hf_pin.run(window=win, binsize=256, threshold=5.5)
    assert hf_pin.band_offsets == (0, 0)
    hf_pin.set_coarse_threshold(None)
    hf_pin.run(window=win, binsize=256, threshold=5.5)
    assert hf_pin.band_offsets[0] > 0 and hf_pin.band_offsets[1] > 0

    # Check run_series with complex series, real series, and set_taps direct time-domain refine.
    exact_s = mf.MatchedFilter(n, ndata=nd, ntemplates=nt)
    exact_s.set_templates(spec)
    ref_s_idx, ref_s_val = exact_s.run_series(
        series_c, starts, ws, we, binsize=256, threshold=5.5, raw=True
    )

    hf_s = mf.HierarchicalFilter(
        n, ndata=nd, ntemplates=nt, snr=5.5, fd=1e-2, search_window=win
    )
    hf_s.set_reference(reference)
    hf_s.set_templates(spec)
    s_idx, s_val = hf_s.run_series(
        series_c, starts, ws, we, binsize=256, threshold=5.5, raw=True
    )
    assert hf_s.band_offsets[0] > 0 and hf_s.band_offsets[1] > 0
    s_mask = s_idx >= 0
    assert np.any(s_mask)
    assert np.array_equal(s_idx[s_mask], ref_s_idx[s_mask])
    # to fp32 rounding, as above
    np.testing.assert_allclose(s_val[s_mask], ref_s_val[s_mask], rtol=1e-5, atol=1e-6)

    # Verify set_taps direct FIR refine agrees with FFT refine on active-band survivors.
    hf_taps = mf.HierarchicalFilter(
        n, ndata=nd, ntemplates=nt, snr=5.5, fd=1e-2, search_window=win
    )
    hf_taps.set_reference(reference)
    hf_taps.set_templates(spec)
    hf_taps.set_taps(taps, counts)
    t_idx, t_val = hf_taps.run_series(
        series_c, starts, ws, we, binsize=256, threshold=5.5, raw=True
    )
    t_mask = t_idx >= 0
    assert np.any(t_mask)
    assert np.array_equal(t_idx[t_mask], ref_s_idx[t_mask])
    assert np.allclose(t_val[t_mask], ref_s_val[t_mask], rtol=1e-4, atol=1e-4)

    # Verify real float32 run_series path with active-band wrapping.
    series_r = series_c.real.astype(np.float32)
    ref_r_idx, ref_r_val = exact_s.run_series(
        series_r, starts, ws, we, binsize=256, threshold=5.5, raw=True
    )
    r_idx, r_val = hf_s.run_series(
        series_r, starts, ws, we, binsize=256, threshold=5.5, raw=True
    )
    r_mask = r_idx >= 0
    assert np.any(r_mask)
    assert np.array_equal(r_idx[r_mask], ref_r_idx[r_mask])
    assert np.allclose(r_val[r_mask], ref_r_val[r_mask], rtol=1e-6, atol=1e-6)


def test_gpu_active_band_feeds_match_cpu_and_exact(monkeypatch):
    """Verify GPU packCoarse, forwardTier0, and seriesForwardBands with k0 > 0 match exact SNR."""
    dev = usable_gpu()
    if dev is None:
        pytest.skip(usable_gpu_reason())

    monkeypatch.setenv("MF_AUTOTUNE", "0")
    n, nt = 4096, 12
    rate = 2048.0
    df = rate / n
    rng = np.random.default_rng(73)
    # Use f_low = 520 Hz (k_low = 1040) so 128, 512, and 1024 all select k0 > 0.
    taps, counts, spec, reference, ref_one_sided = _seismic_bank_inputs(
        rng, n, nt, f_low_hz=520.0, rate=rate
    )

    series_len = 65536
    series = _analytic_series_with_injections(
        rng, series_len, taps, [(2, 11100, 15.0), (9, 29500, 14.0)]
    )
    starts = np.array([8192, 10240, 12288, 26624, 28672], dtype=np.uint32)
    nd = len(starts)
    ws = np.full(nd, 512, dtype=np.uint32)
    we = np.full(nd, n - 512, dtype=np.uint32)

    exact = mf.MatchedFilter(n, ndata=nd, ntemplates=nt, device="cpu")
    exact.set_templates(spec)
    ref_idx, ref_val = exact.run_series(
        series, starts, ws, we, binsize=256, threshold=5.0, raw=True
    )

    # Check GPU hf.run (packCoarse feed) on spectra directly.
    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    blocks = np.stack(
        [(np.fft.fft(series[s:s + n]) / n).astype(np.complex64) for s in starts]
    )
    hf_pack = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=5.0, fd=1e-2, device=dev)
    hf_pack.set_reference(reference)
    hf_pack.set_data(blocks)
    hf_pack.set_templates(spec)
    p_idx, p_val = hf_pack.run(window=(512, n - 512), binsize=256, threshold=5.0, raw=True)
    assert hf_pack.config == (128, 512)
    assert hf_pack.band_offsets[0] > 0 and hf_pack.band_offsets[1] > 0
    p_mask = p_idx >= 0
    assert int(p_mask.sum()) >= 2
    assert np.array_equal(p_idx[p_mask], ref_idx[p_mask])
    assert np.allclose(p_val[p_mask], ref_val[p_mask], rtol=1e-4, atol=1e-4)

    # Check TimeDomainFilterBank.filter_series_many on GPU across:
    # 1) (128, 512) + MF_BAND_FORWARD=0 -> separate forward + packCoarse (k0_0, k0_1 > 0)
    # 2) (128, 512) + MF_BAND_FORWARD=1 -> forwardTier0 (k0_0, k0_1 > 0)
    # 3) (1024,)    + MF_BAND_FORWARD=1 -> seriesForwardBands (fp32 tier 0, k0 > 0)
    win_slice = slice(4096, series_len - 4096)
    flat_bank = TimeDomainFilterBank(
        taps, tap_counts=counts, engine="flat", threshold=5.0,
        device="cpu", fft_lengths=[n], binsize=256
    )
    exact_res = flat_bank.filter_series(series, windows=win_slice)
    exact_peaks = {
        (int(t), int(i)): complex(v)
        for t, i, v in zip(exact_res.template_indices, exact_res.sample_indices, exact_res.snr)
    }

    for chain_str, band_fwd, expect_claim in (
        ("128,512", "0", False),
        ("128,512", "1", True),
        ("1024", "1", True),
    ):
        monkeypatch.setenv("MF_CHAIN_FORCE", chain_str)
        monkeypatch.setenv("MF_BAND_FORWARD", band_fwd)

        cpu_bank = TimeDomainFilterBank(
            taps, tap_counts=counts, engine="hier", threshold=5.0,
            false_dismissal=1e-2, device="cpu", fft_lengths=[n], binsize=256
        )
        cpu_bank.set_reference(ref_one_sided, delta_f=df)
        cpu_res = cpu_bank.filter_series(series, windows=win_slice)
        cpu_peaks = {
            (int(t), int(i)): complex(v)
            for t, i, v in zip(cpu_res.template_indices, cpu_res.sample_indices, cpu_res.snr)
        }
        cpu_thr = cpu_bank._groups[0]._plan._thresholds()

        gpu_bank = TimeDomainFilterBank(
            taps, tap_counts=counts, engine="hier", threshold=5.0,
            false_dismissal=1e-2, device=dev, fft_lengths=[n], binsize=256
        )
        gpu_bank.set_reference(ref_one_sided, delta_f=df)
        orig_thr = mf.HierarchicalFilter._thresholds
        monkeypatch.setattr(
            mf.HierarchicalFilter, "_thresholds",
            lambda self, required=True, _c=cpu_bank._groups[0]._plan.config, _t=cpu_thr: (
                _t if tuple(self._chain or ()) == _c else orig_thr(self, required=required)
            ),
        )

        claims_before = CLAIMS[0]
        gpu_out = TimeDomainFilterBank.filter_series_many(
            [(gpu_bank, series, dict(windows=win_slice))]
        )[0]
        monkeypatch.setattr(mf.HierarchicalFilter, "_thresholds", orig_thr)

        plan_gpu = gpu_bank._groups[0]._plan
        assert all(k0 > 0 for k0 in plan_gpu.band_offsets)
        if expect_claim:
            assert CLAIMS[0] > claims_before

        gpu_peaks = {
            (int(t), int(i)): complex(v)
            for t, i, v in zip(gpu_out.template_indices, gpu_out.sample_indices, gpu_out.snr)
        }
        assert len(gpu_peaks) >= 2
        assert not (set(gpu_peaks) - set(exact_peaks))
        for k, v in gpu_peaks.items():
            assert abs(v - exact_peaks[k]) <= 1e-4
        assert len(set(gpu_peaks) ^ set(cpu_peaks)) <= 4
