"""The hierarchical search on every GPU, written once (stage U2.6, docs/unification-plan.md).

One recording per call shape runs every stage on the device, the counts never reaching the
host between them:

  feed      the tiers read the spectra in place (a stride and a data scale, twiddle.slang
            constants), where the driver specializes kernels when it creates them
            (inplace_feed); else a pack (packCoarse) writes each tier's band first, the fp16
            tier's scaled and packed. Or, when this call claims the deferred forward of these
            spectra
            (Executor._exec_pending), that forward is replaced by one that writes only what
            the tiers read -- the fp16 tier-0 band packed and scaled (forwardTier0) for an
            fp16 first tier, else the widest band in fp32 (seriesForwardBands, read in place)
            -- and the
            refine's blocks are recomputed in full afterwards (markBlocks, seriesForwardListed);
  tier 0    every pair at its band (the fp16 coarse role, its layout measured on the device,
            or the fp32 filter), compacted into a survivor list (compactPairs);
  tier 1    a cascade's second tier over those survivors (the listed refine at its band,
            deciding only), compacted again (compactListed);
  refine    the survivors at n (refineListedBounded), every bin;
  readback  the counts, and the peaks: dense, or sparse as the survivors' rows gathered on the
            host or the hits compacted on the device (a measured choice, flat peaks' rule).

Whether to claim the forward is the bytes model (band_forward_wanted) on the refine-block
fraction this shape measured last time, on every backend. Listed stages are bounded kernels:
a device with indirect dispatch sizes them by the count, one without strides a fixed grid
(the driver's `listed` op).
"""
import math
import os

from . import _config
import struct

import numpy as np

from ._gpuhost import (MAX_BINS, ROWWIN_ON, band_forward_wanted, band_windows, bin_shift,
                       coarse_span, hier_tiers, hier_window, refine_block_fraction, split_bins)
from ._shared import pack_half2, shared_view

#: Where the fp16 coarse tier's operands are put (_c16_scales): the packed templates' largest
#: component in [2^C16_TEMPLATE_EXP, 2^(C16_TEMPLATE_EXP+1)), leaving fp16's lower 18 octaves
#: for a template's own dynamic range, and the tier's threshold at 2^_c16_threshold_exp(band).
C16_TEMPLATE_EXP = 3
C16_THRESHOLD_EXP = 2
#: The threshold over the band, at least 2^C16_BAND_EXP: a band-B transform's values at
#: threshold are sums of B products, each ~thr/B, and those must stay well inside fp16's
#: normal range. Measured on the Iris Xe (flushes subnormals): at band 2048 a threshold of 4
#: left the bound 0.24% under the exact maximum and 8 used 72% of its margin; 16 and above
#: pass (tests/test_gpu_c16_bound.py). Set one octave past that: thr/band >= 2^-6.
C16_BAND_EXP = -6
#: Hierarchical calls that claimed the deferred forward of their spectra (tests and benches).
CLAIMS = [0]
#: The smallest normal float: a gate threshold of 0 passed as this passes the same pairs (a
#: nonzero maximum), and a later tier's compaction then dismisses the pairs it never saw.
_TINY = 1.1754944e-38


def c16_threshold_exp(band):
    """log2 of where the fp16 tier's threshold is put: 2^C16_THRESHOLD_EXP -- where production
    banks already sit (log2 thresholds 1.0-3.0 on the test27 ladder), |y|^2 = 16 at
    threshold, failing open only past 64x it -- raised with the band so thr/band stays at or
    above 2^C16_BAND_EXP (8 at band 512, 32 at 2048)."""
    return max(C16_THRESHOLD_EXP, int(band).bit_length() - 1 + C16_BAND_EXP)


def c16_template_exp(ct0):
    """The exponent the fp16 tier's packed templates are scaled by (2^et), from their largest
    component; 0 when there is nothing to place."""
    a = np.asarray(ct0)
    if a.size == 0:
        return 0
    tm = float(np.abs(np.asarray(a, np.complex64).view(np.float32)).max())
    if not (0.0 < tm < math.inf):
        return 0
    return int(max(-100, min(100, C16_TEMPLATE_EXP - math.floor(math.log2(tm)))))


def c16_data_exp(band, raw_thr, et):
    """The data exponent (2^ed, applied to each element before it is rounded to half) that puts
    the tier's threshold, raw_thr * 2^(et + ed), at 2^c16_threshold_exp(band). Powers of two,
    so in range every value is the unscaled one times an exact factor and the decision is
    unchanged; out of range they are what keeps it: on an Iris Xe, which flushes fp16
    subnormals, templates of ~5e-5 were flushed to zero and every pair dismissed."""
    if not (0.0 < float(raw_thr) < math.inf):
        return 0
    ed = int(round(c16_threshold_exp(band) - math.log2(float(raw_thr)) - et))
    return max(-100, min(100, ed))


def pow2_scaled(a, e):
    """a (complex) times 2^e, exactly (complex64); a itself when e is 0."""
    a = np.ascontiguousarray(a, np.complex64)
    if not e:
        return a
    return np.ldexp(a.view(np.float32), int(e)).view(np.complex64)


_F32 = struct.Struct("<f")
_U32 = struct.Struct("<I")


