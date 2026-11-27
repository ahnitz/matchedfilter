"""tools/golden.py's compare: identical records pass, and a one-bit change, a reordering or a
missing array fails, naming the array."""
import importlib.util
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location(
    "golden", Path(__file__).resolve().parents[1] / "tools" / "golden.py")
golden = importlib.util.module_from_spec(spec)
spec.loader.exec_module(golden)


def _record(path, snr, order=("peaks", "series"), drop=None):
    rec = golden.Recorder(digest_above=8)
    rec.case = "case"
    arrays = dict(peaks=snr, series=np.arange(32, dtype=np.float32))
    for label in order:
        if label != drop:
            rec.add(label, arrays[label])
    rec.save(path)
    return path


def _snr():
    return (np.arange(6) * (1 + 0.5j)).astype(np.complex64)


def test_identical_records_compare_equal(tmp_path, capsys):
    a = _record(tmp_path / "a.npz", _snr())
    b = _record(tmp_path / "b.npz", _snr())
    assert golden.main(["compare", str(a), str(b)]) == 0
    assert "2 arrays; 0 differ" in capsys.readouterr().out


def test_one_bit_of_one_value_is_a_difference(tmp_path, capsys):
    changed = _snr()
    changed.view(np.uint32)[7] ^= 1            # the lowest bit of element 3's imaginary part
    a = _record(tmp_path / "a.npz", _snr())
    b = _record(tmp_path / "b.npz", changed)
    assert golden.main(["compare", str(a), str(b)]) == 1
    out = capsys.readouterr().out
    assert "1 differ" in out and "case|peaks" in out and "first at 3" in out


def test_a_digested_array_differs_when_one_bit_does(tmp_path, capsys):
    rec_a, rec_b = golden.Recorder(digest_above=8), golden.Recorder(digest_above=8)
    big = np.arange(64, dtype=np.float32)
    flipped = big.copy()
    flipped.view(np.uint32)[40] ^= 1
    rec_a.add("big", big)
    rec_b.add("big", flipped)
    assert "sha256" in next(iter(rec_a.arrays))
    rec_a.save(tmp_path / "a.npz")
    rec_b.save(tmp_path / "b.npz")
    assert golden.main(["compare", str(tmp_path / "a.npz"), str(tmp_path / "b.npz")]) == 1
    assert "1 differ" in capsys.readouterr().out


def test_order_and_missing_arrays_are_differences(tmp_path, capsys):
    a = _record(tmp_path / "a.npz", _snr())
    swapped = _record(tmp_path / "b.npz", _snr(), order=("series", "peaks"))
    missing = _record(tmp_path / "c.npz", _snr(), drop="series")
    assert golden.main(["compare", str(a), str(swapped)]) == 1
    assert golden.main(["compare", str(a), str(missing)]) == 1
    out = capsys.readouterr().out
    assert "different arrays" in out and "1 only in A" in out


def _record_synthetic(tmp_path, name, seed, device):
    """golden.py record --no-captures on `device` in a fresh process (record sets the cost-file
    and autotune environment for the process it runs in)."""
    import os
    import subprocess
    import sys
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("MF_COST_FILE", None)
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / name
    run = subprocess.run([sys.executable, str(root / "tools" / "golden.py"), "record", str(out),
                          "--costs", str(seed), "--no-captures", "--device", device,
                          "--tree", str(root / "python")],
                         env=env, capture_output=True, text=True, timeout=900)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "device %s" % device in run.stdout
    return out


def test_device_option_defaults_to_the_cpu():
    """A record made without --device is a CPU record, as it was before the option."""
    seen = {}

    def fake_record(args):
        seen["device"] = args.device
        seen["digest_above"] = args.digest_above
        return 0
    real = golden.record
    golden.record = fake_record
    try:
        assert golden.main(["record", "x.npz", "--costs", "seed.json"]) == 0
    finally:
        golden.record = real
    assert seen == {"device": "cpu", "digest_above": golden.DIGEST_ABOVE}


def test_entry_point_banks_are_made_on_the_device_asked_for(monkeypatch):
    """The entry-point cases make their banks on the device the record runs on."""
    import matchedfilter

    class Stop(Exception):
        pass
    devices = []

    def spy(*args, **kwargs):
        devices.append(kwargs.get("device"))
        raise Stop()
    monkeypatch.setattr(matchedfilter, "TimeDomainFilterBank", spy)
    try:
        golden._entry_point_cases(golden.Recorder(), "gpu:7")
    except Stop:
        pass
    assert devices == ["gpu:7"]


def test_a_gpu_record_is_reproducible_from_its_seed(tmp_path, capsys):
    """Two GPU records of the synthetic cases from one seed are identical (the seeding run
    and a fresh process reading a copy of the seed)."""
    import pytest
    from conftest import usable_gpu, usable_gpu_reason
    device = usable_gpu()
    if device is None:
        pytest.skip(usable_gpu_reason())
    seed = tmp_path / "seed.json"
    a = _record_synthetic(tmp_path, "a.npz", seed, device)
    b = _record_synthetic(tmp_path, "b.npz", seed, device)
    assert golden.main(["compare", str(a), str(b)]) == 0
    assert "0 differ" in capsys.readouterr().out
