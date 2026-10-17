"""Reorder independent gates without changing their intersection or final peaks."""
from types import SimpleNamespace

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core, _roofline, gatechain

N = 2048
CHAIN = (256, 512, 1024)


def noise(rng, shape):
    return (rng.normal(size=shape) + 1j * rng.normal(size=shape)).astype(np.complex64)


def native_plan(templates, group, late):
    p = _core.HMF(N, 1, len(templates), list(CHAIN), group, N)
    p.set_reference(np.ones(N, np.float32))
    p.set_template_batch(0, templates)
    assert p.set_q15_recheck_late(late)
    return p


def counters(p):
    return np.array([*p.tier_inputs(), *(x[1] for x in p.tier_stats()),
                     p.q15_stats()[1], p.first_gate_passed(), *p.stats()], np.int64)


@pytest.mark.parametrize('group', [1, 3, 8])
@pytest.mark.parametrize('binsize', [N, 173])
@pytest.mark.parametrize('kind', ['complex', 'real', 'strided_real'])
def test_reordered_series_reuse_updates_and_counters(group, binsize, kind):
    mf.backend()
    rng = np.random.default_rng(501)
    nt = 43
    templates = noise(rng, (nt, N))
    templates *= np.float32(np.sqrt(N)) / np.linalg.norm(templates, axis=1, keepdims=True)
    plans = [native_plan(templates, group, late) for late in (False, True)]
    if kind != 'complex':
        for p in plans:
            assert p.set_real_series(True, 2 if kind == 'strided_real' else 1)
    starts = np.r_[np.arange(11) * 1536, 0].astype(np.uintp)
    low = np.array([192] * 6 + [224] * 6, np.uintp)
    high = low + 1536
    nb = (1536 + binsize - 1) // binsize
    schedules = [(True, [4.1, 4.76, 5.48]), (True, [0., 0., 0.]),
                 (True, [4., 1e6, 0.]), (True, [4., 0., 1e6]),
                 (False, [4.1, 4.76, 5.48]), (True, [4.1, 4.76, 5.48])]
    saw_peaks = False
    for turn, (q15, thresholds) in enumerate(schedules):
        source = noise(rng, 10 * 1536 + N - 379)
        source[2*N:3*N] = 0
        source[4*N:5*N] *= 12
        if kind == 'real':
            source = source.real.copy()
        # stride=2 reads the real lane of the contiguous complex backing buffer.
        if turn == 5:
            templates = noise(rng, (nt, N))
            templates *= np.float32(np.sqrt(N)) / np.linalg.norm(templates, axis=1, keepdims=True)
            for p in plans:
                p.set_template_batch(0, templates)
        results, counts = [], []
        for late, p in enumerate(plans):
            if q15 and not p.set_q15(True):
                pytest.skip('Q15 unavailable')
            if not q15:
                p.set_q15(False)
            p.set_thresholds(thresholds)
            before = counters(p)
            shape = (len(starts), nt, nb)
            idx = np.full(shape, -99, np.int64)
            val = np.full(shape, complex(99, 99), np.complex64)
            mag = np.full(shape, 99, np.float32)
            cnt = np.full((len(starts), nt), -99, np.int32)
            total = p.run_series(source, starts, low, high, 0, nt, binsize, 0.5,
                                 idx, val, mag, cnt)
            assert total == cnt.sum()
            saw_peaks |= total > 0
            results.append((idx, val, mag, cnt))
            delta = counters(p) - before
            checked, passed = delta[:3], delta[3:6]
            refined, qpassed, first, pairs, triggers = delta[6:]
            assert pairs == len(starts) * nt
            assert refined == triggers == passed[-1]
            if late and q15:
                assert tuple(checked) == (passed[1], qpassed, passed[0])
                assert first == passed[1]
            else:
                assert tuple(checked) == (qpassed if q15 else pairs, passed[0], passed[1])
                assert first == passed[0]
            counts.append(delta)
        for got, want in zip(results[1], results[0]):
            np.testing.assert_array_equal(got, want)
        assert counts[0][6] == counts[1][6]
        assert counts[0][7] == counts[1][7]
        if q15:
            assert counts[1][3] == counts[0][4]  # same intersection after both gates
    assert saw_peaks


def test_reordered_direct_refine_keeps_last_gate_location():
    from test_direct_refine import _bank
    n, taps, lengths, templates, series, layout, ref, _ = _bank(T=17, nblocks=16, nsig=8)
    plans = [native_plan(templates, 3, late) for late in (False, True)]
    results = []
    for p in plans:
        p.set_reference(ref)
        p.set_template_batch(0, templates)
        p.set_taps(taps, taps.shape[1], lengths)
        assert p.set_direct(True, 4)
        if not p.set_q15(True):
            pytest.skip('Q15 unavailable')
        p.set_thresholds([4.1, 4.76, 5.48])
        starts, lo, hi = (np.asarray(x, np.uintp) for x in layout)
        shape = (len(starts), len(templates), 1)
        idx, val = np.zeros(shape, np.int64), np.zeros(shape, np.complex64)
        mag, cnt = np.zeros(shape, np.float32), np.zeros(shape[:2], np.int32)
        p.run_series(series, starts, lo, hi, 0, len(templates), n, 6., idx, val, mag, cnt)
        results.append((idx, val, mag, cnt))
    assert results[0][-1].sum() > 0
    for got, want in zip(results[1], results[0]):
        np.testing.assert_array_equal(got, want)


