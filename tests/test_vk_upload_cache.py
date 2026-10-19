"""Upload lifetime on a GPU, and the fp16 packing every backend uploads.

What each call writes is pinned on a recording driver (test_gpu_hier_plan, and
test_gpu_flat_results for flat peaks).
"""
import numpy as np
import pytest

from matchedfilter import _gpuhier, _vkcompute


@pytest.mark.parametrize("layout", ["contiguous", "strided", "reversed", "transposed"])
def test_half_packing_preserves_shader_bit_layout(layout):
    """The shader expects real in bits 0..15, imaginary in bits 16..31."""
    values = np.array([0., -0., 1., -1., 2**-24, 65504., 65520.,
                       np.inf, -np.inf, np.nan], np.float32)
    a = np.empty((4, values.size), np.complex64)
    a.real = values
    a.imag = values[::-1]
    if layout == "strided":
        a = a[:, ::2]
    elif layout == "reversed":
        a = a[:, ::-1]
    elif layout == "transposed":
        a = a.T
    with np.errstate(over="ignore", invalid="ignore"):
        expected = (a.real.astype(np.float16).view(np.uint16).astype(np.uint32)
                    | (a.imag.astype(np.float16).view(np.uint16).astype(np.uint32) << 16))
        got = _gpuhier.pack_half2(a)
    np.testing.assert_array_equal(got, expected)
    assert got.shape == a.shape and got.flags.c_contiguous


def vulkan_gpu():
    from conftest import usable_gpu
    import matchedfilter as mf
    device = usable_gpu()
    if device is None or next(d for d in mf.devices() if str(d) == device).backend != "vulkan":
        pytest.skip("requires a Vulkan GPU")
    return device


@pytest.mark.parametrize("changed", ["data", "tmpl"])
def test_revisited_window_matches_float64_on_gpu(changed):
    device = vulkan_gpu()
    c = _vkcompute.Context(int(device.split(":")[1]))
    n = 2048
    rng = np.random.default_rng(57)
    def random_spectra():
        return (rng.normal(size=(2, n)) + 1j * rng.normal(size=(2, n))).astype(np.complex64)
    data, tmpl = random_spectra(), random_spectra()
    def run(window, dirty):
        kw = dict(window=window, binsize=n, upload_data=dirty == "data",
                  upload_tmpl=dirty == "tmpl")
        return c.hier_peaks(n, 1024, data, tmpl, tmpl[:, :1024], 0., **kw)
    try:
        run((0, n), None)
        run((100, n), None)
        (data if changed == "data" else tmpl)[:] = random_spectra()
        run((0, n), changed)
        idx, val = run((100, n), None)
        ref = np.fft.ifft(data.astype(np.complex128)[:, None, :]
                          * tmpl.astype(np.complex128).conj()[None, :, :], axis=-1) * n
        expected = np.abs(ref[:, :, 100:]).argmax(axis=-1) + 100
        np.testing.assert_array_equal(idx[:, :, 0], expected)
        np.testing.assert_allclose(val[:, :, 0],
                                   np.take_along_axis(ref, expected[:, :, None], axis=-1)[:, :, 0],
                                   rtol=1e-5, atol=1e-5)
    finally:
        c.destroy()


def test_public_filter_refreshes_cached_windows_and_subranges():
    import matchedfilter as mf
    device = vulkan_gpu()
    rng = np.random.default_rng(81)
    n = 2048
    cpu = mf.MatchedFilter(n, ndata=2, ntemplates=2)
    gpu = mf.MatchedFilter(n, ndata=2, ntemplates=2, device=device)
    for _ in range(2):
        data = (rng.normal(size=(2, n)) + 1j * rng.normal(size=(2, n))).astype(np.complex64)
        tmpl = (rng.normal(size=(2, n)) + 1j * rng.normal(size=(2, n))).astype(np.complex64)
        for plan in (cpu, gpu):
            plan.set_data(data)
            plan.set_templates(tmpl)
        for window in ((0, n), (100, n), (0, n)):
            for start in (0, 1, 0):
                kw = dict(window=window, binsize=n, data=(start, 1), templates=(start, 1))
                want, got = cpu.run(**kw), gpu.run(**kw)
                np.testing.assert_array_equal(got["index"], want["index"])
                np.testing.assert_allclose(got["value"], want["value"], rtol=1e-5, atol=1e-5)
