"""Metal tiled coarse builds (two templates per lane, ragged tiles): the same peaks as the
untiled builds for any template count, including odd counts and partial last tiles."""
import sys

import numpy as np
import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="Metal only")


@pytest.fixture
def ctx():
    from matchedfilter import _mtlcompute
    try:
        c = _mtlcompute.Context(0)
    except Exception as e:                      # pragma: no cover - no device
        pytest.skip("no Metal device: %s" % e)
    yield c
    c.destroy()


@pytest.mark.parametrize("band,nd,nt", [(256, 3, 7), (128, 2, 5), (512, 2, 9), (64, 5, 1),
                                        (256, 4, 16)])
def test_tiled_coarse_matches_untiled(ctx, monkeypatch, band, nd, nt):
    from matchedfilter import _mtlcompute
    from matchedfilter._coarse import TILE_PROBE, coarse_stem
    tiles = [str(t) for t in TILE_PROBE if _mtlcompute._shipped(coarse_stem(band, 1, t))]
    if not tiles:
        pytest.skip("no tiled build at this band")
    n = 4096
    rng = np.random.default_rng(band + nt)
    d = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    d[nd - 1] += 40.0 * h[nt - 1] * np.exp(-2j * np.pi * np.arange(n) * 700 / n).astype(np.complex64)
    # Gate thresholds that dismiss some pairs and pass others: the refined set (and so the
    # peaks) is decided by the coarse kernel, which is what differs between the builds.
    counts = []
    for raw_thr in (0.0, 1.0, 3.0, 10.0):
        out = {}
        # ("1", "0"): untiled with the fp32 twiddle recurrence, the reference; every tile
        # with each twiddle source (MF_METAL_COARSE_TWT: "1" the build's fp16 table).
        for tile in ["1"] + tiles:
            for twt in ("0", "1"):
                monkeypatch.setenv("MF_METAL_COARSE_TILE", tile)
                monkeypatch.setenv("MF_METAL_COARSE_TWT", twt)
                ctx._hier.clear()
                idx, val = ctx.hier_peaks(n, band, d, h, h[:, :band], raw_thr, threshold=0.0)
                out[tile, twt] = (idx.copy(), val.copy(), ctx.last_refinements)
        ref = out["1", "0"]
        for k, got in out.items():
            np.testing.assert_array_equal(ref[0], got[0], err_msg=str(k))
            np.testing.assert_array_equal(ref[1], got[1], err_msg=str(k))
            assert ref[2] == got[2], k
        if raw_thr == 0.0:
            assert ref[0][nd - 1, nt - 1, 0] == 700
        counts.append(ref[2])
    assert counts[0] == nd * nt and counts[-1] < counts[0]   # the gates did dismiss pairs
