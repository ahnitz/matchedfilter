"""Input residency shared by the Vulkan and Metal dispatch caches."""


class Pending:
    """An in-flight dispatch's result, materialized once on first call.

    Returned for async_submit: the caller encodes the next batch while this
    one runs. The context keeps every unfinished one, so evicting or clearing
    cached buffers can finish them first -- a result is read from those
    buffers, and reading one after its release reads freed memory.
    """
    __slots__ = ("ctx", "fn", "result", "done", "stats", "sparse_dev", "owner")

    #: Per-dispatch statistics a finish leaves on the context (last_refinements, ...). A
    #: result can be materialised early -- _drain from timings(), a cache eviction, a slot
    #: reuse -- and in any order, while callers read these attributes when THEY collect
    #: it: each result restores its own values whenever it is returned. Read stale, a
    #: deferred hierarchical call counted 0 refinements and marked itself empty.
    STATS = ("last_refinements", "last_tier1_survivors")

    def __init__(self, ctx, fn, owner=None):
        self.ctx, self.fn, self.result, self.done = ctx, fn, None, False
        self.stats = None
        self.owner = owner
        self.sparse_dev = getattr(fn, "sparse_dev", None)

    def __call__(self):
        if not self.done:
            self.done = True
            self.ctx._inflight.pop(id(self), None)
            if self.owner is not None and self.ctx.__dict__.get("_owned", {}).get(self.owner) is self:
                del self.ctx._owned[self.owner]
            fn, self.fn = self.fn, None
            self.result = fn()
            self.stats = {k: getattr(self.ctx, k) for k in self.STATS if hasattr(self.ctx, k)}
        else:
            for k, v in (self.stats or {}).items():
                setattr(self.ctx, k, v)
        return self.result


class InputUploads:
    def _track(self, fn, owner=None):
        """Register an in-flight readback; see Pending. owner: the output buffers the readback
        reads, so a later call that reuses them collects this result first (_claim)."""
        inflight = self.__dict__.setdefault("_inflight", {})
        pending = Pending(self, fn, None if owner is None else id(owner))
        inflight[id(pending)] = pending
        if owner is not None:
            self.__dict__.setdefault("_owned", {})[id(owner)] = pending
        return pending

    def _claim(self, owner):
        """Collect the in-flight result reading `owner` (output buffers) before a call reuses
        them: writes its inputs, or submits over its outputs. Without this an async result
        read after a same-shaped call returned that call's peaks (CUDA has its own rule,
        _cudacompute._dispatch_result)."""
        pending = self.__dict__.get("_owned", {}).get(id(owner))
        if pending is not None:
            pending()

    def _drain(self):
        """Finish every in-flight dispatch, keeping its result for its caller."""
        for pending in list(self.__dict__.get("_inflight", {}).values()):
            pending()

    def _input_uploads(self, key, data, tmpl, upload_data, upload_tmpl):
        """Invalidate all resident copies when an input changes.

        Each cached storage shape owns its buffers. Clearing a caller's dirty flag
        after one dispatch cannot make the other copies current. Source slices
        also matter: equal shapes need not refer to the same data.

        The backend records the returned signature only after a successful
        write. This bookkeeping never scans or hashes the spectrum contents.
        """
        needed, signatures = [], []
        for name, array, dirty in (("data", data, upload_data),
                                   ("tmpl", tmpl, upload_tmpl)):
            resident = self._uploaded[name]
            if dirty:
                resident.clear()
            signature = (array.ctypes.data, array.shape, array.strides)
            needed.append(resident.get(key) != signature)
            signatures.append(signature)
        return (*needed, *signatures)

    def _write_uploads(self, key, uploads, b_data, data, b_tmpl, tmpl):
        """Write the inputs _input_uploads found stale into their device buffers, and record
        their signatures under key (only after the write succeeded)."""
        from ._shared import write_input
        if uploads[0]:
            write_input(b_data, data)
            self._uploaded["data"][key] = uploads[2]
        if uploads[1]:
            write_input(b_tmpl, tmpl)
            self._uploaded["tmpl"][key] = uploads[3]

    cache_limit_bytes = 512 * 1024 * 1024
    # Recordings are kept per pipelining slot (8 by default) and per chain, and chain trials
    # run several chains: at 32 entries a trialling plan evicted and re-recorded every call
    # (63 buffer allocations per call at n=4096). Memory is bounded by the byte limit.
    cache_limit_entries = 256

    #: Record kind -> the attribute holding that kind's records. Every operation's records
    #: are the shared executor's (_gpuexec), one table on every backend.
    RECORD_TABLES = (('exec', '_exec_records'),)

    def _record_tables(self):
        """{kind: table} for the record tables this context has."""
        return {kind: getattr(self, attr) for kind, attr in self.RECORD_TABLES
                if getattr(self, attr, None) is not None}

    def _evict_all(self):
        """Evict every record through the backend's _evict_record."""
        for kind, table in self._record_tables().items():
            for key in list(table):
                self._evict_record(kind, key)

    @staticmethod
    def _allocation(buf):
        owner = getattr(buf, 'owner', None)
        return owner.buffer if owner is not None else buf

    def _cached_buffers(self):
        """Every buffer a record binds: its own, and callers' shared allocations (which
        _cache_bytes counts only once their caller has let go)."""
        for rec in self.__dict__.get('_exec_records', {}).values():
            yield from rec.buffers.values()

    def _cache_bytes(self, incoming=()):
        """Bytes eviction could free: buffers the cache owns, and borrowed shared
        allocations only once their caller has let go (see _shared._caller_holds). A
        search's middle-stage output, read in place by every fine bank's forward, is
        ~0.5 GB its caller keeps; counted, it filled the budget by itself, and every call
        evicted and re-recorded (100 recordings and 1500 buffer allocations per 8
        segments)."""
        from ._shared import _caller_holds
        allocations = {}
        for buf in (*self._cached_buffers(), *incoming):
            owner = getattr(buf, 'owner', None)
            if owner is not None and _caller_holds(owner):
                continue
            allocation = self._allocation(buf)
            allocations[id(allocation)] = getattr(allocation, 'nbytes', 0)
        return sum(allocations.values())

    def _cache_touch(self, kind, key):
        order = getattr(self, '_cache_order', None)
        if order is None:
            order = self._cache_order = {}
        token = (kind, key)
        order.pop(token, None)
        order[token] = None

    def _cache_room(self, estimate, *, incoming=(), keep_storage=None):
        """Evict least-recently used records until estimate more bytes fit the budget,
        counting shared allocations once. A single oversized operation is still permitted;
        the budget bounds retained work. Incoming shared buffers stay counted even if their
        last old record is evicted while making room."""
        order = getattr(self, '_cache_order', {})
        while order:
            if (len(order) < self.cache_limit_entries
                    and self._cache_bytes(incoming) + estimate <= self.cache_limit_bytes):
                break
            kind, key = next(iter(order))
            order.pop((kind, key))
            self._evict_record(kind, key, keep_storage)
