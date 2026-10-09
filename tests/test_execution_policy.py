"""Measured policy selection is shared; capability and memory bounds still win."""
import json
from types import SimpleNamespace

import numpy as np
import pytest
import matchedfilter as mf
from matchedfilter.device import Device
from matchedfilter._execution_policy import select


def row():
    return dict(id='test', kind='cpu', device='test-cpu', backend='AVX2',
                operation='hierarchical_series', n=4096, band=1024,
                templates_min=32, templates_max=64, series_group=4,
                evidence='unit test')


def install(tmp_path, monkeypatch, rows):
    path = tmp_path / 'policy.json'
    path.write_text(json.dumps(dict(version=1, rules=rows)))
    monkeypatch.setenv('MF_EXECUTION_POLICY', str(path))


def test_cpu_policy_exact_coverage_and_default(tmp_path, monkeypatch):
    install(tmp_path, monkeypatch, [row()])
    d = Device('cpu', 0, 'model', 'AVX2', arch=('test-cpu',))
    for nt in (32, 37, 64):
        assert select(d, 'hierarchical_series', 4096, 1024, nt)['series_group'] == 4
    for n, band, nt in ((4096, 1024, 31), (4096, 1024, 65), (8192, 1024, 64), (4096, 512, 64)):
        assert select(d, 'hierarchical_series', n, band, nt) == {}
    assert select(Device('cpu', 0, 'model', 'SSE4', arch=('test-cpu',)),
                  'hierarchical_series', 4096, 1024, 64) == {}


def test_cpu_identity_keys_are_metadata_not_architecture_special_cases(monkeypatch):
    import io
    import matchedfilter.device as device
    monkeypatch.setattr(device, 'open', lambda path: io.StringIO(
        'processor : 0\nvendor_id : GenuineIntel\ncpu family : 6\n'
        'model : 63\nmodel name : example processor\n\n'), raising=False)
    monkeypatch.setattr(device, '_CPU_DEVICES', {})       # the device is cached per backend
    d = device._cpu_device()
    assert d.name == 'example processor'
    assert d.arch == ('genuineintel-family6-model63',)


def test_exact_device_precedes_family(tmp_path, monkeypatch):
    broad = row()
    exact = dict(broad, id='exact', device='model', series_group=2)
    install(tmp_path, monkeypatch, [broad, exact])
    d = Device('cpu', 0, 'model', 'AVX2', arch=('test-cpu',))
    assert select(d, 'hierarchical_series', 4096, 1024, 64)['id'] == 'exact'


@pytest.mark.parametrize('change', [dict(series_group=0), dict(series_group=True),
                                   dict(series_group=65536), dict(templates_min=65),
                                   dict(coarse_threshold=3), dict(n='4096')])
def test_invalid_policy_is_not_silently_used(tmp_path, monkeypatch, change):
    install(tmp_path, monkeypatch, [dict(row(), **change)])
    with pytest.raises(ValueError):
        select(Device('cpu', 0, 'test-cpu', 'AVX2'), 'hierarchical_series', 4096, 1024, 64)


def test_overlapping_policy_rows_are_rejected(tmp_path, monkeypatch):
    install(tmp_path, monkeypatch, [row(), dict(row(), id='overlap')])
    with pytest.raises(ValueError, match='ambiguous'):
        select(Device('cpu', 0, 'test-cpu', 'AVX2'), 'hierarchical_series', 4096, 1024, 64)


def test_cpu_native_plan_consumes_policy_and_override(tmp_path, monkeypatch):
    monkeypatch.delenv('MF_DGROUP', raising=False)
    from matchedfilter.device import parse
    d = parse('cpu')
    install(tmp_path, monkeypatch, [dict(row(), device=d.name, backend=d.backend)])
    f = mf.HierarchicalFilter(4096, 1, 64, chain=1024)
    assert f._ensure().series_group() == 4
    monkeypatch.setenv('MF_DGROUP', '2')
    f = mf.HierarchicalFilter(4096, 1, 64, chain=1024)
    assert f._ensure().series_group() == 2


