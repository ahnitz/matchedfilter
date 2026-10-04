import numpy as np
import pytest
import matchedfilter as mf
import matchedfilter._core as _core


def inspiral_power(n, exponent=-7 / 3.0, knee_frac=0.0150):
    p = np.zeros(n, dtype=np.float32)
    k = np.arange(1, n // 2).astype(np.float64)
    p[1:n // 2] = (k ** exponent / ((knee_frac * n / k) ** 4 + 1.0)).astype(np.float32)
    return p / p.sum()


@pytest.mark.parametrize("n", [1024, 2048])
@pytest.mark.parametrize("cascade", [False, True])
def test_survivor_pooling_fidelity(n, cascade):
    """Verify that multi-block survivor pooling yields bit-exact triggers matching reference."""
    nd, nt = 4, 16
    band0 = 128 if cascade else 0
    band = 256
    snr_target = 6.0
    threshold = 5.5

    if cascade:
        hmf = _core.HMF(n, nd, nt, snr_target, 0.001, band, 1, 8, 8, band0)
        hmf.set_threshold(3.5, 4.5)
    else:
        hmf = _core.HMF(n, nd, nt, snr_target, 0.001, band, 1, 8, 8)
        hmf.set_threshold(4.5)

    power = inspiral_power(n)
    hmf.set_reference(power)

    # Reference flat filter
    flat_mf = _core.MF(n, nd, nt)

    rng = np.random.default_rng(42)
    # Generate realistic data and templates
    noise_data = (rng.standard_normal((nd, n), dtype=np.float32) + 1j * rng.standard_normal((nd, n), dtype=np.float32))
    templates = np.sqrt(power)[None, :] * np.exp(2j * np.pi * rng.random((nt, n))).astype(np.complex64)

    # Inject 3 strong signals at specific (d, t) pairs to guarantee triggers
    injections = [(0, 3, 8.5), (1, 7, 9.2), (2, 11, 7.8), (3, 2, 8.0)]
    for d, t, snr_val in injections:
        sig = snr_val * templates[t]
        noise_data[d] += sig

    for d in range(nd):
        hmf.set_data(d, noise_data[d])
        flat_mf.set_data(d, noise_data[d])
    for t in range(nt):
        hmf.set_template(t, templates[t])
        flat_mf.set_template(t, templates[t])

    # Run flat MF reference
    ref_peaks = np.empty((nd * nt, 1), dtype=mf.PEAK_DTYPE)
    ref_cnts = np.empty(nd * nt, dtype=np.int32)
    empty_idx = np.empty(0, dtype=np.int64)
    empty_val = np.empty(0, dtype=np.complex64)
    mag = np.empty(0, dtype=np.float32)

    flat_mf.run(0, nd, 0, nt, n, threshold, 0, n, empty_idx, empty_val, mag, ref_cnts, ref_peaks)

    # Run HMF with multi-block survivor pooling
    hmf_peaks = np.empty((nd * nt, 1), dtype=mf.PEAK_DTYPE)
    hmf_cnts = np.empty(nd * nt, dtype=np.int32)
    empty_idx = np.empty(0, dtype=np.int64)
    empty_val = np.empty(0, dtype=np.complex64)
    mag = np.empty(0, dtype=np.float32)

    hmf.run(0, nd, 0, nt, n, threshold, 0, n, empty_idx, empty_val, mag, hmf_cnts, hmf_peaks)

    # Verify injected pairs are detected and match reference
    for d, t, _ in injections:
        row = d * nt + t
        ref_pk = ref_peaks[row, 0]
        hmf_pk = hmf_peaks[row, 0]

        assert ref_pk["index"] >= 0, f"Reference missed injection at ({d}, {t})"
        assert hmf_pk["index"] >= 0, f"HMF missed injection at ({d}, {t})"
        assert hmf_pk["index"] == ref_pk["index"], f"Index mismatch at ({d}, {t}): {hmf_pk['index']} vs {ref_pk['index']}"
        assert np.isclose(np.abs(hmf_pk["value"]), np.abs(ref_pk["value"]), rtol=1e-5), (
            f"Magnitude mismatch at ({d}, {t}): {np.abs(hmf_pk['value'])} vs {np.abs(ref_pk['value'])}"
        )
        assert np.isclose(hmf_pk["value"].real, ref_pk["value"].real, rtol=1e-5)
        assert np.isclose(hmf_pk["value"].imag, ref_pk["value"].imag, rtol=1e-5)

    # For any other pair that triggered in HMF, verify it matches reference exactly
    for row in range(nd * nt):
        if hmf_peaks[row, 0]["index"] >= 0:
            ref_pk = ref_peaks[row, 0]
            hmf_pk = hmf_peaks[row, 0]
            assert hmf_pk["index"] == ref_pk["index"]
            assert np.isclose(np.abs(hmf_pk["value"]), np.abs(ref_pk["value"]), rtol=1e-5)


def test_survivor_pooling_sparse_occupancy():
    """Verify that very sparse survivors across blocks (e.g. 1 survivor per block) execute cleanly."""
    n = 2048
    nd, nt = 8, 32
    hmf = _core.HMF(n, nd, nt, 6.0, 0.001, 256, 1, 8, 8, 128)
    hmf.set_threshold(4.5, 5.0)

    power = inspiral_power(n)
    hmf.set_reference(power)
    flat_mf = _core.MF(n, nd, nt)

    rng = np.random.default_rng(999)
    noise_data = (rng.standard_normal((nd, n), dtype=np.float32) + 1j * rng.standard_normal((nd, n), dtype=np.float32))
    templates = np.sqrt(power)[None, :] * np.exp(2j * np.pi * rng.random((nt, n))).astype(np.complex64)

    # Inject exactly ONE signal in block 1 (template 5) and ONE in block 6 (template 20)
    noise_data[1] += 8.0 * templates[5]
    noise_data[6] += 8.5 * templates[20]

    for d in range(nd):
        hmf.set_data(d, noise_data[d])
        flat_mf.set_data(d, noise_data[d])
    for t in range(nt):
        hmf.set_template(t, templates[t])
        flat_mf.set_template(t, templates[t])

    threshold = 6.0
    ref_peaks = np.empty((nd * nt, 1), dtype=mf.PEAK_DTYPE)
    ref_cnts = np.empty(nd * nt, dtype=np.int32)
    empty_idx = np.empty(0, dtype=np.int64)
    empty_val = np.empty(0, dtype=np.complex64)
    mag = np.empty(0, dtype=np.float32)
    flat_mf.run(0, nd, 0, nt, n, threshold, 0, n, empty_idx, empty_val, mag, ref_cnts, ref_peaks)

    hmf_peaks = np.empty((nd * nt, 1), dtype=mf.PEAK_DTYPE)
    hmf_cnts = np.empty(nd * nt, dtype=np.int32)
    empty_idx = np.empty(0, dtype=np.int64)
    empty_val = np.empty(0, dtype=np.complex64)
    mag = np.empty(0, dtype=np.float32)

    hmf.run(0, nd, 0, nt, n, threshold, 0, n, empty_idx, empty_val, mag, hmf_cnts, hmf_peaks)

    row1 = 1 * nt + 5
    row6 = 6 * nt + 20
    assert hmf_peaks[row1, 0]["index"] == ref_peaks[row1, 0]["index"]
    assert np.isclose(np.abs(hmf_peaks[row1, 0]["value"]), np.abs(ref_peaks[row1, 0]["value"]), rtol=1e-5)
    assert hmf_peaks[row6, 0]["index"] == ref_peaks[row6, 0]["index"]
    assert np.isclose(np.abs(hmf_peaks[row6, 0]["value"]), np.abs(ref_peaks[row6, 0]["value"]), rtol=1e-5)
