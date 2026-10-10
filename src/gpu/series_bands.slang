// BAND-ONLY FORWARD (docs/vulkan-8060s-roofline.md section 12, option (a)).
//
// Appended to tierb.slang + series_forward.slang at NLEN = n, like the shipped forward.
// The hierarchical tiers read only a band of every block's spectrum; refine reads the
// full spectrum of the few blocks that have a survivor (8.7% of a realistic segment's).
// Writing every block's full n-point spectrum to DRAM and reading it back was 85% of a
// fine segment's DRAM bytes for 4% of its flops. So:
//   seriesForwardBands   every block: the first B bins only (fp32), into `bands`
//   markBlocks           the distinct blocks among the refine's survivor pairs
//   seriesForwardListed  those blocks only: their full spectra, into their own rows
// Same transform, same output order and normalisation as seriesForward: the band rows are
// bit-equal to the full spectra's first B bins, and the listed rows to theirs.

[shader("compute")][numthreads(WG,1,1)]
void seriesForwardBands(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                        StructuredBuffer<float2> series,
                        StructuredBuffer<uint> starts,
                        RWStructuredBuffer<float2> bands,
                        uniform uint seriesLength, uniform uint B)
{
    uint tid = lid.x;
    _tid = tid;
    _stgBase = 0;
    uint start = starts[gid.x];
    C r[RADIX];
    [unroll] for (uint k = 0; k < R; ++k) {
        uint offset = tid + WG*k;
        float2 x = float2(0, 0);
        if (start < seriesLength && offset < seriesLength - start)
            x = series[start + offset];
        r[k] = C(x.x / float(N), -x.y / float(N));
    }
    forwardTransform(r, tid);
    [unroll] for (uint k = 0; k < R; ++k) {
        uint index = slotToIndex(tid * R + k);
        if (index < B)
            bands[gid.x * B + index] = float2(r[k].x, -r[k].y);
    }
}

//: The distinct data blocks among `count` survivor pairs (count = countArgs[0]; pair
//: p is block p / ntmpl). flags[] must be zero on entry; the blocks land in
//: blockList[0 .. blockArgs[0]) in no particular order, blockArgs being an indirect
//: dispatch's group count. Dispatched over an upper bound; lanes past the count exit.
[shader("compute")][numthreads(256,1,1)]
void markBlocks(uint3 gid: SV_DispatchThreadID,
                StructuredBuffer<uint> survivors,
                StructuredBuffer<uint> countArgs,
                RWStructuredBuffer<uint> flags,
                RWStructuredBuffer<uint> blockList,
                RWStructuredBuffer<uint> blockArgs,
                uniform uint ntmpl)
{
    uint k = gid.x;
    if (k >= countArgs[0])
        return;
    uint d = survivors[k] / ntmpl;
    uint was;
    InterlockedExchange(flags[d], 1u, was);
    if (was == 0u) {
        uint slot;
        InterlockedAdd(blockArgs[0], 1u, slot);
        blockList[slot] = d;
    }
}

//: seriesForward for the listed blocks only, each written to its own row.
[shader("compute")][numthreads(WG,1,1)]
void seriesForwardListed(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                         StructuredBuffer<float2> series,
                         StructuredBuffer<uint> starts,
                         RWStructuredBuffer<float2> spectra,
                         StructuredBuffer<uint> blockList,
                         uniform uint seriesLength)
{
    uint tid = lid.x;
    _tid = tid;
    _stgBase = 0;
    uint row = blockList[gid.x];
    uint start = starts[row];
    C r[RADIX];
    [unroll] for (uint k = 0; k < R; ++k) {
        uint offset = tid + WG*k;
        float2 x = float2(0, 0);
        if (start < seriesLength && offset < seriesLength - start)
            x = series[start + offset];
        r[k] = C(x.x / float(N), -x.y / float(N));
    }
    forwardTransform(r, tid);
    [unroll] for (uint k = 0; k < R; ++k) {
        uint index = slotToIndex(tid * R + k);
        spectra[row * N + index] = float2(r[k].x, -r[k].y);
    }
}
