"""One set of templates searched in several noise profiles: a plan and a bank hold one
calibration per profile (chain, thresholds, screeners) over one copy of the templates, and a
call names the profile it runs. Each profile's results are those of a plan or bank made for
that profile alone."""
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank, _core
from test_direct_refine import _bank, _pinned_direct_prices  # noqa: F401  (direct-refine prices pinned: plans then refine alike)


def _two_references(ref, n):
    """The reference and one with four times its power below bin 64: another detector's
    noise, for which the planner chooses another chain."""
    other = ref.copy()
    k = np.arange(n)
    other[np.minimum(k, n - k) < 64] *= 4.0
    return ref, other


def _plan(data, reference, monkeypatch):
    n, taps, counts, spec, series, layout, ref, window = data
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    hf = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2, search_window=window)
    hf.set_reference(reference); hf.set_templates(spec); hf.set_taps(taps, counts)
    return hf


def _run(hf, data):
    n, taps, counts, spec, series, layout, ref, window = data
    idx, val = hf.run_series(series, *layout, binsize=n, threshold=6.0, raw=True)
    return idx.copy(), val.copy()


def _same(a, b):
    """The same peaks: where they are exactly, their values to the rounding two plans of one
    profile already differ by (a survivor refined by transform in one, directly in the other)."""
    moved = a[0] != b[0]
    assert moved.mean() < 0.01                 # a tie between two lags of one bin, at most
    np.testing.assert_allclose(np.abs(a[1]), np.abs(b[1]), rtol=0, atol=5e-5)
    np.testing.assert_allclose(a[1][~moved], b[1][~moved], rtol=0, atol=5e-5)


def test_a_plan_holds_a_calibration_per_profile(monkeypatch):
    data = _bank(nblocks=60)
    n, ref = data[0], data[6]
    ref_a, ref_b = _two_references(ref, n)
    alone_a, alone_b = _plan(data, ref_a, monkeypatch), _plan(data, ref_b, monkeypatch)
    want_a, want_b = _run(alone_a, data), _run(alone_b, data)
    assert tuple(alone_a._chain) != tuple(alone_b._chain), "the two references plan alike: no test"

    hf = _plan(data, ref_a, monkeypatch)
    assert hf.profiles == (None,)
    hf.use_profile("b")
    hf.set_reference(ref_b)
    assert hf.profiles == (None, "b")
    _same(_run(hf, data), want_b)
    assert tuple(hf._chain) == tuple(alone_b._chain)
    assert tuple(hf._resolve().thresholds) == tuple(alone_b._resolve().thresholds)
    # back and forth: each profile keeps its own chain, thresholds and compiled plan
    for _ in range(2):
        hf.use_profile(None)
        _same(_run(hf, data), want_a)
        assert tuple(hf._chain) == tuple(alone_a._chain)
        hf.use_profile("b")
        _same(_run(hf, data), want_b)
        assert tuple(hf._chain) == tuple(alone_b._chain)
    plans = hf._each_profile(lambda: hf._mf)
    assert plans[0] is not plans[1]
    assert any(hf.__dict__["_template_owner"] is p for p in plans)     # one of the two holds the templates
    assert hf.__dict__["_profile"] == "b"                    # _each_profile leaves it as it was


def test_the_templates_are_held_once(monkeypatch):
    """A second profile's compiled plan reads the first one's templates and taps: it costs
    far less than a plan of its own."""
    import ctypes, gc

    class MI(ctypes.Structure):
        _fields_ = [(k, ctypes.c_size_t) for k in
                    "arena ordblks smblks hblks hblkhd usmblks fsmblks uordblks fordblks keepcost".split()]
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.mallinfo2.restype = MI
    except (OSError, AttributeError):
        pytest.skip("no glibc mallinfo2")

    def used():
        gc.collect()
        m = libc.mallinfo2()
        return m.uordblks + m.hblkhd

    n, nt, group = 1024, 256, 64
    chain = [128, 256]
    keep = []
    before = used()
    own = _core.HMF(n, 1, nt, chain, group, n)
    keep.append(own)
    alone = used() - before
    before = used()
    keep.append(_core.HMF(n, 1, nt, [64, 128], group, n, own))
    shared = used() - before
    assert shared < 0.6 * alone, (shared, alone)
    with pytest.raises((ValueError, TypeError)):
        _core.HMF(n, 1, nt + 1, chain, group, n, own)        # not the same templates
    with pytest.raises((ValueError, TypeError)):
        _core.HMF(n, 1, nt, chain, group, n, keep[1])        # one that holds none of its own


