#!/usr/bin/env python3
"""Rebuild the hdev fleet comparison from the preserved search logs."""
import importlib.util
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "pycbc-alpha6-fleet-20260927" / "analyze.py"
spec = importlib.util.spec_from_file_location("alpha6_fleet_analyze", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

HOSTS = ("dev1", "dev2", "dev3", "dev4", "su2", "haswell")
ROOT = Path(__import__("sys").argv[1])
out = {}
for host in HOSTS:
    folder = ROOT / host
    a = sorted(folder.glob("paired-A*.log"))
    b = sorted(folder.glob("paired-B*.log"))
    if len(a) != len(b) or len(a) not in (2, 4):
        raise ValueError(f"missing paired logs for {host}: {len(a)} A, {len(b)} B")
    aa = [module.summarize(p) for p in a]
    bb = [module.summarize(p) for p in b]
    pairs = [x["loop_s"] / y["loop_s"] for x, y in zip(aa, bb)]
    out[host] = {
        "alpha6": aa, "hdev": bb,
        "alpha6_mean_rate": module.DENOMINATOR / statistics.mean(x["loop_s"] for x in aa),
        "hdev_mean_rate": module.DENOMINATOR / statistics.mean(x["loop_s"] for x in bb),
        "speedup": statistics.mean(x["loop_s"] for x in aa) /
                   statistics.mean(x["loop_s"] for x in bb),
        "pair_speedups": pairs,
        "hdev_instrumented": module.summarize(folder / "hdev-profile.log"),
    }

(HERE / "results.json").write_text(json.dumps(out, indent=2) + "\n")

names = list(HOSTS)
sx = lambda p: 230 + (p + 8) * 16
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="390" viewBox="0 0 900 390">',
       '<rect width="900" height="390" fill="white"/>',
       '<text x="25" y="31" font-family="sans-serif" font-size="19" font-weight="bold">hdev 08519ef: paired CPU search results</text>']
for tick in (-5, 0, 5, 10, 15, 20, 25):
    x = sx(tick)
    svg += [f'<line x1="{x}" y1="55" x2="{x}" y2="315" stroke="#d8dee5"/>',
            f'<text x="{x}" y="339" text-anchor="middle" font-family="sans-serif" font-size="12">{tick:+d}%</text>']
for i, h in enumerate(names):
    y = 77 + i * 43
    p = (out[h]["speedup"] - 1) * 100
    low = (min(out[h]["pair_speedups"]) - 1) * 100
    high = (max(out[h]["pair_speedups"]) - 1) * 100
    name = "sugwg-login2" if h == "su2" else "og-node-169 (Haswell)" if h == "haswell" else h
    svg += [f'<text x="205" y="{y+4}" text-anchor="end" font-family="sans-serif" font-size="13">{name}</text>',
            f'<rect x="{min(sx(0),sx(p)):.1f}" y="{y-11}" width="{abs(sx(p)-sx(0)):.1f}" height="22" fill="{"#16877a" if p>=0 else "#c45b4b"}"/>',
            f'<line x1="{sx(low):.1f}" y1="{y}" x2="{sx(high):.1f}" y2="{y}" stroke="#202b3a" stroke-width="2"/>',
            f'<line x1="{sx(low):.1f}" y1="{y-5}" x2="{sx(low):.1f}" y2="{y+5}" stroke="#202b3a"/>',
            f'<line x1="{sx(high):.1f}" y1="{y-5}" x2="{sx(high):.1f}" y2="{y+5}" stroke="#202b3a"/>',
            f'<text x="{sx(p)+(10 if p>=0 else -10):.1f}" y="{y+4}" text-anchor="{"start" if p>=0 else "end"}" font-family="sans-serif" font-size="12">{p:+.1f}%</text>']
svg += ['<text x="230" y="365" font-family="sans-serif" font-size="11">Whiskers: interleaved A/B pair range; Haswell includes one slow hdev run.</text>', '</svg>']
(HERE / "chart.svg").write_text("\n".join(svg) + "\n")
print("\n".join(f"{h}: {out[h]['speedup']:.5f}x" for h in names))
