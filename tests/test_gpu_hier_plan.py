"""What the shared hierarchical search (_gpuhier) records, on a driver that records only.

Every GPU backend runs this one plan, so these run everywhere (no device): a cascade
gates each tier with its own threshold, in order; its second tier and the refine run over
the survivor lists the device wrote; and the feed is chosen from what the driver reports
(kernels specialized when created read the spectra in place, others read packed bands).
The hardware tests (test_vk_cascade, test_cuda_parity, test_metal_backend) compare the
same calls against the CPU.
"""
import numpy as np
import pytest

from matchedfilter import _gpuhier
from matchedfilter._gpu_cache import InputUploads
from matchedfilter._gpuexec import Arg, Executor


class _Buf:
    def __init__(self, nbytes):
        self.nbytes = nbytes
        self.value = None
        self.writes = 0

    def write(self, array):
        self.value = np.asarray(array).copy()
        self.writes += 1

    def destroy(self):
        pass


def _check_words(words):
    """The driver contract (_gpuexec): each word a uint32, an Arg, or a tuple of at most
    four (one uint4 parameter). A driver that flattens tuples hides a longer one; CUDA
    passes it as a single 16-byte parameter."""
    for w in words:
        assert isinstance(w, (int, np.integer, Arg)) or (
            isinstance(w, tuple) and len(w) <= 4), w


class _List:
    def __init__(self, ops):
        self.ops = ops

    def dispatch(self, kernel, groups, buffers, words=(), offsets=None):
        _check_words(words)
        self.ops.append(("dispatch", kernel, buffers, words))

    def listed(self, kernel, count, max_groups, buffers, words=()):
        _check_words(words)
        self.ops.append(("listed", kernel, buffers, words, count))

    def barrier(self):
        self.ops.append(("barrier",))

    def stamp(self, name):
        self.ops.append(("stamp", name))

    def fill(self, buf, word):
        self.ops.append(("fill", buf, word))

    def update(self, buf, words):
        self.ops.append(("update", buf, tuple(words)))

    def readback(self, buf, nbytes):
        self.ops.append(("readback", buf, nbytes))

    def end(self):
        return self.ops


class Driver(Executor, InputUploads):
    """A driver whose kernels are their names and whose runs record their bindings. Every
    count reads back zero: no pair survives, so a result is all "no peak"."""
    max_dispatch_x = 65535
    storage_offset_alignment = 16
    subgroup_size = 32
    kernel_family = "fake"

    def __init__(self, inplace_feed=True, c16=False, one_bin=True):
        self.inplace_feed = inplace_feed
        self.c16, self.one_bin = c16, one_bin
        self._uploaded = {"data": {}, "tmpl": {}}
        self.runs = []

    def _x_kernel(self, name, n, consts=None):
        return (name, n, tuple(sorted((consts or {}).items())))

    def _x_has_c16(self, band):
        return self.c16

    def _x_has_kernel(self, name, n):
        return name != "tier1" or self.one_bin

    def _x_coarse_candidates(self, band):
        return [(32, 2, 1, False)]

    def _coarse_layout(self, band):
        return (32, 2, 1, False)

    def _gate_way(self, band):
        return "gate"

    def _x_alloc(self, nbytes, readback=False, upload=False):
        return _Buf(nbytes)

    def _x_upload(self, buf, array, slot):
        buf.write(array)

    def _x_list(self, label, once=False):
        return _List([])

    def _x_run(self, native, wait, binds=None, slot=None, pre=()):
        self.runs.append((native, binds, slot, list(pre)))

    def _x_submit(self, native, binds, slot, pre=()):
        self._x_run(native, False, binds, slot, pre)
        return lambda: None

    def _x_read(self, buf, out, offset=0):
        out[...] = 0

    def _x_view(self, buf, dtype, count):
        return np.zeros(count, dtype)

    def _x_release(self, native, done=False):
        self.__dict__.setdefault("released", []).append(done)

    @staticmethod
    def _x_free(buf):
        buf.destroy()

    @staticmethod
    def _x_section(buf, offset, nbytes):
        return ("section", buf, offset, nbytes)

    def _x_idle(self):
        self.__dict__["idles"] = self.__dict__.get("idles", 0) + 1


def _names(ops):
    return [(op[0], op[1][0]) for op in ops if op[0] in ("dispatch", "listed")]


