"""Shared measurement for the coarse-gate tests.

Four copies of the same loop had accumulated across test_gate_population,
test_low_ratio_corner and test_heterogeneous_bank: build a bank, inject at
the design SNR, filter with the flat filter and the hierarchical one, and
count the peaks the flat filter reports that the hierarchical one does not.
They differed only in what they summed at the end.

Underscore-prefixed so pytest does not collect it as a test module.

Independent of tools/audit_threshold.py, whose injection harness provides
another check of model gate placement.
"""
import time

import numpy as np

import matchedfilter as mf
from test_api import noise, inspiral_power, template_with_power


def dismissal_by_template(n, H, reference, band, snr, fd, reps=12,
                          nb=64, amp=1.04, seed=23, threshold=None):
    """Per-template (detected, dismissed) for injections at `amp * snr`.

    Per template rather than aggregate because the SHAPE of the loss is
    what identifies its cause: flat across the bank means the threshold is
    simply too high, ordered by the template's own in-band fraction means
    the reference normalisation in hmf.c refresh_template(). Callers that
    only want the total sum the arrays.

    `amp` slightly above 1 so an injection at the detection threshold is
    actually detected by the flat filter; a pair the flat filter misses
    says nothing about the gate.
    """
    nt = H.shape[0]
    flat = mf.MatchedFilter(n, nb, nt)
    flat.set_templates(H)
    hier = mf.HierarchicalFilter(n, nb, nt, snr=snr, fd=fd, chain=band)
    hier.set_reference(reference)
    hier.set_templates(H)
    if threshold is not None:
        hier.set_coarse_threshold(threshold)
    ph = np.exp(2j * np.pi * np.arange(n) / n)
    rng = np.random.default_rng(seed)
    detected = np.zeros(nt, int)
    dismissed = np.zeros(nt, int)
    for _ in range(reps):
        D = noise((nb, n), rng)
        which = rng.integers(0, nt, nb)
        for b in range(nb):
            lag = int(rng.integers(0, n))
            D[b] += (amp * snr * H[which[b]] * ph ** lag).astype(np.complex64)
        flat.set_data(D)
        hier.set_data(D)
        a = flat.run(binsize=n, threshold=snr)
        c = hier.run(binsize=n, threshold=snr)
        for b in range(nb):
            t = which[b]
            if a["index"][b, t, 0] >= 0:
                detected[t] += 1
                dismissed[t] += int(c["index"][b, t, 0] < 0)
    return detected, dismissed


def noise_trigger_loss(n, H, reference, band, snr, fd, reps=12,
                       nb=64, seed=5):
    """(flat triggers, of which the gate dismissed) on PURE NOISE.

    Also asserts the
    one-sided guarantee, which has to hold on every population: the gate
    may dismiss, never promote.
    """
    nt = H.shape[0]
    flat = mf.MatchedFilter(n, nb, nt)
    flat.set_templates(H)
    hier = mf.HierarchicalFilter(n, nb, nt, snr=snr, fd=fd, chain=band)
    hier.set_reference(reference)
    hier.set_templates(H)
    rng = np.random.default_rng(seed)
    total = missed = 0
    for _ in range(reps):
        D = noise((nb, n), rng)
        flat.set_data(D)
        hier.set_data(D)
        a = flat.run(binsize=n, threshold=snr)
        b = hier.run(binsize=n, threshold=snr)
        fi, hi = a["index"], b["index"]
        total += int((fi >= 0).sum())
        missed += int(((fi >= 0) & (hi < 0)).sum())
        assert int(((fi < 0) & (hi >= 0)).sum()) == 0, \
            "band %d: the gate promoted a trigger the flat filter never had" \
            % band
    return total, missed


# Injection-based checks of the gate model (formerly tools/hmf_tune.py, which also
# regenerated the retired cost tables).

