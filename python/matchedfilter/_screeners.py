"""Shared screeners: one coarse vector that screens a group of alike templates in place of
each template's own.

A leaf bank's templates over a first band are paired, then merged into groups of up to 16,
each with a screener every member overlaps well (cluster_tier0_candidates); a group's
members can be paired again at the next band (cluster_tier1_from_tier0). The compiled
routines do the work (_core.tier0_match, tier0_pair_level, tier0_pass; src/tier0_*.cc); this
module prepares the band's vectors for them and packs what they return. The planner prices
a chain with the screeners' retentions (gatechain.choose_chain)."""
import math
from typing import NamedTuple, Optional

import numpy as np

from . import _core
from .gatechain import _band_slice, _norm_profile


class Tier0Cluster(NamedTuple):
    """Precomputed Tier-0 coarse screener bank and calibration parameters. The thresholds
    are solved for one retention, alpha (from the members' mean less half their spread);
    member_alphas holds each template's own, which tools/fdr_audit.py --bank models a plan's
    dismissal with. A Tier-1 sub-screener bank (cluster_tier1_from_tier0) has the same form,
    with alpha its members' smallest retention."""
    specs: np.ndarray
    offsets: np.ndarray
    members: np.ndarray
    lag_pad: int
    ratio: float
    alpha: float
    member_alphas: Optional[np.ndarray] = None


class _BandSetup(NamedTuple):
    """A bank's templates over one band, as the shared-screener code works on them."""
    nt: int                    # templates
    k_lo: int                  # the band's first fine bin
    length: int                # its bins
    C: np.ndarray              # (nt, length) complex128: the band's bins over sqrt(its power)
    W: np.ndarray              # (length,) float64 weights of the inner product
    v: np.ndarray              # (nt,) each template's variance, sum_k W |C|^2
    valid: np.ndarray          # (nt,) bool, v > 0
    inv_sqrt_v: np.ndarray     # (nt,) 1 / sqrt(v), 0 where not valid
    U64: np.ndarray            # (nt, length) complex64 unit vectors, C sqrt(W) / sqrt(v)
    WC64: np.ndarray           # (nt, length) complex64 W C / sqrt(v)
    W32: np.ndarray            # (length,) float32 W
    R: int                     # fine samples a coarse one, n / band
    s_step: int                # lags between coarse shifts
    exp_all: np.ndarray        # (2 R + 1, length) complex128: lag d turns a vector by row d + R
    exp_all64: np.ndarray      # the same, complex64
    dls: np.ndarray            # the coarse shifts' lags, ascending
    dls_ord: np.ndarray        # the same from 0 outwards, the order they are tried in
    Sr: np.ndarray             # (shifts, length) float32, the coarse shifts' real parts ...
    Si: np.ndarray             # ... and imaginary parts, in that order


