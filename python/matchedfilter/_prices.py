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


#: (n, backend, gate kind) key -> (ticks per lag x tap, ticks per transform pair): the prices a
#: survivor's direct-or-transform refine compares (_direct_pair_prices).
_DIRECT_PAIR = {}


def _direct_pair_prices(n, plan):
    """The prices every CPU plan of size n compares, per survivor, to refine it directly or by
    its whole-block transform: timed once on `plan`'s kernels and kept in MF_COST_FILE. A plan
    timing its own made the choice depend on that plan's timing noise: two plans of one bank
    layout, a merged call and its separate calls, refined the pairs near the boundary
    differently and so reported them to different fp32 rounding."""
    from . import gatechain
    key = "direct-pair|%d|%s|%s" % (int(n), _core.backend() if hasattr(_core, "backend") else "",
                                     gatechain.cpu_gate_kind())

    def measure():
        got = plan.price_direct_pair()
        if not got or not (got[0] > 0 and got[1] > 0):
            return None, None                  # a failed price is not stored; the plan times its own
        return (float(got[0]), float(got[1])), {"lagtap": float(got[0]), "fftpair": float(got[1])}

    def read(r):
        if isinstance(r, dict) and all(isinstance(r.get(k), (int, float)) and r[k] > 0
                                       for k in ("lagtap", "fftpair")):
            return (float(r["lagtap"]), float(r["fftpair"]))
        return None
    return price_once(_DIRECT_PAIR, key, "choice|" + key, measure, read)
