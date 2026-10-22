"""Per-machine prices: a cost timed once and kept in MF_COST_FILE, so every process sharing
the file prices alike. One helper (price_once) holds the rule: this process's memo, else the
record on file, else measure and store first-writer-wins (a valid record another process
stored first is the one used)."""
from . import _core, _costfile


def price_once(memo, mkey, file_key, measure, read):
    """The price under mkey: memo[mkey], else read(the record under file_key in
    MF_COST_FILE) when that is a valid one (read returns None otherwise), else measure() ->
    (value, record to store or None), stored first-writer-wins. Kept in memo either way."""
    hit = memo.get(mkey)
    if hit is not None:
        return hit
    path = _costfile._cost_file()
    if path is not None:
        hit = read(_costfile._load_cost_file(path).get(file_key))
        if hit is not None:
            memo[mkey] = hit
            return hit
    hit, record = measure()
    if path is not None and record is not None:
        got = read(_costfile._store_first(path, file_key, record, lambda r: read(r) is not None))
        if got is not None:
            hit = got
    memo[mkey] = hit
    return hit


#: n -> whether the hierarchical series' block forward runs through the platform FFT
#: (vDSP on macOS): priced once per n (_cpu_forward_platform), kept in MF_COST_FILE.
_CPU_FWD_PFFT = {}


_Q15_TIER0 = {}


def _q15_tier0_fp16(band):
    """Whether tier 0 behind the Q15 screen runs on the FP16 gate at this band: both kernels
    are timed once on a synthetic survivor list (_core.price_q15_tier0) and the cheaper is
    kept ("q15-tier0|band" in MF_COST_FILE). The FP16 gate reports an upper bound on the
    FP32 magnitude, so its survivors are a superset of the FP32 pass's and the next tier and
    the refine decide them; only time is at stake, and a whole-call trial of a tier ~10% of
    a call sits at the shared rule's tie (gatechain.measured_choice), so it is priced."""
    band = int(band)
    if not getattr(_core, "gate16", lambda: False)():
        _Q15_TIER0[band] = False
        return False

    def measure():
        try:
            fp32, fp16 = _core.price_q15_tier0(band, 128)
        except Exception:                      # noqa: BLE001 -- no price: keep the FP32 pass
            fp32, fp16 = 1.0, -1.0
        hit = bool(fp16 > 0 and fp16 < fp32)
        return hit, {"fp16": hit, "ticks": {"fp32": fp32, "fp16": fp16}}
    return price_once(_Q15_TIER0, band, "q15-tier0|%d" % band, measure,
                      lambda r: bool(r["fp16"]) if isinstance(r, dict) and "fp16" in r else None)


def _cpu_forward_platform(n):
    """Whether the block forward at n is cheaper through the platform FFT. Both transforms
    are timed once on this size (_core.forward_cost: copy with 1/n and transform, best of a
    few repetitions) and the cheaper is kept ("cpu-fft|n|cpu" in MF_COST_FILE). Their
    results differ by fp32 rounding only, so this is a price, not a contest: a trial over
    whole calls dilutes a transform that is ~11% of a call below the shared tie margin
    (gatechain.measured_choice), which kept the slower transform in half of fresh files."""
    n = int(n)

    def measure():
        native, platform = _core.forward_cost(n)
        hit = bool(platform > 0 and platform < native)
        return hit, {"platform": hit, "seconds": {"engine": native, "platform": platform}}
    return price_once(_CPU_FWD_PFFT, n, "cpu-fft|%d|cpu" % n, measure,
                      lambda r: bool(r["platform"]) if isinstance(r, dict) and "platform" in r
                      else None)


#: (backend, gate kind) key -> ticks per lag x tap of the direct refine (_direct_lagtap).
_DIRECT_LAGTAP = {}


def _direct_lagtap():
    """Ticks per lag x tap of the direct refine on this machine: timed once and kept in
    MF_COST_FILE, so every process sharing the file prices chains alike (the chain choice
    depends on it)."""
    from . import gatechain
    key = "direct-lagtap|%s|%s" % (_core.backend() if hasattr(_core, "backend") else "",
                                   gatechain.cpu_gate_kind())

    def measure():
        v = float(_core.price_direct())
        return v, ({"value": v} if v > 0 else None)     # a failed price is not stored
    return price_once(_DIRECT_LAGTAP, key, "choice|" + key, measure,
                      lambda r: float(r["value"]) if isinstance(r, dict)
                      and isinstance(r.get("value"), (int, float)) and r["value"] > 0 else None)
