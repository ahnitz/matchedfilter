"""The shared command list (_gpuhost.CommandList): built by _gpuexec through ctx._x_list,
taken by every backend.

The construction and decoding tests need no device, so CI's Linux jobs cover the shared
logic; the Vulkan emitter is checked against stand-in entry points (ctypes callbacks). The
last test runs a list on whatever GPU backend this host has."""
import array
import ctypes
import gc

import numpy as np
import pytest

from matchedfilter._gpuhost import Arg, CommandList


class _Calls:
    """A backend list stand-in: records each call as made."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        return lambda *a: self.calls.append((name,) + a)


#: The objects a list is built with: kernels, buffers, a count buffer and two Args.
_K1, _K2, _B1, _B2, _CNT = object(), object(), object(), object(), object()
_SERIES, _WINDOW = Arg("series"), Arg("window", 2)


def _build(target):
    k1, k2, b1, b2, cnt, series, window = _K1, _K2, _B1, _B2, _CNT, _SERIES, _WINDOW
    target.barrier()
    target.dispatch(k1, 17, [b1, series, b2], (3, (1, 2, 3, 4), window), [0, 64, 128])
    target.stamp("forward")
    target.listed(k2, cnt, 99, [b2, b1], (5,))
    target.fill(b1, 0xFFFFFFFF, 16, None, 3, 256)
    target.update(b2, [7, 8, 9])
    target.readback(b2, 4096)
    target.dispatch(k1, 1, [b1], ())
    return target


def _norm(calls):
    """Calls with sequences as lists (a list gives back lists for the tuples it was given)."""
    out = []
    full = {"dispatch": 6, "listed": 7}          # with words=() and offsets=None given
    for c in calls:
        c = tuple(c)
        if c[0] in full and len(c) < full[c[0]]:
            c = c + ((), None)[len(c) - full[c[0]]:]
        out.append(tuple(list(x) if isinstance(x, (list, tuple)) else x for x in c))
    return out


def _same(got, want):
    assert len(got) == len(want)
    for g, w in zip(got, want):
        assert len(g) == len(w) and g[0] == w[0]
        for a, b in zip(g[1:], w[1:]):
            if isinstance(b, list):
                assert len(a) == len(b) and all(x is y or x == y for x, y in zip(a, b))
            else:
                assert a is b or a == b


def test_a_list_gives_back_the_calls_that_built_it():
    """decode() yields every call with the objects passed -- kernels, buffers, Args, vector
    words, offsets -- and replay_into() makes them again on a backend's own list."""
    want = _norm(_build(_Calls()).calls)
    cl = _build(CommandList("t"))
    _same(_norm(cl.decode()), want)
    _same(_norm(_build(CommandList("t")).replay_into(_Calls()).calls), want)
    assert cl.arg_names() == ["series", "window"] and cl.has_stamps()


def test_a_list_is_integers_and_a_few_tables():
    """The operations are one integer array that refers to no object (one object for the
    collector to visit, not one per command); the objects are in the list's tables, each
    once however often it is used."""
    cl = _build(CommandList("t"))
    assert isinstance(cl.ops, array.array)
    assert all(isinstance(r, type) for r in gc.get_referents(cl.ops))
    assert len(cl.kernels) == 2 and len(cl.buffers) == 3 and len(cl.args) == 2


