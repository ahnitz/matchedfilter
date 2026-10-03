"""The Metal kernels: generated, complete, and lowering to native primitives.

These run everywhere, including on Linux with no Apple hardware, because
what they check is the BUILD OUTPUT rather than execution. That is the part
that can silently rot: Slang marks its Metal target work in progress, so a
release that starts emulating a wave reduction instead of emitting simd_max
would still compile, still be correct, and quietly cost most of the
performance.

Running the kernels needs a Mac and is covered by the macOS CI job.
"""
import json
import pathlib

import pytest

import matchedfilter

METAL_DIR = pathlib.Path(matchedfilter.__file__).resolve().parent / "metal"
MANIFEST = (pathlib.Path(matchedfilter.__file__).resolve().parent
            / "spirv" / "manifest.json")

pytestmark = pytest.mark.skipif(not METAL_DIR.is_dir(),
                                reason="Metal kernels not built into this tree")


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST.read_text())


def test_every_size_has_metal(manifest):
    """A macOS wheel must carry the same coverage as a Linux one."""
    for key, info in manifest["modules"].items():
        assert "metal" in info, "n=%s has no Metal output" % key
        for entry, files in info["metal"].items():
            src = METAL_DIR / files["msl"]
            assert src.is_file(), "%s missing" % src
            assert src.stat().st_size > 1000, "%s looks empty" % src


@pytest.mark.parametrize("n", [1024, 4096, 16384])
def test_the_wave_reduction_is_native(manifest, n):
    """simd_max, not a shared-memory loop pretending to be one.

    This is the single thing that decided Metal over a translation layer,
    and it is a property of Slang's code generator rather than of this
    source -- so it is worth asserting rather than assuming it stays true
    across upgrades.
    """
    src = (METAL_DIR / manifest["modules"][str(n)]["metal"]["fusedTierB"]["msl"]).read_text()
    assert "simd_max" in src, "the wave reduction stopped lowering to simd_max"
    assert "simd_is_first" in src


@pytest.mark.parametrize("n", [1024, 4096, 16384])
def test_shared_memory_and_atomics_are_native(manifest, n):
    src = (METAL_DIR / manifest["modules"][str(n)]["metal"]["fusedTierB"]["msl"]).read_text()
    assert "threadgroup" in src, "no threadgroup storage"
    assert "threadgroup_barrier" in src
    assert "atomic_fetch_max_explicit" in src, \
        "the per-bin maximum stopped using a native atomic"


def test_the_coarse_kernel_has_metal():
    assert (METAL_DIR / "coarse_256.metal").is_file()


@pytest.mark.parametrize("band", [64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384])
def test_the_fp16_coarse_and_compact_kernels_have_metal(band):
    assert (METAL_DIR / f"tierb_{band}_c16.metal").is_file()
    assert (METAL_DIR / f"compact_{band}.metal").is_file()


@pytest.mark.parametrize("band", [8192, 16384, 32768, 65536])
def test_compact_portable_kernels_have_metal(band):
    assert (METAL_DIR / f"compact_{band}_lds32.metal").is_file()


def test_metal_fp16_helpers():
    import numpy as np
    from matchedfilter import _mtlcompute as M
    for band in (64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384):
        assert M._use_c16(band)
    assert not M._use_c16(32768)
    assert not M._use_c16(65536)

    # Values including subnormals, zeros, negative numbers, infinities, boundaries
    vals = np.array([0.0, -0.0, 1.0, -0.5, 2.0, -2.0, 65504.0, -65504.0, 2**-14], dtype=np.float32)
    c = (vals + 1j * vals[::-1]).astype(np.complex64)
    packed = M._pack_half2(c)
    assert packed.dtype == np.uint32
    assert packed.shape == c.shape
    re = packed.view(np.uint16)[0::2].view(np.float16)
    im = packed.view(np.uint16)[1::2].view(np.float16)
    np.testing.assert_allclose(re, c.real.astype(np.float16))
    np.testing.assert_allclose(im, c.imag.astype(np.float16))


def test_metal_stem_resolution():
    from matchedfilter import _mtlcompute as M
    class FakeContext(M.Context):
        pass
    ctx = FakeContext.__new__(FakeContext)
    ctx.max_shared_memory = 32768
    ctx.name = "Apple M2"
    for band in (64, 128, 256, 512, 1024, 2048, 4096):
        assert ctx._stem(band, "coarse16") == f"tierb_{band}_c16"
        assert ctx._stem(band, "compactPairs") == f"compact_{band}"
    # Bands exceeding 32KB on M2 select portable lds32 for compactPairs
    for band in (8192, 16384, 32768, 65536):
        assert ctx._stem(band, "compactPairs") == f"compact_{band}_lds32"


@pytest.mark.parametrize("n", [2048, 4096, 8192])
def test_single_bin_artifacts(manifest, n):
    for entry in ("fusedTierB", "refineListed"):
        info = manifest["modules"][str(n)]["metal"][entry]["one_bin"]
        assert info["lds_bytes"] <= 32768
        assert (METAL_DIR / info["msl"]).stat().st_size > 1000
        if info["metallib"] is not None:
            assert (METAL_DIR / info["metallib"]).is_file()


