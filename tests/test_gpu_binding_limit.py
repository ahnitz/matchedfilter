"""Work whose output one GPU binding cannot span is split, and every element is still
written. A Vulkan storage binding spans at most maxStorageBufferRange bytes (under 4 GiB);
RADV wrote nothing at all for a 4.29 GB full correlation (512 x 512 x 4096), and the call
returned normally. The limit is lowered here so the split runs at test sizes: on Vulkan the
descriptor ranges are clamped to it too, so a tile reaching past its binding would read or
write outside it."""
import numpy as np
import pytest
from conftest import usable_gpu_reason

import matchedfilter as mf


def _gpu():
    from conftest import usable_gpu
    dev = usable_gpu()
    if dev is None:
        pytest.skip(usable_gpu_reason())
    return dev


@pytest.mark.parametrize("shared", [True, False])
def test_full_correlation_past_the_binding_limit_writes_every_pair(monkeypatch, shared):
    n, nd, nt = 1024, 7, 5
    rng = np.random.default_rng(4)
    d = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    f = mf.CorrelationFilter(n, nd, nt, device=_gpu())
    f.set_data(d)
    f.set_templates(h)
    # Two data rows' output per binding: runs of 2, 2, 2 and 1 rows.
    monkeypatch.setattr(f._gpu, "max_binding_bytes", 2 * nt * n * 8, raising=False)
    out = f.empty_shared((nd, nt, n)) if shared else np.zeros((nd, nt, n), np.complex64)
    out[...] = 0
    got = np.asarray(f.run(out=out))
    want = np.fft.ifft(d[:, None].astype(np.complex128) * h[None].conj(), axis=-1) * n
    assert np.abs(got - want).max() <= 1e-5 * np.abs(want).max()


def test_full_correlation_splits_templates_when_one_row_is_past_the_limit(monkeypatch):
    n, nd, nt = 1024, 3, 6
    rng = np.random.default_rng(5)
    d = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    f = mf.CorrelationFilter(n, nd, nt, device=_gpu())
    f.set_data(d)
    f.set_templates(h)
    monkeypatch.setattr(f._gpu, "max_binding_bytes", 4 * n * 8, raising=False)  # 4 templates
    out = f.empty_shared((nd, nt, n))
    out[...] = 0
    got = np.asarray(f.run(out=out))
    want = np.fft.ifft(d[:, None].astype(np.complex128) * h[None].conj(), axis=-1) * n
    assert np.abs(got - want).max() <= 1e-5 * np.abs(want).max()


def test_continuous_correlation_past_the_binding_limit_matches_the_unsplit_call(monkeypatch):
    n, nt, L = 1024, 6, 1 << 14
    rng = np.random.default_rng(6)
    taps = (rng.standard_normal((nt, n // 4)) + 1j * rng.standard_normal((nt, n // 4)))
    h = np.zeros((nt, n), np.complex64)
    h[:, :n // 4] = taps
    spec = np.fft.fft(h, axis=1).astype(np.complex64)
    ser = (rng.standard_normal(L) + 1j * rng.standard_normal(L)).astype(np.complex64)
    f = mf.CorrelationFilter(n, ndata=1, ntemplates=nt, valid=(n // 8, n - n // 8), device=_gpu())
    f.set_templates(spec)
    whole = np.asarray(f.run_series(ser)).copy()
    monkeypatch.setattr(f._gpu, "max_binding_bytes", 2 * L * 8, raising=False)  # 2 templates
    split = np.asarray(f.run_series(ser))
    assert np.abs(whole).max() > 0
    np.testing.assert_allclose(split, whole, rtol=0, atol=1e-6 * np.abs(whole).max())
