// Tensor-core fp16 coarse gate (CUDA, sm_80+): the band-B inverse DFT of D * conj(T) as two
// split-complex matrix products on the tensor cores, the twiddle step in registers between.
//
// B = 16 * M (M = 16: band 256; M = 32: band 512). With n = n1 + 16 n2 and tau = k2 + M k1,
//
//   A[n1][k2] = sum_n2 X[n1][n2] W_M^(n2 k2)          (16 x M) . (M x M)    stage 1
//   C[n1][k2] = A[n1][k2] W_B^(n1 k2)                  elementwise, fp32     twiddle
//   Z[k1][k2] = sum_n1 W_16^(n1 k1) C[n1][k2]          (16 x 16) . (16 x M)  stage 2
//
// with W_L = exp(+2 pi i / L): the inverse transform, unnormalised, as the Slang coarse tier
// computes it. Z row-major is y[tau] in order. The products are mma.sync m16n8k16 (fp16 in,
// fp32 accumulate), four real products per complex one; a negated imaginary DFT matrix keeps
// every one an accumulate. The fragment layouts are PTX's documented ones, so the twiddle is
// applied to the stage-1 accumulators in registers and the window maximum is taken on the
// stage-2 accumulators in registers; only the stage-2 operand C goes through shared memory
// (the accumulator and B-operand layouts differ).
//
// Interface and geometry are the Slang fused coarse kernel's (fusedTierB, COARSE16, tiled
// ragged): one warp per slot of 2 templates of one data row, the row count in `binsize`,
// WPB warps per block; peakVal gets the bound on the window's |y| maximum (that maximum
// itself with mf_c16_raw set), peakIdx its lag. A non-finite value anywhere reports +inf:
// the gate fails open.
//
// The bound has the Slang form |c|(1 + 3u) + KAPPA u rms(y), KAPPA measured for THIS kernel
// (tools/cuda_tc_sigma.py): its rounding is not the radix-16 FFT's.
#include <cuda_fp16.h>

#ifndef BAND
#define BAND 256
#endif
#ifndef WPB
#define WPB 4
#endif
#ifndef KAPPA
#define KAPPA 0.0f
#endif
#define M (BAND / 16)
#define NT (M / 8)            // n tiles of 8 columns
#define U 4.8828125e-4f

extern "C" {
__constant__ unsigned int mf_c16_raw = 0;   // the host's raw switch (MF_VK_C16_BOUND=0)
}

__device__ __forceinline__ void mma16816(float c[4], unsigned a0, unsigned a1, unsigned a2,
                                         unsigned a3, unsigned b0, unsigned b1)
{
    asm volatile("mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32 "
                 "{%0,%1,%2,%3}, {%4,%5,%6,%7}, {%8,%9}, {%0,%1,%2,%3};"
                 : "+f"(c[0]), "+f"(c[1]), "+f"(c[2]), "+f"(c[3])
                 : "r"(a0), "r"(a1), "r"(a2), "r"(a3), "r"(b0), "r"(b1));
}

__device__ __forceinline__ unsigned pack2(__half lo, __half hi)
{
    return (unsigned)__half_as_ushort(lo) | ((unsigned)__half_as_ushort(hi) << 16);
}

// A fragment (16 x 16, row-major source with row stride ld) at column offset k0.
__device__ __forceinline__ void loadA(const __half* p, unsigned ld, unsigned k0, unsigned g,
                                      unsigned q, unsigned a[4])
{
    const __half* r0 = p + g * ld + k0 + 2 * q;
    const __half* r1 = r0 + 8 * ld;
    a[0] = pack2(r0[0], r0[1]);
    a[1] = pack2(r1[0], r1[1]);
    a[2] = pack2(r0[8], r0[9]);
    a[3] = pack2(r1[8], r1[9]);
}

// B fragment (16 x 8, k x n) from a row-major [k][n] source with row stride ld.
__device__ __forceinline__ void loadB(const __half* p, unsigned ld, unsigned k0, unsigned n0,
                                      unsigned g, unsigned q, unsigned b[2])
{
    const __half* c = p + (k0 + 2 * q) * ld + n0 + g;
    b[0] = pack2(c[0], c[ld]);
    b[1] = pack2(c[8 * ld], c[9 * ld]);
}

