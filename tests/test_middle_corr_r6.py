"""Regression and parity tests for middle-stage continuous correlation (Track 3).

Covers two-regime CPU block tiling across transform sizes, cached-forward subset
block tiling, cost-based correlation bank partitioning on CPU and GPU, and GPU
device zeroing on empty windows and multi-group shared outputs.
"""
import os
import subprocess
import sys

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter.time_domain import TimeDomainFilterBank


def _gpu_corr_bank(taps, tap_counts=None, fft_lengths=None):
    """Instantiate a GPU correlation bank or skip when no GPU backend is available.

    Parameters
    ----------
    taps : numpy.ndarray
        Time-domain filter taps array.
    tap_counts : Sequence[int], optional
        Per-template active tap lengths.
    fft_lengths : Sequence[int], optional
        Explicit candidate FFT block sizes.

    Returns
    -------
    TimeDomainFilterBank
        Initialized correlation bank on ``gpu:0``.
    """
    try:
        bank = TimeDomainFilterBank(
            taps, tap_counts=tap_counts, engine="corr", device="gpu:0",
            fft_lengths=fft_lengths,
        )
        bank._groups
    except Exception as exc:  # pragma: no cover - no GPU available
        pytest.skip(f"no GPU device: {exc}")
    return bank


def _direct_correlate(series, taps, counts):
    """Compute direct NumPy correlation matching TimeDomainFilterBank lag alignment.

    Parameters
    ----------
    series : numpy.ndarray
        1-D real or complex input series of length ``S``.
    taps : numpy.ndarray
        2-D array of real or complex taps.
    counts : numpy.ndarray
        1-D integer array of tap counts per template.

    Returns
    -------
    numpy.ndarray
        ``(len(counts), len(series))`` complex64 reference correlation.
    """
    S = len(series)
    x = np.asarray(series, dtype=np.complex128)
    out = np.zeros((len(counts), S), dtype=np.complex64)
    for idx, cnt in enumerate(counts):
        cnt = int(cnt)
        centre = (cnt - 1) // 2
        filt = np.conj(np.asarray(taps[idx, :cnt], dtype=np.complex128))[::-1]
        full = np.convolve(x, filt, mode="full")
        out[idx] = full[centre:centre + S].astype(np.complex64)
    return out


@pytest.mark.parametrize("n_fft", [2048, 4096, 8192, 16384, 32768, 65536])
@pytest.mark.parametrize("real_series", [False, True])
def test_cpu_block_tiling_regimes_exact(n_fft, real_series):
    """Verify CPU continuous correlation across L2-resident and LLC-overflow tile regimes."""
    rng = np.random.default_rng(100 + n_fft + int(real_series))
    nt = 10 if n_fft <= 16384 else 6
    max_tap = min(n_fft // 4, 2048)
    counts = np.linspace(31, max_tap - 1, nt, dtype=np.int64)
    taps = np.zeros((nt, int(counts.max())), dtype=np.float32)
    for i, c in enumerate(counts):
        taps[i, :c] = rng.standard_normal(int(c)).astype(np.float32) / np.sqrt(float(c))

    # Span at least 5 blocks so multi-block tiling (b_tile > 1) executes multiple slabs.
    n_valid = n_fft - int(counts.max()) + 1
    S = max(5 * n_valid + n_fft, 24576)
    if real_series:
        ser = rng.standard_normal(S).astype(np.float32)
    else:
        ser = ((rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2.0)).astype(
            np.complex64
        )

    c_bad = int(counts.max()) // 2
    win = (c_bad + 64, S - n_fft - 64)
    bank = TimeDomainFilterBank(
        taps, tap_counts=counts, engine="corr", device="cpu", fft_lengths=(n_fft,)
    )
    got = bank.correlate_series(ser, windows=[win])
    ref = _direct_correlate(ser, taps, counts)

    # Unwritten margins outside the requested window must be exact zero.
    assert np.all(got[:, :win[0]] == 0)
    assert np.all(got[:, win[1]:] == 0)

    # Interior window values must match direct time-domain correlation.
    sl = slice(win[0], win[1])
    scale = max(float(np.abs(ref[:, sl]).max()), 1e-6)
    np.testing.assert_allclose(got[:, sl], ref[:, sl], rtol=0, atol=2e-4 * scale)


@pytest.mark.parametrize("n_fft", [8192, 65536])
def test_cpu_cached_forward_selected_templates_tiled(n_fft):
    """Verify subset correlation (corr_fwd_tab hit and miss) with block tiling matches full bank."""
    rng = np.random.default_rng(700 + n_fft)
    nt = 12
    counts = np.full(nt, 257, dtype=np.int64)
    taps = (rng.standard_normal((nt, 257)) / 16.0).astype(np.float32)
    S = 5 * n_fft + 2048
    ser = ((rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2.0)).astype(
        np.complex64
    )
    win = [(512, S - n_fft - 256)]

    bank = TimeDomainFilterBank(
        taps, tap_counts=counts, engine="corr", device="cpu", fft_lengths=(n_fft,)
    )
    full = bank.correlate_series(ser, windows=win)

    # First subset populates corr_fwd_tab; second ascending subset hits corr_fwd_tab.
    sub_a = [0, 1, 2, 3, 4]
    sub_b = [5, 6, 7, 8, 9, 10]
    got_a = bank.correlate_series(ser, windows=win, templates=sub_a)
    got_b = bank.correlate_series(ser, windows=win, templates=sub_b)
    np.testing.assert_allclose(got_a, full[sub_a], rtol=0, atol=1e-6)
    np.testing.assert_allclose(got_b, full[sub_b], rtol=0, atol=1e-6)


def test_corr_bank_layout_avoids_spurious_batch_split():
    """Verify correlation bank layout keeps >32 templates unified on CPU without coarse-band split."""
    rng = np.random.default_rng(42)
    counts = np.linspace(15, 5871, 35, dtype=np.int64)
    taps = np.zeros((len(counts), int(counts.max())), dtype=np.float32)
    for i, c in enumerate(counts):
        taps[i, :c] = rng.standard_normal(int(c)).astype(np.float32) / np.sqrt(float(c))

    cpu_bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="corr", device="cpu")
    seen = np.concatenate([g["template_indices"] for g in cpu_bank.groups])
    assert sorted(seen.tolist()) == list(range(len(counts)))
    # All 35 templates fit in <2 groups (not artificially split at 32 into two same-N groups).
    group_ns = [g["n"] for g in cpu_bank.groups]
    assert len(group_ns) == len(set(group_ns))

    S = 1 << 17
    ser = ((rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2.0)).astype(
        np.complex64
    )
    win = slice(8192, S - 65536)
    cpu_out = cpu_bank.correlate_series(ser, windows=win)

    gpu_bank = _gpu_corr_bank(taps, tap_counts=counts)
    gpu_out = gpu_bank.correlate_series(ser, windows=win)
    scale = max(float(np.abs(cpu_out[:, win]).max()), 1e-6)
    np.testing.assert_allclose(gpu_out[:, win], cpu_out[:, win], rtol=0, atol=1e-5 * scale)
    assert np.all(gpu_out[:, :win.start] == 0)
    assert np.all(gpu_out[:, win.stop:] == 0)


