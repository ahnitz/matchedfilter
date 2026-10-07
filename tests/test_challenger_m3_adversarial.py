"""Adversarial stress-test harness for Milestone 3 Gate (HierarchicalFilter Precision Challenger).

Empirically challenges:
1. Edge frequency bins (DC bin, Nyquist bin, transition bins in Hermitian and DIF modes).
2. Noise floor invariant: std(Re(rho)) = 1.00 +/- 0.02 under unit Gaussian noise.
3. Strict threshold contract: zero false alarms from noise crossing rho >= 6.0.
4. Numerical precision across SNR ladder (SNR 6.0 to 100.0) against MatchedFilter and direct DFT oracle.
5. Timing invariance (zero sub-sample drift) and phase linearity.
6. Boundary conditions (window edges, binsize sweeps, calling order semantics).
"""
import os
import math
import numpy as np
import pytest
import matchedfilter as mf


BANK_PATH = "/home/ahnitz/projects/claude/searchdev/work/scale100k/fir_three_level_opt501_v2.hdf"


def load_real_bank_templates(n_max=32):
    """Load realistic template FIR taps from the production template bank."""
    if not os.path.exists(BANK_PATH):
        pytest.skip(f"Template bank not found: {BANK_PATH}")
    h5py = pytest.importorskip("h5py")
    with h5py.File(BANK_PATH, "r") as f:
        taps = f["fir_data/0/taps"][:n_max]
        counts = f["fir_data/0/actual_tap_count"][:n_max]
    return taps, counts


