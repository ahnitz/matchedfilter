"""Correctness checks for the experimental full-output kernels.

This is intentionally an internal prototype; there is no public output-mode
choice until the performance tradeoff is accepted.
"""
import numpy as np
import pytest

from matchedfilter import _core
from conftest import usable_gpu


def banks(n):
    rng = np.random.default_rng(4029)
    data = (rng.standard_normal((3, n)) + 1j*rng.standard_normal((3, n))).astype(np.complex64)
    tmpl = (rng.standard_normal((4, n)) + 1j*rng.standard_normal((4, n))).astype(np.complex64)
    return data, tmpl


def reference(data, tmpl):
    n = data.shape[-1]
    return (np.fft.ifft(data[:, None, :] * tmpl[None, :, :].conj(), axis=-1) * n).astype(np.complex64)


@pytest.mark.parametrize('n', [2048, 4096, 8192])
def test_cpu_full_output_and_subrange(n):
    data, tmpl = banks(n)
    f = _core.MF(n, 3, 4)
    for i, row in enumerate(data):
        f.set_data(i, row)
    for i, row in enumerate(tmpl):
        f.set_template(i, row)
    actual = np.empty((2, 2, n), np.complex64)
    f.correlate(1, 2, 1, 2, actual)
    expected = reference(data[1:], tmpl[1:3])
    assert np.max(np.abs(actual-expected)) / np.max(np.abs(expected)) < 3e-6


@pytest.mark.parametrize('n', [2048, 4096, 8192])
def test_vulkan_full_output(n):
    dev = usable_gpu()
    if dev is None:
        pytest.skip('no usable Vulkan GPU')
    from matchedfilter.device import parse
    parsed = parse(dev)
    if parsed.backend != 'vulkan':
        pytest.skip('no usable Vulkan GPU')
    from matchedfilter._vkcompute import Context
    data, tmpl = banks(n)
    ctx = Context(parsed.index)
    try:
        actual = ctx._full_probe(n, data, tmpl)
        expected = reference(data, tmpl)
        assert np.max(np.abs(actual-expected)) / np.max(np.abs(expected)) < 3e-6
    finally:
        ctx.destroy()
