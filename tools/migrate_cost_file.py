#!/usr/bin/env python
"""Rewrite an MF_COST_FILE's trial locks in the measured-choice format (2026-10-21).

    python tools/migrate_cost_file.py costs.json [--out new.json]

Block-size, chain and Q15 trials keep their locks as measured choices, one record
"choice|<key>" each ({"value": ..., "median": ...}), since stage C of the unification plan.
The library does not read the older records ("block-trial|...", "chain-trial|...",
"q15-trial|..." and "chain-trial|...|batches"): without migration, a machine runs those
trials once more and stores the new records. This rewrites the locks (with their trial
medians and re-check state) and the unfinished trials (their samples, needs and batch
counts), so both continue as they were. Every other record is copied unchanged. Writes in place unless --out is given; run it while no
process is using the file.
"""
import argparse
import json
import sys

OLD = ("block-trial|", "chain-trial|", "q15-trial|")


def _lock(k, v):
    """The new lock record for an old one, or None (no lock in it)."""
    if k.startswith("block-trial|") and "winner" in v:
        value = int(v["winner"])
    elif k.startswith("chain-trial|") and v.get("chain"):
        value = ",".join(str(int(b)) for b in v["chain"])
    elif k.startswith("q15-trial|") and "q15" in v:
        value = str(bool(v["q15"]))
    else:
        return None
    rec = {"value": value}
    if isinstance(v.get("median"), dict):
        rec["median"] = {str(c): float(m) for c, m in v["median"].items()}
    if v.get("rechecked"):
        rec["rechecked"] = True
    return rec


def _open(k, v):
    """The new open-contest record for an old unfinished trial, or None (no samples)."""
    smp = v.get("samples")
    if not isinstance(smp, dict) or not any(smp.values()):
        return None
    rec = {"samples": {str(c): [float(x) for x in s] for c, s in smp.items()},
           "need": {str(c): int(n) for c, n in (v.get("need") or {}).items()},
           "attempts": int(v.get("batches", 0)),
           "dropped": sorted(str(c) for c in v.get("dropped", ()))}
    if v.get("method") == "paired-v1":
        rec["method"] = "paired"
    if v.get("rechecked"):
        rec["rechecked"] = True
    return rec


def migrate(records):
    """(new records, {old key: (new key, "lock" or "open") or None for dropped}). A chain
    trial's unfinished batch samples ("|batches") continue only where its chain has no lock."""
    out, moved = {}, {}
    for k, v in records.items():
        if not k.startswith(OLD):
            out[k] = v
            continue
        moved[k] = None
        if not isinstance(v, dict):
            continue
        base = k[:-len("|batches")] if k.endswith("|batches") else k
        new = "choice|" + base
        lock = None if k.endswith("|batches") else _lock(k, v)
        if lock is None and k.endswith("|batches") and _lock(base, records.get(base) or {}):
            continue                                    # the chain is locked: samples done
        rec, kind = (lock, "lock") if lock is not None else (_open(k, v), "open")
        if rec is None or new in records:               # nothing to keep, or already new
            continue
        if new in out and "value" in out[new]:
            continue                                    # a lock beats an open contest
        out[new] = rec
        moved[k] = (new, kind)
    return out, moved


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    with open(args.path) as f:
        records = json.load(f)
    out, moved = migrate(records)
    with open(args.out or args.path, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    for k, v in sorted(moved.items()):
        print("%-6s %s" % (v[1] if v else "drop", k))
    locks = sum(1 for v in moved.values() if v and v[1] == "lock")
    opened = sum(1 for v in moved.values() if v and v[1] == "open")
    print("%d trial locks and %d unfinished trials migrated, %d records dropped"
          % (locks, opened, len(moved) - locks - opened))
    return 0


if __name__ == "__main__":
    sys.exit(main())
