#!/usr/bin/env python3
"""Rebuild paired PyCBC fleet rates and SVG from archived logs.

Usage: python analyze.py /path/to/unpacked/fleet
"""
import json
import statistics
import sys
from pathlib import Path
from log_parser import DENOMINATOR, summarize

HERE = Path(__file__).resolve().parent
HOSTS = ("dev1", "dev2", "dev3", "dev4", "su2", "haswell")
ROOT = Path(sys.argv[1])


def measure(folder):
    a = sorted(folder.glob("paired-A*.log"))
    b = sorted(folder.glob("paired-B*.log"))
    if len(a) != len(b) or len(a) < 2:
        raise ValueError(f"incomplete A/B log set: {folder}")
    left = [summarize(p) for p in a]
    right = [summarize(p) for p in b]
    ma = statistics.mean(x["loop_s"] for x in left)
    mb = statistics.mean(x["loop_s"] for x in right)
    return {
        "A_runs": left, "B_runs": right,
        "A_rate": DENOMINATOR / ma,
        "B_rate": DENOMINATOR / mb,
        "speedup": ma / mb,
        "pair_speedups": [x["loop_s"] / y["loop_s"] for x, y in zip(left, right)],
        "A_lower_rate": DENOMINATOR / statistics.mean(x["lower_s"] for x in left),
        "B_lower_rate": DENOMINATOR / statistics.mean(x["lower_s"] for x in right),
        "A_lower_s": statistics.mean(x["lower_s"] for x in left),
        "B_lower_s": statistics.mean(x["lower_s"] for x in right),
        "A_upper_s": statistics.mean(x["upper_s"] for x in left),
        "B_upper_s": statistics.mean(x["upper_s"] for x in right),
    }


out = {h: {"vs_alpha6": measure(ROOT / h),
           "vs_old_hdev": measure(ROOT / h / "old-v-new")} for h in HOSTS}
(HERE / "results.json").write_text(json.dumps(out, indent=2) + "\n")

sx = lambda pct: 260 + (pct + 18) * 12.3
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1140" height="410" viewBox="0 0 1140 410">',
       '<rect width="1140" height="410" fill="white"/>',
       '<text x="25" y="31" font-family="sans-serif" font-size="19" font-weight="bold">Updated hdev c38f24f: paired complete PyCBC search</text>',
       '<text x="25" y="52" font-family="sans-serif" font-size="12">Change versus contemporaneous alpha6 (teal) and prior hdev 5e56728 (orange)</text>']
for tick in (-15, -10, 0, 10, 20, 30, 40, 50):
    x = sx(tick)
    svg += [f'<line x1="{x:.1f}" y1="66" x2="{x:.1f}" y2="344" stroke="#dce3e8"/>',
            f'<text x="{x:.1f}" y="364" text-anchor="middle" font-family="sans-serif" font-size="12">{tick:+d}%</text>']
for i, h in enumerate(HOSTS):
    cy = 91 + i * 44
    name = "sugwg-login2" if h == "su2" else "Haswell" if h == "haswell" else h
    svg.append(f'<text x="205" y="{cy+3}" text-anchor="end" font-family="sans-serif" font-size="13">{name}</text>')
    for dy, key, color in ((-8, "vs_alpha6", "#16877a"), (8, "vs_old_hdev", "#c98c43")):
        v = out[h][key]
        pct = (v["speedup"] - 1) * 100
        lo = (min(v["pair_speedups"]) - 1) * 100
        hi = (max(v["pair_speedups"]) - 1) * 100
        y = cy + dy
        svg += [f'<rect x="{min(sx(0),sx(pct)):.1f}" y="{y-6}" width="{abs(sx(pct)-sx(0)):.1f}" height="12" fill="{color}"/>',
                f'<line x1="{sx(lo):.1f}" y1="{y}" x2="{sx(hi):.1f}" y2="{y}" stroke="#202b3a"/>',
                f'<line x1="{sx(lo):.1f}" y1="{y-4}" x2="{sx(lo):.1f}" y2="{y+4}" stroke="#202b3a"/>',
                f'<line x1="{sx(hi):.1f}" y1="{y-4}" x2="{sx(hi):.1f}" y2="{y+4}" stroke="#202b3a"/>',
                f'<text x="{sx(pct)+(7 if pct>=0 else -7):.1f}" y="{y+4}" text-anchor="{"start" if pct>=0 else "end"}" font-family="sans-serif" font-size="11">{pct:+.1f}%</text>']
svg += ['<text x="230" y="390" font-family="sans-serif" font-size="11">Whiskers show the range of interleaved A/B pair ratios.</text>', '</svg>']
(HERE / "chart.svg").write_text("\n".join(svg) + "\n")

