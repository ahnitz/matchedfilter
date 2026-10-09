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


@novk
@pytest.mark.parametrize("kind", ["peaks", "peaks_grouped", "hier", "hier_cascade"])
@pytest.mark.parametrize("level", ["mid", "zero"])     # mid: about a fifth of bins a peak
@pytest.mark.parametrize("gate", [0.0, 0.5])            # 0: every pair refined
def test_vk_sparse_readback_equals_dense(ctx, kind, level, gate):
    """sparse=True gives the dense result's peaks exactly; the hierarchical paths read only
    the refined pairs (survivor list) back, relying on the refine writing every bin of them."""
    from matchedfilter import _SparsePeaks
    n, nd, nt, bs = 2048, 24, 9, 512
    rng = np.random.default_rng(17)
    spec = ctx.empty_shared((nd, n))
    spec[:] = ((rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n)))
               / np.sqrt(2 * n)).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True) / np.sqrt(n)
    groups = [(0, 2000, 0, 3), (40, 2040, 3, 20), (10, 2010, 20, 24)]

    def call(sparse):
        if kind == "peaks":
            return ctx.peaks(n, spec, h, binsize=bs, threshold=thr, window=(40, 2040), sparse=sparse)
        if kind == "peaks_grouped":
            return ctx.peaks_grouped(n, spec, h, groups, bs, thr, sparse=sparse)
        if kind == "hier":
            return ctx.hier_peaks(n, 512, spec, h, h[:, :512], gate, binsize=bs, threshold=thr,
                                  window=(40, 2040), sparse=sparse)
        return ctx.hier_peaks(n, 512, spec, h, h[:, :128], gate, cascade_band=128, ct1=h[:, :512],
                              raw_thr1=2 * gate, binsize=bs, threshold=thr, window=(40, 2040),
                              sparse=sparse)
    thr = 0.0
    if level == "mid":
        thr = float(np.quantile(np.abs(call(False)[1]), 0.8))
    di, dv = call(False)
    sp = call(True)
    assert isinstance(sp, _SparsePeaks) and sp.shape == di.shape
    si, sv = sp.dense()
    np.testing.assert_array_equal(si, di)
    np.testing.assert_array_equal(sv, dv)
    if gate == 0.0 or kind.startswith("peaks"):
        assert 0 < sp.flat.size < di.size if level == "mid" else sp.flat.size == di.size


def test_fused_cache_key_is_not_a_command_buffer_handle():
    """A fused recording is cached by its constituents' serials, not their handles: an
    evicted recording's handle value is reused by the next one, and a handle-keyed cache
    resubmitted commands naming the evicted recording's freed buffers (GPU page faults)."""
    from types import SimpleNamespace
    from matchedfilter import _vkcompute as V
    ctx = SimpleNamespace(device=object(), _phases={0xabc: {"_serial": next(V._RECORDING_SERIAL)}})
    before = V._fused_key([(ctx, [0xabc])])
    serial = before[0][1]
    assert V._fused_valid(ctx, [0xabc], serial)
    # Evicted, and the same handle value registered again for a new recording.
    ctx._phases[0xabc] = {"_serial": next(V._RECORDING_SERIAL)}
    assert V._fused_key([(ctx, [0xabc])]) != before
    assert not V._fused_valid(ctx, [0xabc], serial)
    del ctx._phases[0xabc]
    assert not V._fused_valid(ctx, [0xabc], serial)
