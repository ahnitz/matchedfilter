"""The hierarchical filter (HierarchicalFilter): a gate chain of cheap coarse correlations
that refines on demand, and its resolved plan. Re-exported by the package."""
import hashlib
import math
import operator
import os
import sys
import threading
import time
import warnings
from types import SimpleNamespace
from typing import NamedTuple, Optional

import numpy as np

from . import _calibration

from . import _config
from . import _core
from . import gatechain as _gatechain
from . import _chains, _prices, _trial
from ._choice import _AUTOTUNE_LOCK, _autotune_enabled, _log_autotune  # noqa: F401
from ._results import PEAK_DTYPE, _Deferred, _SparsePeaks  # noqa: F401
from ._filter import MatchedFilter, _GPU_SIZES, _from_any, _valid_series_window  # noqa: F401


def _detach(res):
    """res with every array copied (raw CPU results reuse the plan's buffers)."""
    if isinstance(res, np.ndarray):
        return res.copy()
    if isinstance(res, tuple):
        parts = [_detach(x) for x in res]
        return type(res)(*parts) if hasattr(res, "_fields") else tuple(parts)
    if isinstance(res, list):
        return [_detach(x) for x in res]
    return res


def _uncovered_message(n, snr, fd):
    return (
        f"no gate chain for n={n} snr={snr:.2f} fd={fd:.0e}: the gate model cannot resolve "
        "the false-dismissal budget for this reference profile. Provide a reference with a "
        "localised correlation peak, or pin a chain and set its thresholds explicitly."
    )


def _band_features(power, m):
    """(in-band fraction, effective bandwidth in bins) at band m."""
    p = np.asarray(power, dtype=np.float64)
    p = np.where(p > 0, p, 0.0)
    tot = p.sum()
    if tot <= 0:
        return 0.0, 1.0
    inb = p[:m]
    s = inb.sum()
    if s <= 0:
        return 0.0, 1.0
    q = inb / s
    return float(s / tot), float(1.0 / np.sum(q ** 2))


# References without a localised correlation peak are outside automatic selection.
_BEFF_MIN = 8.0


def _uncovered_reference(power, n):
    """True when no candidate band has a localised peak to work with.

    A reference whose in-band power sits in a bin or two gives a correlation
    of nearly constant magnitude -- there is no peak to find coarsely and
    refine, so the hierarchical method does not apply. See `_BEFF_MIN`.
    """
    bands = _gatechain.candidate_bands(n)
    return bool(bands) and all(_band_features(power, b)[1] < _BEFF_MIN for b in bands)


def _normalize_chain(chain, n):
    """A chain as a tuple of strictly increasing power-of-two bands in [64, n)."""
    if isinstance(chain, (int, np.integer)):
        chain = (int(chain),)
    chain = tuple(int(b) for b in chain)
    if not chain:
        raise ValueError("a chain needs at least one band")
    for i, b in enumerate(chain):
        if b < 64 or b >= n or b & (b - 1):
            raise ValueError("chain bands must be powers of two, >= 64 and < n; got %s" % (chain,))
        if i and b <= chain[i - 1]:
            raise ValueError("chain bands must be strictly increasing; got %s" % (chain,))
    return chain


_Q15_BANDS = {}


def _q15_available(band):
    """Whether this machine's back end has a Q15 screen for a first tier at `band`."""
    band = int(band)
    if band not in _Q15_BANDS:
        try:
            _Q15_BANDS[band] = _core.MF(band, 1, 1).q15_lanes() > 0
        except (ValueError, AttributeError):
            _Q15_BANDS[band] = False
    return _Q15_BANDS[band]


# Cumulative host calibration work, for benchmark boundaries (not search timing).
_CPU_TRIAL_WORK = {"calls": 0, "seconds": 0.0}


def _record_cpu_trial(start):
    _CPU_TRIAL_WORK["calls"] += 1
    _CPU_TRIAL_WORK["seconds"] += time.perf_counter() - start


def _direct_refine_enabled():
    return _config.get("MF_DIRECT_REFINE")


class _Resolved(NamedTuple):
    """A hierarchical filter's resolved plan (docs/resolved-plan.md), immutable: one is
    computed per set of inputs (HierarchicalFilter._resolve)."""
    chain: tuple
    thresholds: tuple
    reach: Optional[float]           # the model's per-pair refine probability, or None
    fractions: Optional[tuple]       # each tier's share of the reference's power, or None
    direct_hw: Optional[int]         # the CPU direct refine's window half-width, or None


