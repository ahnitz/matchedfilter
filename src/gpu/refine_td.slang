// Direct time-domain FIR correlation refinement over narrow windows around coarse peak lags.
//
// Evaluates surviving (block, template) pairs directly from the input time series `series`
// and pre-loaded FIR `taps` across lags [a, b) = [ceIdx * R - hw * R, ceIdx * R + hw * R + 1)
// clipped to the block's search window [ws, we), matching src/hmf.c (refine_direct_pair and
// hmf_refine). Any survivor whose window touches multiple output bins, wraps the block,
// carries an invalid or overflowed coarse peak, exceeds shared-memory or per-pair lag-tap
// cost bounds, or lands its maximum on an interior window edge is appended to `fbSurv`
// (`fbArgs[0]`) for the existing FFT listed-refine fallback (`markBlocks`, `seriesForwardListed`,
// `refineListedBounded`). When zero pairs fall back, `fbArgs[0]` stays 0 and zero FFT refine
// workgroups run.

#include "twiddle.slang"

static const uint TD_ROWWIN_ON = 0xFFFFFFFFu;
static const uint TD_ROWWIN_WORDS = 3u;
// Capped so total workgroup memory stays within 16 KiB (4 workgroups/CU on 64 KiB LDS,
// 3 blocks/SM on 48 KiB CUDA static shared, 2 threadgroups on 32 KiB Metal).
static const uint TD_X_CAP = 1968u;

#ifdef MF_VULKAN
[[vk::binding(11, 0)]] StructuredBuffer<uint> gRowWin;
#define TD_ROWWIN_PARAM
#define TD_ROWWIN_ARG
[ForceInline]
void tdRowWindow(uint d, inout uint winStart, inout uint winEnd, inout uint binPhase)
{
    binPhase = 0u;
    if (mfRowWindows == 0u) return;
    winStart = gRowWin[TD_ROWWIN_WORDS * d];
    winEnd   = gRowWin[TD_ROWWIN_WORDS * d + 1u];
    binPhase = gRowWin[TD_ROWWIN_WORDS * d + 2u];
}
#elif defined(MF_METAL)
#define TD_ROWWIN_PARAM , StructuredBuffer<uint> rowWin
#define TD_ROWWIN_ARG , rowWin
[ForceInline]
void tdRowWindow(uint d, inout uint winStart, inout uint winEnd, inout uint binPhase,
                 StructuredBuffer<uint> rowWin)
{
    binPhase = 0u;
    if (mfRowWindows == 0u) return;
    winStart = rowWin[TD_ROWWIN_WORDS * d];
    winEnd   = rowWin[TD_ROWWIN_WORDS * d + 1u];
    binPhase = rowWin[TD_ROWWIN_WORDS * d + 2u];
}
#elif defined(MF_CUDA)
#define TD_ROWWIN_PARAM , StructuredBuffer<uint> rowWin
#define TD_ROWWIN_ARG , rowWin
[ForceInline]
void tdRowWindow(uint d, inout uint winStart, inout uint winEnd, inout uint binPhase,
                 StructuredBuffer<uint> rowWin)
{
    binPhase = 0u;
    if (winStart != TD_ROWWIN_ON) return;
    winStart = rowWin[TD_ROWWIN_WORDS * d];
    winEnd   = rowWin[TD_ROWWIN_WORDS * d + 1u];
    binPhase = rowWin[TD_ROWWIN_WORDS * d + 2u];
}
#else
#define TD_ROWWIN_PARAM
#define TD_ROWWIN_ARG
[ForceInline]
void tdRowWindow(uint d, inout uint winStart, inout uint winEnd, inout uint binPhase)
{
    binPhase = 0u;
}
#endif

[ForceInline]
float2 tdSeriesSample(StructuredBuffer<float2> series, uint i, uint layout)
{
    if (layout == 0u)
        return series[i];
    uint f = (layout >> 2u) + (layout & 3u) * i;
    float2 p = series[f >> 1u];
    return float2((f & 1u) != 0u ? p.y : p.x, 0.0f);
}

