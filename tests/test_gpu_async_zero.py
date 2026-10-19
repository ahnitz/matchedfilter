"""Every GPU: correlate_series(wait=False) leaves the middle stage and its zeroing in
flight (zero_columns_done(wait=False)); other contexts' work is ordered after it on the
device, and settle_writes()/bank.wait() wait on the host. zero_columns itself clears exactly
the columns asked for, kept recordings included."""
import numpy as np
import pytest

import matchedfilter as mf


def _gpu_bank(taps, **kw):
    try:
        b = mf.TimeDomainFilterBank(taps, device="gpu:0", **kw)
        b._groups
    except Exception as e:                      # pragma: no cover - no device
        pytest.skip("no GPU device: %s" % e)
    return b


@pytest.mark.parametrize("wait", [True, False])
def test_zero_columns_clears_exactly_the_ranges(wait):
    bank = _gpu_bank(np.ones((2, 256), np.float32), engine="corr")
    gpu = bank._groups[0].get_correlation_plan()._gpu
    out = bank.empty_shared((6, 4096))
    for rep in range(3):                        # the second and third runs reuse the recording
        out[:] = 1.0 + rep
        expect = out.copy()
        gpu.zero_columns(out, 3, 700)
        gpu.zero_columns(out[2:5], 1000, 4096)  # a block of rows inside the allocation
        expect[:, 3:700] = 0
        expect[2:5, 1000:] = 0
        gpu.zero_columns_done(wait=wait)
        if not wait:
            gpu.settle_writes()
        np.testing.assert_array_equal(out, expect)


def test_series_left_in_flight_feeds_another_bank_exactly():
    rng = np.random.default_rng(7)
    S, nm = 1 << 18, 3
    mid_taps = (rng.standard_normal((nm, 2048)) * 0.02).astype(np.float32)
    fine_taps = (rng.standard_normal((40, 1024)) * 0.03).astype(np.float32)
    mid = _gpu_bank(mid_taps, engine="corr")
    fine = _gpu_bank(fine_taps, engine="corr")
    x = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
    win = slice(S // 4, 3 * S // 4)
    ref_mid = mid.correlate_series(x, windows=win).copy()
    ref = [fine.correlate_series(ref_mid[r], windows=slice(S // 3, S // 2)).copy() for r in range(nm)]
    out = mid.empty_shared((nm, S))
    for _ in range(3):
        out[:] = 1.0                            # stale contents the zeroing must replace
        m = mid.correlate_series(x, windows=win, out=out, wait=False)
        got = [fine.correlate_series(m[r], windows=slice(S // 3, S // 2)) for r in range(nm)]
        mid.wait()
        np.testing.assert_array_equal(out, ref_mid)
        for g, r in zip(got, ref):
            np.testing.assert_allclose(g, r, rtol=0, atol=1e-5 * np.abs(r).max())
