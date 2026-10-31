"""Measuring this machine's tier costs through the engine itself: the CPU and GPU cost-model
calibrations, the per-device block costs and the block-size pricing that uses them. They run
hierarchical plans, so they sit above the model (gatechain), which they feed."""
import time

import numpy as np

from . import _choice
from . import gatechain as _gc


#: calibrate_costs' calls (blocks a call, `reps` for its rounds, the seed of its series and
#: templates) when the caller names none. A model measured with any other is kept apart, in
#: the process and in MF_COST_FILE: under one key, whichever call ran first set the model
#: every later one used.
_CAL_BLOCKS, _CAL_REPS, _CAL_SEED = 32, 5, 11


def _pass_threshold(rate, density, lags, start=None):
    """A first-tier threshold passing about `density` of pairs, rate(t) the pass fraction at
    threshold t (counts only: nothing is timed): secant steps on the log pass rate (a noise
    tail is near linear in it), bisection where a step leaves its bracket, from where a
    block's maximum over its `lags` coarse lags passes t with probability ~ lags e^(-t^2/2)
    (or `start`). A density is a target to within 25%: each cost's own density is read from
    its call's counts. Every calibration places its thresholds with it."""
    lo, hi = 0.0, 16.0
    if start is None:
        start = np.sqrt(2.0 * np.log(max(max(int(lags), 1) / density, 1.5)))
    t = float(start)
    prev = None
    for _ in range(12):
        frac = rate(t)
        if abs(frac - density) < 0.25 * density:
            return t
        if frac > density:
            lo = max(lo, t)
        else:
            hi = min(hi, t)
        nxt = None
        if prev is not None and frac > 0 and prev[1] > 0 and frac != prev[1]:
            slope = (np.log(frac) - np.log(prev[1])) / (t - prev[0])
            if slope < 0:
                nxt = t + (np.log(density) - np.log(frac)) / slope
        prev = (t, frac)
        if nxt is None or not (lo < nxt < hi):
            nxt = t + 0.5 if frac > density and hi >= 16.0 else 0.5 * (lo + hi)
        t = float(nxt)
    return t