def _phases(ops):
    """[(phase name, its ops)] split at the stamps."""
    out, cur = [], []
    for op in ops:
        if op[0] == "stamp":
            out.append((op[1], cur))
            cur = []
        else:
            cur.append(op)
    return out


def _words(binds, op):
    """The per-run words of an op: its Arg words looked up in binds."""
    return [binds[w.name] for w in op[3] if isinstance(w, Arg)]


def _call(ctx, cascade=True, **kw):
    n, b0, b1 = 4096, 128, 512
    d = np.ones((2, n), np.complex64)
    h = np.ones((3, n), np.complex64)
    if cascade:
        return ctx.hier_peaks(n, b1, d, h, h[:, :b0], 0.25, cascade_band=b0, ct1=h[:, :b1],
                              raw_thr1=0.75, threshold=5.0, **kw)
    return ctx.hier_peaks(n, b0, d, h, h[:, :b0], 0.5, **kw)


def test_cascade_gates_each_tier_with_its_own_threshold_in_order():
    ctx = Driver()
    idx, val = _call(ctx)
    assert idx.shape == (2, 3, 1) and (idx == -1).all() and not val.any()
    (ops, binds, _, _), = ctx.runs
    assert _names(ops) == [("dispatch", "gate"), ("dispatch", "compact"), ("listed", "tier1"),
                           ("dispatch", "compactl"), ("listed", "refine1")]
    compacts = [op for op in ops if op[0] == "dispatch" and op[1][0].startswith("compact")]
    thr = [np.uint32(_words(binds, op)[0][1]).view(np.float32) for op in compacts]
    assert thr == [np.float32(0.25), np.float32(0.75)]
    # The second tier runs over tier 0's survivors, the refine over tier 1's: the counts
    # each compaction wrote.
    tier, refine = [op for op in ops if op[0] == "listed"]
    rec = next(iter(ctx._exec_table().values()))
    assert tier[4] is rec.buffers["args0"] and refine[4] is rec.buffers["args1"]
    # Each tier's templates as uploaded, fp32 without an fp16 build.
    np.testing.assert_array_equal(rec.buffers["ct1"].value, np.ones((3, 512), np.complex64))
    # A one-bin build gates tier 1 alone (nbins 0: no peak search).
    assert binds["tier"][5] == 0


def test_one_tier_chain_gates_then_refines():
    ctx = Driver()
    _call(ctx, cascade=False)
    (ops, _, _, _), = ctx.runs
    assert _names(ops) == [("dispatch", "gate"), ("dispatch", "compact"), ("listed", "refine1")]


def test_without_a_one_bin_build_tier_one_searches_its_bin():
    ctx = Driver(one_bin=False)
    _call(ctx)
    (ops, binds, _, _), = ctx.runs
    assert ("listed", "tier") in _names(ops) and binds["tier"][5] == 1


@pytest.mark.parametrize("inplace", [True, False])
def test_the_feed_follows_the_driver_feature(inplace):
    """Kernels specialized when created read the spectra at their stride; others read the
    bands a pack kernel wrote (stride 0), each tier its own."""
    ctx = Driver(inplace_feed=inplace, c16=True)
    _call(ctx)
    (ops, _, _, _), = ctx.runs
    names = _names(ops)
    assert names.count(("dispatch", "pack")) == (0 if inplace else 2)
    coarse = next(op for op in ops if op[0] == "dispatch" and op[1][0] == "coarse")
    assert dict(coarse[1][2])["stride"] == (4096 if inplace else 0)
    # The fp16 tier's templates are packed half2 words, and its data is scaled by the same
    # power of two on either feed: as the coarse kernel reads it, or as the pack writes it.
    rec = next(iter(ctx._exec_table().values()))
    assert rec.buffers["ct0"].value.dtype == np.uint32
    et = _gpuhier.c16_template_exp(np.ones((3, 128), np.complex64))
    ed = _gpuhier.c16_data_exp(128, 0.25, et)
    if inplace:
        assert dict(coarse[1][2])["scale"] == ed
    else:
        pack0 = next(op for op in ops if op[0] == "dispatch" and op[1][0] == "pack")
        assert pack0[3][3] == 1 and pack0[3][4] == _gpuhier._bits(2.0 ** ed)
        assert dict(coarse[1][2])["scale"] == 0


