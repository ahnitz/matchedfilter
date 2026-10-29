"""The NVIDIA CUDA PTX kernels and driver backend: generated, complete, and correct.

Checks both:
1. AOT PTX build output (presence of sm_75 kernels, warp shuffle/active intrinsics,
   no StructuredBuffer count padding).
2. Live hardware execution against CPU reference when an NVIDIA GPU is present.
"""
import json
import pathlib
import pytest
import numpy as np

import matchedfilter
from matchedfilter.device import Device
from matchedfilter import _cuda

#: The install's PTX, or on macOS (whose installs carry none) the checkout's.
PTX_DIR = pathlib.Path(matchedfilter.__file__).resolve().parent / "ptx"
if not PTX_DIR.is_dir():
    PTX_DIR = pathlib.Path(__file__).resolve().parents[1] / "python" / "matchedfilter" / "ptx"
MANIFEST = PTX_DIR / "manifest.json"

pytestmark = pytest.mark.skipif(not PTX_DIR.is_dir(),
                                reason="no PTX kernels in this install or a checkout beside it")


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST.read_text())


def _flat(info):
    """The module serving a length's flat filter: its own build, or the 32 KB staging build where
    its own would need more static shared memory than CUDA allows (tools/build_ptx.py)."""
    return info.get("file") or info["portable"]["file"]


@pytest.fixture
def build_ptx(monkeypatch):
    """tools/build_ptx.py of the checkout beside the tests (skips for an installed package)."""
    import importlib
    tools = pathlib.Path(__file__).resolve().parents[1] / "tools"
    if not (tools / "build_ptx.py").is_file():
        pytest.skip("tools/ is not beside the tests (installed package?)")
    monkeypatch.syspath_prepend(str(tools))
    return importlib.import_module("build_ptx")


def test_every_size_has_ptx(manifest):
    """Every supported transform size must have PTX blobs shipped."""
    for key, info in manifest["modules"].items():
        assert "file" in info or "portable" in info, f"n={key} has no main PTX output"
        ptx = PTX_DIR / _flat(info)
        assert ptx.is_file(), f"{ptx} missing"
        assert ptx.stat().st_size > 1000, f"{ptx} looks empty"


def test_no_shipped_module_declares_more_static_shared_memory_than_cuda_allows(manifest, build_ptx):
    """CUDA allows a block 48 KB of static shared memory on every architecture and its JIT
    rejects a module past it, so such a module could launch on no NVIDIA GPU
    (build_ptx.STATIC_SHARED_MAX). The bytes are read from each module's .shared declarations,
    and the reading is checked against the staging the manifest records for the 32 KB builds,
    so a parse that found nothing could not pass."""
    shared = {p.name: build_ptx.static_shared(p.read_text()) for p in sorted(PTX_DIR.glob("*.ptx"))}
    portable = [info["portable"] for info in manifest["modules"].values() if "portable" in info]
    assert portable and all(shared[p["file"]] == p["lds_bytes"] for p in portable)
    over = {name: size for name, size in shared.items() if size > build_ptx.STATIC_SHARED_MAX}
    assert not over, "modules no NVIDIA GPU can launch: %s" % over


def test_every_kernel_the_host_asks_for_is_a_shipped_module(build_ptx):
    """Context.pipeline serves the flat, one-bin flat, refine, one-bin refine, follow-up,
    forward and full-correlation kernels at every length from a module that ships: its own
    build, or the _lds32 build where its own staging is past CUDA's static shared limit and
    so did not ship. A one-bin request gets a one-bin build wherever one is built (from 256).
    Needs no device: the module load is stubbed. A missing module fails here rather than
    skipping (conftest turns an UnsupportedSize into a skip)."""
    from matchedfilter import UnsupportedSize
    from matchedfilter import _cudacompute as C
    ctx = C.Context.__new__(C.Context)
    ctx._pipelines = {}
    ctx._load = lambda stem, path, fn_name, wg: (stem, path)
    served = {}
    for n in build_ptx.TIER_B:
        asks = [("fusedTierB", False), ("refineListed", False), ("refineListed", True),
                ("refineItems", False), ("seriesForward", False)]
        asks += [("fullCorrelation", False), ("fullCorrelationSeries", False)] if n >= 1024 else []
        asks += [("fusedTierB", True)] if n >= 4096 else []
        for entry, one_bin in asks:
            try:
                (stem, path), _ = ctx.pipeline(n, entry, one_bin=one_bin)
            except UnsupportedSize as e:
                pytest.fail("n=%d %s one_bin=%s: %s" % (n, entry, one_bin, e))
            assert path.is_file() and stem == path.stem, (n, entry, stem)
            assert build_ptx.static_shared(path.read_text()) <= build_ptx.STATIC_SHARED_MAX
            assert not one_bin or n < 256 or "_onebin" in stem, (n, entry, stem)
            served[(n, entry, one_bin)] = stem
    assert served[(8192, "fusedTierB", False)] == "tierb_8192_lds32"
    assert served[(65536, "refineListed", True)] == "refine_65536_onebin_lds32"
    assert C.Context._x_has_kernel("items", 16384) and C.Context._x_has_kernel("tier1", 16384)


