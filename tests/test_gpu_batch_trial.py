"""A batch of GPU banks is always fused (time_domain._fuse_close) and equals its direct calls;
the device trials that remain (where follow-ups run, the kernels' slots) play on the batches
themselves, and no trial chooses whether to fuse."""
import numpy as np
import pytest
from conftest import usable_gpu_reason

from matchedfilter import TimeDomainFilterBank


def test_batches_are_fused_and_equal_their_direct_calls(monkeypatch, tmp_path):
    from conftest import usable_gpu
    from test_time_domain import _whitened_inspiral_bank
    from matchedfilter import time_domain as td
    dev = usable_gpu()
    if dev is None:
        pytest.skip(usable_gpu_reason())
    monkeypatch.setenv("MF_AUTOTUNE", "1")
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    monkeypatch.setenv("MF_CHAIN_FORCE", "2048:256")
    from matchedfilter import _choice
    monkeypatch.setattr(_choice, "_CHOICES", {})     # this test's choices only
    rng = np.random.default_rng(41)
    banks = []
    for _ in range(2):
        counts = list(rng.integers(200, 400, 24))
        taps, w, df = _whitened_inspiral_bank(rng, counts)
        b = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=4.5,
                                 false_dismissal=1e-3, device=dev, fft_lengths=[2048],
                                 binsize=2048)
        b.set_reference(w, delta_f=df)
        banks.append(b)
    S = 1 << 17
    closes = []
    orig = td._fuse_close
    monkeypatch.setattr(td, "_fuse_close", lambda jobs: closes.append(orig(jobs)) or closes[-1])
    for _ in range(6):
        xs = []
        for _ in banks:
            X = np.fft.fft(rng.standard_normal(S))
            X[S // 2:] = 0
            xs.append((np.fft.ifft(X) * 2).astype(np.complex64))
        jobs = [(b, x, dict(windows=slice(3000, S - 3000))) for b, x in zip(banks, xs)]
        got = TimeDomainFilterBank.filter_series_many(jobs)
        for (b, x, kw), r in zip(jobs, got):
            want = b.filter_series(x, **kw)
            for f in want._fields:
                np.testing.assert_array_equal(getattr(want, f), getattr(r, f))
    assert closes and all(c is not None for c in closes), closes
    assert not _choice.of_kind("gpu-batch")
