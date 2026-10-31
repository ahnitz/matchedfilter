"""Identities of the shipped GPU programs, which persistent measured choices are keyed on.

Each kernel's identity is its artifact's digest, recorded in the backend's manifest when it
is built (tools/kernel_variants.py) and restamped after an external compile (a release
wheel's Metal libraries: tools/kernel_build_id.py). Hashing the output covers any source,
generator, compiler or flag change that changes the code being timed, and unchanged generated
code keeps its identity. A measured choice is keyed on the kernels it timed (kernel_id), so a
rebuild that changes one kernel re-measures only the choices that timed it. The runtime reads
the small manifest fields once per backend and does not scan the PTX bank on startup; a
legacy or custom install whose manifest lacks them falls back to hashing the programs named.
It imports nothing from the package, so the build tools can run it by path.
"""
import hashlib
import json
import pathlib
from functools import lru_cache


#: backend -> (artifact folder, artifact suffixes, digest fields of a record). The folder
#: holds the backend's manifest.json. A Metal kernel is its source and, where Apple's tooling
#: compiled one, its library.
BACKENDS = {
    "vulkan": ("spirv", (".spv",), ("sha256",)),
    "cuda": ("ptx", (".ptx.gz",), ("sha256",)),
    "metal": ("metal", (".metal", ".metallib"), ("sha256", "metallib_sha256")),
}


def _stem_of(name, suffixes):
    """Strip the first matching artifact suffix from `name` (handles multi-part `.ptx.gz`)."""
    for s in suffixes:
        if name.endswith(s):
            return name[:-len(s)]
    return name.rsplit(".", 1)[0]


def file_sha256(path):
    """The sha256 hex digest of one file."""
    program = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            program.update(chunk)
    return program.hexdigest()


def record_ids(folder, filename):
    """The digest fields of a manifest record for the artifact `filename` in folder: sha256 of
    the artifact, and metallib_sha256 of a Metal source's compiled library where one exists."""
    folder = pathlib.Path(folder)
    out = {"sha256": file_sha256(folder / filename)}
    if filename.endswith(".metal"):
        lib = folder / (filename[:-len(".metal")] + ".metallib")
        if lib.is_file():
            out["metallib_sha256"] = file_sha256(lib)
    return out


def stamp(package, backends=tuple(BACKENDS)):
    """Restamp the digest fields of every record in each backend's manifest from the artifacts
    on disk (after Apple's compiler added the Metal libraries, for instance)."""
    for backend in backends:
        folder = pathlib.Path(package) / BACKENDS[backend][0]
        path = folder / "manifest.json"
        manifest = json.loads(path.read_text())
        for rec in manifest.get("kernels", {}).values():
            for field in BACKENDS[backend][2]:
                rec.pop(field, None)
            rec.update(record_ids(folder, rec["file"]))
        path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")


def _package():
    return pathlib.Path(__file__).resolve().parent


@lru_cache(maxsize=3)
def _ids(backend):
    """{artifact file name: digest} for every program of a backend, from its manifest (a
    Metal library under its own name); a manifest without them is hashed from the programs."""
    folder = _package() / BACKENDS[backend][0]
    try:
        kernels = json.loads((folder / "manifest.json").read_text()).get("kernels", {})
    except (OSError, ValueError):
        kernels = {}
    out = {}
    for rec in kernels.values():
        if not isinstance(rec, dict) or "file" not in rec:
            continue
        digest = rec.get("sha256")
        if not (isinstance(digest, str) and len(digest) == 64):
            try:
                digest = file_sha256(folder / rec["file"])
            except OSError:
                continue
        out[rec["file"]] = digest
        lib = rec.get("metallib_sha256")
        if isinstance(lib, str) and len(lib) == 64:
            out[rec["file"][:-len(".metal")] + ".metallib"] = lib
    if not kernels and folder.is_dir():          # no manifest at all: what is on disk
        for path in sorted(folder.iterdir()):
            if any(path.name.endswith(s) for s in BACKENDS[backend][1]) and path.is_file():
                out[path.name] = file_sha256(path)
    return out


def _digest(backend, names):
    digest = hashlib.sha256()
    digest.update(backend.encode() + b"\0")
    ids = _ids(backend)
    for name in sorted(names):
        digest.update(name.encode() + b"\0")
        digest.update(bytes.fromhex(ids[name]) if name in ids else b"-")
    return digest.hexdigest()[:16]


def kernel_id(backend, stems):
    """Identity of the named kernels (artifact stems: "tierb_256_c16p4", ...) of a backend:
    the digest of their programs' digests, 16 hex digits. A stem that did not ship counts as
    absent, so shipping it later changes the identity too."""
    suffixes = BACKENDS[backend][1]
    ids = _ids(backend)
    names = []
    for stem in set(stems):
        found = [stem + s for s in suffixes if stem + s in ids]
        names.extend(found or [stem + suffixes[0]])
    return _digest(backend, names)


def family_id(backend, prefix):
    """Identity of every shipped kernel of a backend whose stem starts with prefix (all the
    coarse builds of one band, "tierb_256_c16", for instance)."""
    suffixes = BACKENDS[backend][1]
    return kernel_id(backend, [_stem_of(n, suffixes) for n in _ids(backend)
                               if n.startswith(prefix)] or [prefix])


def gpu_kernel_id(backend="vulkan"):
    """Identity of every shipped program of a backend (for a choice that times all of them,
    and for reports): the digest of each program's name and digest, in name order -- the same
    value whether read from the manifest or hashed from the programs."""
    return _digest(backend, _ids(backend))


def clear():
    """Forget the identities read (a test that rebuilds an install)."""
    _ids.cache_clear()
