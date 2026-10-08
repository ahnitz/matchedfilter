"""Metal backend: the guarantees the Vulkan tests give, on Apple hardware.

The mocked tests run everywhere and pin what is DISPATCHED; the hardware
tests run where a Metal device exists and compare against the CPU.
"""
import os
import re
import pathlib
import subprocess
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _mtlcompute


# --- mocked: what a two-tier chain dispatches -------------------------------
class _Buf:
    def __init__(self, ctx=None, nbytes=16):
        self.nbytes = nbytes
        self.handle = object()
        self.value = None

    def write(self, value):
        self.value = np.asarray(value).copy()

    def read(self, dtype, count):
        return np.zeros(count, dtype=dtype)

    def destroy(self):
        pass


@pytest.fixture
def mock_ctx(monkeypatch):
    monkeypatch.setattr(_mtlcompute, "_Buffer", _Buf)
    c = _mtlcompute.Context.__new__(_mtlcompute.Context)
    c._batches, c._hier, c._inflight = {}, {}, {}
    c._uploaded = {"data": {}, "tmpl": {}}
    c._pipelines = {}
    c.queue = None
    c.o = SimpleNamespace(call=lambda *a, **k: None, autorelease_pool=nullcontext)
    c.pipeline = lambda n, entry="fusedTierB", one_bin=False, c16=False: (n, entry, one_bin)
    c._check_completed = lambda *a: None
    c._record_gpu_time = lambda *a: None
    c.dispatched = []

    def dispatch(enc, pso, params, buffers, tg, groups=None, indirect=None):
        c.dispatched.append(dict(pso=pso, params=tuple(params), tg=tg, groups=groups,
                                 indirect=indirect is not None))
    c._dispatch = dispatch
    return c


def test_metal_two_tier_chain_runs_both_tiers(mock_ctx):
    """The cascade used to collapse to its second tier with its threshold."""
    n, b0, b1 = 4096, 128, 512
    d = np.ones((2, n), np.complex64)
    h = np.ones((3, n), np.complex64)
    mock_ctx.hier_peaks(n, b1, d, h, h[:, :b0], 0.25, cascade_band=b0,
                        ct1=h[:, :b1], raw_thr1=0.75, threshold=5.0)
    # The coarse entry may carry a pairs-per-group suffix (coarse16p8).
    kinds = [(x["pso"][0], "coarse16" if x["pso"][1].startswith("coarse16") else x["pso"][1])
             for x in mock_ctx.dispatched]
    coarse = "coarse16" if _mtlcompute._use_c16(b0) else "fusedTierB"
    assert kinds == [(b0, coarse), (b0, "compactPairs"), (b1, "refineListed"),
                     (b0, "compactPairs"), (n, "refineListed")]
    # Each tier is gated by its own threshold, in order.
    thr = [np.uint32(x["params"][1]).view(np.float32) for x in mock_ctx.dispatched
           if x["pso"][1] == "compactPairs"]
    assert thr == [np.float32(0.25), np.float32(0.75)]
    # The second tier and the refine run over the device-side survivor lists.
    assert [x["indirect"] for x in mock_ctx.dispatched] == [False, False, True, False, True]
    bufs = next(iter(mock_ctx._hier.values()))
    np.testing.assert_array_equal(bufs["ct1"].value, h[:, :b1])
    np.testing.assert_array_equal(bufs["cval1"].value, 0)


def test_metal_one_tier_chain_is_unchanged(mock_ctx):
    n, b = 4096, 256
    d = np.ones((1, n), np.complex64)
    h = np.ones((2, n), np.complex64)
    mock_ctx.hier_peaks(n, b, d, h, h[:, :b], 0.5)
    assert [("coarse16" if x["pso"][1].startswith("coarse16") else x["pso"][1])
            for x in mock_ctx.dispatched] == [
        "coarse16" if _mtlcompute._use_c16(b) else "fusedTierB", "compactPairs", "refineListed"]


