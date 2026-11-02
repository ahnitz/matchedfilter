"""GPU FP16 (`COARSE16`) listed Tier-1 gate (`refine_{64,128,256,512}_c16`) and FP16 `band1` tests.

Covers:
1. Shared `_gpuhier` recording plan for `half1 = True` (`b1 <= 512`) vs `half1 = False`
   (`b1 == 1024`) across `inplace`, `pack`, `tier0`, and `bands` feeds, `t1args` indirect
   workgroup count emission, gate-only vs coarse-lag election (`use_direct`), narrow
   subgroups (`sg = 8`), and shifted active bands (`k0 > 0`).
2. Shipped CUDA PTX entry parameter layout, packed `f16x2` arithmetic emission, warp-local
   barriers, and zero shared-memory staging (`lds_bytes == 0`) on CUDA and Metal.
3. Offline Metal stem, entry-point, macro, and manifest resolution for `tier1_c16`.
4. Live GPU execution on all enumerable Vulkan devices (including RADV `sg=64` and
   `llvmpipe` `sg=8`) across all four feeds, odd/zero/single survivor counts, FP16 overflow
   fail-open, `hier_peaks_grouped` per-row windows, shifted active bands (`band_offsets`),
   Tier-0 coarse centroid clustering (`tier0_cluster`), and direct time-domain refinement
   (`use_direct = True`).
"""
import ctypes
import json
import re
import struct

import numpy as np
import pytest
from conftest import (
    forced_coarse_layouts,
    gpu_backend,
    gpu_context,
    kernel_dir,
    usable_gpu,
    usable_gpu_reason,
)
from test_gpu_hier_plan import Driver, _names, _words
from test_gpu_tier0_feed import _ptx_entry_params, _read_ptx, _StubBuf, _stub_cuda_context

import matchedfilter as mf
from matchedfilter import _cudacompute, _gpuhier, _mtlcompute
from matchedfilter.time_domain import template_spectra


class _Tier1C16Driver(Driver):
    """Recording-only driver with `c16` and `tier1_c16` enabled for bands <= 512."""

    def __init__(self, inplace_feed=True, subgroup_size=32, fwd_tier0=True):
        super().__init__(inplace_feed=inplace_feed, c16=True, one_bin=True)
        self.subgroup_size = subgroup_size
        self.fwd_tier0 = fwd_tier0

    def _x_has_c16(self, band):
        return band <= 16384

    def _x_has_kernel(self, name, n):
        if name == "tier1_c16":
            return n in (64, 128, 256, 512)
        if name == "fwd_tier0":
            return self.fwd_tier0
        if name == "refine_td":
            return n <= 65536
        return True


def _enumerated_gpu_specs():
    """Return `[(dev_str, label), ...]` for every usable GPU device on this host."""
    specs = []
    try:
        from matchedfilter import _vkcompute, _vulkan
        devs, _ = _vulkan.enumerate_devices()
        for idx, info in enumerate(devs or ()):
            try:
                c = _vkcompute.Context(idx)
                name = getattr(c, "device_name", "") or str(info)
                sg = getattr(c, "subgroup_size", 0)
                c.destroy()
                specs.append(("vulkan:%d" % idx, "vk%d_%s_sg%d" % (idx, name.split()[0], sg)))
            except Exception:
                continue
    except Exception:
        pass
    if specs:
        return specs
    dev = usable_gpu()
    if dev is not None:
        return [(dev, dev)]
    return []


_GPU_SPECS = _enumerated_gpu_specs()


@pytest.fixture(scope="module", params=_GPU_SPECS or [("none", "none")],
                ids=[s[1] for s in _GPU_SPECS] or ["no_gpu"])
def gpu_dev_module(request):
    """Open and yield `(dev_spec, low_level_ctx)` once per module for each GPU device."""
    spec, _ = request.param
    if spec == "none":
        pytest.skip(usable_gpu_reason() or "no usable GPU")
    if spec.startswith("vulkan:"):
        from matchedfilter import _vkcompute
        idx = int(spec.split(":")[1])
        ctx = _vkcompute.Context(idx)
        try:
            yield ("gpu:%d" % idx, ctx)
        finally:
            ctx.destroy()
    else:
        ctx = gpu_context(gpu_backend())
        try:
            yield (spec, ctx)
        finally:
            ctx.destroy()


@pytest.fixture
def gpu_dev(gpu_dev_module, monkeypatch):
    """Provide `(dev_spec, ctx)` and pin coarse layouts on software Vulkan adapters."""
    dev_str, ctx = gpu_dev_module
    dev_name = (getattr(ctx, "device_name", "") or "").lower()
    if "llvmpipe" in dev_name or "lavapipe" in dev_name:
        forced = forced_coarse_layouts(ctx, (64, 128, 256, 512, 1024), lambda f: f[2] <= 2)
        if forced:
            monkeypatch.setenv("MF_COARSE_LAYOUT", forced)
        from matchedfilter import _calibration
        orig_cal = _calibration.calibrate_costs_gpu
        monkeypatch.setattr(
            _calibration, "calibrate_costs_gpu",
            lambda n, device, blocks=64, reps=2, seed=11, nt=32:
                orig_cal(n, device, blocks=blocks, reps=reps, seed=seed, nt=nt))
    return dev_str, ctx


