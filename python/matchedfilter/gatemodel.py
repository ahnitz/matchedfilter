"""The coarse gate's false-dismissal rate, computed rather than tabulated.

This replaces the ACC2 accuracy table. That table stored a measured
dismissal rate per (n, taps, snr, f, B_eff, gate) cell; this derives the
same quantity from the reference profile and the algorithm, with nothing
fitted.

WHY IT CAN BE COMPUTED AT ALL. The coarse and fine stages are both maxima
over lags of a matched-filter output, and they share their in-band noise.
For a normalised in-band profile q, the output at lag tau has

    signal            rho * sqrt(f) * A(tau - L)
    E[n(t1)n*(t2)]    A(t1 - t2)          where A(d) = sum_k q_k e^(2i.pi.k.d/n)

The noise covariance IS the signal response. So one function computed from
the profile fixes the entire joint distribution of the two stages, and the
only other inputs are the coarse band and the lag spacing -- both
properties of the algorithm.

WHY THE TABLE HAD TO GO, beyond the cost of measuring it:

  * Its key was insufficient. (f, B_eff) does not determine the gate's
    behaviour: a real |H|^2/S profile and a synthetic one matched on both
    dismiss 11.7x differently at the same gate, because B_eff is only a
    second-moment proxy for the scalloping that actually matters.
  * Half of it measured nothing. `taps` has no effect since the coarse
    stage stopped interpolating, and 3500 of 3500 cell pairs were
    bit-identical across it.
  * 46-61% of its cells were zero-count -- estimating a 1e-4 probability by
    counting -- so most of the measurement bought no information.

NOISE CONVENTION. Re and Im of the filter output each have variance 1, so
|z|^2 is chi2_2 with mean 2 and SNR=5 means |z|=5. A model written with
E|n|^2 = 1 is a factor sqrt(2) too narrow and under-disperses BOTH stages,
which is indistinguishable from a missing mechanism. It is not.

Validated against the filter across fifteen configurations -- three
profile shapes, bands 512/1024/2048, snr 5.0/5.5/6.0 -- at ratios 0.88 to
1.10, and against every device, which is how an approximation in the
coarse stage (the GPU already runs it in half precision) shows up as a
calibration change rather than passing quietly. See tests/test_gate_model.py.

The joint draws now live in gatechain, which takes them over every candidate
band at once so that a chain of tiers (and a single tier, its length-1 case)
is calibrated from one sample set. This module keeps the single-band view:
gate_for and dismissal, the quantities the validation above is stated in.
"""
import functools
import math

import numpy as np

#: Per-component variance is 1, so a complex draw normalised to E|z|^2 = 1
#: is scaled by this. See the noise-convention note above.
_SIG = np.sqrt(2.0)


#: Large profiles' signatures by the memory they hold ((data address, size, dtype) ->
#: (weakref to the owning array, sum and end bins, signature)): a bank prices its block sizes
#: on the full-resolution reference (2^19 bins), every leaf bank of a top is handed the same
#: array, and hashing it per bank cost 14 s of a Haswell job's setup. Keyed by address, not by
#: object: np.asarray(x, dtype) returns a new view of the same data. The sum and end bins guard
#: against an array changed in place.
_SIG_MEMO = {}
_SIG_MEMO_MIN = 1 << 16


def _profile_sig(power):
    """Signature of a profile's shape: its normalised bins to 2^-32 of the total, so only
    profiles equal to float rounding share it. (A 24-bin, 1%-quantised signature let profiles
    whose gates differ share a plan: an A+ reference took an O4 one's thresholds and dismissed
    4x its budget.) Near-identical profiles share plans through gatechain's reuse instead,
    which compares what the gates depend on (gatechain._similar_get)."""
    if power is None:
        return b""
    if isinstance(power, np.ndarray) and power.size >= _SIG_MEMO_MIN and power.flags.c_contiguous:
        import weakref
        owner = power
        while isinstance(owner.base, np.ndarray):
            owner = owner.base
        key = (power.__array_interface__["data"][0], power.size, power.dtype.str)
        check = (float(np.sum(power)), float(power.flat[0]), float(power.flat[-1]))
        hit = _SIG_MEMO.get(key)
        if hit is not None and hit[0]() is owner and hit[1] == check:
            return hit[2]
        sig = _profile_sig_uncached(power)
        try:
            ref = weakref.ref(owner, lambda _r, k=key: _SIG_MEMO.pop(k, None))
        except TypeError:
            return sig
        _SIG_MEMO[key] = (ref, check, sig)
        return sig
    return _profile_sig_uncached(power)