def test_metal_incomplete_cascade_raises(mock_ctx):
    n = 4096
    d = np.ones((1, n), np.complex64)
    h = np.ones((1, n), np.complex64)
    with pytest.raises(ValueError):
        mock_ctx.hier_peaks(n, 512, d, h, h[:, :128], 0.5, cascade_band=128)
    with pytest.raises(ValueError):
        mock_ctx.hier_peaks(n, 128, d, h, h[:, :512], 0.5, cascade_band=512,
                            ct1=h[:, :128], raw_thr1=0.5)


def test_async_submission_is_deferred_and_keyed_by_slot(mock_ctx):
    n, b = 4096, 256
    d = np.ones((1, n), np.complex64)
    h = np.ones((1, n), np.complex64)
    pend = [mock_ctx.hier_peaks(n, b, d, h, h[:, :b], 0.5, slot=s, async_submit=True)
            for s in (0, 1)]
    # Nothing was waited on: both are in flight, each with its own buffers.
    assert all(isinstance(p, _mtlcompute._Pending) for p in pend)
    assert len(mock_ctx._inflight) == 2 and len(mock_ctx._hier) == 2
    pend[0]()
    assert len(mock_ctx._inflight) == 1
    mock_ctx._drain()
    assert not mock_ctx._inflight
    assert pend[1].done


def test_series_pipelining_is_a_declared_capability():
    from matchedfilter import _vkcompute, _cudacompute
    assert _mtlcompute.Context.supports_async and _vkcompute.Context.supports_async
    assert not getattr(_cudacompute.Context, "supports_async", False)


def test_no_signature_probing_retries_in_the_dispatch_path():
    """A TypeError raised after a submit used to be retried: the same work twice."""
    root = pathlib.Path(mf.__file__).parent
    for name in ("__init__.py", "_mtlcompute.py", "_vkcompute.py"):
        text = (root / name).read_text()
        for m in re.finditer(r"except TypeError:\n(.*\n){1,3}", text):
            assert "_submit" not in m.group(0) and "dispatch" not in m.group(0) \
                and "forward" not in m.group(0) and "peaks" not in m.group(0), m.group(0)


def _threadgroup_bytes(source):
    sizes = {"uint": 4, "int": 4, "float": 4, "float2": 8, "half2": 4, "uint2": 8}
    seen, total = set(), 0
    for m in re.finditer(r"array<\s*(\w+)\s*,\s*int\(\s*(\d+)\s*\)\s*>\s+threadgroup\s*\*\s*(\w+)",
                         source):
        if m.group(3) not in seen:
            seen.add(m.group(3))
            total += sizes[m.group(1)] * int(m.group(2))
    return total


@pytest.mark.parametrize("n", [64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536])
def test_every_selectable_metal_kernel_fits_32k_of_threadgroup_memory(n):
    """Apple allows a threadgroup 32 KB. The variant the runtime picks must fit.

    Read from the generated source rather than the manifest, so a manifest
    that disagrees with its kernels cannot hide an oversized variant.
    """
    c = _mtlcompute.Context.__new__(_mtlcompute.Context)
    c.max_shared_memory = 32768
    c.name = "32 KB device"
    entries = ["fusedTierB", "refineListed", "compactPairs", "seriesForward"]
    if n >= 1024:
        entries += ["fullCorrelation", "fullCorrelationSeries"]
    if (_mtlcompute._METAL_DIR / ("tierb_%d_c16.metal" % n)).is_file():
        entries.append("coarse16")
    info = _mtlcompute._manifest()["modules"][str(n)]
    for entry in entries:
        stem = c._stem(n, entry)
        src = (_mtlcompute._METAL_DIR / (stem + ".metal")).read_text()
        assert _threadgroup_bytes(src) <= 32768, (stem, _threadgroup_bytes(src))
    for entry, one in ((e, info.get("metal", {}).get(e, {}).get("one_bin")) for e in
                       ("fusedTierB", "refineListed")):
        if one:
            src = (_mtlcompute._METAL_DIR / one["msl"]).read_text()
            assert (_threadgroup_bytes(src) <= 32768) == (one["lds_bytes"] <= 32768)
            assert _threadgroup_bytes(src) == one["lds_bytes"]


