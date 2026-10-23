"""filter_series' peak bins are the window's, whatever blocks the bank computes them in.

binsize is the samples per peak bin of each window: window [v0, v1) has bins [v0 + k*binsize,
v0 + (k+1)*binsize) clipped to v1, and each bin reports the peak of the correlation inside it.
Until 2026-10-23 the bins restarted at every block's span instead, so a window of exactly 1000
bins of 61 samples came back as 1021 peaks at block size 2048 and 1002 at 4096. pycbc's
asymmetric follow-up asks for exactly such a window, and the hierarchical engine picks its
block size by a timed trial, so the follow-up triggers changed from run to run.

The reference is the bank's own correlation series (correlate_series), binned here in numpy:
every engine, block size and device must report its peak in every bin, at its sample.
"""
import numpy as np
import pytest

from conftest import usable_gpu
from matchedfilter.time_domain import TimeDomainFilterBank

L, NT, S = 257, 3, 1 << 17


def _inputs():
    rng = np.random.default_rng(11)
    taps = (rng.standard_normal((NT, L)) + 1j * rng.standard_normal((NT, L))).astype(np.complex64)
    taps /= np.sqrt((np.abs(taps) ** 2).sum(axis=1))[:, None]
    ser = ((rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2)).astype(np.complex64)
    return taps, ser


def _reference(corr, windows, binsize, threshold):
    """{(template, sample): |snr|} of every window-aligned bin's peak at or above threshold."""
    out = {}
    for t in range(corr.shape[0]):
        for v0, v1 in windows:
            for b0 in range(v0, v1, binsize):
                seg = np.abs(corr[t, b0:min(b0 + binsize, v1)])
                k = int(np.argmax(seg))
                if seg[k] >= threshold and seg[k] > 0:
                    out[(t, b0 + k)] = float(seg[k])
    return out


def _bank(taps, engine, n, device):
    b = TimeDomainFilterBank(taps, engine=engine, threshold=5.0,
                             fft_lengths=[n] if n else None, device=device)
    if engine == "hier":
        b.set_reference(np.ones(2049), delta_f=0.5)
    return b


DEVICES = [None, "gpu"]


@pytest.mark.parametrize("device", DEVICES)
@pytest.mark.parametrize("engine", ["flat", "hier"])
@pytest.mark.parametrize("n", [2048, 4096])
@pytest.mark.parametrize("binsize", [61, 1000, 2048, 3001])
def test_bins_are_the_windows(device, engine, n, binsize, monkeypatch):
    # Threshold 0 reports every bin; the hierarchical engine then runs ungated (exact).
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    if device == "gpu":
        device = usable_gpu() or pytest.skip("no usable GPU")
    taps, ser = _inputs()
    corr = TimeDomainFilterBank(taps, engine="corr").correlate_series(ser)
    # Window starts off every block edge; one window shorter than a bin, one many bins long.
    windows = [(20_017, 20_017 + 1000 * 61), (90_001, 90_001 + 37), (100_003, 123_456)]
    want = _reference(corr, windows, binsize, 0.0)
    bank = _bank(taps, engine, n, device)
    r = bank.filter_series(ser, windows=[slice(a, b) for a, b in windows], binsize=binsize,
                           threshold=0.0)
    got = {(int(t), int(i)): float(abs(v)) for t, i, v in
           zip(r.template_indices, r.sample_indices, r.snr)}
    assert set(got) == set(want), ("%d bins differ: %d reported outside the window bins' peaks, "
                                   "%d window bins missing" % (len(set(got) ^ set(want)),
                                                              len(set(got) - set(want)),
                                                              len(set(want) - set(got))))
    for k, v in want.items():
        assert got[k] == pytest.approx(v, rel=2e-5, abs=1e-6)


@pytest.mark.parametrize("n", [2048, 4096])
def test_one_template_follow_up_window_has_its_bins(n, monkeypatch):
    # pycbc's asymmetric follow-up: one template, num_bins bins of bin_width, threshold 0.
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    taps, ser = _inputs()
    bank = _bank(taps, "hier", n, None)
    r = bank.filter_series(ser, windows=slice(50_017, 50_017 + 1000 * 61), binsize=61,
                           threshold=0.0, template_index=1)
    bins = (np.asarray(r.sample_indices) - 50_017) // 61
    assert len(bins) == 1000 and np.array_equal(np.sort(bins), np.arange(1000))


