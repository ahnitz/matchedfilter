"""Single-template plans generate spectra only when a template is loaded."""
import numpy as np

import matchedfilter
from matchedfilter.device import Device
from matchedfilter.time_domain import _TemplateGroup


def test_gpu_single_plan_reuses_loaded_template(monkeypatch):
    events = []

    class Plan:
        def __init__(self, *args, **kwargs):
            events.append("create")

        def _settle_deferred(self):
            events.append("settle")

        def set_templates(self, spectra):
            events.append(("load", int(spectra[0, 0].real)))

    def spectra(rows):
        events.append(("spectra", rows.start))
        return np.full((1, 64), rows.start, np.complex64)

    monkeypatch.setattr(matchedfilter, "MatchedFilter", Plan)
    group = _TemplateGroup(None, 64, np.arange(3), 0, 64, 1,
                           device=Device("gpu", 0, "test", "cuda"), row_source=spectra)
    first = group.get_single_plan(1)
    assert group.get_single_plan(1) is first
    assert events == [("spectra", 1), "create", "settle", ("load", 1)]

    assert group.get_single_plan(2) is first
    assert events[-3:] == [("spectra", 2), "settle", ("load", 2)]
    before = len(events)
    assert group.get_single_plan(2) is first
    assert len(events) == before

    assert group.get_single_plan(1) is first
    assert events[-3:] == [("spectra", 1), "settle", ("load", 1)]


def test_cpu_single_plan_keeps_cached_templates(monkeypatch):
    loads = []

    class Plan:
        def __init__(self, *args, **kwargs):
            pass

        def set_templates(self, spectra):
            loads.append(int(spectra[0, 0].real))

    def spectra(rows):
        return np.full((1, 64), rows.start, np.complex64)

    monkeypatch.setattr(matchedfilter, "MatchedFilter", Plan)
    group = _TemplateGroup(None, 64, np.arange(3), 0, 64, 1,
                           device="cpu", row_source=spectra)
    first = group.get_single_plan(1)
    second = group.get_single_plan(2)
    assert first is not second
    assert group.get_single_plan(1) is first
    assert group.get_single_plan(2) is second
    assert loads == [1, 2]
