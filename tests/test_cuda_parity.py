"""CUDA backend parity: each audited defect has a test that failed before its fix.

Every test here runs on real NVIDIA hardware and compares against the CPU (or a
float64 reference), never the GPU against itself. Without a CUDA device they skip.

Defects (docs/gpu-parity-plan.md A3/A4, F):
- two-tier chains ran tier 1's band with tier 0's templates and threshold;
- grouped run_series unpacked 4-tuples as pairs (ValueError) and computed
  every window over every row;
- the refine read the survivor count back to the host between dispatches;
- no cache eviction: every new shape allocated device memory for good;
- correlate staged the whole output in one device allocation (untiled);
- n > 65536 (two-stage) correlation and forward had no CUDA kernels;
- kernels with more than 48 KB of static shared memory failed to load;
- ``except TypeError`` probing re-dispatched work that had already run.
"""
import ctypes
import os
import subprocess
import sys

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _cuda

_DEVICES = _cuda.enumerate_devices()[0]
pytestmark = pytest.mark.skipif(not _DEVICES, reason="no NVIDIA CUDA device")
DEV = "cuda:0"


def _complex(rng, shape):
    return (rng.standard_normal(shape) + 1j * rng.standard_normal(shape)).astype(np.complex64)


@pytest.fixture(scope="module")
def ctx():
    from matchedfilter import _cudacompute
    c = _cudacompute.Context(0)
    yield c
    c.destroy()


def _bank(n, nd, nt, seed, inject=()):
    rng = np.random.default_rng(seed)
    d = _complex(rng, (nd, n))
    h = _complex(rng, (nt, n))
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    for di, ti, lag, amp in inject:
        d[di] += amp * h[ti] * np.exp(-2j * np.pi * np.arange(n) * lag / n).astype(np.complex64)
    return d, h


# ---- A4: two-tier chains -------------------------------------------------------
def test_two_tier_direct_detects_and_counts(ctx):
    n, b0, b1, nd, nt = 4096, 128, 512, 4, 8
    d, h = _bank(n, nd, nt, 42, inject=[(1, 2, 500, 50.0)])
    idx, val = ctx.hier_peaks(n, b1, d, h, h[:, :b0], 0.9,
                              cascade_band=b0, ct1=h[:, :b1], raw_thr1=2.0, threshold=30.0)
    assert idx[1, 2, 0] == 500 and abs(val[1, 2, 0]) > 30.0
    rest = np.delete(idx.reshape(-1), 1 * nt + 2)
    assert np.all(rest == -1)
    assert ctx.last_refinements == 1
    assert ctx.last_tier1_survivors == 1


def test_two_tier_rejects_mismatched_coarse_templates(ctx):
    """The old code ran band1 with tier-0 templates; a shape mismatch must raise."""
    n, nd, nt = 4096, 2, 2
    d, h = _bank(n, nd, nt, 1)
    with pytest.raises(ValueError):
        ctx.hier_peaks(n, 512, d, h, h[:, :512], 0.9,
                       cascade_band=128, ct1=h[:, :512], raw_thr1=2.0)


@pytest.mark.parametrize("chain", [(128, 512), (256, 1024)])
def test_two_tier_public_api_matches_cpu(chain):
    n, nd, nt = 4096, 4, 6
    d, h = _bank(n, nd, nt, 123, inject=[(2, 3, 1200, 40.0), (0, 5, 77, 25.0)])
    out = {}
    for dev in ("cpu", DEV):
        f = mf.HierarchicalFilter(n, nd, nt, snr=10.0, fd=1e-4, chain=chain, device=dev)
        f.set_coarse_threshold((0.9, 2.0))
        assert f.config == chain
        f.set_data(d)
        f.set_templates(h)
        out[dev] = f.run(threshold=20.0).copy()
    np.testing.assert_array_equal(out[DEV]["index"], out["cpu"]["index"])
    np.testing.assert_allclose(out[DEV]["value"], out["cpu"]["value"], rtol=2e-5, atol=1e-5)
    assert out["cpu"][2, 3]["index"] == 1200


