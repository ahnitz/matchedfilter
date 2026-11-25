"""The middle stage's block-size prices (_layout._corr_block_costs) and what they are keyed on."""
from types import SimpleNamespace

from matchedfilter import _kernel_id, _layout


def _priced_key(monkeypatch, device):
    keys = []

    def price_once(memo, mkey, key, measure, parse):
        keys.append(key)
        return (1.0, 0.0, 0.0)
    monkeypatch.setattr(_layout, "price_once", price_once)
    monkeypatch.setattr(_layout, "_CORR_COSTS", {})
    monkeypatch.setattr(_layout, "_parse_device", lambda d: device)
    _layout._corr_block_costs(32768, "gpu:0")
    return keys[-1]


def test_a_gpu_price_is_keyed_on_the_kernels_it_timed(monkeypatch):
    """A rebuilt series kernel is priced again: its stored price, kept under the old kernels'
    identity, is not reused for the new one."""
    gpu = SimpleNamespace(kind="gpu", backend="vulkan")
    before = _priced_key(monkeypatch, gpu)
    ids = dict(_kernel_id._ids("vulkan"))
    ids["full_series_32768.spv"] = "00" * 32
    monkeypatch.setattr(_kernel_id, "_ids", lambda backend: ids)
    after = _priced_key(monkeypatch, gpu)
    assert before.startswith("corr4,32768,gpu:0|k") and after != before
    ids["tierb_256.spv"] = "11" * 32                 # a kernel the price did not time
    assert _priced_key(monkeypatch, gpu) == after


def test_a_cpu_price_keeps_its_key(monkeypatch):
    assert _priced_key(monkeypatch, SimpleNamespace(kind="cpu", backend=None)) == "corr4,32768"


def _model_prefers(n_best):
    """_corr_block_costs as a model that prices n_best cheapest per sample."""
    return lambda n, device=None: ((1e-6, 1e-6, 1e-10) if n == n_best else (3e-6, 3e-6, 3e-10))


def _layout_of(monkeypatch, kind, counts, prices):
    """TimeDomainFilterBank._corr_bank_layout for a bank of these tap counts on a device of
    `kind`, with the per-size model preferring 32768 and group prices from `prices`
    {n: price} (recording each (n, rows, taps) priced)."""
    from matchedfilter import time_domain
    priced = []

    def group_prices(cands, rows, taps, device):
        priced.extend((n, rows, taps) for n in cands)
        return {n: prices[n] for n in cands}
    monkeypatch.setattr(_layout, "_corr_block_costs", _model_prefers(32768))
    monkeypatch.setattr(_layout, "_corr_group_prices", group_prices)
    monkeypatch.setattr(time_domain._device, "parse", lambda d: SimpleNamespace(kind=kind))
    bank = SimpleNamespace(effective_data_counts=list(counts), max_batch_size=None, device="x")
    groups, _ = time_domain.TimeDomainFilterBank._corr_bank_layout(
        bank, (2048, 4096, 8192, 16384, 32768, 65536))
    return [g[2] for g in groups], priced


def test_a_gpu_bank_runs_each_group_at_its_measured_cheapest_size(monkeypatch):
    """The model's choice (32768) is checked against its neighbours at the group's own rows
    and taps; one measured cheaper by more than _choice.TIE replaces it."""
    sizes, priced = _layout_of(monkeypatch, "gpu", [5720] * 18,
                               {16384: 0.80, 32768: 0.87, 65536: 2.0})
    assert sizes == [16384]
    # priced at the taps rounded up to a sixteenth of the shortest candidate (1024)
    assert sorted(priced) == [(16384, 18, 6144), (32768, 18, 6144), (65536, 18, 6144)]


def test_banks_of_nearby_taps_share_a_price(monkeypatch):
    """Taps within one sixteenth of the shortest candidate are priced as one shape."""
    _, a = _layout_of(monkeypatch, "gpu", [5200] * 18, {16384: 0.8, 32768: 0.9, 65536: 2.0})
    _, b = _layout_of(monkeypatch, "gpu", [6100] * 18, {16384: 0.8, 32768: 0.9, 65536: 2.0})
    assert a == b


def test_a_gpu_bank_keeps_the_model_choice_within_the_tie(monkeypatch):
    sizes, _ = _layout_of(monkeypatch, "gpu", [5720] * 18,
                          {16384: 0.85, 32768: 0.87, 65536: 2.0})
    assert sizes == [32768]


def test_a_neighbour_too_short_for_the_taps_is_not_priced(monkeypatch):
    sizes, priced = _layout_of(monkeypatch, "gpu", [20000] * 4, {32768: 1.0, 65536: 0.5})
    assert sizes == [65536] and {p[0] for p in priced} == {32768, 65536}


def test_a_cpu_bank_is_not_priced_by_group(monkeypatch):
    """The CPU's layout stays the per-size model's."""
    sizes, priced = _layout_of(monkeypatch, "cpu", [5720] * 18, {})
    assert priced == [] and sizes == [32768]


def test_group_prices_are_measured_once_per_shape_and_kernels(monkeypatch):
    """Kept per (device, rows, taps, candidate sizes) under the series kernels' identities."""
    calls, keys = [], []
    monkeypatch.setattr(_layout, "_CORR_GROUP_PRICES", {})
    monkeypatch.setattr(_layout, "_parse_device", lambda d: SimpleNamespace(kind="gpu", backend="vulkan"))
    monkeypatch.setattr(_layout, "_corr_group_measure",
                        lambda cands, *a: calls.append(cands) or {n: 2e-9 for n in cands})

    def price_once(memo, mkey, key, measure, read):
        keys.append(key)
        if mkey not in memo:
            memo[mkey] = measure()[0]
        return memo[mkey]
    monkeypatch.setattr(_layout, "price_once", price_once)
    for _ in range(2):
        assert _layout._corr_group_prices([32768, 16384], 18, 5720, "gpu:0") == {
            16384: 2e-9, 32768: 2e-9}
    _layout._corr_group_prices([16384, 32768], 19, 5720, "gpu:0")
    assert calls == [(16384, 32768), (16384, 32768)]
    kids = ";".join(_layout._corr_kernel_id(n, "vulkan") for n in (16384, 32768))
    assert keys[0] == "choice|corrgroup2,gpu:0,18,5720,16384;32768|k" + kids


def test_measuring_group_prices_leaves_the_device_timers_as_they_were(monkeypatch):
    """The measurement turns each context's timers on for its own calls only: afterwards
    every context it used has the setting it had and none of its records."""
    import pytest
    import matchedfilter
    from conftest import usable_gpu
    device = usable_gpu()
    if device is None:
        pytest.skip("no usable GPU")
    made = []

    class Recorded(matchedfilter.CorrelationFilter):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            made.append((self._gpu, self._gpu._timing))
    monkeypatch.setattr(matchedfilter, "CorrelationFilter", Recorded)
    prices = _layout._corr_group_measure((4096, 8192), 3, 1001, device)
    assert set(prices) == {4096, 8192} and all(p > 0 for p in prices.values())
    assert len(made) == 2
    for ctx, was in made:
        assert ctx._timing == was and len(ctx.timings()) == 0
