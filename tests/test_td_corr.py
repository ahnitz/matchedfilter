"""Multi-ISA verification of direct time-domain correlation kernels (td-inl.h)."""
import ctypes as C
import os

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core


@pytest.fixture(scope="module")
def native():
    lib = C.CDLL(_core.__file__)
    V, I = C.c_void_p, C.c_int
    lib.ap_td_corr.argtypes, lib.ap_td_corr.restype = [V, V, I, I, V], None
    lib.ap_td_corr_ex.argtypes, lib.ap_td_corr_ex.restype = [V, I, V, V, I, I, V], None
    return lib


@pytest.fixture(params=mf.targets())
def target_isa(request):
    mf.backend()
    mf.set_target(request.param)
    yield request.param
    mf.set_target(os.environ.get("MF_ISA") or None)


def _reference_corr(x, x_real, tr, ti, length, nlag):
    taps = tr[:length].astype(np.complex128)
    if ti is not None:
        taps = taps + 1j * ti[:length].astype(np.complex128)
    total = nlag + length - 1
    if x_real:
        series = x[:total].astype(np.complex128)
    else:
        raw = x[: 2 * total].astype(np.float64)
        series = raw[0::2] + 1j * raw[1::2]
    # out[i] = sum_{k<L} (tr[k] + j ti[k]) * series[i + k]
    out = np.correlate(series, np.conj(taps), mode="valid")
    assert out.shape == (nlag,)
    interleaved = np.empty(2 * nlag, dtype=np.float64)
    interleaved[0::2] = out.real
    interleaved[1::2] = out.imag
    return interleaved


@pytest.mark.parametrize("mode", ["rr", "rc", "cc", "cr"])
def test_td_corr_all_nlag_1_to_200(native, target_isa, mode):
    rng = np.random.default_rng(42)
    x_real = 1 if mode in ("rr", "rc") else 0
    has_ti = mode in ("rc", "cc")
    max_l, max_nlag = 73, 200
    x = rng.standard_normal(2 * (max_nlag + max_l + 8)).astype(np.float32)
    tr = rng.standard_normal(max_l).astype(np.float32)
    ti = rng.standard_normal(max_l).astype(np.float32) if has_ti else None
    ti_ptr = 0 if ti is None else ti.ctypes.data

    guard = np.float32(-9876.5)
    buf = np.empty(2 * max_nlag + 16, dtype=np.float32)

    for length in (1, 2, 3, 4, 5, 7, 8, 16, 31, 64, 73):
        for nlag in range(1, 201):
            buf.fill(guard)
            out_view = buf[4 : 4 + 2 * nlag]
            native.ap_td_corr_ex(
                x.ctypes.data, x_real, tr.ctypes.data, ti_ptr, length, nlag, out_view.ctypes.data
            )
            assert np.all(buf[:4] == guard)
            assert np.all(buf[4 + 2 * nlag :] == guard)
            ref = _reference_corr(x, x_real, tr, ti, length, nlag)
            scale = max(float(np.max(np.abs(ref))), 1.0)
            assert np.max(np.abs(out_view.astype(np.float64) - ref)) <= 1e-6 * scale
            if mode == "rr":
                assert np.all(out_view[1::2] == 0.0)


@pytest.mark.parametrize("mode", ["rr", "rc", "cc", "cr"])
def test_td_corr_tap_lengths_up_to_1024(native, target_isa, mode):
    rng = np.random.default_rng(109)
    x_real = 1 if mode in ("rr", "rc") else 0
    has_ti = mode in ("rc", "cc")
    max_l, nlag = 1024, 67
    x = rng.standard_normal(2 * (nlag + max_l + 8)).astype(np.float32)
    tr = rng.standard_normal(max_l).astype(np.float32)
    ti = rng.standard_normal(max_l).astype(np.float32) if has_ti else None
    ti_ptr = 0 if ti is None else ti.ctypes.data
    out = np.empty(2 * nlag, dtype=np.float32)

    tap_lengths = (
        list(range(1, 25))
        + [31, 32, 33, 47, 48, 49, 63, 64, 65, 127, 128, 129, 255, 256, 257, 511, 512, 513, 1023, 1024]
    )
    for length in tap_lengths:
        native.ap_td_corr_ex(
            x.ctypes.data, x_real, tr.ctypes.data, ti_ptr, length, nlag, out.ctypes.data
        )
        ref = _reference_corr(x, x_real, tr, ti, length, nlag)
        scale = max(float(np.max(np.abs(ref))), 1.0)
        assert np.max(np.abs(out.astype(np.float64) - ref)) <= 1.5e-6 * scale
        if mode == "cr":
            out_cr = np.empty(2 * nlag, dtype=np.float32)
            native.ap_td_corr(x.ctypes.data, tr.ctypes.data, length, nlag, out_cr.ctypes.data)
            np.testing.assert_array_equal(out_cr, out)
