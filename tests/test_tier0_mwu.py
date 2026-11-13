"""_core.tier0_mwu builds each group's shared screener (gatechain.cluster_tier0_candidates):
the mean of the members phased to a common frame, or the minimax vector multiplicative
weights find, whichever the worst-matched member overlaps better. Checked against the numpy
code it replaced."""
import numpy as np
import pytest

from matchedfilter import _core


def _reference(U_raw, ref, W, steps):
    """The numpy implementation the C routine replaced: (c_unit, exact_ov)."""
    ref_frame = ref[:, None, :]
    g0 = np.sum(W[None, None, :] * ref_frame.conj() * U_raw, axis=2)
    abs_g0 = np.abs(g0)
    phase0 = np.where(abs_g0 > 1e-12, g0.conj() / np.maximum(abs_g0, 1e-12), 1.0 + 0.0j)
    U_tilde = U_raw * phase0[:, :, None]
    mean_vec = np.mean(U_tilde, axis=1)
    mean_norm = np.sqrt(np.maximum(
        np.sum((mean_vec.real ** 2 + mean_vec.imag ** 2) * W[None, :], axis=1), 1e-30))
    c_mean = mean_vec / mean_norm[:, None]
    ov_mean = np.abs(np.sum(W[None, None, :] * c_mean[:, None, :].conj() * U_raw, axis=2))
    weights = np.ones(U_raw.shape[:2])
    U_iter = U_tilde.copy()
    for _ in range(steps):
        s_vec = np.sum(weights[:, :, None] * U_iter, axis=1)
        s_norm = np.sqrt(np.maximum(
            np.sum((s_vec.real ** 2 + s_vec.imag ** 2) * W[None, :], axis=1), 1e-30))
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
        np.sum((s_vec.real ** 2 + s_vec.imag ** 2) * W[None, :], axis=1), 1e-30))
    c_mwu = s_vec / s_norm[:, None]
    ov_mwu = np.abs(np.sum(W[None, None, :] * c_mwu[:, None, :].conj() * U_raw, axis=2))
    use_mwu = np.min(ov_mwu, axis=1) >= np.min(ov_mean, axis=1)
    return (np.where(use_mwu[:, None], c_mwu, c_mean),
            np.where(use_mwu[:, None], ov_mwu, ov_mean), use_mwu)


def _groups(rng, nb, m, K, spread):
    """nb groups of m unit-norm members: a common vector plus `spread` of their own, each
    turned by a random phase."""
    W = rng.uniform(0.2, 2.0, K)
    base = rng.standard_normal((nb, 1, K)) + 1j * rng.standard_normal((nb, 1, K))
    own = rng.standard_normal((nb, m, K)) + 1j * rng.standard_normal((nb, m, K))
    U = (base + spread * own) * np.exp(2j * np.pi * rng.uniform(size=(nb, m, 1)))
    U /= np.sqrt(np.sum(np.abs(U) ** 2 * W, axis=2, keepdims=True))
    ref = U[:, 0, :] + U[:, -1, :]
    return np.ascontiguousarray(U), np.ascontiguousarray(ref), W


@pytest.mark.parametrize("m, steps", [(2, 4), (3, 4), (4, 4), (8, 6), (16, 8)])
@pytest.mark.parametrize("spread", [0.05, 0.3, 1.0])
def test_matches_the_numpy_implementation(m, steps, spread):
    rng = np.random.default_rng([m, steps, int(100 * spread)])
    nb, K = 9, 128
    U, ref, W = _groups(rng, nb, m, K, spread)
    c = np.empty((nb, K), np.complex128)
    ov = np.empty((nb, m), np.float64)
    _core.tier0_mwu(U, ref, W, steps, c, ov)
    c_ref, ov_ref, use_mwu = _reference(U, ref, W, steps)
    # Equal to rounding: the weights' exponentials grow a last-bit difference to ~1e-11.
    np.testing.assert_allclose(ov, ov_ref, rtol=0, atol=1e-9)
    np.testing.assert_allclose(c, c_ref, rtol=0, atol=1e-9)
    np.testing.assert_allclose(np.sum(np.abs(c) ** 2 * W, axis=1), 1.0, atol=1e-12)
    assert (ov <= 1.0 + 1e-12).all()
    if spread == 0.3 and m >= 3:
        assert use_mwu.any()                      # the minimax candidate is exercised


def test_a_member_orthogonal_to_the_frame_keeps_its_phase():
    """A member with no overlap with the reference frame is not rephased (the numpy code's
    guard at 1e-12), and nothing divides by zero."""
    K = 16
    W = np.ones(K)
    U = np.zeros((1, 2, K), np.complex128)
    U[0, 0, 0] = 1.0
    U[0, 1, 1] = 1.0j
    ref = np.zeros((1, K), np.complex128)
    ref[0, 0] = 1.0
    c = np.empty((1, K), np.complex128)
    ov = np.empty((1, 2))
    _core.tier0_mwu(U, ref, W, 4, c, ov)
    c_ref, ov_ref, _ = _reference(U, ref, W, 4)
    assert np.isfinite(c).all() and np.isfinite(ov).all()
    np.testing.assert_allclose(ov, ov_ref, atol=1e-12)
    np.testing.assert_allclose(c, c_ref, atol=1e-12)


def test_rejects_mismatched_shapes():
    W = np.ones(8)
    U = np.zeros((2, 3, 8), np.complex128)
    with pytest.raises(ValueError):
        _core.tier0_mwu(U, np.zeros((2, 7), np.complex128), W, 4,
                        np.empty((2, 8), np.complex128), np.empty((2, 3)))
    with pytest.raises(ValueError):
        _core.tier0_mwu(U.astype(np.complex64), np.zeros((2, 8), np.complex128), W, 4,
                        np.empty((2, 8), np.complex128), np.empty((2, 3)))
