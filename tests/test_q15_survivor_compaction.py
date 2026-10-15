"""The Q15 survivor list keeps dense output, sparse contracts, and counters intact."""
import ctypes as C
import os

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core


class _Peak(C.Structure):
    _fields_ = [("index", C.c_long), ("re", C.c_float), ("im", C.c_float),
                ("magnitude", C.c_float)]


@pytest.fixture(scope="module")
def native():
    lib = C.CDLL(_core.__file__)
    V, I, Z, F = C.c_void_p, C.c_int, C.c_size_t, C.c_float
    signatures = {
        "ap_hmf_create_chain": ([Z, Z, I, I, V, I, I], V),
        "ap_hmf_destroy": ([V], None),
        "ap_hmf_set_template": ([V, I, V], I),
        "ap_hmf_set_data": ([V, I, V], I),
        "ap_hmf_set_reference": ([V, V], I),
        "ap_hmf_set_thresholds": ([V, V, I], I),
        "ap_hmf_set_q15": ([V, I], I),
        "ap_hmf_set_sparse": ([V, I], I),
        "ap_hmf_run": ([V, I, I, I, I, Z, F, V, V, Z, Z], I),
        "ap_hmf_stats": ([V, V, V], None),
        "ap_hmf_tier_stats": ([V, I, V, V], I),
        "ap_hmf_q15_stats": ([V, V, V], I),
    }
    for name, (args, result) in signatures.items():
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = args, result
    return lib


@pytest.fixture(params=mf.targets())
def target(request, monkeypatch):
    mf.backend()                            # apply MF_ISA before overriding the active target
    mf.set_target(request.param)
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.delenv("MF_HMF_TRACE", raising=False)
    monkeypatch.delenv("MF_HMF_DUMP", raising=False)
    yield request.param
    mf.set_target(os.environ.get("MF_ISA") or None)


def _inputs():
    n, nd, nt = 2048, 5, 43
    rng = np.random.default_rng(933)
    noise = lambda shape: (rng.normal(size=shape) + 1j*rng.normal(size=shape)).astype(np.complex64)
    data, templates = noise((nd, n)), noise((nt, n))
    templates /= np.linalg.norm(templates, axis=1, keepdims=True)
    # A partial screen must include clear rejects, not just near-threshold float rejects.
    templates[::2] *= np.float32(.01)
    return data, templates


def _plan(lib, data, templates, chain, screened):
    n = data.shape[1]
    bands = np.asarray(chain, dtype=np.uintp)
    p = lib.ap_hmf_create_chain(n, n, len(data), len(templates),
                                bands.ctypes.data, len(bands), len(data))
    assert p
    try:
        if lib.ap_hmf_set_q15(p, int(screened)) < 0:
            pytest.skip("this target has no Q15 screen for the first tier")
        reference = np.ones(n, dtype=np.float32)
        assert lib.ap_hmf_set_reference(p, reference.ctypes.data) == 0
        for i, row in enumerate(templates):
            assert lib.ap_hmf_set_template(p, i, row.ctypes.data) == 0
        for i, row in enumerate(data):
            assert lib.ap_hmf_set_data(p, i, row.ctypes.data) == 0
        return p
    except BaseException:
        lib.ap_hmf_destroy(p)
        raise


def _stats(lib, p, ntiers):
    pairs, refined = C.c_long(), C.c_long()
    lib.ap_hmf_stats(p, C.byref(pairs), C.byref(refined))
    passed, ticks = C.c_long(), C.c_ulonglong()
    tiers = []
    for i in range(ntiers):
        assert lib.ap_hmf_tier_stats(p, i, C.byref(passed), C.byref(ticks)) == 0
        tiers.append(passed.value)
    lib.ap_hmf_q15_stats(p, C.byref(passed), C.byref(ticks))
    return np.asarray([pairs.value, refined.value, *tiers, passed.value], dtype=np.int64)


def _fields(peak):
    return peak.index, peak.re, peak.im, peak.magnitude


@pytest.mark.parametrize("chain", [(256,), (256, 512)])
@pytest.mark.parametrize("sparse,with_counts", [(False, True), (False, False),
                                                (True, True), (True, False)])