// B fragment (16 x 8) of a row-major [k][n] shared matrix by ldmatrix.trans: lanes 0-15
// give the addresses of rows k0 + lane (8 contiguous halves from column n0 each).
__device__ __forceinline__ void ldB(const __half* p, unsigned ld, unsigned n0, unsigned lane,
                                    unsigned b[2])
{
    unsigned a = (unsigned)__cvta_generic_to_shared(p + (lane & 15u) * ld + n0);
    asm volatile("ldmatrix.sync.aligned.m8n8.x2.trans.shared.b16 {%0,%1}, [%2];"
                 : "=r"(b[0]), "=r"(b[1]) : "r"(a));
}

struct WarpStage {
    __half xr[16 * M], xi[16 * M];     // stage-2 input C (16 x M)
};

extern "C" __global__ void __launch_bounds__(32 * WPB)
fusedTierB(const __half2* __restrict__ data, const __half2* __restrict__ tmpl,
           int* __restrict__ peakIdx, float2* __restrict__ peakVal,
           unsigned ntmpl, unsigned winStart, unsigned winEnd, unsigned rows,
           int binShift, unsigned nbins, unsigned thrBits)
{
    // DFT matrices, shared by the block: F_M (re, im, -im), F_16 (re, im, -im), twiddles.
    __shared__ __align__(16) __half fmr[M * M], fmi[M * M], fmn[M * M];
    __shared__ __align__(16) __half f16r[256], f16i[256], f16n[256];
    __shared__ __align__(16) float twr[16 * M], twi[16 * M];
    __shared__ __align__(16) WarpStage st[WPB];

    const unsigned lane = threadIdx.x & 31u, warp = threadIdx.x >> 5;
    const unsigned g = lane >> 2, q = lane & 3u;
    for (unsigned e = threadIdx.x; e < M * M; e += 32 * WPB) {
        unsigned r = e / M, c = e % M;
        float s, co;
        sincospif(2.0f * float((r * c) % M) / float(M), &s, &co);
        fmr[e] = __float2half_rn(co); fmi[e] = __float2half_rn(s); fmn[e] = __float2half_rn(-s);
    }
    for (unsigned e = threadIdx.x; e < 256; e += 32 * WPB) {
        unsigned r = e / 16, c = e % 16;
        float s, co;
        sincospif(2.0f * float((r * c) % 16) / 16.0f, &s, &co);
        f16r[e] = __float2half_rn(co); f16i[e] = __float2half_rn(s); f16n[e] = __float2half_rn(-s);
    }
    for (unsigned e = threadIdx.x; e < 16 * M; e += 32 * WPB) {
        unsigned n1 = e / M, k2 = e % M;
        float s, co;
        sincospif(2.0f * float((n1 * k2) % BAND) / float(BAND), &s, &co);
        twr[e] = co; twi[e] = s;
    }
    __syncthreads();

    const unsigned tiles = (ntmpl + 1u) / 2u;
    const unsigned slots = rows * tiles;
    WarpStage& w = st[warp];

    // Constant operands, in registers for the warp's life: stage-2 A (F_16), stage-1 B
    // (F_M per k step and n tile) and the twiddles at this lane's accumulator positions.
    unsigned fr[4], fi[4], fn[4];
    loadA(f16r, 16, 0, g, q, fr);
    loadA(f16i, 16, 0, g, q, fi);
    loadA(f16n, 16, 0, g, q, fn);
    unsigned bmr[M / 16][NT][2], bmi[M / 16][NT][2], bmn[M / 16][NT][2];
    float tr[NT][4], ti[NT][4];
#pragma unroll
    for (unsigned kk = 0; kk < M / 16; ++kk)
#pragma unroll
        for (unsigned j = 0; j < NT; ++j) {
            loadB(fmr, M, 16 * kk, 8 * j, g, q, bmr[kk][j]);
            loadB(fmi, M, 16 * kk, 8 * j, g, q, bmi[kk][j]);
            loadB(fmn, M, 16 * kk, 8 * j, g, q, bmn[kk][j]);
        }
#pragma unroll
    for (unsigned j = 0; j < NT; ++j)
#pragma unroll
        for (unsigned e = 0; e < 4; ++e) {
            unsigned i = (g + 8 * (e >> 1)) * M + 8 * j + 2 * q + (e & 1u);
            tr[j][e] = twr[i]; ti[j][e] = twi[i];
        }

    // Persistent warps: the block's setup (the DFT matrices, ~1.5k sincos) is paid once per
    // block, not per slot; any grid size is valid (whole warps leave together).
    for (unsigned slot = blockIdx.x * WPB + warp; slot < slots; slot += gridDim.x * WPB) {
    const unsigned d = slot / tiles, t0 = (slot - d * tiles) * 2u;
    const __half2* drow = data + (size_t)d * BAND;
    // The data row's elements this lane feeds into A, read once for both templates.
    float2 dv[M / 16][8];
#pragma unroll
    for (unsigned kk = 0; kk < M / 16; ++kk)
#pragma unroll
        for (unsigned v = 0; v < 8; ++v) {
            unsigned reg = v >> 1;
            unsigned row = g + 8 * (reg & 1u), col = 16 * kk + 2 * q + (v & 1u) + 8 * (reg >> 1);
            dv[kk][v] = __half22float2(drow[row + 16 * col]);
        }
    for (unsigned k = 0; k < 2; ++k) {
        const unsigned t = t0 + k;
        if (t >= ntmpl) break;                 // uniform across the warp
        const __half2* trow = tmpl + (size_t)t * BAND;
        // Stage 1: A = X . F_M. X[n1][n2] = x[n1 + 16 n2], x = D conj(T) rounded to fp16,
        // read straight into the A fragments: rows g, g+8, columns 16kk + 2q + {0,1,8,9}.
        float ar[NT][4], ai[NT][4];
#pragma unroll
        for (unsigned j = 0; j < NT; ++j)
#pragma unroll
            for (unsigned e = 0; e < 4; ++e) ar[j][e] = ai[j][e] = 0.0f;
#pragma unroll
        for (unsigned kk = 0; kk < M / 16; ++kk) {
            __half hr[8], hi[8];
#pragma unroll
            for (unsigned v = 0; v < 8; ++v) {
                // v: (reg >> 1) picks the row (g / g+8) and column half (+0 / +8), v & 1 the
                // pair element; register order a0 = (g, c), a1 = (g+8, c), a2 = (g, c+8), a3.
                unsigned reg = v >> 1;
                unsigned row = g + 8 * (reg & 1u), col = 16 * kk + 2 * q + (v & 1u) + 8 * (reg >> 1);
                unsigned n = row + 16 * col;
                float2 a = dv[kk][v], b = __half22float2(trow[n]);
                hr[v] = __float2half_rn(a.x * b.x + a.y * b.y);
                hi[v] = __float2half_rn(a.y * b.x - a.x * b.y);
            }
            unsigned xr[4], xi[4];
#pragma unroll
            for (unsigned r = 0; r < 4; ++r) {
                xr[r] = pack2(hr[2 * r], hr[2 * r + 1]);
                xi[r] = pack2(hi[2 * r], hi[2 * r + 1]);
            }
#pragma unroll
            for (unsigned j = 0; j < NT; ++j) {
                mma16816(ar[j], xr[0], xr[1], xr[2], xr[3], bmr[kk][j][0], bmr[kk][j][1]);
                mma16816(ar[j], xi[0], xi[1], xi[2], xi[3], bmn[kk][j][0], bmn[kk][j][1]);
                mma16816(ai[j], xr[0], xr[1], xr[2], xr[3], bmi[kk][j][0], bmi[kk][j][1]);
                mma16816(ai[j], xi[0], xi[1], xi[2], xi[3], bmr[kk][j][0], bmr[kk][j][1]);
            }
        }
        // Twiddle on the accumulators, in registers; C to shared as fp16 (stage-2 B operand:
        // its fragment layout differs from the accumulator's).
#pragma unroll
        for (unsigned j = 0; j < NT; ++j)
#pragma unroll
            for (unsigned e = 0; e < 4; e += 2) {
                unsigned i = (g + 8 * (e >> 1)) * M + 8 * j + 2 * q;
                float c0r = ar[j][e] * tr[j][e] - ai[j][e] * ti[j][e];
                float c0i = ar[j][e] * ti[j][e] + ai[j][e] * tr[j][e];
                float c1r = ar[j][e + 1] * tr[j][e + 1] - ai[j][e + 1] * ti[j][e + 1];
                float c1i = ar[j][e + 1] * ti[j][e + 1] + ai[j][e + 1] * tr[j][e + 1];
                *reinterpret_cast<__half2*>(w.xr + i) = __floats2half2_rn(c0r, c1r);
                *reinterpret_cast<__half2*>(w.xi + i) = __floats2half2_rn(c0i, c1i);
            }
        __syncwarp();
        // Stage 2: Z = F_16 . C; the window maximum, its value and the energy, in registers.
        float best = -1.0f, energy = 0.0f, vre = 0.0f, vim = 0.0f;
        unsigned bidx = 0xFFFFFFFFu;
        bool bad = false;
#pragma unroll
        for (unsigned j = 0; j < NT; ++j) {
            unsigned br[2], bi[2];
            ldB(w.xr, M, 8 * j, lane, br);
            ldB(w.xi, M, 8 * j, lane, bi);
            float zr[4] = {0.f, 0.f, 0.f, 0.f}, zi[4] = {0.f, 0.f, 0.f, 0.f};
            mma16816(zr, fr[0], fr[1], fr[2], fr[3], br[0], br[1]);   // Fr Cr
            mma16816(zr, fn[0], fn[1], fn[2], fn[3], bi[0], bi[1]);   // - Fi Ci
            mma16816(zi, fr[0], fr[1], fr[2], fr[3], bi[0], bi[1]);   // Fr Ci
            mma16816(zi, fi[0], fi[1], fi[2], fi[3], br[0], br[1]);   // + Fi Cr
#pragma unroll
            for (unsigned e = 0; e < 4; ++e) {
                unsigned tau = (8 * j + 2 * q + (e & 1u)) + M * (g + 8 * (e >> 1));
                float m2 = zr[e] * zr[e] + zi[e] * zi[e];
                bad |= !(m2 <= 3.0e38f);
                energy += m2;
                if (tau >= winStart && tau < winEnd && (m2 > best || (m2 == best && tau < bidx))) {
                    best = m2; bidx = tau; vre = zr[e]; vim = zi[e];
                }
            }
        }
        __syncwarp();                          // C is rewritten by the next template
#pragma unroll
        for (unsigned s = 16; s > 0; s >>= 1) {
            float ob = __shfl_xor_sync(0xffffffffu, best, s);
            unsigned oi = __shfl_xor_sync(0xffffffffu, bidx, s);
            float orr = __shfl_xor_sync(0xffffffffu, vre, s);
            float oii = __shfl_xor_sync(0xffffffffu, vim, s);
            if (ob > best || (ob == best && oi < bidx)) { best = ob; bidx = oi; vre = orr; vim = oii; }
            energy += __shfl_xor_sync(0xffffffffu, energy, s);
        }
        bad = __any_sync(0xffffffffu, bad);
        if (lane == 0) {
            const unsigned pair = d * ntmpl + t;
            if (bad) {
                peakIdx[pair] = 0;
                peakVal[pair] = make_float2(__int_as_float(0x7f800000), 0.0f);
            } else if (bidx == 0xFFFFFFFFu) {
                peakIdx[pair] = -1;
                peakVal[pair] = make_float2(0.0f, 0.0f);
            } else {
                float m = sqrtf(best);
                float b = (mf_c16_raw != 0u) ? m
                          : m * (1.0f + 3.0f * U) + KAPPA * U * sqrtf(energy / float(BAND));
                peakIdx[pair] = int(bidx);
                peakVal[pair] = (m > 0.0f) ? make_float2(vre * (b / m), vim * (b / m))
                                           : make_float2(b, 0.0f);
            }
        }
        __syncwarp();
    }
}
}
