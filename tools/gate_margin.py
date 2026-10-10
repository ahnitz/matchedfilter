#!/usr/bin/env python3
"""One validation harness for every narrow first tier: x86 Q15 screen, GPU fp16 coarse.

A narrow gate (int16, fp16) decides per (block, template) pair whether the pair's coarse
maximum max_k |y_k| might reach the tier threshold; survivors are re-checked exactly. The
gate is safe iff it never rejects a pair whose exact maximum reaches the threshold. This
harness measures that directly, from the gate's DECISIONS only, so it applies unchanged to
any implementation (CPU screen, GPU kernel) without access to its internals:

  * Each pair's exact coarse maximum ref is computed in float64 (numpy), and the inputs are
    scaled so ref = K for every pair (one data row per call, each template scaled), so one
    global threshold grid thr = K (1 + delta) probes every pair at once.
  * thr_max = the largest grid threshold at which the gate still passes the pair.
  * slack = thr_max / ref - 1. slack < 0 means a rejected exact pass: a false dismissal the
    gate added. The pass criterion is min slack > 0 over every family.
  * For a gate that exposes its statistic s (Q15: q15_screen's stat), margin use
    u = (ref - s) / (thr_max - s): the fraction of the gate's own margin its error used.
    The criterion is max u < 0.5 (2x headroom); a margin fitted until tests pass shows u ~ 1.

Families (coarse spectra of length N): white noise, profile-shaped templates, injections,
a loud broadband transient, and full scale (K near the top of fp16 range, where a gate
that scales nothing overflows). Each family runs at the requested N.

    python tools/gate_margin.py --gate q15 --n 64 128 256 512 1024
    python tools/gate_margin.py --gate gpu-c16 --n 128 256 512 1024 --device gpu:0 --loud

--device picks the backend as the library does (Metal on Apple, CUDA on NVIDIA, else
Vulkan), so the same command runs the full harness on every GPU.
    python tools/gate_margin.py --gate q15 gpu-c16 --json out.json

The NEON fp16 gate (src/gate16.cc) reports its statistic through MF_GATE16_DEBUG and is
measured by tools/gate16_error.py on ARM; an adapter belongs here once the gate is exposed
per call (as q15_screen is). See docs/cross-platform-review.md section 6.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "python"))

# Thresholds relative to ref: fine near 1 (fp16/Q15 errors are ~1e-3..1e-2), coarse beyond.
# delta = 0 (thr = ref exactly) is on the grid: rejecting there IS a dismissal.
_DELTAS = np.unique(np.round(np.concatenate([np.arange(-100, 101) * 0.0002,
                                             np.arange(-60, 61) * 0.005, [0.0]]), 6))


def exact_max(D, T):
    """float64 max_k |sum_j D_j conj(T_j) e^{2 pi i jk/N}| per (row, template)."""
    N = D.shape[1]
    y = np.fft.ifft(D[:, None, :].astype(np.complex128) * np.conj(T[None].astype(np.complex128)),
                    axis=2) * N
    return np.abs(y).max(axis=2)


def families(N, rng, nt):
    """(name, D (1, N), T (nt, N), K) cases. T rows are scaled so every pair's exact max is K."""
    from matchedfilter.benchmark import _inspiral_power
    white = lambda *s: (rng.standard_normal(s) + 1j * rng.standard_normal(s))
    shape = np.sqrt(_inspiral_power(8 * N)[:N]).astype(np.float64)
    shape /= shape.max()
    out = []
    for rep in range(4):
        out.append(("noise", white(1, N), white(nt, N), 1.0))
        out.append(("profile", white(1, N) * shape, white(nt, N) * shape, 1.0))
        T = white(nt, N) * shape
        lag = rng.integers(0, N, nt)
        D = white(1, N) * shape + 12.0 * T[0] * np.exp(-2j * np.pi * lag[0] * np.arange(N) / N)
        out.append(("injection", D, T, 1.0))
        burst = np.zeros(N, complex)
        t0 = int(rng.integers(0, N - 8))
        burst[t0:t0 + 8] = 200.0 * np.exp(1j * np.linspace(0, 6, 8))
        out.append(("transient", white(1, N) + np.fft.fft(burst)[None], white(nt, N), 1.0))
        out.append(("fullscale", white(1, N) * shape, white(nt, N) * shape, 3.0e4))
    cases = []
    for name, D, T, K in out:
        ref = exact_max(D, T)[0]
        T = T * (K / ref)[:, None]
        cases.append((name, D.astype(np.complex64), T.astype(np.complex64), K))
    return cases


