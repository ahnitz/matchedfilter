"""Paths the suite did not run before 2026-11-24 (line coverage of a run without a GPU):
the ends of a series, several windows in one tiled cascade, real and complex series in one
batch, a pinned chain, a reference taken away, the band-limited engine
with a bin size, and randomly drawn combinations of bank, series and call.

Each test compares against an answer that does not go through the path under test: the
definition of the correlation, the ungated bank, the flat engine, or the same calls made
one at a time.
"""
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank

RATE = 2048.0


def _bank_and_profile(rng, counts, quadrature=False):
    """Templates in a few families of near-identical members, their spectra following an
    inspiral-like output-power profile, and that profile on a fine grid (what the bank is
    handed as its reference). With quadrature the taps are the analytic filters, which a
    bank applies to a real series."""
    df = 1.0 / 16
    f = np.arange(int(RATE / 2 / df) + 1) * df
    w = np.where((f > 20) & (f < 900), np.maximum(f, 1.0) ** (-7.0 / 3), 0.0)
    families = [rng.random(4097) for _ in range(max(1, len(counts) // 6))]
    taps = []
    for c in counts:
        ff = np.fft.rfftfreq(c, 1 / RATE)
        phase = np.interp(ff, np.linspace(0, RATE / 2, 4097), families[rng.integers(len(families))])
        spec = np.sqrt(np.interp(ff, f, w)) * np.exp(
            2j * np.pi * (phase * rng.uniform(20, 200) + 0.02 * rng.random(ff.size)))
        h = np.fft.irfft(spec, c)
        h = h / np.linalg.norm(h)
        if quadrature:
            H = np.fft.fft(h)
            H[c // 2 + 1:] = 0
            H[1:(c + 1) // 2] *= 2
            taps.append((np.fft.ifft(H) / np.sqrt(2)).astype(np.complex64))
        else:
            taps.append(h.astype(np.float32))
    return taps, w, df


def _analytic(x):
    """The analytic series of a real one, at unit noise variance for unit white noise."""
    X = np.fft.fft(x)
    X[len(x) // 2:] = 0
    return (np.fft.ifft(X) * np.sqrt(2)).astype(np.complex64)


def _correlation(ser, h, sample):
    """The definition: the series against the taps, centred on the sample, the series taken
    as zero outside itself."""
    c = len(h)
    lo = sample - c // 2
    seg = np.zeros(c, np.complex128)
    a, b = max(lo, 0), min(lo + c, len(ser))
    if b > a:
        seg[a - lo:b - lo] = ser[a:b]
    return np.sum(seg * h)


def _keys(res, S):
    return res.template_indices.astype(np.int64) * (S + 1) + res.sample_indices.astype(np.int64)


def _assert_same_peaks(got, want, S, binsize, scale):
    """The two results hold the same peaks: the same (template, sample) with the same value,
    or, where two samples of a bin are within rounding of each other, either of them."""
    tol = 2e-4 * np.abs(want.snr) + 2e-6 * scale if len(want.snr) else 0.0
    kg, kw = _keys(got, S), _keys(want, S)
    assert len(kg) == len(kw)
    og, ow = np.argsort(kg), np.argsort(kw)
    same = kg[og] == kw[ow]
    dv = np.abs(np.abs(got.snr[og]) - np.abs(want.snr[ow]))
    assert np.all(dv <= (tol[ow] if len(kw) else 0.0)), float(dv.max())
    # a different sample is a tie: same template, same bin's reach, same value (checked above)
    moved = np.abs(got.sample_indices[og] - want.sample_indices[ow])[~same]
    assert np.all(got.template_indices[og][~same] == want.template_indices[ow][~same])
    assert np.all(moved < binsize) and (~same).sum() <= max(1, len(kw) // 200)


# ---------------------------------------------------------------- the ends of a series

@pytest.mark.parametrize("window, binsize", [((-64, None), 8), ((-3000, None), 500),
                                             ((-700, -3), 37)])
def test_peaks_at_the_end_of_a_series_are_the_correlation_with_zeros_beyond_it(window, binsize):
    """Where the taps reach past the last sample the series counts as zero there: for the
    whole ungated bank, and for a one-template call, whose few lags are correlated directly
    on a copy padded with zeros (followup.c)."""
    rng = np.random.default_rng(11)
    counts = [int(c) for c in rng.integers(300, 600, 8)]
    taps, w, df = _bank_and_profile(rng, counts)
    S = 20000
    ser = _analytic(rng.standard_normal(S))
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=6.5)
    bank.set_reference(w, delta_f=df)
    win = slice(*window)
    lo, hi, _ = win.indices(S)
    every = bank.filter_series(ser, windows=win, binsize=binsize, threshold=0.0)
    nbins = -(-(hi - lo) // binsize)
    for k in (0, 3, 7):
        v = np.abs([_correlation(ser, taps[k], s) for s in range(lo, hi)])
        want = np.array([lo + i * binsize + int(np.argmax(v[i * binsize:(i + 1) * binsize]))
                         for i in range(nbins)])
        one = bank.filter_series(ser, windows=win, binsize=binsize, threshold=0.0,
                                 template_index=k)
        sel = every.template_indices == k
        for samples, values in ((one.sample_indices, one.snr),
                                (every.sample_indices[sel], every.snr[sel])):
            order = np.argsort(samples)
            np.testing.assert_array_equal(samples[order], want)
            np.testing.assert_allclose(np.abs(values[order]), v[want - lo], rtol=2e-5)


# ---------------------------------------------------- several windows in a tiled cascade

def test_a_tiled_cascade_over_separate_windows_is_the_untiled_one(monkeypatch):
    """correlate_and_filter_many with analysis windows that leave gaps: the middle series
    and the leaf peaks are those of correlate_series followed by filter_series_many, over
    tiles small enough that a chunk holds blocks of more than one window."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_DIRECT_REFINE", "0")
    rng = np.random.default_rng(31)
    S, pad = 98304, 2048
    spans = [(6000, 21000), (26000, 27500), (40000, 71000), (80000, 92000)]
    leaf_w = [slice(a, b) for a, b in spans]
    corr_w = [slice(a - pad, b + pad) for a, b in spans]
    mid_counts = [int(c) for c in rng.integers(500, 1400, 4)]
    mid_taps, w, df = _bank_and_profile(rng, mid_counts)
    leaf_specs = [_bank_and_profile(rng, [int(c) for c in rng.integers(200, 380, 20)])[0]
                  for _ in mid_counts]
    ser = ((rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2)).astype(np.complex64)
    for at in (6001, 20990, 26800, 55555, 91000):
        ser[at - 64:at + 64] += np.float32(12.0) * np.exp(1j * np.linspace(0, 20, 128, dtype=np.float32))

    def banks():
        middle = TimeDomainFilterBank(mid_taps, tap_counts=mid_counts, engine="corr",
                                      device="cpu", fft_lengths=(4096,))
        leaves = []
        for taps in leaf_specs:
            leaf = TimeDomainFilterBank(taps, engine="hier", device="cpu", threshold=4.2,
                                        false_dismissal=1e-3, binsize=1024, fft_lengths=(2048,))
            leaf.set_reference(w, delta_f=df)
            leaves.append(leaf)
        return middle, leaves

    middle, leaves = banks()
    out_ref = np.zeros((len(mid_counts), S), np.complex64)
    middle.correlate_series(ser, windows=corr_w, out=out_ref)
    want = TimeDomainFilterBank.filter_series_many(
        [(leaf, out_ref[row], dict(windows=leaf_w)) for row, leaf in enumerate(leaves)])

    for tile_bytes in (32768, 4 << 20):
        middle, leaves = banks()
        out = np.full((len(mid_counts), S), -9.0 + 7.0j, np.complex64)
        got = TimeDomainFilterBank.correlate_and_filter_many(
            [(middle, ser, dict(windows=corr_w, out=out))],
            [(leaf, out[row], dict(windows=leaf_w)) for row, leaf in enumerate(leaves)],
            tile_bytes=tile_bytes)
        for cw in corr_w:
            np.testing.assert_array_equal(out[:, cw], out_ref[:, cw])
        assert sum(len(r.snr) for r in want) > 10
        for g, r in zip(got, want):
            np.testing.assert_array_equal(g.template_indices, r.template_indices)
            np.testing.assert_array_equal(g.sample_indices, r.sample_indices)
            np.testing.assert_allclose(g.snr, r.snr, rtol=1e-6, atol=0)
            inside = np.zeros(S, bool)
            for a, b in spans:
                inside[a:b] = True
            assert inside[g.sample_indices].all()


# ------------------------------------------------- real and complex series in one batch

def test_a_batch_of_real_and_complex_series_is_its_calls_one_at_a_time(monkeypatch):
    """One quadrature bank filters real series (transformed at half size) and complex ones
    in a single batch; the plan changes between the two forms inside the batch, and every
    job's peaks are those of the job run alone."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    rng = np.random.default_rng(41)
    counts = [int(c) for c in rng.integers(300, 600, 12)]
    taps, w, df = _bank_and_profile(rng, counts, quadrature=True)
    S = 40000
    series = []
    for i in range(6):
        x = rng.standard_normal(S)
        k = int(rng.integers(len(counts)))
        at = int(rng.integers(2000, S - 2000))
        x[at - counts[k] // 2: at - counts[k] // 2 + counts[k]] += 14.0 * np.sqrt(2) * taps[k].real
        series.append(x.astype(np.float32) if i % 2 == 0 else x.astype(np.complex64))

    def bank():
        b = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=6.0,
                                 false_dismissal=1e-3, binsize=256)
        b.set_reference(w, delta_f=df)
        return b

    one_bank = bank()
    got = TimeDomainFilterBank.filter_series_many([(one_bank, s, {}) for s in series])
    alone = bank()
    for s, g in zip(series, got):
        want = alone.filter_series(s)
        assert len(want.snr) > 0
        np.testing.assert_array_equal(g.template_indices, want.template_indices)
        np.testing.assert_array_equal(g.sample_indices, want.sample_indices)
        np.testing.assert_allclose(g.snr, want.snr, rtol=1e-5, atol=0)
    # the real and the complex form of one series give the same peaks
    twin = alone.filter_series(series[0].astype(np.complex64))
    base = alone.filter_series(series[0])
    np.testing.assert_array_equal(np.sort(_keys(twin, S)), np.sort(_keys(base, S)))


# ------------------------------------------------------- a pinned chain, no screeners

@pytest.mark.parametrize("band_hz", [64.0, (64.0, 256.0)])
def test_a_pinned_chain_over_near_identical_templates_reports_ungated_peaks(band_hz):
    """A bank whose chain the caller pins runs that chain, without shared screeners (those
    belong to a chain the model prices), over templates near enough to each other to share
    one. Each peak it reports is an ungated peak or the correlation at its sample, and loud
    signals are reported."""
    rng = np.random.default_rng(51)
    counts = [int(c) for c in rng.integers(300, 600, 48)]
    taps, w, df = _bank_and_profile(rng, counts)
    S = 1 << 16
    x = rng.standard_normal(S)
    planted = []
    for k, at in ((2, 9000), (17, 30011), (40, 51111)):
        x[at - counts[k] // 2: at - counts[k] // 2 + counts[k]] += 14.0 * np.sqrt(2) * taps[k]
        planted.append((k, at))
    ser = _analytic(x)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=6.5,
                                false_dismissal=1e-3, coarse_band_hz=band_hz,
                                fft_lengths=[2048])
    bank.set_reference(w, delta_f=df)
    gated = bank.filter_series(ser, binsize=256)
    every = bank.filter_series(ser, binsize=256, threshold=0.0)
    plan = bank._groups[0].plan
    assert tuple(plan._resolve().chain) == tuple(
        int(round(b / (RATE / 2048))) for b in np.atleast_1d(band_hz))
    assert plan._active_tier0_cluster() is None
    known = np.isin(_keys(gated, S), _keys(every, S))
    for i in np.flatnonzero(~known):
        t, s = int(gated.template_indices[i]), int(gated.sample_indices[i])
        assert abs(_correlation(ser, taps[t], s)) == pytest.approx(abs(gated.snr[i]), rel=2e-4)
    assert np.all(np.abs(gated.snr) >= 6.5 * (1 - 1e-5))
    for k, at in planted:
        near = (gated.template_indices == k) & (np.abs(gated.sample_indices - at) <= 1)
        assert near.any(), (k, at)


# ------------------------------------------------------------ a reference taken away

def test_a_reference_taken_away_leaves_nothing_to_run_and_comes_back_the_same():
    """set_reference(None) forgets the reference and what was planned on it: an unpinned
    filter then has no thresholds and says so, and the same reference set again gives the
    peaks it gave before."""
    from matchedfilter.gatechain import rebin_profile
    rng = np.random.default_rng(61)
    n, nt = 2048, 8
    counts = [int(c) for c in rng.integers(300, 600, nt)]
    taps, w, df = _bank_and_profile(rng, counts)
    power = rebin_profile(w, df, RATE, n)
    templates = np.zeros((nt, n), np.complex64)
    for i, (h, c) in enumerate(zip(taps, counts)):
        buf = np.zeros(n, np.float32)
        buf[:c] = h
        templates[i] = np.conj(np.fft.fft(np.roll(buf, -(c // 2))))
    x = rng.standard_normal(n)
    x[700 - counts[2] // 2: 700 - counts[2] // 2 + counts[2]] += 20.0 * np.sqrt(2) * taps[2]
    data = np.fft.fft(_analytic(x))[None, :].astype(np.complex64)

    hf = mf.HierarchicalFilter(n, ndata=1, ntemplates=nt, snr=5.5, fd=1e-2)
    hf.set_reference(power)
    hf.set_templates(templates)
    hf.set_data(data)
    first = np.array(hf.run(binsize=n, threshold=5.5))
    assert first["index"][0, 2, 0] >= 0              # the planted signal's template fires
    hf.set_reference(None)
    with pytest.raises(ValueError, match="reference"):
        hf.run(binsize=n, threshold=5.5)
    hf.set_reference(power)
    np.testing.assert_array_equal(np.array(hf.run(binsize=n, threshold=5.5)), first)


# ------------------------------------------------- the band-limited engine with bins

@pytest.mark.parametrize("binsize", [64, 200, 5000])
def test_the_band_limited_engine_with_a_bin_size_reports_the_flat_engines_peaks(binsize):
    """On a series with no power in the upper half band, the band-limited engine (two
    half-rate channels) reports the flat engine's peaks for a caller's bin size, over a
    window that leaves ragged bins at both ends."""
    rng = np.random.default_rng(71)
    taps = [rng.standard_normal(250).astype(np.float32) for _ in range(6)]
    S = 32768
    spec = np.fft.fft(rng.standard_normal(S) + 1j * rng.standard_normal(S))
    spec[int(S * 800 / RATE):] = 0
    ser = (np.fft.ifft(spec) * 10).astype(np.complex64)
    win = slice(3000, 29011)
    dif = TimeDomainFilterBank(taps, engine="dif", threshold=5.0)
    flat = TimeDomainFilterBank(taps, engine="flat", threshold=5.0)
    got = dif.filter_series(ser, windows=win, binsize=binsize)
    want = flat.filter_series(ser, windows=win, binsize=binsize)
    assert len(want.snr) > 20
    _assert_same_peaks(got, want, S, binsize, float(np.abs(want.snr).max()))


# ----------------------------------------------------------------- random combinations

def _random_case(seed):
    """One randomly drawn bank, series and call, checked against the bank's own ungated
    answer. Returns (loud ungated peaks, how many of them the gated call missed)."""
    rng = np.random.default_rng(seed)
    T = int(rng.choice([1, 2, 7, 16, 33, 64]))
    lo, hi = [(40, 120), (300, 600), (300, 900), (900, 1900), (60, 1900)][rng.integers(5)]
    counts = [int(c) for c in rng.integers(lo, hi, T)]
    quadrature = bool(rng.random() < 0.3)
    thr = float(rng.choice([5.5, 6.5, 8.0]))
    binsize = int(rng.choice([1, 37, 61, 128, 256, 500, 1024, 5000]))
    S = int(rng.choice([1 << 16, (1 << 16) + 4097, 30011, 9973]))
    taps, w, df = _bank_and_profile(rng, counts, quadrature)
    kw = dict(engine="hier", threshold=thr, false_dismissal=float(rng.choice([1e-3, 1e-2])))
    mode = int(rng.integers(3))
    if mode == 0:
        kw["binsize"] = binsize                       # the bank chooses its block size
    elif mode == 1:
        kw["fft_lengths"] = [int(rng.choice([2048, 4096]))]
    bank = TimeDomainFilterBank(taps, tap_counts=counts, **kw)
    bank.set_reference(w, delta_f=df)

    # white noise and signals in the real stream, made analytic unless the taps are
    x = rng.standard_normal(S)
    longest = max(counts)
    for _ in range(int(rng.integers(0, 12))):
        k = int(rng.integers(T))
        if S <= 3 * longest + 2:
            break
        at = int(rng.integers(longest, S - longest - 1))
        amp = float(rng.choice([thr - 0.5, thr + 0.5, thr + 4, 12, 30, 300]))
        x[at - counts[k] // 2: at - counts[k] // 2 + counts[k]] += amp * np.sqrt(2) * taps[k].real
    ser = x.astype(np.float32) if quadrature else _analytic(x)
    hazard = int(rng.integers(5))
    if hazard == 1:                                   # a gated span of exact zeros
        a = int(rng.integers(0, S - 1))
        ser[a:a + int(rng.integers(1, 5000))] = 0
    elif hazard == 2:                                 # one very loud sample
        ser[int(rng.integers(S))] += 1e5
    elif hazard == 3:                                 # zeros at both ends (padding)
        k = int(rng.integers(1, longest))
        ser[:k] = 0
        ser[-k:] = 0
    windows = None
    if rng.random() < 0.7:
        cuts = np.sort(rng.integers(0, S, 2 * int(rng.integers(1, 4))))
        windows = [slice(int(a), int(b)) for a, b in zip(cuts[::2], cuts[1::2])]
    call_bins = None if (mode != 0 and rng.random() < 0.5) else binsize
    one_template = int(rng.integers(T))

    gated = bank.filter_series(ser, windows=windows, binsize=call_bins)
    every = bank.filter_series(ser, windows=windows, binsize=call_bins, threshold=0.0)
    ke, kg = _keys(every, S), _keys(gated, S)
    what = "seed %d" % seed
    assert len(np.unique(ke)) == len(ke) and len(np.unique(kg)) == len(kg), what
    assert np.isfinite(every.snr).all() and np.isfinite(gated.snr).all(), what
    scale = float(np.abs(every.snr).max()) if len(ke) else 0.0
    # every gated peak is above the threshold, and is an ungated peak with the same value or
    # (a direct refine reads a few lags of a bin) the correlation at its own sample
    assert np.all(np.abs(gated.snr) >= thr * (1 - 1e-5)), what
    order = np.argsort(ke)
    at = np.minimum(np.searchsorted(ke[order], kg), max(len(ke) - 1, 0))
    known = (ke[order][at] == kg) if len(ke) else np.zeros(len(kg), bool)
    dv = np.abs(every.snr[order][at][known] - gated.snr[known])
    assert np.all(dv <= 2e-4 * np.abs(gated.snr[known]) + 2e-6 * scale), what
    for i in np.flatnonzero(~known):
        t, s = int(gated.template_indices[i]), int(gated.sample_indices[i])
        h = np.conj(taps[t]) if quadrature else taps[t]
        assert abs(abs(_correlation(ser, h, s)) - abs(gated.snr[i])) <= 2e-4 * abs(gated.snr[i]), what
    # a one-template call is the ungated bank's rows for it (peaks of exact zeros are ties)
    one = bank.filter_series(ser, windows=windows, binsize=call_bins, threshold=0.0,
                             template_index=one_template)
    keep = np.abs(one.snr) > 1e-3
    rows = (every.template_indices == one_template) & (np.abs(every.snr) > 1e-3)
    _assert_same_peaks(type(one)(*[np.asarray(getattr(one, f))[keep] for f in one._fields]),
                       type(every)(*[np.asarray(getattr(every, f))[rows] for f in every._fields]),
                       S, call_bins or int(max(bank.block_lengths)), scale)
    loud = np.abs(every.snr) >= thr + 3
    return int(loud.sum()), int((~np.isin(ke[loud], kg)).sum())


@pytest.mark.parametrize("first", [0, 40, 80])
def test_random_banks_series_and_calls_agree_with_their_ungated_answer(first):
    """Forty drawn cases a parameter: real and quadrature taps of 40 to 1900 samples, one to
    64 templates, series of odd lengths, up to three windows, bins of 1 to 5000 samples,
    block sizes chosen or pinned, with spans of zeros, a very loud sample or zero padding.
    The gated call's peaks are ungated peaks or correlations at their samples, a
    one-template call is the ungated bank's rows, and peaks 3 above the threshold are
    reported (the budget is one in a hundred to a thousand at the threshold itself)."""
    loud = missed = 0
    for seed in range(first, first + 40):
        n, m = _random_case(seed)
        loud += n
        missed += m
    assert loud > 1000
    assert missed <= 0.01 * loud, (missed, loud)
