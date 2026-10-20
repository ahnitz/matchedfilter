"""The measured-choice lifecycle (_choice), driven with injected timings: no device, no wall
clock, so every branch is exact and none can flake."""
import json

import pytest

from matchedfilter import _choice


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    monkeypatch.setattr(_choice, "_CHOICES", {})


def _drive(ch, timer, calls=100):
    """Run calls through ch with timer(candidate, i) seconds; the candidates taken in order."""
    seen, k = [], {c: 0 for c in ch.candidates}
    for _ in range(calls):
        cand, record = ch.next()
        seen.append(cand)
        if record is None:
            break
        record(timer(cand, k[cand]))
        k[cand] += 1
    return seen


def test_candidates_alternate_from_the_preference_and_a_clear_win_locks():
    ch = _choice.Choice(("gpu", "cpu"))
    seen = _drive(ch, lambda c, i: 1.0 if c == "gpu" else 0.4)
    assert seen[:4] == ["gpu", "cpu", "gpu", "cpu"]
    assert ch.winner == "cpu"
    # A decision needs every candidate past the warm-up by `minimum` samples, no sooner.
    assert all(len(v) == ch.warmup + ch.minimum for v in ch.samples.values())
    assert ch.next() == ("cpu", None)


def test_the_warm_up_samples_are_dropped():
    """The warm-up samples never decide: here two fast first calls of the preference would
    have kept it, but its steady calls are twice the other's."""
    ch = _choice.Choice(("gpu", "cpu"), warmup=2, minimum=1)
    _drive(ch, lambda c, i: (0.1 if i < 2 else 2.0) if c == "gpu" else 1.0)
    assert ch.winner == "cpu"


def test_an_unclear_contest_samples_to_the_cap_then_keeps_the_preference():
    # The CPU's median is past the tie but inside the noise (first samples: warm-up).
    seq = {"gpu": [5.0, 1.0, 1.3, 0.8, 1.25, 0.85, 1.0, 1.1],
           "cpu": [5.0, 0.8, 1.2, 0.85, 1.3, 0.75, 1.15, 0.9]}
    ch = _choice.Choice(("gpu", "cpu"))
    _drive(ch, lambda c, i: seq[c][i])
    assert ch.winner == "gpu"
    assert len(ch.samples["gpu"]) - ch.warmup == ch.cap


def test_the_lock_is_stored_and_a_later_process_reuses_it_untimed(monkeypatch, tmp_path):
    cost = tmp_path / "costs.json"
    monkeypatch.setenv("MF_COST_FILE", str(cost))
    ch = _choice.choice("demo", ("k",), ("fused", "unfused"), store_key="demo|k")
    _drive(ch, lambda c, i: 2.0 if c == "fused" else 1.0)
    assert ch.winner == "unfused"
    assert json.loads(cost.read_text())["choice|demo|k"]["value"] == "unfused"
    _choice.reset()                                     # another process
    again = _choice.choice("demo", ("k",), ("fused", "unfused"), store_key="demo|k")
    assert again is not ch and again.next() == ("unfused", None)


def test_a_stored_value_that_is_not_a_candidate_is_ignored(monkeypatch, tmp_path):
    cost = tmp_path / "costs.json"
    cost.write_text(json.dumps({"choice|demo|k": {"value": "gone"}}))
    monkeypatch.setenv("MF_COST_FILE", str(cost))
    ch = _choice.Choice(("a", "b"), store_key="demo|k")
    assert ch.winner is None and ch.next()[1] is not None


def test_without_a_cost_file_the_choice_is_still_measured_and_kept_for_the_process(monkeypatch):
    monkeypatch.delenv("MF_COST_FILE", raising=False)
    ch = _choice.choice("demo", 1, ("a", "b"), store_key="demo|1")
    _drive(ch, lambda c, i: 3.0 if c == "a" else 1.0)
    assert ch.winner == "b"
    assert _choice.choice("demo", 1, ("a", "b")) is ch     # the process's one choice


def test_the_registry_keeps_one_choice_per_kind_and_key():
    a = _choice.choice("x", 1, ("p", "q"))
    assert _choice.choice("x", 1, ("p", "q")) is a
    b = _choice.choice("y", 1, ("p", "q"))
    assert b is not a and set(_choice.of_kind("x")) == {1}
    _choice.reset("x")
    assert _choice.of_kind("x") == {} and _choice.of_kind("y") == {1: b}


def test_three_candidates_are_sampled_in_turn():
    ch = _choice.Choice(("a", "b", "c"))
    seen = _drive(ch, lambda c, i: {"a": 1.0, "b": 0.5, "c": 2.0}[c])
    assert seen[:6] == ["a", "b", "c", "a", "b", "c"]
    assert ch.winner == "b"


@pytest.mark.parametrize("bad", [("a",), ("a", "a")])
def test_a_choice_needs_distinct_candidates(bad):
    with pytest.raises(ValueError):
        _choice.Choice(bad)


def test_a_retrial_starts_the_contest_again_after_that_many_calls():
    """A lock made under passing load does not stick: `retrial` calls later the candidates
    are timed again, and the new contest can lock the other one."""
    ch = _choice.Choice(("a", "b"), tie=0.0, z=0.0, retrial=10)
    _drive(ch, lambda c, i: 1.0 if c == "a" else 2.0)
    assert ch.winner == "a" and ch.calls == 1          # _drive's last call saw the lock
    for _ in range(ch.retrial - 2):
        assert ch.next() == ("a", None)
    cand, record = ch.next()                            # the 10th: a new trial begins
    assert record is not None and ch.winner is None
    _drive(ch, lambda c, i: 3.0 if c == "a" else 2.0)
    assert ch.winner == "b"


def test_tie_zero_takes_the_lower_median_however_close():
    """The sparse-way schedule (tie 0, z 0): whichever way's median is lower, even by 1%."""
    ch = _choice.Choice(("rows", "compact"), tie=0.0, z=0.0)
    _drive(ch, lambda c, i: 1.0 if c == "rows" else 0.99)
    assert ch.winner == "compact"
    default = _choice.Choice(("rows", "compact"))        # the shared rule's tie keeps rows
    _drive(default, lambda c, i: 1.0 if c == "rows" else 0.99)
    assert default.winner == "rows"


def test_offline_seconds_pick_the_fastest_and_store_runners_up(monkeypatch, tmp_path):
    cost = tmp_path / "costs.json"
    monkeypatch.setenv("MF_COST_FILE", str(cost))
    ch = _choice.Choice(("a", "b", "c", "d"), store_key="k", recheck_stored=True)
    assert ch.decide(lambda cs: {"a": 3.0, "b": 1.0, "c": 2.0, "d": 4.0}) == "b"
    rec = json.loads(cost.read_text())["choice|k"]
    assert rec["value"] == "b" and rec["rivals"] == "c;a"
    # A later process times the stored choice against its rivals: a rival now clearly
    # faster (a spoiled first measurement) is remeasured and stored.
    again = _choice.Choice(("a", "b", "c", "d"), store_key="k", recheck_stored=True)
    assert again.decide(lambda cs: {c: {"a": 0.5, "b": 1.0, "c": 2.0, "d": 4.0}[c] for c in cs}) == "a"


def test_offline_samples_decide_by_the_shared_rule():
    ch = _choice.Choice((32, 16, 8))
    assert ch.decide(lambda cs: {32: [5.0] * 5, 16: [2.0] * 5, 8: [0.6] * 5}) == 8
    close = _choice.Choice((32, 8))                      # inside the tie: the preference
    assert close.decide(lambda cs: {32: [1.0] * 5, 8: [0.98] * 5}) == 32
