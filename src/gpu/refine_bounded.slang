// Appended to tierb.slang by tools/build_ptx.py for the CUDA refine (refine_<n>.ptx).
//
// CUDA has no indirect dispatch, so the survivor count cannot size the launch
// the way vkCmdDispatchIndirect does, and reading it back to the host between
// the compaction and the refine costs a full round trip per call. Instead the
// host launches a fixed grid (the device's resident capacity, capped at the
// pair count) and each block strides over the compacted list up to the count
// the compaction left in count[0].
//
// The loop bound is block-uniform, so the barriers inside filterPair stay
// legal. The barrier at the end of each iteration keeps the next transform's
// staging writes from racing the previous peak election's reads.
[shader("compute")][numthreads(WG*PPG,1,1)]
void refineListedBounded(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                         StructuredBuffer<CVal> data, StructuredBuffer<CVal> tmpl,
                         RWStructuredBuffer<int> peakIdx,
                         RWStructuredBuffer<float2> peakVal,
                         StructuredBuffer<uint> survivors,
                         StructuredBuffer<uint> count,
                         uniform uint ntmpl, uniform uint winStart, uniform uint winEnd,
                         uniform uint binsize, uniform int binShift, uniform uint nbins,
                         uniform uint thrBits, uniform uint gridSize)
{
    uint total = count[0];
    for (uint i = gid.x; i < total; i += gridSize) {
        _stgBase = 0;
        filterPair(survivors[i], lid.x, data, tmpl, peakIdx, peakVal, ntmpl,
                   winStart, winEnd, binsize, binShift, nbins, thrBits);
        GroupMemoryBarrierWithGroupSync();
    }
}
