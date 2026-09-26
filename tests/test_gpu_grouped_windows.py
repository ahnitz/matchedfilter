"""Mixed-window submissions preserve the block API and bounded storage."""
import numpy as np
import pytest
import matchedfilter as mf
from conftest import usable_gpu


@pytest.mark.parametrize('n', [1024, 2048, 8192])
@pytest.mark.parametrize('binsize', [127, 16384])
@pytest.mark.parametrize('shared', [False, True])
def test_grouped_windows_match_cpu_after_updates_and_eviction(n, binsize, shared):
    device = usable_gpu()
    if not device:
        pytest.skip('no usable GPU')
    gpu = mf.MatchedFilter(n, 2, 5, device=device)
    if not hasattr(gpu._gpu, 'peaks_grouped'):
        pytest.skip('Vulkan grouped submission optimization')
    cpu = mf.MatchedFilter(n, 2, 5, device='cpu')
    rng = np.random.default_rng(n)
    series = (rng.normal(size=3*n) + 1j*rng.normal(size=3*n)).astype('complex64')
    templates = (rng.normal(size=(5,n)) + 1j*rng.normal(size=(5,n))).astype('complex64')
    if shared:
        bank = gpu.empty_shared(templates.shape)
        bank[:] = templates
        templates = bank
    # Repeated and distinct windows, caller order, zero-padded and empty tails.
    starts = np.array([2*n, 0, n//2, 3*n, n, n//3, 2*n+13], dtype=np.uintp)
    low = np.array([9, 0, 23, 9, 0, 37, 23], dtype=np.uintp)
    high = low + n//2
    for turn in range(3):
        series *= np.complex64(0.8 + 0.2j)
        templates *= np.complex64(0.7 - 0.4j)
        for f in (cpu, gpu):
            f.set_templates(templates)
        if turn == 1:
            # Force several bounded batches and cache eviction during execution.
            gpu.set_memory_limits(cache_bytes=1, series_bytes=2*(8*n+4+12*3*16))
        elif turn == 2:
            gpu.set_memory_limits(cache_bytes=512*1024*1024, series_bytes=64*1024*1024)
        kwargs = dict(binsize=binsize, threshold=0.1, templates=(1,3), raw=True)
        want_i, want_v = cpu.run_blocks(series, starts, low, high, **kwargs)
        got_i, got_v = gpu.run_blocks(series, starts, low, high, **kwargs)
        np.testing.assert_array_equal(got_i, want_i)
        np.testing.assert_allclose(got_v, want_v, rtol=3e-5, atol=3e-5)


def test_irregular_windows_share_one_submission(monkeypatch):
    device = usable_gpu()
    if not device:
        pytest.skip('no usable GPU')
    f = mf.MatchedFilter(1024, 1, 3, device=device)
    if not hasattr(f._gpu, 'peaks_grouped'):
        pytest.skip('Vulkan grouped submission optimization')
    rng = np.random.default_rng(123)
    f.set_templates((rng.normal(size=(3,1024))+1j*rng.normal(size=(3,1024))).astype('complex64'))
    series = (rng.normal(size=4096)+1j*rng.normal(size=4096)).astype('complex64')
    starts = np.arange(16, dtype=np.uintp)*128
    low = np.arange(16, dtype=np.uintp)
    f.run_blocks(series, starts, low, low+512)
    calls = []
    original = f._gpu._submit
    def submit(cmd):
        calls.append(cmd)
        return original(cmd)
    monkeypatch.setattr(f._gpu, '_submit', submit)
    grouped = f.run_blocks(series, starts, low, low+512).copy()
    assert len(calls) == 1
    # A template bank larger than the dispatch limit still uses template tiling.
    monkeypatch.setattr(f._gpu, 'max_dispatch_x', 2)
    tiled = f.run_blocks(series, starts, low, low+512)
    np.testing.assert_array_equal(tiled['index'], grouped['index'])
    np.testing.assert_allclose(tiled['value'], grouped['value'], rtol=3e-5, atol=3e-5)