class Q15:
    """The x86 Q15 screen (src/q15-inl.h) through _core.MF.q15_screen."""
    name = "q15"

    def __init__(self, N, nt):
        from matchedfilter import _core
        self.m = _core.MF(N, 1, nt)
        self.N, self.nt = N, nt
        if self.m.q15_lanes() == 0:
            raise RuntimeError("no Q15 screen on this back end")

    def load(self, D, T):
        # _core.MF correlates D against conj(T) itself (checked: its float tier gives ref).
        self.m.set_data_batch(0, D.astype(np.complex64).view(np.float32).tobytes())
        self.m.set_template_batch(0, T.view(np.float32).tobytes())

    def decide(self, thr):
        ps = np.zeros(self.nt, np.uint8)
        st = np.zeros(self.nt, np.float32)
        self.m.q15_screen(0, 1, 0, self.nt, float(thr), 0, self.N, ps, st)
        return ps.astype(bool), st


def gpu_backend(device):
    """(compute module, index) for a device spec, chosen exactly as the library chooses it:
    Metal on Apple, CUDA on NVIDIA, else Vulkan."""
    from matchedfilter.device import parse
    dev = parse(device)
    backend = getattr(dev, "backend", None)
    if backend == "metal":
        from matchedfilter import _mtlcompute as mod
    elif backend == "cuda":
        from matchedfilter import _cudacompute as mod
    else:
        from matchedfilter import _vkcompute as mod
    return mod, dev.index


class GpuC16:
    """The GPU first tier at band N (fp16 coarse where shipped) through hier_peaks, on any
    backend (Vulkan, CUDA, Metal: the contract is the same): every pair the tier passes is
    refined with threshold 0, so idx >= 0 marks the pass."""
    name = "gpu-c16"
    n = 4096

    def __init__(self, N, nt, device="gpu:0"):
        mod, index = gpu_backend(device)
        self.ctx = mod.Context(index)
        self.name = "gpu-c16/" + mod.__name__.rsplit("._", 1)[-1].replace("compute", "")
        self.N, self.nt = N, nt

    def load(self, D, T):
        rng = np.random.default_rng(0)
        self.data = (rng.standard_normal((1, self.n)) * 1e-3).astype(np.complex64)
        self.data[:, :self.N] = D
        self.tmpl = np.zeros((self.nt, self.n), np.complex64)
        self.tmpl[:, :self.N] = T                  # the tier correlates D with conj(ct0)
        self.ct0 = np.ascontiguousarray(self.tmpl[:, :self.N])
        self.fresh = True

    def decide(self, thr):
        idx, _ = self.ctx.hier_peaks(self.n, self.N, self.data, self.tmpl, self.ct0, float(thr),
                                     binsize=self.n, threshold=0.0, upload_data=self.fresh,
                                     upload_tmpl=self.fresh)
        self.fresh = False
        return idx.reshape(self.nt) >= 0, None


