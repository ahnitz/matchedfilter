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
