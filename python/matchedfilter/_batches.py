"""Batches of time-domain filtering calls: how several banks' jobs run as one.

TimeDomainFilterBank.filter_series_many runs its jobs through _run_batch, which hands each
kind of job to the path that takes many at once (follow-up windows, single-template calls,
sparse CPU jobs) and runs the rest in turn. TimeDomainFilterBank.correlate_and_filter_many
runs a hierarchical search's middle correlations and the leaf jobs that read them as one
table, or (with tile_bytes) in time tiles of multi-detector cohorts; the functions it is made of are here, in the order it calls them.

time_domain imports this module last and its batch methods call into it; this module reads
time_domain's helpers.
"""
from collections import OrderedDict
from typing import Any
from typing import NamedTuple
from typing import Optional
import math
import numpy as np
import time
import weakref

from . import _core
from . import _settings
from . import _trial
from ._choice import _AUTOTUNE_LOCK, _autotune_enabled, playing
from ._filter import _from_any, MatchedFilter
from ._results import (FilterResults, _Deferred, _EMPTY_FILTER_RESULTS, _PeaksBatch,
                       _PeaksJob, _assemble_jobs)
from ._windows import _normalize_windows, _window_bin_phases
from .time_domain import (
    TimeDomainFilterBank, _SAME_PROFILE, _aligned_zeros, _bin_phases, _blocks_by_bin_count,
    _host_copy, _intersect_runs, _interval_runs, _settle_device_writes, _stored_bins,
    _trial_key,
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

#: Seconds the process's correlation steps have spent in the extension (their kernels, the
#: clearing and the scaling): correlate_series, correlate_series_channels and the middle
#: correlations of correlate_and_filter_many on the CPU. Read as a difference, as
#: STEP_COMPUTE_SECONDS is (HierarchicalSearch.timings["inner_compute"]).
CORR_COMPUTE_SECONDS = 0.0

#: A plan's set of data rows that hold data, when none do (MatchedFilter._data_ready).
_NO_DATA_READY = frozenset()


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
            batches.append((k_cur, li0, kr, b_rows))
            for q, r_out in enumerate(b_rows):
                row_slot[r_out] = q
            k_cur = k_end
        pre_grp_batches.append((g_m, row_pairs, batches))
    return pre_grp_batches, row_slot, max_kr


class _LeafSub:
    """A leaf step of a tiled cohort while its schedule is compiled: the step, its slabs
    (_layout_slabs) and how many of them the tiles so far have made ready."""
    __slots__ = ("step", "slab_info", "cursor")

    def __init__(self, step, slab_info):
        self.step, self.slab_info, self.cursor = step, slab_info, 0


class _Ops:
    """A schedule being compiled: its ops (_core.c's HMF_OP_*, twelve int64 each) and the
    runs, rows and slices they read."""

    CORR, POOL, STALE, ZERO, SCALE, COPY, COLLAR, LEAF, RETAIN, PENDING, LANE = (
        1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)

    def __init__(self):
        self.ops, self.args = [], []

    def arg(self, values):
        """Append values (int64) to the args; returns their offset."""
        at = len(self.args)
        self.args.extend(int(v) for v in np.asarray(values, np.int64).ravel())
        return at

    def op(self, kind, *fields):
        self.ops.append([kind] + [int(f) for f in fields] + [0] * (11 - len(fields)))

    def arrays(self):
        return (np.asarray(self.ops, np.int64).reshape(-1), np.asarray(self.args, np.int64))


def _tile_scratch(corr_bank, D, S, max_kr):
    """The middle bank's scratch pool for a cohort of D detectors: per detector, max_kr rows
    of S samples that stay in cache, zero where nothing has been written, and its state (the
    layout it was last used with, then each row's span an earlier group wrote, which the
    schedule's OP_POOL and OP_STALE read and update). Returns the pool, its state, each
    detector's rows and the samples of the pool the layout uses."""
    # Stagger detector buffers by 256 samples (2 KiB) so power-of-two/64-aligned spans
    # do not alias onto identical L2/L3 cache sets across detectors.
    det_span = max_kr * S
    pad_s = 256 if (det_span & 63) == 0 else 0
    stride_det = det_span + pad_s
    need_total = D * stride_det
    raw_pool = corr_bank.__dict__.get("_l3_tile_pool")
    if raw_pool is None or raw_pool.size < need_total:
        raw_pool = _aligned_zeros(need_total, dtype=np.complex64)
        corr_bank.__dict__["_l3_tile_pool"] = raw_pool
        # a new pool is zero: its state says so for this layout
        state = np.zeros(2 + 2 * 8 * max(D, 64), np.int64)
        state[:2] = (S, stride_det)
        corr_bank.__dict__["_l3_tile_state"] = state
    state = corr_bank.__dict__["_l3_tile_state"]
    tbuf_det = [
        raw_pool[d * stride_det : d * stride_det + det_span].reshape(max_kr, S)
        for d in range(D)
    ]
    return raw_pool, state, stride_det, tbuf_det, need_total


def _bind_leaves(members, leaf_jobs, S, n_out_rows, row_slot, tbuf_det):
    """Bind every leaf job of the cohort to the scratch row its series will be read from.

    A leaf job's series is a row (or a real or imaginary lane) of a member's output; it is
    filtered on the scratch row that holds that output row while its batch runs. Returns None
    where a leaf job cannot run tiled (not a hierarchical bank on such a row, a threshold
    below the bank's, a plan that would have to switch its series mode within the cohort).
    Otherwise (the leaf calls on the scratch rows, as _compile_steps takes them; leaf job ->
    (detector, output row); the leaf jobs with no window)."""
    calls, placed, empty = [], {}, []
    row_stride_bytes = S * 8
    for d_idx, (ci, info) in enumerate(members):
        out_lo = info.out.ctypes.data
        out_hi = out_lo + info.out.nbytes
        for j in info.leaves:
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
            out_row, rem_b = divmod(l_ser_raw.ctypes.data - out_lo, row_stride_bytes)
            if out_row < 0 or out_row >= n_out_rows:
                return None
            t_row_base = tbuf_det[d_idx][row_slot[out_row]]
            if l_ser_raw.dtype == np.complex64:
                if rem_b != 0:
                    return None
                tbuf_view = t_row_base
            elif rem_b in (0, 4):
                tbuf_view = t_row_base.real if rem_b == 0 else t_row_base.imag
            else:
                return None
            thr_arg = l_kw.get("threshold")
            eff_thr = l_bank.threshold if thr_arg is None else float(thr_arg)
            if not np.isfinite(eff_thr) or eff_thr < l_bank.threshold or eff_thr <= 0.0:
                return None
            ser_t = l_bank._input_series(tbuf_view)
            if ser_t.ctypes.data != tbuf_view.ctypes.data or ser_t.size != S:
                return None
            W_leaf, cache_key = l_bank._call_windows(l_kw.get("windows"), S)
            if W_leaf.shape[0] == 0:
                empty.append(j)
                continue
            calls.append((j, l_bank, ser_t, W_leaf, cache_key, l_kw.get("binsize"), eff_thr,
                          l_kw.get("profile", _SAME_PROFILE)))
            placed[j] = (d_idx, out_row)
    # A plan asked for two series modes within the cohort runs untiled (its slices of one
    # batch would share one mode).
    if calls:
        probe = _compile_steps(calls, split_modes=False)
        if probe is None or len(probe.calls) != len(calls):
            return None
    return calls, placed, empty


def _chunk_batch_jobs(batches, subs_by_row, D, S, horizon, has_b, more_chunks):
    """One chunk's work per template batch: the slices (step, first block, end block,
    cluster, scratch row) of every leaf slab that ends within the chunk's horizon (the first
    sample a later chunk writes), and the earliest sample a slab still waiting will read,
    which is what must be carried to the next chunk. Advances each sub's slab cursor."""
    chunk_batch_jobs = []
    for k_r0, li0, kr, b_rows in batches:
        items = []
        for d_idx in range(D):
            for q, out_row in enumerate(b_rows):
                cluster = d_idx * kr + q
                for sub in subs_by_row[out_row][d_idx]:
                    slab_info = sub.slab_info
                    s_cur = sub.cursor
                    if slab_info[0]:
                        _, _, slab_r1, slab_req_end, _ = slab_info
                        if s_cur >= slab_req_end.size:
                            continue
                        s_next = (slab_req_end.size if horizon >= S
                                  else int(np.searchsorted(slab_req_end, horizon, side="right")))
                        if s_next <= s_cur:
                            continue
                        r0 = 0 if s_cur == 0 else int(slab_r1[s_cur - 1])
                        sub.cursor = s_next
                        items.append((sub.step, r0, int(slab_r1[s_next - 1]), cluster, q))
                    else:
                        _, _, sorted_r0, sorted_r1, sorted_req_end, _ = slab_info
                        if s_cur >= sorted_req_end.size:
                            continue
                        s_next = (sorted_req_end.size if horizon >= S
                                  else int(np.searchsorted(sorted_req_end, horizon, side="right")))
                        if s_next <= s_cur:
                            continue
                        sub.cursor = s_next
                        run_r0, run_r1 = int(sorted_r0[s_cur]), int(sorted_r1[s_cur])
                        for k_s in range(s_cur + 1, s_next):
                            nr0, nr1 = int(sorted_r0[k_s]), int(sorted_r1[k_s])
                            if nr0 == run_r1:
                                run_r1 = nr1
                            else:
                                items.append((sub.step, run_r0, run_r1, cluster, q))
                                run_r0, run_r1 = nr0, nr1
                        items.append((sub.step, run_r0, run_r1, cluster, q))
        min_fut = S
        if has_b and more_chunks and len(batches) > 1:
            for d_idx in range(D):
                for out_row in b_rows:
                    for sub in subs_by_row[out_row][d_idx]:
                        suf_min = sub.slab_info[-1]
                        if sub.cursor < suf_min.size:
                            min_fut = min(min_fut, int(suf_min[sub.cursor]))
        chunk_batch_jobs.append((k_r0, li0, kr, b_rows, items, min_fut))
    return chunk_batch_jobs


def _cohort_schedule(ops, members, pre_grp_batches, subs_by_row, S, W_corr, n_out_rows,
                     eff_tile_bytes, retain_radius, retain_threshold, slots, carry_need):
    """Compile one tiled cohort into the schedule: per template group of the middle bank, the
    stale scratch cleared, the output's margins zeroed and scaled (where it is written), then
    per time chunk (as many as keep a batch's span within eff_tile_bytes) and template batch:
    the carried collar restored, the batch's correlation steps (every detector) into the
    scratch rows, the rows copied to the output (or copied around the batch's peaks with
    retain_radius > 0), the leaf slabs that are ready filtered, and the
    collar a later chunk's leaves read carried.

    ``slots`` is (first series slot of the detectors' series, first output slot of their
    scratch rows, first output slot of their outputs, first correlation step, first scale
    vector, the pool state tile, the pool tile, the first carry tile). carry_need[parity] is
    raised to the samples the carries of that chunk parity hold. Returns the correlation step
    tuples, the correlation plans, and per group the work counters (block length, counts)."""
    D = len(members)
    ser0, scr0, out0, step0, vec0, _, _, carry0 = slots
    corr_bank = members[0][1].bank
    corr_steps, corr_plans, work = [], [], []
    r_pad = retain_radius if (retain_radius is not None and retain_radius > 0) else 0
    for g_m, row_pairs, batches in pre_grp_batches:
        nt_sel_g = len(row_pairs)
        max_batch_kr = max((b[2] for b in batches), default=1)
        row_indices_arr = np.array([r_out for _, r_out in row_pairs], dtype=np.int64)
        li_arr = np.array([li for li, _ in row_pairs], dtype=np.int64)
        st, bounds, keep, _ = corr_bank._windows_layout(g_m, S, W_corr, None)
        M = int(st.size)
        if M > 0:
            cplan = g_m.get_correlation_plan()
            cplan._require_templates(0, len(g_m.template_indices))
            ep_m = cplan._continuous_plan()
            corr_plans.append((cplan, ep_m))
            lo_v, hi_v = cplan.valid
            s64 = st.astype(np.int64)
            if bounds is not None:
                b64 = bounds.astype(np.int64)
                col0, col1 = s64 + b64[:, 0], s64 + b64[:, 1]
            else:
                col0, col1 = s64 + lo_v, np.minimum(s64 + hi_v, S)
            written_runs = _interval_runs(S, col0, col1)
            work.append((g_m.n, dict(blocks=M, pairs=M * nt_sel_g,
                                     out_samples=int((keep[:, 1] - keep[:, 0]).sum()) * nt_sel_g,
                                     tmpl_values=nt_sel_g * _stored_bins(g_m))))
        else:
            col0 = col1 = np.empty(0, dtype=np.int64)
            written_runs = np.empty((0, 2), dtype=np.int64)
        unwritten_runs = np.concatenate(([0], written_runs.ravel(), [S])).reshape(-1, 2)
        if W_corr.shape[0] > 1 and M > 0:
            full_edges = np.concatenate(([0], keep.ravel(), [S])).reshape(-1, 2)
            bridged_edges = _intersect_runs(full_edges, written_runs)
        else:
            bridged_edges = np.empty((0, 2), dtype=np.int64)

        # each row's entry of its detector's scale vector (the bank's per-template scales)
        scale_entries = [None] * D
        for d_idx, (_, info) in enumerate(members):
            if info.scales is not None:
                scale_entries[d_idx] = (info.selection[row_indices_arr]
                                        if info.selection is not None
                                        else g_m.template_indices[li_arr]).astype(np.int64)

        # the stale scratch an earlier group left where this group's blocks will not write
        new_dirty = (int(col0[0]), int(col1[-1])) if M > 0 else (0, 0)
        unwritten_at = ops.arg(unwritten_runs)
        ops.op(_Ops.STALE, slots[5], D, max_batch_kr, unwritten_at, len(unwritten_runs),
               new_dirty[0], new_dirty[1], scr0)
        # the output's margins zeroed and its unwritten samples scaled, where it is written
        rows_at = ops.arg(row_indices_arr)
        if retain_radius != 0:
            for d_idx, (_, info) in enumerate(members):
                _, _, _, edges_d = corr_bank._windows_layout(g_m, S, W_corr, info.support)
                edges_d = edges_d.reshape(-1, 2)
                edges_d = edges_d[edges_d[:, 1] > edges_d[:, 0]]
                ops.op(_Ops.ZERO, out0 + d_idx, rows_at, nt_sel_g, ops.arg(edges_d), len(edges_d))
                if scale_entries[d_idx] is not None:
                    ops.op(_Ops.SCALE, out0 + d_idx, rows_at, nt_sel_g, unwritten_at,
                           len(unwritten_runs), vec0 + d_idx, ops.arg(scale_entries[d_idx]))

        # the group's time chunks
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
        n_chunks, n_batches = len(raw_chunks), len(batches)
        need_collars = n_chunks > 1 and n_batches > 1
        pending = retain_radius is not None and retain_radius > 0 and n_chunks > 1
        if pending:
            ops.op(_Ops.PENDING, nt_sel_g)
        saved = [None] * n_batches
        written_at = ops.arg(written_runs)
        thr_bits = int(np.array([0.0 if retain_threshold is None else retain_threshold],
                                np.float64).view(np.int64)[0])
        for ck_idx, (m0, m1, horizon) in enumerate(raw_chunks):
            has_b = m1 > m0
            if has_b:
                st_c = st[m0:m1]
                bnd_c = bounds[m0:m1] if bounds is not None else None
                c_start, c_end = int(col0[m0:m1].min()), int(col1[m0:m1].max())
                if m1 - m0 == 1 or W_corr.shape[0] <= 1:
                    t_runs = ((c_start, c_end),)
                else:
                    brk = np.flatnonzero(col0[m0 + 1:m1] > col1[m0:m1 - 1]) + 1
                    r_starts = col0[m0:m1][np.concatenate(([0], brk))]
                    r_stops = col1[m0:m1][np.concatenate((brk - 1, [m1 - m0 - 1]))]
                    t_runs = tuple((int(ra), int(rb)) for ra, rb in zip(r_starts, r_stops)
                                   if rb > ra)
                chunk_bridges = (_intersect_runs(bridged_edges, np.asarray(t_runs, dtype=np.int64))
                                 if bridged_edges.size > 0 and t_runs
                                 else np.empty((0, 2), dtype=np.int64))
                bridges = (np.ascontiguousarray(chunk_bridges, np.int64)
                           if chunk_bridges.size else None)
                t_runs_at = ops.arg(np.asarray(t_runs, np.int64).reshape(-1, 2))
            chunk_jobs = _chunk_batch_jobs(batches, subs_by_row, D, S, horizon, has_b,
                                           ck_idx + 1 < n_chunks)
            write_off = 0
            parity = ck_idx & 1
            for b_idx, (k_r0, li0, kr, b_rows, items, min_fut) in enumerate(chunk_jobs):
                # the collar the previous chunk carried for this batch
                if saved[b_idx] is not None:
                    lo_s, hi_s, par_s, off_s = saved[b_idx]
                    for d_idx in range(D):
                        ops.op(_Ops.COLLAR, 1, scr0 + d_idx, carry0 + par_s,
                               off_s + d_idx * kr * (hi_s - lo_s), kr, lo_s, hi_s)
                    valid_lo = lo_s
                    saved[b_idx] = None
                elif n_batches == 1 and ck_idx > 0:
                    valid_lo = grp_min_col
                else:
                    valid_lo = c_start if has_b else 0
                # the batch's correlation steps, every detector, then its rows to the output
                if has_b:
                    first = step0 + len(corr_steps)
                    for d_idx, (_, info) in enumerate(members):
                        scaled = info.scales is not None
                        corr_steps.append((
                            ep_m, ser0 + d_idx, int(info.series.dtype == np.float32),
                            scr0 + d_idx, 0, None, li0, kr, st_c, bnd_c, lo_v, hi_v, bridges,
                            vec0 + d_idx if scaled else -1,
                            scale_entries[d_idx][k_r0:k_r0 + kr] if scaled else None,
                            np.asarray(t_runs, dtype=np.int64).reshape(-1, 2) if scaled else None))
                    ops.op(_Ops.CORR, first, first + D)
                    if retain_radius is None:
                        for d_idx in range(D):
                            for q, r_out in enumerate(b_rows):
                                ops.op(_Ops.COPY, scr0 + d_idx, q, out0 + d_idx, r_out,
                                       t_runs_at, len(t_runs), 1)
                # the leaf slabs this batch made ready, every detector, as one batch
                if items or r_pad:
                    ops.op(_Ops.LEAF, ops.arg(items), len(items), int(r_pad > 0), thr_bits)
                # the output written around the batch's peaks
                if has_b and r_pad:
                    ops.op(_Ops.RETAIN, ops.arg([kr, k_r0, D, scr0, out0, ops.arg(b_rows),
                                                 valid_lo, c_start, c_end, written_at,
                                                 len(written_runs), retain_radius, S,
                                                 int(pending), 1]))
                # the collar a later chunk's leaves still read
                if need_collars and has_b and ck_idx + 1 < n_chunks and min_fut < S:
                    collar_lo = max(grp_min_col, min_fut - r_pad)
                    if collar_lo < c_end:
                        for d_idx in range(D):
                            ops.op(_Ops.COLLAR, 0, scr0 + d_idx, carry0 + parity,
                                   write_off + d_idx * kr * (c_end - collar_lo), kr, collar_lo,
                                   c_end)
                        saved[b_idx] = (collar_lo, c_end, parity, write_off)
                        write_off += D * kr * (c_end - collar_lo)
            carry_need[parity] = max(carry_need[parity], write_off)
    return corr_steps, corr_plans, work


class _Cascade(NamedTuple):
    """correlate_and_filter_many's calls compiled into one table with a schedule
    (_cascade_steps): what a run binds and how its results map to the leaf jobs."""
    steps: Any            # _Steps
    series: list          # the series slots
    outs: list            # the output slots
    scales: Any           # the scale vectors, or None
    tiles: list           # pool states, pools, carries
    before: list          # correlation jobs correlated by their own call before the table
    leftover: list        # leaf jobs the table does not run (filter_series_many after it)
    empty: list           # leaf jobs with no window
    ephemeral: bool       # retain_radius 0 and every correlation tiled: no output written


def _cascade_steps(corr_jobs, leaf_jobs, screened_out, cohorts, eff_tile_bytes,
                   retain_radius, retain_threshold):
    """Compile correlate_and_filter_many's calls, where some cohort runs tiled, into one
    table with a schedule: the untiled correlations first (one OP_CORR), then each tiled
    cohort's schedule (_cohort_schedule), then, after it, the leaf steps of every leaf job not
    tiled, in their phases. Returns a _Cascade, or None where no cohort can be bound tiled
    (every job then runs untiled)."""
    ops = _Ops()
    untiled_cohort_jobs, tiled_parts, tiled_calls, placed_all, empty = [], [], [], {}, []
    for members in cohorts:
        first = members[0][1]
        pre_grp_batches, row_slot, max_kr = _template_batches(
            first.bank, first.selection, first.out.shape[0])
        pool, state, stride_det, tbuf_det, need_total = _tile_scratch(
            first.bank, len(members), first.S, max_kr)
        bound = _bind_leaves(members, leaf_jobs, first.S, first.out.shape[0], row_slot, tbuf_det)
        if bound is None:
            untiled_cohort_jobs.extend(ci for ci, _ in members)
            continue
        calls, placed, cohort_empty = bound
        tiled_calls.extend(calls)
        for j, (d_idx, out_row) in placed.items():
            placed_all[j] = (len(tiled_parts), d_idx, out_row)
        empty.extend(cohort_empty)
        tiled_parts.append((members, pre_grp_batches, pool, state, stride_det, tbuf_det,
                            need_total))
    if not tiled_parts:
        return None
    # the untiled correlations, in the order the jobs were screened: as steps where every one
    # can be, else all by their own calls before the table
    untiled_corr = list(screened_out) + untiled_cohort_jobs
    corr_calls, corr_scales, before = [], [], []
    for ci in untiled_corr:
        bank, series, kw = corr_jobs[ci]
        kw = kw or {}
        if (not (set(kw) <= _CORR_KEYS) or not bank._correlates_on_cpu()
                or (isinstance(series, np.ndarray)
                    and any(np.may_share_memory(series, call[5]) for call in corr_calls))):
            corr_calls, corr_scales, before = [], [], untiled_corr
            break
        call, row_scales = _corr_call(bank, series, kw)
        corr_calls.append(call)
        corr_scales.append(row_scales)
    # the leaf jobs not tiled: every one the leaf steps run, in leaf job order
    leaf_calls, leftover = {c[0]: c for c in tiled_calls}, []
    for j in sorted(set(range(len(leaf_jobs))) - set(placed_all) - set(empty)):
        bank, series, kw = leaf_jobs[j]
        call = _leaf_call(j, bank, series, kw)
        if call is _EMPTY_FILTER_RESULTS:
            empty.append(j)
        elif call is None:
            leftover.append(j)
        else:
            leaf_calls[j] = call

    # slots: series = untiled inputs, the cohorts' detectors' series, the leaf series;
    # outputs = untiled outputs, per cohort its scratch rows then its outputs; scale vectors
    # = untiled, then per cohort its detectors' bank scales; tiles = per cohort its pool's
    # state and the pool, then the two carries
    ncorr = len(corr_calls)
    series = [c[1] for c in corr_calls]
    outs = [c[5] for c in corr_calls]
    scales = [np.empty(0, np.float32) if sc is None else sc for sc in corr_scales]
    tiles, layouts = [], []
    for members, _, pool, state, _, tbuf_det, _ in tiled_parts:
        layouts.append((len(series), len(outs), len(scales), len(tiles)))
        series.extend(info.series for _, info in members)
        outs.extend(tbuf_det)
        outs.extend(info.out for _, info in members)
        scales.extend(np.empty(0, np.float32) if info.scales is None else info.scales
                      for _, info in members)
        tiles.extend((state, pool))
    carry0 = len(tiles)
    carry_need = [0, 0]

    def schedule(steps, n_untiled_steps):
        # the untiled correlations first
        if n_untiled_steps:
            ops.op(_Ops.CORR, 0, n_untiled_steps)
        # each tiled leaf call's steps, as subs of the scratch row its series is read from
        subs_by_row = [[[[] for _ in range(len(part[0]))] for _ in range(part[0][0][1].out.shape[0])]
                       for part in tiled_parts]
        for k, (j, g_f, _, sl, _, ep, _, _, _, _, _) in enumerate(steps):
            if j in placed_all:
                p, d_idx, out_row = placed_all[j]
                S = tiled_parts[p][0][0][1].S
                subs_by_row[p][out_row][d_idx].append(
                    _LeafSub(k, _layout_slabs(sl, int(ep.series_group()), g_f.n, S)))
        more_corrs, plans, banks, work = [], [], [], []
        for p, ((members, pre_grp_batches, _, _, stride_det, _, need_total),
                (ser0, out0, vec0, tile0)) in enumerate(zip(tiled_parts, layouts)):
            D = len(members)
            first = members[0][1]
            ops.op(_Ops.POOL, tile0, first.S, stride_det, tile0 + 1, need_total)
            c_steps, c_plans, c_work = _cohort_schedule(
                ops, members, pre_grp_batches, subs_by_row[p], first.S, first.windows,
                first.out.shape[0], eff_tile_bytes, retain_radius, retain_threshold,
                (ser0, out0, out0 + D, n_untiled_steps + len(more_corrs), vec0, tile0,
                 tile0 + 1, carry0), carry_need)
            more_corrs.extend(c_steps)
            plans.extend(c_plans)
            banks.append((weakref.ref(first.bank), first.bank._groups))
            w_span = int((first.windows[:, 1] - first.windows[:, 0]).sum())
            work.extend((len(banks) - 1, c_work, w_span) for _ in range(D))
        return (more_corrs, len(outs) - ncorr, ops.arrays(), plans, banks, work)

    ordered = [leaf_calls[j] for j in sorted(leaf_calls)]
    compiled = _compile_steps(ordered, corr_calls, tuple(sc is not None for sc in corr_scales),
                              scheduled=frozenset(placed_all), extra_series=len(series) - ncorr,
                              schedule=schedule)
    compiled_jobs = {j for j, _, _ in compiled.calls}
    if not set(placed_all) <= compiled_jobs:
        return None
    leftover = sorted(set(leftover) | (set(leaf_calls) - compiled_jobs))
    series.extend(leaf_calls[j][2] for j, _, _ in compiled.calls)
    tiles.extend(_aligned_zeros(max(1, n), np.complex64) for n in carry_need)
    return _Cascade(compiled, series, outs, scales if corr_scales or any(
        info.scales is not None for part in tiled_parts for _, info in part[0]) else None,
        tiles, before, leftover, empty, retain_radius == 0 and not untiled_corr)


def _run_batch(jobs, wait, corr=None):
    """filter_series_many's batch, once, with the GPU settings in force (_settings). corr:
    correlation calls on CPU banks that the batch's CPU every-template calls follow in one
    table (_cpu_sparse_batch's ``corr``), run before any of the batch's calls; default none."""
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
    done |= _cpu_sparse_batch(jobs, out, skip=done, corr=corr)
    done |= _cpu_single_td_batch(jobs, out, skip=done)
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
    # The jobs whose peaks the extension assembles when asked: all in one call, by whichever
    # is asked first (_results._PeaksBatch).
    assembled = [r for r in out if isinstance(r, _PeaksJob)]
    if len(assembled) > 1:
        _PeaksBatch(assembled)
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
    # Every member's peaks assembled in one extension call (_core.assemble_peaks): a member
    # without bin phases as one call per bin count gives them (each count's blocks in turn,
    # in increasing count); a phased window as one filter_series call, peaks by block then
    # bin, its partial bins merged into their window bins.
    assembled = []
    for bs, members, res in submitted:
        res = res()
        for (j, bank, g, ser, st, ws, we, tl, ti, W, ph), (idx, val) in zip(members, res):
            counts = ((we - ws + bs - 1) // bs).astype(np.int64) if ph is None else None
            job = _PeaksJob([(np.array([ti], np.int64), st, counts, g.n,
                              (np.ascontiguousarray(idx), np.ascontiguousarray(val)))],
                            None if ph is None else np.ascontiguousarray(W[:, 0], np.int64),
                            () if ph is None else (bs,))
            assembled.append((j, job))
            done.add(j)
    if assembled:
        _assemble_jobs([job for _, job in assembled])
        for j, job in assembled:
            out[j] = job._value
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
    offs_b, ti_b, si_b, snr_b, bs_b, bl_b, _, _, kernel, _ = table.run((), calls)
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
    _, ti_b, si_b, snr_b, bs_b, bl_b, _, _, kernel, _ = table.run(
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


class _Steps(NamedTuple):
    """Correlation calls and leaf calls compiled into the steps of one table (_compile_steps):
    the extension's table (_core.HMFTable) and what a run checks and updates around it.

    The table's series slots are the correlation calls' inputs, one per call, then the leaf
    calls' series; its output slots are the correlation calls' outputs. A run executes every
    correlation step, then the leaf steps, which may read what the correlation steps wrote.

    A gated step is one template group's blocks of one bin count, on the compiled plan of the
    call's profile; ``steps`` holds per gated step (call index, group, block starts in output
    order, SeriesLayout, plan, compiled plan, templates, bin size, threshold, real, stride). A
    flat step is the same on the group's ungated plan (a flat bank's plan, or a hierarchical
    group's flat plan for a call below the bank's threshold). A correlation step is a run of a
    correlation bank's template group into rows of its call's output.

    The banks are held by weak reference: the first call's bank keeps its compiled steps, so
    a strong reference to it from them would make a cycle, and a leaf bank would then live
    until the cyclic collector ran (in a PyCBC job, 130 to 280 MB of dead banks a top)."""
    table: Any
    ncorr: int           # correlation calls: the table's first series slots and its outputs
    calls: list          # per compiled leaf call: (index in the caller's list, weak reference
    #                      to its bank, profile given)
    merges: list         # per compiled leaf call: its windows and the bin sizes its peaks merge at
    steps: list
    plans: list          # distinct (plan, profile name, compiled plan, resolution) checked on reuse
    banks: list          # (weak reference to a bank, its template groups) checked on reuse: the
    #                      leaf banks and the correlation banks
    flat_plans: list     # distinct (ungated plan, its compiled plan) of the flat steps
    corr_plans: list     # distinct (correlation plan, its compiled plan), checked on reuse
    corr_work: list      # per distinct correlation bank: (its index in banks, [(block length,
    #                      work counters)], input samples the windows read), added per run


def _compile_steps(calls, corr_calls=(), scaled=(), split_modes=True, scheduled=frozenset(),
                   extra_series=0, schedule=None, lanes=()):
    """The steps of correlation calls and leaf calls, compiled into one table.

    Correlation call c reads series slot c and writes output slot c. Its output rows are its
    bank's templates in order, or the templates ``rows`` lists. A correlation step is one
    block-size group's templates adjacent both in the group and in the output, over the
    group's blocks that a window reaches, written into those rows; then the samples outside
    what the windows hold (and, with a support, inside it) are cleared on them, and with
    scales (``scaled[c]``) each row is scaled by entry ``row`` of scale vector c. Every
    template of a bank whose group's templates are not one run of the output is one step
    written through a scratch of the group's rows, cleared over every sample the windows do
    not hold, then copied to its rows. These are the calls, clearing and scaling
    correlate_series made group by group.

    The leaf calls are compiled in order after them, each template group's blocks of one bin
    count a step, exactly as the bank's assembly once laid them out call by call. A call at or
    above a hierarchical bank's threshold has gated steps; a call of a flat bank, or below a
    hierarchical bank's threshold, has flat steps, on each group's ungated plan (a CPU
    MatchedFilter of one data row; a call whose plans are not that is left out). Compiling
    configures each gated plan as a call did (its profile, templates, compiled plan, series
    mode and direct prices), and the table keeps that configuration per step, so a run sets a
    plan's mode again only where another call left it otherwise. A plan asked for two series
    modes starts a new phase (the steps before it run as one batch), as the per-call assembly
    flushed its batch. A flat step reads a real series widened to complex in the extension,
    over the samples its blocks read, as the call did in Python.

    Parameters
    ----------
    calls : sequence of tuple
        Leaf calls, ``(index, bank, series, W, cache_key, binsize, threshold, profile)`` per
        call (those the steps do not run are left out of them, and of the result's
        ``calls``): the series as the bank reads it (``_input_series``), the normalised
        windows and their key (``_call_windows``), the bin size argument, the effective
        threshold, and the profile argument.
    corr_calls : sequence of tuple, optional
        Correlation calls on CPU banks, ``(bank, series, windows, support, rows)``, or with
        the call's output after them (which compiling does not read): the series
        1-D float32 (read at half-size transforms) or complex64, ``windows`` and ``support``
        normalised (``(K, 2)`` int64; ``support`` None where the output may hold anything),
        ``rows`` None or an int64 array of distinct template indices. Default none.
    scaled : sequence of bool, optional
        Per correlation call, whether the run gives it a scale vector.
    split_modes : bool, optional
        False refuses (None) where a plan would be asked for two series modes. Default True.
    scheduled : set of int, optional
        Leaf call indices whose steps a schedule runs (in block ranges, OP_LEAF): their steps
        are phase -1 and take no part in the phases of the others. Default none.
    extra_series : int, optional
        Series slots after the correlation calls' inputs and before the leaf calls' series,
        which the schedule's correlation steps read. Default 0.
    schedule : callable, optional
        ``schedule(steps, n)`` with the compiled leaf steps (``_Steps.steps``) and the
        number of the calls' correlation steps returns the schedule's (correlation step tuples after the calls', output slots after the calls',
        (ops, args) int64 arrays, correlation plans, banks, work); default None, no schedule.
    lanes : sequence of tuple, optional
        Lane copies, ``(call, source call, source row, part, runs)``: before correlation call
        ``call``'s steps, part 0 (real) or 1 (imaginary) of row ``source row`` of an earlier
        call's output is copied into call's series (a writable contiguous float32 array)
        within ``runs`` (``(k, 2)`` int64), so that call correlates a real lane of a row the
        table writes (an inner node's output filtered by its inner children). The table is
        then scheduled: its correlation steps in ranges with the copies between them, then the
        leaf phases. Not with ``schedule``. Default none.

    Returns
    -------
    _Steps or None
        The compiled steps; None where leaf calls were given and none is one the steps run, or
        a plan cannot read the real series it is given.
    """
    ncorr = len(corr_calls)
    banks, bank_index = [], {}

    # The correlation steps, call by call.
    corr_steps, corr_plans, work = [], {}, {}
    for c, (call, with_scales) in enumerate(zip(corr_calls, scaled)):
        bank, ser, W, support, rows = call[:5]
        S = ser.size
        b = bank_index.get(id(bank))
        if b is None:
            b = bank_index[id(bank)] = len(banks)
            banks.append((weakref.ref(bank), bank._groups))
            work[b] = ({}, 0)
        counters, in_samples = work[b]
        work[b] = (counters, in_samples + int((W[:, 1] - W[:, 0]).sum()))
        if S == 0:
            continue
        # the runs of output rows each step writes: (group, first local, count, first row,
        # rows through a scratch or None)
        runs = []
        if rows is None:
            for g in bank._groups:
                g_indices = g.template_indices
                cnt = len(g_indices)
                if cnt == 0:
                    continue
                if g_indices[-1] - g_indices[0] + 1 == cnt and np.array_equal(
                        g_indices, np.arange(g_indices[0], g_indices[0] + cnt)):
                    runs.append((g, 0, cnt, int(g_indices[0]), None))
                else:
                    runs.append((g, 0, cnt, 0, np.ascontiguousarray(g_indices, np.int64)))
        else:
            for j, t in enumerate(rows):
                g, li = bank._template_map[int(t)]
                if runs and runs[-1][0] is g and runs[-1][1] + runs[-1][2] == li:
                    runs[-1][2] += 1
                else:
                    runs.append([g, li, 1, j, None])
        for g, li, cnt, row0, scattered in runs:
            cplan = g.get_correlation_plan()
            cplan._require_templates(li, cnt)
            ep = cplan._continuous_plan()
            corr_plans[id(cplan)] = (cplan, ep)
            lo, hi = cplan.valid
            # a scratch holds anything: every sample the windows do not hold is cleared
            st, bounds, keep, edges = bank._windows_layout(
                g, S, W, support if scattered is None else None)
            clear = edges.reshape(-1, 2)
            clear = np.ascontiguousarray(clear[clear[:, 1] > clear[:, 0]], np.int64)
            out_rows = (np.arange(row0, row0 + cnt, dtype=np.int64) if scattered is None
                        else scattered)
            corr_steps.append((ep, c, int(ser.dtype == np.float32), c, row0, scattered, li, cnt,
                               st if st.size else None, bounds if st.size else None, lo, hi,
                               clear, c if with_scales else -1,
                               out_rows if with_scales else None,
                               np.array([[0, S]], np.int64) if with_scales else None))
            if st.size:
                n_work = counters.setdefault(g.n, dict(blocks=0, pairs=0, out_samples=0,
                                                       tmpl_values=0))
                n_work["blocks"] += int(st.size)
                n_work["pairs"] += int(st.size) * cnt
                n_work["out_samples"] += int((keep[:, 1] - keep[:, 0]).sum()) * cnt
                n_work["tmpl_values"] += cnt * _stored_bins(g)

    # The leaf steps, call by call, reading series slots after the correlation calls' inputs.
    steps, step_args, jobs, plans, compiled_calls, merges = [], [], [], {}, [], []
    flat_args, flat_plans = [], {}
    modes = {}
    phase = 0
    series = []
    for index, bank, ser, W, cache_key, binsize, eff_threshold, profile in calls:
        if profile is not _SAME_PROFILE:
            bank.use_profile(profile)
        plan_profile = bank._plan_profile(bank.__dict__.get("_profile"))
        # A call these steps do not run is left to the caller (filter_series' own path).
        if (_parse_device(bank.device).kind != 'cpu' or not np.isfinite(eff_threshold)
                or eff_threshold < 0.0 or (binsize is not None and int(binsize) < 1)):
            continue
        groups = bank._groups
        # Ungated (flat steps): a flat bank's call, or a hierarchical bank's below its
        # threshold, on each group's ungated plan, as filter_series chose it.
        flat = bank.engine != 'hier' or eff_threshold < bank.threshold or eff_threshold <= 0.0
        if flat:
            group_plans = [g.get_flat_plan() if bank.engine == 'hier' else g.plan
                           for g in groups]
            if not all(type(p) is MatchedFilter and p._gpu is None and p.ndata == 1
                       and not getattr(p, '_bandlimited', False)
                       and 'run_series' not in p.__dict__ and '_series_flags' not in p.__dict__
                       for p in group_plans):
                continue
        elif all(g.is_hier and _plan_is_gated_cpu(g.plan) for g in groups):
            group_plans = [g.plan for g in groups]
        else:
            continue
        slot = ncorr + extra_series + len(series)
        series.append(ser)
        if id(bank) not in bank_index:
            bank_index[id(bank)] = len(banks)
            banks.append((weakref.ref(bank), groups))
        S = len(ser)
        real = ser.dtype == np.float32
        stride = 2 if real and ser.strides == (8,) else 1
        aligned = binsize is not None or bank.binsize is not None
        merge_bs = []
        for g, plan in zip(groups, group_plans):
            N = g.n
            bstarts, bws, bwe = bank._group_blocks(g, W, S, cache_key)
            if bstarts.size == 0:
                continue
            bs = int(binsize) if binsize is not None else (bank.binsize or N)
            bph = None
            if aligned:
                bph = _bin_phases(g, plan, W, cache_key, bs, bstarts, bws, bwe)
                if bph is not None and bs not in merge_bs:
                    merge_bs.append(bs)
            for sub_st, sub_ws, sub_we, sub_ph in _blocks_by_bin_count(plan, N, bs, bstarts,
                                                                       bws, bwe, bph):
                layout = SeriesLayout(N, np.ascontiguousarray(sub_st, dtype=np.uintp),
                                      np.ascontiguousarray(sub_ws, dtype=np.uintp),
                                      np.ascontiguousarray(sub_we, dtype=np.uintp), bs,
                                      ragged=False, phase=sub_ph)
                job = len(jobs)
                if flat:
                    # One ungated run over the blocks in the caller's order (a plan of one
                    # data row does not group them).
                    nt = plan.ntemplates
                    plan._require_templates(0, nt)
                    ep = plan._execution_plan()
                    flat_plans[id(plan)] = (plan, ep)
                    flat_args.append((ep, slot, int(real), stride, layout.starts, layout.low,
                                      layout.high, layout.phase, nt, bs, float(eff_threshold),
                                      job,
                                      np.ascontiguousarray(g.template_indices, dtype=np.int64),
                                      np.ascontiguousarray(sub_st, dtype=np.int64),
                                      plan._step_stats))
                    continue
                layout.group(materialize=False)
                plan.use_profile(plan_profile)
                nt = plan.ntemplates
                plan._require_templates(0, nt)
                # The plan's series mode, as each call once set it: a mode another step of
                # these calls set otherwise ends the phase (a scheduled step sets its mode
                # for its own block ranges and is in no phase).
                in_phases = index not in scheduled
                previous = getattr(plan, '_mf', None)
                if (in_phases and previous is not None and id(previous) in modes
                        and modes[id(previous)] != (real, stride)):
                    if not split_modes:
                        return None
                    phase += 1
                    modes.clear()
                plan._want_real = real
                ep = plan._execution_plan()
                if in_phases and id(ep) in modes and modes[id(ep)] != (real, stride):
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
                if in_phases:
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
                                  prices, phase if in_phases else -1, job,
                                  np.ascontiguousarray(g.template_indices, dtype=np.int64),
                                  None if layout.order is None
                                  else np.ascontiguousarray(layout.order, dtype=np.int64),
                                  np.ascontiguousarray(sub_st, dtype=np.int64),
                                  plan._step_stats))
                steps.append((index, g, sub_st, layout, plan, ep, nt, bs, float(eff_threshold),
                              real, stride))
        jobs.append((np.ascontiguousarray(W[:, 0], dtype=np.int64), tuple(merge_bs)))
        compiled_calls.append((index, weakref.ref(bank), profile))
        merges.append((W, merge_bs))
    if calls and not compiled_calls and not ncorr and schedule is None:
        return None
    work = [(b, list(counters.items()), in_samples) for b, (counters, in_samples) in work.items()]
    corr_plans = list(corr_plans.values())
    nouts, sched = ncorr, None
    if schedule is not None:
        # the schedule's correlation steps, outputs, ops and accounting after the calls'
        more_corrs, more_outs, sched, more_plans, more_banks, more_work = schedule(
            steps, len(corr_steps))
        corr_steps.extend(more_corrs)
        nouts += more_outs
        corr_plans.extend(more_plans)
        first = len(banks)
        banks.extend(more_banks)
        work.extend((first + b, counters, in_samples) for b, counters, in_samples in more_work)
    elif lanes:
        # the correlation steps in ranges, each call's lane copies before its first step (a
        # step's input slot is its call)
        ops = _Ops()
        pending = {}
        for call, source, row, part, runs in lanes:
            if source >= call:
                raise ValueError("a lane copy reads the output of a later correlation call")
            pending.setdefault(call, []).append((source, row, part, runs))
        first = 0
        for i, step in enumerate(corr_steps):
            copies = pending.pop(step[1], None)
            if copies is None:
                continue
            if i > first:
                ops.op(_Ops.CORR, first, i)
            for source, row, part, runs in copies:
                ops.op(_Ops.LANE, source, row, part, step[1], ops.arg(runs), len(runs))
            first = i
        if first < len(corr_steps):
            ops.op(_Ops.CORR, first, len(corr_steps))
        sched = ops.arrays()
    table = _core.HMFTable(step_args, jobs, ncorr + extra_series + len(series), (), flat_args,
                           corr_steps, nouts, sched)
    return _Steps(table, ncorr, compiled_calls, merges, steps, list(plans.values()), banks,
                  list(flat_plans.values()), corr_plans, work)


def _steps_valid(compiled):
    """Whether compiled steps still describe their banks and plans: the same template groups,
    each leaf plan's compiled plan and resolution of the profile as when compiled, and each
    ungated and correlation plan's compiled plan."""
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
    for plan, ep in compiled.flat_plans:
        if plan.__dict__.get("_mf") is not ep:
            return False
    for plan, ep in compiled.corr_plans:
        if plan.__dict__.get("_mf") is not ep:
            return False
    return True


def _run_steps(compiled, series, outs=None, scales=None, tiles=None):
    """Run compiled steps on bound series (one per slot), outputs and scale vectors (one per
    correlation call, None or an empty vector for a call without) and, for a table with a
    schedule, its tiles (scratch pools' states, the pools, carries), in one C call
    (_core.HMFTable.run), and update what the calls once updated: the plans' data state, the
    correlation banks' work counters and the compute seconds.

    Returns
    -------
    results : list of FilterResults
        Per compiled leaf call, in the order of ``compiled.calls``.
    corr_seconds : float
        The seconds the correlation steps spent in the extension.
    """
    if compiled.calls or tiles is not None or compiled.table.ops:
        # Device writes to shared host-readable series must have landed.
        _settle_device_writes()
        (offs_b, ti_b, si_b, snr_b, bs_b, bl_b, totals_b, seconds_b, kernel,
         corr_seconds) = compiled.table.run(series, (), outs, scales, tiles)
    else:
        # correlation steps only, unscheduled (a correlation call): the table's correlation
        # entry, which assembles no peaks
        kernel = 0.0
        corr_seconds = compiled.table.run_corr(0, compiled.table.corrs, series, outs, scales)
    for plan, _, _, _ in compiled.plans:
        plan._dataset = False
        if plan._data_ready:
            plan._data_ready = set()
    # An ungated plan read its series as complex, as its run_series once left it.
    for plan, _ in compiled.flat_plans:
        plan._dataset = False
        plan._want_real = False
        plan._data_ready = set()
    # The correlation kernels overwrote the plans' data buffers.
    for plan, _ in compiled.corr_plans:
        plan._dataset = False
        if plan._data_ready != _NO_DATA_READY:
            plan._data_ready = set()
    for b, counters, in_samples in compiled.corr_work:
        bank = compiled.banks[b][0]()
        bank._add_corr_in(in_samples)
        for n, counts in counters:
            bank._add_corr_work(n, counts)
    global STEP_COMPUTE_SECONDS, CORR_COMPUTE_SECONDS
    STEP_COMPUTE_SECONDS += kernel
    CORR_COMPUTE_SECONDS += corr_seconds
    if not compiled.calls:
        return [], corr_seconds
    offs = np.frombuffer(offs_b, np.int64)
    columns = (np.frombuffer(ti_b, np.int64), np.frombuffer(si_b, np.int64),
               np.frombuffer(snr_b, np.complex64), np.frombuffer(bs_b, np.int64),
               np.frombuffer(bl_b, np.int64))
    results = []
    for k in range(len(compiled.calls)):
        p0, p1 = int(offs[k]), int(offs[k + 1])
        results.append(_EMPTY_FILTER_RESULTS if p0 == p1
                       else FilterResults(*(c[p0:p1] for c in columns)))
    return results, corr_seconds


def _corr_key(calls, scaled):
    """The part of a compiled table's key that its correlation calls make: per call its bank,
    layout, series length and kind, windows, support, rows and whether it is scaled."""
    return tuple((id(bank), bank.__dict__.get("_layout_rank"), ser.size, ser.dtype.char,
                  W.tobytes(), None if support is None else support.tobytes(),
                  None if rows is None else rows.tobytes(), with_scales)
                 for (bank, ser, W, support, rows, _), with_scales in zip(calls, scaled))


def _call_steps(calls, corr_calls=(), corr_scales=None, lanes=()):
    """The compiled steps of normalised leaf calls (_leaf_call) after correlation calls
    (_corr_call) and their lane copies (_compile_steps), kept by the first call's bank under a
    key of every correlation call's (_corr_key), every lane copy, and every leaf call's bank,
    layout, profile, windows, series kind and stride, bin size and threshold; or None where no
    leaf call compiles."""
    scaled = (tuple(s is not None for s in corr_scales) if corr_scales is not None
              else (False,) * len(corr_calls))
    key = (_corr_key(corr_calls, scaled),
           tuple((id(bank), bank.__dict__.get("_layout_rank"),
                  bank._plan_profile(bank.__dict__.get("_profile") if profile is _SAME_PROFILE
                                     else profile),
                  cache_key, ser.dtype.char, ser.strides, binsize, float(eff_threshold))
                 for _, bank, ser, _, cache_key, binsize, eff_threshold, profile in calls),
           tuple((call, source, row, part, runs.tobytes())
                 for call, source, row, part, runs in lanes))
    first = corr_calls[0][0] if corr_calls else calls[0][1]
    return _memo_steps(first.__dict__.setdefault("_compiled_steps", OrderedDict()), key,
                       (calls, corr_calls, scaled, True, frozenset(), 0, None, lanes))


def _memo_steps(memo, key, compile_args):
    """The compiled steps kept in memo (an OrderedDict a bank owns) under key, checked before
    reuse (_steps_valid), or compiled from compile_args (_compile_steps) and kept, the eight
    most recent at most. None where nothing compiles."""
    compiled = memo.get(key)
    if compiled is not None and _steps_valid(compiled):
        memo.move_to_end(key)
        for _, bank_ref, profile in compiled.calls:
            if profile is not _SAME_PROFILE:
                bank_ref().use_profile(profile)
        return compiled
    compiled = _compile_steps(*compile_args)
    if compiled is not None:
        memo[key] = compiled
        while len(memo) > 8:
            memo.popitem(last=False)
    return compiled


#: The keyword arguments of a filter_series call that the leaf steps run.
_LEAF_KEYS = frozenset(("windows", "binsize", "threshold", "template_index", "profile"))


def _leaf_call(index, bank, series, kw):
    """A leaf job ``bank.filter_series(series, **kw)`` as the call _compile_steps takes
    (``(index, bank, series, W, cache_key, binsize, threshold, profile)``, the series as the
    bank reads it and the windows normalised), _EMPTY_FILTER_RESULTS for a call with no
    window, or None for one the leaf steps do not run (a single template, an argument they
    do not take, a threshold that is not a finite non-negative number, a bank off the CPU, a
    series that is not one-dimensional)."""
    kw = kw or {}
    if kw.get("template_index") is not None or (set(kw) - _LEAF_KEYS):
        return None
    thr_arg = kw.get("threshold")
    eff_threshold = bank.threshold if thr_arg is None else float(thr_arg)
    if not np.isfinite(eff_threshold) or eff_threshold < 0.0:
        return None
    if _parse_device(bank.device).kind != 'cpu':
        return None
    ser = bank._input_series(series)
    if ser.ndim != 1:
        return None
    W, cache_key = bank._call_windows(kw.get("windows"), len(ser))
    if W.shape[0] == 0:
        return _EMPTY_FILTER_RESULTS
    return (index, bank, ser, W, cache_key, kw.get("binsize"), eff_threshold,
            kw.get("profile", _SAME_PROFILE))


def _cpu_sparse_batch(jobs, out, skip=None, pre_jobs=None, corr=None):
    """Run the CPU every-template calls of a batch as compiled leaf steps, in one C call: a
    hierarchical bank's at or above its threshold as gated steps, and a flat bank's or a call
    below a hierarchical bank's threshold as flat steps; with ``corr``, after correlation calls
    in the same table and the same C call.

    The calls' steps are compiled once per call shape (_compile_steps) and kept by the first
    call's bank under a key of every call's bank, layout, profile, series length, kind and
    stride, windows, bin size and threshold (and the correlation calls' key). A run binds the
    series, runs the steps (_core.HMFTable.run) and hands each call the slice of the peak arena
    that is its FilterResults.

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
    corr : tuple, optional
        ``(calls, scales)``: correlation calls on CPU banks as _cpu_correlate takes them, run
        before any leaf call (the leaf series may be rows of their outputs). Default None.
        They always run, in the table or, where no leaf call compiles, on their own.

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
            call = _leaf_call(j, bank, series, kw)
            if call is _EMPTY_FILTER_RESULTS:
                out[j] = _EMPTY_FILTER_RESULTS
                done.add(j)
            elif call is not None:
                calls.append(call)
    corr_calls, corr_scales = corr if corr is not None else ((), None)
    # A leaf series the bank read through a copy made now, of memory a correlation call
    # writes, would be read stale: the correlation calls then run first, on their own.
    if corr_calls and jobs is not None and any(
            isinstance(jobs[c[0]][1], np.ndarray) and not np.may_share_memory(c[2], jobs[c[0]][1])
            and any(np.may_share_memory(jobs[c[0]][1], cc[5]) for cc in corr_calls)
            for c in calls):
        _cpu_correlate(corr_calls, corr_scales)
        return done | _cpu_sparse_batch(jobs, out, skip)
    if (not calls or getattr(MatchedFilter.run_series, '__qualname__', '')
            != 'MatchedFilter.run_series'):
        if corr_calls:
            _cpu_correlate(corr_calls, corr_scales)
        return done

    compiled = _call_steps(calls, corr_calls, corr_scales)
    if compiled is None:
        if corr_calls:
            _cpu_correlate(corr_calls, corr_scales)
        return done
    slot_of = {c[0]: c[2] for c in calls}
    results, _ = _run_steps(
        compiled, [c[1] for c in corr_calls] + [slot_of[j] for j, _, _ in compiled.calls],
        [c[5] for c in corr_calls] if corr_calls else None,
        None if corr_scales is None else [np.empty(0, np.float32) if s is None else s
                                          for s in corr_scales])
    for (j, _, _), res in zip(compiled.calls, results):
        out[j] = res
        done.add(j)
    return done


def _cpu_correlate(calls, scales=None):
    """Run correlation calls on CPU banks as correlation steps, in one C call.

    The steps of a call shape are compiled once (_compile_steps) and kept by the first call's
    bank under a key of every call's bank, layout, series length and kind, windows, support,
    rows and whether it is scaled; a run binds the series, outputs and scale vectors and runs
    every step (_core.HMFTable.run), which writes every output sample the calls' windows and
    supports ask for.

    Parameters
    ----------
    calls : sequence of tuple
        ``(bank, series, windows, support, rows, out)``: as _compile_steps takes them, with
        ``out`` the call's ``(rows, len(series))`` C-contiguous complex64 output.
    scales : sequence, optional
        Per call None or a float32 vector with one scale per output row. Default None: no
        call is scaled.

    Returns
    -------
    float
        The seconds the steps spent in the extension.
    """
    scaled = (False,) * len(calls) if scales is None else tuple(s is not None for s in scales)
    compiled = _memo_steps(calls[0][0].__dict__.setdefault("_compiled_steps", OrderedDict()),
                           (_corr_key(calls, scaled), ()), ((), calls, scaled))
    _, seconds = _run_steps(
        compiled, [c[1] for c in calls], [c[5] for c in calls],
        None if scales is None else [np.empty(0, np.float32) if s is None else s
                                     for s in scales])
    return seconds

#: correlate_series' keyword arguments.
_CORR_KEYS = frozenset(("windows", "scales", "template_index", "out", "wait", "templates",
                        "out_support"))


def _corr_call(bank, series, kw):
    """A correlation job ``bank.correlate_series(series, **kw)`` on a CPU bank as the call
    _compile_steps takes, with its output (``(bank, series, windows, support, rows, out)``),
    and its rows' scale vector or None: the series, windows, selection and support
    normalised, and the output allocated or checked (TimeDomainFilterBank._correlation_call)."""
    templates, out_support = kw.get("templates"), kw.get("out_support")
    ser = bank._series_input(series)
    W, _ = bank._call_windows(kw.get("windows"), ser.size)
    rows, row_scales, result, _, support = bank._correlation_call(
        ser, W, kw.get("scales"), kw.get("template_index"), kw.get("out"),
        None if templates is None else bank._template_selection(templates),
        None if out_support is None else _normalize_windows(out_support, ser.size))
    return (bank, ser, W, support, rows, result), row_scales


def _correlate_jobs(corr_jobs, indices, corr_times):
    """``bank.correlate_series(series, **kwargs)`` for the (bank, series, kwargs) jobs at
    indices, in order: consecutive jobs on CPU banks as the correlation steps of one table
    (one C call, _cpu_correlate), any other job by its own call. A job whose series may lie in
    the output of an earlier job of the batch starts a new batch, so it reads that output
    written. Each job's wall seconds go into corr_times at its index; a batch's are shared
    evenly between its jobs."""
    batch, batch_scales, batch_index = [], [], []

    def flush():
        if batch:
            t0 = time.perf_counter()
            _cpu_correlate(batch, batch_scales if any(s is not None for s in batch_scales)
                           else None)
            share = (time.perf_counter() - t0) / len(batch)
            for ci in batch_index:
                corr_times[ci] += share
            batch.clear()
            batch_scales.clear()
            batch_index.clear()

    for ci in indices:
        bank, series, kw = corr_jobs[ci]
        kw = kw or {}
        if not (set(kw) <= _CORR_KEYS) or not bank._correlates_on_cpu():
            flush()
            t0 = time.perf_counter()
            bank.correlate_series(series, **kw)
            corr_times[ci] += time.perf_counter() - t0
            continue
        if isinstance(series, np.ndarray) and any(np.may_share_memory(series, call[5])
                                                  for call in batch):
            flush()
        t0 = time.perf_counter()
        call, row_scales = _corr_call(bank, series, kw)
        corr_times[ci] += time.perf_counter() - t0
        batch.append(call)
        batch_scales.append(row_scales)
        batch_index.append(ci)
    flush()


def _untiled_batch(corr_jobs, corr_indices, leaf_jobs, leaf_indices, corr_times):
    """The correlation jobs at corr_indices, in order, then the leaf jobs at leaf_indices as
    one filter_series_many batch: the results of the leaf jobs, in order. Where every
    correlation job is on a CPU bank, the leaf banks' trials are decided and every leaf job
    runs on the CPU, the correlation calls and the batch's every-template calls are the steps
    of one table, run by one C call (_run_batch with ``corr``); otherwise the jobs are
    correlated (_correlate_jobs), then filtered. The correlation jobs' seconds go into
    corr_times at their indices: their preparation, and the seconds the correlation steps
    spent in the extension shared evenly."""
    sub_jobs = [leaf_jobs[j] for j in leaf_indices]
    calls, scales = [], []
    t0 = time.perf_counter()
    for ci in corr_indices:
        bank, series, kw = corr_jobs[ci]
        kw = kw or {}
        # A job off the CPU, or whose series may lie in an earlier job's output (its copy
        # would be made before that output is written), is correlated by _correlate_jobs.
        if (not (set(kw) <= _CORR_KEYS) or not bank._correlates_on_cpu()
                or (isinstance(series, np.ndarray)
                    and any(np.may_share_memory(series, call[5]) for call in calls))):
            calls = None
            break
        call, row_scales = _corr_call(bank, series, kw)
        calls.append(call)
        scales.append(row_scales)
    if (calls is None or not _trials_decided(sub_jobs)
            or any(_parse_device(b.device).kind != "cpu" for b, _, _ in sub_jobs)):
        _correlate_jobs(corr_jobs, corr_indices, corr_times)
        return TimeDomainFilterBank.filter_series_many(sub_jobs, wait=True) if sub_jobs else []
    prepared = time.perf_counter() - t0
    corr0 = CORR_COMPUTE_SECONDS
    if not sub_jobs:
        _cpu_correlate(calls, scales if any(s is not None for s in scales) else None)
        results = []
    else:
        results = _run_batch(sub_jobs, True,
                             (calls, scales if any(s is not None for s in scales) else None))
    share = (prepared + CORR_COMPUTE_SECONDS - corr0) / max(1, len(calls))
    for ci in corr_indices:
        corr_times[ci] += share
    return results


def _tiling_cohorts(corr_jobs, leaf_by_corr):
    """Which correlation jobs the tiled cascade runs: (the jobs it cannot run, the cohorts
    of the others (_cohorts))."""
    cand_jobs, screened_out = [], []
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
            screened_out.append(ci)
        else:
            cand_jobs.append((ci, info))
    return screened_out, _cohorts(cand_jobs)


def _chunk_steps(corr_jobs, leaf_jobs, lanes=()):
    """The steps of a search chunk's correlation jobs, their lane copies and the leaf jobs that
    read them, compiled into one table: (the compiled steps, the series they bind, the outputs
    they write), or None where not every job is in it (a job off the CPU, a trial undecided, a
    leaf job the leaf steps do not run or with no window, a series read through a copy of
    memory a correlation writes). The correlation jobs run in order, so a job may read an
    earlier job's output in place (an inner node's complex row, filtered by its own inner
    children), or a real lane of it through its series, which a lane copy fills first
    (``lanes``: ``(job, source job, source row, part, runs)`` as _compile_steps takes them).
    Running them (_run_steps) gives what correlating the jobs in order, filling each lane's
    series as the copy does, and then filtering the leaf jobs (filter_series_many) gives, in
    the order of leaf_jobs."""
    if not _trials_decided(leaf_jobs):
        return None
    corr_calls, corr_scales = [], []
    for bank, series, kw in corr_jobs:
        kw = kw or {}
        if not (set(kw) <= _CORR_KEYS) or not bank._correlates_on_cpu():
            return None
        call, row_scales = _corr_call(bank, series, kw)
        # a copy of an earlier job's output, made now, would be read stale
        if (isinstance(series, np.ndarray) and not np.may_share_memory(call[1], series)
                and any(np.may_share_memory(series, cc[5]) for cc in corr_calls)):
            return None
        corr_calls.append(call)
        corr_scales.append(row_scales)
    calls = []
    for j, (bank, series, kw) in enumerate(leaf_jobs):
        call = _leaf_call(j, bank, series, kw)
        if (call is None or call is _EMPTY_FILTER_RESULTS
                or (isinstance(series, np.ndarray) and not np.may_share_memory(call[2], series)
                    and any(np.may_share_memory(series, cc[5]) for cc in corr_calls))):
            return None
        calls.append(call)
    if not calls or (getattr(MatchedFilter.run_series, '__qualname__', '')
                     != 'MatchedFilter.run_series'):
        return None
    scales = corr_scales if any(sc is not None for sc in corr_scales) else None
    compiled = _call_steps(calls, corr_calls, scales, lanes)
    if compiled is None or len(compiled.calls) != len(calls):
        return None
    return (compiled, [c[1] for c in corr_calls] + [c[2] for c in calls],
            [c[5] for c in corr_calls])


def correlate_and_filter_many(corr_jobs, leaf_jobs, wait=True, timings=None,
                              tile_bytes=None, retain_radius=None,
                              retain_threshold=None):
    """TimeDomainFilterBank.correlate_and_filter_many, which documents it."""

    eff_tile_bytes = 0 if tile_bytes is None else int(tile_bytes)
    if retain_radius is not None:
        retain_radius = int(retain_radius)
        if retain_radius < 0:
            raise ValueError("retain_radius must be non-negative")
    eff_ret_thr = 0.0 if retain_threshold is None else float(retain_threshold)

    def _run_untiled():
        corr_times = [0.0] * len(corr_jobs)
        t_0 = time.perf_counter()
        if wait:
            res = _untiled_batch(corr_jobs, range(len(corr_jobs)), leaf_jobs,
                                 range(len(leaf_jobs)), corr_times)
        else:
            _correlate_jobs(corr_jobs, range(len(corr_jobs)), corr_times)
            res = (TimeDomainFilterBank.filter_series_many(leaf_jobs, wait=wait)
                   if leaf_jobs else [])
        if timings is not None:
            timings["correlate_per_job"] = corr_times
            timings["correlate"] = sum(corr_times)
            timings["filter"] = max(0.0, time.perf_counter() - t_0 - sum(corr_times))
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

    leaf_by_corr, _ = _leaves_by_producer(corr_jobs, leaf_jobs)
    screened_out, cohorts = _tiling_cohorts(corr_jobs, leaf_by_corr)
    # No cohort can run tiled: every job untiled, the correlations and the leaves in one table.
    if not cohorts:
        return _run_untiled()
    _settle_device_writes()
    cascade = _cascade_steps(corr_jobs, leaf_jobs, screened_out, cohorts, eff_tile_bytes,
                             retain_radius, eff_ret_thr)
    if cascade is None:
        return _run_untiled()

    # The table: the untiled correlations, the cohorts' schedules, the untiled leaves.
    corr_times = [0.0] * len(corr_jobs)
    t_0 = time.perf_counter()
    if cascade.before:
        _correlate_jobs(corr_jobs, cascade.before, corr_times)
    results, corr_seconds = _run_steps(cascade.steps, cascade.series, cascade.outs,
                                       cascade.scales, cascade.tiles)
    out_results = [None] * len(leaf_jobs)
    for j in cascade.empty:
        out_results[j] = _EMPTY_FILTER_RESULTS
    for (j, _, _), res in zip(cascade.steps.calls, results):
        out_results[j] = res
    # the leaf jobs the steps do not run, in leaf job order
    if cascade.leftover:
        for j, res in zip(cascade.leftover, TimeDomainFilterBank.filter_series_many(
                [leaf_jobs[j] for j in cascade.leftover], wait=True)):
            out_results[j] = res
    in_table = [ci for ci in range(len(corr_jobs)) if ci not in set(cascade.before)]
    for ci in in_table:
        corr_times[ci] += corr_seconds / len(in_table)
    if timings is not None:
        timings["correlate_per_job"] = corr_times
        timings["correlate"] = sum(corr_times)
        timings["filter"] = max(0.0, time.perf_counter() - t_0 - sum(corr_times))
        timings["ephemeral_used"] = cascade.ephemeral
    return out_results
