"""Adaptive CPU execution must preserve results through fallback and updates."""
import numpy as np
import pytest
import matchedfilter as mf


@pytest.mark.parametrize("n", [256, 512, 1024])
def test_adaptive_pairbatch_and_fallbacks(n, monkeypatch):
    rng = np.random.default_rng(n)
    def noise(shape):
        return (rng.normal(size=shape)+1j*rng.normal(size=shape)).astype(np.complex64)
    data, templates = noise((16,n)), noise((64,n))
    monkeypatch.setenv("MF_PBMAX", "128")
    reference = mf.MatchedFilter(n,16,64)
    monkeypatch.delenv("MF_PBMAX")
    adaptive = mf.MatchedFilter(n,16,64)
    for f in (reference,adaptive):
        f.set_data(data); f.set_templates(templates)
    for update in range(2):
        if update:
            for f in (reference,adaptive):
                f.set_data(data[10]*2j,index=10)
                f.set_templates(templates[31]*(1+1j),index=31)
        for t0,nt in ((16,16),(0,64),(0,16),(0,17),(0,24),(1,32),(16,32),(0,1)):
            for lo,hi,bs in ((0,n,n),(n//4,3*n//4,n),(100,101,n),(0,n,17)):
                kw=dict(data=(8,8),templates=(t0,nt),window=(lo,hi),binsize=bs,threshold=2*np.sqrt(n),counts=True)
                want,wc=reference.run(**kw)
                got,gc=adaptive.run(**kw)
                np.testing.assert_array_equal(got["index"],want["index"])
                np.testing.assert_allclose(got["value"],want["value"],rtol=2e-5,atol=1e-4)
                np.testing.assert_array_equal(gc,wc)


@pytest.mark.parametrize("band", [256,512,1024])
def test_hierarchical_pairbatch_matches_balanced(band,monkeypatch):
    n,nt=4096,37
    rng=np.random.default_rng(914)
    h=(rng.normal(size=(nt,n))+1j*rng.normal(size=(nt,n))).astype(np.complex64)
    series=(rng.normal(size=4*n)+1j*rng.normal(size=4*n)).astype(np.complex64)
    outputs=[]
    for cutoff in ("128",None):
        if cutoff is None: monkeypatch.delenv("MF_PBMAX")
        else: monkeypatch.setenv("MF_PBMAX",cutoff)
        f=mf.HierarchicalFilter(n,1,nt,band=band,snr=5.5,fd=1e-2)
        f.set_reference(np.ones(n,np.float32)); f.set_coarse_threshold(0.)
        f.set_templates(h)
        outputs.append(f.run_series(series,[0,n,2*n,3*n],[0,300,0,300],[n]*4,
                                     binsize=n).copy())
    assert (outputs[0]["index"]>=0).all()
    np.testing.assert_array_equal(outputs[0]["index"],outputs[1]["index"])
    np.testing.assert_allclose(outputs[0]["value"],outputs[1]["value"],rtol=2e-5,atol=1e-4)


@pytest.mark.parametrize("n", [64, 128, 256, 512, 1024])
def test_pairbatch_scalar_data_and_partial_template_groups(n, monkeypatch):
    """Distinct rows and lane tails must not contaminate broadcast data loads."""
    monkeypatch.setenv("MF_PBMAX", "1024")
    rng = np.random.default_rng(20260926 + n)
    def noise(shape):
        return (rng.normal(size=shape) + 1j*rng.normal(size=shape)).astype(np.complex64)
    data, templates = noise((3, n)), noise((37, n))
    data *= np.array([0.01j, 1, -10j], np.complex64)[:, None]
    f = mf.MatchedFilter(n, 3, 37)
    f.set_templates(templates)
    for update in range(2):
        if update:
            data[1] = noise((n,))
        f.set_data(data)
        for start, count in ((0, 37), (1, 19), (16, 1)):
            lo, hi = 3, n-5
            got = f.run(templates=(start, count), window=(lo, hi), binsize=n)
            want = np.fft.ifft(data[:, None, :].astype(np.complex128)
                               * templates[None, start:start+count, :].conj(), axis=-1)*n
            idx = np.abs(want[..., lo:hi]).argmax(axis=-1) + lo
            val = np.take_along_axis(want, idx[..., None], axis=-1)
            np.testing.assert_array_equal(got["index"], idx[..., None])
            np.testing.assert_allclose(got["value"], val, rtol=2e-5, atol=1e-5)


def test_adaptive_threshold_changes_keep_both_layouts_current(monkeypatch):
    """A threshold/batch change can switch layouts after either input is updated."""
    n = 1024
    rng = np.random.default_rng(169)
    def noise(shape):
        return (rng.normal(size=shape) + 1j*rng.normal(size=shape)).astype(np.complex64)
    data, templates = noise((8, n)), noise((128, n))
    monkeypatch.setenv("MF_PBMAX", "128")
    reference = mf.MatchedFilter(n, 8, 128)
    monkeypatch.delenv("MF_PBMAX")
    adaptive = mf.MatchedFilter(n, 8, 128)
    for f in (reference, adaptive):
        f.set_data(data)
        f.set_templates(templates)
    for update in range(2):
        if update:
            for f in (reference, adaptive):
                f.set_data(data[3] * 2j, index=3)
                f.set_templates(templates[31] * (1 + 1j), index=31)
        for threshold in (0., 100., 1e6, 0.):
            for start, count in ((0, 64), (0, 128), (16, 37), (1, 32)):
                kw = dict(templates=(start, count), window=(100, 924),
                          binsize=n, threshold=threshold, counts=True)
                want, wc = reference.run(**kw)
                got, gc = adaptive.run(**kw)
                np.testing.assert_array_equal(got['index'], want['index'])
                np.testing.assert_allclose(got['value'], want['value'], rtol=2e-5, atol=1e-4)
                np.testing.assert_array_equal(gc, wc)


@pytest.mark.parametrize('nt', [32, 37, 64])
def test_series_grouping_preserves_ragged_blocks_and_refinement(nt, monkeypatch):
    n = 4096
    rng = np.random.default_rng(169 + nt)
    def noise(shape):
        return (rng.normal(size=shape) + 1j*rng.normal(size=shape)).astype(np.complex64)
    series, templates = noise((7*n,)), noise((nt, n))
    starts = np.arange(13) * (n//2)
    lo = np.zeros(13, dtype=int)
    hi = np.full(13, n, dtype=int)
    lo[0], hi[-1] = 123, n-321
    plans = []
    for group in ('8', '4', None):
        if group is None:
            monkeypatch.delenv('MF_DGROUP')
        else:
            monkeypatch.setenv('MF_DGROUP', group)
        f = mf.HierarchicalFilter(n, 1, nt, band=1024, snr=5.5, fd=.001)
        f.set_templates(templates)
        f.set_coarse_threshold(0.)
        # Realize lazy native plans while the explicit grouping is in scope.
        f.run_series(series, starts, lo, hi, binsize=n)
        plans.append(f)
    for threshold in (0., .5, 1e6, 0.):
        results = []
        for f in plans:
            f.set_coarse_threshold(threshold)
            results.append(f.run_series(series, starts, lo, hi, binsize=n).copy())
        for got in results[1:]:
            np.testing.assert_array_equal(got['index'], results[0]['index'])
            np.testing.assert_allclose(got['value'], results[0]['value'], rtol=2e-5, atol=1e-4)


@pytest.mark.parametrize('window', [(576, 918), (105, 918), (576, 1024), (0, 918)])
@pytest.mark.parametrize('thr', [0.0, 4.61751, 8.0])
def test_haswell_coarse_windows(window, thr):
    """PyCBC real Haswell workloads use partial coarse windows like (576, 918).

    Verifies that the vectorised fused 32×32 binmax agrees with a numpy
    fp64 reference on the *maximum magnitude* within the given window.
    Index tie-breaks may differ between fp32 and fp64, so we only check
    the magnitude at the chosen index matches the true maximum.
    """
    n, nd, nt = 1024, 8, 64
    rng = np.random.default_rng(576918)
    def noise(shape):
        return (rng.normal(size=shape) + 1j*rng.normal(size=shape)).astype(np.complex64)
    data, templates = noise((nd, n)), noise((nt, n))

    f = mf.MatchedFilter(n, nd, nt)
    f.set_data(data)
    f.set_templates(templates)

    got = f.run(binsize=n, window=window, threshold=thr)

    # Reference computation using direct IFFT at fp64
    lo, hi = window
    ref_full = np.fft.ifft(data[:, None, :].astype(np.complex128)
                           * templates[None, :, :].conj().astype(np.complex128),
                           axis=-1) * n
    ref_sub = ref_full[:, :, lo:hi]  # (nd, nt, hi-lo)
    ref_m2 = (ref_sub.real**2 + ref_sub.imag**2).astype(np.float32)
    ref_max_m2 = ref_m2.max(axis=2)  # (nd, nt)

    for d in range(nd):
        for t in range(nt):
            idx = int(got['index'][d, t, 0])
            val = got['value'][d, t, 0]
            if thr > 0 and np.sqrt(ref_max_m2[d, t]) < thr:
                # Below threshold: kernel should report -1
                assert idx == -1, f"d={d} t={t}: expected -1, got {idx}"
            else:
                # Kernel should pick a lag within the window
                assert lo <= idx < hi, f"d={d} t={t}: idx {idx} outside [{lo},{hi})"
                # The magnitude at the chosen index should match the reference max
                got_m2 = val.real**2 + val.imag**2
                np.testing.assert_allclose(got_m2, ref_max_m2[d, t],
                                           rtol=5e-5, atol=1e-6)


@pytest.mark.parametrize("n", [256, 512, 1024])
def test_pairbatch_nd4_matches_balanced(n, monkeypatch):
    """When nd=4 (typical for Haswell series_group=4), pairbatch must match balanced."""
    nd, nt = 4, 32
    rng = np.random.default_rng(42 + n)
    def noise(shape):
        return (rng.normal(size=shape) + 1j*rng.normal(size=shape)).astype(np.complex64)
    data, templates = noise((nd, n)), noise((nt, n))

    monkeypatch.setenv("MF_PBMAX", "128")
    ref = mf.MatchedFilter(n, nd, nt)
    ref.set_data(data)
    ref.set_templates(templates)
    want, wc = ref.run(binsize=n, threshold=2.0 * np.sqrt(n), counts=True)

    monkeypatch.delenv("MF_PBMAX")
    got_mf = mf.MatchedFilter(n, nd, nt)
    got_mf.set_data(data)
    got_mf.set_templates(templates)
    got, gc = got_mf.run(binsize=n, threshold=2.0 * np.sqrt(n), counts=True)

    np.testing.assert_array_equal(got["index"], want["index"])
    np.testing.assert_allclose(got["value"], want["value"], rtol=2e-5, atol=1e-4)
    np.testing.assert_array_equal(gc, wc)


