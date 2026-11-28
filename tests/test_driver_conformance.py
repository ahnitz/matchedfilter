"""Driver conformance: what a caller of a GPU driver's Context may rely on, one test per
contract, written once and run on every driver the host has.

Each test uses only the driver interface the _gpuexec module docstring describes -- a
Context's _x_* primitives, its documented attributes, and the executor's write tokens
(settle_writes, write_token, settle_until), which are part of the same contract -- and two
shipped kernels (forward and fwd_listed) as its writers and readers, never the workloads
built on them. Each runs on

  * "sim": the simulated driver (tests/sim_driver.py), on every host. It executes submitted
    work only when something waits on it, so a missing order fails every time, not when
    timing exposes it; it checks the shared layers (the executor's write tokens and
    deferred work, the shared allocation pool) and the contract itself, without a GPU;
  * "device": the host's usable GPU (conftest.gpu_backend), whatever its backend; skipped
    without one. Ordering is checked as deterministically as a device allows: outputs are
    filled with NaN first, the writer is slow and the reader quick, and tokens and
    registration are checked as well as data.

A gap a backend is known to have is a strict xfail naming the backend and the gap
(known_gap): when the gap is fixed the test passes, the xfail fails, and the mark must go.
The marks for CUDA and Metal were derived from reading the code and are unverified until
the suite runs there.

Run on one backend: OMP_NUM_THREADS=1 python -m pytest tests/test_driver_conformance.py
tests/test_gpu_root.py -q -rxX (the backend is the host's GPU; -rxX lists each known gap).
"""
import gc
import re

import numpy as np
import pytest

import sim_driver
from conftest import gpu_backend, gpu_context
from matchedfilter import _choice, _gpuexec
from matchedfilter._gpuexec import Arg

#: Transform length of every writer and reader (shipped for every backend).
N = 1024


# ---- contexts and known gaps --------------------------------------------------------------
def known_gap(backend, reason, **params):
    """Mark a test a strict xfail on `backend` (with parameters matching `params`, if
    given): a contract the backend's driver is known not to keep, and why."""
    def mark(fn):
        fn.__dict__.setdefault("known_gaps", []).append((backend, reason, params))
        return fn
    return mark


class _Maker:
    """make() -> a new context on one device (one simulated device per test, or the
    host's GPU), destroyed at the end of the test. backend: "sim", "vulkan", "cuda" or
    "metal"; big: whether writers should be slow (a device) or small (the simulation)."""

    def __init__(self, backend, faults=()):
        self.backend, self.made, self.big = backend, [], backend != "sim"
        self.dev = sim_driver._Device() if backend == "sim" else None
        self.faults = faults

    def __call__(self):
        if self.backend == "sim":
            ctx = sim_driver.Context(device=self.dev, faults=self.faults)
        else:
            ctx = gpu_context(self.backend)
        self.made.append(ctx)
        return ctx

    def close(self):
        for ctx in self.made:
            try:
                ctx.settle_writes()
                ctx._x_idle()
            except Exception:
                pass
        for ctx in self.made:
            ctx.destroy()
        self.made = []


@pytest.fixture(params=["sim", "device"])
def make(request):
    backend = "sim" if request.param == "sim" else gpu_backend()
    params = getattr(request.node, "callspec", None)
    params = params.params if params is not None else {}
    for gap_backend, reason, match in getattr(request.function, "known_gaps", ()):
        if gap_backend == backend and all(params.get(k) == v for k, v in match.items()):
            request.node.add_marker(pytest.mark.xfail(
                strict=True, reason="known gap on %s: %s" % (backend, reason)))
    maker = _Maker(backend)
    yield maker
    maker.close()


# ---- writers, readers and checks -----------------------------------------------------------
def _sync(ctx, slot=None):
    """Wait for everything ordered before the next work on `slot` (an upload's contract)."""
    lst = ctx._x_list("sync")
    lst.barrier()
    native = lst.end()
    ctx._x_run(native, True, None, slot)
    ctx._x_release(native, done=True)


def _upload(ctx, array, slot=None):
    """An upload buffer holding array, written and finished."""
    array = np.ascontiguousarray(array)
    buf = ctx._x_alloc(array.nbytes, upload=True)
    ctx._x_upload(buf, array, slot)
    _sync(ctx, slot)
    return buf


def _read(ctx, buf, dtype, count, offset=0):
    out = np.empty(count, dtype)
    ctx._x_read(buf, out, offset)
    return out


def _nan_fill(ctx, buf, nbytes):
    """Fill a readback buffer with 0xFFFFFFFF words (NaN), finished."""
    lst = ctx._x_list("nan")
    lst.fill(buf, 0xFFFFFFFF)
    lst.barrier()
    lst.readback(buf, nbytes)
    native = lst.end()
    ctx._x_run(native, True)
    ctx._x_release(native, done=True)


def _spectra(x, starts, nser):
    """What the forward kernel writes: each start's n samples (zero past nser), FFT / n."""
    out = np.zeros((len(starts), N), np.complex128)
    for i, s in enumerate(starts):
        m = max(0, min(N, nser - int(s)))
        out[i, :m] = x[int(s):int(s) + m]
    return np.fft.fft(out, axis=1) / N


def _close(got, want, what):
    got = np.asarray(got).reshape(np.shape(want))
    np.testing.assert_allclose(got, want, rtol=0, atol=1e-4 * np.abs(want).max(),
                               err_msg=what)