def _band_setup(spectra, power, n, band, k0):
    """The templates of `spectra` over the band of `band` bins at offset `k0`, weighted by the
    profile `power` over the templates' mean power there, with the lag tables the pair
    scoring and the lag refinement read; None where the band holds nothing to work on.

    Parameters
    ----------
    spectra : array_like
        ``(nt, bins)`` complex template spectra.
    power : array_like
        Expected filter-output power of length ``n``.
    n, band, k0 : int
        Block length, the band's transform length (it divides ``n``, below ``n // 2``), and
        the band's starting bin.

    Returns
    -------
    _BandSetup or None
    """
    H = np.asarray(spectra)
    if H.ndim != 2 or H.shape[0] < 2 or band < 1 or band >= n // 2 or n % band != 0:
        return None
    nt = int(H.shape[0])
    p = _norm_profile(np.asarray(power, dtype=np.float32), n)
    k_lo, k_hi = _band_slice(n, band, k0)
    length = k_hi - k_lo
    if length <= 0 or k_hi > H.shape[1]:
        return None
    p_band = p[k_lo:k_hi]
    total = float(p_band.sum())
    if total <= 0.0:
        return None
    # Scale-free inverse-PSD weights W_k from the profile over the templates' mean |H[k]|^2
    H_band = np.asarray(H[:, k_lo:k_hi], dtype=np.complex128)
    C = H_band * (1.0 / math.sqrt(total))
    m_bin = (H_band.real * H_band.real + H_band.imag * H_band.imag).mean(axis=0)
    m_max = float(m_bin.max())
    if m_max <= 0.0:
        return None
    W = p_band / np.maximum(m_bin, 1e-6 * m_max)
    v = np.sum((C.real * C.real + C.imag * C.imag) * W[None, :], axis=1)
    valid = v > 0.0
    inv_sqrt_v = np.zeros(nt, dtype=np.float64)
    inv_sqrt_v[valid] = 1.0 / np.sqrt(v[valid])
    U64 = (C * (inv_sqrt_v[:, None] * np.sqrt(W)[None, :])).astype(np.complex64)
    WC64 = (W[None, :] * C * inv_sqrt_v[:, None]).astype(np.complex64)
    # Lags -R .. R, and the coarse shifts among them from lag 0 outwards (of two as far from
    # 0, the negative first)
    R = n // band
    s_step = max(1, R // 8)
    all_dls = np.arange(-R, R + 1, dtype=np.int64)
    k_idx = np.arange(k_lo, k_hi, dtype=np.float64)
    exp_all = np.exp((-2j * np.pi / n) * (all_dls[:, None] * k_idx[None, :]))
    exp_all64 = exp_all.astype(np.complex64)
    dls = all_dls[::s_step]
    order = np.argsort(np.abs(dls), kind="stable")
    shifts_ord = exp_all64[::s_step][order]
    return _BandSetup(nt, k_lo, length, C, W, v, valid, inv_sqrt_v, U64, WC64, W.astype(np.float32),
                      R, s_step, exp_all, exp_all64, dls, dls[order],
                      np.ascontiguousarray(shifts_ord.real, dtype=np.float32),
                      np.ascontiguousarray(shifts_ord.imag, dtype=np.float32))


def _band_slots(vectors, band, k0, k_lo):
    """Band vectors (rows of the band's bins from `k_lo` up) in the `band` slots the coarse
    transform reads them from: as they are for a band at 0, wrapped for a band at `k0`."""
    length = vectors.shape[1]
    out = np.zeros((vectors.shape[0], band), dtype=np.complex64)
    if k0 <= 0:
        out[:, :length] = vectors
    else:
        first_slot = k_lo & (band - 1)
        first = min(length, band - first_slot)
        if first > 0:
            out[:, first_slot:first_slot + first] = vectors[:, :first]
        if length > first:
            out[:, :length - first] = vectors[:, first:]
    return out


def cluster_tier0_candidates(spectra, power, n, band, k0=0, rho_min=0.90, max_arity=4,
                             pass2=None):
    """Build hierarchical Tier-0 screener banks up to ``max_arity`` (``k <= 2, 4, 8, 16``).

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
        Maximum cluster arity in ``2 .. 16`` (default ``4``).
    pass2 : callable, optional
        Called with the preceding pass's ``Tier0Cluster`` before each pass ``>= 2``; further
        passes run only when it returns True (default ``None``: always).

    Returns
    -------
    tuple of (Tier0Cluster or None, ...)
        Candidate ``Tier0Cluster`` tuple across hierarchical passes (2-tuple ``(cl_k2, cl_k4)``
        when ``max_arity <= 4``, 3-tuple up to ``k <= 8``, 4-tuple up to ``k <= 16``).
    """
    n, b0, k0 = int(n), int(band), int(k0)
    cap_arity = int(max_arity)
    if cap_arity < 2:
        raise ValueError("max_arity must be >= 2")
    cap_arity = min(cap_arity, 16)
    # At least 2 output slots so max_arity=2 preserves the (cl_k2, None) 2-tuple contract
    num_slots = max(2, int(math.ceil(math.log2(cap_arity))))
    empty_ret = (None,) * num_slots
    setup = _band_setup(spectra, power, n, b0, k0)
    if setup is None or np.count_nonzero(setup.valid) < 2:
        return empty_ret
    (nt, k_lo, length, C, W, v, valid, inv_sqrt_v, U64, WC64, W32, R, s_step, exp_all, exp_all64,
     dls, dls_ord, Sr, Si) = setup
    sqrt_W = np.sqrt(W)
    shifts64 = np.ascontiguousarray(exp_all64[::s_step])

    # Order valid templates by mean in-band frequency so neighbors fall in one L1/L2 chunk
    valid_idx = np.flatnonzero(valid)
    u_pow = U64.real * U64.real + U64.imag * U64.imag
    k_f32 = np.arange(k_lo, k_lo + length, dtype=np.float64).astype(np.float32)
    f_mean = np.sum(u_pow[valid_idx] * k_f32[None, :], axis=1)
    perm = valid_idx[np.argsort(f_mean, kind="stable")]
    coarse_rho_floor = float(rho_min) * (0.90 if s_step > 1 else 1.0)
    floor2 = coarse_rho_floor * coarse_rho_floor

    l2_b = int(_core.l2_bytes()) or 262144
    chunk_size = max(48, min(192, ((l2_b * 3 // 4) // (16 * max(length, 1)) // 16) * 16))
    match_lags = np.ascontiguousarray(dls_ord, dtype=np.int64)

    def _run_chunked_matching(order_idx, U_arr, v_arr, f2_floor, sizes=None, size_cap=2):
        # The nodes' pairs (_core.tier0_match): a chunk of neighbours at a time scored,
        # matched greedily and its left-overs placed by breaking a pair, then the chunks'
        # left-overs matched once more. Returns (smaller index, larger, lag of the larger).
        half = int(order_idx.size) // 2
        out_a = np.empty(half, dtype=np.int32)
        out_b = np.empty(half, dtype=np.int32)
        out_dl = np.empty(half, dtype=np.int64)
        count = _core.tier0_match(
            np.ascontiguousarray(order_idx, dtype=np.int64), U_arr, v_arr, Sr, Si, match_lags,
            float(f2_floor), sizes, int(size_cap), int(chunk_size), out_a, out_b, out_dl)
        return out_a[:count], out_b[:count], out_dl[:count]

    def _pack_cluster(bvecs_c64, offs_i32, mems_i32, alphas_arr, max_dl):
        # A level as a Tier0Cluster, its members' retentions measured as the engine meets
        # them (k <= 4 members at 0.96 at their build lag met the engine at ~0.99)
        nc_out = int(offs_i32.size) - 1
        specs_out = _band_slots(bvecs_c64, b0, k0, k_lo)
        lpad = int((max_dl + R - 1) // R) if max_dl > 0 else 0
        alphas_arr = _screener_retention(bvecs_c64, offs_i32, mems_i32, alphas_arr, lpad,
                                         W32, WC64, exp_all64, R, v)
        rat = round((nc_out / float(nt)) * 20.0) / 20.0
        raw_a = float(np.mean(alphas_arr) - 0.5 * np.std(alphas_arr))
        eff_a = max(0.5, min(1.0, math.floor(raw_a * 200.0 + 1e-9) / 200.0))
        return Tier0Cluster(specs=specs_out, offsets=offs_i32, members=mems_i32,
                            lag_pad=lpad, ratio=rat, alpha=eff_a,
                            member_alphas=np.asarray(alphas_arr, np.float32))

    # The first level (_core.tier0_pair_level): the templates' pairs, their lags refined in
    # complex128, made clusters of two where the two are coherent to rho_min, with the
    # pair's screener and its members' retentions; every other template a cluster of its own
    pa, pb, pdl = _run_chunked_matching(perm, U64, v, floor2)
    level_128 = np.empty((nt, length), dtype=np.complex128)
    level_v = np.empty(nt, dtype=np.float64)
    level_dl = np.empty(nt, dtype=np.int64)
    level_offsets = np.empty(nt + 1, dtype=np.int32)
    members = np.empty(nt, dtype=np.int32)
    alphas = np.empty(nt, dtype=np.float64)
    nc, max_abs_dl = _core.tier0_pair_level(
        C, inv_sqrt_v, v, W, exp_all, int(s_step - 1), float(rho_min), int(0.85 * nt),
        pa, pb, pdl, level_128, level_v, level_dl, level_offsets, members, alphas)
    if nc == 0:
        return empty_ret
    # The current level: its clusters' vectors, variances, lags and CSR partition
    cur_nc = nc
    cur_vecs_128 = level_128[:nc]
    cur_v, cur_dl, cur_offsets = level_v[:nc], level_dl[:nc], level_offsets[:nc + 1]
    cur_members, cur_alphas = members, alphas

    prev_cl = _pack_cluster(cur_vecs_128.astype(np.complex64), cur_offsets, cur_members,
                            cur_alphas, max_abs_dl)
    out_levels = [prev_cl]
    if cap_arity <= 2:
        return tuple(out_levels + [None] * (num_slots - len(out_levels)))

    # Passes 2..num_slots: iterative hierarchical matching + minimax weight synthesis up to cap_arity
    alpha_floor = max(0.88, min(0.93, float(rho_min) + 0.03))
    rho_min_hi = max(0.84, float(rho_min) - 0.05)
    coarse_floor_hi = rho_min_hi * (0.90 if s_step > 1 else 1.0)
    f2_hi = coarse_floor_hi * coarse_floor_hi

    pass_lags = np.ascontiguousarray(dls)
    for p_idx in range(2, num_slots + 1):
        if cur_nc < 2 or (pass2 is not None and not pass2(prev_cl)):
            break
        pass_cap = min(cap_arity, 1 << p_idx)
        sz_cur = cur_offsets[1:] - cur_offsets[:-1]
        valid_cur = (cur_v > 0.0) & (sz_cur < pass_cap)
        valid_cur_idx = np.flatnonzero(valid_cur)
        if valid_cur_idx.size < 2:
            break

        inv_sqrt_vc = np.zeros(cur_nc, dtype=np.float64)
        inv_sqrt_vc[valid_cur] = 1.0 / np.sqrt(cur_v[valid_cur])
        Uc_64 = (cur_vecs_128 * (inv_sqrt_vc[:, None] * sqrt_W[None, :])).astype(np.complex64)
        uc_pow = Uc_64.real * Uc_64.real + Uc_64.imag * Uc_64.imag
        f_meanc = np.sum(uc_pow[valid_cur_idx] * k_f32[None, :], axis=1)
        permc = valid_cur_idx[np.argsort(f_meanc, kind="stable")]

        ca_arr, cb_arr, cdl_arr = _run_chunked_matching(
            permc, Uc_64, cur_v, f2_hi, sizes=sz_cur, size_cap=pass_cap
        )
        if not ca_arr.size:
            break
        ca_arr, cb_arr = ca_arr.astype(np.int64), cb_arr.astype(np.int64)

        # The next level (_core.tier0_pass): every candidate merge's members aligned in the
        # two clusters' common frame and their screener synthesised; a merge whose members
        # all keep alpha_floor of their SNR replaces its two clusters
        next_128 = np.empty((cur_nc, length), dtype=np.complex128)
        next_v = np.empty(cur_nc, dtype=np.float64)
        next_dl = np.empty(cur_nc, dtype=np.int64)
        next_offsets = np.empty(cur_nc + 1, dtype=np.int32)
        members_hi = np.empty(nt, dtype=np.int32)
        alphas_hi = cur_alphas.copy()
        merged, max_dl_hi = _core.tier0_pass(
            C, inv_sqrt_v, v, W, exp_all, shifts64, pass_lags, int(s_step - 1), cur_vecs_128,
            inv_sqrt_vc, cur_v, cur_dl, cur_offsets, cur_members, ca_arr, cb_arr, cdl_arr,
            2 * p_idx, alpha_floor,
            next_128, next_v, next_dl, next_offsets, members_hi, alphas_hi)
        if not merged:
            break
        # The merged level becomes the current one
        cur_nc -= merged
        cur_vecs_128 = next_128[:cur_nc]
        cur_v, cur_dl, cur_offsets = next_v[:cur_nc], next_dl[:cur_nc], next_offsets[:cur_nc + 1]
        cur_members, cur_alphas = members_hi, alphas_hi
        prev_cl = _pack_cluster(cur_vecs_128.astype(np.complex64), cur_offsets, cur_members,
                                cur_alphas, max_dl_hi)
        out_levels.append(prev_cl)

    return tuple(out_levels + [None] * (num_slots - len(out_levels)))


def cluster_tier0_templates(spectra, power, n, band, k0=0, rho_min=0.90, max_arity=2):
    """Build a lag-and-phase-aligned Tier-0 coarse screener bank up to ``max_arity``.

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
        Maximum templates merged into a single screener in ``{2, 3, 4}`` (default ``2``).

    Returns
    -------
    Tier0Cluster or None
        Precomputed screener spectra ``(nt0, b0)``, CSR ``offsets`` ``(nt0 + 1,)``,
        ``members`` ``(nt,)``, coarse window ``lag_pad``, quantized count ``ratio``,
        and conservative signal-retention factor ``alpha``, or ``None`` when ``nt < 2``
        or fewer than 15% of templates merge.
    """
    cands = cluster_tier0_candidates(
        spectra, power, n, band, k0=k0, rho_min=rho_min, max_arity=max_arity
    )
    if int(max_arity) <= 2:
        return cands[0]
    best = None
    for cl in cands:
        if cl is not None:
            best = cl
    return best


def _screener_retention(bvecs, offsets, members, alphas, lag_pad, W32, WC64, exp_all64, R, v):
    """Each clustered member's retention as the engine meets it.

    The retention is the peak, over the lags the screener's padded window reaches
    (``|lag| <= lag_pad * R`` fine samples), of the screener's overlap with the member, in the
    member's variance units: ``alpha = sqrt(v_c / v_t) |<c, u_t>|`` for unit ``c`` and ``u_t``.
    The overlap at the one lag a member was aligned at when the screener was built is only a
    lower bound: the screener blends members, and its cross-correlation with a member can peak
    elsewhere.

    Parameters
    ----------
    bvecs : numpy.ndarray
        ``(nc, length)`` complex64 in-band screener vectors.
    offsets, members : numpy.ndarray
        CSR partition of the templates into the ``nc`` screeners.
    alphas : array_like
        ``(nt,)`` starting retentions; singletons keep theirs.
    lag_pad : int
        Coarse lags of padding the engine searches around each screener's window.
    W32 : numpy.ndarray
        ``(length,)`` float32 inverse-PSD weights.
    WC64 : numpy.ndarray
        ``(nt, length)`` complex64 ``W * C_t / sqrt(v_t)``.
    exp_all64 : numpy.ndarray
        ``(2R + 1, length)`` complex64 fine-lag phase ramps for lags ``-R .. R``.
    R : int
        Fine samples per coarse sample.
    v : numpy.ndarray
        ``(nt,)`` weighted member variances.

    Returns
    -------
    numpy.ndarray
        ``(nt,)`` float64 retentions, at most 1.
    """
    cid = np.repeat(np.arange(offsets.size - 1), np.diff(offsets))
    sizes = np.diff(offsets)[cid]
    out = np.asarray(alphas, dtype=np.float64).copy()
    multi = np.flatnonzero(sizes > 1)
    if multi.size == 0:
        return out
    t_m = members[multi]
    B64 = bvecs[cid[multi]]
    v_c = np.sum((B64.real * B64.real + B64.imag * B64.imag) * W32[None, :], axis=1, dtype=np.float64)
    reach = min(R, int(lag_pad) * R)
    taus64 = exp_all64[R - reach:R + reach + 1]
    prod64 = B64.conj() * WC64[t_m]
    ov = np.max(np.abs(prod64 @ taus64.T), axis=1).astype(np.float64) / np.sqrt(np.maximum(v_c, 1e-300))
    out[t_m] = np.minimum(1.0, np.sqrt(v_c / v[t_m]) * ov)
    return out


def _pairs_within_clusters(offsets, members, valid, U64, v, Sr, Si, dls_ord, floor2):
    """Pair the valid members of each multi-member cluster greedily by coherence.

    Every pair of a cluster's members is scored over the coarse shifts
    (``_core.tier0_pair_scores``); the pairs whose squared coherence reaches ``floor2`` are
    taken best first, each member at most once.

    Returns
    -------
    tuple of list
        ``(first, second, lag)``: per pair the smaller template index, the larger, and the
        coarse-shift lag of the larger against the smaller.
    """
    pa_l, pb_l, dl_l = [], [], []
    for c0 in range(offsets.size - 1):
        grp = members[offsets[c0]:offsets[c0 + 1]]
        grp = grp[valid[grp]]
        m_g = int(grp.size)
        if m_g < 2:
            continue
        U_g = U64[grp]
        r2 = np.empty((m_g, m_g), dtype=np.float32)
        bs = np.empty((m_g, m_g), dtype=np.int32)
        _core.tier0_pair_scores(np.ascontiguousarray(U_g.real), np.ascontiguousarray(U_g.imag),
                                Sr, Si, np.ascontiguousarray(v[grp], dtype=np.float64), r2, bs)
        ia, ib = np.nonzero(r2 >= floor2)
        used = np.zeros(m_g, dtype=bool)
        for e in np.argsort(-r2[ia, ib], kind="stable"):
            a, b = int(ia[e]), int(ib[e])
            if used[a] or used[b]:
                continue
            used[a] = used[b] = True
            dl = int(dls_ord[bs[a, b]])
            ta, tb = int(grp[a]), int(grp[b])
            pa_l.append(min(ta, tb))
            pb_l.append(max(ta, tb))
            dl_l.append(dl if ta < tb else -dl)
    return pa_l, pb_l, dl_l


#: Smallest member retention a Tier-1 sub-screener may have (cluster_tier1_from_tier0).
TIER1_ALPHA_MIN = 0.995


def cluster_tier1_from_tier0(spectra, power, n, tier0_cluster, band1, k0=0, rho_min=0.985,
                             alpha_min=TIER1_ALPHA_MIN):
    """Build a Tier-1 sub-screener bank by pairing members inside each Tier-0 cluster.

    Pairs are scored at band ``band1`` with the same C kernels Tier-0 clustering uses
    (``_core.tier0_pair_scores`` over coarse shifts, ``_core.tier0_refine_lags`` for the exact
    fine lag), matched greedily by coherence within each multi-member Tier-0 cluster, and
    merged into unit-variance screeners. Each merged member's retention is then measured as the
    engine meets it (:func:`_screener_retention`), and any pair with a member below
    ``alpha_min`` is split again, so the threshold model's Tier-1 loss stays small and is
    passed to :func:`chain_thresholds` (``tier1_cluster``) exactly.

    Parameters
    ----------
    spectra : array_like
        Complex frequency-domain template bank of shape ``(nt, k_bins)``.
    power : array_like
        Expected nonnegative filter-output power profile of length ``n``.
    n : int
        Full fine FFT block length.
    tier0_cluster : Tier0Cluster
        Active Tier-0 screener bank; only its multi-member clusters are split further.
    band1 : int
        Tier-1 coarse FFT band length ``b1`` (must divide ``n`` and be ``< n // 2``).
    k0 : int, optional
        Starting fine bin offset of Tier 1 (default ``0``).
    rho_min : float, optional
        Minimum PSD-weighted in-band coherence at ``band1`` to merge a pair (default ``0.985``).
    alpha_min : float, optional
        Minimum measured member retention a merged pair must keep (default
        ``TIER1_ALPHA_MIN`` = 0.995).

    Returns
    -------
    Tier0Cluster or None
        Tier-1 sub-screener bank (``specs`` ``(nc1, b1)``, CSR ``offsets``/``members`` nested
        inside ``tier0_cluster``'s clusters, ``lag_pad``, ``alpha`` = smallest member
        retention, ``member_alphas``), or ``None`` when no pair merges.
    """
    if tier0_cluster is None:
        return None
    n, b1, k0 = int(n), int(band1), int(k0)
    setup = _band_setup(spectra, power, n, b1, k0)
    if setup is None:
        return None
    (nt, k_lo, length, C, W, v, valid, inv_sqrt_v, U64, WC64, W32, R1, s_step, exp_all, exp_all64,
     dls, dls_ord, Sr, Si) = setup
    off0 = np.asarray(tier0_cluster.offsets, dtype=np.int32)
    mem0 = np.asarray(tier0_cluster.members, dtype=np.int32)
    if off0.size < 2 or int(mem0.size) != nt or not np.any(np.diff(off0) >= 2):
        return None
    coarse_floor = float(rho_min) * (0.90 if s_step > 1 else 1.0)
    floor2 = coarse_floor * coarse_floor

    pa_l, pb_l, dl_l = _pairs_within_clusters(off0, mem0, valid, U64, v, Sr, Si, dls_ord,
                                              floor2)
    if not pa_l:
        return None

    # Exact fine lag and coherence per pair, then keep pairs at rho_min
    pa = np.asarray(pa_l, dtype=np.int32)
    pb = np.asarray(pb_l, dtype=np.int32)
    Ca_u = C[pa] * inv_sqrt_v[pa, None]
    Cb_u = C[pb] * inv_sqrt_v[pb, None]
    prod_ab = np.ascontiguousarray((W[None, :] * Ca_u.conj()) * Cb_u, dtype=np.complex128)
    pdl = np.empty(pa.size, dtype=np.int64)
    g = np.empty(pa.size, dtype=np.complex128)
    _core.tier0_refine_lags(prod_ab, exp_all, np.asarray(dl_l, dtype=np.int64), int(R1),
                            int(s_step - 1) if s_step > 1 else 0, pdl, g)
    rho = np.abs(g)
    keep = rho >= float(rho_min)
    if not np.any(keep):
        return None
    pa, pb, pdl, g, rho = pa[keep], pb[keep], pdl[keep], g[keep], rho[keep]
    Ca_u, Cb_u = Ca_u[keep], Cb_u[keep]

    # Unit-variance pair screeners (cluster_tier0_candidates' Pass-1 synthesis)
    target_v = 0.5 * (v[pa] + v[pb])
    pair_vecs = ((np.sqrt(target_v / (2.0 * (1.0 + rho))))[:, None]
                 * (Ca_u + (g.conj() / rho)[:, None] * (Cb_u * exp_all[pdl + R1]))
                 ).astype(np.complex64)

    def _assemble(sel):
        # CSR layout in Tier-0 cluster order (so Tier-1 clusters nest), merged pairs first
        partner = np.full(nt, -1, dtype=np.int64)
        slot = np.full(nt, -1, dtype=np.int64)
        idx = np.flatnonzero(sel)
        partner[pa[idx]] = pb[idx]
        partner[pb[idx]] = pa[idx]
        slot[pa[idx]] = idx
        vecs, offs, mems = [], [0], []
        for c0 in range(off0.size - 1):
            grp = mem0[off0[c0]:off0[c0 + 1]]
            for t in grp:
                t = int(t)
                if slot[t] >= 0:
                    vecs.append(pair_vecs[slot[t]])
                    mems.extend((t, int(partner[t])))
                    offs.append(len(mems))
            for t in grp:
                t = int(t)
                if partner[t] < 0:
                    vecs.append(C[t].astype(np.complex64))
                    mems.append(t)
                    offs.append(len(mems))
        max_dl = int(np.max(np.abs(pdl[idx]))) if idx.size else 0
        lpad = int((max_dl + R1 - 1) // R1) if max_dl > 0 else 0
        bvecs = np.asarray(vecs, dtype=np.complex64)
        offs_i32 = np.asarray(offs, dtype=np.int32)
        mems_i32 = np.asarray(mems, dtype=np.int32)
        alphas = _screener_retention(bvecs, offs_i32, mems_i32, np.ones(nt), lpad,
                                     W32, WC64, exp_all64, R1, v)
        return bvecs, offs_i32, mems_i32, lpad, alphas

    # Measure retentions; split pairs with a member below alpha_min until all remaining keep it
    sel = np.ones(pa.size, dtype=bool)
    while True:
        bvecs, offs_i32, mems_i32, lpad, alphas = _assemble(sel)
        bad = sel & ((alphas[pa] < float(alpha_min)) | (alphas[pb] < float(alpha_min)))
        if not np.any(bad):
            break
        sel &= ~bad
        if not np.any(sel):
            return None

    nc1 = int(offs_i32.size) - 1
    specs_out = _band_slots(bvecs, b1, k0, k_lo)
    a_min = float(np.min(alphas))
    return Tier0Cluster(
        specs=specs_out,
        offsets=offs_i32,
        members=mems_i32,
        lag_pad=lpad,
        ratio=round((nc1 / float(nt)) * 20.0) / 20.0,
        alpha=math.floor(a_min * 1000.0 + 1e-9) / 1000.0,
        member_alphas=np.asarray(alphas, dtype=np.float32),
    )
