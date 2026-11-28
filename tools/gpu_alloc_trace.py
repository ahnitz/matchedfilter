#!/usr/bin/env python3
"""Trace every Vulkan device allocation a program makes, by role, and report the peak.

    python tools/gpu_alloc_trace.py OUT.json SCRIPT [ARGS...]

runs SCRIPT as ``__main__`` (a pycbc executable, tools/search_bench.py, a test) with a trace of
every device buffer the Vulkan backend allocates (``matchedfilter._vkcompute._Buffer``), and
writes OUT.json when the program exits. Per allocation it records:

- its role, read from the call stack: ``spectra slot k`` and ``starts slot k`` (a plan's series
  workspace, made by ``MatchedFilter._series_submit`` when a batch first uses slot k), ``series
  source``, ``<record>:<buffer>`` for a
  record's own buffers (``hier:cval1``, ``forward:starts``, ``followups:tab``, ...), ``inner
  rows``, ``middle workspace``, ``templates``, ``tap table``, the root's buffers, calibration
  probes, or ``other:<file>:<function>``;
- the bytes asked for and the capacity allocated (the device pool's size class);
- whether it was ever touched: bound to a kernel (a descriptor set), the target of a fill or an
  update in a recording, or written by the host through ``write()``. A host write through a
  NumPy view of a shared array is not seen; such arrays are bound when a kernel uses them.

It also samples, every 0.1 s, the live capacity, the pool's idle bytes and the GPU's GTT counter
(``/sys/class/drm/cardN/device/mem_info_gtt_used``), and at the peak of live capacity keeps the
live allocations, so the report gives the breakdown at the peak by role and how much of it was
never touched.

The trace delegates: every wrapper takes ``*args, **kwargs`` and forwards them unchanged, and it
holds no reference to a buffer, context or plan (allocations are named by their serial). An
exception Python would otherwise swallow (in ``__del__`` or a finaliser) aborts the process
with exit code 70, as does a failure of the trace's own bookkeeping: a probe that silently
stops buffers being freed can fill the GPU's memory. Vulkan only (the backend whose buffers
it wraps); the report notes when no allocation was seen.
"""
import atexit
import collections
import inspect
import json
import os
import runpy
import sys
import threading
import time
import traceback

#: Exit code of an aborted trace.
ABORT_CODE = 70

#: serial -> [role, bytes asked, capacity, time allocated, time freed, bound, filled, host-written]
INFO = {}
LIVE = set()
STATE = dict(live=0, peak=0, peak_t=0.0, snapshot_at=-1, snapshot=None)
SAMPLES = []
T0 = time.perf_counter()
#: The source lines that allocate a plan's workspace: a slot's spectra and starts
#: (MatchedFilter._series_submit) and the series source (MatchedFilter._series_call).
LINES = {}
DEVICES = []
#: A new snapshot of the live set is taken when the peak grows by this much.
SNAPSHOT_STEP = 32 << 20

ROLE_FUNCTIONS = {
    "_continuous_gpu": "middle workspace", "_continuous_gpu_parts": "middle workspace",
    "_slots": "inner rows", "_gpu_set": "templates", "_gpu_direct_arg": "tap table",
    "take_output": "root outputs", "_block": "root input blocks", "set_template": "root template",
    "peaks_items": "items outputs", "_time_coarse_layouts": "calibration probe",
    "_time_gate_ways": "calibration probe", "time_direct_ratio": "calibration probe",
    "calibrate_costs_gpu": "calibration probe", "_x_time": "calibration probe",
    "_probe_trig": "probe", "_descriptor_set": "dummy binding",
}
RECORD_KINDS = {"_hier_record": "hier", "forward": "forward", "correlate_continuous": "continuous",
                "_followup_record": "followups", "correlate": "correlate",
                "_correlate_tile": "correlate", "_flat_run": "flat"}
GENERIC = {"__init__", "_x_alloc", "empty_shared", "<lambda>", "factory", "traced_init",
           "_exec_buffer", "<listcomp>", "buf"}


def gtt_counters():
    """The GTT counter files of the machine's GPUs (cardN only, not their connectors)."""
    root = "/sys/class/drm"
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return []
    paths = (os.path.join(root, d, "device", "mem_info_gtt_used") for d in names
             if d.startswith("card") and d[4:].isdigit())
    return [p for p in paths if os.path.exists(p)]


GTT = gtt_counters()


def _abort(message):
    sys.stderr.write("gpu_alloc_trace: %s\n" % message)
    traceback.print_stack()
    sys.stderr.flush()
    os._exit(ABORT_CODE)