def _profile_sig_uncached(power):
    p = np.asarray(power, dtype=np.float64)
    tot = float(np.sum(p))
    if tot <= 0:
        return b""
    import hashlib
    quant = np.round(p / tot * 2.0 ** 32).astype(np.int64)
    return hashlib.sha1(quant.tobytes()).digest() + len(p).to_bytes(4, "little")


#: The per-plan tolerance of the false-dismissal budget (POLICY: roadmap decision D1, "fd is a
#: target and no plan is much worse"): at most _TAIL_SHARE of plans may dismiss more than
#: _TAIL_RATIO times fd. It sets how many draws the model takes (fit_order).
_TAIL_RATIO = 1.25
_TAIL_SHARE = 0.05

#: The most detections the model holds (RESOURCE): each holds its statistics' running-maximum
#: records, about 0.4 KB at n = 2048 (five bands) and 0.53 KB at 4096, so this is 0.7-0.9 GB.
#: It is the detections the 3,000,000-draw cap held before (about 0.58 of the draws are
#: detections at snr 5.5), and it reaches the tail bound down to fd = 5.5e-5. A budget
#: needing more refuses.
_MAX_DETECTIONS = 1750000


def _binom_cdf(k, m, q):
    """P(X <= k) for X ~ Binomial(m, q), summed from its terms."""
    if q <= 0.0:
        return 1.0
    if q >= 1.0:
        return 1.0 if k >= m else 0.0
    lq, lp = math.log(q), math.log1p(-q)
    lm = math.lgamma(m + 1)
    return min(1.0, sum(math.exp(lm - math.lgamma(i + 1) - math.lgamma(m - i + 1) + i * lq + (m - i) * lp)
                        for i in range(0, min(int(k), int(m)) + 1)))


def plan_tail(fd, m):
    """The probability that a plan fitted on m detections dismisses more than _TAIL_RATIO fd:
    its dismissal is the j-th smallest of m uniforms, j = round(fd (m + 1)) (fit_order), so
    this is P(Binomial(m, _TAIL_RATIO fd) <= j - 1)."""
    fd = float(fd)
    return _binom_cdf(int(round(fd * (m + 1))) - 1, int(m), min(1.0, _TAIL_RATIO * fd))


@functools.lru_cache(maxsize=None)
def fit_order(fd):
    """The order statistic j a plan's thresholds are fitted at: the smallest whose plans meet
    the tail bound (_TAIL_RATIO, _TAIL_SHARE).

    A plan's thresholds are fitted on M draws it was not chosen on (gatechain.plan_chain): the
    j-th smallest of their scores, M + 1 = round(j / fd). Given everything else in the plan,
    those draws are independent of it and the score is continuous, so the plan's dismissal is
    the j-th smallest of M uniforms: mean j / (M + 1) = fd, and above r fd with probability
    P(Binomial(M, r fd) <= j - 1) (plan_tail). For a small fd its sd is about fd / sqrt(j).
    Returns j."""
    fd = float(fd)
    j = 1
    while plan_tail(fd, int(round(j / fd)) - 1) > _TAIL_SHARE:
        j += 1
    return j


def _betabinom_sf(k, m, a, b):
    """P(X > k) for X ~ BetaBinomial(m, a, b), from its terms up to k."""
    lb = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    lm = math.lgamma(m + 1) - math.lgamma(m + a + b)
    below = sum(math.exp(lm - math.lgamma(x + 1) - math.lgamma(m - x + 1) + math.lgamma(x + a)
                         + math.lgamma(m - x + b) - lb) for x in range(0, min(int(k), int(m)) + 1))
    return max(0.0, 1.0 - below)


