#!/usr/bin/env python3
"""Exactness harness for stage U (GPU host unification): record, then check.

    python tools/unify_golden.py record DIR --device gpu:0
    python tools/unify_golden.py check  DIR --device gpu:0

`record` runs a fixed set of seeded cases through the public API on one device and saves
every output; `check` reruns them and requires every output to be bit-identical. A port
of a GPU operation onto the shared executor keeps the kernels, so on the device the
golden was recorded on it must reproduce them exactly (a different device rounds
differently: record per device).

Choices that change results are pinned: MF_AUTOTUNE=0 and MF_CHAIN_FORCE (set here), fixed
block lengths, and every calibrated cost through MF_COST_FILE (DIR/costs_<device>.json, written
by `record`, read by `check`): the middle bank's block sizes follow measured costs, so two
processes measuring afresh correlate at different lengths. Coarse layouts do not change
results (test_coarse_conformance).
Peaks are compared sorted by (template, sample), since the order of a compaction may
legitimately differ.

Cases (each a public entry point the host layers serve):
  corr_*      TimeDomainFilterBank engine 'corr': whole bank, windows, a selection, a real
              series, a lane of a device row, async (wait=False) then wait
  flat_*      engine 'flat': filter_series over windows, and deferred filter_series_many
  hier_*      engine 'hier' (real and quadrature taps): filter_series, a real lane
  followup    a single template, threshold 0, short windows (the follow-up executor)
  full        CorrelationFilter.run, one- and two-stage sizes, and wait=False
  search      HierarchicalSearch, three levels, two chunks, two channels, narrow windows
"""
import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("MF_AUTOTUNE", "0")
os.environ.setdefault("MF_CHAIN_FORCE", "256,512")
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_k, "1")
sys.path.append(str(Path(__file__).resolve().parent.parent / "python"))

import numpy as np  # noqa: E402

S = 1 << 16


def _taps(rng, counts, complex_taps=False):
    taps = np.zeros((len(counts), max(counts)), np.complex64 if complex_taps else np.float32)
    for i, c in enumerate(counts):
        t = rng.standard_normal(c) + (1j * rng.standard_normal(c) if complex_taps else 0)
        taps[i, :c] = t / np.linalg.norm(t)
    return taps


