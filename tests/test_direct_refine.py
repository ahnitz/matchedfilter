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


def _run(direct, chain, data, binsize=None, monkeypatch=None, fd=1e-2):
    n, taps, counts, spec, series, layout, ref, window = data
    monkeypatch.setenv("MF_DIRECT_REFINE", "1" if direct else "0")
    # fd 1%, production's: at 1e-3 a noise peak elsewhere in the window is the last tier's
    # coarse maximum for more than the direct refine's share of the budget at any half-width
    # for chains ending at band 512, and those plans refine by transform
    hf = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=fd, chain=chain,
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
    if len(chain) > 1 or gatechain.cpu_gate_kind() != "f16":
        # (a one-tier chain's tier is the FP16 gate on ARM, which reports no lag: transform)
        assert st["pairs"] > 0, "the direct refine never ran: %s" % st
    np.testing.assert_array_equal(i1, i0)
    m = i0 >= 0
    np.testing.assert_allclose(v1[m], v0[m], rtol=2e-5, atol=1e-4)


def test_several_bins_refine_by_transform(monkeypatch):
    """A window cannot promise every bin's maximum: several bins per pair take the transform."""
    data = _bank(nblocks=40)
    i1, v1, st = _run(True, (256, 512), data, binsize=64, monkeypatch=monkeypatch, fd=1e-3)
    i0, v0, _ = _run(False, (256, 512), data, binsize=64, monkeypatch=monkeypatch, fd=1e-3)
    assert (i0 >= 0).sum() > 20
    assert st["pairs"] == 0
    np.testing.assert_array_equal(i1, i0)


def test_taps_are_checked():
    hf = mf.HierarchicalFilter(1024, 1, 4, snr=6.0, fd=1e-3)
    with pytest.raises(ValueError):
        hf.set_taps(np.zeros((3, 10), np.float32))
    with pytest.raises(ValueError):
        hf.set_taps(np.zeros((4, 10), np.float32), counts=[10, 10, 11, 10])


@pytest.mark.parametrize("fd", [1e-2, 1e-3])
def test_halfwidth_from_the_model(fd):
    """The half-width is the smallest that leaves at most the direct refine's share of the
    budget outside it, among the gate model's own kept draws; small at fd 1% where the last
    band localises the peak (512 at n = 2048 on an inspiral profile)."""
    from matchedfilter.benchmark import _inspiral_power
    n = 2048
    ref, win = _inspiral_power(n), (192, 1856)
    p = gatechain._norm_profile(ref, n)
    bands = gatechain.usable_bands(p, n)
    for chain in [(512,), (256, 512), (256, 512, 1024)]:
        pl = gatechain.chain_thresholds(ref, n, 6.0, fd, chain, window=win)
        hw, q, kept = gatechain.direct_halfwidth(ref, n, chain, pl["thresholds"], 6.0, fd, window=win)
        (C, F), (fat, cat) = gatechain.signal_draws(p, n, bands, 6.0, gatechain._gm._nsamp_for(fd),
                                                    window=win, lags_too=True)
        ok = F[:, 0] >= 6.0
        for b, t in zip(chain, pl["thresholds"]):
            ok &= C[:, bands.index(b)] >= t
        d = np.abs(fat - cat[:, bands.index(chain[-1])])[ok]
        d = np.minimum(d, n - d) / (n // chain[-1])
        allow = gatechain._LOCALISE_SHARE * fd * kept
        assert kept == ok.sum() > 5000
        assert (d > hw).sum() <= allow, (chain, hw)
        assert hw == 1 or (d > hw - 1).sum() > allow, (chain, hw)
        if fd == 1e-2:
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


def test_padded_one_bin_rows_refine_directly(monkeypatch):
    """A bin phase pads a row with empty bins so a call's rows share one bin count. A padded
    row whose window still lies in one bin is a one-bin pair: it takes the direct refine and
    reports exactly what its unpadded call reports, in its touched bin. Until 2026-10-23 the
    padded row took the transform (nb > 1), so a merged filter_series call and the separate
    calls of its windows differed by fp32 rounding wherever the direct refine is priced
    cheaper (arm64 CI: test_merged_equals_separate_calls[256-hier])."""
    data = _bank(nblocks=60)
    n, taps, counts, spec, series, layout, ref, window = data
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")

    def run(phase):
        hf = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-3, chain=(256, 512),
                                   search_window=window)
        hf.set_reference(ref); hf.set_templates(spec); hf.set_taps(taps, counts)
        kw = {} if phase is None else {"bin_phase": np.full(layout[0].size, phase, np.uint32)}
        idx, val = hf.run_series(series, *layout, binsize=n, threshold=6.0, raw=True, **kw)
        return idx.copy(), val.copy(), hf.direct_stats()

    i0, v0, s0 = run(None)
    i1, v1, s1 = run(n)                   # one empty bin first: nb = 2, the window in bin 1
    assert (i0 >= 0).sum() > 20 and s0["pairs"] > 0, s0
    assert i1.shape[-1] == 2 and i0.shape[-1] == 1
    assert s1["pairs"] == s0["pairs"], (s0, s1)
    assert np.all(i1[..., 0] < 0)
    np.testing.assert_array_equal(i1[..., 1], i0[..., 0])
    np.testing.assert_array_equal(v1[..., 1], v0[..., 0])


def test_plans_of_one_size_compare_the_same_direct_prices(monkeypatch):
    """Every plan of a size refines a survivor directly or by transform on prices timed once
    per process (_prices._direct_pair_prices), not on its own timing: two plans otherwise
    split the pairs near the boundary differently, and identical calls reported different
    fp32 roundings (a padded layout against its unpadded call)."""
    from matchedfilter import _prices
    data = _bank(nblocks=60)
    n, taps, counts, spec, series, layout, ref, window = data
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    monkeypatch.setattr(_prices, "_DIRECT_PAIR", {})

    def stats():
        hf = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-3, chain=(256, 512),
                                   search_window=window)
        hf.set_reference(ref); hf.set_templates(spec); hf.set_taps(taps, counts)
        hf.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)
        s = hf.direct_stats()
        return s["ticks_per_lag_tap"], s["ticks_per_fft_pair"]

    a, b = stats(), stats()
    assert a[0] > 0 and a[1] > 0, a
    assert a == b, (a, b)
    assert len(_prices._DIRECT_PAIR) == 1
