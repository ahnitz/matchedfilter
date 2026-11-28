"""The tiled cascade of correlate_and_filter_many is a schedule of the step table
(_batches._cascade_steps, _core.HMFTable's ops): per time tile the middle correlation steps
into a scratch slot, the leaf slices that are ready, the copies to the output and the collars
carried. Its peaks are, to the bit and in order, the untiled schedule's in every retain mode;
its middle output is too wherever it is written whole; and with retain_radius > 0 the
executor writes the output exactly around the leaf peaks it found (a data-dependent copy)."""
import numpy as np
import pytest

from matchedfilter import _batches
from matchedfilter.time_domain import TimeDomainFilterBank

S = 1 << 16


def _banks():
    rng = np.random.default_rng(23)
    mid = np.zeros((4, 1201), np.float32)
    counts = np.array([701, 851, 1201, 951])
    for i, c in enumerate(counts):
        mid[i, :c] = rng.standard_normal(c) / np.sqrt(c)
    corr = TimeDomainFilterBank(mid, counts, engine="corr", device="cpu")
    lt = np.zeros((6, 300), np.complex64)
    for i in range(6):
        t = np.arange(200 + 15 * i) / 2048.0
        row = np.exp(2j * np.pi * (60 + 11 * i) * t) * np.hanning(t.size)
        lt[i, :t.size] = row / np.linalg.norm(row)
    leaf = TimeDomainFilterBank(lt, np.array([200 + 15 * i for i in range(6)]), engine="hier",
                                threshold=3.0, false_dismissal=1e-2, device="cpu")
    f = np.arange(16385) / 16.0
    leaf.set_reference(np.where((f >= 24) & (f <= 850), np.maximum(f, 1) ** (-7 / 3), 0), 1 / 16)
    pair = [rng.standard_normal(S).astype(np.float32) * 3 for _ in range(2)]
    return corr, leaf, pair


def _run(corr, leaf, pair, scaled, **kw):
    scales = np.array([0.5, -2.0, 1.25, 0.75], np.float32) if scaled else None
    outs = [np.zeros((3, S), np.complex64) for _ in pair]
    corr_jobs = [(corr, s, dict(windows=[(6000, 30000), (30300, S - 6000)],
                                templates=[0, 2, 3], scales=scales, out=o))
                 for s, o in zip(pair, outs)]
    leaf_jobs = [(leaf, o[r], dict(windows=[(9000, 29000), (36000, S - 9000)]))
                 for o in outs for r in range(3)]
    timings = {}
    res = TimeDomainFilterBank.correlate_and_filter_many(corr_jobs, leaf_jobs, timings=timings,
                                                         **kw)
    return outs, res, timings


def _same_results(a, b):
    assert sum(len(r.snr) for r in a) > 0
    for x, y in zip(a, b):
        for u, v in zip(x, y):
            assert u.dtype == v.dtype and u.tobytes() == v.tobytes()


@pytest.mark.parametrize("mode", ["written", "mirrored", "ephemeral", "retained", "auto"])
def test_the_tiled_schedule_gives_the_untiled_schedule(mode):
    corr, leaf, pair = _banks()
    kw = dict(written=dict(tile_bytes=1 << 18), mirrored=dict(tile_bytes=1 << 18),
              ephemeral=dict(tile_bytes=1 << 18, retain_radius=0),
              retained=dict(tile_bytes=1 << 18, retain_radius=700, retain_threshold=3.5),
              auto=dict())[mode]
    scaled = mode != "mirrored"
    outs_t, res_t, t_t = _run(corr, leaf, pair, scaled, **kw)
    outs_u, res_u, _ = _run(corr, leaf, pair, scaled, **dict(kw, tile_bytes=0))
    _same_results(res_t, res_u)
    if mode in ("written", "mirrored", "auto"):
        for a, b in zip(outs_t, outs_u):
            assert a.tobytes() == b.tobytes()
    elif mode == "ephemeral":
        assert t_t["ephemeral_used"] and not any(o.any() for o in outs_t)


def test_retained_output_is_written_around_the_peaks_the_executor_found():
    """With retain_radius R the output holds the untiled values at every sample within R of
    a leaf peak at or above the retain threshold on its row in any detector of the cohort, and nothing farther from every such peak
    than R and one leaf block (the slices' peaks the spans come from include those the window
    bins later merge away, which lie within a block of a kept one): the spans come from the
    peaks of the leaf slices run just before the copy."""
    corr, leaf, pair = _banks()
    R, thr = 500, 3.5
    outs_t, res_t, _ = _run(corr, leaf, pair, True, tile_bytes=1 << 18, retain_radius=R,
                            retain_threshold=thr)
    outs_u, res_u, _ = _run(corr, leaf, pair, True, tile_bytes=0)
    _same_results(res_t, res_u)
    checked, block = 0, int(leaf.max_block_length)
    for k, res in enumerate(res_t):
        d, row = divmod(k, 3)
        got, want = outs_t[d][row], outs_u[d][row]
        pos = np.concatenate([r.sample_indices[np.abs(r.snr) >= np.float32(thr)]
                              for r in (res_t[row], res_t[3 + row])])
        near, reach = np.zeros(S, bool), np.zeros(S, bool)
        for p in pos:
            near[max(0, p - R):min(S, p + R)] = True
            reach[max(0, p - R - block):min(S, p + R + block)] = True
        written = got != 0
        # every written sample is the untiled value and lies near a peak of this row
        assert np.array_equal(got[written], want[written])
        assert written.any() and not (written & ~reach).any()
        # the samples near a peak that the middle blocks wrote are written
        assert np.array_equal(got[near & (want != 0)], want[near & (want != 0)])
        checked += int(pos.size)
    assert checked > 0
