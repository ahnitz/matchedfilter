"""The fused forward (forward_tier0.slang) on Metal: the hierarchical fine stage writes only the
tiers' bands and recomputes its refine blocks; results must equal the separate forward+pack."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from test_time_domain import _whitened_inspiral_bank


#: How far two float paths' |snr| may differ: the GPU paths are 1.4-1.9e-5 from the CPU
#: reference on an M2 (three seeds); this is five times that.
SNR_TOL = 1e-4
THRESHOLD = 4.0


def _run(monkeypatch, enabled, device=None, rng_seed=5):
    from conftest import usable_gpu
    dev = usable_gpu() if device is None else device
    if dev is None:
        pytest.skip("no usable GPU")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_BAND_FORWARD", "1" if enabled else "0")
    rng = np.random.default_rng(rng_seed)
    counts = sorted(rng.integers(200, 1800, 24))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=THRESHOLD,
                                false_dismissal=1e-3, device=dev, fft_lengths=[2048])
    bank.set_reference(w, delta_f=df)
    S = 1 << 19
    X = np.fft.fft(rng.standard_normal(S))
    X[S // 2:] = 0
    x = (np.fft.ifft(X) * 2).astype(np.complex64)
    x[S // 3] += 40.0                        # a loud sample: refine survivors in many blocks
    jobs = [(bank, x, dict(windows=slice(4096, S - 4096)))] * 2
    out = TimeDomainFilterBank.filter_series_many(jobs)
    return [{(int(t), int(i)): complex(v) for t, i, v in
             zip(r.template_indices, r.sample_indices, r.snr)} for r in out]


def _assert_same_peaks(got, want, n, label):
    """Assert two peak sets {(template, sample): snr} agree to float precision.

    A peak both sides report must have the same complex SNR within SNR_TOL. A peak only
    one side reports is allowed only where rounding can decide it: its |snr| is within
    SNR_TOL of the threshold, or the other side reports a peak of the same template within
    one block whose |snr| ties it within SNR_TOL (two lags of one bin, elected differently).
    Anything else is a missed or spurious peak, and the message lists them."""
    common = set(got) & set(want)
    worst = max((abs(got[k] - want[k]) for k in common), default=0.0)
    assert worst <= SNR_TOL, "%s: SNR differs by %.2e on a common peak" % (label, worst)

    def explained(k, mine, other):
        a = abs(mine[k])
        if abs(a - THRESHOLD) <= SNR_TOL:
            return True
        return any(t == k[0] and abs(i - k[1]) < n and abs(abs(v) - a) <= SNR_TOL
                   for (t, i), v in other.items() if (t, i) not in mine)
    bad = ([("only " + label, k, abs(got[k])) for k in set(got) - set(want)
            if not explained(k, got, want)]
           + [("missing from " + label, k, abs(want[k])) for k in set(want) - set(got)
              if not explained(k, want, got)])
    assert not bad, bad


def test_fused_forward_matches_separate(monkeypatch):
    """The band forward and the separate forward each give the CPU reference's peaks.

    They are different float paths, so a peak within rounding of the threshold (or a lag
    tie inside a bin) may fall either way; exact equality between them is not a property
    of either. A peak missed or invented anywhere else fails."""
    pytest.importorskip("matchedfilter._mtlcompute")
    try:
        from matchedfilter import _mtlcompute
        _mtlcompute.Context(0).destroy()
    except Exception:
        pytest.skip("Metal not available")
    a = _run(monkeypatch, False)
    before = _mtlcompute._FUSED_FORWARDS[0]
    b = _run(monkeypatch, True)
    assert _mtlcompute._FUSED_FORWARDS[0] > before, "the fused forward was not taken"
    ref = _run(monkeypatch, False, device="cpu")
    assert len(a) == len(b) == len(ref)
    for ra, rb, rr in zip(a, b, ref):
        assert len(rr) > 100
        _assert_same_peaks(ra, rr, 2048, "separate forward")
        _assert_same_peaks(rb, rr, 2048, "band forward")
