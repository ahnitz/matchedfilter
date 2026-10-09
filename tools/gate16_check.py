#!/usr/bin/env python3
"""The CPU fine stage with the FP16 first gate against the FP32 gate, on the ladder.

Runs tools/ladder.py's device loop twice on the CPU in one process -- MF_GATE16=1, then
MF_GATE16=0 -- with the same seed, and compares every call's peaks with ladder.compare:
a peak only one gate finds is a dismissal (or an extra pass) the bound did not prevent.
Steady-segment times of both are reported (warm-up segments excluded, as --warmup).

    python tools/gate16_check.py --bank BANK.hdf --profiles PROFILES.npz [--segments 5]
"""
import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ladder  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--profiles", required=True)
    ap.add_argument("--tops", type=int, default=1)
    ap.add_argument("--segments", type=int, default=5)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    args = argparse.Namespace(
        bank=a.bank, profiles=a.profiles, seg_samples=1 << 20, start_pad=120.0, end_pad=16.0,
        pad=4096, threshold=6.0, fd=1e-3, peak_window=1.0, asym_threshold=6.0,
        asym_bin_width=0.03, asym_num_bins=1000, segments=a.segments, warmup=a.warmup,
        fft_length=0, no_batch=False, pure=True, overlap=False)
    os.environ["MF_SINGLE_DEVICE"] = "bank"
    tops = ladder.load_tops(a.bank, a.tops)
    out = {}
    for kind, flag in (("f16", "1"), ("f32", "0")):
        os.environ["MF_GATE16"] = flag
        rep, res = ladder.run_device("cpu", tops, args, a.seed)
        out[kind] = (rep, res)
        print(kind, "steady", {k: round(v, 3) for k, v in rep["steady_s"].items()})
    check = ladder.compare(out["f32"][1], out["f16"][1], args.threshold)
    print("check (reference f32, device f16):", json.dumps(check, default=float))


if __name__ == "__main__":
    main()
