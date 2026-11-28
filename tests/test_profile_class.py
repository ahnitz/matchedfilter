"""A reference's ProfileClass: made once per reference and block size and handed to every plan
that reference reaches, identified by its content, answering as the per-call computations it
replaced, and released with the last plan that holds it, with the collector off."""
import gc
import weakref

import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from matchedfilter import _gatedraws as gd
from matchedfilter import time_domain as td

N = 2048


@pytest.fixture(autouse=True)
def fresh_reference_cache(monkeypatch):
    monkeypatch.setattr(td, "_REF_BINNED_CACHE", td._ReferenceCache())


def _bank():
    return TimeDomainFilterBank(np.ones((1, 31), np.float32), engine="hier",
                                fft_lengths=[N], coarse_band_hz=512,
                                tap_sample_rate=2048, data_sample_rate=2048)


def _reference():
    f = np.arange(2049, dtype=np.float64)
    ref = np.zeros(2049)
    ref[20:900] = f[20:900] ** (-7.0 / 3.0)
    return ref


def test_the_plans_given_one_reference_share_one_class():
    ref = _reference()
    first, second = _bank(), _bank()
    first.set_reference(ref, delta_f=1)
    second.set_reference(ref, delta_f=1)
    shared = first._groups[0].plan._profile_class
    assert second._groups[0].plan._profile_class is shared
    assert shared.n == N and not shared.reference.flags.writeable

    # another array of the same content: another class, of the same identity
    other = _bank()
    other.set_reference(ref.copy(), delta_f=1)
    held = other._groups[0].plan._profile_class
    assert held is not shared
    assert held.identity == shared.identity and held.signature == shared.signature
    changed = ref.copy()
    changed[100:200] *= 2.0
    other.set_reference(changed, delta_f=1)
    assert other._groups[0].plan._profile_class.identity != shared.identity


def test_a_class_answers_as_the_computations_it_replaces():
    reference = np.asarray(gd._norm_profile(np.abs(np.sin(np.arange(N) / 97.0)) + 0.1, N) * 3.0,
                           np.float32)
    cls = gd.ProfileClass(reference.copy(), N)
    p = np.asarray(reference, np.float64)
    p = p / p.sum()
    np.testing.assert_array_equal(cls.profile, p)
    bands = gd.candidate_bands(N)
    assert cls.band_offsets()[:2] == (bands, tuple(gd.band_offset(p, N, b) for b in bands))
    assert cls.usable_bands() == gd.usable_bands(reference, N)
    assert [cls.reference_offset(b) for b in bands] == [gd.band_offset(reference, N, b) for b in bands]
    np.testing.assert_array_equal(cls.features, gd._gate_features(p, N))

    # the similarity store's test, decided once per other profile
    near = gd.profile_class(p * (1.0 + 1e-6 * np.cos(np.arange(N))), N)
    far = gd.profile_class(p * (1.0 + 0.5 * (np.arange(N) < 300)), N)
    assert cls.resembles(near.identity, near.unit, near.features)
    assert not cls.resembles(far.identity, far.unit, far.features)
    assert cls.resembles(far.identity, near.unit, near.features) is False   # kept from the first answer
    assert gd.profile_class(p.copy(), N) is gd.profile_class(p.copy(), N)  # one per content
    with pytest.raises(ValueError):
        gd.profile_class(cls, N // 2)


def test_a_class_goes_with_the_last_plan_holding_it_with_the_collector_off():
    ref = _reference()
    bank = _bank()
    bank.set_reference(ref, delta_f=1)
    plan = bank._groups[0].plan
    plan._resolve()                     # a chain chosen and thresholds solved on the class
    held = weakref.ref(plan._profile_class)
    del plan
    gc.collect()
    gc.disable()
    try:
        assert held() is not None           # the bank's plan holds it
        del bank, ref
        assert held() is None
    finally:
        gc.enable()
