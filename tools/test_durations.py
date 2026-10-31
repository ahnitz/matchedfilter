#!/usr/bin/env python3
"""Write tests/durations.json, each test module's seconds, from a pytest --durations=0 log.

    python -m pytest tests --durations=0 --durations-min=0 > durations.log   # unsanitized
    python tools/test_durations.py durations.log

The table is what conftest's --shard balances its parts by (heaviest module first, into the
lightest shard so far); it is a hint, so a stale one moves only the balance. Times are summed
over each module's call, setup and teardown phases.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "tests" / "durations.json"


def module_seconds(lines):
    """{module name: seconds} from the lines of a --durations=0 report."""
    total = defaultdict(float)
    for line in lines:
        m = re.match(r"\s*([\d.]+)s (?:call|setup|teardown)\s+(?:\S*/)?(test_\w+)\.py::", line)
        if m:
            total[m.group(2)] += float(m.group(1))
    return dict(total)


def main(argv):
    if len(argv) != 2:
        sys.exit(__doc__)
    with open(argv[1]) as f:
        seconds = module_seconds(f)
    if not seconds:
        sys.exit("no durations in %s: run pytest with --durations=0" % argv[1])
    OUT.write_text(json.dumps({k: round(v, 2) for k, v in sorted(seconds.items())}, indent=1) + "\n")
    print("%d modules, %.0f s, written to %s" % (len(seconds), sum(seconds.values()), OUT))


if __name__ == "__main__":
    main(sys.argv)
