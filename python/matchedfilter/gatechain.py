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
    Fb = np.array([p[:b].sum() for b in bands])
    if Fb[0] <= 0:
        return None          # a band holding no power cannot gate; callers drop such bands (usable_bands)
    lags = _engine_lags(n, bands, window)
    ndet = int(ndet)
    key = _key(p, n, bands, float(snr), ndet, int(seed), lags, _NF)
    hit = _SIGNAL_CACHE.get(key)
    if hit is not None:
        _SIGNAL_CACHE.move_to_end(key)
        return hit[0] if not lags_too else hit
    sim = _signal_records(p, n, bands, Fb, float(snr), ndet, int(seed))
    while True:
        C, F, at = _signal_window(sim, n, bands, lags)
        det = np.flatnonzero(F >= snr)
        if det.size >= ndet:
            break
        # the window misses some of the block's detections: more, in proportion
        kept = sim["t"].size
        sim = _signal_records(p, n, bands, Fb, float(snr),
                              kept + int(math.ceil((ndet - det.size) * kept / max(det.size, 1))) + 1,
                              int(seed))
    end = int(det[ndet - 1]) + 1 if ndet > 0 else 0
    C, F, at = C[:end], F[:end], (at[0][:end], at[1][:end])
    hit = ((C, np.broadcast_to(F[:, None], C.shape)), at)
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


def _signal_records(p, n, bands, Fb, snr, kept, seed):
    """signal_draws' simulation, with at least `kept` draws kept: a dict holding the profile
    it simulates and, per kept draw, the signal's integer arrival t in [0, R_max), a uniform u
    in [0, 1) placing it in a window, and per statistic (fine, then each band) and side
    (right, left) the records (pos, val, off) of its running maximum outward from the signal.
    Extended in place when a request needs more kept draws: a row's draws depend only on its
    row, so the draws are those of one simulation run at once."""
    key = _key(p, n, bands, snr, seed, _NF)
    sim = _SIGNAL_RECORDS.get(key)
    if sim is not None:
        _SIGNAL_RECORDS.move_to_end(key)
    else:
        # profiles alike in the gates' response share a simulation (_similar_get), whatever
        # window each searches: a job's banks have nearly one reference profile. It is
        # extended with its own profile, so it stays one simulation.
        params = (n, tuple(bands), snr, seed, _NF)
        unit, sim = _similar_get("signal-records", p, params)
        if sim is None:
            sim = dict(p=p, Fb=Fb, rows=0, t=np.empty(0, np.int64), u=np.empty(0), recs=None,
                       tab=None)
            _similar_put("signal-records", unit, params, sim, keep=_RECORDS_MAX)
        _SIGNAL_RECORDS[key] = sim
        while len(_SIGNAL_RECORDS) > _RECORDS_MAX:
            _SIGNAL_RECORDS.popitem(last=False)
    if sim["t"].size < kept:
        _extend_signal(sim, n, bands, snr, kept, seed)
    return sim


def _extend_signal(sim, n, bands, snr, kept, seed):
    """Simulate further rows of `sim` until it holds `kept` kept draws."""
    p, Fb = sim["p"], sim["Fb"]
    if sim["tab"] is None:
        k = np.arange(n)
        # the signal's response, per arrival fraction, for the fine statistic then each band
        # (bins [0, b), normalised as the band is): a band of b lags R apart at [rho b + e]
        # holds it at its lag e after the one rho samples before the signal, d = e R - rho
        # samples after it
        tab = np.empty((_NF, 1 + len(bands), n), np.complex64)
        for j in range(_NF):
            q = p * np.exp(-2j * np.pi * k * (j / _NF) / n)
            for s, (m, f) in enumerate([(n, 1.0)] + list(zip(bands, Fb))):
                resp = np.fft.ifft(np.where(k < m, q, 0.0) if m < n else q) * (n * snr / np.sqrt(f))
                R = n // m
                d = (np.arange(m)[None, :] * R - np.arange(R)[:, None]) % n
                tab[j, s] = resp[d].reshape(-1)
        sim["tab"] = tab
    # Draws whose fine statistic stays below snr at every lag cannot be kept by any window and
    # hold no records. About 0.6 are kept at a usual snr, far fewer at a large one, where only
    # signals arriving close to a sample reach snr (about 3% at snr = 1000): each step runs the
    # rows the kept share so far says are still needed (the first assumes all are kept), and
    # three standard deviations of their count more, so that a third step is rare; what it
    # overshoots stays for a later request. The model's noise blocks (_NOISE_BLOCKS) are the
    # first rows' noise alone, recorded as they run (a third of a row's work): later rows'
    # are left to noise_block_maxima, which simulates them should a request read that far.
    nkey = _key(p, n, bands, seed)
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
        recs, nrec = _simulate(p, n, bands, step, rows, seed, (sim["tab"], t, fi), noise, keep_at=snr)
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
    starts = off[:-1][keep]
    idx = np.repeat(starts - np.concatenate(([0], np.cumsum(cnt)[:-1])), cnt) + np.arange(cnt.sum())
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


