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
from ._shared import empty_shared, shared_buffer, shared_key, shared_view, write_input
from ._gpuhost import (MAX_BINS, band_windows, bin_shift, coarse_span, plan_items, split_items, hier_tiers, hier_window,
                       split_bins, hier_peaks_grouped as _hier_peaks_grouped)
from ._shared import pack_half2 as _pack_half2, sparsified as _sparsified

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


#: Where the fp16 coarse tier's operands are put (_c16_scales): the packed templates' largest
#: component in [2^C16_TEMPLATE_EXP, 2^(C16_TEMPLATE_EXP+1)), leaving fp16's lower 18 octaves
#: for a template's own dynamic range, and the tier's threshold at 2^_c16_threshold_exp(band).
C16_TEMPLATE_EXP = 3
C16_THRESHOLD_EXP = 2
#: The threshold over the band, at least 2^C16_BAND_EXP: a band-B transform's values at
#: threshold are sums of B products, each ~thr/B, and those must stay well inside fp16's
#: normal range. Measured on the Iris Xe (flushes subnormals): at band 2048 a threshold of 4
#: left the bound 0.24% under the exact maximum and 8 used 72% of its margin; 16 and above
#: pass (tests/test_gpu_c16_bound.py). Set one octave past that: thr/band >= 2^-6.
C16_BAND_EXP = -6


def _c16_threshold_exp(band):
    """log2 of where the tier's threshold is put: 2^C16_THRESHOLD_EXP -- where production
    banks already sit (log2 thresholds 1.0-3.0 on the test27 ladder), |y|^2 = 16 at
    threshold, failing open only past 64x it -- raised with the band so thr/band stays at or
    above 2^C16_BAND_EXP (8 at band 512, 32 at 2048)."""
    return max(C16_THRESHOLD_EXP, int(band).bit_length() - 1 + C16_BAND_EXP)


def _c16_scales(ct0, raw_thr, band=None):
    """(template exponent, data exponent) for the fp16 coarse tier: ct0 is packed times
    2^et, each data element is multiplied by 2^ed before it is rounded to half (constant 79),
    and the tier compares against raw_thr * 2^(et+ed). Powers of two, so in range every
    value is the unscaled one times an exact factor and the decision is unchanged; out of
    range they are what keeps it: on an Iris Xe, which flushes fp16 subnormals, templates of
    ~5e-5 (gate_margin's transient and injection families) were flushed to zero and every
    pair dismissed. (0, 0) where there is nothing to place (no threshold, empty templates)."""
    import math
    a = np.asarray(ct0)
    if a.size == 0 or not (0.0 < float(raw_thr) < math.inf):
        return 0, 0
    tm = float(np.abs(a.view(np.float32) if a.dtype == np.complex64 else
                      np.asarray(a, np.complex64).view(np.float32)).max())
    if not (0.0 < tm < math.inf):
        return 0, 0
    et = C16_TEMPLATE_EXP - math.floor(math.log2(tm))
    band = a.shape[-1] if band is None else band
    ed = int(round(_c16_threshold_exp(band) - math.log2(float(raw_thr)) - et))
    return int(max(-100, min(100, et))), int(max(-100, min(100, ed)))


def _pow2_scaled(a, e):
    """a (complex) times 2^e, exactly (complex64); a itself when e is 0."""
    a = np.ascontiguousarray(a, np.complex64)
    if not e:
        return a
    return np.ldexp(a.view(np.float32), int(e)).view(np.complex64)


from ._coarse import coarse_launch   # noqa: E402,F401  (shared with Metal; re-exported)
from ._coarse import stored_measured_choice, time_staged   # noqa: E402
from ._coarse import coarse_stem, shipped_tiles, forced_tile   # noqa: E402
from ._coarse import forced_layout, layout_label   # noqa: E402


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


#: An indirect dispatch's initial (x, y, z) = (0, 1, 1): x counts survivors. One
#: vkCmdUpdateBuffer per counter instead of two fills; small transfer commands cost ~2 us
#: each on the device, and a segment records hundreds. Module-level because fused batches
#: re-record captured calls later, and the command reads its data at record time.
_ARGS_INIT = (ctypes.c_uint32 * 3)(0, 1, 1)


def _reset_args(vk, cmd, buf):
    vk.vkCmdUpdateBuffer(cmd, buf.handle, 0, 12, ctypes.addressof(_ARGS_INIT))


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
        self.vk.vkCmdDispatchIndirect(self.cmd, buf.handle, 0)

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
#: A phase is ONE step of each recording: a fused batch emits every item's work for a phase
#: and then their barriers, so a recording's barrier only separates its phases. Steps that
#: depend on each other within a call (marking survivor blocks, then recomputing them) are
#: therefore separate phases.
_FUSED_PHASES = ("forward", "fill", "pack", "coarse0", "compact0", "coarse1", "compact1",
                 "mark", "recompute", "refine")

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


def _band_key(bands):
    """What a band-mode recording binds besides its storage: the band width and the series
    the recompute reads (the buffers and the row offset), or None in full mode."""
    if not bands:
        return None
    B, (n, series_b, starts_b, r0, count, nser, _slot, _cmd) = bands
    return (B, getattr(series_b.handle, "value", series_b.handle),
            getattr(starts_b.handle, "value", starts_b.handle), r0, nser)


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
            if (_SSC_EXT in have and ssc.subgroupSizeControl
                    and not os.environ.get("MF_VK_NO_SUBGROUP_PIN")):
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


class _HierHandle:
    """What hier_replay needs to submit one hier_peaks call again (see hier_peaks)."""
    __slots__ = ("kind", "key", "batch", "storage_key", "dsig", "tsig", "nd", "nt", "nbins",
                 "sparse", "mode", "bfwd")

    def __init__(self, kind, key, batch, storage_key, dsig, tsig, nd, nt, nbins, sparse,
                 mode=None, bfwd=None):
        self.kind, self.key, self.batch, self.storage_key = kind, key, batch, storage_key
        self.dsig, self.tsig, self.nd, self.nt, self.nbins, self.sparse = (
            dsig, tsig, nd, nt, nbins, sparse)
        # mode: (n, B, nd, nt, band key or None): the band/full choice this record was made
        # for. bfwd: (forward key, record) of its band-only forward, in band mode.
        self.mode, self.bfwd = mode, bfwd


