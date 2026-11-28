#!/usr/bin/env python3
"""Record every result the library hands a caller on fixed inputs, and compare two records.

A record is what a caller receives, in the order it receives it: every filtering call's
peaks (template, sample, complex SNR, block start, block length), every correlation's
output, and what a search's hooks see (the root series given to on_series, each leaf's
peaks and envelope values, the parent series and its support, and the results of the
hook's refilter calls). Two records compare bitwise, order included, so a change that
must not change results can be checked against the tree it changes.

    python tools/golden.py record OUT.npz --costs SEED.json
    python tools/golden.py compare A.npz B.npz
    python tools/golden.py schedules A.npz

The cases:

- each capture top (a pickle of tools/search_bench.py's format, ``--tops``), searched
  with its own windows and recording hooks, one setup pass then one recorded pass;
- the first top again with an envelope and refilter calls in its hooks (a follow-up in
  the other channel around each channel's loudest peaks, as pycbc_inspiral_fir makes);
- the first top again with every window answer cut into three windows with gaps;
- the first top again with an injection job's windows (one 9-second window per block, four
  leaves live), with an envelope and follow-ups;
- the first top's chunks (the correlation and leaf jobs its search's walk makes, with its own
  windows and with the injection job's) through correlate_and_filter_many, untiled and tiled
  at a 4 MB tile;
- a small synthetic search with an envelope and refilter calls;
- the low-level entry points on small synthetic inputs: filter_series (every template, a
  window list with a bin size, one template, a threshold below the bank's), on a gated and
  an ungated bank; filter_series_many over mixed jobs; correlate_series of a real and a
  complex series (with windows, templates and scales); correlate_series_channels;
  correlate_series and correlate_series_channels on a bank whose block-size groups
  interleave, of complex series, with gapped windows, scales, selections across groups and
  outputs reused through out_support; correlate_and_filter_many; and the tiled cascade's
  middle calls (two windows its blocks bridge, scales, time chunks forced by a small tile)
  with the middle output written (scaled, and unscaled: the case "mirrored", named after the
  streaming copy that once made it), not written, and kept around peaks. A search never
  tiles (tiling is an explicit choice of correlate_and_filter_many); every
  correlate_and_filter_many case is recorded under both schedules (``.untiled``, ``.other``,
  ``.tiled``), and ``schedules`` checks that a record's two schedules gave the same peaks
  and series (and, where both wrote it, the same middle output).

Decisions must be the same in both trees for a bitwise comparison to mean anything, so
every run reads its measured costs from a cost file and runs with MF_AUTOTUNE=0 (no timed
trials). ``--costs`` names the seed: when it does not exist the run is cold and writes it;
when it exists the run reads a private copy and reports whether the run added to it (a
measurement the seed did not hold, made in this process: such a run is not reproducible).
Record a seed once, then record each tree from it. Run on one thread
(OMP_NUM_THREADS=1 and the BLAS equivalents).

``--device`` runs every case on that device (``cpu``, the default, or a GPU such as
``gpu:0``): the searches' leaves, the banks of the entry points and the correlation banks.
A device's measured choices differ from the CPU's, so each device has a seed of its own; a
record compares only with records of the same device. A device's first run after a new
build also compiles its kernels (minutes on RADV): make the seeding run that one.

The tool imports the matchedfilter package of its own checkout (``--tree`` names another
checkout's python/ directory). An array of more than ``DIGEST_ABOVE`` elements is stored as
its SHA-256 digest, with its dtype and shape in its name.

``compare`` prints ``N arrays; 0 differ`` and exits 0 when the records hold the same names
in the same order and every array is equal byte for byte; otherwise it prints the first
differences and exits 1.
"""
import argparse
import hashlib
import os
import pickle
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
#: Arrays with more elements are recorded as their SHA-256 digest.
DIGEST_ABOVE = 1 << 16
#: The capture tops recorded by default.
DEFAULT_TOPS = [str(ROOT.parent.parent / "research" / "captures" / "tops" / ("search%02d.pkl" % i))
                for i in (1, 2, 3)]


