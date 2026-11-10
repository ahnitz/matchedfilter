"""Tests for L1D-tiled multi-block Q15 screening, same-block Tier-1 gather register reuse,
CPU-cache-queried L2 sizing and n = 1024 hierarchical block eligibility, and multi-arity
(k <= 16) Tier-0 coarse centroids."""
import ctypes
import math

import numpy as np
import pytest
from scipy.stats import binomtest

import matchedfilter as mf
from matchedfilter import _calibration, _core, gatechain
from matchedfilter.time_domain import TimeDomainFilterBank


@pytest.fixture(params=mf.targets())
def target(request):
    """Select each compiled SIMD target in turn and restore default afterward."""
    mf.backend()
    mf.set_target(request.param)
    yield request.param
    mf.set_target(None)


def _make_family_bank(n, nt, band, group_size=16, sep=2800.0, drift_amp=0.14, seed=9090):
    """Construct a colored-PSD bank with ``group_size``-template correlated families."""
    rng = np.random.default_rng(seed)
    k = np.arange(n, dtype=np.float64)
    freqs = np.linspace(0.0, 1.0, n, endpoint=False)
    psd = 0.2 + 12.0 * (1.0 - np.sin(np.pi * np.minimum(freqs, 0.5))) ** 2 + 4.0 * freqs ** 2
    raw_h2 = np.where((k >= 20) & (k < n // 2), np.maximum(k, 1.0) ** (-7.0 / 3), 0.0)
    power = (raw_h2 / psd).astype(np.float32)
    power /= float(power.sum())
    base_amp = np.sqrt(power / psd)
    step_r = n // band

    templates = np.empty((nt, n), dtype=np.complex64)
    n_groups = nt // group_size
    for g_idx in range(n_groups):
        base_phase = rng.uniform(0.0, 2.0 * np.pi) + sep * g_idx * (k / max(band, 1)) ** 2
        base_spec = base_amp * np.exp(1j * base_phase)
        for m_idx in range(group_size):
            centered = (m_idx - 0.5 * (group_size - 1)) / max(0.5 * (group_size - 1), 1.0)
            dl = int(round(centered * max(1, (step_r * 3) // 4)))
            dl = max(-step_r, min(step_r, dl))
            phi0 = rng.uniform(-np.pi, np.pi)
            drift = drift_amp * centered * np.sin(2.0 * np.pi * k / max(band, 1))
            tilt = 1.0 + 0.04 * centered * ((k / (n / 2.0)) - 0.5)
            spec = base_spec * tilt * np.exp(1j * (phi0 + drift) + (2j * np.pi * dl / n) * k)
            norm = math.sqrt(float(np.sum(psd * (spec.real ** 2 + spec.imag ** 2))))
            templates[g_idx * group_size + m_idx] = (spec / norm).astype(np.complex64)
    for t_idx in range(n_groups * group_size, nt):
        phases = rng.uniform(0.0, 2.0 * np.pi, size=n)
        spec = base_amp * np.exp(1j * phases)
        norm = math.sqrt(float(np.sum(psd * (spec.real ** 2 + spec.imag ** 2))))
        templates[t_idx] = (spec / norm).astype(np.complex64)
    return power, psd, templates


def test_l2_bytes_and_layout_batch_target_cache_scaling(monkeypatch):
    """Verify _core.l2_bytes() is exposed and _layout._batch_target scales cleanly from L2."""
    from matchedfilter import _layout
    l2 = int(_core.l2_bytes())
    assert l2 >= 0
    monkeypatch.delenv("MF_DGROUP", raising=False)
    def_g1024 = gatechain.default_series_group(1024)
    assert _core.series_group(1024, def_g1024) == (64 if l2 >= 1024 * 1024 else 32)
    bt_2048 = _layout._batch_target(2048, None)
    bt_1024 = _layout._batch_target(1024, None)
    assert bt_2048 == 512
    if l2 >= 1024 * 1024:
        assert bt_1024 == 1024
    else:
        assert bt_1024 == 512


@pytest.mark.parametrize("band", [64, 128, 256, 512, 1024])
def test_q15_screen_blocks_bit_exact_against_stat_path(target, band):
    """Verify L1D-tiled q15_screen_blocks (stat=NULL) matches the single-block stat!=NULL path
    bit-for-bit across all SIMD targets, windows, margins, block counts, and lane slices."""
    lib = ctypes.CDLL(_core.__file__)
    lib.ap_mf_create.argtypes = [ctypes.c_size_t, ctypes.c_int, ctypes.c_int]
    lib.ap_mf_create.restype = ctypes.c_void_p
    lib.ap_mf_destroy.argtypes = [ctypes.c_void_p]
    lib.ap_mf_destroy.restype = None
    lib.ap_mf_q15_lanes.argtypes = [ctypes.c_void_p]
    lib.ap_mf_q15_lanes.restype = ctypes.c_int
    lib.ap_mf_set_data.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_float)]
    lib.ap_mf_set_data.restype = ctypes.c_int
    lib.ap_mf_set_template.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_float)]
    lib.ap_mf_set_template.restype = ctypes.c_int
    lib.ap_mf_set_q15_margin.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.ap_mf_set_q15_margin.restype = ctypes.c_int
    lib.ap_mf_q15_screen.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.POINTER(ctypes.c_float),
    ]
    lib.ap_mf_q15_screen.restype = ctypes.c_int

    nd, nt = 19, 70
    plan = lib.ap_mf_create(band, nd, nt)
    assert plan
    try:
        qw = lib.ap_mf_q15_lanes(plan)
        if qw <= 0:
            pytest.skip(f"no Q15 screen for target {target} at band {band}")
        rng = np.random.default_rng(4200 + band)
        data = (rng.standard_normal((nd, band)) + 1j * rng.standard_normal((nd, band))).astype(np.complex64)
        data[0] = 0.0
        tmpls = (rng.standard_normal((nt, band)) + 1j * rng.standard_normal((nt, band))).astype(np.complex64)
        tmpls /= np.maximum(np.linalg.norm(tmpls, axis=1, keepdims=True), 1e-12)
        tmpls[3] = 0.0
        for d in range(nd):
            assert lib.ap_mf_set_data(plan, d, data[d].view(np.float32).ctypes.data_as(ctypes.POINTER(ctypes.c_float))) == 0
        for t in range(nt):
            assert lib.ap_mf_set_template(plan, t, tmpls[t].view(np.float32).ctypes.data_as(ctypes.POINTER(ctypes.c_float))) == 0

        windows = [(0, band), (band // 8, band - band // 8), (band // 4, band // 4 + 5)]
        slices = [(0, nd, 0, nt), (1, 7, 0, qw), (2, 11, 3, min(nt - 3, qw + 9)), (0, 5, qw - 2, 5)]
        for margin_on in (1, 0):
            lib.ap_mf_set_q15_margin(plan, margin_on)
            for ws, we in windows:
                for d0, sub_nd, t0, sub_nt in slices:
                    if t0 + sub_nt > nt or sub_nt < 1:
                        continue
                    pass_fast = np.full(sub_nd * sub_nt, 9, dtype=np.uint8)
                    pass_ref = np.full(sub_nd * sub_nt, 7, dtype=np.uint8)
                    stat_ref = np.zeros(sub_nd * sub_nt, dtype=np.float32)
                    c_fast = lib.ap_mf_q15_screen(
                        plan, d0, sub_nd, t0, sub_nt, 3.1, ws, we,
                        pass_fast.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)), None,
                    )
                    c_ref = lib.ap_mf_q15_screen(
                        plan, d0, sub_nd, t0, sub_nt, 3.1, ws, we,
                        pass_ref.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)),
                        stat_ref.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                    )
                    assert c_fast == c_ref
                    np.testing.assert_array_equal(pass_fast, pass_ref)
    finally:
        lib.ap_mf_destroy(plan)