def _unraisable(info):
    sys.stderr.write("gpu_alloc_trace: swallowed exception in %r: %s\n"
                     % (info.object, info.exc_value))
    traceback.print_exception(info.exc_type, info.exc_value, info.exc_traceback)
    sys.stderr.flush()
    os._exit(ABORT_CODE)


def _gtt_bytes():
    total = 0
    for path in GTT:
        try:
            with open(path) as f:
                total += int(f.read())
        except (OSError, ValueError):
            pass
    return total


def _idle_bytes():
    return sum(getattr(getattr(d, "buffers", None), "idle_bytes", 0) for d in DEVICES)


def role_of(frame):
    """The role of an allocation made below `frame` (the allocating call's caller).

    Parameters
    ----------
    frame : frame
        Where to start walking up the stack.

    Returns
    -------
    str
        The role (see the module docstring).
    """
    depth = 0
    while frame is not None and depth < 40:
        code = frame.f_code
        name = code.co_name
        if name == "_exec_buffer":
            caller = frame.f_back
            kind = caller.f_code.co_name
            if kind == "<lambda>":
                kind = caller.f_back.f_code.co_name
            return "%s:%s" % (RECORD_KINDS.get(kind, kind), frame.f_locals.get("name"))
        if name == "_series_submit" and code.co_filename.endswith("_filter.py"):
            line = frame.f_lineno
            for what in ("spectra", "starts"):
                if line == LINES.get(what):
                    return "%s slot %d" % (what, frame.f_locals.get("slot", -1))
            return "series submit:%d" % line
        if name == "_series_call" and code.co_filename.endswith("_filter.py"):
            line = frame.f_lineno
            if line == LINES.get("source"):
                return "series source"
            return "series call:%d" % line
        if name in ROLE_FUNCTIONS and "matchedfilter" in code.co_filename:
            return ROLE_FUNCTIONS[name]
        if name == "run" and code.co_filename.endswith("_gpuroot.py"):
            return "root params/scratch"
        if name not in GENERIC and "matchedfilter" in code.co_filename:
            return "other:%s:%s" % (os.path.basename(code.co_filename), name)
        frame = frame.f_back
        depth += 1
    return "other:?"


def _base_serial(buf):
    owner = getattr(buf, "owner", None)
    if owner is not None:
        buf = owner.buffer
    base = getattr(buf, "base", None)
    if base is not None:
        buf = base
    return getattr(buf, "serial", None)


def _mark(buf, column):
    serial = _base_serial(buf)
    if serial is not None and serial in INFO:
        INFO[serial][column] = True


def note_allocation(serial, role, asked, capacity):
    """Record a live allocation (the bookkeeping of the traced constructor)."""
    t = time.perf_counter() - T0
    INFO[serial] = [role, int(asked), int(capacity), t, None, False, False, False]
    LIVE.add(serial)
    STATE["live"] += int(capacity)
    if STATE["live"] > STATE["peak"]:
        STATE["peak"], STATE["peak_t"] = STATE["live"], t
        if STATE["live"] > STATE["snapshot_at"] + SNAPSHOT_STEP:
            STATE["snapshot_at"] = STATE["live"]
            STATE["snapshot"] = (t, STATE["live"], sorted(LIVE))


def note_free(serial):
    """Record that a live allocation was given back."""
    if serial in LIVE:
        LIVE.discard(serial)
        INFO[serial][4] = time.perf_counter() - T0
        STATE["live"] -= INFO[serial][2]


