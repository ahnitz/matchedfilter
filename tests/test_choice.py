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
    # A decision needs every candidate past the warm-up by `minimum` samples, no sooner:
    # the warm-up samples are not kept.
    assert all(len(v) == ch.minimum for v in ch.samples.values())
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
    assert len(ch.samples["gpu"]) == ch.cap


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


def test_a_choice_needs_distinct_candidates():
    with pytest.raises(ValueError):
        _choice.Choice(("a", "a"))


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


def test_a_persisted_contest_continues_across_processes(monkeypatch, tmp_path):
    """One sample a process: the samples are kept on file, so the contest completes across
    processes as in one long one."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    cost = {"a": 1.0, "b": 0.5}
    for proc in range(20):
        ch = _choice.Choice(("a", "b"), store_key="p", warmup=0, persist=True)
        if ch.winner is not None:
            break
        cand, record = ch.next()
        record(cost[cand])
    assert ch.winner == "b" and proc == 2 * ch.minimum


def test_the_budget_ends_a_contest_whose_samples_never_come(monkeypatch, tmp_path):
    """Attempts that yield no sample still count, across processes: the contest ends at its
    budget, and with nothing to compare the preference stands."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    for proc in range(50):
        ch = _choice.Choice(("a", "b"), store_key="q", persist=True, budget=(2, 1))
        if ch.winner is not None:
            break
        ch.tick()
    assert ch.winner == "a" and proc == 2 * 2 + 1 + 1


def test_at_the_budget_a_clearly_faster_candidate_still_wins():
    ch = _choice.Choice(("a", "b", "c"), warmup=0, minimum=6, budget=(1, 0))
    for _ in range(2):
        ch.record("a", 1.0)
        ch.record("b", 0.5)                    # c never runs
    for _ in range(3):
        ch.tick()
    assert ch.winner is None
    ch.tick()
    assert ch.winner == "b"


def test_at_the_budget_the_preference_stands_when_it_has_too_few_samples():
    ch = _choice.Choice(("a", "b"), warmup=0, budget=(1, 0))
    ch.record("b", 0.1)
    ch.record("b", 0.1)
    for _ in range(3):
        ch.tick()
    assert ch.winner == "a"                    # b was never compared with it


def test_a_lock_another_process_stored_first_is_adopted(monkeypatch, tmp_path):
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    mine = _choice.Choice(("a", "b"), store_key="r", warmup=0, persist=True)
    other = _choice.Choice(("a", "b"), store_key="r", warmup=0, persist=True)
    _drive(other, lambda c, i: 1.0 if c == "a" else 3.0)
    assert other.winner == "a"
    mine.record("a", 3.0)                      # mid-contest: the file's lock is seen
    assert mine.winner == "a"
    _drive(mine, lambda c, i: 3.0 if c == "a" else 1.0)
    assert mine.winner == "a"


def test_a_dropped_candidate_leaves_the_contest():
    ch = _choice.Choice(("a", "b", "c"), warmup=0, minimum=2)
    ch.drop("c")
    seen = _drive(ch, lambda c, i: 1.0 if c == "a" else 0.5)
    assert "c" not in seen and ch.winner == "b"


def test_paired_rounds_decide_and_ignore_unpaired_samples():
    ch = _choice.Choice((False, True), warmup=0, minimum=5, cap=10, paired=True)
    ch.record(True, 0.1)                       # not a round: ignored
    assert ch.samples[True] == []
    for i in range(5):
        ch.round({False: 1.0 + i, True: 0.8 * (1.0 + i)})
    assert ch.winner is True


@pytest.mark.parametrize("kw", [dict(), dict(warmup=2, cap=7), dict(budget=(2, 1)),
                                dict(budget=(50, 0)), dict(paired=True, minimum=3, cap=6)])
def test_a_contest_that_never_resolves_locks_within_its_limit(kw):
    """limit is a bound, not a guess: a contest whose samples never separate (alternating
    0.5/2.0 on both sides, a coin-flip contest) and one whose samples never come both lock
    within it."""
    ch = _choice.Choice(("a", "b"), **kw)
    for i in range(ch.limit):
        if ch.winner is not None:
            break
        if ch.paired:
            ch.round({"a": 1.0 + (i % 2), "b": 2.0 - (i % 2)})
            continue
        if ch.budget is not None:
            if ch.tick() is not None:
                break
            continue                      # an attempt that yields no sample
        cand, record = ch.next()
        record(0.5 if i % 2 else 2.0)
    assert ch.winner is not None, (kw, ch.limit)


def test_a_second_writer_in_an_open_contest_is_reported(monkeypatch, tmp_path):
    """Two processes sampling one open contest overwrite each other's samples: the one that
    finds the record further along than it left it says so, once (decision 7: one file is
    not written by concurrent processes; this is the signal if it is)."""
    import warnings
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    a = _choice.Choice(("x", "y"), store_key="w", warmup=0, minimum=4, persist=True)
    b = _choice.Choice(("x", "y"), store_key="w", warmup=0, minimum=4, persist=True)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        a.record("x", 1.0)                   # a writes first
        a.record("y", 1.0)                   # a alone: no warning
        assert not [x for x in w if "another process" in str(x.message)]
        b.record("x", 2.0)                   # b finds a's samples it never saw
        b.record("y", 2.0)
    hits = [x for x in w if "another process" in str(x.message)]
    assert len(hits) == 1


def test_replacing_another_methods_record_is_not_a_second_writer(monkeypatch, tmp_path):
    """A paired contest replaces an unpaired record it cannot continue; nobody else is
    sampling, so nothing is said."""
    import warnings
    from matchedfilter import gatechain
    from matchedfilter import _costfile
    path = tmp_path / "costs.json"
    monkeypatch.setenv("MF_COST_FILE", str(path))
    _costfile._store_cost(path, "choice|w", {"samples": {"x": [1.0] * 4, "y": [2.0] * 4},
                                             "attempts": 3})
    c = _choice.Choice(("x", "y"), store_key="w", persist=True, paired=True)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        c.round({"x": 1.0, "y": 1.1})
    assert not [x for x in w if "another process" in str(x.message)]


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
