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

import matchedfilter as mf
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


@pytest.mark.skipif(len(_core.targets()) < 2 if hasattr(_core, "targets") else True,
                    reason="one SIMD target in this build")
def test_every_isa_draws_the_same_integers():
    """The generators' integers are identical on every target; the float part (log, sincos)
    differs in the last ulp at most."""
    code = ("import sys, numpy as np; from matchedfilter import _core; "
            "o = np.empty(100000, np.float32); _core.gauss_fill(o, %d, 12345); "
            "np.save(sys.argv[1], o)" % SEED)
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


def _profile(n):
    p = np.exp(-np.arange(n) / (n / 7.0)) + 1e-4
    p[: n // 100] = 0
    return gc._norm_profile(p, n)


@pytest.fixture
def fresh(monkeypatch):
    from collections import OrderedDict
    for c in ("_NOISE_CACHE", "_NOISE_RECORDS", "_SIGNAL_CACHE"):
        monkeypatch.setattr(gc, c, OrderedDict())
    monkeypatch.setattr(gc, "_SIMILAR", {})
    monkeypatch.setattr(gc, "_STREAMS", {})


@pytest.mark.parametrize("order", [(20000,), (5000, 20000), (20000, 5000), (5000, 7000, 20000)])
def test_fewer_noise_blocks_are_a_prefix_of_more(fresh, order):
    """A noise simulation extended from a smaller one, or read as the prefix of a larger one,
    gives exactly the blocks a single full simulation gives (a provisional model's blocks are
    its full model's first)."""
    n = 2048
    p, bands, win = _profile(n), gc.candidate_bands(n), (128, 1920)
    got = {ns: gc.noise_block_maxima(p, n, bands, nsim=ns, window=win).copy() for ns in order}
    for c in (gc._NOISE_CACHE, gc._NOISE_RECORDS):
        c.clear()
    gc._SIMILAR.clear()
    full = gc.noise_block_maxima(p, n, bands, nsim=20000, window=win)
    for ns, v in got.items():
        np.testing.assert_array_equal(v, full[:ns], err_msg=str(ns))


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


def test_the_signal_stream_cache_changes_nothing(fresh, monkeypatch):
    """The signal simulation reads its stream's cached prefix (every reference reads it from
    the start): the draws equal those generated afresh, for a second profile too."""
    n = 2048
    p1, p2 = _profile(n), gc._norm_profile(np.exp(-np.arange(n) / 250.0) + 1e-4, n)
    bands = gc.usable_bands(p1, n)
    cached = [gc.signal_draws(p, n, bands, 6.0, 20000) for p in (p1, p2)]
    assert gc._STREAMS, "the stream was not cached"
    monkeypatch.setattr(gc, "_STREAM_MAX_BYTES", 0)       # nothing cached: generated on read
    gc._STREAMS.clear(); gc._SIGNAL_CACHE.clear(); gc._SIMILAR.clear()
    for p, (C, F) in zip((p1, p2), cached):
        C2, F2 = gc.signal_draws(p, n, bands, 6.0, 20000)
        np.testing.assert_array_equal(C, C2)
        np.testing.assert_array_equal(F, F2)
        gc._SIGNAL_CACHE.clear(); gc._SIMILAR.clear()


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


def test_provisional_models_keep_the_signal_and_quarter_the_noise():
    """Inside provisional(), only the noise blocks drop (to a quarter); the signal draws the
    budget rests on keep their count; outside, both are the full counts."""
    full = gc.model_draws(0.01)
    with gc.provisional():
        prov = gc.model_draws(0.01)
    assert prov[0] == full[0] and prov[1] == full[1] // gc._PROVISIONAL_FRACTION
    with gc.provisional(False):
        assert gc.model_draws(0.01) == full
    assert gc.model_draws(0.01) == full



def test_block_size_ranking_models_provisionally(fresh, monkeypatch):
    """price_block_sizes ranks sizes on a quarter of the noise blocks; the plans of a bank
    model with all of them (a plan's own chain choice is not inside provisional())."""
    from matchedfilter import _calibration as cal
    monkeypatch.setattr(gc, "_PRICE_CACHE", type(gc._PRICE_CACHE)())
    monkeypatch.setattr(gc, "_CHOICE_CACHE", type(gc._CHOICE_CACHE)())
    seen = []
    orig = gc._noise_records
    monkeypatch.setattr(gc, "_noise_records", lambda p, n, b, nsim, seed: seen.append(nsim) or orig(p, n, b, nsim, seed))
    fine = np.exp(-np.arange(4097) / 600.0); fine[:30] = 0
    cal.price_block_sizes(fine, 0.25, 2048.0, 300, 150, 64, 6.0, 0.01, [2048, 4096])
    assert seen and set(seen) == {20000 // gc._PROVISIONAL_FRACTION}, seen
