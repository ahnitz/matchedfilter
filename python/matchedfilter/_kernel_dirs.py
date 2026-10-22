"""Which ahead-of-time kernel directories a platform's install carries.

SPIR-V (Vulkan) everywhere; CUDA's PTX where CUDA runs (not macOS); Metal's libraries and
sources only on macOS. setup.py reads this file by path to leave the others out of a
wheel (the sdist keeps every directory), and the tests read it to know what an install
should hold. It imports nothing, so the build can read it before the package exists.
"""
import sys

ALL = ("spirv", "ptx", "metal")


def shipped(platform=None):
    """The kernel directories an install for this platform (sys.platform) carries."""
    platform = sys.platform if platform is None else platform
    return ("spirv", "metal") if platform == "darwin" else ("spirv", "ptx")
