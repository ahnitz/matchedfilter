"""Reference setters observe updates without retaining a search's retired PSDs."""
import gc
from concurrent.futures import ThreadPoolExecutor
import threading
from types import SimpleNamespace
import weakref

import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from matchedfilter import time_domain as td
from matchedfilter.gatechain import rebin_profile


@pytest.fixture(autouse=True)
def fresh_caches(monkeypatch):
    monkeypatch.setattr(td, "_REF_PROFILE_CACHE", td._ReferenceCache())
    monkeypatch.setattr(td, "_REF_BINNED_CACHE", td._ReferenceCache())


def _bank(rate=2048):
    return TimeDomainFilterBank(np.ones((1, 31), np.float32), engine="hier",
                                fft_lengths=[2048], coarse_band_hz=512,
                                tap_sample_rate=rate, data_sample_rate=rate)


def _profile(bank):
    return bank._groups[0].plan._pending_ref


def _expected(reference, rate=2048, df=1):
    p = rebin_profile(reference, df, rate, 2048).astype(np.float32)
    return p / p.sum()


def test_shared_reference_rebins_for_each_data_sample_rate():
    ref = np.zeros(2049)
    ref[400:501] = 1
    for rate in (2048, 4096, 2048):
        bank = _bank(rate)
        bank.set_reference(ref, delta_f=1)
        np.testing.assert_allclose(_profile(bank), _expected(ref, rate), rtol=1e-6)


@pytest.mark.parametrize("fine", [False, True])
def test_repeated_setter_observes_in_place_reference_changes(fine):
    bank = _bank()
    ref = np.ones(2048, np.float64)
    kwargs = {"delta_f": 1} if fine else {}
    bank.set_reference(ref, **kwargs)
    before = _profile(bank).copy()
    version = bank._state_version
    bank.set_reference(ref, **kwargs)
    assert bank._state_version == version       # unchanged setters preserve replay state

    ref[:512] = 8
    bank.set_reference(ref, **kwargs)
    assert bank._state_version > version
    assert not np.array_equal(_profile(bank), before)
    expected = _expected(ref) if fine else ref.astype(np.float32)
    np.testing.assert_allclose(_profile(bank), expected, rtol=1e-6)


@pytest.mark.parametrize("changed", ["template", "psd"])
def test_reference_from_template_observes_in_place_input_changes(changed):
    bank = _bank()
    template = np.ones(2049, np.complex64)
    psd = np.ones(2049)
    stilde = SimpleNamespace(delta_f=1)
    bank.set_reference_from_template(stilde, psd, template)
    before = _profile(bank).copy()
    (template if changed == "template" else psd)[:512] = 4
    bank.set_reference_from_template(stilde, psd, template)
    assert not np.array_equal(_profile(bank), before)
    np.testing.assert_allclose(_profile(bank), _expected(np.abs(template) ** 2 / psd),
                               rtol=1e-6)


def test_reference_caches_release_retired_inputs():
    bank = _bank()
    template = np.ones(2049, np.complex64)
    template_ref = weakref.ref(template)
    refs = []
    for i in range(8):
        psd = np.ones(2049)
        psd[:512] = i + 1
        refs.append(weakref.ref(psd))
        bank.set_reference_from_template(SimpleNamespace(delta_f=1), psd, template)
    del psd, template, bank
    gc.collect()
    assert template_ref() is None
    assert all(ref() is None for ref in refs)
    assert not td._REF_PROFILE_CACHE.entries
    assert not td._REF_BINNED_CACHE.entries
    assert td._REF_PROFILE_CACHE.nbytes == td._REF_BINNED_CACHE.nbytes == 0


def test_reference_cache_bounds_live_snapshots_and_derived_profiles():
    # Eight-byte sources and eight-byte results: only two entries fit, even though
    # every caller keeps its input alive. Accessing one protects it from eviction.
    cache = td._ReferenceCache(max_entries=3, max_bytes=32)
    sources = [np.ones(1) for _ in range(4)]
    for i in (0, 1):
        cache.put(i, (sources[i],), sources[i].copy())
    assert cache.get(0, (sources[0],)) is not None
    cache.put(2, (sources[2],), sources[2].copy())
    assert cache.get(1, (sources[1],)) is None
    assert cache.nbytes == 32
    assert len(cache.entries) == 2
    cache.max_entries = 1
    cache.put(3, (sources[3],), sources[3].copy())
    assert list(cache.entries) == [3]
    large = np.ones(100)
    assert cache.put(4, (large,), large.copy()) is None
    assert cache.nbytes == 16


def test_list_reference_remains_supported_without_identity_caching():
    bank = _bank()
    ref = [1.] * 2048
    bank.set_reference(ref)
    ref[0] = 8
    bank.set_reference(ref)
    assert _profile(bank)[0] == 8


def test_reference_cache_serializes_comparison_and_eviction(monkeypatch):
    cache = td._ReferenceCache(max_entries=1)
    first, second = np.ones(8), np.zeros(8)
    cache.put("first", (first,), first.copy())
    comparing, release, inserting, inserted = (threading.Event() for _ in range(4))
    array_equal = np.array_equal

    def paused_equal(a, b):
        comparing.set()
        assert release.wait(5)
        return array_equal(a, b)

    def replace():
        inserting.set()
        cache.put("second", (second,), second.copy())
        inserted.set()

    monkeypatch.setattr(np, "array_equal", paused_equal)
    with ThreadPoolExecutor(max_workers=2) as pool:
        lookup = pool.submit(cache.get, "first", (first,))
        try:
            assert comparing.wait(5)
            replacement = pool.submit(replace)
            assert inserting.wait(5)
            assert not inserted.wait(.05)       # comparison released the GIL, not the cache
        finally:
            release.set()
        assert lookup.result(5) is not None
        replacement.result(5)
    assert list(cache.entries) == ["second"]
    assert cache.nbytes == 2 * second.nbytes
