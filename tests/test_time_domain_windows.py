"""Analysis windows on TimeDomainFilterBank.filter_series / correlate_series.

The contract: the output depends only on the union of the windows, taken as a
set of samples; one call equals one single-window call per normalised window;
a block that intersects no window is never computed; correlate_series is exact
zero outside the union.

Fixture rules: analytic series (what pycbc passes), a reference profile that
matches the taps, MF_AUTOTUNE=0 so the hierarchical configuration cannot change
between the calls being compared, and every equivalence test asserts a
non-trivial trigger count, because empty == empty proves nothing.
"""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from matchedfilter.time_domain import _normalize_windows


@pytest.fixture(autouse=True)
def _pinned_configuration(monkeypatch):
    monkeypatch.setenv("MF_AUTOTUNE", "0")


S = 24 * 4096
NT, C = 12, 451


def _analytic(seed, scale=2.0, n=S):
    r = np.random.default_rng(seed)
    x = scale * (r.standard_normal(n) + 1j * r.standard_normal(n)) / np.sqrt(2)
    F = np.fft.fft(x)
    F[n // 2:] = 0
    return (np.fft.ifft(F) * np.sqrt(2)).astype(np.complex64)


def _white_taps(rng, counts):
    return [rng.standard_normal(c).astype(np.float32) / np.sqrt(c) for c in counts]


def _flat_profile(n):
    p = np.zeros(n, np.float32)
    p[:n // 2 + 1] = 1.0
    return p / p.sum()


def _bank(engine, device=None, hetero=False, seed=1):
    rng = np.random.default_rng(seed)
    if hetero:
        counts = [251, 1151] * (NT // 2)          # two block sizes, interleaved templates
        return TimeDomainFilterBank(_white_taps(rng, counts), counts, engine=engine,
                                    threshold=5.0, device=device)
    kw = dict(engine=engine, threshold=5.0, device=device, fft_lengths=[4096])
    if engine == "hier":
        kw["reference"] = _flat_profile(4096)
    return TimeDomainFilterBank(_white_taps(rng, [C] * NT), [C] * NT, **kw)


def _sorted(r):
    o = np.lexsort((r.sample_indices, r.template_indices))
    return r.template_indices[o], r.sample_indices[o], r.snr[o]


def _concat(results):
    keys = ("template_indices", "sample_indices", "snr")
    cat = {k: np.concatenate([getattr(r, k) for r in results]) if results else np.empty(0)
           for k in keys}
    o = np.lexsort((cat["sample_indices"], cat["template_indices"]))
    return tuple(cat[k][o] for k in keys)


def _gpu():
    from conftest import usable_gpu
    return usable_gpu()


# --------------------------------------------------------------------- 1. normalisation

@pytest.mark.parametrize("windows, expected", [
    (None, [[0, 100]]),
    (slice(10, 20), [[10, 20]]),
    (slice(None, 20), [[0, 20]]),
    (slice(-30, None), [[70, 100]]),
    (slice(90, 500), [[90, 100]]),
    ([slice(50, 60), slice(10, 20)], [[10, 20], [50, 60]]),
    ([(50, 60), (10, 20)], [[10, 20], [50, 60]]),
    (np.array([[50, 60], [10, 20]], np.int32), [[10, 20], [50, 60]]),
    ([(10, 30), (20, 40)], [[10, 40]]),                 # overlapping
    ([(10, 20), (20, 40)], [[10, 40]]),                 # touching
    ([(10, 10), (30, 20), slice(200, 300)], []),        # empty, reversed, out of range
    ([], []),
    ([(np.int64(3), np.int64(9))], [[3, 9]]),
])
def test_normalize_windows(windows, expected):
    got = _normalize_windows(windows, 100)
    assert got.dtype == np.int64 and got.shape == (len(expected), 2)
    assert got.tolist() == expected


@pytest.mark.parametrize("bad, exc", [
    ([10, 20], ValueError),                              # ambiguous flat pair
    ((10, 20), ValueError),
    (slice(0, 10, 2), ValueError),
    (np.zeros((3,), np.int64), ValueError),
    (np.zeros((2, 3), np.int64), ValueError),
    (np.zeros((2, 2), np.float64), TypeError),
    ([(1.0, 5.0)], TypeError),
    ([(True, 5)], TypeError),
    ([(1, 2, 3)], TypeError),
    (5, TypeError),
])
def test_normalize_windows_rejects(bad, exc):
    with pytest.raises(exc):
        _normalize_windows(bad, 100)


# ------------------------------------------------------- 2. K=1 layout is today's layout

def _old_narrow(S_, c_bad, N_valid, v_start, v_stop):
    """filter_series' former narrow-window layout, verbatim apart from packaging."""
    STEP = N_valid
    first_b = max(0, int((v_start - c_bad) // STEP))
    last_b = min(max(0, int((S_ - 1) // STEP)), int((v_stop - 1 - c_bad) // STEP))
    out = []
    if last_b < first_b:
        return out
    for b_idx in range(first_b, last_b + 1):
        t = b_idx * STEP
        if t >= S_:
            break
        bvt0 = t + c_bad
        rs = max(v_start, bvt0)
        re = min(v_stop, bvt0 + N_valid)
        if re > rs:
            out.append((t, rs - t, re - t))
    return out


def _old_wide(S_, c_bad, N_valid, v_start, v_stop):
    """filter_series' former vectorised layout, verbatim apart from packaging."""
    STEP = N_valid
    first_block_idx = max(0, int(np.floor((v_start - c_bad) / STEP)))
    loop_start = first_block_idx * STEP
    ts = np.arange(loop_start, S_, STEP, dtype=np.uintp)
    bvt0 = ts + c_bad
    keep = (bvt0 < v_stop) & (bvt0 + N_valid > v_start)
    if keep.any():
        last = np.flatnonzero(bvt0 < v_stop)
        keep &= np.arange(ts.size) <= last[-1]
    ts = ts[keep]
    if not ts.size:
        return []
    rs = np.maximum(v_start, bvt0[keep])
    re = np.minimum(v_stop, bvt0[keep] + N_valid)
    good = re > rs
    return list(zip(ts[good].tolist(), (rs - ts)[good].tolist(), (re - ts)[good].tolist()))


class _Geometry:
    def __init__(self, n, taps):
        self.n, self.c_bad, self.n_valid = n, taps - 1, n - taps + 1


def test_single_window_layout_matches_former_layouts():
    rng = np.random.default_rng(0)
    checked = 0
    for S_ in (4096 * 5, 512 * 2048, 512 * 2048 + 777):
        for n, taps in ((4096, 451), (4096, 1151), (2048, 251)):
            g = _Geometry(n, taps)
            for _ in range(700):
                a = int(rng.integers(0, S_))
                b = int(rng.integers(a + 1, S_ + 1))
                t, ws, we = TimeDomainFilterBank._window_layout(g, np.array([[a, b]], np.int64), S_)
                new = list(zip(t.tolist(), ws.tolist(), we.tolist()))
                ref = _old_wide(S_, g.c_bad, g.n_valid, a, b)
                assert new == ref, (S_, n, taps, a, b)
                assert new == _old_narrow(S_, g.c_bad, g.n_valid, a, b)
                checked += 1
    assert checked == 3 * 3 * 700


# ------------------------------------------------------------ 3. K-window equivalence

GEOMETRIES = {
    # two windows inside one block, touching windows, a window narrower than a bin,
    # and windows at both series edges
    "two_in_one_block": [(9000, 9400), (9800, 10300)],
    "touching": [(20000, 26000), (26000, 31000), (40000, 47000)],
    "narrow": [(15000, 15050), (30000, 30010), (61000, 70000)],
    "edges": [(0, 3000), (S - 5000, S), (45000, 52000)],
}


def _equivalence(bank, ser, windows, **kw):
    W = _normalize_windows(windows, ser.size)
    merged = _sorted(bank.filter_series(ser, windows=windows, **kw))
    separate = _concat([bank.filter_series(ser, windows=slice(int(a), int(b)), **kw) for a, b in W])
    for m, s_ in zip(merged, separate):
        np.testing.assert_array_equal(m, s_)
    return len(merged[0])


@pytest.mark.parametrize("engine", ["matchedfilter", "hier"])
@pytest.mark.parametrize("binsize", [None, 256])
def test_merged_equals_separate_calls(engine, binsize):
    ser = _analytic(3)
    bank = _bank(engine)
    total = 0
    for windows in GEOMETRIES.values():
        total += _equivalence(bank, ser, windows, binsize=binsize)
    assert total > 30


def test_hier_counts_track_flat():
    ser = _analytic(3)
    w = list(GEOMETRIES["touching"]) + list(GEOMETRIES["edges"])
    nf = len(_bank("matchedfilter").filter_series(ser, windows=w).snr)
    nh = len(_bank("hier").filter_series(ser, windows=w).snr)
    assert nf > 30 and abs(nh - nf) <= max(2, 0.02 * nf)


def test_merged_equals_separate_template_index_and_threshold_fallback():
    ser = _analytic(4)
    w = GEOMETRIES["touching"] + GEOMETRIES["two_in_one_block"]
    bank = _bank("hier")
    n = _equivalence(bank, ser, w, template_index=3)
    n += _equivalence(bank, ser, w, threshold=4.0)          # below the bank's: flat fallback
    assert n > 20


def test_merged_equals_separate_heterogeneous_bank():
    ser = _analytic(5)
    bank = _bank("matchedfilter", hetero=True)
    n = sum(_equivalence(bank, ser, w, binsize=b) for w in GEOMETRIES.values() for b in (None, 256))
    assert n > 30


@pytest.mark.parametrize("engine", ["matchedfilter", "hier"])
def test_merged_equals_separate_on_gpu(engine):
    gpu = _gpu()
    if gpu is None:
        pytest.skip("no usable GPU")
    ser = _analytic(3)
    bank = _bank(engine, device=gpu)
    n = sum(_equivalence(bank, ser, w, binsize=256) for w in GEOMETRIES.values())
    assert n > 30


def test_union_not_partition_decides_the_result():
    ser = _analytic(6)
    bank = _bank("matchedfilter")
    a = _sorted(bank.filter_series(ser, windows=[(10000, 20000), (20000, 30000)]))
    b = _sorted(bank.filter_series(ser, windows=slice(10000, 30000)))
    c = _sorted(bank.filter_series(ser, windows=np.array([[15000, 30000], [10000, 16000]])))
    for x, y, z in zip(a, b, c):
        np.testing.assert_array_equal(x, y)
        np.testing.assert_array_equal(x, z)
    assert len(a[0]) > 0


def test_peaks_stay_inside_their_windows():
    ser = _analytic(7)
    bank = _bank("matchedfilter")
    w = GEOMETRIES["two_in_one_block"] + GEOMETRIES["narrow"]
    r = bank.filter_series(ser, windows=w, binsize=256, threshold=0.0)
    W = _normalize_windows(w, S)
    inside = np.zeros(S, bool)
    for a, b in W:
        inside[a:b] = True
    assert r.sample_indices.size > 0 and inside[r.sample_indices].all()


def test_empty_windows_return_empty_results():
    bank = _bank("hier")
    for w in ([], [(5, 5)], slice(S + 10, S + 20)):
        r = bank.filter_series(_analytic(8), windows=w)
        assert r.snr.size == 0


# ------------------------------------------------------------ 4. correlate_series

def _corr_bank(layout, device=None):
    rng = np.random.default_rng(9)
    counts = {"contiguous": [251] * 6 + [1151] * 6, "interleaved": [251, 1151] * 6}[layout]
    return TimeDomainFilterBank(_white_taps(rng, counts), counts, engine="corr", device=device)


def _corr_check(bank, ser, windows, ref_bank=None, tol=0.0, **kw):
    W = _normalize_windows(windows, ser.size)
    got = bank.correlate_series(ser, windows=windows, **kw)
    ref_bank = ref_bank or bank
    got = got.reshape(-1, ser.size)
    inside = np.zeros(ser.size, bool)
    for a, b in W:
        inside[a:b] = True
        single = ref_bank.correlate_series(ser, windows=slice(int(a), int(b)), **kw).reshape(-1, ser.size)
        diff = np.max(np.abs(got[:, a:b] - single[:, a:b])) if b > a else 0.0
        assert diff <= tol * max(1.0, float(np.abs(single).max()))
    assert not np.any(got[:, ~inside])
    return got


@pytest.mark.parametrize("layout", ["contiguous", "interleaved"])
def test_correlate_union_values_and_exact_zeros(layout):
    ser = _analytic(10)
    bank = _corr_bank(layout)
    for w in GEOMETRIES.values():
        got = _corr_check(bank, ser, w)
        assert np.count_nonzero(got) > 0
    _corr_check(bank, ser, GEOMETRIES["touching"], template_index=4)
    sc = np.linspace(0.5, 2.0, bank.n_templates).astype(np.float32)
    _corr_check(bank, ser, GEOMETRIES["edges"], scales=sc)


def test_correlate_overwrites_garbage_out():
    ser = _analytic(11)
    bank = _corr_bank("interleaved")
    out = np.full((bank.n_templates, S), 7 + 7j, np.complex64)
    ref = bank.correlate_series(ser, windows=GEOMETRIES["narrow"])
    got = bank.correlate_series(ser, windows=GEOMETRIES["narrow"], out=out)
    assert got is out
    np.testing.assert_array_equal(out, ref)
    out1 = np.full(S, 3 + 0j, np.complex64)
    bank.correlate_series(ser, windows=GEOMETRIES["narrow"], template_index=2, out=out1)
    np.testing.assert_array_equal(out1, ref[2])


@pytest.mark.parametrize("layout", ["contiguous", "interleaved"])
def test_correlate_on_gpu_including_stale_workspace(layout):
    gpu = _gpu()
    if gpu is None:
        pytest.skip("no usable GPU")
    ser = _analytic(12)
    cpu = _corr_bank(layout)
    gbank = _corr_bank(layout, device=gpu)
    for w in (GEOMETRIES["touching"], GEOMETRIES["narrow"], GEOMETRIES["edges"]):
        _corr_check(gbank, ser, w, ref_bank=cpu, tol=1e-5)    # second and third calls reuse the workspace


# ---------------------------------------------------------- 5. skipping is enforced

def _expected_filter_blocks(g, W):
    starts = set()
    for a, b in W:
        t, _, _ = TimeDomainFilterBank._window_layout(g, np.array([[a, b]], np.int64), S)
        starts.update(t.tolist())
    return starts


@pytest.mark.parametrize("engine", ["matchedfilter", "hier"])
def test_filter_series_computes_only_intersecting_blocks(engine, monkeypatch):
    bank = _bank(engine)
    g = bank._groups[0]
    seen = []
    plan_cls = type(g.plan)
    orig = plan_cls.run_series

    def spy(self, series, starts, *a, **k):
        seen.extend(np.asarray(starts).tolist())
        return orig(self, series, starts, *a, **k)

    monkeypatch.setattr(plan_cls, "run_series", spy)
    w = GEOMETRIES["narrow"]
    bank.filter_series(_analytic(13), windows=w)
    W = _normalize_windows(w, S)
    expected = _expected_filter_blocks(g, W)
    assert set(seen) == expected
    all_blocks = set(range(0, S, g.n_valid))
    assert len(expected) < len(all_blocks) // 2
    seen.clear()
    bank.filter_series(_analytic(13), windows=[])
    assert seen == []


@pytest.mark.parametrize("layout", ["contiguous", "interleaved"])
def test_correlate_series_computes_only_intersecting_blocks(layout, monkeypatch):
    from matchedfilter import _automatic_series_layout
    bank = _corr_bank(layout)
    calls = []
    orig = TimeDomainFilterBank._correlate_group

    def spy(self, g, ser, st, t0, nt, dest):
        calls.append((g.n, np.asarray(st).tolist()))
        return orig(self, g, ser, st, t0, nt, dest)

    monkeypatch.setattr(TimeDomainFilterBank, "_correlate_group", spy)
    w = GEOMETRIES["narrow"]
    W = _normalize_windows(w, S)
    bank.correlate_series(_analytic(14), windows=w)
    for g in bank._groups:
        cp = g.get_correlation_plan()
        lo, hi = cp.valid
        st, _, _ = _automatic_series_layout(S, cp.valid)
        want = [int(s) for s in st
                if any(int(s) + lo < b and min(int(s) + hi, S) > a for a, b in W)]
        got = [c[1] for c in calls if c[0] == g.n]
        assert got == [want] and 0 < len(want) < len(st) // 2
    calls.clear()
    assert not np.any(bank.correlate_series(_analytic(14), windows=[]))
    assert calls == []


# ---------------------------------------------------------------------- 6. cache

def test_layout_cache_reused_for_identical_windows(monkeypatch):
    bank = _bank("matchedfilter")
    count = {"n": 0}
    orig = TimeDomainFilterBank._window_layout

    def spy(g, W, S_):
        count["n"] += 1
        return orig(g, W, S_)

    monkeypatch.setattr(TimeDomainFilterBank, "_window_layout", staticmethod(spy))
    ser = _analytic(15)
    w = GEOMETRIES["touching"]
    bank.filter_series(ser, windows=w)
    first = count["n"]
    bank.filter_series(ser, windows=list(w))                 # same windows, new object
    assert count["n"] == first
    bank.filter_series(ser, windows=GEOMETRIES["edges"])
    assert count["n"] > first
