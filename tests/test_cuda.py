"""The NVIDIA CUDA PTX kernels and driver backend: generated, complete, and correct.

Checks both:
1. AOT PTX build output (presence of sm_75 kernels, warp shuffle/active intrinsics,
   no StructuredBuffer count padding).
2. Live hardware execution against CPU reference when an NVIDIA GPU is present.
"""
import ctypes
import gzip
import json
import pathlib
import pytest

import sim_driver
import numpy as np

import matchedfilter
from matchedfilter.device import Device
from matchedfilter import _cuda

#: The install's PTX, or on macOS (whose installs carry none) the checkout's.
PTX_DIR = pathlib.Path(matchedfilter.__file__).resolve().parent / "ptx"
if not PTX_DIR.is_dir():
    PTX_DIR = pathlib.Path(__file__).resolve().parents[1] / "python" / "matchedfilter" / "ptx"
MANIFEST = PTX_DIR / "manifest.json"

pytestmark = pytest.mark.skipif(not PTX_DIR.is_dir(),
                                reason="no PTX kernels in this install or a checkout beside it")


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST.read_text())


def _flat(manifest, n):
    """The module serving a length's flat filter: its own build, or the 32 KB staging build where
    its own would need more static shared memory than CUDA allows (tools/kernel_variants.py)."""
    kernels = manifest["kernels"]
    return (kernels.get("tierb_%d" % n) or kernels["tierb_%d_lds32" % n])["file"]


@pytest.fixture
def build_ptx(monkeypatch):
    """tools/kernel_variants.py of the checkout beside the tests (skips for an installed
    package)."""
    import importlib
    tools = pathlib.Path(__file__).resolve().parents[1] / "tools"
    if not (tools / "kernel_variants.py").is_file():
        pytest.skip("tools/ is not beside the tests (installed package?)")
    monkeypatch.syspath_prepend(str(tools))
    return importlib.import_module("kernel_variants")


def _read_ptx(path):
    raw = path.read_bytes()
    return (gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw).decode("utf-8")


def test_every_size_has_ptx(manifest, build_ptx):
    """Every supported transform size must have PTX blobs shipped."""
    for n in build_ptx.TIER_B:
        ptx = PTX_DIR / _flat(manifest, n)
        assert ptx.is_file(), f"{ptx} missing"
        assert len(_read_ptx(ptx)) > 1000, f"{ptx} looks empty"


def test_no_shipped_module_declares_more_static_shared_memory_than_cuda_allows(manifest, build_ptx):
    """CUDA allows a block 48 KB of static shared memory on every architecture and its JIT
    rejects a module past it, so such a module could launch on no NVIDIA GPU
    (build_ptx.STATIC_SHARED_MAX). The bytes are read from each module's .shared declarations,
    and the reading is checked against the staging the 32 KB builds were made with, so a parse
    that found nothing could not pass."""
    shared = {p.name: build_ptx.static_shared(_read_ptx(p))
              for p in sorted(PTX_DIR.glob("*.ptx.gz"))}
    portable = [rec for stem, rec in manifest["kernels"].items()
                if stem.startswith("tierb_") and stem.endswith("_lds32") and "_c16" not in stem]
    assert portable and all(shared[r["file"]] == build_ptx.lds_bytes(r["n"], build_ptx.PORTABLE_CAP)
                            for r in portable)
    over = {name: size for name, size in shared.items() if size > build_ptx.STATIC_SHARED_MAX}
    assert not over, "modules no NVIDIA GPU can launch: %s" % over


