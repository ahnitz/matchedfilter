#!/usr/bin/env python3
"""Build the Vulkan (SPIR-V) and Metal kernels: tools/kernel_variants.py's build for those
two backends, which writes each one's manifest.

Run:  python tools/build_spirv.py [--slangc PATH] [--only GLOB] [--jobs N]
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kernel_variants  # noqa: E402


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    return kernel_variants.main(["build", "--backend", "vulkan,metal"] + argv)


if __name__ == "__main__":
    raise SystemExit(main())