def measure(gate, cases):
    rows = {}
    for name, D, T, K in cases:
        gate.load(D, T)
        thr_max = np.full(T.shape[0], -np.inf)
        stat = None
        for d in _DELTAS:
            thr = K * (1 + d)
            passed, st = gate.decide(thr)
            thr_max = np.where(passed, np.maximum(thr_max, thr), thr_max)
            if st is not None and stat is None:
                stat = st.astype(np.float64)
        # A pair never passed on the grid has slack below its bottom (-0.3); report it as -1.
        slack = np.where(np.isfinite(thr_max), thr_max / K - 1, -1.0)
        r = rows.setdefault(name, dict(pairs=0, slack=[], use=[]))
        r["pairs"] += len(slack)
        r["slack"].extend(slack.tolist())
        if stat is not None:
            m = thr_max - stat
            r["use"].extend(np.where(m > 0, (K - stat) / np.where(m > 0, m, 1), np.inf).tolist())
    out = {}
    for name, r in rows.items():
        s = np.array(r["slack"])
        u = np.array(r["use"]) if r["use"] else None
        out[name] = dict(pairs=r["pairs"], dismissals=int((s < 0).sum()),
                         slack_min=float(s.min()), slack_p001=float(np.quantile(s, 0.001)),
                         slack_median=float(np.median(s)),
                         use_max=None if u is None else float(u.max()),
                         use_p999=None if u is None else float(np.quantile(u, 0.999)))
        out[name]["ok"] = out[name]["dismissals"] == 0 and (u is None or out[name]["use_max"] < 0.5)
    return out


def loud_end_to_end(device, snrs=(100, 1000, 2000, 2500, 3000, 10000)):
    """CPU against GPU HierarchicalFilter on a batch with one loud injection: the number of
    peaks each returns. A narrow tier that overflows must still pass the loud pair (fail
    open); it must never change the other pairs' results."""
    import matchedfilter as mf
    from matchedfilter.benchmark import _inspiral_power
    n, nd, nt = 4096, 4, 16
    power = _inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)
    rng = np.random.default_rng(2026)
    tm = (h * np.exp(2j * np.pi * rng.random((nt, n)) * 0.05)).astype(np.complex64)
    noise = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    rows = []
    for snr in snrs:
        data = noise.copy()
        data[1] += snr * np.conj(tm[3]) / np.linalg.norm(tm[3]) * np.sqrt(n)
        got = []
        for dev in (None, device):
            hf = mf.HierarchicalFilter(n, nd, nt, chain=(256,), snr=5.5, fd=1e-3, device=dev)
            hf.set_reference(power)
            hf.set_templates(np.conj(tm))
            hf.set_data(data)
            r = hf.run(binsize=n // 4, threshold=6.0 * np.sqrt(n))
            got.append((int((r["index"] >= 0).sum()), float(np.abs(r["value"]).max()) / np.sqrt(n)))
        rows.append((snr, got[0], got[1]))
        print("loud injection snr %6d: cpu %3d peaks (max %.0f)  %s %3d peaks (max %.0f)  %s"
              % (snr, got[0][0], got[0][1], device, got[1][0], got[1][1],
                 "ok" if got[0][0] == got[1][0] else "DIFFERS"))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", nargs="+", default=["q15"], choices=["q15", "gpu-c16"])
    ap.add_argument("--n", type=int, nargs="+", default=[128, 256, 512, 1024])
    ap.add_argument("--templates", type=int, default=64)
    ap.add_argument("--device", default="gpu:0")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--json")
    ap.add_argument("--loud", action="store_true",
                    help="also run the end-to-end loud-injection check on --device")
    args = ap.parse_args()
    report = {}
    if args.loud:
        report["loud"] = loud_end_to_end(args.device)
    for g in args.gate:
        for N in args.n:
            rng = np.random.default_rng(args.seed + N)
            try:
                gate = (Q15(N, args.templates) if g == "q15" else
                        GpuC16(N, args.templates, args.device))
            except Exception as e:                       # noqa: BLE001
                print("%-8s N=%-5d unavailable: %s" % (g, N, e))
                continue
            res = measure(gate, families(N, rng, args.templates))
            report["%s/%d" % (gate.name, N)] = res
            for fam, r in res.items():
                print("%-12s N=%-5d %-10s pairs %5d  dismissals %3d  slack min %+.4f p0.1%% %+.4f "
                      "median %+.4f  margin use max %s  %s"
                      % (gate.name, N, fam, r["pairs"], r["dismissals"], r["slack_min"], r["slack_p001"],
                         r["slack_median"], "-" if r["use_max"] is None else "%.3f" % r["use_max"],
                         "ok" if r["ok"] else "FAIL"))
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