alpha = ['<svg xmlns="http://www.w3.org/2000/svg" width="1140" height="390" viewBox="0 0 1140 390">',
         '<rect width="1140" height="390" fill="white"/>',
         '<text x="24" y="32" font-family="sans-serif" font-size="20" font-weight="bold">Updated hdev versus alpha6: complete PyCBC search</text>']
for tick in (-15, -10, 0, 10, 20, 30, 40, 50):
    x = sx(tick)
    alpha += [f'<line x1="{x:.1f}" y1="53" x2="{x:.1f}" y2="317" stroke="#dae1e7"/>',
              f'<text x="{x:.1f}" y="338" text-anchor="middle" font-family="sans-serif" font-size="12">{tick:+d}%</text>']
for i, h in enumerate(HOSTS):
    y = 77 + i * 44
    v = out[h]["vs_alpha6"]
    p = (v["speedup"] - 1) * 100
    lo = (min(v["pair_speedups"]) - 1) * 100
    hi = (max(v["pair_speedups"]) - 1) * 100
    name = "sugwg-login2" if h == "su2" else "Haswell" if h == "haswell" else h
    alpha += [f'<text x="220" y="{y+4}" text-anchor="end" font-family="sans-serif" font-size="13">{name}</text>',
              f'<rect x="{min(sx(0),sx(p)):.1f}" y="{y-11}" width="{abs(sx(p)-sx(0)):.1f}" height="22" fill="{"#16877a" if p>=0 else "#c45b4b"}"/>',
              f'<line x1="{sx(lo):.1f}" y1="{y}" x2="{sx(hi):.1f}" y2="{y}" stroke="#202b3a" stroke-width="2"/>',
              f'<line x1="{sx(lo):.1f}" y1="{y-5}" x2="{sx(lo):.1f}" y2="{y+5}" stroke="#202b3a"/>',
              f'<line x1="{sx(hi):.1f}" y1="{y-5}" x2="{sx(hi):.1f}" y2="{y+5}" stroke="#202b3a"/>',
              f'<text x="{sx(p)+(9 if p>=0 else -9):.1f}" y="{y+4}" text-anchor="{"start" if p>=0 else "end"}" font-family="sans-serif" font-size="12">{p:+.1f}%</text>']
alpha += ['<text x="24" y="375" font-family="sans-serif" font-size="11">Whiskers show the range of interleaved A/B pair ratios.</text>', '</svg>']
(HERE / "alpha6-chart.svg").write_text("\n".join(alpha) + "\n")

# Paired clean runs report lower and upper time separately. Show their
# contribution without mixing in the separately instrumented profile.
cost = ['<svg xmlns="http://www.w3.org/2000/svg" width="1020" height="390" viewBox="0 0 1020 390">',
        '<rect width="1020" height="390" fill="white"/>',
        '<text x="24" y="32" font-family="sans-serif" font-size="19" font-weight="bold">Updated hdev: complete-search steady-loop cost</text>',
        '<text x="24" y="52" font-family="sans-serif" font-size="12">Mean of clean paired new-build runs; four measured segments; seconds</text>']
scale = 20
for tick in range(0, 36, 5):
    x = 240 + tick * scale
    cost += [f'<line x1="{x}" y1="70" x2="{x}" y2="344" stroke="#dce3e8"/>',
             f'<text x="{x}" y="364" text-anchor="middle" font-family="sans-serif" font-size="12">{tick}</text>']
for i, h in enumerate(HOSTS):
    row = out[h]["vs_alpha6"]
    lower, upper = row["B_lower_s"], row["B_upper_s"]
    y = 79 + i * 44
    name = "sugwg-login2" if h == "su2" else "Haswell" if h == "haswell" else h
    cost += [f'<text x="220" y="{y+15}" text-anchor="end" font-family="sans-serif" font-size="13">{name}</text>',
             f'<rect x="240" y="{y}" width="{lower*scale:.1f}" height="20" fill="#2878b5"/>',
             f'<rect x="{240+lower*scale:.1f}" y="{y}" width="{upper*scale:.1f}" height="20" fill="#e89531"/>',
             f'<text x="{247+(lower+upper)*scale:.1f}" y="{y+15}" font-family="sans-serif" font-size="12">{lower:.1f} + {upper:.1f} s</text>']
cost += ['<text x="240" y="384" font-family="sans-serif" font-size="12" fill="#2878b5">■ Lower filter</text>',
         '<text x="390" y="384" font-family="sans-serif" font-size="12" fill="#e89531">■ Upper stage</text>', '</svg>']
(HERE / "cost-breakdown.svg").write_text("\n".join(cost) + "\n")

for h in HOSTS:
    a, b = out[h]["vs_alpha6"], out[h]["vs_old_hdev"]
    print(f"{h:8s} alpha6 {a['A_rate']/1000:7.1f}k  new {a['B_rate']/1000:7.1f}k  "
          f"vs alpha6 {a['speedup']:.3f}x  vs old hdev {b['speedup']:.3f}x")
