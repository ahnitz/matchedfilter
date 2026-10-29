"""The public interface (docs/robustness-plan.md, decision 5): the package root's __all__,
the public submodules, and gatechain's documented functions. Everything else is private
and may move. A rename or removal here is a deliberate API change, noted in CHANGELOG."""
import importlib

import matchedfilter as mf

ROOT = {"MatchedFilter", "CorrelationFilter", "HierarchicalFilter", "PEAK_DTYPE", "backend",
        "targets", "set_target", "devices", "Device", "__version__", "get_autotune_state",
        "clear_autotune_cache", "TimeDomainFilterBank", "FilterResults", "taps_to_spectra",
        "template_spectra", "template_valid", "include_dir", "UnsupportedSize"}

SUBMODULES = {
    "time_domain": {"TimeDomainFilterBank", "FilterResults", "template_spectra",
                    "template_valid", "reference_profile"},
    "search": {"HierarchicalSearch", "Root", "Inner", "Leaf", "BlockInput"},
    "device": {"Device", "parse", "devices"},
    "precision": {"sweep"},
    "gatechain": {"chain_thresholds", "calibrate_costs", "choose_chain"},
}


def test_the_root_exports_exactly_the_public_names():
    assert set(mf.__all__) == ROOT
    for name in ROOT:
        assert getattr(mf, name) is not None, name


def test_the_public_submodules_and_their_names():
    for mod, names in SUBMODULES.items():
        m = importlib.import_module("matchedfilter." + mod)
        missing = [n for n in names if not hasattr(m, n)]
        assert not missing, (mod, missing)