@pytest.mark.parametrize("b1,want_half1,want_shift", [
    (64, True, 5),
    (128, True, 4),
    (256, True, 3),
    (512, True, 2),
    (1024, False, 0),
])
@pytest.mark.parametrize("inplace", [True, False])
def test_plan_tier1_fp16_feeds_binds_and_slots(b1, want_half1, want_shift, inplace):
    """Verify `_gpuhier` buffer sizing, `t1args`, `packShift`, `scale1`, and slot pruning."""
    n, nd, nt = 2048, 6, 10
    if b1 == 64:
        # Test standalone _hier_record/_hier_binds for b1=64 and cascade (64, 128) via hier_peaks.
        b0, b1_eff, want_shift_eff = 64, 128, 4
    else:
        b0, b1_eff, want_shift_eff = 64, b1, want_shift
    ctx = _Tier1C16Driver(inplace_feed=inplace, subgroup_size=32)
    rng = np.random.default_rng(7)
    d = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    ct0 = h[:, :b0].copy()
    ct1 = h[:, :b1_eff].copy()
    hout = []
    ctx.hier_peaks(n, b1_eff, d, h, ct0, 0.35, cascade_band=b0, ct1=ct1, raw_thr1=0.85,
                   threshold=5.0, handle_out=hout)
    (ops, binds, _, _), = ctx.runs
    rec = hout[0].rec
    et1 = _gpuhier.c16_template_exp(ct1)
    ed1 = _gpuhier.c16_data_exp(b1_eff, 0.85, et1)

    if b1 == 64:
        # Directly verify b1=64 packShift == 5 (2 * PPG = 32 pairs/WG).
        tiers_64 = ((32, h[:, :32], 0.35), (64, h[:, :64], 0.85))
        b64 = ctx._hier_binds(n, tiers_64, nd, nt, 1, 0, n, n, 11, 25.0, True, 0, 0, False,
                              (32, 4, 2, True), None, d, half1=True, ed1=0, et1=0)
        assert b64["compact0"][-1] == 5

    if want_half1:
        # Tier-1 templates are packed half2 uint32 words (4 bytes/bin).
        assert rec.buffers["ct1"].nbytes == nt * b1_eff * 4
        assert rec.buffers["ct1"].value.dtype == np.uint32
        assert ("listed", "tier1_c16") in _names(ops)
        tier_op = next(op for op in ops if op[0] == "listed" and op[1][0] == "tier1_c16")
        assert tier_op[4] == ("section", rec.buffers["counts"], 16, 16)
        assert binds["compact0"][-1] == want_shift_eff
        # Gate-only mode when WG <= subgroup_size and not use_direct (_played "gateway" == "gate").
        assert binds["tier"][5] == 0 and binds["tier"][6] != 0
        ctx._kernel_pair = lambda what, band: (("gate", "elect") if what == "gateway"
                                               else (((32, 2, 1, False), None)))
        assert ("gateway", b1_eff, ("gate", "elect")) in ctx._call_slots(
            (b0, b1_eff), True, False, use_direct=False, half1=True)
        assert all(s[0] != "gateway" for s in ctx._call_slots(
            (b0, b1_eff), True, False, use_direct=True, half1=True))
        if inplace:
            assert dict(tier_op[1][2])["stride"] == n
            assert dict(tier_op[1][2])["scale"] == ed1
        else:
            assert rec.buffers["band1"].nbytes == nd * b1_eff * 4
            packs = [op for op in ops if op[0] == "dispatch" and op[1][0] == "pack"]
            assert len(packs) == 2
            assert packs[1][3][3] == 1 and packs[1][3][4] == _gpuhier._bits(2.0 ** ed1)
            assert dict(tier_op[1][2])["stride"] == 0 and dict(tier_op[1][2])["scale"] == 0
    else:
        assert rec.buffers["ct1"].nbytes == nt * b1_eff * 8
        assert ("listed", "tier1_c16") not in _names(ops)
        assert "t1args" not in rec.buffers
        assert binds["compact0"][-1] == 0
        if not inplace:
            assert rec.buffers["band1"].nbytes == nd * b1_eff * 8


