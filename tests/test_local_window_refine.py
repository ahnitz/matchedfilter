"""The planner's local window where far noise can draw a direct refine away from the signal
(tests/test_local_window.py has the window itself): the chance is charged as often as it
happens, and a plan with a direct refine keeps its budget on the real window. A module of
its own: under the sanitizers the two together outran a shard's time (Nightly,
2026-11-16)."""
import numpy as np
import pytest

from matchedfilter import gatechain as gc
from matchedfilter import gatemodel as gm

from test_local_window import (CHECK_SEED, DATA, PROFILES, _production, empty_model)  # noqa: F401 (empty_model is a fixture)


def _far_cases():
    return [("o2 measured", 6.0), ("o4 broadband", 6.0), ("bimodal", 6.0)]


@pytest.mark.parametrize("name,snr", _far_cases())
def test_far_noise_drawing_the_refine_away_is_charged_as_often_as_it_happens(empty_model, name, snr):
    """The engine's direct refine looks around the last tier's largest coarse value in the
    window (hmf.c refine_direct_pair). Sometimes that is noise far from the signal, and the
    refine misses the signal. Draws in the local window cannot show it, so the plan pairs
    each with the searched window's noise maximum (gatechain._distances, far=). The share of
    detections it charges that way is at least the share for which, in a simulation of the
    searched window itself, the coarse maximum lies outside the local window -- and not
    several times it."""
    p, n = PROFILES[name]()
    bands = gc.usable_bands(p, n)
    window = _production(n)
    local = gc.local_window(p, n, bands, window)
    ndet = 4 * gc.model_draws(1e-3)[0]
    noise = gc.noise_block_maxima(p, n, bands, nsim=gc.model_draws(1e-3)[1], window=window)
    sig, lags = gc.signal_draws(p, n, bands, snr, ndet, window=local, lags_too=True)
    (C, F), (fat, cat) = gc.signal_draws(p, n, bands, snr, ndet, seed=CHECK_SEED, window=window, lags_too=True)
    det = F[:, 0] >= snr
    counted = 0
    for b in (128, 256, 512):
        col, R = bands.index(b), n // b
        charged = gc._distances(sig, lags, bands, (b,), snr, n, noise) >= b
        happens = np.abs(fat[det] - cat[det, col]) > (local[1] - local[0]) + 2 * R
        # without the pairing the local draws show none of them: their coarse maxima lie in
        # the local window, or one coarse sample past an end of it (as the engine searches)
        plain = gc._distances(sig, lags, bands, (b,), snr, n)
        assert np.count_nonzero(plain * R > (local[1] - local[0]) + 2 * R) == 0
        if happens.sum() < 30:
            continue                                   # too rare in this band to count
        counted += 1
        slack = 3.0 * np.sqrt(happens.sum()) / det.sum()
        assert charged.mean() >= happens.mean() - slack, (b, charged.mean(), happens.mean())
        assert charged.mean() <= 3.0 * happens.mean() + slack, (b, charged.mean(), happens.mean())
    assert counted >= 1


@pytest.mark.parametrize("name,snr", _far_cases())
def test_a_plan_with_a_direct_refine_keeps_the_budget_on_the_real_window(empty_model, name, snr):
    """The tiers and the direct refine's window share one budget (plan_chain). Audited on
    independent draws of the searched window -- a detection lost if a tier dismisses it or
    its fine maximum lies beyond the half-width from the last tier's coarse maximum, wherever
    in the window that is -- the plan keeps it."""
    import json
    p, n = PROFILES[name]()
    fd = 1e-3
    bands = gc.usable_bands(p, n)
    window = _production(n)
    rec = json.loads((DATA / "cost_model_2048_zen5.json").read_text())
    direct = gc.CostModel.from_dict(rec["model"]).unscreened().with_direct(0.09 * 256 + 4.0)
    ndet = 4 * gc.model_draws(fd)[0]
    (C, F), (fat, cat) = gc.signal_draws(p, n, bands, snr, ndet, seed=CHECK_SEED, window=window, lags_too=True)
    det = F[:, 0] >= snr
    windows = 0
    for chain in ((256,), (128, 256), (256, 512)):
        pl = gc.chain_thresholds(p, n, snr, fd, chain, cost=direct, window=window)
        lost = np.zeros(int(det.sum()), bool)
        for b, t in zip(chain, pl["thresholds"]):
            lost |= C[det, bands.index(b)] < t
        if pl["halfwidth"] is not None:
            windows += 1
            lost |= np.abs(fat[det] - cat[det, bands.index(chain[-1])]) / (n // chain[-1]) > pl["halfwidth"]
        assert lost.mean() <= fd * (gm._TAIL_RATIO + 3.0 / np.sqrt(fd * det.sum())), (chain, lost.mean() / fd)
    assert windows >= 1, "no chain of the case was planned with a direct refine"
