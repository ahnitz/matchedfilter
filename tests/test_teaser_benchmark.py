"""The teaser must measure the same public API on CPU and GPU."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


@pytest.mark.parametrize('device', ['cpu', 'gpu'])
@pytest.mark.parametrize('kind', ['full', 'flat', 'hier'])
def test_teaser_times_public_run(monkeypatch, device, kind):
    path = Path(__file__).resolve().parents[1] / 'tools' / 'teaser_figure.py'
    spec = importlib.util.spec_from_file_location('teaser_timing_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls = []
    elapsed = [0.0]

    class Filter:
        def __init__(self, *args, **kwargs):
            self._gpu = SimpleNamespace(destroy=lambda: None) if device == 'gpu' else None

        def set_reference(self, value):
            pass

        def set_data(self, value):
            pass

        def set_templates(self, value):
            pass

        def empty_shared(self, shape):
            return np.empty(shape, np.complex64)

        def run(self, **kwargs):
            calls.append(kwargs)
            elapsed[0] += 0.002

    monkeypatch.setattr(module.mf, 'MatchedFilter', Filter)
    monkeypatch.setattr(module.mf, 'CorrelationFilter', Filter)
    monkeypatch.setattr(module.mf, 'HierarchicalFilter', Filter)
    monkeypatch.setattr(module, '_case', lambda: (np.zeros(1), np.zeros(1)))
    monkeypatch.setattr(module, '_reference', lambda: (np.ones(1), np.ones(1)))
    monkeypatch.setattr(module.time, 'perf_counter', lambda: elapsed[0])
    result = getattr(module, device + '_ms')(kind, reps=4)
    assert result == pytest.approx(2.0)
    assert len(calls) > 4  # warmup also uses the same API
    if kind == 'full':
        assert all(c['out'].shape == (module.ND, module.NT, module.N) for c in calls)
    else:
        assert all(c == {'binsize': module.N, 'threshold': 5.5} for c in calls)


def test_teaser_selects_metal_reference_and_records_machine(monkeypatch, tmp_path):
    import json
    path = Path(__file__).resolve().parents[1] / 'tools' / 'teaser_figure.py'
    spec = importlib.util.spec_from_file_location('teaser_portability_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.sys, 'platform', 'darwin')
    monkeypatch.setattr(module, '_cpu_name', lambda: 'Apple M2')
    monkeypatch.setattr(module, '_gpu_name', lambda: 'Apple M2')
    monkeypatch.setattr(module, 'plot', lambda report, out: None)
    module._timed.details = dict(min_ms=1., max_ms=1.)
    monkeypatch.setattr(module, 'fftw_ms', lambda: 1.)
    monkeypatch.setattr(module, 'mlx_ms', lambda: 2.)
    def measure(kind, fd):
        for device in ('cpu', 'gpu'):
            module._DETAILS[(device, fd)] = dict(band=256, taps=4, refine_rate=.1)
        return 3.
    monkeypatch.setattr(module, 'cpu_ms', measure)
    monkeypatch.setattr(module, 'gpu_ms', measure)
    module.main(['--out', str(tmp_path / 'm2.svg')])
    report = json.loads((tmp_path / 'm2.json').read_text())
    assert report['cpu'] == report['gpu'] == 'Apple M2'
    assert report['gpu_baseline'] == 'MLX'
    row = next(r for r in report['rows'] if r['device'] == 'gpu' and r['kind'] == 'baseline')
    assert row['ms'] == 2.
    assert row['timing']['executions_per_call'] == 8
    with pytest.raises(ValueError, match='same workload'):
        module.plot_comparison([report, dict(report, data=report['data']*2)], tmp_path/'bad.svg')


def test_aligned_fftw_reference(monkeypatch):
    import ctypes
    pyfftw = pytest.importorskip('pyfftw')
    lib = ctypes.CDLL(pyfftw.pyfftw.__file__)
    if not hasattr(lib, 'fftwf_plan_many_dft'):
        pytest.skip('FFTW C symbols are not visible through this wrapper')
    path = Path(__file__).resolve().parents[1] / 'tools' / 'teaser_figure.py'
    spec = importlib.util.spec_from_file_location('teaser_fftw_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'N', 1024)
    monkeypatch.setattr(module, 'ND', 1)
    monkeypatch.setattr(module, 'NT', 2)
    monkeypatch.setattr(module, 'PAIRS', 2)
    monkeypatch.setattr(module, '_timed', lambda fn, reps: fn() or 1.)
    module._DETAILS['fftw'] = {}
    # The native reference validates its output against a double-precision FFT.
    assert module._fftw_native_ms(lib, 1) == 1.
    assert module._DETAILS['fftw']['interface'] == 'aligned C API; single thread'
