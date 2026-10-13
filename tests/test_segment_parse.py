"""SegmentPlan._parse_dispatches (the replay read shared by the CUDA graph and the Vulkan
replay) with one flat index and one sort per dispatch gives exactly what the per-group parse
it replaced gave: same peaks, same order, for sorted or unsorted records, padded group rows,
a caller block order, single-template and bank-wide jobs, and dense dispatches."""
import types

import numpy as np

from matchedfilter import _SparsePeaks
from matchedfilter.time_domain import SegmentPlan, _consume_into, _results_from


def _reference_parse(tr, reader=None):
    """Read every dispatch of a finished segment graph. Sparse results go straight
    into the job's peak lists, without dense tables, in the order filter_series gives:
    (block, template, bin), blocks in the caller's order. A dense dispatch (threshold 0,
    or a fallback) takes the table route for its whole call."""
    pass                                     # _SparsePeaks imported above
    results = []
    for entries, template_index in tr["jobs"]:
        lists = ([], [], [], [], [])
        for d, sub_starts, g, tmpl_arg, N in entries:
            t = d.trace
            nt, nb = t["shape"][1], t["shape"][2]
            order = t["order"]
            rows, tis, bns, idxs, vals = [], [], [], [], []
            dense = None
            for b0, b1, entry in t["groups"]:
                r = entry() if reader is None else reader(entry, t)
                if isinstance(r, _SparsePeaks):
                    if r.flat.size == 0:
                        continue
                    per = r.shape[1] * r.shape[2]
                    keep = r.flat < (b1 - b0) * per          # padded rows dropped
                    bi, rest = np.divmod(r.flat[keep].astype(np.int64), per)
                    ti, bn = np.divmod(rest, r.shape[2])
                    rows.append(bi + b0)                       # layout row
                    tis.append(ti)
                    bns.append(bn)
                    idxs.append(r.idx[keep].astype(np.int64))
                    vals.append(r.val[keep])
                else:
                    gi, gv = r
                    if not (gi >= 0).any():
                        continue
                    if dense is None:
                        dense = (np.full(t["shape"], -1, dtype=np.int64),
                                 np.zeros(t["shape"], dtype=np.complex64))
                    dense[0][b0:b1], dense[1][b0:b1] = gi[:b1 - b0], gv[:b1 - b0]
            if dense is not None:
                idx, val = dense
                if rows:
                    lr, ti, bn = (np.concatenate(x) for x in (rows, tis, bns))
                    idx[lr, ti, bn] = np.concatenate(idxs)
                    val[lr, ti, bn] = np.concatenate(vals)
                if order is not None:
                    ri, rv = np.empty_like(idx), np.empty_like(val)
                    ri[order], rv[order] = idx, val
                    idx, val = ri, rv
                _consume_into(lists, idx, val, sub_starts, g, tmpl_arg, N, template_index)
                continue
            if not rows:
                continue
            row = np.concatenate(rows)
            if order is not None:
                row = order[row]                               # the caller's block
            ti, bn = np.concatenate(tis), np.concatenate(bns)
            srt = np.argsort((row * nt + ti) * nb + bn, kind="stable")
            row, ti = row[srt], ti[srt]
            ii = np.concatenate(idxs)[srt]
            vv = np.concatenate(vals)[srt]
            if tmpl_arg is not None:
                lists[0].append(np.full(row.size, template_index, dtype=np.int64))
            else:
                lists[0].append(g.template_indices[ti])
            lists[1].append(sub_starts[row] + ii)
            lists[2].append(vv)
            lists[3].append(sub_starts[row])
            lists[4].append(np.full(row.size, N, dtype=np.int64))
        results.append(_results_from(lists))
    return results


