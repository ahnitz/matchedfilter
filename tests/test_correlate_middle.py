"""Windowed and streaming continuous correlation across SIMD targets, alignments, and bounds."""
import os
import subprocess
import sys
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import CorrelationFilter, TimeDomainFilterBank
from matchedfilter._filter import _automatic_series_layout
from matchedfilter.search import BlockInput, HierarchicalSearch, Inner, Leaf, Root


def _llc_bytes():
    """Return the CPU last-level cache size in bytes from sysfs (or 32 MiB fallback)."""
    for idx in (3, 2):
        try:
            txt = open(f"/sys/devices/system/cpu/cpu0/cache/index{idx}/size").read().strip()
        except OSError:
            continue
        mult = {"K": 1024, "M": 1024 * 1024}.get(txt[-1:], 1)
        return int(txt.rstrip("KM")) * mult
    return 32 << 20


def _alloc_with_offset(shape, byte_offset, sentinel=0.0):
    """Return a writable C-contiguous complex64 array whose base pointer mod 64 == byte_offset."""
    nbytes = int(np.prod(shape)) * 8
    raw = np.empty(nbytes + 128, dtype=np.uint8)
    cur = raw.ctypes.data & 63
    shift = (byte_offset - cur) & 63
    arr = raw[shift:shift + nbytes].view(np.complex64).reshape(shape)
    arr[:] = sentinel
    assert (arr.ctypes.data & 63) == byte_offset
    return arr


