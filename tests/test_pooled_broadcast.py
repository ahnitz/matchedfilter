"""Pooled CPU batches preserve arbitrary pair lists while reusing packed inputs."""
import ctypes as C
import os

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core


class Peak(C.Structure):
    # The native peak includes magnitude and ABI padding; PEAK_DTYPE does not.
    _fields_ = [("index", C.c_long), ("re", C.c_float), ("im", C.c_float),
                ("magnitude", C.c_float)]


@pytest.fixture(scope="module")
def native():
    lib = C.CDLL(_core.__file__)
    V, I, Z, F = C.c_void_p, C.c_int, C.c_size_t, C.c_float
    signatures = {
        "ap_mf_create_pairbatch": ([Z, I, I], V),
        "ap_mf_destroy": ([V], None),
        "ap_mf_set_template": ([V, I, V], I),
        "ap_mf_set_data": ([V, I, V], I),
        "ap_mf_run": ([V, I, I, I, I, Z, F, V, V, Z, Z], I),
        "ap_mf_run_pairs_pooled": ([V, I, V, V, I, I, Z, F, V, V, Z, Z, I], I),
        "ap_create_pairbatch": ([Z], V),
        "ap_destroy": ([V], None),
        "ap_plan_pairbatch": ([V], I),
        "ap_plan_broadcast_data": ([V], I),
    }
    for name, (args, result) in signatures.items():
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = args, result
    return lib


@pytest.fixture(params=mf.targets())
def target(request):
    mf.backend()                            # apply MF_ISA before the explicit override
    mf.set_target(request.param)
    yield request.param
    mf.set_target(os.environ.get("MF_ISA") or None)


@pytest.mark.parametrize("n", [64, 256, 512])
@pytest.mark.parametrize("pattern", ["same_scattered", "same_packed", "padded_tail",
                                     "mixed_packed", "mixed_scattered", "repeated"])
def test_pooled_inputs_and_scatter(native, target, n, pattern):
    transform = native.ap_create_pairbatch(n)
    if not transform:
        pytest.skip(f"{target} has no pair-batched transform of length {n}")
    try:
        width = native.ap_plan_pairbatch(transform)
        broadcast = native.ap_plan_broadcast_data(transform)
    finally:
        native.ap_destroy(transform)
    assert width > 0
    # Both scalar-data and expanded-data backends must accept the same pair lists.
    if target == "AVX2":
        assert bool(broadcast) == (n >= 256)
    elif target == "SSE4":
        assert not broadcast

    d0, t0, nd, total_nt = 2, 3, 3, 3 * width + 5
    nt = total_nt - t0
    rng = np.random.default_rng(700 + n)
    noise = lambda shape: (rng.normal(size=shape) + 1j*rng.normal(size=shape)).astype(np.complex64)
    data, templates = noise((d0 + nd, n)), noise((total_nt, n))
    data *= np.array([.01j, -2j, .1, 1j, 3], np.complex64)[:, None]
    if pattern == "padded_tail":
        ts = np.arange(3 * width - t0, nt, dtype=np.int32)
    elif pattern.endswith("packed"):
        ts = np.arange(width - t0, 2 * width + 3 - t0, dtype=np.int32)
    elif pattern == "repeated":
        ts = np.resize(np.array([nt - 1, 0, 0, width], np.int32), 2 * width + 3)
    else:
        ts = rng.integers(0, nt, size=2 * width + 3, dtype=np.int32)
    ds = (np.arange(len(ts), dtype=np.int32) % nd if pattern.startswith("mixed")
          else np.full(len(ts), 1, dtype=np.int32))
    selected = set(zip(ds.tolist(), ts.tolist()))
    plan = native.ap_mf_create_pairbatch(n, d0 + nd, total_nt)
    assert plan
    try:
        for d, row in enumerate(data):
            assert native.ap_mf_set_data(plan, d, row.ctypes.data) == 0
        for t, row in enumerate(templates):
            assert native.ap_mf_set_template(plan, t, row.ctypes.data) == 0
        # Odd bins, a nonzero window, a final partial bin, and an actual one-lag tail.
        for lo, hi, binsize in ((3, n - 5, n), (3, n - 5, 7), (n - 1, n, 3)):
            nb = (hi - lo + binsize - 1) // binsize
            for threshold in (0., 3 * np.sqrt(n), 1e9):
                expected = (Peak * (nd * nt * nb))()
                wanted_counts = np.zeros(nd * nt, dtype=np.int32)
                assert native.ap_mf_run(plan, d0, nd, t0, nt, binsize, threshold,
                                       expected, wanted_counts.ctypes.data, lo, hi) >= 0
                actual = (Peak * (nd * nt * nb))()
                for peak in actual:
                    peak.index, peak.re, peak.im, peak.magnitude = -77, 123, 456, 789
                counts = np.full(nd * nt, -99, dtype=np.int32)
                total = native.ap_mf_run_pairs_pooled(
                    plan, d0, ds.ctypes.data, ts.ctypes.data, len(ts), t0,
                    binsize, threshold, actual, counts.ctypes.data, lo, hi, nt)
                # Repeated pairs are counted each time, while their output row is shared.
                assert total == sum(int(wanted_counts[d * nt + t]) for d, t in zip(ds, ts))
                for d in range(nd):
                    for t in range(nt):
                        row = d * nt + t
                        if (d, t) not in selected:
                            assert counts[row] == -99
                            for b in range(nb):
                                peak = actual[row * nb + b]
                                assert (peak.index, peak.re, peak.im, peak.magnitude) == (-77, 123, 456, 789)
                            continue
                        assert counts[row] == wanted_counts[row]
                        for b in range(nb):
                            got, want = actual[row * nb + b], expected[row * nb + b]
                            assert got.index == want.index
                            np.testing.assert_allclose(
                                [got.re, got.im, got.magnitude],
                                [want.re, want.im, want.magnitude], rtol=2e-5, atol=1e-4)
    finally:
        native.ap_mf_destroy(plan)
