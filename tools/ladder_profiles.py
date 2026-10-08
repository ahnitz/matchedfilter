#!/usr/bin/env python3
"""Per-top-template reference profiles for tools/ladder.py (needs pycbc; run once per bank).

The bench is only as realistic as its data. pycbc_inspiral_fir filters, for each top template,
the reference SNR series of whitened detector data, whose spectrum is w_top(f) = |h_top(f)|^2 / S(f)
on [f_lower, f_high]; it hands the fine banks that same w_top as their reference
(TimeDomainFilterBank.set_reference_from_template). A single generic profile for every top
template makes the gates miss their calibration: the bench refined ~75% of pairs where the
production replica refines ~0.2%.

This writes w_top for every top template of a three-level bank, with S from an ASD file, on a
1/16 Hz grid, to an .npz the bench reads with --profiles. The bench itself stays pycbc-free.

    python tools/ladder_profiles.py --bank BANK.hdf --asd H1-O2-ASD.txt --out profiles.npz
"""
import argparse

import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bank", required=True)
    p.add_argument("--asd", required=True, help="two columns: frequency, amplitude spectral density")
    p.add_argument("--sample-rate", type=float, default=2048.0)
    p.add_argument("--segment-length", type=float, default=512.0)
    p.add_argument("--f-high", type=float, default=0.0, help="0: no cutoff beyond the template's")
    p.add_argument("--out-df", type=float, default=1.0 / 16)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    from pycbc.waveform.bank import RatioFilterBank
    flen = int(args.segment_length * args.sample_rate) // 2 + 1
    df = 1.0 / args.segment_length
    bank = RatioFilterBank(args.bank, filter_length=flen, delta_f=df, dtype=np.complex64)
    f = np.arange(flen) * df
    asd = np.loadtxt(args.asd)
    S = np.interp(f, asd[:, 0], asd[:, 1] ** 2, left=np.inf, right=np.inf)
    step = int(round(args.out_df / df))
    nout = flen // step
    out = {"delta_f": np.float64(step * df)}
    for top in bank.top_indices:
        h = bank.get_top_template(int(top))
        hf = np.asarray(h)[:flen]
        w = np.zeros(flen)
        good = np.isfinite(S[:hf.size]) & (S[:hf.size] > 0)
        w[:hf.size][good] = np.abs(hf[good]) ** 2 / S[:hf.size][good]
        flo = float(getattr(h, "f_lower", 0.0) or 0.0)
        w[f < flo] = 0.0
        if args.f_high > 0:
            w[f > args.f_high] = 0.0
        out["top_%d" % int(top)] = w[:nout * step].reshape(nout, step).mean(axis=1)
    np.savez_compressed(args.out, **out)
    print("wrote %d profiles at delta_f %.4g to %s" % (len(out) - 1, step * df, args.out))


if __name__ == "__main__":
    main()