def _bits(x):
    """A float's float32 bits as a uint32 word (every call passes several: struct, not a
    NumPy scalar, which cost a fifth of a call's host time; out of float32 range, NumPy's
    inf)."""
    try:
        return _U32.unpack(_F32.pack(x))[0]
    except OverflowError:
        return int(np.float32(x).view(np.uint32))


class HierHandle:
    """A replay handle for one hier_peaks call (handle_out): the record, its bindings and
    words, and the input signatures it was valid for."""
    __slots__ = ("key", "rec", "binds", "dsig", "tsig", "storage", "shape", "sparse", "way",
                 "claim", "mode")

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def _count_names(ntiers, banded, compact):
    """The words a hierarchical record keeps in its one counts buffer, in order: each tier's
    survivor count (an indirect dispatch's [count, 1, 1]), the recompute's block count, and
    the compacted-hit count."""
    return (["args%d" % i for i in range(ntiers)] + (["bargs"] if banded else [])
            + (["count"] if compact else []))


def _rw_names(ntiers):
    return ["rw"] + ["rw%d" % i for i in range(ntiers)]


class HierOps:
    """The hierarchical operations of _gpuexec.Executor (a mixin of it)."""

    #: Pair-count bound a coarse layout is timed at (synthetic data), and the screen size
    #: every candidate is first timed at (a pathological layout is dropped before a
    #: full-size dispatch of it can run long enough for the driver to reset the device).
    _COARSE_PAIRS, _COARSE_SCREEN, _COARSE_NT = 16384, 1024, 16

    # ---- what the build shipped -------------------------------------------------------
    def _shipped(self, what, n):
        """_x_has_c16(n) (what "c16") or _x_has_kernel(what, n), asked of the driver once:
        the answer is a property of the installed build (a driver may look on disk)."""
        memo = self.__dict__.setdefault("_shipped_memo", {})
        got = memo.get((what, n))
        if got is None:
            got = memo[(what, n)] = bool(self._x_has_c16(n) if what == "c16"
                                         else self._x_has_kernel(what, n))
        return got

    # ---- the coarse layout ---------------------------------------------------------------
    def _coarse_layout(self, band):
        """(subgroup, pairs per group, templates per tile, twiddle table) of the fp16 coarse
        kernel at this band: the fastest of the device's candidates (_x_coarse_candidates),
        timed once on synthetic data and kept in MF_COST_FILE (_coarse.stored_measured_choice).
        Made once per band and MF_COARSE_LAYOUT value: every call asks."""
        from . import gatechain
        from ._coarse import forced_layout, stored_measured_choice
        holder = getattr(self, "_device_state", None) or self
        forced = forced_layout(band)
        made = holder.__dict__.setdefault("coarse_layout", {})
        layout = made.get((band, forced))
        if layout is not None:
            return layout
        memo = holder.__dict__.setdefault("coarse_choice", {})
        cands = self._x_coarse_candidates(band)
        layout = made[(band, forced)] = stored_measured_choice(
            memo, "coarse", getattr(self, "device_name", "") or getattr(self, "name", ""),
            band, cands, lambda c: self._layout_label(band, c),
            gatechain.gpu_kernel_id(self.kernel_family),
            lambda cs: self._time_coarse_layouts(band, cs),
            tiebreak=lambda c: (c[2], c[1], c[0]), forced=forced)
        return layout

    def _gate_use(self, band):
        """Whether a later gate tier at this band runs the one-bin refine's gate-only build,
        reporting the window's maximum alone (nbins word 0), rather than the one-bin
        election."""
        return (self._shipped("tier1", band) and self._shipped("tier1gate", band)
                and self._gate_way(band) == "gate")

    def _gate_way(self, band):
        """How a later gate tier reports at this band (tierb.slang MF_GATE_ONLY): "gate", the
        window's maximum alone from its own build, or "elect", the one-bin election --
        whichever this device runs faster, timed once on synthetic data and kept in
        MF_COST_FILE (stored_measured_choice). Measured per pair: gate 10-13% faster on the
        8060S, 12-18% on the M2, the tier halved on a RENOIR; within 1% on the L40S. The
        gate is its own build: compiled into the one-bin refine it cost that kernel
        registers (102 -> 127 at n = 512 on the L40S) and its tier 15%."""
        from . import gatechain
        from ._coarse import stored_measured_choice
        holder = getattr(self, "_device_state", None) or self
        made = holder.__dict__.setdefault("gate_way", {})
        way = made.get(band)
        if way is None:
            memo = holder.__dict__.setdefault("gate_choice", {})
            way = made[band] = stored_measured_choice(
                memo, "gateway", getattr(self, "device_name", "") or getattr(self, "name", ""),
                band, ("elect", "gate"), str, gatechain.gpu_kernel_id(self.kernel_family),
                lambda cs: self._time_gate_ways(band, cs))
        return way

    #: Tier-0 survivors per pair in the gate-way timing: a later tier runs over a sparse
    #: list with its grid sized for every pair, as a call dispatches it. Every pair listed
    #: timed only busy groups, and on the L40S picked the gate build (1-3% faster there)
    #: whose registers cost the search's leaf 4%: the idle groups are the cost.
    _GATE_SURVIVORS = 32

    def _time_gate_ways(self, band, ways):
        """Device seconds of the one-bin tier at this band in each way, over a synthetic
        batch whose survivors are one pair in _GATE_SURVIVORS, dispatched for every pair
        (_coarse.time_staged)."""
        from ._coarse import time_staged
        ntm, pairs = self._COARSE_NT, self._COARSE_PAIRS
        rng = np.random.default_rng(1)
        x = ((rng.standard_normal((pairs // ntm, band))
              + 1j * rng.standard_normal((pairs // ntm, band))) * 0.1).astype(np.complex64)
        bufs = [self._x_alloc(x.nbytes), self._x_alloc(ntm * band * 8),
                self._x_alloc(pairs * 4), self._x_alloc(pairs * 8),
                self._x_alloc(pairs * 4), self._x_alloc(16)]
        bufs[0].write(x)
        bufs[1].write(x[:ntm])
        surv = np.arange(0, pairs, self._GATE_SURVIVORS, dtype=np.uint32)
        bufs[4].write(surv)
        bufs[5].write(np.array([surv.size, 1, 1, 0], np.uint32))
        natives = []

        def time_way(way):
            kern = self._x_kernel("tier1", band, dict(stride=0, rowwin=False,
                                                      gate=(way == "gate")))
            lst = self._x_list("gate timing")
            lst.listed(kern, bufs[5], pairs, bufs,
                       (ntm, 0, band, band, bin_shift(band) & 0xFFFFFFFF,
                        0 if way == "gate" else 1, 0))
            native = lst.end()
            natives.append(native)
            return self._x_time(native, {}, 2)
        try:
            return time_staged([list(ways)], time_way, rounds=3)
        finally:
            for native in natives:
                self._x_release(native)
            for b in bufs:
                b.destroy()

    def coarse_layouts(self, band):
        """The names (_coarse.layout_label) of every coarse layout the choice may take at this
        band on this device; MF_COARSE_LAYOUT forces one."""
        return [self._layout_label(band, c) for c in self._x_coarse_candidates(band)]

    @staticmethod
    def _layout_label(band, c):
        from ._coarse import layout_label
        if len(c) > 4:                        # a driver's own gate (CUDA's tensor-core one)
            return "coarse_%s_%d_w%d" % (c[4], band, c[1])
        return layout_label(band, c[1], c[2], c[3], c[0])

    def _time_coarse_layouts(self, band, cands):
        """Device seconds per pair of each coarse layout on synthetic data (screened, then
        timed in interleaved rounds and confirmed: _coarse.time_staged)."""
        from ._coarse import time_staged
        ntm = self._COARSE_NT
        rng = np.random.default_rng(0)
        x = ((rng.standard_normal((self._COARSE_PAIRS // ntm, band))
              + 1j * rng.standard_normal((self._COARSE_PAIRS // ntm, band))) * 0.1
             ).astype(np.complex64)
        # Fed as calls feed it (_hier_record): fp32 rows read in place, or packed fp16 rows.
        rows = x if self.inplace_feed else pack_half2(x)
        data = self._x_alloc(rows.nbytes)
        data.write(rows)
        tmpl = self._x_alloc(ntm * band * 4)
        tmpl.write(pack_half2(x[:ntm]))
        cidx = self._x_alloc(self._COARSE_PAIRS * 4)
        cval = self._x_alloc(self._COARSE_PAIRS * 8)
        natives = []

        def time_at(layout, pairs):
            from ._coarse import coarse_launch
            nd = pairs // ntm
            kernel = self._coarse_kernel(band, layout, stride=band if self.inplace_feed else 0,
                                         scale=0, rowwin=False)
            slot_val, groups = coarse_launch(nd, ntm, layout[1], layout[2], band)
            groups = self._x_coarse_groups(kernel, groups)
            lst = self._x_list("coarse timing")
            lst.dispatch(kernel, groups, [data, tmpl, cidx, cval],
                         (ntm, 0, band, slot_val, band.bit_length() - 1, 1,
                          self._gate_bits(0.0, band, layout)))
            native = lst.end()
            natives.append(native)
            return self._x_time(native, {}, 2) / pairs

        def tiles(times):
            # Tiled layouts at the two fastest untiled (subgroup, ppg), and wherever no untiled
            # sibling was timed: a tile is skipped only when its untiled sibling lost.
            lead = {c[:2] for c in sorted(times, key=times.get)[:2]}
            timed = {c[:2] for c in times}
            return [c for c in cands if c[2] > 1 and (c[:2] in lead or c[:2] not in timed)]
        try:
            untiled = [c for c in cands if c[2] == 1]
            out = time_staged([untiled or cands] + ([tiles] if untiled and len(untiled) < len(cands)
                                                     else []),
                              lambda c: time_at(c, self._COARSE_PAIRS),
                              time_screen=lambda c: time_at(c, self._COARSE_SCREEN), rounds=3)
        finally:
            for native in natives:
                self._x_release(native)
            for b in (data, tmpl, cidx, cval):
                b.destroy()
        self.__dict__.setdefault("coarse_times", {}).setdefault(band, {}).update(
            {self._layout_label(band, c): v for c, v in out.items()})
        return out

    def _coarse_kernel(self, band, layout, stride, scale, rowwin):
        sg, ppg, tile, twt = layout[:4]
        return self._x_kernel("coarse", band, dict(sg=sg, ppg=ppg, tile=tile, twt=twt,
                                                   stride=stride, scale=scale, rowwin=rowwin,
                                                   layout=layout))

    @staticmethod
    def _x_coarse_groups(kernel, groups):
        """The groups a coarse dispatch launches: all of them (a driver whose kernel is
        persistent caps its grid)."""
        return groups

    def _gate_bits(self, thr, band, layout):
        """The coarse kernel's last word: for a tiled build whose pair fits one subgroup, the
        gate threshold as magnitude bits (tierb.slang peakTwoGate: only the pass and its
        bound, no election -- nothing reads tier 0's index); 0 elects (peakTwoWave)."""
        sg, _, tile, _ = layout[:4]
        if len(layout) > 4 or tile <= 1 or _config.get("MF_COARSE_RAW"):
            return 0
        if band // 16 > (sg or self.subgroup_size):
            return 0
        return _bits(max(float(thr), _TINY))

    # ---- the call ------------------------------------------------------------------------
    def hier_peaks(self, *args, **kwargs):
        """See _hier_peaks. A forward record this call claims is held against eviction
        until the call has submitted (_exec_claim)."""
        try:
            return self._hier_peaks(*args, **kwargs)
        finally:
            self.__dict__.pop("_exec_hold", None)

    def _hier_peaks(self, n, band, data, tmpl, ct0, raw_thr, binsize=None, threshold=0.0,
                   window=None, upload_data=True, upload_tmpl=True, cascade_band=None, ct1=None,
                   raw_thr1=None, slot=None, async_submit=False, sparse=False, row_windows=None,
                   handle_out=None, refine_reach=None, nbins=None):
        """Hierarchical peaks: (idx, val) shaped (data rows, templates, bins) as peaks returns,
        or a _SparsePeaks when sparse, from one recording that gates every pair at a narrow
        band (one tier, or a cascade of two) and refines only the survivors at n.

        band/ct0/raw_thr are the gate tier (the band, its templates and its raw threshold);
        a cascade's tier 0 is cascade_band/ct0/raw_thr and tier 1 band/ct1/raw_thr1
        (_gpuhost.hier_tiers also takes pairs). row_windows (hier_peaks_grouped): (groups,
        uint32 [lo, hi] per data row) narrows each row's window on the device. handle_out (a
        list): receives a handle hier_replay takes. nbins: at least this many bins (a grouped
        call's rows with bin phases can need more than any window of n holds)."""
        band, ct0, raw_thr, cascade_band, ct1, raw_thr1 = hier_tiers(
            n, band, ct0, raw_thr, cascade_band, ct1, raw_thr1)
        nd, nt = data.shape[0], tmpl.shape[0]
        lo, hi, binsize, wbins = hier_window(n, window, binsize)
        nbins = wbins if nbins is None else max(wbins, int(nbins))
        rw_key = None if row_windows is None else row_windows[0]
        rw = None if row_windows is None else row_windows[1]
        if nbins > MAX_BINS:
            if rw is not None:
                raise ValueError("grouped dispatch exceeds the kernel bin limit")
            return split_bins(
                lambda w, ud, ut: self.hier_peaks(
                    n, band, data, tmpl, ct0, raw_thr, binsize=binsize, threshold=threshold,
                    window=w, upload_data=ud, upload_tmpl=ut, cascade_band=cascade_band,
                    ct1=ct1, raw_thr1=raw_thr1, slot=slot, refine_reach=refine_reach),
                lo, hi, binsize, MAX_BINS, upload_data, upload_tmpl, sparse, async_submit)
        if cascade_band is not None:
            tiers = ((int(cascade_band), ct0, float(raw_thr)), (int(band), ct1, float(raw_thr1)))
            if not tiers[0][0] < tiers[1][0] < n:
                raise ValueError("cascade bands must increase below n: %r"
                                 % ((tiers[0][0], tiers[1][0]),))
        else:
            tiers = ((int(band), ct0, float(raw_thr)),)
        for i, (b, ct, _) in enumerate(tiers):
            if ct.shape != (nt, b):
                raise ValueError("tier-%d coarse templates must be (%d, %d), got %s"
                                 % (i, nt, b, ct.shape))
        bands = tuple(b for b, _, _ in tiers)
        half = self._shipped("c16", bands[0])          # the fp16 coarse role at tier 0
        layout = self._coarse_layout(bands[0]) if half else None
        shift = bin_shift(binsize)
        t2 = float(threshold) ** 2 if threshold > 0 else 0.0
        top = max(bands)

        dv, tv = shared_view(data, self), shared_view(tmpl, self)
        # The feed: claim the deferred forward of these spectra when its bands move fewer
        # bytes than the full spectra (band_forward_wanted). It is a function of the call,
        # never of earlier ones: the feeds round differently (different FFT routes before
        # the fp16 step), so a fraction measured on an earlier call made a batch and the same
        # calls made one by one disagree on pairs within an fp16 step of a gate's threshold.
        # The call's refine-block fraction lies between refine_reach (a pair's modelled
        # probability of reaching the refine; a block refines at least as often as any of its
        # pairs) and 1 - (1 - reach)^templates (independent pairs). The lower bound prices
        # it, so the full forward is taken only when it moves fewer bytes for certain: the
        # upper bound took it on the production profile, where bank neighbours trigger
        # together, and lost 3.8% on the 8060S ladder.
        feed = "inplace" if self.inplace_feed else "pack"
        claim = None
        frac_key = (n, top, nd, nt)
        banded = band_forward_wanted(
            n, top, None if refine_reach is None else min(max(float(refine_reach), 0.0), 1.0))
        tier0_ok = half and self._shipped("fwd_tier0", n)
        if dv is not None and (tier0_ok or self.inplace_feed) and banded:
            claim = self._exec_claim(slot, data, nd)
            if claim is not None:
                CLAIMS[0] += 1
                feed = "tier0" if tier0_ok else "bands"
        # Each tier's input and its stride: the spectra rows (n), the band rows, or packed.
        ed = 0
        et = 0
        storage_key = ("hierstore", n, bands, nd, nt, nbins, rw_key is not None,
                       dv is not None and data.ctypes.data, tv is not None and tmpl.ctypes.data,
                       slot if async_submit else None)
        uploads = self._input_uploads(storage_key, data, tmpl, upload_data, upload_tmpl)
        if half:
            held = self.__dict__.setdefault("_c16_template_exp", {})
            if uploads[1] or storage_key not in held:
                held[storage_key] = c16_template_exp(ct0)
            et = held[storage_key]
            ed = c16_data_exp(bands[0], tiers[0][2], et)
        self._last_c16_scale = 2.0 ** (et + ed)         # tier-0 values / this = unscaled
        way, trial = (self._sparse_way(("hier", n, bands, nd, nt, nbins)) if sparse
                      else ("dense", None))
        key = ("hier", n, bands, nd, nt, nbins, layout, feed, way, rw_key is not None, ed,
               storage_key)
        table = self._exec_table()
        rec = table.get(key)
        fresh = rec is None
        if fresh:
            rec = self._hier_record(key, n, tiers, nd, nt, nbins, layout, half, feed, way, rw,
                                    ed, dv, tv, data, tmpl, claim)
            table[key] = rec
        self._cache_touch(key)
        self._claim(rec.buffers["idx"])          # an earlier result still reading these outputs
        if fresh:
            uploads = (True, True, *uploads[2:])
        self._hier_upload(rec, storage_key, uploads, data, tmpl, tiers, half, et, slot)
        if rw is not None:
            # Every row-window table in one upload, each at its section (_hier_record).
            span = (self._section_offset(rec.buffers, "rw0")
                    - self._section_offset(rec.buffers, "rw"))
            tables = [np.ascontiguousarray(rw, np.uint32)] + [band_windows(rw, n, b)
                                                              for b in bands]
            packed = np.zeros((len(tables), span // 4), np.uint32)
            for j, t in enumerate(tables):
                packed[j, :t.size] = t.reshape(-1)
            self._x_upload(rec.buffers["rws"], packed, slot)

        binds = self._hier_binds(n, tiers, nd, nt, nbins, lo, hi, binsize, shift, t2, half, ed,
                                 et, rw is not None, layout, claim, data)
        shape = (nd, nt, nbins)
        mode = (frac_key, feed in ("tier0", "bands") or banded) if dv is not None else None
        if handle_out is not None:
            handle_out.append(HierHandle(
                key=key, rec=rec, binds=binds, dsig=self._uploaded["data"].get(storage_key),
                tsig=self._uploaded["tmpl"].get(storage_key), storage=storage_key, shape=shape,
                sparse=sparse, way=way, claim=claim is not None, mode=mode))
        return self._hier_run(rec, binds, shape, sparse, way, len(tiers) > 1,
                              frac_key if dv is not None else None, slot, async_submit, trial)

    def _hier_upload(self, rec, storage_key, uploads, data, tmpl, tiers, half, et, slot):
        """Inputs found stale (_input_uploads): the spectra and templates where the record owns
        them, and the tiers' templates -- the fp16 tier's packed at 2^et -- always."""
        if uploads[0] and "data" in rec.owned:
            self._x_upload(rec.buffers["data"], np.ascontiguousarray(data, np.complex64), slot)
        if uploads[0]:
            self._uploaded["data"][storage_key] = uploads[2]
        if uploads[1]:
            if "tmpl" in rec.owned:
                self._x_upload(rec.buffers["tmpl"], np.ascontiguousarray(tmpl, np.complex64),
                               slot)
            for i, (_, ct, _) in enumerate(tiers):
                self._x_upload(rec.buffers["ct%d" % i],
                               pack_half2(pow2_scaled(ct, et)) if i == 0 and half
                               else np.ascontiguousarray(ct, np.complex64), slot)
            self._uploaded["tmpl"][storage_key] = uploads[3]

    def _hier_record(self, key, n, tiers, nd, nt, nbins, layout, half, feed, way, rw, ed, dv,
                     tv, data, tmpl, claim):
        """Buffers and the recording of one call shape (see the module docstring)."""
        from ._coarse import coarse_launch
        from ._gpuexec import Arg, Record
        bands = tuple(b for b, _, _ in tiers)
        last = len(tiers) - 1
        pairs = nd * nt
        out = pairs * nbins
        rowwin = rw is not None
        cb0 = 4 if half else 8
        estimate = (sum(a.nbytes for a, v in ((data, dv), (tmpl, tv)) if v is None)
                    + sum((cb0 if i == 0 else 8) * b * nt for i, b in enumerate(bands))
                    + pairs * (12 * len(bands) + 4) + out * 12 + 64
                    + (nd * (bands[0] * cb0 + (bands[1] * 8 if last else 0))
                       if feed in ("tier0", "pack") else nd * max(bands) * 8 if feed == "bands"
                       else 0)
                    + (out * 16 if way == "compact" else 0))
        self._exec_room(estimate, [v for v in (dv, tv) if v is not None])
        rec = Record()
        buf = lambda name, nbytes, **kw: self._exec_buffer(rec, name, nbytes=nbytes, **kw)
        bd = self._exec_buffer(rec, "data", dv, data.nbytes)
        bt = self._exec_buffer(rec, "tmpl", tv, tmpl.nbytes)
        for i, b in enumerate(bands):
            buf("ct%d" % i, nt * b * (cb0 if i == 0 else 8), upload=True)
            buf("cidx%d" % i, pairs * 4)
            buf("cval%d" % i, pairs * 8)
            buf("surv%d" % i, pairs * 4, readback=i == last)
        # Small words share one buffer each way (one update, one readback; one upload of the
        # row windows): a buffer each made 5 readbacks and 7 uploads a call where 1ccbbe4b's
        # CUDA path made 3 and 4, 12% of the L40S fine stage at n=4096.
        align = max(16, int(self.storage_offset_alignment))
        names = _count_names(len(bands), feed in ("tier0", "bands"), way == "compact")
        counts = buf("counts", align * len(names), readback=True)
        for j, name in enumerate(names):
            rec.buffers[name] = self._x_section(counts, j * align, 16)
        bi = buf("idx", out * 4, readback=True)
        bv = buf("val", out * 8, readback=True)
        if rowwin:
            # (lo, hi, bin phase) per row: tierb.slang ROWWIN_WORDS.
            span = -(-nd * 12 // align) * align
            rws = buf("rws", span * (len(bands) + 1), upload=True)
            for j, name in enumerate(_rw_names(len(bands))):
                rec.buffers[name] = self._x_section(rws, j * span, nd * 12)
        if feed in ("tier0", "pack"):
            buf("band0", nd * bands[0] * cb0)
            buf("band1", nd * bands[1] * 8 if last else 16)
        elif feed == "bands":
            buf("bands", nd * max(bands) * 8)
        if feed in ("tier0", "bands"):
            buf("flags", nd * 4)
            buf("blist", nd * 4)
        if way == "compact":
            buf("list", out * 16, readback=True)

        B = rec.buffers
        S = lambda name: B[name]
        rws = lambda name: [B[name]] if rowwin else []
        lst = self._x_list("hierarchical")
        lst.stamp("start")
        # The feed's forward, when this call claimed the deferred one.
        if feed == "tier0":
            lst.dispatch(self._x_kernel("fwd_tier0", n), nd,
                         [Arg("series"), Arg("starts"), B["band0"], B["band1"]],
                         (Arg("tier0", 5),))
            lst.barrier()
            lst.stamp("forward")
        elif feed == "bands":
            lst.dispatch(self._x_kernel("fwd_bands", n), nd,
                         [Arg("series"), Arg("starts"), B["bands"]], (Arg("bands", 3),))
            lst.barrier()
            lst.stamp("forward")
        # Counts to zero (an indirect dispatch's [count, 1, 1]), in one update; dense outputs
        # to "nothing".
        words = []
        for name in names:
            words += [0, 0, 0, 0] if name == "count" else [0, 1, 1, 0]
            words += [0] * (align // 4 - 4)
        lst.update(counts, words)
        if feed in ("tier0", "bands"):
            lst.fill(B["flags"], 0)
        if way != "rows":
            lst.fill(bi, 0xFFFFFFFF)
            lst.fill(bv, 0)
        lst.barrier()
        lst.stamp("fill")
        if feed == "pack":
            # Each tier's band from the spectra: the fp16 tier's packed at its data scale.
            for i, b in enumerate(bands):
                h = int(i == 0 and half)
                lst.dispatch(self._x_kernel("pack", n), (nd * b + 255) // 256,
                             [bd, B["band%d" % i]],
                             (n, b, nd * b, h, _bits(2.0 ** ed if h else 1.0)))
            lst.barrier()
            lst.stamp("pack")
        # Tier inputs: (buffer, row stride in elements (0: the tier's own band), data scale
        # exponent applied as the tier reads it).
        if feed == "inplace":
            src = [(bd, n, ed if (i == 0 and half) else 0) for i in range(len(bands))]
        elif feed == "bands":
            src = [(B["bands"], max(bands), ed if (i == 0 and half) else 0)
                   for i in range(len(bands))]
        else:                                   # tier0 or pack: the bands as written
            src = [(B["band0"], 0, 0)] + ([(B["band1"], 0, 0)] if last else [])
        for i, b in enumerate(bands):
            sbuf, stride, scale = src[i]
            if i == 0:
                if half:
                    kern = self._coarse_kernel(b, layout, stride, scale, rowwin)
                    _, groups = coarse_launch(nd, nt, layout[1], layout[2], 0)
                    groups = self._x_coarse_groups(kern, groups)
                else:
                    kern = self._x_kernel("gate", b, dict(stride=stride, rowwin=rowwin))
                    groups = pairs
                lst.dispatch(kern, groups, [sbuf, S("ct0"), S("cidx0"), S("cval0")] + rws("rw0"),
                             (Arg("coarse", 7),))
                lst.barrier()
                lst.stamp("coarse0")
                lst.dispatch(self._x_kernel("compact", n), (pairs + 255) // 256,
                             [S("cval0"), S("surv0"), S("args0")], (Arg("compact0", 3),))
            else:
                one = self._shipped("tier1", b)
                kern = self._x_kernel("tier1" if one else "tier", b,
                                      dict(stride=stride, rowwin=rowwin,
                                           gate=one and self._gate_use(b)))
                lst.listed(kern, S("args0"), pairs,
                           [sbuf, S("ct1"), S("cidx1"), S("cval1"), S("surv0"), S("args0")]
                           + rws("rw1"), (Arg("tier", 7),))
                lst.barrier()
                lst.stamp("coarse1")
                lst.dispatch(self._x_kernel("compactl", n), (pairs + 255) // 256,
                             [S("cval1"), S("surv1"), S("args1"), S("surv0"), S("args0")],
                             (Arg("compact1", 3),))
            lst.barrier()
            lst.stamp("compact%d" % i)
        survs, sargs = "surv%d" % last, "args%d" % last
        if feed in ("tier0", "bands"):
            # The refine reads the full spectra of its survivors' blocks: recompute those.
            lst.dispatch(self._x_kernel("mark", n), (pairs + 255) // 256,
                         [S(survs), S(sargs), B["flags"], B["blist"], B["bargs"]], (nt,))
            lst.barrier()
            lst.stamp("mark")
            lst.listed(self._x_kernel("fwd_listed", n), B["bargs"], nd,
                       [Arg("series"), Arg("starts"), bd, B["blist"], B["bargs"]],
                       (Arg("listed", 2),))
            lst.barrier()
            lst.stamp("recompute")
        lst.listed(self._x_kernel("refine1" if nbins == 1 else "refine", n,
                                  dict(rowwin=rowwin)), S(sargs), pairs,
                   [bd, bt, bi, bv, S(survs), S(sargs)] + rws("rw"), (Arg("refine", 7),))
        lst.barrier()
        lst.stamp("refine")
        if way == "compact":
            # Its own phase: a fused batch runs a phase's work unordered (see stamp).
            lst.dispatch(self._x_kernel("compact_peaks", n), (out + 255) // 256,
                         [bi, bv, B["count"], B["list"]], (out, out))
            lst.barrier()
            lst.stamp("peaks")
        # What the host reads: the counts, then the peaks as `way` reads them.
        lst.readback(counts, align * len(names))
        if dv is not None and way != "rows":
            # The survivors: the refine-block fraction every call on shared spectra notes.
            lst.readback(S(survs), pairs * 4)
        if way == "dense":
            lst.readback(bi, out * 4)
            lst.readback(bv, out * 8)
        elif way == "rows":
            lst.readback(S(survs), pairs * 4)
            lst.readback(bi, out * 4)
            lst.readback(bv, out * 8)
        else:
            lst.readback(B["list"], min(out, self._SPARSE_FIRST) * 16)
        rec.native = lst.end()
        return rec

    def _hier_binds(self, n, tiers, nd, nt, nbins, lo, hi, binsize, shift, t2, half, ed, et,
                    rowwin, layout, claim, data):
        """The per-run words and bindings of a hier_peaks call."""
        from ._coarse import coarse_launch
        pairs = nd * nt
        binds = {}
        start = (lambda first: ROWWIN_ON) if rowwin else (lambda first: first)
        b0, _, thr0 = tiers[0]
        cs, ce, csp, csh = coarse_span(n, b0, lo, hi)
        thr0 = thr0 * (2.0 ** (et + ed) if half else 1.0)
        if half:
            slot_val, _ = coarse_launch(nd, nt, layout[1], layout[2], csp)
            binds["coarse"] = (nt, start(cs), ce, slot_val, csh & 0xFFFFFFFF, 1,
                               self._gate_bits(thr0, b0, layout))
        else:
            binds["coarse"] = (nt, start(cs), ce, csp, csh & 0xFFFFFFFF, 1, 0)
        binds["compact0"] = (pairs, _bits(thr0), nbins)
        if len(tiers) > 1:
            b1, _, thr1 = tiers[1]
            cs1, ce1, csp1, csh1 = coarse_span(n, b1, lo, hi)
            # nbins 0 asks a one-bin build for the gate's decision alone (tierb.slang gateOnly).
            # nbins 0 asks a one-bin build for the gate's decision alone, where it is faster.
            gate = self._gate_use(b1)
            binds["tier"] = (nt, start(cs1), ce1, csp1, csh1 & 0xFFFFFFFF, 0 if gate else 1, 0)
            # The pairs tier 0 dismissed hold zeros: the smallest normal float dismisses them.
            binds["compact1"] = (pairs, _bits(max(thr1, _TINY)), nbins)
        binds["refine"] = (nt, start(lo), hi, binsize, shift & 0xFFFFFFFF, nbins, _bits(t2))
        if claim is not None:
            series, starts, row, count, nser, code = claim
            binds["series"], binds["starts"] = series, starts
            binds["listed"] = (nser, code)
            b1 = tiers[1][0] if len(tiers) > 1 else 0
            binds["tier0"] = (nser, b0, b1, _bits(2.0 ** ed if half else 1.0), code)
            binds["bands"] = (nser, max(b for b, _, _ in tiers), code)
        return binds

    def _sparse_way(self, shape):
        """(way, record or None): how this shape reads a sparse result -- its survivors'
        rows gathered on the host, or the hits compacted on the device -- an online
        _choice.Choice per shape, as for flat peaks (_gpuexec.SPARSE_WAYS)."""
        from . import _choice
        from ._gpuexec import SPARSE_WAYS, _SPARSE_SCHEDULE
        return _choice.choice("sparse-way", ("hier",) + tuple(shape), SPARSE_WAYS["hier"],
                              scope=self.__dict__, **_SPARSE_SCHEDULE).next()

    def _hier_run(self, rec, binds, shape, sparse, way, cascade, frac_key, slot,
                  async_submit, trial=None):
        """Run a recorded call and return its result (a tracked collector when async).
        frac_key: where the call notes its refine-block fraction (a call on shared spectra,
        banded or not: the next call's band/full choice reads it), or None.
        trial: the sparse-way choice's record for this call (a synchronous call only)."""
        import time
        timed = trial is not None and not async_submit
        t0 = time.perf_counter()
        wait = self._exec_submit(rec.native, binds, slot, rec) if async_submit else None
        if wait is None:
            self._exec_run(rec.native, True, binds, slot, rec)

        def result():
            if wait is not None:
                wait()
            res = self._hier_result(rec, shape, sparse, way, cascade, frac_key)
            if timed:
                trial(time.perf_counter() - t0)
            return res
        return self._track(result, owner=rec.buffers["idx"]) if async_submit else result()

    def _hier_result(self, rec, shape, sparse, way, cascade, frac_key):
        """The call's peaks from its readback buffers. Counts, survivors and the rows a
        sparse result gathers are read in place where the host sees the buffers (_x_view):
        only a dense result copies its outputs whole."""
        from ._results import _SparsePeaks
        nd, nt, nbins = shape
        pairs, out = nd * nt, nd * nt * nbins
        B = rec.buffers
        last = 1 if cascade else 0
        words = self._x_view(B["counts"], np.uint32, B["counts"].nbytes // 4)
        at = lambda name: int(words[self._section_offset(B, name) // 4])
        count = at("args%d" % last)
        self.last_refinements = count
        if cascade:
            self.last_tier1_survivors = at("args0")
        rows = None
        if frac_key is not None or (sparse and way == "rows"):
            rows = self._x_view(B["surv%d" % last], np.uint32, count)
        if frac_key is not None:
            from . import gatechain
            # Measured for the cost model's forward pricing (not for the feed: see
            # _hier_peaks).
            gatechain.note_refine_blocks(frac_key[0], frac_key[1],
                                         refine_block_fraction(rows, nt, nd))
        if not sparse:
            if count == 0:
                return (np.full(shape, -1, np.int32), np.zeros(shape, np.complex64))
            idx = np.empty(out, np.int32)
            val = np.empty(out, np.complex64)
            self._x_read(B["idx"], idx)
            self._x_read(B["val"], val)
            return idx.reshape(shape), val.reshape(shape)
        empty = np.empty(0, np.int64)
        if count == 0:
            return _SparsePeaks(shape, empty, empty, np.empty(0, np.complex64))
        if way == "rows":
            ri = self._x_view(B["idx"], np.int32, out).reshape(pairs, nbins)[rows]
            k, b = np.nonzero(ri >= 0)
            if not k.size:
                return _SparsePeaks(shape, empty, empty, np.empty(0, np.complex64))
            rk = rows[k].astype(np.int64)
            flat = rk * nbins + b
            order = np.argsort(flat)
            val = self._x_view(B["val"], np.complex64, out).reshape(pairs, nbins)
            return _SparsePeaks(shape, flat[order], ri[k, b][order], val[rk, b][order])
        c = at("count")
        recs = self._x_view(B["list"], np.uint32, 4 * c).reshape(c, 4)
        pos = recs[:, 0].astype(np.int64)
        order = np.argsort(pos)                 # positions are distinct: C order
        recs = recs[order]
        v = recs[:, 2:4].copy().view(np.float32).view(np.complex64).reshape(-1)
        return _SparsePeaks(shape, pos[order], recs[:, 1].view(np.int32), v)

    @staticmethod
    def _section_offset(B, name):
        sec = B[name]
        off = getattr(sec, "offset", None)
        return off if off is not None else sec[2]          # a driver section, or a test's

    # ---- replay --------------------------------------------------------------------------
    def hier_valid(self, h):
        """Whether hier_replay(h) would submit: the record is the one the handle saw and both
        inputs are still resident under the signatures it saw. (The band/full feed is a
        function of the call, so a replay of the same call takes the same one.)"""
        return (self._exec_table().get(h.key) is h.rec
                and self._uploaded["data"].get(h.storage) == h.dsig
                and self._uploaded["tmpl"].get(h.storage) == h.tsig)

    def hier_replay(self, h, slot, async_submit, validated=False):
        """Submit a hier_peaks call again from its handle, or None if the handle is stale.
        validated=True: the caller checked hier_valid for every part of a call first."""
        if not validated and not self.hier_valid(h):
            return None
        self._cache_touch(h.key)
        if h.claim:
            CLAIMS[0] += 1
            self._exec_claim(slot, None, h.shape[0])      # the replayed forward it replaces
        return self._hier_run(h.rec, h.binds, h.shape, h.sparse, h.way, "args1" in h.rec.buffers,
                              h.mode[0] if h.mode is not None else None, slot, async_submit)