@functools.lru_cache(maxsize=None)
def window_allowance(fd, ma, mb):
    """The most of ma search-half detections the direct refine's window may miss, or -1 for
    none (gatechain._halfwidths).

    The fit (gatechain._fit) counts the window's misses among its mb detections as dismissed;
    where they alone reach j = round(fd (mb + 1)) the plan cannot be fitted with that window and
    refines by transform instead, a choice made on the fit half, which the fit's tail
    (plan_tail) does not cover. So a window is offered only where the predictive probability
    of that, given the m it misses on the search half, is at most the share of the tail bound
    the fit leaves, _TAIL_SHARE - plan_tail(fd, mb): then the plan exceeds _TAIL_RATIO fd with
    probability at most _TAIL_SHARE in all. The predictive count of misses among mb fresh
    detections is BetaBinomial(mb, m + 1/2, ma - m + 1/2), the binomial under the Jeffreys
    posterior of the miss rate. Returns the largest such m."""
    fd = float(fd)
    j = int(round(fd * (mb + 1)))
    room = _TAIL_SHARE - plan_tail(fd, mb)
    m = -1
    while m + 1 < min(j, ma + 1) and _betabinom_sf(j - 1, mb, m + 1.5, ma - m - 0.5) <= room:
        m += 1
    return m


def _nsamp_for(fd):
    """The detections the model draws at budget fd (draws the fine stage keeps; gatechain
    simulates until it has them), or None when the tail bound needs more than _MAX_DETECTIONS.

    Two halves, each of round(j / fd) - 1 detections, j = fit_order(fd): a plan's structure is
    searched on one and its thresholds fitted on the other (gatechain.plan_chain), so each
    half rests on about j dismissed draws. A pure function of fd and the tail bound: at fd
    1e-3, 2 x 47,999, about 167,000 draws at snr 5.5 (149,000-194,000 over the fdr_audit
    profiles), where 200/fd drew 200,000.
    """
    fd = float(fd)
    half = int(round(fit_order(fd) / fd)) - 1
    return 2 * half if 2 * half <= _MAX_DETECTIONS else None


def _validate(n, band, snr, fd):
    if (not isinstance(n, (int, np.integer)) or n < 64
            or not isinstance(band, (int, np.integer)) or band < 1
            or band > n or band & (band - 1) or n % band):
        raise ValueError("n must be divisible by a power-of-two band <= n")
    if not np.isfinite(snr) or snr <= 0:
        raise ValueError("snr must be finite and positive")
    if not np.isfinite(fd) or not 0 < fd < 1:
        raise ValueError("fd must be finite and between zero and one")


def _check_power(power, n):
    p = np.asarray(power, dtype=np.float64)
    if (p.shape != (n,) or not np.isfinite(p).all() or (p < 0).any()
            or not np.isfinite(p.sum()) or p.sum() <= 0):
        raise ValueError("power must be a finite nonnegative length-n profile with positive sum")
    return p


def _kept(power, n, band, snr, fd):
    """Sorted coarse maxima at `band` of the model's detections (draws the fine stage keeps)
    at budget fd, or None: each the maximum over the whole block, as the engine searches it
    (gatechain.signal_draws)."""
    from . import gatechain
    bands = gatechain.usable_bands(power, n)
    ndet = _nsamp_for(fd)
    if band not in bands or ndet is None:
        return None
    sig = gatechain.signal_draws(power, n, bands, snr, ndet)
    if sig is None:
        return None
    return np.sort(gatechain.kept_draws(sig, bands, (band,), snr)[:, 0])


def dismissal(power, n, band, snr, gate, fd_hint=1e-3):
    """Modelled false-dismissal rate of a single tier at `band` with threshold `gate`: the
    share of the model's detections at budget fd_hint below it, or None where it has none."""
    _validate(n, band, snr, fd_hint)
    if not np.isfinite(gate) or gate < 0:
        raise ValueError("gate must be finite and nonnegative")
    kept = _kept(_check_power(power, n), n, band, snr, fd_hint)
    if kept is None or not len(kept):
        return None
    return float(np.searchsorted(kept, float(gate)) / len(kept))


def gate_for(power, n, band, snr, fd):
    """The single-tier gate at `band` whose modelled dismissal is `fd`: the threshold of the
    length-1 chain (gatechain.chain_thresholds, fitted on half the model's detections).
    Returns None when the budget needs more detections than the model holds, so the caller
    refuses rather than guessing.
    """
    _validate(n, band, snr, fd)
    p = _check_power(power, n)
    if _nsamp_for(fd) is None:
        return None
    from . import gatechain
    if band not in gatechain.usable_bands(p, n):
        return None
    plan = gatechain.chain_thresholds(p, n, snr, fd, (band,))
    return None if plan is None else float(plan["thresholds"][0])
