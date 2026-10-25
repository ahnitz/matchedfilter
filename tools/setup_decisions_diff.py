#!/usr/bin/env python
"""Compare two setup replays' decisions (tools/setup_replay.py --decisions).

    python tools/setup_decisions_diff.py A.json B.json

Prints how many banks agree on block sizes and on every decision (block sizes, chains, Q15),
the largest relative difference of the thresholds of banks that agree, and the first banks
that differ.
"""
import json
import sys


def main():
    a, b = (json.load(open(f)) for f in sys.argv[1:3])
    blk = same = 0
    worst = 0.0
    diff = []
    for i, (x, y) in enumerate(zip(a, b)):
        blk += x[1] == y[1]
        cx = [(c, q) for c, q, _ in x[2]]
        cy = [(c, q) for c, q, _ in y[2]]
        if x[1] == y[1] and cx == cy:
            same += 1
            for (_, _, tx), (_, _, ty) in zip(x[2], y[2]):
                for u, v in zip(tx, ty):
                    if u < 1e30 and v < 1e30:
                        worst = max(worst, abs(u - v) / max(abs(u), 1e-9))
        else:
            diff.append((i, x[1], cx, y[1], cy))
    print("banks %d/%d: block sizes agree %d, all decisions agree %d; max threshold diff %.2f%%"
          % (len(a), len(b), blk, same, 100 * worst))
    for d in diff[:10]:
        print("  DIFF bank %d: %s %s | %s %s" % d)
    return 0 if same == len(a) == len(b) else 1


if __name__ == "__main__":
    sys.exit(main())
