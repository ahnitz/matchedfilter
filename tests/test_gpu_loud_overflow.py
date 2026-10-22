"""A loud signal must never be gated out by a narrow tier that overflows.

The packed fp16 coarse tier overflows once |v|^2 passes 65504 (and inf - inf = NaN inside
the transform). It must FAIL OPEN: the loud pair passes and the refine, in fp32, reports
it. A regression made the overflowed value a NaN that compared false against the gate,
and Vulkan returned 0 peaks for a batch where the CPU returned 62 (SNR >= 2500).
"""
import numpy as np
import pytest
from conftest import usable_gpu_reason

import matchedfilter as mf


def _gpu():
    from conftest import usable_gpu
    dev = usable_gpu()
    if dev is None:
        pytest.skip(usable_gpu_reason())
    return dev


@pytest.fixture(params=["measured", "t1", "t2", "t4", "t8"])
def builds(request, monkeypatch):
    """The device's measured coarse layout, or one with each tile forced (t1 = untiled) at
    every band the device has one: any of them can be a device's choice, so each must fail
    open. Returns a function of the chain that sets MF_COARSE_LAYOUT."""
    def force(chain):
        if request.param == "measured":
            return
        from conftest import forced_coarse_layouts, gpu_backend, gpu_context
        tile = int(request.param[1:])
        ctx = gpu_context(gpu_backend())
        try:
            value = forced_coarse_layouts(ctx, chain, lambda f: f[2] == tile)
        finally:
            ctx.destroy()
        if not value:
            pytest.skip("no tile-%d coarse layout at %s on this device" % (tile, chain))
        monkeypatch.setenv("MF_COARSE_LAYOUT", value)
    return force


@pytest.mark.parametrize("chain", [(64,), (128,), (256,), (512,), (1024,), (2048,),
                                   (128, 512), (256, 1024)])
@pytest.mark.parametrize("snr", [2000, 3000, 1e5])
def test_loud_injection_matches_cpu(chain, snr, builds):
    dev = _gpu()
    builds(chain)
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
