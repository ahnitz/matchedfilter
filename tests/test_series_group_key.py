"""A cost model is stored under the series group the plans run, not the one requested
(docs/robustness-plan.md, B9a). MF_DGROUP and the 4 MB held-spectra cap change the group
a hierarchical plan runs; the calibration used to be keyed by the requested group, so a
model measured at a forced group was adopted by later processes at the default."""
import json

from matchedfilter import _core, gatechain
from matchedfilter import _calibration


def test_the_effective_group_follows_the_plan(monkeypatch):
    monkeypatch.delenv("MF_DGROUP", raising=False)
    assert _core.series_group(1024, 32) == 32
    assert _core.series_group(1 << 20, 16) == 1              # 4 MB cap: one 8 MB block
    monkeypatch.setenv("MF_DGROUP", "8")
    assert _core.series_group(1024, 32) == 8
    h = _core.HMF(1024, 1, 4, [256], 32)
    assert h.series_group() == _core.series_group(1024, 32)


def test_a_calibration_under_mf_dgroup_is_stored_under_the_group_that_ran(monkeypatch, tmp_path):
    cost = tmp_path / "costs.json"
    monkeypatch.setenv("MF_COST_FILE", str(cost))
    monkeypatch.setenv("MF_DGROUP", "8")
    monkeypatch.setattr(gatechain, "_COSTS", {})
    _calibration.calibrate_costs(1024, 16, group=32)
    keys = [k for k in json.loads(cost.read_text()) if k.startswith("1024,")]
    assert keys and all(k.split(",")[2] == "8" for k in keys), keys
