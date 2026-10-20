"""Cache budgets count physical allocations and evict only enough LRU entries."""
from types import SimpleNamespace
import pytest
from matchedfilter._gpu_cache import InputUploads
from matchedfilter._gpuexec import Executor, Record


def _rec(*buffers):
    """A record binding these buffers (its own and callers' alike, as _cached_buffers sees)."""
    r = Record()
    r.buffers = {i: b for i, b in enumerate(buffers)}
    return r


class Cache(Executor, InputUploads):
    def __init__(self):
        self._exec_records = {}
        self.evicted = []

    def _exec_evict(self, key, done=False):
        self.evicted.append(key)
        self._exec_records.pop(key)


def test_shared_allocation_counted_once_including_incoming_prefix():
    c = Cache()
    physical = SimpleNamespace(nbytes=4096)
    owner = SimpleNamespace(buffer=physical)
    a, b = SimpleNamespace(owner=owner), SimpleNamespace(owner=owner)
    c._exec_records = {0: _rec(a, SimpleNamespace(nbytes=16)), 1: _rec(b, SimpleNamespace(nbytes=32))}
    assert c._cache_bytes((SimpleNamespace(owner=owner),)) == 4096+16+32


def test_lru_preserves_recent_records_and_incoming_budget():
    c = Cache()
    for i in range(3):
        c._exec_records[i] = _rec(SimpleNamespace(nbytes=100))
        c._cache_touch(i)
    c._cache_touch(0)
    c.cache_limit_bytes = 350
    c._cache_room(25, incoming=(SimpleNamespace(nbytes=100),))
    assert c.evicted == [1]
    assert set(c._exec_records) == {0, 2}


def test_entry_cap_is_independent_of_byte_budget():
    c = Cache()
    c.cache_limit_entries = 2
    for i in range(2):
        c._exec_records[i] = _rec(SimpleNamespace(nbytes=1))
        c._cache_touch(i)
    c._cache_room(1)
    assert c.evicted == [0]


@pytest.mark.parametrize("byte_limit,entry_limit,expected", [
    (250, 99, ["older", "newer"]),      # bytes alone need two removals
    (1000, 3, ["older"]),              # reserve one entry for the new record
    (250, 3, ["older", "newer"]),      # both limits apply
])
def test_active_consumer_protects_held_lru_record(byte_limit, entry_limit, expected):
    """A new recording may evict neighbors, never the input record its consumer binds."""
    c = Cache()
    for key in ("forward", "older", "newer"):
        c._exec_records[key] = _rec(SimpleNamespace(nbytes=100))
        c._cache_touch(key)
    c._exec_hold = {"forward"}
    c.cache_limit_bytes, c.cache_limit_entries = byte_limit, entry_limit
    c._exec_room(100)
    assert c.evicted == expected
    assert "forward" in c._exec_records
    assert list(c._exec_records) == [k for k in ("forward", "older", "newer")
                                    if k not in expected]


def test_all_held_records_survive_pressure_then_become_evictable():
    """Active work may temporarily exceed a soft budget; releasing it restores eviction."""
    c = Cache()
    for key in ("first", "second"):
        c._exec_records[key] = _rec(SimpleNamespace(nbytes=100))
        c._cache_touch(key)
    c._exec_hold = {"first", "second"}
    c.cache_limit_bytes, c.cache_limit_entries = 50, 1
    c._exec_room(100)
    assert c.evicted == []
    assert list(c._exec_records) == ["first", "second"]

    c._exec_hold.remove("second")
    c._exec_room(100)
    assert c.evicted == ["second"]
    assert list(c._exec_records) == ["first"]

    c._exec_hold.clear()
    c._exec_room(100)
    assert c.evicted == ["second", "first"]
    assert not c._exec_records


def test_incoming_shared_allocation_stays_counted_after_its_old_record_is_evicted():
    """Evicting the last cached view cannot free storage the incoming operation binds."""
    c = Cache()
    physical = SimpleNamespace(nbytes=100)
    owner = SimpleNamespace(buffer=physical)
    incoming = SimpleNamespace(owner=owner)
    c._exec_records["old-view"] = _rec(SimpleNamespace(owner=owner))
    c._exec_records["scratch"] = _rec(SimpleNamespace(nbytes=40))
    for key in c._exec_records:
        c._cache_touch(key)
    c.cache_limit_bytes = 125
    c._exec_room(25, incoming=(incoming,))
    assert c.evicted == ["old-view", "scratch"]
    assert c._cache_bytes((incoming,)) == 100


def test_caller_held_shared_allocation_is_not_counted():
    """A shared allocation its caller still holds is not in the budget (eviction cannot
    free it); once the caller lets go, the borrowing records are what keep it, and it counts.
    Counting a search's ~0.5 GB middle output made every fine call evict and re-record."""
    import weakref

    class Storage:
        pass
    c = Cache()
    storage = Storage()
    owner = SimpleNamespace(buffer=SimpleNamespace(nbytes=4096), _storage=weakref.ref(storage))
    c._exec_records = {0: _rec(SimpleNamespace(owner=owner), SimpleNamespace(nbytes=16)),
                       1: _rec(SimpleNamespace(owner=owner), SimpleNamespace(nbytes=32))}
    incoming = SimpleNamespace(owner=owner)
    for key in c._exec_records:
        c._cache_touch(key)
    c.cache_limit_bytes = 64
    assert c._cache_bytes((incoming,)) == 48
    c._exec_room(16, incoming=(incoming,))
    assert not c.evicted

    del storage
    assert c._cache_bytes((incoming,)) == 4096 + 48
    c._exec_room(16, incoming=(incoming,))
    assert c.evicted == [0, 1]
    assert c._cache_bytes((incoming,)) == 4096