class TestEdgeFrequencyBins:
    """Stress-test edge frequency bins: DC (k=0), Nyquist (k=K), and band transitions."""

    @pytest.mark.parametrize("edge_bin", [0, 1, 127, 128, 255, 256, 512, 1023, 1024])
    def test_edge_bin_hermitian_exact_parity(self, edge_bin):
        """Verify that Hermitian HierarchicalFilter matches MatchedFilter on single-frequency and edge tones."""
        N = 2048
        K = N // 2
        rng = np.random.default_rng(1000 + edge_bin)

        t_full = np.zeros((1, N), dtype=np.complex64)
        # Generate positive frequencies
        spec = (rng.standard_normal(K) + 1j * rng.standard_normal(K)).astype(np.complex64)
        t_full[0, 1:K] = spec[1:]
        t_full[0, 0] = rng.standard_normal()
        t_full[0, K] = rng.standard_normal()

        # Enforce exact Hermitian conjugate symmetry for real FIR filter
        for k in range(1, K):
            t_full[0, N - k] = np.conj(t_full[0, k])

        # Add pure tone at edge bin
        if edge_bin == 0:
            t_full[0, 0] += 5.0
        elif edge_bin == K:
            t_full[0, K] += 5.0
        else:
            t_full[0, edge_bin] += 5.0 + 2.0j
            t_full[0, N - edge_bin] = np.conj(t_full[0, edge_bin])

        # Packed half template
        t_half = np.ascontiguousarray(t_full[:, :K].copy())
        t_half[0, 0] = t_full[0, 0].real + 1j * t_full[0, K].real

        # Data with noisy signal containing the template
        d_time = (rng.standard_normal(N) + 1j * rng.standard_normal(N)).astype(np.complex64) * 0.1
        d_full = (np.fft.fft(d_time) / N).astype(np.complex64).reshape(1, N)
        d_full += t_full * 10.0 / N

        # 1. Baseline MatchedFilter
        mf_plan = mf.MatchedFilter(N, ndata=1, ntemplates=1)
        mf_plan.set_templates(t_full)
        mf_plan.set_data(d_full)
        res_mf = mf_plan.run(threshold=0.0)

        # 2. HierarchicalFilter (Hermitian mode)
        hf_plan = mf.HierarchicalFilter(N, ndata=1, ntemplates=1, band=256, taps=8, cascade=False)
        hf_plan.set_hermitian(True)
        hf_plan.set_coarse_threshold(0.0)
        hf_plan.set_templates(t_half)
        hf_plan.set_data(d_full)
        res_hf = hf_plan.run(threshold=0.0)

        # Direct NumPy IFFT oracle
        prod = d_full[0] * np.conj(t_full[0])
        direct_snr = np.fft.ifft(prod) * N
        direct_idx = np.argmax(np.abs(direct_snr))
        direct_val = direct_snr[direct_idx]

        idx_mf = res_mf['index'][0, 0, 0]
        val_mf = res_mf['value'][0, 0, 0]
        idx_hf = res_hf['index'][0, 0, 0]
        val_hf = res_hf['value'][0, 0, 0]

        assert idx_mf == direct_idx, f"MF index {idx_mf} != direct {direct_idx}"
        assert idx_hf == idx_mf, f"Edge bin {edge_bin}: HF index {idx_hf} != MF index {idx_mf}"
        np.testing.assert_allclose(val_hf, val_mf, atol=1e-5, rtol=1e-5,
                                   err_msg=f"Edge bin {edge_bin}: HF value mismatch vs MF")
        np.testing.assert_allclose(val_hf, direct_val, atol=1e-5, rtol=1e-5,
                                   err_msg=f"Edge bin {edge_bin}: HF value mismatch vs direct IFFT")

    @pytest.mark.parametrize("edge_bin", [0, 1, 200, 500, 799, 800, 1023])
    def test_edge_bin_dif_exact_parity(self, edge_bin):
        """Verify that DIF HierarchicalFilter matches MatchedFilter on bandlimited analytic signals."""
        N = 2048
        K = N // 2
        rng = np.random.default_rng(2000 + edge_bin)

        # Template supported in [0, 800]
        t_full = np.zeros((1, N), dtype=np.complex64)
        spec = (rng.standard_normal(200) + 1j * rng.standard_normal(200)).astype(np.complex64)
        t_full[0, 20:220] = spec / np.linalg.norm(spec)

        if edge_bin < K:
            t_full[0, edge_bin] += 2.0 + 1.0j

        t_half = np.ascontiguousarray(t_full[:, :K].copy())

        # Bandlimited data
        d_full = np.zeros((1, N), dtype=np.complex64)
        d_spec = (rng.standard_normal(800) + 1j * rng.standard_normal(800)).astype(np.complex64)
        d_full[0, :800] = d_spec / np.linalg.norm(d_spec)
        d_full += t_full * 5.0

        mf_plan = mf.MatchedFilter(N, ndata=1, ntemplates=1)
        mf_plan.set_templates(t_full)
        mf_plan.set_data(d_full)
        res_mf = mf_plan.run(threshold=0.0)

        hf_dif = mf.HierarchicalFilter(N, ndata=1, ntemplates=1, band=256, taps=8, cascade=False)
        hf_dif.set_hermitian(False)
        hf_dif.set_coarse_threshold(0.0)
        hf_dif.set_templates(t_half)
        hf_dif.set_data(d_full)
        res_hf = hf_dif.run(threshold=0.0)

        idx_mf = res_mf['index'][0, 0, 0]
        val_mf = res_mf['value'][0, 0, 0]
        idx_hf = res_hf['index'][0, 0, 0]
        val_hf = res_hf['value'][0, 0, 0]

        assert idx_hf == idx_mf, f"DIF edge bin {edge_bin}: index mismatch {idx_hf} vs {idx_mf}"
        np.testing.assert_allclose(val_hf, val_mf, atol=1e-5, rtol=1e-5)


