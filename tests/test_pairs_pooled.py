"""Multi-ISA verification of fused gather-multiply in ap_mf_run_pairs_pooled / packed."""
import ctypes as C
import os

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core


class Peak(C.Structure):
    _fields_ = [
        ("index", C.c_long),
        ("re", C.c_float),
        ("im", C.c_float),
        ("magnitude", C.c_float),
    ]


@pytest.fixture(scope="module")
def native():
    lib = C.CDLL(_core.__file__)
    V, I, Z, F = C.c_void_p, C.c_int, C.c_size_t, C.c_float
    signatures = {
        "ap_mf_create_pairbatch": ([Z, I, I], V),
        "ap_mf_destroy": ([V], None),
        "ap_mf_set_template": ([V, I, V], I),
        "ap_mf_set_data": ([V, I, V], I),
        "ap_mf_set_bin_phase": ([V, V], None),
        "ap_mf_run": ([V, I, I, I, I, Z, F, V, V, Z, Z], I),
        "ap_mf_run_pairs_pooled": ([V, I, V, V, I, I, Z, F, V, V, Z, Z, I], I),
        "ap_mf_run_pairs_packed": ([V, I, V, V, I, I, Z, F, V, Z, Z], I),
        "ap_lane_width": ([], I),
    }
    for name, (args, res) in signatures.items():
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = args, res
    return lib


@pytest.fixture(params=mf.targets())
def target_isa(request):
    mf.backend()
    mf.set_target(request.param)
    yield request.param
    mf.set_target(os.environ.get("MF_ISA") or None)


def _assert_peaks_match(got, want, count):
    for j in range(count):
        g, w = got[j], want[j]
        assert g.index == w.index
        if w.index >= 0:
            np.testing.assert_allclose(
                [g.re, g.im, g.magnitude],
                [w.re, w.im, w.magnitude],
                rtol=2e-5,
                atol=1e-4,
            )
        else:
            assert (g.re, g.im, g.magnitude) == (0.0, 0.0, 0.0)


