#!/usr/bin/env python3
"""Parse a complete five-segment PyCBC FIR search log."""
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