def _simulate(p, n, bands, rows, row0, seed, signal=None, noise=True, keep_at=0.0):
    """Rows row0 .. row0 + rows of the gate model's one simulation (_core.simulate): with
    signal = (tab, t, fi) its records outward from the signal (none for a draw whose fine
    statistic is below keep_at at every lag), and with noise each band's records of the noise
    alone. A block's draws depend only on its row, so its noise alone is the same whichever
    call simulates it. Returns (signal records or None, noise records or None): per statistic
    and side (fine first, right then left), and per band, the records (pos, val, off); pos and
    val may be views of arrays a few percent longer."""
    from . import _core
    scale = (np.sqrt(p) / np.sqrt(2)).astype(np.float32)
    kmax = int(np.flatnonzero(p)[-1]) + 1
    bscale = tuple(float(_SIG / np.sqrt(p[:b].sum())) for b in bands)
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
                                     *sig, *noi, float(keep_at))
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


def _noise_records(p, n, bands, nsim, seed):
    """Per band, the records (pos int32, val float32, off int64) of each simulated block's
    running maximum of the band's normalised coarse statistic of the noise alone over its b
    lags, rows in order: row r's records are [off[r], off[r + 1]).

    The blocks are signal_draws' (_simulate), so a simulation of fewer blocks is a prefix of
    one of more: a request reads the prefix of a larger simulation held (a signal
    simulation's included), or extends a smaller one."""
    key = _key(p, n, bands, seed)
    hit = _NOISE_RECORDS.get(key)
    if hit is not None:
        _NOISE_RECORDS.move_to_end(key)
        have, recs = hit
        if nsim <= have:
            return tuple((pos[:off[nsim]], val[:off[nsim]], off[:nsim + 1]) for pos, val, off in recs)
    else:
        have, recs = 0, None
    _, new = _simulate(p, n, bands, nsim - have, have, seed)
    _add_noise_records(key, have, nsim - have, new)
    return _NOISE_RECORDS[key][1]


def noise_block_maxima(power, n, bands, nsim=_NOISE_BLOCKS, seed=_SEED, window=None):
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
    from ._windows import coarse_lags
    # the engine's coarse lags for the window (one sample past each end)
    counts = tuple(int(c1 - c0) for c0, c1 in (coarse_lags(n, b, win[0], win[1]) for b in bands))
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


#: CostModel's interpolation tables as arrays, per table (a model's rows do not change once
#: made): every chain priced asked np.log of the same few rows again, 117k times a job.
_LOG_TABLES = {}


