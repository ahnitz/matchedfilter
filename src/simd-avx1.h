/* The SIMD layer for AVX1 (Sandy and Ivy Bridge): 8-float __m256 vectors, no FMA, no 256-bit
 * integer ALU.
 *
 * Highway has no AVX1 target (its x86 targets go SSE4 -> AVX2), so these CPUs ran the 4-lane
 * SSE4 kernels. The float kernels (balanced-inl.h, elemfft-inl.h, product-inl.h and the
 * generated codelets) speak only through the macros below, so this header gives them 8 lanes
 * without Highway; kernel_avx1.cc compiles them with it (AP_SIMD_AVX1). The integer kernels
 * (Q15 screen) and the hn::-based helpers (td, rsplit) stay with the SSE4 backend: AVX1 has no
 * 256-bit integer arithmetic to give them.
 *
 * Arithmetic is the SSE4 path's, operation for operation: MulAdd is a multiply then an add,
 * as Highway's non-FMA targets do it (mul * x + add, add - mul * x, mul * x - sub,
 * Neg(mul) * x - sub), so results are bit-identical to MF_ISA=SSE4. Integer lanes (indices,
 * masks) live in the float domain: loads, stores, broadcasts and blends need no integer ALU.
 */
#ifndef AP_SIMD_AVX1_H_
#define AP_SIMD_AVX1_H_
#include <immintrin.h>
#include <stdint.h>
#include <string.h>

#define restrict __restrict
#if defined(__GNUC__) || defined(__clang__)
#define AP_ALWAYS_INLINE inline __attribute__((always_inline))
#else
#define AP_ALWAYS_INLINE inline
#endif

/* What the kernel headers take from Highway. HWY_TARGET_TOGGLE stays undefined, so their
   re-inclusion guards include each body once. */
#define HWY_BEFORE_NAMESPACE()
#define HWY_AFTER_NAMESPACE()
#define HWY_NAMESPACE N_AVX
#define HWY_NOINLINE __attribute__((noinline))
#define HWY_INLINE inline __attribute__((always_inline))
#define HWY_ATTR
#define HWY_RESTRICT __restrict
#define HWY_MAX_BYTES 32

namespace ap {
namespace N_AVX {

constexpr int AP_W = 8;
typedef __m256 vf;
typedef __m256i vi;
typedef __m256 vm;     /* all-ones / all-zeros lanes, as vcmpps writes them */

#define V_ZERO()        _mm256_setzero_ps()
#define V_SET1(x)       _mm256_set1_ps((float)(x))
#define V_LOAD(p)       _mm256_loadu_ps((const float *)(p))
#define V_LOADU(p)      _mm256_loadu_ps((const float *)(p))
#define V_STORE(p, v)   _mm256_storeu_ps((float *)(p), (v))
#define V_STOREU(p, v)  _mm256_storeu_ps((float *)(p), (v))
#define V_ADD(a, b)     _mm256_add_ps((a), (b))
#define V_SUB(a, b)     _mm256_sub_ps((a), (b))
#define V_MUL(a, b)     _mm256_mul_ps((a), (b))
#define V_SIGNMASK()    _mm256_castsi256_ps(_mm256_set1_epi32((int32_t)0x80000000))
#define V_XOR(a, b)     _mm256_xor_ps((a), (b))
#define V_FMADD(a,b,c)  _mm256_add_ps(_mm256_mul_ps((a), (b)), (c))           /*  a*b + c */
#define V_FMSUB(a,b,c)  _mm256_sub_ps(_mm256_mul_ps((a), (b)), (c))           /*  a*b - c */
#define V_FNMADD(a,b,c) _mm256_sub_ps((c), _mm256_mul_ps((a), (b)))           /* -a*b + c */
#define V_FNMSUB(a,b,c) _mm256_sub_ps(_mm256_mul_ps(V_XOR((a), V_SIGNMASK()), (b)), (c)) /* -a*b - c */

#define VI_SET1(x)      _mm256_set1_epi32((int32_t)(x))
#define VI_LOADU(p)     _mm256_loadu_si256((const __m256i *)(p))
#define VI_STOREU(p, v) _mm256_storeu_si256((__m256i *)(p), (v))

#define V_CMP_GT(a, b)      _mm256_cmp_ps((a), (b), _CMP_GT_OQ)
#define V_MASK_ANY(m)       (_mm256_movemask_ps(m) != 0)
#define V_MASK_AND(a, b)    _mm256_and_ps((a), (b))
#define V_MASK_ANDNOT(a, b) _mm256_andnot_ps((a), (b))   /* ~a & b */
/* select b where the mask is set, a where clear */
#define V_SEL(m, a, b)  _mm256_blendv_ps((a), (b), (m))
#define VI_SEL(m, a, b) _mm256_castps_si256(_mm256_blendv_ps(_mm256_castsi256_ps(a), \
                                                             _mm256_castsi256_ps(b), (m)))

