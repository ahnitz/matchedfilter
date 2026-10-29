#!/usr/bin/env python3
"""Build the CUDA (PTX) kernels: tools/kernel_variants.py's build for that backend, which
writes its manifest.

Run:  python tools/build_ptx.py [--slangc PATH] [--only GLOB] [--jobs N]
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kernel_variants  # noqa: E402


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    return kernel_variants.main(["build", "--backend", "cuda"] + argv)


if __name__ == "__main__":
    raise SystemExit(main())
