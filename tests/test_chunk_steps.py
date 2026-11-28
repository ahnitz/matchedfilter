"""A CPU search chunk's inner correlations and leaf searches run as the steps of one table
(_batches._chunk_steps, HierarchicalSearch._cpu_chunk): compiled the first time a chunk's
shape (its windows and what its inner nodes' slots hold) is seen, kept by the search, and
run by one C call. Its peaks and series are, to the bit, those of the walk and
correlate_and_filter_many; correlate_and_filter_many's untiled path is the same table."""
import gc
import weakref

import numpy as np

from matchedfilter import _batches
from matchedfilter.search import BlockInput, HierarchicalSearch, Inner, Leaf, Root
from matchedfilter.time_domain import TimeDomainFilterBank

N = 1 << 14
VALID = (2048, N - 2048)
BAND = (40, N // 2 - 100)
LEAF = dict(engine="flat", binsize=256)


def _complex_taps(rng, counts):
    taps = np.zeros((len(counts), max(counts)), np.complex64)
    for i, c in enumerate(counts):
        t = rng.standard_normal(c) + 1j * rng.standard_normal(c)
        taps[i, :c] = t / np.linalg.norm(t)
    return taps


def _spec(rng):
    h = N // 2 + 1
    return (rng.standard_normal(h) + 1j * rng.standard_normal(h)).astype(np.complex64)


def _search(rng):
    """A root, three inner nodes of complex taps (complex rows, which the leaves read in
    place) and a leaf of three templates below each."""
    inner = []
    for i, c in enumerate((201, 301, 251)):
        leaf = Leaf(_complex_taps(rng, (61, 91, 121)), (61, 91, 121), node_id=("leaf", i))
        inner.append(Inner(_complex_taps(rng, (c,))[0], children=[leaf], node_id=("inner", i)))
    root = Root(_spec(rng), BAND, children=inner, node_id="root")
    return HierarchicalSearch([root], threshold=2.0, leaf_options=LEAF)


def _inputs(rng, nblocks):
    return {ch: BlockInput([_spec(rng) for _ in range(nblocks)], [VALID] * nblocks,
                           root_scale=lambda root, b, s=1.0 + 0.5 * j: s / N)
            for j, ch in enumerate(("A", "B"))}


def _collect(search, inputs, windows=None):
    got = []

    def on_peaks(ctx):
        for ch in ctx.channels:
            got.append((ctx.leaf.node_id, ctx.chunk, ch, tuple(ctx.peaks[ch]),
                        ctx.series(ch).copy()))
    search.run(inputs, windows=windows, on_peaks=on_peaks)
    return got


def _same(a, b):
    assert len(a) == len(b) and len(a) > 0
    for x, y in zip(a, b):
        assert x[:3] == y[:3]
        for u, v in zip(x[3], y[3]):
            assert u.dtype == v.dtype and np.array_equal(u, v)
        assert x[4].tobytes() == y[4].tobytes()


def test_a_chunk_shape_compiles_once_and_gives_the_walk(monkeypatch):
    """Chunks of one shape compile once (the first chunk, whose slots held nothing, and the
    second, whose slots held the first's spans), every later chunk and pass runs the kept
    plan; a chunk with other windows compiles its own; the peaks and the series the hooks
    read are, to the bit, those of the walk."""
    rng = np.random.default_rng(3)
    search = _search(rng)
    inputs = _inputs(rng, 5)
    compiled = []
    chunk_steps = _batches._chunk_steps
    monkeypatch.setattr(_batches, "_chunk_steps",
                        lambda *a: compiled.append(1) or chunk_steps(*a))
    first = _collect(search, inputs)
    again = _collect(search, inputs)
    assert len(compiled) == 2
    _same(first, again)

    def windows(leaf, chunk, ch, extra):
        return [(3000 - extra, 9000 + extra)] if chunk == 2 else None
    shaped = _collect(search, inputs, windows)
    assert len(compiled) == 4            # chunk 2, and chunk 3, whose slots held chunk 2's
    monkeypatch.setattr(HierarchicalSearch, "_chunks_as_table", lambda self, root: False)
    walked = _search(np.random.default_rng(3))
    _same(first, _collect(walked, inputs))
    _same(shaped, _collect(walked, inputs, windows))


def test_correlate_and_filter_many_untiled_is_one_table(monkeypatch):
    """Untiled, correlate_and_filter_many runs its correlations and the leaf jobs that read
    them as one table run, with the outputs and peaks of correlate_series followed by
    filter_series_many."""
    rng = np.random.default_rng(8)
    mid = TimeDomainFilterBank(_complex_taps(rng, (201, 301)), [201, 301], engine="corr")
    leaf = TimeDomainFilterBank(_complex_taps(rng, (61, 91)), [61, 91], threshold=2.0, **LEAF)
    x = [rng.standard_normal(N).astype(np.float32) for _ in range(2)]
    outs = [np.zeros((2, N), np.complex64) for _ in x]
    runs = []
    run_steps = _batches._run_steps
    monkeypatch.setattr(_batches, "_run_steps", lambda *a: runs.append(1) or run_steps(*a))
    got = TimeDomainFilterBank.correlate_and_filter_many(
        [(mid, s, dict(windows=[(1000, 15000)], out=o)) for s, o in zip(x, outs)],
        [(leaf, o[r], dict(windows=[(1500, 14000)])) for o in outs for r in range(2)],
        tile_bytes=0)
    assert len(runs) == 1
    ref_outs = [mid.correlate_series(s, windows=[(1000, 15000)]) for s in x]
    want = TimeDomainFilterBank.filter_series_many(
        [(leaf, o[r], dict(windows=[(1500, 14000)])) for o in ref_outs for r in range(2)])
    for o, r in zip(outs, ref_outs):
        assert o.tobytes() == r.tobytes()
    assert sum(len(g.snr) for g in got) > 0
    for g, w in zip(got, want):
        for u, v in zip(g, w):
            assert np.array_equal(u, v)


def test_a_search_with_kept_chunks_frees_its_banks_without_the_collector():
    """The kept chunk plans hold the leaf banks by weak reference: a finished search and its
    banks die with the cyclic collector disabled."""
    rng = np.random.default_rng(5)
    search = _search(rng)
    _collect(search, _inputs(rng, 3))
    assert search._chunk_plans
    refs = [weakref.ref(b) for b in search._leaf_banks.values()]
    refs.append(weakref.ref(search))
    gc.disable()
    try:
        del search
        assert all(r() is None for r in refs)
    finally:
        gc.enable()
