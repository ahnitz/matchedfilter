"""The planner's signal table drawn from the joint law of the few numbers it holds.

The gate model's simulation (_gatedraws._simulate) makes a block of noise bins, adds a signal
and transforms it for the fine statistic and for each band; the planner then keeps, per
draw, the largest fine statistic and each band's largest coarse statistic in a window around
the signal, and where they lie. Those are functions of a few samples next to the signal, and
the samples' joint law is known in closed form:

* a band's statistic is the fine statistic's own bins restricted to the band, so every fine
  and coarse sample is one linear function of the same independent Gaussian bins;
* the covariance of two samples is the sum over the bins they share of
  ``p_k exp(2 pi i k (x_i - x_j) / n)``, x their block lags, over the two statistics'
  norms; the signal's mean is the same sum against its arrival, times its strength;
* a coarse sample far from the signal is noise alone, and the largest of N independent
  noise moduli has the distribution ``(1 - exp(-x^2 / 2))^N``.

So a draw here is the fine samples at the lags around the arrival and each band's nearest
coarse samples, drawn from that joint Gaussian, with the coarse samples further away
replaced by the largest of as many independent noise samples. Chains of bands, a band's
retention under a shared screener and the lags of the maxima are all read from the one
vector: nothing is drawn again for them.

The simulation remains the reference this is tested against (tests/test_signal_law.py) and
the planner's fallback.
"""
import hashlib
from collections import OrderedDict

import numpy as np

from . import _core

#: Fine lags drawn on each side of the arrival, and coarse lags of a band drawn around it.
#: Fewer fine lags than a band's drawn coarse lags span puts the two maxima too far apart
#: (the half-width table); more of either changes nothing.
_FINE_REACH = 8
_NEAR = 8
#: Draws a pass makes at once.
_CHUNK = 1 << 16
_DOMAIN_LAW = 7
#: The draws held for the profiles being planned: a retention's table is read from its
#: profile's draws, not drawn again. About 29 MB a profile at 96,000 draws and a block of
#: 1024. Three: a job's banks alternate between the top templates they hang under, and two
#: top templates' banks under two detectors plan on three profiles that are not alike
#: (_gatedraws._law_profile); holding two, every other bank drew its profile again.
_DRAWS = OrderedDict()
_DRAWS_MAX = 3


def _stream(seed):
    """The generator stream the law draws its normals from for `seed` (apart from the
    simulation's, which uses the seed itself)."""
    return (int(seed) * 2654435761 + _DOMAIN_LAW) % (1 << 63)


def _sums(q, n):
    """``g[d] = sum_k q_k exp(2 pi i k d / n)`` for every integer d (mod n)."""
    return np.fft.ifft(q) * n


def signal_table(p, n, bands, slices, snr, ndet, seed, lags, alphas=None, nf=16):
    """Draws of the fine and coarse window maxima under a signal of strength ``snr``.

    Parameters
    ----------
    p : numpy.ndarray
        The profile, ``(n,)``, of unit sum.
    n : int
        The block length.
    bands : sequence of int
        The bands, ascending.
    slices : sequence of (int, int)
        Each band's bin range ``[lo, hi)``.
    snr : float
        The signal's strength; a draw is kept when its fine maximum reaches it.
    ndet : int
        The number of kept draws to return.
    seed : int
        The draws' seed.
    lags : tuple
        ``(w0, w1, c0, c1)``: the fine window and each band's coarse lags
        (_gatedraws._engine_lags).
    alphas : sequence of float, optional
        Each band's retention; a band with one below 1 keeps that share of the signal and
        of the noise it has in common with the other statistics.
    nf : int, optional
        The fractions of a sample the arrival takes.

    Returns
    -------
    C : numpy.ndarray
        ``(ndet, bands)`` float32, each band's largest coarse statistic.
    F : numpy.ndarray
        ``(ndet,)`` float32, the largest fine statistic.
    at : tuple of numpy.ndarray
        ``(fine_at, coarse_at)``: the block lags of the maxima, ``(ndet,)`` and
        ``(ndet, bands)`` int32 (a coarse lag times its band's step).
    """
    p = np.asarray(p, np.float64)
    key = (hashlib.blake2b(p.tobytes(), digest_size=16).digest(), int(n), tuple(bands),
           tuple(map(tuple, slices)), float(snr), int(ndet), int(seed),
           (int(lags[0]), int(lags[1]), tuple(map(int, lags[2])), tuple(map(int, lags[3]))), int(nf))
    draws = _DRAWS.get(key)
    if draws is None:
        draws = _DRAWS[key] = _draw(p, n, bands, slices, snr, ndet, seed, lags, nf)
        while len(_DRAWS) > _DRAWS_MAX:
            _DRAWS.popitem(last=False)
    else:
        _DRAWS.move_to_end(key)
    nb = len(bands)
    if "plain" not in draws:
        C = np.empty((draws["F"].size, nb), np.float32)
        cat = np.empty((draws["F"].size, nb), np.int32)
        for i in range(nb):
            C[:, i], cat[:, i] = _column(draws, i, n, seed)
        draws["plain"] = (C, cat)
    C, cat = draws["plain"]
    altered = [i for i in range(nb) if alphas is not None and float(alphas[i]) < 1.0]
    if altered:
        # a retention's table: the plain one with its altered bands' columns read again
        C, cat = C.copy(), cat.copy()
        for i in altered:
            C[:, i], cat[:, i] = _column(draws, i, n, seed, float(alphas[i]))
    F, fat = draws["F"], draws["fat"] % n if draws["whole"] else draws["fat"]
    for x in (C, F, fat, cat):
        x.setflags(write=False)
    return C, F, (fat, cat)