@pytest.mark.parametrize('backend', ['vulkan', 'metal'])
@pytest.mark.parametrize('memory_blocks', [2, 10])
def test_gpu_policy_caps_batches_without_overriding_memory(tmp_path, monkeypatch, backend, memory_blocks):
    n, nt = 1024, 2
    install(tmp_path, monkeypatch, [dict(row(), kind='gpu', device='test-gpu', backend=backend,
                                       operation='flat_series', n=n, band=0,
                                       templates_min=nt, templates_max=nt, series_group=3)])
    f = object.__new__(mf.MatchedFilter)
    f.n = n
    f.device = Device('gpu', 0, 'model', backend, arch=('test-gpu',))
    f._gtmpl = np.zeros((nt, n), np.complex64)
    calls = []
    f._gpu = SimpleNamespace(max_dispatch_x=65535,
                             empty_shared=lambda shape, dtype=np.complex64: np.empty(shape, dtype),
                             forward=lambda n, source, starts, spec, **kw: calls.append(len(starts)),
                             cancel_forward=lambda **kw: None)
    f._series_batch_bytes = memory_blocks * (8*n + 4 + 12*nt)
    f._series_window = lambda d, h, *args, **kw: (np.zeros((len(d), nt, 1), np.int64),
                                          np.zeros((len(d), nt, 1), np.complex64))
    layout = SimpleNamespace(nbins=1, starts=np.arange(7)*n, groups=[(0, n, 0, 7)], order=None)
    idx, val = f._run_series_gpu(np.zeros(8*n, np.complex64), layout, n, 0., 0, nt, True)
    assert calls == ([2, 2, 2, 1] if memory_blocks == 2 else [3, 3, 1])
    assert idx.shape == val.shape == (7, nt, 1)


@pytest.mark.parametrize('group', [0, -1, 65536])
def test_native_group_rejects_invalid_sizes(group):
    from matchedfilter import _core
    with pytest.raises(ValueError):
        _core.HMF(4096, 1, 1, [1024], group)


@pytest.mark.parametrize('hierarchical', [False, True])
def test_measured_gpu_group_preserves_series_results(tmp_path, monkeypatch, hierarchical):
    from conftest import usable_gpu
    from matchedfilter.device import parse
    gpu = usable_gpu()
    if gpu is None:
        pytest.skip('no usable hardware GPU')
    d = parse(gpu)
    n, nt = 1024, 2
    install(tmp_path, monkeypatch, [dict(row(), kind='gpu', device=d.name, backend=d.backend,
                                       operation='hierarchical_series' if hierarchical else 'flat_series',
                                       n=n, band=256 if hierarchical else 0,
                                       templates_min=nt, templates_max=nt, series_group=3)])
    rng = np.random.default_rng(169)
    def noise(shape):
        return (rng.normal(size=shape) + 1j*rng.normal(size=shape)).astype(np.complex64)
    series, templates = noise((8*n,)), noise((nt, n))
    if hierarchical:
        f = mf.HierarchicalFilter(n, 1, nt, chain=256, device=gpu)
        f.set_coarse_threshold(0.)
    else:
        f = mf.MatchedFilter(n, 1, nt, device=gpu)
    reference = mf.MatchedFilter(n, 1, nt, device='cpu')
    args = (series, np.arange(7)*n, np.zeros(7, int), np.full(7, n, int))
    for p in (f, reference):
        p.set_templates(templates)
    got, want = f.run_series(*args, binsize=n), reference.run_series(*args, binsize=n)
    assert f._last_series_batch == 3
    np.testing.assert_array_equal(got['index'], want['index'])
    np.testing.assert_allclose(got['value'], want['value'], rtol=3e-4, atol=3e-5)
