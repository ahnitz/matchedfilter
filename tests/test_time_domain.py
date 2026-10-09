"""Unit tests for TimeDomainFilterBank and dynamic length partitioning."""

import numpy as np
import pytest
from matchedfilter import TimeDomainFilterBank, FilterResults
from matchedfilter.time_domain import _partition_templates


def test_partition_algorithm():
    # Empty
    groups, order = _partition_templates(np.array([], dtype=int))
    assert len(groups) == 0

    # Single template
    groups, order = _partition_templates(np.array([500]))
    assert len(groups) == 1
    assert groups[0][2] in (1024, 2048, 4096)

    # Identical counts
    counts = np.full(100, 400)
    groups, order = _partition_templates(counts, max_batch=64)
    assert len(groups) == 2
    assert groups[0][1] - groups[0][0] <= 64
    assert groups[1][1] - groups[1][0] <= 64
    assert groups[0][2] == groups[1][2]

    # Mixed counts ranging from short to very long (enough templates to justify partition)
    counts = np.array([100] * 40 + [2400] * 40)
    groups, order = _partition_templates(counts, max_batch=64)
    assert len(groups) == 2
    # Ensure short templates get smaller N than long templates
    short_n = groups[0][2]
    long_n = groups[-1][2]
    assert short_n < long_n
    assert short_n in (512, 1024, 2048, 4096)
    assert long_n in (8192, 16384, 32768)


def test_multirate_conversion():
    rng = np.random.default_rng(12345)
    
    # 1. Same sample rate
    taps = rng.standard_normal(400).astype(np.float32)
    bank1 = TimeDomainFilterBank(
        [taps], tap_counts=[400],
        tap_sample_rate=2048, data_sample_rate=2048,
        engine='flat', fft_lengths=[4096]
    )
    f1 = bank1.get_filter_f(0)
    assert len(f1) == 4096
    buf = np.zeros(4096, dtype=np.float32)
    buf[:400] = taps
    buf = np.roll(buf, -200)
    ref_f = np.conj(np.fft.fft(buf))
    np.testing.assert_allclose(f1, ref_f, atol=1e-5)

    # 2. Tap sample rate > Data sample rate (4096 Hz -> 2048 Hz)
    bank2 = TimeDomainFilterBank(
        [taps], tap_counts=[400],
        tap_sample_rate=4096, data_sample_rate=2048,
        engine='flat', fft_lengths=[4096]
    )
    f2 = bank2.get_filter_f(0)
    assert len(f2) == 4096
    buf2 = np.zeros(8192, dtype=np.float32)
    buf2[:400] = taps
    buf2 = np.roll(buf2, -200)
    spec2 = np.conj(np.fft.fft(buf2))
    ref_f2 = np.zeros(4096, dtype=np.complex64)
    ref_f2[:2049] = spec2[:2049]
    ref_f2[2049:] = spec2[8192 - (4096 - 2049):]
    np.testing.assert_allclose(f2, ref_f2, atol=1e-5)

    # 3. Tap sample rate < Data sample rate (1024 Hz -> 2048 Hz)
    bank3 = TimeDomainFilterBank(
        [taps], tap_counts=[400],
        tap_sample_rate=1024, data_sample_rate=2048,
        engine='flat', fft_lengths=[4096]
    )
    f3 = bank3.get_filter_f(0)
    assert len(f3) == 4096
    buf3 = np.zeros(2048, dtype=np.float32)
    buf3[:400] = taps
    buf3 = np.roll(buf3, -200)
    spec3 = np.conj(np.fft.fft(buf3))
    ref_f3 = np.zeros(4096, dtype=np.complex64)
    ref_f3[:1025] = spec3[:1025]
    ref_f3[4096 - (2048 - 1025):] = spec3[1025:]
    np.testing.assert_allclose(f3, ref_f3, atol=1e-5)


