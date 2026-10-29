# extract.py OUT.jsonl.gz DATADIR: every A/A log under DATADIR/<host>/<set>/<tag>.jsonl as one
# gzipped JSON-lines file, each record given its "set" and "_file" (<host>/<set>/<tag>), the
# derivable fields (ratios, aa_ratio) and the repeated name ("what") dropped, in file order;
# plus each process's wall time and load from the job index (event "job").
import glob, gzip, json, os, sys
out, base = sys.argv[1], sys.argv[2]
n = 0
with gzip.open(out, "wt", compresslevel=9) as f:
    for host in sorted(h for h in os.listdir(base) if os.path.isdir(os.path.join(base, h))):
        for st in sorted(os.listdir(os.path.join(base, host))):
            d = os.path.join(base, host, st)
            if not os.path.isdir(d):
                continue
            idx = os.path.join(d, "index.jsonl")
            if os.path.exists(idx):
                for line in open(idx):
                    j = json.loads(line)
                    f.write(json.dumps({"event": "job", "machine": host, "set": st, "_file": "%s/%s/%s" % (host, st, j["tag"]),
                                        "host": j.get("host"), "core": j["core"], "wall": round(j["wall"], 3),
                                        "load_start": j["load_start"], "load_end": j["load_end"], "rc": j["rc"]}) + "\n")
            for p in sorted(glob.glob(os.path.join(d, st + "_*.jsonl"))):
                tag = os.path.basename(p)[:-len(".jsonl")]
                for line in open(p):
                    r = json.loads(line)
                    for k in ("ratios", "aa_ratio", "what"):
                        r.pop(k, None)
                    r["machine"], r["set"], r["_file"] = host, st, "%s/%s/%s" % (host, st, tag)
                    f.write(json.dumps(r, separators=(",", ":")) + "\n")
                    n += 1
print("records", n, "bytes", os.path.getsize(out))
