"""Dispatching the embedded SPIR-V through Vulkan, with ctypes.

No slangpy, no Vulkan SDK, no compiled host code: the loader is whatever the
user's system provides, and everything above it is the twenty-odd entry points
a compute-only workload needs.  That keeps the wheel self-contained -- it
carries kernels, not a toolchain -- and keeps the GPU path out of the way of
callers who only ever use the CPU.

Scope is deliberately compute-only.  No swapchain, no images, no graphics
pipeline, one queue, one descriptor set.
"""
import ctypes
import itertools
import os
from collections import OrderedDict
import pathlib
import sys

import numpy as np

from . import _gputime, _vulkan
from ._shared import empty_shared, shared_buffer, shared_key, shared_view, write_input

_SPIRV = pathlib.Path(__file__).resolve().parent / "spirv"

_MANIFEST = None


def _manifest():
    global _MANIFEST
    if _MANIFEST is None:
        try:
            import json
            _MANIFEST = json.loads((_SPIRV / "manifest.json").read_text())
        except Exception:
            _MANIFEST = {}
    return _MANIFEST

#: The per-bin table aliases the 8 KB exchange staging: CAP=1024 complex =
#: 2048 uints. Past that the kernel needs its own array and the LDS cost
#: halves occupancy, so this refuses rather than silently getting slower.
_MAX_BINS = 2048

#: Must match COARSE_TILE_T in tools/build_spirv.py -- the kernel is
#: compiled with the tile baked in, so the dispatch has to agree.
_COARSE_TILE_T = {128: 2, 256: 2, 512: 4, 1024: 2}


def _use_c16(band):
    """Half-width coarse path, only where filling a wave pays for it.

    WG = band/16, so a band under 512 gives a workgroup SMALLER than one
    wave32 and packing PPG = 512/band pairs into it fills the idle lanes.
    Measured at band 128 (WG 8, PPG 4): 1.911 -> 0.865 ms, 2.2x.

    At band 512 the workgroup is already a full wave and there is nothing
    to fill, so the half2 conversions in the stage are pure added cost --
    2.239 -> 2.615 ms, 17% SLOWER, and band 1024 11% slower. Those are
    means of three runs; single runs on this part vary by ~15% at band 128
    and ~7% at 512, which is wide enough that one measurement either way
    would have supported the wrong answer.
    """
    return True   # one-bin specialised coarse kernel; applies at every band


def _pack_half2(a):
    """complex64 -> one uint32 per value, real in the low half.

    The coarse stage is bandwidth bound -- 978 GB/s at 3.19 FLOP/byte -- so
    its two big inputs ship at half width. Packed into uint32 rather than a
    half2 buffer so no 16-bit storage extension is needed.

    Done ONCE on upload: every row is reused across the whole N x M pair
    grid, so the conversion amortises to nothing.

    Coarse only. The refine stage reads the full-precision data/tmpl
    buffers, which is why survivors still get an exact peak.
    """
    a = np.ascontiguousarray(a, np.complex64)
    if np.little_endian:
        # Complex storage is already [real, imag]. Convert the interleaved
        # components in one pass rather than allocating widened integers,
        # shifting, and ORing two separately converted arrays.
        return a.view(np.float32).astype(np.float16).view(np.uint32)
    re = a.real.astype(np.float16).view(np.uint16).astype(np.uint32)
    im = a.imag.astype(np.float16).view(np.uint16).astype(np.uint32)
    return np.ascontiguousarray(re | (im << 16), np.uint32)

#: Byte offsets into VkPhysicalDeviceProperties. The 5 leading uint32s, the
#: 256-byte name and the 16-byte UUID come to 292, padded to 296 because
#: VkPhysicalDeviceLimits contains 64-bit members; maxComputeSharedMemorySize
#: sits 216 bytes into those limits.
_OFF_SHARED_MEMORY = 296 + 216
_OFF_MAX_INVOCATIONS = 296 + 232
#: timestampPeriod (float, ns per tick) sits 424 bytes into the limits.
_OFF_TIMESTAMP_PERIOD = 296 + 424

#: Bands that USE the tiled coarse kernel. It is built and validated for
#: 512 and 1024 as well, and deliberately not selected there.
#:
#: Tiling pays at 256 and only at 256, because the untiled workgroup is
#: BAND/16 threads and 16 is HALF A WAVE -- the other half idles. At 512
#: that is a full wave and at 1024 two, so there is no waste to recover,
#: while the tile's shared memory grows to 16 and 32 KB against 4 and costs
#: occupancy. Measured, hierarchical call, untiled against tiled:
#:
#:     n=8192  band 512   0.761 -> 0.730 ms   1.04x
#:     n=8192  band 512   0.417 -> 0.539 ms   0.77x
#:     n=16384 band 1024  0.973 -> 1.008 ms   0.97x
#:     n=16384 band 512   2.007 -> 1.664 ms   1.21x
#:
#: Noise around one. The 1.8x the tile buys at 256 does not generalise, and
#: assuming it did is what prompted the measurement.
#:
#: The tile must match the TILE the kernel was compiled with, or the
#: dispatch covers the wrong number of pairs.
#: EMPTY. This selected a separate fp32 tiled coarse kernel (coarse_N.spv)
#: that predates the fp16 work, and band 256 was still routed to it -- so
#: the band the teaser autotunes to ran with ZERO fp16 instructions while
#: every other band had been converted. Disassembly found it: 4125
#: instructions, 1351 fp32, no v_pk_* at all.
#:
#: On the converted kernel band 256 goes 1.109 -> 0.868 ms. Kept as an
#: empty dict rather than deleted so the selection point stays visible.
_COARSE_TILE = {}

# --- enough of the Vulkan enums to dispatch -------------------------------
_QUEUE_COMPUTE = 0x2
_BUF_STORAGE = 0x20
_BUF_INDIRECT = 0x100   # an indirect dispatch reads its group count from a buffer
_BUF_TRANSFER_DST = 0x2
_MEM_DEVICE_LOCAL, _MEM_HOST_VISIBLE, _MEM_HOST_COHERENT = 0x1, 0x2, 0x4
#: HOST_CACHED. The CPU reads the two output buffers and nothing else,
#: and reading uncached device-visible memory runs at about 240 MB/s --
#: measured, and enough to cost more than the kernel.
_MEM_HOST_CACHED = 0x8
_DESC_STORAGE_BUFFER = 7
_STAGE_COMPUTE = 0x20
_BIND_POINT_COMPUTE = 1
_ONE_TIME_SUBMIT = 0x1
_STAGE_COMPUTE_BIT = 0x800
_STAGE_DRAW_INDIRECT_BIT, _STAGE_TRANSFER_BIT, _STAGE_HOST_BIT = 0x2, 0x1000, 0x4000
_ACCESS_SHADER_READ, _ACCESS_SHADER_WRITE = 0x20, 0x40
_ACCESS_INDIRECT_READ, _ACCESS_TRANSFER_WRITE, _ACCESS_HOST_READ = 0x1, 0x1000, 0x2000
_WHOLE_SIZE = 0xFFFFFFFFFFFFFFFF

_u32, _u64, _vp = ctypes.c_uint32, ctypes.c_uint64, ctypes.c_void_p

#: data, tmpl, peakIdx, peakVal -- confirmed against spirv/manifest.json,
#: generated by reflecting the compiled module, not by reading the source.
_NBIND = 4

#: ntmpl, winStart, winEnd, binsize, binShift, nbins, thrBits
_PUSH_BYTES = 28


def _struct(name, *fields):
    return type(name, (ctypes.Structure,), {"_fields_": list(fields)})


_QueueCreate = _struct("VkDeviceQueueCreateInfo",
                       ("sType", _u32), ("pNext", _vp), ("flags", _u32),
                       ("queueFamilyIndex", _u32), ("queueCount", _u32),
                       ("pQueuePriorities", ctypes.POINTER(ctypes.c_float)))
_DeviceCreate = _struct("VkDeviceCreateInfo",
                        ("sType", _u32), ("pNext", _vp), ("flags", _u32),
                        ("queueCreateInfoCount", _u32),
                        ("pQueueCreateInfos", ctypes.POINTER(_QueueCreate)),
                        ("enabledLayerCount", _u32), ("ppEnabledLayerNames", _vp),
                        ("enabledExtensionCount", _u32), ("ppEnabledExtensionNames", _vp),
                        ("pEnabledFeatures", _vp))
_BufferCreate = _struct("VkBufferCreateInfo",
                        ("sType", _u32), ("pNext", _vp), ("flags", _u32),
                        ("size", _u64), ("usage", _u32), ("sharingMode", _u32),
                        ("queueFamilyIndexCount", _u32), ("pQueueFamilyIndices", _vp))
_MemAlloc = _struct("VkMemoryAllocateInfo",
                    ("sType", _u32), ("pNext", _vp),
                    ("allocationSize", _u64), ("memoryTypeIndex", _u32))
_MemReq = _struct("VkMemoryRequirements",
                  ("size", _u64), ("alignment", _u64), ("memoryTypeBits", _u32))
_MemType = _struct("VkMemoryType", ("propertyFlags", _u32), ("heapIndex", _u32))
_MemHeap = _struct("VkMemoryHeap", ("size", _u64), ("flags", _u32))
_MemProps = _struct("VkPhysicalDeviceMemoryProperties",
                    ("memoryTypeCount", _u32), ("memoryTypes", _MemType * 32),
                    ("memoryHeapCount", _u32), ("memoryHeaps", _MemHeap * 16))
_QueueFamily = _struct("VkQueueFamilyProperties",
                       ("queueFlags", _u32), ("queueCount", _u32),
                       ("timestampValidBits", _u32),
                       ("minImageTransferGranularity", _u32 * 3))
_ShaderModule = _struct("VkShaderModuleCreateInfo",
                        ("sType", _u32), ("pNext", _vp), ("flags", _u32),
                        ("codeSize", ctypes.c_size_t), ("pCode", _vp))
_LayoutBinding = _struct("VkDescriptorSetLayoutBinding",
                         ("binding", _u32), ("descriptorType", _u32),
                         ("descriptorCount", _u32), ("stageFlags", _u32),
                         ("pImmutableSamplers", _vp))
_SetLayoutCreate = _struct("VkDescriptorSetLayoutCreateInfo",
                           ("sType", _u32), ("pNext", _vp), ("flags", _u32),
                           ("bindingCount", _u32),
                           ("pBindings", ctypes.POINTER(_LayoutBinding)))
_PushRange = _struct("VkPushConstantRange",
                     ("stageFlags", _u32), ("offset", _u32), ("size", _u32))
_PipelineLayoutCreate = _struct("VkPipelineLayoutCreateInfo",
                                ("sType", _u32), ("pNext", _vp), ("flags", _u32),
                                ("setLayoutCount", _u32), ("pSetLayouts", _vp),
                                ("pushConstantRangeCount", _u32),
                                ("pPushConstantRanges", ctypes.POINTER(_PushRange)))
_StageCreate = _struct("VkPipelineShaderStageCreateInfo",
                       ("sType", _u32), ("pNext", _vp), ("flags", _u32),
                       ("stage", _u32), ("module", _vp),
                       ("pName", ctypes.c_char_p), ("pSpecializationInfo", _vp))
_SpecializationEntry = _struct("VkSpecializationMapEntry",
                              ("constantID", _u32), ("offset", _u32),
                              ("size", ctypes.c_size_t))
_SpecializationInfo = _struct("VkSpecializationInfo",
                             ("mapEntryCount", _u32),
                             ("pMapEntries", ctypes.POINTER(_SpecializationEntry)),
                             ("dataSize", ctypes.c_size_t), ("pData", _vp))
_SubgroupProperties = _struct("VkPhysicalDeviceSubgroupProperties",
                             ("sType", _u32), ("pNext", _vp),
                             ("subgroupSize", _u32),
                             ("supportedStages", _u32),
                             ("supportedOperations", _u32),
                             ("quadOperationsInAllStages", _u32))
_PhysicalDeviceProperties2 = _struct("VkPhysicalDeviceProperties2",
                                    ("sType", _u32), ("pNext", _vp),
                                    ("properties", ctypes.c_ubyte * 2048))
_ComputePipelineCreate = _struct("VkComputePipelineCreateInfo",
                                 ("sType", _u32), ("pNext", _vp), ("flags", _u32),
                                 ("stage", _StageCreate), ("layout", _vp),
                                 ("basePipelineHandle", _vp),
                                 ("basePipelineIndex", ctypes.c_int32))
_PoolSize = _struct("VkDescriptorPoolSize", ("type", _u32), ("descriptorCount", _u32))
_DescPoolCreate = _struct("VkDescriptorPoolCreateInfo",
                          ("sType", _u32), ("pNext", _vp), ("flags", _u32),
                          ("maxSets", _u32), ("poolSizeCount", _u32),
                          ("pPoolSizes", ctypes.POINTER(_PoolSize)))
_DescSetAlloc = _struct("VkDescriptorSetAllocateInfo",
                        ("sType", _u32), ("pNext", _vp), ("descriptorPool", _vp),
                        ("descriptorSetCount", _u32), ("pSetLayouts", _vp))
_DescBufferInfo = _struct("VkDescriptorBufferInfo",
                          ("buffer", _vp), ("offset", _u64), ("range", _u64))
_WriteDescSet = _struct("VkWriteDescriptorSet",
                        ("sType", _u32), ("pNext", _vp), ("dstSet", _vp),
                        ("dstBinding", _u32), ("dstArrayElement", _u32),
                        ("descriptorCount", _u32), ("descriptorType", _u32),
                        ("pImageInfo", _vp),
                        ("pBufferInfo", ctypes.POINTER(_DescBufferInfo)),
                        ("pTexelBufferView", _vp))
_CmdPoolCreate = _struct("VkCommandPoolCreateInfo",
                         ("sType", _u32), ("pNext", _vp), ("flags", _u32),
                         ("queueFamilyIndex", _u32))
_CmdBufAlloc = _struct("VkCommandBufferAllocateInfo",
                       ("sType", _u32), ("pNext", _vp), ("commandPool", _vp),
                       ("level", _u32), ("commandBufferCount", _u32))
_CmdBufBegin = _struct("VkCommandBufferBeginInfo",
                       ("sType", _u32), ("pNext", _vp), ("flags", _u32),
                       ("pInheritanceInfo", _vp))
_QueryPoolCreate = _struct("VkQueryPoolCreateInfo",
                           ("sType", ctypes.c_int), ("pNext", _vp), ("flags", _u32),
                           ("queryType", ctypes.c_int), ("queryCount", _u32),
                           ("pipelineStatistics", _u32))
_SubmitInfo = _struct("VkSubmitInfo",
                      ("sType", _u32), ("pNext", _vp),
                      ("waitSemaphoreCount", _u32), ("pWaitSemaphores", _vp),
                      ("pWaitDstStageMask", _vp),
                      ("commandBufferCount", _u32),
                      ("pCommandBuffers", ctypes.POINTER(_vp)),
                      ("signalSemaphoreCount", _u32), ("pSignalSemaphores", _vp))
_FenceCreate = _struct("VkFenceCreateInfo",
                       ("sType", _u32), ("pNext", _vp), ("flags", _u32))


_MemBarrier = _struct("VkMemoryBarrier",
                      ("sType", _u32), ("pNext", _vp),
                      ("srcAccessMask", _u32), ("dstAccessMask", _u32))

_QUEUE_FAMILY_IGNORED = 0xFFFFFFFF
_BufMemBarrier = _struct("VkBufferMemoryBarrier",
                         ("sType", _u32), ("pNext", _vp),
                         ("srcAccessMask", _u32), ("dstAccessMask", _u32),
                         ("srcQueueFamilyIndex", _u32), ("dstQueueFamilyIndex", _u32),
                         ("buffer", _vp), ("offset", _u64), ("size", _u64))


from ._errors import UnsupportedSize      # noqa: F401  (re-export)
from ._gpu_cache import InputUploads


class VulkanError(RuntimeError):
    pass


def _check(rc, what):
    if rc != 0:
        raise VulkanError("%s failed with VkResult %d" % (what, rc))


def _sparse_from_dense(idx, val):
    from . import _SparsePeaks
    flat = np.flatnonzero(idx >= 0)
    return _SparsePeaks(idx.shape, flat, idx.reshape(-1)[flat], val.reshape(-1)[flat])


def _sparsified(res, sparse):
    """A dense (idx, val) result -- or a readback giving one -- as a _SparsePeaks."""
    if not sparse:
        return res
    if callable(res):
        return lambda: _sparse_from_dense(*res())
    return _sparse_from_dense(*res)


#: An indirect dispatch's initial (x, y, z) = (0, 1, 1): x counts survivors. One
#: vkCmdUpdateBuffer per counter instead of two fills; small transfer commands cost ~2 us
#: each on the device, and a segment records hundreds. Module-level because fused batches
#: re-record captured calls later, and the command reads its data at record time.
_ARGS_INIT = (ctypes.c_uint32 * 3)(0, 1, 1)


def _reset_args(vk, cmd, buf):
    vk.vkCmdUpdateBuffer(cmd, buf.handle, 0, 12, ctypes.addressof(_ARGS_INIT))


class _Buffer:
    """A storage buffer plus its memory, mapped for the lifetime of the object.

    Host-visible throughout, with DEVICE_LOCAL preferred when the driver
    offers it.  On an integrated GPU that combination is the whole of memory,
    so this is not a compromise; on a discrete card it is, and a staging copy
    will be needed there -- deliberately not written until there is a discrete
    card to measure it on, because an unmeasured transfer path is exactly the
    kind of code that looks right and halves throughput.
    """

    # TRANSFER_DST: any buffer may be cleared on the device (zero_columns, output fills).
    def __init__(self, ctx, nbytes, readback=False, usage=_BUF_STORAGE | _BUF_TRANSFER_DST):
        self.ctx, self.nbytes = ctx, max(int(nbytes), 4)
        vk = ctx.vk
        info = _BufferCreate(12, None, 0, self.nbytes, usage, 0, 0, None)
        self.handle = _vp()
        _check(vk.vkCreateBuffer(ctx.device, ctypes.byref(info), None,
                                 ctypes.byref(self.handle)), "vkCreateBuffer")
        req = _MemReq()
        vk.vkGetBufferMemoryRequirements(ctx.device, self.handle, ctypes.byref(req))
        alloc = _MemAlloc(5, None, req.size, ctx.memory_type(req.memoryTypeBits, readback))
        self.memory = _vp()
        _check(vk.vkAllocateMemory(ctx.device, ctypes.byref(alloc), None,
                                   ctypes.byref(self.memory)), "vkAllocateMemory")
        _check(vk.vkBindBufferMemory(ctx.device, self.handle, self.memory, 0),
               "vkBindBufferMemory")
        self.ptr = _vp()
        _check(vk.vkMapMemory(ctx.device, self.memory, 0, _WHOLE_SIZE, 0,
                              ctypes.byref(self.ptr)), "vkMapMemory")

    def write(self, array):
        flat = np.ascontiguousarray(array)
        ctypes.memmove(self.ptr, flat.ctypes.data, flat.nbytes)

    def read(self, dtype, count):
        out = np.empty(count, dtype=dtype)
        ctypes.memmove(out.ctypes.data, self.ptr, out.nbytes)
        return out

    def view(self, dtype, count):
        """The first count elements, in place (valid while the buffer lives)."""
        dtype = np.dtype(dtype)
        return np.frombuffer((ctypes.c_char * (count * dtype.itemsize)).from_address(
            int(self.ptr.value if hasattr(self.ptr, 'value') else self.ptr)), dtype, count)

    def read_into(self, out):
        """Zero-copy direct read into caller-provided contiguous array."""
        ctypes.memmove(out.ctypes.data, self.ptr, min(self.nbytes, out.nbytes))
        return out

    def destroy(self):
        vk, dev = self.ctx.vk, self.ctx.device
        if self.handle:
            vk.vkUnmapMemory(dev, self.memory)
            vk.vkDestroyBuffer(dev, self.handle, None)
            vk.vkFreeMemory(dev, self.memory, None)
            self.handle = None