def test_plan_tier1_fp16_narrow_subgroup_and_tier0_feed():
    """Verify narrow subgroup (`sg = 8`) falls back to `peakLane` (`gate_bits1 == 0`) at `b1 >= 256`
    and `forward_tier0` receives `scaleBits1 != 0` for `b1 <= 512` vs `0` for `b1 == 1024`."""
    n, nd, nt = 2048, 4, 8
    d = np.ones((nd, n), np.complex64)
    h = np.ones((nt, n), np.complex64)

    # Narrow subgroup sg=8: b1=128 has WG=8 <= 8 (gate_bits1 != 0), b1=256 has WG=16 > 8 (0).
    ctx_sg8 = _Tier1C16Driver(inplace_feed=True, subgroup_size=8)
    ctx_sg8.hier_peaks(n, 128, d, h, h[:, :64], 0.3, cascade_band=64, ct1=h[:, :128], raw_thr1=0.8)
    ctx_sg8.hier_peaks(n, 256, d, h, h[:, :64], 0.3, cascade_band=64, ct1=h[:, :256], raw_thr1=0.8)
    binds_128 = ctx_sg8.runs[0][1]
    binds_256 = ctx_sg8.runs[1][1]
    assert binds_128["tier"][5] == 0 and binds_128["tier"][6] != 0
    assert binds_256["tier"][5] == 1 and binds_256["tier"][6] == 0

    # Deferred forward claim (`feed == "tier0"`): 8-word uniform with scaleBits1 != 0 vs 0.
    ctx_t0 = _Tier1C16Driver(inplace_feed=True, subgroup_size=32)
    series = _Tier1C16Driver._x_alloc(ctx_t0, (nd + 1) * n * 8)
    starts = _Tier1C16Driver._x_alloc(ctx_t0, nd * 4)
    claim = (series, starts, n, nd, (nd + 1) * n, 0)
    tiers_512 = ((128, h[:, :128], 0.3), (512, h[:, :512], 0.8))
    tiers_1024 = ((256, h[:, :256], 0.3), (1024, h[:, :1024], 0.8))
    et1 = _gpuhier.c16_template_exp(h[:, :512])
    ed1 = _gpuhier.c16_data_exp(512, 0.8, et1)

    rec_512 = ctx_t0._hier_record(
        ("t0", 512), n, tiers_512, nd, nt, 1, (32, 4, 2, True), True, "tier0", "dense", None,
        0, d, h, d, h, claim, (64, 96), use_direct=True, half1=True, ed1=ed1)
    assert rec_512.buffers["band1"].nbytes == nd * 512 * 4
    taps_stub = (series, 32, 0, 4, 4096)
    binds_512 = ctx_t0._hier_binds(
        n, tiers_512, nd, nt, 1, 0, n, n, 11, 25.0, True, 0, 0, False, (32, 4, 2, True),
        claim, d, (64, 96), direct=taps_stub, half1=True, ed1=ed1, et1=et1)
    assert len(binds_512["tier0"]) == 8
    assert binds_512["tier0"][4] == _gpuhier._bits(2.0 ** ed1)
    assert binds_512["tier0"][5:7] == (64, 96)
    # Direct refine requires elected coarse lag: nbins=1 and gate_bits1=0.
    assert binds_512["tier"][5] == 1 and binds_512["tier"][6] == 0

    rec_1024 = ctx_t0._hier_record(
        ("t0", 1024), n, tiers_1024, nd, nt, 1, (32, 4, 2, True), True, "tier0", "dense", None,
        0, d, h, d, h, claim, (64, 96), half1=False, ed1=0)
    assert rec_1024.buffers["band1"].nbytes == nd * 1024 * 8
    binds_1024 = ctx_t0._hier_binds(
        n, tiers_1024, nd, nt, 1, 0, n, n, 11, 25.0, True, 0, 0, False, (32, 4, 2, True),
        claim, d, (64, 96), half1=False, ed1=0, et1=0)
    assert binds_1024["tier0"][4] == 0
    assert _words(binds_512, rec_512.native[1])[0] == binds_512["tier0"]


