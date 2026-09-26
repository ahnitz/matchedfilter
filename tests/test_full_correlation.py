"""Public full-correlation contract, checked against an independent FFT."""
import numpy as np
import pytest

from matchedfilter import CorrelationFilter, MatchedFilter
from conftest import usable_gpu


SIZES = [1 << k for k in range(10, 23)]


def _device(name):
    if name == 'cpu':
        return 'cpu'
    device = usable_gpu()
    if device is None:
        pytest.skip('no usable GPU')
    return device


def _spectra(shape, seed):
    rng = np.random.default_rng(seed)
    return (rng.standard_normal(shape) + 1j*rng.standard_normal(shape)).astype(np.complex64)


def _reference(data, tmpl):
    n = data.shape[-1]
    return (np.fft.ifft(data[:, None] * tmpl[None].conj(), axis=-1) * n).astype(np.complex64)


def _agrees(actual, expected, tol=1e-5):
    scale = max(float(np.max(np.abs(expected))), 1)
    assert np.max(np.abs(actual - expected)) / scale < tol


def _full_tol(f):
    # The 65536-point Metal kernel holds 64 samples per thread and builds
    # twiddles by fp32 recurrence. Its full-output and series paths reach
    # about 1.0e-5 and 1.6e-5 maximum error against NumPy on Apple silicon.
    # Keep the tighter bound for every other length and backend.
    return 3e-5 if f.n == 65536 and f.device.backend == 'metal' else 1e-5


@pytest.mark.parametrize('device', ['cpu', 'gpu'])
@pytest.mark.parametrize('n', SIZES)
def test_every_supported_length(n, device):
    data = _spectra((1, n), 510 + n)
    tmpl = _spectra((1, n), 720 + n)
    f = CorrelationFilter(n, device=_device(device))
    f.set_data(data)
    f.set_templates(tmpl)
    _agrees(f.run(), _reference(data, tmpl), tol=_full_tol(f))


@pytest.mark.parametrize('device', ['cpu', 'gpu'])
def test_banks_selectors_output_ownership_and_peak_parity(device):
    n = 2048
    data, tmpl = _spectra((3, n), 11), _spectra((5, n), 12)
    f = CorrelationFilter(n, 3, 5, device=_device(device))
    p = MatchedFilter(n, 3, 5, device=f.device)
    for obj in (f, p):
        obj.set_data(data)
        obj.set_templates(tmpl)
    expected = _reference(data, tmpl)
    full = f.run()
    _agrees(full, expected)
    out = np.full((2, 3, n), np.nan, np.complex64)
    assert f.run(data=(1, 2), templates=(1, 3), out=out) is out
    _agrees(out, expected[1:3, 1:4])
    peaks = p.run(binsize=n)
    for d in range(3):
        for t in range(5):
            k = peaks['index'][d, t, 0]
            _agrees(np.array([peaks['value'][d, t, 0]]),
                    np.array([expected[d, t, k]]))
    full[0, 0, 0] = np.nan
    assert np.isfinite(f.run()[0, 0, 0])


@pytest.mark.parametrize('device', ['cpu', 'gpu'])
def test_series_padding_phase_and_batch_boundary(device):
    n = 1024
    series = _spectra((n + 29,), 91)
    tmpl = _spectra((3, n), 92)
    starts = np.array([0, 13, n - 3, n + 5, n + 29], np.intp)
    f = CorrelationFilter(n, ndata=2, ntemplates=3, device=_device(device))
    f.set_templates(tmpl)
    got = f.run_series(series, starts)
    blocks = np.zeros((len(starts), n), np.complex64)
    for j, start in enumerate(starts):
        length = min(n, max(0, series.size - start))
        blocks[j, :length] = series[start:start + length]
    expected = _reference(np.fft.fft(blocks, axis=-1).astype(np.complex64) / n, tmpl)
    _agrees(got, expected)
    assert f.run_series(series, starts[:1], templates=(1, 2)).shape == (1, 2, n)
    with pytest.raises(ValueError):
        f.run()


@pytest.mark.parametrize('device', ['cpu', 'gpu'])
def test_lag_order_scale_complex_conjugation(device):
    n = 1024
    data = ((2 + 3j) * np.exp(-2j * np.pi * np.arange(n) / n)).astype(np.complex64)[None]
    tmpl = np.full((1, n), 4 - 1j, np.complex64)
    f = CorrelationFilter(n, device=_device(device))
    f.set_data(data)
    f.set_templates(tmpl)
    got = f.run()[0, 0]
    expected = np.zeros(n, np.complex64)
    expected[1] = n * (2 + 3j) * (4 + 1j)
    _agrees(got, expected)


