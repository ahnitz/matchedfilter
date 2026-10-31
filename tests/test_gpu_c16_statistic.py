"""The GPU fp16 coarse tier reports its own statistic: each pair's fp16 maximum, which tracks
its exact coarse maximum to fp16 precision, on every layout the coarse choice may pick.

What its rounding does to the search is accepted by the chain's false dismissal against the
flat filter (tools/fdr_audit.py --device), not here. These check for gross errors -- a wrong
lag, a wrong scale, an overflow -- with a limit of 2^-6 relative: the worst residual the
arithmetic showed was 4.9 u rms(y) (u = 2^-11; band 2048, a loud transient), below 2^-8.
Families: white noise, profile-shaped templates, an injection and a loud broadband burst.
"""
import numpy as np
import pytest

#: The relative limit of a gross error (see the module docstring).
GROSS = 2.0 ** -6


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
    # The tier places its operands for the threshold (_gpuhier.c16_data_exp) and passes a
    # pair whose value reaches it: half the pairs' own scale (8, below), so every pair passes
    # and reports its value, which comes back divided by the scale the tier applied.
    ctx.hier_peaks(n, B, data, tmpl, np.ascontiguousarray(tmpl[:, :B]), 4.0,
                   binsize=n, threshold=0.0)
    key = next(reversed(ctx._cache_order))     # the record this call ran (touched last)
    cval = np.empty(nt, np.complex64)
    ctx._x_read(ctx._exec_records[key].buffers["cval0"], cval)
    return np.abs(cval.astype(np.complex128)) / ctx._last_c16_scale


@pytest.mark.parametrize("B", [64, 256, 1024, 2048])
def test_the_tier_reports_its_own_statistic(B):
    from conftest import vulkan_runs
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)
    from matchedfilter import _vkcompute
    n, nt = 4096, 128
    rng = np.random.default_rng(1234 + B)
    ctx = _vkcompute.Context(0)
    try:
        for D, T in _families(B, rng, nt):
            # Scale each template so every pair's exact maximum is 8 (well inside fp16).
            y = np.fft.ifft(D * np.conj(T), axis=1) * B
            T = (T * (8.0 / np.abs(y).max(axis=1))[:, None]).astype(np.complex64)
            got = _coarse(ctx, n, B, D.astype(np.complex64), T)
            exact = np.abs(np.fft.ifft(D.astype(np.complex128) * np.conj(T.astype(np.complex128)),
                                       axis=1) * B).max(axis=1)
            err = np.abs(got / exact - 1.0)
            assert err.max() < GROSS, "band %d: relative error %.2e" % (B, err.max())
    finally:
        ctx.destroy()


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
        lst = ctx._x_list("c16 statistic", once=True)
        lst.dispatch(kernel, groups, bufs,
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
def test_every_coarse_layout_reports_the_statistic(B):
    """Every layout the measured choice may pick on this GPU (_x_coarse_candidates: subgroup,
    pairs per group, tiles, twiddle table) reports each pair's maximum to fp16 precision, not
    only the one it picked."""
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
    ctx = gpu_context(backend)
    try:
        if not ctx._x_has_c16(B):
            pytest.skip("band %d has no fp16 coarse tier" % B)
        layouts = ctx._x_coarse_candidates(B)
        assert layouts
        for layout in layouts:
            for D, T, exact in cases:
                err = np.abs(_layout_values(ctx, layout, B, D, T) / exact - 1.0)
                assert err.max() < GROSS, "band %d layout %r: relative error %.2e" % (
                    B, layout, err.max())
    finally:
        ctx.destroy()


@pytest.mark.parametrize("B", [64, 1024])
def test_every_coarse_layout_fails_open_on_fp16_overflow(B):
    """A loud transient that overflows fp16 (producing Inf/NaN in butterfly intermediates)
    must fail open to a finite sentinel above any threshold on every c16 layout, never
    silently suppressing the pair via NaN > best == false."""
    from conftest import gpu_backend, gpu_context
    backend = gpu_backend()
    nt = 16
    rng = np.random.default_rng(9876 + B)
    T = (rng.standard_normal((nt, B)) + 1j * rng.standard_normal((nt, B))).astype(np.complex64)
    # 1e12 overflows half16 even after threshold-anchored pow2 scaling, creating Inf - Inf = NaN.
    D = np.full((1, B), 1e12 + 1e12j, dtype=np.complex64)
    ctx = gpu_context(backend)
    try:
        if not ctx._x_has_c16(B):
            pytest.skip("band %d has no fp16 coarse tier" % B)
        for layout in ctx._x_coarse_candidates(B):
            vals = _layout_values(ctx, layout, B, D, T, thr=8.0)
            assert np.all(np.isfinite(vals) & (vals >= 1e20)), (
                "band %d layout %r failed to fail-open on fp16 overflow: %r" % (B, layout, vals))
    finally:
        ctx.destroy()