def test_trigger_accuracy_flat():
    rng = np.random.default_rng(42)
    counts = [100, 250, 600, 1500, 2200]
    M = len(counts)
    taps_list = [rng.standard_normal(c).astype(np.float32) for c in counts]

    bank = TimeDomainFilterBank(
        taps_list, tap_counts=counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine='flat', threshold=100.0
    )

    data_len = 65536
    data = (rng.standard_normal(data_len) + 1j * rng.standard_normal(data_len)).astype(np.complex64)

    # Inject template 1 at sample 25000 and template 3 at sample 48000
    inj_pos1 = 25000
    c1 = counts[1]
    t1 = taps_list[1]
    data[inj_pos1 - c1 // 2 : inj_pos1 - c1 // 2 + c1] += t1 * 20.0

    inj_pos2 = 48000
    c3 = counts[3]
    t3 = taps_list[3]
    data[inj_pos2 - c3 // 2 : inj_pos2 - c3 // 2 + c3] += t3 * 20.0

    # Filter with TimeDomainFilterBank
    results = bank.filter_series(data)
    assert isinstance(results, FilterResults)
    assert len(results.template_indices) > 0

    # Direct time domain correlations at injected positions
    ref_val1 = np.sum(data[inj_pos1 - c1 // 2 : inj_pos1 - c1 // 2 + c1] * t1)
    ref_val2 = np.sum(data[inj_pos2 - c3 // 2 : inj_pos2 - c3 // 2 + c3] * t3)

    # Find trigger for template 1 near 25000
    mask1 = (results.template_indices == 1) & (np.abs(results.sample_indices - inj_pos1) <= 1)
    assert np.any(mask1)
    idx1 = np.flatnonzero(mask1)[0]
    assert results.sample_indices[idx1] == inj_pos1
    rel_err1 = abs(results.snr[idx1] - ref_val1) / abs(ref_val1)
    assert rel_err1 < 1e-4

    # Find trigger for template 3 near 48000
    mask3 = (results.template_indices == 3) & (np.abs(results.sample_indices - inj_pos2) <= 1)
    assert np.any(mask3)
    idx3 = np.flatnonzero(mask3)[0]
    assert results.sample_indices[idx3] == inj_pos2
    rel_err2 = abs(results.snr[idx3] - ref_val2) / abs(ref_val2)
    assert rel_err2 < 1e-4


def test_window_series():
    rng = np.random.default_rng(999)
    counts = [200, 500]
    taps = [rng.standard_normal(c).astype(np.float32) for c in counts]

    bank = TimeDomainFilterBank(
        taps, tap_counts=counts,
        tap_sample_rate=2048, data_sample_rate=2048,
        engine='flat', threshold=50.0
    )

    data_len = 65536
    data = (rng.standard_normal(data_len) + 1j * rng.standard_normal(data_len)).astype(np.complex64)

    # Inject inside valid slice [20000, 40000)
    data[30000 - 100 : 30000 - 100 + 200] += taps[0] * 30.0
    # Inject outside valid slice at 10000 and 50000
    data[10000 - 100 : 10000 - 100 + 200] += taps[0] * 30.0
    data[50000 - 100 : 50000 - 100 + 200] += taps[0] * 30.0

    valid_slice = slice(20000, 40000)
    results = bank.filter_series(data, windows=valid_slice)

    # Triggers must lie entirely within [20000, 40000)
    assert np.all(results.sample_indices >= 20000)
    assert np.all(results.sample_indices < 40000)
    assert 30000 in results.sample_indices
    assert 10000 not in results.sample_indices
    assert 50000 not in results.sample_indices


def test_filter_f_and_block_length_properties():
    rng = np.random.default_rng(777)
    counts = [150, 1800]
    taps = [rng.standard_normal(c).astype(np.float32) for c in counts]

    bank = TimeDomainFilterBank(
        taps, tap_counts=counts,
        engine='flat'
    )

    assert len(bank.filters_f) == 2
    assert len(bank.block_lengths) == 2
    assert bank.get_block_length(0) in (512, 1024, 2048, 4096, 8192, 16384)
    assert bank.get_block_length(1) in (512, 1024, 2048, 4096, 8192, 16384)
    assert len(bank.get_filter_f(0)) == bank.get_block_length(0)
    assert len(bank.get_filter_f(1)) == bank.get_block_length(1)


def test_reference_must_cover_every_hierarchical_block_size():
    """A 1-D profile without delta_f fits one block size; a bank with two must
    get a dict (or delta_f).  It used to drop the profile silently for the other
    group, which then failed later with a misleading gate-model error."""
    rng = np.random.default_rng(6)
    counts = [251] * 8 + [1501] * 8
    taps = [rng.standard_normal(c).astype(np.float32) / np.sqrt(c) for c in counts]

    def prof(n):
        p = np.zeros(n, np.float32); p[:n // 2 + 1] = 1
        return p / p.sum()

    bank = TimeDomainFilterBank(taps, counts, engine='hier', threshold=5.0)
    ns = sorted({g.n for g in bank._groups})
    assert len(ns) == 2
    with pytest.raises(ValueError) as e:
        bank.set_reference(prof(ns[1]))
    assert str(ns[0]) in str(e.value) and "dict" in str(e.value)
    with pytest.raises(ValueError) as e:
        bank.set_reference({ns[1]: prof(ns[1])})
    assert str(ns[0]) in str(e.value)
    bank.set_reference({n: prof(n) for n in ns})
    bank.filter_series(np.zeros(32 * 4096, np.complex64))


def test_hierarchical_mode_and_reference():
    from spectral_profiles import make_spectral_profile
    rng = np.random.default_rng(888)
    counts = [200, 400]
    taps = [rng.standard_normal(c).astype(np.float32) for c in counts]

    bank = TimeDomainFilterBank(
        taps, tap_counts=counts,
        engine='hier', threshold=5.5,
        false_dismissal=0.001,
        fft_lengths=[4096]
    )

    # Set realistic reference spectrum
    ref = make_spectral_profile('inspiral_canonical', 4096)
    bank.set_reference(ref)

    data_len = 65536
    data = (rng.standard_normal(data_len) + 1j * rng.standard_normal(data_len)).astype(np.complex64)
    # Inject loud signal
    data[25000 - 100 : 25000 - 100 + 200] += taps[0] * 50.0

    results = bank.filter_series(data)
    assert isinstance(results, FilterResults)
    mask = (results.template_indices == 0) & (results.sample_indices == 25000)
    assert np.any(mask)


def test_partition_boundary_no_dropped_templates():
    """Verify that templates near max_batch boundaries with FFT size changes are not dropped."""
    from matchedfilter.time_domain import _partition_templates
    # Simulate group 449: 110 templates with 4096-sized taps and 9 with 8192-sized taps
    counts = np.array([500] * 110 + [1251] * 9, dtype=np.int64)
    groups, order = _partition_templates(counts, max_batch=64)
    total_partitioned = sum(g[1] - g[0] for g in groups)
    assert total_partitioned == len(counts), f"Expected {len(counts)}, got {total_partitioned}"
    assert len(order) == len(counts)
    for g in groups:
        assert g[1] - g[0] <= 64


def test_filter_series_binsize_ragged_edges():
    """Verify that filter_series with binsize handles ragged edge blocks without error."""
    rng = np.random.default_rng(123)
    counts = [200, 500]
    taps = [rng.standard_normal(c).astype(np.float32) for c in counts]
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='flat', threshold=5.0)

    data = (rng.standard_normal(65536) + 1j * rng.standard_normal(65536)).astype(np.complex64)
    # Valid slice with non-aligned boundaries creating ragged edge blocks
    res = bank.filter_series(data, windows=slice(100, 20000), binsize=200)
    assert isinstance(res, FilterResults)
    if len(res.sample_indices) > 0:
        assert np.all(res.sample_indices >= 100)
        assert np.all(res.sample_indices < 20000)


def test_filter_series_single_template_zero_threshold():
    """Verify that filter_series supports filtering a specific template with threshold=0.0."""
    rng = np.random.default_rng(456)
    counts = [200, 500, 300]
    taps = [rng.standard_normal(c).astype(np.float32) for c in counts]
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='flat', threshold=1000.0)

    data = (rng.standard_normal(32768) + 1j * rng.standard_normal(32768)).astype(np.complex64)
    # With bank threshold=1000.0, nothing triggers.
    res_none = bank.filter_series(data, template_index=1)
    assert len(res_none.sample_indices) == 0

    # With threshold=0.0 and binsize=200 over a 2000-sample window, each bin produces a peak
    res_zero = bank.filter_series(data, windows=slice(5000, 7000), binsize=200, threshold=0.0, template_index=1)
    assert len(res_zero.sample_indices) > 0
    assert np.all(res_zero.template_indices == 1)
    assert np.all(res_zero.sample_indices >= 5000)
    assert np.all(res_zero.sample_indices < 7000)


def test_filter_series_template_index_bounds_check():
    """Verify that filter_series raises IndexError for invalid template_index."""
    import pytest
    rng = np.random.default_rng(456)
    counts = [200, 500]
    taps = [rng.standard_normal(c).astype(np.float32) for c in counts]
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='flat', threshold=5.0)

    data = (rng.standard_normal(4096) + 1j * rng.standard_normal(4096)).astype(np.complex64)
    with pytest.raises(IndexError):
        bank.filter_series(data, template_index=-1)
    with pytest.raises(IndexError):
        bank.filter_series(data, template_index=2)


def test_filter_series_hierarchical_single_template_zero_threshold():
    """Verify that hierarchical engine supports un-gated single template filtering with threshold=0.0."""
    from spectral_profiles import make_spectral_profile
    rng = np.random.default_rng(888)
    counts = [200, 400]
    taps = [rng.standard_normal(c).astype(np.float32) for c in counts]
    for i in range(len(taps)):
        taps[i] /= np.linalg.norm(taps[i]) * np.sqrt(2 * 4096)

    bank = TimeDomainFilterBank(
        taps, tap_counts=counts,
        engine='hier', threshold=5.5,
        false_dismissal=0.001,
        fft_lengths=[4096]
    )
    ref = make_spectral_profile('inspiral_canonical', 4096)
    bank.set_reference(ref)

    data_len = 65536
    data = (rng.standard_normal(data_len) + 1j * rng.standard_normal(data_len)).astype(np.complex64)

    # Pure noise with default bank threshold=5.5 is dismissed by coarse gating
    res_default = bank.filter_series(data, template_index=0, binsize=512)
    assert len(res_default.sample_indices) == 0

    # Overridden threshold=0.0 returns peaks for all bins
    res_zero = bank.filter_series(data, threshold=0.0, template_index=0, binsize=512)
    assert len(res_zero.sample_indices) > 0
    assert np.all(res_zero.template_indices == 0)


def test_correlate_series_engines_and_convolution_parity():
    """Verify that correlate_series across all engines matches direct time-domain convolution."""
    rng = np.random.default_rng(42)
    T = 4
    counts = [501, 1501, 3001, 6001]
    max_taps = max(counts)
    taps = np.zeros((T, max_taps), dtype=np.float32)
    for i in range(T):
        taps[i, :counts[i]] = rng.standard_normal(counts[i]).astype(np.float32)

    L_data = 65536
    data = (rng.standard_normal(L_data) + 1j * rng.standard_normal(L_data)).astype(np.complex64)
    scales = rng.uniform(0.5, 2.0, size=T).astype(np.float32)

    for engine in ['corr', 'flat', 'hier']:
        bank = TimeDomainFilterBank(
            taps, tap_counts=counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine=engine
        )
        res = bank.correlate_series(data, scales=scales)
        assert res.shape == (T, L_data)
        assert res.dtype == np.complex64

        for i in range(T):
            fir = taps[i, :counts[i]]
            conv = np.convolve(data, fir[::-1], mode='full')
            m = counts[i] // 2
            direct = conv[m : m + L_data] * scales[i]

            g, ti_loc = bank._template_map[i]
            c_bad = g.c_bad
            valid_sl = slice(c_bad, L_data - c_bad)
            diff = np.max(np.abs(res[i, valid_sl] - direct[valid_sl]))
            rel = diff / np.max(np.abs(direct[valid_sl]))
            assert rel < 1e-4, f"Engine {engine} template {i} diff too high: {rel}"


def test_correlate_series_out_and_template_index():
    """Verify out buffer reuse and template_index single-template correlation."""
    rng = np.random.default_rng(123)
    T = 3
    counts = [501, 3001, 501]
    max_taps = max(counts)
    taps = np.zeros((T, max_taps), dtype=np.float32)
    for i in range(T):
        taps[i, :counts[i]] = rng.standard_normal(counts[i]).astype(np.float32)

    L_data = 32768
    data = (rng.standard_normal(L_data) + 1j * rng.standard_normal(L_data)).astype(np.complex64)
    scales = np.array([1.2, 0.8, 1.5], dtype=np.float32)

    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='corr')

    # Full output into preallocated buffer
    out_buf = np.empty((T, L_data), dtype=np.complex64)
    res = bank.correlate_series(data, scales=scales, out=out_buf)
    assert res is out_buf

    # Single template correlation with and without out
    for i in range(T):
        res_single = bank.correlate_series(data, scales=scales, template_index=i)
        assert res_single.shape == (L_data,)
        assert np.allclose(res_single, res[i])

        out_1d = np.empty(L_data, dtype=np.complex64)
        res_1d = bank.correlate_series(data, scales=scales, template_index=i, out=out_1d)
        assert res_1d is out_1d
        assert np.allclose(res_1d, res[i])

    # Out validation
    with pytest.raises(ValueError):
        bank.correlate_series(data, out=np.empty((T + 1, L_data), dtype=np.complex64))
    with pytest.raises(ValueError):
        bank.correlate_series(data, out=np.empty((T, L_data), dtype=np.complex128))
    with pytest.raises(IndexError):
        bank.correlate_series(data, template_index=-1)
    with pytest.raises(IndexError):
        bank.correlate_series(data, template_index=T)


def test_correlate_series_window():
    """A window restricts block computation and matches the unwindowed output inside it."""
    rng = np.random.default_rng(999)
    T = 2
    counts = [1001, 3001]
    taps = rng.standard_normal((T, 3001)).astype(np.float32)
    L_data = 65536
    data = (rng.standard_normal(L_data) + 1j * rng.standard_normal(L_data)).astype(np.complex64)

    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='corr')
    res_full = bank.correlate_series(data)

    v_slice = slice(20000, 40000)
    res_slice = bank.correlate_series(data, windows=v_slice)

    # Valid slice window must match full
    np.testing.assert_allclose(res_slice[:, 20000:40000], res_full[:, 20000:40000], atol=1e-5)
    # Outside margins must remain zero
    assert np.all(res_slice[:, :14000] == 0)
    assert np.all(res_slice[:, 45000:] == 0)


def test_correlation_filter_scales_support():
    """Verify CorrelationFilter.run and run_series scales parameter."""
    from matchedfilter import CorrelationFilter
    rng = np.random.default_rng(777)
    n = 2048
    T = 3
    filt = CorrelationFilter(n, ntemplates=T, valid=(100, 1900))
    tmpl = (rng.standard_normal((T, n)) + 1j * rng.standard_normal((T, n))).astype(np.complex64)
    filt.set_templates(tmpl)

    data = (rng.standard_normal((1, n)) + 1j * rng.standard_normal((1, n))).astype(np.complex64)
    filt.set_data(data)

    scales = np.array([0.5, 2.0, 1.5], dtype=np.float32)

    # Circular run
    res_unscaled = filt.run()
    res_scaled = filt.run(scales=scales)
    for i in range(T):
        np.testing.assert_allclose(res_scaled[0, i], res_unscaled[0, i] * scales[i], rtol=1e-5)

    # Continuous run_series
    ser = (rng.standard_normal(16384) + 1j * rng.standard_normal(16384)).astype(np.complex64)
    ser_unscaled = filt.run_series(ser).copy()
    ser_scaled = filt.run_series(ser, scales=scales)
    for i in range(T):
        np.testing.assert_allclose(ser_scaled[i], ser_unscaled[i] * scales[i], rtol=1e-5)





def _corr_bank_taps(layout, rng):
    if layout == "one":
        counts = [451] * 8
    elif layout == "two":
        counts = [251] * 6 + [1151] * 6          # contiguous groups
    else:
        counts = [251, 1151] * 6                 # interleaved groups
    taps = [rng.standard_normal(c).astype(np.float32) / np.sqrt(c) for c in counts]
    return taps, counts


# The layouts below are the valid-fraction rule's groupings; a CPU bank otherwise prices its own
# (and a GPU bank does not), so pin the sizes to compare the same groups on both devices.
PINNED = [2048, 4096]


@pytest.mark.parametrize("layout", ["one", "two", "interleaved"])
@pytest.mark.parametrize("window", [None, slice(20000, 90000)])
def test_correlate_series_gpu_matches_cpu_for_every_group_layout(layout, window):
    """The GPU continuous path needs a library-allocated shared output. The
    contiguous-group branch used to pass a plain NumPy slice and raised
    'continuous output and starts must be shared GPU buffers'."""
    from conftest import usable_gpu
    gpu = usable_gpu()
    if gpu is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(7)
    taps, counts = _corr_bank_taps(layout, rng)
    S = 32 * 4096
    ser = ((rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2)).astype(np.complex64)
    cpu = TimeDomainFilterBank(taps, counts, engine='corr', fft_lengths=PINNED).correlate_series(ser, windows=window)
    gbank = TimeDomainFilterBank(taps, counts, engine='corr', device=gpu, fft_lengths=PINNED)
    got = gbank.correlate_series(ser, windows=window)
    scale = np.abs(cpu).max()
    assert scale > 0
    assert np.max(np.abs(got - cpu)) <= 1e-5 * scale
    # Same bank, a different window: the shared workspace must not leak the
    # previous call's samples into the new result.
    window2 = slice(60000, 61000)
    cpu2 = TimeDomainFilterBank(taps, counts, engine='corr', fft_lengths=PINNED).correlate_series(ser, windows=window2)
    got2 = gbank.correlate_series(ser, windows=window2)
    assert np.max(np.abs(got2 - cpu2)) <= 1e-5 * np.abs(cpu2).max()
    got_t = gbank.correlate_series(ser, windows=window, template_index=3)
    assert np.max(np.abs(got_t - cpu[3])) <= 1e-5 * scale


@pytest.mark.parametrize("layout", ["two", "interleaved"])
def test_correlate_series_window_before_first_block_is_zero(layout):
    """A window that no block's valid region reaches used to pass an empty
    block list to the execution layer, which raised."""
    rng = np.random.default_rng(8)
    taps, counts = _corr_bank_taps(layout, rng)
    S = 16 * 4096
    ser = ((rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2)).astype(np.complex64)
    bank = TimeDomainFilterBank(taps, counts, engine='corr')
    assert not np.any(bank.correlate_series(ser, windows=slice(0, 50)))
    assert not np.any(bank.correlate_series(ser, windows=slice(0, 50), template_index=2))


def _whitened_inspiral_bank(rng, counts, rate=2048.0):
    """Templates whose spectra follow an inspiral-like output-power profile, and that profile
    on a fine grid (delta_f = 1/16 Hz): what pycbc hands the bank as its reference."""
    df = 1.0 / 16
    f = np.arange(int(rate / 2 / df) + 1) * df
    w = np.where((f > 20) & (f < 900), np.maximum(f, 1.0) ** (-7.0 / 3), 0.0)
    taps = []
    for c in counts:
        ff = np.fft.rfftfreq(c, 1 / rate)
        amp = np.sqrt(np.interp(ff, f, w))
        h = np.fft.irfft(amp * np.exp(2j * np.pi * rng.random(ff.size)), c)
        taps.append((h / np.linalg.norm(h)).astype(np.float32))
    return taps, w, df


def test_block_size_chosen_by_cost_when_peak_granularity_is_stated():
    rng = np.random.default_rng(5)
    counts = list(rng.integers(300, 900, 48))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=5.5,
                                false_dismissal=0.001, binsize=256)
    assert bank._built is None                       # nothing built before the reference
    bound = bank.max_block_length
    bank.set_reference(w, delta_f=df)
    assert bank.max_block_length == bound            # the announced bound holds after the choice
    longest = max(counts)
    for g in bank.groups:
        assert longest < g['n'] <= bound
    assert sum(c for c, _ in bank.chosen_layout) == len(counts)

    L = 1 << 16
    data = ((rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
    t0, k = 30000, 7
    data[t0 - counts[k] // 2: t0 - counts[k] // 2 + counts[k]] += 12.0 * taps[k]
    res = bank.filter_series(data)
    hit = (res.template_indices == k) & (np.abs(res.sample_indices - t0) <= 1)
    assert hit.any()
    # every reported peak is the exact correlation at its sample (centre tap (count - 1) // 2)
    for ti in np.unique(res.template_indices):
        fir = taps[ti]
        m = (counts[ti] - 1) // 2
        direct = np.convolve(data, fir[::-1], mode='full')[m: m + L]
        sel = res.template_indices == ti
        np.testing.assert_allclose(res.snr[sel], direct[res.sample_indices[sel]], rtol=1e-3, atol=1e-3)


def test_block_size_rule_stands_without_peak_granularity():
    rng = np.random.default_rng(6)
    counts = [400, 700]
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=5.5)
    before = [g['n'] for g in bank.groups]
    bank.set_reference(w, delta_f=df)
    assert [g['n'] for g in bank.groups] == before
    assert not hasattr(bank, 'chosen_layout')


def test_unpinned_band_of_zero_still_chooses_block_size():
    rng = np.random.default_rng(7)
    counts = [400, 700]
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=5.5,
                                binsize=256, coarse_band_hz=0.0)      # pycbc's "not pinned"
    bank.set_reference(w, delta_f=df)
    assert hasattr(bank, 'chosen_layout')


def test_correlation_layout_is_priced_and_exact():
    """engine='corr' picks its partition by calibrated cost: every template in exactly one group,
    each group's transform longer than its longest filter, no costlier than the valid-fraction
    rule under the same costs, and the output still the direct correlation."""
    from matchedfilter import time_domain as td
    rng = np.random.default_rng(11)
    counts = np.sort(rng.integers(15, 5000, 25))
    taps = np.zeros((len(counts), counts.max()), np.float32)
    for i, c in enumerate(counts):
        taps[i, :c] = rng.standard_normal(c)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='corr')
    seen = np.concatenate([g['template_indices'] for g in bank.groups])
    assert sorted(seen.tolist()) == list(range(len(counts)))
    for g in bank.groups:
        assert g['n'] > counts[g['template_indices']].max()

    def modelled(groups):
        return sum((td._corr_block_costs(n)[0] + (j - i) * td._corr_block_costs(n)[1]) / (n - L + 1)
                   for i, j, n, L in groups)
    legacy, _ = td._partition_templates(counts, candidate_ns=(2048, 4096, 8192, 16384, 32768, 65536))
    legacy_eff = [(i, j, n, int(np.sort(counts)[j - 1])) for i, j, n, _ in legacy]
    assert modelled(td._corr_layout(counts, (2048, 4096, 8192, 16384, 32768, 65536), None)[0]) <= modelled(legacy_eff) * (1 + 1e-12)

    L = 1 << 16
    data = (rng.standard_normal(L) + 1j * rng.standard_normal(L)).astype(np.complex64)
    res = bank.correlate_series(data)
    for i in (0, len(counts) // 2, len(counts) - 1):
        m = (counts[i] - 1) // 2                      # centre tap of an even-length filter
        direct = np.convolve(data, taps[i, :counts[i]][::-1], mode='full')[m: m + L]
        g, _ = bank._template_map[i]
        sl = slice(g.c_bad, L - g.c_bad)
        assert np.max(np.abs(res[i, sl] - direct[sl])) / np.max(np.abs(direct[sl])) < 1e-4


def test_reference_caches_never_serve_a_recycled_id():
    """A freed reference array's id is reused by the next allocation; the bank must not serve
    the new array the old one's binned profile."""
    rng = np.random.default_rng(12)
    counts = [400, 700]
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=5.5)
    n = bank.groups[0]['n']
    for scale_lo in (1.0, 50.0, 1.0, 50.0):
        prof = w.copy()
        prof[: len(prof) // 8] *= scale_lo           # a different shape each round, often the same id
        bank.set_reference(prof, delta_f=df)
        got = bank._groups[0].plan._pending_ref
        from matchedfilter.gatechain import rebin_profile
        want = rebin_profile(prof, df, bank.data_sample_rate, n).astype(np.float32)
        np.testing.assert_allclose(np.asarray(got, np.float64), want / want.sum(), rtol=1e-6)
        del prof


def test_single_template_call_equals_the_ungated_bank_for_that_template():
    """filter_series(template_index=k) runs a one-template plan; it must report exactly what the
    group's whole ungated plan reports for template k."""
    rng = np.random.default_rng(13)
    counts = list(rng.integers(300, 600, 24))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=5.5)
    bank.set_reference(w, delta_f=df)
    L = 1 << 16
    x = rng.standard_normal(L); X = np.fft.fft(x); X[L // 2:] = 0
    ser = (np.fft.ifft(X) * np.sqrt(2)).astype(np.complex64)
    win = slice(9000, 40000)
    every = bank.filter_series(ser, windows=win, binsize=61, threshold=0.0)
    for k in (0, 7, 23):
        one = bank.filter_series(ser, windows=win, binsize=61, threshold=0.0, template_index=k)
        sel = every.template_indices == k
        assert sel.sum() > 0 and len(one.snr) == sel.sum()
        o1 = np.argsort(one.sample_indices); o2 = np.argsort(every.sample_indices[sel])
        np.testing.assert_array_equal(one.sample_indices[o1], every.sample_indices[sel][o2])
        np.testing.assert_array_equal(one.snr[o1], every.snr[sel][o2])


def test_gpu_correlation_bank_prices_its_own_layout_and_matches_cpu():
    """Each device prices its correlation layout with its own block costs; whatever groups result,
    the correlation agrees with the CPU's away from the series edges (where coverage depends on
    the transform size)."""
    from conftest import usable_gpu
    gpu = usable_gpu()
    if gpu is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(21)
    counts = np.sort(rng.integers(15, 5000, 24))
    taps = np.zeros((len(counts), counts.max()), np.float32)
    for i, c in enumerate(counts):
        taps[i, :c] = rng.standard_normal(c) / np.sqrt(c)
    S = 1 << 18
    ser = ((rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2)).astype(np.complex64)
    cpu = TimeDomainFilterBank(taps, tap_counts=counts, engine='corr')
    g = TimeDomainFilterBank(taps, tap_counts=counts, engine='corr', device=gpu)
    assert sum(x['count'] for x in g.groups) == len(counts)
    a, b = cpu.correlate_series(ser), g.correlate_series(ser)
    edge = 2 * int(counts.max())
    inner = slice(edge, S - 65536)                 # past the largest block's tail on either device
    scale = np.abs(a[:, inner]).max()
    assert np.max(np.abs(b[:, inner] - a[:, inner])) <= 1e-5 * scale


@pytest.mark.parametrize("pack", [False, True])
def test_gpu_hierarchical_bank_matches_cpu_including_packed_templates(pack):
    """The fine-stage bank finds the same peaks on a GPU as on the CPU. Packed templates hold
    the Nyquist bin in the imaginary part of bin 0; a GPU plan that zero-padded them instead of
    unpacking the Hermitian spectrum was off by ~3e-3."""
    from conftest import usable_gpu
    gpu = usable_gpu()
    if gpu is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(4)
    counts = list(rng.integers(200, 400, 24))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    S = 1 << 17
    X = np.fft.fft(rng.standard_normal(S))
    X[S // 2:] = 0
    ser = (np.fft.ifft(X) * 2).astype(np.complex64)      # analytic, unit variance per quadrature
    found = []
    for dev in (None, gpu):
        bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                    false_dismissal=1e-3, device=dev, fft_lengths=[2048],
                                    pack_templates=pack)
        bank.set_reference(w, delta_f=df)
        r = bank.filter_series(ser, binsize=2048)
        found.append(dict(zip(zip(r.template_indices.tolist(), r.sample_indices.tolist()), r.snr)))
    cpu, dev = found
    # Each device prices its own gate chain, so near-threshold noise peaks may be dismissed
    # differently (the gate is calibrated for signals at the threshold SNR): a peak found on
    # one side only must lie within 0.25 of the threshold. (On the L40S the CUDA-priced
    # chain dismisses two peaks at SNR 4.51 and 4.69 that the CPU's chain keeps; the CPU
    # with the same pinned chain dismisses exactly the same two.) The precision claim --
    # the packed Nyquist bin -- is the SNR agreement on every common peak.
    common = set(cpu) & set(dev)
    assert len(common) >= 10
    for k in set(cpu) ^ set(dev):
        assert abs(cpu[k] if k in cpu else dev[k]) < 4.5 + 0.25, k
    assert max(abs(dev[k] - cpu[k]) / abs(cpu[k]) for k in common) < 1e-5


@pytest.mark.parametrize("device", ["cpu", "gpu"])
def test_filter_series_many_matches_one_call_at_a_time(device, monkeypatch):
    """A batch returns exactly what the calls return one at a time -- including a bank that
    appears in several jobs with different series (in flight together on a GPU) and
    single-template calls -- whatever the device does to overlap them."""
    from conftest import usable_gpu
    # The model's choices only: trials would move single-template calls between devices
    # mid-test, and this compares GPU deferral against GPU calls exactly.
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    dev = None
    if device == "gpu":
        dev = usable_gpu()
        if dev is None:
            pytest.skip("no usable GPU")
    rng = np.random.default_rng(8)
    banks = []
    for _ in range(3):
        counts = list(rng.integers(200, 400, 40))
        taps, w, df = _whitened_inspiral_bank(rng, counts)
        b = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                 false_dismissal=1e-3, device=dev, fft_lengths=[2048], binsize=2048)
        b.set_reference(w, delta_f=df)
        banks.append(b)
    S = 1 << 17
    series = []
    for _ in range(2):
        X = np.fft.fft(rng.standard_normal(S))
        X[S // 2:] = 0
        series.append((np.fft.ifft(X) * 2).astype(np.complex64))
    jobs = [(b, x, dict(windows=slice(3000, S - 3000))) for b in banks for x in series]
    jobs += [(banks[0], series[1], dict(windows=slice(40000, 60000), binsize=61, threshold=0.0,
                                        template_index=7))]
    one = [b.filter_series(x, **kw) for b, x, kw in jobs]
    many = TimeDomainFilterBank.filter_series_many(jobs)
    assert sum(len(r.snr) for r in one[:-1]) >= 5
    for r1, r2 in zip(one, many):
        for f in r1._fields:
            np.testing.assert_array_equal(getattr(r1, f), getattr(r2, f))


def test_filter_series_many_mixes_deferred_and_synchronous_calls_on_one_plan(monkeypatch):
    """Follow-up-style calls in one batch: one template's single plan serves several jobs,
    some with windows that give mixed bin counts (a synchronous path on some backends) and
    some deferred. A synchronous call must not reuse a slot a deferred call still holds --
    that left a fence wait that never returned."""
    from conftest import usable_gpu
    monkeypatch.setenv("MF_AUTOTUNE", "0")     # keep the follow-ups on the GPU plan
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(12)
    counts = list(rng.integers(200, 400, 30))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=5.0,
                                false_dismissal=1e-3, device=dev, fft_lengths=[2048], binsize=2048)
    bank.set_reference(w, delta_f=df)
    S = 1 << 17
    X = np.fft.fft(rng.standard_normal(S))
    X[S // 2:] = 0
    x = (np.fft.ifft(X) * 2).astype(np.complex64)
    jobs = [(bank, x, dict(windows=slice(c - 15000, c + 15000), binsize=61, threshold=0.0,
                           template_index=t))
            for t, c in ((3, 30000), (3, 61000), (8, 47000), (8, 90000), (3, 70000)) * 4]
    one = [bank.filter_series(x, **kw) for _, x, kw in jobs]
    many = TimeDomainFilterBank.filter_series_many(jobs)
    for r1, r2 in zip(one, many):
        np.testing.assert_array_equal(r1.sample_indices, r2.sample_indices)
        np.testing.assert_array_equal(r1.snr, r2.snr)


def test_single_template_calls_choose_the_faster_device_and_agree():
    """A GPU bank's single-template calls are timed on the GPU and on a CPU plan for their
    first calls, then run on the faster; either way they give the GPU's answers to ~1e-5."""
    from conftest import usable_gpu
    from matchedfilter import time_domain as td
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(14)
    counts = list(rng.integers(200, 400, 20))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    S = 1 << 17
    X = np.fft.fft(rng.standard_normal(S))
    X[S // 2:] = 0
    x = (np.fft.ifft(X) * 2).astype(np.complex64)
    gpu = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=5.0,
                               false_dismissal=1e-3, device=dev, fft_lengths=[2048], binsize=2048)
    cpu = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=5.0,
                               false_dismissal=1e-3, fft_lengths=[2048], binsize=2048)
    for b in (gpu, cpu):
        b.set_reference(w, delta_f=df)
    td._SINGLE_CHOICE.clear()
    for k, c in enumerate(range(20000, 110000, 7000)):
        kw = dict(windows=slice(c - 9000, c + 9000), binsize=61, threshold=0.0, template_index=k % 5)
        r_g, r_c = gpu.filter_series(x, **kw), cpu.filter_series(x, **kw)
        np.testing.assert_array_equal(r_g.sample_indices, r_c.sample_indices)
        scale = np.maximum(np.abs(r_c.snr), 1.0)
        assert np.max(np.abs(r_g.snr - r_c.snr) / scale) < 1e-4
    (state,) = td._SINGLE_CHOICE.values()
    assert state["winner"] in ("gpu", "cpu") and len(state["gpu"]) >= 4 and len(state["cpu"]) >= 4


def test_segment_plan_replays_and_matches(monkeypatch):
    """A recurring job set (same banks, windows and device input buffers, rewritten in place
    each segment) is traced once and then replayed; every replay returns what
    filter_series_many returns for the same data."""
    from conftest import usable_gpu
    from matchedfilter.time_domain import SegmentPlan
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_SEGMENT_REPLAY", "1")      # experimental: exercised here
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(31)
    banks = []
    for _ in range(3):
        counts = list(rng.integers(200, 400, 37))           # odd: exercises dispatch padding
        taps, w, df = _whitened_inspiral_bank(rng, counts)
        b = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                 false_dismissal=1e-3, device=dev, fft_lengths=[2048], binsize=2048)
        b.set_reference(w, delta_f=df)
        banks.append(b)
    S = 1 << 17
    rows = banks[0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, b in enumerate(banks)]
    plan = SegmentPlan()
    total = 0
    for seg in range(4):
        for i in range(len(banks)):
            X = np.fft.fft(rng.standard_normal(S))
            X[S // 2:] = 0
            rows[i] = (np.fft.ifft(X) * 2).astype(np.complex64)
        got = plan.run(jobs)
        want = TimeDomainFilterBank.filter_series_many(jobs)
        for r1, r2 in zip(want, got):
            for f in r1._fields:
                np.testing.assert_array_equal(getattr(r1, f), getattr(r2, f))
        total += sum(len(r.snr) for r in got)
    if getattr(rows, 'ctypes', None) is not None and plan.replays == 0:
        from matchedfilter._shared import shared_buffer
        ctx = banks[0]._groups[0].plan._gpu
        # Replay is implemented for Vulkan recordings only; elsewhere this is
        # filter_series_many, which the comparison above already checks.
        if shared_buffer(rows, ctx) is not None and type(ctx).__module__.endswith("_vkcompute"):
            pytest.fail("a device-resident job set was never replayed")
    assert total >= 5


def test_filter_series_many_without_wait_overlaps_and_matches(monkeypatch):
    """wait=False hands back results to collect later; two batches in flight on the same banks
    (different input buffers) both come back exactly as synchronous calls give them."""
    from conftest import usable_gpu
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(41)
    banks = []
    for _ in range(2):
        counts = list(rng.integers(200, 400, 30))
        taps, w, df = _whitened_inspiral_bank(rng, counts)
        b = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                 false_dismissal=1e-3, device=dev, fft_lengths=[2048], binsize=2048)
        b.set_reference(w, delta_f=df)
        banks.append(b)
    S = 1 << 16
    def series():
        X = np.fft.fft(rng.standard_normal(S))
        X[S // 2:] = 0
        return (np.fft.ifft(X) * 2).astype(np.complex64)
    xs = [series() for _ in range(4)]
    batch1 = [(b, xs[i], dict(windows=slice(2000, S - 2000))) for i, b in enumerate(banks)]
    batch2 = [(b, xs[2 + i], dict(windows=slice(2000, S - 2000))) for i, b in enumerate(banks)]
    f1 = TimeDomainFilterBank.filter_series_many(batch1, wait=False)
    f2 = TimeDomainFilterBank.filter_series_many(batch2, wait=False)
    got = [f.result() for f in f1 + f2]
    want = [b.filter_series(x, **kw) for b, x, kw in batch1 + batch2]
    assert sum(len(r.snr) for r in want) >= 3
    for r1, r2 in zip(want, got):
        np.testing.assert_array_equal(r1.sample_indices, r2.sample_indices)
        np.testing.assert_array_equal(r1.snr, r2.snr)


def test_gpu_follow_up_batch_matches_direct_calls(monkeypatch):
    """Single-template calls on device-resident rows go out as one forward and one item
    submission per template group; each job's FilterResults equal its direct call exactly,
    peak order included (one call per bin count), with edge blocks of fewer bins."""
    from conftest import usable_gpu
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_SINGLE_DEVICE", "bank")
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(53)
    counts = list(rng.integers(200, 400, 25))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=5.0,
                                false_dismissal=1e-3, device=dev, fft_lengths=[2048], binsize=2048)
    bank.set_reference(w, delta_f=df)
    S = 1 << 17
    rows = bank.empty_shared((2, S))
    for i in range(2):
        X = np.fft.fft(rng.standard_normal(S))
        X[S // 2:] = 0
        rows[i] = (np.fft.ifft(X) * 2).astype(np.complex64)
    jobs = []
    for k in range(16):
        c0 = int(rng.integers(20000, S - 20000))
        jobs.append((bank, rows[k % 2], dict(windows=slice(c0 - 9000, c0 + 9100), binsize=61,
                                             threshold=0.0, template_index=int(rng.integers(0, 25)))))
    from matchedfilter import _vkcompute
    used = []
    if hasattr(_vkcompute.Context, "peaks_items"):
        orig = _vkcompute.Context.peaks_items
        monkeypatch.setattr(_vkcompute.Context, "peaks_items",
                            lambda self, *a, **k: used.append(1) or orig(self, *a, **k))
    many = TimeDomainFilterBank.filter_series_many(jobs)
    direct = [b.filter_series(x, **kw) for b, x, kw in jobs]
    for r1, r2 in zip(direct, many):
        for f in r1._fields:
            np.testing.assert_array_equal(getattr(r1, f), getattr(r2, f))
    if bank._groups[0].plan._gpu is not None and hasattr(bank._groups[0].plan._gpu, "peaks_items"):
        assert used, "the batched follow-up path was not taken"
