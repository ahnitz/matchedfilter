"""Metal: correlate_series(wait=False) leaves the middle stage and its zeroing in flight
(zero_columns_done(wait=False)); other contexts' command buffers wait for it on the GPU
(an MTLSharedEvent per context), and settle_writes()/bank.wait() wait on the host."""
import sys

import numpy as np
import pytest

import matchedfilter as mf

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="Metal only")


def _metal_bank(taps, **kw):
    try:
        b = mf.TimeDomainFilterBank(taps, device="gpu:0", **kw)
        b._groups
    except Exception as e:                      # pragma: no cover - no device
        pytest.skip("no Metal device: %s" % e)
    return b


def test_series_left_in_flight_feeds_another_bank_exactly():
    rng = np.random.default_rng(7)
    S, nm = 1 << 18, 3
    mid_taps = (rng.standard_normal((nm, 2048)) * 0.02).astype(np.float32)
    fine_taps = (rng.standard_normal((40, 1024)) * 0.03).astype(np.float32)
    mid = _metal_bank(mid_taps, engine="corr")
    if not getattr(mid._groups[0].get_correlation_plan()._gpu, "async_zero", False):
        pytest.skip("backend leaves no zeroing in flight")
    fine = _metal_bank(fine_taps, engine="corr")
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