def test_set_data_reaches_the_profile_in_use(monkeypatch):
    """Data set once (set_data) is every profile's: switching profile runs the same data."""
    data = _bank(nblocks=4)
    n, taps, counts, spec, series, layout, ref, window = data
    ref_a, ref_b = _two_references(ref, n)
    block = np.fft.fft(series[:n]).astype(np.complex64)

    def run(hf):
        return hf.run(binsize=n, threshold=6.0, raw=True)

    alone = {}
    for name, r in (("a", ref_a), ("b", ref_b)):
        hf = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2)
        hf.set_reference(r); hf.set_templates(spec); hf.set_data(block[None, :])
        alone[name] = run(hf)
    hf = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-2)
    hf.set_reference(ref_a); hf.set_templates(spec); hf.set_data(block[None, :])
    got_a = run(hf)
    hf.use_profile("b"); hf.set_reference(ref_b)
    got_b = run(hf)
    hf.use_profile(None)
    again_a = run(hf)
    for got, want in ((got_a, alone["a"]), (got_b, alone["b"]), (again_a, alone["a"])):
        for g, w in zip(got, want):
            np.testing.assert_allclose(g, w, rtol=0, atol=5e-5)


def test_a_bank_holds_a_calibration_per_profile():
    """A bank given references under two names filters each named profile as a bank made
    for it alone does -- called one at a time, and with both profiles' calls in one batch."""
    n, taps, counts, spec, series, layout, ref, window = _bank(nblocks=60)
    ref_a, ref_b = _two_references(ref, n)
    opts = dict(engine="hier", threshold=6.0, false_dismissal=1e-2, fft_lengths=[n], binsize=n)

    def alone(reference):
        bank = TimeDomainFilterBank(taps, tap_counts=counts, **opts)
        bank.set_reference(reference)
        return bank.filter_series(series), [tuple(g.plan._chain) for g in bank._groups]

    (want_a, chains_a), (want_b, chains_b) = alone(ref_a), alone(ref_b)
    want = {"a": want_a, "b": want_b}
    assert chains_a != chains_b, "the two references plan alike: no test"
    bank = TimeDomainFilterBank(taps, tap_counts=counts, **opts)
    bank.set_reference(ref_a, profile="a")
    bank.set_reference(ref_b, profile="b")
    assert bank.profiles == ("a", "b")

    def same(got, ref):
        assert got.template_indices.size > 0
        np.testing.assert_array_equal(got.template_indices, ref.template_indices)
        moved = got.sample_indices != ref.sample_indices
        assert moved.mean() < 0.01
        np.testing.assert_allclose(np.abs(got.snr), np.abs(ref.snr), rtol=0, atol=5e-5)

    for name in ("a", "b", "a"):
        same(bank.filter_series(series, profile=name), want[name])
        bank.use_profile(name)
        assert [tuple(g.plan._chain) for g in bank._groups] == (chains_a if name == "a" else chains_b)
    both = TimeDomainFilterBank.filter_series_many(
        [(bank, series, dict(profile="b")), (bank, series, dict(profile="a")), (bank, series, dict(profile="b"))])
    for got, name in zip(both, ("b", "a", "b")):
        same(got, want[name])
    for g in bank._groups:
        assert g.plan.profiles == (None, "b")                # the first profile is the plans' unnamed one
