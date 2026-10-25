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
import warnings
import math
import os
import tempfile
from contextlib import contextmanager
from collections import OrderedDict
from itertools import combinations

import hashlib
import numpy as np

from . import gatemodel as _gm
# The decision rules live in _choice; gatechain's callers keep them by these names.
from ._choice import CHOICE_Z, TIE, measured_choice, paired_choice, sample_spread  # noqa: F401
# The cost file lives in _costfile; these names stay importable from here for the callers
# that use them through gatechain.
from ._costfile import (_COST_WARNED, _LEGACY_PREFIXES, _cost_file, _cost_file_lock,  # noqa: F401
                        _cost_warn, _load_cost_file, _read_cost_file, _store_cost,
                        _store_first, _update_cost, _write_cost_file, store_choice,
                        stored_choice)

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


_SIMILAR = {}           # (kind, n, bands, params) -> [((unit profile, gate features), value)]

#: Reuse tolerances: a profile takes a cached result of another only if their shapes agree
#: (cosine, a cheap first test) AND every candidate band's signal response sqrt(f_b) g_b
#: (in-band power fraction times the worst coarse-grid loss, _gate_features) agrees to this
#: relative tolerance. The response is what sets a gate's dismissal: 3% of it at band 128
#: (an O4 against an A+ reference, cosine 0.995) put a borrowed plan at 4.3x its budget, and
#: 5% PSD jitter moves it as much, so the cosine alone cannot tell them apart.
_REUSE_COS = 0.985
_REUSE_RESPONSE = 3e-3


_FEATURES = OrderedDict()


def _gate_features(p, n, m=17):
    """Per candidate band b of n: sqrt(f_b) * g_b, f_b the band's share of the profile and g_b
    the smallest normalised in-band correlation over half a coarse step (the worst sub-grid
    offset). Memoised per profile (every similarity lookup asks again: ~1000 a job)."""
    p = np.asarray(p, np.float64)
    key = (hashlib.sha1(p.tobytes()).digest(), p.size, int(n), int(m))
    hit = _FEATURES.get(key)
    if hit is None:
        hit = _FEATURES[key] = _gate_features_uncached(p, n, m)
        while len(_FEATURES) > 4096:
            _FEATURES.popitem(last=False)
    return hit.copy()