@pytest.mark.parametrize("band", [256, 512, 1024])
def test_q15_pairs_batch_same_block_centroid_runs_exact(target, band):
    """Verify 4-way and 2-way same-block register reuse in q15_screen_gather_row_fused_n matches
    single-pair evaluation bit-for-bit across runs of 1..9 survivors per data block."""
    lib = ctypes.CDLL(_core.__file__)
    lib.ap_mf_create.argtypes = [ctypes.c_size_t, ctypes.c_int, ctypes.c_int]
    lib.ap_mf_create.restype = ctypes.c_void_p
    lib.ap_mf_destroy.argtypes = [ctypes.c_void_p]
    lib.ap_mf_destroy.restype = None
    lib.ap_mf_q15_lanes.argtypes = [ctypes.c_void_p]
    lib.ap_mf_q15_lanes.restype = ctypes.c_int
    lib.ap_mf_set_data.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_float)]
    lib.ap_mf_set_data.restype = ctypes.c_int
    lib.ap_mf_set_template.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_float)]
    lib.ap_mf_set_template.restype = ctypes.c_int
    lib.ap_mf_q15_pairs_lag.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_int16),
    ]
    lib.ap_mf_q15_pairs_lag.restype = ctypes.c_int

    nd, nt = 8, 40
    plan = lib.ap_mf_create(band, nd, nt)
    assert plan
    try:
        if lib.ap_mf_q15_lanes(plan) <= 0:
            pytest.skip(f"no Q15 screen for target {target}")
        rng = np.random.default_rng(7100 + band)
        data = (rng.standard_normal((nd, band)) + 1j * rng.standard_normal((nd, band))).astype(np.complex64)
        tmpls = (rng.standard_normal((nt, band)) + 1j * rng.standard_normal((nt, band))).astype(np.complex64)
        tmpls /= np.linalg.norm(tmpls, axis=1, keepdims=True)
        for d in range(nd):
            lib.ap_mf_set_data(plan, d, data[d].view(np.float32).ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
        for t in range(nt):
            lib.ap_mf_set_template(plan, t, tmpls[t].view(np.float32).ctypes.data_as(ctypes.POINTER(ctypes.c_float)))

        # Construct runs of 1, 2, 3, 4, 5, 8, 9 consecutive pairs sharing the same d
        run_lengths = [4, 2, 1, 5, 8, 3, 9, 6]
        ds_list, ts_list = [], []
        for d_idx, rlen in enumerate(run_lengths):
            t_picks = rng.choice(nt, size=rlen, replace=False)
            for tp in t_picks:
                ds_list.append(d_idx)
                ts_list.append(int(tp))
        ds = np.asarray(ds_list, dtype=np.int32)
        ts = np.asarray(ts_list, dtype=np.int32)
        npairs = int(ds.size)

        pass_bat = np.full(npairs, 9, dtype=np.uint8)
        lag_bat = np.full(npairs, -9, dtype=np.int16)
        c_bat = lib.ap_mf_q15_pairs_lag(
            plan, 0, ds.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
            ts.ctypes.data_as(ctypes.POINTER(ctypes.c_int)), npairs, 0,
            2.9, band // 8, band - band // 8,
            pass_bat.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)), None,
            lag_bat.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
        )
        pass_one = np.empty(npairs, dtype=np.uint8)
        lag_one = np.empty(npairs, dtype=np.int16)
        for j in range(npairs):
            d1 = np.array([ds[j]], dtype=np.int32)
            t1 = np.array([ts[j]], dtype=np.int32)
            p1 = np.zeros(1, dtype=np.uint8)
            l1 = np.zeros(1, dtype=np.int16)
            lib.ap_mf_q15_pairs_lag(
                plan, 0, d1.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                t1.ctypes.data_as(ctypes.POINTER(ctypes.c_int)), 1, 0,
                2.9, band // 8, band - band // 8,
                p1.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)), None,
                l1.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
            )
            pass_one[j] = p1[0]
            lag_one[j] = l1[0]
        assert c_bat == int(pass_one.sum())
        np.testing.assert_array_equal(pass_bat, pass_one)
        np.testing.assert_array_equal(lag_bat, lag_one)
    finally:
        lib.ap_mf_destroy(plan)


