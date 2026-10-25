"""The gate model reuses a result for another profile only where the gates would not change:
equal profiles share exactly, near-identical ones share, and profiles whose band responses
differ (here an O4 and an A+ reference, cosine 0.995) are each planned on their own -- one
borrowing the other's plan dismissed 4x its budget."""
import pathlib
from collections import OrderedDict

import numpy as np
import pytest

from matchedfilter import gatechain as gc
from matchedfilter import gatemodel as gm

DATA = pathlib.Path(__file__).parent / "data"
N, WIN = 2048, (192, 1856)


def _psd(name):
    z = np.load(DATA / "psd_model_profiles.npz")
    names = [str(x) for x in z["names"]]
    return z["p2048"][names.index(name)].astype(np.float64)


@pytest.fixture
def empty_model(monkeypatch):
    for c in ("_SIGNAL_CACHE", "_NOISE_CACHE", "_CAND_CACHE", "_CHOICE_CACHE", "_PLAN_CACHE",
              "_DIRECT_CACHE", "_DIRECT_DRAWS", "_NOISE_RECORDS"):
        monkeypatch.setattr(gc, c, OrderedDict())
    monkeypatch.setattr(gc, "_SIMILAR", {})


def test_the_signature_tells_different_profiles_apart():
    a = _psd("aLIGOAdVO4T1800545|flow=30|fcut=1024")
    b = _psd("aLIGOAPlusDesignSensitivityT1800042|flow=30|fcut=1024")
    assert gm._profile_sig(a) != gm._profile_sig(b)
    assert gm._profile_sig(a) == gm._profile_sig(7.0 * a)          # only the shape matters


def test_a_different_profile_is_planned_on_its_own(empty_model):
    a = _psd("aLIGOAdVO4T1800545|flow=30|fcut=1024")
    b = _psd("aLIGOAPlusDesignSensitivityT1800042|flow=30|fcut=1024")
    cos = float(a @ b / np.linalg.norm(a) / np.linalg.norm(b))
    assert cos > gc._REUSE_COS          # the old criterion alone would have shared these
    chain = (128, 256, 512)
    first = gc.chain_thresholds(a, N, 6.0, 1e-2, chain, window=WIN)
    after = gc.chain_thresholds(b, N, 6.0, 1e-2, chain, window=WIN)
    for c in (gc._SIGNAL_CACHE, gc._NOISE_CACHE, gc._PLAN_CACHE, gc._CAND_CACHE):
        c.clear()
    gc._SIMILAR.clear()
    alone = gc.chain_thresholds(b, N, 6.0, 1e-2, chain, window=WIN)
    assert after is not first
    assert tuple(after["thresholds"]) == tuple(alone["thresholds"])


def test_a_near_identical_profile_reuses(empty_model):
    a = np.load(DATA / "reference_profile_o2_h1l1_2048.npy").astype(np.float64)
    rng = np.random.default_rng(1)
    b = a * (1.0 + 1e-5 * rng.standard_normal(N))
    assert gm._profile_sig(a) != gm._profile_sig(b)
    chain = (256, 512, 1024)
    first = gc.chain_thresholds(a, N, 6.0, 1e-3, chain, window=WIN)
    assert gc.chain_thresholds(b, N, 6.0, 1e-3, chain, window=WIN) is first


def test_no_reuse_past_the_response_tolerance(empty_model):
    """A profile whose band response moved more than the tolerance gets its own draws."""
    a = np.load(DATA / "reference_profile_o2_h1l1_2048.npy").astype(np.float64)
    k = np.arange(N)
    b = a * (1.0 + 0.2 * (k < 128))           # 20% more power in the lowest bins
    fa, fb = gc._gate_features(a, N), gc._gate_features(b, N)
    assert np.max(np.abs(fa - fb) / np.maximum(fa, 1e-12)) > gc._REUSE_RESPONSE
    sa = gc.signal_draws(a, N, [256, 512, 1024], 6.0, 20000)
    assert gc.signal_draws(b, N, [256, 512, 1024], 6.0, 20000) is not sa


def test_a_reused_result_is_found_again_by_its_own_signature(empty_model):
    """A profile that took another's result finds it again without the similarity search
    (which costs ~1 ms a lookup against ~0.03 ms; a filter asks once per tier and resolution)."""
    a = np.load(DATA / "reference_profile_o2_h1l1_2048.npy").astype(np.float64)
    b = a * (1.0 + 1e-5 * np.random.default_rng(2).standard_normal(N))
    chain = (256, 512, 1024)
    first = gc.chain_thresholds(a, N, 6.0, 1e-3, chain, window=WIN)
    assert gc.chain_thresholds(b, N, 6.0, 1e-3, chain, window=WIN) is first
    gc._SIMILAR.clear()                 # only b's own signature can find it now
    assert gc.chain_thresholds(b, N, 6.0, 1e-3, chain, window=WIN) is first
