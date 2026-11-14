"""The hierarchical filter (HierarchicalFilter): a gate chain of cheap coarse correlations
that refines on demand, and its resolved plan. Re-exported by the package."""
import math
import time
from typing import NamedTuple, Optional

import numpy as np

from . import _calibration

from . import _config
from . import _core
from . import gatechain as _gatechain
from . import _chains, _choice, _prices, _settings, _trial
from ._choice import _AUTOTUNE_LOCK, _autotune_enabled, _log_autotune
from ._filter import MatchedFilter, _from_any


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


def _band_features(power, m, k0=0):
    """(in-band fraction, effective bandwidth in bins) at band m starting at k0."""
    p = np.asarray(power, dtype=np.float64)
    p = np.where(p > 0, p, 0.0)
    tot = p.sum()
    if tot <= 0:
        return 0.0, 1.0
    k0, khi = _gatechain._band_slice(len(p), m, k0)
    inb = p[k0:khi]
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
    return bool(bands) and all(
        _band_features(power, b, _gatechain.band_offset(power, n, b))[1] < _BEFF_MIN
        for b in bands
    )


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


_TIER0_PAIR_CENTROID = True
_TIER0_MAX_ARITY = 16
#: Skip building a wider first band's shared screeners when it loses even at the best ratio a
#: narrower band found (HierarchicalFilter._choose_chain). False builds them for every band
#: whose lower bound can win, as a check on the rule.
_TIER0_PRUNE_WIDER = True


def _tier0_centroid_enabled():
    return bool(_TIER0_PAIR_CENTROID)


