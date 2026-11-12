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
    assert events == ["create", ("spectra", 1), "settle", ("load", 1)]

    assert group.get_single_plan(2) is first
    assert events[-3:] == [("spectra", 2), "settle", ("load", 2)]
    before = len(events)
    assert group.get_single_plan(2) is first
    assert len(events) == before

    assert group.get_single_plan(1) is first
    assert events[-3:] == [("spectra", 1), "settle", ("load", 1)]


def test_cpu_groups_of_one_block_length_share_a_batched_plan(monkeypatch):
    """Every CPU group of one block length loads its template into the same plan, which takes
    several blocks per kernel call. The template is loaded when the plan holds another one --
    another row, or the same row of another group -- and not otherwise."""
    from matchedfilter import time_domain
    created, loads = [], []

    class Plan:
        def __init__(self, n, ndata=None, ntemplates=None, device=None):
            created.append((n, ndata, ntemplates, device))

        def set_templates(self, spectra):
            loads.append(int(spectra[0, 0].real))

    def spectra_of(base):
        return lambda rows: np.full((1, 64), base + rows.start, np.complex64)

    monkeypatch.setattr(matchedfilter, "MatchedFilter", Plan)
    monkeypatch.setattr(time_domain, "_SINGLE_CPU_PLANS", {})
    a = _TemplateGroup(None, 64, np.arange(3), 0, 64, 1, device="cpu", row_source=spectra_of(0))
    b = _TemplateGroup(None, 64, np.arange(3), 0, 64, 1, device="cpu", row_source=spectra_of(10))
    other = _TemplateGroup(None, 128, np.arange(3), 0, 128, 1, device="cpu",
                           row_source=spectra_of(20))
    plan = a.get_single_plan(1)
    assert a.get_single_plan(1) is plan and loads == [1]         # held: not loaded again
    assert a.get_single_plan(2) is plan and loads == [1, 2]
    assert b.get_single_plan(2) is plan and loads == [1, 2, 12]  # same row, another group
    assert a.get_single_plan(2) is plan and loads == [1, 2, 12, 2]
    assert other.get_single_plan(0) is not plan                  # another block length
    assert created == [(64, time_domain._single_plan_blocks(64), 1, "cpu"),
                       (128, time_domain._single_plan_blocks(128), 1, "cpu")]
    assert time_domain._single_plan_blocks(64) > 1
