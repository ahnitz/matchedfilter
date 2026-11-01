"""GPU Tier-0 coarse centroid clustering (`compactPairsClustered`) unit and FDR tests."""
import ctypes
import math

import numpy as np
import pytest
from conftest import kernel_dir, usable_gpu, usable_gpu_reason
from spectral_profiles import binomtest

import matchedfilter as mf
from matchedfilter import _cudacompute, _gpuhier, _hierarchical
from matchedfilter import gatechain as gc
from matchedfilter._gpuexec import fused
from test_coarse_pair_centroids import (
    _make_colored_correlated_bank,
    _make_quad_correlated_bank,
)
from test_gpu_tier0_feed import _ptx_entry_params, _read_ptx, _StubBuf, _stub_cuda_context


def test_cuda_ptx_compactc_abi_and_buffer_sizing(monkeypatch):
    """Verify `compactc` PTX entry ABI and `(nd*nc)` vs `(nd*nt)` buffer sizing across all feeds."""
    ctx, ptx_dir = _stub_cuda_context(monkeypatch)
    n, nd, nt, nc = 2048, 6, 16, 5
    rng = np.random.default_rng(123)
    ct0 = (rng.standard_normal((nc, 256)) + 1j * rng.standard_normal((nc, 256))).astype(
        np.complex64
    )
    ct1 = (rng.standard_normal((nt, 512)) + 1j * rng.standard_normal((nt, 512))).astype(
        np.complex64
    )
    cl_off = np.array([0, 4, 8, 11, 14, 16], dtype=np.uint32)
    cl_mem = np.arange(nt, dtype=np.uint32)
    cl_meta = (nc, cl_off, cl_mem, 1, "test_cl_sig")
    tiers_two = ((256, ct0, 3.8), (512, ct1, 4.6))
    et = _gpuhier.c16_template_exp(ct0)
    ed = _gpuhier.c16_data_exp(256, 3.8, et)
    layout = (32, 4, 2, True)
    bd = _StubBuf(0x9000000, nd * n * 8)
    bt = _StubBuf(0x9100000, nt * n * 8)
    series = _StubBuf(0x9200000, (nd + 2) * n * 8)
    starts = _StubBuf(0x9300000, nd * 4)
    data_arr = np.zeros((nd, n), np.complex64)
    tmpl_arr = np.zeros((nt, n), np.complex64)

    for feed, half in (("inplace", True), ("tier0", True), ("bands", False), ("pack", True)):
        monkeypatch.setattr(ctx, "inplace_feed", feed != "pack")
        claim = None if feed in ("inplace", "pack") else (series, starts, n, nd, (nd + 2) * n, 0)
        rec = ctx._hier_record(
            ("test_cl", feed, half), n, tiers_two, nd, nt, 4,
            layout if half else None, half, feed, "dense", None,
            ed if half else 0, bd, bt, data_arr, tmpl_arr, claim,
            cl_meta=cl_meta,
        )
        # Tier-0 coarse output holds nd * nc pairs while surv0 holds worst-case nd * nt uint32 indices
        assert rec.buffers["cval0"].nbytes == nd * nc * 8
        assert rec.buffers["surv0"].nbytes == nd * nt * 4
        assert rec.buffers["cloff"].nbytes == (nc + 1) * 4
        assert rec.buffers["clmem"].nbytes == nt * 4

        binds = ctx._hier_binds(
            n, tiers_two, nd, nt, 4, 0, n, 512, 9, 6.0, half,
            ed if half else 0, et if half else 0, False,
            layout if half else None, claim, data_arr,
            cl_meta=cl_meta,
        )
        for block, at, fn_name, off in rec.native.args:
            if off < 0:
                _cudacompute._pack_words(-off)(block, at, *binds[fn_name])
            else:
                _cudacompute._PACK_U64(block, at, binds[fn_name].dptr.value + off)

        launched = [op for op in rec.native.ops if op[0] == "launch"]
        stems = [op[1][0] for op in launched]
        assert "compactc" in stems
        assert "compact" not in stems
        for op in launched:
            stem, _, entry = op[1]
            block, ptrs = op[4], op[5]
            ptx_params = _ptx_entry_params(_read_ptx(ptx_dir, stem), entry)
            assert len(ptrs) == len(ptx_params)
            buf_base = ctypes.addressof(block)
            for idx, (ptr_val, (align, size)) in enumerate(zip(ptrs, ptx_params)):
                rel = ptr_val - buf_base
                assert 0 <= rel and rel + size <= ctypes.sizeof(block)
                assert rel % align == 0, f"{stem} param {idx} misaligned"


