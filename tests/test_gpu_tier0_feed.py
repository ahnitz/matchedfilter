"""Zero-pack CUDA feed, gate-only Tier-0 peak reduction, and subgroup-scoped staging barriers.

Covers:
1. CUDA `Context.inplace_feed = True` and PTX `.entry` parameter layout parity across
   `feed = "inplace"`, `"tier0"`, and `"bands"` without requiring physical NVIDIA hardware.
2. Shipped PTX `bar.warp.sync` emission on >= 32-thread multi-level transforms and absence
   of `bar.warp.sync` on < 32-thread CTAs (`tierb_64`, `tierb_128`, `tierb_256`).
3. Live GPU execution of Tier-0 `peakTwoGate` (`nbins = 0` boolean ballot on cascades vs
   `nbins = 1` statistic on single-tier chains, grouped windows, and fp16 overflow fail-open),
   all three hierarchical feed modes (`inplace`, `tier0`, `bands`), and subgroup-scoped
   barriers across multi-wave transforms.
"""
import ctypes
import gzip
import re
import struct

import numpy as np
import pytest
from conftest import gpu_backend, gpu_context, kernel_dir, usable_gpu, usable_gpu_reason

import matchedfilter as mf
from matchedfilter import _cudacompute, _gpuhier, _kernels


def _read_ptx(ptx_dir, stem):
    raw = (ptx_dir / (stem + ".ptx.gz")).read_bytes()
    return (gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw).decode("utf-8")


