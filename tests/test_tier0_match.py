"""_core.tier0_match pairs a level's vectors (_screeners.cluster_tier0_candidates): a chunk of
neighbours at a time is scored, matched greedily and its left-overs placed by breaking a
pair, and the chunks' left-overs are matched once more. Checked against the numpy code it
replaced."""
import numpy as np
import pytest

from matchedfilter import _core


def _best_swap(scores, u, vs, w_arr, z_arr, floor):
    """The swap that pairs two unmatched nodes by breaking one matched pair.

    A matched pair (w, z) can be replaced by (u, w) and (v, z), or by (u, z) and (v, w),
    when both new pairs score at least ``floor``; the swap's gain is the two new scores'
    sum. For the unmatched node ``u`` this returns the swap of largest gain over the nodes
    ``vs``: of equal gains, the first v in ``vs``, for a v the swap with u on w's side
    before the one with u on z's side, and on a side the first pair.

    Parameters
    ----------
    scores : numpy.ndarray
        ``(m, m)`` symmetric pair scores.
    u : int
        The unmatched node being placed.
    vs : numpy.ndarray
        The other unmatched nodes it may be placed with, in the order they are tried.
    w_arr, z_arr : numpy.ndarray
        The matched pairs: pair ``e`` is ``(w_arr[e], z_arr[e])``.
    floor : float
        The least score a pair may have.

    Returns
    -------
    tuple or None
        ``(e, v, (a, b), (c, d))``: the pair ``e`` to replace by ``(a, b)``, which holds u,
        and the new pair ``(c, d)``, which holds v, each with its smaller node first; None
        when no swap exists.
    """
    if not vs.size:
        return None
    v_w = scores[np.ix_(vs, w_arr)]
    v_z = scores[np.ix_(vs, z_arr)]
    u_w, u_z = scores[u, w_arr], scores[u, z_arr]
    # the gain of each (v, pair) with u on w's side, and with u on z's side
    gain_w = np.where((u_w >= floor)[None, :] & (v_z >= floor), u_w[None, :] + v_z, -np.inf)
    gain_z = np.where((u_z >= floor)[None, :] & (v_w >= floor), u_z[None, :] + v_w, -np.inf)
    pair_w, pair_z = gain_w.argmax(axis=1), gain_z.argmax(axis=1)
    each = np.arange(vs.size)
    # per v: (best on w's side, best on z's side), then the first of the largest over all
    gains = np.stack([gain_w[each, pair_w], gain_z[each, pair_z]], axis=1).ravel()
    first = int(gains.argmax())
    if not gains[first] > -1.0:
        return None
    v = int(vs[first // 2])
    if first % 2 == 0:
        e = int(pair_w[first // 2])
        mine, theirs = int(w_arr[e]), int(z_arr[e])
    else:
        e = int(pair_z[first // 2])
        mine, theirs = int(z_arr[e]), int(w_arr[e])
    return e, v, (min(u, mine), max(u, mine)), (min(v, theirs), max(v, theirs))


def _match_chunk(sub_idx, U, v, Sr, Si, lags, floor, sizes, size_cap, swaps):
    """One chunk's pairs by the numpy code: lists (smaller index, larger, lag)."""
    m_c = int(sub_idx.size)
    if m_c < 2:
        return [], [], []
    U_c = U[sub_idx]
    best_rho2 = np.empty((m_c, m_c), dtype=np.float32)
    best_s = np.empty((m_c, m_c), dtype=np.int32)
    _core.tier0_pair_scores(np.ascontiguousarray(U_c.real), np.ascontiguousarray(U_c.imag), Sr, Si,
                            np.ascontiguousarray(v[sub_idx]), 0.0, best_rho2, best_s)
    if sizes is not None:
        sz_c = sizes[sub_idx]
        best_rho2[sz_c[:, None] + sz_c[None, :] > size_cap] = -1.0
    ri = np.arange(m_c)[:, None]
    if m_c > 9:
        top_cols = np.argpartition(-best_rho2, kth=7, axis=1)[:, :8]
        top_vals = best_rho2[ri, top_cols]
        ia_loc, kb_loc = np.nonzero(top_vals >= floor)
        ib_loc = top_cols[ia_loc, kb_loc]
        cand_r2 = top_vals[ia_loc, kb_loc]
    else:
        ia_loc, ib_loc = np.nonzero(best_rho2 >= floor)
        cand_r2 = best_rho2[ia_loc, ib_loc]
    if ia_loc.size == 0:
        return [], [], []
    used = np.zeros(m_c, dtype=bool)
    local_pairs = []
    for idx in np.argsort(-cand_r2, kind="stable"):
        a_l, b_l = int(ia_loc[idx]), int(ib_loc[idx])
        if used[a_l] or used[b_l]:
            continue
        used[a_l] = used[b_l] = True
        local_pairs.append((a_l, b_l) if a_l < b_l else (b_l, a_l))
    if sizes is None and m_c - 2 * len(local_pairs) >= 2 and local_pairs:
        sym_r2 = best_rho2 + best_rho2.T
        free_arr = np.flatnonzero(~used)
        w_arr = np.array([p[0] for p in local_pairs], dtype=np.int32)
        z_arr = np.array([p[1] for p in local_pairs], dtype=np.int32)
        uw_mat = (sym_r2[np.ix_(free_arr, w_arr)] >= floor).astype(np.float32)
        uz_mat = (sym_r2[np.ix_(free_arr, z_arr)] >= floor).astype(np.float32)
        aug_adj = np.triu(uw_mat @ uz_mat.T + uz_mat @ uw_mat.T, k=1)
        for idx_u in np.flatnonzero(np.any(aug_adj > 0.0, axis=1)):
            node_u = int(free_arr[idx_u])
            if used[node_u]:
                continue
            if not (np.any(sym_r2[node_u, w_arr] >= floor) or np.any(sym_r2[node_u, z_arr] >= floor)):
                continue
            later = free_arr[idx_u + 1:]
            best_swap = _best_swap(sym_r2, node_u, later[~used[later]], w_arr, z_arr, floor)
            if best_swap is not None:
                e_idx, node_v, e1, e2 = best_swap
                used[node_u] = used[node_v] = True
                local_pairs[e_idx] = e1
                local_pairs.append(e2)
                w_arr[e_idx], z_arr[e_idx] = e1
                w_arr, z_arr = np.append(w_arr, e2[0]), np.append(z_arr, e2[1])
                swaps.append(1)
    out_a, out_b, out_dl = [], [], []
    for a_l, b_l in local_pairs:
        ta, tb = int(sub_idx[a_l]), int(sub_idx[b_l])
        dl_ab = int(lags[best_s[a_l, b_l]])
        out_a.append(min(ta, tb))
        out_b.append(max(ta, tb))
        out_dl.append(dl_ab if ta < tb else -dl_ab)
    return out_a, out_b, out_dl


def _reference(order, U, v, Sr, Si, lags, floor, sizes, size_cap, chunk):
    """The numpy implementation the C++ routine replaced: (a, b, dl) lists, and the number of
    swaps it made."""
    a_list, b_list, dl_list, swaps = [], [], [], []
    paired = np.zeros(U.shape[0], dtype=bool)
    for start in range(0, order.size, chunk):
        ca, cb, cdl = _match_chunk(order[start:start + chunk], U, v, Sr, Si, lags, floor, sizes,
                                   size_cap, swaps)
        paired[ca] = True
        paired[cb] = True
        a_list += ca
        b_list += cb
        dl_list += cdl
    rem = order[~paired[order]]
    if rem.size >= 2:
        for start in range(0, rem.size, chunk):
            ca, cb, cdl = _match_chunk(rem[start:start + chunk], U, v, Sr, Si, lags, floor, sizes,
                                       size_cap, swaps)
            a_list += ca
            b_list += cb
            dl_list += cdl
    return a_list, b_list, dl_list, len(swaps)


def _setting(seed, nodes, K=64, R=4, spread=0.25):
    """Unit vectors in families of two to five alike members at lags of their own, in an
    order that keeps a family together; the coarse shifts in the order they are tried."""
    rng = np.random.default_rng(seed)
    k = np.arange(K)
    turn = np.exp((-2j * np.pi / 512) * (np.arange(-R, R + 1)[:, None] * k[None, :]))
    U = np.empty((nodes, K), np.complex64)
    at = 0
    while at < nodes:
        base = np.exp(1j * (rng.uniform(0, 2 * np.pi) + rng.uniform(20, 400) * (k / K) ** 2))
        for _ in range(min(int(rng.integers(2, 6)), nodes - at)):
            own = spread * (rng.standard_normal(K) + 1j * rng.standard_normal(K))
            x = (base + own) * turn[int(rng.integers(0, 2 * R + 1))]
            U[at] = x / np.sqrt(np.sum(np.abs(x) ** 2))
            at += 1
    v = rng.uniform(0.93, 1.0, nodes)
    order = np.arange(nodes, dtype=np.int64)
    for start in range(0, nodes - 8, 8):                 # shuffled a little, not sorted
        order[start:start + 8] = rng.permutation(order[start:start + 8])
    tried = [R] + [x for s in range(1, R + 1) for x in (R - s, R + s)]
    Sr = np.ascontiguousarray(turn[tried].real, dtype=np.float32)
    Si = np.ascontiguousarray(turn[tried].imag, dtype=np.float32)
    lags = np.ascontiguousarray(np.arange(-R, R + 1, dtype=np.int64)[tried])
    return order, U, v, Sr, Si, lags


def _run(order, U, v, Sr, Si, lags, floor, sizes, size_cap, chunk):
    a = np.empty(order.size // 2, np.int32)
    b = np.empty(order.size // 2, np.int32)
    dl = np.empty(order.size // 2, np.int64)
    n = _core.tier0_match(order, U, v, Sr, Si, lags, floor, sizes, size_cap, chunk, a, b, dl)
    return a[:n].tolist(), b[:n].tolist(), dl[:n].tolist()


@pytest.mark.parametrize("nodes, chunk", [(7, 48), (9, 48), (40, 48), (131, 48), (300, 64), (300, 192)])
def test_matches_the_numpy_implementation(nodes, chunk):
    swaps = 0
    for seed in range(6):
        setting = _setting([seed, nodes], nodes)
        want = _reference(*setting, 0.55, None, 2, chunk)
        assert _run(*setting, 0.55, None, 2, chunk) == want[:3]
        swaps += want[3]
        assert len(want[0]) >= nodes // 4                # the families pair up
        assert len(set(want[0]) | set(want[1])) == 2 * len(want[0])     # a node in one pair
    if nodes >= 40:
        assert swaps > 0                                 # left-overs were placed by a swap


@pytest.mark.parametrize("size_cap", [2, 4, 8])
def test_sizes_cap_what_may_pair(size_cap):
    """With sizes (a later pass: the nodes are clusters), two nodes pair only if their sizes
    sum to at most the cap, and no left-over is placed by a swap."""
    for seed in range(4):
        setting = _setting([seed, size_cap], 200)
        sizes = np.random.default_rng(seed).integers(1, 5, 200).astype(np.int32)
        want = _reference(*setting, 0.5, sizes, size_cap, 48)
        got = _run(*setting, 0.5, sizes, size_cap, 48)
        assert got == want[:3] and want[3] == 0
        assert all(sizes[a] + sizes[b] <= size_cap for a, b in zip(got[0], got[1]))
        if size_cap >= 4:
            assert got[0]


def test_equal_scores_are_taken_by_column():
    """Vectors that are copies of one another score the same against each other. numpy's
    order among a row's equal candidates was its partial sort's; the routine takes them by
    column, so the pairs are the same on every run and every machine."""
    order, U, v, Sr, Si, lags = _setting(3, 24)
    U[:] = U[0]
    v[:] = 1.0
    order = np.arange(24, dtype=np.int64)
    a, b, dl = _run(order, U, v, Sr, Si, lags, 0.5, None, 2, 48)
    assert (a, b) == (list(range(0, 24, 2)), list(range(1, 24, 2))) and not any(dl)


def test_rejects_what_it_cannot_index():
    order, U, v, Sr, Si, lags = _setting(5, 20)
    twice = order.copy()
    twice[1] = twice[0]
    for bad in ((twice, U), (order + 1, U), (order, U.astype(np.complex128))):
        with pytest.raises(ValueError):
            _run(bad[0], bad[1], v, Sr, Si, lags, 0.5, None, 2, 48)
    with pytest.raises(ValueError):
        _run(order, U, v, Sr, Si, lags, 0.5, np.ones(19, np.int32), 2, 48)