class Recorder:
    """The ordered arrays of a record: each added under its case, a running index and a label.

    Parameters
    ----------
    digest_above : int, optional
        Arrays with more elements than this are stored as their SHA-256 digest. Default
        ``DIGEST_ABOVE``.
    """

    def __init__(self, digest_above=DIGEST_ABOVE):
        self.digest_above = digest_above
        self.arrays = {}
        self.case = ""

    def add(self, label, value):
        """Add one array (or anything numpy makes one of) under the current case.

        Parameters
        ----------
        label : str
            What the array is, within the case.
        value : array_like
            The array. It is copied (or digested) at once, so a caller's buffer may be
            reused afterwards.
        """
        a = np.ascontiguousarray(np.asarray(value))
        name = "%06d|%s|%s" % (len(self.arrays), self.case, label)
        if a.size > self.digest_above:
            name += "|sha256 %s %s" % (a.dtype.str, "x".join(str(s) for s in a.shape))
            a = np.frombuffer(hashlib.sha256(a.tobytes()).digest(), dtype=np.uint8).copy()
        else:
            a = a.copy()
        self.arrays[name] = a

    def add_results(self, label, res):
        """Add a FilterResults' five columns, in its order."""
        for field in ("template_indices", "sample_indices", "snr", "block_starts",
                      "block_lengths"):
            self.add("%s.%s" % (label, field), getattr(res, field))

    def save(self, path):
        np.savez(path, **self.arrays)


def _record_hooks(rec, search, envelope=None, refilter=None):
    """on_series, on_peaks and on_chunk hooks that record what the search hands them.

    Parameters
    ----------
    rec : Recorder or None
        Where to record; None records nothing (a setup pass), but the hooks still make
        their refilter calls, so the setup pass does what the recorded one does.
    search : HierarchicalSearch
        The search the hooks are given to.
    envelope : callable, optional
        ``envelope(series) -> callable``: the threshold envelope on_series returns for a
        channel's root series. Default None: no envelope.
    refilter : callable, optional
        ``refilter(ctx, rec)``: refilter calls an on_peaks hook makes, recording their
        results. Default None: none.

    Returns
    -------
    dict
        ``on_series``, ``on_peaks`` and ``on_chunk`` for HierarchicalSearch.run.
    """
    names = {}

    def on_series(ctx):
        out = {}
        for c in ctx.channels:
            if rec is not None:
                rec.add("chunk%d.%s.root" % (ctx.chunk, c), ctx.series[c])
            if envelope is not None:
                out[c] = envelope(np.array(ctx.series[c]))
        return out

    def on_peaks(ctx):
        leaf = names.setdefault(id(ctx.leaf), len(names))
        for c in ctx.channels:
            if rec is not None:
                tag = "chunk%d.leaf%d.%s" % (ctx.chunk, leaf, c)
                rec.add_results(tag + ".peaks", ctx.peaks[c])
                e = ctx.envelope(c)
                rec.add(tag + ".envelope", np.empty(0) if e is None else e)
                support = ctx.support(c)
                rec.add(tag + ".support", np.asarray(support, dtype=np.int64).reshape(-1, 2))
                ser = ctx.series(c)
                rec.add(tag + ".series", np.concatenate([ser[a:b] for a, b in support])
                        if support else ser[:0])
        if refilter is not None:
            refilter(ctx, rec)

    def on_chunk(ctx):
        if rec is not None:
            rec.add("chunk%d.channels" % ctx.chunk, np.array(ctx.channels))
    return dict(on_series=on_series, on_peaks=on_peaks, on_chunk=on_chunk)


def _envelope_of(series):
    """A threshold envelope at or above 1 that depends on the root series' values."""
    level = np.abs(series).astype(np.float64)
    level = 1.0 + 0.2 * np.minimum(1.0, level / (4.0 * max(level.std(), 1e-30)))
    return lambda t: level[t]


def _follow_up(binsize, half_bins):
    """A refilter hook as pycbc_inspiral_fir's follow-up makes them: for each channel's three
    loudest peaks, the peak's template in every other channel over a window of 2 * half_bins
    bins around its sample, at threshold 0; and once per leaf every template over the first
    of those windows at the search's threshold."""
    def refilter(ctx, rec):
        leaf_tag = "chunk%d.leaf%s" % (ctx.chunk, getattr(ctx.leaf, "node_id", "?"))
        for a in ctx.channels:
            p = ctx.peaks[a]
            loud = np.argsort(-np.abs(p.snr), kind="stable")[:3]
            for b in ctx.channels:
                if b == a:
                    continue
                support = ctx.support(b)
                if not support:
                    continue
                lo, hi = support[0][0], support[-1][1]
                for k, i in enumerate(loud):
                    s = int(p.sample_indices[i])
                    w0 = max(lo, s - half_bins * binsize)
                    w1 = min(hi, s + half_bins * binsize)
                    if w1 <= w0:
                        continue
                    res = ctx.refilter(b, windows=slice(w0, w1), binsize=binsize, threshold=0.0,
                                       template_index=int(p.template_indices[i]))
                    if rec is not None:
                        rec.add_results("%s.%s>%s.%d.refilter" % (leaf_tag, a, b, k), res)
                    if k == 0:
                        res = ctx.refilter(b, windows=[(w0, w1)], binsize=binsize,
                                           threshold=ctx.leaf_threshold)
                        if rec is not None:
                            rec.add_results("%s.%s>%s.all.refilter" % (leaf_tag, a, b), res)
    return refilter


