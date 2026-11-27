"""Batches of time-domain filtering calls: how several banks' jobs run as one.

TimeDomainFilterBank.filter_series_many runs its jobs through _run_batch, which hands each
kind of job to the path that takes many at once (follow-up windows, single-template calls,
sparse CPU jobs) and runs the rest in turn. TimeDomainFilterBank.correlate_and_filter_many
runs a hierarchical search's middle correlations and the leaf jobs that read them in
cache-sized cohorts; the functions it is made of are here, in the order it calls them.

time_domain imports this module last and its batch methods call into it; this module reads
time_domain's helpers.
"""
from collections import OrderedDict
from typing import Any
from typing import NamedTuple
from typing import Optional
import ctypes
import math
import numpy as np
import time
import weakref

from . import _core
from . import _settings
from . import _trial
from ._choice import _AUTOTUNE_LOCK, _autotune_enabled, playing
from ._filter import _from_any, MatchedFilter
from ._results import FilterResults, _Deferred, _EMPTY_FILTER_RESULTS, _SparsePeaks
from ._windows import _merge_window_bins, _normalize_windows, _window_bin_phases
from .time_domain import (
    TimeDomainFilterBank, _SAME_PROFILE, _aligned_zeros, _bin_phases, _blocks_by_bin_count,
    _consume_into, _host_copy, _intersect_runs, _interval_runs, _results_from,
    _settle_device_writes, _stored_bins, _trial_key,
)
from . import _gpuhost
from ._gpuexec import fused
from ._series import SeriesLayout
from .device import parse as _parse_device


#: Identifies one filter_series_many batch to the plans it defers.
_BATCH_TOKEN = 0

#: Seconds the process's compiled steps have spent in the extension's runs of them: the
#: gated leaf steps (_cpu_sparse_batch and the tiled cascade's slabs) and the single-template
#: steps (_cpu_single_td_one and _cpu_single_td_batch). A caller reads it as a difference
#: around its calls (HierarchicalSearch.timings).
STEP_COMPUTE_SECONDS = 0.0


def _fuse_close(jobs):
    """Fuse this batch's submissions (_gpuexec.fused) where it has GPU banks: the batch's
    close, or None. Always: pinned at production length, unfused batches were 3-17% slower on
    the 8060S, RENOIR and Iris Xe (2026-10-30; replays of a short run on an idle device had
    timed unfused faster, which the device trial that chose it locked)."""
    if not any(_parse_device(b.device).kind == "gpu" for b, _, _ in jobs
               if hasattr(b, "device")):
        return None
    return fused()


def _layout_slabs(sl, dgroup: int, n_block: int, S: int):
    """Partition SeriesLayout blocks into exact C hmf_slab_len slabs with required input ends."""
    cache = sl.__dict__.setdefault("_slab_cache", {})
    key = (dgroup, n_block, S)
    hit = cache.get(key)
    if hit is not None:
        return hit
    if len(cache) >= 16:
        cache.clear()
    n_blk = sl.starts.size
    if n_blk == 0:
        empty = np.empty(0, dtype=np.int64)
        res = (True, True, empty, empty, empty)
        cache[key] = res
        return res
    low, high = sl.low, sl.high
    cuts = np.flatnonzero((low[1:] != low[:-1]) | (high[1:] != high[:-1])) + 1
    run_edges = np.r_[0, cuts, n_blk]
    slab_r0 = np.concatenate([
        np.arange(int(a), int(b), dgroup, dtype=np.int64)
        for a, b in zip(run_edges[:-1], run_edges[1:])
    ])
    slab_r1 = np.empty_like(slab_r0)
    slab_r1[:-1] = slab_r0[1:]
    slab_r1[-1] = n_blk
    starts_i64 = sl.starts.astype(np.int64, copy=False)
    starts_nondec = bool(n_blk <= 1 or np.all(starts_i64[1:] >= starts_i64[:-1]))
    if starts_nondec:
        slab_min = starts_i64[slab_r0]
        slab_max = starts_i64[slab_r1 - 1]
    else:
        slab_min = np.minimum.reduceat(starts_i64, slab_r0)
        slab_max = np.maximum.reduceat(starts_i64, slab_r0)
    slab_req_end = np.minimum(S, slab_max + n_block)
    req_nondec = bool(slab_req_end.size <= 1 or np.all(slab_req_end[1:] >= slab_req_end[:-1]))
    if req_nondec:
        suffix_min = np.minimum.accumulate(slab_min[::-1])[::-1]
        res = (True, starts_nondec, slab_r1, slab_req_end, suffix_min)
    else:
        perm = np.argsort(slab_req_end, kind="stable")
        slab_min_p = slab_min[perm]
        suffix_min = np.minimum.accumulate(slab_min_p[::-1])[::-1]
        res = (False, False, slab_r0[perm], slab_r1[perm], slab_req_end[perm], suffix_min)
    cache[key] = res
    return res


class _TiledJob(NamedTuple):
    """A middle-stage correlation job the tiled cascade can run (correlate_and_filter_many)."""
    bank: Any                   # the middle bank
    series: np.ndarray          # its input series, float32 or complex64, on the host
    S: int                      # the series' samples
    windows: np.ndarray         # the windows correlated, normalised
    support: Optional[np.ndarray]   # the samples of `out` that are written, or None for all
    out: np.ndarray             # (rows, S) complex64 output the leaf jobs read
    selection: Optional[np.ndarray]     # the templates correlated, or None for every one
    selection_key: Optional[bytes]      # the selection as bytes, to compare jobs by
    scales: Optional[np.ndarray]        # per-template scales, or None
    leaves: list                # indices of the leaf jobs that read `out`


def _trials_decided(leaf_jobs):
    """Adopt the block sizes the leaf banks' joint trials have decided; False while a bank's
    trial is still playing (its calls must run one by one to be timed)."""
    if not leaf_jobs or playing() or not _autotune_enabled():
        return True
    for l_bank, _, l_kw in leaf_jobs:
        if (l_kw or {}).get("template_index") is not None or not getattr(l_bank, "_in_trial", False):
            continue
        t_key = _trial_key(l_bank)
        win = _trial.winner(t_key)
        if win is not None:
            l_bank._lock_arm(win)
            continue
        tr = _trial.trial(t_key, l_bank._joint_arms)
        if len(tr.live()) < 2:
            with _AUTOTUNE_LOCK:
                tr.choice.lock(_trial.DEFAULT)
        if tr.winner is not None:
            l_bank._lock_arm(tr.winner)
            continue
        return False
    return True


def _leaves_by_producer(corr_jobs, leaf_jobs):
    """Which correlation job writes the series each leaf job filters: a leaf's series is a row
    (or a real or imaginary lane) of a correlation job's preallocated ``out``, found by its
    address. Returns (per correlation job the leaf jobs reading its output, the leaf jobs
    reading none)."""
    corr_ranges = []
    leaf_by_corr = [[] for _ in range(len(corr_jobs))]
    for ci, (_, _, c_kw) in enumerate(corr_jobs):
        out_arr = (c_kw or {}).get("out")
        if (isinstance(out_arr, np.ndarray) and out_arr.dtype == np.complex64
                and out_arr.ndim == 2 and out_arr.flags.c_contiguous
                and out_arr.flags.writeable and out_arr.nbytes > 0):
            lo_addr = out_arr.ctypes.data
            corr_ranges.append((ci, lo_addr, lo_addr + out_arr.nbytes))
    independent_leaves = []
    for j, (_, l_ser, _) in enumerate(leaf_jobs):
        matched_ci = None
        if isinstance(l_ser, np.ndarray) and l_ser.nbytes > 0:
            ptr = l_ser.ctypes.data
            for ci, lo_addr, hi_addr in corr_ranges:
                if lo_addr <= ptr < hi_addr:
                    matched_ci = ci
                    break
        if matched_ci is not None:
            leaf_by_corr[matched_ci].append(j)
        else:
            independent_leaves.append(j)
    return leaf_by_corr, independent_leaves


def _tiled_job(corr_bank, corr_series, corr_kw, dep_indices):
    """The correlation job as a _TiledJob, or None where the tiled cascade cannot run it: a
    series that is not one-dimensional, an output that is not a writable (rows, samples)
    complex64 array matching the templates asked for, a plan on a GPU, scales or a selection
    of the wrong shape."""
    a_in = _from_any(corr_series)
    if (isinstance(a_in, np.ndarray) and not np.iscomplexobj(a_in)
            and corr_bank._correlation_reads_real()):
        ser_mid = np.ascontiguousarray(a_in, np.float32)
    else:
        ser_mid = _host_copy(a_in, np.complex64)
    if ser_mid.ndim != 1 or ser_mid.size == 0:
        return None
    S = ser_mid.size
    out_arr = corr_kw["out"]
    if not (isinstance(out_arr, np.ndarray) and out_arr.dtype == np.complex64
            and out_arr.ndim == 2 and out_arr.shape[1] == S
            and out_arr.flags.c_contiguous and out_arr.flags.writeable):
        return None
    W_corr = _normalize_windows(corr_kw.get("windows"), S)
    out_support_arg = corr_kw.get("out_support")
    support = _normalize_windows(out_support_arg, S) if out_support_arg is not None else None
    if any(getattr(g.get_correlation_plan(), "_gpu", None) is not None for g in corr_bank._groups):
        return None
    sc_full = None
    scales_arg = corr_kw.get("scales")
    if scales_arg is not None:
        sc_full = np.ascontiguousarray(_from_any(scales_arg), dtype=np.float32)
        if sc_full.ndim != 1 or sc_full.size != corr_bank.n_templates:
            return None
    sel_arr = None
    templates_sel = corr_kw.get("templates")
    if templates_sel is not None:
        sel_arr = np.asarray(templates_sel, dtype=np.int64).ravel()
        if (sel_arr.size and (sel_arr.min() < 0 or sel_arr.max() >= corr_bank.n_templates)
                or np.unique(sel_arr).size != sel_arr.size
                or out_arr.shape != (sel_arr.size, S)):
            return None
    elif out_arr.shape != (corr_bank.n_templates, S):
        return None
    return _TiledJob(corr_bank, ser_mid, S, W_corr, support, out_arr, sel_arr,
                     None if sel_arr is None else sel_arr.tobytes(), sc_full, dep_indices)


def _cohorts(cand_jobs):
    """The jobs (index, _TiledJob) grouped into cohorts that run together: the same middle
    bank, series length, windows and template selection (the detectors of one search), with
    outputs that do not overlap. In the order of their first job."""
    cohorts = []
    used_cand = [False] * len(cand_jobs)
    for idx_a, (ci_a, info_a) in enumerate(cand_jobs):
        if used_cand[idx_a]:
            continue
        used_cand[idx_a] = True
        key_a = (id(info_a.bank), info_a.S, info_a.windows.tobytes(), info_a.selection_key)
        members = [(ci_a, info_a)]
        out_a = info_a.out
        addr_spans = [(out_a.ctypes.data, out_a.ctypes.data + out_a.nbytes)]
        for idx_b in range(idx_a + 1, len(cand_jobs)):
            if used_cand[idx_b]:
                continue
            ci_b, info_b = cand_jobs[idx_b]
            if (id(info_b.bank), info_b.S, info_b.windows.tobytes(), info_b.selection_key) != key_a:
                continue
            out_b = info_b.out
            lo_b, hi_b = out_b.ctypes.data, out_b.ctypes.data + out_b.nbytes
            if any(lo_b < hi_x and lo_x < hi_b for lo_x, hi_x in addr_spans):
                continue
            used_cand[idx_b] = True
            members.append((ci_b, info_b))
            addr_spans.append((lo_b, hi_b))
        cohorts.append(members)
    return cohorts


