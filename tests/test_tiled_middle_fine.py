"""Bit-exactness and zero-extra-FFT tests for L3-tiled CPU middle-to-fine execution."""

import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from matchedfilter.search import BlockInput, HierarchicalSearch, Inner, Leaf, Root


def _reference_profile(n_bins=16385, delta_f=1.0 / 16.0):
    f = np.arange(n_bins, dtype=np.float64) * delta_f
    w = np.where((f >= 24.0) & (f <= 850.0), np.maximum(f, 1.0) ** (-7.0 / 3.0), 0.0)
    return w


def _make_real_taps(rng, n_templates, counts):
    counts = np.asarray(counts, dtype=np.int64)
    width = int(counts.max())
    taps = np.zeros((n_templates, width), dtype=np.float32)
    for i in range(n_templates):
        c = int(counts[i])
        t = np.arange(c, dtype=np.float32) / 2048.0
        f0 = 35.0 + 9.0 * (i % 17)
        f1 = 180.0 + 14.0 * (i % 23)
        phase = 2.0 * np.pi * (f0 * t + 0.5 * (f1 - f0) * t * t)
        row = (np.cos(phase) * np.hanning(c)).astype(np.float32)
        row /= np.float32(np.linalg.norm(row))
        taps[i, :c] = row
    return taps, counts


def _make_quadrature_taps(rng, n_templates, counts):
    counts = np.asarray(counts, dtype=np.int64)
    width = int(counts.max())
    taps = np.zeros((n_templates, width), dtype=np.complex64)
    for i in range(n_templates):
        c = int(counts[i])
        t = np.arange(c, dtype=np.float32) / 2048.0
        f0 = 40.0 + 8.0 * (i % 13)
        f1 = 210.0 + 12.0 * (i % 19)
        phase = 2.0 * np.pi * (f0 * t + 0.5 * (f1 - f0) * t * t)
        env = np.hanning(c).astype(np.float32)
        row = (np.exp(1j * phase) * env).astype(np.complex64)
        row /= np.float32(np.linalg.norm(row))
        taps[i, :c] = row
    return taps, counts


def _pack_real_pairs(taps, counts):
    n = len(counts)
    npair = (n + 1) // 2
    pc = np.array([int(max(counts[2 * q:2 * q + 2])) for q in range(npair)], dtype=np.int64)
    out = np.zeros((npair, int(pc.max())), dtype=np.complex64)
    for r in range(n):
        q, lane = divmod(r, 2)
        c = int(counts[r])
        off = int(pc[q]) // 2 - c // 2
        out[q, off:off + c] += (1.0 if lane == 0 else -1j) * taps[r, :c]
    return out, pc


def _assert_bits_equal(a: np.ndarray, b: np.ndarray):
    assert a.dtype == b.dtype and a.shape == b.shape
    np.testing.assert_array_equal(a.view(np.uint8), b.view(np.uint8))


def _assert_results_bit_identical(res_a, res_b):
    assert len(res_a) == len(res_b)
    for a, b in zip(res_a, res_b):
        np.testing.assert_array_equal(a.template_indices, b.template_indices)
        np.testing.assert_array_equal(a.sample_indices, b.sample_indices)
        _assert_bits_equal(a.snr, b.snr)
        np.testing.assert_array_equal(a.block_starts, b.block_starts)
        np.testing.assert_array_equal(a.block_lengths, b.block_lengths)