def test_gpu_empty_windows_and_multi_group_shared_zero():
    """Verify GPU-shared outputs zero cleanly on empty windows and across multi-group banks."""
    rng = np.random.default_rng(314)
    counts = np.array([31, 63, 127, 255, 1500, 2200, 2800, 3200], dtype=np.int64)
    taps = np.zeros((len(counts), int(counts.max())), dtype=np.float32)
    for i, c in enumerate(counts):
        taps[i, :c] = rng.standard_normal(int(c)).astype(np.float32) / np.sqrt(float(c))

    gpu_bank = _gpu_corr_bank(taps, tap_counts=counts, fft_lengths=(4096, 8192))
    cpu_bank = TimeDomainFilterBank(
        taps, tap_counts=counts, engine="corr", device="cpu", fft_lengths=(4096, 8192)
    )
    assert len(gpu_bank.groups) == 2

    S = 1 << 16
    ser_host = ((rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2.0)).astype(
        np.complex64
    )
    ser = gpu_bank.empty_shared((S,), np.complex64)
    ser[:] = ser_host
    out = gpu_bank.empty_shared((len(counts), S), np.complex64)

    # Multi-group async correlation + coalesced device zeroing matches CPU.
    win = [(4096, 28000), (34000, S - 8192)]
    out[:] = 9.0 - 4.0j
    gpu_bank.correlate_series(ser, windows=win, out=out, wait=False)
    gpu_bank.wait()
    cpu_ref = cpu_bank.correlate_series(ser_host, windows=win)
    scale = max(float(np.abs(cpu_ref).max()), 1e-6)
    np.testing.assert_allclose(out, cpu_ref, rtol=0, atol=1e-5 * scale)

    # Empty windows with out_support clears previous windows on device without host fault.
    gpu_bank.correlate_series(ser, windows=[], out=out, out_support=win, wait=False)
    gpu_bank.wait()
    assert np.all(out == 0)

    # Empty windows with out_support=None clears the entire shared buffer on device.
    out[:] = -5.0 + 2.0j
    gpu_bank.correlate_series(ser, windows=[], out=out, wait=True)
    assert np.all(out == 0)


def test_multi_isa_agreement_across_tiled_sizes():
    """Verify AVX3, AVX2, AVX, and SSE4 agree on block-tiled continuous correlations."""
    if not os.environ.get("MF_ISA"):
        mf.set_target(None)
    avail = set(mf.targets())
    wanted = [t for t in ("AVX3", "AVX2", "AVX", "SSE4") if t in avail]
    if len(wanted) < 2:
        pytest.skip("fewer than two x86 SIMD targets available")

    code = (
        "import sys, numpy as np, matchedfilter as mf\n"
        "rng = np.random.default_rng(2026)\n"
        "counts = np.array([31, 95, 255, 511, 1023, 2047], dtype=np.int64)\n"
        "taps = rng.standard_normal((6, 2047)).astype(np.float32)\n"
        "S = 163840\n"
        "ser = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)\n"
        "for n in (4096, 8192, 65536):\n"
        "    b = mf.TimeDomainFilterBank(taps, tap_counts=counts, engine='corr', device='cpu', fft_lengths=(n,))\n"
        "    y = b.correlate_series(ser, windows=[(2048, S - 65536)])\n"
        "    sys.stdout.buffer.write(y.tobytes())\n"
    )
    outputs = {}
    for isa in wanted:
        env = dict(os.environ)
        env["MF_ISA"] = isa
        proc = subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            check=True,
            capture_output=True,
        )
        outputs[isa] = np.frombuffer(proc.stdout, dtype=np.complex64)
    base = outputs[wanted[0]]
    scale = max(float(np.abs(base).max()), 1.0)
    for isa in wanted[1:]:
        np.testing.assert_allclose(outputs[isa], base, rtol=0, atol=2e-6 * scale)
