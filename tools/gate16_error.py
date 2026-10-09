#!/usr/bin/env python3
"""Measure the FP16 first gate's error against the FP32 gate, pair by pair (gate16.cc).

The FP16 gate reports |y16|max (1 + 3u) + kappa*u*rms(y) as an upper bound on the FP32
tier's |y32|max (u = 2^-11, rms over all m lags of the pair's coarse output; the factor
is the proven cost of choosing the lag on FP16 powers). This measures, for every (block,
template) pair of realistic fine-bank calls, the normalised error

    e = (|y16|max (1 + 3u) - |y32|max) / (u * rms)

and reports its distribution and its extreme on the low side, which kappa must exceed. Both gates see the
same plans (chain pinned, tier-0 threshold 0 so every pair is recorded through
MF_HMF_DUMP), and MF_GATE16_DEBUG makes the FP16 gate report kappa = 0 and the rms.

    python tools/gate16_error.py --bank BANK.hdf --profiles PROFILES.npz [--series 8]

Coarse output for realistic data: the ladder's largest fine bank of its largest top, the
top's own output profile as the reference, middle-filtered analytic noise as input; and
the same with a loud chirp-like transient added out of the search window (the bound must
hold when out-of-window power raises the error everywhere).
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def worker(args):
    """One mode in a fresh process (the switches are read when plans are built)."""
    sys.path.insert(0, str(HERE.parent / "python"))
    sys.path.insert(0, str(HERE))
    import ladder
    from matchedfilter import TimeDomainFilterBank
    top = ladder.load_tops(args.bank, 1)[0]
    pz = np.load(args.profiles)
    w, df = pz["top_%d" % top["top"]], float(pz["delta_f"])
    amp = np.sqrt(w)
    rng = np.random.default_rng(args.seed)
    probe = TimeDomainFilterBank(top["mid_taps"], tap_counts=top["mid_counts"], engine="corr")
    y = probe.correlate_series(ladder.analytic_series(rng, 1 << 18, amp, df))[:, 1 << 15:-(1 << 15)]
    scale = (1.0 / np.sqrt(np.mean(np.abs(y) ** 2, axis=1) / 2)).astype(np.float32)
    row = int(np.argmax([f[1].shape[0] for f in top["fine"]]))
    m, taps, c = top["fine"][row]
    xm = probe.correlate_series(ladder.analytic_series(rng, 1 << 18, amp, df))[row] * scale[row]
    pf = TimeDomainFilterBank(taps, tap_counts=c, engine="corr")
    yf = pf.correlate_series(xm)[:, 1 << 15:-(1 << 15)]
    taps = taps / np.sqrt(np.mean(np.abs(yf) ** 2, axis=1) / 2)[:, None].astype(np.float32)
    bank = TimeDomainFilterBank(taps, tap_counts=c, engine="hier", threshold=6.0,
                                false_dismissal=1e-3, binsize=2048, fft_lengths=[2048],
                                coarse_band_hz=tuple(args.chain))
    bank.set_reference(w, delta_f=df)
    S = 1 << 19
    for k in range(args.series):
        x = probe.correlate_series(ladder.analytic_series(rng, S, amp, df))[row] * scale[row]
        x = np.ascontiguousarray(x, np.complex64)
        if args.transient and k % 2 == 1:
            # loud short transient: a glitch the window does not contain in most blocks
            t0 = int(rng.integers(S // 4, 3 * S // 4))
            x[t0:t0 + 64] += (40.0 * np.exp(1j * np.linspace(0, 20, 64))).astype(np.complex64)
        bank._groups
        for g in bank._groups:
            g.plan.set_coarse_threshold(tuple(0.0 for _ in g.plan.config))
        bank.filter_series(x, windows=slice(4096, S - 4096))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--profiles", required=True)
    ap.add_argument("--series", type=int, default=8)
    ap.add_argument("--chain", type=float, nargs="+", default=[256.0, 512.0],
                    help="pinned chain, in Hz at 2048 Hz (bands in bins at n=2048)")
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--transient", action="store_true")
    ap.add_argument("--worker", action="store_true")
    a = ap.parse_args()
    if a.worker:
        worker(a)
        return
    tmp = Path(tempfile.mkdtemp())
    recs = {}
    for mode, env in (("f32", {"MF_GATE16": "0"}), ("f16", {"MF_GATE16_DEBUG": "1"})):
        path = tmp / (mode + ".bin")
        e = dict(os.environ, MF_HMF_DUMP=str(path), MF_AUTOTUNE="0", **env)
        cmd = [sys.executable, __file__, "--worker", "--bank", a.bank, "--profiles", a.profiles,
               "--series", str(a.series), "--seed", str(a.seed), "--chain", *map(str, a.chain)]
        if a.transient:
            cmd.append("--transient")
        subprocess.run(cmd, env=e, check=True)
        recs[mode] = np.fromfile(path, np.float32).reshape(-1, 8)
    r32, r16 = recs["f32"], recs["f16"]
    n = min(len(r32), len(r16))
    assert len(r32) == len(r16), (len(r32), len(r16))
    assert np.array_equal(r32[:, 6:], r16[:, 6:]), "pair order differs between modes"
    m32, m16, rms = r32[:, 0].astype(np.float64), r16[:, 0].astype(np.float64), r16[:, 2].astype(np.float64)
    u = 2.0 ** -11
    e = (m16 - m32) / (u * rms)
    rel = np.abs(m16 - m32) / np.maximum(m32, 1e-30)
    q = np.quantile(np.abs(e), [0.5, 0.9, 0.99, 0.999, 0.9999, 1.0])
    print("pairs %d  rms(y) median %.3f  max|y32| median %.3f" % (n, np.median(rms), np.median(m32)))
    print("normalised error e = (|y16|(1+3u)-|y32|)/(u*rms): mean %.3f std %.3f" % (e.mean(), e.std()))
    print("|e| quantiles 50/90/99/99.9/99.99/max: " + " ".join("%.2f" % v for v in q))
    print("relative error of the maximum: median %.2e  max %.2e" % (np.median(rel), rel.max()))
    print("max |e| / std(e) = %.1f" % (np.abs(e).max() / e.std()))
    print("most negative e (kappa must exceed its size): %.2f" % e.min())


if __name__ == "__main__":
    main()
