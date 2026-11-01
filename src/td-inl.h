/* Direct (time-domain) correlation over a short run of consecutive lags: the refine's
 * answer at the few lags a survivor's coarse tier points at, without a whole-block transform.
 *
 *     out[i] = sum_{k<L} conj(taps[k]) * x[i + k],   i in [0, nlag)
 *
 * Pre-conjugated split taps pass tr[k] = Re(taps[k]) and ti[k] = -Im(taps[k]) (ti == NULL for
 * real taps). Written through the V_* layer so every Highway target and the 8-lane AVX1 build
 * (simd-avx1.h) compile the same vectorised kernels.
 */
#include "simd-inl.h"

#ifndef AP_TD_NO_UNROLL
#if defined(__GNUC__) && !defined(__clang__)
#define AP_TD_NO_UNROLL _Pragma("GCC unroll 1")
#elif defined(__clang__)
#define AP_TD_NO_UNROLL _Pragma("clang loop unroll(disable)")
#else
#define AP_TD_NO_UNROLL
#endif
#if defined(__GNUC__) || defined(__clang__)
/* Stop -fpredictive-commoning from carrying sliding-window vector loads across k iterations
   and spilling YMM/XMM accumulators to %rsp when L1D memory-operand FMAs are free. */
#define AP_TD_HIDE_PTR(p) __asm__("" : "+r"(p))
#else
#define AP_TD_HIDE_PTR(p) ((void)0)
#endif
#endif

#if defined(AP_TD_INL_H_) == defined(HWY_TARGET_TOGGLE)
#ifdef AP_TD_INL_H_
#undef AP_TD_INL_H_
#else
#define AP_TD_INL_H_
#endif