# --- hardware ---------------------------------------------------------------
def _metal_ok():
    if sys.platform != "darwin":
        return False, "Metal is only available on macOS"
    from matchedfilter import _metal
    return _metal.available()


_OK, _WHY = _metal_ok()
metal = pytest.mark.skipif(not _OK, reason=_WHY or "no Metal device")


@pytest.fixture(scope="module")
def ctx():
    c = _mtlcompute.Context(0)
    yield c
    c.destroy()


def _bank(n, nd, nt, seed=42):
    rng = np.random.default_rng(seed)
    d = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    return d, h


@metal
def test_metal_cascade_direct(ctx):
    n, b0, b1, nd, nt = 4096, 128, 512, 4, 8
    d, h = _bank(n, nd, nt)
    lag = 500
    d[1] += 50.0 * h[2] * np.exp(-2j * np.pi * np.arange(n) * lag / n).astype(np.complex64)
    idx, val = ctx.hier_peaks(n, b1, d, h, h[:, :b0], 0.9, cascade_band=b0,
                              ct1=h[:, :b1], raw_thr1=2.0, threshold=30.0)
    assert idx[1, 2, 0] == lag and abs(val[1, 2, 0]) > 30.0
    assert np.all(np.delete(idx.reshape(-1), nt + 2) == -1)
    assert ctx.last_refinements == 1 and ctx.last_tier1_survivors == 1


@metal
def test_metal_tier_one_gate_is_applied(ctx):
    """Tier 0 passes everything; tier 1 alone must decide who is refined."""
    n, b0, b1, nd, nt = 4096, 128, 512, 2, 4
    d, h = _bank(n, nd, nt, seed=5)
    flat_i, flat_v = ctx.peaks(n, d, h)
    ctx.hier_peaks(n, b1, d, h, h[:, :b0], 0.0, cascade_band=b0, ct1=h[:, :b1],
                   raw_thr1=1e10)
    assert ctx.last_tier1_survivors == nd * nt and ctx.last_refinements == 0
    idx, val = ctx.hier_peaks(n, b1, d, h, h[:, :b0], 0.0, cascade_band=b0, ct1=h[:, :b1],
                              raw_thr1=0.0)
    assert ctx.last_refinements == nd * nt
    np.testing.assert_array_equal(idx, flat_i)
    np.testing.assert_allclose(val, flat_v, rtol=1e-5, atol=1e-6)


@metal
def test_metal_cascade_async_matches_sync(ctx):
    n, b0, b1 = 4096, 128, 512
    d, h = _bank(n, 2, 4)
    kw = dict(cascade_band=b0, ct1=h[:, :b1], raw_thr1=0.0, threshold=0.0)
    pend = [ctx.hier_peaks(n, b1, d, h, h[:, :b0], 0.0, slot=s, async_submit=True, **kw)
            for s in range(3)]
    sync = ctx.hier_peaks(n, b1, d, h, h[:, :b0], 0.0, **kw)
    for p in pend:
        got = p()
        np.testing.assert_array_equal(got[0], sync[0])
        np.testing.assert_allclose(got[1], sync[1], rtol=1e-5, atol=1e-5)


@metal
def test_metal_two_tier_public_api_matches_cpu():
    n, nd, nt = 4096, 4, 4
    d, h = _bank(n, nd, nt, seed=123)
    lag = 1200
    d[2] += 40.0 * h[3] * np.exp(-2j * np.pi * np.arange(n) * lag / n).astype(np.complex64)
    plans = [mf.HierarchicalFilter(n, nd, nt, snr=10.0, fd=1e-4, chain=(128, 512), device=dev)
             for dev in ("gpu", "cpu")]
    for p in plans:
        p.set_coarse_threshold((0.9, 2.0))
        assert p.config == (128, 512)
        p.set_data(d)
        p.set_templates(h)
    g, c = (p.run(threshold=25.0) for p in plans)
    np.testing.assert_array_equal(g["index"], c["index"])
    assert g[2, 3]["index"] == lag
    np.testing.assert_allclose(g[2, 3]["value"], c[2, 3]["value"], rtol=1e-5)


