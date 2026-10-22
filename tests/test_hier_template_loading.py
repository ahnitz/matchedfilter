"""Template ingestion and ownership when a CPU hierarchical plan is first built."""
import weakref

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter.time_domain import _TemplateGroup


@pytest.fixture
def deferred_filter(monkeypatch):
    """Exercise the real lazy wrapper without timing a gate-model calibration."""
    hf = mf.HierarchicalFilter(256, ndata=2, ntemplates=3)
    hf.set_reference(np.ones(hf.n, np.float32))
    events, plans = [], []

    class Plan:
        def __init__(self):
            self.k = hf.k
            self.batches = []
            events.append("create")

        def set_reference(self, reference):
            self.reference = reference.copy()
            events.append("reference")

        def set_template_batch(self, start, templates):
            assert start == 0
            assert templates.dtype == np.complex64
            assert templates.flags.c_contiguous
            self.batches.append(templates.copy())
            events.append("templates")

        def set_template(self, index, template):
            self.batches[-1][index] = template
            events.append(("template", index))

        def set_data_batch(self, start, data):
            assert start == 0
            self.data = data.copy()
            events.append("data")

    def create(chain):
        plan = Plan()
        plans.append(plan)
        return plan

    monkeypatch.setattr(hf, "_choose_chain", lambda: (64,))
    monkeypatch.setattr(hf, "_new_cpu_plan", create)
    return hf, events, plans


def test_group_initial_load_generates_and_ingests_once(deferred_filter):
    hf, events, plans = deferred_filter
    generated = []

    def source():
        events.append("source")
        spectra = np.ones((hf.ntemplates, hf.n), np.complex64)
        generated.append(weakref.ref(spectra))
        return spectra

    group = _TemplateGroup(hf, hf.n, np.arange(hf.ntemplates), 0, hf.n, 1,
                           spectra_source=source)
    group.load_templates(hf)

    assert events == ["source", "create", "reference", "templates"]
    assert len(plans[0].batches) == 1
    assert hf._held_templates is None
    assert generated[0]() is None
    hf._require_templates(0, hf.ntemplates)


