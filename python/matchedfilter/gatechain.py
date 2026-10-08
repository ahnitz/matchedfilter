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
            Per-tier costs are measured on the machine the job runs on, through
            the engine itself (calibrate_costs), as functions of survivor
            density: pooled tiers and the refine amortise less when few pairs
            survive. Nothing is tabulated; the numbers belong to this process.

The model does not have to be exact. Its job is to keep the cheapest chain on a
short list; the autotuner measures the short list on the real workload.

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

#: Grid of per-tier budget shares searched when splitting fd across a chain. Chains of three or
#: more tiers search a product of these grids, so they use the coarser one.
_SPLIT = np.linspace(0.05, 0.95, 19)
_SPLIT_COARSE = np.linspace(0.05, 0.95, 9)

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
    """Joint draws of every band's coarse maximum and local fine maximum under a signal of strength snr.

    Returns (C, F), both (M, len(bands)) float32: C[:, i] is band i's coarse
    maximum over its own lag grid, F[:, i] the fine maximum over the fine lags
    and that grid -- the neighbourhood gatemodel's single-band construction
    uses. A chain conditions on the maximum of F over its own bands (its
    tiers' grids plus the fine lags), which for one band is exactly the
    single-tier model and for two the cascade model. Generalises those
    samplers: the in-band noise is split into independent segments between
    consecutive band edges, and tier b's noise is the normalised sum of the
    segments below it, so all tiers and the fine stage share their noise
    exactly as the filter does.
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
        nfull = sum(sn for sn in seg_noise if sn is not None)
        afull = np.abs(np.float32(snr) * look(full_corr, taus - off).astype(np.complex64)[None, :] + nfull)
        fidx = np.searchsorted(taus, fl)
        ffine = afull[:, fidx].max(1)
        cols, fcols = [], []
        for i, b in enumerate(bands):
            # tier i's noise is the sum of the segments below its band edge, j = 0..i
            acc_b = sum(sn for sn in seg_noise[:i + 1] if sn is not None)
            nb = acc_b / np.float32(np.sqrt(F[i]))
            z = np.float32(snr * np.sqrt(F[i])) * look(band_corr[i], taus - off).astype(np.complex64)[None, :] + nb
            cols.append(np.abs(z)[:, gidx[i]].max(1))
            # the coarse lags are a subset of the fine grid, so they count toward the fine maximum
            fcols.append(np.maximum(ffine, afull[:, gidx[i]].max(1)))
        C_out.append(np.stack(cols, 1))
        F_out.append(np.stack(fcols, 1))
    out = (np.concatenate(C_out).astype(np.float32), np.concatenate(F_out).astype(np.float32))
    _cache_put(_SIGNAL_CACHE, key, out)
    _similar_put("signal", unit, sim_params, out)
    return out


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
    """Per-tier costs for one transform size, in engine ticks.

    dense[b]          first tier at band b, per pair
    sparse[b]         [(density, ticks per survivor)] for a later tier at band b
    refine            [(density, ticks per refined pair)]
    """

    def __init__(self, n, dense, sparse, refine, block=0.0):
        self.n = int(n)
        self.block = float(block)          # fixed work per block: forward transform, ingest
        self.dense = {int(b): float(v) for b, v in dense.items()}
        self._sparse = {int(b): sorted((float(f), float(v)) for f, v in rows) for b, rows in sparse.items()}
        self._refine = sorted((float(f), float(v)) for f, v in refine)

    @staticmethod
    def _interp(rows, f):
        """Cost per survivor at density f: linear in log f, clamped to the measured range."""
        fs = np.log([r[0] for r in rows]); vs = [r[1] for r in rows]
        return float(np.interp(math.log(max(f, 1e-12)), fs, vs))

    def refine(self, f):
        return self._interp(self._refine, f)

    def sparse(self, b, f):
        return self._interp(self._sparse[int(b)], f)

    def to_dict(self):
        return {"n": self.n, "block": self.block, "dense": self.dense,
                "sparse": self._sparse, "refine": self._refine}

    @classmethod
    def from_dict(cls, d):
        return cls(d["n"], d["dense"], d["sparse"], d["refine"], block=d.get("block", 0.0))

    def chain_cost(self, chain, reach):
        """reach[i] = P(a pair reaches tier i+1) for i = 0..k-1, reach[k] = P(reaches refine)."""
        c = self.dense[int(chain[0])]
        for i in range(1, len(chain)):
            c += reach[i] * self.sparse(chain[i], reach[i])
        c += reach[len(chain)] * self.refine(reach[len(chain)])
        return c


_COSTS = {}
#: Survivor densities the calibration places the tiers at (bracketing production's 0.1-10%).
_CAL_DENSITIES = (0.1, 0.01)


def _cost_file():
    """MF_COST_FILE: a JSON file of measured cost models, for reproducible runs.

    Calibration times the engine, so under varying machine load two runs can
    measure different costs and choose different chains or budget splits --
    each within the false-dismissal budget, but not the same triggers near
    threshold. With MF_COST_FILE set, models are read from the file and any
    missing one is measured once and added; with the file populated and
    MF_AUTOTUNE=0 (no timed trials), the chain choice is deterministic.
    """
    return os.environ.get("MF_COST_FILE") or None


def _load_cost_file(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _store_cost(path, skey, cm):
    """Add one model to the file; merges with what other processes wrote, replaces atomically."""
    data = _load_cost_file(path)
    data[skey] = cm.to_dict()
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def default_series_group(n):
    """Blocks a CPU plan filters together, as HierarchicalFilter uses without an execution policy."""
    return 32 if n <= 2048 else 16


def calibrate_costs(n, ntemplates, blocks=256, reps=5, seed=11, group=None):
    """Measure this machine's tier costs at transform size n through the engine itself.

    Synthetic analytic noise and whitened random templates; thresholds are
    placed so that the tier under test sees each target survivor density, and
    costs are read from the engine's per-tier counters (ap_hmf_tier_stats), so
    no wall-clock subtraction is involved. Calls are sized like a segment's
    (hundreds of blocks), because a pooled tier's fixed per-call cost is only
    representative when amortised over a realistic number of survivors.
    Under a second per (n, template count to the nearest power of two, series
    group), once per process.
    """
    from . import _core
    # Per-pair costs vary slowly with the template count (cache footprint, per-call
    # amortisation), so one calibration per power of two serves every bank near it:
    # a run builds banks of many sizes, and each calibration is a fraction of a second.
    nt = 1 << int(round(math.log2(min(max(int(ntemplates), 8), 128))))
    # The series group must be the plans' own: the first tier batches its work over the blocks in a
    # group, so calibrating at a smaller group overstates its cost (2x at n=1024 with 8 vs 32).
    group = int(group or default_series_group(n))
    key = (int(n), nt, group)
    if key in _COSTS:
        return _COSTS[key]
    path = _cost_file()
    skey = "%d,%d,%d" % key
    if path is not None:
        stored = _load_cost_file(path).get(skey)
        if stored is not None:
            _COSTS[key] = cm = CostModel.from_dict(stored)
            return cm
    rng = np.random.default_rng(seed)
    bands = candidate_bands(n)
    taps = n // 4
    h = np.zeros((nt, n), np.complex64)
    h[:, :taps] = rng.standard_normal((nt, taps)) / np.sqrt(taps)
    spec = np.fft.fft(h, axis=1).astype(np.complex64)
    step = n - taps
    S = (blocks + 1) * step + n
    x = (rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2)
    X = np.fft.fft(x); X[S // 2:] = 0
    ser = (np.fft.ifft(X) * np.sqrt(2)).astype(np.complex64).view(np.float32)
    starts = (np.arange(blocks) * step).astype(np.uint64)
    ws = np.full(blocks, taps, np.uint64); we = np.full(blocks, n, np.uint64)
    ref = np.zeros(n, np.float32); ref[:n // 2] = 1.0
    idx = np.zeros((blocks, nt, 1), np.int64); val = np.zeros((blocks, nt, 1), np.complex64)
    mag = np.zeros((blocks, nt, 1), np.float32); cnt = np.zeros((blocks, nt), np.int32)
    big = float(np.finfo(np.float32).max)

    def run(chain, thr, reps=reps):
        """Pairs per call and per-tier (band, passed, ticks) per call: medians over repetitions."""
        p = _core.HMF(n, 1, nt, list(chain), group, n)
        p.set_reference(ref); p.set_template_batch(0, spec); p.set_thresholds(list(thr))
        p.run_series(ser, starts, ws, we, 0, nt, n, big, idx, val, mag, cnt)      # warm-up
        prev = p.tier_stats(); rows = []
        for _ in range(reps):
            p.run_series(ser, starts, ws, we, 0, nt, n, big, idx, val, mag, cnt)
            cur = p.tier_stats()
            rows.append([(c[1] - q[1], c[2] - q[2]) for c, q in zip(cur, prev)])
            prev = cur
        med = [(prev[i][0], float(np.median([r[i][0] for r in rows])), float(np.median([r[i][1] for r in rows])))
               for i in range(len(prev))]
        return blocks * nt, med

    def thr_for(b, density):
        """Tier-0 threshold at band b passing about `density` of pairs (secant on log pass rate)."""
        lo, hi = 0.0, 16.0
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            pairs, st = run((b,), (mid,), reps=1)
            frac = st[0][1] / pairs
            if frac > density:
                lo = mid
            else:
                hi = mid
            if abs(frac - density) < 0.25 * density:
                break
        return mid

    dense, sparse, refine = {}, {}, []
    block = []
    for b in bands:
        pairs, st = run((b,), (big,))
        dense[b] = st[0][2] / pairs
    # Per-block fixed work: a whole run_series call minus its tiers and refine (nothing passes), per block.
    for b in bands[:2]:
        p = _core.HMF(n, 1, nt, [b], group, n)
        p.set_reference(ref); p.set_template_batch(0, spec); p.set_thresholds([big])
        p.run_series(ser, starts, ws, we, 0, nt, n, big, idx, val, mag, cnt)
        per = []
        for _ in range(reps):
            s0, t0 = p.series_ticks(), sum(x[2] for x in p.tier_stats())
            p.run_series(ser, starts, ws, we, 0, nt, n, big, idx, val, mag, cnt)
            per.append((p.series_ticks() - s0 - (sum(x[2] for x in p.tier_stats()) - t0)) / blocks)
        block.append(float(np.median(per)))
    b0 = bands[0]
    for f in _CAL_DENSITIES:
        g0 = thr_for(b0, f)
        pairs, st = run((b0,), (g0,))
        if st[-1][1]:
            refine.append((st[0][1] / pairs, st[-1][2] / st[-1][1]))
        for b in bands[1:]:
            pairs, st = run((b0, b), (g0, big))
            if st[0][1]:
                sparse.setdefault(b, []).append((st[0][1] / pairs, st[1][2] / st[0][1]))
    # the first band can only be a first tier; give it the next band's sparse curve for completeness
    if bands[1:]:
        sparse.setdefault(b0, list(sparse.get(bands[1], [])))
    cm = CostModel(n, dense, sparse, refine, block=float(np.median(block)))
    _COSTS[key] = cm
    if path is not None:
        _store_cost(path, skey, cm)
    return cm


def _reach(N, cols, thresholds):
    """Cumulative noise pass probabilities through the chain."""
    alive = np.ones(N.shape[0], bool)
    out = [1.0]
    for c, g in zip(cols, thresholds):
        alive &= N[:, c] >= g
        out.append(float(alive.mean()))
    return out


def kept_draws(sig, bands, chain, snr):
    """Coarse maxima of `chain`'s tiers for the draws the fine stage keeps (fine max >= snr)."""
    C, F = sig
    cols = [bands.index(b) for b in chain]
    keep = F[:, cols].max(1) >= snr
    return C[keep][:, cols]


