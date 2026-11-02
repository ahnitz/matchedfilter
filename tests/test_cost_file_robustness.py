"""MF_COST_FILE never loses data, and processes sharing it agree (docs/robustness-plan.md, B1).

Until 2026-10-21 a damaged file (truncated, garbage, a JSON list) read as empty and the
next write replaced it with one record: every stored model and lock was gone, silently.
An unreadable file (EIO, a permission change) was replaced the same way. And two
processes calibrating or pricing at once each kept their own result in memory, so they
priced chains differently, whichever stored last."""
import builtins
import errno
import json
import os
import warnings

import pytest

from matchedfilter import gatechain
from matchedfilter import _costfile


@pytest.fixture
def cost(tmp_path, monkeypatch):
    path = tmp_path / "costs.json"
    monkeypatch.setenv("MF_COST_FILE", str(path))
    monkeypatch.setattr(_costfile, "_COST_WARNED", set())
    return path


@pytest.mark.parametrize("damage", [b'{"keep|me": {"value": 1}, "trunc', b"\x00\xff\xfe garbage",
                                     b"[1, 2, 3]"], ids=["truncated", "binary", "list"])
def test_a_damaged_file_is_kept_aside_reported_and_replaced(cost, damage):
    cost.write_bytes(damage)
    with pytest.warns(RuntimeWarning, match="not a JSON object"):
        assert _costfile._load_cost_file(str(cost)) == {}
    with pytest.warns(RuntimeWarning, match="kept as"):
        _costfile._store_cost(str(cost), "new|rec", {"x": 1})
    aside = [p for p in cost.parent.iterdir() if ".corrupt." in p.name]
    assert len(aside) == 1 and aside[0].read_bytes() == damage       # nothing lost
    assert json.loads(cost.read_text()) == {"new|rec": {"x": 1}}


def test_an_unreadable_file_is_never_replaced(cost, monkeypatch):
    cost.write_text(json.dumps({"keep|me": {"value": 1}}))
    real_open = builtins.open

    def failing_open(file, mode="r", *a, **kw):
        if os.fspath(file) == str(cost) and mode in ("r", "rb"):
            raise OSError(errno.EIO, "I/O error")
        return real_open(file, mode, *a, **kw)
    monkeypatch.setattr(builtins, "open", failing_open)
    with pytest.warns(RuntimeWarning, match="cannot be read"):
        assert _costfile._update_cost(str(cost), "new|rec", lambda old: {"x": 1}) is None
    monkeypatch.setattr(builtins, "open", real_open)
    assert json.loads(cost.read_text()) == {"keep|me": {"value": 1}}


def test_an_update_returns_the_record_now_on_file(cost):
    assert _costfile._update_cost(str(cost), "k", lambda old: {"v": 1}) == {"v": 1}
    assert _costfile._update_cost(str(cost), "k", lambda old: None) == {"v": 1}


def test_the_first_valid_record_stands(cost):
    first = gatechain._store_first(str(cost), "price", {"v": 1}, lambda r: "v" in r)
    second = gatechain._store_first(str(cost), "price", {"v": 2}, lambda r: "v" in r)
    assert first == second == {"v": 1}
    cost.write_text(json.dumps({"price": {"broken": True}}))      # not valid: replaced
    assert gatechain._store_first(str(cost), "price", {"v": 3}, lambda r: "v" in r) == {"v": 3}


def test_a_stored_record_that_is_not_a_cost_model_is_recalibrated(cost):
    good = gatechain.CostModel(256, {64: 1.0}, {64: [(0.01, 2.0), (0.1, 2.5)]},
                               [(0.01, 3.0), (0.1, 3.5)], block=1.0).to_dict()
    cost.write_text(json.dumps({"good": good, "bad": {"n": 256}}))
    assert gatechain._stored_cost_model(str(cost), "good").to_dict() == good
    with pytest.warns(RuntimeWarning, match="not a cost model"):
        assert gatechain._stored_cost_model(str(cost), "bad") is None
    assert gatechain._stored_cost_model(str(cost), "absent") is None


def test_legacy_trial_records_are_reported_once(cost):
    cost.write_text(json.dumps({"block-trial|cpu|2048": {"winner": 0}, "x": 1}))
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _costfile._load_cost_file(str(cost))
        _costfile._load_cost_file(str(cost))
    hits = [x for x in w if "migrate_cost_file" in str(x.message)]
    assert len(hits) == 1


def test_migrate_refuses_a_damaged_file(cost, tmp_path):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "migrate_cost_file", Path(__file__).resolve().parents[1] / "tools" / "migrate_cost_file.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    cost.write_bytes(b'{"trunc')
    assert tool.main([str(cost)]) == 1
    assert cost.read_bytes() == b'{"trunc'
