#!/usr/bin/env python3
"""Replay captured single-template refilter calls (HierarchicalSearch's PeaksContext.refilter:
one template of a leaf bank over one window of its parent series, usually at threshold 0 with
a fine bin size -- a search's follow-up in another detector).

  python tools/bench_refilter.py CAPTURE.pkl [--rounds 5] [--calls N] [--no-check]

CAPTURE.pkl holds each leaf bank's taps, counts, options and reference profile, and per call
the series span around the window, the request, and the result the capturing library returned
(dict(banks=..., profiles=..., calls=[...])). Each bank is rebuilt and referenced untimed. A
call is then timed cold (the first for its template: the single-template plan is built) and
warm (the fastest of --rounds repeats), and its peaks are compared with the captured ones.

Prints per-call cold and warm times and the largest SNR difference from the capture; exits 1
when any call's peak positions differ or an SNR differs by more than --rtol of its magnitude.
"""
import argparse
import pickle
import sys
import time

import numpy as np

from matchedfilter import TimeDomainFilterBank


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("capture")
    ap.add_argument("--rounds", type=int, default=5, help="warm repeats per call (fastest counts)")
    ap.add_argument("--calls", type=int, default=0, help="replay only the first N calls")
    ap.add_argument("--rtol", type=float, default=1e-4,
                    help="largest accepted |SNR difference| / |SNR| from the capture")
    ap.add_argument("--no-check", action="store_true", help="time only")
    a = ap.parse_args(argv)
    with open(a.capture, "rb") as f:
        cap = pickle.load(f)
    calls = cap["calls"][:a.calls] if a.calls else cap["calls"]
    banks, cold, warm, worst, bad = {}, [], [], 0.0, 0
    for c in calls:
        bank = banks.get(c["bank"])
        if bank is None:
            b = cap["banks"][c["bank"]]
            bank = banks[c["bank"]] = TimeDomainFilterBank(b["taps"], b["counts"], **b["opts"])
            w, df = cap["profiles"][b["profile"]]
            bank.set_reference(w, delta_f=df)
        ser = c["series"]
        if c.get("strided"):
            # as the search passes it: one lane of a packed pair of real series
            pair = np.zeros(len(ser), np.complex64)
            pair.real = ser
            ser = pair.real
        kw = dict(windows=slice(*c["window"]), binsize=c["binsize"], threshold=c["threshold"],
                  template_index=c["template_index"])
        t = time.perf_counter()
        res = bank.filter_series(ser, **kw)
        cold.append(time.perf_counter() - t)
        best = float("inf")
        for _ in range(a.rounds):
            t = time.perf_counter()
            res = bank.filter_series(ser, **kw)
            best = min(best, time.perf_counter() - t)
        warm.append(best)
        if not a.no_check:
            order = np.argsort(res.sample_indices, kind="stable")
            ref = np.argsort(c["sample_indices"], kind="stable")
            same = (res.sample_indices.size == c["sample_indices"].size
                    and np.array_equal(res.sample_indices[order], c["sample_indices"][ref]))
            if same and res.snr.size:
                d = np.abs(res.snr[order] - c["snr"][ref]) / np.maximum(np.abs(c["snr"][ref]), 1e-30)
                worst = max(worst, float(d.max()))
                same = float(d.max()) <= a.rtol
            bad += not same
    cold, warm = np.array(cold), np.array(warm)
    print("%d calls over %d banks" % (len(calls), len(banks)))
    print("cold (first call of a template): mean %.3f ms, median %.3f ms" % (1e3 * cold.mean(), 1e3 * np.median(cold)))
    print("warm (fastest of %d):            mean %.3f ms, median %.3f ms" % (a.rounds, 1e3 * warm.mean(), 1e3 * np.median(warm)))
    if not a.no_check:
        print("check against the capture: %d calls differ; largest relative SNR difference %.2e" % (bad, worst))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
