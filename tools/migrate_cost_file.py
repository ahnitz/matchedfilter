#!/usr/bin/env python
"""Rewrite an MF_COST_FILE's trial locks in the measured-choice format (2026-10-21).

    python tools/migrate_cost_file.py costs.json [--out new.json]

Block-size, chain and Q15 trials keep their locks as measured choices, one record
"choice|<key>" each ({"value": ..., "median": ...}), since stage C of the unification plan.
The library does not read the older records ("block-trial|...", "chain-trial|...",
"q15-trial|..." and "chain-trial|...|batches"): without migration, a machine runs those
trials once more and stores the new records. This rewrites the locks, keeps their trial
medians and re-check state, and drops unfinished trials (their samples restart). Every
other record is copied unchanged. Writes in place unless --out is given; run it while no
process is using the file.
"""
import argparse
import json
import sys

OLD = ("block-trial|", "chain-trial|", "q15-trial|")


def migrate(records):
    """(new records, {old key: new key or None for dropped})."""
    out, moved = {}, {}
    for k, v in records.items():
        if not k.startswith(OLD):
            out[k] = v
            continue
        new = None
        if isinstance(v, dict) and not k.endswith("|batches"):
            if k.startswith("block-trial|") and "winner" in v:
                value = int(v["winner"])
            elif k.startswith("chain-trial|") and v.get("chain"):
                value = ",".join(str(int(b)) for b in v["chain"])
            elif k.startswith("q15-trial|") and "q15" in v:
                value = str(bool(v["q15"]))
            else:
                value = None
            if value is not None:
                new = "choice|" + k
                rec = {"value": value}
                if isinstance(v.get("median"), dict):
                    rec["median"] = {str(c): float(m) for c, m in v["median"].items()}
                if v.get("rechecked"):
                    rec["rechecked"] = True
                if new not in records:              # a record already in the new format wins
                    out[new] = rec
        moved[k] = new
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
    kept = sum(1 for v in moved.values() if v)
    print("%d trial locks migrated, %d unfinished trials dropped" % (kept, len(moved) - kept))
    return 0


if __name__ == "__main__":
    sys.exit(main())