def _dispatch(rng, nd, nt, nb, ngroups, sort, dense_at=None, odd_shape=False):
    cuts = np.sort(rng.choice(np.arange(1, nd), ngroups - 1, replace=False)) if ngroups > 1 else []
    bounds = [0, *[int(c) for c in cuts], nd]
    groups = []
    for gi, (b0, b1) in enumerate(zip(bounds[:-1], bounds[1:])):
        rows = b1 - b0 + int(rng.integers(0, 3))                     # padded rows
        gnt, gnb = (nt, nb + 1) if (odd_shape and gi == 0) else (nt, nb)
        if dense_at == gi:
            gi_ = np.full((rows, gnt, gnb), -1, np.int64)
            gv_ = np.zeros((rows, gnt, gnb), np.complex64)
            m = rng.random(gi_.shape) < 0.1
            gi_[m] = rng.integers(0, 4096, m.sum())
            gv_[m] = rng.standard_normal(m.sum())
            r = (gi_, gv_)
        else:
            tot = rows * gnt * gnb
            flat = rng.choice(tot, int(rng.integers(0, min(tot, 30) + 1)), replace=False)
            if sort:
                flat = np.sort(flat)
            if odd_shape and gi == 0:
                flat = flat[(flat % gnb) < nb]                         # bins the trace has
            r = _SparsePeaks((rows, gnt, gnb), flat, rng.integers(0, 4096, flat.size),
                             (rng.standard_normal(flat.size)
                              + 1j * rng.standard_normal(flat.size)).astype(np.complex64))
        calls = []

        def entry(sort=True, r=r, calls=calls):
            calls.append(sort)
            return r
        groups.append((b0, b1, entry))
    order = rng.permutation(nd) if rng.random() < 0.5 else None
    return types.SimpleNamespace(trace=dict(shape=(nd, nt, nb), order=order, groups=groups))


def _trace(rng, sort=True, dense=False, odd_shape=False):
    jobs = []
    for _ in range(4):
        entries = []
        single = rng.random() < 0.3                  # a single-template job (template_index)
        for _ in range(int(rng.integers(1, 4))):
            nd, nt, nb = int(rng.integers(3, 12)), int(rng.integers(1, 6)), int(rng.integers(1, 4))
            g = types.SimpleNamespace(template_indices=rng.permutation(100)[:nt])
            d = _dispatch(rng, nd, nt, nb, int(rng.integers(1, min(nd, 4) + 1)), sort,
                          dense_at=0 if dense else None, odd_shape=odd_shape)
            entries.append((d, rng.integers(0, 10 ** 6, nd).astype(np.int64), g,
                            (0, 1) if single else None, 2048))
        jobs.append((entries, 7 if single else None))
    return dict(jobs=jobs)


def _same(a, b):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        for f in x._fields:
            np.testing.assert_array_equal(getattr(x, f), getattr(y, f))


def _sorted_view(tr):
    """The trace's records as the per-group parse saw them: sorted in each group (the CUDA
    collect sorted before this change)."""
    for entries, _ in tr["jobs"]:
        for d, *_ in entries:
            for b0, b1, entry in d.trace["groups"]:
                r = entry()
                if isinstance(r, _SparsePeaks):
                    k = np.argsort(r.flat, kind="stable")
                    r.flat, r.idx, r.val = r.flat[k], r.idx[k], r.val[k]
    return tr


def test_matches_the_per_group_parse():
    rng = np.random.default_rng(11)
    for sort in (True, False):
        for _ in range(30):
            tr = _trace(rng, sort=sort)
            got = SegmentPlan._parse_dispatches(None, tr)
            _same(_reference_parse(_sorted_view(tr)), got)


def test_dense_dispatches_and_group_shapes_unlike_the_trace():
    rng = np.random.default_rng(12)
    for _ in range(20):
        tr = _trace(rng, dense=True)
        _same(_reference_parse(_sorted_view(tr)), SegmentPlan._parse_dispatches(None, tr))
        tr = _trace(rng, odd_shape=True)
        _same(_reference_parse(_sorted_view(tr)), SegmentPlan._parse_dispatches(None, tr))


def test_callable_readers_are_asked_unsorted():
    rng = np.random.default_rng(13)
    tr = _trace(rng, sort=False)
    SegmentPlan._parse_dispatches(None, tr)
    asked = [c for entries, _ in tr["jobs"] for d, *_ in entries
             for _, _, e in d.trace["groups"] for c in e.__defaults__[2]]
    assert asked and not any(asked)
