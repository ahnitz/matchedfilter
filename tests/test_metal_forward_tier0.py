"""The fused forward (forward_tier0.slang) on Metal: the hierarchical fine stage writes only the
tiers' bands and recomputes its refine blocks; results must equal the separate forward+pack."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from test_time_domain import _whitened_inspiral_bank


def _run(monkeypatch, enabled, rng_seed=5):
    from conftest import usable_gpu
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_BAND_FORWARD", "1" if enabled else "0")
    rng = np.random.default_rng(rng_seed)
    counts = sorted(rng.integers(200, 1800, 24))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.0,
                                false_dismissal=1e-3, device=dev, fft_lengths=[2048])
    bank.set_reference(w, delta_f=df)
    S = 1 << 19
    X = np.fft.fft(rng.standard_normal(S))
    X[S // 2:] = 0
    x = (np.fft.ifft(X) * 2).astype(np.complex64)
    x[S // 3] += 40.0                        # a loud sample: refine survivors in many blocks
    jobs = [(bank, x, dict(windows=slice(4096, S - 4096)))] * 2
    out = TimeDomainFilterBank.filter_series_many(jobs)
    return [(r.sample_indices, r.template_indices, r.snr) for r in out]


def test_fused_forward_matches_separate(monkeypatch):
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
    assert len(a) == len(b)
    for (ia, ta, sa), (ib, tb, sb) in zip(a, b):
        assert len(ia) > 0
        np.testing.assert_array_equal(ia, ib)
        np.testing.assert_array_equal(ta, tb)
        np.testing.assert_array_equal(sa, sb)
