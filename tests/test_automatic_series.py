"""Automatic overlap-save layout and continuous full-correlation output."""
import numpy as np
import pytest

from matchedfilter import CorrelationFilter, HierarchicalFilter, MatchedFilter
from conftest import usable_gpu


def _spectra(shape, seed):
    rng = np.random.default_rng(seed)
    return (rng.standard_normal(shape) + 1j * rng.standard_normal(shape)).astype(np.complex64)


class _DLPackOnly:
    def __init__(self, array):
        self.array = array

    def __dlpack_device__(self):
        return self.array.__dlpack_device__()

    def __dlpack__(self, *args, **kwargs):
        return self.array.__dlpack__(*args, **kwargs)


@pytest.mark.parametrize('n,valid,length', [
    (1024, (31, 793), 2403),
    (32768, (4000, 28768), 80001),
    (65536, (4000, 61536), 80001),
    (131072, (4000, 127072), 141072),
])
@pytest.mark.parametrize('selected', [None, (1, 2)])
@pytest.mark.parametrize('device', ['cpu', 'gpu'])
def test_continuous_matches_block_output_and_preserves_gaps(n, valid, length, selected, device):
    if device == 'gpu':
        device = usable_gpu()
        if device is None:
            pytest.skip('no usable GPU')
    series = _spectra((length,), 11)
    templates = _spectra((3, n), 12)
    f = CorrelationFilter(n, ndata=3, ntemplates=3, device=device, valid=valid)
    f.set_templates(templates)
    lo, hi = valid
    starts = np.arange(0, length - lo, hi - lo, dtype=np.uintp)
    blocks = f.run_series(series, starts, templates=selected)
    nt = 3 if selected is None else selected[1]
    expected = np.zeros((nt, length), np.complex64)
    for b, start in enumerate(starts):
        end = min(hi, length - int(start))
        expected[:, int(start) + lo:int(start) + end] = blocks[b, :, lo:end]
    out = f.run_series(series, templates=selected)
    np.testing.assert_allclose(out, expected, rtol=1e-5, atol=1e-5)
    out[:, :lo] = 7 + 9j
    expected[:, :lo] = 7 + 9j
    # The next segment must overwrite every valid sample without clearing the
    # caller's invalid edge or leaking a cached data spectrum.
    changed = 1j * series
    second = f.run_series(changed, starts, templates=selected)
    for b, start in enumerate(starts):
        end = min(hi, length - int(start))
        expected[:, int(start) + lo:int(start) + end] = second[b, :, lo:end]
    assert f.run_series(changed, templates=selected) is out
    np.testing.assert_allclose(out, expected, rtol=1e-5, atol=1e-5)
    assert out.shape == (nt, length)
    if f.device.kind == 'gpu':
        from matchedfilter._shared import shared_buffer
        assert shared_buffer(out, f._gpu) is not None
        f.clear_cache()
        assert f.run_series(changed, templates=selected) is out
        np.testing.assert_allclose(out, expected, rtol=1e-5, atol=1e-5)


@pytest.mark.parametrize('klass', [MatchedFilter, HierarchicalFilter])
def test_peak_filters_derive_same_blocks_and_pad_last_bins(klass):
    n, valid, length = 1024, (100, 700), 2100
    series = _spectra((length,), 20)
    tmpl = _spectra((2, n), 21)
    kwargs = {'band': 128} if klass is HierarchicalFilter else {}
    f = klass(n, ndata=3, ntemplates=2, valid=valid, **kwargs)
    if klass is HierarchicalFilter:
        f.set_coarse_threshold(0)
    f.set_templates(tmpl)
    got = f.run_series(series, binsize=256, raw=True)
    structured = f.run_series(series, binsize=256)
    np.testing.assert_array_equal(structured['index'], got[0])
    np.testing.assert_allclose(structured['value'], got[1])
    starts = [0, 600, 1200, 1800]
    for b, start in enumerate(starts):
        end = min(700, length - start)
        one = f.run_series(series, [start], [100], [end], binsize=256, raw=True)
        nb = one[0].shape[-1]
        expected_index = np.where(one[0][0] >= 0, one[0][0] + start, -1)
        np.testing.assert_array_equal(got[0][b, :, :nb], expected_index)
        np.testing.assert_allclose(got[1][b, :, :nb], one[1][0])
        assert np.all(got[0][b, :, nb:] == -1)
        assert np.all(got[1][b, :, nb:] == 0)