def test_out_validation_guard_and_memmap(tmp_path):
    n = 1024
    f = CorrelationFilter(n, 2, 2)
    zeros = np.zeros((2, n), np.complex64)
    f.set_data(zeros)
    f.set_templates(zeros)
    for invalid in (np.empty((2, 2, n), np.complex128),
                    np.empty((2, 1, n), np.complex64),
                    np.empty((2, 2, n + 1), np.complex64)[..., :n]):
        with pytest.raises(ValueError, match='out'):
            f.run(out=invalid)
    readonly = np.empty((2, 2, n), np.complex64)
    readonly.flags.writeable = False
    with pytest.raises(ValueError, match='out'):
        f.run(out=readonly)
    path = tmp_path / 'out.dat'
    mapped = np.memmap(path, mode='w+', dtype=np.complex64, shape=(2, 2, n))
    assert f.run(out=mapped) is mapped
    assert np.all(mapped == 0)
    f._max_auto_output_bytes = 1
    with pytest.raises(ValueError, match='pass a preallocated out'):
        f.run()
    assert f.run(out=mapped) is mapped


def test_forced_cpu_pair_batch(monkeypatch):
    monkeypatch.setenv('MF_PBMAX', '1024')
    n = 1024
    data, tmpl = _spectra((2, n), 82), _spectra((5, n), 83)
    f = CorrelationFilter(n, 2, 5)
    f.set_data(data)
    f.set_templates(tmpl)
    _agrees(f.run(templates=(1, 4)), _reference(data, tmpl[1:5]))
    series = _spectra((n + 4,), 84)
    got = f.run_series(series, [4], templates=(1, 4))
    block = np.fft.fft(series[4:][None], axis=-1).astype(np.complex64) / n
    _agrees(got, _reference(block, tmpl[1:5]))


def test_cpu_non_group_major_fallback(monkeypatch):
    monkeypatch.setenv('MF_GMAJOR', '0')
    n = 4096
    data, tmpl = _spectra((2, n), 85), _spectra((3, n), 86)
    f = CorrelationFilter(n, 2, 3)
    f.set_data(data)
    f.set_templates(tmpl)
    _agrees(f.run(), _reference(data, tmpl))


def test_gpu_shared_output_and_changed_banks():
    device = _device('gpu')
    n = 4096
    data, tmpl = _spectra((2, n), 93), _spectra((3, n), 94)
    f = CorrelationFilter(n, 2, 3, device=device)
    f.set_data(data)
    f.set_templates(tmpl)
    out = f.empty_shared((2, 3, n))
    assert f.run(out=out) is out
    _agrees(out, _reference(data, tmpl))
    tmpl *= 1j
    f.set_templates(tmpl)
    _agrees(f.run(out=out), _reference(data, tmpl))
    f.clear_cache()
    _agrees(f.run(out=out), _reference(data, tmpl))
    readback = f.empty_shared((2, 3, n), readback=True)
    assert f.run(out=readback) is readback
    _agrees(readback, _reference(data, tmpl))


def test_gpu_memmap_output(tmp_path):
    device = _device('gpu')
    n = 1024
    data, tmpl = _spectra((2, n), 98), _spectra((3, n), 99)
    f = CorrelationFilter(n, 2, 3, device=device)
    f.set_data(data)
    f.set_templates(tmpl)
    out = np.memmap(tmp_path / 'gpu-full.dat', mode='w+',
                    dtype=np.complex64, shape=(2, 3, n))
    assert f.run(out=out) is out
    _agrees(out, _reference(data, tmpl))


def test_gpu_shared_output_is_one_dispatch_past_staging_budget(monkeypatch):
    device = _device('gpu')
    from matchedfilter.device import parse
    parsed = parse(device)
    backend = (__import__('matchedfilter._mtlcompute', fromlist=['Context'])
               if parsed.backend == 'metal' else
               __import__('matchedfilter._vkcompute', fromlist=['Context']))
    ctx = backend.Context(parsed.index)
    try:
        n, nt = 4096, 2049  # just above the 64 MiB host staging budget
        data = np.empty((1, n), np.complex64)
        tmpl = np.empty((nt, n), np.complex64)
        out = ctx.empty_shared((1, nt, n))
        calls = []
        monkeypatch.setattr(ctx, '_full_tile', lambda *args: calls.append(args))
        ctx.correlate(n, data, tmpl, out)
        assert len(calls) == 1
        assert calls[0][1].shape == data.shape
        assert calls[0][2].shape == tmpl.shape
    finally:
        ctx.destroy()


@pytest.mark.parametrize('n', [65536, 131072, 1 << 22])
def test_gpu_series_across_two_stage_boundary(n):
    device = _device('gpu')
    series = _spectra((n + 7,), 96)
    tmpl = _spectra((1, n), 97)
    f = CorrelationFilter(n, ntemplates=1, device=device)
    f.set_templates(tmpl)
    got = f.run_series(series, [7])
    block = np.zeros((1, n), np.complex64)
    block[0, :n] = series[7:]
    expected = _reference(np.fft.fft(block, axis=-1).astype(np.complex64) / n, tmpl)
    _agrees(got, expected, tol=_full_tol(f))
