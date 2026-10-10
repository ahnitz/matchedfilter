// Intel Xe's native sin/cos approximation loses enough accuracy for an FFT
// twiddle recurrence to exceed the full-output contract. Specialize this at
// pipeline creation; other devices retain the original native instructions.
#ifdef MF_VULKAN
[[vk::constant_id(73)]] const uint mfAccurateTrig = 0;
[[vk::constant_id(74)]] const uint mfSubgroupSize = 32;
// Row stride of the DATA spectra, in complex elements; 0 means the kernel's own
// length. The hierarchical stages read their band straight out of the full
// n-point spectra (stride n) instead of a packed band copy.
[[vk::constant_id(75)]] const uint mfDataStride = 0;
// Per-row search windows (hier_peaks_grouped): 0 off, 1 the row's raw window
// [lo, hi), 2 that window mapped onto this kernel's coarse band. The rows'
// (lo, hi) come from the gRowWin buffer.
[[vk::constant_id(76)]] const uint mfRowWindows = 0;
// The fp16 coarse tier's error bound (C16_KAPPA): 1 applies it (the default the host
// uses), 0 reports the raw fp16 maximum -- for measuring the bound's margin use only.
[[vk::constant_id(77)]] const uint mfC16Bound = 1;
#else
static const uint mfDataStride = 0;
static const uint mfRowWindows = 0;
static const uint mfC16Bound = 1;
static const uint mfAccurateTrig = 0;
static const uint mfSubgroupSize = 32;
#endif

float2 mfTwiddle(float angle)
{
    if (mfAccurateTrig == 0)
        return float2(cos(angle), sin(angle));
    // Reduce to [-pi/4, pi/4]. Splitting pi/2 avoids cancellation near
    // quadrant boundaries. FFT callers supply angles within [0, 2*pi].
    int quadrant = int(floor(angle * 0.63661977236758134f + 0.5f));
    float x = (angle - float(quadrant)*1.5707962512969971f)
                    - float(quadrant)*7.5497894158615964e-8f;
    float z = x*x;
    float c = 1.0f + z*(-0.5f + z*(1.0f/24.0f + z*(-1.0f/720.0f
                   + z*(1.0f/40320.0f + z*(-1.0f/3628800.0f)))));
    float s = x*(1.0f + z*(-1.0f/6.0f + z*(1.0f/120.0f
                   + z*(-1.0f/5040.0f + z*(1.0f/362880.0f
                   + z*(-1.0f/39916800.0f))))));
    switch (quadrant & 3) {
        case 1: return float2(-s, c);
        case 2: return float2(-c, -s);
        case 3: return float2(s, -c);
        default: return float2(c, s);
    }
}
