"""CPU correlation calls run as correlation steps of one table (_batches._cpu_correlate and
_core.HMFTable.run_corr): correlate_series, and correlate_series_channels for every channel in
one C call. The outputs are, to the bit, what each block-size group's correlation kernel gives
over the blocks the windows reach, with the samples outside the windows zeroed and the rows
scaled with numpy, group by group, as the Python path computed them. The steps of a call shape
are compiled once; new windows, supports or selections compile their own, scale values and
outputs are bound per call."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank, _batches

S = 1 << 16


def _bank(counts, complex_taps, seed):
    """A correlation bank of windowed chirps with these tap counts."""
    rng = np.random.default_rng(seed)
    taps = np.zeros((len(counts), max(counts)), dtype=np.complex64 if complex_taps else np.float32)
    for i, c in enumerate(counts):
        t = np.arange(c) / 2048.0
        phase = 2 * np.pi * ((40 + 9 * i) * t + 0.5 * (120 + 13 * i) * t * t) + rng.uniform(0, 6)
        row = (np.exp(1j * phase) if complex_taps else np.cos(phase)) * np.hanning(c)
        taps[i, :c] = row / np.linalg.norm(row)
    return TimeDomainFilterBank(taps, np.asarray(counts), engine="corr", device="cpu")


#: Tap counts whose block-size groups interleave in the bank's order.
INTERLEAVED = [300, 2900, 420, 3100, 360, 2500]


def _series(rng, complex_series):
    if complex_series:
        return (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
    return rng.standard_normal(S).astype(np.float32)


def _per_group(bank, ser, windows, rows=None, row_scales=None, out=None, support=None):
    """The output as the Python path made it: per template group (and run of the selected
    rows) one kernel call over the blocks the windows reach, then the samples outside the
    windows zeroed and the rows scaled with numpy; a group whose templates are not one run of
    the output computed into a scratch and copied to its rows."""
    W = np.asarray(windows, dtype=np.int64).reshape(-1, 2) if windows is not None else \
        np.array([[0, ser.size]], np.int64)
    n_rows = bank.n_templates if rows is None else len(rows)
    out = np.zeros((n_rows, ser.size), np.complex64) if out is None else out
    runs = []
    if rows is None:
        for g in bank._groups:
            idx = g.template_indices
            if np.array_equal(idx, np.arange(idx[0], idx[0] + idx.size)):
                runs.append((g, 0, idx.size, np.arange(idx[0], idx[0] + idx.size), True))
            else:
                runs.append((g, 0, idx.size, idx, False))
    else:
        for j, t in enumerate(rows):
            g, li = bank._template_map[int(t)]
            if runs and runs[-1][0] is g and runs[-1][1] + runs[-1][2] == li:
                runs[-1][2] += 1
                runs[-1][3].append(j)
            else:
                runs.append([g, li, 1, [j], True])
    for g, li, cnt, out_rows, direct in runs:
        out_rows = np.asarray(out_rows)
        cp = g.get_correlation_plan()
        ep = cp._continuous_plan()
        lo, hi = cp.valid
        st, bounds, _, edges = bank._windows_layout(g, ser.size, W, support if direct else None)
        dest = out[out_rows[0]:out_rows[0] + cnt] if direct else np.empty((cnt, ser.size),
                                                                           np.complex64)
        if st.size:
            run = (ep.correlate_series_continuous_real if ser.dtype == np.float32
                   else ep.correlate_series_continuous)
            run(ser, st, lo, hi, li, cnt, dest, bounds)
        for a, b in edges.reshape(-1, 2):
            dest[:, a:b] = 0
        if row_scales is not None:
            np.multiply(dest, row_scales[out_rows][:, None], out=dest)
        if not direct:
            out[out_rows] = dest
    return out


def _bits(a):
    return np.ascontiguousarray(a).view(np.uint32)


@pytest.mark.parametrize("complex_series", [False, True])
def test_every_channel_in_one_call_is_each_groups_kernel_calls(complex_series, monkeypatch):
    rng = np.random.default_rng(31 + complex_series)
    bank = _bank(INTERLEAVED, complex_series, 5)
    chans = [_series(rng, complex_series) for _ in range(3)]
    wins = [[(2000, 21000), (21400, 40000)], [(9000, 60000)], [(0, 3000), (50000, S)]]
    sel = [4, 1, 0, 5]                 # across groups, not in the bank's order
    runs = []
    monkeypatch.setattr(type(bank), "correlate_series", lambda *a, **k: pytest.fail("per channel"))
    original = _batches._cpu_correlate

    def counting(calls, scales=None):
        runs.append(len(calls))
        return original(calls, scales)

    monkeypatch.setattr(_batches, "_cpu_correlate", counting)
    outs = [np.full((4, S), 5 - 3j, np.complex64) for _ in chans]
    bank.correlate_series_channels(chans, wins, outs, [None] * 3, templates=sel)
    assert runs == [3]
    for ser, w, o in zip(chans, wins, outs):
        ref = _per_group(bank, ser, w, rows=sel)
        assert np.array_equal(_bits(o), _bits(ref))
    # every template, in the bank's order: interleaved groups go through a scratch
    outs = [np.full((len(INTERLEAVED), S), 1 + 1j, np.complex64) for _ in chans]
    bank.correlate_series_channels(chans, wins, outs, [None] * 3)
    for ser, w, o in zip(chans, wins, outs):
        assert np.array_equal(_bits(o), _bits(_per_group(bank, ser, w)))


@pytest.mark.parametrize("complex_series", [False, True])
def test_scales_selections_and_one_template_are_numpys_products(complex_series):
    rng = np.random.default_rng(41 + complex_series)
    bank = _bank(INTERLEAVED, complex_series, 6)
    x = _series(rng, complex_series)
    scales = np.array([-1.5, 0.25, 2.0, -0.0, 3.5, 0.75], np.float32)
    w = [(1000, 20000), (20300, 45000)]
    got = bank.correlate_series(x, windows=w, scales=scales)
    assert np.array_equal(_bits(got), _bits(_per_group(bank, x, w, row_scales=scales)))
    sel = [5, 0, 2, 3]
    got = bank.correlate_series(x, windows=w, templates=sel, scales=scales)
    ref = _per_group(bank, x, w, rows=sel, row_scales=scales[sel])
    assert np.array_equal(_bits(got), _bits(ref))
    got = bank.correlate_series(x, windows=w, template_index=0, scales=scales[0:1])
    ref = _per_group(bank, x, w, rows=[0], row_scales=scales[0:1])
    assert got.shape == (S,) and np.array_equal(_bits(got), _bits(ref[0]))
    # zeros scaled keep numpy's signs: a negative scale makes the cleared samples -0 + 0i
    assert np.signbit(got[:500].real).all() and not np.signbit(got[:500].imag).any()


def test_a_reused_output_with_its_support_equals_a_fresh_call():
    rng = np.random.default_rng(51)
    bank = _bank(INTERLEAVED, True, 7)
    x = _series(rng, True)
    sel = [1, 2, 4]
    first, second = [(5000, 30000)], [(20000, 50000), (60000, S)]
    out = np.full((3, S), 7 + 7j, np.complex64)
    bank.correlate_series(x, windows=first, templates=sel, out=out)
    bank.correlate_series(x, windows=second, templates=sel, out=out, out_support=first)
    fresh = bank.correlate_series(x, windows=second, templates=sel)
    assert np.array_equal(_bits(out), _bits(fresh))
    assert np.array_equal(_bits(out), _bits(_per_group(bank, x, second, rows=sel)))


def test_a_call_shape_compiles_once_and_binds_its_values(monkeypatch):
    rng = np.random.default_rng(61)
    bank = _bank(INTERLEAVED, False, 8)
    compiled = []
    original = _batches._compile_corr_steps

    def counting(calls, scaled):
        compiled.append(len(calls))
        return original(calls, scaled)

    monkeypatch.setattr(_batches, "_compile_corr_steps", counting)
    chans = [_series(rng, False) for _ in range(2)]
    outs = [np.zeros((2, S), np.complex64) for _ in chans]
    for k in range(3):
        # new series values, new list objects for the windows: the same shape
        chans = [c[::-1].copy() for c in chans]
        bank.correlate_series_channels(chans, [[(1000, 30000)], [(4000, 50000)]], outs,
                                       [None, None], templates=[3, 0])
        assert compiled == [2]
        for ser, w, o in zip(chans, [[(1000, 30000)], [(4000, 50000)]], outs):
            assert np.array_equal(_bits(o), _bits(_per_group(bank, ser, w, rows=[3, 0])))
    # other windows, a support or another selection compile their own steps
    bank.correlate_series_channels(chans, [[(1000, 31000)], [(4000, 50000)]], outs,
                                   [None, None], templates=[3, 0])
    bank.correlate_series_channels(chans, [[(1000, 31000)], [(4000, 50000)]], outs,
                                   [[(1000, 30000)], None], templates=[3, 0])
    bank.correlate_series_channels(chans, [[(1000, 31000)], [(4000, 50000)]], outs,
                                   [None, None], templates=[0, 3])
    assert compiled == [2, 2, 2, 2]
    # scale values are bound per call: one compile for a scaled shape, any values
    for k in range(3):
        scales = np.linspace(-1, 1 + k, 6).astype(np.float32)
        got = bank.correlate_series(chans[0], windows=slice(2000, 40000), scales=scales)
        ref = _per_group(bank, chans[0], [(2000, 40000)], row_scales=scales)
        assert np.array_equal(_bits(got), _bits(ref))
    assert compiled == [2, 2, 2, 2, 1]


def test_wrong_outputs_and_selections_are_refused_before_anything_runs():
    rng = np.random.default_rng(71)
    bank = _bank(INTERLEAVED, True, 9)
    chans = [_series(rng, True) for _ in range(2)]
    good = np.zeros((2, S), np.complex64)
    with pytest.raises(ValueError, match="out must be"):
        bank.correlate_series_channels(chans, [None, None],
                                       [good, np.zeros((3, S), np.complex64)], [None, None],
                                       templates=[0, 1])
    with pytest.raises(IndexError):
        bank.correlate_series_channels(chans, [None, None], [good, good.copy()], [None, None],
                                       templates=[0, 6])
    with pytest.raises(ValueError, match="distinct"):
        bank.correlate_series_channels(chans, [None, None], [good, good.copy()], [None, None],
                                       templates=[1, 1])
    assert not good.any()


def test_banks_with_compiled_correlation_steps_are_freed_without_the_cyclic_collector():
    """A bank keeps its compiled correlation steps; they must not hold the bank, or a dead
    bank waits in a reference cycle for the collector."""
    import gc
    import weakref
    rng = np.random.default_rng(81)
    bank = _bank(INTERLEAVED, True, 10)
    x = _series(rng, True)
    outs = [np.zeros((6, S), np.complex64) for _ in range(2)]
    bank.correlate_series_channels([x, x[::-1].copy()], [None, [(100, 9000)]], outs,
                                   [None, None])
    assert len(bank.__dict__["_corr_steps"]) == 1
    ref = weakref.ref(bank)
    gc.disable()
    try:
        del bank
        assert ref() is None
    finally:
        gc.enable()
