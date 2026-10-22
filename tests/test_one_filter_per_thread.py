"""One filter object per thread (docs/robustness-plan.md, B7). The methods release the GIL
while the kernels run; until 2026-10-22 a second thread could call into the same object
meanwhile and corrupt its buffers silently. Now that call raises."""
import threading
import time

import numpy as np
import pytest

from matchedfilter import _core


def _long_run(f, n, nd, nt):
    """Arguments for an MF.run over every pair, and its output buffers."""
    nb = 1
    idx = np.empty(nd * nt * nb, np.int64)
    val = np.empty(nd * nt * nb, np.complex64)
    mag = np.empty(nd * nt * nb, np.float32)
    cnt = np.empty(nd * nt, np.int32)
    return (0, nd, 0, nt, n, 0.0, 0, n, idx, val, mag, cnt)


def test_a_second_thread_gets_an_error_not_a_corrupted_plan():
    n, nd = 1 << 16, 4
    rng = np.random.default_rng(0)
    spec = (rng.standard_normal(2 * n)).astype(np.float32)
    # Size the call to last at least 0.5 s on this host, so the other thread can see it.
    nt = 2
    while True:
        f = _core.MF(n, nd, nt)
        for d in range(nd):
            f.set_data(d, spec)
        for t in range(nt):
            f.set_template(t, spec)
        args = _long_run(f, n, nd, nt)
        t0 = time.perf_counter()
        f.run(*args)
        if time.perf_counter() - t0 >= 0.5 or nt >= 512:
            break
        nt *= 2
    errors, seen = [], []
    worker = threading.Thread(target=lambda: f.run(*args))
    worker.start()
    deadline = time.perf_counter() + 30
    while not f._busy and worker.is_alive() and time.perf_counter() < deadline:
        time.sleep(0.001)
    if f._busy:
        seen.append(True)
        try:
            f.set_data(0, spec)
        except RuntimeError as e:
            errors.append(str(e))
    worker.join(60)
    assert seen, "the worker's call was never observed in flight"
    assert errors and "one filter per thread" in errors[0]
    assert not f._busy
    f.run(*args)                         # usable again once the call has returned


def test_a_failed_guarded_call_leaves_the_object_usable():
    f = _core.MF(1024, 1, 1)
    with pytest.raises((ValueError, TypeError)):
        f.run(0, 5, 0, 1, 1024, 0.0, 0, 1024, b"", b"", b"", b"")
    assert not f._busy
