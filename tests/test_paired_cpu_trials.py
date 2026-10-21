"""Comparable CPU trial rounds: load bursts, work variation, and persistence."""
import types

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import gatechain as gc


@pytest.mark.parametrize('model', [False, True])
@pytest.mark.parametrize('burst_arm', [False, True])
def test_q15_gain_survives_one_arm_burst_and_workload_variation(model, burst_arm):
    samples = {False: [], True: []}
    for i, work in enumerate([1, 100, 0.01, 17, 3, 0.8]):
        for arm in samples:
            samples[arm].append(work * (0.8 if arm else 1) * (100 if i == 1 and arm == burst_arm else 1))
    assert gc.paired_choice(samples, model, 12, minimum=6)[0] is True


def test_model_does_not_lock_from_two_misleading_rounds():
    samples = {False: [1, 1], True: [8, 8]}
    assert gc.paired_choice(samples, False, 12)[0] is None
    for _ in range(10):
        samples[False].append(1)
        samples[True].append(0.8)
    assert gc.paired_choice(samples, False, 12)[0] is True


def test_ambiguous_pairs_are_bounded_and_ties_keep_model():
    samples = {False: [1] * 6, True: [0.8, 1.2] * 3}
    assert gc.paired_choice(samples, False, 12)[0] is None
    assert gc.paired_choice(samples, False, 6)[0] is False
    assert gc.paired_choice({False: [1] * 6, True: [0.99] * 6}, False, 12)[0] is False


def test_partial_round_is_not_a_pair():
    with pytest.raises(ValueError, match='complete rounds'):
        gc.paired_choice({False: [1], True: []}, False, 12)


def _plan(monkeypatch, path):
    monkeypatch.setenv('MF_COST_FILE', str(path))
    monkeypatch.setattr(mf, '_Q15_TRIALS', {})
    p = object.__new__(mf.HierarchicalFilter)
    p.n, p._fs_snr, p.snr, p.fd = 2048, None, 6, 0.001
    p._chain, p._q15_pref = (256, 512, 1024), False
    p.device = 'cpu:0'
    return p


def test_complete_q15_rounds_resume_across_processes(monkeypatch, tmp_path):
    path = tmp_path / 'costs.json'
    for i in range(6):
        p = _plan(monkeypatch, path)
        p._q15_record_pair({False: 1 + i, True: 0.8 * (1 + i)}, 100)
    p = _plan(monkeypatch, path)
    assert p._q15_trial().winner is True
    assert len(p._q15_trial().samples[False]) == 0  # locked: no more sampling


def test_q15_replay_reverses_order_and_excludes_settle_time(monkeypatch, tmp_path):
    p = _plan(monkeypatch, tmp_path / 'costs.json')
    arm, calls = [False], []
    p._mf = types.SimpleNamespace(set_q15=lambda on: arm.__setitem__(0, on))
    clock = [0.0]
    monkeypatch.setattr(mf.time, 'perf_counter', lambda: clock[0])
    def run():
        calls.append(arm[0])
        clock[0] += (0.8 if arm[0] else 1) + (100 if len(calls) % 2 else 0)
        return len(calls)
    assert p._q15_run_pair(run, 1) == 4
    assert p._q15_run_pair(run, 1) == 8
    assert calls == [False, False, True, True, True, True, False, False]
    np.testing.assert_allclose(p._q15_trial().samples[False], [1, 1])
    np.testing.assert_allclose(p._q15_trial().samples[True], [0.8, 0.8])


def test_block_complete_rounds_persist_and_reject_unpaired_history(monkeypatch, tmp_path):
    from matchedfilter import time_domain as td
    path = tmp_path / 'costs.json'
    monkeypatch.setenv('MF_COST_FILE', str(path))
    key = 'cpu|2048,4096'
    gc._store_cost(path, 'choice|block-trial|' + key, {'samples': {'0': [100] * 4, '1': [1] * 4}})
    for i in range(5):
        trial = td._BlockTrials()
        trial.record_cpu_round(key, {0: 1, 1: 1.2})
        assert trial.winner(key) == (0 if i == 4 else None)
    assert td._BlockTrials().winner(key) == 0


