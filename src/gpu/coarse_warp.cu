// CUDA coarse gate: one warp per run of pairs, warp-shuffle FFT in packed fp16 (half2).
//
// Built by tools/build_ptx.py (NVRTC) into coarse_warp_<band>.ptx; selected in
// _cudacompute._coarse_kernel only when it times fastest against the Slang variants.
// Same parameters and meaning as tierb.slang's coarse (COARSE16) fusedTierB:
//   data  (rows, B) half2-packed complex (re | im<<16), the coarse band of each row
//   tmpl  (nt, B)   likewise, the scaled coarse templates
//   for pair p = d*nt + t: y[m] = sum_k D[d,k] conj(T[t,k]) e^{+2 pi i k m / B},
//   value = max |y[m]|^2 over cstart <= m < cend, written as peakVal[p] = (sqrt(value), 0).
// The compaction reads only |peakVal|; peakIdx is not written (no consumer reads it).
//
// Layout: B = R * 32. Lane l holds elements n = l + 32 j (j < R). A radix-2 DIF FFT over j
// in registers, a twiddle w_B^{l k2}, then a 32-point DIF FFT across lanes with xor
// shuffles: element m = k2 + R k1 ends in register bitrev_R(k2), lane bitrev_5(k1). Two
// pairs share each half2 lane (.x pair A, .y pair B), so every op works on two pairs.
// The data row is cached across a warp's pairs and reloaded only when the row changes.
#include <cuda_fp16.h>

#ifndef BAND
#define BAND 256
#endif
#ifndef PPW
#define PPW 16                       // pairs per warp (even)
#endif
#ifndef WPB
#define WPB 4                        // warps per block
#endif
#ifndef LANES
#define LANES 32                     // lanes per pair-pair; a warp runs 32 / LANES of them
#endif
#define R (BAND / LANES)
#define G (32 / LANES)

template <int N> struct Log2 { static constexpr int v = 1 + Log2<N / 2>::v; };
template <> struct Log2<1> { static constexpr int v = 0; };
#define LGR (Log2<R>::v)
#define LGL (Log2<LANES>::v)

__device__ __forceinline__ unsigned brev(unsigned x, int bits) { return __brev(x) >> (32 - bits); }
__device__ __forceinline__ __half2 h2u(unsigned u) { return *reinterpret_cast<__half2 *>(&u); }
__device__ __forceinline__ unsigned u2h(__half2 h) { return *reinterpret_cast<unsigned *>(&h); }

// (ar + i ai) * (wr + i wi) with scalar fp32 twiddle broadcast to both lanes
__device__ __forceinline__ void cmulw(__half2 &ar, __half2 &ai, __half2 wr, __half2 wi)
{
    __half2 r = __hsub2(__hmul2(ar, wr), __hmul2(ai, wi));
    __half2 i = __hfma2(ar, wi, __hmul2(ai, wr));
    ar = r; ai = i;
}

// In-register DIF over R points, all stages: stage L uses w_L^k = w_R^{k R / L}.
template <int L> struct DifReg {
    __device__ __forceinline__ static void run(__half2 (&xr)[R], __half2 (&xi)[R],
                                               const __half2 (&wr)[R / 2], const __half2 (&wi)[R / 2])
    {
#pragma unroll
        for (int b0 = 0; b0 < R; b0 += L) {
#pragma unroll
            for (int k = 0; k < L / 2; ++k) {
                const int u = b0 + k, v = u + L / 2;
                __half2 sr = __hadd2(xr[u], xr[v]), si = __hadd2(xi[u], xi[v]);
                __half2 dr = __hsub2(xr[u], xr[v]), di = __hsub2(xi[u], xi[v]);
                xr[u] = sr; xi[u] = si;
                // w = 1 (k = 0) needs nothing; w = i (k = L/4) is a swap: (dr, di) -> (-di, dr)
                if (4 * k == L) { __half2 t = dr; dr = __hneg2(di); di = t; }
                else if (k) cmulw(dr, di, wr[k * (R / L)], wi[k * (R / L)]);
                xr[v] = dr; xi[v] = di;
            }
        }
        DifReg<L / 2>::run(xr, xi, wr, wi);
    }
};
template <> struct DifReg<1> {
    __device__ __forceinline__ static void run(__half2 (&)[R], __half2 (&)[R],
                                               const __half2 (&)[R / 2], const __half2 (&)[R / 2]) {}
};