HWY_BEFORE_NAMESPACE();
namespace ap {
namespace HWY_NAMESPACE {

/* Interleaved complex x with real taps: a vector of AP_W floats holds AP_W/2 complex lags. */
static HWY_INLINE void td_pass_cr_vec(const float *HWY_RESTRICT x, const float *HWY_RESTRICT taps,
                                      int L, float *HWY_RESTRICT out) {
  vf a0 = V_ZERO(), b0 = V_ZERO(), c0 = V_ZERO(), d0 = V_ZERO();
  int k = 0;
  AP_TD_NO_UNROLL
  for (; k + 3 < L; k += 4) {
    const float *p = x + 2 * (size_t)k;
    a0 = V_FMADD(V_SET1(taps[k]), V_LOADU(p), a0);
    b0 = V_FMADD(V_SET1(taps[k + 1]), V_LOADU(p + 2), b0);
    c0 = V_FMADD(V_SET1(taps[k + 2]), V_LOADU(p + 4), c0);
    d0 = V_FMADD(V_SET1(taps[k + 3]), V_LOADU(p + 6), d0);
  }
  for (; k < L; k++) {
    a0 = V_FMADD(V_SET1(taps[k]), V_LOADU(x + 2 * (size_t)k), a0);
  }
  V_STOREU(out, V_ADD(V_ADD(a0, b0), V_ADD(c0, d0)));
}

/* Reads x[0, 2*(nlag + L - 1)) floats, writes out[0, 2*nlag). */
static void td_corr(const float *HWY_RESTRICT x, const float *HWY_RESTRICT taps, int L, int nlag,
                    float *HWY_RESTRICT out) {
  const size_t nf = 2 * (size_t)nlag;
  const size_t W = (size_t)AP_W;
  size_t i = 0;
#if !defined(AP_SIMD_AVX1) && (!defined(HWY_TARGET) || HWY_TARGET != HWY_SSE4)
  /* FMA targets: 4*W floats (12 FMA chains on AVX-512, 8 on AVX2/NEON) -> 2*W (8 FMA chains). */
  for (; i + 4 * W <= nf; i += 4 * W) {
    vf a0 = V_ZERO(), a1 = V_ZERO(), a2 = V_ZERO(), a3 = V_ZERO();
    vf b0 = V_ZERO(), b1 = V_ZERO(), b2 = V_ZERO(), b3 = V_ZERO();
    if constexpr (AP_W >= 16) {
      vf c0 = V_ZERO(), c1 = V_ZERO(), c2 = V_ZERO(), c3 = V_ZERO();
      int k = 0;
      AP_TD_NO_UNROLL
      for (; k + 2 < L; k += 3) {
        const float *p = x + i + 2 * (size_t)k;
        AP_TD_HIDE_PTR(p);
        const vf w0 = V_SET1(taps[k]);
        a0 = V_FMADD(w0, V_LOADU(p), a0);
        a1 = V_FMADD(w0, V_LOADU(p + W), a1);
        a2 = V_FMADD(w0, V_LOADU(p + 2 * W), a2);
        a3 = V_FMADD(w0, V_LOADU(p + 3 * W), a3);
        const vf w1 = V_SET1(taps[k + 1]);
        b0 = V_FMADD(w1, V_LOADU(p + 2), b0);
        b1 = V_FMADD(w1, V_LOADU(p + W + 2), b1);
        b2 = V_FMADD(w1, V_LOADU(p + 2 * W + 2), b2);
        b3 = V_FMADD(w1, V_LOADU(p + 3 * W + 2), b3);
        const vf w2 = V_SET1(taps[k + 2]);
        c0 = V_FMADD(w2, V_LOADU(p + 4), c0);
        c1 = V_FMADD(w2, V_LOADU(p + W + 4), c1);
        c2 = V_FMADD(w2, V_LOADU(p + 2 * W + 4), c2);
        c3 = V_FMADD(w2, V_LOADU(p + 3 * W + 4), c3);
      }
      for (; k < L; k++) {
        const float *p = x + i + 2 * (size_t)k;
        const vf w0 = V_SET1(taps[k]);
        a0 = V_FMADD(w0, V_LOADU(p), a0);
        a1 = V_FMADD(w0, V_LOADU(p + W), a1);
        a2 = V_FMADD(w0, V_LOADU(p + 2 * W), a2);
        a3 = V_FMADD(w0, V_LOADU(p + 3 * W), a3);
      }
      V_STOREU(out + i, V_ADD(V_ADD(a0, b0), c0));
      V_STOREU(out + i + W, V_ADD(V_ADD(a1, b1), c1));
      V_STOREU(out + i + 2 * W, V_ADD(V_ADD(a2, b2), c2));
      V_STOREU(out + i + 3 * W, V_ADD(V_ADD(a3, b3), c3));
    } else {
      int k = 0;
      AP_TD_NO_UNROLL
      for (; k + 1 < L; k += 2) {
        const float *p = x + i + 2 * (size_t)k;
        AP_TD_HIDE_PTR(p);
        const vf w0 = V_SET1(taps[k]);
        a0 = V_FMADD(w0, V_LOADU(p), a0);
        a1 = V_FMADD(w0, V_LOADU(p + W), a1);
        a2 = V_FMADD(w0, V_LOADU(p + 2 * W), a2);
        a3 = V_FMADD(w0, V_LOADU(p + 3 * W), a3);
        const vf w1 = V_SET1(taps[k + 1]);
        b0 = V_FMADD(w1, V_LOADU(p + 2), b0);
        b1 = V_FMADD(w1, V_LOADU(p + W + 2), b1);
        b2 = V_FMADD(w1, V_LOADU(p + 2 * W + 2), b2);
        b3 = V_FMADD(w1, V_LOADU(p + 3 * W + 2), b3);
      }
      for (; k < L; k++) {
        const float *p = x + i + 2 * (size_t)k;
        const vf w0 = V_SET1(taps[k]);
        a0 = V_FMADD(w0, V_LOADU(p), a0);
        a1 = V_FMADD(w0, V_LOADU(p + W), a1);
        a2 = V_FMADD(w0, V_LOADU(p + 2 * W), a2);
        a3 = V_FMADD(w0, V_LOADU(p + 3 * W), a3);
      }
      V_STOREU(out + i, V_ADD(a0, b0));
      V_STOREU(out + i + W, V_ADD(a1, b1));
      V_STOREU(out + i + 2 * W, V_ADD(a2, b2));
      V_STOREU(out + i + 3 * W, V_ADD(a3, b3));
    }
  }
  for (; i + 2 * W <= nf; i += 2 * W) {
    vf a0 = V_ZERO(), b0 = V_ZERO(), c0 = V_ZERO(), d0 = V_ZERO();
    vf a1 = V_ZERO(), b1 = V_ZERO(), c1 = V_ZERO(), d1 = V_ZERO();
    int k = 0;
    AP_TD_NO_UNROLL
    for (; k + 3 < L; k += 4) {
      const float *p = x + i + 2 * (size_t)k;
      AP_TD_HIDE_PTR(p);
      const vf w0 = V_SET1(taps[k]);
      a0 = V_FMADD(w0, V_LOADU(p), a0);
      a1 = V_FMADD(w0, V_LOADU(p + W), a1);
      const vf w1 = V_SET1(taps[k + 1]);
      b0 = V_FMADD(w1, V_LOADU(p + 2), b0);
      b1 = V_FMADD(w1, V_LOADU(p + W + 2), b1);
      const vf w2 = V_SET1(taps[k + 2]);
      c0 = V_FMADD(w2, V_LOADU(p + 4), c0);
      c1 = V_FMADD(w2, V_LOADU(p + W + 4), c1);
      const vf w3 = V_SET1(taps[k + 3]);
      d0 = V_FMADD(w3, V_LOADU(p + 6), d0);
      d1 = V_FMADD(w3, V_LOADU(p + W + 6), d1);
    }
    for (; k < L; k++) {
      const float *p = x + i + 2 * (size_t)k;
      const vf w0 = V_SET1(taps[k]);
      a0 = V_FMADD(w0, V_LOADU(p), a0);
      a1 = V_FMADD(w0, V_LOADU(p + W), a1);
    }
    V_STOREU(out + i, V_ADD(V_ADD(a0, b0), V_ADD(c0, d0)));
    V_STOREU(out + i + W, V_ADD(V_ADD(a1, b1), V_ADD(c1, d1)));
  }
#else
  /* Non-FMA targets (SSE4, AVX1): let predictive commoning reuse sliding loads without spills. */
#if !defined(AP_SIMD_AVX1)
  for (; i + 3 * W <= nf; i += 3 * W) {
    vf a0 = V_ZERO(), b0 = V_ZERO(), a1 = V_ZERO(), b1 = V_ZERO(), a2 = V_ZERO(), b2 = V_ZERO();
    int k = 0;
    for (; k + 1 < L; k += 2) {
      const float *p = x + i + 2 * (size_t)k;
      const vf w0 = V_SET1(taps[k]), w1 = V_SET1(taps[k + 1]);
      a0 = V_FMADD(w0, V_LOADU(p), a0);
      b0 = V_FMADD(w1, V_LOADU(p + 2), b0);
      a1 = V_FMADD(w0, V_LOADU(p + W), a1);
      b1 = V_FMADD(w1, V_LOADU(p + W + 2), b1);
      a2 = V_FMADD(w0, V_LOADU(p + 2 * W), a2);
      b2 = V_FMADD(w1, V_LOADU(p + 2 * W + 2), b2);
    }
    for (; k < L; k++) {
      const float *p = x + i + 2 * (size_t)k;
      const vf w0 = V_SET1(taps[k]);
      a0 = V_FMADD(w0, V_LOADU(p), a0);
      a1 = V_FMADD(w0, V_LOADU(p + W), a1);
      a2 = V_FMADD(w0, V_LOADU(p + 2 * W), a2);
    }
    V_STOREU(out + i, V_ADD(a0, b0));
    V_STOREU(out + i + W, V_ADD(a1, b1));
    V_STOREU(out + i + 2 * W, V_ADD(a2, b2));
  }
#endif
  for (; i + 2 * W <= nf; i += 2 * W) {
    vf a0 = V_ZERO(), b0 = V_ZERO(), a1 = V_ZERO(), b1 = V_ZERO();
    int k = 0;
    for (; k + 1 < L; k += 2) {
      const float *p = x + i + 2 * (size_t)k;
      const vf w0 = V_SET1(taps[k]), w1 = V_SET1(taps[k + 1]);
      a0 = V_FMADD(w0, V_LOADU(p), a0);
      b0 = V_FMADD(w1, V_LOADU(p + 2), b0);
      a1 = V_FMADD(w0, V_LOADU(p + W), a1);
      b1 = V_FMADD(w1, V_LOADU(p + W + 2), b1);
    }
    for (; k < L; k++) {
      const float *p = x + i + 2 * (size_t)k;
      const vf w0 = V_SET1(taps[k]);
      a0 = V_FMADD(w0, V_LOADU(p), a0);
      a1 = V_FMADD(w0, V_LOADU(p + W), a1);
    }
    V_STOREU(out + i, V_ADD(a0, b0));
    V_STOREU(out + i + W, V_ADD(a1, b1));
  }
#endif
  if (i + W <= nf) { td_pass_cr_vec(x + i, taps, L, out + i); i += W; }
  for (; i < nf; i += 2) {
    float ar = 0.f, br = 0.f, ai = 0.f, bi = 0.f;
    int k = 0;
    for (; k + 1 < L; k += 2) {
      const float w0 = taps[k], w1 = taps[k + 1];
      const float *p = x + i + 2 * (size_t)k;
      ar += w0 * p[0]; ai += w0 * p[1];
      br += w1 * p[2]; bi += w1 * p[3];
    }
    for (; k < L; k++) {
      const float w0 = taps[k];
      const float *p = x + i + 2 * (size_t)k;
      ar += w0 * p[0]; ai += w0 * p[1];
    }
    out[i] = ar + br;
    out[i + 1] = ai + bi;
  }
}

/* Contiguous real x[0, nlag + L - 1) with split conjugated complex taps (tr, ti). */
static void td_corr_rc(const float *HWY_RESTRICT x, const float *HWY_RESTRICT tr,
                       const float *HWY_RESTRICT ti, int L, int nlag, float *HWY_RESTRICT out) {
  const size_t nl = (size_t)nlag, W = (size_t)AP_W;
  size_t i = 0;
  if (!ti) {
    /* Real x, real taps: 4*W -> 2*W -> 1*W cascade, 8-12 FMA accumulators, zero spills. */
    for (; i + 4 * W <= nl; i += 4 * W) {
      vf a0 = V_ZERO(), a1 = V_ZERO(), a2 = V_ZERO(), a3 = V_ZERO();
      vf b0 = V_ZERO(), b1 = V_ZERO(), b2 = V_ZERO(), b3 = V_ZERO();
#if !defined(AP_SIMD_AVX1)
      vf c0 = V_ZERO(), c1 = V_ZERO(), c2 = V_ZERO(), c3 = V_ZERO();
      int k = 0;
      AP_TD_NO_UNROLL
      for (; k + 2 < L; k += 3) {
        const float *p = x + i + (size_t)k;
        AP_TD_HIDE_PTR(p);
        const vf w0 = V_SET1(tr[k]);
        a0 = V_FMADD(w0, V_LOADU(p), a0);
        a1 = V_FMADD(w0, V_LOADU(p + W), a1);
        a2 = V_FMADD(w0, V_LOADU(p + 2 * W), a2);
        a3 = V_FMADD(w0, V_LOADU(p + 3 * W), a3);
        const vf w1 = V_SET1(tr[k + 1]);
        b0 = V_FMADD(w1, V_LOADU(p + 1), b0);
        b1 = V_FMADD(w1, V_LOADU(p + W + 1), b1);
        b2 = V_FMADD(w1, V_LOADU(p + 2 * W + 1), b2);
        b3 = V_FMADD(w1, V_LOADU(p + 3 * W + 1), b3);
        const vf w2 = V_SET1(tr[k + 2]);
        c0 = V_FMADD(w2, V_LOADU(p + 2), c0);
        c1 = V_FMADD(w2, V_LOADU(p + W + 2), c1);
        c2 = V_FMADD(w2, V_LOADU(p + 2 * W + 2), c2);
        c3 = V_FMADD(w2, V_LOADU(p + 3 * W + 2), c3);
      }
      for (; k < L; k++) {
        const float *p = x + i + (size_t)k;
        const vf w0 = V_SET1(tr[k]);
        a0 = V_FMADD(w0, V_LOADU(p), a0);
        a1 = V_FMADD(w0, V_LOADU(p + W), a1);
        a2 = V_FMADD(w0, V_LOADU(p + 2 * W), a2);
        a3 = V_FMADD(w0, V_LOADU(p + 3 * W), a3);
      }
      const vf z = V_ZERO();
      v_inter(out + 2 * i, V_ADD(V_ADD(a0, b0), c0), z);
      v_inter(out + 2 * (i + W), V_ADD(V_ADD(a1, b1), c1), z);
      v_inter(out + 2 * (i + 2 * W), V_ADD(V_ADD(a2, b2), c2), z);
      v_inter(out + 2 * (i + 3 * W), V_ADD(V_ADD(a3, b3), c3), z);
#else
      int k = 0;
      AP_TD_NO_UNROLL
      for (; k + 1 < L; k += 2) {
        const float *p = x + i + (size_t)k;
        AP_TD_HIDE_PTR(p);
        const vf w0 = V_SET1(tr[k]);
        a0 = V_FMADD(w0, V_LOADU(p), a0);
        a1 = V_FMADD(w0, V_LOADU(p + W), a1);
        a2 = V_FMADD(w0, V_LOADU(p + 2 * W), a2);
        a3 = V_FMADD(w0, V_LOADU(p + 3 * W), a3);
        const vf w1 = V_SET1(tr[k + 1]);
        b0 = V_FMADD(w1, V_LOADU(p + 1), b0);
        b1 = V_FMADD(w1, V_LOADU(p + W + 1), b1);
        b2 = V_FMADD(w1, V_LOADU(p + 2 * W + 1), b2);
        b3 = V_FMADD(w1, V_LOADU(p + 3 * W + 1), b3);
      }
      for (; k < L; k++) {
        const float *p = x + i + (size_t)k;
        const vf w0 = V_SET1(tr[k]);
        a0 = V_FMADD(w0, V_LOADU(p), a0);
        a1 = V_FMADD(w0, V_LOADU(p + W), a1);
        a2 = V_FMADD(w0, V_LOADU(p + 2 * W), a2);
        a3 = V_FMADD(w0, V_LOADU(p + 3 * W), a3);
      }
      const vf z = V_ZERO();
      v_inter(out + 2 * i, V_ADD(a0, b0), z);
      v_inter(out + 2 * (i + W), V_ADD(a1, b1), z);
      v_inter(out + 2 * (i + 2 * W), V_ADD(a2, b2), z);
      v_inter(out + 2 * (i + 3 * W), V_ADD(a3, b3), z);
#endif
    }
    for (; i + 2 * W <= nl; i += 2 * W) {
      vf a0 = V_ZERO(), b0 = V_ZERO(), c0 = V_ZERO(), d0 = V_ZERO();
      vf a1 = V_ZERO(), b1 = V_ZERO(), c1 = V_ZERO(), d1 = V_ZERO();
      int k = 0;
      AP_TD_NO_UNROLL
      for (; k + 3 < L; k += 4) {
        const float *p = x + i + (size_t)k;
        AP_TD_HIDE_PTR(p);
        const vf w0 = V_SET1(tr[k]);
        a0 = V_FMADD(w0, V_LOADU(p), a0);
        a1 = V_FMADD(w0, V_LOADU(p + W), a1);
        const vf w1 = V_SET1(tr[k + 1]);
        b0 = V_FMADD(w1, V_LOADU(p + 1), b0);
        b1 = V_FMADD(w1, V_LOADU(p + W + 1), b1);
        const vf w2 = V_SET1(tr[k + 2]);
        c0 = V_FMADD(w2, V_LOADU(p + 2), c0);
        c1 = V_FMADD(w2, V_LOADU(p + W + 2), c1);
        const vf w3 = V_SET1(tr[k + 3]);
        d0 = V_FMADD(w3, V_LOADU(p + 3), d0);
        d1 = V_FMADD(w3, V_LOADU(p + W + 3), d1);
      }
      for (; k < L; k++) {
        const float *p = x + i + (size_t)k;
        const vf w0 = V_SET1(tr[k]);
        a0 = V_FMADD(w0, V_LOADU(p), a0);
        a1 = V_FMADD(w0, V_LOADU(p + W), a1);
      }
      const vf z = V_ZERO();
      v_inter(out + 2 * i, V_ADD(V_ADD(a0, b0), V_ADD(c0, d0)), z);
      v_inter(out + 2 * (i + W), V_ADD(V_ADD(a1, b1), V_ADD(c1, d1)), z);
    }
    for (; i + W <= nl; i += W) {
      vf a0 = V_ZERO(), b0 = V_ZERO(), c0 = V_ZERO(), d0 = V_ZERO();
      int k = 0;
      AP_TD_NO_UNROLL
      for (; k + 3 < L; k += 4) {
        const float *p = x + i + (size_t)k;
        AP_TD_HIDE_PTR(p);
        a0 = V_FMADD(V_SET1(tr[k]), V_LOADU(p), a0);
        b0 = V_FMADD(V_SET1(tr[k + 1]), V_LOADU(p + 1), b0);
        c0 = V_FMADD(V_SET1(tr[k + 2]), V_LOADU(p + 2), c0);
        d0 = V_FMADD(V_SET1(tr[k + 3]), V_LOADU(p + 3), d0);
      }
      for (; k < L; k++) a0 = V_FMADD(V_SET1(tr[k]), V_LOADU(x + i + (size_t)k), a0);
      v_inter(out + 2 * i, V_ADD(V_ADD(a0, b0), V_ADD(c0, d0)), V_ZERO());
    }
    for (; i < nl; i++) {
      float ar = 0.f, br = 0.f;
      int k = 0;
      for (; k + 1 < L; k += 2) { ar += tr[k] * x[i + k]; br += tr[k + 1] * x[i + k + 1]; }
      for (; k < L; k++) ar += tr[k] * x[i + k];
      out[2 * i] = ar + br;
      out[2 * i + 1] = 0.f;
    }
    return;
  }

  /* Real x, complex taps: 3*W on AVX-512, 2*W (8-12 FMA chains) main loop on all targets. */
  if constexpr (AP_W >= 16) {
    for (; i + 3 * W <= nl; i += 3 * W) {
      vf ar0 = V_ZERO(), ai0 = V_ZERO(), ar1 = V_ZERO(), ai1 = V_ZERO(), ar2 = V_ZERO(), ai2 = V_ZERO();
      vf br0 = V_ZERO(), bi0 = V_ZERO(), br1 = V_ZERO(), bi1 = V_ZERO(), br2 = V_ZERO(), bi2 = V_ZERO();
      int k = 0;
      AP_TD_NO_UNROLL
      for (; k + 1 < L; k += 2) {
        const float *p = x + i + (size_t)k;
        AP_TD_HIDE_PTR(p);
        const vf wr0 = V_SET1(tr[k]), wi0 = V_SET1(ti[k]);
        const vf x00 = V_LOADU(p), x10 = V_LOADU(p + W), x20 = V_LOADU(p + 2 * W);
        ar0 = V_FMADD(wr0, x00, ar0); ai0 = V_FMADD(wi0, x00, ai0);
        ar1 = V_FMADD(wr0, x10, ar1); ai1 = V_FMADD(wi0, x10, ai1);
        ar2 = V_FMADD(wr0, x20, ar2); ai2 = V_FMADD(wi0, x20, ai2);
        const vf wr1 = V_SET1(tr[k + 1]), wi1 = V_SET1(ti[k + 1]);
        const vf x01 = V_LOADU(p + 1), x11 = V_LOADU(p + W + 1), x21 = V_LOADU(p + 2 * W + 1);
        br0 = V_FMADD(wr1, x01, br0); bi0 = V_FMADD(wi1, x01, bi0);
        br1 = V_FMADD(wr1, x11, br1); bi1 = V_FMADD(wi1, x11, bi1);
        br2 = V_FMADD(wr1, x21, br2); bi2 = V_FMADD(wi1, x21, bi2);
      }
      for (; k < L; k++) {
        const float *p = x + i + (size_t)k;
        const vf wr0 = V_SET1(tr[k]), wi0 = V_SET1(ti[k]);
        const vf x00 = V_LOADU(p), x10 = V_LOADU(p + W), x20 = V_LOADU(p + 2 * W);
        ar0 = V_FMADD(wr0, x00, ar0); ai0 = V_FMADD(wi0, x00, ai0);
        ar1 = V_FMADD(wr0, x10, ar1); ai1 = V_FMADD(wi0, x10, ai1);
        ar2 = V_FMADD(wr0, x20, ar2); ai2 = V_FMADD(wi0, x20, ai2);
      }
      v_inter(out + 2 * i, V_ADD(ar0, br0), V_ADD(ai0, bi0));
      v_inter(out + 2 * (i + W), V_ADD(ar1, br1), V_ADD(ai1, bi1));
      v_inter(out + 2 * (i + 2 * W), V_ADD(ar2, br2), V_ADD(ai2, bi2));
    }
  }
  for (; i + 2 * W <= nl; i += 2 * W) {
#if !defined(AP_SIMD_AVX1)
    vf ar0 = V_ZERO(), ai0 = V_ZERO(), ar1 = V_ZERO(), ai1 = V_ZERO();
    vf br0 = V_ZERO(), bi0 = V_ZERO(), br1 = V_ZERO(), bi1 = V_ZERO();
    vf cr0 = V_ZERO(), ci0 = V_ZERO(), cr1 = V_ZERO(), ci1 = V_ZERO();
    int k = 0;
    AP_TD_NO_UNROLL
    for (; k + 2 < L; k += 3) {
      const float *p = x + i + (size_t)k;
      AP_TD_HIDE_PTR(p);
      {
        const vf wr = V_SET1(tr[k]), wi = V_SET1(ti[k]);
        const vf x0 = V_LOADU(p);
        ar0 = V_FMADD(wr, x0, ar0); ai0 = V_FMADD(wi, x0, ai0);
        const vf x1 = V_LOADU(p + W);
        ar1 = V_FMADD(wr, x1, ar1); ai1 = V_FMADD(wi, x1, ai1);
      }
      {
        const vf wr = V_SET1(tr[k + 1]), wi = V_SET1(ti[k + 1]);
        const vf x0 = V_LOADU(p + 1);
        br0 = V_FMADD(wr, x0, br0); bi0 = V_FMADD(wi, x0, bi0);
        const vf x1 = V_LOADU(p + W + 1);
        br1 = V_FMADD(wr, x1, br1); bi1 = V_FMADD(wi, x1, bi1);
      }
      {
        const vf wr = V_SET1(tr[k + 2]), wi = V_SET1(ti[k + 2]);
        const vf x0 = V_LOADU(p + 2);
        cr0 = V_FMADD(wr, x0, cr0); ci0 = V_FMADD(wi, x0, ci0);
        const vf x1 = V_LOADU(p + W + 2);
        cr1 = V_FMADD(wr, x1, cr1); ci1 = V_FMADD(wi, x1, ci1);
      }
    }
    for (; k < L; k++) {
      const float *p = x + i + (size_t)k;
      const vf wr = V_SET1(tr[k]), wi = V_SET1(ti[k]);
      const vf x0 = V_LOADU(p), x1 = V_LOADU(p + W);
      ar0 = V_FMADD(wr, x0, ar0); ai0 = V_FMADD(wi, x0, ai0);
      ar1 = V_FMADD(wr, x1, ar1); ai1 = V_FMADD(wi, x1, ai1);
    }
    v_inter(out + 2 * i, V_ADD(V_ADD(ar0, br0), cr0), V_ADD(V_ADD(ai0, bi0), ci0));
    v_inter(out + 2 * (i + W), V_ADD(V_ADD(ar1, br1), cr1), V_ADD(V_ADD(ai1, bi1), ci1));
#else
    vf ar0 = V_ZERO(), ai0 = V_ZERO(), ar1 = V_ZERO(), ai1 = V_ZERO();
    vf br0 = V_ZERO(), bi0 = V_ZERO(), br1 = V_ZERO(), bi1 = V_ZERO();
    int k = 0;
    AP_TD_NO_UNROLL
    for (; k + 1 < L; k += 2) {
      const float *p = x + i + (size_t)k;
      AP_TD_HIDE_PTR(p);
      const vf wr0 = V_SET1(tr[k]), wi0 = V_SET1(ti[k]);
      const vf x00 = V_LOADU(p), x10 = V_LOADU(p + W);
      ar0 = V_FMADD(wr0, x00, ar0); ai0 = V_FMADD(wi0, x00, ai0);
      ar1 = V_FMADD(wr0, x10, ar1); ai1 = V_FMADD(wi0, x10, ai1);
      const vf wr1 = V_SET1(tr[k + 1]), wi1 = V_SET1(ti[k + 1]);
      const vf x01 = V_LOADU(p + 1), x11 = V_LOADU(p + W + 1);
      br0 = V_FMADD(wr1, x01, br0); bi0 = V_FMADD(wi1, x01, bi0);
      br1 = V_FMADD(wr1, x11, br1); bi1 = V_FMADD(wi1, x11, bi1);
    }
    for (; k < L; k++) {
      const float *p = x + i + (size_t)k;
      const vf wr0 = V_SET1(tr[k]), wi0 = V_SET1(ti[k]);
      const vf x00 = V_LOADU(p), x10 = V_LOADU(p + W);
      ar0 = V_FMADD(wr0, x00, ar0); ai0 = V_FMADD(wi0, x00, ai0);
      ar1 = V_FMADD(wr0, x10, ar1); ai1 = V_FMADD(wi0, x10, ai1);
    }
    v_inter(out + 2 * i, V_ADD(ar0, br0), V_ADD(ai0, bi0));
    v_inter(out + 2 * (i + W), V_ADD(ar1, br1), V_ADD(ai1, bi1));
#endif
  }
  for (; i + W <= nl; i += W) {
    if constexpr (AP_W >= 16) {
      vf ar = V_ZERO(), br = V_ZERO(), cr = V_ZERO(), dr = V_ZERO();
      vf ai = V_ZERO(), bi = V_ZERO(), ci = V_ZERO(), di = V_ZERO();
      int k = 0;
      AP_TD_NO_UNROLL
      for (; k + 3 < L; k += 4) {
        const float *p = x + i + (size_t)k;
        AP_TD_HIDE_PTR(p);
        const vf x0 = V_LOADU(p), x1 = V_LOADU(p + 1);
        ar = V_FMADD(V_SET1(tr[k]), x0, ar);
        ai = V_FMADD(V_SET1(ti[k]), x0, ai);
        br = V_FMADD(V_SET1(tr[k + 1]), x1, br);
        bi = V_FMADD(V_SET1(ti[k + 1]), x1, bi);
        const vf x2 = V_LOADU(p + 2), x3 = V_LOADU(p + 3);
        cr = V_FMADD(V_SET1(tr[k + 2]), x2, cr);
        ci = V_FMADD(V_SET1(ti[k + 2]), x2, ci);
        dr = V_FMADD(V_SET1(tr[k + 3]), x3, dr);
        di = V_FMADD(V_SET1(ti[k + 3]), x3, di);
      }
      for (; k < L; k++) {
        const vf x0 = V_LOADU(x + i + (size_t)k);
        ar = V_FMADD(V_SET1(tr[k]), x0, ar);
        ai = V_FMADD(V_SET1(ti[k]), x0, ai);
      }
      v_inter(out + 2 * i, V_ADD(V_ADD(ar, br), V_ADD(cr, dr)), V_ADD(V_ADD(ai, bi), V_ADD(ci, di)));
    } else {
      vf ar = V_ZERO(), br = V_ZERO(), ai = V_ZERO(), bi = V_ZERO();
      int k = 0;
      AP_TD_NO_UNROLL
      for (; k + 1 < L; k += 2) {
        const float *p = x + i + (size_t)k;
        AP_TD_HIDE_PTR(p);
        const vf x0 = V_LOADU(p), x1 = V_LOADU(p + 1);
        ar = V_FMADD(V_SET1(tr[k]), x0, ar);
        ai = V_FMADD(V_SET1(ti[k]), x0, ai);
        br = V_FMADD(V_SET1(tr[k + 1]), x1, br);
        bi = V_FMADD(V_SET1(ti[k + 1]), x1, bi);
      }
      for (; k < L; k++) {
        const vf x0 = V_LOADU(x + i + (size_t)k);
        ar = V_FMADD(V_SET1(tr[k]), x0, ar);
        ai = V_FMADD(V_SET1(ti[k]), x0, ai);
      }
      v_inter(out + 2 * i, V_ADD(ar, br), V_ADD(ai, bi));
    }
  }
  for (; i < nl; i++) {
    float ar = 0.f, br = 0.f, ai = 0.f, bi = 0.f;
    int k = 0;
    for (; k + 1 < L; k += 2) {
      const float x0 = x[i + k], x1 = x[i + k + 1];
      ar += tr[k] * x0; ai += ti[k] * x0;
      br += tr[k + 1] * x1; bi += ti[k + 1] * x1;
    }
    for (; k < L; k++) {
      const float x0 = x[i + k];
      ar += tr[k] * x0; ai += ti[k] * x0;
    }
    out[2 * i] = ar + br;
    out[2 * i + 1] = ai + bi;
  }
}

/* Interleaved complex x with split conjugated complex taps (tr, ti): (xr + j xi)(tr + j ti).
   Accumulate u = sum tr[k]*z and v = sum ti[k]*z directly on interleaved x with zero shuffles
   in the inner tap loop, then deinterleave and combine once per lag block after summing over k. */
static HWY_INLINE void td_store_cc_w(float *HWY_RESTRICT out, vf u0, vf u1, vf v0, vf v1) {
  vf rr, ri, ir, ii;
  v_deint_vec(u0, u1, &rr, &ri);
  v_deint_vec(v0, v1, &ir, &ii);
  v_inter(out, V_SUB(rr, ii), V_ADD(ri, ir));
}

static void td_corr_cc(const float *HWY_RESTRICT x, const float *HWY_RESTRICT tr,
                       const float *HWY_RESTRICT ti, int L, int nlag, float *HWY_RESTRICT out) {
  const size_t nl = (size_t)nlag, W = (size_t)AP_W;
  size_t i = 0;
  /* 2*W complex lags (4*W floats): 16 FMA chains on AVX-512, 8 FMA chains on 16-reg targets. */
  for (; i + 2 * W <= nl; i += 2 * W) {
    if constexpr (AP_W >= 16) {
      vf u0a = V_ZERO(), v0a = V_ZERO(), u1a = V_ZERO(), v1a = V_ZERO();
      vf u2a = V_ZERO(), v2a = V_ZERO(), u3a = V_ZERO(), v3a = V_ZERO();
      vf u0b = V_ZERO(), v0b = V_ZERO(), u1b = V_ZERO(), v1b = V_ZERO();
      vf u2b = V_ZERO(), v2b = V_ZERO(), u3b = V_ZERO(), v3b = V_ZERO();
      int k = 0;
      AP_TD_NO_UNROLL
      for (; k + 1 < L; k += 2) {
        const float *p = x + 2 * (i + (size_t)k);
        AP_TD_HIDE_PTR(p);
        {
          const vf wr = V_SET1(tr[k]), wi = V_SET1(ti[k]);
          const vf z0 = V_LOADU(p), z1 = V_LOADU(p + W);
          u0a = V_FMADD(wr, z0, u0a); v0a = V_FMADD(wi, z0, v0a);
          u1a = V_FMADD(wr, z1, u1a); v1a = V_FMADD(wi, z1, v1a);
          const vf z2 = V_LOADU(p + 2 * W), z3 = V_LOADU(p + 3 * W);
          u2a = V_FMADD(wr, z2, u2a); v2a = V_FMADD(wi, z2, v2a);
          u3a = V_FMADD(wr, z3, u3a); v3a = V_FMADD(wi, z3, v3a);
        }
        {
          const vf wr = V_SET1(tr[k + 1]), wi = V_SET1(ti[k + 1]);
          const vf z0 = V_LOADU(p + 2), z1 = V_LOADU(p + W + 2);
          u0b = V_FMADD(wr, z0, u0b); v0b = V_FMADD(wi, z0, v0b);
          u1b = V_FMADD(wr, z1, u1b); v1b = V_FMADD(wi, z1, v1b);
          const vf z2 = V_LOADU(p + 2 * W + 2), z3 = V_LOADU(p + 3 * W + 2);
          u2b = V_FMADD(wr, z2, u2b); v2b = V_FMADD(wi, z2, v2b);
          u3b = V_FMADD(wr, z3, u3b); v3b = V_FMADD(wi, z3, v3b);
        }
      }
      for (; k < L; k++) {
        const float *p = x + 2 * (i + (size_t)k);
        const vf wr = V_SET1(tr[k]), wi = V_SET1(ti[k]);
        const vf z0 = V_LOADU(p), z1 = V_LOADU(p + W);
        u0a = V_FMADD(wr, z0, u0a); v0a = V_FMADD(wi, z0, v0a);
        u1a = V_FMADD(wr, z1, u1a); v1a = V_FMADD(wi, z1, v1a);
        const vf z2 = V_LOADU(p + 2 * W), z3 = V_LOADU(p + 3 * W);
        u2a = V_FMADD(wr, z2, u2a); v2a = V_FMADD(wi, z2, v2a);
        u3a = V_FMADD(wr, z3, u3a); v3a = V_FMADD(wi, z3, v3a);
      }
      td_store_cc_w(out + 2 * i, V_ADD(u0a, u0b), V_ADD(u1a, u1b), V_ADD(v0a, v0b), V_ADD(v1a, v1b));
      td_store_cc_w(out + 2 * (i + W), V_ADD(u2a, u2b), V_ADD(u3a, u3b), V_ADD(v2a, v2b), V_ADD(v3a, v3b));
    } else {
      vf u0 = V_ZERO(), v0 = V_ZERO(), u1 = V_ZERO(), v1 = V_ZERO();
      vf u2 = V_ZERO(), v2 = V_ZERO(), u3 = V_ZERO(), v3 = V_ZERO();
      AP_TD_NO_UNROLL
      for (int k = 0; k < L; k++) {
        const float *p = x + 2 * (i + (size_t)k);
        AP_TD_HIDE_PTR(p);
        const vf wr = V_SET1(tr[k]), wi = V_SET1(ti[k]);
        const vf z0 = V_LOADU(p);
        u0 = V_FMADD(wr, z0, u0); v0 = V_FMADD(wi, z0, v0);
        const vf z1 = V_LOADU(p + W);
        u1 = V_FMADD(wr, z1, u1); v1 = V_FMADD(wi, z1, v1);
        const vf z2 = V_LOADU(p + 2 * W);
        u2 = V_FMADD(wr, z2, u2); v2 = V_FMADD(wi, z2, v2);
        const vf z3 = V_LOADU(p + 3 * W);
        u3 = V_FMADD(wr, z3, u3); v3 = V_FMADD(wi, z3, v3);
      }
      td_store_cc_w(out + 2 * i, u0, u1, v0, v1);
      td_store_cc_w(out + 2 * (i + W), u2, u3, v2, v3);
    }
  }
  /* 1*W complex lags (2*W floats): 8 FMA chains across k += 2. */
  for (; i + W <= nl; i += W) {
    vf u0a = V_ZERO(), v0a = V_ZERO(), u1a = V_ZERO(), v1a = V_ZERO();
    vf u0b = V_ZERO(), v0b = V_ZERO(), u1b = V_ZERO(), v1b = V_ZERO();
    int k = 0;
    AP_TD_NO_UNROLL
    for (; k + 1 < L; k += 2) {
      const float *p = x + 2 * (i + (size_t)k);
      AP_TD_HIDE_PTR(p);
      {
        const vf wr = V_SET1(tr[k]), wi = V_SET1(ti[k]);
        const vf z0 = V_LOADU(p);
        u0a = V_FMADD(wr, z0, u0a); v0a = V_FMADD(wi, z0, v0a);
        const vf z1 = V_LOADU(p + W);
        u1a = V_FMADD(wr, z1, u1a); v1a = V_FMADD(wi, z1, v1a);
      }
      {
        const vf wr = V_SET1(tr[k + 1]), wi = V_SET1(ti[k + 1]);
        const vf z0 = V_LOADU(p + 2);
        u0b = V_FMADD(wr, z0, u0b); v0b = V_FMADD(wi, z0, v0b);
        const vf z1 = V_LOADU(p + W + 2);
        u1b = V_FMADD(wr, z1, u1b); v1b = V_FMADD(wi, z1, v1b);
      }
    }
    for (; k < L; k++) {
      const float *p = x + 2 * (i + (size_t)k);
      const vf wr = V_SET1(tr[k]), wi = V_SET1(ti[k]);
      const vf z0 = V_LOADU(p), z1 = V_LOADU(p + W);
      u0a = V_FMADD(wr, z0, u0a); v0a = V_FMADD(wi, z0, v0a);
      u1a = V_FMADD(wr, z1, u1a); v1a = V_FMADD(wi, z1, v1a);
    }
    td_store_cc_w(out + 2 * i, V_ADD(u0a, u0b), V_ADD(u1a, u1b), V_ADD(v0a, v0b), V_ADD(v1a, v1b));
  }
  /* W/2 complex lags (1*W floats): covers 8-lag tail on AVX-512, 4-lag on AVX2/AVX1, 2-lag on SSE4. */
  if (i + W / 2 <= nl) {
    vf u0a = V_ZERO(), v0a = V_ZERO(), u0b = V_ZERO(), v0b = V_ZERO();
    int k = 0;
    AP_TD_NO_UNROLL
    for (; k + 1 < L; k += 2) {
      const float *p = x + 2 * (i + (size_t)k);
      const vf z0 = V_LOADU(p), z1 = V_LOADU(p + 2);
      u0a = V_FMADD(V_SET1(tr[k]), z0, u0a);
      v0a = V_FMADD(V_SET1(ti[k]), z0, v0a);
      u0b = V_FMADD(V_SET1(tr[k + 1]), z1, u0b);
      v0b = V_FMADD(V_SET1(ti[k + 1]), z1, v0b);
    }
    for (; k < L; k++) {
      const vf z0 = V_LOADU(x + 2 * (i + (size_t)k));
      u0a = V_FMADD(V_SET1(tr[k]), z0, u0a);
      v0a = V_FMADD(V_SET1(ti[k]), z0, v0a);
    }
    alignas(64) float tmp[2 * AP_W];
    const vf z = V_ZERO();
    td_store_cc_w(tmp, V_ADD(u0a, u0b), z, V_ADD(v0a, v0b), z);
    V_STOREU(out + 2 * i, V_LOADU(tmp));
    i += W / 2;
  }
  for (; i < nl; i++) {
    float ar = 0.f, ai = 0.f;
    for (int k = 0; k < L; k++) {
      const float xr = x[2 * (i + (size_t)k)], xi = x[2 * (i + (size_t)k) + 1];
      ar += tr[k] * xr - ti[k] * xi;
      ai += tr[k] * xi + ti[k] * xr;
    }
    out[2 * i] = ar;
    out[2 * i + 1] = ai;
  }
}

static void td_corr_ex(const float *x, int x_real, const float *tr, const float *ti, int L,
                       int nlag, float *out) {
  if (x_real) td_corr_rc(x, tr, ti, L, nlag, out);
  else if (!ti) td_corr(x, tr, L, nlag, out);
  else td_corr_cc(x, tr, ti, L, nlag, out);
}

}  // namespace HWY_NAMESPACE
}  // namespace ap
HWY_AFTER_NAMESPACE();

#endif
