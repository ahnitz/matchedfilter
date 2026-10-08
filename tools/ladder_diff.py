#!/usr/bin/env python3
"""Localise a tools/ladder.py --check mismatch: compare each stage on identical inputs.

Builds the ladder's first top exactly as ladder.py does, then
  middle  correlate_series of one analytic segment on both devices
  fine    each fine bank's filter_series over the SAME (CPU) middle row
and prints the worst difference per stage, so a device mismatch is pinned to
the stage that produces it rather than inherited downstream.

    python tools/ladder_diff.py --bank BANK.hdf --device gpu:0
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
import ladder                                                  # noqa: E402
from matchedfilter import TimeDomainFilterBank                 # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bank", required=True)
    p.add_argument("--device", default="gpu:0")
    p.add_argument("--rows", type=int, default=0, help="fine banks to check (0: all)")
    p.add_argument("--seed", type=int, default=1)
    a = p.parse_args()
    top = ladder.load_tops(a.bank, 1)[0]
    rng = np.random.default_rng(a.seed)
    amp = np.sqrt(ladder.profile())
    w = ladder.profile()
    S = 1 << 20
    a0, a1 = int(120 * ladder.RATE), S - int(16 * ladder.RATE)
    probe = TimeDomainFilterBank(top["mid_taps"], tap_counts=top["mid_counts"], engine="corr")
    y = probe.correlate_series(ladder.analytic_series(rng, 1 << 18, amp))[:, 1 << 15:-(1 << 15)]
    scale = (1.0 / np.sqrt(np.mean(np.abs(y) ** 2, axis=1) / 2)).astype(np.float32)
    taps = top["mid_taps"] * scale[:, None]
    ser = ladder.analytic_series(rng, S, amp)
    mids = {}
    for dev in ("cpu", a.device):
        m = TimeDomainFilterBank(taps, tap_counts=top["mid_counts"], engine="corr", device=dev)
        mids[dev] = np.array(m.correlate_series(ser, windows=slice(a0 - 4096, a1 + 4096)))
    ref = mids["cpu"]
    d = np.abs(mids[a.device] - ref)
    rows = np.max(d, axis=1) / np.maximum(np.max(np.abs(ref), axis=1), 1e-30)
    print("middle: worst row rel diff %.3g (row %d), rows > 1e-5: %d / %d"
          % (rows.max(), rows.argmax(), int(np.sum(rows > 1e-5)), rows.size))
    bad = np.flatnonzero(rows > 1e-5)
    if bad.size:
        r = bad[0]
        cols = np.flatnonzero(d[r] > 1e-5 * np.abs(ref[r]).max())
        print("  row %d: %d bad samples, first %s, last %s" % (r, cols.size, cols[:5], cols[-5:]))
    xm = probe.correlate_series(ladder.analytic_series(rng, 1 << 18, amp)) * scale[:, None]
    nrow = len(top["fine"]) if a.rows == 0 else a.rows
    for row, (mid, ftaps, c) in enumerate(top["fine"][:nrow]):
        pf = TimeDomainFilterBank(ftaps, tap_counts=c, engine="corr")
        yf = pf.correlate_series(xm[row])[:, 1 << 15:-(1 << 15)]
        ftaps = ftaps / np.sqrt(np.mean(np.abs(yf) ** 2, axis=1) / 2)[:, None].astype(np.float32)
        res = {}
        for dev in ("cpu", a.device):
            b = TimeDomainFilterBank(ftaps, tap_counts=c, engine="hier", threshold=6.0,
                                     false_dismissal=1e-3, device=dev, binsize=2048)
            b.set_reference(w, delta_f=ladder.DF)
            r = b.filter_series(ref[row], windows=slice(a0, a1))
            res[dev] = dict(zip(zip(r.template_indices.tolist(), r.sample_indices.tolist()),
                                np.abs(r.snr).tolist()))
            if dev != "cpu":
                chains = [g.get("chain") for g in b.groups] if hasattr(b, "groups") else None
        A, B = res["cpu"], res[a.device]
        common = set(A) & set(B)
        worst = max((abs(A[k] - B[k]) / A[k] for k in common), default=0.0)
        only_a = sorted(set(A) - set(B))
        only_b = sorted(set(B) - set(A))
        flag = "" if not only_a and not only_b and worst < 1e-4 else "   <-- MISMATCH"
        print("fine row %2d (mid %d, %d tmpl): cpu %d, dev %d, common %d, worst %.2g%s"
              % (row, mid, ftaps.shape[0], len(A), len(B), len(common), worst, flag))
        for k in only_a[:3]:
            print("    only cpu %s snr %.3f" % (k, A[k]))
        for k in only_b[:3]:
            print("    only dev %s snr %.3f" % (k, B[k]))


if __name__ == "__main__":
    main()