@pytest.mark.parametrize("n", [64, 128, 256, 512, 1024, 2048, 4096, 8192])
@pytest.mark.parametrize("real", [False, True])
def test_windowed_correlation_across_targets_and_alignments(n, real):
    """Windowed continuous correlation must match direct FFT reference across every available
    SIMD target, transform size (pairbatch and balanced), window shape, and base alignment."""
    if real and n < 128:
        pytest.skip("half-size transform requires n >= 128")
    rng = np.random.default_rng(100 + n + int(real))
    nt = 5 if n >= 512 else 19
    L = 3 * n + 37

    ser = rng.standard_normal(L).astype(np.float32)
    if not real:
        ser = (ser + 1j * rng.standard_normal(L)).astype(np.complex64)
    ser_c = ser.astype(np.complex64)

    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    spec = np.fft.fft(h, axis=1).astype(np.complex64)

    windows = [
        (n // 8, n - n // 8),          # 64B/32B/16B aligned interior
        (n // 8 + 2, n - n // 8 - 2),  # +16B shifted
        (n // 8 + 1, n - n // 8 - 3),  # odd lo -> 8B aligned destination
        (n // 4 + 3, n // 4 + 10),     # narrow window (< AP_W on AVX2/AVX3: lo_in > hi_in)
    ]

    targets = list(mf.targets())
    try:
        for tgt in targets:
            mf.set_target(tgt)
            for valid in windows:
                if valid[0] >= valid[1] or valid[1] > n:
                    continue
                cf = CorrelationFilter(n, ndata=1, ntemplates=nt, valid=valid, device="cpu")
                cf.set_templates(spec)
                lo, hi = cf.valid
                st, _, _ = _automatic_series_layout(L, cf.valid)
                ep = cf._execution_plan()
                run = ep.correlate_series_continuous_real if real else ep.correlate_series_continuous

                for base_off in (0, 8, 16, 32):
                    sentinel = np.complex64(-13.5 + 27.25j)
                    got = _alloc_with_offset((nt, L), base_off, sentinel)
                    run(ser, st, lo, hi, 0, nt, got)

                    b0 = int(st[0])
                    blk = np.zeros(n, dtype=np.complex64)
                    have = min(n, L - b0)
                    blk[:have] = ser_c[b0:b0 + have]
                    ref = np.fft.ifft(np.fft.fft(blk)[None, :] * np.conj(spec), axis=1)
                    end = min(hi, L - b0)
                    scale = max(float(np.abs(ref).max()), 1.0)
                    np.testing.assert_allclose(
                        got[:, b0 + lo:b0 + end],
                        ref[:, lo:end],
                        rtol=0,
                        atol=2e-6 * scale,
                    )
    finally:
        mf.set_target(None)


@pytest.mark.parametrize("n", [128, 4096])
@pytest.mark.parametrize("real", [False, True])
def test_streaming_stores_bit_identical_across_targets_bounds_and_alignments(monkeypatch, n, real):
    """Above-LLC streaming correlation and MF_CORR_NO_STREAM=1 must write identical bits across
    every SIMD target, base pointer alignment (0..48B), and per-block bounds."""
    llc = _llc_bytes()
    if llc > (128 << 20):
        pytest.skip("LLC size too large for quick streaming test")
    rng = np.random.default_rng(200 + n + int(real))
    nt = 16 if n >= 512 else 19
    lo, hi = 8, n - 8
    span = hi - lo

    # Choose enough blocks so nt * span_sum * 8 > 2.5 * llc, forcing stream=1 naturally.
    n_test = 6
    n_pad = int((5 * llc) // (2 * nt * span * 8)) + 2
    L = (n_test + 2) * n
    ser = rng.standard_normal(L).astype(np.float32)
    if not real:
        ser = (ser + 1j * rng.standard_normal(L)).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    spec = np.fft.fft(h, axis=1).astype(np.complex64)

    # First n_pad blocks write to block 0 (raising span_sum past LLC); last 6 blocks sit in
    # disjoint regions [k*n, (k+1)*n) testing aligned, +16B, +32B, odd-start, 1-sample, and <16-sample bounds.
    st = np.array([0] * n_pad + [k * n for k in range(1, n_test + 1)], dtype=np.uintp)
    bounds = np.empty((len(st), 2), dtype=np.uintp)
    bounds[:n_pad] = (lo, hi)
    bounds[n_pad + 0] = (lo, hi)                   # aligned interior
    bounds[n_pad + 1] = (lo + 2, hi - 2)           # +16B shifted
    bounds[n_pad + 2] = (lo + 4, hi - 4)           # +32B shifted
    bounds[n_pad + 3] = (lo + 1, hi - 3)           # odd start (+8B)
    bounds[n_pad + 4] = (lo + 5, lo + 6)           # 1-sample bound
    bounds[n_pad + 5] = (lo + 3, min(hi, lo + 12)) # narrow (< 16 lanes) bound

    span_sum = int((bounds[:, 1] - bounds[:, 0]).sum())
    assert nt * span_sum * 8 > 2 * llc

    for tgt in mf.targets():
        try:
            mf.set_target(tgt)
            cf = CorrelationFilter(n, ndata=1, ntemplates=nt, valid=(lo, hi), device="cpu")
            cf.set_templates(spec)
            ep = cf._execution_plan()
            run = ep.correlate_series_continuous_real if real else ep.correlate_series_continuous

            for base_off in (0, 8, 16, 32, 48):
                sentinel = np.complex64(42.0 - 19.0j)
                monkeypatch.setenv("MF_CORR_NO_STREAM", "1")
                ref = _alloc_with_offset((nt, L), base_off, sentinel)
                run(ser, st, lo, hi, 0, nt, ref, bounds)

                monkeypatch.delenv("MF_CORR_NO_STREAM", raising=False)
                got = _alloc_with_offset((nt, L), base_off, sentinel)
                run(ser, st, lo, hi, 0, nt, got, bounds)

                assert np.array_equal(
                    got.view(np.uint32), ref.view(np.uint32)
                ), f"mismatch target={tgt} n={n} real={real} off={base_off}"

                inside = np.zeros(L, dtype=bool)
                for s, (a, b) in zip(st, bounds):
                    s_i = int(s)
                    inside[s_i + int(a):min(s_i + int(b), L)] = True
                assert np.all(got[:, ~inside] == sentinel)
        finally:
            mf.set_target(None)


def test_mf_isa_env_subprocesses_agree():
    """Verify MF_ISA=AVX3, AVX2, AVX, SSE4 (whichever this CPU/build supports) agree to 1e-6."""
    avail = set(mf.targets())
    wanted = [t for t in ("AVX3", "AVX2", "AVX", "SSE4") if t in avail]
    if len(wanted) < 2:
        pytest.skip("fewer than two x86 SIMD targets available")
    code = (
        "import numpy as np, matchedfilter as mf\n"
        "rng = np.random.default_rng(9)\n"
        "taps = rng.standard_normal((16, 511)).astype(np.float32)\n"
        "ser = rng.standard_normal(32768).astype(np.float32)\n"
        "bank = mf.TimeDomainFilterBank(taps, engine='corr', device='cpu')\n"
        "out = bank.correlate_series(ser, windows=[(1024, 31000)])\n"
        "sys.stdout.buffer.write(out.tobytes())\n"
    )
    outputs = {}
    for isa in wanted:
        env = dict(os.environ)
        env["MF_ISA"] = isa
        proc = subprocess.run(
            [sys.executable, "-c", "import sys; " + code],
            env=env,
            check=True,
            capture_output=True,
        )
        outputs[isa] = np.frombuffer(proc.stdout, dtype=np.complex64).reshape(16, 32768)
    base = outputs[wanted[0]]
    scale = max(float(np.abs(base).max()), 1.0)
    for isa in wanted[1:]:
        np.testing.assert_allclose(outputs[isa], base, rtol=0, atol=1e-6 * scale)


def test_hierarchical_search_cpu_multi_chunk_reuses_aligned_buffers():
    """Multi-chunk CPU HierarchicalSearch keeps 64B-aligned inner slots and root buffers
    and matches single-chunk runs peak-for-peak."""
    rng = np.random.default_rng(123)
    N = 16384
    inners = []
    for i, c in enumerate((129, 257, 513)):
        ltaps = (rng.standard_normal((4, 65)) + 1j * rng.standard_normal((4, 65))).astype(np.complex64)
        ltaps /= np.linalg.norm(ltaps, axis=1, keepdims=True)
        lf = Leaf(ltaps, np.full(4, 65, dtype=np.int64), node_id=f"lf{i}")
        itaps = rng.standard_normal(c).astype(np.float32)
        itaps /= np.linalg.norm(itaps)
        inners.append(Inner(itaps, count=c, children=[lf], node_id=f"in{i}"))

    root = Root(
        spectrum=np.ones(N // 2 + 1, dtype=np.complex64),
        band=(64, N // 2 - 64),
        children=inners,
        profile=(np.ones(257, dtype=np.float64), 1.0),
    )
    specs = []
    for _ in range(3):
        sp = (rng.standard_normal(N // 2 + 1) + 1j * rng.standard_normal(N // 2 + 1)).astype(np.complex64)
        sp[0] = sp[0].real
        sp[-1] = sp[-1].real
        specs.append(sp)
    inp = {"H1": BlockInput(specs, [(2048, N - 2048)] * 3, lambda rt, k: 1.0 / np.sqrt(N))}

    hs = HierarchicalSearch([root], threshold=4.5, leaf_options=dict(binsize=512, engine="hier", device="cpu"))
    root_ptrs = []
    multi_peaks = {}

    def on_series(ctx):
        arr = ctx.series["H1"]
        assert (arr.ctypes.data & 63) == 0
        root_ptrs.append(arr.ctypes.data)

    def on_peaks(ctx):
        p = ctx.peaks["H1"]
        # Packed real inner rows start on 64B; lane 0 (.real) is +0B and lane 1 (.imag) is +4B
        assert (ctx.series("H1").ctypes.data & 63) in (0, 4)
        multi_peaks[(ctx.chunk, ctx.leaf.node_id)] = (
            p.template_indices.copy(), p.sample_indices.copy(), p.snr.copy()
        )

    hs.run(inp, on_series=on_series, on_peaks=on_peaks)
    # Chunk 0 and chunk 2 reuse slot 0 (chunk % 2), chunk 1 uses slot 1
    assert root_ptrs[0] == root_ptrs[2] and root_ptrs[0] != root_ptrs[1]

    # Compare every chunk against an isolated 1-chunk search
    for k in range(3):
        hs1 = HierarchicalSearch([root], threshold=4.5, leaf_options=dict(binsize=512, engine="hier", device="cpu"))
        inp1 = {"H1": BlockInput([specs[k]], [(2048, N - 2048)], lambda rt, _: 1.0 / np.sqrt(N))}
        got1 = {}
        hs1.run(inp1, on_peaks=lambda ctx, k=k: got1.update({
            (k, ctx.leaf.node_id): (
                ctx.peaks["H1"].template_indices.copy(),
                ctx.peaks["H1"].sample_indices.copy(),
                ctx.peaks["H1"].snr.copy(),
            )
        }))
        for key, val in got1.items():
            np.testing.assert_array_equal(multi_peaks[key][0], val[0])
            np.testing.assert_array_equal(multi_peaks[key][1], val[1])
            np.testing.assert_allclose(multi_peaks[key][2], val[2], rtol=0, atol=1e-6)


@pytest.mark.parametrize("n", [8192, 16384, 32768])
@pytest.mark.parametrize("real", [False, True])
def test_large_balanced_carry_streaming_and_l2_blocking_bit_identical(monkeypatch, n, real):
    """Large balanced transforms (n >= 8192, ndata > 1) exercise L2-aware g=1 series_spectra
    blocking and 64B-misaligned carry-streaming across all SIMD targets and window shapes."""
    llc = _llc_bytes()
    if llc > (128 << 20):
        pytest.skip("LLC size too large for quick streaming test")
    rng = np.random.default_rng(500 + n + int(real))
    nt = 6
    lo, hi = 7, n - 9
    span = hi - lo

    n_test = 7
    n_pad = int((5 * llc) // (2 * nt * span * 8)) + 2
    L = (n_test + 2) * n
    ser = rng.standard_normal(L).astype(np.float32)
    if not real:
        ser = (ser + 1j * rng.standard_normal(L)).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    spec = np.fft.fft(h, axis=1).astype(np.complex64)

    st = np.array([0] * n_pad + [k * n for k in range(1, n_test + 1)], dtype=np.uintp)
    bounds = np.empty((len(st), 2), dtype=np.uintp)
    bounds[:n_pad] = (lo, hi)
    bounds[n_pad + 0] = (lo, hi)                        # unaligned lo/hi
    bounds[n_pad + 1] = (16, n - 16)                    # 64B-aligned lo/hi
    bounds[n_pad + 2] = (18, n - 18)                    # +16B shifted
    bounds[n_pad + 3] = (21, n - 23)                    # odd start and odd end (+8B)
    bounds[n_pad + 4] = (256, 512)                      # single interior rowSpan
    bounds[n_pad + 5] = (257, 263)                      # narrow (< 8 samples, k1_lo > k1_hi)
    bounds[n_pad + 6] = (n // 2 - 5, n // 2 + 261)      # partial head + full row + partial tail

    targets = list(mf.targets())
    offs = (0, 4, 8, 16, 24, 32, 40, 48, 56) if n == 8192 else (0, 8, 16, 24, 32, 48, 56)
    try:
        for tgt in targets:
            mf.set_target(tgt)
            # ndata=4 > 1 exercises L2-aware g=1 blocking for 2*n*sizeof(float) >= 65536
            cf = CorrelationFilter(n, ndata=4, ntemplates=nt, valid=(lo, hi), device="cpu")
            cf.set_templates(spec)
            ep = cf._execution_plan()
            run = ep.correlate_series_continuous_real if real else ep.correlate_series_continuous

            for base_off in offs:
                sentinel = np.complex64(-31.25 + 17.5j)
                monkeypatch.setenv("MF_CORR_NO_STREAM", "1")
                ref = _alloc_with_offset((nt, L), base_off, sentinel)
                run(ser, st, lo, hi, 0, nt, ref, bounds)

                monkeypatch.delenv("MF_CORR_NO_STREAM", raising=False)
                got = _alloc_with_offset((nt, L), base_off, sentinel)
                run(ser, st, lo, hi, 0, nt, got, bounds)

                assert np.array_equal(
                    got.view(np.uint32), ref.view(np.uint32)
                ), f"mismatch target={tgt} n={n} real={real} off={base_off}"

                inside = np.zeros(L, dtype=bool)
                for s, (a, b) in zip(st, bounds):
                    s_i = int(s)
                    inside[s_i + int(a):min(s_i + int(b), L)] = True
                assert np.all(got[:, ~inside] == sentinel)
    finally:
        mf.set_target(None)


def test_correlate_series_out_none_modes_and_recycled_buffer_lifetime():
    """CPU correlate_series(out=None) matches preallocated out across full, wide, multi-gap,
    sparse, and empty windows, single/selected templates, scales, and view lifetimes."""
    rng = np.random.default_rng(909)
    S = 32768
    # Interleaved short and long tap counts produce multiple groups in TimeDomainFilterBank
    counts = np.array([65, 1025, 97, 1537, 129, 2047], dtype=np.int64)
    nt = len(counts)
    taps = np.zeros((nt, int(counts.max())), dtype=np.float32)
    for i, c in enumerate(counts):
        taps[i, :c] = rng.standard_normal(int(c)).astype(np.float32)

    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="corr", device="cpu")
    ser1 = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
    ser2 = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
    scales = rng.uniform(0.5, 2.0, size=nt).astype(np.float32)

    # Exercise full, wide (> S//2), gapped wide (> S//2), sparse (<= S//2), and empty windows
    window_cases = [
        None,
        [(1500, S - 1200)],
        [(600, S // 2 - 200), (S // 2 + 200, S - 700)],
        [(4000, 9000)],
        [],
    ]
    for win in window_cases:
        ref = np.full((nt, S), -77.0 + 55.0j, dtype=np.complex64)
        bank.correlate_series(ser1, windows=win, scales=scales, out=ref)
        # Pollute recycled pool slot first, then drop so the next wide call reuses dirty memory
        tmp = bank.correlate_series(ser2)
        tmp[:] = 12345.0 - 6789.0j
        del tmp
        got = bank.correlate_series(ser1, windows=win, scales=scales)
        assert (got.ctypes.data & 16383) == 0
        np.testing.assert_array_equal(got, ref)

    # Single-template (returns 1D slice view over (1, S) buffer) and selected-templates modes
    ref_1d = np.full(S, -11.0 + 22.0j, dtype=np.complex64)
    bank.correlate_series(ser1, windows=[(1000, S - 1000)], template_index=3, scales=scales, out=ref_1d)
    got_1d = bank.correlate_series(ser1, windows=[(1000, S - 1000)], template_index=3, scales=scales)
    assert got_1d.shape == (S,)
    np.testing.assert_array_equal(got_1d, ref_1d)
    snap_1d = got_1d.copy()

    # Holding got_1d (a view) while running another single-template call must not alias got_1d
    other_1d = bank.correlate_series(ser2, windows=[(1000, S - 1000)], template_index=1)
    np.testing.assert_array_equal(got_1d, snap_1d)
    del got_1d, other_1d

    sel = [4, 1, 5]
    ref_sel = np.full((len(sel), S), -9.0 + 3.0j, dtype=np.complex64)
    bank.correlate_series(ser1, windows=[(800, S - 800)], templates=sel, scales=scales, out=ref_sel)
    got_sel = bank.correlate_series(ser1, windows=[(800, S - 800)], templates=sel, scales=scales)
    np.testing.assert_array_equal(got_sel, ref_sel)

    # Holding only a sub-slice / .real view after deleting the parent array must keep backing memory alive
    r_parent = bank.correlate_series(ser1, windows=[(1000, S - 1000)])
    sub_view = r_parent[2, 2000:2500]
    expected_sub = sub_view.copy()
    del r_parent
    r_next = bank.correlate_series(ser2, windows=[(1000, S - 1000)])
    np.testing.assert_array_equal(sub_view, expected_sub)
    del sub_view, r_next

