"""Complex (quadrature) taps on a real series: the fine filters of a real-real-complex FIR
hierarchy, the analytic version of each real filter, which turn the real middle series into
the complex SNR. Same convention as real taps: the series correlated against the taps,
z[t] = sum_k conj(taps[k]) x[t + k - m], m the centre tap."""
import numpy as np
import pytest

from matchedfilter.time_domain import TimeDomainFilterBank


def _quadrature_bank(rng, counts, rate=2048.0):
    """Analytic versions of inspiral-like real filters (positive frequencies, doubled), and
    the output-power profile on a fine grid, as the FIR bank builds them."""
    df = 1.0 / 16
    f = np.arange(int(rate / 2 / df) + 1) * df
    w = np.where((f > 20) & (f < 900), np.maximum(f, 1.0) ** (-7.0 / 3), 0.0)
    taps = np.zeros((len(counts), max(counts)), np.complex64)
    for i, c in enumerate(counts):
        ff = np.fft.fftfreq(c, 1 / rate)
        amp = np.sqrt(np.interp(np.abs(ff), f, w)) * (ff > 0) * 2.0
        h = np.fft.ifft(amp * np.exp(2j * np.pi * rng.random(c)))
        taps[i, :c] = (h / np.linalg.norm(h)).astype(np.complex64)
    return taps, w, df


def _direct(x, taps, c):
    m = (c - 1) // 2
    return np.convolve(x.astype(np.float64), np.conj(taps[:c]).astype(np.complex128)[::-1],
                       mode="full")[m: m + x.size]


def test_quadrature_taps_on_a_real_series_correlate():
    rng = np.random.default_rng(3)
    counts = [87, 160, 315, 401]
    taps, _, _ = _quadrature_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="corr")
    assert bank.complex_taps
    L = 1 << 15
    x = rng.standard_normal(L).astype(np.float32)
    res = bank.correlate_series(x)
    assert np.iscomplexobj(res)
    for i, c in enumerate(counts):
        ref = _direct(x, taps[i], c)
        g, _ = bank._template_map[i]
        sl = slice(g.c_bad, L - g.c_bad)
        err = np.max(np.abs(res[i, sl] - ref[sl])) / np.max(np.abs(ref[sl]))
        assert err < 1e-4, (c, err)
        # The output is the complex SNR: its imaginary part carries as much power as the real.
        q = np.mean(ref[sl].imag ** 2) / np.mean(ref[sl].real ** 2)
        assert 0.8 < q < 1.25


def _devices():
    import matchedfilter as mf
    out = ["cpu"]
    try:
        if any(str(d) == "gpu:0" for d in mf.devices()):
            out.append("gpu:0")
    except Exception:
        pass
    return out


@pytest.mark.parametrize("device", _devices())
@pytest.mark.parametrize("pack", [False, True])
def test_quadrature_taps_through_the_hierarchy(pack, device):
    """The hierarchical engine on a real series with quadrature taps: every trigger it reports
    is the correlation's value there, and every clear threshold crossing is reported."""
    rng = np.random.default_rng(4)
    counts = list(rng.integers(150, 401, 24))
    taps, w, df = _quadrature_bank(rng, counts)
    thr = 5.5
    hier = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=thr,
                                pack_templates=pack, binsize=2048)
    hier.set_reference(w, delta_f=df)
    corr = TimeDomainFilterBank(taps, tap_counts=counts, engine="corr")
    L = 1 << 18
    # Coloured real noise with loud template-shaped signals (real parts of the filters).
    x = np.fft.irfft(np.fft.rfft(rng.standard_normal(L)) *
                     np.sqrt(np.interp(np.fft.rfftfreq(L, 1 / 2048.0), np.arange(w.size) * df, w)
                             + 1e-12)).astype(np.float32)
    zc = corr.correlate_series(x)
    scale = 1.0 / np.sqrt(np.mean(np.abs(zc[:, 4096:-4096]) ** 2, axis=1) / 2)
    hier = TimeDomainFilterBank(taps * scale[:, None].astype(np.float32), tap_counts=counts,
                                engine="hier", threshold=thr, pack_templates=pack, binsize=2048,
                                device=device)
    hier.set_reference(w, delta_f=df)
    for j, i in enumerate(range(0, len(counts), 4)):
        pos = 20000 + j * (L - 40000) // 6
        c = counts[i]
        x[pos:pos + c] += (9.0 / scale[i]) * np.real(taps[i, :c][::-1]) / np.linalg.norm(taps[i, :c]) * 3
    zc = corr.correlate_series(x) * scale[:, None]
    res = hier.filter_series(x)
    assert res.snr.size > 0, "the injections must trigger"
    got = zc[res.template_indices, res.sample_indices]
    np.testing.assert_allclose(np.abs(res.snr), np.abs(got), rtol=2e-3, atol=2e-3)
    edge = 4096
    for i in range(len(counts)):
        a = np.abs(zc[i, edge:-edge])
        if a.max() > thr * 1.05:
            hit = res.sample_indices[res.template_indices == i]
            assert hit.size, "template %d: a crossing at %.2f was not reported" % (i, a.max())


