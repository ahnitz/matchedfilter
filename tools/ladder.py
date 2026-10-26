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


def real_series(rng, S, amp, df=DF, out=None):
    """Real Gaussian series of length S, spectrum amp(f), unit variance: the top filter's
    output in a real-real-complex hierarchy (complex, quadrature final taps), where the top
    and middle filters are real and only the final filters make the complex SNR."""
    X = np.fft.rfft(rng.standard_normal(S))
    X *= np.interp(np.arange(X.size) * RATE / S, np.arange(amp.size) * df, amp)
    x = np.fft.irfft(X, S)
    x /= np.sqrt(np.mean(x ** 2))
    if out is not None:
        out[:] = x
        return out
    return x.astype(np.float32)


def source_series(top, rng, S, amp, df=DF, out=None):
    """The middle stage's input for this top: real for a bank whose final taps are complex
    (quadrature), else analytic as the all-real hierarchy feeds it."""
    return (real_series if top["quadrature"] else analytic_series)(rng, S, amp, df, out=out)


def pack_real_pairs(taps, counts):
    """Two real filters as one complex filter, h_a - i h_b, each placed so its own centre
    tap is the packed filter's centre (offset c//2 - c_i//2): correlated with a real series
    it gives out_a + i out_b, exactly each filter's output (as pycbc_inspiral_fir packs its
    middle filters for a bank with complex final taps). Returns (packed taps, counts)."""
    n = len(counts)
    npair = (n + 1) // 2
    pc = np.array([int(max(counts[2 * q:2 * q + 2])) for q in range(npair)], dtype=np.int64)
    out = np.zeros((npair, int(pc.max())), dtype=np.complex64)
    for r in range(n):
        q, lane = divmod(r, 2)
        c = int(counts[r])
        o = int(pc[q]) // 2 - c // 2
        out[q, o:o + c] += (1.0 if lane == 0 else -1j) * taps[r, :c]
    return out, pc


class _Lanes:
    """Rows of a packed middle output: row r is lane r % 2 (real, imaginary) of pair r // 2,
    a strided real series the fine banks read in place."""

    def __init__(self, out):
        self.out = out

    def __getitem__(self, r):
        row = self.out[r // 2]
        return row.real if r % 2 == 0 else row.imag


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
                t = fg["taps"][:, :int(c.max())]
                # Complex final taps: quadrature filters (real-real-complex hierarchy).
                fine.append((int(m), t.astype(np.complex64 if np.iscomplexobj(t) else np.float32), c))
            out.append(dict(top=tid, mid_taps=g["taps"][:][order].astype(np.float32),
                            mid_counts=counts[order], mids=mids, fine=fine, nfine=nfine,
                            quadrature=any(np.iscomplexobj(t) for _, t, _ in fine)))
    return out


class Timer:
    """Wall time per stage and, with --timing, device time per stage and kernel label."""

    def __init__(self):
        self.t = defaultdict(float)
        self.n = defaultdict(int)
        self.samples = defaultdict(list)        # each add's seconds: a stall shows as one
        self.device = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))

    def add(self, key, dt, n=1):
        self.t[key] += dt
        self.n[key] += n
        self.samples[key].append(float(dt))
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


#: Joint trials (block size, chains, screen) open when the steady segments began (tools
#: report: a trial that locks during them still means the steady timings span its rounds).
_STEADY_OPEN_TRIALS = set()
_STEADY_CPU_TRIAL_START = None


def _open_trials():
    """Keys of this process's joint trials without a lock."""
    from matchedfilter import _trial
    return sorted(k for k, t in _trial._TRIALS.items() if t.winner is None)


def _note_open_trials():
    global _STEADY_CPU_TRIAL_START
    from matchedfilter import _CPU_TRIAL_WORK
    _STEADY_OPEN_TRIALS.update(_open_trials())
    if _STEADY_CPU_TRIAL_START is None:
        _STEADY_CPU_TRIAL_START = dict(_CPU_TRIAL_WORK)