class TestNoiseFloorInvariant:
    """Stress-test the noise floor invariant: unit Gaussian noise produces std(Re(rho)) = 1.00 +/- 0.02."""

    def test_noise_floor_hermitian_mode(self):
        N = 2048
        K = N // 2
        n_blocks = 120
        rng = np.random.default_rng(31415)

        h_raw = rng.standard_normal(350).astype(np.float32)
        h_raw /= np.linalg.norm(h_raw)  # sum(h^2) == 1.0

        h_buf = np.zeros(N, dtype=np.float32)
        h_buf[:len(h_raw)] = h_raw
        t_full = np.fft.fft(h_buf).astype(np.complex64).reshape(1, N)

        t_half = np.ascontiguousarray(t_full[:, :K].copy())
        t_half[0, 0] = t_full[0, 0].real + 1j * t_full[0, K].real

        all_re_hf = []
        all_re_mf = []

        hf_plan = mf.HierarchicalFilter(N, ndata=1, ntemplates=1, band=256, taps=8, cascade=False)
        hf_plan.set_hermitian(True)
        hf_plan.set_coarse_threshold(0.0)
        hf_plan.set_templates(t_half)

        mf_plan = mf.MatchedFilter(N, ndata=1, ntemplates=1)
        mf_plan.set_templates(t_full)

        for _ in range(n_blocks):
            noise_time = (rng.standard_normal(N) + 1j * rng.standard_normal(N)).astype(np.complex64)
            d_full = (np.fft.fft(noise_time) / N).astype(np.complex64).reshape(1, N)

            hf_plan.set_data(d_full)
            res_hf = hf_plan.run(binsize=1, threshold=0.0)
            v_hf = res_hf['value'][0, 0, :]

            mf_plan.set_data(d_full)
            res_mf = mf_plan.run(binsize=1, threshold=0.0)
            v_mf = res_mf['value'][0, 0, :]

            all_re_hf.append(np.real(v_hf))
            all_re_mf.append(np.real(v_mf))

        all_re_hf = np.concatenate(all_re_hf)
        all_re_mf = np.concatenate(all_re_mf)

        std_hf = np.std(all_re_hf)
        std_mf = np.std(all_re_mf)
        max_diff = np.max(np.abs(all_re_hf - all_re_mf))

        assert abs(std_hf - 1.00) <= 0.02, f"Noise floor invariant failed: std(Re(rho)) = {std_hf:.5f} not in [0.98, 1.02]"
        assert abs(std_mf - 1.00) <= 0.02, f"Baseline MF std(Re(rho)) = {std_mf:.5f} not in [0.98, 1.02]"
        assert max_diff <= 1e-5, f"HF vs MF max difference {max_diff} exceeded 1e-5"

    def test_noise_floor_pure_noise_zero_false_alarms(self):
        """Verify that unit Gaussian noise produces ZERO false alarms above rho >= 6.0 with normalized templates."""
        N = 2048
        S_len = 131072
        rng = np.random.default_rng(4242)

        # Unit-normalized templates (sum h^2 = 1.0)
        n_templates = 8
        taps = []
        counts = []
        for _ in range(n_templates):
            cnt = 300
            h = rng.standard_normal(cnt).astype(np.float32)
            h /= np.linalg.norm(h)
            taps.append(h)
            counts.append(cnt)

        ref = np.ones(N, dtype=np.float32)
        bank_hier = mf.TimeDomainFilterBank(
            taps, counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine='hier', threshold=6.0, coarse_band_hz=256.0,
            reference=ref
        )
        bank_base = mf.TimeDomainFilterBank(
            taps, counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine='flat', threshold=6.0
        )

        noise = (rng.standard_normal(S_len) + 1j * rng.standard_normal(S_len)).astype(np.complex64)
        res_h = bank_hier.filter_series(noise, windows=slice(N, S_len - N), threshold=6.0)
        res_b = bank_base.filter_series(noise, windows=slice(N, S_len - N), threshold=6.0)

        assert len(res_h.snr) == 0, f"False alarm violation! HierarchicalFilter produced {len(res_h.snr)} triggers at rho >= 6.0 in pure noise"
        assert len(res_b.snr) == 0, f"False alarm violation in baseline! Produced {len(res_b.snr)} triggers at rho >= 6.0"