def _search_case(rec, name, search, inputs, windows, hooks):
    """One setup pass of a search, then one recorded pass, under case `name`."""
    search.run(inputs, windows=windows, **hooks(None))
    rec.case = name
    search.run(inputs, windows=windows, **hooks(rec))


def _split_windows(windows, inputs):
    """The capture's windows answer (None: the block's valid span) with each window cut
    into three, 4096-sample gaps between them; the widened answer (extra > 0) widens each
    piece by extra."""
    def split(lf, k, c, extra):
        base = windows(lf, k, c, 0)
        if base is None:
            base = [inputs[c].valid[k]]
        if not base:
            return base
        out = []
        for a, b in base:
            third = (b - a) // 3
            if third <= 8192:
                out.append((a, b))
                continue
            for p0, p1 in ((a, a + third), (a + third + 4096, a + 2 * third),
                           (a + 2 * third + 4096, b)):
                out.append((p0 - extra, p1 + extra))
        return out
    return split


def _injection_windows(search, inputs, live_leaves=4, half_width=int(4.5 * 2048)):
    """Windows as pycbc_inspiral_fir asks for them in an injection job with an injection
    window (``--injection-window 4.5``, as PyCBC's search configuration sets it): one window
    of +/- half_width samples around an injection at the middle of each block's valid span,
    widened by the job's guard (a cluster window of 2048 samples and twice the search's pad),
    for the first live_leaves leaves (those whose chirp times match the injection's); the
    others are skipped."""
    order = {}
    guard = 2048 + 2 * search.pad(search.roots[0])

    def windows(lf, k, c, extra):
        if order.setdefault(id(lf), len(order)) >= live_leaves:
            return []
        v0, v1 = inputs[c].valid[k]
        mid = (v0 + v1) // 2
        return [(mid - half_width - guard - extra, mid + half_width + guard + extra)]
    return windows


def _capture_cases(rec, tops, device):
    """Every capture top, then the first again with follow-ups, with split windows and with
    an injection job's windows, each searched on `device`."""
    sys.path.insert(0, str(ROOT / "tools"))
    import search_bench
    for i, path in enumerate(tops):
        with open(path, "rb") as f:
            capture = pickle.load(f)
        top = Path(path).stem
        variants = [("plain", None, None, None)]
        if i == 0:
            variants += [("followup", _envelope_of, _follow_up(205, 50), None),
                         ("split", None, None, None),
                         ("injection", _envelope_of, _follow_up(205, 50), None)]
        for variant, envelope, refilter, _ in variants:
            search, inputs, windows, _, _ = search_bench.build(capture, device)
            search_threshold = search.threshold
            if variant == "split":
                windows = _split_windows(windows, inputs)
            elif variant.startswith("injection"):
                windows = _injection_windows(search, inputs)

            def hooks(r, search=search, envelope=envelope, refilter=refilter,
                      threshold=search_threshold):
                h = _record_hooks(r, search, envelope, refilter)
                on_peaks = h["on_peaks"]

                def with_threshold(ctx):
                    ctx.leaf_threshold = threshold
                    on_peaks(ctx)
                h["on_peaks"] = with_threshold
                return h
            _search_case(rec, "%s.%s" % (top, variant), search, inputs, windows, hooks)
            print("recorded %s.%s (%d arrays so far)" % (top, variant, len(rec.arrays)),
                  flush=True)
        if i == 0:
            _chunk_cases(rec, top, capture, device)