def _gate_features_uncached(p, n, m):
    tot = p.sum()
    out = []
    for b in candidate_bands(int(n)):
        q = p[:b]
        f = q.sum() / tot if tot > 0 else 0.0
        if f <= 0:
            out.append(0.0)
            continue
        ds = np.linspace(0.0, (n // b) / 2.0, m)
        g = np.abs(np.exp(2j * np.pi * np.outer(ds, np.arange(b)) / n) @ (q / q.sum())).min()
        out.append(float(np.sqrt(f) * g))
    return np.array(out)


def _similar_get(kind, p, params):
    u = (p / np.linalg.norm(p)).astype(np.float32)
    feats = None
    for (v, fv), val in _SIMILAR.get((kind,) + params, []):
        if float(np.dot(u, v)) < _REUSE_COS:
            continue
        if feats is None:
            feats = _gate_features(p, params[0])
        if fv.shape == feats.shape and np.all(
                np.abs(fv - feats) <= _REUSE_RESPONSE * np.maximum(np.abs(feats), 1e-12)):
            return (u, feats), val
    if feats is None:
        feats = _gate_features(p, params[0])
    return (u, feats), None


def _similar_put(kind, u, params, value):
    lst = _SIMILAR.setdefault((kind,) + params, [])
    lst.append((u, value))
    del lst[:-_CACHE_MAX]


class _Normals:
    """Standard normal float32 draws from one counter-based stream (_core.gauss_fill,
    src/gauss.cc): every draw depends only on the seed, the simulation's domain and its
    position, so a simulation is reproducible however it is chunked. ~1-6 ns a draw against
    NumPy's ~8-40; the draws were most of a job's setup simulation on Haswell."""

    def __init__(self, seed, domain):
        self.seed = ((int(domain) & 0xFFFFFFFF) << 32) | (int(seed) & 0xFFFFFFFF)
        self.pos = 0

    def take(self, shape):
        from . import _core
        out = np.empty(shape, np.float32)
        _core.gauss_fill(out, self.seed, self.pos)
        self.pos += out.size
        return out

    def complex(self, shape, scale=1.0):
        """Complex draws, real and imaginary parts consecutive draws of the stream, times scale
        (broadcast along the last axis): one fill, viewed in place."""
        from . import _core
        shape = tuple(shape) if np.ndim(shape) else (int(shape),)
        z = np.empty(shape, np.complex64)
        _core.gauss_fill(z.view(np.float32).reshape(-1), self.seed, self.pos)
        self.pos += 2 * z.size
        if np.ndim(scale) or scale != 1.0:
            z *= np.asarray(scale, np.float32)
        return z


def _row_peaks(z, scale, sig=None, start=None, step=0, amp=None):
    """Per row of z (complex64, rows may be strided): the largest |scale z + amp sig[start + j
    step]| and its j, in one pass (_core.row_peaks)."""
    from . import _core
    if z.dtype != np.complex64:
        z = z.astype(np.complex64)      # NumPy < 2 transforms complex64 in double precision
    m = z.shape[0]
    pk, at = np.empty(m, np.float32), np.empty(m, np.int32)
    if sig is None:
        _core.row_peaks(z, float(scale), None, None, 0, None, pk, at)
    else:
        _core.row_peaks(z, float(scale), sig, np.ascontiguousarray(start, np.int64), int(step),
                        np.ascontiguousarray(amp, np.complex64), pk, at)
    return pk, at


#: Stream domains, one per simulation, so their draws never coincide.
_DOMAIN_SIGNAL, _DOMAIN_NOISE, _DOMAIN_DIRECT = 1, 2, 3


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
        _cache_put(_SIGNAL_CACHE, key, hit)
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
    draws = _Normals(seed, _DOMAIN_SIGNAL)
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
            w = draws.complex((m, len(taus)), 1.0 / np.sqrt(2))
            seg_noise.append((w @ L.T) * np.float32(_SIG * np.sqrt(fr)))      # unnormalised: variance fr
        # running sums of the segments, in the order sum() took them: cum[i] is tiers i's noise
        # (segments 0..i), cum[-1] the full band's (bit for bit what re-summing each prefix gave)
        cum, acc = [], 0
        for sn in seg_noise:
            if sn is not None:
                acc = sn if isinstance(acc, int) else acc + sn
            cum.append(acc)
        nfull = acc
        afull = np.abs(np.float32(snr) * look(full_corr, taus - off).astype(np.complex64)[None, :] + nfull)
        fidx = np.searchsorted(taus, fl)
        ffine = afull[:, fidx].max(1)
        cols, fcols = [], []
        for i, b in enumerate(bands):
            # tier i's noise is the sum of the segments below its band edge, j = 0..i
            # only its grid lags are read: the same arithmetic as over every lag, on those
            g = gidx[i]
            nb = cum[i][:, g] / np.float32(np.sqrt(F[i]))
            z = np.float32(snr * np.sqrt(F[i])) * look(band_corr[i], taus[g] - off).astype(np.complex64)[None, :] + nb
            cols.append(np.abs(z).max(1))
            # the coarse lags are a subset of the fine grid, so they count toward the fine maximum
            fcols.append(np.maximum(ffine, afull[:, gidx[i]].max(1)))
        C_out.append(np.stack(cols, 1))
        F_out.append(np.stack(fcols, 1))
    out = (np.concatenate(C_out).astype(np.float32), np.concatenate(F_out).astype(np.float32))
    _cache_put(_SIGNAL_CACHE, key, out)
    _similar_put("signal", unit, sim_params, out)
    return out


#: The noise simulation's running-maximum records per (profile, n, bands, nsim, seed): every
#: window's block maxima come from them (noise_block_maxima), so the windows of a profile's
#: template groups share one simulation. ~6 MB each at n = 4096.
_NOISE_RECORDS = OrderedDict()
_RECORDS_MAX = 16


def _noise_records(p, n, bands, nsim, seed):
    """Per band, the records (pos int16, val float32, off int64) of each simulated block's
    running maximum of the band's normalised coarse statistic over its b lags, rows in order:
    row r's records are [off[r], off[r + 1])."""
    from . import _core
    key = _key(p, n, bands, nsim, seed)
    hit = _NOISE_RECORDS.get(key)
    if hit is not None:
        _NOISE_RECORDS.move_to_end(key)
        return hit
    # One pass in C (_core.noise_records): per block its draws (the stream positions
    # _Normals.complex gives a (nsim, bmax) array), each band's transform with the library's
    # FFT, and the running maximum's records. NumPy's transforms and a pass per band were 1.5x
    # the time (dev2); the draws are the same, the transforms agree to float32 rounding.
    bmax = bands[-1]
    scale = np.sqrt(p[:bmax]).astype(np.float32) / np.float32(np.sqrt(2))
    F = np.array([p[:b].sum() for b in bands])
    # the transform is unnormalised: 1/b of NumPy's ifft is folded into each band's scale
    bscale = tuple(float(np.float32(b * _SIG / np.sqrt(F[i])) / b) for i, b in enumerate(bands))
    stream = _Normals(seed, _DOMAIN_NOISE).seed
    cap = 16 * nsim
    while True:
        pos = tuple(np.empty(cap, np.int16) for _ in bands)
        val = tuple(np.empty(cap, np.float32) for _ in bands)
        off = tuple(np.empty(nsim + 1, np.int64) for _ in bands)
        k = _core.noise_records(scale, stream, nsim, tuple(int(b) for b in bands), bscale, pos, val, off)
        if min(k) >= 0:
            break
        cap *= 2
    out = tuple((pos[i][:k[i]].copy(), val[i][:k[i]].copy(), off[i]) for i in range(len(bands)))
    _NOISE_RECORDS[key] = out
    while len(_NOISE_RECORDS) > _RECORDS_MAX:
        _NOISE_RECORDS.popitem(last=False)
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
    # Each band's coarse statistic is circularly stationary over its lags (independent
    # bins), so a window's maximum depends only on how many lags it covers, not where:
    # simulate lags [0, count) per band, and windows of equal span share one simulation.
    counts = []
    for b in bands:
        R = n // b
        c0 = max(win[0] // R - 1, 0) if win[0] > 0 else 0
        # the engine's coarse lags for the window: one sample past each end (hmf.c)
        c1 = min(-(-win[1] // R) + 1, b)
        counts.append(max(c1 - c0, 1))
    counts = tuple(counts)
    key = _key(p, n, bands, int(nsim), int(seed), counts)
    hit = _NOISE_CACHE.get(key)
    if hit is not None:
        _NOISE_CACHE.move_to_end(key)
        return hit
    sim_params = (n, tuple(bands), int(nsim), int(seed), counts)
    unit, hit = _similar_get("noise", p, sim_params)
    if hit is not None:
        _cache_put(_NOISE_CACHE, key, hit)
        return hit
    recs = _noise_records(p, n, bands, int(nsim), int(seed))
    out = np.empty((nsim, len(bands)), np.float32)
    for i, (pos, val, off) in enumerate(recs):
        # row r's maximum over lags [0, c) is its last record below c (records rise in lag)
        below = np.cumsum(pos < counts[i])
        last = below[off[1:] - 1] - np.concatenate(([0], below[off[1:-1] - 1]))
        out[:, i] = val[off[:-1] + last - 1]
    _cache_put(_NOISE_CACHE, key, out)
    _similar_put("noise", unit, sim_params, out)
    return out


class CostModel:
    """Per-tier costs for one transform size, in engine ticks.

    dense[b]          first tier at band b, per pair
    sparse[b]         [(density, ticks per survivor)] for a later tier at band b
    refine            [(density, ticks per refined pair)]
    screen[b]         Q15 screen as the first tier at band b (q15-inl.h), when the back
                      end has one: {"dense": ticks per pair screened,
                      "excess": [(float density, screen density)], "recheck": ticks per
                      pair it passes beyond the screen itself (compaction)}
    """

    def __init__(self, n, dense, sparse, refine, block=0.0, screen=None, excess=None,
                 forward=0.0, band_forward=False):
        self.n = int(n)
        # forward: the full forward transform's share of `block`, per block. band_forward: the
        # backend can instead write only the widest tier's band and recompute the full
        # spectra of blocks with a refined pair (Vulkan, docs/vulkan-8060s-roofline.md
        # section 13), so a chain's forward cost depends on its band and refine-block
        # fraction (forward_cost).
        self.forward = float(forward)
        self.band_forward = bool(band_forward)
        # excess[b]: [(modelled density, measured density)] for a first tier at band b whose
        # gate reports an upper bound of the FP32 statistic instead of the statistic itself
        # (GPU fp16 coarse with its error bound): it passes a superset of the pairs the gate
        # model assumes, and those extra pairs reach the next stage. Measured, per band,
        # against the same gate with the bound off (calibrate_costs_gpu).
        self.excess = {int(b): sorted((float(a), float(c)) for a, c in rows)
                       for b, rows in (excess or {}).items()}
        self.screen = {int(b): {"dense": float(v["dense"]), "recheck": float(v["recheck"]),
                                "excess": sorted((float(a), float(c)) for a, c in v["excess"])}
                       for b, v in (screen or {}).items()}
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

    def signature(self):
        """A hashable summary of the model's content, for cache keys (an object's id can be
        reused once it is collected, which would hand a new model an old model's results)."""
        sig = getattr(self, "_sig", None)
        if sig is None:
            sig = self._sig = (self.n, self.block, tuple(sorted(self.dense.items())),
                               tuple((b, tuple(r)) for b, r in sorted(self._sparse.items())),
                               tuple(self._refine),
                               tuple((b, v["dense"], v["recheck"], tuple(v["excess"]))
                                     for b, v in sorted(self.screen.items())),
                               tuple((b, tuple(r)) for b, r in sorted(self.excess.items())),
                               tuple(sorted((getattr(self, "direct", None) or {}).items())),
                               getattr(self, "direct_single", True))
        return sig

    def to_dict(self):
        return {"n": self.n, "block": self.block, "dense": self.dense,
                "forward": self.forward, "band_forward": self.band_forward,
                "sparse": self._sparse, "refine": self._refine, "screen": self.screen,
                "excess": self.excess}

    @classmethod
    def from_dict(cls, d):
        return cls(d["n"], d["dense"], d["sparse"], d["refine"], block=d.get("block", 0.0),
                   screen=d.get("screen"), excess=d.get("excess"),
                   forward=d.get("forward", 0.0), band_forward=d.get("band_forward", False))

    def forward_cost(self, chain, f):
        """Per-block forward cost for this chain: the full forward, or -- where the backend
        has band forwards and chooses them (f < (n - B)/2n, its own byte rule, B the widest
        band) -- the band write plus recomputing the f blocks that have a refined pair.
        Costs scale the measured full forward: a band forward reads the same series and
        writes B of n samples (half the full forward's time is the write); a recompute is a
        full forward of one block. On the 8060S at (1024, 512), n=2048 this gives 0.75 of the
        full forward for the band write, against 2.8/3.8 = 0.74 measured."""
        full = self.forward
        if not self.band_forward or full <= 0:
            return full
        n, B = self.n, int(max(chain))
        if B >= n or not f < (n - B) / (2.0 * n):
            return full
        return full * (0.5 + 0.5 * B / n) + float(f) * full

    def pass_excess(self, b, f):
        """Measured / modelled first-tier pass rate at band b and modelled density f (>= 1):
        1 for a gate that reports its statistic, larger for one that reports a bound."""
        rows = self.excess.get(int(b))
        if not rows:
            return 1.0
        fs = np.log([r[0] for r in rows]); rs = np.log([max(r[1] / r[0], 1.0) for r in rows])
        return float(np.exp(np.interp(math.log(max(f, 1e-12)), fs, rs)))

    def screen_reach(self, b, reach1):
        """Modelled Q15 pass fraction from measured screen/float excess."""
        sc = self.screen.get(int(b))
        if sc is None or not sc["excess"]:
            return None
        fs = np.log([r[0] for r in sc["excess"]])
        ratio = np.log([r[1] / r[0] for r in sc["excess"]])
        return min(1.0, max(reach1, 1e-6) * float(np.exp(
            np.interp(math.log(max(reach1, 1e-6)), fs, ratio))))

    def first_tier(self, b, reach1):
        """(cost per pair, q15) of the cheaper first tier at band b, where reach1 is the float
        tier's pass rate. Screened: the screen on every pair, plus its per-pass cost beyond
        the screen, at reach1 scaled by the measured excess (about 1 now that the screen is
        the tier's gate on its own statistic; larger for a screen with a margin)."""
        c = self.dense[int(b)]
        sc = self.screen.get(int(b))
        if sc is None or not sc["excess"]:
            return c, False
        passed = self.screen_reach(b, reach1)
        cq = sc["dense"] + passed * sc["recheck"]
        # A close call takes the screen, as pick_stable takes its canonical chain within TIE:
        # calibration moves by about that much between processes, and a strict comparison
        # flipped the screen between processes under load (dev2, 2026-10-24) -- which also
        # moves where the pairs it passes are refined.
        return (cq, True) if cq <= c * (1.0 + TIE) else (c, False)

    def chain_forward_delta(self, chain, reach, ntemplates, model_f=False):
        """Per-pair change from the full forward this chain's forward makes (<= 0), with the
        refine-block fraction from the model: a block has a refined pair with probability
        1 - (1 - P(refine))^templates, unless a measured fraction is registered."""
        if not self.band_forward or not ntemplates or self.forward <= 0:
            return 0.0
        f = measured_refine_blocks(self.n, chain)
        if f is None and model_f:
            # Proposals only (block-size trial candidates, time_domain._BlockTrials): the
            # model's fraction may suggest a size, and the end-to-end trial decides.
            f = 1.0 - (1.0 - min(max(reach[len(chain)], 0.0), 1.0)) ** int(ntemplates)
        if f is None:
            # No measurement: no credit. The model's refine-block fraction,
            # 1 - (1 - P(refine))^templates, is right per chain, but with it the credit tipped
            # near-ties between block sizes whose per-term GPU costs are noisier than the
            # credit: 1757 of 4249 ladder templates moved to n = 8192 and the fine stage got
            # 1.4-1.7x slower (docs/gate-model.md). Model f waits for block-size trials.
            return 0.0
        return (self.forward_cost(chain, f) - self.forward) / float(ntemplates)

    def with_direct(self, prices, single_tier=True):
        """A copy whose refine is the cheaper of the measured whole-block refine and a direct
        refine priced at prices[b] ticks per refined pair for a chain whose last tier is band
        b (HierarchicalFilter._direct_prices: the direct refine's window scales with
        n / b, so it favours chains ending in a wider band)."""
        import copy
        cm = copy.copy(self)
        cm.direct = {int(b): float(v) for b, v in prices.items()}
        # single_tier False: a one-tier chain's tier runs on the CPU's FP16 gate, which reports
        # no lag, so its survivors refine by transform (hmf.c hmf_tier.lagged).
        cm.direct_single = bool(single_tier)
        cm._sig = None
        return cm

    def refine_for(self, chain, f):
        """Ticks per refined pair for this chain at refine density f."""
        r = self.refine(f)
        d = getattr(self, "direct", None)
        if d and int(chain[-1]) in d and (len(chain) > 1 or getattr(self, "direct_single", True)):
            r = min(r, d[int(chain[-1])])
        return r

    def chain_cost(self, chain, reach):
        """reach[i] = P(a pair reaches tier i+1) for i = 0..k-1, reach[k] = P(reaches refine)."""
        c, screened = self.first_tier(chain[0], reach[1] if len(reach) > 1 else 1.0)
        if len(reach) > 1:
            # A bounding first tier's extra passes are the next stage's to pay for. Only the
            # first stage after it is scaled: those pairs sit just under the gate, so a later
            # tier (same signal, more band) rejects them at its modelled rate or better.
            reach = list(reach)
            reach[1] = min(1.0, reach[1] * self.pass_excess(chain[0], reach[1]))
        for i in range(1, len(chain)):
            c += reach[i] * self.sparse(chain[i], reach[i])
        # A one-tier chain behind the Q15 screen has no coarse lag to refine around (hmf.c: the
        # screen reports none), so its survivors refine by transform, as the engine runs them.
        f = reach[len(chain)]
        c += f * (self.refine(f) if screened and len(chain) == 1 else self.refine_for(chain, f))
        return c


_COSTS = {}

#: The engine's diagnostics, read by a plan when it is created (hmf.c).
_PLAN_DIAGNOSTICS = ("MF_HMF_DUMP", "MF_HMF_TRACE")


@contextmanager
def _internal_plans():
    """Off, while the library creates plans for itself (cost calibration): the diagnostic dump
    and trace describe the caller's plans. A calibration plan would otherwise truncate the
    caller's dump file and write its own pairs into it."""
    held = {k: os.environ.pop(k) for k in _PLAN_DIAGNOSTICS if k in os.environ}
    try:
        yield
    finally:
        os.environ.update(held)


def cpu_gate_kind():
    """'f16' when new CPU hierarchical plans run the FP16 first gate (gate16.cc: ARM with
    FP16 vectors, unless MF_GATE16=0), else 'f32'. Costs, block prices and chain choices
    are cached per kind."""
    from . import _core
    return "f16" if getattr(_core, "gate16", lambda: False)() else "f32"


def _cost_sig(cost):
    return None if cost is None else cost.signature()
#: Survivor densities the calibration places the tiers at (bracketing production's 0.1-10%).
_CAL_DENSITIES = (0.1, 0.01)


def gpu_kernel_id(backend="vulkan"):
    """Identity of the shipped kernels whose measured choices this backend stores."""
    from ._kernel_id import gpu_kernel_id as identity
    return identity(backend)


def _cost_model_ok(record):
    """Whether a stored record is a cost model CostModel.from_dict can read."""
    try:
        CostModel.from_dict(record)
        return True
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def _stored_cost_model(path, skey):
    """The cost model stored under skey, or None (none stored, or a record that is not
    one: then it is reported, and a fresh calibration replaces it)."""
    stored = _load_cost_file(path).get(skey)
    if stored is None:
        return None
    if not _cost_model_ok(stored):
        _cost_warn(path, "model:" + skey, "record %r is not a cost model; recalibrating" % skey)
        return None
    return CostModel.from_dict(stored)


#: The template count calibrations run at. Per-pair tier and refine costs are flat in the
#: count to within a calibration's own noise (n=2048, 4096; 40-128 templates), and a bank's
#: own count enters pricing through the per-block share (CostModel.block / ntemplates), so one
#: calibration per transform size serves every bank -- and every bank then shares one cost
#: model, and with it the cached chain choices.
_CAL_TEMPLATES = 64


_Q15_BAND = {}


def _q15_band(b):
    """Whether this back end has a Q15 screen for a first tier at band b."""
    from . import _core
    b = int(b)
    if b not in _Q15_BAND:
        try:
            _Q15_BAND[b] = _core.MF(b, 1, 1).q15_lanes() > 0
        except (ValueError, AttributeError):
            _Q15_BAND[b] = False
    return _Q15_BAND[b]


def default_series_group(n):
    """Blocks a CPU plan filters together, as HierarchicalFilter uses without an execution policy."""
    return 32 if n <= 2048 else 16


#: The environment switch that makes a GPU's first tier report the raw coarse statistic
#: instead of an upper bound of it (read when its kernels are built: Vulkan's constant 77,
#: CUDA's mf_c16_raw, Metal's MF_C16_RAW), its raw value, and the gate kind named in
#: cost-file keys. Every GPU's coarse tier reports the bound.
_RAW_GATE_SWITCH = ("MF_COARSE_RAW", "1", "c16b")   # (variable, its raw setting, gate kind)


def _run_ms(log):
    """Device milliseconds of the runs in a timing log (Executor.timings), without the
    MF_GPU_PROFILE entries ("k:...") that lie inside them."""
    return sum(ms for label, ms in log if not label.startswith("k:"))


def _is_gpu(device):
    """Whether `device` names a GPU (the cost model's band forward and fp16 gate)."""
    try:
        from .device import parse as _parse
        return _parse(device).kind == "gpu"
    except Exception:
        return False


def gpu_gate_kind(device):
    """'f32' unless the device's first tier reports a bound (a GPU whose raw switch,
    _RAW_GATE_SWITCH, is not set); then 'c16b'."""
    row = _RAW_GATE_SWITCH
    from . import _config
    if not _is_gpu(device) or _config.get(row[0]):
        return "f32"
    return row[2]


def _reach(N, cols, thresholds):
    """Cumulative noise pass probabilities through the chain."""
    alive = np.ones(N.shape[0], bool)
    out = [1.0]
    for c, g in zip(cols, thresholds):
        alive &= N[:, c] >= g
        out.append(float(alive.mean()))
    return out


_KEPT = OrderedDict()


def kept_draws(sig, bands, chain, snr):
    """Coarse maxima of `chain`'s tiers for the draws the fine stage keeps (fine max >= snr).
    Memoised per draws (by identity, the draws held so it cannot be reused), chain and snr:
    every template group pricing a profile asks again."""
    C, F = sig
    cols = [bands.index(b) for b in chain]
    key = (id(C), id(F), tuple(cols), float(snr))
    hit = _KEPT.get(key)
    if hit is not None and hit[0] is C and hit[1] is F:
        _KEPT.move_to_end(key)
        return hit[2]
    keep = F[:, cols].max(1) >= snr
    out = C[keep][:, cols]
    out.setflags(write=False)
    _KEPT[key] = (C, F, out)
    while len(_KEPT) > 512:
        _KEPT.popitem(last=False)
    return out


def _smallest(col, m):
    """Indices of col's m smallest values, in ascending order of value (O(len) selection)."""
    m = min(int(m), col.size)
    if m <= 0:
        return np.empty(0, np.int64)
    idx = np.argpartition(col, m - 1)[:m] if m < col.size else np.arange(col.size)
    return idx[np.argsort(col[idx], kind="stable")]


#: plan_chain's candidate thresholds per (draws, chain): they do not depend on the cost model,
#: so every template group pricing the same profile and window reuses them.
_CAND_CACHE = OrderedDict()
_CAND_CACHE_MAX = 4096


def plan_chain(sig, noise, bands, chain, fd, cost, n, snr, prune=False, ntemplates=None,
               model_f=False, memo=None):
    """Thresholds for `chain` meeting compound dismissal <= fd at minimum modelled cost.

    sig, noise: signal_draws / noise_block_maxima over `bands`.
    Returns dict(chain, thresholds, reach, cost) or None when fd cannot be resolved.

    Every threshold here dismisses at most the budget K of the M kept draws, so only
    each column's K-or-so smallest values ever matter: the search works on those (a
    selection, not a sort, per column) and on the few dismissed draws' indices, instead
    of masking and sorting all M draws for every candidate split. Noise passes are
    carried down the split search, so candidates sharing a prefix share its work.

    The search yields candidate (thresholds, reach) pairs that do not depend on the cost
    model; only their pricing does. memo, a key naming the draws (_choose_chain passes the
    profile, n, window and draw parameters), caches the candidates, so another template
    group or cost model prices them without searching again. The cheapest candidate wins,
    the earliest on a tie, as without the cache.
    """
    key = None if memo is None else tuple(memo) + (tuple(int(b) for b in chain), bool(prune))
    cands = _CAND_CACHE.get(key) if key is not None else None
    if cands is None:
        cands = _chain_candidates(sig, noise, bands, chain, fd, snr, prune)
        if key is not None:
            _CAND_CACHE[key] = cands
            while len(_CAND_CACHE) > _CAND_CACHE_MAX:
                _CAND_CACHE.popitem(last=False)
    else:
        _CAND_CACHE.move_to_end(key)
    if cands is None:
        return None
    best = None
    for th, reach in cands:
        c = cost.chain_cost(chain, list(reach)) if cost is not None else _flop_cost(chain, list(reach), n)
        if ntemplates and getattr(cost, "band_forward", False):
            # only the change from the full forward (already in `block`), so a chain without
            # a measured credit is priced exactly as before; pick_stable's tie window is
            # absolute-valued, so a credit that takes a total below zero still compares
            c += cost.chain_forward_delta(chain, list(reach), ntemplates, model_f=model_f)
        if best is None or c < best["cost"]:
            best = dict(chain=tuple(chain), thresholds=th, reach=reach, cost=float(c))
    if best is not None:
        best["q15"] = (bool(cost.first_tier(chain[0], best["reach"][1])[1])
                       if hasattr(cost, "first_tier") else False)
    return best


def _chain_candidates(sig, noise, bands, chain, fd, snr, prune):
    """plan_chain's search: every (thresholds, reach) it considers for `chain`, in its order,
    or None when fd cannot be resolved."""
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
    # The earlier tiers' thresholds sit at index <= K of their sorted columns; the last
    # tier's is the rem-th smallest alive value with rem + dismissed <= K.
    low = [_smallest(S[:, i], K + 1) for i in range(k - 1)]
    low_val = [S[o, i] for i, o in enumerate(low)]
    last_order = _smallest(S[:, k - 1], K + 1)
    last_val = S[last_order, k - 1]
    out = []
    Nn = noise.shape[0]
    # The draws the earlier tiers dismiss, set and unset as the search descends and returns
    # (a copy per node was much of a search). Noise blocks below the lowest first-tier
    # threshold the search tries are dismissed on every branch: the search runs on the others
    # only, their chain columns contiguous, with alive masks over them. A reach is the alive
    # count over all Nn blocks, the same float as the mean of a full-length mask.
    dead = np.zeros(M, bool)
    splits = _SPLIT if k <= 2 else _SPLIT_COARSE
    if k > 1:
        firsts = [int(math.floor(a * K)) for a in splits]
        g0 = min((float(low_val[0][i]) for i in firsts if i >= 1), default=None)
        rows = noise[:, cols[0]] >= g0 if g0 is not None else np.zeros(Nn, bool)
        Nc = np.ascontiguousarray(noise[rows][:, cols].T)
    else:
        Nc = np.ascontiguousarray(noise[:, cols].T)

    def consider(prefix, ndead, alive, fracs):
        """Given thresholds for tiers 0..k-2, the last uses the remaining budget: ndead draws
        are dismissed (marked in dead), alive the noise blocks passing every earlier tier
        (None: all of them), fracs those tiers' pass rates."""
        rem = K - ndead
        if rem < 0 or rem >= M - ndead:
            return
        # the rem-th smallest last-tier value among draws not yet dismissed
        pos = np.flatnonzero(~dead[last_order]) if ndead else None
        if pos is not None:
            if pos.size <= rem:
                return
            at = pos[rem]
        else:
            if last_order.size <= rem:
                return
            at = rem
        g = float(last_val[at])
        th = list(prefix) + [g]
        hit = Nc[-1] >= g
        if alive is not None:
            hit &= alive
        reach = [1.0] + fracs + [int(np.count_nonzero(hit)) / Nn]
        if prune and any(r > _USELESS_PASS for r in reach[1:len(chain)]):
            # choosing: a tier that passes most of its pairs on to ANOTHER TIER only adds its
            # own cost. (The last tier's pass rate into the refine is not judged here: at a
            # low snr every chain refines most pairs, and the cost already says so.)
            return
        out.append((tuple(th), tuple(reach)))

    def rec(i, prefix, remaining, ndead, alive, fracs):
        # tier i takes a share of the budget still unallocated; the last tier gets what is left
        if i == k - 1:
            consider(prefix, ndead, alive, fracs)
            return
        for a in splits:
            share = a * remaining
            idx = int(math.floor(share * K))
            if idx < 1:
                continue
            g = float(low_val[i][idx])
            # draws this tier dismisses: its column strictly below g
            cut = int(np.searchsorted(low_val[i], g, side="left"))
            cand = low[i][:cut]
            new = cand[~dead[cand]]
            dead[new] = True
            an = Nc[i] >= g
            if alive is not None:
                an &= alive
            rec(i + 1, prefix + [g], remaining - share, ndead + int(new.size), an,
                fracs + [int(np.count_nonzero(an)) / Nn])
            dead[new] = False

    rec(0, [], 1.0, 0, None, [])
    return out


#: A tier whose modelled noise pass rate exceeds this rejects too little to be worth running:
#: such a split is skipped, so a chain is priced only with thresholds that make every tier
#: gate. (Seen on Vulkan: a band-64 first tier ahead of 256 passing 4,337,904 of 4,337,904
#: pairs, at 2-3x the segment time of every other choice.)
_USELESS_PASS = 0.5


def canonical_order(chain):
    """Deterministic preference among tied chains: fewer tiers, then the smaller bands."""
    return (len(chain), tuple(chain))


def pick_stable(items, cost, key):
    """The canonical-first of the items whose cost is within TIE of the cheapest."""
    items = list(items)
    if not items:
        return None
    lo = min(cost(x) for x in items)
    return min((x for x in items if cost(x) <= lo + TIE * abs(lo)), key=key)


_REFINE_BLOCKS = {}


def note_refine_blocks(n, band, f):
    """Record a measured refine-block fraction for transform size n and widest band `band`
    (a backend that measures it -- Vulkan's band/full choice -- calls this after each call),
    used by forward pricing in place of the model's. Keyed by the widest band, which is what
    the backend sees; chains sharing it share the measurement (a running mean)."""
    key = (int(n), int(band))
    old = _REFINE_BLOCKS.get(key)
    _REFINE_BLOCKS[key] = float(f) if old is None else 0.5 * (old + float(f))


def measured_refine_blocks(n, chain):
    return _REFINE_BLOCKS.get((int(n), int(max(chain))))


def _flop_cost(chain, reach, n):
    """Fallback when no measured table exists: transform-size proxy b log b per tier, n log n per refine."""
    c = chain[0] * math.log2(chain[0])
    for i in range(1, len(chain)):
        c += reach[i] * chain[i] * math.log2(chain[i])
    return c + reach[len(chain)] * n * math.log2(n)


_CHOICE_CACHE = OrderedDict()


def choose_chain(power, n, snr, fd, cost=None, max_tiers=3, floor=_MIN_BAND, nsim=20000, window=None,
                 ntemplates=None, model_f=False):
    """Price every chain and return (best, all_plans sorted by cost).

    Cached like the draws it is built from: by profile signature, and reused for
    profiles within the cosine similarity gatemodel applies to them.
    """
    p = _norm_profile(power, n)
    win = None if window is None else (int(window[0]), int(window[1]))
    params = (n, float(snr), float(fd), int(max_tiers), int(floor), int(nsim), win, _cost_sig(cost),
              # ntemplates prices the forward; measured refine-block fractions are left out of
              # the key on purpose, so a choice made once stays made in this process instead
              # of drifting with each call's measurement.
              None if not getattr(cost, "band_forward", False) else (int(ntemplates or 0), bool(model_f)))
    key = (_gm._profile_sig(p),) + params
    hit = _CHOICE_CACHE.get(key)
    if hit is not None:
        _CHOICE_CACHE.move_to_end(key)
        return hit
    unit, hit = _similar_get("choice", p, params)
    if hit is not None:
        _cache_put(_CHOICE_CACHE, key, hit)
        return hit
    out = _choose_chain(p, n, snr, fd, cost, max_tiers, floor, nsim, win, ntemplates, model_f)
    _cache_put(_CHOICE_CACHE, key, out)
    _similar_put("choice", unit, params, out)
    return out


def _choose_chain(power, n, snr, fd, cost, max_tiers, floor, nsim, window, ntemplates=None,
                  model_f=False):
    bands = usable_bands(power, n, floor)
    if not bands:
        return None, []
    sig = signal_draws(power, n, bands, snr, _gm._nsamp_for(fd))
    if sig is None:
        return None, []
    noise = noise_block_maxima(power, n, bands, nsim=nsim, window=window)
    memo = ("choose", _gm._profile_sig(power), n, float(snr), float(fd), tuple(bands), window,
            int(nsim), _gm._nsamp_for(fd))
    plans = []
    for chain in enumerate_chains(n, max_tiers, floor, bands=bands):
        pl = plan_chain(sig, noise, bands, list(chain), fd, cost, n, snr, prune=True,
                        ntemplates=ntemplates, model_f=model_f, memo=memo)
        if pl is not None:
            plans.append(pl)
    plans.sort(key=lambda d: d["cost"])
    # Ties (within the calibration's process-to-process noise) go to the cheaper chain on the
    # calibration-free flop proxy: deterministic for a given profile, and still a cost.
    best = pick_stable(plans, lambda d: d["cost"], lambda d: (_flop_cost(d["chain"], d["reach"], n), d["chain"]))
    return best, plans


_PLAN_CACHE = OrderedDict()


_DIRECT_CACHE = OrderedDict()
#: Per-draw statistics of direct_halfwidth's model, shared by every chain and threshold set
#: on one (profile, n, window, snr, seed): (sig, n, window, snr, seed) -> _DirectDraws.
_DIRECT_DRAWS = OrderedDict()
_DIRECT_DRAWS_MAX = 8
_DIRECT_CHUNK = 1000


class _DirectDraws:
    """direct_halfwidth's draws, reduced to what any chain needs: per draw, whether the fine
    maximum reaches snr and its lag, and per band the coarse maximum over the window and its
    lag. A chain and its thresholds then select draws with masks. The draws are generated
    chunk by chunk from one seeded generator, exactly as direct_halfwidth always drew them,
    so the first k chunks are the same for any draw count: a call wanting fewer draws reads
    a prefix, one wanting more continues the generator."""

    def __init__(self, p, n, win, snr, seed, bands):
        self.n, self.win, self.snr = n, win, float(snr)
        self.rng = np.random.default_rng(seed)          # the lags and phases
        self._draws = _Normals(seed, _DOMAIN_DIRECT)    # the noise
        self.bands = tuple(int(b) for b in bands)
        w0, w1 = win
        self.A = np.fft.ifft(p) * n
        self.lags = np.arange(w0, w1)
        self.sq = _SIG * np.sqrt(p)
        self.tier = {}
        for b in self.bands:
            f = float(p[:b].sum())
            q = np.zeros(n)
            q[:b] = p[:b]
            R = n // b
            cs = w0 // R
            cs = cs - 1 if cs > 0 else cs
            ce = min(-(-w1 // R) + 1, b)               # one coarse sample past each end (hmf.c)
            self.tier[b] = (f, np.fft.ifft(q) * n / np.sqrt(f), R, cs, ce)
        self.fine_ok, self.fa = [], []
        self.cmax = {b: [] for b in self.bands}
        self.cam = {b: [] for b in self.bands}

    def extend(self, nsim):
        """Draw chunks until nsim draws are held.

        The noise comes from the counter-based stream (_Normals), the lags and phases from
        NumPy's generator, and everything runs in single precision, in place: in double
        precision, from NumPy's generator, this was most of a Haswell job's setup simulation."""
        n, (w0, w1) = self.n, self.win
        if not hasattr(self, "_A32"):
            self._A32 = np.concatenate([self.A, self.A]).astype(np.complex64)
            self._scale32 = (self.sq / np.sqrt(2)).astype(np.float32)
            self._tier32 = {b: (np.float32(b / np.sqrt(t[0])), np.concatenate([t[1], t[1]]).astype(np.complex64))
                            for b, t in self.tier.items()}
        while len(self.fine_ok) * _DIRECT_CHUNK < nsim:
            m = _DIRECT_CHUNK
            N = self._draws.complex((m, n), self._scale32)
            tau0 = self.rng.integers(w0, w1, m)
            amp = (self.snr * np.exp(2j * np.pi * self.rng.random(m))).astype(np.complex64)
            # the signal's response at lags w0..w1-1 around tau0: a run of the doubled A
            pk, at = _row_peaks(np.fft.ifft(N, axis=1)[:, w0:w1], n, self._A32, (w0 - tau0) % n, 1, amp)
            self.fine_ok.append(pk >= self.snr)
            self.fa.append(at + w0)
            for b in self.bands:
                f, Abt, R, cs, ce = self.tier[b]
                sc, Ab32 = self._tier32[b]
                pk, at = _row_peaks(np.fft.ifft(N[:, :b], axis=1)[:, cs:ce], sc, Ab32, (cs * R - tau0) % n, R, amp)
                self.cmax[b].append(pk)
                self.cam[b].append((at.astype(np.int64) + cs) * R)

    def distances(self, chain, thresholds, nsim):
        """direct_halfwidth's per-chunk kept distances for this chain, from the first nsim draws."""
        self.extend(nsim)
        n, out = self.n, []
        for c in range(nsim // _DIRECT_CHUNK):
            ok = self.fine_ok[c].copy()
            for b, thr in zip(chain, thresholds):
                ok &= self.cmax[b][c] >= float(thr)
            d = np.abs(self.fa[c] - self.cam[chain[-1]][c])
            d = np.minimum(d, n - d) / (n // chain[-1])
            out.append(d[ok])
        return out


def _direct_draws(p, n, chain, win, snr, nsim, seed):
    """The shared draws for this question, or None where they cannot answer it exactly (a
    draw count that is not whole chunks, or a band outside the profile's usable bands)."""
    if nsim % _DIRECT_CHUNK:
        return None
    bands = usable_bands(p, n)
    if not set(chain) <= set(bands):
        return None
    key = (_gm._profile_sig(p), n, win, float(snr), int(seed))
    hit = _DIRECT_DRAWS.get(key)
    if hit is None:
        hit = _DirectDraws(p, n, win, snr, seed, bands)
        _DIRECT_DRAWS[key] = hit
        while len(_DIRECT_DRAWS) > _DIRECT_DRAWS_MAX:
            _DIRECT_DRAWS.popitem(last=False)
    else:
        _DIRECT_DRAWS.move_to_end(key)
    return hit


def direct_halfwidth(power, n, chain, thresholds, snr, fd, window=None, nsim=20000, seed=31):
    """Half-width, in last-tier coarse samples, of the direct refine's window around a pair's
    largest last-tier coarse lag: the largest distance to the fine peak seen in nsim draws
    the gate passes, rounded up (at least 1).

    The draws are signal_draws' model over whole blocks: noise with spectrum _SIG^2 p, a
    signal of strength snr whose output spectrum is snr p at a uniform lag in the window,
    every tier's coarse statistic (its band of the product over sqrt(F_b)), kept when every
    tier passes and the fine maximum reaches snr. Returns (halfwidth, distances' 99.99th
    percentile, draws kept)."""
    p = _norm_profile(power, n)
    chain = tuple(int(b) for b in chain)
    win = (0, n) if window is None else (int(window[0]), int(window[1]))
    key = _key(p, n, chain, tuple(float(t) for t in thresholds), float(snr), float(fd), win,
               int(nsim), int(seed))
    hit = _DIRECT_CACHE.get(key)
    if hit is not None:
        return hit
    # Thresholds are rounded for the similarity key: plans of similar profiles (another
    # segment's PSD, another template group) have thresholds equal to ~1e-3 and share draws.
    sim_params = (n, chain, tuple(round(float(t), 2) for t in thresholds), float(snr),
                  float(fd), win, int(nsim), int(seed))
    unit, hit = _similar_get("direct", p, sim_params)
    if hit is not None:
        _cache_put(_DIRECT_CACHE, key, hit)
        return hit
    shared = _direct_draws(p, n, chain, win, snr, int(nsim), seed)
    if shared is not None:
        dist = shared.distances(chain, thresholds, int(nsim))
        kept = int(sum(len(d) for d in dist))
        d = np.concatenate(dist) if dist else np.zeros(0)
        hw = max(1, int(np.ceil(d.max()))) if len(d) else 1     # the caller adds its margin
        out = (hw, float(np.percentile(d, 99.99)) if len(d) else 0.0, kept)
        _cache_put(_DIRECT_CACHE, key, out)
        _similar_put("direct", unit, sim_params, out)
        return out
    rng = np.random.default_rng(seed)
    F = [float(p[:b].sum()) for b in chain]
    w0, w1 = win
    # The signal in the lag domain: the fine output's is snr * A(tau - tau0), A the reference's
    # correlation (peak 1), and tier b's at coarse lag j is snr * A_b(jR - tau0), A_b the
    # correlation of its band over sqrt(F_b) -- tabulated once, so a draw costs one n-point
    # transform of its noise plus one per tier.
    A = np.fft.ifft(p) * n
    Ab = []
    for b, f in zip(chain, F):
        q = np.zeros(n); q[:b] = p[:b]
        Ab.append(np.fft.ifft(q) * n / np.sqrt(f))
    tiers = []
    for b in chain:
        R = n // b
        cs = w0 // R
        cs = cs - 1 if cs > 0 else cs
        ce = min(-(-w1 // R) + 1, b)                   # one coarse sample past each end (hmf.c)
        tiers.append((b, R, cs, ce))
    lags = np.arange(w0, w1)
    sq = _SIG * np.sqrt(p)
    kept, dist = 0, []
    chunk = 1000
    for c0 in range(0, nsim, chunk):
        m = min(chunk, nsim - c0)
        N = (rng.standard_normal((m, n)) + 1j * rng.standard_normal((m, n))) * (sq / np.sqrt(2))
        tau0 = rng.integers(w0, w1, m)
        amp = float(snr) * np.exp(2j * np.pi * rng.random(m))
        fine = np.fft.ifft(N, axis=1)[:, w0:w1] * n
        fine = np.abs(fine + amp[:, None] * A[(lags[None, :] - tau0[:, None]) % n])
        ok = fine.max(1) >= float(snr)
        am = None
        for (b, R, cs, ce), Abt, thr, f in zip(tiers, Ab, thresholds, F):
            co = np.fft.ifft(N[:, :b], axis=1)[:, cs:ce] * b / np.sqrt(f)
            cl = np.arange(cs, ce) * R
            co = np.abs(co + amp[:, None] * Abt[(cl[None, :] - tau0[:, None]) % n])
            ok &= co.max(1) >= float(thr)
            am = (co.argmax(1) + cs) * R
        fa = fine.argmax(1) + w0
        d = np.abs(fa - am)
        d = np.minimum(d, n - d) / (n // chain[-1])      # lags are circular in a block
        dist.append(d[ok])
        kept += int(ok.sum())
    d = np.concatenate(dist) if dist else np.zeros(0)
    hw = max(1, int(np.ceil(d.max()))) if len(d) else 1     # the caller adds its margin
    out = (hw, float(np.percentile(d, 99.99)) if len(d) else 0.0, kept)
    _cache_put(_DIRECT_CACHE, key, out)
    _similar_put("direct", unit, sim_params, out)
    return out


#: The cost calibration runs hierarchical plans, which sit above this module, so it lives in
#: matchedfilter._calibration and registers itself here when it loads (the package loads it).
_CALIBRATE = None


def calibrate_costs(n, ntemplates, blocks=256, reps=5, seed=11, group=None):
    """Measure this machine's tier costs at transform size n through the engine itself: the
    CostModel the chain choice prices with (matchedfilter._calibration.calibrate_costs,
    which documents the measurement). Kept in MF_COST_FILE when it is set."""
    return _CALIBRATE(n, ntemplates, blocks=blocks, reps=reps, seed=seed, group=group)


def chain_thresholds(power, n, snr, fd, chain, cost=None, floor=_MIN_BAND, nsim=20000, window=None):
    """Thresholds (and modelled reach/cost) for one given chain under `power`.

    Called whenever a plan's reference changes, inside the caller's filtering,
    so results are cached -- by profile signature, and reused for profiles
    within the same cosine similarity gatemodel applies to its draws.
    """
    p = _norm_profile(power, n)
    chain = tuple(int(b) for b in chain)
    win = None if window is None else (int(window[0]), int(window[1]))
    key = _key(p, n, chain, float(snr), float(fd), win, int(nsim), _cost_sig(cost))
    hit = _PLAN_CACHE.get(key)
    if hit is not None:
        _PLAN_CACHE.move_to_end(key)
        return hit
    sim_params = (n, chain, float(snr), float(fd), win, int(nsim), _cost_sig(cost))
    unit, hit = _similar_get("plan", p, sim_params)
    if hit is not None:
        _cache_put(_PLAN_CACHE, key, hit)
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


_PRICE_CACHE = OrderedDict()