#: The keyword arguments a correlation job and a leaf job may carry and still run tiled.
_TILED_CORR_KEYS = frozenset(("windows", "scales", "templates", "out", "out_support", "wait"))
_TILED_LEAF_KEYS = frozenset(("windows", "binsize", "threshold", "template_index", "profile"))


class _LeafSub:
    """One leaf plan's share of a tiled leaf job: a template group of the leaf bank, the
    blocks it filters and the compiled plan that filters them, which is step `step` of the
    cohort's compiled leaf steps (`table`). Compiling the cohort advances `cursor` through
    its slabs; a run adds the peaks found, their count and the seconds spent."""
    __slots__ = ("group", "starts", "slabs", "plan", "ep", "series", "ntemplates", "binsize",
                 "threshold", "parts", "total", "seconds", "slab_info", "cursor", "table",
                 "step")

    def __init__(self, group, starts, slabs, plan, ep, series, ntemplates, binsize, threshold,
                 slab_info, table, step):
        self.group, self.starts, self.slabs, self.plan, self.ep = group, starts, slabs, plan, ep
        self.series, self.ntemplates, self.binsize = series, ntemplates, binsize
        self.threshold, self.slab_info = threshold, slab_info
        self.table, self.step = table, step
        self.parts, self.total, self.seconds, self.cursor = [], 0, 0.0, 0


class _TiledGroup(NamedTuple):
    """One template group of the middle bank, compiled for a cohort: its rows of the output,
    the blocks it correlates and the samples they write, and its chunks. A chunk is
    (has blocks, block starts, block bounds, first sample, end sample, written runs,
    bridges to zero, batch jobs); a batch job is (first row, first template, templates,
    output rows, rows contiguous, filter calls, their leaf subs, earliest sample a later
    chunk's leaf still reads)."""
    group: Any
    n_rows: int
    max_batch: int
    n_batches: int
    rows: Any
    local: Any
    contiguous: bool
    out_rows: Any
    blocks: int
    out_samples: int
    template_values: int
    plan: Any
    ep: Any
    lo: int
    hi: int
    col0: Any
    col1: Any
    written: Any
    unwritten: Any
    edges: Any
    first_col: int
    chunks: list


class _CohortPrep(NamedTuple):
    """What a cohort settles before it runs, kept by the middle bank for the next call with
    the same jobs: the leaf banks and plans it was made for (checked before reuse), every
    leaf sub, the leaf jobs with no window, each other leaf job's assembly record
    (job, windows, bin sizes to merge, subs), the compiled groups and the samples the
    cohort's windows span."""
    bank_refs: list
    plan_checks: list
    subs: list
    empty_leaves: list
    leaf_preps: list
    groups: list
    w_span: int


def _template_batches(corr_bank, sel_arr, n_out_rows):
    """The cohort's output rows by template group of the middle bank, each group's rows cut
    into batches of consecutive templates (up to 8 at n <= 4096, 4 at 8192, else 1) that one
    correlation call fills. Returns the groups as (group, [(local template, output row)],
    batches), each output row's slot within its batch, and the largest batch."""
    grp_rows_map = {}
    if sel_arr is not None:
        for out_row, tmpl_id in enumerate(sel_arr):
            g_m, li = corr_bank._template_map[int(tmpl_id)]
            grp_rows_map.setdefault(id(g_m), (g_m, []))[1].append((int(li), int(out_row)))
        grp_work = []
        for g_m in corr_bank._groups:
            entry = grp_rows_map.get(id(g_m))
            if entry is not None:
                entry[1].sort(key=lambda pair: pair[0])
                grp_work.append(entry)
    else:
        grp_work = []
        for g_m in corr_bank._groups:
            g_indices = g_m.template_indices
            if len(g_indices) > 0:
                grp_work.append((
                    g_m,
                    [(li, int(out_row)) for li, out_row in enumerate(g_indices)],
                ))

    row_slot = [0] * n_out_rows
    pre_grp_batches = []
    max_kr = 1
    for g_m, row_pairs in grp_work:
        nt_sel_g = len(row_pairs)
        max_kr_g = 8 if g_m.n <= 4096 else (4 if g_m.n == 8192 else 1)
        batches = []
        k_cur = 0
        while k_cur < nt_sel_g:
            li0 = row_pairs[k_cur][0]
            k_end = k_cur + 1
            while (
                k_end < nt_sel_g
                and k_end - k_cur < max_kr_g
                and row_pairs[k_end][0] == li0 + (k_end - k_cur)
            ):
                k_end += 1
            kr = k_end - k_cur
            if kr > max_kr:
                max_kr = kr
            b_rows = tuple(row_pairs[k][1] for k in range(k_cur, k_end))
            b_contig_out = all(b_rows[q] == b_rows[0] + q for q in range(kr))
            batches.append((k_cur, li0, kr, b_rows, b_contig_out))
            for q, r_out in enumerate(b_rows):
                row_slot[r_out] = q
            k_cur = k_end
        pre_grp_batches.append((g_m, row_pairs, batches))
    return pre_grp_batches, row_slot, max_kr


def _tile_scratch(corr_bank, D, S, max_kr):
    """The middle bank's scratch for a cohort of D detectors: per detector, max_kr rows of S
    samples that stay in cache, zero where nothing has been written. Returns the pool, the
    detectors' stride in it, each detector's rows and the map of what each row holds."""
    # Stagger detector buffers by 256 samples (2 KiB) so power-of-two/64-aligned spans
    # do not alias onto identical L2/L3 cache sets across detectors.
    det_span = max_kr * S
    pad_s = 256 if (det_span & 63) == 0 else 0
    stride_det = det_span + pad_s
    need_total = D * stride_det
    raw_pool = corr_bank.__dict__.get("_l3_tile_pool")
    prev_layout = corr_bank.__dict__.get("_l3_tile_layout")
    dirty_map = corr_bank.__dict__.setdefault("_l3_tile_dirty_map", {})
    if raw_pool is None or raw_pool.size < need_total:
        raw_pool = _aligned_zeros(need_total, dtype=np.complex64)
        corr_bank.__dict__["_l3_tile_pool"] = raw_pool
        corr_bank.__dict__["_l3_tile_layout"] = (S, stride_det)
        dirty_map.clear()
    elif prev_layout != (S, stride_det):
        raw_pool[:need_total] = 0
        corr_bank.__dict__["_l3_tile_layout"] = (S, stride_det)
        dirty_map.clear()
    tbuf_det = [
        raw_pool[d * stride_det : d * stride_det + det_span].reshape(max_kr, S)
        for d in range(D)
    ]
    return raw_pool, stride_det, tbuf_det, dirty_map


def _cohort_memo_key(corr_bank, members, leaf_jobs, S, max_kr, stride_det, W_corr,
                     eff_tile_bytes, raw_pool):
    """The key a cohort's preparation is kept under, or None where it may not be reused: a
    trial is playing, a job carries scales, or a leaf job is not a plain windowed call on an
    array. The key names the jobs' arrays by address and layout, and the leaf banks."""
    D = len(members)
    memo_ok = (not playing() and not getattr(corr_bank, "_in_trial", False)
               and all(info.scales is None for _, info in members))
    memo_key = None
    if memo_ok:
        leaf_sigs = []
        for d_idx, (_, info) in enumerate(members):
            for j in info.leaves:
                lb, ls, lk = leaf_jobs[j]
                if (getattr(lb, "_in_trial", False)
                        or not isinstance(ls, np.ndarray)
                        or (lk and ((set(lk) - _TILED_LEAF_KEYS)
                                    or lk.get("template_index") is not None))):
                    memo_ok = False
                    break
                w_arg = lk.get("windows") if lk else None
                if w_arg is not None and type(w_arg) is not slice:
                    memo_ok = False
                    break
                w_sig = None if w_arg is None else (w_arg.start, w_arg.stop, w_arg.step)
                leaf_sigs.append((
                    j, d_idx, id(lb), getattr(lb, "_layout_rank", None),
                    ls.ctypes.data, ls.dtype.char, ls.shape, ls.strides,
                    w_sig, lk.get("binsize") if lk else None,
                    lk.get("threshold") if lk else None,
                ))
            if not memo_ok:
                break
        if memo_ok:
            mem_sigs = tuple(
                (info.out.ctypes.data, info.out.shape,
                 None if info.support is None else info.support.tobytes())
                for _, info in members
            )
            memo_key = (
                D, S, max_kr, stride_det, W_corr.tobytes(), members[0][1].selection_key,
                eff_tile_bytes, id(raw_pool), mem_sigs, tuple(leaf_sigs),
            )
    return memo_key


def _prep_still_valid(cached_prep, leaf_jobs):
    """Whether a kept preparation still describes these leaf jobs: the same bank objects,
    each plan still holding the execution plan and the real-series mode it was bound with."""
    valid_cache = all(
        wref() is leaf_jobs[j_ref][0] for wref, j_ref in cached_prep.bank_refs
    )
    if valid_cache:
        for ap, ep, real_m, _ in cached_prep.plan_checks:
            if getattr(ap, "_mf", None) is not ep:
                valid_cache = False
                break
            if ap.__dict__.get("_applied_real", False) is not real_m and hasattr(ap, "_sync_direct_prices"):
                valid_cache = False
                break
            if real_m and ap.__dict__.get("_ep_real") != (ep, True):
                valid_cache = False
                break
    return valid_cache


def _reset_prep(cached_prep):
    """Clear what the last run left in a kept preparation: the plans' data state and each
    leaf sub's peaks, count and seconds."""
    for ap, _, _, _ in cached_prep.plan_checks:
        ap._dataset = False
        if ap._data_ready:
            ap._data_ready.clear()
    for srec in cached_prep.subs:
        srec.parts.clear()
        srec.total = 0
        srec.seconds = 0.0