def test_automatic_series_validation():
    n = 1024
    for valid in ((-1, 10), (1, 1), (0, n + 1), (0.5, 700),
                  (0, 700.9), ('0', 700)):
        with pytest.raises(ValueError, match='valid'):
            CorrelationFilter(n, valid=valid)
    f = CorrelationFilter(n, valid=(50, 700))
    f.set_templates(np.ones((1, n), np.complex64))
    series = np.ones(1700, np.complex64)
    with pytest.raises(ValueError, match='owns its output'):
        f.run_series(series, out=np.empty((1, 1700), np.complex128))
    with pytest.raises(ValueError, match='valid'):
        CorrelationFilter(n).run_series(series)


@pytest.mark.parametrize('device', ['cpu', 'gpu'])
def test_continuous_output_against_independent_fft(device):
    if device == 'gpu':
        device = usable_gpu()
        if device is None:
            pytest.skip('no usable GPU')
    n, valid, length = 2048, (173, 1729), 4321
    series = _spectra((length,), 171)
    templates = _spectra((2, n), 172)
    f = CorrelationFilter(n, ntemplates=2, device=device, valid=valid)
    f.set_templates(templates)
    actual = f.run_series(series)
    expected = np.zeros((2, length), np.complex64)
    lo, hi = valid
    for start in range(0, length - lo, hi - lo):
        block = np.zeros(n, np.complex64)
        count = min(n, length - start)
        block[:count] = series[start:start + count]
        spectrum = np.fft.fft(block)
        corr = np.fft.ifft(spectrum[None] * templates.conj(), axis=-1)
        end = min(hi, length - start)
        expected[:, start + lo:start + end] = corr[:, lo:end]
    scale = max(float(np.max(np.abs(expected))), 1.0)
    assert float(np.max(np.abs(actual - expected))) / scale < 1e-5


def test_automatic_layout_accepts_host_dlpack_without_len():
    n = 1024
    series = _spectra((1733,), 38)
    tmpl = _spectra((1, n), 39)
    for cls in (MatchedFilter, CorrelationFilter):
        f = cls(n, valid=(50, 750))
        f.set_templates(tmpl)
        expected = f.run_series(series).copy()
        result = f.run_series(_DLPackOnly(series))
        np.testing.assert_array_equal(result, expected)


def test_continuous_forced_pair_batch_and_fir_bank(monkeypatch):
    monkeypatch.setenv('MF_PBMAX', '1024')
    n, length, valid = 1024, 2813, (61, 819)
    rng = np.random.default_rng(44)
    series = _spectra((length,), 45)
    taps = rng.standard_normal((6, 401)).astype(np.float32)
    padded = np.zeros((6, n), np.float32)
    padded[:, :401] = taps
    templates = np.fft.fft(padded, axis=-1).astype(np.complex64)
    f = CorrelationFilter(n, ndata=4, ntemplates=6, valid=valid)
    f.set_templates(templates)
    starts = np.arange(0, length - valid[0], valid[1] - valid[0], dtype=np.uintp)
    blocks = f.run_series(series, starts)
    expected = np.zeros((6, length), np.complex64)
    for b, start in enumerate(starts):
        end = min(valid[1], length - int(start))
        expected[:, int(start) + valid[0]:int(start) + end] = blocks[b, :, valid[0]:end]
    out = f.run_series(series)
    np.testing.assert_allclose(out[:, valid[0]:], expected[:, valid[0]:],
                               rtol=1e-5, atol=1e-5)
    assert np.all(out[:, :valid[0]] == 0)


def test_six_real_fir_spectra_at_the_43_block_boundary():
    n, length, lo, hi = 32768, 1048576, 4000, 28768
    starts = np.arange(0, length - lo, hi - lo, dtype=np.uintp)
    assert starts.size == 43
    rng = np.random.default_rng(90)
    series = (rng.standard_normal(length) + 1j * rng.standard_normal(length)).astype(np.complex64)
    taps = rng.standard_normal((6, 8001)).astype(np.float32)
    centered = np.zeros((6, n), np.float32)
    centered[:, (np.arange(8001) - 4000) % n] = taps
    templates = np.fft.fft(centered, axis=-1).astype(np.complex64)
    f = CorrelationFilter(n, ndata=43, ntemplates=6, valid=(lo, hi))
    f.set_templates(templates)
    blocks = f.run_series(series, starts)
    continuous = f.run_series(series)
    assert np.all(continuous[:, :lo] == 0)
    for b, start in enumerate(starts):
        end = min(hi, length - int(start))
        np.testing.assert_allclose(
            continuous[:, int(start) + lo:int(start) + end],
            blocks[b, :, lo:end], rtol=1e-5, atol=1e-5)
    assert int(starts[-1]) + hi > length  # the final block was clipped
