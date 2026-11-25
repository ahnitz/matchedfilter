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
