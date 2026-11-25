"""The cost model a gate chain is priced with, and where it is kept.

A CostModel holds this machine's measured tier costs at one transform size, as functions of
survivor density: the dense first tier, the pooled later tiers and the refine. The chain
choice (gatechain.choose_chain) prices every chain on it. `_calibration.calibrate_costs`
measures one through the engine and keeps it in MF_COST_FILE when that is set; this module
holds the model, the models of the process (_COSTS) and the checks a stored model must pass.

gatechain binds every name here under its own, which is where callers and tests reach them.
"""
import copy
import math
import os
from contextlib import contextmanager

from . import _config
from ._choice import TIE
from ._costfile import _cost_warn, _load_cost_file
from . import _core
from ._kernel_id import gpu_kernel_id as identity
from .device import parse as _parse


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
    if forced is None:
        forced = _config.get("MF_BAND_FORWARD")
    return _band_forward_given(n, band, f, forced)


def _band_forward_given(n, band, f, forced):
    """band_forward_wanted's rule with MF_BAND_FORWARD's value already read (`forced`: False,
    True or None, the bytes rule)."""
    if forced is False or n > 65536 or band >= n:
        return False
    if forced:
        return True
    return f is None or f < (n - band) / (2.0 * n)


#: feed_delta's default: read MF_BAND_FORWARD at the call.
READ_ENV = object()


