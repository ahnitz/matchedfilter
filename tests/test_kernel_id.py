"""Persistent kernel choices follow compiled artifacts, kernel by kernel."""
import json
from pathlib import Path

import pytest

from matchedfilter import _kernel_id


def _write_manifest(folder, files):
    kernels = {Path(f).stem: {"file": f} for f in files}
    (folder / "manifest.json").write_text(json.dumps({"kernels": kernels}))


@pytest.fixture
def package(tmp_path, monkeypatch):
    """A package with two kernels per backend and manifests that name them (no digests)."""
    for folder, suffix in (("spirv", ".spv"), ("ptx", ".ptx"), ("metal", ".metal")):
        (tmp_path / folder).mkdir()
        for stem in ("tierb_256", "compact_peaks"):
            (tmp_path / folder / (stem + suffix)).write_bytes(("%s %s" % (folder, stem)).encode())
        _write_manifest(tmp_path / folder, ["tierb_256" + suffix, "compact_peaks" + suffix])
    monkeypatch.setattr(_kernel_id, "__file__", str(tmp_path / "_kernel_id.py"))
    _kernel_id.clear()
    yield tmp_path
    _kernel_id.clear()


def _ids():
    _kernel_id.clear()               # a later process reads the rebuilt install
    return {b: _kernel_id.gpu_kernel_id(b) for b in _kernel_id.BACKENDS}


def test_cuda_only_rebuild_changes_only_cuda_identity(package):
    _kernel_id.stamp(package)
    before = _ids()
    (package / "ptx" / "compact_peaks.ptx").write_bytes(b"new compiler or generated constants")
    _kernel_id.stamp(package, ("cuda",))
    after = _ids()
    assert after["cuda"] != before["cuda"]
    assert after["vulkan"] == before["vulkan"] and after["metal"] == before["metal"]


def test_a_rebuilt_kernel_changes_only_the_identities_that_name_it(package):
    _kernel_id.stamp(package)
    before = _kernel_id.kernel_id("vulkan", ["tierb_256"]), _kernel_id.kernel_id("vulkan", ["compact_peaks"])
    (package / "spirv" / "compact_peaks.spv").write_bytes(b"rebuilt")
    _kernel_id.stamp(package, ("vulkan",))
    _kernel_id.clear()
    after = _kernel_id.kernel_id("vulkan", ["tierb_256"]), _kernel_id.kernel_id("vulkan", ["compact_peaks"])
    assert after[0] == before[0] and after[1] != before[1]


def test_compiled_metal_library_changes_identity(package):
    _kernel_id.stamp(package)
    before = _ids()["metal"]
    library = package / "metal" / "tierb_256.metallib"
    for binary in (b"compiled", b"different compiler output"):
        library.write_bytes(binary)
        _kernel_id.stamp(package, ("metal",))
        after = _ids()["metal"]
        assert after != before
        before = after


def test_a_kernel_that_ships_later_changes_the_identity_that_named_it(package):
    _kernel_id.stamp(package)
    before = _kernel_id.kernel_id("vulkan", ["tierb_256_c16"])
    (package / "spirv" / "tierb_256_c16.spv").write_bytes(b"new")
    _write_manifest(package / "spirv", ["tierb_256.spv", "compact_peaks.spv", "tierb_256_c16.spv"])
    _kernel_id.stamp(package, ("vulkan",))
    _kernel_id.clear()
    assert _kernel_id.kernel_id("vulkan", ["tierb_256_c16"]) != before


def test_normal_startup_does_not_read_kernel_bank(package, monkeypatch):
    _kernel_id.stamp(package)
    _kernel_id.clear()

    def unexpected(*args):
        raise AssertionError("runtime hashed compiled programs")

    monkeypatch.setattr(_kernel_id, "file_sha256", unexpected)
    for backend in _kernel_id.BACKENDS:
        assert len(_kernel_id.gpu_kernel_id(backend)) == 16


def test_a_manifest_without_digests_hashes_the_programs_it_names(package):
    before = _ids()["cuda"]                       # the fixture's manifests carry no digests
    (package / "ptx" / "compact_peaks.ptx").write_bytes(b"changed")
    assert _ids()["cuda"] != before


def test_an_identity_is_the_same_from_the_manifest_or_the_programs(package):
    unstamped = _ids()
    _kernel_id.stamp(package)
    assert _ids() == unstamped


def test_shipped_digests_match_every_compiled_program():
    """Every record's digest is its artifact's: a rebuild that did not rewrite the manifest
    (or a hand-copied kernel) fails here."""
    from conftest import kernel_dir
    for backend, (folder, _, fields) in _kernel_id.BACKENDS.items():
        root = kernel_dir(folder)
        manifest = json.loads((root / "manifest.json").read_text())
        stale = [rec["file"] for rec in manifest["kernels"].values()
                 if {k: rec.get(k) for k in fields if k in rec}
                 != {k: v for k, v in _kernel_id.record_ids(root, rec["file"]).items() if k in fields}]
        assert not stale, ("GPU artifacts changed without their manifest: rebuild with "
                           "tools/kernel_variants.py or run tools/kernel_build_id.py: %s" % stale[:5])