@pytest.mark.parametrize("source_backed", [False, True])
def test_explicit_batches_replace_once_and_restore_data(deferred_filter, source_backed):
    hf, events, plans = deferred_filter

    def unwanted_source():
        pytest.fail("an explicit batch must not be regenerated")

    if source_backed:
        hf.set_template_source(unwanted_source)
    # Conversion and contiguity validation still happen before building the plan.
    first = np.arange(hf.ntemplates * hf.n * 2).reshape(hf.ntemplates, -1)[:, ::2]
    hf.set_templates(first)
    np.testing.assert_array_equal(plans[0].batches[0], first)
    assert len(plans[0].batches) == 1
    data = np.ones((hf.ndata, hf.n), np.complex64)
    hf.set_data(data)

    replacement = np.full((hf.ntemplates, hf.n), 2 + 3j, np.complex64)
    events.clear()
    hf.set_templates(replacement)
    assert events == ["templates"]
    np.testing.assert_array_equal(plans[0].batches[-1], replacement)

    # Both shape transitions build a plan with the new batch, retaining loaded data.
    for width in (hf.n // 2, hf.n):
        replacement = np.full((hf.ntemplates, width), width + 1j, np.complex64)
        events.clear()
        hf.set_templates(replacement)
        assert events == ["create", "reference", "templates", "data"]
        assert len(plans[-1].batches) == 1
        np.testing.assert_array_equal(plans[-1].batches[0], replacement)
        np.testing.assert_array_equal(plans[-1].data, data)
        assert (hf._held_templates is None) == source_backed
        if not source_backed:
            assert not np.shares_memory(hf._held_templates, replacement)


def test_source_is_used_for_reference_changes_and_chain_rebuilds(deferred_filter):
    hf, events, plans = deferred_filter
    templates = np.ones((hf.ntemplates, hf.n), np.complex64)

    def source():
        events.append("source")
        return templates.copy()

    hf.set_template_source(source)
    hf.set_templates(templates)
    hf.set_data(np.ones((hf.ndata, hf.n), np.complex64))
    events.clear()
    hf.set_reference(np.arange(1, hf.n + 1, dtype=np.float32))
    assert events == ["reference", "source", "templates"]
    assert hf._held_templates is None

    events.clear()
    hf._switch_chain((128,))
    assert events == ["create", "reference", "source", "templates", "data"]
    assert hf._held_templates is None
    np.testing.assert_array_equal(plans[-1].batches[0], templates)


def test_owned_batch_survives_caller_mutation_and_rebuild(deferred_filter):
    hf, events, plans = deferred_filter
    templates = np.ones((hf.ntemplates, hf.n), np.complex64)
    hf.set_templates(templates)
    templates[:] = 9
    hf._switch_chain((128,))
    np.testing.assert_array_equal(plans[-1].batches[0], 1)

    # Indexed updates keep the existing route and are replayed with the other rows.
    replacement = np.full(hf.n, 4 + 2j, np.complex64)
    events.clear()
    hf.set_templates(replacement, index=1)
    assert events == [("template", 1)]
    hf._switch_chain((64,))
    np.testing.assert_array_equal(plans[-1].batches[0][1], replacement)
    np.testing.assert_array_equal(plans[-1].batches[0][[0, 2]], 1)


@pytest.mark.parametrize("shape", [(256,), (2, 256), (3, 129)])
def test_invalid_batch_does_not_build_or_invoke_source(deferred_filter, shape):
    hf, events, plans = deferred_filter
    hf.set_template_source(lambda: pytest.fail("invalid input must not invoke the source"))
    with pytest.raises(ValueError):
        hf.set_templates(np.ones(shape))
    assert events == []
    assert plans == []
    assert hf._held_templates is None
    with pytest.raises(ValueError, match="no templates"):
        hf._require_templates(0, hf.ntemplates)


@pytest.mark.parametrize("source_backed", [False, True])
def test_lazy_native_ingestion_matches_prebuilt_plan(monkeypatch, source_backed):
    """Real native results agree through replacements, rebuilds and subset runs."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setattr(mf._prices, "_cpu_forward_platform", lambda n: False)
    n, nt, nd = 256, 3, 2
    rng = np.random.default_rng(826)
    templates = (rng.normal(size=(nt, n)) + 1j * rng.normal(size=(nt, n))).astype(np.complex64)
    templates[:, n // 2:] = 0
    data = (rng.normal(size=(nd, n)) + 1j * rng.normal(size=(nd, n))).astype(np.complex64)
    reference = np.arange(1, n + 1, dtype=np.float32)

    lazy = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt)
    monkeypatch.setattr(lazy, "_choose_chain", lambda: (64,))
    # Gate calibration is irrelevant to ingestion; admit every pair in both plans.
    monkeypatch.setattr(lazy, "_thresholds", lambda **kw: (0.0,))
    lazy.set_reference(reference)
    if source_backed:
        lazy.set_template_source(lambda: current)

    for width in (n, n // 2, n):
        current = np.ascontiguousarray(templates[:, :width])
        lazy.set_templates(current)
        lazy.set_data(data)
        expected = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, chain=(64,))
        expected.set_coarse_threshold(0.0)
        expected.set_reference(reference)
        expected.set_templates(current)
        expected.set_data(data)
        for subset in (None, (1, 1)):
            actual = lazy.run(binsize=32, threshold=0, templates=subset)
            want = expected.run(binsize=32, threshold=0, templates=subset)
            np.testing.assert_array_equal(actual["index"], want["index"])
            np.testing.assert_array_equal(actual["value"], want["value"])
        assert (lazy._held_templates is None) == source_backed
