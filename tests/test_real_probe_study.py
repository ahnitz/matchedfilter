"""Pure sampling/selection checks; importing the tool does not import MF."""
import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    "real_probe_study", Path(__file__).resolve().parents[1] / "tools" / "real_probe_study.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_pilot_keeps_complete_native_groups_inside_real_windows():
    low = [9] + [32] * 177 + [64] * 96 + [7]
    high = [2048] * len(low)
    rows, info = probe.stratified_rows(low, high, 128, 32)
    assert len(rows) == len(set(rows)) == 128
    assert rows == sorted(rows)
    assert info["eligible_chunks"] == 8
    assert info["excluded_partial_rows"] == 19
    for a, b in info["original_row_ranges"]:
        assert b - a == 32
        assert len(set(low[a:b])) == 1
        assert (a - (1 if low[a] == 32 else 178)) % 32 == 0
    assert any(low[i] == 32 for i in rows)
    assert any(low[i] == 64 for i in rows)


@pytest.mark.parametrize("blocks,group", [(31, 32), (64, 3), (160, 32)])
def test_invalid_or_oversized_pilot_rejected(blocks, group):
    with pytest.raises(ValueError):
        probe.stratified_rows([32] * 128, [2048] * 128, blocks, group)


def test_rotated_pilot_has_balanced_positions():
    k = len(probe.ARMS)
    orders = [probe.arm_order(probe.ARMS, r, 1) for r in range(k)]
    assert all(set(order) == set(probe.ARMS) for order in orders)
    assert all(set(order[position] for order in orders) == set(probe.ARMS)
               for position in range(k))


def test_selection_uses_paired_ratios_and_keeps_baseline_for_small_gain():
    rounds = [dict(float=scale * .99, q15=scale) for scale in (100, 200, 80)]
    assert probe.select_pilot(rounds, "q15", .02)["selected"] == "q15"
    for row in rounds:
        row["float"] *= .8
    assert probe.select_pilot(rounds, "q15", .02)["selected"] == "float"


def test_one_fast_outlier_does_not_choose_new_arm():
    rounds = [dict(float=x, q15=100) for x in (1, 110, 110)]
    assert probe.select_pilot(rounds, "q15", .02)["selected"] == "q15"


@pytest.mark.parametrize("alias", [80, 120])
def test_unchanged_policy_has_no_savings_despite_alias_noise(alias):
    medians = dict(float=90, q15=100, baseline=alias)
    result = probe.compare_full_call(medians, "q15", "q15", 900)
    assert result["baseline_median_ns"] == 100
    assert result["saved_ns_per_call"] == 0
    assert result["selected_over_baseline"] == 1
    assert result["full_calls_to_amortize_probe"] is None
    assert result["one_call_including_probe_over_baseline"] == 10
    assert result["regret"] == pytest.approx(100 / 90 - 1)


def test_changed_policy_savings_use_canonical_baseline():
    medians = dict(float=90, q15=100, baseline=80)
    result = probe.compare_full_call(medians, "q15", "float", 900)
    assert result["saved_ns_per_call"] == 10
    assert result["selected_over_baseline"] == .9
    assert result["full_calls_to_amortize_probe"] == 90


def test_aggregate_unchanged_policy_has_zero_savings():
    rows = []
    for alias in (80, 120):
        medians = dict(float=90, q15=100, baseline=alias)
        rows.append(dict(
            complete=True, nblocks=320, ntemplates=100, full=dict(peaks_per_call=0),
            baseline_threshold_preparation_excluded_ns=200,
            pilots=[dict(blocks=32, probe_elapsed_ns=900, rare_survivor_warning=True,
                         full_comparison=probe.compare_full_call(
                             medians, "q15", "q15", 900))]))
    result = probe.aggregate(rows, [32])["pilots"]["32"]
    assert result["saved_ns_per_pass"] == 0
    assert result["selected_over_baseline"] == 1
    assert result["full_calls_to_amortize_probe"] is None
    assert result["one_pass_including_probes_over_baseline"] == 10