@pytest.mark.skipif(not usable_gpu(), reason=usable_gpu_reason() or "no usable GPU")
@pytest.mark.parametrize("profile_name", ["inspiral_canonical", "deadzone_bandpass"])
def test_gpu_clustered_tier0_arities_windows_and_feeds(profile_name, monkeypatch):
    """GPU Tier-0 centroids (k in {1, 2, 3, 4}, k0=0 and k0>0, interior & wrap windows) match flat."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    n, nd, nt = 2048, 8, 20
    if profile_name == "deadzone_bandpass":
        power, psd, templates = _make_colored_correlated_bank(
            n, nt, 128, profile_name=profile_name, seed=313
        )
    else:
        power, psd, templates = _make_quad_correlated_bank(n, nt, 128, chain_drift=0.16, seed=314)
        # Turn last template into an uncorrelated singleton so k in {1, 3, 4} all execute together
        rng_s = np.random.default_rng(315)
        raw_last = np.sqrt(power / psd) * np.exp(1j * rng_s.uniform(0.0, 2.0 * np.pi, size=n))
        templates[-1] = (raw_last / math.sqrt(float(np.sum(psd * np.abs(raw_last) ** 2)))).astype(
            np.complex64
        )

    rng = np.random.default_rng(415)
    noise_scale = np.sqrt(psd)
    k = np.arange(n, dtype=np.float64)

    # 1. Frequency-domain run() path (inplace/pack feed), including wrap-around window [8, n-8)
    data = (
        (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))) * noise_scale[None, :]
    ).astype(np.complex64)
    injections = [(0, 3, 420), (2, 11, 1080), (5, 18, 24), (7, 19, 1700)]
    for d_idx, t_idx, lag in injections:
        data[d_idx] += (
            11.5 * psd * templates[t_idx] * np.exp((-2j * np.pi * lag / n) * k)
        ).astype(np.complex64)

    flat = mf.MatchedFilter(n, ndata=nd, ntemplates=nt, device="gpu")
    flat.set_templates(templates)
    flat.set_data(data)
    ref = flat.run(binsize=n // 4, threshold=6.5, window=(8, n - 8))

    hf = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=5.5, fd=1e-3, device="gpu")
    hf.set_reference(power)
    hf.set_templates(templates)
    hf.set_data(data)
    res = hf.run(binsize=n // 4, threshold=6.5, window=(8, n - 8))

    cl_active = hf._active_tier0_cluster()
    assert cl_active is not None
    nc = int(cl_active.specs.shape[0])
    assert nc < nt
    wc = hf.work_counts()
    assert wc["pairs"] == nd * nt
    assert wc["checked"][0] == nd * nc

    for d_idx, t_idx, _ in injections:
        valid = ref[d_idx, t_idx]["index"] >= 0
        assert valid.any()
        np.testing.assert_array_equal(res[d_idx, t_idx]["index"][valid], ref[d_idx, t_idx]["index"][valid])
        np.testing.assert_allclose(
            res[d_idx, t_idx]["value"][valid], ref[d_idx, t_idx]["value"][valid], rtol=1e-4, atol=1e-4
        )

    # Sub-slice template range falls back cleanly to unclustered Tier 0, then resumes clustered
    sub_res = hf.run(binsize=n // 4, threshold=6.5, window=(8, n - 8), templates=(2, 10))
    valid_sub = ref[0, 3]["index"] >= 0
    np.testing.assert_array_equal(sub_res[0, 1]["index"][valid_sub], ref[0, 3]["index"][valid_sub])
    res_again = hf.run(binsize=n // 4, threshold=6.5, window=(8, n - 8))
    assert hf.work_counts()["checked"][0] == 2 * nd * nc + nd * 10
    np.testing.assert_array_equal(res_again[0, 3]["index"][valid_sub], ref[0, 3]["index"][valid_sub])

    # 2. Time-series run_series() path with irregular row_windows, tier0/bands feeds, replay & fused()
    ser_len = 6 * n
    series = hf.empty_shared(ser_len, dtype=np.complex64)
    series[:] = (rng.standard_normal(ser_len) + 1j * rng.standard_normal(ser_len)).astype(np.complex64)
    # Inject a strong time-domain template waveform into block 2 at lag 600
    td_wave = np.fft.ifft(psd * templates[3]).astype(np.complex64) * n
    starts = np.array([0, n // 2, n, 2 * n, 3 * n], dtype=np.int64)
    win_s = np.array([256, 128, 256, 256, 192], dtype=np.int64)
    win_e = np.array([1792, 1664, 1792, 1792, 1728], dtype=np.int64)
    series[starts[2]:starts[2] + n] += 12.0 * np.roll(td_wave, 600)

    flat_ser = mf.MatchedFilter(n, ndata=len(starts), ntemplates=nt, device="gpu", valid=(256, 1792))
    flat_ser.set_templates(templates)
    ref_s = flat_ser.run_series(
        series, starts=starts, win_start=win_s, win_end=win_e, binsize=256, threshold=6.5
    )

    hf_ser = mf.HierarchicalFilter(
        n, ndata=len(starts), ntemplates=nt, snr=5.5, fd=1e-3, device="gpu", valid=(256, 1792)
    )
    hf_ser.set_reference(power)
    hf_ser.set_templates(templates)
    got_s = hf_ser.run_series(
        series, starts=starts, win_start=win_s, win_end=win_e, binsize=256, threshold=6.5
    )
    v_mask = ref_s[2, 3]["index"] >= 0
    assert v_mask.any()
    np.testing.assert_array_equal(got_s[2, 3]["index"][v_mask], ref_s[2, 3]["index"][v_mask])

    # Exercise deferred call-plan recording + hier_replay + fused() submission across two plans
    hf_ser2 = mf.HierarchicalFilter(
        n, ndata=len(starts), ntemplates=nt, snr=5.5, fd=1e-3, device="gpu", valid=(256, 1792)
    )
    hf_ser2.set_reference(power)
    hf_ser2.set_templates(templates)
    for step in range(3):
        token = object()
        close = fused()
        try:
            with hf_ser._series_flags(defer=token, sparse=True), hf_ser2._series_flags(
                defer=token, sparse=True
            ):
                d1 = hf_ser.run_series(
                    series, starts=starts, win_start=win_s, win_end=win_e,
                    binsize=256, threshold=6.5, raw=True,
                )
                d2 = hf_ser2.run_series(
                    series, starts=starts, win_start=win_s, win_end=win_e,
                    binsize=256, threshold=6.5, raw=True,
                )
        finally:
            close()
        r1 = d1.result()
        r2 = d2.result()
        idx1, _ = r1.dense() if hasattr(r1, "dense") else r1
        idx2, _ = r2.dense() if hasattr(r2, "dense") else r2
        np.testing.assert_array_equal(idx1[2, 3][v_mask], ref_s[2, 3]["index"][v_mask])
        np.testing.assert_array_equal(idx2[2, 3][v_mask], ref_s[2, 3]["index"][v_mask])
    assert getattr(hf_ser, "call_plan_replays", 0) >= 1

    # Single-row set_templates invalidates clusters and call plans cleanly
    hf_ser.set_templates(templates[0], index=0)
    assert hf_ser._active_tier0_cluster() is None


@pytest.mark.skipif(not usable_gpu(), reason=usable_gpu_reason() or "no usable GPU")
def test_gpu_compactc_nan_inf_fails_open():
    """NaN or Inf in a Tier-0 centroid coarse value fails open and expands all member templates."""
    n, nd, nt = 1024, 2, 8
    power, _, templates = _make_quad_correlated_bank(n, nt, 128, seed=818)
    hf = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=5.5, fd=0.01, device="gpu")
    hf.set_reference(power)
    hf.set_templates(templates)
    cl = gc.cluster_tier0_templates(templates, power, n, 128, max_arity=4)
    assert cl is not None

    # Corrupt data row 0 with Inf so fp16/fp32 Tier 0 produces NaN/Inf and must fail open
    bad_data = np.zeros((nd, n), dtype=np.complex64)
    bad_data[0, :16] = np.complex64(np.inf)
    ct1 = hf._coarse_templates(templates, (256,), (0.5,))[0]
    idx, _ = hf._gpu.hier_peaks(
        n, 256, bad_data, templates, cl.specs, 5.0,
        binsize=256, threshold=5.0, cascade_band=128, ct1=ct1, raw_thr1=5.0,
        tier0_cluster=cl,
    )
    # Row 0 expanded all nt members through compactPairsClustered without crashing or dropping
    assert idx.shape == (nd, nt, n // 256)
    assert hf._gpu.last_tier1_survivors >= nt


@pytest.mark.skipif(not usable_gpu(), reason=usable_gpu_reason() or "no usable GPU")
def test_gpu_clustered_tier0_empirical_fdr_respects_budget(monkeypatch):
    """GPU Tier-0 centroids (k <= 4) respect the false-dismissal budget on interior and edge lags."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    n, nt = 2048, 16
    snr, fd = 5.5, 0.05
    win = (256, 1792)
    power, psd, templates = _make_quad_correlated_bank(n, nt, 128, chain_drift=0.18, seed=919)

    hf = mf.HierarchicalFilter(
        n, ndata=32, ntemplates=nt, snr=snr, fd=fd, search_window=win, device="gpu"
    )
    hf.set_reference(power)
    hf.set_templates(templates)

    flat = mf.MatchedFilter(n, ndata=32, ntemplates=nt, device="gpu")
    flat.set_templates(templates)

    rng = np.random.default_rng(920)
    noise_scale = np.sqrt(psd)
    k = np.arange(n, dtype=np.float64)
    step_r = n // 128
    w0, w1 = win

    det = 0
    miss = 0
    # Batch 32 independent injections per GPU dispatch for fast, high-power statistical check
    for batch_idx in range(45):
        d_batch = np.empty((32, n), dtype=np.complex64)
        lags = np.empty(32, dtype=np.float64)
        t_ids = np.empty(32, dtype=np.int64)
        for row in range(32):
            trial = batch_idx * 32 + row
            t_idx = int(trial % nt)
            t_ids[row] = t_idx
            if trial % 4 == 0:
                lag = float(rng.uniform(w0 + 2, w0 + 2 * step_r))
            elif trial % 4 == 1:
                lag = float(rng.uniform(w1 - 2 * step_r, w1 - 2))
            else:
                lag = float(rng.uniform(w0 + 32, w1 - 32))
            lags[row] = lag
            sig = snr * psd * templates[t_idx] * np.exp((-2j * np.pi * lag / n) * k)
            noise = (rng.standard_normal(n) + 1j * rng.standard_normal(n)) * noise_scale
            d_batch[row] = (sig + noise).astype(np.complex64)

        flat.set_data(d_batch)
        ref = flat.run(binsize=w1 - w0, threshold=snr, window=win)
        hf.set_data(d_batch)
        got = hf.run(binsize=w1 - w0, threshold=snr, window=win)

        for row in range(32):
            t_idx = int(t_ids[row])
            r_pk = ref[row, t_idx, 0]
            at = int(r_pk["index"])
            mag = abs(complex(r_pk["value"]))
            if at < 0 or mag < snr or abs(at - lags[row]) > 32:
                continue
            det += 1
            g_pk = got[row, t_idx, 0]
            if int(g_pk["index"]) < 0 or abs(complex(g_pk["value"])) < snr:
                miss += 1

    cl = hf._active_tier0_cluster()
    assert cl is not None and int(cl.specs.shape[0]) == nt // 4
    assert det >= 500
    pval = binomtest(miss, det, p=fd, alternative="greater").pvalue
    assert pval >= 1e-3, (
        f"GPU k=4 empirical FDR {miss}/{det} = {miss / det:.4f} > {fd} (p={pval:.2e})"
    )
