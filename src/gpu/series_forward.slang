void forwardTransform(inout C r[RADIX], uint tid)
{
#include "fft_transform.slang"
}

// A series sample. With MF_SERIES_LAYOUT the forwards also take a real series without the
// host widening it: seriesLayout 0 reads complex samples; otherwise sample i is float
// (seriesLayout >> 2) + (seriesLayout & 3) * i of the buffer read as floats, imaginary part
// zero -- one lane of a packed complex row (stride 2, lane 0 or 1) or a real series
// (stride 1). The layout is uniform across a dispatch, so the branch costs nothing.
#ifdef MF_SERIES_LAYOUT
float2 seriesSample(StructuredBuffer<float2> series, uint i, uint layout)
{
    if (layout == 0)
        return series[i];
    uint f = (layout >> 2) + (layout & 3) * i;
    float2 p = series[f >> 1];
    return float2((f & 1) != 0 ? p.y : p.x, 0);
}
#define SERIES_LAYOUT , uniform uint seriesLayout
#define SERIES_AT(i) seriesSample(series, (i), seriesLayout)
#else
#define SERIES_LAYOUT
#define SERIES_AT(i) series[(i)]
#endif

// Appended to tierb.slang by build_forward.py: share its exact butterflies,
// staging exchange, and output permutation. FFT(x)/N = conj(IFFT(conj(x)/N)).
[shader("compute")][numthreads(WG,1,1)]
void seriesForward(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                   StructuredBuffer<float2> series,
                   StructuredBuffer<uint> starts,
                   RWStructuredBuffer<float2> spectra,
                   uniform uint seriesLength SERIES_LAYOUT)
{
    uint tid = lid.x;
    _tid = tid;
    _stgBase = 0;
    uint start = starts[gid.x];
    C r[RADIX];
    [unroll] for (uint k = 0; k < R; ++k) {
        uint offset = tid + WG*k;
        float2 x = float2(0, 0);
        // Subtraction avoids wraparound for starts beyond the input tail.
        if (start < seriesLength && offset < seriesLength - start)
            x = SERIES_AT(start + offset);
        r[k] = C(x.x / float(N), -x.y / float(N));
    }
    forwardTransform(r, tid);
    [unroll] for (uint k = 0; k < R; ++k) {
        uint index = slotToIndex(tid * R + k);
        spectra[gid.x*N + index] = float2(r[k].x, -r[k].y);
    }
}