def plan_chain(sig, noise, bands, chain, fd, cost, n, snr):
    """Thresholds for `chain` meeting compound dismissal <= fd at minimum modelled cost.

    sig, noise: signal_draws / noise_block_maxima over `bands`.
    Returns dict(chain, thresholds, reach, cost) or None when fd cannot be resolved.
    """
    cols = [bands.index(b) for b in chain]
    S = kept_draws(sig, bands, chain, snr)
    M = S.shape[0]
    k = len(chain)
    if k == 1:
        K = int(math.floor(float(fd) * M))   # the single-tier contract of gatemodel.gate_for
    else:
        # Splitting the budget searches many threshold combinations on the same draws and keeps
        # the cheapest, which favours combinations whose dismissal those draws understate. A
        # one-sided 95% binomial tolerance on the budget removes that selection bias.
        K = int(math.floor(float(fd) * M - 1.645 * math.sqrt(M * float(fd) * (1.0 - float(fd)))))
    if K < 8:
        return None
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
            for a in (_SPLIT if k <= 2 else _SPLIT_COARSE):
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
    if sig is None:
        return None, []
    noise = noise_block_maxima(power, n, bands, nsim=nsim, window=window)
    plans = []
    for chain in enumerate_chains(n, max_tiers, floor, bands=bands):
        pl = plan_chain(sig, noise, bands, list(chain), fd, cost, n, snr)
        if pl is not None:
            plans.append(pl)
    plans.sort(key=lambda d: d["cost"])
    return (plans[0] if plans else None), plans


