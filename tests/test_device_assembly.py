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
    """A record holding one batch's readback as the device writes it."""
    from matchedfilter._gpuexec import Record
    nd, nt, nbins = lags.shape
    pairs, out = nd * nt, nd * nt * nbins
    rec = Record()
    B = rec.buffers
    names = ["args0"] + (["args1"] if case["cascade"] else []) + ["count", "fbargs"]
    counts = ctx._x_alloc(16 * len(names), readback=True)
    B["counts"] = counts
    for j, name in enumerate(names):
        B[name] = ctx._x_section(counts, 16 * j, 16)
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
    B["cidx0"] = ctx._x_alloc(pairs * 4)
    B["surv%d" % (1 if case["cascade"] else 0)] = sv = ctx._x_alloc(pairs * 4, readback=True)
    ctx._x_view(sv, np.uint32, surv.size)[:] = surv
    bi = B["idx"] = ctx._x_alloc(out * 4, readback=True)
    bv = B["val"] = ctx._x_alloc(out * 8, readback=True)
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
        lst = B["list"] = ctx._x_alloc(out * 16, readback=True)
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
