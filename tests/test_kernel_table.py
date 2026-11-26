"""The kernel-role table (_kernels.resolve): every driver resolves its kernels through it.

tests/data/kernel_resolution.json records, for every role and length the shipped manifests
hold and each backend's recorded device limits (CASES), the artifact the table resolves. It
was written from the table once the table was shown to resolve what the three drivers' own
copies did, on every (role, n, constants, limits), except where those copies disagreed or
named a build that did not ship or fit (each such case is "unsupported" now: the device
cannot run it, and it is reported instead of being replaced by another kernel). Needs no
device: it holds on every host.
"""
import json
import pathlib

import pytest

import sim_driver

from matchedfilter import _kernels
from matchedfilter._errors import UnsupportedSize

#: Recorded device limits: (backend, shared bytes, max threads).
CASES = {
    "vulkan-radeon": ("vulkan", 65536, 1024),       # Radeon 8060S (RADV): 64 KB, 1024
    "vulkan-32k": ("vulkan", 32768, 1024),          # a 32 KB Vulkan device
    "metal-apple": ("metal", 32768, 1024),          # Apple GPUs: 32 KB threadgroup memory
    "cuda-48k": ("cuda", 49152, 1024),              # CUDA static shared memory per block
}
LOAD_TIME_CONSTANTS = {"vulkan": True, "metal": True, "cuda": False}


def _limits(case):
    """The case's device properties (a DeviceProps of recorded values)."""
    fam, shared, threads = CASES[case]
    return sim_driver.stated_props(artifact_family=fam, max_group_memory=shared,
                                   max_threads=threads, load_time_constants=LOAD_TIME_CONSTANTS[fam])


def _calls(backend):
    """(role, n, consts) for every role at every length the backend's manifest holds."""
    kernels = _kernels.manifest(backend)["kernels"]
    ns = sorted({int(r["n"]) for s, r in kernels.items() if s.startswith("tierb_") and r.get("n")})
    out = []
    for n in ns:
        for role in ("peaks", "peaks1", "gate", "tier", "tier1", "refine", "refine1",
                     "tier1_c16", "items", "forward", "fwd_tier0", "fwd_bands", "fwd_listed",
                     "full", "series"):
            out.append((role, n, None))
        out.append(("tier1", n, {"gate": True}))
    for role in ("refine_td", "compact", "compactc", "compactl", "mark", "pack",
                 "compact_peaks"):
        out.append((role, 0, None))
    for n in sorted(int(k) for k in _kernels.manifest(backend).get("two_stage", {})):
        for role in ("tc1", "tc2", "tcs2", "tf1", "tf2", "root1", "root2"):
            out.append((role, n, None))
    coarse = set()
    for s, r in kernels.items():
        if "_c16" in s and s.startswith("tierb_") and not s.endswith("_lds32"):
            coarse.add((int(s.split("_")[1]), int(r.get("ppg", 1)), int(r.get("tile", 1))))
    for band, ppg, tile in sorted(coarse):
        for twt in (0, 1):
            out.append(("coarse", band, dict(ppg=ppg, tile=tile, twt=twt)))
    return out


def _new(case, role, n, consts):
    try:
        return _kernels.resolve(_limits(case), role, n, consts)["stem"]
    except UnsupportedSize:
        return "unsupported"


def test_every_shipped_role_resolves_as_recorded():
    """The table's resolution of every (role, n, constants) the manifests hold, under each
    recorded device's limits, as recorded (tests/data/kernel_resolution.json)."""
    want = json.loads((pathlib.Path(__file__).parent / "data" / "kernel_resolution.json")
                      .read_text())
    got = {}
    for case, (backend, _, _) in CASES.items():
        got[case] = {"%s|%d|%s" % (r, n, json.dumps(c, sort_keys=True)): _new(case, r, n, c)
                     for r, n, c in _calls(backend)}
    for case in CASES:
        diff = {k: (want[case].get(k), v) for k, v in got[case].items() if want[case].get(k) != v}
        assert not diff, "%s: %d differ, e.g. %s" % (case, len(diff), sorted(diff.items())[:5])
        assert set(want[case]) == set(got[case]), case


def test_a_role_the_device_cannot_run_is_reported_not_substituted():
    """A build past the device's workgroup memory with no 32 KB build, a gate-only build
    that did not ship, a length without the two-stage kernels: UnsupportedSize, never
    another kernel; an unknown role is a ValueError."""
    tiny = sim_driver.stated_props(artifact_family="vulkan", max_group_memory=1024)
    with pytest.raises(UnsupportedSize):
        _kernels.resolve(tiny, "peaks", 1024)
    with pytest.raises(UnsupportedSize):
        _kernels.resolve(_limits("vulkan-radeon"), "tier1", 1 << 20, {"gate": True})
    with pytest.raises(UnsupportedSize):
        _kernels.resolve(_limits("vulkan-radeon"), "tc1", 4096)
    with pytest.raises(ValueError):
        _kernels.resolve(_limits("vulkan-radeon"), "no-such-kernel", 1024)
    few = sim_driver.stated_props(artifact_family="vulkan", max_group_memory=65536, max_threads=32)
    with pytest.raises(UnsupportedSize):
        _kernels.resolve(few, "peaks", 4096)


