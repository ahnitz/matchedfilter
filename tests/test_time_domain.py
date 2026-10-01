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
    assert groups[0][2] in (2048, 4096)

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
    assert short_n in (1024, 2048, 4096)
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


def test_valid_slice_series():
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
    results = bank.filter_series(data, valid_slice=valid_slice)

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
    assert bank.get_block_length(0) in (2048, 4096, 8192, 16384)
    assert bank.get_block_length(1) in (2048, 4096, 8192, 16384)
    assert len(bank.get_filter_f(0)) == bank.get_block_length(0)
    assert len(bank.get_filter_f(1)) == bank.get_block_length(1)


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
    res = bank.filter_series(data, valid_slice=slice(100, 20000), binsize=200)
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
    res_zero = bank.filter_series(data, valid_slice=slice(5000, 7000), binsize=200, threshold=0.0, template_index=1)
    assert len(res_zero.sample_indices) > 0
    assert np.all(res_zero.template_indices == 1)
    assert np.all(res_zero.sample_indices >= 5000)
    assert np.all(res_zero.sample_indices < 7000)


