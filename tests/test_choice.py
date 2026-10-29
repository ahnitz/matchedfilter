"""The measured-choice lifecycle (_choice), driven with injected timings: no device, no wall
clock, so every branch is exact and none can flake."""
import json

import numpy as np
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


# ---- the A/A diagnostic (MF_TRIAL_AA_LOG) ----------------------------------------------------

class _Plays:
    """A fake clock for plays that knows each run's arm: at a call's start (begin) it lays
    out the runs the call makes -- every live candidate, and with the diagnostic the A/A arm
    after them, in the order of the round (reversed every round), each a settling run (k 0)
    and a timed run (k 1) -- and each run costs cost(arm, call, k) seconds. A candidate's
    runs then cost the same whether or not the A/A arm runs, and the A/A arm's its own."""

    def __init__(self, cost):
        self.t, self.cost, self.play, self.expect, self.runs = 0.0, cost, 0, [], []

    def begin(self, ch, aa):
        assert not self.expect, "the last call did not make the runs laid out for it"
        live = ch.live()
        arms = live + ["A/A"] if aa else live
        order = arms if len(ch.samples[live[0]]) % 2 == 0 else arms[::-1]
        self.play, self.pref = self.play + 1, ch.preference
        self.expect = [(arm, k) for arm in order for k in (0, 1)]

    def run(self, c):
        arm, k = self.expect.pop(0)
        assert c == (self.pref if arm == "A/A" else arm)
        self.runs.append((self.play, arm, k))
        self.t += self.cost(arm, self.play, k)
        return "result of %s" % c


def _contest(make, cost, monkeypatch, aa, plays=80):
    """Play make()'s choice until it locks (at most `plays` calls). Returns its trace -- per
    call the result, the live candidates, the candidate being confirmed, the winner and every
    sample so far -- and the clock."""
    import time
    clock, ch, trace = _Plays(cost), make(), []
    monkeypatch.setattr(time, "perf_counter", lambda: clock.t)
    while ch.winner is None and clock.play < plays:
        clock.begin(ch, aa)
        res = ch.play(clock.run, set())
        assert not clock.expect
        trace.append((res, tuple(ch.live()), ch.confirming, ch.winner,
                      {c: list(v) for c, v in ch.samples.items()}))
    return trace, clock


def _noise(seed, gains, sd):
    """cost(arm, call, k): an arm's cost (1 - its gain, in units of 1e6 ticks; the A/A
    arm's is the preference's, 1) with log-normal noise of sd `sd` drawn per run, from
    (seed, arm, call, k). Whole ticks: the clock's sums and differences are then exact,
    whatever ran before."""
    names = sorted(gains) + ["A/A"]

    def cost(arm, play, k):
        z = np.random.default_rng([seed, names.index(arm), play, k]).standard_normal()
        return float(round(1e6 * (1.0 - gains.get(arm, 0.0)) * np.exp(sd * z)))
    return cost


def _contests():
    """(candidates, Choice keywords, cost) covering every branch the rule takes: a clear win
    and its confirmation, equal candidates, elimination, the cap, a winner not confirmed,
    and 60 random contests."""
    out = [(("a", "b"), dict(confirm=True), _noise(1, {"a": 0.0, "b": 0.4}, 0.02)),
           (("a", "b", "c"), dict(confirm=True), _noise(2, {"a": 0.0, "b": 0.0, "c": 0.0}, 0.06)),
           (("a", "b", "c", "d"), dict(confirm=True),
            _noise(3, {"a": 0.0, "b": 0.15, "c": -0.3, "d": -0.5}, 0.03)),
           (("a", "b"), dict(), _noise(4, {"a": 0.0, "b": 0.06}, 0.04)),
           (("a", "b", "c"), dict(confirm=True, budget=(0, 3)),
            _noise(5, {"a": 0.0, "b": 0.08, "c": 0.07}, 0.05))]
    rng = np.random.default_rng(11)
    for seed in range(60):
        names = tuple("abcde"[:int(rng.integers(2, 6))])
        gains = {c: 0.0 if c == "a" else float(rng.uniform(-0.2, 0.2)) for c in names}
        out.append((names, dict(confirm=bool(seed % 2)),
                    _noise(100 + seed, gains, float(rng.uniform(0.01, 0.1)))))
    return out


