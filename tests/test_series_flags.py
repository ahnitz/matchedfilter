"""The series-call flags a bank sets on its plans (MatchedFilter._series_flags): set for each
call the bank makes and cleared when the call returns, however it returns.

A flag left set changes the plan's next call made by anyone else: a hierarchical plan's raw
call at a threshold returns sparse peaks (_SparsePeaks) instead of its dense table, and a GPU
plan defers its call and keys its recorded call plans on the flags. These tests run on the
CPU; the GPU's deferred and replayed calls are covered by test_call_plan and
test_followup_batch.
"""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from matchedfilter._results import _SparsePeaks
from matchedfilter.time_domain import _normalize_windows
from test_time_domain_windows import S, _analytic, _bank


@pytest.fixture(autouse=True)
def _pinned_configuration(monkeypatch):
    monkeypatch.setenv("MF_AUTOTUNE", "0")


def _flags(plan):
    return plan._defer_series, plan._want_sparse


def _spy_flags(monkeypatch, plan, seen, fail=False):
    """Record the flags each run_series call of plan's class sees; with fail, raise after."""
    cls = type(plan)
    orig = cls.run_series

    def spy(self, *a, **k):
        seen.append(_flags(self))
        if fail:
            raise RuntimeError("the plan's call failed")
        return orig(self, *a, **k)

    monkeypatch.setattr(cls, "run_series", spy)


@pytest.mark.parametrize("engine", ["matchedfilter", "hier"])
@pytest.mark.parametrize("batched", [False, True])
def test_flags_are_set_for_the_banks_call_and_cleared_after(engine, batched, monkeypatch):
    """The bank's call sees sparse asked for, and deferral asked for exactly when it is part
    of a filter_series_many batch (the batch's token); afterwards both flags are False."""
    bank = _bank(engine)
    plan = bank._groups[0].plan
    seen = []
    _spy_flags(monkeypatch, plan, seen)
    ser = _analytic(21)
    if batched:
        res = TimeDomainFilterBank.filter_series_many([(bank, ser, {})])[0]
    else:
        res = bank.filter_series(ser)
    assert len(res.snr) > 0
    assert seen and all(want_sparse is True for _, want_sparse in seen)
    if batched:
        assert all(defer for defer, _ in seen), seen
    else:
        assert all(defer is False for defer, _ in seen), seen
    for g in bank._groups:
        assert _flags(g.plan) == (False, False)


@pytest.mark.parametrize("batched", [False, True])
def test_flags_are_cleared_when_the_call_raises(batched, monkeypatch):
    bank = _bank("hier")
    plan = bank._groups[0].plan
    seen = []
    _spy_flags(monkeypatch, plan, seen, fail=True)
    ser = _analytic(22)
    with pytest.raises(RuntimeError, match="the plan's call failed"):
        if batched:
            TimeDomainFilterBank.filter_series_many([(bank, ser, {})])
        else:
            bank.filter_series(ser)
    assert seen and seen[0][1] is True and bool(seen[0][0]) is batched
    assert _flags(plan) == (False, False)


def test_a_plans_own_call_after_a_bank_call_is_dense():
    """A hierarchical plan's raw call at a threshold returns its dense (index, value) table,
    the same before and after the bank has called the plan (sparse) in a batch."""
    bank = _bank("hier")
    g = bank._groups[0]
    plan = g.plan
    ser = _analytic(23)
    starts, ws, we = TimeDomainFilterBank._window_layout(g, _normalize_windows(None, S), S)

    def direct():
        res = plan.run_series(ser, starts, ws, we, binsize=g.n, threshold=bank.threshold,
                              raw=True)
        assert not isinstance(res, _SparsePeaks)
        idx, val = res
        return np.array(idx), np.array(val)

    before = direct()
    assert (before[0] >= 0).sum() > 0          # peaks above the threshold, not an empty table
    TimeDomainFilterBank.filter_series_many([(bank, ser, {})])
    after = direct()
    np.testing.assert_array_equal(before[0], after[0])
    np.testing.assert_array_equal(before[1], after[1])
