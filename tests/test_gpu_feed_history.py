"""A hierarchical GPU call's tier-0 feed (bands from the series, or the full forward) is a
function of the call, not of the calls before it: the feeds round differently, so a feed
chosen from an earlier call's measured refine fraction made results depend on call order
(a batch disagreed with the same calls made one by one, on pairs within an fp16 step of a
gate's threshold)."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank


def test_a_call_repeated_after_a_different_one_takes_the_same_feed(monkeypatch):
    from conftest import usable_gpu
    from test_time_domain import _whitened_inspiral_bank
    from matchedfilter import _gpuhier
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.delenv("MF_BAND_FORWARD", raising=False)
    rng = np.random.default_rng(21)
    counts = list(rng.integers(300, 1500, 40))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=6.0,
                                false_dismissal=1e-3, device=dev, fft_lengths=[2048])
    bank.set_reference(w, delta_f=df)
    S = 1 << 18
    X = np.fft.fft(rng.standard_normal(S))
    X[S // 2:] = 0
    quiet = (np.fft.ifft(X) * 2).astype(np.complex64)
    loud = quiet * np.float32(30.0)              # every block refines

    def run(x):
        before = _gpuhier.CLAIMS[0]
        r = bank.filter_series(x)
        return r, _gpuhier.CLAIMS[0] - before
    run(quiet)                                   # setup: calibration plans, records
    first, claims_first = run(quiet)
    run(loud)
    again, claims_again = run(quiet)
    assert claims_again == claims_first, (claims_first, claims_again)
    for f in first._fields:
        np.testing.assert_array_equal(getattr(first, f), getattr(again, f))
