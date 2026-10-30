import gzip, json, collections, sys, numpy as np
rows = collections.defaultdict(list)
for l in gzip.open(sys.argv[1], "rt"):
    r = json.loads(l)
    if r["event"] != "round": continue
    pref = r["preference"]; tp = r["times"].get(pref); ta = r.get("A/A")
    if not tp or not ta: continue
    played = r["shared"].get(pref, pref); order = r["order"]
    if played not in order: continue
    gap = order.index("A/A") - order.index(played)
    x = float(np.log(ta / tp))
    rows[(r["machine"], r["kind"], "A/A after" if gap > 0 else "A/A before")].append(x)
    rows[(r["machine"], r["kind"], "all")].append(x)
for k, v in sorted(rows.items()):
    v = np.array(v); print("%-5s %-12s %-11s %4d  mean %+.3f  sd %.3f  P(x<log .95) %.2f" % (k + (len(v), v.mean(), v.std(), np.mean(v < np.log(.95)))))
