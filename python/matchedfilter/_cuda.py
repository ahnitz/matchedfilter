"""Enumerate and interface with NVIDIA CUDA devices via the CUDA Driver API.

Uses libcuda.so.1 directly through ctypes, without requiring CUDA Toolkit,
nvcc, pycuda, cupy, or runtime compilation.

Every NVIDIA driver installation provides libcuda.so.1 (Linux) or nvcuda.dll
(Windows), ensuring zero-dependency execution across workstations, cloud VMs,
and headless compute clusters.
"""
import ctypes
import os
import platform
import sys

_CUDA_SUCCESS = 0

_CUDA_DEVICE_ATTR_COMPUTE_CAPABILITY_MAJOR = 75
_CUDA_DEVICE_ATTR_COMPUTE_CAPABILITY_MINOR = 76
_CUDA_DEVICE_ATTR_MULTIPROCESSOR_COUNT = 16
_CUDA_DEVICE_ATTR_WARP_SIZE = 10
_CUDA_DEVICE_ATTR_MAX_THREADS_PER_BLOCK = 1
_CUDA_DEVICE_ATTR_MAX_SHARED_MEMORY_PER_BLOCK = 8


class CudaError(RuntimeError):
    """Raised when a CUDA Driver API call returns non-zero."""
    def __init__(self, code, func_name=""):
        self.code = code
        self.func_name = func_name
        super().__init__(f"CUDA Driver API error {code} in {func_name}")


_LIB_CACHE = None
_INIT_ATTEMPTED = False
_INIT_SUCCESS = False


def _find_cuda_lib():
    """Locate the system libcuda library."""
    if sys.platform.startswith("win"):
        candidates = ["nvcuda.dll"]
    elif sys.platform == "darwin":
        return None  # CUDA unsupported on modern macOS
    else:
        candidates = [
            "libcuda.so.1",
            "libcuda.so",
            "/usr/lib/x86_64-linux-gnu/libcuda.so.1",
            "/usr/lib64/libcuda.so.1",
            "/usr/lib/libcuda.so.1",
        ]
    for c in candidates:
        try:
            return ctypes.CDLL(c)
        except OSError:
            continue
    return None