def test_every_kernel_the_host_asks_for_is_a_shipped_module(build_ptx, monkeypatch):
    """Context._x_kernel serves the flat, one-bin flat, refine, one-bin refine, follow-up,
    forward and full-correlation kernels at every length from a module that ships: its own
    build, or the _lds32 build where its own staging is past CUDA's static shared limit and
    so did not ship. A one-bin request gets a one-bin build wherever one is built (from 256).
    Needs no device: the module load is stubbed. A missing module fails here rather than
    skipping (conftest turns an UnsupportedSize into a skip).

    The host resolves against PTX_DIR, the PTX these tests check: a macOS install carries no
    ptx/ of its own, so there the installed host is checked against the checkout's PTX."""
    from matchedfilter import UnsupportedSize, _kernels
    from matchedfilter import _cudacompute as C
    monkeypatch.setattr(C, "_PTX_DIR", PTX_DIR)
    folder = _kernels.folder
    monkeypatch.setattr(_kernels, "folder", lambda b: PTX_DIR if b == "cuda" else folder(b))
    _kernels.clear()
    ctx = C.Context.__new__(C.Context)
    ctx._pipelines = {}
    ctx.props = sim_driver.stated_props(artifact_family="cuda", max_group_memory=48 * 1024,
                                        max_threads=1024, load_time_constants=False)
    ctx._load = lambda stem, path, fn_name, wg: (stem, path)
    role = {("fusedTierB", False): "peaks", ("fusedTierB", True): "peaks1",
            ("refineListed", False): "tier", ("refineListed", True): "tier1",
            ("refineItems", False): "items", ("seriesForward", False): "forward",
            ("fullCorrelation", False): "full", ("fullCorrelationSeries", False): "series"}
    served = {}
    for n in build_ptx.TIER_B:
        asks = [("fusedTierB", False), ("refineListed", False), ("refineListed", True),
                ("refineItems", False), ("seriesForward", False)]
        asks += [("fullCorrelation", False), ("fullCorrelationSeries", False)] if n >= 1024 else []
        asks += [("fusedTierB", True)] if n >= 4096 else []
        for entry, one_bin in asks:
            try:
                (stem, path) = ctx._x_kernel(role[(entry, one_bin)], n)[0]
            except UnsupportedSize as e:
                pytest.fail("n=%d %s one_bin=%s: %s" % (n, entry, one_bin, e))
            assert path.is_file() and path.name == stem + ".ptx.gz", (n, entry, stem)
            assert build_ptx.static_shared(_read_ptx(path)) <= build_ptx.STATIC_SHARED_MAX
            assert not one_bin or n < 256 or "_onebin" in stem, (n, entry, stem)
            served[(n, entry, one_bin)] = stem
    assert served[(8192, "fusedTierB", False)] == "tierb_8192_lds32"
    assert served[(65536, "refineListed", True)] == "refine_65536_onebin_lds32"
    assert ctx._x_has_kernel("items", 16384) and ctx._x_has_kernel("tier1", 16384)
    _kernels.clear()


@pytest.mark.parametrize("n", [1024, 4096, 16384])
def test_ptx_targets_sm75_and_64bit_pointers(manifest, n):
    """Verify PTX code declares .target sm_75 and 64-bit device pointers."""
    text = _read_ptx(PTX_DIR / _flat(manifest, n))
    assert ".target sm_75" in text or ".target sm_" in text
    assert ".address_size 64" in text
    # fusedTierB buffer params must be 8 bytes (.b8 ...[8]), not 16 bytes
    assert "fusedTierB_param_0[8]" in text
    assert "fusedTierB_param_1[8]" in text


def test_pack_and_compact_kernels_shipped(manifest):
    assert (PTX_DIR / "pack_coarse.ptx.gz").is_file()
    assert (PTX_DIR / "compact.ptx.gz").is_file()


def test_destroy_handles_nested_pending_timing_regions():
    import ctypes
    from types import SimpleNamespace
    from matchedfilter import _cudacompute as C

    destroyed = []
    e0, e1 = ctypes.c_void_p(0x101), ctypes.c_void_p(0x202)
    ctx = C.Context.__new__(C.Context)
    ctx.ctx = ctypes.c_void_p(0x1)
    ctx.device = ctypes.c_int(0)
    ctx._using_primary_ctx = False
    ctx._shared_modules = True
    ctx._modules = {}
    ctx._pipelines = {}
    ctx._pending_events = {1: [("hier", None, [("coarse", e0, e1)])]}
    ctx._event_pool = []
    ctx.streams = []
    ctx._inflight = {}
    ctx._exec_records = {}
    ctx._exec_lru = []
    ctx._exec_bytes = 0
    ctx._uploaded = {"data": {}, "tmpl": {}}
    ctx._cache_order = {}
    ctx.cuda = SimpleNamespace(
        cuCtxSetCurrent=lambda c: 0,
        cuCtxSynchronize=lambda: 0,
        cuEventDestroy_v2=lambda e: destroyed.append(e.value) or 0,
        cuStreamDestroy_v2=lambda s: 0,
        cuCtxDestroy_v2=lambda c: 0,
    )
    ctx.destroy()
    assert destroyed == [0x101, 0x202]
    assert not ctx.ctx.value


