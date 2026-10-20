"""Native sparse extraction preserves dense peaks across reused series buffers."""
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core


@pytest.mark.parametrize("kind", ["complex", "real", "strided_real"])
@pytest.mark.parametrize("binsize", [1024, 127])
@pytest.mark.parametrize("q15", [False, True])
def test_sparse_series_matches_dense_with_reused_storage(kind, binsize, q15):
    mf.backend()
    n, nt_all, t0, nt = 1024, 13, 3, 7
    rng = np.random.default_rng(1741)
    templates = (rng.normal(size=(nt_all, n))
                 + 1j * rng.normal(size=(nt_all, n))).astype(np.complex64)
    templates *= np.float32(np.sqrt(n)) / np.linalg.norm(
        templates, axis=1, keepdims=True)
    templates[::3] *= np.float32(.001)       # populated calls also have empty rows
    plans = [_core.HMF(n, 1, nt_all, [128, 256], 3, n) for _ in range(2)]
    for plan in plans:
        plan.set_reference(np.ones(n, np.float32))
        plan.set_template_batch(0, templates)
        if q15 and not plan.set_q15(True):
            pytest.skip("Q15 unavailable")
        if not q15:
            plan.set_q15(False)
        assert plan.set_q15_recheck_late(q15)
        if kind != "complex":
            assert plan.set_real_series(True, 2 if kind == "strided_real" else 1)

    starts = (np.arange(8) * 768).astype(np.uintp)
    low = np.array([64] * 5 + [96] * 3, np.uintp)
    high = low + 768                         # equal bin counts, different windows
    size = int(starts[-1]) + n - 139         # last block needs zero padding
    source = (rng.normal(size=size) + 1j * rng.normal(size=size)).astype(np.complex64)
    if kind == "real":
        source = source.real.copy()
    elif kind == "strided_real":
        # Export exactly the contiguous floats spanning the real lane, as the
        # Python run_series path does; native stride=2 ignores imaginary samples.
        source = source.view(np.float32)[:-1]
    nb = (768 + binsize - 1) // binsize
    shape = (len(starts), nt, nb)
    idx = np.empty(shape, np.int64)
    val = np.empty(shape, np.complex64)
    mag = np.empty(shape, np.float32)
    counts = [np.empty(shape[:2], np.int32) for _ in plans]
    # Exercise both kinds of empty result: rejected by a gate, or refined but
    # below the final threshold. The last call leaves earlier sparse peaks stale.
    schedule = [([1e8, 1e8], .2, False), ([0., 0.], .2, True),
                ([0., 0.], 1e8, False), ([0., 0.], .2, True),
                ([1e8, 1e8], .2, False)]
    for gates, threshold, populated in schedule:
        for plan, count in zip(plans, counts):
            plan.set_thresholds(gates)
            count.fill(-77)
        fl, ix, vl, total = plans[0].run_series_sparse(
            source, starts, low, high, t0, nt, binsize, threshold, counts[0])
        dense_total = plans[1].run_series(
            source, starts, low, high, t0, nt, binsize, threshold,
            idx, val, mag, counts[1])
        flat = np.flatnonzero(idx.ravel() >= 0)
        assert total == dense_total == len(flat) == int(counts[1].sum())
        np.testing.assert_array_equal(counts[0], counts[1])
        np.testing.assert_array_equal(np.frombuffer(fl, np.int64), flat)
        np.testing.assert_array_equal(np.frombuffer(ix, np.int64), idx.ravel()[flat])
        np.testing.assert_array_equal(np.frombuffer(vl, np.complex64), val.ravel()[flat])
        assert len(fl) == len(ix) == len(vl) == 8 * total
        if populated:
            assert 0 < total < idx.size
            assert np.any(counts[0] == 0)
            if nb > 1:
                assert np.any(counts[0] > 1)
        else:
            assert total == 0
            assert fl == ix == vl == b""


@pytest.mark.parametrize("bad", ["short_counts", "different_bins", "bad_template"])
def test_sparse_series_rejects_invalid_output_layout(bad):
    n = 128
    plan = _core.HMF(n, 1, 1, [64])
    plan.set_thresholds([0.])
    plan.set_template(0, np.ones(n, np.complex64))
    source = np.ones(2 * n, np.complex64)
    starts = np.array([0, n], np.uintp)
    low = np.zeros(2, np.uintp)
    high = np.full(2, n, np.uintp)
    backing = np.full(2, -77, np.int32)
    count, t0 = backing, 0
    if bad == "short_counts":
        count = backing[:1]
    elif bad == "different_bins":
        high[1] -= 1
    else:
        t0 = 1
    with pytest.raises(ValueError):
        plan.run_series_sparse(source, starts, low, high, t0, 1, 1, .2, count)
    np.testing.assert_array_equal(backing, [-77, -77])