def _chunk_cases(rec, top, capture, device):
    """The first top's chunks (the correlation and leaf jobs a CPU search's walk makes, with
    its own windows and with an injection job's) through correlate_and_filter_many, untiled
    (the default) and tiled at a 4 MB tile (``.tiled``): the leaves' peaks and the middle
    outputs."""
    import schedule_bench
    import search_bench
    from matchedfilter.time_domain import TimeDomainFilterBank
    for variant in ("plain", "injection"):
        search, inputs, windows, _, _ = search_bench.build(capture, device)
        if variant == "injection":
            windows = _injection_windows(search, inputs)
        chunks = schedule_bench.chunk_jobs(search, inputs, windows)
        for suffix, kw in (("", {}), (".tiled", dict(tile_bytes=4 << 20))):
            rec.case = "%s.%s.chunks%s" % (top, variant, suffix)
            for n, (corr_jobs, leaf_jobs) in enumerate(chunks):
                for _, _, c_kw in corr_jobs:
                    c_kw["out"][:] = 0
                res = TimeDomainFilterBank.correlate_and_filter_many(corr_jobs, leaf_jobs, **kw)
                for k, r in enumerate(res):
                    rec.add_results("chunk%d.leaf%d" % (n, k), r)
                for k, (_, _, c_kw) in enumerate(corr_jobs):
                    rec.add("chunk%d.middle%d" % (n, k), c_kw["out"])
        print("recorded %s.%s.chunks (%d arrays so far)" % (top, variant, len(rec.arrays)),
              flush=True)


def _reference(n_bins=16385, delta_f=1.0 / 16.0):
    """A one-sided power profile (f^-7/3 between 24 and 850 Hz) and its spacing."""
    f = np.arange(n_bins, dtype=np.float64) * delta_f
    return np.where((f >= 24.0) & (f <= 850.0), np.maximum(f, 1.0) ** (-7.0 / 3.0), 0.0), delta_f


def _chirps(n_templates, counts, complex_taps, seed):
    """Unit-norm windowed chirp taps of the given lengths, real or complex."""
    counts = np.asarray(counts, dtype=np.int64)
    taps = np.zeros((n_templates, int(counts.max())),
                    dtype=np.complex64 if complex_taps else np.float32)
    for i in range(n_templates):
        c = int(counts[i])
        t = np.arange(c) / 2048.0
        f0, f1 = 35.0 + 9.0 * ((i + seed) % 17), 180.0 + 14.0 * ((i + seed) % 23)
        phase = 2.0 * np.pi * (f0 * t + 0.5 * (f1 - f0) * t * t)
        row = (np.exp(1j * phase) if complex_taps else np.cos(phase)) * np.hanning(c)
        taps[i, :c] = row / np.linalg.norm(row)
    return taps, counts


def _synthetic_search_case(rec, device):
    """A small search (one root, four inner nodes, a 12-template leaf under each, two
    channels, two chunks) with an envelope and follow-ups: small enough that every
    middle-to-leaf path the library has runs on it. Its leaves run on `device`."""
    from matchedfilter.search import BlockInput, HierarchicalSearch, Inner, Leaf, Root
    rng = np.random.default_rng(777)
    n = 131072
    nb = n // 2 + 1
    w, df = _reference()
    spec = np.zeros(nb, dtype=np.complex64)
    spec[64:20000] = rng.standard_normal(19936) + 1j * rng.standard_normal(19936)
    spec /= np.float32(np.linalg.norm(spec))
    inner = []
    for i in range(4):
        itaps, icounts = _chirps(1, [701 + 200 * i], False, i)
        ftaps, fcounts = _chirps(12, rng.integers(180, 300, size=12), True, 3 * i)
        leaf = Leaf(ftaps, fcounts, lags=rng.integers(-20, 20, size=12), node_id=i)
        inner.append(Inner(itaps[0], int(icounts[0]), children=[leaf], node_id=100 + i))
    root = Root(spec, band=(64, 20000), children=inner, profile=(w, df), node_id="root")
    inputs = {c: BlockInput([(rng.standard_normal(nb) + 1j * rng.standard_normal(nb))
                             .astype(np.complex64) for _ in range(2)],
                            [(12288, n - 12288), (24576, 65536)], root_scale=lambda r, k: 25.0)
              for c in ("H1", "L1")}

    def windows(leaf, chunk, channel, extra):
        if chunk == 0:
            return None
        if leaf.node_id == 0 and channel == "L1":
            return []
        return [(28000 - extra, 40000 + extra), (44000 - extra, 52000 + extra)]
    search = HierarchicalSearch([root], threshold=3.6, envelope_floor=1.0, context=256,
                                min_pad=2048,
                                leaf_options=dict(engine="hier", device=device, binsize=2048,
                                                  false_dismissal=1e-2))

    def hooks(r):
        h = _record_hooks(r, search, _envelope_of, _follow_up(256, 2))
        on_peaks = h["on_peaks"]

        def with_threshold(ctx):
            ctx.leaf_threshold = 3.6
            on_peaks(ctx)
        h["on_peaks"] = with_threshold
        return h
    _search_case(rec, "synthetic.search", search, inputs, windows, hooks)


