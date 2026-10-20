"""The Vulkan fp16 coarse tier reports an UPPER BOUND on each pair's exact coarse maximum.

B = |c16|(1+3u) + kappa_B u rms(y) (tierb.slang c16Bound; kappa from tools/coarse_layout.py).
The gate must never reject a pair whose exact maximum reaches the threshold, so B must sit
at or above the float64 maximum for every pair -- and the bound must not be wasteful: the
fp16 error may use at most half of its margin (margin use < 0.5, the criterion of
tools/gate_margin.py). Families and seed differ from the ones sigma_B was measured on.
"""
import numpy as np
import pytest

u = 2.0 ** -11


def _families(B, rng, nt):
    from matchedfilter.benchmark import _inspiral_power
    white = lambda *s: (rng.standard_normal(s) + 1j * rng.standard_normal(s))
    shape = np.sqrt(_inspiral_power(8 * B)[:B]); shape /= shape.max()
    T = white(nt, B) * shape
    out = [white(1, B), white(1, B) * shape]
    lag = int(rng.integers(0, B))
    out.append(white(1, B) * shape + 12.0 * T[0] * np.exp(-2j * np.pi * lag * np.arange(B) / B))
    burst = np.zeros(B, complex); t0 = int(rng.integers(0, B - 8))
    burst[t0:t0 + 8] = 200.0 * np.exp(1j * np.linspace(0, 6, 8))
    out.append(white(1, B) + np.fft.fft(burst)[None])
    return [(D, T) for D in out]


def _coarse(ctx, n, B, D, T):
    nt = T.shape[0]
    data = np.zeros((1, n), np.complex64); data[:, :B] = D
    tmpl = np.zeros((nt, n), np.complex64); tmpl[:, :B] = T
    # The tier places its operands for the threshold (_gpuhier.c16_data_exp): the pairs'
    # own scale (8, below), and its values come back divided by the scale it applied.
    ctx.hier_peaks(n, B, data, tmpl, np.ascontiguousarray(tmpl[:, :B]), 8.0,
                   binsize=n, threshold=0.0)
    key = next(reversed(ctx._cache_order))     # the record this call ran (touched last)
    cval = np.empty(nt, np.complex64)
    ctx._x_read(ctx._exec_records[key].buffers["cval0"], cval)
    return np.abs(cval.astype(np.complex128)) / ctx._last_c16_scale


@pytest.mark.parametrize("B", [64, 256, 1024, 2048])
def test_bound_covers_the_exact_maximum(B, monkeypatch):
    from conftest import vulkan_runs
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)
    from matchedfilter import _vkcompute
    n, nt = 4096, 128
    rng = np.random.default_rng(1234 + B)
    cases = _families(B, rng, nt)
    raws, bnds = [], []
    for flag, out in (("0", raws), ("1", bnds)):
        monkeypatch.setenv("MF_VK_C16_BOUND", flag)
        ctx = _vkcompute.Context(0)
        try:
            for D, T in cases:
                # Scale each template so every pair's exact maximum is 8 (well inside fp16).
                y = np.fft.ifft(D * np.conj(T), axis=1) * B
                T = (T * (8.0 / np.abs(y).max(axis=1))[:, None]).astype(np.complex64)
                out.append((_coarse(ctx, n, B, D.astype(np.complex64), T),
                            np.abs(np.fft.ifft(D.astype(np.complex128) * np.conj(T.astype(np.complex128)),
                                               axis=1) * B).max(axis=1)))
        finally:
            ctx.destroy()
    for (raw, exact), (bnd, _) in zip(raws, bnds):
        assert (bnd >= exact).all(), "bound below the exact maximum: %r" % ((bnd - exact).min(),)
        use = (exact - raw) / (bnd - raw)
        assert use.max() < 0.5, "margin use %.3f" % use.max()


