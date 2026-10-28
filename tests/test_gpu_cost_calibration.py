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


class _Resident(np.ndarray):
    """A series in the probe's device memory (Plan.empty_shared)."""


def _probe_calibration(monkeypatch, kind="f32", step=0.0, host=1.0, spell=None, reps=2, lost=None):
    """Exercise the real calibration with deterministic device times and survivor counts.
    step: device time a two-tier call adds whenever anything passes its first tier.
    host: how much slower a call runs on a series copied from the host than on one resident
    in device memory (the device idles through the copy). spell(i): how much slower the
    i-th device call runs (a slow spell spans consecutive calls, whatever they run).
    lost(i): whether the i-th call's timer records nothing (a rejected timestamp pair)."""
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

        def empty_shared(self, shape, dtype=np.complex64):
            return np.empty(shape, dtype).view(_Resident)

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
            ns *= (1.0 if isinstance(series, _Resident) else host)
            ns *= spell(len(calls) - 1) if spell is not None else 1.0
            if self._gpu._timing and not (lost is not None and lost(len(calls) - 1)):
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
        cm = _calibration.calibrate_costs_gpu(n, "probe", blocks=blocks, reps=reps, nt=nt)
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


def _assert_probe_prices(cm):
    assert cm.block == pytest.approx(100.0)
    assert cm.dense == pytest.approx({64: 2.0, 128: 4.0})
    for density in (0.01, 0.1):
        assert cm.refine(density) == pytest.approx(80.0)
        assert cm.sparse(128, density) == pytest.approx(10.0)


def test_calibration_times_calls_on_a_series_resident_in_device_memory(monkeypatch):
    """The fine stage reads its middle series where it lies in device memory. A series
    copied from the host on every call (16 MB at n=2048) left an 8060S idle long enough to
    run the timed call up to 1.8x slower, by a varying amount: the calibration must time
    calls as the fine stage makes them."""
    cm, _ = _probe_calibration(monkeypatch, host=1.8)
    _assert_probe_prices(cm)


def test_a_slow_spell_moves_no_price(monkeypatch):
    """A spell of slow calls (here 6 in a row at 2x, every 24 calls) spans whatever runs
    then: with a configuration's repetitions back to back it covered a whole run and its
    median, and moved a second tier's slope 2.3x on an 8060S. Repetitions are taken in
    turn across configurations and each price is its fastest, so a spell slows one
    repetition of several configurations, never all of one."""
    cm, _ = _probe_calibration(monkeypatch, spell=lambda i: 2.0 if (i // 6) % 4 == 1 else 1.0,
                               reps=5)
    _assert_probe_prices(cm)


def test_a_price_is_its_configurations_fastest_call_not_its_median(monkeypatch):
    """What moves a call only adds time, so a price is its configuration's fastest call:
    here two of every three back-to-back calls run 1.5x slow, so every configuration's
    median is slow and only its fastest call is its time."""
    cm, _ = _probe_calibration(monkeypatch, spell=lambda i: 1.0 if i % 3 == 0 else 1.5, reps=3)
    _assert_probe_prices(cm)


def test_a_call_whose_timer_recorded_nothing_moves_no_price(monkeypatch):
    """A call whose timestamps were rejected logs no time: it is not a measurement, so it
    cannot be a configuration's fastest (as a time of zero it made a price zero)."""
    cm, _ = _probe_calibration(monkeypatch, lost=lambda i: i % 7 == 3, reps=3)
    _assert_probe_prices(cm)


def test_the_clock_anchor_is_timed_on_a_warmed_device_however_long_the_first_call_takes(monkeypatch):
    """The anchor every calibration in a process is scaled to is the reference's fastest call
    on a warmed device. The first call records the plan's commands: 0.06 s on an idle 8060S,
    0.4-0.5 s with eight other processes on its four cores, longer than the 0.25 s warm-up.
    Timed from before that call, the warm-up had already run out, and the anchor was taken
    on a device still at its idle clock in 17 of 178 loaded processes (0.105-0.134 ms against
    0.028-0.031), which scaled every price of their models 2.8-4.3x. Here the first call
    takes 0.4 s and the device runs 4x slow for its first 20 calls."""
    now, calls = [0.0], []

    class Plan:
        def __init__(self, size, ndata, ntemplates, chain, device):
            self.log = []
            self._gpu = SimpleNamespace(_timing=False, timings=lambda: self.log)

        def set_templates(self, spectra):
            pass

        def set_coarse_threshold(self, thresholds):
            pass

        def empty_shared(self, shape, dtype=np.complex64):
            return np.empty(shape, dtype)

        def run_series(self, series, starts, ws, we, threshold):
            calls.append(len(calls))
            now[0] += 0.4 if len(calls) == 1 else 1e-3
            self.log.append(("run", 0.12 if len(calls) <= 20 else 0.03))

    monkeypatch.setattr(mf, "HierarchicalFilter", Plan)
    monkeypatch.setattr(time, "perf_counter", lambda: now[0])
    ref = _calibration._ClockRef("probe")
    assert len(calls) > 200                         # 0.25 s of calls after the first
    assert ref.anchor == pytest.approx(0.03e6)
