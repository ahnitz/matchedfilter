"""The levels of the shared-screener merging (_screeners.cluster_tier0_candidates), in C++:
_core.tier0_pair_level makes the templates' coherent pairs clusters of two, and
_core.tier0_pass turns a level and its candidate merges of two clusters into the next, each
merge a group with one screener or turned down. Checked against the numpy code they
replaced."""
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
        _core.tier0_mwu(U_raw, np.array([grp.size]), np.ascontiguousarray(mid_u[row:row + 1]), W,
                        steps, c_unit, overlap)
        v_bar = float(np.mean(v[grp]))
        alphas = np.minimum(1.0, np.sqrt(v_bar / v[grp]) * overlap[0])
        if alphas.min() >= alpha_floor:
            accepted[g] = (np.sqrt(v_bar) * c_unit[0], v_bar, alphas, int(np.max(np.abs(fine))))
    return groups, accepted


def _setting(seed, s_step, K=96, R=8, families=6):
    """`families` of four alike templates, each family two clusters of a pair; the candidate
    merges: the two clusters of each family but the last two (one family has a member of a
    variance too far from the rest), and a cluster of each of the last two families."""
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
    cur_v = rng.uniform(0.5, 2.0, nc)
    cur_dl = rng.integers(0, R + 1, nc).astype(np.int64)
    inv_sqrt_vc = 1.0 / np.sqrt(np.sum((cur.real ** 2 + cur.imag ** 2) * W, axis=1))
    ca = np.array(list(range(0, nc - 4, 2)) + [nc - 4], np.int64)
    cb = np.array(list(range(1, nc - 4, 2)) + [nc - 2], np.int64)
    cdl = rng.integers(-3, 4, ca.size).astype(np.int64)
    cdl[2] = 3 * R                                       # clipped to the lags there are
    dls = np.ascontiguousarray(np.arange(-R, R + 1, dtype=np.int64)[::s_step])
    shifts64 = np.ascontiguousarray(exp_all[::s_step].astype(np.complex64))
    return (C, inv_sqrt_v, v, W, exp_all, shifts64, dls, s_step, cur, inv_sqrt_vc, cur_offsets,
            cur_members, ca, cb, cdl), (cur_v, cur_dl)


def _next_level(args, extra, groups, accepted, alphas):
    """The level after a pass, as the numpy code built it: an accepted merge where the smaller
    of its two clusters stood, every other cluster as it is."""
    cur, cur_offsets, cur_members, ca, cb = args[8], args[10], args[11], args[12], args[13]
    cur_v, cur_dl = extra
    nc = cur.shape[0]
    gid, partner = np.full(nc, -1), np.full(nc, -1)
    for g in accepted:
        lo, hi = sorted((int(ca[g]), int(cb[g])))
        gid[lo], partner[lo], partner[hi] = g, hi, lo
    vecs, v_out, dl_out, offsets, members = [], [], [], [0], []
    alphas = alphas.copy()
    for c in range(nc):
        if 0 <= partner[c] < c:
            continue
        if partner[c] > c:
            screener, v_bar, al, reach = accepted[gid[c]]
            vecs.append(screener)
            v_out.append(v_bar)
            dl_out.append(reach)
            members += groups[gid[c]]
            alphas[groups[gid[c]]] = al
        else:
            vecs.append(cur[c])
            v_out.append(cur_v[c])
            dl_out.append(int(cur_dl[c]))
            members += cur_members[cur_offsets[c]:cur_offsets[c + 1]].tolist()
        offsets.append(len(members))
    return np.array(vecs), np.array(v_out), dl_out, offsets, members, alphas


def _run(args, extra, steps, alpha_floor, alphas):
    (C, inv_sqrt_v, v, W, exp_all, shifts64, dls, s_step, cur, inv_sqrt_vc, cur_offsets,
     cur_members, ca, cb, cdl) = args
    nt, nc = C.shape[0], cur.shape[0]
    out = dict(vecs=np.empty((nc, C.shape[1]), np.complex128), v=np.empty(nc),
               dl=np.empty(nc, np.int64), offsets=np.empty(nc + 1, np.int32),
               members=np.empty(nt, np.int32), alphas=alphas.copy())
    count, reach = _core.tier0_pass(
        C, inv_sqrt_v, v, W, exp_all, shifts64, dls, s_step - 1, cur, inv_sqrt_vc, extra[0],
        extra[1], cur_offsets, cur_members, ca, cb, cdl, steps, alpha_floor,
        out["vecs"], out["v"], out["dl"], out["offsets"], out["members"], out["alphas"])
    return count, reach, out


