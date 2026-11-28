#!/usr/bin/env python3
"""Replay captured HierarchicalSearch runs with no-op hooks (or follow-ups), on any device.

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
    python tools/search_bench.py CAPTURE_DIR --device cpu --followups

With --followups, on_peaks makes the follow-ups tools/golden.py records (pycbc_inspiral_fir's:
each channel's three loudest peaks refiltered, template by template, in every other channel
around their samples at threshold 0, and once per leaf every template there at the search's
threshold), so the hooks' share and its compute (hooks_compute) are measured too.

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
    ap.add_argument("--roofline", action="store_true",
                    help="account the timed passes' work against the device's peaks "
                         "(matchedfilter._roofline; one segment = one pass over every capture)")
    ap.add_argument("--limit", type=int, default=0, help="first N tops only")
    ap.add_argument("--json", default=None,
                    help="write the results (throughput, stages, host CPU time, per-label device "
                         "counts and time, roofline, device and kernel ids) to this file")
    ap.add_argument("--followups", action="store_true",
                    help="on_peaks refilters as pycbc_inspiral_fir's follow-ups do "
                         "(tools/golden.py's follow-up hook) instead of doing nothing")
    ap.add_argument("--peaks", default=None,
                    help="also save every leaf's peaks from one extra (untimed) pass to this .npz, "
                         "to compare devices or builds")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.capture, "*.pkl")))
    if a.limit:
        files = files[:a.limit]
    noop = lambda ctx: None
    follow_up = None
    if a.followups:
        from golden import _follow_up
        follow_up = _follow_up(205, 50)
    tot = {"setup_s": 0.0, "steady_s": 0.0, "work": 0.0}
    stage = {}
    setup_stage = {}
    kernels = {}
    from matchedfilter import _gputime as gputime
    from matchedfilter import _roofline as rl
    roof = dict(work=rl.Work(), problems=[], ctx=None, ticks={})
    for f in files:
        rec = pickle.load(open(f, "rb"))
        search, inputs, windows, nt, secs = build(rec, a.device)
        on_peaks = noop
        if follow_up is not None:
            def on_peaks(ctx, threshold=search.threshold):
                ctx.leaf_threshold = threshold
                follow_up(ctx, None)
        t0 = time.perf_counter()
        for _ in range(max(1, a.warmup)):
            search.run(inputs, windows=windows, on_series=noop, on_peaks=on_peaks, on_chunk=noop)
        tot["setup_s"] += time.perf_counter() - t0
        base = dict(search.timings)
        for k, v in base.items():
            setup_stage[k] = setup_stage.get(k, 0.0) + v
        if gputime.enabled():
            gputime.collect(clear=True)
            gputime.busy(clear=True)
        mids = [b.bank for b in search._inner.values()]
        fines = list(search._leaf_banks.values())
        before = rl.snapshot(mids, fines) if a.roofline else None
        roots0 = {n: list(v) for n, v in getattr(search, "root_counts", {}).items()}
        t0, c0 = time.perf_counter(), time.process_time()
        for _ in range(a.repeats):
            search.run(inputs, windows=windows, on_series=noop, on_peaks=on_peaks, on_chunk=noop)
        dt = (time.perf_counter() - t0) / a.repeats
        tot["host_cpu_s"] = tot.get("host_cpu_s", 0.0) + (time.process_time() - c0) / a.repeats
        if a.roofline:
            after = rl.snapshot(mids, fines)
            rl.middle_work(roof["work"], before, after, mids)
            rl.root_work(roof["work"], roots0, getattr(search, "root_counts", {}))
            ticks = rl.fine_work(roof["work"], before, after, fines, a.device,
                                 problems=roof["problems"])
            for k, v in ticks.items():
                roof["ticks"][k] = roof["ticks"].get(k, 0) + v
            roof["ctx"] = roof["ctx"] or rl.gpu_context(fines)
        if gputime.enabled():
            # collect first: Vulkan resolves its timestamps, and so records the intervals
            # busy() unites, only when its log is collected
            for lab, (n, ms) in gputime.collect(clear=True).items():
                k = kernels.setdefault(lab, [0, 0.0])
                k[0] += n / a.repeats
                k[1] += ms / 1e3 / a.repeats
            dev_s = gputime.busy(clear=True)[0] / a.repeats
            tot["device_s"] = tot.get("device_s", 0.0) + dev_s
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
    # the setup passes by stage: a plan's per-plan setup is booked in setup, wherever it runs
    print("setup passes by stage: " + ", ".join(
        "%s %.2f s" % (k, setup_stage[k]) for k in ("root", "inner", "leaf", "hooks", "setup")
        if k in setup_stage) + "; leaf + setup %.2f s"
        % (setup_stage.get("leaf", 0.0) + setup_stage.get("setup", 0.0)))
    if stage.get("inner_compute") and stage.get("inner"):
        print("  inner compute fraction (CPU correlation steps in the extension) %.3f s/pass = "
              "%.1f%% of inner" % (stage["inner_compute"], 100 * stage["inner_compute"] / stage["inner"]))
    if stage.get("leaf_compute") and stage.get("leaf"):
        print("  leaf compute fraction (CPU leaf steps in the extension) %.3f s/pass = %.1f%% of leaf"
              % (stage["leaf_compute"], 100 * stage["leaf_compute"] / stage["leaf"]))
    if stage.get("hooks_compute") and stage.get("hooks"):
        print("  hooks compute fraction (the refilters' steps in the extension) %.3f s/pass = "
              "%.1f%% of hooks" % (stage["hooks_compute"], 100 * stage["hooks_compute"] / stage["hooks"]))
    if "device_s" in tot:
        # the union of the device's intervals; the label sums below count each submission
        # (overlapping ones twice, and k: marks again inside their submissions)
        labelled = sum(sec for lab, (_, sec) in kernels.items() if not lab.startswith("k:"))
        print("  device compute fraction (device busy, MF_GPU_TIMING) %.3f s/pass = %.1f%% of "
              "steady wall; submissions' device time summed %.3f s/pass"
              % (tot["device_s"], 100 * tot["device_s"] / s, labelled))
        for lab, (n, sec) in sorted(kernels.items(), key=lambda kv: -kv[1][1])[:12]:
            print("    %-28s %8.0f submissions/pass %8.3f s/pass" % (lab, n, sec))
    r = None
    if a.roofline:
        # Measured per stage, as tools/ladder.py has it: the middle is the search's inner
        # stage timer; the CPU's fine stages are engine ticks over the timed passes.
        measured = {"middle": stage.get("inner", 0.0) * a.repeats} if "inner" in stage else {}
        if roof["ticks"]:
            rate = rl.cpu_tick_rate()
            measured.update({k: v / rate for k, v in roof["ticks"].items()})
        r = rl.report(roof["work"], rl.peaks(a.device, ctx=roof["ctx"]), a.repeats,
                      s * a.repeats, measured)
        r["problems"] = r["problems"] + roof["problems"]
        print(rl.format_report(r))
    if a.json:
        import json
        import platform
        import matchedfilter as mf
        dev = next((d for d in mf.devices() if str(d) == a.device), None)
        out = dict(device=a.device, device_name=getattr(dev, "name", None),
                   backend=getattr(dev, "backend", None), host=platform.node(),
                   tops=len(files), repeats=a.repeats, warmup=a.warmup,
                   steady_s=s, templates_real_time=tot["work"] / s,
                   host_cpu_s=tot.get("host_cpu_s"), setup_s=tot["setup_s"],
                   stages=stage, setup_stages=setup_stage, device_busy_s=tot.get("device_s"),
                   labels={k: dict(per_pass=v[0], seconds=v[1]) for k, v in kernels.items()},
                   roofline=r, env={k: v for k, v in os.environ.items() if k.startswith("MF_")})
        try:
            from matchedfilter._kernel_id import gpu_kernel_id
            out["kernel_id"] = gpu_kernel_id(out["backend"]) if out["backend"] else None
        except Exception as e:                      # recorded, not fatal
            out["kernel_id"] = repr(e)
        with open(a.json, "w") as fh:
            json.dump(out, fh, indent=1, default=float)
    print("  other  %8.3f s/pass  %5.1f%%" % (s - sum(stage.get(k, 0) for k in ("root", "inner", "leaf", "hooks", "setup")),
                                            100 * (s - sum(stage.get(k, 0) for k in ("root", "inner", "leaf", "hooks", "setup"))) / s))


if __name__ == "__main__":
    main()
