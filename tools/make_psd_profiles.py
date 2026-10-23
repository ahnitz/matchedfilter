#!/usr/bin/env python3
"""Write tests/data/psd_model_profiles.npz: whitened inspiral signal power profiles
p(f) = f^(-7/3) / S(f) on [f_low, f_cut], from pycbc's analytic detector noise curves, for
the profile coverage of the gate tests (tests/test_screen_taper.py,
tools/verify_screen_taper.py). Needs pycbc; the tests read only the file.

  python tools/make_psd_profiles.py [--out tests/data/psd_model_profiles.npz]
"""
import argparse
import numpy as np

PSDS = ("aLIGOEarlyHighSensitivityP1200087",   # O1-like
        "aLIGOMidHighSensitivityP1200087",     # O2-like
        "aLIGOO3LowT1800545",                  # O3
        "aLIGOAdVO4T1800545",                  # O4
        "aLIGOAPlusDesignSensitivityT1800042") # A+
F_LOW = (20.0, 30.0)
F_CUT = (1024.0, 400.0, 200.0)                 # BNS-like (full band), and BBH-like merger cuts
RATE = 2048.0                                  # samples per second: n bins span RATE Hz


def profile(psd_name, f_low, f_cut, n):
    import pycbc.psd
    df = RATE / n
    length = n // 2 + 1
    S = np.asarray(pycbc.psd.from_string(psd_name, length, df, f_low).data, np.float64)
    f = np.arange(length) * df
    p = np.zeros(n)
    band = (f >= f_low) & (f <= f_cut) & (S > 0)
    p[:length][band] = f[band] ** (-7.0 / 3.0) / S[band]
    return p / p.sum()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="tests/data/psd_model_profiles.npz")
    a = ap.parse_args()
    names, out = [], {2048: [], 4096: []}
    for psd in PSDS:
        for fl in F_LOW:
            for fc in F_CUT:
                names.append("%s|flow=%g|fcut=%g" % (psd, fl, fc))
                for n in out:
                    out[n].append(profile(psd, fl, fc, n))
    np.savez_compressed(a.out, names=np.array(names), p2048=np.array(out[2048], np.float32),
                        p4096=np.array(out[4096], np.float32))
    print("wrote %d profiles to %s" % (len(names), a.out))


if __name__ == "__main__":
    main()
