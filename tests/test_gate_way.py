"""A cascade's later gate tier reports either the window's maximum alone or the full one-bin
election (HierOps._played "gateway", measured per device): both ways must give the same
peaks, so the measured choice can only change speed. Each way is forced here."""
import numpy as np
import pytest
from conftest import usable_gpu_reason

from matchedfilter import TimeDomainFilterBank


@pytest.mark.parametrize("way", ["gate", "elect"])
def test_both_gate_ways_give_the_same_peaks(way, monkeypatch):
    from conftest import usable_gpu
    from test_time_domain import _whitened_inspiral_bank
    from matchedfilter import _gpuhier
    dev = usable_gpu()
    if dev is None:
        pytest.skip(usable_gpu_reason())
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "2048:256,512")
    rng = np.random.default_rng(31)
    counts = list(rng.integers(300, 1500, 40))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    S = 1 << 18
    X = np.fft.fft(rng.standard_normal(S))
    X[S // 2:] = 0
    x = (np.fft.ifft(X) * 2).astype(np.complex64)
    t7 = np.asarray(taps[7])[:counts[7]]
    x[100000:100000 + t7.size] += 3 * t7                  # something for the tiers to pass

    asked = []

    def run(choice):
        orig = _gpuhier.HierOps._played
        monkeypatch.setattr(_gpuhier.HierOps, "_played", lambda self, what, band: (
            asked.append(choice) or choice) if what == "gateway" else orig(self, what, band))
        bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=4.5,
                                    false_dismissal=1e-3, device=dev, fft_lengths=[2048])
        bank.set_reference(w, delta_f=df)
        return bank.filter_series(x)
    other = "elect" if way == "gate" else "gate"
    a, b = run(way), run(other)
    assert a.sample_indices.size > 0
    assert set(asked) == {"gate", "elect"}, "the cascade's later tier never ran"
    for f in a._fields:
        np.testing.assert_array_equal(getattr(a, f), getattr(b, f))
