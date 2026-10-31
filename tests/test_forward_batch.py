"""Batched small-N forward transforms (fft_forward_batch / fft_real_batch), fused scaled
stage-A loads (fft_forward_scaled), and windowed correlation stores (corr_prod_window) across
all supported targets, block sizes, real strides, ragged edge blocks, and narrow windows."""
import numpy as np
import pytest

import matchedfilter as mf


@pytest.fixture(params=mf.targets())
def target(request):
    mf.backend()
    mf.set_target(request.param)
    yield request.param
    mf.set_target(None)


@pytest.mark.parametrize("n", [128, 256, 512, 1024, 2048, 4096])
@pytest.mark.parametrize("real_kind", ["complex", "real_contig", "real_stride2"])
def test_forward_batch_matches_reference_and_is_batch_invariant(target, n, real_kind):
    rng = np.random.default_rng(100 + n)
    nt = 4
    L_tap = min(65, n // 4 + 1)
    taps = (rng.standard_normal((nt, L_tap)) + 1j * rng.standard_normal((nt, L_tap))).astype(np.complex64)
    taps /= np.linalg.norm(taps, axis=1, keepdims=True)
    step = n - L_tap + 1
    # 19 blocks + 13 samples exercises a full SIMD batch + a partial tail batch + a ragged final block
    S = 18 * step + L_tap + 13
    if real_kind == "complex":
        ser = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
        ser_ref = ser
    elif real_kind == "real_contig":
        ser = rng.standard_normal(S).astype(np.float32)
        ser_ref = ser.astype(np.complex64)
    else:
        packed = np.empty(S, np.complex64)
        packed.real = rng.standard_normal(S).astype(np.float32)
        packed.imag = rng.standard_normal(S).astype(np.float32)
        ser = packed.imag
        ser_ref = np.ascontiguousarray(ser, dtype=np.complex64)

    # 1. CorrelationFilter (via TimeDomainFilterBank engine='corr', ndata=1)
    cbank = mf.TimeDomainFilterBank(taps, engine="corr", fft_lengths=(n,), device="cpu")
    got = cbank.correlate_series(ser)
    # Direct numpy overlap-save reference
    for t in range(nt):
        ref_t = np.correlate(ser_ref, taps[t], mode="same")
        lo = L_tap // 2
        hi = S - L_tap // 2
        np.testing.assert_allclose(got[t, lo:hi], ref_t[lo:hi], rtol=3e-5, atol=3e-5)

    # Multi-window vs single-window must be bit-for-bit identical (cnt=1 vs cnt>1 & corr_prod_window)
    wins = [(n + 3, n + 4), (n + 17, n + 150), (3 * step + 50, 3 * step + 250)]
    if wins[-1][1] < S - L_tap:
        z_union = cbank.correlate_series(ser, windows=wins)
        for a, b in wins:
            z_one = cbank.correlate_series(ser, windows=slice(a, b))
            np.testing.assert_array_equal(z_union[:, a:b], z_one[:, a:b])
            np.testing.assert_allclose(z_one[:, a:b], got[:, a:b], rtol=0.0, atol=0.0)

    # 2. HierarchicalFilter real & complex series forward path (including ragged edge block + have==0)
    hf = mf.HierarchicalFilter(n, 1, nt, chain=(min(64, n // 2),), device="cpu")
    hf.set_reference(np.ones(n, np.float32))
    hf.set_coarse_threshold((0.0,))
    hf.set_templates(np.conj(np.fft.fft(taps, n=n, axis=1)).astype(np.complex64))
    nblk = 19
    starts = (np.arange(nblk) * step).astype(np.uintp)
    # Put last block start past S to test have == 0 zero-block edge handling in batched forward
    starts[-1] = S + 16
    ws = np.full(nblk, L_tap // 2, np.uintp)
    we = np.full(nblk, n - L_tap // 2, np.uintp)
    p_all = hf.run_series(ser, starts, ws, we, binsize=n, threshold=0.0).copy()
    p_one = hf.run_series(ser, starts[:1], ws[:1], we[:1], binsize=n, threshold=0.0).copy()
    np.testing.assert_array_equal(p_all["index"][:1], p_one["index"])
    np.testing.assert_array_equal(p_all["value"][:1], p_one["value"])
    # Zero block (starts[-1] >= S) produces zero correlation
    np.testing.assert_allclose(np.abs(p_all["value"][-1]), 0.0, atol=1e-7)