@pytest.mark.parametrize("n", [2048, 4096, 8192])
@pytest.mark.parametrize("hierarchical", [False, True])
def test_single_bin_and_general_pipeline_agree(n, hierarchical, monkeypatch):
    """Changing bin counts on a reused plan must select the right kernel."""
    import numpy as np
    _metal_or_skip()
    rng = np.random.default_rng(n)
    bank = (rng.normal(size=(7, n)) + 1j*rng.normal(size=(7, n))).astype('complex64')
    data = (rng.normal(size=(3, n)) + 1j*rng.normal(size=(3, n))).astype('complex64')
    bank /= np.linalg.norm(bank, axis=1, keepdims=True)
    if hierarchical:
        f = matchedfilter.HierarchicalFilter(n, 3, 7, band=256, device='gpu')
        f.set_coarse_threshold(0.)  # all pairs refine
    else:
        f = matchedfilter.MatchedFilter(n, 3, 7, device='gpu')
    f.set_templates(bank)
    f.set_data(data)
    pipeline = f._gpu.pipeline
    for threshold in (0., 5.5):
        for window in ((0, n), (7, n-3), (17, 18)):
            for binsize in (n, 257, n):
                monkeypatch.setattr(f._gpu, 'pipeline', pipeline)
                got = f.run(window=window, binsize=binsize, threshold=threshold).copy()
                monkeypatch.setattr(f._gpu, 'pipeline',
                    lambda size, entry='fusedTierB', one_bin=False: pipeline(size, entry))
                ref = f.run(window=window, binsize=binsize, threshold=threshold)
                np.testing.assert_array_equal(got['index'], ref['index'])
                np.testing.assert_allclose(got['value'], ref['value'], rtol=3e-5, atol=3e-5)


def test_metallib_presence_is_recorded(manifest):
    """Whether a compiled library shipped is a fact about the BUILD.

    It is built only where Apple's compiler exists, so on a Linux build it
    is absent and the manifest says so. What must not happen is the
    manifest claiming one that is not there -- the runtime would then load
    nothing and fail on the user's machine.
    """
    for info in manifest["modules"].values():
        for files in info["metal"].values():
            lib = files.get("metallib")
            if lib is not None:
                assert (METAL_DIR / lib).is_file(), \
                    "manifest claims %s but it is not in the package" % lib


def _metal_or_skip():
    """A live Metal device, or a skip that says why there is none."""
    import sys
    if sys.platform != "darwin":
        pytest.skip("Metal needs macOS")
    from matchedfilter import _metal
    ok, why = _metal.available()
    if not ok:
        pytest.skip(why or "no Metal device")
    from matchedfilter import _mtlcompute
    return _mtlcompute


def test_the_chosen_metal_kernel_fits_the_device(manifest):
    """Never select a Metal kernel asking for more threadgroup memory than exists.

    This had no coverage because its Vulkan twin skips on macOS with the
    reason "the Metal backend ships one library per size and has nothing to
    choose" -- which stopped being true when the portable 32 KB Metal builds
    were added. Metal has two variants at the top sizes and _stem picks
    between them, so there is very much a question here to answer, and the
    selection reads a manifest field (metal_lds_bytes) that is distinct from
    the Vulkan one. Getting it wrong does not return a wrong answer, it
    fails to create a pipeline at all, and Metal reports that as
    "Compilation failed" naming nothing.
    """
    M = _metal_or_skip()
    ctx = M.Context(0)
    try:
        for key, info in manifest["modules"].items():
            n = int(key)
            if n < 1024:
                continue
            stem = ctx._stem(n, "fusedTierB")
            need = (info.get("metal_lds_bytes", info["lds_bytes"])
                    if not stem.endswith("_lds32")
                    else info["metal"]["fusedTierB"]["portable"]["lds_bytes"])
            assert need <= ctx.max_shared_memory, (
                "n=%d picked %s needing %d KB with %d KB available"
                % (n, stem, need // 1024, ctx.max_shared_memory // 1024))
            # And it must actually build, which is the failure being guarded.
            ctx.pipeline(n)
    finally:
        ctx.destroy()


def test_apple_takes_the_full_32kb_staging_where_it_fits(manifest):
    """n=4096 must use the base build, not a portable one.

    The Metal staging cap was widened to CH=16 at 1024/2048/4096, which is
    2.01x at n=4096 on an M2 and lands on exactly 32 KB -- precisely Apple's
    limit. One byte more and _stem would quietly fall back to a portable
    variant that does not exist for these sizes, or to the Vulkan figure and
    pick wrong. This pins the fit.
    """
    _metal_or_skip()
    for n in (1024, 2048, 4096):
        info = manifest["modules"][str(n)]
        assert info["metal_lds_bytes"] <= 32768
        assert "portable" not in info["metal"]["fusedTierB"], (
            "n=%d gained a portable Metal variant; the base build no longer "
            "fits Apple and the CH=16 win is silently gone" % n)
    assert manifest["modules"]["4096"]["metal_lds_bytes"] == 32768