class _CaptureVK:
    """The Vulkan function table, also logging vkCmd* calls (name, args) into a capture."""

    def __init__(self, real, cap):
        self._real, self._cap = real, cap

    def __getattr__(self, name):
        fn = getattr(self._real, name)
        if not name.startswith("vkCmd"):
            return fn
        cap = self._cap

        def call(*args):
            cap["ops"].append((name, args))
            return fn(*args)
        return call


#: Phases of forward and hierarchical recordings, in execution order. A fused batch runs
#: every recording's work for a phase, then their barriers, then the next phase: the
#: dispatches of a phase are independent across recordings and overlap on the device.
_FUSED_PHASES = ("forward", "fill", "pack", "coarse0", "compact0", "coarse1", "compact1", "refine")

#: A unique number per captured recording. Fused recordings are cached by their constituents,
#: and a command-buffer handle is no identity: once a recording is evicted the driver hands
#: the same handle value to a new one, and a cache keyed on handles resubmitted a fused buffer
#: whose commands still named the evicted recording's freed descriptor sets and buffers -- a
#: GPU write to freed pages (amdgpu page fault, VK_ERROR_DEVICE_LOST) in about a third of
#: ladder runs.
_RECORDING_SERIAL = itertools.count(1)


def _fused_key(items):
    """Cache key of a fused batch: per context, its recordings' serials (see above)."""
    return tuple((id(ctx), tuple(ctx._phases[h]["_serial"] for h in cmds)) for ctx, cmds in items)


def _fused_valid(ctx, cmds, serials):
    """Every recording of cmds is still the one the serials name."""
    phases = getattr(ctx, "_phases", {})
    return (ctx is not None and ctx.device is not None and len(cmds) == len(serials)
            and all(phases.get(h, {}).get("_serial") == k for h, k in zip(cmds, serials)))


class _FusedBatch:
    """Submissions collected across contexts on one device, recorded and submitted together."""

    def __init__(self, dev):
        self.dev, self.items, self.state = dev, [], "open"

    #: Submissions per fused command buffer. The device starts on a chunk while the host
    #: prepares the next: fusing a whole segment into one buffer left the GPU idle through
    #: all the host's preparation. MF_GPU_FUSE_CHUNK overrides.
    chunk = int(os.environ.get("MF_GPU_FUSE_CHUNK", "16"))

    def add(self, ctx, commands, fence):
        self.items.append((ctx, [getattr(c, "value", c) for c in commands]))
        ctx.__dict__.setdefault("_collected", {})[getattr(fence, "value", fence)] = self
        if len(self.items) >= self.chunk and self.dev.collector is self:
            nxt = _FusedBatch(self.dev)
            self.dev.collector = nxt
            self.flush()
            self.dev.collector = nxt

    def flush(self):
        if self.state != "open":
            return
        self.state = "submitted"
        if self.dev.collector is self:
            # Flushed early (a wait mid-batch: a slot settled, an eviction drained): keep
            # collecting the rest of the batch into a fresh one rather than stop fusing.
            self.dev.collector = _FusedBatch(self.dev)
        dev, vk = self.dev, self.dev.vk
        # The same jobs recur every segment: reuse their fused recording while every
        # constituent recording is still cached (eviction drops its phases).
        key = _fused_key(self.items)
        cache = dev.__dict__.setdefault("fused_cache", OrderedDict())
        hit = cache.get(key)
        if dev.trace is not None:
            dev.trace.append(key)
        if hit is not None:
            # Serials are never reused, so a hit IS these recordings; they are live (add()
            # accepts only registered recordings, and eviction flushes the batch first).
            cache.move_to_end(key)
            self._submit_fused(hit[0])
            return
        if hit is not None:
            cache.pop(key)
            self._free(hit[0])
        cmd = _vp()
        info = _CmdBufAlloc(40, None, dev.command_pool, 0, 1)
        _check(vk.vkAllocateCommandBuffers(dev.device, ctypes.byref(info), ctypes.byref(cmd)),
               "allocate fused")
        _check(vk.vkBeginCommandBuffer(cmd, ctypes.byref(_CmdBufBegin(42, None, 0, None))),
               "begin fused")
        prof = next((ctx for ctx, _ in self.items if getattr(ctx, "_profile", False)), None)
        if prof is not None:
            prof._stamp(cmd, "start")
        for phase in _FUSED_PHASES:
            barriers = []
            for ctx, cmds in self.items:
                for h in cmds:
                    work_bar = ctx._phases[h].get(phase)
                    if work_bar is None:
                        continue
                    work, bar = work_bar
                    for name, args in work:
                        getattr(vk, name)(cmd, *args[1:])
                    barriers.extend(bar)
            # One global barrier per distinct (stages, access) is enough for the whole phase;
            # buffer barriers are kept as recorded.
            seen = set()
            for name, args in barriers:
                if args[4] == 1 and args[6] == 0:
                    mb = getattr(args[5], "_obj", None)
                    sig = (args[1], args[2], getattr(mb, "srcAccessMask", id(mb)),
                           getattr(mb, "dstAccessMask", id(mb)))
                    if sig in seen:
                        continue
                    seen.add(sig)
                getattr(vk, name)(cmd, *args[1:])
            if prof is not None:
                prof._stamp(cmd, "fused " + phase)
        _check(vk.vkEndCommandBuffer(cmd), "end fused")
        self.prof = prof
        cache[key] = (cmd, [list(cmds) for _, cmds in self.items])
        while len(cache) > int(os.environ.get("MF_GPU_FUSE_CACHE", "64")):
            _, (old_cmd, _) = cache.popitem(last=False)
            self._free(old_cmd)
        self._submit_fused(cmd)

    def _free(self, cmd):
        vk = self.dev.vk
        vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
        vk.vkFreeCommandBuffers(self.dev.device, self.dev.command_pool, 1, (_vp * 1)(cmd))

    def _submit_fused(self, cmd):
        dev, vk = self.dev, self.dev.vk
        prof = next((ctx for ctx, _ in self.items if getattr(ctx, "_profile", False)), None)
        if prof is not None:
            prof._profile_submitted([cmd])
        fc = _FenceCreate(8, None, 0)
        self.fence = _vp()
        _check(vk.vkCreateFence(dev.device, ctypes.byref(fc), None, ctypes.byref(self.fence)),
               "vkCreateFence")
        self.cmd = cmd
        timed = next((ctx for ctx, _ in self.items if ctx._timing), None)
        if timed is not None:
            begin, end = timed._timestamp_pair("fused")
            cmds = (_vp * 3)(begin, cmd, end)
            submit = _SubmitInfo(4, None, 0, None, None, 3, cmds, 0, None)
        else:
            cmds = (_vp * 1)(cmd)
            submit = _SubmitInfo(4, None, 0, None, None, 1, cmds, 0, None)
        _check(vk.vkQueueSubmit(dev.queue, 1, ctypes.byref(submit), self.fence), "vkQueueSubmit")

    def wait(self):
        if self.state == "open":
            self.flush()
        if self.state != "submitted":
            return
        self.state = "done"
        dev, vk = self.dev, self.dev.vk
        fences = (_vp * 1)(self.fence)
        _check(vk.vkWaitForFences(dev.device, 1, fences, 1, 0xFFFFFFFFFFFFFFFF), "vkWaitForFences")
        vk.vkDestroyFence(dev.device, self.fence, None)


def fused():
    """Begin a fused batch on every Vulkan device in use; returns a callable that closes it
    (any collected work is submitted when first waited on, or at close)."""
    devs = []
    for dev in _DEVICES.values():
        if dev.collector is None:
            dev.collector = _FusedBatch(dev)
            devs.append(dev)

    def close():
        for dev in devs:
            b, dev.collector = dev.collector, None
            if b is not None and b.items:
                b.flush()
    return close


def replay_fused(dev, keys):
    """Submit cached fused recordings again, in order, as one submission, and wait; False
    (nothing submitted) if any is gone or a constituent recording was evicted."""
    cache = dev.__dict__.get("fused_cache", {})
    cmds = []
    for key in keys:
        hit = cache.get(key)
        if hit is None:
            if os.environ.get("MF_REPLAY_DEBUG"):
                print("replay invalid: fused key not cached", flush=True)
            return False
        # Every constituent recording must still exist: eviction frees its descriptor sets
        # and buffers, and replaying a recording built on them faults the device.
        for (ctx_id, serials), cmds in zip(key, hit[1]):
            if not _fused_valid(_CONTEXTS_BY_ID.get(ctx_id), cmds, serials):
                if os.environ.get("MF_REPLAY_DEBUG"):
                    print("replay invalid: constituent recording gone", flush=True)
                return False
        cmds.append(hit[0])
    vk = dev.vk
    arr = (_vp * len(cmds))(*cmds)
    submit = _SubmitInfo(4, None, 0, None, None, len(cmds), arr, 0, None)
    fc = _FenceCreate(8, None, 0)
    fence = _vp()
    _check(vk.vkCreateFence(dev.device, ctypes.byref(fc), None, ctypes.byref(fence)), "vkCreateFence")
    try:
        _check(vk.vkQueueSubmit(dev.queue, 1, ctypes.byref(submit), fence), "vkQueueSubmit")
        _check(vk.vkWaitForFences(dev.device, 1, (_vp * 1)(fence), 1, 0xFFFFFFFFFFFFFFFF),
               "vkWaitForFences")
    finally:
        vk.vkDestroyFence(dev.device, fence, None)
    return True


def read_dispatch(entry):
    """(count, idx, val) of one recorded hierarchical dispatch, from its result buffers."""
    bufs, nd, nt, nbins, cascade = entry
    count = int(bufs["args_refine" if cascade else "args"].read(np.uint32, 1)[0])
    if count == 0:
        return 0, None, None
    # From the refined pairs (the survivor list): a sparse recording does not clear the
    # dense tables, and the refine writes every bin of a listed pair.
    idx, val = Context._read_peaks(bufs, "surv1" if cascade else "surv", count,
                                   nd, nt, nbins, True).dense()
    return count, idx, val


#: One _Device per Vulkan device index, for the life of the process.
_DEVICES = {}

#: Live contexts by id(), for validating cached fused recordings (keys hold ids).
import weakref as _weakref
_CONTEXTS_BY_ID = _weakref.WeakValueDictionary()


class _Device:
    """A Vulkan instance and logical device, its compute queues, command pool and pipelines."""

    def __init__(self, index):
        vk, err = _vulkan._load()
        if vk is None:
            raise VulkanError(err)
        self.vk = vk
        # Every Context uses THIS function table (vk is shared): argtypes set on a context's
        # own table were dropped. VkDeviceSize is 64-bit; without argtypes ctypes passes a
        # Python int as a C int, truncating offsets and sizes (or crashing).
        vk.vkCmdFillBuffer.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                       ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint32]
        vk.vkCmdDispatchIndirect.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint64]
        vk.vkCmdUpdateBuffer.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint64,
                                         ctypes.c_uint64, ctypes.c_void_p]
        self.pipelines = {}
        self.collector = None        # a _FusedBatch while filter_series_many is collecting
        self.trace = None            # fused-batch keys flushed while a SegmentPlan traces
        app = _vulkan._AppInfo(0, None, b"matchedfilter", 1, b"matchedfilter", 1,
                               (1 << 22) | (1 << 12))
        ci = _vulkan._InstInfo(1, None, 0, ctypes.pointer(app), 0, None, 0, None)
        self.instance = _vp()
        _check(vk.vkCreateInstance(ctypes.byref(ci), None,
                                   ctypes.byref(self.instance)), "vkCreateInstance")

        count = _u32(0)
        vk.vkEnumeratePhysicalDevices(self.instance, ctypes.byref(count), None)
        if index >= count.value:
            raise VulkanError("no Vulkan device with index %d" % index)
        handles = (_vp * count.value)()
        vk.vkEnumeratePhysicalDevices(self.instance, ctypes.byref(count), handles)
        self.physical = _vp(handles[index])

        self.queue_family, fam_qcount = self._compute_queue_family()
        q_count = max(1, min(int(fam_qcount), 4))
        priorities = (ctypes.c_float * q_count)(*(1.0 for _ in range(q_count)))
        qci = _QueueCreate(2, None, 0, self.queue_family, q_count, priorities)
        dci = _DeviceCreate(3, None, 0, 1, ctypes.pointer(qci),
                            0, None, 0, None, None)
        self.device = _vp()
        _check(vk.vkCreateDevice(self.physical, ctypes.byref(dci), None,
                                 ctypes.byref(self.device)), "vkCreateDevice")
        self.queues = []
        for q_idx in range(q_count):
            q = _vp()
            vk.vkGetDeviceQueue(self.device, self.queue_family, q_idx,
                                ctypes.byref(q))
            self.queues.append(q)
        self.queue = self.queues[0]

        # What this device will actually give a workgroup. Several kernels
        # are built at 64 KB because that is fastest here, and Apple allows
        # 32 KB -- so the size has to be asked for rather than assumed. A
        # software rasteriser will not reveal the mistake: llvmpipe reports
        # 32 KB and runs a 64 KB kernel regardless.
        props = (ctypes.c_ubyte * 2048)()
        vk.vkGetPhysicalDeviceProperties(self.physical, ctypes.byref(props))
        # vendorID is the third uint32 in VkPhysicalDeviceProperties.
        # Intel's native trig loses accuracy in repeated FFT rotations.
        # A pipeline specialization selects accurate twiddles without adding
        # a runtime branch or changing arithmetic on other vendors.
        self._accurate_trig = ctypes.cast(props, ctypes.POINTER(_u32))[2] == 0x8086
        self.max_shared_memory = int(ctypes.cast(
            ctypes.byref(props, _OFF_SHARED_MEMORY),
            ctypes.POINTER(_u32))[0])
        # n=16384 needs a 1024-thread workgroup, which is exactly the limit
        # on Apple hardware and on this one. A device offering fewer cannot
        # run the larger kernels at all, and should say so rather than fail
        # to create a pipeline.
        self.max_invocations = int(ctypes.cast(
            ctypes.byref(props, _OFF_MAX_INVOCATIONS),
            ctypes.POINTER(_u32))[0])

        self.max_dispatch_x = int(ctypes.cast(
            ctypes.byref(props, _OFF_MAX_INVOCATIONS - 12),
            ctypes.POINTER(_u32))[0])

        self.subgroup_size = 32
        try:
            if hasattr(vk, "vkGetPhysicalDeviceProperties2"):
                sub_props = _SubgroupProperties(1000094000, None, 0, 0, 0, 0)
                props2 = _PhysicalDeviceProperties2(
                    1000059000,
                    ctypes.cast(ctypes.pointer(sub_props), _vp),
                    (ctypes.c_ubyte * 2048)()
                )
                vk.vkGetPhysicalDeviceProperties2.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
                vk.vkGetPhysicalDeviceProperties2.restype = None
                vk.vkGetPhysicalDeviceProperties2(self.physical, ctypes.byref(props2))
                if sub_props.subgroupSize > 0:
                    self.subgroup_size = int(sub_props.subgroupSize)
        except Exception:
            self.subgroup_size = 32

        self.mem_props = _MemProps()
        vk.vkGetPhysicalDeviceMemoryProperties(self.physical,
                                               ctypes.byref(self.mem_props))

        pool_info = _CmdPoolCreate(39, None, 0, self.queue_family)
        self.command_pool = _vp()
        _check(vk.vkCreateCommandPool(self.device, ctypes.byref(pool_info), None,
                                      ctypes.byref(self.command_pool)),
               "vkCreateCommandPool")
        self._ts_period = float(ctypes.cast(ctypes.byref(props, _OFF_TIMESTAMP_PERIOD),
                                            ctypes.POINTER(ctypes.c_float))[0])

    def _compute_queue_family(self):
        """The queue family with COMPUTE.

        Prefers dedicated compute queues (COMPUTE without GRAPHICS) when available
        with multiple hardware queues, falling back to the universal family.
        """
        count = _u32(0)
        self.vk.vkGetPhysicalDeviceQueueFamilyProperties(
            self.physical, ctypes.byref(count), None)
        families = (_QueueFamily * count.value)()
        self.vk.vkGetPhysicalDeviceQueueFamilyProperties(
            self.physical, ctypes.byref(count), families)
        # Dedicated compute queues with multiple hardware queues
        for i, fam in enumerate(families):
            if (fam.queueFlags & _QUEUE_COMPUTE) and not (fam.queueFlags & 1):
                return i, fam.queueCount
        for i, fam in enumerate(families):
            if fam.queueFlags & _QUEUE_COMPUTE:
                return i, fam.queueCount
        raise VulkanError("device exposes no compute queue")


