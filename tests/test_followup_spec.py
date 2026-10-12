"""The follow-up rule (_gpuhost.FollowupSpec): the host reference, and device selections that
must equal it exactly.

select() is the rule pycbc's asymmetric follow-up applies (and tools/ladder.py applied itself):
per job, peaks with |snr| >= threshold, loudest first (stable), one per dedupe interval, each
followed up on the partner job's series. A backend that runs the rule on the device
(``supports_device_followups``) must return the same follow-ups -- same keys, same results --
as filter_series_many(jobs, followups=spec), which runs it on the host.
"""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from matchedfilter._gpuhost import FollowupSpec
from matchedfilter.time_domain import FilterResults, SegmentPlan


def _fr(ti, si, snr):
    n = len(si)
    return FilterResults(np.asarray(ti, np.int64), np.asarray(si, np.int64),
                         np.asarray(snr, np.complex64), np.zeros(n, np.int64), np.zeros(n, np.int64))


def test_select_is_the_ladder_rule():
    """Loudest first, ties in result order, one per second shared across templates."""
    fine = [_fr([0, 1, 2, 3, 4], [10, 2050, 30, 2047, 5000], [7, 9, 7, 8, 5]),
            _fr([], [], [])]
    jobs = [(None, np.zeros(10000, np.complex64), {}), (None, np.zeros(10000, np.complex64), {})]
    spec = FollowupSpec(pairs=[1, 0], threshold=6.0, dedupe=2048, half=100, binsize=61)
    sel = spec.select(jobs, fine)
    # |snr| order: 9 (s=2050, sec 1), 8 (2047, sec 0), 7 (10, sec 0: taken), 7 (30, sec 0)
    assert [(j, c0, ti) for j, _, c0, ti, _ in sel] == [(0, 2050, 1), (0, 2047, 3)]
    assert sel[0][4][2]["windows"] == slice(1950, 2150)
    assert sel[1][4][2]["template_index"] == 3


def _banks(monkeypatch, device, nbanks=2, seed=91):
    from test_time_domain import _whitened_inspiral_bank
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    rng = np.random.default_rng(seed)
    banks = []
    for _ in range(nbanks):
        counts = list(rng.integers(200, 400, 33))
        taps, w, df = _whitened_inspiral_bank(rng, counts)
        b = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=4.5,
                                 false_dismissal=1e-3, device=device, fft_lengths=[2048],
                                 binsize=2048)
        b.set_reference(w, delta_f=df)
        banks.append(b)
    return rng, banks


def _device_followup_backends():
    out = []
    try:
        from matchedfilter import _cuda
        if _cuda.enumerate_devices()[0]:
            out.append("cuda:0")
    except Exception:                                  # noqa: BLE001
        pass
    try:
        from matchedfilter import _vulkan
        if _vulkan.enumerate_devices()[0]:
            out.append("gpu:0")
    except Exception:                                  # noqa: BLE001
        pass
    return out


