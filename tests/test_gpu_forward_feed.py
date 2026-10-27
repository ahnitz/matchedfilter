"""The band feed of the hierarchical fine stage, on every GPU (_gpuhier): a call that claims
the deferred forward of its spectra writes only the tiers' bands (forward_tier0.slang for an
fp16 first tier, else seriesForwardBands) and recomputes its refine blocks. Results must be a
correct hierarchical result, as the separate forward's are."""
import numpy as np
import pytest
from conftest import usable_gpu_reason

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

#: Each run's gates, (chain, thresholds) per template group, by run label: a failure names
#: the gates both sides ran, so a threshold split taken differently is told from wrong data.
_GATES = {}


def _run(monkeypatch, enabled, device=None, engine="hier", rng_seed=5):
    from conftest import usable_gpu
    dev = usable_gpu() if device is None else device
    if dev is None:
        pytest.skip(usable_gpu_reason())
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
    _GATES[(str(dev), engine, enabled)] = [
        (tuple(g._plan._chain or ()), tuple(float(t) for t in g._plan._thresholds(required=False) or ()))
        for g in bank._groups if g.is_hier and g._plan is not None]
    return [{(int(t), int(i)): complex(v) for t, i, v in
             zip(r.template_indices, r.sample_indices, r.snr)} for r in out]


def _assert_consistent(got, same_chain, exact, label, gates=""):
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
    assert len(flips) <= GATE_FLIPS, "%s: %d gate decisions differ from the CPU's: %s; %s" % (
        label, len(flips), [(k, round(abs(exact[k]), 4)) for k in flips[:6]], gates)


def test_fused_forward_matches_separate(monkeypatch):
    """The band forward and the separate forward each give a correct hierarchical result:
    only exact peaks, at the exact SNR, and the CPU's gate decisions on the same chain up to
    rounding-margin flips. Exact equality between the two GPU paths is not a property of
    either: they round the coarse bands differently.

    The GPU runs gate at the CPU run's thresholds. The model splits the dismissal budget
    across a chain's tiers by each device's calibrated costs, so on a near-tie two devices
    take different valid splits (in full suites dev2 and CI's Metal runner have split
    (256, 512) as (3.03, 3.34) on the GPU against (3.25, 2.63) on the CPU), and then two
    dozen pairs gate differently for that reason alone, not for the feed's numerics."""
    import matchedfilter as mf
    from matchedfilter import _gpuhier
    cpu = _run(monkeypatch, False, device="cpu")
    pinned = {chain: thr for chain, thr in _GATES[("cpu", "hier", False)]}
    model = mf.HierarchicalFilter._thresholds    # the library's own calibration plans keep it
    monkeypatch.setattr(mf.HierarchicalFilter, "_thresholds",
                        lambda self, required=True: pinned.get(tuple(self._chain or ()))
                        or model(self, required=required))
    a = _run(monkeypatch, False)
    before = _gpuhier.CLAIMS[0]
    b = _run(monkeypatch, True)
    assert _gpuhier.CLAIMS[0] > before, "no call claimed its forward"
    from conftest import usable_gpu
    for band in (False, True):                  # the GPU runs gated as the CPU's did
        assert dict(_GATES[(str(usable_gpu()), "hier", band)]) == pinned
    monkeypatch.undo()
    exact = _run(monkeypatch, False, device="cpu", engine="flat")
    assert len(a) == len(b) == len(cpu) == len(exact)
    gates = "gates (chain, thresholds) per group: %s" % {
        "%s %s band=%s" % k: [(c, tuple(round(t, 5) for t in thr)) for c, thr in v]
        for k, v in _GATES.items() if k[1] == "hier"}
    for ra, rb, rc, rx in zip(a, b, cpu, exact):
        assert len(rc) > 100
        _assert_consistent(ra, rc, rx, "separate forward", gates)
        _assert_consistent(rb, rc, rx, "band forward", gates)


def test_every_sparse_way_gives_the_same_peaks(monkeypatch):
    """A sparse hierarchical result read as survivors' rows or compacted on the device (a
    measured choice) is the same result, through the fused batches of filter_series_many:
    the device compaction once read the refine's output before it was written, losing peaks
    only when its timing made it the choice."""
    from matchedfilter import _gpusettings as td
    out = {}
    orig = td.kernel_slot
    for way in ("rows", "compact"):
        # The sparse ways only (flat peaks take this way where they have it, else theirs).
        monkeypatch.setattr(td, "kernel_slot", lambda dev, what, band, d, alt, w=way: (
            w if w in (d, alt) else d) if what == "sparse" else orig(dev, what, band, d, alt))
        out[way] = _run(monkeypatch, False)
    for a, b in zip(out["rows"], out["compact"]):
        assert a == b
