"""A GPU call's peaks assembled in the extension (_core.assemble_peaks), the assembly the CPU
step table uses, against what filter_series' Python assembly gave before it was removed.

The hierarchical record's readback buffers (counts words, survivor rows, dense lags and
values, the compacted list) are written with synthetic peaks on the simulated driver
(tests/sim_driver.py), in every way a sparse result is read, with cascades, direct refines,
block orders, ragged bin counts and window-bin merges, several batches a call and several
calls and jobs at once. DIGESTS holds each case's result as the Python path produced it at
5acd2207 (filter_series' _consume_into, _merge_window_bins and _results_from over
_hier_result, _SparsePeaks.combine and _RaggedSplit), order included, and the work counters
_account kept; host results (dense and sparse) of the general loop are cases too. On a GPU,
a batch of real leaf calls is assembled against its calls made one at a time.

Records whose buffers are sections of a search's arena (_gpuhost.Arena), in each layout the
simulated device takes (sections packed in shared blocks, readback buffers of the context's
own, a block per section), are read as records without an arena are, also when two tenants
take the arena in turns; a lease's end leaves no readback view of its sections. On a GPU two
searches alternate on the device's arena against runs without one, and a call compacts more
peaks than the 4,096 records a run copies back where the host does not see device memory.
"""
import hashlib

import numpy as np
import pytest

from sim_driver import Context, stated_props


def _cases():
    """The synthetic cases: per case (name, way, cascade, direct, nt, nbins, batches, order,
    ragged, merge), each batch's rows."""
    rng = np.random.default_rng(20261128)
    out = []
    for k, (way, cascade, direct, ordered, ragged, merged) in enumerate([
            ("rows", False, False, False, False, False),
            ("rows", True, False, True, False, False),
            ("rows", True, True, False, True, False),
            ("compact", False, False, False, False, False),
            ("compact", True, True, True, False, True),
            ("compact", False, False, True, True, True),
            ("rows", False, True, True, True, True),
            ("dense", False, False, False, False, False),
            ("dense", True, False, True, True, True),
            ("host-dense", False, False, False, True, True),
            ("host-sparse", False, False, False, False, True),
            ("rows", False, False, False, False, False)]):        # a call with no peaks
        nt = int(rng.integers(1, 7))
        nbins = int(rng.integers(1, 5))
        batches = [int(rng.integers(1, 9)) for _ in range(int(rng.integers(1, 4)))]
        out.append(dict(name="case%d" % k, way=way, cascade=cascade, direct=direct, nt=nt,
                        nbins=nbins, batches=batches, ordered=ordered, ragged=ragged,
                        merged=merged, empty=k == 11, seed=1000 + k))
    return out


