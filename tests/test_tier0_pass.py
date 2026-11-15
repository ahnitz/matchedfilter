"""_core.tier0_pass makes one pass of the shared-screener merging
(gatechain.cluster_tier0_candidates): every candidate merge of two clusters becomes a group
with one screener, or is turned down. Checked against the numpy code it replaced."""
import numpy as np
import pytest

from matchedfilter import _core


def _reference(C, inv_sqrt_v, v, W, exp_all, shifts64, dls, s_step, cur, inv_sqrt_vc,
               cur_offsets, cur_members, ca, cb, cdl, steps, alpha_floor):
    """The numpy implementation the C++ routine replaced. Returns every candidate's sorted
    members and, by candidate, an accepted group's (screener, mean variance, retentions,
    largest lag)."""
    R = (exp_all.shape[0] - 1) // 2
    length = C.shape[1]
    groups = [sorted(int(t) for c in (a, b) for t in cur_members[cur_offsets[c]:cur_offsets[c + 1]])
              for a, b in zip(ca, cb)]
    keep = [g for g, grp in enumerate(groups) if not v[grp].min() < 0.80 * v[grp].max()]
    accepted = {}
    if not keep:
        return groups, accepted
    ca_arr, cb_arr = ca[keep], cb[keep]
    cdl_arr = np.clip(cdl[keep], -R, R)
    ua = cur[ca_arr] * inv_sqrt_vc[ca_arr, None]
    ub_s = (cur[cb_arr] * inv_sqrt_vc[cb_arr, None]) * exp_all[cdl_arr + R]
    ip_ab = np.einsum("ij,ij->i", W[None, :] * ua.conj(), ub_s)
    abs_ip = np.abs(ip_ab)
    ph_ab = np.where(abs_ip > 1e-12, ip_ab.conj() / np.maximum(abs_ip, 1e-12), 1.0 + 0.0j)
    mid_raw = ua + ph_ab[:, None] * ub_s
    mid_norm = np.sqrt(np.maximum(
        np.sum((mid_raw.real * mid_raw.real + mid_raw.imag * mid_raw.imag) * W[None, :], axis=1),
        1e-30))
    mid_u = mid_raw / mid_norm[:, None]
    for row, g in enumerate(keep):
        grp = np.array(groups[g])
        unit = C[grp] * inv_sqrt_v[grp, None]
        prod = (W[None, :] * mid_u[row].conj()[None, :]) * unit
        dl = dls[np.argmax(np.abs(prod.astype(np.complex64) @ shifts64.T), axis=1)]
        best = np.full(grp.size, -1.0)
        fine = dl.copy()
        for off in range(-(s_step - 1), s_step):
            trial = np.clip(dl + off, -R, R)
            size = np.abs(np.einsum("ij,ij->i", prod, exp_all[trial + R]))
            better = size > best
            best, fine = np.where(better, size, best), np.where(better, trial, fine)
        U_raw = np.ascontiguousarray((unit * exp_all[fine + R])[None])
        c_unit = np.empty((1, length), np.complex128)
        overlap = np.empty((1, grp.size))
        _core.tier0_mwu(U_raw, np.ascontiguousarray(mid_u[row:row + 1]), W, steps, c_unit, overlap)
        v_bar = float(np.mean(v[grp]))
        alphas = np.minimum(1.0, np.sqrt(v_bar / v[grp]) * overlap[0])
        if alphas.min() >= alpha_floor:
            accepted[g] = (np.sqrt(v_bar) * c_unit[0], v_bar, alphas, int(np.max(np.abs(fine))))
    return groups, accepted


