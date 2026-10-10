"""Device timestamps (MF_GPU_TIMING) read while work is still in flight are real intervals.

A timestamp pair's queries were reset by its own command buffers on the device, so until the
submission ran they read as AVAILABLE: zero on a slot's first use, the previous use's values
after that. A collect while pipelined batches were in flight therefore returned 0/0 pairs
(~15% of a ladder's) and stale intervals. Pairs and profile marks are now reset from the host
when handed out (VK_EXT_host_query_reset), so a waiting read waits for this use's writes.
"""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from test_time_domain import _whitened_inspiral_bank


def test_timestamps_read_in_flight_are_never_zero(monkeypatch):
    from conftest import usable_gpu
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_GPU_TIMING", "1")
    monkeypatch.setenv("MF_GPU_PROFILE", "1")
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    rng = np.random.default_rng(91)
    banks = []
    for _ in range(3):
        counts = list(rng.integers(200, 400, 33))
        taps, w, df = _whitened_inspiral_bank(rng, counts)
        b = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                 false_dismissal=1e-3, device=dev, fft_lengths=[2048], binsize=2048)
        b.set_reference(w, delta_f=df)
        banks.append(b)
    ctxs = {id(g.plan._gpu): g.plan._gpu for b in banks for g in b._groups}
    ctx = next(iter(ctxs.values()))
    if not hasattr(ctx, "_reset_query"):
        pytest.skip("Vulkan contexts only")
    if ctx._reset_query is None:
        pytest.skip("device has no host query reset")
    S = 1 << 17
    rows = banks[0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=slice(3000, S - 3000))) for i, b in enumerate(banks)]
    logged = []
    for _ in range(24):
        X = np.fft.fft(rng.standard_normal((len(banks), S)), axis=1)
        X[:, S // 2:] = 0
        rows[:] = (np.fft.ifft(X, axis=1) * 2).astype(np.complex64)
        futures = TimeDomainFilterBank.filter_series_many(jobs, wait=False)
        for c in ctxs.values():                      # collect while the batch is in flight
            logged.extend(c.timings())
            c.timings().clear()
        [f.result() for f in futures]
    for c in ctxs.values():
        logged.extend(c.timings())
    assert len(logged) > 50
    bad = [(label, ms) for label, ms in logged if not ms > 0]
    assert not bad, "%d of %d timestamp intervals were not real: %r" % (
        len(bad), len(logged), bad[:5])
