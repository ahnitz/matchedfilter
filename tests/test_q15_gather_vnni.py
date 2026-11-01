"""Unit tests for arbitrary-pair Q15 gather screening (ap_mf_q15_pairs_lag),
AVX3_DL (VNNI/VBMI) target dispatch, and multi-tier HierarchicalFilter Q15
execution on intermediate and final coarse tiers."""
import ctypes as C
import os

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core
from matchedfilter.time_domain import template_spectra


@pytest.fixture(scope="module")
def core_lib():
    """Bind C entry points for direct Q15 gather screen verification."""
    lib = C.CDLL(_core.__file__)
    void_p, c_int, c_size_t, c_float = C.c_void_p, C.c_int, C.c_size_t, C.c_float
    signatures = (
        ("ap_mf_create_pairbatch", [c_size_t, c_int, c_int], void_p),
        ("ap_mf_create", [c_size_t, c_int, c_int], void_p),
        ("ap_mf_destroy", [void_p], None),
        ("ap_mf_set_data", [void_p, c_int, void_p], c_int),
        ("ap_mf_set_template", [void_p, c_int, void_p], c_int),
        ("ap_mf_q15_lanes", [void_p], c_int),
        ("ap_mf_set_q15_margin", [void_p, c_int], c_int),
        ("ap_mf_q15_screen", [void_p, c_int, c_int, c_int, c_int, c_float,
                             c_size_t, c_size_t, void_p, void_p], c_int),
        ("ap_mf_q15_pairs_lag", [void_p, c_int, void_p, void_p, c_int, c_int,
                                c_float, c_size_t, c_size_t, void_p, void_p,
                                void_p], c_int),
    )
    for name, argtypes, restype in signatures:
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = argtypes, restype
    return lib


@pytest.fixture(params=mf.targets())
def target(request):
    """Iterate across every runtime SIMD target supported on the host."""
    mf.backend()
    mf.set_target(request.param)
    yield request.param
    mf.set_target(None)


def _cpu_has_avx512_vnni():
    """Return True on Linux x86_64 hosts advertising AVX-512 VNNI/VBMI2."""
    if not os.path.isfile("/proc/cpuinfo"):
        return False
    text = open("/proc/cpuinfo", encoding="utf-8", errors="ignore").read()
    needed = ("avx512f", "avx512bw", "avx512dq", "avx512vl",
              "avx512_vnni", "avx512_vbmi", "avx512_vbmi2")
    return all(flag in text for flag in needed)


def test_avx3_dl_enabled_and_selected_when_supported():
    """Verify HWY_AVX3_DL is compiled in and chosen by default on VNNI CPUs."""
    if os.environ.get("MF_ISA"):
        pytest.skip("MF_ISA restricts active target list")
    if not _cpu_has_avx512_vnni():
        pytest.skip("CPU does not advertise AVX-512 DL (VNNI/VBMI2)")
    mf.set_target(None)
    assert "AVX3_DL" in mf.targets()
    assert mf.backend() == "AVX3_DL"
    assert _core.MF(256, 1, 1).q15_lanes() == 32


