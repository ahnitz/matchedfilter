"""Gate chains: one model for every hierarchical configuration.

A configuration is a chain of coarse bands b1 < b2 < ... < bk followed by the
full refine. k = 1 is what used to be called a single-tier gate, k = 2 a
cascade; they are the same object here, enumerated, priced and chosen on equal
footing. Each tier runs on the previous tier's survivors.

Two questions decide a chain, and they are kept separate:

  ACCURACY  For a signal of strength `snr`, the thresholds g1..gk (and on the
            CPU the direct refine's window) must dismiss `fd` of the pairs the
            full filter would keep, on average, with the per-plan tail
            gatemodel.fit_order states. Taken from joint draws of every tier's
            coarse maximum and the fine maximum under signal (the same
            construction as gatemodel, generalised from two tiers to any set of
            bands; all candidate bands are drawn jointly, so every chain is
            evaluated on the same draws).

  COST      Expected cost per (block, template) pair:
                dense(b1) + sum_i P(reach tier i) sparse(b_i | density)
                          + P(reach refine) refine(density)
            The P's are noise-only pass probabilities of whole-block maxima,
            simulated exactly from the reference profile: the filter output
            noise in a block has independent bins with variance given by the
            profile, so a tier at band b sees the b-point inverse transform of
            the first b bins -- precisely its coarse lag grid. Tiers are nested
            and share their noise, so their passes are strongly correlated; the
            simulation carries that, which a product of marginal rates cannot.
            Per-tier costs are measured on the machine the job runs on, through
            the engine itself (calibrate_costs), as functions of survivor
            density: pooled tiers and the refine amortise less when few pairs
            survive. Nothing is tabulated; the numbers belong to this process.

The model does not have to be exact. Its job is to keep the cheapest chain on a
short list; the autotuner measures the short list on the real workload.

The budget is split between the tiers by minimising that cost on half the draws, and
the thresholds are fitted on the other half (plan_chain), so that no choice is judged on
the draws it was made on; the split is part of the chain's plan.
"""
import math
import os
from contextlib import contextmanager
from collections import OrderedDict
from itertools import combinations
from typing import NamedTuple, Optional

import hashlib
import numpy as np

from . import gatemodel as _gm
from . import _costfile
# The decision rules live in _choice; gatechain's callers keep them by these names.
from ._choice import TIE
# The cost file lives in _costfile. The calibration, the bank's layout and the Vulkan back end
# reach these through gatechain (and tests patch _cost_file here), so they stay bound here.
from ._costfile import _cost_warn, _load_cost_file
_cost_file, _store_first = _costfile._cost_file, _costfile._store_first
store_choice, stored_choice = _costfile.store_choice, _costfile.stored_choice

_SIG = _gm._SIG
#: Sub-sample arrival fractions signal_draws spreads its signals over, 1/_NF apart, the sample
#: itself among them: at a high snr only a signal arriving near a sample reaches it on the
#: sampled grid (strata midpoints left no draw detected at snr = 1000). A signal's loss
#: between samples is second order in the offset, so 1/16 of a sample stands for any time.
_NF = 16
_MIN_BAND = 64

#: The per-tier budget shares the split search tries (plan_chain; three tiers search their
#: product). MEASURED: the fitted plans of a search on 19 shares instead (19 x 19 for three
#: tiers) cost within 0.05% of these on average over every given chain, and within 0.4 +- 0.3%
#: for the pick, where a few of 50 picks change chain either way (5 profiles x 10 model seeds,
#: n = 2048 and 4096, fd 1e-3, Zen 5 costs, with and without a direct refine; 2026-10-29). The
#: fit moves every tier's threshold, so the split's fine structure matters little.
_SPLIT = np.linspace(0.05, 0.95, 9)

_SIGNAL_CACHE = OrderedDict()

#: The noise blocks the model's pass rates rest on (model_draws), the signal simulation's
#: first rows (_extend_signal): about 20 blocks pass a tier at a pass rate of 1e-3.
_NOISE_BLOCKS = 20000


def model_draws(fd):
    """(detections, noise blocks) the model runs with at budget fd: the signal simulation's
    detections (gatemodel._nsamp_for; None when the budget needs more than the model holds)
    and the noise blocks, the first of the same simulation's draws (_simulate), so where it
    runs as many they cost nothing more."""
    return _gm._nsamp_for(fd), _NOISE_BLOCKS

_NOISE_CACHE = OrderedDict()
_CACHE_MAX = 64


class GateTier(NamedTuple):
    """One coarse gate tier: transform length `band` and starting fine bin `k0`."""
    band: int
    k0: int = 0


class Tier0Cluster(NamedTuple):
    """Precomputed Tier-0 coarse centroid bank and calibration parameters."""
    specs: np.ndarray
    offsets: np.ndarray
    members: np.ndarray
    lag_pad: int
    ratio: float
    alpha: float
    member_alphas: Optional[np.ndarray] = None


