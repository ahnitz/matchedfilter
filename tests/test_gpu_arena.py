"""A search's buffer arena (_gpuhost.Arena and ArenaLease): sections laid out per lease and
recycled across leases, and nothing that outlives a lease mistaking a recycled section for its
previous tenant.

Each recycle test runs on the simulated driver (tests/sim_driver.py) as a device whose host sees
device memory in place, as one whose host does not (whose arena holds device-only scratch only,
as CUDA's) and as one that orders work by allocation (whose arena gives each section a block of
its own, as Metal's), and on the host's GPU; each checks its property through the device (sections
written and read by kernels), and, where the arena holds host-addressed arrays, through them
too. The search tests need a GPU: they compare a search's peaks after another search has used the arena
with its peaks without an arena.
"""
import gc
import weakref

import numpy as np
import pytest

import sim_driver
from conftest import gpu_backend, gpu_context
from matchedfilter import _gpuhost, _gpuroot
from matchedfilter._gpuexec import Record
from matchedfilter._gpuhost import ARENA_BLOCK, Arena, binding_key
from test_driver_conformance import _read, _upload

N = 1024


class _Device:
    """make() -> a context on one device (a simulated one, or the host's GPU); arena() -> an
    Arena on that device with a context of its own. Everything is destroyed at the end."""

    def __init__(self, backend, props=None):
        self.backend, self.made = backend, []
        self.dev = sim_driver._Device() if backend == "sim" else None
        if props is not None:
            self.dev.props = sim_driver.stated_props(**props)

    def make(self):
        ctx = (sim_driver.Context(device=self.dev) if self.backend == "sim"
               else gpu_context(self.backend))
        self.made.append(ctx)
        return ctx

    def arena(self):
        arena = Arena(self.make())
        self.arenas = getattr(self, "arenas", []) + [arena]
        return arena

    def close(self):
        for arena in getattr(self, "arenas", ()):
            arena.release()
        for ctx in self.made:
            ctx._x_idle()
            ctx.destroy()


@pytest.fixture(params=["sim", "sim-device-only", "sim-allocation-hazards", "device"])
def device(request):
    """The simulated driver as a device whose host sees device memory in place (its arena
    holds every kind and host arrays), as one whose host does not (unified_memory False, as
    CUDA: its arena holds device-only scratch only), and as one that orders work by
    allocation (allocation_hazards, as Metal: its arena gives each section a block of its
    own); and the host's GPU."""
    if request.param == "device":
        dev = _Device(gpu_backend())
    elif request.param == "sim-device-only":
        dev = _Device("sim", props=dict(unified_memory=False))
    elif request.param == "sim-allocation-hazards":
        dev = _Device("sim", props=dict(allocation_hazards=True))
    else:
        dev = _Device("sim")
    yield dev
    dev.close()


@pytest.fixture
def sim():
    dev = _Device("sim")
    yield dev
    dev.close()


def _series(ctx, rng, size):
    """A complex series in ctx's shared memory, filled from rng."""
    ser = ctx.empty_shared((size,))
    ser[:] = (rng.standard_normal(size) + 1j * rng.standard_normal(size)).astype(np.complex64)
    return ser


def _want(series, starts):
    """Each block's forward transform, normalised by 1/N (zero past the series' end)."""
    out = np.zeros((len(starts), N), np.complex128)
    for i, s in enumerate(starts):
        block = np.zeros(N, np.complex128)
        part = series[s:s + N]
        block[:part.size] = part
        out[i] = np.fft.fft(block) / N
    return out


def _check(spectra, series, starts, tolerance=2e-6):
    """Spectra against each block's transform, to `tolerance` of the largest: 2e-6, or 1e-4
    for spectra read back through the device (two more transforms there)."""
    want = _want(series, starts)
    np.testing.assert_allclose(spectra, want, rtol=0, atol=tolerance * np.abs(want).max())