def _bind_leaves(members, leaf_jobs, S, n_out_rows, row_slot, tbuf_det):
    """Bind every leaf job of the cohort to the scratch row its series will be read from.

    A leaf job's series is a row (or a real or imaginary lane) of a member's output; its
    plans are prepared on the scratch row that holds that output row while its batch runs.
    Returns None where a leaf job cannot run tiled (not a hierarchical bank on such a row, a
    threshold below the bank's, a plan that would have to switch its series mode within the
    cohort). Otherwise (subs by output row and detector, the assembly record of each leaf
    job, the leaf jobs with no window, every sub, the plans to check before reuse, the
    banks to check before reuse, the compiled leaf steps' table or None). The leaf jobs are
    compiled as every gated CPU call is (_compile_leaf_steps); each sub is one step."""
    D = len(members)
    calls, placed, series_of = [], {}, {}
    subs_by_row = [[[] for _ in range(D)] for _ in range(n_out_rows)]
    cohort_leaf_preps = []
    cohort_empty_leaves = []
    all_sub_recs = []
    plan_checks = []
    bank_refs = []
    row_stride_bytes = S * 8

    for d_idx, (ci, info) in enumerate(members):
        _, _, _, _, _, out_arr, _, _, _, dep_indices = info
        out_lo = out_arr.ctypes.data
        out_hi = out_lo + out_arr.nbytes
        for j in dep_indices:
            l_bank, l_ser_raw, l_kw = leaf_jobs[j]
            l_kw = l_kw or {}
            if (l_bank.engine != "hier" or l_kw.get("template_index") is not None
                    or (set(l_kw) - _TILED_LEAF_KEYS)
                    or not isinstance(l_ser_raw, np.ndarray)
                    or l_ser_raw.ndim != 1 or l_ser_raw.size != S
                    or l_ser_raw.strides != (8,)
                    or l_ser_raw.dtype not in (np.complex64, np.float32)
                    or l_ser_raw.ctypes.data + (S - 1) * 8 + l_ser_raw.itemsize > out_hi):
                return None
            off_b = l_ser_raw.ctypes.data - out_lo
            out_row, rem_b = divmod(off_b, row_stride_bytes)
            if out_row < 0 or out_row >= n_out_rows:
                return None
            q_slot = row_slot[out_row]
            t_row_base = tbuf_det[d_idx][q_slot]
            if l_ser_raw.dtype == np.complex64:
                if rem_b != 0:
                    return None
                tbuf_view = t_row_base
            else:
                if rem_b == 0:
                    tbuf_view = t_row_base.real
                elif rem_b == 4:
                    tbuf_view = t_row_base.imag
                else:
                    return None

            thr_arg = l_kw.get("threshold")
            eff_thr = l_bank.threshold if thr_arg is None else float(thr_arg)
            if not np.isfinite(eff_thr) or eff_thr < l_bank.threshold or eff_thr <= 0.0:
                return None
            ser_t = l_bank._input_series(tbuf_view)
            if ser_t.ctypes.data != tbuf_view.ctypes.data or ser_t.size != S:
                return None

            bank_refs.append((weakref.ref(l_bank), j))
            series_of[j] = ser_t
            W_leaf, cache_key = l_bank._call_windows(l_kw.get("windows"), S)
            if W_leaf.shape[0] == 0:
                cohort_empty_leaves.append(j)
                continue
            calls.append((j, l_bank, ser_t, W_leaf, cache_key, l_kw.get("binsize"), eff_thr,
                          l_kw.get("profile", _SAME_PROFILE)))
            placed[j] = (d_idx, out_row)

    # The leaf jobs' steps, compiled as every other gated CPU call's: a plan asked for two
    # series modes within the cohort runs untiled.
    if not calls:
        return (subs_by_row, cohort_leaf_preps, cohort_empty_leaves, all_sub_recs, plan_checks,
                bank_refs, None)
    compiled = _compile_leaf_steps(calls, split_modes=False)
    if compiled is None or len(compiled.calls) != len(calls):
        return None
    subs_of = {j: [] for j, _, _ in compiled.calls}
    for k, (j, g_f, sub_st, sl, active_plan, ep, nt_f, bs, thr_f, real, stride) in enumerate(
            compiled.steps):
        active_plan._dataset = False
        active_plan._data_ready = set()
        plan_checks.append((active_plan, ep, real, stride))
        slab_info = _layout_slabs(sl, int(ep.series_group()), g_f.n, S)
        d_idx, out_row = placed[j]
        sub_rec = _LeafSub(g_f, sub_st, sl, active_plan, ep, series_of[j], nt_f, bs, thr_f,
                           slab_info, compiled.table, k)
        subs_of[j].append(sub_rec)
        all_sub_recs.append(sub_rec)
        subs_by_row[out_row][d_idx].append(sub_rec)
    for (j, _, _), (W_p, merge_bs) in zip(compiled.calls, compiled.merges):
        cohort_leaf_preps.append((j, W_p, merge_bs, subs_of[j]))
    return (subs_by_row, cohort_leaf_preps, cohort_empty_leaves, all_sub_recs, plan_checks,
            bank_refs, compiled.table)


def _chunk_batch_jobs(batches, subs_by_row, D, S, horizon, has_b, more_chunks):
    """One chunk's work per template batch: the filter calls for every leaf slab that ends
    within the chunk's horizon (the first sample a later chunk writes), each with the sub it
    belongs to, and the earliest sample a slab still waiting will read, which is what must
    be carried to the next chunk. Advances each sub's slab cursor."""
    chunk_batch_jobs = []
    for k_r0, li0, kr, b_rows, b_contig_out in batches:
        c_jobs = []
        back_subs = []
        for d_idx in range(D):
            for q, out_row in enumerate(b_rows):
                cid = d_idx * kr + q
                for sub_rec in subs_by_row[out_row][d_idx]:
                    slab_info = sub_rec.slab_info
                    s_cur = sub_rec.cursor
                    if slab_info[0]:
                        _, _, slab_r1, slab_req_end, _ = slab_info
                        if s_cur >= slab_req_end.size:
                            continue
                        s_next = (slab_req_end.size if horizon >= S
                                  else int(np.searchsorted(slab_req_end, horizon, side="right")))
                        if s_next <= s_cur:
                            continue
                        r0 = 0 if s_cur == 0 else int(slab_r1[s_cur - 1])
                        r1 = int(slab_r1[s_next - 1])
                        sub_rec.cursor = s_next
                        c_jobs.append((sub_rec.step, r0, r1, cid, sub_rec.series))
                        back_subs.append((sub_rec, q, r0, r1))
                    else:
                        _, _, sorted_r0, sorted_r1, sorted_req_end, _ = slab_info
                        if s_cur >= sorted_req_end.size:
                            continue
                        s_next = (sorted_req_end.size if horizon >= S
                                  else int(np.searchsorted(sorted_req_end, horizon, side="right")))
                        if s_next <= s_cur:
                            continue
                        sub_rec.cursor = s_next
                        run_r0 = int(sorted_r0[s_cur])
                        run_r1 = int(sorted_r1[s_cur])
                        slices = []
                        for k_s in range(s_cur + 1, s_next):
                            nr0 = int(sorted_r0[k_s])
                            nr1 = int(sorted_r1[k_s])
                            if nr0 == run_r1:
                                run_r1 = nr1
                            else:
                                slices.append((run_r0, run_r1))
                                run_r0, run_r1 = nr0, nr1
                        slices.append((run_r0, run_r1))
                        for r0, r1 in slices:
                            c_jobs.append((sub_rec.step, r0, r1, cid, sub_rec.series))
                            back_subs.append((sub_rec, q, r0, r1))

        min_fut = S
        if has_b and more_chunks and len(batches) > 1:
            for d_idx in range(D):
                for out_row in b_rows:
                    for sub_rec in subs_by_row[out_row][d_idx]:
                        s_cur = sub_rec.cursor
                        suf_min = sub_rec.slab_info[-1]
                        if s_cur < suf_min.size:
                            v_min = int(suf_min[s_cur])
                            if v_min < min_fut:
                                min_fut = v_min
        chunk_batch_jobs.append((
            k_r0, li0, kr, b_rows, b_contig_out, c_jobs, back_subs, min_fut,
        ))
    return chunk_batch_jobs


