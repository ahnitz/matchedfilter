"""Gate chains: one model for every hierarchical configuration.

A configuration is a chain of coarse bands b1 < b2 < ... < bk followed by the
full refine. k = 1 is what used to be called a single-tier gate, k = 2 a
cascade; they are the same object here, enumerated, priced and chosen on equal
footing. Each tier runs on the previous tier's survivors.

Two questions decide a chain, and they are kept separate:

  ACCURACY  For a signal of strength `snr`, the thresholds g1..gk (and on the
            CPU the direct refine's window) must dismiss `fd` of the pairs the
            full filter would keep, on average, with the per-plan tail
            gatemodel.fit_order states. Taken from joint draws of every tier's
            coarse maximum and the fine maximum under signal (the same
            construction as gatemodel, generalised from two tiers to any set of
            bands; all candidate bands are drawn jointly, so every chain is
            evaluated on the same draws).

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

The budget is split between the tiers by minimising that cost on half the draws, and
the thresholds are fitted on the other half (plan_chain), so that no choice is judged on
the draws it was made on; the split is part of the chain's plan.
"""
import math
import os
from contextlib import contextmanager
from collections import OrderedDict
from itertools import combinations
from typing import NamedTuple

import hashlib
import numpy as np

from . import gatemodel as _gm
from . import _costfile
# The decision rules live in _choice; gatechain's callers keep them by these names.
from ._choice import TIE
# The cost file lives in _costfile. The calibration, the bank's layout and the Vulkan back end
# reach these through gatechain (and tests patch _cost_file here), so they stay bound here.
from ._costfile import _cost_warn, _load_cost_file
_cost_file, _store_first = _costfile._cost_file, _costfile._store_first
store_choice, stored_choice = _costfile.store_choice, _costfile.stored_choice

_SIG = _gm._SIG
#: Sub-sample arrival fractions signal_draws spreads its signals over, 1/_NF apart, the sample
#: itself among them: at a high snr only a signal arriving near a sample reaches it on the
#: sampled grid (strata midpoints left no draw detected at snr = 1000). A signal's loss
#: between samples is second order in the offset, so 1/16 of a sample stands for any time.
_NF = 16
_MIN_BAND = 64

#: The per-tier budget shares the split search tries (plan_chain; three tiers search their
#: product). MEASURED: the fitted plans of a search on 19 shares instead (19 x 19 for three
#: tiers) cost within 0.05% of these on average over every given chain, and within 0.4 +- 0.3%
#: for the pick, where a few of 50 picks change chain either way (5 profiles x 10 model seeds,
#: n = 2048 and 4096, fd 1e-3, Zen 5 costs, with and without a direct refine; 2026-10-29). The
#: fit moves every tier's threshold, so the split's fine structure matters little.
_SPLIT = np.linspace(0.05, 0.95, 9)

_SIGNAL_CACHE = OrderedDict()

#: The noise blocks the model's pass rates rest on (model_draws), the signal simulation's
#: first rows (_extend_signal): about 20 blocks pass a tier at a pass rate of 1e-3.
_NOISE_BLOCKS = 20000


def model_draws(fd):
    """(detections, noise blocks) the model runs with at budget fd: the signal simulation's
    detections (gatemodel._nsamp_for; None when the budget needs more than the model holds)
    and the noise blocks, the first of the same simulation's draws (_simulate), so where it
    runs as many they cost nothing more."""
    return _gm._nsamp_for(fd), _NOISE_BLOCKS

_NOISE_CACHE = OrderedDict()
_CACHE_MAX = 64


class GateTier(NamedTuple):
    """One coarse gate tier: transform length `band` and starting fine bin `k0`."""
    band: int
    k0: int = 0


