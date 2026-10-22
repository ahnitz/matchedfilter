"""The library's own CPU plans run on the CPU whatever MF_DEVICE says (robustness plan, B8).

MF_DEVICE moves a caller's plans built with device=None to another backend. The library
built two of its own CPU plans with device=None -- the CPU plan of a single-template call
on a GPU group, and the correlation price probe -- so MF_DEVICE moved those too (or, for a
device that does not exist, made them fail)."""
import numpy as np

from matchedfilter import TimeDomainFilterBank
from matchedfilter import time_domain as td


def test_a_single_template_cpu_plan_ignores_mf_device(monkeypatch):
    rng = np.random.default_rng(0)
    taps = (rng.standard_normal((4, 101)) / 10).astype(np.float32)
    bank = TimeDomainFilterBank(taps, tap_counts=[101] * 4, engine="flat", device="cpu",
                                fft_lengths=[1024])
    monkeypatch.setenv("MF_DEVICE", "gpu:99")
    plan = bank._groups[0].get_single_plan(0, on_cpu=True)
    assert plan.device.kind == "cpu"


def test_the_correlation_price_probe_ignores_mf_device(monkeypatch):
    monkeypatch.delenv("MF_COST_FILE", raising=False)
    monkeypatch.setattr(td, "_CORR_COSTS", {})
    monkeypatch.setenv("MF_DEVICE", "gpu:99")
    costs = td._corr_block_costs(1024, "cpu")
    assert len(costs) == 3 and all(np.isfinite(costs))