@pytest.mark.parametrize("tile_bytes", [0, 32768, 131072, 4 << 20])
def test_complex_multigroup_middle_and_zero_extra_work(tile_bytes):
    """Multi-group middle bank (including non-contiguous template order) + multi-group fine
    banks match untiled execution bit-for-bit with identical middle/fine block and pair counts."""
    rng = np.random.default_rng(20261101)
    S = 131072
    a0, a1, pad = 16384, S - 16384, 4096

    # Interleave short (n=4096) and long (n=16384) middle templates so template_indices are non-contiguous.
    mid_counts = np.array([512, 3600, 640, 3900, 700, 3700], dtype=np.int64)
    mid_taps, mid_counts = _make_real_taps(rng, len(mid_counts), mid_counts)
    ref_w = _reference_profile()

    fine_specs = [
        _make_real_taps(rng, 24, rng.integers(180, 340, size=24)),
        _make_real_taps(rng, 28, np.concatenate([rng.integers(160, 260, size=14),
                                                 rng.integers(900, 1300, size=14)])),
        _make_real_taps(rng, 20, rng.integers(200, 320, size=20)),
        _make_real_taps(rng, 22, rng.integers(220, 380, size=22)),
        _make_real_taps(rng, 18, rng.integers(190, 310, size=18)),
        _make_real_taps(rng, 26, rng.integers(210, 360, size=26)),
    ]

    def _build_banks():
        mb = TimeDomainFilterBank(
            mid_taps, mid_counts, engine="corr", device="cpu",
            fft_lengths=(4096, 16384),
        )
        fbs = []
        for ft, fc in fine_specs:
            fb = TimeDomainFilterBank(
                ft, fc, engine="hier", device="cpu",
                threshold=4.2, false_dismissal=1e-3, binsize=2048,
                fft_lengths=(2048, 4096),
            )
            fb.set_reference(ref_w, delta_f=1.0 / 16.0)
            fbs.append(fb)
        return mb, fbs

    ser = ((rng.standard_normal(S) + 1j * rng.standard_normal(S))
           * np.float32(1.0 / np.sqrt(2.0))).astype(np.complex64)
    # Inject bright impulses near tile and 2048-sample bin boundaries so partial-bin merges trigger.
    for boundary_idx in (a0 + 2047, a0 + 2048, a0 + 16383, a0 + 16384, a0 + 32768, a1 - 2049):
        ser[boundary_idx - 64:boundary_idx + 64] += np.float32(12.0) * np.exp(
            1j * np.linspace(0.0, 20.0, 128, dtype=np.float32)
        )

    mid_ref, fine_ref = _build_banks()
    out_ref = np.full((len(mid_counts), S), np.nan + 1j * np.nan, dtype=np.complex64)
    mid_ref.correlate_series(ser, windows=slice(a0 - pad, a1 + pad), out=out_ref)
    ref_jobs = [(fb, out_ref[row], dict(windows=slice(a0, a1)))
                for row, fb in enumerate(fine_ref)]
    res_ref = TimeDomainFilterBank.filter_series_many(ref_jobs)

    mid_tiled, fine_tiled = _build_banks()
    out_tiled = np.full((len(mid_counts), S), -999.0 + 777.0j, dtype=np.complex64)
    corr_jobs = [(mid_tiled, ser, dict(windows=slice(a0 - pad, a1 + pad), out=out_tiled))]
    tiled_jobs = [(fb, out_tiled[row], dict(windows=slice(a0, a1)))
                  for row, fb in enumerate(fine_tiled)]
    timings = {}
    res_tiled = TimeDomainFilterBank.correlate_and_filter_many(
        corr_jobs, tiled_jobs, timings=timings, tile_bytes=tile_bytes)

    _assert_bits_equal(out_tiled, out_ref)
    _assert_results_bit_identical(res_tiled, res_ref)
    assert sum(len(r.snr) for r in res_tiled) > 10
    assert len(timings["correlate_per_job"]) == 1

    # Verify zero extra middle FFTs/blocks and identical fine pair evaluations.
    assert getattr(mid_tiled, "_corr_in_samples", 0) == getattr(mid_ref, "_corr_in_samples", 0)
    assert getattr(mid_tiled, "_corr_work", {}) == getattr(mid_ref, "_corr_work", {})
    for fb_t, fb_r in zip(fine_tiled, fine_ref):
        for g_t, g_r in zip(fb_t._groups, fb_r._groups):
            assert g_t.plan._execution_plan().stats()[0] == g_r.plan._execution_plan().stats()[0]


