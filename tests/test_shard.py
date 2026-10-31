"""conftest's --shard K/N: every module in exactly one shard."""
import pytest

from conftest import shard_modules


def test_shards_partition_the_modules():
    modules = ["test_%02d" % i for i in range(23)] + ["test_03"]     # a repeat counts once
    parts = [shard_modules(modules, k, 4) for k in range(1, 5)]
    assert set().union(*parts) == set(modules)
    assert sum(len(p) for p in parts) == len(set(modules))
    assert max(map(len, parts)) - min(map(len, parts)) <= 1


@pytest.mark.parametrize("k,n", [(0, 4), (5, 4), (1, 0)])
def test_an_impossible_shard_is_refused(k, n):
    with pytest.raises(pytest.UsageError):
        shard_modules(["test_a"], k, n)


def test_shards_balance_by_module_weight():
    """A module heavier than a shard's share takes a shard of its own, and the rest are
    placed heaviest first into the lightest shard: no shard ends heavier than the lightest by
    more than the heaviest module it took after the first (dealt by name, the quarter of the
    suite, then all in test_fdr_calibration, shared a shard and ran out of time, 2026-10-30)."""
    weights = {"test_big": 50.0, "test_mid": 20.0, "test_new": 2.0}
    weights.update({"test_s%02d" % i: 1.0 + 0.1 * i for i in range(20)})
    modules = sorted(weights) + ["test_unweighed"]
    parts = [shard_modules(modules, k, 4, weights) for k in range(1, 5)]
    assert set().union(*parts) == set(modules) and sum(map(len, parts)) == len(modules)
    assert {"test_big"} in parts                      # alone
    median = sorted(weights.values())[len(weights) // 2]
    load = [sum(weights.get(m, median) for m in p) for p in parts]
    others = [l for p, l in zip(parts, load) if "test_big" not in p]
    assert max(others) - min(others) <= 20.0          # within one placement of each other


def test_the_durations_table_names_modules_of_this_suite():
    """tests/durations.json (tools/test_durations.py) weighs modules by the names pytest
    gives them, so its entries are this directory's test modules."""
    import os
    from conftest import module_weights
    here = os.path.dirname(os.path.abspath(__file__))
    weights = module_weights()
    assert weights, "tests/durations.json is missing or empty"
    present = {f[:-3] for f in os.listdir(here) if f.startswith("test_") and f.endswith(".py")}
    assert set(weights) <= present, sorted(set(weights) - present)[:5]
