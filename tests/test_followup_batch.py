"""Batched single-template calls (a search's follow-ups) on a GPU backend: each call's
FilterResults must be its own, equal to the same call made alone."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank


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
        # A hardware Vulkan device that runs a filter: enumeration alone also lists a software
        # rasteriser (lavapipe), whose device timers record nothing, and a driver that cannot
        # allocate (conftest.usable_gpu).
        import matchedfilter as mf
        from conftest import usable_gpu
        if (any(str(d) == "gpu:0" and d.backend == "vulkan" and not d.is_software
                for d in mf.devices()) and usable_gpu() is not None):
            out.append("gpu:0")
    except Exception:                                  # noqa: BLE001
        pass
    return out


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
    monkeypatch.setenv("MF_DEVICE_FOLLOWUPS", "0")
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