def _case_data(case):
    """A case's inputs: per batch its dense lags (-1 empty) and values over (rows, nt, nbins)
    and the survivor pairs in device order; the geometry (bank template indices, block starts
    in output order, block order, bin counts, block length, window starts, merge bin size)."""
    rng = np.random.default_rng(case["seed"])
    nt, nbins = case["nt"], case["nbins"]
    nrows = sum(case["batches"])
    block_len = 64
    batches = []
    for nd in case["batches"]:
        pairs = nd * nt
        lags = np.full((nd, nt, nbins), -1, np.int32)
        vals = np.zeros((nd, nt, nbins), np.complex64)
        surv = np.flatnonzero(rng.random(pairs) < (0.0 if case["empty"] else 0.6))
        rng.shuffle(surv)                           # the compaction's atomics' order
        for p in surv:
            b, t = divmod(int(p), nt)
            hit = rng.random(nbins) < 0.7
            lags[b, t, hit] = rng.integers(0, block_len, int(hit.sum()))
            vals[b, t, hit] = (rng.standard_normal(int(hit.sum()))
                               + 1j * rng.standard_normal(int(hit.sum()))).astype(np.complex64)
        batches.append((lags, vals, surv.astype(np.uint32)))
    templates = np.sort(rng.choice(1000, nt, replace=False)).astype(np.int64)
    starts = np.sort(rng.choice(np.arange(0, 40 * nrows, 8), nrows, replace=False)).astype(np.uintp)
    order = rng.permutation(nrows).astype(np.int64) if case["ordered"] else None
    row_bins = (rng.integers(1, nbins + 1, nrows).astype(np.int64)
                if case["ragged"] and nbins > 1 else None)
    win_starts = (np.array([0, 40 * nrows // 3, 2 * 40 * nrows // 3 + 5], np.int64)
                  if case["merged"] else None)
    return batches, templates, starts, order, row_bins, block_len, win_starts, 16


def _record(ctx, case, lags, vals, surv):
    """A record holding one batch's readback as the device writes it. Its buffers are made as
    the hierarchical record makes them (Executor._exec_buffer, _exec_section): sections of
    the arena lease in force on the context's device where there is one and it holds the
    kind, else buffers of the context's own; the counters are sections of the counts buffer
    (of its base block, at the summed offset, where it is itself a section)."""
    from matchedfilter._gpuexec import Record
    nd, nt, nbins = lags.shape
    pairs, out = nd * nt, nd * nt * nbins
    rec = Record()
    B = rec.buffers

    def buf(name, nbytes, readback=False):
        return ctx._exec_buffer(rec, name, nbytes=nbytes, readback=readback)
    names = ["args0"] + (["args1"] if case["cascade"] else []) + ["count", "fbargs"]
    counts = buf("counts", 16 * len(names), readback=True)
    for j, name in enumerate(names):
        B[name] = ctx._exec_section(counts, 16 * j, 16)
    if not case["direct"]:
        del B["fbargs"]
    if case["way"] != "compact":
        del B["count"]
    words = ctx._x_view(counts, np.uint32, 4 * len(names))
    last = "args1" if case["cascade"] else "args0"
    words[:] = 0
    words[names.index(last) * 4] = surv.size
    if case["cascade"]:
        words[0] = surv.size + 3                    # tier 0's passes
    if case["direct"]:
        words[names.index("fbargs") * 4] = surv.size // 2
    buf("cidx0", pairs * 4)
    sv = buf("surv%d" % (1 if case["cascade"] else 0), pairs * 4, readback=True)
    ctx._x_view(sv, np.uint32, surv.size)[:] = surv
    bi = buf("idx", out * 4, readback=True)
    bv = buf("val", out * 8, readback=True)
    li = ctx._x_view(bi, np.int32, out)
    lv = ctx._x_view(bv, np.complex64, out)
    if case["way"] == "rows":
        # only the survivors' bins are written (no fill)
        li[:] = 12345
        lv[:] = np.complex64(7 + 7j)
        for p in surv:
            li[p * nbins:(p + 1) * nbins] = lags.reshape(pairs, nbins)[p]
            lv[p * nbins:(p + 1) * nbins] = vals.reshape(pairs, nbins)[p]
    else:
        li[:] = lags.reshape(-1)
        lv[:] = vals.reshape(-1)
    if case["way"] == "compact":
        lst = buf("list", out * 16, readback=True)
        rows = [(p * nbins + b) for p in surv for b in range(nbins)
                if lags.reshape(pairs, nbins)[p, b] >= 0]
        recs = np.zeros((len(rows), 4), np.uint32)
        for r, pos in enumerate(rows):
            recs[r, 0] = pos
            recs[r, 1] = np.int32(li[pos]).view(np.uint32)
            recs[r, 2:4] = np.array([lv[pos]], np.complex64).view(np.uint32)
        recs = recs[np.random.default_rng(len(rows)).permutation(len(rows))]
        ctx._x_view(lst, np.uint32, recs.size)[:] = recs.reshape(-1)
        words[names.index("count") * 4] = len(rows)
    return rec


def _digest(res, work):
    h = hashlib.sha256()
    for a in res:
        a = np.ascontiguousarray(a)
        h.update(str(a.dtype).encode())
        h.update(a.tobytes())
    h.update(np.asarray(work, np.int64).tobytes())
    return h.hexdigest()[:24]


#: Each case's (FilterResults, work counters) digest from the Python assembly at 5acd2207
#: (recorded by running this module's cases through that tree's _hier_result,
#: _SparsePeaks.combine, _RaggedSplit, _consume_into, _merge_window_bins and _results_from).
DIGESTS = {
    "case0": "f3a0ffebc29c85903a83208e",
    "case1": "6f81e9d96980ad2b25c45283",
    "case2": "1c3fc5c351dc612539dac193",
    "case3": "eba89342a86ea7ae8d05b72d",
    "case4": "aebdaf2bc3033e1bcae146f8",
    "case5": "12021ee3b1b69168fdb1a361",
    "case6": "9bf009b13579dddb47c04309",
    "case7": "cdd64ce8950a17b798655d08",
    "case8": "ea90b0b7520189d827855743",
    "case9": "c753e16aa41185dfaed532af",
    "case10": "a379959d465c17b06f8965e5",
    "case11": "61ca6a9bc9bd4b0fa2a0068b",
}


def _new_job(ctx, case, records):
    """The case as a job of assemble_peaks (the readbacks of its batches' records, or its
    host results), and the work counters it adds to. The records are appended to records:
    a readback's views name their buffers' memory, which the record holds (the context's
    table, on a device)."""
    from matchedfilter._results import _SparsePeaks
    batches, templates, starts, order, row_bins, block_len, win_starts, bs = _case_data(case)
    nt, nbins = case["nt"], case["nbins"]
    work = np.zeros(6, np.int64)
    parts, b0 = [], 0
    if case["way"].startswith("host"):
        lags = np.concatenate([b[0] for b in batches]).astype(np.int64)
        vals = np.concatenate([b[1] for b in batches])
        if case["way"] == "host-dense":
            parts.append((0, (lags, vals)))
        else:
            flat = np.flatnonzero(lags >= 0)
            parts.append((0, _SparsePeaks(lags.shape, flat, lags.reshape(-1)[flat],
                                          vals.reshape(-1)[flat])))
        geometry = (templates, starts, None, row_bins, nt, nbins, block_len, None)
    else:
        for lags, vals, surv in batches:
            rec = _record(ctx, case, lags, vals, surv)
            records.append(rec)
            parts.append((b0, ctx._readback(rec, lags.shape, case["way"], case["cascade"])))
            b0 += lags.shape[0]
        geometry = (templates, starts, order, row_bins, nt, nbins, block_len, work)
    return ([(geometry, parts)], win_starts, (bs,) if win_starts is not None else ()), work


@pytest.mark.parametrize("unified", [True, False])
def test_device_readbacks_assemble_as_the_python_path_did(unified):
    """Every case, all in one assemble_peaks call, equals the Python path's result (order
    included) and work counters; with the readback viewed in place (unified memory) and
    through the bytes a recording reads back (a page-locked copy's prefix)."""
    from matchedfilter import _core
    from matchedfilter._results import FilterResults
    ctx = Context()
    ctx.props = stated_props(unified_memory=unified)
    if not unified:
        ctx._SPARSE_FIRST = 3          # compacted lists longer than the copy, read per run
    cases = _cases()
    records = []
    jobs, works = zip(*(_new_job(ctx, c, records) for c in cases))
    offsets, *cols = _core.assemble_peaks(list(jobs))
    offsets = np.frombuffer(offsets, np.int64)
    cols = [np.frombuffer(c, d) for c, d in
            zip(cols, (np.int64, np.int64, np.complex64, np.int64, np.int64))]
    got = {}
    for k, case in enumerate(cases):
        res = FilterResults(*(c[offsets[k]:offsets[k + 1]] for c in cols))
        got[case["name"]] = _digest(res, works[k])
    assert got == DIGESTS


def test_a_read_back_result_is_the_python_paths():
    """_hier_result (a call collected on its own, the reader assemble_peaks uses) gives the
    peaks and counters the Python reader gave, in flat order."""
    from matchedfilter._results import _SparsePeaks
    ctx = Context()
    for case in _cases():
        if case["way"] not in ("rows", "compact"):
            continue
        lags, vals, surv = _case_data(case)[0][0]
        rec = _record(ctx, case, lags, vals, surv)
        sp = ctx._hier_result(rec, lags.shape, True, case["way"], case["cascade"])
        assert isinstance(sp, _SparsePeaks) and sp.shape == lags.shape
        flat = np.flatnonzero(lags.reshape(-1) >= 0)
        flat = flat[np.isin(flat // case["nbins"], surv)]
        np.testing.assert_array_equal(sp.flat, flat)
        np.testing.assert_array_equal(sp.idx, lags.reshape(-1)[flat])
        np.testing.assert_array_equal(sp.val, vals.reshape(-1)[flat])
        assert ctx.last_refinements == surv.size
        assert ctx.last_fft_refinements == (surv.size // 2 if case["direct"] else surv.size)
        assert ctx.last_tier0_checked == lags.shape[0] * case["nt"]


#: The simulated device's setups an arena is laid out for (tests/test_gpu_arena.py): a host
#: that sees device memory in place (every kind packed in shared blocks), one that does not
#: (unified_memory False, as CUDA: readback buffers are the context's own, device-only
#: scratch in the arena), and one that orders work by allocation (allocation_hazards, as
#: Metal: a block per section).
ARENA_SETUPS = {"host-visible": {}, "device-only": dict(unified_memory=False),
                "allocation-hazards": dict(allocation_hazards=True)}


class _Tenant:
    """An arena lease's owner, as a search is (Arena.begin holds it weakly)."""


def _arena_context(setup):
    """A simulated context and an arena on its device in one of ARENA_SETUPS."""
    import sim_driver
    from matchedfilter._gpuhost import Arena
    dev = sim_driver._Device()
    dev.props = stated_props(**ARENA_SETUPS[setup])
    return Context(device=dev), Arena(Context(device=dev))


def _lease_records(ctx, lease, cases, pad, key):
    """Records of the cases' batches on `lease`, after a pad section of `pad` bytes of each
    kind the arena holds (so the records' sections lie at offsets other than 0 where
    sections share blocks), each in ctx's executor table under (key, k) with an empty
    recording, as a recorded call's record is (so the lease's end evicts it). Returns the
    jobs and work counters (_new_job) and the records."""
    for readback in (False, True):
        if lease.arena.holds(readback=readback):
            lease.take(ctx, pad, readback=readback)
    records = []
    jobs, works = zip(*(_new_job(ctx, c, records) for c in cases))
    for k, rec in enumerate(records):
        rec.native = ctx._x_list("assembly test").end()
        ctx._exec_table()[(key, k)] = rec
    return jobs, works, records


def _assembled_digests(cases, jobs, works):
    """Each case's digest (_digest) from one assemble_peaks call over the jobs, with the work
    counters but the tier-0 pairs checked: that one is read from the size of the record's
    tier-0 index buffer (cidx0), which an arena section rounds up to 16 bytes, so a batch of
    fewer than four pairs counts four there (on main too; a roofline counter, not a peak)."""
    from matchedfilter import _core
    from matchedfilter._results import FilterResults
    offsets, *cols = _core.assemble_peaks(list(jobs))
    offsets = np.frombuffer(offsets, np.int64)
    cols = [np.frombuffer(c, d) for c, d in
            zip(cols, (np.int64, np.int64, np.complex64, np.int64, np.int64))]
    return {case["name"]: _digest(FilterResults(*(c[offsets[k]:offsets[k + 1]] for c in cols)),
                                  works[k][:5]) for k, case in enumerate(cases)}


def _reference_digests(cases):
    """_assembled_digests of the cases' records made without an arena (buffers of a
    context's own), whose assembly equals the Python path's (DIGESTS:
    test_device_readbacks_assemble_as_the_python_path_did)."""
    records = []
    jobs, works = zip(*(_new_job(Context(), c, records) for c in cases))
    return _assembled_digests(cases, jobs, works)


@pytest.mark.parametrize("setup", sorted(ARENA_SETUPS))
def test_readbacks_of_arena_sections_assemble_as_the_python_path_did(setup):
    """Records whose buffers are sections of an arena lease's blocks, at offsets other than 0
    where sections share blocks, are read back as the Python path read them: the counters'
    words are found relative to the counts section handed to the reader, and every view
    reads its own section. (Word indices taken from the start of the block fail here, in the
    host-visible setup.)"""
    ctx, arena = _arena_context(setup)
    if setup == "device-only":
        ctx._SPARSE_FIRST = 3          # compacted lists longer than the copy, read per run
    lease = arena.begin(_Tenant())
    cases = [c for c in _cases() if not c["way"].startswith("host")]
    jobs, works, records = _lease_records(ctx, lease, cases, 1000, "arena sections")
    offsets = [getattr(rec.buffers["counts"], "offset", 0) for rec in records]
    if setup == "host-visible":
        assert all(getattr(rec.buffers["counts"], "lease", None) is lease for rec in records)
        assert min(offsets) > 0
    assert _assembled_digests(cases, jobs, works) == _reference_digests(cases)


@pytest.mark.parametrize("setup", sorted(ARENA_SETUPS))
def test_two_tenants_alternating_on_an_arena_read_their_own_readbacks(setup):
    """Two tenants take an arena in turns, as two searches do (a lease ends when the other's
    begins), each with its own records on the bytes the other's records used: every turn's
    readbacks assemble to what its cases' records give without an arena. When a lease ends,
    every record on it is evicted with its readback views, also a record something else
    still holds (a call plan's handle holds its record), and, with the collector off, every
    view made in the lease dies at once; a result in flight at the end is collected into
    host arrays first, so taking it after the next tenant has written the same bytes gives
    its own peaks. A readback cached past its lease would read the next tenant's peaks."""
    import gc
    import weakref
    ctx, arena = _arena_context(setup)
    device_cases = [c for c in _cases() if not c["way"].startswith("host")]
    tenants = [_Tenant(), _Tenant()]
    shares = (device_cases[0::2], device_cases[1::2])
    held = None
    for turn in range(4):
        cases = shares[turn % 2]
        lease = arena.begin(tenants[turn % 2])
        assert lease is not None
        if held is not None:
            # the previous lease has ended: its records evicted, its views gone with them
            previous, kept, views, pending, want = held
            assert not [key for key, rec in ctx._exec_table().items() if key[0] == turn - 1]
            assert kept.readback is None
            assert [v() for v in views] == [None] * len(views), "a readback outlived its lease"
            assert pending.done
            gc.enable()
        jobs, works, records = _lease_records(ctx, lease, cases, 512 * (1 + turn % 2), turn)
        assert _assembled_digests(cases, jobs, works) == _reference_digests(cases)
        if held is not None:
            # the previous tenant's result in flight at its lease's end, taken now
            live, got = pending.take()
            assert not live
            np.testing.assert_array_equal(got.flat, want.flat)
            np.testing.assert_array_equal(got.idx, want.idx)
            np.testing.assert_array_equal(got.val, want.val)
        # a result left in flight (as _hier_run tracks one), and its expected peaks
        rec, case = records[0], cases[0]
        shape = (case["batches"][0], case["nt"], case["nbins"])
        want = ctx._hier_result(rec, shape, True, case["way"], case["cascade"])
        call = (rec, shape, case["way"], case["cascade"])
        pending = ctx._track(lambda call=call: ctx._hier_result(call[0], call[1], True, *call[2:]),
                             owner=rec.buffers["idx"],
                             live=lambda call=call: ctx._readback(*call))
        views = [weakref.ref(v) for r in records for v in r.readback[4:] if
                 isinstance(v, np.ndarray)]
        held = (lease, records[-1], views, pending, want)
        lease.suspend()                 # the tenant's run is over (HierarchicalSearch.run)
        del jobs, records, rec, call
        gc.collect()
        gc.disable()
    gc.enable()


def test_a_window_bin_merge_compares_magnitudes_as_numpy_does():
    """Two partial bins of one window bin whose peaks' magnitudes are equal as hypotf rounds
    them and one unit in the last place apart as numpy's absolute value rounds them (two
    peaks of the capture tops at threshold 4.0: hypotf 4.0295701 for both; np.abs 4.0295701
    and 4.0295696): in a job whose peaks are not in template-then-sample order, the assembly
    keeps the peak the Python merge kept (_windows._merge_window_bins, numpy's lexsort over
    -np.abs), the later one here, as main's GPU assembly did; hypotf's tie kept the earlier.
    The same for 2,000 window bins of such pairs."""
    from matchedfilter import _core
    from matchedfilter._results import _SparsePeaks
    from matchedfilter._windows import _merge_window_bins
    larger, smaller = np.complex64(-3.331164 + 2.267329j), np.complex64(-2.0475807 + 3.4705687j)
    assert np.abs(larger) > np.abs(smaller)
    # two blocks (starts 0 and 40, length 64) of two templates (bank indices 3 and 7), one
    # bin each: template 3's peaks at samples 50 (block 0, the larger) and 43 (block 1)
    lags = np.full((2, 2, 1), -1, np.int64)
    vals = np.zeros((2, 2, 1), np.complex64)
    lags[0, 0, 0], vals[0, 0, 0] = 50, larger
    lags[0, 1, 0], vals[0, 1, 0] = 10, np.complex64(5 + 0j)
    lags[1, 0, 0], vals[1, 0, 0] = 3, smaller
    flat = np.flatnonzero(lags.reshape(-1) >= 0)
    part = _SparsePeaks(lags.shape, flat, lags.reshape(-1)[flat], vals.reshape(-1)[flat])
    geometry = (np.array([3, 7], np.int64), np.array([0, 40], np.uintp), None, None, 2, 1, 64,
                None)
    W = np.array([[0, 128]], np.int64)

    def assemble(merged):
        out = _core.assemble_peaks([([(geometry, ((0, part),))],
                                     W[:, 0].copy() if merged else None,
                                     (64,) if merged else ())])
        t, s, v = (np.frombuffer(c, d) for c, d in
                   zip(out[1:4], (np.int64, np.int64, np.complex64)))
        return t, s, v
    t, s, v = assemble(False)
    assert t.tolist() == [3, 7, 3] and s.tolist() == [50, 10, 43]
    want = _merge_window_bins(W, 64, t, s, v)
    assert want[1].tolist() == [50, 10]
    for got, ref in zip(assemble(True), want):
        np.testing.assert_array_equal(got, ref)
    # Many such pairs: per window bin of 64 samples (2,000 of them) a peak of block 0 (start
    # 0) and one of block 1 (start 32), of one magnitude at random phases, so the two
    # magnitudes are equal or a unit in the last place apart; one peak of a second template
    # in block 0 puts the job out of template-then-sample order.
    rng = np.random.default_rng(29)
    nbins = 2000
    lags = np.full((2, 2, nbins), -1, np.int64)
    vals = np.zeros((2, 2, nbins), np.complex64)
    j = np.arange(1, nbins)
    lags[0, 0, j] = 64 * j + rng.integers(32, 64, j.size)
    lags[1, 0, j - 1] = 64 * j - 32 + rng.integers(0, 32, j.size)
    lags[0, 1, 0] = 5
    phase = rng.random((2, 2, nbins)) * 2 * np.pi
    vals[:] = (4.0295699 * np.exp(1j * phase)).astype(np.complex64)
    flat = np.flatnonzero(lags.reshape(-1) >= 0)
    part = _SparsePeaks(lags.shape, flat, lags.reshape(-1)[flat], vals.reshape(-1)[flat])
    geometry = (np.array([3, 7], np.int64), np.array([0, 32], np.uintp), None, None, 2, nbins,
                64 * nbins, None)
    W = np.array([[0, 64 * (nbins + 1)]], np.int64)
    t, s, v = assemble(False)
    want = _merge_window_bins(W, 64, t, s, v)
    assert want[0].size == nbins                      # a peak kept per window bin
    for got, ref in zip(assemble(True), want):
        np.testing.assert_array_equal(got, ref)
    # the pairs numpy orders where hypotf ties (what the comparison above decides)
    a, b = vals[0, 0, j], vals[1, 0, j - 1]
    hyp = [np.hypot(x.real, x.imag) for x in (a, b)]
    assert np.count_nonzero((hyp[0] == hyp[1]) & (np.abs(a) != np.abs(b))) > 0


def test_a_compacted_list_past_the_mirrored_records_is_read_whole():
    """A compacted list of more records than a run copies back (_SPARSE_FIRST, 4,096, on a
    device whose host does not see device memory in place) is read whole for that run: the
    readback cached on the record keeps the copied prefix, the run's readback views the whole
    list, and the call's peaks (read alone, and assembled) equal its peaks counted from the
    device's outputs."""
    from matchedfilter import _core
    from matchedfilter._results import _SparsePeaks
    ctx = Context()
    ctx.props = stated_props(unified_memory=False)
    assert ctx._SPARSE_FIRST == 4096
    case = dict(name="long list", way="compact", cascade=True, direct=False, nt=32, nbins=8,
                batches=[48], ordered=False, ragged=False, merged=False, empty=False, seed=77)
    lags, vals, surv = _case_data(case)[0][0]
    rec = _record(ctx, case, lags, vals, surv)
    flat = np.flatnonzero(lags.reshape(-1) >= 0)
    flat = flat[np.isin(flat // case["nbins"], surv)]
    assert flat.size > 4096
    rb = ctx._readback(rec, lags.shape, "compact", True)
    assert rec.readback[13].size == 4 * 4096 and rb[13].size == 4 * flat.size
    sp = ctx._hier_result(rec, lags.shape, True, "compact", True)
    np.testing.assert_array_equal(sp.flat, flat)
    np.testing.assert_array_equal(sp.idx, lags.reshape(-1)[flat])
    np.testing.assert_array_equal(sp.val, vals.reshape(-1)[flat])
    assert rec.readback[13].size == 4 * 4096
    # assembled from the readback, and from the host peaks, the same
    templates = np.arange(case["nt"], dtype=np.int64)
    starts = np.arange(lags.shape[0], dtype=np.uintp) * 64
    host = _SparsePeaks(lags.shape, flat, lags.reshape(-1)[flat], vals.reshape(-1)[flat])
    got = [_core.assemble_peaks([([((templates, starts, None, None, case["nt"], case["nbins"],
                                     64, w), ((0, part),))], None, ())])
           for part, w in ((ctx._readback(rec, lags.shape, "compact", True),
                            np.zeros(6, np.int64)), (host, None))]
    for a, b in zip(*got):
        assert bytes(a) == bytes(b)


def test_a_gpu_batch_is_one_assembly_with_the_counts_of_its_calls(monkeypatch):
    """On a GPU: a batch of leaf calls (full calls, then replays of their call plans) is
    assembled in one extension call; its peaks equal the same calls made one at a time, and
    the plans' work counters grow by what those calls count in Python (_account). A bank
    dropped after a batch dies without the cyclic collector, with its plans' slot buffers."""
    import gc
    import weakref
    from conftest import usable_gpu, usable_gpu_reason
    from matchedfilter import TimeDomainFilterBank, _core
    from test_time_domain import _whitened_inspiral_bank
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    dev = usable_gpu()
    if dev is None:
        pytest.skip(usable_gpu_reason())
    rng = np.random.default_rng(81)
    banks = []
    for _ in range(3):
        counts = list(rng.integers(200, 400, 29))
        taps, w, df = _whitened_inspiral_bank(rng, counts)
        b = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                 false_dismissal=1e-3, device=dev, fft_lengths=[2048],
                                 binsize=700)
        b.set_reference(w, delta_f=df)
        banks.append(b)
    S = 1 << 17
    rows = banks[0].empty_shared((len(banks), S))
    jobs = [(b, rows[i], dict(windows=[(3000, 50000), (52000, S - 3000)]))
            for i, b in enumerate(banks)]
    calls = []
    assemble = _core.assemble_peaks
    monkeypatch.setattr(_core, "assemble_peaks", lambda j: calls.append(len(j)) or assemble(j))

    def work(banks):
        return [g.plan._gwork.copy() for b in banks for g in b._groups]
    for _ in range(3):
        for r in rows:
            X = np.fft.fft(rng.standard_normal(S))
            X[S // 2:] = 0
            r[:] = (np.fft.ifft(X) * 2).astype(np.complex64)
        del calls[:]
        w0 = work(banks)
        got = [f.result() for f in TimeDomainFilterBank.filter_series_many(jobs, wait=False)]
        assert calls == [len(jobs)]
        w1 = work(banks)
        want = [b.filter_series(x, **kw) for b, x, kw in jobs]
        w2 = work(banks)
        for r1, r2 in zip(want, got):
            for f in r1._fields:
                np.testing.assert_array_equal(getattr(r1, f), getattr(r2, f))
        for before, batched, single in zip(w0, w1, w2):
            np.testing.assert_array_equal(batched - before, single - batched)
    assert sum(getattr(g.plan, "call_plan_replays", 0) for b in banks for g in b._groups) > 0
    held = [weakref.ref(a) for b in banks for g in b._groups
            for pool in g.plan._series_workspace[2:4] for a in pool if a is not None]
    held += [weakref.ref(b) for b in banks]
    gc.collect()
    gc.disable()
    try:
        del banks, jobs, got, want, rows, r, r1, r2, b
        assert [r() is None for r in held] == [True] * len(held)
    finally:
        gc.enable()


def _watch_readbacks(monkeypatch, seen):
    """Record every readback a GPU call's collection makes (HierOps._readback, wrapped: it is
    called as before and returns what it returned): per call the context's arena lease
    generation (None without one), the counts buffer's offset in its base (None where it is
    not a section), weak references to the views cached on the record when they were made by
    this call, the way, the compacted count, and whether the run's list was viewed afresh."""
    import weakref
    from matchedfilter import _gpuhier
    readback = _gpuhier.HierOps._readback

    def watched(self, rec, shape, way, cascade):
        fresh = rec.readback is None
        rb = readback(self, rec, shape, way, cascade)
        lease = getattr(rec.buffers["counts"], "lease", None)
        seen.append(dict(
            lease=None if lease is None else lease.generation,
            offset=getattr(rec.buffers["counts"], "offset", None), way=way,
            views=[weakref.ref(v) for v in rec.readback[4:] if isinstance(v, np.ndarray)]
            if fresh else [],
            listed=int(rb[4][rb[6]]) if way == "compact" else 0,
            reviewed=way == "compact" and rb[13] is not rec.readback[13]))
        return rb
    monkeypatch.setattr(_gpuhier.HierOps, "_readback", watched)


def test_gpu_searches_alternating_on_the_arena_assemble_their_own_peaks(monkeypatch):
    """On a GPU: two searches with different templates take the device's arena in turns
    (every section filled with NaN when handed out). Each run's leaf peaks are assembled from
    readbacks of its own records' buffers, which are arena sections where the device holds
    readback buffers in its arena, at offsets other than 0 where sections share blocks, and
    equal the same search's peaks without an arena. With the collector off from the end of a
    run, every readback view made in that run's lease is gone once the next search has
    begun (its lease's end evicts the records)."""
    import gc
    from conftest import usable_gpu, usable_gpu_reason
    from matchedfilter import _gpuhost, _gpuroot
    from matchedfilter._gpuhost import Arena
    from matchedfilter.search import HierarchicalSearch
    from test_hierarchical_search import _collect, _inputs, _profiles, _tree
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    if usable_gpu() is None:
        pytest.skip(usable_gpu_reason())
    monkeypatch.setattr(Arena, "poison", True)
    opts = dict(engine="hier", binsize=512, device="gpu:0")
    roots = [_tree(np.random.default_rng(51 + i), inner_counts=(301, 351)) for i in range(2)]
    for root in roots:
        root.profile = _profiles()
    inputs = _inputs(np.random.default_rng(61), nblocks=2)

    def run(i):
        return _collect(HierarchicalSearch([roots[i]], threshold=4.0, leaf_options=opts),
                        inputs)

    def same(got, want):
        assert [g[:3] for g in got] == [w[:3] for w in want]
        for g, w in zip(got, want):
            np.testing.assert_array_equal(g[3].template_indices, w[3].template_indices)
            np.testing.assert_array_equal(g[3].sample_indices, w[3].sample_indices)
            np.testing.assert_array_equal(g[3].snr, w[3].snr)
    real_arena = _gpuroot.device_arena
    monkeypatch.setattr(_gpuroot, "device_arena", lambda device: None)
    want = [run(0), run(1)]
    monkeypatch.setattr(_gpuroot, "device_arena", real_arena)
    arena = _gpuroot.device_arena(_gpuhost._parse_device("gpu:0"))
    seen = []
    _watch_readbacks(monkeypatch, seen)
    gc.collect()
    try:
        for turn in range(4):
            first = len(seen)
            got = run(turn % 2)
            if turn:
                # the previous run's lease ended when this one began: its views went with it
                ended = [v for s in seen[:first] for v in s["views"]]
                assert ended and [v() for v in ended] == [None] * len(ended), \
                    "a readback view outlived its lease"
            gc.enable()
            mine = seen[first:]
            assert mine, "no leaf call was read back for the assembly"
            if arena.holds(readback=True):
                assert {s["lease"] for s in mine} == {arena.lease.generation}
                if not arena.block_per_section:
                    assert max(s["offset"] for s in mine) > 0
            same(got, want[turn % 2])
            del got
            gc.collect()
            gc.disable()
    finally:
        gc.enable()


def test_a_gpu_call_compacting_more_records_than_are_mirrored_gives_the_rows_peaks(
        monkeypatch):
    """On a GPU: a leaf call whose sparse peaks are compacted on the device into more records
    than a run copies back where the host does not see device memory (_SPARSE_FIRST, 4,096;
    there the run's list is viewed afresh past the copy, on CUDA) gives the peaks of the
    same call read as survivors' rows. Inputs that do it: 64 templates, threshold 2.5, bins
    of 32 samples at block length 2048, so nearly every (block, template, bin) of noise
    holds a peak (40 x 64 x 53 cells, 26,000 records in one call)."""
    from conftest import usable_gpu, usable_gpu_reason
    from matchedfilter import TimeDomainFilterBank, _settings
    from test_time_domain import _whitened_inspiral_bank
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    dev = usable_gpu()
    if dev is None:
        pytest.skip(usable_gpu_reason())
    rng = np.random.default_rng(91)
    counts = list(rng.integers(200, 400, 64))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=2.5,
                                false_dismissal=1e-3, device=dev, fft_lengths=[2048],
                                binsize=32)
    bank.set_reference(w, delta_f=df)
    S = 1 << 16
    x = bank.empty_shared((S,))
    X = np.fft.fft(rng.standard_normal(S))
    X[S // 2:] = 0
    x[:] = (np.fft.ifft(X) * 2).astype(np.complex64)
    # The plan's first call resolves it, and in a process that has not calibrated this
    # device's GPU cost model yet that times dense calls of its own
    # (_hierarchical._gpu_calibration, calibrate_costs_gpu): made here, before the readbacks
    # are watched, so the calls below are the leaf call alone whatever ran before.
    bank.filter_series(x)
    seen, got = [], {}
    _watch_readbacks(monkeypatch, seen)
    for way in ("rows", "compact"):
        del seen[:]
        with _settings.running({_settings.KERNEL + "sparse:hier": way}):
            got[way] = bank.filter_series(x)
        assert {s["way"] for s in seen} == {way}
    ctx = bank._groups[0].plan._gpu
    assert max(s["listed"] for s in seen) > ctx._SPARSE_FIRST == 4096
    if not ctx.props.unified_memory:
        assert any(s["reviewed"] for s in seen)
    for f in got["rows"]._fields:
        np.testing.assert_array_equal(getattr(got["rows"], f), getattr(got["compact"], f))