def _shaped_taps(rng, counts, w, df, analytic, rate=2048.0):
    """Inspiral-like filters (amplitude from the profile; analytic = positive frequencies,
    doubled), as tests/test_complex_taps.py builds them: the gate model expects templates
    whose power follows the reference profile."""
    f = np.arange(w.size) * df
    taps = np.zeros((len(counts), max(counts)), np.complex64 if analytic else np.float32)
    for i, c in enumerate(counts):
        ff = np.fft.fftfreq(c, 1 / rate)
        amp = np.sqrt(np.interp(np.abs(ff), f, w))
        if analytic:
            h = np.fft.ifft(amp * (ff > 0) * 2.0 * np.exp(2j * np.pi * rng.random(c)))
        else:
            h = np.fft.irfft(np.sqrt(np.interp(np.fft.rfftfreq(c, 1 / rate), f, w))
                             * np.exp(2j * np.pi * rng.random(c // 2 + 1)), c)
        taps[i, :c] = (h / np.linalg.norm(h)).astype(taps.dtype)
    return taps


def _profile():
    df = 1.0 / 16
    f = np.arange(int(1024 / df) + 1) * df
    return np.where((f > 20) & (f < 900), np.maximum(f, 1.0) ** (-7.0 / 3), 0.0), df


def _peaks(prefix, r, out):
    o = np.lexsort((np.asarray(r.sample_indices), np.asarray(r.template_indices)))
    out[prefix + "_t"] = np.asarray(r.template_indices)[o]
    out[prefix + "_s"] = np.asarray(r.sample_indices)[o]
    out[prefix + "_z"] = np.asarray(r.snr)[o]


def cases(device):
    from matchedfilter import CorrelationFilter
    from matchedfilter.time_domain import TimeDomainFilterBank as B
    rng = np.random.default_rng(2026)
    out = {}
    x = rng.standard_normal(S).astype(np.float32)
    xc = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
    w, df = _profile()
    windows = [(3000, 9000), (20000, 21000), (40000, 60000)]

    # correlation (the middle stage's engine)
    counts = [251, 401, 401, 1151, 900, 300]
    corr = B(_taps(rng, counts), counts, engine="corr", device=device, fft_lengths=[2048, 4096])
    out["corr_whole"] = corr.correlate_series(xc)
    out["corr_windows"] = corr.correlate_series(xc, windows=windows)
    out["corr_selected"] = corr.correlate_series(x, windows=windows, templates=[1, 3, 4])
    out["corr_real"] = corr.correlate_series(x, windows=windows)
    rows = corr.empty_shared((2, S))
    rows[1] = (x + 1j * xc.real).astype(np.complex64)
    out["corr_lane"] = corr.correlate_series(rows[1].imag, windows=windows)
    dest = corr.empty_shared((3, S))
    dest[:] = 0
    corr.correlate_series(x, windows=windows, templates=[0, 2, 5], out=dest, wait=False)
    corr.wait()
    out["corr_async"] = np.array(dest)

    # flat peaks
    fcounts = [101, 151, 201, 251]
    flat = B(_taps(rng, fcounts, True), fcounts, engine="flat", threshold=3.0, binsize=512,
             device=device)
    _peaks("flat_windows", flat.filter_series(xc, windows=windows), out)
    many = B.filter_series_many([(flat, xc, dict(windows=windows)), (flat, x, {})], wait=False)
    for i, r in enumerate(many):
        _peaks("flat_many%d" % i, r.result(), out)

    # hierarchical: profile-shaped filters, coloured noise and loud template-shaped
    # injections, so the gates pass pairs and the refine runs
    hcounts = [int(c) for c in rng.integers(150, 401, 16)]
    f = np.fft.rfftfreq(S, 1 / 2048.0)
    colored = np.fft.irfft(np.fft.rfft(rng.standard_normal(S)) *
                           np.sqrt(np.interp(f, np.arange(w.size) * df, w) + 1e-12), S)
    colored = (colored / colored.std()).astype(np.float32)
    for name, cplx in (("hier_real_taps", False), ("hier_quadrature", True)):
        taps = _shaped_taps(rng, hcounts, w, df, cplx)
        y = colored.copy()
        for j, i in enumerate(range(0, len(hcounts), 3)):
            c = hcounts[i]
            pos = 3000 + j * 9000
            y[pos:pos + c] += 25.0 * np.real(taps[i, :c][::-1])
        if not cplx:
            y = y.astype(np.complex64)
        hb = B(taps, hcounts, engine="hier", threshold=5.5, binsize=2048,
               device=device, fft_lengths=[2048])
        hb.set_reference(w, delta_f=df)
        _peaks(name, hb.filter_series(y), out)
        if cplx:
            lane = corr.empty_shared((2, S))
            lane[1] = (rng.standard_normal(S) + 1j * y).astype(np.complex64)
            _peaks(name + "_lane", hb.filter_series(lane[1].imag), out)
            _peaks("followup", hb.filter_series(x, windows=slice(30000, 30000 + 40 * 61),
                                                binsize=61, threshold=0.0, template_index=3),
                   out)

    # full correlation
    for n in (4096, 1 << 17):
        cf = CorrelationFilter(n, ndata=1, ntemplates=2, device=device)
        cf.set_templates((rng.standard_normal((2, n)) + 1j * rng.standard_normal((2, n)))
                         .astype(np.complex64))
        cf.set_data((rng.standard_normal((1, n)) + 1j * rng.standard_normal((1, n)))
                    .astype(np.complex64))
        out["full_%d" % n] = np.array(cf.run())
        if cf._gpu is not None:
            o = cf.empty_shared((1, 2, n), readback=True)
            cf.run(out=o, wait=False)
            cf.wait()
            out["full_%d_async" % n] = np.array(o)

    # the whole search
    from matchedfilter.search import BlockInput, HierarchicalSearch, Inner, Leaf, Root
    N = 1 << 15

    def spec():
        return (rng.standard_normal(N // 2 + 1) + 1j * rng.standard_normal(N // 2 + 1)).astype(
            np.complex64)
    groups = []
    for i, c in enumerate((301, 451, 451, 601)):
        lf = Leaf(_taps(rng, (101, 151, 201), True), (101, 151, 201),
                  lags=rng.integers(0, 40, 3), node_id=("leaf", i))
        t = rng.standard_normal(c).astype(np.float32)
        groups.append(Inner(t / np.linalg.norm(t), children=[lf], node_id=("inner", i)))
    root = Root(spec(), (60, N // 2 - 200), children=groups, node_id="root")
    inputs = {ch: BlockInput([spec() for _ in range(2)], [(4096, N - 4096)] * 2,
                             root_scale=lambda r, b, s=1.0 + 0.25 * j: s / N)
              for j, ch in enumerate(("A", "B"))}

    def win(leaf, chunk, ch, extra):
        if chunk == 0:
            return None
        return [(12000 - extra, 14000 + extra)] if leaf.node_id == ("leaf", 2) else []
    search = HierarchicalSearch([root], threshold=0.0, context=300,
                                leaf_options=dict(engine="flat", binsize=512, device=device))

    def on_peaks(ctx):
        for ch in ctx.channels:
            key = "search_%s_%d_%s" % (ctx.leaf.node_id[1], ctx.chunk, ch)
            _peaks(key, ctx.peaks[ch], out)
            out[key + "_series"] = np.array(ctx.series(ch))
    search.run(inputs, windows=win, on_peaks=on_peaks)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["record", "check"])
    ap.add_argument("dir")
    ap.add_argument("--device", default="gpu:0")
    a = ap.parse_args()
    tag = a.device.replace(":", "")
    path = Path(a.dir) / ("golden_%s.npz" % tag)
    Path(a.dir).mkdir(parents=True, exist_ok=True)
    costs = Path(a.dir) / ("costs_%s.json" % tag)
    if a.mode == "record" and costs.exists():
        costs.unlink()                            # a fresh record measures afresh
    os.environ.setdefault("MF_COST_FILE", str(costs))
    got = cases(a.device)
    if a.mode == "record":
        Path(a.dir).mkdir(parents=True, exist_ok=True)
        np.savez(path, **got)
        print("recorded %d arrays to %s" % (len(got), path))
        return
    ref = np.load(path)
    bad = sorted(k for k in set(ref.files) | set(got)
                 if k not in got or k not in ref.files or not np.array_equal(ref[k], got[k]))
    for k in bad[:20]:
        print("DIFFERS: %s" % k)
    print("unify_golden: %d arrays, %d differ" % (len(ref.files), len(bad)))
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