def _ptx_entry_params(ptx_text, entry_name=None):
    """Return [(align, byte_size), ...] of a PTX `.visible .entry` parameter list."""
    pat = (r"\.visible\s+\.entry\s+" + re.escape(entry_name) + r"\((.*?)\)"
           if entry_name else r"\.visible\s+\.entry\s+\w+\((.*?)\)")
    m = re.search(pat, ptx_text, re.S)
    assert m is not None, "missing .visible .entry in PTX"
    out = []
    for line in m.group(1).splitlines():
        line = line.strip().rstrip(",")
        if not line.startswith(".param"):
            continue
        ma = re.search(r"\.align\s+(\d+)\s+\.b8\s+\w+\[(\d+)\]", line)
        if ma:
            out.append((int(ma.group(1)), int(ma.group(2))))
            continue
        mb = re.search(r"\.(b|u|s|f)(16|32|64)\b", line)
        assert mb is not None, "unrecognized PTX param declaration: %r" % line
        bits = int(mb.group(2))
        out.append((bits // 8, bits // 8))
    return out


class _StubBuf:
    """Minimal device buffer stub carrying a distinct 64-bit address for `_CudaList`."""

    def __init__(self, addr, nbytes):
        self.dptr = ctypes.c_uint64(addr)
        self.nbytes = nbytes
        self.host = None

    def write(self, data):
        self.last_write = bytes(np.ascontiguousarray(data))

    def zero(self, size=None):
        pass

    def mirror(self, nbytes):
        return (0x7000000, int(nbytes))

    def destroy(self):
        pass


def _stub_cuda_context(monkeypatch):
    """Instantiate a driver-free `_cudacompute.Context` backed by the shipped PTX manifest."""
    ptx_dir = kernel_dir("ptx")
    monkeypatch.setattr(_cudacompute, "_PTX_DIR", ptx_dir)
    orig_folder = _kernels.folder
    monkeypatch.setattr(_kernels, "folder",
                        lambda b: ptx_dir if b == "cuda" else orig_folder(b))
    _kernels.clear()

    ctx = _cudacompute.Context.__new__(_cudacompute.Context)
    ctx._pipelines = {}
    ctx._exec_records = {}
    ctx._exec_lru = []
    ctx._exec_bytes = 0
    ctx._cache_order = {}
    ctx._uploaded = {"data": {}, "tmpl": {}}
    ctx.cache_limit_bytes = 1 << 30
    ctx._next_addr = 0x100000
    ctx._pinned_keep = []

    def load(stem, path, fn_name, wg):
        return (stem, path, fn_name)

    def alloc(nbytes, readback=False, upload=False):
        addr = ctx._next_addr
        ctx._next_addr += (max(int(nbytes), 16) + 0xFFF) & ~0xFFF
        return _StubBuf(addr, int(nbytes))

    def take_words(nbytes):
        raw = (ctypes.c_ubyte * max(int(nbytes), 16))()
        ctx._pinned_keep.append(raw)
        return ctypes.addressof(raw), int(nbytes)

    ctx._load = load
    ctx._x_alloc = alloc
    ctx._refine_grid = lambda fn, wg, pairs: max(1, min(int(pairs), 64))
    ctx._gate_use = lambda band: True
    ctx._word_slots = lambda: type("_Words", (), {"take": staticmethod(take_words)})()
    ctx._x_list = lambda label, once=False: _cudacompute._CudaList(ctx, label)
    return ctx, ptx_dir


def test_cuda_inplace_feed_and_ptx_param_abi(monkeypatch):
    """CUDA enables `inplace_feed` and packs exact PTX-matching entry parameters across
    `inplace`, `tier0`, and `bands` hierarchical recordings without `packCoarse`."""
    assert _cudacompute.Context.inplace_feed is True
    ctx, ptx_dir = _stub_cuda_context(monkeypatch)
    try:
        n, nd, nt = 2048, 8, 12
        rng = np.random.default_rng(101)
        ct0 = (rng.standard_normal((nt, 256)) + 1j * rng.standard_normal((nt, 256))).astype(
            np.complex64)
        ct1 = (rng.standard_normal((nt, 512)) + 1j * rng.standard_normal((nt, 512))).astype(
            np.complex64)
        tiers_two = ((256, ct0, 4.0), (512, ct1, 5.0))
        et = _gpuhier.c16_template_exp(ct0)
        ed = _gpuhier.c16_data_exp(256, 4.0, et)
        layout = (32, 4, 2, True)
        bd = _StubBuf(0x9000000, nd * n * 8)
        bt = _StubBuf(0x9100000, nt * n * 8)
        series = _StubBuf(0x9200000, (nd + 2) * n * 8)
        starts = _StubBuf(0x9300000, nd * 4)
        data_arr = np.zeros((nd, n), np.complex64)
        tmpl_arr = np.zeros((nt, n), np.complex64)

        for feed, half in (("inplace", True), ("tier0", True), ("bands", False)):
            claim = None if feed == "inplace" else (series, starts, n, nd, (nd + 2) * n, 0)
            rec = ctx._hier_record(
                ("test", feed, half), n, tiers_two, nd, nt, 4,
                layout if half else None, half, feed, "dense", None,
                ed if half else 0, bd, bt, data_arr, tmpl_arr, claim)
            binds = ctx._hier_binds(
                n, tiers_two, nd, nt, 4, 0, n, 512, 9, 6.0, half,
                ed if half else 0, et if half else 0, False,
                layout if half else None, claim, data_arr)
            # Apply dynamic Arg bindings exactly as Context._enqueue does before cuLaunchKernel.
            for block, at, fn_name, off in rec.native.args:
                if off < 0:
                    _cudacompute._pack_words(-off)(block, at, *binds[fn_name])
                else:
                    _cudacompute._PACK_U64(block, at, binds[fn_name].dptr.value + off)

            launched = [op for op in rec.native.ops if op[0] == "launch"]
            stems = [op[1][0] for op in launched]
            assert not any("pack_coarse" in s for s in stems), stems
            if feed == "inplace":
                assert stems[0].startswith("tierb_256_c16")
            elif feed == "tier0":
                assert stems[0] == "forward_tier0_2048"
                assert "markblocks" in stems and "forward_listed_2048" in stems
            else:
                assert stems[0] == "forward_bands_2048"
                assert "markblocks" in stems and "forward_listed_2048" in stems

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
                    assert off % align == 0 and 0 <= off and off + size <= len(block), (
                        stem, idx, off, align, size)

            if feed == "inplace":
                # Tier 0 (c16) carries (stride=n, scale=2**ed); Tier 1 carries (stride=n, 1.0);
                # full-length refine carries (stride=0, 1.0).
                want_scale = int(np.float32(2.0 ** ed).view(np.uint32))
                t0_op = next(op for op in launched if op[1][0].startswith("tierb_256_c16"))
                t1_op = next(op for op in launched if op[1][0].startswith("refine_512"))
                rf_op = next(op for op in launched if op[1][0].startswith("refine_2048"))
                t0_tail = struct.unpack_from("<II", t0_op[4], len(t0_op[4]) - 8)
                t1_tail = struct.unpack_from("<II", t1_op[4], len(t1_op[4]) - 8)
                rf_tail = struct.unpack_from("<II", rf_op[4], len(rf_op[4]) - 8)
                assert t0_tail == (n, want_scale)
                assert t1_tail == (n, 0x3F800000)
                assert rf_tail == (0, 0x3F800000)
            elif feed == "bands":
                # seriesForwardBands writes max(bands)=512; tier 0 reads stride 512, scale 1.0.
                t0_op = next(op for op in launched if op[1][0] == "tierb_256")
                t0_tail = struct.unpack_from("<II", t0_op[4], len(t0_op[4]) - 8)
                assert t0_tail == (512, 0x3F800000)
    finally:
        _kernels.clear()


def test_ptx_warp_barriers_and_register_footprint():
    """Multi-level >= 32-thread PTX kernels emit `bar.warp.sync` on warp-local stages without
    adding `.local` spill bytes, while < 32-thread CTAs emit zero `bar.warp.sync`."""
    ptx_dir = kernel_dir("ptx")
    for stem in ("refine_2048", "refine_4096", "refine_65536_lds32",
                 "refine_512_onebin_gate", "forward_tier0_2048", "forward_bands_2048"):
        txt = _read_ptx(ptx_dir, stem)
        assert re.search(r"\bbar\.warp\.sync\b", txt), "%s missing bar.warp.sync" % stem
        local_bytes = sum(int(m.group(1)) for m in re.finditer(
            r"\.local\s+\.align\s+\d+\s+\.b8\s+\w+\[(\d+)\];", txt))
        assert local_bytes <= 28, "%s unexpected .local bytes: %d" % (stem, local_bytes)

    # Untiled small transforms have WG = 4, 8, 16 (< 32 threads per CTA): bar.warp.sync -1
    # would include non-existent warp lanes on sm_75+, so they must use bar.sync only.
    for stem in ("tierb_64", "tierb_128", "tierb_256"):
        txt = _read_ptx(ptx_dir, stem)
        assert not re.search(r"\bbar\.warp\.sync\b", txt), (
            "%s (< 32-thread CTA) must not emit bar.warp.sync" % stem)


def test_tier0_boolean_gate_vs_single_tier_statistic_and_overflow():
    """A 2-tier cascade dispatches coarse tier 0 with `nbins = 0` (boolean gate markers in
    `cval0`, zero false dismissals, fail-open on fp16 overflow), while a 1-tier chain keeps
    `nbins = 1` (reporting its fp16 coarse statistic)."""
    dev = usable_gpu()
    if dev is None:
        pytest.skip(usable_gpu_reason())
    ctx = gpu_context(gpu_backend())
    try:
        n, b0, b1, nd, nt = 2048, 256, 512, 4, 16
        if not ctx._x_has_c16(b0):
            pytest.skip("band %d has no fp16 coarse tier" % b0)
        rng = np.random.default_rng(2027)
        tmpl = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(
            np.complex64)
        tmpl /= np.linalg.norm(tmpl, axis=1, keepdims=True)
        data = ((rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))) * 0.05
                ).astype(np.complex64)
        # Inject one clear signal on (row 1, tmpl 5, lag 600) and one massive fp16-overflowing
        # transient on row 3 so every template on row 3 must fail open through tier 0.
        k = np.arange(n, dtype=np.float32)
        data[1] += (18.0 * tmpl[5] * np.exp(-2j * np.pi * k * 600.0 / n)).astype(np.complex64)
        data[3] = np.full(n, 1e12 + 1e12j, dtype=np.complex64)

        ref_i, ref_v = ctx.peaks(n, data[:3], tmpl, binsize=512, threshold=8.0)

        hout = []
        got_i, got_v = ctx.hier_peaks(
            n, b1, data, tmpl, np.ascontiguousarray(tmpl[:, :b0]), 0.8,
            cascade_band=b0, ct1=np.ascontiguousarray(tmpl[:, :b1]), raw_thr1=1.5,
            binsize=512, threshold=8.0, handle_out=hout)
        assert hout and hout[0].binds["coarse"][5] == 0

        # Rows 0..2 match exact flat peaks; row 3 overflowed fp16 and failed open into fp32 refine.
        np.testing.assert_array_equal(got_i[:3], ref_i)
        np.testing.assert_allclose(got_v[:3], ref_v, rtol=2e-5, atol=1e-4)
        assert np.all(got_i[3] >= 0), "fp16 overflow row was gated out instead of failing open"

        # If a tiled wave layout ran (gate_bits != 0), cval0 holds boolean gate markers only:
        # 0 for dismissed pairs, exact scaled threshold (or overflow sentinel) for passing pairs.
        if hout[0].binds["coarse"][6] != 0:
            cval0 = np.empty(nd * nt, np.complex64)
            ctx._x_read(hout[0].rec.buffers["cval0"], cval0)
            mags = np.abs(cval0[:3 * nt])
            thr_scaled = np.float32(0.8 * ctx._last_c16_scale)
            nz = mags[mags > 0]
            assert nz.size >= 1 and (mags == 0).sum() >= 1
            assert np.all((np.isclose(nz, thr_scaled, rtol=1e-6)) | (nz > 1e30)), nz

        # Grouped per-row windows on a 2-tier cascade also pass through `peakTwoGate` cleanly.
        spec = ctx.empty_shared((nd, n))
        spec[:] = data
        spec_ok = ctx.empty_shared((3, n))
        spec_ok[:] = data[:3]
        groups = [(50, 1950, 0, 1), (100, 1900, 1, 3), (0, 2048, 3, 4)]
        gi, gv = ctx.hier_peaks_grouped(
            n, b1, spec, tmpl, np.ascontiguousarray(tmpl[:, :b0]), 0.8,
            groups, 512, 8.0, cascade_band=b0,
            ct1=np.ascontiguousarray(tmpl[:, :b1]), raw_thr1=1.5)
        ri, rv = ctx.peaks_grouped(n, spec_ok, tmpl, groups[:2], 512, 8.0)
        np.testing.assert_array_equal(gi[:3, :, :ri.shape[2]], ri)
        np.testing.assert_allclose(gv[:3, :, :rv.shape[2]], rv, rtol=2e-5, atol=1e-4)

        # Single-tier chain (`len(tiers) == 1`) keeps `nbins = 1` so `cval0` reports its fp16
        # coarse statistic rather than a constant threshold marker.
        hout1 = []
        ctx.hier_peaks(n, b0, data[:2], tmpl, np.ascontiguousarray(tmpl[:, :b0]), 0.8,
                       binsize=512, threshold=8.0, handle_out=hout1)
        assert hout1 and hout1[0].binds["coarse"][5] == 1
    finally:
        ctx.destroy()