def _compile_groups(corr_bank, members, pre_grp_batches, subs_by_row, S, W_corr, n_out_rows,
                    eff_tile_bytes):
    """Compile each template group of the middle bank for the cohort: where its blocks
    write, which output margins and gaps must be zero, its time chunks (as many as keep a
    batch's span within eff_tile_bytes) and each chunk's filter calls. Returns the
    _TiledGroup list and the samples the windows span."""
    D = len(members)
    w_span = int((W_corr[:, 1] - W_corr[:, 0]).sum())
    compiled_groups = []
    for g_m, row_pairs, batches in pre_grp_batches:
        nt_sel_g = len(row_pairs)
        max_batch_kr = max((b[2] for b in batches), default=1)
        row_indices_arr = np.array([r_out for _, r_out in row_pairs], dtype=np.int64)
        li_arr = np.array([li for li, _ in row_pairs], dtype=np.int64)
        is_contig_out = (
            nt_sel_g == n_out_rows
            and row_indices_arr[0] == 0
            and np.array_equal(row_indices_arr, np.arange(n_out_rows, dtype=np.int64))
        ) or (
            row_indices_arr[-1] - row_indices_arr[0] + 1 == nt_sel_g
            and np.array_equal(
                row_indices_arr,
                np.arange(row_indices_arr[0], row_indices_arr[0] + nt_sel_g, dtype=np.int64),
            )
        )
        out_slice_obj = (slice(int(row_indices_arr[0]), int(row_indices_arr[0]) + nt_sel_g)
                         if is_contig_out else row_indices_arr)

        st, bounds, keep, _ = corr_bank._windows_layout(g_m, S, W_corr, None)
        M = int(st.size)
        if M > 0:
            w_out_samples = int((keep[:, 1] - keep[:, 0]).sum()) * nt_sel_g
            tmpl_vals = nt_sel_g * _stored_bins(g_m)
            cplan = g_m.get_correlation_plan()
            cplan._require_templates(0, len(g_m.template_indices))
            ep_m = cplan._continuous_plan()
            lo_v, hi_v = cplan.valid
            s64 = st.astype(np.int64)
            if bounds is not None:
                b64 = bounds.astype(np.int64)
                col0 = s64 + b64[:, 0]
                col1 = s64 + b64[:, 1]
            else:
                col0 = s64 + lo_v
                col1 = np.minimum(s64 + hi_v, S)
            written_runs = _interval_runs(S, col0, col1)
        else:
            w_out_samples = tmpl_vals = 0
            cplan = ep_m = None
            lo_v = hi_v = 0
            col0 = col1 = np.empty(0, dtype=np.int64)
            written_runs = np.empty((0, 2), dtype=np.int64)

        unwritten_runs = np.concatenate(([0], written_runs.ravel(), [S])).reshape(-1, 2)
        det_edge_runs = []
        for _, info in members:
            _, _, _, edges_d = corr_bank._windows_layout(g_m, S, W_corr, info.support)
            det_edge_runs.append(edges_d.reshape(-1, 2))

        if W_corr.shape[0] > 1 and M > 0:
            full_edges = np.concatenate(([0], keep.ravel(), [S])).reshape(-1, 2)
            bridged_edges = _intersect_runs(full_edges, written_runs)
        else:
            bridged_edges = np.empty((0, 2), dtype=np.int64)

        if M == 0:
            raw_chunks = [(0, 0, S)]
            grp_min_col = 0
        else:
            grp_min_col = int(col0.min())
            batch_span_bytes = D * int(col1.max() - grp_min_col) * 8 * max_batch_kr
            kt = min(M, max(1, int(math.ceil(batch_span_bytes / eff_tile_bytes))))
            if kt <= 1:
                raw_chunks = [(0, M, S)]
            else:
                raw_chunks = []
                m_prev = 0
                for ck_i in range(1, kt + 1):
                    if ck_i == kt:
                        m_next = M
                    else:
                        m_next = (M * ck_i) // kt
                        if g_m.n <= 4096:
                            m_next = min(M, ((m_next + 15) // 16) * 16)
                    if m_next > m_prev:
                        hz = S if m_next == M else int(col0[m_next:].min())
                        raw_chunks.append((m_prev, m_next, hz))
                        m_prev = m_next

        comp_chunks = []
        for ck_idx, (m0, m1, horizon) in enumerate(raw_chunks):
            has_b = m1 > m0
            if has_b:
                st_c = st[m0:m1]
                bnd_c = bounds[m0:m1] if bounds is not None else None
                c_start = int(col0[m0:m1].min())
                c_end = int(col1[m0:m1].max())
                if m1 - m0 == 1 or W_corr.shape[0] <= 1:
                    t_runs = ((c_start, c_end),)
                else:
                    brk = np.flatnonzero(col0[m0 + 1:m1] > col1[m0:m1 - 1]) + 1
                    r_starts = col0[m0:m1][np.concatenate(([0], brk))]
                    r_stops = col1[m0:m1][np.concatenate((brk - 1, [m1 - m0 - 1]))]
                    t_runs = tuple(
                        (int(ra), int(rb)) for ra, rb in zip(r_starts, r_stops) if rb > ra
                    )
                chunk_bridges = (
                    _intersect_runs(bridged_edges, np.asarray(t_runs, dtype=np.int64))
                    if bridged_edges.size > 0 and t_runs else np.empty((0, 2), dtype=np.int64)
                )
            else:
                st_c = bnd_c = None
                c_start = c_end = 0
                t_runs = ()
                chunk_bridges = np.empty((0, 2), dtype=np.int64)

            chunk_batch_jobs = _chunk_batch_jobs(
                batches, subs_by_row, D, S, horizon, has_b, ck_idx + 1 < len(raw_chunks))
            comp_chunks.append((
                has_b, st_c, bnd_c, c_start, c_end, t_runs, chunk_bridges, chunk_batch_jobs,
            ))

        compiled_groups.append(_TiledGroup(
            g_m, nt_sel_g, max_batch_kr, len(batches), row_indices_arr, li_arr,
            is_contig_out, out_slice_obj, M, w_out_samples, tmpl_vals,
            cplan, ep_m, lo_v, hi_v, col0, col1, written_runs, unwritten_runs,
            det_edge_runs, grp_min_col, comp_chunks,
        ))
    return compiled_groups, w_span


def _clear_stale_scratch(M, col0, col1, max_batch_kr, unwritten_runs, tbuf_det, dirty_map,
                         dt_corr_d):
    """Zero what an earlier group left in the scratch rows where this group's blocks will
    not write, and record what this group will leave. The time is shared between the
    detectors' correlation times."""
    D = len(tbuf_det)
    t_c0 = time.perf_counter()
    new_dirty = (int(col0[0]), int(col1[-1])) if M > 0 else (0, 0)
    for d_idx in range(D):
        t_det = tbuf_det[d_idx]
        for q in range(max_batch_kr):
            d_lo, d_hi = dirty_map.get((d_idx, q), (0, 0))
            if d_hi > d_lo:
                stale = _intersect_runs(
                    unwritten_runs, np.array([[d_lo, d_hi]], dtype=np.int64))
                for sa, sb in stale:
                    if sb > sa:
                        t_det[q, int(sa):int(sb)] = 0
            dirty_map[(d_idx, q)] = new_dirty
    dt_share = (time.perf_counter() - t_c0) / D
    for d_idx in range(D):
        dt_corr_d[d_idx] += dt_share


def _output_margins_and_scales(members, g_m, row_indices_arr, li_arr, is_contig_out,
                               out_slice_obj, det_edge_runs, unwritten_runs, retain_radius,
                               dt_corr_d):
    """Each detector's per-row scales for this group (None without scales). Where the output
    is written (retain_radius is not 0), also zero its margins and apply the scales to the
    samples no block writes, as correlate_series does."""
    D = len(members)
    det_scales = [None] * D
    if retain_radius != 0:
        for d_idx, (_, info) in enumerate(members):
            t_d0 = time.perf_counter()
            _, _, _, _, _, out_d, sel_d, _, sc_d, _ = info
            for ea, eb in det_edge_runs[d_idx]:
                if eb > ea:
                    out_d[out_slice_obj, int(ea):int(eb)] = 0
            if sc_d is not None:
                row_sc = (sc_d[sel_d[row_indices_arr]] if sel_d is not None
                          else sc_d[g_m.template_indices[li_arr]])
                det_scales[d_idx] = row_sc
                for ua, ub in unwritten_runs:
                    if ub > ua:
                        ua_i, ub_i = int(ua), int(ub)
                        if is_contig_out:
                            sub_v = out_d[out_slice_obj, ua_i:ub_i]
                            np.multiply(sub_v, row_sc[:, None], out=sub_v)
                        else:
                            for k_r, r_out in enumerate(row_indices_arr):
                                np.multiply(
                                    out_d[r_out, ua_i:ub_i], row_sc[k_r],
                                    out=out_d[r_out, ua_i:ub_i],
                                )
            dt_corr_d[d_idx] += time.perf_counter() - t_d0
    else:
        for d_idx, (_, info) in enumerate(members):
            _, _, _, _, _, _, sel_d, _, sc_d, _ = info
            if sc_d is not None:
                det_scales[d_idx] = (
                    sc_d[sel_d[row_indices_arr]] if sel_d is not None
                    else sc_d[g_m.template_indices[li_arr]]
                )
    return det_scales


def _copy_runs(out, row, scratch_row, runs, stream_cp):
    """Copy sample runs of a scratch row into row ``row`` of an output array, through the
    streaming store when there is one. Returns whether the streaming store was used."""
    if stream_cp is None:
        for ra, rb in runs:
            out[row, ra:rb] = scratch_row[ra:rb]
        return False
    out_ptr = out[row].ctypes.data
    scratch_ptr = scratch_row.ctypes.data
    used = False
    for ra, rb in runs:
        ra, rb = int(ra), int(rb)
        stream_cp(out_ptr + ra * 8, scratch_ptr + ra * 8, (rb - ra) * 8)
        used = True
    return used


def _restore_collar(saved, tbuf_det, kr, dt_corr_d):
    """Copy back into every detector's scratch rows the samples :func:`_save_collar` kept
    for a batch at the end of the previous chunk. Returns the first sample restored. The time
    is shared between the detectors' correlation times."""
    D = len(tbuf_det)
    t_c0 = time.perf_counter()
    saved_lo, saved_hi, src_pool, src_off = saved
    c_len = saved_hi - saved_lo
    step_elems = kr * c_len
    for d_idx in range(D):
        base_off = src_off + d_idx * step_elems
        tbuf_det[d_idx][:kr, saved_lo:saved_hi] = (
            src_pool[base_off : base_off + step_elems].reshape(kr, c_len)
        )
    dt_share = (time.perf_counter() - t_c0) / D
    for d_idx in range(D):
        dt_corr_d[d_idx] += dt_share
    return saved_lo


def _save_collar(collar_pools, pool_idx, write_off, tbuf_det, kr, collar_lo, c_end, n_batches,
                 dt_corr_d):
    """Keep samples [collar_lo, c_end) of a batch's kr scratch rows, for every detector, in
    pool ``pool_idx`` at ``write_off`` (the pool grows as needed), because leaves of the next
    chunk still read them. Returns the record :func:`_restore_collar` takes. The time is
    shared between the detectors' correlation times."""
    D = len(tbuf_det)
    t_c0 = time.perf_counter()
    c_len = c_end - collar_lo
    step_elems = kr * c_len
    total_elems = D * step_elems
    dst_pool = collar_pools[pool_idx]
    if dst_pool is None or write_off + total_elems > dst_pool.size:
        new_cap = max(
            write_off + total_elems,
            0 if dst_pool is None else dst_pool.size * 2,
            max(1, n_batches) * D * max(c_len, 4096),
        )
        grown = _aligned_zeros(new_cap, dtype=np.complex64)
        if dst_pool is not None and write_off > 0:
            grown[:write_off] = dst_pool[:write_off]
        dst_pool = grown
        collar_pools[pool_idx] = dst_pool
    for d_idx in range(D):
        base_off = write_off + d_idx * step_elems
        dst_pool[base_off : base_off + step_elems].reshape(kr, c_len)[:] = (
            tbuf_det[d_idx][:kr, collar_lo:c_end]
        )
    dt_share = (time.perf_counter() - t_c0) / D
    for d_idx in range(D):
        dt_corr_d[d_idx] += dt_share
    return collar_lo, c_end, dst_pool, write_off


def _filter_ready_slabs(c_jobs, back_subs, kr, retain_radius, eff_ret_thr):
    """Filter a batch's ready leaf slabs, for all detectors, in one C call, and add each
    slab's peaks to its sub. Returns the seconds the call took and, where output is kept
    around peaks (retain_radius > 0), per scratch row the sample positions of the peaks at
    or above eff_ret_thr (None when there are none)."""
    t_f0 = time.perf_counter()
    if not c_jobs:
        return time.perf_counter() - t_f0, None
    peaks_by_q = None
    global STEP_COMPUTE_SECONDS
    c_out = back_subs[0][0].table.run_slices(c_jobs)
    dt_b = time.perf_counter() - t_f0
    STEP_COMPUTE_SECONDS += dt_b
    dt_each = dt_b / len(c_jobs)
    for (fl, ix, vl, tot), (sub_rec, q, r0, r1) in zip(c_out, back_subs):
        sub_rec.total += tot
        sub_rec.seconds += dt_each
        if tot > 0:
            sl = sub_rec.slabs
            nt_f = sub_rec.ntemplates
            fl_arr = np.frombuffer(fl, np.int64)
            ix_arr = np.frombuffer(ix, np.int64)
            vl_arr = np.frombuffer(vl, np.complex64)
            sp = _SparsePeaks((r1 - r0, nt_f, sl.nbins), fl_arr, ix_arr, vl_arr)
            sub_rec.parts.append((r0, sp))
            if retain_radius is not None and retain_radius > 0:
                keep_pk = (
                    np.ones(vl_arr.size, dtype=bool)
                    if eff_ret_thr <= 0.0
                    else (np.abs(vl_arr) >= eff_ret_thr)
                )
                if np.any(keep_pk):
                    bi = fl_arr[keep_pk] // (nt_f * sl.nbins)
                    s_pos = sl.starts[r0 + bi].astype(np.int64) + ix_arr[keep_pk]
                    if peaks_by_q is None:
                        peaks_by_q = [[] for _ in range(kr)]
                    peaks_by_q[q].append(s_pos)
    return dt_b, peaks_by_q


def _retained_spans(q_peaks, pending_fwd_end, k_r, valid_lo, c_start, c_end, S, retain_radius,
                    written_runs):
    """The sample spans of this chunk to write for one output row: retain_radius either side
    of each of its peaks, and what a peak of an earlier chunk still reaches into this one
    (pending_fwd_end[k_r], which this updates for the chunks after), merged and clipped to
    the samples the group's blocks wrote. Returns an (m, 2) int64 array, or None for
    nothing to write."""
    spans = []
    if pending_fwd_end is not None and pending_fwd_end[k_r] > c_start:
        spans.append((c_start, min(c_end, pending_fwd_end[k_r])))
    if q_peaks:
        all_s = q_peaks[0] if len(q_peaks) == 1 else np.concatenate(q_peaks)
        if pending_fwd_end is not None:
            max_fwd = int(all_s.max()) + retain_radius
            if max_fwd > c_end and max_fwd > pending_fwd_end[k_r]:
                pending_fwd_end[k_r] = min(S, max_fwd)
        for s_val in all_s.tolist():
            ca = max(valid_lo, int(s_val) - retain_radius)
            cb = min(c_end, int(s_val) + retain_radius)
            if cb > ca:
                spans.append((ca, cb))
    if not spans:
        return None
    spans.sort()
    merged = [list(spans[0])]
    for sa, sb in spans[1:]:
        if sa <= merged[-1][1]:
            if sb > merged[-1][1]:
                merged[-1][1] = sb
        else:
            merged.append([sa, sb])
    w_spans = _intersect_runs(np.asarray(merged, dtype=np.int64), written_runs)
    return w_spans if w_spans.size > 0 else None


def _run_tiled_group(grp, corr_bank, members, tbuf_det, dirty_map, collar_pools, S,
                     retain_radius, eff_ret_thr, set_mirror, stream_cp, dt_corr_d):
    """Run one compiled group: for each time chunk and template batch, correlate the batch
    for every detector into the scratch rows, write the output as asked (all of it, nothing,
    or collars around retained peaks), filter every leaf slab that is ready, and carry the
    samples a later chunk's leaves still read. Adds each detector's correlation time to
    dt_corr_d; returns the filtering seconds and whether a streaming store was used."""
    (g_m, nt_sel_g, max_batch_kr, n_batches, row_indices_arr, li_arr,
     is_contig_out, out_slice_obj, M, w_out_samples, tmpl_vals,
     cplan, ep_m, lo_v, hi_v, col0, col1, written_runs, unwritten_runs,
     det_edge_runs, grp_min_col, comp_chunks) = grp
    D = len(members)
    dt_fine_cohort = 0.0
    used_nt_stream = False
    if M > 0:
        for _ in range(D):
            corr_bank._add_corr_work(g_m.n, dict(
                blocks=M, pairs=M * nt_sel_g,
                out_samples=w_out_samples, tmpl_values=tmpl_vals,
            ))
        cplan._dataset = False
        if cplan._data_ready:
            cplan._data_ready.clear()

    _clear_stale_scratch(M, col0, col1, max_batch_kr, unwritten_runs, tbuf_det, dirty_map,
                         dt_corr_d)
    det_scales = _output_margins_and_scales(
        members, g_m, row_indices_arr, li_arr, is_contig_out, out_slice_obj, det_edge_runs,
        unwritten_runs, retain_radius, dt_corr_d)

    n_chunks = len(comp_chunks)
    need_collars = n_chunks > 1 and n_batches > 1
    pending_fwd_end = (
        [0] * nt_sel_g
        if (retain_radius is not None and retain_radius > 0 and n_chunks > 1)
        else None
    )
    saved_collars = [None] * n_batches if need_collars else None
    r_pad = retain_radius if (retain_radius is not None and retain_radius > 0) else 0

    # Resolve per-detector C correlation callables once per group.
    if M > 0:
        has_real_corr = hasattr(ep_m, "correlate_series_continuous_real")
        det_run_fns = [
            ep_m.correlate_series_continuous_real
            if info.series.dtype == np.float32 and has_real_corr
            else ep_m.correlate_series_continuous
            for _, info in members
        ]
    else:
        det_run_fns = None

    for ck_idx, (has_blocks, st_c, bnd_c, c_start, c_end, t_runs, chunk_bridges, chunk_batch_jobs) in enumerate(comp_chunks):
        has_bridges = chunk_bridges.size > 0
        write_pool_idx = ck_idx & 1
        write_off = 0

        for b_idx, (k_r0, li0, kr, b_rows, b_contig_out, c_jobs, back_subs, min_fut) in enumerate(chunk_batch_jobs):
            # Restore any cross-chunk boundary collar saved from the previous chunk.
            if saved_collars is not None and saved_collars[b_idx] is not None:
                valid_lo = _restore_collar(saved_collars[b_idx], tbuf_det, kr, dt_corr_d)
                saved_collars[b_idx] = None
            elif n_batches == 1 and ck_idx > 0:
                valid_lo = grp_min_col
            else:
                valid_lo = c_start

            # Correlate batch [li0, li0 + kr) across all detectors in the cohort into L3 tbuf.
            if has_blocks:
                out_row_first = b_rows[0]
                for d_idx, (_, info) in enumerate(members):
                    t_d0 = time.perf_counter()
                    ser_d = info.series
                    out_d = info.out
                    r_sc = det_scales[d_idx]
                    t_det_batch = tbuf_det[d_idx][:kr]
                    direct_mirror = (
                        retain_radius is None
                        and r_sc is None
                        and not has_bridges
                        and b_contig_out
                        and set_mirror is not None
                    )
                    if direct_mirror:
                        set_mirror(out_d[out_row_first].ctypes.data, S)
                        used_nt_stream = True
                    det_run_fns[d_idx](ser_d, st_c, lo_v, hi_v, li0, kr, t_det_batch, bnd_c)
                    if has_bridges:
                        for za, zb in chunk_bridges:
                            t_det_batch[:, int(za):int(zb)] = 0
                    if r_sc is not None:
                        if kr == 1:
                            sc_val = r_sc[k_r0]
                            t_row_1d = t_det_batch[0]
                            for ra, rb in t_runs:
                                np.multiply(t_row_1d[ra:rb], sc_val, out=t_row_1d[ra:rb])
                        else:
                            sc_vec = r_sc[k_r0 : k_r0 + kr, None]
                            for ra, rb in t_runs:
                                np.multiply(t_det_batch[:, ra:rb], sc_vec, out=t_det_batch[:, ra:rb])
                    if retain_radius is None and not direct_mirror:
                        for q, r_out in enumerate(b_rows):
                            if _copy_runs(out_d, r_out, t_det_batch[q], t_runs, stream_cp):
                                used_nt_stream = True
                    dt_corr_d[d_idx] += time.perf_counter() - t_d0

            # Filter all ready slabs of this batch across all detectors in one C call.
            dt_filter, peaks_by_q = _filter_ready_slabs(
                c_jobs, back_subs, kr, retain_radius, eff_ret_thr)
            dt_fine_cohort += dt_filter

            # Write the output around retained peaks when retain_radius > 0.
            if has_blocks and retain_radius is not None and retain_radius > 0:
                for q, r_out in enumerate(b_rows):
                    w_spans = _retained_spans(
                        peaks_by_q[q] if peaks_by_q is not None else None,
                        pending_fwd_end, k_r0 + q, valid_lo, c_start, c_end, S, retain_radius,
                        written_runs)
                    if w_spans is None:
                        continue
                    for d_idx, (_, info) in enumerate(members):
                        t_d0 = time.perf_counter()
                        if _copy_runs(info.out, r_out, tbuf_det[d_idx][q], w_spans, stream_cp):
                            used_nt_stream = True
                        dt_corr_d[d_idx] += time.perf_counter() - t_d0

            # Save cross-chunk boundary collar into persistent ping-pong pool when needed.
            if need_collars and has_blocks and ck_idx + 1 < n_chunks and min_fut < S:
                collar_lo = max(grp_min_col, min_fut - r_pad)
                if collar_lo < c_end:
                    saved_collars[b_idx] = _save_collar(
                        collar_pools, write_pool_idx, write_off, tbuf_det, kr, collar_lo, c_end,
                        n_batches, dt_corr_d)
                    write_off += D * kr * (c_end - collar_lo)
    return dt_fine_cohort, used_nt_stream


def _assemble_leaf_results(cohort_leaf_preps, out_results):
    """Each tiled leaf job's FilterResults from its subs' peaks, into out_results: the
    chunks' peaks joined in block order, bins merged where the job asked for a larger bin
    size. Records each plan's trigger count and time."""
    for j, W_p, merge_bs, job_subs in cohort_leaf_preps:
        lists = ([], [], [], [], [])
        for sub_rec in job_subs:
            g_f, sub_st, sl, active_plan = sub_rec.group, sub_rec.starts, sub_rec.slabs, sub_rec.plan
            nt_f, parts, tot_sum, dt_sum = sub_rec.ntemplates, sub_rec.parts, sub_rec.total, sub_rec.seconds
            active_plan._last_n_triggers = tot_sum
            active_plan._record_batch_time(dt_sum)
            if tot_sum == 0 or not parts:
                continue
            shape = (sl.starts.size, nt_f, sl.nbins)
            if sl.order is None and all(
                parts[i][0] > parts[i - 1][0] for i in range(1, len(parts))
            ):
                if len(parts) == 1 and parts[0][0] == 0:
                    sp = parts[0][1]
                else:
                    per_block = nt_f * sl.nbins
                    sp = _SparsePeaks(
                        shape,
                        np.concatenate([p.flat + b0 * per_block for b0, p in parts]),
                        np.concatenate([p.idx for _, p in parts]),
                        np.concatenate([p.val for _, p in parts]),
                    )
            else:
                sp = _SparsePeaks.combine(parts, shape, sl.order)
            _consume_into(lists, sp, None, sub_st, g_f, None, g_f.n, None)
        if merge_bs and lists[0]:
            cols = [np.concatenate(c) for c in lists]
            for bs_m in merge_bs:
                cols = list(_merge_window_bins(W_p, bs_m, *cols))
            for lst, c in zip(lists, cols):
                lst[:] = [c]
        out_results[j] = _results_from(lists)


def _run_batch(jobs, wait):
    """filter_series_many's batch, once, with the GPU settings in force (_settings)."""
    global _BATCH_TOKEN
    _BATCH_TOKEN += 1
    # The deferred submissions may also be fused where a GPU driver batches them (Vulkan:
    # one command buffer runs every job's forward transforms, then every job's first
    # tier, ..., one barrier per phase; _gpuexec.fused): the device trial's setting.
    close = _fuse_close(jobs)
    out = [None] * len(jobs)
    # Single-template (follow-up) calls on a GPU bank, per template group: one forward
    # dispatch and one submission for all of them instead of a few submissions each.
    done = _items_batch(jobs, out)
    done |= _cpu_single_td_batch(jobs, out, skip=done)
    done |= _cpu_sparse_batch(jobs, out, skip=done)
    try:
        for j, (bank, series, kw) in enumerate(jobs):
            if j in done:
                continue
            bank._defer, bank._queue_offset = _BATCH_TOKEN, j
            try:
                out[j] = bank.filter_series(series, **(kw or {}))
            finally:
                bank._defer, bank._queue_offset = 0, 0
    finally:
        if close is not None:
            close()
    if not wait:
        return [r if isinstance(r, _Deferred) else _Deferred(lambda r=r: r) for r in out]
    return [r.result() if isinstance(r, _Deferred) else r for r in out]


def _items_batch(jobs, out):
    """Run eligible single-template GPU jobs of a batch together; returns their indices."""
    cands = []
    side = device = None
    for j, (bank, series, kw) in enumerate(jobs):
        kw = kw or {}
        ti = kw.get("template_index")
        if (ti is None or bank.engine != 'hier' or _parse_device(bank.device).kind != 'gpu'
                or set(kw) - {"windows", "binsize", "threshold", "template_index"}):
            continue
        ti = int(ti)
        if ti < 0 or ti >= bank.n_templates:
            continue
        ser = series                     # widened only for the items path, below
        if getattr(ser, "ndim", 1) != 1:
            continue
        bank._groups
        g, ti_local = bank._template_map[ti]
        aligned = kw.get("binsize") is not None or bank.binsize is not None
        bs = int(kw["binsize"]) if kw.get("binsize") is not None else (bank.binsize or g.n)
        if bs < 1:
            continue
        thr = bank.threshold if kw.get("threshold") is None else float(kw["threshold"])
        if not np.isfinite(thr):
            continue
        # Where the batch runs: the device trial's side (_settings "single"); a batch's
        # jobs on another device run per call.
        if side is None:
            device = str(bank.device)
            side = _settings.setting("single", device)
        elif str(bank.device) != device:
            continue
        cands.append((j, bank, g, ser, kw, bs, thr, aligned, ti_local, ti))
    if not cands:
        return set()
    done = set()
    if side == "cpu":
        cpu_idx = {c[0] for c in cands}
        done |= _cpu_single_td_batch(
            jobs, out, skip=set(range(len(jobs))) - cpu_idx, force_cpu=True)
        for j in sorted(cpu_idx - done):
            bank = jobs[j][0]
            bank._single_force = "cpu"
            try:
                out[j] = bank.filter_series(jobs[j][1], **(jobs[j][2] or {}))
            finally:
                del bank._single_force
            done.add(j)
        return done
    # Threshold-0 follow-ups: every group's items as listed entries, all in one
    # submission (_gpuhost.submit_followups). None (past what the device path takes):
    # the per-group path below.
    fast = [c[0] for c in cands if c[6] == 0.0]
    if fast:
        collect = _gpuhost.submit_followups([jobs[j] for j in fast])
        if collect is not None:
            # Submitted, not waited on: each job's result is read when asked for, so a
            # caller collecting later (filter_series_many(wait=False)) never waits here.
            for i, j in enumerate(fast):
                out[j] = _Deferred(lambda c=collect, i=i: c()[i])
                done.add(j)
            cands = [c for c in cands if c[0] not in done]
            if not cands:
                return done
    groups = {}
    for j, bank, g, ser, kw, bs, thr, aligned, ti_local, ti in cands:
        S = len(ser)
        W = _normalize_windows(kw.get("windows"), S)
        if W.shape[0] == 0:
            out[j] = _EMPTY_FILTER_RESULTS
            done.add(j)
            continue
        bstarts, bws, bwe = bank._window_layout(g, W, S)
        if bstarts.size == 0:
            out[j] = _EMPTY_FILTER_RESULTS
            done.add(j)
            continue
        # The window's bins (filter_series): each block's phase on its window's grid.
        ph = _window_bin_phases(W, bstarts, bws, bs) if aligned else None
        groups.setdefault((id(bank), id(g), bs, thr, aligned), []).append(
            (j, bank, g, ser, bstarts, bws, bwe, ti_local, ti, W, ph))
    if not groups:
        return done
    fast_ok = sorted(
        m[0] for (_, _, _, thr, _), members in groups.items() if thr == 0.0
        for m in members
        if _gpuhost._followup_job_ok(m[1], m[2], m[3], m[4])
    )
    if fast_ok:
        collect = _gpuhost.submit_followups([jobs[j] for j in fast_ok])
        if collect is not None:
            for i, j in enumerate(fast_ok):
                out[j] = _Deferred(lambda c=collect, i=i: c()[i])
                done.add(j)
            groups = {
                k: [m for m in v if m[0] not in done]
                for k, v in groups.items()
            }
            groups = {k: v for k, v in groups.items() if v}
    # Submit every template group's items, then collect: a backend that can leaves each
    # submission in flight (wait=False), so the device runs them back to back.
    submitted = []
    for (_, _, bs, thr, _), members in groups.items():
        g = members[0][2]
        if bs >= g.n:
            continue
        plan = g.get_flat_plan()
        res = plan._items_gpu([(_host_copy(ser, np.complex64), st, ws, we, tl, ph)
                               for _, _, _, ser, st, ws, we, tl, _, _, ph in members],
                              bs, thr, wait=False) if hasattr(plan, "_items_gpu") else None
        if res is not None:
            submitted.append((bs, members, res))
    for bs, members, res in submitted:
        res = res()
        for (j, bank, g, ser, st, ws, we, tl, ti, W, ph), (idx, val) in zip(members, res):
            lists = ([], [], [], [], [])
            if ph is None:
                # Peaks in the order one call per bin count gives them.
                counts = ((we - ws + bs - 1) // bs).astype(np.int64)
                for u in np.unique(counts):
                    m = counts == u
                    _consume_into(lists, idx[m][:, :, :u], val[m][:, :, :u], st[m], g,
                                  (tl, 1), g.n, ti)
            else:
                # A phased window is one filter_series call: peaks by block, then bin
                # (bins a block does not have are empty).
                _consume_into(lists, idx, val, st, g, (tl, 1), g.n, ti)
            res_j = _results_from(lists)
            if ph is not None:
                # Partial bins (a block edge inside a window bin) into their window bins.
                res_j = FilterResults(*_merge_window_bins(W, bs, *res_j))
            out[j] = res_j
            done.add(j)
    return done


def _single_step(bank, g):
    """Template group g as a single-template step takes it, made once and kept by the group:
    the tuple ``_core.HMFTable`` compiles a single-template step from.

    The group's own arrays (its template indices, taps and counts) are referenced, not copied.
    A template with taps (the bank's taps at the data's rate, as the group keeps them) has its
    spectrum made from them in the extension when a call needs it, into a slot of the group's
    store of template spectra (``_core.SpectrumStore``: up to ``min(T, 256)`` slots, each
    allocated when a template first takes it, the least recently used given up first), which
    every table compiled from the group shares; a template never asked for holds nothing. Any
    other template's spectrum (a resampled bank's, or one whose taps do not fit a block) is
    made here once, with the group's full spectra.

    Parameters
    ----------
    bank : TimeDomainFilterBank
        The bank that owns the group.
    g : _TemplateGroup
        The template group.

    Returns
    -------
    tuple
        ``(n, step, c_bad, template indices, taps, counts, spectra, spectrum rows, store)``:
        the group's block geometry and its templates' indices in the bank's input; its taps
        and their counts (or None); the spectra given (or None) and per template its row in
        them (-1: made from taps); the group's SpectrumStore (or None).
    """
    step = g.__dict__.get("_single_step")
    if step is not None:
        return step
    nt = len(g.template_indices)
    src = (g._row_source.__defaults__[0]
           if getattr(g._row_source, "__defaults__", None) else None)
    taps = counts = spectra = spectrum_rows = store = None
    given = np.arange(nt)
    if (bank.rate_ratio == 1.0 and isinstance(src, dict) and "taps" in src
            and "counts" in src):
        counts = np.ascontiguousarray(src["counts"], dtype=np.int64)
        taps = src["taps"]
        if taps.dtype not in (np.float32, np.complex64) or not taps.flags.c_contiguous:
            taps = np.ascontiguousarray(
                taps, dtype=np.complex64 if np.iscomplexobj(taps) else np.float32)
        # a template whose taps do not fit a block has its spectrum given
        given = np.flatnonzero((counts < 1) | (counts > g.n))
        store = _core.SpectrumStore(min(nt, 256), g.n)
    if given.size:
        spectra = np.array(g.full_spectra(given), dtype=np.complex64, copy=True, order="C")
        spectrum_rows = np.full(nt, -1, dtype=np.int64)
        spectrum_rows[given] = np.arange(given.size)
    step = g._single_step = (g.n, g.n_valid, g.c_bad,
                             np.ascontiguousarray(g.template_indices, dtype=np.int64), taps,
                             counts, spectra, spectrum_rows, store)
    return step


def _single_td_job(bank, series, windows, binsize, threshold, ti, force_cpu):
    """One single-template call as a single-template step binds it: the call's arguments,
    checked and normalised; nothing is compiled.

    Parameters
    ----------
    bank : TimeDomainFilterBank
        The bank.
    series : ndarray
        The series, as the caller passed it.
    windows, binsize, threshold
        As :meth:`TimeDomainFilterBank.filter_series` takes them.
    ti : int
        The template, as indexed in the bank's input.
    force_cpu : bool
        True runs a GPU bank's call too (its call shape's lock chose the CPU side).

    Returns
    -------
    tuple or FilterResults or None
        ``(g, call)``: the template's group and the call's bound arguments ``(series, row,
        windows, binsize, aligned, threshold)``, which ``_core.HMFTable.run`` takes after the
        step's index; the empty result when the window holds no sample; None when a
        single-template step does not run this call.
    """
    if bank.engine not in ("hier", "flat"):
        return None
    if not force_cpu and _parse_device(bank.device).kind != "cpu":
        return None
    ti = int(ti)
    if ti < 0 or ti >= bank.n_templates:
        return None
    thr = float(bank.threshold if threshold is None else threshold)
    if not math.isfinite(thr):
        return None

    bank._groups
    g, row = bank._template_map[ti]
    if bank.engine == "flat":
        p_flat = g._plan
        if p_flat is not None and (
            "run_series" in p_flat.__dict__
            or getattr(type(p_flat).run_series, "__qualname__", "") != "MatchedFilter.run_series"
        ):
            return None
    aligned = binsize is not None or bank.binsize is not None
    bs = int(binsize) if binsize is not None else (bank.binsize or g.n)
    if bs < 1:
        return None

    # A float32 series (contiguous, or one lane of a complex one) and a contiguous complex64
    # one are read in place; anything else as the bank reads it.
    if not (isinstance(series, np.ndarray) and series.ndim == 1
            and ((series.dtype == np.float32 and series.strides in ((4,), (8,)))
                 or (series.dtype == np.complex64 and series.flags.c_contiguous))):
        series = bank._input_series(series)
        if series.ndim != 1:
            return None
        if not (series.flags.c_contiguous
                or (series.dtype == np.float32 and series.strides == (8,))):
            series = np.ascontiguousarray(series)

    S = int(series.size)
    if windows is None:
        if S <= 0:
            return _EMPTY_FILTER_RESULTS
        W = (0, S)
    elif (type(windows) is slice and (windows.step is None or windows.step == 1)
          and (windows.start is None or type(windows.start) is int)
          and (windows.stop is None or type(windows.stop) is int)):
        v0, v1, _ = windows.indices(S)
        if v1 <= v0:
            return _EMPTY_FILTER_RESULTS
        W = (v0, v1)
    else:
        W = _normalize_windows(windows, S)
        if W.shape[0] == 0:
            return _EMPTY_FILTER_RESULTS
    return g, (series, row, W, bs, aligned, thr)


def _cpu_single_td_batch(jobs, out, skip=None, force_cpu=False):
    """Run a batch's single-template CPU calls as the single-template steps of one table, in
    one C call.

    The table has a step per template group the calls filter, compiled once per set of groups
    (a group's own table for one group, else kept by the first call's bank); each call binds
    its template, series, windows, bin size and threshold.

    Parameters
    ----------
    jobs : sequence of tuple
        Sequence of ``(bank, series, kwargs)`` batch items.
    out : list
        Output result list populated at each handled job index.
    skip : set of int, optional
        Job indices already handled earlier in the batch.
    force_cpu : bool, optional
        When True, run GPU-bank jobs whose batch trial selected the CPU side.

    Returns
    -------
    set of int
        Indices of jobs whose ``FilterResults`` were written into ``out``.
    """
    if getattr(MatchedFilter.run_series, "__qualname__", "") != "MatchedFilter.run_series":
        return set()

    done = set()
    skip = skip or set()
    calls, call_jobs, sources, step_of = [], [], [], {}

    # Each call's arguments, bound to its group's step.
    for j, (bank, series, kw) in enumerate(jobs):
        if j in skip:
            continue
        kw = kw or {}
        ti = kw.get("template_index")
        if ti is None or (set(kw) - {"windows", "binsize", "threshold", "template_index", "profile"}):
            continue
        job = _single_td_job(bank, series, kw.get("windows"), kw.get("binsize"),
                             kw.get("threshold"), ti, force_cpu)
        if job is None:
            continue
        if job is _EMPTY_FILTER_RESULTS:
            out[j] = job
            done.add(j)
            continue
        g, call = job
        step = step_of.get(id(g))
        if step is None:
            step = step_of[id(g)] = len(sources)
            sources.append((bank, g))
        calls.append((step,) + call)
        call_jobs.append(j)
    # One call is still a batch: a call at a time takes this path too (filter_series), so a
    # call gives the same peaks alone, among other kinds of call, or with others like it.
    if not calls:
        return done

    # The table: a lone group's own, else one kept by the first bank for this set of groups.
    if len(sources) == 1:
        bank, g = sources[0]
        table = g.__dict__.get("_single_table")
        if table is None:
            table = g._single_table = _core.HMFTable((), (), 0, (_single_step(bank, g),))
    else:
        key = tuple(step_of)
        memo = sources[0][0].__dict__.setdefault("_single_tables", OrderedDict())
        held = memo.get(key)
        if held is not None and all(ref() is g for ref, (_, g) in zip(held[1], sources)):
            memo.move_to_end(key)
            table = held[0]
        else:
            table = _core.HMFTable((), (), 0, tuple(_single_step(b, g) for b, g in sources))
            memo[key] = (table, [weakref.ref(g) for _, g in sources])
            while len(memo) > 8:
                memo.popitem(last=False)

    # Settle any pending device writes once before reading host/shared buffers in C.
    _settle_device_writes()
    offs_b, ti_b, si_b, snr_b, bs_b, bl_b, _, _, kernel = table.run((), calls)
    global STEP_COMPUTE_SECONDS
    STEP_COMPUTE_SECONDS += kernel
    offs = np.frombuffer(offs_b, dtype=np.int64)
    columns = (np.frombuffer(ti_b, dtype=np.int64), np.frombuffer(si_b, dtype=np.int64),
               np.frombuffer(snr_b, dtype=np.complex64), np.frombuffer(bs_b, dtype=np.int64),
               np.frombuffer(bl_b, dtype=np.int64))
    for k, j in enumerate(call_jobs):
        p0, p1 = int(offs[k]), int(offs[k + 1])
        out[j] = (_EMPTY_FILTER_RESULTS if p0 == p1
                  else FilterResults(*(c[p0:p1] for c in columns)))
        done.add(j)
    return done


def _cpu_single_td_one(bank, series, windows, binsize, threshold, ti, force_cpu=False):
    """One single-template call as its group's single-template step, without building a
    batch around it (a search's follow-ups come one call at a time: PeaksContext.refilter):
    what :func:`_cpu_single_td_batch` gives for the one call.

    The group's table is compiled at its first call and kept by the group; a call binds its
    template, series, windows, bin size and threshold and runs it.

    Parameters
    ----------
    bank : TimeDomainFilterBank
        The bank.
    series : ndarray
        The series.
    windows, binsize, threshold
        As :meth:`TimeDomainFilterBank.filter_series` takes them.
    ti : int
        The template, as indexed in the bank's input.
    force_cpu : bool, optional
        True runs a GPU bank's call too (its call shape's lock chose the CPU side). Default
        False.

    Returns
    -------
    FilterResults or None
        The peaks, or None when a single-template step does not run this call.
    """
    if getattr(MatchedFilter.run_series, "__qualname__", "") != "MatchedFilter.run_series":
        return None
    job = _single_td_job(bank, series, windows, binsize, threshold, ti, force_cpu)
    if job is None or job is _EMPTY_FILTER_RESULTS:
        return job
    g, (ser, row, W, bs, aligned, thr) = job
    table = g.__dict__.get("_single_table")
    if table is None:
        table = g._single_table = _core.HMFTable((), (), 0, (_single_step(bank, g),))
    _settle_device_writes()
    _, ti_b, si_b, snr_b, bs_b, bl_b, _, _, kernel = table.run(
        (), ((0, ser, row, W, bs, aligned, thr),))
    global STEP_COMPUTE_SECONDS
    STEP_COMPUTE_SECONDS += kernel
    if not si_b:
        return _EMPTY_FILTER_RESULTS
    return FilterResults(np.frombuffer(ti_b, dtype=np.int64), np.frombuffer(si_b, dtype=np.int64),
                         np.frombuffer(snr_b, dtype=np.complex64),
                         np.frombuffer(bs_b, dtype=np.int64), np.frombuffer(bl_b, dtype=np.int64))


def _plan_is_gated_cpu(plan):
    """Whether a template group's plan runs its series calls through the gated leaf steps: a
    CPU hierarchical plan whose run_series and _series_flags are the library's own."""
    return (getattr(plan, '_gpu', None) is None
            and getattr(plan, '_is_hierarchical', False)
            and 'run_series' not in plan.__dict__ and '_series_flags' not in plan.__dict__
            and getattr(type(plan).run_series, '__qualname__', '') == 'HierarchicalFilter.run_series'
            and getattr(type(plan)._series_flags, '__qualname__', '') == 'MatchedFilter._series_flags'
            and plan._plan_trial() is None)


class _LeafSteps(NamedTuple):
    """The gated leaf steps of a set of bank calls, compiled once (_compile_leaf_steps): the
    extension's table (_core.HMFTable) and what a run checks and updates around it.

    Each step is one template group's blocks of one bin count, on the compiled plan of the
    call's profile; ``steps`` holds per step (call index, group, block starts in output order,
    SeriesLayout, plan, compiled plan, templates, bin size, threshold, real, stride)."""
    table: Any
    calls: list          # per compiled call: (index in the caller's list, bank, profile given)
    merges: list         # per compiled call: its windows and the bin sizes its peaks merge at
    steps: list
    plans: list          # distinct (plan, profile name, compiled plan, resolution) checked on reuse
    banks: list          # (weak reference to a bank, its template groups) checked on reuse


def _compile_leaf_steps(calls, split_modes=True):
    """The gated leaf steps of bank calls, or None where a call cannot run as such.

    The calls are compiled in order, each template group's blocks of one bin count a step,
    exactly as the bank's assembly once laid them out call by call. Compiling configures each
    plan as a call did (its profile, templates, compiled plan, series mode and direct prices),
    and the table keeps that configuration per step, so a run sets a plan's mode again only
    where another call left it otherwise. A plan asked for two series modes starts a new phase
    (the steps before it run as one batch), as the per-call assembly flushed its batch.

    Parameters
    ----------
    calls : sequence of tuple
        ``(index, bank, series, W, cache_key, binsize, threshold, profile)`` per call (those
        the steps do not run are left out of them, and of the result's ``calls``): the
        series as the bank reads it (``_input_series``), the normalised windows and their key
        (``_call_windows``), the bin size argument, the effective threshold, and the profile
        argument.
    split_modes : bool, optional
        False refuses (None) where a plan would be asked for two series modes. Default True.

    Returns
    -------
    _LeafSteps or None
        The compiled steps; None where no call is one the steps run, or a plan cannot read
        the real series it is given.
    """
    steps, step_args, jobs, plans, banks, compiled_calls, merges = [], [], [], {}, {}, [], []
    modes = {}
    phase = 0
    series = []
    for index, bank, ser, W, cache_key, binsize, eff_threshold, profile in calls:
        if profile is not _SAME_PROFILE:
            bank.use_profile(profile)
        plan_profile = bank._plan_profile(bank.__dict__.get("_profile"))
        # A call these steps do not run is left to the caller (filter_series' own path).
        if (bank.engine != 'hier' or _parse_device(bank.device).kind != 'cpu'
                or not np.isfinite(eff_threshold) or eff_threshold < bank.threshold
                or eff_threshold <= 0.0 or (binsize is not None and int(binsize) < 1)):
            continue
        groups = bank._groups
        if not all(g.is_hier and _plan_is_gated_cpu(g.plan) for g in groups):
            continue
        slot = len(series)
        series.append(ser)
        banks[id(bank)] = (weakref.ref(bank), groups)
        S = len(ser)
        real = ser.dtype == np.float32
        stride = 2 if real and ser.strides == (8,) else 1
        aligned = binsize is not None or bank.binsize is not None
        merge_bs = []
        for g in groups:
            N = g.n
            bstarts, bws, bwe = bank._group_blocks(g, W, S, cache_key)
            if bstarts.size == 0:
                continue
            bs = int(binsize) if binsize is not None else (bank.binsize or N)
            bph = None
            if aligned:
                bph = _bin_phases(g, g.plan, W, cache_key, bs, bstarts, bws, bwe)
                if bph is not None and bs not in merge_bs:
                    merge_bs.append(bs)
            for sub_st, sub_ws, sub_we, sub_ph in _blocks_by_bin_count(g.plan, N, bs, bstarts,
                                                                       bws, bwe, bph):
                layout = SeriesLayout(N, np.ascontiguousarray(sub_st, dtype=np.uintp),
                                      np.ascontiguousarray(sub_ws, dtype=np.uintp),
                                      np.ascontiguousarray(sub_we, dtype=np.uintp), bs,
                                      ragged=False, phase=sub_ph)
                layout.group(materialize=False)
                plan = g.plan
                plan.use_profile(plan_profile)
                nt = plan.ntemplates
                plan._require_templates(0, nt)
                # The plan's series mode, as each call once set it: a mode another step of
                # these calls set otherwise ends the phase.
                previous = getattr(plan, '_mf', None)
                if (previous is not None and id(previous) in modes
                        and modes[id(previous)] != (real, stride)):
                    if not split_modes:
                        return None
                    phase += 1
                    modes.clear()
                plan._want_real = real
                ep = plan._execution_plan()
                if id(ep) in modes and modes[id(ep)] != (real, stride):
                    if not split_modes:
                        return None
                    phase += 1
                    modes.clear()
                held = plan.__dict__.get("_ep_real")
                if real or (held is not None and held[0] is ep and held[1]):
                    if not ep.set_real_series(real, stride) and real:
                        return None              # a plan that cannot read a real series
                    plan._ep_real = (ep, real)
                if (plan.__dict__.get("_applied_real") is not real
                        and hasattr(plan, "_sync_direct_prices")):
                    plan._sync_direct_prices(ep, real)
                modes[id(ep)] = (real, stride)
                resolved = plan.__dict__.get("_resolved")
                prices = None
                if getattr(plan, "_taps", None) is not None and resolved is not None \
                        and resolved.direct_hw is not None:
                    st = ep.direct_stats()
                    prices = (st["ticks_per_lag_tap"], st["ticks_per_fft_pair"])
                plans[(id(plan), plan_profile)] = (plan, plan_profile, ep, resolved)
                step_args.append((ep, slot, int(real), stride, layout.starts, layout.low,
                                  layout.high, layout.phase, nt, bs, float(eff_threshold),
                                  prices, phase, slot,
                                  np.ascontiguousarray(g.template_indices, dtype=np.int64),
                                  None if layout.order is None
                                  else np.ascontiguousarray(layout.order, dtype=np.int64),
                                  np.ascontiguousarray(sub_st, dtype=np.int64),
                                  plan._step_stats))
                steps.append((index, g, sub_st, layout, plan, ep, nt, bs, float(eff_threshold),
                              real, stride))
        jobs.append((np.ascontiguousarray(W[:, 0], dtype=np.int64), tuple(merge_bs)))
        compiled_calls.append((index, bank, profile))
        merges.append((W, merge_bs))
    if not compiled_calls:
        return None
    table = _core.HMFTable(step_args, jobs, len(series))
    return _LeafSteps(table, compiled_calls, merges, steps, list(plans.values()),
                      list(banks.values()))


def _leaf_steps_valid(compiled):
    """Whether compiled leaf steps still describe their banks and plans: the same template
    groups, and each plan's compiled plan and resolution of the profile as when compiled."""
    for ref, groups in compiled.banks:
        bank = ref()
        if bank is None or bank.__dict__.get("_built") is not groups:
            return False
    for plan, profile, ep, resolved in compiled.plans:
        d = plan.__dict__
        state = d if d.get("_profile") == profile else d.get("_profiles", {}).get(profile)
        if (state is None or state.get("_mf") is not ep or resolved is None
                or state.get("_resolved") is not resolved
                or state.get("_applied_plan") is not ep or state.get("_applied_res") is not resolved):
            return False
    return True


def _cpu_sparse_batch(jobs, out, skip=None, pre_jobs=None):
    """Run the gated CPU hierarchical calls of a batch as compiled leaf steps, in one C call.

    The calls' steps are compiled once per call shape (_compile_leaf_steps) and kept by the
    first call's bank under a key of every call's bank, layout, profile, series length,
    kind and stride, windows, bin size and threshold. A run binds the series, runs the
    steps (_core.HMFTable.run) and hands each call the slice of the peak arena that is its
    FilterResults.

    Parameters
    ----------
    jobs : sequence of tuple or None
        ``(bank, series, kwargs)`` batch items when ``pre_jobs`` is None.
    out : list
        Output results, written at each handled job's index.
    skip : set of int, optional
        Job indices already handled earlier in the batch.
    pre_jobs : list of tuple, optional
        ``(job_index, bank, ser, W, cache_key, binsize, eff_threshold)`` items normalised by
        ``filter_series``.

    Returns
    -------
    set of int
        Indices of the jobs whose FilterResults were written into ``out``.
    """
    done = set()
    calls = []
    if pre_jobs is not None:
        for j, bank, ser, W, cache_key, binsize, eff_threshold in pre_jobs:
            calls.append((j, bank, ser, W, cache_key, binsize, eff_threshold, _SAME_PROFILE))
    else:
        skip = skip or set()
        for j, (bank, series, kw) in enumerate(jobs):
            if j in skip:
                continue
            kw = kw or {}
            if (bank.engine != 'hier' or kw.get("template_index") is not None
                    or (set(kw) - {"windows", "binsize", "threshold", "template_index", "profile"})):
                continue
            thr_arg = kw.get("threshold")
            eff_threshold = bank.threshold if thr_arg is None else float(thr_arg)
            if not np.isfinite(eff_threshold) or eff_threshold < bank.threshold or eff_threshold <= 0.0:
                continue
            if _parse_device(bank.device).kind != 'cpu':
                continue
            ser = bank._input_series(series)
            if ser.ndim != 1:
                continue
            W, cache_key = bank._call_windows(kw.get("windows"), len(ser))
            if W.shape[0] == 0:
                out[j] = _EMPTY_FILTER_RESULTS
                done.add(j)
                continue
            calls.append((j, bank, ser, W, cache_key, kw.get("binsize"), eff_threshold,
                          kw.get("profile", _SAME_PROFILE)))
    if not calls:
        return done
    if (getattr(MatchedFilter.run_series, '__qualname__', '') != 'MatchedFilter.run_series'):
        return done

    # The compiled steps of this call shape: kept by the first bank, checked before reuse.
    key = tuple((id(bank), bank.__dict__.get("_layout_rank"),
                 bank._plan_profile(bank.__dict__.get("_profile") if profile is _SAME_PROFILE
                                    else profile),
                 cache_key, ser.dtype.char, ser.strides, binsize, float(eff_threshold))
                for _, bank, ser, _, cache_key, binsize, eff_threshold, profile in calls)
    memo = calls[0][1].__dict__.setdefault("_leaf_steps", OrderedDict())
    compiled = memo.get(key)
    if compiled is not None and _leaf_steps_valid(compiled):
        memo.move_to_end(key)
        for _, bank, profile in compiled.calls:
            if profile is not _SAME_PROFILE:
                bank.use_profile(profile)
    else:
        compiled = _compile_leaf_steps(calls)
        if compiled is None:
            return done
        memo[key] = compiled
        while len(memo) > 8:
            memo.popitem(last=False)

    # Device writes to shared host-readable series must have landed.
    _settle_device_writes()
    slot_of = {c[0]: c[2] for c in calls}
    (offs_b, ti_b, si_b, snr_b, bs_b, bl_b, totals_b, seconds_b,
     kernel) = compiled.table.run([slot_of[j] for j, _, _ in compiled.calls])
    for plan, _, _, _ in compiled.plans:
        plan._dataset = False
        if plan._data_ready:
            plan._data_ready = set()
    global STEP_COMPUTE_SECONDS
    STEP_COMPUTE_SECONDS += kernel
    offs = np.frombuffer(offs_b, np.int64)
    columns = (np.frombuffer(ti_b, np.int64), np.frombuffer(si_b, np.int64),
               np.frombuffer(snr_b, np.complex64), np.frombuffer(bs_b, np.int64),
               np.frombuffer(bl_b, np.int64))
    for k, (j, _, _) in enumerate(compiled.calls):
        p0, p1 = int(offs[k]), int(offs[k + 1])
        out[j] = (_EMPTY_FILTER_RESULTS if p0 == p1
                  else FilterResults(*(c[p0:p1] for c in columns)))
        done.add(j)
    return done


def _corr_stream_hooks():
    """Return lazily bound C non-temporal streaming helpers from _core."""
    hooks = TimeDomainFilterBank._STREAM_HOOKS
    if hooks is not None:
        return hooks
    try:
        clib = ctypes.CDLL(_core.__file__)
        set_mirror = clib.ap_mf_set_corr_mirror
        set_mirror.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        set_mirror.restype = None
        stream_cp = clib.ap_mf_stream_copy
        stream_cp.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
        stream_cp.restype = None
        stream_fn = clib.ap_mf_stream_fence
        stream_fn.argtypes = []
        stream_fn.restype = None
        hooks = (set_mirror, stream_cp, stream_fn)
    except AttributeError:
        hooks = (None, None, None)
    TimeDomainFilterBank._STREAM_HOOKS = hooks
    return hooks


def correlate_and_filter_many(corr_jobs, leaf_jobs, wait=True, timings=None,
                              tile_bytes=None, retain_radius=None,
                              retain_threshold=None):
    """TimeDomainFilterBank.correlate_and_filter_many, which documents it."""

    eff_tile_bytes = (TimeDomainFilterBank._TILE_BYTES
                      if tile_bytes is None else int(tile_bytes))
    if retain_radius is not None:
        retain_radius = int(retain_radius)
        if retain_radius < 0:
            raise ValueError("retain_radius must be non-negative")
    eff_ret_thr = 0.0 if retain_threshold is None else float(retain_threshold)

    def _run_untiled():
        corr_times = []
        for c_bank, c_ser, c_kw in corr_jobs:
            t_c0 = time.perf_counter()
            c_bank.correlate_series(c_ser, **(c_kw or {}))
            corr_times.append(time.perf_counter() - t_c0)
        t_f0 = time.perf_counter()
        res = TimeDomainFilterBank.filter_series_many(leaf_jobs, wait=wait) if leaf_jobs else []
        dt_f = time.perf_counter() - t_f0
        if timings is not None:
            timings["correlate_per_job"] = corr_times
            timings["correlate"] = sum(corr_times)
            timings["filter"] = dt_f
            timings["ephemeral_used"] = False
        return res

    if not corr_jobs:
        return _run_untiled()

    # A leaf bank whose block-size trial is still playing runs untiled
    if not _trials_decided(leaf_jobs):
        return _run_untiled()

    if not wait or eff_tile_bytes <= 0:
        return _run_untiled()
    if any(_parse_device(b.device).kind != "cpu" for b, _, _ in corr_jobs):
        return _run_untiled()
    if any(_parse_device(b.device).kind != "cpu" for b, _, _ in leaf_jobs):
        return _run_untiled()

    set_mirror, stream_cp, stream_fn = _corr_stream_hooks()

    leaf_by_corr, independent_leaves = _leaves_by_producer(corr_jobs, leaf_jobs)

    _settle_device_writes()

    out_results = [None] * len(leaf_jobs)
    corr_times = [0.0] * len(corr_jobs)
    dt_filter_total = 0.0
    fallback_leaves = list(independent_leaves)
    all_ephemeral = retain_radius == 0

    def _correlate_untiled(indices):
        """Correlate these jobs with correlate_series and leave their leaves to
        filter_series_many."""
        nonlocal all_ephemeral
        all_ephemeral = False
        for ci in indices:
            c_bank, c_ser, c_kw = corr_jobs[ci]
            t_c0 = time.perf_counter()
            c_bank.correlate_series(c_ser, **(c_kw or {}))
            corr_times[ci] = time.perf_counter() - t_c0
            fallback_leaves.extend(leaf_by_corr[ci])

    # Screen candidate correlation jobs and group compatible multi-detector jobs into cohorts.
    cand_jobs = []
    for ci, (corr_bank, corr_series, corr_kw) in enumerate(corr_jobs):
        corr_kw = corr_kw or {}
        dep_indices = leaf_by_corr[ci]
        can_tile = (
            bool(dep_indices)
            and corr_bank.engine in ("corr", "flat", "hier", "dif")
            and corr_kw.get("wait", True)
            and not (set(corr_kw) - _TILED_CORR_KEYS)
            and corr_kw.get("out") is not None
        )
        info = _tiled_job(corr_bank, corr_series, corr_kw, dep_indices) if can_tile else None
        if info is None:
            _correlate_untiled([ci])
        else:
            cand_jobs.append((ci, info))

    cohorts = _cohorts(cand_jobs)

    # Execute each multi-detector cohort in L3-resident chunks when its active output
    # fits within the automatic L3 residency budget (or when tile_bytes is explicit).
    auto_cohort_cap = max(eff_tile_bytes, 4 << 20) if tile_bytes is None else None
    used_nt_stream = False
    for members in cohorts:
        D = len(members)
        first = members[0][1]
        corr_bank, S, W_corr = first.bank, first.S, first.windows
        n_out_rows = first.out.shape[0]
        w_corr_samples = int((W_corr[:, 1] - W_corr[:, 0]).sum())
        if auto_cohort_cap is not None and D * n_out_rows * w_corr_samples * 8 > auto_cohort_cap:
            _correlate_untiled([ci for ci, _ in members])
            continue

        # Template batches that fill SIMD lanes, and the scratch rows they write.
        pre_grp_batches, row_slot, max_kr = _template_batches(
            corr_bank, first.selection, n_out_rows)
        raw_pool, stride_det, tbuf_det, dirty_map = _tile_scratch(corr_bank, D, S, max_kr)

        # The cohort's preparation: kept from the last call with the same jobs, or made.
        memo_key = _cohort_memo_key(corr_bank, members, leaf_jobs, S, max_kr, stride_det,
                                    W_corr, eff_tile_bytes, raw_pool)
        prep_cache = corr_bank.__dict__.setdefault("_cached_cohort_preps", OrderedDict())
        prep = prep_cache.get(memo_key) if memo_key is not None else None
        if prep is not None and not _prep_still_valid(prep, leaf_jobs):
            prep = None
        if prep is not None:
            prep_cache.move_to_end(memo_key)
            _reset_prep(prep)
        else:
            bound = _bind_leaves(members, leaf_jobs, S, n_out_rows, row_slot, tbuf_det)
            if bound is None:
                _correlate_untiled([ci for ci, _ in members])
                continue
            subs_by_row, leaf_preps, empty_leaves, subs, plan_checks, bank_refs, _ = bound
            groups, w_span = _compile_groups(corr_bank, members, pre_grp_batches,
                                             subs_by_row, S, W_corr, n_out_rows,
                                             eff_tile_bytes)
            prep = _CohortPrep(bank_refs, plan_checks, subs, empty_leaves, leaf_preps,
                               groups, w_span)
            if memo_key is not None:
                prep_cache[memo_key] = prep
                while len(prep_cache) > 4:
                    prep_cache.popitem(last=False)

        for j_empty in prep.empty_leaves:
            out_results[j_empty] = _EMPTY_FILTER_RESULTS

        for ci, _ in members:
            corr_bank._add_corr_in(prep.w_span)

        # Run each middle-bank group across its time chunks and template batches.
        dt_corr_d = [0.0] * D
        dt_fine_cohort = 0.0
        collar_pools = corr_bank.__dict__.setdefault("_l3_collar_pools", [None, None])
        for grp in prep.groups:
            dt_fine, streamed = _run_tiled_group(
                grp, corr_bank, members, tbuf_det, dirty_map, collar_pools, S,
                retain_radius, eff_ret_thr, set_mirror, stream_cp, dt_corr_d)
            dt_fine_cohort += dt_fine
            used_nt_stream = used_nt_stream or streamed

        # Assemble FilterResults for every tiled leaf job in the cohort.
        t_f0 = time.perf_counter()
        _assemble_leaf_results(prep.leaf_preps, out_results)
        dt_fine_cohort += time.perf_counter() - t_f0

        for d_idx, (ci, _) in enumerate(members):
            corr_times[ci] = dt_corr_d[d_idx]
        dt_filter_total += dt_fine_cohort


    if used_nt_stream and stream_fn is not None:
        stream_fn()

    # Execute any independent or fallback leaf jobs in original leaf_jobs order so
    # bank-grouped multi-detector pairs stay adjacent in cache.
    if fallback_leaves:
        fallback_leaves.sort()
        t_f0 = time.perf_counter()
        fb_res = TimeDomainFilterBank.filter_series_many(
            [leaf_jobs[j] for j in fallback_leaves], wait=True)
        dt_filter_total += time.perf_counter() - t_f0
        for j, r in zip(fallback_leaves, fb_res):
            out_results[j] = r

    if timings is not None:
        timings["correlate_per_job"] = corr_times
        timings["correlate"] = sum(corr_times)
        timings["filter"] = dt_filter_total
        timings["ephemeral_used"] = bool(all_ephemeral)
    return out_results