extern "C" __global__ void __launch_bounds__(32 * WPB)
coarseWarp(const unsigned *__restrict__ data, const unsigned *__restrict__ tmpl,
           int *__restrict__ peakIdx, float2 *__restrict__ peakVal,
           unsigned ntmpl, unsigned cstart, unsigned cend, unsigned cspan, int cshift,
           unsigned nbins, unsigned thrBits)
{
    const unsigned wl = threadIdx.x & 31;
    const unsigned lane = wl & (LANES - 1), gi = wl / LANES;      // lane within the group
    const unsigned warp = blockIdx.x * WPB + (threadIdx.x >> 5);
    const unsigned p0 = warp * PPW;

    // Step-B twiddles w_B^{l k2}, and the lane-stage twiddles, once per thread.
    __half2 twr[R], twi[R];
#pragma unroll
    for (int j = 0; j < R; ++j) {
        unsigned k2 = brev(j, LGR);
        float s, c;
        sincospif(2.0f * float(lane * k2) / float(BAND), &s, &c);
        twr[j] = __float2half2_rn(c); twi[j] = __float2half2_rn(s);
    }
    __half2 rwr[R / 2], rwi[R / 2];             // w_R^k, the register stages' twiddles
#pragma unroll
    for (int k = 0; k < R / 2; ++k) {
        float s, c;
        sincospif(2.0f * float(k) / float(R), &s, &c);
        rwr[k] = __float2half2_rn(c); rwi[k] = __float2half2_rn(s);
    }
    __half2 lwr[LGL], lwi[LGL], lsg[LGL];
#pragma unroll
    for (int st = 0; st < LGL; ++st) {         // half-size h = LANES/2 >> st, L = 2h
        unsigned h = (LANES / 2) >> st;
        float s, c;
        sincospif(2.0f * float(lane & (h - 1)) / float(2 * h), &s, &c);
        // Lower lanes keep (u + v): twiddle 1. Upper lanes take (u - v) w.
        if (!(lane & h)) { c = 1.f; s = 0.f; }
        lwr[st] = __float2half2_rn(c); lwi[st] = __float2half2_rn(s);
        lsg[st] = __float2half2_rn((lane & h) ? -1.f : 1.f);
    }
    // Window mask: register j, this lane -> output index m = bitrev(j) + R * bitrev5(lane)
    unsigned live = 0;
    const unsigned k1 = brev(lane, LGL);
#pragma unroll
    for (int j = 0; j < R; ++j) {
        unsigned m = brev(j, LGR) + R * k1;
        if (m >= cstart && m < cend) live |= 1u << j;
    }

    unsigned drow = 0xffffffffu;
    __half2 dre[R], dim[R];
#pragma unroll
    for (int j = 0; j < R; ++j) { dre[j] = __float2half2_rn(0.f); dim[j] = dre[j]; }

    for (unsigned q = 2 * gi; q < PPW; q += 2 * G) {
        const unsigned pa = p0 + q, pb = pa + 1;
        const unsigned da = pa / ntmpl, ta = pa - da * ntmpl;
        const unsigned db = pb / ntmpl, tb = pb - db * ntmpl;
#ifdef EXPERIMENT_SAME_T
        const unsigned ta_ = 0, tb_ = 1;
#define ta ta_
#define tb tb_
#endif
        __half2 xr[R], xi[R];
        if (da != drow) {
            drow = da;
#pragma unroll
            for (int j = 0; j < R; ++j) {
                __half2 v = h2u(__ldg(data + (size_t)da * BAND + lane + LANES * j));
                dre[j] = __low2half2(v); dim[j] = __high2half2(v);
            }
        }
#pragma unroll
        for (int j = 0; j < R; ++j) {
            __half2 a = h2u(__ldg(tmpl + (size_t)ta * BAND + lane + LANES * j));
            __half2 b = h2u(__ldg(tmpl + (size_t)tb * BAND + lane + LANES * j));
            __half2 tr = __lows2half2(a, b), ti = __highs2half2(a, b);
            __half2 drj = dre[j], dij = dim[j];
            if (db != da) {                           // the pair straddles a row end
                __half2 v = h2u(__ldg(data + (size_t)db * BAND + lane + LANES * j));
                drj = __lows2half2(dre[j], v); dij = __lows2half2(dim[j], __high2half2(v));
            }
            // D * conj(T)
            xr[j] = __hfma2(drj, tr, __hmul2(dij, ti));
            xi[j] = __hsub2(__hmul2(dij, tr), __hmul2(drj, ti));
        }
        // Radix-2 DIF over j (size R): template recursion keeps every index a constant,
        // so xr/xi stay in registers (a runtime-bounded loop here put them in local memory).
        DifReg<R>::run(xr, xi, rwr, rwi);
        // Twiddle w_B^{lane * k2}
#pragma unroll
        for (int j = 1; j < R; ++j) cmulw(xr[j], xi[j], twr[j], twi[j]);   // j = 0: k2 = 0, w = 1
        // LANES-point DIF across the group's lanes (xor masks stay inside the group)
#pragma unroll
        for (int st = 0; st < LGL; ++st) {
            unsigned h = (LANES / 2) >> st;
            // Branch-free butterfly: lower lanes u + v, upper lanes (u - v) w, as
            // (self * sign + other) * twiddle with sign = -1 and twiddle w on upper lanes.
#pragma unroll
            for (int j = 0; j < R; ++j) {
                __half2 or_ = h2u(__shfl_xor_sync(0xffffffffu, u2h(xr[j]), h));
                __half2 oi = h2u(__shfl_xor_sync(0xffffffffu, u2h(xi[j]), h));
                __half2 dr = __hfma2(xr[j], lsg[st], or_), di = __hfma2(xi[j], lsg[st], oi);
                if (st < LGL - 1) cmulw(dr, di, lwr[st], lwi[st]);
                xr[j] = dr; xi[j] = di;
            }
        }
        // Peak |y|^2 in the window, per pair (lane .x = pair A, .y = pair B)
        __half2 best = __float2half2_rn(0.f);
#pragma unroll
        for (int j = 0; j < R; ++j) {
            __half2 mg = __hfma2(xr[j], xr[j], __hmul2(xi[j], xi[j]));
            if (live & (1u << j)) best = __hmax2(best, mg);
        }
#pragma unroll
        for (int o = LANES / 2; o >= 1; o >>= 1)
            best = __hmax2(best, h2u(__shfl_xor_sync(0xffffffffu, u2h(best), o)));
        if (lane == 0) {
            float2 m = __half22float2(best);
            peakVal[pa] = make_float2(sqrtf(m.x), 0.f);
            peakVal[pb] = make_float2(sqrtf(m.y), 0.f);
        }
    }
}
