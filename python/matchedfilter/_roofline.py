"""Fraction of theoretical throughput: one metric, the same on every platform.

    fraction = roofline time per segment / measured steady wall time per segment

    roofline time = sum over stages s of max(flops_s / peak_flops(precision_s),
                                             bytes_s / peak_bandwidth)

The stages of one segment of the three-level search (tools/ladder.py):

  root        (hierarchical search) the root's output per block and channel: the band
              product and one real inverse of length n. fp32.
  middle      the middle bank's correlation (engine 'corr'): per block of length n a
              forward transform, per (block, template) pair a complex product and an
              inverse. fp32.
  forward     the fine banks' forward transforms: one per (block) of each fine group.
              fp32.
  tier<i>     coarse gate tier i at band b, on what the engine ran it on: tier 0 over
              every block against the templates -- or against the shared screeners where
              the tier runs on them ((block, screener) pairs) -- and tier i > 0 over tier
              i-1's survivors, or the (block, sub-screener) pairs they map to (the CPU's
              tier-1 sub-screeners). Precision: int16 where the CPU's Q15 screen ran (the
              screen IS tier 0: there is no float pass behind it), fp16 where the backend
              runs the packed half-precision gate (GPU tier 0, ARM gate16), else fp32.
  refine      the full length-n correlation of every pair the last tier passed. fp32.
  followups   the single-template, threshold-0 follow-ups: per block a forward transform
              and one full pair. fp32.

Work per stage, in samples and bins only (the library is unit-agnostic):

  flops   the algorithmic count already used by tools/gpu_roofline.py and
          tools/metal_roofline.py: 5 n log2 n per length-n transform, and per
          (block, template) pair 6 n (complex product) + 5 n log2 n (inverse) + 3 n
          (|z|^2 and the running maximum; omitted for the middle stage, which writes the
          series rather than peaks). Twiddles, addressing and barriers are not counted.
  bytes   the minimum DRAM traffic, the unique data the stage must touch:
            middle    input windows once (8 B/sample), template spectra once per call
                      (8 B x stored bins), and the requested output window per template
                      (8 B/sample).
            forward   block inputs, non-overlapping (8 n_valid B).
                      A transform's output spectrum is not charged in any stage (middle,
                      forward, follow-ups): its consumers can read it where it is made (the
                      CPU's fused path keeps it in cache), so writing it out is not minimum
                      traffic. A device that writes it pays that as measured time.
            tier i    data band rows and template band rows at the tier's precision
                      (4 B per complex fp16/int16 value, 8 B fp32) and 8 B per survivor
                      (its pair id). For i > 0 and the refine the rows read are bounded
                      by min(input pairs, rows) per group over the measured span.
            refine    data rows (8 n B) and template rows (8 B x stored bins) bounded as
                      above, and 12 B per output bin (index + complex value).
            followups the window's input, one template row and 12 B per output bin.
            root      the band of the block's spectrum and of the root's (8 B a bin each)
                      and the n-sample real series it outputs (4 n B: a stage's result,
                      charged as the middle's output windows are, not a transform's
                      intermediate spectrum); flops 6 per band bin and
                      2.5 n log2 n for the real inverse.

Counts come from what the run did, not from a model of it:
  * middle: TimeDomainFilterBank counters (_corr_work, _corr_in_samples) incremented
    where the blocks are chosen (time_domain._correlate_windows);
  * fine stage: each hierarchical plan's work_counts() -- the engine's own pair, tier-input
    (checked: the pairs or screener pairs each tier ran on), tier-pass and refine counters
    on the CPU (ap_hmf_stats/tier_inputs/tier_stats/q15_stats), and the per-call pair,
    tier-0 input, last_tier1_survivors and last_refinements accumulators on the GPU
    (group_work holds the arithmetic);
  * follow-ups: the ladder's job list, laid out with the bank's own _window_layout.
Blocks of a fine group are pairs / templates in the group (every fine call takes the whole
group; follow-ups use separate single-template plans and are not in these counters).
Device follow-ups are counted from the host rule's job list, which the ladder checks
against the device's items.

Judgement calls (stated so that nobody tunes them to flatter a platform):
  1. Work the implementation does that the algorithm does not need -- zeroing the parts
     of the middle output outside the windows, padding pairs in ragged tiles, the pack
     of coarse bands, host-side work, fills -- is NOT roofline work. It shows up only as
     measured time.
  2. The gate's work is counted as run: the chain and thresholds the autotuner chose, the
     shared screeners it ran on, and the survivors that chain produced. A chain with more
     survivors has more roofline work; that is the algorithm as run. Each transform is
     charged 5 n log2 n whatever algorithm and precision computes it (the Q15 screen's
     split-radix four-step does fewer operations): one convention on every device.
  3. The precision of a stage is the precision the backend executes it in. A packed fp16
     tier is compared with the fp16 peak.
  4. Peaks are THEORETICAL (data-sheet formula). The x86 int16 peak counts the vector
     int16 MULTIPLY pipes, not the FMA ports: Haswell/Broadwell have one (int16 then peaks
     at the fp32 rate, not twice it), Skylake+ and Zen 2-5 two (_x86_int16_mul_ports). The
     clock is cpuinfo_max_freq: with turbo on, the single-core turbo; with turbo off
     (intel_pstate no_turbo=1, as on the Haswell test node) the base clock, which the core
     can exceed (E5-2698 v3: 2.3 GHz basis, ~2.45 GHz sustained AVX2 FMA, so its fractions
     read ~6% high). The one measured peak is the CPU's memory bandwidth: one
     core cannot reach the socket's DRAM bandwidth, so a single-threaded CPU run uses one
     core's measured streaming bandwidth (a numpy copy, read + write bytes). Measured
     ceilings are recorded beside the theoretical ones but never used for the headline.
  5. CUDA's tensor cores are not counted in the fp16 peak: the gate's flops are FFT flops,
     and the vector fp16 peak is the rate those flops have. The tensor peak is recorded.
  6. The min(pairs, rows) bound for tiers > 0 and the refine is taken over the summed
     counts of a group, which can only overstate bytes when one call's survivors exceed
     its rows; with sparse survivors it is the survivor count.
  7. Measured time is the ladder's steady "segment" wall time per segment. Per-stage
     measured times are the ladder's stage timers (host wall; under --pipeline they
     overlap and on a GPU they are enqueue times) and, on the CPU, the engine's per-tier
     tick counters converted to seconds with a calibrated tick rate.
  8. Block lengths and chains are the ones the run used (the autotuner's, per device). A
     device that picks a shorter middle block does more transform work per sample and is
     credited with it; the ladder's report shows the counts so that choice stays visible.
"""
import math
import platform
import time

