// PROTOTYPE (not built by tools/build_spirv.py): the series forward transform writing
// only what the hierarchical tiers read, instead of the full n-point spectra.
//
// Appended to tierb.slang + series_forward.slang at NLEN = n, like the shipped forward.
// Per block it writes
//   bands1[block * B1 + k]   k < B1   fp32, the second tier's band (refine and later
//                                     tiers recompute full spectra for survivor blocks)
//   bands0[block * B0 + k]   k < B0   packed fp16 (real low half), the first tier's band
// against 2 x n x 8 bytes of full spectra written and re-read today. See
// docs/vulkan-8060s-roofline.md section 12 for the accounting.
//
// push: seriesLength, B0, B1 (powers of two, B0 <= B1 <= NLEN).
[shader("compute")][numthreads(WG,1,1)]
void seriesForwardBands(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                        StructuredBuffer<float2> series,
                        StructuredBuffer<uint> starts,
                        RWStructuredBuffer<float2> bands1,
                        RWStructuredBuffer<uint> bands0,
                        uniform uint seriesLength, uniform uint B0, uniform uint B1)
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
        float2 v = float2(r[k].x, -r[k].y);
        if (index < B1)
            bands1[gid.x * B1 + index] = v;
        if (index < B0)
            bands0[gid.x * B0 + index] = f32tof16(v.x) | (f32tof16(v.y) << 16);
    }
}
