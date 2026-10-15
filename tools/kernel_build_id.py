#!/usr/bin/env python3
"""Stamp per-backend artifact identities after a full or partial GPU build.

The runtime reads these small fields instead of hashing tens of MB of PTX. This command
also handles externally compiled artifacts, such as a release wheel's Metal libraries.
"""
import argparse
import json
import pathlib
import runpy


ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "python" / "matchedfilter"
_helper = runpy.run_path(str(PACKAGE / "_kernel_id.py"))
BACKENDS, artifact_digest = _helper["BACKENDS"], _helper["artifact_digest"]


def stamp(package=PACKAGE, backends=tuple(BACKENDS)):
    package = pathlib.Path(package)
    manifests = {}
    for backend in backends:
        _, _, manifest_dir, field = BACKENDS[backend]
        path = package / manifest_dir / "manifest.json"
        if path not in manifests:
            manifests[path] = json.loads(path.read_text())
        manifests[path][field] = artifact_digest(package, backend)
    for path, manifest in manifests.items():
        path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", action="append", choices=tuple(BACKENDS))
    args = parser.parse_args()
    stamp(backends=args.backend or tuple(BACKENDS))