def _entry_point_cases(rec, device):
    """The low-level entry points on small synthetic inputs, with every bank on `device`."""
    from matchedfilter import TimeDomainFilterBank
    rng = np.random.default_rng(2026)
    w, df = _reference()
    S = 1 << 17
    x = rng.standard_normal(S).astype(np.float32)
    ftaps, fcounts = _chirps(24, rng.integers(150, 900, size=24), False, 1)
    x[40000:40000 + int(fcounts[5])] += 9.0 * ftaps[5, :fcounts[5]]
    xc = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)

    rec.case = "entry.filter_series"
    hier = TimeDomainFilterBank(ftaps, fcounts, engine="hier", threshold=3.8,
                                false_dismissal=1e-2, device=device)
    hier.set_reference(w, delta_f=df)
    flat = TimeDomainFilterBank(_chirps(10, rng.integers(100, 600, size=10), True, 4)[0],
                                rng.integers(100, 600, size=10), engine="flat", threshold=4.0,
                                device=device)
    for bank_name, bank, series in (("hier", hier, x), ("flat", flat, xc)):
        calls = [dict(),
                 dict(windows=[(5000, 30000), (31000, 90000), (100000, 120000)], binsize=300),
                 dict(windows=slice(30000, 52000), binsize=205, threshold=0.0, template_index=5),
                 dict(windows=slice(60000, 61000), binsize=64, threshold=2.0, template_index=2),
                 dict(windows=[(20000, 70000)], threshold=3.0)]
        for k, kw in enumerate(calls):
            rec.add_results("%s.call%d" % (bank_name, k), bank.filter_series(series, **kw))

    rec.case = "entry.filter_series_many"
    jobs = [(hier, x, dict()),
            (hier, x, dict(windows=slice(30000, 52000), binsize=205, threshold=0.0,
                           template_index=5)),
            (flat, xc, dict(windows=[(1000, 50000)], binsize=500)),
            (hier, x[::-1].copy(), dict(windows=[(0, 60000), (70000, 130000)], binsize=1000)),
            (flat, xc, dict(windows=slice(4000, 9000), binsize=64, threshold=0.0,
                            template_index=7))]
    for k, res in enumerate(TimeDomainFilterBank.filter_series_many(jobs)):
        rec.add_results("job%d" % k, res)

    rec.case = "entry.correlate_series"
    mtaps, mcounts = _chirps(6, [701, 851, 1201, 1501, 2001, 3001], False, 7)
    corr = TimeDomainFilterBank(mtaps, mcounts, engine="corr", device=device)
    ctaps, ccounts = _chirps(5, [300, 500, 700, 1100, 1700], True, 9)
    corr_c = TimeDomainFilterBank(ctaps, ccounts, engine="corr", device=device)
    scales = np.linspace(0.5, 2.0, 6).astype(np.float32)
    rec.add("real.all", corr.correlate_series(x))
    rec.add("real.windows", corr.correlate_series(x, windows=[(4000, 40000), (60000, 90000)]))
    rec.add("real.templates", corr.correlate_series(x, windows=slice(1000, 100000),
                                                    templates=[1, 2, 4]))
    rec.add("real.scaled", corr.correlate_series(x, scales=scales))
    rec.add("real.one", corr.correlate_series(x, template_index=3))
    rec.add("complex.all", corr_c.correlate_series(xc))
    rec.add("complex.windows", corr_c.correlate_series(xc, windows=[(2000, 50000)],
                                                       templates=[0, 3, 4]))

    rec.case = "entry.correlate_series_channels"
    y = rng.standard_normal(S).astype(np.float32)
    outs = [np.zeros((3, S), np.complex64) for _ in range(2)]
    corr.correlate_series_channels([x, y], [[(3000, 70000)], [(10000, 120000)]], outs,
                                   [None, None], templates=[0, 1, 2])
    for k, o in enumerate(outs):
        rec.add("channel%d" % k, o)
    outs_c = [np.zeros((5, S), np.complex64) for _ in range(2)]
    corr_c.correlate_series_channels([xc, xc[::-1].copy()], [None, [(5000, 90000)]], outs_c,
                                     [None, None])
    for k, o in enumerate(outs_c):
        rec.add("complex.channel%d" % k, o)

    rec.case = "entry.correlate_series.interleaved"
    # Templates whose block-size groups interleave in the bank's order, so a group's rows are
    # not one run of the output; scales, selections and one template of a complex series.
    itaps, icounts = _chirps(6, [300, 2900, 420, 3100, 360, 2500], True, 13)
    corr_i = TimeDomainFilterBank(itaps, icounts, engine="corr", device="cpu")
    iscales = np.linspace(-1.5, 2.5, 6).astype(np.float32)
    rec.add("all.scaled", corr_i.correlate_series(xc, scales=iscales))
    rec.add("windows.scaled", corr_i.correlate_series(
        xc, windows=[(3000, 20000), (20500, 41000), (90000, 125000)], scales=iscales))
    rec.add("templates.scaled", corr_i.correlate_series(
        xc, windows=slice(7000, 110000), templates=[5, 0, 2, 3], scales=iscales))
    rec.add("one.scaled", corr_i.correlate_series(xc, windows=[(1000, 9000)], template_index=1,
                                                  scales=iscales[1:2]))
    reused = np.full((3, S), 7 + 7j, np.complex64)
    corr_i.correlate_series(xc, windows=[(5000, 60000)], templates=[1, 2, 4], out=reused)
    corr_i.correlate_series(xc, windows=[(30000, 80000), (100000, 120000)], templates=[1, 2, 4],
                            out=reused, out_support=[(5000, 60000)])
    rec.add("reused.support", reused)
    # several complex channels, gapped windows, a selection across groups, outputs reused
    chans = [xc, xc[::-1].copy(), (xc * np.complex64(0.5 - 0.25j)).astype(np.complex64)]
    wins = [[(2000, 30000), (31000, 64000)], [(15000, 120000)], [(0, 5000), (70000, 131072)]]
    outs_i = [np.full((4, S), 3 - 1j, np.complex64) for _ in chans]
    corr_i.correlate_series_channels(chans, wins, outs_i, [None] * 3, templates=[4, 1, 0, 5])
    for k, o in enumerate(outs_i):
        rec.add("channels.first%d" % k, o)
    corr_i.correlate_series_channels(chans, [wins[2], wins[0], wins[1]], outs_i, wins,
                                     templates=[4, 1, 0, 5])
    for k, o in enumerate(outs_i):
        rec.add("channels.reused%d" % k, o)

    rec.case = "entry.correlate_and_filter_many"
    # Two leaf banks: one reads the middle rows as complex series, the other one row's real
    # lane (a plan reads one kind of series within a call). The small cohort's middle output
    # is below the 4 MB tiling cap and the large one's above it.
    leaf_taps, leaf_counts = _chirps(12, rng.integers(180, 300, size=12), True, 11)
    leaf = TimeDomainFilterBank(leaf_taps, leaf_counts, engine="hier", threshold=3.6,
                                false_dismissal=1e-2, device=device, binsize=2048)
    leaf.set_reference(w, delta_f=df)
    lane_leaf = TimeDomainFilterBank(leaf_taps[:8], leaf_counts[:8], engine="hier",
                                     threshold=3.6, false_dismissal=1e-2, device=device)
    lane_leaf.set_reference(w, delta_f=df)
    for series_name, pair in (("small", (x[:65536].copy(), y[:65536].copy())),
                              ("large", (np.tile(x, 4), np.tile(y, 4)))):
        L = pair[0].size
        outs = [np.zeros((3, L), np.complex64) for _ in pair]
        corr_jobs = [(corr, s, dict(windows=[(8192, L - 8192)], templates=[0, 1, 2], out=o))
                     for s, o in zip(pair, outs)]
        leaf_jobs = [(leaf, o[r], dict(windows=slice(12000, L - 12000))) for o in outs
                     for r in range(3)]
        leaf_jobs += [(lane_leaf, o[1].real, dict(windows=[(20000, 40000), (45000, L - 20000)]))
                      for o in outs]
        for k, res in enumerate(TimeDomainFilterBank.correlate_and_filter_many(corr_jobs,
                                                                               leaf_jobs)):
            rec.add_results("%s.leaf%d" % (series_name, k), res)
        for k, o in enumerate(outs):
            rec.add("%s.middle%d" % (series_name, k), o)
        # the same calls under the other schedule (tiled)
        for o in outs:
            o[:] = 0
        for k, res in enumerate(TimeDomainFilterBank.correlate_and_filter_many(
                corr_jobs, leaf_jobs, tile_bytes=1 << 40)):
            rec.add_results("%s.other.leaf%d" % (series_name, k), res)
        for k, o in enumerate(outs):
            rec.add("%s.other.middle%d" % (series_name, k), o)

    rec.case = "entry.correlate_and_filter_many.cascade"
    # The tiled cascade's middle calls: two windows (a gap its blocks bridge), scales, time
    # chunks forced by a small tile, and each retain mode of the middle output.
    pair = (x[:65536].copy(), y[:65536].copy())
    L = pair[0].size
    for mode, scaled, kw in (("written", True, dict(tile_bytes=1 << 18)),
                             ("mirrored", False, dict(tile_bytes=1 << 18)),
                             ("ephemeral", True, dict(tile_bytes=1 << 18, retain_radius=0)),
                             ("retained", True, dict(tile_bytes=1 << 18, retain_radius=600,
                                                     retain_threshold=3.0)),
                             ("auto", True, dict())):
        outs = [np.zeros((3, L), np.complex64) for _ in pair]
        corr_jobs = [(corr, s, dict(windows=[(6000, 30000), (30300, L - 6000)],
                                    templates=[0, 1, 2], scales=scales if scaled else None,
                                    out=o))
                     for s, o in zip(pair, outs)]
        leaf_jobs = [(leaf, o[r], dict(windows=[(9000, 29000), (36000, L - 9000)]))
                     for o in outs for r in range(3)]
        for k, res in enumerate(TimeDomainFilterBank.correlate_and_filter_many(
                corr_jobs, leaf_jobs, **kw)):
            rec.add_results("%s.leaf%d" % (mode, k), res)
        for k, o in enumerate(outs):
            rec.add("%s.middle%d" % (mode, k), o)
        # untiled, with the same retain mode: the same peaks, and the middle output written
        for o in outs:
            o[:] = 0
        kw_untiled = dict(kw, tile_bytes=0)
        for k, res in enumerate(TimeDomainFilterBank.correlate_and_filter_many(
                corr_jobs, leaf_jobs, **kw_untiled)):
            rec.add_results("%s.untiled.leaf%d" % (mode, k), res)
        for k, o in enumerate(outs):
            rec.add("%s.untiled.middle%d" % (mode, k), o)


