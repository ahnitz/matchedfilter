#!/usr/bin/env python3
"""The three-level FIR search's call pattern on ideal data: a standalone bench for every device.

An analogue of pycbc_inspiral_fir that needs no pycbc, so the library can be developed and
measured on any backend against the workload it serves. Per top template, per segment, per
detector:

  top     an analytic Gaussian series with an inspiral-like spectrum (pycbc's reference SNR
          series of one top template; here generated, untimed, like data setup)
  middle  TimeDomainFilterBank(engine='corr') over the top template's middle taps: one
          correlation series per middle template
  fine    per middle template, its fine bank (engine='hier', threshold 6, FD 1e-3, one peak per
          second) over the analysed part of that middle series
  asym    each fine trigger above the asym threshold (at most one per group per second) is
          followed up in the other detector: one template, a window of num_bins bins, threshold
          0 -- the single-template call pycbc's asymmetric follow-up makes

Taps come from a three-level bank file (fir_data/upper/<top> -> middle taps, fir_data/<middle>
-> fine taps), the format pycbc reads. The first --warmup segments (default 2) of each top
template are reported separately: the first holds plan construction and the bank's block and
chain choices, the second the chain trials locking (MF_AUTOTUNE). Neither recurs.

    python tools/ladder.py --bank BANK.hdf --device gpu:0 --tops 2 --segments 3
    python tools/ladder.py --bank BANK.hdf --device gpu:0 --check cpu      # outputs vs the CPU

Throughput is templates-in-real-time: fine templates x analysed seconds x detectors / time.
"""
import argparse
import json
import os
import platform
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
import matchedfilter as mf                                    # noqa: E402
from matchedfilter import TimeDomainFilterBank, _gputime      # noqa: E402
from matchedfilter import _roofline                           # noqa: E402
from matchedfilter.time_domain import SegmentPlan             # noqa: E402

RATE = 2048.0
DF = 1.0 / 16


def profile():
    """Output-power profile on a fine grid: inspiral-like, 20-900 Hz (the fine banks' reference)."""
    f = np.arange(int(RATE / 2 / DF) + 1) * DF
    return np.where((f > 20) & (f < 900), np.maximum(f, 1.0) ** (-7.0 / 3), 0.0)