import numpy as np

from .time_domain import _stored_bins, _normalize_windows
from ._peaks import _MEASURED, _read
from . import _core, _kernels
from .device import parse

#: Bytes per complex value at each precision.
CBYTES = {"fp32": 8, "fp16": 4, "int16": 4}


# ---- the analytic work model (shared with tools/gpu_roofline.py, tools/metal_roofline.py) ---

def fft_flops(n):
    """Algorithmic flops of one complex length-n transform: 5 n log2 n."""
    return 5.0 * n * math.log2(n) if n > 1 else 0.0


def pair_flops(n, peak=True):
    """One (data, template) pair at length n: complex product 6n, inverse 5n log2 n and,
    with peak, |z|^2 and the running maximum 3n."""
    return 6.0 * n + fft_flops(n) + (3.0 * n if peak else 0.0)


class Stage:
    __slots__ = ("name", "precision", "flops", "bytes", "count", "unit", "measured_s")

    def __init__(self, name, precision, flops=0.0, nbytes=0.0, count=0, unit="pairs"):
        self.name, self.precision = name, precision
        self.flops, self.bytes, self.count, self.unit = float(flops), float(nbytes), count, unit
        self.measured_s = None

    def add(self, flops, nbytes, count):
        self.flops += flops
        self.bytes += nbytes
        self.count += count

    def terms_s(self, peaks):
        """(compute seconds, memory seconds) at the peaks. A term with work whose peak is
        unknown (missing, NaN or not positive) is NaN; a term without work is zero."""
        def seconds(work, peak):
            if not work:
                return 0.0
            return work / peak if (peak is not None and peak > 0) else float("nan")
        return (seconds(self.flops, peaks["flops"].get(self.precision)),
                seconds(self.bytes, peaks.get("bandwidth")))

    def roofline_s(self, peaks):
        """(seconds, bound): the larger of the compute and memory times and which one it is.
        When either term is unknown the time is NaN and the bound 'unknown': a missing peak
        never decides the bound by dropping out of the maximum."""
        tf, tb = self.terms_s(peaks)
        if math.isnan(tf) or math.isnan(tb):
            return float("nan"), "unknown"
        return max(tf, tb), ("compute" if tf >= tb else "memory")

    def as_dict(self, peaks, per=1.0):
        t, bound = self.roofline_s(peaks)
        tf, tb = self.terms_s(peaks)
        d = dict(stage=self.name, precision=self.precision, count=self.count / per, unit=self.unit,
                 flops=self.flops / per, bytes=self.bytes / per, roofline_s=t / per, bound=bound,
                 compute_s=tf / per, memory_s=tb / per)
        if self.measured_s is not None:
            d["measured_s"] = self.measured_s / per
        return d