def test_async_calls_are_deferred_and_keyed_by_slot():
    ctx = Driver()
    pend = [_call(ctx, slot=s, async_submit=True) for s in (0, 1)]
    # Nothing was waited on: each slot has its own record and buffers.
    assert [r[2] for r in ctx.runs] == [0, 1]
    assert len(ctx._exec_table()) == 2 and len(ctx._inflight) == 2
    idx, _ = pend[0]()
    assert (idx == -1).all() and len(ctx._inflight) == 1
    ctx._drain()
    assert not ctx._inflight and pend[1].done


def test_a_deferred_forward_runs_first_in_the_same_submission():
    ctx = Driver()
    ctx._defer("forward", {"x": 1}, 3, None)
    _call(ctx, slot=3)
    (_, _, slot, pre), = ctx.runs
    assert slot == 3 and pre == [("forward", {"x": 1})] and not ctx._pending()


def test_an_incomplete_or_unordered_cascade_raises():
    ctx = Driver()
    n = 4096
    d = np.ones((1, n), np.complex64)
    h = np.ones((1, n), np.complex64)
    with pytest.raises(ValueError):
        ctx.hier_peaks(n, 512, d, h, h[:, :128], 0.5, cascade_band=128)
    with pytest.raises(ValueError):
        ctx.hier_peaks(n, 128, d, h, h[:, :512], 0.5, cascade_band=512,
                       ct1=h[:, :128], raw_thr1=0.5)


# --- input residency: what each call writes -------------------------------------------
def _inputs(ctx, names=("data", "tmpl", "ct0")):
    return [rec.buffers[k] for rec in ctx._exec_table().values() for k in names
            if k in rec.buffers]


