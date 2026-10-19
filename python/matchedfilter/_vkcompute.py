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
import time

import numpy as np

from . import _gputime, _vulkan
from ._shared import empty_shared, shared_view
from ._gpuhost import MAX_BINS

_SPIRV = pathlib.Path(__file__).resolve().parent / "spirv"


def _spv_shipped(stem, _seen={}):
    """Whether spirv/<stem>.spv is built (cached: the build set is fixed for a process)."""
    if stem not in _seen:
        _seen[stem] = (_SPIRV / (stem + ".spv")).is_file()
    return _seen[stem]

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
_MAX_BINS = MAX_BINS          # _gpuhost.MAX_BINS: one limit for every backend


def _module_bindings(blob):
    """1 + the highest descriptor binding a SPIR-V module declares (0 if none)."""
    import struct
    words = struct.unpack("<%dI" % (len(blob) // 4), blob)
    top, i = -1, 5
    while i < len(words):
        op, count = words[i] & 0xFFFF, words[i] >> 16
        if count == 0:
            break
        if op == 71 and count >= 4 and words[i + 2] == 33:      # OpDecorate Binding
            top = max(top, words[i + 3])
        i += count
    return top + 1


def _module_invocations(blob):
    """Invocations per workgroup a SPIR-V module declares (OpExecutionMode LocalSize; 0 if
    it declares none that way)."""
    import struct
    words = struct.unpack("<%dI" % (len(blob) // 4), blob)
    i = 5
    while i < len(words):
        op, count = words[i] & 0xFFFF, words[i] >> 16
        if count == 0:
            break
        if op == 16 and count >= 6 and words[i + 2] == 17:      # OpExecutionMode LocalSize
            return words[i + 3] * words[i + 4] * words[i + 5]
        i += count
    return 0


def _fit_workgroup(sg, invocations, rng, max_subgroups):
    """The subgroup size to require for a workgroup of `invocations`: sg, or -- when that
    would split the group into more subgroups than the device allows
    (maxComputeWorkgroupSubgroups; a required size past it lost the device on an Iris Xe at
    8 for the 1024-invocation transforms) -- the smallest size in range that does not."""
    if not max_subgroups or not invocations or -(-invocations // sg) <= max_subgroups:
        return sg
    for s in (4, 8, 16, 32, 64, 128):
        if s > sg and rng[0] <= s <= rng[1] and -(-invocations // s) <= max_subgroups:
            return s
    return sg


from ._coarse import coarse_stem, shipped_tiles, forced_tile   # noqa: E402


#: Byte offsets into VkPhysicalDeviceProperties. The 5 leading uint32s, the
#: 256-byte name and the 16-byte UUID come to 292, padded to 296 because
#: VkPhysicalDeviceLimits contains 64-bit members; maxComputeSharedMemorySize
#: sits 216 bytes into those limits.
_OFF_SHARED_MEMORY = 296 + 216
_OFF_MAX_INVOCATIONS = 296 + 232
#: timestampPeriod (float, ns per tick) sits 424 bytes into the limits.
_OFF_TIMESTAMP_PERIOD = 296 + 424
#: maxComputeWorkGroupSize[3] (uint32) sits 236 bytes into the limits, and
#: minStorageBufferOffsetAlignment (VkDeviceSize) 328.
_OFF_MAX_WORKGROUP_SIZE = 296 + 236
_OFF_STORAGE_OFFSET_ALIGNMENT = 296 + 328


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
_SIMULTANEOUS_USE = 0x4    # VK_COMMAND_BUFFER_USAGE_SIMULTANEOUS_USE_BIT
#: Zeroing recordings a context keeps (one per distinct set of ranges: a middle stage has one
#: per output buffer and detector).
_ZERO_RECS = 8
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
#: VK_EXT_subgroup_size_control (core in 1.3; this instance asks for 1.1).
_SSC_EXT = b"VK_EXT_subgroup_size_control"
_SSCFeatures = _struct("VkPhysicalDeviceSubgroupSizeControlFeatures",
                       ("sType", _u32), ("pNext", _vp),
                       ("subgroupSizeControl", _u32), ("computeFullSubgroups", _u32))
_SSCProperties = _struct("VkPhysicalDeviceSubgroupSizeControlProperties",
                         ("sType", _u32), ("pNext", _vp),
                         ("minSubgroupSize", _u32), ("maxSubgroupSize", _u32),
                         ("maxComputeWorkgroupSubgroups", _u32),
                         ("requiredSubgroupSizeStages", _u32))
_StageRequiredSize = _struct("VkPipelineShaderStageRequiredSubgroupSizeCreateInfo",
                             ("sType", _u32), ("pNext", _vp), ("requiredSubgroupSize", _u32))
#: VK_EXT_host_query_reset (core in 1.2): timestamp queries reset from the host when a
#: slot is handed out, so a read that waits really waits for this use's write.
_HQR_EXT = b"VK_EXT_host_query_reset"
_HQRFeatures = _struct("VkPhysicalDeviceHostQueryResetFeatures",
                       ("sType", _u32), ("pNext", _vp), ("hostQueryReset", _u32))
_Features2 = _struct("VkPhysicalDeviceFeatures2", ("sType", _u32), ("pNext", _vp),
                     ("features", ctypes.c_ubyte * 256))
_ExtProps = _struct("VkExtensionProperties", ("extensionName", ctypes.c_char * 256),
                    ("specVersion", _u32))
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
from ._gpuexec import Arg, Executor


class VulkanError(RuntimeError):
    pass


def _check(rc, what):
    if rc != 0:
        raise VulkanError("%s failed with VkResult %d" % (what, rc))


def _global_barrier(vk, cmd):
    """All earlier compute/transfer work before all later work, memory included."""
    mb = _MemBarrier(46, None, _ACCESS_SHADER_WRITE | _ACCESS_TRANSFER_WRITE | _ACCESS_SHADER_READ,
                     _ACCESS_SHADER_READ | _ACCESS_SHADER_WRITE | _ACCESS_TRANSFER_WRITE
                     | _ACCESS_HOST_READ)
    vk.vkCmdPipelineBarrier(cmd, _STAGE_COMPUTE_BIT | _STAGE_TRANSFER_BIT,
                            _STAGE_COMPUTE_BIT | _STAGE_TRANSFER_BIT | _STAGE_HOST_BIT,
                            0, 1, ctypes.byref(mb), 0, None, 0, None)


class _Recording:
    """A primary command buffer being recorded: allocated from the context's pool and begun
    with `flags` (a VkCommandBufferUsageFlags), with the steps every recording repeats.
    end() finishes it and returns the handle; `cmd` takes any other command."""

    def __init__(self, ctx, what, flags=0):
        self.vk, self.ctx, self.what = ctx.vk, ctx, what
        self.cmd = _vp()
        _check(self.vk.vkAllocateCommandBuffers(ctx.device, ctypes.byref(
            _CmdBufAlloc(40, None, ctx.command_pool, 0, 1)), ctypes.byref(self.cmd)),
            what + " allocate")
        _check(self.vk.vkBeginCommandBuffer(self.cmd, ctypes.byref(
            _CmdBufBegin(42, None, flags, None))), what + " begin")

    def bind(self, pipe, ds, words=(), size=None):
        """Bind pipe, a (pipeline, layout, set layout) triple, with descriptor set ds, and
        push `words` (uint32; negative values as their two's complement) as `size` bytes
        (4 per word by default)."""
        vk, cmd = self.vk, self.cmd
        vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, pipe[0])
        vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, pipe[1], 0, 1, (_vp * 1)(ds),
                                   0, None)
        if words:
            pc = (ctypes.c_uint32 * len(words))(*(int(w) & 0xFFFFFFFF for w in words))
            vk.vkCmdPushConstants(cmd, pipe[1], _STAGE_COMPUTE, 0, size or 4 * len(words),
                                  ctypes.byref(pc))

    def dispatch(self, groups):
        self.vk.vkCmdDispatch(self.cmd, groups, 1, 1)

    def dispatch_indirect(self, buf):
        self.vk.vkCmdDispatchIndirect(self.cmd, buf.handle, getattr(buf, "offset", 0))

    def barrier(self, src_stage=_STAGE_COMPUTE_BIT, dst_stage=_STAGE_COMPUTE_BIT,
                src_access=_ACCESS_SHADER_WRITE, dst_access=_ACCESS_SHADER_READ, buffer=None):
        """A memory barrier, or one on `buffer` alone (its whole range)."""
        if buffer is None:
            mb = _MemBarrier(46, None, src_access, dst_access)
            self.vk.vkCmdPipelineBarrier(self.cmd, src_stage, dst_stage, 0, 1,
                                         ctypes.byref(mb), 0, None, 0, None)
        else:
            bmb = _BufMemBarrier(44, None, src_access, dst_access, _QUEUE_FAMILY_IGNORED,
                                 _QUEUE_FAMILY_IGNORED, buffer.handle, 0, _WHOLE_SIZE)
            self.vk.vkCmdPipelineBarrier(self.cmd, src_stage, dst_stage, 0, 0, None, 1,
                                         ctypes.byref(bmb), 0, None)

    def stamp(self, name):
        self.ctx._stamp(self.cmd, name)

    def end(self):
        _check(self.vk.vkEndCommandBuffer(self.cmd), self.what + " end")
        return self.cmd


class _Buffer:
    """A storage buffer plus its memory, mapped for the lifetime of the object.

    Host-visible throughout, with DEVICE_LOCAL preferred when the driver
    offers it.  On an integrated GPU that combination is the whole of memory,
    so this is not a compromise; on a discrete card it is, and a staging copy
    will be needed there -- deliberately not written until there is a discrete
    card to measure it on, because an unmeasured transfer path is exactly the
    kind of code that looks right and halves throughput.
    """

    #: Slotted: a search holds thousands, and every full garbage collection walks them.
    __slots__ = ("ctx", "nbytes", "handle", "memory", "ptr", "_bytes")

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
        """The first count elements, in place (valid while the buffer lives). The bytes are
        wrapped once: a result reads several views per call."""
        raw = getattr(self, "_bytes", None)
        if raw is None:
            raw = self._bytes = np.frombuffer((ctypes.c_char * self.nbytes).from_address(
                int(self.ptr.value if hasattr(self.ptr, 'value') else self.ptr)), np.uint8)
        return raw[:count * np.dtype(dtype).itemsize].view(dtype)

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


class _Section:
    """Bytes [offset, offset + nbytes) of a _Buffer (Context._x_section)."""
    __slots__ = ("base", "handle", "offset", "nbytes", "ptr")

    def __init__(self, base, offset, nbytes):
        self.base, self.handle, self.offset, self.nbytes = base, base.handle, offset, nbytes
        ptr = base.ptr.value if hasattr(base.ptr, "value") else base.ptr
        self.ptr = ptr + offset

    def write(self, array):
        flat = np.ascontiguousarray(array)
        ctypes.memmove(self.ptr, flat.ctypes.data, min(flat.nbytes, self.nbytes))

    def view(self, dtype, count):
        dtype = np.dtype(dtype)
        return self.base.view(np.uint8, self.offset + count * dtype.itemsize)[self.offset:].view(dtype)

    def destroy(self):
        pass                                    # the base buffer owns the memory


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
#: A phase is ONE step of each recording: a fused batch emits every item's work for a phase
#: and then their barriers, so a recording's barrier only separates its phases. Steps that
#: depend on each other within a call (marking survivor blocks, then recomputing them) are
#: therefore separate phases.
_FUSED_PHASES = ("forward", "fill", "pack", "coarse0", "compact0", "coarse1", "compact1",
                 "mark", "recompute", "refine", "peaks")

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


#: Interleave depths a fused batch is timed at: 0 is lockstep; 3 puts the second half's
#: forward (DRAM-bound) beside the first half's coarse0 (VALU-bound).
_INTERLEAVE_CANDIDATES = (0, 3)
#: Timed submissions per candidate before a batch shape's depth is first judged, and the most
#: an unclear contest takes before lockstep (the model's depth) stands
#: (gatechain.measured_choice).
_INTERLEAVE_TRIALS = 5
_INTERLEAVE_TRIALS_MAX = 10


def _interleave_key(dev, shape):
    from . import gatechain
    return "vk-interleave|%s|%r|k%s" % (getattr(dev, "index", 0), shape, gatechain.gpu_kernel_id())


def _batch_shape(items):
    """(shape, work) of a fused batch: the multiset of phase sets its items carry, and its
    coarse work (workgroups dispatched in coarse0, at least 1) to normalise a timing."""
    sig, work = [], 1
    for ctx, cmds in items:
        names = []
        for h in cmds:
            ph = ctx._phases[h]
            names.extend(n for n in _FUSED_PHASES if n in ph)
            for name, args in (ph.get("coarse0") or ((), ()))[0]:
                if name == "vkCmdDispatch":
                    work += int(getattr(args[1], "value", args[1]))
        sig.append(tuple(names))
    return (len(items) > 1, tuple(sorted(set(sig)))), work


def _fuse_interleave():
    """A forced interleave depth (MF_GPU_FUSE_INTERLEAVE), or None: measured per batch."""
    v = os.environ.get("MF_GPU_FUSE_INTERLEAVE")
    if v is not None and v != "":
        return max(0, int(v))
    return None


class _DeviceTimer:
    """Timestamps around whole submissions on one device, independent of MF_GPU_TIMING:
    used to choose a fused batch's interleave depth by measurement."""
    RING = 64

    def __init__(self, dev):
        vk = dev.vk
        for name, args in (("vkCmdWriteTimestamp", [_vp, _u32, _vp, _u32]),
                           ("vkCmdResetQueryPool", [_vp, _vp, _u32, _u32]),
                           ("vkGetQueryPoolResults", [_vp, _vp, _u32, _u32, ctypes.c_size_t, _vp,
                                                      ctypes.c_uint64, _u32])):
            getattr(vk, name).argtypes = args
        self.dev = dev
        self.pool = _vp()
        _check(vk.vkCreateQueryPool(dev.device, ctypes.byref(
            _QueryPoolCreate(11, None, 0, 2, 2 * self.RING, 0)), None, ctypes.byref(self.pool)),
            "timer pool")
        self.cmds = (_vp * (2 * self.RING))()
        _check(vk.vkAllocateCommandBuffers(dev.device, ctypes.byref(
            _CmdBufAlloc(40, None, dev.command_pool, 0, 2 * self.RING)), self.cmds), "timer cmds")
        for i in range(self.RING):
            b, e = _vp(self.cmds[2 * i]), _vp(self.cmds[2 * i + 1])
            begin = _CmdBufBegin(42, None, 0, None)
            _check(vk.vkBeginCommandBuffer(b, ctypes.byref(begin)), "timer b")
            vk.vkCmdResetQueryPool(b, self.pool, 2 * i, 2)
            vk.vkCmdWriteTimestamp(b, 0x1, self.pool, 2 * i)
            _check(vk.vkEndCommandBuffer(b), "timer b end")
            _check(vk.vkBeginCommandBuffer(e, ctypes.byref(begin)), "timer e")
            vk.vkCmdWriteTimestamp(e, 0x2000, self.pool, 2 * i + 1)
            _check(vk.vkEndCommandBuffer(e), "timer e end")
        self.next = 0

    def pair(self):
        i = self.next
        self.next = (i + 1) % self.RING
        return i, _vp(self.cmds[2 * i]), _vp(self.cmds[2 * i + 1])

    def ns(self, i, period):
        out = (ctypes.c_uint64 * 2)()
        _check(self.dev.vk.vkGetQueryPoolResults(self.dev.device, self.pool, 2 * i, 2, 16, out, 8,
                                                 0x3), "timer read")
        return (out[1] - out[0]) * period


class _FusedBatch:
    """Submissions collected across contexts on one device, recorded and submitted together."""

    def __init__(self, dev):
        self.dev, self.items, self.state = dev, [], "open"
        self.trial = None

    #: Submissions per fused command buffer. The device starts on a chunk while the host
    #: prepares the next: fusing a whole segment into one buffer left the GPU idle through
    #: all the host's preparation.
    chunk = 16

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
        base = _fused_key(self.items)
        # The interleave depth is a MEASURED choice, per device and batch SHAPE (the
        # phases its items carry): the first batches of a shape take the candidates in a
        # random order under device timestamps, each time normalised by the batch's
        # coarse work, and the lower median is kept from then on. So it turns on where the
        # forward is DRAM-bound (full clock, other GPUs) and stays off where it is not.
        # Batches rarely recur exactly (a chunk's composition varies), so a per-batch
        # trial would seldom finish; the shape is what decides whether overlap can pay.
        forced = _fuse_interleave()
        choice = dev.__dict__.setdefault("interleave_choice", {})
        if forced is not None or len(self.items) < 2:
            k = forced or 0
        else:
            shape, work = _batch_shape(self.items)
            st = choice.get(shape)
            if st is None:
                # a depth this machine already measured for the shape is reused untimed
                from . import gatechain
                held = gatechain.stored_choice(_interleave_key(dev, shape))
                st = choice[shape] = {"k": held if held in _INTERLEAVE_CANDIDATES else None,
                                      "t": {c: [] for c in _INTERLEAVE_CANDIDATES},
                                      "need": {c: _INTERLEAVE_TRIALS
                                               for c in _INTERLEAVE_CANDIDATES}}
            if st["k"] is not None:
                k = st["k"]
            else:
                pending = [c for c in _INTERLEAVE_CANDIDATES
                           if len(st["t"][c]) < st["need"][c]] or list(_INTERLEAVE_CANDIDATES)
                k = pending[int.from_bytes(os.urandom(1), "little") % len(pending)]
                self.trial = (shape, k, work)
        key = (base, k)
        cache = dev.__dict__.setdefault("fused_cache", OrderedDict())
        hit = cache.get(key)
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
        # Phases run in lockstep across the batch's items, one global barrier per phase.
        # With an interleave offset k the batch's second half runs k phases behind its
        # first: forward (DRAM-bound) of one half then shares a barrier interval with
        # coarse0 (VALU-bound) of the other, so the two overlap on the device. Every item
        # still sees its own phases in order, each behind its own recorded barriers.
        P = _FUSED_PHASES
        half = (len(self.items) + 1) // 2
        groups = ((self.items[:half], 0), (self.items[half:], k)) if k else ((self.items, 0),)
        for step in range(len(P) + k):
            barriers = []
            labels = []
            for items, lag in groups:
                i = step - lag
                if not 0 <= i < len(P):
                    continue
                phase = P[i]
                labels.append(phase)
                for ctx, cmds in items:
                    for h in cmds:
                        work_bar = ctx._phases[h].get(phase)
                        if work_bar is None:
                            continue
                        work, bar = work_bar
                        for name, args in work:
                            getattr(vk, name)(cmd, *args[1:])
                        barriers.extend(bar)
            # One global barrier per distinct (stages, access) is enough for the step;
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
                prof._stamp(cmd, "fused " + ("+".join(labels) if k else labels[0]))
        _check(vk.vkEndCommandBuffer(cmd), "end fused")
        self.prof = prof
        cache[key] = (cmd, [list(cmds) for _, cmds in self.items])
        while len(cache) > 64:
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
        if self.trial is not None:
            timer = dev.__dict__.get("fuse_timer")
            if timer is None:
                timer = dev.fuse_timer = _DeviceTimer(dev)
            slot, begin, end = timer.pair()
            self.trial = self.trial + (slot,)
            cmds = (_vp * 3)(begin, cmd, end)
            submit = _SubmitInfo(4, None, 0, None, None, 3, cmds, 0, None)
        elif timed is not None:
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
        if self.trial is not None and len(self.trial) == 4:
            shape, k, work, slot = self.trial
            st = dev.__dict__.get("interleave_choice", {}).get(shape)
            if st is not None and st["k"] is None:
                st["t"][k].append(dev.fuse_timer.ns(slot, dev._ts_period) / work)
                if all(len(v) >= st["need"][c] for c, v in st["t"].items()):
                    # The shared rule (gatechain.measured_choice): lockstep (0) stands unless
                    # a deeper interleave is faster past TIE and the noise -- the timings
                    # carry clock and content noise, and a coin flip between two equal
                    # choices only adds a barrier per phase. Unclear: sample both further.
                    from . import gatechain
                    w, more = gatechain.measured_choice(st["t"], 0, _INTERLEAVE_TRIALS_MAX)
                    if w is None:
                        st["need"].update(more)
                    else:
                        st["k"] = w
                        gatechain.store_choice(_interleave_key(dev, shape), int(w))
                    # The losers' recordings are never submitted again; the cache's LRU
                    # retires them (another batch may still be executing one now).


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


#: One _Device per Vulkan device index, for the life of the process.
_DEVICES = {}

#: Live contexts by id(), for validating cached fused recordings (keys hold ids).
import weakref as _weakref
_CONTEXTS_BY_ID = _weakref.WeakValueDictionary()


def settle_all():
    """Wait for every write left in flight on any Vulkan device (a host read follows)."""
    for dev in list(_DEVICES.values()):
        while dev.pending_writes:
            fence = dev.pending_writes.pop(0)
            _check(dev.vk.vkWaitForFences(dev.device, 1, (_vp * 1)(fence), 1,
                                          0xFFFFFFFFFFFFFFFF), "vkWaitForFences")
            dev.vk.vkDestroyFence(dev.device, fence, None)


class _Device:
    """A Vulkan instance and logical device, its compute queues, command pool and pipelines."""

    def __init__(self, index):
        self.index = index
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
        # Fences of writes left in flight (correlate_series(wait=False)): device consumers on
        # the main queue are ordered by the barriers those recordings carry; anything else
        # (another queue, a host write to their inputs, a host read) waits here first.
        self.pending_writes = []
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
        # Pin the subgroup size where the device lets us (VK_EXT_subgroup_size_control):
        # the kernels are specialized on it (constant 74), and RADV may otherwise pick
        # wave32 or wave64 per pipeline.
        ssc_feat, ext_names = self._subgroup_control_features()
        dci = _DeviceCreate(3, ctypes.cast(ctypes.pointer(ssc_feat), _vp) if ssc_feat else None,
                            0, 1, ctypes.pointer(qci), 0, None,
                            len(ext_names) if ext_names else 0,
                            ctypes.cast(ext_names, _vp) if ext_names else None, None)
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
        # Host query reset: a timestamp slot handed out again is made unavailable on the
        # host first, so a waiting read cannot return a value that is not this use's.
        self._reset_query = None
        if getattr(self, "host_query_reset", False):
            vk.vkGetDeviceProcAddr.argtypes = [_vp, ctypes.c_char_p]
            vk.vkGetDeviceProcAddr.restype = _vp
            fn = vk.vkGetDeviceProcAddr(self.device, b"vkResetQueryPoolEXT")
            if fn:
                self._reset_query = ctypes.CFUNCTYPE(None, _vp, _vp, _u32, _u32)(fn)

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
        # deviceName follows the five leading uint32s: it keys this device's measured choices.
        self.device_name = bytes(props[20:276]).split(b"\0")[0].decode("utf-8", "replace")
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

        # Descriptor offsets into a storage buffer must be multiples of this. 256 is the
        # largest the spec allows (AMD), NVIDIA reports 16-64; packing sub-results at the
        # device's own alignment instead of 256 keeps the readback dense where it can be.
        align = int(ctypes.cast(ctypes.byref(props, _OFF_STORAGE_OFFSET_ALIGNMENT),
                                ctypes.POINTER(_u64))[0])
        self.storage_offset_alignment = align if 0 < align <= 256 and align & (align - 1) == 0 \
            else 256
        self.max_workgroup_size = tuple(int(v) for v in ctypes.cast(
            ctypes.byref(props, _OFF_MAX_WORKGROUP_SIZE), ctypes.POINTER(_u32 * 3))[0])

        self.subgroup_size = 32
        self.subgroup_range = None          # (min, max) when the size can be required
        self.max_workgroup_subgroups = 0    # maxComputeWorkgroupSubgroups (0: unknown)
        try:
            if hasattr(vk, "vkGetPhysicalDeviceProperties2"):
                ssc_props = _SSCProperties(1000225000, None, 0, 0, 0, 0)
                sub_props = _SubgroupProperties(
                    1000094000, ctypes.cast(ctypes.pointer(ssc_props), _vp)
                    if getattr(self, "subgroup_control", False) else None,
                    0, 0, 0, 0)
                props2 = _PhysicalDeviceProperties2(
                    1000059001,
                    ctypes.cast(ctypes.pointer(sub_props), _vp),
                    (ctypes.c_ubyte * 2048)()
                )
                vk.vkGetPhysicalDeviceProperties2.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
                vk.vkGetPhysicalDeviceProperties2.restype = None
                vk.vkGetPhysicalDeviceProperties2(self.physical, ctypes.byref(props2))
                if sub_props.subgroupSize > 0:
                    self.subgroup_size = int(sub_props.subgroupSize)
                if getattr(self, "subgroup_control", False) \
                        and ssc_props.requiredSubgroupSizeStages & _STAGE_COMPUTE \
                        and ssc_props.minSubgroupSize <= self.subgroup_size <= ssc_props.maxSubgroupSize:
                    self.subgroup_range = (int(ssc_props.minSubgroupSize),
                                           int(ssc_props.maxSubgroupSize))
                    self.max_workgroup_subgroups = int(ssc_props.maxComputeWorkgroupSubgroups)
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

    def _subgroup_control_features(self):
        """(feature chain head, extension-name array) enabling the device extensions used:
        subgroup size control and host query reset, each where the device offers it; or
        (None, None)."""
        vk = self.vk
        try:
            if not hasattr(vk, "vkGetPhysicalDeviceFeatures2"):
                return None, None
            vk.vkEnumerateDeviceExtensionProperties.argtypes = [_vp, _vp, ctypes.POINTER(_u32), _vp]
            n = _u32()
            vk.vkEnumerateDeviceExtensionProperties(self.physical, None, ctypes.byref(n), None)
            exts = (_ExtProps * n.value)()
            vk.vkEnumerateDeviceExtensionProperties(self.physical, None, ctypes.byref(n), exts)
            have = {e.extensionName for e in exts}
            ssc = _SSCFeatures(1000225002, None, 0, 0)
            hqr = _HQRFeatures(1000261000, None, 0)
            ssc.pNext = ctypes.cast(ctypes.pointer(hqr), _vp)
            f2 = _Features2(1000059000, ctypes.cast(ctypes.pointer(ssc), _vp), (ctypes.c_ubyte * 256)())
            vk.vkGetPhysicalDeviceFeatures2.argtypes = [_vp, _vp]
            vk.vkGetPhysicalDeviceFeatures2.restype = None
            vk.vkGetPhysicalDeviceFeatures2(self.physical, ctypes.byref(f2))
            names, chain = [], []
            if _SSC_EXT in have and ssc.subgroupSizeControl:
                ssc.computeFullSubgroups = 0
                names.append(_SSC_EXT); chain.append(ssc)
            if _HQR_EXT in have and hqr.hostQueryReset:
                names.append(_HQR_EXT); chain.append(hqr)
            self.host_query_reset = _HQR_EXT in names
            if not chain:
                return None, None
            for a, b in zip(chain, chain[1:]):
                a.pNext = ctypes.cast(ctypes.pointer(b), _vp)
            chain[-1].pNext = None
            self._ssc_keep = (chain[0], (ctypes.c_char_p * len(names))(*names), chain)
            self.subgroup_control = _SSC_EXT in names
            return self._ssc_keep[:2]
        except Exception:
            return None, None

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
                self.timestamp_bits = int(fam.timestampValidBits)
                return i, fam.queueCount
        for i, fam in enumerate(families):
            if fam.queueFlags & _QUEUE_COMPUTE:
                self.timestamp_bits = int(fam.timestampValidBits)
                return i, fam.queueCount
        raise VulkanError("device exposes no compute queue")


def _list_barrier(vk, cmd):
    """A list's barrier (_gpuexec): every earlier compute or transfer write before every later
    compute, transfer, indirect-argument or host access. Indirect fetch is in the scope: an
    indirect dispatch reads a count a shader just wrote (missing it, Intel used the previous
    dispatch's count)."""
    mb = _MemBarrier(46, None, _ACCESS_SHADER_WRITE | _ACCESS_TRANSFER_WRITE,
                     _ACCESS_SHADER_READ | _ACCESS_SHADER_WRITE | _ACCESS_TRANSFER_WRITE
                     | _ACCESS_INDIRECT_READ | _ACCESS_HOST_READ)
    vk.vkCmdPipelineBarrier(cmd, _STAGE_COMPUTE_BIT | _STAGE_TRANSFER_BIT,
                            _STAGE_COMPUTE_BIT | _STAGE_TRANSFER_BIT | _STAGE_HOST_BIT
                            | _STAGE_DRAW_INDIRECT_BIT, 0, 1, ctypes.byref(mb), 0, None, 0, None)


def _flat_words(words, binds=None):
    out = []
    for w in words:
        if isinstance(w, Arg):
            out.extend(binds[w.name] if binds is not None else (w,))
        elif isinstance(w, tuple):
            out.extend(w)
        else:
            out.append(w)
    return out


class _VkList:
    """A command list being recorded (_gpuexec's driver interface). Descriptor sets and push
    constants are fixed in a command buffer, so the list is kept as its operations and
    recorded once per binding of its Args (_VkNative)."""

    def __init__(self, ctx, label, once=False):
        self.ctx, self.label, self.once, self.ops = ctx, label, once, []

    def dispatch(self, kernel, groups, buffers, words=(), offsets=None):
        self.ops.append(("dispatch", kernel, int(groups), list(buffers), offsets, list(words)))

    def listed(self, kernel, count, max_groups, buffers, words=(), offsets=None):
        # Indirect, sized by the count a shader wrote; the bounded kernel's gridSize word is
        # the upper bound, so each group takes one item.
        self.ops.append(("listed", kernel, count, list(buffers), offsets,
                         list(words) + [int(max_groups)]))

    def barrier(self):
        self.ops.append(("barrier",))

    def stamp(self, name):
        self.ops.append(("stamp", name))

    def fill(self, buf, word):
        self.ops.append(("fill", buf, int(word) & 0xFFFFFFFF))

    def update(self, buf, words):
        # vkCmdUpdateBuffer reads its data when recorded -- and again whenever a fused batch
        # re-records a captured call -- so the words live as long as the list.
        data = (ctypes.c_uint32 * len(words))(*[int(w) & 0xFFFFFFFF for w in words])
        self.ops.append(("update", buf, data))

    def readback(self, buf, nbytes):
        pass                        # host-visible memory: the host reads it after the run

    def end(self):
        return _VkNative(self.ctx, self.label, self.ops, self.once)


class _VkNative:
    """A recorded list: a command buffer per binding of its Args (just one without Args),
    the most recently used _BINDINGS kept, each holding the views it binds so no allocation
    can be freed and its handle reused under it. Past _BINDINGS, a run that is waited for
    records a one-off command buffer instead (a stream of new search windows), freed when
    it has finished: evicting a cached one would idle every queue. A `once` list (follow-up
    items) is recorded for its one run and freed when that run has finished."""
    _BINDINGS = 8

    def __init__(self, ctx, label, ops, once=False):
        self.ctx, self.label, self.ops, self.once = ctx, label, ops, once
        names = set()
        for op in ops:
            if op[0] in ("dispatch", "listed"):
                names.update(b.name for b in op[3] if isinstance(b, Arg))
                names.update(w.name for w in op[5] if isinstance(w, Arg))
        self.args = sorted(names)
        # A list with phase stamps is captured, so fused batches can interleave it.
        self.captured = any(op[0] == "stamp" for op in ops)
        self.cmds = {}                       # binding key -> (cmd, pools, held values)

    @staticmethod
    def _key(value):
        return (id(value.owner), value.offset) if hasattr(value, "owner") else value

    def command(self, binds, transient=False):
        """(command buffer, release): release() frees a one-off one once its run finished
        (None for a cached one)."""
        values = tuple(binds[name] for name in self.args)
        if self.once:
            cmd, pools = self.record(dict(zip(self.args, values)))
            return cmd, lambda: self.free(cmd, pools)
        key = tuple(self._key(v) for v in values)
        entry = self.cmds.pop(key, None)
        if entry is None:
            if transient and len(self.cmds) >= self._BINDINGS:
                cmd, pools = self.record(dict(zip(self.args, values)))
                return cmd, lambda: self.free(cmd, pools)
            if len(self.cmds) >= self._BINDINGS:
                self.release_one(next(iter(self.cmds)))
            entry = self.record(dict(zip(self.args, values))) + (values,)
        self.cmds[key] = entry               # most recently used last
        return entry[0], None

    def record(self, binds):
        ctx = self.ctx
        pool_start = len(getattr(ctx, "_pools", []))
        if self.captured:
            ctx._capture_begin()
        cmd = None
        try:
            rec = _Recording(ctx, self.label, flags=1 if self.once else 0)
            cmd = rec.cmd
            self._emit(rec, binds)
            rec.end()
        finally:
            if self.captured:
                ctx._capture_end(cmd)
        pools = list(getattr(ctx, "_pools", [])[pool_start:])
        return cmd, pools

    def _emit(self, rec, binds):
        ctx = self.ctx
        for op in self.ops:
            kind = op[0]
            if kind == "barrier":
                _list_barrier(ctx.vk, rec.cmd)
            elif kind == "stamp":
                rec.stamp(op[1])
            elif kind == "fill":
                ctx.vk.vkCmdFillBuffer(rec.cmd, op[1].handle, getattr(op[1], "offset", 0),
                                       _WHOLE_SIZE, op[2])
            elif kind == "update":
                ctx.vk.vkCmdUpdateBuffer(rec.cmd, op[1].handle, getattr(op[1], "offset", 0),
                                         ctypes.sizeof(op[2]), ctypes.addressof(op[2]))
            else:
                _, kernel, groups, buffers, offsets, words = op
                bound = [binds[b.name] if isinstance(b, Arg) else b for b in buffers]
                offs = [getattr(b, "offset", 0) + (offsets[i] if offsets else 0)
                        for i, b in enumerate(bound)]
                ds = ctx._descriptor_set(kernel[2], bound, offs if any(offs) else None)
                rec.bind(kernel, ds, [int(w) & 0xFFFFFFFF for w in _flat_words(words, binds)])
                if kind == "dispatch":
                    rec.dispatch(groups)
                else:
                    rec.dispatch_indirect(groups)

    def free(self, cmd, pools):
        ctx = self.ctx
        getattr(ctx, "_phases", {}).pop(getattr(cmd, "value", cmd), None)
        ctx.vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
        ctx.vk.vkFreeCommandBuffers(ctx.device, ctx.command_pool, 1, (_vp * 1)(cmd))
        dead = {pool.value for pool in pools}
        for pool in pools:
            ctx.vk.vkDestroyDescriptorPool(ctx.device, pool, None)
        ctx._pools = [pool for pool in getattr(ctx, "_pools", []) if pool.value not in dead]

    def release_one(self, key, done=False):
        cmd, pools, _ = self.cmds.pop(key)
        if not done:
            self.ctx._wait_queues()
        self.free(cmd, pools)

    def release(self, done=False):
        if self.cmds and not done:
            self.ctx._wait_queues()
        for key in list(self.cmds):
            self.release_one(key, done=True)


class Context(Executor, InputUploads):
    """One Vulkan device, its compute queue, and the pipelines built on it: the Vulkan driver
    under the shared GPU executor (_gpuexec)."""

    max_grouped_bins = _MAX_BINS

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
        self._fences = {}
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
               "_accurate_trig", "device_name", "max_shared_memory", "max_invocations", "max_dispatch_x",
               "subgroup_size", "subgroup_range", "max_workgroup_subgroups", "mem_props", "command_pool", "_ts_period",
               "_reset_query",
               "storage_offset_alignment", "max_workgroup_size", "timestamp_bits")

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

    def _build_pipeline(self, key, filename, nbind, push_bytes, data_stride=0, row_windows=0,
                        subgroup=0, data_scale=0, coarse_twt=None):
        """data_stride: specialization constant 75 (mfDataStride), the data spectra's row
        stride when a hierarchical stage reads its band straight out of them.
        row_windows: constant 76 (mfRowWindows), per-row windows from the gRowWin binding.

        The set layout covers every binding the MODULE declares, which can exceed the
        caller's count (gRowWin); _descriptor_set fills such trailing bindings with a
        dummy buffer."""
        if data_stride or row_windows:
            key = (key, "stride", data_stride, "rowwin", row_windows)
        if data_scale:
            key = (key, "dscale", int(data_scale))
        if coarse_twt is not None:
            key = (key, "twt", int(coarse_twt))
        raw_c16 = os.environ.get("MF_VK_C16_BOUND", "1") == "0"
        if raw_c16:
            key = (key, "raw-c16")
        # subgroup: a size within the device's required-size range to build this pipeline
        # at instead of the default (specialization constant 74 follows it).
        rng = getattr(self, "subgroup_range", None)
        if not subgroup and rng:
            # MF_VK_SUBGROUP=size[:prefix,prefix...]: build every pipeline that does not
            # choose its own -- or only those whose SPIR-V file starts with one of the
            # prefixes (forward, tierb, refine, items, compact, full, corr, ...) -- at this
            # size (within the device's range), for measurement: e.g. an Intel GPU's 8 or 16
            # against the 32 it reports.
            spec = os.environ.get("MF_VK_SUBGROUP", "") or ""
            size, _, roles = spec.partition(":")
            forced = int(size or 0)
            pick = not roles or any(str(filename).startswith(r) for r in roles.split(",") if r)
            if forced:
                if pick and rng[0] <= forced <= rng[1] and forced != self.subgroup_size:
                    subgroup = forced
            else:
                # Otherwise this device's measured size (_vksubgroup.choose), once per device.
                ds = self._device_state
                chosen = ds.__dict__.get("pipeline_subgroup")
                if chosen is None:
                    from . import _vksubgroup
                    chosen = ds.pipeline_subgroup = _vksubgroup.choose(self)
                if chosen != self.subgroup_size and rng[0] <= chosen <= rng[1]:
                    subgroup = chosen
        if subgroup and not (rng and rng[0] <= subgroup <= rng[1]):
            raise VulkanError("subgroup size %d cannot be required here" % subgroup)
        sg = int(subgroup or self.subgroup_size)
        if rng:
            # Never more subgroups per workgroup than the device allows.
            sg = _fit_workgroup(sg, self._invocations(filename), rng,
                                getattr(self, "max_workgroup_subgroups", 0))
            subgroup = 0 if sg == self.subgroup_size else sg
        if subgroup:
            key = (key, "subgroup", sg)
        if key in self._pipelines:
            return self._pipelines[key]
        vk = self.vk
        blob = (_SPIRV / filename).read_bytes()
        nbind = max(nbind, _module_bindings(blob))
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
        self._device_state.__dict__.setdefault("layout_nbind", {})[set_layout.value] = nbind

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
        data_vals.append(sg)
        offset += 4
        if data_stride:
            entries.append(_SpecializationEntry(75, offset, 4))
            data_vals.append(int(data_stride))
            offset += 4
        if row_windows:
            entries.append(_SpecializationEntry(76, offset, 4))
            data_vals.append(int(row_windows))
            offset += 4
        if data_scale:
            # The fp16 coarse tier's data scale 2^data_scale, as float bits (constant 79).
            entries.append(_SpecializationEntry(79, offset, 4))
            data_vals.append(int(np.float32(2.0 ** int(data_scale)).view(np.uint32)))
            offset += 4
        if coarse_twt is not None:
            # The untiled coarse transform's twiddles: table (1) or recurrence (0), constant 80.
            entries.append(_SpecializationEntry(80, offset, 4))
            data_vals.append(int(coarse_twt))
            offset += 4
        if raw_c16:
            # Raw fp16 coarse maxima, for measuring the error bound's margin use only.
            entries.append(_SpecializationEntry(77, offset, 4))
            data_vals.append(0)
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
        req = None
        if getattr(self, "subgroup_range", None):
            # The size the kernels are specialized on (constant 74), required, not hoped for.
            req = _StageRequiredSize(1000225001, None, sg)
        stage = _StageCreate(18, ctypes.cast(ctypes.pointer(req), _vp) if req else None,
                             0, _STAGE_COMPUTE, module,
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

    def _read_peaks(bufs, surv_key, count, nd, nt, nbins, sparse):
        """The refined result: dense (idx, val), or a _SparsePeaks read from the refined
        pairs alone (the survivor list): the refine writes every bin of a listed pair."""
        if sparse:
            from . import _SparsePeaks
            # Gathered and scanned in the list's (completion) order; only the hits are put
            # in C order -- most refined pairs hold no peak.
            rows = bufs[surv_key].view(np.uint32, count)
            ri = bufs["idx"].view(np.int32, nd * nt * nbins).reshape(nd * nt, nbins)[rows]
            k, b = np.nonzero(ri >= 0)
            vals = bufs["val"].view(np.complex64, nd * nt * nbins).reshape(nd * nt, nbins)
            rk = rows[k].astype(np.int64)
            flat = rk * nbins + b
            order = np.argsort(flat)
            return _SparsePeaks((nd, nt, nbins), flat[order], ri[k, b][order],
                                vals[rk, b][order])
        if count == 0:
            return (np.full((nd, nt, nbins), -1, dtype=np.int32),
                    np.zeros((nd, nt, nbins), dtype=np.complex64))
        out = nd * nt * nbins
        return (bufs["idx"].read(np.int32, out).reshape(nd, nt, nbins),
                bufs["val"].read(np.complex64, out).reshape(nd, nt, nbins))

    def _descriptor_set(self, set_layout, bufs, offsets=None):
        vk = self.vk
        # Bindings the module declares past the caller's list (gRowWin when per-row
        # windows are off) get a small dummy buffer the kernel never reads.
        want = self._device_state.__dict__.get("layout_nbind", {}).get(
            getattr(set_layout, "value", set_layout), len(bufs))
        if len(bufs) > want:
            # A buffer for a binding the module does not declare: the kernel cannot read
            # it, so whatever the caller meant it to do silently does not happen.
            raise VulkanError("descriptor set given %d buffers for a %d-binding layout"
                              % (len(bufs), want))
        if want > len(bufs):
            dummy = getattr(self, "_dummy_buf", None)
            if dummy is None:
                dummy = self._dummy_buf = _Buffer(self, 64)
            bufs = list(bufs) + [dummy] * (want - len(bufs))
            if offsets is not None:
                offsets = list(offsets) + [0] * (want - len(offsets))
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

    _INVOCATIONS = {}

    def _invocations(self, filename):
        """Invocations per workgroup of a shipped SPIR-V module (cached per file)."""
        n = self._INVOCATIONS.get(filename)
        if n is None:
            n = self._INVOCATIONS[filename] = _module_invocations((_SPIRV / filename).read_bytes())
        return n

    def _fit_subgroup(self, n):
        """The subgroup size to build a one-pair-per-group kernel of length n at: the
        smallest the device can be required to run that still holds the workgroup
        (n/16 invocations), so a 32-invocation group does not leave half of a 64-wide
        wave idle. 0 (the default size) otherwise. Listed one-bin refine, CU-cycles/pair,
        wave64 -> wave32: n=256 481 -> 385, n=512 (32 invocations) 620 -> 552; 1024 1020 -> 1157, 2048
        2113 -> 2266, 4096 4400 -> 4921 (larger groups lose)."""
        rng = getattr(self, "subgroup_range", None)
        wg = max(1, n // 16)
        if not rng or wg > rng[0] or rng[0] >= self.subgroup_size:
            return 0
        return rng[0] if wg <= rng[0] else 0

    # ---- band-only forward with survivor recompute (docs section 12, option (a)) ----------

    def empty_shared(self, shape, dtype=np.complex64, *, readback=False, host_input=False):
        factory = (lambda ctx, size: _Buffer(ctx, size, readback=True)) if readback else _Buffer
        return empty_shared(self, factory, shape, dtype)

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
        # The pair's queries are reset on the device when its command buffers run. Until
        # then a waiting read saw them AVAILABLE -- zero on a slot's first use, its previous
        # use's values after that -- so a read made before the submission executed (a
        # collect while a pipelined batch is still in flight) returned 0/0 or a stale
        # interval. Reset from the host now: the read then waits for this use's writes.
        if getattr(self, "_reset_query", None) is not None:
            self._reset_query(self.device, ts["pool"], 2 * i, 2)
        ts["pending"][i] = (label, time.perf_counter())
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
            kinds = [o[0] == "vkCmdPipelineBarrier" for o in ops]
            if any(b and not later for b, later in
                   zip(kinds, [all(kinds[i + 1:]) for i in range(len(kinds))])):
                # A barrier between two of a phase's commands: the batch would run them
                # unordered (it keeps a phase's barriers for its end). Never fused.
                return
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
                # As for timestamp pairs: unavailable until this submission writes them.
                if getattr(self, "_reset_query", None) is not None:
                    for q, _ in pr["marks"][h]:
                        self._reset_query(self.device, pr["pool"], q, 1)

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
            label, t_host = ts["pending"].pop(i)
            _check(self.vk.vkGetQueryPoolResults(self.device, ts["pool"], 2 * i, 2, 16, out, 8, 0x3),
                   "vkGetQueryPoolResults")              # 64-bit, wait
            ms = _gputime.interval_ms(out[0], out[1], self._ts_period,
                                      getattr(self, "timestamp_bits", 64),
                                      (time.perf_counter() - t_host) * 1e3)
            if ms is None:
                self.timing_rejected = getattr(self, "timing_rejected", 0) + 1
            else:
                self.timing_log.append((label, ms))

    def timings(self):
        """Settle outstanding timestamps and return the timing log (MF_GPU_TIMING=1)."""
        self._timestamp_resolve()
        self._profile_resolve()
        return self.timing_log

    def _submit(self, cmd, fence=None, wait=True, slot=None, pre=()):
        """Submit commands (pre: run first, in the same submission -- the work the executor
        deferred for this slot) and wait for them unless asked not to."""
        pending = None
        commands = list(pre)
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
        dev = getattr(self, "_device_state", None)
        if dev is not None and dev.pending_writes and queue is not self.queue \
                and getattr(queue, "value", queue) != getattr(self.queue, "value", self.queue):
            self.settle_writes()                # barriers order only one queue
        _check(self.vk.vkQueueSubmit(queue, 1, ctypes.byref(submit), fence),
               "vkQueueSubmit")
        if wait:
            if fence is not None:
                self._wait_fence(fence)
            else:
                _check(self.vk.vkQueueWaitIdle(queue), "vkQueueWaitIdle")

    # ---- driver primitives (_gpuexec) -----------------------------------------------------
    #: Kernels are specialized when their pipeline is built (constants 75/76/79): the tiers
    #: read the spectra in place, at a stride and a data scale (_gpuhier feeds).
    inplace_feed = True
    #: Whose kernel identity stored measured choices are tied to (gatechain.gpu_kernel_id).
    kernel_family = "vulkan"

    def _x_kernel(self, name, n, consts=None):
        c = consts or {}
        stride, rowwin = int(c.get("stride", 0) or 0), 1 if c.get("rowwin") else 0
        if name in ("peaks", "peaks1"):
            filename = self._peak_file(n, 1 if name == "peaks1" else 2)
            return self._build_pipeline(("peaks", filename), filename, _NBIND, _PUSH_BYTES)
        if name == "gate":                    # the fp32 filter as a gate tier, at its band
            filename = self._kernel_file(n)
            return self._build_pipeline(("peaks", filename), filename, _NBIND, _PUSH_BYTES,
                                        data_stride=stride, row_windows=rowwin)
        if name == "coarse":
            filename = coarse_stem(n, c["ppg"], c["tile"]) + ".spv"
            return self._build_pipeline(
                ("coarse16", n, c["ppg"], c["tile"]), filename, _NBIND, _PUSH_BYTES,
                data_stride=stride, row_windows=rowwin, subgroup=c.get("sg", 0),
                data_scale=c.get("scale", 0), coarse_twt=c.get("twt", 1))
        if name in ("tier", "tier1", "refine", "refine1"):
            # refineListedBounded (refine_bounded.slang): data, tmpl, idx, val, survivors and
            # their count, then the row-window table (binding 6).
            filename = self._peak_file(n, 1 if name.endswith("1") else 2, refine=True)
            return self._build_pipeline(("refine", filename), filename, 6, 32,
                                        data_stride=stride, row_windows=rowwin,
                                        subgroup=self._fit_subgroup(n))
        fixed = {"compact": ("compact.spv", 3, 12), "compactl": ("compactl.spv", 5, 12),
                 "mark": ("markblocks.spv", 5, 4),
                 "pack": (_manifest()["pack_coarse"]["file"], 2, 20),
                 "compact_peaks": (_manifest()["compact_peaks"]["file"], 4, 8),
                 "fwd_tier0": ("forward_tier0_%d.spv" % n, 4, 20),
                 "fwd_bands": ("forward_bands_%d.spv" % n, 3, 12),
                 "fwd_listed": ("forward_listed_%d.spv" % n, 5, 12),
                 "forward": ("forward_%d.spv" % n, 3, 8)}
        if name in fixed:
            filename, nbind, push = fixed[name]
            return self._build_pipeline((name, filename), filename, nbind, push)
        if name in ("full", "series"):
            entry = "full" if name == "full" else "full_series"
            module = _manifest().get('modules', {}).get(str(n)) or {}
            info = module.get(entry)
            if info is None:
                raise UnsupportedSize('no %s GPU kernel for n=%d' % (entry, n))
            filename = ((info.get('portable') or {}).get('file')
                        if module.get('lds_bytes', 0) > self.max_shared_memory else info['file'])
            if not filename:
                raise UnsupportedSize('no portable %s GPU kernel for n=%d' % (entry, n))
            if name == "full":
                return self._build_pipeline(('full', filename), filename, 3, 4)
            return self._build_pipeline(('full-series', filename), filename, 4, 16)
        info = _manifest().get('full_tierc', {}).get(str(n))
        if info is None:
            raise UnsupportedSize('no two-stage full-correlation kernel for n=%d' % n)
        if name == "tc1":
            return self._build_pipeline(('tc-corr1', n), info['corr1']['file'], 3, 4)
        if name == "tf1":
            return self._build_pipeline(('tc-fwd1', n), info['fwd1']['file'], 3, 4)
        if name == "tf2":
            return self._build_pipeline(('tc-fwd2', n), info['fwd2']['file'], 2, 0)
        if name == "tcs2":
            return self._build_pipeline(('tc-corr-series2', n), info['corr_series2']['file'],
                                        3, 16)
        return self._build_pipeline(('tc-corr2', n), info['corr2']['file'], 2, 0)

    @staticmethod
    def _x_has_c16(band):
        return _spv_shipped("tierb_%d_c16" % band)

    @staticmethod
    def _x_has_kernel(name, n):
        if name == "tier1":
            info = (_manifest().get("modules", {}).get(str(n)) or {}).get("refine") or {}
            return bool(info.get("one_bin"))
        if name == "fwd_tier0":
            return (_SPIRV / ("forward_tier0_%d.spv" % n)).is_file()
        raise ValueError(name)

    def _x_coarse_candidates(self, band):
        """Every coarse layout (subgroup, ppg, tile, twt) this device can run at this band: the
        shipped builds whose group fits the device's invocation and shared-memory limits, at
        each subgroup size it can require (VK_EXT_subgroup_size_control; the default size
        only, 0, without it). MF_VK_COARSE_PPG caps the packing, MF_VK_COARSE_TILE and
        MF_VK_COARSE_SUBGROUP fix the tile (1 = untiled) and subgroup, and MF_VK_COARSE_TWT an
        untiled build's twiddles (1 table, 0 recurrence), for measurement and tests."""
        wg = max(1, band // 16)
        cap = int(os.environ.get("MF_VK_COARSE_PPG", "0") or 0)
        rng = getattr(self, "subgroup_range", None)
        sizes = [0]
        if rng:
            sizes = [s for s in (4, 8, 16, 32, 64, 128) if rng[0] <= s <= rng[1]]
        forced_sg = forced_tile("MF_VK_COARSE_SUBGROUP")
        if forced_sg is not None:
            sizes = [forced_sg if forced_sg in sizes else sizes[0]]
        forced = forced_tile("MF_VK_COARSE_TILE")
        forced_twt = forced_tile("MF_VK_COARSE_TWT")
        out = []
        for ppg in (1, 2, 4, 8, 16, 32):
            if cap and ppg > cap:
                continue
            # A group of ppg pairs is (band/16)*ppg invocations and holds ppg padded
            # exchange stages (about 17/16 * band words each).
            if (wg * ppg > self.max_invocations
                    or (band * 17 // 16 + 32) * 4 * ppg > self.max_shared_memory):
                continue
            for tile in (1,) + shipped_tiles(band, ppg, _spv_shipped):
                if forced is not None and tile != forced:
                    continue
                if not _spv_shipped(coarse_stem(band, ppg, tile)):
                    continue
                # Sizes that would split the group past maxComputeWorkgroupSubgroups are
                # out (_build_pipeline would bump them to the next size anyway).
                lim = getattr(self, "max_workgroup_subgroups", 0)
                out.extend((sg, ppg, tile, twt) for sg in sizes
                           for twt in ((1, 0) if tile == 1 else (1,))
                           if forced_twt is None or tile > 1 or twt == forced_twt
                           if not (lim and sg and -(-wg * ppg // sg) > lim))
        if not out:
            out = [(sizes[0], 1, 1, 0)]
        return out

    def _x_time(self, native, binds, reps):
        """The least device time of `reps` runs of a recorded list (device timestamps)."""
        vk = self.vk
        ds = self._device_state
        timer = ds.__dict__.get("fuse_timer")
        if timer is None:
            timer = ds.fuse_timer = _DeviceTimer(ds)
        cmd, release = native.command(binds or {}, transient=True)
        times = []
        try:
            for rep in range(reps + 1):
                i, begin, end = timer.pair()
                cmds = (_vp * 3)(begin, cmd, end)
                fence = _vp()
                _check(vk.vkCreateFence(self.device, ctypes.byref(_FenceCreate(8, None, 0)),
                                        None, ctypes.byref(fence)), "vkCreateFence")
                try:
                    _check(vk.vkQueueSubmit(self.queue, 1, ctypes.byref(
                        _SubmitInfo(4, None, 0, None, None, 3, cmds, 0, None)), fence),
                        "vkQueueSubmit")
                    _check(vk.vkWaitForFences(self.device, 1, (_vp * 1)(fence), 1,
                                              0xFFFFFFFFFFFFFFFF), "vkWaitForFences")
                finally:
                    vk.vkDestroyFence(self.device, fence, None)
                if rep:                          # the first run is a warm-up
                    times.append(timer.ns(i, self._ts_period) * 1e-9)
        finally:
            if release is not None:
                release()
        return min(times)

    def _x_tierc(self, n):
        info = _manifest().get('full_tierc', {}).get(str(n))
        if info is None:
            raise UnsupportedSize('no two-stage full-correlation kernel for n=%d' % n)
        return info['n1'], info['n2']

    def _x_alloc(self, nbytes, readback=False, upload=False):
        return _Buffer(self, nbytes, readback=readback)

    def _x_list(self, label, once=False):
        return _VkList(self, label, once)

    @staticmethod
    def _pre_commands(pre):
        out, frees = [], []
        for native, binds in pre:
            cmd, release = native.command(binds or {}, transient=True)
            out.append(cmd)
            if release is not None:
                frees.append(release)
        return out, frees

    def _x_run(self, native, wait, binds=None, slot=None, pre=()):
        cmd, release = native.command(binds or {}, transient=wait)
        pcmds, frees = self._pre_commands(pre)
        if wait:
            self._submit(cmd, slot=slot, pre=pcmds)
            for free in frees + ([release] if release is not None else []):
                free()
        else:
            self._submit_pending(cmd, pre=pcmds)

    def _x_submit(self, native, binds, slot, pre=()):
        cmd, release = native.command(binds, transient=True)
        pcmds, frees = self._pre_commands(pre)
        frees = frees + ([release] if release is not None else [])
        if slot is None:                    # per-slot fences: an unslotted run is waited now
            self._submit(cmd, pre=pcmds)
            for free in frees:
                free()
            return lambda: None
        fence = self._get_fence(slot)
        self._submit(cmd, fence=fence, wait=False, slot=slot, pre=pcmds)

        def wait():
            self._wait_fence(fence)
            for free in frees:
                free()
            del frees[:]
        return wait

    @staticmethod
    def _x_upload(buf, array, slot):
        buf.write(array)

    def _x_prefetch(self, view, offset, nbytes, slot):
        pass

    def _x_after_readers(self):
        pass                # no wait added (open question: docs/unification-plan.md log)

    @staticmethod
    def _x_release(native, done=False):
        native.release(done)

    def _x_idle(self):
        self._wait_queues()

    @staticmethod
    def _x_free(buf):
        buf.destroy()

    @staticmethod
    def _x_section(buf, offset, nbytes):
        return _Section(buf, offset, nbytes)

    @staticmethod
    def _x_read(buf, out, offset=0):
        ptr = buf.ptr.value if hasattr(buf.ptr, "value") else buf.ptr
        ctypes.memmove(out.ctypes.data, ptr + offset, out.nbytes)

    @staticmethod
    def _x_view(buf, dtype, count):
        return buf.view(dtype, count)

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

    def zero_columns_done(self, wait=True):
        """Record and submit every collected zero_columns range, and wait for them and every
        write left in flight -- or, wait=False, leave them in flight too."""
        ranges, self._zero_ranges = getattr(self, "_zero_ranges", None) or [], []
        if not ranges:
            if wait:
                self.settle_writes()
            return
        vk = self.vk
        # A middle stage zeroes the same ranges every segment (the same windows of the same
        # output): its recording is kept and submitted again. Keyed by the allocations
        # (held by the entry, so their ids stay theirs) and the byte ranges.
        key = tuple((id(sb.owner), off, length) for sb, off, length in ranges)
        cache = self.__dict__.setdefault("_zero_recs", OrderedDict())
        hit = cache.get(key)
        if hit is not None:
            cache.move_to_end(key)
            if not wait:
                self._submit_pending(hit[1])
                return
            self._submit(hit[1])
            self.settle_writes()
            self._wait_queues()
            return
        cmd = _vp()
        _check(vk.vkAllocateCommandBuffers(self.device, ctypes.byref(
            _CmdBufAlloc(40, None, self.command_pool, 0, 1)), ctypes.byref(cmd)), "allocate zero")
        try:
            # Simultaneous use: segment k's submission of it may still be in flight (wait=False)
            # when segment k+1 submits it again.
            _check(vk.vkBeginCommandBuffer(cmd, ctypes.byref(_CmdBufBegin(42, None, _SIMULTANEOUS_USE,
                                                                          None))), "begin zero")
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
            owners = tuple(sb.owner for sb, _, _ in ranges)
            if len(cache) >= _ZERO_RECS:
                # The oldest recording may still be in flight: settle before freeing it.
                self.settle_writes()
                _, (_, old) = cache.popitem(last=False)
                vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
                vk.vkFreeCommandBuffers(self.device, self.command_pool, 1, (_vp * 1)(old))
            cache[key] = (owners, cmd)
            rec, cmd = cmd, None                 # kept (freed with the context's caches)
            if not wait:
                self._submit_pending(rec)
                return
            self._submit(rec)                   # waits; same queue as the correlation
            self.settle_writes()
            self._wait_queues()                 # and anything on the other queues
        finally:
            if cmd is not None:
                vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
                vk.vkFreeCommandBuffers(self.device, self.command_pool, 1, (_vp * 1)(cmd))

    def _free_zero_recs(self):
        """Free the kept zeroing recordings (after settling everything in flight)."""
        cache = self.__dict__.pop("_zero_recs", None)
        if cache:
            self.settle_writes()
            cmds = [c for _, c in cache.values()]
            vk = self.vk
            vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
            vk.vkFreeCommandBuffers(self.device, self.command_pool, len(cmds), (_vp * len(cmds))(*cmds))

    def _free_zero_cmds(self):
        """Free zeroing command buffers left in flight, once their writes are settled."""
        cmds, self._zero_cmds = getattr(self, "_zero_cmds", []), []
        if cmds:
            self.settle_writes()
            vk = self.vk
            vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
            vk.vkFreeCommandBuffers(self.device, self.command_pool, len(cmds), (_vp * len(cmds))(*cmds))

    def _submit_pending(self, cmd, pre=()):
        """Submit on the main queue and leave it in flight (see _Device.pending_writes)."""
        fence = _vp()
        _check(self.vk.vkCreateFence(self.device, ctypes.byref(_FenceCreate(8, None, 0)), None,
                                     ctypes.byref(fence)), "vkCreateFence")
        try:
            self._submit(cmd, fence=fence, wait=False, pre=pre)
        except BaseException:
            self.vk.vkDestroyFence(self.device, fence, None)
            raise
        self._device_state.pending_writes.append(fence)

    def settle_writes(self):
        """Wait for every write left in flight on this device (correlate_series(wait=False))."""
        dev = self._device_state
        while dev.pending_writes:
            fence = dev.pending_writes.pop(0)
            fences = (_vp * 1)(fence)
            _check(self.vk.vkWaitForFences(self.device, 1, fences, 1, 0xFFFFFFFFFFFFFFFF),
                   "vkWaitForFences")
            self.vk.vkDestroyFence(self.device, fence, None)

    def write_token(self):
        """A token for the writes left in flight so far on this device (the newest one), for
        settle_until: None when nothing is in flight."""
        dev = self._device_state
        return dev.pending_writes[-1] if dev.pending_writes else None

    def settle_until(self, token):
        """Wait for the writes in flight up to and including token (write_token()), not
        later ones. Each earlier write is waited on too (submissions may complete out of
        order). A token already settled is a no-op."""
        dev = self._device_state
        if token is None or all(f is not token for f in dev.pending_writes):
            return
        while dev.pending_writes:
            fence = dev.pending_writes.pop(0)
            fences = (_vp * 1)(fence)
            _check(self.vk.vkWaitForFences(self.device, 1, fences, 1, 0xFFFFFFFFFFFFFFFF),
                   "vkWaitForFences")
            self.vk.vkDestroyFence(self.device, fence, None)
            if fence is token:
                break



    def followup_executor(self):
        """This device's executor for _gpuhost.submit_followups (_vkfollowup: one recording per group, replayed)."""
        from . import _vkfollowup
        return _vkfollowup.executor(self)

    def clear_cache(self):
        """Release records and owned storage, preserving external shared arrays."""
        self._drain()
        self._free_zero_recs()
        self._wait_queues()
        self.vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
        self._evict_all()
        # Descriptor pools left by a failed construction.
        for pool in getattr(self, '_pools', []):
            self.vk.vkDestroyDescriptorPool(self.device, pool, None)
        self._pools = []
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
