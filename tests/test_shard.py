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
