"""The subgroup size Vulkan pipelines are built at: a measured choice per device.

A device with VK_EXT_subgroup_size_control can be required to run a pipeline at any size in
its range; without a requirement every pipeline runs at the size the driver reports, and the
library builds at that size. On an Intel Iris Xe (range 8-32, reports 32) the transform
kernels -- forward, refine, full correlation -- run 3.3x faster end to end at 16, exact; on
a Radeon 8060S (32-64, reports 64) no size is clearly faster. So the size is measured, once
per device and kept in MF_COST_FILE: each candidate runs a representative workload in a
SUBPROCESS (a size can make the driver lose the device -- 8 did on the Iris Xe -- and that
must not take the caller with it), its results are compared with the reported size's, and
the paired rule (_choice.paired_choice: every size runs the same calls, paired by call)
keeps the reported size unless another is
faster past the tie margin. Pipelines that choose their own size (the coarse layout,
_fit_subgroup) are unaffected.

Measured with MF_AUTOTUNE on, whether or not MF_COST_FILE is set (without one the choice
lasts the process); MF_AUTOTUNE=0 keeps the reported size. MF_VK_SUBGROUP forces a size
(with an optional role filter, see _vkcompute._build_pipeline), for measurement.
"""
import json
import os

from . import _config
import subprocess
import sys

import numpy as np

#: Samples per candidate (after warm-up), each one sample for the shared rule:
#: the mean of back-to-back calls over at least ~0.1 s -- a single call is ~1 ms on a Radeon
#: 8060S, within launch jitter and GPU idle-latency effects.
REPS = 7

_WORKLOAD = r'''
import json, os, sys, time
import numpy as np
sys.path.insert(0, sys.argv[1])
import matchedfilter as mf
dev = sys.argv[2]
reps = int(sys.argv[3])
rng = np.random.default_rng(11)
n, nt = 4096, 32
k = np.arange(n)
shape = np.where((k > 20) & (k < 1600), (np.maximum(k, 1.0) / 100.0) ** (-7.0 / 6.0), 0.0)
spec = (shape * np.exp(2j * np.pi * rng.random((nt, n)))).astype(np.complex64)
spec /= np.linalg.norm(spec, axis=1, keepdims=True) / np.sqrt(n)
ref = (shape ** 2).astype(np.float64)
L = 1 << 18
series = ((rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
for j in range(24):                       # triggers to compare: loud template-shaped signals
    t = j % nt
    w = np.fft.ifft(np.conj(spec[t])) * np.sqrt(n)
    pos = 3000 + j * (L - 2 * n) // 24
    series[pos:pos + n] += (8.0 * w / np.abs(w).max()).astype(np.complex64)
starts = np.arange(0, L - n, 3072)
ws = np.full(len(starts), 512); we = np.full(len(starts), 3584)
hf = mf.HierarchicalFilter(n, 1, nt, chain=(256, 1024), device=dev)
hf.set_reference(ref); hf.set_coarse_threshold((3.6, 4.2)); hf.set_templates(spec)
N2 = 1 << 17
cf = mf.CorrelationFilter(N2, 1, 4, device=dev)
t2 = (rng.standard_normal((4, N2)) + 1j * rng.standard_normal((4, N2))).astype(np.complex64)
cf.set_templates(t2)
cf.set_data((rng.standard_normal((1, N2)) + 1j * rng.standard_normal((1, N2))).astype(np.complex64))
def once():
    idx, val = hf.run_series(series, starts, ws, we, binsize=n, threshold=5.0, raw=True)
    out = cf.run()
    return idx, val, out
once()                                    # first call: pipeline builds, uploads
t, c = time.perf_counter(), 0
while c < 2 or time.perf_counter() - t < 0.05:  # steady-state call time
    once(); c += 1
k = max(1, int(-(-0.1 // ((time.perf_counter() - t) / c))))  # calls per sample: >= ~0.1 s
times = []
for _ in range(reps):
    t = time.perf_counter()
    for _ in range(k):
        idx, val, out = once()
    times.append((time.perf_counter() - t) / k)
m = idx >= 0
print(json.dumps({"peaks": int(m.sum()), "times": times, "idx": idx[m].tolist(), "val": np.abs(val[m]).tolist(),
                  "corr": np.abs(out[0, :, ::997]).ravel().tolist()}))
'''


def _candidates(rng):
    return [s for s in (4, 8, 16, 32, 64, 128) if rng[0] <= s <= rng[1]]


def _run(size, index, timeout=600):
    """The workload at one size, in a subprocess: dict, or None if it failed (the size is
    then not a candidate -- e.g. the device was lost)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the package's parent
    env = dict(os.environ, MF_VK_SUBGROUP=str(size), MF_AUTOTUNE="0", MF_VK_SUBGROUP_MEASURING="1")
    env.pop("MF_COST_FILE", None)            # the workload decides nothing; it only runs
    try:
        p = subprocess.run([sys.executable, "-c", _WORKLOAD, root, "gpu:%d" % index, str(REPS)],
                           env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    if p.returncode != 0:
        return None
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None


def _agree(a, b):
    """The same triggers (indices) and values to fp32 rounding."""
    if a["idx"] != b["idx"]:
        return False
    for key in ("val", "corr"):
        x, y = np.asarray(a[key]), np.asarray(b[key])
        if x.shape != y.shape:
            return False
        if y.size and not np.allclose(x, y, rtol=1e-4, atol=1e-4 * np.abs(y).max()):
            return False
    return True


def measure(index, reported, rng):
    """{size: [seconds per call, ...]} for every size that runs and reproduces the reported
    size's results; the reported size first."""
    base = _run(reported, index)
    if base is None:
        return {}
    out = {reported: base["times"]}
    for size in _candidates(rng):
        if size == reported:
            continue
        r = _run(size, index)
        if r is not None and _agree(r, base):
            out[size] = r["times"]
    return out


def choose(ctx):
    """The size this device's pipelines are built at when they do not choose their own: a
    _choice.Choice over the sizes the device can require, the reported size first (the
    preference), decided by the paired rule over the sizes' timings of the same calls (each
    size needs a device of its own, so a call cannot carry an arm: subprocesses run it), kept
    in MF_COST_FILE when there is one and for the process otherwise.
    Measured with or without a cost file (MF_AUTOTUNE=0 keeps the reported size): without
    one the Iris Xe built at its reported 32 and ran full and peak calls 5-30x slower than
    at the measured 8 (7.6 s of measuring, once per process)."""
    reported = int(ctx.subgroup_size)
    rng = getattr(ctx, "subgroup_range", None)
    if not rng or len(_candidates(rng)) < 2 or _config.get("MF_VK_SUBGROUP_MEASURING"):
        return reported
    from . import _choice, _kernel_id
    from ._choice import _autotune_enabled
    if not _autotune_enabled():
        return reported
    sizes = [reported] + [s for s in _candidates(rng) if s != reported]
    name = getattr(ctx, "device_name", "")
    ch = _choice.choice("vk-subgroup", name, sizes, label=int,
                        store_key="vk-subgroup|%s|k%s" % (name, _kernel_id.gpu_kernel_id("vulkan")),
                        what="VK-SUBGROUP %s" % name)
    if ch.winner is not None:
        return int(ch.winner)
    times = measure(getattr(ctx, "index", 0), reported, rng)
    m = min((len(v) for v in times.values()), default=0)
    w = reported
    if len(times) > 1 and m >= 2:
        w = _choice.paired_choice({s: list(v[:m]) for s, v in times.items()}, reported, m,
                                  minimum=m)[0] or reported
    ch.lock(w)
    return int(ch.winner)
