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
    if any("clock" in u for u in pk["unknown"]):
        # A core whose clock or pipes cannot be derived (an ARM core that is not a listed
        # Apple chip) has unknown peaks, and says so, rather than another chip's.
        assert all(math.isnan(v) for v in f.values()) and "unknown" in pk["formula"]
    else:
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
    # Zen 5 runs AVX-512 at full width except on the mobile Strix Point and Krackan Point.
    assert r._x86_core(zen5)[0] == 512
    assert r._x86_core(dict(zen5, model="36"))[0] == 256
    assert r._x86_core(dict(zen5, model="96"))[0] == 256
    skx = {"flags": "avx avx2 fma avx512f", "vendor_id": "GenuineIntel", "cpu family": "6",
           "model": "85"}
    assert r._x86_core(skx)[3] == 2


# ---- peaks from recorded device properties (no GPU needed) ----------------------------------

def _radv(name, pci="0000:c2:00.0", cus=(2, 2, 10, 2, 64)):
    """A stand-in for a Vulkan context with the properties RADV reported on the Radeon 8060S."""
    from types import SimpleNamespace
    exts = {b"VK_AMD_shader_core_properties", b"VK_EXT_pci_bus_info"}
    return SimpleNamespace(_device_extensions=lambda: exts,
                           _shader_core=lambda extensions=None: cus,
                           _pci_address=lambda extensions=None: pci), dict(
        device="gpu:0", name=name, backend="vulkan")


def _strix_sysfs(tmp_path):
    """The amdgpu IP discovery files and shader clock levels of the 8060S, under tmp_path."""
    base = tmp_path / "0000:c2:00.0"
    ip = base / "ip_discovery" / "die" / "0" / "11" / "0"
    ip.mkdir(parents=True)
    for f, v in (("major", 11), ("minor", 5), ("revision", 1)):
        (ip / f).write_text("%d\n" % v)
    (base / "pp_dpm_sclk").write_text("0: 600Mhz *\n1: 1100Mhz \n2: 2900Mhz \n")
    return str(tmp_path)


@pytest.mark.parametrize("name", ["AMD Radeon 8060S Graphics (RADV STRIX_HALO)",
                                  "AMD Radeon Graphics (RADV GFX1151)"])
def test_vulkan_peaks_do_not_depend_on_the_device_name(tmp_path, monkeypatch, name):
    """The architecture comes from the kernel's IP discovery for the device's PCI address, so
    RADV's newer marketing name gives the same peaks as its older gfx name: dual-issue fp32
    (40 CUs x 128 lanes x 2 x 2.9 GHz) and the 256-bit LPDDR5X-8000 bandwidth."""
    from matchedfilter import _peaks, _vkcompute
    root = _strix_sysfs(tmp_path)
    monkeypatch.setattr(_peaks, "amd_ip_arch",
                        lambda pci, _f=_peaks.amd_ip_arch: _f(pci, root=root))
    monkeypatch.setattr(_peaks, "_read", lambda p, _r=_peaks._read: _r(
        p.replace("/sys/bus/pci/devices", root)))
    ctx, out = _radv(name)
    pk = _vkcompute.Context._x_peaks(ctx, out)
    assert pk["arch"] == "gfx1151" and pk["arch_source"] == "amdgpu IP discovery"
    assert pk["flops"]["fp32"] == pytest.approx(40 * 128 * 2 * 2.9e9)
    assert pk["flops"]["fp16"] == pytest.approx(2 * pk["flops"]["fp32"])
    assert pk["bandwidth"] == pytest.approx(256e9)
    assert pk["unknown"] == []


def test_vulkan_peaks_unknown_without_architecture(monkeypatch):
    """With no IP discovery and no gfx name the architecture -- so the lanes per CU and the
    memory -- is unknown: the peaks are NaN with reasons, not RDNA 2 lanes and a NaN that the
    roofline then drops."""
    from matchedfilter import _peaks, _vkcompute
    monkeypatch.setattr(_peaks, "amd_ip_arch", lambda pci: None)
    monkeypatch.setattr(_peaks, "_read", lambda p: None)
    ctx, out = _radv("AMD Radeon 8060S Graphics (RADV STRIX_HALO)")
    pk = _vkcompute.Context._x_peaks(ctx, out)
    assert math.isnan(pk["flops"]["fp32"]) and math.isnan(pk["bandwidth"])
    assert any("architecture" in u for u in pk["unknown"])
    assert any("shader clock" in u for u in pk["unknown"])


