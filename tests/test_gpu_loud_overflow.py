"""A loud signal must never be gated out by a narrow tier that overflows.

The packed fp16 coarse tier overflows once |v|^2 passes 65504 (and inf - inf = NaN inside
the transform). It must FAIL OPEN: the loud pair passes and the refine, in fp32, reports
it. A regression made the overflowed value a NaN that compared false against the gate,
and Vulkan returned 0 peaks for a batch where the CPU returned 62 (SNR >= 2500).
"""
import numpy as np
import pytest

import matchedfilter as mf


def _gpu():
    from conftest import usable_gpu
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    return dev


@pytest.fixture(params=["tiled", "untiled"])
def builds(request, monkeypatch):
    if request.param == "untiled":
        try:
            from matchedfilter import _vkcompute
        except Exception:
            pytest.skip("Vulkan build families only")
        monkeypatch.setattr(_vkcompute, "_COARSE_TILE_T", {})
    return request.param


@pytest.mark.parametrize("chain", [(64,), (128,), (256,), (512,), (1024,), (2048,),
                                   (128, 512), (256, 1024)])
@pytest.mark.parametrize("snr", [2000, 3000, 1e5])
def test_loud_injection_matches_cpu(chain, snr, builds):
    dev = _gpu()
    from matchedfilter.benchmark import _inspiral_power
    n, nd, nt = 4096, 4, 16
    power = _inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)
    rng = np.random.default_rng(2026)
    tm = (h * np.exp(2j * np.pi * rng.random((nt, n)) * 0.05)).astype(np.complex64)
    data = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    data[1] += snr * np.conj(tm[3]) / np.linalg.norm(tm[3]) * np.sqrt(n)
    got = []
    for d in (None, dev):
        hf = mf.HierarchicalFilter(n, nd, nt, chain=chain, snr=5.5, fd=1e-3, device=d)
        hf.set_reference(power)
        hf.set_templates(np.conj(tm))
        hf.set_data(data)
        got.append(hf.run(binsize=n // 4, threshold=6.0 * np.sqrt(n)))
    cpu, gpu = got
    assert (cpu["index"] >= 0).sum() > 0
    np.testing.assert_array_equal(cpu["index"], gpu["index"])
