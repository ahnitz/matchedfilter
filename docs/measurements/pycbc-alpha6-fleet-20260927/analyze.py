#!/usr/bin/env python3
"""Summarize the five-segment PyCBC FIR search and plot alpha fleet results.

Input layout: ROOT/HOST/clean-{1,2,3}.log and ROOT/HOST/native-phase.log.
For dev2, the corrected search launcher logs are source-clean-{1,2,3}.log.
"""
import argparse
import json
import re
from pathlib import Path
from statistics import median

ANALYZE_SECONDS = 376
TEMPLATES = 5883
DENOMINATOR = 4 * TEMPLATES * ANALYZE_SECONDS
HOSTS = ("dev1", "dev2", "dev3", "dev4", "su2", "haswell")


def summarize(path):
    groups = {}
    upper = {}
    upper_parts = {k: 0.0 for k in ("direct", "library", "scale", "norms")}
    phase = {}
    segment = group = count = None
    prof = []
    cycle_snapshots = {}
    for line in path.read_text(errors="replace").splitlines():
        if m := re.search(r"Ratio Batch (\d+)/\d+, (\d+) FIR templates", line):
            group, count = map(int, m.groups())
        if m := re.search(r"Processing Segment (\d+)", line):
            segment = int(m[1])
            prof = []
        if m := re.search(r"batch perf: ([\d.]+) templates s/s", line):
            if segment is not None and group is not None:
                groups[group, segment] = count * ANALYZE_SECONDS / float(m[1])
        if m := re.search(r"Upper segment (\d+) total: ([\d.]+) s", line):
            upper[int(m[1])] = float(m[2])
        if m := re.search(r"Upper segment (\d+) top \d+: direct ([\d.]+) s, library ([\d.]+) s, scale ([\d.]+) s, norms ([\d.]+) s", line):
            if int(m[1]) in (1, 2, 3, 4):
                for key, value in zip(upper_parts, m.groups()[1:]):
                    upper_parts[key] += float(value)
        if m := re.search(r"\[ratio-timing\].*kernel=([\d.]+) s", line):
            if group is not None and segment is not None:
                phase[group, segment] = float(m[1])
        if m := re.search(r"\[prof\] cycles/pair: even=(\d+) .* gate=(\d+) .* refine=(\d+) .* fill=(\d+)", line):
            prof.append(tuple(map(int, m.groups())))
        if m := re.search(r"\[ratio-phase\].* of (\d+) pair-calls triggered", line):
            if prof and group is not None and segment is not None:
                cycle_snapshots[group, segment] = (
                    int(m[1]),
                    [sum(row[i] for row in prof) / len(prof) for i in range(4)],
                )
            prof = []

    lower = sum(value for (group, seg), value in groups.items() if seg in (1, 2, 3, 4))
    upper_s = sum(upper.get(seg, 0) for seg in (1, 2, 3, 4))
    result = {"lower_s": lower, "upper_s": upper_s,
              "loop_s": lower + upper_s,
              "throughput": DENOMINATOR / (lower + upper_s),
              "upper_parts_s": upper_parts,
              "lower_kernel_s": sum(phase.get((group, 4), 0.0) -
                                    phase.get((group, 0), 0.0)
                                    for group in range(1, 69))}
    if len(groups) != 68 * 5 or len(upper) != 5:
        raise ValueError(f"incomplete search log: {path} ({len(groups)} groups, {len(upper)} upper segments)")
    if cycle_snapshots:
        if len(cycle_snapshots) != 68 * 5:
            raise ValueError(f"incomplete native phase profile: {path}")
        cycles = [0.0] * 4
        for group in range(1, 69):
            for seg in range(1, 5):
                pair_now, avg_now = cycle_snapshots[group, seg]
                pair_prev, avg_prev = cycle_snapshots[group, seg - 1]
                for i in range(4):
                    cycles[i] += pair_now * avg_now[i] - pair_prev * avg_prev[i]
        total = sum(cycles)
        result["native_phase_fraction"] = {
            key: value / total for key, value in zip(("coarse", "gate", "refine", "fill"), cycles)
        }
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("--json", type=Path, required=True)
    p.add_argument("--chart", type=Path, required=True)
    a = p.parse_args()
    result = {}
    for host in HOSTS:
        folder = a.root / host
        prefix = "source-clean" if host == "dev2" else "clean"
        clean = [summarize(folder / f"{prefix}-{i}.log") for i in (1, 2, 3)]
        prof = summarize(folder / "native-phase.log")
        result[host] = {
            "clean_repeats": clean,
            "median_throughput": median(v["throughput"] for v in clean),
            "median_loop_s": median(v["loop_s"] for v in clean),
            "profile": prof,
        }
    a.json.parent.mkdir(parents=True, exist_ok=True)
    a.json.write_text(json.dumps(result, indent=2) + "\n")

    import matplotlib.pyplot as plt
    import numpy as np
    names = list(HOSTS)
    y = np.arange(len(names))
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13.0, 5.0),
                                 gridspec_kw={"width_ratios": [1.5, 1]})
    pieces = (
        ("Lower filter kernel", lambda p: p["lower_kernel_s"], "#2878b5"),
        ("Other lower", lambda p: p["lower_s"] - p["lower_kernel_s"], "#83b4d9"),
        ("Upper library", lambda p: p["upper_parts_s"]["library"], "#e89531"),
        ("Upper direct", lambda p: p["upper_parts_s"]["direct"], "#edbd73"),
        ("Other upper", lambda p: p["upper_s"] - p["upper_parts_s"]["library"] - p["upper_parts_s"]["direct"], "#e8d4ae"),
    )
    left = np.zeros(len(names))
    for label, get, color in pieces:
        values = np.array([get(result[h]["profile"]) for h in names])
        ax.barh(y, values, left=left, label=label, color=color, height=.68)
        left += values
    ax.set_yticks(y, names)
    ax.invert_yaxis()
    ax.set_xlabel("Profiled steady-loop time (s), 4 segments")
    ax.set_title("PyCBC wall time by stage")
    ax.legend(loc="upper left", bbox_to_anchor=(0, -.16), ncol=3, fontsize=8)
    ax.grid(axis="x", alpha=.2)
    ax.set_axisbelow(True)

    left = np.zeros(len(names))
    for label, color in (("Coarse FFT/peak", "#2878b5"),
                         ("Gate", "#80c1bb"), ("Refine", "#e89531"),
                         ("Fill", "#b3a3c5")):
        key = label.split()[0].lower()
        values = np.array([100 * result[h]["profile"]["native_phase_fraction"][key]
                           for h in names])
        bx.barh(y, values, left=left, label=label, color=color, height=.68)
        left += values
    bx.set_yticks(y, [""] * len(names))
    bx.invert_yaxis()
    bx.set_xlim(0, 100)
    bx.set_xlabel("Native lower-kernel cycles (%)")
    bx.set_title("Within the lower hierarchy")
    bx.legend(loc="upper left", bbox_to_anchor=(0, -.16), ncol=2, fontsize=8)
    bx.grid(axis="x", alpha=.2)
    bx.set_axisbelow(True)
    fig.suptitle("matchedfilter 0.1.0a6 in the PyCBC FIR search")
    fig.tight_layout()
    a.chart.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.chart, bbox_inches="tight")
    # Matplotlib writes trailing spaces in SVG path data. Keep the committed
    # artifact clean while preserving the rendered geometry.
    a.chart.write_text("\n".join(line.rstrip() for line in
                                 a.chart.read_text().splitlines()) + "\n")


if __name__ == "__main__":
    main()
