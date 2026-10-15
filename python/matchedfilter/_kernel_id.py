"""Identities of the shipped GPU programs used by persistent measured choices.

Builders hash the artifacts after compilation, including generated constants, compiler
options and CUDA-only kernels. Runtime reads that small manifest field once per backend;
it does not scan the PTX bank on every process startup. Legacy/custom installs without
the field fall back to hashing their actual programs once.
"""
import hashlib
import json
import pathlib
from functools import lru_cache


BACKENDS = {
    "vulkan": ("spirv", (".spv",), "spirv", "build_id"),
    "cuda": ("ptx", (".ptx",), "ptx", "build_id"),
    "metal": ("metal", (".metal", ".metallib"), "spirv", "metal_build_id"),
}


def artifact_digest(package, backend):
    """Digest program names and bytes, independent of source/build-machine paths.

    Hashing the output covers any source, generator, compiler or flag change that
    changes the code being timed. Unchanged generated code keeps its identity.
    """
    folder, suffixes, _, _ = BACKENDS[backend]
    digest = hashlib.sha256()
    digest.update(backend.encode() + b"\0")
    for path in sorted((pathlib.Path(package) / folder).iterdir()):
        if path.suffix not in suffixes or not path.is_file():
            continue
        digest.update(path.name.encode() + b"\0")
        with path.open("rb") as source:
            program = hashlib.sha256()
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                program.update(chunk)
            digest.update(program.digest())
    return digest.hexdigest()


@lru_cache(maxsize=3)
def gpu_kernel_id(backend="vulkan"):
    package = pathlib.Path(__file__).resolve().parent
    _, _, manifest_dir, field = BACKENDS[backend]
    try:
        manifest = json.loads((package / manifest_dir / "manifest.json").read_text())
        value = manifest.get(field)
        if (isinstance(value, str) and len(value) == 64
                and all(c in "0123456789abcdef" for c in value)):
            return value[:16]
    except (OSError, ValueError):
        pass
    try:
        return artifact_digest(package, backend)[:16]
    except OSError:
        return ""