class TestSNRLadderAndFidelity:
    """Stress-test numerical precision across SNR ladder from 6.0 to 100.0."""

    @pytest.mark.parametrize("target_snr", [6.0, 8.0, 10.0, 15.0, 20.0, 50.0, 100.0])
    def test_snr_ladder_precision_and_phase_invariance(self, target_snr):
        """Verify exact SNR parity, sample timing index, and complex phase across SNR ladder."""
        N = 2048
        S_len = 16384
        rng = np.random.default_rng(int(target_snr * 100))

        # Use normalized FIR filter taps
        n_templates = 4
        taps = []
        counts = []
        for i in range(n_templates):
            cnt = 250
            h = rng.standard_normal(cnt).astype(np.float32)
            h /= np.linalg.norm(h)
            taps.append(h)
            counts.append(cnt)

        target_template_idx = 1
        t_tap = taps[target_template_idx]

        ref = np.ones(N, dtype=np.float32)
        bank_hier = mf.TimeDomainFilterBank(
            taps, counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine='hier', threshold=5.0, coarse_band_hz=256.0,
            reference=ref
        )
        bank_base = mf.TimeDomainFilterBank(
            taps, counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine='flat', threshold=5.0
        )

        # Low background noise
        noise = (rng.standard_normal(S_len) + 1j * rng.standard_normal(S_len)).astype(np.complex64) * 0.05

        # Synthesize injection waveform
        inj_phase = rng.uniform(0, 2 * np.pi)
        inj_time = 8192
        inj_waveform = t_tap * np.exp(1j * inj_phase) * target_snr
        noise[inj_time:inj_time + len(t_tap)] += inj_waveform

        res_hier = bank_hier.filter_series(noise, windows=slice(N, S_len - N),
                                           template_index=target_template_idx, threshold=5.0)
        res_base = bank_base.filter_series(noise, windows=slice(N, S_len - N),
                                           template_index=target_template_idx, threshold=5.0)

        assert len(res_hier.snr) > 0, f"SNR {target_snr}: HierarchicalFilter failed to recover injection"
        assert len(res_base.snr) > 0, f"SNR {target_snr}: Baseline failed to recover injection"
        assert len(res_hier.snr) == len(res_base.snr), (
            f"Trigger count mismatch at SNR {target_snr}: {len(res_hier.snr)} vs {len(res_base.snr)}"
        )

        # Check exact sample timing index
        np.testing.assert_array_equal(
            res_hier.sample_indices, res_base.sample_indices,
            err_msg=f"Sample timing index mismatch at SNR {target_snr}!"
        )

        # Check SNR magnitude difference
        snr_diff = np.abs(np.abs(res_hier.snr) - np.abs(res_base.snr))
        max_snr_diff = np.max(snr_diff)
        assert max_snr_diff <= 1e-4, f"Max SNR difference {max_snr_diff:.2e} exceeded 1e-4 at SNR {target_snr}"

        # Check complex phase matching
        phase_hier = np.angle(res_hier.snr)
        phase_base = np.angle(res_base.snr)
        phase_diff = np.abs(np.angle(np.exp(1j * (phase_hier - phase_base))))
        max_phase_diff = np.max(phase_diff)
        assert max_phase_diff <= 1e-4, f"Max phase difference {max_phase_diff:.2e} rad exceeded 1e-4 at SNR {target_snr}"