class Writer:
    """A slow writer of `out` (rows of spectra): its list fills out with NaN, makes `passes`
    forward transforms into a scratch buffer, and only then writes out -- so out holds NaN
    while it runs. The list begins and ends with a barrier."""

    def __init__(self, maker, ctx, rng, rows=None, passes=None, captured=False, out_arg=False):
        big = maker.big
        self.ctx = ctx
        self.rows = rows or (2048 if big else 4)
        self.passes = (16 if big else 1) if passes is None else passes
        self.nser = (self.rows + 1) * N
        self.x = (rng.standard_normal(self.nser)
                  + 1j * rng.standard_normal(self.nser)).astype(np.complex64)
        st = (np.arange(self.rows) * N + rng.integers(0, N, self.rows)).astype(np.uint32)
        self.series = _upload(ctx, self.x)
        self.starts = _upload(ctx, st)
        self.want = _spectra(self.x, st, self.nser)
        self.nbytes = self.rows * N * 8
        self.out = ctx._x_alloc(self.nbytes, readback=True)
        _nan_fill(ctx, self.out, self.nbytes)
        fwd = ctx._x_kernel("forward", N)
        lst = ctx._x_list("writer")
        out = Arg("out") if out_arg else self.out
        if captured:
            # the shape of a forward recording (_gpuexec.forward), which fused batches take
            lst.stamp("start")
            lst.dispatch(fwd, self.rows, [self.series, self.starts, out], (self.nser, 0))
            lst.barrier()
            lst.stamp("forward")
            self.scratch = None
        else:
            lst.barrier()
            if not out_arg:
                lst.fill(out, 0xFFFFFFFF)
                lst.barrier()
            self.scratch = ctx._x_alloc(self.nbytes) if self.passes else None
            for _ in range(self.passes):
                lst.dispatch(fwd, self.rows, [self.series, self.starts, self.scratch],
                             (self.nser, 0))
                lst.barrier()
            lst.dispatch(fwd, self.rows, [self.series, self.starts, out], (self.nser, 0))
            lst.barrier()
        if not out_arg:
            lst.readback(self.out, self.nbytes)
        self.native = lst.end()

    def check(self, what="writer output"):
        _close(_read(self.ctx, self.out, np.complex64, self.rows * N), self.want, what)

    def unwritten(self):
        """Whether its output still holds the NaN it was filled with."""
        return bool(np.isnan(_read(self.ctx, self.out, np.complex64, self.rows * N)).all())