class HierarchicalFilter(MatchedFilter):
    """Matched filter that gates on cheap coarse correlations and refines on demand.

    Most of a template's SNR sits in the low part of its band. A gate chain
    correlates only low bands -- tier 0 at band b1 on every pair, tier i at
    band b_i on the survivors of tier i-1 -- and pays for the full correlation
    only for pairs that pass every tier.

        >>> hf = matchedfilter.HierarchicalFilter(1 << 12, ndata=16, ntemplates=16,
        ...                                       snr=5.5, fd=1e-2)
        >>> hf.set_reference(profile)          # expected output power per bin
        >>> hf.set_data(data_spectra)
        >>> hf.set_templates(template_spectra)
        >>> peaks = hf.run(binsize=1024, threshold=t)
        >>> hf.config, hf.refine_rate          # the chain in use, fraction refined

    Surviving pairs normally receive a full correlation and binned peak search;
    equivalent transform paths can differ by floating-point rounding. With
    :meth:`set_taps`, direct refinement can instead search near the last coarse
    candidate for a single-bin result. With several excursions this can return
    a smaller local maximum than the whole-bin search. ``MF_DIRECT_REFINE=0``
    disables that approximation. The gate can omit peaks; ``fd`` is its modelled
    false-dismissal target at strength ``snr``, shared between the chain's tiers.
    Use :class:`MatchedFilter` for an ungated full-bin search.

    The chain is chosen automatically from the reference: every chain of up to
    ``max_tiers`` bands is priced by a model (gate thresholds from the profile,
    noise pass rates simulated from it, tier costs calibrated on this machine),
    and the ones the model cannot separate are measured on the real workload
    (``MF_AUTOTUNE=0`` keeps the model's choice). Pin a chain with
    ``chain=(b1, b2, ...)``; pass explicit thresholds with
    :meth:`set_coarse_threshold` to skip the model entirely.
    """
    _is_hierarchical = True

    #: Tiers each device's engine executes.
    _MAX_TIERS = {"cpu": 8, "gpu": 2}

    def __init__(self, n, ndata=1, ntemplates=1, snr=5.5, fd=1e-2, chain=None,
                 device=None, *, valid=None, max_tiers=3, search_window=None):
        from .device import parse as _parse_device
        self.device = _parse_device(device)
        self.n = int(n)
        self.valid = _valid_series_window(self.n, valid)
        self.ndata = int(ndata)
        self.ntemplates = int(ntemplates)
        if self.ndata < 1 or self.ntemplates < 1:
            raise ValueError("ndata and ntemplates must be >= 1")
        if self.device.kind == 'cpu' and self.n > self._cpu_max_n:
            raise ValueError("CPU transform size %d exceeds this filter's limit of %d"
                             % (self.n, self._cpu_max_n))
        self.snr = float(snr)
        self.fd = float(fd)
        self.max_tiers = int(max_tiers)
        if self.max_tiers < 1:
            raise ValueError("max_tiers must be >= 1")
        #: Lags each block's peak search covers, (start, end) in samples; prices noise passes.
        self.search_window = None if search_window is None else (int(search_window[0]), int(search_window[1]))
        self._init_state()
        self._pending_ref = None
        self._cal_thr = None           # explicit per-tier thresholds, bypassing the model
        self._resolved = None          # the resolved plan (_resolve), until an input changes
        self._fs_snr = None
        self._hermitian = False
        self._mf = None
        self._q15 = False
        # The joint-trial arm this plan runs (_trial): DEFAULT, a lock, or a trial's arm. A plan
        # inside a bank is governed by the bank's trial and runs none of its own.
        self._arm, self._governed, self._forced = _trial.DEFAULT, False, False
        self._model_chain = None
        self._cfg_cache = {}            # chain -> (CPU plan, resolved plan, screen): cheap switches
        self._pinned = None if chain is None else _normalize_chain(chain, self.n)
        if self._pinned is not None and len(self._pinned) > self._MAX_TIERS[self.device.kind]:
            raise ValueError("this device executes chains of at most %d tiers"
                             % self._MAX_TIERS[self.device.kind])
        self._chain = self._pinned
        self.autotune_info = {"status": "pinned" if self._pinned else "uninitialized",
                              "winner": self._pinned, "shortlist": ()}
        if self.device.kind == "gpu":
            self._start_gpu()
            return
        if self._pinned is not None:
            self._mf = self._new_cpu_plan(self._pinned)

    # ---- plan --------------------------------------------------------------
    def _reads_real_series(self):
        """Whether run_series reads a real (float32) series as it is: the CPU plan
        transforms it at half size; a GPU forward reads its samples (one-stage forwards
        only, n <= 65536). Elsewhere a real series is widened."""
        if self._gpu is None:
            return self.device.kind == "cpu" and self.n >= 4
        return self.n <= 65536

    def _new_cpu_plan(self, chain):
        self._execution_policy = self._series_policy('hierarchical_series', chain[-1], self.ntemplates)
        grp = self._execution_policy.get('series_group', 32 if self.n <= 2048 else 16)
        plan = _core.HMF(self.n, self.ndata, self.ntemplates, list(chain), grp,
                         int(getattr(self, 'k', self.n) or self.n))
        if self._hermitian:
            plan.set_hermitian(True)
        if getattr(self, "_q15", False) and not plan.set_q15(True):
            self._q15 = False
        # The block forward's transform: a cost-model price (_cpu_forward_platform), not a
        # trial -- its effect is under the shared rule's tie margin of a whole call.
        self._pfft = _prices._cpu_forward_platform(self.n) and plan.set_platform_fft(True)
        taps = getattr(self, "_taps", None)
        if taps is not None:
            plan.set_taps(taps[0], taps[0].shape[1], taps[1])   # direct: with the thresholds
        return plan

    # ---- joint-trial arms (_trial) ----------------------------------------------
    # A plan's measured dimensions are its chain and the Q15 screen in front of its first tier
    # (docs/cpu-q15-gate.md: the screen changes no result -- the float tier re-runs every pair
    # it passes -- so only time is at stake). An arm label resolves to one (chain, screen):
    # DEFAULT is the model's chain and its screen setting; "chain=n:..." a chain this plan can
    # run, with the model's screen for it; "q15=0/1" the model's chain with the screen set
    # where its first band has one. A bank's arms (block sizes) leave a plan on its model.
    def _q15_model(self, chain):
        """The cost model's screen setting for chain (gatechain.CostModel.first_tier)."""
        with _AUTOTUNE_LOCK:
            return bool(_chains._Q15_MODEL.get((getattr(self, "_choice_key", None), tuple(chain)), False))

    def _q15_ok(self, chain):
        return self.device.kind == "cpu" and _q15_available(chain[0])

    def arm_config(self, label):
        """(chain, screen on) this plan runs for a joint-trial arm: a pinned or forced chain
        whatever the arm, else the arm resolved against this plan's model choice."""
        kind, v = _trial.parse_arm(label)
        if self._pinned is not None:
            # a pinned chain stands; only its screen is an arm (the model's setting: off)
            chain = tuple(self._pinned)
            q = v if kind == "q15" else False
            return chain, bool(q) and self._q15_ok(chain)
        if self._model_chain is None:
            if self._chain is None:
                self._chain = self._choose_chain()      # first use: the model's choice
                self._q15 = False
            if self._model_chain is None:               # a chain set without the model's
                c = tuple(self._chain)
                self._model_chain, self._feasible, self._shortlist = c, (c,), (c,)
        chain = self._model_chain
        if not self._forced and kind == "chain" and v[0] == self.n and v[1] in self._feasible:
            chain = v[1]
        q = v if kind == "q15" else self._q15_model(chain)
        return chain, bool(q) and self._q15_ok(chain)

    def _arm_q15(self, chain):
        """The screen setting this plan's arm gives chain."""
        kind, v = _trial.parse_arm(self._arm)
        q = v if kind == "q15" else (False if self._pinned is not None else self._q15_model(chain))
        return bool(q) and self._q15_ok(tuple(chain))

    def use_arm(self, label):
        """Run arm label from the next call on."""
        self._arm = str(label)
        if self._chain is not None:
            self._set_config(*self.arm_config(label))

    def lock_arm(self, label):
        """Run arm label from now on (a trial's lock): the other arms' plans are freed."""
        self.use_arm(label)
        self._cfg_cache = {}
        self.autotune_info.update(status="locked", winner=tuple(self._chain), arm=self._arm)

    def _set_config(self, chain, q15):
        """Run (chain, screen) from the next call on. A CPU plan keeps the plans it leaves, so
        a trial alternating arms does not rebuild them."""
        chain = tuple(chain)
        if chain != tuple(self._chain):
            if self._gpu is None and self._mf is not None:
                self._cfg_cache[tuple(self._chain)] = (self._mf, self._resolved, self._q15)
                hit = self._cfg_cache.pop(chain, None)
                if hit is not None:
                    self._chain = chain
                    self._mf, self._resolved, self._q15 = hit
                else:
                    self._switch_chain(chain)
            else:
                self._switch_chain(chain)
        if self._mf is not None and self._gpu is None:
            if bool(q15) != bool(self._q15):
                self._q15 = bool(q15) and bool(self._mf.set_q15(True))
                if not q15:
                    self._mf.set_q15(False)
        else:
            self._q15 = bool(q15)

    def _plan_trial_key(self):
        """A standalone plan's trial key: what its arms mean (block size, statistics, tiers,
        device; whether the direct refine is priced in)."""
        tiers = min(self.max_tiers, self._MAX_TIERS[self.device.kind])
        pin = "" if self._pinned is None else "|pin=" + ",".join(str(int(b)) for b in self._pinned)
        return "plan|%d|%g|%g|%d|%s%s%s" % (self.n, float(self._fs_snr or self.snr), float(self.fd),
                                            tiers, self.device,
                                            "" if self._direct_key() is None else "|direct", pin)

    def _trial_arms(self):
        """DEFAULT, then the model's other shortlisted chains (none for a pinned chain), then the
        screen both ways."""
        own = tuple(self._chain) if self._pinned is not None else self._model_chain
        arms = [_trial.DEFAULT]
        if self._pinned is None:
            arms += [_trial.chain_arm(self.n, c) for c in self._shortlist if tuple(c) != own]
        if self._q15_ok(own):
            arms += [_trial.q15_arm(True), _trial.q15_arm(False)]
        return arms

    def _plan_trial(self):
        """This standalone plan's open joint trial, or None: none for a plan a bank governs, a
        pinned or forced chain, MF_AUTOTUNE=0, or a plan with one arm. A lock (this process's
        or MF_COST_FILE's) is adopted here."""
        if self._governed or not _autotune_enabled():
            return None
        if self._chain is None:
            if self._pending_ref is None:
                return None
            self._chain = self._choose_chain()
            self._q15 = self._arm_q15(self._chain)
        if self._forced:
            return None
        key = self._plan_trial_key()
        w = _trial.winner(key)
        if w is None:
            arms = self._trial_arms()
            if len(arms) < 2:
                return None
            tr = _trial.trial(key, lambda: arms)
            w = tr.winner
            if w is None:
                return tr
        if self._arm != w or self.autotune_info.get("status") != "locked":
            self.lock_arm(w)
        return None

    def _load_held_templates(self, plan):
        """Load into plan the templates this filter was given: from its template source, or
        the copy it holds."""
        t = self._held_templates
        if t is None and getattr(self, "_template_source", None) is not None:
            t = np.ascontiguousarray(self._template_source(), dtype=np.complex64)
        if isinstance(t, np.ndarray):
            plan.set_template_batch(0, t)
        elif isinstance(t, list):
            for i, x in enumerate(t):
                if x is not None:
                    plan.set_template(i, x)

    def _restore_into(self, plan, templates=None):
        """Replay reference, templates and data into a freshly built plan."""
        if self._pending_ref is not None:
            plan.set_reference(self._pending_ref)
        if templates is None:
            self._load_held_templates(plan)
        else:
            plan.set_template_batch(0, templates)
        if self._held:
            if -1 in self._held:
                plan.set_data_batch(0, self._held[-1])
            else:
                for i, d in self._held.items():
                    if d is not None and i >= 0:
                        plan.set_data(i, d)

    def _ensure(self, templates=None):
        """The live plan, built on first use once the chain is known."""
        if self._mf is not None:
            return self._mf
        if self._chain is None:
            if self._pending_ref is None:
                raise ValueError("set a reference first (set_reference), or pin a chain")
            self._chain = self._choose_chain(); self._q15 = self._arm_q15(self._chain)
        self._mf = self._new_cpu_plan(self._chain)
        self._resolved = None
        self._restore_into(self._mf, templates)
        return self._mf

    def _execution_plan(self):
        """The CPU plan, with the resolved plan (_resolve) applied to it: once per plan and
        resolution (a new plan, or a changed input, applies it again)."""
        plan = self._ensure()
        r = self._resolve()
        d = self.__dict__
        if d.get("_applied_plan") is not plan or d.get("_applied_res") is not r:
            plan.set_thresholds(list(r.thresholds))
            if getattr(self, "_taps", None) is not None:
                if r.direct_hw is not None:
                    prices = _prices._direct_pair_prices(self.n, plan)
                    if prices is not None:
                        plan.set_direct_prices(*prices)
                plan.set_direct(r.direct_hw is not None, r.direct_hw or 1)
            self._applied_plan, self._applied_res = plan, r
        return plan

    def _resolve(self):
        """The resolved plan (docs/resolved-plan.md): chain, one threshold per tier, the
        model's refine reach, per-tier reference band fractions, and on the CPU the direct
        refine's half-width. Computed once, and again only
        after an input changes (every setter that changes one drops it)."""
        r = self.__dict__.get("_resolved")
        if r is not None:
            return r
        if self._chain is None:
            if self._pending_ref is None:
                raise ValueError("set a reference first (set_reference), or pin a chain")
            self._chain = self._choose_chain(); self._q15 = self._arm_q15(self._chain)
        chain = tuple(self._chain)
        thr = tuple(self._thresholds(required=True))
        f = hw = None
        if self._pending_ref is not None:
            ref = np.asarray(self._pending_ref, dtype=np.float64)
            tot = ref.sum()
            f = tuple(float(ref[:b].sum() / tot) if tot > 0 else 0.0 for b in chain)
        if self.device.kind == 'cpu':
            if getattr(self, "_taps", None) is not None:
                hw = self._direct_halfwidth(chain, list(thr))
        r = self._resolved = _Resolved(chain, thr, getattr(self, "_refine_reach", None), f,
                                       hw)
        return r

    def _direct_halfwidth(self, chain, thresholds, nsim=20000):
        """The direct refine's window half-width for this chain (gatechain.direct_halfwidth,
        plus one coarse sample), or None where it does not apply: off (MF_DIRECT_REFINE=0),
        or no reference to model it on."""
        if not _direct_refine_enabled() or self._pending_ref is None:
            return None
        hw, _, _ = _gatechain.direct_halfwidth(self._pending_ref, self.n, chain, thresholds,
                                               self._fs_snr or self.snr, self.fd,
                                               window=self.search_window, nsim=nsim)
        return hw + 1

    def _direct_prices(self, base):
        """{band: ticks per refined pair} of the direct refine with this plan's taps, for a
        chain whose last tier is that band (window from the single-tier model at the band);
        empty where the direct refine does not apply. Cached per reference and taps."""
        taps = getattr(self, "_taps", None)
        if taps is None or not _direct_refine_enabled() or self._pending_ref is None:
            return {}
        key = (float(self._fs_snr or self.snr), float(self.fd), self.search_window)
        hit = getattr(self, "_dprice", None)
        if (hit is not None and hit[0] == key and hit[2] is self._pending_ref
                and hit[3] is taps[0]):
            return hit[1]
        lagtap = _prices._direct_lagtap()
        L = 32.0 * max(1, int(round(float(np.mean(taps[1])) / 32.0)))   # as the chain key rounds it
        prices = {}
        if lagtap > 0:
            p = np.asarray(self._pending_ref, dtype=np.float64)
            for b in _gatechain.usable_bands(p / p.sum(), self.n):
                pl = _gatechain.chain_thresholds(self._pending_ref, self.n, self._fs_snr or self.snr,
                                                 self.fd, (b,), cost=base, window=self.search_window)
                if pl is None:
                    continue
                # The window the chain will run with (_resolve: the full draw count), not a
                # cheaper estimate: the half-width is a tail percentile, and at band 256 a tenth
                # of the draws gave 2 coarse samples against 62 (33 lags against 993), so the
                # model priced a direct refine the engine never ran and chose single-tier
                # chains 50% slower than the best (test27 leaves, dev2, 2026-10-24). The draws
                # are shared (gatechain._DIRECT_DRAWS), so pricing adds no simulation.
                hw = self._direct_halfwidth((b,), pl["thresholds"])
                lags = 2 * hw * (self.n // b) + 1
                # the correlation, plus the per-lag binning around it (~4 ticks a lag)
                prices[int(b)] = lagtap * L * lags + 4.0 * lags
        self._dprice = (key, prices, self._pending_ref, taps[0])   # held: identity is the key
        return prices


    def _switch_chain(self, chain):
        """Run a different configuration from now on, keeping loaded data and templates."""
        self._chain, self._q15 = tuple(chain), False
        self._resolved = None
        if self._gpu is not None:
            self._tdirty = True
            # A host plan built for the old chain (_execution_plan builds one for a timed
            # trial call) would take the new chain's thresholds: one per tier of a chain it
            # does not run. Rebuilt on next use.
            self._mf = None
            return
        self._mf = self._new_cpu_plan(self._chain)
        self._restore_into(self._mf)

    # ---- thresholds ----------------------------------------------------------
    def _thresholds(self, *, required=True):
        """One threshold per tier: explicit, or from the reference model."""
        self._refine_reach = None    # the model's per-pair refine probability (hier_peaks)
        if self._cal_thr is not None:
            if len(self._cal_thr) != len(self._chain):
                raise ValueError("explicit thresholds %s do not match chain %s" % (self._cal_thr, self._chain))
            return self._cal_thr
        if self._pending_ref is not None:
            pl = _gatechain.chain_thresholds(self._pending_ref, self.n, self._fs_snr or self.snr, self.fd,
                                             self._chain, cost=self._cost_model(),
                                             window=self.search_window)
            if pl is not None:
                th = tuple(float(x) for x in pl["thresholds"])
                for v in th:
                    if not np.isfinite(v) or v < 0 or v > float(np.finfo(np.float32).max):
                        raise ValueError("calibrated coarse threshold must be finite, nonnegative float32; got %r" % (th,))
                reach = pl.get("reach")
                if reach is not None and len(reach) > len(self._chain):
                    self._refine_reach = float(reach[len(self._chain)])
                return th
        if required:
            raise ValueError(
                "no calibrated coarse threshold for chain %s at n=%d: provide a reference and a "
                "resolvable budget, or set the thresholds explicitly" % (self._chain, self.n))
        return None

    def set_coarse_threshold(self, value):
        """Set the gate thresholds directly, bypassing the model.

        ``value`` is one number per tier of the pinned chain (a bare number
        for a one-tier chain). Each tier's coarse maximum is compared against
        its threshold; a pair that falls below any is dismissed. The guarantee
        becomes whatever these thresholds imply. Pass None to return to the model.
        """
        if value is None:
            self._cal_thr = None
            self._resolved = None
            return
        vals = (value,) if np.isscalar(value) else tuple(value)
        vals = tuple(float(v) for v in vals)
        for v in vals:
            if not np.isfinite(v) or v < 0 or v > float(np.finfo(np.float32).max):
                raise ValueError("coarse thresholds must be finite nonnegative float32, or None")
        if self._pinned is None:
            raise ValueError("explicit thresholds require an explicit band (a pinned chain)")
        if len(vals) != len(self._pinned):
            raise ValueError("chain %s needs %d thresholds" % (self._pinned, len(self._pinned)))
        self._cal_thr = vals
        self._resolved = None

    def set_first_stage(self, snr):
        """Calibrate the gate against `snr` rather than the constructor's.

        Final triggers are still cut at the threshold passed to :meth:`run`;
        this sets only where the gate decides a full reconstruction is needed.
        Pass ``None`` or a non-positive value to use the constructor's SNR.
        """
        self._fs_snr = float(snr) if snr is not None and float(snr) > 0 else None
        self._resolved = None

    def set_reference(self, power):
        """Set the reference SNR distribution: expected power per bin of the filter output.

        Only its shape matters. The profile must describe every template in
        this plan. Pass ``None`` to use each template's own band fraction
        (explicit thresholds only). Changing it recalibrates the thresholds of
        the chain in use.
        """
        if power is not None:
            p = np.ascontiguousarray(_from_any(power), dtype=np.float32)
            if p.shape != (self.n,) and p.shape != (getattr(self, 'k', self.n),):
                raise ValueError("reference must be a one-dimensional array of length %d" % self.n)
            if not np.isfinite(p).all() or np.any(p < 0) or not np.any(p > 0):
                raise ValueError("reference must be finite, nonnegative, with positive total power")
            if self._pending_ref is not None and np.array_equal(p, self._pending_ref):
                return
        self._resolved = None
        if self._gpu is not None:
            self._tdirty = True
        if power is None:
            self._pending_ref = None
            if self._mf is not None:
                self._mf.set_reference(None)
                self._reload_templates()
            return
        self._pending_ref = p.copy()
        self._cfg_cache = {}            # the other chains' plans hold the old reference
        if self._mf is not None:
            self._mf.set_reference(p)
            self._reload_templates()

    def _reload_templates(self):
        """After a reference change: the CPU plan's loaded templates were scaled for the old
        reference and are stale (it keeps no unscaled copy); load them again."""
        if self._template_ready is None or self._template_ready:
            self._load_held_templates(self._mf)

    # ---- chain choice ----------------------------------------------------------
    def _cost_model(self):
        """The costs of the device this plan runs on: chains rank differently on a GPU (a refined
        pair costs ~30 coarse pairs there against ~100 on a CPU core)."""
        if self.device.kind == "gpu":
            return _calibration.calibrate_costs_gpu(self.n, str(self.device))
        policy = self._series_policy('hierarchical_series', 0, self.ntemplates) or {}
        cm = _calibration.calibrate_costs(self.n, self.ntemplates,
                                        group=policy.get('series_group', _gatechain.default_series_group(self.n)))
        prices = self._direct_prices(cm)
        return (cm.with_direct(prices, single_tier=_gatechain.cpu_gate_kind() != "f16")
                if prices else cm)

    def _direct_key(self):
        """The direct refine's rounded tap length when it is priced into this plan's chain
        choice (HierarchicalFilter._direct_prices), else None: chain choices and locks are
        kept apart by it, since a cheaper refine changes which chain wins."""
        taps = getattr(self, "_taps", None)
        if taps is None or not _direct_refine_enabled() or self.device.kind != "cpu":
            return None
        return int(round(float(np.mean(taps[1])) / 32.0))

    def _choose_chain(self):
        """Pick a gate chain: the model prices every chain, measurement settles the close ones.

        The model need not be exact. It prunes: chains whose modelled cost is
        more than the model's error margin above the best cannot win and are
        never run. If more than one chain survives, plans sharing a shortlist
        run it round-robin on real calls, and the chain with the lowest
        measured time per pair is kept for all of them. MF_AUTOTUNE=0 keeps
        the model's choice.
        """
        if _uncovered_reference(self._pending_ref, self.n):
            raise ValueError(
                "the reference has no localised correlation peak at n=%d: every candidate "
                "band has an effective bandwidth below %.0f bins, so there is nothing for a "
                "coarse pass to localise -- use MatchedFilter. A reference like this is "
                "usually |h|^2 without the 1/S(f), or a spectrum with no low-frequency cutoff."
                % (self.n, _BEFF_MIN))
        if not _gatechain.candidate_bands(self.n):
            # No band fits below n/2 (n = 64): no chain to price, and pricing one (the cost
            # model's calibration) has no tier to time.
            raise ValueError(_uncovered_message(self.n, self.snr, self.fd))
        snr = self._fs_snr or self.snr
        tiers = min(self.max_tiers, self._MAX_TIERS[self.device.kind])
        ref = np.asarray(self._pending_ref, np.float64)
        prof = _gatechain._gm._profile_sig(ref / ref.sum())
        direct = self._direct_key()
        key = (self.n, float(snr), float(self.fd), tiers, self.search_window, prof, str(self.device),
               _gatechain.cpu_gate_kind() if self.device.kind == "cpu" else None, direct)
        with _AUTOTUNE_LOCK:
            hit = _chains._CHAIN_CHOICE.get(key)
        if hit is None:
            best, plans = _gatechain.choose_chain(self._pending_ref, self.n, snr, self.fd, ntemplates=self.ntemplates,
                                                  cost=self._cost_model(), max_tiers=tiers,
                                                  window=self.search_window)
            if best is None:
                raise ValueError(_uncovered_message(self.n, self.snr, self.fd))
            margin = _config.get("MF_CHAIN_MARGIN", _chains._CHAIN_MARGIN)
            # On a GPU the trial runs on whole batches in the search's own mode, so its cost
            # is a few segments: the model's best few are measured whatever their modelled
            # gap. The model prices device work only, and missed the faster chain by 38%
            # (n=2048: (256, 1024) priced 1.8 against 1.3, measured ~1.5 ms/segment faster).
            near = (lambda q: True) if self.device.kind == "gpu" else (
                lambda q: q["cost"] <= best["cost"] * (1.0 + margin))
            shortlist = tuple(q["chain"] for q in sorted(
                (q for q in plans if near(q)),
                key=lambda q: (q["chain"] != best["chain"], q["cost"])))
            hit = (tuple(best["chain"]), shortlist[:_chains._CHAIN_SHORTLIST_MAX if self.device.kind != "gpu"
                                                   else _chains._CHAIN_SHORTLIST_GPU],
                   tuple(tuple(q["chain"]) for q in plans))
            with _AUTOTUNE_LOCK:
                for q in plans:
                    _chains._Q15_MODEL[(key, tuple(q["chain"]))] = bool(q.get("q15", False))
            with _AUTOTUNE_LOCK:
                _chains._CHAIN_CHOICE[key] = hit
            _log_autotune("CHAIN n=%d model=%s shortlist=%s ranking=%s", self.n, hit[0], hit[1],
                          [(q["chain"], round(q["cost"], 1)) for q in plans[:6]])
        model_best, shortlist, feasible = hit
        forced = _config.get("MF_CHAIN_FORCE")
        self._forced = False
        if forced:
            # Measurement only (chain studies): every hierarchical plan of this n runs the
            # given bands, whatever its arm. "n:b1,b2;n2:b1" or "b1,b2" for every n.
            for part in forced.split(";"):
                pn, _, bands = part.rpartition(":")
                if not pn or int(pn) == self.n:
                    want = tuple(int(b) for b in bands.split(",") if b)
                    if want and len(want) <= tiers and all(b < self.n for b in want):
                        model_best, shortlist, feasible = want, (want,), (want,)
                        self._forced = True
        self._choice_key = key
        self._model_chain = tuple(model_best)
        self._shortlist = tuple(tuple(c) for c in shortlist) if _autotune_enabled() else shortlist[:1]
        self._feasible = tuple(tuple(c) for c in feasible)
        # The arm this plan runs (DEFAULT unless a trial or a lock says otherwise), resolved here.
        kind, v = _trial.parse_arm(self._arm)
        chain = self._model_chain
        if not self._forced and kind == "chain" and v[0] == self.n and v[1] in self._feasible:
            chain = v[1]
        self.autotune_info = {"status": "forced" if self._forced else "model", "winner": chain,
                              "shortlist": self._shortlist, "model": self._model_chain,
                              "arm": self._arm}
        return chain

    # ---- run ----------------------------------------------------------------
    def run_series(self, series, starts=None, win_start=None, win_end=None,
                   binsize=None, threshold=0.0, templates=None, raw=False,
                   decimated=None, bin_phase=None):
        parent_run = super().run_series

        def run():
            return parent_run(series, starts=starts, win_start=win_start, win_end=win_end,
                              binsize=binsize, threshold=threshold, templates=templates,
                              raw=raw, decimated=decimated, bin_phase=bin_phase)
        tr = self._plan_trial()
        if tr is None or tr.replaying:
            return run()
        full = templates is None or templates[1] >= self.ntemplates
        try:
            nblk = len(starts) if starts is not None else 1
        except TypeError:
            nblk = 0
        if not (full and nblk >= 2):
            # not the work the trial decides (a follow-up, one block): run as it stands
            with _AUTOTUNE_LOCK:
                w = tr.tick()
            if w is not None:
                self.lock_arm(w)
            return run()
        # A round of this plan's joint trial: every arm on this same call (_trial.run_round).
        # Raw CPU results reuse buffers, so DEFAULT's is copied before later arms run.
        begin = time.perf_counter()
        res = _trial.run_round(tr, [self], run, nblk * self.ntemplates * self.ndata, keep=_detach)
        if self._gpu is None:
            _record_cpu_trial(begin)
        return res

    def set_templates(self, spectra, index=None):
        if self._gpu is not None or index is not None:
            return super().set_templates(spectra, index=index)
        a = np.ascontiguousarray(_from_any(spectra), dtype=np.complex64)
        if a.ndim != 2:
            raise ValueError(f"expected 2D array of spectra, got {a.shape}")
        if a.shape[0] != self.ntemplates:
            raise ValueError(f"expected {self.ntemplates} templates, got {a.shape[0]}")
        if a.shape[1] == self.n:
            self._bandlimited, k = False, self.n
        elif a.shape[1] == self.n // 2:
            self._bandlimited, k = True, self.n // 2
        else:
            raise ValueError(f"expected shape ({self.ntemplates}, {self.n}) or ({self.ntemplates}, {self.n // 2}), got {a.shape}")
        rebuild = self._mf is None or getattr(self._mf, 'k', self.n) != k
        self.k = k
        self._cfg_cache = {}            # the other chains' plans hold the old templates
        self._held_templates = self._hold(a)
        if rebuild:
            self._mf = None
        # A new plan consumes this batch while restoring its state; regenerating it
        # from the template source here would duplicate both generation and ingestion.
        plan = self._ensure(templates=a)
        if not rebuild:
            plan.set_template_batch(0, a)
        self._mark_ready("template", None)

    def set_taps(self, taps, counts=None):
        """Each template's real FIR taps, for the direct refine on the CPU.

        taps (ntemplates, m) float32, row t's first counts[t] taps valid (all m when counts
        is None), the centre tap counts[t] // 2 at lag 0 -- the filter whose spectrum
        set_templates holds, at the data's sample rate (time_domain.template_spectra with
        tap and data rates equal). run_series then refines a survivor by direct correlation
        at the lags around its last tier's firing coarse lags wherever that is priced
        cheaper than a whole-block transform; MF_DIRECT_REFINE=0 turns it off."""
        taps = np.ascontiguousarray(taps, dtype=np.float32)
        if taps.ndim != 2 or taps.shape[0] != self.ntemplates:
            raise ValueError("taps must be (ntemplates, m) = (%d, m)" % self.ntemplates)
        counts = (np.full(self.ntemplates, taps.shape[1], np.int64) if counts is None
                  else np.ascontiguousarray(counts, dtype=np.int64))
        if counts.shape != (self.ntemplates,) or counts.min() < 1 or counts.max() > min(taps.shape[1], self.n):
            raise ValueError("counts must be (ntemplates,) in [1, min(m, n)]")
        self._taps = (taps, counts)
        self._dprice = None
        self._cfg_cache = {}
        if self._pinned is None and self._chain is not None and self.device.kind == "cpu":
            # The model priced the chain without the direct refine: choose again (the plan is
            # rebuilt on next use and replays reference, templates and data).
            self._chain, self._mf, self._resolved = None, None, None
        elif self._mf is not None:
            self._mf.set_taps(taps, taps.shape[1], counts)
            self._resolved = None               # the direct window is part of the resolved plan

    def direct_stats(self):
        """Direct-refine counters of the CPU plan ({} before one exists)."""
        return self._mf.direct_stats() if self._mf is not None else {}

    def set_hermitian(self, hermitian: bool):
        self._hermitian = bool(hermitian)
        if self._mf is not None:
            self._mf.set_hermitian(self._hermitian)
        # The GPU kernels take full spectra: half-length templates were unpacked when
        # set, so a change of convention re-unpacks them.
        if self._gpu is not None and getattr(self, "_gpu_packed", None) is not None:
            self.set_templates(self._gpu_packed)

    @property
    def hermitian(self):
        return self._hermitian

    @hermitian.setter
    def hermitian(self, value):
        self.set_hermitian(value)

    # ---- GPU -----------------------------------------------------------
    #
    # The coarse pass IS a matched filter on an m-point plan: the ordinary flat
    # filter at length `band`, on templates truncated to that band and scaled
    # by 1/sqrt(f). A supplied reference gives a common power fraction;
    # otherwise each coarse template is normalized by its own.
    def _start_gpu(self):
        if self.n not in _GPU_SIZES:
            raise ValueError(
                "device='gpu' supports n in %s; got %d"
                % (sorted(_GPU_SIZES), self.n))
        self._gpu = self._backend().Context(self.device.index)
        self._gdata = None  # series execution uses its own workspace
        self._gtmpl = None
        self._resolved = None

    def _gpu_calibration(self, threshold):
        """(chain, per-tier reference band fractions or None, per-tier thresholds), from the
        resolved plan (_resolve)."""
        r = self._resolve()
        return r.chain, r.fractions, r.thresholds

    def _coarse_templates(self, H, bands, f):
        """Coarse templates per tier: the first b bins scaled by 1/sqrt(band fraction)."""
        out = []
        for i, b in enumerate(bands):
            if f is None:
                power = H.real * H.real + H.imag * H.imag
                total = power.sum(axis=1, dtype=np.float64)
                frac = np.divide(power[:, :b].sum(axis=1, dtype=np.float64), total,
                                 out=np.zeros_like(total), where=total > 0)
                sc = np.divide(1.0, np.sqrt(frac), out=np.zeros_like(frac), where=frac > 0)[:, None].astype(np.float32)
            else:
                sc = np.float32(1.0 / np.sqrt(f[i])) if f[i] > 0 else np.float32(0.0)
            out.append(H[:, :b] * sc)
        return out

    def _grouped_dispatch(self, n, spec, H, groups, binsize, threshold, **kw):
        """The gate chain over every window group of one spectra batch, one submission."""
        chain, f, thr = self._gpu_calibration(threshold)
        ck = (chain, f, H.ctypes.data, H.shape)
        if getattr(self, "_ckey", None) != ck or self._tdirty:
            self._ct = self._coarse_templates(H, chain, f)
            self._ckey = ck
        ct = self._ct
        extra = {} if len(chain) == 1 else dict(cascade_band=chain[0], ct1=ct[1], raw_thr1=thr[1])
        res = self._gpu.hier_peaks_grouped(n, chain[-1], spec, H, ct[0], thr[0], groups, binsize,
                                           threshold, upload_tmpl=self._tdirty,
                                           refine_reach=getattr(self, "_refine_reach", None),
                                           **extra, **kw)

        def account(r):
            shp = r.shape if isinstance(r, _SparsePeaks) else r[0].shape
            self._gpairs += shp[0] * shp[1]
            self._gtrig += self._gpu.last_refinements
            self._gt1 += getattr(self._gpu, "last_tier1_survivors", 0) or 0
            return r
        if kw.get("async_submit"):
            return lambda: account(res())
        return account(res)

    def _gpu_dispatch(self, D, H, binsize, threshold, start, end, slot=None, async_submit=False,
                      **kw):
        """Run the gate chain and refinement without host survivor readback."""
        chain, f, thr = self._gpu_calibration(threshold)
        ck = (chain, f, H.ctypes.data, H.shape)
        if getattr(self, "_ckey", None) != ck or self._tdirty:
            self._ct = self._coarse_templates(H, chain, f)
            self._ckey = ck
        ct = self._ct
        if len(chain) == 1:
            res = self._gpu.hier_peaks(
                self.n, chain[0], D, H, ct[0], thr[0],
                binsize=binsize, threshold=threshold, window=(start, end),
                upload_data=self._ddirty, upload_tmpl=self._tdirty,
                slot=slot, async_submit=async_submit,
                refine_reach=getattr(self, "_refine_reach", None), **kw)
        else:
            res = self._gpu.hier_peaks(
                self.n, chain[1], D, H, ct[0], thr[0],
                binsize=binsize, threshold=threshold, window=(start, end),
                upload_data=self._ddirty, upload_tmpl=self._tdirty,
                cascade_band=chain[0], ct1=ct[1], raw_thr1=thr[1],
                slot=slot, async_submit=async_submit,
                refine_reach=getattr(self, "_refine_reach", None), **kw)
        self._ddirty = self._tdirty = False

        def account(r):
            shp = r.shape if isinstance(r, _SparsePeaks) else r[0].shape
            self._gpairs += shp[0] * shp[1]
            self._gtrig += self._gpu.last_refinements
            self._gt1 += getattr(self._gpu, "last_tier1_survivors", 0) or 0
            return r
        if async_submit:
            return lambda: account(res())
        return account(res)

    # ---- reporting -----------------------------------------------------------
    @property
    def config(self):
        """The gate chain in use: a tuple of bands."""
        if self._chain is None:
            if self._gpu is not None:
                self._gpu_calibration(self.snr)
            else:
                self._ensure()
        return tuple(self._chain)

    @property
    def stats(self):
        """``(pairs, refined)`` accumulated since construction."""
        if self._gpu is not None:
            return (self._gpairs, self._gtrig)
        return self._ensure().stats()

    def work_counts(self):
        """Cumulative work counters for matchedfilter._roofline: a dict with the chain
        (bands), pairs (block, template) seen by tier 0, passed (pairs each tier passed;
        the last tier's passes are the refines), refined, q15 (pairs the int16 screen
        passed to the float tier 0, or None when no screen ran) and, on the CPU, ticks per
        tier, refine, screen and whole series calls. GPU passes for tier 0 of a two-tier
        chain come from the backend's last_tier1_survivors; ticks are None there."""
        chain = tuple(self._chain) if self._chain else ()
        if self._gpu is not None:
            passed = ([self._gt1] if len(chain) == 2 else []) + [self._gtrig]
            return dict(backend="gpu", chain=chain, pairs=self._gpairs, passed=passed,
                        refined=self._gtrig, q15=None, ticks=None, ident=id(self))
        mf = getattr(self, "_mf", None)
        if mf is None:
            return dict(backend="cpu", chain=chain, pairs=0, passed=[0] * len(chain),
                        refined=0, q15=None, ticks=None, ident=None)
        st = mf.tier_stats()
        pairs, refined = mf.stats()
        q_on, q_passed, q_ticks = mf.q15_stats()
        return dict(backend="cpu", chain=tuple(int(b) for b, _, _ in st[:-1]), pairs=int(pairs),
                    passed=[int(p) for _, p, _ in st[:-1]],
                    checked=[int(c) for c in mf.tier_inputs()], refined=int(refined),
                    q15=int(q_passed), q15_on=bool(q_on),
                    ticks=dict(tiers=[int(t) for _, _, t in st[:-1]], refine=int(st[-1][2]),
                               q15=int(q_ticks), series=int(mf.series_ticks())),
                    ident=id(mf))

    @property
    def tier_stats(self):
        """Per logical tier ``(band, passed, ticks)``, then refine ``(n, refined, ticks)``.

        Passed counts include only pairs evaluated at that gate. With reordered
        gates they need not decrease in logical band order; work_counts()['checked']
        gives each gate's actual input count.
        """
        if self._gpu is not None:
            return None
        return self._ensure().tier_stats()

    @property
    def refine_rate(self):
        """Fraction of pairs that needed the full correlation.

        This is what the speedup rides on, and the first thing to look at when
        the filter is slower than expected. Counted over the plan's lifetime.
        """
        pairs, trig = self.stats
        return trig / pairs if pairs else 0.0