def _log_table(rows, kind):
    """(log densities, values) of a CostModel table of (density, value) rows: the values as
    given ("cost"), log of their ratio to the density floored at 1 ("excess"), or log of the
    ratio ("ratio"), the arrays the interpolations read."""
    hit = _LOG_TABLES.get((id(rows), kind))
    if hit is not None and hit[0] is rows:
        return hit[1], hit[2]
    fs = np.log([r[0] for r in rows])
    if kind == "cost":
        vs = np.asarray([r[1] for r in rows], dtype=np.float64)
    elif kind == "excess":
        vs = np.log([max(r[1] / r[0], 1.0) for r in rows])
    else:
        vs = np.log([r[1] / r[0] for r in rows])
    _LOG_TABLES[(id(rows), kind)] = (rows, fs, vs)     # rows held: the id cannot be reused
    if len(_LOG_TABLES) > 4096:
        _LOG_TABLES.pop(next(iter(_LOG_TABLES)))
    return fs, vs


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

    def __init__(self, n, dense, sparse, refine, block=0.0, screen=None, excess=None,
                 feed=None):
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
        fs, vs = _log_table(rows, "cost")
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
                               getattr(self, "direct_lag", None), getattr(self, "direct_single", True),
                               None if self.feed is None else (tuple(sorted(self.feed["band"].items())),
                                                               self.feed["full"]))
        return sig

    def to_dict(self):
        return {"n": self.n, "block": self.block, "dense": self.dense,
                "feed": None if self.feed is None else {
                    "band": {str(b): v for b, v in self.feed["band"].items()},
                    "full": self.feed["full"]},
                "sparse": self._sparse, "refine": self._refine, "screen": self.screen,
                "excess": self.excess}

    @classmethod
    def from_dict(cls, d):
        return cls(d["n"], d["dense"], d["sparse"], d["refine"], block=d.get("block", 0.0),
                   screen=d.get("screen"), excess=d.get("excess"),
                   feed=d.get("feed"))

    def pass_excess(self, b, f):
        """Measured / modelled first-tier pass rate at band b and modelled density f (>= 1):
        1 for a gate that reports its statistic, larger for one that reports a bound."""
        rows = self.excess.get(int(b))
        if not rows:
            return 1.0
        fs, rs = _log_table(rows, "excess")
        return float(np.exp(np.interp(math.log(max(f, 1e-12)), fs, rs)))

    def screen_reach(self, b, reach1):
        """Modelled Q15 pass fraction from measured screen/float excess."""
        sc = self.screen.get(int(b))
        if sc is None or not sc["excess"]:
            return None
        fs, ratio = _log_table(sc["excess"], "ratio")
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

    def feed_delta(self, chain, reach, ntemplates):
        """Per-pair change from `block` of the forward this chain's calls take: the band
        forward at its widest band, or the full forward, as the backend decides from the
        chain's modelled refine probability reach[len(chain)] (band_forward_wanted,
        the call's own rule), each measured per block and spread over the templates. 0 where
        the backend has one feed."""
        if self.feed is None or not ntemplates:
            return 0.0
        top = int(max(chain))
        r = min(max(float(reach[len(chain)]), 0.0), 1.0)
        if band_forward_wanted(self.n, top, r) and top in self.feed["band"]:
            per = self.feed["band"][top]
        else:
            per = self.feed["full"]
        return per / float(ntemplates)

    def with_direct(self, lag_price, single_tier=True):
        """A copy that also prices a direct refine at lag_price ticks per lag of its window
        (HierarchicalFilter._direct_price): a chain whose last tier reports its coarse lag
        then refines a pair, with a window of half-width h coarse samples, at the cheaper of
        the measured whole-block refine and 2 h n / b + 1 lags, b its last band (refine_for;
        the window scales with n / b, so it favours chains ending in a wider band)."""
        import copy
        cm = copy.copy(self)
        cm.direct_lag = float(lag_price)
        # single_tier False: a one-tier chain's tier runs on the CPU's FP16 gate, which reports
        # no lag, so its survivors refine by transform (hmf.c hmf_tier.lagged).
        cm.direct_single = bool(single_tier)
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
                and (len(chain) > 1 or getattr(self, "direct_single", True)))

    def refine_for(self, chain, f, hw=None):
        """Ticks per refined pair for this chain at refine density f, with the direct refine's
        window half-width hw (None: the whole-block refine)."""
        r = self.refine(f)
        if hw is not None and self.prices_direct(chain):
            r = min(r, self.direct_lag * (2 * int(hw) * (self.n // int(chain[-1])) + 1))
        return r

    def chain_cost(self, chain, reach, hw=None):
        """reach[i] = P(a pair reaches tier i+1) for i = 0..k-1, reach[k] = P(reaches refine);
        hw the direct refine's half-width (refine_for)."""
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


#: plan_chain's candidates per (draws, chain, prune, half-widths): they do not depend on the
#: cost model, so every template group pricing the same profile and window reuses them.
_CAND_CACHE = OrderedDict()
_CAND_CACHE_MAX = 4096


def _halves(x):
    """(search half, fit half) of the detections x: its even rows and its odd rows, each
    contiguous. The detections are independent draws in simulation order, so the halves are
    independent of each other."""
    return np.ascontiguousarray(x[0::2]), np.ascontiguousarray(x[1::2])


def _distances(sig, lags, bands, chain, snr, n):
    """Per detection (kept_draws' rows), how far the fine maximum lies from the chain's last
    tier's coarse maximum, in that tier's coarse samples: the direct refine's window of
    half-width h around the coarse maximum holds the fine peak iff this is at most h
    (hmf.c refine_direct_pair)."""
    fat, cat = lags
    keep = sig[1][:, 0] >= snr
    return np.abs(fat[keep] - cat[keep, bands.index(chain[-1])]) / (n // int(chain[-1]))


def _halfwidths(dist, allow, cost, chain, n):
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
    hmax = int((top / cost.direct_lag - 1.0) // (2 * R))      # 2 h R + 1 lags priced below top
    srt = np.sort(dist)[::-1]
    hmin = max(1, int(math.ceil(srt[allow]))) if srt.size > allow else 1
    if hmax < hmin:
        return (None,)
    up = np.ceil(dist[dist > hmin]).astype(np.int64)
    return (None,) + tuple(sorted({hmin} | {int(h) for h in up[up <= hmax]}))


def plan_chain(sig, noise, bands, chain, fd, cost, n, snr, prune=False, ntemplates=None,
               memo=None, lags=None):
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
    if K < 0 or B.shape[0] < 1:
        return None
    dA = dB = None
    if lags is not None and cost is not None and cost.prices_direct(chain):
        dA, dB = _halves(_distances(sig, lags, bands, chain, snr, n))
    hws = _halfwidths(dA, _gm.window_allowance(float(fd), A.shape[0], B.shape[0]) if dA is not None
                      else -1, cost, chain, n)
    key = None if memo is None else tuple(memo) + (tuple(int(b) for b in chain), bool(prune), hws)
    cands = _CAND_CACHE.get(key) if key is not None else None
    if cands is None:
        dead = tuple(np.empty(0, np.int64) if h is None else np.flatnonzero(dA > h) for h in hws)
        cands = _chain_candidates(A, noise, cols, K, prune, dead)
        if key is not None:
            _CAND_CACHE[key] = cands
            while len(_CAND_CACHE) > _CAND_CACHE_MAX:
                _CAND_CACHE.popitem(last=False)
    else:
        _CAND_CACHE.move_to_end(key)
    best = None
    for pth, preach, lasts in cands:
        for hw, last in zip(hws, lasts):
            if last is None:
                continue
            th, reach = pth + (last[0],), preach + (last[1],)
            c = cost.chain_cost(chain, list(reach), hw) if cost is not None else _flop_cost(chain, list(reach), n)
            if ntemplates and getattr(cost, "feed", None):
                # the change from the feed `block` was measured with; pick_stable's tie window
                # is absolute-valued, so a change that takes a total below zero still compares
                c += cost.feed_delta(chain, list(reach), ntemplates)
            if best is None or c < best[0]:
                best = (float(c), th, reach, hw)
    if best is None:
        return None
    c, th, reach, hw = best
    fit = _fit(B, dB, th, hw, fd)
    if fit is None:
        return None
    thresholds, halfwidth = fit
    q15 = bool(cost.first_tier(chain[0], reach[1])[1]) if hasattr(cost, "first_tier") else False
    missed = 0 if hw is None else int(np.count_nonzero(dA > hw))
    return dict(chain=tuple(chain), thresholds=thresholds,
                reach=tuple(_reach(noise, cols, thresholds)), halfwidth=halfwidth, cost=c,
                q15=q15, search=dict(thresholds=th, reach=reach, halfwidth=hw, missed=missed, K=K))


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
    params = (n, float(snr), float(fd), int(max_tiers), int(floor), int(nsim), int(nsamp), win, _cost_sig(cost),
              # ntemplates prices the feed
              None if not getattr(cost, "feed", None) else int(ntemplates or 0))
    key = (_gm._profile_sig(p),) + params
    hit = _CHOICE_CACHE.get(key)
    if hit is not None:
        _CHOICE_CACHE.move_to_end(key)
        return hit
    unit, hit = _similar_get("choice", p, params)
    if hit is not None:
        _cache_put(_CHOICE_CACHE, key, hit)
        return hit
    out = _choose_chain(p, n, snr, fd, cost, max_tiers, floor, nsim, win, ntemplates, nsamp)
    _cache_put(_CHOICE_CACHE, key, out)
    _similar_put("choice", unit, params, out)
    return out


def _choose_chain(power, n, snr, fd, cost, max_tiers, floor, nsim, window, ntemplates=None,
                  nsamp=None):
    bands = usable_bands(power, n, floor)
    if not bands:
        return None, []
    nsamp = _gm._nsamp_for(fd) if nsamp is None else int(nsamp)
    drawn = signal_draws(power, n, bands, snr, nsamp, window=window, lags_too=True)
    if drawn is None:
        return None, []
    sig, lags = drawn
    noise = noise_block_maxima(power, n, bands, nsim=nsim, window=window)
    memo = ("choose", _gm._profile_sig(power), n, float(snr), float(fd), tuple(bands), window,
            int(nsim), int(nsamp))
    plans = []
    for chain in enumerate_chains(n, max_tiers, floor, bands=bands):
        pl = plan_chain(sig, noise, bands, list(chain), fd, cost, n, snr, prune=True,
                        ntemplates=ntemplates, memo=memo, lags=lags)
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
    key = _key(p, n, chain, float(snr), float(fd), win, int(nsim), int(nsamp), _cost_sig(cost))
    hit = _PLAN_CACHE.get(key)
    if hit is not None:
        _PLAN_CACHE.move_to_end(key)
        return hit
    sim_params = (n, chain, float(snr), float(fd), win, int(nsim), int(nsamp), _cost_sig(cost))
    unit, hit = _similar_get("plan", p, sim_params)
    if hit is not None:
        _cache_put(_PLAN_CACHE, key, hit)
        return hit
    bands = usable_bands(p, n, floor)
    if not set(chain) <= set(bands):
        return None
    drawn = signal_draws(p, n, bands, snr, nsamp, window=window, lags_too=True)
    if drawn is None:
        return None
    noise = noise_block_maxima(p, n, bands, nsim=nsim, window=window)
    out = plan_chain(drawn[0], noise, bands, list(chain), fd, cost, n, snr, lags=drawn[1])
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