def measure(n, band, snr, trials, seed=13, batch=None, power=None,
            device=None, thr=None, fd=1e-3):
    """`band` is a gate chain (one band or a tuple of bands); `thr` one threshold per tier, or None
    for the library's own calibration."""
    """Measured (dismissal, seconds-per-pair) for one configuration.

    Both numbers come from the real filter.  Injections go into a batch of
    data spectra at once, which is how a caller drives it, so the time is
    throughput rather than per-call overhead, and the trial count needed to
    resolve 1e-4 stays affordable.

    `device` picks which implementation is being characterised. CPU and
    GPU use the same algorithm with different arithmetic precision.
    The flat filter stays on the same device as
    the hierarchical one: a dismissal is defined against what the flat
    filter found, and comparing across devices would fold their float
    differences into the answer.
    """
    if batch is None:
        batch = 64 if device in (None, "cpu") else 2048
    rng = np.random.default_rng(seed)
    if power is None:
        power = inspiral_power(n)
    power = np.ascontiguousarray(power, dtype=np.float32)
    # The statistic's distribution is fixed by how the SNR accumulates with
    # frequency, which is what the reference states.  A template whose own
    # power equals the reference reproduces that accumulation exactly, so it
    # stands in for any bank with the same profile -- including a ratio filter
    # whose own spectrum looks nothing like its output.
    H = template_with_power(n, power)
    flat = mf.MatchedFilter(n, ndata=batch, ntemplates=1, device=device)
    hf = mf.HierarchicalFilter(n, ndata=batch, ntemplates=1, snr=snr, fd=fd,
                               chain=band, device=device)
    hf.set_reference(power)
    if thr is not None:
        hf.set_coarse_threshold(thr if np.ndim(thr) else float(thr))
    flat.set_templates(H[None, :])
    hf.set_templates(H[None, :])

    detected = omitted = 0
    sec = 0.0
    npair = 0
    # exp(2 pi i k L / n) by table lookup rather than ph ** L. The phase
    # ramp only ever takes the n values already in the table, and a complex
    # power recomputes one from scratch per element: measured at 30.7 ms a
    # batch against 0.98 ms, and it was 77% of the whole cell -- the sweep
    # was spending its time building injections, not filtering them. The
    # lookup is also the more accurate of the two, since repeated powers
    # drift and an exact index does not.
    kidx = np.arange(n)
    ph_tab = np.exp(2j * np.pi * kidx / n)
    lag0 = 0
    for _ in range((trials + batch - 1) // batch):
        D = noise((batch, n), rng)
        # One vectorised injection per batch rather than `batch` Python
        # iterations. With the noise pooled this loop WAS the cell: 0.138s
        # of 0.254s at n=1024, against 0.039s of actual filtering. The lag
        # sequence is unchanged -- lag0 advances by 37 per trial and
        # carries across batches -- so the injected data is identical.
        lags = (lag0 + 37 * np.arange(1, batch + 1)) % n
        lag0 = int(lags[-1])
        ramp = ph_tab[(kidx[None, :] * lags[:, None]) % n]
        D += (snr * H[None, :] * ramp).astype(np.complex64)
        flat.set_data(D)
        hf.set_data(D)
        a_ = flat.run(binsize=n, threshold=snr, raw=True)
        t0 = time.perf_counter()
        b_ = hf.run(binsize=n, threshold=snr, raw=True)
        sec += time.perf_counter() - t0
        npair += batch
        ai = np.array(a_[0])[:, 0, 0]
        bi = np.array(b_[0])[:, 0, 0]
        hit = ai >= 0
        detected += int(hit.sum())
        omitted += int((bi[hit] < 0).sum())
    for o in (flat, hf):
        if getattr(o, "_gpu", None) is not None:
            o._gpu.destroy()
    return (omitted / detected if detected else 1.0), detected, sec / npair


def beff_of(p, m):
    """Effective bandwidth of the in-band power, in bins (participation ratio)."""
    q = np.asarray(p[:m], float)
    s = q.sum()
    if s <= 0:
        return 1.0
    q = q / s
    return float(1.0 / np.sum(q ** 2))


def make_ref(n, m, f, beff, tol=0.02):
    """Synthetic exponential profile with specified fraction and bandwidth.

    A cost-grid fixture, not an accuracy proxy: matching these two features
    does not fix scalloping. Accuracy checks also use real reference shapes.
    """
    lo, hi = 0.3, float(4 * m)
    k = np.arange(m)
    for _ in range(60):
        tau = 0.5 * (lo + hi)
        b = beff_of(np.exp(-k / tau), m)
        if abs(b - beff) < tol * beff:
            break
        if b < beff:
            lo = tau
        else:
            hi = tau
    p = np.zeros(n)
    p[:m] = np.exp(-k / tau)
    p[:m] *= f / p[:m].sum()
    out = np.arange(m, n // 2)
    if len(out):
        p[m:n // 2] = np.exp(-(out - m) / max(400.0, m / 4.0))
        p[m:n // 2] *= (1.0 - f) / p[m:n // 2].sum()
    return p.astype(np.float32)
