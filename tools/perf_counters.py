#!/usr/bin/env python3
"""Self-profiling hardware counters for a single-threaded call, via perf_event_open.

No perf binary and no permission change: a process may count its own user-mode events
whenever /proc/sys/kernel/perf_event_paranoid <= 2 (the default on most distributions).
Kernel events are excluded, so paranoid 2 suffices. Linux x86_64 and aarch64 only.

    from perf_counters import Counters
    with Counters() as c:
        work()
    print(c.read())        # {'cycles': ..., 'instructions': ..., 'ipc': ..., ...}

    python tools/perf_counters.py      # self-test: counts a numpy FFT

Events are the generic PERF_TYPE_HARDWARE / HW_CACHE ones, so the same names work on Intel
and AMD. Each event is its own group leader (no multiplexing constraints); scaled counts
(time_enabled / time_running) are reported when the PMU multiplexed them.
"""
import ctypes
import os
import platform
import struct

_NR = {"x86_64": 298, "aarch64": 241}

PERF_TYPE_HARDWARE, PERF_TYPE_HW_CACHE = 0, 3
HW = {"cycles": 0, "instructions": 1, "cache_references": 2, "cache_misses": 3,
      "branch_misses": 5, "stalled_frontend": 7, "stalled_backend": 8}
# HW_CACHE config: id | (op << 8) | (result << 16); op read = 0; result access 0, miss 1.
_L1D, _LL, _DTLB = 0, 2, 3
HW_CACHE = {"l1d_reads": _L1D | (0 << 8) | (0 << 16), "l1d_read_misses": _L1D | (0 << 8) | (1 << 16),
            "llc_read_misses": _LL | (0 << 8) | (1 << 16), "dtlb_read_misses": _DTLB | (0 << 8) | (1 << 16)}
DEFAULT = ("cycles", "instructions", "l1d_reads", "l1d_read_misses", "cache_misses",
           "stalled_backend", "branch_misses")

_READ_FORMAT = 1 | 2          # TOTAL_TIME_ENABLED | TOTAL_TIME_RUNNING
_IOC_ENABLE, _IOC_DISABLE, _IOC_RESET = 0x2400, 0x2401, 0x2403


class _Attr(ctypes.Structure):
    _fields_ = [("type", ctypes.c_uint32), ("size", ctypes.c_uint32), ("config", ctypes.c_uint64),
                ("sample_period", ctypes.c_uint64), ("sample_type", ctypes.c_uint64),
                ("read_format", ctypes.c_uint64), ("flags", ctypes.c_uint64),
                ("wakeup_events", ctypes.c_uint32), ("bp_type", ctypes.c_uint32),
                ("config1", ctypes.c_uint64), ("config2", ctypes.c_uint64),
                ("branch_sample_type", ctypes.c_uint64), ("sample_regs_user", ctypes.c_uint64),
                ("sample_stack_user", ctypes.c_uint32), ("clockid", ctypes.c_int32),
                ("sample_regs_intr", ctypes.c_uint64), ("aux_watermark", ctypes.c_uint32),
                ("sample_max_stack", ctypes.c_uint16), ("reserved", ctypes.c_uint16)]


# flags bits: disabled(0) inherit(1) pinned(2) exclusive(3) exclude_user(4) exclude_kernel(5)
# exclude_hv(6) exclude_idle(7)
_FLAGS = (1 << 0) | (1 << 5) | (1 << 6)


def paranoid():
    try:
        return int(open("/proc/sys/kernel/perf_event_paranoid").read())
    except OSError:
        return None


class Counters:
    """Count the named events on the calling thread between __enter__ and __exit__."""

    def __init__(self, events=DEFAULT):
        nr = _NR.get(platform.machine())
        if nr is None:
            raise OSError("perf_event_open: unsupported machine %s" % platform.machine())
        self._libc = ctypes.CDLL(None, use_errno=True)
        self._libc.syscall.restype = ctypes.c_long
        self.fds = {}
        for name in events:
            a = _Attr()
            a.size = ctypes.sizeof(_Attr)
            if name in HW:
                a.type, a.config = PERF_TYPE_HARDWARE, HW[name]
            elif name in HW_CACHE:
                a.type, a.config = PERF_TYPE_HW_CACHE, HW_CACHE[name]
            else:
                raise ValueError("unknown event %s" % name)
            a.read_format, a.flags = _READ_FORMAT, _FLAGS
            fd = self._libc.syscall(nr, ctypes.byref(a), 0, -1, -1, 0)   # this thread, any CPU
            if fd < 0:
                err = ctypes.get_errno()
                if name in ("cycles", "instructions"):
                    raise OSError(err, "perf_event_open(%s): %s (perf_event_paranoid=%s)"
                                  % (name, os.strerror(err), paranoid()))
                continue                          # an event this PMU lacks is just omitted
            self.fds[name] = fd

    def _ioctl(self, req):
        for fd in self.fds.values():
            self._libc.ioctl(fd, req, 0)

    def __enter__(self):
        self._ioctl(_IOC_RESET)
        self._ioctl(_IOC_ENABLE)
        return self

    def __exit__(self, *exc):
        self._ioctl(_IOC_DISABLE)
        return False

    def read(self):
        out = {}
        for name, fd in self.fds.items():
            v, en, run = struct.unpack("QQQ", os.read(fd, 24))
            out[name] = v * en / run if run and run < en else float(v)
        if out.get("cycles"):
            if "instructions" in out:
                out["ipc"] = out["instructions"] / out["cycles"]
            if "stalled_backend" in out:
                out["backend_stall_frac"] = out["stalled_backend"] / out["cycles"]
        if out.get("l1d_reads") and "l1d_read_misses" in out:
            out["l1d_miss_rate"] = out["l1d_read_misses"] / out["l1d_reads"]
        return out

    def close(self):
        for fd in self.fds.values():
            os.close(fd)
        self.fds = {}

    def __del__(self):
        try:
            self.close()
        except Exception:                          # noqa: BLE001 -- interpreter teardown
            pass


if __name__ == "__main__":
    import numpy as np
    x = np.random.standard_normal(1 << 16).astype(np.complex64)
    with Counters() as c:
        for _ in range(50):
            np.fft.fft(x)
    print("perf_event_paranoid =", paranoid())
    for k, v in c.read().items():
        print("  %-20s %.4g" % (k, v))
