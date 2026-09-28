#!/usr/bin/env python3
"""Rebuild the fleet table, plot and JSON from the archived logs.

Usage: analyze.py <logs-root> <out-dir> [baseline-results.json]

Writes results.json, table.md and chart.svg into <out-dir>. Never touches the
committed handoff folder -- analyze.py writes back into its own directory,
which would overwrite the published artifacts.
"""
import json, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from log_parser import DENOMINATOR, summarize

HOSTS = ("dev1", "dev2", "dev3", "dev4", "su2", "haswell")
LABEL = {"su2": "sugwg-login2", "haswell": "Haswell"}
CPU = {"dev1": "Ryzen 9 5950X", "dev2": "Ryzen AI MAX+ 395",
       "dev3": "Ryzen 5 5500U", "dev4": "Core i5-13500H",
       "su2": "Xeon Platinum 8260", "haswell": "Xeon E5-2698 v3"}
# Hosts whose pinned core was time-shared with other users during the run.
# Their absolute rates are real for that condition, not comparable to an
# idle-node rate. Flagged rather than dropped: a loaded shared node is the
# realistic operating environment.
CONTENDED = {}  # this run: Haswell load fell to ~14; runs 24.4-27.6s, uncontended
root, outdir = Path(sys.argv[1]), Path(sys.argv[2])
published = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
outdir.mkdir(parents=True, exist_ok=True)


def measure(folder):
    a = sorted(folder.glob("paired-A*.log")); b = sorted(folder.glob("paired-B*.log"))
    if len(a) != len(b) or len(a) < 2:
        raise ValueError(f"incomplete A/B log set: {folder}")
    L = [summarize(p) for p in a]; R = [summarize(p) for p in b]

    # Identify a machine-condition change WITHIN a variant, never from the
    # A/B ratio itself: a large A/B ratio is exactly what a real speedup
    # looks like, so filtering on it discards genuine wins (it threw out
    # dev4's +30%). A run that differs from the median of its OWN variant
    # by more than 25% did not measure the same machine as its siblings.
    def outliers(runs):
        med = statistics.median(x["loop_s"] for x in runs)
        return {i for i, x in enumerate(runs)
                if not 0.75 <= x["loop_s"] / med <= 1.333}
    bad = outliers(L) | outliers(R)
    keep = [i for i in range(len(L)) if i not in bad]
    if len(keep) < 1:
        raise ValueError(f"no pair measured a stable machine: {folder}")
    L, R = [L[i] for i in keep], [R[i] for i in keep]
    ma = statistics.mean(x["loop_s"] for x in L); mb = statistics.mean(x["loop_s"] for x in R)
    pair = [x["loop_s"] / y["loop_s"] for x, y in zip(L, R)]
    return {"A_rate": DENOMINATOR/ma, "B_rate": DENOMINATOR/mb, "speedup": ma/mb,
            "pair_speedups": pair, "n_pairs": len(pair), "dropped_pairs": len(bad),
            "B_lower_s": statistics.mean(x["lower_s"] for x in R),
            "B_upper_s": statistics.mean(x["upper_s"] for x in R)}


out, missing = {}, []
for h in HOSTS:
    try:
        out[h] = {"vs_alpha6": measure(root/h), "vs_old_hdev": measure(root/h/"old-v-new")}
    except (ValueError, OSError) as e:
        missing.append((h, str(e)[:70]))
(outdir/"results.json").write_text(json.dumps(out, indent=2)+"\n")

# ---- table -------------------------------------------------------------
rows = []
for h in HOSTS:
    if h not in out: continue
    a, o = out[h]["vs_alpha6"], out[h]["vs_old_hdev"]
    pa = published.get(h, {})
    rows.append((LABEL.get(h,h)+(" \u2020" if h in CONTENDED else ""), CPU[h], a["A_rate"]/1e3, a["B_rate"]/1e3,
                 (a["speedup"]-1)*100, (o["speedup"]-1)*100,
                 (pa.get("vs_alpha6",{}).get("speedup",0)-1)*100 if pa else None,
                 (pa.get("vs_old_hdev",{}).get("speedup",0)-1)*100 if pa else None,
                 min(o["pair_speedups"]), max(o["pair_speedups"]), o["n_pairs"],
                 o["dropped_pairs"] + a["dropped_pairs"]))

t = ["| host | CPU | alpha6 kt-s/s | new kt-s/s | vs alpha6 | vs prior `hdev` | published vs prior | pair range (vs prior) |",
     "|---|---|---:|---:|---:|---:|---:|---|"]
for r in rows:
    t.append("| %s | %s | %.1f | %.1f | %+.1f%% | **%+.1f%%** | %s | %.3f–%.3f (n=%d) |"
             % (r[0], r[1], r[2], r[3], r[4], r[5],
                "%+.1f%%" % r[7] if r[7] is not None else "—", r[8], r[9], r[10]))
table = "\n".join(t)
if missing:
    table += "\n\nNot collected: " + "; ".join("%s (%s)" % m for m in missing)
