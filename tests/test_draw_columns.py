"""The planner holds a profile's draws once, column by column: a chain's detections are
views of the table's two halves, a screener retention holds its own band's column beside the
plain profile's, and a window adds a few indices to one shared array of distances. These
tests hold that what the planner reads is unchanged by it, and that it stays that small."""
import pathlib
from collections import OrderedDict

import numpy as np
import pytest

from matchedfilter import gatechain as gc

DATA = pathlib.Path(__file__).parent / "data"
N, SNR = 2048, 6.0
WINDOWS = [(192, 1856), (0, 2048), (256, 1792), (320, 1728)]


def _profile():
    return np.load(DATA / "reference_profile_o2_h1l1_2048.npy").astype(np.float64)


@pytest.fixture
def empty_model(monkeypatch):
    for c in ("_SIGNAL_CACHE", "_NOISE_CACHE", "_CAND_CACHE", "_CHOICE_CACHE", "_PLAN_CACHE",
              "_SIGNAL_RECORDS", "_NOISE_RECORDS", "_KEPT", "_LOCAL_WINDOWS"):
        monkeypatch.setattr(gc, c, OrderedDict())
    monkeypatch.setattr(gc, "_SIMILAR", {})
    monkeypatch.setattr(gc, "_SIMILAR_COUNT", {})


def _draws(p, bands, fd=1e-2, alphas=None, held=True):
    """The draws as the planner holds them (held), or written out as plain arrays."""
    kw = {} if alphas is None else {"alphas": alphas}
    read = gc._signal_table if held else gc.signal_draws
    return read(p, N, bands, SNR, gc.model_draws(fd)[0],
                window=gc.local_window(p, N, bands, WINDOWS[0]), lags_too=True, **kw)


def _held_bytes(cache):
    """Bytes of the distinct arrays a memo's values hold (views counted by their base)."""
    seen, total = set(), 0

    def walk(o):
        nonlocal total
        if isinstance(o, np.ndarray):
            b = o
            while isinstance(b.base, np.ndarray):
                b = b.base
            if id(b) not in seen:
                seen.add(id(b))
                total += b.nbytes
        elif isinstance(o, (tuple, list)):
            for x in o:
                walk(x)
    for _, value in cache.values():
        walk(value)
    return total


@pytest.mark.parametrize("chain", [(128,), (128, 256), (64, 256), (128, 256, 512), (64, 128, 512)])
def test_a_chains_columns_are_its_kept_draws_halves(empty_model, chain):
    """_kept_halves gives, as views, exactly what halving a copy of the chain's kept draws
    gives, for adjacent and for scattered columns."""
    p = _profile()
    bands = gc.usable_bands(p, N)
    sig, _ = _draws(p, bands)
    cols = [bands.index(b) for b in chain]
    A, B = gc._kept_halves(sig, bands, cols, chain, SNR)
    kept = gc.kept_draws(sig, bands, chain, SNR)
    assert A.shape == (kept[0::2].shape[0], len(chain)) and B.shape == (kept[1::2].shape[0], len(chain))
    for i in range(len(chain)):
        np.testing.assert_array_equal(A[:, i], kept[0::2, i])
        np.testing.assert_array_equal(B[:, i], kept[1::2, i])
        assert A.cols[i].flags.c_contiguous and A.cols[i].base is not None       # a view
        order = A.smallest(i, 50)
        np.testing.assert_array_equal(order, gc._smallest(kept[0::2, i], 50))
        assert A.smallest(i, 50) is order                                        # held
    th = np.linspace(3.0, 4.0, len(chain))
    np.testing.assert_allclose(B.score(th), (kept[1::2] - th).min(axis=1), rtol=0, atol=1e-6)


def test_a_retention_holds_its_own_band_beside_the_plain_draws(empty_model):
    """A retention alters one band. Held, its draws are the plain draws' arrays -- fine
    maxima, lags, every other band -- and one column of its own for that band, for the coarse
    maxima and for their lags; written out (signal_draws) they are the whole table, and what
    the planner reads of them is that table's."""
    p = _profile()
    bands = gc.usable_bands(p, N)
    (Cp, Fp), (fatp, catp) = _draws(p, bands)
    alphas = tuple(0.97 if b == 128 else 1.0 for b in bands)
    (C, F), (fat, cat) = _draws(p, bands, alphas=alphas)
    altered = bands.index(128)
    assert isinstance(C, gc._Beside) and isinstance(cat, gc._Beside)
    assert C.plain is Cp and cat.plain is catp and F is Fp and fat is fatp
    assert set(C.own) == {altered} == set(cat.own)
    assert C.own[altered].nbytes + cat.own[altered].nbytes < 0.3 * (Cp.nbytes + catp.nbytes)
    (Cw, Fw), (fatw, catw) = _draws(p, bands, alphas=alphas, held=False)
    assert isinstance(Cw, np.ndarray) and Cw.shape == Cp.shape
    for i in range(len(bands)):
        np.testing.assert_array_equal(Cw[:, i], C.column(i))
        np.testing.assert_array_equal(catw[:, i], cat.column(i))
        assert np.array_equal(Cw[:, i], Cp[:, i]) == (i != altered)
    np.testing.assert_array_equal(Fw[:, 0], Fp[:, 0])
    for chain in ((128, 256), (64, 128, 512), (256, 512)):
        cols = [bands.index(b) for b in chain]
        A, B = gc._kept_halves((C, F), bands, cols, chain, SNR)
        Ap, _ = gc._kept_halves((Cp, Fp), bands, cols, chain, SNR)
        ref = gc.kept_draws((Cw, Fw), bands, chain, SNR)
        for i, c in enumerate(cols):
            np.testing.assert_array_equal(A[:, i], ref[0::2, i])
            np.testing.assert_array_equal(B[:, i], ref[1::2, i])
            assert (A.cols[i].base is Ap.cols[i].base) == (c != altered)      # the plain half itself


