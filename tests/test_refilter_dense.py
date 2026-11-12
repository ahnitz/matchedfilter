"""A single-template call at threshold 0 (a search's follow-up: PeaksContext.refilter) returns
the loudest sample of every bin of its window, equal to the correlation computed directly."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank


def _direct(series, taps, lo, hi):
    """sum_k series[t + k - (L - 1) // 2] * conj(taps[k]) for t in [lo, hi): the bank's
    convention (X * conj(FFT(taps)), centred on the middle tap), in float64."""
    L = len(taps)
    c = (L - 1) // 2
    x = np.asarray(series, np.complex128)
    h = np.conj(np.asarray(taps, np.complex128))
    return np.array([np.dot(x[t - c:t - c + L], h) for t in range(lo, hi)])


@pytest.mark.parametrize("lane", [False, True])
@pytest.mark.parametrize("window, binsize", [((3000, 5040), 51), ((2500, 9000), 64),
                                              ((4000, 4700), 33)])
def test_dense_single_template_call_equals_direct_correlation(lane, window, binsize):
    """Real series (contiguous, or one lane of a packed pair) and complex taps, as a
    real-real-complex hierarchy's leaf bank filters. The window spans several blocks, and the
    bin size does not divide it, so a block edge cuts bins and the last bin is short."""
    rng = np.random.default_rng(5)
    counts = [157, 301, 499, 43]
    taps = np.zeros((4, 499), np.complex64)
    for i, c in enumerate(counts):
        taps[i, :c] = (rng.standard_normal(c) + 1j * rng.standard_normal(c)) / np.sqrt(c)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=6.0,
                                binsize=2048, false_dismissal=1e-3, fft_lengths=[1024])
    bank.set_reference(np.ones(513, np.float32), delta_f=2.0)
    S = 12000
    x = rng.standard_normal(S).astype(np.float32)
    if lane:
        pair = (x + 1j * rng.standard_normal(S)).astype(np.complex64)
        series = pair.real
        assert series.strides == (8,)
    else:
        series = x
    lo, hi = window
    for ti, c in enumerate(counts):
        res = bank.filter_series(series, windows=slice(lo, hi), binsize=binsize,
                                 threshold=0.0, template_index=ti)
        z = _direct(x, taps[ti, :c], lo, hi)
        nbins = -(-(hi - lo) // binsize)
        assert res.snr.size == nbins
        assert np.all(res.template_indices == ti)
        order = np.argsort(res.sample_indices)
        for b, j in enumerate(order):
            seg = z[b * binsize:(b + 1) * binsize]
            k = int(np.argmax(np.abs(seg)))
            assert res.sample_indices[j] == lo + b * binsize + k
            np.testing.assert_allclose(res.snr[j], seg[k], rtol=2e-4, atol=2e-4)


def test_one_call_and_a_batch_agree_with_direct_correlation_at_a_threshold():
    """The same request made alone (filter_series) and inside filter_series_many, at a
    threshold that keeps some bins and not others: both report exactly the bins whose loudest
    sample reaches the threshold, as the direct correlation gives them."""
    rng = np.random.default_rng(11)
    counts = [211, 487]
    taps = np.zeros((2, 487), np.complex64)
    for i, c in enumerate(counts):
        taps[i, :c] = (rng.standard_normal(c) + 1j * rng.standard_normal(c)) / np.sqrt(c)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=6.0,
                                binsize=2048, false_dismissal=1e-3, fft_lengths=[1024])
    bank.set_reference(np.ones(513, np.float32), delta_f=2.0)
    S, lo, hi, bs, thr = 20000, 4000, 15000, 51, 3.2
    x = rng.standard_normal(S).astype(np.float32)
    kw = [dict(windows=slice(lo, hi), binsize=bs, threshold=thr, template_index=ti)
          for ti in range(2)]
    alone = [bank.filter_series(x, **k) for k in kw]
    batch = TimeDomainFilterBank.filter_series_many([(bank, x, k) for k in kw])
    for ti, (a, b) in enumerate(zip(alone, batch)):
        z = _direct(x, taps[ti, :counts[ti]], lo, hi)
        want = {}
        for j in range(-(-(hi - lo) // bs)):
            seg = z[j * bs:(j + 1) * bs]
            k = int(np.argmax(np.abs(seg)))
            # bins within rounding of the threshold may fall either side: leave them out
            if abs(abs(seg[k]) - thr) > 1e-3:
                want[lo + j * bs + k] = seg[k] if abs(seg[k]) >= thr else None
        kept = {s: v for s, v in want.items() if v is not None}
        assert 20 < len(kept) < len(want)
        for res in (a, b):
            got = dict(zip(res.sample_indices.tolist(), res.snr.tolist()))
            assert set(kept) <= set(got)
            assert not (set(got) & {s for s, v in want.items() if v is None})
            for s, v in kept.items():
                np.testing.assert_allclose(got[s], v, rtol=2e-4, atol=2e-4)
