"""The one price-once rule (_prices.price_once): this process's memo, else a valid record on
file, else measure and store first-writer-wins."""
import json

from matchedfilter import _costfile, _prices


def _read(r):
    return float(r["v"]) if isinstance(r, dict) and r.get("v", 0) > 0 else None


def test_memo_then_file_then_measure(monkeypatch, tmp_path):
    path = tmp_path / "costs.json"
    monkeypatch.setenv("MF_COST_FILE", str(path))
    calls = []

    def measure():
        calls.append(1)
        return 2.0, {"v": 2.0}
    memo = {}
    assert _prices.price_once(memo, "k", "price|k", measure, _read) == 2.0
    assert json.loads(path.read_text())["price|k"] == {"v": 2.0}
    assert _prices.price_once(memo, "k", "price|k", measure, _read) == 2.0 and len(calls) == 1
    # a new process reads the file instead of measuring
    assert _prices.price_once({}, "k", "price|k", measure, _read) == 2.0 and len(calls) == 1


def test_a_price_another_process_stored_first_is_used(monkeypatch, tmp_path):
    path = tmp_path / "costs.json"
    monkeypatch.setenv("MF_COST_FILE", str(path))

    def measure():                   # another process stores while this one measures
        _costfile._store_cost(path, "price|k", {"v": 5.0})
        return 3.0, {"v": 3.0}
    assert _prices.price_once({}, "k", "price|k", measure, _read) == 5.0


def test_an_invalid_record_is_replaced_and_a_failed_price_never_stored(monkeypatch, tmp_path):
    path = tmp_path / "costs.json"
    monkeypatch.setenv("MF_COST_FILE", str(path))
    _costfile._store_cost(path, "price|k", {"v": -1})
    assert _prices.price_once({}, "k", "price|k", lambda: (4.0, {"v": 4.0}), _read) == 4.0
    assert json.loads(path.read_text())["price|k"] == {"v": 4.0}
    memo = {}
    assert _prices.price_once(memo, "f", "price|f", lambda: (-1.0, None), _read) == -1.0
    assert "price|f" not in json.loads(path.read_text()) and memo == {"f": -1.0}


def test_without_a_cost_file_the_process_measures_once(monkeypatch):
    monkeypatch.delenv("MF_COST_FILE", raising=False)
    calls = []
    memo = {}
    for _ in range(3):
        _prices.price_once(memo, "k", "price|k", lambda: (calls.append(1) or 1.5, {"v": 1.5}), _read)
    assert len(calls) == 1