class Context(InputUploads):
    """One Vulkan device, its compute queue, and the pipelines built on it."""

    max_grouped_bins = _MAX_BINS
    #: Async submission with per-slot fences: the series loop keeps several
    #: batches in flight. A declared capability, not a signature probe.
    supports_async = True
    #: peaks, peaks_grouped and hier_peaks take sparse=True and return a _SparsePeaks;
    #: hier_peaks reads only its refined pairs (the survivor list) back.
    supports_sparse = True
    #: correlate_continuous writes into rows of a caller's shared output, at an offset.
    continuous_out_views = True
    #: peaks_items(async_submit=True) returns a collector; forward takes rows=(r0, count).
    items_async = True
    forward_rows = True

    def __init__(self, index=0):
        vk, err = _vulkan._load()
        if vk is None:
            raise VulkanError(err)
        self.vk = vk
        # VkDeviceSize is 64-bit. Without argtypes ctypes passes a Python int
        # as a C int and the offset and size arrive truncated, which for a
        # fill is silent corruption rather than an error.
        vk.vkCmdFillBuffer.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                       ctypes.c_uint64, ctypes.c_uint64,
                                       ctypes.c_uint32]
        vk.vkCmdDispatchIndirect.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                             ctypes.c_uint64]
        self._batches = {}
        self._full_batches = {}
        self._tierc_batches = {}
        self._storage = {}
        self._storage_users = {}
        self._record_storage = {}
        self._record_pools = {}
        self._hier = {}
        self._hier_cascade = {}
        self._fences = {}
        self._pending_forward = None
        self._uploaded = {"data": {}, "tmpl": {}}
        self._queue_offset = 0

        self._attach_device(index)
        _CONTEXTS_BY_ID[id(self)] = self

        # MF_GPU_TIMING=1: device time of every submission, as (label, device_ms) in
        # timing_log (the contract all backends share). Off, it costs one attribute test.
        self._timing = _gputime.enabled()
        self.timing_log = []
        if self._timing:
            _gputime.register(self)
        self._ts = None
        # MF_GPU_PROFILE=1 (set when plans are recorded): timestamps between the phases of a
        # recording, reported as ("k:<phase>", device_ms) in timing_log.
        self._profile = self._timing and os.environ.get("MF_GPU_PROFILE", "0") not in ("", "0")
        self._prof = None

    _SHARED = ("vk", "instance", "physical", "queue_family", "queues", "queue", "device",
               "_accurate_trig", "max_shared_memory", "max_invocations", "max_dispatch_x",
               "subgroup_size", "mem_props", "command_pool", "_ts_period")

    def _attach_device(self, index):
        """Share the device, its queues, command pool and compiled pipelines per process.

        Creating an instance and device and compiling pipelines took ~10-50 ms per context,
        and a bank holds one plan per template group: a three-level bank built dozens. What
        stays per context is what a plan owns -- its buffers, recordings, descriptor pools,
        fences and caches -- so plans still cannot evict or free each other's work.
        """
        dev = _DEVICES.get(index)
        if dev is None:
            dev = _DEVICES[index] = _Device(index)
        self._device_state = dev
        for name in self._SHARED:
            setattr(self, name, getattr(dev, name))
        self._pipelines = dev.pipelines

    def _get_fence(self, slot=0):
        if slot is None:
            slot = 0
        fence = self._fences.get(slot)
        if fence is None:
            fc = _FenceCreate(8, None, 0)
            fence = _vp()
            _check(self.vk.vkCreateFence(self.device, ctypes.byref(fc), None,
                                         ctypes.byref(fence)), "vkCreateFence")
            self._fences[slot] = fence
        return fence

    def _wait_fence(self, fence):
        batch = getattr(self, "_collected", {}).pop(getattr(fence, "value", fence), None)
        if batch is not None:
            batch.wait()
            return
        fences = (_vp * 1)(fence)
        _check(self.vk.vkWaitForFences(self.device, 1, fences, 1, 0xFFFFFFFFFFFFFFFF),
               "vkWaitForFences")
        _check(self.vk.vkResetFences(self.device, 1, fences), "vkResetFences")

    def memory_type(self, allowed_bits, readback=False):
        """A memory type for this buffer; host-visible either way.

        Direction decides the preference, because the two wants are opposed.
        A buffer the CPU WRITES wants DEVICE_LOCAL and host-visible -- the
        resizable-BAR heap -- which is write-combined: streaming stores go
        straight to the card. A buffer the CPU READS wants HOST_CACHED,
        because reads from write-combined memory are uncached and crawl.

        Measured on gfx1151: the peak outputs came back at 240 MB/s, so at
        n=16384 with ten bins the 3.9 MB readback cost 16 ms against 24 ms
        for the kernel that produced it. Same allocation, one flag.
        """
        want = _MEM_HOST_VISIBLE | _MEM_HOST_COHERENT
        order = ((want | _MEM_HOST_CACHED, want | _MEM_DEVICE_LOCAL, want)
                 if readback else (want | _MEM_DEVICE_LOCAL, want))
        for require in order:
            for i in range(self.mem_props.memoryTypeCount):
                flags = self.mem_props.memoryTypes[i].propertyFlags
                if allowed_bits & (1 << i) and (flags & require) == require:
                    return i
        raise VulkanError("no host-visible memory type available")

    # ---- pipeline ---------------------------------------------------------
    def _refine_file(self, n):
        """refineListed for `n`, portable build where the device needs it."""
        info = (_manifest().get("modules", {}).get(str(n)) or {}).get("refine")
        if info and info.get("portable") \
                and _manifest()["modules"][str(n)].get("lds_bytes", 0) \
                > self.max_shared_memory:
            return info["portable"]["file"]
        return "refine_%d.spv" % n

    def _peak_file(self, n, nbins, refine=False):
        general = self._refine_file(n) if refine else self._kernel_file(n)
        info = _manifest().get("modules", {}).get(str(n), {})
        if refine:
            info = info.get("refine", {})
        one = info.get("one_bin") if nbins == 1 else None
        if one:
            if general.endswith("_lds32.spv"):
                return one.get("portable", {}).get("file", general)
            return one["file"]
        return general

    def pipeline(self, n):
        """Build (and cache) the compute pipeline for transform length ``n``.

        Cached because creating a pipeline compiles the SPIR-V in the driver,
        which costs milliseconds -- far more than a dispatch -- and a batched
        workload calls this once and dispatches many times.
        """
        return self._build_pipeline(n, self._kernel_file(n), _NBIND, _PUSH_BYTES)

    def _kernel_file(self, n):
        """The fastest variant this device can actually run.

        Falls back to the 32 KB build when the preferred one asks for more
        shared memory than the device offers, rather than failing to create
        the pipeline on the user's machine.
        """
        info = _manifest().get("modules", {}).get(str(n))
        if info and info.get("local_size", [0])[0] > self.max_invocations:
            raise UnsupportedSize(
                "n=%d needs a %d-thread workgroup and this device allows %d; "
                "use a shorter transform or device='cpu'"
                % (n, info["local_size"][0], self.max_invocations))
        if info and info.get("lds_bytes", 0) > self.max_shared_memory:
            alt = info.get("portable")
            if alt is None:
                raise VulkanError(
                    "n=%d needs %d KB of workgroup memory and this device "
                    "offers %d KB" % (n, info["lds_bytes"] // 1024,
                                      self.max_shared_memory // 1024))
            return alt["file"]
        return "tierb_%d.spv" % n

    def _build_pipeline(self, key, filename, nbind, push_bytes):
        if key in self._pipelines:
            return self._pipelines[key]
        vk = self.vk
        blob = (_SPIRV / filename).read_bytes()
        code = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        sm_info = _ShaderModule(16, None, 0, len(blob), ctypes.cast(code, _vp))
        module = _vp()
        _check(vk.vkCreateShaderModule(self.device, ctypes.byref(sm_info), None,
                                       ctypes.byref(module)), "vkCreateShaderModule")

        bindings = (_LayoutBinding * nbind)(
            *[_LayoutBinding(i, _DESC_STORAGE_BUFFER, 1, _STAGE_COMPUTE, None)
              for i in range(nbind)])
        sl_info = _SetLayoutCreate(32, None, 0, nbind, bindings)
        set_layout = _vp()
        _check(vk.vkCreateDescriptorSetLayout(self.device, ctypes.byref(sl_info),
                                              None, ctypes.byref(set_layout)),
               "vkCreateDescriptorSetLayout")

        # The uniform entry-point parameters compile to PUSH CONSTANTS, not
        # to a descriptor. Taking that from the compiled module rather than
        # the source is the difference between working and binding a buffer
        # the shader never reads.
        push = _PushRange(_STAGE_COMPUTE, 0, push_bytes)
        layouts = (_vp * 1)(set_layout)
        pl_info = _PipelineLayoutCreate(30, None, 0, 1, ctypes.cast(layouts, _vp),
                                        1 if push_bytes else 0,
                                        ctypes.pointer(push) if push_bytes else None)
        layout = _vp()
        _check(vk.vkCreatePipelineLayout(self.device, ctypes.byref(pl_info), None,
                                         ctypes.byref(layout)),
               "vkCreatePipelineLayout")

        entries = []
        data_vals = []
        offset = 0

        # Subgroup specialization (constant ID 74)
        entries.append(_SpecializationEntry(74, offset, 4))
        data_vals.append(int(self.subgroup_size))
        offset += 4

        # Intel accurate trig (constant ID 73)
        if self._accurate_trig:
            entries.append(_SpecializationEntry(73, offset, 4))
            data_vals.append(1)
            offset += 4

        c_entries = (_SpecializationEntry * len(entries))(*entries)
        c_data = (_u32 * len(data_vals))(*data_vals)
        spec_info = _SpecializationInfo(len(entries), c_entries,
                                        ctypes.sizeof(c_data),
                                        ctypes.cast(ctypes.pointer(c_data), _vp))
        special = ctypes.cast(ctypes.pointer(spec_info), _vp)
        stage = _StageCreate(18, None, 0, _STAGE_COMPUTE, module,
                             b"main", special)
        cp_info = _ComputePipelineCreate(29, None, 0, stage, layout, None, 0)
        pipe = _vp()
        _check(vk.vkCreateComputePipelines(self.device, None, 1,
                                           ctypes.byref(cp_info), None,
                                           ctypes.byref(pipe)),
               "vkCreateComputePipelines")
        vk.vkDestroyShaderModule(self.device, module, None)
        self._pipelines[key] = (pipe, layout, set_layout)
        return self._pipelines[key]

    def hier_peaks(self, n, band, data, tmpl, ct0, raw_thr,
                   binsize=None, threshold=0.0, window=None,
                   upload_data=True, upload_tmpl=True,
                   cascade_band=None, ct1=None, raw_thr1=None,
                   slot=None, async_submit=False, sparse=False):
        """The whole hierarchical filter in ONE command buffer.

        Coarse correlation, survivor compaction, then listed refinement.
        Supports single-tier or two-tier cascade indirect execution.
        """
        if isinstance(band, (tuple, list)):
            cascade_band = band[0]
            band = band[1]
        if isinstance(ct0, (tuple, list)):
            ct1 = ct0[1]
            ct0 = ct0[0]
        if isinstance(raw_thr, (tuple, list)):
            raw_thr1 = raw_thr[1]
            raw_thr = raw_thr[0]

        vk = self.vk
        nd, nt = data.shape[0], tmpl.shape[0]
        lo, hi = (0, n) if window is None else (int(window[0]), int(window[1]))
        lo, hi = max(0, min(lo, n)), max(0, min(hi, n))
        if lo >= hi:
            raise ValueError("empty window (%d, %d)" % (lo, hi))
        binsize = n if binsize is None else int(binsize)
        nbins = -(-(hi - lo) // binsize)
        if nbins > _MAX_BINS:
            span = _MAX_BINS * binsize
            pi, pv = [], []
            for a in range(lo, hi, span):
                bnd = min(a + span, hi)
                i2, v2 = self.hier_peaks(n, band, data, tmpl, ct0, raw_thr, binsize=binsize,
                                         threshold=threshold, window=(a, bnd),
                                         upload_data=upload_data,
                                         upload_tmpl=upload_tmpl,
                                         cascade_band=cascade_band, ct1=ct1, raw_thr1=raw_thr1,
                                         slot=slot, async_submit=False)
                pi.append(i2); pv.append(v2)
                upload_data = upload_tmpl = False
            idx, val = np.concatenate(pi, axis=2), np.concatenate(pv, axis=2)
            return _sparse_from_dense(idx, val) if sparse else (idx, val)
        shift = (binsize.bit_length() - 1) if binsize & (binsize - 1) == 0 else -1
        t2 = float(threshold) ** 2 if threshold > 0 else 0.0

        if cascade_band is not None:
            band0 = int(cascade_band)
            band1 = int(band)
            thr0 = float(raw_thr)
            thr1 = float(raw_thr1)
            # A sparse caller reads only the refined pairs, which the refine writes in full:
            # its recording skips clearing the dense outputs (bool(sparse) in the key).
            key = ("hier_cascade", n, band0, band1, nd, nt, nbins, binsize, shift, lo, hi,
                   int(np.float32(t2).view(np.uint32)),
                   thr0, thr1, bool(sparse))
            key += (shared_key(data, self), shared_key(tmpl, self), slot)
            storage_key = ("hier_cascade", n, band0, band1, nd, nt, nbins, *key[-3:])
            upload_data, upload_tmpl, dsig, tsig = self._input_uploads(
                storage_key, data, tmpl, upload_data, upload_tmpl)
            batch = self._hier_cascade.get(key)
            if batch is None:
                incoming = [b for b in (shared_buffer(data, self), shared_buffer(tmpl, self)) if b is not None]
                estimate = (8*n*(nd+nt) + 4*band0*(nd+nt) + 8*band1*(nd+nt) + nd*nt*(24+12*nbins) + 24
                            - (nd*n*8 if shared_buffer(data, self) else 0)
                            - (nt*n*8 if shared_buffer(tmpl, self) else 0))
                if storage_key in self._storage:
                    estimate = 0
                self._cache_room(estimate, incoming=incoming, keep_storage=storage_key)
                fresh = storage_key not in self._storage
                pool_start = len(getattr(self, '_pools', []))
                self._capture_begin()
                try:
                    batch = self._make_hier_cascade(storage_key, n, band0, band1, nd, nt, nbins, binsize,
                                                    shift, lo, hi, t2, thr0, thr1, data, tmpl,
                                                    clear_out=not sparse)
                finally:
                    self._capture_end(batch[-1] if batch else None)
                self._hier_cascade[key] = batch
                self._register_record('hier_cascade', key, storage_key, pool_start)
                if fresh:
                    upload_data = upload_tmpl = True
            self._cache_touch('hier_cascade', key)
            bufs, cmd = batch
            # What a traced segment (SegmentPlan) reads back on replay.
            self._last_dispatch = (bufs, nd, nt, nbins, True)
            if upload_data:
                write_input(bufs["data"], data)
                if shared_buffer(data, self) is not None:
                    pass
                else:
                    bufs["cdata0"].write(_pack_half2(data[:, :band0]))
                    bufs["cdata1"].write(np.ascontiguousarray(data[:, :band1], np.complex64))
                self._uploaded["data"][storage_key] = dsig
            if upload_tmpl:
                write_input(bufs["tmpl"], tmpl)
                bufs["ct0"].write(_pack_half2(ct0))
                bufs["ct1"].write(np.ascontiguousarray(ct1, np.complex64))
                self._uploaded["tmpl"][storage_key] = tsig

            fence = self._get_fence(slot) if (async_submit and slot is not None) else None
            if async_submit and slot is not None:
                self._submit(cmd, fence=fence, wait=False, slot=slot)
            else:
                self._submit(cmd)

            def readback():
                if fence is not None:
                    self._wait_fence(fence)
                surv_count = int(bufs["args_refine"].read(np.uint32, 1)[0])
                self.last_refinements = surv_count
                self.last_tier1_survivors = int(bufs["args_tier1"].read(np.uint32, 1)[0])
                return self._read_peaks(bufs, "surv1", surv_count, nd, nt, nbins, sparse)
            return self._track(readback) if async_submit else readback()

        key = ("hier", n, band, nd, nt, nbins, binsize, shift, lo, hi,
               int(np.float32(t2).view(np.uint32)),
               float(raw_thr), bool(sparse))
        key += (shared_key(data, self), shared_key(tmpl, self), slot)
        storage_key = ("hier", n, band, nd, nt, nbins, *key[-3:])
        upload_data, upload_tmpl, dsig, tsig = self._input_uploads(
            storage_key, data, tmpl, upload_data, upload_tmpl)
        batch = self._hier.get(key)
        if batch is None:
            incoming = [b for b in (shared_buffer(data, self), shared_buffer(tmpl, self)) if b is not None]
            estimate = (8*n*(nd+nt) + 8*band*(nd+nt) + nd*nt*(16+12*nbins) + 12
                        - (nd*n*8 if shared_buffer(data, self) else 0)
                        - (nt*n*8 if shared_buffer(tmpl, self) else 0))
            if storage_key in self._storage:
                estimate = 0
            self._cache_room(estimate, incoming=incoming, keep_storage=storage_key)
            fresh = storage_key not in self._storage
            pool_start = len(getattr(self, '_pools', []))
            self._capture_begin()
            try:
                batch = self._make_hier(storage_key, n, band, nd, nt, nbins, binsize,
                                        shift, lo, hi, t2, raw_thr, data, tmpl,
                                        clear_out=not sparse)
            finally:
                self._capture_end(batch[-1] if batch else None)
            self._hier[key] = batch
            self._register_record('hier', key, storage_key, pool_start)
            if fresh:
                upload_data = upload_tmpl = True
        self._cache_touch('hier', key)
        bufs, cmd = batch
        # What a traced segment (SegmentPlan) reads back on replay.
        self._last_dispatch = (bufs, nd, nt, nbins, False)
        if upload_data:
            write_input(bufs["data"], data)
            if shared_buffer(data, self) is not None:
                pass
            elif _use_c16(band) and not _COARSE_TILE.get(band):
                bufs["cdata"].write(_pack_half2(data[:, :band]))
            else:
                bufs["cdata"].write(np.ascontiguousarray(data[:, :band], np.complex64))
            self._uploaded["data"][storage_key] = dsig
        if upload_tmpl:
            write_input(bufs["tmpl"], tmpl)
            if _use_c16(band) and not _COARSE_TILE.get(band):
                bufs["ct0"].write(_pack_half2(ct0))
            else:
                bufs["ct0"].write(np.ascontiguousarray(ct0, np.complex64))
            self._uploaded["tmpl"][storage_key] = tsig

        fence = self._get_fence(slot) if (async_submit and slot is not None) else None
        if async_submit and slot is not None:
            self._submit(cmd, fence=fence, wait=False, slot=slot)
        else:
            self._submit(cmd)

        def readback():
            if fence is not None:
                self._wait_fence(fence)
            surv_count = int(bufs["args"].read(np.uint32, 1)[0])
            self.last_refinements = surv_count
            return self._read_peaks(bufs, "surv", surv_count, nd, nt, nbins, sparse)
        return self._track(readback) if async_submit else readback()

    @staticmethod
    def _read_peaks(bufs, surv_key, count, nd, nt, nbins, sparse):
        """The refined result: dense (idx, val), or a _SparsePeaks read from the refined
        pairs alone (the survivor list): the refine writes every bin of a listed pair."""
        if sparse:
            from . import _SparsePeaks
            rows = np.sort(bufs[surv_key].view(np.uint32, count).astype(np.int64))
            ri = bufs["idx"].view(np.int32, nd * nt * nbins).reshape(nd * nt, nbins)[rows]
            k, b = np.nonzero(ri >= 0)
            vals = bufs["val"].view(np.complex64, nd * nt * nbins).reshape(nd * nt, nbins)
            return _SparsePeaks((nd, nt, nbins), rows[k] * nbins + b, ri[k, b],
                                vals[rows[k], b])
        if count == 0:
            return (np.full((nd, nt, nbins), -1, dtype=np.int32),
                    np.zeros((nd, nt, nbins), dtype=np.complex64))
        out = nd * nt * nbins
        return (bufs["idx"].read(np.int32, out).reshape(nd, nt, nbins),
                bufs["val"].read(np.complex64, out).reshape(nd, nt, nbins))

    def _descriptor_set(self, set_layout, bufs, offsets=None):
        vk = self.vk
        nbind = len(bufs)
        sizes = (_PoolSize * 1)(_PoolSize(_DESC_STORAGE_BUFFER, nbind))
        dp = _DescPoolCreate(33, None, 0, 1, 1, sizes)
        pool = _vp()
        _check(vk.vkCreateDescriptorPool(self.device, ctypes.byref(dp), None,
                                         ctypes.byref(pool)),
               "vkCreateDescriptorPool")
        self._pools = getattr(self, "_pools", [])
        self._pools.append(pool)
        layouts = (_vp * 1)(set_layout)
        da = _DescSetAlloc(34, None, pool, 1, ctypes.cast(layouts, _vp))
        dset = _vp()
        _check(vk.vkAllocateDescriptorSets(self.device, ctypes.byref(da),
                                           ctypes.byref(dset)),
               "vkAllocateDescriptorSets")
        # A view's nbytes already excludes its own offset (_Borrowed): the range runs from
        # the descriptor offset to the end of the whole buffer.
        infos = (_DescBufferInfo * nbind)(
            *[_DescBufferInfo(b.handle, offset, b.nbytes + getattr(b, 'offset', 0) - offset)
              for b, offset in zip(bufs, offsets or [0] * nbind)])
        writes = (_WriteDescSet * nbind)(*[
            _WriteDescSet(35, None, dset, i, 0, 1, _DESC_STORAGE_BUFFER, None,
                          ctypes.pointer(infos[i]), None) for i in range(nbind)])
        vk.vkUpdateDescriptorSets(self.device, nbind, writes, 0, None)
        return dset

    def _coarse_geometry(self, band, nd, nt):
        """(pairs per workgroup, templates per tile, groups, ragged) for the packed coarse kernel.

        A pair takes band/16 threads, so pairs are packed until a workgroup fills one wave of
        THIS device. The rule was 512/band -- a wave32 -- and this Radeon runs wave64: band 128
        filled half of every wave and band 64 a quarter. MF_VK_COARSE_PPG caps it, for
        measurement.

        A tiled build (TILE_T templates per pair slot) takes RAGGED tiles: each slot covers
        TILE_T templates of one data row and the row's last tile is clamped inside the kernel,
        so any template count and any group count work -- the host passes the row count and
        dispatches ceil(rows * ceil(nt/TILE_T) / PPG) groups. The exact-tile rule it replaces
        (nt % TILE_T == 0 and pairs % (PPG*TILE_T) == 0) sent every odd template count to the
        untiled build: 52% of a realistic fine segment's coarse pairs, at 2.5x the cycles per
        pair. Untiled builds keep exact geometry: the largest built PPG dividing the pair count.
        """
        wg = max(1, band // 16)
        want = max(1, int(self.subgroup_size) // wg)
        # At most 4 pairs unless asked: the 8- and 16-pair builds hung the GPU (compute ring
        # timeout) under realistic gating on gfx1151, and measured within 3% of 4 pairs once
        # dispatches are padded. MF_VK_COARSE_PPG sets the cap, to investigate them.
        cap = int(os.environ.get("MF_VK_COARSE_PPG", "0") or 0) or 4
        want = min(want, cap)
        pairs = nd * nt
        tile = _COARSE_TILE_T.get(band, 1)
        if tile > 1:
            for ppg in sorted({p for p in (want, 32, 16, 8, 4, 2, 1) if p <= want}, reverse=True):
                name = "tierb_%d_c16%st%d.spv" % (band, "p%d" % ppg if ppg > 1 else "", tile)
                if (_SPIRV / name).is_file():
                    slots = nd * (-(-nt // tile))
                    return ppg, tile, -(-slots // ppg), True
        for ppg in sorted({p for p in (want, 32, 16, 8, 4, 2, 1) if p <= want}, reverse=True):
            name = "tierb_%d_c16%s.spv" % (band, "p%d" % ppg if ppg > 1 else "")
            if pairs % ppg or not (_SPIRV / name).is_file():
                continue
            return ppg, 1, pairs // ppg, False
        return 1, 1, pairs, False

    def _make_hier(self, key, n, band, nd, nt, nbins, binsize, shift, lo, hi,
                   t2, raw_thr, data=None, tmpl=None, clear_out=True):
        vk = self.vk
        tile = _COARSE_TILE.get(band)
        _ppg = 1          # pairs per workgroup; raised only on the c16 path
        _ragged, _groups = False, nd * nt   # see _coarse_geometry
        _tile = 1         # templates per tile; compiled into the kernel,
                          # so it is chosen with the kernel, not later
        if tile:
            cpipe, clayout, cset_layout = self._build_pipeline(
                ("coarse", band), "coarse_%d.spv" % band, 3, 8)
        elif not _use_c16(band):
            cpipe, clayout, cset_layout = self.pipeline(band)
        else:
            # The coarse ROLE, reading packed cdata/ct0. Not self.pipeline()
            # -- that is the flat filter's full-precision build of the same
            # entry, and handing it packed buffers makes it read 4-byte
            # elements as 8-byte ones: every peak comes back -1.
            # Four pairs per workgroup where the count allows it. A partial
            # group would index past the data buffer, so the fallback is not
            # optional -- it is what makes the fast build safe to ship.
            # Fill exactly one wave32 and no more. WG = band/16, so
            # PPG = 32/WG = 512/band. Measured at band 128 (WG 8): 1.911 ->
            # 0.932 ms, 2.05x. Beyond a full wave it does not pay -- band
            # 512 is already WG 32 and PPG 4 changed nothing there, while
            # band 1024 regressed 4.348 -> 5.006 as the per-group stage grew.
            # PPG = 512/band fills a wave32 where WG < 32. Safe now
            # that the peak reduction is per-pair (see tierb.slang): each
            # lane maxes into its own slot, so tiles cannot mix.
            _ppg, _tile, _groups, _ragged = self._coarse_geometry(band, nd, nt)

            # TILE_T is COMPILED INTO the kernel, so it is part of kernel
            # identity and must be decided HERE, where the kernel is
            # chosen -- not at dispatch time, where the two could disagree.
            #
            # The tile walks TILE_T CONSECUTIVE TEMPLATES from one data
            # row, so ntemplates must divide by it. The pair count dividing
            # is NOT sufficient: nt=2 with tile=4 gives 4 % 4 == 0 while
            # the tile still runs past the end of the bank. Traced at
            # band 512: 4 groups at p0 = 0, 4, 8, 12 with only pairs 0 and
            # 1 reachable, so half the signals were dismissed -- and at
            # nt=4 the out-of-range groups WROTE past the output buffer.

            cpipe, clayout, cset_layout = self._build_pipeline(
                ("coarse16", band, _ppg, _tile),
                "tierb_%d_c16%s%s.spv" % (band,
                    "p%d" % _ppg if _ppg > 1 else "",
                    "t%d" % _tile if _tile > 1 else ""),
                _NBIND, _PUSH_BYTES)
        # gatedTierB is NOT built. Its only caller was coarse_odd(), the
        # last remnant of the even/odd split, which was never invoked after
        # the odd half was removed -- so the kernel was compiled on every
        # plan and never dispatched. RADV_DEBUG=shaderstats showed it at 256
        # VGPRs with 18 SPILLED and 2304 bytes of scratch: the worst kernel
        # in the build, existing only to be compiled.
        kpipe, klayout, kset_layout = self._build_pipeline(
            "compact", "compact.spv", 3, 12)
        refine_file = self._peak_file(n, nbins, refine=True)
        rpipe, rlayout, rset_layout = self._build_pipeline(
            ("refine", refine_file), refine_file, 5, _PUSH_BYTES)
        pairs = nd * nt
        b = self._storage.get(key)
        if b is None:
            b = {
                "data":  shared_buffer(data, self) or _Buffer(self, nd * n * 8),
                "tmpl":  shared_buffer(tmpl, self) or _Buffer(self, nt * n * 8),
                "cdata": _Buffer(self, nd * band * (4 if _use_c16(band) and not tile else 8)),
                "ct0":   _Buffer(self, nt * band * (4 if _use_c16(band) and not tile else 8)),
                "cidx":  _Buffer(self, pairs * 4),
                "cval":  _Buffer(self, pairs * 8),
                # The compacted survivor list and the indirect group count.
                # args is [groupCountX, 1, 1]; compactPairs atomically bumps
                # [0], so the count never has to reach the host and this
                # stays one recorded command buffer.
                "surv":  _Buffer(self, pairs * 4),
                "args":  _Buffer(self, 12, usage=_BUF_STORAGE | _BUF_INDIRECT | _BUF_TRANSFER_DST),
                "idx":   _Buffer(self, nd * nt * nbins * 4, readback=True, usage=_BUF_STORAGE | _BUF_TRANSFER_DST),
                "val":   _Buffer(self, nd * nt * nbins * 8, readback=True, usage=_BUF_STORAGE | _BUF_TRANSFER_DST),
            }
            self._storage[key] = b
        # The tiled coarse kernel reports a magnitude per pair and nothing
        # else -- a maximum does not depend on the output ordering, so it
        # needs no index and no digit reversal.
        if tile:
            ds_coarse = self._descriptor_set(cset_layout,
                                           [b["cdata"], b["ct0"], b["cval"]])
        else:
            ds_coarse = self._descriptor_set(cset_layout,
                                           [b["cdata"], b["ct0"], b["cidx"], b["cval"]])
        ds_compact = self._descriptor_set(
            kset_layout, [b["cval"], b["surv"], b["args"]])
        ds_listed = self._descriptor_set(
            rset_layout,
            [b["data"], b["tmpl"], b["idx"], b["val"], b["surv"]])

        shared_data = shared_buffer(data, self) is not None
        if shared_data:
            ppipe, playout, psl = self._build_pipeline(
                "pack_coarse", "pack_coarse.spv", 2, 16)
            ds_pack = self._descriptor_set(psl, [b["data"], b["cdata"]])

        cb = _CmdBufAlloc(40, None, self.command_pool, 0, 1)
        cmd = _vp()
        _check(vk.vkAllocateCommandBuffers(self.device, ctypes.byref(cb),
                                           ctypes.byref(cmd)),
               "vkAllocateCommandBuffers")
        _check(vk.vkBeginCommandBuffer(cmd, ctypes.byref(
            _CmdBufBegin(42, None, 0, None))), "vkBeginCommandBuffer")
        self._stamp(cmd, "start")

        def coarse(ds):
            vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, cpipe)
            sets = (_vp * 1)(ds)
            vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, clayout, 0, 1,
                                       sets, 0, None)
            if tile:
                pc = (ctypes.c_uint32 * 2)(nt, pairs)
                vk.vkCmdPushConstants(cmd, clayout, _STAGE_COMPUTE, 0, 8,
                                      ctypes.byref(pc))
                vk.vkCmdDispatch(cmd, (pairs + tile - 1) // tile, 1, 1)
            else:
                # One bin over the coarse window span: the reported peak IS
                # the maximum, which is what the gate needs. Widen by one coarse
                # sample so rounding the caller's window remains conservative.
                R_coarse = n // band
                cstart = lo // R_coarse
                cend = (hi + R_coarse - 1) // R_coarse
                if cend > band:
                    cend = band
                if cstart > 0:
                    cstart -= 1
                cend = max(cstart + 1, cend)
                cspan = max(1, cend - cstart)
                shift_c = (cspan.bit_length() - 1) if cspan & (cspan - 1) == 0 else -1
                # A ragged-tile build reads the data row count where the
                # (unused, one-bin) coarse bin size would go.
                pc = (ctypes.c_uint32 * 7)(nt, cstart, cend, nd if _ragged else cspan,
                                           shift_c & 0xFFFFFFFF, 1, 0)
                vk.vkCmdPushConstants(cmd, clayout, _STAGE_COMPUTE, 0,
                                      _PUSH_BYTES, ctypes.byref(pc))
                # PPG pairs per workgroup and TILE_T templates per pair,
                # so PPG*TILE_T times fewer groups.
                #
                # _tile is the one the KERNEL was compiled with -- it is
                # chosen where the pipeline is chosen. Recomputing it here
                # is what let the two disagree: the kernel carried tile 4
                # while this dispatched for tile 1.
                vk.vkCmdDispatch(cmd, _groups, 1, 1)

        def barrier(src_stage=_STAGE_COMPUTE_BIT, dst_stage=_STAGE_COMPUTE_BIT,
                    src_access=_ACCESS_SHADER_WRITE, dst_access=_ACCESS_SHADER_READ):
            mb = _MemBarrier(46, None, src_access, dst_access)
            vk.vkCmdPipelineBarrier(cmd, src_stage, dst_stage,
                                    0, 1, ctypes.byref(mb), 0, None, 0, None)

        # Pairs that do not survive are never visited now, so their -1 has
        # to be written up front rather than by a workgroup that launches
        # only to exit. That is the whole saving: 1.394 ms at 512x512.
        # Only the twelve bytes of args. The output needs no clear: the
        # compaction kernel walks every pair and writes the -1 for the ones
        # it dismisses, so filling 3 MB here would only be overwriting
        # slots the refine is about to fill anyway.
        _reset_args(vk, cmd, b["args"])                       # count 0, y = z = 1
        if clear_out:                       # pairs never refined read as -1 / 0 (dense)
            vk.vkCmdFillBuffer(cmd, b["idx"].handle, 0, _WHOLE_SIZE, 0xFFFFFFFF)
            vk.vkCmdFillBuffer(cmd, b["val"].handle, 0, _WHOLE_SIZE, 0)
        # Compaction atomically updates the filled count, and indirect fetch
        # reads all three words. With zero survivors, even the count remains
        # a transfer-only write: the later shader-write barrier cannot cover it.
        barrier(src_stage=_STAGE_TRANSFER_BIT, src_access=_ACCESS_TRANSFER_WRITE,
                dst_stage=_STAGE_COMPUTE_BIT | _STAGE_DRAW_INDIRECT_BIT,
                dst_access=_ACCESS_SHADER_READ | _ACCESS_SHADER_WRITE | _ACCESS_INDIRECT_READ)
        self._stamp(cmd, "fill")

        if shared_data:
            vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, ppipe)
            sets = (_vp * 1)(ds_pack)
            vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, playout,
                                      0, 1, sets, 0, None)
            pc = (ctypes.c_uint32 * 4)(n, band, nd*band,
                                      int(_use_c16(band) and not tile))
            vk.vkCmdPushConstants(cmd, playout, _STAGE_COMPUTE, 0, 16,
                                  ctypes.byref(pc))
            vk.vkCmdDispatch(cmd, (nd*band + 255)//256, 1, 1)
            barrier()
            self._stamp(cmd, "pack")

        coarse(ds_coarse)
        barrier()
        self._stamp(cmd, "coarse%d" % band)

        vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, kpipe)
        sets = (_vp * 1)(ds_compact)
        vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, klayout, 0, 1,
                                   sets, 0, None)
        kpc = (ctypes.c_uint32 * 3)(
            pairs, int(np.float32(raw_thr).view(np.uint32)), nbins)
        vk.vkCmdPushConstants(cmd, klayout, _STAGE_COMPUTE, 0, 12,
                              ctypes.byref(kpc))
        vk.vkCmdDispatch(cmd, (pairs + 255) // 256, 1, 1)
        # The count is consumed by indirect-command fetch, not by a shader.
        # Missing this dependency made Intel use the previous dispatch count
        # (zero on first use), even while the host read the new count later.
        barrier(dst_stage=_STAGE_COMPUTE_BIT | _STAGE_DRAW_INDIRECT_BIT,
                dst_access=_ACCESS_SHADER_READ | _ACCESS_SHADER_WRITE | _ACCESS_INDIRECT_READ)
        self._stamp(cmd, "compact")

        vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, rpipe)
        sets = (_vp * 1)(ds_listed)
        vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, rlayout, 0, 1,
                                   sets, 0, None)
        pc = (ctypes.c_uint32 * 7)(
            nt, lo, hi, binsize, shift & 0xFFFFFFFF, nbins,
            int(np.float32(t2).view(np.uint32)))
        vk.vkCmdPushConstants(cmd, rlayout, _STAGE_COMPUTE, 0,
                              _PUSH_BYTES, ctypes.byref(pc))
        vk.vkCmdDispatchIndirect(cmd, b["args"].handle, 0)
        # Host readback includes the survivor count, which remains a fill
        # write when no pair survives, as well as shader-written peaks.
        barrier(src_stage=_STAGE_COMPUTE_BIT | _STAGE_TRANSFER_BIT,
                src_access=_ACCESS_SHADER_WRITE | _ACCESS_TRANSFER_WRITE,
                dst_stage=_STAGE_HOST_BIT, dst_access=_ACCESS_HOST_READ)
        self._stamp(cmd, "refine")
        _check(vk.vkEndCommandBuffer(cmd), "vkEndCommandBuffer")
        return b, cmd

    def _make_hier_cascade(self, key, n, band0, band1, nd, nt, nbins, binsize, shift, lo, hi,
                           t2, raw_thr0, raw_thr1, data=None, tmpl=None, clear_out=True):
        vk = self.vk
        _ppg0, _tile0, _groups0, _ragged0 = self._coarse_geometry(band0, nd, nt)

        cpipe0, clayout0, cset_layout0 = self._build_pipeline(
            ("coarse16", band0, _ppg0, _tile0),
            "tierb_%d_c16%s%s.spv" % (band0,
                "p%d" % _ppg0 if _ppg0 > 1 else "",
                "t%d" % _tile0 if _tile0 > 1 else ""),
            _NBIND, _PUSH_BYTES)

        kpipe, klayout, kset_layout = self._build_pipeline(
            "compact", "compact.spv", 3, 12)

        refine_file1 = self._peak_file(band1, 1, refine=True)
        cpipe1, clayout1, cset_layout1 = self._build_pipeline(
            ("refine", refine_file1), refine_file1, 5, _PUSH_BYTES)

        refine_file = self._peak_file(n, nbins, refine=True)
        rpipe, rlayout, rset_layout = self._build_pipeline(
            ("refine", refine_file), refine_file, 5, _PUSH_BYTES)

        pairs = nd * nt
        b = self._storage.get(key)
        if b is None:
            b = {
                "data":        shared_buffer(data, self) or _Buffer(self, nd * n * 8),
                "tmpl":        shared_buffer(tmpl, self) or _Buffer(self, nt * n * 8),
                "cdata0":      _Buffer(self, nd * band0 * 4),
                "ct0":         _Buffer(self, nt * band0 * 4),
                "cidx0":       _Buffer(self, pairs * 4),
                "cval0":       _Buffer(self, pairs * 8),
                "surv0":       _Buffer(self, pairs * 4),
                "args_tier1":  _Buffer(self, 12, usage=_BUF_STORAGE | _BUF_INDIRECT | _BUF_TRANSFER_DST),
                "cdata1":      _Buffer(self, nd * band1 * 8),
                "ct1":         _Buffer(self, nt * band1 * 8),
                "cidx1":       _Buffer(self, pairs * 4),
                "cval1":       _Buffer(self, pairs * 8, usage=_BUF_STORAGE | _BUF_TRANSFER_DST),
                "surv1":       _Buffer(self, pairs * 4),
                "args_refine": _Buffer(self, 12, usage=_BUF_STORAGE | _BUF_INDIRECT | _BUF_TRANSFER_DST),
                "idx":         _Buffer(self, nd * nt * nbins * 4, readback=True, usage=_BUF_STORAGE | _BUF_TRANSFER_DST),
                "val":         _Buffer(self, nd * nt * nbins * 8, readback=True, usage=_BUF_STORAGE | _BUF_TRANSFER_DST),
            }
            self._storage[key] = b

        ds_coarse0 = self._descriptor_set(
            cset_layout0, [b["cdata0"], b["ct0"], b["cidx0"], b["cval0"]])
        ds_compact0 = self._descriptor_set(
            kset_layout, [b["cval0"], b["surv0"], b["args_tier1"]])
        ds_tier1 = self._descriptor_set(
            cset_layout1, [b["cdata1"], b["ct1"], b["cidx1"], b["cval1"], b["surv0"]])
        ds_compact1 = self._descriptor_set(
            kset_layout, [b["cval1"], b["surv1"], b["args_refine"]])
        ds_listed = self._descriptor_set(
            rset_layout, [b["data"], b["tmpl"], b["idx"], b["val"], b["surv1"]])

        shared_data = shared_buffer(data, self) is not None
        if shared_data:
            ppipe, playout, psl = self._build_pipeline(
                "pack_coarse", "pack_coarse.spv", 2, 16)
            ds_pack0 = self._descriptor_set(psl, [b["data"], b["cdata0"]])
            ds_pack1 = self._descriptor_set(psl, [b["data"], b["cdata1"]])

        cb = _CmdBufAlloc(40, None, self.command_pool, 0, 1)
        cmd = _vp()
        _check(vk.vkAllocateCommandBuffers(self.device, ctypes.byref(cb),
                                           ctypes.byref(cmd)),
               "vkAllocateCommandBuffers")
        _check(vk.vkBeginCommandBuffer(cmd, ctypes.byref(
            _CmdBufBegin(42, None, 0, None))), "vkBeginCommandBuffer")
        self._stamp(cmd, "start")

        def barrier(src_stage=_STAGE_COMPUTE_BIT, dst_stage=_STAGE_COMPUTE_BIT,
                    src_access=_ACCESS_SHADER_WRITE, dst_access=_ACCESS_SHADER_READ):
            mb = _MemBarrier(46, None, src_access, dst_access)
            vk.vkCmdPipelineBarrier(cmd, src_stage, dst_stage,
                                    0, 1, ctypes.byref(mb), 0, None, 0, None)

        # 1. Clear indirect args and intermediate peak values
        _reset_args(vk, cmd, b["args_tier1"])
        _reset_args(vk, cmd, b["args_refine"])
        vk.vkCmdFillBuffer(cmd, b["cval1"].handle, 0, pairs * 8, 0)
        if clear_out:                       # pairs never refined read as -1 / 0 (dense)
            vk.vkCmdFillBuffer(cmd, b["idx"].handle, 0, _WHOLE_SIZE, 0xFFFFFFFF)
            vk.vkCmdFillBuffer(cmd, b["val"].handle, 0, _WHOLE_SIZE, 0)
        barrier(src_stage=_STAGE_TRANSFER_BIT, src_access=_ACCESS_TRANSFER_WRITE,
                dst_stage=_STAGE_COMPUTE_BIT | _STAGE_DRAW_INDIRECT_BIT,
                dst_access=_ACCESS_SHADER_READ | _ACCESS_SHADER_WRITE | _ACCESS_INDIRECT_READ)

        self._stamp(cmd, "fill")
        # 2. Extract coarse bands if shared
        if shared_data:
            vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, ppipe)
            sets = (_vp * 1)(ds_pack0)
            vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, playout, 0, 1, sets, 0, None)
            pc0 = (ctypes.c_uint32 * 4)(n, band0, nd * band0, 1)
            vk.vkCmdPushConstants(cmd, playout, _STAGE_COMPUTE, 0, 16, ctypes.byref(pc0))
            vk.vkCmdDispatch(cmd, (nd * band0 + 255) // 256, 1, 1)

            sets = (_vp * 1)(ds_pack1)
            vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, playout, 0, 1, sets, 0, None)
            pc1 = (ctypes.c_uint32 * 4)(n, band1, nd * band1, 0)
            vk.vkCmdPushConstants(cmd, playout, _STAGE_COMPUTE, 0, 16, ctypes.byref(pc1))
            vk.vkCmdDispatch(cmd, (nd * band1 + 255) // 256, 1, 1)
            barrier()
            self._stamp(cmd, "pack")

        # 3. Stage 1: Tier 0 Coarse (all pairs)
        vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, cpipe0)
        sets = (_vp * 1)(ds_coarse0)
        vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, clayout0, 0, 1, sets, 0, None)
        R_coarse0 = n // band0
        cstart0 = lo // R_coarse0
        cend0 = (hi + R_coarse0 - 1) // R_coarse0
        if cend0 > band0:
            cend0 = band0
        if cstart0 > 0:
            cstart0 -= 1
        cend0 = max(cstart0 + 1, cend0)
        cspan0 = max(1, cend0 - cstart0)
        shift_c0 = (cspan0.bit_length() - 1) if cspan0 & (cspan0 - 1) == 0 else -1
        pc0 = (ctypes.c_uint32 * 7)(nt, cstart0, cend0, nd if _ragged0 else cspan0,
                                    shift_c0 & 0xFFFFFFFF, 1, 0)
        vk.vkCmdPushConstants(cmd, clayout0, _STAGE_COMPUTE, 0, _PUSH_BYTES, ctypes.byref(pc0))
        vk.vkCmdDispatch(cmd, _groups0, 1, 1)
        barrier()
        self._stamp(cmd, "coarse%d" % band0)

        # 4. Stage 2: Compact 0
        vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, kpipe)
        sets = (_vp * 1)(ds_compact0)
        vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, klayout, 0, 1, sets, 0, None)
        kpc0 = (ctypes.c_uint32 * 3)(pairs, int(np.float32(raw_thr0).view(np.uint32)), nbins)
        vk.vkCmdPushConstants(cmd, klayout, _STAGE_COMPUTE, 0, 12, ctypes.byref(kpc0))
        vk.vkCmdDispatch(cmd, (pairs + 255) // 256, 1, 1)
        barrier(dst_stage=_STAGE_COMPUTE_BIT | _STAGE_DRAW_INDIRECT_BIT,
                dst_access=_ACCESS_SHADER_READ | _ACCESS_SHADER_WRITE | _ACCESS_INDIRECT_READ)
        self._stamp(cmd, "compact0")

        # 5. Stage 3: Tier 1 Coarse (Indirect on survivors0)
        vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, cpipe1)
        sets = (_vp * 1)(ds_tier1)
        vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, clayout1, 0, 1, sets, 0, None)
        R_coarse1 = n // band1
        cstart1 = lo // R_coarse1
        cend1 = (hi + R_coarse1 - 1) // R_coarse1
        if cend1 > band1:
            cend1 = band1
        if cstart1 > 0:
            cstart1 -= 1
        cend1 = max(cstart1 + 1, cend1)
        cspan1 = max(1, cend1 - cstart1)
        shift_c1 = (cspan1.bit_length() - 1) if cspan1 & (cspan1 - 1) == 0 else -1
        pc1 = (ctypes.c_uint32 * 7)(nt, cstart1, cend1, cspan1, shift_c1 & 0xFFFFFFFF, 1, 0)
        vk.vkCmdPushConstants(cmd, clayout1, _STAGE_COMPUTE, 0, _PUSH_BYTES, ctypes.byref(pc1))
        vk.vkCmdDispatchIndirect(cmd, b["args_tier1"].handle, 0)
        barrier()
        self._stamp(cmd, "coarse%d" % band1)

        # 6. Stage 4: Compact 1
        vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, kpipe)
        sets = (_vp * 1)(ds_compact1)
        vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, klayout, 0, 1, sets, 0, None)
        kpc1 = (ctypes.c_uint32 * 3)(pairs, int(np.float32(raw_thr1).view(np.uint32)), nbins)
        vk.vkCmdPushConstants(cmd, klayout, _STAGE_COMPUTE, 0, 12, ctypes.byref(kpc1))
        vk.vkCmdDispatch(cmd, (pairs + 255) // 256, 1, 1)
        barrier(dst_stage=_STAGE_COMPUTE_BIT | _STAGE_DRAW_INDIRECT_BIT,
                dst_access=_ACCESS_SHADER_READ | _ACCESS_SHADER_WRITE | _ACCESS_INDIRECT_READ)
        self._stamp(cmd, "compact1")

        # 7. Stage 5: Refine (Indirect on survivors1)
        vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, rpipe)
        sets = (_vp * 1)(ds_listed)
        vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, rlayout, 0, 1, sets, 0, None)
        pc = (ctypes.c_uint32 * 7)(
            nt, lo, hi, binsize, shift & 0xFFFFFFFF, nbins,
            int(np.float32(t2).view(np.uint32)))
        vk.vkCmdPushConstants(cmd, rlayout, _STAGE_COMPUTE, 0, _PUSH_BYTES, ctypes.byref(pc))
        vk.vkCmdDispatchIndirect(cmd, b["args_refine"].handle, 0)

        # 8. Host read barrier
        barrier(src_stage=_STAGE_COMPUTE_BIT | _STAGE_TRANSFER_BIT,
                src_access=_ACCESS_SHADER_WRITE | _ACCESS_TRANSFER_WRITE,
                dst_stage=_STAGE_HOST_BIT, dst_access=_ACCESS_HOST_READ)
        self._stamp(cmd, "refine")
        _check(vk.vkEndCommandBuffer(cmd), "vkEndCommandBuffer")
        return b, cmd

    def empty_shared(self, shape, dtype=np.complex64, *, readback=False):
        factory = (lambda ctx, size: _Buffer(ctx, size, readback=True)) if readback else _Buffer
        return empty_shared(self, factory, shape, dtype)

    def _forward_fused(self, n, series, starts, spectra, *, defer=False, slot=None):
        """Dispatch fused forward FFT kernel path."""
        return self.forward(n, series, starts, spectra, defer=defer, slot=slot, fused=True)

    def forward(self, n, series, starts, spectra, *, defer=False, slot=None, fused=False, rows=None):
        """Gather and normalize forward FFTs directly into shared spectra.

        rows=(r0, count): only rows r0..r0+count of starts/spectra (r0 a multiple of 64, so
        the descriptor offsets stay aligned); lets several series allocations fill one
        spectra workspace."""
        if n > 65536:
            if rows is not None:
                raise UnsupportedSize('row ranges need the one-stage forward')
            return self._forward_tierc(n, series, starts, spectra, defer=defer, slot=slot, fused=fused)
        r0, count = rows if rows is not None else (0, spectra.shape[0])
        if r0 % 64:
            raise ValueError("forward row offsets must be multiples of 64")
        vk = self.vk
        pipe, layout, sl = self._build_pipeline(
            ("forward", n), "forward_%d.spv" % n, 3, 4)
        buffers = [shared_buffer(a, self) for a in (series, starts, spectra)]
        if any(b is None for b in buffers):
            raise ValueError("forward buffers must belong to this GPU context")
        key = (n, series.size, spectra.shape[0], fused, rows,
               *(a.ctypes.data for a in (series, starts, spectra)))
        forwards = getattr(self, "_forwards", None)
        if forwards is None:
            forwards = self._forwards = {}
        batch = forwards.get(key)
        if batch is None:
            self._cache_room(0, incoming=buffers)
            pool_start = len(getattr(self, '_pools', []))
            ds = self._descriptor_set(sl, buffers, [0, r0 * 4, r0 * n * 8] if r0 else None)
            cmd = _vp()
            info = _CmdBufAlloc(40, None, self.command_pool, 0, 1)
            _check(vk.vkAllocateCommandBuffers(self.device, ctypes.byref(info),
                                               ctypes.byref(cmd)), "allocate forward")
            vk = self._capture_begin()
            begin = _CmdBufBegin(42, None, 0, None)
            _check(vk.vkBeginCommandBuffer(cmd, ctypes.byref(begin)), "begin forward")
            self._stamp(cmd, "start")
            vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, pipe)
            sets = (_vp * 1)(ds)
            vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, layout, 0, 1,
                                      sets, 0, None)
            params = _u32(series.size)
            vk.vkCmdPushConstants(cmd, layout, _STAGE_COMPUTE, 0, 4,
                                  ctypes.byref(params))
            vk.vkCmdDispatch(cmd, count, 1, 1)
            barrier = _BufMemBarrier(44, None, _ACCESS_SHADER_WRITE,
                                     _ACCESS_SHADER_READ | 0x2000,
                                     _QUEUE_FAMILY_IGNORED, _QUEUE_FAMILY_IGNORED,
                                     buffers[2].handle, 0, _WHOLE_SIZE)
            vk.vkCmdPipelineBarrier(cmd, _STAGE_COMPUTE_BIT,
                                    _STAGE_COMPUTE_BIT | 0x4000,  # HOST
                                    0, 0, None, 1, ctypes.byref(barrier), 0, None)
            self._stamp(cmd, "forward")
            _check(vk.vkEndCommandBuffer(cmd), "end forward")
            self._capture_end(cmd)
            vk = self.vk
            batch = (*buffers, cmd)
            forwards[key] = batch
            self._register_record('forward', key, None, pool_start)
        self._cache_touch('forward', key)
        cmd = batch[-1]
        if defer:
            if not isinstance(getattr(self, "_pending_forward", None), dict):
                self._pending_forward = {}
            self._pending_forward[slot] = cmd
        else:
            self._submit(cmd, slot=slot)

    def _forward_tierc(self, n, series, starts, spectra, *, defer=False, slot=None, fused=False):
        info = _manifest().get('full_tierc', {}).get(str(n))
        if info is None:
            raise UnsupportedSize('no two-stage series FFT for n=%d' % n)
        buffers = [shared_buffer(a, self) for a in (series, starts, spectra)]
        if any(b is None for b in buffers):
            raise ValueError('two-stage forward buffers must belong to this GPU context')
        key = ('tierc', n, series.size, spectra.shape[0], fused, slot,
               *(a.ctypes.data for a in (series, starts, spectra)))
        forwards = getattr(self, '_forwards', None)
        if forwards is None:
            forwards = self._forwards = {}
        batch = forwards.get(key)
        if batch is None:
            p1, l1, sl1 = self._build_pipeline(('tc-fwd1', n), info['fwd1']['file'], 3, 4)
            p2, l2, sl2 = self._build_pipeline(('tc-fwd2', n), info['fwd2']['file'], 2, 0)
            self._cache_room(spectra.nbytes, incoming=buffers)
            pool_start = len(getattr(self, '_pools', []))
            slot_key = slot if slot is not None else 0
            if getattr(self, '_persistent_scratch', None) is None:
                self._persistent_scratch = {}
            if spectra.shape[0] * n * 8 <= 64 * 1024 * 1024:
                scratch_buf = self._persistent_scratch.get(slot_key)
                if scratch_buf is None or scratch_buf.nbytes < spectra.nbytes:
                    if scratch_buf is not None:
                        scratch_buf.destroy()
                    scratch_buf = _Buffer(self, max(spectra.nbytes, 64 * 1024 * 1024))
                    self._persistent_scratch[slot_key] = scratch_buf
                scratch = scratch_buf
            else:
                scratch = _Buffer(self, spectra.nbytes)
            ds1 = self._descriptor_set(sl1, (buffers[0], buffers[1], scratch))
            ds2 = self._descriptor_set(sl2, (scratch, buffers[2]))
            cmd = _vp()
            ci = _CmdBufAlloc(40, None, self.command_pool, 0, 1)
            _check(self.vk.vkAllocateCommandBuffers(self.device, ctypes.byref(ci),
                                                    ctypes.byref(cmd)), 'two-stage forward allocate')
            _check(self.vk.vkBeginCommandBuffer(cmd, ctypes.byref(
                _CmdBufBegin(42, None, 0, None))), 'two-stage forward begin')
            self.vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, p1)
            sets = (_vp * 1)(ds1)
            self.vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, l1,
                                            0, 1, sets, 0, None)
            pc = ctypes.c_uint32(series.size)
            self.vk.vkCmdPushConstants(cmd, l1, _STAGE_COMPUTE, 0, 4,
                                        ctypes.byref(pc))
            self.vk.vkCmdDispatch(cmd, spectra.shape[0]*info['n1'], 1, 1)
            bmb = _BufMemBarrier(44, None, _ACCESS_SHADER_WRITE, _ACCESS_SHADER_READ,
                                 _QUEUE_FAMILY_IGNORED, _QUEUE_FAMILY_IGNORED,
                                 scratch.handle, 0, _WHOLE_SIZE)
            self.vk.vkCmdPipelineBarrier(cmd, _STAGE_COMPUTE_BIT, _STAGE_COMPUTE_BIT,
                                         0, 0, None, 1, ctypes.byref(bmb), 0, None)
            self.vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, p2)
            sets = (_vp * 1)(ds2)
            self.vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, l2,
                                            0, 1, sets, 0, None)
            self.vk.vkCmdDispatch(cmd, spectra.shape[0]*info['n2'], 1, 1)
            barrier = _BufMemBarrier(44, None, _ACCESS_SHADER_WRITE,
                                     _ACCESS_SHADER_READ | 0x2000,
                                     _QUEUE_FAMILY_IGNORED, _QUEUE_FAMILY_IGNORED,
                                     buffers[2].handle, 0, _WHOLE_SIZE)
            self.vk.vkCmdPipelineBarrier(cmd, _STAGE_COMPUTE_BIT,
                                         _STAGE_COMPUTE_BIT | 0x4000,
                                         0, 0, None, 1, ctypes.byref(barrier), 0, None)
            _check(self.vk.vkEndCommandBuffer(cmd), 'two-stage forward end')
            batch = (*buffers, scratch, cmd)
            forwards[key] = batch
            self._register_record('forward', key, None, pool_start)
        self._cache_touch('forward', key)
        cmd = batch[-1]
        if defer:
            if not isinstance(getattr(self, "_pending_forward", None), dict):
                self._pending_forward = {}
            self._pending_forward[slot] = cmd
        else:
            self._submit(cmd, slot=slot)

    def cancel_forward(self, slot=None):
        if isinstance(getattr(self, "_pending_forward", None), dict):
            if slot is None:
                self._pending_forward.clear()
            else:
                self._pending_forward.pop(slot, None)
            if not self._pending_forward:
                self._pending_forward = None
        else:
            self._pending_forward = None

    _TS_RING = 256

    def _timestamp_pair(self, label):
        """Two recorded command buffers bracketing a submission with timestamps."""
        vk = self.vk
        if self._ts is None:
            vk.vkCmdWriteTimestamp.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                               ctypes.c_void_p, ctypes.c_uint32]
            vk.vkCmdResetQueryPool.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                               ctypes.c_uint32, ctypes.c_uint32]
            vk.vkGetQueryPoolResults.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32,
                                                 ctypes.c_uint32, ctypes.c_size_t, ctypes.c_void_p,
                                                 ctypes.c_uint64, ctypes.c_uint32]
            info = _QueryPoolCreate(11, None, 0, 2, 2 * self._TS_RING, 0)   # TIMESTAMP
            pool = _vp()
            _check(vk.vkCreateQueryPool(self.device, ctypes.byref(info), None, ctypes.byref(pool)),
                   "vkCreateQueryPool")
            cmds = (_vp * (2 * self._TS_RING))()
            alloc = _CmdBufAlloc(40, None, self.command_pool, 0, 2 * self._TS_RING)
            _check(vk.vkAllocateCommandBuffers(self.device, ctypes.byref(alloc), cmds),
                   "allocate timestamp buffers")
            for i in range(self._TS_RING):
                # As handles, not ints: indexing a c_void_p array yields a Python int, which
                # ctypes passes to a function without argtypes as a 32-bit C int.
                b, e = _vp(cmds[2 * i]), _vp(cmds[2 * i + 1])
                begin = _CmdBufBegin(42, None, 0, None)
                _check(vk.vkBeginCommandBuffer(b, ctypes.byref(begin)), "begin timestamp")
                vk.vkCmdResetQueryPool(b, pool, 2 * i, 2)
                vk.vkCmdWriteTimestamp(b, 0x1, pool, 2 * i)            # TOP_OF_PIPE
                _check(vk.vkEndCommandBuffer(b), "end timestamp")
                _check(vk.vkBeginCommandBuffer(e, ctypes.byref(begin)), "begin timestamp")
                vk.vkCmdWriteTimestamp(e, 0x2000, pool, 2 * i + 1)     # BOTTOM_OF_PIPE
                _check(vk.vkEndCommandBuffer(e), "end timestamp")
            self._ts = dict(pool=pool, cmds=cmds, next=0, pending={})
        ts = self._ts
        i = ts["next"]
        ts["next"] = (i + 1) % self._TS_RING
        if i in ts["pending"]:                 # the ring wrapped: settle that slot first
            self._timestamp_resolve(only=i)
        ts["pending"][i] = label
        return _vp(ts["cmds"][2 * i]), _vp(ts["cmds"][2 * i + 1])

    def _capture_begin(self):
        """Record the vkCmd* calls of the recording about to be built, by phase (see _stamp),
        so a fused batch can replay them interleaved with other recordings'."""
        self._cap = {"phases": [], "ops": []}
        self.vk = _CaptureVK(self.vk, self._cap)
        return self.vk

    def _capture_end(self, cmd):
        self.vk = getattr(self.vk, "_real", self.vk)
        cap, self._cap = getattr(self, "_cap", None), None
        if cap is None or cmd is None:
            return
        phases, coarse = {}, 0
        for label, ops in cap["phases"]:
            if label == "start":
                name = "start"
            elif label.startswith("coarse"):
                name = "coarse%d" % min(coarse, 1)
                coarse += 1
            elif label == "compact":
                name = "compact0"
            else:
                name = label
            phases[name] = ([o for o in ops if o[0] != "vkCmdPipelineBarrier"],
                            [o for o in ops if o[0] == "vkCmdPipelineBarrier"])
        if set(phases) - set(_FUSED_PHASES) - {"start"}:
            return                                  # an unknown structure: never fused
        phases["_serial"] = next(_RECORDING_SERIAL)
        self.__dict__.setdefault("_phases", {})[getattr(cmd, "value", cmd)] = phases

    _PROF_QUERIES = 8192

    def _stamp(self, cmd, label):
        """Mark a phase boundary in recording `cmd`: for a capture (fused batches), and with
        MF_GPU_PROFILE=1 as a timestamp."""
        cap = getattr(self, "_cap", None)
        if cap is not None:
            cap["phases"].append((label, cap["ops"]))
            cap["ops"] = []
        if not getattr(self, "_profile", False):
            return
        vk = getattr(self.vk, "_real", self.vk)
        if self._prof is None:
            for name, args in (("vkCmdWriteTimestamp", [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32]),
                               ("vkCmdResetQueryPool", [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32]),
                               ("vkGetQueryPoolResults", [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32,
                                                          ctypes.c_uint32, ctypes.c_size_t, ctypes.c_void_p,
                                                          ctypes.c_uint64, ctypes.c_uint32])):
                getattr(vk, name).argtypes = args
            info = _QueryPoolCreate(11, None, 0, 2, self._PROF_QUERIES, 0)
            pool = _vp()
            _check(vk.vkCreateQueryPool(self.device, ctypes.byref(info), None, ctypes.byref(pool)),
                   "vkCreateQueryPool")
            self._prof = dict(pool=pool, next=0, marks={}, pending=[])
        pr = self._prof
        q = pr["next"]
        if q >= self._PROF_QUERIES:
            return                                     # out of queries: stop marking
        pr["next"] = q + 1
        handle = getattr(cmd, "value", cmd)
        vk.vkCmdResetQueryPool(cmd, pr["pool"], q, 1)
        vk.vkCmdWriteTimestamp(cmd, 0x2000, pr["pool"], q)        # BOTTOM_OF_PIPE
        pr["marks"].setdefault(handle, []).append((q, label))

    def _profile_submitted(self, commands):
        pr = self._prof
        if pr is None:
            return
        for c in commands:
            h = getattr(c, "value", c)
            if h in pr["marks"]:
                if h in pr["pending"]:                 # its queries are about to be rewritten
                    self._profile_resolve()
                pr["pending"].append(h)

    def _profile_resolve(self):
        pr = self._prof
        if pr is None or not pr["pending"]:
            return
        out = ctypes.c_uint64()
        for h in pr["pending"]:
            marks = pr["marks"][h]
            times = []
            for q, label in marks:
                _check(self.vk.vkGetQueryPoolResults(self.device, pr["pool"], q, 1, 8,
                                                     ctypes.byref(out), 8, 0x3), "vkGetQueryPoolResults")
                times.append(out.value)
            for (_, label), t0, t1 in zip(marks[1:], times, times[1:]):
                self.timing_log.append(("k:" + label, (t1 - t0) * self._ts_period * 1e-6))
        pr["pending"] = []

    def _wait_queues(self):
        """Wait for every queue this context submits to. Pipelined slots run on queues 1-3, so
        waiting on queue 0 alone let a recording be freed while another queue executed it."""
        for q in self.queues:
            _check(self.vk.vkQueueWaitIdle(q), "vkQueueWaitIdle")

    def _timestamp_resolve(self, only=None):
        ts = self._ts
        if ts is None:
            return
        out = (ctypes.c_uint64 * 2)()
        for i in ([only] if only is not None else sorted(ts["pending"])):
            label = ts["pending"].pop(i)
            _check(self.vk.vkGetQueryPoolResults(self.device, ts["pool"], 2 * i, 2, 16, out, 8, 0x3),
                   "vkGetQueryPoolResults")              # 64-bit, wait
            self.timing_log.append((label, (out[1] - out[0]) * self._ts_period * 1e-6))

    def timings(self):
        """Settle outstanding timestamps and return the timing log (MF_GPU_TIMING=1)."""
        self._timestamp_resolve()
        self._profile_resolve()
        return self.timing_log

    def _submit(self, cmd, fence=None, wait=True, slot=None, pre=()):
        """Forward and correlation share one submit and completion wait (pre: commands to
        run first, in the same submission)."""
        pending = None
        if isinstance(getattr(self, "_pending_forward", None), dict):
            if slot is not None:
                pending = self._pending_forward.pop(slot, None)
            elif len(self._pending_forward) == 1:
                pending = next(iter(self._pending_forward.values()))
                self._pending_forward.clear()
            if not self._pending_forward:
                self._pending_forward = None
        else:
            pending = getattr(self, "_pending_forward", None)
            self._pending_forward = None
        commands = list(pre) + ([pending] if pending is not None else [])
        if cmd is not None:
            commands.append(cmd)
        if not commands:
            return
        batch = self._device_state.collector
        if (batch is not None and fence is not None and not wait
                and all(getattr(c, "value", c) in getattr(self, "_phases", {}) for c in commands)):
            # A fused batch (filter_series_many): recorded with the others when first waited on.
            batch.add(self, commands, fence)
            return
        if self._timing:
            label = sys._getframe(1).f_code.co_name + ("+forward" if pending is not None or pre else "")
            begin, end = self._timestamp_pair(label)
            self._profile_submitted(commands)
            commands = [begin] + commands + [end]
        cmds = (_vp * len(commands))(*commands)
        submit = _SubmitInfo(4, None, 0, None, None, len(commands), cmds, 0, None)
        # _queue_offset spreads concurrent plans over the compute queues (filter_series_many):
        # barriers order work only within a queue, so banks on different queues overlap.
        queue = (self.queues[(slot + self._queue_offset) % len(self.queues)]
                 if (getattr(self, "queues", None) and slot is not None) else self.queue)
        _check(self.vk.vkQueueSubmit(queue, 1, ctypes.byref(submit), fence),
               "vkQueueSubmit")
        if wait:
            if fence is not None:
                self._wait_fence(fence)
            else:
                _check(self.vk.vkQueueWaitIdle(queue), "vkQueueWaitIdle")

    def _make_batch(self, key, n, nd, nt, nbins, binsize, shift, lo, hi, t2, data=None, tmpl=None):
        """Buffers, descriptor set and a recorded command buffer for one shape."""
        vk = self.vk
        filename = self._peak_file(n, nbins)
        pipe, layout, set_layout = self._build_pipeline(
            ("peaks", filename), filename, _NBIND, _PUSH_BYTES)
        out = nd * nt * nbins
        bufs = self._storage.get(key)
        if bufs is None:
            bufs = (shared_buffer(data, self) or _Buffer(self, nd * n * 8),
                    shared_buffer(tmpl, self) or _Buffer(self, nt * n * 8),
                    _Buffer(self, out * 4, readback=True),
                    _Buffer(self, out * 8, readback=True))
            self._storage[key] = bufs
        b_data, b_tmpl, b_idx, b_val = bufs
        dset = self._descriptor_set(set_layout, bufs)

        cb_info = _CmdBufAlloc(40, None, self.command_pool, 0, 1)
        cmd = _vp()
        _check(vk.vkAllocateCommandBuffers(self.device, ctypes.byref(cb_info),
                                           ctypes.byref(cmd)),
               "vkAllocateCommandBuffers")
        # NOT one-time-submit: this recording is replayed on every call.
        begin = _CmdBufBegin(42, None, 0, None)
        _check(vk.vkBeginCommandBuffer(cmd, ctypes.byref(begin)),
               "vkBeginCommandBuffer")
        vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, pipe)
        sets = (_vp * 1)(dset)
        vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, layout, 0, 1,
                                   sets, 0, None)
        pc = (ctypes.c_uint32 * 7)(
            nt, lo, hi, binsize, shift & 0xFFFFFFFF, nbins,
            int(np.float32(t2).view(np.uint32)))
        vk.vkCmdPushConstants(cmd, layout, _STAGE_COMPUTE, 0, _PUSH_BYTES,
                              ctypes.byref(pc))
        vk.vkCmdDispatch(cmd, nd * nt, 1, 1)
        _check(vk.vkEndCommandBuffer(cmd), "vkEndCommandBuffer")
        return (b_data, b_tmpl, b_idx, b_val, cmd)

    def _transient_peaks(self, storage_key, n, nd, nt, nbins, binsize, shift, lo, hi, t2):
        """(command buffer, descriptor pool) for one flat-peaks call on cached buffers."""
        vk = self.vk
        filename = self._peak_file(n, nbins)
        pipe, layout, set_layout = self._build_pipeline(
            ("peaks", filename), filename, _NBIND, _PUSH_BYTES)
        pools = self.__dict__.setdefault("_pools", [])
        dset = self._descriptor_set(set_layout, self._storage[storage_key])
        pool = pools.pop()                       # owned by this call, not the cache
        cmd = _vp()
        info = _CmdBufAlloc(40, None, self.command_pool, 0, 1)
        _check(vk.vkAllocateCommandBuffers(self.device, ctypes.byref(info), ctypes.byref(cmd)),
               "allocate transient peaks")
        _check(vk.vkBeginCommandBuffer(cmd, ctypes.byref(_CmdBufBegin(42, None, 1, None))),
               "begin transient peaks")            # ONE_TIME_SUBMIT
        vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, pipe)
        vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, layout, 0, 1, (_vp * 1)(dset),
                                   0, None)
        pc = (ctypes.c_uint32 * 7)(nt, lo, hi, binsize, shift & 0xFFFFFFFF, nbins,
                                   int(np.float32(t2).view(np.uint32)))
        vk.vkCmdPushConstants(cmd, layout, _STAGE_COMPUTE, 0, _PUSH_BYTES, ctypes.byref(pc))
        vk.vkCmdDispatch(cmd, nd * nt, 1, 1)
        _check(vk.vkEndCommandBuffer(cmd), "end transient peaks")
        return cmd, pool

    def _release_transient(self, transient):
        cmd, pool = transient
        vk = self.vk
        vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
        vk.vkFreeCommandBuffers(self.device, self.command_pool, 1, (_vp * 1)(cmd))
        vk.vkDestroyDescriptorPool(self.device, pool, None)

    def peaks(self, n, data, tmpl, binsize=None, threshold=0.0, window=None,
              upload_data=True, upload_tmpl=True, slot=None, async_submit=False, sparse=False):
        return _sparsified(self._peaks(n, data, tmpl, binsize, threshold, window, upload_data,
                                       upload_tmpl, slot, async_submit), sparse)

    def _peaks(self, n, data, tmpl, binsize=None, threshold=0.0, window=None,
               upload_data=True, upload_tmpl=True, slot=None, async_submit=False):
        """Peak index and complex value per (data, template, bin).

        Mirrors MatchedFilter.run: bins are ``ceil((end-start)/binsize)``
        counted from ``start``, and a bin whose maximum does not exceed
        ``threshold`` comes back with index -1 and a zero value.  No
        magnitude is produced anywhere -- it is ``abs(value)``.
        """
        vk = self.vk
        nd, nt = data.shape[0], tmpl.shape[0]
        lo, hi = (0, n) if window is None else (int(window[0]), int(window[1]))
        lo = max(0, min(lo, n))
        hi = max(0, min(hi, n))
        if lo >= hi:
            raise ValueError("empty window (%d, %d)" % (lo, hi))
        binsize = n if binsize is None else int(binsize)
        if binsize < 1:
            raise ValueError("binsize must be >= 1")
        nbins = -(-(hi - lo) // binsize)
        if nbins > _MAX_BINS:
            # The per-bin table lives in shared memory and holds _MAX_BINS
            # entries. Bins are contiguous in the window, so splitting the
            # WINDOW on a bin boundary splits the bins exactly -- each piece
            # is an ordinary call and the results concatenate. No kernel
            # change, and no limit left to explain to a caller.
            span = _MAX_BINS * binsize
            parts_i, parts_v = [], []
            for start in range(lo, hi, span):
                stop = min(start + span, hi)
                pi, pv = self.peaks(n, data, tmpl, binsize=binsize,
                                    threshold=threshold, window=(start, stop),
                                    upload_data=upload_data,
                                    upload_tmpl=upload_tmpl,
                                    slot=slot, async_submit=False)
                parts_i.append(pi)
                parts_v.append(pv)
                upload_data = upload_tmpl = False
            return (np.concatenate(parts_i, axis=2),
                    np.concatenate(parts_v, axis=2))
        # Shift when the binsize is a power of two, divide when it is not --
        # the same split the CPU makes, and why no restriction is needed.
        shift = (binsize.bit_length() - 1) if binsize & (binsize - 1) == 0 else -1
        t2 = float(threshold) ** 2 if threshold > 0 else 0.0

        # Everything below the data itself is REUSED across calls. Rebuilding
        # it cost 0.5 ms of the 0.65 ms a 1024-pair call took: buffers,
        # descriptor pool and set, and the recorded command buffer. With them
        # cached a call is a host copy, a submit and a read -- 0.14 ms, of
        # which the dispatch is 0.07.
        #
        # The key carries the push constants because they are RECORDED into
        # the command buffer. A call that changes the threshold or the window
        # gets its own recording rather than silently running the previous
        # one, which would be wrong rather than slow.
        key = (n, nd, nt, nbins, binsize, shift, lo, hi,
               int(np.float32(t2).view(np.uint32)))
        key += (shared_key(data, self), shared_key(tmpl, self), slot)
        storage_key = ("flat", n, nd, nt, nbins, *key[-3:])
        upload_data, upload_tmpl, dsig, tsig = self._input_uploads(
            storage_key, data, tmpl, upload_data, upload_tmpl)
        batch = self._batches.get(key)
        transient = None
        windows = self.__dict__.setdefault("_flat_windows", {})
        if batch is None and storage_key in self._storage and windows.get(storage_key, 0) >= 8:
            # A stream of new windows (follow-ups): every one would be a cached recording,
            # and once the cache filled each would evict another -- descriptor pools freed,
            # every queue idled. Past 8 windows of a shape, record a one-off command
            # buffer on the cached buffers instead (released after the call); the first
            # windows of a shape stay cached, for callers that repeat them.
            transient = self._transient_peaks(storage_key, n, nd, nt, nbins, binsize, shift,
                                              lo, hi, t2)
            batch = (*self._storage[storage_key], transient[0])
        elif batch is None:
            incoming = [b for b in (shared_buffer(data, self), shared_buffer(tmpl, self)) if b is not None]
            estimate = (8*n*(nd+nt) + 12*nd*nt*nbins
                        - (nd*n*8 if shared_buffer(data, self) else 0)
                        - (nt*n*8 if shared_buffer(tmpl, self) else 0))
            if storage_key in self._storage:
                estimate = 0
            self._cache_room(estimate, incoming=incoming, keep_storage=storage_key)
            fresh = storage_key not in self._storage
            pool_start = len(getattr(self, '_pools', []))
            batch = self._make_batch(storage_key, n, nd, nt, nbins,
                                     binsize, shift, lo, hi, t2, data, tmpl)
            self._batches[key] = batch
            self._register_record('flat', key, storage_key, pool_start)
            windows[storage_key] = windows.get(storage_key, 0) + 1
            if fresh:
                upload_data = upload_tmpl = True
        if transient is None:
            self._cache_touch('flat', key)
        b_data, b_tmpl, b_idx, b_val, cmd = batch

        if upload_data:
            write_input(b_data, data)
            self._uploaded["data"][storage_key] = dsig
        if upload_tmpl:
            write_input(b_tmpl, tmpl)
            self._uploaded["tmpl"][storage_key] = tsig

        fence = self._get_fence(slot) if (async_submit and slot is not None) else None
        if async_submit and slot is not None:
            self._submit(cmd, fence=fence, wait=False, slot=slot)
        else:
            self._submit(cmd)

        out = nd * nt * nbins
        if async_submit:
            def readback():
                if fence is not None:
                    self._wait_fence(fence)
                idx = b_idx.read(np.int32, out).reshape(nd, nt, nbins)
                val = b_val.read(np.complex64, out).reshape(nd, nt, nbins)
                if transient is not None:
                    self._release_transient(transient)
                return idx, val
            return self._track(readback)
        if transient is not None:
            self._release_transient(transient)

        # int32 as the kernel wrote it. The caller's PEAK_DTYPE index is
        # int64, and assigning int32 into that field widens it during the
        # strided write that has to happen anyway -- so converting here
        # first is a whole extra pass over the output and a whole extra
        # allocation, for nothing. Measured at 65536 pairs: the host side of
        # a call was 0.168 ms, five passes over 0.79 MB.
        idx = b_idx.read(np.int32, out).reshape(nd, nt, nbins)
        val = b_val.read(np.complex64, out).reshape(nd, nt, nbins)
        return idx, val

    def peaks_items(self, n, data, tmpl, items, binsize, threshold, *, async_submit=False):
        """One submission over items (lo, hi, a, b, t): rows a:b of data against template row t,
        searched over [lo, hi) in bins of binsize. Returns per item (idx, val) shaped
        (b - a, 1, nbins). Data and templates are shared allocations; descriptor offsets select
        each item's rows. A one-off recording (follow-up windows do not repeat), with one
        descriptor pool for all its sets, released after the call.

        Every forward deferred into data (forward(..., defer=True, slot=('items', i))) goes in
        the same submission. async_submit=True submits and returns a function giving the results, so
        several plans' follow-ups share one wait; this context's next call must come after it."""
        wait = not async_submit
        vk = self.vk
        pending = getattr(self, "_items_finish", None)
        if pending is not None:
            pending()
        b_data, b_tmpl = shared_buffer(data, self), shared_buffer(tmpl, self)
        if b_data is None or b_tmpl is None:
            raise ValueError("item spectra and templates must be shared allocations")
        shift = binsize.bit_length() - 1 if binsize & (binsize - 1) == 0 else -1
        t2 = int(np.float32(float(threshold) ** 2 if threshold > 0 else 0).view(np.uint32))
        offs, nbs, size = [], [], 0
        for lo, hi, a, b, t in items:
            nb = -(-(hi - lo) // binsize)
            if nb > _MAX_BINS:
                raise UnsupportedSize("an item's window exceeds the kernel bin limit")
            offs.append(size)
            nbs.append(nb)
            size += ((b - a) * nb + 63) // 64 * 64          # 256-byte aligned offsets
        cap = getattr(self, "_items_cap", 0)
        if cap < size:
            cap = max(size, 2 * cap)
            self._items_out = (_Buffer(self, cap * 4, readback=True),
                               _Buffer(self, cap * 8, readback=True))
            self._items_cap = cap
        b_idx, b_val = self._items_out
        sizes = (_PoolSize * 1)(_PoolSize(_DESC_STORAGE_BUFFER, 4 * len(items)))
        dp = _DescPoolCreate(33, None, 0, len(items), 1, sizes)
        pool = _vp()
        _check(vk.vkCreateDescriptorPool(self.device, ctypes.byref(dp), None, ctypes.byref(pool)),
               "vkCreateDescriptorPool")
        cmd = _vp()
        try:
            info = _CmdBufAlloc(40, None, self.command_pool, 0, 1)
            _check(vk.vkAllocateCommandBuffers(self.device, ctypes.byref(info), ctypes.byref(cmd)),
                   "allocate item peaks")
            _check(vk.vkBeginCommandBuffer(cmd, ctypes.byref(_CmdBufBegin(42, None, 1, None))),
                   "begin item peaks")
            bufs = (b_data, b_tmpl, b_idx, b_val)
            bound = None
            for (lo, hi, a, b, t), off, nb in zip(items, offs, nbs):
                filename = self._peak_file(n, nb)
                pipe, layout, sl = self._build_pipeline(("peaks", filename), filename,
                                                        _NBIND, _PUSH_BYTES)
                if bound != pipe:
                    vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, pipe)
                    bound = pipe
                layouts = (_vp * 1)(sl)
                dset = _vp()
                _check(vk.vkAllocateDescriptorSets(self.device, ctypes.byref(
                    _DescSetAlloc(34, None, pool, 1, ctypes.cast(layouts, _vp))), ctypes.byref(dset)),
                    "vkAllocateDescriptorSets")
                offsets = (a * n * 8, t * n * 8, off * 4, off * 8)
                infos = (_DescBufferInfo * 4)(*[_DescBufferInfo(bf.handle, o, bf.nbytes - o)
                                                for bf, o in zip(bufs, offsets)])
                writes = (_WriteDescSet * 4)(*[
                    _WriteDescSet(35, None, dset, i, 0, 1, _DESC_STORAGE_BUFFER, None,
                                  ctypes.pointer(infos[i]), None) for i in range(4)])
                vk.vkUpdateDescriptorSets(self.device, 4, writes, 0, None)
                vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, layout, 0, 1,
                                           (_vp * 1)(dset), 0, None)
                pc = (_u32 * 7)(1, lo, hi, binsize, shift & 0xffffffff, nb, t2)
                vk.vkCmdPushConstants(cmd, layout, _STAGE_COMPUTE, 0, _PUSH_BYTES, ctypes.byref(pc))
                vk.vkCmdDispatch(cmd, b - a, 1, 1)
            barriers = (_BufMemBarrier * 2)(
                _BufMemBarrier(44, None, _ACCESS_SHADER_WRITE, 0x2000, _QUEUE_FAMILY_IGNORED,
                               _QUEUE_FAMILY_IGNORED, b_idx.handle, 0, _WHOLE_SIZE),
                _BufMemBarrier(44, None, _ACCESS_SHADER_WRITE, 0x2000, _QUEUE_FAMILY_IGNORED,
                               _QUEUE_FAMILY_IGNORED, b_val.handle, 0, _WHOLE_SIZE))
            vk.vkCmdPipelineBarrier(cmd, _STAGE_COMPUTE_BIT, 0x4000, 0, 0, None, 2,
                                    ctypes.cast(barriers, _vp), 0, None)
            _check(vk.vkEndCommandBuffer(cmd), "end item peaks")
            fwd = self._pending_forward if isinstance(getattr(self, "_pending_forward", None), dict) else {}
            pre = [fwd.pop(k) for k in sorted((k for k in fwd if isinstance(k, tuple)
                                                and k[0] == 'items'), key=lambda k: k[1])]
            if fwd is not None and not fwd:
                self._pending_forward = None
            fence = None
            if not wait:
                fence = _vp()
                _check(vk.vkCreateFence(self.device, ctypes.byref(_FenceCreate(8, None, 0)), None,
                                        ctypes.byref(fence)), "vkCreateFence")
            self._submit(cmd, fence=fence, wait=wait, pre=pre)   # with the pending forwards
        except BaseException:
            self._items_release(cmd, pool, None)
            raise
        if wait:
            self._items_release(cmd, pool, None)
            return self._items_read(items, offs, nbs, size)
        done = []

        def finish():
            if not done:
                self._items_finish = None
                try:
                    self._wait_fence(fence)
                finally:
                    self._items_release(cmd, pool, fence)
                done.append(self._items_read(items, offs, nbs, size))
            return done[0]
        self._items_finish = finish
        return finish

    def _items_release(self, cmd, pool, fence):
        vk = self.vk
        if cmd:
            vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
            vk.vkFreeCommandBuffers(self.device, self.command_pool, 1, (_vp * 1)(cmd))
        vk.vkDestroyDescriptorPool(self.device, pool, None)
        if fence is not None:
            vk.vkDestroyFence(self.device, fence, None)

    def _items_read(self, items, offs, nbs, size):
        b_idx, b_val = self._items_out
        indices = b_idx.read(np.int32, size)
        values = b_val.read(np.complex64, size)
        out = []
        for (lo, hi, a, b, t), off, nb in zip(items, offs, nbs):
            c = (b - a) * nb
            out.append((indices[off:off + c].reshape(b - a, 1, nb),
                        values[off:off + c].reshape(b - a, 1, nb)))
        return out

    def peaks_grouped(self, n, data, tmpl, groups, binsize, threshold, *, upload_tmpl=True,
                      slot=None, async_submit=False, sparse=False):
        return _sparsified(self._peaks_grouped(n, data, tmpl, groups, binsize, threshold,
                                               upload_tmpl=upload_tmpl, slot=slot,
                                               async_submit=async_submit), sparse)

    def _peaks_grouped(self, n, data, tmpl, groups, binsize, threshold, *, upload_tmpl=True,
                       slot=None, async_submit=False):
        """Run distinct flat search windows in one synchronous submission.

        Data is a shared forward-FFT batch. Descriptor offsets select each
        group's rows; padded output offsets satisfy Vulkan's storage-buffer
        alignment without changing the existing correlation kernels.
        """
        nd, nt = data.shape[0], tmpl.shape[0]
        nb = (groups[0][1] - groups[0][0] - 1) // binsize + 1
        if nb > _MAX_BINS:
            raise ValueError("grouped dispatch exceeds the kernel bin limit")
        groups = tuple(groups)
        shift = binsize.bit_length() - 1 if binsize & (binsize - 1) == 0 else -1
        t2 = np.float32(float(threshold) ** 2 if threshold > 0 else 0).view(np.uint32)
        key = ("grouped", n, nd, nt, binsize, int(t2), groups,
               shared_key(data, self), shared_key(tmpl, self), slot)
        if key[-3] is None:
            raise ValueError("grouped spectra must belong to this GPU context")
        # 64 indices occupy 256 bytes, meeting Vulkan storage-offset alignment.
        offsets, size = [], 0
        for _, _, a, b in groups:
            offsets.append(size)
            size += ((b - a) * nt * nb + 63) // 64 * 64
        _, upload_tmpl, _, tsig = self._input_uploads(
            key, data, tmpl, False, upload_tmpl)
        batch = self._batches.get(key)
        if batch is None:
            incoming = [shared_buffer(data, self)]
            if shared_buffer(tmpl, self) is not None:
                incoming.append(shared_buffer(tmpl, self))
            self._cache_room(size * 12 + (0 if len(incoming) == 2 else tmpl.nbytes),
                             incoming=incoming, keep_storage=key)
            pool_start = len(getattr(self, '_pools', []))
            bufs = (shared_buffer(data, self),
                    shared_buffer(tmpl, self) or _Buffer(self, tmpl.nbytes),
                    _Buffer(self, size * 4, readback=True),
                    _Buffer(self, size * 8, readback=True))
            self._storage[key] = bufs
            filename = self._peak_file(n, nb)
            pipe, layout, sl = self._build_pipeline(
                ("peaks", filename), filename, _NBIND, _PUSH_BYTES)
            cmd = _vp()
            info = _CmdBufAlloc(40, None, self.command_pool, 0, 1)
            vk = self.vk
            _check(vk.vkAllocateCommandBuffers(self.device, ctypes.byref(info),
                                              ctypes.byref(cmd)), "allocate grouped peaks")
            begin = _CmdBufBegin(42, None, 0, None)
            _check(vk.vkBeginCommandBuffer(cmd, ctypes.byref(begin)), "begin grouped peaks")
            vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, pipe)
            for (lo, hi, a, b), offset in zip(groups, offsets):
                ds = self._descriptor_set(sl, bufs, (a*n*8, 0, offset*4, offset*8))
                sets = (_vp * 1)(ds)
                vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, layout,
                                          0, 1, sets, 0, None)
                pc = (_u32 * 7)(nt, lo, hi, binsize, shift & 0xffffffff, nb, int(t2))
                vk.vkCmdPushConstants(cmd, layout, _STAGE_COMPUTE, 0,
                                      _PUSH_BYTES, ctypes.byref(pc))
                vk.vkCmdDispatch(cmd, (b-a)*nt, 1, 1)
            barriers = (_BufMemBarrier * 2)(
                _BufMemBarrier(44, None, _ACCESS_SHADER_WRITE, 0x2000,
                               _QUEUE_FAMILY_IGNORED, _QUEUE_FAMILY_IGNORED,
                               bufs[2].handle, 0, _WHOLE_SIZE),
                _BufMemBarrier(44, None, _ACCESS_SHADER_WRITE, 0x2000,
                               _QUEUE_FAMILY_IGNORED, _QUEUE_FAMILY_IGNORED,
                               bufs[3].handle, 0, _WHOLE_SIZE)
            )
            vk.vkCmdPipelineBarrier(cmd, _STAGE_COMPUTE_BIT, 0x4000, 0,
                                    0, None, 2, ctypes.cast(barriers, _vp), 0, None)
            _check(vk.vkEndCommandBuffer(cmd), "end grouped peaks")
            batch = (*bufs, cmd)
            self._batches[key] = batch
            self._register_record('flat', key, key, pool_start)
            upload_tmpl = True
        self._cache_touch('flat', key)
        _, b_tmpl, b_idx, b_val, cmd = batch
        if upload_tmpl:
            write_input(b_tmpl, tmpl)
            self._uploaded["tmpl"][key] = tsig
        fence = self._get_fence(slot) if (async_submit and slot is not None) else None
        if async_submit and slot is not None:
            self._submit(cmd, fence=fence, wait=False, slot=slot)
        else:
            self._submit(cmd)
        if async_submit:
            def readback():
                if fence is not None:
                    self._wait_fence(fence)
                indices = b_idx.read(np.int32, size)
                values = b_val.read(np.complex64, size)
                idx = np.empty((nd, nt, nb), np.int32)
                val = np.empty((nd, nt, nb), np.complex64)
                for (_, _, a, b), offset in zip(groups, offsets):
                    count = (b-a)*nt*nb
                    idx[a:b] = indices[offset:offset+count].reshape(b-a, nt, nb)
                    val[a:b] = values[offset:offset+count].reshape(b-a, nt, nb)
                return idx, val
            return self._track(readback)
        indices = b_idx.read(np.int32, size)
        values = b_val.read(np.complex64, size)
        idx = np.empty((nd, nt, nb), np.int32)
        val = np.empty((nd, nt, nb), np.complex64)
        for (_, _, a, b), offset in zip(groups, offsets):
            count = (b-a)*nt*nb
            idx[a:b] = indices[offset:offset+count].reshape(b-a, nt, nb)
            val[a:b] = values[offset:offset+count].reshape(b-a, nt, nb)
        return idx, val

    def _full_tile(self, n, data, tmpl, out, upload_data, upload_tmpl):
        nd, nt = data.shape[0], tmpl.shape[0]
        keys = (shared_key(data, self), shared_key(tmpl, self),
                shared_key(out, self))
        key = (n, nd, nt, *keys)
        uploads = self._input_uploads(key, data, tmpl, upload_data, upload_tmpl)
        batch = self._full_batches.get(key)
        if batch is None:
            info = (_manifest().get('modules', {}).get(str(n)) or {}).get('full')
            if info is None:
                raise UnsupportedSize('no full-correlation GPU kernel for n=%d' % n)
            filename = (info.get('portable') or {}).get('file') \
                if _manifest()['modules'][str(n)].get('lds_bytes', 0) > self.max_shared_memory \
                else info['file']
            if not filename:
                raise UnsupportedSize('no portable full-correlation GPU kernel for n=%d' % n)
            pipe, layout, sl = self._build_pipeline(('full', filename), filename, 3, 4)
            external = [b for a in (data, tmpl, out)
                        if (b := shared_buffer(a, self)) is not None]
            estimate = sum(a.nbytes for a in (data, tmpl, out)
                           if shared_buffer(a, self) is None)
            self._cache_room(estimate, incoming=external)
            pool_start = len(getattr(self, '_pools', []))
            bufs = (shared_buffer(data, self) or _Buffer(self, data.nbytes),
                    shared_buffer(tmpl, self) or _Buffer(self, tmpl.nbytes),
                    shared_buffer(out, self) or _Buffer(self, out.nbytes, readback=True))
            ds = self._descriptor_set(sl, bufs)
            cmd = _vp()
            info = _CmdBufAlloc(40, None, self.command_pool, 0, 1)
            _check(self.vk.vkAllocateCommandBuffers(self.device, ctypes.byref(info),
                                                    ctypes.byref(cmd)), 'full allocate')
            _check(self.vk.vkBeginCommandBuffer(cmd, ctypes.byref(
                _CmdBufBegin(42, None, 0, None))), 'full begin')
            self.vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, pipe)
            sets = (_vp * 1)(ds)
            self.vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, layout,
                                            0, 1, sets, 0, None)
            pc = ctypes.c_uint32(nt)
            self.vk.vkCmdPushConstants(cmd, layout, _STAGE_COMPUTE, 0, 4,
                                        ctypes.byref(pc))
            self.vk.vkCmdDispatch(cmd, nd * nt, 1, 1)
            _check(self.vk.vkEndCommandBuffer(cmd), 'full end')
            batch = (*bufs, cmd)
            self._full_batches[key] = batch
            self._register_record('full', key, None, pool_start)
            uploads = (True, True, *uploads[2:])
        self._cache_touch('full', key)
        bdata, btmpl, bout, cmd = batch
        if uploads[0]:
            write_input(bdata, data)
            self._uploaded['data'][key] = uploads[2]
        if uploads[1]:
            write_input(btmpl, tmpl)
            self._uploaded['tmpl'][key] = uploads[3]
        self._submit(cmd)
        if shared_buffer(out, self) is None:
            bout.read_into(out)

    def _tierc_tile(self, n, data, tmpl, out, upload_data, upload_tmpl):
        nd, nt = data.shape[0], tmpl.shape[0]
        info = _manifest().get('full_tierc', {}).get(str(n))
        if info is None:
            raise UnsupportedSize('no two-stage full-correlation kernel for n=%d' % n)
        key = (n, nd, nt, shared_key(data, self), shared_key(tmpl, self),
               shared_key(out, self))
        uploads = self._input_uploads(key, data, tmpl, upload_data, upload_tmpl)
        batch = self._tierc_batches.get(key)
        if batch is None:
            p1, l1, sl1 = self._build_pipeline(('tc-corr1', n), info['corr1']['file'], 3, 4)
            p2, l2, sl2 = self._build_pipeline(('tc-corr2', n), info['corr2']['file'], 2, 0)
            external = [b for a in (data, tmpl, out)
                        if (b := shared_buffer(a, self)) is not None]
            estimate = nd*nt*n*8 + sum(a.nbytes for a in (data, tmpl, out)
                                       if shared_buffer(a, self) is None)
            self._cache_room(estimate, incoming=external)
            pool_start = len(getattr(self, '_pools', []))
            bd = shared_buffer(data, self) or _Buffer(self, data.nbytes)
            bt = shared_buffer(tmpl, self) or _Buffer(self, tmpl.nbytes)
            scratch = _Buffer(self, nd*nt*n*8)
            bo = shared_buffer(out, self) or _Buffer(self, out.nbytes, readback=True)
            ds1 = self._descriptor_set(sl1, (bd, bt, scratch))
            ds2 = self._descriptor_set(sl2, (scratch, bo))
            cmd = _vp()
            ci = _CmdBufAlloc(40, None, self.command_pool, 0, 1)
            _check(self.vk.vkAllocateCommandBuffers(self.device, ctypes.byref(ci),
                                                    ctypes.byref(cmd)), 'two-stage allocate')
            _check(self.vk.vkBeginCommandBuffer(cmd, ctypes.byref(
                _CmdBufBegin(42, None, 0, None))), 'two-stage begin')
            self.vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, p1)
            sets = (_vp * 1)(ds1)
            self.vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, l1,
                                            0, 1, sets, 0, None)
            pc = ctypes.c_uint32(nt)
            self.vk.vkCmdPushConstants(cmd, l1, _STAGE_COMPUTE, 0, 4,
                                        ctypes.byref(pc))
            self.vk.vkCmdDispatch(cmd, nd*nt*info['n1'], 1, 1)
            bmb = _BufMemBarrier(44, None, _ACCESS_SHADER_WRITE, _ACCESS_SHADER_READ,
                                 _QUEUE_FAMILY_IGNORED, _QUEUE_FAMILY_IGNORED,
                                 scratch.handle, 0, _WHOLE_SIZE)
            self.vk.vkCmdPipelineBarrier(cmd, _STAGE_COMPUTE_BIT, _STAGE_COMPUTE_BIT,
                                         0, 0, None, 1, ctypes.byref(bmb), 0, None)
            self.vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, p2)
            sets = (_vp * 1)(ds2)
            self.vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, l2,
                                            0, 1, sets, 0, None)
            self.vk.vkCmdDispatch(cmd, nd*nt*info['n2'], 1, 1)
            _check(self.vk.vkEndCommandBuffer(cmd), 'two-stage end')
            batch = (bd, bt, scratch, bo, cmd)
            self._tierc_batches[key] = batch
            self._register_record('tierc', key, None, pool_start)
            uploads = (True, True, *uploads[2:])
        self._cache_touch('tierc', key)
        bd, bt, scratch, bo, cmd = batch
        if uploads[0]:
            write_input(bd, data)
            self._uploaded['data'][key] = uploads[2]
        if uploads[1]:
            write_input(bt, tmpl)
            self._uploaded['tmpl'][key] = uploads[3]
        self._submit(cmd)
        if shared_buffer(out, self) is None:
            bo.read_into(out)

    def zero_columns(self, dest, a, b):
        """Zero dest[:, a:b] of a device-shared 2-D array (or rows of one) on the device.

        Collected, and recorded by zero_columns_done() as fills in one submission behind a
        barrier, so they land after the correlation writes they may overlap. A host memset
        of a middle stage's complement is ~60 MB a call; the device clears it in ~0.3 ms."""
        sb = shared_view(dest, self, align=4)
        if sb is None or dest.ndim != 2 or b <= a or not dest.flags.c_contiguous:
            raise ValueError("zero_columns needs a device-shared 2-D array and a nonempty range")
        base = sb.offset + a * dest.itemsize
        length = (b - a) * dest.itemsize
        if base % 4 or length % 4:
            raise ValueError("zero_columns ranges must be 4-byte aligned")
        pending = self.__dict__.setdefault("_zero_ranges", [])
        row = dest.strides[0]
        pending.extend((sb, base + r * row, length) for r in range(dest.shape[0]))

    def zero_columns_done(self):
        """Record and submit every collected zero_columns range, and wait for them."""
        ranges, self._zero_ranges = getattr(self, "_zero_ranges", None) or [], []
        if not ranges:
            return
        vk = self.vk
        cmd = _vp()
        _check(vk.vkAllocateCommandBuffers(self.device, ctypes.byref(
            _CmdBufAlloc(40, None, self.command_pool, 0, 1)), ctypes.byref(cmd)), "allocate zero")
        try:
            _check(vk.vkBeginCommandBuffer(cmd, ctypes.byref(_CmdBufBegin(42, None, _ONE_TIME_SUBMIT, None))),
                   "begin zero")
            mb = _MemBarrier(46, None, _ACCESS_SHADER_WRITE | _ACCESS_TRANSFER_WRITE,
                             _ACCESS_TRANSFER_WRITE)
            vk.vkCmdPipelineBarrier(cmd, _STAGE_COMPUTE_BIT | _STAGE_TRANSFER_BIT, _STAGE_TRANSFER_BIT,
                                    0, 1, ctypes.byref(mb), 0, None, 0, None)
            for sb, off, length in ranges:
                vk.vkCmdFillBuffer(cmd, sb.handle, off, length, 0)
            mb = _MemBarrier(46, None, _ACCESS_TRANSFER_WRITE,
                             _ACCESS_HOST_READ | _ACCESS_SHADER_READ)
            vk.vkCmdPipelineBarrier(cmd, _STAGE_TRANSFER_BIT, _STAGE_HOST_BIT | _STAGE_COMPUTE_BIT,
                                    0, 1, ctypes.byref(mb), 0, None, 0, None)
            _check(vk.vkEndCommandBuffer(cmd), "end zero")
            self._submit(cmd)                   # waits; same queue as the correlation
            self._wait_queues()                 # and anything on the other queues
        finally:
            vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
            vk.vkFreeCommandBuffers(self.device, self.command_pool, 1, (_vp * 1)(cmd))

    def correlate_continuous(self, n, data, tmpl, starts, out, lo, hi,
                             *, upload_data=True, upload_tmpl=True):
        """Write valid lags into template-major shared output on the GPU."""
        nd, nt = data.shape[0], tmpl.shape[0]
        length = out.shape[1]
        # out may be rows inside a caller's shared output (continuous_out_views).
        bs, bo = shared_buffer(starts, self), shared_view(out, self)
        if bs is None or bo is None or starts.shape != (nd,) or out.shape[0] != nt:
            raise ValueError('continuous output and starts must be shared GPU buffers')
        geometry = _manifest().get('full_tierc', {}).get(str(n)) if n > 65536 else None
        if n > 65536 and geometry is None:
            raise UnsupportedSize('no two-stage continuous kernel for n=%d' % n)
        # out by address, not shared_key: a view inside an allocation has no shared_key, and
        # every row view sharing the key None replayed one view's recording into another's
        # rows. The recording holds its _Borrowed, so the address cannot be reused under it.
        key = ('series', n, nd, nt, length, lo, hi,
               shared_key(data, self), shared_key(tmpl, self),
               shared_key(starts, self), out.ctypes.data)
        uploads = self._input_uploads(key, data, tmpl, upload_data, upload_tmpl)
        cache = self._tierc_batches if geometry else self._full_batches
        batch = cache.get(key)
        if batch is None:
            external = [b for a in (data, tmpl, starts, out)
                        if (b := shared_buffer(a, self)) is not None]
            estimate = (nd*nt*n*8 if geometry else 0) + sum(
                a.nbytes for a in (data, tmpl) if shared_buffer(a, self) is None)
            self._cache_room(estimate, incoming=external)
            pool_start = len(getattr(self, '_pools', []))
            bd = shared_buffer(data, self) or _Buffer(self, data.nbytes)
            bt = shared_buffer(tmpl, self) or _Buffer(self, tmpl.nbytes)
            if geometry:
                p1, l1, sl1 = self._build_pipeline(('tc-corr1', n),
                                                   geometry['corr1']['file'], 3, 4)
                p2, l2, sl2 = self._build_pipeline(('tc-corr-series2', n),
                                                   geometry['corr_series2']['file'], 3, 16)
                scratch = _Buffer(self, nd*nt*n*8)
                ds1 = self._descriptor_set(sl1, (bd, bt, scratch))
                ds2 = self._descriptor_set(sl2, (scratch, bs, bo), [0, 0, bo.offset])
            else:
                info = _manifest()['modules'][str(n)]
                entry = info['full_series']
                filename = ((entry.get('portable') or {}).get('file')
                            if info.get('lds_bytes', 0) > self.max_shared_memory
                            else entry['file'])
                if filename is None:
                    raise UnsupportedSize('no portable continuous kernel for n=%d' % n)
                pipe, layout, sl = self._build_pipeline(('full-series', filename),
                                                         filename, 4, 16)
                ds = self._descriptor_set(sl, (bd, bt, bs, bo), [0, 0, 0, bo.offset])
            cmd = _vp()
            ci = _CmdBufAlloc(40, None, self.command_pool, 0, 1)
            _check(self.vk.vkAllocateCommandBuffers(self.device, ctypes.byref(ci),
                                                    ctypes.byref(cmd)), 'continuous allocate')
            _check(self.vk.vkBeginCommandBuffer(cmd, ctypes.byref(
                _CmdBufBegin(42, None, 0, None))), 'continuous begin')
            params = (_u32 * 4)(nt, length, lo, hi)
            if geometry:
                self.vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, p1)
                sets = (_vp * 1)(ds1)
                self.vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, l1,
                                                0, 1, sets, 0, None)
                count = _u32(nt)
                self.vk.vkCmdPushConstants(cmd, l1, _STAGE_COMPUTE, 0, 4,
                                            ctypes.byref(count))
                self.vk.vkCmdDispatch(cmd, nd*nt*geometry['n1'], 1, 1)
                bmb = _BufMemBarrier(44, None, _ACCESS_SHADER_WRITE, _ACCESS_SHADER_READ,
                                     _QUEUE_FAMILY_IGNORED, _QUEUE_FAMILY_IGNORED,
                                     scratch.handle, 0, _WHOLE_SIZE)
                self.vk.vkCmdPipelineBarrier(cmd, _STAGE_COMPUTE_BIT, _STAGE_COMPUTE_BIT,
                                             0, 0, None, 1, ctypes.byref(bmb), 0, None)
                pipe, layout, ds = p2, l2, ds2
            self.vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, pipe)
            sets = (_vp * 1)(ds)
            self.vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, layout,
                                            0, 1, sets, 0, None)
            self.vk.vkCmdPushConstants(cmd, layout, _STAGE_COMPUTE, 0, 16,
                                        ctypes.byref(params))
            self.vk.vkCmdDispatch(cmd, nd*nt*(geometry['n2'] if geometry else 1), 1, 1)
            _check(self.vk.vkEndCommandBuffer(cmd), 'continuous end')
            batch = ((bd, bt, scratch, bs, bo, cmd) if geometry
                     else (bd, bt, bs, bo, cmd))
            cache[key] = batch
            self._register_record('tierc' if geometry else 'full', key, None, pool_start)
            uploads = (True, True, *uploads[2:])
        self._cache_touch('tierc' if geometry else 'full', key)
        bd, bt = batch[:2]
        if uploads[0]:
            write_input(bd, data)
            self._uploaded['data'][key] = uploads[2]
        if uploads[1]:
            write_input(bt, tmpl)
            self._uploaded['tmpl'][key] = uploads[3]
        self._submit(batch[-1])

    def correlate(self, n, data, tmpl, out, *, upload_data=True, upload_tmpl=True):
        """Write full correlations to caller storage with bounded GPU batches."""
        nd, nt = data.shape[0], tmpl.shape[0]
        if out.shape != (nd, nt, n):
            raise ValueError('full output shape does not match the banks')
        budget = 64 * 1024 * 1024
        per_pair = 8 * n
        tierc = n > 65536
        geom = _manifest().get('full_tierc', {}).get(str(n)) if tierc else None
        if tierc and geom is None:
            raise UnsupportedSize('no two-stage full-correlation kernel for n=%d' % n)
        groups = max(geom['n1'], geom['n2']) if tierc else 1
        fn = self._tierc_tile if tierc else self._full_tile
        direct = shared_buffer(out, self) is not None
        # Tier B writes directly to caller-owned shared output. Its size is
        # not a temporary staging budget; splitting it forces host copies of
        # every later row and defeats the point of shared output.
        working_bytes = nd*nt*per_pair*((1 if direct else 2) if tierc else (0 if direct else 1))
        if (working_bytes <= budget
                and nd * nt * groups <= self.max_dispatch_x):
            fn(n, data, tmpl, out, upload_data, upload_tmpl)
            return
        tile = min(nt, max(1, budget // (per_pair*(2 if tierc else 1))),
                   max(1, self.max_dispatch_x // groups))
        for d in range(nd):
            for t0 in range(0, nt, tile):
                t1 = min(t0 + tile, nt)
                fn(n, data[d:d+1], tmpl[t0:t1], out[d:d+1,t0:t1],
                   upload_data, upload_tmpl)

    cache_limit_recordings = 256

    def _register_record(self, kind, key, storage, pool_start):
        token = (kind, key)
        self._record_pools[token] = self._pools[pool_start:]
        if storage is not None:
            self._record_storage[token] = storage
            self._storage_users.setdefault(storage, set()).add(token)

    def _drop_storage(self, key):
        buffers = self._storage.pop(key)
        for buf in (buffers.values() if isinstance(buffers, dict) else buffers):
            buf.destroy()
        self._storage_users.pop(key, None)
        for resident in self._uploaded.values():
            resident.pop(key, None)

    def _evict_record(self, kind, key, keep_storage=None):
        # An in-flight readback reads this record's buffers when collected.
        self._drain()
        token = (kind, key)
        cache = {'flat': self._batches, 'hier': self._hier,
                 'hier_cascade': getattr(self, '_hier_cascade', {}),
                 'forward': getattr(self, '_forwards', {}),
                 'full': getattr(self, '_full_batches', {}),
                 'tierc': getattr(self, '_tierc_batches', {})}[kind]
        batch = cache.pop(key)
        cmd = batch[-1]
        getattr(self, "_phases", {}).pop(getattr(cmd, "value", cmd), None)
        pf = getattr(self, '_pending_forward', None)
        cmd_val = getattr(cmd, 'value', cmd)
        if isinstance(pf, dict):
            for s, pcmd in list(pf.items()):
                if getattr(pcmd, 'value', pcmd) == cmd_val:
                    del pf[s]
                    self._submit(cmd, slot=s)
            if not pf:
                self._pending_forward = None
        elif pf is not None and getattr(pf, 'value', pf) == cmd_val:
            self._pending_forward = None
            self._submit(cmd)
        self._wait_queues()
        commands = (_vp * 1)(cmd)
        self.vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
        self.vk.vkFreeCommandBuffers(self.device, self.command_pool, 1, commands)
        if kind in ('full', 'tierc', 'forward'):
            p_bufs = set(self._persistent_scratch.values()) if isinstance(getattr(self, '_persistent_scratch', None), dict) else set()
            for buf in batch[:-1]:
                if buf not in p_bufs and buf is not getattr(self, '_persistent_scratch', None) and not hasattr(buf, 'owner'):
                    buf.destroy()
        pools = self._record_pools.pop(token, [])
        for pool in pools:
            self.vk.vkDestroyDescriptorPool(self.device, pool, None)
        dead = {pool.value for pool in pools}
        self._pools = [pool for pool in self._pools if pool.value not in dead]
        storage = self._record_storage.pop(token, None)
        if storage is not None:
            users = self._storage_users[storage]
            users.discard(token)
            if not users and storage != keep_storage:
                self._drop_storage(storage)

    def clear_cache(self):
        """Release records and owned storage, preserving external shared arrays."""
        self._drain()
        self._submit(None)
        self._wait_queues()
        self.vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
        for kind, cache in (('flat', self._batches), ('hier', self._hier),
                            ('hier_cascade', getattr(self, '_hier_cascade', {})),
                            ('full', getattr(self, '_full_batches', {})),
                            ('tierc', getattr(self, '_tierc_batches', {})),
                            ('forward', getattr(self, '_forwards', {}))):
            for key in list(cache):
                self._evict_record(kind, key)
        # Also clean up storage/descriptors left by failed construction.
        for key in list(self._storage):
            self._drop_storage(key)
        for pool in getattr(self, '_pools', []):
            self.vk.vkDestroyDescriptorPool(self.device, pool, None)
        self._pools = []
        if getattr(self, "_persistent_scratch", None) is not None:
            if isinstance(self._persistent_scratch, dict):
                for sbuf in self._persistent_scratch.values():
                    sbuf.destroy()
                self._persistent_scratch.clear()
            else:
                self._persistent_scratch.destroy()
                self._persistent_scratch = None
        self._cache_order = {}
        self._uploaded = {"data": {}, "tmpl": {}}

    def destroy(self):
        if getattr(self, "device", None) is None:
            return
        self.clear_cache()
        vk = self.vk
        for fence in getattr(self, "_fences", {}).values():
            vk.vkDestroyFence(self.device, fence, None)
        self._fences.clear()
        if getattr(self, "_prof", None) is not None:
            vk.vkDestroyQueryPool(self.device, self._prof["pool"], None)
            self._prof = None
        if self._ts is not None:
            vk.vkFreeCommandBuffers(self.device, self.command_pool, 2 * self._TS_RING,
                                    self._ts["cmds"])
            vk.vkDestroyQueryPool(self.device, self._ts["pool"], None)
            self._ts = None
        # The device, its pipelines and command pool are shared (_Device) and live as long
        # as the process; what this context created is released above.
        self.device = None
        self.instance = None

    def __del__(self):
        """A context that goes out of scope must give the device back.

        Nothing called destroy() unless a caller did so by hand, so every
        MatchedFilter(device="gpu") that was simply dropped leaked its
        instance and device -- a few file descriptors each. A process that
        builds many then walks into RLIMIT_NOFILE, which Fedora ships at 1024.

        What makes this worth a comment is how it presents. The fd exhaustion
        surfaces as Mesa failing to create an anonymous file for its
        allocations, vkCreateInstance returning VK_ERROR_INCOMPATIBLE_DRIVER,
        and the GPU disappearing from enumeration mid-session -- so the
        machine looks like it has a broken driver, and the tests report
        dozens of failures that name everything except the cause. Measured on
        this box the suite leaked 540 descriptors across 108 tests.

        Exceptions are swallowed: this can run during interpreter shutdown,
        and a finalizer that raises there is noise nobody can act on.
        """
        try:
            self.destroy()
        except Exception:
            pass
