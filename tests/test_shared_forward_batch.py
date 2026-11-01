"""Tests for batched sparse CPU hierarchical series execution, L2-windowed strided lane
clustering, shared forward-FFT reuse, and counts-free sparse peak collection."""
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core


@pytest.fixture(params=mf.targets())
def target(request):
    mf.backend()
    mf.set_target(request.param)
    yield request.param
    mf.set_target(None)


def _assert_results_identical(got, want):
    """Assert bit-for-bit equality of two FilterResults instances."""
    np.testing.assert_array_equal(got.template_indices, want.template_indices)
    np.testing.assert_array_equal(got.sample_indices, want.sample_indices)
    np.testing.assert_array_equal(got.snr, want.snr)
    np.testing.assert_array_equal(got.block_starts, want.block_starts)
    np.testing.assert_array_equal(got.block_lengths, want.block_lengths)


def _make_bank(rng, n_templates, tap_counts, complex_taps=False, fft_lengths=(2048,),
               binsize=128, threshold=4.5, max_batch_size=None, pack_templates=False):
    max_len = int(np.max(tap_counts))
    dtype = np.complex64 if complex_taps else np.float32
    taps = np.zeros((n_templates, max_len), dtype=dtype)
    for i, c in enumerate(tap_counts):
        c_int = int(c)
        t = np.arange(c_int, dtype=np.float64) / 2048.0
        f0 = 35.0 + 6.0 * (i % 15) + rng.uniform(-2.0, 2.0)
        f1 = 160.0 + 10.0 * (i % 12)
        dur = max(t[-1], 1.0 / 2048.0)
        phase = 2.0 * np.pi * (f0 * t + 0.5 * (f1 - f0) * (t ** 2) / dur)
        win = np.hanning(c_int)
        if complex_taps:
            wave = (np.exp(1j * phase) * win).astype(np.complex64)
            norm = np.linalg.norm(wave)
            if norm > 0:
                wave /= norm / np.sqrt(2.0)
        else:
            wave = (np.sin(phase) * win).astype(np.float32)
            norm = np.linalg.norm(wave)
            if norm > 0:
                wave /= norm
        taps[i, :c_int] = wave
    bank = mf.TimeDomainFilterBank(
        taps,
        tap_counts=tap_counts,
        engine="hier",
        threshold=threshold,
        false_dismissal=1e-3,
        device="cpu",
        binsize=binsize,
        fft_lengths=fft_lengths,
        max_batch_size=max_batch_size,
        pack_templates=pack_templates,
    )
    ref = {}
    for n in set(bank.block_lengths):
        n_int = int(n)
        p = np.zeros(n_int, dtype=np.float32)
        k = np.arange(1, n_int // 2, dtype=np.float64)
        p[1:n_int // 2] = (k ** (-7.0 / 3.0) / ((0.015 * n_int / k) ** 4 + 1.0)).astype(np.float32)
        p /= p.sum()
        ref[n_int] = p
    bank.set_reference(ref)
    return bank, taps


def _reference_via_plan(bank, series, kwargs):
    """Reference FilterResults bypassing TimeDomainFilterBank._cpu_sparse_batch."""
    bank._defer = -1
    try:
        res = bank.filter_series(series, **(kwargs or {}))
    finally:
        bank._defer = 0
    return res.result() if hasattr(res, "result") else res


def test_strided_quadrature_lanes_interleaved_detectors(target):
    """Interleaved H1/L1 .real and .imag strided views match per-call execution bit-for-bit."""
    rng = np.random.default_rng(401)
    n_samples = 40000
    # Two packed middle pairs per detector -> 4 fine banks with distinct tap lengths
    packed_h1 = (rng.standard_normal((2, n_samples))
                 + 1j * rng.standard_normal((2, n_samples))).astype(np.complex64)
    packed_l1 = (rng.standard_normal((2, n_samples))
                 + 1j * rng.standard_normal((2, n_samples))).astype(np.complex64)

    banks = []
    for k, counts in enumerate([
        np.linspace(180, 320, 12, dtype=np.int64),
        np.linspace(195, 345, 12, dtype=np.int64),
        np.linspace(210, 360, 10, dtype=np.int64),
        np.linspace(210, 360, 10, dtype=np.int64),
    ]):
        bank, taps = _make_bank(rng, len(counts), counts, complex_taps=True,
                                fft_lengths=(2048,), binsize=204, threshold=4.2)
        # Inject synthetic signals into H1 and L1 lanes
        lane_h1 = packed_h1[k // 2].imag if (k % 2) else packed_h1[k // 2].real
        lane_l1 = packed_l1[k // 2].imag if (k % 2) else packed_l1[k // 2].real
        c0 = int(counts[0])
        pos = 12000 + k * 900
        lane_h1[pos:pos + c0] += 8.5 * np.real(taps[0, :c0]).astype(np.float32)
        lane_l1[pos + 500:pos + 500 + c0] += 7.5 * np.real(taps[0, :c0]).astype(np.float32)
        banks.append(bank)

    win = slice(2048, n_samples - 2048)
    jobs = []
    for k, bank in enumerate(banks):
        lane_h1 = packed_h1[k // 2].imag if (k % 2) else packed_h1[k // 2].real
        lane_l1 = packed_l1[k // 2].imag if (k % 2) else packed_l1[k // 2].real
        assert lane_h1.strides == (8,) and lane_l1.strides == (8,)
        jobs.append((bank, lane_h1, {"windows": win}))
        jobs.append((bank, lane_l1, {"windows": win}))

    want = [_reference_via_plan(b, s, kw) for b, s, kw in jobs]
    got = mf.TimeDomainFilterBank.filter_series_many(jobs)
    assert len(got) == len(want)
    total_triggers = 0
    for g_res, w_res in zip(got, want):
        _assert_results_identical(g_res, w_res)
        total_triggers += len(g_res.snr)
    assert total_triggers >= 4

    # Deferred mode (wait=False) returns _Deferred wrappers yielding identical results
    deferred = mf.TimeDomainFilterBank.filter_series_many(jobs, wait=False)
    for fut, w_res in zip(deferred, want):
        assert hasattr(fut, "result")
        _assert_results_identical(fut.result(), w_res)


@pytest.mark.parametrize("real_series", [False, True])
def test_shared_forward_fft_reduces_follower_forward_ticks(target, real_series):
    """Follower banks on the same series and block starts reuse lead forward spectra."""
    rng = np.random.default_rng(902 + int(real_series))
    n_samples = 65536
    counts = np.full(16, 256, dtype=np.int64)
    bank_a, taps_a = _make_bank(rng, 16, counts, complex_taps=real_series,
                                fft_lengths=(2048,), binsize=256, threshold=4.4)
    bank_b, taps_b = _make_bank(rng, 16, counts, complex_taps=real_series,
                                fft_lengths=(2048,), binsize=256, threshold=4.4)

    if real_series:
        ser = rng.standard_normal(n_samples).astype(np.float32)
        ser[15000:15256] += 9.0 * np.real(taps_a[3, :256]).astype(np.float32)
        ser[33000:33256] += 9.0 * np.real(taps_b[5, :256]).astype(np.float32)
    else:
        ser = ((rng.standard_normal(n_samples) + 1j * rng.standard_normal(n_samples))
               / np.sqrt(2.0)).astype(np.complex64)
        ser[15000:15256] += 9.0 * taps_a[3, :256]
        ser[33000:33256] += 9.0 * taps_b[5, :256]

    win = slice(2048, n_samples - 2048)
    # Warm up both plans once
    ref_a = _reference_via_plan(bank_a, ser, {"windows": win})
    ref_b = _reference_via_plan(bank_b, ser, {"windows": win})

    def forward_ticks(bank):
        wc = bank._groups[0].plan.work_counts()["ticks"]
        return wc["series"] - sum(wc["tiers"]) - wc["refine"]

    # Measure standalone forward ticks on bank_b over 4 repetitions
    f0 = forward_ticks(bank_b)
    for _ in range(4):
        _reference_via_plan(bank_b, ser, {"windows": win})
    standalone_b_fwd = forward_ticks(bank_b) - f0

    # Measure follower forward ticks on bank_b when batched behind bank_a
    f1 = forward_ticks(bank_b)
    for _ in range(4):
        res_a, res_b = mf.TimeDomainFilterBank.filter_series_many([
            (bank_a, ser, {"windows": win}),
            (bank_b, ser, {"windows": win}),
        ])
    shared_b_fwd = forward_ticks(bank_b) - f1

    _assert_results_identical(res_a, ref_a)
    _assert_results_identical(res_b, ref_b)
    assert len(res_a.snr) >= 1 and len(res_b.snr) >= 1
    # Follower bank skips block forward transforms and only sets tier-0 pointers
    assert shared_b_fwd < 0.65 * standalone_b_fwd


def test_multigroup_windows_pack_and_mixed_batch_modes(target):
    """Multi-group banks, disjoint windows, Hermitian packing, follow-ups, and mode switches."""
    rng = np.random.default_rng(777)
    n_samples = 49152
    # Spans 2048 and 4096 block sizes and splits into multiple sub-batches via max_batch_size=6
    counts = np.array([160, 180, 200, 220, 240, 240, 260, 1200, 1300, 1400, 1450, 1500],
                      dtype=np.int64)
    bank_multi, taps_m = _make_bank(
        rng, len(counts), counts, complex_taps=False,
        fft_lengths=(2048, 4096), binsize=192, threshold=4.1,
        max_batch_size=6, pack_templates=True,
    )
    assert len(bank_multi._groups) >= 3

    ser = ((rng.standard_normal(n_samples) + 1j * rng.standard_normal(n_samples))
           / np.sqrt(2.0)).astype(np.complex64)
    ser[10000:10160] += 9.5 * taps_m[0, :160]
    ser[31000:32500] += 9.5 * taps_m[-1, :1500]

    wins = [(4096, 18000), (26000, 44000)]

    # Standalone filter_series (uses single-job _cpu_sparse_batch) vs _reference_via_plan
    got_single = bank_multi.filter_series(ser, windows=wins)
    want_single = _reference_via_plan(bank_multi, ser, {"windows": wins})
    _assert_results_identical(got_single, want_single)
    assert len(got_single.snr) >= 2

    # Mixed batch: normal hier job, high-trigger low-threshold override, below-bank-threshold
    # fallback, single-template follow-up, unaligned binsize=None, and empty window
    q_counts = np.array([150, 150, 180, 200], dtype=np.int64)
    q_bank, _ = _make_bank(rng, 4, q_counts, complex_taps=True,
                           fft_lengths=(2048,), binsize=None, threshold=3.2)
    packed = (rng.standard_normal(n_samples) + 1j * rng.standard_normal(n_samples)).astype(np.complex64)
    contig_real = np.ascontiguousarray(packed.real)

    mixed_jobs = [
        (bank_multi, ser, {"windows": wins}),
        (bank_multi, ser, {"windows": wins, "threshold": 4.8}),
        (bank_multi, ser, {"windows": wins, "threshold": 3.5}),   # < bank.threshold -> flat fallback
        (bank_multi, ser, {"windows": wins, "template_index": 0}),
        (bank_multi, ser, {"windows": [(5000, 5000)]}),            # empty window
        # Same quadrature bank across contiguous real, strided real, and complex64 in one batch
        (q_bank, contig_real, {"windows": slice(2048, 25000), "binsize": 64}),
        (q_bank, packed.imag, {"windows": slice(2048, 25000), "binsize": 64}),
        (q_bank, ser, {"windows": slice(2048, 25000), "binsize": 64}),
    ]
    want_mixed = [_reference_via_plan(b, s, kw) for b, s, kw in mixed_jobs]
    got_mixed = mf.TimeDomainFilterBank.filter_series_many(mixed_jobs)
    for g_res, w_res in zip(got_mixed, want_mixed):
        _assert_results_identical(g_res, w_res)


def test_hmf_sparse_counts_optional_and_batch_validation(target):
    """_core.HMF.run_series_sparse accepts cnt=None or an int32 buffer and matches exactly."""
    rng = np.random.default_rng(1234)
    n, nt, nblocks = 1024, 8, 20
    hmf = _core.HMF(n, 1, nt, [128], 8, n)
    hmf.set_reference(np.ones(n, dtype=np.float32))
    hmf.set_thresholds([2.5])
    tmpls = ((rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n)))
             / np.sqrt(2.0 * n)).astype(np.complex64)
    hmf.set_template_batch(0, tmpls)

    step = 768
    ser = ((rng.standard_normal(nblocks * step + n)
            + 1j * rng.standard_normal(nblocks * step + n)) / np.sqrt(2.0)).astype(np.complex64)
    st = (np.arange(nblocks) * step).astype(np.uintp)
    ws = np.full(nblocks, 128, dtype=np.uintp)
    we = np.full(nblocks, n - 128, dtype=np.uintp)

    cnt_a = np.full(nblocks * nt, -99, dtype=np.int32)
    fl_a, ix_a, vl_a, tot_a = hmf.run_series_sparse(ser, st, ws, we, 0, nt, 64, 3.3, cnt_a)
    fl_b, ix_b, vl_b, tot_b = hmf.run_series_sparse(ser, st, ws, we, 0, nt, 64, 3.3, None)
    assert (fl_a, ix_a, vl_a, tot_a) == (fl_b, ix_b, vl_b, tot_b)
    assert np.all(cnt_a >= 0)
    assert int(cnt_a.sum()) == tot_a

    # Empty batch and single-item batch match run_series_sparse
    assert _core.HMF.run_series_batch_sparse([]) == []
    [(fl_c, ix_c, vl_c, tot_c)] = _core.HMF.run_series_batch_sparse([
        (hmf, ser, st, ws, we, 0, nt, 64, 3.3, None, None, 0),
    ])
    assert (fl_c, ix_c, vl_c, tot_c) == (fl_a, ix_a, vl_a, tot_a)

    # Too-small counts buffer still raises ValueError
    with pytest.raises(ValueError, match="counts buffer too small"):
        hmf.run_series_sparse(ser, st, ws, we, 0, nt, 64, 3.3, np.zeros(2, dtype=np.int32))


def test_hmf_batch_sparse_thread_busy_guard():
    """Concurrent use of an HMF instance across threads raises RuntimeError."""
    import threading
    rng = np.random.default_rng(2026)
    n, nt, nblocks = 2048, 64, 400
    hmf = _core.HMF(n, 1, nt, [128], 8, n)
    hmf.set_reference(np.ones(n, dtype=np.float32))
    hmf.set_thresholds([1.5])
    tmpls = ((rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n)))
             / np.sqrt(2.0 * n)).astype(np.complex64)
    hmf.set_template_batch(0, tmpls)
    step = 1536
    ser = np.zeros(nblocks * step + n, dtype=np.complex64)
    st = (np.arange(nblocks) * step).astype(np.uintp)
    ws = np.full(nblocks, 128, dtype=np.uintp)
    we = np.full(nblocks, n - 128, dtype=np.uintp)
    job = (hmf, ser, st, ws, we, 0, nt, 64, 3.3, None, None, 0)

    barrier = threading.Barrier(2)
    errors = []

    def worker():
        barrier.wait()
        for _ in range(15):
            try:
                _core.HMF.run_series_batch_sparse([job, job])
            except RuntimeError as exc:
                errors.append(str(exc))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert not hmf._busy
    for msg in errors:
        assert "in use by another thread" in msg