def _tier0_min_clusters(band, is_cpu=True):
    """Minimum worthwhile cluster count above k <= 4 from the backend's SIMD tile width."""
    if not is_cpu:
        return 8
    try:
        qw = int(_core.MF(int(band), 1, 1).q15_lanes())
    except Exception:
        qw = 0
    return max(4, qw // 4) if qw > 0 else 4


def _pareto_tier0_candidates(raw_cands):
    """Distinct Pareto-undominated Tier-0 centroid candidates ordered from largest to smallest ratio."""
    distinct = []
    for cl in raw_cands:
        if cl is not None and (not distinct or cl.ratio <= distinct[-1].ratio - 0.05 + 1e-9):
            distinct.append(cl)
    if len(distinct) <= 1:
        return distinct
    kept = []
    aq = [math.floor(c.alpha * 200.0 + 1e-9) / 200.0 for c in distinct]
    for i, ci in enumerate(distinct):
        # Drop ci if a strictly smaller-ratio candidate j > i has >= quantized alpha and <= lag_pad
        if any(aq[j] >= aq[i] - 1e-12 and distinct[j].lag_pad <= ci.lag_pad
               for j in range(i + 1, len(distinct))):
            continue
        kept.append(ci)
    return kept


#: The step the direct refine's bin fractions are priced at (HierarchicalFilter._cost_model).
_PRICE_FRACTION_STEP = 0.05


class _Resolved(NamedTuple):
    """A hierarchical filter's resolved plan (docs/resolved-plan.md), immutable: one is
    computed per set of inputs (HierarchicalFilter._resolve)."""
    chain: tuple
    thresholds: tuple
    reach: Optional[float]           # the model's per-pair refine probability, or None
    fractions: Optional[tuple]       # each tier's share of the reference's power, or None
    direct_hw: Optional[int]         # the CPU direct refine's window half-width, or None
    offsets: tuple = ()              # per-tier starting fine bin k0


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
    noise pass rates simulated from it, tier costs calibrated on this machine).
    The model's best runs; the chain is not timed on the workload. A joint trial on
    the real workload can find another Q15 screen setting clearly faster
    (``MF_AUTOTUNE=0`` keeps the model's). Inside a ``TimeDomainFilterBank`` the bank's
    trial decides. Pin a chain with ``chain=(b1, b2, ...)``; pass explicit thresholds with
    :meth:`set_coarse_threshold` to skip the model entirely.
    """
    _is_hierarchical = True

    #: Tiers each device's engine executes.
    _MAX_TIERS = {"cpu": 8, "gpu": 2}

    def __init__(self, n, ndata=1, ntemplates=1, snr=5.5, fd=1e-2, chain=None,
                 device=None, *, valid=None, max_tiers=3, search_window=None):
        self._init_common(n, ndata, ntemplates, device, valid)
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
        self._tier0_clusters = {}
        self._tier0_cand_cache = {}
        self._tier1_clusters = {}
        self._clusters_allowed = False
        self._live_templates = None
        self._chosen_csig = ()
        self._synced_t0 = None
        self._synced_t1 = None
        self._gt0_checked = 0
        # The joint-trial arm this plan runs (_trial): DEFAULT, a lock, or a trial's arm. A plan
        # inside a bank is governed by the bank's trial and runs none of its own.
        self._arm, self._governed, self._forced = _trial.DEFAULT, False, False
        self._model_chain = None
        self._pinned = None if chain is None else _normalize_chain(chain, self.n)
        if self._pinned is not None and len(self._pinned) > self._MAX_TIERS[self.device.kind]:
            raise ValueError("this device executes chains of at most %d tiers"
                             % self._MAX_TIERS[self.device.kind])
        self._chain = self._pinned
        self.autotune_info = {"status": "pinned" if self._pinned else "uninitialized",
                              "winner": self._pinned}
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
        grp = int(self._execution_policy.get('series_group', _gatechain.default_series_group(self.n)))
        plan = _core.HMF(self.n, self.ndata, self.ntemplates, list(chain), grp,
                         int(getattr(self, 'k', self.n) or self.n))
        if self._hermitian:
            plan.set_hermitian(True)
        if getattr(self, "_q15", False) and not plan.set_q15(True):
            self._q15 = False
        taps = getattr(self, "_taps", None)
        if taps is not None:
            plan.set_taps(taps[0], taps[0].shape[1], taps[1], bool(taps[2]))
        return plan

    # ---- joint-trial arms (_trial) ----------------------------------------------
    # A plan's chain is the model's choice (or a pinned one, or MF_CHAIN_FORCE's), never a trial
    # arm: the best chain depends on the profile, and a pooled chain decision sampled on the
    # first banks of a search picked one that was faster there and 5-10% slower over the rest
    # (test67, Haswell and Ivy under load, 2026-10-26). Its measured dimension is the Q15 screen
    # in front of its first tier (docs/cpu-q15-gate.md: the screen changes no result -- the
    # float tier re-runs every pair it passes -- so only time is at stake). DEFAULT is the cost
    # model's screen setting for the chain; "q15=0/1" sets it where the first band has one.
    # A bank's arms (block sizes) leave a plan on DEFAULT.
    def _q15_model(self, chain):
        """The cost model's screen setting for chain (gatechain.CostModel.first_tier)."""
        with _AUTOTUNE_LOCK:
            return bool(_chains._Q15_MODEL.get((getattr(self, "_choice_key", None), tuple(chain)), False))

    def _q15_ok(self, chain):
        return self.device.kind == "cpu" and _q15_available(chain[0])

    def _arm_q15(self, chain):
        """The screen setting this plan's arm gives chain: the arm's, else the model's (off for a
        pinned chain, which the model did not price)."""
        q = _settings.moves(self._arm).get("q15")
        q = q if q is not None else (False if self._pinned is not None else self._q15_model(chain))
        return bool(q) and self._q15_ok(tuple(chain))

    def arm_config(self, label):
        """(chain, screen on) this plan runs for a joint-trial arm."""
        if self._chain is None:
            self._chain = self._choose_chain()          # first use: the model's choice
            self._q15 = False
        chain = tuple(self._chain)
        q = _settings.moves(label).get("q15")
        q = q if q is not None else (False if self._pinned is not None else self._q15_model(chain))
        return chain, bool(q) and self._q15_ok(chain)

    def use_arm(self, label):
        """Run arm label from the next call on."""
        self._arm = str(label)
        if self._chain is not None:
            self._set_q15(self.arm_config(label)[1])

    def lock_arm(self, label):
        """Run arm label from now on (a trial's lock)."""
        self.use_arm(label)
        self.autotune_info.update(status="locked", arm=self._arm)

    def _set_q15(self, on):
        """The screen on or off from the next call on."""
        if self._mf is not None and self._gpu is None:
            if bool(on) != bool(self._q15):
                self._q15 = bool(on) and bool(self._mf.set_q15(True))
                if not on:
                    self._mf.set_q15(False)
        else:
            self._q15 = bool(on)

    def _plan_trial_key(self):
        """A standalone plan's trial key: what its arms mean (block size, statistics, tiers,
        device, its chain; whether the direct refine is priced in)."""
        tiers = min(self.max_tiers, self._MAX_TIERS[self.device.kind])
        chain = ",".join(str(int(b)) for b in self._chain)
        cl = self._active_tier0_cluster(self._chain)
        ctag = "|t0=%g" % round(cl.ratio, 2) if cl is not None else ""
        return "plan|%d|%g|%g|%d|%s|%s%s%s" % (self.n, float(self._fs_snr or self.snr), float(self.fd),
                                               tiers, self.device, chain,
                                               "" if self._direct_key() is None else "|direct", ctag)

    def _tier0_cluster_eligible(self):
        """Return True when Tier-0 coarse centroid clustering applies to this plan."""
        tiers = min(self.max_tiers, self._MAX_TIERS[self.device.kind])
        dev_ok = (
            (self.device.kind == "cpu" and self._gpu is None)
            or (
                self.device.kind == "gpu"
                and self._gpu is not None
                and self._gpu._shipped("compactc", self.n)
            )
        )
        min_tiers = 1 if self.device.kind == "cpu" else 2
        return (self._clusters_allowed and tiers >= min_tiers and self.ntemplates >= 4
                and self._pinned is None and self._cal_thr is None
                and self._pending_ref is not None and len(self._pending_ref) == self.n
                and dev_ok and not self._hermitian and _tier0_centroid_enabled())

    def _templates_for_clustering(self):
        """Return current template spectra array without regenerating if already in memory."""
        for t in (self._live_templates, self._held_templates, getattr(self, "_gtmpl", None)):
            if isinstance(t, np.ndarray):
                return t
        src = getattr(self, "_template_source", None)
        if src is not None and (self._template_ready is None or self._template_ready):
            return np.ascontiguousarray(src(), dtype=np.complex64)
        return None

    def _tier0_candidates_for_band(self, band, templates=None, pass2=None):
        """Lazily build candidate Tier-0 clusters up to `_TIER0_MAX_ARITY` for `band`. `pass2`,
        when given, decides after each pass whether the next higher-arity pass is built
        (gatechain.cluster_tier0_candidates); a later call without it builds what was skipped."""
        max_k = int(_TIER0_MAX_ARITY)
        empty = (None,) * (2 if max_k <= 4 else int(math.ceil(math.log2(max_k))))
        if not self._tier0_cluster_eligible():
            return empty
        b = int(band)
        got = self._tier0_cand_cache.get(b)
        if got is not None and (got[1] or pass2 is not None):
            return got[0]
        usable = _gatechain.usable_bands(self._pending_ref, self.n)
        cand_ok = (b in usable) if self.device.kind == "cpu" else (len(usable) >= 2 and b in usable[:-1])
        if not cand_ok:
            self._tier0_cand_cache[b] = (empty, True)
            return empty
        tmpl = self._templates_for_clustering() if templates is None else templates
        if tmpl is None:
            return empty
        k0 = _gatechain.band_offset(self._pending_ref, self.n, b)
        min_cl = _tier0_min_clusters(b, is_cpu=self.device.kind == "cpu")
        step_ref = [0]
        skipped = [False]

        def wants_pass(prev_cl):
            step_ref[0] += 1
            cur_cap = 1 << step_ref[0]
            floor_cl = 2 if cur_cap < 4 else min_cl
            if (int(prev_cl.offsets.size) - 1) <= floor_cl:
                return False
            if pass2 is not None and not bool(pass2(prev_cl, cur_cap)):
                skipped[0] = True
                return False
            return True

        def call_pass2(prev_cl):
            try:
                return wants_pass(prev_cl)
            except TypeError:
                floor_cl = 2 if (1 << step_ref[0]) < 4 else min_cl
                if (int(prev_cl.offsets.size) - 1) <= floor_cl:
                    return False
                ok = bool(pass2(prev_cl))
                if not ok:
                    skipped[0] = True
                return ok

        cands = _gatechain.cluster_tier0_candidates(
            tmpl, self._pending_ref, self.n, b, k0=k0, max_arity=max_k, pass2=call_pass2
        )
        self._tier0_cand_cache[b] = (cands, not skipped[0])
        return cands

    def _tier0_cluster_for_band(self, band, templates=None, forced_chain=None):
        """Lazily compute and memoize `Tier0Cluster` (or `None`) for `band` under `_pending_ref`."""
        if not self._tier0_cluster_eligible():
            return None
        b = int(band)
        if b in self._tier0_clusters:
            return self._tier0_clusters[b]
        raw_cands = self._tier0_candidates_for_band(b, templates=templates)
        cands = _pareto_tier0_candidates(raw_cands)
        if not cands:
            self._tier0_clusters[b] = None
            return None
        # Compare candidate arities against unclustered cost from smallest ratio upward
        snr = self._fs_snr or self.snr
        is_cpu = self.device.kind == "cpu"
        min_len = 1 if is_cpu else 2
        base_cm = self._cost_model(cluster_ratios={})
        use_forced = forced_chain is not None and len(forced_chain) >= min_len and forced_chain[0] == b
        tiers = min(self.max_tiers, self._MAX_TIERS[self.device.kind])
        if use_forced:
            pl_uncl = _gatechain.chain_thresholds(
                self._pending_ref, self.n, snr, self.fd, forced_chain,
                cost=base_cm, window=self.search_window
            )
            best_cost = float("inf") if pl_uncl is None else (
                pl_uncl["cost"] + base_cm.feed_delta(
                    forced_chain, pl_uncl["reach"], self.ntemplates, pl_uncl.get("halfwidth")
                )
            )
        else:
            _, uncl_plans = _gatechain.choose_chain(
                self._pending_ref, self.n, snr, self.fd, ntemplates=self.ntemplates,
                cost=base_cm, max_tiers=tiers, window=self.search_window, first=b
            )
            best_cost = min((q["cost"] for q in uncl_plans), default=float("inf"))
        best_cl = None
        for cand in reversed(cands):
            cm_cand = base_cm.with_tier0_cluster({b: cand.ratio}, single_tier=is_cpu)
            if use_forced:
                pl_lb = _gatechain.chain_thresholds(
                    self._pending_ref, self.n, snr, self.fd, forced_chain,
                    cost=cm_cand, window=self.search_window
                )
                lb_val = float("inf") if pl_lb is None else (
                    pl_lb["cost"] + cm_cand.feed_delta(
                        forced_chain, pl_lb["reach"], self.ntemplates, pl_lb.get("halfwidth")
                    )
                )
                if lb_val >= best_cost:
                    continue
                pl = _gatechain.chain_thresholds(
                    self._pending_ref, self.n, snr, self.fd, forced_chain,
                    cost=cm_cand, window=self.search_window, tier0_cluster=cand
                )
                c_val = float("inf") if pl is None else (
                    pl["cost"] + cm_cand.feed_delta(
                        forced_chain, pl["reach"], self.ntemplates, pl.get("halfwidth")
                    )
                )
            else:
                _, lb_plans = _gatechain.choose_chain(
                    self._pending_ref, self.n, snr, self.fd, ntemplates=self.ntemplates,
                    cost=cm_cand, max_tiers=tiers, window=self.search_window, first=b
                )
                if min((q["cost"] for q in lb_plans), default=float("inf")) >= best_cost:
                    continue
                a_q = math.floor(cand.alpha * 200.0 + 1e-9) / 200.0
                _, plans = _gatechain.choose_chain(
                    self._pending_ref, self.n, snr, self.fd, ntemplates=self.ntemplates,
                    cost=cm_cand, max_tiers=tiers, window=self.search_window,
                    tier0_clusters={b: (a_q, cand.lag_pad)}, first=b
                )
                c_val = min(
                    (q["cost"] for q in plans if len(q["chain"]) >= min_len and q["chain"][0] == b),
                    default=float("inf"),
                )
            if c_val < best_cost:
                best_cost = c_val
                best_cl = cand
        self._tier0_clusters[b] = best_cl
        return best_cl

    def _clusters_sig(self):
        """Hashable summary of materialized candidate Tier-0 clusters for chain choice caching."""
        if not self._tier0_clusters or not _tier0_centroid_enabled():
            return ()
        return tuple(
            (b, round(cl.ratio, 2), math.floor(cl.alpha * 200.0 + 1e-9) / 200.0, cl.lag_pad)
            for b, cl in sorted(self._tier0_clusters.items())
            if cl is not None
        )

    def _active_tier0_cluster(self, chain=None):
        """Active `Tier0Cluster` for `chain[0]`, or `None` when Tier-0 clustering is disabled."""
        ch = self._chain if chain is None else chain
        min_len = 1 if self.device.kind == "cpu" else 2
        if ch is None or len(ch) < min_len:
            return None
        return self._tier0_cluster_for_band(int(ch[0]))

    def _tier1_usable(self, chain):
        """Whether Tier-1 sub-centroids may run on `chain`: a CPU plan of at least two tiers,
        except where Tier 1 is the last tier and a direct refine may apply (the direct refine
        elects each survivor's own last-tier lag, which a shared centroid cannot give; the C
        plan runs that tier unclustered then, ap_hmf_run)."""
        if self.device.kind != "cpu" or self._gpu is not None or chain is None or len(chain) < 2:
            return False
        if len(chain) == 2 and (getattr(self, "_taps", None) is not None
                                and _direct_refine_enabled() and self._cal_thr is None):
            return False
        return True

    def _active_tier1_cluster(self, chain=None):
        """Active Tier-1 sub-centroid `Tier0Cluster` for `chain[1]` (nested inside the active
        Tier-0 clusters), or `None` when Tier-1 clustering does not apply."""
        ch = self._chain if chain is None else chain
        if not self._tier1_usable(ch):
            return None
        cl0 = self._active_tier0_cluster(ch)
        if cl0 is None or cl0.specs.shape[0] >= self.ntemplates:
            return None
        key = (int(ch[0]), int(ch[1]))
        hit = self._tier1_clusters.get(key)
        if hit is not None and hit[0] is cl0:
            return hit[1]
        tmpl = self._templates_for_clustering()
        if tmpl is None:
            return None
        cl1 = _gatechain.cluster_tier1_from_tier0(
            tmpl, self._pending_ref, self.n, cl0, key[1],
            k0=self._desired_offsets(ch)[1])
        self._tier1_clusters[key] = (cl0, cl1)
        return cl1

    def _sync_tier0_clusters(self, plan):
        """Upload or clear Tier-0 and Tier-1 pair centroids on CPU `_core.HMF` `plan`."""
        if plan is None or not hasattr(plan, "set_tier0_clusters"):
            return
        cl = self._active_tier0_cluster()
        tag = (id(plan), None if cl is None else id(cl))
        if self._synced_t0 != tag or not (
            (cl is None and plan.tier0_cluster_count() == 0)
            or (cl is not None and plan.tier0_cluster_count() == cl.specs.shape[0])
        ):
            if cl is None:
                if plan.tier0_cluster_count() > 0:
                    plan.clear_tier0_clusters()
            else:
                plan.set_tier0_clusters(cl.specs, cl.offsets, cl.members, int(cl.lag_pad))
            self._synced_t0 = tag
        # Tier-1 sub-centroids nest inside the Tier-0 clusters: the C plan drops them whenever
        # the Tier-0 clusters change, and they are uploaded after them.
        cl1 = self._active_tier1_cluster() if cl is not None else None
        tag1 = (id(plan), None if cl1 is None else id(cl1))
        if self._synced_t1 == tag1 and (
            (cl1 is None and plan.tier1_cluster_count() == 0)
            or (cl1 is not None and plan.tier1_cluster_count() == cl1.specs.shape[0])
        ):
            return
        if cl1 is None:
            if plan.tier1_cluster_count() > 0:
                plan.clear_tier1_clusters()
        else:
            plan.set_tier1_clusters(cl1.specs, cl1.offsets, cl1.members, int(cl1.lag_pad))
        self._synced_t1 = tag1

    def _trial_arms(self):
        """DEFAULT, then the screen both ways where the chain's first band has one."""
        arms = [_trial.DEFAULT]
        if self._q15_ok(tuple(self._chain)):
            arms += [_settings.arm("q15", True), _settings.arm("q15", False)]
        return arms

    def _plan_trial(self):
        """This standalone plan's open joint trial, or None: none for a plan a bank governs,
        MF_AUTOTUNE=0, or a plan with one arm. A lock (this process's or MF_COST_FILE's) is
        adopted here."""
        if self._governed or not _autotune_enabled():
            return None
        if self._chain is None:
            if self._pending_ref is None:
                return None
            self._chain = self._choose_chain()
            self._q15 = self._arm_q15(self._chain)
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
            prev_live = self._live_templates
            self._live_templates = t
            try:
                plan.set_template_batch(0, t)
                self._sync_tier0_clusters(plan)
            finally:
                self._live_templates = prev_live
        elif isinstance(t, list):
            for i, x in enumerate(t):
                if x is not None:
                    plan.set_template(i, x)

    def _desired_offsets(self, chain):
        """Per-tier starting fine bins k0: model-selected offsets when calibrating from a
        reference profile, or zeros when explicit thresholds bypass the model."""
        if self._pending_ref is not None and self._cal_thr is None:
            return tuple(int(_gatechain.band_offset(self._pending_ref, self.n, b)) for b in chain)
        return (0,) * len(chain)

    def _restore_into(self, plan, templates=None):
        """Replay reference, templates and data into a freshly built plan."""
        if hasattr(plan, "set_band_offsets"):
            plan.set_band_offsets(list(self._desired_offsets(self._chain)))
        if self._pending_ref is not None:
            plan.set_reference(self._pending_ref)
        if templates is None:
            self._load_held_templates(plan)
        else:
            plan.set_template_batch(0, templates)
            self._sync_tier0_clusters(plan)
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

    def _sync_direct_prices(self, plan, real_series):
        """Update plan's direct-refine prices for real_series (True or False)."""
        taps = getattr(self, "_taps", None)
        r = self.__dict__.get("_resolved")
        if taps is not None and r is not None and r.direct_hw is not None:
            prices = _prices._direct_pair_prices(self.n, plan, real_series=bool(real_series),
                                                 complex_taps=bool(taps[2]))
            if prices is not None:
                plan.set_direct_prices(*prices)
        self._applied_real = bool(real_series)

    def _execution_plan(self):
        """The CPU plan, with the resolved plan (_resolve) applied to it: once per plan and
        resolution (a new plan, or a changed input, applies it again)."""
        plan = self._ensure()
        r = self._resolve()
        d = self.__dict__
        want_real = bool(d.get("_want_real", False))
        if d.get("_applied_plan") is not plan or d.get("_applied_res") is not r:
            if hasattr(plan, "band_offsets") and plan.band_offsets() != r.offsets:
                plan.set_band_offsets(list(r.offsets))
                if self._pending_ref is not None:
                    plan.set_reference(self._pending_ref)
                self._reload_templates()
            plan.set_thresholds(list(r.thresholds))
            self._sync_tier0_clusters(plan)
            taps = getattr(self, "_taps", None)
            if taps is not None:
                if r.direct_hw is not None:
                    if want_real:
                        plan.set_real_series(True)
                    prices = _prices._direct_pair_prices(self.n, plan, real_series=want_real,
                                                         complex_taps=bool(taps[2]))
                    if prices is not None:
                        plan.set_direct_prices(*prices)
                plan.set_direct(r.direct_hw is not None, r.direct_hw or 1)
            self._applied_plan, self._applied_res, self._applied_real = plan, r, want_real
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
        offsets = self._desired_offsets(chain)
        f = hw = None
        if self._pending_ref is not None:
            ref = np.asarray(self._pending_ref, dtype=np.float64)
            tot = ref.sum()
            f = tuple(float(ref[slice(*_gatechain._band_slice(self.n, b, k0))].sum() / tot)
                      if tot > 0 else 0.0 for b, k0 in zip(chain, offsets))
        if (getattr(self, "_taps", None) is not None
                and _direct_refine_enabled() and self._cal_thr is None
                and (self.device.kind == 'cpu'
                     or (self._gpu is not None and self.n <= 65536
                         and self._gpu._shipped("refine_td", self.n)))):
            # the model's plan: its thresholds and half-width share the budget. Explicit
            # thresholds carry their own guarantee, which a window would add to: transform.
            hw = getattr(self, "_plan_halfwidth", None)
        r = self._resolved = _Resolved(chain, thr, getattr(self, "_refine_reach", None), f,
                                       hw, offsets)
        return r

    def _direct_price(self, cm=None):
        """Ticks (or GPU anchor ns) per lag of the direct refine's window with this plan's
        taps, which the chain choice prices every chain's window by
        (gatechain.CostModel.with_direct), or None where the direct refine does not apply:
        off (MF_DIRECT_REFINE=0), no taps, or no reference to model it on."""
        taps = getattr(self, "_taps", None)
        if (taps is None or not _direct_refine_enabled() or self._pending_ref is None
                or getattr(self, "_one_bin_frac", 1.0) <= 0.0):
            return None
        cplx = bool(taps[2])
        want_real = self.__dict__.get("_want_real")
        rs = bool(cplx) if want_real is None else bool(want_real)
        L = 32.0 * max(1, int(round(float(np.mean(taps[1])) / 32.0)))   # as the chain key rounds it
        if self.device.kind == "gpu":
            if (self._gpu is None or self.n > 65536
                    or not self._gpu._shipped("refine_td", self.n) or cm is None
                    or not cm._refine):
                return None
            ratio = _prices._gpu_direct_ratio(self.n, self._gpu, real_series=rs, complex_taps=cplx)
            if not ratio > 0:
                return None
            return ratio * min(v for _, v in cm._refine) * L
        lagtap = _prices._direct_lagtap(real_series=rs, complex_taps=cplx)
        if not lagtap > 0:
            return None
        # the correlation, plus the per-lag binning around it (~4 ticks a lag)
        return lagtap * L + 4.0


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
        self._plan_halfwidth = None  # the model's direct-refine half-width (_resolve)
        if self._cal_thr is not None:
            if len(self._cal_thr) != len(self._chain):
                raise ValueError("explicit thresholds %s do not match chain %s" % (self._cal_thr, self._chain))
            return self._cal_thr
        if self._pending_ref is not None:
            cost = self._cost_model()
            if self._pinned is not None:
                # priced as it runs: a pinned chain's first tier has no screen (_arm_q15), so a
                # one-tier chain's tier reports its lag for the direct refine's window
                cost = cost.unscreened()
            cl0 = self._active_tier0_cluster(self._chain)
            cl1 = self._active_tier1_cluster(self._chain) if cl0 is not None else None
            pl = _gatechain.chain_thresholds(self._pending_ref, self.n, self._fs_snr or self.snr, self.fd,
                                             self._chain, cost=cost, window=self.search_window,
                                             tier0_cluster=cl0, tier1_cluster=cl1)
            if pl is not None:
                th = tuple(float(x) for x in pl["thresholds"])
                for v in th:
                    if not np.isfinite(v) or v < 0 or v > float(np.finfo(np.float32).max):
                        raise ValueError("calibrated coarse threshold must be finite, nonnegative float32; got %r" % (th,))
                reach = pl.get("reach")
                if reach is not None and len(reach) > len(self._chain):
                    self._refine_reach = float(reach[len(self._chain)])
                self._plan_halfwidth = pl.get("halfwidth")
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
            self._ckey = None
            self.__dict__.pop("_call_plans", None)
        if power is None:
            self._pending_ref = None
            self._tier0_clusters = {}
            self._tier0_cand_cache = {}
            self._tier1_clusters = {}
            self._synced_t0 = None
            self._synced_t1 = None
            if self._mf is not None:
                if hasattr(self._mf, "set_band_offsets"):
                    self._mf.set_band_offsets(list(self._desired_offsets(self._chain)))
                self._mf.set_reference(None)
                self._reload_templates()
            return
        self._pending_ref = p.copy()
        self._tier0_clusters = {}
        self._tier0_cand_cache = {}
        self._tier1_clusters = {}
        self._synced_t0 = None
        self._synced_t1 = None
        if self._pinned is None and self._chain is not None and (self._chosen_csig or self._tier0_cluster_eligible()):
            self._chain = None
            self._mf = None
        if self._mf is not None:
            if hasattr(self._mf, "set_band_offsets"):
                self._mf.set_band_offsets(list(self._desired_offsets(self._chain)))
            self._mf.set_reference(p)
            self._reload_templates()

    def _reload_templates(self):
        """After a reference change: the CPU plan's loaded templates were scaled for the old
        reference and are stale (it keeps no unscaled copy); load them again."""
        if self._template_ready is None or self._template_ready:
            self._load_held_templates(self._mf)

    # ---- chain choice ----------------------------------------------------------
    def _cost_model(self, cluster_ratios=None):
        """The costs of the device this plan runs on: chains rank differently on a GPU (a refined
        pair costs ~30 coarse pairs there against ~100 on a CPU core)."""
        if self.device.kind == "gpu":
            cm = _calibration.calibrate_costs_gpu(self.n, str(self.device))
            price = self._direct_price(cm)
            cm = (cm.with_direct(price, single_tier=True,
                                 fraction=getattr(self, "_one_bin_frac", 1.0))
                  if price is not None else cm)
        else:
            policy = self._series_policy('hierarchical_series', 0, self.ntemplates) or {}
            cm = _calibration.calibrate_costs(self.n, self.ntemplates,
                                            group=policy.get('series_group', _gatechain.default_series_group(self.n)))
            price = self._direct_price()
            if price is not None:
                # The two bin fractions are a template group's own (its valid span against
                # the output bins), a different number in every group of a bank's siblings,
                # and they are prices' weights, not thresholds. To a twentieth they are the
                # same for groups of nearly one length, whose chain searches then are one
                # search: no two groups of a top template's leaf banks shared a search
                # otherwise (their cost models differed in these alone).
                step = _PRICE_FRACTION_STEP
                mfrac = round(max(0.0, 1.0 - float(getattr(self, "_unsplit_bin_frac", 1.0))) / step) * step
                frac = min(1.0, round(float(getattr(self, "_one_bin_frac", 1.0)) / step) * step)
                cm = cm.with_direct(price, single_tier=_gatechain.cpu_gate_kind() != "f16",
                                    fraction=frac, base=0.25 * cm.refine(0.1), multi_frac=mfrac)
        is_cpu = self.device.kind == "cpu"
        if cluster_ratios is None:
            csig = self._clusters_sig()
            if csig and self._cal_thr is None:
                cm = cm.with_tier0_cluster({b: r for b, r, _, _ in csig}, single_tier=is_cpu)
        elif cluster_ratios:
            cm = cm.with_tier0_cluster(cluster_ratios, single_tier=is_cpu)
        return cm

    def _direct_key(self):
        """The direct refine's rounded tap length when it is priced into this plan's chain
        choice (HierarchicalFilter._direct_price), else None: chain choices and locks are
        kept apart by it, since a cheaper refine changes which chain wins."""
        taps = getattr(self, "_taps", None)
        if taps is None or not _direct_refine_enabled():
            return None
        if self.device.kind == "gpu":
            if self._gpu is None or self.n > 65536 or not self._gpu._shipped("refine_td", self.n):
                return None
        elif self.device.kind != "cpu":
            return None
        frac = round(float(getattr(self, "_one_bin_frac", 1.0)), 2)
        if frac <= 0.0:
            return None
        rl = int(round(float(np.mean(taps[1])) / 32.0))
        if frac < 1.0:
            return (rl, bool(taps[2]), frac)
        return (rl, True) if taps[2] else rl

    def _choose_chain(self):
        """The chain this plan runs: the model's choice, which prices every chain for this
        plan's reference (cached per reference profile, _chains._CHAIN_CHOICE), or
        MF_CHAIN_FORCE's for measurement. Records the model's screen setting for every priced
        chain (_chains._Q15_MODEL), which the joint trial's screen arms start from.
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
        forced = _config.get("MF_CHAIN_FORCE")
        forced_want = None
        if forced:
            for part in forced.split(";"):
                pn, _, bands_str = part.rpartition(":")
                if not pn or int(pn) == self.n:
                    want = tuple(int(b) for b in bands_str.split(",") if b)
                    if want and len(want) <= tiers and all(b < self.n for b in want):
                        forced_want = want

        # Lazily cluster only candidate Tier-0 bands whose optimistic lower bound can win
        if self._tier0_cluster_eligible():
            is_cpu = self.device.kind == "cpu"
            min_len = 1 if is_cpu else 2
            usable = _gatechain.usable_bands(self._pending_ref, self.n)
            cand_bands = usable if (is_cpu and usable) else (usable[:-1] if len(usable) >= 2 else [])
            tmpl = self._templates_for_clustering() if cand_bands else None
            if tmpl is not None:
                if forced_want is not None:
                    if len(forced_want) >= min_len and forced_want[0] in cand_bands:
                        self._tier0_cluster_for_band(
                            forced_want[0], templates=tmpl, forced_chain=forced_want
                        )
                else:
                    max_k = int(_TIER0_MAX_ARITY)
                    opt_map = {
                        int(b): max(
                            0.15,
                            round(max(1.0 / max_k, _tier0_min_clusters(b, is_cpu) / max(self.ntemplates, 1)) * 20.0) / 20.0,
                        )
                        for b in cand_bands
                    }
                    base_cm = self._cost_model(cluster_ratios={})
                    opt_cm = base_cm.with_tier0_cluster(opt_map, single_tier=is_cpu)
                    _, lb_plans = _gatechain.choose_chain(
                        self._pending_ref, self.n, snr, self.fd, ntemplates=self.ntemplates,
                        cost=opt_cm, max_tiers=tiers, window=self.search_window
                    )
                    best_uncl, uncl_plans = _gatechain.choose_chain(
                        self._pending_ref, self.n, snr, self.fd, ntemplates=self.ntemplates,
                        cost=base_cm, max_tiers=tiers, window=self.search_window
                    )
                    best_upper = best_uncl["cost"] if best_uncl is not None else float("inf")
                    best_b0 = int(best_uncl["chain"][0]) if best_uncl is not None else self.n
                    lb_by_b0 = {
                        int(b0): min(
                            (q["cost"] for q in lb_plans if len(q["chain"]) >= min_len and q["chain"][0] == b0),
                            default=float("inf"),
                        )
                        for b0 in cand_bands
                    }
                    uncl_by_b0 = {
                        int(b0): min(
                            (q["cost"] for q in uncl_plans if len(q["chain"]) >= min_len and q["chain"][0] == b0),
                            default=float("inf"),
                        )
                        for b0 in cand_bands
                    }
                    ordered_b0 = sorted((int(b) for b in cand_bands), key=lambda b: (lb_by_b0[b], b))
                    tie_slack = 1.0 + _gatechain.TIE
                    shared = {}        # band -> the smallest screener-to-template ratio found
                    for b0 in ordered_b0:
                        limit = best_upper * (tie_slack if b0 < best_b0 else 1.0)
                        if lb_by_b0[b0] >= limit or not math.isfinite(lb_by_b0[b0]):
                            continue
                        def bound(ratio, b0=b0):
                            # the cheapest chain from b0 with tier 0 at this centroid ratio
                            # and no loss of signal (alpha 1, no lag padding): a lower bound
                            _, plans_r = _gatechain.choose_chain(
                                self._pending_ref, self.n, snr, self.fd,
                                ntemplates=self.ntemplates,
                                cost=base_cm.with_tier0_cluster({b0: ratio}, single_tier=is_cpu),
                                max_tiers=tiers,
                                window=self.search_window, first=b0)
                            return min((q["cost"] for q in plans_r), default=float("inf"))

                        def next_can_win(prev_cl, cur_cap=2, limit=limit, bound=bound, opt_b=opt_map[b0]):
                            nt = int(prev_cl.members.size)
                            nc_prev = int(prev_cl.offsets.size) - 1
                            rem_div = max(2, max_k // max(int(cur_cap), 2))
                            r_best = max(opt_b, round(math.ceil(nc_prev / rem_div) / nt * 20.0) / 20.0)
                            return bound(r_best) < limit

                        # A wider band shares no better than a narrower one: templates that
                        # agree over more of the spectrum agree over less of it too (the rule
                        # every bank of the 171,828-template BNS search obeyed: the 256 band
                        # reached 0.45-0.60 where the 128 band reached 0.30-0.40). If b0 loses
                        # even at the best ratio a narrower band found, its screeners are not
                        # built: that was half of the clustering in a leaf bank's setup, for
                        # a band that never won.
                        narrower = [r for b, r in shared.items() if b < b0]
                        if (_TIER0_PRUNE_WIDER and narrower
                                and bound(max(opt_map[b0], min(narrower))) >= limit):
                            self._tier0_clusters[b0] = None
                            continue
                        raw_cands = self._tier0_candidates_for_band(b0, templates=tmpl,
                                                                    pass2=next_can_win)
                        found = [float(c.ratio) for c in raw_cands if c is not None]
                        if found:
                            shared[b0] = min(found)
                        cands = _pareto_tier0_candidates(raw_cands)
                        best_cand = None
                        best_cand_b0_cost = uncl_by_b0[b0]
                        for cand in reversed(cands):
                            if bound(cand.ratio) >= min(limit, best_cand_b0_cost):
                                continue
                            a_q = math.floor(cand.alpha * 200.0 + 1e-9) / 200.0
                            cm_b0 = base_cm.with_tier0_cluster({b0: cand.ratio}, single_tier=is_cpu)
                            _, cur_plans = _gatechain.choose_chain(
                                self._pending_ref, self.n, snr, self.fd, ntemplates=self.ntemplates,
                                cost=cm_b0, max_tiers=tiers, window=self.search_window,
                                tier0_clusters={b0: (a_q, cand.lag_pad)}, first=b0
                            )
                            cand_b0_cost = min(
                                (q["cost"] for q in cur_plans if len(q["chain"]) >= min_len and q["chain"][0] == b0),
                                default=float("inf"),
                            )
                            if cand_b0_cost < best_cand_b0_cost:
                                best_cand_b0_cost = cand_b0_cost
                                best_cand = cand
                        self._tier0_clusters[b0] = best_cand
                        if best_cand is not None and best_cand_b0_cost < best_upper:
                            best_upper = best_cand_b0_cost
                            best_b0 = b0

        ref = np.asarray(self._pending_ref, np.float64)
        prof = _gatechain._gm._profile_sig(ref / ref.sum())
        direct = self._direct_key()
        csig = self._clusters_sig() if self._cal_thr is None else ()
        key = (self.n, float(snr), float(self.fd), tiers, self.search_window, prof, str(self.device),
               _gatechain.cpu_gate_kind() if self.device.kind == "cpu" else None, direct)
        if csig:
            key = key + (csig,)
        with _AUTOTUNE_LOCK:
            hit = _chains._CHAIN_CHOICE.get(key)
        if hit is None:
            t0_choice = {b: (a, lp) for b, _, a, lp in csig} if csig else None
            best, plans = _gatechain.choose_chain(self._pending_ref, self.n, snr, self.fd, ntemplates=self.ntemplates,
                                                  cost=self._cost_model(), max_tiers=tiers,
                                                  window=self.search_window,
                                                  tier0_clusters=t0_choice)
            if best is None:
                raise ValueError(_uncovered_message(self.n, self.snr, self.fd))
            hit = (tuple(best["chain"]), tuple(tuple(q["chain"]) for q in plans))
            with _AUTOTUNE_LOCK:
                for q in plans:
                    _chains._Q15_MODEL[(key, tuple(q["chain"]))] = bool(q.get("q15", False))
            with _AUTOTUNE_LOCK:
                _chains._CHAIN_CHOICE[key] = hit
            _log_autotune("CHAIN n=%d model=%s ranking=%s", self.n, hit[0],
                          [(q["chain"], round(q["cost"], 1)) for q in plans[:6]])
        model_best = hit[0]
        self._forced = False
        if forced_want is not None:
            model_best = forced_want
            self._forced = True
        self._choice_key = key
        self._chosen_csig = csig
        self._model_chain = chain = tuple(model_best)
        self.autotune_info = {"status": "forced" if self._forced else "model", "winner": chain,
                              "model": self._model_chain, "arm": self._arm}
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
        if tr is None or _choice.playing():
            return run()
        full = templates is None or templates[1] >= self.ntemplates
        try:
            nblk = len(starts) if starts is not None else 1
        except TypeError:
            nblk = 0
        if not (full and nblk >= 2):
            # not the work the trial decides (a follow-up, one block): run as it stands
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
        if index is not None:
            self._clusters_allowed = False
            if self._tier0_clusters or self._tier0_cand_cache or self._tier1_clusters:
                self._tier0_clusters = {}
                self._tier0_cand_cache = {}
                self._tier1_clusters = {}
                self._synced_t0 = None
                self._synced_t1 = None
                self._resolved = None
                self._ckey = None
                self.__dict__.pop("_call_plans", None)
                if self._mf is not None:
                    self._mf.clear_tier0_clusters()   # drops the nested Tier-1 clusters too
            if self._pinned is None and self._chain is not None and self._chosen_csig:
                self._chain, self._mf, self._resolved = None, None, None
                self._ckey = None
                self.__dict__.pop("_call_plans", None)
            return super().set_templates(spectra, index=index)
        if self._gpu is not None:
            super().set_templates(spectra, index=None)
            self._clusters_allowed = True
            self._tier0_clusters = {}
            self._tier0_cand_cache = {}
            self._tier1_clusters = {}
            self._synced_t0 = None
            self._synced_t1 = None
            self._ckey = None
            self.__dict__.pop("_call_plans", None)
            if self._cal_thr is None:
                self._resolved = None
            if self._pinned is None and self._chain is not None and (
                self._chosen_csig or self._tier0_cluster_eligible()
            ):
                self._chain = None
                self._mf = None
            return
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
        self.k = k
        self._held_templates = self._hold(a)
        self._clusters_allowed = True
        self._tier0_clusters = {}
        self._tier0_cand_cache = {}
        self._tier1_clusters = {}
        self._synced_t0 = None
        self._synced_t1 = None
        if self._cal_thr is None:
            self._resolved = None
        if self._pinned is None and self._chain is not None and (self._chosen_csig or self._tier0_cluster_eligible()):
            self._chain = None
            self._mf = None
        rebuild = self._mf is None or getattr(self._mf, 'k', self.n) != k
        if rebuild:
            self._mf = None
        # A new plan consumes this batch while restoring its state; regenerating it
        # from the template source here would duplicate both generation and ingestion.
        prev_live = self._live_templates
        self._live_templates = a
        try:
            plan = self._ensure(templates=a)
            if not rebuild:
                plan.set_template_batch(0, a)
                self._sync_tier0_clusters(plan)
        finally:
            self._live_templates = prev_live
        self._mark_ready("template", None)

    def set_taps(self, taps, counts=None):
        """Each template's real or complex FIR taps, for the direct refine on CPU and GPU.

        taps (ntemplates, m) float32 or complex64, row t's first counts[t] taps valid (all m
        when counts is None), the centre tap counts[t] // 2 at lag 0 -- the filter whose
        spectrum set_templates holds, at the data's sample rate (time_domain.template_spectra
        with tap and data rates equal). run_series then refines a survivor by direct correlation
        at the lags around its last tier's firing coarse lags wherever that is priced
        cheaper than a whole-block transform; MF_DIRECT_REFINE=0 turns it off."""
        arr = np.asarray(taps)
        cplx = np.iscomplexobj(arr)
        taps = np.ascontiguousarray(arr, dtype=np.complex64 if cplx else np.float32)
        if taps.ndim != 2 or taps.shape[0] != self.ntemplates:
            raise ValueError("taps must be (ntemplates, m) = (%d, m)" % self.ntemplates)
        counts = (np.full(self.ntemplates, taps.shape[1], np.int64) if counts is None
                  else np.ascontiguousarray(counts, dtype=np.int64))
        if counts.shape != (self.ntemplates,) or counts.min() < 1 or counts.max() > min(taps.shape[1], self.n):
            raise ValueError("counts must be (ntemplates,) in [1, min(m, n)]")
        self._taps = (taps, counts, cplx)
        self._gtaps_info = None
        self.__dict__.pop("_call_plans", None)
        if self._pinned is None and self._chain is not None:
            # The model priced the chain without the direct refine: choose again (the plan is
            # rebuilt on next use and replays reference, templates and data).
            self._chain, self._mf, self._resolved = None, None, None
        elif self._mf is not None:
            self._mf.set_taps(taps, taps.shape[1], counts, cplx)
            self._resolved = None               # the direct window is part of the resolved plan
        else:
            self._resolved = None

    def direct_stats(self):
        """Direct-refine counters of the plan ({} on CPU before one exists)."""
        if self._gpu is not None:
            return dict(pairs=int(self._gdirect), fft=int(self._gfft))
        return self._mf.direct_stats() if self._mf is not None else {}

    def set_hermitian(self, hermitian: bool):
        h = bool(hermitian)
        if h != self._hermitian:
            self._hermitian = h
            self._resolved = None
            if h and (self._tier0_clusters or self._tier0_cand_cache or self._tier1_clusters):
                self._tier0_clusters = {}
                self._tier0_cand_cache = {}
                self._tier1_clusters = {}
                self._synced_t0 = None
                self._synced_t1 = None
                self._ckey = None
                self.__dict__.pop("_call_plans", None)
                if self._pinned is None and self._chain is not None and self._chosen_csig:
                    self._chain, self._mf = None, None
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
    def _gpu_calibration(self, threshold):
        """(chain, per-tier reference band fractions or None, per-tier thresholds), from the
        resolved plan (_resolve)."""
        r = self._resolve()
        return r.chain, r.fractions, r.thresholds

    def _coarse_templates(self, H, bands, f, offsets=None):
        """Coarse templates per tier: active band [k0, khi) wrapped to cyclic slots and scaled
        by 1/sqrt(band fraction)."""
        offsets = (0,) * len(bands) if offsets is None else offsets
        out = []
        power = total = None
        for i, (b, k0) in enumerate(zip(bands, offsets)):
            k0, khi = _gatechain._band_slice(self.n, b, k0)
            if f is None:
                if power is None:
                    power = H.real * H.real + H.imag * H.imag
                    total = power.sum(axis=1, dtype=np.float64)
                frac = np.divide(power[:, k0:khi].sum(axis=1, dtype=np.float64), total,
                                 out=np.zeros_like(total), where=total > 0)
                sc = np.divide(1.0, np.sqrt(frac), out=np.zeros_like(frac), where=frac > 0)[:, None].astype(np.float32)
            else:
                sc = np.float32(1.0 / np.sqrt(f[i])) if f[i] > 0 else np.float32(0.0)
            if k0 == 0:
                out.append(H[:, :b] * sc)
            else:
                ct = np.zeros((H.shape[0], b), dtype=np.complex64)
                length = max(khi - k0, 0)
                u0 = k0 & (b - 1)
                first = min(length, b - u0)
                if first > 0:
                    ct[:, u0:u0 + first] = H[:, k0:k0 + first] * sc
                if length > first:
                    ct[:, :length - first] = H[:, k0 + first:khi] * sc
                out.append(ct)
        return out

    def _gate_args(self, H, threshold):
        """What a dispatch of templates H passes the backend's gate chain: (chain, coarse
        templates per tier, per-tier thresholds, and the keywords of a second tier and active
        band offsets). The coarse templates are cut again only when H, the chain, its offsets
        or its band fractions change, or the templates were set again."""
        r = self._resolve()
        chain, f, thr, offsets = r.chain, r.fractions, r.thresholds, r.offsets
        if len(chain) > 2:
            # The kernels take a first (cascade) band and a last band; every chain a GPU plan
            # is given is bounded by _MAX_TIERS["gpu"].
            raise RuntimeError("a GPU chain has at most two tiers; got %s" % (chain,))
        cl = (
            self._active_tier0_cluster(chain)
            if (len(chain) == 2 and H.shape[0] == self.ntemplates
                and (self._gtmpl is None or H.ctypes.data == self._gtmpl.ctypes.data))
            else None
        )
        ck = (chain, offsets, f, H.ctypes.data, H.shape, None if cl is None else id(cl))
        if getattr(self, "_ckey", None) != ck or self._tdirty:
            if cl is not None:
                ct1 = self._coarse_templates(
                    H, chain[1:], None if f is None else f[1:], offsets[1:]
                )[0]
                self._ct = [cl.specs, ct1]
            else:
                self._ct = self._coarse_templates(H, chain, f, offsets)
            self._ckey = ck
            self._tdirty = True
        ct = self._ct
        extra = {} if len(chain) == 1 else dict(cascade_band=chain[0], ct1=ct[1], raw_thr1=thr[1])
        if cl is not None:
            extra["tier0_cluster"] = cl
        if any(offsets):
            extra["band_offsets"] = offsets
        return chain, ct, thr, extra

    def _gpu_direct_arg(self, H):
        """The GPU direct-refine descriptor (taps_view, tap_meta, tmpl_offset, direct_hw,
        max_lag_tap) for template slice H, or None when direct refine is inactive."""
        r = self._resolve()
        if r.direct_hw is None:
            return None
        taps = getattr(self, "_taps", None)
        if (taps is None or not _direct_refine_enabled() or self._gpu is None
                or self.n > 65536 or not self._gpu._shipped("refine_td", self.n)):
            return None
        gtmpl = self._gtmpl
        if gtmpl is None or gtmpl.strides[0] <= 0:
            return None
        byte_off = H.ctypes.data - gtmpl.ctypes.data
        row_bytes = gtmpl.strides[0]
        if (byte_off < 0 or byte_off % row_bytes != 0
                or byte_off // row_bytes + H.shape[0] > self.ntemplates):
            return None
        tmpl_offset = int(byte_off // row_bytes)
        # Pack and upload the conjugated/zero-masked tap table lazily on first active dispatch.
        info = self.__dict__.get("_gtaps_info")
        if info is None or info[0] is not self._gpu:
            arr_taps, counts, cplx = taps
            tap_stride = (int(counts.max()) + 3) & ~3
            row_words = 4 + (2 * tap_stride if cplx else tap_stride)
            packed = np.zeros((self.ntemplates, row_words), dtype=np.uint32)
            packed[:, 0] = counts.astype(np.uint32)
            m = min(arr_taps.shape[1], tap_stride)
            mask = np.arange(m)[None, :] < counts[:, None]
            if cplx:
                masked = np.ascontiguousarray(
                    np.where(mask, np.conj(arr_taps[:, :m]), np.complex64(0)),
                    dtype=np.complex64)
                packed[:, 4:4 + 2 * m] = masked.view(np.uint32)
            else:
                masked = np.ascontiguousarray(
                    np.where(mask, arr_taps[:, :m], np.float32(0)),
                    dtype=np.float32)
                packed[:, 4:4 + m] = masked.view(np.uint32)
            buf = self._gpu.empty_shared((self.ntemplates, row_words), dtype=np.uint32)
            buf[:] = packed
            from ._shared import shared_view
            view = shared_view(buf, self._gpu)
            if self._gpu.stage_host_inputs and view is not None:
                self._gpu._x_prefetch(view, 0, buf.nbytes, None)
            tap_meta = (tap_stride << 1) | int(bool(cplx))
            info = self._gtaps_info = (self._gpu, buf, view, tap_meta, {})
        if info[2] is None:
            return None
        rs = bool(self.__dict__.get("_want_real", False))
        max_lag_tap = info[4].get(rs)
        if max_lag_tap is None:
            ratio = _prices._gpu_direct_ratio(self.n, self._gpu, real_series=rs,
                                              complex_taps=bool(taps[2]))
            if not ratio > 0:
                return None
            cm = _calibration.calibrate_costs_gpu(self.n, str(self.device))
            ref_vals = [v for _, v in cm._refine] if cm._refine else [1.0]
            scale = max(ref_vals) / max(min(ref_vals), 1e-12)
            max_lag_tap = max(1, min(0xFFFFFFFF, int(round(scale / ratio))))
            info[4][rs] = max_lag_tap
        return (info[2], info[3], tmpl_offset, int(r.direct_hw), max_lag_tap)

    def _grouped_dispatch(self, n, spec, H, groups, binsize, threshold, **kw):
        """The gate chain over every window group of one spectra batch, one submission."""
        chain, ct, thr, extra = self._gate_args(H, threshold)
        res = self._gpu.hier_peaks_grouped(n, chain[-1], spec, H, ct[0], thr[0], groups, binsize,
                                           threshold, upload_tmpl=self._tdirty,
                                           refine_reach=getattr(self, "_refine_reach", None),
                                           direct=self._gpu_direct_arg(H),
                                           **extra, **kw)
        if kw.get("async_submit"):
            return lambda: self._account(res())
        return self._account(res)

    def _gpu_dispatch(self, D, H, binsize, threshold, start, end, slot=None, async_submit=False,
                      **kw):
        """Run the gate chain and refinement without host survivor readback."""
        chain, ct, thr, extra = self._gate_args(H, threshold)
        res = self._gpu.hier_peaks(
            self.n, chain[-1], D, H, ct[0], thr[0],
            binsize=binsize, threshold=threshold, window=(start, end),
            upload_data=self._ddirty, upload_tmpl=self._tdirty,
            slot=slot, async_submit=async_submit,
            refine_reach=getattr(self, "_refine_reach", None),
            direct=self._gpu_direct_arg(H), **extra, **kw)
        self._ddirty = self._tdirty = False
        if async_submit:
            return lambda: self._account(res())
        return self._account(res)

    def _account(self, r):
        pairs_before = self._gpairs
        r = super()._account(r)
        batch_pairs = self._gpairs - pairs_before
        t0_checked = getattr(self._gpu, "last_tier0_checked", 0) or batch_pairs
        self._gt0_checked += int(t0_checked)
        return r

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
    def band_offsets(self):
        """Per-tier starting fine bin `k0` of the active coarse bands."""
        return tuple(self._resolve().offsets)

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
            checked = (
                [self._gt0_checked, self._gt1]
                if len(chain) == 2
                else ([self._gt0_checked] if len(chain) == 1 else [])
            )
            return dict(backend="gpu", chain=chain, pairs=self._gpairs, passed=passed,
                        checked=checked, refined=self._gtrig, q15=None, ticks=None,
                        ident=id(self))
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