def record(args):
    """The record subcommand: every case into args.out."""
    seed = Path(args.costs).resolve()
    work = Path(tempfile.mkdtemp(prefix="golden-costs-"))
    cold = not seed.exists()
    cost_file = seed if cold else work / "costs.json"
    if not cold:
        shutil.copyfile(seed, cost_file)
    os.environ["MF_COST_FILE"] = str(cost_file)
    os.environ["MF_AUTOTUNE"] = "0"
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        if os.environ.get(var) != "1":
            print("warning: %s is not 1" % var)
    sys.path.insert(0, str(Path(args.tree).resolve() if args.tree else ROOT / "python"))
    import matchedfilter
    print("matchedfilter from %s, device %s, cost file %s (%s)"
          % (matchedfilter.__file__, args.device, cost_file,
             "cold: writing the seed" if cold else "copy"), flush=True)
    rec = Recorder(digest_above=args.digest_above)
    if not args.no_captures:
        _capture_cases(rec, args.tops, args.device)
    _synthetic_search_case(rec, args.device)
    print("recorded synthetic.search (%d arrays so far)" % len(rec.arrays), flush=True)
    _entry_point_cases(rec, args.device)
    rec.save(args.out)
    print("%d arrays recorded to %s" % (len(rec.arrays), args.out))
    if not cold:
        same = cost_file.read_bytes() == seed.read_bytes()
        print("cost file %s by the run" % ("unchanged" if same else "CHANGED"))
        shutil.rmtree(work)
        if not same:
            print("this run measured something the seed did not hold: not reproducible")
            return 1
    return 0


