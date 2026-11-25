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
    # A device that writes these rows through a host view (Metal's unified memory) keeps
    # its own per-channel path; elsewhere the channels are one call.
    ctx = both.bank._groups[0].get_correlation_plan()._gpu
    view = getattr(ctx, "host_view", None)
    hosted = view is not None and view(both._chan["A"]["slots"][:2]) is not None
    assert calls[2:] == ([1, 1] if hosted else [2])
    for ch in regions:
        np.testing.assert_array_equal(np.asarray(both._chan[ch]["slots"][:2]),
                                      np.asarray(one._chan[ch]["slots"][:2]))
