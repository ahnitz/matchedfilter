"""The measured-choice lifecycle (_choice), driven with injected timings: no device, no wall
clock, so every branch is exact and none can flake."""
import json

import pytest

from matchedfilter import _choice


@pytest.fixture(autouse=True)
def _test_kinds(monkeypatch):
    """The kinds these tests make, declared as every kind must be (_choice.SCOPES)."""
    for kind in ("demo", "x", "y"):
        monkeypatch.setitem(_choice.SCOPES, kind, "workload")


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    monkeypatch.setattr(_choice, "_CHOICES", {})


def _rounds(ch, cost, n=100):
    """Feed ch up to n complete rounds, cost(candidate, round) seconds each, until it locks."""
    for i in range(n):
        if ch.winner is not None:
            break
        ch.round({c: cost(c, i) for c in ch.live()})
    return ch.winner


def test_a_clear_win_locks_and_the_preference_holds_a_tie():
    assert _rounds(_choice.Choice(("a", "b")), lambda c, i: 1.0 if c == "a" else 0.5) == "b"
    assert _rounds(_choice.Choice(("a", "b")), lambda c, i: 1.0 if c == "a" else 0.98) == "a"


def test_an_unclear_contest_runs_to_the_cap_then_keeps_the_preference():
    ch = _choice.Choice(("a", "b"))
    seq = [0.8, 1.2] * 10                    # b alternately faster and slower: never 75%
    assert _rounds(ch, lambda c, i: 1.0 if c == "a" else seq[i]) == "a"
    assert len(ch.samples["a"]) <= ch.cap


def test_the_lock_is_stored_and_a_later_process_reuses_it_untimed(monkeypatch, tmp_path):
    cost = tmp_path / "costs.json"
    monkeypatch.setenv("MF_COST_FILE", str(cost))
    ch = _choice.Choice(("gpu", "cpu"), store_key="k")
    assert _rounds(ch, lambda c, i: 1.0 if c == "gpu" else 0.4) == "cpu"
    assert json.loads(cost.read_text())["choice|k"]["value"] == "cpu"
    again = _choice.Choice(("gpu", "cpu"), store_key="k")
    assert again.winner == "cpu" and not any(again.samples.values())


def test_a_stored_value_that_is_not_a_candidate_is_ignored(monkeypatch, tmp_path):
    cost = tmp_path / "costs.json"
    cost.write_text(json.dumps({"choice|k": {"value": "tpu"}}))
    monkeypatch.setenv("MF_COST_FILE", str(cost))
    ch = _choice.Choice(("gpu", "cpu"), store_key="k")
    assert ch.winner is None


def test_without_a_cost_file_the_choice_is_still_measured_and_kept_for_the_process(monkeypatch):
    monkeypatch.delenv("MF_COST_FILE", raising=False)
    ch = _choice.Choice(("gpu", "cpu"), store_key="k")
    assert _rounds(ch, lambda c, i: 1.0 if c == "gpu" else 0.4) == "cpu"


def test_the_registry_keeps_one_choice_per_kind_and_key():
    a = _choice.choice("x", 1, ("p", "q"))
    assert _choice.choice("x", 1, ("p", "q")) is a
    b = _choice.choice("y", 1, ("p", "q"))
    assert b is not a and set(_choice.of_kind("x")) == {1}
    _choice.reset("x")
    assert _choice.of_kind("x") == {} and _choice.of_kind("y") == {1: b}


def test_a_choice_needs_distinct_candidates():
    with pytest.raises(ValueError):
        _choice.Choice(("a", "a"))


def test_the_budget_ends_a_contest_whose_rounds_never_come(monkeypatch, tmp_path):
    ch = _choice.Choice(("a", "b"), budget=(2, 1))
    for _ in range(ch.limit):
        ch.tick()
    assert ch.winner == "a"


