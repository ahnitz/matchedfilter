"""The CPU direct refine: a survivor refined by direct correlation with its real taps at the
lags around its last tier's largest coarse lag must report exactly what the whole-block
transform reports (HierarchicalFilter.set_taps, hmf.c refine_direct_pair)."""
import os

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import gatechain
from matchedfilter.time_domain import template_spectra


def _bank(n=2048, T=48, nblocks=120, nsig=60, seed=3):
    """Data the gate model describes, as the consumer's are: the series is a reference-SNR
    series -- noise coloured by the inspiral SNR profile p, |z|^2 averaging 2, and signals as
    pulses with spectrum p -- and the fine filters are near-flat over the band (a centre tap
    plus a small smooth correction), so every template's output spectrum follows p. Then
    the coarse tiers localise a peak as the model's draws do (gatechain.direct_halfwidth)."""
    from matchedfilter.benchmark import _inspiral_power
    rng = np.random.default_rng(seed)
    counts = (2 * rng.integers(50, 200, T) + 1).astype(np.int64)
    taps = np.zeros((T, counts.max()), np.float32)
    for t in range(T):
        L = int(counts[t]); x = np.zeros(L)
        x[L // 2] = 1.0
        x += 0.15 * np.hanning(L) * np.cos(np.linspace(0, 3 + 0.1 * t, L)) / np.sqrt(L)
        taps[t, :L] = x.astype(np.float32)
    filt, valid = template_spectra(taps, counts, n)
    spec = np.conj(filt)                   # what TimeDomainFilterBank gives a plan
    cbad, vend = int(valid[:, 0].max()), int(valid[:, 1].min())
    step = vend - cbad
    total = 1 << int(np.ceil(np.log2(step * nblocks + n)))
    p = _inspiral_power(total); p = p / p.sum()
    w = (rng.standard_normal(total) + 1j * rng.standard_normal(total)) / np.sqrt(2)
    series = np.fft.ifft(np.sqrt(p) * w) * np.sqrt(total)
    series *= np.sqrt(2.0 / np.mean(np.abs(series) ** 2))
    pulse = np.fft.ifft(p) * total                        # the reference's correlation, peak 1
    # At most one signal per block, as in real data: with two above-threshold excursions in a
    # block, one bin per pair reports the one at the coarse maximum (test_two_excursions).
    gap = (total - 2 * n) // max(nsig, 1)
    for i in range(nsig):
        tau = n + i * gap + rng.integers(0, max(gap - 2 * n, 1))
        series += rng.uniform(6, 10) * np.exp(2j * np.pi * rng.random()) * np.roll(pulse, tau)
    series = series.astype(np.complex64)
    starts = np.arange(nblocks) * step
    layout = (starts, np.full(nblocks, cbad), np.full(nblocks, vend))
    q = n // 32
    window = ((cbad // q) * q, n - (cbad // q) * q)      # TimeDomainFilterBank._priced_window
    return n, taps, counts, spec, series, layout, _inspiral_power(n), window


def _run(direct, chain, data, binsize=None, monkeypatch=None):
    n, taps, counts, spec, series, layout, ref, window = data
    monkeypatch.setenv("MF_DIRECT_REFINE", "1" if direct else "0")
    hf = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-3, chain=chain,
                               search_window=window)
    hf.set_reference(ref); hf.set_templates(spec); hf.set_taps(taps, counts)
    idx, val = hf.run_series(series, *layout, binsize=binsize or n, threshold=6.0, raw=True)
    return idx.copy(), val.copy(), hf.direct_stats()


@pytest.mark.parametrize("chain", [(512,), (256, 512), (256, 512, 1024), (128, 256, 512)])
def test_direct_refine_matches_transform(chain, monkeypatch):
    data = _bank()
    i1, v1, st = _run(True, chain, data, monkeypatch=monkeypatch)
    i0, v0, _ = _run(False, chain, data, monkeypatch=monkeypatch)
    assert (i0 >= 0).sum() > 20, "the bank must produce triggers"
    assert st["pairs"] > 0, "the direct refine never ran: %s" % st
    np.testing.assert_array_equal(i1, i0)
    m = i0 >= 0
    np.testing.assert_allclose(v1[m], v0[m], rtol=2e-5, atol=1e-4)


def test_several_bins_refine_by_transform(monkeypatch):
    """A window cannot promise every bin's maximum: several bins per pair take the transform."""
    data = _bank(nblocks=40)
    i1, v1, st = _run(True, (256, 512), data, binsize=64, monkeypatch=monkeypatch)
    i0, v0, _ = _run(False, (256, 512), data, binsize=64, monkeypatch=monkeypatch)
    assert (i0 >= 0).sum() > 20
    assert st["pairs"] == 0
    np.testing.assert_array_equal(i1, i0)


def test_taps_are_checked():
    hf = mf.HierarchicalFilter(1024, 1, 4, snr=6.0, fd=1e-3)
    with pytest.raises(ValueError):
        hf.set_taps(np.zeros((3, 10), np.float32))
    with pytest.raises(ValueError):
        hf.set_taps(np.zeros((4, 10), np.float32), counts=[10, 10, 11, 10])


def test_halfwidth_from_the_model():
    """Small where the last band localises the peak (512 at n = 2048 on an inspiral profile);
    never below the distances it was drawn from."""
    from matchedfilter.benchmark import _inspiral_power
    n = 2048
    ref, win = _inspiral_power(n), (192, 1856)
    for chain in [(512,), (256, 512), (256, 512, 1024)]:
        pl = gatechain.chain_thresholds(ref, n, 6.0, 1e-3, chain, window=win)
        hw, q, kept = gatechain.direct_halfwidth(ref, n, chain, pl["thresholds"], 6.0, 1e-3,
                                                 window=win, nsim=4000)
        assert kept > 1000
        assert 1 <= hw and q <= hw, (chain, hw, q)
        assert hw <= 16, (chain, hw)


def test_two_excursions_in_a_block(monkeypatch):
    """The direct refine's one documented difference: with ONE bin per pair and TWO
    above-threshold excursions in a block (two signals, or a glitch's lobes), it reports the
    excursion at the last tier's coarse maximum, which need not be the larger fine one. Both
    are above threshold and either is a trigger; the transform reports the larger."""
    data = _bank(nblocks=24, nsig=0)
    n, taps, counts, spec, series, layout, ref, window = data
    from matchedfilter.benchmark import _inspiral_power
    total = len(series)
    p = _inspiral_power(total); p = p / p.sum()
    pulse = np.fft.ifft(p) * total
    s0 = int(layout[0][5]); w0, w1 = int(layout[1][5]), int(layout[2][5])
    series = series.astype(np.complex128)
    series += 9.0 * np.roll(pulse, s0 + w0 + 100) + 8.8 * np.roll(pulse, s0 + w1 - 100)
    data = (n, taps, counts, spec, series.astype(np.complex64), layout, ref, window)
    i1, _, _ = _run(True, (256, 512), data, monkeypatch=monkeypatch)
    i0, _, _ = _run(False, (256, 512), data, monkeypatch=monkeypatch)
    assert (i1[5] >= 0).all() and (i0[5] >= 0).all()       # every template reports a trigger
    near = lambda i, k: np.abs(i - k) < 30
    assert (near(i1[5], w0 + 100) | near(i1[5], w1 - 100)).all()   # one of the two
