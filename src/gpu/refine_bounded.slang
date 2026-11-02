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
                         uniform uint thrBits, uniform uint gridSize ROWWIN_PARAM CUDA_DATA_PARAM)
{
    CUDA_DATA_INIT
    uint total = count[0];
#if COARSE16
    if (total == 0u) return;
    const uint pairsPerWG = 2u * PPG;
#if PPG == 1
    uint sub = 0u, tid = lid.x;
    _stgBase = 0;
#else
    uint sub = lid.x / WG, tid = lid.x % WG;
    _stgBase = sub * STGW;
#endif
    for (uint base = gid.x * pairsPerWG; base < total; base += gridSize * pairsPerWG) {
        uint idxA = base + 2u * sub;
        uint idxB = idxA + 1u;
        uint pairA = (idxA < total) ? survivors[idxA] : NOPAIR;
        uint pairB = (idxB < total) ? survivors[idxB] : NOPAIR;
        uint refPairA = (pairA != NOPAIR) ? pairA : survivors[total - 1u];
        uint refPairB = (pairB != NOPAIR) ? pairB : refPairA;
        uint dA = refPairA / ntmpl, tA = refPairA % ntmpl;
        uint dB = refPairB / ntmpl, tB = refPairB % ntmpl;
        uint wsA = winStart, weA = winEnd, wsB = winStart, weB = winEnd;
        rowWindow(dA, wsA, weA ROWWIN_ARG);
        rowWindow(dB, wsB, weB ROWWIN_ARG);
        filterTwoListed(pairA, pairB, dA, tA, dB, tB, tid, data, tmpl, peakIdx, peakVal,
                        wsA, weA, wsB, weB, nbins, thrBits);
#if defined(MF_VULKAN)
        if (base + gridSize * pairsPerWG < total)
            GroupMemoryBarrierWithGroupSync();
#endif
    }
#else
    for (uint i = gid.x; i < total; i += gridSize) {
        _stgBase = 0;
        uint pair = survivors[i], ws = winStart, we = winEnd;
        rowWindow(pair / ntmpl, ws, we ROWWIN_ARG);       // per-row windows (tierb.slang)
        filterPair(pair, lid.x, data, tmpl, peakIdx, peakVal, ntmpl,
                   ws, we, binsize, binShift, nbins, thrBits ROWWIN_COARSE_ARG);
        GroupMemoryBarrierWithGroupSync();
    }
#endif
}

#if !COARSE16
// Follow-up items, sized on the device (CUDA). Each list entry is a (data row, template,
// window) the host built (_gpuhost.followup_layout): six uints (d, t, lo, hi, out, phase).
// The pair d*ntmpl + t is searched over [lo, hi) in bins of binsize numbered from
// lo - phase (the follow-up window's bin grid), and its nbins peaks land at output slot
// `out`, so the output is as compact as the list. Same grid-stride form as refineListedBounded: the count is
// read on the device, and lanes past it do nothing.
[shader("compute")][numthreads(WG*PPG,1,1)]
void refineItems(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                 StructuredBuffer<CVal> data, StructuredBuffer<CVal> tmpl,
                 RWStructuredBuffer<int> peakIdx,
                 RWStructuredBuffer<float2> peakVal,
                 StructuredBuffer<uint> items,
                 StructuredBuffer<uint> count,
                 uniform uint ntmpl, uniform uint binsize, uniform int binShift,
                 uniform uint nbins, uniform uint thrBits, uniform uint gridSize)
{
    uint total = count[0];
    for (uint i = gid.x; i < total; i += gridSize) {
        _stgBase = 0;
        uint d = items[6u * i], t = items[6u * i + 1u];
        _binPhase = items[6u * i + 5u];
        filterPairOut(d * ntmpl + t, items[6u * i + 4u], lid.x, data, tmpl, peakIdx, peakVal,
                      ntmpl, items[6u * i + 2u], items[6u * i + 3u], binsize, binShift, nbins,
                      thrBits);
        GroupMemoryBarrierWithGroupSync();
    }
}
#endif
