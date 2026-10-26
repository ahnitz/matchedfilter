"""tools/migrate_cost_file.py: superseded trial records are removed, everything else kept."""
import importlib.util
import json
from pathlib import Path

import matchedfilter as mf
from matchedfilter import _trial


def _tool():
    path = Path(__file__).resolve().parents[1] / "tools" / "migrate_cost_file.py"
    spec = importlib.util.spec_from_file_location("migrate_cost_file", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


OLD = {
    "block-trial|cpu:0|2048,4096": {"winner": 1, "median": {"0": 2.0, "1": 1.5}},
    "chain-trial|2048|6|0.001|2|cpu:0": {"chain": [256, 1024]},
    "q15-trial|2048|6|0.001|256,512|cpu:0": {"q15": True},
    "choice|block-trial|None|2048,4096,model": {"value": 0},
    "choice|chain-trial|2048|6|0.001|3|cpu:0": {"value": "256,512,1024"},
    "choice|q15-trial|2048|6|0.001|256,512,1024|cpu:0": {"value": "True"},
    "choice|joint|bank|None|2048,4096,model|6|0.001": {"value": "default"},     # kept
    "choice|single-device|gpu:0|2048|4": {"value": "gpu"},                       # kept
    "fft|2048": {"cost": 1.0},                                                   # kept
}


def test_superseded_trial_records_are_removed(monkeypatch, tmp_path):
    path = tmp_path / "costs.json"
    path.write_text(json.dumps(OLD))
    assert _tool().main([str(path)]) == 0
    new = json.loads(path.read_text())
    assert set(new) == {"choice|joint|bank|None|2048,4096,model|6|0.001",
                        "choice|single-device|gpu:0|2048|4", "fft|2048"}
    assert all(new[k] == OLD[k] for k in new)
    monkeypatch.setenv("MF_COST_FILE", str(path))
    mf.clear_autotune_cache()
    assert _trial.winner("bank|None|2048,4096,model|6|0.001") == "default"   # read as before
