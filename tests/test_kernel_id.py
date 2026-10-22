"""Persistent kernel choices follow compiled artifacts, including partial rebuilds."""
import importlib
import json
from pathlib import Path

import pytest

from matchedfilter import _kernel_id


@pytest.fixture
def package(tmp_path, monkeypatch):
    for folder in ("spirv", "ptx", "metal"):
        (tmp_path / folder).mkdir()
    for folder in ("spirv", "ptx"):
        (tmp_path / folder / "manifest.json").write_text('{"source_hashes": {"unchanged": "1"}}')
    (tmp_path / "spirv" / "tierb.spv").write_bytes(b"spirv")
    (tmp_path / "ptx" / "tierb.ptx").write_bytes(b"ptx")
    (tmp_path / "ptx" / "coarse_tc_256_w2.ptx").write_bytes(b"tensor core")
    (tmp_path / "metal" / "tierb.metal").write_bytes(b"source")
    monkeypatch.setattr(_kernel_id, "__file__", str(tmp_path / "_kernel_id.py"))
    _kernel_id.gpu_kernel_id.cache_clear()
    yield tmp_path
    _kernel_id.gpu_kernel_id.cache_clear()


@pytest.fixture
def stamp(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    return importlib.import_module("kernel_build_id").stamp


def test_cuda_only_rebuild_changes_only_cuda_identity(package, stamp):
    stamp(package)
    before = {b: _kernel_id.gpu_kernel_id(b) for b in _kernel_id.BACKENDS}
    (package / "ptx" / "coarse_tc_256_w2.ptx").write_bytes(b"new compiler or generated constants")
    stamp(package, ("cuda",))
    _kernel_id.gpu_kernel_id.cache_clear()       # a later process reads the rebuilt install
    after = {b: _kernel_id.gpu_kernel_id(b) for b in _kernel_id.BACKENDS}
    assert after["cuda"] != before["cuda"]
    assert after["vulkan"] == before["vulkan"] and after["metal"] == before["metal"]


def test_compiled_metal_library_and_added_variant_change_identity(package, stamp):
    stamp(package)
    before = _kernel_id.gpu_kernel_id("metal")
    library = package / "metal" / "tierb.metallib"
    for binary in (b"compiled", b"different compiler output"):
        library.write_bytes(binary)
        stamp(package, ("metal",))
        _kernel_id.gpu_kernel_id.cache_clear()
        after = _kernel_id.gpu_kernel_id("metal")
        assert after != before
        before = after


def test_normal_startup_does_not_read_kernel_bank(package, stamp, monkeypatch):
    stamp(package)

    def unexpected(*args):
        raise AssertionError("runtime scanned compiled programs")

    monkeypatch.setattr(_kernel_id, "artifact_digest", unexpected)
    for backend in _kernel_id.BACKENDS:
        assert len(_kernel_id.gpu_kernel_id(backend)) == 16


def test_legacy_manifest_uses_actual_programs(package):
    before = _kernel_id.gpu_kernel_id("cuda")
    (package / "ptx" / "coarse_tc_256_w2.ptx").write_bytes(b"changed")
    _kernel_id.gpu_kernel_id.cache_clear()
    assert _kernel_id.gpu_kernel_id("cuda") != before


@pytest.mark.parametrize("builder,backends", [("build_spirv", ("vulkan", "metal")),
                                              ("build_ptx", ("cuda",))])
def test_successful_partial_or_full_build_stamps_output(package, stamp, monkeypatch,
                                                        builder, backends):
    # Every early return from a partial build passes through main's stamp wrapper.
    module = importlib.import_module(builder)
    monkeypatch.setattr(module, "ROOT", package.parents[1])
    target = package.parents[1] / "python" / "matchedfilter"

    def stamp_build(actual, backends):
        assert actual == target
        stamp(package, backends)

    monkeypatch.setattr(importlib.import_module("kernel_build_id"), "stamp", stamp_build)
    monkeypatch.setattr(module, "_build", lambda *a: 0)
    assert module.main() == 0
    for backend in backends:
        _, _, folder, field = _kernel_id.BACKENDS[backend]
        assert json.loads((package / folder / "manifest.json").read_text())[field]


def test_shipped_build_ids_match_every_compiled_program():
    from conftest import kernel_dir
    for backend, (files, _, folder, field) in _kernel_id.BACKENDS.items():
        package = kernel_dir(files).parent     # off macOS, Metal's are the checkout's
        manifest = json.loads((package / folder / "manifest.json").read_text())
        assert manifest[field] == _kernel_id.artifact_digest(package, backend), (
            "GPU artifacts changed: run tools/kernel_build_id.py after rebuilding")
