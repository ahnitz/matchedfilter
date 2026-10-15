"""Native plan lifetime and full-rate DIF grid regressions."""
import os
import subprocess
import sys
import textwrap

import numpy as np
import pytest

import matchedfilter as mf


def _noise(rng, shape):
    return (rng.normal(size=shape) + 1j * rng.normal(size=shape)).astype(np.complex64)


@pytest.mark.parametrize("initialized", [False, True])
def test_q15_plan_keeps_backend_after_target_change(initialized):
    # Isolate the regression: the old wider kernel overwrote heap allocations.
    script = textwrap.dedent(f"""
        import resource
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        import numpy as np
        import matchedfilter as mf
        from matchedfilter import _core
        targets = mf.targets()
        if len(targets) < 2:
            raise SystemExit(77)
        mf.set_target(targets[-1])
        rng = np.random.default_rng(123)
        noise = lambda shape: (rng.normal(size=shape) + 1j*rng.normal(size=shape)).astype(np.complex64)
        d, t = noise((2, 256)), noise((17, 256))
        def plan():
            p = _core.MF(256, 2, 17)
            p.set_data_batch(0, d); p.set_template_batch(0, t)
            return p
        def screen(p):
            passed = np.empty(34, np.uint8); stat = np.empty(34, np.float32)
            p.q15_screen(0, 2, 0, 17, 75., 3, 251, passed, stat)
            return passed, stat
        p, reference = plan(), plan()
        if not p.q15_lanes():
            raise SystemExit(77)
        lanes = p.q15_lanes()
        expected = screen(reference)
        if {initialized!r}:
            screen(p)
        mf.set_target(targets[0])
        assert p.q15_lanes() == lanes
        for actual, wanted in zip(screen(p), expected):
            np.testing.assert_array_equal(actual, wanted)
        mf.set_target(targets[-1])
        for actual, wanted in zip(screen(p), expected):
            np.testing.assert_array_equal(actual, wanted)
    """)
    env = os.environ.copy()
    env.pop("MF_ISA", None)  # This subprocess selects both targets explicitly.
    result = subprocess.run([sys.executable, "-c", script], env=env,
                            capture_output=True, text=True)
    if result.returncode == 77:
        pytest.skip("requires two SIMD targets with a Q15 screen")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("binsize", [1, 3, 7, 128, 257, 4096])
@pytest.mark.parametrize("window", [(0, 2048), (1, 2000), (17, 2050), (500, 501), (501, 502)])
def test_hierarchical_dif_preserves_full_rate_bins(binsize, window, monkeypatch):
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_GATE16", "0")
    n, nd, nt = 2048, 2, 3
    rng = np.random.default_rng(812)
    data = _noise(rng, (nd, n))
    templates = np.zeros((nt, n), np.complex64)
    templates[:, :n//2] = _noise(rng, (nt, n//2))
    full = mf.MatchedFilter(n, nd, nt)
    half = mf.HierarchicalFilter(n, nd, nt, chain=256)
    half.set_coarse_threshold(0.)
    full.set_templates(templates)
    half.set_templates(templates[:, :n//2].copy())
    for f in (full, half):
        f.set_data(data)
    want = full.run(binsize=binsize, window=window)
    got = half.run(binsize=binsize, window=window)
    np.testing.assert_array_equal(got['index'], want['index'])
    np.testing.assert_allclose(got['value'], want['value'], rtol=2e-5, atol=2e-4)


@pytest.mark.parametrize("binsize,window", [(1, (1, 511)), (3, (0, 512)), (7, (17, 500)),
                                           (128, (1, 500)), (257, (17, 550)), (512, (501, 502))])
@pytest.mark.parametrize("raw", [False, True])
def test_flat_dif_series_preserves_shape_and_template_subrange(binsize, window, raw):
    n, nt = 512, 20
    rng = np.random.default_rng(822)
    series = _noise(rng, 2*n)
    templates = np.zeros((nt, n), np.complex64)
    templates[:, :n//2] = _noise(rng, (nt, n//2))
    full, half = (mf.MatchedFilter(n, 2, nt) for _ in range(2))
    full.set_templates(templates)
    half.set_templates(templates[:, :n//2].copy())
    kw = dict(binsize=binsize, templates=(2, 17), raw=raw, threshold=0.5)
    args = (series, [0, n//3], [window[0]]*2, [window[1]]*2)
    want, got = full.run_series(*args, **kw), half.run_series(*args, **kw)
    wi, wv = want if raw else (want['index'], want['value'])
    gi, gv = got if raw else (got['index'], got['value'])
    np.testing.assert_array_equal(gi, wi)
    np.testing.assert_allclose(gv, wv, rtol=2e-5, atol=1e-4)


@pytest.mark.parametrize("binsize", [1, 7, 128, 1024])
def test_decimated_dif_bins_stay_in_input_sample_units(binsize):
    n, nt = 256, 3
    rng = np.random.default_rng(823)
    series, templates = _noise(rng, n), _noise(rng, (nt, n))
    f = mf.MatchedFilter(n, 2, nt)
    f.set_templates(templates)
    lo, hi = 3, 251
    got = f.run_series_dif(series, [0], [lo], [hi], binsize=binsize, decimated=True)
    product = np.fft.fft(series)/n * templates.conj()
    z = np.fft.ifft(np.pad(product, ((0, 0), (0, n))), axis=-1)*(2*n)
    edges = list(range(2*lo, 2*hi, 2*binsize))
    expected = np.array([[a + np.abs(row[a:min(a+2*binsize, 2*hi)]).argmax()
                          for a in edges] for row in z])
    np.testing.assert_array_equal(got['index'][0], expected)
    np.testing.assert_allclose(got['value'][0], np.take_along_axis(z, expected, axis=-1),
                               rtol=2e-5, atol=1e-4)


@pytest.mark.parametrize("binsize", [3, 4, 8])
def test_dif_ties_keep_the_earlier_full_rate_lag(binsize):
    n = 1024
    templates = np.zeros((1, n), np.complex64)
    templates[0, 0] = 1.
    f = mf.MatchedFilter(n, 2, 1)
    f.set_templates(templates)
    got = f.run_series_dif(np.ones(2*n, np.complex64), [0], [1], [9], binsize=binsize)
    np.testing.assert_array_equal(got['index'][0, 0], np.arange(1, 9, binsize))
    np.testing.assert_array_equal(got['value'], 1.)


@pytest.mark.parametrize("initial", [False, True])
@pytest.mark.parametrize("coarse_threshold", [0., 120.])
def test_hermitian_mode_changes_replay_native_templates(initial, coarse_threshold, monkeypatch):
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_GATE16", "0")
    n, nd, nt = 2048, 8, 3
    rng = np.random.default_rng(712)
    data, templates = _noise(rng, (nd, n)), _noise(rng, (nt, n//2))
    def create(mode):
        f = mf.HierarchicalFilter(n, nd, nt, chain=256)
        f.set_hermitian(mode)
        f.set_coarse_threshold(coarse_threshold)
        f.set_templates(templates)
        f.set_data(data)
        return f
    f = create(initial)
    f.run()
    for mode in (not initial, initial, not initial):
        f.set_hermitian(mode)
        want, got = create(mode).run(), f.run()
        np.testing.assert_array_equal(got['index'], want['index'])
        np.testing.assert_allclose(got['value'], want['value'], rtol=2e-5, atol=2e-4)
