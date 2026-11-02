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
import hashlib
import math

import struct

import numpy as np

from ._gpuhost import (MAX_BINS, ROWWIN_ON, band_windows, bin_shift,
                       coarse_span, hier_tiers, hier_window, split_bins)
from .gatechain import band_forward_wanted
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
    words, the input signatures it was valid for, and the kernel slots the call consulted
    with the values it ran (slots: ((what, band, (default, alternative)), ...); values)."""
    __slots__ = ("key", "rec", "binds", "dsig", "tsig", "storage", "shape", "sparse", "way",
                 "claim", "slots", "values")

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def _count_names(ntiers, banded, compact, direct=False):
    """The words a hierarchical record keeps in its one counts buffer, in order: each tier's
    survivor count (an indirect dispatch's [count, 1, 1]), the direct refine's fallback count,
    the recompute's block count, and the compacted-hit count."""
    return (["args%d" % i for i in range(ntiers)] + (["fbargs"] if direct else [])
            + (["bargs"] if banded else []) + (["count"] if compact else []))


def _rw_names(ntiers):
    return ["rw"] + ["rw%d" % i for i in range(ntiers)]


class HierOps:
    """The hierarchical operations of _gpuexec.Executor (a mixin of it)."""

    #: True on GPU backends whose packed half2 ALU throughput exceeds fp32 (RDNA, CUDA).
    packed_fp16 = True

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

    # ---- the coarse layout and gate way: shortlists the device trial plays ----------------
    def _kernel_pair(self, what, band):
        """(first, second or None) of a kernel decision at this band (what: "coarse", the fp16
        coarse layout of tier 0 -- (subgroup, pairs per group, templates per tile, twiddle
        table); "gateway", how a later tier reports): the device's offline screen's fastest
        two on synthetic dispatches (_coarse.shortlist, kept in MF_COST_FILE). The device
        trial plays them on real batches (kernel slots, _settings.slot). MF_COARSE_LAYOUT
        forces a layout, unplayed. Made once per band and setting: every call asks."""
        from . import gatechain
        from ._coarse import forced_layout, shortlist
        holder = getattr(self, "_device_state", None) or self
        forced = forced_layout(band) if what == "coarse" else None
        made = holder.__dict__.setdefault("kernel_pairs", {})
        pair = made.get((what, band, forced))
        if pair is not None:
            return pair
        memo = holder.__dict__.setdefault("screens", {})
        device = getattr(self, "device_name", "") or getattr(self, "name", "")
        kid = gatechain.gpu_kernel_id(self.kernel_family)
        if what == "coarse":
            pair = shortlist(memo, "coarse", device, band, self._x_coarse_candidates(band),
                             lambda c: self._layout_label(band, c), kid,
                             lambda cs: self._time_coarse_layouts(band, cs),
                             tiebreak=lambda c: (c[2], c[1], c[0]), forced=forced)
        else:
            pair = shortlist(memo, "gateway", device, band, ("elect", "gate"), str, kid,
                             lambda cs: self._time_gate_ways(band, cs))
        made[(what, band, forced)] = pair
        return pair

    def _played(self, what, band):
        """The kernel decision a call runs at this band: the screen's fastest, or its
        runner-up where the device trial plays or locked it (_settings.slot)."""
        first, second = self._kernel_pair(what, band)
        if second is None:
            return first
        from ._settings import slot as kernel_slot
        a, b = self._slot_labels(what, band, (first, second))
        return second if kernel_slot(self._dev_name(), what, band, a, b) == b else first

    def _slot_labels(self, what, band, pair):
        """A kernel pair's labels as its slot names them."""
        if what == "coarse":
            return tuple(self._layout_label(band, c) for c in pair)
        return tuple(str(c) for c in pair)

    def _coarse_layout(self, band):
        """The fp16 coarse layout a call runs at this band (_played "coarse")."""
        return self._played("coarse", band)

    def _dev_name(self):
        holder = getattr(self, "_device_state", None) or self
        return (getattr(holder, "device_name", "") or getattr(self, "device_name", "")
                or getattr(self, "name", ""))

    def _gate_use(self, band):
        """Whether a later gate tier at this band runs the one-bin refine's gate-only build,
        reporting the window's maximum alone (nbins word 0), rather than the one-bin election
        (tierb.slang MF_GATE_ONLY or peakTwoGate) -- measured per pair (_played "gateway")."""
        if self.packed_fp16 and self._shipped("c16", band) and self._shipped("tier1_c16", band):
            if band // 16 > self.subgroup_size:
                return False
            return self._played("gateway", band) == "gate"
        if not (self._shipped("tier1", band) and self._shipped("tier1gate", band)):
            return False
        return self._played("gateway", band) == "gate"

    #: Tier-0 survivors per pair in the gate-way timing: a later tier runs over a sparse
    #: list with its grid sized for every pair, as a call dispatches it. Every pair listed
    #: timed only busy groups, and on the L40S picked the gate build (1-3% faster there)
    #: whose registers cost the search's leaf 4%: the idle groups are the cost.
    _GATE_SURVIVORS = 32

    def _time_gate_ways(self, band, ways):
        """Device seconds of the one-bin tier at this band in each way, over a synthetic
        batch whose survivors are one pair in _GATE_SURVIVORS, dispatched for every pair
        (_coarse.screen)."""
        from ._coarse import screen
        ntm, pairs = self._COARSE_NT, self._COARSE_PAIRS
        rng = np.random.default_rng(1)
        x = ((rng.standard_normal((pairs // ntm, band))
              + 1j * rng.standard_normal((pairs // ntm, band))) * 0.1).astype(np.complex64)
        c16 = (self.packed_fp16 and self._shipped("c16", band)
               and self._shipped("tier1_c16", band) and band // 16 <= self.subgroup_size)
        drows = (x if self.inplace_feed else pack_half2(x)) if c16 else x
        trows = pack_half2(x[:ntm]) if c16 else x[:ntm]
        bufs = [self._x_alloc(drows.nbytes), self._x_alloc(trows.nbytes),
                self._x_alloc(pairs * 4), self._x_alloc(pairs * 8),
                self._x_alloc(pairs * 4), self._x_alloc(16), self._x_alloc(16)]
        bufs[0].write(drows)
        bufs[1].write(trows)
        surv = np.arange(0, pairs, self._GATE_SURVIVORS, dtype=np.uint32)
        bufs[4].write(surv)
        bufs[5].write(np.array([surv.size, 1, 1, 0], np.uint32))
        ppg = max(1, 1024 // band)
        groups = -(-surv.size // (2 * ppg)) if c16 else surv.size
        max_groups = -(-pairs // (2 * ppg)) if c16 else pairs
        bufs[6].write(np.array([groups, 1, 1, 0], np.uint32))
        natives = []

        def time_way(way):
            is_gate = (way == "gate")
            if c16:
                kern = self._x_kernel("tier1_c16", band,
                                      dict(stride=band if self.inplace_feed else 0, scale=0,
                                           rowwin=False, twt=1))
                lst = self._x_list("gate timing")
                lst.listed(kern, bufs[6], max_groups, bufs[:6],
                           (ntm, 0, band, band, bin_shift(band) & 0xFFFFFFFF,
                            0 if is_gate else 1, _bits(4.0) if is_gate else 0))
            else:
                kern = self._x_kernel("tier1", band, dict(stride=0, rowwin=False, gate=is_gate))
                lst = self._x_list("gate timing")
                lst.listed(kern, bufs[5], pairs, bufs[:6],
                           (ntm, 0, band, band, bin_shift(band) & 0xFFFFFFFF,
                            0 if is_gate else 1, 0))
            native = lst.end()
            natives.append(native)
            return self._x_time(native, {}, 2)
        try:
            return screen([list(ways)], time_way, rounds=3)
        finally:
            for native in natives:
                self._x_release(native)
            for b in bufs:
                b.destroy()

    def time_direct_ratio(self, n, real_series=False, complex_taps=False):
        """Device time of one direct-refine (lag x tap) divided by one length-n FFT refine pair,
        measured on synthetic survivor dispatches in interleaved rounds (_coarse.screen)."""
        from ._coarse import screen
        ntm, pairs = self._COARSE_NT, 4096
        nd = pairs // ntm
        tap_count = min(256, max(16, n // 4))
        tap_stride = (tap_count + 3) & ~3
        cplx = bool(complex_taps)
        row_words = 4 + (2 * tap_stride if cplx else tap_stride)
        tap_meta = (tap_stride << 1) | int(cplx)
        last_band = max(64, n // 4)
        r_step = max(1, n // last_band)
        hw = 6 if n >= 1024 else max(1, (n // 8) // r_step)
        m_lags = 2 * hw * r_step + 1
        ce_idx = (n // 2) // r_step
        rng = np.random.default_rng(3)
        x = ((rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))) * 0.1
             ).astype(np.complex64)
        starts_arr = np.arange(nd, dtype=np.uint32) * (2 * n if real_series else n)
        series_length = 2 * nd * n if real_series else nd * n
        series_layout = 1 if real_series else 0
        taps_arr = np.zeros((ntm, row_words), np.uint32)
        taps_arr[:, 0] = tap_count
        thr_bits = _bits(1e30)
        surv = np.arange(0, pairs, 4, dtype=np.uint32)
        nsurv = int(surv.size)
        bufs = [self._x_alloc(x.nbytes), self._x_alloc(starts_arr.nbytes),
                self._x_alloc(taps_arr.nbytes), self._x_alloc(pairs * 4),
                self._x_alloc(pairs * 8), self._x_alloc(pairs * 4), self._x_alloc(16),
                self._x_alloc(pairs * 4), self._x_alloc(16), self._x_alloc(pairs * 4),
                self._x_alloc(pairs * 8), self._x_alloc(ntm * n * 8),
                self._x_alloc(nd * n * 8), self._x_alloc(nd * 4), self._x_alloc(16)]
        bufs[0].write(x)
        bufs[1].write(starts_arr)
        bufs[2].write(taps_arr)
        bufs[3].write(np.full(pairs, ce_idx, np.int32))
        bufs[4].write(np.ones(pairs, np.complex64))
        bufs[5].write(np.pad(surv, (0, pairs - nsurv)))
        bufs[6].write(np.array([nsurv, 1, 1, 0], np.uint32))
        bufs[8].write(np.array([0, 1, 1, 0], np.uint32))
        bufs[11].write(x[:ntm])
        bufs[12].write(x)
        bufs[13].write(np.arange(nd, dtype=np.uint32))
        bufs[14].write(np.array([nd, 1, 1, 0], np.uint32))
        natives = []

        def time_kind(kind):
            lst = self._x_list("direct ratio timing")
            if kind == "td":
                kern = self._x_kernel("refine_td", n, dict(rowwin=False))
                lst.listed(kern, bufs[6], pairs, bufs[:11],
                           (n, last_band, ntm, 0, series_length, series_layout, tap_meta, hw,
                            0xFFFFFFFF, 0, n, n, bin_shift(n) & 0xFFFFFFFF, 1, thr_bits))
            else:
                if self._shipped("fwd_tier0", n):
                    fkern = self._x_kernel("fwd_listed", n)
                    lst.listed(fkern, bufs[14], nd,
                               [bufs[0], bufs[1], bufs[12], bufs[13], bufs[14]],
                               (series_length, series_layout))
                    lst.barrier()
                one = self._shipped("tier1", n)
                kern = self._x_kernel("refine1" if one else "refine", n, dict(rowwin=False))
                lst.listed(kern, bufs[6], pairs,
                           [bufs[12], bufs[11], bufs[9], bufs[10], bufs[5], bufs[6]],
                           (ntm, 0, n, n, bin_shift(n) & 0xFFFFFFFF, 1, thr_bits))
            native = lst.end()
            natives.append(native)
            return self._x_time(native, {}, 2)
        try:
            out = screen([["td", "fft"]], time_kind, rounds=3)
            if not (out.get("fft", 0.0) > 0.0 and out.get("td", 0.0) > 0.0):
                return 0.0
            return (out["td"] / (nsurv * m_lags * tap_count)) / (out["fft"] / nsurv)
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
        return layout_label(band, c[1], c[2], c[3], c[0])

    def _time_coarse_layouts(self, band, cands):
        """Device seconds per pair of each coarse layout on synthetic data (screened, then
        timed in interleaved rounds, the fastest few again together: _coarse.screen)."""
        from ._coarse import screen
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
            lst = self._x_list("coarse timing")
            lst.dispatch(kernel, groups, [data, tmpl, cidx, cval],
                         (ntm, 0, band, slot_val, band.bit_length() - 1, 0,
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
            out = screen([untiled or cands] + ([tiles] if untiled and len(untiled) < len(cands)
                                                     else []),
                              lambda c: time_at(c, self._COARSE_PAIRS),
                              time_screen=lambda c: time_at(c, self._COARSE_SCREEN), rounds=3)
        finally:
            for native in natives:
                self._x_release(native)
            for b in (data, tmpl, cidx, cval):
                b.destroy()
        return out

    def _coarse_kernel(self, band, layout, stride, scale, rowwin):
        sg, ppg, tile, twt = layout[:4]
        return self._x_kernel("coarse", band, dict(sg=sg, ppg=ppg, tile=tile, twt=twt,
                                                   stride=stride, scale=scale, rowwin=rowwin))

    def _gate_bits(self, thr, band, layout):
        """The coarse kernel's last word: for a tiled build whose pair fits one subgroup, the
        gate threshold as magnitude bits (tierb.slang peakTwoGate: only the pass and its
        value, no election -- nothing reads tier 0's index); 0 elects (peakTwoWave)."""
        sg, _, tile, _ = layout[:4]
        if tile <= 1:
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
                   handle_out=None, refine_reach=None, nbins=None, band_offsets=None,
                   direct=None, tier0_cluster=None):
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
                    ct1=ct1, raw_thr1=raw_thr1, slot=slot, refine_reach=refine_reach,
                    band_offsets=band_offsets, direct=direct, tier0_cluster=tier0_cluster),
                lo, hi, binsize, MAX_BINS, upload_data, upload_tmpl, sparse, async_submit)
        if cascade_band is not None:
            tiers = ((int(cascade_band), ct0, float(raw_thr)), (int(band), ct1, float(raw_thr1)))
            if not tiers[0][0] < tiers[1][0] < n:
                raise ValueError("cascade bands must increase below n: %r"
                                 % ((tiers[0][0], tiers[1][0]),))
        else:
            tiers = ((int(band), ct0, float(raw_thr)),)
        cl_meta = None
        cl_sig = None
        cl_lag_pad = 0
        nc = nt
        if tier0_cluster is not None:
            if len(tiers) < 2:
                raise ValueError("tier0_cluster requires a two-tier cascade")
            cl_cache = self.__dict__.setdefault("_cl_meta_cache", {})
            cid = id(tier0_cluster)
            hit = cl_cache.get(cid)
            if hit is not None and hit[0] is tier0_cluster and hit[1] == nt:
                cl_off, cl_mem, cl_lag_pad, cl_sig = hit[2:]
            else:
                raw_off = np.asarray(tier0_cluster.offsets, dtype=np.int64)
                raw_mem = np.asarray(tier0_cluster.members, dtype=np.int64)
                cl_lag_pad = int(getattr(tier0_cluster, "lag_pad", 0))
                if (raw_off.ndim != 1 or raw_off.size < 2 or int(raw_off[0]) != 0
                        or int(raw_off[-1]) != nt or raw_mem.shape != (nt,)
                        or cl_lag_pad < 0 or cl_lag_pad >= tiers[0][0]):
                    raise ValueError("invalid tier0_cluster partition or lag_pad")
                if np.any(raw_off[:-1] >= raw_off[1:]) or np.any((raw_mem < 0) | (raw_mem >= nt)):
                    raise ValueError("invalid tier0_cluster CSR offsets or member indices")
                if np.unique(raw_mem).size != nt:
                    raise ValueError("tier0_cluster members must partition [0, nt)")
                cl_off = np.ascontiguousarray(raw_off, dtype=np.uint32)
                cl_mem = np.ascontiguousarray(raw_mem, dtype=np.uint32)
                h = hashlib.blake2b(digest_size=12)
                h.update(memoryview(cl_off))
                h.update(memoryview(cl_mem))
                cl_sig = (int(cl_off.size - 1), cl_lag_pad, h.digest())
                if len(cl_cache) > 256:
                    cl_cache.clear()
                cl_cache[cid] = (tier0_cluster, nt, cl_off, cl_mem, cl_lag_pad, cl_sig)
            nc = int(cl_off.size - 1)
            cl_meta = (nc, cl_off, cl_mem, cl_lag_pad)
        for i, (b, ct, _) in enumerate(tiers):
            want_nt = nc if i == 0 else nt
            if ct.shape != (want_nt, b):
                raise ValueError("tier-%d coarse templates must be (%d, %d), got %s"
                                 % (i, want_nt, b, ct.shape))
        if band_offsets is None:
            k0s = (0,) * len(tiers)
        else:
            k0s = tuple(int(x) for x in band_offsets)
            if len(k0s) != len(tiers) or any(x < 0 or (x > 0 and x >= n // 2) for x in k0s):
                raise ValueError("band_offsets must have one valid offset (< n // 2) per tier")
        shifted = any(k0s)
        bands = tuple(b for b, _, _ in tiers)
        half = self._shipped("c16", bands[0])          # the fp16 coarse role at tier 0
        half1 = (len(bands) > 1 and self.packed_fp16 and self._shipped("c16", bands[1])
                 and self._shipped("tier1_c16", bands[1]))
        layout0 = self._coarse_layout(bands[0]) if half else None
        shift = bin_shift(binsize)
        t2 = float(threshold) ** 2 if threshold > 0 else 0.0
        top = max(bands)

        dv, tv = shared_view(data, self), shared_view(tmpl, self)
        one_bin_possible = (
            any(g_lo < g_hi and g_hi - 1 - g_lo < binsize for g_lo, g_hi, _, _ in rw_key)
            if rw is not None else (lo < hi and (hi - 1) // binsize == lo // binsize))
        want_direct = (direct is not None and n <= 65536 and self._shipped("refine_td", n)
                       and one_bin_possible)
        # The feed: claim the deferred forward of these spectra when its bands move fewer
        # bytes than the full spectra (band_forward_wanted), or whenever direct time-domain
        # refine will read the series directly instead of recomputing survivor block FFTs.
        # With shifted active bands (k0 > 0), in-place reads at row start cannot wrap [k0, k0+b)
        # into cyclic slots, so un-claimed calls pack via packCoarse and claimed forwards use
        # forwardTier0 (or seriesForwardBands for a single tier).
        feed = "inplace" if (self.inplace_feed and not shifted) else "pack"
        claim = None
        forced_feed = self.__dict__.get("feed_forced")
        reach_for_feed = (0.0 if (want_direct and forced_feed is None)
                          else (None if refine_reach is None
                                else min(max(float(refine_reach), 0.0), 1.0)))
        banded = band_forward_wanted(n, top, reach_for_feed, forced=forced_feed)
        tier0_ok = half and self._shipped("fwd_tier0", n)
        bands_ok = self.inplace_feed and (not shifted or len(tiers) == 1)
        if dv is not None and (tier0_ok or bands_ok) and banded:
            claim = self._exec_claim(slot, data, nd)
            if claim is not None:
                CLAIMS[0] += 1
                feed = "tier0" if tier0_ok else "bands"
        use_direct = bool(want_direct and claim is not None)
        # Each tier's input and its stride: the spectra rows (n), the band rows, or packed.
        ed, et = 0, 0
        ed1, et1 = 0, 0
        k0_extra = (k0s,) if shifted else ()
        cl_extra = (("cl", cl_sig),) if cl_sig is not None else ()
        storage_key = ("hierstore", n, bands, nd, nt, nbins, rw_key is not None,
                       dv is not None and data.ctypes.data, tv is not None and tmpl.ctypes.data,
                       slot if async_submit else None, *k0_extra, *cl_extra)
        uploads = self._input_uploads(storage_key, data, tmpl, upload_data, upload_tmpl)
        if half or half1:
            held = self.__dict__.setdefault("_c16_template_exp", {})
            if half:
                if uploads[1] or storage_key not in held:
                    held[storage_key] = c16_template_exp(ct0)
                et = held[storage_key]
                ed = c16_data_exp(bands[0], tiers[0][2], et)
            if half1:
                key1 = (storage_key, 1)
                if uploads[1] or key1 not in held:
                    held[key1] = c16_template_exp(ct1)
                et1 = held[key1]
                ed1 = c16_data_exp(bands[1], tiers[1][2], et1)
        self._last_c16_scale = 2.0 ** (et + ed)         # tier-0 values / this = unscaled
        self._last_c16_scale1 = 2.0 ** (et1 + ed1) if half1 else 1.0
        # How a sparse result is read (_sparse_way): a paired choice per call shape, played on
        # this call (Choice.play) when the call is waited on; each way has its own record.
        handles = {}

        def run(way, layout=layout0):
            gate = False if use_direct else (self._gate_use(bands[1]) if len(bands) > 1 else None)
            t1_extra = ((half1, ed1),) if half1 else ()
            key = ("hier", n, bands, nd, nt, nbins, layout, gate, feed, use_direct, way,
                   rw_key is not None, ed, storage_key, *k0_extra, *t1_extra)
            table = self._exec_table()
            rec = table.get(key)
            fresh = rec is None
            if fresh:
                rec = self._hier_record(key, n, tiers, nd, nt, nbins, layout, half, feed, way, rw,
                                        ed, dv, tv, data, tmpl, claim, k0s,
                                        use_direct=use_direct, cl_meta=cl_meta,
                                        half1=half1, ed1=ed1)
                table[key] = rec
            self._cache_touch(key)
            self._claim(rec.buffers["idx"])          # an earlier result still reading these outputs
            # every way's record takes the call's inputs (a play runs each on this call)
            up = (True, True, *uploads[2:]) if fresh else uploads
            self._hier_upload(rec, storage_key, up, data, tmpl, tiers, half, et, slot,
                              cl_meta=cl_meta, half1=half1, et1=et1)
            if rw is not None:
                # Every row-window table in one upload, each at its section (_hier_record).
                span = (self._section_offset(rec.buffers, "rw0")
                        - self._section_offset(rec.buffers, "rw"))
                tables = [np.ascontiguousarray(rw, np.uint32)] + [
                    band_windows(rw, n, b, lag_pad=cl_lag_pad if j == 0 else 0)
                    for j, b in enumerate(bands)
                ]
                packed = np.zeros((len(tables), span // 4), np.uint32)
                for j, t in enumerate(tables):
                    packed[j, :t.size] = t.reshape(-1)
                self._x_upload(rec.buffers["rws"], packed, slot)

            binds = self._hier_binds(n, tiers, nd, nt, nbins, lo, hi, binsize, shift, t2, half, ed,
                                     et, rw is not None, layout, claim, data, k0s,
                                     direct=direct if use_direct else None, cl_meta=cl_meta,
                                     half1=half1, ed1=ed1, et1=et1)
            shape = (nd, nt, nbins)
            if handle_out is not None:
                slots = self._call_slots(bands, half, sparse, use_direct=use_direct, half1=half1)
                handles[way] = (HierHandle(
                    key=key, rec=rec, binds=binds, dsig=self._uploaded["data"].get(storage_key),
                    tsig=self._uploaded["tmpl"].get(storage_key), storage=storage_key, shape=shape,
                    sparse=sparse, way=way, claim=claim is not None,
                    slots=slots, values=self._slot_values(slots)))
            return self._hier_run(rec, binds, shape, sparse, way, len(tiers) > 1, slot,
                                  async_submit)

        # The sparse read, the coarse layout and the gate way are kernel slots the device
        # trial plays on whole batches (_settings.slot): a call here runs what they say.
        way = self._sparse_way() if sparse else "dense"
        res = run(way)
        if handle_out is not None and way in handles:
            handle_out.append(handles[way])
        return res

    def _hier_upload(self, rec, storage_key, uploads, data, tmpl, tiers, half, et, slot,
                     cl_meta=None, half1=False, et1=0):
        """Inputs found stale (_input_uploads): the spectra and templates where the record owns
        them, and the tiers' templates -- each fp16 tier's packed at its 2^et -- always."""
        if uploads[0] and "data" in rec.owned:
            self._x_upload(rec.buffers["data"], np.ascontiguousarray(data, np.complex64), slot)
        if uploads[0]:
            self._uploaded["data"][storage_key] = uploads[2]
        if uploads[1]:
            if "tmpl" in rec.owned:
                self._x_upload(rec.buffers["tmpl"], np.ascontiguousarray(tmpl, np.complex64),
                               slot)
            for i, (_, ct, _) in enumerate(tiers):
                use_half = (half if i == 0 else half1)
                texp = et if i == 0 else et1
                self._x_upload(rec.buffers["ct%d" % i],
                               pack_half2(pow2_scaled(ct, texp)) if use_half
                               else np.ascontiguousarray(ct, np.complex64), slot)
            if cl_meta is not None:
                self._x_upload(rec.buffers["cloff"], cl_meta[1], slot)
                self._x_upload(rec.buffers["clmem"], cl_meta[2], slot)
            self._uploaded["tmpl"][storage_key] = uploads[3]

    def _hier_record(self, key, n, tiers, nd, nt, nbins, layout, half, feed, way, rw, ed, dv,
                     tv, data, tmpl, claim, k0s=None, use_direct=False, cl_meta=None,
                     half1=False, ed1=0):
        """Buffers and the recording of one call shape (see the module docstring)."""
        from ._coarse import coarse_launch
        from ._gpuexec import Arg, Record
        k0s = (0,) * len(tiers) if k0s is None else k0s
        bands = tuple(b for b, _, _ in tiers)
        last = len(tiers) - 1
        nc = nt if cl_meta is None else cl_meta[0]
        pairs0 = nd * nc
        pairs = nd * nt
        out = pairs * nbins
        rowwin = rw is not None
        cb0 = 4 if half else 8
        cb1 = 4 if half1 else 8
        t1_ppg = (1024 // bands[1]) if half1 else 0
        t1_shift = ((2 * t1_ppg).bit_length() - 1) if half1 else 0
        align = max(16, int(self.storage_offset_alignment))
        count_step = max(32 if t1_shift else 16, align)
        estimate = (sum(a.nbytes for a, v in ((data, dv), (tmpl, tv)) if v is None)
                    + sum((cb0 * b * nc if i == 0 else cb1 * b * nt) for i, b in enumerate(bands))
                    + pairs0 * 12 + pairs * (4 + (16 if last else 0)) + out * 12 + 64
                    + ((nc + 1 + nt) * 4 if cl_meta is not None else 0)
                    + (nd * (bands[0] * cb0 + (bands[1] * cb1 if last else 0))
                       if feed in ("tier0", "pack") else nd * max(bands) * 8 if feed == "bands"
                       else 0)
                    + (out * 16 if way == "compact" else 0)
                    + (pairs * 4 + count_step if use_direct else 0))
        self._exec_room(estimate, [v for v in (dv, tv) if v is not None])
        rec = Record()
        buf = lambda name, nbytes, **kw: self._exec_buffer(rec, name, nbytes=nbytes, **kw)
        bd = self._exec_buffer(rec, "data", dv, data.nbytes)
        bt = self._exec_buffer(rec, "tmpl", tv, tmpl.nbytes)
        for i, b in enumerate(bands):
            nti = nc if i == 0 else nt
            pi = pairs0 if i == 0 else pairs
            buf("ct%d" % i, nti * b * (cb0 if i == 0 else cb1), upload=True)
            buf("cidx%d" % i, pi * 4)
            buf("cval%d" % i, pi * 8)
            buf("surv%d" % i, pairs * 4, readback=i == last)
        if cl_meta is not None:
            buf("cloff", (nc + 1) * 4, upload=True)
            buf("clmem", nt * 4, upload=True)
        if use_direct:
            buf("fbsurv", pairs * 4)
        # Small words share one buffer each way (one update, one readback; one upload of the
        # row windows): a buffer each made 5 readbacks and 7 uploads a call where 1ccbbe4b's
        # CUDA path made 3 and 4, 12% of the L40S fine stage at n=4096.
        names = _count_names(len(bands), feed in ("tier0", "bands"), way == "compact", use_direct)
        counts = buf("counts", count_step * len(names), readback=True)
        for j, name in enumerate(names):
            rec.buffers[name] = self._x_section(
                counts, j * count_step, 32 if (name == "args0" and t1_shift) else 16)
        if t1_shift:
            rec.buffers["t1args"] = self._x_section(counts, 16, 16)
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
            buf("band1", nd * bands[1] * cb1 if last else 16)
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
                         (Arg("tier0", 8),))
            lst.barrier()
            lst.stamp("forward")
        elif feed == "bands":
            lst.dispatch(self._x_kernel("fwd_bands", n), nd,
                         [Arg("series"), Arg("starts"), B["bands"]], (Arg("bands", 4),))
            lst.barrier()
            lst.stamp("forward")
        # Counts to zero (an indirect dispatch's [count, 1, 1]), in one update; dense outputs
        # to "nothing".
        words = []
        for name in names:
            if name == "count":
                head = [0, 0, 0, 0]
            elif name == "args0" and t1_shift:
                head = [0, 1, 1, 0, 0, 1, 1, 0]
            else:
                head = [0, 1, 1, 0]
            words += head + [0] * (count_step // 4 - len(head))
        lst.update(counts, words)
        if feed in ("tier0", "bands"):
            lst.fill(B["flags"], 0)
        if way != "rows":
            lst.fill(bi, 0xFFFFFFFF)
            lst.fill(bv, 0)
        lst.barrier()
        lst.stamp("fill")
        if feed == "pack":
            # Each tier's band from the spectra: each fp16 tier's packed at its data scale.
            for i, b in enumerate(bands):
                h = int((i == 0 and half) or (i == 1 and half1))
                dexp = ed if i == 0 else ed1
                lst.dispatch(self._x_kernel("pack", n), (nd * b + 255) // 256,
                             [bd, B["band%d" % i]],
                             (n, b, nd * b, h, _bits(2.0 ** dexp if h else 1.0), k0s[i]))
            lst.barrier()
            lst.stamp("pack")
        # Tier inputs: (buffer, row stride in elements (0: the tier's own band), data scale
        # exponent applied as the tier reads it).
        if feed == "inplace":
            src = [(bd, n, ed if (i == 0 and half) else (ed1 if (i == 1 and half1) else 0))
                   for i in range(len(bands))]
        elif feed == "bands":
            src = [(B["bands"], max(bands),
                    ed if (i == 0 and half) else (ed1 if (i == 1 and half1) else 0))
                   for i in range(len(bands))]
        else:                                   # tier0 or pack: the bands as written
            src = [(B["band0"], 0, 0)] + ([(B["band1"], 0, 0)] if last else [])
        for i, b in enumerate(bands):
            sbuf, stride, scale = src[i]
            if i == 0:
                if half:
                    kern = self._coarse_kernel(b, layout, stride, scale, rowwin)
                    _, groups = coarse_launch(nd, nc, layout[1], layout[2], 0)
                else:
                    kern = self._x_kernel("gate", b, dict(stride=stride, rowwin=rowwin))
                    groups = pairs0
                lst.dispatch(kern, groups, [sbuf, S("ct0"), S("cidx0"), S("cval0")] + rws("rw0"),
                             (Arg("coarse", 7),))
                lst.barrier()
                lst.stamp("coarse0")
                if cl_meta is not None:
                    lst.dispatch(self._x_kernel("compactc", n), (pairs0 + 255) // 256,
                                 [S("cval0"), S("cloff"), S("clmem"), S("surv0"), S("args0")],
                                 (Arg("compact0", 5),))
                else:
                    lst.dispatch(self._x_kernel("compact", n), (pairs + 255) // 256,
                                 [S("cval0"), S("surv0"), S("args0")], (Arg("compact0", 3),))
            else:
                if half1:
                    kern = self._x_kernel("tier1_c16", b,
                                          dict(stride=stride, scale=scale, rowwin=rowwin, twt=1))
                    lst.listed(kern, S("t1args"), -(-pairs // (2 * t1_ppg)),
                               [sbuf, S("ct1"), S("cidx1"), S("cval1"), S("surv0"), S("args0")]
                               + rws("rw1"), (Arg("tier", 7),))
                else:
                    one = self._shipped("tier1", b)
                    kern = self._x_kernel("tier1" if one else "tier", b,
                                          dict(stride=stride, rowwin=rowwin,
                                               gate=one and not use_direct and self._gate_use(b)))
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
        if use_direct:
            lst.listed(self._x_kernel("refine_td", n, dict(rowwin=rowwin)), S(sargs), pairs,
                       [Arg("series"), Arg("starts"), Arg("taps"),
                        S("cidx%d" % last), S("cval%d" % last), S(survs), S(sargs),
                        B["fbsurv"], B["fbargs"], bi, bv] + rws("rw"),
                       (Arg("refine_td", 15),))
            lst.barrier()
            lst.stamp("refine_td")
        fft_survs, fft_args = (B["fbsurv"], B["fbargs"]) if use_direct else (S(survs), S(sargs))
        if feed in ("tier0", "bands"):
            # The refine reads the full spectra of its survivors' blocks: recompute those.
            lst.dispatch(self._x_kernel("mark", n), (pairs + 255) // 256,
                         [fft_survs, fft_args, B["flags"], B["blist"], B["bargs"]], (nt,))
            lst.barrier()
            lst.stamp("mark")
            lst.listed(self._x_kernel("fwd_listed", n), B["bargs"], nd,
                       [Arg("series"), Arg("starts"), bd, B["blist"], B["bargs"]],
                       (Arg("listed", 2),))
            lst.barrier()
            lst.stamp("recompute")
        lst.listed(self._x_kernel("refine1" if nbins == 1 else "refine", n,
                                  dict(rowwin=rowwin)), fft_args, pairs,
                   [bd, bt, bi, bv, fft_survs, fft_args] + rws("rw"), (Arg("refine", 7),))
        lst.barrier()
        lst.stamp("refine")
        if way == "compact":
            # Its own phase: a fused batch runs a phase's work unordered (see stamp).
            lst.dispatch(self._x_kernel("compact_peaks", n), (out + 255) // 256,
                         [bi, bv, B["count"], B["list"]], (out, out))
            lst.barrier()
            lst.stamp("peaks")
        # What the host reads: the counts, then the peaks as `way` reads them.
        lst.readback(counts, count_step * len(names))
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
                    rowwin, layout, claim, data, k0s=None, direct=None, cl_meta=None,
                    half1=False, ed1=0, et1=0):
        """The per-run words and bindings of a hier_peaks call."""
        from ._coarse import coarse_launch
        k0s = (0,) * len(tiers) if k0s is None else k0s
        nc = nt if cl_meta is None else cl_meta[0]
        lag_pad0 = 0 if cl_meta is None else cl_meta[3]
        pairs0 = nd * nc
        pairs = nd * nt
        binds = {}
        start = (lambda first: ROWWIN_ON) if rowwin else (lambda first: first)
        b0, _, thr0 = tiers[0]
        cs, ce, csp, csh = coarse_span(n, b0, lo, hi, lag_pad=lag_pad0)
        thr0 = thr0 * (2.0 ** (et + ed) if half else 1.0)
        if half:
            slot_val, _ = coarse_launch(nd, nc, layout[1], layout[2], csp)
            gate_bits = (0 if (direct is not None and len(tiers) == 1)
                         else self._gate_bits(thr0, b0, layout))
            # nbins 0 asks a non-final fp16 gate tier for the pass/fail decision alone.
            binds["coarse"] = (nc, start(cs), ce, slot_val, csh & 0xFFFFFFFF,
                               0 if len(tiers) > 1 else 1, gate_bits)
        else:
            binds["coarse"] = (nc, start(cs), ce, csp, csh & 0xFFFFFFFF, 1, 0)
        pack_shift = ((2048 // tiers[1][0]).bit_length() - 1) if half1 else 0
        if cl_meta is not None:
            binds["compact0"] = (pairs0, nc, nt, _bits(thr0), pack_shift)
        else:
            binds["compact0"] = (pairs, _bits(thr0), pack_shift)
        if len(tiers) > 1:
            b1, _, thr1 = tiers[1]
            cs1, ce1, csp1, csh1 = coarse_span(n, b1, lo, hi)
            if half1:
                thr1 = thr1 * (2.0 ** (et1 + ed1))
                gate = False if direct is not None else self._gate_use(b1)
                gate_bits1 = _bits(max(float(thr1), _TINY)) if gate else 0
                binds["tier"] = (nt, start(cs1), ce1, csp1, csh1 & 0xFFFFFFFF,
                                 0 if gate_bits1 else 1, gate_bits1)
            else:
                # nbins 0 asks a one-bin build for the gate's decision alone, unless direct refine
                # needs tier 1's elected coarse lag.
                gate = False if direct is not None else self._gate_use(b1)
                binds["tier"] = (nt, start(cs1), ce1, csp1, csh1 & 0xFFFFFFFF, 0 if gate else 1, 0)
            # The pairs tier 0 dismissed hold zeros: the smallest normal float dismisses them.
            binds["compact1"] = (pairs, _bits(max(thr1, _TINY)), nbins)
        binds["refine"] = (nt, start(lo), hi, binsize, shift & 0xFFFFFFFF, nbins, _bits(t2))
        if claim is not None:
            series, starts, row, count, nser, code = claim
            binds["series"], binds["starts"] = series, starts
            binds["listed"] = (nser, code)
            b1 = tiers[1][0] if len(tiers) > 1 else 0
            k0_1 = k0s[1] if len(k0s) > 1 else 0
            scale1 = _bits(2.0 ** ed1) if (len(tiers) > 1 and half1) else 0
            binds["tier0"] = (nser, b0, b1, _bits(2.0 ** ed if half else 1.0),
                              scale1, k0s[0], k0_1, code)
            binds["bands"] = (nser, max(b for b, _, _ in tiers), k0s[0], code)
            if direct is not None:
                taps_view, tap_meta, tmpl_offset, direct_hw, max_lag_tap = direct
                binds["taps"] = taps_view
                binds["refine_td"] = (n, tiers[-1][0], nt, tmpl_offset, nser, code, tap_meta,
                                      direct_hw, max_lag_tap, start(lo), hi, binsize,
                                      shift & 0xFFFFFFFF, nbins, _bits(t2))
        return binds

    def _sparse_way(self):
        """How a sparse result is read -- its survivors' rows gathered on the host, or the hits
        compacted on the device: a kernel slot of the device trial (_gpuexec.SPARSE_WAYS)."""
        from ._gpuexec import SPARSE_WAYS
        from ._settings import slot as kernel_slot
        return kernel_slot(self._dev_name(), "sparse", "hier", *SPARSE_WAYS["hier"])

    def _hier_run(self, rec, binds, shape, sparse, way, cascade, slot, async_submit):
        """Run a recorded call and return its result (a tracked collector when async)."""
        wait = self._exec_submit(rec.native, binds, slot, rec) if async_submit else None
        if wait is None:
            self._exec_run(rec.native, True, binds, slot, rec)

        def result():
            if wait is not None:
                wait()
            return self._hier_result(rec, shape, sparse, way, cascade)
        return self._track(result, owner=rec.buffers["idx"]) if async_submit else result()

    def _hier_result(self, rec, shape, sparse, way, cascade):
        """The call's peaks from its readback buffers. Counts, survivors and the rows a
        sparse result gathers are read in place where the host sees the buffers (_x_view):
        only a dense result copies its outputs whole."""
        from ._results import _SparsePeaks
        nd, nt, nbins = shape
        pairs, out = nd * nt, nd * nt * nbins
        B = rec.buffers
        last = 1 if cascade else 0
        self.last_tier0_checked = getattr(B.get("cidx0"), "nbytes", pairs * 4) // 4
        words = self._x_view(B["counts"], np.uint32, B["counts"].nbytes // 4)
        at = lambda name: int(words[self._section_offset(B, name) // 4])
        count = at("args%d" % last)
        self.last_refinements = count
        if "fbargs" in B:
            fb = at("fbargs")
            self.last_direct_refinements = max(0, count - fb)
            self.last_fft_refinements = fb
        else:
            self.last_direct_refinements = 0
            self.last_fft_refinements = count
        if cascade:
            self.last_tier1_survivors = at("args0")
        rows = None
        if sparse and way == "rows":
            rows = self._x_view(B["surv%d" % last], np.uint32, count)
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
        """Whether hier_replay(h) would submit: the record is the one the handle saw, both
        inputs are still resident under the signatures it saw, and its kernel slots still say
        what it ran (a device trial's arm that moves one makes the call record afresh; the
        slots are consulted, so a replayed call counts as using them). (The band/full feed
        is a function of the call, so a replay of the same call takes the same one.)"""
        return (self._exec_table().get(h.key) is h.rec
                and self._uploaded["data"].get(h.storage) == h.dsig
                and self._uploaded["tmpl"].get(h.storage) == h.tsig
                and self._slot_values(h.slots) == h.values)

    def _call_slots(self, bands, half, sparse, use_direct=False, half1=False):
        """The kernel slots a hier_peaks call over these bands consults: ((what, band,
        (default, alternative)), ...) (time_domain's device trial plays them)."""
        from ._gpuexec import SPARSE_WAYS
        out = []
        if half:
            pair = self._kernel_pair("coarse", bands[0])
            if pair[1] is not None:
                out.append(("coarse", bands[0], self._slot_labels("coarse", bands[0], pair)))
        can_gate1 = (not use_direct and len(bands) > 1
                     and ((half1 and bands[1] // 16 <= self.subgroup_size)
                          or (not half1 and self._shipped("tier1", bands[1])
                              and self._shipped("tier1gate", bands[1]))))
        if can_gate1:
            pair = self._kernel_pair("gateway", bands[1])
            if pair[1] is not None:
                out.append(("gateway", bands[1], self._slot_labels("gateway", bands[1], pair)))
        if sparse:
            out.append(("sparse", "hier", SPARSE_WAYS["hier"]))
        return tuple(out)

    def _slot_values(self, slots):
        from ._settings import slot as kernel_slot
        name = self._dev_name()
        return tuple(kernel_slot(name, w, b, *pair) for w, b, pair in slots)

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
                              slot, async_submit)
