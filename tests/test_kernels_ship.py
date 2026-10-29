"""Every kernel the library can ask for is present in the install.

A missing kernel is not a build error. tools/kernel_variants.py writes what
it is told to write, the package-data globs copy whatever matches, and nothing
compares the two -- so a kernel that stopped being generated, or a new
variant that no glob matched, ships as a wheel that works on the developer's
machine and fails on a device that selects the missing one.

That is not hypothetical. The flat kernel had a 32 KB variant for the two
sizes whose staging wants 64 KB and the refine kernel did not, so a device
offering 32 KB ran the flat path and could not create a hierarchical
pipeline at all. Every GPU used in development has 64 KB, so nothing here
could have noticed.

These check the SHIPPED tree via matchedfilter.__file__, so they hold for
an installed wheel and not only for a source checkout.
"""
import json
import pathlib

import pytest

import matchedfilter as mf
from matchedfilter import _kernel_dirs


#: The kernel directory each backend's manifest is in.
_FOLDER = {"vulkan": "spirv", "metal": "metal", "cuda": "ptx"}


def _shipped_backends():
    """The backends whose kernels this install carries."""
    return [b for b, d in _FOLDER.items() if d in _kernel_dirs.shipped()]


def _manifest(backend="vulkan"):
    p = pathlib.Path(mf.__file__).resolve().parent / _FOLDER[backend] / "manifest.json"
    if not p.is_file():
        pytest.skip("no %s manifest in this install" % backend)
    return json.loads(p.read_text())


@pytest.mark.parametrize("backend", sorted(_FOLDER))
def test_every_supported_length_has_a_kernel(backend):
    """_GPU_SIZES is the promise; every backend's manifest has to keep it, with the filter
    and the listed refine (or their 32 KB builds) at each length."""
    if backend not in _shipped_backends():
        pytest.skip("%s does not ship on this platform" % backend)
    kernels = _manifest(backend)["kernels"]
    for n in sorted(mf._filter._GPU_SIZES):
        for role in ("tierb", "refine"):
            stem = "%s_%d" % (role, n)
            assert stem in kernels or stem + "_lds32" in kernels, (
                "device='gpu' accepts n=%d but no %s kernel was built for it on %s"
                % (n, role, backend))


@pytest.mark.parametrize("backend", sorted(_FOLDER))
def test_every_file_the_manifest_names_exists(backend):
    """Including the 32 KB builds, which is where the gap was."""
    if backend not in _shipped_backends():
        pytest.skip("%s does not ship on this platform" % backend)
    folder = pathlib.Path(mf.__file__).resolve().parent / _FOLDER[backend]
    missing = ["%s: %s" % (stem, rec["file"]) for stem, rec in
               sorted(_manifest(backend)["kernels"].items()) if not (folder / rec["file"]).is_file()]
    assert not missing, "the manifest names kernels that did not ship:\n  " + "\n  ".join(missing)


@pytest.mark.parametrize("backend", sorted(_FOLDER))
def test_both_entry_points_have_the_same_variants(backend):
    """The flat and refine kernels run on the same devices, so they need the
    same fallbacks. Having one without the other is the bug this catches."""
    if backend not in _shipped_backends():
        pytest.skip("%s does not ship on this platform" % backend)
    kernels = _manifest(backend)["kernels"]
    for n in sorted(mf._filter._GPU_SIZES):
        flat_small = "tierb_%d_lds32" % n in kernels
        refine_small = "refine_%d_lds32" % n in kernels
        assert flat_small == refine_small, (
            "n=%s ships a 32 KB variant for %s only on %s -- a device that needs "
            "one needs both, and will run the flat path and fail to build a "
            "hierarchical pipeline"
            % (n, "the flat kernel" if flat_small else "the refine kernel", backend))


@pytest.mark.parametrize("backend", sorted(_FOLDER))
def test_forward_and_packing_kernels_ship(backend):
    if backend not in _shipped_backends():
        pytest.skip("%s does not ship on this platform" % backend)
    kernels = _manifest(backend)["kernels"]
    for n in mf._filter._GPU_SIZES:
        forward = kernels["forward_%d" % n]
        flat = kernels.get("tierb_%d" % n) or kernels["tierb_%d_lds32" % n]
        assert forward["local_size"] == flat["local_size"]
    for kernel in ("pack_coarse", "compact_peaks"):
        assert kernel in kernels


@pytest.mark.parametrize("backend", sorted(_FOLDER))
def test_production_shader_sources_match_built_manifest(backend):
    import hashlib
    source = pathlib.Path(__file__).resolve().parents[1] / 'src/gpu'
    if not source.is_dir():
        pytest.skip('source tree not available in this installation')
    if backend not in _shipped_backends():
        pytest.skip("%s does not ship on this platform" % backend)
    recorded = _manifest(backend)['source_hashes']
    assert set(recorded) == {'tierb.slang', 'fft_transform.slang',
                             'series_forward.slang', 'series_bands.slang', 'forward_tier0.slang',
                             'pack_coarse.slang',
                             'twiddle.slang', 'refine_bounded.slang', 'compact_peaks.slang'}
    for name, digest in recorded.items():
        assert hashlib.sha256((source / name).read_bytes()).hexdigest() == digest, (
            '%s changed: rebuild the kernels with tools/kernel_variants.py build' % name)


def test_shipped_kernels_carry_no_build_paths_or_stray_files():
    """The kernel directories of the installed package hold build outputs only: no source
    naming the machine it was built on (an absolute #line path in a Metal source also
    changes the Metal kernel identity from build host to build host) and no sync-conflict
    copies."""
    import re
    import matchedfilter
    pkg = pathlib.Path(matchedfilter.__file__).resolve().parent
    absolute = re.compile(rb'(/home/|/Users/)')
    found = []
    for sub in ("metal", "spirv", "ptx"):
        for p in sorted((pkg / sub).glob("*")):
            if "conflict" in p.name.lower():
                found.append("%s/%s: a sync-conflict copy" % (sub, p.name))
            elif p.suffix in (".metal", ".json") and absolute.search(p.read_bytes()):
                found.append("%s/%s: names an absolute path" % (sub, p.name))
    assert not found, found


def test_the_install_holds_its_platforms_kernel_directories():
    """Each directory _kernel_dirs says this platform ships is present and not empty."""
    root = pathlib.Path(mf.__file__).resolve().parent
    for d in _kernel_dirs.shipped():
        assert any((root / d).glob("*")), "%s/ is missing from this install" % d


@pytest.mark.parametrize("platform,want", [("darwin", ("spirv", "metal")),
                                           ("linux", ("spirv", "ptx"))])
def test_a_wheel_carries_only_what_its_platform_loads(platform, want):
    assert _kernel_dirs.shipped(platform) == want
