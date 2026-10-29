#!/usr/bin/env python3
"""Restamp the kernel identities in the GPU manifests after an external compile (a release
wheel's Metal libraries): every record's digest fields from the artifacts on disk
(matchedfilter._kernel_id.stamp).

Run:  python tools/kernel_build_id.py [--backend vulkan|metal|cuda ...]
"""
import argparse
import pathlib
import runpy

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "python" / "matchedfilter"
_helper = runpy.run_path(str(PACKAGE / "_kernel_id.py"))
BACKENDS, stamp = _helper["BACKENDS"], _helper["stamp"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--backend", action="append", choices=tuple(BACKENDS))
    args = parser.parse_args()
    stamp(PACKAGE, backends=args.backend or tuple(BACKENDS))