def test_the_vulkan_emitter_calls_each_entry_point_with_its_arguments():
    """_core.vulkan_emit records a resolved list (_vkcompute._VK_OPS) through the entry
    points it is given: here stand-ins, so no device is needed."""
    from matchedfilter import _core, _vkcompute as V
    vp, u32, u64 = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint64
    seen = []
    protos = {
        "vkCmdBindPipeline": (None, vp, u32, u64),
        "vkCmdBindDescriptorSets": (None, vp, u32, u64, u32, u32, ctypes.POINTER(u64), u32, vp),
        "vkCmdPushConstants": (None, vp, u64, u32, u32, u32, ctypes.POINTER(u32)),
        "vkCmdDispatch": (None, vp, u32, u32, u32),
        "vkCmdDispatchIndirect": (None, vp, u64, u64),
        "vkCmdFillBuffer": (None, vp, u64, u64, u64, u32),
        "vkCmdUpdateBuffer": (None, vp, u64, u64, u64, vp),
        "vkCmdPipelineBarrier": (None, vp, u32, u32, u32, u32, ctypes.POINTER(V._MemBarrier),
                                 u32, ctypes.POINTER(V._BufMemBarrier), u32, vp),
    }

    def stand_in(name):
        def call(cmd, *a):
            if name == "vkCmdBindDescriptorSets":
                a = a[:4] + (a[4][0],) + a[5:6]
            elif name == "vkCmdPushConstants":
                a = a[:4] + (tuple(a[4][k] for k in range(a[3] // 4)),)
            elif name == "vkCmdPipelineBarrier":
                mb = (a[4][0].srcAccessMask, a[4][0].dstAccessMask) if a[3] else None
                bb = a[6][0] if a[5] else None
                bb = None if bb is None else (bb.srcAccessMask, bb.dstAccessMask,
                                              bb.srcQueueFamilyIndex, bb.dstQueueFamilyIndex,
                                              bb.buffer, bb.offset, bb.size)
                a = a[:3] + (mb, bb)
            seen.append((name, cmd) + tuple(a))
        return ctypes.CFUNCTYPE(*protos[name])(call)
    keep = {name: stand_in(name) for name in protos}
    fns = array.array("Q", [0] * 9)
    for code, name in V._VK_OPS.items():
        fns[code] = ctypes.cast(keep[name], vp).value
    upd = (u32 * 2)(5, 6)
    ops = array.array("Q", [
        1, 0, 0xAAAA,
        2, 0, 0xBBBB, 0xCCCC,
        3, 0xBBBB, 32, 0, 12, 3, 7, 0xFFFFFFFF, 42,
        4, 17, 1, 1,
        5, 0xDDDD, 64,
        6, 0xEEEE, 8, 256, 0xDEADBEEF,
        7, 0xEEEE, 0, 8, ctypes.addressof(upd),
        8, 0x800, 0x801, 0, 0x40, 0x20,
        9, 0x800, 0x1000, 0, 0x40, 0x800, 0xFFFFFFFF, 0xFFFFFFFF, 0x9999, 16, 4096,
    ])
    assert _core.vulkan_emit(0x1234, fns, ops, 0, len(ops)) == len(ops)
    assert seen == [
        ("vkCmdBindPipeline", 0x1234, 0, 0xAAAA),
        ("vkCmdBindDescriptorSets", 0x1234, 0, 0xBBBB, 0, 1, 0xCCCC, 0),
        ("vkCmdPushConstants", 0x1234, 0xBBBB, 32, 0, 12, (7, 0xFFFFFFFF, 42)),
        ("vkCmdDispatch", 0x1234, 17, 1, 1),
        ("vkCmdDispatchIndirect", 0x1234, 0xDDDD, 64),
        ("vkCmdFillBuffer", 0x1234, 0xEEEE, 8, 256, 0xDEADBEEF),
        ("vkCmdUpdateBuffer", 0x1234, 0xEEEE, 0, 8, ctypes.addressof(upd)),
        ("vkCmdPipelineBarrier", 0x1234, 0x800, 0x801, 0, (0x40, 0x20), None),
        ("vkCmdPipelineBarrier", 0x1234, 0x800, 0x1000, 0, None,
         (0x40, 0x800, 0xFFFFFFFF, 0xFFFFFFFF, 0x9999, 16, 4096)),
    ]
    sizes = dict(V._VK_OP_SIZE)
    sizes[3] = 6 + 3
    i = n = 0
    while i < len(ops):
        i += sizes[ops[i]]
        n += 1
    assert i == len(ops) and n == len(seen)       # the op sizes the fused batch walks by
    with pytest.raises(ValueError):
        _core.vulkan_emit(0x1234, fns, array.array("Q", [99]), 0, 1)


def test_a_list_runs_on_this_hosts_backend():
    """A list built through a context's _x_list -- a fill, an update after it, a barrier, a
    readback -- runs on the host's GPU backend and leaves the words in stream order."""
    from conftest import usable_gpu
    dev = usable_gpu()
    if dev is None:
        pytest.skip("no usable GPU")
    import matchedfilter as mf
    f = mf.MatchedFilter(1024, 1, 1, device=dev)
    rng = np.random.default_rng(1)
    h = (rng.normal(size=(1, 1024)) + 1j * rng.normal(size=(1, 1024))).astype(np.complex64)
    f.set_templates(h)
    f.set_data(h)
    f.run(binsize=1024)
    ctx = f._gpu
    buf = ctx._x_alloc(64, readback=True)
    lst = ctx._x_list("command-list test")
    assert isinstance(lst, CommandList)
    lst.fill(buf, 0xFFFFFFFF)
    lst.barrier()
    lst.update(buf, [1, 2, 3])
    lst.barrier()
    lst.readback(buf, 64)
    native = lst.end()
    ctx._x_run(native, True)
    out = np.zeros(16, np.uint32)
    ctx._x_read(buf, out)
    np.testing.assert_array_equal(out, [1, 2, 3] + [0xFFFFFFFF] * 13)
    ctx._x_release(native, done=True)


def test_bindings_are_named_by_serials_not_by_address():
    """binding_key names a view by its allocation's serial and offset, a buffer by its serial,
    a section by its base's serial, offset and size: a recycled allocation at the same
    address or handle (a new serial) is a different binding."""
    from types import SimpleNamespace as NS
    from matchedfilter._gpuhost import binding_key
    a1, a2 = NS(serial=11), NS(serial=12)
    assert binding_key(NS(owner=a1, offset=64)) == ("view", 11, 64)
    assert binding_key(NS(owner=a1, offset=64)) != binding_key(NS(owner=a2, offset=64))
    assert binding_key(NS(serial=5)) == ("buffer", 5)
    assert binding_key(NS(base=NS(serial=7), offset=16, nbytes=32)) == ("section", 7, 16, 32)
    assert binding_key((3, 4)) == (3, 4)


def test_the_binding_cache_keeps_the_most_recent_and_frees_the_rest():
    """BindingCache: one instance per binding, the most recently used `limit` kept; a waited
    run past the limit gets a one-off instance instead of an eviction; a `once` recording is
    made for its run; evictions free without the done flag, one-offs and clear(done) with
    it."""
    from types import SimpleNamespace as NS
    from matchedfilter._gpuhost import BindingCache
    made, freed = [], []
    cache = BindingCache(limit=2)
    make = lambda b: made.append(b["x"]) or ("inst", b["x"])
    free = lambda inst, done: freed.append((inst[1], done))
    views = [NS(owner=NS(serial=i), offset=0) for i in range(4)]
    assert cache.get(["x"], {"x": views[0]}, make, free)[1] is None
    cache.get(["x"], {"x": views[1]}, make, free)
    assert cache.get(["x"], {"x": NS(owner=views[0].owner, offset=0)}, make, free)[0] == ("inst", views[0])
    assert len(made) == 2                       # the same allocation and offset: kept
    inst, release = cache.get(["x"], {"x": views[2]}, make, free, transient=True)
    assert release is not None and len(cache) == 2 and freed == []
    release()
    assert freed == [(views[2], True)]
    cache.get(["x"], {"x": views[3]}, make, free)           # evicts the least recently used: views[1]
    assert freed[-1] == (views[1], False) and len(cache) == 2
    inst, release = cache.get(["x"], {"x": views[0]}, make, free, once=True)
    assert release is not None and made[-1] is views[0]
    cache.clear(free, done=True)
    assert len(cache) == 0 and sorted(id(f[0]) for f in freed[-2:]) == sorted(
        [id(views[0]), id(views[3])]) and all(f[1] for f in freed[-2:])


def test_lists_and_caches_make_no_reference_cycle_with_their_owner():
    """A finished list keeps no reference to the backend that recorded it, and a binding
    cache none to its owner: a native that keeps its list, and a cache that kept its native's
    methods, made every recording a cycle through its context, freed only by the collector
    (device memory followed the collector's timing: 18 GB in a pycbc job)."""
    import weakref

    class Owner:
        def __init__(self):
            self.cache = __import__("matchedfilter._gpuhost", fromlist=["x"]).BindingCache(2)

        def record(self, commands):
            self.commands = commands             # a native keeps its list
            return self

    owner = Owner()
    cl = CommandList("t", record=owner.record)
    cl.barrier()
    assert cl.end() is owner
    owner.cache.get([], {}, lambda b: ("inst",), lambda inst, done: None)
    ref = weakref.ref(owner)
    gc.disable()
    try:
        del owner
        assert ref() is None                    # reference counting alone frees it
    finally:
        gc.enable()
