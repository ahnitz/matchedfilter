"""The fused forward (forward_tier0.slang) on Metal: the hierarchical fine stage writes only the
tiers' bands and recomputes its refine blocks; results must equal the separate forward+pack."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from test_time_domain import _whitened_inspiral_bank


#: How far two float paths' |snr| may differ: the GPU paths are 1.4-1.9e-5 from the CPU
#: reference on an M2 (three seeds); this is five times that.
SNR_TOL = 1e-4
THRESHOLD = 4.0
#: The gate chain every run takes. The gates are statistical (false_dismissal), so which
#: peaks a run dismisses depends on its chain, and an unforced chain is each device's
#: measured choice: CI's paravirtual GPU chose 512 where the CPU chose 256 and dismissed
#: a different 1036 of the 1080 exact peaks.
CHAIN = "256,512"
#: Gate decisions the two float paths may take differently: a pair whose coarse maximum
#: sits within rounding of a gate threshold. CI saw one such swap in 1036 peaks.
GATE_FLIPS = 2


def _run(monkeypatch, enabled, device=None, engine="hier", rng_seed=5):
    from conftest import usable_gpu
    dev = usable_gpu() if device is None else device
    if dev is None:
        pytest.skip("no usable GPU")
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", CHAIN)
    monkeypatch.setenv("MF_BAND_FORWARD", "1" if enabled else "0")
    rng = np.random.default_rng(rng_seed)
    counts = sorted(rng.integers(200, 1800, 24))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine=engine, threshold=THRESHOLD,
                                false_dismissal=1e-3, device=dev, fft_lengths=[2048])
    bank.set_reference(w, delta_f=df)
    S = 1 << 19
    X = np.fft.fft(rng.standard_normal(S))
    X[S // 2:] = 0
    x = (np.fft.ifft(X) * 2).astype(np.complex64)
    x[S // 3] += 40.0                        # a loud sample: refine survivors in many blocks
    jobs = [(bank, x, dict(windows=slice(4096, S - 4096)))] * 2
    out = TimeDomainFilterBank.filter_series_many(jobs)
    return [{(int(t), int(i)): complex(v) for t, i, v in
             zip(r.template_indices, r.sample_indices, r.snr)} for r in out]


def _assert_consistent(got, same_chain, exact, label):
    """Assert a GPU run's peaks {(template, sample): snr} are a correct hierarchical result.

    Every peak it reports is an exact (ungated) peak with that SNR within SNR_TOL: a gate
    can only dismiss, so anything else is a wrong refine or a misattributed pair. Against
    the CPU on the same chain it may differ by at most GATE_FLIPS peaks, each a gate
    decision taken at rounding margin; more is a gate computed on wrong data."""
    invented = sorted(set(got) - set(exact))
    assert not invented, "%s: peaks the exact filter does not have: %s" % (label, invented[:5])
    worst = max((abs(got[k] - exact[k]) for k in got), default=0.0)
    assert worst <= SNR_TOL, "%s: SNR differs from the exact filter by %.2e" % (label, worst)
    flips = sorted(set(got) ^ set(same_chain))
    assert len(flips) <= GATE_FLIPS, "%s: %d gate decisions differ from the CPU's: %s" % (
        label, len(flips), [(k, round(abs(exact[k]), 4)) for k in flips[:6]])


def test_fused_forward_matches_separate(monkeypatch):
    """The band forward and the separate forward each give a correct hierarchical result:
    only exact peaks, at the exact SNR, and the CPU's gate decisions on the same chain up to
    rounding-margin flips. Exact equality between the two GPU paths is not a property of
    either: they round the coarse bands differently."""
    pytest.importorskip("matchedfilter._mtlcompute")
    try:
        from matchedfilter import _mtlcompute
        _mtlcompute.Context(0).destroy()
    except Exception:
        pytest.skip("Metal not available")
    a = _run(monkeypatch, False)
    before = _mtlcompute._FUSED_FORWARDS[0]
    b = _run(monkeypatch, True)
    assert _mtlcompute._FUSED_FORWARDS[0] > before, "the fused forward was not taken"
    cpu = _run(monkeypatch, False, device="cpu")
    exact = _run(monkeypatch, False, device="cpu", engine="flat")
    assert len(a) == len(b) == len(cpu) == len(exact)
    for ra, rb, rc, rx in zip(a, b, cpu, exact):
        assert len(rc) > 100
        _assert_consistent(ra, rc, rx, "separate forward")
        _assert_consistent(rb, rc, rx, "band forward")
