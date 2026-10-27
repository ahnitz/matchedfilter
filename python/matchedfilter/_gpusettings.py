"""The GPU settings a batch runs with, and the kernel slots its calls consult.

The device trials (time_domain._gpu_batch) decide batch-wide GPU settings and kernels' slots
on real batches; the GPU host layer and the backends read what is in force here (gpu_setting,
kernel_slot), below the workloads that run the trials.
"""

#: The device trial's dimensions (time_domain._gpu_batch): every batch-wide GPU setting a batch of GPU
#: banks runs with, at its default. fuse: the batch's submissions fused into shared command
#: buffers (_gpuexec.fused: every job's phases interleaved, one barrier per phase) -- +16% on
#: an M2, -3 to -6% on an 8060S, nothing on a RENOIR (paired ladders, 2026-10-19).
#: single: where a batch's single-template (follow-up) jobs run, batched on the device or each
#: on a CPU plan. interleave: a fused Vulkan batch's interleave depth, 0 lockstep or 3, the
#: second half's forward (DRAM-bound) beside the first half's coarse0 (VALU-bound).
_GPU_DEFAULT = dict(fuse=True, single="gpu", interleave=0)
#: The settings in force while a batch runs (time_domain._gpu_batch); empty between batches.
_GPU_ARM = {}
#: Each device set's locked settings, for calls outside a batch (gpu_setting).
_GPU_LOCKS = {}


def _gpu_arm(label) -> dict:
    """The settings an arm of the device trial runs: DEFAULT, or one dimension moved
    ("fuse=0", "single=cpu", "interleave=3", or a kernel slot's alternative,
    "kern:coarse:256=<layout label>": kernel_slot)."""
    out = dict(_GPU_DEFAULT)
    if label != "default":
        k, _, v = str(label).partition("=")
        if k.startswith("kern:"):
            _, what, band = k.split(":")
            out["kernels"] = {(what, band): v}
            return out
        if k not in out:
            raise ValueError("not a device-trial arm: %r" % (label,))
        out[k] = (v == "1") if k == "fuse" else (int(v) if k == "interleave" else v)
    return out


#: Kernel slots per GPU device name: every decision a call's kernels take that the device
#: trial "gpu-kernels" plays on batches -- (what, band) -> (default, alternative) labels:
#: the fp16 coarse layout of tier 0 and the gate way of a later tier at a band (offline
#: screens' fastest and runner-up, _gpuhier._kernel_shortlist), and how sparse results are
#: read ("sparse", "hier" / "flat"). Registered by the calls that consult them (kernel_slot).
_KERNEL_SLOTS = {}
#: (device, slot) consulted since the running batch began (time_domain._gpu_batch keeps them
#: per batch composition: an arm counts as running a batch differently only where its slot
#: was used the last time that batch ran -- a batch's banks recur).
_KERNEL_SEEN = set()


def kernel_slot(device, what, band, default, alternative):
    """A call consults kernel slot (what, band) on device (its name) with these two labels;
    returns the label to run: the running batch's arm, else the device trial's lock, else the
    default."""
    slot = (str(what), str(band))
    _KERNEL_SLOTS.setdefault(device, {})[slot] = (default, alternative)
    _KERNEL_SEEN.add((device, slot))
    over = _GPU_ARM.get("kernels", {})
    if slot in over:
        return over[slot]
    for devs, arm in _GPU_LOCKS.items():
        if any(d.endswith(" " + device) for d in devs) and slot in arm.get("kernels", {}):
            return arm["kernels"][slot]
    return default


def gpu_setting(name, device=None):
    """A batch-wide GPU setting (_GPU_DEFAULT) now: the running batch's arm, else the locked
    choice of a device set holding `device`, else the default."""
    if name in _GPU_ARM:
        return _GPU_ARM[name]
    for devs, arm in _GPU_LOCKS.items():
        if name in arm and (device is None or any(d.startswith(str(device) + " ") for d in devs)):
            return arm[name]
    return _GPU_DEFAULT[name]


def fingerprint():
    """The settings in force, as a key: a recorded call plan is kept per configuration, so the
    arms a device trial plays do not overwrite one another's (and the default's) plans."""
    return (tuple(sorted((k, v) for k, v in _GPU_ARM.items() if k != "kernels")),
            tuple(sorted(_GPU_ARM.get("kernels", {}).items())))
