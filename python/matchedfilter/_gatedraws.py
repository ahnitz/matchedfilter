"""The draws a gate plan rests on.

A plan's thresholds are fitted on draws of every candidate band's coarse maximum beside the
fine maximum under signal, and priced on the noise pass rates of whole-block maxima
(gatechain's module docstring states the model). This module makes those draws and keeps
them: the profile's normal form and its usable bands, the signal table (drawn from the
samples' joint law, _signal_law, or simulated), the noise simulation's running-maximum
records, the window local to a signal that the planner reads, the store that lets a
profile reuse the results of one like it (_SIMILAR), and a reference's ProfileClass, which
works out once what follows from the reference alone for every plan it reaches.

gatechain plans on these and binds the public names here under its own.
"""
import functools
import math
from collections import OrderedDict
from itertools import combinations
import hashlib
import numpy as np

from . import gatemodel as _gm
from . import _config
from ._windows import coarse_lags
from . import _core
from . import _signal_law

_SIG = _gm._SIG
#: Sub-sample arrival fractions signal_draws spreads its signals over, 1/_NF apart, the sample
#: itself among them: at a high snr only a signal arriving near a sample reaches it on the
#: sampled grid (strata midpoints left no draw detected at snr = 1000). A signal's loss
#: between samples is second order in the offset, so 1/16 of a sample stands for any time.
_NF = 16
_MIN_BAND = 64

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
    facts = _gm._frozen_facts(power)
    if facts is None:
        return _band_offset(power, n, b)
    if ("k0", n, b) not in facts:
        facts["k0", n, b] = _band_offset(power, n, b)
    return facts["k0", n, b]


def _band_offset(power, n, b):
    """band_offset's computation, for 1 <= b < n // 2."""
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
    """`power` as a float64 profile of unit sum, read-only (gatemodel._freeze: its signature
    and band offsets are kept with it). A profile this returned is returned as it is."""
    if _gm._frozen_facts(power) is not None and power.shape == (n,):
        return power
    p = np.asarray(power, dtype=np.float64)
    if (p.shape != (n,) or not np.isfinite(p).all() or (p < 0).any() or p.sum() <= 0):
        raise ValueError("power must be a finite nonnegative length-n profile with positive sum")
    return _gm._freeze(p / p.sum())


def _key(p, n, bands, *rest):
    return (_gm._profile_sig(p), n, tuple(bands)) + tuple(rest)


def _cache_put(cache, key, value):
    cache[key] = value
    while len(cache) > _CACHE_MAX:
        cache.popitem(last=False)


_SIMILAR = {}           # (kind, n, bands, params) -> [((identity, unit, features), value, seq)]

#: Reuse tolerances: a profile takes a cached result of another only if their shapes agree
#: (cosine, a cheap first test) AND every candidate band's signal response sqrt(f_b) g_b
#: (in-band power fraction times the worst coarse-grid loss, _gate_features) agrees to this
#: relative tolerance. The response is what sets a gate's dismissal: 3% of it at band 128
#: (an O4 against an A+ reference, cosine 0.995) put a borrowed plan at 4.3x its budget, and
#: 5% PSD jitter moves it as much, so the cosine alone cannot tell them apart.
_REUSE_COS = 0.985
_REUSE_RESPONSE = 3e-3


def _gate_features(p, n, m=17):
    """Per candidate band b of n: sqrt(f_b) * g_b, f_b the band's share of the profile and g_b
    the smallest normalised in-band correlation over half a coarse step (the worst sub-grid
    offset). A profile's are worked out once, by its ProfileClass."""
    p = np.asarray(p, np.float64)
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


def _band_features(power, m, k0=0):
    """(in-band fraction, effective bandwidth in bins) at band m starting at k0."""
    p = np.asarray(power, dtype=np.float64)
    p = np.where(p > 0, p, 0.0)
    tot = p.sum()
    if tot <= 0:
        return 0.0, 1.0
    k0, khi = _band_slice(len(p), m, k0)
    inb = p[k0:khi]
    s = inb.sum()
    if s <= 0:
        return 0.0, 1.0
    q = inb / s
    return float(s / tot), float(1.0 / np.sum(q ** 2))


#: References without a localised correlation peak are outside automatic selection: every
#: candidate band's effective bandwidth (_band_features) below this many bins.
_BEFF_MIN = 8.0


