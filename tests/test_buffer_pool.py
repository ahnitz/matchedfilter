"""Device allocations recycled between buffers (_gpuhost.BufferPool): the pool's accounting,
and on a Vulkan device that a recycled allocation is a new buffer to everything that caches
on one (its serial, the upload cache's signature), whatever handle and address it reuses."""
import gc

import numpy as np
import pytest

from matchedfilter._gpuhost import BufferPool


def test_size_classes_hold_the_request_within_a_quarter():
    for n in list(range(1, 5000, 7)) + [1 << 20, (1 << 20) + 1, 7_340_000]:
        c = BufferPool.size_class(n)
        assert c >= max(n, 256) and (n < 256 or c <= 1.25 * n + 1)


def test_the_pool_never_holds_more_than_was_ever_live():
    """Idle and live allocations together stay within the most live at once; past it the
    oldest idle ones are freed; a take gets the one given back last."""
    pool, freed = BufferPool(), []
    for _ in range(4):
        pool.note_made(1024)
    for i in range(4):
        pool.give("k", 1024, i, 0, freed.append)
    assert (pool.live_bytes, pool.idle_bytes, freed) == (0, 4096, [])
    assert pool.take("k", 1024) == 3 and pool.take("k", 2048) is None
    pool.note_made(2048)                     # live 3072 of a 4096 peak: one idle must go
    assert freed == [0, 1] and pool.live_bytes + pool.idle_bytes <= pool.peak_live
    pool.clear()
    assert freed == [0, 1, 2] and pool.idle_bytes == 0


def test_poison_fills_a_recycled_allocation():
    import ctypes
    buf = (ctypes.c_ubyte * 512)()
    pool = BufferPool()
    pool.note_made(512)
    pool.give("k", 512, "res", ctypes.addressof(buf), None)
    pool.poison = True
    assert pool.take("k", 512) == "res" and bytes(buf) == b"\xff" * 512


def test_a_recycled_vulkan_allocation_is_a_new_buffer():
    """A Vulkan buffer freed and made again at its size reuses the allocation (handle and
    host address), under a new serial; the upload cache, keyed on the array's address, tells
    the two arrays apart by their allocations' serials, so a cached upload of the first is
    not taken for the second."""
    from conftest import gpu_backend, gpu_context
    if gpu_backend() != "vulkan":
        pytest.skip("Vulkan buffers")
    from matchedfilter._shared import allocation_serial
    ctx = gpu_context("vulkan")
    pool = ctx._device_state.buffers
    a = ctx.empty_shared((1000,))
    a[:] = 1.0
    where, serial = a.ctypes.data, allocation_serial(a)
    sig_a = ctx._input_uploads("k", a, a, False, False)[2]
    reused = pool.reused
    del a
    gc.collect()
    b = ctx.empty_shared((1000,))
    assert pool.reused == reused + 1 and b.ctypes.data == where
    assert allocation_serial(b) not in (None, serial)
    assert ctx._input_uploads("k", b, b, False, False)[2] != sig_a
    np.testing.assert_array_equal(b.real, 1.0)     # its old contents: nothing zeroes them
