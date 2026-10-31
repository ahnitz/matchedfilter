"""The C engine end to end dismisses what the model says a chain's plan dismisses, two-sided,
single and multi-tier chains, whole-block and windowed searches (see test_fdr_calibration's
docstring for the claims and their budgets)."""
import pytest

from matchedfilter import gatechain as gc
from spectral_profiles import binomtest
from fdr_support import ALPHA, engine_misses, profile


@pytest.mark.parametrize("name", ["f^-1", "f^0", "f^1", "inspiral_canonical", "notched_lines",
                                  "bandpass_plateau", "skewed_edge"])
@pytest.mark.parametrize("chain", [(1024,), (256, 1024), (128, 512, 1024)])
def test_the_engine_dismisses_its_budget(name, chain):
    """End to end through the C engine: misses among detections are what the model says the
    chain's plan dismisses, two-sided, multi-tier chains included."""
    n, fd = 2048, 0.05
    power = profile(name, n)
    if not set(chain) <= set(gc.usable_bands(power, n)):
        pytest.skip("a band of %s holds none of %s's power" % (chain, name))
    thr, det, miss, want = engine_misses(power, n, chain, fd, 2500)
    p = binomtest(miss, det, p=want, alternative="two-sided").pvalue
    assert p >= ALPHA, ("%s %s: thresholds %s miss %d of %d detections (%.4f), modelled %.4f "
                        "(budget %.3f)" % (name, chain, [round(t, 3) for t in thr], miss, det,
                                           miss / det, want, fd))


@pytest.mark.parametrize("name", ["f^0", "inspiral_canonical"])
def test_a_windowed_search_dismisses_its_budget(name):
    """A search over part of the block (search_window): the gates are set for the window's
    noise, and dismiss what the model says they dismiss of signals inside it."""
    n, fd = 2048, 0.05
    power = profile(name, n)
    thr, det, miss, want = engine_misses(power, n, (256, 1024), fd, 2500, window=(512, 1536))
    p = binomtest(miss, det, p=want, alternative="two-sided").pvalue
    assert p >= ALPHA, ("%s windowed: thresholds %s miss %d of %d detections (%.4f), modelled "
                        "%.4f (budget %.3f)" % (name, [round(t, 3) for t in thr], miss, det,
                                                miss / det, want, fd))