class Work:
    """Stages keyed by name, in segment order."""

    def __init__(self):
        self.stages = {}

    def stage(self, name, precision, unit="pairs"):
        s = self.stages.get(name)
        if s is None:
            s = self.stages[name] = Stage(name, precision, unit=unit)
        elif s.precision != precision:
            return self.stage(name + "/" + precision, precision, unit)
        return s


# ---- counters -------------------------------------------------------------------------------

def _hier_groups(banks):
    for bank in banks:
        for g in bank._groups:
            if getattr(g, "is_hier", False) and g._plan is not None:
                yield g


def snapshot(middle_banks, fine_banks):
    """Every counter the work model reads, at one instant."""
    mid = {}
    for b in middle_banks:
        mid[id(b)] = (getattr(b, "_corr_in_samples", 0),
                      {n: dict(v) for n, v in getattr(b, "_corr_work", {}).items()})
    fine = {}
    for g in _hier_groups(fine_banks):
        fine[id(g)] = g.plan.work_counts()
    return dict(middle=mid, fine=fine)


def _sub(a, b):
    if isinstance(a, dict):
        return {k: _sub(a[k], (b or {}).get(k)) if k in a else None for k in a}
    if isinstance(a, list):
        b = b or [0] * len(a)
        return [_sub(x, y) for x, y in zip(a, b)] if len(b) == len(a) else list(a)
    if isinstance(a, (int, float)) and not isinstance(a, bool):
        return a - (b or 0)
    return a


def _backend_c16(device):
    """Whether the device runs tier 0 at `band` in packed fp16 (an fp16 coarse build shipped
    for the band in its driver's artifact family), as a function of band; None on a CPU."""
    d = parse(device)
    if d.kind != "gpu":
        return None
    # a device's backend names the artifact family its driver runs (DeviceProps)
    return lambda band: _kernels.shipped(d.backend, "tierb_%d_c16" % band)


def tier_precision(device, tier, band):
    """The precision a coarse tier executes in on this device."""
    c16 = _backend_c16(device)
    if c16 is not None:                                     # GPU: packed fp16 tier 0
        return "fp16" if tier == 0 and c16(band) else "fp32"
    if tier == 0:
        if getattr(_core, "gate16", lambda: False)():      # ARM FP16 first gate
            return "fp16"
    return "fp32"