class ProfileClass:
    """A reference profile at one transform size, and what follows from it alone.

    The plans of one root and channel (a top template's leaf banks in one detector) are
    handed one reference at each block size, and the chain choice, its thresholds and the
    screeners ask the same questions of it for every plan and every call: its normalised
    profile and that profile's signature, its band offsets, the bands that hold power, and
    whether a result the similarity store holds for another profile stands for it
    (_similar_get). This object answers each question once and is handed to every plan of
    the root and channel (TimeDomainFilterBank.set_reference makes one per reference and
    block size). Its identity is its content: equal profiles at one size have equal
    identities, whichever object holds them.

    It holds no plan, bank or other class, only its arrays and the answers, so it goes with
    the last plan that holds it (and, for one made from a bare array, when _CLASSES drops
    it, the oldest first past _CLASSES_MAX).

    Parameters
    ----------
    reference : numpy.ndarray
        The profile as a plan is handed it: nonnegative power per frequency bin, length n
        for every answer that needs the normalised profile. The class keeps this array, as
        it is, and makes it read-only.
    n : int
        The transform size.

    Attributes
    ----------
    reference : numpy.ndarray
        The profile as handed, read-only.
    n : int
        The transform size.
    """

    def __init__(self, reference, n):
        reference.setflags(write=False)
        self.reference = reference
        self.n = int(n)
        self._band_offsets = {}         # floor -> (candidate bands, their offsets, usable bands)
        self._chain_offsets = {}        # chain -> its bands' offsets
        self._reference_offsets = {}    # band -> band_offset of the reference as handed
        self._usable = {}               # floor -> usable_bands of the reference as handed
        self._resembles = {}            # identity of another profile -> whether this one takes its results

    @functools.cached_property
    def profile(self):
        """The reference normalised to unit sum (_norm_profile: float64, read-only)."""
        return _norm_profile(self.reference, self.n)

    @functools.cached_property
    def identity(self):
        """bytes: the SHA-1 digest of the normalised profile's bytes, then n."""
        return hashlib.sha1(self.profile.tobytes()).digest() + self.n.to_bytes(4, "little")

    @functools.cached_property
    def signature(self):
        """bytes: the normalised profile's signature (gatemodel._profile_sig), the key of the
        exact caches of choices and plans."""
        return _gm._profile_sig(self.profile)

    @functools.cached_property
    def unit(self):
        """The normalised profile scaled to unit length, float32: the similarity store's
        first test (cosine)."""
        return (self.profile / np.linalg.norm(self.profile)).astype(np.float32)

    @functools.cached_property
    def features(self):
        """The normalised profile's gate features at n (_gate_features)."""
        return _gate_features(self.profile, self.n)

    @functools.cached_property
    def uncovered(self):
        """True when no candidate band of the reference has a localised peak to work with: a
        reference whose in-band power sits in a bin or two gives a correlation of nearly
        constant magnitude, with no peak to find coarsely and refine (_BEFF_MIN)."""
        bands = candidate_bands(self.n)
        return bool(bands) and all(
            _band_features(self.reference, b, self.reference_offset(b))[1] < _BEFF_MIN
            for b in bands)

    def band_offsets(self, floor=_MIN_BAND):
        """The normalised profile's candidate bands from `floor`, their offsets (band_offset)
        and the bands among them that hold power.

        Parameters
        ----------
        floor : int, optional
            The narrowest band (default _MIN_BAND).

        Returns
        -------
        tuple
            (candidate bands, a tuple of their offsets k0, the list of usable bands).
        """
        hit = self._band_offsets.get(floor)
        if hit is None:
            p, n = self.profile, self.n
            c_bands = candidate_bands(n, floor)
            k0_cand = tuple(band_offset(p, n, b) for b in c_bands)
            bands = [b for b, k0 in zip(c_bands, k0_cand) if p[slice(*_band_slice(n, b, k0))].sum() > 0]
            hit = self._band_offsets[floor] = (c_bands, k0_cand, bands)
        return hit

    def chain_offsets(self, chain):
        """The normalised profile's offsets (band_offset) of the bands of `chain`, a tuple."""
        hit = self._chain_offsets.get(chain)
        if hit is None:
            hit = self._chain_offsets[chain] = tuple(band_offset(self.profile, self.n, b) for b in chain)
        return hit

    def reference_offset(self, band):
        """band_offset of the reference as handed (not normalised) at `band`, an int."""
        hit = self._reference_offsets.get(band)
        if hit is None:
            hit = self._reference_offsets[band] = band_offset(self.reference, self.n, band)
        return hit

    def usable_bands(self, floor=_MIN_BAND):
        """usable_bands of the reference as handed: the candidate bands from `floor` that hold
        some of its power, a list."""
        hit = self._usable.get(floor)
        if hit is None:
            hit = self._usable[floor] = usable_bands(self.reference, self.n, floor)
        return hit

    def resembles(self, identity, unit, features):
        """Whether this profile takes a result the similarity store holds for the profile of
        `identity` (whose unit vector and gate features are `unit` and `features`): their
        cosine at least _REUSE_COS and every gate feature within _REUSE_RESPONSE of this
        profile's, relative. Decided once for each such profile.

        Returns
        -------
        bool
        """
        hit = self._resembles.get(identity)
        if hit is None:
            feats = self.features
            hit = self._resembles[identity] = bool(
                float(np.dot(self.unit, unit)) >= _REUSE_COS
                and features.shape == feats.shape
                and np.all(np.abs(features - feats)
                           <= _REUSE_RESPONSE * np.maximum(np.abs(feats), 1e-12)))
        return hit

    @property
    def nbytes(self):
        """The bytes of its reference (what a reference cache that holds it counts)."""
        return self.reference.nbytes


#: Classes made from bare arrays (profile_class), by identity, the most recent last.
_CLASSES = OrderedDict()
_CLASSES_MAX = 4096


def profile_class(power, n):
    """The ProfileClass of `power` at transform size n.

    Parameters
    ----------
    power : ProfileClass or numpy.ndarray
        A class (returned as it is), or a profile: then the class of its normalised profile
        (_norm_profile), one per content, made on first use and held in _CLASSES.
    n : int
        The transform size.

    Returns
    -------
    ProfileClass

    Raises
    ------
    ValueError
        If `power` is a class of another transform size, or not a finite nonnegative
        length-n profile with positive sum.
    """
    if isinstance(power, ProfileClass):
        if power.n != int(n):
            raise ValueError("a profile class of n=%d asked for at n=%d" % (power.n, int(n)))
        return power
    made = ProfileClass(_norm_profile(power, n), n)
    held = _CLASSES.get(made.identity)
    if held is not None:
        _CLASSES.move_to_end(made.identity)
        return held
    _CLASSES[made.identity] = made
    while len(_CLASSES) > _CLASSES_MAX:
        _CLASSES.popitem(last=False)
    return made


def _similar_get(kind, profile, params):
    """The first result held under (kind,) + params for a profile `profile` (a ProfileClass)
    resembles, in the order they were put; None if there is none."""
    for (identity, unit, features), value, _ in _SIMILAR.get((kind,) + params, ()):
        if profile.resembles(identity, unit, features):
            return value
    return None


#: The most entries _SIMILAR holds of each kind over all its keys, the oldest dropped first.
#: A key's own list is bounded (_similar_put's keep), but a job meets new keys as long as it
#: runs -- a choice's key holds the cost model, which differs between template groups -- so
#: the keys were not: a worker of the 171,828-template search added about 290 choices and
#: plans a top template. A simulation is 10-30 MB and is held for the plain profile only (a
#: retention's is released once its draws are read, signal_draws); the others are a few kB.
_SIMILAR_MAX = {"signal-records": 8, "noise": 256, "plan": 4096, "choice": 8192}
_SIMILAR_COUNT = {}     # kind -> entries put since the kind was last counted (an upper bound)
_SIMILAR_SEQ = [0]