def feed_rule(cost, chain, ntemplates, forced):
    """How CostModel.feed_delta prices chain's feed, as numbers _core.plan_best takes:
    (mode, band, full, threshold), each feed per pair. mode 0: always the full forward's;
    1: always the band forward's; 2: the band forward's where the refine fraction (0 for a
    pair the direct refine claims) is below threshold, else the full's. forced is
    MF_BAND_FORWARD's value (band_forward_wanted)."""
    top = int(max(chain))
    nt = float(ntemplates)
    full = cost.feed["full"] / nt
    band = cost.feed["band"].get(top)
    if forced is False or cost.n > 65536 or top >= cost.n or band is None:
        return (0, full, full, 0.0)
    if forced:
        return (1, band / nt, full, 0.0)
    return (2, band / nt, full, (cost.n - top) / (2.0 * cost.n))


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
        # A feed costs at least the head's own band forward, which moves the fewest bytes: a
        # change below zero is a measurement's scatter (-1.6 per block at band 512 in one
        # pycbc job's calibration on the 8060S), priced as none, here and in a stored model.
        self.feed = None if not feed else {
            "band": {int(b): max(0.0, float(v)) for b, v in feed["band"].items()},
            "full": max(0.0, float(feed["full"]))}
        self.screen = {}
        for b, v in (screen or {}).items():
            ent = {"dense": float(v["dense"]), "recheck": float(v["recheck"]),
                   "excess": sorted((float(a), float(c)) for a, c in v["excess"])}
            if v.get("sparse"):
                ent["sparse"] = sorted((float(f), float(c)) for f, c in v["sparse"])
            self.screen[int(b)] = ent
        self.block = float(block)          # fixed work per block: forward transform, ingest
        self.dense = {int(b): float(v) for b, v in dense.items()}
        self._sparse = {int(b): sorted((float(f), float(v)) for f, v in rows) for b, rows in sparse.items()}
        self._refine = sorted((float(f), float(v)) for f, v in refine)
        # shared screeners' ratios by first band (with_tier0_cluster), and whether a one-tier
        # chain may use them
        self.tier0_ratios = {}
        self.tier0_single = True
        # the direct refine (with_direct): None prices none
        self.direct_lag = None
        self.direct_single = True
        self.direct_frac = 1.0
        self.direct_base = 0.0
        self.direct_multi_frac = 0.0
        self._sig = None

    @staticmethod
    def _interp(rows, f):
        """Cost per survivor at density f: linear in log f, clamped to the measured range."""
        fs, vs = _log_table(rows, "cost")
        return _interp_clamped(math.log(max(f, 1e-12)), fs, vs)

    def refine(self, f):
        return self._interp(self._refine, f)

    def sparse(self, b, f):
        return self._interp(self._sparse[int(b)], f)

    def sparse_for(self, b, f, screened=False):
        """Ticks per survivor at later-tier band `b` and reach `f`, using Q15 sparse pricing
        when `screened` is True and `b` has a measured Q15 sparse curve."""
        b = int(b)
        if screened:
            sc = self.screen.get(b)
            if sc is not None and sc.get("sparse"):
                return self._interp(sc["sparse"], f)
        return self._interp(self._sparse[b], f)

    def signature(self):
        """A hashable summary of the model's content, for cache keys (an object's id can be
        reused once it is collected, which would hand a new model an old model's results)."""
        sig = self._sig
        if sig is None:
            t0r = self.tier0_ratios
            sig = (self.n, self.block, tuple(sorted(self.dense.items())),
                   tuple((b, tuple(r)) for b, r in sorted(self._sparse.items())),
                   tuple(self._refine),
                   tuple((b, v["dense"], v["recheck"], tuple(v["excess"]))
                         + ((tuple(v["sparse"]),) if "sparse" in v else ())
                         for b, v in sorted(self.screen.items())),
                   self.direct_lag, self.direct_single,
                   self.direct_frac,
                   self.direct_base,
                   self.direct_multi_frac,
                   None if self.feed is None else (tuple(sorted(self.feed["band"].items())),
                                                   self.feed["full"]))
            if t0r:
                sig = sig + (tuple(sorted(t0r.items())), bool(self.tier0_single))
            self._sig = sig
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

    def first_tier_for(self, chain, reach1):
        """(cost per pair, q15) of `chain`'s first tier, scaling dense Tier-0 work by screener ratio
        when `chain[0]` has an active Tier-0 cluster ratio."""
        b = int(chain[0])
        t0r = self.tier0_ratios
        if not t0r or b not in t0r or (len(chain) <= 1 and not self.tier0_single):
            return self.first_tier(b, reach1)
        ratio = t0r[b]
        c = self.dense[b] * ratio
        sc = self.screen.get(b)
        if sc is None or not sc["excess"]:
            return c, False
        passed = self.screen_reach(b, reach1)
        cq = sc["dense"] * ratio + passed * sc["recheck"]
        return (cq, True) if cq <= c * (1.0 + TIE) else (c, False)

    def with_tier0_cluster(self, ratios, single_tier=True):
        """Return a shallow copy pricing chains' first tier with screener ratios.

        Parameters
        ----------
        ratios : dict of {int: float} or None
            Mapping from candidate Tier-0 band `b` to `n_clusters / n_templates` (`< 1.0`).
        single_tier : bool, optional
            Whether single-tier chains `(b,)` may use Tier-0 screeners (`True` on CPU,
            `False` on GPU).

        Returns
        -------
        CostModel
            Copy of this cost model with `tier0_ratios` set (or `self` when unchanged).
        """
        clean = {int(b): round(float(r), 4)
                 for b, r in (ratios or {}).items() if 0.0 < float(r) < 1.0}
        if not clean and not self.tier0_ratios:
            return self
        cm = copy.copy(self)
        cm.tier0_ratios = clean
        cm.tier0_single = bool(single_tier)
        cm._sig = None
        return cm

    def feed_delta(self, chain, reach, ntemplates, hw=None, forced=READ_ENV):
        """Per-pair change from `block` of the forward this chain's calls take: the band
        forward at its widest band, or the full forward, as the backend decides from the
        chain's modelled refine probability reach[len(chain)] (band_forward_wanted,
        the call's own rule; 0 when direct refine claims the band forward), each measured
        per block and spread over the templates. 0 where the backend has one feed. forced:
        MF_BAND_FORWARD's value when the caller has read it (a chain choice reads it once)."""
        if self.feed is None or not ntemplates:
            return 0.0
        top = int(max(chain))
        r = (0.0 if (hw is not None and self.prices_direct(chain))
             else min(max(float(reach[len(chain)]), 0.0), 1.0))
        if forced is READ_ENV:
            forced = _config.get("MF_BAND_FORWARD")
        if _band_forward_given(self.n, top, r, forced) and top in self.feed["band"]:
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
        cm = copy.copy(self)
        cm.screen = {}
        cm._sig = None
        return cm

    def prices_direct(self, chain):
        """Whether this model prices a direct refine for chain (with_direct)."""
        return (self.direct_lag is not None
                and self.direct_frac > 0.0
                and (len(chain) > 1 or self.direct_single))

    def refine_for(self, chain, f, hw=None):
        """Ticks per refined pair for this chain at refine density f, with the direct refine's
        window half-width hw (None: the whole-block refine)."""
        r = self.refine(f)
        if hw is not None and self.prices_direct(chain):
            d = self.direct_base + self.direct_lag * (2 * int(hw) * (self.n // int(chain[-1])) + 1)
            mfrac = self.direct_multi_frac
            if mfrac > 0.0:
                b_last = int(chain[-1])
                if b_last in self._sparse:
                    d += mfrac * self.sparse(b_last, f)
            d = min(r, d)
            frac = self.direct_frac
            r = (1.0 - frac) * r + frac * d
        return r

    def chain_cost(self, chain, reach, hw=None):
        """reach[i] = P(a pair reaches tier i+1) for i = 0..k-1, reach[k] = P(reaches refine);
        hw the direct refine's half-width (refine_for)."""
        c, screened = self.first_tier_for(chain, reach[1] if len(reach) > 1 else 1.0)
        for i in range(1, len(chain)):
            c += reach[i] * self.sparse_for(chain[i], reach[i], screened)
        f = reach[len(chain)]
        if len(chain) == 1:
            b0 = int(chain[0])
            t0r = self.tier0_ratios
            if t0r and b0 in t0r and self.tier0_single:
                if hw is not None and self.prices_direct(chain):
                    f_surv = (self.screen_reach(b0, f) or f) if screened else f
                    c_elect = self.sparse(b0, f_surv) if b0 in self._sparse else self.dense[b0]
                    c += f_surv * (c_elect + self.refine_for(chain, f_surv, hw))
                else:
                    c += f * self.refine(f)
                return c
            c += f * (self.refine(f) if screened else self.refine_for(chain, f, hw))
            return c
        c += f * self.refine_for(chain, f, hw)
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
    return "f16" if getattr(_core, "gate16", lambda: False)() else "f32"


def _cost_sig(cost):
    return None if cost is None else cost.signature()
#: Survivor densities the calibration places the tiers at (bracketing production's 0.1-10%).
_CAL_DENSITIES = (0.1, 0.01)


def gpu_kernel_id(backend="vulkan"):
    """Identity of the shipped kernels whose measured choices this backend stores."""
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
    b = int(b)
    if b not in _Q15_BAND:
        try:
            _Q15_BAND[b] = _core.MF(b, 1, 1).q15_lanes() > 0
        except (ValueError, AttributeError):
            _Q15_BAND[b] = False
    return _Q15_BAND[b]


def default_series_group(n):
    """Blocks a CPU plan filters together, as HierarchicalFilter uses without an execution policy."""
    n_i = max(1, int(n))
    grp = 64
    while grp > 1 and grp * 8 * n_i > 512 * 1024:
        grp >>= 1
    if grp > 32:
        l2 = int(_core.l2_bytes())
        while grp > 32 and grp * 8 * n_i > (l2 >> 1):
            grp >>= 1
    return grp


def _run_ms(log):
    """Device milliseconds of the runs in a timing log (Executor.timings), without the
    MF_GPU_PROFILE entries ("k:...") that lie inside them."""
    return sum(ms for label, ms in log if not label.startswith("k:"))


def _is_gpu(device):
    """Whether `device` names a GPU (the cost model's band forward and fp16 gate)."""
    try:
        return _parse(device).kind == "gpu"
    except Exception:
        return False