class _Blocks:
    """A series and block starts in device memory of ctx's own (upload buffers, outside any
    arena), and a recorded list writing their forward transforms into a given buffer or arena
    section (write): the device path, which every arena holds, where the host may not
    address the section."""

    def __init__(self, ctx, rng, starts):
        self.ctx = ctx
        self.starts = np.asarray(starts, np.uint32)
        self.nser = int(self.starts.max()) + 2 * N
        self.x = (rng.standard_normal(self.nser)
                  + 1j * rng.standard_normal(self.nser)).astype(np.complex64)
        self.series_buffer = _upload(ctx, self.x)
        self.starts_buffer = _upload(ctx, self.starts)

    def write(self, out):
        """A recorded list (between barriers) writing each block's transform into a row of
        `out`; the caller runs and releases it."""
        lst = self.ctx._x_list("arena test writer")
        lst.barrier()
        lst.dispatch(self.ctx._x_kernel("forward", N), len(self.starts),
                     [self.series_buffer, self.starts_buffer, out], (self.nser, 0))
        lst.barrier()
        return lst.end()

    def free(self):
        self.ctx._x_free(self.series_buffer)
        self.ctx._x_free(self.starts_buffer)


def _read_back(ctx, buf, rows):
    """The first `rows` rows of N complex values in `buf` (a buffer or an arena section the
    host may not address), read through the device: each row's forward transform, written by
    ctx into a readback buffer of its own and inverted on the host."""
    starts = _upload(ctx, np.arange(rows, dtype=np.uint32) * N)
    out = ctx._x_alloc(rows * N * 8, readback=True)
    lst = ctx._x_list("arena test reader")
    lst.barrier()
    lst.dispatch(ctx._x_kernel("forward", N), rows, [buf, starts, out], (rows * N, 0))
    lst.barrier()
    lst.readback(out, rows * N * 8)
    native = lst.end()
    ctx._x_run(native, True)
    ctx._x_release(native, done=True)
    transforms = _read(ctx, out, np.complex64, rows * N).reshape(rows, N)
    ctx._x_free(out)
    ctx._x_free(starts)
    return np.fft.ifft(transforms.astype(np.complex128) * N, axis=1)


def _fill(ctx, buf, word):
    """Fill a buffer or section with a 32-bit word through the device, finished."""
    lst = ctx._x_list("arena test fill")
    lst.barrier()
    lst.fill(buf, word)
    lst.barrier()
    native = lst.end()
    ctx._x_run(native, True)
    ctx._x_release(native, done=True)


def _owning(ctx, lease):
    """The keys of ctx's records that own a section of `lease`."""
    return [key for key, rec in ctx._exec_table().items()
            if any(getattr(rec.buffers[name], "lease", None) is lease for name in rec.owned)]


def test_a_lease_lays_out_aligned_sections_and_the_next_lease_reuses_its_blocks(sim):
    """Sections are taken from the arena's blocks at multiples of its alignment; a new lease
    starts the blocks again from the start, so taking what an earlier lease took allocates
    nothing; a request no block has room for adds one block of at least ARENA_BLOCK bytes."""
    ctx, arena = sim.make(), sim.arena()
    lease = arena.begin()
    first = [lease.take(ctx, nbytes) for nbytes in (100, 4096, 3 << 20)]
    assert [s.offset for s in first] == [0, 256, 256 + 4096]
    assert all(s.base is first[0].base for s in first) and arena.made == 1
    assert arena.capacity() == ARENA_BLOCK
    lease.end()
    lease = arena.begin()
    again = [lease.take(ctx, nbytes) for nbytes in (100, 4096, 3 << 20)]
    assert [(s.base, s.offset) for s in again] == [(s.base, s.offset) for s in first]
    assert arena.made == 1
    big = lease.take(ctx, ARENA_BLOCK)
    assert arena.made == 2 and big.base is not first[0].base and big.offset == 0
    lease.end()
    assert arena.leases == 2 and arena.lease is None


def test_a_device_that_orders_work_by_allocation_gets_a_block_per_section():
    """Where the device orders work by allocation (allocation_hazards, as Metal), every
    section is a block of its own: the smallest free block that holds it at no more than
    twice its size, else a new block of its size; a later lease taking the same sizes in
    another order makes no block, and a section never lies in a block more than twice its
    size."""
    dev = _Device("sim", props=dict(allocation_hazards=True))
    try:
        ctx, arena = dev.make(), dev.arena()
        sizes = (100, 4096, 3 << 20, 4096)
        lease = arena.begin()
        first = [lease.take(ctx, nbytes) for nbytes in sizes]
        assert [s.offset for s in first] == [0] * 4
        assert len({id(s.base) for s in first}) == 4 and arena.made == 4
        assert [s.base.nbytes for s in first] == [256, 4096, 3 << 20, 4096]
        lease.end()
        lease = arena.begin()
        again = [lease.take(ctx, nbytes) for nbytes in reversed(sizes)]
        assert arena.made == 4, "a lease of the same sizes made a block"
        assert sorted(id(s.base) for s in again) == sorted(id(s.base) for s in first)
        small = lease.take(ctx, 300)        # no free block within twice its size
        assert arena.made == 5 and small.base.nbytes == 512
        lease.end()
        lease = arena.begin()
        tiny = lease.take(ctx, 16)          # the 256-byte block, not the 512-byte one
        assert tiny.base is first[0].base
        lease.end()
    finally:
        dev.close()


