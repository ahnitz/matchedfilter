"""Fleet reports must not turn unavailable or incorrect results into bars."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import numpy as np


@pytest.fixture
def fleet(monkeypatch):
    tools = Path(__file__).resolve().parents[1] / 'tools'
    monkeypatch.syspath_prepend(str(tools))
    spec = importlib.util.spec_from_file_location('fleet_test', tools/'teaser_fleet.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validation_checks_cpu_values_indices_and_injection(fleet, monkeypatch):
    monkeypatch.setattr(fleet.teaser, 'N', 1024)
    monkeypatch.setattr(fleet.teaser, 'NT', 3)
    assert set(fleet.validate('cpu')) == {'full', 'flat', 'hier'}


def test_failed_validation_leaves_no_timings(fleet, monkeypatch, tmp_path):
    def fail(device):
        raise AssertionError('incorrect phase')
    monkeypatch.setattr(fleet, 'validate', fail)
    monkeypatch.setattr(fleet.teaser.mf, 'devices', lambda: [])
    out = tmp_path/'failed.json'
    args = SimpleNamespace(cpu=None, host='test', revision='test', device='cpu', out=out)
    with pytest.raises(AssertionError, match='incorrect phase'):
        fleet.collect(args)
    report = json.loads(out.read_text())
    assert report['rows'] == []
    assert 'incorrect phase' in report['errors'][0]


def test_plot_missing_gpu_and_reference(fleet, tmp_path):
    pytest.importorskip('matplotlib')
    base = dict(host='test', n=4096, data=16, templates=512, snr=5.5,
                cpu='Test CPU', gpu='Unavailable', rows=[])
    cpu = dict(base, device='cpu', rows=[dict(kind='flat', fd=None, ms=20)])
    gpu = dict(base, device='gpu')
    paths = [tmp_path/'cpu.json', tmp_path/'gpu.json']
    for path, report in zip(paths, (cpu, gpu)):
        path.write_text(json.dumps(report))
    fleet.compare(paths, tmp_path/'comparison.svg')
    assert (tmp_path/'comparison.svg').stat().st_size > 1000
    assert (tmp_path/'comparison.png').is_file()
    with pytest.raises(ValueError, match='one report per host'):
        fleet.compare([paths[0], paths[0]], tmp_path/'duplicate.svg')
    gpu['data'] = 128
    paths[1].write_text(json.dumps(gpu))
    with pytest.raises(ValueError, match='same workload'):
        fleet.compare(paths, tmp_path/'different.svg')


def test_gpu_reference_samples_match_reported_units(fleet, monkeypatch, tmp_path):
    device = SimpleNamespace(kind='gpu', is_software=False, name='Test GPU')
    monkeypatch.setattr(fleet.teaser.mf, 'devices', lambda: [device])
    monkeypatch.setattr(fleet, 'validate', lambda device: {})
    monkeypatch.setattr(fleet, 'MODES', [])
    monkeypatch.setattr(fleet.sys, 'platform', 'linux')
    def baseline():
        fleet.teaser._timed.details = dict(block_ms=[8., 16., 24.],
                                           calls_per_block=[1, 1, 1], min_ms=8., max_ms=24.)
        return 2.
    monkeypatch.setattr(fleet.teaser, 'rocfft_ms', baseline)
    out = tmp_path/'gpu.json'
    fleet.collect(SimpleNamespace(cpu=None, host='test', revision='test', device='gpu', out=out))
    row = json.loads(out.read_text())['rows'][0]
    assert np.median(row['timing']['block_ms']) == row['ms']
    assert row['timing']['min_ms'] == 1.
    assert row['timing']['max_ms'] == 3.
