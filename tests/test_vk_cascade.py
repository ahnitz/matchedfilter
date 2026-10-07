import numpy as np
import pytest

from matchedfilter import _vulkan, HierarchicalFilter, MatchedFilter

_devices, _reason = _vulkan.enumerate_devices()
novk = pytest.mark.skipif(not _devices, reason=_reason or "no Vulkan device")


@pytest.fixture(scope="module")
def ctx():
    from conftest import vulkan_runs
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)
    from matchedfilter import _vkcompute
    c = _vkcompute.Context(0)
    yield c
    c.destroy()


def make_data_and_templates(n, nd, nt, seed=42):
    rng = np.random.default_rng(seed)
    d = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    return d, h


@novk
def test_vk_cascade_direct(ctx):
    n = 4096
    b0 = 128
    b1 = 512
    nd, nt = 4, 8
    d, h = make_data_and_templates(n, nd, nt)

    # Inject strong signal into pair (1, 2) at lag 500
    lag = 500
    phase = np.exp(-2j * np.pi * np.arange(n) * lag / n).astype(np.complex64)
    d[1] += 50.0 * h[2] * phase

    ct0 = h[:, :b0]
    ct1 = h[:, :b1]

    # Thresholds tuned to filter noise but pass injection
    thr0 = 0.9
    thr1 = 2.0
    final_thr = 30.0

    idx, val = ctx.hier_peaks(
        n, b1, d, h, ct0, thr0,
        cascade_band=b0, ct1=ct1, raw_thr1=thr1,
        threshold=final_thr)

    # Injected pair (1, 2) must be detected at lag
    assert idx[1, 2, 0] == lag
    assert abs(val[1, 2, 0]) > final_thr

    # Other pairs in noise should be dismissed (-1)
    noise_idx = np.delete(idx.reshape(nd * nt), 1 * nt + 2)
    assert np.all(noise_idx == -1)

    # Verify survivor counters
    assert ctx.last_refinements == 1
    assert ctx.last_tier1_survivors == 1


@novk
def test_vk_cascade_async_submit(ctx):
    n = 4096
    b0 = 128
    b1 = 512
    nd, nt = 2, 4
    d, h = make_data_and_templates(n, nd, nt)

    ct0 = h[:, :b0]
    ct1 = h[:, :b1]

    rb = ctx.hier_peaks(
        n, b1, d, h, ct0, 0.0,
        cascade_band=b0, ct1=ct1, raw_thr1=0.0,
        threshold=0.0, slot=1, async_submit=True)

    idx_async, val_async = rb()
    idx_sync, val_sync = ctx.hier_peaks(
        n, b1, d, h, ct0, 0.0,
        cascade_band=b0, ct1=ct1, raw_thr1=0.0,
        threshold=0.0)

    np.testing.assert_array_equal(idx_async, idx_sync)
    np.testing.assert_allclose(val_async, val_sync, rtol=1e-5, atol=1e-5)


@novk
def test_hierarchical_gpu_cascade_vs_cpu():
    from conftest import vulkan_runs
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)

    n = 4096
    nd, nt = 4, 4
    d, h = make_data_and_templates(n, nd, nt, seed=123)

    # Inject signal in pair (2, 3) at lag 1200
    lag = 1200
    phase = np.exp(-2j * np.pi * np.arange(n) * lag / n).astype(np.complex64)
    d[2] += 40.0 * h[3] * phase

    # Pinned two-tier chain (128, 512)
    gpu_plan = HierarchicalFilter(n, nd, nt, snr=10.0, fd=1e-4, chain=(128, 512), device="gpu")
    cpu_plan = HierarchicalFilter(n, nd, nt, snr=10.0, fd=1e-4, chain=(128, 512), device="cpu")

    # Set explicit coarse thresholds (t0, t1)
    gpu_plan.set_coarse_threshold((0.9, 2.0))
    cpu_plan.set_coarse_threshold((0.9, 2.0))

    assert gpu_plan.config == (128, 512)
    assert cpu_plan.config == (128, 512)

    gpu_plan.set_data(d)
    gpu_plan.set_templates(h)
    cpu_plan.set_data(d)
    cpu_plan.set_templates(h)

    gpu_res = gpu_plan.run(threshold=25.0)
    cpu_res = cpu_plan.run(threshold=25.0)

    # Injected detection
    assert gpu_res[2, 3]["index"] == lag
    assert cpu_res[2, 3]["index"] == lag
    np.testing.assert_allclose(gpu_res[2, 3]["value"], cpu_res[2, 3]["value"], rtol=1e-4)

    # Other pairs dismissed
    for i in range(nd):
        for j in range(nt):
            if (i, j) != (2, 3):
                assert gpu_res[i, j]["index"] == -1
                assert cpu_res[i, j]["index"] == -1


@novk
def test_gpu_series_pipelined():
    from conftest import vulkan_runs
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)

    n = 4096
    nt = 2
    nblk = 32
    ser_len = (nblk + 1) * n
    rng = np.random.default_rng(999)
    ser = (rng.standard_normal(ser_len) + 1j * rng.standard_normal(ser_len)).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True)

    starts = np.arange(0, nblk * n, n, dtype=np.uint32)
    ws = np.zeros(nblk, dtype=np.uint32)
    we = np.full(nblk, n, dtype=np.uint32)

    # Test both flat and hierarchical cascade pipelining
    flat_gpu = MatchedFilter(n, 1, nt, device="gpu")
    flat_gpu.set_templates(h)
    res_flat = flat_gpu.run_series(ser, starts, ws, we)
    assert res_flat.shape == (nblk, nt, 1)

    hier_gpu = HierarchicalFilter(n, 1, nt, snr=10.0, fd=1e-4, chain=(128, 512), device="gpu")
    hier_gpu.set_coarse_threshold((0.9, 2.0))
    hier_gpu.set_templates(h)
    res_hier = hier_gpu.run_series(ser, starts, ws, we)
    assert res_hier.shape == (nblk, nt, 1)
