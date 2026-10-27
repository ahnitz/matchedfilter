"""The paired rule (_choice.paired_choice): load bursts, work variation, ties, and when
a candidate can no longer win (_choice.can_still_win)."""
import numpy as np
import pytest

from matchedfilter import _choice


@pytest.mark.parametrize('model', [False, True])
@pytest.mark.parametrize('burst_arm', [False, True])
def test_q15_gain_survives_one_arm_burst_and_workload_variation(model, burst_arm):
    samples = {False: [], True: []}
    for i, work in enumerate([1, 100, 0.01, 17, 3, 0.8]):
        for arm in samples:
            samples[arm].append(work * (0.8 if arm else 1) * (100 if i == 1 and arm == burst_arm else 1))
    assert _choice.paired_choice(samples, model, 12, minimum=6)[0] is True


def test_model_does_not_lock_from_two_misleading_rounds():
    samples = {False: [1, 1], True: [8, 8]}
    assert _choice.paired_choice(samples, False, 12)[0] is None
    for _ in range(10):
        samples[False].append(1)
        samples[True].append(0.8)
    assert _choice.paired_choice(samples, False, 12)[0] is True


def test_ambiguous_pairs_are_bounded_and_ties_keep_model():
    samples = {False: [1] * 6, True: [0.8, 1.2] * 3}
    assert _choice.paired_choice(samples, False, 12)[0] is None
    assert _choice.paired_choice(samples, False, 6)[0] is False
    assert _choice.paired_choice({False: [1] * 6, True: [0.99] * 6}, False, 12)[0] is False


def test_partial_round_is_not_a_pair():
    with pytest.raises(ValueError, match='complete rounds'):
        _choice.paired_choice({False: [1], True: []}, False, 12)


def test_noisy_fast_median_does_not_hide_a_consistent_challenger():
    samples = {0: [1] * 6, 1: [0.5, 1.1] * 3, 2: [0.9] * 6}
    # Rank 1 has the best median, but only rank 2 has consistent evidence of a win.
    assert np.median(samples[1]) < np.median(samples[2])
    assert _choice.paired_choice(samples, 0, 6)[0] == 2


def test_a_candidate_is_dropped_exactly_when_no_rounds_to_come_could_make_it_win():
    """can_still_win agrees with paired_choice: for every history of wins and losses short of
    the cap, a candidate can still win iff some continuation of rounds makes paired_choice
    choose it."""
    import itertools
    from matchedfilter import _choice
    cap = 6
    for count in range(1, cap):
        for hist in itertools.product((0.8, 1.0), repeat=count):
            model = [1.0] * count
            reachable = False
            for rest in itertools.product((0.8, 1.0), repeat=cap - count):
                for k in range(count, cap + 1):
                    smp = {"m": [1.0] * k, "c": list(hist + rest)[:k]}
                    if _choice.paired_choice(smp, "m", cap, minimum=1)[0] == "c":
                        reachable = True
                        break
                if reachable:
                    break
            assert _choice.can_still_win(list(hist), model, cap) == reachable, hist
