"""tools/migrate_cost_file.py: trial locks in the old record format are rewritten so the
library reads them back as the same choices."""
import importlib.util
import json
from pathlib import Path

import matchedfilter as mf
from matchedfilter import time_domain as td


def _tool():
    path = Path(__file__).resolve().parents[1] / "tools" / "migrate_cost_file.py"
    spec = importlib.util.spec_from_file_location("migrate_cost_file", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


OLD = {
    "block-trial|cpu:0|2048,4096": {"winner": 1, "median": {"0": 2.0, "1": 1.5}, "rechecked": True},
    "block-trial|gpu:0|2048,8192": {"samples": {"0": [1.0], "1": []}},          # unfinished
    "chain-trial|2048|6|0.001|2|cpu:0": {"chain": [256, 1024], "rechecked": False,
                                         "median": {"256,1024": 1e-9, "512": 2e-9}},
    "chain-trial|2048|6|0.001|2|gpu:0|batches": {"samples": {"512": [1.0]}},     # unfinished
    "q15-trial|2048|6|0.001|256,512|cpu:0": {"method": "paired-v1", "q15": True,
                                             "samples": {"False": [1.0], "True": [0.8]}},
    "fft|2048": {"cost": 1.0},                                                   # untouched
}


def test_old_trial_locks_read_back_as_the_same_choices(monkeypatch, tmp_path):
    path = tmp_path / "costs.json"
    path.write_text(json.dumps(OLD))
    assert _tool().main([str(path)]) == 0
    new = json.loads(path.read_text())
    assert new["fft|2048"] == OLD["fft|2048"]
    assert not any(k.startswith(("block-trial|", "chain-trial|", "q15-trial|")) for k in new)
    assert set(k for k in new if k.startswith("choice|")) == {
        "choice|block-trial|cpu:0|2048,4096", "choice|chain-trial|2048|6|0.001|2|cpu:0",
        "choice|q15-trial|2048|6|0.001|256,512|cpu:0"}

    monkeypatch.setenv("MF_COST_FILE", str(path))
    mf.clear_autotune_cache()
    trials = td._BlockTrials()
    assert trials.winner("cpu:0|2048,4096") == 1
    assert trials._st("cpu:0|2048,4096").rechecked             # its re-check state kept
    assert trials.winner("gpu:0|2048,8192") is None             # unfinished: trialled afresh
    tk = (2048, 6.0, 0.001, 2, "cpu:0")
    assert mf._stored_chain_lock(tk, None) == (256, 1024)
    assert mf._chain_trial(tk).median == {(256, 1024): 1e-9, (512,): 2e-9}
    p = object.__new__(mf.HierarchicalFilter)
    p.n, p._fs_snr, p.snr, p.fd = 2048, None, 6, 0.001
    p._chain, p._q15_pref, p.device = (256, 512), False, "cpu:0"
    assert p._q15_trial().winner is True