@metal
def test_metal_pinned_three_tier_chain_is_refused():
    with pytest.raises(ValueError):
        mf.HierarchicalFilter(4096, 1, 1, chain=(64, 128, 512), device="gpu")


@metal
@pytest.mark.parametrize("chain", [(256,), (128, 512)])
def test_metal_pipelined_series_values_match_cpu(chain):
    """Many batches in flight (K=8 slots, more batches than slots)."""
    n, nt, nblk = 4096, 2, 40
    rng = np.random.default_rng(999)
    ser = (rng.standard_normal((nblk + 1) * n)
           + 1j * rng.standard_normal((nblk + 1) * n)).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    starts = np.arange(0, nblk * n, n, dtype=np.uint32)
    ws = np.zeros(nblk, np.uint32)
    we = np.full(nblk, n, np.uint32)
    out = {}
    for dev in ("cpu", "gpu"):
        flat = mf.MatchedFilter(n, 1, nt, device=dev)
        flat.set_templates(h)
        hier = mf.HierarchicalFilter(n, 1, nt, snr=10.0, fd=1e-4, chain=chain, device=dev)
        hier.set_coarse_threshold(tuple(0.0 for _ in chain))
        hier.set_templates(h)
        if dev == "gpu":
            hier.set_memory_limits(series_bytes=4 * (8 * n + 4 + 12 * nt))  # 4 blocks a batch
            flat.set_memory_limits(series_bytes=4 * (8 * n + 4 + 12 * nt))
        out[dev] = [f.run_series(ser, starts, ws, we).copy() for f in (flat, hier)]
    for g, c in zip(out["gpu"], out["cpu"]):
        np.testing.assert_array_equal(g["index"], c["index"])
        scale = np.abs(c["value"]).max()
        assert np.abs(g["value"] - c["value"]).max() / scale < 1e-5


@metal
@pytest.mark.parametrize("binsize", [1, 127, 2048])
def test_metal_first_dispatch_and_changing_survivor_counts(binsize):
    n = 2048
    rng = np.random.default_rng(641)
    d = (rng.normal(size=(2, n)) + 1j * rng.normal(size=(2, n))).astype(np.complex64)
    h = (rng.normal(size=(3, n)) + 1j * rng.normal(size=(3, n))).astype(np.complex64)
    flat = mf.MatchedFilter(n, 2, 3, device="cpu")
    hier = mf.HierarchicalFilter(n, 2, 3, chain=256, device="gpu")
    for f in (flat, hier):
        f.set_data(d)
        f.set_templates(h)
    want = flat.run(binsize=binsize).copy()
    total = refined = 0
    for coarse in (0., 1e10, 0., 1e10, 0.):
        hier.set_coarse_threshold(coarse)
        got = hier.run(binsize=binsize)
        total += 6
        refined += 0 if coarse else 6
        assert hier.stats == (total, refined)
        if coarse:
            assert (got["index"] == -1).all() and (got["value"] == 0).all()
        else:
            np.testing.assert_array_equal(got["index"], want["index"])
            assert (np.abs(got["value"] - want["value"]).max()
                    / np.abs(want["value"]).max()) < 1e-5


@metal
@pytest.mark.parametrize("n", [2048, 4096, 8192])
@pytest.mark.parametrize("hierarchical", [False, True])
def test_metal_one_bin_and_general_kernels_agree(n, hierarchical, monkeypatch):
    rng = np.random.default_rng(n)
    d = (rng.normal(size=(3, n)) + 1j * rng.normal(size=(3, n))).astype(np.complex64)
    h = (rng.normal(size=(2, n)) + 1j * rng.normal(size=(2, n))).astype(np.complex64)
    filters = []
    for specialized in (False, True):
        f = (mf.HierarchicalFilter(n, 3, 2, chain=256, device="gpu") if hierarchical
             else mf.MatchedFilter(n, 3, 2, device="gpu"))
        if hierarchical:
            f.set_coarse_threshold(0.)
        f.set_templates(h)
        f.set_data(d)
        if not specialized:
            real = f._gpu.pipeline
            f._gpu.pipeline = (lambda n_, entry="fusedTierB", one_bin=False, c16=False,
                               real=real: real(n_, entry, False, c16))
        filters.append(f)
    for window in [(0, n), (11, n - 17)]:
        for threshold in (0., 1e10):
            a, b = [f.run(window=window, threshold=threshold).copy() for f in filters]
            np.testing.assert_array_equal(a, b)


