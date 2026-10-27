"""Every coarse layout a device's choice may take, forced through the production path
(hier_peaks) on whichever GPU backend this machine has, must make the gate decisions the
exact coarse statistic makes, and fail open.

The layout -- packing, tile, twiddle source, subgroup size, and on CUDA the tensor-core
gate -- is a per-device measured choice (_coarse.shortlist, then the device trial), so any of them
can run in production. Each backend lists them by one name (coarse_layouts,
_coarse.layout_label) and MF_COARSE_LAYOUT forces one, so one test covers all three
backends and a rule cannot drift on one of them again. This replaces the per-backend tile,
packing and transient tests.

Gate thresholds sit at the midpoints of wide gaps in the pairs' exact float64 maxima, so
the fp16 tier's rounding cannot decide them: each layout must refine exactly the pairs
whose maximum is above the threshold, and report what the untiled one-pair layout does.
"""
import numpy as np
import pytest

from conftest import gpu_backend as _backend, gpu_context as _context

BANDS = [64, 128, 256, 512, 1024, 2048]


def _layouts(backend, band):
    ctx = _context(backend)
    try:
        names = ctx.coarse_layouts(band)
    finally:
        ctx.destroy()
    if not names:
        pytest.skip("no fp16 coarse tier at band %d on %s" % (band, backend))
    return names


def _reference(band, names):
    """The untiled one-pair layout (with the twiddle recurrence where there is a choice)."""
    from matchedfilter._coarse import coarse_stem
    stem = coarse_stem(band, 1, 1)
    for want in (stem, stem + "w"):
        hit = [s for s in names if s.split("@")[0] == want]
        if hit:
            return hit[0]
    return names[0]


def _exact(D, T):
    """Each pair's exact coarse maximum, as the gate compares it."""
    band = D.shape[1]
    return np.abs(np.fft.ifft(D[:, None, :] * np.conj(T)[None], axis=2) * band).max(axis=2)


def _gap_thresholds(exact, count=3, ratio=1.08):
    """Thresholds at the geometric midpoints of the widest gaps between the sorted maxima,
    each gap at least `ratio` wide: no fp16 rounding can move a pair across one."""
    v = np.unique(exact.ravel())
    gaps = sorted(((v[i + 1] / v[i], np.sqrt(v[i] * v[i + 1])) for i in range(len(v) - 1)
                   if v[i] > 0 and v[i + 1] / v[i] >= ratio), reverse=True)
    return sorted(t for _, t in gaps[:count])


def _run(backend, name, n, band, data, tmpl, thr):
    import os
    os.environ["MF_COARSE_LAYOUT"] = name
    ctx = _context(backend)                 # plans are cached per context, not per layout
    try:
        ct0 = np.ascontiguousarray(tmpl[:, :band])
        idx, val = ctx.hier_peaks(n, band, data, tmpl, ct0, thr, binsize=n, threshold=0.0)
        return np.asarray(idx).copy(), np.asarray(val).copy()
    finally:
        ctx.destroy()


@pytest.mark.parametrize("band", BANDS)
def test_every_layout_makes_the_exact_gate_decisions(band, monkeypatch):
    """A ragged pair count (3 x 7), a planted signal, a row that overflows fp16 (it must
    pass every gate: fail open), and thresholds in wide gaps of the exact maxima."""
    backend = _backend()
    monkeypatch.setenv("MF_COARSE_LAYOUT", "")
    names = _layouts(backend, band)
    n, nd, nt = 4096, 3, 7
    rng = np.random.default_rng(band)
    data = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    tmpl = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    tmpl /= np.linalg.norm(tmpl[:, :band], axis=1, keepdims=True)
    data[0, :band] += 30.0 * tmpl[nt - 1, :band]
    data[2, :band] *= 1e5                   # overflows the fp16 transform
    exact = _exact(data[:, :band].astype(complex), tmpl[:, :band].astype(complex))
    thresholds = [0.0] + _gap_thresholds(exact[:2])
    assert len(thresholds) >= 3, "no wide gaps in the maxima"
    ref = _reference(band, names)
    for thr in thresholds:
        want = exact > thr
        want[2] = True                      # the loud row: above every threshold, and must pass
        expect = _run(backend, ref, n, band, data, tmpl, thr)
        for name in names:
            idx, val = expect if name == ref else _run(backend, name, n, band, data, tmpl, thr)
            where = "%s %s threshold %.4g" % (backend, name, thr)
            passed = (idx >= 0).any(axis=2)
            np.testing.assert_array_equal(passed, want, err_msg="%s: gate decisions" % where)
            np.testing.assert_array_equal(idx, expect[0], err_msg=where)
            np.testing.assert_array_equal(val, expect[1], err_msg=where)


