"""GPU kernel and host pipeline optimization tests.

Covers:
1. Scalar (nbins <= 4) and 64-bit bitmask (nbins > 4) multi-bin peak reduction.
2. COARSE16 subgroup-shuffle transpose and barrier-free peakTwoWave across layouts.
3. Multi-batch grouped deferral, _SparsePeaks.combine empty fast-path, and
   _Deferred.empty propagation (both initial grouped calls and call-plan replays).
4. GPU direct time-domain FIR refinement (refine_td.slang) across real/complex
   taps and series, 1-tier and 2-tier chains, template sub-slices, sparse modes,
   TimeDomainFilterBank end-to-end, and per-survivor FFT fallback paths.
"""
import numpy as np
import pytest

from conftest import usable_gpu, usable_gpu_reason
import matchedfilter as mf
from matchedfilter._results import _Deferred, _SparsePeaks
from matchedfilter.time_domain import template_spectra


@pytest.fixture
def dev():
    gpu = usable_gpu()
    if gpu is None:
        pytest.skip(usable_gpu_reason())
    return gpu


def _synthetic_td_bank(n=2048, ntemplates=24, nblocks=32, nsig=12, complex_taps=False,
                       real_kind="complex", seed=19):
    """Build synthetic inspiral-like taps, spectra, reference, and series for GPU tests."""
    from matchedfilter.benchmark import _inspiral_power
    rng = np.random.default_rng(seed)
    counts = (2 * rng.integers(48, 120, ntemplates) + 1).astype(np.int64)
    if complex_taps:
        taps = np.zeros((ntemplates, counts.max()), np.complex64)
        for t in range(ntemplates):
            tap_len = int(counts[t])
            phase = 0.35 + 0.06 * t
            w = np.zeros(tap_len, np.complex128)
            w[tap_len // 2] = np.exp(1j * phase)
            w += 0.14 * np.hanning(tap_len) * np.exp(
                1j * np.linspace(0, 2.8 + 0.1 * t, tap_len)) / np.sqrt(tap_len)
            taps[t, :tap_len] = w.astype(np.complex64)
    else:
        taps = np.zeros((ntemplates, counts.max()), np.float32)
        for t in range(ntemplates):
            tap_len = int(counts[t])
            x = np.zeros(tap_len)
            x[tap_len // 2] = 1.0
            x += 0.14 * np.hanning(tap_len) * np.cos(
                np.linspace(0, 2.8 + 0.1 * t, tap_len)) / np.sqrt(tap_len)
            taps[t, :tap_len] = x.astype(np.float32)
    filt, valid = template_spectra(taps, counts, n)
    spec = np.conj(filt)
    cbad, vend = int(valid[:, 0].max()), int(valid[:, 1].min())
    step = vend - cbad
    # Include a partial trailing block so zero-padded series boundary gathering is tested.
    total = step * (nblocks - 1) + vend + 9
    tot_fft = 1 << int(np.ceil(np.log2(total + n)))
    p = _inspiral_power(tot_fft)
    p = p / p.sum()
    if real_kind == "complex":
        w = (rng.standard_normal(tot_fft) + 1j * rng.standard_normal(tot_fft)) / np.sqrt(2)
        full = np.fft.ifft(np.sqrt(p) * w) * np.sqrt(tot_fft)
        full *= np.sqrt(2.0 / np.mean(np.abs(full) ** 2))
        pulse = np.fft.ifft(p) * tot_fft
        gap = max((total - 2 * n) // max(nsig, 1), 1)
        for i in range(nsig):
            tau = cbad + 80 + i * gap
            full += rng.uniform(8.5, 11.0) * np.exp(2j * np.pi * rng.random()) * np.roll(pulse, tau)
        series = full[:total].astype(np.complex64)
    else:
        p1 = p.copy()
        p1[tot_fft // 2:] = 0.0
        p1 /= p1.sum()
        w = rng.standard_normal(tot_fft)
        spec_w = np.fft.rfft(w)
        shaped = np.zeros_like(spec_w)
        half_n = min(len(shaped), tot_fft // 2)
        shaped[:half_n] = spec_w[:half_n] * np.sqrt(p1[:half_n] * tot_fft)
        full = np.fft.irfft(shaped, n=tot_fft)
        full /= np.std(full)
        pulse = np.real(np.fft.ifft(p1) * tot_fft) * 2.0
        gap = max((total - 2 * n) // max(nsig, 1), 1)
        for i in range(nsig):
            tau = cbad + 80 + i * gap
            full += rng.uniform(8.5, 11.0) * np.roll(pulse, tau)
        rser = full[:total].astype(np.float32)
        if real_kind == "real_stride2":
            packed = np.empty(total, np.complex64)
            packed.real = rng.standard_normal(total).astype(np.float32)
            packed.imag = rser
            series = packed.imag
        else:
            series = rser

    starts = np.arange(nblocks) * step
    layout = (starts, np.full(nblocks, cbad), np.full(nblocks, vend))
    q = n // 32
    window = ((cbad // q) * q, n - (cbad // q) * q)
    ref = _inspiral_power(n).copy()
    if real_kind != "complex":
        ref[n // 2:] = 0.0
    return n, taps, counts, spec, series, layout, ref, window


@pytest.mark.parametrize("nbins", [1, 2, 3, 4, 5, 7, 8])
def test_gpu_multibin_reduction_matches_cpu(dev, nbins):
    """Exercise both scalar (nbins <= 4) and 64-bit bitmask (nbins > 4) GPU bin reductions."""
    rng = np.random.default_rng(100 + nbins)
    n, nblocks, nt = 1024, 10, 12
    binsize = 96
    ws = np.full(nblocks, 64, np.int64)
    # Give the last two blocks a non-zero bin_phase while keeping uniform bin count.
    phase = np.zeros(nblocks, np.uint32)
    phase[-2:] = 32
    span = (nbins - 1) * binsize + 40
    we = ws + span - phase.astype(np.int64)
    starts = np.arange(nblocks, dtype=np.int64) * 512
    total = int(starts[-1]) + n + 64
    series = ((rng.standard_normal(total) + 1j * rng.standard_normal(total))
              / np.sqrt(2)).astype(np.complex64)
    raw_h = ((rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n)))
             / np.sqrt(2 * n)).astype(np.complex64)
    tmpl = np.fft.fft(raw_h, axis=1).astype(np.complex64)

    f_cpu = mf.MatchedFilter(n, 1, nt, device="cpu")
    f_gpu = mf.MatchedFilter(n, 1, nt, device=dev)
    f_cpu.set_templates(tmpl)
    f_gpu.set_templates(tmpl)

    ci, cv = f_cpu.run_series(series, starts, ws, we, binsize=binsize, threshold=2.2,
                              raw=True, bin_phase=phase)
    gi, gv = f_gpu.run_series(series, starts, ws, we, binsize=binsize, threshold=2.2,
                              raw=True, bin_phase=phase)
    assert gi.shape == (nblocks, nt, nbins)
    np.testing.assert_array_equal(gi, ci)
    hit = ci >= 0
    assert np.count_nonzero(hit) > 10
    np.testing.assert_allclose(gv[hit], cv[hit], rtol=2e-5, atol=2e-4)


@pytest.mark.parametrize("band", [64, 128, 256, 512, 1024])
def test_gpu_c16_shuffle_transpose_and_peak_two_wave(dev, band, monkeypatch):
    """Verify every shipped COARSE16 layout (untiled and tiled) matches CPU hierarchical peaks."""
    data = _synthetic_td_bank(n=2048, ntemplates=16, nblocks=16, nsig=6,
                              complex_taps=False, real_kind="complex", seed=200 + band)
    n, _, _, tmpl, series, (starts, ws, we), ref, _ = data
    probe = mf.HierarchicalFilter(n, 1, tmpl.shape[0], chain=(band,), device=dev)
    layouts = probe._gpu.coarse_layouts(band)
    if not layouts:
        pytest.skip("no COARSE16 layouts at band %d" % band)

    hf_cpu = mf.HierarchicalFilter(n, 1, tmpl.shape[0], chain=(band,), device="cpu")
    hf_cpu.set_reference(ref)
    hf_cpu.set_templates(tmpl)
    hf_cpu.set_coarse_threshold(3.5)
    ci, cv = hf_cpu.run_series(series, starts, ws, we, binsize=n, threshold=6.0, raw=True)
    assert np.count_nonzero(ci >= 0) >= tmpl.shape[0]

    # Test representative untiled and tiled layouts on this GPU.
    tested = [layouts[0]] + [s for s in layouts[1:] if "t" in s][:2]
    for label in tested:
        monkeypatch.setenv("MF_COARSE_LAYOUT", label)
        hf_gpu = mf.HierarchicalFilter(n, 1, tmpl.shape[0], chain=(band,), device=dev)
        hf_gpu.set_reference(ref)
        hf_gpu.set_templates(tmpl)
        hf_gpu.set_coarse_threshold(3.5)
        gi, gv = hf_gpu.run_series(series, starts, ws, we, binsize=n, threshold=6.0, raw=True)
        np.testing.assert_array_equal(gi, ci)
        hit = ci >= 0
        np.testing.assert_allclose(gv[hit], cv[hit], rtol=2e-5, atol=2e-4)


def test_gpu_deferred_grouped_multibatch_and_empty_flag(dev):
    """Verify multi-batch grouped deferral, _SparsePeaks.combine empty fast-path, and
    deferred.empty on both initial grouped calls and call-plan replays."""
    from matchedfilter.benchmark import _inspiral_power
    rng = np.random.default_rng(77)
    n, nt, nblocks = 1024, 16, 20
    ref = _inspiral_power(n)
    p = ref / ref.sum()
    tmpl = np.zeros((nt, n), np.complex64)
    for t in range(nt):
        tmpl[t] = (np.exp(1j * 0.1 * t)).astype(np.complex64)

    # Irregular windows (>= 2 window groups) + tight series_bytes so nblocks splits into >1 batch.
    starts = np.arange(nblocks, dtype=np.int64) * 512
    ws = np.where(np.arange(nblocks) % 2 == 0, 64, 96).astype(np.int64)
    we = np.where(np.arange(nblocks) % 2 == 0, n - 64, n - 96).astype(np.int64)
    total = int(starts[-1]) + n + 64

    # 1. Flat MatchedFilter multi-batch grouped deferral.
    f_flat = mf.MatchedFilter(n, 1, nt, device=dev)
    f_flat.set_memory_limits(series_bytes=64 * 1024)
    f_flat.set_templates(tmpl)
    quiet = ((rng.standard_normal(total) + 1j * rng.standard_normal(total))
             * 0.05).astype(np.complex64)
    with f_flat._series_flags(defer="tok_flat", sparse=True):
        d_flat = f_flat.run_series(quiet, starts, ws, we, binsize=n, threshold=6.0, raw=True)
    assert isinstance(d_flat, _Deferred)
    assert f_flat._last_series_batch < nblocks
    sp_flat = d_flat.result()
    assert isinstance(sp_flat, _SparsePeaks) and sp_flat.flat.size == 0

    # 2. HierarchicalFilter multi-batch grouped deferral + call-plan replay on shared series.
    hf = mf.HierarchicalFilter(n, 1, nt, chain=(256,), device=dev)
    hf.set_memory_limits(series_bytes=64 * 1024)
    hf.set_reference(ref)
    hf.set_templates(tmpl)
    hf.set_coarse_threshold(4.5)
    shared_ser = hf.empty_shared((total,), dtype=np.complex64)
    shared_ser[:] = quiet

    # First deferred call records the call plan and marks deferred.empty = True on 0 refinements.
    with hf._series_flags(defer="tok_h1", sparse=True):
        d1 = hf.run_series(shared_ser, starts, ws, we, binsize=n, threshold=6.0, raw=True)
    assert isinstance(d1, _Deferred)
    assert hf._last_series_batch < nblocks
    r1 = d1.result()
    assert d1.empty is True
    assert isinstance(r1, _SparsePeaks) and r1.flat.size == 0

    # Second deferred call on the same shared buffer replays the call plan and also marks empty.
    with hf._series_flags(defer="tok_h2", sparse=True):
        d2 = hf.run_series(shared_ser, starts, ws, we, binsize=n, threshold=6.0, raw=True)
    assert getattr(hf, "call_plan_replays", 0) >= 1
    r2 = d2.result()
    assert d2.empty is True
    assert isinstance(r2, _SparsePeaks) and r2.flat.size == 0

    # Injecting a loud signal into shared_ser in-place must produce triggers and empty == False.
    pulse = (np.fft.ifft(p) * n).astype(np.complex64)
    loud = quiet.copy()
    loud[starts[5]:starts[5] + n] += np.float32(12.0) * np.roll(pulse, 300)
    shared_ser[:] = loud
    with hf._series_flags(defer="tok_h3", sparse=True):
        d3 = hf.run_series(shared_ser, starts, ws, we, binsize=n, threshold=6.0, raw=True)
    r3 = d3.result()
    assert d3.empty is False
    assert isinstance(r3, _SparsePeaks) and r3.flat.size > 0
    ref_i, ref_v = hf.run_series(loud, starts, ws, we, binsize=n, threshold=6.0, raw=True)
    di, dv = r3.dense()
    np.testing.assert_array_equal(di, ref_i)
    hit = ref_i >= 0
    np.testing.assert_allclose(dv[hit], ref_v[hit], rtol=1e-5, atol=1e-5)


@pytest.mark.parametrize("chain", [(512,), (256, 512)])
@pytest.mark.parametrize("real_kind", ["complex", "real_contig", "real_stride2"])
@pytest.mark.parametrize("complex_taps", [False, True])
def test_gpu_direct_refine_chains_and_modes(dev, chain, real_kind, complex_taps, monkeypatch):
    """GPU direct time-domain refine matches GPU FFT refine across 1/2-tier chains and dtypes."""
    data = _synthetic_td_bank(n=2048, ntemplates=20, nblocks=28, nsig=10,
                              complex_taps=complex_taps, real_kind=real_kind, seed=31)
    n, taps, counts, spec, series, layout, ref, window = data

    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    hf_dir = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=chain,
                                   search_window=window, device=dev)
    hf_dir.set_reference(ref)
    hf_dir.set_templates(spec)
    hf_dir.set_taps(taps, counts)
    i_dir, v_dir = hf_dir.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)
    st = hf_dir.direct_stats()
    thr = hf_dir._resolve().thresholds
    assert hf_dir._resolve().direct_hw is not None
    assert st["pairs"] > 0, "expected GPU direct refine to run, got %s" % (st,)

    # Compare against whole-block GPU FFT refine at the exact same coarse thresholds.
    monkeypatch.setenv("MF_DIRECT_REFINE", "0")
    hf_fft = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=chain,
                                   search_window=window, device=dev)
    hf_fft.set_reference(ref)
    hf_fft.set_templates(spec)
    hf_fft.set_coarse_threshold(thr)
    i_fft, v_fft = hf_fft.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)

    assert np.count_nonzero(i_fft >= 0) >= 8
    np.testing.assert_array_equal(i_dir, i_fft)
    hit = i_fft >= 0
    np.testing.assert_allclose(v_dir[hit], v_fft[hit], rtol=2e-5, atol=2e-4)

    # Also verify non-zero template sub-slice (tmpl_offset > 0) and sparse output modes.
    if chain == (256, 512) and real_kind == "real_contig" and complex_taps:
        monkeypatch.setenv("MF_DIRECT_REFINE", "1")
        i_sub, v_sub = hf_dir.run_series(series, *layout, binsize=n, threshold=6.0,
                                         templates=(5, 11), raw=True)
        np.testing.assert_array_equal(i_sub, i_fft[:, 5:16])
        sub_hit = i_fft[:, 5:16] >= 0
        np.testing.assert_allclose(v_sub[sub_hit], v_fft[:, 5:16][sub_hit], rtol=2e-5, atol=2e-4)

        for way in ("rows", "compact"):
            monkeypatch.setattr(hf_dir._gpu, "_sparse_way", lambda w=way: w)
            with hf_dir._series_flags(sparse=True):
                sp = hf_dir.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)
            assert isinstance(sp, _SparsePeaks)
            si, sv = sp.dense()
            np.testing.assert_array_equal(si, i_fft)
            np.testing.assert_allclose(sv[hit], v_fft[hit], rtol=2e-5, atol=2e-4)


def test_gpu_direct_refine_fallbacks_and_time_domain_bank(dev, monkeypatch):
    """Verify multi-bin bypass, straddling-bin mixed direct/FFT fallback, edge/long-tap
    fallback, and TimeDomainFilterBank end-to-end on GPU."""
    data = _synthetic_td_bank(n=2048, ntemplates=20, nblocks=36, nsig=14,
                              complex_taps=True, real_kind="real_contig", seed=53)
    n, taps, counts, spec, series, layout, ref, window = data

    # 1. Multi-bin call bypasses direct refine cleanly (st['pairs'] == 0).
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    hf_mb = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=(256, 512),
                                  search_window=window, device=dev)
    hf_mb.set_reference(ref)
    hf_mb.set_templates(spec)
    hf_mb.set_taps(taps, counts)
    thr = hf_mb._resolve().thresholds
    i_mb1, v_mb1 = hf_mb.run_series(series, *layout, binsize=64, threshold=6.0, raw=True)
    assert hf_mb.direct_stats()["pairs"] == 0

    monkeypatch.setenv("MF_DIRECT_REFINE", "0")
    hf_mb0 = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=(256, 512),
                                   search_window=window, device=dev)
    hf_mb0.set_reference(ref)
    hf_mb0.set_templates(spec)
    hf_mb0.set_coarse_threshold(thr)
    i_mb0, v_mb0 = hf_mb0.run_series(series, *layout, binsize=64, threshold=6.0, raw=True)
    np.testing.assert_array_equal(i_mb1, i_mb0)
    mb_hit = i_mb0 >= 0
    np.testing.assert_allclose(v_mb1[mb_hit], v_mb0[mb_hit], rtol=2e-5, atol=2e-4)

    # 2. Forcing a tiny max_lag_tap sends every survivor through the fbSurv/fbArgs -> mark ->
    # seriesForwardListed -> refineListed fallback path and still matches FFT refine bit-closely.
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    hf_fb = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=(256, 512),
                                  search_window=window, device=dev)
    hf_fb.set_reference(ref)
    hf_fb.set_templates(spec)
    hf_fb.set_taps(taps, counts)
    orig_arg = hf_fb._gpu_direct_arg
    monkeypatch.setattr(hf_fb, "_gpu_direct_arg",
                        lambda H: (lambda d: None if d is None else (*d[:4], 1))(orig_arg(H)))
    i_fb, v_fb = hf_fb.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)
    st_fb = hf_fb.direct_stats()
    assert st_fb["pairs"] == 0 and st_fb["fft"] > 0, st_fb

    monkeypatch.setenv("MF_DIRECT_REFINE", "0")
    hf_ref = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=(256, 512),
                                   search_window=window, device=dev)
    hf_ref.set_reference(ref)
    hf_ref.set_templates(spec)
    hf_ref.set_coarse_threshold(hf_fb._resolve().thresholds)
    i_ref, v_ref = hf_ref.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)
    np.testing.assert_array_equal(i_fb, i_ref)
    fb_hit = i_ref >= 0
    np.testing.assert_allclose(v_fb[fb_hit], v_ref[fb_hit], rtol=2e-5, atol=2e-4)

    # 3. TimeDomainFilterBank end-to-end on GPU with straddling window bins (binsize=2500):
    # exercises mixed direct + FFT fallback within a single grouped hierarchical call.
    from matchedfilter.benchmark import _inspiral_power
    rng = np.random.default_rng(91)
    bt_counts = np.full(16, 129, np.int64)
    bt_taps = np.zeros((16, 129), np.complex64)
    for t in range(16):
        w = np.zeros(129, np.complex128)
        w[64] = np.exp(1j * 0.15 * t)
        w += 0.12 * np.hanning(129) * np.exp(1j * np.linspace(0, 2.8, 129)) / np.sqrt(129)
        bt_taps[t] = w.astype(np.complex64)
    total_s = 65536
    p1 = _inspiral_power(total_s).copy()
    p1[total_s // 2:] = 0.0
    p1 /= p1.sum()
    w_s = np.fft.rfft(rng.standard_normal(total_s))
    shaped_s = np.zeros_like(w_s)
    shaped_s[:total_s // 2] = w_s[:total_s // 2] * np.sqrt(p1[:total_s // 2] * total_s)
    x = np.fft.irfft(shaped_s, n=total_s)
    x = (x / np.std(x)).astype(np.float64)
    pulse_s = np.real(np.fft.ifft(p1) * total_s) * 2.0
    for tau in range(4200, 60000, 2350):
        x += 9.0 * np.roll(pulse_s, tau)
    x = x.astype(np.float32)

    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    b_dir = mf.TimeDomainFilterBank(bt_taps, bt_counts, tap_sample_rate=2048.0,
                                    data_sample_rate=2048.0, threshold=6.0, false_dismissal=1e-2,
                                    binsize=2500, fft_lengths=(n,), device=dev)
    b_dir.set_reference(ref)
    r_dir = b_dir.filter_series(x, windows=slice(4096, 61440))
    st_bank = [g.plan.direct_stats() for g in b_dir._groups if g.is_hier][0]
    assert st_bank["pairs"] > 0 and st_bank["fft"] > 0, st_bank

    monkeypatch.setenv("MF_DIRECT_REFINE", "0")
    b_fft = mf.TimeDomainFilterBank(bt_taps, bt_counts, tap_sample_rate=2048.0,
                                    data_sample_rate=2048.0, threshold=6.0, false_dismissal=1e-2,
                                    binsize=2500, fft_lengths=(n,), device=dev)
    b_fft.set_reference(ref)
    r_fft = b_fft.filter_series(x, windows=slice(4096, 61440))
    assert len(r_dir.sample_indices) > 15
    np.testing.assert_array_equal(r_dir.template_indices, r_fft.template_indices)
    np.testing.assert_array_equal(r_dir.sample_indices, r_fft.sample_indices)
    np.testing.assert_allclose(r_dir.snr, r_fft.snr, rtol=2e-5, atol=2e-4)
