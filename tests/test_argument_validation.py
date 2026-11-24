"""Arguments outside what a bank or a hierarchical filter can run are refused by name.

Before 2026-11-24 a false-dismissal budget outside (0, 1) made the gate model loop without
end (gatemodel.fit_order), an unknown engine name ran as the flat engine, and negative bin
sizes, bands and first-stage thresholds were ignored.
"""
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank


def _taps(counts=(200, 300, 400)):
    rng = np.random.default_rng(1)
    return [rng.standard_normal(c).astype(np.float32) for c in counts]


@pytest.mark.parametrize("fd", [0.0, -0.1, 1.0, 1.5, float("nan"), float("inf")])
def test_a_false_dismissal_budget_outside_zero_to_one_is_refused(fd):
    with pytest.raises(ValueError, match="false_dismissal"):
        TimeDomainFilterBank(_taps(), engine="hier", false_dismissal=fd)
    with pytest.raises(ValueError, match="false-dismissal"):
        mf.HierarchicalFilter(2048, ndata=1, ntemplates=3, snr=6.0, fd=fd)


@pytest.mark.parametrize("fd", [1e-6, 1e-3, 0.5, 0.999])
def test_a_false_dismissal_budget_inside_zero_to_one_is_accepted(fd):
    assert TimeDomainFilterBank(_taps(), engine="hier", false_dismissal=fd).false_dismissal == fd
    assert mf.HierarchicalFilter(2048, ndata=1, ntemplates=3, snr=6.0, fd=fd).fd == fd


def test_an_unknown_engine_is_refused_and_every_alias_is_accepted():
    with pytest.raises(ValueError, match="unknown engine 'nope'"):
        TimeDomainFilterBank(_taps(), engine="nope")
    names = {"hier": "hier", "matchedfilter-hierarchical": "hier", "flat": "flat",
             "matchedfilter": "flat", "pycbc": "flat", "corr": "corr", "correlation": "corr",
             "dif": "dif", "FLAT": "flat"}
    for name, engine in names.items():
        assert TimeDomainFilterBank(_taps(), engine=name).engine == engine


@pytest.mark.parametrize("kw, name", [
    (dict(tap_sample_rate=0.0), "tap_sample_rate"),
    (dict(data_sample_rate=-2048.0), "data_sample_rate"),
    (dict(tap_sample_rate=float("nan")), "tap_sample_rate"),
    (dict(first_stage_snr=-3.0), "first_stage_snr"),
    (dict(first_stage_snr=float("nan")), "first_stage_snr"),
    (dict(coarse_band_hz=-64.0), "coarse_band_hz"),
    (dict(coarse_band_hz=(64.0, float("nan"))), "coarse_band_hz"),
    (dict(max_batch_size=0), "max_batch_size"),
    (dict(max_batch_size=-4), "max_batch_size"),
    (dict(binsize=-5), "binsize"),
    (dict(binsize=100.5), "binsize"),
])
def test_an_argument_out_of_range_is_refused_by_name(kw, name):
    with pytest.raises(ValueError, match=name):
        TimeDomainFilterBank(_taps(), engine="flat", **kw)


def test_arguments_at_the_edge_of_their_range_are_accepted():
    """What the checks must not refuse: no first-stage threshold, an unpinned band given as
    zero, one template per group, a bin of one sample, and a bin size given as a numpy
    integer or as zero (no bin size)."""
    taps = _taps()
    TimeDomainFilterBank(taps, engine="hier", first_stage_snr=0.0, coarse_band_hz=0)
    TimeDomainFilterBank(taps, engine="flat", max_batch_size=1)
    assert TimeDomainFilterBank(taps, engine="flat", binsize=1).binsize == 1
    assert TimeDomainFilterBank(taps, engine="flat", binsize=np.int64(256)).binsize == 256
    assert TimeDomainFilterBank(taps, engine="flat", binsize=0).binsize is None


def test_tap_counts_outside_their_templates_are_refused():
    taps = _taps()
    with pytest.raises(ValueError, match=r"tap_counts\[2\] = 900 is outside its template's 400"):
        TimeDomainFilterBank(taps, tap_counts=[200, 300, 900], engine="flat")
    with pytest.raises(ValueError, match=r"tap_counts\[1\] = -5"):
        TimeDomainFilterBank(taps, tap_counts=[200, -5, 400], engine="flat")
    padded = np.zeros((2, 500), np.float32)
    padded[0, :200], padded[1] = taps[0], np.resize(taps[2], 500)
    with pytest.raises(ValueError, match=r"tap_counts\[0\] = 501"):
        TimeDomainFilterBank(padded, tap_counts=[501, 500], engine="flat")
    # counts shorter than the arrays are the documented way to hold templates of several lengths
    assert TimeDomainFilterBank(padded, tap_counts=[200, 500], engine="flat").n_templates == 2
