"""The gate model's random draws and the simulations that reuse them.

The simulations' standard normals come from one counter-based stream per simulation kind
(src/gauss.cc); every reference reads it from its start. These tests pin what the reuse
depends on: a draw depends only on its stream and position, whatever the ISA or how a read
is split; the draws are normal out to the tails the block maxima live in; a simulation of
fewer noise blocks is the start of one of more; and the signal simulation's cached stream
gives what generating it afresh gives.
"""
import math
import os
import subprocess
import sys

import numpy as np
import pytest

from matchedfilter import _core
from matchedfilter import gatechain as gc

SEED = (2 << 32) | 29


def _fill(n, offset, seed=SEED):
    out = np.empty(n, np.float32)
    _core.gauss_fill(out, seed, offset)
    return out


def test_a_draw_depends_only_on_its_position():
    """Any read of the stream -- unaligned, inside a 2048-draw block, across blocks, a single
    draw -- returns exactly the same span of one long read."""
    whole = _fill(300_000, 0)
    for off, n in ((0, 1), (1, 1), (3, 2048), (2047, 3), (2048, 2048), (1000, 70_000), (123_457, 99_999)):
        np.testing.assert_array_equal(_fill(n, off), whole[off:off + n], err_msg="offset %d n %d" % (off, n))


def test_streams_are_distinct():
    a, b = _fill(10_000, 0), _fill(10_000, 0, seed=SEED + 1)
    assert abs(float(np.corrcoef(a, b)[0, 1])) < 0.05


def test_the_draws_are_normal_into_the_tails():
    """Moments, lag correlations and the 3-4.5 sigma tail rates of 40M draws against the
    normal's, each within 4 standard errors."""
    x = _fill(40_000_000, 0).astype(np.float64)
    n = x.size
    assert abs(x.mean()) < 4 / math.sqrt(n)
    assert abs(x.var() - 1) < 4 * math.sqrt(2 / n)
    assert abs(((x - x.mean()) ** 4).mean() / x.var() ** 2 - 3) < 4 * math.sqrt(24 / n)
    for lag in (1, 2, 8, 16, 2048):
        assert abs(float(np.corrcoef(x[:-lag], x[lag:])[0, 1])) < 4 / math.sqrt(n), lag
    a = np.abs(x)
    for t in (3.0, 3.5, 4.0, 4.5):
        e = n * math.erfc(t / math.sqrt(2))
        assert abs((a > t).sum() - e) < 4 * math.sqrt(e), (t, (a > t).sum(), e)
    assert a.max() < 5.8                 # u1 >= 2^-24: at most 5.77 sigma


