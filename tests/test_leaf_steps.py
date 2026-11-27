"""Gated CPU leaf calls run as compiled leaf steps (_batches._compile_leaf_steps and
_core.HMFTable): the steps of a call shape are compiled once and reused, a window list given
again as a new list reuses them, and their peaks are, to the bit and in order, those of the
call-at-a-time path (each template group's plan run_series, assembled in Python)."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank, _batches


@pytest.fixture(autouse=True)
def _decisions_fixed(monkeypatch):
    """One chain and screen per plan, whichever path runs it."""
    monkeypatch.setenv("MF_AUTOTUNE", "0")


def _profile(n_bins=16385, delta_f=1.0 / 16.0):
    f = np.arange(n_bins, dtype=np.float64) * delta_f
    return np.where((f >= 24.0) & (f <= 850.0), np.maximum(f, 1.0) ** (-7.0 / 3.0), 0.0), delta_f


def _bank(rng, n_templates=20, complex_taps=False, binsize=None):
    counts = rng.integers(150, 1500, size=n_templates)
    taps = np.zeros((n_templates, int(counts.max())),
                    dtype=np.complex64 if complex_taps else np.float32)
    for i, c in enumerate(counts):
        t = np.arange(c) / 2048.0
        phase = 2 * np.pi * ((30 + 7 * i) * t + 0.5 * (150 + 11 * i) * t * t)
        row = (np.exp(1j * phase) if complex_taps else np.cos(phase)) * np.hanning(c)
        taps[i, :c] = row / np.linalg.norm(row)
    bank = TimeDomainFilterBank(taps, counts, engine="hier", threshold=3.6,
                                false_dismissal=1e-2, device="cpu", binsize=binsize)
    w, df = _profile()
    bank.set_reference(w, delta_f=df)
    return bank


def _same(a, b):
    for field in a._fields:
        x, y = getattr(a, field), getattr(b, field)
        assert x.dtype == y.dtype and x.shape == y.shape, field
        assert x.tobytes() == y.tobytes(), field


def test_a_call_shape_compiles_once_and_a_new_window_list_reuses_it(monkeypatch):
    rng = np.random.default_rng(5)
    bank = _bank(rng)
    x = rng.standard_normal(1 << 17).astype(np.float32)
    compiled = []
    compile_steps = _batches._compile_leaf_steps
    monkeypatch.setattr(_batches, "_compile_leaf_steps",
                        lambda *a, **k: compiled.append(1) or compile_steps(*a, **k))
    first = bank.filter_series(x, windows=[(4000, 50000), (60000, 120000)])
    again = bank.filter_series(x, windows=[(4000, 50000), (60000, 120000)])
    assert len(compiled) == 1
    _same(first, again)
    bank.filter_series(x, windows=[(4000, 50000), (60000, 110000)])
    assert len(compiled) == 2
    bank.filter_series(x.copy(), windows=[(4000, 50000), (60000, 120000)])
    assert len(compiled) == 2                   # another series of the same kind: no compile


def test_compiled_steps_give_the_call_at_a_time_peaks(monkeypatch):
    """Every template group, bin count, window list and series kind of a batch, against the
    same calls made one at a time through each plan's run_series."""
    rng = np.random.default_rng(11)
    real_bank, lane_bank = _bank(rng, binsize=700), _bank(rng, complex_taps=True)
    S = 1 << 17
    x = rng.standard_normal(S).astype(np.float32)
    z = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
    jobs = [(real_bank, x, dict(windows=[(3000, 41000), (47000, 101000)], binsize=300)),
            (real_bank, x[::-1].copy(), dict()),
            (lane_bank, z, dict(windows=slice(9000, 120000))),
            (lane_bank, z.real, dict(windows=[(20000, 30000), (31000, 90000)], binsize=512)),
            (real_bank, x, dict(threshold=4.0))]
    got = TimeDomainFilterBank.filter_series_many(jobs)
    assert sum(len(r.snr) for r in got) > 50
    monkeypatch.setattr(_batches, "_cpu_sparse_batch", lambda *a, **k: set())
    want = [bank.filter_series(series, **kw) for bank, series, kw in jobs]
    for g, w in zip(got, want):
        _same(g, w)
