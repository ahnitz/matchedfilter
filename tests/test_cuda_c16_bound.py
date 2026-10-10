"""The CUDA fp16 coarse tier reports the same UPPER BOUND as Vulkan's (tierb.slang c16Bound).

B = |c16|(1+3u) + kappa_B u rms(y) must sit at or above every pair's float64 maximum, and
the fp16 error may use at most half of the margin (tools/gate_margin.py's criterion). The
bound is switched off through the coarse module's mf_c16_raw constant, which the host sets
from MF_VK_C16_BOUND=0 (_cudacompute._c16_bound_flag). The families are those of
tests/test_gpu_c16_bound.py (the Vulkan test); the coarse kernel is launched directly, on
every variant the measured choice may pick, so ragged tiles and wave election are covered.
"""
import numpy as np
import pytest

from matchedfilter import _cuda

pytestmark = pytest.mark.skipif(not _cuda.enumerate_devices()[0], reason="no NVIDIA CUDA device")


def _variants(cc, ctx, band):
    tiles = (1, cc._COARSE_TILE_T[band]) if band in cc._COARSE_TILE_T else (1,)
    out = []
    for tile in tiles:
        for ppg in (1, 2, 4, 8, 16):
            if ppg > 1 and band // 16 * ppg > 1024:
                continue
            for twt in (False, True):
                try:
                    fn, wg = ctx.pipeline(band, "fusedTierB", c16=True, ppg=ppg, tile=tile, twt=twt)
                except Exception:                               # noqa: BLE001 -- not built
                    continue
                out.append((fn, wg, ppg, tile))
    return out


def _coarse(cc, ctx, var, band, D, T):
    """|coarse value| per template for one data row, by one coarse variant."""
    fn, wg, ppg, tile = var
    nt = T.shape[0]
    rows = 1
    bufs = [cc._Buffer(ctx, rows * band * 4), cc._Buffer(ctx, nt * band * 4),
            cc._Buffer(ctx, rows * nt * 4 + 4096), cc._Buffer(ctx, rows * nt * 8 + 4096)]
    try:
        st = ctx.stream
        bufs[0].write(cc._pack_half2(D), st)
        bufs[1].write(cc._pack_half2(T), st)
        ent = ctx._c16_flags.get(ctx._labels.get(fn.value))
        ctx._c16_bound_flag(fn)
        assert ent is not None, "coarse module without the mf_c16_raw switch"
        grid, rowarg = cc._coarse_grid(rows, nt, ppg, tile)
        ctx._launch(fn, grid, wg, [bufs[0].dptr, bufs[1].dptr, bufs[2].dptr, bufs[3].dptr,
                                   cc._u32(nt), cc._u32(0), cc._u32(band),
                                   cc._u32(band if rowarg is None else rowarg),
                                   cc._i32(cc._shift(band)), cc._u32(1), cc._u32(0)], stream=st)
        ctx._sync(st)
        v = bufs[3].read(np.complex64, rows * nt)
    finally:
        for b in bufs:
            b.destroy()
    return np.abs(v.astype(np.complex128))


@pytest.mark.parametrize("band", [64, 256, 1024])
def test_bound_covers_the_exact_maximum(band, monkeypatch):
    from matchedfilter import _cudacompute as cc
    from test_gpu_c16_bound import _families
    if not cc._use_c16(band):
        pytest.skip("band %d has no fp16 coarse tier" % band)
    nt = 128
    rng = np.random.default_rng(1234 + band)
    cases = []
    for D, T in _families(band, rng, nt):
        # Scale each template so every pair's exact maximum is 8 (well inside fp16).
        y = np.fft.ifft(D * np.conj(T), axis=1) * band
        T = T * (8.0 / np.abs(y).max(axis=1))[:, None]
        exact = np.abs(np.fft.ifft(D.astype(np.complex64).astype(np.complex128)
                                   * np.conj(T.astype(np.complex64).astype(np.complex128)),
                                   axis=1) * band).max(axis=1)
        cases.append((D.astype(np.complex64), T.astype(np.complex64), exact))
    ctx = cc.Context(0)
    try:
        variants = _variants(cc, ctx, band)
        assert variants
        for var in variants:
            for D, T, exact in cases:
                monkeypatch.setenv("MF_VK_C16_BOUND", "0")
                raw = _coarse(cc, ctx, var, band, D, T)
                monkeypatch.setenv("MF_VK_C16_BOUND", "1")
                bnd = _coarse(cc, ctx, var, band, D, T)
                tag = "band %d ppg %d tile %d" % (band, var[2], var[3])
                assert (bnd >= exact).all(), "%s: bound below the exact maximum by %r" % (
                    tag, (bnd - exact).min())
                assert (bnd > raw).all(), "%s: the switch did not change the output" % tag
                use = (exact - raw) / (bnd - raw)
                assert use.max() < 0.5, "%s: margin use %.3f" % (tag, use.max())
    finally:
        ctx.destroy()
