"""The Q15 coarse screen (src/q15-inl.h): it may only reject pairs the float tier rejects."""
import numpy as np
import pytest

from matchedfilter import _core
import matchedfilter as mf
from matchedfilter.benchmark import _inspiral_power


def _screen_case(n, nd, nt, rng, snr=0.0):
    d = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    t = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    if snr:
        lag = rng.integers(0, n, nd)
        d += (snr * t[0] * np.exp(-2j * np.pi * np.outer(lag, np.arange(n)) / n)).astype(np.complex64)
    m = _core.MF(n, nd, nt)
    m.set_data_batch(0, d.view(np.float32).tobytes())
    m.set_template_batch(0, t.view(np.float32).tobytes())
    return m


@pytest.mark.parametrize("n", [64, 128, 256, 512, 1024])
def test_screen_never_rejects_a_float_pass(n):
    rng = np.random.default_rng(n)
    nd, nt = 8, 70                         # a partial last lane group
    m = _screen_case(n, nd, nt, rng, snr=6.0)
    if m.q15_lanes() == 0:
        pytest.skip("no Q15 screen on this back end")
    rows = nd * nt
    idx = np.zeros(rows, np.int64); val = np.zeros(rows, np.complex64)
    mag = np.zeros(rows, np.float32); cnt = np.zeros(rows, np.int32)
    ws, we = n // 8, n
    m.run(0, nd, 0, nt, we - ws, 0.0, ws, we, idx, val, mag, cnt)
    for q in (0.5, 0.9, 0.99):
        thr = float(np.quantile(mag, q))
        ps = np.zeros(rows, np.uint8); st = np.zeros(rows, np.float32)
        npass = m.q15_screen(0, nd, 0, nt, thr, ws, we, ps, st)
        assert npass == int(ps.sum())
        assert np.all(ps[mag >= thr] == 1)
        assert ps.sum() < rows                 # it does reject
        np.testing.assert_allclose(st, mag, rtol=0.02, atol=0.05)


def test_screen_subrange_rows():
    rng = np.random.default_rng(5)
    m = _screen_case(256, 4, 50, rng)
    if m.q15_lanes() == 0:
        pytest.skip("no Q15 screen on this back end")
    full = np.zeros(4 * 50, np.uint8); fs = np.zeros(4 * 50, np.float32)
    m.q15_screen(0, 4, 0, 50, 0.0, 0, 256, full, fs)
    part = np.zeros(2 * 21, np.uint8); ps = np.zeros(2 * 21, np.float32)
    m.q15_screen(1, 2, 13, 21, 0.0, 0, 256, part, ps)
    np.testing.assert_array_equal(ps.reshape(2, 21), fs.reshape(4, 50)[1:3, 13:34])


@pytest.mark.parametrize("chain", [(256,), (512,), (128, 512)])
def test_hierarchical_results_identical_with_screen(chain):
    n, nd, nt = 4096, 8, 40
    power = _inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)
    rng = np.random.default_rng(2026)
    tm = (h * np.exp(2j * np.pi * rng.random((nt, n)) * 0.05)).astype(np.complex64)
    data = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    data[0] += 9.0 * np.conj(tm[3]) / np.linalg.norm(tm[3]) * np.sqrt(n)
    out = []
    for q in (False, True):
        hf = mf.HierarchicalFilter(n, nd, nt, chain=chain, snr=5.5, fd=1e-3)
        hf.set_reference(power)
        hf.set_templates(np.conj(tm))
        hf.set_data(data)
        hf._ensure()
        assert hf._mf.set_q15(q) == q or not q
        if q and not hf._mf.q15_stats()[0]:
            pytest.skip("no Q15 screen for this band")
        res = hf.run(binsize=n // 4, threshold=4.0)
        out.append((res, hf.stats))
    np.testing.assert_array_equal(out[0][0]["index"], out[1][0]["index"])
    np.testing.assert_array_equal(out[0][0]["value"], out[1][0]["value"])
    assert out[0][1] == out[1][1]


def test_cost_model_prices_the_screen():
    cm = mf._gatechain.calibrate_costs(2048, 64)
    if not cm.screen:
        pytest.skip("no Q15 screen on this back end")
    for b, ent in cm.screen.items():
        assert ent["dense"] > 0 and ent["recheck"] > 0
        assert all(q >= f for f, q in ent["excess"])          # the screen passes a superset
        c, on = cm.first_tier(b, 0.01)
        assert on == (c < cm.dense[b])
    import json
    rt = mf._gatechain.CostModel.from_dict(json.loads(json.dumps(cm.to_dict())))
    assert rt.signature() == cm.signature()
