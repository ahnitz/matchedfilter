// FORWARD + TIER-0 BANDS (fused forward of the hierarchical fine stage).
//
// Appended to tierb.slang + series_forward.slang (+ series_bands.slang, whose markBlocks and
// seriesForwardListed recompute the full spectra of the blocks the refine reads) at
// NLEN = n, like the shipped forward. One pass per block writes only what the tiers read:
//
//   band0  the first B0 bins times 2^scale (scaleBits: an exact power of two as float bits,
//          the fp16 tier's data scale, twiddle.slang mfDataScaleBits), packed as the fp16
//          tier-0 gate reads them (one uint per bin: f32tof16(re) | f32tof16(im) << 16, the
//          rounding the gate applies when it reads the spectra in place)
//   band1  the first B1 bins in fp32 (the next tier's band; B1 = 0 writes none)
//
// No full spectrum is written: it was ~430 MB per realistic M2 fine segment, read back only
// for the few blocks with a refine survivor, which seriesForwardListed recomputes. Same
// transform, output order and normalisation as seriesForward, so band0/band1 are bit-equal
// to packCoarse applied to seriesForward's spectra. Geometry (WG, R, staging) is the build's
// per-backend choice from API limits (threadgroup memory, SIMD width), as for seriesForward.

[shader("compute")][numthreads(WG,1,1)]
void forwardTier0(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                  StructuredBuffer<float2> series,
                  StructuredBuffer<uint> starts,
                  RWStructuredBuffer<uint> band0,
                  RWStructuredBuffer<float2> band1,
                  uniform uint seriesLength, uniform uint B0, uniform uint B1,
                  uniform uint scaleBits SERIES_LAYOUT)
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
            x = SERIES_AT(start + offset);
        r[k] = C(x.x / float(N), -x.y / float(N));
    }
    forwardTransform(r, tid);
    [unroll] for (uint k = 0; k < R; ++k) {
        uint index = slotToIndex(tid * R + k);
        float2 v = float2(r[k].x, -r[k].y);
        if (index < B0) {
            const float s = asfloat(scaleBits);
            band0[gid.x * B0 + index] = f32tof16(v.x * s) | (f32tof16(v.y * s) << 16);
        }
        if (index < B1)
            band1[gid.x * B1 + index] = v;
    }
}
