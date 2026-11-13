"""Chains the model prices within TIE of the cheapest are a tie, and the tie goes to the chain
with the fewest tiers: a tier adds a pass over its survivors that the costs underprice (a
two-tier chain priced equal to a three-tier one ran its fine stage in 17-18% less CPU on Ivy
Bridge and Haswell)."""
import pytest

from matchedfilter import gatechain
from matchedfilter._choice import TIE
from spectral_profiles import make_spectral_profile


@pytest.mark.parametrize("name", ["inspiral_canonical", "aligo_o4_inspiral", "bandpass_plateau"])
@pytest.mark.parametrize("snr, fd", [(6.0, 1e-3), (5.5, 1e-2)])
def test_a_tie_goes_to_the_fewest_tiers(name, snr, fd):
    n = 1024
    power = make_spectral_profile(name, n)
    best, plans = gatechain.choose_chain(power, n, snr, fd, max_tiers=3)
    if best is None:
        pytest.skip("no chain covers this profile")
    lo = min(p["cost"] for p in plans)
    tied = [p for p in plans if p["cost"] <= lo + TIE * abs(lo)]
    assert best in tied
    assert len(best["chain"]) == min(len(p["chain"]) for p in tied)


def test_pick_stable_orders_a_tie_by_its_key():
    items = [dict(c=1.00, k=3), dict(c=1.04, k=2), dict(c=1.06, k=1)]
    assert gatechain.pick_stable(items, lambda d: d["c"], lambda d: d["k"])["k"] == 2
