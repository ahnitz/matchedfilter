"""The shipped SPIR-V, and whether it still matches the source it came from.

A stale kernel blob is a dangerous failure because it is silent: the module
loads, dispatches, and returns plausible numbers computed by the wrong code.
This project has already paid for that once -- a stale `N = 2048` left in a
kernel made a baseline 2.8x too slow, which would have flattered a speedup by
the same factor, and it was caught only because an unrelated figure was
printed beside it.

So the blobs are checked two ways: their host-side contract is pinned here,
and when slangc is present they are recompiled and compared byte for byte.
"""
import json
import pathlib
import struct

import pytest

import matchedfilter


def _tools_dir():
    """tools/ beside the TESTS, not beside the installed package.

    Using matchedfilter.__file__ works only in a source checkout; against an
    installed wheel the package sits in site-packages and tools/ is nowhere
    near it.
    """
    here = pathlib.Path(__file__).resolve().parent
    for base in (here.parent, here.parent.parent):
        cand = base / "tools"
        if (cand / "kernel_variants.py").is_file():
            return cand
    return None


def _generator():
    """tools/kernel_variants.py of the checkout beside the tests (skips for an installed
    package)."""
    import sys
    tools = _tools_dir()
    if tools is None:
        pytest.skip("tools/ is not beside the tests (installed package?)")
    sys.path.insert(0, str(tools))
    import kernel_variants
    return kernel_variants


SPIRV_DIR = pathlib.Path(matchedfilter.__file__).resolve().parent / "spirv"
MANIFEST = SPIRV_DIR / "manifest.json"


def test_the_kernels_are_present_in_the_installed_package():
    """The GPU blobs must travel with the package, and this must FAIL loudly.

    It was a skip once, and that hid a real bug: setup.py carried a
    package_data= listing the SPIR-V, a pyproject build ignores that
    argument, and the wheel shipped without a single kernel in it. The build
    succeeded, the install succeeded, and only device="gpu" would have found
    out -- on the user's machine.
    """
    import hashlib
    assert MANIFEST.is_file(), (
        "%s is missing. Run tools/kernel_variants.py build, and if this is an installed "
        "package check [tool.setuptools.package-data] in pyproject.toml."
        % MANIFEST)
    for rec in json.loads(MANIFEST.read_text())["kernels"].values():
        blob = SPIRV_DIR / rec["file"]
        assert blob.is_file(), "%s missing from the package" % blob
        assert hashlib.sha256(blob.read_bytes()).hexdigest() == rec["sha256"]


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST.read_text())


def _flat(kernels, n):
    """The flat kernel's record at n: its own build, or its 32 KB one."""
    return kernels.get("tierb_%d" % n) or kernels["tierb_%d_lds32" % n]


def test_every_tier_b_size_is_present(manifest):
    kv = _generator()
    built = {rec["n"] for stem, rec in manifest["kernels"].items()
             if stem in ("tierb_%d" % rec["n"], "tierb_%d_lds32" % rec["n"])}
    assert sorted(built) == sorted(kv.TIER_B)


def test_full_output_artifacts_cover_the_public_sizes(manifest):
    from conftest import kernel_dir
    from matchedfilter import _kernels
    metal = json.loads((kernel_dir('metal') / "manifest.json").read_text())["kernels"]
    for n in sorted(matchedfilter.CorrelationFilter._gpu_sizes):
        if n <= 65536:
            for kernels in (manifest["kernels"], metal):
                for role in ("full", "full_series"):
                    stem = "%s_%d" % (role, n)
                    assert stem in kernels or stem + "_lds32" in kernels, stem
                    for name in (stem, stem + "_lds32"):
                        assert name not in kernels or kernels[name]["lds_bytes"] <= 65536
                    assert (stem in kernels and kernels[stem]["lds_bytes"] <= 32768
                            or stem + "_lds32" in kernels), (
                        "%s has no build Apple's 32 KB holds" % stem)
        else:
            n1, n2 = _kernels.two_stage("vulkan", n)
            assert n1 * n2 == n
            for role in ('corr1', 'corr2', 'corr_series2', 'fwd1', 'fwd2'):
                assert "tc_%s_%d" % (role, n) in manifest["kernels"]
                assert "tc_%s_%d" % (role, n) in metal


