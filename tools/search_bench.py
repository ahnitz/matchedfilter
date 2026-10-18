#!/usr/bin/env python3
"""Replay captured HierarchicalSearch runs with no-op hooks, on any device.

A capture (one pickle per top template) holds what pycbc_inspiral_fir hands the search for one
top: the tree (root spectrum, band and profile; middle taps; fine taps and lags), the search's
parameters, each detector's input blocks (one-sided segment spectra, analysed spans, root scales)
and every windows() answer. The hooks are replaced by no-ops -- on_series returns no envelope,
on_peaks and on_chunk do nothing -- so what is measured is the library's share of the search:
root, middle, leaf search and their data movement, with the callbacks free.

The first --warmup passes over a capture (default 2) build the banks, price block sizes, run
the trials and record the GPU's work (setup): a call shape's first run uses the full forward
and its second the band forward its measured refine fraction chose -- a second recording, so
a single setup pass left every recording of the first timed pass to be rebuilt. The next
--repeats passes are timed (steady). Throughput is templates-in-real-time: fine
templates x analysed seconds x detectors / steady seconds per pass.

    python tools/search_bench.py CAPTURE_DIR --device gpu:0
    python tools/search_bench.py CAPTURE_DIR --device cpu --repeats 2

Captures come from pycbc_inspiral_fir run with a sitecustomize hook that pickles
HierarchicalSearch.run's arguments (see the session notes that produced this tool).
"""
import argparse
import glob
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np

# the repo's own python/ last, so a PYTHONPATH build (an A/B variant) wins
sys.path.append(str(Path(__file__).resolve().parent.parent / "python"))


def build(rec, device):
    from matchedfilter.search import BlockInput, HierarchicalSearch, Inner, Leaf, Root

    leaves = []

    def make(d):
        if d["kind"] == "leaf":
            lf = Leaf(d["taps"], d["counts"], lags=d["lags"], node_id=d["id"])
            leaves.append(lf)
            return lf
        kids = [make(c) for c in d["children"]]
        if d["kind"] == "inner":
            return Inner(d["taps"], count=d["count"], children=kids, node_id=d["id"])
        return Root(d["spectrum"], d["band"], children=kids, profile=d["profile"], node_id=d["id"])

    root = make(rec["tree"])
    opts = dict(rec["leaf_options"])
    opts["device"] = None if device == "cpu" else device
    kw = dict(threshold=rec["threshold"], envelope_floor=rec["envelope_floor"], leaf_options=opts,
              context=rec["context"])
    if rec.get("min_pad"):
        kw["min_pad"] = rec["min_pad"]
    search = HierarchicalSearch([root], **kw)
    inputs = {c: BlockInput(v["spectra"], v["valid"],
                            lambda _r, k, s=tuple(v["scales"]): s[k])
              for c, v in rec["inputs"].items()}
    index = {id(lf): i for i, lf in enumerate(leaves)}
    win = rec["windows"]

    def windows(lf, k, c, extra):
        return win.get((index[id(lf)], k, c, extra))

    templates = sum(int(np.asarray(lf.counts).size) for lf in leaves)
    seconds = sum((b - a) / 2048.0 for v in rec["inputs"].values() for a, b in v["valid"])
    return search, inputs, windows, templates, seconds