[ForceInline]
void tdUpdateBest(float2 z, int lag, inout uint bestM, inout int bestK, inout float2 bestV)
{
    uint zx = asuint(z.x) & 0x7FFFFFFFu;
    uint zy = asuint(z.y) & 0x7FFFFFFFu;
    uint mBits = (zx >= 0x7F800000u || zy >= 0x7F800000u)
               ? 0x7F800000u
               : asuint(z.x * z.x + z.y * z.y);
    if (mBits > bestM || (mBits == bestM && bestK < 0)) {
        bestM = mBits;
        bestK = lag;
        bestV = z;
    }
}

groupshared float2 x_sh[TD_X_CAP + 4u];
groupshared float2 bestV_sh[32];
groupshared uint bestM_sh[32];
groupshared int bestK_sh[32];

[shader("compute")][numthreads(32, 1, 1)]
void refineDirect(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                  StructuredBuffer<float2> series,
                  StructuredBuffer<uint> starts,
                  StructuredBuffer<uint> taps,
                  StructuredBuffer<int> cidx,
                  StructuredBuffer<float2> cval,
                  StructuredBuffer<uint> survivors,
                  StructuredBuffer<uint> survCount,
                  RWStructuredBuffer<uint> fbSurv,
                  RWStructuredBuffer<uint> fbArgs,
                  RWStructuredBuffer<int> peakIdx,
                  RWStructuredBuffer<float2> peakVal,
                  uniform uint n,
                  uniform uint lastBand,
                  uniform uint ntmpl,
                  uniform uint tmplOffset,
                  uniform uint seriesLength,
                  uniform uint seriesLayout,
                  uniform uint tapMeta,
                  uniform uint directHw,
                  uniform uint maxLagTap,
                  uniform uint winStart,
                  uniform uint winEnd,
                  uniform uint binsize,
                  uniform int binShift,
                  uniform uint nbins,
                  uniform uint thrBits,
                  uniform uint gridSize TD_ROWWIN_PARAM)
{
    uint tid = lid.x;
    uint total = survCount[0];
    uint tapStride = tapMeta >> 1u;
    bool isCplx = (tapMeta & 1u) != 0u;
    uint rowWords = 4u + (isCplx ? (2u * tapStride) : tapStride);

    for (uint item = gid.x; item < total; item += gridSize) {
        uint pair = survivors[item];
        uint d = pair / ntmpl;
        uint t = pair - d * ntmpl;
        uint ws = winStart, we = winEnd, binPhase = 0u;
        tdRowWindow(d, ws, we, binPhase TD_ROWWIN_ARG);
        we = min(we, n);

        // An empty window dismisses every bin without needing FFT fallback.
        if (ws >= we) {
            uint baseOut = pair * nbins;
            for (uint bin = tid; bin < nbins; bin += 32u) {
                peakIdx[baseOut + bin] = -1;
                peakVal[baseOut + bin] = float2(0.0f, 0.0f);
            }
            continue;
        }

        // Direct refine applies only when the row's searched samples touch a single bin.
        uint jb = binShift >= 0 ? (binPhase >> uint(binShift)) : (binPhase / binsize);
        uint lastOff = (we - 1u - ws) + binPhase;
        uint jbLast = binShift >= 0 ? (lastOff >> uint(binShift)) : (lastOff / binsize);
        if (jb != jbLast) {
            if (tid == 0u) {
                uint slot;
                InterlockedAdd(fbArgs[0], 1u, slot);
                fbSurv[slot] = pair;
            }
            continue;
        }

        // Non-finite or fail-open sentinel coarse values carry no reliable lag: fall back.
        int ceIdx = cidx[pair];
        float2 ceVal = cval[pair];
        bool badCoarse = (ceIdx < 0)
            || ((asuint(ceVal.x) & 0x7FFFFFFFu) >= 0x7F7FFFFFu)
            || ((asuint(ceVal.y) & 0x7FFFFFFFu) >= 0x7F7FFFFFu);
        if (badCoarse) {
            if (tid == 0u) {
                uint slot;
                InterlockedAdd(fbArgs[0], 1u, slot);
                fbSurv[slot] = pair;
            }
            continue;
        }

        int rStep = int(n / lastBand);
        int hwLags = int(directHw) * rStep;
        int a = max(int(ws), ceIdx * rStep - hwLags);
        int b = min(int(we), ceIdx * rStep + hwLags + 1);
        if (a >= b) {
            uint baseOut = pair * nbins;
            for (uint bin = tid; bin < nbins; bin += 32u) {
                peakIdx[baseOut + bin] = -1;
                peakVal[baseOut + bin] = float2(0.0f, 0.0f);
            }
            continue;
        }

        uint tRow = (t + tmplOffset) * rowWords;
        int L = int(taps[tRow]);
        int center = L >> 1;
        int s0 = a - center;
        int mLags = b - a;
        int need = mLags + L - 1;
        if (s0 < 0 || s0 + need > int(n) || uint(need) > TD_X_CAP
                || uint(mLags) * uint(L) >= maxLagTap) {
            if (tid == 0u) {
                uint slot;
                InterlockedAdd(fbArgs[0], 1u, slot);
                fbSurv[slot] = pair;
            }
            continue;
        }

        // Cooperatively stage the required block samples into shared memory.
        uint start = starts[d];
        uint uNeed = uint(need);
        for (uint i = tid; i < uNeed; i += 32u) {
            uint off = uint(s0) + i;
            float2 x = float2(0.0f, 0.0f);
            if (start < seriesLength && off < seriesLength - start)
                x = tdSeriesSample(series, start + off, seriesLayout);
            x_sh[i] = x;
        }
        if (tid < 4u)
            x_sh[uNeed + tid] = float2(0.0f, 0.0f);
        GroupMemoryBarrierWithGroupSync();

        // Evaluate 64 lags per pass (2 lags per thread across 32 threads) using uniform scalar
        // tap loads and barrier-free in-register accumulation; use single-accumulator pass when
        // <= 32 lags remain.
        uint uMLags = uint(mLags);
        uint lPad = (uint(L) + 3u) & ~3u;
        uint tapData = tRow + 4u;
        uint myBestM = thrBits;
        int myBestK = -1;
        float2 myBestV = float2(0.0f, 0.0f);
        for (uint lagBase = 0u; lagBase < uMLags; lagBase += 64u) {
            uint lag0 = lagBase + tid;
            uint x0 = min(lag0, uMLags - 1u);
            if (lagBase + 32u < uMLags) {
                uint lag1 = lag0 + 32u;
                uint x1 = min(lag1, uMLags - 1u);
                float2 acc0 = float2(0.0f, 0.0f);
                float2 acc1 = float2(0.0f, 0.0f);
                if (!isCplx) {
                    for (uint k = 0u; k < lPad; k += 4u) {
                        float h0 = asfloat(taps[tapData + k]);
                        float h1 = asfloat(taps[tapData + k + 1u]);
                        float h2 = asfloat(taps[tapData + k + 2u]);
                        float h3 = asfloat(taps[tapData + k + 3u]);
                        acc0 += h0 * x_sh[x0 + k]
                              + h1 * x_sh[x0 + k + 1u]
                              + h2 * x_sh[x0 + k + 2u]
                              + h3 * x_sh[x0 + k + 3u];
                        acc1 += h0 * x_sh[x1 + k]
                              + h1 * x_sh[x1 + k + 1u]
                              + h2 * x_sh[x1 + k + 2u]
                              + h3 * x_sh[x1 + k + 3u];
                    }
                } else {
                    for (uint k = 0u; k < lPad; k += 2u) {
                        uint hk = tapData + 2u * k;
                        float hr0 = asfloat(taps[hk]);
                        float hi0 = asfloat(taps[hk + 1u]);
                        float hr1 = asfloat(taps[hk + 2u]);
                        float hi1 = asfloat(taps[hk + 3u]);
                        float2 xv00 = x_sh[x0 + k];
                        float2 xv01 = x_sh[x0 + k + 1u];
                        acc0.x += hr0 * xv00.x - hi0 * xv00.y + hr1 * xv01.x - hi1 * xv01.y;
                        acc0.y += hr0 * xv00.y + hi0 * xv00.x + hr1 * xv01.y + hi1 * xv01.x;
                        float2 xv10 = x_sh[x1 + k];
                        float2 xv11 = x_sh[x1 + k + 1u];
                        acc1.x += hr0 * xv10.x - hi0 * xv10.y + hr1 * xv11.x - hi1 * xv11.y;
                        acc1.y += hr0 * xv10.y + hi0 * xv10.x + hr1 * xv11.y + hi1 * xv11.x;
                    }
                }
                tdUpdateBest(acc0, a + int(lag0), myBestM, myBestK, myBestV);
                if (lag1 < uMLags)
                    tdUpdateBest(acc1, a + int(lag1), myBestM, myBestK, myBestV);
            } else {
                float2 acc0 = float2(0.0f, 0.0f);
                if (!isCplx) {
                    for (uint k = 0u; k < lPad; k += 4u) {
                        float h0 = asfloat(taps[tapData + k]);
                        float h1 = asfloat(taps[tapData + k + 1u]);
                        float h2 = asfloat(taps[tapData + k + 2u]);
                        float h3 = asfloat(taps[tapData + k + 3u]);
                        acc0 += h0 * x_sh[x0 + k]
                              + h1 * x_sh[x0 + k + 1u]
                              + h2 * x_sh[x0 + k + 2u]
                              + h3 * x_sh[x0 + k + 3u];
                    }
                } else {
                    for (uint k = 0u; k < lPad; k += 2u) {
                        uint hk = tapData + 2u * k;
                        float hr0 = asfloat(taps[hk]);
                        float hi0 = asfloat(taps[hk + 1u]);
                        float hr1 = asfloat(taps[hk + 2u]);
                        float hi1 = asfloat(taps[hk + 3u]);
                        float2 xv00 = x_sh[x0 + k];
                        float2 xv01 = x_sh[x0 + k + 1u];
                        acc0.x += hr0 * xv00.x - hi0 * xv00.y + hr1 * xv01.x - hi1 * xv01.y;
                        acc0.y += hr0 * xv00.y + hi0 * xv00.x + hr1 * xv01.y + hi1 * xv01.x;
                    }
                }
                if (lag0 < uMLags)
                    tdUpdateBest(acc0, a + int(lag0), myBestM, myBestK, myBestV);
            }
        }

        // Reduce across the 32 lag lanes, breaking exact magnitude ties toward smallest lag.
        bestM_sh[tid] = myBestM;
        bestK_sh[tid] = myBestK;
        bestV_sh[tid] = myBestV;
        GroupMemoryBarrierWithGroupSync();

        uint bestM = thrBits;
        int bestK = -1;
        uint bestLane = 0u;
        [ForceUnroll] for (uint l = 0u; l < 32u; ++l) {
            uint m = bestM_sh[l];
            int k = bestK_sh[l];
            if (m > bestM || (m == bestM && k >= 0 && (bestK < 0 || k < bestK))) {
                bestM = m;
                bestK = k;
                bestLane = l;
            }
        }

        // An elected peak on an interior edge of [a, b) may be the shoulder of a larger peak
        // outside the direct window: fall back to the whole-block FFT refine (hmf.c:986-991).
        bool edgeFallback = (bestK >= 0)
            && ((bestK == a && a > int(ws)) || (bestK == b - 1 && b < int(we)));
        if (edgeFallback) {
            if (tid == 0u) {
                uint slot;
                InterlockedAdd(fbArgs[0], 1u, slot);
                fbSurv[slot] = pair;
            }
        } else {
            float2 winVal = bestV_sh[bestLane];
            uint baseOut = pair * nbins;
            for (uint bin = tid; bin < nbins; bin += 32u) {
                if (bin == jb && bestK >= 0) {
                    peakIdx[baseOut + bin] = bestK;
                    peakVal[baseOut + bin] = winVal;
                } else {
                    peakIdx[baseOut + bin] = -1;
                    peakVal[baseOut + bin] = float2(0.0f, 0.0f);
                }
            }
        }
        if (item + gridSize < total)
            GroupMemoryBarrierWithGroupSync();
    }
}