class Context(InputUploads):
    """One Vulkan device, its compute queue, and the pipelines built on it."""

    max_grouped_bins = _MAX_BINS
    #: Async submission with per-slot fences: the series loop keeps several
    #: batches in flight. A declared capability, not a signature probe.
    supports_async = True
    #: hier_peaks/forward take handle_out, and hier_replay/forward_replay resubmit them.
    supports_replay = True
    #: Selected follow-ups (_gpuhost.FollowupSpec) run as one fixed recording per template
    #: group (_vkfollowup), refineItems over listed entries.
    supports_device_followups = True
    #: hier_peaks_grouped takes groups of different bin counts (nbins = the largest; per-row
    #: windows bound each block), so a hierarchical plan's ragged call is one submission.
    supports_ragged_hier = True
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

    def hier_peaks(self, n, band, data, tmpl, ct0, raw_thr,
                   binsize=None, threshold=0.0, window=None,
                   upload_data=True, upload_tmpl=True,
                   cascade_band=None, ct1=None, raw_thr1=None,
                   slot=None, async_submit=False, sparse=False, row_windows=None,
                   handle_out=None):
        """The whole hierarchical filter in ONE command buffer.

        Coarse correlation, survivor compaction, then listed refinement.
        Supports single-tier or two-tier cascade indirect execution.

        handle_out (a list): receives a replay handle for this exact call -- the record it
        submitted and the input signatures it was valid for. hier_replay(handle, ...) submits
        that record again without any of the work above, or returns None when the handle
        no longer holds (record evicted or rebuilt, inputs re-uploaded since).
        """
        band, ct0, raw_thr, cascade_band, ct1, raw_thr1 = hier_tiers(
            n, band, ct0, raw_thr, cascade_band, ct1, raw_thr1)

        nd, nt = data.shape[0], tmpl.shape[0]
        lo, hi, binsize, nbins = hier_window(n, window, binsize)
        # row_windows (hier_peaks_grouped): (groups, per-row uint32 [lo, hi] pairs).
        rw_key = None if row_windows is None else row_windows[0]
        rw = None if row_windows is None else row_windows[1]
        if nbins > _MAX_BINS and rw is not None:
            raise ValueError("grouped dispatch exceeds the kernel bin limit")
        if nbins > _MAX_BINS:
            return split_bins(
                lambda w, ud, ut: self.hier_peaks(
                    n, band, data, tmpl, ct0, raw_thr, binsize=binsize, threshold=threshold,
                    window=w, upload_data=ud, upload_tmpl=ut, cascade_band=cascade_band,
                    ct1=ct1, raw_thr1=raw_thr1, slot=slot, async_submit=False),
                lo, hi, binsize, _MAX_BINS, upload_data, upload_tmpl, sparse, async_submit)
        shift = bin_shift(binsize)
        t2 = float(threshold) ** 2 if threshold > 0 else 0.0

        # The gate tiers in order -- bands tb, thresholds tthr, templates tct: one, or a
        # cascade of two. Plain tuples: this runs on every call (a generator per field
        # cost 1.7 us of a 43 us call).
        cascade = cascade_band is not None
        if cascade:
            tb, tthr, tct = ((int(cascade_band), int(band)), (float(raw_thr), float(raw_thr1)),
                             (ct0, ct1))
        else:
            tb, tthr, tct = (int(band),), (float(raw_thr),), (ct0,)
        kind = "hier_cascade" if cascade else "hier"
        # Tier 0 is the packed fp16 coarse role where its band has one; a cascade's always is.
        half = cascade or bool(_use_c16(tb[0]))
        top = max(tb)
        bands = self._band_source(n, top, nd, nt, data, slot) if half else None
        bkey = _band_key(bands)
        # A sparse caller reads only the refined pairs, which the refine writes in full: its
        # recording skips clearing the dense outputs (bool(sparse) in the key).
        key = ((kind, n) + tb + (nd, nt, nbins, binsize, shift, lo, hi,
               int(np.float32(t2).view(np.uint32))) + tthr + (bool(sparse), rw_key, bkey))
        key += (shared_key(data, self), shared_key(tmpl, self), slot)
        # Storage depends on the band widths only. The series/starts a band-mode record binds
        # (bkey) change with the follow-up pools every segment: keying the buffers on them
        # allocated a new set per call (1339 buffers in 38 steady segments).
        storage_key = (kind, n, *tb, nd, nt, nbins, rw_key, bkey and bkey[0], *key[-3:])
        upload_data, upload_tmpl, dsig, tsig = self._input_uploads(
            storage_key, data, tmpl, upload_data, upload_tmpl)
        et, ed = (self._c16_exponents(storage_key, ct0, tthr[0], upload_tmpl, tb[0])
                  if half else (0, 0))
        key += (ed,)
        self._last_c16_scale = 2.0 ** (et + ed)   # tier-0 values / this = unscaled
        table = self._hier_cascade if cascade else self._hier
        batch = table.get(key)
        if batch is None:
            sd, st = shared_buffer(data, self), shared_buffer(tmpl, self)
            incoming = [x for x in (sd, st) if x is not None]
            estimate = 0
            if storage_key not in self._storage:
                estimate = (8 * n * (nd + nt) - (nd * n * 8 if sd else 0) - (nt * n * 8 if st else 0)
                            + sum((4 if i == 0 and cascade else 8) * b * (nd + nt)
                                  for i, b in enumerate(tb))
                            + nd * nt * (8 * len(tb) + 8 + 12 * nbins) + 12 * len(tb))
            self._cache_room(estimate, incoming=incoming, keep_storage=storage_key)
            fresh = storage_key not in self._storage
            pool_start = len(getattr(self, '_pools', []))
            self._capture_begin()
            try:
                batch = self._make_hier(
                    storage_key, n, [(b, thr * (2.0 ** (et + ed) if i == 0 else 1.0))
                                     for i, (b, thr) in enumerate(zip(tb, tthr))],
                    nd, nt, nbins, binsize, shift, lo, hi, t2, data, tmpl,
                    clear_out=not sparse, rowwin=rw, bands=bands, data_scale=ed)
            finally:
                self._capture_end(batch[-1] if batch else None)
            table[key] = batch
            self._register_record(kind, key, storage_key, pool_start)
            if fresh:
                upload_data = upload_tmpl = True
        self._cache_touch(kind, key)
        bufs, cmd = batch
        self._claim(bufs["idx"])                 # an earlier result still reading these outputs
        bfwd = self._band_forward(storage_key, bufs, bands, nd) if bands else None
        if bfwd is not None:
            self._pending_forward[slot] = bfwd[1][-1]
        if upload_data:
            write_input(bufs["data"], data)
            if not half and shared_buffer(data, self) is None:
                # The full-precision coarse role reads a band copy (the packed one reads
                # `data` itself, and a shared buffer is packed on the device).
                bufs["cdata"].write(np.ascontiguousarray(data[:, :tb[0]], np.complex64))
            self._uploaded["data"][storage_key] = dsig
        if upload_tmpl:
            write_input(bufs["tmpl"], tmpl)
            for i, ct in enumerate(tct):
                bufs["ct%d" % i].write(_pack_half2(_pow2_scaled(ct, et)) if i == 0 and half
                                       else np.ascontiguousarray(ct, np.complex64))
            self._uploaded["tmpl"][storage_key] = tsig

        mode = (n, top, nd, nt, bkey)
        if handle_out is not None:
            handle_out.append(_HierHandle(kind, key, batch, storage_key,
                                          self._uploaded["data"].get(storage_key),
                                          self._uploaded["tmpl"].get(storage_key),
                                          nd, nt, nbins, sparse, mode, bfwd))
        return self._hier_submit(batch, cascade, nd, nt, nbins, sparse, slot, async_submit, mode)

    def _hier_submit(self, batch, cascade, nd, nt, nbins, sparse, slot, async_submit,
                     mode=None):
        """Submit one hierarchical record and return its readback (tracked when async)."""
        bufs, cmd = batch
        fence = self._get_fence(slot) if (async_submit and slot is not None) else None
        if async_submit and slot is not None:
            self._submit(cmd, fence=fence, wait=False, slot=slot)
        else:
            self._submit(cmd)

        v = self._peak_views(bufs, cascade, nd, nt, nbins)

        def readback():
            if fence is not None:
                self._wait_fence(fence)
            if v is None:                       # buffers without in-place views
                surv_count = int(bufs["args"].read(np.uint32, 1)[0])
                self.last_refinements = surv_count
                if mode is not None:
                    self._band_measure(mode[0], mode[1], nd, nt, bufs, "surv", surv_count)
                if cascade:
                    self.last_tier1_survivors = int(bufs["args0"].read(np.uint32, 1)[0])
                return self._read_peaks(bufs, "surv", surv_count,
                                        nd, nt, nbins, sparse)
            surv_count = int(v[0][0])
            self.last_refinements = surv_count
            if cascade:
                self.last_tier1_survivors = int(v[1][0])
            if surv_count == 0 and sparse:
                # The common case at a detection threshold: nothing to sort, gather or scan.
                if mode is not None:
                    self.__dict__.setdefault("_band_f", {})[(mode[0], mode[1], nd, nt)] = 0.0
                from . import _SparsePeaks
                e = np.empty(0, np.int64)
                return _SparsePeaks((nd, nt, nbins), e, e, np.empty(0, np.complex64))
            rows = v[2][:surv_count] if (sparse or mode is not None) else None
            if mode is not None:
                # The refine-block fraction: distinct survivor blocks, marked rather than
                # sorted (the list is in device completion order).
                seen = np.zeros(nd, np.bool_)
                seen[rows // nt] = True
                self.__dict__.setdefault("_band_f", {})[(mode[0], mode[1], nd, nt)] = (
                    int(np.count_nonzero(seen)) / float(nd))
            if sparse:
                from . import _SparsePeaks
                # Gather and scan in completion order; only the hits are put in C order.
                ri = v[3][rows]
                k, b = np.nonzero(ri >= 0)
                if not k.size:
                    e = np.empty(0, np.int64)
                    return _SparsePeaks((nd, nt, nbins), e, e, np.empty(0, np.complex64))
                rk = rows[k]
                flat = rk.astype(np.int64) * nbins + b
                order = np.argsort(flat)
                return _SparsePeaks((nd, nt, nbins), flat[order], ri[k, b][order],
                                    v[4][rk, b][order])
            if surv_count == 0:
                return (np.full((nd, nt, nbins), -1, dtype=np.int32),
                        np.zeros((nd, nt, nbins), dtype=np.complex64))
            return v[3].reshape(nd, nt, nbins).copy(), v[4].reshape(nd, nt, nbins).copy()
        return self._track(readback, owner=bufs["idx"]) if async_submit else readback()

    def _peak_views(self, bufs, cascade, nd, nt, nbins):
        """In-place views of a hierarchical record's outputs, made once per record: (refine
        count, tier-1 count or None, survivor list, idx (pairs, nbins), val (pairs, nbins)).
        Results read through them are copied (np.sort, fancy indexing, .copy()) before the
        record runs again. Dropped with the record (_evict_record)."""
        views = self.__dict__.setdefault("_pviews", {})
        hit = views.get(id(bufs))
        if hit is not None and hit[0] is bufs and hit[1] == (nd, nt, nbins):
            return hit[2]
        pairs = nd * nt
        names = ("args", "surv", "idx", "val") + (("args0",) if cascade else ())
        if not all(hasattr(bufs[k], "view") for k in names):
            return None
        v = (bufs["args"].view(np.uint32, 1),
             bufs["args0"].view(np.uint32, 1) if cascade else None,
             bufs["surv"].view(np.uint32, pairs),
             bufs["idx"].view(np.int32, pairs * nbins).reshape(pairs, nbins),
             bufs["val"].view(np.complex64, pairs * nbins).reshape(pairs, nbins))
        views[id(bufs)] = (bufs, (nd, nt, nbins), v)
        return v

    def hier_valid(self, h):
        """Whether hier_replay(h) would submit: the record is the one the handle saw (an
        evicted or rebuilt record is a new object) and both inputs are still resident under
        the signatures it saw (nothing re-uploaded or invalidated them since)."""
        table = self._hier_cascade if h.kind == 'hier_cascade' else self._hier
        if not (table.get(h.key) is h.batch
                and self._uploaded["data"].get(h.storage_key) == h.dsig
                and self._uploaded["tmpl"].get(h.storage_key) == h.tsig):
            return False
        # The band/full choice is part of validity: a record made for one mode is never
        # replayed once the measured refine-block fraction has flipped the choice.
        if h.mode is not None:
            n, B, nd, nt, bkey = h.mode
            if self._band_wanted(n, B, nd, nt) != (bkey is not None):
                return False
            forwards = getattr(self, "_forwards", None) or {}
            if h.bfwd is not None and forwards.get(h.bfwd[0]) is not h.bfwd[1]:
                return False
        return True

    def forward_valid(self, h):
        forwards = getattr(self, "_forwards", None)
        return forwards is not None and forwards.get(h[0]) is h[1]

    def hier_replay(self, h, slot, async_submit, validated=False):
        """Submit a hier_peaks call again from its handle, or None if the handle is stale.

        Valid exactly when the record is the one the handle saw (identity: an evicted or
        rebuilt record is a new object) and both inputs are still resident under the
        signatures it saw (nothing re-uploaded or invalidated them since).

        validated=True: the caller checked hier_valid for every part of a call before
        submitting any (a call's parts go out together or not at all). Submitting a part
        cannot evict a record or re-upload an input, but it can move the measured band/full
        choice (a flush collects measurements) -- a performance choice that must not leave a
        call half submitted, so it is not re-checked here."""
        if not validated and not self.hier_valid(h):
            return None
        self._cache_touch(h.kind, h.key)
        if h.bfwd is not None:
            # Band mode: the pending forward (queued by forward_replay) is the full one;
            # this record reads the band-only forward's rows instead.
            self._cache_touch('forward', h.bfwd[0])
            if not isinstance(getattr(self, "_pending_forward", None), dict):
                self._pending_forward = {}
            self._pending_forward[slot] = h.bfwd[1][-1]
        return self._hier_submit(h.batch, h.kind == 'hier_cascade', h.nd, h.nt, h.nbins,
                                 h.sparse, slot, async_submit, h.mode)

    def forward_replay(self, h, slot):
        """Queue a forward call again from its handle (forward(..., handle_out=)); False if
        the record is no longer the one the handle saw."""
        if not self.forward_valid(h):
            return False
        self._cache_touch('forward', h[0])
        if not isinstance(getattr(self, "_pending_forward", None), dict):
            self._pending_forward = {}
        self._pending_forward[slot] = h[1][-1]
        return True

    @staticmethod
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

    def _c16_exponents(self, storage_key, ct0, raw_thr, upload_tmpl, band):
        """(template, data) exponents of the fp16 coarse tier (_c16_scales) for a record on
        storage_key. The template exponent belongs to the templates in that storage: taken
        from ct0 when they are (re)written, kept with the storage otherwise, so a record and
        the packed templates it reads always agree; the data exponent follows from it and
        the threshold."""
        import math
        held = self.__dict__.setdefault("_c16_template_exp", {})
        if upload_tmpl or storage_key not in held:
            held[storage_key] = _c16_scales(ct0, 1.0)[0]
        et = held[storage_key]
        if not (0.0 < float(raw_thr) < math.inf):
            return et, 0
        ed = int(round(_c16_threshold_exp(band) - math.log2(float(raw_thr)) - et))
        return et, max(-100, min(100, ed))

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

    def _gate_bits(self, thr, band, sg, tile):
        """The coarse tier's last push constant: for a tiled build whose pair fits one subgroup,
        the gate threshold as magnitude bits (tierb.slang peakTwoGate: each pair reports only
        its pass and bound, no election -- nothing reads tier 0's index, only the compaction
        reads its values); 0 elects (peakTwoWave). Metal's rule. A threshold of 0 is passed
        as the smallest normal float, which passes the same pairs (a nonzero maximum)."""
        if tile <= 1 or os.environ.get("MF_VK_C16_BOUND", "1") == "0":
            return 0
        if band // 16 > (sg or self.subgroup_size):
            return 0
        return int(np.float32(max(float(thr), 1.1754944e-38)).view(np.uint32))

    def _coarse_geometry(self, band, nd, nt):
        """(subgroup, pairs per workgroup, templates per tile, groups, ragged) for the packed
        coarse kernel; subgroup 0 is the driver's default size.

        The layout -- the subgroup size the pipeline is built at, pairs per workgroup (PPG)
        and templates per pair slot (TILE_T) -- is this device's measured choice
        (_coarse_choice). A tiled build takes RAGGED tiles: each slot covers TILE_T
        templates of one data row and the row's last tile is clamped inside the kernel, so
        any template count and any group count work -- the host passes the row count and
        dispatches ceil(rows * ceil(nt/TILE_T) / PPG) groups. An untiled build with PPG > 1
        takes RAGGED groups the same way (ceil(rows * nt / PPG) groups), so the chosen
        packing holds at any pair count. The rule it replaces -- the largest PPG that
        divides the pair count -- ran 10 of a production segment's 27 fine groups (odd
        counts) at one pair per group, which on the Iris Xe cancelled a 1.45x coarse gain.
        """
        sg, ppg, tile, twt = self._coarse_choice(band)
        if tile > 1:
            return sg, ppg, tile, coarse_launch(nd, nt, ppg, tile, 0)[1], True, twt
        for p in (32, 16, 8, 4, 2, 1):
            if p <= ppg and _spv_shipped(coarse_stem(band, p, 1)):
                return (sg, p, 1, coarse_launch(nd, nt, p, 1, 0)[1], p > 1,
                        twt)
        return sg, 1, 1, nd * nt, False, twt

    def _coarse_layouts(self, band):
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

    def _coarse_choice(self, band):
        """The coarse layout (subgroup, ppg, tile) at this band: the fastest of
        _coarse_layouts on this device, timed once (device timestamps, synthetic data) and
        kept in MF_COST_FILE -- priced, not trialled: a deterministic micro-benchmark,
        the choice CUDA's _time_coarse makes. All three are the device's to decide. A fixed
        tile table (tuned on RDNA) was wrong on every GPU measured, RDNA included; filling
        one subgroup with pairs was the packing rule; and the subgroup was the driver's
        default, which on the Iris Xe (8-32 wide) is 32 -- the band-256 coarse kernel ran
        at ~2.9 us per pair there against ~0.25 us at subgroup 8 or 16."""
        from . import gatechain
        return stored_measured_choice(
            self._device_state.__dict__.setdefault("coarse_choice", {}), "vk-coarse",
            getattr(self, "device_name", ""), band, self._coarse_layouts(band),
            lambda c: layout_label(band, c[1], c[2], c[3], c[0]), gatechain.gpu_kernel_id(),
            lambda cs: self._time_coarse_layouts(band, cs), tiebreak=lambda c: (c[2], c[1], c[0]),
            forced=forced_layout(band))

    def coarse_layouts(self, band):
        """The names (_coarse.layout_label) of every coarse layout the choice may take at this
        band on this device; MF_COARSE_LAYOUT forces one."""
        return [layout_label(band, c[1], c[2], c[3], c[0]) for c in self._coarse_layouts(band)]

    def _time_coarse_layouts(self, band, cands, pairs=16384, screen=1024, ntm=16, reps=3):
        """Device ns per pair of each coarse layout on synthetic data, in
        self.coarse_times[band] for reports. Every candidate is first timed on `screen` pairs
        and only those within 4x of the fastest are timed on `pairs`: some layouts are
        pathological on some devices (band 256 at subgroup 32 on the Iris Xe: ~240 us per
        pair), and a full-size dispatch of one can run long enough for the driver to reset
        the device. Each stage times its candidates in `reps` interleaved rounds (a warm-up
        and one timed dispatch each, min over rounds), and the contenders are then confirmed
        against the fastest, paired (_coarse.confirm_fastest): the GPU may be shared."""
        ndm = pairs // ntm
        rng = np.random.default_rng(0)
        x = ((rng.standard_normal((ndm, band)) + 1j * rng.standard_normal((ndm, band)))
             * 0.1).astype(np.complex64)
        bufs = [_Buffer(self, x.nbytes), _Buffer(self, ntm * band * 4),
                _Buffer(self, pairs * 4), _Buffer(self, pairs * 8)]
        bufs[0].write(x)
        bufs[1].write(_pack_half2(x[:ntm]))
        ds = self._device_state
        timer = ds.__dict__.get("fuse_timer")
        if timer is None:
            timer = ds.fuse_timer = _DeviceTimer(ds)
        full = lambda c: self._time_coarse_layout(band, c, bufs, timer, ndm, ntm, 2)
        screen_ = lambda c: self._time_coarse_layout(band, c, bufs, timer, screen // ntm, ntm, 2)

        def tiles(times):
            # The tiles at the two fastest untiled (subgroup, ppg), and at any (subgroup, ppg)
            # with no untiled layout among cands (a re-check's set): a tile is skipped only
            # when its untiled sibling was measured and lost. Building a pipeline is most of
            # the cost (a tiled build took up to 50 s on the Iris Xe).
            lead = {c[:2] for c in sorted(times, key=times.get)[:2]}
            timed = {c[:2] for c in times}
            return [c for c in cands if c[2] > 1 and (c[:2] in lead or c[:2] not in timed)]
        try:
            untiled = [c for c in cands if c[2] == 1]
            out = time_staged([untiled or cands] + ([tiles] if untiled and len(untiled) < len(cands)
                                                     else []),
                              full, time_screen=screen_, rounds=reps)
        finally:
            for b in bufs:
                b.destroy()
        self.__dict__.setdefault("coarse_times", {}).setdefault(band, {}).update(
            {layout_label(band, c[1], c[2], c[3], c[0]): v
             for c, v in out.items()})
        return out

    def _time_coarse_layout(self, band, layout_, bufs, timer, ndm, ntm, reps):
        vk = self.vk
        sg, ppg, tile = layout_[:3]
        twt = layout_[3] if len(layout_) > 3 else 1
        pipe = self._build_pipeline(
            ("coarse16", band, ppg, tile), coarse_stem(band, ppg, tile) + ".spv",
            _NBIND, _PUSH_BYTES, data_stride=band, subgroup=sg, coarse_twt=twt)
        dset = self._descriptor_set(pipe[2], bufs)
        slot_val, groups = coarse_launch(ndm, ntm, ppg, tile, band)
        rec = _Recording(self, "coarse timing")
        cmd = rec.cmd
        times = []
        try:
            rec.bind(pipe, dset, (ntm, 0, band, slot_val, band.bit_length() - 1, 1,
                                  self._gate_bits(0.0, band, sg, tile)))
            rec.dispatch(groups)
            rec.end()
            for rep in range(reps):
                slot, begin, end = timer.pair()
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
                if rep:
                    times.append(timer.ns(slot, self._ts_period))
        finally:
            vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
            vk.vkFreeCommandBuffers(self.device, self.command_pool, 1, (_vp * 1)(cmd))
        return min(times) / (ndm * ntm)

    def _make_hier(self, key, n, tiers, nd, nt, nbins, binsize, shift, lo, hi, t2,
                   data=None, tmpl=None, clear_out=True, rowwin=None, bands=None, data_scale=0):
        """Record one hierarchical dispatch: the gate tiers, then the listed refine at n.

        tiers is [(band, raw threshold)], one tier or a cascade of two. Tier 0 correlates every
        pair at its band: the packed fp16 coarse role in a cascade or where the band has one
        (_use_c16),
        reading its band straight from the spectra (or the band rows, `bands`), and
        otherwise the full-precision filter over a band copy (cdata). A later tier refines
        only the previous tier's survivors at its own band, at full precision. Each tier is
        compacted into a survivor list whose count lands in an indirect-dispatch argument, so
        the count never reaches the host and the call stays one recorded command buffer.

        Tier i writes cidx<i> and cval<i> from ct<i>; its survivors are surv<i> and args<i>,
        except the last tier's: surv and args, which the refine and every reader take."""
        vk = self.vk
        pairs = nd * nt
        last = len(tiers) - 1
        surv = lambda i: "surv" if i == last else "surv%d" % i
        args = lambda i: "args" if i == last else "args%d" % i
        band0 = tiers[0][0]
        direct = bool(last or _use_c16(band0))    # a cascade's tier 0 is always packed
        dstride = bands[0] if bands else n
        rwf = 1 if rowwin is not None else 0       # row windows, mode 1 for every tier
        if direct:
            # The coarse ROLE, reading packed cdata/ct0. Not self.pipeline(): that is the flat
            # filter's full-precision build of the same entry, and handing it packed buffers
            # makes it read 4-byte elements as 8-byte ones (every peak comes back -1). The
            # layout -- subgroup, pairs per group, tile (compiled into the kernel, so decided
            # here with the kernel) and twiddle source -- is the device's (_coarse_geometry).
            sg, ppg, tile, groups, ragged, twt = self._coarse_geometry(band0, nd, nt)
            cpipe = self._build_pipeline(
                ("coarse16", band0, ppg, tile), coarse_stem(band0, ppg, tile) + ".spv",
                _NBIND, _PUSH_BYTES, data_stride=dstride, row_windows=rwf, subgroup=sg,
                data_scale=data_scale, coarse_twt=twt)
        else:
            sg, tile, groups, ragged = 0, 1, pairs, False
            cpipe = self.pipeline(band0)
        kpipe = self._build_pipeline("compact", "compact.spv", 3, 12)
        lpipe = self._build_pipeline("compactl", "compactl.spv", 5, 12) if last else None
        tpipes = [None]
        for b1, _ in tiers[1:]:
            f = self._peak_file(b1, 1, refine=True)
            tpipes.append(self._build_pipeline(
                ("refine", f), f, 5, _PUSH_BYTES, data_stride=dstride, row_windows=rwf,
                subgroup=self._fit_subgroup(b1)))
        refine_file = self._peak_file(n, nbins, refine=True)
        rpipe = self._build_pipeline(
            ("refine", refine_file), refine_file, 5, _PUSH_BYTES, row_windows=rwf,
            subgroup=self._fit_subgroup(n))

        b = self._storage.get(key)
        if b is None:
            indirect = _BUF_STORAGE | _BUF_INDIRECT | _BUF_TRANSFER_DST
            b = {
                "data": shared_buffer(data, self) or _Buffer(self, nd * n * 8),
                "tmpl": shared_buffer(tmpl, self) or _Buffer(self, nt * n * 8),
                "idx":  _Buffer(self, pairs * nbins * 4, readback=True, usage=_BUF_STORAGE | _BUF_TRANSFER_DST),
                "val":  _Buffer(self, pairs * nbins * 8, readback=True, usage=_BUF_STORAGE | _BUF_TRANSFER_DST),
            }
            if not direct:
                b["cdata"] = _Buffer(self, nd * band0 * 8)
            for i, (bi, _) in enumerate(tiers):
                b["ct%d" % i] = _Buffer(self, nt * bi * (4 if i == 0 and direct else 8))
                b["cidx%d" % i] = _Buffer(self, pairs * 4)
                b["cval%d" % i] = _Buffer(self, pairs * 8)
                # The survivor list and the indirect group count [count, 1, 1]: the compaction
                # bumps the count atomically.
                b[surv(i)] = _Buffer(self, pairs * 4, readback=i == last)
                b[args(i)] = _Buffer(self, 12, usage=indirect)
            if rowwin is not None:
                if not direct:
                    raise ValueError("per-row windows need the packed coarse role")
                b["rowwin"] = _Buffer(self, rowwin.nbytes)
                b["rowwin"].write(rowwin)
                for i, (bi, _) in enumerate(tiers):   # each tier's, mapped onto its band
                    cw = band_windows(rowwin, n, bi)
                    b["rowwin_c%d" % i] = _Buffer(self, cw.nbytes)
                    b["rowwin_c%d" % i].write(cw)
            if bands:
                if not direct:
                    raise ValueError("band rows need the packed coarse role")
                self._band_storage(b, nd, bands[0])
            self._storage[key] = b
        rw = (lambda name: [b[name]]) if rowwin is not None else (lambda name: [])
        src = (b["bands"] if bands else b["data"]) if direct else b["cdata"]
        sets = [self._descriptor_set(cpipe[2], [src, b["ct0"], b["cidx0"], b["cval0"]]
                                     + rw("rowwin_c0"))]
        csets = [self._descriptor_set(kpipe[2], [b["cval0"], b[surv(0)], b[args(0)]])]
        for i in range(1, last + 1):
            sets.append(self._descriptor_set(
                tpipes[i][2], [src, b["ct%d" % i], b["cidx%d" % i], b["cval%d" % i],
                               b[surv(i - 1)]] + rw("rowwin_c%d" % i)))
            csets.append(self._descriptor_set(
                lpipe[2], [b["cval%d" % i], b[surv(i)], b[args(i)], b[surv(i - 1)],
                           b[args(i - 1)]]))
        ds_listed = self._descriptor_set(
            rpipe[2], [b["data"], b["tmpl"], b["idx"], b["val"], b["surv"]] + rw("rowwin"))
        pack = shared_buffer(data, self) is not None and not direct
        if pack:
            ppipe = self._build_pipeline("pack_coarse", "pack_coarse.spv", 2, 16)
            ds_pack = self._descriptor_set(ppipe[2], [b["data"], b["cdata"]])

        rec = _Recording(self, "hierarchical")
        cmd, barrier, stamp = rec.cmd, rec.barrier, rec.stamp
        stamp("start")

        # The counts start at zero. Pairs that do not survive are never visited, so dense
        # outputs are cleared up front (a sparse reader takes only listed pairs, every bin of
        # which the refine writes). A later tier's cval needs no clear: its compaction reads
        # only the pairs that tier wrote.
        for i in range(last + 1):
            _reset_args(vk, cmd, b[args(i)])                  # count 0, y = z = 1
        if bands:
            self._band_fill(vk, cmd, b)
        if clear_out:
            vk.vkCmdFillBuffer(cmd, b["idx"].handle, 0, _WHOLE_SIZE, 0xFFFFFFFF)
            vk.vkCmdFillBuffer(cmd, b["val"].handle, 0, _WHOLE_SIZE, 0)
        # The compaction updates the counts atomically and indirect fetch reads all three
        # words. With zero survivors a count stays a transfer-only write, which the later
        # shader-write barriers cannot cover.
        barrier(src_stage=_STAGE_TRANSFER_BIT, src_access=_ACCESS_TRANSFER_WRITE,
                dst_stage=_STAGE_COMPUTE_BIT | _STAGE_DRAW_INDIRECT_BIT,
                dst_access=_ACCESS_SHADER_READ | _ACCESS_SHADER_WRITE | _ACCESS_INDIRECT_READ)
        stamp("fill")

        if pack:
            rec.bind(ppipe, ds_pack, (n, band0, nd * band0, 0))
            rec.dispatch((nd * band0 + 255) // 256)
            barrier()
            stamp("pack")

        for i, (bi, thr) in enumerate(tiers):
            cstart, cend, cspan, cshift = coarse_span(n, bi, lo, hi)
            if i == 0:
                # A ragged build reads the data row count where the (unused, one-bin)
                # coarse bin size would go; the last word is the gate threshold of a
                # gate-only tiled build (_gate_bits).
                rec.bind(cpipe, sets[0], (nt, cstart, cend, nd if ragged else cspan, cshift, 1,
                                          self._gate_bits(thr, bi, sg, tile)))
                rec.dispatch(groups)
            else:
                rec.bind(tpipes[i], sets[i], (nt, cstart, cend, cspan, cshift, 1, 0))
                rec.dispatch_indirect(b[args(i - 1)])
            barrier()
            stamp("coarse%d" % bi)
            rec.bind(kpipe if i == 0 else lpipe, csets[i],
                     (pairs, int(np.float32(thr).view(np.uint32)), nbins))
            rec.dispatch((pairs + 255) // 256)
            # The count is consumed by indirect-command fetch, not by a shader. Missing this
            # dependency made Intel use the previous dispatch count (zero on first use),
            # even while the host read the new count later.
            barrier(dst_stage=_STAGE_COMPUTE_BIT | _STAGE_DRAW_INDIRECT_BIT,
                    dst_access=_ACCESS_SHADER_READ | _ACCESS_SHADER_WRITE | _ACCESS_INDIRECT_READ)
            stamp("compact" if not last else "compact%d" % i)
        if bands:
            self._band_recompute(vk, cmd, b, bands, nt, pairs, "surv", "args", barrier)
            stamp("recompute")

        rec.bind(rpipe, ds_listed, (nt, lo, hi, binsize, shift, nbins,
                                    int(np.float32(t2).view(np.uint32))))
        rec.dispatch_indirect(b["args"])
        # Host readback includes the survivor count, which remains a fill write when no pair
        # survives, as well as shader-written peaks.
        barrier(src_stage=_STAGE_COMPUTE_BIT | _STAGE_TRANSFER_BIT,
                src_access=_ACCESS_SHADER_WRITE | _ACCESS_TRANSFER_WRITE,
                dst_stage=_STAGE_HOST_BIT, dst_access=_ACCESS_HOST_READ)
        stamp("refine")
        return b, rec.end()

    # ---- band-only forward with survivor recompute (docs section 12, option (a)) ----------
    def _band_source(self, n, B, nd, nt, data, slot):
        """(B, source) when this call should read band rows and recompute survivor rows,
        else None. Chosen from bytes, not a switch: per block the full forward writes n
        samples and the band forward B, while the recompute reads and writes n for each block
        with a refined pair, so bands move fewer bytes iff that fraction f < (n - B) / 2n.
        f is the one measured on this call shape's previous run; the first run is full."""
        if os.environ.get("MF_VK_BAND_FORWARD") == "0" or n > 65536 or B >= n:
            return None
        src = getattr(self, "_fwd_src", {}).get(data.ctypes.data)
        pend = getattr(self, "_pending_forward", None)
        if (src is None or src[0] != n or src[4] != nd or not isinstance(pend, dict)
                or pend.get(slot) is not src[7]):
            return None
        if not self._band_wanted(n, B, nd, nt):
            return None
        return (B, src)

    def _band_wanted(self, n, B, nd, nt):
        """The band/full choice for this call shape from its measured refine-block fraction
        (see _band_source); forced by MF_VK_BAND_FORWARD=0/1."""
        env = os.environ.get("MF_VK_BAND_FORWARD")
        if env == "0" or n > 65536 or B >= n:
            return False
        if env == "1":
            return True
        f = getattr(self, "_band_f", {}).get((n, B, nd, nt))
        return f is not None and f < (n - B) / (2.0 * n)

    def _band_storage(self, b, nd, B):
        b["bands"] = _Buffer(self, nd * B * 8)
        b["bflags"] = _Buffer(self, nd * 4, usage=_BUF_STORAGE | _BUF_TRANSFER_DST)
        b["blocks"] = _Buffer(self, nd * 4)
        b["bargs"] = _Buffer(self, 12, usage=_BUF_STORAGE | _BUF_INDIRECT | _BUF_TRANSFER_DST)

    def _band_fill(self, vk, cmd, b):
        vk.vkCmdFillBuffer(cmd, b["bflags"].handle, 0, _WHOLE_SIZE, 0)
        _reset_args(vk, cmd, b["bargs"])

    def _band_recompute(self, vk, cmd, b, bands, nt, pairs, surv_key, args_key, barrier):
        # Two phases ("mark", then "recompute"): the second reads what the first wrote.
        """The refine's survivor blocks, their full spectra recomputed into their rows."""
        B, (n, series_b, starts_b, r0, count, nser, _slot, _cmd) = bands
        mpipe, mlayout, msl = self._build_pipeline("markblocks", "markblocks.spv", 5, 4)
        ds = self._descriptor_set(msl, [b[surv_key], b[args_key], b["bflags"], b["blocks"],
                                        b["bargs"]])
        vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, mpipe)
        vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, mlayout, 0, 1, (_vp * 1)(ds), 0, None)
        pc = (ctypes.c_uint32 * 1)(nt)
        vk.vkCmdPushConstants(cmd, mlayout, _STAGE_COMPUTE, 0, 4, ctypes.byref(pc))
        vk.vkCmdDispatch(cmd, (pairs + 255) // 256, 1, 1)
        barrier(dst_stage=_STAGE_COMPUTE_BIT | _STAGE_DRAW_INDIRECT_BIT,
                dst_access=_ACCESS_SHADER_READ | _ACCESS_SHADER_WRITE | _ACCESS_INDIRECT_READ)
        self._stamp(cmd, "mark")
        lname = "forward_listed_%d.spv" % n
        lpipe, llayout, lsl = self._build_pipeline(("listed", n), lname, 4, 4)
        ds = self._descriptor_set(lsl, [series_b, starts_b, b["data"], b["blocks"]],
                                  [0, r0 * 4, 0, 0] if r0 else None)
        vk.vkCmdBindPipeline(cmd, _BIND_POINT_COMPUTE, lpipe)
        vk.vkCmdBindDescriptorSets(cmd, _BIND_POINT_COMPUTE, llayout, 0, 1, (_vp * 1)(ds), 0, None)
        pc = (ctypes.c_uint32 * 1)(nser)
        vk.vkCmdPushConstants(cmd, llayout, _STAGE_COMPUTE, 0, 4, ctypes.byref(pc))
        vk.vkCmdDispatchIndirect(cmd, b["bargs"].handle, 0)
        barrier()

    def _band_forward(self, storage_key, b, bands, nd):
        """The band-only forward writing b["bands"]: a recording of its own (phase
        "forward"), swapped in for the pending full forward of the same spectra."""
        B, (n, series_b, starts_b, r0, count, nser, slot, _cmd) = bands
        fkey = ("bandfwd", storage_key, _band_key(bands))
        forwards = self.__dict__.setdefault("_forwards", {})
        rec = forwards.get(fkey)
        if rec is not None:
            self._cache_touch('forward', fkey)
            return fkey, rec
        pipe, layout, sl = self._build_pipeline(("bands", n), "forward_bands_%d.spv" % n, 3, 8)
        pool_start = len(getattr(self, '_pools', []))
        ds = self._descriptor_set(sl, [series_b, starts_b, b["bands"]],
                                  [0, r0 * 4, 0] if r0 else None)
        self._capture_begin()
        cmd = None
        try:
            rec = _Recording(self, "band forward")
            cmd = rec.cmd
            rec.stamp("start")
            rec.bind((pipe, layout), ds, (nser, B))
            rec.dispatch(nd)
            rec.barrier()
            rec.stamp("forward")
            rec.end()
        finally:
            self._capture_end(cmd)
        # A forward record like any other, tied to the storage whose band buffer it writes.
        forwards[fkey] = (cmd,)          # buffers belong to the storage and the caller
        self._register_record('forward', fkey, storage_key, pool_start)
        return fkey, forwards[fkey]

    def _band_measure(self, n, B, nd, nt, bufs, surv_key, count):
        """The fraction of blocks the refine touched, for the next call's choice."""
        if count <= 0:
            f = 0.0
        else:
            f = len(np.unique(bufs[surv_key].view(np.uint32, count) // nt)) / float(nd)
        self.__dict__.setdefault("_band_f", {})[(n, B, nd, nt)] = f
        from . import gatechain as _gc           # forward pricing uses the measured fraction
        _gc.note_refine_blocks(n, B, f)

    def hier_peaks_grouped(self, n, band, data, tmpl, ct0, raw_thr, groups, binsize, threshold,
                           *, upload_tmpl=True, cascade_band=None, ct1=None, raw_thr1=None,
                           slot=None, async_submit=False, sparse=False, nbins=None,
                           handle_out=None):
        """Hierarchical peaks over row ranges of one spectra batch, each with its own window,
        as ONE recording: every tier is a single dispatch over all rows.

        ``groups`` holds (lo, hi, a, b): rows a..b of ``data`` are searched over [lo, hi).
        The windows go to the kernels per row (gRowWin, mfRowWindows), so a series call's
        first, interior and last block groups no longer cost three dispatches per stage.
        Output bins follow the first group's bin count, as hier_peaks_grouped on CUDA."""
        return _hier_peaks_grouped(self, n, band, data, tmpl, ct0, raw_thr, groups, binsize,
                                   threshold, upload_tmpl=upload_tmpl, cascade_band=cascade_band,
                                   ct1=ct1, raw_thr1=raw_thr1, slot=slot,
                                   async_submit=async_submit, sparse=sparse, nbins=nbins,
                                   max_bins=_MAX_BINS, handle_out=handle_out)

    def empty_shared(self, shape, dtype=np.complex64, *, readback=False, host_input=False):
        factory = (lambda ctx, size: _Buffer(ctx, size, readback=True)) if readback else _Buffer
        return empty_shared(self, factory, shape, dtype)

    def _forward_fused(self, n, series, starts, spectra, *, defer=False, slot=None):
        """Dispatch fused forward FFT kernel path."""
        return self.forward(n, series, starts, spectra, defer=defer, slot=slot, fused=True)

    def forward(self, n, series, starts, spectra, *, defer=False, slot=None, fused=False, rows=None,
                handle_out=None):
        """Gather and normalize forward FFTs directly into shared spectra.

        handle_out (a list): receives (key, record) for forward_replay.

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
            self._capture_begin()
            rec = _Recording(self, "forward")
            cmd = rec.cmd
            rec.stamp("start")
            rec.bind((pipe, layout), ds, (series.size,))
            rec.dispatch(count)
            # The spectra are read next by shaders and by the host (0x2000, 0x4000).
            rec.barrier(dst_stage=_STAGE_COMPUTE_BIT | 0x4000,
                        dst_access=_ACCESS_SHADER_READ | 0x2000, buffer=buffers[2])
            rec.stamp("forward")
            rec.end()
            self._capture_end(cmd)
            batch = (*buffers, cmd)
            forwards[key] = batch
            self._register_record('forward', key, None, pool_start)
        self._cache_touch('forward', key)
        cmd = batch[-1]
        if handle_out is not None:
            handle_out.append((key, batch))
        if defer:
            if not isinstance(getattr(self, "_pending_forward", None), dict):
                self._pending_forward = {}
            self._pending_forward[slot] = cmd
            # A hierarchical call on these spectra may swap this forward for the band-only
            # one (_band_source): what it needs to recompute survivor rows itself.
            self.__dict__.setdefault("_fwd_src", {})[spectra.ctypes.data + r0 * n * 8] = (
                n, buffers[0], buffers[1], r0, count, int(series.size), slot, cmd)
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
            rec = _Recording(self, "two-stage forward")
            rec.bind((p1, l1), ds1, (series.size,))
            rec.dispatch(spectra.shape[0] * info['n1'])
            rec.barrier(buffer=scratch)
            rec.bind((p2, l2), ds2)
            rec.dispatch(spectra.shape[0] * info['n2'])
            # The spectra are read next by shaders and by transfers (0x2000, 0x4000).
            rec.barrier(dst_stage=_STAGE_COMPUTE_BIT | 0x4000,
                        dst_access=_ACCESS_SHADER_READ | 0x2000, buffer=buffers[2])
            cmd = rec.end()
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

    def _make_batch(self, key, n, nd, nt, nbins, binsize, shift, lo, hi, t2, data=None, tmpl=None):
        """Buffers, descriptor set and a recorded command buffer for one shape."""
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

        # NOT one-time-submit: this recording is replayed on every call.
        rec = _Recording(self, "peaks")
        rec.bind((pipe, layout), dset, (nt, lo, hi, binsize, shift, nbins,
                                        int(np.float32(t2).view(np.uint32))))
        rec.dispatch(nd * nt)
        return (b_data, b_tmpl, b_idx, b_val, rec.end())

    def _transient_peaks(self, storage_key, n, nd, nt, nbins, binsize, shift, lo, hi, t2):
        """(command buffer, descriptor pool) for one flat-peaks call on cached buffers."""
        filename = self._peak_file(n, nbins)
        pipe, layout, set_layout = self._build_pipeline(
            ("peaks", filename), filename, _NBIND, _PUSH_BYTES)
        pools = self.__dict__.setdefault("_pools", [])
        dset = self._descriptor_set(set_layout, self._storage[storage_key])
        pool = pools.pop()                       # owned by this call, not the cache
        rec = _Recording(self, "transient peaks", flags=1)    # ONE_TIME_SUBMIT
        rec.bind((pipe, layout), dset, (nt, lo, hi, binsize, shift, nbins,
                                        int(np.float32(t2).view(np.uint32))))
        rec.dispatch(nd * nt)
        return rec.end(), pool

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
        self._claim(b_idx)                       # an earlier result still reading these outputs

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
            return self._track(readback, owner=b_idx)
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
        shift = bin_shift(binsize)
        t2 = int(np.float32(float(threshold) ** 2 if threshold > 0 else 0).view(np.uint32))
        # Each item's output starts at the storage-buffer offset alignment (descriptor offsets).
        offs, nbs, size = plan_items(items, binsize, self.storage_offset_alignment // 4, _MAX_BINS)
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
        return split_items(items, offs, nbs, b_idx.read(np.int32, size),
                           b_val.read(np.complex64, size))

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
        # Each group's results start at the device's storage-buffer offset alignment.
        offsets, size, words = [], 0, self.storage_offset_alignment // 4
        for _, _, a, b in groups:
            offsets.append(size)
            size += -(-((b - a) * nt * nb) // words) * words
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
            rec = _Recording(self, "grouped peaks")
            for (lo, hi, a, b), offset in zip(groups, offsets):
                ds = self._descriptor_set(sl, bufs, (a*n*8, 0, offset*4, offset*8))
                rec.bind((pipe, layout), ds, (nt, lo, hi, binsize, shift, nb, int(t2)))
                rec.dispatch((b - a) * nt)
            for out in bufs[2:4]:                # the host reads the peaks (0x4000, 0x2000)
                rec.barrier(dst_stage=0x4000, dst_access=0x2000, buffer=out)
            batch = (*bufs, rec.end())
            self._batches[key] = batch
            self._register_record('flat', key, key, pool_start)
            upload_tmpl = True
        self._cache_touch('flat', key)
        _, b_tmpl, b_idx, b_val, cmd = batch
        self._claim(b_idx)                       # an earlier result still reading these outputs
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
            return self._track(readback, owner=b_idx)
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
            pipe = self._build_pipeline(('full', filename), filename, 3, 4)
            external = [b for a in (data, tmpl, out)
                        if (b := shared_buffer(a, self)) is not None]
            estimate = sum(a.nbytes for a in (data, tmpl, out)
                           if shared_buffer(a, self) is None)
            self._cache_room(estimate, incoming=external)
            pool_start = len(getattr(self, '_pools', []))
            bufs = (shared_buffer(data, self) or _Buffer(self, data.nbytes),
                    shared_buffer(tmpl, self) or _Buffer(self, tmpl.nbytes),
                    shared_buffer(out, self) or _Buffer(self, out.nbytes, readback=True))
            rec = _Recording(self, "full")
            rec.bind(pipe, self._descriptor_set(pipe[2], bufs), (nt,))
            rec.dispatch(nd * nt)
            batch = (*bufs, rec.end())
            self._full_batches[key] = batch
            self._register_record('full', key, None, pool_start)
            uploads = (True, True, *uploads[2:])
        self._cache_touch('full', key)
        bdata, btmpl, bout, cmd = batch
        self._write_uploads(key, uploads, bdata, data, btmpl, tmpl)
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
            rec = _Recording(self, "two-stage")
            rec.bind((p1, l1), ds1, (nt,))
            rec.dispatch(nd * nt * info['n1'])
            rec.barrier(buffer=scratch)
            rec.bind((p2, l2), ds2)
            rec.dispatch(nd * nt * info['n2'])
            batch = (bd, bt, scratch, bo, rec.end())
            self._tierc_batches[key] = batch
            self._register_record('tierc', key, None, pool_start)
            uploads = (True, True, *uploads[2:])
        self._cache_touch('tierc', key)
        bd, bt, scratch, bo, cmd = batch
        self._write_uploads(key, uploads, bd, data, bt, tmpl)
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

    def correlate_continuous(self, n, data, tmpl, starts, out, lo, hi,
                             *, upload_data=True, upload_tmpl=True, async_submit=False):
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
            rec = _Recording(self, "continuous")
            cmd = rec.cmd
            # Ordered against neighbouring work on this queue without a host wait: earlier
            # readers of `out` (last segment's fine stage) finish first, and later readers
            # see these writes (correlate_series(wait=False) leaves this in flight).
            _global_barrier(self.vk, cmd)
            if geometry:
                rec.bind((p1, l1), ds1, (nt,))
                rec.dispatch(nd * nt * geometry['n1'])
                rec.barrier(buffer=scratch)
                pipe, layout, ds = p2, l2, ds2
            rec.bind((pipe, layout), ds, (nt, length, lo, hi))
            rec.dispatch(nd * nt * (geometry['n2'] if geometry else 1))
            _global_barrier(self.vk, cmd)
            rec.end()
            batch = ((bd, bt, scratch, bs, bo, cmd) if geometry
                     else (bd, bt, bs, bo, cmd))
            cache[key] = batch
            self._register_record('tierc' if geometry else 'full', key, None, pool_start)
            uploads = (True, True, *uploads[2:])
        self._cache_touch('tierc' if geometry else 'full', key)
        bd, bt = batch[:2]
        self._write_uploads(key, uploads, bd, data, bt, tmpl)
        if async_submit:
            self._submit_pending(batch[-1])
        else:
            self._submit(batch[-1])

    def _submit_pending(self, cmd):
        """Submit on the main queue and leave it in flight (see _Device.pending_writes)."""
        fence = _vp()
        _check(self.vk.vkCreateFence(self.device, ctypes.byref(_FenceCreate(8, None, 0)), None,
                                     ctypes.byref(fence)), "vkCreateFence")
        try:
            self._submit(cmd, fence=fence, wait=False)
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

    #: correlate_continuous(async_submit=True) leaves the last batch in flight; a later call
    #: settles it before rewriting the workspaces it reads (_continuous_gpu).
    defers_continuous = True
    #: zero_columns_done(wait=False) leaves the zeroing in flight.
    async_zero = True

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
        self.__dict__.get("_c16_template_exp", {}).pop(key, None)

    def _evict_record(self, kind, key, keep_storage=None):
        # An in-flight readback reads this record's buffers when collected.
        self._drain()
        token = (kind, key)
        batch = self._record_tables()[kind].pop(key)
        if kind in ('hier', 'hier_cascade'):
            self.__dict__.get("_pviews", {}).pop(id(batch[0]), None)
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
        self._free_zero_recs()
        self._submit(None)
        self._wait_queues()
        self.vk.vkFreeCommandBuffers.argtypes = [_vp, _vp, _u32, ctypes.POINTER(_vp)]
        self._evict_all()
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