def test_q15_compaction_preserves_outputs_and_stats(native, target, chain, sparse, with_counts):
    data, templates = _inputs()
    reference = _plan(native, data, templates, chain, False)
    screened = None
    try:
        screened = _plan(native, data, templates, chain, True)
        native.ap_hmf_set_sparse(screened, int(sparse))
        n, d0, nd, t0, nt = data.shape[1], 1, 3, 7, 19
        rows = nd * nt
        for lo, hi, binsize in ((0, n, n), (17, n - 11, 137)):
            nb = (hi - lo + binsize - 1) // binsize
            expected, actual = (_Peak * (rows * nb))(), (_Peak * (rows * nb))()
            wanted_counts = np.zeros(rows, np.int32)
            counts = np.full(rows, -77, np.int32)
            for peak in actual:
                peak.index, peak.re, peak.im, peak.magnitude = 123, 1, 2, 3
            # Reuse the actual buffer: rejected rows contain genuine earlier peaks.
            for state in ("allpass", "partial", "allreject", "partial", "allpass"):
                thresholds = np.asarray(([0.] * len(chain) if state == "allpass" else
                    [1e8] * len(chain) if state == "allreject" else
                    [2.5] + [3.5] * (len(chain) - 1)), dtype=np.float32)
                for plan in (reference, screened):
                    assert native.ap_hmf_set_thresholds(plan, thresholds.ctypes.data, len(chain)) == 0
                previous = [_fields(peak) for peak in actual]
                before = [_stats(native, p, len(chain)) for p in (reference, screened)]
                want_total = native.ap_hmf_run(reference, d0, nd, t0, nt, binsize, 0.,
                                              expected, wanted_counts.ctypes.data, lo, hi)
                total = native.ap_hmf_run(screened, d0, nd, t0, nt, binsize, 0., actual,
                                         counts.ctypes.data if with_counts else None, lo, hi)
                assert total == want_total >= 0
                if with_counts:
                    np.testing.assert_array_equal(counts, wanted_counts)
                for row in range(rows):
                    for b in range(nb):
                        i = row * nb + b
                        if sparse and with_counts and wanted_counts[row] == 0:
                            assert _fields(actual[i]) == previous[i]
                        else:
                            assert actual[i].index == expected[i].index
                            np.testing.assert_allclose(_fields(actual[i])[1:], _fields(expected[i])[1:],
                                                       rtol=2e-5, atol=1e-5)
                            if wanted_counts[row] == 0:
                                assert _fields(actual[i]) == (-1, 0., 0., 0.)
                after = [_stats(native, p, len(chain)) for p in (reference, screened)]
                ref_delta, got_delta = [end - start for end, start in zip(after, before)]
                np.testing.assert_array_equal(got_delta[:-1], ref_delta[:-1])
                assert got_delta[0] == rows           # includes pairs rejected by Q15
                assert got_delta[1] == np.count_nonzero(wanted_counts)
                assert got_delta[2] <= got_delta[-1] <= rows
                if state == "allpass":
                    assert got_delta[-1] == rows and np.all(wanted_counts == nb)
                elif state == "allreject":
                    assert got_delta[-1] == 0 and not wanted_counts.any()
                else:
                    assert 0 < got_delta[-1] < rows
                    assert 0 < np.count_nonzero(wanted_counts) < rows
    finally:
        if screened is not None:
            native.ap_hmf_destroy(screened)
        native.ap_hmf_destroy(reference)


def test_q15_compaction_preserves_trace_and_dump_order(native, target, monkeypatch, tmp_path, capfd):
    data, templates = _inputs()
    traces, dumps = [], []
    for screened in (False, True):
        path = tmp_path / f"gate-{int(screened)}.bin"
        monkeypatch.setenv("MF_HMF_TRACE", "1")
        monkeypatch.setenv("MF_HMF_DUMP", str(path))
        plan = _plan(native, data, templates, (256,), screened)
        try:
            threshold = np.asarray([1.5], np.float32)
            assert native.ap_hmf_set_thresholds(plan, threshold.ctypes.data, 1) == 0
            peaks, counts = (_Peak * 57)(), np.empty(57, np.int32)
            assert native.ap_hmf_run(plan, 1, 3, 7, 19, 2048, 0., peaks,
                                     counts.ctypes.data, 0, 2048) >= 0
        finally:
            native.ap_hmf_destroy(plan)       # close and flush the diagnostic dump
        traces.append(capfd.readouterr().err)
        dumps.append(np.fromfile(path, dtype=np.float32).reshape(-1, 8))
    assert traces[0] and traces[0] == traces[1]
    assert "pair=1 " in traces[0] and "pair=3 " in traces[0] and "pair=5 " in traces[0]
    np.testing.assert_array_equal(dumps[0], dumps[1])
    pairs = [(int(row[6]), int(row[7])) for row in dumps[1]]
    assert pairs and pairs == sorted(pairs)   # local compaction preserves data-major order
    assert all(1 <= d < 4 and 7 <= t < 26 for d, t in pairs)