def test_amd_arch_names():
    from matchedfilter import _peaks
    assert _peaks.amd_arch(11, 5, 1) == "gfx1151"
    assert _peaks.amd_arch(9, 0, 10) == "gfx90a"
    assert _peaks.max_clock_mhz("0: 600Mhz *\n2: 2900Mhz \n") == 2900
    assert _peaks.max_clock_mhz(None) is None


def test_unknown_bandwidth_never_silently_picks_the_compute_bound():
    """A NaN (or missing) peak makes the stage's roofline time NaN and its bound 'unknown';
    max(compute, NaN) would return the compute time and call the stage compute-only."""
    st = _roofline.Stage("tier0 b128", "fp16", flops=1e9, nbytes=1e9)
    pk = dict(flops=dict(fp32=1e12, fp16=2e12, int16=2e12), bandwidth=float("nan"),
              unknown=["memory bandwidth of gfx9999 (no entry)"])
    t, bound = st.roofline_s(pk)
    assert math.isnan(t) and bound == "unknown"
    # A stage with no bytes does not need the bandwidth.
    assert st.terms_s(dict(pk, bandwidth=None))[0] == pytest.approx(5e-4)
    assert _roofline.Stage("x", "fp32", flops=1e9).roofline_s(pk) == (pytest.approx(1e-3),
                                                                      "compute")
    w = _roofline.Work()
    w.stages["tier0 b128"] = st
    r = _roofline.report(w, pk, segments=1, wall_s=1.0)
    assert math.isnan(r["fraction"]) and r["dominant"] is None
    assert r["problems"] and r["problems"][0].startswith("ROOFLINE INCOMPLETE")
    assert "gfx9999" in r["problems"][0]
    assert "WARNING: ROOFLINE INCOMPLETE" in _roofline.format_report(r)


def test_cuda_peaks_need_a_listed_compute_capability():
    """L40S attributes give the stated formula; an unlisted compute capability is unknown
    rather than assumed to have 128 lanes per SM."""
    from matchedfilter import _peaks
    pk = _peaks.cuda_gpu_peaks(dict(name="NVIDIA L40S"), 142, 2520000, 9001000, 384, (8, 9))
    assert pk["flops"]["fp32"] == pytest.approx(142 * 128 * 2 * 2.52e9)
    assert pk["bandwidth"] == pytest.approx(2 * 9001e6 * 384 / 8)
    assert pk["unknown"] == []
    pk = _peaks.cuda_gpu_peaks(dict(name="future"), 100, 2000000, 0, 0, (11, 0))
    assert math.isnan(pk["flops"]["fp32"]) and math.isnan(pk["bandwidth"])
    assert len(pk["unknown"]) == 2


def test_apple_gpu_peaks_need_the_named_chip():
    """An Apple GPU's peaks come from its own generation; an unlisted chip is unknown rather
    than an M2, and a Pro/Max/Ultra part's bus (unlike the base chip's) is unknown."""
    from matchedfilter import _peaks
    pk = _peaks.apple_gpu_peaks(dict(name="Apple M2"), 10)
    assert pk["flops"]["fp32"] == pytest.approx(10 * 128 * 2 * 1.398e9)
    assert pk["bandwidth"] == pytest.approx(128 * 6400e6 / 8) and pk["unknown"] == []
    pk = _peaks.apple_gpu_peaks(dict(name="Apple M2 Pro"), 19)
    assert pk["flops"]["fp32"] == pytest.approx(19 * 128 * 2 * 1.398e9)
    assert math.isnan(pk["bandwidth"]) and pk["unknown"]
    pk = _peaks.apple_gpu_peaks(dict(name="Apple M9"), 12)
    assert math.isnan(pk["flops"]["fp32"]) and pk["unknown"]


def test_an_unlisted_arm_core_has_unknown_peaks_and_a_formula(monkeypatch):
    """cpu_peaks on an ARM core that is not a listed Apple chip (a Linux arm64 runner):
    the peaks are NaN, the unknown terms are named, and the formula is still a string."""
    monkeypatch.setattr(_roofline.platform, "machine", lambda: "aarch64")
    pk = _roofline.cpu_peaks(measure_bandwidth=False)
    assert all(math.isnan(v) for v in pk["flops"].values())
    assert any("clock and FMA pipes" in u for u in pk["unknown"])
    assert "unknown x 128-bit FMA pipes" in pk["formula"]