def test_cuda_ptx_tier1_fp16_abi_and_codegen(monkeypatch):
    """Verify shipped CUDA PTX `refine_{64,128,256,512}_c16` codegen and entry parameter ABI."""
    ctx, ptx_dir = _stub_cuda_context(monkeypatch)
    try:
        manifest = json.loads((ptx_dir / "manifest.json").read_text())["kernels"]
        for band in (64, 128, 256, 512):
            stem = "refine_%d_c16" % band
            assert stem in manifest
            rec_m = manifest[stem]
            assert rec_m["coarse16"] == 1
            assert rec_m["local_size"] == [64, 1, 1]
            assert rec_m["lds_bytes"] == 0
            txt = _read_ptx(ptx_dir, stem)
            assert "mul.f16x2" in txt and "add.f16x2" in txt, (
                "%s missing packed f16x2 arithmetic instructions" % stem)
            # WG <= 32 == warpSize on CUDA: pure shfl.sync.bfly.b32 exchange & reduction, 0 barriers.
            assert "shfl.sync.bfly.b32" in txt and not re.search(r"\bbar\.", txt), (
                "%s expected pure warp-shuffle execution with zero barriers" % stem)
            local_bytes = sum(int(m.group(1)) for m in re.finditer(
                r"\.local\s+\.align\s+\d+\s+\.b8\s+\w+\[(\d+)\];", txt))
            assert local_bytes <= 28, "%s unexpected .local spill: %d" % (stem, local_bytes)

        n, nd, nt, nc = 2048, 6, 12, 4
        rng = np.random.default_rng(303)
        ct0_cl = (rng.standard_normal((nc, 128)) + 1j * rng.standard_normal((nc, 128))).astype(
            np.complex64)
        ct0_un = (rng.standard_normal((nt, 128)) + 1j * rng.standard_normal((nt, 128))).astype(
            np.complex64)
        ct1 = (rng.standard_normal((nt, 512)) + 1j * rng.standard_normal((nt, 512))).astype(
            np.complex64)
        cl_off = np.array([0, 3, 6, 9, 12], dtype=np.uint32)
        cl_mem = np.arange(nt, dtype=np.uint32)
        cl_meta = (nc, cl_off, cl_mem, 1, "cl_sig")

        et0 = _gpuhier.c16_template_exp(ct0_un)
        ed0 = _gpuhier.c16_data_exp(128, 3.5, et0)
        et1 = _gpuhier.c16_template_exp(ct1)
        ed1 = _gpuhier.c16_data_exp(512, 4.5, et1)
        layout = (32, 4, 2, True)
        bd = _StubBuf(0x9000000, nd * n * 8)
        bt = _StubBuf(0x9100000, nt * n * 8)
        series = _StubBuf(0x9200000, (nd + 2) * n * 8)
        starts = _StubBuf(0x9300000, nd * 4)
        taps_buf = _StubBuf(0x9400000, nt * 128 * 4)
        data_arr = np.zeros((nd, n), np.complex64)
        tmpl_arr = np.zeros((nt, n), np.complex64)
        rw_arr = np.tile(np.array([0, n, 0], dtype=np.uint32), (nd, 1))

        for feed in ("inplace", "tier0", "bands", "pack"):
            for use_cl in (False, True):
                for use_direct in (False, True):
                    for use_rw in (False, True):
                        if use_direct and feed in ("inplace", "pack"):
                            continue
                        monkeypatch.setattr(ctx, "inplace_feed", feed != "pack")
                        claim = (None if feed in ("inplace", "pack")
                                 else (series, starts, n, nd, (nd + 2) * n, 0))
                        tiers = ((128, ct0_cl if use_cl else ct0_un, 3.5), (512, ct1, 4.5))
                        direct_arg = (taps_buf, 64, 0, 4, 8192) if use_direct else None
                        rec = ctx._hier_record(
                            ("c16_t1", feed, use_cl, use_direct, use_rw), n, tiers, nd, nt, 1,
                            layout, True, feed, "dense", rw_arr if use_rw else None,
                            ed0, bd, bt, data_arr, tmpl_arr, claim,
                            use_direct=use_direct, cl_meta=cl_meta if use_cl else None,
                            half1=True, ed1=ed1)
                        binds = ctx._hier_binds(
                            n, tiers, nd, nt, 1, 0, n, n, 11, 25.0, True, ed0, et0, use_rw,
                            layout, claim, data_arr, direct=direct_arg,
                            cl_meta=cl_meta if use_cl else None, half1=True, ed1=ed1, et1=et1)
                        for block, at, fn_name, off in rec.native.args:
                            if off < 0:
                                _cudacompute._pack_words(-off)(block, at, *binds[fn_name])
                            else:
                                _cudacompute._PACK_U64(block, at, binds[fn_name].dptr.value + off)

                        launched = [op for op in rec.native.ops if op[0] == "launch"]
                        stems = [op[1][0] for op in launched]
                        assert "refine_512_c16" in stems
                        for op in launched:
                            stem, _, entry = op[1]
                            block, ptrs = op[4], op[5]
                            ptx_params = _ptx_entry_params(_read_ptx(ptx_dir, stem), entry)
                            assert len(ptrs) == len(ptx_params), (
                                "%s (%s): host packed %d params, PTX expects %d"
                                % (stem, entry, len(ptrs), len(ptx_params)))
                            buf_base = ctypes.addressof(block)
                            for idx, (align, size) in enumerate(ptx_params):
                                off = int(ptrs[idx]) - buf_base
                                assert off % align == 0 and 0 <= off and off + size <= len(block)

                        t1_op = next(op for op in launched if op[1][0] == "refine_512_c16")
                        t1_tail = struct.unpack_from("<II", t1_op[4], len(t1_op[4]) - 8)
                        if feed == "inplace":
                            assert t1_tail == (n, _gpuhier._bits(2.0 ** ed1))
                        elif feed == "bands":
                            assert t1_tail == (512, _gpuhier._bits(2.0 ** ed1))
                        else:
                            assert t1_tail == (0, 0x3F800000)
    finally:
        from matchedfilter import _kernels
        _kernels.clear()


