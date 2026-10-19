// Extract a coarse band from full spectra on the device: the band rows a tier reads when its
// kernel cannot read the spectra in place (a fixed row length, _gpuhier "pack" feed). packed
// != 0 writes the fp16 tier's form, each value times scaleBits (an exact power of two as float
// bits, the tier's data scale: the rounding the in-place read applies, tierb.slang dload);
// otherwise fp32, unscaled.
[shader("compute")][numthreads(256,1,1)]
void packCoarse(uint3 tid: SV_DispatchThreadID,
                StructuredBuffer<float2> data,
                RWStructuredBuffer<uint> coarse,
                uniform uint n, uniform uint band,
                uniform uint count, uniform uint packed, uniform uint scaleBits)
{
    uint i = tid.x;
    if (i >= count) return;
    // The host accepts only positive power-of-two coarse bands.
    float2 x = data[(i >> firstbithigh(band))*n + (i & (band-1))];
    if (packed != 0) {
        const float s = asfloat(scaleBits);
        coarse[i] = f32tof16(x.x * s) | (f32tof16(x.y * s) << 16);
    } else {
        coarse[2*i] = asuint(x.x);
        coarse[2*i+1] = asuint(x.y);
    }
}
