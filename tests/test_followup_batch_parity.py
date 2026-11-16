"""Parity and edge-case tests for batched CPU and GPU single-template follow-ups."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank, _core


def _make_taps(rng, counts, complex_taps=False):
    """Synthesize unit-norm real or quadrature FIR templates for testing.

    Parameters
    ----------
    rng : numpy.random.Generator
        Random number generator instance.
    counts : sequence of int
        Valid tap count for each template.
    complex_taps : bool, optional
        When True, generate complex64 quadrature templates; otherwise float32.

    Returns
    -------
    taps : numpy.ndarray
        2-D template tap array of shape ``(len(counts), max(counts))``.
    ref_profile : numpy.ndarray
        Flat positive reference power profile for hierarchical initialization.
    delta_f : float
        Frequency resolution corresponding to ``ref_profile``.
    """
    max_len = int(max(counts))
    dtype = np.complex64 if complex_taps else np.float32
    taps = np.zeros((len(counts), max_len), dtype=dtype)
    for idx, length in enumerate(counts):
        t_grid = np.linspace(0.0, 1.0, int(length), dtype=np.float64)
        phase = 2.0 * np.pi * (12.0 + 3.5 * idx) * (t_grid ** 1.7)
        env = np.hanning(int(length))
        if complex_taps:
            wave = env * (np.cos(phase) + 1j * np.sin(phase))
        else:
            wave = env * np.cos(phase)
        norm = np.sqrt(np.sum(np.abs(wave) ** 2))
        taps[idx, :int(length)] = (wave / max(norm, 1e-12)).astype(dtype)
    ref_profile = np.ones(4097, dtype=np.float64)
    return taps, ref_profile, 0.25


def _assert_results_match(expected, actual, rtol=1e-4, atol=1e-4):
    """Assert two FilterResults match in indices, block metadata, and complex SNR.

    Parameters
    ----------
    expected : FilterResults
        Reference single-call result.
    actual : FilterResults
        Batched follow-up result.
    rtol : float, optional
        Relative tolerance for complex SNR comparison.
    atol : float, optional
        Absolute tolerance scale for complex SNR comparison.
    """
    np.testing.assert_array_equal(expected.template_indices, actual.template_indices)
    if expected.snr.size == 0:
        assert actual.snr.size == 0
        return
    assert expected.sample_indices.shape == actual.sample_indices.shape
    scale = max(float(np.max(np.abs(expected.snr))), 1.0)
    same_idx = expected.sample_indices == actual.sample_indices
    if np.all(same_idx):
        np.testing.assert_array_equal(expected.block_starts, actual.block_starts)
        np.testing.assert_array_equal(expected.block_lengths, actual.block_lengths)
        np.testing.assert_allclose(actual.snr, expected.snr, rtol=rtol, atol=atol * scale)
    else:
        # Half-size real FFT vs widened complex FFT may swap two tied ULP-equal noise samples.
        np.testing.assert_allclose(
            actual.snr[same_idx], expected.snr[same_idx], rtol=rtol, atol=atol * scale
        )
        np.testing.assert_allclose(
            np.abs(actual.snr[~same_idx]),
            np.abs(expected.snr[~same_idx]),
            rtol=1e-5,
            atol=1e-5 * scale,
        )
        np.testing.assert_array_equal(
            expected.block_lengths[same_idx], actual.block_lengths[same_idx]
        )


@pytest.mark.parametrize("complex_taps", [False, True])
@pytest.mark.parametrize("engine", ["hier", "flat"])
def test_cpu_followup_batch_narrow_and_wide_parity(monkeypatch, complex_taps, engine):
    """Verify batched CPU follow-ups match per-call filter_series on narrow TD and wide FFT windows."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    rng = np.random.default_rng(601)

    # Span multiple FFT block lengths (1024, 2048, 4096) across template groups.
    counts = [160, 220, 480, 620, 1100, 1450]
    taps, ref_profile, delta_f = _make_taps(rng, counts, complex_taps=complex_taps)
    bank = TimeDomainFilterBank(
        taps,
        tap_counts=counts,
        data_sample_rate=1024.0,
        tap_sample_rate=1024.0,
        engine=engine,
        threshold=4.0,
        false_dismissal=1e-3,
        device="cpu",
        fft_lengths=[1024, 2048, 4096],
        binsize=2048,
        max_batch_size=2,
    )
    if engine == "hier":
        bank.set_reference(ref_profile, delta_f=delta_f)

    n_samples = 1 << 16
    cplx_pair = (
        rng.standard_normal(n_samples) + 1j * rng.standard_normal(n_samples)
    ).astype(np.complex64)
    f32_contig = rng.standard_normal(n_samples).astype(np.float32)
    series_pool = [cplx_pair, f32_contig, cplx_pair.real, cplx_pair.imag]

    # Build mixed batch with narrow windows (Direct TD) and overlapping wide windows (Batched FFT).
    batch_calls = []
    orig_td_batch = _core.td_followup_batch
    monkeypatch.setattr(
        _core,
        "td_followup_batch",
        lambda c_jobs: batch_calls.append(len(c_jobs)) or orig_td_batch(c_jobs),
    )

    jobs = []
    for k in range(24):
        ser = series_pool[k % len(series_pool)]
        tmpl_idx = k % len(counts)
        center = 8000 + (k // 2) * 3500
        if k % 3 == 0:
            win = slice(center - 20, center + 20)
        elif k % 3 == 1:
            win = slice(center - 6000, center + 6000)
        else:
            win = slice(3000, n_samples - 3000)
        jobs.append((
            bank,
            ser,
            dict(windows=win, binsize=61 if k % 2 else None, threshold=0.0, template_index=tmpl_idx),
        ))

    got = TimeDomainFilterBank.filter_series_many(jobs, wait=True)
    assert batch_calls == [len(jobs)]
    for (job_bank, job_ser, job_kw), actual in zip(jobs, got):
        expected = job_bank.filter_series(job_ser, **job_kw)
        _assert_results_match(expected, actual)


def test_cpu_followup_batch_binsizes_thresholds_and_windows(monkeypatch):
    """Verify CPU follow-up parity across binsizes, thresholds, multi-rate taps, and edge windows."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    rng = np.random.default_rng(602)

    # Choose tap count 449 at N=2048 so n_valid = 2048 - 449 + 1 = 1600 (divisible by binsize=64).
    counts = [449, 449, 310, 520]
    taps, ref_profile, delta_f = _make_taps(rng, counts, complex_taps=True)
    bank_unaligned = TimeDomainFilterBank(
        taps,
        tap_counts=counts,
        engine="hier",
        threshold=4.5,
        false_dismissal=1e-3,
        device="cpu",
        fft_lengths=[2048],
        binsize=None,
    )
    bank_unaligned.set_reference(ref_profile, delta_f=delta_f)

    # Multi-rate banks (rate_ratio > 1 and rate_ratio < 1) exercising precomputed spectra in C.
    bank_up = TimeDomainFilterBank(
        taps,
        tap_counts=counts,
        data_sample_rate=2048.0,
        tap_sample_rate=4096.0,
        engine="hier",
        threshold=4.5,
        false_dismissal=1e-3,
        device="cpu",
        fft_lengths=[2048],
        binsize=2048,
    )
    bank_up.set_reference(ref_profile, delta_f=delta_f)

    bank_down = TimeDomainFilterBank(
        taps[:, :256],
        tap_counts=[200, 220, 240, 256],
        data_sample_rate=2048.0,
        tap_sample_rate=1024.0,
        engine="hier",
        threshold=4.5,
        false_dismissal=1e-3,
        device="cpu",
        fft_lengths=[2048],
        binsize=2048,
    )
    bank_down.set_reference(ref_profile, delta_f=delta_f)

    n_samples = 20000
    pair = (rng.standard_normal(n_samples) + 1j * rng.standard_normal(n_samples)).astype(np.complex64)
    zeros_real = np.zeros(n_samples, dtype=np.float32)
    zeros_cplx = np.zeros(n_samples, dtype=np.complex64)

    # Exercise bin_count_groups ordering (binsize=64 on STEP=1600), binsize >= N, and boundaries.
    jobs = [
        # All-zero series at threshold=0.0 must emit 0 triggers in both TD and FFT modes.
        (bank_unaligned, zeros_real, dict(windows=slice(4000, 4040), threshold=0.0, template_index=0)),
        (bank_unaligned, zeros_cplx, dict(windows=slice(1000, 12000), threshold=0.0, template_index=1)),
        # Unaligned bank with binsize=None vs explicit binsizes (61, 64, 2048, 4096).
        (bank_unaligned, pair.real, dict(windows=slice(2000, 15000), binsize=None, threshold=0.0, template_index=0)),
        (bank_unaligned, pair.imag, dict(windows=slice(1600, 9000), binsize=64, threshold=0.0, template_index=0)),
        (bank_unaligned, pair.real, dict(windows=slice(2500, 11000), binsize=61, threshold=0.0, template_index=2)),
        (bank_unaligned, pair, dict(windows=slice(2500, 11000), binsize=2048, threshold=0.0, template_index=3)),
        (bank_unaligned, pair, dict(windows=slice(2500, 14000), binsize=4096, threshold=0.0, template_index=3)),
        # Positive thresholds in both narrow TD and wide FFT modes.
        (bank_unaligned, pair.real, dict(windows=slice(5000, 5035), binsize=61, threshold=2.5, template_index=1)),
        (bank_unaligned, pair.imag, dict(windows=slice(1500, 16500), binsize=61, threshold=3.5, template_index=2)),
        # Disjoint multi-window list, empty window, and exact [0, S] / .imag tail boundary windows.
        (bank_unaligned, pair.imag, dict(windows=[(0, 60), (6000, 6050), (n_samples - 50, n_samples)], binsize=61, threshold=0.0, template_index=0)),
        (bank_unaligned, pair.imag, dict(windows=slice(0, n_samples), binsize=2048, threshold=0.0, template_index=1)),
        (bank_unaligned, pair.real, dict(windows=slice(500, 500), binsize=61, threshold=0.0, template_index=0)),
        # Multi-rate follow-ups (rate_ratio = 2.0 and rate_ratio = 0.5).
        (bank_up, pair.real, dict(windows=slice(3000, 3040), binsize=61, threshold=0.0, template_index=0)),
        (bank_up, pair, dict(windows=slice(2000, 12000), binsize=2048, threshold=0.0, template_index=2)),
        (bank_down, pair.imag, dict(windows=slice(2000, 12000), binsize=61, threshold=0.0, template_index=1)),
    ]

    # Check both wait=True and wait=False deferred result wrappers.
    got_sync = TimeDomainFilterBank.filter_series_many(jobs, wait=True)
    got_defer = [d.result() for d in TimeDomainFilterBank.filter_series_many(jobs, wait=False)]
    assert got_sync[0].snr.size == 0
    assert got_sync[1].snr.size == 0
    assert got_sync[11].snr.size == 0

    for (job_bank, job_ser, job_kw), res_sync, res_def in zip(jobs, got_sync, got_defer):
        expected = job_bank.filter_series(job_ser, **job_kw)
        _assert_results_match(expected, res_sync)
        _assert_results_match(expected, res_def)


def test_gpu_followup_batch_coalesced_groups_and_binsizes(monkeypatch):
    """Verify GPU device follow-ups coalesce many leaf groups without flat plans and match CPU."""
    from conftest import usable_gpu
    from matchedfilter import _gpuhost
    from matchedfilter.time_domain import _TemplateGroup

    device = usable_gpu()
    if device is None:
        pytest.skip("no usable GPU backend")

    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_SINGLE_DEVICE", "bank")
    rng = np.random.default_rng(603)

    # Create 48 quadrature templates with max_batch_size=2 (24 leaf groups) and binsize=2048 (== N).
    counts = list(rng.integers(220, 480, size=48))
    taps, ref_profile, delta_f = _make_taps(rng, counts, complex_taps=True)
    gpu_bank = TimeDomainFilterBank(
        taps,
        tap_counts=counts,
        engine="hier",
        threshold=4.5,
        false_dismissal=1e-3,
        device=device,
        fft_lengths=[2048],
        binsize=2048,
        max_batch_size=2,
    )
    gpu_bank.set_reference(ref_profile, delta_f=delta_f)
    assert len(gpu_bank._groups) >= 20

    cpu_bank = TimeDomainFilterBank(
        taps,
        tap_counts=counts,
        engine="hier",
        threshold=4.5,
        false_dismissal=1e-3,
        device="cpu",
        fft_lengths=[2048],
        binsize=2048,
        max_batch_size=2,
    )
    cpu_bank.set_reference(ref_profile, delta_f=delta_f)

    # Forbid get_flat_plan() during threshold-0 device follow-ups.
    def _forbid_flat_plan(self):
        raise AssertionError("get_flat_plan() should not be called by device follow-ups")

    monkeypatch.setattr(_TemplateGroup, "get_flat_plan", _forbid_flat_plan)

    layouts_seen = []
    orig_layout = _gpuhost.followup_layout

    def _spy_layout(batch_jobs, ctx, max_rows=None):
        res = orig_layout(batch_jobs, ctx, max_rows=max_rows)
        if res is not None:
            layouts_seen.append(len(res[0]))
        return res

    monkeypatch.setattr(_gpuhost, "followup_layout", _spy_layout)

    n_samples = 1 << 16
    shared_cplx = gpu_bank.empty_shared((2, n_samples), dtype=np.complex64)
    shared_cplx[0] = (
        rng.standard_normal(n_samples) + 1j * rng.standard_normal(n_samples)
    ).astype(np.complex64)
    shared_cplx[1] = 0.0

    # Batch across all 24 leaf groups, binsize=None (2048), 61, 4096, and real/imag lanes.
    gpu_jobs = []
    cpu_jobs = []
    host_cplx0 = np.array(shared_cplx[0])
    host_cplx1 = np.array(shared_cplx[1])
    binsize_choices = [None, 61, 2048, 4096]
    for k in range(36):
        tmpl_idx = (k * 5) % len(counts)
        center = 6000 + (k * 1300) % (n_samples - 12000)
        bs_arg = binsize_choices[k % len(binsize_choices)]
        if k == 0:
            # Zero series at threshold=0.0
            g_ser, c_ser = shared_cplx[1], host_cplx1
            win = slice(10000, 10040)
        elif k == 1:
            # Empty window
            g_ser, c_ser = shared_cplx[0].real, host_cplx0.real
            win = slice(5000, 5000)
        elif k % 3 == 0:
            g_ser, c_ser = shared_cplx[0], host_cplx0
            win = slice(center - 20, center + 20)
        elif k % 3 == 1:
            g_ser, c_ser = shared_cplx[0].real, host_cplx0.real
            win = slice(center - 2500, center + 2500)
        else:
            g_ser, c_ser = shared_cplx[0].imag, host_cplx0.imag
            win = [(center - 1500, center - 900), (center + 300, center + 1200)]
        kw = dict(windows=win, binsize=bs_arg, threshold=0.0, template_index=tmpl_idx)
        gpu_jobs.append((gpu_bank, g_ser, kw))
        cpu_jobs.append((cpu_bank, c_ser, kw))

    got_gpu = TimeDomainFilterBank.filter_series_many(gpu_jobs, wait=True)
    got_gpu_def = [d.result() for d in TimeDomainFilterBank.filter_series_many(gpu_jobs, wait=False)]
    assert layouts_seen, "device follow-up path was not taken"
    # Coalesced by 3 distinct binsizes (61, 2048, 4096) x 3 distinct layout codes = 9 groups.
    assert max(layouts_seen) == 9

    assert got_gpu[0].snr.size == 0
    assert got_gpu[1].snr.size == 0
    for (_, c_ser, c_kw), res_gpu, res_def in zip(cpu_jobs, got_gpu, got_gpu_def):
        expected = cpu_bank.filter_series(c_ser, **c_kw)
        _assert_results_match(expected, res_gpu)
        _assert_results_match(expected, res_def)


def test_gpu_followup_partial_batch_with_edge_job(monkeypatch):
    """Verify a GPU batch with one end-of-series job still dispatches eligible jobs on GPU."""
    from conftest import usable_gpu
    from matchedfilter import _gpuhost

    device = usable_gpu()
    if device is None:
        pytest.skip("no usable GPU backend")

    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_SINGLE_DEVICE", "bank")
    rng = np.random.default_rng(604)

    counts = [240, 320, 410, 500]
    taps, ref_profile, delta_f = _make_taps(rng, counts, complex_taps=True)
    gpu_bank = TimeDomainFilterBank(
        taps,
        tap_counts=counts,
        engine="hier",
        threshold=4.5,
        false_dismissal=1e-3,
        device=device,
        fft_lengths=[2048],
        binsize=2048,
    )
    gpu_bank.set_reference(ref_profile, delta_f=delta_f)

    n_samples = 16384
    shared_row = gpu_bank.empty_shared((n_samples,), dtype=np.complex64)
    shared_row[:] = (
        rng.standard_normal(n_samples) + 1j * rng.standard_normal(n_samples)
    ).astype(np.complex64)

    submitted_sizes = []
    orig_submit = _gpuhost.submit_followups

    def _spy_submit(batch_jobs):
        col = orig_submit(batch_jobs)
        if col is not None:
            submitted_sizes.append(len(batch_jobs))
        return col

    monkeypatch.setattr(_gpuhost, "submit_followups", _spy_submit)

    # First 4 jobs are interior device jobs; 5th job reaches n_samples (requires zero-padding).
    jobs = [
        (gpu_bank, shared_row, dict(windows=slice(4000, 4050), binsize=2048, threshold=0.0, template_index=0)),
        (gpu_bank, shared_row.real, dict(windows=slice(6000, 6050), binsize=61, threshold=0.0, template_index=1)),
        (gpu_bank, shared_row.imag, dict(windows=slice(8000, 8050), binsize=2048, threshold=0.0, template_index=2)),
        (gpu_bank, shared_row, dict(windows=slice(9000, 9050), binsize=4096, threshold=0.0, template_index=3)),
        (gpu_bank, shared_row, dict(windows=slice(n_samples - 40, n_samples), binsize=61, threshold=0.0, template_index=0)),
    ]

    got = TimeDomainFilterBank.filter_series_many(jobs, wait=True)
    assert submitted_sizes == [4]
    for (job_bank, job_ser, job_kw), actual in zip(jobs, got):
        expected = job_bank.filter_series(job_ser, **job_kw)
        _assert_results_match(expected, actual)