@pytest.mark.parametrize("K", [1.0, 32.0])
@pytest.mark.parametrize("band", [128, 256, 512, 1024])
def test_every_layout_passes_a_transient(band, K, monkeypatch):
    """gate_margin's transient family: a loud broadband burst in the data, templates scaled
    so every pair's exact maximum is K, and a gate at 0.999 K, which must pass every pair.

    K = 1 is gate_margin's scale: templates of ~5e-5, subnormal in fp16. A device that
    flushes fp16 subnormals (the Iris Xe) dismissed every pair there until the tier placed
    its operands by powers of two (_vkcompute._c16_scales); K = 32 sits in range either way."""
    backend = _backend()
    monkeypatch.setenv("MF_COARSE_LAYOUT", "")
    names = _layouts(backend, band)
    n, nt = 4096, 16
    rng = np.random.default_rng(band + 7)
    burst = np.zeros(band, complex)
    t0 = int(rng.integers(0, band - 8))
    burst[t0:t0 + 8] = 200.0 * np.exp(1j * np.linspace(0, 6, 8))
    D = (rng.standard_normal(band) + 1j * rng.standard_normal(band)) + np.fft.fft(burst)
    T = rng.standard_normal((nt, band)) + 1j * rng.standard_normal((nt, band))
    T = T / _exact(D[None], T)[0][:, None] * K
    data = (np.random.default_rng(0).standard_normal((1, n)) * 1e-3).astype(np.complex64)
    data[0, :band] = D
    tmpl = np.zeros((nt, n), np.complex64)
    tmpl[:, :band] = T
    for name in names:
        idx, _ = _run(backend, name, n, band, data, tmpl, 0.999 * K)
        lost = int((idx.reshape(nt) < 0).sum())
        assert not lost, "%s %s: gate dismissed %d of %d pairs" % (backend, name, lost, nt)


def _grouped_case(ctx, band, cascade, sparse):
    """(grouped result, [(rows, per-group result)]): hier_peaks_grouped over three window
    groups against hier_peaks run on each group's rows, with loud injections near the
    windows' edges. Each tier's gate sits between the noise-only pairs' exact maxima and the
    injected pairs', so a tier that searched the wrong window would dismiss an injection
    (two lie outside the first group's window, which a tier ignoring the per-row windows
    would search)."""
    n, nd, nt, bs = 2048, 23, 9, 512
    rng = np.random.default_rng(band + cascade)
    spec = ctx.empty_shared((nd, n))
    spec[:] = ((rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n)))
               / np.sqrt(2 * n)).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True) / np.sqrt(n)
    inj = ((0, 3, 300), (5, 1, 1900), (12, 7, 1000), (22, 0, 45), (21, 4, 2030))
    for d, t, lag in inj:
        spec[d] += 40 * h[t] * np.exp(-2j * np.pi * np.arange(n) * lag / n) / np.sqrt(n)
    # The first group's window sets the bin count; the others must not need more.
    groups = [(199, 1849, 0, 1), (40, 2040, 1, 22), (10, 1500, 22, 23)]

    def gate_for(b):
        ex = _exact(np.asarray(spec)[:, :b].astype(complex), h[:, :b].astype(complex))
        noise = np.ones(ex.shape, bool)
        for d, t, _ in inj:
            noise[d, t] = False
        lo_, hi_ = ex[noise].max(), min(ex[d, t] for d, t, _ in inj)
        assert hi_ > 1.5 * lo_, "no gap between noise and injections at band %d" % b
        return float(np.sqrt(lo_ * hi_))
    gate, thr = gate_for(band), 3.0
    kw = dict(cascade_band=band, ct1=h[:, :1024], raw_thr1=gate_for(1024)) if cascade else {}
    top, ct0 = (1024, h[:, :band]) if cascade else (band, h[:, :band])
    got = ctx.hier_peaks_grouped(n, top, spec, h, ct0, gate, groups, bs, thr, sparse=sparse, **kw)
    got = got.dense() if sparse else got
    parts = []
    for lo, hi, a, b in groups:
        sub = ctx.empty_shared((b - a, n))
        sub[:] = spec[a:b]
        parts.append(((a, b), ctx.hier_peaks(n, top, sub, h, ct0, gate, binsize=bs, threshold=thr,
                                             window=(lo, hi), **kw)))
    return got, parts


@pytest.mark.parametrize("band,cascade", [(128, False), (512, False), (256, True)])
@pytest.mark.parametrize("sparse", [False, True])
def test_every_layout_runs_grouped_as_per_group(band, cascade, sparse, monkeypatch):
    """One grouped call (every tier one dispatch over all rows, each row in its own window:
    per-row windows in the kernels) equals hier_peaks on each group's rows, in every coarse
    layout -- the untiled builds once ignored per-row windows, which no other test saw."""
    backend = _backend()
    monkeypatch.setenv("MF_COARSE_LAYOUT", "")
    probe = _context(backend)
    try:
        if not hasattr(probe, "hier_peaks_grouped"):
            pytest.skip("%s has no grouped hierarchical call" % backend)
    finally:
        probe.destroy()
    names = _layouts(backend, band)
    hits = None
    for name in names:
        import os
        os.environ["MF_COARSE_LAYOUT"] = name
        ctx = _context(backend)
        try:
            got, parts = _grouped_case(ctx, band, cascade, sparse)
        finally:
            ctx.destroy()
        count = 0
        for (a, b), (ri, rv) in parts:
            k = ri.shape[2]
            where = "%s %s rows %d-%d" % (backend, name, a, b)
            np.testing.assert_array_equal(got[0][a:b, :, :k], ri, err_msg=where)
            np.testing.assert_array_equal(got[1][a:b, :, :k], rv, err_msg=where)
            assert (got[0][a:b, :, k:] == -1).all(), where
            count += int((ri >= 0).sum())
        assert count >= 5, "%s %s: the gates passed too little to compare" % (backend, name)
        hits = count if hits is None else hits
        assert count == hits, "%s %s: %d peaks against %d" % (backend, name, count, hits)