@pytest.mark.parametrize("s_step", [1, 2, 4])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_a_pass_matches_the_numpy_implementation(seed, s_step):
    args, extra = _setting(seed, s_step)
    alphas = np.random.default_rng(seed).uniform(0.9, 1.0, args[0].shape[0])
    groups, accepted = _reference(*args, 4, 0.90)
    # families' merges are accepted; the wide variance and the unlike pair are not
    assert len(accepted) >= 1 and 1 not in accepted and len(groups) - 1 not in accepted
    vecs, v_out, dl_out, offsets, members, want_alphas = _next_level(args, extra, groups, accepted, alphas)
    count, reach, out = _run(args, extra, 4, 0.90, alphas)
    nc = args[8].shape[0] - count
    assert count == len(accepted) and nc == len(v_out) and reach == max(dl_out)
    assert out["offsets"][:nc + 1].tolist() == offsets and out["members"].tolist() == members
    assert out["dl"][:nc].tolist() == dl_out
    # equal to rounding: numpy's complex modulus is not the same on every machine
    np.testing.assert_allclose(out["vecs"][:nc], vecs, rtol=0, atol=1e-11)
    np.testing.assert_allclose(out["v"][:nc], v_out, rtol=1e-12)
    np.testing.assert_allclose(out["alphas"], want_alphas, rtol=0, atol=1e-11)


def test_a_pass_that_accepts_nothing_says_so():
    args, extra = _setting(4, 2)
    alphas = np.ones(args[0].shape[0])
    count, _, out = _run(args, extra, 4, 1.01, alphas)          # no retention reaches the floor
    assert count == 0 and np.array_equal(out["alphas"], alphas)


def test_a_pass_rejects_what_it_cannot_index():
    args, extra = _setting(5, 2)
    alphas = np.ones(args[0].shape[0])
    _run(args, extra, 4, 0.9, alphas)
    for at, change in ((12, lambda x: np.where(np.arange(x.size) == 0, 99, x)),      # no such cluster
                       (12, lambda x: np.where(np.arange(x.size) == 1, x[0], x)),    # a cluster twice
                       (11, lambda x: np.where(np.arange(x.size) == 3, 1000, x).astype(np.int32)),
                       (0, lambda x: x.astype(np.complex64))):
        bad = list(args)
        bad[at] = np.ascontiguousarray(change(args[at]))
        with pytest.raises(ValueError):
            _run(bad, extra, 4, 0.9, alphas)


def _pair_reference(C, inv_sqrt_v, v, W, exp_all, s_step, rho_min, max_nc, pa, pb, pdl):
    """The numpy implementation of the first level: None where no pair is kept or too many
    clusters are left, else (vectors, variances, lags, offsets, members, retentions)."""
    nt, R = C.shape[0], (exp_all.shape[0] - 1) // 2
    if pa.size == 0 or nt - pa.size > max_nc:
        return None
    Ca_u = C[pa] * inv_sqrt_v[pa, None]
    Cb_u = C[pb] * inv_sqrt_v[pb, None]
    prod_ab = (W[None, :] * Ca_u.conj()) * Cb_u
    best = np.full(pa.size, -1.0)
    lag = pdl.copy()
    g_vec = np.zeros(pa.size, np.complex128)
    for off in range(-(s_step - 1), s_step):
        trial = np.clip(pdl + off, -R, R)
        g = np.einsum("ij,ij->i", prod_ab, exp_all[trial + R])
        better = np.abs(g) > best
        best, lag, g_vec = np.where(better, np.abs(g), best), np.where(better, trial, lag), np.where(better, g, g_vec)
    rho = np.abs(g_vec)
    keep = rho >= rho_min
    pa, pb, lag, Ca_u, Cb_u, g_vec, rho = (x[keep] for x in (pa, pb, lag, Ca_u, Cb_u, g_vec, rho))
    if pa.size == 0 or nt - pa.size > max_nc:
        return None
    target_v = 0.5 * (v[pa] + v[pb])
    pair_vecs = ((np.sqrt(target_v) / np.sqrt(2.0 * (1.0 + rho)))[:, None]
                 * (Ca_u + (g_vec.conj() / rho)[:, None] * (Cb_u * exp_all[lag + R])))
    alphas = np.ones(nt)
    alphas[pa] = np.minimum(1.0, np.sqrt(target_v / v[pa]) * np.sqrt(0.5 * (1.0 + rho)))
    alphas[pb] = np.minimum(1.0, np.sqrt(target_v / v[pb]) * np.sqrt(0.5 * (1.0 + rho)))
    slot = {int(a): i for i, a in enumerate(pa)}
    second = set(int(b) for b in pb)
    vecs, v_out, dl_out, offsets, members = [], [], [], [0], []
    for t in range(nt):
        if t in second:
            continue
        if t in slot:
            i = slot[t]
            vecs.append(pair_vecs[i])
            v_out.append(target_v[i])
            dl_out.append(abs(int(lag[i])))
            members += [t, int(pb[i])]
        else:
            vecs.append(C[t])
            v_out.append(v[t])
            dl_out.append(0)
            members.append(t)
        offsets.append(len(members))
    return np.array(vecs), np.array(v_out), dl_out, offsets, members, alphas