@metal
def test_metal_timing_log_contract():
    code = ("import numpy as np, matchedfilter as mf\n"
            "f = mf.MatchedFilter(2048, 2, 3, device='gpu')\n"
            "f.set_data(np.ones((2, 2048), np.complex64)); f.set_templates(np.ones((3, 2048), np.complex64))\n"
            "f.run(); f.run()\n"
            "from matchedfilter import _gputime\n"
            "assert f._gpu in _gputime._CONTEXTS\n"
            "log = f._gpu.timings()\n"
            "assert len(log) == 2 and all(lab == 'flat' and ms > 0 for lab, ms in log), log\n"
            "print('ok')\n")
    env = dict(os.environ, MF_GPU_TIMING="1")
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert r.returncode == 0 and "ok" in r.stdout, r.stderr
    f = mf.MatchedFilter(2048, 1, 1, device="gpu")
    f.set_data(np.ones((1, 2048), np.complex64))
    f.set_templates(np.ones((1, 2048), np.complex64))
    if os.environ.get("MF_GPU_TIMING", "") in ("", "0"):
        f.run()
        assert f._gpu.timing_log == []


def test_coarse_packing_fills_a_simd_group():
    for band in (64, 128, 256, 512):
        p = _mtlcompute.coarse_ppg(band, 1000, override=None) if not os.environ.get(
            "MF_METAL_COARSE_PPG") else None
        if p is not None:
            assert band // 16 * p >= _mtlcompute.TARGET_THREADS
            assert (_mtlcompute._METAL_DIR / ("tierb_%d_c16p%d.metal" % (band, p))).is_file()
    assert _mtlcompute.coarse_ppg(64, 10, override=3) == 1     # not shipped: unpacked


@metal
@pytest.mark.parametrize("band", [64, 128])
def test_metal_packed_coarse_handles_partial_groups(ctx, band, monkeypatch):
    """15 pairs never fill a group of 2, 4, 8 or 16: the padding must not leak."""
    n, nd, nt = 2048, 3, 5
    d, h = _bank(n, nd, nt, seed=band)
    lag = 77
    d[2] += 30.0 * h[4] * np.exp(-2j * np.pi * np.arange(n) * lag / n).astype(np.complex64)
    results = {}
    for p in (1, 2, 4, 8, 16):
        monkeypatch.setenv("MF_METAL_COARSE_PPG", str(p))
        idx, val = ctx.hier_peaks(n, band, d, h, h[:, :band], {64: 0.75, 128: 1.2}[band],
                                  threshold=0.0)
        results[p] = (idx.copy(), val.copy(), ctx.last_refinements)
    for p, (idx, val, refined) in results.items():
        np.testing.assert_array_equal(idx, results[1][0])
        np.testing.assert_array_equal(val, results[1][1])
        assert refined == results[1][2]
    assert results[1][0][2, 4, 0] == lag
    assert 0 < results[1][2] < nd * nt          # the gate dismissed some pairs


