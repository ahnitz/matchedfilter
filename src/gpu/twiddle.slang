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
// Per-row search windows (hier_peaks_grouped): 0 off, 1 the row's window [lo, hi) from
// the gRowWin buffer, in this kernel's own samples (a coarse tier's mapped onto its band
// by the host).
[[vk::constant_id(76)]] const uint mfRowWindows = 0;
// The fp16 coarse tier's data scale, as float bits (1.0 by default): an exact power of
// two applied to each data element before it is rounded to half (tierb.slang dload), so
// the tier's values sit where fp16 holds them whatever the caller's units. The host
// scales the packed templates and the tier's threshold to match (_vkcompute._c16_scales).
[[vk::constant_id(79)]] const uint mfDataScaleBits = 0x3f800000u;
// The untiled fp16 coarse transform's inter-level twiddles: 1 from the build's fp16 table
// (COARSE_TWT), 0 from an fp32 recurrence. A measured per-device choice (_vkcompute
// _coarse_layouts): the table was 7% faster on a Radeon 8060S and 1.3-7x slower on an
// Iris Xe, whose table loads cost more than the recurrence's arithmetic.
[[vk::constant_id(80)]] const uint mfCoarseTwt = 1;
#elif defined(MF_CUDA)
static const uint mfCoarseTwt = 1;
// The data stride and data scale stay build-time (Vulkan's constants 75 and 79): read from a
// module __constant__ instead, the refine and tier kernels ran 12-39% slower on an L40S (the
// row-index arithmetic of the unrolled loops is no longer a compile-time power of two). A
// CUDA host therefore feeds the tiers packed bands (pack_coarse), not the spectra in place.
static const uint mfDataStride = 0;
static const uint mfDataScaleBits = 0x3f800000u;
// Accurate trig stays a build-time 0: CUDA builds without fast math, so its sin/cos are
// already the accurate ones (a runtime switch changed how NVRTC compiled them, and the
// two-stage transform's results with it).
static const uint mfAccurateTrig = 0;
// Per-row windows: CUDA takes the table as the entry's last argument and a window start of
// ROWWIN_ON switches it on (tierb.slang rowWindow), so no constant is needed.
static const uint mfRowWindows = 0;
static const uint mfSubgroupSize = 32;
#elif defined(MF_METAL)
// The coarse transform's twiddle source (constant 80 on Vulkan) as an MSL preprocessor macro
// the host sets when it compiles a library (MF_COARSE_TWT=1 for a "w" coarse entry): 0 is
// the fp32 recurrence, 1 the build's fp16 table. Measured per device and candidate.
__target_intrinsic(metal, "(MF_COARSE_TWT)")
uint mfCoarseTwtValue();
uint mfCoarseTwtFlag()
{
    __requirePrelude("#ifndef MF_COARSE_TWT\n#define MF_COARSE_TWT 0u\n#endif");
    return mfCoarseTwtValue();
}
#define mfCoarseTwt mfCoarseTwtFlag()
// The data stride, data scale, accurate trig and row windows (Vulkan's constants 75, 79, 73
// and 76) as MSL macros the host sets when it compiles a library, like MF_COARSE_TWT: Metal compiles its
// libraries at runtime, so these are compile-time values exactly as on Vulkan.
__target_intrinsic(metal, "(MF_DATA_STRIDE)")
uint mfDataStrideValue();
uint mfDataStrideFlag()
{
    __requirePrelude("#ifndef MF_DATA_STRIDE\n#define MF_DATA_STRIDE 0u\n#endif");
    return mfDataStrideValue();
}
#define mfDataStride mfDataStrideFlag()
__target_intrinsic(metal, "(MF_DATA_SCALE_BITS)")
uint mfDataScaleValue();
uint mfDataScaleFlag()
{
    __requirePrelude("#ifndef MF_DATA_SCALE_BITS\n#define MF_DATA_SCALE_BITS 0x3f800000u\n#endif");
    return mfDataScaleValue();
}
#define mfDataScaleBits mfDataScaleFlag()
__target_intrinsic(metal, "(MF_ACCURATE_TRIG)")
uint mfAccurateTrigValue();
uint mfAccurateTrigFlag()
{
    __requirePrelude("#ifndef MF_ACCURATE_TRIG\n#define MF_ACCURATE_TRIG 0u\n#endif");
    return mfAccurateTrigValue();
}
#define mfAccurateTrig mfAccurateTrigFlag()
// Per-row windows (Vulkan's constant 76): MF_ROW_WINDOWS=1 reads each row's window from the
// table, the entry's last argument (tierb.slang rowWindow); 0 compiles the read out, as a
// specialization constant does, so the table is then an inactive argument nothing binds.
__target_intrinsic(metal, "(MF_ROW_WINDOWS)")
uint mfRowWindowsValue();
uint mfRowWindowsFlag()
{
    __requirePrelude("#ifndef MF_ROW_WINDOWS\n#define MF_ROW_WINDOWS 0u\n#endif");
    return mfRowWindowsValue();
}
#define mfRowWindows mfRowWindowsFlag()
static const uint mfSubgroupSize = 32;
#else
static const uint mfCoarseTwt = 0;
static const uint mfDataStride = 0;
static const uint mfRowWindows = 0;
static const uint mfDataScaleBits = 0x3f800000u;
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
