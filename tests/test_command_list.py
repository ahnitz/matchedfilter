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