def _similar_put(kind, profile, params, value, keep=None):
    """Hold `value` for profiles like `profile` (a ProfileClass) under (kind,) + params: the
    key's newest `keep` entries, and of the kind's entries over all keys its newest
    _SIMILAR_MAX (an eighth are dropped at a time, oldest first, when the bound is passed)."""
    key = (kind,) + params
    lst = _SIMILAR.setdefault(key, [])
    _SIMILAR_SEQ[0] += 1
    lst.append(((profile.identity, profile.unit, profile.features), value, _SIMILAR_SEQ[0]))
    del lst[:-(keep or _CACHE_MAX)]
    cap = _SIMILAR_MAX.get(kind, 4096)
    _SIMILAR_COUNT[kind] = _SIMILAR_COUNT.get(kind, 0) + 1
    if _SIMILAR_COUNT[kind] > cap:
        held = sorted((e[2], k) for k, es in _SIMILAR.items() if k[0] == kind for e in es)
        drop = len(held) - (cap - cap // 8)
        if drop > 0:
            cut = held[drop - 1][0]
            for k in {k for _, k in held[:drop]}:
                kept = [e for e in _SIMILAR[k] if e[2] > cut]
                if kept:
                    _SIMILAR[k][:] = kept
                else:
                    del _SIMILAR[k]
        _SIMILAR_COUNT[kind] = min(len(held), cap - cap // 8)


#: The gate model's stream domain: its draws are _core.gauss_fill's (src/gauss.cc) at this
#: domain and the seed, counter-based, so any block's draws depend only on its position.
_DOMAIN_SIGNAL = 1
#: The gate model's simulation seed: signal_draws and noise_block_maxima read one simulation.
_SEED = 13


def _coarse_lags_padded(n, b, w0, w1, lag_pad=0):
    """Coarse-lag range `(c0, c1)` for band `b` widened by `lag_pad` coarse samples (`hmf.c`)."""
    lp = int(lag_pad)
    if lp <= 0:
        return coarse_lags(n, b, w0, w1)
    r = n // int(b)
    w0, w1 = int(w0), int(w1)
    if w0 < lp * r or w1 + lp * r > n:
        return 0, int(b)
    pad = 1 + lp
    c0 = w0 // r
    c0 = c0 - pad if c0 > pad else 0
    c1 = min(int(b), -(-w1 // r) + pad)
    return c0, max(c0 + 1, c1)


def _engine_lags(n, bands, window):
    """(w0, w1, c0, c1): the fine lags [w0, w1) and each band's coarse lags [c0, c1) the engine
    searches for `window` (hmf.c: one coarse sample past each end inside the block)."""
    w0, w1 = (0, n) if window is None else (int(window[0]), int(window[1]))
    lags = [coarse_lags(n, b, w0, w1) for b in bands]
    return w0, w1, tuple(c[0] for c in lags), tuple(c[1] for c in lags)


#: local_window: the signal's window is this many times the longer of the profile's
#: autocorrelation extent and the coarsest band's step, and the autocorrelation's extent is its
#: last lag at or above this fraction of its peak.
_LOCAL_LOBES = 4
_LOCAL_TAIL = 0.05
_LOCAL_WINDOWS = OrderedDict()


def local_window(power, n, bands, window=None):
    """The window the gate model draws its signals in when a search covers `window`: a window
    around the signal wide enough that a wider one changes nothing a gate's dismissal rests
    on, or `window` itself where that is no narrower.

    A plan's thresholds are quantiles of the detections' coarse maxima, a detection a signal
    whose fine statistic reaches snr somewhere in the window. Far from the signal the window
    holds noise alone, which can only raise a maximum: a plan made without it dismisses no
    more. Near the signal the window matters: the fine maximum is taken over the samples the
    signal's autocorrelation reaches, and each band's over its coarse lags beside the signal,
    so a window inside either selects other detections than the search's (planned on the
    signal's own sample alone, a gate dismissed 3-9% at a budget of 0.1%). The local window
    is therefore _LOCAL_LOBES times the longer of the autocorrelation's extent (its last lag
    at or above _LOCAL_TAIL of the peak, from the profile) and the coarsest band's step,
    rounded up to a power-of-two number of those steps and centred in the block on the
    coarsest band's grid. Every window of a profile at least that wide then shares one set of
    signal draws; the noise maxima stay those of the window searched (noise_block_maxima).

    MEASURED (notes/window_free_2026-11-13, 379,680 plans: 30 PSD-model profiles and the
    O2 and showcase H1 and L1 profiles, n 1024-4096, snr 5.5-8, fd 1e-2 and 1e-3, every chain
    of up to three tiers, production and whole-block windows, with and without tier-0 and
    tier-1 retention): planned on a local window of 32 to 256 samples the cheapest chain's
    dismissal on independent draws of the real window averaged 0.94-0.95 of the budget
    (exact plan 0.99) with no more cases beyond 1.5 budgets than the exact plan's; at 16
    samples, inside these profiles' autocorrelation, it failed at snr 8.
    """
    p = _norm_profile(power, n)
    w0, w1 = (0, int(n)) if window is None else (int(window[0]), int(window[1]))
    step = int(n) // int(min(bands))
    key = (_gm._profile_sig(p), int(n), step)
    span = _LOCAL_WINDOWS.get(key)
    if span is None:
        r = np.abs(np.fft.ifft(p))
        tail = np.flatnonzero(r[1:int(n) // 2 + 1] >= _LOCAL_TAIL * r[0])
        extent = int(tail[-1]) + 1 if tail.size else 1
        steps = -(-_LOCAL_LOBES * max(extent, step) // step)
        span = step * (1 << (steps - 1).bit_length())
        _LOCAL_WINDOWS[key] = span
        while len(_LOCAL_WINDOWS) > _CACHE_MAX:
            _LOCAL_WINDOWS.popitem(last=False)
    else:
        _LOCAL_WINDOWS.move_to_end(key)
    if span >= w1 - w0:
        return (w0, w1)
    lo = ((int(n) - span) // 2 // step) * step
    return (lo, lo + span)


#: Rows per block of the signal simulation's arrival draws (_arrivals): a row's arrival depends
#: only on its row, so a simulation extended in steps draws what one run at once draws.
_ARRIVAL_ROWS = 1 << 14
#: The signal simulation per (profile, n, bands, snr, seed), extended when a request needs
#: more draws. The planner reads it once, in the window local to the signal (local_window),
#: and a retention's is released when read (signal_draws): what stays is the plain profile's,
#: beside which a retention's band is simulated.
_SIGNAL_RECORDS = OrderedDict()


def signal_draws(power, n, bands, snr, ndet, seed=_SEED, window=None, lags_too=False,
                 alphas=None, _exact=False):
    """Joint draws of every band's coarse window maximum and the fine window maximum under a
    signal of strength snr: _signal_table's (which has the account of them), as plain
    arrays. The planner reads the table as it is held, where a retention's draws are its
    altered bands beside the plain draws (_Beside); here they are written out."""
    hit = _signal_table(power, n, bands, snr, ndet, seed=seed, window=window, lags_too=True,
                        alphas=alphas, _exact=_exact)
    if hit is None:
        return None
    (C, F), (fat, cat) = hit
    if not isinstance(C, _Beside):
        return hit if lags_too else hit[0]          # the held arrays themselves
    C, cat = C.full(), cat.full()
    return ((C, F), (fat, cat)) if lags_too else (C, F)


def _law_applies(n, window):
    """Whether the signal table for `window` of an n-point block is drawn from the samples'
    joint law (_signal_law) and not simulated: MF_SIGNAL_LAW, and a window of at most half
    the block. The law draws the samples next to the signal and takes the others as
    independent noise, which holds where the profile's correlations die out well inside the
    block -- there the planner's own window (local_window) is a small part of it. A profile
    whose correlations span the block (a steep red spectrum, narrow lines) is planned on the
    whole block, and simulated."""
    return _signal_law_enabled() and 2 * (int(window[1]) - int(window[0])) <= int(n)


def _law_profile(p, n, bands, snr, k0s):
    """The profile whose draws (_signal_law) stand for `p`'s: p itself, or an earlier profile
    alike in the gates' response (_similar_get), as a job's banks' simulations are shared."""
    params = (n, tuple(bands), float(snr), tuple(k0s))
    profile = profile_class(p, n)
    base = _similar_get("law-profile", profile, params)
    if base is None:
        _similar_put("law-profile", profile, params, p, keep=_RECORDS_MAX)
        return p
    return base


def _signal_law_enabled():
    """Whether the planner's signal table is drawn from the samples' joint law (_signal_law)
    where that holds (_law_applies), and not simulated: on unless MF_SIGNAL_LAW=0."""
    return bool(_config.get("MF_SIGNAL_LAW"))


def _far_maxima(p, n, bands, k0s, seed):
    """The law's far noise (_signal_law.signal_table's far_maxima): far_maxima(i, lags, u)
    gives, per draw j, the u[j] quantile of the maximum of band i's noise over lags[j]
    contiguous lags, from the running-maximum records of the model's noise blocks that its
    noise pass rates come from (_noise_records): the same blocks and, once simulated for
    either, no new simulation. A band's noise is circularly stationary over its lags, so any
    lags[j] contiguous lags have the same law, and u uniform draws it.

    The largest of as many independent noise samples bounds it: each lag's |z| <= x is a
    symmetric convex set, so by the Gaussian correlation inequality correlation only raises
    the chance that all of them hold. The simulated quantile passes the bound by its sampling
    error alone, where the lags are independent, and is held to the bound at the lower end of
    its quantile's bin, so that it is never above what the independent-noise law drew."""
    held = {}

    def far_maxima(i, lags, u):
        lags = np.asarray(lags, np.int64)
        lo, hi = int(lags.min()), int(lags.max())
        table = held.get(i)
        if table is None or lo < table[0] or hi >= table[0] + table[1].shape[0]:
            if "recs" not in held:
                held["recs"] = _noise_records(p, n, bands, _NOISE_BLOCKS, seed,
                                              **({"k0s": k0s} if any(k0s) else {}))
            pos, val, off = held["recs"][i]
            if table is not None:
                lo, hi = min(lo, table[0]), max(hi, table[0] + table[1].shape[0] - 1)
            rows = off.size - 1
            # each block's maximum over lags [0, m) for m in [lo, hi]: its last record below
            # m (records rise in lag), the few records at lo and beyond counted off its end
            late = np.flatnonzero(pos >= lo)
            block_of = np.searchsorted(off, late, side="right") - 1
            late_pos = pos[late]
            maxima = np.empty((hi - lo + 1, rows), np.float32)
            for m in range(lo, hi + 1):
                beyond = np.bincount(block_of[late_pos >= m], minlength=rows)
                maxima[m - lo] = val[off[1:] - 1 - beyond]
            # sorted per lag count, so that u reads the quantile (rising with u, as the
            # independent-noise law's did), and held to the independent bound
            maxima.sort(axis=1)
            at = np.arange(rows) / rows
            for m in range(lo, hi + 1):
                bound = np.sqrt(-2.0 * np.log1p(-np.minimum(at ** (1.0 / m), 1.0 - 1e-12)))
                np.minimum(maxima[m - lo], bound, out=maxima[m - lo])
            table = held[i] = (lo, maxima)
        rows = table[1].shape[1]
        at = np.minimum((np.asarray(u) * rows).astype(np.int64), rows - 1)
        return table[1][lags - table[0], at]

    return far_maxima


def _signal_table(power, n, bands, snr, ndet, seed=_SEED, window=None, lags_too=False,
                  alphas=None, _exact=False):
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
    apart. The maxima are over the whole of `window`, as the engine's are: no pairing with
    noise elsewhere in the block (_simulate). The planner asks for the window local to the
    signal (local_window) and takes the searched window's noise from noise_block_maxima; an
    audit asks for the searched window itself.

    Each draw holds its statistics' running-maximum records outward from the signal, so any
    window around it is two lookups: draw r's signal lies a_r + frac samples into the window,
    a_r uniform, and the window starts where the engine's would relative to the coarse grids
    (a_r = (t_r - w0) mod R_max + m R_max, m uniform; a draw whose a_r falls past the span
    is dropped, which keeps a_r exactly uniform).

    With lags_too, returns ((C, F), (fine_at, coarse_at)): where each draw's fine maximum and
    each band's coarse maximum lie, as block lags (coarse lags times the band's step), as the
    engine's direct refine compares them (hmf.c refine_direct_pair)."""
    p = _norm_profile(power, n)
    if alphas is None:
        bands = sorted(int(b) for b in bands)
        al = None
    else:
        ba = sorted((int(b), float(a)) for b, a in zip(bands, alphas))
        bands = [b for b, _ in ba]
        al_raw = tuple(round(max(0.0, min(1.0, a)), 6) for _, a in ba)
        al = al_raw if any(a < 1.0 for a in al_raw) else None
    k0s = tuple(band_offset(p, n, b) for b in bands)
    Fb = np.array([p[slice(*_band_slice(n, b, k0))].sum() for b, k0 in zip(bands, k0s)])
    if np.any(Fb <= 0):
        return None          # a band holding no power cannot gate; callers drop such bands (usable_bands)
    lags = _engine_lags(n, bands, window)
    ndet = int(ndet)
    extra = (k0s, al) if al is not None else ((k0s,) if any(k0s) else ())
    if _exact:
        extra = extra + ("exact",)
    key = _key(p, n, bands, float(snr), ndet, int(seed), lags, _NF, *extra)
    hit = _SIGNAL_CACHE.get(key)
    if hit is not None:
        _SIGNAL_CACHE.move_to_end(key)
        return hit[0] if not lags_too else hit
    if al is not None and not _exact and sum(a < 1.0 for a in al) > 1:
        # A band's draws under its retention are the same whatever the other bands' are
        # (each mixes its own bins of one row of independent noise, _core.simulate), so a
        # retention of several bands is its bands' single retentions side by side: their
        # columns, with nothing simulated that a single one has not been simulated for.
        hit = _beside_singles([
            (i, _signal_table(p, n, bands, snr, ndet, seed=seed, window=window, lags_too=True,
                              alphas=tuple(a if j == i else 1.0 for j, a in enumerate(al))))
            for i, a in enumerate(al) if a < 1.0])
        if hit is not None:
            _cache_put(_SIGNAL_CACHE, key, hit)
            return hit[0] if not lags_too else hit
    if not _exact and _law_applies(n, (lags[0], lags[1])):
        # the draws from the samples' joint law (_signal_law): no simulation
        C, F, at = _signal_law.signal_table(
            p, n, bands, [_band_slice(n, b, k0) for b, k0 in zip(bands, k0s)], float(snr), ndet,
            int(seed), lags, _far_maxima(p, n, bands, k0s, int(seed)), alphas=al, nf=_NF)
        hit = ((C, np.broadcast_to(F[:, None], C.shape)), at)
        if al is not None:
            hit = _beside_plain(hit, _signal_table(p, n, bands, snr, ndet, seed=seed, window=window,
                                                   lags_too=True))
        _cache_put(_SIGNAL_CACHE, key, hit)
        return hit[0] if not lags_too else hit
    sr_kw = {}
    if any(k0s):
        sr_kw["k0s"] = k0s
    if al is not None:
        sr_kw["alphas"] = al
    if _exact:
        sr_kw["_exact"] = True
    sim = _signal_records(p, n, bands, Fb, float(snr), ndet, int(seed), **sr_kw)
    while True:
        C, F, at = _signal_window(sim, n, bands, lags)
        det = np.flatnonzero(F >= snr)
        if det.size >= ndet:
            break
        # the window misses some of the block's detections: more, in proportion
        kept = sim["t"].size
        sim = _signal_records(p, n, bands, Fb, float(snr),
                              kept + int(math.ceil((ndet - det.size) * kept / max(det.size, 1))) + 1,
                              int(seed), **sr_kw)
    end = int(det[ndet - 1]) + 1 if ndet > 0 else 0
    C, F, at = C[:end], F[:end], (at[0][:end], at[1][:end])
    hit = ((C, np.broadcast_to(F[:, None], C.shape)), at)
    if al is not None and not _exact:
        # beside the plain draws of the same simulation (read now if they have not been)
        hit = _beside_plain(hit, _signal_table(p, n, bands, snr, ndet, seed=seed, window=window,
                                               lags_too=True))
    _cache_put(_SIGNAL_CACHE, key, hit)
    if al is not None and not _exact:
        # A retention's simulation is its band simulated again beside the plain one's
        # records. Its draws are read once, in the window local to the signal
        # (local_window), and those are held (here, under the profile simulated: the
        # planner asks with that profile, _choose_chain's p_base, so a retention's draws and
        # the plain ones it pairs them with row for row are one simulation's). The records
        # are not, and a request these draws no longer serve simulates the band again.
        _release_signal_records(sim)
    return hit[0] if not lags_too else hit


class _Beside:
    """A retention's table (its coarse maxima, or their lags) held beside the plain draws':
    `plain` the plain draws' array, `own` the retention's column for each band it alters.
    Every other column is the plain array's. Stands where the (M, bands) array would."""
    __slots__ = ("plain", "own", "shape", "__weakref__")

    def __init__(self, plain, own):
        self.plain, self.own, self.shape = plain, own, plain.shape

    def column(self, c):
        return self.own[c] if c in self.own else self.plain[:, c]

    def full(self):
        """The table written out: a copy of the plain one with the altered columns."""
        out = self.plain.copy()
        for c, col in self.own.items():
            out[:, c] = col
        return out


def _column(table, c):
    """Column c of a table of draws (an array, or a retention's _Beside)."""
    return table.column(c) if isinstance(table, _Beside) else table[:, c]


def _beside_plain(hit, plain):
    """A retention's draws ((C, F), (fat, cat)) as held beside the plain profile's `plain`
    (the same simulation's without the retention): the retention's fine maxima, their lags
    and every band it does not alter are the plain draws' own, so it holds the plain draws'
    arrays for those and a column of its own for each band it alters (_Beside) -- one or two
    columns where a whole table and its lags were held. What the planner derives from a
    column it derives once for the plain draws and every retention of them. Returned as it
    is where the two do not agree (never, for one simulation's; it is checked)."""
    (C, F), (fat, cat) = hit
    (Cp, Fp), (fatp, catp) = plain
    if (isinstance(Cp, _Beside) or C.shape != Cp.shape or not np.array_equal(F[:, 0], Fp[:, 0])
            or not np.array_equal(fat, fatp)):
        return hit
    altered = [i for i in range(C.shape[1])
               if not (np.array_equal(C[:, i], Cp[:, i]) and np.array_equal(cat[:, i], catp[:, i]))]
    if len(altered) == C.shape[1]:
        return hit
    own_c, own_at = {}, {}
    for i in altered:
        own_c[i] = np.ascontiguousarray(C[:, i])
        own_at[i] = np.ascontiguousarray(cat[:, i])
        own_c[i].setflags(write=False)
        own_at[i].setflags(write=False)
    return (_Beside(Cp, own_c), Fp), (fatp, _Beside(catp, own_at))


def _beside_singles(parts):
    """The draws of a retention of several bands, from its bands' single retentions: `parts`
    holds (band index, that band's retention alone as _beside_plain holds it). Returns the
    table with each of those columns beside the plain draws all of them stand beside, or
    None when they do not stand beside one plain table (a single retention that was not
    held as columns)."""
    own_c, own_at = {}, {}
    (C0, F0), (fat0, cat0) = parts[0][1]
    for i, ((C, F), (fat, cat)) in parts:
        if not (isinstance(C, _Beside) and isinstance(cat, _Beside) and C.plain is C0.plain
                and cat.plain is cat0.plain and set(C.own) <= {i} and set(cat.own) <= {i}):
            return None
        own_c.update(C.own)
        own_at.update(cat.own)
    return (_Beside(C0.plain, own_c), F0), (fat0, _Beside(cat0.plain, own_at))


def _release_signal_records(sim):
    """Drop the simulation `sim` from where it is held for reuse (_SIGNAL_RECORDS, and
    _SIMILAR's entries for profiles alike)."""
    for k in [k for k, v in _SIGNAL_RECORDS.items() if v is sim]:
        del _SIGNAL_RECORDS[k]
    for k in [k for k, es in _SIMILAR.items() if k[0] == "signal-records" and any(e[1] is sim for e in es)]:
        kept = [e for e in _SIMILAR[k] if e[1] is not sim]
        if kept:
            _SIMILAR[k][:] = kept
        else:
            del _SIMILAR[k]


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


def _prefix_record(rec, m_rows):
    pos, val, off = rec
    if off.size - 1 == m_rows:
        return rec
    return pos[:off[m_rows]], val[:off[m_rows]], off[:m_rows + 1]


def _signal_records(p, n, bands, Fb, snr, kept, seed, k0s=None, alphas=None, _exact=False):
    """signal_draws' simulation, with at least `kept` draws kept: a dict holding the profile
    it simulates and, per kept draw, the signal's integer arrival t in [0, R_max), a uniform u
    in [0, 1) placing it in a window, and per statistic (fine, then each band) and side
    (right, left) the records (pos, val, off) of its running maximum outward from the signal.
    Extended in place when a request needs more kept draws: a row's draws depend only on its
    row, so the draws are those of one simulation run at once."""
    k0s = (0,) * len(bands) if k0s is None else tuple(int(x) for x in k0s)
    al = tuple(float(a) for a in alphas) if (alphas is not None and any(a < 1.0 for a in alphas)) else None
    sub_idx = [i for i, a in enumerate(al) if a < 1.0] if al is not None else []
    use_base = 0 < len(sub_idx) < len(bands)
    extra = (k0s, al) if al is not None else ((k0s,) if any(k0s) else ())
    key = _key(p, n, bands, snr, seed, _NF, *extra)
    sim = _SIGNAL_RECORDS.get(key)
    if sim is not None:
        _SIGNAL_RECORDS.move_to_end(key)
    else:
        # profiles alike in the gates' response share a simulation (_similar_get): a job's
        # banks have nearly one reference profile. It is extended with its own profile, so
        # it stays one simulation.
        params = (n, tuple(bands), snr, seed, _NF) + extra
        sim = None if _exact else _similar_get("signal-records", profile_class(p, n), params)
        if sim is None:
            if use_base:
                base0 = _signal_records(p, n, bands, Fb, snr, kept, seed, k0s=k0s, alphas=None,
                                        _exact=_exact)
                p_sim, Fb_sim = base0["p"], base0["Fb"]
            else:
                p_sim, Fb_sim = p, Fb
            sim = dict(p=p_sim, Fb=Fb_sim, k0s=k0s, alphas=al, rows=0,
                       t=np.empty(0, np.int64), u=np.empty(0),
                       keep_mask=np.empty(0, np.uint8), recs=None, sub_recs=None, tab=None)
            # held as p's where p was looked up (its class asked the store), else as p_sim's
            _similar_put("signal-records", profile_class(p_sim if _exact else p, n), params, sim,
                         keep=_RECORDS_MAX)
        _SIGNAL_RECORDS[key] = sim
        while len(_SIGNAL_RECORDS) > _RECORDS_MAX:
            _SIGNAL_RECORDS.popitem(last=False)
    if sim["t"].size < kept:
        _extend_signal(sim, n, bands, snr, kept, seed, k0s=k0s, alphas=al)
    return sim


def _extend_signal(sim, n, bands, snr, kept, seed, k0s=None, alphas=None):
    """Simulate further rows of `sim` until it holds `kept` kept draws."""
    p, Fb = sim["p"], sim["Fb"]
    if k0s is None:
        k0s = sim.get("k0s") or ((0,) * len(bands))
    else:
        k0s = tuple(int(x) for x in k0s)
    if alphas is None:
        alphas = sim.get("alphas")
    sub_idx = [i for i, a in enumerate(alphas) if a < 1.0] if alphas is not None else []
    if 0 < len(sub_idx) < len(bands):
        base = _signal_records(p, n, bands, Fb, snr, kept, seed, k0s=k0s, alphas=None, _exact=True)
        target_rows = base["rows"]
        have_rows = sim["rows"]
        if have_rows < target_rows:
            sub_bands = [bands[i] for i in sub_idx]
            sub_k0s = tuple(k0s[i] for i in sub_idx)
            sub_al = tuple(alphas[i] for i in sub_idx)
            if sim["tab"] is None:
                sub_tab = np.zeros((_NF, 1 + len(sub_idx), n), np.complex64)
                for j, i in enumerate(sub_idx):
                    sub_tab[:, 1 + j] = base["tab"][:, 1 + i] * np.float32(alphas[i])
                sim["tab"] = sub_tab
            km_all = base["keep_mask"][:target_rows]
            n_kept_all = int(km_all.sum())
            t_all = np.zeros(target_rows, np.int64)
            t_all[km_all.astype(bool)] = base["t"][:n_kept_all]
            sub_nkey = _key(p, n, sub_bands, seed, sub_k0s, sub_al)
            sub_parts = [] if sim.get("sub_recs") is None else [sim["sub_recs"]]
            cur = have_rows
            while cur < target_rows:
                held = _NOISE_RECORDS.get(sub_nkey)
                noise_flag = (held[0] if held is not None else 0) == cur < _NOISE_BLOCKS
                end_r = min(target_rows, _NOISE_BLOCKS) if noise_flag else target_rows
                step = end_r - cur
                t_step = np.ascontiguousarray(t_all[cur:end_r])
                km_step = np.ascontiguousarray(km_all[cur:end_r])
                fi_step = ((cur + np.arange(step)) % _NF).astype(np.int32)
                srecs, nrec = _simulate(p, n, sub_bands, step, cur, seed,
                                        (sim["tab"], t_step, fi_step), noise_flag,
                                        keep_at=snr, k0s=sub_k0s, alphas=sub_al,
                                        kept_mask=km_step)
                if nrec is not None:
                    _add_noise_records(sub_nkey, cur, step, nrec)
                keep_b = km_step.astype(bool)
                sub_parts.append(tuple(_rows(r, keep_b) for r in srecs[2:]))
                cur = end_r
            sub_joined = tuple(_join_records([pt[q] for pt in sub_parts])
                               for q in range(2 * len(sub_idx)))
            sim["sub_recs"] = sub_joined
            merged = [_prefix_record(r, n_kept_all) for r in base["recs"]]
            for j, i in enumerate(sub_idx):
                merged[2 + 2 * i] = sub_joined[2 * j]
                merged[3 + 2 * i] = sub_joined[2 * j + 1]
            sim["recs"] = tuple(merged)
            sim["t"] = base["t"][:n_kept_all]
            sim["u"] = base["u"][:n_kept_all]
            sim["keep_mask"] = km_all
            sim["rows"] = target_rows
        return
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
            scale_s = n * snr / np.sqrt(f)
            if alphas is not None and alphas[s - 1] < 1.0:
                scale_s *= float(alphas[s - 1])
            resp = np.fft.ifft(qm, axis=1) * scale_s
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
    extra = (k0s, alphas) if alphas is not None else ((k0s,) if any(k0s) else ())
    nkey = _key(p, n, bands, seed, *extra)
    km_cur = sim.get("keep_mask")
    kms = [np.empty(0, np.uint8) if km_cur is None else km_cur]
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
                               keep_at=snr, k0s=k0s, alphas=alphas)
        if nrec is not None:
            _add_noise_records(nkey, rows, step, nrec)
        keep = np.diff(recs[0][2]) > 0          # a kept draw's fine maximum has a record
        kms.append(keep.astype(np.uint8))
        ts.append(t[keep]); us.append(u[keep])
        parts.append(tuple(_rows(r, keep) for r in recs))
        rows += step
        have += int(keep.sum())
    sim["keep_mask"] = np.concatenate(kms)
    sim["t"], sim["u"] = np.concatenate(ts), np.concatenate(us)
    sim["recs"] = tuple(_join_records([pt[q] for pt in parts]) for q in range(len(parts[0])))
    sim["rows"] = rows


def _last_within(rec, reach):
    """Per row of records (pos, val, off): the value of its last record at distance <= reach[r]
    (records rise with distance) and that distance, 0 and -1 where none is
    (_core.records_within)."""
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
    cat = np.empty((t.size, len(bands)), np.int32)
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
    fat = fat.astype(np.int32)
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
_RECORDS_MAX = 32
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


def _simulate(p, n, bands, rows, row0, seed, signal=None, noise=True, keep_at=0.0, k0s=None,
              alphas=None, kept_mask=None):
    """Rows row0 .. row0 + rows of the gate model's one simulation (_core.simulate): with
    signal = (tab, t, fi) its records outward from the signal (none for a draw whose fine
    statistic is below keep_at at every lag), and with noise each band's records of the noise
    alone. A block's draws depend only on its row, so its noise alone is the same whichever
    call simulates it. Returns (signal records or None, noise records or None): per statistic
    and side (fine first, right then left), and per band, the records (pos, val, off); pos and
    val may be views of arrays a few percent longer."""
    k0s = (0,) * len(bands) if k0s is None else tuple(int(x) for x in k0s)
    al_arg = (tuple(float(a) for a in alphas)
              if (alphas is not None and any(float(a) < 1.0 for a in alphas)) else None)
    if kept_mask is None:
        if al_arg is not None:
            sim_extra = (k0s, al_arg)
        else:
            sim_extra = (k0s,) if any(k0s) else ()
    else:
        sim_extra = None
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
    if signal is None:
        first = []
    elif kept_mask is not None:
        first = [0.0, 0.0] + [math.log(m) + 3 for m in bands for _ in (0, 1)]
    else:
        first = [math.log(m) + 3 for m in [n] + list(bands) for _ in (0, 1)]
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
        tail = (sim_extra if kept_mask is None
                else (k0s if any(k0s) else None, al_arg, kept_mask[done:done + todo]))
        sk, nk, got = _core.simulate(scale, stream, int(row0 + done), int(todo), kmax,
                                     tuple(int(b) for b in bands), bscale, float(_SIG), tab,
                                     None if t is None else t[done:done + todo],
                                     None if fi is None else fi[done:done + todo],
                                     *sig, *noi, float(keep_at), *tail)
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


def _noise_records(p, n, bands, nsim, seed, k0s=None, alphas=None):
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
    al = tuple(float(a) for a in alphas) if (alphas is not None and any(a < 1.0 for a in alphas)) else None
    sub_idx = [i for i, a in enumerate(al) if a < 1.0] if al is not None else []
    extra = (k0s, al) if al is not None else ((k0s,) if any(k0s) else ())
    key = _key(p, n, bands, seed, *extra)
    hit = _NOISE_RECORDS.get(key)
    if hit is not None:
        _NOISE_RECORDS.move_to_end(key)
        have, recs = hit
        if nsim <= have:
            return tuple((pos[:off[nsim]], val[:off[nsim]], off[:nsim + 1]) for pos, val, off in recs)
    else:
        have, recs = 0, None
    if 0 < len(sub_idx) < len(bands):
        base_recs = _noise_records(p, n, bands, nsim, seed, k0s=k0s, alphas=None)
        merged = [_prefix_record(r, nsim) for r in base_recs]
        for i in sub_idx:
            # each altered band on its own: its noise does not depend on the other bands'
            # retentions, and a band's is held once whichever retentions it is asked with
            own = _noise_records(p, n, [bands[i]], nsim, seed, k0s=(k0s[i],), alphas=(al[i],))
            merged[i] = _prefix_record(own[0], nsim)
        merged_t = tuple(merged)
        _NOISE_RECORDS[key] = (nsim, merged_t)
        _NOISE_RECORDS.move_to_end(key)
        while len(_NOISE_RECORDS) > _RECORDS_MAX:
            _NOISE_RECORDS.popitem(last=False)
        return merged_t
    _, new = _simulate(p, n, bands, nsim - have, have, seed, k0s=k0s, alphas=al)
    _add_noise_records(key, have, nsim - have, new)
    return _NOISE_RECORDS[key][1]


def noise_block_maxima(power, n, bands, nsim=_NOISE_BLOCKS, seed=_SEED, window=None,
                       alphas=None, lag_pads=None, _exact=False):
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
    if alphas is None and lag_pads is None:
        bands = sorted(int(b) for b in bands)
        al = None
        lps = (0,) * len(bands)
    else:
        al_in = (1.0,) * len(bands) if alphas is None else alphas
        lp_in = (0,) * len(bands) if lag_pads is None else lag_pads
        bal = sorted((int(b), float(a), int(lp)) for b, a, lp in zip(bands, al_in, lp_in))
        bands = [b for b, _, _ in bal]
        al_raw = tuple(round(max(0.0, min(1.0, a)), 6) for _, a, _ in bal)
        al = al_raw if any(a < 1.0 for a in al_raw) else None
        lps = tuple(max(0, lp) for _, _, lp in bal)
    k0s = tuple(band_offset(p, n, b) for b in bands)
    extra = (k0s, al) if al is not None else ((k0s,) if any(k0s) else ())
    if _exact:
        extra = extra + ("exact",)
    win = (0, n) if window is None else (int(window[0]), int(window[1]))
    # Each band's coarse statistic is circularly stationary over its lags (independent
    # bins), so a window's maximum depends only on how many lags it covers, not where:
    # simulate lags [0, count) per band, and windows of equal span share one simulation.
    counts = tuple(int(c1 - c0) for c0, c1 in (
        _coarse_lags_padded(n, b, win[0], win[1], lp) for b, lp in zip(bands, lps)
    ))
    key = _key(p, n, bands, int(nsim), int(seed), counts, *extra)
    hit = _NOISE_CACHE.get(key)
    if hit is not None:
        _NOISE_CACHE.move_to_end(key)
        return hit
    sim_params = (n, tuple(bands), int(nsim), int(seed), counts) + extra
    hit = None if _exact else _similar_get("noise", profile_class(p, n), sim_params)
    if hit is not None:
        _cache_put(_NOISE_CACHE, key, hit)
        return hit
    nr_kw = {}
    if any(k0s):
        nr_kw["k0s"] = k0s
    if al is not None:
        nr_kw["alphas"] = al
    recs = _noise_records(p, n, bands, int(nsim), int(seed), **nr_kw)
    out = np.empty((nsim, len(bands)), np.float32)
    for i, (pos, val, off) in enumerate(recs):
        # row r's maximum over lags [0, c) is its last record below c (records rise in lag)
        below = np.cumsum(pos < counts[i])
        last = below[off[1:] - 1] - np.concatenate(([0], below[off[1:-1] - 1]))
        out[:, i] = val[off[:-1] + last - 1]
    _cache_put(_NOISE_CACHE, key, out)
    _similar_put("noise", profile_class(p, n), sim_params, out)
    return out
