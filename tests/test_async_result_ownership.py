"""An async result owns the output buffers it reads until it is collected, on every backend:
a later call that reuses the same record (same shapes, new inputs) collects it first
(_gpu_cache.InputUploads._claim; CUDA: _dispatch_result). Before, on Vulkan, the first
result read after a same-shaped call returned that call's peaks."""
import numpy as np
import pytest

from test_coarse_ragged_groups import _backend


def _context(backend):
    if backend == "vulkan":
        from matchedfilter import _vkcompute as V
        return V.Context(0)
    if backend == "metal":
        from matchedfilter import _mtlcompute as M
        return M.Context(0)
    if backend == "cuda":
        from matchedfilter import _cudacompute as C
        return C.Context(0)
    pytest.skip("backend %s" % backend)


@pytest.mark.parametrize("cascade", [False, True])
@pytest.mark.parametrize("after", ["reuse", "evict"])
def test_async_result_survives_reuse_and_eviction(cascade, after):
    ctx = _context(_backend())
    n, band, nd, nt = 2048, 256, 6, 5
    rng = np.random.default_rng(11)

    def inputs():
        d = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
        t = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
        d[:, :band] *= 4.0
        return d, t

    def call(d, t, **kw):
        if cascade:
            kw.update(cascade_band=128, ct1=np.ascontiguousarray(t[:, :band]), raw_thr1=0.0)
            ct0 = np.ascontiguousarray(t[:, :128])
        else:
            ct0 = np.ascontiguousarray(t[:, :band])
        return ctx.hier_peaks(n, band, d, t, ct0, 0.0, binsize=n, threshold=0.0, **kw)

    try:
        d1, t1 = inputs()
        d2, t2 = inputs()
        want = [np.array(a) for a in call(d1, t1)]
        pending = call(d1, t1, async_submit=True)
        if after == "reuse":
            call(d2, t2)                    # the same record, new inputs, before collection
        else:
            ctx._evict_all()
        got = pending() if callable(pending) else pending.result()
        for a, b in zip(got, want):
            np.testing.assert_array_equal(np.asarray(a), b)
    finally:
        if hasattr(ctx, "destroy"):
            ctx.destroy()
