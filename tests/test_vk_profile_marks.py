"""Phase marks (MF_GPU_PROFILE) are read only from queries a submitted run writes.

A read waits for its query (VK_QUERY_RESULT_WAIT_BIT), and RADV answered a wait on a query
nothing would write with VK_ERROR_DEVICE_LOST. Two ways led there, both on the first call of
a profiled ladder: a submission listing a new recording before reading one it ran again, and
a recording begun under a freed one's handle inheriting its marks. No GPU: a context with a
query pool whose unwritten queries fail as RADV's did.
"""
import weakref

import pytest

from matchedfilter import _gputime, _vkcompute


class _Queries:
    """vkGetQueryPoolResults over a pool where `written` queries hold their index."""

    def __init__(self, written):
        self.written = set(written)
        self.read = []

    def vkGetQueryPoolResults(self, device, pool, q, count, size, out, stride, flags):
        self.read.append(q)
        if q not in self.written:
            return -4                             # VK_ERROR_DEVICE_LOST
        out._obj.value = q
        return 0


def _context(written, marks, pending):
    ctx = object.__new__(_vkcompute.Context)
    ctx.vk = _Queries(written)
    ctx.device = None
    ctx._ts_period = 1.0
    ctx.timing_log = []
    ctx._prof = dict(pool=None, next=len(marks), marks=dict(marks), pending=list(pending))
    ctx.reset = []
    ctx._reset_query = lambda device, pool, q, count: ctx.reset.append(q)
    return ctx


def test_a_recording_run_again_is_read_before_its_submission_lists_another():
    """A deferred forward (B, new) ahead of a recording run again (A): A's earlier run is
    read first, and B, listed but not yet submitted, is never waited on."""
    ctx = _context({0, 1}, {"A": [(0, "start"), (1, "forward")],
                            "B": [(2, "start"), (3, "forward")]}, ["A"])
    ctx._profile_submitted(["B", "A"])
    assert ctx.vk.read == [0, 1]
    assert ctx.timing_log == [("k:forward", pytest.approx(1e-6))]
    assert sorted(ctx._prof["pending"]) == ["A", "B"]
    assert sorted(ctx.reset) == [0, 1, 2, 3]       # each reset for the run it is about to get


def test_a_buffer_begun_under_a_freed_ones_handle_has_none_of_its_marks(monkeypatch):
    """A trig probe's forward, stamped and freed with its cache, handed its handle to a
    correlation with no stamps. The new buffer must not wait on the probe's queries; the
    probe's own run, finished, is read before its marks go."""
    ctx = _context({0, 1}, {"H": [(0, "start"), (1, "forward")]}, ["H"])
    monkeypatch.setattr(_gputime, "_CONTEXTS", weakref.WeakSet([ctx]))
    _vkcompute._profile_forget("H")
    assert "H" not in ctx._prof["marks"] and ctx._prof["pending"] == []
    assert ctx.timing_log == [("k:forward", pytest.approx(1e-6))]
    ctx.vk.written.clear()                        # the new buffer writes no query
    ctx._profile_submitted(["H"])
    ctx._profile_resolve()
    assert ctx.vk.read == [0, 1] and ctx._prof["pending"] == []
