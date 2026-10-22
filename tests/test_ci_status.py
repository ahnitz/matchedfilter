"""tools/ci_status.py's verdicts, on synthetic API records: no network."""
import datetime
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "ci_status", Path(__file__).resolve().parents[1] / "tools" / "ci_status.py")
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)

NOW = datetime.datetime(2026, 10, 21, 12, tzinfo=datetime.timezone.utc)


def run(name="CI", status="completed", conclusion="success", created="2026-10-21T10:00:00Z",
        attempt=1, branch="main", sha="a" * 40):
    return dict(name=name, status=status, conclusion=conclusion, created_at=created,
                run_attempt=attempt, head_branch=branch, head_sha=sha, id=1, html_url="u")


@pytest.mark.parametrize("status,conclusion,want", [
    ("completed", "success", "green"), ("completed", "failure", "red"),
    ("completed", "cancelled", "red"), ("completed", "timed_out", "red"),
    ("completed", "startup_failure", "red"), ("in_progress", None, "unknown"),
    ("queued", None, "unknown")])
def test_a_run_is_green_only_when_it_succeeded(status, conclusion, want):
    assert ci.verdict(run(status=status, conclusion=conclusion)) == want


def test_the_latest_attempt_of_each_workflow_is_judged():
    old = run(conclusion="failure", created="2026-10-20T10:00:00Z")
    rerun = run(conclusion="success", created="2026-10-20T10:00:00Z", attempt=2)
    bench = run(name="Benchmark", conclusion="failure")
    got = ci.latest_per_workflow([old, rerun, bench])
    assert [(r["name"], r["conclusion"]) for r in got] == [("Benchmark", "failure"), ("CI", "success")]


@pytest.mark.parametrize("cron,days", [("0 6 * * 1", 7), ("17 3 * * *", 1), ("0 0 1 * *", 31)])
def test_schedule_periods(cron, days):
    assert ci.schedule_period(cron) == days * 86400


def test_a_schedule_that_stopped_running_is_red():
    week = ci.schedule_period("0 6 * * 1")
    fresh = run(name="Benchmark", created="2026-10-19T06:00:00Z")
    stale = run(name="Benchmark", created="2026-10-01T06:00:00Z")      # 20 days: > 2 weeks + 6 h
    assert ci.schedule_verdict(fresh, week, NOW)[0] == "green"
    assert ci.schedule_verdict(stale, week, NOW)[0] == "red"
    assert ci.schedule_verdict(None, week, NOW)[0] == "unknown"
    failed = run(name="Benchmark", conclusion="failure", created="2026-10-19T06:00:00Z")
    assert ci.schedule_verdict(failed, week, NOW)[0] == "red"


def test_a_red_schedule_is_cleared_only_by_a_newer_green_proof_of_the_same_workflow():
    red = run(name="Benchmark", conclusion="failure", created="2026-10-19T06:00:00Z")
    proof = run(name="Benchmark", created="2026-10-21T08:00:00Z", branch="ci/bench/a1")
    assert ci.cleared_by(red, [proof]) is proof
    assert ci.cleared_by(red, [dict(proof, conclusion="failure")]) is None        # not green
    assert ci.cleared_by(red, [dict(proof, created_at="2026-10-18T00:00:00Z")]) is None  # older
    assert ci.cleared_by(red, [dict(proof, name="CI")]) is None                   # other workflow
    assert ci.cleared_by(red, [dict(proof, head_branch="main")]) is None          # not a proof


def test_the_worst_verdict_wins():
    assert ci._worse("green", "unknown") == "unknown"
    assert ci._worse("unknown", "red") == "red"
    assert ci._worse("red", "green") == "red"


def test_the_scheduled_workflows_are_read_from_the_repository():
    got = ci.scheduled_workflows(Path(__file__).resolve().parents[1])
    assert got.get("Benchmark") == "0 6 * * 1"
