"""Helpers of the false-dismissal calibration tests (test_fdr_calibration, test_fdr_engine,
test_fdr_plans): the profiles they run on and a plan's modelled dismissal, against which each
counts its misses. The tests' claims are stated in test_fdr_calibration's docstring; they are
three modules so a sharded run (the sanitizers, conftest --shard) can spread them."""
import numpy as np

import matchedfilter as mf
import matchedfilter._core as _core
from matchedfilter import gatechain as gc
from spectral_profiles import SHAPE_NAMES, make_spectral_profile

SNR = 5.5
#: Two-sided binomial p-value below which a count is off budget. With ~40 cases a run, a
#: calibrated model fails one by chance about once in 25 runs at 1e-3; the errors these
#: tests exist for gave p < 1e-12.
ALPHA = 1e-3


def law(n, e):
    p = np.zeros(n)
    k = np.arange(1, n // 2)
    p[1:n // 2] = k.astype(float) ** e
    return p / p.sum()


def profile(name, n):
    if name.startswith("f^"):
        return law(n, float(name[2:]))
    p = make_spectral_profile(name, n).astype(np.float64)
    return p / p.sum()


PROFILES = ["f^-2", "f^-1", "f^0", "f^1"] + list(SHAPE_NAMES)


#: Independent model detections a plan's modelled dismissal is counted on (_modelled): at a
#: budget of 5% about 10,000 dismissed, 1% of its count's sd beside a test's ~10%.
MODELLED = 200000


def modelled(power, n, chain, thresholds, window=None):
    """The share of MODELLED detections of an independent model simulation (seed 977, not
    the plans' 13) that some tier of chain with these thresholds dismisses."""
    bands = gc.usable_bands(power, n)
    C, F = gc.signal_draws(power, n, bands, SNR, MODELLED, seed=977, window=window)
    det = F[:, 0] >= SNR
    lost = np.zeros(int(det.sum()), bool)
    for b, t in zip(chain, thresholds):
        lost |= C[det, bands.index(b)] < t
    return float(lost.mean())



def engine_misses(power, n, chain, fd, inj, window=None, seed=11):
    """(thresholds, detections, misses, modelled dismissal) of chain_thresholds' plan run
    through the C engine on inj injections."""
    plan = gc.chain_thresholds(power, n, SNR, fd, chain, window=window)
    assert plan is not None
    thr = [float(x) for x in plan["thresholds"]]
    want = modelled(power, n, chain, thr, window)
    w0, w1 = window or (0, n)
    h = np.sqrt(power).astype(np.complex64)
    full = mf.MatchedFilter(n, 1, 1)
    full.set_templates(np.conj(h)[None, :])
    hm = _core.HMF(n, 1, 1, list(chain), 8)
    hm.set_reference(power.astype(np.float32))
    hm.set_thresholds(thr)
    hm.set_template(0, np.conj(h))
    pk = np.empty((1, 1), dtype=mf.PEAK_DTYPE)
    cnt = np.empty(1, np.int32)
    ei, ev, mb = np.empty(0, np.int64), np.empty(0, np.complex64), np.empty(0, np.float32)
    rng = np.random.default_rng(seed)
    k = np.arange(n)
    det = miss = 0
    for _ in range(inj):
        # the engine reports a signal arriving at `lag` at n - lag: keep it inside the window
        lag = n - rng.uniform(w0 + 64, w1 - 64)
        d = (SNR * h * np.exp(2j * np.pi * lag * k / n)).astype(np.complex64)
        d += rng.standard_normal(n, dtype=np.float32) + 1j * rng.standard_normal(n, dtype=np.float32)
        full.set_data(d[None, :])
        r = full.run(binsize=n, threshold=SNR)
        at = int(r["index"][0, 0, 0])
        if abs(r["value"][0, 0, 0]) < SNR or abs(((at + lag + n / 2) % n) - n / 2) > 64:
            continue
        det += 1
        hm.set_data(0, d)
        hm.run(0, 1, 0, 1, n, SNR, w0, w1, ei, ev, mb, cnt, pk)
        miss += pk[0, 0]["index"] < 0 or abs(pk[0, 0]["value"]) < SNR
    return thr, det, miss, want

