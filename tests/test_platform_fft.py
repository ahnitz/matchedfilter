"""The block forward through the platform FFT (src/fft_accel.c: vDSP on macOS) is an autotuner
candidate. Where it exists, a CPU search's peaks with it match those with the engine's
transform (fp32 rounding apart); where it does not, asking for it says so."""
import numpy as np

import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank
from test_time_domain import _whitened_inspiral_bank


def _search(monkeypatch, platform):
    monkeypatch.setenv("MF_AUTOTUNE", "0")

    def pick(self):                     # this test's choice instead of the trial's
        if self._mf is not None and bool(self._pfft) != platform:
            self._pfft = platform and self._mf.set_platform_fft(platform)
            if not platform:
                self._mf.set_platform_fft(False)
        return False
    monkeypatch.setattr(mf.HierarchicalFilter, "_pfft_before_call", pick)
    rng = np.random.default_rng(5)
    counts = sorted(rng.integers(200, 1800, 16))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.0,
                                false_dismissal=1e-3, device="cpu", fft_lengths=[2048])
    bank.set_reference(w, delta_f=df)
    S = 1 << 18
    X = np.fft.fft(rng.standard_normal(S))
    X[S // 2:] = 0
    x = (np.fft.ifft(X) * 2).astype(np.complex64)
    x[S // 3] += 40.0
    r = bank.filter_series(x, windows=slice(4096, S - 4096))
    used = any(getattr(g.plan, "_pfft", False) for g in bank._groups)
    return r, used


def test_platform_fft_matches_engine(monkeypatch):
    a, _ = _search(monkeypatch, False)
    b, used = _search(monkeypatch, True)
    if not used:
        return                           # no platform FFT on this machine
    assert len(a.snr) > 0
    np.testing.assert_array_equal(a.sample_indices, b.sample_indices)
    np.testing.assert_array_equal(a.template_indices, b.template_indices)
    np.testing.assert_allclose(np.abs(b.snr), np.abs(a.snr), rtol=1e-4)


def test_platform_fft_refused_where_absent():
    h = mf._core.HMF(2048, 2, 2, [256], 2, 2048)
    on = h.set_platform_fft(True)
    import sys
    assert on == (sys.platform == "darwin")


def test_continuous_correlation_platform_fft_matches_engine():
    """The middle stage's continuous correlation through the platform FFT (a cost-model
    candidate, _CORR_PFFT) equals the engine's to fp32 rounding."""
    from matchedfilter import CorrelationFilter, _automatic_series_layout
    n, nt, taps = 8192, 4, 2048
    rng = np.random.default_rng(1)
    h = np.zeros((nt, n), np.complex64)
    h[:, :taps] = rng.standard_normal((nt, taps))
    L = 6 * n
    ser = (rng.standard_normal(L) + 1j * rng.standard_normal(L)).astype(np.complex64)
    cf = CorrelationFilter(n, ndata=1, ntemplates=nt, valid=(taps // 2, n - taps // 2))
    cf.set_templates(np.fft.fft(h, axis=1).astype(np.complex64))
    lo, hi = cf.valid
    st, _, _ = _automatic_series_layout(L, cf.valid)
    ep = cf._execution_plan()
    out = {}
    for on in (False, True):
        if not ep.set_platform_fft(on):
            assert on
            return                               # no platform FFT here
        d = np.zeros((nt, L), np.complex64)
        ep.correlate_series_continuous(ser, st, lo, hi, 0, nt, d)
        out[on] = d
    a, b = out[False], out[True]
    assert np.abs(a - b).max() <= 1e-5 * np.abs(a).max()