def compare(args):
    """The compare subcommand: 0 when the records are identical, else 1."""
    with np.load(args.a) as fa, np.load(args.b) as fb:
        names_a, names_b = list(fa.files), list(fb.files)
        diffs = []
        # A name begins with the array's position, so arrays in another order are other names.
        if names_a != names_b:
            only_a = [n for n in names_a if n not in set(names_b)]
            only_b = [n for n in names_b if n not in set(names_a)]
            diffs.append("the records hold different arrays: %d only in A, %d only in B; "
                         "first only in A: %s; first only in B: %s"
                         % (len(only_a), len(only_b), only_a[:1], only_b[:1]))
        for name in names_a:
            if name not in fb.files:
                continue
            a, b = fa[name], fb[name]
            if a.dtype != b.dtype or a.shape != b.shape:
                diffs.append("%s: %s %s against %s %s" % (name, a.dtype, a.shape, b.dtype,
                                                         b.shape))
            elif a.tobytes() != b.tobytes():
                # elements compared as bytes, so that NaNs and signed zeros count as bits do
                flat_a, flat_b = a.reshape(-1), b.reshape(-1)
                bytes_a = np.ascontiguousarray(flat_a).view(np.uint8).reshape(flat_a.size, -1)
                bytes_b = np.ascontiguousarray(flat_b).view(np.uint8).reshape(flat_b.size, -1)
                bad = np.flatnonzero((bytes_a != bytes_b).any(axis=1))
                diffs.append("%s: %d of %d elements differ, first at %d: %r against %r"
                             % (name, bad.size, flat_a.size, bad[0], flat_a[bad[0]],
                                flat_b[bad[0]]))
        n = len(names_a)
    if not diffs:
        print("%d arrays; 0 differ" % n)
        return 0
    print("%d arrays; %d differ" % (n, len(diffs)))
    for line in diffs[:args.show]:
        print("  " + line)
    return 1


