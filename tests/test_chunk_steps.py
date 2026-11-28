"""A CPU search chunk's inner correlations and leaf searches run as the steps of one table
(_batches._chunk_steps, HierarchicalSearch._cpu_chunk): compiled the first time a chunk's
shape (its windows and what its inner nodes' slots hold) is seen, kept by the search, and
run by one C call. Its peaks and series are, to the bit, those of the walk and
correlate_and_filter_many; correlate_and_filter_many's untiled path is the same table. A
search whose inner nodes have inner children is one table too: a child's correlation reads
its parent's complex row in place, or a real lane of it through a lane buffer that the
table's lane copy fills."""
import gc
import weakref

import numpy as np
import pytest

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


def _real_taps(rng, count):
    t = rng.standard_normal(count).astype(np.float32)
    return t / np.float32(np.linalg.norm(t))


def _nested_search(rng):
    """A root whose inner children A and B (real) are a packed pair; A's children are a real
    and a complex filter (complex rows of A's real series) and a leaf, each with an inner
    child of its own (A1x: real taps on the real part of A1's complex row; A2x: complex taps
    reading A2's complex row in place); B's are two real filters (B's series is the pair's
    imaginary lane; their own rows a packed pair). Every lowest inner node has a leaf; the
    leaves are gated, so they read a real lane in place."""
    def leaf(name):
        return Leaf(_complex_taps(rng, (61, 91, 121)), (61, 91, 121), node_id=name)
    a1 = Inner(_real_taps(rng, 151), children=[Inner(_real_taps(rng, 101),
                                                     children=[leaf("A1x")], node_id="A1x")],
               node_id="A1")
    a2 = Inner(_complex_taps(rng, (171,))[0],
               children=[Inner(_complex_taps(rng, (81,))[0], children=[leaf("A2x")],
                               node_id="A2x"), leaf("A2")], node_id="A2")
    a = Inner(_real_taps(rng, 201), children=[a1, a2, leaf("A")], node_id="A")
    b = Inner(_real_taps(rng, 251), children=[
        Inner(_real_taps(rng, 131), children=[leaf("B1")], node_id="B1"),
        Inner(_real_taps(rng, 111), children=[leaf("B2")], node_id="B2")], node_id="B")
    # gated leaves, which read a real lane of a packed row in place
    f = np.arange(N // 2 + 1, dtype=np.float64)
    root = Root(_spec(rng), BAND, children=[a, b], node_id="root",
                profile=(np.where(f > 20, (f + 1.0) ** -2.0, 0.0), 1.0))
    return HierarchicalSearch([root], threshold=2.5, context=64,
                              leaf_options=dict(engine="hier", binsize=256,
                                                false_dismissal=1e-2))


def _collect_ancestors(search, inputs, windows=None):
    """Every leaf's peaks, and every inner ancestor's series and support, as the hooks read
    them."""
    got = []

    def on_peaks(ctx):
        for ch in ctx.channels:
            series = []
            node = search._parent[id(ctx.leaf)]
            while not isinstance(node, Root):
                series.append((node.node_id, tuple(ctx.support(ch, node)),
                               ctx.series(ch, node).copy()))
                node = search._parent[id(node)]
            got.append((ctx.leaf.node_id, ctx.chunk, ch, tuple(ctx.peaks[ch]), series))
    search.run(inputs, windows=windows, on_peaks=on_peaks)
    return got


def _same_ancestors(a, b):
    assert len(a) == len(b) and len(a) > 0
    assert sum(len(x[3][0]) for x in a) > 0
    for x, y in zip(a, b):
        assert x[:3] == y[:3]
        for u, v in zip(x[3], y[3]):
            assert u.dtype == v.dtype and np.array_equal(u, v)
        assert len(x[4]) == len(y[4])
        for (na, sa, ua), (nb, sb, ub) in zip(x[4], y[4]):
            assert (na, sa) == (nb, sb)
            assert ua.dtype == ub.dtype and ua.tobytes() == ub.tobytes()


def test_a_nested_search_runs_one_table_a_chunk_and_gives_the_walk(monkeypatch):
    """A search whose inner nodes have inner children compiles each chunk shape into one
    table with lane copies (real and imaginary lanes of packed rows, the real part of a
    complex row) and reads a complex row in place; with windows that move between chunks,
    so a lane buffer holds spans the next chunk's parent does not, its peaks and every
    ancestor's series are, to the bit, those of the walk, and a second pass runs kept
    plans. (No trials: a leaf bank in a trial runs its chunks as the walk.)"""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    rng = np.random.default_rng(11)
    search = _nested_search(rng)
    inputs = _inputs(rng, 4, gain=200.0)
    compiled, lanes, declined = [], [], []
    chunk_steps = _batches._chunk_steps

    def recording(corr_jobs, leaf_jobs, lane_copies=()):
        result = chunk_steps(corr_jobs, leaf_jobs, lane_copies)
        (compiled if result is not None else declined).append(1)
        lanes.extend(part for _, _, _, part, _ in lane_copies)
        return result
    monkeypatch.setattr(_batches, "_chunk_steps", recording)

    def windows(leaf, chunk, ch, extra):
        if chunk == 1:
            return [(9000 - extra, 12000 + extra)]
        if chunk == 2:
            return [(2500 - extra, 5000 + extra)]
        return None
    first = _collect_ancestors(search, inputs, windows)
    again = _collect_ancestors(search, inputs, windows)
    assert compiled and not declined
    assert 0 in lanes and 1 in lanes      # real and imaginary lanes copied
    n_compiled = len(compiled)
    third = _collect_ancestors(search, inputs, windows)
    assert len(compiled) == n_compiled    # every chunk shape kept
    _same_ancestors(first, again)
    _same_ancestors(first, third)
    monkeypatch.setattr(HierarchicalSearch, "_chunks_as_table", lambda self, root: False)
    walked = _nested_search(np.random.default_rng(11))
    _same_ancestors(first, _collect_ancestors(walked, inputs, windows))


def test_a_lane_copy_fills_its_runs_from_the_row_written_before_it():
    """A lane copy writes the real or imaginary part of a row an earlier correlation call of
    the table wrote into the series of a later call, within its runs only (the rest of the
    series is left as it was), before the later call reads it; a series that is not a
    writable contiguous float32 array, runs past the row and a copy of a later call's output
    are refused."""
    rng = np.random.default_rng(21)
    parent = TimeDomainFilterBank(_complex_taps(rng, (201, 301)), [201, 301], engine="corr")
    child = TimeDomainFilterBank(_real_taps(rng, 121)[None, :], [121], engine="corr")
    x = rng.standard_normal(N).astype(np.float32)
    runs = np.array([[1000, 6000], [7000, 15000]], np.int64)
    for part in (0, 1):
        lane = np.full(N, 7.0, np.float32)
        p_out = np.zeros((2, N), np.complex64)
        c_out = np.zeros((1, N), np.complex64)
        p_call, _ = _batches._corr_call(parent, x, dict(windows=[(500, 15500)], out=p_out))
        c_call, _ = _batches._corr_call(child, lane, dict(windows=[(2000, 14000)], out=c_out))
        compiled = _batches._compile_steps([], [p_call, c_call], (False, False),
                                           lanes=[(1, 0, 1, part, runs)])
        _batches._run_steps(compiled, [x, lane], [p_out, c_out])
        row = p_out[1].imag if part else p_out[1].real
        want = np.full(N, 7.0, np.float32)
        for a, b in runs:
            want[a:b] = row[a:b]
        assert lane.tobytes() == want.tobytes()
        ref = child.correlate_series(want, windows=[(2000, 14000)])
        assert c_out.tobytes() == ref.tobytes()
    readonly = lane.copy()
    readonly.setflags(write=False)
    with pytest.raises(ValueError):
        _batches._run_steps(compiled, [x, readonly], [p_out, c_out])
    long_runs = np.array([[0, N + 1]], np.int64)
    compiled = _batches._compile_steps([], [p_call, c_call], (False, False),
                                       lanes=[(1, 0, 1, 0, long_runs)])
    with pytest.raises(ValueError):
        _batches._run_steps(compiled, [x, lane], [p_out, c_out])
    with pytest.raises(ValueError):
        _batches._compile_steps([], [p_call, c_call], (False, False),
                                lanes=[(0, 1, 0, 0, runs)])


def _inputs(rng, nblocks, gain=1.0):
    return {ch: BlockInput([_spec(rng) for _ in range(nblocks)], [VALID] * nblocks,
                           root_scale=lambda root, b, s=gain * (1.0 + 0.5 * j): s / N)
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


@pytest.mark.parametrize("build", [_search, _nested_search])
def test_a_search_with_kept_chunks_frees_its_banks_without_the_collector(build, monkeypatch):
    """The kept chunk plans hold the leaf banks by weak reference: a finished search, its
    banks, its inner batches' banks and their slots and lane buffers die with the cyclic
    collector disabled."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    rng = np.random.default_rng(5)
    search = build(rng)
    _collect(search, _inputs(rng, 3))
    assert search._chunk_plans
    refs = [weakref.ref(b) for b in search._leaf_banks.values()]
    refs += [weakref.ref(b.bank) for b in search._inner.values()]
    held = [a for b in search._inner.values() for st in b._chan.values()
            for a in (st["slots"], st["lane"]) if a is not None]
    if build is _nested_search:
        assert any(st["lane"] is not None for b in search._inner.values()
                   for st in b._chan.values())
    refs += [weakref.ref(a) for a in held]
    del held
    refs.append(weakref.ref(search))
    gc.disable()
    try:
        del search
        assert all(r() is None for r in refs)
    finally:
        gc.enable()