def test_one_lease_is_in_force_at_a_time(sim):
    """While a lease is in force on its device, begin() gives no second one (a search run
    from another's hook allocates as before), and a context's records take sections only
    from the lease in force."""
    arena = sim.arena()
    lease = arena.begin()
    assert arena.begin() is None
    assert arena.ctx._device_state.arena_lease is lease
    lease.end()
    assert arena.ctx._device_state.arena_lease is None
    with pytest.raises(RuntimeError):
        lease.take(arena.ctx, 16)
    assert arena.begin() is not None


def test_a_search_keeps_its_lease_between_runs(sim):
    """A lease suspended at the end of its owner's run stays the owner's: no section is taken
    from it outside a run, its tenants keep their records, and the owner's next run resumes
    it (nothing to re-record). Another owner's begin ends it, releasing those records."""
    class Search:
        pass
    first, second = Search(), Search()
    ctx, arena = sim.make(), sim.arena()
    rng = np.random.default_rng(5)
    ser = _series(ctx, rng, 2 * N)
    lease = arena.begin(first)
    spectra = lease.array(ctx, (1, N))
    ctx.forward(N, ser, np.array([3], np.uint32), spectra)
    records = dict(ctx._exec_table())
    lease.suspend()
    assert ctx._device_state.arena_lease is None and lease.live
    assert arena.begin(first) is lease and arena.leases == 1
    ctx.forward(N, ser, np.array([3], np.uint32), spectra)
    assert dict(ctx._exec_table()) == records, "a resumed lease re-recorded"
    lease.suspend()
    other = arena.begin(second)
    assert other is not lease and not lease.live and arena.leases == 2
    assert not ctx._exec_table(), "the ended lease's records were kept"
    other.end()


def test_a_recycled_section_is_named_afresh(sim):
    """The same bytes of the same block, taken in two leases, are two sections with serials
    of their own, so a binding cache cannot take the second for the first; a host array over
    them is a new shared allocation with a serial of its own."""
    from matchedfilter._shared import allocation_serial
    ctx, arena = sim.make(), sim.arena()
    lease = arena.begin()
    a = lease.take(ctx, 4096)
    arr = lease.array(ctx, (4,), np.complex64)
    serial = allocation_serial(arr)
    key, addr = binding_key(a), arr.ctypes.data
    lease.end()
    lease = arena.begin()
    b = lease.take(ctx, 4096)
    arr2 = lease.array(ctx, (4,), np.complex64)
    assert (b.base, b.offset) == (a.base, a.offset) and binding_key(b) != key
    assert arr2.ctypes.data == addr and allocation_serial(arr2) != serial
    lease.end()


def test_a_section_given_back_within_a_lease_is_reused(sim):
    """A record evicted during a search gives its sections back to the lease, and the next
    request of the same kind and size takes the same bytes: re-recording within a search
    does not grow the arena."""
    ctx, arena = sim.make(), sim.arena()
    rng = np.random.default_rng(1)
    ser = _series(ctx, rng, 4 * N)
    lease = arena.begin()
    spectra = lease.array(ctx, (3, N))
    starts = np.array([0, 700, 3000], np.uint32)
    ctx.forward(N, ser, starts, spectra)               # staged starts: a record owns them
    owned = [rec.buffers[name] for rec in ctx._exec_table().values() for name in rec.owned]
    assert owned and all(b.lease is lease for b in owned)
    place = [(b.base, b.offset) for b in owned]
    ctx._exec_clear()
    ctx.forward(N, ser, starts, spectra)
    again = [rec.buffers[name] for rec in ctx._exec_table().values() for name in rec.owned]
    assert [(b.base, b.offset) for b in again] == place
    _check(spectra, ser, starts)
    lease.end()