def test_metal_tier1_fp16_resolution_and_manifest():
    """Verify Metal offline manifest and `Context` resolution for `tier1_c16`."""
    metal_dir = kernel_dir("metal")
    manifest = json.loads((metal_dir / "manifest.json").read_text())["kernels"]

    ctx = _mtlcompute.Context.__new__(_mtlcompute.Context)
    ctx.max_shared_memory = 32768
    ctx.name = "Apple M2"
    assert ctx.packed_fp16 is False

    assert _mtlcompute._twt_entry("refineListedC16w") == ("refineListedC16", True)
    assert _mtlcompute._twt_entry("refineListedC16") == ("refineListedC16", False)
    assert ("MF_ROW_WINDOWS", 1) in ctx._macros({"rowwin": True, "stride": 2048, "scale": 2})

    for band in (64, 128, 256, 512):
        assert ctx._x_has_kernel("tier1_c16", band)
        for entry in ("refineListedC16", "refineListedC16w"):
            assert _mtlcompute._function(entry) == "refineListedBounded"
            base, _ = _mtlcompute._twt_entry(entry)
            stem = ctx._stem(band, base)
            assert stem == "refine_%d_c16" % band
            assert stem in manifest
            rec_m = manifest[stem]
            assert rec_m["coarse16"] == 1
            assert rec_m["lds_bytes"] == 0
            assert rec_m["local_size"] == [64, 1, 1]
            src = (metal_dir / rec_m["file"]).read_text()
            assert "simd_shuffle_xor" in src
    assert not ctx._x_has_kernel("tier1_c16", 1024)


@pytest.mark.parametrize("chain", [(64, 128), (64, 256), (128, 512), (256, 512), (256, 1024)])
@pytest.mark.parametrize("feed_mode", ["tier0", "inplace", "pack", "bands"])
def test_gpu_tier1_fp16_chains_and_feeds(gpu_dev, chain, feed_mode, monkeypatch):
    """Verify live GPU parity across all 4 feeds and 2-tier chains (including 1024 fallback)."""
    _, ctx = gpu_dev
    b0, b1 = chain
    n, nd, nt = 2048, 6, 14
    if not ctx._x_has_c16(b0):
        pytest.skip("band %d has no fp16 coarse tier" % b0)
    rng = np.random.default_rng(1100 + b0 + b1)
    tmpl = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    tmpl /= np.linalg.norm(tmpl, axis=1, keepdims=True)

    # Synthesize time-series blocks with injected matched templates so forward feeds work too.
    series = ctx.empty_shared(((nd + 1) * n,), dtype=np.complex64)
    raw_td = ((rng.standard_normal(series.size) + 1j * rng.standard_normal(series.size)) * 0.04
              ).astype(np.complex64)
    injections = [(0, 2, 320, 16.0), (2, 7, 940, 15.5), (5, 13, 1610, 17.0)]
    for d_idx, t_idx, lag, amp in injections:
        td_sig = (np.fft.ifft(tmpl[t_idx]) * n).astype(np.complex64)
        raw_td[d_idx * n:(d_idx + 1) * n] += amp * np.roll(td_sig, lag)
    series[:] = raw_td
    starts = np.arange(nd, dtype=np.uint32) * n

    spec_ref = ctx.empty_shared((nd, n))
    ctx.forward(n, series, starts, spec_ref, defer=False)
    ref_i, ref_v = ctx.peaks(n, spec_ref, tmpl, binsize=512, threshold=7.5)

    # Configure the requested feed mode cleanly.
    if feed_mode in ("tier0", "bands"):
        if feed_mode == "bands":
            if not ctx.inplace_feed:
                pytest.skip("bands feed requires inplace_feed")
            monkeypatch.setitem(
                ctx.__dict__.setdefault("_shipped_memo", {}), ("fwd_tier0", n), False)
        monkeypatch.setitem(ctx.__dict__, "feed_forced", True)
        spec_shared = ctx.empty_shared((nd, n))
        ctx.forward(n, series, starts, spec_shared, defer=True)
        hout = []
        got_i, got_v = ctx.hier_peaks(
            n, b1, spec_shared, tmpl, tmpl[:, :b0], 0.3, binsize=512, threshold=7.5,
            cascade_band=b0, ct1=tmpl[:, :b1], raw_thr1=0.5, handle_out=hout)
        assert hout[0].key[8] == feed_mode
    else:
        if feed_mode == "inplace" and not ctx.inplace_feed:
            pytest.skip("device does not support inplace_feed")
        monkeypatch.setattr(ctx, "inplace_feed", feed_mode == "inplace")
        spec_np = np.asarray(spec_ref).copy()
        hout = []
        got_i, got_v = ctx.hier_peaks(
            n, b1, spec_np, tmpl, tmpl[:, :b0], 0.3, binsize=512, threshold=7.5,
            cascade_band=b0, ct1=tmpl[:, :b1], raw_thr1=0.5, handle_out=hout)
        assert hout[0].key[8] == feed_mode

    assert ("t1args" in hout[0].rec.buffers) == (b1 <= 512 and ctx.packed_fp16)
    hits = ref_i >= 0
    assert int(hits.sum()) >= 3
    np.testing.assert_array_equal(got_i[hits], ref_i[hits])
    np.testing.assert_allclose(got_v[hits], ref_v[hits], rtol=2e-4, atol=2e-4)