class Reader:
    """A quick reader of a writer's output, in context ctx: a forward transform of a few of
    its rows into its own readback buffer (a list beginning and ending with a barrier).
    passes > 0 makes it slow instead (that many transforms into a scratch buffer first)."""

    def __init__(self, ctx, writer, passes=0):
        self.ctx, self.writer = ctx, writer
        picks = sorted({0, writer.rows // 2, writer.rows - 1})
        self.count = len(picks)
        nser = writer.rows * N
        self.want = _spectra(writer.want.astype(np.complex64).ravel(),
                             [p * N for p in picks], nser)
        st = np.asarray([p * N for p in picks], np.uint32)
        self.starts = _upload(ctx, st)
        self.nbytes = self.count * N * 8
        self.out = ctx._x_alloc(self.nbytes, readback=True)
        _nan_fill(ctx, self.out, self.nbytes)
        fwd = ctx._x_kernel("forward", N)
        lst = ctx._x_list("reader")
        lst.barrier()
        self.scratch = ctx._x_alloc(self.nbytes) if passes else None
        for _ in range(passes):
            lst.dispatch(fwd, self.count, [writer.out, self.starts, self.scratch], (nser, 0))
            lst.barrier()
        lst.dispatch(fwd, self.count, [writer.out, self.starts, self.out], (nser, 0))
        lst.barrier()
        lst.readback(self.out, self.nbytes)
        self.native = lst.end()

    def check(self, what="reader output"):
        _close(_read(self.ctx, self.out, np.complex64, self.count * N), self.want, what)


SLOTS = [None, 0, 1]


# ---- C0: the simulated driver is a driver --------------------------------------------------
def test_the_simulated_driver_provides_every_primitive():
    """The simulated driver defines every primitive the executor calls (the _gpuexec
    docstring's list), so the suite's simulated runs exercise the same interface."""
    from test_driver_primitives import _primitives
    missing = sorted(n for n in _primitives() if not callable(getattr(sim_driver.Context, n,
                                                                      None)))
    assert not missing, missing


# ---- C1-C3: what is finished, and what is a pending write, after each call -----------------
@pytest.mark.parametrize("slot", SLOTS)
def test_a_waited_run_is_finished_on_return(make, slot):
    """_x_run(wait=True) returns after the run has finished: the host reads its output with
    _x_read at once, on any slot."""
    ctx = make()
    w = Writer(make, ctx, np.random.default_rng(1))
    ctx._x_run(w.native, True, None, slot)
    w.check()


@pytest.mark.parametrize("slot", SLOTS)
def test_a_run_left_in_flight_is_a_pending_write(make, slot):
    """_x_run(wait=False) leaves the run in flight as a pending write, on any slot: it is the
    device's newest write token until settled, and after settle_writes the host reads its
    output (and the token is gone)."""
    ctx = make()
    w = Writer(make, ctx, np.random.default_rng(2))
    before = ctx.write_token()
    ctx._x_run(w.native, False, None, slot)
    token = ctx.write_token()
    assert token is not None and token is not before, "no write token for the run"
    ctx.settle_writes()
    assert ctx.write_token() is None
    w.check()


@pytest.mark.parametrize("slot", SLOTS)
def test_a_submitted_run_is_finished_by_its_wait(make, slot):
    """_x_submit returns wait(): after it returns, the host reads the run's output, on any
    slot."""
    ctx = make()
    w = Writer(make, ctx, np.random.default_rng(3))
    wait = ctx._x_submit(w.native, {}, slot)
    wait()
    w.check()


@pytest.mark.parametrize("pending", [True, False])
@pytest.mark.parametrize("slot", SLOTS)
def test_a_submission_is_a_pending_write_exactly_when_asked(make, slot, pending):
    """_x_submit(pending=True) is a pending write on any slot: the device's newest write
    token, which settle_writes waits for (the device root's series, which the middle stage
    and the host read). Without pending it registers nothing -- settle_writes and other
    slots do not wait for a pipelined call -- and its wait() finishes it."""
    ctx = make()
    w = Writer(make, ctx, np.random.default_rng(4))
    before = ctx.write_token()
    wait = ctx._x_submit(w.native, {}, slot, pending=pending)
    token = ctx.write_token()
    try:
        if pending:
            assert token is not None and token is not before, "no write token for the run"
            ctx.settle_writes()
            w.check()
        else:
            assert token is before, "a submission without pending registered a write token"
    finally:
        wait()
    w.check()


# ---- C4, C5: who is ordered after a pending write -----------------------------------------
@pytest.mark.parametrize("form", ["run", "submit"])
@pytest.mark.parametrize("slot", [None, 1])
def test_another_context_reads_a_pending_write(make, form, slot):
    """Another context's run on the same device, on any slot, executes after a pending write
    submitted before it (a list that reads it begins with a barrier): the middle stage reads
    what the device root (an unslotted _x_submit) or a correlation left in flight
    (_x_run(wait=False)) wrote."""
    a, b = make(), make()
    w = Writer(make, a, np.random.default_rng(5))
    r = Reader(b, w)
    if form == "run":
        a._x_run(w.native, False)
        wait = None
    else:
        wait = a._x_submit(w.native, {}, None, pending=True)
    b._x_run(r.native, True, None, slot)
    r.check("a reader in another context")
    if wait is not None:
        wait()
    a.settle_writes()


@pytest.mark.parametrize("slots", [(0, 1), (1, None), (None, 1), (1, 1)])
def test_another_slot_reads_a_pending_write(make, slots):
    """A run of the same context on any slot executes after a pending write the context
    submitted before it on another slot (or the same one)."""
    ctx = make()
    w = Writer(make, ctx, np.random.default_rng(6))
    r = Reader(ctx, w)
    ctx._x_run(w.native, False, None, slots[0])
    ctx._x_run(r.native, True, None, slots[1])
    r.check("a reader on slot %s after a write on slot %s" % (slots[1], slots[0]))
    ctx.settle_writes()


@pytest.mark.parametrize("form", ["waited", "in flight"])
def test_a_run_on_a_slot_follows_earlier_work_on_that_slot(make, form):
    """Work a context submits on a slot executes after the work it submitted on that slot
    before it (the later list beginning with a barrier), whether the later run is waited
    for or left in flight: a pipelined slot's next work follows its last call. (A slot has
    one _x_submit in flight at a time: a pipelining caller waits for a slot's result before
    it submits there again.)"""
    ctx = make()
    w = Writer(make, ctx, np.random.default_rng(20))
    r = Reader(ctx, w)
    wait = ctx._x_submit(w.native, {}, 1)
    if form == "waited":
        ctx._x_run(r.native, True, None, 1)
    else:
        ctx._x_run(r.native, False, None, 1)
        ctx.settle_writes()
    try:
        r.check("a reader after a writer on its slot")
    finally:
        wait()
        ctx.settle_writes()


# ---- C6: deferred work in the same submission ---------------------------------------------
@pytest.mark.parametrize("form", ["waited", "in flight", "submitted"])
def test_deferred_work_runs_first_in_the_same_submission(make, form):
    """A run's `pre` items ((native, binds) deferred for it) execute before it, in the same
    submission, whether it is waited for, left in flight or submitted."""
    ctx = make()
    w = Writer(make, ctx, np.random.default_rng(7))
    r = Reader(ctx, w)
    pre = [(w.native, {})]
    if form == "waited":
        ctx._x_run(r.native, True, None, 1, pre=pre)
    elif form == "in flight":
        ctx._x_run(r.native, False, None, 1, pre=pre)
        ctx.settle_writes()
    else:
        ctx._x_submit(r.native, {}, 1, pre=pre)()
    w.check("deferred writer")
    r.check("its consumer")


class _Counting:
    """A driver function wrapped to count its calls (argtypes and other attributes are the
    wrapped function's)."""

    def __init__(self, fn, counts, name, amount):
        object.__setattr__(self, "_fn", fn)
        object.__setattr__(self, "_count", (counts, name, amount))

    def __call__(self, *args):
        counts, name, amount = self._count
        counts[name] = counts.get(name, 0) + amount(args)
        return self._fn(*args)

    def __getattr__(self, attr):
        return getattr(self._fn, attr)

    def __setattr__(self, attr, value):
        setattr(self._fn, attr, value)


class _Table:
    """A driver's function table (ctx.vk, ctx.cuda) or Objective-C bridge (ctx.o) seen through
    a proxy that counts the calls named in `counted` (name -> amount(args))."""

    def __init__(self, real, counts, counted):
        self._real, self._counts, self._counted = real, counts, counted

    def __getattr__(self, name):
        fn = getattr(self._real, name)
        if name in self._counted:
            return _Counting(fn, self._counts, name, self._counted[name])
        return fn


def _one(args):
    return 1


def _metal_selector(prefix):
    return lambda args: 1 if len(args) > 1 and bytes(args[1]).startswith(prefix) else 0


def instrument(ctx):
    """Counters of what ctx's driver makes: {"recordings": live native recordings it holds
    (a function of the counts), "allocations": device allocations made}. Installed on this
    context only, before it records or allocates anything the test counts. The simulated
    driver counts its own; for a device the counts come from the API calls that make and
    free them -- Vulkan command buffers and memory, CUDA graph executables and memory
    (nothing else is a per-binding recording there), Metal buffers (it records nothing:
    every run encodes afresh, so it holds no recordings). The CUDA and Metal counters are
    unverified until the suite runs there."""
    counts = {}
    family = ctx.props.artifact_family
    if family == "sim":
        dev = ctx._device_state
        return lambda: {"recordings": dev.live_recordings, "allocations": dev.allocations}
    if family == "vulkan":
        ctx.vk = _Table(ctx.vk, counts, {
            "vkAllocateCommandBuffers": lambda a: int(a[1]._obj.commandBufferCount),
            "vkFreeCommandBuffers": lambda a: int(a[2]),
            "vkAllocateMemory": _one})
        return lambda: {"recordings": counts.get("vkAllocateCommandBuffers", 0)
                        - counts.get("vkFreeCommandBuffers", 0),
                        "allocations": counts.get("vkAllocateMemory", 0)}
    if family == "cuda":
        ctx.cuda = _Table(ctx.cuda, counts, {
            "cuGraphInstantiateWithFlags": _one, "cuGraphExecDestroy": _one,
            "cuMemAlloc_v2": _one, "cuMemAllocHost_v2": _one, "cuMemAllocManaged": _one})
        return lambda: {"recordings": counts.get("cuGraphInstantiateWithFlags", 0)
                        - counts.get("cuGraphExecDestroy", 0),
                        "allocations": sum(counts.get(k, 0) for k in (
                            "cuMemAlloc_v2", "cuMemAllocHost_v2", "cuMemAllocManaged"))}
    if family == "metal":
        real = ctx.o

        class _Bridge:
            def __getattr__(self, name):
                return getattr(real, name)

            def call(self, obj, selector, *args, **kwargs):
                if bytes(selector).startswith(b"newBuffer"):
                    counts["newBuffer"] = counts.get("newBuffer", 0) + 1
                return real.call(obj, selector, *args, **kwargs)
        ctx.o = _Bridge()
        return lambda: {"recordings": 0, "allocations": counts.get("newBuffer", 0)}
    raise AssertionError("no counters for driver %s: add them here" % family)


@pytest.mark.parametrize("form", ["waited", "in flight", "submitted"])
def test_one_off_recordings_are_freed_after_their_run(make, form):
    """A recording bound to more bindings than a driver keeps (a stream of new outputs)
    records a one-off instance per run, which is freed once that run has finished: after
    the runs are waited or settled and the recordings released, the driver holds no more
    recordings than before them. What it covers per backend: Vulkan's command buffers (a
    one-off one past 8 bindings, which _x_run(wait=False) once leaked), CUDA's graph
    executables, the simulated driver's instances; Metal makes no recording objects (every
    run encodes afresh), so there it holds by construction and checks only the outputs."""
    ctx = make()
    counters = instrument(ctx)
    rng = np.random.default_rng(8)
    x = (rng.standard_normal(2 * N) + 1j * rng.standard_normal(2 * N)).astype(np.complex64)
    series, starts = _upload(ctx, x), _upload(ctx, np.zeros(1, np.uint32))
    outs = [ctx._x_alloc(N * 8, readback=True) for _ in range(12)]
    fwd = ctx._x_kernel("forward", N)
    lst = ctx._x_list("pre")
    lst.dispatch(fwd, 1, [series, starts, Arg("out")], (2 * N, 0))
    lst.barrier()
    pre = lst.end()
    lst = ctx._x_list("consumer")
    lst.barrier()
    consumer = lst.end()
    before = counters()["recordings"]
    for out in outs:
        items = [(pre, {"out": out})]
        if form == "waited":
            ctx._x_run(consumer, True, None, None, pre=items)
        elif form == "in flight":
            ctx._x_run(consumer, False, None, None, pre=items)
        else:
            ctx._x_submit(consumer, {}, None, pre=items)()
    ctx.settle_writes()
    ctx._x_idle()
    want = _spectra(x, [0], 2 * N)
    for out in outs:
        _close(_read(ctx, out, np.complex64, N), want, "deferred output")
    ctx._x_release(pre, done=True)
    ctx._x_release(consumer, done=True)
    assert counters()["recordings"] == before, counters()


# ---- C7: settling up to a token ------------------------------------------------------------
def test_settle_until_waits_for_that_write_and_older_ones(make):
    """settle_until(token) waits for the pending write that token names and every older
    one, and leaves newer ones registered; a token already settled is a no-op."""
    ctx = make()
    rng = np.random.default_rng(9)
    w1, w2 = Writer(make, ctx, rng), Writer(make, ctx, rng)
    ctx._x_run(w1.native, False)
    t1 = ctx.write_token()
    ctx._x_run(w2.native, False)
    t2 = ctx.write_token()
    assert t1 is not None and t2 is not None and t2 is not t1
    ctx.settle_until(t1)
    w1.check("the write settled to")
    assert ctx.write_token() is t2, "settle_until settled a newer write's token"
    ctx.settle_until(t1)
    assert ctx.write_token() is t2
    ctx.settle_until(t2)
    assert ctx.write_token() is None
    w2.check("the newer write")


# ---- C8: release and free wait for the runs that use them ----------------------------------
def test_a_released_recording_and_its_freed_buffers_are_not_written_later(make):
    """_x_release(native) without done=True waits for the recording's runs still in flight,
    so the buffers they wrote can then be freed with _x_free: memory a new allocation
    recycles from them is never written by those runs."""
    ctx = make()
    w = Writer(make, ctx, np.random.default_rng(10))
    wait = ctx._x_submit(w.native, {}, 1)
    ctx._x_release(w.native)
    ctx._x_free(w.out)
    if w.scratch is not None:
        ctx._x_free(w.scratch)
    fresh = [ctx._x_alloc(w.nbytes, readback=True) for _ in range(2)]
    for buf in fresh:
        lst = ctx._x_list("zero")
        lst.fill(buf, 0)
        lst.barrier()
        lst.readback(buf, w.nbytes)
        native = lst.end()
        ctx._x_run(native, True)
        ctx._x_release(native, done=True)
    wait()
    ctx._x_idle()
    for buf in fresh:
        assert not _read(ctx, buf, np.uint32, w.nbytes // 4).any(), \
            "a released recording's run wrote recycled memory"


# ---- C9, C11: per-run bindings -------------------------------------------------------------
@known_gap("cuda", "_x_read of a readback buffer copies its page-locked mirror, which only a "
                   "list's readback op of that buffer refreshes: a run that writes it through "
                   "an Arg (no readback op of its own) is read as the mirror of an earlier "
                   "run (_cudacompute._Readback.read_into)")
@pytest.mark.parametrize("wait", [True, False])
def test_a_recording_writes_the_buffers_each_run_binds(make, wait):
    """A recording with an Arg writes the buffer each run binds: two buffers in turn, more
    bindings than a driver keeps, a first one again, and a buffer allocated where a freed
    one was."""
    ctx = make()
    w = Writer(make, ctx, np.random.default_rng(11), passes=0, out_arg=True)
    outs = [ctx._x_alloc(w.nbytes, readback=True) for _ in range(10)]
    order = [0, 1, 0] + list(range(2, 10)) + [0]

    def run(out):
        _nan_fill(ctx, out, w.nbytes)
        ctx._x_run(w.native, wait, {"out": out})
        ctx.settle_writes()
        _close(_read(ctx, out, np.complex64, w.rows * N), w.want, "a rebound output")
    for i in order:
        run(outs[i])
    ctx._x_free(outs.pop(1))
    run(ctx._x_alloc(w.nbytes, readback=True))


# ---- C10: steady state allocates nothing and leaves no cyclic garbage ----------------------
@pytest.mark.parametrize("wait", [True, False])
def test_steady_runs_allocate_nothing_and_leave_no_cyclic_garbage(make, wait):
    """Repeating a run of one recording with the same bindings makes no device allocation
    and leaves no reference cycles for the collector (a ctypes array type made per call is
    one: about 1.4 million objects of garbage in a pycbc GPU job)."""
    ctx = make()
    counters = instrument(ctx)
    w = Writer(make, ctx, np.random.default_rng(12), passes=0)
    for _ in range(2):
        ctx._x_run(w.native, wait)
        ctx.settle_writes()
    before = counters()["allocations"]
    gc.collect()
    gc.disable()
    try:
        gc.set_debug(gc.DEBUG_SAVEALL)
        for _ in range(50):
            ctx._x_run(w.native, wait)
            ctx.settle_writes()
        gc.collect()
        kinds = {type(o).__name__ for o in gc.garbage}
    finally:
        gc.garbage.clear()
        gc.set_debug(0)
        gc.enable()
    assert counters()["allocations"] == before, "steady runs allocated device memory"
    assert "PyCArrayType" not in kinds, kinds
    w.check()


_UNPOOLED_METAL = ("Metal makes every buffer with newBufferWithLength and releases it at "
                   "once: no allocation pool (audit section 3.2, plan step 5)")


@known_gap("metal", _UNPOOLED_METAL)
@known_gap("cuda", "CUDA's shared arrays are managed allocations (_HostBuffer), freed with "
                   "a device synchronization and never pooled (audit section 3.2)",
           kind="shared")
@pytest.mark.parametrize("kind", ["device", "readback", "upload", "shared"])
def test_freed_allocations_are_recycled(make, kind):
    """A buffer freed with _x_free -- or a shared array (empty_shared) dropped by its last
    holder -- gives its allocation to the next buffer of its kind and size: alloc/free
    cycles make no new device allocation after the first."""
    ctx = make()
    counters = instrument(ctx)
    # each kind its own size: a pool is the device's for the process (CUDA's _Pool), so an
    # earlier kind's freed allocation of the same size would serve this kind's first buffer
    size = {"device": 3 << 20, "readback": 7 << 19, "upload": 5 << 20, "shared": 7 << 20}[kind]

    def cycle():
        if kind == "shared":
            a = ctx.empty_shared((size // 8,), np.complex64)
            a[:4] = 1
            del a
        else:
            buf = ctx._x_alloc(size, readback=kind == "readback", upload=kind == "upload")
            ctx._x_free(buf)
    cycle()
    first = counters()["allocations"]
    assert first >= 1, "the first buffer was not counted (instrument needs updating)"
    for _ in range(20):
        cycle()
    assert counters()["allocations"] == first, "freed allocations were not recycled"


# ---- C12: timing ---------------------------------------------------------------------------
def test_timing_logs_one_interval_per_submission(make):
    """With timing on (_timing, as calibration sets it), every submission of a recorded list
    -- waited, left in flight and settled, or submitted and waited -- adds one (its label,
    device milliseconds > 0) entry to the timing log once timings() collects them."""
    ctx = make()
    w = Writer(make, ctx, np.random.default_rng(13), passes=1)
    ctx._x_run(w.native, True)
    ctx._timing = True
    ctx.timings()
    ctx.timing_log.clear()
    ctx._x_run(w.native, True)
    ctx._x_run(w.native, True, None, 1)
    ctx._x_run(w.native, False)
    ctx.settle_writes()
    ctx._x_submit(w.native, {}, 1)()
    log = [e for e in ctx.timings() if not e[0].startswith("k:")]
    ctx._timing = False
    assert [label for label, _ in log] == ["writer"] * 4, log
    assert all(np.isfinite(ms) and ms > 0 for _, ms in log), log


def test_a_timing_without_a_sample_is_no_time(make):
    """_x_time gives the least device time of `reps` runs after a warm-up: a positive finite
    time, or, when no run recorded one (reps=0 here), the value _choice.no_time reads as
    no time -- never infinity, which would rank as a slow measurement."""
    ctx = make()
    w = Writer(make, ctx, np.random.default_rng(14), passes=0)
    t = ctx._x_time(w.native, {}, 2)
    assert np.isfinite(t) and (t > 0 or _choice.no_time(t)), t
    t0 = ctx._x_time(w.native, {}, 0)
    assert _choice.no_time(t0), t0


# ---- C13-C15: list operations --------------------------------------------------------------
def test_fill_sets_every_word_of_its_range_in_each_row(make):
    """fill(buf, word, offset, nbytes, rows, pitch) sets every 32-bit word of bytes [offset,
    offset + nbytes) of each of `rows` rows `pitch` bytes apart to word -- 0 or 0xFFFFFFFF,
    the byte patterns the interface allows -- and nothing else; nbytes None fills to the
    buffer's end."""
    ctx = make()
    words = 4096
    buf = ctx._x_alloc(words * 4, readback=True)
    lst = ctx._x_list("fills")
    lst.fill(buf, 0)
    lst.barrier()
    lst.fill(buf, 0xFFFFFFFF, offset=64, nbytes=256, rows=5, pitch=1024)
    lst.fill(buf, 0xFFFFFFFF, offset=12288)
    lst.barrier()
    lst.readback(buf, words * 4)
    native = lst.end()
    ctx._x_run(native, True)
    want = np.zeros(words, np.uint32)
    for r in range(5):
        want[(64 + r * 1024) // 4:(64 + r * 1024 + 256) // 4] = 0xFFFFFFFF
    want[12288 // 4:] = 0xFFFFFFFF
    np.testing.assert_array_equal(_read(ctx, buf, np.uint32, words), want)


def test_update_is_in_order_with_the_lists_work(make):
    """update(buf, words) writes its words in order with the list's work: after a fill
    before it (and behind a barrier) and before work after it."""
    ctx = make()
    buf = ctx._x_alloc(4096, readback=True)
    lst = ctx._x_list("update")
    lst.fill(buf, 0xFFFFFFFF)
    lst.barrier()
    lst.update(buf, [1, 2, 3, 4])
    lst.barrier()
    lst.readback(buf, 4096)
    native = lst.end()
    ctx._x_run(native, True)
    got = _read(ctx, buf, np.uint32, 1024)
    np.testing.assert_array_equal(got[:4], [1, 2, 3, 4])
    assert (got[4:] == 0xFFFFFFFF).all()


def test_a_listed_dispatch_runs_the_count_a_run_wrote(make):
    """listed(kernel, count, max_groups, ...) runs the kernel over the first count[0] items
    of its list, count[0] written by the same run: the listed forward transforms exactly
    the rows its list names, and leaves the others as they were."""
    ctx = make()
    rng = np.random.default_rng(15)
    cap, k, rows = 64, 23, 64
    x = (rng.standard_normal((rows + 1) * N) + 1j * rng.standard_normal((rows + 1) * N)) \
        .astype(np.complex64)
    nser = x.size
    st = (np.arange(rows) * N + rng.integers(0, N, rows)).astype(np.uint32)
    ids = rng.permutation(rows).astype(np.uint32)
    align = max(16, int(ctx.props.offset_alignment))
    tab = ctx._x_alloc(3 * align + 4 * rows + 4 * cap, upload=True)
    host = np.zeros(tab.nbytes // 4, np.uint32)
    o_st, o_ids, o_args = 0, -(-4 * rows // align) * align, 0
    o_args = o_ids + -(-4 * cap // align) * align
    host[o_st // 4:o_st // 4 + rows] = st
    host[o_ids // 4:o_ids // 4 + cap] = np.resize(ids, cap)
    ctx._x_upload(tab, host, None)
    starts = ctx._x_section(tab, o_st, 4 * rows)
    listv = ctx._x_section(tab, o_ids, 4 * cap)
    args = ctx._x_section(tab, o_args, 16)
    series = _upload(ctx, x)
    spec = ctx._x_alloc(rows * N * 8, readback=True)
    _nan_fill(ctx, spec, rows * N * 8)
    lst = ctx._x_list("listed")
    lst.update(args, [k, 1, 1, 0])
    lst.barrier()
    lst.listed(ctx._x_kernel("fwd_listed", N), args, cap,
               [series, starts, spec, listv, args], (nser, 0))
    lst.barrier()
    lst.readback(spec, rows * N * 8)
    native = lst.end()
    ctx._x_run(native, True)
    got = _read(ctx, spec, np.complex64, rows * N).reshape(rows, N)
    done = np.zeros(rows, bool)
    done[ids[:k]] = True
    _close(got[done], _spectra(x, st[done], nser), "listed rows")
    assert np.isnan(got[~done]).all(), "rows past the count were written"


def test_sections_of_one_buffer_are_filled_updated_and_read_together(make):
    """Sections (_x_section) of one buffer at multiples of props.offset_alignment are
    filled and updated as buffers of their own, and read back with the buffer."""
    ctx = make()
    align = max(16, int(ctx.props.offset_alignment))
    buf = ctx._x_alloc(4 * align, readback=True)
    parts = [ctx._x_section(buf, i * align, align) for i in range(4)]
    lst = ctx._x_list("sections")
    lst.fill(buf, 0)
    lst.barrier()
    lst.fill(parts[1], 0xFFFFFFFF, nbytes=align)
    lst.fill(parts[3], 0xFFFFFFFF, offset=8, nbytes=align - 8)
    lst.fill(parts[3], 0xFFFFFFFF, nbytes=8)
    lst.barrier()
    lst.update(parts[2], [7, 8])
    lst.barrier()
    lst.readback(buf, 4 * align)
    native = lst.end()
    ctx._x_run(native, True)
    got = _read(ctx, buf, np.uint32, align).reshape(4, align // 4)
    assert not got[0].any()
    assert (got[1] == 0xFFFFFFFF).all() and (got[3] == 0xFFFFFFFF).all()
    np.testing.assert_array_equal(got[2][:2], [7, 8])
    assert not got[2][2:].any()
    np.testing.assert_array_equal(_read(ctx, buf, np.uint32, 2, offset=2 * align), [7, 8])


def test_a_fill_without_a_size_ends_at_the_end_of_its_section(make):
    """fill(view, word) without nbytes fills to the end of the view it was given -- a section's
    own end, not its buffer's: the sections after it keep their words."""
    ctx = make()
    align = max(16, int(ctx.props.offset_alignment))
    buf = ctx._x_alloc(3 * align, readback=True)
    lst = ctx._x_list("section fill")
    lst.fill(buf, 0)
    lst.barrier()
    lst.fill(ctx._x_section(buf, align, align), 0xFFFFFFFF)
    lst.barrier()
    lst.readback(buf, 3 * align)
    native = lst.end()
    ctx._x_run(native, True)
    got = _read(ctx, buf, np.uint32, 3 * align // 4).reshape(3, align // 4)
    assert (got[1] == 0xFFFFFFFF).all()
    assert not got[0].any() and not got[2].any(), "the fill ran past its section"


# ---- C16: fused batches ---------------------------------------------------------------------
@pytest.mark.parametrize("settle", ["before close", "after close"])
def test_fused_runs_give_unfused_results_and_settle(make, settle):
    """Inside a fused batch (_gpuexec.fused) runs that several contexts leave in flight are
    pending writes, as unfused: each has a write token, settle_writes waits for them (also
    before the batch is closed), and each writes what it writes alone."""
    rng = np.random.default_rng(16)
    ctxs = [make() for _ in range(3)]
    ws = [Writer(make, c, rng, captured=True) for c in ctxs]
    close = _gpuexec.fused()
    try:
        for c, w in zip(ctxs, ws):
            before = c.write_token()
            c._x_run(w.native, False)
            assert c.write_token() is not None and c.write_token() is not before
        if settle == "before close":
            ctxs[0].settle_writes()
    finally:
        close()
    ctxs[0].settle_writes()
    for w in ws:
        w.check("a fused run's output")


def test_a_run_outside_a_fused_batch_follows_its_pending_writes(make):
    """A run that is not fused (one not recorded in phases) is ordered after the pending
    writes that runs collected in an open fused batch left before it, as after any pending
    write."""
    rng = np.random.default_rng(17)
    a, b = make(), make()
    w = Writer(make, a, rng, captured=True)
    r = Reader(b, w)
    close = _gpuexec.fused()
    try:
        a._x_run(w.native, False)
        b._x_run(r.native, True)
        r.check("a reader outside the batch")
    finally:
        close()
        a.settle_writes()


# ---- idle and readers ----------------------------------------------------------------------
def test_idle_waits_for_every_run_of_the_context(make):
    """_x_idle() returns after every run the context submitted has finished: waited, left in
    flight or submitted, on any slot."""
    ctx = make()
    rng = np.random.default_rng(18)
    ws = [Writer(make, ctx, rng) for _ in range(3)]
    ctx._x_run(ws[0].native, False, None, None)
    wait1 = ctx._x_submit(ws[1].native, {}, 1)
    wait2 = ctx._x_submit(ws[2].native, {}, None)
    ctx._x_idle()
    for w in ws:
        w.check("a run the context was idle after")
    wait1()
    wait2()
    ctx.settle_writes()


@pytest.mark.parametrize("slot", [None, 1])
def test_after_readers_orders_the_next_run_after_readers_in_flight(make, slot):
    """After _x_after_readers(), the context's next (unslotted) run executes after every run
    on the device submitted before the call -- another context's reader still in flight on
    any slot -- so it may rewrite what those runs read."""
    rng = np.random.default_rng(19)
    a, b = make(), make()
    w = Writer(make, a, rng, passes=0)
    a._x_run(w.native, True)
    r = Reader(b, w, passes=16 if make.big else 1)
    wait = b._x_submit(r.native, {}, slot)
    a._x_after_readers()
    lst = a._x_list("rewrite")
    lst.barrier()
    lst.fill(w.out, 0)
    lst.barrier()
    rewrite = lst.end()
    a._x_run(rewrite, False)
    wait()
    r.check("a reader in flight before the rewrite")
    a.settle_writes()


# ---- C16b: kernel resolution ---------------------------------------------------------------
def test_a_kernel_the_device_cannot_run_is_reported_not_substituted(make):
    """_x_kernel raises UnsupportedSize for a build the device cannot run -- a gate-only
    build at a length none was built for, a two-stage kernel at a one-stage length -- and
    ValueError for a name that is no kernel, never handing back another kernel."""
    from matchedfilter import UnsupportedSize
    ctx = make()
    with pytest.raises(UnsupportedSize):
        ctx._x_kernel("tier1", 1 << 20, dict(gate=True))
    with pytest.raises(UnsupportedSize):
        ctx._x_kernel("tc1", N)
    with pytest.raises(ValueError):
        ctx._x_kernel("no such kernel", N)
    for name in ("compactc", "tier1", "tier1_c16", "fwd_tier0", "items", "tier1gate",
                 "refine_td"):
        assert isinstance(ctx._x_has_kernel(name, N), bool), name
    with pytest.raises(ValueError):
        ctx._x_has_kernel("no such kernel", N)


# ---- C17: what a driver reports ------------------------------------------------------------
#: What each documented DeviceProps field must hold: a test of the value.
def _positive(v):
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def _flag(v):
    return isinstance(v, bool)


def _name(v):
    return isinstance(v, str) and bool(v)


PROPERTY_TYPES = {
    "name": _name, "artifact_family": _name,
    "max_group_memory": _positive, "max_threads": _positive,
    "indirect_dispatch": _flag, "runtime_specialization": _flag, "load_time_constants": _flag,
    "max_dispatch_x": _positive,
    "max_binding_bytes": lambda v: v is None or _positive(v),
    "offset_alignment": lambda v: _positive(v) and v & (v - 1) == 0,
    "subgroup_size": _positive,
    "subgroup_range": lambda v: v is None or (len(v) == 2 and 0 < v[0] <= v[1]),
    "unified_memory": _flag, "managed_inputs": _flag, "offset_views": _flag,
    "host_pointer_views": _flag, "shared_queue": _flag, "fp16": _flag,
    "cache_budget": _positive,
    "memory_budget": lambda v: v is None or _positive(v),
    "device_root": _flag,
}


def test_a_driver_reports_every_documented_property(make):
    """A Context reports every property DeviceProps documents (ctx.props), each a value of
    its kind: the record is a DeviceProps, every field in its FIELDS is documented in its
    docstring and checked here, every field holds a value of its kind, the subgroup size
    lies in the subgroup range where there is one, and device_root is the driver's class
    attribute (what _gpuroot.device_root reads before it makes a context). inplace_feed,
    a driver attribute, is a boolean."""
    from matchedfilter._gpuhost import DeviceProps
    ctx = make()
    props = ctx.props
    assert type(props) is DeviceProps
    assert set(PROPERTY_TYPES) == set(DeviceProps.FIELDS)
    documented = set(re.findall(r"^ +(\w+)  +\S", DeviceProps.__doc__, re.M))
    assert set(DeviceProps.FIELDS) <= documented, set(DeviceProps.FIELDS) - documented
    bad = {f: getattr(props, f) for f in DeviceProps.FIELDS
           if not PROPERTY_TYPES[f](getattr(props, f))}
    assert not bad, bad
    if props.subgroup_range is not None:
        assert props.subgroup_range[0] <= props.subgroup_size <= props.subgroup_range[1]
    assert props.device_root is type(ctx).device_root
    assert isinstance(ctx.inplace_feed, bool)


def test_a_driver_names_its_device_and_shares_its_state(make):
    """Every context on a device has the same device state object (_device_state, which
    holds the device's pending writes; open while a buffer made on it can be freed) and the
    same properties record, which names the device as device_name does."""
    a, b = make(), make()
    assert a._device_state is not None and a._device_state is b._device_state
    assert a._device_state.open is True
    assert a.props is b.props
    assert a.props.name == a.device_name


# ---- interpreter exit ----------------------------------------------------------------------
_AT_EXIT = """
import atexit
import sys
sys.path[:0] = %r
measured = {}


def report():
    # Registered before the library is imported, so it runs after the library's own exit
    # handlers (atexit runs the last registered first).
    pool = measured.get("pool")
    if pool is not None:
        print("root bytes live after the exit handlers: %%d"
              %% (pool.live_bytes - measured["before"]), flush=True)


atexit.register(report)
import numpy as np
import matchedfilter as mf
import matchedfilter._errors, matchedfilter._shared
from matchedfilter import _gpuroot
backend = %r
if backend == "sim":
    import sim_driver
    ctx = sim_driver.Context()
    root_ctx = sim_driver.Context(device=ctx._device_state)
else:
    from conftest import gpu_context
    ctx, root_ctx = gpu_context(backend), gpu_context(backend)
arrays = lambda k: [ctx.empty_shared((1 << 16,), np.complex64) for _ in range(k)]
# Shared arrays held by modules torn down before and after the backend's (the order a
# module's globals are cleared at exit is the interpreter's).
matchedfilter._shared.held = arrays(2)
matchedfilter._errors.held = arrays(2)
np.held = arrays(2)
mf.held = arrays(2) + [ctx]
pool = getattr(root_ctx._device_state, "buffers", None)
if pool is not None:
    measured.update(pool=pool, before=pool.live_bytes)
# A device root, held for the process as _gpuroot.device_root holds one: its idle outputs
# (shared arrays) and its template buffer.
n = 1 << 16
root = _gpuroot._ROOTS["exit test"] = _gpuroot.DeviceRoot(root_ctx, "exit test")
root.set_template(n, np.ones(n // 2 + 1, np.complex64))
outputs = {(c, p): root.take_output(n, c, p) for c in range(2) for p in range(2)}
for (c, p), out in outputs.items():
    root.give_output(n, c, p, out)
del outputs, out
if pool is not None:
    assert pool.live_bytes > measured["before"]
print("ran")
"""


def test_teardown_at_exit_is_orderly(make):
    """At interpreter exit the library releases what it holds for the process -- a device
    root's outputs, template and context -- while every module is intact, so those destroys
    run: none of a device root's bytes are live after the exit handlers. Shared arrays a
    caller still holds then, in modules torn down before and after the backend's, are left
    to the process's end. Neither prints "Exception ignored" (four at the end of every
    Vulkan pycbc job: a device root's outputs freed while the interpreter cleared modules,
    their destroy() calling a backend function already cleared)."""
    import os
    import subprocess
    import sys
    tests = os.path.dirname(os.path.abspath(__file__))
    import matchedfilter
    path = [tests, os.path.dirname(os.path.dirname(matchedfilter.__file__))]
    out = subprocess.run([sys.executable, "-c", _AT_EXIT % (path, make.backend)],
                         capture_output=True, text=True, timeout=300, cwd=tests)
    assert out.returncode == 0 and "ran" in out.stdout, out.stderr[-2000:]
    assert "Exception ignored" not in out.stderr, out.stderr[-2000:]
    if make.backend in ("sim", "vulkan"):        # the backends whose device has a BufferPool
        assert "root bytes live after the exit handlers: 0" in out.stdout, out.stdout


# ---- the suite catches the faults that happened ---------------------------------------------
def _faulty(*faults):
    return _Maker("sim", faults)


#: For each simulated fault, the tests (with parameters) that must fail under it.
CATCHES = {
    "submit_not_pending": [(test_a_submission_is_a_pending_write_exactly_when_asked,
                            {"slot": 1, "pending": True}),
                           (test_another_context_reads_a_pending_write,
                            {"form": "submit", "slot": 1})],
    "run_ignores_slot": [(test_a_run_on_a_slot_follows_earlier_work_on_that_slot,
                          {"form": "in flight"})],
    "drops_pre_frees": [(test_one_off_recordings_are_freed_after_their_run,
                         {"form": "in flight"})],
    "no_pool": [(test_freed_allocations_are_recycled, {"kind": "device"}),
                (test_freed_allocations_are_recycled, {"kind": "shared"})],
    "ctypes_per_call": [(test_steady_runs_allocate_nothing_and_leave_no_cyclic_garbage,
                         {"wait": True})],
    "update_at_encode": [(test_update_is_in_order_with_the_lists_work, {})],
    "time_no_sample_inf": [(test_a_timing_without_a_sample_is_no_time, {})],
}


@pytest.mark.parametrize("fault", sorted(CATCHES))
def test_the_suite_catches_each_known_driver_fault(fault):
    """Each driver fault that happened (sim_driver.FAULTS), reproduced in the simulated
    driver, fails the conformance tests that state the contract it broke -- and those tests
    pass on the faultless simulated driver."""
    for test, params in CATCHES[fault]:
        good = _faulty()
        try:
            test(good, **params)
        finally:
            good.close()
        bad = _faulty(fault)
        try:
            with pytest.raises(AssertionError):
                test(bad, **params)
        finally:
            bad.close()
