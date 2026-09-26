"""CPU cost regeneration must preserve cells outside a targeted repair."""
import importlib.util
import json
from pathlib import Path


def test_targeted_repair_keeps_other_measured_groups(tmp_path):
    path = Path(__file__).resolve().parents[1] / 'tools/regen/cost_cpu.py'
    spec = importlib.util.spec_from_file_location('cost_cpu_under_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    def row(n, blocks):
        return dict(n=n, snr=5., fd=.001, profile='-2', ndata=1,
                    ntemplates=1, band=256, ms=1., blocks_ms=blocks,
                    fraction=.8, beff=100., refine_rate=.1, gate=3.)
    measurements = tmp_path / 'measured.json'
    measurements.write_text(json.dumps(dict(records=[
        row(1024, [1., 1., 1.]), row(2048, [1., 2., 1.])])) + '\n')
    output = tmp_path / 'cost.txt'
    module.main(['--sizes', '1024', '--snrs', '5', '--fds', '.001',
                 '--profiles=-2', '--shape', '1x1', '--teaser-shape', '1x1',
                 '--measurements', str(measurements), '--out', str(output),
                 '--repair-outliers'])
    assert {int(line.split()[1]) for line in output.read_text().splitlines()
            if line.startswith('COST ')} == {1024, 2048}