def _draw(p, n, bands, slices, snr, ndet, seed, lags, nf):
    """The draws a profile's tables are read from (signal_table): per kept draw the fine
    maximum and its lag, and per band its drawn samples, their lags, and its undrawn lags'
    largest noise."""
    nb = len(bands)
    w0, w1, c0, c1 = lags
    span = w1 - w0
    steps = [n // b for b in bands]
    step = max(steps)
    sets = [(0, n)] + [tuple(s) for s in slices]         # the statistics' bins: fine, then each band
    norm = [1.0] + [np.sqrt(p[lo:hi].sum()) for lo, hi in slices]
    k = np.arange(n)

    def band_sums(lo, hi, frac=0.0):
        q = np.zeros(n, complex)
        q[lo:hi] = p[lo:hi] * np.exp(-2j * np.pi * k[lo:hi] * frac / n)
        return _sums(q, n)

    # covariance of two statistics' samples by lag difference, and each statistic's response
    # to a signal arriving f / nf of a sample after a lag
    cov = {(a, b): band_sums(max(sa[0], sb[0]), min(sa[1], sb[1])) / (norm[a] * norm[b])
           for a, sa in enumerate(sets) for b, sb in enumerate(sets)}
    resp = np.array([[band_sums(lo, hi, f / nf) / norm[a] for a, (lo, hi) in enumerate(sets)]
                     for f in range(nf)])

    # per arrival class t (its lag against the coarsest grid): the samples drawn, the factor
    # of their covariance and the mean per fraction; a retention's own noise by its band
    classes = []
    for t in range(step):
        kind, pos, cols = [0] * (2 * _FINE_REACH), list(range(t - _FINE_REACH + 1, t + _FINE_REACH + 1)), []
        for i, r in enumerate(steps):
            count = int(c1[i] - c0[i])
            # a band of few lags is drawn whole (every lag the window can hold on either
            # side of the arrival): its samples are too alike to stand in as independent noise
            near = 2 * count if count <= _NEAR else _NEAR
            first = t // r - near // 2 + 1
            cols.append((len(kind), near, count))
            kind += [1 + i] * near
            pos += [j * r for j in range(first, first + near)]
        kind, pos = np.array(kind), np.array(pos)
        size = kind.size
        s = np.empty((size, size), complex)
        for a in range(len(sets)):
            ia = np.flatnonzero(kind == a)
            for b in range(len(sets)):
                ib = np.flatnonzero(kind == b)
                s[np.ix_(ia, ib)] = cov[a, b][(pos[ia][:, None] - pos[ib][None, :]) % n]
        factor = np.linalg.cholesky(s + 1e-7 * np.eye(size)).T.astype(np.complex64)
        mean = (snr * resp[:, kind, (pos - t) % n]).astype(np.complex64)
        if t == 0:
            # a band's own noise (a retention mixes it in): its samples' covariance, which
            # is the same whatever the arrival's class
            own = [np.linalg.cholesky(s[c:c + near, c:c + near] + 1e-7 * np.eye(near)).T.astype(np.complex64)
                   for c, near, _ in cols]
        classes.append((pos, cols, np.ascontiguousarray(factor), mean))

    whole = span >= n
    cols = classes[0][1]
    # per pass and class: (F, fine lag, top, spot, samples, inside, first lag, class)
    kept = []
    have, part = 0, 0
    while have < ndet:
        rng = np.random.default_rng([int(seed), _DOMAIN_LAW, part])
        m = _CHUNK
        t = rng.integers(0, step, m)
        # where the signal lies in the window: on its class's lag, a whole number of steps in
        a = (t - w0) % step + rng.integers(0, -(-span // step), m) * step
        ok = a < span
        for tc in range(step):
            rows = np.flatnonzero(ok & (t == tc))
            if not rows.size:
                continue
            pos, cols, factor, mean = classes[tc]
            size = pos.size
            # unit normals from the library's generator (a stream position per pass and class)
            g = np.empty(rows.size * 2 * size, np.float32)
            _core.gauss_fill(g, _stream(seed), (part * step + tc) << 32)
            x = g.view(np.complex64).reshape(rows.size, size) @ factor + mean[rows % nf]
            fine_lag = (w0 + a[rows] - tc)[:, None] + pos[None, :2 * _FINE_REACH]
            fine = np.abs(x[:, :2 * _FINE_REACH])
            if not whole:
                # the engine does not search outside the window
                fine[(fine_lag < w0) | (fine_lag >= w1)] = -1.0
            best = fine.argmax(axis=1)
            F = fine[np.arange(rows.size), best]
            keep = np.flatnonzero(F >= snr)
            if not keep.size:
                continue
            base = (w0 + a[rows[keep]] - tc)[:, None]
            xs, ins = [], []
            top, spot = np.empty((keep.size, nb), np.float32), np.empty((keep.size, nb), np.int32)
            for i, (c, near, count) in enumerate(cols):
                lag = (base + pos[None, c:c + near]).astype(np.int32)
                if whole:
                    inside = np.ones(lag.shape, bool)
                else:
                    j = lag // steps[i]
                    inside = (j >= c0[i]) & (j < c1[i])
                xs.append(np.where(inside, x[keep, c:c + near], 0))
                ins.append(inside)
                # the band's lags that were not drawn: the largest of that many independent
                # noise samples, at one of the band's lags
                others = np.maximum(count - inside.sum(axis=1), 0)
                u = rng.random(keep.size)
                spot[:, i] = (c0[i] + rng.integers(0, int(c1[i] - c0[i]), keep.size)) * steps[i]
                far = np.sqrt(-2.0 * np.log1p(-np.minimum(u ** (1.0 / np.maximum(others, 1)), 1.0 - 1e-12)))
                top[:, i] = np.where(others > 0, far, -1.0)
            kept.append((F[keep], fine_lag[keep, best[keep]].astype(np.int32), top, spot, xs, ins,
                         base[:, 0].astype(np.int32), np.full(keep.size, tc, np.int16)))
            have += keep.size
        part += 1
    # the draws in an order that does not follow the classes (the last pass is cut short)
    order = np.random.default_rng([int(seed), _DOMAIN_LAW, 1 << 30]).permutation(have)[:ndet]
    rows_of = lambda j: np.concatenate([q[j] for q in kept])[order]
    band_of = lambda j, i: np.concatenate([q[j][i] for q in kept])[order]
    # a sample's block lag is its draw's first lag plus the sample's place in its class
    places = [np.array([pos[c:c + near] for pos, _, _, _ in classes]) for c, near, _ in cols]
    return dict(F=rows_of(0), fat=rows_of(1), top=rows_of(2), spot=rows_of(3),
                x=[band_of(4, i) for i in range(nb)], inside=[band_of(5, i) for i in range(nb)],
                first=rows_of(6), cls=rows_of(7), places=places, own=own, whole=whole)


def _column(draws, i, n, seed, alpha=1.0):
    """Band i's largest coarse statistic and its block lag in every draw, under a retention
    ``alpha``: the band's samples keep that share of what they are and take the rest from
    noise of their own (the band's stream: every retention of the band mixes in the same)."""
    x = draws["x"][i]
    if alpha < 1.0:
        g = np.empty(2 * x.size, np.float32)
        _core.gauss_fill(g, _stream(seed), (1 << 56) + (i << 48))
        x = np.float32(alpha) * x + np.float32(np.sqrt(1.0 - alpha * alpha)) * (
            g.view(np.complex64).reshape(x.shape) @ draws["own"][i])
    mod = np.where(draws["inside"][i], np.abs(x), np.float32(-1.0))
    best = mod.argmax(axis=1)
    val = mod[np.arange(mod.shape[0]), best]
    where = draws["first"] + draws["places"][i][draws["cls"], best]
    top = draws["top"][:, i]
    where = np.where(top > val, draws["spot"][:, i], where)
    val = np.maximum(val, top)
    return val.astype(np.float32), (where % n if draws["whole"] else where).astype(np.int32)
