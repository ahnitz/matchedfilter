"""A filter owns the data it is given (docs/robustness-plan.md, B5).

Until 2026-10-22 the hierarchical plan kept the caller's pointer: the refine ingests the
full spectrum lazily, so a caller that reused its buffer after set_data -- the natural
thing in a loop over segments -- changed what the refine read (a loud peak at |v| ~ 8e4
read as no peak at all). The Python layer also kept the caller's array for replay into a
rebuilt plan. Both copy now, as the flat C plan always did."""
import numpy as np
import pytest

import matchedfilter as mf

N = 4096


def _problem(rng):
    t = np.zeros(N, np.complex64)
    t[:64] = rng.standard_normal(64)
    tmpl = np.conj(np.fft.fft(t)).astype(np.complex64)[None]
    data = np.fft.fft(np.roll(t, 161)).astype(np.complex64)[None].copy()
    return tmpl, data


def _filter(kind):
    if kind == "hier":
        f = mf.HierarchicalFilter(N, 1, 1, chain=[256])
        f.set_coarse_threshold(0.0)
        return f
    return mf.MatchedFilter(N, 1, 1)


@pytest.mark.parametrize("kind", ["flat", "hier"])
@pytest.mark.parametrize("batch", [True, False], ids=["batch", "one-row"])
def test_the_callers_buffer_may_be_reused_after_set_data(kind, batch):
    rng = np.random.default_rng(0)
    tmpl, data = _problem(rng)
    ref = _filter(kind)
    ref.set_templates(tmpl)
    ref.set_data(data.copy())
    want = ref.run(binsize=N, threshold=0.0).copy()
    assert want["index"].ravel()[0] >= 0 and np.abs(want["value"]).ravel()[0] > 1e3   # loud

    f = _filter(kind)
    f.set_templates(tmpl)
    buf = data.copy()
    if batch:
        f.set_data(buf)
    else:
        f.set_data(buf[0], index=0)
    buf[:] = np.fft.fft(rng.standard_normal(N)).astype(np.complex64)   # the next segment
    got = f.run(binsize=N, threshold=0.0)
    np.testing.assert_array_equal(got["index"], want["index"])
    np.testing.assert_array_equal(got["value"], want["value"])