def test_a_retentions_plans_are_those_of_its_own_table(empty_model, monkeypatch):
    """Sharing columns changes nothing a plan rests on: with the sharing switched off (a
    retention's draws held whole) every plan comes out the same."""
    p = _profile()

    def plans():
        out = []
        for window in WINDOWS[:2]:
            for chain in ((128, 256), (64, 128, 256), (128,)):
                for t0 in ((0.97, 1), (0.98, 1)):
                    pl = gc.chain_thresholds(p, N, SNR, 1e-2, chain, window=window, tier0_cluster=t0)
                    out.append((tuple(pl["thresholds"]), pl["halfwidth"], pl["cost"]))
        return out

    shared = plans()
    assert any(isinstance(v[0][0], gc._Beside) for v in gc._SIGNAL_CACHE.values())
    for c in ("_SIGNAL_CACHE", "_NOISE_CACHE", "_CAND_CACHE", "_PLAN_CACHE", "_SIGNAL_RECORDS",
              "_NOISE_RECORDS", "_KEPT"):
        getattr(gc, c).clear()
    gc._SIMILAR.clear()
    monkeypatch.setattr(gc, "_beside_plain", lambda hit, plain: hit)
    assert plans() == shared


@pytest.mark.parametrize("far", [False, True])
def test_distance_halves_are_the_distances_halved(empty_model, far):
    """_distance_halves' two halves, read out, are _distances' even and odd rows, with and
    without the searched window's far noise; and what they count and select beyond a
    half-width is what the array gives."""
    p = _profile()
    bands = gc.usable_bands(p, N)
    sig, lags = _draws(p, bands, fd=1e-3)
    noise = gc.noise_block_maxima(p, N, bands, nsim=gc.model_draws(1e-3)[1], window=WINDOWS[0]) if far else None
    for b in (256, 512):
        A, B = gc._distance_halves(sig, lags, bands, (b,), SNR, N, noise)
        whole = gc._distances(sig, lags, bands, (b,), SNR, N, noise)
        np.testing.assert_array_equal(A.values(), whole[0::2])
        np.testing.assert_array_equal(B.values(), whole[1::2])
        (C, F), (fat, cat) = sig, lags
        keep = F[:, 0] >= SNR
        plain = np.abs(fat[keep] - cat[keep, bands.index(b)]) / (N // b)
        if far:
            taken = noise[np.arange(plain.size) % noise.shape[0], bands.index(b)] > C[keep, bands.index(b)]
            assert taken.sum() > 0
            plain = np.where(taken, float(b), plain)
        np.testing.assert_array_equal(whole, plain)
        for h in (1, 2, 5):
            np.testing.assert_array_equal(A.beyond(h), np.flatnonzero(whole[0::2] > h))
            np.testing.assert_array_equal(B.mask_beyond(h), whole[1::2] > h)
            assert A.count_beyond(h) == int(np.count_nonzero(whole[0::2] > h))


def test_windows_and_chains_add_almost_nothing_to_what_is_held(empty_model):
    """Planning every chain of a profile for one window holds the table's halves, its
    distances and a few small arrays. Planning it for three more windows, and for a
    retention, adds far less than another table: a window's own is its noise maxima and a
    few indices, a retention's its band's column."""
    import json
    p = _profile()
    bands = gc.usable_bands(p, N)
    rec = json.loads((DATA / "cost_model_2048_zen5.json").read_text())
    cost = gc.CostModel.from_dict(rec["model"]).unscreened().with_direct(0.09 * 256 + 4.0)
    fd = 1e-3
    gc.choose_chain(p, N, SNR, fd, cost=cost, window=WINDOWS[0])
    (C, F), (fat, cat) = _draws(p, bands, fd=fd)
    table = C.nbytes + fat.nbytes + cat.nbytes
    held_tables = lambda: sum(  # noqa: E731  (what the draws' own cache holds)
        x.nbytes for (c, _), (_, at) in gc._SIGNAL_CACHE.values()
        for t in (c, at) for x in (t.own.values() if isinstance(t, gc._Beside) else [t]))
    tables_before = held_tables()
    one = _held_bytes(gc._KEPT)
    assert one < 2.5 * table
    for window in WINDOWS[1:]:
        gc.choose_chain(p, N, SNR, fd, cost=cost, window=window)
    assert _held_bytes(gc._KEPT) - one < 0.5 * table       # (a narrow band's far draws are many)
    before = _held_bytes(gc._KEPT)
    for window in WINDOWS:
        gc.choose_chain(p, N, SNR, fd, cost=cost, window=window, tier0_clusters={128: (0.97, 1)})
    assert _held_bytes(gc._KEPT) - before < 0.5 * table
    assert held_tables() - tables_before < 0.35 * table       # the retention's two columns