def get_cuda_lib():
    """Return the bound CUDA Driver API CDLL or raise RuntimeError."""
    global _LIB_CACHE
    if _LIB_CACHE is not None:
        return _LIB_CACHE

    lib = _find_cuda_lib()
    if lib is None:
        raise RuntimeError("NVIDIA CUDA driver library (libcuda.so.1 / nvcuda.dll) not found")

    # Driver & Context
    lib.cuInit.argtypes = [ctypes.c_uint]
    lib.cuInit.restype = ctypes.c_int

    lib.cuDriverGetVersion.argtypes = [ctypes.POINTER(ctypes.c_int)]
    lib.cuDriverGetVersion.restype = ctypes.c_int

    lib.cuDeviceGetCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
    lib.cuDeviceGetCount.restype = ctypes.c_int

    lib.cuDeviceGet.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int]
    lib.cuDeviceGet.restype = ctypes.c_int

    lib.cuDeviceGetName.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
    lib.cuDeviceGetName.restype = ctypes.c_int

    lib.cuDeviceGetPCIBusId.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
    lib.cuDeviceGetPCIBusId.restype = ctypes.c_int

    lib.cuDeviceTotalMem_v2.argtypes = [ctypes.POINTER(ctypes.c_size_t), ctypes.c_int]
    lib.cuDeviceTotalMem_v2.restype = ctypes.c_int

    lib.cuDeviceGetAttribute.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int]
    lib.cuDeviceGetAttribute.restype = ctypes.c_int

    lib.cuCtxCreate_v2.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint, ctypes.c_int]
    lib.cuCtxCreate_v2.restype = ctypes.c_int

    if hasattr(lib, "cuDevicePrimaryCtxRetain"):
        lib.cuDevicePrimaryCtxRetain.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
        lib.cuDevicePrimaryCtxRetain.restype = ctypes.c_int
    if hasattr(lib, "cuDevicePrimaryCtxRelease"):
        lib.cuDevicePrimaryCtxRelease.argtypes = [ctypes.c_int]
        lib.cuDevicePrimaryCtxRelease.restype = ctypes.c_int

    lib.cuCtxDestroy_v2.argtypes = [ctypes.c_void_p]
    lib.cuCtxDestroy_v2.restype = ctypes.c_int

    lib.cuCtxSetCurrent.argtypes = [ctypes.c_void_p]
    lib.cuCtxSetCurrent.restype = ctypes.c_int

    lib.cuCtxGetCurrent.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    lib.cuCtxGetCurrent.restype = ctypes.c_int

    lib.cuCtxSynchronize.argtypes = []
    lib.cuCtxSynchronize.restype = ctypes.c_int

    # Module & Function
    lib.cuModuleLoadData.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p]
    lib.cuModuleLoadData.restype = ctypes.c_int

    if hasattr(lib, "cuModuleLoadDataEx"):
        lib.cuModuleLoadDataEx.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_char_p,
            ctypes.c_uint,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_void_p),
        ]
        lib.cuModuleLoadDataEx.restype = ctypes.c_int

    lib.cuModuleUnload.argtypes = [ctypes.c_void_p]
    lib.cuModuleUnload.restype = ctypes.c_int

    lib.cuModuleGetFunction.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, ctypes.c_char_p]
    lib.cuModuleGetFunction.restype = ctypes.c_int

    lib.cuModuleGetGlobal_v2.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_size_t),
                                         ctypes.c_void_p, ctypes.c_char_p]
    lib.cuModuleGetGlobal_v2.restype = ctypes.c_int

    # Memory Management
    lib.cuMemAlloc_v2.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t]
    lib.cuMemAlloc_v2.restype = ctypes.c_int

    lib.cuMemFree_v2.argtypes = [ctypes.c_uint64]
    lib.cuMemFree_v2.restype = ctypes.c_int

    lib.cuMemAllocHost_v2.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_size_t]
    lib.cuMemAllocHost_v2.restype = ctypes.c_int

    if hasattr(lib, "cuMemAllocManaged"):
        lib.cuMemAllocManaged.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.c_uint]
        lib.cuMemAllocManaged.restype = ctypes.c_int

    lib.cuMemFreeHost.argtypes = [ctypes.c_void_p]
    lib.cuMemFreeHost.restype = ctypes.c_int

    lib.cuMemcpyHtoD_v2.argtypes = [ctypes.c_uint64, ctypes.c_void_p, ctypes.c_size_t]
    lib.cuMemcpyHtoD_v2.restype = ctypes.c_int

    lib.cuMemcpyDtoH_v2.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_size_t]
    lib.cuMemcpyDtoH_v2.restype = ctypes.c_int

    lib.cuMemcpyDtoD_v2.argtypes = [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_size_t]
    lib.cuMemcpyDtoD_v2.restype = ctypes.c_int

    lib.cuMemcpyHtoDAsync_v2.argtypes = [ctypes.c_uint64, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
    lib.cuMemcpyHtoDAsync_v2.restype = ctypes.c_int

    lib.cuMemcpyDtoHAsync_v2.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_size_t, ctypes.c_void_p]
    lib.cuMemcpyDtoHAsync_v2.restype = ctypes.c_int

    lib.cuMemsetD8_v2.argtypes = [ctypes.c_uint64, ctypes.c_ubyte, ctypes.c_size_t]
    lib.cuMemsetD8_v2.restype = ctypes.c_int

    lib.cuMemsetD32_v2.argtypes = [ctypes.c_uint64, ctypes.c_uint, ctypes.c_size_t]
    lib.cuMemsetD32_v2.restype = ctypes.c_int

    if hasattr(lib, "cuMemsetD32Async"):
        lib.cuMemsetD32Async.argtypes = [ctypes.c_uint64, ctypes.c_uint, ctypes.c_size_t, ctypes.c_void_p]
        lib.cuMemsetD32Async.restype = ctypes.c_int

    # Execution & Streams
    lib.cuLaunchKernel.argtypes = [
        ctypes.c_void_p,                              # f
        ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,  # gridDimX, Y, Z
        ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,  # blockDimX, Y, Z
        ctypes.c_uint,                                # sharedMemBytes
        ctypes.c_void_p,                              # hStream
        ctypes.POINTER(ctypes.c_void_p),              # kernelParams
        ctypes.POINTER(ctypes.c_void_p),              # extra
    ]
    lib.cuLaunchKernel.restype = ctypes.c_int

    lib.cuStreamCreate.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint]
    lib.cuStreamCreate.restype = ctypes.c_int

    lib.cuStreamDestroy_v2.argtypes = [ctypes.c_void_p]
    lib.cuStreamDestroy_v2.restype = ctypes.c_int

    lib.cuStreamSynchronize.argtypes = [ctypes.c_void_p]
    lib.cuStreamSynchronize.restype = ctypes.c_int

    # Events
    lib.cuEventCreate.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint]
    lib.cuEventCreate.restype = ctypes.c_int

    lib.cuEventDestroy_v2.argtypes = [ctypes.c_void_p]
    lib.cuEventDestroy_v2.restype = ctypes.c_int

    lib.cuEventRecord.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    lib.cuEventRecord.restype = ctypes.c_int

    lib.cuEventSynchronize.argtypes = [ctypes.c_void_p]
    lib.cuEventSynchronize.restype = ctypes.c_int

    lib.cuEventElapsedTime.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_void_p, ctypes.c_void_p]
    lib.cuEventElapsedTime.restype = ctypes.c_int

    # Optional entry points: bound when the driver has them, probed with hasattr.
    _opt = {
        "cuMemcpyDtoDAsync_v2": [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_size_t, ctypes.c_void_p],
        "cuMemcpyAsync": [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_size_t, ctypes.c_void_p],
        "cuMemsetD8Async": [ctypes.c_uint64, ctypes.c_ubyte, ctypes.c_size_t, ctypes.c_void_p],
        "cuMemsetD2D32Async": [ctypes.c_uint64, ctypes.c_size_t, ctypes.c_uint, ctypes.c_size_t,
                               ctypes.c_size_t, ctypes.c_void_p],
        "cuMemPrefetchAsync": [ctypes.c_uint64, ctypes.c_size_t, ctypes.c_int, ctypes.c_void_p],
        "cuMemAdvise": [ctypes.c_uint64, ctypes.c_size_t, ctypes.c_int, ctypes.c_int],
        "cuFuncGetAttribute": [ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_void_p],
        "cuFuncSetAttribute": [ctypes.c_void_p, ctypes.c_int, ctypes.c_int],
        "cuOccupancyMaxActiveBlocksPerMultiprocessor": [
            ctypes.POINTER(ctypes.c_int), ctypes.c_void_p, ctypes.c_int, ctypes.c_size_t],
        "cuStreamWaitEvent": [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint],
        "cuEventQuery": [ctypes.c_void_p],
        "cuMemGetInfo_v2": [ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)],
        "cuMemHostRegister_v2": [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint],
        "cuMemHostUnregister": [ctypes.c_void_p],
        "cuStreamBeginCapture_v2": [ctypes.c_void_p, ctypes.c_int],
        "cuStreamEndCapture": [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
        "cuGraphInstantiateWithFlags": [ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
                                        ctypes.c_ulonglong],
        "cuGraphLaunch": [ctypes.c_void_p, ctypes.c_void_p],
        "cuGraphExecDestroy": [ctypes.c_void_p],
        "cuGraphDestroy": [ctypes.c_void_p],
    }
    for name, argtypes in _opt.items():
        if hasattr(lib, name):
            fn = getattr(lib, name)
            fn.argtypes = argtypes
            fn.restype = ctypes.c_int

    _LIB_CACHE = lib
    return lib