def _layout_values(ctx, layout, B, D, T, thr=8.0):
    """|coarse value| per template of one data row from one coarse layout, dispatched as the
    layout choice times it (_gpuhier._time_coarse_layouts), electing each pair's maximum.
    The operands are placed as a call places them for raw threshold thr (templates at 2^et,
    data at 2^ed, _gpuhier.c16_template_exp/c16_data_exp) and the values returned unscaled:
    unplaced, a loud burst left fp16's range on an Intel Iris Xe (every layout 0.93 low)."""
    from matchedfilter import _gpuhier
    from matchedfilter._coarse import coarse_launch
    from matchedfilter._shared import pack_half2
    nt = T.shape[0]
    et = _gpuhier.c16_template_exp(T)
    ed = _gpuhier.c16_data_exp(B, thr, et)
    rows = (np.ascontiguousarray(D, np.complex64) if ctx.inplace_feed
            else pack_half2(_gpuhier.pow2_scaled(D, ed)))
    bufs = [ctx._x_alloc(rows.nbytes), ctx._x_alloc(nt * B * 4),
            ctx._x_alloc(nt * 4 + 4096), ctx._x_alloc(nt * 8 + 4096, readback=True)]
    native = None
    try:
        bufs[0].write(rows)
        bufs[1].write(pack_half2(_gpuhier.pow2_scaled(T, et)))
        kernel = ctx._coarse_kernel(B, layout, stride=B if ctx.inplace_feed else 0,
                                    scale=ed if ctx.inplace_feed else 0, rowwin=False)
        slot, groups = coarse_launch(1, nt, layout[1], layout[2], B)
        lst = ctx._x_list("c16 bound", once=True)
        lst.dispatch(kernel, ctx._x_coarse_groups(kernel, groups), bufs,
                     (nt, 0, B, slot, B.bit_length() - 1, 1, 0))
        lst.barrier()
        lst.readback(bufs[3], nt * 8)
        native = lst.end()
        ctx._x_run(native, True, {}, None)
        v = np.empty(nt, np.complex64)
        ctx._x_read(bufs[3], v)
    finally:
        if native is not None:
            ctx._x_release(native, done=True)
        for b in bufs:
            b.destroy()
    return np.abs(v.astype(np.complex128)) / 2.0 ** (et + ed)


@pytest.mark.parametrize("B", [64, 256, 1024, 2048])
def test_every_coarse_layout_bounds_the_exact_maximum(B, monkeypatch):
    """The bound holds, within half its margin, on every layout the measured choice may
    pick on this GPU (_x_coarse_candidates: subgroup, pairs per group, tiles, twiddle table;
    CUDA's tensor-core gate with its own kappa), not only the one it picked."""
    from conftest import gpu_backend, gpu_context
    backend = gpu_backend()
    nt = 128
    rng = np.random.default_rng(4321 + B)
    cases = []
    for D, T in _families(B, rng, nt):
        y = np.fft.ifft(D * np.conj(T), axis=1) * B
        T = (T * (8.0 / np.abs(y).max(axis=1))[:, None]).astype(np.complex64)
        D = D.astype(np.complex64)
        cases.append((D, T, np.abs(np.fft.ifft(D.astype(np.complex128)
                                               * np.conj(T.astype(np.complex128)),
                                               axis=1) * B).max(axis=1)))
    out = {}
    for flag in ("0", "1"):
        monkeypatch.setenv("MF_VK_C16_BOUND", flag)
        ctx = gpu_context(backend)
        try:
            if not ctx._x_has_c16(B):
                pytest.skip("band %d has no fp16 coarse tier" % B)
            for layout in ctx._x_coarse_candidates(B):
                out[flag, layout] = [_layout_values(ctx, layout, B, D, T) for D, T, _ in cases]
        finally:
            ctx.destroy()
    layouts = [k[1] for k in out if k[0] == "1"]
    assert layouts
    for layout in layouts:
        for raw, bnd, (_, _, exact) in zip(out["0", layout], out["1", layout], cases):
            tag = "band %d layout %r" % (B, layout)
            assert (bnd >= exact).all(), "%s: bound below the exact maximum by %r" % (
                tag, (bnd - exact).min())
            assert (bnd > raw).all(), "%s: the switch did not change the output" % tag
            use = (exact - raw) / (bnd - raw)
            assert use.max() < 0.5, "%s: margin use %.3f" % (tag, use.max())
