"""Concurrent calibration writers preserve each other's records and valid JSON."""
import json
import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from matchedfilter import gatechain


def _write_cost(path, key, started, done, release=None):
    if release is not None:
        # Pause the writer after it has read the file under the lock (_update_cost's read).
        original = gatechain._read_cost_file

        def paused_read(filename):
            data = original(filename)
            started.set()
            if not release.wait(15):
                raise RuntimeError("writer was not released")
            return data

        gatechain._read_cost_file = paused_read
    else:
        started.set()
    gatechain._store_cost(path, key, {"value": key})
    done.set()


def test_overlapping_process_writers_preserve_both_records(tmp_path):
    path = tmp_path / "costs.json"
    path.write_text('{"existing": {"value": 0}}')
    ctx = multiprocessing.get_context("spawn")
    release = ctx.Event()
    started = [ctx.Event(), ctx.Event()]
    done = [ctx.Event(), ctx.Event()]
    procs = [ctx.Process(target=_write_cost,
                         args=(str(path), key, started[i], done[i], release if i == 0 else None))
             for i, key in enumerate(("first", "second"))]
    try:
        procs[0].start()
        assert started[0].wait(15)  # first writer has read its snapshot
        procs[1].start()
        assert started[1].wait(15)
        # With only atomic replacement the second writer finishes against the old
        # snapshot, then its record is lost when the paused first writer resumes.
        done[1].wait(1)
        release.set()
        for proc in procs:
            proc.join(15)
            assert proc.exitcode == 0
    finally:
        release.set()
        for proc in procs:
            if proc.pid is not None:
                if proc.is_alive():
                    proc.terminate()
                proc.join(5)
    assert json.loads(path.read_text()) == {
        "existing": {"value": 0}, "first": {"value": "first"}, "second": {"value": "second"}}


def test_thread_writers_do_not_share_a_temporary_file(tmp_path):
    path = tmp_path / "costs.json"
    barrier = threading.Barrier(4)

    def write(worker):
        barrier.wait(timeout=10)
        for i in range(8):
            gatechain._store_cost(path, f"{worker}:{i}", worker * 8 + i)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write, range(4)))
    assert json.loads(path.read_text()) == {f"{w}:{i}": w * 8 + i
                                          for w in range(4) for i in range(8)}
    assert not list(tmp_path.glob("*.tmp"))


def test_failed_write_preserves_existing_file_and_releases_lock(tmp_path):
    path = tmp_path / "costs.json"
    gatechain._store_cost(path, "existing", 1)
    with pytest.raises(TypeError):
        gatechain._store_cost(path, "bad", object())
    assert json.loads(path.read_text()) == {"existing": 1}
    assert not list(tmp_path.glob("*.tmp"))
    gatechain._store_cost(path, "next", 2)
    assert json.loads(path.read_text()) == {"existing": 1, "next": 2}
