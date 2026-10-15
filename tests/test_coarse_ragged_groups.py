"""One coarse launch rule on every GPU backend (_coarse.coarse_launch): an untiled build with
several pairs per group takes ragged groups, its spare slots computing the last pair and
writing nothing. Each packing, forced on this machine's backend, must elect exactly what one
pair per group elects at a pair count no packing divides."""
import numpy as np
import pytest


def _backend():
    from conftest import usable_gpu
    import matchedfilter as mf
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    return next(d for d in mf.devices() if str(d) == dev).backend


def _drop_cuda_choice(ctx, band):
    pipes = getattr(ctx, "_pipelines", None)
    if isinstance(pipes, dict):
        pipes.pop(("coarse_choice", band, True), None)


def _forced_context(backend, band, ppg, monkeypatch):
    """A fresh context whose band-`band` coarse layout is untiled at `ppg` pairs per group."""
    if backend == "vulkan":
        from matchedfilter import _vkcompute as V
        monkeypatch.setenv("MF_VK_COARSE_PPG", str(ppg))
        monkeypatch.setenv("MF_VK_COARSE_TILE", "1")
        ctx = V.Context(0)
        if ctx._coarse_geometry(band, 7, 5)[1] != ppg:
            ctx.destroy()
            return None
        return ctx
    if backend == "metal":
        from matchedfilter import _mtlcompute as M
        monkeypatch.setenv("MF_METAL_COARSE_PPG", str(ppg))
        monkeypatch.setenv("MF_METAL_COARSE_TILE", "1")
        return M.Context(0)
    if backend == "cuda":
        from matchedfilter import _cudacompute as C
        orig = C.Context._time_coarse

        def pick(self, b, cands):
            mine = [c for c in cands if c[2] == ppg and c[3] == 1 and c[1] == b // 16 * ppg]
            return mine[0] if mine else orig(self, b, cands)
        monkeypatch.setattr(C.Context, "_time_coarse", pick)
        ctx = C.Context(0)
        # The chosen kernel is cached per DEVICE (shared by every context): drop it so this
        # forced choice is made, and drop the forced one after (_drop_cuda_choice).
        ctx._pipelines.pop(("coarse_choice", band, True), None)
        if ctx._coarse_kernel(band, 5)[2] != ppg:
            _drop_cuda_choice(ctx, band)
            return None
        return ctx
    pytest.skip("backend %s" % backend)


@pytest.mark.parametrize("band", [128, 256, 512])
def test_packed_untiled_builds_elect_what_one_pair_per_group_does(band, monkeypatch):
    backend = _backend()
    n, nd, nt = 2048, 7, 5                          # 35 pairs: no packing divides them
    rng = np.random.default_rng(band)
    data = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    tmpl = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    data[:, :band] *= 4.0                           # the coarse band carries the signal
    ct0 = np.ascontiguousarray(tmpl[:, :band])

    def run(ppg):
        ctx = _forced_context(backend, band, ppg, monkeypatch)
        if ctx is None:
            return None
        try:
            idx, val = ctx.hier_peaks(n, band, data, tmpl, ct0, 0.0, binsize=n, threshold=0.0)
            return np.asarray(idx).copy(), np.asarray(val).copy()
        finally:
            if backend == "cuda":
                _drop_cuda_choice(ctx, band)
            if hasattr(ctx, "destroy"):
                ctx.destroy()

    ref = run(1)
    assert ref is not None and (ref[0] >= 0).all()
    ran = 0
    for ppg in (2, 4, 8, 16):
        got = run(ppg)
        if got is None:                             # not shipped, or past the device's limits
            continue
        ran += 1
        np.testing.assert_array_equal(got[0], ref[0], err_msg="%s band %d ppg %d" % (backend, band, ppg))
        np.testing.assert_allclose(got[1], ref[1], rtol=1e-6, atol=0,
                                   err_msg="%s band %d ppg %d" % (backend, band, ppg))
    if not ran:
        pytest.skip("no packed untiled build at band %d on %s" % (band, backend))