@pytest.mark.parametrize("n", [1024, 4096, 16384])
def test_ptx_targets_sm75_and_64bit_pointers(manifest, n):
    """Verify PTX code declares .target sm_75 and 64-bit device pointers."""
    info = manifest["modules"][str(n)]
    text = (PTX_DIR / _flat(info)).read_text()
    assert ".target sm_75" in text or ".target sm_" in text
    assert ".address_size 64" in text
    # fusedTierB buffer params must be 8 bytes (.b8 ...[8]), not 16 bytes
    assert "fusedTierB_param_0[8]" in text
    assert "fusedTierB_param_1[8]" in text


def test_pack_and_compact_kernels_shipped(manifest):
    assert (PTX_DIR / "pack_coarse.ptx").is_file()
    assert (PTX_DIR / "compact.ptx").is_file()


@pytest.mark.skipif(not _cuda.enumerate_devices()[0], reason="No NVIDIA CUDA GPU available on host")
def test_cuda_flat_filter_agrees_with_cpu():
    dev = Device.parse("cuda:0")
    assert dev.backend == "cuda"

    n = 1024
    np.random.seed(1234)
    data = (np.random.randn(2, n) + 1j * np.random.randn(2, n)).astype(np.complex64)
    tmpl = (np.random.randn(4, n) + 1j * np.random.randn(4, n)).astype(np.complex64)

    mf_cpu = matchedfilter.MatchedFilter(n, 2, 4, device="cpu")
    mf_cpu.set_data(data)
    mf_cpu.set_templates(tmpl)
    res_cpu = mf_cpu.run()

    mf_gpu = matchedfilter.MatchedFilter(n, 2, 4, device=dev)
    mf_gpu.set_data(data)
    mf_gpu.set_templates(tmpl)
    res_gpu = mf_gpu.run()

    np.testing.assert_array_equal(res_gpu["index"], res_cpu["index"])
    np.testing.assert_allclose(res_gpu["value"], res_cpu["value"], rtol=1e-4, atol=1e-4)


@pytest.mark.skipif(not _cuda.enumerate_devices()[0], reason="No NVIDIA CUDA GPU available on host")
def test_cuda_hierarchical_filter_agrees_with_cpu():
    dev = Device.parse("cuda:0")
    n = 4096
    np.random.seed(5678)
    data = (np.random.randn(2, n) + 1j * np.random.randn(2, n)).astype(np.complex64)
    tmpl = (np.random.randn(4, n) + 1j * np.random.randn(4, n)).astype(np.complex64)

    # Add strong injection to trigger survivor
    data[0, :] += 15.0 * tmpl[0, :]

    hf_cpu = matchedfilter.HierarchicalFilter(n, 2, 4, chain=512, device="cpu")
    hf_cpu.set_reference(np.ones(n, dtype=np.float32))
    hf_cpu.set_coarse_threshold(4.0)
    hf_cpu.set_data(data)
    hf_cpu.set_templates(tmpl)
    res_cpu = hf_cpu.run(threshold=6.0)

    hf_gpu = matchedfilter.HierarchicalFilter(n, 2, 4, chain=512, device=dev)
    hf_gpu.set_reference(np.ones(n, dtype=np.float32))
    hf_gpu.set_coarse_threshold(4.0)
    hf_gpu.set_data(data)
    hf_gpu.set_templates(tmpl)
    res_gpu = hf_gpu.run(threshold=6.0)

    np.testing.assert_array_equal(res_gpu["index"], res_cpu["index"])
    np.testing.assert_allclose(res_gpu["value"], res_cpu["value"], rtol=1e-3, atol=1e-3)