_PLAN_CACHE = OrderedDict()


def chain_thresholds(power, n, snr, fd, chain, cost=None, floor=_MIN_BAND, nsim=20000, window=None):
    """Thresholds (and modelled reach/cost) for one given chain under `power`.

    Called whenever a plan's reference changes, inside the caller's filtering,
    so results are cached -- by profile signature, and reused for profiles
    within the same cosine similarity gatemodel applies to its draws.
    """
    p = _norm_profile(power, n)
    chain = tuple(int(b) for b in chain)
    win = None if window is None else (int(window[0]), int(window[1]))
    key = _key(p, n, chain, float(snr), float(fd), win, int(nsim), id(cost))
    hit = _PLAN_CACHE.get(key)
    if hit is not None:
        _PLAN_CACHE.move_to_end(key)
        return hit
    sim_params = (n, chain, float(snr), float(fd), win, int(nsim), id(cost))
    unit, hit = _similar_get("plan", p, sim_params)
    if hit is not None:
        return hit
    bands = usable_bands(p, n, floor)
    if not set(chain) <= set(bands):
        return None
    sig = signal_draws(p, n, bands, snr, _gm._nsamp_for(fd))
    if sig is None:
        return None
    noise = noise_block_maxima(p, n, bands, nsim=nsim, window=window)
    out = plan_chain(sig, noise, bands, list(chain), fd, cost, n, snr)
    _cache_put(_PLAN_CACHE, key, out)
    _similar_put("plan", unit, sim_params, out)
    return out




