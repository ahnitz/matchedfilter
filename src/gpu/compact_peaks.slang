// Sparse peak readback (CUDA build only; tools/build_ptx.py -> compact_peaks.ptx).
//
// A fine-stage call writes a dense (blocks, templates, bins) table in which almost every
// entry is -1 at a detection threshold. Reading the dense table back, widening it and
// scanning it on the host cost more than the device call itself. This compacts it on the
// device into (flat index, sample index, value) records behind an atomic count; the host
// reads the count and the records and sorts them (the order of atomics is not fixed).
[shader("compute")][numthreads(256,1,1)]
void compactPeaks(uint3 tid: SV_DispatchThreadID,
                  StructuredBuffer<int> peakIdx,
                  StructuredBuffer<float2> peakVal,
                  RWStructuredBuffer<uint> count,
                  RWStructuredBuffer<uint4> list,
                  uniform uint total, uniform uint cap)
{
    uint i = tid.x;
    if (i >= total) return;
    int k = peakIdx[i];
    if (k < 0) return;
    uint slot;
    InterlockedAdd(count[0], 1u, slot);
    if (slot < cap) {
        float2 v = peakVal[i];
        list[slot] = uint4(i, uint(k), asuint(v.x), asuint(v.y));
    }
}