@pytest.mark.parametrize("transform_len", [64, 128, 256, 512, 1024])
@pytest.mark.parametrize("pairbatch", [True, False])
def test_gather_partial_batches_and_shared_data_blocks(core_lib, target,
                                                       transform_len, pairbatch):
    """Verify arbitrary-pair Q15 gather matches dense Q15 bit-for-bit across
    every partial batch size, unsorted cross-slab pairs, and shared-d runs."""
    ndata, ntmpl = 39, 73
    rng = np.random.default_rng(transform_len * 13 + int(pairbatch))
    create_fn = core_lib.ap_mf_create_pairbatch if pairbatch else core_lib.ap_mf_create
    plan = create_fn(transform_len, ndata, ntmpl)
    assert plan
    try:
        if core_lib.ap_mf_q15_lanes(plan) <= 0:
            pytest.skip("no Q15 screen on this target")
        core_lib.ap_mf_set_q15_margin(plan, 1)
        data = np.ascontiguousarray(
            (rng.standard_normal((ndata, transform_len, 2)) / 6.0).astype(np.float32)
        )
        tmpls = np.ascontiguousarray(
            (rng.standard_normal((ntmpl, transform_len, 2)) / 6.0).astype(np.float32)
        )
        data[3] *= 25.0
        data[27] *= 20.0
        for d_idx in range(ndata):
            assert core_lib.ap_mf_set_data(plan, d_idx, data[d_idx].ctypes.data) == 0
        for t_idx in range(ntmpl):
            assert core_lib.ap_mf_set_template(plan, t_idx, tmpls[t_idx].ctypes.data) == 0

        lo = max(1, transform_len // 10)
        hi = transform_len - lo
        threshold = 2.6
        dense_pass = np.zeros(ndata * ntmpl, dtype=np.uint8)
        dense_stat = np.zeros(ndata * ntmpl, dtype=np.float32)
        core_lib.ap_mf_q15_screen(
            plan, 0, ndata, 0, ntmpl, C.c_float(threshold), lo, hi,
            dense_pass.ctypes.data, dense_stat.ctypes.data
        )

        # Test critical partial-vector counts, full vectors, and multi-batch tails
        for count in (1, 7, 8, 9, 15, 16, 17, 31, 32, 33, 65):
            # Unsorted random pairs spanning arbitrary (d, t) combinations
            flat = rng.choice(ndata * ntmpl, size=count, replace=False)
            dsel = np.ascontiguousarray(flat // ntmpl, dtype=np.int32)
            tsel = np.ascontiguousarray(flat % ntmpl, dtype=np.int32)
            out_pass = np.full(count, 9, dtype=np.uint8)
            out_stat = np.full(count, -9.0, dtype=np.float32)
            out_lag = np.full(count, -9, dtype=np.int16)
            npass = core_lib.ap_mf_q15_pairs_lag(
                plan, 0, dsel.ctypes.data, tsel.ctypes.data, count, 0,
                C.c_float(threshold), lo, hi,
                out_pass.ctypes.data, out_stat.ctypes.data, out_lag.ctypes.data
            )
            assert npass == int(out_pass.sum())
            np.testing.assert_array_equal(out_pass, dense_pass[flat])
            np.testing.assert_array_equal(out_stat, dense_stat[flat])
            assert np.all((out_lag >= lo) & (out_lag < hi))

        # Test consecutive shared-d runs (exercises register dR/dI reuse path)
        shared_d = np.repeat(np.array([0, 3, 27], dtype=np.int32), 13)
        shared_t = np.tile(np.arange(13, dtype=np.int32) * 5, 3)
        flat_shared = shared_d * ntmpl + shared_t
        out_pass = np.zeros(len(shared_d), dtype=np.uint8)
        out_stat = np.zeros(len(shared_d), dtype=np.float32)
        npass = core_lib.ap_mf_q15_pairs_lag(
            plan, 0, shared_d.ctypes.data, shared_t.ctypes.data, len(shared_d), 0,
            C.c_float(threshold), lo, hi,
            out_pass.ctypes.data, out_stat.ctypes.data, None
        )
        assert npass == int(out_pass.sum())
        np.testing.assert_array_equal(out_pass, dense_pass[flat_shared])
        np.testing.assert_array_equal(out_stat, dense_stat[flat_shared])
    finally:
        core_lib.ap_mf_destroy(plan)


@pytest.mark.parametrize("chain", [(256, 512), (256, 512, 1024)])
def test_hierarchical_multitier_q15_sparse_gather_and_direct_refine(monkeypatch,
                                                                    target, chain):
    """Verify multi-tier HierarchicalFilter executes sparse Q15 gather + lag
    election on intermediate (512) and final (512/1024) coarse tiers and
    recovers injected signals accurately."""
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    if _core.MF(256, 1, 1).q15_lanes() == 0:
        pytest.skip("no Q15 screen on this target")

    rng = np.random.default_rng(7700 + len(chain))
    full_n, ntmpl, nblocks, tap_len = 2048, 48, 8, 161
    taps = (rng.standard_normal((ntmpl, tap_len)) / np.sqrt(tap_len)).astype(np.float32)
    taps /= np.linalg.norm(taps, axis=1, keepdims=True)
    counts = np.full(ntmpl, tap_len, dtype=np.int32)
    spec, valid = template_spectra(taps, counts, full_n)
    lo = int(valid[:, 0].max())
    hi = int(valid[:, 1].min())
    step = hi - lo

    series = rng.standard_normal(nblocks * step + full_n).astype(np.float32)
    # Inject signals across 24 templates in block 2 so > ql/2 survivors reach
    # both intermediate (b512) and final (b512/b1024) coarse Q15 gather tiers.
    inj_lag = lo + step // 2
    inj_start = 2 * step + inj_lag - (tap_len // 2)
    for t_inj in range(24):
        amp = 16.0 if t_inj == 11 else 8.0
        series[inj_start:inj_start + tap_len] += amp * taps[t_inj]
    starts = np.arange(nblocks, dtype=np.int64) * step
    los = np.full(nblocks, lo, dtype=np.int64)
    his = np.full(nblocks, hi, dtype=np.int64)

    def _run_hmf(enable_q15):
        hf = mf.HierarchicalFilter(
            full_n, nblocks, ntmpl, snr=5.5, fd=1e-3, chain=chain,
            search_window=(lo, hi)
        )
        hf.set_reference(np.ones(full_n, dtype=np.float32))
        hf.set_templates(np.conj(spec))
        hf.set_taps(taps, counts)
        hf._ensure()
        hf._set_q15(enable_q15)
        res = hf.run_series(series, starts, los, his, binsize=full_n, threshold=5.5)
        return hf, res

    hf_q15, res_q15 = _run_hmf(True)
    _, res_fp32 = _run_hmf(False)

    # Loud injection on (block=2, template=11) must be recovered identically
    assert res_q15["index"][2, 11, 0] == res_fp32["index"][2, 11, 0]
    np.testing.assert_allclose(
        np.abs(res_q15["value"][2, 11, 0]),
        np.abs(res_fp32["value"][2, 11, 0]),
        rtol=1e-4, atol=1e-4
    )
    assert np.abs(res_q15["value"][2, 11, 0]) > 12.0
    # Confirm Q15 screen executed and passed >= 16 survivors into later Q15 tiers
    q_on, q_passed, _ = hf_q15._mf.q15_stats()
    assert q_on and q_passed >= 16