def run_device(device, tops, args, seed, fine_engine="hier"):
    global _STEADY_CPU_TRIAL_START
    _STEADY_CPU_TRIAL_START = None
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
    # --roofline: work counted over each top's steady segments (matchedfilter._roofline).
    roof = dict(work=_roofline.Work(), ticks=defaultdict(int), problems=[], ctx=None,
                followup_jobs=[], series_len=S) \
        if args.roofline else None

    def one_top(top):
        # Each top template in its own scope: its segment loop keeps its own banks, buffers
        # and data.
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
            x = source_series(top, rng, 1 << 18, amp, df)
            y = probe.correlate_series(x)[:, 1 << 15:-(1 << 15)]
            # Unit variance per quadrature of an analytic middle output; unit variance of a
            # real one (quadrature final taps make the complex SNR from it).
            scale = 1.0 / np.sqrt(np.mean(np.abs(y) ** 2, axis=1) / (1 if top["quadrature"] else 2))
            # Quadrature bank on the CPU: the middle filters run in packed real pairs, as pycbc
            # does (the fine banks read each real series in place as one lane of its pair).
            pack = top["quadrature"] and str(device).startswith("cpu") \
                and os.environ.get("LADDER_PACK_MIDDLE", "1") != "0"
            mtaps = top["mid_taps"] * scale[:, None].astype(np.float32)
            mcounts = top["mid_counts"]
            if pack:
                mtaps, mcounts = pack_real_pairs(mtaps, mcounts)
            mid = TimeDomainFilterBank(mtaps, tap_counts=mcounts, engine="corr", device=device)
            lanes = (lambda o: _Lanes(o)) if pack else (lambda o: o)
            # The fine taps are scaled likewise against a middle series, so a fine output in noise
            # is an SNR (pycbc gets this from the reference series' normalisation).
            xm = probe.correlate_series(source_series(top, rng, 1 << 18, amp, df))
            xm = xm * scale[:, None].astype(np.float32)
            fine = []
            for row, (m, taps, c) in enumerate(top["fine"]):
                pf = TimeDomainFilterBank(taps, tap_counts=c, engine="corr")
                yf = pf.correlate_series(xm[row])[:, 1 << 15:-(1 << 15)]
                taps = taps / np.sqrt(np.mean(np.abs(yf) ** 2, axis=1) / 2)[:, None].astype(np.float32)
                b = TimeDomainFilterBank(taps, tap_counts=c, engine=fine_engine, threshold=args.threshold,
                                         false_dismissal=args.fd, device=device,
                                         binsize=int(args.peak_window * RATE),
                                         fft_lengths=[args.fft_length] if args.fft_length else None)
                b.set_reference(w, delta_f=df)
                fine.append((m, b))
            # The middle output in device memory, reused every segment (as a pipeline would):
            # written in place by the middle stage and read in place by the fine banks.
            mid_out = {ifo: mid.empty_shared((mid.n_templates, S)) for ifo in ("H1", "L1")}
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
                    # Counted at the report, outside the timed segments (only the jobs'
                    # banks, windows and kwargs are read).
                    roof["followup_jobs"].append([(b, None, kw) for b, _, kw in jobs[0]])
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

            def finish(seg, ser, mids, fine_out, tm):
                """A segment's fine results: record them and run its follow-ups."""
                jobs, keys = followups(seg, ser, mids, fine_out)
                collect_followups(keys, submit_followups(jobs, tm), tm)

            # --pregen draws every segment's data up front, in the same order (identical data):
            # the bench's own generation (~0.1 s a segment) then stays off the device's timeline.
            def draw():
                # --shared-input: the producer writes into the middle bank's device-shared
                # memory (empty_shared), as a search can whiten into it: the middle stage then
                # reads the series in place instead of copying it to the device every call.
                return {ifo: source_series(top, rng, S, amp, df,
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
                bufs = [mid_out] + [{ifo: mid.empty_shared((mid.n_templates, S))
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
                        mids = {ifo: lanes(mid.correlate_series(
                            ser[ifo], windows=slice(max(0, a0 - args.pad), min(S, a1 + args.pad)),
                            out=out[ifo], wait=False)) for ifo in ser}
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
            def seg_loop():
                """The batched segment loop: each segment's middle stage, then its fine stage
                as one filter_series_many call over every bank and both detectors."""
                nonlocal next_ser
                bsampler = GpuSampler()                # device busy over the steady segments
                bsampler.start()
                for seg in range(args.segments):
                    tm = first if seg < args.warmup else steady
                    bsampler.mark(args.warmup <= seg)
                    if seg == args.warmup:
                        _note_open_trials()
                        roof_snap("mid")             # the middle's work is counted at submit
                        roof_snap("fine")
                    if seg == args.warmup and os.environ.get("LADDER_GC_FREEZE"):
                        # What an application does after setup: move the setup heap out of the
                        # cyclic collector's view (a full collection of it measured ~11 ms here).
                        import gc
                        gc.collect()
                        gc.freeze()
                    if prof is not None and tm is steady:
                        prof.enable()
                    if os.environ.get("MF_AUTOTUNE_LOG", "0") != "0":
                        print("[ladder] segment %d" % seg, file=sys.stderr, flush=True)
                    t_seg = time.perf_counter()
                    c_seg = time.thread_time()          # host CPU per segment, as --pipeline
                    ser = next_ser
                    next_ser = None
                    mids = {}
                    for ifo in ser:
                        t = time.perf_counter()
                        mids[ifo] = mid.correlate_series(ser[ifo], windows=slice(max(0, a0 - args.pad),
                                                                                 min(S, a1 + args.pad)),
                                                         out=mid_out[ifo])
                        mids[ifo] = lanes(mids[ifo])
                        tm.add("middle", time.perf_counter() - t)
                    # The fine stage of a segment: every bank on its middle series, both detectors.
                    # Batched (default), the library sees the whole segment in one call.
                    jobs = [(b, mids[ifo][row], dict(windows=slice(a0, a1)))
                            for row, (m, b) in enumerate(fine) for ifo in ser]
                    t = time.perf_counter()
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
                        fine_out = TimeDomainFilterBank.filter_series_many(jobs)
                    tm.add("fine", time.perf_counter() - t)
                    finish(seg, ser, mids, fine_out, tm)
                    tm.add("segment", time.perf_counter() - t_seg)
                    tm.add("wall", time.perf_counter() - t_seg, n=0)
                    tm.add("cpu", time.thread_time() - c_seg, n=0)
                    if prof is not None and tm is steady:
                        prof.disable()
                        prof.dump_stats(os.environ["LADDER_PROFILE"])
                    if next_ser is None and seg + 1 < args.segments:
                        next_ser = new_series()
                bsampler.stop()
                bu = bsampler.busy_union()
                if bu:
                    counts["gpu_busy_union"] = bu
                if bsampler.samples:
                    counts["gpu_sampler"] = bsampler.report()
                roof_close()

            seg_loop()

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
                            res = g.plan.__dict__.get("_resolved")
                            thr = res.thresholds if res else None
                            print("gate", m, gi, getattr(g.plan, "_chain", None),
                                  None if thr is None else tuple(float("%.9g" % x) for x in thr),
                                  flush=True)
    for top in tops:
        one_top(top)
    nfine = sum(t["nfine"] for t in tops)
    steady_segments = max(0, args.segments - args.warmup) * len(tops)
    # "segment" is the whole of each segment (the stages together, as the device is fed):
    # the total when present -- the stage timers overlap under --pipeline -- else their sum.
    total = steady.t.get("segment") or sum(v for k, v in steady.t.items() if k != "segment")
    report = dict(
        device=str(device), segments=args.segments, tops=[t["top"] for t in tops], fine_templates=nfine,
        analysed_seconds_per_segment=analysed, first_segment_s=dict(first.t), steady_s=dict(steady.t),
        steady_samples={k: list(v) for k, v in steady.samples.items()},
        steady_calls=dict(steady.n), counts=dict(counts),
    )
    from matchedfilter import _CPU_TRIAL_WORK
    if _STEADY_CPU_TRIAL_START is not None:
        report["cpu_trial_work_in_steady"] = {
            k: _CPU_TRIAL_WORK[k] - v for k, v in _STEADY_CPU_TRIAL_START.items()}
        report["steady_valid"] = report["cpu_trial_work_in_steady"]["calls"] == 0
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
        for jobs in roof["followup_jobs"]:
            _roofline.followup_work(roof["work"], jobs, series_len=roof["series_len"])
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
    # Reference fine peaks and the device's misses per |snr| band above the threshold.
    edges = [threshold + e for e in (0.0, 0.25, 0.5, 1.0, 2.0, 4.0)] + [float("inf")]
    by_snr = [[0, 0] for _ in edges[:-1]]
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
            for k, v in ka.items():
                i = next((j for j in range(len(edges) - 1) if abs(v) < edges[j + 1]), None)
                if i is not None and abs(v) >= edges[0]:
                    by_snr[i][0] += 1
                    by_snr[i][1] += k not in kb
            for name, side, keys in (("reference only", ka, set(ka) - set(kb)),
                                     ("device only", kb, set(kb) - set(ka))):
                other = kb if side is ka else ka
                for k in keys:
                    if abs(side[k]) < threshold + margin:
                        margin_only += 1
                    else:
                        # The other side's nearest peak of the same template: a peak one bin
                        # elects differently shows up as a pair of one-sided peaks.
                        near = min(((abs(s2 - k[1]), s2, float(abs(v)))
                                    for (t2, s2), v in other.items() if t2 == k[0]),
                                   default=None)
                        missed.append((name, key, k, float(abs(side[k])),
                                       near[1:] if near else None))
    return dict(calls=calls, max_snr_diff=worst, gate_margin_peaks=margin_only,
                peaks_reference_only=sum(m[0] == "reference only" for m in missed),
                peaks_device_only=sum(m[0] == "device only" for m in missed),
                missed_by_snr={"%.2f-%.2f" % (edges[i], edges[i + 1]): "%d/%d" % (m, t)
                               for i, (t, m) in enumerate(by_snr)},
                loudest=sorted(missed, key=lambda m: -m[3])[:5],
                device_only=sorted((m for m in missed if m[0] == "device only"),
                                   key=lambda m: -m[3])[:5])


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
    p.add_argument("--check-engine", default="hier", choices=("hier", "flat"),
                   help="the --check run's fine-bank engine: flat is the exact (ungated) filter, "
                        "so the check measures the gates' dismissals; hier compares like with like")
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
        ref_report, ref_results = run_device(args.check, tops, args, args.seed,
                                             fine_engine=args.check_engine)
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
    if report.get("steady_valid") is False:
        print("WARNING: CPU calibration occurred after the steady boundary: "
              + str(report["cpu_trial_work_in_steady"])
              + "; throughput includes tuning, rerun with the same MF_COST_FILE")
    if "total" in tirt:
        # The headline: template throughput through the representative stages.
        print(f"throughput: {tirt['total']:.4g} templates in real time on {report['device']} "
              "(fine templates x analysed seconds x 2 detectors / steady wall)")
    print(f"{report['device']}: {report['fine_templates']} fine templates, {len(tops)} tops x "
          f"{args.segments} segments; steady " + ", ".join(
              f"{k} {v:.2f}s" for k, v in report["steady_s"].items()) +
          f"; warmup ({args.warmup} segments) {sum(v for k, v in report['first_segment_s'].items() if k != 'segment'):.1f}s")
    ss = report.get("steady_samples") or {}
    if ss.get("segment"):
        # Per steady segment: a run whose total is far above median x count holds stalls.
        print("  per steady segment: " + ", ".join(
            "%s median %.3fs max %.3fs" % (k, float(np.median(v)), max(v))
            for k, v in ss.items() if k in ("segment", "fine", "asym", "middle") and v))
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
    from matchedfilter import _trial
    for key in sorted(set(_STEADY_OPEN_TRIALS) - set(_open_trials())):
        print(f"  WARNING: joint trial {key} locked during the steady segments; these "
              "timings include its rounds -- rerun with the same MF_COST_FILE")
    for key in _open_trials():
        # The steady segments ran inside a joint trial: each of its rounds replays a batch on
        # every live arm, so times and roofline counts are not one configuration's. Its rounds
        # are kept in MF_COST_FILE; rerun (or run more segments) until it locks.
        t = _trial._TRIALS[key]
        print(f"  WARNING: joint trial {key} not locked yet ({t.rounds} rounds, live arms "
              f"{t.live()}); these timings include its rounds -- rerun with the same MF_COST_FILE")
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