@pytest.mark.parametrize("c16", [False, True])
@pytest.mark.parametrize("changed", ["data", "tmpl"])
def test_revisited_window_receives_updated_inputs(c16, changed):
    """Each window is its own record: a caller's dirty flag, cleared after one call, must
    still reach the other window's copy."""
    ctx = Driver(c16=c16)
    n = 2048
    data = np.ones((1, n), np.complex64)
    tmpl = np.ones((1, n), np.complex64)

    def run(window, dirty):
        ctx.hier_peaks(n, 1024, data, tmpl, tmpl[:, :1024], 0., window=window,
                       binsize=n // 2, upload_data=dirty == "data", upload_tmpl=dirty == "tmpl")
        return ctx.runs[-1][0]

    a, b = (0, n), (100, n // 2)
    run(a, None)
    native_b = run(b, None)
    (data if changed == "data" else tmpl)[:] = 7 + 2j
    run(a, changed)
    assert run(b, None) is native_b      # caller has already cleared its dirty flag
    rec = next(r for r in ctx._exec_table().values() if r.native is native_b)
    target = rec.buffers[changed]
    np.testing.assert_array_equal(target.value, data if changed == "data" else tmpl)
    coarse = tmpl[:, :1024]
    if c16:                              # packed at the tier's template scale
        et = _gpuhier.c16_template_exp(coarse)
        coarse = _gpuhier.pack_half2(_gpuhier.pow2_scaled(coarse, et))
    np.testing.assert_array_equal(rec.buffers["ct0"].value, coarse)
    writes = target.writes
    run(b, None)
    assert target.writes == writes       # an unchanged input is not written again


def test_split_dispatch_keeps_resident_inputs():
    """More bins than one kernel takes split into pieces, each its own record: an
    unchanged call writes none of their inputs."""
    ctx = Driver()
    n = 8192                             # three full splits and a shorter last piece
    d = np.ones((1, n), np.complex64)
    h = np.ones((1, n), np.complex64)

    def run(dirty):
        ctx.hier_peaks(n, 1024, d, h, h[:, :1024], 0., binsize=1, window=(17, n),
                       upload_data=dirty, upload_tmpl=dirty)

    for _ in range(2):
        d *= 2
        h *= 3
        run(True)
        assert len(ctx._exec_table()) > 1
        warm = sum(b.writes for b in _inputs(ctx))
        run(False)
        assert sum(b.writes for b in _inputs(ctx)) == warm, \
            "unchanged split call re-uploaded inputs"


def test_changing_data_keeps_templates_resident():
    ctx = Driver()
    n = 2048
    d, h = np.ones((1, n), np.complex64), np.ones((1, n), np.complex64)

    def run():
        ctx.hier_peaks(n, 1024, d, h, h[:, :1024], 0., upload_data=True, upload_tmpl=False)

    run()
    for _ in range(3):
        d *= 2
        run()
    rec, = ctx._exec_table().values()
    assert rec.buffers["tmpl"].writes == 1 and rec.buffers["ct0"].writes == 1
    assert rec.buffers["data"].writes == 4


# --- the word contract, on the operations that do not run through hier_peaks above ---
def test_coarse_layout_timing_passes_scalar_words():
    ctx = Driver(c16=True)
    ctx._x_time = lambda native, binds, reps: 1e-3
    cands = [(32, 1, 1, False), (32, 2, 1, False), (32, 2, 2, False)]
    times = _gpuhier.HierOps._time_coarse_layouts(ctx, 128, cands)
    assert set(times) == set(cands)


def test_follow_up_items_pass_scalar_words(monkeypatch):
    from matchedfilter import _gpuexec
    monkeypatch.setattr(_gpuexec, "shared_view", lambda array, ctx: array)
    ctx = Driver()
    n = 1024
    d = np.ones((4, n), np.complex64)
    h = np.ones((2, n), np.complex64)
    out = ctx.peaks_items(n, d, h, [(0, n, 0, 2, 0), (10, 500, 1, 4, 1)], n, 0.0)
    assert [i.shape for i, _ in out] == [(2, 1, 1), (3, 1, 1)]


# --- the band/full choice -------------------------------------------------------------
def test_the_band_feed_follows_the_measured_refine_fraction(monkeypatch):
    """A call on shared spectra claims its deferred forward and writes only the bands when
    the blocks its shape refined last time make that the fewer bytes, or when nothing is
    measured yet (a gate dismisses nearly every block); a measured large fraction takes the
    full forward. Every call notes its fraction, banded or not."""
    monkeypatch.setattr(_gpuhier, "shared_view", lambda array, ctx: array)
    ctx = Driver()
    n = 4096
    d = np.ones((2, n), np.complex64)
    h = np.ones((3, n), np.complex64)
    claimed = []
    for f in (None, 0.9, 0.0):
        if f is not None:
            ctx._band_f[(n, 128, 2, 3)] = f
        source = (n, None, None, 0, 2, 8 * n, 0, d, d.ctypes.data)
        ctx._defer("forward", {}, 0, source)
        claims = _gpuhier.CLAIMS[0]
        ctx.hier_peaks(n, 128, d, h, h[:, :128], 0.5, slot=0)
        claimed.append(_gpuhier.CLAIMS[0] - claims)
        assert ctx._band_f[(n, 128, 2, 3)] == 0.0      # noted: no pair refined
        ctx.cancel_forward()
    assert claimed == [1, 0, 1]
    assert ("dispatch", "fwd_bands") in _names(ctx.runs[-1][0])


@pytest.mark.parametrize("cascade", [False, True])
@pytest.mark.parametrize("way", ["dense", "rows", "compact"])
@pytest.mark.parametrize("feed", ["inplace", "pack", "bands", "tier0"])
def test_no_phase_orders_work_inside_itself(monkeypatch, feed, way, cascade):
    """A fused batch runs a phase's commands unordered, its barriers at the phase's end: a
    barrier between two pieces of one phase's work would be dropped (device compaction once
    shared the refine's phase and read its output half-written)."""
    from matchedfilter import _gpuexec
    monkeypatch.setattr(_gpuhier, "shared_view", lambda array, ctx: array)
    monkeypatch.setattr(_gpuexec.Measured, "way", lambda self: (way, False))
    monkeypatch.setenv("MF_BAND_FORWARD", "1" if feed in ("bands", "tier0") else "0")
    ctx = Driver(inplace_feed=feed != "pack", c16=feed in ("tier0", "pack", "inplace"))
    n = 4096
    d = np.ones((2, n), np.complex64)
    h = np.ones((3, n), np.complex64)
    if feed in ("bands", "tier0"):
        ctx._defer("forward", {}, 0, (n, None, None, 0, 2, 8 * n, 0, d, d.ctypes.data))
    kw = dict(cascade_band=128, ct1=h[:, :512], raw_thr1=0.5) if cascade else {}
    ctx.hier_peaks(n, 512 if cascade else 128, d, h, h[:, :128], 0.5, slot=0,
                   sparse=way != "dense", **kw)
    (ops, _, _, _), = ctx.runs
    assert ("dispatch", "compact_peaks") in _names(ops) or way != "compact"
    if feed in ("bands", "tier0"):
        assert ("dispatch", "fwd_bands" if feed == "bands" else "fwd_tier0") in _names(ops)
    for name, work in _phases(ops):
        kinds = [op[0] for op in work if op[0] != "readback"]
        assert "barrier" not in kinds[:-1] or all(k == "barrier" for k in
                                                  kinds[kinds.index("barrier"):]), (name, kinds)


def test_an_unslotted_run_leaves_unrelated_deferred_work_for_its_consumer(monkeypatch):
    """An unslotted run (a middle-stage correlation) runs only the deferred work that writes
    what it binds: another slot's forward stays deferred, for its hierarchical call to claim.
    Flushing every slot's work once cost each claim and made the host wait on it."""
    monkeypatch.setattr(_gpuhier, "shared_view", lambda array, ctx: array)
    from matchedfilter import _gpuexec
    monkeypatch.setattr(_gpuexec, "shared_view", lambda array, ctx: array)
    ctx = Driver()
    n = 4096
    d = np.ones((2, n), np.complex64)
    other = np.ones((2, n), np.complex64)
    h = np.ones((3, n), np.complex64)
    ctx._defer("fwd-d", {}, 1, (n, None, None, 0, 2, 8 * n, 0, d, d.ctypes.data))
    ctx._defer("fwd-other", {}, 2, (n, None, None, 0, 2, 8 * n, 0, other, other.ctypes.data))
    ctx.peaks(n, other, h, binsize=n)              # unslotted, binds `other` only
    ran = [r[0] for r in ctx.runs]
    assert "fwd-other" in ran and "fwd-d" not in ran
    assert list(ctx._pending()) == [1]
    before = _gpuhier.CLAIMS[0]
    ctx._band_f = {(n, 128, 2, 3): 0.0}           # the band feed is wanted
    monkeypatch.setenv("MF_BAND_FORWARD", "1")
    ctx.hier_peaks(n, 128, d, h, h[:, :128], 0.5, slot=1)
    assert _gpuhier.CLAIMS[0] == before + 1 and not ctx._pending()


def test_clearing_a_context_waits_once_then_frees_every_record():
    """A cleared context (clear_cache, a dropped trial layout) waits for its own work once
    and frees every record as finished: a device-wide wait per record stalled every other
    plan sharing the device, once per record."""
    ctx = Driver()
    for nd in (1, 2, 3):
        n = 4096
        d = np.ones((nd, n), np.complex64)
        h = np.ones((3, n), np.complex64)
        ctx.hier_peaks(n, 128, d, h, h[:, :128], 0.5)
    assert len(ctx._exec_table()) == 3
    ctx._evict_all()
    assert not ctx._exec_table()
    assert ctx.idles == 1 and ctx.released == [True, True, True]


def test_a_claimed_forward_record_outlives_its_claimers_recording(monkeypatch):
    """The claimer binds the claimed forward's staged block starts: under a cache budget
    of one byte, making room for the hierarchical record evicted that forward record and
    its kernels read freed memory (a CUDA illegal address)."""
    from matchedfilter import _gpuexec
    monkeypatch.setattr(_gpuhier, "shared_view", lambda array, ctx: array)
    monkeypatch.setattr(_gpuexec, "shared_view", lambda array, ctx: array)
    ctx = Driver()
    ctx.cache_limit_bytes = 1
    n = 4096
    series = np.ones(4 * n, np.complex64)
    d = np.zeros((2, n), np.complex64)
    h = np.ones((3, n), np.complex64)
    ctx.forward(n, series, np.array([0, n], np.uint32), d, defer=True, slot=0)
    fkey = next(k for k in ctx._exec_table() if k[0] == "forward")
    evicted = []
    real = ctx._exec_evict
    ctx._exec_evict = lambda key, done=False: (evicted.append(key), real(key, done))[1]
    claims = _gpuhier.CLAIMS[0]
    ctx.hier_peaks(n, 128, d, h, h[:, :128], 0.5, slot=0)
    assert _gpuhier.CLAIMS[0] == claims + 1
    assert fkey not in evicted and "_exec_hold" not in ctx.__dict__