class TestTimingAndPhaseInvariance:
    """Stress-test sub-sample drift and phase linearity across arrivals and angles."""

    def test_arrival_time_sweep_zero_drift(self):
        """Sweep injection arrival time across 20 consecutive samples; verify zero sample drift."""
        N = 2048
        S_len = 8192
        rng = np.random.default_rng(555)
        h = rng.standard_normal(250).astype(np.float32)
        h /= np.linalg.norm(h)
        taps = [h]
        counts = [len(h)]
        target_template_idx = 0
        t_tap = taps[0]

        ref = np.ones(N, dtype=np.float32)
        bank_hier = mf.TimeDomainFilterBank(
            taps, counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine='hier', threshold=6.0, coarse_band_hz=256.0,
            reference=ref
        )
        bank_base = mf.TimeDomainFilterBank(
            taps, counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine='flat', threshold=6.0
        )

        for offset in range(20):
            inj_pos = 4000 + offset
            noise = np.zeros(S_len, dtype=np.complex64)
            noise[inj_pos:inj_pos + len(t_tap)] = t_tap * 12.0

            r_h = bank_hier.filter_series(noise, windows=slice(N, S_len - N),
                                          template_index=target_template_idx, threshold=6.0)
            r_b = bank_base.filter_series(noise, windows=slice(N, S_len - N),
                                          template_index=target_template_idx, threshold=6.0)

            assert len(r_h.sample_indices) == 1
            assert len(r_b.sample_indices) == 1
            assert r_h.sample_indices[0] == r_b.sample_indices[0], (
                f"Timing offset {offset}: sample index drift! HF={r_h.sample_indices[0]} vs Base={r_b.sample_indices[0]}"
            )
            np.testing.assert_allclose(r_h.snr[0], r_b.snr[0], atol=1e-5, rtol=1e-5)

    def test_phase_sweep_linearity(self):
        """Sweep phase angle from 0 to 2*pi in 16 steps; verify exact phase tracking."""
        N = 2048
        S_len = 8192
        rng = np.random.default_rng(777)
        h = rng.standard_normal(250).astype(np.float32)
        h /= np.linalg.norm(h)
        taps = [h]
        counts = [len(h)]
        target_template_idx = 0
        t_tap = taps[0]

        ref = np.ones(N, dtype=np.float32)
        bank_hier = mf.TimeDomainFilterBank(
            taps, counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine='hier', threshold=6.0, coarse_band_hz=256.0,
            reference=ref
        )
        bank_base = mf.TimeDomainFilterBank(
            taps, counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine='flat', threshold=6.0
        )

        inj_pos = 4000
        angles = np.linspace(0, 2 * np.pi, 16, endpoint=False)

        for ang in angles:
            noise = np.zeros(S_len, dtype=np.complex64)
            noise[inj_pos:inj_pos + len(t_tap)] = t_tap * 15.0 * np.exp(1j * ang)

            r_h = bank_hier.filter_series(noise, windows=slice(N, S_len - N),
                                          template_index=target_template_idx, threshold=6.0)
            r_b = bank_base.filter_series(noise, windows=slice(N, S_len - N),
                                          template_index=target_template_idx, threshold=6.0)

            assert len(r_h.snr) == 1
            assert len(r_b.snr) == 1
            diff = abs(r_h.snr[0] - r_b.snr[0])
            assert diff <= 1e-4, f"Angle {ang:.3f}: complex SNR diff {diff:.2e} exceeded 1e-4"