def calibrate_costs(n, ntemplates, blocks=_CAL_BLOCKS, reps=_CAL_REPS, seed=_CAL_SEED, group=None):
    """Measure this machine's tier costs at transform size n through the engine itself.

    Synthetic analytic noise and whitened random templates; thresholds are
    placed so that the tier under test sees each target survivor density, and
    costs are read from the engine's per-tier counters (ap_hmf_tier_stats), so
    no wall-clock subtraction is involved. Calls are 32 blocks of 64 templates: a full series
    group at n <= 2048, as production calls run, while fewer templates move the screen and
    later tiers (the first tier batches over templates). The size decides the block-size
    choice's noise more than the cost's: under load (dev2, 2026-10-24) the modelled 4096/2048
    cost ratio scattered with sd 0.06 at 16 blocks, 0.02-0.03 at 32 and 64, 0.014 at 128,
    for 0.06, 0.09-0.10, 0.18 and 0.35 s of calibration for both sizes.
    The band costs are shared by every n on the same series group, so a second n measures
    only its refine and per-block work. About 0.05 s per n on dev2; once per process. Runs at _CAL_TEMPLATES
    templates whatever `ntemplates` is (kept for callers; see _CAL_TEMPLATES).
    """
    from . import _core
    nt = _gc._CAL_TEMPLATES
    # The series group must be the plans' own: the first tier batches its work over the blocks in a
    # group, so calibrating at a smaller group overstates its cost (2x at n=1024 with 8 vs 32).
    group = int(group or _gc.default_series_group(n))
    # Keyed by the group the plans actually run (MF_DGROUP, the 4 MB cap at long n), not the
    # one asked for: a model measured at a forced group stored under the default's key was
    # adopted by every later process at the default group.
    group = _core.series_group(int(n), group)
    # The FP16 first gate (ARM, gate16.cc) changes what tier 0 costs: priced and cached
    # apart from the FP32 gate, so neither is ranked with the other's numbers.
    g16 = _gc.cpu_gate_kind() == "f16"
    how = (int(blocks), int(reps), int(seed))
    key = (int(n), nt, group) + how + (("g16",) if g16 else ())
    if key in _gc._COSTS:
        return _gc._COSTS[key]
    path = _gc._cost_file()
    # A model made without the Q15 screen's prices (an older build, or a back end without
    # it) must not be reused by one that has it, or the screen is never priced. The default
    # calls' key is the one their models have always been stored under.
    skey = ("%d,%d,%d" % key[:3] + (",g16" if g16 else "") + (",q15" if not g16 and _gc._q15_band(64) else "")
            + ("" if how == (_CAL_BLOCKS, _CAL_REPS, _CAL_SEED) else ",b%d,r%d,s%d" % how))
    if path is not None:
        cm = _gc._stored_cost_model(path, skey)
        if cm is not None:
            _gc._COSTS[key] = cm
            return cm
    rng = np.random.default_rng(seed)
    bands = _gc.candidate_bands(n)
    taps = n // 4
    h = np.zeros((nt, n), np.complex64)
    h[:, :taps] = rng.standard_normal((nt, taps)) / np.sqrt(taps)
    spec = np.fft.fft(h, axis=1).astype(np.complex64)
    step = n - taps
    S = (blocks + 1) * step + n
    x = (rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2)
    X = np.fft.fft(x); X[S // 2:] = 0
    ser = (np.fft.ifft(X) * np.sqrt(2)).astype(np.complex64).view(np.float32)
    starts = (np.arange(blocks) * step).astype(np.uint64)
    ws = np.full(blocks, taps, np.uint64); we = np.full(blocks, n, np.uint64)
    ref = np.zeros(n, np.float32); ref[:n // 2] = 1.0
    idx = np.zeros((blocks, nt, 1), np.int64); val = np.zeros((blocks, nt, 1), np.complex64)
    mag = np.zeros((blocks, nt, 1), np.float32); cnt = np.zeros((blocks, nt), np.int32)
    big = float(np.finfo(np.float32).max)

    pairs = blocks * nt

    # One plan per chain shape, its thresholds and screen set per use: a plan's construction
    # loads the 64 templates, and building one per measurement and per bisection step was a
    # fifth of the calibration.
    plans = {}

    def plan(chain, thr, q15=False):
        p = plans.get(tuple(chain))
        if p is None:
            with _gc._internal_plans():
                p = plans[tuple(chain)] = _core.HMF(n, 1, nt, list(chain), group, n)
            p.set_reference(ref); p.set_template_batch(0, spec)
        p.set_thresholds(list(thr))
        p.set_q15(bool(q15))
        return p

    def count(chain, thr, q15=False):
        """(pairs the first tier passes, pairs the screen passes) per pair, untimed. A one-tier
        chain is counted behind a second tier nothing passes, so its passes are not refined."""
        if len(chain) == 1 and chain[0] != bands[-1]:
            chain, thr = (chain[0], bands[-1]), (thr[0], big)
        p = plan(chain, thr, q15)
        t0, q0 = p.tier_stats()[0][1], p.q15_stats()[1]
        p.run_series(ser, starts, ws, we, 0, nt, n, big, idx, val, mag, cnt)
        return (p.tier_stats()[0][1] - t0) / pairs, (p.q15_stats()[1] - q0) / pairs

    def settle(chain):
        """An untimed call on the plan, so its timed calls see the caches a run of calls leaves
        (timed straight after another plan's, the refine and later tiers read 25-30% dearer);
        jobs on one plan differ only in thresholds and the screen, so one settles them all."""
        p = plans[tuple(chain)]
        p.run_series(ser, starts, ws, we, 0, nt, n, big, idx, val, mag, cnt)

    def sample(job):
        """One timed call: per tier (and the refine, last) (passed, ticks), the screen's
        (passed, ticks), and the call's ticks outside its tiers and refine."""
        p = plan(*job)
        t0, q0, s0 = p.tier_stats(), p.q15_stats(), p.series_ticks()
        p.run_series(ser, starts, ws, we, 0, nt, n, big, idx, val, mag, cnt)
        t1, q1, s1 = p.tier_stats(), p.q15_stats(), p.series_ticks()
        tiers = [(c[1] - q[1], c[2] - q[2]) for c, q in zip(t1, t0)]
        return tiers, (q1[1] - q0[1], q1[2] - q0[2]), s1 - s0 - sum(t[1] for t in tiers)

    def thr_for(b, density, start=None):
        """Tier-0 threshold at band b passing about `density` of pairs (_pass_threshold)."""
        return _pass_threshold(lambda t: count((b,), (t,))[0], density,
                               b * (n - taps) // n, start)

    # Every timed quantity is a job (a plan and its settings). The jobs run round-robin, `reps`
    # rounds, each round starting at another job, and each quantity is the minimum over its
    # rounds. Interference (another process on the core or its SMT sibling, a busy memory
    # system) only ever adds time, and a round-robin gives every job the same mix of load
    # states, so the minima keep the costs' ratios -- which are all the chain choice and the
    # tiers' threshold split read -- under load that changes during the calibration. Timed in
    # sequence with medians, one band's samples could fall in a busy spell and another's not:
    # costs moved up to 4x between processes under dynamic load (dev2, 2026-10-24).
    b0 = bands[0]
    dens = _gc._CAL_DENSITIES
    g0, t = {}, None
    for f in dens:
        g0[f] = t = thr_for(b0, f, t)
    qbands = [] if g16 else [b for b in bands if _gc._q15_band(b)]
    # The band costs (first tier, screen, later tiers) do not depend on n, only on the series
    # group the first tier batches over: measured once per group and shared by every n that
    # uses it. The refine and the per-block work are n's own.
    # Kept with the models (gatechain._COSTS), so whatever forgets those forgets these.
    bkey = ("bands", nt, group, bool(g16), tuple(qbands) != ()) + how
    shared = _gc._COSTS.get(bkey)
    need = [b for b in bands if shared is None or b not in shared["dense"]]
    jobs = {("dense", b): ((b,), (big,), False) for b in need}
    jobs[("dense", b0)] = ((b0,), (big,), False)       # its call also gives the per-block work
    for f in dens:
        jobs[("refine", f)] = ((b0,), (g0[f],), False)
        for b in bands[1:]:
            if b in need:
                jobs[("sparse", b, f)] = ((b0, b), (g0[f], big), False)
    for b in qbands:
        if b in need:
            jobs[("screen", b)] = ((b,), (big,), True)
    qneed = [b for b in qbands if b in need]
    if qneed:
        # what a pass costs beyond the screen (compaction), per pass and the same at every band:
        # under a tick (against ~100 a pair for the screen itself), timed once, at the first
        # band measured here and the first density. Not the first screen band: band costs
        # shared from a smaller n on this series group leave only the wider bands to measure
        # (n = 1024 then 2048: band 1024 alone), and their screens need it too.
        jobs[("recheck",)] = ((qneed[0],), (g0[dens[0]],), True)
    # rounds of the plans in turn (each round starting at another), every plan settled and then
    # its jobs timed. Settled per plan and screen setting: a screen call timed straight after
    # the same plan without the screen read up to 20% dearer at 16 blocks a call.
    byplan = {}
    for nm, job in jobs.items():
        byplan.setdefault((tuple(job[0]), job[2]), []).append(nm)
    order = list(byplan)
    got = {nm: [] for nm in jobs}
    rounds = max(3, (reps + 1) // 2)
    for r in range(rounds):
        k = r % len(order)
        for ch in order[k:] + order[:k]:
            plan(*jobs[byplan[ch][0]])
            settle(ch[0])
            for nm in byplan[ch]:
                got[nm].append(sample(jobs[nm]))
    def least(nm, value):
        return min(value(x) for x in got[nm])

    dense = dict(shared["dense"]) if shared else {}
    dense.update({b: least(("dense", b), lambda x: x[0][0][1]) / pairs for b in need})
    dense = {b: dense[b] for b in bands}
    # Per-block fixed work: a whole run_series call minus its tiers and refine (nothing passes).
    block = [least(("dense", b0), lambda x: x[2]) / blocks]
    sparse = {b: list(v) for b, v in (shared["sparse"].items() if shared else ()) if b in bands}
    refine = []
    for f in dens:
        tt = got[("refine", f)][0][0]
        if tt[-1][0]:
            refine.append((tt[0][0] / pairs, least(("refine", f), lambda x: x[0][-1][1]) / tt[-1][0]))
        for b in bands[1:]:
            if b not in need:
                continue
            tt = got[("sparse", b, f)][0][0]
            if tt[0][0]:
                sparse.setdefault(b, []).append((tt[0][0] / pairs, least(("sparse", b, f), lambda x: x[0][1][1]) / tt[0][0]))
    # the first band can only be a first tier; give it the next band's sparse curve for completeness
    if bands[1:]:
        sparse[b0] = list(sparse.get(bands[1], []))
    screen = {b: dict(v) for b, v in (shared["screen"].items() if shared else ()) if b in bands}
    for b in qbands:
        if b not in need:
            continue
        # screen alone: at an unreachable threshold nothing passes, so the tier's ticks are the
        # screen's; how many pairs it passes at each density (counted: the screen is the tier's
        # gate, so they are the tier's passes); what each costs beyond the screen
        # the screen is the tier's gate: it passes the pairs the tier passes (excess 1)
        tt, q, _ = got[("recheck",)][0]
        if not q[0]:
            continue
        ent = {"dense": least(("screen", b), lambda x: x[0][0][1]) / pairs,
               "excess": [(tt[0][0] / pairs, q[0] / pairs)],
               "recheck": max(least(("recheck",), lambda x: x[0][0][1] - x[1][1]) / q[0], 0.0)}
        screen[b] = ent
    _gc._COSTS[bkey] = {"dense": dict(dense), "sparse": {b: list(v) for b, v in sparse.items()},
                         "screen": {b: dict(v) for b, v in screen.items()}}
    plans.clear()
    cm = _gc.CostModel(n, dense, sparse, refine, block=float(np.median(block)), screen=screen)
    if path is not None:          # another process's model, stored first, is the one used
        cm = _gc.CostModel.from_dict(_gc._store_first(path, skey, cm.to_dict(), _gc._cost_model_ok))
    _gc._COSTS[key] = cm
    return cm


def _warm(run, seconds=0.25):
    """The results of run() called repeatedly until `seconds` after its first call returned,
    without that first call's: the device is warmed past the low clock it idles at, which
    reads slow for its first calls. The time starts after the first call because that call
    records the plan's commands, 0.06 s on an idle 8060S and 0.4-0.5 s when eight other
    processes share its four cores (dev2, 2026-10-28): timed from before it, the warm-up had
    run out before it began in each of 178 processes with 6-12 others on their cores."""
    run()
    until = time.perf_counter() + seconds
    out = [run()]
    while time.perf_counter() < until:
        out.append(run())
    return out


#: Per device: the fixed reference call and its fastest warmed device time (see _ClockRef).
class _ClockRef:
    """A fixed reference call, timed once in every round of a calibration's measurements.

    A GPU's clock moves with load and power state (an idle M2 reads slow for its first
    calls; an APU's GPU drops to a fifth of its clock under CPU load), so a device time is
    the work divided by a clock that is not constant across a calibration, let alone
    across n. A calibration times this reference once in every round of its measurements
    and scales its times by the ratio of the reference's fastest time on the warmed device
    in this process (the anchor, _warm) to its fastest during the calibration: chains and
    block sizes are ranked by those ratios, which the clock cancels out of. One small, fixed
    workload for every n, so models at different n stay comparable. (It was the ratio to a
    reference timed just before each measurement; under CPU load the 8060S's clock changes
    between one call and the next, and that pairing scaled a call by a quarter as often as
    not.) Backend-neutral: it only needs device timers (ctx.timings()).

    A backend that can read its clock (``ctx.clock_mhz()``, CUDA through NVML) is scaled by
    the clock itself instead: the reference call is small, and its own launch latency after
    a host pause (1.4-2x on the L40S at a fixed 2520 MHz) made it a noisier ruler than the
    clock it stands for. The reference stays the fallback wherever the clock is unknown.
    """

    def __init__(self, device):
        from . import HierarchicalFilter
        n, nt, blocks = 2048, 64, 128
        rng = np.random.default_rng(5)
        h = np.zeros((nt, n), np.complex64)
        h[:, :n // 4] = rng.standard_normal((nt, n // 4)) / np.sqrt(n // 4)
        self.plan = HierarchicalFilter(n, 1, nt, chain=(64,), device=device)
        self.plan.set_templates(np.fft.fft(h, axis=1).astype(np.complex64))
        self.plan.set_coarse_threshold((float(np.finfo(np.float32).max),))
        step = n - n // 4
        S = (blocks + 1) * step + n
        # Resident in device memory, as calibrate_costs_gpu's series: no host copy before it.
        self.ser = self.plan.empty_shared((S,))
        self.ser[:] = ((rng.standard_normal(S) + 1j * rng.standard_normal(S)) / 2).astype(np.complex64)
        self.args = ((np.arange(blocks) * step).astype(np.int64),
                     np.full(blocks, n // 4, np.int64), np.full(blocks, n, np.int64))
        # The anchor is the fastest call of the warmed device; a call whose timer recorded
        # nothing (a rejected timestamp pair) is not a time.
        self.anchor = min((t for t in _warm(self._timed) if t > 0), default=0.0)
        reader = getattr(self.plan._gpu, "clock_mhz", None)
        mhz = reader() if reader is not None else None
        self._mhz = (reader, mhz) if mhz else None

    def time(self):
        """The reference, in device ns at the current clock: the anchor scaled by the clock
        when the backend reports one, else the reference call timed now."""
        if self._mhz is not None:
            reader, mhz0 = self._mhz
            now = reader()
            if now:
                return self.anchor * mhz0 / now
        return self._timed()

    def _timed(self):
        ctx = self.plan._gpu
        ctx._timing = True
        try:
            ctx.timings().clear()
            self.plan.run_series(self.ser, *self.args, threshold=1e6)
            log = ctx.timings()
            t = _gc._run_ms(log) * 1e6
            log.clear()
        finally:
            ctx._timing = False
        return t


_CLOCK_REFS = {}


def _clock_ref(device):
    ref = _CLOCK_REFS.get(str(device))
    if ref is None:
        ref = _CLOCK_REFS[str(device)] = _ClockRef(device)
    return ref


#: How calibrate_costs_gpu measures -- its series resident in device memory, each time the
#: fastest of its repetitions (runs), scaled to an anchor timed on a warmed device (_warm) --
#: and prices a second tier (_sparse_rows, the slope) and the feeds (the band forward at each
#: widest band and the full forward, against the head's), in its models' store key: a model
#: stored with another method is measured afresh.
_GPU_CAL_METHOD = "slope,resident,warm,feed,own"

#: Calls of a configuration back to back within each round of calibrate_costs_gpu (runs).
_BURST = 3

#: calibrate_costs_gpu's rounds, seed and template count when the caller names none (its
#: blocks default to a fixed span of series); a model measured otherwise is kept apart.
_GPU_CAL_REPS, _GPU_CAL_SEED, _GPU_CAL_TEMPLATES = 15, 11, 256


def _sparse_rows(points, head, pairs):
    """A second tier's [(density, device ns per first-tier survivor)] from runs of one chain
    at thresholds placed at _CAL_DENSITIES: points [(survivors, time)], head the measured
    time of the chain's first tier and blocks alone (the same rounds' run with nothing
    passing).

    With two or more points, the price is the slope of time against survivors, the same at
    every density. The runs differ only in their threshold, so what a run costs whatever
    passes -- a launch, or a process's state (in a ladder process, 30-40k of a 380k call
    appeared as soon as anything passed) -- cancels. The old price, (time - head) /
    survivors per point, put that and the head's error on the few survivors of the 1%
    point: 31-81 per survivor for band 512 at n=2048 on an 8060S, against a slope of 4.0-4.4
    in every process, which tied a one-tier chain with a two-tier one that ran in half its
    device time (2026-10-27). With one point, that point's old price."""
    pts = sorted((float(s1), float(t)) for s1, t in points if s1 > 0)
    if len(pts) >= 2:
        s1 = np.array([p[0] for p in pts]); t = np.array([p[1] for p in pts])
        slope = float(np.polyfit(s1, t, 1)[0])
        return [(a / pairs, max(1e-3, slope)) for a, _ in pts]
    return [(a / pairs, max(1e-3, (b - head) / a)) for a, b in pts]


def calibrate_costs_gpu(n, device, blocks=None, reps=_GPU_CAL_REPS, seed=_GPU_CAL_SEED,
                        nt=_GPU_CAL_TEMPLATES):
    """This GPU's tier costs at transform size n, in device nanoseconds, as a CostModel.

    The CPU calibration's construction (synthetic analytic noise, whitened random templates,
    thresholds placed at target survivor densities), timed by the device's own timestamps
    around each submission rather than tick counters: the GPU executes a chain as one
    recording, so a tier's cost is the difference between runs that differ in that tier.
      block      per-block fixed work (forward transform, compaction setup): from two template
                 counts at a threshold nothing passes
      dense[b]   a first tier at band b, per pair
      refine     per refined pair, at survivor densities _CAL_DENSITIES
      sparse[b]  a second tier at band b, per first-tier survivor (_sparse_rows: the slope
                 of time against survivors over the densities)
    Sized like a segment's call: a fixed span of series (2^21 samples: 1024 blocks at
    n=2048, 128 at 16384) against 256 templates, so every n is measured at the call size
    it serves and above the few thousand pairs where a GPU call is fixed latency. Sized
    in blocks instead, the work grew as n log n: 139 s at n=16384 and 814 s at 32768 on
    an M2. The device is warmed first: a GPU idle at a low clock reads slow for its first
    calls (one process of three priced band 128 at 2x the others). Every time is then
    scaled by a fixed reference call timed once a round (_ClockRef), so the model ranks
    configurations by ratios the clock cancels out of.
    The series is resident in device memory, as the fine stage reads its middle series in
    place. Copied from the host on every call (16 MB at n=2048, ~1.5 ms of host time), it
    left the device idle for that long before each timed call, and a device idle for 2 ms
    ran the next call 1.8x slower on the 8060S, by an amount that varied from call to call:
    the terms of one ladder process were 0.25-4x another's (second tier at band 512: 0.8 to
    18 per survivor, against 3.9-4.4 resident), enough to rank (256, 1024) at 0.7-1.5x
    (256, 512) where it ran 1.06x (2026-10-27).
    About a second per n on an M2, 5-8 s on the 8060S (15-26 s under CPU load 57), once per
    process, or read from MF_COST_FILE.
    """
    from . import HierarchicalFilter
    span = max(64, (1024 * 2048) // int(n))
    blocks = span if blocks is None else int(blocks)
    # Kept apart by the calls measured, as calibrate_costs' models are.
    how = (blocks, int(reps), int(seed), int(nt))
    key = ("gpu", int(n), str(device)) + how
    if key in _gc._COSTS:
        return _gc._COSTS[key]
    path = _gc._cost_file()
    skey = ("gpu,%d,%s" % (int(n), str(device))
            + "," + _GPU_CAL_METHOD
            + ("" if how == (span, _GPU_CAL_REPS, _GPU_CAL_SEED, _GPU_CAL_TEMPLATES) else ",b%d,r%d,s%d,t%d" % how))
    if path is not None:
        cm = _gc._stored_cost_model(path, skey)
        if cm is not None:
            _gc._COSTS[key] = cm
            return cm
    bands = _gc.candidate_bands(n)
    spec, ser, starts, ws, we = _gpu_cal_inputs(n, blocks, nt, seed)
    big = float(np.finfo(np.float32).max)
    plans = {}
    resident = []
    clock_refs = []

    def plan(chain, ntm):
        k = (tuple(chain), ntm)
        p = plans.get(k)
        if p is None:
            p = plans[k] = HierarchicalFilter(n, 1, ntm, chain=tuple(chain), device=device)
            p.set_templates(spec[:ntm])
        if not resident:
            resident.append(p.empty_shared(ser.shape))
            resident[0][:] = ser
        return p

    def call(p, thr, feed=None):
        """One timed run of plan p at thresholds thr, with the backend's own feed (None) or
        the full forward ("full"): (device ns, first-tier survivors, refined pairs)."""
        p.set_coarse_threshold(tuple(thr))
        ctx = p._gpu
        ctx._timing = True
        ctx.feed_forced = False if feed == "full" else None
        try:
            ctx.timings().clear()
            p.run_series(resident[0], starts, ws, we, threshold=1e6)
            log = ctx.timings()
            t = _gc._run_ms(log) * 1e6
            log.clear()
        finally:
            ctx._timing = False
            ctx.feed_forced = None
        return t, getattr(ctx, "last_tier1_survivors", 0), getattr(ctx, "last_refinements", 0)

    def runs(configs, reps=reps):
        """[(device ns per call, first-tier survivors, refined pairs)] for configs [(chain,
        thresholds[, templates[, feed]])] (templates None: nt): `reps` rounds, each timing the clock reference once
        (clock_refs) and every configuration in turn, _BURST times back to back. A time is
        its configuration's fastest, in device ns (the calibration scales them all to the
        reference's anchor by its fastest reference at the end).
        The fastest, not the median: what moves a call only adds time, and on the 8060S it
        moved them by 1.5-4x -- a device idle between calls (above); a slow spell of several
        milliseconds (a second tier at band 1024 read 0.75, 0.63, 0.58, 0.59, 0.52, 0.53 ms
        for a call that ran 0.35 before and after, and the median of five, even the minimum
        of five in a row, moved its slope 2.3x); and under CPU load (load 57, other users'
        jobs) a power-limited GPU throttled through sustained work, where a band-512 first
        tier ran 0.62 ms at best and 0.9-1.5 ms in the median. In turn (_choice.fastest_of_rounds,
        each round timing the clock reference first), so that a spell
        slows a burst of several configurations and never every call of one; in bursts,
        because under load the fast state came in runs of calls: 15 rounds of 1 left a
        configuration without a fast call in two calibrations of six, 15 rounds of 3 in
        none of twelve.
        A reference timed just before each call (the earlier pairing) no longer stood for
        that call's clock: under load it ran at 0.13 ms in place of 0.03 for 40% of calls
        whose own state was the fast one, and scaled them to a quarter."""
        ps = [(plan(c[0], c[2] if len(c) > 2 and c[2] else nt), c[1], c[3] if len(c) > 3 else None)
              for c in configs]
        for p, thr, feed in ps:
            call(p, thr, feed)                                        # warm-up, recording
        s1, r = ([[] for _ in ps] for _ in range(2))

        def time_one(i):
            p, thr, feed = ps[i]
            ti, si, ri = call(p, thr, feed)
            s1[i].append(si)
            r[i].append(ri)
            return ti
        # a call whose timer recorded nothing (a rejected timestamp pair) is not a time
        t = _choice.fastest_of_rounds(range(len(ps)), time_one, reps, burst=_BURST,
                                      each_round=lambda: clock_refs.append(clock.time()))
        return [(t[i], float(np.median(s1[i])), float(np.median(r[i]))) for i in range(len(ps))]

    def refined_pairs(chain, thr):
        """Refined pairs of one run (its time unused): thresholds are placed by counts."""
        return call(plan(chain, nt), thr)[2]

    def thr_for(b, density):
        """Tier-0 threshold at band b passing about `density` of pairs (_pass_threshold)."""
        return _pass_threshold(lambda t: refined_pairs((b,), (t,)) / (blocks * nt), density,
                               b * (n - n // 4) // n)

    b0 = bands[0]
    clock = _clock_ref(device)
    _warm(lambda: call(plan((b0,), nt), (big,)))
    (t_small, _, _), (t_full, _, _) = runs([((b0,), (big,), nt // 4), ((b0,), (big,))])
    if not (t_full > 0 and t_small > 0):
        # A backend that ignored the timer switch reports nothing, and a model priced at zero
        # picks the largest blocks and widest gates (seen on CUDA): refuse rather than guess.
        raise RuntimeError("device timers recorded no time on %s; cannot calibrate GPU costs"
                           % (device,))
    per_pair0 = (t_full - t_small) / (blocks * (nt - nt // 4))
    block = max(0.0, t_full / blocks - nt * per_pair0)
    dense = {}
    for b, (t, _, _) in zip(bands, runs([((b,), (big,)) for b in bands])):
        dense[b] = max(1e-3, (t / blocks - block) / nt)
    refine, sparse, tier2 = [], {}, {}
    thr0 = [thr_for(b0, f) for f in _gc._CAL_DENSITIES]
    # The first tier and blocks alone (the modelled head, blocks * (block + nt * dense[b0]),
    # is this same run's time) timed in the same rounds as the runs it is subtracted from:
    # a run's time depends on what ran before it (a device cache warm with its own data or
    # another configuration's), and the refine at 1%, ~30% of its run, came out at zero
    # against the head of another round in one calibration of nine.
    # The feeds, in the same rounds: at a threshold nothing passes, the chain (b0, B) runs
    # what the head runs but for its forward, the band forward at widest band B (where the
    # backend takes it); and the head with the full forward forced.
    configs = ([((b0,), (big,))] + [((b0,), (g0,)) for g0 in thr0]
               + [((b0, b), (g0, big)) for g0 in thr0 for b in bands[1:]]
               + [((b0, b), (big, big)) for b in bands[1:]] + [((b0,), (big,), None, "full")])
    timed = iter(runs(configs))
    head = next(timed)[0]
    for _ in thr0:
        t, _, refined = next(timed)
        if refined:
            refine.append((refined / (blocks * nt), max(1e-3, (t - head) / refined)))
    for _ in thr0:
        for b in bands[1:]:
            t2, s1, _ = next(timed)
            if s1:
                tier2.setdefault(b, []).append((s1, t2))
    feed_band = {b0: 0.0}
    for b in bands[1:]:
        feed_band[b] = (next(timed)[0] - head) / blocks
    feed = {"band": feed_band, "full": (next(timed)[0] - head) / blocks}
    # A first tier at band b was timed alone, its feed the band forward at b: that is the
    # feed's (feed_delta prices it by the chain's widest band), not the tier's.
    dense = {b: max(1e-3, v - feed_band.get(b, 0.0) / nt) for b, v in dense.items()}
    for b, pts in tier2.items():
        sparse[b] = _sparse_rows(pts, head, blocks * nt)
    if bands[1:]:
        sparse.setdefault(b0, list(sparse.get(bands[1], [])))
    # Every time to the reference's anchor units: the fastest reference of the calibration
    # against its fastest in this process (see _ClockRef), so models at different n, made at
    # different times, stay comparable.
    fast = min(clock_refs) if clock_refs else 0.0
    k = clock.anchor / fast if fast > 0 else 1.0
    block *= k
    dense = {b: v * k for b, v in dense.items()}
    refine = [(f, v * k) for f, v in refine]
    sparse = {b: [(f, v * k) for f, v in rows] for b, rows in sparse.items()}
    feed = {"band": {b: v * k for b, v in feed["band"].items()}, "full": feed["full"] * k}
    cm = _gc.CostModel(n, dense, sparse, refine, block=block, feed=feed)
    if path is not None:          # another process's model, stored first, is the one used
        cm = _gc.CostModel.from_dict(_gc._store_first(path, skey, cm.to_dict(), _gc._cost_model_ok))
    _gc._COSTS[key] = cm
    return cm


def _gpu_cal_inputs(n, blocks, nt, seed):
    """The synthetic series and templates calibrate_costs_gpu measures on."""
    rng = np.random.default_rng(seed)
    taps = n // 4
    h = np.zeros((nt, n), np.complex64)
    h[:, :taps] = rng.standard_normal((nt, taps)) / np.sqrt(taps)
    spec = np.fft.fft(h, axis=1).astype(np.complex64)
    step = n - taps
    S = (blocks + 1) * step + n
    x = (rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2)
    X = np.fft.fft(x); X[S // 2:] = 0
    ser = (np.fft.ifft(X) * np.sqrt(2)).astype(np.complex64)
    starts = (np.arange(blocks) * step).astype(np.int64)
    ws = np.full(blocks, taps, np.int64); we = np.full(blocks, n, np.int64)
    return spec, ser, starts, ws, we


def device_costs(n, device=None, ntemplates=_gc._CAL_TEMPLATES, group=None):
    """The cost model of the device a plan runs on: CPU tick counters, or GPU device time."""
    from .device import parse as _parse_device
    dev = _parse_device(device)
    if dev.kind == "gpu":
        return calibrate_costs_gpu(n, str(dev))
    return calibrate_costs(n, ntemplates, group=group)


def price_block_sizes(fine, delta_f, data_rate, longest, margin, ntemplates, snr, fd, candidates,
                      max_tiers=3, device=None, ahead=0):
    """Rank block sizes for one bank by modelled cost per valid output sample and template.

    For each n the bank would run one plan over blocks advancing n - longest + 1 samples; a
    block costs its fixed work (calibrated) spread over the templates, plus every pair's cost
    under the best chain at that n (gate model with the reference rebinned to n, calibrated
    tier costs). Returns [(cost, n, chain)] sorted, cheapest first.

    Candidates are priced in ascending order and the search stops at the first that
    costs more than the best so far: a pair's cost grows faster than n (every tier and
    the refine scale with it at fixed bandwidth) while the valid fraction only creeps
    toward one, so past the minimum larger blocks only get dearer -- and pricing one
    means calibrating and simulating at that size.
    """
    sig = _gc._gm._profile_sig(np.asarray(fine, np.float64))
    out = []
    for n in sorted(int(c) for c in candidates):
        nvalid = n - int(longest) + 1
        if nvalid < 1:
            continue
        q = max(n // 32, 1)                  # the bank prices its windows on this grid
        lo = (int(margin) // q) * q
        key = (sig, float(delta_f), float(data_rate), n, lo, float(snr), float(fd), int(max_tiers), str(device),
               _gc.cpu_gate_kind(), int(ntemplates))
        hit = _gc._PRICE_CACHE.get(key)
        if hit is None:
            ref = _gc.rebin_profile(fine, delta_f, data_rate, n)
            hit = (None, None, None)
            if ref is not None:
                ref = ref.astype(np.float32, copy=False)
                cm = device_costs(n, device, ntemplates)
                best, _ = _gc.choose_chain(ref, n, snr, fd, cost=cm, max_tiers=max_tiers, window=(lo, n - lo),
                                           ntemplates=ntemplates)
                if best is not None:
                    hit = (cm.block, best["cost"], best["chain"])
            _gc._cache_put(_gc._PRICE_CACHE, key, hit)
        else:
            _gc._PRICE_CACHE.move_to_end(key)
        block, pair_cost, chain = hit
        if pair_cost is None:
            continue
        # per valid output sample and template: the block's fixed work shared by the bank's templates
        c = (block / max(int(ntemplates), 1) + pair_cost) / nvalid
        # Stop at the first size dearer than the best so far (it is still listed, so a size
        # within TIE stays in the tie-break below), after `ahead` more dearer ones for
        # a joint trial's block-size arms. Continuing past a size merely within TIE priced the
        # next size too -- a timed calibration at that n (about 11 s at 8192 on Zen 3) for a
        # size that is dearer still.
        best = min((o[0] for o in out), default=None)
        stop = best is not None and c > best and \
            sum(o[0] > best for o in out) + 1 > ahead
        out.append((c, n, chain))
        if stop:
            break
    out.sort()
    # Within TIE of the cheapest, prefer the smaller n so calibration noise does not flip
    # neighbouring block sizes between processes.
    first = _gc.pick_stable(out, lambda o: o[0], lambda o: o[1])
    if first is not None:
        out.remove(first)
        out.insert(0, first)
    return out


_gc.calibrate_costs = calibrate_costs    # gatechain.calibrate_costs, the public name
