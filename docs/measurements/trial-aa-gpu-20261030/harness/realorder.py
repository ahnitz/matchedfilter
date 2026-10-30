import gzip, json, collections, sys, numpy as np
rows = collections.defaultdict(list)
for l in gzip.open(sys.argv[1], "rt"):
    r = json.loads(l)
    if r["event"] != "round": continue
    pref = r["preference"]; tp = r["times"].get(pref)
    played = r["shared"].get(pref, pref); order = r["order"]
    if not tp or played not in order: continue
    for c, t in r["times"].items():
        if c == pref or r["shared"].get(c, c) != c or c not in order or not t: continue
        rel = "after" if order.index(c) > order.index(played) else "before"
        rows[(r["machine"], r["kind"], c[:30], rel)].append(np.log(t / tp))
for k, v in sorted(rows.items()):
    v = np.array(v); print("%-5s %-11s %-30s challenger %-6s %4d  mean %+.3f sd %.3f" % (k + (len(v), v.mean(), v.std())))