@pytest.mark.parametrize("chain", [(64, 256), (128, 512)])
def test_gpu_tier1_fp16_survivor_counts_and_overflow(gpu_dev, chain, monkeypatch):
    """Verify exact 0, 1, 3, 5, and 7 survivor counts (`NOPAIR` odd lanes) and FP16 overflow."""
    _, ctx = gpu_dev
    monkeypatch.setattr(ctx, "packed_fp16", True)
    b0, b1 = chain
    n, nd, nt = 2048, 4, 8
    rng = np.random.default_rng(2200 + b1)
    # Build orthogonal multi-bin templates inside [2, 50) (< 64) so each injection has a sharp lag.
    tmpl = np.zeros((nt, n), dtype=np.complex64)
    for t in range(nt):
        lo_k, hi_k = 2 + 6 * t, 2 + 6 * (t + 1)
        phases = np.exp(2j * np.pi * rng.random(hi_k - lo_k))
        tmpl[t, lo_k:hi_k] = (phases / np.linalg.norm(phases)).astype(np.complex64)

    k = np.arange(n, dtype=np.float32)
    target_pairs = [(0, 1, 200), (0, 6, 700), (1, 2, 1100), (2, 0, 450),
                    (2, 5, 1500), (3, 3, 900), (3, 7, 1750)]

    for want_surv in (0, 1, 3, 5, 7):
        data = ((rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))) * 1e-3
                ).astype(np.complex64)
        for d_idx, t_idx, lag in target_pairs[:want_surv]:
            data[d_idx] += (20.0 * tmpl[t_idx] * np.exp(-2j * np.pi * k * lag / n)).astype(
                np.complex64)
        got_i, got_v = ctx.hier_peaks(
            n, b1, data, tmpl, tmpl[:, :b0], 5.0, binsize=n, threshold=10.0,
            cascade_band=b0, ct1=tmpl[:, :b1], raw_thr1=8.0)
        assert ctx.last_tier1_survivors == want_surv
        assert ctx.last_refinements == want_surv
        assert int((got_i >= 0).sum()) == want_surv
        for d_idx, t_idx, lag in target_pairs[:want_surv]:
            assert got_i[d_idx, t_idx, 0] == lag
            assert abs(got_v[d_idx, t_idx, 0]) > 19.5

    # Loud 1e12 + 1e12j row overflows FP16 in both Tier 0 and Tier 1 and must fail open.
    data_ov = ((rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))) * 1e-3
               ).astype(np.complex64)
    data_ov[1] += (18.0 * tmpl[4] * np.exp(-2j * np.pi * k * 640.0 / n)).astype(np.complex64)
    data_ov[3] = np.full(n, 1e12 + 1e12j, dtype=np.complex64)
    ov_i, _ = ctx.hier_peaks(
        n, b1, data_ov, tmpl, tmpl[:, :b0], 5.0, binsize=n, threshold=10.0,
        cascade_band=b0, ct1=tmpl[:, :b1], raw_thr1=8.0)
    assert ov_i[1, 4, 0] == 640
    # Every template on overflowed row 3 must fail open through Tier 0 and FP16 Tier 1.
    assert ctx.last_tier1_survivors >= nt + 1
    assert ctx.last_refinements >= nt + 1
    assert (ov_i[3, :, 0] >= 0).all()


@pytest.mark.parametrize("chain", [(64, 256), (128, 512)])
def test_gpu_tier1_fp16_grouped_row_windows(gpu_dev, chain):
    """Verify `hier_peaks_grouped` with distinct per-lane windows `[wsA, weA) != [wsB, weB)`."""
    _, ctx = gpu_dev
    b0, b1 = chain
    n, nd, nt = 2048, 13, 9
    rng = np.random.default_rng(3300 + b1)
    spec = ctx.empty_shared((nd, n))
    spec[:] = ((rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n)))
               / np.sqrt(2 * n)).astype(np.complex64)
    h = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True) / np.sqrt(n)
    k = np.arange(n, dtype=np.float32)

    # Inject signals near different window boundaries so packed survivor pairs cross row groups.
    for d_idx, t_idx, lag in ((0, 2, 260), (1, 7, 1780), (2, 1, 70), (8, 5, 1990),
                              (9, 4, 500), (11, 0, 35), (12, 8, 1420)):
        spec[d_idx] += (38.0 * h[t_idx] * np.exp(-2j * np.pi * k * lag / n)
                        / np.sqrt(n)).astype(np.complex64)

    groups = [(199, 1849, 0, 2), (40, 2040, 2, 9), (500, 501, 9, 11), (10, 1500, 11, 13)]
    got_i, got_v = ctx.hier_peaks_grouped(
        n, b1, spec, h, h[:, :b0], 1.8, groups, 512, 3.2,
        cascade_band=b0, ct1=h[:, :b1], raw_thr1=2.2)

    total_hits = 0
    for lo, hi, a, b in groups:
        sub = ctx.empty_shared((b - a, n))
        sub[:] = spec[a:b]
        ri, rv = ctx.hier_peaks(
            n, b1, sub, h, h[:, :b0], 1.8, binsize=512, threshold=3.2, window=(lo, hi),
            cascade_band=b0, ct1=h[:, :b1], raw_thr1=2.2)
        kb = ri.shape[2]
        np.testing.assert_array_equal(got_i[a:b, :, :kb], ri)
        np.testing.assert_array_equal(got_v[a:b, :, :kb], rv)
        assert (got_i[a:b, :, kb:] == -1).all()
        total_hits += int((ri >= 0).sum())
    assert total_hits >= 6


