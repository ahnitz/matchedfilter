"""Dispatching Slang PTX kernels via the native CUDA Driver API.

Zero runtime dependencies: uses libcuda.so.1 through ctypes directly.
Does not require CUDA Toolkit, nvcc, or runtime compilers.
Loads pre-compiled PTX blobs from python/matchedfilter/ptx/.
"""
import ctypes
import os
import pathlib
import sys
from functools import wraps

import numpy as np

from . import _cuda
from ._cuda import check_cuda
from ._errors import UnsupportedSize
from ._gpu_cache import InputUploads
from ._shared import empty_shared, shared_buffer, shared_key, write_input

_HERE = pathlib.Path(__file__).resolve().parent
_PTX_DIR = _HERE / "ptx"
_MANIFEST = _PTX_DIR / "manifest.json"

_manifest_cache = None


def _manifest():
    """Build manifest for the PTX kernels."""
    global _manifest_cache
    if _manifest_cache is None:
        import json
        _manifest_cache = (
            json.loads(_MANIFEST.read_text()) if _MANIFEST.is_file() else {}
        )
    return _manifest_cache


_MAX_BINS = 2048


def _radix(n):
    return {32768: 32, 65536: 64}.get(n, 16)


def _use_c16(band):
    return band <= 1024


def _pack_half2(a):
    """Bit-pack complex64 into uint32 holding (real_half, imag_half)."""
    a = np.ascontiguousarray(a, dtype=np.complex64)
    r = a.real.astype(np.float16).view(np.uint16)
    i = a.imag.astype(np.float16).view(np.uint16)
    return (r.astype(np.uint32) | (i.astype(np.uint32) << 16)).copy()


class _Buffer:
    """Device memory allocation managed via cuMemAlloc / cuMemFree."""

    def __init__(self, ctx, nbytes):
        self.ctx = ctx
        self.nbytes = int(nbytes)
        self.dptr = ctypes.c_uint64(0)
        if self.nbytes > 0:
            check_cuda(
                self.ctx.cuda.cuMemAlloc_v2(ctypes.byref(self.dptr), self.nbytes),
                "cuMemAlloc",
            )

    def write(self, array):
        """Host to device memory copy."""
        array = np.ascontiguousarray(array)
        to_copy = min(self.nbytes, array.nbytes)
        if to_copy > 0:
            check_cuda(
                self.ctx.cuda.cuMemcpyHtoDAsync_v2(
                    self.dptr, array.ctypes.data, to_copy, self.ctx.stream
                ),
                "cuMemcpyHtoDAsync",
            )

    def read(self, dtype, count):
        """Device to host read."""
        out = np.empty(count, dtype=dtype)
        self.read_into(out)
        return out

    def read_into(self, out):
        """Direct read into caller-provided array."""
        out = np.ascontiguousarray(out)
        to_copy = min(self.nbytes, out.nbytes)
        if to_copy > 0:
            check_cuda(
                self.ctx.cuda.cuMemcpyDtoHAsync_v2(
                    out.ctypes.data, self.dptr, to_copy, self.ctx.stream
                ),
                "cuMemcpyDtoHAsync",
            )
            check_cuda(
                self.ctx.cuda.cuStreamSynchronize(self.ctx.stream),
                "cuStreamSynchronize",
            )
        return out

    def destroy(self):
        if self.dptr.value:
            self.ctx.cuda.cuMemFree_v2(self.dptr)
            self.dptr.value = 0

    def __del__(self):
        self.destroy()