@pytest.mark.parametrize("pack", [False, True])
def test_a_real_series_is_transformed_at_half_size_exactly(pack, monkeypatch):
    """A CPU hierarchical bank given a real series transforms its blocks as real ones
    (half-size transforms giving the full spectrum, ap_hmf_set_real_series): the same
    triggers and values, to float rounding, as the same series widened to complex."""
    rng = np.random.default_rng(8)
    counts = list(rng.integers(150, 401, 16))
    taps, w, df = _quadrature_bank(rng, counts)
    L = 1 << 18
    x = np.fft.irfft(np.fft.rfft(rng.standard_normal(L)) *
                     np.sqrt(np.interp(np.fft.rfftfreq(L, 1 / 2048.0), np.arange(w.size) * df, w)
                             + 1e-12)).astype(np.float32)
    x /= x.std()
    for j, i in enumerate(range(0, len(counts), 3)):
        c = counts[i]
        pos = 20000 + j * (L - 40000) // 6
        x[pos:pos + c] += 25.0 * np.real(taps[i, :c][::-1]) / np.linalg.norm(taps[i, :c])

    def run(real):
        monkeypatch.setenv("MF_REAL_SERIES", "1" if real else "0")
        # One chain for both (in Hz): a chain chosen per bank from timed calibrations may
        # differ between the two, and two chains may dismiss different borderline pairs.
        bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=5.5,
                                    pack_templates=pack, binsize=2048,
                                    coarse_band_hz=(128.0, 256.0))
        bank.set_reference(w, delta_f=df)
        r = bank.filter_series(x)
        order = np.lexsort((r.sample_indices, r.template_indices))
        return r.template_indices[order], r.sample_indices[order], r.snr[order]

    t0, s0, z0 = run(False)
    t1, s1, z1 = run(True)
    assert z0.size > 3, "the injections must trigger"
    np.testing.assert_array_equal(t0, t1)
    np.testing.assert_array_equal(s0, s1)
    np.testing.assert_allclose(z1, z0, rtol=1e-4, atol=1e-4 * np.abs(z0).max())