def test_gpu_tier1_fp16_shifted_bands_and_clustered_tier0(gpu_dev, monkeypatch):
    """Verify shifted active bands (`k0 > 0`) on `tier0`/`pack` and clustered Tier-0 (`compactc`)."""
    dev_str, ctx = gpu_dev
    n, nd, nt = 2048, 5, 12
    rng = np.random.default_rng(4400)

    # 1. Shifted active bands: zero signal below bin 96 so k0_0 = 96, k0_1 = 96.
    k0_0, k0_1 = 96, 96
    tmpl = np.zeros((nt, n), dtype=np.complex64)
    tmpl[:, 96:700] = (rng.standard_normal((nt, 604))
                       + 1j * rng.standard_normal((nt, 604))).astype(np.complex64)
    tmpl /= np.linalg.norm(tmpl, axis=1, keepdims=True)

    series = ctx.empty_shared(((nd + 1) * n,), dtype=np.complex64)
    raw_td = ((rng.standard_normal(series.size) + 1j * rng.standard_normal(series.size)) * 0.04
              ).astype(np.complex64)
    for d_idx, t_idx, lag in ((1, 3, 520), (3, 9, 1340)):
        td_sig = (np.fft.ifft(tmpl[t_idx]) * n).astype(np.complex64)
        raw_td[d_idx * n:(d_idx + 1) * n] += 16.5 * np.roll(td_sig, lag)
    series[:] = raw_td
    starts = np.arange(nd, dtype=np.uint32) * n

    spec_ref = ctx.empty_shared((nd, n))
    ctx.forward(n, series, starts, spec_ref, defer=False)
    spec_np = np.asarray(spec_ref).copy()
    ref_i, ref_v = ctx.peaks(n, spec_np, tmpl, binsize=512, threshold=7.5)

    def wrap_ct(arr, band, k0):
        out = np.zeros((arr.shape[0], band), dtype=np.complex64)
        khi = min(k0 + band, n // 2)
        slots = np.arange(k0, khi) & (band - 1)
        out[:, slots] = arr[:, k0:khi]
        return out

    for b0, b1 in ((64, 256), (256, 1024)):
        ct0_w = wrap_ct(tmpl, b0, k0_0)
        ct1_w = wrap_ct(tmpl, b1, k0_1)
        # Pack feed (unclaimed spectra with k0 > 0)
        hout_p = []
        p_i, p_v = ctx.hier_peaks(
            n, b1, spec_np, tmpl, ct0_w, 0.25, binsize=512, threshold=7.5,
            cascade_band=b0, ct1=ct1_w, raw_thr1=0.45, band_offsets=(k0_0, k0_1),
            handle_out=hout_p)
        assert hout_p[0].key[8] == "pack"
        # Tier-0 forward feed (claimed deferred forward with k0 > 0)
        monkeypatch.setitem(ctx.__dict__, "feed_forced", True)
        spec_sh = ctx.empty_shared((nd, n))
        ctx.forward(n, series, starts, spec_sh, defer=True)
        hout = []
        t_i, t_v = ctx.hier_peaks(
            n, b1, spec_sh, tmpl, ct0_w, 0.25, binsize=512, threshold=7.5,
            cascade_band=b0, ct1=ct1_w, raw_thr1=0.45, band_offsets=(k0_0, k0_1),
            handle_out=hout)
        assert hout[0].key[8] == "tier0"
        hits = ref_i >= 0
        assert int(hits.sum()) >= 2
        np.testing.assert_array_equal(p_i[hits], ref_i[hits])
        np.testing.assert_allclose(p_v[hits], ref_v[hits], rtol=2e-4, atol=2e-4)
        np.testing.assert_array_equal(t_i[hits], ref_i[hits])
        np.testing.assert_allclose(t_v[hits], ref_v[hits], rtol=2e-4, atol=2e-4)

    # 2. Clustered Tier-0 (`compactPairsClustered` writing `t1args` via `packShift`) on (128, 512).
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "128,512")
    from test_coarse_pair_centroids import _make_quad_correlated_bank
    power, psd, c_tmpls = _make_quad_correlated_bank(n, 16, 128, chain_drift=0.14, seed=515)
    c_data = ((rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n)))
              * np.sqrt(psd)[None, :]).astype(np.complex64)
    k = np.arange(n, dtype=np.float64)
    c_data[2] += (12.0 * psd * c_tmpls[5] * np.exp((-2j * np.pi * 840.0 / n) * k)).astype(
        np.complex64)

    flat = mf.MatchedFilter(n, ndata=nd, ntemplates=16, device=dev_str)
    flat.set_templates(c_tmpls)
    flat.set_data(c_data)
    ref_cl = flat.run(binsize=512, threshold=6.5, window=(64, n - 64))

    hf = mf.HierarchicalFilter(n, ndata=nd, ntemplates=16, snr=5.5, fd=1e-3, device=dev_str)
    hf.set_reference(power)
    hf.set_templates(c_tmpls)
    hf.set_data(c_data)
    got_cl = hf.run(binsize=512, threshold=6.5, window=(64, n - 64))
    assert hf._active_tier0_cluster() is not None
    v_cl = ref_cl[2, 5]["index"] >= 0
    assert v_cl.any()
    np.testing.assert_array_equal(got_cl[2, 5]["index"][v_cl], ref_cl[2, 5]["index"][v_cl])