class Context(InputUploads):
    """One NVIDIA CUDA device context, stream, and loaded PTX pipelines."""

    max_grouped_bins = _MAX_BINS

    def __init__(self, index=0):
        self.cuda = _cuda.get_cuda_lib()
        self.dev_idx = index
        self.device = ctypes.c_int(0)
        self.ctx = ctypes.c_void_p()
        self.stream = ctypes.c_void_p()
        self._start_event = ctypes.c_void_p()
        self._stop_event = ctypes.c_void_p()

        check_cuda(self.cuda.cuInit(0), "cuInit")
        check_cuda(self.cuda.cuDeviceGet(ctypes.byref(self.device), index), "cuDeviceGet")
        name_buf = ctypes.create_string_buffer(256)
        self.cuda.cuDeviceGetName(name_buf, len(name_buf), self.device.value)
        self.name = name_buf.value.decode("utf-8", "replace").strip()

        check_cuda(self.cuda.cuCtxCreate_v2(ctypes.byref(self.ctx), 0, self.device), "cuCtxCreate")
        check_cuda(self.cuda.cuStreamCreate(ctypes.byref(self.stream), 0), "cuStreamCreate")
        check_cuda(self.cuda.cuEventCreate(ctypes.byref(self._start_event), 0), "cuEventCreate")
        check_cuda(self.cuda.cuEventCreate(ctypes.byref(self._stop_event), 0), "cuEventCreate")

        self.last_gpu_time = 0.0
        self.last_refinements = 0
        self.cache_limit_bytes = 1024 * 1024 * 1024
        self._modules = {}
        self._pipelines = {}
        self._batches = {}
        self._full_batches = {}
        self._tierc_batches = {}
        self._forwards = {}
        self._hier = {}
        self._uploaded = {"data": {}, "tmpl": {}}

    def _stem(self, n, entry, one_bin=False, c16=False, ppg=1, tile=1):
        if entry == "packCoarse":
            return "pack_coarse"
        if entry == "compactPairs":
            return "compact"
        if entry == "seriesForward":
            return f"forward_{n}"
        if entry == "coarseTile":
            return f"coarse_{n}"
        if c16:
            p_s = f"p{ppg}" if ppg > 1 else ""
            t_s = f"t{tile}" if tile > 1 else ""
            return f"tierb_{n}_c16{p_s}{t_s}"
        if one_bin and n >= 16384:
            return f"tierb_{n}_onebin"
        if entry == "refineListed":
            return f"refine_{n}_onebin" if (one_bin and n >= 16384) else f"refine_{n}"
        if entry == "fullCorrelation":
            return f"full_{n}"
        if entry == "fullCorrelationSeries":
            return f"full_series_{n}"
        return f"tierb_{n}"

    def pipeline(self, n, entry="fusedTierB", one_bin=False, c16=False, ppg=1, tile=1):
        """Retrieve or load the compiled PTX kernel function."""
        key = (n, entry, one_bin, c16, ppg, tile)
        if key in self._pipelines:
            return self._pipelines[key]

        stem = self._stem(n, entry, one_bin=one_bin, c16=c16, ppg=ppg, tile=tile)
        if stem not in self._modules:
            ptx_file = _PTX_DIR / f"{stem}.ptx"
            if not ptx_file.is_file():
                # Fall back to base variant if tiled/ppg variant absent
                alt_stem = self._stem(n, entry, one_bin=one_bin, c16=c16, ppg=1, tile=1)
                alt_ptx = _PTX_DIR / f"{alt_stem}.ptx"
                if alt_ptx.is_file():
                    ptx_file = alt_ptx
                    stem = alt_stem
                else:
                    raise UnsupportedSize(f"no PTX kernel for {stem} (n={n}, entry={entry})")

            mod = ctypes.c_void_p()
            ptx_bytes = ptx_file.read_bytes()
            check_cuda(
                self.cuda.cuModuleLoadData(ctypes.byref(mod), ptx_bytes),
                f"cuModuleLoadData({stem})",
            )
            self._modules[stem] = mod

        mod = self._modules[stem]
        fn_name = "fusedTierB" if (c16 and entry not in ("coarseTile", "refineListed")) else entry
        hfunc = ctypes.c_void_p()
        check_cuda(
            self.cuda.cuModuleGetFunction(ctypes.byref(hfunc), mod, fn_name.encode("utf-8")),
            f"cuModuleGetFunction({fn_name})",
        )

        r = _radix(n)
        wg = (n // r) * ppg if entry in ("fusedTierB", "refineListed") else (
            256 if entry == "compactPairs" else (
                64 if entry == "coarseTile" else (n // r)
            )
        )
        res = (hfunc, wg)
        self._pipelines[key] = res
        return res

    def empty_shared(self, shape, dtype=np.complex64, *, readback=False):
        return empty_shared(self, _Buffer, shape, dtype)

    def _launch(self, hfunc, grid_dim, block_dim, params, shared_mem=0):
        param_ptrs = (ctypes.c_void_p * len(params))(
            *[ctypes.c_void_p(ctypes.addressof(p)) for p in params]
        )
        gx, gy, gz = grid_dim if isinstance(grid_dim, tuple) else (grid_dim, 1, 1)
        bx, by, bz = block_dim if isinstance(block_dim, tuple) else (block_dim, 1, 1)
        check_cuda(
            self.cuda.cuLaunchKernel(
                hfunc,
                gx, gy, gz,
                bx, by, bz,
                shared_mem,
                self.stream,
                param_ptrs,
                None,
            ),
            "cuLaunchKernel",
        )

    def _sync_and_time(self):
        check_cuda(self.cuda.cuEventRecord(self._stop_event, self.stream), "cuEventRecord")
        check_cuda(self.cuda.cuEventSynchronize(self._stop_event), "cuEventSynchronize")
        ms = ctypes.c_float(0.0)
        check_cuda(
            self.cuda.cuEventElapsedTime(ctypes.byref(ms), self._start_event, self._stop_event),
            "cuEventElapsedTime",
        )
        self.last_gpu_time = ms.value * 1e-3

    def peaks(self, n, data, tmpl, binsize=None, threshold=0.0, window=None,
              upload_data=True, upload_tmpl=True, _groups=None,
              slot=None, async_submit=False):
        nd, nt = data.shape[0], tmpl.shape[0]
        lo, hi = (0, n) if window is None else (int(window[0]), int(window[1]))
        lo, hi = max(0, min(lo, n)), max(0, min(hi, n))
        if lo >= hi:
            raise ValueError(f"empty window ({lo}, {hi})")
        binsize = n if binsize is None else int(binsize)
        nbins = -(-(hi - lo) // binsize)
        if nbins > _MAX_BINS:
            span = _MAX_BINS * binsize
            pi, pv = [], []
            for a in range(lo, hi, span):
                i2, v2 = self.peaks(n, data, tmpl, binsize=binsize,
                                    threshold=threshold,
                                    window=(a, min(a + span, hi)),
                                    upload_data=upload_data,
                                    upload_tmpl=upload_tmpl)
                pi.append(i2)
                pv.append(v2)
                upload_data = upload_tmpl = False
            return np.concatenate(pi, axis=2), np.concatenate(pv, axis=2)

        shift = (binsize.bit_length() - 1) if binsize & (binsize - 1) == 0 else -1
        t2 = float(threshold) ** 2 if threshold > 0 else 0.0

        key = (n, nd, nt, nbins)
        key += (shared_key(data, self), shared_key(tmpl, self))
        upload_data, upload_tmpl, dsig, tsig = self._input_uploads(
            key, data, tmpl, upload_data, upload_tmpl
        )

        bufs = self._batches.get(key)
        if bufs is None:
            bufs = {
                "data": shared_buffer(data, self) or _Buffer(self, nd * n * 8),
                "tmpl": shared_buffer(tmpl, self) or _Buffer(self, nt * n * 8),
                "idx": _Buffer(self, nd * nt * nbins * 4),
                "val": _Buffer(self, nd * nt * nbins * 8),
            }
            self._batches[key] = bufs
            upload_data = upload_tmpl = True

        self._cache_touch("flat", key)
        if upload_data:
            write_input(bufs["data"], data)
            self._uploaded["data"][key] = dsig
        if upload_tmpl:
            write_input(bufs["tmpl"], tmpl)
            self._uploaded["tmpl"][key] = tsig

        hfunc, wg = self.pipeline(n, "fusedTierB", one_bin=(nbins == 1))

        # Parameters for fusedTierB
        c_ntmpl = ctypes.c_uint32(nt)
        c_winStart = ctypes.c_uint32(lo)
        c_winEnd = ctypes.c_uint32(hi)
        c_binsize = ctypes.c_uint32(binsize)
        c_binShift = ctypes.c_int32(shift)
        c_nbins = ctypes.c_uint32(nbins)
        c_thrBits = ctypes.c_uint32(int(np.float32(t2).view(np.uint32)))

        params = [
            bufs["data"].dptr,
            bufs["tmpl"].dptr,
            bufs["idx"].dptr,
            bufs["val"].dptr,
            c_ntmpl,
            c_winStart,
            c_winEnd,
            c_binsize,
            c_binShift,
            c_nbins,
            c_thrBits,
        ]

        check_cuda(self.cuda.cuEventRecord(self._start_event, self.stream), "cuEventRecord")
        self._launch(hfunc, nd * nt, wg, params)
        self._sync_and_time()

        idx = bufs["idx"].read(np.int32, nd * nt * nbins).reshape(nd, nt, nbins)
        val_raw = bufs["val"].read(np.float32, nd * nt * nbins * 2).reshape(nd, nt, nbins, 2)
        val = (val_raw[..., 0] + 1j * val_raw[..., 1]).astype(np.complex64)
        return idx, val

    def peaks_grouped(self, n, data, tmpl, groups, binsize, threshold, *, upload_tmpl=True,
                      slot=None, async_submit=False):
        """Dispatch grouped window intervals across pairs."""
        nd, nt = data.shape[0], tmpl.shape[0]
        idx_all = np.full((nd, nt, len(groups)), -1, dtype=np.int32)
        val_all = np.zeros((nd, nt, len(groups)), dtype=np.complex64)
        for g_idx, (lo, hi) in enumerate(groups):
            pi, pv = self.peaks(n, data, tmpl, binsize=binsize, threshold=threshold,
                                window=(lo, hi), upload_data=(g_idx == 0),
                                upload_tmpl=(upload_tmpl and g_idx == 0))
            idx_all[:, :, g_idx:g_idx+1] = pi
            val_all[:, :, g_idx:g_idx+1] = pv
        return idx_all, val_all

    def correlate(self, n, data, tmpl, out, *, upload_data=True, upload_tmpl=True):
        """Full circular correlation in natural lag order."""
        nd, nt = data.shape[0], tmpl.shape[0]
        out_buf = shared_buffer(out, self) or _Buffer(self, out.nbytes)
        key = (n, nd, nt, "full")
        bufs = self._full_batches.get(key)
        if bufs is None:
            bufs = {
                "data": shared_buffer(data, self) or _Buffer(self, data.nbytes),
                "tmpl": shared_buffer(tmpl, self) or _Buffer(self, tmpl.nbytes),
            }
            self._full_batches[key] = bufs
            upload_data = upload_tmpl = True

        if upload_data:
            write_input(bufs["data"], data)
        if upload_tmpl:
            write_input(bufs["tmpl"], tmpl)

        hfunc, wg = self.pipeline(n, "fullCorrelation")
        c_ntmpl = ctypes.c_uint32(nt)
        params = [bufs["data"].dptr, bufs["tmpl"].dptr, out_buf.dptr, c_ntmpl]

        check_cuda(self.cuda.cuEventRecord(self._start_event, self.stream), "cuEventRecord")
        self._launch(hfunc, nd * nt, wg, params)
        self._sync_and_time()

        if shared_buffer(out, self) is None:
            out_buf.read_into(out)
        return out

    def correlate_continuous(self, n, data, tmpl, starts, out, lo, hi,
                             *, upload_data=True, upload_tmpl=True):
        """Full correlation written at continuous absolute series offsets."""
        nd, nt = data.shape[0], tmpl.shape[0]
        out_buf = shared_buffer(out, self) or _Buffer(self, out.nbytes)
        starts_buf = shared_buffer(starts, self) or _Buffer(self, starts.nbytes)
        if shared_buffer(starts, self) is None:
            starts_buf.write(starts)

        key = (n, nd, nt, "full_series")
        bufs = self._full_batches.get(key)
        if bufs is None:
            bufs = {
                "data": shared_buffer(data, self) or _Buffer(self, data.nbytes),
                "tmpl": shared_buffer(tmpl, self) or _Buffer(self, tmpl.nbytes),
            }
            self._full_batches[key] = bufs
            upload_data = upload_tmpl = True

        if upload_data:
            write_input(bufs["data"], data)
        if upload_tmpl:
            write_input(bufs["tmpl"], tmpl)

        hfunc, wg = self.pipeline(n, "fullCorrelationSeries")
        # params: uniform uint4 (ntmpl, output_len, lo, hi)
        c_ntmpl = ctypes.c_uint32(nt)
        c_out_len = ctypes.c_uint32(out.shape[-1])
        c_lo = ctypes.c_uint32(lo)
        c_hi = ctypes.c_uint32(hi)

        params = [
            bufs["data"].dptr,
            bufs["tmpl"].dptr,
            starts_buf.dptr,
            out_buf.dptr,
            c_ntmpl,
            c_out_len,
            c_lo,
            c_hi,
        ]

        check_cuda(self.cuda.cuEventRecord(self._start_event, self.stream), "cuEventRecord")
        self._launch(hfunc, nd * nt, wg, params)
        self._sync_and_time()

        if shared_buffer(out, self) is None:
            out_buf.read_into(out)
        return out

    def hier_peaks(self, n, band, data, tmpl, ct0, raw_thr, binsize=None,
                   threshold=0.0, window=None, upload_data=True, upload_tmpl=True,
                   cascade_band=None, ct1=None, raw_thr1=None,
                   slot=None, async_submit=False):
        """Hierarchical coarse-to-fine peak detection."""
        nd, nt = data.shape[0], tmpl.shape[0]
        pairs = nd * nt
        lo, hi = (0, n) if window is None else (int(window[0]), int(window[1]))
        lo, hi = max(0, min(lo, n)), max(0, min(hi, n))
        if lo >= hi:
            raise ValueError(f"empty window ({lo}, {hi})")
        binsize = n if binsize is None else int(binsize)
        nbins = -(-(hi - lo) // binsize)
        if nbins > _MAX_BINS:
            span = _MAX_BINS * binsize
            pi, pv = [], []
            for a in range(lo, hi, span):
                i2, v2 = self.hier_peaks(n, band, data, tmpl, ct0, raw_thr,
                                         binsize=binsize, threshold=threshold,
                                         window=(a, min(a + span, hi)),
                                         upload_data=upload_data, upload_tmpl=upload_tmpl)
                pi.append(i2)
                pv.append(v2)
                upload_data = upload_tmpl = False
            return np.concatenate(pi, axis=2), np.concatenate(pv, axis=2)

        shift = (binsize.bit_length() - 1) if binsize & (binsize - 1) == 0 else -1
        t2 = float(threshold) ** 2 if threshold > 0 else 0.0

        key = (n, band, nd, nt, nbins)
        key += (shared_key(data, self), shared_key(tmpl, self))
        upload_data, upload_tmpl, dsig, tsig = self._input_uploads(
            key, data, tmpl, upload_data, upload_tmpl
        )

        cbytes = 4 if _use_c16(band) else 8
        bufs = self._hier.get(key)
        if bufs is None:
            bufs = {
                "data": shared_buffer(data, self) or _Buffer(self, nd * n * 8),
                "tmpl": shared_buffer(tmpl, self) or _Buffer(self, nt * n * 8),
                "cdata": _Buffer(self, nd * band * cbytes),
                "ct0": _Buffer(self, nt * band * cbytes),
                "cidx": _Buffer(self, pairs * 4),
                "cval": _Buffer(self, pairs * 8),
                "surv": _Buffer(self, pairs * 4),
                "args": _Buffer(self, 16),
                "idx": _Buffer(self, nd * nt * nbins * 4),
                "val": _Buffer(self, nd * nt * nbins * 8),
            }
            self._hier[key] = bufs
            upload_data = upload_tmpl = True

        self._cache_touch("hier", key)
        if upload_data:
            write_input(bufs["data"], data)
            if shared_buffer(data, self) is None:
                if _use_c16(band):
                    bufs["cdata"].write(_pack_half2(data[:, :band]))
                else:
                    bufs["cdata"].write(np.ascontiguousarray(data[:, :band], np.complex64))
            self._uploaded["data"][key] = dsig
        if upload_tmpl:
            write_input(bufs["tmpl"], tmpl)
            if _use_c16(band):
                bufs["ct0"].write(_pack_half2(ct0))
            else:
                bufs["ct0"].write(np.ascontiguousarray(ct0, np.complex64))
            self._uploaded["tmpl"][key] = tsig

        # Reset survivor counter
        init_args = np.array([0, 1, 1, 0], dtype=np.uint32)
        bufs["args"].write(init_args)

        check_cuda(self.cuda.cuEventRecord(self._start_event, self.stream), "cuEventRecord")

        # 1. Coarse stage
        if shared_buffer(data, self) is not None:
            # Pack coarse on GPU
            pack_fn, pack_wg = self.pipeline(4096, "packCoarse")
            c_n = ctypes.c_uint32(n)
            c_b = ctypes.c_uint32(band)
            c_tot = ctypes.c_uint32(nd * band)
            c_c16 = ctypes.c_uint32(int(_use_c16(band)))
            self._launch(pack_fn, (nd * band + 255) // 256, 256,
                         [bufs["data"].dptr, bufs["cdata"].dptr, c_n, c_b, c_tot, c_c16])

        R_coarse = n // band
        cstart = lo // R_coarse
        cend = min(band, (hi + R_coarse - 1) // R_coarse)
        if cstart > 0:
            cstart -= 1
        cend = max(cstart + 1, cend)
        cspan = max(1, cend - cstart)
        shift_c = (cspan.bit_length() - 1) if cspan & (cspan - 1) == 0 else -1

        coarse_fn, coarse_wg = self.pipeline(band, "fusedTierB", c16=_use_c16(band))
        c_cntmpl = ctypes.c_uint32(nt)
        c_cstart = ctypes.c_uint32(cstart)
        c_cend = ctypes.c_uint32(cend)
        c_cspan = ctypes.c_uint32(cspan)
        c_shift_c = ctypes.c_int32(shift_c)
        c_one = ctypes.c_uint32(1)
        c_zero = ctypes.c_uint32(0)

        params_coarse = [
            bufs["cdata"].dptr,
            bufs["ct0"].dptr,
            bufs["cidx"].dptr,
            bufs["cval"].dptr,
            c_cntmpl,
            c_cstart,
            c_cend,
            c_cspan,
            c_shift_c,
            c_one,
            c_zero,
        ]
        self._launch(coarse_fn, pairs, coarse_wg, params_coarse)

        # 2. Compact survivors
        compact_fn, compact_wg = self.pipeline(band, "compactPairs")
        c_pairs = ctypes.c_uint32(pairs)
        c_thr = ctypes.c_float(float(raw_thr))
        c_nb = ctypes.c_uint32(nbins)

        params_compact = [
            bufs["cval"].dptr,
            bufs["surv"].dptr,
            bufs["args"].dptr,
            bufs["idx"].dptr,
            bufs["val"].dptr,
            c_pairs,
            c_thr,
            c_nb,
        ]
        self._launch(compact_fn, (pairs + 255) // 256, 256, params_compact)

        # Read back survivor count
        surv_count_arr = bufs["args"].read(np.uint32, 1)
        surv_count = int(surv_count_arr[0])

        # 3. Refine surviving pairs
        if surv_count > 0:
            refine_fn, refine_wg = self.pipeline(n, "refineListed", one_bin=(nbins == 1))
            c_ntmpl = ctypes.c_uint32(nt)
            c_winStart = ctypes.c_uint32(lo)
            c_winEnd = ctypes.c_uint32(hi)
            c_binsize = ctypes.c_uint32(binsize)
            c_binShift = ctypes.c_int32(shift)
            c_nbins = ctypes.c_uint32(nbins)
            c_thrBits = ctypes.c_uint32(int(np.float32(t2).view(np.uint32)))

            params_refine = [
                bufs["data"].dptr,
                bufs["tmpl"].dptr,
                bufs["idx"].dptr,
                bufs["val"].dptr,
                bufs["surv"].dptr,
                c_ntmpl,
                c_winStart,
                c_winEnd,
                c_binsize,
                c_binShift,
                c_nbins,
                c_thrBits,
            ]
            self._launch(refine_fn, surv_count, refine_wg, params_refine)

        self._sync_and_time()
        self.last_refinements = surv_count

        idx = bufs["idx"].read(np.int32, nd * nt * nbins).reshape(nd, nt, nbins)
        val_raw = bufs["val"].read(np.float32, nd * nt * nbins * 2).reshape(nd, nt, nbins, 2)
        val = (val_raw[..., 0] + 1j * val_raw[..., 1]).astype(np.complex64)
        return idx, val

    def forward(self, n, series, starts, spectra, *, defer=False):
        """Batch forward series FFTs."""
        hfunc, wg = self.pipeline(n, "seriesForward")
        series_buf = shared_buffer(series, self) or _Buffer(self, series.nbytes)
        starts_buf = shared_buffer(starts, self) or _Buffer(self, starts.nbytes)
        spectra_buf = shared_buffer(spectra, self) or _Buffer(self, spectra.nbytes)

        if shared_buffer(series, self) is None:
            series_buf.write(series)
        if shared_buffer(starts, self) is None:
            starts_buf.write(starts)

        c_len = ctypes.c_uint32(series.size)
        params = [series_buf.dptr, starts_buf.dptr, spectra_buf.dptr, c_len]

        check_cuda(self.cuda.cuEventRecord(self._start_event, self.stream), "cuEventRecord")
        self._launch(hfunc, spectra.shape[0], wg, params)
        self._sync_and_time()

        if shared_buffer(spectra, self) is None:
            spectra_buf.read_into(spectra)

    def cancel_forward(self):
        pass

    def clear_cache(self):
        for b in list(self._batches.values()) + list(self._full_batches.values()) + list(self._hier.values()):
            for buf in b.values():
                if isinstance(buf, _Buffer):
                    buf.destroy()
        self._batches.clear()
        self._full_batches.clear()
        self._hier.clear()
        self._uploaded = {"data": {}, "tmpl": {}}

    def destroy(self):
        self.clear_cache()
        for mod in self._modules.values():
            self.cuda.cuModuleUnload(mod)
        self._modules.clear()
        self._pipelines.clear()
        if self._start_event.value:
            self.cuda.cuEventDestroy_v2(self._start_event)
            self._start_event.value = 0
        if self._stop_event.value:
            self.cuda.cuEventDestroy_v2(self._stop_event)
            self._stop_event.value = 0
        if self.stream.value:
            self.cuda.cuStreamDestroy_v2(self.stream)
            self.stream.value = 0
        if self.ctx.value:
            self.cuda.cuCtxDestroy_v2(self.ctx)
            self.ctx.value = 0

    def __del__(self):
        self.destroy()
