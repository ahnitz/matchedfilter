"""Measuring this machine's tier costs through the engine itself: the CPU and GPU cost-model
calibrations, the per-device block costs and the block-size pricing that uses them. They run
hierarchical plans, so they sit above the model (gatechain), which they feed."""
import math
import os
import time

import numpy as np

from . import gatechain as _gc


def calibrate_costs(n, ntemplates, blocks=256, reps=5, seed=11, group=None):
    """Measure this machine's tier costs at transform size n through the engine itself.

    Synthetic analytic noise and whitened random templates; thresholds are
    placed so that the tier under test sees each target survivor density, and
    costs are read from the engine's per-tier counters (ap_hmf_tier_stats), so
    no wall-clock subtraction is involved. Calls are sized like a segment's
    (hundreds of blocks), because a pooled tier's fixed per-call cost is only
    representative when amortised over a realistic number of survivors.
    Under a second per (n, series group), once per process. Runs at _CAL_TEMPLATES
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
    key = (int(n), nt, group) + (("g16",) if g16 else ())
    if key in _gc._COSTS:
        return _gc._COSTS[key]
    path = _gc._cost_file()
    # A model made without the Q15 screen's prices (an older build, or a back end without
    # it) must not be reused by one that has it, or the screen is never priced.
    skey = "%d,%d,%d" % key[:3] + (",g16" if g16 else "") + (",q15" if not g16 and _gc._q15_band(64) else "")
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

    def run(chain, thr, reps=reps, q15=False, stats=False):
        """Pairs per call and per-tier (band, passed, ticks) per call: medians over repetitions.
        With stats, also the Q15 screen's (on, passed, ticks) per call."""
        with _gc._internal_plans():
            p = _core.HMF(n, 1, nt, list(chain), group, n)
        p.set_reference(ref); p.set_template_batch(0, spec); p.set_thresholds(list(thr))
        if q15:
            p.set_q15(True)
        p.run_series(ser, starts, ws, we, 0, nt, n, big, idx, val, mag, cnt)      # warm-up
        prev = p.tier_stats(); rows = []
        qprev = p.q15_stats(); qrows = []
        for _ in range(reps):
            p.run_series(ser, starts, ws, we, 0, nt, n, big, idx, val, mag, cnt)
            cur = p.tier_stats()
            rows.append([(c[1] - q[1], c[2] - q[2]) for c, q in zip(cur, prev)])
            prev = cur
            qcur = p.q15_stats()
            qrows.append((qcur[1] - qprev[1], qcur[2] - qprev[2]))
            qprev = qcur
        med = [(prev[i][0], float(np.median([r[i][0] for r in rows])), float(np.median([r[i][1] for r in rows])))
               for i in range(len(prev))]
        if stats:
            return blocks * nt, med, (qprev[0], float(np.median([r[0] for r in qrows])),
                                      float(np.median([r[1] for r in qrows])))
        return blocks * nt, med

    def thr_for(b, density):
        """Tier-0 threshold at band b passing about `density` of pairs (secant on log pass rate)."""
        lo, hi = 0.0, 16.0
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            pairs, st = run((b,), (mid,), reps=1)
            frac = st[0][1] / pairs
            if frac > density:
                lo = mid
            else:
                hi = mid
            if abs(frac - density) < 0.25 * density:
                break
        return mid

    dense, sparse, refine = {}, {}, []
    block = []
    for b in bands:
        pairs, st = run((b,), (big,))
        dense[b] = st[0][2] / pairs
    # Per-block fixed work: a whole run_series call minus its tiers and refine (nothing passes), per block.
    for b in bands[:2]:
        with _gc._internal_plans():
            p = _core.HMF(n, 1, nt, [b], group, n)
        p.set_reference(ref); p.set_template_batch(0, spec); p.set_thresholds([big])
        p.run_series(ser, starts, ws, we, 0, nt, n, big, idx, val, mag, cnt)
        per = []
        for _ in range(reps):
            s0, t0 = p.series_ticks(), sum(x[2] for x in p.tier_stats())
            p.run_series(ser, starts, ws, we, 0, nt, n, big, idx, val, mag, cnt)
            per.append((p.series_ticks() - s0 - (sum(x[2] for x in p.tier_stats()) - t0)) / blocks)
        block.append(float(np.median(per)))
    b0 = bands[0]
    for f in _gc._CAL_DENSITIES:
        g0 = thr_for(b0, f)
        pairs, st = run((b0,), (g0,))
        if st[-1][1]:
            refine.append((st[0][1] / pairs, st[-1][2] / st[-1][1]))
        for b in bands[1:]:
            pairs, st = run((b0, b), (g0, big))
            if st[0][1]:
                sparse.setdefault(b, []).append((st[0][1] / pairs, st[1][2] / st[0][1]))
    # the first band can only be a first tier; give it the next band's sparse curve for completeness
    if bands[1:]:
        sparse.setdefault(b0, list(sparse.get(bands[1], [])))
    screen = {}
    if not g16:
        for b in bands:
            if not _gc._q15_band(b):
                continue
            # screen alone: at an unreachable threshold nothing passes, so the tier's ticks are
            # the screen's; then at calibrated densities, how many pairs it passes to the float
            # tier and what re-running them costs
            pairs, st = run((b,), (big,), q15=True)
            ent = {"dense": st[0][2] / pairs, "excess": [], "recheck": 0.0}
            rc = []
            for f in _gc._CAL_DENSITIES:
                g = thr_for(b, f)
                pairs, st, qs = run((b,), (g,), q15=True, stats=True)
                if st[0][1] and qs[1]:
                    ent["excess"].append((st[0][1] / pairs, qs[1] / pairs))
                    rc.append((st[0][2] - qs[2]) / qs[1])
            if ent["excess"]:
                ent["recheck"] = float(np.median(rc))
                screen[b] = ent
    cm = _gc.CostModel(n, dense, sparse, refine, block=float(np.median(block)), screen=screen)
    if path is not None:          # another process's model, stored first, is the one used
        cm = _gc.CostModel.from_dict(_gc._store_first(path, skey, cm.to_dict(), _gc._cost_model_ok))
    _gc._COSTS[key] = cm
    return cm


