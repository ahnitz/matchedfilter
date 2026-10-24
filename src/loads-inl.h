/* Block and spectrum loads that use only the V_* layer, so the AVX1 build (simd-avx1.h) has them
 * at 8 lanes as well: split_store's vector path needs the plan's lane width, which for the AVX
 * back end is 8, and the SSE4 copy it inherited fell back to the scalar loop there. */
#include <string.h>
#include "simd-inl.h"

#if defined(AP_LOADS_INL_H_) == defined(HWY_TARGET_TOGGLE)
#ifdef AP_LOADS_INL_H_
#undef AP_LOADS_INL_H_
#else
#define AP_LOADS_INL_H_
#endif

HWY_BEFORE_NAMESPACE();
namespace ap {
namespace HWY_NAMESPACE {

/* dst[k] = src[k * stride] * scale for k < have, then zeros to n: a block's samples read for
 * its forward transform (hmf.c), stride 1 for a series or 2 for one lane of a complex
 * series. In hmf.c the loop ran at the SSE4.2 baseline (4 lanes, an insertps gather at stride 2). */
static void scale_load(float *HWY_RESTRICT dst, const float *HWY_RESTRICT src, size_t have,
                       size_t n, size_t stride, float scale) {
  const vf s = V_SET1(scale);
  size_t k = 0;
  if (stride == 1) {
    for (; k + AP_W <= have; k += AP_W) V_STOREU(dst + k, V_MUL(V_LOADU(src + k), s));
  } else if (stride == 2) {
    for (; k + AP_W <= have; k += AP_W) {
      vf a, b;
      v_deint(src + 2 * k, &a, &b);
      V_STOREU(dst + k, V_MUL(a, s));
    }
  }
  for (; k < have; k++) dst[k] = src[k * stride] * scale;
  if (have < n) memset(dst + have, 0, (n - have) * sizeof(float));
}

/* A spectrum into the plan's split, group-major layout: re/im[g][b][l] = x[b*n1 + g*W + l]
 * (conjugated if conj), one interleaved load and two stores per W complex samples. The
 * plan's lane width w must be this target's AP_W; anything else (or n1 = 0, the natural
 * layout) takes the scalar copy. matchfilt.c's own copy was scalar: matchfilt.c is built at
 * the SSE4.2 baseline and GCC kept the strided loop as movss (8% of the hierarchical
 * engine's library time on test27, 2026-10-23). */
static void split_store(const float *HWY_RESTRICT x, float *HWY_RESTRICT re, float *HWY_RESTRICT im,
                        size_t n, int conj, int n1, int n2, int w) {
  const vf sg = conj ? V_SIGNMASK() : V_ZERO();
  if (n1 > 0 && n2 > 0 && w == AP_W && (size_t)n1 * (size_t)n2 == n && n1 % AP_W == 0) {
    const int ng = n1 / AP_W;
    for (int g = 0; g < ng; g++) {
      const float *src = x + 2 * (size_t)g * AP_W;
      float *r = re + (size_t)g * n2 * AP_W, *i = im + (size_t)g * n2 * AP_W;
      for (int b = 0; b < n2; b++, src += 2 * (size_t)n1, r += AP_W, i += AP_W) {
        vf vr, vi;
        v_deint(src, &vr, &vi);
        V_STOREU(r, vr);
        V_STOREU(i, V_XOR(vi, sg));
      }
    }
    return;
  }
  if (n1 > 0 && n2 > 0 && w > 0 && (size_t)n1 * (size_t)n2 == n) {
    const int ng = n1 / w;
    for (int g = 0; g < ng; g++)
      for (int b = 0; b < n2; b++)
        for (int l = 0; l < w; l++) {
          const size_t s = 2 * ((size_t)b * n1 + (size_t)g * w + l), o = ((size_t)g * n2 + b) * w + l;
          re[o] = x[s]; im[o] = conj ? -x[s + 1] : x[s + 1];
        }
    return;
  }
  for (size_t k = 0; k < n; k++) { re[k] = x[2 * k]; im[k] = conj ? -x[2 * k + 1] : x[2 * k + 1]; }
}

}  // namespace HWY_NAMESPACE
}  // namespace ap
HWY_AFTER_NAMESPACE();

#endif  // toggle guard
