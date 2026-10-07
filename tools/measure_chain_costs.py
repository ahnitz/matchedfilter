"""Measure the cost of each gate-chain tier on this machine.

The chain cost model needs, per transform size n:

  dense(b)        first tier at band b, run on every (block, template) pair   [per pair]
  sparse(b | f)   a later tier at band b, run on survivors at density f       [per survivor]
  refine(f)       full-band correlation of a surviving pair at density f      [per refine]

Survivor density matters: pooled tiers and the refine amortise less when few
pairs survive, so each is measured at several densities. Thresholds are set at
the (1-f) quantile of the previous tier's coarse maxima (read from the engine's
own dump), and costs come from the engine's per-section cycle counters
(MF_HMF_PROF), which charge each tier separately. Wall-clock differences of
whole runs cannot resolve a 3% tier on a loaded machine; the counters can.
Units are TSC ticks; only ratios between entries are used.

usage: measure_chain_costs.py [--n 2048] [--nt 64] [--blocks 96] [--reps 5] [--out costs.json]
"""
import argparse, gc, json, os, platform, re, tempfile
import numpy as np
import matchedfilter as mf

_PROF = re.compile(r"even=([\d.]+).*gate=([\d.]+).*refine=([\d.]+).*fill=([\d.]+)")


def analytic_series(S, seed):
    r = np.random.default_rng(seed)
    x = (r.standard_normal(S) + 1j * r.standard_normal(S)) / np.sqrt(2)
    F = np.fft.fft(x); F[S // 2:] = 0
    return (np.fft.ifft(F) * np.sqrt(2)).astype(np.complex64)


class _CaptureFd2:
    """Capture C-level writes to stderr (the engine prints its counters there)."""
    def __enter__(self):
        self.tmp = tempfile.TemporaryFile(mode="w+b")
        self.saved = os.dup(2); os.dup2(self.tmp.fileno(), 2)
        return self
    def __exit__(self, *exc):
        os.dup2(self.saved, 2); os.close(self.saved)
        self.tmp.seek(0); self.text = self.tmp.read().decode(errors="replace"); self.tmp.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2048)
    ap.add_argument("--nt", type=int, default=64)
    ap.add_argument("--blocks", type=int, default=96)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--taps", type=int, default=451)
    ap.add_argument("--out")
    a = ap.parse_args()
    n, nt = a.n, a.nt
    rng = np.random.default_rng(3)
    taps = [rng.standard_normal(a.taps).astype(np.float32) / np.sqrt(a.taps) for _ in range(nt)]
    bank = mf.TimeDomainFilterBank(taps, [a.taps] * nt, engine="matchedfilter", threshold=1e9, fft_lengths=[n])
    g = bank._groups[0]
    spectra, c_bad = g.spectra, g.c_bad
    step = n - 2 * c_bad
    ser = analytic_series((a.blocks + 1) * step, 5)
    starts = np.arange(a.blocks, dtype=np.int64) * step
    ws = np.full(a.blocks, c_bad, np.int64); we = np.full(a.blocks, n - c_bad, np.int64)
    bands = [b for b in (64, 128, 256, 512, 1024, 2048, 4096) if b < n]
    big = float(np.finfo(np.float32).max)

    def plan(cfg, thr, env=None):
        old = {}
        for k, v in (env or {}).items():
            old[k] = os.environ.get(k); os.environ[k] = v
        try:
            hp = mf.HierarchicalFilter(n, ndata=1, ntemplates=nt, snr=6.0, fd=1e-3, band=cfg)
        finally:
            for k, v in old.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k] = v
        hp.set_templates(spectra); hp.set_coarse_threshold(thr)
        return hp

    def coarse_values(b):
        path = os.path.join(tempfile.gettempdir(), f"mf_chain_cost_dump_{os.getpid()}")
        hp = plan((b, 8), 0.0, {"MF_HMF_DUMP": path, "MF_DGROUP": "1"})
        hp.run_series(ser, starts, ws, we, binsize=n, threshold=1e9, raw=True)
        del hp; gc.collect()
        v = np.fromfile(path, dtype=np.float32).reshape(-1, 8)[:, 0]; os.remove(path)
        return v

    def counters(cfg, thr):
        """Ticks per pair (even = first tier incl. bookkeeping, gate = second tier, refine) and refine rate."""
        hp = plan(cfg, thr, {"MF_HMF_PROF": "1"})
        hp.run_series(ser, starts, ws, we, binsize=n, threshold=1e9, raw=True)   # warm (counted; it is a rep like the others)
        for _ in range(a.reps - 1):
            hp.run_series(ser, starts, ws, we, binsize=n, threshold=1e9, raw=True)
        with _CaptureFd2() as cap:
            pairs, trig = hp.stats
        m = _PROF.search(cap.text)
        even, gate, ref, fill = (float(x) for x in m.groups()) if m else (np.nan,) * 4
        return dict(first=even + fill, second=gate, refine=ref, rate=trig / pairs if pairs else 0.0)

    cv = {b: coarse_values(b) for b in bands}
    fracs = (1.0, 0.3, 0.1, 0.03, 0.01)
    dense, refine, sparse = {}, {}, {}
    for b in bands:
        c = counters((b, 8), big)
        dense[str(b)] = c["first"]
        for f in fracs:
            thr = 0.0 if f >= 1 else float(np.quantile(cv[b], 1 - f))
            c = counters((b, 8), thr)
            if c["rate"] > 0:
                refine.setdefault(str(f), []).append(c["refine"] / c["rate"])
    refine = {f: float(np.median(v)) for f, v in refine.items()}
    for b0 in bands:
        for b1 in bands:
            if b1 <= b0:
                continue
            for f in fracs:
                thr0 = 0.0 if f >= 1 else float(np.quantile(cv[b0], 1 - f))
                c = counters((b0, b1, 8), (thr0, big))
                sparse.setdefault(str(b1), {}).setdefault(str(f), []).append(c["second"] / f)
    sparse = {b1: {f: float(np.median(v)) for f, v in d.items()} for b1, d in sparse.items()}

    print(f"n={n} nt={nt}  ticks; dense per pair, sparse/refine per survivor")
    print("dense  " + "  ".join(f"{b}:{dense[b]:.0f}" for b in dense))
    print("refine " + "  ".join(f"f={f}:{v:.0f}" for f, v in refine.items()))
    for b1, d in sparse.items():
        print(f"sparse {b1:>5s} " + "  ".join(f"f={f}:{v:.0f}" for f, v in d.items()))
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(dict(n=n, nt=nt, blocks=a.blocks, host=platform.node(), units="TSC ticks",
                           dense=dense, refine=refine, sparse=sparse), fh, indent=1)


if __name__ == "__main__":
    main()
