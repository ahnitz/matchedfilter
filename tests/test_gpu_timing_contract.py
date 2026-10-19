"""The device-timer contract every GPU backend shares (Executor.timings, _gputime): with
MF_GPU_TIMING=1 each run of a recorded list is one (its label, device ms) entry; off,
nothing is logged."""
import os
import subprocess
import sys

import numpy as np
import pytest

import matchedfilter as mf


def _gpu_filter():
    try:
        f = mf.MatchedFilter(2048, 1, 1, device="gpu")
    except Exception as e:                      # pragma: no cover - no device
        pytest.skip("no GPU device: %s" % e)
    if getattr(f, "_gpu", None) is None:
        pytest.skip("no GPU device")
    return f


def test_each_run_logs_its_label_and_device_time():
    _gpu_filter()
    code = ("import numpy as np, matchedfilter as mf\n"
            "f = mf.MatchedFilter(2048, 2, 3, device='gpu')\n"
            "f.set_data(np.ones((2, 2048), np.complex64))\n"
            "f.set_templates(np.ones((3, 2048), np.complex64))\n"
            "f.run(); f.run()\n"
            "from matchedfilter import _gputime\n"
            "assert f._gpu in _gputime._CONTEXTS\n"
            "log = f._gpu.timings()\n"
            "runs = [(lab, ms) for lab, ms in log if lab == 'flat']\n"
            "assert len(runs) == 2 and all(ms > 0 for _, ms in log), log\n"
            "assert not any(lab.startswith('k:') for lab, _ in log), log\n"
            "print('ok')\n")
    env = dict(os.environ, MF_GPU_TIMING="1")
    env.pop("MF_GPU_PROFILE", None)
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert r.returncode == 0 and "ok" in r.stdout, r.stdout + r.stderr


def test_nothing_is_logged_with_timers_off():
    if os.environ.get("MF_GPU_TIMING", "") not in ("", "0"):
        pytest.skip("timers on in this process")
    f = _gpu_filter()
    f.set_data(np.ones((1, 2048), np.complex64))
    f.set_templates(np.ones((1, 2048), np.complex64))
    f.run()
    assert f._gpu.timing_log == []
