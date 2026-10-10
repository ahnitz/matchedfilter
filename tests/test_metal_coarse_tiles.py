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
    if not _mtlcompute._shipped("tierb_%d_c16t%d" % (band, _mtlcompute._COARSE_TILE_T[band])):
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
        for tile in ("0", "1"):
            monkeypatch.setenv("MF_METAL_COARSE_TILE", tile)
            ctx._hier.clear()
            idx, val = ctx.hier_peaks(n, band, d, h, h[:, :band], raw_thr, threshold=0.0)
            out[tile] = (idx.copy(), val.copy(), ctx.last_refinements)
        np.testing.assert_array_equal(out["0"][0], out["1"][0])
        np.testing.assert_array_equal(out["0"][1], out["1"][1])
        assert out["0"][2] == out["1"][2]
        if raw_thr == 0.0:
            assert out["1"][0][nd - 1, nt - 1, 0] == 700
        counts.append(out["1"][2])
    assert counts[0] == nd * nt and counts[-1] < counts[0]   # the gates did dismiss pairs
