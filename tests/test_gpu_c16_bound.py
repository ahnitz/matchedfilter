"""The Vulkan fp16 coarse tier reports an UPPER BOUND on each pair's exact coarse maximum.

B = |c16|(1+3u) + kappa_B u rms(y) (tierb.slang c16Bound; kappa from tools/coarse_layout.py).
The gate must never reject a pair whose exact maximum reaches the threshold, so B must sit
at or above the float64 maximum for every pair -- and the bound must not be wasteful: the
fp16 error may use at most half of its margin (margin use < 0.5, the criterion of
tools/gate_margin.py). Families and seed differ from the ones sigma_B was measured on.
"""
import numpy as np
import pytest

u = 2.0 ** -11


def _families(B, rng, nt):
    from matchedfilter.benchmark import _inspiral_power
    white = lambda *s: (rng.standard_normal(s) + 1j * rng.standard_normal(s))
    shape = np.sqrt(_inspiral_power(8 * B)[:B]); shape /= shape.max()
    T = white(nt, B) * shape
    out = [white(1, B), white(1, B) * shape]
    lag = int(rng.integers(0, B))
    out.append(white(1, B) * shape + 12.0 * T[0] * np.exp(-2j * np.pi * lag * np.arange(B) / B))
    burst = np.zeros(B, complex); t0 = int(rng.integers(0, B - 8))
    burst[t0:t0 + 8] = 200.0 * np.exp(1j * np.linspace(0, 6, 8))
    out.append(white(1, B) + np.fft.fft(burst)[None])
    return [(D, T) for D in out]


def _coarse(ctx, n, B, D, T):
    nt = T.shape[0]
    data = np.zeros((1, n), np.complex64); data[:, :B] = D
    tmpl = np.zeros((nt, n), np.complex64); tmpl[:, :B] = T
    ctx.hier_peaks(n, B, data, tmpl, np.ascontiguousarray(tmpl[:, :B]), 1e30,
                   binsize=n, threshold=0.0)
    return np.abs(ctx._last_dispatch[0]["cval"].read(np.complex64, nt).astype(np.complex128))


@pytest.mark.parametrize("B", [64, 256, 1024, 2048])
def test_bound_covers_the_exact_maximum(B, monkeypatch):
    from conftest import vulkan_runs
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)
    from matchedfilter import _vkcompute
    n, nt = 4096, 128
    rng = np.random.default_rng(1234 + B)
    cases = _families(B, rng, nt)
    raws, bnds = [], []
    for flag, out in (("0", raws), ("1", bnds)):
        monkeypatch.setenv("MF_VK_C16_BOUND", flag)
        ctx = _vkcompute.Context(0)
        try:
            for D, T in cases:
                # Scale each template so every pair's exact maximum is 8 (well inside fp16).
                y = np.fft.ifft(D * np.conj(T), axis=1) * B
                T = (T * (8.0 / np.abs(y).max(axis=1))[:, None]).astype(np.complex64)
                out.append((_coarse(ctx, n, B, D.astype(np.complex64), T),
                            np.abs(np.fft.ifft(D.astype(np.complex128) * np.conj(T.astype(np.complex128)),
                                               axis=1) * B).max(axis=1)))
        finally:
            ctx.destroy()
    for (raw, exact), (bnd, _) in zip(raws, bnds):
        assert (bnd >= exact).all(), "bound below the exact maximum: %r" % ((bnd - exact).min(),)
        use = (exact - raw) / (bnd - raw)
        assert use.max() < 0.5, "margin use %.3f" % use.max()
