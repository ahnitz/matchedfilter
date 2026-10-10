"""Device timestamps (MF_GPU_TIMING=1): intervals that cannot be real are rejected, a
counter wrap within timestampValidBits is still the right interval."""
import numpy as np
import pytest

from matchedfilter import _gputime


def test_interval_ms():
    assert _gputime.interval_ms(1000, 3000, 10.0) == pytest.approx(0.02)
    # A never-written (or reset) query reads 0: end - 0 was the ~768,000 s "totals".
    assert _gputime.interval_ms(0, 76830213001506, 10.0) is None
    assert _gputime.interval_ms(76830213001506, 0, 10.0) is None
    # End before begin on a 64-bit counter cannot be an interval.
    assert _gputime.interval_ms(5000, 4000, 10.0) is None
    # A 36-bit counter that wrapped between the reads: modular difference.
    bits = 36
    assert _gputime.interval_ms((1 << bits) - 100, 50, 10.0, bits) == pytest.approx(150 * 1e-5)
    # No device interval longer than the host time from submission to readback.
    assert _gputime.interval_ms(1, 1 + 10**9, 1.0, 64, host_ms=5.0) is None
    assert _gputime.interval_ms(1, 1 + 10**6, 1.0, 64, host_ms=5.0) == pytest.approx(1.0)
    assert _gputime.interval_ms(1, 2, 1.0, 0) is None       # no timestamps on this queue


def test_vulkan_timings_are_sane(monkeypatch):
    from conftest import usable_gpu
    monkeypatch.setenv("MF_GPU_TIMING", "1")
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    import matchedfilter as mf
    from matchedfilter.device import parse
    if parse(dev).backend != "vulkan":
        pytest.skip("Vulkan timestamps")
    f = mf.CorrelationFilter(4096, 2, 3, device=dev)
    rng = np.random.default_rng(1)
    f.set_data((rng.standard_normal((2, 4096)) + 0j).astype(np.complex64))
    f.set_templates((rng.standard_normal((3, 4096)) + 0j).astype(np.complex64))
    for _ in range(300):                       # past the 256-slot ring
        f.run()
    times = _gputime.collect()
    assert times and all(0 <= ms < 60e3 for _, ms in times.values()), times
