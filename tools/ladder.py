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
from matchedfilter.time_domain import SegmentPlan             # noqa: E402

RATE = 2048.0
DF = 1.0 / 16


def profile():
    """Output-power profile on a fine grid: inspiral-like, 20-900 Hz (the fine banks' reference)."""
    f = np.arange(int(RATE / 2 / DF) + 1) * DF
    return np.where((f > 20) & (f < 900), np.maximum(f, 1.0) ** (-7.0 / 3), 0.0)


def analytic_series(rng, S, amp, df=DF):
    """Analytic Gaussian series of length S, spectrum amp(f) (on a grid of spacing df), unit
    variance per quadrature."""
    X = np.fft.fft(rng.standard_normal(S))
    k = np.arange(S // 2)
    X[:S // 2] *= np.interp(k * RATE / S, np.arange(amp.size) * df, amp)
    X[S // 2:] = 0
    x = np.fft.ifft(X)
    x /= np.sqrt(np.mean(np.abs(x) ** 2) / 2)
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


def _timing():
    import os
    return os.environ.get("MF_GPU_TIMING", "0") not in ("", "0")


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
    for top in tops:
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
        def followups(seg, ser, mids, fine_out):
            """A segment's fine results: record them, and return its follow-up jobs."""
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
        next_ser = {ifo: analytic_series(rng, S, amp, df) for ifo in ("H1", "L1")}
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
            bufs = [mid_out, {ifo: mid.empty_shared((len(top["mid_counts"]), S))
                              for ifo in ("H1", "L1")}]
            pending = None
            for seg in range(args.segments + 1):
                t_seg = time.perf_counter()
                if seg < args.segments:
                    tm = first if seg < args.warmup else steady
                    ser, next_ser = next_ser, None
                    out = bufs[seg % 2]
                    t = time.perf_counter()
                    mids = {ifo: mid.correlate_series(
                        ser[ifo], windows=slice(max(0, a0 - args.pad), min(S, a1 + args.pad)),
                        out=out[ifo], wait=False) for ifo in ser}
                    tm.add("middle", time.perf_counter() - t)
                asym = None
                if pending is not None:
                    p_seg, p_ser, p_mids, p_futures, p_tm = pending
                    t = time.perf_counter()
                    p_out = [f.result() for f in p_futures]
                    p_tm.add("fine", time.perf_counter() - t)
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
                pending = (seg, ser, mids, futures, tm) if seg < args.segments else None
                elapsed = time.perf_counter() - t_seg
                if seg < args.segments:
                    tm.add("segment", elapsed)
                    t = time.perf_counter()
                    if seg + 1 < args.segments:   # data for k+1, untimed as everywhere here
                        next_ser = {ifo: analytic_series(rng, S, amp, df) for ifo in ("H1", "L1")}
                else:
                    tm.add("segment", elapsed)    # the last collection belongs to the last segment
            continue
        prof = None
        if os.environ.get("LADDER_PROFILE"):      # cProfile of the steady segments only
            import cProfile
            prof = cProfile.Profile()
        for seg in range(args.segments):
            tm = first if seg < args.warmup else steady
            if prof is not None and tm is steady:
                prof.enable()
            t_seg = time.perf_counter()
            ser = next_ser
            next_ser = None
            mids = {}
            for ifo in ser:
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
            if args.no_batch:
                fine_out = [b.filter_series(x, **kw) for b, x, kw in jobs]
            elif args.overlap and seg + 1 < args.segments:
                # Submit, prepare the next segment's data on the host while the device works
                # (untimed, as data setup is), then collect: a busy device keeps its clock up.
                futures = TimeDomainFilterBank.filter_series_many(jobs, wait=False)
                submit = time.perf_counter() - t
                next_ser = {ifo: analytic_series(rng, S, amp, df) for ifo in ("H1", "L1")}
                t = time.perf_counter() - submit
                fine_out = [f.result() for f in futures]
            else:
                # SegmentPlan replay (LADDER_REPLAY=1, MF_SEGMENT_REPLAY=1) is exact but not
                # faster than the batched path, which is the default.
                fine_out = (seg_plan.run(jobs) if os.environ.get("LADDER_REPLAY")
                            else TimeDomainFilterBank.filter_series_many(jobs))
                if os.environ.get("LADDER_VERIFY_REPLAY"):
                    again = TimeDomainFilterBank.filter_series_many(jobs)
                    bad = sum(not (np.array_equal(a.sample_indices, b.sample_indices)
                                   and np.array_equal(a.snr, b.snr)) for a, b in zip(fine_out, again))
                    in_trial = sum(getattr(g.plan, "_chain_trial", None) is not None
                                   for _, bk in fine for g in bk._groups)
                    print("verify replay seg %d: replays %d, mismatched jobs %d, peaks %d, plans in trial %d"
                          % (seg, seg_plan.replays, bad, sum(len(a.snr) for a in fine_out), in_trial),
                          flush=True)
            tm.add("fine", time.perf_counter() - t)
            finish(seg, ser, mids, fine_out, tm)
            tm.add("segment", time.perf_counter() - t_seg)
            if prof is not None and tm is steady:
                prof.disable()
                prof.dump_stats(os.environ["LADDER_PROFILE"])
            if next_ser is None and seg + 1 < args.segments:
                next_ser = {ifo: analytic_series(rng, S, amp, df) for ifo in ("H1", "L1")}
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
          "; " + ", ".join(f"{k} {v}" for k, v in report["counts"].items()))
    for stage, d in report.get("steady_device_ms", {}).items():
        dev = sum(v[1] for v in d.values())
        print(f"  {stage}: device {dev / 1e3:.3f}s of wall {report['steady_s'][stage]:.3f}s; " +
              ", ".join(f"{l} {v[0]}x {v[1]:.1f}ms" for l, v in sorted(d.items(), key=lambda x: -x[1][1])))
    if "check" in report:
        r = report["reference"]
        print(f"  reference {r['device']}: steady " + ", ".join(f"{k} {v:.2f}s" for k, v in r["steady_s"].items()))
        print("  check: " + json.dumps(report["check"], default=float))


if __name__ == "__main__":
    main()