def test_a_lane_of_a_complex_series_is_read_in_place():
    """A real series that is one lane (real or imaginary part) of a complex array -- a packed
    pair of real middle series -- is filtered in place, with exactly the results of the same
    series made contiguous."""
    rng = np.random.default_rng(9)
    counts = list(rng.integers(150, 401, 12))
    taps, w, df = _quadrature_bank(rng, counts)
    L = 1 << 17
    a = rng.standard_normal(L).astype(np.float32)
    b = rng.standard_normal(L).astype(np.float32)
    for x in (a, b):
        for j, i in enumerate(range(0, len(counts), 3)):
            c = counts[i]
            pos = 10000 + j * (L - 20000) // 5
            x[pos:pos + c] += 25.0 * np.real(taps[i, :c][::-1]) / np.linalg.norm(taps[i, :c])
    packed = (a + 1j * b).astype(np.complex64)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=5.5,
                                binsize=2048, coarse_band_hz=(128.0, 256.0))
    bank.set_reference(w, delta_f=df)

    def run(x):
        r = bank.filter_series(x)
        order = np.lexsort((r.sample_indices, r.template_indices))
        return r.template_indices[order], r.sample_indices[order], r.snr[order]

    for lane, ref in ((packed.real, a), (packed.imag, b)):
        assert lane.strides == (8,)
        t0, s0, z0 = run(np.ascontiguousarray(ref))
        t1, s1, z1 = run(lane)
        assert z0.size > 3
        np.testing.assert_array_equal(t0, t1)
        np.testing.assert_array_equal(s0, s1)
        np.testing.assert_array_equal(z0, z1)


def test_a_followup_on_a_real_series_reads_only_its_span():
    """A single-template, threshold-0 call (a pycbc follow-up) on a real series -- or on one
    lane of a packed pair -- gives what it gives on the same series as complex; its plan has
    no real path, so only the window's blocks are widened."""
    rng = np.random.default_rng(10)
    counts = list(rng.integers(150, 401, 8))
    taps, w, df = _quadrature_bank(rng, counts)
    L = 1 << 18
    a = rng.standard_normal(L).astype(np.float32)
    packed = (a + 1j * rng.standard_normal(L)).astype(np.complex64)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=5.5,
                                binsize=2048)
    bank.set_reference(w, delta_f=df)
    kw = dict(windows=slice(100000, 100000 + 1000 * 61), binsize=61, threshold=0.0,
              template_index=3)
    ref = bank.filter_series(a.astype(np.complex64), **kw)
    for x in (a, packed.real):
        got = bank.filter_series(x, **kw)
        np.testing.assert_array_equal(got.sample_indices, ref.sample_indices)
        np.testing.assert_allclose(got.snr, ref.snr, rtol=1e-6, atol=1e-6 * np.abs(ref.snr).max())
        assert got.snr.size > 900


def test_a_real_series_correlates_at_half_size_exactly(monkeypatch):
    """correlate_series of a real series on the CPU (the middle stage of a real-real-complex
    hierarchy) runs half-size block transforms: the same output, to float rounding, as the
    series widened to complex -- for real taps and for packed (complex) pairs."""
    def pack_real_pairs(taps, counts):
        # two real filters as one complex filter, each keeping its own centre tap
        npair = (len(counts) + 1) // 2
        pc = np.array([max(counts[2 * q:2 * q + 2]) for q in range(npair)], dtype=np.int64)
        out = np.zeros((npair, pc.max()), np.complex64)
        for r, c in enumerate(counts):
            q, lane = divmod(r, 2)
            o = pc[q] // 2 - c // 2
            out[q, o:o + c] += (1.0 if lane == 0 else -1j) * taps[r, :c]
        return out, pc

    rng = np.random.default_rng(12)
    counts = np.sort(rng.integers(300, 3000, 9))
    taps = np.zeros((counts.size, counts.max()), np.float32)
    for i, c in enumerate(counts):
        taps[i, :c] = rng.standard_normal(c)
    L = 1 << 17
    x = rng.standard_normal(L).astype(np.float32)
    for t, c in ((taps, counts), pack_real_pairs(taps, counts)):
        bank = TimeDomainFilterBank(t, tap_counts=c, engine="corr")
        monkeypatch.setenv("MF_REAL_SERIES", "0")
        ref = bank.correlate_series(x)
        monkeypatch.setenv("MF_REAL_SERIES", "1")
        got = bank.correlate_series(x)
        np.testing.assert_allclose(got, ref, rtol=1e-5, atol=1e-5 * np.abs(ref).max())
