"""The shipped GPU kernels of each backend, as its build recorded them.

tools/kernel_variants.py writes one manifest per backend (spirv/, metal/, ptx/), every
kernel a record under its artifact's stem: the file, the entry point the host loads, the
facts it was built with (n, cap, ppg, tile, ...) and those read back from the artifact
(local size, workgroup memory; for SPIR-V its descriptors and push-constant bytes). The
hosts take kernel facts from here and restate none of them.

Stems follow one scheme on every backend: <role>_<n>[_<variant>][_lds32], where the _lds32
build is the same kernel staged in 32 KB of workgroup memory for a device that offers less
than the first build asks (runnable).
"""
import json
import pathlib
from functools import lru_cache

from ._kernel_id import BACKENDS

_PACKAGE = pathlib.Path(__file__).resolve().parent


def folder(backend):
    """The package folder holding a backend's artifacts and manifest."""
    return _PACKAGE / BACKENDS[backend][0]


@lru_cache(maxsize=None)
def manifest(backend):
    """A backend's manifest ({} for an install without one)."""
    try:
        return json.loads((folder(backend) / "manifest.json").read_text())
    except (OSError, ValueError):
        return {}


def record(backend, stem):
    """The manifest record of one kernel, or None where it did not ship."""
    return manifest(backend).get("kernels", {}).get(stem)


def shipped(backend, stem):
    """Whether a kernel shipped."""
    return record(backend, stem) is not None


def runnable(backend, stem, max_shared):
    """The record of the build of `stem` a device with max_shared bytes of workgroup memory
    can run: stem's own, or its 32 KB build (stem + "_lds32") where stem asks for more or did
    not ship. None when neither ships or fits."""
    for name in (stem, stem + "_lds32"):
        rec = record(backend, name)
        if rec is not None and rec.get("lds_bytes", 0) <= max_shared:
            return rec
    return None


def two_stage(backend, n):
    """(n1, n2), the two-stage split of the full correlation at length n, or None where the
    two-stage kernels were not built for n."""
    split = manifest(backend).get("two_stage", {}).get(str(n))
    return None if split is None else (split["n1"], split["n2"])


def clear():
    """Forget the manifests read (a test that rebuilds an install)."""
    manifest.cache_clear()
