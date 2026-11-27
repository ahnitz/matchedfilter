"""tools/gpu_alloc_trace.py: the report's breakdown at the peak, the role read from the call
stack, and (on a GPU) a traced filtering call whose workspace slots show as such."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gpu_alloc_trace",
                                              ROOT / "tools" / "gpu_alloc_trace.py")
trace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trace)


@pytest.fixture
def fresh(monkeypatch):
    """The trace's state, emptied for one test."""
    monkeypatch.setattr(trace, "INFO", {})
    monkeypatch.setattr(trace, "LIVE", set())
    monkeypatch.setattr(trace, "STATE", dict(live=0, peak=0, peak_t=0.0, snapshot_at=-1,
                                             snapshot=None))
    monkeypatch.setattr(trace, "SAMPLES", [])
    monkeypatch.setattr(trace, "SNAPSHOT_STEP", 0)
    return trace


def test_the_peak_breakdown_counts_what_was_live_and_never_touched(fresh):
    fresh.note_allocation(1, "spectra slot 0", 1000, 1024)
    fresh.note_allocation(2, "spectra slot 1", 1000, 1024)
    fresh.note_allocation(3, "hier:val", 500, 512)
    fresh.INFO[1][5] = True              # slot 0 bound to a kernel
    fresh.INFO[3][7] = True              # the output written by the host
    fresh.note_free(3)
    fresh.note_allocation(4, "templates", 100, 256)    # below the peak: not in its snapshot
    report = fresh.summary()
    assert report["peak_live_bytes"] == 2560
    peak = report["peak"]
    assert peak["live_bytes"] == 2560
    assert peak["roles"]["spectra slot 0"] == dict(count=1, bytes=1024, untouched=0)
    assert peak["roles"]["spectra slot 1"] == dict(count=1, bytes=1024, untouched=1024)
    assert peak["untouched_bytes"] == 1024 + 0
    assert "templates" not in peak["roles"]
    assert report["roles"]["templates"]["untouched_bytes"] == 256
    assert report["roles"]["hier:val"]["host"] == 1


def test_a_record_buffer_is_named_by_its_record_and_name():
    def _exec_buffer(name):
        return trace.role_of(sys._getframe())

    def _hier_record():
        buf = lambda name: _exec_buffer(name)     # as _gpuhier._hier_record allocates
        return buf("cval1")
    assert _hier_record() == "hier:cval1"


def test_a_traced_gpu_call_shows_its_workspace_slots(tmp_path):
    from conftest import usable_gpu, usable_gpu_reason
    device = usable_gpu()
    if device is None:
        pytest.skip(usable_gpu_reason())
    if not device.startswith("gpu") or "vulkan" not in str(
            [d.backend for d in __import__("matchedfilter").devices() if str(d) == device]):
        pytest.skip("the trace wraps the Vulkan backend")
    script = tmp_path / "call.py"
    script.write_text(
        "import numpy as np\n"
        "from matchedfilter import TimeDomainFilterBank\n"
        "rng = np.random.default_rng(1)\n"
        "taps = rng.standard_normal((8, 200)).astype(np.float32)\n"
        "bank = TimeDomainFilterBank(taps, np.full(8, 200), engine='flat', threshold=4.0,\n"
        "                            device=%r)\n"
        "x = rng.standard_normal(1 << 16).astype(np.float32)\n"
        "TimeDomainFilterBank.filter_series_many([(bank, x, {}), (bank, x[::-1].copy(), {})])\n"
        % device)
    out = tmp_path / "trace.json"
    env = dict(os.environ, PYTHONPATH=str(ROOT / "python"), OMP_NUM_THREADS="1")
    run = subprocess.run([sys.executable, str(ROOT / "tools" / "gpu_alloc_trace.py"), str(out),
                          str(script)], env=env, capture_output=True, text=True, timeout=600)
    assert run.returncode == 0, run.stdout + run.stderr
    report = json.loads(out.read_text())
    assert report["allocations"] > 0
    slots = {k: v for k, v in report["roles"].items() if k.startswith("spectra slot")}
    assert slots, sorted(report["roles"])
    assert slots["spectra slot 0"]["touched"] == slots["spectra slot 0"]["count"]