@pytest.mark.parametrize("offset, step, length, rows", [
    (0, 4096, 2048, 7),            # simulate's rows at n = 2048: one block each
    (0, 8192, 4096, 5),            # two blocks a row
    (0, 4096, 1024, 6),            # the start of each row's block
    (0, 4096, 1602, 7),            # n = 2048, kmax = 801 (a captured profile's): ends off a step
    (0, 8192, 3202, 5),            # n = 4096, kmax = 1601: a whole block, then one ending off a step
    (2048 * 3, 1024, 1000, 9),     # rows inside blocks, ends off the 16-draw steps
    (3072, 1024, 402, 9),          # n = 512, kmax = 201: two rows a block, ends off a step
    (17, 4096, 2048, 4),           # odd starts: every block read from inside
    (5, 300, 301, 11),             # rows overlapping in the stream
    (2 ** 40 + 4096, 4096, 2048, 3),
])
def test_rows_of_draws_are_spans_of_the_stream(offset, step, length, rows):
    """gauss_fill_rows (simulate's fill: rows in one call, blocks of different rows generated
    together, each pair of draws times its bin's scale) gives each row's span of one long read,
    times the scale, exactly."""
    span = (rows - 1) * step + length
    whole = _fill(span, offset)
    want = np.stack([whole[r * step:r * step + length] for r in range(rows)])
    got = np.full((rows, length), np.nan, np.float32)
    _core.gauss_fill_rows(got, SEED, offset, step)
    np.testing.assert_array_equal(got, want)
    scale = np.linspace(0.25, 3.0, (length + 1) // 2, dtype=np.float32)
    _core.gauss_fill_rows(got, SEED, offset, step, scale)
    np.testing.assert_array_equal(got, want * np.repeat(scale, 2)[:length])


@pytest.mark.skipif(len(_core.targets()) < 2 if hasattr(_core, "targets") else True,
                    reason="one SIMD target in this build")
def test_every_isa_draws_the_same_integers():
    """The generators' integers are identical on every target; the float part (log, sincos)
    differs in the last ulp at most. AVX2 and AVX-512 share that arithmetic (FMA, the same
    polynomials), so AVX-512's two blocks a 16-lane vector give bit for bit what AVX2's one
    block an 8-lane vector gives."""
    code = ("import sys, numpy as np; from matchedfilter import _core; "
            "o = np.empty(100000, np.float32); _core.gauss_fill(o, %d, 12345); "
            "w = np.empty((5, 2048), np.float32); _core.gauss_fill_rows(w, %d, 4096, 4096); "
            "np.save(sys.argv[1], np.concatenate([o, w.ravel()]))" % (SEED, SEED))
    got = {}
    for isa in _core.targets():
        path = os.path.join(os.environ.get("TMPDIR", "/tmp"), "gauss_%s_%d.npy" % (isa, os.getpid()))
        env = dict(os.environ, MF_ISA=isa)
        r = subprocess.run([sys.executable, "-c", code, path], env=env, capture_output=True, text=True)
        assert r.returncode == 0, (isa, r.stderr[-500:])
        got[isa] = np.load(path)
        os.unlink(path)
    ref = next(iter(got.values()))
    for isa, v in got.items():
        np.testing.assert_allclose(v, ref, rtol=0, atol=1e-6, err_msg=isa)
    if "AVX3" in got and "AVX2" in got:
        np.testing.assert_array_equal(got["AVX3"], got["AVX2"])


def _records_one_at_a_time(a, e0, step, L, d0):
    best, pos, val = -1.0, [], []
    for i in range(L):
        x = a[e0 + step * i]
        if x > best:
            best = x
            pos.append(i + d0)
            val.append(np.sqrt(np.float32(x)))
    return np.array(pos, np.int32), np.array(val, np.float32)


def test_the_records_are_those_of_a_scan_one_value_at_a_time():
    """simulate's running-maximum records (src/records.cc: 16 values at a time, every record of
    a block at once) are exactly a scan of one value at a time's, both ways, on white noise,
    on a rising run (every value a record), with ties, zeros and NaNs (never records), at any
    length; and arrays one entry too short report it."""
    rng = np.random.default_rng(3)
    smooth = np.convolve(rng.exponential(size=700), np.ones(40), "same")
    ties = np.round(rng.exponential(size=700) * 4) / 4
    rising = np.cumsum(rng.exponential(size=700))
    nan = rng.exponential(size=700)
    nan[rng.integers(0, 700, 60)] = np.nan
    zeros = np.where(rng.random(700) < 0.5, 0.0, rng.exponential(size=700))
    zeros[:20] = 0.0
    cases = [rng.exponential(size=700), smooth, ties, rising, nan, zeros, np.zeros(700)]
    for c, a in enumerate(cases):
        a = np.ascontiguousarray(a, np.float32)
        for L in (0, 1, 15, 16, 17, 31, 32, 33, 100, 511, 699):
            for e0, step, d0 in ((0, 1, 0), (3, 1, 5), (699, -1, 1), (L - 1, -1, 0)):
                if L == 0 or e0 < 0 or (step > 0 and e0 + L > a.size) or (step < 0 and e0 - L < -1):
                    continue
                pos, val = _records_one_at_a_time(a, e0, step, L, d0)
                gp, gv = np.empty(L + 1, np.int32), np.empty(L + 1, np.float32)
                k = _core.running_records(a, e0, step, L, d0, gp, gv)
                where = "case %d L %d e0 %d dir %d" % (c, L, e0, step)
                assert k == pos.size, where
                np.testing.assert_array_equal(gp[:k], pos, err_msg=where)
                np.testing.assert_array_equal(gv[:k].view(np.uint32), val.view(np.uint32), err_msg=where)
                if k:
                    short = k - 1
                    assert _core.running_records(a, e0, step, L, d0, gp[:short], gv[:short]) == -1, where


def _profile(n):
    p = np.exp(-np.arange(n) / (n / 7.0)) + 1e-4
    p[: n // 100] = 0
    return gc._norm_profile(p, n)


@pytest.fixture
def fresh(monkeypatch):
    from collections import OrderedDict
    for c in ("_NOISE_CACHE", "_NOISE_RECORDS", "_SIGNAL_CACHE", "_SIGNAL_RECORDS"):
        monkeypatch.setattr(gc, c, OrderedDict())
    monkeypatch.setattr(gc, "_SIMILAR", {})


@pytest.mark.parametrize("order", [(20000,), (5000, 20000), (20000, 5000), (5000, 7000, 20000)])
def test_fewer_noise_blocks_are_a_prefix_of_more(fresh, order):
    """A noise simulation extended from a smaller one, or read as the prefix of a larger one,
    gives exactly the blocks a single full simulation gives."""
    n = 2048
    p, bands, win = _profile(n), gc.candidate_bands(n), (128, 1920)
    got = {ns: gc.noise_block_maxima(p, n, bands, nsim=ns, window=win).copy() for ns in order}
    for c in (gc._NOISE_CACHE, gc._NOISE_RECORDS):
        c.clear()
    gc._SIMILAR.clear()
    full = gc.noise_block_maxima(p, n, bands, nsim=20000, window=win)
    for ns, v in got.items():
        np.testing.assert_array_equal(v, full[:ns], err_msg=str(ns))


def test_noise_maxima_do_not_depend_on_which_simulation_ran_first(fresh):
    """noise_block_maxima reads the blocks of the one simulation signal_draws also runs: the
    same numbers whether a signal simulation ran first (and recorded its noise) or not."""
    n = 2048
    p, bands, win = _profile(n), gc.candidate_bands(n), (128, 1920)
    alone = gc.noise_block_maxima(p, n, bands, nsim=6000, window=win).copy()
    for c in (gc._NOISE_CACHE, gc._NOISE_RECORDS, gc._SIGNAL_CACHE, gc._SIGNAL_RECORDS):
        c.clear()
    gc._SIMILAR.clear()
    gc.signal_draws(p, n, bands, 6.0, 4000, window=win)
    assert gc._NOISE_RECORDS, "the signal simulation recorded no noise"
    np.testing.assert_array_equal(alone, gc.noise_block_maxima(p, n, bands, nsim=6000, window=win))


def test_every_window_reads_one_noise_simulation(fresh):
    """Windows of one profile share its simulation's running-maximum records: one simulation,
    each window's maxima what a simulation of that window alone gives."""
    n = 2048
    p, bands = _profile(n), gc.candidate_bands(n)
    wins = [(128, 1920), (192, 1856), (64, 1984), None]
    shared = [gc.noise_block_maxima(p, n, bands, window=w).copy() for w in wins]
    assert len(gc._NOISE_RECORDS) == 1
    for w, v in zip(wins, shared):
        for c in (gc._NOISE_CACHE, gc._NOISE_RECORDS):
            c.clear()
        gc._SIMILAR.clear()
        np.testing.assert_array_equal(v, gc.noise_block_maxima(p, n, bands, window=w), err_msg=str(w))


@pytest.mark.parametrize("cut", [None, 801])
def test_the_noise_statistics_are_the_transforms_of_the_stream(fresh, cut):
    """Each band's noise statistic in the simulation (rows of the stream times the profile's
    scale, one block's draws shared by all of a row's transforms) is the b-point transform of
    the row's first b bins, |.|^2's running-maximum records as NumPy finds them in float64:
    also where the profile ends at bin 800 (the captured references' kmax = 801), the rows'
    draws ending inside a 16-draw step and the bins past them empty."""
    n, rows = 2048, 24
    p = _profile(n)
    if cut is not None:
        p = p.copy()
        p[cut:] = 0
        p = gc._norm_profile(p, n)
    bands = gc.usable_bands(p, n)
    recs = gc._noise_records(p, n, bands, rows, 13)
    scale = (np.sqrt(p) / np.sqrt(2)).astype(np.float32)
    kfill = min(int(np.flatnonzero(p)[-1]) + 1, bands[-1])
    for r in range(rows):
        d = _fill(2 * kfill, 2 * r * n, seed=(gc._DOMAIN_SIGNAL << 32) | 13) * np.repeat(scale[:kfill], 2)
        x = d[0::2].astype(np.float64) + 1j * d[1::2]
        for b, (pos, val, off) in zip(bands, recs):
            # bins past kfill empty: x zero-padded to the band's b
            a = np.abs(np.fft.ifft(x[:b], b) * b * (gc._SIG / np.sqrt(p[:b].sum()))) ** 2
            want = np.flatnonzero(a > np.maximum.accumulate(np.concatenate(([-1.0], a[:-1]))))
            got = slice(off[r], off[r + 1])
            np.testing.assert_array_equal(pos[got], want, err_msg="row %d band %d" % (r, b))
            np.testing.assert_allclose(val[got], np.sqrt(a[want]), rtol=2e-5, err_msg="row %d band %d" % (r, b))


def test_a_simulation_out_of_room_continues_where_it_stopped(fresh, monkeypatch):
    """A simulation whose records outgrow their arrays stops at the row that did not fit and
    continues from there (_simulate): with room for a fiftieth of the records a row it gives
    exactly the records of one call with room."""
    n = 2048
    p = _profile(n)
    bands = gc.usable_bands(p, n)
    Fb = [p[:b].sum() for b in bands]
    calls = []
    orig = _core.simulate
    monkeypatch.setattr(_core, "simulate", lambda *a: calls.append(a[3]) or orig(*a))
    t, u, sig = gc._signal_records(p, n, bands, Fb, 6.0, 3000, 13)
    noise = gc._NOISE_RECORDS[gc._key(p, n, bands, 13)][1]
    roomy = len(calls)
    for c in (gc._NOISE_RECORDS, gc._SIGNAL_RECORDS):
        c.clear()
    gc._SIMILAR.clear()
    monkeypatch.setattr(gc, "_ROOM", 0.02)
    t2, u2, sig2 = gc._signal_records(p, n, bands, Fb, 6.0, 3000, 13)
    noise2 = gc._NOISE_RECORDS[gc._key(p, n, bands, 13)][1]
    assert roomy == 1 and len(calls) - roomy >= 2, calls      # it did run out, and continued
    np.testing.assert_array_equal(t, t2)
    np.testing.assert_array_equal(u, u2)
    for a, b in zip(sig + noise, sig2 + noise2):
        for x, y in zip(a, b):
            np.testing.assert_array_equal(x, y)


def test_signal_draws_depend_only_on_their_seed(fresh):
    """The signal simulation is a function of the profile, window and seed: drawn afresh (no
    cache) it gives the same numbers, a second seed others, and a window moved by whole steps
    of the coarsest band is the same search."""
    n = 2048
    p = _profile(n)
    bands = gc.usable_bands(p, n)
    C, F = gc.signal_draws(p, n, bands, 6.0, 4000, window=(128, 1920))
    gc._SIGNAL_CACHE.clear(); gc._SIMILAR.clear()
    C2, F2 = gc.signal_draws(p, n, bands, 6.0, 4000, window=(128, 1920))
    np.testing.assert_array_equal(C, C2)
    np.testing.assert_array_equal(F, F2)
    step = n // bands[0]
    gc._SIGNAL_CACHE.clear(); gc._SIMILAR.clear()
    C3, _ = gc.signal_draws(p, n, bands, 6.0, 4000, window=(128 + step, 1920 + step))
    np.testing.assert_array_equal(C, C3)
    C4, _ = gc.signal_draws(p, n, bands, 6.0, 4000, seed=14, window=(128, 1920))
    assert not np.array_equal(C, C4)


def test_the_c_plan_search_matches_the_python_one(fresh, monkeypatch):
    """_chain_candidates' C search returns the Python recursion's candidates, in order."""
    n = 2048
    p = _profile(n)
    bands = gc.usable_bands(p, n)
    sig = gc.signal_draws(p, n, bands, 6.0, 20000)
    for win in ((128, 1920), None):
        noise = gc.noise_block_maxima(p, n, bands, window=win)
        for chain in gc.enumerate_chains(n, 3, bands=bands):
            for prune in (False, True):
                monkeypatch.setattr(gc, "_C_SEARCH", True)
                c = gc._chain_candidates(sig, noise, bands, chain, 0.01, 6.0, prune)
                monkeypatch.setattr(gc, "_C_SEARCH", False)
                py = gc._chain_candidates(sig, noise, bands, chain, 0.01, 6.0, prune)
                assert c == py, (chain, prune, win)


def test_block_size_ranking_models_with_every_draw(fresh, monkeypatch):
    """price_block_sizes models each size with the plans' own draw counts: the noise blocks are
    the signal simulation's first, so ranking on fewer would save nothing."""
    from matchedfilter import _calibration as cal
    monkeypatch.setattr(gc, "_PRICE_CACHE", type(gc._PRICE_CACHE)())
    monkeypatch.setattr(gc, "_CHOICE_CACHE", type(gc._CHOICE_CACHE)())
    seen = []
    orig = gc._noise_records
    monkeypatch.setattr(gc, "_noise_records", lambda p, n, b, nsim, seed: seen.append(nsim) or orig(p, n, b, nsim, seed))
    fine = np.exp(-np.arange(4097) / 600.0); fine[:30] = 0
    cal.price_block_sizes(fine, 0.25, 2048.0, 300, 150, 64, 6.0, 0.01, [2048, 4096])
    assert seen and set(seen) == {gc.model_draws(0.01)[1]}, seen
