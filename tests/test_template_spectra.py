"""template_spectra: a bank's filters on one block length without building the bank."""
import numpy as np
import pytest

import matchedfilter as mf


def _taps(rng, counts):
    taps = np.zeros((len(counts), int(max(counts))), dtype=np.float32)
    for i, c in enumerate(counts):
        taps[i, :c] = rng.standard_normal(c)
    return taps


@pytest.mark.parametrize("tap_rate,data_rate", [(2048, 2048), (4096, 2048), (1024, 2048)])
def test_matches_bank_filters(tap_rate, data_rate):
    rng = np.random.default_rng(1)
    counts = np.array([251, 351, 97, 2001, 640])
    taps = _taps(rng, counts)
    n = 4096
    bank = mf.TimeDomainFilterBank(taps, counts, tap_sample_rate=tap_rate,
                                   data_sample_rate=data_rate, engine='matchedfilter',
                                   fft_lengths=[n])
    filters, valid = mf.template_spectra(taps, counts, n, tap_sample_rate=tap_rate,
                                         data_sample_rate=data_rate)
    for i in range(len(counts)):
        np.testing.assert_array_equal(filters[i], bank.filters_f[i])
    # Each template's own range holds its group's (the group's is set by its longest filter).
    for g in bank.groups:
        for i in g['template_indices']:
            assert valid[i, 0] <= g['c_bad']
            assert valid[i, 1] >= g['c_bad'] + g['n_valid']
    # The longest filter's range is its group's exactly.
    i = int(np.argmax(counts))
    g = next(g for g in bank.groups if i in g['template_indices'])
    assert tuple(valid[i]) == (g['c_bad'], g['c_bad'] + g['n_valid'])


def test_writes_into_out():
    rng = np.random.default_rng(2)
    counts = np.array([100, 300, 200])
    taps = _taps(rng, counts)
    pool = np.empty((8, 2048), dtype=np.complex64)
    out = pool[:3]
    filters, _ = mf.template_spectra(taps, counts, 2048, out=out)
    assert filters is out
    ref, _ = mf.template_spectra(taps, counts, 2048)
    np.testing.assert_array_equal(out, ref)


def test_rejects_bad_out_and_short_block():
    taps = np.ones((2, 600), dtype=np.float32)
    with pytest.raises(ValueError):
        mf.template_spectra(taps, [600, 600], 512)
    with pytest.raises(ValueError):
        mf.template_spectra(taps, [600, 600], 2048, out=np.empty((2, 2048), np.complex128))
    with pytest.raises(ValueError):
        mf.template_spectra(taps, [600, 600], 2048, out=np.empty((2, 4096), np.complex64)[:, ::2])