def test_multi_arity_k16_centroids_partition_variance_and_fdr(monkeypatch):
    """Verify k <= 16 multi-pass centroids produce valid CSR partitions, unit colored-PSD
    variance, lazy pass pruning, and empirical FDR within budget."""
    monkeypatch.setenv("MF_GATE16", "0")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    n, nt, b0 = 2048, 128, 128
    snr, fd = 5.5, 0.05
    win = (256, 1792)
    power, psd, templates = _make_family_bank(n, nt, b0, group_size=16, drift_amp=0.14, seed=9191)

    cands = gatechain.cluster_tier0_candidates(templates, power, n, b0, max_arity=16)
    assert len(cands) == 4
    cl_k2, cl_k4, cl_k8, cl_k16 = cands
    assert cl_k2 is not None and cl_k4 is not None and cl_k8 is not None and cl_k16 is not None
    assert cl_k16.specs.shape[0] < cl_k8.specs.shape[0] < cl_k4.specs.shape[0] < cl_k2.specs.shape[0]
    sizes = np.diff(cl_k16.offsets)
    assert int(cl_k16.offsets[0]) == 0 and int(cl_k16.offsets[-1]) == nt
    assert sorted(int(m) for m in cl_k16.members) == list(range(nt))
    assert int(sizes.max()) > 4 and int(sizes.max()) <= 16

    # Colored-PSD coarse noise variance == 1.0 across all k <= 16 centroids
    rng = np.random.default_rng(9192)
    d_band = (
        (rng.standard_normal((800, b0)) + 1j * rng.standard_normal((800, b0)))
        * np.sqrt(psd)[None, :b0]
    )
    vars_all = []
    for ci in range(cl_k16.specs.shape[0]):
        corr = b0 * np.fft.ifft(d_band * np.conj(cl_k16.specs[ci].astype(np.complex128))[None, :], axis=1)
        vars_all.extend([float(np.var(corr.real)), float(np.var(corr.imag))])
    assert float(np.mean(vars_all)) == pytest.approx(1.0, abs=0.04)

    # HierarchicalFilter selects high-arity (>4) centroids and respects empirical FDR budget
    hf = mf.HierarchicalFilter(n, ndata=1, ntemplates=nt, snr=snr, fd=fd, search_window=win)
    hf.set_reference(power)
    hf.set_templates(templates)
    hf._execution_plan()
    assert hf._mf.tier0_cluster_count() < nt // 4

    flat = _core.MF(n, 1, nt)
    flat.set_template_batch(0, templates)
    noise_scale = np.sqrt(psd)
    k = np.arange(n, dtype=np.float64)
    w0, w1 = win
    idx_f = np.empty(1, dtype=np.int64)
    val_f = np.empty(1, dtype=np.complex64)
    mag_f = np.empty(1, dtype=np.float32)
    cnt_f = np.empty(1, dtype=np.int32)
    det = 0
    miss = 0
    for trial in range(1000):
        t_idx = int(trial % nt)
        lag = float(rng.uniform(w0 + 8, w1 - 8))
        sig = snr * psd * templates[t_idx] * np.exp((-2j * np.pi * lag / n) * k)
        noise = (rng.standard_normal(n) + 1j * rng.standard_normal(n)) * noise_scale
        d = (sig + noise).astype(np.complex64)
        flat.set_data(0, d)
        flat.run(0, 1, t_idx, 1, w1 - w0, snr, w0, w1, idx_f, val_f, mag_f, cnt_f)
        at = int(idx_f[0])
        if at < 0 or float(mag_f[0]) < snr or abs(at - lag) > 32:
            continue
        det += 1
        hf.set_data(d[None, :])
        pk = hf.run(binsize=w1 - w0, threshold=snr, window=win)[0, t_idx, 0]
        if int(pk["index"]) < 0 or abs(complex(pk["value"])) < snr:
            miss += 1
    assert det >= 350
    pval = binomtest(miss, det, p=fd, alternative="greater").pvalue
    assert pval >= 1e-3, f"k<=16 empirical FDR {miss}/{det} = {miss / det:.4f} > {fd} (p={pval:.2e})"


