"""The subgroup size Vulkan pipelines are built at never splits a workgroup into more
subgroups than the device allows (maxComputeWorkgroupSubgroups).

On an Iris Xe (sizes 8-32, at most 64 subgroups per workgroup) requiring 8 for the
1024-invocation transforms lost the device. The limit is read from the driver and every
required size -- measured, forced or a coarse layout's -- is raised past it.
"""
import pytest

from matchedfilter import _vkcompute
from matchedfilter._vkcompute import _SPIRV, _fit_workgroup, _module_invocations


def test_module_invocations_reads_local_size():
    seen = {}
    for name in ("forward_64.spv", "forward_16384.spv", "full_8192.spv"):
        path = _SPIRV / name
        if path.exists():
            seen[name] = _module_invocations(path.read_bytes())
    if not seen:
        pytest.skip("no shipped SPIR-V")
    expect = {"forward_64.spv": 4, "forward_16384.spv": 1024, "full_8192.spv": 512}
    assert seen == {k: expect[k] for k in seen}


def test_every_shipped_module_declares_its_size():
    # The limit can only be enforced for modules whose size the parser finds.
    names = sorted(_SPIRV.glob("*.spv"))
    if not names:
        pytest.skip("no shipped SPIR-V")
    assert all(_module_invocations(p.read_bytes()) > 0 for p in names)


@pytest.mark.parametrize("sg, inv, rng, lim, want", [
    (8, 1024, (8, 32), 64, 16),     # Iris Xe: 128 subgroups -> 16
    (8, 512, (8, 32), 64, 8),       # 64 subgroups fit
    (8, 1024, (8, 32), 32, 32),     # only the top of the range fits
    (8, 1024, (8, 8), 16, 8),       # nothing in range fits: leave it (driver default rules)
    (32, 1024, (32, 64), 0, 32),    # limit unknown
    (64, 1024, (32, 64), 32, 64),
])
def test_fit_workgroup(sg, inv, rng, lim, want):
    assert _fit_workgroup(sg, inv, rng, lim) == want


def test_smallest_size_runs_the_largest_transforms(monkeypatch):
    """Forcing the device's smallest size through a 1024-invocation transform (full
    correlation at N=2^16) runs and matches numpy: the builder raises the size where the
    group would exceed the limit instead of losing the device."""
    import numpy as np
    from matchedfilter import _vulkan
    devices, reason = _vulkan.enumerate_devices()
    if not devices:
        pytest.skip(reason or "no Vulkan device")
    from conftest import vulkan_runs
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)
    c = _vkcompute.Context(0)
    if not c.subgroup_range:
        pytest.skip("device cannot require a subgroup size")
    monkeypatch.setenv("MF_VK_SUBGROUP", str(c.subgroup_range[0]))
    import matchedfilter as mf
    n = 1 << 16
    rng = np.random.default_rng(3)
    t = (rng.standard_normal((2, n)) + 1j * rng.standard_normal((2, n))).astype(np.complex64)
    d = (rng.standard_normal((1, n)) + 1j * rng.standard_normal((1, n))).astype(np.complex64)
    f = mf.CorrelationFilter(n, 1, 2, device="gpu:0")
    f.set_templates(t)
    f.set_data(d)
    out = np.asarray(f.run())[0]
    ref = np.fft.ifft(np.conj(t) * d, axis=-1) * n
    assert np.allclose(out, ref, rtol=1e-3, atol=1e-3 * np.abs(ref).max())