def install():
    """Wrap the Vulkan backend's buffer constructor and destroy, its host writes, descriptor
    sets, and recordings' fills and updates, by delegation."""
    from matchedfilter import _vkcompute, _filter, _gpuhost
    source, first = inspect.getsourcelines(_filter.MatchedFilter._series_submit)
    for i, text in enumerate(source):
        if "c.spectra_pool[slot] = " in text:
            LINES["spectra"] = first + i
        elif "c.starts_pool[slot] = " in text:
            LINES["starts"] = first + i
    source, first = inspect.getsourcelines(_filter.MatchedFilter._series_call)
    for i, text in enumerate(source):
        if "src = sources[slot0] =" in text:
            LINES["source"] = first + i
    if len(LINES) != 3:
        _abort("could not find the workspace lines of _series_submit and _series_call: %r"
               % LINES)

    buffer_type = _vkcompute._Buffer
    init, destroy, write = buffer_type.__init__, buffer_type.destroy, buffer_type.write

    def traced_init(self, *args, **kwargs):
        init(self, *args, **kwargs)
        try:
            if not any(d is self.dev for d in DEVICES):
                DEVICES.append(self.dev)
            note_allocation(self.serial, role_of(sys._getframe(1)), self.nbytes, self.capacity)
        except Exception as e:
            _abort("bookkeeping failed in __init__: %r" % (e,))

    def traced_destroy(self, *args, **kwargs):
        serial = getattr(self, "serial", None)
        live = bool(getattr(self, "handle", None))
        out = destroy(self, *args, **kwargs)
        try:
            if live:
                note_free(serial)
        except Exception as e:
            _abort("bookkeeping failed in destroy: %r" % (e,))
        return out

    def traced_write(self, *args, **kwargs):
        _mark(self, 7)
        return write(self, *args, **kwargs)

    buffer_type.__init__, buffer_type.destroy = traced_init, traced_destroy
    buffer_type.write = traced_write

    section_write = _gpuhost.Section.write

    def traced_section_write(self, *args, **kwargs):
        _mark(self, 7)
        return section_write(self, *args, **kwargs)
    _gpuhost.Section.write = traced_section_write

    descriptor_set = _vkcompute.Context._descriptor_set

    def traced_descriptor_set(self, *args, **kwargs):
        for buf in (args[1] if len(args) > 1 else kwargs.get("bufs", ())):
            _mark(buf, 5)
        return descriptor_set(self, *args, **kwargs)
    _vkcompute.Context._descriptor_set = traced_descriptor_set

    resolve = _vkcompute._VkNative._resolve

    def traced_resolve(self, *args, **kwargs):
        binds = args[0] if args else kwargs.get("binds", {})
        for op in self.commands.decode():
            if op[0] in ("fill", "update"):
                buf = op[1]
                if hasattr(buf, "name") and not hasattr(buf, "handle"):
                    buf = (binds or {}).get(buf.name, buf)
                _mark(buf, 6)
        return resolve(self, *args, **kwargs)
    _vkcompute._VkNative._resolve = traced_resolve

    def sample():
        while True:
            SAMPLES.append((round(time.perf_counter() - T0, 3), STATE["live"], _idle_bytes(),
                            _gtt_bytes()))
            time.sleep(0.1)
    threading.Thread(target=sample, daemon=True).start()


def summary():
    """The report: allocations, the peak of live capacity, the breakdown at the peak by role
    (count, bytes, bytes never touched), every role over the whole run, and the samples.

    Returns
    -------
    dict
        The report, as written to OUT.json.
    """
    roles = collections.defaultdict(lambda: dict(count=0, bytes=0, touched=0, bound=0,
                                                 host=0, untouched_bytes=0))
    for role, asked, capacity, _, _, bound, filled, host in INFO.values():
        r = roles[role]
        r["count"] += 1
        r["bytes"] += capacity
        touched = bound or filled or host
        r["touched"] += touched
        r["bound"] += bound
        r["host"] += host
        if not touched:
            r["untouched_bytes"] += capacity
    peak = None
    if STATE["snapshot"] is not None:
        t, live, serials = STATE["snapshot"]
        at_peak = collections.defaultdict(lambda: dict(count=0, bytes=0, untouched=0))
        for serial in serials:
            role, _, capacity, _, _, bound, filled, host = INFO[serial]
            r = at_peak[role]
            r["count"] += 1
            r["bytes"] += capacity
            if not (bound or filled or host):
                r["untouched"] += capacity
        peak = dict(t=t, live_bytes=live,
                    untouched_bytes=sum(r["untouched"] for r in at_peak.values()),
                    roles=dict(sorted(at_peak.items(), key=lambda kv: -kv[1]["bytes"])))
    return dict(allocations=len(INFO), peak_live_bytes=STATE["peak"],
                peak_live_t=STATE["peak_t"], peak=peak,
                roles=dict(sorted(roles.items(), key=lambda kv: -kv[1]["bytes"])),
                gtt_peak_sample=max(SAMPLES, key=lambda s: s[3]) if SAMPLES else None,
                samples=SAMPLES[::5], workspace_lines=LINES)


def _write(path):
    data = summary()
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
    sys.stderr.write("gpu_alloc_trace: %d allocations, peak live %.0f MB, %.0f MB of it never "
                     "touched; written to %s\n"
                     % (data["allocations"], data["peak_live_bytes"] / 2**20,
                        (data["peak"] or {}).get("untouched_bytes", 0) / 2**20, path))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        sys.stderr.write(__doc__)
        return 2
    out, script = os.path.abspath(argv[0]), argv[1]
    sys.unraisablehook = _unraisable
    sys.argv = argv[1:]
    sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
    install()
    atexit.register(_write, out)
    runpy.run_path(script, run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main())