def group_work(work, d, n, n_valid, nt, kt, nbins, device, problems=None):
    """Add one fine group's forward, tier and refine work from its counter deltas `d` (a
    work_counts() dict, or the difference of two) and return its CPU engine ticks per stage
    name (empty without ticks). n, n_valid: the block length and its valid samples; nt: the
    group's templates; kt: stored bins per template; nbins: output bins per block.

    The counts are the engine's own: `checked[i]` is what tier i ran on -- (block, screener)
    pairs where it runs on shared screeners (tier 0's, and the CPU's tier-1 sub-screeners),
    else the pairs it was handed -- and `passed[i]` the (block, template) pairs it passed.
    Where the int16 screen ran (CPU, `q15_on` with screen ticks), the screen IS tier 0: one
    int16 stage on tier 0's inputs, no float pass behind it (hmf.c)."""
    problems = problems if problems is not None else []
    ticks = {}
    pairs = d["pairs"]
    if not pairs:
        return ticks
    blocks = pairs / nt
    if abs(blocks - round(blocks)) > 1e-9:
        problems.append("group n=%d: pairs %d not a multiple of %d templates" % (n, pairs, nt))
    chain = tuple(d["chain"])
    if len(d["passed"]) != len(chain):
        problems.append("group n=%d chain %s: %d tier counters" % (n, chain, len(d["passed"])))
        return ticks
    t = d.get("ticks")
    # Forward: block input read, spectrum left where its consumers read it (minimum traffic;
    # a fused consumer reads it from cache, so writing it out is not the floor).
    s = work.stage("forward", "fp32", unit="blocks")
    s.add(blocks * fft_flops(n), blocks * n_valid * 8, blocks)
    if t:
        ticks["forward"] = t["series"] - sum(t["tiers"]) - t["refine"]
    screened = bool(d.get("q15") is not None and t and t["q15"] > 0)
    inputs = pairs
    for i, band in enumerate(chain):
        if d.get("checked") is not None:
            inputs = d["checked"][i]
        prec = "int16" if (i == 0 and screened) else tier_precision(device, i, band)
        surv = d["passed"][i]
        if i == 0:
            # tier 0 runs on every block: its template rows are the templates, or the shared
            # screeners it ran on (checked = blocks x screeners)
            rows_d, rows_t = blocks, min(nt, inputs / blocks if blocks else 0)
        elif inputs == pairs:
            rows_d, rows_t = blocks, nt
        else:
            rows_d, rows_t = min(inputs, blocks), min(inputs, nt)
        s = work.stage("tier%d b%d" % (i, band), prec)
        s.add(inputs * pair_flops(band), (rows_d + rows_t) * band * CBYTES[prec] + surv * 8,
              inputs)
        if t:
            ticks[s.name] = ticks.get(s.name, 0) + t["tiers"][i]
        inputs = surv
    r = d["refined"]
    s = work.stage("refine n%d" % n, "fp32")
    s.add(r * pair_flops(n), min(r, blocks) * n * 8 + min(r, nt) * kt * 8 + r * nbins * 12, r)
    if t:
        ticks[s.name] = ticks.get(s.name, 0) + t["refine"]
    return ticks