@pytest.mark.parametrize("chain", [(64, 256), (128, 512)])
def test_gpu_tier1_fp16_direct_refine_and_overflow_fallback(gpu_dev, chain, monkeypatch):
    """Verify `HierarchicalFilter` with `set_taps` (`use_direct=True`) elects coarse lags in FP16
    Tier 1 and falls back cleanly to `fbSurv` on an FP16-overflowing glitch block."""
    dev_str, ctx = gpu_dev
    monkeypatch.setattr(type(ctx), "packed_fp16", True)
    monkeypatch.setattr(ctx, "packed_fp16", True)
    from matchedfilter.benchmark import _inspiral_power
    n, nt, nblocks = 2048, 16, 24
    rng = np.random.default_rng(5500 + chain[1])
    counts = np.full(nt, 161, dtype=np.int64)
    taps = np.zeros((nt, 161), np.float32)
    for t in range(nt):
        x = np.zeros(161)
        x[80] = 1.0
        x += 0.12 * np.hanning(161) * np.cos(np.linspace(0, 2.5 + 0.1 * t, 161)) / np.sqrt(161)
        taps[t] = x.astype(np.float32)
    filt, valid = template_spectra(taps, counts, n)
    spec = np.conj(filt)
    cbad, vend = int(valid[:, 0].max()), int(valid[:, 1].min())
    step = vend - cbad
    total = 1 << int(np.ceil(np.log2(step * nblocks + n)))
    p = _inspiral_power(total)
    p = p / p.sum()
    w = (rng.standard_normal(total) + 1j * rng.standard_normal(total)) / np.sqrt(2)
    series = np.fft.ifft(np.sqrt(p) * w) * np.sqrt(total)
    series *= np.sqrt(2.0 / np.mean(np.abs(series) ** 2))
    pulse = np.fft.ifft(p) * total
    for blk in (2, 7, 13, 19):
        tau = blk * step + cbad + 300 + 40 * (blk % 5)
        series += 9.5 * np.exp(2j * np.pi * rng.random()) * np.roll(pulse, tau)
    series = series.astype(np.complex64)
    # Add an extreme glitch in block 22 that overflows FP16 in both Tier 0 and Tier 1.
    series[22 * step + cbad + 400:22 * step + cbad + 460] = 1e10 + 1e10j

    starts = np.arange(nblocks, dtype=np.int64) * step
    win_s = np.full(nblocks, cbad, dtype=np.int64)
    win_e = np.full(nblocks, vend, dtype=np.int64)
    q = n // 32
    window = ((cbad // q) * q, n - (cbad // q) * q)
    ref_pow = _inspiral_power(n)

    def run_hf(direct_on):
        monkeypatch.setenv("MF_DIRECT_REFINE", "1" if direct_on else "0")
        hf = mf.HierarchicalFilter(n, 8, nt, snr=6.0, fd=1e-2, chain=chain,
                                   search_window=window, device=dev_str)
        hf.set_reference(ref_pow)
        hf.set_templates(spec)
        hf.set_taps(taps, counts)
        idx, val = hf.run_series(series, starts, win_s, win_e, binsize=n, threshold=6.0, raw=True)
        return idx.copy(), val.copy(), hf.direct_stats()

    i_dir, v_dir, st_dir = run_hf(True)
    i_fft, v_fft, _ = run_hf(False)
    assert st_dir["pairs"] > 0, "expected direct time-domain refinements to execute: %s" % st_dir
    assert st_dir["fft"] >= nt, "overflowed block 22 must fall back to FFT: %s" % st_dir
    # Normal blocks (0..21) and overflowed block 22 must agree between direct and FFT refine.
    np.testing.assert_array_equal(i_dir[:21], i_fft[:21])
    hit_norm = i_fft[:21] >= 0
    assert int(hit_norm.sum()) >= 4 * nt
    np.testing.assert_allclose(v_dir[:21][hit_norm], v_fft[:21][hit_norm], rtol=2e-4, atol=2e-4)
    assert (i_dir[22] >= 0).all() and (i_fft[22] >= 0).all()
