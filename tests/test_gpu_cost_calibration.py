"""Device cost calibration without a GPU: recover known prices from synthetic timers."""
import itertools
import math
import time
from types import SimpleNamespace

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _calibration
from matchedfilter import gatechain as gc


def _probe_calibration(monkeypatch, kind="f32", step=0.0):
    """Exercise the real calibration with deterministic device times and survivor counts.
    step: device time a two-tier call adds whenever anything passes its first tier."""
    n, blocks, nt = 256, 16, 64
    inputs = _calibration._gpu_cal_inputs(n, blocks, nt, 11)
    calls, raw_calls = [], []
    dense = {64: 2.0, 128: 4.0}
    bound = 2.0 if kind != "f32" else 1.0

    class Plan:
        def __init__(self, size, ndata, ntemplates, chain, device):
            assert size == n and ndata == 1
            self.nt, self.chain = ntemplates, chain
            self.log = []
            self._gpu = SimpleNamespace(_timing=False, timings=lambda: self.log)

        def set_templates(self, spectra):
            assert spectra.shape == (self.nt, n)

        def set_coarse_threshold(self, thresholds):
            self.thresholds = thresholds

        def run_series(self, series, starts, ws, we, threshold):
            calls.append((len(series), len(starts)))
            assert len(ws) == len(we) == len(starts)
            pairs = len(starts) * self.nt
            first = int(pairs * min(1.0, bound * math.exp(-self.thresholds[0])))
            refined = first
            ns = len(starts) * 100.0 + pairs * dense[self.chain[0]]
            if len(self.chain) > 1:
                ns += first * 10.0 + (step if first else 0.0)
                refined = int(first * math.exp(-self.thresholds[1]))
            ns += refined * 80.0
            self._gpu.last_tier1_survivors = first
            self._gpu.last_refinements = refined
            if self._gpu._timing:
                # The reference says the device currently runs twice as slowly.
                self.log.extend([("run", 2 * ns / 1e6), ("k:coarse", 999.0)])

    def raw_survivors(*args):
        raw_calls.append(args)
        return [(b, g, int(blocks * nt * math.exp(-g)))
                for b in dense for g in (2.0, 4.0)]

    monkeypatch.setattr(mf, "HierarchicalFilter", Plan)
    monkeypatch.setattr(gc, "_COSTS", {})
    monkeypatch.setattr(gc, "_cost_file", lambda: None)
    monkeypatch.setattr(_calibration, "_gpu_cal_inputs", lambda *args: inputs)
    monkeypatch.setattr(gc, "gpu_gate_kind", lambda device: kind)
    monkeypatch.setattr(gc, "_is_gpu", lambda device: True)
    monkeypatch.setattr(_calibration, "_raw_gate_survivors", raw_survivors)
    monkeypatch.setattr(_calibration, "_clock_ref", lambda device: SimpleNamespace(anchor=2.0, time=lambda: 4.0))
    # Skip the wall-clock warm-up wait; this probe has no physical device to warm.
    with monkeypatch.context() as clock_patch:
        clock_patch.setattr(time, "perf_counter", itertools.count().__next__)
        cm = _calibration.calibrate_costs_gpu(n, "probe", blocks=blocks, reps=2, nt=nt)
    expected_shape = (len(inputs[1]), blocks)
    metrics = {"device_calls": len(calls),
               "host_only_calls": sum(shape != expected_shape for shape in calls),
               "raw_gate_calls": len(raw_calls)}
    return cm, metrics


@pytest.mark.parametrize("kind", ["f32", "c16b"])
def test_calibration_recovers_active_costs(monkeypatch, kind):
    """Removing unused batches preserves clock correction, tier prices, and gate excess."""
    cm, metrics = _probe_calibration(monkeypatch, kind)
    assert cm.block == pytest.approx(100.0)
    assert cm.forward == cm.block and cm.band_forward
    assert cm.dense == pytest.approx({64: 2.0, 128: 4.0})
    for density in (0.01, 0.1):
        assert cm.refine(density) == pytest.approx(80.0)
        assert cm.sparse(128, density) == pytest.approx(10.0)
    assert metrics["host_only_calls"] == 0
    assert metrics["raw_gate_calls"] == (kind != "f32")
    if kind == "f32":
        assert cm.excess == {}
    else:
        expected = sorted((int(1024 * math.exp(-g)) / 1024,
                           int(2048 * math.exp(-g)) / 1024) for g in (2.0, 4.0))
        np.testing.assert_array_equal(cm.excess[64], expected)
        np.testing.assert_array_equal(cm.excess[128], expected)


def test_a_second_tiers_price_is_its_slope_not_a_fixed_cost_on_few_survivors(monkeypatch):
    """A cost a two-tier call pays whenever anything passes (a launch, a process's state) is
    not a per-survivor price: spread over the 1% point's few survivors it once made a second
    tier look 3-20x dearer than it ran (_calibration._sparse_rows)."""
    cm, _ = _probe_calibration(monkeypatch, step=5000.0)
    for density in (0.01, 0.1):
        assert cm.sparse(128, density) == pytest.approx(10.0)
    assert _calibration._sparse_rows([(100, 1000.0)], 500.0, 1000) == [(0.1, 5.0)]
