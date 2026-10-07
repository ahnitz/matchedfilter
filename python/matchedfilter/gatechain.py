"""Gate chains: one model for every hierarchical configuration.

A configuration is a chain of coarse bands b1 < b2 < ... < bk followed by the
full refine. k = 1 is what used to be called a single-tier gate, k = 2 a
cascade; they are the same object here, enumerated, priced and chosen on equal
footing. Each tier runs on the previous tier's survivors.

Two questions decide a chain, and they are kept separate:

  ACCURACY  For a signal of strength `snr`, the thresholds g1..gk must dismiss
            at most `fd` of the pairs the full filter would keep. Taken from
            joint draws of every tier's coarse maximum and the fine maximum
            under signal (the same construction as gatemodel, generalised from
            two tiers to any set of bands; all candidate bands are drawn
            jointly, so every chain is evaluated on the same draws).

  COST      Expected cost per (block, template) pair:
                dense(b1) + sum_i P(reach tier i) sparse(b_i | density)
                          + P(reach refine) refine(density)
            The P's are noise-only pass probabilities of whole-block maxima,
            simulated exactly from the reference profile: the filter output
            noise in a block has independent bins with variance given by the
            profile, so a tier at band b sees the b-point inverse transform of
            the first b bins -- precisely its coarse lag grid. Tiers are nested
            and share their noise, so their passes are strongly correlated; the
            simulation carries that, which a product of marginal rates cannot.
            Per-tier costs are measured on the machine (tools/measure_chain_costs.py)
            as functions of survivor density, since pooled tiers and the refine
            amortise less when few pairs survive.

The budget is split between the tiers by minimising that cost subject to the
compound dismissal bound; the split is part of the chain's plan.
"""
import json
import math
import os
from collections import OrderedDict
from itertools import combinations

import numpy as np

from . import gatemodel as _gm

_SIG = _gm._SIG
_NB, _W = _gm._NB, _gm._W
_MIN_BAND = 64

#: Grid of per-tier budget shares searched when splitting fd across a chain.
_SPLIT = np.linspace(0.05, 0.95, 19)

_SIGNAL_CACHE = OrderedDict()
_NOISE_CACHE = OrderedDict()
_CACHE_MAX = 64


def candidate_bands(n, floor=_MIN_BAND):
    """Every band a tier can use at transform size n: powers of two in [floor, n/2]."""
    out, b = [], int(floor)
    while b <= n // 2:
        out.append(b)
        b *= 2
    return out


def usable_bands(power, n, floor=_MIN_BAND):
    """Candidate bands that hold some of the profile's power (a band with none cannot gate)."""
    p = np.asarray(power, dtype=np.float64)
    return [b for b in candidate_bands(n, floor) if p[:b].sum() > 0]


def enumerate_chains(n, max_tiers=3, floor=_MIN_BAND, bands=None):
    """All increasing band tuples of length 1..max_tiers."""
    bands = candidate_bands(n, floor) if bands is None else list(bands)
    out = []
    for k in range(1, int(max_tiers) + 1):
        out.extend(combinations(bands, k))
    return out


def _norm_profile(power, n):
    p = np.asarray(power, dtype=np.float64)
    if (p.shape != (n,) or not np.isfinite(p).all() or (p < 0).any() or p.sum() <= 0):
        raise ValueError("power must be a finite nonnegative length-n profile with positive sum")
    return p / p.sum()


def _key(p, n, bands, *rest):
    return (_gm._profile_sig(p), n, tuple(bands)) + tuple(rest)


def _cache_put(cache, key, value):
    cache[key] = value
    while len(cache) > _CACHE_MAX:
        cache.popitem(last=False)


_SIMILAR = {}           # (kind, n, bands, params) -> [(unit profile, value)]


def _similar_get(kind, p, params):
    u = (p / np.linalg.norm(p)).astype(np.float32)
    for v, val in _SIMILAR.get((kind,) + params, []):
        if float(np.dot(u, v)) >= 0.985:        # the reuse criterion gatemodel applies to its draws
            return u, val
    return u, None


def _similar_put(kind, u, params, value):
    lst = _SIMILAR.setdefault((kind,) + params, [])
    lst.append((u, value))
    del lst[:-_CACHE_MAX]


