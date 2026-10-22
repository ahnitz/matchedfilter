"""Every caller-supplied range and size reaching the C core is checked without overflow
(docs/robustness-plan.md, B6). Until 2026-10-22 several checks formed lo + count or a
product of counts in int or Py_ssize_t: a value near the type's maximum wrapped, the check
passed, and the kernel read or wrote out of bounds. Each case must raise and leave the
output untouched."""
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core

INT_MAX = 2**31 - 1


def test_a_q15_screen_range_that_overflows_is_refused():
    f = _core.MF(1024, 2, 4)
    passed = np.full(8, 7, np.uint8)
    if f.q15_lanes() <= 0:
        pytest.skip("no Q15 screen in this build")
    with pytest.raises(ValueError):
        f.q15_screen(0, 1, INT_MAX - 1, 2, 1.0, 0, 1024, passed, bytearray())
    with pytest.raises(ValueError):
        f.q15_screen(INT_MAX - 1, 2, 0, 1, 1.0, 0, 1024, passed, bytearray())
    assert (passed == 7).all()


def test_a_tap_stride_that_overflows_the_size_check_is_refused():
    h = _core.HMF(2048, 1, 4, [256, 512])
    taps = np.zeros(16, np.float32)
    counts = np.full(4, 3, np.int64)
    with pytest.raises(ValueError, match="bad taps"):
        h.set_taps(taps, 2**62, counts)


def test_taps_to_spectra_refuses_an_output_size_that_overflows():
    taps = np.zeros((2, 8), np.float32)
    counts = np.full(2, 8, np.int64)
    out = np.full(16, 3.0, np.float32)
    with pytest.raises(ValueError):
        _core.taps_to_spectra(taps, counts, 2**61, 8, out)
    assert (out == 3.0).all()


@pytest.mark.parametrize("kind", ["flat", "hier"])
def test_a_nan_threshold_is_refused(kind):
    n = 1024
    f = (mf.MatchedFilter(n, 1, 1) if kind == "flat"
         else mf.HierarchicalFilter(n, 1, 1, chain=[256]))
    f.set_templates(np.ones((1, n), np.complex64))
    f.set_data(np.ones((1, n), np.complex64))
    with pytest.raises(ValueError, match="NaN"):
        f.run(binsize=n, threshold=float("nan"))
    with pytest.raises(ValueError, match="NaN"):
        f.run_series(np.zeros(4 * n, np.complex64), binsize=n, threshold=float("nan"))


@pytest.mark.parametrize("make", [lambda: _core.MF(1024, 1, 1),
                                  lambda: _core.HMF(2048, 1, 1, [256])], ids=["MF", "HMF"])
def test_a_filter_object_cannot_be_initialised_twice(make):
    f = make()
    with pytest.raises(RuntimeError, match="already initialised"):
        f.__init__(1024, 1, 1)


def test_forward_cost_refuses_a_size_the_engine_does_not_support():
    """It used to return 1e30 seconds -- a price a caller would store as "slow"."""
    with pytest.raises(ValueError, match="not a size the engine supports"):
        _core.forward_cost(1 << 40)