def test_a_device_without_host_visible_memory_leases_device_scratch_only():
    """Where the host does not see device memory in place (unified_memory False: CUDA), the
    arena holds device-only scratch; buffers the host reads back or writes stay buffers of
    their own, and no host array is made over the arena."""
    dev = _Device("sim", props=dict(unified_memory=False))
    try:
        ctx, arena = dev.make(), dev.arena()
        assert arena.holds() and not arena.holds(readback=True) and not arena.holds(upload=True)
        lease = arena.begin()
        rec = Record()
        assert ctx._exec_buffer(rec, "s", nbytes=64).lease is lease
        assert getattr(ctx._exec_buffer(rec, "r", nbytes=64, readback=True), "lease",
                       None) is None
        assert getattr(ctx._exec_buffer(rec, "u", nbytes=64, upload=True), "lease",
                       None) is None
        with pytest.raises(ValueError):
            lease.array(ctx, (4,))
        for name in ("r", "u"):
            ctx._x_free(rec.buffers[name])
        lease.end()
    finally:
        dev.close()


def test_work_held_from_an_ended_lease_never_writes_the_next_tenants_bytes(device):
    """Work deferred into a lease's section and never run is dropped when the lease ends:
    the context's next run on that slot, after the next lease has given the same bytes to
    another tenant, leaves that tenant's values as they are (claimed by address, or run first
    on its slot, the old work would have written them). On every arena with device-only
    sections written and read through the device; where the arena holds host-addressed
    arrays, also with a forward deferred into a lease's spectra array (a plan's slots)."""
    ctx, other = device.make(), device.make()
    rng = np.random.default_rng(2)
    blocks = _Blocks(ctx, rng, [0, 1500])
    arena = device.arena()
    lease = arena.begin()
    held = lease.take(ctx, 2 * N * 8)
    held_native = blocks.write(held)
    ctx._defer(held_native, {}, 0, None)
    lease.end()
    assert not ctx._pending()
    lease = arena.begin()
    theirs = lease.take(other, 2 * N * 8)
    assert (theirs.base, theirs.offset) == (held.base, held.offset)
    _fill(other, theirs, 0)
    mine = lease.take(ctx, 2 * N * 8)
    native = blocks.write(mine)
    ctx._exec_run(native, True, {}, 0)
    ctx._x_idle()
    assert not np.any(_read_back(other, theirs, 2)), \
        "work held from an ended lease wrote the next tenant's section"
    _check(_read_back(ctx, mine, 2), blocks.x, blocks.starts, 1e-4)
    lease.end()
    for nat in (held_native, native):
        ctx._x_release(nat, done=True)
    blocks.free()
    if not arena.holds(upload=True):
        return
    # host-addressed spectra: a forward deferred by MatchedFilter's path (forward(defer=True))
    arena = device.arena()
    ser = _series(ctx, rng, 4 * N)
    # starts in shared memory, bound in place: the forward's record owns nothing of the
    # lease, so only the lease's end dropping held work keeps the forward from running later
    starts = ctx.empty_shared((2,), np.uint32)
    starts[:] = [0, 1500]
    lease = arena.begin()
    spectra = lease.array(ctx, (2, N))
    ctx.forward(N, ser, starts, spectra, defer=True, slot=0)
    addr = spectra.ctypes.data
    lease.end()
    assert not ctx._pending()
    lease = arena.begin()
    theirs = lease.array(other, (2, N))
    assert theirs.ctypes.data == addr
    theirs[:] = 7.0
    mine = lease.array(ctx, (2, N))
    ctx.forward(N, ser, starts, mine, slot=0)
    ctx._x_idle()
    assert np.all(theirs == 7.0), "a forward of an ended lease wrote the next tenant's bytes"
    _check(mine, ser, starts)
    lease.end()


