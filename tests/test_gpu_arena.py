"""A search's buffer arena (_gpuhost.Arena and ArenaLease): sections laid out per lease and
recycled across leases, and nothing that outlives a lease mistaking a recycled section for its
previous tenant.

Each recycle test runs on the simulated driver (tests/sim_driver.py) and on the host's GPU. The
search tests need a GPU: they compare a search's peaks after another search has used the arena
with its peaks without an arena.
"""
import gc
import weakref

import numpy as np
import pytest

import sim_driver
from conftest import gpu_backend, gpu_context
from matchedfilter import _gpuhost, _gpuroot
from matchedfilter._gpuhost import ARENA_BLOCK, Arena, binding_key

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


@pytest.fixture(params=["sim", "device"])
def device(request):
    backend = "sim" if request.param == "sim" else gpu_backend()
    dev = _Device(backend)
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


def _check(spectra, series, starts):
    want = _want(series, starts)
    np.testing.assert_allclose(spectra, want, rtol=0, atol=2e-6 * np.abs(want).max())


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
        from matchedfilter._gpuexec import Record
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
    """A forward deferred into a lease's spectra and never run is dropped when the lease ends:
    the context's next run on that slot, after the next lease has given the same bytes to
    another tenant, leaves that tenant's values as they are (claimed by address, or run first
    on its slot, the old forward would have written them)."""
    ctx, other = device.make(), device.make()
    arena = device.arena()
    rng = np.random.default_rng(2)
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
    bytes no one wrote): every forward's spectra are its own inputs' transforms, and the
    records of an ended lease are released."""
    monkeypatch.setattr(Arena, "poison", True)
    ctxs = [device.make(), device.make()]
    arena = device.arena()
    rng = np.random.default_rng(3)
    plans = [(_series(c, rng, 6 * N), np.array(s, np.uint32))
             for c, s in zip(ctxs, ([0, 900, 4000], [10, 2000, 5100]))]
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
        for c in ctxs:
            assert not any(getattr(rec.buffers[name], "lease", None) is lease
                           for rec in c._exec_table().values() for name in rec.owned)
    assert arena.made == 2      # one block of each kind taken (spectra, staged starts)


def test_a_lease_holds_its_tenants_weakly_and_frees_without_the_collector(device):
    """A lease names its tenant contexts and plans by weak reference, and sections hold their
    lease, not their tenant: with the collector off, a tenant's arrays and an ended lease
    with nothing left on it go with their last holder, and a dropped device context is freed
    at once (a simulated driver's buffers hold their context, and its finished runs what they
    bound, so there only the arrays are checked)."""
    arena = device.arena()
    gc.collect()
    gc.disable()
    try:
        ctx = (sim_driver.Context(device=device.dev) if device.backend == "sim"
               else gpu_context(device.backend))
        lease = arena.begin()
        rng = np.random.default_rng(4)
        ser = _series(ctx, rng, 2 * N)
        spectra = lease.array(ctx, (1, N))
        ctx.forward(N, ser, np.array([5], np.uint32), spectra)
        refs = [weakref.ref(spectra)]
        if device.backend != "sim":
            refs += [weakref.ref(lease), weakref.ref(ctx)]
        lease.end()
        ctx.destroy()
        del ctx, spectra, ser, lease
        assert [r() for r in refs] == [None] * len(refs)
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
    the ones the same search finds without an arena, the plans of an ended run keep no
    record on the arena, the second pair of runs allocates no block, and a search dropped
    with the collector off is freed at once."""
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
        assert arena.leases == leases + 1 and arena.lease is None
        made.append(arena.made)
        assert [g[:3] for g in got] == [w[:3] for w in want[i]]
        for g, w in zip(got, want[i]):
            assert g[3].template_indices.tolist() == w[3].template_indices.tolist()
            assert g[3].sample_indices.tolist() == w[3].sample_indices.tolist()
            np.testing.assert_array_equal(g[3].snr, w[3].snr)
            np.testing.assert_array_equal(g[4], w[4])
    assert made[3] == made[1], "a repeated pair of searches grew the arena"
    assert arena.peak_bytes > 0
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