def _setting(seed, s_step, K=96, R=8, families=6):
    """`families` of four alike templates, each family two clusters of a pair; the candidate
    merges: every family's two clusters, one with a member of a variance too far from the
    rest, and two clusters of different families."""
    rng = np.random.default_rng(seed)
    k = np.arange(K)
    W = rng.uniform(0.5, 2.0, K)
    exp_all = np.exp((-2j * np.pi / 1024) * (np.arange(-R, R + 1)[:, None] * k[None, :]))
    C = np.empty((4 * families, K), np.complex128)
    for f in range(families):
        base = np.exp(1j * (rng.uniform(0, 2 * np.pi) + 40.0 * (f + 1) * (k / K) ** 2))
        for j in range(4):
            own = 0.12 * (rng.standard_normal(K) + 1j * rng.standard_normal(K))
            C[4 * f + j] = ((base + own) * exp_all[R + int(rng.integers(-5, 6))]
                            * np.exp(1j * rng.uniform(0, 2 * np.pi)) * rng.uniform(0.95, 1.05))
    C[7] *= 0.85                                         # variance 0.72 of its family's
    v = np.sum((C.real ** 2 + C.imag ** 2) * W, axis=1)
    inv_sqrt_v = 1.0 / np.sqrt(v)
    nc = 2 * families
    cur_offsets = np.arange(0, 4 * families + 1, 2, dtype=np.int32)
    cur_members = np.arange(4 * families, dtype=np.int32)
    cur_members[[0, 1]] = [1, 0]                         # a cluster's members need no order
    cur = C[0::2] + C[1::2]
    inv_sqrt_vc = 1.0 / np.sqrt(np.sum((cur.real ** 2 + cur.imag ** 2) * W, axis=1))
    ca = np.array(list(range(0, nc, 2)) + [1], np.int64)
    cb = np.array(list(range(1, nc, 2)) + [4], np.int64)
    cdl = rng.integers(-3, 4, ca.size).astype(np.int64)
    cdl[2] = 3 * R                                       # clipped to the lags there are
    dls = np.ascontiguousarray(np.arange(-R, R + 1, dtype=np.int64)[::s_step])
    shifts64 = np.ascontiguousarray(exp_all[::s_step].astype(np.complex64))
    return (C, inv_sqrt_v, v, W, exp_all, shifts64, dls, s_step, cur, inv_sqrt_vc, cur_offsets,
            cur_members, ca, cb, cdl)


def _run(args, steps, alpha_floor):
    (C, inv_sqrt_v, v, W, exp_all, shifts64, dls, s_step, cur, inv_sqrt_vc, cur_offsets,
     cur_members, ca, cb, cdl) = args
    sizes = np.diff(cur_offsets)
    total = int(sum(sizes[min(int(c), sizes.size - 1)] for c in list(ca) + list(cb)))
    out = dict(accepted=np.zeros(ca.size, bool), screener=np.empty((ca.size, C.shape[1]), np.complex128),
               v_bar=np.empty(ca.size), reach=np.empty(ca.size, np.int64),
               members=np.empty(total, np.int32), offsets=np.empty(ca.size + 1, np.int32),
               alpha=np.empty(total))
    count = _core.tier0_pass(C, inv_sqrt_v, v, W, exp_all, shifts64, dls, s_step - 1, cur,
                             inv_sqrt_vc, cur_offsets, cur_members, ca, cb, cdl, steps, alpha_floor,
                             out["accepted"], out["screener"], out["v_bar"], out["reach"],
                             out["members"], out["offsets"], out["alpha"])
    return count, out


@pytest.mark.parametrize("s_step", [1, 2, 4])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_matches_the_numpy_implementation(seed, s_step):
    args = _setting(seed, s_step)
    groups, accepted = _reference(*args, 4, 0.90)
    count, out = _run(args, 4, 0.90)
    assert count == len(accepted) == int(out["accepted"].sum())
    assert sorted(accepted) == np.flatnonzero(out["accepted"]).tolist()
    # the families' merges are accepted; the wide variance and the unlike pair are not
    assert 0 in accepted and 1 not in accepted and len(groups) - 1 not in accepted
    for g, grp in enumerate(groups):
        lo, hi = out["offsets"][g], out["offsets"][g + 1]
        assert out["members"][lo:hi].tolist() == grp
        if g in accepted:
            screener, v_bar, alphas, reach = accepted[g]
            # equal to rounding: numpy's complex modulus is not the same on every machine
            np.testing.assert_allclose(out["screener"][g], screener, rtol=0, atol=1e-11)
            np.testing.assert_allclose(out["alpha"][lo:hi], alphas, rtol=0, atol=1e-11)
            assert abs(out["v_bar"][g] - v_bar) < 1e-12 * v_bar and out["reach"][g] == reach


def test_nothing_accepted_writes_every_candidates_members():
    args = _setting(4, 2)
    count, out = _run(args, 4, 1.01)                     # no retention reaches the floor
    assert count == 0 and not out["accepted"].any()
    groups, _ = _reference(*args, 4, 1.01)
    assert out["members"].tolist() == [t for grp in groups for t in grp]


def test_rejects_what_it_cannot_index():
    args = list(_setting(5, 2))
    _run(args, 4, 0.9)
    bad = list(args)
    bad[12] = args[12].copy()
    bad[12][0] = 99                                      # a cluster that is not there
    with pytest.raises(ValueError):
        _run(bad, 4, 0.9)
    bad = list(args)
    bad[11] = args[11].copy()
    bad[11][3] = 1000                                    # a member that is not a template
    with pytest.raises(ValueError):
        _run(bad, 4, 0.9)
    bad = list(args)
    bad[0] = args[0].astype(np.complex64)
    with pytest.raises(ValueError):
        _run(bad, 4, 0.9)