def test_at_the_budget_a_clearly_faster_candidate_still_wins_by_the_paired_rule():
    ch = _choice.Choice(("a", "b"), budget=(0, 3))
    for _ in range(3):
        ch.round({"a": 1.0, "b": 0.5})                    # short of the minimum
    while ch.winner is None:
        ch.tick()
    assert ch.winner == "b"


def test_at_the_budget_the_preference_stands_with_too_few_rounds():
    ch = _choice.Choice(("a", "b"), budget=(0, 3))
    ch.round({"a": 1.0, "b": 0.5})
    while ch.winner is None:
        ch.tick()
    assert ch.winner == "a"


def test_a_lock_another_process_stored_first_is_adopted(monkeypatch, tmp_path):
    cost = tmp_path / "costs.json"
    monkeypatch.setenv("MF_COST_FILE", str(cost))
    mine = _choice.Choice(("gpu", "cpu"), store_key="k")
    other = _choice.Choice(("gpu", "cpu"), store_key="k")
    assert _rounds(other, lambda c, i: 1.0 if c == "gpu" else 0.4) == "cpu"
    _rounds(mine, lambda c, i: 1.0 if c == "cpu" else 0.4)   # would pick the GPU
    assert mine.winner == "cpu"


def test_a_dropped_candidate_leaves_the_contest():
    ch = _choice.Choice(("a", "b", "c"))
    ch.drop("c")
    assert ch.live() == ["a", "b"]
    assert _rounds(ch, lambda c, i: {"a": 1.0, "b": 0.5, "c": 0.1}[c]) == "b"


def test_a_retrial_starts_the_contest_again(monkeypatch):
    """A lock made under passing load does not stick: `retrial` plays after a lock the
    candidates are timed again, and the new contest can lock the other one."""
    ch = _choice.Choice(("a", "b"), retrial=4)
    ch.lock("a")
    import time
    clock = [0.0]
    monkeypatch.setattr(time, "perf_counter", lambda: clock[0])
    cost = {"a": 3.0, "b": 2.0}

    def run(c):
        clock[0] += cost[c]
        return c
    for _ in range(3):
        assert ch.play(run, set()) == "a" and ch.winner == "a"
    ch.play(run, set())                                  # the 4th call: a new contest
    assert ch.winner is None
    for _ in range(40):
        if ch.winner is not None:
            break
        ch.play(run, set())
    assert ch.winner == "b"


@pytest.mark.parametrize("kw", [dict(), dict(cap=7), dict(budget=(2, 1)), dict(minimum=3, cap=4)])
def test_a_contest_that_never_resolves_locks_within_its_limit(kw):
    """Choice.limit bounds the calls a contest takes, whatever its timings: rounds that never
    agree end at the cap, and calls that are never rounds at the budget."""
    ch = _choice.Choice(("a", "b"), **kw)
    seq = [0.8, 1.2]
    for i in range(ch.limit):
        if ch.winner is not None:
            break
        if ch.budget is not None:
            ch.tick()
        else:
            ch.round({"a": 1.0, "b": seq[i % 2]})
    assert ch.winner == "a"


def test_a_kind_declares_its_reset_scope(monkeypatch):
    with pytest.raises(ValueError, match="declare choice kind 'undeclared'"):
        _choice.choice("undeclared", 1, ("a", "b"))
    monkeypatch.setitem(_choice.SCOPES, "hw", "machine")
    w = _choice.choice("x", 1, ("p", "q"))
    m = _choice.choice("hw", 1, ("p", "q"))
    _choice.reset(scope="workload")
    assert _choice.of_kind("x") == {} and _choice.of_kind("hw") == {1: m}
    _choice.reset("hw")
    assert w is not _choice.choice("x", 1, ("p", "q"))


class _Clock:
    """time.perf_counter for Choice.play: each run advances it by its candidate's cost."""

    def __init__(self, cost):
        self.t, self.cost, self.runs = 0.0, cost, []

    def run(self, c):
        self.runs.append(c)
        self.t += self.cost(c, len(self.runs))
        return "result of %s" % c


