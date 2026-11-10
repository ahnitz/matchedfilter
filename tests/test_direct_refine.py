"""The CPU direct refine: a survivor refined by direct correlation with its real taps at the
lags around its last tier's largest coarse lag must report exactly what the whole-block
transform reports (HierarchicalFilter.set_taps, hmf.c refine_direct_pair)."""
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
    the coarse tiers localise a peak as the model's draws do (gatechain._distances)."""
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
def test_halfwidth_shares_the_budget(fd):
    """The direct refine's window and the tiers share one budget (gatechain.plan_chain): on the
    fit half of the model's detections, those some tier dismisses or the window misses (the
    fine maximum further than the half-width from the last tier's coarse maximum) number
    exactly j - 1 (gatemodel.fit_order), so the window's misses come out of the tiers' share
    instead of adding to it. The half-width is a whole number of coarse samples, and the same
    chain priced without the direct refine refines by transform and gives the tiers it all."""
    import json
    from pathlib import Path
    from matchedfilter.benchmark import _inspiral_power
    n = 2048
    ref, win = _inspiral_power(n), (192, 1856)
    p = gatechain._norm_profile(ref, n)
    bands = gatechain.usable_bands(p, n)
    rec = json.loads((Path(__file__).parent / "data" / "cost_model_2048_zen5.json").read_text())
    cm = gatechain.CostModel.from_dict(rec["model"]).unscreened()
    direct = cm.with_direct(0.09 * 256 + 4.0)      # ticks per lag of a 256-tap window on Zen 5
    (C, F), (fat, cat) = gatechain.signal_draws(p, n, bands, 6.0, gatechain.model_draws(fd)[0],
                                                window=win, lags_too=True)
    det = F[:, 0] >= 6.0
    fit = np.zeros(det.sum(), bool)
    fit[1::2] = True                                  # the fit half: every other detection
    j = gatechain._gm.fit_order(fd)
    windows = 0
    for chain in [(512,), (256, 512), (256, 512, 1024)]:
        pl = gatechain.chain_thresholds(ref, n, 6.0, fd, chain, cost=direct, window=win)
        plain = gatechain.chain_thresholds(ref, n, 6.0, fd, chain, cost=cm, window=win)
        assert plain["halfwidth"] is None and plain["search"]["halfwidth"] is None
        hw = pl["halfwidth"]
        lost = np.zeros(det.sum(), bool)
        for b, t in zip(chain, pl["thresholds"]):
            lost |= C[det, bands.index(b)] < t
        tiers = int(np.count_nonzero(lost[fit]))
        if hw is not None:
            assert isinstance(hw, int) and hw >= 1, (chain, hw)
            far = np.abs(fat[det] - cat[det, bands.index(chain[-1])]) / (n // chain[-1]) > hw
            assert (np.count_nonzero(far[~fit]) == pl["search"]["missed"]
                    <= gatechain._gm.window_allowance(fd, int((~fit).sum()), int(fit.sum()))), chain
            lost |= far
            windows += 1
        assert np.count_nonzero(lost[fit]) == j - 1, (chain, hw)
        if hw is not None and np.count_nonzero(lost[fit]) > tiers:
            # the window's misses came out of the tiers' share: they dismiss less than alone
            alone = np.zeros(det.sum(), bool)
            for b, t in zip(chain, plain["thresholds"]):
                alone |= C[det, bands.index(b)] < t
            assert tiers < np.count_nonzero(alone[fit]) == j - 1, chain
    assert windows >= 2, windows          # the direct refine is priced in, and chosen


def test_a_plans_window_misses_no_more_than_the_allowance():
    """A plan's window misses at most gatemodel.window_allowance of the search half (here 15 of
    4,699 at fd 1%), though the budget (46) would pay for a cheaper window: on an f^-1 profile a
    one-tier chain at band 1024 searched against the whole budget takes a window missing 31,
    which the fit half then fails to hold often enough to break the tail bound."""
    import json
    from pathlib import Path
    rec = json.loads((Path(__file__).parent / "data" / "cost_model_2048_zen5.json").read_text())
    cm = gatechain.CostModel.from_dict(rec["model"]).unscreened().with_direct(0.09 * 256 + 4.0)
    n, fd, win = 2048, 1e-2, (192, 1856)
    p = np.zeros(n)
    p[1:n // 2] = 1.0 / np.arange(1, n // 2)
    pl = gatechain.chain_thresholds(p, n, 6.0, fd, (1024,), cost=cm, window=win)
    m = gatechain.model_draws(fd)[0] // 2
    allow = gatechain._gm.window_allowance(fd, m, m)
    assert allow == 15
    assert pl["search"]["halfwidth"] is not None and pl["search"]["missed"] <= allow, pl["search"]


def test_windows_miss_no_more_than_the_allowance():
    """The candidate half-widths (gatechain._halfwidths) start at the smallest whose window
    misses at most the allowance of the search half's detections (gatemodel.window_allowance),
    each the smallest with its set of misses; where only a window priced above the transform
    would miss so few, or the allowance is -1, the transform is the only candidate."""
    import json
    from pathlib import Path
    rec = json.loads((Path(__file__).parent / "data" / "cost_model_2048_zen5.json").read_text())
    cm = gatechain.CostModel.from_dict(rec["model"]).unscreened().with_direct(0.09 * 256 + 4.0)
    n, chain = 2048, (256, 512)
    rng = np.random.default_rng(5)
    # near misses a few coarse samples out, and three far ones no window priced below the
    # transform reaches (a noise peak elsewhere in the block was the coarse maximum)
    dist = np.concatenate([np.abs(rng.normal(0, 1.2, 4000)), rng.uniform(300, 400, 3)])
    for allow in (0, 2):
        assert gatechain._halfwidths(dist, allow, cm, chain, n) == (None,), allow
    for allow in (3, 5, 21, 29):
        hws = gatechain._halfwidths(dist, allow, cm, chain, n)
        assert hws[0] is None and len(hws) > 1, (allow, hws)
        h0 = hws[1]
        assert np.count_nonzero(dist > h0) <= allow
        assert h0 == 1 or np.count_nonzero(dist > h0 - 1) > allow, (allow, h0)
        for h in hws[2:]:
            assert np.count_nonzero(dist > h) < np.count_nonzero(dist > h - 1), (allow, h)
    assert gatechain._halfwidths(dist, -1, cm, chain, n) == (None,)


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
        # fd 1% (as _run): at 1e-3 a chain ending at band 512 refines a wide window, which a
        # back end pricing the direct refine dearer (AVX: 4x the ticks per lag) does by transform
        hf = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=(256, 512),
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


@pytest.mark.parametrize("real_kind", ["complex", "real_contig", "real_stride2"])
@pytest.mark.parametrize("complex_taps", [False, True])
def test_direct_refine_real_and_complex_combinations(real_kind, complex_taps, monkeypatch):
    """Direct refine handles all {real (stride 1 & 2), complex} x {real, complex} tap/series
    combinations and matches the whole-block transform."""
    from matchedfilter.benchmark import _inspiral_power
    rng = np.random.default_rng(17)
    n, T, nblocks, nsig = 2048, 32, 48, 24
    counts = (2 * rng.integers(48, 128, T) + 1).astype(np.int64)
    if complex_taps:
        taps = np.zeros((T, counts.max()), np.complex64)
        for t in range(T):
            L = int(counts[t])
            ph = 0.4 + 0.05 * t
            w = np.zeros(L, np.complex128)
            w[L // 2] = np.exp(1j * ph)
            w += 0.15 * np.hanning(L) * np.exp(1j * np.linspace(0, 3 + 0.1 * t, L)) / np.sqrt(L)
            taps[t, :L] = w.astype(np.complex64)
    else:
        taps = np.zeros((T, counts.max()), np.float32)
        for t in range(T):
            L = int(counts[t])
            x = np.zeros(L)
            x[L // 2] = 1.0
            x += 0.15 * np.hanning(L) * np.cos(np.linspace(0, 3 + 0.1 * t, L)) / np.sqrt(L)
            taps[t, :L] = x.astype(np.float32)
    filt, valid = template_spectra(taps, counts, n)
    spec = np.conj(filt)
    cbad, vend = int(valid[:, 0].max()), int(valid[:, 1].min())
    step = vend - cbad
    # include a partial trailing block so zero-padded edge gathering is exercised too
    total = step * (nblocks - 1) + vend + 7
    tot_fft = 1 << int(np.ceil(np.log2(total + n)))
    p = _inspiral_power(tot_fft); p = p / p.sum()
    if real_kind == "complex":
        w = (rng.standard_normal(tot_fft) + 1j * rng.standard_normal(tot_fft)) / np.sqrt(2)
        full = np.fft.ifft(np.sqrt(p) * w) * np.sqrt(tot_fft)
        full *= np.sqrt(2.0 / np.mean(np.abs(full) ** 2))
        pulse = np.fft.ifft(p) * tot_fft
        gap = (total - 2 * n) // max(nsig, 1)
        for i in range(nsig):
            tau = cbad + 64 + i * gap
            full += rng.uniform(8.5, 11.0) * np.exp(2j * np.pi * rng.random()) * np.roll(pulse, tau)
        series = full[:total].astype(np.complex64)
    else:
        # One-sided positive-frequency inspiral profile: real series filtered by analytic/real taps
        p1 = p.copy()
        p1[tot_fft // 2:] = 0.0
        p1 /= p1.sum()
        w = rng.standard_normal(tot_fft)
        W = np.fft.rfft(w)
        S = np.zeros_like(W)
        m = min(len(S), tot_fft // 2)
        S[:m] = W[:m] * np.sqrt(p1[:m] * tot_fft)
        full = np.fft.irfft(S, n=tot_fft)
        full /= np.std(full)
        pulse = np.real(np.fft.ifft(p1) * tot_fft) * 2.0
        gap = (total - 2 * n) // max(nsig, 1)
        for i in range(nsig):
            tau = cbad + 64 + i * gap
            full += rng.uniform(8.5, 11.0) * np.roll(pulse, tau)
        rser = full[:total].astype(np.float32)
        if real_kind == "real_stride2":
            packed = np.empty(total, np.complex64)
            packed.real = rng.standard_normal(total).astype(np.float32)
            packed.imag = rser
            series = packed.imag    # stride-8 float32 view
        else:
            series = rser

    starts = np.arange(nblocks) * step
    layout = (starts, np.full(nblocks, cbad), np.full(nblocks, vend))
    q = n // 32
    window = ((cbad // q) * q, n - (cbad // q) * q)
    ref = _inspiral_power(n)
    if real_kind != "complex":
        ref = ref.copy()
        ref[n // 2:] = 0.0
    data = (n, taps, counts, spec, series, layout, ref, window)

    # Use the direct plan's exact coarse thresholds on the transform plan so both pass the
    # identical survivor set to refine.
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    hf1 = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=(256, 512),
                                search_window=window)
    hf1.set_reference(ref); hf1.set_templates(spec); hf1.set_taps(taps, counts)
    i1, v1 = hf1.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)
    i1, v1, st = i1.copy(), v1.copy(), hf1.direct_stats()
    thr = hf1._resolve().thresholds

    monkeypatch.setenv("MF_DIRECT_REFINE", "0")
    hf0 = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=(256, 512),
                                search_window=window)
    hf0.set_reference(ref); hf0.set_templates(spec); hf0.set_coarse_threshold(thr)
    i0, v0 = hf0.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)
    assert (i0 >= 0).sum() > 15
    assert st["pairs"] > 0, st
    np.testing.assert_array_equal(i1, i0)
    m = i0 >= 0
    np.testing.assert_allclose(v1[m], v0[m], rtol=2e-5, atol=1e-4)


def test_time_domain_bank_complex_taps_uses_direct_refine(monkeypatch):
    """TimeDomainFilterBank passes complex64 taps to HierarchicalFilter so real-series +
    complex-taps consumer calls take direct refine instead of whole-block IFFTs."""
    from matchedfilter.benchmark import _inspiral_power
    rng = np.random.default_rng(29)
    n, T = 2048, 24
    counts = np.full(T, 161, np.int64)
    taps = np.zeros((T, 161), np.complex64)
    for t in range(T):
        L = 161
        w = np.zeros(L, np.complex128)
        w[L // 2] = np.exp(1j * 0.2 * t)
        w += 0.1 * np.hanning(L) * np.exp(1j * np.linspace(0, 2.5, L)) / np.sqrt(L)
        taps[t] = w.astype(np.complex64)
    ref = _inspiral_power(n).copy()
    ref[n // 2:] = 0.0
    total = 32768
    p1 = _inspiral_power(total).copy()
    p1[total // 2:] = 0.0
    p1 /= p1.sum()
    W = np.fft.rfft(rng.standard_normal(total))
    S = np.zeros_like(W)
    S[:total // 2] = W[:total // 2] * np.sqrt(p1[:total // 2] * total)
    x = (np.fft.irfft(S, n=total) / np.std(np.fft.irfft(S, n=total))).astype(np.float64)
    pulse = np.real(np.fft.ifft(p1) * total) * 2.0
    for tau in (4096, 12000, 22000):
        x += 8.5 * np.roll(pulse, tau)
    x = x.astype(np.float32)

    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    b_dir = mf.TimeDomainFilterBank(taps, counts, tap_sample_rate=2048.0, data_sample_rate=2048.0,
                                    threshold=6.0, false_dismissal=1e-2, fft_lengths=(n,))
    b_dir.set_reference(ref)
    r_dir = b_dir.filter_series(x)
    dir_pairs = sum(g.plan.direct_stats().get("pairs", 0) for g in b_dir._groups if g.is_hier)
    assert dir_pairs > 0

    monkeypatch.setenv("MF_DIRECT_REFINE", "0")
    b_fft = mf.TimeDomainFilterBank(taps, counts, tap_sample_rate=2048.0, data_sample_rate=2048.0,
                                    threshold=6.0, false_dismissal=1e-2, fft_lengths=(n,))
    b_fft.set_reference(ref)
    r_fft = b_fft.filter_series(x)
    assert len(r_dir.template_indices) > 10
    np.testing.assert_array_equal(r_dir.template_indices, r_fft.template_indices)
    np.testing.assert_array_equal(r_dir.sample_indices, r_fft.sample_indices)
    np.testing.assert_allclose(r_dir.snr, r_fft.snr, rtol=2e-5, atol=1e-4)


def test_straddling_window_bins_refine_per_survivor_and_price_one_bin_fraction(monkeypatch):
    """Blocks touching up to HMF_MAX_DIRECT_BINS (4) window bins refine directly per survivor
    (fraction 1.0 at binsize=2048, n=2048 where straddling blocks touch 2 bins), while at
    binsize=512 (n_valid=1726) 4-bin blocks take direct refine and 5-bin straddling blocks fall
    back to the whole-block transform weighted by (4 * binsize - n_valid + 1) / binsize."""
    from matchedfilter.benchmark import _inspiral_power
    rng = np.random.default_rng(43)
    n, T = 2048, 20
    counts = np.full(T, 323, np.int64)
    taps = np.zeros((T, 323), np.complex64)
    for t in range(T):
        w = np.zeros(323, np.complex128)
        w[161] = np.exp(1j * 0.15 * t)
        w += 0.12 * np.hanning(323) * np.exp(1j * np.linspace(0, 2.8, 323)) / np.sqrt(323)
        taps[t] = w.astype(np.complex64)
    ref = _inspiral_power(n).copy()
    ref[n // 2:] = 0.0
    total = 65536
    p1 = _inspiral_power(total).copy()
    p1[total // 2:] = 0.0
    p1 /= p1.sum()
    W = np.fft.rfft(rng.standard_normal(total))
    S = np.zeros_like(W)
    S[:total // 2] = W[:total // 2] * np.sqrt(p1[:total // 2] * total)
    x = np.fft.irfft(S, n=total)
    x = (x / np.std(x)).astype(np.float64)
    pulse = np.real(np.fft.ifft(p1) * total) * 2.0
    # Inject signals across many phases so 1..5-bin straddling blocks fire
    for tau in range(4200, 60000, 2350):
        x += 9.0 * np.roll(pulse, tau)
    x = x.astype(np.float32)

    monkeypatch.setenv("MF_AUTOTUNE", "0")
    for binsize, expect_full_direct in ((2048, True), (512, False)):
        monkeypatch.setenv("MF_DIRECT_REFINE", "1")
        b_dir = mf.TimeDomainFilterBank(taps, counts, tap_sample_rate=2048.0, data_sample_rate=2048.0,
                                        threshold=6.0, false_dismissal=1e-2, binsize=binsize,
                                        fft_lengths=(n,))
        b_dir.set_reference(ref)
        for g in b_dir._groups:
            if g.is_hier:
                frac = getattr(g.plan, "_one_bin_frac", None)
                if expect_full_direct:
                    assert frac == 1.0, frac
                else:
                    assert frac is not None and 0.5 < frac < 0.7, frac
        r_dir = b_dir.filter_series(x, windows=slice(4096, 61440))
        st = [g.plan.direct_stats() for g in b_dir._groups if g.is_hier][0]
        assert st["pairs"] > 0, st
        if expect_full_direct:
            assert st["fft"] == 0, st
        else:
            assert st["fft"] > 0, st

        monkeypatch.setenv("MF_DIRECT_REFINE", "0")
        b_fft = mf.TimeDomainFilterBank(taps, counts, tap_sample_rate=2048.0, data_sample_rate=2048.0,
                                        threshold=6.0, false_dismissal=1e-2, binsize=binsize,
                                        fft_lengths=(n,))
        b_fft.set_reference(ref)
        r_fft = b_fft.filter_series(x, windows=slice(4096, 61440))
        assert len(r_dir.sample_indices) > 20
        np.testing.assert_array_equal(r_dir.template_indices, r_fft.template_indices)
        np.testing.assert_array_equal(r_dir.sample_indices, r_fft.sample_indices)
        np.testing.assert_allclose(r_dir.snr, r_fft.snr, rtol=2e-5, atol=2e-4)


def test_multitier_q15_last_tier_supplies_coarse_lag_to_direct_refine(monkeypatch):
    """A multi-tier plan with Q15 enabled gates its last coarse tier in Q15 at high survivor
    density while electing each survivor's coarse argmax lag for direct time-domain refinement."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    data = _bank(nblocks=60)
    n, taps, counts, spec, series, layout, ref, window = data
    if mf._core.MF(256, 1, 1).q15_lanes() == 0:
        pytest.skip("no Q15 screen on this target")
    hf = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=(256, 512),
                               search_window=window)
    hf.set_reference(ref); hf.set_templates(spec); hf.set_taps(taps, counts)
    hf.lock_arm(mf._settings.arm("q15", True))
    thr = (1.5, hf._resolve().thresholds[1])
    hf._execution_plan().set_thresholds(list(thr))
    idx_q, val_q = hf.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)
    st_q = hf.direct_stats()
    assert hf._mf.q15_stats()[1] > 0
    assert st_q["pairs"] > 0, st_q
    monkeypatch.setenv("MF_DIRECT_REFINE", "0")
    hf_ref = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=(256, 512),
                                   search_window=window)
    hf_ref.set_reference(ref); hf_ref.set_templates(spec); hf_ref.set_coarse_threshold(thr)
    hf_ref.lock_arm(mf._settings.arm("q15", True))
    idx_f, val_f = hf_ref.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)
    assert (idx_f >= 0).sum() > 15
    np.testing.assert_array_equal(idx_q, idx_f)
    m = idx_f >= 0
    np.testing.assert_allclose(val_q[m], val_f[m], rtol=2e-5, atol=1e-4)


@pytest.mark.parametrize("n,binsize,phase_mode", [
    (2048, 900, "zero"),        # ntouch = 2
    (2048, 650, "sub"),         # ntouch = 3 with 0 < ph < binsize
    (2048, 560, "padded"),      # ntouch = 4 with ph >= binsize (leading empty bin)
    (4096, 2048, "continuous"), # 1s binning on n=4096 (ntouch = 2..3)
])
@pytest.mark.parametrize("chain", [(512,), (256, 512), (256, 512, 1024)])
def test_multibin_direct_refine_phases_and_chains(n, binsize, phase_mode, chain, monkeypatch):
    """Multi-bin direct refine (2 <= ntouch <= 4) matches the whole-block transform across
    zero, sub-bin, and padded bin phases and across 1-tier, pair-batched, and balanced final tiers."""
    data = _bank(n=n, T=32, nblocks=48, nsig=28, seed=11)
    _, taps, counts, spec, series, layout, ref, window = data
    starts, w0, w1 = layout
    nblk = len(starts)
    if phase_mode == "zero":
        bph = None
    elif phase_mode == "sub":
        bph = np.full(nblk, binsize // 3, dtype=np.uint32)
    elif phase_mode == "padded":
        bph = np.full(nblk, binsize + binsize // 4, dtype=np.uint32)
    else:
        raw = ((starts + w0) % binsize).astype(np.uint32)
        nbe = (w1 - w0 + raw + binsize - 1) // binsize
        bph = (raw + (int(nbe.max()) - nbe) * binsize).astype(np.uint32)

    kw = {} if bph is None else {"bin_phase": bph}
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    hf1 = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=chain,
                                search_window=window)
    hf1.set_reference(ref); hf1.set_templates(spec); hf1.set_taps(taps, counts)
    i1, v1 = hf1.run_series(series, starts, w0, w1, binsize=binsize, threshold=6.0, raw=True, **kw)
    i1, v1, st = i1.copy(), v1.copy(), hf1.direct_stats()
    thr = hf1._resolve().thresholds

    monkeypatch.setenv("MF_DIRECT_REFINE", "0")
    hf0 = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=chain,
                                search_window=window)
    hf0.set_reference(ref); hf0.set_templates(spec); hf0.set_coarse_threshold(thr)
    i0, v0 = hf0.run_series(series, starts, w0, w1, binsize=binsize, threshold=6.0, raw=True, **kw)

    assert (i0 >= 0).sum() > 15
    if len(chain) > 1 or gatechain.cpu_gate_kind() != "f16":
        assert st["pairs"] > 0, st
    np.testing.assert_array_equal(i1, i0)
    m = i0 >= 0
    np.testing.assert_allclose(v1[m], v0[m], rtol=2e-5, atol=1e-4)


@pytest.mark.parametrize("use_q15_last", [False, True])
def test_multibin_per_bin_coarse_election_with_loud_neighbor_excursion(use_q15_last, monkeypatch):
    """When two or more output bins in the same block each contain an above-threshold signal
    (e.g. a loud SNR ~ 14 excursion in one bin and an SNR ~ 8 signal near a bin boundary in
    another), per-bin coarse election refines both bins and matches the whole-block transform."""
    from matchedfilter.benchmark import _inspiral_power
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_GATE16", "0")
    if use_q15_last and mf._core.MF(256, 1, 1).q15_lanes() == 0:
        pytest.skip("no Q15 screen on this target")

    data = _bank(n=2048, T=32, nblocks=24, nsig=0, seed=21)
    n, taps, counts, spec, series, layout, ref, window = data
    starts, w0, w1 = layout
    total = len(series)
    p = _inspiral_power(total); p /= p.sum()
    pulse = np.fft.ifft(p) * total

    binsize = 560  # n_valid ~ 1660 -> 3..4 bins
    bph = np.full(len(starts), 180, dtype=np.uint32)
    s = series.astype(np.complex128)
    # Block 3: loud SNR 14 excursion in bin 2 AND SNR 8.2 signal right near bin 0/1 boundary
    s0 = int(starts[3]); lo = int(w0[3])
    boundary = lo + (binsize - 180)
    s += 14.5 * np.exp(0.7j) * np.roll(pulse, s0 + boundary + binsize + 120)
    s += 8.2 * np.exp(-1.1j) * np.roll(pulse, s0 + boundary - 3)
    # Block 7: signals in three separate bins
    s7 = int(starts[7]); lo7 = int(w0[7]); b7 = lo7 + (binsize - 180)
    s += 13.0 * np.roll(pulse, s7 + lo7 + 90)
    s += 8.5 * np.exp(1.3j) * np.roll(pulse, s7 + b7 + 200)
    s += 9.1 * np.exp(-0.5j) * np.roll(pulse, s7 + b7 + binsize + 150)
    series = s.astype(np.complex64)

    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    hf1 = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=(256, 512),
                                search_window=window)
    hf1.set_reference(ref); hf1.set_templates(spec); hf1.set_taps(taps, counts)
    if use_q15_last:
        hf1.lock_arm(mf._settings.arm("q15", True))
        thr = (1.5, hf1._resolve().thresholds[1])
        hf1._execution_plan().set_thresholds(list(thr))
    else:
        thr = hf1._resolve().thresholds
    i1, v1 = hf1.run_series(series, starts, w0, w1, binsize=binsize, threshold=6.0, raw=True,
                            bin_phase=bph)
    i1, v1, st = i1.copy(), v1.copy(), hf1.direct_stats()

    monkeypatch.setenv("MF_DIRECT_REFINE", "0")
    hf0 = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, chain=(256, 512),
                                search_window=window)
    hf0.set_reference(ref); hf0.set_templates(spec); hf0.set_coarse_threshold(thr)
    if use_q15_last:
        hf0.lock_arm(mf._settings.arm("q15", True))
    i0, v0 = hf0.run_series(series, starts, w0, w1, binsize=binsize, threshold=6.0, raw=True,
                            bin_phase=bph)

    assert st["pairs"] > 0, st
    assert (i0[3] >= 0).sum() >= 2 * spec.shape[0]
    assert (i0[7] >= 0).sum() >= 3 * spec.shape[0]
    np.testing.assert_array_equal(i1, i0)
    m = i0 >= 0
    np.testing.assert_allclose(v1[m], v0[m], rtol=2e-5, atol=1e-4)


@pytest.mark.parametrize("isa", mf.targets())
@pytest.mark.parametrize("real_quadrature", [False, True])
def test_direct_refine_multi_isa_odd_and_tail_windows(isa, real_quadrature, monkeypatch):
    """Across every runtime SIMD target, direct refine on odd 2*hw*R+1 windows, clipped windows,
    and truncated end-of-series blocks (have < n) matches the whole-block transform."""
    import os
    from matchedfilter import _prices

    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setattr(_prices, "_DIRECT_PAIR", {})
    mf.backend()
    mf.set_target(isa)
    try:
        if not real_quadrature:
            data = _bank(n=1024, T=16, nblocks=18, nsig=12, seed=31)
            n, taps, counts, spec, series, layout, ref, window = data
            starts, w0, w1 = layout
            # Truncate series so the final block has have < n (tests unpadded dx tail path too).
            series_cut = series[: int(starts[-1] + w1[-1] + int(counts.max()) // 2 - 5)]
            monkeypatch.setenv("MF_DIRECT_REFINE", "1")
            hf1 = mf.HierarchicalFilter(n, 1, T := spec.shape[0], snr=6.0, fd=1e-2,
                                        chain=(256, 512), search_window=window)
            hf1.set_reference(ref); hf1.set_templates(spec); hf1.set_taps(taps, counts)
            hf1._execution_plan().set_direct_prices(0.01, 1e9)
            i1, v1 = hf1.run_series(series_cut, starts, w0, w1, binsize=n, threshold=6.0, raw=True)
            i1, v1, st = i1.copy(), v1.copy(), hf1.direct_stats()
            thr = hf1._resolve().thresholds

            monkeypatch.setenv("MF_DIRECT_REFINE", "0")
            hf0 = mf.HierarchicalFilter(n, 1, T, snr=6.0, fd=1e-2, chain=(256, 512),
                                        search_window=window)
            hf0.set_reference(ref); hf0.set_templates(spec); hf0.set_coarse_threshold(thr)
            i0, v0 = hf0.run_series(series_cut, starts, w0, w1, binsize=n, threshold=6.0, raw=True)
            assert (i0 >= 0).sum() > 10
            assert st["pairs"] > 0, (isa, st)
            np.testing.assert_array_equal(i1, i0)
            m = i0 >= 0
            np.testing.assert_allclose(v1[m], v0[m], rtol=2e-5, atol=1e-4)
        else:
            from matchedfilter.benchmark import _inspiral_power
            rng = np.random.default_rng(37)
            n, T, nblocks, nsig = 1024, 16, 18, 10
            counts = (2 * rng.integers(45, 130, T) + 1).astype(np.int64)
            taps = np.zeros((T, int(counts.max())), np.complex64)
            for t in range(T):
                L = int(counts[t])
                w = np.zeros(L, np.complex128)
                w[L // 2] = np.exp(1j * (0.3 + 0.07 * t))
                w += 0.15 * np.hanning(L) * np.exp(1j * np.linspace(0, 3 + 0.1 * t, L)) / np.sqrt(L)
                taps[t, :L] = w.astype(np.complex64)
            filt, valid = template_spectra(taps, counts, n)
            spec = np.conj(filt)
            cbad, vend = int(valid[:, 0].max()), int(valid[:, 1].min())
            step = vend - cbad
            total = step * (nblocks - 1) + vend + 7  # truncated final block (have < n)
            tot_fft = 1 << int(np.ceil(np.log2(total + n)))
            p1 = _inspiral_power(tot_fft)
            p1[tot_fft // 2 :] = 0.0
            p1 /= p1.sum()
            W = np.fft.rfft(rng.standard_normal(tot_fft))
            S = np.zeros_like(W)
            m_bins = min(len(S), tot_fft // 2)
            S[:m_bins] = W[:m_bins] * np.sqrt(p1[:m_bins] * tot_fft)
            full = np.fft.irfft(S, n=tot_fft)
            full /= np.std(full)
            pulse = np.real(np.fft.ifft(p1) * tot_fft) * 2.0
            gap = (total - 2 * n) // max(nsig, 1)
            for i in range(nsig):
                full += rng.uniform(8.5, 11.0) * np.roll(pulse, cbad + 48 + i * gap)
            x = full[:total].astype(np.float32)
            starts = (np.arange(nblocks) * step).astype(np.int64)
            w0 = np.full(nblocks, cbad, np.int64)
            w1 = np.full(nblocks, vend, np.int64)
            q = n // 32
            win = ((cbad // q) * q, n - (cbad // q) * q)
            ref = _inspiral_power(n)
            ref[n // 2 :] = 0.0

            monkeypatch.setenv("MF_DIRECT_REFINE", "1")
            hf1 = mf.HierarchicalFilter(n, 1, T, snr=6.0, fd=1e-2, chain=(256, 512),
                                        search_window=win)
            hf1.set_reference(ref); hf1.set_templates(spec); hf1.set_taps(taps, counts)
            # Force cheap direct price so AVX1/SSE4 also exercise direct refine on real+complex taps
            hf1._execution_plan().set_direct_prices(0.01, 1e9)
            i1, v1 = hf1.run_series(x, starts, w0, w1, binsize=n, threshold=6.0, raw=True)
            i1, v1, st = i1.copy(), v1.copy(), hf1.direct_stats()
            thr = hf1._resolve().thresholds

            monkeypatch.setenv("MF_DIRECT_REFINE", "0")
            hf0 = mf.HierarchicalFilter(n, 1, T, snr=6.0, fd=1e-2, chain=(256, 512),
                                        search_window=win)
            hf0.set_reference(ref); hf0.set_templates(spec); hf0.set_coarse_threshold(thr)
            i0, v0 = hf0.run_series(x, starts, w0, w1, binsize=n, threshold=6.0, raw=True)

            assert (i0 >= 0).sum() > 8
            assert st["pairs"] > 0, (isa, st)
            np.testing.assert_array_equal(i1, i0)
            m = i0 >= 0
            np.testing.assert_allclose(v1[m], v0[m], rtol=2e-5, atol=1e-4)
    finally:
        mf.set_target(os.environ.get("MF_ISA") or None)


