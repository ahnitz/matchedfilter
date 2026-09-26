"""Opt-in timing gates; use an idle machine and the same environment for baselines."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import matchedfilter as mf
from matchedfilter.benchmark import host_info
from conftest import usable_gpu

pytestmark = pytest.mark.performance
ROOT = Path(__file__).resolve().parents[1]


def _tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def series_bench():
    return _tool('bench_series_workloads')


@pytest.fixture(scope='module')
def audit():
    return _tool('audit_class_execution')


@pytest.fixture(params=['cpu', 'gpu'])
def device(request):
    if request.param == 'cpu':
        return 'cpu'
    gpu = usable_gpu()
    if gpu is None:
        pytest.skip('no usable physical GPU')
    return gpu


@pytest.fixture(scope='module')
def timing_gate(request):
    host = host_info(None)
    # Refuse different hosts, ISAs, or numerical runtimes; package version may
    # change intentionally between baseline and candidate.
    identity = {k: host[k] for k in ('label', 'backend', 'machine', 'system',
                                    'processor', 'python', 'numpy', 'isa_forced')}
    identity['devices'] = [repr(d) for d in mf.devices()]
    baseline_path = request.config.getoption('--performance-baseline')
    baseline = json.loads(Path(baseline_path).read_text()) if baseline_path else None
    if baseline:
        assert baseline['identity'] == identity, 'Performance baseline belongs to a different host/runtime'
    measured = {}

    def check(name, milliseconds):
        measured[name] = milliseconds
        assert np.isfinite(milliseconds) and milliseconds > 0
        if baseline is not None:
            assert name in baseline['milliseconds'], f'Missing performance baseline: {name}'
            old = baseline['milliseconds'][name]
            assert milliseconds <= old * 1.25, (
                f'{name}: {milliseconds:.3f} ms exceeds baseline {old:.3f} ms by more than 25%')
    yield check
    output = request.config.getoption('--performance-record')
    if output and measured and not request.session.testsfailed:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(identity=identity, milliseconds=measured), indent=2) + '\n')


@pytest.mark.parametrize('n', [2048, 4096, 8192])
def test_automatic_peak_series_overhead(device, n, series_bench, timing_gate):
    row = series_bench.peak_series(device, n, 15)
    assert row['automatic_ms'] <= row['explicit_ms'] * 1.5, row
    timing_gate(f'{device}/series/peak/{n}/43x128', row['automatic_ms'])


def test_continuous_output_overhead(device, series_bench, timing_gate):
    row = series_bench.continuous_series(device, 1048576, 11)
    assert row['automatic_ms'] <= row['explicit_and_stitch_ms'] * 1.5, row
    timing_gate(f'{device}/series/full/32768/43x6', row['automatic_ms'])


def test_irregular_gpu_submission_gain(audit, timing_gate):
    gpu = usable_gpu()
    if gpu is None:
        pytest.skip('no usable physical GPU')
    series, starts, low, high, h = audit.inputs(4096, 128, 32, 128)
    f = audit.plan(4096, 32, 32, gpu, 'flat', h)
    maximum = getattr(f._gpu, 'max_grouped_bins', 0)
    if not maximum:
        pytest.skip('grouped submission is Vulkan-specific')
    def call(limit):
        f._gpu.max_grouped_bins = limit
        return f.run_blocks(series, starts, low, high)
    try:
        audit.validate(call(0).copy(), call(maximum))
        results = audit.times({'separate': lambda: call(0),
                               'grouped': lambda: call(maximum)}, 9)
    finally:
        f._gpu.max_grouped_bins = maximum
    old = results['separate']['median_ms']
    new = results['grouped']['median_ms']
    assert new <= old * 0.5, results
    timing_gate(f'{gpu}/blocks/irregular/4096/128x32', new)


@pytest.mark.parametrize('n,nd,nt', [(2048,16,128), (4096,16,128),
                                    (8192,16,128), (4096,128,512)])
@pytest.mark.parametrize('kind', ['flat', 'hier'])
def test_cached_spectral_calls(device, n, nd, nt, kind, audit, timing_gate):
    rng = np.random.default_rng(n)
    data = (rng.normal(size=(nd,n)) + 1j*rng.normal(size=(nd,n))).astype('complex64')
    templates = (rng.normal(size=(nt,n)) + 1j*rng.normal(size=(nt,n))).astype('complex64')
    templates /= np.linalg.norm(templates, axis=1, keepdims=True)
    f = audit.plan(n, nd, nt, device, kind, templates)
    f.set_data(data)
    result = f.run(binsize=n, threshold=0.)
    assert np.all(np.isfinite(result['value']))
    assert np.any(result['index'] >= 0), 'Correctness check needs admitted peaks'
    # Check admitted peaks against an independent double-precision transform.
    for d, t in np.argwhere(result['index'][..., 0] >= 0)[:8]:
        corr = np.fft.ifft(data[d].astype('complex128') * templates[t].conj().astype('complex128')) * n
        lag = int(result['index'][d,t,0])
        np.testing.assert_allclose(result['value'][d,t,0], corr[lag], rtol=3e-5, atol=3e-5)
    # Verify unfloored peaks above, then time the usual sparse-output floor.
    measurements = audit.times({'run': lambda: f.run(binsize=n, threshold=5.5)}, 9)
    timing_gate(f'{device}/run/{kind}/{n}/{nd}x{nt}/floor5.5', measurements['run']['median_ms'])
