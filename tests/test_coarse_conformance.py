"""Every coarse layout a device's choice may take, forced through the production path
(hier_peaks) on whichever GPU backend this machine has, must make the gate decisions the
exact coarse statistic makes, and fail open.

The layout -- packing, tile, twiddle source, subgroup size, and on CUDA the tensor-core
gate -- is a per-device measured choice (_coarse.stored_measured_choice), so any of them
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
