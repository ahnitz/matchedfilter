"""read_followup_items (the host assembly of device follow-ups) in array passes gives exactly
the per-item, per-block assembly it replaced: the same items, layouts and hits in the same
order, and declines (None) whenever a device item's block count disagrees with the layout."""
import types

import numpy as np

from matchedfilter._gpuhost import FOLLOWUP_ITEM_WORDS, read_followup_items
from matchedfilter.time_domain import TimeDomainFilterBank, _consume_into, _results_from


def _reference(items, idx_all, val_all, nbins, bpi, groups, spec, series_len):
    out = []
    order = np.lexsort((items[:, 1], items[:, 0]))
    bs = int(spec.binsize)
    for it in order:
        o = items[it]
        j, rank = int(o[0]), int(o[1])
        c0 = int(o[2]) | (int(o[3]) << 32)
        ti = int(o[4]) | (int(o[5]) << 32)
        g = groups[int(o[7])]
        S = int(series_len[int(spec.pairs[j])])
        W = np.array([[max(0, c0 - int(spec.half)), min(S, c0 + int(spec.half))]], np.int64)
        st, ws, we = TimeDomainFilterBank._window_layout(g, W, S)
        m = int(st.size)
        if m != int(o[9]) or m > bpi:
            return None
        base = int(it) * bpi * nbins
        idx = np.asarray(idx_all[base:base + m * nbins]).reshape(m, 1, nbins).astype(np.int64)
        val = np.array(val_all[base:base + m * nbins]).reshape(m, 1, nbins)
        counts = ((we - ws + bs - 1) // bs).astype(np.int64)
        lists = ([], [], [], [], [])
        stt = st.astype(np.int64)
        for u in np.unique(counts):
            mk = counts == u
            _consume_into(lists, idx[mk][:, :, :u], val[mk][:, :, :u], stt[mk], g,
                          (int(o[6]), 1), g.n, ti)
        out.append((j, rank, c0, ti, _results_from(lists)))
    return out


def _case(rng, ngroups=2, k=40, S=1 << 18, half=500 * 61, bs=61, nbins=None, bpi=None):
    groups = []
    for _ in range(ngroups):
        n = int(rng.choice([2048, 4096]))
        cbad = int(rng.integers(100, 600))
        groups.append(types.SimpleNamespace(n=n, c_bad=cbad, n_valid=n - cbad,
                                            template_indices=np.arange(8)))
    spec = types.SimpleNamespace(binsize=bs, half=half, pairs=[1, 0, 3, 2])
    series_len = [S, S - 5000, S, S - 77]
    lay = []
    for _ in range(k):
        j = int(rng.integers(0, 4))
        gi = int(rng.integers(0, ngroups))
        Sj = series_len[spec.pairs[j]]
        c0 = int(rng.choice([rng.integers(0, 2000), rng.integers(0, Sj),
                             rng.integers(Sj - 2000, Sj)]))
        W = np.array([[max(0, c0 - half), min(Sj, c0 + half)]], np.int64)
        st, ws, we = TimeDomainFilterBank._window_layout(groups[gi], W, Sj)
        lay.append((j, gi, c0, st.size, ((we - ws + bs - 1) // bs).max() if st.size else 1))
    bpi = bpi or max(m for *_, m, _ in lay)
    nbins = nbins or int(max(u for *_, u in lay))
    items = np.zeros((k, FOLLOWUP_ITEM_WORDS), np.uint32)
    for r, (j, gi, c0, m, _) in enumerate(lay):
        tig = int(rng.integers(0, 1 << 33))
        items[r] = (j, int(rng.integers(0, 3)), c0 & 0xFFFFFFFF, c0 >> 32, tig & 0xFFFFFFFF,
                    tig >> 32, int(rng.integers(0, 8)), gi, r, m)
    idx = np.where(rng.random(k * bpi * nbins) < 0.3,
                   rng.integers(0, 2048, k * bpi * nbins), -1).astype(np.int32)
    val = (rng.standard_normal(k * bpi * nbins)
           + 1j * rng.standard_normal(k * bpi * nbins)).astype(np.complex64)
    return items, idx, val, nbins, bpi, groups, spec, series_len


def _same(a, b):
    assert (a is None) == (b is None)
    if a is None:
        return
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert x[:4] == y[:4]
        for f in x[4]._fields:
            np.testing.assert_array_equal(getattr(x[4], f), getattr(y[4], f))


def test_matches_the_per_item_assembly():
    rng = np.random.default_rng(5)
    for _ in range(20):
        case = _case(rng)
        _same(_reference(*case), read_followup_items(*case))


def test_declines_like_the_per_item_assembly_on_a_block_count_mismatch():
    rng = np.random.default_rng(6)
    items, *rest = _case(rng)
    items[3, 9] += 1
    assert _reference(items, *rest) is None
    assert read_followup_items(items, *rest) is None


def test_no_items():
    rng = np.random.default_rng(7)
    items, *rest = _case(rng)
    assert read_followup_items(items[:0], *rest) == []
