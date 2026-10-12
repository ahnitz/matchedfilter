"""matchedfilter._roofline: work counted from the run, and sane peaks.

The bank below is pinned to n = 512 with 65-tap filters, so c_bad = 32 and n_valid = 448:
blocks start at k*448 and are valid over [k*448 + 32, k*448 + 480). A window [1000, 5000)
meets the blocks with k*448 + 480 > 1000 and k*448 + 32 < 5000, i.e. k = 2..11: 10 blocks,
and with 3 templates 30 (block, template) pairs.
"""
import math

import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank, _roofline

N, NT, BLOCKS = 512, 3, 10
WIN = slice(1000, 5000)


@pytest.fixture(scope="module")
def setup():
    rng = np.random.default_rng(0)
    taps = rng.standard_normal((NT, 65)).astype(np.float32)
    taps /= np.linalg.norm(taps, axis=1)[:, None]
    x = (rng.standard_normal(8192) + 1j * rng.standard_normal(8192)).astype(np.complex64)
    return taps, x


def test_geometry_is_the_hand_counted_one(setup):
    taps, _ = setup
    b = TimeDomainFilterBank(taps, engine="hier", threshold=4.0, fft_lengths=[N],
                             reference=np.ones(N, np.float32))
    (g,) = b._groups
    assert (g.n, g.c_bad, g.n_valid, len(g.template_indices)) == (N, 32, 448, NT)


@pytest.mark.parametrize("threshold", [4.0, 1e3])
def test_fine_counts_exact(setup, threshold):
    taps, x = setup
    b = TimeDomainFilterBank(taps, engine="hier", threshold=threshold, fft_lengths=[N],
                             reference=np.ones(N, np.float32))
    b.filter_series(x, windows=WIN)                  # builds the plan; not counted
    s0 = _roofline.snapshot([], [b])
    for _ in range(2):
        b.filter_series(x, windows=WIN)
    s1 = _roofline.snapshot([], [b])
    w = _roofline.Work()
    problems = []
    _roofline.fine_work(w, s0, s1, [b], "cpu", binsize=N, problems=problems)
    assert not problems
    st = w.stages
    assert st["forward"].count == 2 * BLOCKS
    assert st["forward"].flops == 2 * BLOCKS * 5 * N * math.log2(N)
    (c,) = s1["fine"].values()
    tiers = [k for k in st if k.startswith("tier")]
    assert len(tiers) == len(c["chain"])
    # Tier 0 (or the int16 screen in front of it, when it ran) sees every pair.
    b0 = c["chain"][0]
    first = st.get("q15 b%d" % b0, st[tiers[0]])
    assert first.count == 2 * BLOCKS * NT
    assert first.flops == 2 * BLOCKS * NT * (6 * b0 + 5 * b0 * math.log2(b0) + 3 * b0)
    if "q15 b%d" % b0 in st:
        assert st[tiers[0]].count <= first.count
    refined = st["refine n%d" % N].count if "refine n%d" % N in st else 0
    d = _roofline._sub(c, s0["fine"][next(iter(s0["fine"]))])
    assert refined == d["refined"] == d["passed"][-1]
    if threshold > 100:
        assert refined == 0
    else:
        assert refined > 0


def test_middle_counts_exact(setup):
    taps, x = setup
    m = TimeDomainFilterBank(taps, engine="corr", fft_lengths=[N])
    s0 = _roofline.snapshot([m], [])
    m.correlate_series(x, windows=WIN)
    s1 = _roofline.snapshot([m], [])
    (in1, c1), = s1["middle"].values()
    assert in1 == 4000
    assert c1[N] == dict(blocks=BLOCKS, pairs=BLOCKS * NT, out_samples=4000 * NT,
                         tmpl_values=NT * int(np.shape(m._groups[0].spectra)[1]))
    w = _roofline.Work()
    s = _roofline.middle_work(w, s0, s1, [m])
    assert s.count == BLOCKS * NT
    assert s.flops == BLOCKS * 5 * N * math.log2(N) + BLOCKS * NT * (6 * N + 5 * N * math.log2(N))


def test_followup_counts_exact(setup):
    taps, x = setup
    b = TimeDomainFilterBank(taps, engine="hier", threshold=4.0, fft_lengths=[N],
                             reference=np.ones(N, np.float32))
    w = _roofline.Work()
    s = _roofline.followup_work(w, [(b, x, dict(windows=WIN, binsize=64, threshold=0.0,
                                                template_index=1))])
    assert s.count == BLOCKS
    assert s.flops == BLOCKS * (5 * N * math.log2(N) + 6 * N + 5 * N * math.log2(N) + 3 * N)


def test_cpu_peaks_sane():
    pk = _roofline.peaks("cpu", measure_bandwidth=False)
    f = pk["flops"]
    assert 1e9 < f["fp32"] < 2e12                  # one core
    assert f["fp16"] >= f["fp32"] and f["int16"] >= f["fp32"]
    assert 0.5 < pk["clock_ghz"] < 7
    bw = _roofline.cpu_bandwidth(1 << 25, reps=2)
    assert 1e9 < bw < 1e12
    assert _roofline.cpu_tick_rate() > 1e8


def test_report_is_sum_of_maxima():
    w = _roofline.Work()
    w.stage("forward", "fp32", unit="blocks").add(1e9, 1e6, 10)     # compute bound
    w.stage("refine n512", "fp32").add(1e3, 1e9, 5)                  # memory bound
    pk = dict(flops=dict(fp32=1e12, fp16=2e12, int16=2e12), bandwidth=1e11)
    r = _roofline.report(w, pk, segments=2, wall_s=0.2)
    assert r["roofline_s"] == pytest.approx((1e9 / 1e12 + 1e9 / 1e11) / 2)
    assert r["fraction"] == pytest.approx(r["roofline_s"] / 0.1)
    assert r["dominant"] == "refine n512"
    assert [s["bound"] for s in r["stages"]] == ["compute", "memory"]


def test_x86_int16_peak_counts_multiply_pipes():
    """Haswell has one vector int16 multiply pipe, so its int16 peak is its fp32 peak, not
    twice it; Zen 2-5 and Skylake+ have two."""
    from matchedfilter import _roofline as r
    hsw = dict(flags="avx avx2 fma", vendor_id="GenuineIntel", model="63")
    hsw["cpu family"] = "6"
    width, fma, _, imul = r._x86_core(hsw)
    assert (width, fma, imul) == (256, 2, 1)
    assert (width // 16) * imul == (width // 32) * fma          # int16 rate == fp32 rate
    zen5 = {"flags": "avx avx2 fma avx512f", "vendor_id": "AuthenticAMD", "cpu family": "26",
            "model": "112"}
    assert r._x86_core(zen5)[3] == 2
    skx = {"flags": "avx avx2 fma avx512f", "vendor_id": "GenuineIntel", "cpu family": "6",
           "model": "85"}
    assert r._x86_core(skx)[3] == 2
