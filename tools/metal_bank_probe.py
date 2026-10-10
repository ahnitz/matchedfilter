#!/usr/bin/env python3
"""Measure the threadgroup-memory bank geometry of a Metal device.

Neither Metal nor Apple documents the bank count, and the coarse kernel's exchange padding
(tools/coarse_layout.py) is chosen from a bank model. This times a SIMD group's 32 lanes
each reading word (lane * stride) of threadgroup memory, in a dependent chain, for strides
1..64. A stride that maps k lanes onto one bank takes ~k times as long, so the time against
stride reveals the bank count (the smallest stride with the full 32-way slowdown) and the
access width. Device-timed (GPUStartTime/GPUEndTime), min of --reps.

    python tools/metal_bank_probe.py [--reps 5]
"""
import argparse
import ctypes
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from matchedfilter import _mtlcompute as M  # noqa: E402

SRC = r"""
#include <metal_stdlib>
using namespace metal;
kernel void probe(device uint *out [[buffer(0)]], constant uint &stride [[buffer(1)]],
                  constant uint &iters [[buffer(2)]],
                  uint tid [[thread_position_in_threadgroup]]) {
    threadgroup uint buf[8192];
    for (uint i = tid; i < 8192; i += 32) buf[i] = (i * 2654435761u) & 0;
    threadgroup_barrier(mem_flags::mem_threadgroup);
    uint idx = (tid * stride) & 8191u;
    uint acc = 0;
    for (uint k = 0; k < iters; ++k) {
        acc += buf[idx];
        idx = (idx + acc) & 8191u;          // dependent: buf is all zero, idx unchanged
    }
    out[tid] = acc;
}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--iters", type=int, default=4096)
    ap.add_argument("--groups", type=int, default=4096)
    a = ap.parse_args()
    ctx = M.Context(0)
    o = ctx.o
    err = ctypes.c_void_p()
    lib = o.call(ctx.device, b"newLibraryWithSource:options:error:",
                 args=(o.nsstring(SRC), None, ctypes.byref(err)),
                 argtypes=(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p))
    fn = o.call(lib, b"newFunctionWithName:", args=(o.nsstring("probe"),), argtypes=(ctypes.c_void_p,))
    pso = o.call(ctx.device, b"newComputePipelineStateWithFunction:error:",
                 args=(fn, ctypes.byref(err)), argtypes=(ctypes.c_void_p, ctypes.c_void_p))
    width = int(o.call(pso, b"threadExecutionWidth", restype=ctypes.c_ulong))
    out = M._Buffer(ctx, 32 * 4)
    print("device %s, threadExecutionWidth %d" % (ctx.name, width))
    base = None
    for stride in range(1, 65):
        best = None
        for _ in range(a.reps):
            cmd = o.call(ctx.queue, b"commandBuffer")
            enc = o.call(cmd, b"computeCommandEncoder")
            o.call(enc, b"setComputePipelineState:", restype=None, args=(pso,), argtypes=(ctypes.c_void_p,))
            o.call(enc, b"setBuffer:offset:atIndex:", restype=None, args=(out.handle, 0, 0),
                   argtypes=(ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong))
            for slot, v in ((1, stride), (2, a.iters)):
                c = ctypes.c_uint32(v)
                o.call(enc, b"setBytes:length:atIndex:", restype=None, args=(ctypes.byref(c), 4, slot),
                       argtypes=(ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong))
            o.call(enc, b"dispatchThreadgroups:threadsPerThreadgroup:", restype=None,
                   args=(M._MTLSize(a.groups, 1, 1), M._MTLSize(32, 1, 1)),
                   argtypes=(M._MTLSize, M._MTLSize))
            o.call(enc, b"endEncoding", restype=None)
            o.call(cmd, b"commit", restype=None)
            o.call(cmd, b"waitUntilCompleted", restype=None)
            t = (o.call(cmd, b"GPUEndTime", restype=ctypes.c_double)
                 - o.call(cmd, b"GPUStartTime", restype=ctypes.c_double))
            best = t if best is None else min(best, t)
        base = base or best
        print("stride %2d  %.3f ms  x%.2f" % (stride, best * 1e3, best / base))


if __name__ == "__main__":
    main()
