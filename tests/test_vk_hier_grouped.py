"""Vulkan hier_peaks_grouped: one recording over every window group, per-row windows in
the kernels, must equal hier_peaks run on each group's rows separately."""
import numpy as np
import pytest

from matchedfilter import _vulkan

_devices, _reason = _vulkan.enumerate_devices()
novk = pytest.mark.skipif(not _devices, reason=_reason or "no Vulkan device")


@pytest.fixture(scope="module")
def ctx():
    from conftest import vulkan_runs
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)
    from matchedfilter import _vkcompute
    c = _vkcompute.Context(0)
    yield c
    c.destroy()


@novk
@pytest.mark.parametrize("cascade", [False, True])
@pytest.mark.parametrize("bs", [2048, 512])
@pytest.mark.parametrize("sparse", [False, True])
def test_grouped_equals_per_group(ctx, cascade, bs, sparse):
    n, nd, nt = 2048, 23, 9
    rng = np.random.default_rng(5)
    spec = ctx.empty_shared((nd, n))
    spec[:] = ((rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n)))
               / np.sqrt(2 * n)).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True) / np.sqrt(n)
    # Loud injections so the gates pass some pairs in every group, near each edge.
    for d, t, lag in ((0, 3, 300), (5, 1, 1900), (12, 7, 1000), (22, 0, 45), (21, 4, 2030)):
        spec[d] += 40 * h[t] * np.exp(-2j * np.pi * np.arange(n) * lag / n) / np.sqrt(n)
    # The first group's window sets the bin count; the others must not need more bins.
    groups = [(199, 1849, 0, 1), (40, 2040, 1, 22), (10, 1500, 22, 23)]
    gate, thr = 2.0, 3.0
    kw = dict(cascade_band=256, ct1=h[:, :1024], raw_thr1=gate) if cascade else {}
    band, ct0 = (1024, h[:, :256]) if cascade else (512, h[:, :512])
    got = ctx.hier_peaks_grouped(n, band, spec, h, ct0, gate, groups, bs, thr,
                                 sparse=sparse, **kw)
    if sparse:
        got = got.dense()
    nb = (groups[0][1] - groups[0][0] - 1) // bs + 1
    assert got[0].shape == (nd, nt, nb)
    hits = 0
    for lo, hi, a, b in groups:
        sub = ctx.empty_shared((b - a, n))
        sub[:] = spec[a:b]
        ri, rv = ctx.hier_peaks(n, band, sub, h, ct0, gate, binsize=bs, threshold=thr,
                                window=(lo, hi), **kw)
        k = ri.shape[2]
        np.testing.assert_array_equal(got[0][a:b, :, :k], ri)
        np.testing.assert_array_equal(got[1][a:b, :, :k], rv)
        assert (got[0][a:b, :, k:] == -1).all()
        hits += int((ri >= 0).sum())
    assert hits >= 5