@metal
def test_metal_continuous_correlation_writes_in_place():
    """Unified memory: the GPU writes the bank's output where the caller reads it."""
    from matchedfilter import TimeDomainFilterBank
    rng = np.random.default_rng(3)
    taps = rng.standard_normal((6, 700)).astype(np.float32)
    counts = np.array([300, 350, 420, 500, 640, 700])
    S = 1 << 17
    x = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
    win = [(5000, 60000), (70000, 120000)]
    got = TimeDomainFilterBank(taps, tap_counts=counts, engine="corr", device="gpu")
    want = TimeDomainFilterBank(taps, tap_counts=counts, engine="corr", device="cpu")
    a = got.correlate_series(x, windows=win)
    b = want.correlate_series(x, windows=win)
    assert a.ctypes.data % _mtlcompute.Context.page_bytes == 0
    assert all(getattr(g, "_corr_workspace", None) is None for g in got._groups)
    scale = np.abs(b).max()
    assert np.abs(a - b).max() / scale < 1e-5
    np.testing.assert_array_equal(a[:, :5000], 0)
    np.testing.assert_array_equal(a[:, 60000:70000], 0)
    # A caller-provided output that cannot back a buffer still works, via the workspace.
    out = np.empty(6 * S + 1, np.complex64)[1:].reshape(6, S)      # 8 bytes off a page
    assert out.flags.c_contiguous and out.ctypes.data % _mtlcompute.Context.page_bytes
    np.testing.assert_array_equal(got.correlate_series(x, windows=win, out=out), a)
    assert any(getattr(g, "_corr_workspace", None) is not None for g in got._groups)


@metal
def test_metal_ragged_bins_are_one_submission_and_match_per_count_calls(monkeypatch):
    """Window groups with different bin counts: one command buffer, same peaks."""
    n, nt = 2048, 1
    rng = np.random.default_rng(11)
    ser = (rng.standard_normal(9 * n) + 1j * rng.standard_normal(9 * n)).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    starts = np.arange(0, 8 * 1500, 1500, dtype=np.uint64)
    ws = np.array([700, 300, 300, 300, 300, 300, 300, 300], np.uint64)
    we = np.array([1800, 1800, 1800, 1800, 1800, 1800, 1800, 1100], np.uint64)
    bs = 61
    f = mf.MatchedFilter(n, 1, nt, device="gpu")
    f.set_templates(h)
    commits = []
    real = f._gpu._commit
    monkeypatch.setattr(f._gpu, "_commit", lambda cmd, label, **kw: (commits.append(label),
                                                                      real(cmd, label, **kw))[1])
    idx, val = f._run_series_ragged(ser, starts, ws, we, binsize=bs)
    assert len(commits) == 1
    counts = 1 + (we - ws - 1) // bs
    assert idx.shape == (8, nt, counts.max())
    for c in np.unique(counts):
        m = counts == c
        ri, rv = f.run_series(ser, starts[m], ws[m], we[m], binsize=bs, raw=True)
        np.testing.assert_array_equal(idx[m][:, :, :c], ri)
        np.testing.assert_array_equal(val[m][:, :, :c], rv)
        np.testing.assert_array_equal(idx[m][:, :, c:], -1)
        np.testing.assert_array_equal(val[m][:, :, c:], 0)


@metal
def test_metal_single_template_follow_up_matches_cpu():
    from matchedfilter import TimeDomainFilterBank
    rng = np.random.default_rng(5)
    taps = rng.standard_normal((4, 400)).astype(np.float32)
    counts = np.array([250, 300, 380, 400])
    x = (rng.standard_normal(1 << 17) + 1j * rng.standard_normal(1 << 17)).astype(np.complex64)
    kw = dict(engine="hier", threshold=6.0, false_dismissal=1e-3, binsize=2048)
    res = []
    for dev in ("gpu", "cpu"):
        b = TimeDomainFilterBank(taps, tap_counts=counts, device=dev, **kw)
        b.set_reference(np.where(np.arange(1025) > 20, 1.0, 0.0), delta_f=1.0)
        res.append(b.filter_series(x, windows=slice(40000, 40000 + 1000 * 31), binsize=31,
                                   threshold=0.0, template_index=2))
    # Same peaks; the order follows the call structure (one ragged call on the GPU,
    # one call per bin count on the CPU), so compare sorted by sample.
    g, c = ((np.sort(r.sample_indices), r.snr[np.argsort(r.sample_indices)]) for r in res)
    np.testing.assert_array_equal(g[0], c[0])
    np.testing.assert_allclose(g[1], c[1], rtol=2e-5, atol=1e-5 * np.abs(c[1]).max())
