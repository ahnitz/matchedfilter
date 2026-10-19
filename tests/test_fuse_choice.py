"""Whether filter_series_many fuses a batch's submissions is measured per set of GPU devices
(time_domain._fuse_begin): the first batches alternate fused and unfused, one side is kept,
and every batch equals its direct calls either way."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank


def test_batches_alternate_fused_and_unfused_then_keep_one(monkeypatch, tmp_path):
    from conftest import usable_gpu
    from test_time_domain import _whitened_inspiral_bank
    from matchedfilter import time_domain as td
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    monkeypatch.setenv("MF_AUTOTUNE", "1")
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    monkeypatch.setenv("MF_CHAIN_FORCE", "2048:256")
    monkeypatch.setattr(td, "_FUSE_CHOICE", {})
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
    orig = td._device_trial
    monkeypatch.setattr(td, "_device_trial", lambda table, key, *a, **k:
                        (lambda r: sides.append(r[0]) or r)(orig(table, key, *a, **k))
                        if table is td._FUSE_CHOICE else orig(table, key, *a, **k))
    for _ in range(2 * td._SINGLE_TRIALS + 4):
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
    assert {"fused", "unfused"} <= set(sides), sides
    trial = next(iter(td._FUSE_CHOICE.values()))
    assert trial["winner"] in ("fused", "unfused"), trial