def signal_draws(power, n, bands, snr, nsamp, seed=13):
    """Coarse maxima at every band in `bands`, for draws whose fine maximum >= snr.

    Returns an (M, len(bands)) float32 array. Generalises gatemodel's
    single/cascade samplers: the in-band noise is split into independent
    segments between consecutive band edges, and tier b's noise is the
    normalised sum of the segments below it, so all tiers and the fine stage
    share their noise exactly as the filter does.
    """
    p = _norm_profile(power, n)
    bands = sorted(int(b) for b in bands)
    key = _key(p, n, bands, float(snr), int(nsamp), int(seed))
    hit = _SIGNAL_CACHE.get(key)
    if hit is not None:
        _SIGNAL_CACHE.move_to_end(key)
        return hit
    sim_params = (n, tuple(bands), float(snr), int(nsamp), int(seed))
    unit, hit = _similar_get("signal", p, sim_params)
    if hit is not None:
        return hit
    F = np.array([p[:b].sum() for b in bands])
    if F[0] <= 0:
        return None          # a band holding no power cannot gate; callers drop such bands (usable_bands)
    edges = [0] + bands + [n]
    # Unnormalised correlation of each segment: S_j(d) = sum_{k in seg j} p_k e^{2 i pi k d / n}.
    seg_corr, seg_frac = [], []
    for j in range(len(edges) - 1):
        q = np.zeros(n); q[edges[j]:edges[j + 1]] = p[edges[j]:edges[j + 1]]
        fr = float(q.sum())
        seg_frac.append(fr)
        seg_corr.append(np.fft.ifft(q) * n if fr > 1e-12 else None)
    band_corr = []           # normalised in-band correlation A_b(d)
    for b, fb in zip(bands, F):
        q = np.zeros(n); q[:b] = p[:b] / fb
        band_corr.append(np.fft.ifft(q) * n)
    full_corr = np.fft.ifft(p) * n
    look = lambda tab, d: tab[np.asarray(d) % n]

    steps = [n // b for b in bands]
    step0 = steps[0]
    rng = np.random.default_rng(seed)
    m = max(nsamp // step0, 256)
    C_out, F_out = [], []
    for off in range(step0):
        fl = np.arange(-_W, _W + 1) + off
        grids = [(off // s) * s + np.arange(-_NB, _NB + 1) * s for s in steps]
        taus = np.unique(np.concatenate([fl] + grids))
        gidx = [np.searchsorted(taus, gr) for gr in grids]
        lag = taus[:, None] - taus[None, :]
        eye = 1e-9 * np.eye(len(taus))
        seg_noise = []
        for S, fr in zip(seg_corr, seg_frac):
            if S is None:
                seg_noise.append(None); continue
            C = look(S, lag) / fr
            C = (C + C.conj().T) / 2 + eye
            L = np.linalg.cholesky(C).astype(np.complex64)
            w = (rng.standard_normal((m, len(taus)), dtype=np.float32)
                 + 1j * rng.standard_normal((m, len(taus)), dtype=np.float32)) / np.float32(np.sqrt(2))
            seg_noise.append((w @ L.T) * np.float32(_SIG * np.sqrt(fr)))      # unnormalised: variance fr
        cols = []
        for i, b in enumerate(bands):
            # tier i's noise is the sum of the segments below its band edge, j = 0..i
            acc_b = sum(sn for sn in seg_noise[:i + 1] if sn is not None)
            nb = acc_b / np.float32(np.sqrt(F[i]))
            z = np.float32(snr * np.sqrt(F[i])) * look(band_corr[i], taus - off).astype(np.complex64)[None, :] + nb
            cols.append(np.abs(z)[:, gidx[i]].max(1))
        nfull = sum(sn for sn in seg_noise if sn is not None)
        zf = np.float32(snr) * look(full_corr, taus - off).astype(np.complex64)[None, :] + nfull
        F_out.append(np.abs(zf).max(1))
        C_out.append(np.stack(cols, 1))
    C_all = np.concatenate(C_out); F_all = np.concatenate(F_out)
    kept = C_all[F_all >= snr].astype(np.float32)
    _cache_put(_SIGNAL_CACHE, key, kept)
    _similar_put("signal", unit, sim_params, kept)
    return kept


def noise_block_maxima(power, n, bands, nsim=20000, seed=29, chunk=2000, window=None):
    """Noise-only block maxima of every band's coarse statistic, (nsim, len(bands)).

    Exact for stationary Gaussian noise with output profile `power`: bins are
    independent with variance p_k; band b's coarse grid is the b-point inverse
    transform of bins [0, b), normalised to unit per-component variance.
    `window` = (start, end) in samples is the lag range each block's search
    covers; every tier takes its maximum over the coarse lags the engine
    visits for it (hmf.c: cstart = start/R - 1, cend = ceil(end/R)), so a
    chain's noise passes are joint passes of whole-window maxima.
    """
    p = _norm_profile(power, n)
    bands = sorted(int(b) for b in bands)
    win = (0, n) if window is None else (int(window[0]), int(window[1]))
    key = _key(p, n, bands, int(nsim), int(seed), win)
    hit = _NOISE_CACHE.get(key)
    if hit is not None:
        _NOISE_CACHE.move_to_end(key)
        return hit
    sim_params = (n, tuple(bands), int(nsim), int(seed), win)
    unit, hit = _similar_get("noise", p, sim_params)
    if hit is not None:
        return hit
    bmax = bands[-1]
    sd = np.sqrt(p[:bmax]).astype(np.float32)
    F = np.array([p[:b].sum() for b in bands])
    rng = np.random.default_rng(seed)
    out = np.empty((nsim, len(bands)), np.float32)
    for s in range(0, nsim, chunk):
        m = min(chunk, nsim - s)
        X = ((rng.standard_normal((m, bmax), dtype=np.float32)
              + 1j * rng.standard_normal((m, bmax), dtype=np.float32)) / np.float32(np.sqrt(2))) * sd
        for i, b in enumerate(bands):
            R = n // b
            c0 = max(win[0] // R - 1, 0) if win[0] > 0 else 0
            c1 = min(-(-win[1] // R), b)
            z = np.fft.ifft(X[:, :b], axis=1) * np.float32(b)
            out[s:s + m, i] = np.abs(z[:, c0:c1]).max(1) * np.float32(_SIG / np.sqrt(F[i]))
    _cache_put(_NOISE_CACHE, key, out)
    _similar_put("noise", unit, sim_params, out)
    return out


class CostModel:
    """Measured per-tier costs for one transform size (see tools/measure_chain_costs.py)."""

    def __init__(self, table):
        self.n = int(table["n"])
        self.dense = {int(b): float(v) for b, v in table["dense"].items()}
        self._refine = sorted((float(f), float(v)) for f, v in table["refine"].items())
        self._sparse = {int(b): sorted((float(f), float(v)) for f, v in d.items())
                        for b, d in table["sparse"].items()}

    @staticmethod
    def _interp(rows, f):
        """Cost per survivor at density f: linear in log f, clamped to the measured range."""
        fs = np.log([r[0] for r in rows]); vs = [r[1] for r in rows]
        return float(np.interp(math.log(max(f, 1e-12)), fs, vs))

    def refine(self, f):
        return self._interp(self._refine, f)

    def sparse(self, b, f):
        return self._interp(self._sparse[int(b)], f)

    def chain_cost(self, chain, reach):
        """reach[i] = P(a pair reaches tier i+1) for i = 0..k-1, reach[k] = P(reaches refine)."""
        c = self.dense[int(chain[0])]
        for i in range(1, len(chain)):
            c += reach[i] * self.sparse(chain[i], reach[i])
        c += reach[len(chain)] * self.refine(reach[len(chain)])
        return c

    @classmethod
    def load(cls, path=None, n=None):
        path = path or os.environ.get("MF_CHAIN_COSTS")
        if not path:
            return None
        with open(path) as fh:
            data = json.load(fh)
        tables = data if isinstance(data, list) else [data]
        for t in tables:
            if n is None or int(t["n"]) == int(n):
                return cls(t)
        return None


def _reach(N, cols, thresholds):
    """Cumulative noise pass probabilities through the chain."""
    alive = np.ones(N.shape[0], bool)
    out = [1.0]
    for c, g in zip(cols, thresholds):
        alive &= N[:, c] >= g
        out.append(float(alive.mean()))
    return out


def plan_chain(sig, noise, bands, chain, fd, cost, n):
    """Thresholds for `chain` meeting compound dismissal <= fd at minimum modelled cost.

    sig, noise: signal_draws / noise_block_maxima over `bands`.
    Returns dict(chain, thresholds, reach, cost) or None when fd cannot be resolved.
    """
    cols = [bands.index(b) for b in chain]
    M = sig.shape[0]
    K = int(math.floor(float(fd) * M))       # the single-tier contract of gatemodel.gate_for
    if K < 8:
        return None
    S = sig[:, cols]
    k = len(chain)
    best = None

    def finish(prefix):
        """Given thresholds for tiers 0..k-2, set the last to use the remaining budget."""
        alive = np.ones(M, bool)
        for i, g in enumerate(prefix):
            alive &= S[:, i] >= g
        used = M - int(alive.sum())
        rem = K - used
        if rem < 0:
            return None
        last = np.sort(S[alive, k - 1])
        if rem >= len(last):
            return None
        return list(prefix) + [float(last[rem])]

    if k == 1:
        cands = [finish([])]
    else:
        # Each earlier tier spends a share of the budget on its own marginal; the last fills the rest.
        sorted_cols = [np.sort(S[:, i]) for i in range(k - 1)]
        cands = []
        def rec(i, prefix, remaining):
            # tier i takes a share of the budget still unallocated; the last tier gets what is left
            if i == k - 1:
                cands.append(finish(prefix)); return
            for a in _SPLIT:
                share = a * remaining
                idx = int(math.floor(share * K))
                if idx < 1:
                    continue
                rec(i + 1, prefix + [float(sorted_cols[i][idx])], remaining - share)
        rec(0, [], 1.0)
    for th in cands:
        if th is None:
            continue
        reach = _reach(noise, cols, th)
        c = cost.chain_cost(chain, reach) if cost is not None else _flop_cost(chain, reach, n)
        if best is None or c < best["cost"]:
            best = dict(chain=tuple(chain), thresholds=tuple(th), reach=tuple(reach), cost=float(c))
    return best


def _flop_cost(chain, reach, n):
    """Fallback when no measured table exists: transform-size proxy b log b per tier, n log n per refine."""
    c = chain[0] * math.log2(chain[0])
    for i in range(1, len(chain)):
        c += reach[i] * chain[i] * math.log2(chain[i])
    return c + reach[len(chain)] * n * math.log2(n)


def choose_chain(power, n, snr, fd, cost=None, max_tiers=3, floor=_MIN_BAND, nsim=20000, window=None):
    """Price every chain and return (best, all_plans sorted by cost)."""
    bands = usable_bands(power, n, floor)
    if not bands:
        return None, []
    sig = signal_draws(power, n, bands, snr, _gm._nsamp_for(fd))
    if sig is None or not len(sig):
        return None, []
    noise = noise_block_maxima(power, n, bands, nsim=nsim, window=window)
    plans = []
    for chain in enumerate_chains(n, max_tiers, floor, bands=bands):
        pl = plan_chain(sig, noise, bands, list(chain), fd, cost, n)
        if pl is not None:
            plans.append(pl)
    plans.sort(key=lambda d: d["cost"])
    return (plans[0] if plans else None), plans


def chain_thresholds(power, n, snr, fd, chain, cost=None, floor=_MIN_BAND, nsim=20000, window=None):
    """Thresholds (and modelled reach/cost) for one given chain under `power`."""
    bands = usable_bands(power, n, floor)
    if not set(chain) <= set(bands):
        return None
    sig = signal_draws(power, n, bands, snr, _gm._nsamp_for(fd))
    if sig is None or not len(sig):
        return None
    noise = noise_block_maxima(power, n, bands, nsim=nsim, window=window)
    return plan_chain(sig, noise, bands, list(chain), fd, cost, n)


_COSTS = {}


def cost_model(n):
    """The measured cost table for n from $MF_CHAIN_COSTS, or None (then chains are not used)."""
    path = os.environ.get("MF_CHAIN_COSTS")
    if not path:
        return None
    key = (path, int(n))
    if key not in _COSTS:
        try:
            _COSTS[key] = CostModel.load(path, n)
        except (OSError, ValueError, KeyError):
            _COSTS[key] = None
    return _COSTS[key]
