"""The middle stage's continuous correlation copies its output with streaming stores when the
call's output exceeds the last-level cache (src/matchfilt.c, 6b15bb83): the rule is the
footprint against the LLC size the OS reports, MF_CORR_NO_STREAM=1 turns it off. The two
must write the same bytes."""
import numpy as np
import pytest


def _llc_bytes():
    """The last-level cache size as src/matchfilt.c's llc_bytes reads it (sysfs index3, then
    index2), or 0."""
    for idx in (3, 2):
        try:
            txt = open("/sys/devices/system/cpu/cpu0/cache/index%d/size" % idx).read().strip()
        except OSError:
            continue
        mult = {"K": 1024, "M": 1024 * 1024}.get(txt[-1:], 1)
        return int(txt.rstrip("KM")) * mult
    return 0


def test_continuous_correlation_streaming_stores_are_bit_identical(monkeypatch):
    """A continuous correlation whose output exceeds the LLC copies it with streaming stores
    (6b15bb83); MF_CORR_NO_STREAM=1 keeps ordinary stores. The bytes written must be the
    same, including rows that start off a 16-byte boundary (odd lo)."""
    from matchedfilter import CorrelationFilter
    from matchedfilter._filter import _automatic_series_layout
    llc = _llc_bytes()
    if not llc or llc > (64 << 20):
        pytest.skip("LLC size unknown or too large for a quick test")
    n, nt, taps = 8192, 16, 2047
    valid = (taps // 2 + 1, n - taps // 2)          # odd lo: unaligned row starts
    span = valid[1] - valid[0]
    # Footprint 2.5x the LLC: past it whichever level the OS's sysconf reports (it can
    # count every slice; sysfs reports one).
    blocks = 5 * llc // (2 * nt * span * 8) + 1
    rng = np.random.default_rng(3)
    h = np.zeros((nt, n), np.complex64)
    h[:, :taps] = rng.standard_normal((nt, taps))
    L = (blocks + 1) * span + n
    ser = (rng.standard_normal(L) + 1j * rng.standard_normal(L)).astype(np.complex64)
    cf = CorrelationFilter(n, ndata=1, ntemplates=nt, valid=valid)
    cf.set_templates(np.fft.fft(h, axis=1).astype(np.complex64))
    lo, hi = cf.valid
    st, _, _ = _automatic_series_layout(L, cf.valid)
    assert nt * len(st) * (hi - lo) * 8 > llc
    ep = cf._execution_plan()
    out = {}
    for no_stream in (False, True):
        if no_stream:
            monkeypatch.setenv("MF_CORR_NO_STREAM", "1")
        else:
            monkeypatch.delenv("MF_CORR_NO_STREAM", raising=False)
        d = np.zeros((nt, L), np.complex64)
        ep.correlate_series_continuous(ser, st, lo, hi, 0, nt, d)
        out[no_stream] = d
    assert np.array_equal(out[False].view(np.uint32), out[True].view(np.uint32))


@pytest.mark.parametrize("real", [False, True])
def test_per_block_bounds_narrow_only_the_copy_out(real):
    """bounds (one [lo, hi) per block inside the valid span) writes exactly those samples of
    each block, bit-identical to the unbounded call there, and leaves every other sample as it
    was; a bound outside the valid span is refused."""
    from matchedfilter import CorrelationFilter
    from matchedfilter._filter import _automatic_series_layout
    n, nt, taps = 4096, 5, 301
    rng = np.random.default_rng(4)
    h = np.zeros((nt, n), np.complex64)
    h[:, :taps] = rng.standard_normal((nt, taps)) + 1j * rng.standard_normal((nt, taps))
    cf = CorrelationFilter(n, ndata=1, ntemplates=nt, valid=(taps // 2, n - taps // 2))
    cf.set_templates(np.fft.fft(h, axis=1).astype(np.complex64))
    lo, hi = cf.valid
    L = 9 * n
    ser = rng.standard_normal(L).astype(np.float32)
    if not real:
        ser = (ser + 1j * rng.standard_normal(L)).astype(np.complex64)
    st, _, _ = _automatic_series_layout(L, cf.valid)
    ep = cf._execution_plan()
    run = ep.correlate_series_continuous_real if real else ep.correlate_series_continuous
    full = np.zeros((nt, L), np.complex64)
    run(ser, st, lo, hi, 0, nt, full)
    bounds = np.empty((len(st), 2), np.uintp)
    bounds[:, 0], bounds[:, 1] = lo, hi
    bounds[0] = (lo + 37, hi)                     # a narrower start, an odd one
    bounds[-1] = (lo, lo + 1001)                  # a narrower end
    bounds[len(st) // 2] = (lo + 500, hi - 700)   # both
    sentinel = np.complex64(7 + 7j)
    got = np.full((nt, L), sentinel, np.complex64)
    run(ser, st, lo, hi, 0, nt, got, bounds)
    inside = np.zeros(L, bool)
    for s, (a, b) in zip(st, bounds):
        inside[int(s) + int(a):min(int(s) + int(b), L)] = True
    assert np.array_equal(got.view(np.uint32)[:, np.repeat(inside, 2)],
                          full.view(np.uint32)[:, np.repeat(inside, 2)])
    assert np.all(got[:, ~inside] == sentinel) and (~inside).any()
    bad = bounds.copy()
    bad[1] = (lo - 1, hi)
    with pytest.raises(RuntimeError):
        run(ser, st, lo, hi, 0, nt, got, bad)