@pytest.mark.parametrize("n", [16, 32, 64, 128, 256, 512, 1024])
def test_pairs_pooled_and_packed_lane_counts_and_patterns(native, target_isa, n):
    width = native.ap_lane_width()
    d0, t0 = 1, 2
    nd, nt = 6, 2 * width + 5
    plan = native.ap_mf_create_pairbatch(n, d0 + nd, t0 + nt)
    if not plan:
        assert n < 64
        return
    rng = np.random.default_rng(3000 + n)
    data = (rng.standard_normal((d0 + nd, n)) + 1j * rng.standard_normal((d0 + nd, n))).astype(
        np.complex64
    )
    tmpls = (rng.standard_normal((t0 + nt, n)) + 1j * rng.standard_normal((t0 + nt, n))).astype(
        np.complex64
    )
    try:
        for d in range(d0 + nd):
            assert native.ap_mf_set_data(plan, d, data[d].ctypes.data) == 0
        for t in range(t0 + nt):
            assert native.ap_mf_set_template(plan, t, tmpls[t].ctypes.data) == 0

        lo, hi = 4, n - 4
        for binsize in (hi - lo, 13):
            nb = (hi - lo + binsize - 1) // binsize
            thr = 2.2 * float(np.sqrt(n))
            ref_peaks = (Peak * (nd * nt * nb))()
            ref_counts = np.zeros(nd * nt, dtype=np.int32)
            assert (
                native.ap_mf_run(
                    plan, d0, nd, t0, nt, binsize, thr, ref_peaks, ref_counts.ctypes.data, lo, hi
                )
                >= 0
            )

            # Test every cnt in 1..width plus multi-batch mixed/shared-d/packed-template lists
            pair_lists = []
            for cnt in range(1, width + 1):
                ds = np.array([(l * 3) % nd for l in range(cnt)], dtype=np.int32)
                ts = np.array([(l * 5 + 1) % nt for l in range(cnt)], dtype=np.int32)
                pair_lists.append((ds, ts))
            # Shared data blocks (3 consecutive pairs sharing d) + scattered templates
            ds_clustered = (np.arange(2 * width + 3, dtype=np.int32) // 3) % nd
            ts_scattered = rng.integers(0, nt, size=len(ds_clustered), dtype=np.int32)
            pair_lists.append((ds_clustered, ts_scattered))
            # Same data block, scattered templates
            pair_lists.append((np.full(width + 3, 2, dtype=np.int32), ts_scattered[: width + 3]))
            # Mixed data blocks, aligned packed template group (base % width == 0)
            aligned_t0 = (width - (t0 % width)) % width
            if aligned_t0 + width <= nt:
                pair_lists.append(
                    (
                        np.arange(width, dtype=np.int32) % nd,
                        np.arange(aligned_t0, aligned_t0 + width, dtype=np.int32),
                    )
                )

            for ds, ts in pair_lists:
                npairs = len(ds)
                out_pooled = (Peak * (nd * nt * nb))()
                counts = np.full(nd * nt, -1, dtype=np.int32)
                tot = native.ap_mf_run_pairs_pooled(
                    plan, d0, ds.ctypes.data, ts.ctypes.data, npairs, t0,
                    binsize, thr, out_pooled, counts.ctypes.data, lo, hi, nt,
                )
                assert tot == sum(int(ref_counts[int(d) * nt + int(t)]) for d, t in zip(ds, ts))
                for d, t in set(zip(ds.tolist(), ts.tolist())):
                    row = d * nt + t
                    assert counts[row] == ref_counts[row]
                    _assert_peaks_match(
                        out_pooled[row * nb : (row + 1) * nb],
                        ref_peaks[row * nb : (row + 1) * nb],
                        nb,
                    )

                out_packed = (Peak * (npairs * nb))()
                rc = native.ap_mf_run_pairs_packed(
                    plan, d0, ds.ctypes.data, ts.ctypes.data, npairs, t0,
                    binsize, thr, out_packed, lo, hi,
                )
                assert rc == 1
                for j, (d, t) in enumerate(zip(ds.tolist(), ts.tolist())):
                    row = d * nt + t
                    _assert_peaks_match(
                        out_packed[j * nb : (j + 1) * nb],
                        ref_peaks[row * nb : (row + 1) * nb],
                        nb,
                    )
    finally:
        native.ap_mf_destroy(plan)


@pytest.mark.parametrize("n", [64, 128, 256, 512, 1024])
def test_pairs_pooled_phased_multibin_and_singlebin(native, target_isa, n):
    width = native.ap_lane_width()
    d0, t0 = 1, 1
    nd, nt = 5, 2 * width + 3
    plan = native.ap_mf_create_pairbatch(n, d0 + nd, t0 + nt)
    assert plan
    rng = np.random.default_rng(5000 + n)
    data = (rng.standard_normal((d0 + nd, n)) + 1j * rng.standard_normal((d0 + nd, n))).astype(
        np.complex64
    )
    tmpls = (rng.standard_normal((t0 + nt, n)) + 1j * rng.standard_normal((t0 + nt, n))).astype(
        np.complex64
    )
    try:
        for d in range(d0 + nd):
            assert native.ap_mf_set_data(plan, d, data[d].ctypes.data) == 0
        for t in range(t0 + nt):
            assert native.ap_mf_set_template(plan, t, tmpls[t].ctypes.data) == 0

        lo, hi = 6, n - 6
        for binsize in (hi - lo, 19):
            # Construct valid per-row bin phases sharing the same total bin count nb
            raw_ph = np.array([0, 5, 11, binsize - 1, 3, 7], dtype=np.uint32)[: d0 + nd]
            nbe = (hi - lo + raw_ph + binsize - 1) // binsize
            nb = int(nbe.max())
            bph = (raw_ph + (nb - nbe) * binsize).astype(np.uint32)
            native.ap_mf_set_bin_phase(plan, bph.ctypes.data)

            thr = 2.0 * float(np.sqrt(n))
            ref_peaks = (Peak * (nd * nt * nb))()
            ref_counts = np.zeros(nd * nt, dtype=np.int32)
            for d in range(nd):
                for t in range(nt):
                    row = d * nt + t
                    r = native.ap_mf_run(
                        plan, d0 + d, 1, t0 + t, 1, binsize, thr,
                        C.byref(ref_peaks, row * nb * C.sizeof(Peak)),
                        ref_counts[row : row + 1].ctypes.data,
                        lo, hi,
                    )
                    assert r >= 0

            ds = rng.integers(0, nd, size=2 * width + 3, dtype=np.int32)
            ts = rng.integers(0, nt, size=2 * width + 3, dtype=np.int32)
            out_pooled = (Peak * (nd * nt * nb))()
            counts = np.full(nd * nt, -1, dtype=np.int32)
            tot = native.ap_mf_run_pairs_pooled(
                plan, d0, ds.ctypes.data, ts.ctypes.data, len(ds), t0,
                binsize, thr, out_pooled, counts.ctypes.data, lo, hi, nt,
            )
            assert tot == sum(int(ref_counts[int(d) * nt + int(t)]) for d, t in zip(ds, ts))
            for d, t in set(zip(ds.tolist(), ts.tolist())):
                row = d * nt + t
                assert counts[row] == ref_counts[row]
                _assert_peaks_match(
                    out_pooled[row * nb : (row + 1) * nb],
                    ref_peaks[row * nb : (row + 1) * nb],
                    nb,
                )
            native.ap_mf_set_bin_phase(plan, None)
    finally:
        native.ap_mf_destroy(plan)