if CONTENDED:
    table += "\n\n" + "\n".join(
        "\u2020 %s measured under contention: %s. Absolute rates are for that "
        "loaded condition; interleaved A/B cancels steady load but not drift."
        % (LABEL.get(k,k), v) for k, v in CONTENDED.items() if k in out)
(outdir/"table.md").write_text(table+"\n")

# ---- plot --------------------------------------------------------------
W, rowh, top = 1180, 52, 108
H = top + rowh*len(rows) + 86
lo_p = min([r[5] for r in rows]+[r[4] for r in rows]+[-8])
hi_p = max([r[5] for r in rows]+[r[4] for r in rows]+[8])
lo_p, hi_p = lo_p-6, hi_p+8
x0, x1 = 330, W-70
sx = lambda p: x0 + (p-lo_p)*(x1-x0)/(hi_p-lo_p)
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="26" y="34" font-family="sans-serif" font-size="20" font-weight="bold">PyCBC fleet: new hdev head c38f24f, paired complete search</text>',
     '<text x="26" y="56" font-family="sans-serif" font-size="12.5" fill="#444">Teal = versus contemporaneous alpha6. Orange = versus prior head c38f24f, the comparison that isolates these three commits.</text>',
     '<text x="26" y="74" font-family="sans-serif" font-size="12.5" fill="#444">Grey caret = the c38f24f re-run measured earlier today (its own vs-prior result). Whiskers span the interleaved pair ratios.</text>']
step = 5 if hi_p-lo_p > 30 else 2
tick = int(lo_p//step*step)
while tick <= hi_p:
    x = sx(tick)
    if x0 <= x <= x1:
        s += [f'<line x1="{x:.1f}" y1="{top-18}" x2="{x:.1f}" y2="{top+rowh*len(rows)-14}" stroke="#e0e6ea"/>',
              f'<text x="{x:.1f}" y="{top+rowh*len(rows)+4}" text-anchor="middle" font-family="sans-serif" font-size="11.5" fill="#555">{tick:+d}%</text>']
    tick += step
s.append(f'<line x1="{sx(0):.1f}" y1="{top-18}" x2="{sx(0):.1f}" y2="{top+rowh*len(rows)-14}" stroke="#9aa5ad" stroke-width="1.5"/>')
for i, r in enumerate(rows):
    cy = top + i*rowh
    s += [f'<text x="222" y="{cy+1}" text-anchor="end" font-family="sans-serif" font-size="13.5" font-weight="600">{r[0]}</text>',
          f'<text x="222" y="{cy+16}" text-anchor="end" font-family="sans-serif" font-size="10.5" fill="#777">{r[1]}</text>']
    for dy, pct, color in ((-9, r[4], "#16877a"), (7, r[5], "#c98c43" if r[5] >= 0 else "#c4514b")):
        y = cy + dy
        s += [f'<rect x="{min(sx(0),sx(pct)):.1f}" y="{y-6}" width="{abs(sx(pct)-sx(0)):.1f}" height="12" fill="{color}"/>',
              f'<text x="{sx(pct)+(7 if pct>=0 else -7):.1f}" y="{y+4}" text-anchor="{"start" if pct>=0 else "end"}" font-family="sans-serif" font-size="11.5">{pct:+.1f}%</text>']
    lo, hi = (r[8]-1)*100, (r[9]-1)*100
    y = cy+7
    s += [f'<line x1="{sx(lo):.1f}" y1="{y}" x2="{sx(hi):.1f}" y2="{y}" stroke="#202b3a"/>',
          f'<line x1="{sx(lo):.1f}" y1="{y-4}" x2="{sx(lo):.1f}" y2="{y+4}" stroke="#202b3a"/>',
          f'<line x1="{sx(hi):.1f}" y1="{y-4}" x2="{sx(hi):.1f}" y2="{y+4}" stroke="#202b3a"/>']
    if r[7] is not None:
        px = sx(r[7])
        s.append(f'<path d="M {px:.1f} {cy+18} l -5 7 l 10 0 z" fill="#8d97a0"/>')
s += [f'<text x="26" y="{H-26}" font-family="sans-serif" font-size="11.5" fill="#16877a">■ vs alpha6</text>',
      f'<text x="126" y="{H-26}" font-family="sans-serif" font-size="11.5" fill="#c98c43">■ vs prior head c38f24f</text>',
      f'<text x="256" y="{H-26}" font-family="sans-serif" font-size="11.5" fill="#8d97a0">▲ published vs prior hdev</text>',
      f'<text x="26" y="{H-9}" font-family="sans-serif" font-size="11" fill="#777">Host-to-host rates are descriptive, not a pooled benchmark. Each bar is the mean of interleaved paired runs on one pinned CPU.</text>',
      '</svg>']
(outdir/"chart.svg").write_text("\n".join(s)+"\n")
print(table)
print("\nwrote", outdir/"results.json", outdir/"table.md", outdir/"chart.svg")