@pytest.mark.parametrize("device", _device_followup_backends() or ["none"])
def test_device_followups_equal_the_host_rule(device, monkeypatch):
    if device == "none":
        pytest.skip("no backend with device follow-ups")
    rng, banks = _banks(monkeypatch, device)
    gpu = banks[0]._groups[0].plan._gpu
    if not getattr(gpu, "supports_device_followups", False):
        pytest.skip("backend has no device follow-ups")
    S = 1 << 17
    rows = banks[0].empty_shared((2 * len(banks), S))
    jobs = [(b, rows[2 * i + d], dict(windows=slice(4000, S - 4000)))
            for i, b in enumerate(banks) for d in range(2)]
    spec = FollowupSpec(pairs=[j ^ 1 for j in range(len(jobs))], threshold=5.0, dedupe=2048,
                        half=6000, binsize=61)
    plan = SegmentPlan()
    nfu = 0
    for seg in range(6):
        for r in rows:
            X = np.fft.fft(rng.standard_normal(S))
            X[S // 2:] = 0
            r[:] = (np.fft.ifft(X) * 2).astype(np.complex64)
            r[rng.integers(8000, S - 8000, 5)] += 30.0          # loud samples: follow-ups
        fine, fu = plan.run(jobs, followup=spec)
        # The reference: the fine stage as a batch, and each selected follow-up as its own
        # filter_series call (no batched or device path on either side).
        want_fine = TimeDomainFilterBank.filter_series_many(jobs)
        want_fu = [(j, rank, c0, ti, b.filter_series(x, **kw))
                   for j, rank, c0, ti, (b, x, kw) in spec.select(jobs, want_fine)]
        for a, b in zip(want_fine, fine):
            for f in a._fields:
                np.testing.assert_array_equal(getattr(a, f), getattr(b, f))
        assert [k[:4] for k in fu] == [k[:4] for k in want_fu]
        for a, b in zip(want_fu, fu):
            for f in a[4]._fields:
                np.testing.assert_array_equal(getattr(a[4], f), getattr(b[4], f))
        nfu += len(fu)
    assert getattr(plan, "followups_device", 0) >= 3, vars(plan).get("followup_unsupported")
    assert nfu > 0



@pytest.mark.parametrize("device", _device_followup_backends() or ["none"])
def test_batched_single_template_calls_own_their_results(device, monkeypatch):
    """Single-template calls batched by filter_series_many equal the same calls made one by
    one. A call whose window splits into bin-count groups defers its first group and may run
    a later one synchronously (a grouped flat call over more blocks than one batch); that
    result is held until the batch is built, so it must not be the plan's reused output
    buffers (_sbuf), which the next call of the same shape on the plan overwrites. The
    aliasing returned a later follow-up's peaks for an earlier one (the intermittent
    test_device_followups_equal_the_host_rule failure: the batch size there comes from a
    measured policy). Here a small batch budget forces the synchronous group every call."""
    if device == "none":
        pytest.skip("no GPU backend")
    monkeypatch.setenv("MF_GPU_ITEMS", "0")             # the per-call path, not the items batch
    monkeypatch.setenv("MF_VK_DEVICE_FOLLOWUPS", "0")
    rng, banks = _banks(monkeypatch, device, nbanks=1)
    bank = banks[0]
    g = bank._groups[0]
    plan = g.get_single_plan(0)
    if getattr(plan, "_gpu", None) is None:
        pytest.skip("single-template calls run on the host")
    # Four blocks per batch: a follow-up window's middle blocks (two window groups, one bin
    # count) exceed it and run synchronously; its edge blocks (other bin counts) defer.
    plan._series_batch_bytes = 4 * (8 * g.n + 4 + 12 * 64)
    S = 1 << 17
    rows = bank.empty_shared((2, S))
    for r in rows:
        r[:] = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
    # Windows whose layout is an edge block (its own bin count) then seven blocks of one bin
    # count over two window groups: the edge block defers, the seven run synchronously.
    from matchedfilter.time_domain import _normalize_windows
    centres = []
    for c0 in range(10000, S - 10000, 7):
        st, ws, we = TimeDomainFilterBank._window_layout(
            g, _normalize_windows(slice(c0 - 6000, c0 + 6000), S), S)
        bc = (we - ws + 60) // 61
        last = bc == bc.max()
        if (len(np.unique(bc)) == 2 and int(last.sum()) == 7
                and len(set(zip(ws[last].tolist(), we[last].tolist()))) == 2):
            centres.append(c0)
    assert len(centres) >= 8
    centres = centres[::max(1, len(centres) // 8)][:8]
    jobs = [(bank, rows[k % 2], dict(windows=slice(c0 - 6000, c0 + 6000), binsize=61,
                                     threshold=0.0, template_index=(5 * k) % 33))
            for k, c0 in enumerate(centres)]
    got = TimeDomainFilterBank.filter_series_many(jobs)
    for (b, x, kw), r in zip(jobs, got):
        want = b.filter_series(x, **kw)
        for f in want._fields:
            np.testing.assert_array_equal(getattr(want, f), getattr(r, f))