def save_peaks(files, a):
    """One more pass per capture with a recording on_peaks; peaks keyed top/leaf/chunk/channel."""
    out = {}
    for fi, f in enumerate(files):
        rec = pickle.load(open(f, "rb"))
        search, inputs, windows, _, _ = build(rec, a.device)
        names = {}

        def on_peaks(ctx):
            li = names.setdefault(id(ctx.leaf), len(names))
            for c in ctx.channels:
                p = ctx.peaks[c]
                o = np.lexsort((p.sample_indices, p.template_indices))
                key = "%d_%d_%d_%s" % (fi, li, ctx.chunk, c)
                out[key + "_t"] = np.asarray(p.template_indices)[o]
                out[key + "_s"] = np.asarray(p.sample_indices)[o]
                out[key + "_z"] = np.asarray(p.snr)[o]
        search.run(inputs, windows=windows, on_series=lambda ctx: None, on_peaks=on_peaks)
    np.savez(a.peaks, **out)
    print("saved %d peak arrays to %s" % (len(out) // 3, a.peaks))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("capture")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--warmup", type=int, default=2, help="untimed setup passes per capture")
    ap.add_argument("--limit", type=int, default=0, help="first N tops only")
    ap.add_argument("--peaks", default=None,
                    help="also save every leaf's peaks from one extra (untimed) pass to this .npz, "
                         "to compare devices or builds")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.capture, "*.pkl")))
    if a.limit:
        files = files[:a.limit]
    noop = lambda ctx: None
    tot = {"setup_s": 0.0, "steady_s": 0.0, "work": 0.0}
    stage = {}
    kernels = {}
    from matchedfilter import _gputime as gputime
    for f in files:
        rec = pickle.load(open(f, "rb"))
        search, inputs, windows, nt, secs = build(rec, a.device)
        t0 = time.perf_counter()
        for _ in range(max(1, a.warmup)):
            search.run(inputs, windows=windows, on_series=noop, on_peaks=noop, on_chunk=noop)
        tot["setup_s"] += time.perf_counter() - t0
        base = dict(search.timings)
        if gputime.enabled():
            gputime.collect(clear=True)
            gputime.busy(clear=True)
        t0 = time.perf_counter()
        for _ in range(a.repeats):
            search.run(inputs, windows=windows, on_series=noop, on_peaks=noop, on_chunk=noop)
        dt = (time.perf_counter() - t0) / a.repeats
        if gputime.enabled():
            dev_s = gputime.busy(clear=True)[0] / a.repeats
            tot["device_s"] = tot.get("device_s", 0.0) + dev_s
            for lab, (n, ms) in gputime.collect(clear=True).items():
                k = kernels.setdefault(lab, [0, 0.0])
                k[0] += n / a.repeats
                k[1] += ms / 1e3 / a.repeats
        tot["steady_s"] += dt
        tot["work"] += nt * secs
        for k, v in search.timings.items():
            stage[k] = stage.get(k, 0.0) + (v - base.get(k, 0.0)) / a.repeats
        print("%s: %d fine templates, %.0f detector-s; setup passes %.2f s, steady %.3f s/pass "
              "(%.2f M templates in real time)" % (os.path.basename(f), nt, secs,
                                                    tot["setup_s"], dt, nt * secs / dt / 1e6))
    if a.peaks:
        save_peaks(files, a)
    s = tot["steady_s"]
    print("device %s | %d tops | steady %.3f s/pass, %.2f M templates in real time | setup passes %.1f s"
          % (a.device, len(files), s, tot["work"] / s / 1e6, tot["setup_s"]))
    for k in ("root", "inner", "leaf", "hooks", "setup"):
        if k in stage:
            print("  %-6s %8.3f s/pass  %5.1f%%" % (k, stage[k], 100 * stage[k] / s))
    if "device_s" in tot:
        print("  device busy (MF_GPU_TIMING) %.3f s/pass = %.1f%% of steady wall"
              % (tot["device_s"], 100 * tot["device_s"] / s))
        for lab, (n, sec) in sorted(kernels.items(), key=lambda kv: -kv[1][1])[:12]:
            print("    %-28s %8.0f submissions/pass %8.3f s/pass" % (lab, n, sec))
    print("  other  %8.3f s/pass  %5.1f%%" % (s - sum(stage.get(k, 0) for k in ("root", "inner", "leaf", "hooks", "setup")),
                                            100 * (s - sum(stage.get(k, 0) for k in ("root", "inner", "leaf", "hooks", "setup"))) / s))


if __name__ == "__main__":
    main()
