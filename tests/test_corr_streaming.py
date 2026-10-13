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
    from matchedfilter import CorrelationFilter, _automatic_series_layout
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