def test_outputs_after_a_recycle_are_the_new_tenants(device, monkeypatch):
    """Two contexts take turns over three leases, each with its own series and block starts,
    on sections the earlier leases used (filled with NaN when handed out, so nothing reads
    bytes no one wrote): every output is its own inputs' transforms, and the records of an
    ended lease are released. On every arena with records owning device-only sections,
    written and read through the device; where the arena holds host-addressed arrays, also
    with forwards into a lease's spectra arrays."""
    monkeypatch.setattr(Arena, "poison", True)
    ctxs = [device.make(), device.make()]
    rng = np.random.default_rng(3)
    firsts = ([0, 900, 4000], [10, 2000, 5100])
    arena = device.arena()
    made = []
    for turn in range(3):
        lease = arena.begin()
        order = (0, 1) if turn % 2 == 0 else (1, 0)
        got = []
        for i in order:
            ctx = ctxs[i]
            blocks = _Blocks(ctx, rng, np.array(firsts[i]) + turn * 37)
            # a record owning a section of the lease, as an executor operation's scratch
            rec = Record()
            out = ctx._exec_buffer(rec, "out", nbytes=3 * N * 8)
            assert out.lease is lease
            rec.native = blocks.write(out)
            ctx._exec_table()[("arena test", turn)] = rec
            ctx._exec_run(rec.native, True, {}, 0)
            got.append((ctx, out, blocks))
        for ctx, out, blocks in got:
            _check(_read_back(ctx, out, 3), blocks.x, blocks.starts, 1e-4)
            blocks.free()
        lease.end()
        for ctx in ctxs:
            assert not _owning(ctx, lease), "a record of an ended lease was kept"
        made.append(arena.made)
    assert made[0] == made[-1], "a lease after the first made a block"
    if not arena.holds(upload=True):
        return
    # host-addressed spectra, written by forwards into a lease's arrays
    arena = device.arena()
    plans = [(_series(c, rng, 6 * N), np.array(s, np.uint32)) for c, s in zip(ctxs, firsts)]
    made = []
    for turn in range(3):
        lease = arena.begin()
        order = (0, 1) if turn % 2 == 0 else (1, 0)
        got = []
        for i in order:
            ser, starts = plans[i]
            starts = starts + np.uint32(turn * 37)
            spectra = lease.array(ctxs[i], (3, N))
            ctxs[i].forward(N, ser, starts, spectra)
            got.append((spectra, ser, starts))
        for spectra, ser, starts in got:
            _check(spectra, ser, starts)
        lease.end()
        for ctx in ctxs:
            assert not _owning(ctx, lease), "a record of an ended lease was kept"
        made.append(arena.made)
    assert made[0] == made[-1], "a lease after the first made a block"


def test_a_lease_holds_its_tenants_weakly_and_frees_without_the_collector(device):
    """A lease names its tenant contexts and plans by weak reference, and sections hold their
    lease, not their tenant: with the collector off, an ended lease with nothing left on it,
    a tenant's arrays, and a dropped device context go with their last holder. On every
    arena with a record owning a device-only section; where the arena holds host-addressed
    arrays, also with a lease's array. (A simulated driver's buffers hold their context, and
    its finished runs what they bound -- a host array's view, through it the array's section
    and the lease -- so there the context is not checked, nor the lease of the arrays.)"""
    forms = ["sections"]
    if device.arena().holds(upload=True):
        forms.append("arrays")
    for form in forms:
        arena = device.arena()
        gc.collect()
        gc.disable()
        try:
            ctx = (sim_driver.Context(device=device.dev) if device.backend == "sim"
                   else gpu_context(device.backend))
            rng = np.random.default_rng(4)
            lease = arena.begin()
            refs = []
            if form == "sections" or device.backend != "sim":
                refs.append(weakref.ref(lease))
            if form == "sections":
                blocks = _Blocks(ctx, rng, [5])
                rec = Record()
                out = ctx._exec_buffer(rec, "out", nbytes=N * 8)
                rec.native = blocks.write(out)
                ctx._exec_table()[("arena test",)] = rec
                ctx._exec_run(rec.native, True, {}, 0)
                lease.end()
                blocks.free()
                del blocks, rec, out
            else:
                ser = _series(ctx, rng, 2 * N)
                spectra = lease.array(ctx, (1, N))
                ctx.forward(N, ser, np.array([5], np.uint32), spectra)
                refs.append(weakref.ref(spectra))
                lease.end()
                del ser, spectra
            if device.backend != "sim":
                refs.append(weakref.ref(ctx))
            ctx.destroy()
            del ctx, lease
            assert [r() for r in refs] == [None] * len(refs), form
        finally:
            gc.enable()


# ---- searches on the GPU ----------------------------------------------------------------
def _has_gpu():
    import matchedfilter as mf
    try:
        return any(str(d) == "gpu:0" for d in mf.devices())
    except Exception:
        return False


