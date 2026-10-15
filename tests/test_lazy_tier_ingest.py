"""Series data slots must refresh every coarse tier when they are reused."""
import numpy as np
import pytest

import matchedfilter as mf


N = 1024
CHAIN = (64, 128, 512)


def make_plan(q15, thresholds, ndata=3):
    plan = mf.HierarchicalFilter(N, ndata, 3, chain=CHAIN)
    templates = np.zeros((3, N), np.complex64)
    templates[:, 0] = [1, 1j, -1]
    plan.set_templates(templates)
    plan.set_coarse_threshold(thresholds)
    if q15 and not plan._mf.set_q15(True):
        pytest.skip("Q15 unavailable on this CPU target")
    if not q15:
        plan._mf.set_q15(False)
    plan._q15 = q15
    return plan


@pytest.mark.parametrize("group", [1, 3])
@pytest.mark.parametrize("kind", ["complex", "real", "strided_real"])
@pytest.mark.parametrize("q15", [False, True])
def test_series_slot_reuse_and_repeated_windows(monkeypatch, group, kind, q15):
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_DGROUP", str(group))
    monkeypatch.setenv("MF_GATE16", "0")
    # Long equal-window runs reuse slots, repeated starts search another window,
    # and the final block is zero padded. Zero/nonzero blocks change which tiers
    # run; comparing each row to a fresh one-block plan detects stale data even
    # when both a reused and a fresh multi-block plan would make the same mistake.
    starts = np.array([0, 1, 2, 3, 4, 5, 0, 2, 6, 7, 8, 8], np.uintp) * N
    low = np.array([17] * 6 + [61, 123, 17, 17, 17, 99], np.uintp)
    high = np.array([901] * 6 + [401, 789, 901, 901, 901, 300], np.uintp)
    amplitudes = np.array([0, 2, 0, 4, 0, 8, 2, 0, 4], np.float32)
    length = 8 * N + 379
    if kind == "complex":
        series = np.empty(length, np.complex64)
    elif kind == "real":
        series = np.empty(length, np.float32)
    else:
        storage = np.full((length, 2), 12345, np.float32)
        series = storage[:, 0]
        assert series.strides == (8,)
    plan = make_plan(q15, [0.5] * len(CHAIN))
    schedules = ([0.5] * 3, [1e6] * 3, [0.0] * 3,
                 [0.5, 1e6, 0.5], [0.5, 0.5, 1e6], [0.5] * 3)
    for turn, thresholds in enumerate(schedules):
        block_amplitudes = np.roll(amplitudes, turn)
        if thresholds[0] == 0:
            block_amplitudes = block_amplitudes + 1
        series[:] = np.repeat(block_amplitudes, N)[:length]
        if kind == "complex" and turn % 2:
            series *= 1j
        plan.set_coarse_threshold(thresholds)
        before = plan.stats
        actual = plan.run_series(series, starts, low, high, binsize=N,
                                 threshold=0.25, raw=True)
        expected = []
        pairs = refined = 0
        for start, lo, hi in zip(starts, low, high):
            oracle = make_plan(q15, thresholds)
            result = oracle.run_series(series, np.array([start], np.uintp),
                                       np.array([lo], np.uintp), np.array([hi], np.uintp),
                                       binsize=N, threshold=0.25, raw=True)
            expected.append(tuple(a.copy() for a in result))
            p, r = oracle.stats
            pairs += p
            refined += r
        for part in range(2):
            np.testing.assert_array_equal(actual[part], np.concatenate([r[part] for r in expected]))
        assert tuple(a - b for a, b in zip(plan.stats, before)) == (pairs, refined)
        if max(thresholds) > 1e5:
            assert refined == 0
        elif thresholds[0] == 0:
            assert refined == len(starts) * plan.ntemplates
        else:
            assert 0 < refined < len(starts) * plan.ntemplates


@pytest.mark.parametrize("q15", [False, True])
def test_public_set_data_after_series_keeps_eager_coarse_copies(monkeypatch, q15):
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_DGROUP", "3")
    monkeypatch.setenv("MF_GATE16", "0")
    plan = make_plan(q15, [0.5] * 3)
    # Leave later series tiers unused, then replace the public frequency-domain
    # inputs. The full refine retains the input pointer, but every coarse tier
    # has historically copied it immediately at set_data.
    plan.run_series(np.zeros(4 * N, np.complex64),
                    np.arange(4, dtype=np.uintp) * N,
                    np.zeros(4, np.uintp), np.full(4, N, np.uintp),
                    binsize=N, threshold=0.25)
    spectra = np.zeros((plan.ndata, N), np.complex64)
    spectra[:, 0] = [2, 4, 8]
    plan.set_data(spectra)
    spectra[:] = 0
    before = plan.stats
    indices, _ = plan.run(binsize=N, threshold=0.25, raw=True)
    # Old nonzero coarse copies pass every pair. The lazy full refine reads the
    # now-zero spectrum, so no peak is reported. Deferring public coarse copies
    # would incorrectly skip refinement too.
    assert (indices < 0).all()
    assert tuple(a - b for a, b in zip(plan.stats, before)) == (9, 9)
    # The indexed setter must refresh the same state after another series call.
    plan.run_series(np.zeros(2 * N, np.complex64),
                    np.arange(2, dtype=np.uintp) * N,
                    np.zeros(2, np.uintp), np.full(2, N, np.uintp),
                    binsize=N, threshold=0.25)
    for row in range(plan.ndata):
        spectrum = np.zeros(N, np.complex64)
        spectrum[0] = 4
        plan.set_data(spectrum, index=row)
        spectrum[:] = 0
    before = plan.stats
    plan.run(binsize=N, threshold=0.25, raw=True)
    assert tuple(a - b for a, b in zip(plan.stats, before)) == (9, 9)