def test_hier_bank_n1024_candidate_and_half_valid_single_sizes(monkeypatch):
    """Verify hierarchical TimeDomainFilterBank with binsize includes 1024 when _small_blocks_fit
    holds, while _single_sizes skips <50%-valid block sizes when >=50%-valid sizes exist."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    rng = np.random.default_rng(3131)
    short_taps = rng.standard_normal((32, 200)).astype(np.float32)
    short_counts = np.full(32, 200, dtype=np.int64)
    bank_short = TimeDomainFilterBank(
        short_taps, short_counts, tap_sample_rate=2048, data_sample_rate=2048,
        engine="hier", binsize=512, threshold=6.0, false_dismissal=1e-3,
    )
    l1d = int(_core.l1d_bytes())
    if l1d and 3 * 8 * 2048 >= l1d:
        assert 1024 in bank_short._choice_ns
        assert bank_short._single_sizes()[0] == 1024

    long_taps = rng.standard_normal((32, 800)).astype(np.float32)
    long_counts = np.full(32, 800, dtype=np.int64)
    bank_long = TimeDomainFilterBank(
        long_taps, long_counts, tap_sample_rate=2048, data_sample_rate=2048,
        engine="hier", binsize=512, threshold=6.0, false_dismissal=1e-3,
    )
    assert bank_long._single_sizes()[0] == 2048


def test_batch_target_large_l2_does_not_inflate_long_transforms(monkeypatch):
    """Verify _batch_target stays bounded across all transform sizes even if L2 is 16 MiB."""
    from matchedfilter import _layout
    monkeypatch.setattr(_core, "l2_bytes", lambda: 16 * 1024 * 1024)
    assert _layout._batch_target(1024, None) == 1024
    assert _layout._batch_target(2048, None) == 512
    assert _layout._batch_target(4096, None) == 256
    assert _layout._batch_target(16384, None) == 64
    assert _layout._batch_target(32768, None) == 32
    assert _layout._batch_target(65536, None) == 32

    monkeypatch.setattr(_core, "l2_bytes", lambda: 256 * 1024)
    assert _layout._batch_target(1024, None) == 512
    assert _layout._batch_target(2048, None) == 512
    assert _layout._batch_target(16384, None) == 64


def test_pareto_frontier_retains_all_undominated_arities_and_forced_chain_fallback(monkeypatch):
    """Verify _pareto_tier0_candidates keeps every undominated arity and _tier0_cluster_for_band
    falls back cleanly to unclustered None when forced_chain cannot gate with centroids."""
    from matchedfilter import _hierarchical

    def mk(ratio, alpha, lag_pad=1):
        return gatechain.Tier0Cluster(
            specs=np.zeros((4, 64), np.complex64),
            offsets=np.array([0, 2, 4, 6, 8], np.int32),
            members=np.arange(8, dtype=np.int32),
            lag_pad=lag_pad,
            ratio=ratio,
            alpha=alpha,
            member_alphas=np.full(8, alpha, np.float32),
        )

    cands_4 = (mk(0.55, 0.98), mk(0.40, 0.96), mk(0.30, 0.94), mk(0.20, 0.90))
    kept = _hierarchical._pareto_tier0_candidates(cands_4)
    assert len(kept) == 4

    # Dominated intermediate candidate (higher ratio, lower alpha) is pruned cleanly
    cands_dom = (mk(0.55, 0.96), mk(0.40, 0.98), mk(0.25, 0.98))
    kept_dom = _hierarchical._pareto_tier0_candidates(cands_dom)
    assert len(kept_dom) == 1 and kept_dom[0].ratio == 0.25

    # Forced-chain fallback when clustered candidates fail to gate (chain_thresholds -> None)
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    n, nt = 2048, 32
    power, _, templates = _make_family_bank(n, nt, 128, group_size=8, drift_amp=0.10, seed=9494)
    orig_ct = gatechain.chain_thresholds

    def fake_ct(p, n_, s, f, ch, *args, **kwargs):
        if kwargs.get("tier0_cluster") is not None:
            return None
        return orig_ct(p, n_, s, f, ch, *args, **kwargs)

    monkeypatch.setattr(gatechain, "chain_thresholds", fake_ct)
    hf = mf.HierarchicalFilter(n, ndata=1, ntemplates=nt, snr=5.5, fd=0.01)
    hf.set_reference(power)
    hf.set_templates(templates)
    hf._execution_plan()
    assert hf._active_tier0_cluster() is None
    assert hf._mf.tier0_cluster_count() == 0
