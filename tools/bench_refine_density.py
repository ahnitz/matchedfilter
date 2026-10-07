"""Refine (and later-tier) cost per survivor as a function of survivor density.

Production-shaped calls: n=2048, ~53 templates per plan, 377 blocks per
run_series call, one coarse tier (or a two-tier chain). The coarse threshold is
placed to give each target survivor density; costs are the engine's per-tier
tick counters (HMF.tier_stats), so no wall-clock subtraction is involved.

usage: bench_refine_density.py [--n 2048] [--nt 53] [--blocks 377] [--chain 256]
                               [--densities .01 .03 .1] [--reps 5] [--profile-density .01]
With --profile-density, loops at that density for --seconds (for a sampling profiler).
"""
import argparse, time
import numpy as np
from matchedfilter import _core


def _tsc_rate():
    """TSC ticks per second, from the clock the engine's counters use."""
    import ctypes, ctypes.util
    # rdtsc is not reachable from Python directly; time a known interval against the
    # engine's own counter by running an empty-threshold tier for a measured duration.
    t0 = time.perf_counter_ns(); c0 = _rdtsc(); time.sleep(0.2); c1 = _rdtsc(); t1 = time.perf_counter_ns()
    return (c1 - c0) / ((t1 - t0) * 1e-9)


def _rdtsc():
    import ctypes, mmap
    if not hasattr(_rdtsc, "fn"):
        code = bytes([0x0F, 0x31, 0x48, 0xC1, 0xE2, 0x20, 0x48, 0x09, 0xD0, 0xC3])   # rdtsc; shl rdx,32; or rax,rdx; ret
        buf = mmap.mmap(-1, len(code), prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
        buf.write(code)
        addr = ctypes.addressof(ctypes.c_char.from_buffer(buf))
        _rdtsc.buf = buf
        _rdtsc.fn = ctypes.CFUNCTYPE(ctypes.c_uint64)(addr)
    return _rdtsc.fn()


def setup(n, nt, blocks, seed=11):
    rng = np.random.default_rng(seed)
    taps = n // 4
    h = np.zeros((nt, n), np.complex64)
    h[:, :taps] = rng.standard_normal((nt, taps)) / np.sqrt(taps)
    spec = np.fft.fft(h, axis=1).astype(np.complex64)
    step = n - taps
    S = (blocks + 1) * step + n
    x = (rng.standard_normal(S) + 1j * rng.standard_normal(S)) / np.sqrt(2)
    X = np.fft.fft(x); X[S // 2:] = 0
    ser = (np.fft.ifft(X) * np.sqrt(2)).astype(np.complex64).view(np.float32)
    starts = (np.arange(blocks) * step).astype(np.uint64)
    ws = np.full(blocks, taps, np.uint64); we = np.full(blocks, n, np.uint64)
    ref = np.zeros(n, np.float32); ref[:n // 2] = 1.0
    return spec, ser, starts, ws, we, ref


def make(n, nt, chain, spec, ref, thr):
    p = _core.HMF(n, 1, nt, list(chain), 32, n)
    p.set_reference(ref); p.set_template_batch(0, spec); p.set_thresholds(list(thr))
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2048)
    ap.add_argument("--nt", type=int, default=53)
    ap.add_argument("--blocks", type=int, default=377)
    ap.add_argument("--chain", type=int, nargs="+", default=[256])
    ap.add_argument("--densities", type=float, nargs="+", default=[.01, .03, .1])
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--profile-density", type=float)
    ap.add_argument("--seconds", type=float, default=20)
    ap.add_argument("--model", action="store_true",
                    help="account a whole chain at the gate model's own thresholds (snr 6, fd 1e-3)")
    a = ap.parse_args()
    n, nt, blocks = a.n, a.nt, a.blocks
    spec, ser, starts, ws, we, ref = setup(n, nt, blocks)
    idx = np.zeros((blocks, nt, 1), np.int64); val = np.zeros((blocks, nt, 1), np.complex64)
    mag = np.zeros((blocks, nt, 1), np.float32); cnt = np.zeros((blocks, nt), np.int32)
    big = float(np.finfo(np.float32).max)
    chain = tuple(a.chain)

    def run(p):
        return p.run_series(ser, starts, ws, we, 0, nt, n, 0.0, idx, val, mag, cnt)

    def thr_for(f):
        lo, hi = 0.0, 16.0
        for _ in range(16):
            mid = 0.5 * (lo + hi)
            p = make(n, nt, chain[:1], spec, ref, (mid,)); run(p)
            frac = p.tier_stats()[0][1] / (blocks * nt)
            lo, hi = (mid, hi) if frac > f else (lo, mid)
            if abs(frac - f) < 0.1 * f:
                break
        return mid

    rest = tuple(big for _ in chain[1:])
    if a.model:
        from matchedfilter import gatechain
        thr = gatechain.chain_thresholds(ref.astype(np.float64), n, 6.0, 1e-3, chain,
                                         window=(n // 4, n))["thresholds"]
        p = make(n, nt, chain, spec, ref, thr); run(p)
        # TSC rate, to put the tier counters and wall time on one scale
        import ctypes
        t0w = time.perf_counter(); s0 = p.tier_stats(); run(p); t1w = time.perf_counter()
        walls, rows = [], []
        prev = p.tier_stats()
        for _ in range(a.reps):
            w0 = time.perf_counter(); run(p); walls.append(time.perf_counter() - w0)
            cur = p.tier_stats(); rows.append([c[2] - q[2] for c, q in zip(cur, prev)]); prev = cur
        ticks = np.median(np.array(rows), axis=0)
        wall = float(np.median(walls))
        # calibrate ticks/second from a busy loop through the engine itself
        tps = _tsc_rate()
        pairs = blocks * nt
        print(f"chain {chain} thresholds {tuple(round(x,2) for x in thr)}  wall {wall*1e3:.1f} ms/call = {wall*tps/pairs:.0f} ticks/pair")
        names = [f"tier{i}({b})" for i, b in enumerate(chain)] + ["refine"]
        for nm, t in zip(names, ticks):
            print(f"   {nm:12s} {t/pairs:7.1f} ticks/pair  ({t/(wall*tps):5.1%} of wall)")
        other = wall * tps - ticks.sum()
        print(f"   {'untracked':12s} {other/pairs:7.1f} ticks/pair  ({other/(wall*tps):5.1%} of wall)  <- forward FFT + ingest + bookkeeping")
        st = p.tier_stats()
        print("   passes per call:", [round(x[1] / (a.reps + 2)) for x in st])
        return
    if a.profile_density:
        g = thr_for(a.profile_density)
        p = make(n, nt, chain, spec, ref, (g,) + rest)
        t0 = time.time(); calls = 0
        while time.time() - t0 < a.seconds:
            run(p); calls += 1
        st = p.tier_stats()
        print(f"profiled {calls} calls; tier_stats {st}")
        return
    print(f"n={n} nt={nt} blocks={blocks} chain={chain}  (ticks; per pair for tier 0, per survivor otherwise)")
    for f in a.densities:
        g = thr_for(f)
        p = make(n, nt, chain, spec, ref, (g,) + rest)
        run(p)
        prev = p.tier_stats(); rows = []
        for _ in range(a.reps):
            run(p); cur = p.tier_stats()
            rows.append([(c[1] - q[1], c[2] - q[2]) for c, q in zip(cur, prev)]); prev = cur
        med = [(np.median([r[i][0] for r in rows]), np.median([r[i][1] for r in rows])) for i in range(len(prev))]
        pairs = blocks * nt
        dens = med[0][0] / pairs
        line = f"density {dens:6.4f}: tier0 {med[0][1]/pairs:6.0f}/pair"
        for i in range(1, len(chain)):
            line += f"  tier{i} {med[i][1]/max(med[i-1][0],1):6.0f}/survivor"
        line += f"  refine {med[-1][1]/max(med[-1][0],1):6.0f}/refined ({med[-1][0]:.0f} refined/call, {med[-1][0]/blocks:.2f}/block)"
        print(line)


if __name__ == "__main__":
    main()