def _band_slice(n, b, k0):
    """Active fine-bin range (k0, khi) for coarse band `b` starting at `k0`."""
    k0 = int(k0)
    if k0 <= 0:
        return 0, int(b)
    return k0, min(k0 + int(b), int(n) // 2)


def cluster_tier0_candidates(
    spectra, power, n, band, k0=0, rho_min=0.90, max_arity=4, input_psd=None
):
    """Build Pass-1 (``k <= 2``) and optional Pass-2 (``k <= max_arity``) Tier-0 centroid banks.

    Parameters
    ----------
    spectra : array_like
        Complex frequency-domain template bank of shape ``(nt, k_bins)``.
    power : array_like
        Expected nonnegative filter-output power profile of length ``n``.
    n : int
        Full fine FFT block length.
    band : int
        Tier-0 coarse FFT band length ``b0`` (must divide ``n`` and be ``< n // 2``).
    k0 : int, optional
        Starting fine bin offset of Tier 0 (default ``0``).
    rho_min : float, optional
        Minimum PSD-weighted in-band coherence required to merge a Pass-1 pair (default ``0.90``).
    max_arity : int, optional
        Maximum cluster arity for Pass 2 in ``{2, 3, 4}`` (default ``4``).
    input_psd : array_like, optional
        Known per-bin input noise PSD ``S_x[k]`` (default ``None``). When provided,
        each template ``t`` is normalized by its own ``1 / sqrt(f_{t,0})`` using exact
        ``S_x[k]`` weights so both merged centroids and singletons have unit coarse
        noise variance.

    Returns
    -------
    tuple of (Tier0Cluster or None, Tier0Cluster or None)
        ``(cl_k2, cl_hi)`` where ``cl_k2`` is the ``k <= 2`` centroid bank (or ``None`` when
        fewer than 15% of templates merge) and ``cl_hi`` is the ``k <= max_arity`` minimax
        centroid bank (or ``None`` when ``max_arity <= 2`` or Pass 2 merges no additional
        clusters).
    """
    n, b0, k0 = int(n), int(band), int(k0)
    cap_arity = int(max_arity)
    if cap_arity < 2:
        raise ValueError("max_arity must be >= 2")
    cap_arity = min(cap_arity, 4)
    H = np.asarray(spectra)
    if H.ndim != 2 or H.shape[0] < 2 or b0 < 1 or b0 >= n // 2 or n % b0 != 0:
        return None, None
    nt = int(H.shape[0])
    p = _norm_profile(power, n)
    k_lo, k_hi = _band_slice(n, b0, k0)
    length = k_hi - k_lo
    if length <= 0 or k_hi > H.shape[1]:
        return None, None
    p_band = p[k_lo:k_hi]
    f0 = float(p_band.sum())
    if f0 <= 0.0:
        return None, None

    H_band = np.asarray(H[:, k_lo:k_hi], dtype=np.complex128)
    h_pow = H_band.real * H_band.real + H_band.imag * H_band.imag
    if input_psd is not None:
        # Exact per-template whitened coarse normalization under known input PSD S_x[k]
        psd_w = np.asarray(input_psd, dtype=np.float64)[:H.shape[1]]
        if psd_w.shape[0] < k_hi:
            return None, None
        full_pow = ((H.real.astype(np.float64) ** 2 + H.imag.astype(np.float64) ** 2)
                    * psd_w[None, :]).sum(axis=1)
        W = np.asarray(psd_w[k_lo:k_hi], dtype=np.float64)
        band_pow = np.sum(h_pow * W[None, :], axis=1)
        f_t0 = np.divide(band_pow, full_pow, out=np.zeros_like(band_pow), where=full_pow > 0.0)
        sc_t = np.divide(1.0, np.sqrt(f_t0), out=np.zeros_like(f_t0), where=f_t0 > 0.0)
        C = H_band * sc_t[:, None]
    else:
        # Estimate scale-free inverse-PSD weights W_k from p_ref / mean_t |H_t[k]|^2
        scale = 1.0 / math.sqrt(f0)
        C = H_band * scale
        m_bin = h_pow.mean(axis=0)
        m_max = float(m_bin.max())
        if m_max <= 0.0:
            return None, None
        W = p_band / np.maximum(m_bin, 1e-6 * m_max)
    sqrt_W = np.sqrt(W)
    c_pow = C.real * C.real + C.imag * C.imag
    v = np.sum(c_pow * W[None, :], axis=1)
    valid = v > 0.0
    valid_idx = np.flatnonzero(valid)
    if valid_idx.size < 2:
        return None, None

    # Order valid templates by mean in-band frequency so neighbors fall in one L1/L2 chunk
    inv_sqrt_v = np.zeros(nt, dtype=np.float64)
    inv_sqrt_v[valid] = 1.0 / np.sqrt(v[valid])
    U64 = (C * (inv_sqrt_v[:, None] * sqrt_W[None, :])).astype(np.complex64)
    u_pow = U64.real * U64.real + U64.imag * U64.imag
    k_idx = np.arange(k_lo, k_hi, dtype=np.float64)
    k_f32 = k_idx.astype(np.float32)
    f_mean = np.sum(u_pow[valid_idx] * k_f32[None, :], axis=1)
    perm = valid_idx[np.argsort(f_mean, kind="stable")]

    # Search coarse shifts in [-R, +R] via a single-core C inner-product pass per chunk
    R = n // b0
    s_step = max(1, R // 8)
    all_dls = np.arange(-R, R + 1, dtype=np.int64)
    exp_all = np.exp((-2j * np.pi / n) * (all_dls[:, None] * k_idx[None, :]))
    dls = all_dls[::s_step]
    zero_pos = int(np.argmin(np.abs(dls)))
    shifts_c128 = exp_all[::s_step]
    shifts64 = shifts_c128.astype(np.complex64)
    shift_order = [zero_pos]
    for s in range(1, len(dls)):
        if zero_pos - s >= 0:
            shift_order.append(zero_pos - s)
        if zero_pos + s < len(dls):
            shift_order.append(zero_pos + s)
    shifts_ord = shifts64[shift_order]
    dls_ord = dls[shift_order]
    Sr = np.ascontiguousarray(shifts_ord.real, dtype=np.float32)
    Si = np.ascontiguousarray(shifts_ord.imag, dtype=np.float32)
    coarse_rho_floor = float(rho_min) * (0.90 if s_step > 1 else 1.0)
    floor2 = coarse_rho_floor * coarse_rho_floor

    def _match_subset(sub_idx, U_arr, v_arr, f2_floor, sizes=None, size_cap=2):
        from . import _core
        m_c = int(sub_idx.size)
        if m_c < 2:
            return [], [], []
        U_c = U_arr[sub_idx]
        v_c = np.ascontiguousarray(v_arr[sub_idx], dtype=np.float64)
        Ur = np.ascontiguousarray(U_c.real, dtype=np.float32)
        Ui = np.ascontiguousarray(U_c.imag, dtype=np.float32)
        best_rho2 = np.empty((m_c, m_c), dtype=np.float32)
        best_s = np.empty((m_c, m_c), dtype=np.int32)
        _core.tier0_pair_scores(Ur, Ui, Sr, Si, v_c, best_rho2, best_s)
        if sizes is not None and size_cap < 4:
            sz_c = sizes[sub_idx]
            best_rho2[sz_c[:, None] + sz_c[None, :] > size_cap] = -1.0
        ri = np.arange(m_c)[:, None]
        if m_c > 9:
            top_cols = np.argpartition(-best_rho2, kth=7, axis=1)[:, :8]
            top_vals = best_rho2[ri, top_cols]
            ia_loc, kb_loc = np.nonzero(top_vals >= f2_floor)
            ib_loc = top_cols[ia_loc, kb_loc]
            cand_r2 = top_vals[ia_loc, kb_loc]
        else:
            ia_loc, ib_loc = np.nonzero(best_rho2 >= f2_floor)
            cand_r2 = best_rho2[ia_loc, ib_loc]
        if ia_loc.size == 0:
            return [], [], []
        order = np.argsort(-cand_r2, kind="stable")
        used = np.zeros(m_c, dtype=bool)
        local_pairs = []
        for idx in order:
            a_l = int(ia_loc[idx])
            b_l = int(ib_loc[idx])
            if used[a_l] or used[b_l]:
                continue
            used[a_l] = True
            used[b_l] = True
            local_pairs.append((a_l, b_l) if a_l < b_l else (b_l, a_l))
        # Resolve 3-edge augmenting swaps (u - w - z - v) when greedy matching strands two nodes
        if m_c - 2 * len(local_pairs) >= 2 and local_pairs:
            sym_r2 = best_rho2 + best_rho2.T
            free_nodes = [i for i in range(m_c) if not used[i]]
            i_u = 0
            while i_u < len(free_nodes):
                node_u = free_nodes[i_u]
                if used[node_u]:
                    i_u += 1
                    continue
                best_gain = -1.0
                best_swap = None
                for i_v in range(i_u + 1, len(free_nodes)):
                    node_v = free_nodes[i_v]
                    if used[node_v]:
                        continue
                    for e_idx, (w_n, z_n) in enumerate(local_pairs):
                        if sym_r2[node_u, w_n] >= f2_floor and sym_r2[node_v, z_n] >= f2_floor:
                            sc = float(sym_r2[node_u, w_n] + sym_r2[node_v, z_n])
                            if sc > best_gain:
                                best_gain = sc
                                best_swap = (
                                    e_idx,
                                    node_v,
                                    (node_u, w_n) if node_u < w_n else (w_n, node_u),
                                    (node_v, z_n) if node_v < z_n else (z_n, node_v),
                                )
                        if sym_r2[node_u, z_n] >= f2_floor and sym_r2[node_v, w_n] >= f2_floor:
                            sc = float(sym_r2[node_u, z_n] + sym_r2[node_v, w_n])
                            if sc > best_gain:
                                best_gain = sc
                                best_swap = (
                                    e_idx,
                                    node_v,
                                    (node_u, z_n) if node_u < z_n else (z_n, node_u),
                                    (node_v, w_n) if node_v < w_n else (w_n, node_v),
                                )
                if best_swap is not None:
                    e_idx, node_v, e1, e2 = best_swap
                    used[node_u] = True
                    used[node_v] = True
                    local_pairs[e_idx] = e1
                    local_pairs.append(e2)
                i_u += 1
        out_a, out_b, out_dl = [], [], []
        for a_l, b_l in local_pairs:
            ta = int(sub_idx[a_l])
            tb = int(sub_idx[b_l])
            dl_ab = int(dls_ord[best_s[a_l, b_l]])
            if ta < tb:
                out_a.append(ta)
                out_b.append(tb)
                out_dl.append(dl_ab)
            else:
                out_a.append(tb)
                out_b.append(ta)
                out_dl.append(-dl_ab)
        return out_a, out_b, out_dl

    def _run_chunked_matching(order_idx, total_nodes, U_arr, v_arr, f2_floor, sizes=None, size_cap=2):
        a_list, b_list, dl_list = [], [], []
        paired_flag = np.zeros(total_nodes, dtype=bool)
        chunk_size = 48
        for c_start in range(0, order_idx.size, chunk_size):
            ca, cb, cdl = _match_subset(
                order_idx[c_start:c_start + chunk_size], U_arr, v_arr, f2_floor, sizes, size_cap
            )
            if ca:
                paired_flag[ca] = True
                paired_flag[cb] = True
                a_list.extend(ca)
                b_list.extend(cb)
                dl_list.extend(cdl)
        rem = order_idx[~paired_flag[order_idx]]
        if rem.size >= 2:
            for c_start in range(0, rem.size, chunk_size):
                ca, cb, cdl = _match_subset(
                    rem[c_start:c_start + chunk_size], U_arr, v_arr, f2_floor, sizes, size_cap
                )
                if ca:
                    a_list.extend(ca)
                    b_list.extend(cb)
                    dl_list.extend(cdl)
        return a_list, b_list, dl_list

    def _pack_cluster(bvecs_c64, offs_i32, mems_i32, alphas_arr, max_dl):
        nc_out = int(offs_i32.size) - 1
        specs_out = np.zeros((nc_out, b0), dtype=np.complex64)
        if k0 <= 0:
            specs_out[:, :length] = bvecs_c64
        else:
            u0 = k_lo & (b0 - 1)
            first = min(length, b0 - u0)
            if first > 0:
                specs_out[:, u0:u0 + first] = bvecs_c64[:, :first]
            if length > first:
                specs_out[:, :length - first] = bvecs_c64[:, first:]
        lpad = int((max_dl + R - 1) // R) if max_dl > 0 else 0
        rat = round((nc_out / float(nt)) * 20.0) / 20.0
        raw_a = float(np.mean(alphas_arr) - 0.5 * np.std(alphas_arr))
        eff_a = max(0.5, min(1.0, math.floor(raw_a * 50.0 + 1e-9) / 50.0))
        return Tier0Cluster(specs=specs_out, offsets=offs_i32, members=mems_i32,
                            lag_pad=lpad, ratio=rat, alpha=eff_a,
                            member_alphas=alphas_arr.astype(np.float32))

    pair_a_list, pair_b_list, pair_dl_list = _run_chunked_matching(
        perm, nt, U64, v, floor2
    )
    max_nc = int(0.85 * nt)
    npairs = len(pair_a_list)
    if npairs == 0 or (nt - npairs) > max_nc:
        return None, None

    # Pass 1: vectorized exact complex128 lag refinement and unit-variance pair synthesis
    pa = np.asarray(pair_a_list, dtype=np.int32)
    pb = np.asarray(pair_b_list, dtype=np.int32)
    pdl = np.asarray(pair_dl_list, dtype=np.int64)
    Ca_u = C[pa] * inv_sqrt_v[pa, None]
    Cb_u = C[pb] * inv_sqrt_v[pb, None]
    prod_ab = (W[None, :] * Ca_u.conj()) * Cb_u

    sub_offs = np.arange(-(s_step - 1), s_step, dtype=np.int64) if s_step > 1 else None
    if sub_offs is not None:
        cand_dls = np.clip(pdl[:, None] + sub_offs[None, :], -R, R)
        phases_sub = exp_all[cand_dls + R]
        g_sub = np.sum(prod_ab[:, None, :] * phases_sub, axis=2)
        best_sub = np.argmax(np.abs(g_sub), axis=1)
        row_idx = np.arange(npairs)
        pdl = cand_dls[row_idx, best_sub]
        g_vec = g_sub[row_idx, best_sub]
    else:
        g_vec = np.sum(prod_ab * exp_all[pdl + R], axis=1)

    rho_vec = np.abs(g_vec)
    keep_mask = rho_vec >= float(rho_min)
    if not np.all(keep_mask):
        pa = pa[keep_mask]
        pb = pb[keep_mask]
        pdl = pdl[keep_mask]
        Ca_u = Ca_u[keep_mask]
        Cb_u = Cb_u[keep_mask]
        g_vec = g_vec[keep_mask]
        rho_vec = rho_vec[keep_mask]
        npairs = int(pa.size)
        if npairs == 0 or (nt - npairs) > max_nc:
            return None, None

    Cb_u_s = Cb_u * exp_all[pdl + R]
    u_psi = g_vec.conj() / rho_vec
    target_v = 0.5 * (v[pa] + v[pb])
    pair_vecs_128 = (
        (np.sqrt(target_v) / np.sqrt(2.0 * (1.0 + rho_vec)))[:, None]
        * (Ca_u + u_psi[:, None] * Cb_u_s)
    )
    pair_vecs = pair_vecs_128.astype(np.complex64)

    base_ret = np.sqrt(0.5 * (1.0 + rho_vec))
    alphas = np.ones(nt, dtype=np.float64)
    alphas[pa] = np.minimum(1.0, np.sqrt(target_v / v[pa]) * base_ret)
    alphas[pb] = np.minimum(1.0, np.sqrt(target_v / v[pb]) * base_ret)
    max_abs_dl = int(np.max(np.abs(pdl))) if npairs > 0 else 0

    partner = np.full(nt, -1, dtype=np.int32)
    pair_slot = np.full(nt, -1, dtype=np.int32)
    partner[pa] = pb
    partner[pb] = pa
    pair_slot[pa] = np.arange(npairs, dtype=np.int32)

    nc = nt - npairs
    band_vecs = np.empty((nc, length), dtype=np.complex64)
    band_vecs_128 = np.empty((nc, length), dtype=np.complex128) if cap_arity > 2 else None
    v_cl2 = np.empty(nc, dtype=np.float64) if cap_arity > 2 else None
    dl_cl2 = np.zeros(nc, dtype=np.int64) if cap_arity > 2 else None
    offsets = np.empty(nc + 1, dtype=np.int32)
    members = np.empty(nt, dtype=np.int32)
    ci = 0
    m_pos = 0
    for t in range(nt):
        b = int(partner[t])
        if b >= 0 and b < t:
            continue
        offsets[ci] = m_pos
        if b > t:
            slot = int(pair_slot[t])
            band_vecs[ci] = pair_vecs[slot]
            if cap_arity > 2:
                band_vecs_128[ci] = pair_vecs_128[slot]
                v_cl2[ci] = target_v[slot]
                dl_cl2[ci] = abs(int(pdl[slot]))
            members[m_pos] = t
            members[m_pos + 1] = b
            m_pos += 2
        else:
            band_vecs[ci] = C[t].astype(np.complex64)
            if cap_arity > 2:
                band_vecs_128[ci] = C[t]
                v_cl2[ci] = v[t]
            members[m_pos] = t
            m_pos += 1
        ci += 1
    offsets[ci] = m_pos

    cl_k2 = _pack_cluster(band_vecs, offsets, members, alphas, max_abs_dl)
    if cap_arity <= 2 or nc < 2:
        return cl_k2, None

    # Pass 2: pair-of-pairs matching on Pass-1 centroids + 2-step minimax weight synthesis
    sz_2 = offsets[1:] - offsets[:-1]
    valid2 = (v_cl2 > 0.0) & (sz_2 < cap_arity)
    valid2_idx = np.flatnonzero(valid2)
    if valid2_idx.size < 2:
        return cl_k2, None

    inv_sqrt_v2 = np.zeros(nc, dtype=np.float64)
    inv_sqrt_v2[valid2] = 1.0 / np.sqrt(v_cl2[valid2])
    U2_64 = (band_vecs_128 * (inv_sqrt_v2[:, None] * sqrt_W[None, :])).astype(np.complex64)
    u2_pow = U2_64.real * U2_64.real + U2_64.imag * U2_64.imag
    f_mean2 = np.sum(u2_pow[valid2_idx] * k_f32[None, :], axis=1)
    perm2 = valid2_idx[np.argsort(f_mean2, kind="stable")]

    rho_min_p2 = max(0.84, float(rho_min) - 0.05)
    coarse_floor_p2 = rho_min_p2 * (0.90 if s_step > 1 else 1.0)
    ca_list, cb_list, _ = _run_chunked_matching(
        perm2, nc, U2_64, v_cl2, coarse_floor_p2 * coarse_floor_p2, sizes=sz_2, size_cap=cap_arity
    )
    if not ca_list:
        return cl_k2, None

    # Filter Pass-2 candidates by group variance compatibility and collect member lag pairs
    cand_groups = []
    cand_pairs = []
    ref_list = []
    mem_list = []
    for ca_i, cb_i in zip(ca_list, cb_list):
        grp = sorted(
            int(x)
            for x in list(members[offsets[ca_i]:offsets[ca_i + 1]])
            + list(members[offsets[cb_i]:offsets[cb_i + 1]])
        )
        v_grp = v[grp]
        if float(v_grp.min()) < 0.80 * float(v_grp.max()):
            continue
        t0_ref = grp[0]
        for tj in grp[1:]:
            ref_list.append(t0_ref)
            mem_list.append(tj)
        cand_groups.append(grp)
        cand_pairs.append((ca_i, cb_i))
    if not cand_groups:
        return cl_k2, None

    # Align every candidate member tj to its group reference t0_ref across [-R, +R]
    ref_arr = np.asarray(ref_list, dtype=np.int32)
    mem_arr = np.asarray(mem_list, dtype=np.int32)
    prod_p2 = (W[None, :] * (C[ref_arr] * inv_sqrt_v[ref_arr, None]).conj()) * (
        C[mem_arr] * inv_sqrt_v[mem_arr, None]
    )
    g_coarse_p2 = prod_p2 @ shifts_c128.T
    dl_p2 = dls[np.argmax(np.abs(g_coarse_p2), axis=1)]
    if sub_offs is not None:
        cand_dls_p2 = np.clip(dl_p2[:, None] + sub_offs[None, :], -R, R)
        g_sub_p2 = np.sum(prod_p2[:, None, :] * exp_all[cand_dls_p2 + R], axis=2)
        dl_p2 = cand_dls_p2[np.arange(dl_p2.size), np.argmax(np.abs(g_sub_p2), axis=1)]

    # Group candidates by arity m in {2, 3, 4} for vectorized 2-step minimax synthesis
    alpha_floor = max(0.88, min(0.93, float(rho_min) + 0.03))
    by_arity = {2: [], 3: [], 4: []}
    pos_dl = 0
    for idx_g, grp in enumerate(cand_groups):
        m_arity = len(grp)
        dls_grp = [0] + [int(x) for x in dl_p2[pos_dl:pos_dl + m_arity - 1]]
        pos_dl += m_arity - 1
        by_arity[m_arity].append((idx_g, grp, dls_grp))

    accepted = {}
    for m_arity, bucket in by_arity.items():
        if not bucket:
            continue
        g_ids = [item[0] for item in bucket]
        grp_mat = np.asarray([item[1] for item in bucket], dtype=np.int32)
        dls_mat = np.asarray([item[2] for item in bucket], dtype=np.int64)
        U_raw = (C[grp_mat] * inv_sqrt_v[grp_mat, None]) * exp_all[dls_mat + R]
        g0 = np.sum(W[None, None, :] * U_raw[:, 0:1, :].conj() * U_raw, axis=2)
        abs_g0 = np.abs(g0)
        phase0 = np.where(abs_g0 > 1e-12, g0.conj() / np.maximum(abs_g0, 1e-12), 1.0 + 0.0j)
        U_tilde = U_raw * phase0[:, :, None]

        # Unweighted aligned mean baseline + 4-step Multiplicative Weights Update (Hedge) minimax
        mean_vec = np.mean(U_tilde, axis=1)
        mean_norm = np.sqrt(np.maximum(
            np.sum((mean_vec.real * mean_vec.real + mean_vec.imag * mean_vec.imag) * W[None, :], axis=1),
            1e-30,
        ))
        c_mean = mean_vec / mean_norm[:, None]
        ov_mean = np.abs(np.sum(W[None, None, :] * c_mean[:, None, :].conj() * U_raw, axis=2))

        weights = np.ones((len(bucket), m_arity), dtype=np.float64)
        U_iter = U_tilde.copy()
        for _ in range(4):
            s_vec = np.sum(weights[:, :, None] * U_iter, axis=1)
            s_norm = np.sqrt(np.maximum(
                np.sum((s_vec.real * s_vec.real + s_vec.imag * s_vec.imag) * W[None, :], axis=1),
                1e-30,
            ))
            c_iter = s_vec / s_norm[:, None]
            ov = np.sum(W[None, None, :] * c_iter[:, None, :].conj() * U_iter, axis=2)
            abs_ov = np.abs(ov)
            rephase = np.where(abs_ov > 1e-12, ov.conj() / np.maximum(abs_ov, 1e-12), 1.0 + 0.0j)
            U_iter = U_iter * rephase[:, :, None]
            deficit = np.maximum(1.0 - abs_ov, 0.0)
            shift_def = deficit - np.min(deficit, axis=1, keepdims=True)
            weights = weights * np.exp(np.minimum(25.0 * shift_def, 10.0))
            weights = weights / np.mean(weights, axis=1, keepdims=True)

        s_vec = np.sum(weights[:, :, None] * U_iter, axis=1)
        s_norm = np.sqrt(np.maximum(
            np.sum((s_vec.real * s_vec.real + s_vec.imag * s_vec.imag) * W[None, :], axis=1),
            1e-30,
        ))
        c_mwu = s_vec / s_norm[:, None]
        ov_mwu = np.abs(np.sum(W[None, None, :] * c_mwu[:, None, :].conj() * U_raw, axis=2))
        use_mwu = np.min(ov_mwu, axis=1) >= np.min(ov_mean, axis=1)
        c_unit = np.where(use_mwu[:, None], c_mwu, c_mean)
        exact_ov = np.where(use_mwu[:, None], ov_mwu, ov_mean)
        v_mem = v[grp_mat]
        v_bar = np.mean(v_mem, axis=1)
        alpha_mat = np.minimum(1.0, np.sqrt(v_bar[:, None] / v_mem) * exact_ov)
        c_vecs_64 = (np.sqrt(v_bar)[:, None] * c_unit).astype(np.complex64)

        for row_k, gid in enumerate(g_ids):
            if float(alpha_mat[row_k].min()) >= alpha_floor:
                accepted[gid] = (
                    c_vecs_64[row_k],
                    grp_mat[row_k],
                    alpha_mat[row_k],
                    int(np.max(np.abs(dls_mat[row_k]))),
                )

    if not accepted:
        return cl_k2, None

    merged_c2 = np.full(nc, -1, dtype=np.int32)
    merged_partner = np.full(nc, -1, dtype=np.int32)
    for gid, (ca_i, cb_i) in enumerate(cand_pairs):
        if gid in accepted:
            lo_c, hi_c = (ca_i, cb_i) if ca_i < cb_i else (cb_i, ca_i)
            merged_c2[lo_c] = gid
            merged_partner[lo_c] = hi_c
            merged_partner[hi_c] = lo_c

    nc_hi = nc - len(accepted)
    band_vecs_hi = np.empty((nc_hi, length), dtype=np.complex64)
    offsets_hi = np.empty(nc_hi + 1, dtype=np.int32)
    members_hi = np.empty(nt, dtype=np.int32)
    alphas_hi = alphas.copy()
    max_dl_hi = 0
    ci_hi = 0
    m_pos_hi = 0
    for c_idx in range(nc):
        other_c = int(merged_partner[c_idx])
        if other_c >= 0 and other_c < c_idx:
            continue
        offsets_hi[ci_hi] = m_pos_hi
        if other_c > c_idx:
            c_vec, grp_row, a_row, dl_row = accepted[int(merged_c2[c_idx])]
            band_vecs_hi[ci_hi] = c_vec
            m_len = int(grp_row.size)
            members_hi[m_pos_hi:m_pos_hi + m_len] = grp_row
            alphas_hi[grp_row] = a_row
            if dl_row > max_dl_hi:
                max_dl_hi = dl_row
            m_pos_hi += m_len
        else:
            band_vecs_hi[ci_hi] = band_vecs[c_idx]
            s0, s1 = int(offsets[c_idx]), int(offsets[c_idx + 1])
            m_len = s1 - s0
            members_hi[m_pos_hi:m_pos_hi + m_len] = members[s0:s1]
            if int(dl_cl2[c_idx]) > max_dl_hi:
                max_dl_hi = int(dl_cl2[c_idx])
            m_pos_hi += m_len
        ci_hi += 1
    offsets_hi[ci_hi] = m_pos_hi

    cl_hi = _pack_cluster(band_vecs_hi, offsets_hi, members_hi, alphas_hi, max_dl_hi)
    return cl_k2, cl_hi


def cluster_tier0_templates(
    spectra, power, n, band, k0=0, rho_min=0.90, max_arity=2, input_psd=None
):
    """Build a lag-and-phase-aligned Tier-0 coarse centroid bank up to ``max_arity``.

    Parameters
    ----------
    spectra : array_like
        Complex frequency-domain template bank of shape ``(nt, k_bins)``.
    power : array_like
        Expected nonnegative filter-output power profile of length ``n``.
    n : int
        Full fine FFT block length.
    band : int
        Tier-0 coarse FFT band length ``b0`` (must divide ``n`` and be ``< n // 2``).
    k0 : int, optional
        Starting fine bin offset of Tier 0 (default ``0``).
    rho_min : float, optional
        Minimum PSD-weighted in-band coherence required to merge a Pass-1 pair (default ``0.90``).
    max_arity : int, optional
        Maximum templates merged into a single centroid in ``{2, 3, 4}`` (default ``2``).
    input_psd : array_like, optional
        Known per-bin input noise PSD ``S_x[k]`` (default ``None``).

    Returns
    -------
    Tier0Cluster or None
        Precomputed centroid spectra ``(nt0, b0)``, CSR ``offsets`` ``(nt0 + 1,)``,
        ``members`` ``(nt,)``, coarse window ``lag_pad``, quantized count ``ratio``,
        conservative signal-retention factor ``alpha``, and per-template ``member_alphas``,
        or ``None`` when ``nt < 2`` or fewer than 15% of templates merge.
    """
    cl_k2, cl_hi = cluster_tier0_candidates(
        spectra, power, n, band, k0=k0, rho_min=rho_min, max_arity=max_arity,
        input_psd=input_psd,
    )
    if int(max_arity) <= 2 or cl_hi is None:
        return cl_k2
    return cl_hi


def compute_psd_template_model(spectra, input_psd, n, hermitian=False, power=None, floor=_MIN_BAND):
    """Compute bank-mean output profile and per-template coarse retention matrix under `input_psd`.

    Parameters
    ----------
    spectra : array_like
        Complex frequency-domain template bank of shape ``(nt, k_bins)``.
    input_psd : array_like
        Per-bin input noise PSD ``S_x[k]`` of length ``>= k_bins``.
    n : int
        Full fine FFT block length.
    hermitian : bool, optional
        Whether ``spectra`` uses half-length Hermitian packing (``k_bins == n // 2`` with
        Nyquist packed in DC's imaginary part; default ``False``).
    power : array_like, optional
        Explicit length-``n`` reference profile override (default ``None``, which uses
        the bank-mean output profile ``bar_p``).
    floor : int, optional
        Smallest candidate coarse band (default ``_MIN_BAND``).

    Returns
    -------
    tuple
        ``(bar_p, template_alphas)`` where ``bar_p`` is the length-``n`` float32 bank-mean
        output power profile (or ``None`` if all templates are zero) and ``template_alphas``
        is ``(cand_bands, alphas_2d)`` with ``alphas_2d`` of shape ``(nt, len(cand_bands))``
        float32 (or ``None`` when ``nt < 2`` or all templates match ``ref_p``).
    """
    n = int(n)
    H = np.asarray(spectra)
    if H.ndim != 2 or H.shape[0] < 1:
        return None, None
    nt, k_bins = int(H.shape[0]), int(H.shape[1])
    psd_full = np.asarray(input_psd, dtype=np.float64)
    if psd_full.ndim != 1 or psd_full.shape[0] < k_bins:
        return None, None

    # Build per-template normalized length-n output power profiles matching hmf.c folding
    p_t = np.zeros((nt, n), dtype=np.float64)
    if k_bins == n // 2 and hermitian:
        w0 = psd_full[0]
        wn = psd_full[k_bins] if psd_full.shape[0] > k_bins else psd_full[k_bins - 1]
        w_pos = psd_full[1:k_bins]
        w_neg = (psd_full[k_bins + 1:n][::-1]
                 if psd_full.shape[0] >= n else psd_full[1:k_bins])
        rsq = (H[:, 1:k_bins].real.astype(np.float64) ** 2
               + H[:, 1:k_bins].imag.astype(np.float64) ** 2)
        dc_pow = w0 * (H[:, 0].real.astype(np.float64) ** 2)
        nyq_pow = wn * (H[:, 0].imag.astype(np.float64) ** 2)
        pos_pow = rsq * w_pos[None, :]
        neg_pow = rsq * w_neg[None, :]
        tot = dc_pow + nyq_pow + pos_pow.sum(axis=1) + neg_pow.sum(axis=1)
        valid = tot > 0.0
        if not np.any(valid):
            return None, None
        inv_tot = np.zeros(nt, dtype=np.float64)
        inv_tot[valid] = 1.0 / tot[valid]
        p_t[valid, 0] = dc_pow[valid] * inv_tot[valid]
        p_t[valid, 1:k_bins] = pos_pow[valid] * inv_tot[valid, None]
        p_t[valid, k_bins] = nyq_pow[valid] * inv_tot[valid]
        p_t[valid, k_bins + 1:] = (neg_pow[valid] * inv_tot[valid, None])[:, ::-1]
    else:
        psd_w = psd_full[:k_bins]
        raw_pow = ((H.real.astype(np.float64) ** 2 + H.imag.astype(np.float64) ** 2)
                   * psd_w[None, :])
        tot = raw_pow.sum(axis=1)
        valid = tot > 0.0
        if not np.any(valid):
            return None, None
        p_t[valid, :k_bins] = raw_pow[valid] / tot[valid, None]

    bar_p64 = p_t[valid].mean(axis=0)
    bar_sum = float(bar_p64.sum())
    if bar_sum <= 0.0:
        return None, None
    bar_p64 /= bar_sum
    if not np.all(valid):
        p_t[~valid] = bar_p64
    bar_p = bar_p64.astype(np.float32)

    if nt < 2 and power is None:
        return bar_p, None
    ref_p = bar_p64 if power is None else _norm_profile(power, n)
    c_bands = candidate_bands(n, floor)
    if not c_bands:
        return bar_p, None

    # Separate per-template signal retention (amp * scalloping) from fine-coarse noise correlation
    sig_alphas = np.ones((nt, len(c_bands)), dtype=np.float32)
    noise_alphas = np.ones((nt, len(c_bands)), dtype=np.float32)
    trapz_w = np.array([0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5], dtype=np.float64) / 8.0
    for j, b in enumerate(c_bands):
        k0 = band_offset(ref_p, n, b)
        k_lo, k_hi = _band_slice(n, b, k0)
        f_bar = float(ref_p[k_lo:k_hi].sum())
        if f_bar <= 0.0:
            continue
        q_t = p_t[:, k_lo:k_hi]
        f_t = q_t.sum(axis=1)
        amp_ratio = np.sqrt(np.maximum(f_t, 0.0) / f_bar)
        ds = np.linspace(0.0, (n // b) / 2.0, 9)
        k_idx = np.arange(k_lo, k_hi, dtype=np.float64)
        exp_mat = np.exp((2j * np.pi / n) * np.outer(k_idx, ds))
        g_bar = np.abs((ref_p[k_lo:k_hi] / f_bar) @ exp_mat)
        q_norm = np.divide(q_t, f_t[:, None], out=np.zeros_like(q_t), where=f_t[:, None] > 0.0)
        g_t = np.abs(q_norm @ exp_mat)
        scal_ratio = (g_t / np.maximum(g_bar[None, :], 1e-6)) @ trapz_w
        scal_ratio = np.where(f_t > 0.0, scal_ratio, 1.0)
        sig_alphas[:, j] = (amp_ratio * scal_ratio).astype(np.float32)
        noise_alphas[:, j] = np.minimum(1.0, amp_ratio).astype(np.float32)

    alphas = np.stack([sig_alphas, noise_alphas], axis=0)
    if np.allclose(alphas, 1.0, atol=1e-3):
        return bar_p, None
    return bar_p, (tuple(int(b) for b in c_bands), alphas)


def band_offset(power, n, b):
    """Starting fine bin k0 (8-bin aligned, 0 <= k0 <= n // 2 - b) maximizing worst-case
    midpoint coarse SNR per unit fine SNR over [k0, k0 + b).

    Parameters
    ----------
    power : array_like
        Expected nonnegative filter-output power per fine frequency bin (length `n`).
    n : int
        Full fine FFT block length.
    b : int
        Coarse band transform length.

    Returns
    -------
    int
        Optimal 8-bin-aligned starting bin `k0`, or `0` when shifting improves midpoint
        coarse SNR by at most 0.01 per unit fine SNR (or `b >= n // 2`).
    """
    n, b = int(n), int(b)
    if b >= n // 2 or b < 1:
        return 0
    p = np.asarray(power, dtype=np.float64)
    if p.shape != (n,) or not np.all(np.isfinite(p)):
        return 0
    pos = np.where(p > 0.0, p, 0.0)
    tot = float(pos.sum())
    if tot <= 0.0:
        return 0
    w = pos[:n // 2] / tot
    if float(w.sum()) <= 0.0:
        return 0
    cf = np.concatenate(([0.0], np.cumsum(w)))
    k0s = np.arange(0, n // 2 - b + 1, 8, dtype=np.int64)
    # Only skip leading dead-zone bins (<= 1e-5 of total power) when they span at least half
    # of the DC-anchored band [0, b), keeping k0 anchored to the low-frequency cutoff.
    k0s = k0s[cf[k0s] <= 1e-5]
    if k0s.size <= 1 or int(k0s[-1]) < b // 2:
        return 0
    k = np.arange(n // 2, dtype=np.float64)
    cz = np.concatenate(([0.0j], np.cumsum(w * np.exp(1j * np.pi * k / b))))
    f = cf[k0s + b] - cf[k0s]
    z = np.abs(cz[k0s + b] - cz[k0s])
    rho = np.where(f > 1e-12, z / np.sqrt(np.maximum(f, 1e-30)), 0.0)
    best = int(np.argmax(rho))
    if int(k0s[best]) >= b // 2 and rho[best] > rho[0] + 0.01:
        return int(k0s[best])
    return 0


def candidate_bands(n, floor=_MIN_BAND):
    """Every band a tier can use at transform size n: powers of two in [floor, n/2]."""
    out, b = [], int(floor)
    while b <= n // 2:
        out.append(b)
        b *= 2
    return out


def usable_bands(power, n, floor=_MIN_BAND):
    """Candidate bands that hold some of the profile's power (a band with none cannot gate)."""
    p = np.asarray(power, dtype=np.float64)
    out = []
    for b in candidate_bands(n, floor):
        k0, khi = _band_slice(n, b, band_offset(p, n, b))
        if p[k0:khi].sum() > 0:
            out.append(b)
    return out


def enumerate_chains(n, max_tiers=3, floor=_MIN_BAND, bands=None):
    """All increasing band tuples of length 1..max_tiers."""
    bands = candidate_bands(n, floor) if bands is None else list(bands)
    out = []
    for k in range(1, int(max_tiers) + 1):
        out.extend(combinations(bands, k))
    return out


def _norm_profile(power, n):
    p = np.asarray(power, dtype=np.float64)
    if (p.shape != (n,) or not np.isfinite(p).all() or (p < 0).any() or p.sum() <= 0):
        raise ValueError("power must be a finite nonnegative length-n profile with positive sum")
    return p / p.sum()


def _key(p, n, bands, *rest):
    return (_gm._profile_sig(p), n, tuple(bands)) + tuple(rest)


def _cache_put(cache, key, value):
    cache[key] = value
    while len(cache) > _CACHE_MAX:
        cache.popitem(last=False)


_SIMILAR = {}           # (kind, n, bands, params) -> [((unit profile, gate features), value)]

#: Reuse tolerances: a profile takes a cached result of another only if their shapes agree
#: (cosine, a cheap first test) AND every candidate band's signal response sqrt(f_b) g_b
#: (in-band power fraction times the worst coarse-grid loss, _gate_features) agrees to this
#: relative tolerance. The response is what sets a gate's dismissal: 3% of it at band 128
#: (an O4 against an A+ reference, cosine 0.995) put a borrowed plan at 4.3x its budget, and
#: 5% PSD jitter moves it as much, so the cosine alone cannot tell them apart.
_REUSE_COS = 0.985
_REUSE_RESPONSE = 3e-3


_FEATURES = OrderedDict()


def _gate_features(p, n, m=17):
    """Per candidate band b of n: sqrt(f_b) * g_b, f_b the band's share of the profile and g_b
    the smallest normalised in-band correlation over half a coarse step (the worst sub-grid
    offset). Memoised per profile (every similarity lookup asks again: ~1000 a job)."""
    p = np.asarray(p, np.float64)
    key = (hashlib.sha1(p.tobytes()).digest(), p.size, int(n), int(m))
    hit = _FEATURES.get(key)
    if hit is None:
        hit = _FEATURES[key] = _gate_features_uncached(p, n, m)
        while len(_FEATURES) > 4096:
            _FEATURES.popitem(last=False)
    return hit.copy()


def _gate_features_uncached(p, n, m):
    tot = p.sum()
    out = []
    for b in candidate_bands(int(n)):
        k0, khi = _band_slice(int(n), b, band_offset(p, n, b))
        q = p[k0:khi]
        f = q.sum() / tot if tot > 0 else 0.0
        if f <= 0:
            out.append(0.0)
            continue
        ds = np.linspace(0.0, (n // b) / 2.0, m)
        g = np.abs(np.exp(2j * np.pi * np.outer(ds, np.arange(k0, khi)) / n) @ (q / q.sum())).min()
        out.append(float(np.sqrt(f) * g))
    return np.array(out)


def _similar_get(kind, p, params):
    u = (p / np.linalg.norm(p)).astype(np.float32)
    feats = None
    for (v, fv), val in _SIMILAR.get((kind,) + params, []):
        if float(np.dot(u, v)) < _REUSE_COS:
            continue
        if feats is None:
            feats = _gate_features(p, params[0])
        if fv.shape == feats.shape and np.all(
                np.abs(fv - feats) <= _REUSE_RESPONSE * np.maximum(np.abs(feats), 1e-12)):
            return (u, feats), val
    if feats is None:
        feats = _gate_features(p, params[0])
    return (u, feats), None


def _similar_put(kind, u, params, value, keep=None):
    lst = _SIMILAR.setdefault((kind,) + params, [])
    lst.append((u, value))
    del lst[:-(keep or _CACHE_MAX)]


#: The gate model's stream domain: its draws are _core.gauss_fill's (src/gauss.cc) at this
#: domain and the seed, counter-based, so any block's draws depend only on its position.
_DOMAIN_SIGNAL = 1
#: The gate model's simulation seed: signal_draws and noise_block_maxima read one simulation.
_SEED = 13


def _coarse_lags_padded(n, b, w0, w1, lag_pad=0):
    """Coarse-lag range `(c0, c1)` for band `b` widened by `lag_pad` coarse samples (`hmf.c`)."""
    from ._windows import coarse_lags
    lp = int(lag_pad)
    if lp <= 0:
        return coarse_lags(n, b, w0, w1)
    r = n // int(b)
    w0, w1 = int(w0), int(w1)
    if w0 < lp * r or w1 + lp * r > n:
        return 0, int(b)
    pad = 1 + lp
    c0 = w0 // r
    c0 = c0 - pad if c0 > pad else 0
    c1 = min(int(b), -(-w1 // r) + pad)
    return c0, max(c0 + 1, c1)


def _engine_lags(n, bands, window):
    """(w0, w1, c0, c1): the fine lags [w0, w1) and each band's coarse lags [c0, c1) the engine
    searches for `window` (hmf.c: one coarse sample past each end inside the block)."""
    from ._windows import coarse_lags
    w0, w1 = (0, n) if window is None else (int(window[0]), int(window[1]))
    lags = [coarse_lags(n, b, w0, w1) for b in bands]
    return w0, w1, tuple(c[0] for c in lags), tuple(c[1] for c in lags)


#: Rows per block of the signal simulation's arrival draws (_arrivals): a row's arrival depends
#: only on its row, so a simulation extended in steps draws what one run at once draws.
_ARRIVAL_ROWS = 1 << 14
#: The signal simulation per (profile, n, bands, snr, seed): every window's draws come from it
#: (signal_draws), so a profile's windows share one simulation, extended when one needs more.
_SIGNAL_RECORDS = OrderedDict()


def _is_alpha_matrix(alphas):
    return isinstance(alphas, np.ndarray) and alphas.ndim in (2, 3)


def _alpha_key_token(alphas):
    """Hashable cache token for `alphas` (tuple of scalars, 1D/2D/3D ndarray, or None)."""
    if alphas is None:
        return None
    if isinstance(alphas, np.ndarray):
        return ("arr", alphas.shape, hashlib.sha1(np.ascontiguousarray(alphas).tobytes()).digest())
    return alphas


def _select_template_alphas(template_alphas, bands):
    """Align `(src_bands, alphas)` or `(nt, nb)` / `(2, nt, nb)` matrix onto `bands`, or `None`."""
    if template_alphas is None:
        return None
    if isinstance(template_alphas, tuple) and len(template_alphas) == 2:
        src_bands, mat = template_alphas
        idx_map = {int(b): j for j, b in enumerate(src_bands)}
        if not all(int(b) in idx_map for b in bands):
            return None
        cols = [idx_map[int(b)] for b in bands]
        return np.ascontiguousarray(mat[..., cols], dtype=np.float32)
    if _is_alpha_matrix(template_alphas) and template_alphas.shape[-1] == len(bands):
        return np.ascontiguousarray(template_alphas, dtype=np.float32)
    return None


def _combine_tier0_alphas(base_mat, bands, b0, sp, scalar_alpha):
    """Combine per-template `base_mat` (or None) with Tier-0 cluster retention on band `b0`."""
    if base_mat is None:
        return tuple(scalar_alpha if b == b0 else 1.0 for b in bands)
    out = np.array(base_mat, dtype=np.float32, copy=True)
    col = bands.index(b0)
    m_al = getattr(sp, "member_alphas", None)
    if isinstance(m_al, np.ndarray) and m_al.shape == (out.shape[-2],):
        out[..., col] *= m_al.astype(np.float32)
    else:
        out[..., col] *= np.float32(scalar_alpha)
    return out


def signal_draws(power, n, bands, snr, ndet, seed=_SEED, window=None, lags_too=False,
                 alphas=None, _exact=False):
    """Joint draws of every band's coarse window maximum and the fine window maximum under a
    signal of strength snr arriving at a uniformly random time in the window.

    Returns (C, F), both (M, len(bands)) float32: C[:, i] band i's largest coarse statistic
    over the coarse lags the engine searches for `window` (None: the whole block); F every
    column the largest fine statistic over the window's lags (a broadcast view: every chain
    conditions on the same fine maximum). The rows hold exactly `ndet` detections, draws
    whose fine window maximum reaches snr (kept_draws: only they can be kept), the last row
    the ndet-th, and before them the few draws that reach snr elsewhere in the block only.
    The simulation runs until it has them, however few of its draws a large snr keeps.

    One simulation, exact for stationary Gaussian noise: per draw a block's n bins with
    variance p_k, the fine statistic their n-point transform and band b's the b-point
    transform of bins [0, b), normalised to unit per-component variance -- the filter's own
    sharing of noise between the tiers and the fine stage -- plus the signal through the
    transforms' linearity (its response at every lag), arriving on a sample or 1/_NF of one
    apart. The maxima are over the whole window, as the engine's are: no neighbourhood around
    the signal, no pairing with noise elsewhere in the block (_simulate).

    Each draw holds its statistics' running-maximum records outward from the signal, so any
    window around it is two lookups: draw r's signal lies a_r + frac samples into the window,
    a_r uniform, and the window starts where the engine's would relative to the coarse grids
    (a_r = (t_r - w0) mod R_max + m R_max, m uniform; a draw whose a_r falls past the span
    is dropped, which keeps a_r exactly uniform).

    With lags_too, returns ((C, F), (fine_at, coarse_at)): where each draw's fine maximum and
    each band's coarse maximum lie, as block lags (coarse lags times the band's step), as the
    engine's direct refine compares them (hmf.c refine_direct_pair)."""
    p = _norm_profile(power, n)
    if alphas is None:
        bands = sorted(int(b) for b in bands)
        al = None
    elif _is_alpha_matrix(alphas):
        order = np.argsort([int(b) for b in bands], kind="stable")
        bands = [int(bands[i]) for i in order]
        al = np.ascontiguousarray(np.round(alphas[..., order], 4), dtype=np.float32)
    else:
        ba = sorted((int(b), float(a)) for b, a in zip(bands, alphas))
        bands = [b for b, _ in ba]
        al_raw = tuple(round(max(0.0, min(1.0, a)), 6) for _, a in ba)
        al = al_raw if any(a < 1.0 for a in al_raw) else None
    k0s = tuple(band_offset(p, n, b) for b in bands)
    Fb = np.array([p[slice(*_band_slice(n, b, k0))].sum() for b, k0 in zip(bands, k0s)])
    if np.any(Fb <= 0):
        return None          # a band holding no power cannot gate; callers drop such bands (usable_bands)
    lags = _engine_lags(n, bands, window)
    ndet = int(ndet)
    al_tok = _alpha_key_token(al)
    extra = (k0s, al_tok) if al_tok is not None else ((k0s,) if any(k0s) else ())
    if _exact:
        extra = extra + ("exact",)
    key = _key(p, n, bands, float(snr), ndet, int(seed), lags, _NF, *extra)
    hit = _SIGNAL_CACHE.get(key)
    if hit is not None:
        _SIGNAL_CACHE.move_to_end(key)
        return hit[0] if not lags_too else hit
    sr_kw = {}
    if any(k0s):
        sr_kw["k0s"] = k0s
    if al is not None:
        sr_kw["alphas"] = al
    if _exact:
        sr_kw["_exact"] = True
    sim = _signal_records(p, n, bands, Fb, float(snr), ndet, int(seed), **sr_kw)
    skey = ("sim", id(sim), n, tuple(bands), float(snr), ndet, int(seed), lags, _NF, *extra)
    shit = _SIGNAL_CACHE.get(skey)
    if shit is not None and shit[0] is sim:
        _SIGNAL_CACHE.move_to_end(skey)
        hit = shit[1]
        _cache_put(_SIGNAL_CACHE, key, hit)
        return hit[0] if not lags_too else hit
    while True:
        C, F, at = _signal_window(sim, n, bands, lags)
        det = np.flatnonzero(F >= snr)
        if det.size >= ndet:
            break
        # the window misses some of the block's detections: more, in proportion
        kept = sim["t"].size
        sim = _signal_records(p, n, bands, Fb, float(snr),
                              kept + int(math.ceil((ndet - det.size) * kept / max(det.size, 1))) + 1,
                              int(seed), **sr_kw)
    end = int(det[ndet - 1]) + 1 if ndet > 0 else 0
    C, F, at = C[:end], F[:end], (at[0][:end], at[1][:end])
    hit = ((C, np.broadcast_to(F[:, None], C.shape)), at)
    _cache_put(_SIGNAL_CACHE, skey, (sim, hit))
    _cache_put(_SIGNAL_CACHE, key, hit)
    return hit[0] if not lags_too else hit


def _arrivals(seed, R, row0, rows):
    """(t, u) of the signal simulation's rows row0 .. row0 + rows: t its integer arrival,
    uniform in [0, R), and u uniform in [0, 1), each row's from the block of _ARRIVAL_ROWS
    holding it (its own generator)."""
    ts, us = [], []
    for blk in range(row0 // _ARRIVAL_ROWS, (row0 + rows - 1) // _ARRIVAL_ROWS + 1):
        rng = np.random.default_rng([int(seed), _DOMAIN_SIGNAL, blk])
        ts.append(rng.integers(0, R, _ARRIVAL_ROWS))
        us.append(rng.random(_ARRIVAL_ROWS))
    s = row0 % _ARRIVAL_ROWS
    return (np.concatenate(ts)[s:s + rows].astype(np.int64), np.concatenate(us)[s:s + rows])


def _prefix_record(rec, m_rows):
    pos, val, off = rec
    if off.size - 1 == m_rows:
        return rec
    return pos[:off[m_rows]], val[:off[m_rows]], off[:m_rows + 1]


def _signal_records(p, n, bands, Fb, snr, kept, seed, k0s=None, alphas=None, _exact=False):
    """signal_draws' simulation, with at least `kept` draws kept: a dict holding the profile
    it simulates and, per kept draw, the signal's integer arrival t in [0, R_max), a uniform u
    in [0, 1) placing it in a window, and per statistic (fine, then each band) and side
    (right, left) the records (pos, val, off) of its running maximum outward from the signal.
    Extended in place when a request needs more kept draws: a row's draws depend only on its
    row, so the draws are those of one simulation run at once."""
    k0s = (0,) * len(bands) if k0s is None else tuple(int(x) for x in k0s)
    if _is_alpha_matrix(alphas):
        al = np.ascontiguousarray(alphas, dtype=np.float32)
        sub_idx = []
    else:
        al = tuple(float(a) for a in alphas) if (alphas is not None and any(a < 1.0 for a in alphas)) else None
        sub_idx = [i for i, a in enumerate(al) if a < 1.0] if al is not None else []
    use_base = 0 < len(sub_idx) < len(bands)
    al_tok = _alpha_key_token(al)
    extra = (k0s, al_tok) if al_tok is not None else ((k0s,) if any(k0s) else ())
    key = _key(p, n, bands, snr, seed, _NF, *extra)
    sim = _SIGNAL_RECORDS.get(key)
    if sim is not None:
        _SIGNAL_RECORDS.move_to_end(key)
    else:
        # profiles alike in the gates' response share a simulation (_similar_get), whatever
        # window each searches: a job's banks have nearly one reference profile. It is
        # extended with its own profile, so it stays one simulation.
        params = (n, tuple(bands), snr, seed, _NF) + extra
        unit, sim = (None, None) if _exact else _similar_get("signal-records", p, params)
        if sim is None:
            if use_base:
                base0 = _signal_records(p, n, bands, Fb, snr, kept, seed, k0s=k0s, alphas=None,
                                        _exact=_exact)
                p_sim, Fb_sim = base0["p"], base0["Fb"]
            else:
                p_sim, Fb_sim = p, Fb
            sim = dict(p=p_sim, Fb=Fb_sim, k0s=k0s, alphas=al, rows=0,
                       t=np.empty(0, np.int64), u=np.empty(0),
                       keep_mask=np.empty(0, np.uint8), recs=None, sub_recs=None, tab=None)
            if unit is None:
                unit = ((p_sim / np.linalg.norm(p_sim)).astype(np.float32), _gate_features(p_sim, n))
            _similar_put("signal-records", unit, params, sim, keep=_RECORDS_MAX)
        _SIGNAL_RECORDS[key] = sim
        while len(_SIGNAL_RECORDS) > _RECORDS_MAX:
            _SIGNAL_RECORDS.popitem(last=False)
    if sim["t"].size < kept:
        _extend_signal(sim, n, bands, snr, kept, seed, k0s=k0s, alphas=al)
    return sim


def _extend_signal(sim, n, bands, snr, kept, seed, k0s=None, alphas=None):
    """Simulate further rows of `sim` until it holds `kept` kept draws."""
    p, Fb = sim["p"], sim["Fb"]
    if k0s is None:
        k0s = sim.get("k0s") or ((0,) * len(bands))
    else:
        k0s = tuple(int(x) for x in k0s)
    if alphas is None:
        alphas = sim.get("alphas")
    is_mat = _is_alpha_matrix(alphas)
    sub_idx = [] if (alphas is None or is_mat) else [i for i, a in enumerate(alphas) if a < 1.0]
    if 0 < len(sub_idx) < len(bands):
        base = _signal_records(p, n, bands, Fb, snr, kept, seed, k0s=k0s, alphas=None, _exact=True)
        target_rows = base["rows"]
        have_rows = sim["rows"]
        if have_rows < target_rows:
            sub_bands = [bands[i] for i in sub_idx]
            sub_k0s = tuple(k0s[i] for i in sub_idx)
            sub_al = tuple(alphas[i] for i in sub_idx)
            if sim["tab"] is None:
                sub_tab = np.zeros((_NF, 1 + len(sub_idx), n), np.complex64)
                for j, i in enumerate(sub_idx):
                    sub_tab[:, 1 + j] = base["tab"][:, 1 + i] * np.float32(alphas[i])
                sim["tab"] = sub_tab
            km_all = base["keep_mask"][:target_rows]
            n_kept_all = int(km_all.sum())
            t_all = np.zeros(target_rows, np.int64)
            t_all[km_all.astype(bool)] = base["t"][:n_kept_all]
            sub_nkey = _key(p, n, sub_bands, seed, sub_k0s, sub_al)
            sub_parts = [] if sim.get("sub_recs") is None else [sim["sub_recs"]]
            cur = have_rows
            while cur < target_rows:
                held = _NOISE_RECORDS.get(sub_nkey)
                noise_flag = (held[0] if held is not None else 0) == cur < _NOISE_BLOCKS
                end_r = min(target_rows, _NOISE_BLOCKS) if noise_flag else target_rows
                step = end_r - cur
                t_step = np.ascontiguousarray(t_all[cur:end_r])
                km_step = np.ascontiguousarray(km_all[cur:end_r])
                fi_step = ((cur + np.arange(step)) % _NF).astype(np.int32)
                srecs, nrec = _simulate(p, n, sub_bands, step, cur, seed,
                                        (sim["tab"], t_step, fi_step), noise_flag,
                                        keep_at=snr, k0s=sub_k0s, alphas=sub_al,
                                        kept_mask=km_step)
                if nrec is not None:
                    _add_noise_records(sub_nkey, cur, step, nrec)
                keep_b = km_step.astype(bool)
                sub_parts.append(tuple(_rows(r, keep_b) for r in srecs[2:]))
                cur = end_r
            sub_joined = tuple(_join_records([pt[q] for pt in sub_parts])
                               for q in range(2 * len(sub_idx)))
            sim["sub_recs"] = sub_joined
            merged = [_prefix_record(r, n_kept_all) for r in base["recs"]]
            for j, i in enumerate(sub_idx):
                merged[2 + 2 * i] = sub_joined[2 * j]
                merged[3 + 2 * i] = sub_joined[2 * j + 1]
            sim["recs"] = tuple(merged)
            sim["t"] = base["t"][:n_kept_all]
            sim["u"] = base["u"][:n_kept_all]
            sim["keep_mask"] = km_all
            sim["rows"] = target_rows
        return
    if sim["tab"] is None:
        k = np.arange(n)
        # the signal's response, per arrival fraction, for the fine statistic then each band
        # (active bins [k0, khi), normalised as the band is): a band of b lags R apart at
        # [rho b + e] holds it at its lag e after the one rho samples before the signal,
        # d = e R - rho samples after it
        j = np.arange(_NF)[:, None]
        q = p[None, :] * np.exp((-2j * np.pi / (_NF * n)) * j * k[None, :])
        tab = np.empty((_NF, 1 + len(bands), n), np.complex64)
        tab[:, 0] = np.fft.ifft(q, axis=1) * (n * snr)
        qm = np.zeros_like(q)
        prev_lo, prev_hi = 0, 0
        for s, (m, f, k0) in enumerate(zip(bands, Fb, k0s), 1):
            k_lo, k_hi = _band_slice(n, m, k0)
            if k_lo == prev_lo and k_hi >= prev_hi:
                qm[:, prev_hi:k_hi] = q[:, prev_hi:k_hi]
            else:
                qm.fill(0)
                qm[:, k_lo:k_hi] = q[:, k_lo:k_hi]
            prev_lo, prev_hi = k_lo, k_hi
            scale_s = n * snr / np.sqrt(f)
            if alphas is not None and not is_mat and alphas[s - 1] < 1.0:
                scale_s *= float(alphas[s - 1])
            resp = np.fft.ifft(qm, axis=1) * scale_s
            R = n // m
            d = (np.arange(m)[None, :] * R - np.arange(R)[:, None]).reshape(-1) % n
            tab[:, s] = resp[:, d]
        sim["tab"] = tab
    # Draws whose fine statistic stays below snr at every lag cannot be kept by any window and
    # hold no records. About 0.6 are kept at a usual snr, far fewer at a large one, where only
    # signals arriving close to a sample reach snr (about 3% at snr = 1000): each step runs the
    # rows the kept share so far says are still needed (the first assumes all are kept), and
    # three standard deviations of their count more, so that a third step is rare; what it
    # overshoots stays for a later request. The model's noise blocks (_NOISE_BLOCKS) are the
    # first rows' noise alone, recorded as they run (a third of a row's work): later rows'
    # are left to noise_block_maxima, which simulates them should a request read that far.
    al_tok = _alpha_key_token(alphas)
    extra = (k0s, al_tok) if al_tok is not None else ((k0s,) if any(k0s) else ())
    nkey = _key(p, n, bands, seed, *extra)
    km_cur = sim.get("keep_mask")
    kms = [np.empty(0, np.uint8) if km_cur is None else km_cur]
    ts, us, parts = [sim["t"]], [sim["u"]], [] if sim["recs"] is None else [sim["recs"]]
    rows, have = sim["rows"], sim["t"].size
    while have < kept:
        need = kept - have
        step = need if not rows else int(math.ceil((need + 3 * math.sqrt(need)) * rows / max(have, 1)))
        held = _NOISE_RECORDS.get(nkey)
        noise = (held[0] if held is not None else 0) == rows < _NOISE_BLOCKS
        if noise:
            step = min(step, _NOISE_BLOCKS - rows)
        t, u = _arrivals(seed, n // bands[0], rows, step)
        fi = ((rows + np.arange(step)) % _NF).astype(np.int32)
        recs, nrec = _simulate(p, n, bands, step, rows, seed, (sim["tab"], t, fi), noise,
                               keep_at=snr, k0s=k0s, alphas=alphas)
        if nrec is not None:
            _add_noise_records(nkey, rows, step, nrec)
        keep = np.diff(recs[0][2]) > 0          # a kept draw's fine maximum has a record
        kms.append(keep.astype(np.uint8))
        ts.append(t[keep]); us.append(u[keep])
        parts.append(tuple(_rows(r, keep) for r in recs))
        rows += step
        have += int(keep.sum())
    sim["keep_mask"] = np.concatenate(kms)
    sim["t"], sim["u"] = np.concatenate(ts), np.concatenate(us)
    sim["recs"] = tuple(_join_records([pt[q] for pt in parts]) for q in range(len(parts[0])))
    sim["rows"] = rows


def _last_within(rec, reach):
    """Per row of records (pos, val, off): the value of its last record at distance <= reach[r]
    (records rise with distance) and that distance, 0 and -1 where none is
    (_core.records_within)."""
    from . import _core
    pos, val, off = rec
    out = np.empty(off.size - 1, np.float32)
    at = np.empty(off.size - 1, np.int32)
    _core.records_within(pos, val, off, np.ascontiguousarray(reach, np.int64), out, at)
    return out, at


def _both_sides(right, left, reach_right, reach_left):
    """The larger of a statistic's two sides' maxima within their reach, and its lag relative
    to the signal's (positive to the right), in the statistic's own lags."""
    vr, er = _last_within(right, reach_right)
    vl, el = _last_within(left, reach_left)
    take_r = vr >= vl
    return np.where(take_r, vr, vl), np.where(take_r, er, -el).astype(np.int64)


def _signal_window(sim, n, bands, lags):
    """(C, F, at) of signal_draws for the engine's lags `lags` (_engine_lags) from the
    simulation `sim` (_signal_records): at = (fine lag, coarse lags per band) of each maximum,
    as block lags (a coarse lag times its band's step; a statistic searched over the whole
    block wraps into it)."""
    t, u, recs = sim["t"], sim["u"], sim["recs"]
    w0, w1, c0, c1 = lags
    span, step = w1 - w0, n // bands[0]
    # the window starts w0 (mod step) before the signal's grid, so its coarse lags are the
    # engine's moved by whole coarse steps
    a = (t - w0) % step + np.floor(u * -(-span // step)).astype(np.int64) * step
    ok = a < span
    t, a = t[ok], a[ok]
    shift = t - a - w0                       # a multiple of every band's step
    whole = span >= n
    F, fat = _both_sides(_rows(recs[0], ok), _rows(recs[1], ok),
                         np.full(t.size, n - 1) if whole else span - 1 - a,
                         np.zeros(t.size, np.int64) if whole else a)
    C = np.empty((t.size, len(bands)), np.float32)
    cat = np.empty((t.size, len(bands)), np.int64)
    for i, b in enumerate(bands):
        R = n // b
        js = t // R
        if c1[i] - c0[i] >= b:
            right, left = np.full(t.size, b - 1), np.zeros(t.size, np.int64)
        else:
            right, left = c1[i] + shift // R - 1 - js, js - (c0[i] + shift // R)
        C[:, i], e = _both_sides(_rows(recs[2 + 2 * i], ok), _rows(recs[3 + 2 * i], ok), right, left)
        # (js + e) R - t samples after the signal, which lies w0 + a into the block
        cat[:, i] = (js + e) * R - t + w0 + a
        if c1[i] - c0[i] >= b:
            cat[:, i] %= n
    fat = fat + w0 + a
    if whole:
        fat %= n
    for x in (C, F, fat, cat):
        x.setflags(write=False)
    return C, F, (fat, cat)


def _rows(rec, keep):
    """The records (pos, val, off) of the rows `keep` (bool) selects."""
    if keep.all():
        return rec
    pos, val, off = rec
    cnt = np.diff(off)[keep]
    tot = int(cnt.sum())
    if off[0] == 0 and tot == int(off[-1]):
        # Unkept rows hold no records (_extend_signal): pos and val are already contiguous.
        return pos[:tot], val[:tot], np.concatenate(([0], np.cumsum(cnt)))
    starts = off[:-1][keep]
    idx = np.repeat(starts - np.concatenate(([0], np.cumsum(cnt)[:-1])), cnt) + np.arange(tot)
    return pos[idx], val[idx], np.concatenate(([0], np.cumsum(cnt)))


#: The noise simulation's running-maximum records per (profile, n, bands, nsim, seed): every
#: window's block maxima come from them (noise_block_maxima), so the windows of a profile's
#: template groups share one simulation. ~6 MB each at n = 4096.
_NOISE_RECORDS = OrderedDict()
_RECORDS_MAX = 32
#: Records a row the simulation's first call has room for, in units of ln L + 3 for a running
#: maximum over L lags (_simulate); every later call's room is measured.
_ROOM = 2.0
#: Rows the simulation's first call runs (_simulate): enough to measure each statistic's records
#: a row to a few percent, few enough that room for twice the usual is a few MB.
_PILOT = 2048
#: Standard errors past the measured records a row that a call has room for (_simulate).
_ROOM_Z = 4.0


def _grown(a, keep, size):
    """A new array of `size` elements of a's type holding a's first `keep`."""
    out = np.empty(size, a.dtype)
    out[:keep] = a[:keep]
    return out


def _simulate(p, n, bands, rows, row0, seed, signal=None, noise=True, keep_at=0.0, k0s=None,
              alphas=None, kept_mask=None):
    """Rows row0 .. row0 + rows of the gate model's one simulation (_core.simulate): with
    signal = (tab, t, fi) its records outward from the signal (none for a draw whose fine
    statistic is below keep_at at every lag), and with noise each band's records of the noise
    alone. A block's draws depend only on its row, so its noise alone is the same whichever
    call simulates it. Returns (signal records or None, noise records or None): per statistic
    and side (fine first, right then left), and per band, the records (pos, val, off); pos and
    val may be views of arrays a few percent longer."""
    from . import _core
    k0s = (0,) * len(bands) if k0s is None else tuple(int(x) for x in k0s)
    if _is_alpha_matrix(alphas):
        al_arg = np.ascontiguousarray(alphas, dtype=np.float32)
    else:
        al_arg = (tuple(float(a) for a in alphas)
                  if (alphas is not None and any(float(a) < 1.0 for a in alphas)) else None)
    if kept_mask is None:
        if al_arg is not None:
            sim_extra = (k0s, al_arg)
        else:
            sim_extra = (k0s,) if any(k0s) else ()
    else:
        sim_extra = None
    scale = (np.sqrt(p) / np.sqrt(2)).astype(np.float32)
    kmax = int(np.flatnonzero(p)[-1]) + 1
    bscale = tuple(float(_SIG / np.sqrt(p[slice(*_band_slice(n, b, k0))].sum()))
                   for b, k0 in zip(bands, k0s))
    stream = (_DOMAIN_SIGNAL << 32) | (int(seed) & 0xFFFFFFFF)
    tab, t, fi = signal if signal is not None else (None,) * 3
    # Room: a side's running maximum over L lags has about ln L + 0.58 records of white noise,
    # far fewer with the signal at its start (and none in a draw not kept), more where the
    # profile makes neighbouring lags alike (the widest band's noise up to ~1.1 (ln L + 3)), so
    # the records a row are measured, not guessed. The first call runs _PILOT rows with room for
    # _ROOM (ln L + 3) a row; each later one, the rest, with room for the mean records a row so
    # far and _ROOM_Z standard errors of the total (the mean's error over the rows to come and
    # their own spread). A call that runs out stops at the row that did not fit, and the next
    # continues from there; one that fits no row at all doubles its successor's room. Each
    # statistic's records go into one array, grown (its records so far copied) only when a call
    # needs more room than is left.
    ns = 2 * (1 + len(bands)) if signal is not None else 0
    if signal is None:
        first = []
    elif kept_mask is not None:
        first = [0.0, 0.0] + [math.log(m) + 3 for m in bands for _ in (0, 1)]
    else:
        first = [math.log(m) + 3 for m in [n] + list(bands) for _ in (0, 1)]
    first = [_ROOM * c for c in first + ([math.log(b) + 3 for b in bands] if noise else [])]
    nq = len(first)
    off = [np.empty(rows + 1, np.int64) for _ in range(nq)]
    pos = [np.empty(0, np.int32) for _ in range(nq)]
    val = [np.empty(0, np.float32) for _ in range(nq)]
    have = [0] * nq                         # each statistic's records so far
    done, boost = 0, 1
    while done < rows:
        todo = rows - done if done else min(rows, _PILOT)
        if done:
            need = []
            for o in off:
                c = np.diff(o[:done + 1])
                spread = float(c.std()) * math.sqrt(todo * todo / done + todo)
                need.append(todo * float(c.mean()) + _ROOM_Z * spread)
        else:
            need = [c * todo for c in first]
        for q in range(nq):
            want = have[q] + int(math.ceil(boost * need[q])) + 64
            if pos[q].size < want:
                pos[q], val[q] = _grown(pos[q], have[q], want), _grown(val[q], have[q], want)
        # the call writes from the start of its arrays: records after those so far, offsets
        # from its first row on, made absolute below
        cp = [pos[q][have[q]:] for q in range(nq)]
        cv = [val[q][have[q]:] for q in range(nq)]
        co = [off[q][done:done + todo + 1] for q in range(nq)]
        sig = [tuple(x[:ns]) if signal is not None else None for x in (cp, cv, co)]
        noi = [tuple(x[ns:]) if noise else None for x in (cp, cv, co)]
        tail = (sim_extra if kept_mask is None
                else (k0s if any(k0s) else None, al_arg, kept_mask[done:done + todo]))
        sk, nk, got = _core.simulate(scale, stream, int(row0 + done), int(todo), kmax,
                                     tuple(int(b) for b in bands), bscale, float(_SIG), tab,
                                     None if t is None else t[done:done + todo],
                                     None if fi is None else fi[done:done + todo],
                                     *sig, *noi, float(keep_at), *tail)
        counts = list(sk or ()) + list(nk or ())
        for q in range(nq):
            co[q][:got + 1] += have[q]
            have[q] += counts[q]
        boost = 2 * boost if got == 0 else 1
        done += got
    recs = [(pos[q][:have[q]], val[q][:have[q]], off[q]) for q in range(nq)]
    return (tuple(recs[:ns]) if signal is not None else None,
            tuple(recs[ns:]) if noise else None)


def _join_records(parts):
    """One records array (pos, val, off) of consecutive row ranges' records, in order."""
    if len(parts) == 1:
        return parts[0]
    pos = np.concatenate([p for p, _, _ in parts])
    val = np.concatenate([v for _, v, _ in parts])
    offs, base = [np.zeros(1, np.int64)], 0
    for _, _, o in parts:
        offs.append(o[1:] + base)
        base += o[-1]
    return pos, val, np.concatenate(offs)


def _add_noise_records(key, row0, rows, recs):
    """Hold the noise records `recs` of rows row0 .. row0 + rows after those held for rows
    0 .. row0 (a simulation's blocks in order; anything else is left as held)."""
    held = _NOISE_RECORDS.get(key)
    have = 0 if held is None else held[0]
    if have != row0:
        return
    if held is not None:
        recs = tuple(_join_records([h, r]) for h, r in zip(held[1], recs))
    _NOISE_RECORDS[key] = (row0 + rows, recs)
    _NOISE_RECORDS.move_to_end(key)
    while len(_NOISE_RECORDS) > _RECORDS_MAX:
        _NOISE_RECORDS.popitem(last=False)


def _noise_records(p, n, bands, nsim, seed, k0s=None, alphas=None):
    """Per band, the records (pos int32, val float32, off int64) of each simulated block's
    running maximum of the band's normalised coarse statistic of the noise alone over its b
    lags, rows in order: row r's records are [off[r], off[r + 1]).

    The blocks are signal_draws' (_simulate), so a simulation of fewer blocks is a prefix of
    one of more: a request reads the prefix of a larger simulation held (a signal
    simulation's included), or extends a smaller one."""
    if k0s is None:
        k0s = tuple(band_offset(p, n, b) for b in bands)
    else:
        k0s = tuple(int(x) for x in k0s)
    if _is_alpha_matrix(alphas):
        al = np.ascontiguousarray(alphas, dtype=np.float32)
        sub_idx = []
    else:
        al = tuple(float(a) for a in alphas) if (alphas is not None and any(a < 1.0 for a in alphas)) else None
        sub_idx = [i for i, a in enumerate(al) if a < 1.0] if al is not None else []
    al_tok = _alpha_key_token(al)
    extra = (k0s, al_tok) if al_tok is not None else ((k0s,) if any(k0s) else ())
    key = _key(p, n, bands, seed, *extra)
    hit = _NOISE_RECORDS.get(key)
    if hit is not None:
        _NOISE_RECORDS.move_to_end(key)
        have, recs = hit
        if nsim <= have:
            return tuple((pos[:off[nsim]], val[:off[nsim]], off[:nsim + 1]) for pos, val, off in recs)
    else:
        have, recs = 0, None
    if 0 < len(sub_idx) < len(bands):
        base_recs = _noise_records(p, n, bands, nsim, seed, k0s=k0s, alphas=None)
        sub_bands = [bands[i] for i in sub_idx]
        sub_k0s = tuple(k0s[i] for i in sub_idx)
        sub_al = tuple(al[i] for i in sub_idx)
        sub_recs = _noise_records(p, n, sub_bands, nsim, seed, k0s=sub_k0s, alphas=sub_al)
        merged = [_prefix_record(r, nsim) for r in base_recs]
        for j, i in enumerate(sub_idx):
            merged[i] = _prefix_record(sub_recs[j], nsim)
        merged_t = tuple(merged)
        _NOISE_RECORDS[key] = (nsim, merged_t)
        _NOISE_RECORDS.move_to_end(key)
        while len(_NOISE_RECORDS) > _RECORDS_MAX:
            _NOISE_RECORDS.popitem(last=False)
        return merged_t
    _, new = _simulate(p, n, bands, nsim - have, have, seed, k0s=k0s, alphas=al)
    _add_noise_records(key, have, nsim - have, new)
    return _NOISE_RECORDS[key][1]


def noise_block_maxima(power, n, bands, nsim=_NOISE_BLOCKS, seed=_SEED, window=None,
                       alphas=None, lag_pads=None, _exact=False):
    """Noise-only block maxima of every band's coarse statistic, (nsim, len(bands)).

    Exact for stationary Gaussian noise with output profile `power`: bins are
    independent with variance p_k; band b's coarse grid is the b-point inverse
    transform of its active band [k0, khi) wrapped to cyclic slots, normalised
    to unit per-component variance.
    `window` = (start, end) in samples is the lag range each block's search
    covers; every tier takes its maximum over the coarse lags the engine
    visits for it (hmf.c: cstart = start/R - 1, cend = ceil(end/R)), so a
    chain's noise passes are joint passes of whole-window maxima.
    """
    p = _norm_profile(power, n)
    if alphas is None and lag_pads is None:
        bands = sorted(int(b) for b in bands)
        al = None
        lps = (0,) * len(bands)
    elif _is_alpha_matrix(alphas):
        lp_in = (0,) * len(bands) if lag_pads is None else lag_pads
        order = np.argsort([int(b) for b in bands], kind="stable")
        bands = [int(bands[i]) for i in order]
        al = np.ascontiguousarray(np.round(alphas[..., order], 4), dtype=np.float32)
        lps = tuple(max(0, int(lp_in[i])) for i in order)
    else:
        al_in = (1.0,) * len(bands) if alphas is None else alphas
        lp_in = (0,) * len(bands) if lag_pads is None else lag_pads
        bal = sorted((int(b), float(a), int(lp)) for b, a, lp in zip(bands, al_in, lp_in))
        bands = [b for b, _, _ in bal]
        al_raw = tuple(round(max(0.0, min(1.0, a)), 6) for _, a, _ in bal)
        al = al_raw if any(a < 1.0 for a in al_raw) else None
        lps = tuple(max(0, lp) for _, _, lp in bal)
    k0s = tuple(band_offset(p, n, b) for b in bands)
    al_tok = _alpha_key_token(al)
    extra = (k0s, al_tok) if al_tok is not None else ((k0s,) if any(k0s) else ())
    if _exact:
        extra = extra + ("exact",)
    win = (0, n) if window is None else (int(window[0]), int(window[1]))
    # Each band's coarse statistic is circularly stationary over its lags (independent
    # bins), so a window's maximum depends only on how many lags it covers, not where:
    # simulate lags [0, count) per band, and windows of equal span share one simulation.
    counts = tuple(int(c1 - c0) for c0, c1 in (
        _coarse_lags_padded(n, b, win[0], win[1], lp) for b, lp in zip(bands, lps)
    ))
    key = _key(p, n, bands, int(nsim), int(seed), counts, *extra)
    hit = _NOISE_CACHE.get(key)
    if hit is not None:
        _NOISE_CACHE.move_to_end(key)
        return hit
    sim_params = (n, tuple(bands), int(nsim), int(seed), counts) + extra
    unit, hit = (None, None) if _exact else _similar_get("noise", p, sim_params)
    if hit is not None:
        _cache_put(_NOISE_CACHE, key, hit)
        return hit
    nr_kw = {}
    if any(k0s):
        nr_kw["k0s"] = k0s
    if al is not None:
        nr_kw["alphas"] = al
    recs = _noise_records(p, n, bands, int(nsim), int(seed), **nr_kw)
    out = np.empty((nsim, len(bands)), np.float32)
    for i, (pos, val, off) in enumerate(recs):
        # row r's maximum over lags [0, c) is its last record below c (records rise in lag)
        below = np.cumsum(pos < counts[i])
        last = below[off[1:] - 1] - np.concatenate(([0], below[off[1:-1] - 1]))
        out[:, i] = val[off[:-1] + last - 1]
    _cache_put(_NOISE_CACHE, key, out)
    if unit is None:
        unit = ((p / np.linalg.norm(p)).astype(np.float32), _gate_features(p, n))
    _similar_put("noise", unit, sim_params, out)
    return out


#: CostModel's interpolation tables as arrays, per table (a model's rows do not change once
#: made): every chain priced asked np.log of the same few rows again, 117k times a job.
_LOG_TABLES = {}


def _log_table(rows, kind):
    """(log densities, values) of a CostModel table of (density, value) rows: the values as
    given ("cost") or log of their ratio to the density ("ratio"), the tuples the
    interpolations read."""
    hit = _LOG_TABLES.get((id(rows), kind))
    if hit is not None and hit[0] is rows:
        return hit[1], hit[2]
    fs = tuple(math.log(r[0]) for r in rows)
    if kind == "cost":
        vs = tuple(float(r[1]) for r in rows)
    else:
        vs = tuple(math.log(r[1] / r[0]) for r in rows)
    _LOG_TABLES[(id(rows), kind)] = (rows, fs, vs)     # rows held: the id cannot be reused
    if len(_LOG_TABLES) > 4096:
        _LOG_TABLES.pop(next(iter(_LOG_TABLES)))
    return fs, vs


def _interp_clamped(x, fs, vs):
    """Clamped piecewise-linear interpolation on small sorted tuples (fs, vs), matching np.interp."""
    if x <= fs[0]:
        return vs[0]
    if x >= fs[-1]:
        return vs[-1]
    j = 0
    last = len(fs) - 2
    while j < last and fs[j + 1] <= x:
        j += 1
    dx = fs[j + 1] - fs[j]
    if dx == 0.0:
        return vs[j + 1]
    dy = vs[j + 1] - vs[j]
    if dy == 0.0:
        return vs[j]
    return (x - fs[j]) * (dy / dx) + vs[j]


def band_forward_wanted(n, band, f, forced=None):
    """Whether a hierarchical call should forward only its tiers' bands (and then recompute
    the full spectra of the blocks its refine reads) rather than every block in full.
    Chosen from bytes: per block the full forward writes n samples and the band forward
    `band` (the widest band a tier reads), while the recompute reads and writes n for each
    block with a refined pair, so bands move fewer bytes iff that fraction f < (n - band) / 2n.
    f is the gate model's fraction for the call (_gpuhier._hier_peaks: from the chain's
    modelled refine probability), so the choice depends on the call alone; with none
    (thresholds set by hand, no reference), the bands. MF_BAND_FORWARD=0/1 forces it off or on,
    as does `forced` (a context's feed_forced: the GPU calibration times both feeds); the cost
    model prices a chain's feed by this same rule (CostModel.feed_delta)."""
    from . import _config
    if forced is None:
        forced = _config.get("MF_BAND_FORWARD")
    if forced is False or n > 65536 or band >= n:
        return False
    if forced:
        return True
    return f is None or f < (n - band) / (2.0 * n)


class CostModel:
    """Per-tier costs for one transform size, in engine ticks.

    dense[b]          first tier at band b, per pair
    sparse[b]         [(density, ticks per survivor)] for a later tier at band b
    refine            [(density, ticks per refined pair)]
    screen[b]         Q15 screen as the first tier at band b (q15-inl.h), when the back
                      end has one: {"dense": ticks per pair screened,
                      "excess": [(float density, screen density)], "recheck": ticks per
                      pair it passes beyond the screen itself (compaction)}
    """

    def __init__(self, n, dense, sparse, refine, block=0.0, screen=None, feed=None):
        self.n = int(n)
        # feed: a GPU backend's per-block change from the feed `block` was measured with (the
        # band forward of the first tier's band), {"band": {B: change at widest band B},
        # "full": change with the full forward}, measured (calibrate_costs_gpu); None where
        # there is one feed (the CPU). A call takes the band forward or the full one by the
        # backend's own rule (band_forward_wanted), and so does the model
        # (feed_delta).
        self.feed = None if not feed else {
            "band": {int(b): float(v) for b, v in feed["band"].items()},
            "full": float(feed["full"])}
        self.screen = {}
        for b, v in (screen or {}).items():
            ent = {"dense": float(v["dense"]), "recheck": float(v["recheck"]),
                   "excess": sorted((float(a), float(c)) for a, c in v["excess"])}
            if v.get("sparse"):
                ent["sparse"] = sorted((float(f), float(c)) for f, c in v["sparse"])
            self.screen[int(b)] = ent
        self.block = float(block)          # fixed work per block: forward transform, ingest
        self.dense = {int(b): float(v) for b, v in dense.items()}
        self._sparse = {int(b): sorted((float(f), float(v)) for f, v in rows) for b, rows in sparse.items()}
        self._refine = sorted((float(f), float(v)) for f, v in refine)
        self.tier0_ratios = {}

    @staticmethod
    def _interp(rows, f):
        """Cost per survivor at density f: linear in log f, clamped to the measured range."""
        fs, vs = _log_table(rows, "cost")
        return _interp_clamped(math.log(max(f, 1e-12)), fs, vs)

    def refine(self, f):
        return self._interp(self._refine, f)

    def sparse(self, b, f):
        return self._interp(self._sparse[int(b)], f)

    def sparse_for(self, b, f, screened=False):
        """Ticks per survivor at later-tier band `b` and reach `f`, using Q15 sparse pricing
        when `screened` is True and `b` has a measured Q15 sparse curve."""
        b = int(b)
        if screened:
            sc = self.screen.get(b)
            if sc is not None and sc.get("sparse"):
                return self._interp(sc["sparse"], f)
        return self._interp(self._sparse[b], f)

    def signature(self):
        """A hashable summary of the model's content, for cache keys (an object's id can be
        reused once it is collected, which would hand a new model an old model's results)."""
        sig = getattr(self, "_sig", None)
        if sig is None:
            t0r = getattr(self, "tier0_ratios", None)
            sig = (self.n, self.block, tuple(sorted(self.dense.items())),
                   tuple((b, tuple(r)) for b, r in sorted(self._sparse.items())),
                   tuple(self._refine),
                   tuple((b, v["dense"], v["recheck"], tuple(v["excess"]))
                         + ((tuple(v["sparse"]),) if "sparse" in v else ())
                         for b, v in sorted(self.screen.items())),
                   getattr(self, "direct_lag", None), getattr(self, "direct_single", True),
                   getattr(self, "direct_frac", 1.0),
                   getattr(self, "direct_base", 0.0),
                   getattr(self, "direct_multi_frac", 0.0),
                   None if self.feed is None else (tuple(sorted(self.feed["band"].items())),
                                                   self.feed["full"]))
            if t0r:
                sig = sig + (tuple(sorted(t0r.items())),)
            self._sig = sig
        return sig

    def to_dict(self):
        return {"n": self.n, "block": self.block, "dense": self.dense,
                "feed": None if self.feed is None else {
                    "band": {str(b): v for b, v in self.feed["band"].items()},
                    "full": self.feed["full"]},
                "sparse": self._sparse, "refine": self._refine, "screen": self.screen}

    @classmethod
    def from_dict(cls, d):
        return cls(d["n"], d["dense"], d["sparse"], d["refine"], block=d.get("block", 0.0),
                   screen=d.get("screen"), feed=d.get("feed"))

    def screen_reach(self, b, reach1):
        """Modelled Q15 pass fraction from measured screen/float excess."""
        sc = self.screen.get(int(b))
        if sc is None or not sc["excess"]:
            return None
        fs, ratio = _log_table(sc["excess"], "ratio")
        return min(1.0, max(reach1, 1e-6) * math.exp(
            _interp_clamped(math.log(max(reach1, 1e-6)), fs, ratio)))

    def first_tier(self, b, reach1):
        """(cost per pair, q15) of the cheaper first tier at band b, where reach1 is the float
        tier's pass rate. Screened: the screen on every pair, plus its per-pass cost beyond
        the screen, at reach1 scaled by the measured excess (about 1 now that the screen is
        the tier's gate on its own statistic; larger for a screen with a margin)."""
        c = self.dense[int(b)]
        sc = self.screen.get(int(b))
        if sc is None or not sc["excess"]:
            return c, False
        passed = self.screen_reach(b, reach1)
        cq = sc["dense"] + passed * sc["recheck"]
        # A close call takes the screen, as pick_stable takes its canonical chain within TIE:
        # calibration moves by about that much between processes, and a strict comparison
        # flipped the screen between processes under load (dev2, 2026-10-24) -- which also
        # moves where the pairs it passes are refined.
        return (cq, True) if cq <= c * (1.0 + TIE) else (c, False)

    def first_tier_for(self, chain, reach1):
        """(cost per pair, q15) of `chain`'s first tier, scaling dense Tier-0 work by centroid ratio
        when `len(chain) > 1` and `chain[0]` has a Tier-0 cluster ratio."""
        b = int(chain[0])
        t0r = getattr(self, "tier0_ratios", None)
        if len(chain) <= 1 or not t0r or b not in t0r:
            return self.first_tier(b, reach1)
        ratio = t0r[b]
        c = self.dense[b] * ratio
        sc = self.screen.get(b)
        if sc is None or not sc["excess"]:
            return c, False
        passed = self.screen_reach(b, reach1)
        cq = sc["dense"] * ratio + passed * sc["recheck"]
        return (cq, True) if cq <= c * (1.0 + TIE) else (c, False)

    def with_tier0_cluster(self, ratios):
        """Return a shallow copy pricing multi-tier chains' first tier with centroid ratios.

        Parameters
        ----------
        ratios : dict of {int: float} or None
            Mapping from candidate Tier-0 band `b` to `n_clusters / n_templates` (`< 1.0`).

        Returns
        -------
        CostModel
            Copy of this cost model with `tier0_ratios` set (or `self` when unchanged).
        """
        clean = {int(b): round(float(r), 4)
                 for b, r in (ratios or {}).items() if 0.0 < float(r) < 1.0}
        if not clean and not getattr(self, "tier0_ratios", None):
            return self
        import copy
        cm = copy.copy(self)
        cm.tier0_ratios = clean
        cm._sig = None
        return cm

    def feed_delta(self, chain, reach, ntemplates, hw=None):
        """Per-pair change from `block` of the forward this chain's calls take: the band
        forward at its widest band, or the full forward, as the backend decides from the
        chain's modelled refine probability reach[len(chain)] (band_forward_wanted,
        the call's own rule; 0 when direct refine claims the band forward), each measured
        per block and spread over the templates. 0 where the backend has one feed."""
        if self.feed is None or not ntemplates:
            return 0.0
        top = int(max(chain))
        r = (0.0 if (hw is not None and self.prices_direct(chain))
             else min(max(float(reach[len(chain)]), 0.0), 1.0))
        if band_forward_wanted(self.n, top, r) and top in self.feed["band"]:
            per = self.feed["band"][top]
        else:
            per = self.feed["full"]
        return per / float(ntemplates)

    def with_direct(self, lag_price, single_tier=True, fraction=1.0, base=0.0, multi_frac=0.0):
        """A copy that also prices a direct refine at lag_price ticks per lag of its window
        (HierarchicalFilter._direct_price): a chain whose last tier reports its coarse lag
        then refines a pair, with a window of half-width h coarse samples, at the cheaper of
        the measured whole-block refine and base + (2 h n / b + 1) * lag_price, b its last band
        (refine_for; the window scales with n / b, so it favours chains ending in a wider band),
        weighted by the fraction of blocks eligible for direct refine."""
        import copy
        cm = copy.copy(self)
        cm.direct_lag = float(lag_price)
        # single_tier False: a one-tier chain's tier runs on the CPU's FP16 gate, which reports
        # no lag, so its survivors refine by transform (hmf.c hmf_tier.lagged).
        cm.direct_single = bool(single_tier)
        cm.direct_frac = float(fraction)
        cm.direct_base = float(base)
        cm.direct_multi_frac = float(multi_frac)
        cm._sig = None
        return cm

    def unscreened(self):
        """A copy that prices no Q15 screen: the costs of a plan whose first tier runs without
        one (a pinned chain's, HierarchicalFilter._arm_q15)."""
        import copy
        cm = copy.copy(self)
        cm.screen = {}
        cm._sig = None
        return cm

    def prices_direct(self, chain):
        """Whether this model prices a direct refine for chain (with_direct)."""
        return (getattr(self, "direct_lag", None) is not None
                and getattr(self, "direct_frac", 1.0) > 0.0
                and (len(chain) > 1 or getattr(self, "direct_single", True)))

    def refine_for(self, chain, f, hw=None):
        """Ticks per refined pair for this chain at refine density f, with the direct refine's
        window half-width hw (None: the whole-block refine)."""
        r = self.refine(f)
        if hw is not None and self.prices_direct(chain):
            d = getattr(self, "direct_base", 0.0) + self.direct_lag * (2 * int(hw) * (self.n // int(chain[-1])) + 1)
            mfrac = getattr(self, "direct_multi_frac", 0.0)
            if mfrac > 0.0:
                b_last = int(chain[-1])
                if b_last in self._sparse:
                    d += mfrac * self.sparse(b_last, f)
            d = min(r, d)
            frac = getattr(self, "direct_frac", 1.0)
            r = (1.0 - frac) * r + frac * d
        return r

    def chain_cost(self, chain, reach, hw=None):
        """reach[i] = P(a pair reaches tier i+1) for i = 0..k-1, reach[k] = P(reaches refine);
        hw the direct refine's half-width (refine_for)."""
        c, screened = self.first_tier_for(chain, reach[1] if len(reach) > 1 else 1.0)
        for i in range(1, len(chain)):
            c += reach[i] * self.sparse_for(chain[i], reach[i], screened)
        # A one-tier chain behind the Q15 screen has no coarse lag to refine around (hmf.c: the
        # screen reports none), so its survivors refine by transform, as the engine runs them.
        f = reach[len(chain)]
        c += f * (self.refine(f) if screened and len(chain) == 1 else self.refine_for(chain, f, hw))
        return c


_COSTS = {}

#: The engine's diagnostics, read by a plan when it is created (hmf.c).
_PLAN_DIAGNOSTICS = ("MF_HMF_DUMP", "MF_HMF_TRACE")


@contextmanager
def _internal_plans():
    """Off, while the library creates plans for itself (cost calibration): the diagnostic dump
    and trace describe the caller's plans. A calibration plan would otherwise truncate the
    caller's dump file and write its own pairs into it."""
    held = {k: os.environ.pop(k) for k in _PLAN_DIAGNOSTICS if k in os.environ}
    try:
        yield
    finally:
        os.environ.update(held)


def cpu_gate_kind():
    """'f16' when new CPU hierarchical plans run the FP16 first gate (gate16.cc: ARM with
    FP16 vectors, unless MF_GATE16=0), else 'f32'. Costs, block prices and chain choices
    are cached per kind."""
    from . import _core
    return "f16" if getattr(_core, "gate16", lambda: False)() else "f32"


def _cost_sig(cost):
    return None if cost is None else cost.signature()
#: Survivor densities the calibration places the tiers at (bracketing production's 0.1-10%).
_CAL_DENSITIES = (0.1, 0.01)


def gpu_kernel_id(backend="vulkan"):
    """Identity of the shipped kernels whose measured choices this backend stores."""
    from ._kernel_id import gpu_kernel_id as identity
    return identity(backend)


def _cost_model_ok(record):
    """Whether a stored record is a cost model CostModel.from_dict can read."""
    try:
        CostModel.from_dict(record)
        return True
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def _stored_cost_model(path, skey):
    """The cost model stored under skey, or None (none stored, or a record that is not
    one: then it is reported, and a fresh calibration replaces it)."""
    stored = _load_cost_file(path).get(skey)
    if stored is None:
        return None
    if not _cost_model_ok(stored):
        _cost_warn(path, "model:" + skey, "record %r is not a cost model; recalibrating" % skey)
        return None
    return CostModel.from_dict(stored)


#: The template count calibrations run at. Per-pair tier and refine costs are flat in the
#: count to within a calibration's own noise (n=2048, 4096; 40-128 templates), and a bank's
#: own count enters pricing through the per-block share (CostModel.block / ntemplates), so one
#: calibration per transform size serves every bank -- and every bank then shares one cost
#: model, and with it the cached chain choices.
_CAL_TEMPLATES = 64


_Q15_BAND = {}


def _q15_band(b):
    """Whether this back end has a Q15 screen for a first tier at band b."""
    from . import _core
    b = int(b)
    if b not in _Q15_BAND:
        try:
            _Q15_BAND[b] = _core.MF(b, 1, 1).q15_lanes() > 0
        except (ValueError, AttributeError):
            _Q15_BAND[b] = False
    return _Q15_BAND[b]


def default_series_group(n):
    """Blocks a CPU plan filters together, as HierarchicalFilter uses without an execution policy."""
    return 32 if n <= 2048 else 16


def _run_ms(log):
    """Device milliseconds of the runs in a timing log (Executor.timings), without the
    MF_GPU_PROFILE entries ("k:...") that lie inside them."""
    return sum(ms for label, ms in log if not label.startswith("k:"))


def _is_gpu(device):
    """Whether `device` names a GPU (the cost model's band forward and fp16 gate)."""
    try:
        from .device import parse as _parse
        return _parse(device).kind == "gpu"
    except Exception:
        return False


def _reach(N, cols, thresholds):
    """Cumulative noise pass probabilities through the chain."""
    alive = np.ones(N.shape[0], bool)
    out = [1.0]
    for c, g in zip(cols, thresholds):
        alive &= N[:, c] >= g
        out.append(float(alive.mean()))
    return out


_KEPT = OrderedDict()
_KEPT_MAX = 4096


def kept_draws(sig, bands, chain, snr):
    """Coarse maxima of `chain`'s tiers for the draws the fine stage keeps (fine max >= snr).

    signal_draws' maxima are over the whole searched window, as the engine's (hmf.c), so a
    tier whose gate falls below the window's noise floor passes the draws a noise peak
    elsewhere in the block carries. Memoised per draws (by identity, held so they cannot be
    reused), chain and snr: every template group pricing a profile asks again."""
    C, F = sig[0], sig[1]
    cols = [bands.index(b) for b in chain]
    key = (id(C), id(F), tuple(cols), float(snr))
    hit = _KEPT.get(key)
    if hit is not None and hit[0] is C and hit[1] is F:
        _KEPT.move_to_end(key)
        return hit[2]
    # When F broadcasts one fine maximum across all columns (signal_draws), filter C once per
    # (C, F, snr) and slice columns per chain rather than copying and scanning F[:, cols].
    if F.ndim == 2 and F.shape[1] > 0 and F.strides[1] == 0:
        bkey = ("kept_all", id(C), id(F), float(snr))
        bhit = _KEPT.get(bkey)
        if bhit is not None and bhit[0] is C and bhit[1] is F:
            _KEPT.move_to_end(bkey)
            c_kept = bhit[2]
        else:
            c_kept = C[F[:, 0] >= snr]
            _KEPT[bkey] = (C, F, c_kept)
            while len(_KEPT) > _KEPT_MAX:
                _KEPT.popitem(last=False)
        out = c_kept[:, cols]
    else:
        keep = F[:, cols[0]] >= snr
        for c in cols[1:]:
            keep = keep | (F[:, c] >= snr)
        out = C[keep][:, cols]
    out.setflags(write=False)
    _KEPT[key] = (C, F, out)
    while len(_KEPT) > _KEPT_MAX:
        _KEPT.popitem(last=False)
    return out


def _smallest(col, m):
    """Indices of col's m smallest values, in ascending order of value (O(len) selection)."""
    m = min(int(m), col.size)
    if m <= 0:
        return np.empty(0, np.int64)
    idx = np.argpartition(col, m - 1)[:m] if m < col.size else np.arange(col.size)
    return idx[np.argsort(col[idx], kind="stable")]


#: plan_chain's candidates per (draws, chain, prune, half-widths): they do not depend on the
#: cost model, so every template group pricing the same profile and window reuses them.
_CAND_CACHE = OrderedDict()
_CAND_CACHE_MAX = 4096


def _halves(x):
    """(search half, fit half) of the detections x: its even rows and its odd rows, each
    contiguous. The detections are independent draws in simulation order, so the halves are
    independent of each other."""
    key = ("halves", id(x))
    hit = _KEPT.get(key)
    if hit is not None and hit[0] is x:
        _KEPT.move_to_end(key)
        return hit[1], hit[2]
    a = np.ascontiguousarray(x[0::2])
    b = np.ascontiguousarray(x[1::2])
    a.setflags(write=False)
    b.setflags(write=False)
    _KEPT[key] = (x, a, b)
    while len(_KEPT) > _KEPT_MAX:
        _KEPT.popitem(last=False)
    return a, b


def _distances(sig, lags, bands, chain, snr, n):
    """Per detection (kept_draws' rows), how far the fine maximum lies from the chain's last
    tier's coarse maximum, in that tier's coarse samples: the direct refine's window of
    half-width h around the coarse maximum holds the fine peak iff this is at most h
    (hmf.c refine_direct_pair)."""
    F = sig[1]
    fat, cat = lags
    b = int(chain[-1])
    col = bands.index(b)
    key = ("dist", id(F), id(fat), id(cat), col, b, float(snr), int(n))
    hit = _KEPT.get(key)
    if hit is not None and hit[0] is F and hit[1] is fat and hit[2] is cat:
        _KEPT.move_to_end(key)
        return hit[3]
    keep = F[:, 0] >= snr
    out = np.abs(fat[keep] - cat[keep, col]) / (n // b)
    out.setflags(write=False)
    _KEPT[key] = (F, fat, cat, out)
    while len(_KEPT) > _KEPT_MAX:
        _KEPT.popitem(last=False)
    return out


def _all_halfwidths(dist, allow):
    """Cost-independent candidate half-widths (None, hmin, ...) for search half `dist`."""
    if dist is None or allow < 0:
        return (None,)
    key = ("hws", id(dist), int(allow))
    hit = _KEPT.get(key)
    if hit is not None and hit[0] is dist:
        _KEPT.move_to_end(key)
        return hit[1]
    if dist.size > allow:
        kth = dist.size - 1 - allow
        hmin = max(1, int(math.ceil(np.partition(dist, kth)[kth])))
    else:
        hmin = 1
    up = np.ceil(dist[dist > hmin]).astype(np.int64)
    out = (None,) + tuple(sorted({hmin} | {int(h) for h in up}))
    _KEPT[key] = (dist, out)
    while len(_KEPT) > _KEPT_MAX:
        _KEPT.popitem(last=False)
    return out


def _halfwidths(dist, allow, cost, chain, n, all_hws=None):
    """The direct refine's candidate half-widths for `chain` on the search half (dist its
    detections' _distances): None, the whole-block refine, which loses no detection; and,
    where the cost model prices a direct refine for the chain (CostModel.prices_direct), each
    whole number of coarse samples at which a different set of the detections lies beyond
    it, from the smallest leaving at most `allow` of them beyond it (gatemodel.
    window_allowance; -1: none may be missed) to the largest whose window the model prices
    below its dearest whole-block refine. Each is the smallest half-width with its set, so the
    cheapest window losing those detections."""
    if dist is None or cost is None or allow < 0 or not cost.prices_direct(chain):
        return (None,)
    R = n // int(chain[-1])
    top = max(v for _, v in cost._refine)
    dbase = getattr(cost, "direct_base", 0.0)
    hmax = int(((top - dbase) / cost.direct_lag - 1.0) // (2 * R))      # 2 h R + 1 lags priced below top
    if all_hws is None:
        all_hws = _all_halfwidths(dist, allow)
    if len(all_hws) < 2 or hmax < all_hws[1]:
        return (None,)
    return (None,) + tuple(h for h in all_hws[1:] if h <= hmax)


class _LazyPlan(dict):
    """A plan_chain dict whose fit-half thresholds and noise reach materialize on first read."""

    __slots__ = ("_pending",)

    def __init__(self, eager, pending):
        super().__init__(eager)
        self._pending = pending

    def _materialize(self):
        pending = self._pending
        if pending is None:
            return
        self._pending = None
        B, dB, th, hw, fd, noise, cols = pending
        thresholds, halfwidth = _fit(B, dB, th, hw, fd)
        super().__setitem__("thresholds", thresholds)
        super().__setitem__("reach", tuple(_reach(noise, cols, thresholds)))
        super().__setitem__("halfwidth", halfwidth)

    def __getitem__(self, key):
        if not super().__contains__(key) and self._pending is not None:
            self._materialize()
        return super().__getitem__(key)

    def get(self, key, default=None):
        if not super().__contains__(key) and self._pending is not None:
            self._materialize()
        return super().get(key, default)

    def __contains__(self, key):
        if super().__contains__(key):
            return True
        if self._pending is not None:
            self._materialize()
            return super().__contains__(key)
        return False

    def __len__(self):
        if self._pending is not None:
            self._materialize()
        return super().__len__()

    def __iter__(self):
        if self._pending is not None:
            self._materialize()
        return super().__iter__()

    def keys(self):
        if self._pending is not None:
            self._materialize()
        return super().keys()

    def values(self):
        if self._pending is not None:
            self._materialize()
        return super().values()

    def items(self):
        if self._pending is not None:
            self._materialize()
        return super().items()

    def copy(self):
        if self._pending is not None:
            self._materialize()
        return dict(self)

    def __eq__(self, other):
        if self._pending is not None:
            self._materialize()
        if isinstance(other, _LazyPlan) and other._pending is not None:
            other._materialize()
        return super().__eq__(other)

    def __repr__(self):
        if self._pending is not None:
            self._materialize()
        return super().__repr__()

    def __reduce__(self):
        if self._pending is not None:
            self._materialize()
        return (dict, (dict(self),))


def plan_chain(sig, noise, bands, chain, fd, cost, n, snr, prune=False, ntemplates=None,
               memo=None, lags=None, lazy_fit=False, offsets=None):
    """The thresholds and direct-refine half-width for `chain` that meet the false-dismissal
    budget fd at minimum modelled cost.

    sig, noise: signal_draws / noise_block_maxima over `bands` and the same window; lags: the
    draws' lags (signal_draws(..., lags_too=True)), for the direct refine's window where the
    cost model prices one. Returns dict(chain, thresholds, reach, halfwidth, cost, q15,
    search), or None when fd cannot be resolved: the thresholds and the half-width (None:
    the whole-block refine) the filter runs with and the noise share reaching each tier and
    the refine under them; the modelled cost, q15 and `search` (its thresholds, reach,
    half-width and the search half's detections its window misses, of a budget of K) of the
    plan as searched, which every choice ranks plans by.

    The detections fall into two independent halves (_halves), and the plan's dismissal is
    a fraction of the detections: those some tier dismisses or the direct refine's window
    misses, together.

    The SEARCH half decides the plan's structure. Every split of its budget of K dismissed
    detections between the tiers (over the shares _SPLIT) and every candidate half-width
    (_halfwidths: windows missing at most gatemodel.window_allowance of the detections, which
    count against the same K) gives candidate thresholds, and the one the cost model prices
    cheapest wins, the earliest on a tie. A search keeps the candidate those draws flatter,
    so its dismissal on them is not its dismissal: nothing it chooses is judged on them.

    The FIT half sets the thresholds: the search's, every tier moved by one shift fitted to
    the fit half (_fit). Given the search half, the fit half is independent of the plan's
    structure, so the plan's dismissal has mean fd and the tail gatemodel.fit_order sets,
    whatever the search and every choice made from it (choose_chain's among chains included).

    The search's candidates do not depend on the cost model; only their pricing does. Its
    selection works on each column's K-or-so smallest values (a selection, not a sort) and
    on the few dismissed draws' indices, and carries noise passes down the split search, so
    candidates sharing a prefix share its work. memo, a key naming the draws (_choose_chain
    passes the profile, n, window and draw parameters), caches the candidates, so another
    template group or cost model prices them without searching again.
    """
    cols = [bands.index(b) for b in chain]
    A, B = _halves(kept_draws(sig, bands, chain, snr))
    K = int(round(float(fd) * (A.shape[0] + 1))) - 1      # the search half's budget, as the fit's
    fit_j = int(round(float(fd) * (B.shape[0] + 1)))
    if K < 0 or fit_j < 1 or fit_j > B.shape[0]:
        return None
    dA = dB = dA_all = None
    allow = -1
    if lags is not None:
        dA_all, dB_all = _halves(_distances(sig, lags, bands, chain, snr, n))
        allow = _gm.window_allowance(float(fd), A.shape[0], B.shape[0])
        if cost is not None and cost.prices_direct(chain):
            dA, dB = dA_all, dB_all
    all_hws = _all_halfwidths(dA_all, allow)
    hws = _halfwidths(dA, allow, cost, chain, n, all_hws=all_hws)
    eff_prune = bool(prune) and len(chain) > 1
    key = None if memo is None else tuple(memo) + (tuple(int(b) for b in chain), eff_prune, all_hws)
    hit = _CAND_CACHE.get(key) if key is not None else None
    if hit is not None and hit[0] is sig[0] and hit[1] is noise:
        _CAND_CACHE.move_to_end(key)
        cands = hit[2]
    else:
        cand_hws = all_hws if key is not None else hws
        dead = tuple(np.empty(0, np.int64) if h is None else np.flatnonzero(dA_all > h)
                     for h in cand_hws)
        cands = _chain_candidates(A, noise, cols, K, eff_prune, dead)
        if key is not None:
            _CAND_CACHE[key] = (sig[0], noise, cands)
            while len(_CAND_CACHE) > _CAND_CACHE_MAX:
                _CAND_CACHE.popitem(last=False)
    best = None
    has_feed = bool(ntemplates and getattr(cost, "feed", None))
    k = len(chain)
    # Hoist prefix tier costs across candidate half-widths when pricing on CostModel (k >= 2)
    if isinstance(cost, CostModel) and k >= 2:
        later = chain[1:]
        prices_dir = cost.prices_direct(chain)
        dlag = getattr(cost, "direct_lag", 0.0) if prices_dir else 0.0
        dbase = getattr(cost, "direct_base", 0.0) if prices_dir else 0.0
        dmfrac = getattr(cost, "direct_multi_frac", 0.0) if prices_dir else 0.0
        dfrac = getattr(cost, "direct_frac", 1.0) if prices_dir else 1.0
        b_last = int(chain[-1]) if prices_dir else 0
        has_last_sparse = bool(prices_dir and dmfrac > 0.0 and b_last in cost._sparse)
        R = n // b_last if prices_dir else 0
        for pth, preach, lasts in cands:
            c_prefix, screened = cost.first_tier_for(chain, preach[1])
            for idx_t, bt in enumerate(later, 1):
                ri = preach[idx_t]
                c_prefix += ri * cost.sparse_for(bt, ri, screened)
            for hw, last in zip(hws, lasts):
                if last is None:
                    continue
                f = last[1]
                r_cost = cost.refine(f)
                if hw is not None and prices_dir:
                    d_cost = dbase + dlag * (2 * int(hw) * R + 1)
                    if has_last_sparse and f >= 0.05:
                        d_cost += dmfrac * cost.sparse(b_last, f)
                    d_cost = min(r_cost, d_cost)
                    r_cost = (1.0 - dfrac) * r_cost + dfrac * d_cost
                c = c_prefix + f * r_cost
                if has_feed:
                    c += cost.feed_delta(chain, preach + (f,), ntemplates, hw)
                if best is None or c < best[0]:
                    best = (float(c), pth + (last[0],), preach + (f,), hw)
    else:
        for pth, preach, lasts in cands:
            for hw, last in zip(hws, lasts):
                if last is None:
                    continue
                th, reach = pth + (last[0],), preach + (last[1],)
                c = cost.chain_cost(chain, list(reach), hw) if cost is not None else _flop_cost(chain, list(reach), n)
                if has_feed:
                    # the change from the feed `block` was measured with; pick_stable's tie window
                    # is absolute-valued, so a change that takes a total below zero still compares
                    c += cost.feed_delta(chain, list(reach), ntemplates, hw)
                if best is None or c < best[0]:
                    best = (float(c), th, reach, hw)
    if best is None:
        return None
    c, th, reach, hw = best
    if hasattr(cost, "first_tier_for"):
        q15 = bool(cost.first_tier_for(chain, reach[1])[1])
    elif hasattr(cost, "first_tier"):
        q15 = bool(cost.first_tier(chain[0], reach[1])[1])
    else:
        q15 = False
    missed = 0 if hw is None else int(np.count_nonzero(dA > hw))
    search_info = dict(thresholds=th, reach=reach, halfwidth=hw, missed=missed, K=K)
    offs = (0,) * len(chain) if offsets is None else tuple(int(x) for x in offsets)
    if lazy_fit:
        return _LazyPlan(
            dict(chain=tuple(chain), offsets=offs, cost=c, q15=q15, search=search_info),
            (B, dB, th, hw, fd, noise, cols),
        )
    fit = _fit(B, dB, th, hw, fd)
    if fit is None:
        return None
    thresholds, halfwidth = fit
    return dict(chain=tuple(chain), offsets=offs, thresholds=thresholds,
                reach=tuple(_reach(noise, cols, thresholds)), halfwidth=halfwidth, cost=c,
                q15=q15, search=search_info)


def _fit(B, dist, thresholds, hw, fd):
    """The plan's (thresholds, half-width) from the fit half B (M, k) of the detections, dist
    their _distances (None without a direct refine): the search's `thresholds` and half-width
    `hw`, every tier moved by one shift s, or None when M draws cannot place the budget.

    A detection passes every tier at shift s iff s <= its score, the smallest of its coarse
    maxima less their thresholds; one the window misses (dist > hw) is dismissed at any s. s
    is the j-th smallest score, j = round(fd (M + 1)) (gatemodel.fit_order), so j - 1 of B
    are dismissed, and on fresh draws the plan's dismissal is the j-th smallest of M uniforms
    (gatemodel.fit_order): its mean is fd whatever the search chose.

    Where the window alone misses j of B, the plan refines by transform instead (half-width
    None), which misses none, and the tiers take the whole budget. That branch is taken on B,
    so the plan is then not the j-th smallest uniform (fitted on the detections that showed
    the window failing, 17 such plans dismissed 1.14 fd on average; tools/split_bias.py,
    2026-10-29): the search offers only windows for which the branch has at most the
    probability the fit's tail leaves (gatemodel.window_allowance, at most 0.002), so a plan
    exceeds 1.25 fd with probability at most gatemodel._TAIL_SHARE with the branch included,
    and its mean moves by at most that probability times the branch's dismissal."""
    M = B.shape[0]
    j = int(round(float(fd) * (M + 1)))
    if j < 1 or j > M:
        return None
    th = np.asarray(thresholds, np.float64)
    score = (B - th).min(axis=1)
    if hw is not None:
        out = dist > hw
        if np.count_nonzero(out) >= j:
            hw = None
        else:
            score[out] = -np.inf
    s = float(np.partition(score, j - 1)[j - 1])
    return tuple(max(float(g) + s, 0.0) for g in th), hw


def _chain_candidates(S, noise, cols, K, prune, dead):
    """plan_chain's search on the search half's detections S (M, k), each tier's coarse
    maxima, with noise the noise blocks' maxima and cols the chain's columns of them: every
    split of the budget of K dismissed detections it considers, in its order, as (earlier
    thresholds, earlier reach, lasts). The earlier tiers' thresholds and the noise shares
    reaching each tier; and per set in `dead`, detections dismissed whatever the tiers (the
    direct refine's window's misses at one half-width), the last tier's threshold, the K-th
    from the budget, and the noise share it passes on, or None where the set leaves it no
    budget. A split the last tier has budget for under no set is left out."""
    M, k = S.shape
    # The earlier tiers' thresholds sit at index <= K of their sorted columns; the last
    # tier's is the rem-th smallest alive value with rem + dismissed <= K.
    low = [_smallest(S[:, i], K + 1) for i in range(k - 1)]
    low_val = [S[o, i] for i, o in enumerate(low)]
    last_order = _smallest(S[:, k - 1], K + 1)
    last_val = S[last_order, k - 1]
    out = []
    Nn = noise.shape[0]
    # The draws the earlier tiers dismiss, set and unset as the search descends and returns
    # (a copy per node was much of a search). Noise blocks below the lowest first-tier
    # threshold the search tries are dismissed on every branch: the search runs on the others
    # only, their chain columns contiguous, with alive masks over them. A reach is the alive
    # count over all Nn blocks, the same float as the mean of a full-length mask.
    marks = np.zeros(M, np.uint8)
    splits = _SPLIT
    if k > 1:
        firsts = [int(math.floor(a * K)) for a in splits]
        g0 = min((float(low_val[0][i]) for i in firsts if i >= 1), default=None)
        rows = noise[:, cols[0]] >= g0 if g0 is not None else np.zeros(Nn, bool)
        Nc = np.ascontiguousarray(noise[rows][:, cols].T)
    else:
        Nc = np.ascontiguousarray(noise[:, cols].T)

    def consider(prefix, ndead, alive, fracs):
        """Given thresholds for tiers 0..k-2, the last uses the remaining budget: ndead draws
        are dismissed (marked), alive the noise blocks passing every earlier tier (None: all
        of them), fracs those tiers' pass rates."""
        if prune and any(r > _USELESS_PASS for r in fracs):
            # choosing: a tier that passes most of its pairs on to ANOTHER TIER only adds its
            # own cost. (The last tier's pass rate into the refine is not judged here: at a
            # low snr every chain refines most pairs, and the cost already says so.)
            return
        lasts = []
        for D in dead:
            extra = D[marks[D] == 0]
            nd = ndead + int(extra.size)
            rem = K - nd
            at = None
            if 0 <= rem < M - nd:
                # the rem-th smallest last-tier value among draws not yet dismissed
                marks[extra] = 255
                pos = np.flatnonzero(marks[last_order] == 0)
                marks[extra] = 0
                at = int(pos[rem]) if pos.size > rem else None
            if at is None:
                lasts.append(None)
                continue
            g = float(last_val[at])
            hit = Nc[-1] >= g
            if alive is not None:
                hit &= alive
            lasts.append((g, int(np.count_nonzero(hit)) / Nn))
        if any(x is not None for x in lasts):
            out.append((tuple(prefix), (1.0,) + tuple(fracs), tuple(lasts)))

    def rec(i, prefix, remaining, ndead, alive, fracs):
        # tier i takes a share of the budget still unallocated; the last tier gets what is left
        if i == k - 1:
            consider(prefix, ndead, alive, fracs)
            return
        for a in splits:
            share = a * remaining
            idx = int(math.floor(share * K))
            if idx < 1:
                continue
            g = float(low_val[i][idx])
            # draws this tier dismisses: its column strictly below g
            cut = int(np.searchsorted(low_val[i], g, side="left"))
            cand = low[i][:cut]
            new = cand[marks[cand] == 0]
            marks[new] = i + 1
            an = Nc[i] >= g
            if alive is not None:
                an &= alive
            rec(i + 1, prefix + [g], remaining - share, ndead + int(new.size), an,
                fracs + [int(np.count_nonzero(an)) / Nn])
            marks[new] = 0

    if _C_SEARCH and all(len(o) == K + 1 for o in low) and len(last_order) == K + 1:
        from . import _core
        return _core.chain_candidates(np.ascontiguousarray(S, np.float32), Nc, tuple(low),
                                      tuple(np.ascontiguousarray(v, np.float32) for v in low_val),
                                      np.ascontiguousarray(last_order, np.int64),
                                      np.ascontiguousarray(last_val, np.float32),
                                      tuple(float(a) for a in splits), int(K), int(Nn), bool(prune),
                                      float(_USELESS_PASS),
                                      tuple(np.ascontiguousarray(d, np.int64) for d in dead))
    rec(0, [], 1.0, 0, None, [])
    return out


#: _chain_candidates runs its search in C (_core.chain_candidates; the Python recursion above
#: it is the reference, identical candidates in the same order, ~1.3 ms a call of Python and
#: small array operations on dev2). False runs the Python one (tests compare them).
_C_SEARCH = True


#: A tier whose modelled noise pass rate exceeds this rejects too little to be worth running:
#: such a split is skipped, so a chain is priced only with thresholds that make every tier
#: gate. (Seen on Vulkan: a band-64 first tier ahead of 256 passing 4,337,904 of 4,337,904
#: pairs, at 2-3x the segment time of every other choice.)
_USELESS_PASS = 0.5


def canonical_order(chain):
    """Deterministic preference among tied chains: fewer tiers, then the smaller bands."""
    return (len(chain), tuple(chain))


def pick_stable(items, cost, key):
    """The canonical-first of the items whose cost is within TIE of the cheapest."""
    items = list(items)
    if not items:
        return None
    lo = min(cost(x) for x in items)
    return min((x for x in items if cost(x) <= lo + TIE * abs(lo)), key=key)


def _flop_cost(chain, reach, n):
    """Fallback when no measured table exists: transform-size proxy b log b per tier, n log n per refine."""
    c = chain[0] * math.log2(chain[0])
    for i in range(1, len(chain)):
        c += reach[i] * chain[i] * math.log2(chain[i])
    return c + reach[len(chain)] * n * math.log2(n)


_CHOICE_CACHE = OrderedDict()
_OFFSET_CACHE = OrderedDict()


def _cached_band_offsets(p, sig_p, n, floor):
    """Return cached (k0_cand, usable_bands_list) for normalized profile `p` at `(n, floor)`."""
    off_key = (sig_p, int(n), int(floor))
    hit = _OFFSET_CACHE.get(off_key)
    if hit is not None:
        _OFFSET_CACHE.move_to_end(off_key)
        return hit
    c_bands = candidate_bands(n, floor)
    k0_cand = tuple(band_offset(p, n, b) for b in c_bands)
    bands = [b for b, k0 in zip(c_bands, k0_cand) if p[slice(*_band_slice(n, b, k0))].sum() > 0]
    res = (c_bands, k0_cand, bands)
    _cache_put(_OFFSET_CACHE, off_key, res)
    return res


def choose_chain(power, n, snr, fd, cost=None, max_tiers=3, floor=_MIN_BAND, nsim=None, window=None,
                 ntemplates=None, nsamp=None, tier0_clusters=None, template_alphas=None):
    """Price every chain and return (best, all plans sorted by cost): plan_chain's plans,
    ranked by their searched cost, (None, []) when none can be planned. nsamp: the
    detections to draw (default: model_draws').

    Cached like the draws it is built from: by profile signature, and reused for
    profiles within the cosine similarity gatemodel applies to them.
    """
    p = _norm_profile(power, n)
    win = None if window is None else (int(window[0]), int(window[1]))
    dsamp, dsim = model_draws(fd)
    nsamp = dsamp if nsamp is None else int(nsamp)
    nsim = dsim if nsim is None else int(nsim)
    if nsamp is None:
        return None, []          # the tail bound needs more detections than the model holds
    t0_map = {}
    if tier0_clusters and int(max_tiers) >= 2:
        for b, sp in tier0_clusters.items():
            a, lp = (sp.alpha, sp.lag_pad) if hasattr(sp, "alpha") else sp
            t0_map[int(b)] = (round(max(0.0, min(1.0, float(a))), 4), max(0, int(lp)))
    sig_p = _gm._profile_sig(p)
    c_bands, k0_cand, bands = _cached_band_offsets(p, sig_p, n, floor)
    base_mat = _select_template_alphas(template_alphas, bands) if bands else None
    extra = (k0_cand,) if any(k0_cand) else ()
    if t0_map:
        extra = extra + (("t0", tuple(sorted(t0_map.items()))),)
    if base_mat is not None:
        extra = extra + (("tal", _alpha_key_token(np.ascontiguousarray(np.round(base_mat, 4), np.float32))),)
    params = (n, float(snr), float(fd), int(max_tiers), int(floor), int(nsim), int(nsamp), win, _cost_sig(cost),
              # ntemplates prices the feed
              None if not getattr(cost, "feed", None) else int(ntemplates or 0)) + extra
    key = (sig_p,) + params
    hit = _CHOICE_CACHE.get(key)
    if hit is not None:
        _CHOICE_CACHE.move_to_end(key)
        return hit
    unit, hit = _similar_get("choice", p, params)
    if hit is not None:
        _cache_put(_CHOICE_CACHE, key, hit)
        return hit
    offsets_map = dict(zip(c_bands, k0_cand))
    out = _choose_chain(p, n, snr, fd, cost, max_tiers, floor, nsim, win, ntemplates, nsamp,
                        bands=bands, offsets_by_band=offsets_map,
                        tier0_clusters=tier0_clusters if tier0_clusters and int(max_tiers) >= 2 else None,
                        template_alphas=base_mat)
    _cache_put(_CHOICE_CACHE, key, out)
    _similar_put("choice", unit, params, out)
    return out


def _choose_chain(power, n, snr, fd, cost, max_tiers, floor, nsim, window, ntemplates=None,
                  nsamp=None, bands=None, offsets_by_band=None, tier0_clusters=None,
                  template_alphas=None):
    p = _norm_profile(power, n)
    if bands is None:
        bands = usable_bands(p, n, floor)
    else:
        bands = sorted(int(b) for b in bands)
    if not bands:
        return None, []
    win = None if window is None else (int(window[0]), int(window[1]))
    nsamp = _gm._nsamp_for(fd) if nsamp is None else int(nsamp)
    if offsets_by_band is None:
        offsets_by_band = {b: band_offset(p, n, b) for b in bands}
    k0s = tuple(offsets_by_band[b] for b in bands)
    Fb = np.array([p[slice(*_band_slice(n, b, k0))].sum() for b, k0 in zip(bands, k0s)])
    if np.any(Fb <= 0):
        return None, []
    base_mat = _select_template_alphas(template_alphas, bands)
    # Resolve the canonical profile in _SIGNAL_RECORDS so base and clustered draws share one realization
    sr_kw = {"k0s": k0s} if any(k0s) else {}
    if base_mat is not None:
        sr_kw["alphas"] = np.ascontiguousarray(np.round(base_mat, 4), dtype=np.float32)
    p_base = _signal_records(p, n, bands, Fb, float(snr), nsamp, _SEED, **sr_kw)["p"]
    drawn = signal_draws(p_base, n, bands, snr, nsamp, window=win, lags_too=True, alphas=base_mat)
    if drawn is None:
        return None, []
    sig, lags = drawn
    noise = noise_block_maxima(p_base, n, bands, nsim=nsim, window=win, alphas=base_mat)
    memo = ("choose", id(sig[0]), id(noise), n, float(snr), float(fd), tuple(bands), win,
            int(nsim), int(nsamp))

    # Build joint multi-tier signal & noise matrices per clustered Tier-0 band (matching chain_thresholds)
    t0_draws = {}
    if tier0_clusters and int(max_tiers) >= 2 and len(bands) >= 2:
        t0_map = {}
        t0_raw = {}
        for b, sp in tier0_clusters.items():
            a, lp = (sp.alpha, sp.lag_pad) if hasattr(sp, "alpha") else sp
            t0_map[int(b)] = (round(max(0.0, min(1.0, float(a))), 4), max(0, int(lp)))
            t0_raw[int(b)] = sp
        t0_bands = [b for b in bands[:-1] if b in t0_map]
        for b0 in t0_bands:
            a0, lp0 = t0_map[b0]
            al_b0 = _combine_tier0_alphas(base_mat, bands, b0, t0_raw[b0], a0)
            lp_b0 = tuple(lp0 if b == b0 else 0 for b in bands)
            drawn_b0 = signal_draws(p_base, n, bands, snr, nsamp, window=win,
                                    lags_too=True, alphas=al_b0)
            if drawn_b0 is None:
                continue
            sig_b0, lags_b0 = drawn_b0
            noise_b0 = noise_block_maxima(p_base, n, bands, nsim=nsim, window=win,
                                          alphas=al_b0, lag_pads=lp_b0)
            memo_b0 = ("choose_t0", id(sig_b0[0]), id(noise_b0), b0, t0_map[b0], n, float(snr),
                       float(fd), tuple(bands), win, int(nsim), int(nsamp))
            t0_draws[b0] = (sig_b0, noise_b0, memo_b0, lags_b0)

    plans = []
    for chain in enumerate_chains(n, max_tiers, floor, bands=bands):
        offs = tuple(offsets_by_band[b] for b in chain)
        if len(chain) > 1 and chain[0] in t0_draws:
            sig_use, noise_use, memo_use, lags_use = t0_draws[chain[0]]
        else:
            sig_use, noise_use, memo_use, lags_use = sig, noise, memo, lags
        pl = plan_chain(sig_use, noise_use, bands, list(chain), fd, cost, n, snr, prune=True,
                        ntemplates=ntemplates, memo=memo_use, lags=lags_use, lazy_fit=True, offsets=offs)
        if pl is not None:
            plans.append(pl)
    plans.sort(key=lambda d: d["cost"])
    # Ties (within the calibration's process-to-process noise) go to the cheaper chain on the
    # calibration-free flop proxy: deterministic for a given profile, and still a cost. Both
    # are the searched plans' (plan_chain), so the choice is made on the search half only.
    best = pick_stable(plans, lambda d: d["cost"],
                       lambda d: (_flop_cost(d["chain"], d["search"]["reach"], n), d["chain"]))
    return best, plans


_PLAN_CACHE = OrderedDict()


#: calibrate_costs(n, ntemplates, ...) measures this machine's tier costs at transform size n
#: through the engine itself and returns the CostModel the chain choice prices with, kept in
#: MF_COST_FILE when it is set. It runs hierarchical plans, which sit above this module, so
#: it is matchedfilter._calibration.calibrate_costs (which documents the measurement), bound
#: to this name when that module loads (the package loads it): one function, one set of
#: defaults, wherever it is called from.
calibrate_costs = None


def chain_thresholds(power, n, snr, fd, chain, cost=None, floor=_MIN_BAND, nsim=None, window=None,
                     nsamp=None, tier0_cluster=None, template_alphas=None):
    """The plan (plan_chain's: thresholds, reach, the direct refine's half-width where the
    cost model prices one, cost) for one given chain under `power`, or None where it cannot
    be planned. nsamp: the detections to draw (default: model_draws').

    Called whenever a plan's reference changes, inside the caller's filtering,
    so results are cached -- by profile signature, and reused for profiles
    within the same cosine similarity gatemodel applies to its draws.
    """
    p = _norm_profile(power, n)
    chain = tuple(int(b) for b in chain)
    win = None if window is None else (int(window[0]), int(window[1]))
    dsamp, dsim = model_draws(fd)
    nsamp = dsamp if nsamp is None else int(nsamp)
    nsim = dsim if nsim is None else int(nsim)
    if nsamp is None:
        return None              # the tail bound needs more detections than the model holds
    t0_cl = None
    if tier0_cluster is not None and len(chain) > 1:
        a, lp = (tier0_cluster.alpha, tier0_cluster.lag_pad) if hasattr(tier0_cluster, "alpha") else tier0_cluster
        t0_cl = (round(max(0.0, min(1.0, float(a))), 4), max(0, int(lp)))
    sig_p = _gm._profile_sig(p)
    _, _, bands = _cached_band_offsets(p, sig_p, n, floor)
    base_mat = _select_template_alphas(template_alphas, bands) if bands else None
    ch_off_key = ("chain", sig_p, int(n), chain)
    k0_chain = _OFFSET_CACHE.get(ch_off_key)
    if k0_chain is None:
        k0_chain = tuple(band_offset(p, n, b) for b in chain)
        _cache_put(_OFFSET_CACHE, ch_off_key, k0_chain)
    else:
        _OFFSET_CACHE.move_to_end(ch_off_key)
    extra = (k0_chain,) if any(k0_chain) else ()
    if t0_cl is not None:
        extra = extra + (("t0", t0_cl),)
    if base_mat is not None:
        extra = extra + (("tal", _alpha_key_token(np.ascontiguousarray(np.round(base_mat, 4), np.float32))),)
    key = (sig_p, n, chain, float(snr), float(fd), win, int(nsim), int(nsamp), _cost_sig(cost), *extra)
    hit = _PLAN_CACHE.get(key)
    if hit is not None:
        _PLAN_CACHE.move_to_end(key)
        return hit
    sim_params = (n, chain, float(snr), float(fd), win, int(nsim), int(nsamp), _cost_sig(cost)) + extra
    unit, hit = _similar_get("plan", p, sim_params)
    if hit is not None:
        _cache_put(_PLAN_CACHE, key, hit)
        return hit
    if not set(chain) <= set(bands):
        return None
    if t0_cl is not None:
        b0 = chain[0]
        al_vec = _combine_tier0_alphas(base_mat, bands, b0, tier0_cluster, t0_cl[0])
        lp_vec = tuple(t0_cl[1] if b == b0 else 0 for b in bands)
        drawn = signal_draws(p, n, bands, snr, nsamp, window=window, lags_too=True, alphas=al_vec)
        if drawn is None:
            return None
        sig, lags = drawn
        noise = noise_block_maxima(p, n, bands, nsim=nsim, window=window,
                                   alphas=al_vec, lag_pads=lp_vec)
        memo = ("choose_t0", id(sig[0]), id(noise), chain[0], t0_cl, n, float(snr), float(fd),
                tuple(bands), win, int(nsim), int(nsamp))
    else:
        drawn = signal_draws(p, n, bands, snr, nsamp, window=window, lags_too=True, alphas=base_mat)
        if drawn is None:
            return None
        sig, lags = drawn
        noise = noise_block_maxima(p, n, bands, nsim=nsim, window=window, alphas=base_mat)
        memo = ("choose", id(sig[0]), id(noise), n, float(snr), float(fd), tuple(bands), win,
                int(nsim), int(nsamp))
    out = plan_chain(sig, noise, bands, list(chain), fd, cost, n, snr, memo=memo, lags=lags,
                     offsets=k0_chain)
    _cache_put(_PLAN_CACHE, key, out)
    _similar_put("plan", unit, sim_params, out)
    return out


_BOUND_PRICE_CACHE = OrderedDict()


def _cost_model_nonneg(cost):
    if any(v < 0.0 for v in cost.dense.values()):
        return False
    if any(v < 0.0 for _, v in cost._refine):
        return False
    if any(v < 0.0 for rows in cost._sparse.values() for _, v in rows):
        return False
    if any(sc["dense"] < 0.0 or sc["recheck"] < 0.0
           or any(v < 0.0 for _, v in sc.get("sparse", ()))
           for sc in cost.screen.values()):
        return False
    t0r = getattr(cost, "tier0_ratios", None)
    if t0r and any(not (0.0 < r <= 1.0) for r in t0r.values()):
        return False
    dlag = getattr(cost, "direct_lag", None)
    if dlag is not None:
        dfrac = getattr(cost, "direct_frac", 1.0)
        if not (0.0 <= dfrac <= 1.0) or getattr(cost, "direct_multi_frac", 0.0) < 0.0:
            return False
        if dlag < 0.0 or getattr(cost, "direct_base", 0.0) + dlag < 0.0:
            return False
    return True


def pair_cost_lower_bound(power, n, snr, fd, cost, max_tiers=3, floor=_MIN_BAND, nsim=None,
                          window=None, ntemplates=None, nsamp=None, max_cost=None):
    """Analytic lower bound on `choose_chain(...)[0]["cost"]` without Monte Carlo draws.

    Parameters
    ----------
    power : array_like
        Nonnegative filter-output power profile of length `n`.
    n : int
        Transform block length.
    snr : float
        Target detection signal-to-noise ratio.
    fd : float
        False-dismissal budget.
    cost : CostModel
        Calibrated tier and refine cost model at block length `n`.
    max_tiers : int, optional
        Maximum number of coarse gate tiers to consider (default `3`).
    floor : int, optional
        Minimum candidate coarse band size (default `_MIN_BAND`).
    nsim : int, optional
        Number of noise blocks in the gate model (default `model_draws(fd)[1]`).
    window : tuple of int, optional
        Searched fine-lag window `(start, end)` within `[0, n)`, or `None` for the whole block.
    ntemplates : int, optional
        Template count for GPU feed pricing (`CostModel.feed_delta`), or `None`.
    nsamp : int, optional
        Number of signal detections in the gate model (default `model_draws(fd)[0]`).
    max_cost : float, optional
        Optional branch-and-bound threshold. When provided, evaluation stops early as soon
        as a sound lower bound at or below `max_cost` is certified, while still returning a
        valid lower bound on the minimum pair cost across all chains.

    Returns
    -------
    float or None
        Conservative lower bound on the best searched chain cost per `(block, template)` pair,
        or `None` when `cost` is not a nonnegative `CostModel` or `fd` cannot be resolved.
    """
    if not isinstance(cost, CostModel) or not cost._refine or not _cost_model_nonneg(cost):
        return None
    p = _norm_profile(power, n)
    win = None if window is None else (int(window[0]), int(window[1]))
    dsamp, dsim = model_draws(fd)
    nsamp = dsamp if nsamp is None else int(nsamp)
    nsim = dsim if nsim is None else int(nsim)
    if nsamp is None or nsamp < 2 or nsim < 1:
        return None
    m_search = (int(nsamp) + 1) // 2
    m_fit = int(nsamp) // 2
    k_bud = int(round(float(fd) * (m_search + 1))) - 1
    fit_j = int(round(float(fd) * (m_fit + 1)))
    span_chk = n if win is None else (win[1] - win[0])
    if k_bud < 0 or fit_j < 1 or fit_j > m_fit or span_chk < 1:
        return None

    sig_p = _gm._profile_sig(p)
    _, k0_cand, bands = _cached_band_offsets(p, sig_p, n, floor)
    if not bands:
        return None

    # Check exact cache for previously computed lower bounds
    extra = (k0_cand,) if any(k0_cand) else ()
    feed_nt = None if not getattr(cost, "feed", None) else int(ntemplates or 0)
    price_params = (int(n), float(snr), float(fd), int(max_tiers), int(floor), int(nsim),
                    int(nsamp), win, _cost_sig(cost), feed_nt) + extra
    price_key = (sig_p,) + price_params
    if price_key in _BOUND_PRICE_CACHE:
        _BOUND_PRICE_CACHE.move_to_end(price_key)
        return _BOUND_PRICE_CACHE[price_key]

    # Build piecewise-monotone knot grid for CostModel tables
    has_feed = bool(ntemplates and getattr(cost, "feed", None))
    base_knots = {0.0, 1e-12, 1e-6, 0.05 - 1e-12, 0.05, float(_USELESS_PASS), 1.0}
    for f_k, _ in cost._refine:
        base_knots.add(float(f_k))
    for rows in cost._sparse.values():
        for f_k, _ in rows:
            base_knots.add(float(f_k))
    for sc in cost.screen.values():
        for f_k, _ in sc["excess"]:
            base_knots.add(float(f_k))
        for f_k, _ in sc.get("sparse", ()):
            base_knots.add(float(f_k))
    knots_tup = tuple(sorted(f_k for f_k in base_knots if 0.0 <= f_k <= 1.0))

    ft_memo = {}
    t0r = getattr(cost, "tier0_ratios", None)

    def _first_tier_lb(b0, f_lo, f_hi, multi_tier=False):
        ratio = t0r[b0] if (multi_tier and t0r and b0 in t0r) else 1.0
        key_ft = (b0, ratio, f_lo, f_hi)
        hit = ft_memo.get(key_ft)
        if hit is not None:
            return hit
        c_dense = cost.dense[int(b0)] * ratio
        sc = cost.screen.get(int(b0))
        if sc is None or not sc["excess"]:
            res = (c_dense, None, c_dense)
            ft_memo[key_ft] = res
            return res
        sr_lo = cost.screen_reach(b0, f_lo)
        sr_hi = cost.screen_reach(b0, f_hi)
        cq_min = sc["dense"] * ratio + min(sr_lo, sr_hi) * sc["recheck"]
        cq_max = sc["dense"] * ratio + max(sr_lo, sr_hi) * sc["recheck"]
        scr_lb = cq_min if cq_min <= c_dense * (1.0 + TIE) else None
        flt_lb = c_dense if cq_max > c_dense * (1.0 + TIE) else None
        c_min = min(scr_lb if scr_lb is not None else float("inf"),
                    flt_lb if flt_lb is not None else float("inf"))
        res = (c_min, scr_lb, flt_lb)
        ft_memo[key_ft] = res
        return res

    def _feed_min(chain):
        if not has_feed:
            return 0.0
        vals = [cost.feed_delta(chain, [1.0] * len(chain) + [0.0], ntemplates, None),
                cost.feed_delta(chain, [1.0] * len(chain) + [1.0], ntemplates, None)]
        if cost.prices_direct(chain):
            vals.append(cost.feed_delta(chain, [1.0] * len(chain) + [1.0], ntemplates, 1))
        return min(vals)

    # Zero-FFT tier-0 + feed floor across all candidate chains
    c0_floor_1 = {
        b: min(_first_tier_lb(b, knots_tup[i], knots_tup[i + 1], False)[0]
               for i in range(len(knots_tup) - 1))
        for b in bands
    }
    c0_floor_m = {
        b: min(_first_tier_lb(b, knots_tup[i], knots_tup[i + 1], True)[0]
               for i in range(len(knots_tup) - 1))
        for b in bands
    }
    all_chains = enumerate_chains(n, max_tiers, floor, bands=bands)
    if not all_chains:
        return None
    min_all_floor = min(
        (c0_floor_m[ch[0]] if len(ch) > 1 else c0_floor_1[ch[0]]) + _feed_min(ch)
        for ch in all_chains
    )
    out_val = min_all_floor if math.isfinite(min_all_floor) else None
    if max_cost is None or (out_val is not None and out_val <= float(max_cost)):
        _cache_put(_BOUND_PRICE_CACHE, price_key, out_val)
    return out_val


def rebin_profile(fine, delta_f, data_rate, n):
    """A fine-grid output-power profile (spacing delta_f) on block size n's bins, normalised."""
    fine = np.asarray(fine, np.float64)
    ratio = max(int(round((data_rate / n) / float(delta_f))), 1)
    keep = (len(fine) // ratio) * ratio
    binned = fine[:keep].reshape(-1, ratio).sum(axis=1)
    out = np.zeros(n)
    k = min(len(binned), n // 2 + 1)
    out[:k] = binned[:k]
    tot = out.sum()
    return out / tot if tot > 0 else None


_PRICE_CACHE = OrderedDict()