_NVML = None


def nvml_sm_clock(pci_bus_id):
    """A callable giving the current SM clock (MHz) of the GPU at ``pci_bus_id``, or None.

    NVML ships with the driver (libnvidia-ml); the PCI bus id maps a CUDA device to its NVML
    handle whatever CUDA_VISIBLE_DEVICES says."""
    global _NVML
    if _NVML is None:
        _NVML = False
        for name in ("libnvidia-ml.so.1", "libnvidia-ml.so"):
            try:
                lib = ctypes.CDLL(name)
            except OSError:
                continue
            if lib.nvmlInit_v2() == 0:
                _NVML = lib
            break
    if not _NVML:
        return None
    handle = ctypes.c_void_p()
    if _NVML.nvmlDeviceGetHandleByPciBusId_v2(pci_bus_id, ctypes.byref(handle)) != 0:
        return None
    mhz = ctypes.c_uint()

    def clock():
        if _NVML.nvmlDeviceGetClockInfo(handle, 1, ctypes.byref(mhz)) != 0:   # 1: NVML_CLOCK_SM
            return None
        return float(mhz.value)
    return clock if clock() else None


def check_cuda(result, func_name=""):
    """Check a CUDA Driver API result code."""
    if result != _CUDA_SUCCESS:
        raise CudaError(result, func_name)