def test_a_variant_that_is_its_own_artifact_follows_load_time_constants():
    """The coarse twiddle source is a load-time constant where the device sets one, else an
    artifact of its own (the "w" build)."""
    with_c = sim_driver.stated_props(artifact_family="cuda", max_group_memory=49152,
                                     load_time_constants=True)
    without = sim_driver.stated_props(artifact_family="cuda", max_group_memory=49152,
                                      load_time_constants=False)
    c = dict(ppg=2, tile=2, twt=1)
    assert _kernels.resolve(without, "coarse", 256, c)["stem"] == "tierb_256_c16p2t2w"
    assert _kernels.resolve(with_c, "coarse", 256, c)["stem"] == "tierb_256_c16p2t2"


def _fake_driver(case):
    """A driver Context of the case's backend with its limits and its loader replaced by one
    that reports the artifact it was handed (no device)."""
    import contextlib
    from matchedfilter import _vkcompute, _cudacompute, _mtlcompute
    fam, shared, threads = CASES[case]
    mod = {"vulkan": _vkcompute, "cuda": _cudacompute, "metal": _mtlcompute}[fam]
    f = object.__new__(type("Fake", (mod.Context,), {"__del__": lambda self: None}))
    f.max_shared_memory, f.max_invocations, f.name = shared, threads, case
    f.props = _limits(case)
    stem = lambda file: file.split(".")[0]
    if fam == "vulkan":
        f._build_pipeline = lambda key, filename, *a, **k: stem(filename)
        f._fit_subgroup = lambda n: 0
        return f, lambda out: out
    if fam == "cuda":
        f._kernel_function = lambda rec: (stem(rec["file"]), 0)
        return f, lambda out: out[0]
    f._pipeline = lambda rec, n, twt=False, macros=(): stem(rec["file"])
    f.o = type("O", (), {"autorelease_pool": staticmethod(contextlib.nullcontext)})()
    return f, lambda out: out[0]


@pytest.mark.parametrize("case", sorted(CASES))
def test_each_driver_loads_the_build_the_table_resolves(case):
    """A driver's _x_kernel hands its loader the table's build for every role (none keeps
    a mapping of its own): checked on each backend's driver without a device."""
    want = json.loads((pathlib.Path(__file__).parent / "data" / "kernel_resolution.json")
                      .read_text())[case]
    f, first = _fake_driver(case)
    for role, n, consts in _calls(CASES[case][0]):
        key = "%s|%d|%s" % (role, n, json.dumps(consts, sort_keys=True))
        try:
            got = first(f._x_kernel(role, n, consts))
        except UnsupportedSize:
            got = "unsupported"
        assert got == want[key], (case, key)


@pytest.mark.parametrize("case", sorted(CASES))
def test_each_driver_offers_the_coarse_layouts_it_offered(case):
    """_x_coarse_candidates, whose builds now come from the table (coarse_record), offers the
    layouts the drivers' own lookups did (tests/data/coarse_candidates.json, recorded from
    them; a Vulkan device requiring subgroups of 32 or 64, at most 16 per group)."""
    want = json.loads((pathlib.Path(__file__).parent / "data" / "coarse_candidates.json")
                      .read_text())[case]
    f, _ = _fake_driver(case)
    f.subgroup_range = (32, 64) if CASES[case][0] == "vulkan" else None
    f.max_workgroup_subgroups = 16
    for band, layouts in want.items():
        assert [list(c) for c in f._x_coarse_candidates(int(band))] == layouts, (case, band)


def test_the_roofline_reads_the_fp16_tier_from_the_drivers_artifact_family(monkeypatch):
    """_roofline's tier precision asks whether an fp16 coarse build shipped in the device's
    artifact family (the device's backend); it called a driver's _x_has_c16 on the class,
    which needs a device's properties now (every pycbc job's roofline accounting raised)."""
    from matchedfilter import _roofline, device
    monkeypatch.setattr(_roofline, "parse", lambda d: device.Device("gpu", 0, "fake", "vulkan"))
    assert _roofline.tier_precision("gpu:0", 0, 256) == "fp16"
    assert _roofline.tier_precision("gpu:0", 0, 65536) == "fp32"
    assert _roofline.tier_precision("gpu:0", 1, 256) == "fp32"