def test_unsupported_order_is_rejected():
    for chain in ([256], [256, 512], [128, 256, 512]):
        p = _core.HMF(N, 1, 1, chain, 1, N)
        assert not p.set_q15_recheck_late(True)
        assert p.set_q15_recheck_late(False)


def test_order_model_retains_unprofitable_and_uncovered_paths(monkeypatch):
    model = gatechain.CostModel(N, {256: 10., 512: 20.},
        {512: [(0.001, 2.), (1., 2.)]}, [(1., 10.)],
        screen={256: dict(dense=1., recheck=1., excess=[(0.01, 0.015), (1., 1.)])})
    monkeypatch.setattr(gatechain, 'usable_bands', lambda *a: list(CHAIN))
    samples = np.zeros((1000, 3))
    samples[:100, 0] = 10
    samples[:10, 1] = 10
    monkeypatch.setattr(gatechain, 'noise_block_maxima', lambda *a, **k: samples)
    choice = gatechain.q15_recheck_order(np.ones(N), N, CHAIN, [4., 5., 6.], model)
    assert choice['late']
    samples[:, 1] = 10
    assert not gatechain.q15_recheck_order(np.ones(N), N, CHAIN, [4., 5., 6.], model)['late']
    assert gatechain.q15_recheck_order(np.ones(N), N, (128, 256, 512), [4., 5., 6.], model) is None
    model.screen.clear()
    assert gatechain.q15_recheck_order(np.ones(N), N, CHAIN, [4., 5., 6.], model) is None


def test_roofline_uses_actual_gate_inputs():
    g = SimpleNamespace(n=N, n_valid=1536, template_indices=np.arange(10),
                        _stored_bins=N, is_hier=True, _plan=object())
    bank = SimpleNamespace(_groups=[g])
    after = dict(backend='cpu', chain=CHAIN, pairs=1000, checked=[20, 100, 15],
                 passed=[15, 20, 3], refined=3, q15=100, ident=1,
                 ticks=dict(tiers=[200, 300, 100], refine=30, q15=100, series=900))
    w = _roofline.Work()
    _roofline.fine_work(w, {'fine': {}}, {'fine': {id(g): after}}, [bank], 'cpu')
    assert [w.stages[f'tier{i} b{b}'].count for i, b in enumerate(CHAIN)] == [20, 100, 15]
    assert w.stages['refine n2048'].count == 3


@pytest.mark.parametrize('binsize', [N, 173])
def test_reordered_spectral_subranges_and_setter_refresh(binsize):
    rng = np.random.default_rng(511)
    templates, data = noise(rng, (53, N)), noise(rng, (6, N))
    plans = [_core.HMF(N, 6, 53, list(CHAIN), 3, N) for _ in range(2)]
    for late, p in enumerate(plans):
        p.set_reference(np.ones(N, np.float32))
        p.set_template_batch(0, templates)
        p.set_data_batch(0, data)
        if not p.set_q15(True):
            pytest.skip('Q15 unavailable')
        assert p.set_q15_recheck_late(late)
        p.set_thresholds([4.1, 4.76, 5.48])
    for turn in range(3):
        if turn:
            data[:] = noise(rng, data.shape) * (0 if turn == 1 else 3)
            templates[:] = noise(rng, templates.shape)
            for p in plans:
                p.set_data_batch(0, data)
                p.set_template_batch(0, templates)
        results = []
        lo, hi, nd, nt = 23, 1981, 3, 37
        nb = (hi - lo + binsize - 1) // binsize
        for p in plans:
            shape = (nd, nt, nb)
            idx, val = np.zeros(shape, np.int64), np.zeros(shape, np.complex64)
            mag, cnt = np.zeros(shape, np.float32), np.zeros(shape[:2], np.int32)
            p.run(2, nd, 5, nt, binsize, 0.5, lo, hi, idx, val, mag, cnt)
            results.append((idx, val, mag, cnt))
        for got, want in zip(results[1], results[0]):
            np.testing.assert_array_equal(got, want)


def test_automatic_order_is_resolved_on_update_not_each_call(monkeypatch):
    monkeypatch.setenv('MF_AUTOTUNE', '0')
    f = mf.HierarchicalFilter(N, 1, 3, chain=CHAIN)
    f.set_coarse_threshold([4.1, 4.76, 5.48])
    f.set_reference(np.ones(N, np.float32))
    p = f._ensure()
    # Exercise plan invalidation without calibration noise or an ISA requirement.
    f.device = SimpleNamespace(backend='AVX3', kind='cpu')
    monkeypatch.setattr(f, '_cost_model', lambda: None)
    calls = []
    def choose(*args, **kwargs):
        calls.append(tuple(args[3]))
        return {'late': True}
    monkeypatch.setattr(gatechain, 'q15_recheck_order', choose)
    assert f._execution_plan() is p
    assert f._q15_order_choice == {'late': True}
    assert f._execution_plan() is p
    assert len(calls) == 1
    f.set_coarse_threshold([4.2, 4.8, 5.5])
    f._execution_plan()
    assert calls[-1] == (4.2, 4.8, 5.5)
    assert len(calls) == 2
    f.set_reference(None)
    f._execution_plan()
    assert f._q15_order_choice is None
    assert len(calls) == 2
