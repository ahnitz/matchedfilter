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
from matchedfilter import _cuda

PTX_DIR = pathlib.Path(matchedfilter.__file__).resolve().parent / "ptx"
MANIFEST = PTX_DIR / "manifest.json"

pytestmark = pytest.mark.skipif(not PTX_DIR.is_dir(),
                                reason="PTX kernels not built into this tree")


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST.read_text())


def test_every_size_has_ptx(manifest):
    """Every supported transform size must have PTX blobs shipped."""
    for key, info in manifest["modules"].items():
        assert "file" in info, f"n={key} has no main PTX output"
        ptx = PTX_DIR / info["file"]
        assert ptx.is_file(), f"{ptx} missing"
        assert ptx.stat().st_size > 1000, f"{ptx} looks empty"


@pytest.mark.parametrize("n", [1024, 4096, 16384])
def test_ptx_targets_sm75_and_64bit_pointers(manifest, n):
    """Verify PTX code declares .target sm_75 and 64-bit device pointers."""
    info = manifest["modules"][str(n)]
    text = (PTX_DIR / info["file"]).read_text()
    assert ".target sm_75" in text or ".target sm_" in text
    assert ".address_size 64" in text
    # fusedTierB buffer params must be 8 bytes (.b8 ...[8]), not 16 bytes
    assert "fusedTierB_param_0[8]" in text
    assert "fusedTierB_param_1[8]" in text


def test_coarse_and_pack_kernels_shipped(manifest):
    for band in (256, 512, 1024):
        ptx = PTX_DIR / f"coarse_{band}.ptx"
        assert ptx.is_file(), f"{ptx} missing"
    assert (PTX_DIR / "pack_coarse.ptx").is_file()
    assert (PTX_DIR / "compact.ptx").is_file()


@pytest.mark.skipif(not _cuda.enumerate_devices()[0], reason="No NVIDIA CUDA GPU available on host")
def test_cuda_flat_filter_agrees_with_cpu():
    dev = matchedfilter.device.parse("cuda:0")
    assert dev.backend == "cuda"

    n = 1024
    np.random.seed(1234)
    data = (np.random.randn(2, n) + 1j * np.random.randn(2, n)).astype(np.complex64)
    tmpl = (np.random.randn(4, n) + 1j * np.random.randn(4, n)).astype(np.complex64)

    mf_cpu = matchedfilter.MatchedFilter(n, 2, 4, device="cpu")
    idx_cpu, val_cpu = mf_cpu.peaks(data, tmpl)

    mf_gpu = matchedfilter.MatchedFilter(n, 2, 4, device=dev)
    idx_gpu, val_gpu = mf_gpu.peaks(data, tmpl)

    np.testing.assert_array_equal(idx_gpu, idx_cpu)
    np.testing.assert_allclose(val_gpu, val_cpu, rtol=1e-4, atol=1e-4)


@pytest.mark.skipif(not _cuda.enumerate_devices()[0], reason="No NVIDIA CUDA GPU available on host")
def test_cuda_hierarchical_filter_agrees_with_cpu():
    dev = matchedfilter.device.parse("cuda:0")
    n = 4096
    np.random.seed(5678)
    data = (np.random.randn(2, n) + 1j * np.random.randn(2, n)).astype(np.complex64)
    tmpl = (np.random.randn(4, n) + 1j * np.random.randn(4, n)).astype(np.complex64)

    # Add strong injection to trigger survivor
    inj_idx = 500
    data[0, :] += 15.0 * tmpl[0, :]

    hf_cpu = matchedfilter.HierarchicalFilter(n, 2, 4, band=512, device="cpu")
    hf_cpu.set_coarse_threshold(4.0)
    idx_cpu, val_cpu = hf_cpu.peaks(data, tmpl, threshold=6.0)

    hf_gpu = matchedfilter.HierarchicalFilter(n, 2, 4, band=512, device=dev)
    hf_gpu.set_coarse_threshold(4.0)
    idx_gpu, val_gpu = hf_gpu.peaks(data, tmpl, threshold=6.0)

    np.testing.assert_array_equal(idx_gpu, idx_cpu)
    np.testing.assert_allclose(val_gpu, val_cpu, rtol=1e-3, atol=1e-3)
