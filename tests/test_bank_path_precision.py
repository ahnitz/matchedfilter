"""The SNR the bank path reports, against a float64 direct correlation at the reported lag.

The other precision checks compare one engine with another (direct refine with the
transform, the GPU with the CPU, the hierarchical filter with the flat one), so a change
both sides share -- a float16 refine, a dropped tap, a misplaced centre -- passes them.
This compares every reported peak with sum_j conj(tap_j) x[lag + j - c] in float64, c the
centre tap (template_spectra's convention), on the inspiral-shaped series of
test_direct_refine: through the gate chains, with the direct refine and with the
transform, on the flat filter, and on a usable GPU.

The bound: |SNR| is a sum of up to ~400 float32 products and a float32 transform of n =
2048, so its relative rounding is a few times 1e-7 (the observed worst case is 8e-7). 1e-5
sits well above that and far below a float16 result (~1e-3).
"""
import numpy as np
import pytest

import matchedfilter as mf
from conftest import usable_gpu, usable_gpu_reason
from test_direct_refine import _bank

RTOL = 1e-5


def _reference(series, taps, counts, t, pos):
    c, L = int(counts[t]) // 2, int(counts[t])
    x = series[pos - c: pos - c + L].astype(np.complex128)
    return np.sum(np.conj(taps[t, :L].astype(np.float64)) * x)


def _check(idx, val, data, least=20):
    n, taps, counts, spec, series, layout, ref, window = data
    starts = layout[0]
    found = np.argwhere(idx >= 0)
    assert len(found) >= least, "the bank must report peaks: %d" % len(found)
    worst = 0.0
    for b, t, k in found:
        pos = int(starts[b]) + int(idx[b, t, k])          # block-local lag, in series samples
        z = _reference(series, taps, counts, t, pos)
        worst = max(worst, abs(abs(complex(val[b, t, k])) - abs(z)) / abs(z))
    assert worst < RTOL, "worst |SNR| relative error %.2e over %d peaks" % (worst, len(found))


def _hier(data, chain, direct, device, monkeypatch):
    n, taps, counts, spec, series, layout, ref, window = data
    monkeypatch.setenv("MF_DIRECT_REFINE", "1" if direct else "0")
    hf = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-3, chain=chain,
                               device=device, search_window=window)
    hf.set_reference(ref)
    hf.set_templates(spec)
    hf.set_taps(taps, counts)
    idx, val = hf.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)
    return idx.copy(), val.copy()


@pytest.mark.parametrize("chain", [(512,), (256, 512), (128, 256, 512)])
@pytest.mark.parametrize("direct", [True, False], ids=["direct", "transform"])
def test_hierarchical_peaks_are_the_float64_correlation(chain, direct, monkeypatch):
    data = _bank()
    _check(*_hier(data, chain, direct, None, monkeypatch), data)


def test_flat_peaks_are_the_float64_correlation():
    data = _bank()
    n, taps, counts, spec, series, layout, ref, window = data
    f = mf.MatchedFilter(n, 1, spec.shape[0])
    f.set_templates(spec)
    idx, val = f.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)
    _check(idx.copy(), val.copy(), data)


def test_gpu_hierarchical_peaks_are_the_float64_correlation(monkeypatch):
    device = usable_gpu()
    if device is None:
        pytest.skip(usable_gpu_reason())
    data = _bank()
    _check(*_hier(data, (256, 512), False, device, monkeypatch), data)
