#!/usr/bin/env python
"""Remove an MF_COST_FILE's superseded trial records (2026-10-26).

    python tools/migrate_cost_file.py costs.json [--out new.json]

Block sizes, chains and the Q15 screen are decided by one joint trial (_trial), kept as
"choice|joint|<key>". The separate trials before it -- "block-trial|...", "chain-trial|...",
"q15-trial|..." and their measured-choice records "choice|block-trial|...",
"choice|chain-trial|...", "choice|q15-trial|..." -- are not read: a machine runs the joint
trial once more and stores its record. This removes them so the file holds what the library
reads. Every other record is copied unchanged. Writes in place unless --out is given, under
the library's writer lock and atomically.
"""
import argparse
import os
import sys

OLD = ("block-trial|", "chain-trial|", "q15-trial|")


def migrate(records):
    """(records kept, keys removed): every superseded trial record removed."""
    gone = sorted(k for k in records
                  if k.startswith(OLD) or (k.startswith("choice|") and k[len("choice|"):].startswith(OLD)))
    return {k: v for k, v in records.items() if k not in set(gone)}, gone


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    try:
        from matchedfilter import _costfile
    except ImportError:          # run from a checkout without the package installed
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
        from matchedfilter import _costfile
    dest = os.path.abspath(args.out or args.path)
    # Under the library's writer lock and published atomically, as the library writes it:
    # a process using the file meanwhile sees the old file or the new one, never half.
    with _costfile._cost_file_lock(dest):
        records, state = _costfile._read_cost_file(os.path.abspath(args.path))
        if state != "ok":
            print("%s: %s; nothing written" % (args.path, state))
            return 1
        out, gone = migrate(records)
        _costfile._write_cost_file(dest, out)
    for k in gone:
        print("drop   %s" % k)
    print("%d superseded trial records removed, %d records kept" % (len(gone), len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