def test_gpu_band_and_tier0_feeds_match_inplace(monkeypatch):
    """Deferred forwards claimed as `tier0` (fp16 first tier) and `bands` (fp32 first tier)
    each match `inplace` hierarchical peaks on live GPU hardware."""
    dev = usable_gpu()
    if dev is None:
        pytest.skip(usable_gpu_reason())
    ctx = gpu_context(gpu_backend())
    try:
        n, b0, b1, nd, nt = 2048, 256, 512, 16, 8
        rng = np.random.default_rng(77)
        tmpl = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(
            np.complex64)
        tmpl /= np.linalg.norm(tmpl, axis=1, keepdims=True)
        series = ctx.empty_shared(((nd + 2) * n,))
        series[:] = ((rng.standard_normal(series.shape)
                      + 1j * rng.standard_normal(series.shape)) * 0.1).astype(np.complex64)
        # Inject one loud match in block 5 so markBlocks + seriesForwardListed recomputes it.
        starts = np.arange(nd, dtype=np.uint32) * (n // 2)
        s5 = int(starts[5])
        series[s5 + 300:s5 + 300 + n] += (35.0 * n * np.fft.ifft(tmpl[2])).astype(np.complex64)

        spec_ref = ctx.empty_shared((nd, n))
        ctx.forward(n, series, starts, spec_ref, defer=False)
        ref_i, ref_v = ctx.hier_peaks(
            n, b1, spec_ref, tmpl, np.ascontiguousarray(tmpl[:, :b0]), 0.8,
            cascade_band=b0, ct1=np.ascontiguousarray(tmpl[:, :b1]), raw_thr1=1.5,
            binsize=512, threshold=12.0)
        assert ref_i[5, 2, 0] == 300

        # 1) Claimed `tier0` feed (fp16 tier 0).
        if ctx._x_has_c16(b0) and ctx._x_has_kernel("fwd_tier0", n):
            spec_t0 = ctx.empty_shared((nd, n))
            before = _gpuhier.CLAIMS[0]
            ctx.forward(n, series, starts, spec_t0, defer=True)
            hout = []
            i_t0, v_t0 = ctx.hier_peaks(
                n, b1, spec_t0, tmpl, np.ascontiguousarray(tmpl[:, :b0]), 0.8,
                cascade_band=b0, ct1=np.ascontiguousarray(tmpl[:, :b1]), raw_thr1=1.5,
                binsize=512, threshold=12.0, handle_out=hout)
            assert _gpuhier.CLAIMS[0] == before + 1
            assert "tier0" in hout[0].key and "band0" in hout[0].rec.buffers
            np.testing.assert_array_equal(i_t0, ref_i)
            np.testing.assert_allclose(v_t0, ref_v, rtol=2e-5, atol=1e-4)

        # 2) Claimed `bands` feed (fp32 tier 0, when c16 is unavailable at tier 0).
        if ctx.inplace_feed:
            monkeypatch.setattr(ctx, "_x_has_c16", lambda band: False)
            ctx.__dict__.pop("_shipped_memo", None)
            spec_bd = ctx.empty_shared((nd, n))
            before = _gpuhier.CLAIMS[0]
            ctx.forward(n, series, starts, spec_bd, defer=True)
            hout_b = []
            i_bd, v_bd = ctx.hier_peaks(
                n, b1, spec_bd, tmpl, np.ascontiguousarray(tmpl[:, :b0]), 0.8,
                cascade_band=b0, ct1=np.ascontiguousarray(tmpl[:, :b1]), raw_thr1=1.5,
                binsize=512, threshold=12.0, handle_out=hout_b)
            assert _gpuhier.CLAIMS[0] == before + 1
            assert "bands" in hout_b[0].key and "bands" in hout_b[0].rec.buffers
            assert i_bd[5, 2, 0] == 300
            np.testing.assert_allclose(v_bd[5, 2, 0], ref_v[5, 2, 0], rtol=2e-5, atol=1e-4)
    finally:
        ctx.destroy()


@pytest.mark.parametrize("n", [2048, 4096, 8192, 16384])
def test_multiwave_subgroup_barriers_match_cpu(n):
    """Multi-wave transforms exercising subgroup-scoped staging barriers (`exchange`,
    `exchangeS`, `SPLIT_STAGE`) match CPU/NumPy references across lengths 2048..16384."""
    dev = usable_gpu()
    if dev is None:
        pytest.skip(usable_gpu_reason())
    if gpu_backend() == "vulkan":
        ctx = gpu_context("vulkan")
        try:
            assert isinstance(ctx.full_subgroups, bool)
        finally:
            ctx.destroy()

    rng = np.random.default_rng(3000 + n)
    nd, nt = 3, 4
    data = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    tmpl = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    tmpl /= np.linalg.norm(tmpl, axis=1, keepdims=True)
    k = np.arange(n, dtype=np.float32)
    data[1] += (25.0 * tmpl[2] * np.exp(-2j * np.pi * k * (n // 3) / n)).astype(np.complex64)

    out = {}
    for target in ("cpu", dev):
        hf = mf.HierarchicalFilter(n, nd, nt, snr=8.0, fd=1e-3, chain=(256, 512), device=target)
        hf.set_coarse_threshold((0.8, 1.5))
        hf.set_data(data)
        hf.set_templates(tmpl)
        out[str(target)] = hf.run(binsize=n // 4, threshold=12.0).copy()

    got, ref = out[str(dev)], out["cpu"]
    np.testing.assert_array_equal(got["index"], ref["index"])
    np.testing.assert_allclose(got["value"], ref["value"], rtol=2e-5, atol=1e-4)
