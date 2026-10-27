"""A batch's GPU settings -- its submissions fused or not, where its follow-ups run, a fused
Vulkan batch's interleave depth -- are one paired trial per set of GPU devices
(time_domain._gpu_batch), played on the batches themselves: the first batches run every arm,
one is kept, and every batch equals its direct calls whichever ran."""
import numpy as np
import pytest
from conftest import usable_gpu_reason

from matchedfilter import TimeDomainFilterBank


def test_batches_play_every_setting_then_keep_one(monkeypatch, tmp_path):
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
    sides = []
    orig = td._fuse_close
    monkeypatch.setattr(td, "_fuse_close", lambda jobs: sides.append(td.gpu_setting("fuse")) or orig(jobs))
    # Batches until the trial locks, at most its rounds' cap (with a confirmation): the
    # joint trial of the banks' block sizes plays its rounds first, each batch it plays a
    # round of not a round of this trial.
    for _ in range(80):
        if sides and all(t.winner is not None for t in _choice.of_kind("gpu-batch").values()):
            break
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
    assert {True, False} <= set(sides), sides             # both settings played
    trial = next(iter(_choice.of_kind("gpu-batch").values()))
    assert trial.winner in trial.candidates and "fuse=0" in trial.candidates, trial.samples