def test_a_submission_is_a_pending_write_exactly_when_asked():
    """_x_submit(pending=True) (a device root, a follow-up batch: unslotted runs other work
    depends on) registers a pending write, which settle_writes and other streams wait for;
    without it (a slot's leaf call) the run is waited for through the wait() it returns, as
    Vulkan's slot fence, and orders nothing else after it. Host-only: the launch is
    stubbed."""
    from matchedfilter import _cudacompute as C
    ctx = C.Context.__new__(C.Context)
    launched, pended, synced = [], [], []
    ctx._x_launch = lambda native, binds, slot, pre=(): launched.append(slot) or ("stream", slot)
    ctx._pend_write = lambda stream: pended.append(stream)
    ctx._sync = lambda stream=None: synced.append(stream)
    wait = ctx._x_submit(object(), {}, None, pending=True)
    assert pended == [("stream", None)] and not synced
    wait()
    assert synced == [("stream", None)]
    ctx._x_submit(object(), {}, 2)()
    assert launched == [None, 2] and pended == [("stream", None)]
    assert synced[-1] == ("stream", 2)


def test_launch_parameter_arrays_make_no_ctypes_array_types():
    """The ctypes arrays a launch passes (its parameter pointers, direct or recorded) and a
    recorded word update copies from are made from carray's types, made once: a ctypes array
    type is a reference cycle, so a type made per call left cyclic garbage for the collector
    on every call of a pycbc GPU job. Host-only: no device is touched."""
    import ctypes
    import gc
    from types import SimpleNamespace
    from matchedfilter import _cudacompute as C

    host = ctypes.create_string_buffer(4 * 41)
    slots = SimpleNamespace(take=lambda nbytes: (ctypes.addressof(host), nbytes))
    ctx = SimpleNamespace(_word_slots=lambda: slots)
    buf = SimpleNamespace(dptr=ctypes.c_void_p(0x10000), nbytes=4096)
    # lengths no other call path uses, so any array type of them is this test's
    params = [ctypes.c_uint32(i) for i in range(37)]
    gc.collect()
    gc.disable()
    try:
        gc.set_debug(gc.DEBUG_SAVEALL)
        for _ in range(3):
            C._param_ptrs(params)
            lst = C._CudaList(ctx, "test")
            lst.dispatch((ctypes.c_void_p(0x1), 64), 1, [buf] * 3, words=list(range(26)))
            lst.update(buf, list(range(41)))
            del lst
        gc.collect()
        kinds = {type(o).__name__ for o in gc.garbage}
    finally:
        gc.garbage.clear()
        gc.set_debug(0)
        gc.enable()
    assert "PyCArrayType" not in kinds, kinds


@pytest.mark.skipif(not _cuda.enumerate_devices()[0], reason="No NVIDIA CUDA GPU available on host")
def test_cuda_flat_filter_agrees_with_cpu():
    dev = Device.parse("cuda:0")
    assert dev.backend == "cuda"

    n = 1024
    np.random.seed(1234)
    data = (np.random.randn(2, n) + 1j * np.random.randn(2, n)).astype(np.complex64)
    tmpl = (np.random.randn(4, n) + 1j * np.random.randn(4, n)).astype(np.complex64)

    mf_cpu = matchedfilter.MatchedFilter(n, 2, 4, device="cpu")
    mf_cpu.set_data(data)
    mf_cpu.set_templates(tmpl)
    res_cpu = mf_cpu.run()

    mf_gpu = matchedfilter.MatchedFilter(n, 2, 4, device=dev)
    mf_gpu.set_data(data)
    mf_gpu.set_templates(tmpl)
    res_gpu = mf_gpu.run()

    np.testing.assert_array_equal(res_gpu["index"], res_cpu["index"])
    np.testing.assert_allclose(res_gpu["value"], res_cpu["value"], rtol=1e-4, atol=1e-4)