@pytest.mark.parametrize("cands,kw,cost", _contests())
def test_the_aa_arm_changes_no_decision(cands, kw, cost, monkeypatch, tmp_path):
    """The same contest, each candidate's runs timed alike, with and without the A/A
    diagnostic: every call's result, live candidates, confirmation, winner and samples are
    identical, and the A/A arm's timing, which differs from the preference's, is logged."""
    monkeypatch.delenv("MF_TRIAL_AA_LOG", raising=False)
    plain, _ = _contest(lambda: _choice.Choice(cands, **kw), cost, monkeypatch, aa=False)
    log = tmp_path / "aa.jsonl"
    monkeypatch.setenv("MF_TRIAL_AA_LOG", str(log))
    with_aa, clock = _contest(lambda: _choice.Choice(cands, **kw), cost, monkeypatch, aa=True)
    assert with_aa == plain
    rounds = [r for r in map(json.loads, log.read_text().splitlines()) if r["event"] == "round"]
    assert len(rounds) == len(plain) == clock.play
    for play, r in enumerate(rounds, 1):
        assert r["A/A"] == cost("A/A", play, 1) != r["times"]["a"] == cost("a", play, 1)
        assert r["aa_ratio"] == pytest.approx(r["A/A"] / r["times"]["a"])


def test_the_aa_log_holds_every_round_and_the_lock(monkeypatch, tmp_path):
    """One record per round: the order run (the A/A arm last, then first as the order
    reverses), each candidate's timing and ratio to the preference, the A/A arm's, the
    contest's state after the round; and a record of the lock."""
    log = tmp_path / "aa.jsonl"
    monkeypatch.setenv("MF_TRIAL_AA_LOG", str(log))
    cost = _noise(7, {"a": 0.0, "b": 0.4, "c": -0.4}, 0.01)
    trace, _ = _contest(lambda: _choice.choice("demo", 1, ("a", "b", "c"), confirm=True,
                                                store_key="demo|1"), cost, monkeypatch, aa=True)
    recs = [json.loads(x) for x in log.read_text().splitlines()]
    rounds = [r for r in recs if r["event"] == "round"]
    assert len(rounds) == len(trace) and trace[-1][3] == "b"
    assert rounds[0]["order"] == ["a", "b", "c", "A/A"]
    assert rounds[1]["order"] == ["A/A", "c", "b", "a"]
    for r, (_, live, confirming, winner, samples) in zip(rounds, trace):
        assert r["kind"] == "demo" and r["key"] == "demo|1" and r["preference"] == "a"
        assert set(r["times"]) <= set("abc") and len(r["load"]) == 3
        assert r["ratios"] == pytest.approx({c: t / r["times"]["a"] for c, t in r["times"].items()})
        assert r["winner"] == winner and r["confirming"] == confirming
    assert {r["phase"] for r in rounds} == {"contest", "confirm"}
    assert rounds[-1]["phase"] == "confirm" and rounds[-1]["times"].keys() == {"a", "b"}
    locks = [r for r in recs if r["event"] == "lock"]
    assert [(r["value"], r["phase"]) for r in locks] == [("b", "confirm")]


def test_without_the_diagnostic_nothing_is_logged_and_the_preference_runs_once(monkeypatch,
                                                                            tmp_path):
    monkeypatch.delenv("MF_TRIAL_AA_LOG", raising=False)
    monkeypatch.chdir(tmp_path)
    _, clock = _contest(lambda: _choice.Choice(("a", "b")), _noise(8, {"a": 0, "b": 0}, 0.02),
                        monkeypatch, aa=False)
    assert [arm for p, arm, k in clock.runs if p == 1] == ["a", "a", "b", "b"]
    assert list(tmp_path.iterdir()) == []