def fine_work(work, before, after, fine_banks, device, binsize=None, problems=None):
    """Add the fine stage's forward, tier and refine work between two snapshots
    (group_work per hierarchical group). Returns CPU engine ticks per stage name."""
    problems = problems if problems is not None else []
    ticks = {}             # CPU engine ticks per stage name (forward: the rest of run_series)
    for g in _hier_groups(fine_banks):
        a = after["fine"].get(id(g))
        if a is None:
            continue
        b = before["fine"].get(id(g))
        if b is not None and b.get("ident") != a.get("ident"):
            problems.append("group n=%d: plan rebuilt during the span; counted from its rebuild"
                            % g.n)
            b = None
        d = _sub(a, b) if b is not None else a
        nbins = max(1, -(-g.n_valid // binsize)) if binsize else 1
        got = group_work(work, d, g.n, g.n_valid, len(g.template_indices), _stored_bins(g),
                         nbins, device, problems)
        for k, v in got.items():
            ticks[k] = ticks.get(k, 0) + v
    return ticks


def middle_work(work, before, after, middle_banks):
    s = work.stage("middle", "fp32", unit="pairs")
    for bank in middle_banks:
        a_in, a = after["middle"].get(id(bank), (0, {}))
        b_in, b = before["middle"].get(id(bank), (0, {}))
        s.bytes += (a_in - b_in) * 8
        for n, v in a.items():
            d = _sub(v, b.get(n))
            s.add(d["blocks"] * fft_flops(n) + d["pairs"] * pair_flops(n, peak=False),
                  d["tmpl_values"] * 8 + d["out_samples"] * 8, d["pairs"])
    return s


def root_work(work, before, after):
    """The root stage between two HierarchicalSearch.root_counts snapshots ({n: [blocks,
    band bins]}): per block the band product (6 flops a bin) and one real inverse of length
    n (2.5 n log2 n); bytes the band of both spectra (16 B a bin) and the real output (4 n)."""
    s = work.stage("root", "fp32", unit="blocks")
    for n, (calls, bins) in after.items():
        c0, b0 = before.get(n, (0, 0))
        dc, db = calls - c0, bins - b0
        s.add(6.0 * db + dc * 2.5 * n * math.log2(n), 16.0 * db + dc * 4.0 * n, dc)
    return s


def followup_work(work, jobs, series_len=None):
    """The follow-up jobs [(bank, series, kwargs)] as run: one template each, laid out by the
    bank's own block layout. series_len: the series length, when the jobs' series are not
    kept (None)."""
    s = work.stage("followups", "fp32", unit="blocks")
    for bank, ser, kw in jobs:
        g, _ = bank._template_map[int(kw["template_index"])]
        S = int(np.shape(ser)[0]) if ser is not None else int(series_len)
        W = _normalize_windows(kw.get("windows"), S)
        st, ws, we = bank._window_layout(g, W, S)
        if not st.size:
            continue
        blocks = np.unique(st).size
        bs = int(kw.get("binsize") or bank.binsize or g.n)
        nbins = int(((we.astype(np.int64) - ws.astype(np.int64) + bs - 1) // bs).sum())
        kt = _stored_bins(g)
        s.add(blocks * (fft_flops(g.n) + pair_flops(g.n)),
              int((W[:, 1] - W[:, 0]).sum()) * 8 + kt * 8 + nbins * 12, blocks)
    return s


# ---- CPU tick rate --------------------------------------------------------------------------

_TICK_RATE = None


def cpu_tick_rate():
    """ap_ticks per second (TSC on x86, ns elsewhere), from a timed engine run."""
    global _TICK_RATE
    if _TICK_RATE is not None:
        return _TICK_RATE
    if platform.machine().lower() not in ("x86_64", "amd64", "i386", "i686"):
        _TICK_RATE = 1e9
        return _TICK_RATE
    n, nt, blocks = 1024, 8, 64
    rng = np.random.default_rng(0)
    spec = (rng.standard_normal((nt, n)) + 1j * rng.standard_normal((nt, n))).astype(np.complex64)
    S = blocks * (n // 2) + n
    ser = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64).view(np.float32)
    starts = (np.arange(blocks) * (n // 2)).astype(np.uint64)
    ws = np.full(blocks, n // 4, np.uint64)
    we = np.full(blocks, n, np.uint64)
    idx = np.zeros((blocks, nt, 1), np.int64); val = np.zeros((blocks, nt, 1), np.complex64)
    mag = np.zeros((blocks, nt, 1), np.float32); cnt = np.zeros((blocks, nt), np.int32)
    p = _core.HMF(n, 1, nt, [128], 8, n)
    p.set_reference(np.ones(n, np.float32)); p.set_template_batch(0, spec); p.set_thresholds([0.0])
    big = float(np.finfo(np.float32).max)
    rates = []
    for _ in range(5):
        t0, k0 = time.perf_counter(), p.series_ticks()
        while time.perf_counter() - t0 < 0.04:
            p.run_series(ser, starts, ws, we, 0, nt, n, big, idx, val, mag, cnt)
        rates.append((p.series_ticks() - k0) / (time.perf_counter() - t0))
    _TICK_RATE = float(max(rates))       # Python between calls only lowers the ratio
    return _TICK_RATE


# ---- platform peaks -------------------------------------------------------------------------


def _cpuinfo():
    txt = _read("/proc/cpuinfo") or ""
    info = {}
    for line in txt.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            info.setdefault(k.strip(), v.strip())
    return info


def cpu_bandwidth(nbytes=1 << 28, reps=5):
    """One core's streaming DRAM bandwidth: best numpy copy of nbytes, read + write bytes."""
    a = np.ones(nbytes // 8, np.float64)
    b = np.empty_like(a)
    best = 0.0
    for _ in range(reps):
        t = time.perf_counter()
        np.copyto(b, a)
        best = max(best, 2 * nbytes / (time.perf_counter() - t))
    return best


#: x86 vector FMA datapath (bits) and FMA-capable ports, by vendor and family: not queryable.
#: Vector int16 multiply pipes per core (vpmullw / vpmulhrsw / vpmaddwd), by microarchitecture:
#: the int16 peak is set by these, not by the FMA ports. Data-sheet sources: Intel's
#: optimization manual and uops.info port tables (Haswell/Broadwell: port 0 only; Skylake and
#: later: ports 0 and 1); AMD's Software Optimization Guides for families 17h/19h/1Ah (Zen 2-5:
#: two FP pipes take vector integer multiply). Confirmed by a 12-chain register-only loop of
#: each instruction: Haswell E5-2698 v3 vpmulhrsw 2.44 G/s against vfmadd 4.78 G/s at the
#: same clock (1 pipe vs 2); Zen 3 (5950X) and Zen 5 (Ryzen AI MAX+ 395) both at the vfmadd
#: rate (2 pipes).
def _x86_int16_mul_ports(vendor, fam, model):
    if vendor == "AuthenticAMD":
        return 2 if fam >= 0x17 else 1
    if vendor == "GenuineIntel" and fam == 6:
        # Haswell (0x3c 0x3f 0x45 0x46), Broadwell (0x3d 0x47 0x4f 0x56): one port.
        return 1 if model in (0x3c, 0x3f, 0x45, 0x46, 0x3d, 0x47, 0x4f, 0x56) else 2
    return 1


def _x86_core(info):
    flags = set(info.get("flags", "").split())
    vendor = info.get("vendor_id", "")
    fam = int(info.get("cpu family", "0"))
    model = int(info.get("model", "0"))
    isa = 512 if "avx512f" in flags else 256 if "avx2" in flags else 128
    ports = 2 if "fma" in flags else 1
    if vendor == "AuthenticAMD":
        # Zen 5 (family 0x1a) executes AVX-512 at full width on desktop, server and Strix
        # Halo parts; the mobile Strix Point (models 0x20-0x2f) and Krackan Point
        # (0x60-0x6f) have a 256-bit datapath. Zen 4 (0x19) double-pumps 256.
        narrow = fam == 0x1a and (model >> 4) in (0x2, 0x6)
        datapath = 512 if fam >= 0x1a and not narrow else 256 if fam >= 0x17 else 128
        name = {0x1a: "Zen 5", 0x19: "Zen 3/4", 0x17: "Zen 1/2"}.get(fam, "AMD")
    else:
        datapath = isa
        name = "Intel"
    imul = _x86_int16_mul_ports(vendor, fam, model)
    return min(isa, datapath), ports, name, imul


#: Apple cores: (clock GHz, 128-bit FMA pipes) of a performance core.
_APPLE_CPU = {"M1": (3.2, 4), "M2": (3.49, 4), "M3": (4.05, 4), "M4": (4.4, 4)}


def cpu_peaks(measure_bandwidth=True):
    """One core: SIMD lanes x FMA pipes x 2 x max clock per precision, and one core's
    measured streaming bandwidth."""
    mach = platform.machine().lower()
    out = dict(device="cpu", threads=1)
    if mach in ("arm64", "aarch64"):
        brand = ""
        try:
            import subprocess
            brand = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                   capture_output=True, text=True).stdout.strip()
        except OSError:
            pass
        chip = next((k for k in _APPLE_CPU if k in brand), None)
        # An unlisted chip's clock and pipes are unknown, not those of some other chip.
        ghz, pipes = _APPLE_CPU.get(chip, (float("nan"), float("nan")))
        if chip is None:
            out["unknown"] = ["clock and FMA pipes of %r (no entry in _APPLE_CPU)" % brand]
        width = 128
        out["name"] = brand or "arm64"
        lanes = dict(fp32=width // 32, fp16=width // 16, int16=width // 16)
        out["formula"] = ("%s x 128-bit FMA pipes x lanes x 2 x %s GHz (fp16: 8 lanes, NEON "
                          "FP16; int16: 8 lanes, multiply-accumulate)" % (
                              ("unknown", "unknown") if chip is None
                              else ("%d" % pipes, "%.2f" % ghz)))
        out["measured"] = _MEASURED.get("Apple %s CPU" % chip)
    else:
        info = _cpuinfo()
        width, pipes, uarch, imul = _x86_core(info)
        khz = _read("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
        # Without cpufreq (some VMs) the clock is the current reading in /proc/cpuinfo, and
        # the formula says so; without either it is unknown.
        clock_source = "cpuinfo_max_freq, the base clock where turbo is off"
        if khz:
            ghz = int(khz) / 1e6
        elif info.get("cpu MHz"):
            ghz, clock_source = float(info["cpu MHz"]) / 1e3, "the current 'cpu MHz' reading"
        else:
            ghz, clock_source = float("nan"), "unknown"
            out["unknown"] = ["CPU clock (no cpuinfo_max_freq and no 'cpu MHz')"]
        out["name"] = "%s (%s)" % (info.get("model name", "x86"), uarch)
        # No x86 FP16 arithmetic here (AVX512-FP16 aside): fp16 work runs at the fp32 rate.
        lanes = dict(fp32=width // 32, fp16=width // 32, int16=width // 16)
        out["formula"] = ("%d-bit datapath x %d FMA ports x lanes x 2 x %.3f GHz max clock "
                          "(fp16 at the fp32 rate: no FP16 vector arithmetic; int16: %d lanes x "
                          "%d int16 multiply pipe(s) x 2, multiply + add counted as one FMA; "
                          "clock = %s)" % (width, pipes, ghz, width // 16, imul, clock_source))
        out["measured"] = _MEASURED.get(uarch)
    out["clock_ghz"] = ghz
    out["flops"] = {p: lanes[p] * pipes * 2 * ghz * 1e9 for p in lanes}
    if mach not in ("arm64", "aarch64"):
        out["flops"]["int16"] = lanes["int16"] * imul * 2 * ghz * 1e9
    out["bandwidth"] = cpu_bandwidth() if measure_bandwidth else float("nan")
    if not measure_bandwidth:
        out.setdefault("unknown", []).append("memory bandwidth (not measured)")
    out["bandwidth_formula"] = "one core's streaming copy (numpy, read + write), measured"
    return out


def gpu_peaks(device, ctx=None):
    """Theoretical peaks of a GPU from API-queryable counts plus a stated formula: the
    driver's peak model (Context._x_peaks), which ctx -- a context on the device -- runs."""
    d = parse(device)
    if ctx is None:
        raise ValueError("no context on %s to ask for its peaks" % device)
    return ctx._x_peaks(dict(device=str(d), name=d.name, backend=d.backend))


def peaks(device, ctx=None, measure_bandwidth=True):
    d = parse(device)
    return cpu_peaks(measure_bandwidth) if d.kind == "cpu" else gpu_peaks(device, ctx)


def gpu_context(fine_banks):
    for g in _hier_groups(fine_banks):
        ctx = getattr(g.plan, "_gpu", None)
        if ctx is not None:
            return ctx
    return None


# ---- the report -----------------------------------------------------------------------------

def report(work, pk, segments, wall_s, measured=None):
    """The per-segment table and the fraction, as a JSON-able dict.

    work: Work over `segments` steady segments; wall_s: their measured wall time in total;
    measured: optional {stage name: seconds over the span}."""
    for name, t in (measured or {}).items():
        if name in work.stages:
            work.stages[name].measured_s = t
    def order(s):
        head = s.name.split()[0].split("/")[0]
        rank = {"middle": 0, "forward": 1, "q15": 2, "refine": 4, "followups": 5}.get(head, 3)
        return rank, s.name
    rows = [s.as_dict(pk, per=segments) for s in sorted(work.stages.values(), key=order)
            if s.count or s.flops]
    roof = sum(r["roofline_s"] for r in rows)
    wall = wall_s / segments
    problems = []
    blind = [r["stage"] for r in rows if r["bound"] == "unknown"]
    if blind:
        # Loud: the total and the fraction are NaN rather than a smaller, wrong number.
        problems.append("ROOFLINE INCOMPLETE: a peak is unknown, so stages %s have no roofline "
                        "time and the fraction is NaN; unknown: %s" % (
                            ", ".join(blind), "; ".join(pk.get("unknown") or
                                                        ["a peak is NaN or missing"])))
    known = [r for r in rows if not math.isnan(r["roofline_s"])]
    return dict(peaks=pk, segments=segments, stages=rows, roofline_s=roof, wall_s=wall,
                fraction=roof / wall if wall > 0 else float("nan"), problems=problems,
                dominant=max(known, key=lambda r: r["roofline_s"])["stage"] if known else None)


def format_report(r):
    pk = r["peaks"]
    lines = ["roofline (%s, %s): peaks %s; bandwidth %.0f GB/s" % (
        pk.get("device"), pk.get("name"),
        ", ".join("%s %.3g TFLOP/s" % (k, v / 1e12) for k, v in pk["flops"].items()),
        pk["bandwidth"] / 1e9),
        "  flops: " + pk.get("formula", ""), "  bandwidth: " + pk.get("bandwidth_formula", "")]
    for p in r.get("problems", []):
        if p.startswith("ROOFLINE INCOMPLETE"):
            lines.append("  WARNING: " + p)
    if pk.get("measured"):
        lines.append("  measured ceilings (not used): %s" % pk["measured"])
    lines.append("  %-14s %-5s %12s %-6s %10s %9s %8s %7s %11s" % (
        "stage", "prec", "count/seg", "unit", "GFLOP/seg", "MB/seg", "roof ms", "bound",
        "measured ms"))
    for s in r["stages"]:
        lines.append("  %-14s %-5s %12.0f %-6s %10.2f %9.1f %8.2f %7s %11s" % (
            s["stage"], s["precision"], s["count"], s["unit"], s["flops"] / 1e9, s["bytes"] / 1e6,
            s["roofline_s"] * 1e3, s["bound"],
            "%.1f" % (s["measured_s"] * 1e3) if "measured_s" in s else "-"))
    lines.append("  roofline %.2f ms / measured wall %.1f ms per segment = %.2f%% of theoretical "
                 "(dominant stage: %s)" % (r["roofline_s"] * 1e3, r["wall_s"] * 1e3,
                                           100 * r["fraction"], r["dominant"]))
    for p in r.get("problems", []):
        lines.append("  NOTE: " + p)
    return "\n".join(lines)