def _play(ch, clock, monkeypatch, calls, ran):
    import time
    monkeypatch.setattr(time, "perf_counter", lambda: clock.t)
    return [ch.play(clock.run, ran) for _ in range(calls)]


def test_play_returns_the_preference_and_times_second_runs(monkeypatch):
    """Every open play runs each live candidate on the call, the preference's result is the
    call's, and each timed run follows an untimed run of the same candidate: running second
    gains from the run before (a GPU batch 20-30%), so every timed run is a second run."""
    ch = _choice.Choice(("a", "b"), minimum=5, cap=10)
    clock, ran = _Clock(lambda c, i: 1.0), set()
    out = _play(ch, clock, monkeypatch, 3, ran)
    assert out == ["result of a"] * 3
    assert ran == {"a", "b"}
    assert clock.runs[:4] == ["a", "a", "b", "b"]          # untimed, then timed, per candidate
    assert clock.runs[4:8] == ["b", "b", "a", "a"]         # the order reverses every round
    assert len(clock.runs) == 3 * 4


def test_running_second_does_not_decide_a_play(monkeypatch):
    """Equal candidates where a call's first run is cold and its later runs 30% faster (a GPU
    batch: inputs uploaded, caches warm): neither wins. Timed without a run of its own
    before it, the candidate run second would win every round it ran second, and lose
    every other: the 75% rule then never lets a real gain past either."""
    import time
    ch = _choice.Choice(("a", "b"), minimum=5, cap=10)
    clock, first = [0.0], [True]
    monkeypatch.setattr(time, "perf_counter", lambda: clock[0])

    def run(c):
        clock[0] += 1.0 if first[0] else 0.7
        first[0] = False
        return c
    for _ in range(30):
        first[0] = True                                  # a new call: its first run is cold
        ch.play(run, set())
    assert ch.winner == "a"
    r = [x / y for x, y in zip(ch.samples["b"], ch.samples["a"])]
    assert max(r) / min(r) < 1.01, r                     # every round timed two warm runs


def test_play_locks_a_clearly_faster_candidate_after_its_confirmation(monkeypatch):
    ch = _choice.Choice(("a", "b"), minimum=5, cap=10, confirm=True)
    clock = _Clock(lambda c, i: 1.0 if c == "a" else 0.6)
    _play(ch, clock, monkeypatch, 30, set())
    assert ch.winner == "b"
    n = len(clock.runs)
    assert _play(ch, clock, monkeypatch, 1, set()) == ["result of b"]
    assert clock.runs[n:] == ["b"]                         # locked: the winner runs once


def test_play_keeps_the_preference_between_equal_candidates(monkeypatch):
    ch = _choice.Choice(("a", "b"), minimum=5, cap=10)
    clock = _Clock(lambda c, i: 1.0 + 0.01 * (i % 3))
    _play(ch, clock, monkeypatch, 30, set())
    assert ch.winner == "a"


def test_a_choice_met_inside_a_play_takes_its_preference_untimed(monkeypatch):
    outer = _choice.Choice(("a", "b"), minimum=5, cap=10)
    inner = _choice.Choice(("x", "y"), minimum=5, cap=10)
    seen = []

    clock = _Clock(lambda c, i: 1.0)

    def run(c):
        seen.append(inner.play(lambda d: d))
        return clock.run(c)
    _play(outer, clock, monkeypatch, 0, set())
    outer.play(run, set())
    assert set(seen) == {"x"} and not any(inner.samples.values())
    assert all(len(v) == 1 for v in outer.samples.values())


def test_play_retrials_a_lock(monkeypatch):
    ch = _choice.Choice(("a", "b"), minimum=5, cap=10, retrial=4)
    ch.lock("b")
    clock = _Clock(lambda c, i: 1.0)
    _play(ch, clock, monkeypatch, 3, {"a", "b"})
    assert clock.runs == ["b"] * 3
    _play(ch, clock, monkeypatch, 1, {"a", "b"})            # the 4th call: a new trial
    assert ch.winner is None and clock.runs[3:] == ["a", "a", "b", "b"]
