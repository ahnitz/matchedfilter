"""Headroom of template-group partitioning and block size, on captured middle-group calls.

Each capture is one bank call: a middle group's templates (possibly split into
several plans when captured), its series and its reference. The bank is rebuilt
under alternative layouts and every alternative runs the same series:

  one@N      all templates in one plan at block size N
  split k    templates sorted by length, k contiguous plans of equal size, N=2048

Each plan uses the model's best chain for its block size (reference rebinned to
that block's frequency grid; thresholds from the model; no trials), and its own
overlap-save layout: margin c = (longest taps)//2, valid output N - L + 1 per block.
Times are medians of interleaved repetitions of the whole bank call.

usage: replay_partitions.py DIR [--reps 5] [--ns 1024 2048 4096]
"""
import argparse, glob, time
import numpy as np
from matchedfilter import _core, gatechain


def load(path):
    z = np.load(path)
    gs = [{k.split("_", 1)[1]: z[k] for k in z.files if k.startswith(g + "_")}
          for g in sorted({k.split("_")[0] for k in z.files if k.startswith("g")})]
    return z["series"], gs


def taps_of(spec, n):
    """Circularly centred taps from a length-n spectrum: (taps at lags 0..c, taps at lags -c..-1)."""
    h = np.fft.ifft(spec.astype(np.complex128)) * 1.0
    nz = np.nonzero(np.abs(h) > 1e-7 * np.abs(h).max())[0]
    pos = nz[nz < n // 2]; neg = nz[nz >= n // 2]
    cpos = int(pos.max()) if pos.size else 0
    cneg = int(n - neg.min()) if neg.size else 0
    return h, cpos, cneg


def respectrum(spec, n_from, n_to):
    """The same centred FIR at block size n_to (exact re-embedding of its taps)."""
    h = np.fft.ifft(spec.astype(np.complex128))
    out = np.zeros(n_to, np.complex128)
    half = min(n_from, n_to) // 2
    out[:half] = h[:half]
    out[n_to - half:] = h[n_from - half:]
    return np.fft.fft(out).astype(np.complex64)


def rebin_ref(ref, n_from, n_to):
    r = np.asarray(ref, np.float64)
    if n_to == n_from:
        return r
    if n_to > n_from:
        return np.repeat(r, n_to // n_from) / (n_to // n_from)
    return r.reshape(n_to, n_from // n_to).sum(1)


def length_of(spec, n):
    h, cp, cn = taps_of(spec, n)
    return cp + cn + 1, max(cp, cn)


def layout(c, nvalid, lo, hi):
    first = max(0, (lo - c) // nvalid)
    ts = np.arange(first * nvalid, hi, nvalid, dtype=np.int64)
    v0 = ts + c
    keep = (v0 < hi) & (v0 + nvalid > lo)
    ts, v0 = ts[keep], v0[keep]
    rs = np.maximum(lo, v0); re = np.minimum(hi, v0 + nvalid)
    good = re > rs
    return ts[good].astype(np.uintp), (rs - ts)[good].astype(np.uintp), (re - ts)[good].astype(np.uintp)


class Plan:
    def __init__(self, specs, n, ref_n, lengths, margins, lo, hi, snr):
        self.n, self.nt = n, len(specs)
        L = int(max(lengths)); c = int(max(margins))
        self.blocks = layout(c, n - L + 1, lo, hi) if n - L + 1 > 0 else None
        if self.blocks is None or len(self.blocks[0]) == 0:
            self.ok = False; return
        win = (int(self.blocks[1][len(self.blocks[1]) // 2]), int(self.blocks[2][len(self.blocks[2]) // 2]))
        best, _ = gatechain.choose_chain(ref_n, n, snr, 1e-3, cost=gatechain.calibrate_costs(n, self.nt),
                                         max_tiers=3, window=win)
        if best is None:
            self.ok = False; return
        self.chain = best["chain"]
        self.p = _core.HMF(n, 1, self.nt, list(self.chain), 32 if n <= 2048 else 16, n)
        self.p.set_reference(ref_n.astype(np.float32))
        self.p.set_template_batch(0, np.ascontiguousarray(np.stack(specs)))
        self.p.set_thresholds(list(best["thresholds"]))
        nb = len(self.blocks[0])
        self.out = (np.zeros((nb, self.nt, 1), np.int64), np.zeros((nb, self.nt, 1), np.complex64),
                    np.zeros((nb, self.nt, 1), np.float32), np.zeros((nb, self.nt), np.int32))
        self.ok = True

    def run(self, sv, snr):
        st, ws, we = self.blocks
        self.p.run_series(sv, st, ws, we, 0, self.nt, self.n, snr, *self.out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--ns", type=int, nargs="+", default=[1024, 2048, 4096])
    a = ap.parse_args()
    totals = {}
    for f in sorted(glob.glob(f"{a.dir}/cap*.npz")):
        ser, gs = load(f)
        n0 = int(gs[0]["n"]); snr = float(gs[0]["threshold"])
        specs = [s for g in gs for s in g["spectra"]]
        lm = [length_of(s, n0) for s in specs]
        order = np.argsort([l for l, _ in lm])
        specs = [specs[i] for i in order]; lens = [lm[i][0] for i in order]; margs = [lm[i][1] for i in order]
        lo = int(min(g["starts"][0] + g["ws"][0] for g in gs)); hi = int(max(g["starts"][-1] + g["we"][-1] for g in gs))
        ref = gs[0]["ref"]
        configs = {}
        for n in a.ns:
            if max(lens) >= n:
                continue
            sp = specs if n == n0 else [respectrum(s, n0, n) for s in specs]
            configs[f"one@{n}"] = [Plan(sp, n, rebin_ref(ref, n0, n), lens, margs, lo, hi, snr)]
        for k in (2, 3):
            parts = np.array_split(np.arange(len(specs)), k)
            configs[f"split{k}@{n0}"] = [Plan([specs[i] for i in pr], n0, rebin_ref(ref, n0, n0),
                                              [lens[i] for i in pr], [margs[i] for i in pr], lo, hi, snr) for pr in parts]
        configs = {k: v for k, v in configs.items() if all(p.ok for p in v)}
        sv = ser.view(np.float32)
        times = {k: [] for k in configs}
        for _ in range(a.reps):
            for k, plans in configs.items():
                t0 = time.perf_counter()
                for p in plans:
                    p.run(sv, snr)
                times[k].append(time.perf_counter() - t0)
        med = {k: float(np.median(v)) for k, v in times.items()}
        base = med.get(f"one@{n0}")
        line = f"{f.split('/')[-1]}: {len(specs)} templates, taps {min(lens)}-{max(lens)}"
        for k, v in med.items():
            totals.setdefault(k, 0.0); totals[k] += v
            line += f"  {k} {v*1e3:5.1f}ms[{'/'.join(map(str, configs[k][0].chain))}]"
        print(line)
    base = totals.get("one@2048")
    print("\ntotal over calls (relative to one plan at 2048):")
    for k, v in totals.items():
        print(f"   {k:12s} {v*1e3:8.1f} ms   {v/base:5.2f}x")


if __name__ == "__main__":
    main()
