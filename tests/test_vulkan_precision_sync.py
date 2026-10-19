"""Intel exposed approximate twiddles and a stale indirect dispatch count."""
import numpy as np
import pytest
import matchedfilter as mf
from conftest import vulkan_runs


def spectra(shape, rng):
    return (rng.normal(size=shape)+1j*rng.normal(size=shape)).astype(np.complex64)


@pytest.mark.parametrize('n', [1024, 2048, 4096, 8192])
def test_accurate_twiddles_match_every_lag_on_any_vulkan_device(n):
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)
    rng = np.random.default_rng(741+n)
    d, h = spectra((2,n), rng), spectra((3,n), rng)
    f = mf.CorrelationFilter(n,2,3,device='gpu:0')
    try:
        # Exercise the Intel specialization in software-Vulkan CI too.
        f._gpu._accurate_trig = True
        f.set_data(d); f.set_templates(h)
        want = np.fft.ifft(d[:,None].astype(np.complex128) *
                           h[None].astype(np.complex128).conj(), axis=-1)*n
        got = f.run()
        assert np.max(np.abs(got-want))/np.max(np.abs(want)) < 1e-5
    finally:
        f._gpu.destroy()


@pytest.mark.parametrize('binsize', [1, 127, 2048])
def test_first_dispatch_and_changing_survivor_counts(binsize):
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)
    n = 2048
    rng = np.random.default_rng(641)
    d, h = spectra((2,n), rng), spectra((3,n), rng)
    flat = mf.MatchedFilter(n,2,3,device='cpu')
    hier = mf.HierarchicalFilter(n, 2, 3, chain=256, device='gpu:0')
    try:
        for f in (flat,hier):
            f.set_data(d); f.set_templates(h)
        want = flat.run(binsize=binsize).copy()
        # First use, then zero -> all -> zero -> all survivors on reused
        # storage. Stats alone can be right while indirect execution is stale.
        total, refined = 0, 0
        for coarse in (0., 1e10, 0., 1e10, 0.):
            hier.set_coarse_threshold(coarse)
            got = hier.run(binsize=binsize)
            total += 6
            refined += 0 if coarse else 6
            assert hier.stats == (total, refined)
            if coarse:
                assert (got['index'] == -1).all()
                assert (got['value'] == 0).all()
            else:
                np.testing.assert_array_equal(got['index'], want['index'])
                scale = np.max(np.abs(want['value']))
                assert np.max(np.abs(got['value']-want['value']))/scale < 1e-5
    finally:
        hier._gpu.destroy()


def test_accurate_trig_is_measured_not_keyed_on_the_vendor(monkeypatch):
    """Whether a device needs accurate twiddles is a forward transform's error with its
    native trig (Context._probe_trig): an Iris Xe measured 9.4e-5, a Radeon 1.2e-6. The
    probe's native pipelines are dropped when the answer is accurate."""
    from conftest import vulkan_runs
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)
    from matchedfilter import _vkcompute as V
    monkeypatch.delenv("MF_COST_FILE", raising=False)
    c = V.Context(0)
    try:
        assert c._device_state.trig_probed
        assert getattr(c, "_trig_probe_error", None) is None   # measured, not given up
        monkeypatch.setattr(V.Context, "_TRIG_TOLERANCE", 0.0)
        before = set(c._pipelines)
        assert c._probe_trig() is True               # no transform is exact
        assert set(c._pipelines) <= before | set()   # what the probe built is gone
        monkeypatch.setattr(V.Context, "_TRIG_TOLERANCE", 1.0)
        assert c._probe_trig() is False
    finally:
        c.destroy()