def test_two_tier_series_matches_cpu():
    n, nt = 2048, 5
    rng = np.random.default_rng(7)
    h = _complex(rng, (nt, n))
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    ser = _complex(rng, 40000)
    ser[9216 + 500:9216 + 500 + n] += 30 * n * np.fft.ifft(h[3]).astype(np.complex64)
    out = {}
    for dev in ("cpu", DEV):
        f = mf.HierarchicalFilter(n, 1, nt, snr=8.0, fd=1e-3, chain=(128, 512), device=dev)
        f.set_coarse_threshold((0.5, 1.0))
        f.set_templates(h)
        out[dev] = f.run_series(ser, starts=np.arange(0, 38000, 1024),
                                win_start=[100] * 38, win_end=[1924] * 38,
                                binsize=512, threshold=4.0).copy()
    np.testing.assert_array_equal(out[DEV]["index"], out["cpu"]["index"])
    np.testing.assert_allclose(out[DEV]["value"], out["cpu"]["value"], rtol=2e-5, atol=1e-5)


@pytest.mark.parametrize("chain", [256, (128, 512)])
def test_hier_grouped_windows_match_cpu_in_one_sync(chain, monkeypatch):
    """First and last blocks with their own windows: one submission for all groups."""
    n, nt = 2048, 7                      # odd template count: exercises the padded PPG rows
    rng = np.random.default_rng(31)
    h = _complex(rng, (nt, n))
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    ser = _complex(rng, 30000)
    # A block's spectrum is FFT(x)/n, so x = n*ifft(h) correlates to a peak at its offset
    # into the block: lag 700 of the block starting at 12000 (inside the 200..1800 window).
    ser[12700:12700 + n] += 25 * n * np.fft.ifft(h[4]).astype(np.complex64)
    starts = np.arange(0, 26000, 1500)
    ws = np.full(starts.size, 200)
    we = np.full(starts.size, 1800)
    ws[0], we[0] = 0, 1600               # three window groups, one bin count
    ws[-1], we[-1] = 300, 1900
    thr = (0.5, 1.0) if isinstance(chain, tuple) else 0.6
    out = {}
    for dev in ("cpu", DEV):
        f = mf.HierarchicalFilter(n, 1, nt, snr=8.0, fd=1e-3, chain=chain, device=dev)
        f.set_coarse_threshold(thr)
        f.set_templates(h)
        if dev == DEV:
            f.run_series(ser, starts=starts, win_start=ws, win_end=we, binsize=512, threshold=4.0)
            syncs = []
            real = f._gpu._sync
            monkeypatch.setattr(f._gpu, "_sync", lambda st=None: (syncs.append(1), real(st))[1])
        out[dev] = f.run_series(ser, starts=starts, win_start=ws, win_end=we,
                                binsize=512, threshold=4.0).copy()
    assert len(syncs) == 1, "every window group must go in one submission"
    np.testing.assert_array_equal(out[DEV]["index"], out["cpu"]["index"])
    np.testing.assert_allclose(out[DEV]["value"], out["cpu"]["value"], rtol=2e-5, atol=1e-5)
    assert (out["cpu"]["index"] >= 0).any()