def _band_slice(n, b, k0):
    """Active fine-bin range (k0, khi) for coarse band `b` starting at `k0`."""
    k0 = int(k0)
    if k0 <= 0:
        return 0, int(b)
    return k0, min(k0 + int(b), int(n) // 2)


def band_offset(power, n, b):
    """Starting fine bin k0 (8-bin aligned, 0 <= k0 <= n // 2 - b) maximizing worst-case
    midpoint coarse SNR per unit fine SNR over [k0, k0 + b).

    Parameters
    ----------
    power : array_like
        Expected nonnegative filter-output power per fine frequency bin (length `n`).
    n : int
        Full fine FFT block length.
    b : int
        Coarse band transform length.

    Returns
    -------
    int
        Optimal 8-bin-aligned starting bin `k0`, or `0` when shifting improves midpoint
        coarse SNR by at most 0.01 per unit fine SNR (or `b >= n // 2`).
    """
    n, b = int(n), int(b)
    if b >= n // 2 or b < 1:
        return 0
    p = np.asarray(power, dtype=np.float64)
    if p.shape != (n,) or not np.all(np.isfinite(p)):
        return 0
    pos = np.where(p > 0.0, p, 0.0)
    tot = float(pos.sum())
    if tot <= 0.0:
        return 0
    w = pos[:n // 2] / tot
    if float(w.sum()) <= 0.0:
        return 0
    cf = np.concatenate(([0.0], np.cumsum(w)))
    k0s = np.arange(0, n // 2 - b + 1, 8, dtype=np.int64)
    # Only skip leading dead-zone bins (<= 1e-5 of total power) when they span at least half
    # of the DC-anchored band [0, b), keeping k0 anchored to the low-frequency cutoff.
    k0s = k0s[cf[k0s] <= 1e-5]
    if k0s.size <= 1 or int(k0s[-1]) < b // 2:
        return 0
    k = np.arange(n // 2, dtype=np.float64)
    cz = np.concatenate(([0.0j], np.cumsum(w * np.exp(1j * np.pi * k / b))))
    f = cf[k0s + b] - cf[k0s]
    z = np.abs(cz[k0s + b] - cz[k0s])
    rho = np.where(f > 1e-12, z / np.sqrt(np.maximum(f, 1e-30)), 0.0)
    best = int(np.argmax(rho))
    if int(k0s[best]) >= b // 2 and rho[best] > rho[0] + 0.01:
        return int(k0s[best])
    return 0


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
    out = []
    for b in candidate_bands(n, floor):
        k0, khi = _band_slice(n, b, band_offset(p, n, b))
        if p[k0:khi].sum() > 0:
            out.append(b)
    return out


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
        k0, khi = _band_slice(int(n), b, band_offset(p, n, b))
        q = p[k0:khi]
        f = q.sum() / tot if tot > 0 else 0.0
        if f <= 0:
            out.append(0.0)
            continue
        ds = np.linspace(0.0, (n // b) / 2.0, m)
        g = np.abs(np.exp(2j * np.pi * np.outer(ds, np.arange(k0, khi)) / n) @ (q / q.sum())).min()
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


def _similar_put(kind, u, params, value, keep=None):
    lst = _SIMILAR.setdefault((kind,) + params, [])
    lst.append((u, value))
    del lst[:-(keep or _CACHE_MAX)]


#: The gate model's stream domain: its draws are _core.gauss_fill's (src/gauss.cc) at this
#: domain and the seed, counter-based, so any block's draws depend only on its position.
_DOMAIN_SIGNAL = 1
#: The gate model's simulation seed: signal_draws and noise_block_maxima read one simulation.
_SEED = 13


def _engine_lags(n, bands, window):
    """(w0, w1, c0, c1): the fine lags [w0, w1) and each band's coarse lags [c0, c1) the engine
    searches for `window` (hmf.c: one coarse sample past each end inside the block)."""
    from ._windows import coarse_lags
    w0, w1 = (0, n) if window is None else (int(window[0]), int(window[1]))
    lags = [coarse_lags(n, b, w0, w1) for b in bands]
    return w0, w1, tuple(c[0] for c in lags), tuple(c[1] for c in lags)


#: Rows per block of the signal simulation's arrival draws (_arrivals): a row's arrival depends
#: only on its row, so a simulation extended in steps draws what one run at once draws.
_ARRIVAL_ROWS = 1 << 14
#: The signal simulation per (profile, n, bands, snr, seed): every window's draws come from it
#: (signal_draws), so a profile's windows share one simulation, extended when one needs more.
_SIGNAL_RECORDS = OrderedDict()


def signal_draws(power, n, bands, snr, ndet, seed=_SEED, window=None, lags_too=False):
    """Joint draws of every band's coarse window maximum and the fine window maximum under a
    signal of strength snr arriving at a uniformly random time in the window.

    Returns (C, F), both (M, len(bands)) float32: C[:, i] band i's largest coarse statistic
    over the coarse lags the engine searches for `window` (None: the whole block); F every
    column the largest fine statistic over the window's lags (a broadcast view: every chain
    conditions on the same fine maximum). The rows hold exactly `ndet` detections, draws
    whose fine window maximum reaches snr (kept_draws: only they can be kept), the last row
    the ndet-th, and before them the few draws that reach snr elsewhere in the block only.
    The simulation runs until it has them, however few of its draws a large snr keeps.

    One simulation, exact for stationary Gaussian noise: per draw a block's n bins with
    variance p_k, the fine statistic their n-point transform and band b's the b-point
    transform of bins [0, b), normalised to unit per-component variance -- the filter's own
    sharing of noise between the tiers and the fine stage -- plus the signal through the
    transforms' linearity (its response at every lag), arriving on a sample or 1/_NF of one
    apart. The maxima are over the whole window, as the engine's are: no neighbourhood around
    the signal, no pairing with noise elsewhere in the block (_simulate).

    Each draw holds its statistics' running-maximum records outward from the signal, so any
    window around it is two lookups: draw r's signal lies a_r + frac samples into the window,
    a_r uniform, and the window starts where the engine's would relative to the coarse grids
    (a_r = (t_r - w0) mod R_max + m R_max, m uniform; a draw whose a_r falls past the span
    is dropped, which keeps a_r exactly uniform).

    With lags_too, returns ((C, F), (fine_at, coarse_at)): where each draw's fine maximum and
    each band's coarse maximum lie, as block lags (coarse lags times the band's step), as the
    engine's direct refine compares them (hmf.c refine_direct_pair)."""
    p = _norm_profile(power, n)
    bands = sorted(int(b) for b in bands)
    k0s = tuple(band_offset(p, n, b) for b in bands)
    Fb = np.array([p[slice(*_band_slice(n, b, k0))].sum() for b, k0 in zip(bands, k0s)])
    if np.any(Fb <= 0):
        return None          # a band holding no power cannot gate; callers drop such bands (usable_bands)
    lags = _engine_lags(n, bands, window)
    ndet = int(ndet)
    extra = (k0s,) if any(k0s) else ()
    key = _key(p, n, bands, float(snr), ndet, int(seed), lags, _NF, *extra)
    hit = _SIGNAL_CACHE.get(key)
    if hit is not None:
        _SIGNAL_CACHE.move_to_end(key)
        return hit[0] if not lags_too else hit
    sim = _signal_records(p, n, bands, Fb, float(snr), ndet, int(seed), k0s=k0s)
    skey = ("sim", id(sim), n, tuple(bands), float(snr), ndet, int(seed), lags, _NF, *extra)
    shit = _SIGNAL_CACHE.get(skey)
    if shit is not None and shit[0] is sim:
        _SIGNAL_CACHE.move_to_end(skey)
        hit = shit[1]
        _cache_put(_SIGNAL_CACHE, key, hit)
        return hit[0] if not lags_too else hit
    while True:
        C, F, at = _signal_window(sim, n, bands, lags)
        det = np.flatnonzero(F >= snr)
        if det.size >= ndet:
            break
        # the window misses some of the block's detections: more, in proportion
        kept = sim["t"].size
        sim = _signal_records(p, n, bands, Fb, float(snr),
                              kept + int(math.ceil((ndet - det.size) * kept / max(det.size, 1))) + 1,
                              int(seed), k0s=k0s)
    end = int(det[ndet - 1]) + 1 if ndet > 0 else 0
    C, F, at = C[:end], F[:end], (at[0][:end], at[1][:end])
    hit = ((C, np.broadcast_to(F[:, None], C.shape)), at)
    _cache_put(_SIGNAL_CACHE, skey, (sim, hit))
    _cache_put(_SIGNAL_CACHE, key, hit)
    return hit[0] if not lags_too else hit


def _arrivals(seed, R, row0, rows):
    """(t, u) of the signal simulation's rows row0 .. row0 + rows: t its integer arrival,
    uniform in [0, R), and u uniform in [0, 1), each row's from the block of _ARRIVAL_ROWS
    holding it (its own generator)."""
    ts, us = [], []
    for blk in range(row0 // _ARRIVAL_ROWS, (row0 + rows - 1) // _ARRIVAL_ROWS + 1):
        rng = np.random.default_rng([int(seed), _DOMAIN_SIGNAL, blk])
        ts.append(rng.integers(0, R, _ARRIVAL_ROWS))
        us.append(rng.random(_ARRIVAL_ROWS))
    s = row0 % _ARRIVAL_ROWS
    return (np.concatenate(ts)[s:s + rows].astype(np.int64), np.concatenate(us)[s:s + rows])


def _signal_records(p, n, bands, Fb, snr, kept, seed, k0s=None):
    """signal_draws' simulation, with at least `kept` draws kept: a dict holding the profile
    it simulates and, per kept draw, the signal's integer arrival t in [0, R_max), a uniform u
    in [0, 1) placing it in a window, and per statistic (fine, then each band) and side
    (right, left) the records (pos, val, off) of its running maximum outward from the signal.
    Extended in place when a request needs more kept draws: a row's draws depend only on its
    row, so the draws are those of one simulation run at once."""
    k0s = (0,) * len(bands) if k0s is None else tuple(int(x) for x in k0s)
    extra = (k0s,) if any(k0s) else ()
    key = _key(p, n, bands, snr, seed, _NF, *extra)
    sim = _SIGNAL_RECORDS.get(key)
    if sim is not None:
        _SIGNAL_RECORDS.move_to_end(key)
    else:
        # profiles alike in the gates' response share a simulation (_similar_get), whatever
        # window each searches: a job's banks have nearly one reference profile. It is
        # extended with its own profile, so it stays one simulation.
        params = (n, tuple(bands), snr, seed, _NF) + extra
        unit, sim = _similar_get("signal-records", p, params)
        if sim is None:
            sim = dict(p=p, Fb=Fb, k0s=k0s, rows=0, t=np.empty(0, np.int64), u=np.empty(0),
                       recs=None, tab=None)
            _similar_put("signal-records", unit, params, sim, keep=_RECORDS_MAX)
        _SIGNAL_RECORDS[key] = sim
        while len(_SIGNAL_RECORDS) > _RECORDS_MAX:
            _SIGNAL_RECORDS.popitem(last=False)
    if sim["t"].size < kept:
        _extend_signal(sim, n, bands, snr, kept, seed, k0s=k0s)
    return sim


def _extend_signal(sim, n, bands, snr, kept, seed, k0s=None):
    """Simulate further rows of `sim` until it holds `kept` kept draws."""
    p, Fb = sim["p"], sim["Fb"]
    if k0s is None:
        k0s = sim.get("k0s") or ((0,) * len(bands))
    else:
        k0s = tuple(int(x) for x in k0s)
    if sim["tab"] is None:
        k = np.arange(n)
        # the signal's response, per arrival fraction, for the fine statistic then each band
        # (active bins [k0, khi), normalised as the band is): a band of b lags R apart at
        # [rho b + e] holds it at its lag e after the one rho samples before the signal,
        # d = e R - rho samples after it
        j = np.arange(_NF)[:, None]
        q = p[None, :] * np.exp((-2j * np.pi / (_NF * n)) * j * k[None, :])
        tab = np.empty((_NF, 1 + len(bands), n), np.complex64)
        tab[:, 0] = np.fft.ifft(q, axis=1) * (n * snr)
        qm = np.zeros_like(q)
        prev_lo, prev_hi = 0, 0
        for s, (m, f, k0) in enumerate(zip(bands, Fb, k0s), 1):
            k_lo, k_hi = _band_slice(n, m, k0)
            if k_lo == prev_lo and k_hi >= prev_hi:
                qm[:, prev_hi:k_hi] = q[:, prev_hi:k_hi]
            else:
                qm.fill(0)
                qm[:, k_lo:k_hi] = q[:, k_lo:k_hi]
            prev_lo, prev_hi = k_lo, k_hi
            resp = np.fft.ifft(qm, axis=1) * (n * snr / np.sqrt(f))
            R = n // m
            d = (np.arange(m)[None, :] * R - np.arange(R)[:, None]).reshape(-1) % n
            tab[:, s] = resp[:, d]
        sim["tab"] = tab
    # Draws whose fine statistic stays below snr at every lag cannot be kept by any window and
    # hold no records. About 0.6 are kept at a usual snr, far fewer at a large one, where only
    # signals arriving close to a sample reach snr (about 3% at snr = 1000): each step runs the
    # rows the kept share so far says are still needed (the first assumes all are kept), and
    # three standard deviations of their count more, so that a third step is rare; what it
    # overshoots stays for a later request. The model's noise blocks (_NOISE_BLOCKS) are the
    # first rows' noise alone, recorded as they run (a third of a row's work): later rows'
    # are left to noise_block_maxima, which simulates them should a request read that far.
    extra = (k0s,) if any(k0s) else ()
    nkey = _key(p, n, bands, seed, *extra)
    ts, us, parts = [sim["t"]], [sim["u"]], [] if sim["recs"] is None else [sim["recs"]]
    rows, have = sim["rows"], sim["t"].size
    while have < kept:
        need = kept - have
        step = need if not rows else int(math.ceil((need + 3 * math.sqrt(need)) * rows / max(have, 1)))
        held = _NOISE_RECORDS.get(nkey)
        noise = (held[0] if held is not None else 0) == rows < _NOISE_BLOCKS
        if noise:
            step = min(step, _NOISE_BLOCKS - rows)
        t, u = _arrivals(seed, n // bands[0], rows, step)
        fi = ((rows + np.arange(step)) % _NF).astype(np.int32)
        recs, nrec = _simulate(p, n, bands, step, rows, seed, (sim["tab"], t, fi), noise,
                               keep_at=snr, k0s=k0s)
        if nrec is not None:
            _add_noise_records(nkey, rows, step, nrec)
        keep = np.diff(recs[0][2]) > 0          # a kept draw's fine maximum has a record
        ts.append(t[keep]); us.append(u[keep])
        parts.append(tuple(_rows(r, keep) for r in recs))
        rows += step
        have += int(keep.sum())
    sim["t"], sim["u"] = np.concatenate(ts), np.concatenate(us)
    sim["recs"] = tuple(_join_records([pt[q] for pt in parts]) for q in range(len(parts[0])))
    sim["rows"] = rows


def _last_within(rec, reach):
    """Per row of records (pos, val, off): the value of its last record at distance <= reach[r]
    (records rise with distance) and that distance, 0 and -1 where none is
    (_core.records_within)."""
    from . import _core
    pos, val, off = rec
    out = np.empty(off.size - 1, np.float32)
    at = np.empty(off.size - 1, np.int32)
    _core.records_within(pos, val, off, np.ascontiguousarray(reach, np.int64), out, at)
    return out, at


def _both_sides(right, left, reach_right, reach_left):
    """The larger of a statistic's two sides' maxima within their reach, and its lag relative
    to the signal's (positive to the right), in the statistic's own lags."""
    vr, er = _last_within(right, reach_right)
    vl, el = _last_within(left, reach_left)
    take_r = vr >= vl
    return np.where(take_r, vr, vl), np.where(take_r, er, -el).astype(np.int64)


def _signal_window(sim, n, bands, lags):
    """(C, F, at) of signal_draws for the engine's lags `lags` (_engine_lags) from the
    simulation `sim` (_signal_records): at = (fine lag, coarse lags per band) of each maximum,
    as block lags (a coarse lag times its band's step; a statistic searched over the whole
    block wraps into it)."""
    t, u, recs = sim["t"], sim["u"], sim["recs"]
    w0, w1, c0, c1 = lags
    span, step = w1 - w0, n // bands[0]
    # the window starts w0 (mod step) before the signal's grid, so its coarse lags are the
    # engine's moved by whole coarse steps
    a = (t - w0) % step + np.floor(u * -(-span // step)).astype(np.int64) * step
    ok = a < span
    t, a = t[ok], a[ok]
    shift = t - a - w0                       # a multiple of every band's step
    whole = span >= n
    F, fat = _both_sides(_rows(recs[0], ok), _rows(recs[1], ok),
                         np.full(t.size, n - 1) if whole else span - 1 - a,
                         np.zeros(t.size, np.int64) if whole else a)
    C = np.empty((t.size, len(bands)), np.float32)
    cat = np.empty((t.size, len(bands)), np.int64)
    for i, b in enumerate(bands):
        R = n // b
        js = t // R
        if c1[i] - c0[i] >= b:
            right, left = np.full(t.size, b - 1), np.zeros(t.size, np.int64)
        else:
            right, left = c1[i] + shift // R - 1 - js, js - (c0[i] + shift // R)
        C[:, i], e = _both_sides(_rows(recs[2 + 2 * i], ok), _rows(recs[3 + 2 * i], ok), right, left)
        # (js + e) R - t samples after the signal, which lies w0 + a into the block
        cat[:, i] = (js + e) * R - t + w0 + a
        if c1[i] - c0[i] >= b:
            cat[:, i] %= n
    fat = fat + w0 + a
    if whole:
        fat %= n
    for x in (C, F, fat, cat):
        x.setflags(write=False)
    return C, F, (fat, cat)


def _rows(rec, keep):
    """The records (pos, val, off) of the rows `keep` (bool) selects."""
    if keep.all():
        return rec
    pos, val, off = rec
    cnt = np.diff(off)[keep]
    tot = int(cnt.sum())
    if off[0] == 0 and tot == int(off[-1]):
        # Unkept rows hold no records (_extend_signal): pos and val are already contiguous.
        return pos[:tot], val[:tot], np.concatenate(([0], np.cumsum(cnt)))
    starts = off[:-1][keep]
    idx = np.repeat(starts - np.concatenate(([0], np.cumsum(cnt)[:-1])), cnt) + np.arange(tot)
    return pos[idx], val[idx], np.concatenate(([0], np.cumsum(cnt)))


#: The noise simulation's running-maximum records per (profile, n, bands, nsim, seed): every
#: window's block maxima come from them (noise_block_maxima), so the windows of a profile's
#: template groups share one simulation. ~6 MB each at n = 4096.
_NOISE_RECORDS = OrderedDict()
_RECORDS_MAX = 16
#: Records a row the simulation's first call has room for, in units of ln L + 3 for a running
#: maximum over L lags (_simulate); every later call's room is measured.
_ROOM = 2.0
#: Rows the simulation's first call runs (_simulate): enough to measure each statistic's records
#: a row to a few percent, few enough that room for twice the usual is a few MB.
_PILOT = 2048
#: Standard errors past the measured records a row that a call has room for (_simulate).
_ROOM_Z = 4.0


def _grown(a, keep, size):
    """A new array of `size` elements of a's type holding a's first `keep`."""
    out = np.empty(size, a.dtype)
    out[:keep] = a[:keep]
    return out


def _simulate(p, n, bands, rows, row0, seed, signal=None, noise=True, keep_at=0.0, k0s=None):
    """Rows row0 .. row0 + rows of the gate model's one simulation (_core.simulate): with
    signal = (tab, t, fi) its records outward from the signal (none for a draw whose fine
    statistic is below keep_at at every lag), and with noise each band's records of the noise
    alone. A block's draws depend only on its row, so its noise alone is the same whichever
    call simulates it. Returns (signal records or None, noise records or None): per statistic
    and side (fine first, right then left), and per band, the records (pos, val, off); pos and
    val may be views of arrays a few percent longer."""
    from . import _core
    k0s = (0,) * len(bands) if k0s is None else tuple(int(x) for x in k0s)
    sim_extra = (k0s,) if any(k0s) else ()
    scale = (np.sqrt(p) / np.sqrt(2)).astype(np.float32)
    kmax = int(np.flatnonzero(p)[-1]) + 1
    bscale = tuple(float(_SIG / np.sqrt(p[slice(*_band_slice(n, b, k0))].sum()))
                   for b, k0 in zip(bands, k0s))
    stream = (_DOMAIN_SIGNAL << 32) | (int(seed) & 0xFFFFFFFF)
    tab, t, fi = signal if signal is not None else (None,) * 3
    # Room: a side's running maximum over L lags has about ln L + 0.58 records of white noise,
    # far fewer with the signal at its start (and none in a draw not kept), more where the
    # profile makes neighbouring lags alike (the widest band's noise up to ~1.1 (ln L + 3)), so
    # the records a row are measured, not guessed. The first call runs _PILOT rows with room for
    # _ROOM (ln L + 3) a row; each later one, the rest, with room for the mean records a row so
    # far and _ROOM_Z standard errors of the total (the mean's error over the rows to come and
    # their own spread). A call that runs out stops at the row that did not fit, and the next
    # continues from there; one that fits no row at all doubles its successor's room. Each
    # statistic's records go into one array, grown (its records so far copied) only when a call
    # needs more room than is left.
    ns = 2 * (1 + len(bands)) if signal is not None else 0
    first = [math.log(m) + 3 for m in [n] + list(bands) for _ in (0, 1)] if signal is not None else []
    first = [_ROOM * c for c in first + ([math.log(b) + 3 for b in bands] if noise else [])]
    nq = len(first)
    off = [np.empty(rows + 1, np.int64) for _ in range(nq)]
    pos = [np.empty(0, np.int32) for _ in range(nq)]
    val = [np.empty(0, np.float32) for _ in range(nq)]
    have = [0] * nq                         # each statistic's records so far
    done, boost = 0, 1
    while done < rows:
        todo = rows - done if done else min(rows, _PILOT)
        if done:
            need = []
            for o in off:
                c = np.diff(o[:done + 1])
                spread = float(c.std()) * math.sqrt(todo * todo / done + todo)
                need.append(todo * float(c.mean()) + _ROOM_Z * spread)
        else:
            need = [c * todo for c in first]
        for q in range(nq):
            want = have[q] + int(math.ceil(boost * need[q])) + 64
            if pos[q].size < want:
                pos[q], val[q] = _grown(pos[q], have[q], want), _grown(val[q], have[q], want)
        # the call writes from the start of its arrays: records after those so far, offsets
        # from its first row on, made absolute below
        cp = [pos[q][have[q]:] for q in range(nq)]
        cv = [val[q][have[q]:] for q in range(nq)]
        co = [off[q][done:done + todo + 1] for q in range(nq)]
        sig = [tuple(x[:ns]) if signal is not None else None for x in (cp, cv, co)]
        noi = [tuple(x[ns:]) if noise else None for x in (cp, cv, co)]
        sk, nk, got = _core.simulate(scale, stream, int(row0 + done), int(todo), kmax,
                                     tuple(int(b) for b in bands), bscale, float(_SIG), tab,
                                     None if t is None else t[done:done + todo],
                                     None if fi is None else fi[done:done + todo],
                                     *sig, *noi, float(keep_at), *sim_extra)
        counts = list(sk or ()) + list(nk or ())
        for q in range(nq):
            co[q][:got + 1] += have[q]
            have[q] += counts[q]
        boost = 2 * boost if got == 0 else 1
        done += got
    recs = [(pos[q][:have[q]], val[q][:have[q]], off[q]) for q in range(nq)]
    return (tuple(recs[:ns]) if signal is not None else None,
            tuple(recs[ns:]) if noise else None)


def _join_records(parts):
    """One records array (pos, val, off) of consecutive row ranges' records, in order."""
    if len(parts) == 1:
        return parts[0]
    pos = np.concatenate([p for p, _, _ in parts])
    val = np.concatenate([v for _, v, _ in parts])
    offs, base = [np.zeros(1, np.int64)], 0
    for _, _, o in parts:
        offs.append(o[1:] + base)
        base += o[-1]
    return pos, val, np.concatenate(offs)


def _add_noise_records(key, row0, rows, recs):
    """Hold the noise records `recs` of rows row0 .. row0 + rows after those held for rows
    0 .. row0 (a simulation's blocks in order; anything else is left as held)."""
    held = _NOISE_RECORDS.get(key)
    have = 0 if held is None else held[0]
    if have != row0:
        return
    if held is not None:
        recs = tuple(_join_records([h, r]) for h, r in zip(held[1], recs))
    _NOISE_RECORDS[key] = (row0 + rows, recs)
    _NOISE_RECORDS.move_to_end(key)
    while len(_NOISE_RECORDS) > _RECORDS_MAX:
        _NOISE_RECORDS.popitem(last=False)


def _noise_records(p, n, bands, nsim, seed, k0s=None):
    """Per band, the records (pos int32, val float32, off int64) of each simulated block's
    running maximum of the band's normalised coarse statistic of the noise alone over its b
    lags, rows in order: row r's records are [off[r], off[r + 1]).

    The blocks are signal_draws' (_simulate), so a simulation of fewer blocks is a prefix of
    one of more: a request reads the prefix of a larger simulation held (a signal
    simulation's included), or extends a smaller one."""
    if k0s is None:
        k0s = tuple(band_offset(p, n, b) for b in bands)
    else:
        k0s = tuple(int(x) for x in k0s)
    extra = (k0s,) if any(k0s) else ()
    key = _key(p, n, bands, seed, *extra)
    hit = _NOISE_RECORDS.get(key)
    if hit is not None:
        _NOISE_RECORDS.move_to_end(key)
        have, recs = hit
        if nsim <= have:
            return tuple((pos[:off[nsim]], val[:off[nsim]], off[:nsim + 1]) for pos, val, off in recs)
    else:
        have, recs = 0, None
    _, new = _simulate(p, n, bands, nsim - have, have, seed, k0s=k0s)
    _add_noise_records(key, have, nsim - have, new)
    return _NOISE_RECORDS[key][1]


def noise_block_maxima(power, n, bands, nsim=_NOISE_BLOCKS, seed=_SEED, window=None):
    """Noise-only block maxima of every band's coarse statistic, (nsim, len(bands)).

    Exact for stationary Gaussian noise with output profile `power`: bins are
    independent with variance p_k; band b's coarse grid is the b-point inverse
    transform of its active band [k0, khi) wrapped to cyclic slots, normalised
    to unit per-component variance.
    `window` = (start, end) in samples is the lag range each block's search
    covers; every tier takes its maximum over the coarse lags the engine
    visits for it (hmf.c: cstart = start/R - 1, cend = ceil(end/R)), so a
    chain's noise passes are joint passes of whole-window maxima.
    """
    p = _norm_profile(power, n)
    bands = sorted(int(b) for b in bands)
    k0s = tuple(band_offset(p, n, b) for b in bands)
    extra = (k0s,) if any(k0s) else ()
    win = (0, n) if window is None else (int(window[0]), int(window[1]))
    # Each band's coarse statistic is circularly stationary over its lags (independent
    # bins), so a window's maximum depends only on how many lags it covers, not where:
    # simulate lags [0, count) per band, and windows of equal span share one simulation.
    from ._windows import coarse_lags
    # the engine's coarse lags for the window (one sample past each end)
    counts = tuple(int(c1 - c0) for c0, c1 in (coarse_lags(n, b, win[0], win[1]) for b in bands))
    key = _key(p, n, bands, int(nsim), int(seed), counts, *extra)
    hit = _NOISE_CACHE.get(key)
    if hit is not None:
        _NOISE_CACHE.move_to_end(key)
        return hit
    sim_params = (n, tuple(bands), int(nsim), int(seed), counts) + extra
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


#: CostModel's interpolation tables as arrays, per table (a model's rows do not change once
#: made): every chain priced asked np.log of the same few rows again, 117k times a job.
_LOG_TABLES = {}


def _log_table(rows, kind):
    """(log densities, values) of a CostModel table of (density, value) rows: the values as
    given ("cost") or log of their ratio to the density ("ratio"), the tuples the
    interpolations read."""
    hit = _LOG_TABLES.get((id(rows), kind))
    if hit is not None and hit[0] is rows:
        return hit[1], hit[2]
    fs = tuple(math.log(r[0]) for r in rows)
    if kind == "cost":
        vs = tuple(float(r[1]) for r in rows)
    else:
        vs = tuple(math.log(r[1] / r[0]) for r in rows)
    _LOG_TABLES[(id(rows), kind)] = (rows, fs, vs)     # rows held: the id cannot be reused
    if len(_LOG_TABLES) > 4096:
        _LOG_TABLES.pop(next(iter(_LOG_TABLES)))
    return fs, vs


def _interp_clamped(x, fs, vs):
    """Clamped piecewise-linear interpolation on small sorted tuples (fs, vs), matching np.interp."""
    if x <= fs[0]:
        return vs[0]
    if x >= fs[-1]:
        return vs[-1]
    j = 0
    last = len(fs) - 2
    while j < last and fs[j + 1] <= x:
        j += 1
    dx = fs[j + 1] - fs[j]
    if dx == 0.0:
        return vs[j + 1]
    dy = vs[j + 1] - vs[j]
    if dy == 0.0:
        return vs[j]
    return (x - fs[j]) * (dy / dx) + vs[j]


def band_forward_wanted(n, band, f, forced=None):
    """Whether a hierarchical call should forward only its tiers' bands (and then recompute
    the full spectra of the blocks its refine reads) rather than every block in full.
    Chosen from bytes: per block the full forward writes n samples and the band forward
    `band` (the widest band a tier reads), while the recompute reads and writes n for each
    block with a refined pair, so bands move fewer bytes iff that fraction f < (n - band) / 2n.
    f is the gate model's fraction for the call (_gpuhier._hier_peaks: from the chain's
    modelled refine probability), so the choice depends on the call alone; with none
    (thresholds set by hand, no reference), the bands. MF_BAND_FORWARD=0/1 forces it off or on,
    as does `forced` (a context's feed_forced: the GPU calibration times both feeds); the cost
    model prices a chain's feed by this same rule (CostModel.feed_delta)."""
    from . import _config
    if forced is None:
        forced = _config.get("MF_BAND_FORWARD")
    if forced is False or n > 65536 or band >= n:
        return False
    if forced:
        return True
    return f is None or f < (n - band) / (2.0 * n)


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

    def __init__(self, n, dense, sparse, refine, block=0.0, screen=None, feed=None):
        self.n = int(n)
        # feed: a GPU backend's per-block change from the feed `block` was measured with (the
        # band forward of the first tier's band), {"band": {B: change at widest band B},
        # "full": change with the full forward}, measured (calibrate_costs_gpu); None where
        # there is one feed (the CPU). A call takes the band forward or the full one by the
        # backend's own rule (band_forward_wanted), and so does the model
        # (feed_delta).
        self.feed = None if not feed else {
            "band": {int(b): float(v) for b, v in feed["band"].items()},
            "full": float(feed["full"])}
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
        fs, vs = _log_table(rows, "cost")
        return _interp_clamped(math.log(max(f, 1e-12)), fs, vs)

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
                               getattr(self, "direct_lag", None), getattr(self, "direct_single", True),
                               getattr(self, "direct_frac", 1.0),
                               getattr(self, "direct_base", 0.0),
                               getattr(self, "direct_multi_frac", 0.0),
                               None if self.feed is None else (tuple(sorted(self.feed["band"].items())),
                                                               self.feed["full"]))
        return sig

    def to_dict(self):
        return {"n": self.n, "block": self.block, "dense": self.dense,
                "feed": None if self.feed is None else {
                    "band": {str(b): v for b, v in self.feed["band"].items()},
                    "full": self.feed["full"]},
                "sparse": self._sparse, "refine": self._refine, "screen": self.screen}

    @classmethod
    def from_dict(cls, d):
        return cls(d["n"], d["dense"], d["sparse"], d["refine"], block=d.get("block", 0.0),
                   screen=d.get("screen"), feed=d.get("feed"))

    def screen_reach(self, b, reach1):
        """Modelled Q15 pass fraction from measured screen/float excess."""
        sc = self.screen.get(int(b))
        if sc is None or not sc["excess"]:
            return None
        fs, ratio = _log_table(sc["excess"], "ratio")
        return min(1.0, max(reach1, 1e-6) * math.exp(
            _interp_clamped(math.log(max(reach1, 1e-6)), fs, ratio)))

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

    def feed_delta(self, chain, reach, ntemplates, hw=None):
        """Per-pair change from `block` of the forward this chain's calls take: the band
        forward at its widest band, or the full forward, as the backend decides from the
        chain's modelled refine probability reach[len(chain)] (band_forward_wanted,
        the call's own rule; 0 when direct refine claims the band forward), each measured
        per block and spread over the templates. 0 where the backend has one feed."""
        if self.feed is None or not ntemplates:
            return 0.0
        top = int(max(chain))
        r = (0.0 if (hw is not None and self.prices_direct(chain))
             else min(max(float(reach[len(chain)]), 0.0), 1.0))
        if band_forward_wanted(self.n, top, r) and top in self.feed["band"]:
            per = self.feed["band"][top]
        else:
            per = self.feed["full"]
        return per / float(ntemplates)

    def with_direct(self, lag_price, single_tier=True, fraction=1.0, base=0.0, multi_frac=0.0):
        """A copy that also prices a direct refine at lag_price ticks per lag of its window
        (HierarchicalFilter._direct_price): a chain whose last tier reports its coarse lag
        then refines a pair, with a window of half-width h coarse samples, at the cheaper of
        the measured whole-block refine and base + (2 h n / b + 1) * lag_price, b its last band
        (refine_for; the window scales with n / b, so it favours chains ending in a wider band),
        weighted by the fraction of blocks eligible for direct refine."""
        import copy
        cm = copy.copy(self)
        cm.direct_lag = float(lag_price)
        # single_tier False: a one-tier chain's tier runs on the CPU's FP16 gate, which reports
        # no lag, so its survivors refine by transform (hmf.c hmf_tier.lagged).
        cm.direct_single = bool(single_tier)
        cm.direct_frac = float(fraction)
        cm.direct_base = float(base)
        cm.direct_multi_frac = float(multi_frac)
        cm._sig = None
        return cm

    def unscreened(self):
        """A copy that prices no Q15 screen: the costs of a plan whose first tier runs without
        one (a pinned chain's, HierarchicalFilter._arm_q15)."""
        import copy
        cm = copy.copy(self)
        cm.screen = {}
        cm._sig = None
        return cm

    def prices_direct(self, chain):
        """Whether this model prices a direct refine for chain (with_direct)."""
        return (getattr(self, "direct_lag", None) is not None
                and getattr(self, "direct_frac", 1.0) > 0.0
                and (len(chain) > 1 or getattr(self, "direct_single", True)))

    def refine_for(self, chain, f, hw=None):
        """Ticks per refined pair for this chain at refine density f, with the direct refine's
        window half-width hw (None: the whole-block refine)."""
        r = self.refine(f)
        if hw is not None and self.prices_direct(chain):
            d = getattr(self, "direct_base", 0.0) + self.direct_lag * (2 * int(hw) * (self.n // int(chain[-1])) + 1)
            mfrac = getattr(self, "direct_multi_frac", 0.0)
            if mfrac > 0.0:
                b_last = int(chain[-1])
                if b_last in self._sparse:
                    d += mfrac * self.sparse(b_last, f)
            d = min(r, d)
            frac = getattr(self, "direct_frac", 1.0)
            r = (1.0 - frac) * r + frac * d
        return r

    def chain_cost(self, chain, reach, hw=None):
        """reach[i] = P(a pair reaches tier i+1) for i = 0..k-1, reach[k] = P(reaches refine);
        hw the direct refine's half-width (refine_for)."""
        c, screened = self.first_tier(chain[0], reach[1] if len(reach) > 1 else 1.0)
        for i in range(1, len(chain)):
            c += reach[i] * self.sparse(chain[i], reach[i])
        # A one-tier chain behind the Q15 screen has no coarse lag to refine around (hmf.c: the
        # screen reports none), so its survivors refine by transform, as the engine runs them.
        f = reach[len(chain)]
        c += f * (self.refine(f) if screened and len(chain) == 1 else self.refine_for(chain, f, hw))
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


def _reach(N, cols, thresholds):
    """Cumulative noise pass probabilities through the chain."""
    alive = np.ones(N.shape[0], bool)
    out = [1.0]
    for c, g in zip(cols, thresholds):
        alive &= N[:, c] >= g
        out.append(float(alive.mean()))
    return out


_KEPT = OrderedDict()
_KEPT_MAX = 4096


def kept_draws(sig, bands, chain, snr):
    """Coarse maxima of `chain`'s tiers for the draws the fine stage keeps (fine max >= snr).

    signal_draws' maxima are over the whole searched window, as the engine's (hmf.c), so a
    tier whose gate falls below the window's noise floor passes the draws a noise peak
    elsewhere in the block carries. Memoised per draws (by identity, held so they cannot be
    reused), chain and snr: every template group pricing a profile asks again."""
    C, F = sig[0], sig[1]
    cols = [bands.index(b) for b in chain]
    key = (id(C), id(F), tuple(cols), float(snr))
    hit = _KEPT.get(key)
    if hit is not None and hit[0] is C and hit[1] is F:
        _KEPT.move_to_end(key)
        return hit[2]
    # When F broadcasts one fine maximum across all columns (signal_draws), filter C once per
    # (C, F, snr) and slice columns per chain rather than copying and scanning F[:, cols].
    if F.ndim == 2 and F.shape[1] > 0 and F.strides[1] == 0:
        bkey = ("kept_all", id(C), id(F), float(snr))
        bhit = _KEPT.get(bkey)
        if bhit is not None and bhit[0] is C and bhit[1] is F:
            _KEPT.move_to_end(bkey)
            c_kept = bhit[2]
        else:
            c_kept = C[F[:, 0] >= snr]
            _KEPT[bkey] = (C, F, c_kept)
            while len(_KEPT) > _KEPT_MAX:
                _KEPT.popitem(last=False)
        out = c_kept[:, cols]
    else:
        keep = F[:, cols[0]] >= snr
        for c in cols[1:]:
            keep = keep | (F[:, c] >= snr)
        out = C[keep][:, cols]
    out.setflags(write=False)
    _KEPT[key] = (C, F, out)
    while len(_KEPT) > _KEPT_MAX:
        _KEPT.popitem(last=False)
    return out


def _smallest(col, m):
    """Indices of col's m smallest values, in ascending order of value (O(len) selection)."""
    m = min(int(m), col.size)
    if m <= 0:
        return np.empty(0, np.int64)
    idx = np.argpartition(col, m - 1)[:m] if m < col.size else np.arange(col.size)
    return idx[np.argsort(col[idx], kind="stable")]


#: plan_chain's candidates per (draws, chain, prune, half-widths): they do not depend on the
#: cost model, so every template group pricing the same profile and window reuses them.
_CAND_CACHE = OrderedDict()
_CAND_CACHE_MAX = 4096


def _halves(x):
    """(search half, fit half) of the detections x: its even rows and its odd rows, each
    contiguous. The detections are independent draws in simulation order, so the halves are
    independent of each other."""
    key = ("halves", id(x))
    hit = _KEPT.get(key)
    if hit is not None and hit[0] is x:
        _KEPT.move_to_end(key)
        return hit[1], hit[2]
    a = np.ascontiguousarray(x[0::2])
    b = np.ascontiguousarray(x[1::2])
    a.setflags(write=False)
    b.setflags(write=False)
    _KEPT[key] = (x, a, b)
    while len(_KEPT) > _KEPT_MAX:
        _KEPT.popitem(last=False)
    return a, b


def _distances(sig, lags, bands, chain, snr, n):
    """Per detection (kept_draws' rows), how far the fine maximum lies from the chain's last
    tier's coarse maximum, in that tier's coarse samples: the direct refine's window of
    half-width h around the coarse maximum holds the fine peak iff this is at most h
    (hmf.c refine_direct_pair)."""
    F = sig[1]
    fat, cat = lags
    b = int(chain[-1])
    col = bands.index(b)
    key = ("dist", id(F), id(fat), id(cat), col, b, float(snr), int(n))
    hit = _KEPT.get(key)
    if hit is not None and hit[0] is F and hit[1] is fat and hit[2] is cat:
        _KEPT.move_to_end(key)
        return hit[3]
    keep = F[:, 0] >= snr
    out = np.abs(fat[keep] - cat[keep, col]) / (n // b)
    out.setflags(write=False)
    _KEPT[key] = (F, fat, cat, out)
    while len(_KEPT) > _KEPT_MAX:
        _KEPT.popitem(last=False)
    return out


def _all_halfwidths(dist, allow):
    """Cost-independent candidate half-widths (None, hmin, ...) for search half `dist`."""
    if dist is None or allow < 0:
        return (None,)
    key = ("hws", id(dist), int(allow))
    hit = _KEPT.get(key)
    if hit is not None and hit[0] is dist:
        _KEPT.move_to_end(key)
        return hit[1]
    if dist.size > allow:
        kth = dist.size - 1 - allow
        hmin = max(1, int(math.ceil(np.partition(dist, kth)[kth])))
    else:
        hmin = 1
    up = np.ceil(dist[dist > hmin]).astype(np.int64)
    out = (None,) + tuple(sorted({hmin} | {int(h) for h in up}))
    _KEPT[key] = (dist, out)
    while len(_KEPT) > _KEPT_MAX:
        _KEPT.popitem(last=False)
    return out


def _halfwidths(dist, allow, cost, chain, n, all_hws=None):
    """The direct refine's candidate half-widths for `chain` on the search half (dist its
    detections' _distances): None, the whole-block refine, which loses no detection; and,
    where the cost model prices a direct refine for the chain (CostModel.prices_direct), each
    whole number of coarse samples at which a different set of the detections lies beyond
    it, from the smallest leaving at most `allow` of them beyond it (gatemodel.
    window_allowance; -1: none may be missed) to the largest whose window the model prices
    below its dearest whole-block refine. Each is the smallest half-width with its set, so the
    cheapest window losing those detections."""
    if dist is None or cost is None or allow < 0 or not cost.prices_direct(chain):
        return (None,)
    R = n // int(chain[-1])
    top = max(v for _, v in cost._refine)
    dbase = getattr(cost, "direct_base", 0.0)
    hmax = int(((top - dbase) / cost.direct_lag - 1.0) // (2 * R))      # 2 h R + 1 lags priced below top
    if all_hws is None:
        all_hws = _all_halfwidths(dist, allow)
    if len(all_hws) < 2 or hmax < all_hws[1]:
        return (None,)
    return (None,) + tuple(h for h in all_hws[1:] if h <= hmax)


class _LazyPlan(dict):
    """A plan_chain dict whose fit-half thresholds and noise reach materialize on first read."""

    __slots__ = ("_pending",)

    def __init__(self, eager, pending):
        super().__init__(eager)
        self._pending = pending

    def _materialize(self):
        pending = self._pending
        if pending is None:
            return
        self._pending = None
        B, dB, th, hw, fd, noise, cols = pending
        thresholds, halfwidth = _fit(B, dB, th, hw, fd)
        super().__setitem__("thresholds", thresholds)
        super().__setitem__("reach", tuple(_reach(noise, cols, thresholds)))
        super().__setitem__("halfwidth", halfwidth)

    def __getitem__(self, key):
        if not super().__contains__(key) and self._pending is not None:
            self._materialize()
        return super().__getitem__(key)

    def get(self, key, default=None):
        if not super().__contains__(key) and self._pending is not None:
            self._materialize()
        return super().get(key, default)

    def __contains__(self, key):
        if super().__contains__(key):
            return True
        if self._pending is not None:
            self._materialize()
            return super().__contains__(key)
        return False

    def __len__(self):
        if self._pending is not None:
            self._materialize()
        return super().__len__()

    def __iter__(self):
        if self._pending is not None:
            self._materialize()
        return super().__iter__()

    def keys(self):
        if self._pending is not None:
            self._materialize()
        return super().keys()

    def values(self):
        if self._pending is not None:
            self._materialize()
        return super().values()

    def items(self):
        if self._pending is not None:
            self._materialize()
        return super().items()

    def copy(self):
        if self._pending is not None:
            self._materialize()
        return dict(self)

    def __eq__(self, other):
        if self._pending is not None:
            self._materialize()
        if isinstance(other, _LazyPlan) and other._pending is not None:
            other._materialize()
        return super().__eq__(other)

    def __repr__(self):
        if self._pending is not None:
            self._materialize()
        return super().__repr__()

    def __reduce__(self):
        if self._pending is not None:
            self._materialize()
        return (dict, (dict(self),))


def plan_chain(sig, noise, bands, chain, fd, cost, n, snr, prune=False, ntemplates=None,
               memo=None, lags=None, lazy_fit=False, offsets=None):
    """The thresholds and direct-refine half-width for `chain` that meet the false-dismissal
    budget fd at minimum modelled cost.

    sig, noise: signal_draws / noise_block_maxima over `bands` and the same window; lags: the
    draws' lags (signal_draws(..., lags_too=True)), for the direct refine's window where the
    cost model prices one. Returns dict(chain, thresholds, reach, halfwidth, cost, q15,
    search), or None when fd cannot be resolved: the thresholds and the half-width (None:
    the whole-block refine) the filter runs with and the noise share reaching each tier and
    the refine under them; the modelled cost, q15 and `search` (its thresholds, reach,
    half-width and the search half's detections its window misses, of a budget of K) of the
    plan as searched, which every choice ranks plans by.

    The detections fall into two independent halves (_halves), and the plan's dismissal is
    a fraction of the detections: those some tier dismisses or the direct refine's window
    misses, together.

    The SEARCH half decides the plan's structure. Every split of its budget of K dismissed
    detections between the tiers (over the shares _SPLIT) and every candidate half-width
    (_halfwidths: windows missing at most gatemodel.window_allowance of the detections, which
    count against the same K) gives candidate thresholds, and the one the cost model prices
    cheapest wins, the earliest on a tie. A search keeps the candidate those draws flatter,
    so its dismissal on them is not its dismissal: nothing it chooses is judged on them.

    The FIT half sets the thresholds: the search's, every tier moved by one shift fitted to
    the fit half (_fit). Given the search half, the fit half is independent of the plan's
    structure, so the plan's dismissal has mean fd and the tail gatemodel.fit_order sets,
    whatever the search and every choice made from it (choose_chain's among chains included).

    The search's candidates do not depend on the cost model; only their pricing does. Its
    selection works on each column's K-or-so smallest values (a selection, not a sort) and
    on the few dismissed draws' indices, and carries noise passes down the split search, so
    candidates sharing a prefix share its work. memo, a key naming the draws (_choose_chain
    passes the profile, n, window and draw parameters), caches the candidates, so another
    template group or cost model prices them without searching again.
    """
    cols = [bands.index(b) for b in chain]
    A, B = _halves(kept_draws(sig, bands, chain, snr))
    K = int(round(float(fd) * (A.shape[0] + 1))) - 1      # the search half's budget, as the fit's
    fit_j = int(round(float(fd) * (B.shape[0] + 1)))
    if K < 0 or fit_j < 1 or fit_j > B.shape[0]:
        return None
    dA = dB = dA_all = None
    allow = -1
    if lags is not None:
        dA_all, dB_all = _halves(_distances(sig, lags, bands, chain, snr, n))
        allow = _gm.window_allowance(float(fd), A.shape[0], B.shape[0])
        if cost is not None and cost.prices_direct(chain):
            dA, dB = dA_all, dB_all
    all_hws = _all_halfwidths(dA_all, allow)
    hws = _halfwidths(dA, allow, cost, chain, n, all_hws=all_hws)
    eff_prune = bool(prune) and len(chain) > 1
    key = None if memo is None else tuple(memo) + (tuple(int(b) for b in chain), eff_prune, all_hws)
    hit = _CAND_CACHE.get(key) if key is not None else None
    if hit is not None and hit[0] is sig[0] and hit[1] is noise:
        _CAND_CACHE.move_to_end(key)
        cands = hit[2]
    else:
        cand_hws = all_hws if key is not None else hws
        dead = tuple(np.empty(0, np.int64) if h is None else np.flatnonzero(dA_all > h)
                     for h in cand_hws)
        cands = _chain_candidates(A, noise, cols, K, eff_prune, dead)
        if key is not None:
            _CAND_CACHE[key] = (sig[0], noise, cands)
            while len(_CAND_CACHE) > _CAND_CACHE_MAX:
                _CAND_CACHE.popitem(last=False)
    best = None
    has_feed = bool(ntemplates and getattr(cost, "feed", None))
    k = len(chain)
    # Hoist prefix tier costs across candidate half-widths when pricing on CostModel (k >= 2)
    if isinstance(cost, CostModel) and k >= 2 and not has_feed:
        b0 = chain[0]
        later = chain[1:]
        prices_dir = cost.prices_direct(chain)
        dlag = getattr(cost, "direct_lag", 0.0) if prices_dir else 0.0
        dbase = getattr(cost, "direct_base", 0.0) if prices_dir else 0.0
        dmfrac = getattr(cost, "direct_multi_frac", 0.0) if prices_dir else 0.0
        dfrac = getattr(cost, "direct_frac", 1.0) if prices_dir else 1.0
        b_last = int(chain[-1]) if prices_dir else 0
        has_last_sparse = bool(prices_dir and dmfrac > 0.0 and b_last in cost._sparse)
        R = n // b_last if prices_dir else 0
        for pth, preach, lasts in cands:
            c_prefix, _ = cost.first_tier(b0, preach[1])
            for idx_t, bt in enumerate(later, 1):
                ri = preach[idx_t]
                c_prefix += ri * cost.sparse(bt, ri)
            for hw, last in zip(hws, lasts):
                if last is None:
                    continue
                f = last[1]
                r_cost = cost.refine(f)
                if hw is not None and prices_dir:
                    d_cost = dbase + dlag * (2 * int(hw) * R + 1)
                    if has_last_sparse and f >= 0.05:
                        d_cost += dmfrac * cost.sparse(b_last, f)
                    d_cost = min(r_cost, d_cost)
                    r_cost = (1.0 - dfrac) * r_cost + dfrac * d_cost
                c = c_prefix + f * r_cost
                if best is None or c < best[0]:
                    best = (float(c), pth + (last[0],), preach + (f,), hw)
    else:
        for pth, preach, lasts in cands:
            for hw, last in zip(hws, lasts):
                if last is None:
                    continue
                th, reach = pth + (last[0],), preach + (last[1],)
                c = cost.chain_cost(chain, list(reach), hw) if cost is not None else _flop_cost(chain, list(reach), n)
                if has_feed:
                    # the change from the feed `block` was measured with; pick_stable's tie window
                    # is absolute-valued, so a change that takes a total below zero still compares
                    c += cost.feed_delta(chain, list(reach), ntemplates, hw)
                if best is None or c < best[0]:
                    best = (float(c), th, reach, hw)
    if best is None:
        return None
    c, th, reach, hw = best
    q15 = bool(cost.first_tier(chain[0], reach[1])[1]) if hasattr(cost, "first_tier") else False
    missed = 0 if hw is None else int(np.count_nonzero(dA > hw))
    search_info = dict(thresholds=th, reach=reach, halfwidth=hw, missed=missed, K=K)
    offs = (0,) * len(chain) if offsets is None else tuple(int(x) for x in offsets)
    if lazy_fit:
        return _LazyPlan(
            dict(chain=tuple(chain), offsets=offs, cost=c, q15=q15, search=search_info),
            (B, dB, th, hw, fd, noise, cols),
        )
    fit = _fit(B, dB, th, hw, fd)
    if fit is None:
        return None
    thresholds, halfwidth = fit
    return dict(chain=tuple(chain), offsets=offs, thresholds=thresholds,
                reach=tuple(_reach(noise, cols, thresholds)), halfwidth=halfwidth, cost=c,
                q15=q15, search=search_info)


def _fit(B, dist, thresholds, hw, fd):
    """The plan's (thresholds, half-width) from the fit half B (M, k) of the detections, dist
    their _distances (None without a direct refine): the search's `thresholds` and half-width
    `hw`, every tier moved by one shift s, or None when M draws cannot place the budget.

    A detection passes every tier at shift s iff s <= its score, the smallest of its coarse
    maxima less their thresholds; one the window misses (dist > hw) is dismissed at any s. s
    is the j-th smallest score, j = round(fd (M + 1)) (gatemodel.fit_order), so j - 1 of B
    are dismissed, and on fresh draws the plan's dismissal is the j-th smallest of M uniforms
    (gatemodel.fit_order): its mean is fd whatever the search chose.

    Where the window alone misses j of B, the plan refines by transform instead (half-width
    None), which misses none, and the tiers take the whole budget. That branch is taken on B,
    so the plan is then not the j-th smallest uniform (fitted on the detections that showed
    the window failing, 17 such plans dismissed 1.14 fd on average; tools/split_bias.py,
    2026-10-29): the search offers only windows for which the branch has at most the
    probability the fit's tail leaves (gatemodel.window_allowance, at most 0.002), so a plan
    exceeds 1.25 fd with probability at most gatemodel._TAIL_SHARE with the branch included,
    and its mean moves by at most that probability times the branch's dismissal."""
    M = B.shape[0]
    j = int(round(float(fd) * (M + 1)))
    if j < 1 or j > M:
        return None
    th = np.asarray(thresholds, np.float64)
    score = (B - th).min(axis=1)
    if hw is not None:
        out = dist > hw
        if np.count_nonzero(out) >= j:
            hw = None
        else:
            score[out] = -np.inf
    s = float(np.partition(score, j - 1)[j - 1])
    return tuple(max(float(g) + s, 0.0) for g in th), hw


def _chain_candidates(S, noise, cols, K, prune, dead):
    """plan_chain's search on the search half's detections S (M, k), each tier's coarse
    maxima, with noise the noise blocks' maxima and cols the chain's columns of them: every
    split of the budget of K dismissed detections it considers, in its order, as (earlier
    thresholds, earlier reach, lasts). The earlier tiers' thresholds and the noise shares
    reaching each tier; and per set in `dead`, detections dismissed whatever the tiers (the
    direct refine's window's misses at one half-width), the last tier's threshold, the K-th
    from the budget, and the noise share it passes on, or None where the set leaves it no
    budget. A split the last tier has budget for under no set is left out."""
    M, k = S.shape
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
    marks = np.zeros(M, np.uint8)
    splits = _SPLIT
    if k > 1:
        firsts = [int(math.floor(a * K)) for a in splits]
        g0 = min((float(low_val[0][i]) for i in firsts if i >= 1), default=None)
        rows = noise[:, cols[0]] >= g0 if g0 is not None else np.zeros(Nn, bool)
        Nc = np.ascontiguousarray(noise[rows][:, cols].T)
    else:
        Nc = np.ascontiguousarray(noise[:, cols].T)

    def consider(prefix, ndead, alive, fracs):
        """Given thresholds for tiers 0..k-2, the last uses the remaining budget: ndead draws
        are dismissed (marked), alive the noise blocks passing every earlier tier (None: all
        of them), fracs those tiers' pass rates."""
        if prune and any(r > _USELESS_PASS for r in fracs):
            # choosing: a tier that passes most of its pairs on to ANOTHER TIER only adds its
            # own cost. (The last tier's pass rate into the refine is not judged here: at a
            # low snr every chain refines most pairs, and the cost already says so.)
            return
        lasts = []
        for D in dead:
            extra = D[marks[D] == 0]
            nd = ndead + int(extra.size)
            rem = K - nd
            at = None
            if 0 <= rem < M - nd:
                # the rem-th smallest last-tier value among draws not yet dismissed
                marks[extra] = 255
                pos = np.flatnonzero(marks[last_order] == 0)
                marks[extra] = 0
                at = int(pos[rem]) if pos.size > rem else None
            if at is None:
                lasts.append(None)
                continue
            g = float(last_val[at])
            hit = Nc[-1] >= g
            if alive is not None:
                hit &= alive
            lasts.append((g, int(np.count_nonzero(hit)) / Nn))
        if any(x is not None for x in lasts):
            out.append((tuple(prefix), (1.0,) + tuple(fracs), tuple(lasts)))

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
            new = cand[marks[cand] == 0]
            marks[new] = i + 1
            an = Nc[i] >= g
            if alive is not None:
                an &= alive
            rec(i + 1, prefix + [g], remaining - share, ndead + int(new.size), an,
                fracs + [int(np.count_nonzero(an)) / Nn])
            marks[new] = 0

    if _C_SEARCH and all(len(o) == K + 1 for o in low) and len(last_order) == K + 1:
        from . import _core
        return _core.chain_candidates(np.ascontiguousarray(S, np.float32), Nc, tuple(low),
                                      tuple(np.ascontiguousarray(v, np.float32) for v in low_val),
                                      np.ascontiguousarray(last_order, np.int64),
                                      np.ascontiguousarray(last_val, np.float32),
                                      tuple(float(a) for a in splits), int(K), int(Nn), bool(prune),
                                      float(_USELESS_PASS),
                                      tuple(np.ascontiguousarray(d, np.int64) for d in dead))
    rec(0, [], 1.0, 0, None, [])
    return out


#: _chain_candidates runs its search in C (_core.chain_candidates; the Python recursion above
#: it is the reference, identical candidates in the same order, ~1.3 ms a call of Python and
#: small array operations on dev2). False runs the Python one (tests compare them).
_C_SEARCH = True


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


def _flop_cost(chain, reach, n):
    """Fallback when no measured table exists: transform-size proxy b log b per tier, n log n per refine."""
    c = chain[0] * math.log2(chain[0])
    for i in range(1, len(chain)):
        c += reach[i] * chain[i] * math.log2(chain[i])
    return c + reach[len(chain)] * n * math.log2(n)


_CHOICE_CACHE = OrderedDict()
_OFFSET_CACHE = OrderedDict()


def _cached_band_offsets(p, sig_p, n, floor):
    """Return cached (k0_cand, usable_bands_list) for normalized profile `p` at `(n, floor)`."""
    off_key = (sig_p, int(n), int(floor))
    hit = _OFFSET_CACHE.get(off_key)
    if hit is not None:
        _OFFSET_CACHE.move_to_end(off_key)
        return hit
    c_bands = candidate_bands(n, floor)
    k0_cand = tuple(band_offset(p, n, b) for b in c_bands)
    bands = [b for b, k0 in zip(c_bands, k0_cand) if p[slice(*_band_slice(n, b, k0))].sum() > 0]
    res = (c_bands, k0_cand, bands)
    _cache_put(_OFFSET_CACHE, off_key, res)
    return res


def choose_chain(power, n, snr, fd, cost=None, max_tiers=3, floor=_MIN_BAND, nsim=None, window=None,
                 ntemplates=None, nsamp=None):
    """Price every chain and return (best, all plans sorted by cost): plan_chain's plans,
    ranked by their searched cost, (None, []) when none can be planned. nsamp: the
    detections to draw (default: model_draws').

    Cached like the draws it is built from: by profile signature, and reused for
    profiles within the cosine similarity gatemodel applies to them.
    """
    p = _norm_profile(power, n)
    win = None if window is None else (int(window[0]), int(window[1]))
    dsamp, dsim = model_draws(fd)
    nsamp = dsamp if nsamp is None else int(nsamp)
    nsim = dsim if nsim is None else int(nsim)
    if nsamp is None:
        return None, []          # the tail bound needs more detections than the model holds
    sig_p = _gm._profile_sig(p)
    c_bands, k0_cand, bands = _cached_band_offsets(p, sig_p, n, floor)
    extra = (k0_cand,) if any(k0_cand) else ()
    params = (n, float(snr), float(fd), int(max_tiers), int(floor), int(nsim), int(nsamp), win, _cost_sig(cost),
              # ntemplates prices the feed
              None if not getattr(cost, "feed", None) else int(ntemplates or 0)) + extra
    key = (sig_p,) + params
    hit = _CHOICE_CACHE.get(key)
    if hit is not None:
        _CHOICE_CACHE.move_to_end(key)
        return hit
    unit, hit = _similar_get("choice", p, params)
    if hit is not None:
        _cache_put(_CHOICE_CACHE, key, hit)
        return hit
    offsets_map = dict(zip(c_bands, k0_cand))
    out = _choose_chain(p, n, snr, fd, cost, max_tiers, floor, nsim, win, ntemplates, nsamp,
                        bands=bands, offsets_by_band=offsets_map)
    _cache_put(_CHOICE_CACHE, key, out)
    _similar_put("choice", unit, params, out)
    return out


def _choose_chain(power, n, snr, fd, cost, max_tiers, floor, nsim, window, ntemplates=None,
                  nsamp=None, bands=None, offsets_by_band=None):
    if bands is None:
        bands = usable_bands(power, n, floor)
    if not bands:
        return None, []
    nsamp = _gm._nsamp_for(fd) if nsamp is None else int(nsamp)
    drawn = signal_draws(power, n, bands, snr, nsamp, window=window, lags_too=True)
    if drawn is None:
        return None, []
    sig, lags = drawn
    noise = noise_block_maxima(power, n, bands, nsim=nsim, window=window)
    memo = ("choose", id(sig[0]), id(noise), n, float(snr), float(fd), tuple(bands), window,
            int(nsim), int(nsamp))
    if offsets_by_band is None:
        offsets_by_band = {b: band_offset(power, n, b) for b in bands}
    plans = []
    for chain in enumerate_chains(n, max_tiers, floor, bands=bands):
        offs = tuple(offsets_by_band[b] for b in chain)
        pl = plan_chain(sig, noise, bands, list(chain), fd, cost, n, snr, prune=True,
                        ntemplates=ntemplates, memo=memo, lags=lags, lazy_fit=True, offsets=offs)
        if pl is not None:
            plans.append(pl)
    plans.sort(key=lambda d: d["cost"])
    # Ties (within the calibration's process-to-process noise) go to the cheaper chain on the
    # calibration-free flop proxy: deterministic for a given profile, and still a cost. Both
    # are the searched plans' (plan_chain), so the choice is made on the search half only.
    best = pick_stable(plans, lambda d: d["cost"],
                       lambda d: (_flop_cost(d["chain"], d["search"]["reach"], n), d["chain"]))
    return best, plans


_PLAN_CACHE = OrderedDict()


#: calibrate_costs(n, ntemplates, ...) measures this machine's tier costs at transform size n
#: through the engine itself and returns the CostModel the chain choice prices with, kept in
#: MF_COST_FILE when it is set. It runs hierarchical plans, which sit above this module, so
#: it is matchedfilter._calibration.calibrate_costs (which documents the measurement), bound
#: to this name when that module loads (the package loads it): one function, one set of
#: defaults, wherever it is called from.
calibrate_costs = None


def chain_thresholds(power, n, snr, fd, chain, cost=None, floor=_MIN_BAND, nsim=None, window=None,
                     nsamp=None):
    """The plan (plan_chain's: thresholds, reach, the direct refine's half-width where the
    cost model prices one, cost) for one given chain under `power`, or None where it cannot
    be planned. nsamp: the detections to draw (default: model_draws').

    Called whenever a plan's reference changes, inside the caller's filtering,
    so results are cached -- by profile signature, and reused for profiles
    within the same cosine similarity gatemodel applies to its draws.
    """
    p = _norm_profile(power, n)
    chain = tuple(int(b) for b in chain)
    win = None if window is None else (int(window[0]), int(window[1]))
    dsamp, dsim = model_draws(fd)
    nsamp = dsamp if nsamp is None else int(nsamp)
    nsim = dsim if nsim is None else int(nsim)
    if nsamp is None:
        return None              # the tail bound needs more detections than the model holds
    sig_p = _gm._profile_sig(p)
    ch_off_key = ("chain", sig_p, int(n), chain)
    k0_chain = _OFFSET_CACHE.get(ch_off_key)
    if k0_chain is None:
        k0_chain = tuple(band_offset(p, n, b) for b in chain)
        _cache_put(_OFFSET_CACHE, ch_off_key, k0_chain)
    else:
        _OFFSET_CACHE.move_to_end(ch_off_key)
    extra = (k0_chain,) if any(k0_chain) else ()
    key = (sig_p, n, chain, float(snr), float(fd), win, int(nsim), int(nsamp), _cost_sig(cost), *extra)
    hit = _PLAN_CACHE.get(key)
    if hit is not None:
        _PLAN_CACHE.move_to_end(key)
        return hit
    sim_params = (n, chain, float(snr), float(fd), win, int(nsim), int(nsamp), _cost_sig(cost)) + extra
    unit, hit = _similar_get("plan", p, sim_params)
    if hit is not None:
        _cache_put(_PLAN_CACHE, key, hit)
        return hit
    _, _, bands = _cached_band_offsets(p, sig_p, n, floor)
    if not set(chain) <= set(bands):
        return None
    drawn = signal_draws(p, n, bands, snr, nsamp, window=window, lags_too=True)
    if drawn is None:
        return None
    sig, lags = drawn
    noise = noise_block_maxima(p, n, bands, nsim=nsim, window=window)
    memo = ("choose", id(sig[0]), id(noise), n, float(snr), float(fd), tuple(bands), win,
            int(nsim), int(nsamp))
    out = plan_chain(sig, noise, bands, list(chain), fd, cost, n, snr, memo=memo, lags=lags,
                     offsets=k0_chain)
    _cache_put(_PLAN_CACHE, key, out)
    _similar_put("plan", unit, sim_params, out)
    return out


_INV_RT2 = 1.0 / math.sqrt(2.0)
_INV_RT2PI = 1.0 / math.sqrt(2.0 * math.pi)
_BOUND_LOG_INV_DELTA = 25.33
_BOUND_CACHE = OrderedDict()
_BOUND_PRICE_CACHE = OrderedDict()


def _norm_sf_1d(z_arr):
    return np.array([0.5 * math.erfc(float(z) * _INV_RT2) for z in z_arr], dtype=np.float64)


def _gauss_tail_ub(t):
    t = np.maximum(np.asarray(t, dtype=np.float64), 0.0)
    mills_ub = np.minimum(math.sqrt(0.5 * math.pi), 2.0 / (t + np.sqrt(t * t + 2.0)))
    return mills_ub * np.exp(-0.5 * np.minimum(t * t, 1400.0))


def _gauss_tail_lb(t):
    t = np.maximum(np.asarray(t, dtype=np.float64), 0.0)
    mills_lb = 2.0 / (t + np.sqrt(t * t + 4.0))
    return mills_lb * np.exp(-0.5 * np.minimum(t * t, 1400.0))


def _norm_cdf_lb(z):
    z = np.asarray(z, dtype=np.float64)
    return np.where(z >= 0.0,
                    np.maximum(0.5, 1.0 - _gauss_tail_ub(z) * _INV_RT2PI),
                    _gauss_tail_lb(-z) * _INV_RT2PI)


def _norm_cdf_ub(z):
    z = np.asarray(z, dtype=np.float64)
    return np.where(z >= 0.0,
                    1.0 - _gauss_tail_lb(z) * _INV_RT2PI,
                    np.minimum(0.5, _gauss_tail_ub(-z) * _INV_RT2PI))


def _binom_kl(p, q):
    if q >= 1.0:
        return float("inf") if p < 1.0 else 0.0
    if q <= 0.0 or p >= q:
        return 0.0
    if p <= 0.0:
        return -math.log(max(1.0 - q, 1e-300))
    return p * math.log(p / q) + (1.0 - p) * math.log((1.0 - p) / (1.0 - q))


def _binom_lower_tail_q_needed(m_trials, k_max_fail, log_inv_delta=_BOUND_LOG_INV_DELTA):
    if k_max_fail < 0:
        return 0.0
    if k_max_fail >= m_trials:
        return float("inf")
    p = float(k_max_fail) / float(m_trials)
    target = float(log_inv_delta) / float(m_trials)
    lo, hi = p, 1.0 - 1e-15
    if _binom_kl(p, hi) < target:
        return float("inf")
    for _ in range(44):
        mid = 0.5 * (lo + hi)
        if _binom_kl(p, mid) >= target:
            hi = mid
        else:
            lo = mid
    return hi


def _binom_rate_lb(m_trials, q_true_lb, log_inv_delta=_BOUND_LOG_INV_DELTA):
    q = float(q_true_lb)
    if q <= 0.0 or m_trials < 1:
        return 0.0
    if q >= 1.0:
        return 1.0
    target = float(log_inv_delta) / float(m_trials)
    if _binom_kl(0.0, q) < target:
        return 0.0
    lo, hi = 0.0, q
    for _ in range(38):
        mid = 0.5 * (lo + hi)
        if _binom_kl(mid, q) >= target:
            lo = mid
        else:
            hi = mid
    k_lb = int(math.floor(m_trials * lo)) + 1
    return min(q, float(k_lb) / float(m_trials))


def _biv_rayleigh_ub(g, kappa):
    kappa = np.clip(np.asarray(kappa, dtype=np.float64), 0.0, 1.0)
    g = np.asarray(g, dtype=np.float64)
    g2 = g * g
    k = np.clip(kappa, 1e-12, 1.0 - 1e-12)
    omk2 = 1.0 - k * k
    sq_omk2 = np.sqrt(omk2)
    s0 = np.maximum(g * np.sqrt((1.0 - k) / (1.0 + k)), 0.0)
    s1 = np.maximum(g * sq_omk2 / k, 0.0)
    term1 = omk2 * np.exp(-np.minimum(g2 / (1.0 + k), 700.0))
    term2 = (k * k) * np.exp(-np.minimum(g2 / (2.0 * k * k), 700.0))
    integral_diff_ub = np.maximum(_gauss_tail_ub(s0) - _gauss_tail_lb(s1), 0.0)
    term3 = k * np.maximum(g, 0.0) * sq_omk2 * np.exp(-0.5 * np.minimum(g2, 1400.0)) * integral_diff_ub
    out = term1 + term2 + term3
    out = np.where(kappa <= 1e-12, np.exp(-np.minimum(g2, 700.0)), out)
    out = np.where(kappa >= 1.0 - 1e-12, np.exp(-0.5 * np.minimum(g2, 1400.0)), out)
    return np.where(g <= 0.0, 1.0, np.minimum(1.0, out))


def _pivoted_chol_pivots(gamma_b, m_full, b):
    st = max(1, m_full // 48)
    m = (m_full + st - 1) // st
    if m <= 1:
        return np.ones(1, dtype=np.float64)
    idx = (np.arange(m, dtype=np.int64) * st) % b
    dif = idx[:, None] - idx[None, :]
    c_mat = np.where(dif >= 0, gamma_b[dif % b], np.conj(gamma_b[(-dif) % b]))
    diag_rem = np.ones(m, dtype=np.float64)
    lt_mat = np.zeros((m, m), dtype=np.complex128)
    used = np.zeros(m, dtype=bool)
    vs = []
    for step in range(m):
        bi = int(np.argmax(np.where(~used, diag_rem, -1.0)))
        vr = float(diag_rem[bi]) - 1e-11 * (step + 1)
        if vr <= 0.15:
            break
        used[bi] = True
        vs.append(vr)
        proj = (np.conj(lt_mat[:step, bi])[:, None] * lt_mat[:step, :]).sum(axis=0) if step > 0 else 0.0
        col = (c_mat[:, bi] - proj) / math.sqrt(vr)
        lt_mat[step, :] = col
        diag_rem -= col.real * col.real + col.imag * col.imag
    return np.array(vs if vs else [1.0], dtype=np.float64)


def _noise_pop_lb(gamma_b, b, c_cnt, g_vals, nnz_bins=None):
    g_arr = np.asarray(g_vals, dtype=np.float64)
    if not np.all(np.isfinite(g_arr)):
        res = np.zeros_like(g_arr, dtype=np.float64)
        fin = np.isfinite(g_arr)
        if np.any(fin):
            res[fin] = _noise_pop_lb(gamma_b, b, c_cnt, g_arr[fin], nnz_bins=nnz_bins)
        return res
    m_full = min(max(int(c_cnt), 1), int(b))
    g2 = np.minimum(g_arr * g_arr, 1400.0)
    p1 = np.where(g_arr <= 0.0, 1.0, np.exp(-0.5 * g2))
    best_p = p1.copy()

    if m_full > 1:
        kappa_all = np.abs(gamma_b)
        strides = {1, 4}
        if nnz_bins is not None and nnz_bins > 0:
            strides.add(max(1, int(b) // int(nnz_bins)))
        for stride in sorted(strides):
            m = (m_full + stride - 1) // stride
            if m <= 1:
                continue
            d_idx = (np.arange(1, m, dtype=np.int64) * stride) % b
            weights = 2.0 * (m - np.arange(1, m, dtype=np.float64))
            b2 = _biv_rayleigh_ub(g_arr[:, None], kappa_all[d_idx][None, :])
            two_s2 = b2 @ weights
            s1 = m * p1
            valid = s1 > 1e-30
            ratio = np.where(valid, two_s2 / np.maximum(s1, 1e-30), 0.0)
            k_ds = 1.0 + np.floor(np.maximum(ratio, 0.0))
            p_ds = np.where(valid, (2.0 * k_ds * s1 - two_s2) / (k_ds * (k_ds + 1.0)), 0.0)
            best_p = np.maximum(best_p, np.clip(p_ds, 0.0, 1.0))

        if float(np.min(g_arr)) < 3.4:
            vs_piv = _pivoted_chol_pivots(gamma_b, m_full, b)
            p_piv = np.where(g_arr <= 0.0, 1.0,
                             1.0 - np.prod(1.0 - np.exp(-0.5 * g2[:, None] / vs_piv[None, :]), axis=1))
            best_p = np.maximum(best_p, np.clip(p_piv, 0.0, 1.0))
    return best_p


def _i0_exp_neg_a_ub(x, a):
    x2 = x * _INV_RT2
    c1 = 0.5 * (np.exp(np.clip(x - a, -700.0, 500.0)) + np.exp(-np.minimum(x + a, 700.0)))
    c2 = 0.5 * (np.exp(np.clip(x2 - a, -700.0, 500.0)) + np.exp(-np.minimum(x2 + a, 700.0)))
    c0 = np.exp(-np.minimum(a, 700.0))
    return 0.25 * (c1 + 2.0 * c2 + c0)


def _marcum_fast_ub(mu, sig, g):
    inv_2s2 = 0.5 / np.maximum(sig * sig, 1e-30)
    a = g * g * inv_2s2
    lam = mu * mu * inv_2s2
    over = g <= mu
    a_safe = np.where(over, 1.0, a)
    lam_safe = np.where(over, 0.0, lam)
    q = np.sqrt(1.0 + 4.0 * a_safe * lam_safe)
    u = np.maximum(2.0 * a_safe / (1.0 + q), 1.0 + 1e-7)
    b1 = u * np.exp(np.clip(-a_safe * (1.0 - 1.0 / u) + lam_safe * (u - 1.0), -700.0, 50.0))
    b2 = _i0_exp_neg_a_ub(2.0 * np.sqrt(a_safe * lam_safe), a_safe)
    return np.where(over, 1.0, np.minimum(1.0, np.minimum(b1, b2)))


def _disk_prob_lb(mu_hi, sig, g):
    inv_s = 1.0 / np.maximum(sig, 1e-12)
    sig_pos = sig > 1e-9
    h = 0.86 * g
    py_lb = np.maximum(0.0, 1.0 - 2.0 * _gauss_tail_ub((0.5100 * g) * inv_s) * _INV_RT2PI)
    px_lb = np.maximum(0.0, _norm_cdf_lb((h - mu_hi) * inv_s) - _norm_cdf_ub((-h - mu_hi) * inv_s))
    best = np.where(sig_pos, py_lb * px_lb, np.where(g > mu_hi, 1.0, 0.0))
    inv_2s2 = 0.5 * (inv_s * inv_s)
    a = (g * g) * inv_2s2
    lam = (mu_hi * mu_hi) * inv_2s2
    over = g <= mu_hi
    a_s = np.where(over, 1.0, a)
    l_s = np.where(over, 0.0, lam)
    q = np.sqrt(1.0 + 4.0 * a_s * l_s)
    u = np.maximum(2.0 * a_s / (1.0 + q), 1.0 + 1e-7)
    b1 = u * np.exp(np.clip(-a_s * (1.0 - 1.0 / u) + l_s * (u - 1.0), -700.0, 50.0))
    p_chern = np.where(sig_pos, np.where(over, 0.0, np.maximum(0.0, 1.0 - b1)),
                       np.where(g > mu_hi, 1.0, 0.0))
    best = np.maximum(best, p_chern)
    return np.where(g <= 0.0, 0.0, best)


def _fine_det_prob_ub(p, n, snr, span, phase_f_nz, k_nz):
    if float(snr) >= 6.5:
        return 1.0
    n_lags = min(int(span), int(n))
    q_fine = np.zeros((phase_f_nz.shape[0], n), dtype=np.complex128)
    q_fine[:, :k_nz] = phase_f_nz * p[:k_nz][None, :]
    resp_all = np.fft.ifft(q_fine, axis=1) * (n * float(snr))
    if n <= 32:
        p_ub = float(np.minimum(1.0, _marcum_fast_ub(np.abs(resp_all), 1.0, float(snr)).sum(axis=1)).mean())
        return min(1.0, max(p_ub, 1e-12))
    gamma_f = np.fft.ifft(p) * n
    n_near = min(48, n // 2)
    agf_all = np.abs(gamma_f)
    agf_all[0] = 2.0
    d_near = np.argpartition(agf_all, n - n_near)[n - n_near:]
    lag0_pos = int(np.flatnonzero(d_near == 0)[0])
    gf_near = gamma_f[d_near]
    agf_near = np.minimum(np.abs(gf_near), 1.0)
    sig_near = np.sqrt(np.maximum(1.0 - agf_near * agf_near, 1e-12))

    far_mask = np.ones(n, dtype=bool)
    far_mask[d_near] = False
    if n_lags < n:
        rem_lags = max(0, n_lags - 1)
        far_abs = np.abs(resp_all[:, far_mask])
        if rem_lags == 0:
            p_far_ub = np.zeros(resp_all.shape[0], dtype=np.float64)
        elif rem_lags < far_abs.shape[1]:
            top_far = np.partition(far_abs, far_abs.shape[1] - rem_lags, axis=1)[:, far_abs.shape[1] - rem_lags:]
            p_far_ub = _marcum_fast_ub(top_far, 1.0, float(snr)).sum(axis=1)
        else:
            p_far_ub = _marcum_fast_ub(far_abs, 1.0, float(snr)).sum(axis=1)
    else:
        p_far_ub = _marcum_fast_ub(np.abs(resp_all[:, far_mask]), 1.0, float(snr)).sum(axis=1)

    ux = np.linspace(-3.2, 3.2, 11)
    hux = 0.5 * (ux[1] - ux[0])
    uxm = 0.5 * (ux[:-1] + ux[1:])
    pux = _norm_sf_1d(ux[:-1]) - _norm_sf_1d(ux[1:])
    uy = np.linspace(-2.8, 2.8, 9)
    huy = 0.5 * (uy[1] - uy[0])
    uym = 0.5 * (uy[:-1] + uy[1:])
    puy = _norm_sf_1d(uy[:-1]) - _norm_sf_1d(uy[1:])
    zfm = np.repeat(uxm, uym.size) + 1j * np.tile(uym, uxm.size)
    rfc = math.hypot(hux, huy)
    pwf = np.repeat(pux, uym.size) * np.tile(puy, uxm.size)
    p_out = max(0.0, 1.0 - float(pwf.sum()))

    mu_c = (np.abs(resp_all[:, d_near][:, :, None] + gf_near[None, :, None] * zfm[None, None, :])
            + agf_near[None, :, None] * rfc)
    p_near = _marcum_fast_ub(mu_c, sig_near[None, :, None], float(snr))
    p_near[:, lag0_pos, :] = np.where(mu_c[:, lag0_pos, :] >= float(snr), 1.0, 0.0)
    p_cell = np.minimum(1.0, p_far_ub[:, None] + p_near.sum(axis=1))
    p_det = float(((p_cell @ pwf) + p_out).mean())
    return min(1.0, max(p_det, 1e-12))


def _new_bound_state(p, n, bands, k0_by_band, snr, fd, window, nsamp, nsim):
    m_search = (int(nsamp) + 1) // 2
    m_fit = int(nsamp) // 2
    K = int(round(float(fd) * (m_search + 1))) - 1
    fit_j = int(round(float(fd) * (m_fit + 1)))
    if K < 0 or fit_j < 1 or fit_j > m_fit:
        return None

    idx_set = {K}
    t0_idxs = sorted({int(math.floor(float(a0) * K))
                      for a0 in _SPLIT if int(math.floor(float(a0) * K)) >= 1})
    idx_set.update(t0_idxs)
    t01_pairs = []
    for a0 in _SPLIT:
        i0 = int(math.floor(float(a0) * K))
        if i0 < 1:
            continue
        rem = 1.0 - float(a0)
        for a1 in _SPLIT:
            i1 = int(math.floor(float(a1) * rem * K))
            if i1 < 1:
                continue
            idx_set.add(i1)
            t01_pairs.append((i0, i1))
    t01_pairs = sorted(set(t01_pairs))
    all_idxs = sorted(idx_set)
    q_needed = {idx: _binom_lower_tail_q_needed(m_search, idx) for idx in all_idxs}

    w0, w1, c0, c1 = _engine_lags(n, bands, window)
    span = w1 - w0
    if span < 1:
        return None
    band_pos = {int(b): i for i, b in enumerate(bands)}
    return {
        "p": p, "n": int(n), "bands": tuple(bands), "band_pos": band_pos,
        "k0_by_band": dict(k0_by_band), "snr": float(snr), "w0": w0, "span": span,
        "c0": c0, "c1": c1, "nsamp": int(nsamp), "nsim": int(nsim), "K": K,
        "t0_idxs": t0_idxs, "t01_pairs": t01_pairs, "all_idxs": all_idxs,
        "q_needed": q_needed, "common": None,
        "bands_info": {}, "q_new_3": {}, "q_new_cov": {},
    }


def _ensure_bound_common(bstate):
    common = bstate["common"]
    if common is not None:
        return common
    p = bstate["p"]
    n = bstate["n"]
    bands = bstate["bands"]
    snr = bstate["snr"]
    w0 = bstate["w0"]
    span = bstate["span"]
    whole = span >= n
    step = n // bands[0]

    # Exact integer arrival-position weights modulo R_max
    t_mod = (np.arange(step, dtype=np.int64) - w0) % step
    if whole:
        cnt0 = np.ones(step, dtype=np.float64) / step
        cnt1 = cnt0
    else:
        cnt0 = np.where(t_mod < span, (span - 1 - t_mod) // step + 1, 0).astype(np.float64) / float(span)
        cnt1 = (np.where(t_mod < span - 1, (span - 2 - t_mod) // step + 1, 0).astype(np.float64) / float(span)
                if span > 1 else np.zeros(step, dtype=np.float64))

    # Fine-stage mean response and detection probability upper bound
    k_all = np.arange(n, dtype=np.float64)
    k_nz = int(np.flatnonzero(p)[-1]) + 1
    j_all = np.arange(_NF, dtype=np.int64)
    deltas = np.where(j_all <= 8, j_all / float(_NF), (j_all - _NF) / float(_NF))
    phase_f_nz = np.exp((-2j * math.pi / n) * np.outer(deltas, k_all[:k_nz]))
    mu_f = float(snr) * (phase_f_nz @ p[:k_nz])
    p_det_ub = _fine_det_prob_ub(p, n, snr, span, phase_f_nz, k_nz)

    # Compact 12 x 6 cell grid on shared in-band noise U1 ~ CN(0, 2)
    x_edges = np.linspace(-3.4, 1.6, 13)
    hx_cell = 0.5 * float(x_edges[1] - x_edges[0])
    x_mids = 0.5 * (x_edges[:-1] + x_edges[1:])
    px = _norm_sf_1d(x_edges[:-1]) - _norm_sf_1d(x_edges[1:])

    y_edges = np.linspace(-1.8, 1.8, 7)
    hy_cell = 0.5 * float(y_edges[1] - y_edges[0])
    y_mids = 0.5 * (y_edges[:-1] + y_edges[1:])
    py = _norm_sf_1d(y_edges[:-1]) - _norm_sf_1d(y_edges[1:])

    nx_c, ny_c = x_mids.size, y_mids.size
    cx_mid = np.repeat(x_mids, ny_c)
    cy_mid = np.tile(y_mids, nx_c)
    cz_mid = cx_mid + 1j * cy_mid
    crad = math.hypot(hx_cell, hy_cell)
    cp_xy = np.repeat(px, ny_c) * np.tile(py, nx_c)

    # Aligned 6 x 4 cell grid on residual noise U2 for main-lobe coarse lags (e = 0, 1)
    x2e = np.array([-2.8, -1.9, -1.2, -0.6, 0.0, 0.7, 1.6])
    y2e = np.array([-1.6, -0.6, 0.0, 0.6, 1.6])
    px2 = _norm_sf_1d(x2e[:-1]) - _norm_sf_1d(x2e[1:])
    py2 = _norm_sf_1d(y2e[:-1]) - _norm_sf_1d(y2e[1:])
    nx2, ny2 = px2.size, py2.size
    x2_lo = np.repeat(x2e[:-1], ny2)
    x2_hi = np.repeat(x2e[1:], ny2)
    x2_m = 0.5 * (x2_lo + x2_hi)
    hx2 = 0.5 * (x2_hi - x2_lo)
    y2_lo = np.tile(y2e[:-1], nx2)
    y2_hi = np.tile(y2e[1:], nx2)
    y2_m = 0.5 * (y2_lo + y2_hi)
    hy2 = 0.5 * (y2_hi - y2_lo)
    y2_amax = np.maximum(np.abs(y2_lo), np.abs(y2_hi))
    z2_c = x2_m + 1j * y2_m
    r2_c = np.hypot(hx2, hy2)
    p2_w = np.repeat(px2, ny2) * np.tile(py2, nx2)

    grp_1 = ((0.5 / 16.0, 7.5 / 16.0, tuple(range(16))),)
    grp_3 = (
        (0.0, 2.0 / 16.0, (14, 15, 0, 1, 2)),
        (5.5 / 16.0, 2.5 / 16.0, (3, 4, 5, 6, 7, 8)),
        (-5.0 / 16.0, 2.0 / 16.0, (9, 10, 11, 12, 13)),
    )
    common = (cnt0, cnt1, k_all, deltas, mu_f, p_det_ub,
              hx_cell, hy_cell, cx_mid, cy_mid, cz_mid, crad, cp_xy,
              x2_lo, x2_hi, y2_amax, z2_c, r2_c, p2_w, grp_1, grp_3)
    bstate["common"] = common
    return common


def _bound_band_info(bstate, b):
    b = int(b)
    hit = bstate["bands_info"].get(b)
    if hit is not None:
        return hit
    p = bstate["p"]
    n = bstate["n"]
    snr = bstate["snr"]
    nsim = bstate["nsim"]
    all_idxs = bstate["all_idxs"]
    q_needed = bstate["q_needed"]
    bi = bstate["band_pos"][b]
    c_cnt = int(bstate["c1"][bi] - bstate["c0"][bi])

    k0 = bstate["k0_by_band"][b]
    k_lo, k_hi = _band_slice(n, b, k0)
    p_sub = p[k_lo:k_hi]
    fb = float(p_sub.sum())

    # Wide high-SNR bands dismiss detections well above the noise floor (r = 0 is unconditionally sound)
    if fb > 0.60 and float(snr) * math.sqrt(fb) > 5.4 and bi >= 2:
        info = {
            "k_lo": k_lo, "k_hi": k_hi, "fb": fb, "c_cnt": c_cnt,
            "g": {idx: float("inf") for idx in all_idxs},
            "q": {idx: 0.0 for idx in all_idxs},
            "r": {idx: 0.0 for idx in all_idxs},
        }
        bstate["bands_info"][b] = info
        return info

    (cnt0, cnt1, k_all, deltas, mu_f, p_det_ub,
     hx_cell, hy_cell, cx_mid, cy_mid, cz_mid, crad, cp_xy,
     x2_lo, x2_hi, y2_amax, z2_c, r2_c, p2_w, grp_1, grp_3) = _ensure_bound_common(bstate)

    sq_fb = math.sqrt(fb)
    sig_out = math.sqrt(max(1.0 - fb, 0.0))
    R = n // b

    # In-band noise autocorrelation and Gram-Schmidt couplings onto U1, U2, U3
    wb = np.zeros(b, dtype=np.float64)
    u_bins = np.arange(k_lo, k_hi) % b
    wb[u_bins] = p_sub / fb
    nnz_bins = int(np.count_nonzero(wb > 1e-12))
    gamma_b = np.fft.ifft(wb) * b

    noise_med = math.sqrt(2.0 * math.log(max(b, 2)))
    g_lo = max(1.2, min(float(snr) * sq_fb, noise_med) - 1.8)
    g_hi = max(float(snr) * sq_fb, noise_med) + 1.8
    G = 14
    g_grid = np.linspace(g_lo, g_hi, G)

    w_rho0 = cnt0.reshape(-1, R).sum(axis=0)
    w_rho1 = np.roll(cnt1.reshape(-1, R).sum(axis=0), 1)

    k_sub = k_all[k_lo:k_hi]
    omega_sub = (2.0 * math.pi / n) * k_sub
    omega_c = float(np.dot(omega_sub, p_sub)) / fb
    domega = omega_sub - omega_c
    scale_mu = float(snr) / sq_fb
    m2_cen = 0.5 * float(np.dot(domega * domega, p_sub)) * scale_mu
    d1_max_est = float(np.dot(np.abs(domega), p_sub)) * scale_mu

    rho_vec = np.arange(R, dtype=np.float64)[:, None]
    tw_rho = np.exp((-2j * math.pi / n) * (rho_vec * k_sub[None, :]))

    buf_b = np.zeros((R, b), dtype=np.complex128)
    buf_b[:, u_bins] = tw_rho * (p_sub / fb)[None, :]
    c_u1 = np.fft.ifft(buf_b, axis=1) * b
    ac_u1 = np.minimum(np.abs(c_u1), 1.0)
    sig_u1 = np.sqrt(np.maximum(1.0 - ac_u1 * ac_u1, 1e-12))
    inv_2s2 = 0.5 / np.maximum(sig_u1 * sig_u1, 1e-24)

    s0 = sig_u1[:, 0]
    r_cap = 3.2
    tail_23 = 2.0 * math.exp(-0.5 * r_cap * r_cap)
    if b >= 2:
        cov10 = gamma_b[1 % b] - c_u1[:, 1 % b] * np.conj(c_u1[:, 0])
        alpha1 = np.where(s0 > 1e-6, cov10 / np.maximum(s0, 1e-6), 0.0 + 0.0j)
        tau1 = np.sqrt(np.maximum(sig_u1[:, 1] ** 2 - np.abs(alpha1) ** 2, 0.0))

    # Partition side-lobe lags e >= 2 into exact top couplings and geometric buckets
    rows_r = np.arange(R)[:, None]
    far_buckets = []
    if b > 2:
        other_idx = np.arange(2, b)
        cov_e0 = gamma_b[other_idx][None, :] - c_u1[:, 2:] * np.conj(c_u1[:, 0])[:, None]
        beta2 = np.where(s0[:, None] > 1e-6, cov_e0 / np.maximum(s0[:, None], 1e-6), 0.0 + 0.0j)
        cov_e1 = gamma_b[(other_idx - 1) % b][None, :] - c_u1[:, 2:] * np.conj(c_u1[:, 1])[:, None]
        beta3 = np.where(tau1[:, None] > 1e-6,
                         (cov_e1 - beta2 * np.conj(alpha1)[:, None]) / np.maximum(tau1[:, None], 1e-6),
                         0.0 + 0.0j)
        ab23_all = r_cap * (np.abs(beta2) + np.abs(beta3))

        n_other = b - 2
        s_side = min(n_other, 6 if R >= 32 else 12)
        rank_score = ac_u1[:, 2:] + ab23_all
        if n_other > s_side:
            order = np.argsort(rank_score, axis=1)
            side_rel = order[:, n_other - s_side:]
            side_idx = other_idx[side_rel]
            ab23_s = ab23_all[rows_r, side_rel]
            rem_end = n_other - s_side
            for b_sz in (16, 48, 128, rem_end):
                if rem_end <= 0:
                    break
                b_lo = max(0, rem_end - b_sz)
                b_rel = order[:, b_lo:rem_end]
                b_idx = other_idx[b_rel]
                n_b = rem_end - b_lo
                acu_max = ac_u1[rows_r, b_idx].max(axis=1)
                ab23_max = ab23_all[rows_r, b_rel].max(axis=1)
                inv_2s_min = 0.5 / np.maximum(sig_u1[rows_r, b_idx].max(axis=1) ** 2, 1e-24)
                far_buckets.append((b_idx, n_b, acu_max, ab23_max, inv_2s_min))
                rem_end = b_lo
        else:
            side_idx = np.broadcast_to(other_idx[None, :], (R, n_other))
            ab23_s = ab23_all
    else:
        side_idx = None
        ab23_s = None

    if side_idx is not None:
        cu1_s = c_u1[rows_r, side_idx]
        acu1_s = ac_u1[rows_r, side_idx]
        inv_2sigs_sq = inv_2s2[rows_r, side_idx]

    # Lower bound on joint event {C_b <= g, F_win >= snr} across sub-sample arrival groups
    cur_groups = grp_1 if 0.47 * d1_max_est <= 0.22 else grp_3
    p_joint_lb = np.zeros(G, dtype=np.float64)
    abs_z = np.abs(cz_mid) + crad

    for d_mid, d_half, g_js in cur_groups:
        ph_m = np.exp((-1j * d_mid) * domega) * p_sub
        buf_b.fill(0.0)
        buf_b[:, u_bins] = tw_rho * ph_m[None, :]
        mu_m = np.fft.ifft(buf_b, axis=1) * (b * scale_mu)
        buf_b.fill(0.0)
        buf_b[:, u_bins] = tw_rho * (-1j * domega * ph_m)[None, :]
        d1_m = np.abs(np.fft.ifft(buf_b, axis=1)) * (b * scale_mu)
        d2_t = (d_half * d_half) * m2_cen

        w_rc = np.zeros((R, cz_mid.size), dtype=np.float64)
        for j in g_js:
            w0_j = np.exp(1j * float(deltas[j]) * omega_c) * mu_f[j]
            rx_min = np.maximum(0.0, np.abs(w0_j.real + sq_fb * cx_mid) - sq_fb * hx_cell)
            ry_min = np.maximum(0.0, np.abs(w0_j.imag + sq_fb * cy_mid) - sq_fb * hy_cell)
            mf_lb = np.hypot(rx_min, ry_min)
            if sig_out > 1e-12:
                s_thr = float(snr) / sig_out
                a_val = mf_lb / sig_out
                z1 = s_thr - a_val
                pf1 = np.where(z1 >= 0.0, _gauss_tail_lb(z1) * _INV_RT2PI,
                               1.0 - _gauss_tail_ub(-z1) * _INV_RT2PI)
                c_st = 0.75
                z_c = c_st * s_thr - a_val
                pf_c = np.where(z_c >= 0.0, _gauss_tail_lb(z_c) * _INV_RT2PI,
                                1.0 - _gauss_tail_ub(-z_c) * _INV_RT2PI)
                py_out = 2.0 * _gauss_tail_lb(math.sqrt(1.0 - c_st * c_st) * s_thr) * _INV_RT2PI
                pf_ray = math.exp(-0.5 * min(s_thr * s_thr, 700.0))
                pf = np.clip(np.maximum(pf_ray, pf1 + np.maximum(0.0, pf_c - pf1) * py_out), 0.0, 1.0)
            else:
                pf = np.where(mf_lb >= float(snr), 1.0, 0.0)
            w_arr = (w_rho0 if j <= 8 else w_rho1)[:, None]
            w_rc += w_arr * cp_xy[None, :] * pf / float(_NF)

        act = np.flatnonzero(w_rc.sum(axis=0) > 5e-5)
        if act.size == 0:
            continue
        zc, az, wc = cz_mid[act], abs_z[act], w_rc[:, act]

        p_rest = np.ones((R, act.size, G), dtype=np.float64)
        p_rest_cond = np.ones((R, act.size, G), dtype=np.float64)
        if side_idx is not None:
            mu_s = (np.abs(mu_m[rows_r, side_idx][:, None, :] + cu1_s[:, None, :] * zc[None, :, None])
                    + acu1_s[:, None, :] * crad
                    + (d_half * d1_m[rows_r, side_idx] + d2_t)[:, None, :])
            rg_s = np.maximum(0.0, g_grid[None, None, None, :] - mu_s[..., None])
            p_side_each = np.where(rg_s > 0.0,
                                   1.0 - np.exp(-np.minimum(rg_s * rg_s * inv_2sigs_sq[:, None, :, None], 700.0)),
                                   0.0)
            p_rest *= np.prod(p_side_each, axis=2)

            rg_sc = np.maximum(0.0, rg_s - ab23_s[:, None, :, None])
            p_sc_each = np.where(rg_sc > 0.0,
                                 1.0 - np.exp(-np.minimum(rg_sc * rg_sc * inv_2sigs_sq[:, None, :, None], 700.0)),
                                 0.0)
            p_rest_cond *= np.prod(p_sc_each, axis=2)

        for b_idx, n_b, acu_max, ab23_max, inv_2s_min in far_buckets:
            amu_f = np.abs(mu_m[rows_r, b_idx]).max(axis=1)
            d1_f = d1_m[rows_r, b_idx].max(axis=1)
            mu_f_hi = amu_f[:, None] + acu_max[:, None] * az[None, :] + (d_half * d1_f + d2_t)[:, None]
            rg_f = np.maximum(0.0, g_grid[None, None, :] - mu_f_hi[..., None])
            p_far_one = np.where(rg_f > 0.0,
                                 1.0 - np.exp(-np.minimum(rg_f * rg_f * inv_2s_min[:, None, None], 700.0)),
                                 0.0)
            p_rest *= p_far_one ** n_b

            rg_fc = np.maximum(0.0, rg_f - ab23_max[:, None, None])
            p_fc_one = np.where(rg_fc > 0.0,
                                1.0 - np.exp(-np.minimum(rg_fc * rg_fc * inv_2s_min[:, None, None], 700.0)),
                                0.0)
            p_rest_cond *= p_fc_one ** n_b

        m0_c = mu_m[:, None, 0] + c_u1[:, None, 0] * zc[None, :]
        rad0 = ac_u1[:, 0][:, None] * crad + (d_half * d1_m[:, 0] + d2_t)[:, None]
        mu0_hi = np.abs(m0_c) + rad0
        rg0 = np.maximum(0.0, g_grid[None, None, :] - mu0_hi[..., None])
        p0_sym = np.where(rg0 > 0.0,
                          1.0 - np.exp(-np.minimum(rg0 * rg0 * inv_2s2[:, 0][:, None, None], 700.0)),
                          0.0)
        if b == 1:
            surv = p0_sym * p_rest
            if fb >= 0.15:
                p0_d = _disk_prob_lb(mu0_hi[..., None], s0[:, None, None], g_grid[None, None, :])
                surv = np.maximum(surv, np.maximum(0.0, p0_d + p_rest - 1.0))
        else:
            m1_c = mu_m[:, None, 1] + c_u1[:, None, 1] * zc[None, :]
            rad1 = ac_u1[:, 1][:, None] * crad + (d_half * d1_m[:, 1] + d2_t)[:, None]
            mu1_hi = np.abs(m1_c) + rad1
            rg1 = np.maximum(0.0, g_grid[None, None, :] - mu1_hi[..., None])
            p1_sym = np.where(rg1 > 0.0,
                              1.0 - np.exp(-np.minimum(rg1 * rg1 * inv_2s2[:, 1][:, None, None], 700.0)),
                              0.0)
            surv = p0_sym * p1_sym * p_rest
            if fb >= 0.15 and float(p_rest_cond[:, :, -1].max()) > 0.02:
                p0_1d = _disk_prob_lb(mu0_hi[..., None], s0[:, None, None], g_grid[None, None, :])
                p1_1d = _disk_prob_lb(mu1_hi[..., None], sig_u1[:, 1][:, None, None], g_grid[None, None, :])
                p01 = np.maximum(0.0, p0_1d + p1_1d - 1.0)
                r_sub_cnt = min(R, 8)
                if R > r_sub_cnt:
                    top_r = np.argpartition(wc.sum(axis=1), R - r_sub_cnt)[R - r_sub_cnt:]
                else:
                    top_r = slice(None)
                m0_sub = m0_c[top_r]
                m1_sub = m1_c[top_r]
                s0_sub = s0[top_r]
                rad0_sub = rad0[top_r]
                rad1_sub = rad1[top_r]
                alpha1_sub = alpha1[top_r]
                tau1_sub = tau1[top_r]
                am0 = np.abs(m0_sub)
                phi0 = np.where(am0 > 1e-12, m0_sub / np.maximum(am0, 1e-12), 1.0 + 0.0j)
                u0_x = np.maximum(np.abs(am0[:, :, None] + s0_sub[:, None, None] * x2_lo[None, None, :]),
                                  np.abs(am0[:, :, None] + s0_sub[:, None, None] * x2_hi[None, None, :]))
                u0_hi_2 = np.hypot(u0_x, s0_sub[:, None, None] * y2_amax[None, None, :]) + rad0_sub[:, :, None]
                u1_hi_2 = (np.abs(m1_sub[:, :, None] + (alpha1_sub[:, None] * phi0)[:, :, None] * z2_c[None, None, :])
                           + np.abs(alpha1_sub)[:, None, None] * r2_c[None, None, :] + rad1_sub[:, :, None])
                ok0 = g_grid[None, None, None, :] > u0_hi_2[..., None]
                p1_c = _disk_prob_lb(u1_hi_2[..., None], tau1_sub[:, None, None, None], g_grid[None, None, None, :])
                p01_2d = (p2_w[None, None, :, None] * np.where(ok0, p1_c, 0.0)).sum(axis=2)
                p01[top_r] = np.maximum(p01[top_r], p01_2d)
                surv_cond = np.maximum(0.0, p01 - tail_23) * p_rest_cond
                surv = np.maximum(surv, np.maximum(surv_cond, np.maximum(0.0, p01 + p_rest - 1.0)))

        p_joint_lb += (wc[:, :, None] * surv).sum(axis=(0, 1))

    # Invert conservative dismissal CDF for threshold upper bounds and noise-pass lower bounds
    q_safe = np.clip(p_joint_lb / p_det_ub, 0.0, 1.0)
    g_ubs = {}
    for idx in all_idxs:
        ok_g = np.flatnonzero(q_safe >= q_needed[idx])
        g_ubs[idx] = float(g_grid[ok_g[0]]) if ok_g.size > 0 else float("inf")
    g_vec = np.array([g_ubs[idx] for idx in all_idxs], dtype=np.float64)
    q_pop = _noise_pop_lb(gamma_b, b, c_cnt, g_vec, nnz_bins=nnz_bins)
    r_emp = np.array([_binom_rate_lb(int(nsim), float(qv)) for qv in q_pop])
    info = {
        "k_lo": k_lo, "k_hi": k_hi, "fb": fb, "c_cnt": c_cnt,
        "g": {idx: g_ubs[idx] for idx in all_idxs},
        "q": {idx: float(q_pop[i]) for i, idx in enumerate(all_idxs)},
        "r": {idx: float(r_emp[i]) for i, idx in enumerate(all_idxs)},
    }
    bstate["bands_info"][b] = info
    return info


def _bound_q_new_3(bstate, b0, b1, b2):
    key3 = (int(b0), int(b1), int(b2))
    hit = bstate["q_new_3"].get(key3)
    if hit is not None:
        return hit
    inf0 = _bound_band_info(bstate, b0)
    inf1 = _bound_band_info(bstate, b1)
    inf2 = _bound_band_info(bstate, b2)
    g2_ub = inf2["g"][bstate["K"]]
    if not math.isfinite(g2_ub):
        bstate["q_new_3"][key3] = 0.0
        return 0.0
    if inf0["k_hi"] >= inf1["k_lo"] and inf1["k_hi"] >= inf0["k_lo"]:
        cov_key = ("iv", min(inf0["k_lo"], inf1["k_lo"]), max(inf0["k_hi"], inf1["k_hi"]), int(b2))
    else:
        cov_key = ("2iv", inf0["k_lo"], inf0["k_hi"], inf1["k_lo"], inf1["k_hi"], int(b2))
    val = bstate["q_new_cov"].get(cov_key)
    if val is None:
        p = bstate["p"]
        n = bstate["n"]
        nsim = bstate["nsim"]
        mask_new = np.zeros(n, dtype=bool)
        mask_new[inf2["k_lo"]:inf2["k_hi"]] = True
        mask_new[inf0["k_lo"]:inf0["k_hi"]] = False
        mask_new[inf1["k_lo"]:inf1["k_hi"]] = False
        ks_new = np.flatnonzero(mask_new)
        f_new = float(p[ks_new].sum()) if ks_new.size > 0 else 0.0
        if f_new <= 1e-12:
            val = 0.0
        else:
            sig_new = math.sqrt(f_new / inf2["fb"])
            g_eff = g2_ub / sig_new
            if inf2["c_cnt"] * math.exp(-0.5 * min(g_eff * g_eff, 700.0)) * nsim < _BOUND_LOG_INV_DELTA:
                val = 0.0
            else:
                wb_new = np.zeros(int(b2), dtype=np.float64)
                np.add.at(wb_new, ks_new % int(b2), p[ks_new] / f_new)
                nnz_new = int(np.count_nonzero(wb_new > 1e-12))
                gamma_new = np.fft.ifft(wb_new) * int(b2)
                val = float(_noise_pop_lb(
                    gamma_new, int(b2), inf2["c_cnt"], np.array([g_eff]), nnz_bins=nnz_new
                )[0])
        bstate["q_new_cov"][cov_key] = val
    bstate["q_new_3"][key3] = val
    return val


def _cost_model_nonneg(cost):
    if any(v < 0.0 for v in cost.dense.values()):
        return False
    if any(v < 0.0 for _, v in cost._refine):
        return False
    if any(v < 0.0 for rows in cost._sparse.values() for _, v in rows):
        return False
    if any(sc["dense"] < 0.0 or sc["recheck"] < 0.0 for sc in cost.screen.values()):
        return False
    dlag = getattr(cost, "direct_lag", None)
    if dlag is not None:
        dfrac = getattr(cost, "direct_frac", 1.0)
        if not (0.0 <= dfrac <= 1.0) or getattr(cost, "direct_multi_frac", 0.0) < 0.0:
            return False
        if dlag < 0.0 or getattr(cost, "direct_base", 0.0) + dlag < 0.0:
            return False
    return True


def pair_cost_lower_bound(power, n, snr, fd, cost, max_tiers=3, floor=_MIN_BAND, nsim=None,
                          window=None, ntemplates=None, nsamp=None, max_cost=None):
    """Analytic lower bound on `choose_chain(...)[0]["cost"]` without Monte Carlo draws.

    Parameters
    ----------
    power : array_like
        Nonnegative filter-output power profile of length `n`.
    n : int
        Transform block length.
    snr : float
        Target detection signal-to-noise ratio.
    fd : float
        False-dismissal budget.
    cost : CostModel
        Calibrated tier and refine cost model at block length `n`.
    max_tiers : int, optional
        Maximum number of coarse gate tiers to consider (default `3`).
    floor : int, optional
        Minimum candidate coarse band size (default `_MIN_BAND`).
    nsim : int, optional
        Number of noise blocks in the gate model (default `model_draws(fd)[1]`).
    window : tuple of int, optional
        Searched fine-lag window `(start, end)` within `[0, n)`, or `None` for the whole block.
    ntemplates : int, optional
        Template count for GPU feed pricing (`CostModel.feed_delta`), or `None`.
    nsamp : int, optional
        Number of signal detections in the gate model (default `model_draws(fd)[0]`).
    max_cost : float, optional
        Optional branch-and-bound threshold. When provided, evaluation stops early as soon
        as a sound lower bound at or below `max_cost` is certified, while still returning a
        valid lower bound on the minimum pair cost across all chains.

    Returns
    -------
    float or None
        Conservative lower bound on the best searched chain cost per `(block, template)` pair,
        or `None` when `cost` is not a nonnegative `CostModel` or `fd` cannot be resolved.
    """
    if not isinstance(cost, CostModel) or not cost._refine or not _cost_model_nonneg(cost):
        return None
    p = _norm_profile(power, n)
    win = None if window is None else (int(window[0]), int(window[1]))
    dsamp, dsim = model_draws(fd)
    nsamp = dsamp if nsamp is None else int(nsamp)
    nsim = dsim if nsim is None else int(nsim)
    if nsamp is None or nsamp < 2 or nsim < 1:
        return None
    max_c = None if max_cost is None else float(max_cost)

    sig_p = _gm._profile_sig(p)
    c_bands, k0_cand, bands = _cached_band_offsets(p, sig_p, n, floor)
    if not bands:
        return None

    # Check exact and similarity caches for previously computed full lower bounds
    extra = (k0_cand,) if any(k0_cand) else ()
    feed_nt = None if not getattr(cost, "feed", None) else int(ntemplates or 0)
    price_params = (int(n), float(snr), float(fd), int(max_tiers), int(floor), int(nsim),
                    int(nsamp), win, _cost_sig(cost), feed_nt) + extra
    price_key = (sig_p,) + price_params
    if price_key in _BOUND_PRICE_CACHE:
        _BOUND_PRICE_CACHE.move_to_end(price_key)
        return _BOUND_PRICE_CACHE[price_key]

    # Build piecewise-monotone knot grid for CostModel tables
    has_feed = bool(ntemplates and getattr(cost, "feed", None))
    base_knots = {0.0, 1e-12, 1e-6, 0.05 - 1e-12, 0.05, float(_USELESS_PASS), 1.0}
    for f_k, _ in cost._refine:
        base_knots.add(float(f_k))
    for rows in cost._sparse.values():
        for f_k, _ in rows:
            base_knots.add(float(f_k))
    for sc in cost.screen.values():
        for f_k, _ in sc["excess"]:
            base_knots.add(float(f_k))
    knots_tup = tuple(sorted(f_k for f_k in base_knots if 0.0 <= f_k <= 1.0))

    ft_memo = {}

    def _first_tier_lb(b0, f_lo, f_hi):
        key_ft = (b0, f_lo, f_hi)
        hit = ft_memo.get(key_ft)
        if hit is not None:
            return hit
        c_dense = cost.dense[int(b0)]
        sc = cost.screen.get(int(b0))
        if sc is None or not sc["excess"]:
            res = (c_dense, None, c_dense)
            ft_memo[key_ft] = res
            return res
        sr_lo = cost.screen_reach(b0, f_lo)
        sr_hi = cost.screen_reach(b0, f_hi)
        cq_min = sc["dense"] + min(sr_lo, sr_hi) * sc["recheck"]
        cq_max = sc["dense"] + max(sr_lo, sr_hi) * sc["recheck"]
        scr_lb = cq_min if cq_min <= c_dense * (1.0 + TIE) else None
        flt_lb = c_dense if cq_max > c_dense * (1.0 + TIE) else None
        c_min = min(scr_lb if scr_lb is not None else float("inf"),
                    flt_lb if flt_lb is not None else float("inf"))
        res = (c_min, scr_lb, flt_lb)
        ft_memo[key_ft] = res
        return res

    def _feed_min(chain):
        if not has_feed:
            return 0.0
        vals = [cost.feed_delta(chain, [1.0] * len(chain) + [0.0], ntemplates, None),
                cost.feed_delta(chain, [1.0] * len(chain) + [1.0], ntemplates, None)]
        if cost.prices_direct(chain):
            vals.append(cost.feed_delta(chain, [1.0] * len(chain) + [1.0], ntemplates, 1))
        return min(vals)

    # Zero-FFT tier-0 + feed floor check before touching similarity features or FFTs
    c0_floor = {
        b: min(_first_tier_lb(b, knots_tup[i], knots_tup[i + 1])[0]
               for i in range(len(knots_tup) - 1))
        for b in bands
    }
    all_chains = enumerate_chains(n, max_tiers, floor, bands=bands)
    if not all_chains:
        return None
    ordered = sorted(
        ((c0_floor[ch[0]] + _feed_min(ch), ch) for ch in all_chains),
        key=lambda item: (-item[1][0], len(item[1]), item[1]),
    )
    min_all_floor = min(fl for fl, _ in ordered)
    if max_c is not None:
        m_search = (int(nsamp) + 1) // 2
        m_fit = int(nsamp) // 2
        k_bud = int(round(float(fd) * (m_search + 1))) - 1
        fit_j = int(round(float(fd) * (m_fit + 1)))
        span_chk = n if win is None else (win[1] - win[0])
        if k_bud < 0 or fit_j < 1 or fit_j > m_fit or span_chk < 1:
            return None
        if min_all_floor > max_c:
            return min_all_floor
        if int(max_tiers) >= 1 and len(bands) >= 3:
            k0_map = dict(zip(c_bands, k0_cand))
            for b_wide in bands[2:]:
                c_wide = _first_tier_lb(b_wide, knots_tup[0], knots_tup[1])[0] + _feed_min((b_wide,))
                if c_wide <= max_c:
                    fb_w = float(p[slice(*_band_slice(n, b_wide, k0_map[b_wide]))].sum())
                    if fb_w > 0.60 and float(snr) * math.sqrt(fb_w) > 5.4:
                        return min_all_floor

    unit_price, cached_lb = _similar_get("pair-lb", p, price_params)
    if cached_lb is not None:
        _cache_put(_BOUND_PRICE_CACHE, price_key, cached_lb)
        return cached_lb

    # Retrieve or initialize lazy per-band analytic reach state
    b_params = (int(n), float(snr), float(fd), int(floor), int(nsim), int(nsamp), win) + extra
    b_key = (sig_p,) + b_params
    bstate = _BOUND_CACHE.get(b_key)
    if bstate is not None:
        _BOUND_CACHE.move_to_end(b_key)
    else:
        unit, bstate = _similar_get("bound", p, b_params)
        if bstate is None:
            bstate = _new_bound_state(p, n, bands, dict(zip(c_bands, k0_cand)), snr, fd, win, nsamp, nsim)
            if bstate is None:
                return None
            _similar_put("bound", unit, b_params, bstate)
        _cache_put(_BOUND_CACHE, b_key, bstate)

    sp_at = {}

    def _sp_eval(bt, u):
        k_sp = (bt, u)
        v = sp_at.get(k_sp)
        if v is None:
            v = sp_at[k_sp] = cost.sparse(bt, u)
        return v

    ref_at = {}

    def _ref_eval(u):
        v = ref_at.get(u)
        if v is None:
            v = ref_at[u] = cost.refine(u)
        return v

    def _pts_between(lo_v, hi_v):
        pts = [lo_v]
        for x in knots_tup:
            if lo_v < x < hi_v:
                pts.append(x)
        pts.append(hi_v if hi_v > lo_v else lo_v)
        return pts

    def _direct_refine_min(chain, u0_f, u1_f):
        dlag = getattr(cost, "direct_lag", None)
        if dlag is None or dlag < 0.0:
            return 0.0
        f_right = u0_f if (u0_f < 0.05 and u1_f >= 0.05) else u1_f
        return min(cost.refine_for(chain, u0_f, hw=1), cost.refine_for(chain, f_right, hw=1))

    sp_memo = {}

    def _sparse_term_lb(bt, r_lo, r_hi=float(_USELESS_PASS)):
        if r_lo <= 0.0:
            return 0.0
        if r_lo > r_hi:
            return float("inf")
        key_sp = (bt, r_lo, r_hi)
        hit = sp_memo.get(key_sp)
        if hit is not None:
            return hit
        pts = _pts_between(r_lo, r_hi)
        best = float("inf")
        for i in range(len(pts) - 1):
            u0_f, u1_f = pts[i], pts[i + 1]
            v = u0_f * min(_sp_eval(bt, u0_f), _sp_eval(bt, u1_f))
            if v < best:
                best = v
        sp_memo[key_sp] = best
        return best

    ref_memo = {}

    def _refine_term_lb(chain, f_lo, allow_direct=True):
        if f_lo <= 0.0:
            return 0.0
        pdir = allow_direct and cost.prices_direct(chain)
        key_ref = (chain[-1] if pdir else 0, len(chain) if pdir else 0, f_lo, pdir)
        hit = ref_memo.get(key_ref)
        if hit is not None:
            return hit
        pts = _pts_between(f_lo, 1.0)
        best = float("inf")
        for i in range(len(pts) - 1):
            u0_f, u1_f = pts[i], pts[i + 1]
            ref_min = min(_ref_eval(u0_f), _ref_eval(u1_f))
            if pdir:
                ref_min = min(ref_min, _direct_refine_min(chain, u0_f, u1_f))
            v = u0_f * ref_min
            if v < best:
                best = v
        ref_memo[key_ref] = best
        return best

    K = bstate["K"]
    u_cap = float(_USELESS_PASS)
    rate_memo = {}

    def _emp_lb(q_val):
        key_q = round(float(q_val), 9)
        hit = rate_memo.get(key_q)
        if hit is None:
            hit = rate_memo[key_q] = _binom_rate_lb(nsim, key_q)
        return hit

    i1s_by_i0 = {}
    for i0, i1 in bstate["t01_pairs"]:
        i1s_by_i0.setdefault(i0, []).append(i1)

    pair01_memo = {}

    def _pair01_costs(b0, b1):
        hit = pair01_memo.get((b0, b1))
        if hit is not None:
            return hit
        inf0 = _bound_band_info(bstate, b0)
        res = {}
        for i0 in bstate["t0_idxs"]:
            r1_lb = inf0["r"][i0]
            if r1_lb > u_cap:
                continue
            pts = _pts_between(r1_lb, u_cap)
            best01 = float("inf")
            for i in range(len(pts) - 1):
                u0_f, u1_f = pts[i], pts[i + 1]
                c0_lb, _, _ = _first_tier_lb(b0, u0_f, u1_f)
                sp1_min = min(_sp_eval(b1, u0_f), _sp_eval(b1, u1_f))
                v = c0_lb + u0_f * sp1_min
                if v < best01:
                    best01 = v
            res[i0] = best01
        pair01_memo[(b0, b1)] = res
        return res

    # Branch-and-bound minimization across all candidate chains
    best_lb = float("inf")
    used_max_c = False
    for idx_ch, (fl_chain, chain) in enumerate(ordered):
        if fl_chain >= best_lb:
            continue
        if max_c is not None and fl_chain > max_c:
            used_max_c = True
            if fl_chain < best_lb:
                best_lb = fl_chain
            continue

        k = len(chain)
        b0 = chain[0]
        feed_lb = fl_chain - c0_floor[b0]
        c_chain = float("inf")

        if k == 1:
            inf0 = _bound_band_info(bstate, b0)
            r_min = inf0["r"][K]
            pts = _pts_between(r_min, 1.0)
            pdir = cost.prices_direct(chain)
            for i in range(len(pts) - 1):
                u0_f, u1_f = pts[i], pts[i + 1]
                _, scr_lb, flt_lb = _first_tier_lb(b0, u0_f, u1_f)
                ref_xform = min(_ref_eval(u0_f), _ref_eval(u1_f))
                if scr_lb is not None:
                    c_scr = scr_lb + u0_f * ref_xform + feed_lb
                    if c_scr < c_chain:
                        c_chain = c_scr
                if flt_lb is not None:
                    ref_flt = min(ref_xform, _direct_refine_min(chain, u0_f, u1_f)) if pdir else ref_xform
                    c_flt = flt_lb + u0_f * ref_flt + feed_lb
                    if c_flt < c_chain:
                        c_chain = c_flt

        elif k == 2:
            b1 = chain[1]
            c01_map = _pair01_costs(b0, b1)
            if c01_map:
                p_lb_01 = min(c01_map.values()) + feed_lb
                if p_lb_01 >= best_lb:
                    continue
                if max_c is not None and p_lb_01 > max_c:
                    used_max_c = True
                    if p_lb_01 < best_lb:
                        best_lb = p_lb_01
                    continue
                inf0 = _bound_band_info(bstate, b0)
                inf1 = _bound_band_info(bstate, b1)
                q1_k = inf1["q"][K]
                for i0, c01 in c01_map.items():
                    f2_lb = _emp_lb(inf0["q"][i0] * q1_k)
                    c_val = c01 + _refine_term_lb(chain, f2_lb, allow_direct=True) + feed_lb
                    if c_val < c_chain:
                        c_chain = c_val

        else:
            b1, b2 = chain[1], chain[2]
            c01_map = _pair01_costs(b0, b1)
            if c01_map:
                p_lb_01 = min(c01_map.values()) + feed_lb
                if p_lb_01 >= best_lb:
                    continue
                if max_c is not None and p_lb_01 > max_c:
                    used_max_c = True
                    if p_lb_01 < best_lb:
                        best_lb = p_lb_01
                    continue
                inf0 = _bound_band_info(bstate, b0)
                inf1 = _bound_band_info(bstate, b1)
                cand_012 = []
                p_lb_012 = float("inf")
                for i0, c01 in c01_map.items():
                    i1_list = i1s_by_i0.get(i0)
                    if not i1_list:
                        continue
                    q1_min = min(inf1["q"][i1] for i1 in i1_list)
                    q01 = inf0["q"][i0] * q1_min
                    r2_lb = _emp_lb(q01)
                    if r2_lb > u_cap:
                        continue
                    sp2_lb = _sparse_term_lb(b2, r2_lb, u_cap)
                    base_012 = c01 + sp2_lb + feed_lb
                    if base_012 < p_lb_012:
                        p_lb_012 = base_012
                    cand_012.append((q01, base_012))
                if k != 3 or p_lb_012 >= best_lb:
                    if p_lb_012 < best_lb:
                        best_lb = p_lb_012
                    continue
                if max_c is not None and p_lb_012 > max_c:
                    used_max_c = True
                    if p_lb_012 < best_lb:
                        best_lb = p_lb_012
                    continue
                q_new2 = _bound_q_new_3(bstate, b0, b1, b2)
                for q01, base_012 in cand_012:
                    f3_lb = _emp_lb(q01 * q_new2)
                    c_val = base_012 + _refine_term_lb(chain, f3_lb, allow_direct=True)
                    if c_val < c_chain:
                        c_chain = c_val

        if c_chain < best_lb:
            best_lb = c_chain
            if max_c is not None and best_lb <= max_c:
                if idx_ch + 1 < len(ordered):
                    rem_floor = min(fl for fl, _ in ordered[idx_ch + 1:])
                    return min(best_lb, rem_floor)
                used_max_c = False
                break

    out_val = best_lb if math.isfinite(best_lb) else None
    if not used_max_c:
        _cache_put(_BOUND_PRICE_CACHE, price_key, out_val)
        if out_val is not None:
            _similar_put("pair-lb", unit_price, price_params, out_val)
    return out_val


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