def test_continuous_output_gpu_binding_contract(manifest):
    for stem, bindings in (("full_series_4096", 4), ("tc_corr_series2_131072", 3)):
        rec = manifest["kernels"][stem]
        assert [d['binding'] for d in rec['descriptors']] == list(range(bindings))
        assert rec['push_bytes'] > 0


@pytest.mark.parametrize("n", [1024, 2048, 4096, 8192, 16384])
def test_blob_is_valid_spirv(manifest, n):
    blob = (SPIRV_DIR / _flat(manifest["kernels"], n)["file"]).read_bytes()
    assert len(blob) % 4 == 0, "SPIR-V is a word stream"
    assert struct.unpack("<I", blob[:4])[0] == 0x07230203


@pytest.mark.parametrize("n", [1024, 2048, 4096, 8192, 16384])
def test_workgroup_is_one_sixteenth_of_the_transform(manifest, n):
    """WG = n/16 is the four-step split, not a tuning knob.

    Each thread owns one of the 16 rows' worth of work, so a mismatch here
    means the host would dispatch a grid that does not cover the transform.
    """
    assert _flat(manifest["kernels"], n)["local_size"][0] == n // 16


@pytest.mark.parametrize("n", [1024, 4096, 16384])
def test_host_binding_contract(manifest, n):
    """What the host must bind, read from the artefact rather than the source.

    The uniform entry-point parameters compile to PUSH CONSTANTS, not to
    further descriptors. A host written from the Slang source would bind
    buffers the module never reads, so this is pinned where it can be seen.
    """
    rec = _flat(manifest["kernels"], n)
    # data, tmpl, peakIdx, peakVal, then the row-window table (gRowWin: each row's window and
    # bin phase, read when specialization constant 76 is set; a dummy is bound otherwise).
    assert [(d["set"], d["binding"]) for d in rec["descriptors"]] == [
        (0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
    assert all(d["kind"] == "StorageBuffer" for d in rec["descriptors"])
    assert rec["push_bytes"] == 28


def test_blobs_match_the_current_kernel_source(manifest, tmp_path):
    """Recompile and compare, so edited source cannot ship as an old blob."""
    kv = _generator()
    slangc = kv.find_slangc()
    if slangc is None:
        pytest.skip("slangc not installed (build-time dependency only)")
    kv.check_slangc_version(slangc)
    flat = {"tierb_%d" % n for n in kv.TIER_B}
    for v in kv.variants("vulkan"):
        if v.stem not in flat:
            continue
        fresh = kv.compile_variant(slangc, v, tmp_path).read_bytes()
        assert fresh == (SPIRV_DIR / v.file).read_bytes(), (
            "%s is stale: src/gpu has changed since it was built. "
            "Re-run tools/kernel_variants.py build." % v.file)


#: The kernels a host picks by the device's workgroup memory (_kernels.runnable): each needs
#: a 32 KB build where its own asks for more. The coarse layouts are a measured choice among
#: the builds a device holds instead.
_RUNNABLE = ("tierb_", "refine_", "items_", "full_")


@pytest.mark.parametrize("backend", ["vulkan", "metal"])
def test_every_kernel_has_a_portable_variant_when_it_needs_one(backend):
    """Anything over 32 KB of workgroup memory must have a fallback.

    Apple allows a threadgroup 32 KB and several kernels are built at 64 KB
    because that is fastest on the development device. Without a smaller
    build those sizes cannot create a pipeline at all there. Metal is built
    against its own staging cap (Apple and the Radeon want opposite answers),
    so its manifest is checked on its own.
    """
    from conftest import kernel_dir
    folder = SPIRV_DIR if backend == "vulkan" else kernel_dir("metal")
    kernels = json.loads((folder / "manifest.json").read_text())["kernels"]
    for stem, rec in kernels.items():
        if not stem.startswith(_RUNNABLE) or "_c16" in stem or stem.endswith("_lds32"):
            continue
        if rec["lds_bytes"] > 32768:
            small = kernels.get(stem + "_lds32")
            assert small is not None, (
                "%s %s asks for %d KB and has no portable variant"
                % (backend, stem, rec["lds_bytes"] // 1024))
            assert small["lds_bytes"] <= 32768


def test_declared_shared_memory_matches_the_kernels_own_arithmetic(manifest):
    """The manifest must not claim a size the shader does not ask for: every tierb.slang build's
    workgroup memory, read from its artifact on each backend, is the staging its defines give
    (kernel_variants.staging_bytes)."""
    from conftest import kernel_dir
    kv = _generator()
    for backend, folder in (("vulkan", SPIRV_DIR), ("metal", kernel_dir("metal"))):
        kernels = json.loads((folder / "manifest.json").read_text())["kernels"]
        checked = 0
        for v in kv.variants(backend):
            if v.stem.startswith("tierb_") and "cap" in v.facts:
                assert kernels[v.stem]["lds_bytes"] == kv._staging(v), (backend, v.stem)
                checked += 1
        assert checked > 50, backend


def test_base_coarse_kernels_are_untiled():
    """TILE_T is compiled in, so the BASE coarse kernel must be TILE_T=1.

    The host falls back to an untiled dispatch whenever ntemplates does not
    divide by the tile -- nt=1, 3 and 5 never do. If the base kernel
    carries the band's tile instead of 1, that fallback selects a TILED
    kernel and dispatches for an untiled one. The kernel then walks TILE_T
    consecutive templates from p0 = gid.x*TILE_T, past the end of the
    bank: pairs are never visited and the gate silently drops signal, while
    out-of-range groups write past the output buffer.

    Traced at band 512, nt=2: 4 groups at p0 = 0, 4, 8, 12 with only pairs
    0 and 1 reachable, so half the injections vanished.

    Every tile in kernel_variants.COARSE_TILES must exist alongside it at every band, and
    each must be a DIFFERENT kernel -- if they compile identical the tile is not reaching
    the source.
    """
    spv = SPIRV_DIR
    if not any(spv.glob("tierb_*_c16.spv")):
        pytest.skip("no coarse kernels in this build")
    kv = _generator()
    checked = 0
    for band in (64, 128, 256, 512, 1024):
        base = spv / ("tierb_%d_c16.spv" % band)
        if not base.exists():
            continue
        blobs = {base.read_bytes()}
        for tile in kv.COARSE_TILES:
            tiled = spv / ("tierb_%d_c16t%d.spv" % (band, tile))
            assert tiled.exists(), (
                "band %d has no %s: the host could not offer tile %d" % (band, tiled.name, tile))
            blob = tiled.read_bytes()
            assert blob not in blobs, (
                "band %d: tile %d compiles identical to another build, so TILE_T is "
                "not reaching the source" % (band, tile))
            blobs.add(blob)
            checked += 1
    assert checked, "no band with a tile was checked"


def test_no_shipped_module_asks_for_more_than_1024_invocations():
    """Every shipped module's workgroup is at most 1024 invocations, where the build stops
    (tools/kernel_variants.py: RADIX, and the coarse packings skip (n/16) * ppg > 1024). A
    module past it is a blob an older build left behind: tierb_8192_c16p4 and
    tierb_16384_c16p2/p4 (2048-4096 invocations, built 2026-10-03 without the row-window
    binding the host now binds) shipped until 2026-10-29."""
    kv = _generator()
    sizes = {p.name: kv.reflect(p.read_bytes())["local_size"] for p in sorted(SPIRV_DIR.glob("*.spv"))}
    assert sizes and None not in sizes.values()
    over = {name: s for name, s in sizes.items() if s[0] * s[1] * s[2] > 1024}
    assert not over, "modules no build makes: %s" % over