def test_block_pair_runner_reverses_and_settles_each_layout(monkeypatch, tmp_path):
    from matchedfilter import time_domain as td
    monkeypatch.setenv('MF_COST_FILE', str(tmp_path / 'costs.json'))
    monkeypatch.setattr(td, '_BLOCK_TRIALS', td._BlockTrials())
    bank = types.SimpleNamespace(device='cpu', _choice_ns=(2048, 4096), _layouts=[{}, {}], rank=0, filters_f=[0, 1])
    bank._use_layout = lambda r: setattr(bank, 'rank', r)
    clock, calls = [0.0], []
    monkeypatch.setattr(mf.time, 'perf_counter', lambda: clock[0])
    def run(jobs):
        assert td._BLOCK_TRIALS.cpu_replaying
        assert td._trial_begin(jobs) is None
        calls.append(bank.rank)
        clock[0] += (1 if bank.rank == 0 else 0.8) + (100 if len(calls) % 2 else 0)
        return [len(calls)]
    monkeypatch.setattr(td.TimeDomainFilterBank, 'filter_series_many', run)
    jobs = [(bank, np.zeros(10), {})]
    assert td._cpu_block_round(jobs) == [4]
    assert td._cpu_block_round(jobs) == [8]
    assert calls == [0, 0, 1, 1, 1, 1, 0, 0]
    assert not td._BLOCK_TRIALS.cpu_replaying
    np.testing.assert_allclose(td._BLOCK_TRIALS._st(td._trial_key(bank)).samples[0], [0.05, 0.05])


def test_block_replay_exception_releases_guard(monkeypatch, tmp_path):
    from matchedfilter import time_domain as td
    monkeypatch.setenv('MF_COST_FILE', str(tmp_path / 'costs.json'))
    monkeypatch.setattr(td, '_BLOCK_TRIALS', td._BlockTrials())
    bank = types.SimpleNamespace(device='cpu', _choice_ns=(2048, 4096), _layouts=[{}, {}], filters_f=[0, 1])
    bank._use_layout = lambda r: None
    def fail(jobs):
        raise RuntimeError('failure')
    monkeypatch.setattr(td.TimeDomainFilterBank, 'filter_series_many', fail)
    with pytest.raises(RuntimeError, match='failure'):
        td._cpu_block_round([(bank, np.zeros(10), {})])
    assert not td._BLOCK_TRIALS.cpu_replaying
    assert not td._BLOCK_TRIALS._st(td._trial_key(bank)).sampled


@pytest.mark.parametrize('raw', [False, True])
def test_q15_replays_return_the_same_real_series_results(monkeypatch, tmp_path, raw):
    if not mf._q15_available(256):
        pytest.skip('backend has no Q15 screen')
    monkeypatch.setenv('MF_AUTOTUNE', '1')
    monkeypatch.setenv('MF_COST_FILE', str(tmp_path / 'costs.json'))
    rng = np.random.default_rng(123)
    p = mf.HierarchicalFilter(1024, 1, 7, chain=(256, 512))
    p.set_coarse_threshold([0, 0])
    templates = (rng.normal(size=(7, 1024)) + 1j * rng.normal(size=(7, 1024))).astype(np.complex64)
    templates /= np.linalg.norm(templates, axis=1, keepdims=True)
    p.set_templates(templates)
    series = rng.normal(size=4096).astype(np.float32)
    starts = np.array([0, 1024, 2048], np.int64)
    p._trial_hold = True
    ref = p.run_series(series, starts=starts, win_start=np.zeros(3, np.int64),
                           win_end=np.full(3, 1024, np.int64), raw=raw)
    ref = tuple(x.copy() for x in ref) if raw else ref.copy()
    p._trial_hold = False
    for _ in range(2):
        got = p.run_series(series, starts=starts, win_start=np.zeros(3, np.int64),
                           win_end=np.full(3, 1024, np.int64), raw=raw)
        if raw:
            for a, b in zip(got, ref):
                np.testing.assert_array_equal(a, b)
        else:
            np.testing.assert_array_equal(got, ref)
    assert len(p._q15_trial().samples[False]) == 2


def test_noisy_fast_median_does_not_hide_a_consistent_challenger():
    samples = {0: [1] * 6, 1: [0.5, 1.1] * 3, 2: [0.9] * 6}
    # Rank 1 has the best median, but only rank 2 has consistent evidence of a win.
    assert np.median(samples[1]) < np.median(samples[2])
    assert gc.paired_choice(samples, 0, 6)[0] == 2
