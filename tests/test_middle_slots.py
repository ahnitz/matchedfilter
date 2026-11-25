"""The middle stage's channels on a device (search._InnerBatch.compute_channels)."""
import numpy as np
import pytest

from conftest import usable_gpu
from matchedfilter.search import _InnerBatch, Inner


def test_a_device_batch_correlates_its_channels_in_one_submission(monkeypatch):
    """compute_channels on a device: every channel's blocks go to the device in one
    correlate_continuous call (a part per channel, where the device writes the rows in
    place), and each channel's rows are exactly what its own call gives."""
    from matchedfilter import _gpuexec
    device = usable_gpu()
    if device is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(6)
    length = 1 << 17
    kids = [Inner(rng.standard_normal(c).astype(np.float32)) for c in (301, 451, 601, 701)]
    regions = {"A": [(20000, 70000)], "B": [(5000, 9000), (60000, 120000)]}
    one, both = (_InnerBatch(kids, length, real_input=True, device=device) for _ in range(2))
    series = {}
    for ch in regions:
        s = one.bank.empty_shared((length,), np.float32)
        s[:] = rng.standard_normal(length)
        series[ch] = s
    calls = []
    real = _gpuexec.Executor.correlate_continuous

    def spy(self, n, data, tmpl, starts, out, *a, **k):
        calls.append(len(out) if isinstance(out, (list, tuple)) else 1)
        return real(self, n, data, tmpl, starts, out, *a, **k)
    monkeypatch.setattr(_gpuexec.Executor, "correlate_continuous", spy)
    rows = [0, 1]
    for ch in regions:
        for batch in (one, both):
            batch.prepare(ch, series[ch], regions[ch])
        one.compute(ch, rows)
    one.bank.wait()
    assert calls == [1, 1]
    both.compute_channels(list(regions), rows)
    both.bank.wait()
    assert calls[2:] == [2]
    for ch in regions:
        np.testing.assert_array_equal(np.asarray(both._chan[ch]["slots"][:2]),
                                      np.asarray(one._chan[ch]["slots"][:2]))


def _page_aligned(shape, dtype, page):
    """A C-contiguous host array starting on a page boundary (not device memory)."""
    nbytes = int(np.prod(shape)) * np.dtype(dtype).itemsize
    raw = np.empty(nbytes + page, np.uint8)
    off = (-raw.ctypes.data) % page
    return raw[off:off + nbytes].view(dtype).reshape(shape)


def test_host_outputs_on_unified_memory_are_one_submission(monkeypatch):
    """correlate_series_channels into caller (host) arrays on a device that writes host
    memory in place (host_view: unified memory) correlates every channel in one call, as
    into device memory, and each output is its own channel's correlate_series."""
    from matchedfilter import _gpuexec
    from matchedfilter.time_domain import TimeDomainFilterBank
    device = usable_gpu()
    if device is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(8)
    length = 1 << 17
    counts = np.array([301, 451])
    taps = np.zeros((2, counts.max()), np.float32)
    for r, c in enumerate(counts):
        taps[r, :c] = rng.standard_normal(c)
    bank = TimeDomainFilterBank(taps, counts, engine="corr", device=device)
    ctx = bank._groups[0].get_correlation_plan()._gpu
    page = getattr(ctx, "page_bytes", None)
    if getattr(ctx, "host_view", None) is None or page is None:
        pytest.skip("the device does not write host memory in place")
    series, windows = [], [[(20000, 70000)], [(5000, 9000), (60000, 120000)]]
    for _ in windows:
        s = bank.empty_shared((length,), np.float32)
        s[:] = rng.standard_normal(length)
        series.append(s)
    outs = [_page_aligned((len(taps), length), np.complex64, page) for _ in windows]
    assert all(ctx.host_view(o) is not None for o in outs)
    calls = []
    real = _gpuexec.Executor.correlate_continuous

    def spy(self, n, data, tmpl, starts, out, *a, **k):
        calls.append(len(out) if isinstance(out, (list, tuple)) else 1)
        return real(self, n, data, tmpl, starts, out, *a, **k)
    monkeypatch.setattr(_gpuexec.Executor, "correlate_continuous", spy)
    bank.correlate_series_channels(series, windows, outs, [None, None])
    assert calls == [2] * len(bank._groups)
    for s, w, o in zip(series, windows, outs):
        ref = bank.correlate_series(s, windows=w)
        np.testing.assert_array_equal(o, ref)