def test_quadrature_packed_lanes_interleaved_detectors_bit_identical():
    """Packed real-pair middle correlation feeding strided .real/.imag quadrature fine banks
    across two interleaved detectors matches untiled bit-for-bit."""
    rng = np.random.default_rng(9001)
    S = 131072
    a0, a1, pad = 12000, S - 12000, 4096
    ref_w = _reference_profile()

    n_mid = 7  # odd count tests unpaired final lane as well as paired lanes
    raw_mid_counts = np.sort(rng.integers(400, 2600, size=n_mid))
    raw_mid_taps, raw_mid_counts = _make_real_taps(rng, n_mid, raw_mid_counts)
    packed_taps, packed_counts = _pack_real_pairs(raw_mid_taps, raw_mid_counts)
    n_pairs = len(packed_counts)

    mid = TimeDomainFilterBank(
        packed_taps, packed_counts, engine="corr", device="cpu", fft_lengths=(8192,))
    fine_banks = []
    for _ in range(n_mid):
        ft, fc = _make_quadrature_taps(rng, 20, rng.integers(190, 310, size=20))
        fb = TimeDomainFilterBank(
            ft, fc, engine="hier", device="cpu",
            threshold=4.0, false_dismissal=1e-3, binsize=2048, fft_lengths=(2048,),
        )
        fb.set_reference(ref_w, delta_f=1.0 / 16.0)
        fine_banks.append(fb)

    ser = {
        "H1": rng.standard_normal(S).astype(np.float32),
        "L1": rng.standard_normal(S).astype(np.float32),
    }
    ser["H1"][40000:40256] += np.float32(9.0) * np.sin(np.linspace(0, 30, 256, dtype=np.float32))
    ser["L1"][75000:75256] += np.float32(9.5) * np.cos(np.linspace(0, 28, 256, dtype=np.float32))

    def _lane(arr, row):
        pair = arr[row // 2]
        return pair.real if row % 2 == 0 else pair.imag

    # Untiled reference
    out_ref = {
        ifo: np.ones((n_pairs, S), dtype=np.complex64) * (3.0 - 2.0j)
        for ifo in ser
    }
    for ifo in ser:
        mid.correlate_series(ser[ifo], windows=slice(a0 - pad, a1 + pad), out=out_ref[ifo])
    ref_jobs = [
        (fine_banks[row], _lane(out_ref[ifo], row), dict(windows=slice(a0, a1)))
        for row in range(n_mid) for ifo in ("H1", "L1")
    ]
    res_ref = TimeDomainFilterBank.filter_series_many(ref_jobs)

    # Tiled with tight tile_bytes so multiple tiles execute per detector
    out_tiled = {
        ifo: np.ones((n_pairs, S), dtype=np.complex64) * (-5.0 + 4.0j)
        for ifo in ser
    }
    corr_jobs = [
        (mid, ser[ifo], dict(windows=slice(a0 - pad, a1 + pad), out=out_tiled[ifo]))
        for ifo in ("H1", "L1")
    ]
    tiled_jobs = [
        (fine_banks[row], _lane(out_tiled[ifo], row), dict(windows=slice(a0, a1)))
        for row in range(n_mid) for ifo in ("H1", "L1")
    ]
    t_info = {}
    res_tiled = TimeDomainFilterBank.correlate_and_filter_many(
        corr_jobs, tiled_jobs, timings=t_info, tile_bytes=65536)

    for ifo in ("H1", "L1"):
        _assert_bits_equal(out_tiled[ifo], out_ref[ifo])
    _assert_results_bit_identical(res_tiled, res_ref)
    assert len(t_info["correlate_per_job"]) == 2
    assert sum(len(r.snr) for r in res_tiled) > 5


@pytest.mark.parametrize("binsize", [None, 1, 777, 2048])
def test_multi_window_bridged_gaps_scales_templates_and_support(binsize):
    """Disjoint windows (including gaps bridged by middle blocks and reordered SeriesLayout
    blocks), selected middle templates, scales, and out_support match untiled bit-for-bit."""
    rng = np.random.default_rng(424242)
    S = 98304
    ref_w = _reference_profile()

    mid_counts = np.array([600, 1800, 900, 2100, 1200], dtype=np.int64)
    mid_taps, mid_counts = _make_real_taps(rng, len(mid_counts), mid_counts)
    mid = TimeDomainFilterBank(
        mid_taps, mid_counts, engine="corr", device="cpu", fft_lengths=(8192,))

    sel = [0, 2, 3, 4]
    scales = np.array([1.25, -0.75, -1.5, 0.875, 2.125], dtype=np.float32)

    fine_banks = []
    for _ in range(len(sel)):
        ft, fc = _make_real_taps(rng, 16, rng.integers(180, 320, size=16))
        fb = TimeDomainFilterBank(
            ft, fc, engine="hier", device="cpu",
            threshold=3.8, false_dismissal=1e-3, binsize=binsize, fft_lengths=(2048,),
        )
        fb.set_reference(ref_w, delta_f=1.0 / 16.0)
        fine_banks.append(fb)

    ser = ((rng.standard_normal(S) + 1j * rng.standard_normal(S))
           * np.float32(1.0 / np.sqrt(2.0))).astype(np.complex64)
    # Three disjoint leaf windows: first two have a narrow gap bridged by an 8192 middle block.
    leaf_wins = [(10123, 19500), (21000, 34000), (62000, 81000)]
    corr_wins = [(8000, 20200), (20600, 36500), (59500, 84000)]
    prev_support = [(2000, 50000), (85000, 95000)]

    for pos in (14000, 27000, 70000):
        ser[pos:pos + 128] += np.float32(10.0) * np.exp(
            1j * np.linspace(0.0, 18.0, 128, dtype=np.float32)
        )

    def _init_dirty_buffer():
        buf = np.zeros((len(sel), S), dtype=np.complex64)
        for a, b in prev_support:
            buf[:, a:b] = 17.0 - 23.0j
        return buf

    out_ref = _init_dirty_buffer()
    mid.correlate_series(
        ser, windows=corr_wins, scales=scales, templates=sel,
        out=out_ref, out_support=prev_support,
    )
    ref_jobs = [
        (fine_banks[k], out_ref[k], dict(windows=[] if k == 1 else leaf_wins, binsize=binsize))
        for k in range(len(sel))
    ]
    res_ref = TimeDomainFilterBank.filter_series_many(ref_jobs)

    out_tiled = _init_dirty_buffer()
    corr_jobs = [(mid, ser, dict(
        windows=corr_wins, scales=scales, templates=sel,
        out=out_tiled, out_support=prev_support,
    ))]
    tiled_jobs = [
        (fine_banks[k], out_tiled[k], dict(windows=[] if k == 1 else leaf_wins, binsize=binsize))
        for k in range(len(sel))
    ]
    res_tiled = TimeDomainFilterBank.correlate_and_filter_many(
        corr_jobs, tiled_jobs, tile_bytes=49152)

    _assert_bits_equal(out_tiled, out_ref)
    _assert_results_bit_identical(res_tiled, res_ref)
    assert len(res_tiled[1].snr) == 0


def test_hierarchical_search_cpu_tiled_vs_untiled_parity(monkeypatch):
    """End-to-end HierarchicalSearch on CPU with tiled inner->leaf execution matches untiled
    (_TILE_BYTES = 0) bit-for-bit across peaks, envelopes, ctx.series, and ctx.refilter."""
    rng = np.random.default_rng(777)
    n_samples = 131072
    n_bins = n_samples // 2 + 1
    ref_w = _reference_profile(n_bins=16385, delta_f=1.0 / 16.0)

    root_spec = np.zeros(n_bins, dtype=np.complex64)
    root_spec[64:20000] = (rng.standard_normal(19936) + 1j * rng.standard_normal(19936)).astype(
        np.complex64)
    root_spec /= np.float32(np.linalg.norm(root_spec))

    inner_nodes = []
    for i in range(4):
        itaps, icounts = _make_real_taps(rng, 1, [701 + 200 * i])
        ftaps, fcounts = _make_quadrature_taps(rng, 12, rng.integers(180, 300, size=12))
        lags = rng.integers(-20, 20, size=12)
        leaf = Leaf(ftaps, fcounts, lags=lags, node_id=("leaf", i))
        inner_nodes.append(Inner(itaps[0], int(icounts[0]), children=[leaf], node_id=("inner", i)))

    root = Root(root_spec, band=(64, 20000), children=inner_nodes,
                profile=(ref_w, 1.0 / 16.0), node_id="root0")

    spectra_h = []
    spectra_l = []
    for chunk_idx in range(2):
        sh = (rng.standard_normal(n_bins) + 1j * rng.standard_normal(n_bins)).astype(np.complex64)
        sl = (rng.standard_normal(n_bins) + 1j * rng.standard_normal(n_bins)).astype(np.complex64)
        spectra_h.append(sh)
        spectra_l.append(sl)

    inputs = {
        "H1": BlockInput(spectra_h, [(12288, n_samples - 12288), (24576, 65536)],
                         root_scale=lambda r, k: 25.0),
        "L1": BlockInput(spectra_l, [(12288, n_samples - 12288), (24576, 65536)],
                         root_scale=lambda r, k: 25.0),
    }

    def windows_fn(leaf, chunk, ch, extra):
        if chunk == 0:
            return None
        if leaf.node_id == ("leaf", 0) and ch == "L1":
            return []
        return [(28000 - extra, 52000 + extra)]

    def on_series_fn(ctx):
        return {
            ch: (lambda t: 1.0 + 0.15 * np.sin(t.astype(np.float64) * 1e-4) ** 2)
            for ch in ctx.channels
        }

    def _run_with_tile_bytes(tb):
        monkeypatch.setattr(TimeDomainFilterBank, "_TILE_BYTES", tb)
        records = {}
        search = HierarchicalSearch(
            [root], threshold=3.6, envelope_floor=1.0, context=256, min_pad=2048,
            leaf_options=dict(
                engine="hier", device="cpu", binsize=2048,
                false_dismissal=1e-3, fft_lengths=(2048,),
            ),
        )

        def on_peaks_fn(ctx):
            for ch in ctx.channels:
                ser = ctx.series(ch)
                sup = ctx.support(ch)
                refilt = (ctx.refilter(ch, windows=slice(sup[0][0] + 512, sup[0][0] + 1536),
                                       binsize=256, threshold=2.5, template_index=0)
                          if sup and sup[0][1] - sup[0][0] >= 2048 else None)
                records[(ctx.leaf.node_id, ctx.chunk, ch)] = (
                    ctx.peaks[ch],
                    ctx.envelope(ch),
                    ser.copy(),
                    sup,
                    refilt,
                )

        search.run(inputs, windows=windows_fn, on_series=on_series_fn, on_peaks=on_peaks_fn)
        return records

    untiled = _run_with_tile_bytes(0)
    tiled = _run_with_tile_bytes(65536)

    assert untiled.keys() == tiled.keys()
    total_peaks = 0
    for key in untiled:
        pk_u, env_u, ser_u, sup_u, rf_u = untiled[key]
        pk_t, env_t, ser_t, sup_t, rf_t = tiled[key]
        assert sup_u == sup_t
        _assert_bits_equal(ser_t, ser_u)
        _assert_results_bit_identical([pk_t], [pk_u])
        total_peaks += len(pk_t.snr)
        if env_u is None:
            assert env_t is None
        else:
            np.testing.assert_array_equal(env_t, env_u)
        if rf_u is None:
            assert rf_t is None
        else:
            _assert_results_bit_identical([rf_t], [rf_u])
    assert total_peaks > 5


@pytest.mark.parametrize("tile_bytes", [32768, 131072, 4 << 20])
def test_ephemeral_and_retain_radius_collar_followup(tile_bytes):
    """Ephemeral mode (retain_radius=0) leaves out untouched, and sparse collar retention
    (retain_radius > 0) matches untiled cross-detector follow-up refiltering bit-for-bit."""
    rng = np.random.default_rng(314159)
    S = 131072
    a0, a1, pad = 12288, S - 12288, 4096
    half = 2252
    asym_thr = 4.5
    ref_w = _reference_profile()

    n_mid = 6
    raw_counts = np.sort(rng.integers(500, 2400, size=n_mid))
    raw_taps, raw_counts = _make_real_taps(rng, n_mid, raw_counts)
    packed_taps, packed_counts = _pack_real_pairs(raw_taps, raw_counts)
    n_pairs = len(packed_counts)

    mid = TimeDomainFilterBank(
        packed_taps, packed_counts, engine="corr", device="cpu", fft_lengths=(8192,))
    fine_banks = []
    for _ in range(n_mid):
        ft, fc = _make_quadrature_taps(rng, 18, rng.integers(180, 320, size=18))
        fb = TimeDomainFilterBank(
            ft, fc, engine="hier", device="cpu",
            threshold=3.9, false_dismissal=1e-3, binsize=2048, fft_lengths=(2048,),
        )
        fb.set_reference(ref_w, delta_f=1.0 / 16.0)
        fine_banks.append(fb)
    max_fine_block = max(int(fb.max_block_length) for fb in fine_banks)

    ser = {
        "H1": rng.standard_normal(S).astype(np.float32),
        "L1": rng.standard_normal(S).astype(np.float32),
    }
    # Place impulses near chunk boundaries and interior so cross-chunk collars are exercised.
    for pos in (a0 + 512, a0 + 32700, a0 + 65500, a1 - 700):
        ser["H1"][pos - 64:pos + 64] += np.float32(9.5) * np.sin(
            np.linspace(0, 26, 128, dtype=np.float32))
    for pos in (a0 + 16300, a0 + 49100, a1 - 1500):
        ser["L1"][pos - 64:pos + 64] += np.float32(9.5) * np.cos(
            np.linspace(0, 24, 128, dtype=np.float32))

    def _lane(arr, row):
        pair = arr[row // 2]
        return pair.real if row % 2 == 0 else pair.imag

    # Untiled reference
    out_ref = {ifo: np.zeros((n_pairs, S), dtype=np.complex64) for ifo in ("H1", "L1")}
    for ifo in ("H1", "L1"):
        mid.correlate_series(ser[ifo], windows=slice(a0 - pad, a1 + pad), out=out_ref[ifo])
    ref_jobs = [
        (fine_banks[row], _lane(out_ref[ifo], row), dict(windows=slice(a0, a1)))
        for row in range(n_mid) for ifo in ("H1", "L1")
    ]
    res_ref = TimeDomainFilterBank.filter_series_many(ref_jobs)

    # 1. Ephemeral mode (retain_radius=0): zero DRAM writes to out_ephem
    sentinel = np.complex64(-123.0 + 456.0j)
    out_ephem = {
        ifo: np.full((n_pairs, S), sentinel, dtype=np.complex64) for ifo in ("H1", "L1")
    }
    ephem_corr = [
        (mid, ser[ifo], dict(windows=slice(a0 - pad, a1 + pad), out=out_ephem[ifo]))
        for ifo in ("H1", "L1")
    ]
    ephem_jobs = [
        (fine_banks[row], _lane(out_ephem[ifo], row), dict(windows=slice(a0, a1)))
        for row in range(n_mid) for ifo in ("H1", "L1")
    ]
    t_ephem = {}
    res_ephem = TimeDomainFilterBank.correlate_and_filter_many(
        ephem_corr, ephem_jobs, timings=t_ephem, tile_bytes=tile_bytes, retain_radius=0,
    )
    assert t_ephem["ephemeral_used"] is True
    _assert_results_bit_identical(res_ephem, res_ref)
    for ifo in ("H1", "L1"):
        assert np.all(out_ephem[ifo] == sentinel)

    # 2. Sparse collar retention (retain_radius = half + max_fine_block)
    out_col = {ifo: np.zeros((n_pairs, S), dtype=np.complex64) for ifo in ("H1", "L1")}
    # Dirty margins outside mid_win to verify edge clearing still runs on first call.
    for ifo in ("H1", "L1"):
        out_col[ifo][:, :a0 - pad] = 99.0 - 88.0j
        out_col[ifo][:, a1 + pad:] = -77.0 + 66.0j
    col_corr = [
        (mid, ser[ifo], dict(windows=slice(a0 - pad, a1 + pad), out=out_col[ifo]))
        for ifo in ("H1", "L1")
    ]
    col_jobs = [
        (fine_banks[row], _lane(out_col[ifo], row), dict(windows=slice(a0, a1)))
        for row in range(n_mid) for ifo in ("H1", "L1")
    ]
    t_col = {}
    res_col = TimeDomainFilterBank.correlate_and_filter_many(
        col_corr, col_jobs, timings=t_col, tile_bytes=tile_bytes,
        retain_radius=half + max_fine_block, retain_threshold=asym_thr,
    )
    assert t_col["ephemeral_used"] is False
    _assert_results_bit_identical(res_col, res_ref)

    # Run cross-detector single-template follow-ups around every trigger >= asym_thr.
    asym_ref_jobs, asym_col_jobs = [], []
    it = iter(res_col)
    for row, fb in enumerate(fine_banks):
        trig = {"H1": next(it), "L1": next(it)}
        for ifo, other in (("H1", "L1"), ("L1", "H1")):
            r = trig[ifo]
            keep = np.flatnonzero(np.abs(r.snr) >= asym_thr)
            for idx_k in keep:
                c0 = int(r.sample_indices[idx_k])
                ti = int(r.template_indices[idx_k])
                kw = dict(
                    windows=slice(max(0, c0 - half), min(S, c0 + half)),
                    binsize=256, threshold=0.0, template_index=ti,
                )
                asym_ref_jobs.append((fb, _lane(out_ref[other], row), kw))
                asym_col_jobs.append((fb, _lane(out_col[other], row), kw))

    assert len(asym_col_jobs) >= 4
    asym_ref_out = TimeDomainFilterBank.filter_series_many(asym_ref_jobs)
    asym_col_out = TimeDomainFilterBank.filter_series_many(asym_col_jobs)
    _assert_results_bit_identical(asym_col_out, asym_ref_out)


def test_repeated_inplace_mutation_never_reuses_stale_forward_spectra():
    """Mutating input series buffers in place at the same memory address across segments
    always computes fresh forward FFTs without extra blocks."""
    rng = np.random.default_rng(271828)
    S = 65536
    a0, a1, pad = 8192, S - 8192, 2048
    ref_w = _reference_profile()

    # Mix n=4096 (small FFT) and n=16384 (balanced FFT) groups on the same bank.
    mid_counts = np.array([400, 3500, 520, 3700], dtype=np.int64)
    raw_taps, mid_counts = _make_real_taps(rng, len(mid_counts), mid_counts)
    packed_taps, packed_counts = _pack_real_pairs(raw_taps, mid_counts)
    mid_tiled = TimeDomainFilterBank(
        packed_taps, packed_counts, engine="corr", device="cpu", fft_lengths=(4096, 16384))
    mid_ref = TimeDomainFilterBank(
        packed_taps, packed_counts, engine="corr", device="cpu", fft_lengths=(4096, 16384))

    fine_banks = []
    for _ in range(len(mid_counts)):
        ft, fc = _make_quadrature_taps(rng, 14, rng.integers(180, 280, size=14))
        fb = TimeDomainFilterBank(
            ft, fc, engine="hier", device="cpu",
            threshold=3.8, false_dismissal=1e-3, binsize=1024, fft_lengths=(2048,),
        )
        fb.set_reference(ref_w, delta_f=1.0 / 16.0)
        fine_banks.append(fb)

    ser_buf = {
        "H1": np.zeros(S, dtype=np.float32),
        "L1": np.zeros(S, dtype=np.float32),
    }
    addr_h1 = ser_buf["H1"].ctypes.data
    addr_l1 = ser_buf["L1"].ctypes.data
    out_tiled = {ifo: np.zeros((len(packed_counts), S), dtype=np.complex64) for ifo in ("H1", "L1")}
    out_ref = {ifo: np.zeros((len(packed_counts), S), dtype=np.complex64) for ifo in ("H1", "L1")}

    def _lane(arr, row):
        pair = arr[row // 2]
        return pair.real if row % 2 == 0 else pair.imag

    for seg in range(3):
        if seg < 2:
            ser_buf["H1"][:] = rng.standard_normal(S).astype(np.float32)
            ser_buf["L1"][:] = rng.standard_normal(S).astype(np.float32)
        else:
            # Mutate ONLY interior samples while keeping endpoints [0] and [-1] identical!
            ser_buf["H1"][16000:48000] = rng.standard_normal(32000).astype(np.float32) * 2.5
            ser_buf["L1"][20000:50000] = rng.standard_normal(30000).astype(np.float32) * 2.5
        assert ser_buf["H1"].ctypes.data == addr_h1
        assert ser_buf["L1"].ctypes.data == addr_l1

        for ifo in ("H1", "L1"):
            mid_ref.correlate_series(
                ser_buf[ifo], windows=slice(a0 - pad, a1 + pad),
                out=out_ref[ifo], out_support=slice(a0 - pad, a1 + pad) if seg > 0 else None,
            )
        ref_jobs = [
            (fine_banks[row], _lane(out_ref[ifo], row), dict(windows=slice(a0, a1)))
            for row in range(len(mid_counts)) for ifo in ("H1", "L1")
        ]
        res_ref = TimeDomainFilterBank.filter_series_many(ref_jobs)

        corr_jobs = [
            (mid_tiled, ser_buf[ifo], dict(
                windows=slice(a0 - pad, a1 + pad), out=out_tiled[ifo],
                out_support=slice(a0 - pad, a1 + pad) if seg > 0 else None,
            ))
            for ifo in ("H1", "L1")
        ]
        tiled_jobs = [
            (fine_banks[row], _lane(out_tiled[ifo], row), dict(windows=slice(a0, a1)))
            for row in range(len(mid_counts)) for ifo in ("H1", "L1")
        ]
        res_tiled = TimeDomainFilterBank.correlate_and_filter_many(
            corr_jobs, tiled_jobs, tile_bytes=65536)

        for ifo in ("H1", "L1"):
            _assert_bits_equal(out_tiled[ifo], out_ref[ifo])
        _assert_results_bit_identical(res_tiled, res_ref)

    assert getattr(mid_tiled, "_corr_work", {}) == getattr(mid_ref, "_corr_work", {})


def test_hierarchical_search_ephemeral_and_hook_alternation(monkeypatch):
    """Alternating on_peaks=None (ephemeral zero-DRAM-write) and on_peaks=hook on the same
    HierarchicalSearch preserves exact slot support clearing and bit-exact series/peaks."""
    rng = np.random.default_rng(2026)
    n_samples = 65536
    n_bins = n_samples // 2 + 1
    ref_w = _reference_profile(n_bins=16385, delta_f=1.0 / 16.0)

    root_spec = np.zeros(n_bins, dtype=np.complex64)
    root_spec[64:12000] = (rng.standard_normal(11936) + 1j * rng.standard_normal(11936)).astype(
        np.complex64)
    root_spec /= np.float32(np.linalg.norm(root_spec))

    inner_nodes = []
    for i in range(3):
        itaps, icounts = _make_real_taps(rng, 1, [601 + 180 * i])
        ftaps, fcounts = _make_quadrature_taps(rng, 10, rng.integers(180, 260, size=10))
        leaf = Leaf(ftaps, fcounts, node_id=("leaf", i))
        inner_nodes.append(Inner(itaps[0], int(icounts[0]), children=[leaf], node_id=("inner", i)))

    root = Root(root_spec, band=(64, 12000), children=inner_nodes,
                profile=(ref_w, 1.0 / 16.0), node_id="root_alt")

    sh = (rng.standard_normal(n_bins) + 1j * rng.standard_normal(n_bins)).astype(np.complex64)
    sl = (rng.standard_normal(n_bins) + 1j * rng.standard_normal(n_bins)).astype(np.complex64)
    inputs = {
        "H1": BlockInput([sh], [(8192, n_samples - 8192)], root_scale=lambda r, k: 22.0),
        "L1": BlockInput([sl], [(8192, n_samples - 8192)], root_scale=lambda r, k: 22.0),
    }

    def _run_sequence(tb):
        monkeypatch.setattr(TimeDomainFilterBank, "_TILE_BYTES", tb)
        s = HierarchicalSearch(
            [root], threshold=3.6, leaf_options=dict(
                engine="hier", device="cpu", binsize=1024,
                false_dismissal=1e-3, fft_lengths=(2048,),
            ),
        )
        # Step 1: ephemeral run (on_peaks=None) over wide window
        s.run(inputs, windows=lambda lf, k, ch, ex: [(10000 - ex, 54000 + ex)], on_peaks=None)
        if tb > 0:
            batch = s._inner[id(root)]
            for ch in ("H1", "L1"):
                assert np.all(batch._chan[ch]["slots"] == 0)

        # Step 2: materialized run (on_peaks=hook) over wide window [12000, 52000)
        rec1 = {}
        s.run(
            inputs,
            windows=lambda lf, k, ch, ex: [(12000 - ex, 52000 + ex)],
            on_peaks=lambda ctx: rec1.update({
                (ctx.leaf.node_id, ch): (ctx.peaks[ch], ctx.series(ch).copy(), ctx.support(ch))
                for ch in ctx.channels
            }),
        )

        # Step 3: ephemeral run (on_peaks=None) over medium window [18000, 46000)
        s.run(inputs, windows=lambda lf, k, ch, ex: [(18000 - ex, 46000 + ex)], on_peaks=None)

        # Step 4: materialized run (on_peaks=hook) over narrow window [24000, 38000):
        # must still clear stale regions written in Step 2 ([12000, 24000) and [38000, 52000))!
        rec2 = {}
        s.run(
            inputs,
            windows=lambda lf, k, ch, ex: [(24000 - ex, 38000 + ex)],
            on_peaks=lambda ctx: rec2.update({
                (ctx.leaf.node_id, ch): (ctx.peaks[ch], ctx.series(ch).copy(), ctx.support(ch))
                for ch in ctx.channels
            }),
        )
        return rec1, rec2

    u1, u2 = _run_sequence(0)
    t1, t2 = _run_sequence(65536)

    for u_rec, t_rec in ((u1, t1), (u2, t2)):
        assert u_rec.keys() == t_rec.keys()
        for key in u_rec:
            pk_u, ser_u, sup_u = u_rec[key]
            pk_t, ser_t, sup_t = t_rec[key]
            assert sup_u == sup_t
            _assert_bits_equal(ser_t, ser_u)
            _assert_results_bit_identical([pk_t], [pk_u])


def test_multi_batch_small_fft_and_permuted_templates():
    """Groups with n=4096 (>8 templates -> multiple kr<=8 batches) and n=8192 (>4 templates
    -> multiple kr<=4 batches), including permuted template selection and cross-chunk collar
    pools, match untiled bit-for-bit."""
    rng = np.random.default_rng(8675309)
    S = 98304
    a0, a1, pad = 10240, S - 10240, 2048
    ref_w = _reference_profile()

    # 11 short templates (n=4096 -> batches of 8 + 2) and 6 medium templates (n=8192 -> batches of 2 + 3).
    mid_counts = np.concatenate([
        np.sort(rng.integers(320, 620, size=11)),
        np.sort(rng.integers(1400, 2200, size=6)),
    ]).astype(np.int64)
    mid_taps, mid_counts = _make_real_taps(rng, len(mid_counts), mid_counts)
    mid_ref = TimeDomainFilterBank(
        mid_taps, mid_counts, engine="corr", device="cpu", fft_lengths=(4096, 8192))
    mid_tiled = TimeDomainFilterBank(
        mid_taps, mid_counts, engine="corr", device="cpu", fft_lengths=(4096, 8192))

    # Permuted subset that still contains contiguous runs > 1 in both groups.
    sel = [14, 15, 16, 11, 12, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    scales = rng.uniform(-2.0, 2.0, size=len(mid_counts)).astype(np.float32)

    fine_banks = []
    for _ in range(len(sel)):
        ft, fc = _make_real_taps(rng, 10, rng.integers(180, 280, size=10))
        fb = TimeDomainFilterBank(
            ft, fc, engine="hier", device="cpu",
            threshold=3.8, false_dismissal=1e-3, binsize=1024, fft_lengths=(2048,),
        )
        fb.set_reference(ref_w, delta_f=1.0 / 16.0)
        fine_banks.append(fb)

    ser = {
        ifo: ((rng.standard_normal(S) + 1j * rng.standard_normal(S))
              * np.float32(1.0 / np.sqrt(2.0))).astype(np.complex64)
        for ifo in ("H1", "L1")
    }
    for ifo in ("H1", "L1"):
        for pos in (a0 + 16000, a0 + 38000, a0 + 60000):
            ser[ifo][pos:pos + 96] += np.float32(10.5) * np.exp(
                1j * np.linspace(0, 16, 96, dtype=np.float32))

    out_ref = {ifo: np.full((len(sel), S), -3.0 + 5.0j, dtype=np.complex64) for ifo in ("H1", "L1")}
    for ifo in ("H1", "L1"):
        mid_ref.correlate_series(
            ser[ifo], windows=slice(a0 - pad, a1 + pad),
            templates=sel, scales=scales, out=out_ref[ifo],
        )
    ref_jobs = [
        (fine_banks[r], out_ref[ifo][r], dict(windows=slice(a0, a1)))
        for r in range(len(sel)) for ifo in ("H1", "L1")
    ]
    res_ref = TimeDomainFilterBank.filter_series_many(ref_jobs)

    out_tiled = {ifo: np.full((len(sel), S), 7.0 - 9.0j, dtype=np.complex64) for ifo in ("H1", "L1")}
    corr_jobs = [
        (mid_tiled, ser[ifo], dict(
            windows=slice(a0 - pad, a1 + pad),
            templates=sel, scales=scales, out=out_tiled[ifo],
        ))
        for ifo in ("H1", "L1")
    ]
    tiled_jobs = [
        (fine_banks[r], out_tiled[ifo][r], dict(windows=slice(a0, a1)))
        for r in range(len(sel)) for ifo in ("H1", "L1")
    ]
    res_tiled = TimeDomainFilterBank.correlate_and_filter_many(
        corr_jobs, tiled_jobs, tile_bytes=131072)

    for ifo in ("H1", "L1"):
        _assert_bits_equal(out_tiled[ifo], out_ref[ifo])
    _assert_results_bit_identical(res_tiled, res_ref)
    assert mid_tiled._corr_work.keys() == mid_ref._corr_work.keys()
    for n_blk in mid_tiled._corr_work:
        wt = mid_tiled._corr_work[n_blk]
        wr = mid_ref._corr_work[n_blk]
        assert wt["blocks"] <= wr["blocks"]
        assert wt["pairs"] == wr["pairs"]
        assert wt["out_samples"] == wr["out_samples"]
        assert wt["tmpl_values"] == wr["tmpl_values"]


def test_auto_tile_bytes_selects_tiled_or_untiled_by_cohort_footprint():
    """With tile_bytes=None, compact L3-resident cohorts execute ephemerally in L3 tiles
    while oversized full-segment cohorts fall back to untiled streaming bit-identically."""
    rng = np.random.default_rng(20261102)
    S = 262144
    pad = 2048
    ref_w = _reference_profile()

    mid_counts = np.sort(rng.integers(500, 2200, size=12))
    mid_taps, mid_counts = _make_real_taps(rng, len(mid_counts), mid_counts)
    mid = TimeDomainFilterBank(
        mid_taps, mid_counts, engine="corr", device="cpu", fft_lengths=(8192,))

    fine_banks = []
    for _ in range(len(mid_counts)):
        ft, fc = _make_real_taps(rng, 10, rng.integers(180, 280, size=10))
        fb = TimeDomainFilterBank(
            ft, fc, engine="hier", device="cpu",
            threshold=3.9, false_dismissal=1e-3, binsize=1024, fft_lengths=(2048,),
        )
        fb.set_reference(ref_w, delta_f=1.0 / 16.0)
        fine_banks.append(fb)

    ser = {
        ifo: ((rng.standard_normal(S) + 1j * rng.standard_normal(S))
              * np.float32(1.0 / np.sqrt(2.0))).astype(np.complex64)
        for ifo in ("H1", "L1")
    }
    ser["H1"][40000:40128] += np.float32(10.0) * np.exp(1j * np.linspace(0, 15, 128, dtype=np.float32))
    ser["L1"][180000:180128] += np.float32(10.0) * np.exp(1j * np.linspace(0, 14, 128, dtype=np.float32))

    # 1. Sparse window (D=2, 12 rows, 16384 samples -> 3.1 MiB <= 4 MiB): runs L3-tiled ephemerally.
    sparse_mid_w = slice(32768 - pad, 45056 + pad)
    sparse_leaf_w = slice(32768, 45056)
    sentinel = np.complex64(-42.0 + 19.0j)
    out_sparse = {ifo: np.full((len(mid_counts), S), sentinel, dtype=np.complex64) for ifo in ("H1", "L1")}
    t_sparse = {}
    res_sparse = TimeDomainFilterBank.correlate_and_filter_many(
        [(mid, ser[ifo], dict(windows=sparse_mid_w, out=out_sparse[ifo])) for ifo in ("H1", "L1")],
        [(fine_banks[r], out_sparse[ifo][r], dict(windows=sparse_leaf_w))
         for r in range(len(mid_counts)) for ifo in ("H1", "L1")],
        timings=t_sparse, retain_radius=0,
    )
    assert t_sparse["ephemeral_used"] is True
    for ifo in ("H1", "L1"):
        assert np.all(out_sparse[ifo] == sentinel)
    assert sum(len(r.snr) for r in res_sparse) > 0

    # 2. Full segment (D=2, 12 rows, ~245k samples -> 47 MiB > 4 MiB): auto-routes to untiled streaming.
    full_mid_w = slice(8192 - pad, S - 8192 + pad)
    full_leaf_w = slice(8192, S - 8192)
    out_auto = {ifo: np.zeros((len(mid_counts), S), dtype=np.complex64) for ifo in ("H1", "L1")}
    t_auto = {}
    res_auto = TimeDomainFilterBank.correlate_and_filter_many(
        [(mid, ser[ifo], dict(windows=full_mid_w, out=out_auto[ifo])) for ifo in ("H1", "L1")],
        [(fine_banks[r], out_auto[ifo][r], dict(windows=full_leaf_w))
         for r in range(len(mid_counts)) for ifo in ("H1", "L1")],
        timings=t_auto, retain_radius=0,
    )
    assert t_auto["ephemeral_used"] is False

    out_forced = {ifo: np.zeros((len(mid_counts), S), dtype=np.complex64) for ifo in ("H1", "L1")}
    res_forced = TimeDomainFilterBank.correlate_and_filter_many(
        [(mid, ser[ifo], dict(windows=full_mid_w, out=out_forced[ifo])) for ifo in ("H1", "L1")],
        [(fine_banks[r], out_forced[ifo][r], dict(windows=full_leaf_w))
         for r in range(len(mid_counts)) for ifo in ("H1", "L1")],
        tile_bytes=1 << 20,
    )
    for ifo in ("H1", "L1"):
        _assert_bits_equal(out_auto[ifo], out_forced[ifo])
    _assert_results_bit_identical(res_auto, res_forced)