#: Per device: the fixed reference call and its first warmed device time (see _ClockRef).
class _ClockRef:
    """A fixed reference call, timed next to every calibration measurement.

    A GPU's clock moves with load and power state (an idle M2 reads slow for its first
    calls; an APU's GPU drops to a fifth of its clock under CPU load), so a device time is
    the work divided by a clock that is not constant across a calibration, let alone
    across n. Each measurement is therefore taken as the ratio to this reference timed
    just before it, and reported in reference units scaled by the reference's first warmed
    time in this process: chains and block sizes are ranked by those ratios, which the
    clock cancels out of. One small, fixed workload for every n, so models at different n
    stay comparable. Backend-neutral: it only needs device timers (ctx.timings()).

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
        self.ser = ((rng.standard_normal(S) + 1j * rng.standard_normal(S)) / 2).astype(np.complex64)
        self.args = ((np.arange(blocks) * step).astype(np.int64),
                     np.full(blocks, n // 4, np.int64), np.full(blocks, n, np.int64))
        import time as _time
        until = _time.perf_counter() + 0.25          # warm the device before the anchor
        self._timed()
        while _time.perf_counter() < until:
            self._timed()
        self.anchor = min(self._timed() for _ in range(5))
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


def calibrate_costs_gpu(n, device, blocks=None, reps=5, seed=11, nt=256):
    """This GPU's tier costs at transform size n, in device nanoseconds, as a CostModel.

    The CPU calibration's construction (synthetic analytic noise, whitened random templates,
    thresholds placed at target survivor densities), timed by the device's own timestamps
    around each submission rather than tick counters: the GPU executes a chain as one
    recording, so a tier's cost is the difference between runs that differ in that tier.
      block      per-block fixed work (forward transform, compaction setup): from two template
                 counts at a threshold nothing passes
      dense[b]   a first tier at band b, per pair
      refine     per refined pair, at survivor densities _CAL_DENSITIES
      sparse[b]  a second tier at band b, per first-tier survivor
    Sized like a segment's call: a fixed span of series (2^21 samples: 1024 blocks at
    n=2048, 128 at 16384) against 256 templates, so every n is measured at the call size
    it serves and above the few thousand pairs where a GPU call is fixed latency. Sized
    in blocks instead, the work grew as n log n: 139 s at n=16384 and 814 s at 32768 on
    an M2. The device is warmed first: a GPU idle at a low clock reads slow for its first
    calls (one process of three priced band 128 at 2x the others). Every time is then
    taken relative to a fixed reference call timed alongside it (_ClockRef), so the model
    ranks configurations by ratios the clock cancels out of.
    About a second per n on an M2, once per process, or read from MF_COST_FILE.
    """
    from . import HierarchicalFilter
    if blocks is None:
        blocks = max(64, (1024 * 2048) // int(n))
    kind = _gc.gpu_gate_kind(device)
    key = ("gpu", int(n), str(device), kind)
    if key in _gc._COSTS:
        return _gc._COSTS[key]
    path = _gc._cost_file()
    # Keyed by gate kind: a model measured with the bound off (or before it existed) prices a
    # different first tier, and must not be reused for this one.
    skey = "gpu,%d,%s" % (int(n), str(device)) + ("" if kind == "f32" else "," + kind)
    if path is not None:
        cm = _gc._stored_cost_model(path, skey)
        if cm is not None:
            _gc._COSTS[key] = cm
            return cm
    bands = _gc.candidate_bands(n)
    spec, ser, starts, ws, we = _gpu_cal_inputs(n, blocks, nt, seed)
    big = float(np.finfo(np.float32).max)
    plans = {}
    import time as _time

    def run(chain, thr, ntm=nt, reps=reps):
        """(device ns per call, first-tier survivors, refined pairs). The time is the median
        over repetitions of its ratio to the clock reference timed just before it, in the
        reference's anchor units (see _ClockRef): the median, because a ratio of two noisy
        times has outliers on both sides and the minimum picks one."""
        k = (tuple(chain), ntm)
        p = plans.get(k)
        if p is None:
            p = plans[k] = HierarchicalFilter(n, 1, ntm, chain=tuple(chain), device=device)
            p.set_templates(spec[:ntm])
        p.set_coarse_threshold(tuple(thr))
        ctx = p._gpu
        ctx._timing = True
        p.run_series(ser, starts, ws, we, threshold=1e6)                 # warm-up, recording
        ctx.timings().clear()
        t, s1, r = [], [], []
        for _ in range(reps):
            ctx._timing = False
            ref_t = clock.time()             # the reference, just before: same clock state
            ctx._timing = True
            ctx.timings().clear()
            p.run_series(ser, starts, ws, we, threshold=1e6)
            log = ctx.timings()
            dev = _gc._run_ms(log) * 1e6
            t.append(dev * (clock.anchor / ref_t if ref_t > 0 else 1.0))
            log.clear()
            s1.append(getattr(ctx, "last_tier1_survivors", 0))
            r.append(getattr(ctx, "last_refinements", 0))
        ctx._timing = False
        return float(np.median(t)), float(np.median(s1)), float(np.median(r))

    def thr_for(b, density):
        lo, hi = 0.0, 16.0
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            _, _, refined = run((b,), (mid,), reps=1)
            frac = refined / (blocks * nt)
            if frac > density:
                lo = mid
            else:
                hi = mid
            if abs(frac - density) < 0.25 * density:
                break
        return mid

    b0 = bands[0]
    clock = _clock_ref(device)
    warm_until = _time.perf_counter() + 0.25
    run((b0,), (big,), reps=1)
    while _time.perf_counter() < warm_until:
        run((b0,), (big,), reps=1)
    t_small, _, _ = run((b0,), (big,), ntm=nt // 4)
    t_full, _, _ = run((b0,), (big,))
    if not (t_full > 0 and t_small > 0):
        # A backend that ignored the timer switch reports nothing, and a model priced at zero
        # picks the largest blocks and widest gates (seen on CUDA): refuse rather than guess.
        raise RuntimeError("device timers recorded no time on %s; cannot calibrate GPU costs"
                           % (device,))
    per_pair0 = (t_full - t_small) / (blocks * (nt - nt // 4))
    block = max(0.0, t_full / blocks - nt * per_pair0)
    dense = {}
    for b in bands:
        t, _, _ = run((b,), (big,))
        dense[b] = max(1e-3, (t / blocks - block) / nt)
    refine, sparse = [], {}
    for f in _gc._CAL_DENSITIES:
        g0 = thr_for(b0, f)
        t, _, refined = run((b0,), (g0,))
        if refined:
            refine.append((refined / (blocks * nt), max(1e-3, (t - blocks * (block + nt * dense[b0])) / refined)))
        for b in bands[1:]:
            t2, s1, _ = run((b0, b), (g0, big))
            if s1:
                sparse.setdefault(b, []).append(
                    (s1 / (blocks * nt), max(1e-3, (t2 - blocks * (block + nt * dense[b0])) / s1)))
    if bands[1:]:
        sparse.setdefault(b0, list(sparse.get(bands[1], [])))
    # The first tier's pass excess over its own statistic, per band: the same threshold,
    # refined pairs with the gate's bound on against off. Only where the backend has a bound.
    # The raw gate runs in a child process: the switch is read where pipelines are built
    # and baked into recorded command buffers, so it cannot be flipped inside one context.
    excess = {}
    if kind != "f32":
        for b, g, r_raw in _raw_gate_survivors(n, device, bands, blocks, nt, seed):
            _, _, r_bnd = run((b,), (g,))
            excess.setdefault(b, []).append((r_raw / (blocks * nt), r_bnd / (blocks * nt)))
    # The forward's share of the per-block work: the calibration cannot time it apart (one
    # submission), and per-block fixed work on the GPU is the forward transform plus small
    # bookkeeping, so `block` stands for it (an upper estimate of what a band forward saves).
    forward = block
    cm = _gc.CostModel(n, dense, sparse, refine, block=block, excess=excess,
                   forward=forward, band_forward=_gc._is_gpu(device))
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


def _raw_survivors_here(n, device, bands, blocks, nt, seed):
    """[(band, threshold, refined pairs)] with this process's gate, at thresholds placed at
    _CAL_DENSITIES: run by _raw_gate_survivors in a child with the raw switch set."""
    from . import HierarchicalFilter
    spec, ser, starts, ws, we = _gpu_cal_inputs(n, blocks, nt, seed)
    out = []
    for b in bands:
        p = HierarchicalFilter(n, 1, nt, chain=(int(b),), device=device)
        p.set_templates(spec)

        def refined(g):
            p.set_coarse_threshold((g,))
            p.run_series(ser, starts, ws, we, threshold=1e6)
            return p._gpu.last_refinements

        for f in _gc._CAL_DENSITIES:
            lo, hi = 0.0, 16.0
            for _ in range(14):
                mid = 0.5 * (lo + hi)
                r = refined(mid)
                if r / (blocks * nt) > f:
                    lo = mid
                else:
                    hi = mid
                if abs(r / (blocks * nt) - f) < 0.25 * f:
                    break
            out.append((int(b), float(mid), int(refined(mid))))
    return out


def _raw_gate_survivors(n, device, bands, blocks, nt, seed):
    row = _gc._RAW_GATE_SWITCH
    if not _gc._is_gpu(device):
        return []
    import json, subprocess, sys
    env = dict(os.environ)
    env[row[0]] = row[1]
    env.pop("MF_COST_FILE", None)
    code = ("import json,sys; from matchedfilter import _calibration as g; "
            "print(json.dumps(g._raw_survivors_here(%d, %r, %r, %d, %d, %d)))"
            % (int(n), str(device), [int(b) for b in bands], int(blocks), int(nt), int(seed)))
    pkg = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env["PYTHONPATH"] = pkg + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    res = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError("raw-gate calibration failed: %s" % res.stderr[-2000:])
    return [tuple(r) for r in json.loads(res.stdout.strip().splitlines()[-1])]


def device_costs(n, device=None, ntemplates=_gc._CAL_TEMPLATES, group=None):
    """The cost model of the device a plan runs on: CPU tick counters, or GPU device time."""
    from .device import parse as _parse_device
    dev = _parse_device(device)
    if dev.kind == "gpu":
        return calibrate_costs_gpu(n, str(dev))
    return calibrate_costs(n, ntemplates, group=group)


def price_block_sizes(fine, delta_f, data_rate, longest, margin, ntemplates, snr, fd, candidates,
                      max_tiers=3, device=None, ahead=0, model_f=False):
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
               _gc.cpu_gate_kind(), bool(model_f), int(ntemplates))
        hit = _gc._PRICE_CACHE.get(key)
        if hit is None:
            ref = _gc.rebin_profile(fine, delta_f, data_rate, n)
            hit = (None, None, None)
            if ref is not None:
                cm = device_costs(n, device, ntemplates)
                best, _ = _gc.choose_chain(ref, n, snr, fd, cost=cm, max_tiers=max_tiers, window=(lo, n - lo),
                                       ntemplates=ntemplates, model_f=model_f)
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
        # block-size trial candidates. Continuing past a size merely within TIE priced the
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


_gc._CALIBRATE = calibrate_costs         # gatechain.calibrate_costs, the public name
