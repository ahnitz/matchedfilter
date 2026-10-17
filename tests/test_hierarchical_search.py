"""HierarchicalSearch against the same filters composed by hand.

The root is checked against numpy's inverse real transform; inner series against one
correlation bank per filter over the whole series; leaf peaks against a separately built
leaf bank on those series. So these tests check what the search adds -- spans, windows,
packed pairs, buffer reuse across chunks, the threshold envelope, the hooks -- and not
the filters themselves, which have their own tests."""
import numpy as np
import pytest

from matchedfilter import _core
from matchedfilter.search import BlockInput, HierarchicalSearch, Inner, Leaf, Root
from matchedfilter.time_domain import TimeDomainFilterBank

N = 1 << 15                      # block length
VALID = (4096, N - 4096)
BAND = (60, N // 2 - 200)
LEAF = dict(engine="flat", binsize=512)


def _spec(rng, n=N):
    h = n // 2 + 1
    return (rng.standard_normal(h) + 1j * rng.standard_normal(h)).astype(np.complex64)


def _root_ref(D, T, k0, k1, scale, n=N):
    P = np.zeros(n // 2 + 1, np.complex128)
    P[k0:k1] = np.conj(T[k0:k1].astype(np.complex128)) * D[k0:k1]
    P[0], P[-1] = P[0].real, P[-1].real
    return scale * n * np.fft.irfft(P, n)


@pytest.mark.parametrize("n", [128, 1024, 1 << 16])
def test_root_matches_inverse_real_transform_on_every_target(n):
    rng = np.random.default_rng(1)
    h = n // 2
    try:
        for tgt in _core.targets():
            _core.set_target(tgt)
            for k0, k1 in ((0, h + 1), (3, h - 5), (h // 4 + 1, h // 4 + 37), (h // 3, h + 1)):
                D, T = _spec(rng, n), _spec(rng, n)
                out = np.empty(n, np.float32)
                _core.Root(n).real(D, T, k0, k1, 0.37, out)
                ref = _root_ref(D, T, k0, k1, 0.37, n)
                np.testing.assert_allclose(out, ref, rtol=0, atol=2e-6 * np.abs(ref).max(),
                                           err_msg="%s n=%d band %d:%d" % (tgt, n, k0, k1))
    finally:
        _core.set_target(None)


def test_root_rejects_short_spectra_and_bands_past_nyquist():
    r = _core.Root(256)
    out = np.empty(256, np.float32)
    with pytest.raises(ValueError):
        r.real(np.zeros(100, np.complex64), np.zeros(129, np.complex64), 0, 10, 1.0, out)
    with pytest.raises(ValueError):
        r.real(np.zeros(129, np.complex64), np.zeros(129, np.complex64), 0, 130, 1.0, out)


def _real_taps(rng, c):
    t = rng.standard_normal(c).astype(np.float32)
    return t / np.linalg.norm(t)


def _complex_taps(rng, counts):
    taps = np.zeros((len(counts), max(counts)), np.complex64)
    for i, c in enumerate(counts):
        t = rng.standard_normal(c) + 1j * rng.standard_normal(c)
        taps[i, :c] = t / np.linalg.norm(t)
    return taps


def _tree(rng, inner_counts=(301, 451, 451, 601, 251), leaf_counts=(101, 151, 201)):
    groups = []
    for i, c in enumerate(inner_counts):
        lf = Leaf(_complex_taps(rng, leaf_counts), leaf_counts,
                  lags=rng.integers(0, 40, len(leaf_counts)), node_id=("leaf", i))
        groups.append(Inner(_real_taps(rng, c), children=[lf], node_id=("inner", i)))
    return Root(_spec(rng), BAND, children=groups, node_id="root")


def _inputs(rng, nblocks=2, channels=("A", "B")):
    return {ch: BlockInput([_spec(rng) for _ in range(nblocks)], [VALID] * nblocks,
                           root_scale=lambda root, b, s=1.0 + 0.25 * j: s / N,
                           tags=["%s%d" % (ch, b) for b in range(nblocks)])
            for j, ch in enumerate(channels)}


def _reference(root, inputs, ch, k):
    """Every node's series for block k of channel ch, each filter over the whole series."""
    inp = inputs[ch]
    out = {id(root): _root_ref(inp.spectra[k], root.spectrum, *root.band,
                               inp.root_scale(root, k)).astype(np.float32)}

    def down(node):
        for c in node.children:
            if isinstance(c, Inner):
                bank = TimeDomainFilterBank(c.taps[None, :], tap_counts=[c.count], engine="corr")
                z = bank.correlate_series(out[id(node)])[0]
                out[id(c)] = z.real.astype(np.float32) if not np.iscomplexobj(c.taps) else z
                down(c)
    down(root)
    return out


def _collect(search, inputs, windows=None, on_series=None):
    got = []

    def on_peaks(ctx):
        for ch in ctx.channels:
            got.append((ctx.leaf.node_id, ctx.chunk, ch, ctx.peaks[ch], ctx.series(ch).copy()))
    search.run(inputs, windows=windows, on_series=on_series, on_peaks=on_peaks)
    return got


def _assert_same_peaks(a, b, rtol=1e-4):
    ka = sorted(zip(a.template_indices.tolist(), a.sample_indices.tolist()))
    kb = sorted(zip(b.template_indices.tolist(), b.sample_indices.tolist()))
    assert ka == kb
    oa = np.lexsort((a.sample_indices, a.template_indices))
    ob = np.lexsort((b.sample_indices, b.template_indices))
    np.testing.assert_allclose(a.snr[oa], b.snr[ob], rtol=rtol, atol=rtol * np.abs(b.snr).max())


def _median_peak(root, inputs):
    """A threshold that half the unthresholded peaks reach."""
    got = _collect(HierarchicalSearch([root], threshold=0.0, leaf_options=LEAF), inputs)
    return float(np.median(np.concatenate([np.abs(g[3].snr) for g in got])))


def _leaf_ref(leaf, series, windows, threshold):
    bank = TimeDomainFilterBank(leaf.taps, leaf.counts, threshold=threshold, **LEAF)
    return bank.filter_series(series, windows=windows)


def test_three_levels_match_the_filters_composed_by_hand():
    rng = np.random.default_rng(2)
    root = _tree(rng)
    inputs = _inputs(rng)
    search = HierarchicalSearch([root], threshold=0.0, leaf_options=LEAF, min_pad=0)
    got = _collect(search, inputs)
    assert len(got) == 5 * 2 * 2                    # leaves x chunks x channels
    pad = search.pad(root)
    for node_id, k, ch, peaks, parent in got:
        ref = _reference(root, inputs, ch, k)
        inner = next(c for c in root.children if c.node_id == ("inner", node_id[1]))
        lo, hi = VALID[0] - pad, VALID[1] + pad
        np.testing.assert_allclose(parent[lo:hi], ref[id(inner)][lo:hi], rtol=0,
                                   atol=2e-5 * np.abs(ref[id(inner)]).max())
        _assert_same_peaks(peaks, _leaf_ref(inner.children[0], ref[id(inner)], [VALID], 0.0))


def test_two_and_four_levels():
    rng = np.random.default_rng(3)
    # two: the leaf filters the root series directly
    lf = Leaf(_complex_taps(rng, (101, 151)), (101, 151), node_id="leaf")
    root2 = Root(_spec(rng), BAND, children=[lf])
    # four: root -> inner -> inner pair -> leaves
    deep = [Inner(_real_taps(rng, c), children=[Leaf(_complex_taps(rng, (101, 131)), (101, 131),
                                                     node_id=("deep", c))])
            for c in (201, 251)]
    root4 = Root(_spec(rng), BAND, children=[Inner(_real_taps(rng, 301), children=deep)])
    inputs = _inputs(rng, nblocks=1)
    for root in (root2, root4):
        search = HierarchicalSearch([root], threshold=0.0, leaf_options=LEAF, min_pad=0)
        got = _collect(search, inputs)
        assert got
        pad = search.pad(root)
        for node_id, k, ch, peaks, parent in got:
            ref = _reference(root, inputs, ch, k)
            leaf = next(l for l in search._leaves_below(root) if l.node_id == node_id)
            p = search._parent[id(leaf)]
            _assert_same_peaks(peaks, _leaf_ref(leaf, ref[id(p)], [VALID], 0.0))
            # the parent series is exact wherever a hook may read it: the windows +- pad
            lo, hi = VALID[0] - pad, VALID[1] + pad
            np.testing.assert_allclose(parent[lo:hi], ref[id(p)][lo:hi], rtol=0,
                                       atol=2e-5 * np.abs(ref[id(p)]).max())


def test_windows_skip_groups_and_reused_buffers_hold_no_stale_values():
    """Chunk 0 searches everything; chunk 1 one narrow window in one group and channel. The
    buffer chunk 1 reuses must read as if fresh: zero outside what chunk 1 computes."""
    rng = np.random.default_rng(4)
    root = _tree(rng)
    inputs = _inputs(rng)
    narrow = [(12000, 14000)]

    def windows(leaf, chunk, ch, extra):
        if chunk == 0:
            return None
        if leaf.node_id == ("leaf", 2) and ch == "B":
            return [(a - extra, b + extra) for a, b in narrow]
        return []
    search = HierarchicalSearch([root], threshold=0.0, leaf_options=LEAF, context=300)
    got = _collect(search, inputs, windows=windows)
    late = [g for g in got if g[1] == 1]
    assert {(g[0], g[2]) for g in late} == {(("leaf", 2), "A"), (("leaf", 2), "B")}
    for node_id, k, ch, peaks, parent in late:
        if ch == "A":                 # searched nowhere in A: produced, and zero
            assert peaks.snr.size == 0 and not parent.any()
            continue
        inner = root.children[2]
        ref = _reference(root, inputs, ch, 1)[id(inner)]
        _assert_same_peaks(peaks, _leaf_ref(inner.children[0], ref, narrow, 0.0))
        pad = search.pad(root)
        lo, hi = narrow[0][0] - 300 - pad, narrow[0][1] + 300 + pad
        np.testing.assert_allclose(parent[lo:hi], ref[lo:hi], rtol=0, atol=2e-5 * np.abs(ref).max())
        reach = search._inner[id(root)].reach
        assert not parent[:max(0, lo - reach)].any() and not parent[hi + reach:].any()


@pytest.mark.parametrize("floor", [1.0, 0.5])
def test_threshold_envelope_keeps_exactly_the_peaks_above_it(floor):
    rng = np.random.default_rng(5)
    root = _tree(rng, inner_counts=(301, 401))
    inputs = _inputs(rng, nblocks=1)
    T = _median_peak(root, inputs)
    env = lambda t: floor + (1.5 - floor) * (0.5 + 0.5 * np.sin(t / 700.0))   # in [floor, 1.5]
    search = HierarchicalSearch([root], threshold=T, envelope_floor=floor, leaf_options=LEAF)
    for lf in search._leaves_below(root):
        assert search.leaf_bank(root, lf).threshold == pytest.approx(T * floor)
    got = _collect(search, inputs, on_series=lambda ctx: {c: env for c in ctx.channels})
    for node_id, k, ch, peaks, parent in got:
        leaf = next(l for l in search._leaves_below(root) if l.node_id == node_id)
        ref = _leaf_ref(leaf, parent, [VALID], T * floor)
        t = np.clip(ref.sample_indices - leaf.lags[ref.template_indices], 0, N - 1)
        keep = np.abs(ref.snr) >= T * env(t)
        assert keep.any() and not keep.all()
        _assert_same_peaks(peaks, type(ref)(*(f[keep] for f in ref)), rtol=0)


def test_an_envelope_below_its_floor_is_an_error():
    rng = np.random.default_rng(6)
    root = _tree(rng, inner_counts=(301,))
    inputs = _inputs(rng, nblocks=1)
    search = HierarchicalSearch([root], threshold=_median_peak(root, inputs), leaf_options=LEAF)
    with pytest.raises(ValueError, match="envelope_floor"):
        _collect(search, inputs,
                 on_series=lambda ctx: {c: (lambda t: np.full(t.shape, 0.5)) for c in ctx.channels})


def test_hooks_see_root_series_and_refilter_matches_the_leaf_bank():
    rng = np.random.default_rng(7)
    root = _tree(rng, inner_counts=(301, 351))
    inputs = _inputs(rng, nblocks=1)
    search = HierarchicalSearch([root], threshold=0.0, leaf_options=LEAF)
    seen, refiltered = [], []

    def on_series(ctx):
        for ch in ctx.channels:
            ref = _root_ref(inputs[ch].spectra[0], root.spectrum, *root.band,
                            inputs[ch].root_scale(root, 0))
            np.testing.assert_allclose(ctx.series[ch], ref, rtol=0, atol=2e-6 * np.abs(ref).max())
            seen.append(ch)

    def on_peaks(ctx):
        r = ctx.refilter("B", windows=slice(10000, 11000), binsize=64, threshold=0.0,
                         template_index=1)
        direct = search.leaf_bank(root, ctx.leaf).filter_series(
            ctx.series("B"), windows=slice(10000, 11000), binsize=64, threshold=0.0,
            template_index=1)
        _assert_same_peaks(r, direct, rtol=0)
        assert ctx.series("A", node=root) is not None
        refiltered.append(ctx.leaf.node_id)
    search.run(inputs, on_series=on_series, on_peaks=on_peaks)
    assert seen == ["A", "B"] and len(refiltered) == 2


def test_nested_inner_series_cover_their_childrens_reach():
    """A short inner filter (small blocks) above long ones (large blocks), searched in one
    narrow window: the outer series must reach far enough past the inner ones' spans that
    they are exact over theirs -- block rounding alone does not cover a long child."""
    rng = np.random.default_rng(8)
    deep = [Inner(_real_taps(rng, c), children=[Leaf(_complex_taps(rng, (101,)), (101,),
                                                     node_id=("deep", c))])
            for c in (1501, 1201)]
    root = Root(_spec(rng), BAND, children=[Inner(_real_taps(rng, 51), children=deep)])
    inputs = _inputs(rng, nblocks=1, channels=("A",))
    search = HierarchicalSearch([root], threshold=0.0, leaf_options=LEAF, min_pad=0)
    pad = search.pad(root)
    # Put the deep series' span edge on a block boundary of the short filter above them, so
    # whole-block rounding gives that filter nothing past the span.
    short = search._batch(root, N)               # the 51-tap filter's batch
    lo_v, hi_v = short._plan[0][0].valid
    edge = 3 * (hi_v - lo_v) + lo_v              # a block boundary of its output
    start = edge + pad                           # the deep series' span starts there
    narrow = [(start, start + 400)]
    got = _collect(search, inputs, windows=lambda lf, k, c, extra: narrow)
    ref = _reference(root, inputs, "A", 0)
    for node_id, k, ch, peaks, parent in got:
        leaf = next(l for l in search._leaves_below(root) if l.node_id == node_id)
        p = ref[id(search._parent[id(leaf)])]
        lo, hi = narrow[0][0] - pad, narrow[0][1] + pad
        np.testing.assert_allclose(parent[lo:hi], p[lo:hi], rtol=0, atol=2e-5 * np.abs(p).max())
        _assert_same_peaks(peaks, _leaf_ref(leaf, p, narrow, 0.0))