@pytest.mark.skipif(not _cuda.enumerate_devices()[0], reason="No NVIDIA CUDA GPU available on host")
def test_cuda_hierarchical_filter_agrees_with_cpu():
    dev = Device.parse("cuda:0")
    n = 4096
    np.random.seed(5678)
    data = (np.random.randn(2, n) + 1j * np.random.randn(2, n)).astype(np.complex64)
    tmpl = (np.random.randn(4, n) + 1j * np.random.randn(4, n)).astype(np.complex64)

    # Add strong injection to trigger survivor
    data[0, :] += 15.0 * tmpl[0, :]

    hf_cpu = matchedfilter.HierarchicalFilter(n, 2, 4, chain=512, device="cpu")
    hf_cpu.set_reference(np.ones(n, dtype=np.float32))
    hf_cpu.set_coarse_threshold(4.0)
    hf_cpu.set_data(data)
    hf_cpu.set_templates(tmpl)
    res_cpu = hf_cpu.run(threshold=6.0)

    hf_gpu = matchedfilter.HierarchicalFilter(n, 2, 4, chain=512, device=dev)
    hf_gpu.set_reference(np.ones(n, dtype=np.float32))
    hf_gpu.set_coarse_threshold(4.0)
    hf_gpu.set_data(data)
    hf_gpu.set_templates(tmpl)
    res_gpu = hf_gpu.run(threshold=6.0)

    np.testing.assert_array_equal(res_gpu["index"], res_cpu["index"])
    np.testing.assert_allclose(res_gpu["value"], res_cpu["value"], rtol=1e-3, atol=1e-3)


class _Driver:
    """A stand-in for the bound CUDA driver that reports one version."""

    def __init__(self, version, status=0):
        self.version, self.status = version, status

    def cuDriverGetVersion(self, ref):
        ref._obj.value = self.version
        return self.status


def test_a_kernel_is_offered_to_an_older_driver_at_the_version_it_reads(manifest):
    """A driver older than the toolkit that built the kernels refuses their PTX version
    (CUDA error 222). _ptx_for_driver lowers a module's .version line to the newest one the
    driver is sure to read, (M - 4).(m - 1) for CUDA M.m, and changes nothing else; it
    returns None for a driver that already reads the module, one before CUDA 11, or one
    whose version is unknown."""
    from matchedfilter._cudacompute import _ptx_for_driver
    ptx = gzip.decompress((PTX_DIR / _flat(manifest, 2048)).read_bytes())
    assert b"\n.version 8.7\n" in ptx
    older = _ptx_for_driver(ptx, _Driver(11060))
    assert older == ptx.replace(b"\n.version 8.7\n", b"\n.version 7.5\n", 1)
    for release, version in ((12000, b"8.0"), (12060, b"8.5")):
        assert _ptx_for_driver(ptx, _Driver(release)) == ptx.replace(
            b"\n.version 8.7\n", b"\n.version " + version + b"\n", 1)
    assert _ptx_for_driver(ptx, _Driver(12080)) is None      # reads 8.7
    assert _ptx_for_driver(ptx, _Driver(13020)) is None
    assert _ptx_for_driver(ptx, _Driver(10020)) is None
    assert _ptx_for_driver(ptx, _Driver(11060, status=1)) is None


def test_a_device_state_is_open_by_its_context_not_by_its_device_index():
    """A CUDA device state is open while its context is (a buffer made on it can then be
    freed), on device 0 as on any other: the device's index, a c_int that is false on the
    first device, says nothing about whether the device can still free a buffer."""
    from matchedfilter import _cudacompute
    handle = ctypes.c_void_p(0x1234)
    state = _cudacompute._DeviceShared(None, 0, handle)      # device 0, a context of its own
    assert state.open is True
    handle.value = None                                       # the context destroyed
    assert state.open is False