def rebin_profile(fine, delta_f, data_rate, n):
    """A fine-grid output-power profile (spacing delta_f) on block size n's bins, normalised."""
    fine = np.asarray(fine, np.float64)
    ratio = max(int(round((data_rate / n) / float(delta_f))), 1)
    keep = (len(fine) // ratio) * ratio
    binned = fine[:keep].reshape(-1, ratio).sum(axis=1)
    out = np.zeros(n)
    k = min(len(binned), n // 2 + 1)
    out[:k] = binned[:k]
    tot = out.sum()
    return out / tot if tot > 0 else None


def price_block_sizes(fine, delta_f, data_rate, longest, margin, ntemplates, snr, fd, candidates,
                      max_tiers=3):
    """Rank block sizes for one bank by modelled cost per valid output sample and template.

    For each n the bank would run one plan over blocks advancing n - longest + 1 samples; a
    block costs its fixed work (calibrated) spread over the templates, plus every pair's cost
    under the best chain at that n (gate model with the reference rebinned to n, calibrated
    tier costs). Returns [(cost, n, chain)] sorted, cheapest first.
    """
    out = []
    for n in candidates:
        nvalid = n - int(longest) + 1
        if nvalid < n // 8:
            continue
        ref = rebin_profile(fine, delta_f, data_rate, n)
        if ref is None:
            continue
        cm = calibrate_costs(n, ntemplates)
        win = (int(margin), int(n - margin))
        best, _ = choose_chain(ref, n, snr, fd, cost=cm, max_tiers=max_tiers, window=win)
        if best is None:
            continue
        out.append(((cm.block / max(ntemplates, 1) + best["cost"]) / nvalid, int(n), best["chain"]))
    return sorted(out)
