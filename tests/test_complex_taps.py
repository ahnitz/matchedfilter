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
