"""cluster_tier1_from_tier0 pairs the members of each Tier-0 cluster in compiled code
(_core.tier0_pairs_within) and lays the sub-screeners out with whole-array operations. Its
result is checked, bit for bit, against the Python code it replaced, kept here."""
import math

import numpy as np
import pytest

from matchedfilter import _core, _screeners
from matchedfilter import _gatedraws as gd
from spectral_profiles import make_spectral_profile


def _reference_tier1(spectra, power, n, tier0_cluster, band1, k0=0, rho_min=0.985,
                     alpha_min=_screeners.TIER1_ALPHA_MIN):
    """The Tier-1 sub-screener bank as the Python loops built it (pairs greedily matched in each
    Tier-0 cluster, merged, and split again while a member keeps less than alpha_min).

    Parameters
    ----------
    spectra : numpy.ndarray
        ``(nt, bins)`` complex template spectra.
    power : numpy.ndarray
        Expected filter-output power of length ``n``.
    n : int
        Block length.
    tier0_cluster : Tier0Cluster
        The Tier-0 screener bank whose clusters are split.
    band1 : int
        The Tier-1 band.
    k0 : int, optional
        The Tier-1 band's offset (default 0).
    rho_min : float, optional
        Least coherence of a merged pair (default 0.985).
    alpha_min : float, optional
        Least retention of a merged member (default TIER1_ALPHA_MIN).

    Returns
    -------
    Tier0Cluster or None
        The sub-screener bank, or None when no pair merges.
    """
    n, b1, k0 = int(n), int(band1), int(k0)
    setup = _screeners._band_setup(spectra, power, n, b1, k0)
    (nt, k_lo, length, C, W, v, valid, inv_sqrt_v, U64, WC64, W32, R1, s_step, exp_all, exp_all64,
     dls, dls_ord, Sr, Si) = setup
    off0 = np.asarray(tier0_cluster.offsets, dtype=np.int32)
    mem0 = np.asarray(tier0_cluster.members, dtype=np.int32)
    coarse_floor = float(rho_min) * (0.90 if s_step > 1 else 1.0)
    floor2 = coarse_floor * coarse_floor
    # each cluster's pairs, every score exact (floor 0), taken best first
    pa_l, pb_l, dl_l = [], [], []
    for c0 in range(off0.size - 1):
        grp = mem0[off0[c0]:off0[c0 + 1]]
        grp = grp[valid[grp]]
        m_g = int(grp.size)
        if m_g < 2:
            continue
        U_g = U64[grp]
        r2 = np.empty((m_g, m_g), dtype=np.float32)
        bs = np.empty((m_g, m_g), dtype=np.int32)
        _core.tier0_pair_scores(np.ascontiguousarray(U_g.real), np.ascontiguousarray(U_g.imag),
                                Sr, Si, np.ascontiguousarray(v[grp], dtype=np.float64), 0.0,
                                r2, bs)
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
    if not pa_l:
        return None
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
    target_v = 0.5 * (v[pa] + v[pb])
    pair_vecs = ((np.sqrt(target_v / (2.0 * (1.0 + rho))))[:, None]
                 * (Ca_u + (g.conj() / rho)[:, None] * (Cb_u * exp_all[pdl + R1]))
                 ).astype(np.complex64)

    def assemble(sel):
        # CSR layout in Tier-0 cluster order, merged pairs first, one template at a time
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
        alphas = _screeners._screener_retention(bvecs, offs_i32, mems_i32, np.ones(nt), lpad,
                                                W32, WC64, exp_all64, R1, v)
        return bvecs, offs_i32, mems_i32, lpad, alphas

    sel = np.ones(pa.size, dtype=bool)
    while True:
        bvecs, offs_i32, mems_i32, lpad, alphas = assemble(sel)
        bad = sel & ((alphas[pa] < float(alpha_min)) | (alphas[pb] < float(alpha_min)))
        if not np.any(bad):
            break
        sel &= ~bad
        if not np.any(sel):
            return None
    nc1 = int(offs_i32.size) - 1
    return _screeners.Tier0Cluster(
        specs=_screeners._band_slots(bvecs, b1, k0, k_lo), offsets=offs_i32, members=mems_i32,
        lag_pad=lpad, ratio=round((nc1 / float(nt)) * 20.0) / 20.0,
        alpha=math.floor(float(np.min(alphas)) * 1000.0 + 1e-9) / 1000.0,
        member_alphas=np.asarray(alphas, dtype=np.float32))


def _bank(seed, nt=96, n=1024):
    """Chirp-like templates on an inspiral profile, in close families: every fourth one a near
    copy of its neighbour at a small lag, so Tier 1 has pairs to merge and pairs to split."""
    power = make_spectral_profile("inspiral_canonical", n).astype(np.float64)
    rng = np.random.default_rng(seed)
    k = np.arange(n)
    chirp = (np.maximum(k, 4) / 64.0) ** (-5.0 / 3.0) * (k < n // 2)
    phase = (np.sort(rng.uniform(-1, 1, nt)) * 2.5)[:, None] * chirp[None, :] \
        + rng.uniform(0, 2 * np.pi, nt)[:, None]
    phase[1::4] = phase[0::4] + rng.normal(0.0, 0.03, (nt // 4, n)) + (2 * np.pi * 2 / n) * k
    spectra = (np.sqrt(power)[None, :] * np.exp(1j * phase)).astype(np.complex64)
    return power, spectra


@pytest.mark.parametrize("seed,alpha_min", [(5, _screeners.TIER1_ALPHA_MIN), (6, 0.97), (5, 0.999),
                                            (7, 0.9995)])
def test_tier1_bank_is_the_one_the_python_loops_built(seed, alpha_min):
    """The same bank, bit for bit, with the default floor, a looser one, and floors that split
    some merged pairs again (0.999, 0.9995 on these banks)."""
    n, b0, b1 = 1024, 64, 128
    power, spectra = _bank(seed, n=n)
    cl0 = _screeners.cluster_tier0_templates(spectra, power, n, b0,
                                             k0=int(gd.band_offset(power, n, b0)), max_arity=16)
    assert cl0 is not None and np.any(np.diff(cl0.offsets) >= 2)
    k0 = int(gd.band_offset(power, n, b1))
    new = _screeners.cluster_tier1_from_tier0(spectra, power, n, cl0, b1, k0=k0,
                                              alpha_min=alpha_min)
    ref = _reference_tier1(spectra, power, n, cl0, b1, k0=k0, alpha_min=alpha_min)
    assert ref is not None and new is not None
    sizes = np.diff(ref.offsets)
    assert np.any(sizes == 2) and np.any(sizes == 1)
    for field in ("specs", "offsets", "members", "member_alphas"):
        a, b = getattr(new, field), getattr(ref, field)
        assert a.dtype == b.dtype and np.array_equal(a, b), field
    assert (new.lag_pad, new.ratio, new.alpha) == (ref.lag_pad, ref.ratio, ref.alpha)


def test_pairs_within_refuses_a_member_listed_twice():
    """A member in two clusters could be paired twice and overrun the outputs: refused."""
    U = np.zeros((4, 8), np.complex64)
    S = np.ones((1, 8), np.float32)
    out = [np.empty(2, np.int32), np.empty(2, np.int32), np.empty(2, np.int64)]
    with pytest.raises(ValueError):
        _core.tier0_pairs_within(np.array([0, 2, 4], np.int32), np.array([0, 1, 1, 2], np.int32),
                                 np.ones(4, np.uint8), U, np.ones(4), S, S,
                                 np.zeros(1, np.int64), 0.5, *out)