class TestBoundaryAndNegativeConditions:
    """Stress-test edge window boundaries and caller ordering semantics."""

    def test_window_boundary_edge_triggers(self):
        """Trigger positioned exactly at window boundaries."""
        N = 2048
        S_len = 16384
        rng = np.random.default_rng(888)
        h = rng.standard_normal(250).astype(np.float32)
        h /= np.linalg.norm(h)
        taps = [h]
        counts = [len(h)]
        t_tap = taps[0]

        ref = np.ones(N, dtype=np.float32)
        bank = mf.TimeDomainFilterBank(
            taps, counts,
            tap_sample_rate=2048, data_sample_rate=2048,
            engine='hier', threshold=5.0, coarse_band_hz=256.0,
            reference=ref
        )

        # Place injection so valid slice starts/ends close to peak
        v_start = 2048
        v_stop = 8192
        noise = np.zeros(S_len, dtype=np.complex64)
        noise[3000:3000 + len(t_tap)] = t_tap * 10.0

        res = bank.filter_series(noise, windows=slice(v_start, v_stop), threshold=5.0)
        assert len(res.sample_indices) > 0
        for s in res.sample_indices:
            assert v_start <= s < v_stop, f"Trigger index {s} outside valid window [{v_start}, {v_stop})"

    def test_binsize_granularity_sweep(self):
        """Verify binsize powers of 2 from 2048 down to 128 in HierarchicalFilter."""
        N = 2048
        K = N // 2
        rng = np.random.default_rng(987)

        h_raw = rng.standard_normal(200).astype(np.float32)
        h_buf = np.zeros(N, dtype=np.float32)
        h_buf[:len(h_raw)] = h_raw
        t_full = np.fft.fft(h_buf).astype(np.complex64).reshape(1, N)
        t_half = np.ascontiguousarray(t_full[:, :K].copy())
        t_half[0, 0] = t_full[0, 0].real + 1j * t_full[0, K].real

        d_time = (rng.standard_normal(N) + 1j * rng.standard_normal(N)).astype(np.complex64)
        d_full = (np.fft.fft(d_time) / N).astype(np.complex64).reshape(1, N)
        d_full += t_full * 8.0 / N

        mf_plan = mf.MatchedFilter(N, ndata=1, ntemplates=1)
        mf_plan.set_templates(t_full)
        mf_plan.set_data(d_full)

        hf_plan = mf.HierarchicalFilter(N, ndata=1, ntemplates=1, band=256, taps=8, cascade=False)
        hf_plan.set_hermitian(True)
        hf_plan.set_coarse_threshold(0.0)
        hf_plan.set_templates(t_half)
        hf_plan.set_data(d_full)

        for bs in [2048, 1024, 512, 256, 128]:
            r_mf = mf_plan.run(binsize=bs, threshold=0.0)
            r_hf = hf_plan.run(binsize=bs, threshold=0.0)

            np.testing.assert_array_equal(
                r_hf['index'][0, 0, :], r_mf['index'][0, 0, :],
                err_msg=f"Binsize {bs}: peak index mismatch between HF and MF"
            )
            np.testing.assert_allclose(
                r_hf['value'][0, 0, :], r_mf['value'][0, 0, :], atol=1e-5, rtol=1e-5,
                err_msg=f"Binsize {bs}: peak value mismatch between HF and MF"
            )

    def test_calling_order_contract_audit(self):
        """Audit the calling order contract: setting templates before data vs data before templates."""
        N = 2048
        K = N // 2
        rng = np.random.default_rng(1234)

        t_full = np.zeros((1, N), dtype=np.complex64)
        spec = (rng.standard_normal(200) + 1j * rng.standard_normal(200)).astype(np.complex64)
        t_full[0, 20:220] = spec / np.linalg.norm(spec)
        t_half = t_full[:, :K].copy()

        d_full = np.zeros((1, N), dtype=np.complex64)
        d_full[0, 20:220] = spec / np.linalg.norm(spec)

        # Correct contract: templates set before data
        hf_ok = mf.HierarchicalFilter(N, ndata=1, ntemplates=1, band=256, taps=8, cascade=False)
        hf_ok.set_coarse_threshold(0.0)
        hf_ok.set_templates(t_half)
        hf_ok.set_data(d_full)
        r_ok = hf_ok.run(threshold=0.0)
        assert r_ok['index'][0, 0, 0] >= 0, "Correct calling order failed to detect trigger"

        # Adverse order: data set before templates (re-instantiates C plan with K bins)
        hf_adv = mf.HierarchicalFilter(N, ndata=1, ntemplates=1, band=256, taps=8, cascade=False)
        hf_adv.set_coarse_threshold(0.0)
        hf_adv.set_data(d_full)
        hf_adv.set_templates(t_half)
        r_adv = hf_adv.run(threshold=0.0)
        assert r_adv['index'][0, 0, 0] == r_ok['index'][0, 0, 0], "Calling order affected trigger index"
        np.testing.assert_allclose(r_adv['value'][0, 0, 0], r_ok['value'][0, 0, 0], atol=1e-6)
