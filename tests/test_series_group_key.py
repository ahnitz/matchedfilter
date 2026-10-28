"""A cost model is stored under what it measured: the series group the plans run, not the
one requested (docs/robustness-plan.md, B9a), and the calls it was measured with. MF_DGROUP
and the 4 MB held-spectra cap change the group a hierarchical plan runs; the calibration
used to be keyed by the requested group, so a model measured at a forced group was adopted
by later processes at the default."""
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


def test_gatechain_calibrate_costs_is_the_calibration_plans_call():
    """One entry point, one set of defaults: gatechain's public name was a wrapper that
    measured 256-block calls where plans, tools and tests measured 32."""
    assert gatechain.calibrate_costs is _calibration.calibrate_costs


def test_a_model_measured_with_other_calls_is_kept_apart(monkeypatch, tmp_path):
    """Keyed by (n, templates, group) alone, a model measured with 16-block calls was the one
    every later default call returned, in the process and from MF_COST_FILE. The default
    calls keep the key their models have always been stored under."""
    cost = tmp_path / "costs.json"
    monkeypatch.setenv("MF_COST_FILE", str(cost))
    monkeypatch.delenv("MF_DGROUP", raising=False)
    monkeypatch.setattr(gatechain, "_COSTS", {})
    few = _calibration.calibrate_costs(1024, 16, blocks=16)
    default = _calibration.calibrate_costs(1024, 16)
    assert default is not few
    assert _calibration.calibrate_costs(1024, 16, blocks=16) is few
    assert _calibration.calibrate_costs(1024, 16) is default
    keys = sorted(k for k in json.loads(cost.read_text()) if k.startswith("1024,"))
    assert len(keys) == 2 and keys[1] == keys[0] + ",b16,r5,s11", keys
    group = _core.series_group(1024, gatechain.default_series_group(1024))
    assert keys[0].split(",")[:3] == ["1024", str(gatechain._CAL_TEMPLATES), str(group)], keys
