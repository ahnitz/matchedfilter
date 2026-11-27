#!/usr/bin/env python3
"""Follow-ups spread over many template groups, as a PyCBC job makes them: many leaf banks,
each asked for one or two single-template calls, so a group's first call is most of the
calls. Measures what that first call costs in time and memory.

    python tools/bench_followup_groups.py [--banks 400] [--templates 96] [--calls 2]

Each bank is built and referenced untimed (taps of one block length per bank, block lengths
1024 to 4096 across banks). Then every bank gets --calls single-template calls (other
templates, windows of +/- 10,250 samples), timed one by one. Prints the calls' total and
per-call time, the first call of a bank against the later ones, and the process's resident
memory before and after the calls (and what the calls added per bank).

The real job's version of this regression (step 3 of the host-layer plan) was a store of
spectra sized for every template of a group, allocated at a group's first follow-up.
"""
import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np

# the repo's own python/ last, so a PYTHONPATH build (an A/B variant) wins
sys.path.append(str(Path(__file__).resolve().parent.parent / "python"))


def resident_bytes():
    """The process's resident memory, from /proc/self/statm."""
    with open("/proc/self/statm") as f:
        return int(f.read().split()[1]) * os.sysconf("SC_PAGE_SIZE")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--banks", type=int, default=400)
    ap.add_argument("--templates", type=int, default=96, help="templates per bank")
    ap.add_argument("--calls", type=int, default=2, help="single-template calls per bank")
    a = ap.parse_args(argv)
    os.environ.setdefault("MF_AUTOTUNE", "0")
    import matchedfilter
    from matchedfilter import TimeDomainFilterBank
    print("matchedfilter from %s" % matchedfilter.__file__)
    rng = np.random.default_rng(5)
    f = np.arange(16385) / 16.0
    profile = np.where((f >= 24) & (f <= 850), np.maximum(f, 1.0) ** (-7 / 3), 0.0)
    banks = []
    for b in range(a.banks):
        n = (1024, 2048, 4096)[b % 3]
        counts = rng.integers(n // 8, n // 3, size=a.templates)
        taps = np.zeros((a.templates, int(counts.max())), np.complex64)
        for i, c in enumerate(counts):
            t = np.arange(c) / 2048.0
            row = np.exp(2j * np.pi * ((30 + i) * t + (60 + b % 50) * t * t)) * np.hanning(c)
            taps[i, :c] = row / np.linalg.norm(row)
        bank = TimeDomainFilterBank(taps, counts, engine="hier", threshold=5.0,
                                    false_dismissal=1e-3, device="cpu", fft_lengths=[n],
                                    binsize=205)
        bank.set_reference(profile, delta_f=1.0 / 16.0)
        banks.append(bank)
    S = 1 << 20
    x = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
    calls = [(bank, int(rng.integers(0, a.templates)), int(rng.integers(30000, S - 30000)))
             for _ in range(a.calls) for bank in banks]
    before = resident_bytes()
    first, later, seen = [], [], set()
    for bank, ti, c in calls:
        t0 = time.perf_counter()
        bank.filter_series(x, windows=slice(c - 10250, c + 10250), binsize=205, threshold=0.0,
                           template_index=ti)
        dt = time.perf_counter() - t0
        (later if id(bank) in seen else first).append(dt)
        seen.add(id(bank))
    after = resident_bytes()
    total = sum(first) + sum(later)
    print("%d banks x %d calls: %.3f s, %.1f us a call; first call of a bank %.1f us, later "
          "%.1f us" % (a.banks, a.calls, total, 1e6 * total / len(calls),
                       1e6 * np.mean(first), 1e6 * np.mean(later) if later else float("nan")))
    print("resident memory %.1f MB before the calls, %.1f MB after: %.1f KB a bank"
          % (before / 2 ** 20, after / 2 ** 20, (after - before) / 1024 / a.banks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