def schedules(args):
    """The schedules subcommand: 0 when every case recorded under both schedules gave the same
    arrays under each, else 1. A case named ``X.untiled`` or ``X.tiled`` is the other schedule
    of case X; within a case, a label holding ``.other.`` or ``.untiled.`` is the other
    schedule of the label without it. The middle output of a call that keeps only part of it
    (retain_radius 0 or positive) is written whole when untiled and is not compared."""
    with np.load(args.record) as f:
        by_key = {}
        for name in f.files:
            _, case, label = name.split("|", 2)
            by_key[(case, label)] = name
        pairs, diffs = 0, []
        for (case, label), name in by_key.items():
            other_case, other_label = case, label
            for suffix in (".untiled", ".tiled"):
                if case.endswith(suffix):
                    other_case = case[:-len(suffix)]
            for part in (".other.", ".untiled."):
                if part in label:
                    other_label = label.replace(part, ".", 1)
            if (other_case, other_label) == (case, label):
                continue
            if label.split(".")[0] in ("ephemeral", "retained") and ".middle" in label:
                continue
            partner = by_key.get((other_case, other_label))
            if partner is None:
                diffs.append("%s: no record under the other schedule" % name)
                continue
            pairs += 1
            if f[name].tobytes() != f[partner].tobytes() or f[name].dtype != f[partner].dtype:
                diffs.append("%s differs from %s" % (name, partner))
    print("%d arrays under both schedules; %d differ" % (pairs, len(diffs)))
    for line in diffs[:args.show]:
        print("  " + line)
    return 1 if diffs or not pairs else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    rp = sub.add_parser("record", help="record every case")
    rp.add_argument("out", help="the record to write (.npz)")
    rp.add_argument("--costs", required=True,
                    help="the seed cost file: written by a cold run when it does not exist, "
                         "else read through a private copy")
    rp.add_argument("--tops", nargs="*", default=DEFAULT_TOPS,
                    help="capture tops in tools/search_bench.py's format (default: the three "
                         "of research/captures/tops)")
    rp.add_argument("--no-captures", action="store_true",
                    help="only the synthetic cases (for a quick check)")
    rp.add_argument("--device", default="cpu",
                    help="the device every case runs on: cpu (default) or a GPU, e.g. gpu:0")
    rp.add_argument("--digest-above", type=int, default=DIGEST_ABOVE,
                    help="arrays with more elements are stored as their SHA-256 digest "
                         "(default %d); a large value keeps them whole, to see how two "
                         "records differ" % DIGEST_ABOVE)
    rp.add_argument("--tree", default=None,
                    help="another checkout's python/ directory to import matchedfilter from "
                         "(default: this checkout's)")
    cp = sub.add_parser("compare", help="compare two records bitwise, order included")
    cp.add_argument("a")
    cp.add_argument("b")
    cp.add_argument("--show", type=int, default=10, help="differences to print (default 10)")
    sp = sub.add_parser("schedules", help="check a record's cases under both schedules")
    sp.add_argument("record")
    sp.add_argument("--show", type=int, default=10, help="differences to print (default 10)")
    args = ap.parse_args(argv)
    return {"record": record, "compare": compare, "schedules": schedules}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