def _run_pairs(C, inv_sqrt_v, v, W, exp_all, s_step, rho_min, max_nc, pa, pb, pdl):
    nt = C.shape[0]
    out = dict(vecs=np.empty(C.shape, np.complex128), v=np.empty(nt), dl=np.empty(nt, np.int64),
               offsets=np.empty(nt + 1, np.int32), members=np.empty(nt, np.int32),
               alphas=np.empty(nt))
    nc, reach = _core.tier0_pair_level(C, inv_sqrt_v, v, W, exp_all, s_step - 1, rho_min, max_nc,
                                       pa, pb, pdl, out["vecs"], out["v"], out["dl"],
                                       out["offsets"], out["members"], out["alphas"])
    return nc, reach, out


def _pairs(seed, s_step):
    """The setting's templates paired within their families, one pair across two families
    (not coherent), the last family left unpaired."""
    args, _ = _setting(seed, s_step)
    C, inv_sqrt_v, v, W, exp_all = args[:5]
    rng = np.random.default_rng(seed)
    pa = np.array([0, 2, 4, 9, 12, 14, 16], np.int32)
    pb = np.array([1, 3, 5, 13, 18, 15, 17], np.int32)       # (9, 13) and (12, 18): two families
    pdl = rng.integers(-6, 7, pa.size).astype(np.int64)
    return C, inv_sqrt_v, v, W, exp_all, s_step, pa, pb, pdl


@pytest.mark.parametrize("s_step", [1, 2, 4])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_the_pair_level_matches_the_numpy_implementation(seed, s_step):
    C, inv_sqrt_v, v, W, exp_all, s_step, pa, pb, pdl = _pairs(seed, s_step)
    # s_step 1 keeps the lags given: few pairs are coherent at a lag that is not theirs
    want = _pair_reference(C, inv_sqrt_v, v, W, exp_all, s_step, 0.5, 100, pa, pb, pdl)
    nc, reach, out = _run_pairs(C, inv_sqrt_v, v, W, exp_all, s_step, 0.5, 100, pa, pb, pdl)
    vecs, v_out, dl_out, offsets, members, alphas = want
    assert nc == len(v_out) and reach == max(dl_out)
    assert C.shape[0] - 7 <= nc < C.shape[0]                 # some pairs kept, some not
    assert out["offsets"][:nc + 1].tolist() == offsets and out["members"].tolist() == members
    assert out["dl"][:nc].tolist() == dl_out
    np.testing.assert_allclose(out["vecs"][:nc], vecs, rtol=0, atol=1e-11)
    np.testing.assert_allclose(out["v"][:nc], v_out, rtol=1e-12)
    np.testing.assert_allclose(out["alphas"], alphas, rtol=0, atol=1e-11)


def test_the_pair_level_gives_up_as_the_numpy_code_did():
    C, inv_sqrt_v, v, W, exp_all, s_step, pa, pb, pdl = _pairs(2, 4)
    kept = C.shape[0] - _run_pairs(C, inv_sqrt_v, v, W, exp_all, s_step, 0.5, 100, pa, pb, pdl)[0]
    for rho_min, max_nc in ((0.5, C.shape[0] - kept - 1),    # too many clusters left
                            (1.01, 100)):                   # no pair coherent enough
        assert _pair_reference(C, inv_sqrt_v, v, W, exp_all, s_step, rho_min, max_nc, pa, pb, pdl) is None
        assert _run_pairs(C, inv_sqrt_v, v, W, exp_all, s_step, rho_min, max_nc, pa, pb, pdl)[0] == 0
    none = np.empty(0, np.int32)
    assert _run_pairs(C, inv_sqrt_v, v, W, exp_all, s_step, 0.5, 100, none, none,
                      np.empty(0, np.int64))[0] == 0
    with pytest.raises(ValueError):                          # a template in two pairs
        _run_pairs(C, inv_sqrt_v, v, W, exp_all, s_step, 0.5, 100, pa, np.where(pb == 3, 1, pb).astype(np.int32), pdl)
