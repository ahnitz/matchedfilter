import numpy as np
import pytest
from matchedfilter import MatchedFilter
from matchedfilter.time_domain import TimeDomainFilterBank, AnalyticSeries


def test_decoupled_sample_rate_real_taps_truncation():
    """Taps authored at 4096 Hz, filtered on data at 2048 Hz (truncation)."""
    rng = np.random.default_rng(42)
    # Generate 500 taps at 4096 Hz
    cnt = 500
    taps_4096 = rng.standard_normal(cnt).astype(np.float32)

    bank = TimeDomainFilterBank(
        [taps_4096], tap_counts=[cnt],
        tap_sample_rate=4096.0, data_sample_rate=2048.0,
        engine='flat', fft_lengths=[2048]
    )

    f_bank = bank.get_filter_f(0)
    assert len(f_bank) == 2048

    # Reference: direct FFT of 4096-tap buffer rolled, then two-sided truncated to 2048
    buf_4096 = np.zeros(4096, dtype=np.float32)
    buf_4096[:cnt] = taps_4096
    buf_4096 = np.roll(buf_4096, -(cnt // 2))
    spec_4096 = np.conj(np.fft.fft(buf_4096))

    ref_2048 = np.zeros(2048, dtype=np.complex64)
    ref_2048[:1025] = spec_4096[:1025]
    ref_2048[1025:] = spec_4096[4096 - (2048 - 1025):]

    np.testing.assert_allclose(f_bank, ref_2048, atol=1e-5)


def test_decoupled_sample_rate_real_taps_zeropad():
    """Taps authored at 1024 Hz, filtered on data at 2048 Hz (zero-padding)."""
    rng = np.random.default_rng(43)
    cnt = 300
    taps_1024 = rng.standard_normal(cnt).astype(np.float32)

    bank = TimeDomainFilterBank(
        [taps_1024], tap_counts=[cnt],
        tap_sample_rate=1024.0, data_sample_rate=2048.0,
        engine='flat', fft_lengths=[2048]
    )

    f_bank = bank.get_filter_f(0)
    assert len(f_bank) == 2048

    # Reference: 1024-point FFT zero-padded in high frequencies to 2048
    buf_1024 = np.zeros(1024, dtype=np.float32)
    buf_1024[:cnt] = taps_1024
    buf_1024 = np.roll(buf_1024, -(cnt // 2))
    spec_1024 = np.conj(np.fft.fft(buf_1024))

    ref_2048 = np.zeros(2048, dtype=np.complex64)
    ref_2048[:513] = spec_1024[:513]
    ref_2048[2048 - (1024 - 513):] = spec_1024[513:]

    np.testing.assert_allclose(f_bank, ref_2048, atol=1e-5)


def test_decoupled_sample_rate_complex_analytic():
    """Complex analytic taps at 2048 Hz filtered on 1024 Hz data (analytic truncation)."""
    rng = np.random.default_rng(44)
    cnt = 400
    taps_c = (rng.standard_normal(cnt) + 1j * rng.standard_normal(cnt)).astype(np.complex64)

    bank = TimeDomainFilterBank(
        [taps_c], tap_counts=[cnt],
        tap_sample_rate=2048.0, data_sample_rate=1024.0,
        engine='flat', fft_lengths=[1024]
    )

    f_bank = bank.get_filter_f(0)
    assert len(f_bank) == 1024

    buf_2048 = np.zeros(2048, dtype=np.complex64)
    buf_2048[:cnt] = taps_c
    buf_2048 = np.roll(buf_2048, -(cnt // 2))
    spec_2048 = np.conj(np.fft.fft(buf_2048))

    # For analytic complex signals, truncation simply selects [:1024]
    np.testing.assert_allclose(f_bank, spec_2048[:1024], atol=1e-5)


def test_matchedfilter_bandlimited_auto_detection():
    """MatchedFilter.set_templates auto-detects (ntemplates, N//2) and sets _bandlimited."""
    rng = np.random.default_rng(45)
    N = 1024
    T = 4
    spec_half = (rng.standard_normal((T, N // 2)) + 1j * rng.standard_normal((T, N // 2))).astype(np.complex64)

    plan = MatchedFilter(N, ndata=2, ntemplates=T, valid=(128, N - 128))
    assert getattr(plan, '_bandlimited', False) is False

    plan.set_templates(spec_half)
    assert getattr(plan, '_bandlimited', False) is True
    assert plan.k == N // 2

    # Test full-rate series filtering through standard run_series
    data_full = (rng.standard_normal(4096) + 1j * rng.standard_normal(4096)).astype(np.complex64)
    res_full = plan.run_series(data_full, threshold=5.0)
    assert res_full is not None

    # Test critical-rate series filtering through standard run_series with AnalyticSeries
    series_crit = AnalyticSeries(data_full[:2048], sample_rate=1024.0, input_sample_rate=2048.0)
    res_crit = plan.run_series(series_crit, threshold=5.0)
    assert res_crit is not None


def test_matchedfilter_gpu_bandlimited_upload_padding():
    """Verify _gpu_set pads (ntemplates, N//2) to (ntemplates, N) without error."""
    rng = np.random.default_rng(46)
    N = 1024
    T = 2
    spec_half = (rng.standard_normal((T, N // 2)) + 1j * rng.standard_normal((T, N // 2))).astype(np.complex64)

    class MockDevice:
        index = 0
        kind = "gpu"

    class MockContext:
        def __init__(self, idx): pass
        max_dispatch_x = 65535

    plan = MatchedFilter.__new__(MatchedFilter)
    plan.device = MockDevice()
    plan.n = N
    plan.ndata = 1
    plan.ntemplates = T
    plan._init_state()
    plan._gpu = MockContext(0)

    # Calling _gpu_set with half-band should succeed and pad to (T, N)
    plan._gpu_set(None, spec_half, None, "template")
    assert plan._gtmpl is not None
    assert plan._gtmpl.shape == (T, N)
    np.testing.assert_array_equal(plan._gtmpl[:, :N // 2], spec_half)
    np.testing.assert_array_equal(plan._gtmpl[:, N // 2:], np.zeros((T, N // 2), dtype=np.complex64))
