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
-> fine taps), the format pycbc reads. The first segment of each top template is reported
separately: it holds plan construction and the bank's block and chain choices.

    python tools/ladder.py --bank BANK.hdf --device gpu:0 --tops 2 --segments 3
    python tools/ladder.py --bank BANK.hdf --device gpu:0 --check cpu      # outputs vs the CPU

Throughput is templates-in-real-time: fine templates x analysed seconds x detectors / time.
"""
import argparse
import json
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

RATE = 2048.0
DF = 1.0 / 16


def profile():
    """Output-power profile on a fine grid: inspiral-like, 20-900 Hz (the fine banks' reference)."""
    f = np.arange(int(RATE / 2 / DF) + 1) * DF
    return np.where((f > 20) & (f < 900), np.maximum(f, 1.0) ** (-7.0 / 3), 0.0)


def analytic_series(rng, S, amp):
    """Analytic Gaussian series of length S, spectrum amp(f), unit variance per quadrature."""
    X = np.fft.fft(rng.standard_normal(S))
    k = np.arange(S // 2)
    X[:S // 2] *= np.interp(k * RATE / S, np.arange(amp.size) * DF, amp)
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
    amp = np.sqrt(profile())
    w = profile()
    bs = max(1, int(round(args.asym_bin_width * RATE)))
    half = (args.asym_num_bins // 2) * bs
    first, steady = Timer(), Timer()
    results = {}
    counts = defaultdict(int)
    for top in tops:
        t0 = time.perf_counter()
        # Each middle filter's scale is folded into its taps, as pycbc does: here the scale that
        # makes noise unit variance per quadrature, measured once on an untimed series.
        probe = TimeDomainFilterBank(top["mid_taps"], tap_counts=top["mid_counts"], engine="corr")
        x = analytic_series(rng, 1 << 18, amp)
        y = probe.correlate_series(x)[:, 1 << 15:-(1 << 15)]
        scale = 1.0 / np.sqrt(np.mean(np.abs(y) ** 2, axis=1) / 2)
        mid = TimeDomainFilterBank(top["mid_taps"] * scale[:, None].astype(np.float32),
                                   tap_counts=top["mid_counts"], engine="corr", device=device)
        # The fine taps are scaled likewise against a middle series, so a fine output in noise
        # is an SNR (pycbc gets this from the reference series' normalisation).
        xm = probe.correlate_series(analytic_series(rng, 1 << 18, amp))
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
            b.set_reference(w, delta_f=DF)
            fine.append((m, b))
        first.add("prep", time.perf_counter() - t0)
        for seg in range(args.segments):
            tm = first if seg == 0 else steady
            ser = {ifo: analytic_series(rng, S, amp) for ifo in ("H1", "L1")}
            mids = {}
            for ifo in ser:
                t = time.perf_counter()
                mids[ifo] = mid.correlate_series(ser[ifo], windows=slice(max(0, a0 - args.pad),
                                                                         min(S, a1 + args.pad)))
                tm.add("middle", time.perf_counter() - t)
            # The fine stage of a segment: every bank on its middle series, both detectors.
            # Batched (default), the library sees the whole segment in one call.
            jobs = [(b, mids[ifo][row], dict(windows=slice(a0, a1)))
                    for row, (m, b) in enumerate(fine) for ifo in ser]
            t = time.perf_counter()
            if args.no_batch:
                fine_out = [b.filter_series(x, **kw) for b, x, kw in jobs]
            else:
                fine_out = TimeDomainFilterBank.filter_series_many(jobs)
            tm.add("fine", time.perf_counter() - t)
            fine_res = iter(fine_out)
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
                        t = time.perf_counter()
                        fr = b.filter_series(mids[other][row], windows=slice(max(0, c0 - half), min(S, c0 + half)),
                                             binsize=bs, threshold=0.0,
                                             template_index=int(r.template_indices[i]))
                        tm.add("asym", time.perf_counter() - t)
                        results[(top["top"], seg, m, other, "asym", c0, int(r.template_indices[i]))] = fr
                        counts["asym_calls"] += 1
    nfine = sum(t["nfine"] for t in tops)
    steady_segments = max(0, args.segments - 1) * len(tops)
    total = sum(steady.t.values())
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
    p.add_argument("--segments", type=int, default=3, help="segments per top (the first is setup)")
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
    p.add_argument("--check", default=None, help="also run this device (e.g. cpu) and compare outputs")
    p.add_argument("--fft-length", type=int, default=0,
                   help="pin the fine banks' block size (0: the library chooses). A check compares "
                        "peaks per bin, so it is exact only when both devices block alike")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--out", default=None, help="write the JSON report here")
    p.add_argument("--no-batch", action="store_true",
                   help="fine stage as one filter_series call per bank and detector (the old pattern)")
    p.add_argument("--timing", action="store_true",
                   help="device time per kernel label for each stage (sets MF_GPU_TIMING=1)")
    args = p.parse_args()
    if args.timing:
        import os
        os.environ["MF_GPU_TIMING"] = "1"

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
          f"; first segment {sum(report['first_segment_s'].values()):.1f}s")
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
