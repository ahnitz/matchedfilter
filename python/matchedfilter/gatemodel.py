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
import numpy as np

#: Lag half-widths. The in-band correlation decays over ~n/B_eff samples,
#: a few coarse steps in the validated broad-band cases: nb=12/w=6 and
#: nb=4/w=3 agreed to 0.6% there. This is a local approximation, not a
#: convergence guarantee for arbitrary narrow bands; see docs/gate-model.md.
_NB = 4                      # coarse grid lags either side
_W = 3                       # fine integer lags either side

#: Per-component variance is 1, so a complex draw normalised to E|z|^2 = 1
#: is scaled by this. See the noise-convention note above.
_SIG = np.sqrt(2.0)


def _profile_sig(power):
    """Quantised signature of a profile, invariant to small PSD-estimation jitter."""
    if power is None:
        return b""
    p = np.asarray(power, dtype=np.float64)
    tot = float(np.sum(p))
    if tot <= 0:
        return b""
    p_norm = p / tot
    m = 24
    step = len(p_norm) // m
    if step >= 1:
        binned = p_norm[:m * step].reshape(m, step).sum(axis=1)
    else:
        binned = p_norm
    quant = (binned * 100.0).round().astype(np.int32)
    return quant.tobytes()


def _nsamp_for(fd):
    """Enough draws that the fd-quantile rests on a usable number of them.

    Scaled to the BUDGET, which the caller gives us. Roughly half the draws
    survive the detection cut, so 200/fd puts ~100 samples below the
    quantile -- about +-10%, inside the +-20% the budget is itself quoted
    to. A common fd=1e-2 costs 20k draws where a 1e-4 request needs 2M;
    flooring every gate at the tightest case made them all pay for the
    rarest one.

    Below the floor the quantile is not a measurement and gate_for returns
    None, so the caller refuses rather than guesses.
    """
    fd = max(float(fd), 1e-6)
    return int(min(max(2.0e4, 200.0 / fd), 3.0e6))


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
    """Sorted coarse maxima at `band` for draws the fine stage keeps, or None."""
    from . import gatechain
    bands = gatechain.usable_bands(power, n)
    if band not in bands:
        return None
    sig = gatechain.signal_draws(power, n, bands, snr, _nsamp_for(fd))
    if sig is None:
        return None
    return np.sort(gatechain.kept_draws(sig, bands, (band,), snr)[:, 0])


def dismissal(power, n, band, snr, gate, fd_hint=1e-3):
    """Modelled false-dismissal rate of a single tier at `band` with threshold `gate`."""
    _validate(n, band, snr, fd_hint)
    if not np.isfinite(gate) or gate < 0:
        raise ValueError("gate must be finite and nonnegative")
    kept = _kept(_check_power(power, n), n, band, snr, fd_hint)
    if kept is None or not len(kept):
        return None
    return float(np.searchsorted(kept, float(gate)) / len(kept))


def gate_for(power, n, band, snr, fd):
    """The largest single-tier gate at `band` whose modelled dismissal still meets `fd`.

    The length-1 chain of gatechain.chain_thresholds, from the same draws.
    Returns None when the budget is below what this many draws can place,
    so the caller refuses rather than guessing.
    """
    _validate(n, band, snr, fd)
    p = _check_power(power, n)
    if fd * _nsamp_for(fd) < 8:
        return None
    kept = _kept(p, n, band, snr, fd)
    if kept is None or not len(kept):
        return None
    idx = int(np.floor(float(fd) * len(kept)))
    if idx < 8:
        return None                      # too few draws below the budget
    return float(kept[idx])