@pytest.mark.skipif(not _has_gpu(), reason="needs a GPU")
def test_a_gpu_search_after_others_on_the_arena_finds_its_own_peaks(monkeypatch):
    """Two GPU searches with different templates take the device's arena in turns (four runs,
    each section filled with NaN when handed out): each run's peaks and parent series are
    the ones the same search finds without an arena, and the second pair of runs allocates
    no block; a search run twice keeps its lease and records nothing the second time; a
    search dropped with the collector off is freed at once."""
    from test_hierarchical_search import _collect, _inputs, _profiles, _tree
    from matchedfilter.search import HierarchicalSearch
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setattr(Arena, "poison", True)
    opts = dict(engine="hier", binsize=512, device="gpu:0")
    roots = [_tree(np.random.default_rng(31 + i), inner_counts=(301, 351)) for i in range(2)]
    for root in roots:
        root.profile = _profiles()          # a GPU plan is calibrated on its reference
    inputs = _inputs(np.random.default_rng(41), nblocks=2)

    def run(i):
        return _collect(HierarchicalSearch([roots[i]], threshold=4.0, leaf_options=opts),
                        inputs)
    real_arena = _gpuroot.device_arena
    monkeypatch.setattr(_gpuroot, "device_arena", lambda device: None)
    want = [run(0), run(1)]
    monkeypatch.setattr(_gpuroot, "device_arena", real_arena)
    arena = _gpuroot.device_arena(_gpuhost._parse_device("gpu:0"))
    made = []
    for turn in range(4):
        i = turn % 2
        leases = arena.leases
        got = run(i)
        assert arena.leases == leases + 1 and not arena.lease.active
        made.append(arena.made)
        assert [g[:3] for g in got] == [w[:3] for w in want[i]]
        for g, w in zip(got, want[i]):
            assert g[3].template_indices.tolist() == w[3].template_indices.tolist()
            assert g[3].sample_indices.tolist() == w[3].sample_indices.tolist()
            np.testing.assert_array_equal(g[3].snr, w[3].snr)
            np.testing.assert_array_equal(g[4], w[4])
    assert made[3] == made[1], "a repeated pair of searches grew the arena"
    assert arena.peak_bytes > 0
    # one search run twice: the second run resumes its lease and records nothing
    search = HierarchicalSearch([roots[1]], threshold=4.0, leaf_options=opts)
    got = _collect(search, inputs)
    built, leases = search._device_builds(), arena.leases
    again = _collect(search, inputs)
    assert arena.leases == leases and search._device_builds() == built
    assert [g[:3] for g in again] == [g[:3] for g in got]
    for g, w in zip(again, got):
        np.testing.assert_array_equal(g[3].snr, w[3].snr)
    del search, got, again
    gc.collect()
    gc.disable()
    try:
        search = HierarchicalSearch([roots[0]], threshold=4.0, leaf_options=opts)
        _collect(search, inputs)
        banks = [weakref.ref(b) for b in search._leaf_banks.values()]
        ref = weakref.ref(search)
        del search
        assert ref() is None and all(b() is None for b in banks)
    finally:
        gc.enable()


@pytest.mark.skipif(not _has_gpu(), reason="needs a GPU")
def test_a_gpu_search_leaves_no_cyclic_garbage(monkeypatch):
    """A GPU search built, run and dropped with the collector off leaves no object of the
    library for the collector: its banks, plans, contexts, records and leases go with their
    last holder, and nothing it made on the way (device queries, pipelines, descriptor sets,
    chain searches) is a reference cycle. A cycle there held a PyCBC job's dead plans until
    the next full collection."""
    from test_hierarchical_search import _collect, _inputs, _profiles, _tree
    from matchedfilter.search import HierarchicalSearch
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    opts = dict(engine="hier", binsize=512, device="gpu:0")
    root = _tree(np.random.default_rng(37), inner_counts=(301, 351))
    root.profile = _profiles()
    inputs = _inputs(np.random.default_rng(43), nblocks=2)
    gc.collect()
    gc.disable()
    try:
        gc.set_debug(gc.DEBUG_SAVEALL)
        search = HierarchicalSearch([root], threshold=4.0, leaf_options=opts)
        got = _collect(search, inputs)
        assert got
        refs = [weakref.ref(search)] + [weakref.ref(b) for b in search._leaf_banks.values()]
        del search, got
        alive = [r() is not None for r in refs]
        gc.collect()
        # library objects, functions and ctypes types (a type's __module__ is its maker's)
        left = sorted({"%s.%s" % (o.__module__, getattr(o, "__qualname__", type(o).__qualname__))
                       for o in gc.garbage
                       if str(getattr(o, "__module__", "")).startswith("matchedfilter")})
    finally:
        gc.garbage.clear()
        gc.set_debug(0)
        gc.enable()
    assert alive == [False] * len(refs)
    assert left == [], left
