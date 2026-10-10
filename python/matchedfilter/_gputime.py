"""Device-time collection across GPU contexts (MF_GPU_TIMING=1).

The contract every backend follows: with MF_GPU_TIMING=1 a Context registers itself here and
records the device time of each submission as (label, device_ms) in ``timing_log``; its
``timings()`` settles outstanding measurements and returns that log. Off, nothing registers.
"""
import os
import weakref

_CONTEXTS = weakref.WeakSet()


def enabled():
    return os.environ.get("MF_GPU_TIMING", "0") not in ("", "0")


def register(ctx):
    _CONTEXTS.add(ctx)


def collect(clear=True):
    """{label: (calls, device_ms)} summed over every live context."""
    out = {}
    for ctx in list(_CONTEXTS):
        log = ctx.timings()
        for label, ms in log:
            n, t = out.get(label, (0, 0.0))
            out[label] = (n + 1, t + ms)
        if clear:
            log.clear()
    return out


def interval_ms(t0, t1, period_ns, valid_bits=64, host_ms=None):
    """Device milliseconds between two raw timestamps, or None for a pair that cannot be a
    real interval.

    - Timestamps carry valid_bits bits (VkQueueFamilyProperties.timestampValidBits): the
      difference is taken modulo 2^valid_bits, so a counter wrap between the two reads is
      still the right interval.
    - A zero timestamp is a query that was never written (or reset after it was): ladder
      totals of ~768,000 s were exactly such a pair, end minus 0 = the device's uptime.
    - No device interval can exceed the host time from submission to readback (host_ms).
    Rejected pairs are counted (rejected()), never summed."""
    if not valid_bits or t0 == 0 or t1 == 0:
        return None
    d = t1 - t0
    if valid_bits < 64:
        d &= (1 << valid_bits) - 1
    elif d < 0:
        return None
    ms = d * period_ns * 1e-6
    if host_ms is not None and ms > host_ms + 1.0:
        return None
    return ms


def rejected():
    """Timestamp pairs every live context discarded as impossible (see interval_ms)."""
    return sum(getattr(ctx, "timing_rejected", 0) for ctx in list(_CONTEXTS))
