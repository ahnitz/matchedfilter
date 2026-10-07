"""Replay captured template-group calls through the engine and account the fine stage.

Input: npz files written by a capture hook around TimeDomainFilterBank.filter_series
(series, per-group block layout, template spectra, reference, chain, thresholds).
For each group call the engine runs exactly what the pipeline ran (same chain,
same thresholds, same blocks) and reports, per (block, template) pair:

  tier i      ticks in each coarse tier (engine counters)
  refine      ticks in the full correlation of the last tier's survivors
  untracked   wall time not in any tier: per-block forward transform, data
              ingest, bookkeeping

usage: replay_captured_groups.py DIR [--reps 3] [--chain 256 512 ...]
--chain replays the same calls under a different chain (thresholds from the model).
"""
import argparse, glob, time, mmap, ctypes
import numpy as np
from matchedfilter import _core


def rdtsc():
    if not hasattr(rdtsc, "fn"):
        code = bytes([0x0F, 0x31, 0x48, 0xC1, 0xE2, 0x20, 0x48, 0x09, 0xD0, 0xC3])
        buf = mmap.mmap(-1, len(code), prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
        buf.write(code)
        rdtsc.buf = buf
        rdtsc.fn = ctypes.CFUNCTYPE(ctypes.c_uint64)(ctypes.addressof(ctypes.c_char.from_buffer(buf)))
    return rdtsc.fn()


def tsc_rate():
    t0 = time.perf_counter_ns(); c0 = rdtsc(); time.sleep(0.2); c1 = rdtsc(); t1 = time.perf_counter_ns()
    return (c1 - c0) / ((t1 - t0) * 1e-9)


def groups(path):
    z = np.load(path)
    ser = z["series"]
    for g in sorted({k.split("_")[0] for k in z.files if k.startswith("g")}):
        yield ser, {k.split("_", 1)[1]: z[k] for k in z.files if k.startswith(g + "_")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--chain", type=int, nargs="+")
    a = ap.parse_args()
    tps = tsc_rate()
    tot = {}
    tot_pairs = 0
    tot_wall = 0.0
    for f in sorted(glob.glob(f"{a.dir}/cap*.npz")):
        for ser, g in groups(f):
            n = int(g["n"]); spec = g["spectra"]; nt = spec.shape[0]
            chain = tuple(int(b) for b in (a.chain or g["chain"]))
            if a.chain:
                from matchedfilter import gatechain
                thr = gatechain.chain_thresholds(g["ref"].astype(np.float64), n, float(g["threshold"]), 1e-3,
                                                 chain, window=(int(g["ws"][0]), int(g["we"][0])))["thresholds"]
            else:
                thr = tuple(float(x) for x in g["thr"])
            starts = g["starts"].astype(np.uint64); ws = g["ws"].astype(np.uint64); we = g["we"].astype(np.uint64)
            nb = len(starts)
            p = _core.HMF(n, 1, nt, list(chain), 32, spec.shape[1] if spec.shape[1] in (n, n // 2) else n)
            p.set_reference(g["ref"]); p.set_template_batch(0, np.ascontiguousarray(spec)); p.set_thresholds(list(thr))
            idx = np.zeros((nb, nt, 1), np.int64); val = np.zeros((nb, nt, 1), np.complex64)
            mag = np.zeros((nb, nt, 1), np.float32); cnt = np.zeros((nb, nt), np.int32)
            sv = ser.view(np.float32)
            run = lambda: p.run_series(sv, starts, ws, we, 0, nt, n, float(g["threshold"]), idx, val, mag, cnt)
            run()
            prev = p.tier_stats(); walls, rows = [], []
            for _ in range(a.reps):
                w0 = time.perf_counter(); run(); walls.append(time.perf_counter() - w0)
                cur = p.tier_stats(); rows.append([(c[1] - q[1], c[2] - q[2]) for c, q in zip(cur, prev)]); prev = cur
            med = np.median(np.array(rows), axis=0)            # [tier][passed, ticks]
            wall = float(np.median(walls))
            key = chain
            acc = tot.setdefault(key, {"ticks": np.zeros(len(chain) + 1), "passed": np.zeros(len(chain) + 1),
                                       "pairs": 0, "wall": 0.0, "calls": 0})
            acc["ticks"] += med[:, 1]; acc["passed"] += med[:, 0]; acc["pairs"] += nb * nt
            acc["wall"] += wall; acc["calls"] += 1
    for chain, acc in tot.items():
        pairs = acc["pairs"]; wall_t = acc["wall"] * tps
        print(f"chain {chain}: {acc['calls']} group calls, {pairs} pairs, {acc['wall']*1e3/acc['calls']:.1f} ms/call, "
              f"{wall_t/pairs:.0f} ticks/pair")
        names = [f"tier{i}({b})" for i, b in enumerate(chain)] + ["refine"]
        for i, nm in enumerate(names):
            share = acc["ticks"][i] / wall_t
            print(f"   {nm:12s} {acc['ticks'][i]/pairs:7.1f} ticks/pair  {share:6.1%}   passed {acc['passed'][i]/pairs:.4f} of pairs")
        other = wall_t - acc["ticks"].sum()
        print(f"   {'untracked':12s} {other/pairs:7.1f} ticks/pair  {other/wall_t:6.1%}   (forward FFT, ingest, bookkeeping)")


if __name__ == "__main__":
    main()