def analytic_series(rng, S, amp, df=DF, out=None):
    """Analytic Gaussian series of length S, spectrum amp(f) (on a grid of spacing df), unit
    variance per quadrature. out: a complex64 array of length S to write it into (e.g. a
    bank's empty_shared buffer, which correlate_series then reads without a copy)."""
    X = np.fft.fft(rng.standard_normal(S))
    k = np.arange(S // 2)
    X[:S // 2] *= np.interp(k * RATE / S, np.arange(amp.size) * df, amp)
    X[S // 2:] = 0
    x = np.fft.ifft(X)
    x /= np.sqrt(np.mean(np.abs(x) ** 2) / 2)
    if out is not None:
        out[:] = x
        return out
    return x.astype(np.complex64)


def load_tops(path, ntops):
    """The ntops top templates with the most fine templates, with their middle and fine taps."""
    import h5py
    with h5py.File(path, "r") as f:
        fir = f["fir_data"]
        up = fir["upper"]
        tops = []
        for key in (k for k in up.keys() if k.isdigit()):
            g = up[key]
            mids = g["fine_bank_index"][:]
            nfine = sum(fir[str(int(m))]["taps"].shape[0] for m in mids if str(int(m)) in fir)
            tops.append((nfine, int(key)))
        tops.sort(reverse=True)
        out = []
        for nfine, tid in tops[:ntops]:
            g = up[str(tid)]
            counts = g["actual_tap_count"][:]
            order = np.argsort(counts, kind="stable")
            mids = g["fine_bank_index"][:][order]
            fine = []
            for m in mids:
                fg = fir[str(int(m))]
                c = fg["actual_tap_count"][:]
                fine.append((int(m), fg["taps"][:, :int(c.max())].astype(np.float32), c))
            out.append(dict(top=tid, mid_taps=g["taps"][:][order].astype(np.float32),
                            mid_counts=counts[order], mids=mids, fine=fine, nfine=nfine))
    return out


class Timer:
    """Wall time per stage and, with --timing, device time per stage and kernel label."""

    def __init__(self):
        self.t = defaultdict(float)
        self.n = defaultdict(int)
        self.device = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))

    def add(self, key, dt, n=1):
        self.t[key] += dt
        self.n[key] += n
        if _timing():
            for label, (calls, ms) in _gputime.collect().items():
                d = self.device[key][label]
                d[0] += calls
                d[1] += ms


class GpuSampler:
    """Samples the GPU's shader clock and the driver's busy percentage (amdgpu sysfs:
    hwmon freq1_input, gpu_busy_percent) every 20 ms while on: an independent device-busy
    figure, and the clock the timestamps were taken at. Silent where the files are absent."""

    def __init__(self):
        import glob
        self.files = []
        for dev in glob.glob("/sys/class/drm/card*/device"):
            busy = dev + "/gpu_busy_percent"
            freq = glob.glob(dev + "/hwmon/hwmon*/freq1_input")
            if os.path.exists(busy) and freq:
                self.files.append((busy, freq[0]))
        self.nvml = None
        if not self.files:                     # CUDA: NVML utilization and SM clock
            try:
                from matchedfilter import _cuda
                self.nvml = _cuda.nvml_busy(0)
            except Exception:                  # noqa: BLE001 -- no NVML: silent, as without sysfs
                self.nvml = None
        self.samples, self.on, self.thread = [], False, None

    def _run(self):
        while self.thread is not None:
            if self.on and self.nvml is not None:
                v = self.nvml()
                if v is not None:
                    self.samples.append(v)
            if self.on:
                for busy, freq in self.files:
                    try:
                        with open(busy) as b, open(freq) as f:
                            self.samples.append((int(b.read()), int(f.read()) / 1e6))
                    except (OSError, ValueError):
                        pass
            time.sleep(0.02)

    def start(self):
        if (self.files or self.nvml is not None) and self.thread is None:
            import threading
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def stop(self):
        self.thread = None

    def mark(self, on):
        """Steady span starts (on) / ends: device intervals (Metal, MF_GPU_TIMING=1) are
        cleared at the start and their union taken at the end, against the host span."""
        if on and not self.on:
            _gputime.busy(clear=True)
            self.t_on = time.perf_counter()
        self.on = on

    def busy_union(self):
        if getattr(self, "t_on", None) is None:
            return None
        wall = time.perf_counter() - self.t_on
        tot, _, _ = _gputime.busy(clear=True)
        return dict(busy_pct=100.0 * tot / wall, device_s=tot, wall_s=wall) if tot else None

    def report(self):
        if not self.samples:
            return None
        b = np.array([x[0] for x in self.samples], float)
        f = np.array([x[1] for x in self.samples], float)
        return dict(busy_pct=float(b.mean()), sclk_mhz_mean=float(f.mean()),
                    sclk_mhz_min=float(f.min()), sclk_mhz_max=float(f.max()), n=len(b))


def _timing():
    import os
    return os.environ.get("MF_GPU_TIMING", "0") not in ("", "0")


def report_counts(counts, seg_plan):
    if os.environ.get("LADDER_REPLAY"):
        counts["segment_replays"] += seg_plan.replays
        counts["segment_capture_failures"] += getattr(seg_plan, "capture_failures", 0)
        for k in ("followups_device", "followups_host", "followups_overflow"):
            if getattr(seg_plan, k, 0):
                counts[k] += getattr(seg_plan, k)


def drive_folded(gens, args, first, steady, counts):
    """LADDER_FOLD_TOPS: every top's segment k as ONE SegmentPlan request -- their middle
    stages (preludes), fine stages and follow-ups in one capture, one graph per segment."""
    from matchedfilter.time_domain import FollowUp
    plan = SegmentPlan()
    reqs = [next(g) for g in gens]
    seg = 0
    while reqs:
        tm = first if seg < args.warmup else steady
        t_seg = time.perf_counter()
        jobs, offs, preludes, keys, pairs, spec0 = [], [], [], [], [], None
        for jb, prelude, pkey, spec in reqs:
            offs.append(len(jobs))
            if spec is not None:
                spec0 = spec
                pairs += [p + len(jobs) for p in spec.pairs]
            jobs += jb
            if prelude is not None:
                preludes.append(prelude)
                keys.append(pkey)

        def prelude_all(preludes=preludes):
            for f in preludes:
                f()
        spec_all = (FollowUp(pairs, spec0.threshold, spec0.dedupe, spec0.half, spec0.binsize,
                             max_items=spec0.max_items * len(reqs),
                             max_items_per_region=spec0.max_items_per_region)
                    if spec0 is not None else None)
        t = time.perf_counter()
        out = plan.run(jobs, prelude=prelude_all if preludes else None,
                       prelude_key=tuple(keys) if preludes else None, followup=spec_all)
        fine_out, fu = out if spec_all is not None else (out, None)
        tm.add("fine", time.perf_counter() - t)
        if os.environ.get("LADDER_DUMP"):
            import pickle
            with open(os.environ["LADDER_DUMP"] + ".%d" % seg, "wb") as fh:
                pickle.dump([(a.template_indices, a.sample_indices, a.snr) for a in fine_out], fh)
        if os.environ.get("LADDER_VERIFY_REPLAY"):
            again = TimeDomainFilterBank.filter_series_many(jobs)
            bad = [j for j, (a, b) in enumerate(zip(fine_out, again))
                   if not (np.array_equal(a.sample_indices, b.sample_indices)
                           and np.array_equal(a.snr, b.snr))]
            print("verify folded seg %d: replays %d, mismatched jobs %s, peaks %d vs %d"
                  % (seg, plan.replays, bad[:8], sum(len(a.snr) for a in fine_out),
                     sum(len(a.snr) for a in again)), flush=True)
        nxt = []
        for k, g in enumerate(gens):
            lo = offs[k]
            hi = offs[k + 1] if k + 1 < len(offs) else len(jobs)
            mine = None if fu is None else [(j - lo, r, c, ti, fr) for j, r, c, ti, fr in fu
                                              if lo <= j < hi]
            try:
                nxt.append((g, g.send((fine_out[lo:hi], mine))))
            except StopIteration:
                pass
        tm.add("segment", time.perf_counter() - t_seg)
        gens = [g for g, _ in nxt]
        reqs = [r for _, r in nxt]
        seg += 1
    report_counts(counts, plan)


#: Block-size trials open when the steady segments began (tools report: a trial that locks
#: during them still means the steady timings span layout switches).
_STEADY_OPEN_TRIALS = set()


def _note_open_trials():
    from matchedfilter import time_domain as _td
    _STEADY_OPEN_TRIALS.update(_td._BLOCK_TRIALS.open_keys())


def run_device(device, tops, args, seed):
    rng = np.random.default_rng(seed)
    S = args.seg_samples
    a0 = int(args.start_pad * RATE)
    a1 = S - int(args.end_pad * RATE)
    analysed = (a1 - a0) / RATE
    profiles = np.load(args.profiles) if args.profiles else None
    bs = max(1, int(round(args.asym_bin_width * RATE)))
    half = (args.asym_num_bins // 2) * bs
    first, steady = Timer(), Timer()
    results = {}
    counts = defaultdict(int)
    folded = []
    # --roofline: work counted over each top's steady segments (matchedfilter._roofline).
    roof = dict(work=_roofline.Work(), ticks=defaultdict(int), problems=[], ctx=None) \
        if args.roofline else None

    def one_top(top):
        # Each top template in its own scope: its segment loop (a generator under
        # LADDER_FOLD_TOPS) keeps its own banks, buffers and data.
            # The top template's own output profile |h|^2/S (tools/ladder_profiles.py) colours its
            # reference series and is the fine banks' reference, as in pycbc_inspiral_fir; without
            # it a generic inspiral-like profile stands in (and the gates refine far more).
            if profiles is not None:
                w, df = profiles["top_%d" % top["top"]], float(profiles["delta_f"])
            else:
                w, df = profile(), DF
            amp = np.sqrt(w)
            t0 = time.perf_counter()
            # Each middle filter's scale is folded into its taps, as pycbc does: here the scale that
            # makes noise unit variance per quadrature, measured once on an untimed series.
            probe = TimeDomainFilterBank(top["mid_taps"], tap_counts=top["mid_counts"], engine="corr")
            x = analytic_series(rng, 1 << 18, amp, df)
            y = probe.correlate_series(x)[:, 1 << 15:-(1 << 15)]
            scale = 1.0 / np.sqrt(np.mean(np.abs(y) ** 2, axis=1) / 2)
            mid = TimeDomainFilterBank(top["mid_taps"] * scale[:, None].astype(np.float32),
                                       tap_counts=top["mid_counts"], engine="corr", device=device)
            # The fine taps are scaled likewise against a middle series, so a fine output in noise
            # is an SNR (pycbc gets this from the reference series' normalisation).
            xm = probe.correlate_series(analytic_series(rng, 1 << 18, amp, df))
            xm = xm * scale[:, None].astype(np.float32)
            fine = []
            for row, (m, taps, c) in enumerate(top["fine"]):
                pf = TimeDomainFilterBank(taps, tap_counts=c, engine="corr")
                yf = pf.correlate_series(xm[row])[:, 1 << 15:-(1 << 15)]
                taps = taps / np.sqrt(np.mean(np.abs(yf) ** 2, axis=1) / 2)[:, None].astype(np.float32)
                b = TimeDomainFilterBank(taps, tap_counts=c, engine="hier", threshold=args.threshold,
                                         false_dismissal=args.fd, device=device,
                                         binsize=int(args.peak_window * RATE),
                                         fft_lengths=[args.fft_length] if args.fft_length else None)
                b.set_reference(w, delta_f=df)
                fine.append((m, b))
            # The middle output in device memory, reused every segment (as a pipeline would):
            # written in place by the middle stage and read in place by the fine banks.
            mid_out = {ifo: mid.empty_shared((len(top["mid_counts"]), S)) for ifo in ("H1", "L1")}
            seg_plan = SegmentPlan()
            first.add("prep", time.perf_counter() - t0)
            fine_banks = [b for _, b in fine]
            rsnap = {}

            def roof_snap(key):
                if roof is not None:
                    rsnap[key] = _roofline.snapshot([mid], fine_banks)

            def roof_close():
                """This top's steady work: middle from rsnap['mid'], fine from rsnap['fine']."""
                if roof is None:
                    return
                if "mid" not in rsnap or "fine" not in rsnap:
                    roof["problems"].append("top %d: no steady span (segments <= warmup?)" % top["top"])
                    return
                after = _roofline.snapshot([mid], fine_banks)
                _roofline.middle_work(roof["work"], rsnap["mid"], after, [mid])
                t = _roofline.fine_work(roof["work"], rsnap["fine"], after, fine_banks, device,
                                        binsize=int(args.peak_window * RATE),
                                        problems=roof["problems"])
                for k, v in t.items():
                    roof["ticks"][k] += v
                roof["ctx"] = roof["ctx"] or _roofline.gpu_context(fine_banks)
            def followups(seg, ser, mids, fine_out):
                """A segment's fine results: record them, and return its follow-up jobs."""
                if roof is not None and seg >= args.warmup:
                    jobs = followups_of(seg, ser, mids, fine_out)
                    _roofline.followup_work(roof["work"], jobs[0])
                    return jobs
                return followups_of(seg, ser, mids, fine_out)

            def followups_of(seg, ser, mids, fine_out):
                fine_res = iter(fine_out)
                asym_jobs, asym_keys = [], []
                for row, (m, b) in enumerate(fine):
                    trig = {}
                    for ifo in ser:
                        r = next(fine_res)
                        trig[ifo] = r
                        results[(top["top"], seg, m, ifo, "fine")] = r
                        counts["fine_triggers"] += len(r.snr)
                    for ifo, other in (("H1", "L1"), ("L1", "H1")):
                        r = trig[ifo]
                        keep = np.flatnonzero(np.abs(r.snr) >= args.asym_threshold)
                        keep = keep[np.argsort(-np.abs(r.snr[keep]), kind="stable")]
                        used = set()
                        for i in keep:
                            sec = int(r.sample_indices[i] // int(RATE))
                            if sec in used:
                                continue
                            used.add(sec)
                            c0 = int(r.sample_indices[i])
                            asym_jobs.append((b, mids[other][row],
                                              dict(windows=slice(max(0, c0 - half), min(S, c0 + half)),
                                                   binsize=bs, threshold=0.0,
                                                   template_index=int(r.template_indices[i]))))
                            asym_keys.append((top["top"], seg, m, other, "asym", c0, int(r.template_indices[i])))
                return asym_jobs, asym_keys

            def submit_followups(asym_jobs, tm, wait=True):
                """The segment's follow-ups, batched like the fine stage (--no-batch: one call
                each); wait=False returns futures."""
                t = time.perf_counter()
                if args.no_batch:
                    asym_out = [b.filter_series(x, **kw) for b, x, kw in asym_jobs]
                else:
                    asym_out = TimeDomainFilterBank.filter_series_many(asym_jobs, wait=wait)
                if asym_jobs:
                    tm.add("asym", time.perf_counter() - t)
                return asym_out

            def collect_followups(asym_keys, asym_out, tm):
                t = time.perf_counter()
                for k, fr in zip(asym_keys, asym_out):
                    results[k] = fr.result() if hasattr(fr, "result") else fr
                if asym_keys:
                    tm.add("asym", time.perf_counter() - t, n=0)
                counts["asym_calls"] += len(asym_keys)

            def finish(seg, ser, mids, fine_out, tm, fu=None):
                """A segment's fine results: record them and run its follow-ups -- or, with fu
                (SegmentPlan follow-ups, [(job, rank, c0, ti, result)]), record those."""
                jobs, keys = followups(seg, ser, mids, fine_out)
                if fu is None:
                    collect_followups(keys, submit_followups(jobs, tm), tm)
                    return
                ifos = list(ser)
                got = {}
                for j, rank, c0, ti, fr in fu:
                    row, other = j // len(ifos), ifos[(j % len(ifos)) ^ 1]
                    got[(top["top"], seg, fine[row][0], other, "asym", c0, ti)] = fr
                if set(got) != set(keys):
                    raise RuntimeError("device follow-ups differ from the host rule: %d vs %d keys"
                                       % (len(got), len(keys)))
                results.update(got)
                counts["asym_calls"] += len(got)

            def followup_spec(ser):
                from matchedfilter.time_domain import FollowUp
                n = len(ser)
                return FollowUp(pairs=[j ^ 1 for j in range(len(fine) * n)],
                                threshold=args.asym_threshold, dedupe=int(RATE), half=half,
                                binsize=bs)
            # --pregen draws every segment's data up front, in the same order (identical data):
            # the bench's own generation (~0.1 s a segment) then stays off the device's timeline.
            def draw():
                # --shared-input: the producer writes into the middle bank's device-shared
                # memory (empty_shared), as a search can whiten into it: the middle stage then
                # reads the series in place instead of copying it to the device every call.
                return {ifo: analytic_series(rng, S, amp, df,
                                             out=mid.empty_shared((S,)) if args.shared_input
                                             else None) for ifo in ("H1", "L1")}
            pregen = [draw() for _ in range(args.segments)] if args.pregen else None

            def new_series():
                return pregen.pop(0) if pregen else draw()
            next_ser = new_series()
            if args.pipeline:
                # The device is fed continuously: segment k's middle and fine stages are enqueued
                # back to back (the fine banks read the middle output on the device, ordered there),
                # and segment k-1's results and follow-ups are collected while the device works on
                # k. Two middle buffers per detector, so k's middle never overwrites what k-1's
                # follow-ups read. Stage times here are host-side; "segment" is the comparable one.
                # Order within an iteration: k's middle is enqueued; k-1's fine results are read
                # (done by now) and its follow-ups enqueued; then k's fine stage. The follow-ups
                # run ahead of it on the same queues, so collecting them waits for them alone and
                # not for k's fine stage, and the host's remaining work (recording results, k+1's
                # data and middle) overlaps k's fine stage instead of leaving the device idle.
                # --depth segments in flight: segment k's results are collected after k+depth's
                # middle stage is enqueued, so the waits find finished work. depth+1 middle
                # buffers per detector: k's middle never overwrites what an uncollected
                # segment's fine stage or follow-ups read.
                depth = max(1, args.depth)
                bufs = [mid_out] + [{ifo: mid.empty_shared((len(top["mid_counts"]), S))
                                     for ifo in ("H1", "L1")} for _ in range(depth)]
                from collections import deque
                inflight = deque()
                prof = None
                if os.environ.get("LADDER_PROFILE"):  # cProfile of the steady iterations only
                    import cProfile
                    prof = cProfile.Profile()
                sampler = GpuSampler()
                sampler.start()
                for seg in range(args.segments + depth):
                    sampler.on = args.warmup <= seg
                    if seg == args.warmup:
                        _note_open_trials()
                        roof_snap("mid")
                        if args.warmup == 0:
                            roof_snap("fine")
                    profiled = prof is not None and args.warmup <= seg < args.segments
                    if profiled:
                        prof.enable()
                    t_seg = time.perf_counter()
                    c_seg = time.thread_time()
                    if seg < args.segments:
                        tm = first if seg < args.warmup else steady
                        ser, next_ser = next_ser, None
                        out = bufs[seg % (depth + 1)]
                        t = time.perf_counter()
                        mids = {ifo: mid.correlate_series(
                            ser[ifo], windows=slice(max(0, a0 - args.pad), min(S, a1 + args.pad)),
                            out=out[ifo], wait=False) for ifo in ser}
                        tm.add("middle", time.perf_counter() - t)
                    asym = None
                    pending = (inflight.popleft() if len(inflight) >= depth
                               or (seg >= args.segments and inflight) else None)
                    if pending is not None:
                        p_seg, p_ser, p_mids, p_futures, p_tm = pending
                        t = time.perf_counter()
                        p_out = [f.result() for f in p_futures]
                        p_tm.add("fine", time.perf_counter() - t)
                        if p_seg == args.warmup - 1:
                            roof_snap("fine")    # the warmup's fine work is all collected
                        a_jobs, a_keys = followups(p_seg, p_ser, p_mids, p_out)
                        asym = (a_keys, submit_followups(a_jobs, p_tm, wait=False), p_tm)
                    if seg < args.segments:
                        jobs = [(b, mids[ifo][row], dict(windows=slice(a0, a1)))
                                for row, (m, b) in enumerate(fine) for ifo in ser]
                        t = time.perf_counter()
                        futures = TimeDomainFilterBank.filter_series_many(jobs, wait=False)
                        tm.add("fine", time.perf_counter() - t)
                    if asym is not None:
                        collect_followups(*asym)
                    if seg < args.segments:
                        inflight.append((seg, ser, mids, futures, tm))
                    elapsed = time.perf_counter() - t_seg
                    if seg < args.segments:
                        tm.add("segment", elapsed)
                        t = time.perf_counter()
                        if seg + 1 < args.segments:   # data for k+1, untimed as everywhere here
                            next_ser = new_series()
                    else:
                        tm.add("segment", elapsed)    # the last collection belongs to the last segment
                    # "wall": the whole iteration, the bench's data generation included -- what
                    # the device sees between segments (device busy = device time / wall).
                    (tm if seg < args.segments else steady).add("wall", time.perf_counter() - t_seg, n=0)
                    # "cpu": the host thread's CPU time over the same span. wall - cpu is time the
                    # host spent waiting (on the device, or descheduled).
                    (tm if seg < args.segments else steady).add("cpu", time.thread_time() - c_seg, n=0)
                    if profiled:
                        prof.disable()
                sampler.stop()
                counts["gpu_sampler"] = sampler.report()
                roof_close()
                if prof is not None:
                    prof.dump_stats(os.environ["LADDER_PROFILE"])
                return
            prof = None
            if os.environ.get("LADDER_PROFILE"):      # cProfile of the steady segments only
                import cProfile
                prof = cProfile.Profile()
            def seg_loop(fold):
                """The batched segment loop. It yields each segment's fine-stage request
                (jobs, prelude, prelude key, follow-up spec) and is sent (fine results,
                follow-ups): run here (run_request), or with every top's request of the
                segment folded into one SegmentPlan run (LADDER_FOLD_TOPS)."""
                nonlocal next_ser
                bsampler = GpuSampler()                # device busy over the steady segments
                bsampler.start()
                # LADDER_INFLIGHT: two segment graphs in flight (SegmentPlan.submit): segment k
                # is launched, then k-1 is collected while the device runs k. Double-buffered
                # middle input and output; one SegmentPlan per buffer, on its own slot half.
                inflight = bool(os.environ.get("LADDER_INFLIGHT") and os.environ.get("LADDER_REPLAY")
                                and os.environ.get("LADDER_GRAPH_MIDDLE") and not fold)
                if inflight:
                    plans2 = [SegmentPlan(slot_half=0), SegmentPlan(slot_half=1)]
                    outs2 = [mid_out, {ifo: mid.empty_shared((len(top["mid_counts"]), S))
                                       for ifo in ("H1", "L1")}]
                    ins2 = [{ifo: mid.empty_shared((S,)) for ifo in ("H1", "L1")} for _ in range(2)]
                pending = None

                def collect(pend):
                    pseg, pser, pmids, handle, ptm = pend
                    fo, ff = handle.result()
                    finish(pseg, pser, pmids, fo, ptm, fu=ff)
                for seg in range(args.segments):
                    tm = first if seg < args.warmup else steady
                    bsampler.mark(args.warmup <= seg)
                    if seg == args.warmup:
                        _note_open_trials()
                    if seg == args.warmup and not fold:
                        roof_snap("mid")             # the middle's work is counted at submit
                        if not inflight:
                            roof_snap("fine")
                    if seg == args.warmup and os.environ.get("LADDER_GC_FREEZE"):
                        # What an application does after setup: move the setup heap out of the
                        # cyclic collector's view (a full collection of it measured ~11 ms here).
                        import gc
                        gc.collect()
                        gc.freeze()
                    if prof is not None and tm is steady:
                        prof.enable()
                    t_seg = time.perf_counter()
                    c_seg = time.thread_time()          # host CPU per segment, as --pipeline
                    ser = next_ser
                    next_ser = None
                    mids = {}
                    graph_middle = (os.environ.get("LADDER_REPLAY")
                                    and os.environ.get("LADDER_GRAPH_MIDDLE"))
                    if graph_middle:
                        # The middle stage joins the segment graph (SegmentPlan prelude): its input in
                        # device-visible memory the host rewrites each segment, read in place.
                        if inflight:
                            m_in, m_out = ins2[seg % 2], outs2[seg % 2]
                        else:
                            if top.get("_mid_in") is None:
                                top["_mid_in"] = {ifo: mid.empty_shared((S,)) for ifo in ("H1", "L1")}
                            m_in, m_out = top["_mid_in"], mid_out
                        t = time.perf_counter()
                        for ifo in ser:
                            m_in[ifo][:] = ser[ifo]
                            mids[ifo] = m_out[ifo]
                        tm.add("middle", time.perf_counter() - t)

                        def prelude(ser=ser, m_in=m_in, m_out=m_out):
                            for ifo in ser:
                                mid.correlate_series(m_in[ifo],
                                                     windows=slice(max(0, a0 - args.pad), min(S, a1 + args.pad)),
                                                     out=m_out[ifo], wait=False)
                    for ifo in (() if graph_middle else ser):
                        t = time.perf_counter()
                        mids[ifo] = mid.correlate_series(ser[ifo], windows=slice(max(0, a0 - args.pad),
                                                                                 min(S, a1 + args.pad)),
                                                         out=mid_out[ifo])
                        tm.add("middle", time.perf_counter() - t)
                    # The fine stage of a segment: every bank on its middle series, both detectors.
                    # Batched (default), the library sees the whole segment in one call.
                    jobs = [(b, mids[ifo][row], dict(windows=slice(a0, a1)))
                            for row, (m, b) in enumerate(fine) for ifo in ser]
                    t = time.perf_counter()
                    fu = None
                    if args.no_batch:
                        fine_out = [b.filter_series(x, **kw) for b, x, kw in jobs]
                    elif args.overlap and seg + 1 < args.segments:
                        # Submit, prepare the next segment's data on the host while the device works
                        # (untimed, as data setup is), then collect: a busy device keeps its clock up.
                        futures = TimeDomainFilterBank.filter_series_many(jobs, wait=False)
                        submit = time.perf_counter() - t
                        next_ser = new_series()
                        t = time.perf_counter() - submit
                        fine_out = [f.result() for f in futures]
                    else:
                        # SegmentPlan replay (LADDER_REPLAY=1): with two segments in flight
                        # (LADDER_GRAPH_MIDDLE=1 LADDER_INFLIGHT=1) it beats --pipeline on Vulkan.
                        fu = None
                        spec = (followup_spec(ser) if os.environ.get("LADDER_REPLAY")
                                and os.environ.get("LADDER_DEVICE_FOLLOWUPS") else None)
                        if inflight:
                            from matchedfilter.time_domain import FollowUp
                            spec = spec or FollowUp(pairs=[j ^ 1 for j in range(len(jobs))],
                                                    threshold=args.asym_threshold, dedupe=int(RATE),
                                                    half=half, binsize=bs)
                            handle = plans2[seg % 2].submit(jobs, prelude=prelude,
                                                            prelude_key=("middle", top["top"], seg % 2),
                                                            followup=spec)
                            if pending is not None:
                                collect(pending)
                            if seg == args.warmup:
                                # The fine work is counted when collected: the warmup's last
                                # segment just was, so the span holds the steady segments'.
                                roof_snap("fine")
                            pending = (seg, ser, mids, handle, tm)
                            tm.add("fine", time.perf_counter() - t)
                            tm.add("segment", time.perf_counter() - t_seg)
                            tm.add("wall", time.perf_counter() - t_seg, n=0)
                            tm.add("cpu", time.thread_time() - c_seg, n=0)
                            if next_ser is None and seg + 1 < args.segments:
                                next_ser = new_series()
                            continue
                        fine_out, fu = yield (jobs, prelude if graph_middle else None,
                                              ("middle", top["top"]) if graph_middle else None, spec)
                        if os.environ.get("LADDER_VERIFY_REPLAY"):
                            again = TimeDomainFilterBank.filter_series_many(jobs)
                            bad = sum(not (np.array_equal(a.sample_indices, b.sample_indices)
                                           and np.array_equal(a.snr, b.snr)) for a, b in zip(fine_out, again))
                            in_trial = sum(getattr(g.plan, "_chain_trial", None) is not None
                                           for _, bk in fine for g in bk._groups)
                            print("verify replay seg %d: replays %d, mismatched jobs %d, peaks %d, plans in trial %d"
                                  % (seg, seg_plan.replays, bad, sum(len(a.snr) for a in fine_out), in_trial),
                                  flush=True)
                    if not fold:
                        tm.add("fine", time.perf_counter() - t)
                    finish(seg, ser, mids, fine_out, tm, fu=fu)
                    if not fold:
                        tm.add("segment", time.perf_counter() - t_seg)
                        tm.add("wall", time.perf_counter() - t_seg, n=0)
                        tm.add("cpu", time.thread_time() - c_seg, n=0)
                    if prof is not None and tm is steady:
                        prof.disable()
                        prof.dump_stats(os.environ["LADDER_PROFILE"])
                    if next_ser is None and seg + 1 < args.segments:
                        next_ser = new_series()
                if pending is not None:              # the last segment in flight
                    t = time.perf_counter()
                    collect(pending)
                    pending[4].add("segment", time.perf_counter() - t, n=0)
                bsampler.stop()
                bu = bsampler.busy_union()
                if bu:
                    counts["gpu_busy_union"] = bu
                if bsampler.samples:
                    counts["gpu_sampler"] = bsampler.report()
                # A Vulkan segment replay advances the fine plans' work counters as the calls
                # would (_vkcompute.read_dispatch_sparse); the CUDA graph does not yet.
                rctx = _roofline.gpu_context(fine_banks)
                vk_inflight = (inflight and not fold and rctx is not None
                               and type(rctx).__module__.endswith("_vkcompute"))
                if (fold or inflight) and not vk_inflight:
                    if roof is not None:
                        roof["problems"].append("roofline counting is not wired for "
                                                "LADDER_FOLD_TOPS / LADDER_INFLIGHT")
                else:
                    roof_close()
                report_plan(seg_plan)
                if inflight:
                    for sp in plans2:
                        report_plan(sp)

            def report_plan(seg_plan):
                if os.environ.get("LADDER_REPLAY"):
                    counts["segment_replays"] += seg_plan.replays
                    counts["segment_capture_failures"] += getattr(seg_plan, "capture_failures", 0)
                    for k in ("followups_device", "followups_host", "followups_overflow"):
                        if getattr(seg_plan, k, 0):
                            counts[k] += getattr(seg_plan, k)
                    if getattr(seg_plan, "followup_unsupported", None):
                        print("device follow-ups unsupported:", seg_plan.followup_unsupported, flush=True)

            def run_request(req):
                jobs, prelude, pkey, spec = req
                if os.environ.get("LADDER_REPLAY"):
                    out = seg_plan.run(jobs, prelude=prelude, prelude_key=pkey, followup=spec)
                else:
                    out = TimeDomainFilterBank.filter_series_many(jobs)
                return out if spec is not None else (out, None)

            if os.environ.get("LADDER_FOLD_TOPS") and os.environ.get("LADDER_REPLAY"):
                # Every top's segment k runs as one SegmentPlan request (driven after every top
                # is set up).
                folded.append(seg_loop(True))
                return
            gen = seg_loop(False)
            req = next(gen, None)
            while req is not None:
                try:
                    req = gen.send(run_request(req))
                except StopIteration:
                    break

            if os.environ.get("LADDER_CHAINS"):      # each fine bank's (n, chain) per template group
                from collections import Counter
                ch = Counter()
                for _, b in fine:
                    for g in b._groups:
                        ch[(g.n, getattr(g.plan, "_chain", None))] += len(g.template_indices)
                print("chains (n, chain): templates", dict(sorted(ch.items(), key=str)), flush=True)
                if os.environ.get("LADDER_CHAINS") == "2":   # and every group's gate thresholds
                    for m, b in fine:
                        for gi, g in enumerate(b._groups):
                            gc_ = getattr(g.plan, "_gcal", None)
                            thr = gc_[1][2] if gc_ else None
                            print("gate", m, gi, getattr(g.plan, "_chain", None),
                                  None if thr is None else tuple(float("%.9g" % x) for x in thr),
                                  flush=True)
    for top in tops:
        one_top(top)
    if folded:
        drive_folded(folded, args, first, steady, counts)
        # One folded segment covers every top: the steady time is per folded segment.
    nfine = sum(t["nfine"] for t in tops)
    steady_segments = max(0, args.segments - args.warmup) * len(tops)
    # "segment" is the whole of each segment (the stages together, as the device is fed):
    # the total when present -- the stage timers overlap under --pipeline -- else their sum.
    total = steady.t.get("segment") or sum(v for k, v in steady.t.items() if k != "segment")
    report = dict(
        device=str(device), segments=args.segments, tops=[t["top"] for t in tops], fine_templates=nfine,
        analysed_seconds_per_segment=analysed, first_segment_s=dict(first.t), steady_s=dict(steady.t),
        steady_calls=dict(steady.n), counts=dict(counts),
    )
    if steady.device:
        report["steady_device_ms"] = {k: {l: v for l, v in d.items()} for k, d in steady.device.items()}
    if steady_segments and total > 0:
        # templates-in-real-time: each top's fine templates over its analysed time, both detectors
        work = sum(t["nfine"] for t in tops) / len(tops) * analysed * 2 * steady_segments
        report["templates_in_real_time"] = {k: work / v for k, v in steady.t.items() if v > 0}
        report["templates_in_real_time"]["total"] = work / total
    if roof is not None and steady_segments and total > 0:
        measured = {"middle": steady.t.get("middle"), "followups": steady.t.get("asym")}
        if roof["ticks"]:
            rate = _roofline.cpu_tick_rate()
            measured.update({k: v / rate for k, v in roof["ticks"].items()})
        pk = _roofline.peaks(device, ctx=roof["ctx"])
        rr = _roofline.report(roof["work"], pk, steady_segments, total,
                              {k: v for k, v in measured.items() if v is not None})
        rr["problems"] = roof["problems"]
        rr["measured_note"] = ("measured ms: middle/followups are the ladder's host stage timers "
                               "(enqueue time under --pipeline on a GPU); CPU fine stages are "
                               "engine ticks (forward = run_series minus tiers and refine)")
        report["roofline"] = rr
    return report, results


def compare(ref, got, threshold, margin=0.25):
    """Peaks and SNRs of every call, device against reference.

    SNR differences are relative to max(|snr|, 1): a threshold-0 follow-up reports bins whose
    SNR is ~1e-7, where a relative difference means nothing. A fine-stage peak present on one
    device only is a gate-margin difference when its SNR is within `margin` of the threshold
    (the gates are calibrated against signals, so near-threshold noise peaks may be dismissed
    differently by different chains or rounding); anything louder is a miss.
    """
    worst, calls, margin_only, missed = 0.0, 0, 0, []
    for key, a in ref.items():
        b = got.get(key)
        if b is None:
            continue
        calls += 1
        ka = dict(zip(zip(a.template_indices.tolist(), a.sample_indices.tolist()), a.snr))
        kb = dict(zip(zip(b.template_indices.tolist(), b.sample_indices.tolist()), b.snr))
        for k in set(ka) & set(kb):
            worst = max(worst, abs(ka[k] - kb[k]) / max(abs(ka[k]), 1.0))
        if "fine" in key:
            for name, side, keys in (("reference only", ka, set(ka) - set(kb)),
                                     ("device only", kb, set(kb) - set(ka))):
                for k in keys:
                    if abs(side[k]) < threshold + margin:
                        margin_only += 1
                    else:
                        missed.append((name, key, k, float(abs(side[k]))))
    return dict(calls=calls, max_snr_diff=worst, gate_margin_peaks=margin_only,
                peaks_reference_only=sum(m[0] == "reference only" for m in missed),
                peaks_device_only=sum(m[0] == "device only" for m in missed),
                loudest=sorted(missed, key=lambda m: -m[3])[:5])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bank", required=True)
    p.add_argument("--device", default="cpu")
    p.add_argument("--tops", type=int, default=2, help="top templates, most fine templates first")
    p.add_argument("--pipeline", action="store_true",
                   help="feed the device continuously: enqueue segment k's middle and fine "
                        "stages, collect segment k-1 meanwhile (compare 'segment' times)")
    p.add_argument("--segments", type=int, default=3, help="segments per top (the first --warmup are setup)")
    p.add_argument("--warmup", type=int, default=2,
                   help="segments per top not counted as steady: the first builds plans, the "
                        "second is where chain trials lock (MF_AUTOTUNE), each a one-off")
    p.add_argument("--seg-samples", type=int, default=1 << 20, help="512 s at 2048 Hz")
    p.add_argument("--start-pad", type=float, default=120.0)
    p.add_argument("--end-pad", type=float, default=16.0)
    p.add_argument("--pad", type=int, default=4096, help="middle-series context either side")
    p.add_argument("--threshold", type=float, default=6.0)
    p.add_argument("--fd", type=float, default=1e-3)
    p.add_argument("--peak-window", type=float, default=1.0)
    p.add_argument("--asym-threshold", type=float, default=6.0)
    p.add_argument("--asym-bin-width", type=float, default=0.03)
    p.add_argument("--asym-num-bins", type=int, default=1000)
    p.add_argument("--profiles", default=None,
                   help="per-top reference profiles (.npz from tools/ladder_profiles.py)")
    p.add_argument("--check", default=None, help="also run this device (e.g. cpu) and compare outputs")
    p.add_argument("--fft-length", type=int, default=0,
                   help="pin the fine banks' block size (0: the library chooses). A check compares "
                        "peaks per bin, so it is exact only when both devices block alike")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--out", default=None, help="write the JSON report here")
    p.add_argument("--pure", action="store_true",
                   help="every call on the bank's device (MF_SINGLE_DEVICE=bank): the GPU-only or "
                        "CPU-only path, without the library moving small calls to the other device")
    p.add_argument("--overlap", action="store_true",
                   help="submit each segment's fine stage, prepare the next segment's data while "
                        "the device works, then collect (filter_series_many(wait=False))")
    p.add_argument("--no-batch", action="store_true",
                   help="fine stage as one filter_series call per bank and detector (the old pattern)")
    p.add_argument("--no-pregen", dest="pregen", action="store_false",
                   help="generate each segment's input data inside the loop (the old default). By "
                        "default every segment's data is drawn before the timed loop (same data): "
                        "a search reads its data, and generating it here (~0.1 s a segment) idled "
                        "the device between segments")
    p.add_argument("--shared-input", action="store_true",
                   help="draw each segment's series into the middle bank's device-shared memory "
                        "(TimeDomainFilterBank.empty_shared), which correlate_series reads in "
                        "place; by default the series is ordinary host memory, copied each call")
    p.add_argument("--depth", type=int, default=1,
                   help="--pipeline: segments in flight before one is collected (default 1: 2 "
                        "doubles the slots and recordings in use, which at n=8192 exceeds the "
                        "recording cache)")
    p.add_argument("--roofline", action="store_true",
                   help="count each steady segment's work per stage and report the fraction of "
                        "theoretical throughput (matchedfilter._roofline)")
    p.add_argument("--roofline-out", default=None, help="write the roofline report (JSON) here")
    p.add_argument("--timing", action="store_true",
                   help="device time per kernel label for each stage (sets MF_GPU_TIMING=1)")
    args = p.parse_args()
    import os
    if args.timing:
        os.environ["MF_GPU_TIMING"] = "1"
    if args.pure:
        os.environ["MF_SINGLE_DEVICE"] = "bank"

    tops = load_tops(args.bank, args.tops)
    report, results = run_device(args.device, tops, args, args.seed)
    if args.check:
        ref_report, ref_results = run_device(args.check, tops, args, args.seed)
        report["reference"] = ref_report
        report["check"] = compare(ref_results, results, args.threshold)
    try:
        rev = subprocess.run(["git", "-C", str(Path(__file__).parent), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
    except OSError:
        rev = ""
    report["meta"] = dict(revision=rev, host=platform.node(), bank=str(args.bank),
                          devices=[str(d) for d in mf.devices()], args=vars(args))
    text = json.dumps(report, indent=1, default=float)
    if args.out:
        Path(args.out).write_text(text)
    tirt = report.get("templates_in_real_time", {})
    print(f"{report['device']}: {report['fine_templates']} fine templates, {len(tops)} tops x "
          f"{args.segments} segments; steady " + ", ".join(
              f"{k} {v:.2f}s" for k, v in report["steady_s"].items()) +
          f"; warmup ({args.warmup} segments) {sum(v for k, v in report['first_segment_s'].items() if k != 'segment'):.1f}s")
    if tirt:
        print("  templates-in-real-time: " + ", ".join(f"{k} {v:.3g}" for k, v in tirt.items()))
    print("  calls: " + ", ".join(f"{k} {v}" for k, v in report["steady_calls"].items()) +
          "; " + ", ".join(f"{k} {v}" for k, v in report["counts"].items() if not isinstance(v, dict)))
    gs = report["counts"].get("gpu_sampler")
    if gs:
        print(f"  gpu (sysfs, steady): busy {gs['busy_pct']:.0f}%, sclk mean {gs['sclk_mhz_mean']:.0f} "
              f"MHz (min {gs['sclk_mhz_min']:.0f}, max {gs['sclk_mhz_max']:.0f}), {gs['n']} samples")
    bu = report["counts"].get("gpu_busy_union")
    if bu:
        print(f"  gpu (command-buffer union, steady): busy {bu['busy_pct']:.0f}%: device "
              f"{bu['device_s']:.3f}s of {bu['wall_s']:.3f}s")
    if report["steady_s"].get("wall") and report["steady_s"].get("cpu") is not None:
        w, c = report["steady_s"]["wall"], report["steady_s"]["cpu"]
        print(f"  host: cpu {c:.3f}s of steady wall {w:.3f}s ({100 * c / w:.0f}%)")
    if report.get("steady_device_ms") and report["steady_s"].get("wall"):
        dev = sum(v[1] for d in report["steady_device_ms"].values() for v in d.values()) / 1e3
        print(f"  device busy {100 * dev / report['steady_s']['wall']:.0f}%: device {dev:.3f}s "
              f"of steady wall {report['steady_s']['wall']:.3f}s")
        if _gputime.rejected():
            print(f"  ({_gputime.rejected()} timestamp pairs rejected as impossible)")
    for stage, d in report.get("steady_device_ms", {}).items():
        dev = sum(v[1] for v in d.values())
        print(f"  {stage}: device {dev / 1e3:.3f}s of wall {report['steady_s'][stage]:.3f}s; " +
              ", ".join(f"{l} {v[0]}x {v[1]:.1f}ms" for l, v in sorted(d.items(), key=lambda x: -x[1][1])))
    from matchedfilter import time_domain as _td
    for key in sorted(set(_STEADY_OPEN_TRIALS) - set(_td._BLOCK_TRIALS.unlocked())):
        print(f"  WARNING: block-size trial {key} locked during the steady segments; these "
              "timings span layout switches -- rerun with the same MF_COST_FILE")
    for key in _td._BLOCK_TRIALS.unlocked():
        # The steady segments ran inside a block-size trial: layouts switched between them,
        # so times and roofline counts are not one layout's. The samples are kept in
        # MF_COST_FILE; rerun (or run more segments) until the trial locks.
        print(f"  WARNING: block-size trial {key} not locked yet (samples per rank "
              f"{ {r: len(v) for r, v in _td._BLOCK_TRIALS.state[key]['samples'].items()} }); "
              "these timings span layout switches -- rerun with the same MF_COST_FILE")
    if "roofline" in report:
        print(_roofline.format_report(report["roofline"]))
        if args.roofline_out:
            Path(args.roofline_out).write_text(json.dumps(report["roofline"], indent=1, default=float))
    if "check" in report:
        r = report["reference"]
        print(f"  reference {r['device']}: steady " + ", ".join(f"{k} {v:.2f}s" for k, v in r["steady_s"].items()))
        print("  check: " + json.dumps(report["check"], default=float))


if __name__ == "__main__":
    main()