@pytest.mark.parametrize("engine", ["flat", "hier"])
def test_threshold_keeps_the_window_bins_above_it(engine, monkeypatch):
    # Above a threshold a bin is reported iff its window-aligned peak reaches it; the
    # hierarchical engine may dismiss within its budget, so it must report a subset, each
    # exactly the reference's.
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    taps, ser = _inputs()
    ser2 = ser.copy()
    for s in (30_100, 61_234, 101_999):            # loud injections near block edges
        ser2[s:s + L] += (8.0 * taps[1]).astype(np.complex64)
    corr = TimeDomainFilterBank(taps, engine="corr").correlate_series(ser2)
    windows = [(20_017, 120_000)]
    want = _reference(corr, windows, 2048, 4.0)
    bank = _bank(taps, engine, 2048, None)
    r = bank.filter_series(ser2, windows=slice(*windows[0]), binsize=2048, threshold=4.0)
    got = {(int(t), int(i)): float(abs(v)) for t, i, v in
           zip(r.template_indices, r.sample_indices, r.snr)}
    assert want, "the injections must cross the threshold"
    if engine == "flat":
        assert set(got) == set(want)
    else:
        assert set(got) <= set(want)
        assert len(got) >= 3
    for k, v in got.items():
        assert v == pytest.approx(want[k], rel=2e-5, abs=1e-6)


@pytest.mark.parametrize("device_followups", ["1", "0"])
@pytest.mark.parametrize("n", [2048, 4096])
def test_batched_follow_ups_have_the_window_bins(n, device_followups, monkeypatch):
    # filter_series_many's follow-up batches on a GPU bank: the device follow-ups (refineItems)
    # and, without them, the host-built items (peaks_items) -- each its own path to the bins.
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_DEVICE_FOLLOWUPS", device_followups)
    device = usable_gpu() or pytest.skip("no usable GPU")
    taps, ser = _inputs()
    bank = _bank(taps, "hier", n, device)
    gser = bank.empty_shared(ser.shape, input=True)
    gser[:] = ser
    corr = TimeDomainFilterBank(taps, engine="corr").correlate_series(ser)
    windows = [(30_017, 30_017 + 300 * 61), (77_771, 77_771 + 400 * 61)]
    jobs = [(bank, gser, dict(windows=slice(a, b), binsize=61, threshold=0.0, template_index=t))
            for (a, b), t in zip(windows, (1, 2))]
    results = TimeDomainFilterBank.filter_series_many(jobs)
    for (a, b), t, r in zip(windows, (1, 2), results):
        want = {s for (tt, s) in _reference(corr[t:t + 1], [(a, b)], 61, 0.0)}
        got = set(int(i) for i in r.sample_indices)
        assert got == want, "%d of %d bins differ" % (len(got ^ want), len(want))


def test_gpu_hierarchical_refine_has_the_window_bins(monkeypatch):
    # Above threshold the GPU hierarchical bank refines its survivors with the bins of the
    # window (the refine's row table carries each block's phase).
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    device = usable_gpu() or pytest.skip("no usable GPU")
    taps, ser = _inputs()
    ser2 = ser.copy()
    for s in (30_100, 61_234, 101_999):
        ser2[s:s + L] += (8.0 * taps[1]).astype(np.complex64)
    corr = TimeDomainFilterBank(taps, engine="corr").correlate_series(ser2)
    want = _reference(corr, [(20_017, 120_000)], 2048, 4.0)
    bank = _bank(taps, "hier", 2048, device)
    r = bank.filter_series(ser2, windows=slice(20_017, 120_000), binsize=2048, threshold=4.0)
    got = {(int(t), int(i)): float(abs(v)) for t, i, v in
           zip(r.template_indices, r.sample_indices, r.snr)}
    assert set(got) <= set(want) and len(got) >= 3
    for k, v in got.items():
        assert v == pytest.approx(want[k], rel=2e-5, abs=1e-6)


@pytest.mark.parametrize("device", DEVICES)
@pytest.mark.parametrize("engine", ["flat", "hier"])
@pytest.mark.parametrize("binsize", [37, 150, 300])
def test_small_blocks_have_the_window_bins(device, engine, binsize, monkeypatch):
    # 256-sample blocks: the CPU's pair-batched small-N path, whose lanes are templates of one
    # block or pairs of different blocks (a lane's phase may be whole bins: the padding that
    # keeps a bank one call).
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    if device == "gpu":
        device = usable_gpu() or pytest.skip("no usable GPU")
    rng = np.random.default_rng(3)
    taps = (rng.standard_normal((NT, 97)) + 1j * rng.standard_normal((NT, 97))).astype(np.complex64)
    taps /= np.sqrt((np.abs(taps) ** 2).sum(axis=1))[:, None]
    _, ser = _inputs()
    corr = TimeDomainFilterBank(taps, engine="corr").correlate_series(ser)
    windows = [(20_017, 20_017 + 40 * 61), (60_003, 71_111)]
    want = _reference(corr, windows, binsize, 0.0)
    bank = TimeDomainFilterBank(taps, engine=engine, threshold=5.0, fft_lengths=[256],
                                device=device)
    if engine == "hier":
        bank.set_reference(np.ones(129), delta_f=8.0)
    r = bank.filter_series(ser, windows=[slice(a, b) for a, b in windows], binsize=binsize,
                           threshold=0.0)
    got = {(int(t), int(i)): float(abs(v)) for t, i, v in
           zip(r.template_indices, r.sample_indices, r.snr)}
    assert set(got) == set(want), "%d bins differ" % len(set(got) ^ set(want))
    for k, v in want.items():
        assert got[k] == pytest.approx(v, rel=2e-5, abs=1e-6)