def test_slots_sharing_a_stream_keep_their_own_block_starts(ctx):
    """Slots s and s+4 share a stream. The block starts go host -> pinned staging ->
    device asynchronously; with one staging buffer per stream, slot 4's starts overwrote
    slot 0's before the busy stream had copied them, and slot 0 transformed slot 4's blocks."""
    n = 65536
    rng = np.random.default_rng(5)
    series = ctx.empty_shared((40 * n,))
    series[:] = _complex(rng, series.shape)
    spec = [ctx.empty_shared((16, n)) for _ in range(2)]
    starts = [np.arange(16, dtype=np.uint32) * n, np.arange(16, dtype=np.uint32) * n + 17 * n]
    busy = ctx.empty_shared((64, n))                 # a long forward first: stream 0 is busy
    ctx.forward(n, series, np.arange(64, dtype=np.uint32) * (n // 2), busy, defer=True, slot=0)
    ctx.forward(n, series, starts[0], spec[0], defer=True, slot=0)
    ctx.forward(n, series, starts[1], spec[1], defer=True, slot=4)
    ctx._sync(ctx.get_stream(0))
    for s, st in zip(spec, starts):
        ref = np.fft.fft(np.stack([series[a:a + n] for a in st[:3]]), axis=1) / n
        np.testing.assert_allclose(s[:3], ref, rtol=0, atol=1e-5 * np.abs(ref).max())


def test_unslotted_consumer_waits_for_a_slot_forward(ctx):
    """A tiled dispatch runs unslotted (stream 0) on spectra a slot's deferred forward is
    still writing on its own stream: it must be ordered after that forward."""
    n, rows = 65536, 96                                   # a forward of ~1 ms
    rng = np.random.default_rng(6)
    series = ctx.empty_shared((rows * n // 2 + n,))
    series[:] = _complex(rng, series.shape)
    spec = ctx.empty_shared((rows, n))
    h = _complex(rng, (1, n))
    st = np.arange(rows, dtype=np.uint32) * (n // 2)
    d = (np.fft.fft(np.stack([series[a:a + n] for a in st]), axis=1) / n).astype(np.complex64)
    ref_i, ref_v = ctx.peaks(n, d, h, binsize=n)
    for _ in range(3):
        spec[:] = 0
        ctx.forward(n, series, st, spec, defer=True, slot=1)
        idx, val = ctx.peaks(n, spec, h, binsize=n)       # unslotted: stream 0
        np.testing.assert_array_equal(idx, ref_i)
        np.testing.assert_allclose(val, ref_v, rtol=1e-4, atol=1e-6)


@pytest.mark.parametrize("tiled", [False, True])
@pytest.mark.parametrize("kind", ["flat", "hier"])
def test_pipelined_series_across_streams_matches_cpu(kind, tiled, monkeypatch):
    """Many batches in flight on 4 streams (supports_async). With a dispatch limit the
    window falls back to tiled, unslotted dispatches on the default stream, which must
    wait for the forward FFTs enqueued on the slot streams -- without that wait the
    tiled path read spectra still being written (wrong peaks, intermittently)."""
    # n=65536: each batch's forward FFT runs long enough (~1 ms) for an unordered
    # consumer on another stream to overtake it.
    n, nt = 65536, 4
    rng = np.random.default_rng(12)
    h = _complex(rng, (nt, n))
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    ser = _complex(rng, 48 * 40000 + n)
    starts = np.arange(0, 48 * 40000, 40000)
    ws = np.full(starts.size, 1000); we = np.full(starts.size, 61000)
    ws[0], we[0] = 0, 60000; ws[-1], we[-1] = 2000, 62000   # three window groups, one bin count
    out = {}
    for dev in ("cpu", DEV):
        cls = mf.MatchedFilter if kind == "flat" else mf.HierarchicalFilter
        kw = {} if kind == "flat" else dict(snr=6.0, fd=1e-3, chain=256)
        f = cls(n, 1, nt, device=dev, **kw)
        if kind == "hier":
            f.set_coarse_threshold(0.3)
        f.set_templates(h)
        if dev == DEV:
            assert f._gpu.supports_async
            f.set_memory_limits(series_bytes=8 * n * 6)       # ~6 blocks per batch: many batches
            if tiled:
                monkeypatch.setattr(f._gpu, "max_dispatch_x", nt // 2, raising=False)
        # A race shows intermittently: repeat the device call.
        out[dev] = [f.run_series(ser, starts=starts, win_start=ws, win_end=we,
                                 binsize=30000, threshold=3.0).copy()
                    for _ in range(1 if dev == "cpu" else 3)]
    for got in out[DEV]:
        np.testing.assert_array_equal(got["index"], out["cpu"][0]["index"])
        np.testing.assert_allclose(got["value"], out["cpu"][0]["value"], rtol=2e-5, atol=1e-5)


# ---- grouped run_series -----------------------------------------------------------
@pytest.mark.parametrize("binsize", [61, 256])
def test_grouped_windows_match_cpu(binsize):
    n, nt = 4096, 3
    rng = np.random.default_rng(11)
    h = _complex(rng, (nt, n))
    ser = _complex(rng, 60000)
    starts = np.array([0, 3000, 9000, 20000, 33000, 50000])
    ws = np.array([10, 0, 700, 5, 0, 100])      # distinct windows, one bin count
    we = ws + 3000
    out = {}
    for dev in ("cpu", DEV):
        f = mf.MatchedFilter(n, 1, nt, device=dev)
        f.set_templates(h)
        out[dev] = f.run_series(ser, starts=starts, win_start=ws, win_end=we,
                                binsize=binsize, threshold=0.0).copy()
    np.testing.assert_array_equal(out[DEV]["index"], out["cpu"]["index"])
    np.testing.assert_allclose(out[DEV]["value"], out["cpu"]["value"], rtol=2e-5, atol=1e-4)


def test_peaks_grouped_direct(ctx):
    n, nd, nt, bs = 1024, 6, 2, 100
    rng = np.random.default_rng(3)
    spec = ctx.empty_shared((nd, n))
    spec[:] = _complex(rng, (nd, n))
    h = _complex(rng, (nt, n))
    groups = [(0, 1000, 0, 2), (24, 1024, 2, 3), (500, 1000, 3, 6)]
    idx, val = ctx.peaks_grouped(n, spec, h, groups, bs, 0.0)
    for lo, hi, a, b in groups:
        ri, rv = ctx.peaks(n, np.array(spec[a:b]), h, binsize=bs, window=(lo, hi))
        nb = ri.shape[2]
        np.testing.assert_array_equal(idx[a:b, :, :nb], ri)
        np.testing.assert_allclose(val[a:b, :, :nb], rv, rtol=1e-6, atol=1e-6)


# ---- F: no host readback between dispatches -----------------------------------------
@pytest.mark.parametrize("cascade", [False, True])
def test_hier_call_synchronizes_once(ctx, monkeypatch, cascade):
    n, nd, nt = 2048, 2, 4
    d, h = _bank(n, nd, nt, 5, inject=[(0, 1, 300, 30.0)])
    calls = []
    lib = ctx.cuda

    class Spy:
        def __getattr__(self, name):
            return getattr(lib, name)
    spy = Spy()
    spy.cuStreamSynchronize = lambda st: (calls.append(1), lib.cuStreamSynchronize(st))[1]
    spy.cuCtxSynchronize = lambda: (calls.append(1), lib.cuCtxSynchronize())[1]
    kw = dict(cascade_band=128, ct1=h[:, :512], raw_thr1=1.0) if cascade else {}
    ct0 = h[:, :128] if cascade else h[:, :512]
    ctx.hier_peaks(n, 512, d, h, ct0, 0.5, threshold=10.0, **kw)   # warm: build the record
    monkeypatch.setattr(ctx, "cuda", spy)
    idx, _ = ctx.hier_peaks(n, 512, d, h, ct0, 0.5, threshold=10.0, **kw)
    assert idx[0, 1, 0] == 300
    assert len(calls) == 1, "the survivor count must not be read back between dispatches"


def test_many_survivors_past_the_resident_grid(ctx):
    """More survivors than the refine's fixed grid: the grid-stride loop covers all."""
    n, nd, nt = 1024, 4, 1024
    d, h = _bank(n, nd, nt, 9)
    ref_i, ref_v = ctx.peaks(n, d, h, binsize=256)
    idx, val = ctx.hier_peaks(n, 256, d, h, h[:, :256], 0.0, binsize=256)   # every pair survives
    assert ctx.last_refinements == nd * nt
    np.testing.assert_array_equal(idx, ref_i)
    np.testing.assert_allclose(val, ref_v, rtol=1e-6, atol=1e-6)


# ---- eviction -------------------------------------------------------------------------
def test_cache_is_bounded_and_results_survive_eviction(ctx):
    n = 1024
    rng = np.random.default_rng(2)
    h = _complex(rng, (8, n))
    old = ctx.cache_limit_bytes
    ctx.cache_limit_bytes = 2 * 1024 * 1024
    try:
        expected = {}
        for nd in range(1, 40):
            d = _complex(np.random.default_rng(nd), (nd, n))
            expected[nd] = ctx.peaks(n, d, h, binsize=64)
            assert ctx._cache_bytes() <= ctx.cache_limit_bytes + 3 * nd * n * 8 * 2
        for nd in (1, 17, 39):
            d = _complex(np.random.default_rng(nd), (nd, n))
            i2, v2 = ctx.peaks(n, d, h, binsize=64)
            np.testing.assert_array_equal(i2, expected[nd][0])
            np.testing.assert_allclose(v2, expected[nd][1], rtol=1e-6)
        assert len(ctx._batches) < 39
    finally:
        ctx.cache_limit_bytes = old
        ctx.clear_cache()


# ---- tiled correlate and two-stage lengths ------------------------------------------------
def test_correlate_tiles_into_host_output(ctx, monkeypatch):
    from matchedfilter import _cudacompute
    n, nd, nt = 2048, 3, 5
    rng = np.random.default_rng(4)
    d, h = _complex(rng, (nd, n)), _complex(rng, (nt, n))
    monkeypatch.setattr(_cudacompute, "_TILE_BYTES", 2 * n * 8)   # force 2-template tiles
    out = np.zeros((nd, nt, n), np.complex64)
    ctx.correlate(n, d, h, out)
    ref = np.fft.ifft(d[:, None, :] * np.conj(h[None, :, :]), axis=-1) * n
    np.testing.assert_allclose(out, ref, rtol=0, atol=2e-4 * np.abs(ref).max())
    biggest = max(b.nbytes for rec in ctx._full_batches.values()
                  for k, b in rec.items() if k in ("stage", "tierc"))
    assert biggest <= 2 * n * 8


@pytest.mark.parametrize("n", [131072, 262144])
def test_two_stage_correlation_matches_numpy(n):
    rng = np.random.default_rng(n)
    nd, nt = 2, 3
    d, h = _complex(rng, (nd, n)), _complex(rng, (nt, n))
    f = mf.CorrelationFilter(n, nd, nt, device=DEV)
    f.set_data(d)
    f.set_templates(h)
    got = f.run()
    ref = np.fft.ifft(d[:, None, :].astype(np.complex128) * np.conj(h[None, :, :]), axis=-1) * n
    assert np.max(np.abs(got - ref)) <= 1e-5 * np.abs(ref).max() * np.sqrt(n / 1024)


def test_two_stage_series_matches_cpu():
    n = 131072
    rng = np.random.default_rng(8)
    taps = rng.standard_normal((3, 4000)).astype(np.float32)
    ser = _complex(rng, 3 * n)
    valid = (2000, n - 2000)
    out = {}
    for dev in ("cpu", DEV):
        f = mf.CorrelationFilter(n, 1, 3, device=dev, valid=valid)
        hf = np.zeros((3, n), np.complex64)
        hf[:, :4000] = taps
        f.set_templates(np.fft.fft(hf, axis=1).astype(np.complex64))
        out[dev] = np.array(f.run_series(ser))
    scale = np.abs(out["cpu"]).max()
    np.testing.assert_allclose(out[DEV], out["cpu"], rtol=0, atol=1e-5 * scale)


@pytest.mark.parametrize("n", [8192, 16384, 32768, 65536])
def test_large_shared_memory_kernels_load_and_agree(n):
    rng = np.random.default_rng(n)
    d, h = _complex(rng, (2, n)), _complex(rng, (3, n))
    out = {}
    for dev in ("cpu", DEV):
        f = mf.MatchedFilter(n, 2, 3, device=dev)
        f.set_data(d)
        f.set_templates(h)
        out[dev] = f.run(binsize=n // 4).copy()
    np.testing.assert_array_equal(out[DEV]["index"], out["cpu"]["index"])
    np.testing.assert_allclose(out[DEV]["value"], out["cpu"]["value"], rtol=2e-5)


# ---- device-resident middle -> fine (plan D3) --------------------------------------------------
def test_resident_correlation_feeds_filter_in_place():
    from matchedfilter import TimeDomainFilterBank
    from matchedfilter._shared import shared_buffer
    rng = np.random.default_rng(21)
    S = 200000
    ser = _complex(rng, S)
    mid_taps = rng.standard_normal((5, 300)).astype(np.float32)
    fine_taps = rng.standard_normal((7, 250)).astype(np.float32)
    win = slice(30000, 170000)
    banks = {d: TimeDomainFilterBank(mid_taps, engine="corr", device=d) for d in ("cpu", DEV)}
    ref = banks["cpu"].correlate_series(ser, windows=win)
    out = banks[DEV].empty_shared((5, S))
    out[:] = 7.0                               # stale contents must be overwritten, zeros included
    got = banks[DEV].correlate_series(ser, windows=win, out=out)
    assert got is out
    np.testing.assert_allclose(got, ref, rtol=0, atol=1e-5 * np.abs(ref).max())
    assert not np.any(got[:, :win.start - 300]) and not np.any(got[:, win.stop + 300:])
    fine = {d: TimeDomainFilterBank(fine_taps, engine="flat", threshold=3.0, device=d,
                                    binsize=4096) for d in ("cpu", DEV)}
    row = got[3]
    gplan = fine[DEV]._groups[0].plan
    assert shared_buffer(row, gplan._gpu) is not None, "a row of shared output must bind in place"
    r_dev = fine[DEV].filter_series(row, windows=slice(40000, 160000))
    r_cpu = fine["cpu"].filter_series(ref[3], windows=slice(40000, 160000))
    ws = getattr(gplan, "_series_workspace", None)
    assert ws is not None and ws[1] is None, "the series was staged through the host"
    np.testing.assert_array_equal(r_dev.sample_indices, r_cpu.sample_indices)
    np.testing.assert_allclose(r_dev.snr, r_cpu.snr, rtol=2e-5, atol=1e-4)


# ---- A3: no TypeError probing re-dispatch ----------------------------------------------------
def test_backend_type_error_is_not_retried(monkeypatch):
    f = mf.MatchedFilter(1024, 1, 2, device=DEV)
    rng = np.random.default_rng(0)
    f.set_templates(_complex(rng, (2, 1024)))
    calls = []

    def broken(*a, **k):
        calls.append(k)
        raise TypeError("raised inside a dispatch that already ran")
    monkeypatch.setattr(f._gpu, "peaks_grouped", broken)
    with pytest.raises(TypeError):
        f.run_series(_complex(rng, 8000), starts=[0, 3000, 6000],
                     win_start=[0, 10, 0], win_end=[1000, 1000, 950], binsize=100)
    assert len(calls) == 1


# ---- timers ---------------------------------------------------------------------------------
def test_timing_log_off_records_nothing(ctx):
    assert not ctx.timing
    n = 1024
    d, h = _bank(n, 1, 2, 0)
    ctx.peaks(n, d, h)
    assert ctx.timing_log == []
    assert not ctx._pending_events


def test_timing_log_records_each_kernel():
    code = r"""
import numpy as np
from matchedfilter import _cudacompute
c = _cudacompute.Context(0)
n = 2048
rng = np.random.default_rng(0)
d = (rng.standard_normal((2, n)) + 1j*rng.standard_normal((2, n))).astype(np.complex64)
h = (rng.standard_normal((3, n)) + 1j*rng.standard_normal((3, n))).astype(np.complex64)
c.hier_peaks(n, 512, d, h, h[:, :512], 0.0)
labels = [l for l, ms in c.timing_log]
assert all(ms >= 0 for l, ms in c.timing_log), c.timing_log
for want in ("tierb_512_c16", "compact", "refine_2048", "readback", "upload"):
    assert any(l.startswith(want) for l in labels), (want, labels)
from matchedfilter import _gputime
c.peaks(n, d, h)
agg = _gputime.collect()                  # the shared contract: settles and sums
assert agg.get("tierb_2048", (0, 0))[0] == 1, agg
assert c.timing_log == []                 # collect() cleared the context's own log
print("OK", len(labels))
"""
    env = dict(os.environ, MF_GPU_TIMING="1")
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert r.returncode == 0 and "OK" in r.stdout, r.stdout + r.stderr


def test_gpu_cost_calibration_measures_on_cuda():
    """gatechain.calibrate_costs_gpu switches the device timers on through ctx._timing.
    CUDA kept its own flag, so every measurement was 0 ns: the bank priced every chain at
    zero and picked n=8192 banks with 1024-4096 bins of coarse band (2x slower fine stage,
    and loud peaks dismissed). The model must carry real, positive, ordered costs."""
    from matchedfilter import gatechain
    cm = gatechain.calibrate_costs_gpu(2048, DEV, blocks=256, reps=2, nt=64)
    assert cm.block > 0
    assert all(v > 0 for v in cm.dense.values()), cm.dense
    assert cm.refine(1e-2) > 0
    bands = sorted(cm.dense)
    assert cm.dense[bands[-1]] > cm.dense[bands[0]], cm.dense   # a wider gate costs more


# ---- sparse readback ---------------------------------------------------------------------
@pytest.mark.parametrize("kind", ["peaks", "peaks_grouped", "hier", "hier_grouped"])
@pytest.mark.parametrize("thr", [4.5, 0.0])        # 0: every bin a peak, past _SPARSE_HOST
def test_sparse_readback_equals_dense(ctx, kind, thr):
    from matchedfilter import _SparsePeaks
    n, nd, nt, bs = 2048, 24, 9, 512
    rng = np.random.default_rng(17)
    spec = ctx.empty_shared((nd, n))
    spec[:] = _complex(rng, (nd, n)) / np.sqrt(n)
    h = _complex(rng, (nt, n))
    h /= np.linalg.norm(h, axis=1, keepdims=True) / np.sqrt(n)
    groups = [(0, 2000, 0, 3), (40, 2040, 3, 20), (10, 2010, 20, 24)]

    def call(sparse):
        if kind == "peaks":
            return ctx.peaks(n, spec, h, binsize=bs, threshold=thr, window=(40, 2040), sparse=sparse)
        if kind == "peaks_grouped":
            return ctx.peaks_grouped(n, spec, h, groups, bs, thr, sparse=sparse)
        if kind == "hier":
            return ctx.hier_peaks(n, 512, spec, h, h[:, :128], 0.5, cascade_band=128, ct1=h[:, :512],
                                  raw_thr1=1.0, binsize=bs, threshold=thr, window=(40, 2040),
                                  sparse=sparse)
        return ctx.hier_peaks_grouped(n, 256, spec, h, h[:, :256], 0.5, groups, bs, thr,
                                      sparse=sparse)
    di, dv = call(False)
    sp = call(True)
    assert isinstance(sp, _SparsePeaks) and sp.shape == di.shape
    si, sv = sp.dense()
    np.testing.assert_array_equal(si, di)
    np.testing.assert_array_equal(sv, dv)
    if thr == 0.0:
        assert sp.flat.size > 4096 or sp.flat.size == di.size


def test_clock_reference_reads_the_sm_clock(ctx):
    """CUDA calibrations are scaled by the SM clock (NVML), not by a small timed call."""
    mhz = ctx.clock_mhz()
    if mhz is None:
        pytest.skip("NVML unavailable")
    assert 100.0 < mhz < 10000.0
    from matchedfilter import gatechain
    ref = gatechain._clock_ref("gpu:0")
    assert ref._mhz is not None
    # At an unchanged clock the reference is the anchor; it scales inversely with the clock.
    reader, mhz0 = ref._mhz
    ref._mhz = (lambda: mhz0 * 2.0, mhz0)
    try:
        assert ref.time() == pytest.approx(ref.anchor / 2.0)
    finally:
        ref._mhz = (reader, mhz0)
