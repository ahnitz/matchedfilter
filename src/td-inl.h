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
                                      int L, int two_vecs, float *HWY_RESTRICT out) {
  vf a0 = V_ZERO(), b0 = V_ZERO(), a1 = V_ZERO(), b1 = V_ZERO();
  int k = 0;
  for (; k + 1 < L; k += 2) {
    const float *p = x + 2 * (size_t)k;
    const vf w0 = V_SET1(taps[k]), w1 = V_SET1(taps[k + 1]);
    a0 = V_FMADD(w0, V_LOADU(p), a0);
    b0 = V_FMADD(w1, V_LOADU(p + 2), b0);
    if (two_vecs) {
      a1 = V_FMADD(w0, V_LOADU(p + AP_W), a1);
      b1 = V_FMADD(w1, V_LOADU(p + AP_W + 2), b1);
    }
  }
  for (; k < L; k++) {
    const float *p = x + 2 * (size_t)k;
    const vf w0 = V_SET1(taps[k]);
    a0 = V_FMADD(w0, V_LOADU(p), a0);
    if (two_vecs) a1 = V_FMADD(w0, V_LOADU(p + AP_W), a1);
  }
  V_STOREU(out, V_ADD(a0, b0));
  if (two_vecs) V_STOREU(out + AP_W, V_ADD(a1, b1));
}

/* Reads x[0, 2*(nlag + L - 1)) floats, writes out[0, 2*nlag). */
static void td_corr(const float *x, const float *taps, int L, int nlag, float *out) {
  const size_t nf = 2 * (size_t)nlag;
  const size_t W = (size_t)AP_W;
  size_t i = 0;
  for (; i + 2 * W <= nf; i += 2 * W) td_pass_cr_vec(x + i, taps, L, 1, out + i);
  if (i + W <= nf) { td_pass_cr_vec(x + i, taps, L, 0, out + i); i += W; }
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
    /* Real x, real taps: 1 FMA per (tap, lag), imaginary output is zero. */
    const vf z = V_ZERO();
    for (; i + 2 * W <= nl; i += 2 * W) {
      vf a0 = z, b0 = z, a1 = z, b1 = z;
      int k = 0;
      for (; k + 1 < L; k += 2) {
        const float *p = x + i + (size_t)k;
        const vf w0 = V_SET1(tr[k]), w1 = V_SET1(tr[k + 1]);
        a0 = V_FMADD(w0, V_LOADU(p), a0);
        b0 = V_FMADD(w1, V_LOADU(p + 1), b0);
        a1 = V_FMADD(w0, V_LOADU(p + W), a1);
        b1 = V_FMADD(w1, V_LOADU(p + W + 1), b1);
      }
      for (; k < L; k++) {
        const float *p = x + i + (size_t)k;
        const vf w0 = V_SET1(tr[k]);
        a0 = V_FMADD(w0, V_LOADU(p), a0);
        a1 = V_FMADD(w0, V_LOADU(p + W), a1);
      }
      v_inter(out + 2 * i, V_ADD(a0, b0), z);
      v_inter(out + 2 * (i + W), V_ADD(a1, b1), z);
    }
    for (; i + W <= nl; i += W) {
      vf a0 = z, b0 = z;
      int k = 0;
      for (; k + 1 < L; k += 2) {
        const float *p = x + i + (size_t)k;
        a0 = V_FMADD(V_SET1(tr[k]), V_LOADU(p), a0);
        b0 = V_FMADD(V_SET1(tr[k + 1]), V_LOADU(p + 1), b0);
      }
      for (; k < L; k++) a0 = V_FMADD(V_SET1(tr[k]), V_LOADU(x + i + (size_t)k), a0);
      v_inter(out + 2 * i, V_ADD(a0, b0), z);
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
  /* Real x, complex taps: AP_W lags per vector, 4 independent FMA chains (even/odd x re/im). */
  for (; i + W <= nl; i += W) {
    vf ar = V_ZERO(), br = V_ZERO(), ai = V_ZERO(), bi = V_ZERO();
    int k = 0;
    for (; k + 1 < L; k += 2) {
      const vf x0 = V_LOADU(x + i + (size_t)k), x1 = V_LOADU(x + i + (size_t)k + 1);
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

/* Interleaved complex x with split conjugated complex taps (tr, ti): (xr + j xi)(tr + j ti). */
static void td_corr_cc(const float *HWY_RESTRICT x, const float *HWY_RESTRICT tr,
                       const float *HWY_RESTRICT ti, int L, int nlag, float *HWY_RESTRICT out) {
  const size_t nl = (size_t)nlag, W = (size_t)AP_W;
  size_t i = 0;
  for (; i + W <= nl; i += W) {
    vf ar = V_ZERO(), br = V_ZERO(), ai = V_ZERO(), bi = V_ZERO();
    int k = 0;
    for (; k + 1 < L; k += 2) {
      vf xr0, xi0, xr1, xi1;
      v_deint(x + 2 * (i + (size_t)k), &xr0, &xi0);
      v_deint(x + 2 * (i + (size_t)k + 1), &xr1, &xi1);
      const vf wr0 = V_SET1(tr[k]), wi0 = V_SET1(ti[k]);
      const vf wr1 = V_SET1(tr[k + 1]), wi1 = V_SET1(ti[k + 1]);
      ar = V_FNMADD(wi0, xi0, V_FMADD(wr0, xr0, ar));
      ai = V_FMADD(wi0, xr0, V_FMADD(wr0, xi0, ai));
      br = V_FNMADD(wi1, xi1, V_FMADD(wr1, xr1, br));
      bi = V_FMADD(wi1, xr1, V_FMADD(wr1, xi1, bi));
    }
    for (; k < L; k++) {
      vf xr0, xi0;
      v_deint(x + 2 * (i + (size_t)k), &xr0, &xi0);
      const vf wr0 = V_SET1(tr[k]), wi0 = V_SET1(ti[k]);
      ar = V_FNMADD(wi0, xi0, V_FMADD(wr0, xr0, ar));
      ai = V_FMADD(wi0, xr0, V_FMADD(wr0, xi0, ai));
    }
    v_inter(out + 2 * i, V_ADD(ar, br), V_ADD(ai, bi));
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
