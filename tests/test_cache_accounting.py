"""Cache budgets count physical allocations and evict only enough LRU entries."""
from types import SimpleNamespace
from matchedfilter._gpu_cache import InputUploads
from matchedfilter._gpuexec import Record


def _rec(*buffers):
    """A record binding these buffers (its own and callers' alike, as _cached_buffers sees)."""
    r = Record()
    r.buffers = {i: b for i, b in enumerate(buffers)}
    return r


class Cache(InputUploads):
    def __init__(self):
        self._exec_records = {}
        self.evicted = []

    def _evict_record(self, kind, key, keep_storage=None):
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
        c._cache_touch('exec', i)
    c._cache_touch('exec', 0)
    c.cache_limit_bytes = 350
    c._cache_room(25, incoming=(SimpleNamespace(nbytes=100),))
    assert c.evicted == [1]
    assert set(c._exec_records) == {0, 2}


def test_entry_cap_is_independent_of_byte_budget():
    c = Cache()
    c.cache_limit_entries = 2
    for i in range(2):
        c._exec_records[i] = _rec(SimpleNamespace(nbytes=1))
        c._cache_touch('exec', i)
    c._cache_room(1)
    assert c.evicted == [0]


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
    c._exec_records = {0: _rec(SimpleNamespace(owner=owner), SimpleNamespace(nbytes=16))}
    assert c._cache_bytes() == 16
    del storage
    assert c._cache_bytes() == 4096 + 16
