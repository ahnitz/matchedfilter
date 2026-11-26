"""A recorded list's fills, updates and readback run in stream order on the host's GPU
backend (_gpuexec: "update(buf, words) write a few words, in order with the work")."""
import numpy as np
import pytest


def _context():
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
    return f, f._gpu


def _run(ctx, steps, buf):
    lst = ctx._x_list("list order test")
    for step in steps:
        step(lst)
    lst.readback(buf, 64)
    native = lst.end()
    for _ in range(2):           # a recording runs alike every time (a staged update too)
        ctx._x_run(native, True)
        out = np.zeros(16, np.uint32)
        ctx._x_read(buf, out)
        yield out
    ctx._x_release(native, done=True)


@pytest.mark.parametrize("order", ["fill, update", "update, fill"])
def test_updates_and_fills_land_in_list_order(order, request):
    """fill -> barrier -> update -> barrier -> readback leaves the update over the fill;
    update -> barrier -> fill leaves the fill. The second run of each recording reads the
    same (the buffer is rewritten between runs from the host through its write(), which
    every _x_alloc buffer has, to show it is the run's)."""
    f, ctx = _context()
    if ctx.kernel_family == "cuda":
        request.node.add_marker(pytest.mark.xfail(strict=True, reason=(
            "known gap on cuda: a readback buffer (_cudacompute._Readback) has no write(), "
            "which the interface gives every _x_alloc buffer")))
    buf = ctx._x_alloc(64, readback=True)
    fill = lambda lst: (lst.fill(buf, 0xFFFFFFFF), lst.barrier())
    update = lambda lst: (lst.update(buf, [1, 2, 3]), lst.barrier())
    steps = [fill, update] if order == "fill, update" else [update, fill]
    want = ([1, 2, 3] + [0xFFFFFFFF] * 13 if order == "fill, update"
            else [0xFFFFFFFF] * 16)
    for out in _run(ctx, steps, buf):
        np.testing.assert_array_equal(out, want, err_msg=order)
        buf.write(np.zeros(16, np.uint32))
    ctx._x_free(buf)
    del f