/* Bits to lanes without an integer compare: one 32-byte row per bit pattern. */
struct ap_avx1_mask_table {
  alignas(32) int32_t m[256][8];
  ap_avx1_mask_table() {
    for (int b = 0; b < 256; b++)
      for (int l = 0; l < 8; l++) m[b][l] = (b >> l) & 1 ? -1 : 0;
  }
};
static const ap_avx1_mask_table ap_avx1_masks;
static inline vm ap_mask_from_bits(unsigned bits) {
  return _mm256_load_ps((const float *)ap_avx1_masks.m[bits & 255u]);
}
#define V_MASK_FROM_BITS(u) ap_mask_from_bits((unsigned)(u))
#define V_BITS_FROM_MASK(m) ((unsigned)_mm256_movemask_ps(m))

static inline float v_reduce_max(vf v) {
  __m128 m = _mm_max_ps(_mm256_castps256_ps128(v), _mm256_extractf128_ps(v, 1));
  m = _mm_max_ps(m, _mm_movehl_ps(m, m));
  m = _mm_max_ss(m, _mm_shuffle_ps(m, m, 1));
  return _mm_cvtss_f32(m);
}

/* Eight complex samples in, re and im out (and back): lane-crossing only through vperm2f128. */
static inline void v_deint(const float *p, vf *re, vf *im) {
  const vf lo = _mm256_loadu_ps(p), hi = _mm256_loadu_ps(p + 8);
  const vf a = _mm256_permute2f128_ps(lo, hi, 0x20), b = _mm256_permute2f128_ps(lo, hi, 0x31);
  *re = _mm256_shuffle_ps(a, b, 0x88);
  *im = _mm256_shuffle_ps(a, b, 0xdd);
}
static inline void v_inter(float *p, vf re, vf im) {
  const vf a = _mm256_unpacklo_ps(re, im), b = _mm256_unpackhi_ps(re, im);
  _mm256_storeu_ps(p, _mm256_permute2f128_ps(a, b, 0x20));
  _mm256_storeu_ps(p + 8, _mm256_permute2f128_ps(a, b, 0x31));
}

/* 8 x 8 transpose: in-lane 32- and 64-bit interleaves, then the 128-bit halves swapped. */
static inline void v_transpose(const vf *in, vf *out) {
  vf t[8], u[8];
  for (int i = 0; i < 8; i += 2) {
    t[i] = _mm256_unpacklo_ps(in[i], in[i + 1]);
    t[i + 1] = _mm256_unpackhi_ps(in[i], in[i + 1]);
  }
  for (int i = 0; i < 4; i++) {
    const int a = (i & 1) + ((i & 2) << 1);      /* 0,1,4,5 */
    const int b = a + 2;
    u[2 * i] = _mm256_castpd_ps(_mm256_unpacklo_pd(_mm256_castps_pd(t[a]), _mm256_castps_pd(t[b])));
    u[2 * i + 1] = _mm256_castpd_ps(_mm256_unpackhi_pd(_mm256_castps_pd(t[a]), _mm256_castps_pd(t[b])));
  }
  for (int i = 0; i < 4; i++) {
    out[i] = _mm256_permute2f128_ps(u[i], u[i + 4], 0x20);
    out[i + 4] = _mm256_permute2f128_ps(u[i], u[i + 4], 0x31);
  }
}
static inline void v_transpose_store(const vf *in, float *out) {
  vf t[8];
  v_transpose(in, t);
  for (int i = 0; i < 8; i++) _mm256_storeu_ps(out + 8 * i, t[i]);
}
#define V_TRANSPOSE(in, out) v_transpose((in), (out))

}  // namespace N_AVX
}  // namespace ap
#endif