def enumerate_devices():
    """Enumerate NVIDIA CUDA devices. Returns (devices, reason). Never raises."""
    global _INIT_ATTEMPTED, _INIT_SUCCESS
    try:
        lib = get_cuda_lib()
    except Exception as exc:
        return [], str(exc)

    if not _INIT_ATTEMPTED:
        _INIT_ATTEMPTED = True
        res = lib.cuInit(0)
        _INIT_SUCCESS = (res == _CUDA_SUCCESS)

    if not _INIT_SUCCESS:
        return [], "cuInit failed"

    count = ctypes.c_int(0)
    res = lib.cuDeviceGetCount(ctypes.byref(count))
    if res != _CUDA_SUCCESS or count.value <= 0:
        return [], "no CUDA devices reported by driver"

    devices = []
    for i in range(count.value):
        dev = ctypes.c_int()
        if lib.cuDeviceGet(ctypes.byref(dev), i) != _CUDA_SUCCESS:
            continue
        name_buf = ctypes.create_string_buffer(256)
        lib.cuDeviceGetName(name_buf, len(name_buf), dev.value)
        name = name_buf.value.decode("utf-8", "replace").strip()

        major = ctypes.c_int(0)
        minor = ctypes.c_int(0)
        mp_count = ctypes.c_int(0)
        lib.cuDeviceGetAttribute(ctypes.byref(major), _CUDA_DEVICE_ATTR_COMPUTE_CAPABILITY_MAJOR, dev.value)
        lib.cuDeviceGetAttribute(ctypes.byref(minor), _CUDA_DEVICE_ATTR_COMPUTE_CAPABILITY_MINOR, dev.value)
        lib.cuDeviceGetAttribute(ctypes.byref(mp_count), _CUDA_DEVICE_ATTR_MULTIPROCESSOR_COUNT, dev.value)

        total_mem = ctypes.c_size_t(0)
        lib.cuDeviceTotalMem_v2(ctypes.byref(total_mem), dev.value)

        devices.append({
            "index": i,
            "name": name,
            "vendor": 0x10DE,
            "kind": "discrete",
            "major": major.value,
            "minor": minor.value,
            "cc": f"sm_{major.value}{minor.value}",
            "multiprocessors": mp_count.value,
            "memory": total_mem.value,
        })

    return devices, ""
