/* Tier-0 pair centroid scoring (gatechain.cluster_tier0_candidates), under Highway's dispatch.
 *
 * For a chunk of mc unit-variance coarse template vectors U (mc x len, split real and
 * imaginary) and nsh candidate lag shifts S (nsh x len, unit-modulus phases), the coherence
 * of templates a < b at shift s is |sum_k conj(U_a[k]) U_b[k] S_s[k]|^2; the score of the pair
 * is its largest over the shifts and the shift is the first (in S's order) that reaches it.
 * Pairs whose variances v differ by more than 15% are not scored (0).
 *
 * The templates are laid out transposed once (len x mcp, mc padded to a multiple of the
 * vector width with zeros) and each shift's B = U S_s is a vector multiply by a broadcast
 * phase, so the inner loop runs over b in vector lanes with a's values broadcast:
 * accumulators in registers across the band, nothing to reduce across lanes. A shift's set
 * is 8 len mcp bytes (196 KB at len 512, mc 48), inside L2. The plain C loop this replaced
 * (_core.c) ran 4 SSE4 lanes and reduced a dot product per pair and shift. */
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#if AP_HAVE_AVX1
#include <immintrin.h>
#include "backend.h"
#endif

#undef HWY_TARGET_INCLUDE
#define HWY_TARGET_INCLUDE "tier0.cc"
#include "hwy/foreach_target.h"  // must come before highway.h
#include "hwy/highway.h"
#include "alloc.h"

HWY_BEFORE_NAMESPACE();
namespace ap_tier0 {
namespace HWY_NAMESPACE {
namespace hn = hwy::HWY_NAMESPACE;

/* Scores of every pair a < b of the chunk into r2[a mc + b] and the winning shift's index
   into bs[a mc + b]; every other entry 0. Returns 0, or -1 when out of memory. Four rows of
   a share each load of B (eight independent multiply-add chains: a row's two alone were
   bound by their latency). */
int PairScores(const float *ur, const float *ui, const float *sr, const float *si,
               const double *v, long long mc, long long len, long long nsh, float *r2,
               int32_t *bs) {
  const hn::ScalableTag<float> df;
  const hn::RebindToSigned<decltype(df)> di;
  using V = hn::Vec<decltype(df)>;
  const long long N = (long long)hn::Lanes(df);
  constexpr long long A = 4;                         // rows of a sharing each load of B
  memset(r2, 0, (size_t)(mc * mc) * sizeof(float));
  memset(bs, 0, (size_t)(mc * mc) * sizeof(int32_t));
  if (mc < 2) return 0;
  const long long mcp = (mc + N - 1) / N * N;
  const long long mca = (mc + A - 1) / A * A;
  // U transposed (len x mcp), one shift's B = U S_s transposed, and per pair the best score
  // and shift; 64-byte aligned: a row of mcp floats is whole vectors on every target. a's
  // rows are padded to a multiple of A with zeros (their scores are never read).
  float *utr = ap_alloc64((size_t)(len * mcp) * sizeof(float));
  float *uti = ap_alloc64((size_t)(len * mcp) * sizeof(float));
  float *tr = ap_alloc64((size_t)(len * mcp) * sizeof(float));
  float *ti = ap_alloc64((size_t)(len * mcp) * sizeof(float));
  float *ar = ap_alloc64((size_t)(mca * len) * sizeof(float));
  float *ai = ap_alloc64((size_t)(mca * len) * sizeof(float));
  float *best = ap_alloc64((size_t)(mca * mcp) * sizeof(float));
  int32_t *bidx = ap_alloc64((size_t)(mca * mcp) * sizeof(int32_t));
  int rc = -1;
  if (utr && uti && tr && ti && ar && ai && best && bidx) {
    rc = 0;
    memset(utr, 0, (size_t)(len * mcp) * sizeof(float));
    memset(uti, 0, (size_t)(len * mcp) * sizeof(float));
    for (long long b = 0; b < mc; b++)
      for (long long k = 0; k < len; k++) {
        utr[k * mcp + b] = ur[b * len + k];
        uti[k * mcp + b] = ui[b * len + k];
      }
    memset(ar, 0, (size_t)(mca * len) * sizeof(float));
    memset(ai, 0, (size_t)(mca * len) * sizeof(float));
    memcpy(ar, ur, (size_t)(mc * len) * sizeof(float));
    memcpy(ai, ui, (size_t)(mc * len) * sizeof(float));
    for (long long i = 0; i < mca * mcp; i++) { best[i] = -1.f; bidx[i] = 0; }
    for (long long s = 0; s < nsh; s++) {
      // B_s[k][b] = U_b[k] S_s[k]
      for (long long k = 0; k < len; k++) {
        const V c = hn::Set(df, sr[s * len + k]), d = hn::Set(df, si[s * len + k]);
        for (long long b0 = 0; b0 < mcp; b0 += N) {
          const V xr = hn::Load(df, utr + k * mcp + b0), xi = hn::Load(df, uti + k * mcp + b0);
          hn::Store(hn::NegMulAdd(d, xi, hn::Mul(c, xr)), df, tr + k * mcp + b0);
          hn::Store(hn::MulAdd(d, xr, hn::Mul(c, xi)), df, ti + k * mcp + b0);
        }
      }
      const auto vs = hn::Set(di, (int32_t)s);
      for (long long a0 = 0; a0 + 1 < mc; a0 += A) {
        const float *u0 = ar + a0 * len, *w0 = ai + a0 * len;
        for (long long b0 = (a0 + 1) / N * N; b0 < mcp; b0 += N) {
          // re_j += ur_j br + ui_j bi, im_j += ui_j br - ur_j bi for rows a0 .. a0 + 3
          V re0 = hn::Zero(df), re1 = re0, re2 = re0, re3 = re0;
          V im0 = re0, im1 = re0, im2 = re0, im3 = re0;
          for (long long k = 0; k < len; k++) {
            const V br = hn::Load(df, tr + k * mcp + b0), bi = hn::Load(df, ti + k * mcp + b0);
            V x = hn::Set(df, u0[k]), y = hn::Set(df, w0[k]);
            re0 = hn::MulAdd(x, br, hn::MulAdd(y, bi, re0));
            im0 = hn::MulAdd(y, br, hn::NegMulAdd(x, bi, im0));
            x = hn::Set(df, u0[len + k]); y = hn::Set(df, w0[len + k]);
            re1 = hn::MulAdd(x, br, hn::MulAdd(y, bi, re1));
            im1 = hn::MulAdd(y, br, hn::NegMulAdd(x, bi, im1));
            x = hn::Set(df, u0[2 * len + k]); y = hn::Set(df, w0[2 * len + k]);
            re2 = hn::MulAdd(x, br, hn::MulAdd(y, bi, re2));
            im2 = hn::MulAdd(y, br, hn::NegMulAdd(x, bi, im2));
            x = hn::Set(df, u0[3 * len + k]); y = hn::Set(df, w0[3 * len + k]);
            re3 = hn::MulAdd(x, br, hn::MulAdd(y, bi, re3));
            im3 = hn::MulAdd(y, br, hn::NegMulAdd(x, bi, im3));
          }
          const V vals[A] = {hn::MulAdd(re0, re0, hn::Mul(im0, im0)),
                             hn::MulAdd(re1, re1, hn::Mul(im1, im1)),
                             hn::MulAdd(re2, re2, hn::Mul(im2, im2)),
                             hn::MulAdd(re3, re3, hn::Mul(im3, im3))};
          for (long long j = 0; j < A; j++) {
            float *bp = best + (a0 + j) * mcp + b0;
            int32_t *ip = bidx + (a0 + j) * mcp + b0;
            const V old = hn::Load(df, bp);
            const auto gt = hn::Gt(vals[j], old);              // strictly greater: first wins
            hn::Store(hn::IfThenElse(gt, vals[j], old), df, bp);
            hn::Store(hn::IfThenElse(hn::RebindMask(di, gt), vs, hn::Load(di, ip)), di, ip);
          }
        }
      }
    }
    for (long long a = 0; a < mc; a++) {
      for (long long b = a + 1; b < mc; b++) {
        const double vmin = v[a] < v[b] ? v[a] : v[b], vmax = v[a] > v[b] ? v[a] : v[b];
        if (vmin < 0.85 * vmax) continue;
        r2[a * mc + b] = best[a * mcp + b];
        bs[a * mc + b] = bidx[a * mcp + b];
      }
    }
  }
  free(utr); free(uti); free(tr); free(ti); free(ar); free(ai); free(best); free(bidx);
  return rc;
}

/* Exact complex128 fine-lag refinement around each pair's coarse lag pdl[i] over
   [max(-R, pdl[i] - half_span), min(R, pdl[i] + half_span)], keeping prod_ab[i] L1-resident
   and avoiding (npairs, len) complex128 temporary shift matrices. */
void RefineLags(const double *prod_ab, const double *exp_all, const int64_t *pdl,
                long long npairs, long long len, long long R, long long half_span,
                int64_t *out_dl, double *out_g) {
  const hn::ScalableTag<double> dd;
  using VD = hn::Vec<decltype(dd)>;
  const long long W = (long long)hn::Lanes(dd);
  for (long long i = 0; i < npairs; i++) {
    const double *pa = prod_ab + i * 2 * len;
    long long lo = pdl[i] - half_span;
    long long hi = pdl[i] + half_span;
    if (lo < -R) lo = -R;
    if (hi > R) hi = R;
    double best_abs = -1.0, best_re = 0.0, best_im = 0.0;
    long long best_d = lo;
    for (long long dl = lo; dl <= hi; dl++) {
      const double *ex = exp_all + (dl + R) * 2 * len;
      VD vre = hn::Zero(dd), vim = hn::Zero(dd);
      long long k = 0;
      for (; k + W <= len; k += W) {
        VD ar, ai, br, bi;
        hn::LoadInterleaved2(dd, pa + 2 * k, ar, ai);
        hn::LoadInterleaved2(dd, ex + 2 * k, br, bi);
        vre = hn::NegMulAdd(ai, bi, hn::MulAdd(ar, br, vre));
        vim = hn::MulAdd(ai, br, hn::MulAdd(ar, bi, vim));
      }
      double re = hn::ReduceSum(dd, vre);
      double im = hn::ReduceSum(dd, vim);
      for (; k < len; k++) {
        const double ar = pa[2 * k], ai = pa[2 * k + 1];
        const double br = ex[2 * k], bi = ex[2 * k + 1];
        re += ar * br - ai * bi;
        im += ar * bi + ai * br;
      }
      const double mag = hypot(re, im);
      if (mag > best_abs) {
        best_abs = mag;
        best_d = dl;
        best_re = re;
        best_im = im;
      }
    }
    out_dl[i] = (int64_t)best_d;
    if (out_g) {
      out_g[2 * i] = best_re;
      out_g[2 * i + 1] = best_im;
    }
  }
}

}  // namespace HWY_NAMESPACE
}  // namespace ap_tier0
HWY_AFTER_NAMESPACE();

#if HWY_ONCE
#if AP_HAVE_AVX1
HWY_PUSH_ATTRIBUTES("avx")
namespace ap_tier0 {
namespace avx1 {

static int PairScores(const float *ur, const float *ui, const float *sr, const float *si,
                      const double *v, long long mc, long long len, long long nsh, float *r2,
                      int32_t *bs) {
  constexpr long long N = 8;
  constexpr long long A = 4;
  memset(r2, 0, (size_t)(mc * mc) * sizeof(float));
  memset(bs, 0, (size_t)(mc * mc) * sizeof(int32_t));
  if (mc < 2) return 0;
  const long long mcp = (mc + N - 1) / N * N;
  const long long mca = (mc + A - 1) / A * A;
  float *utr = ap_alloc64((size_t)(len * mcp) * sizeof(float));
  float *uti = ap_alloc64((size_t)(len * mcp) * sizeof(float));
  float *tr = ap_alloc64((size_t)(len * mcp) * sizeof(float));
  float *ti = ap_alloc64((size_t)(len * mcp) * sizeof(float));
  float *ar = ap_alloc64((size_t)(mca * len) * sizeof(float));
  float *ai = ap_alloc64((size_t)(mca * len) * sizeof(float));
  float *best = ap_alloc64((size_t)(mca * mcp) * sizeof(float));
  int32_t *bidx = ap_alloc64((size_t)(mca * mcp) * sizeof(int32_t));
  int rc = -1;
  if (utr && uti && tr && ti && ar && ai && best && bidx) {
    rc = 0;
    memset(utr, 0, (size_t)(len * mcp) * sizeof(float));
    memset(uti, 0, (size_t)(len * mcp) * sizeof(float));
    for (long long b = 0; b < mc; b++)
      for (long long k = 0; k < len; k++) {
        utr[k * mcp + b] = ur[b * len + k];
        uti[k * mcp + b] = ui[b * len + k];
      }
    memset(ar, 0, (size_t)(mca * len) * sizeof(float));
    memset(ai, 0, (size_t)(mca * len) * sizeof(float));
    memcpy(ar, ur, (size_t)(mc * len) * sizeof(float));
    memcpy(ai, ui, (size_t)(mc * len) * sizeof(float));
    for (long long i = 0; i < mca * mcp; i++) { best[i] = -1.f; bidx[i] = 0; }
    for (long long s = 0; s < nsh; s++) {
      for (long long k = 0; k < len; k++) {
        const __m256 c = _mm256_broadcast_ss(sr + s * len + k);
        const __m256 d = _mm256_broadcast_ss(si + s * len + k);
        for (long long b0 = 0; b0 < mcp; b0 += N) {
          const __m256 xr = _mm256_load_ps(utr + k * mcp + b0);
          const __m256 xi = _mm256_load_ps(uti + k * mcp + b0);
          _mm256_store_ps(tr + k * mcp + b0, _mm256_sub_ps(_mm256_mul_ps(c, xr), _mm256_mul_ps(d, xi)));
          _mm256_store_ps(ti + k * mcp + b0, _mm256_add_ps(_mm256_mul_ps(d, xr), _mm256_mul_ps(c, xi)));
        }
      }
      const int32_t s32 = (int32_t)s;
      const __m256 vs_ps = _mm256_broadcast_ss((const float *)&s32);
      for (long long a0 = 0; a0 + 1 < mc; a0 += A) {
        const float *u0 = ar + a0 * len, *w0 = ai + a0 * len;
        for (long long b0 = (a0 + 1) / N * N; b0 < mcp; b0 += N) {
          __m256 re0 = _mm256_setzero_ps(), re1 = re0, re2 = re0, re3 = re0;
          __m256 im0 = re0, im1 = re0, im2 = re0, im3 = re0;
          for (long long k = 0; k < len; k++) {
            const __m256 br = _mm256_load_ps(tr + k * mcp + b0);
            const __m256 bi = _mm256_load_ps(ti + k * mcp + b0);
            __m256 x = _mm256_broadcast_ss(u0 + k), y = _mm256_broadcast_ss(w0 + k);
            re0 = _mm256_add_ps(_mm256_mul_ps(x, br), _mm256_add_ps(_mm256_mul_ps(y, bi), re0));
            im0 = _mm256_add_ps(_mm256_mul_ps(y, br), _mm256_sub_ps(im0, _mm256_mul_ps(x, bi)));
            x = _mm256_broadcast_ss(u0 + len + k); y = _mm256_broadcast_ss(w0 + len + k);
            re1 = _mm256_add_ps(_mm256_mul_ps(x, br), _mm256_add_ps(_mm256_mul_ps(y, bi), re1));
            im1 = _mm256_add_ps(_mm256_mul_ps(y, br), _mm256_sub_ps(im1, _mm256_mul_ps(x, bi)));
            x = _mm256_broadcast_ss(u0 + 2 * len + k); y = _mm256_broadcast_ss(w0 + 2 * len + k);
            re2 = _mm256_add_ps(_mm256_mul_ps(x, br), _mm256_add_ps(_mm256_mul_ps(y, bi), re2));
            im2 = _mm256_add_ps(_mm256_mul_ps(y, br), _mm256_sub_ps(im2, _mm256_mul_ps(x, bi)));
            x = _mm256_broadcast_ss(u0 + 3 * len + k); y = _mm256_broadcast_ss(w0 + 3 * len + k);
            re3 = _mm256_add_ps(_mm256_mul_ps(x, br), _mm256_add_ps(_mm256_mul_ps(y, bi), re3));
            im3 = _mm256_add_ps(_mm256_mul_ps(y, br), _mm256_sub_ps(im3, _mm256_mul_ps(x, bi)));
          }
          const __m256 vals[A] = {
            _mm256_add_ps(_mm256_mul_ps(re0, re0), _mm256_mul_ps(im0, im0)),
            _mm256_add_ps(_mm256_mul_ps(re1, re1), _mm256_mul_ps(im1, im1)),
            _mm256_add_ps(_mm256_mul_ps(re2, re2), _mm256_mul_ps(im2, im2)),
            _mm256_add_ps(_mm256_mul_ps(re3, re3), _mm256_mul_ps(im3, im3))
          };
          for (long long j = 0; j < A; j++) {
            float *bp = best + (a0 + j) * mcp + b0;
            float *ip = (float *)(bidx + (a0 + j) * mcp + b0);
            const __m256 old = _mm256_load_ps(bp);
            const __m256 gt = _mm256_cmp_ps(vals[j], old, _CMP_GT_OQ);
            _mm256_store_ps(bp, _mm256_blendv_ps(old, vals[j], gt));
            _mm256_store_ps(ip, _mm256_blendv_ps(_mm256_load_ps(ip), vs_ps, gt));
          }
        }
      }
    }
    for (long long a = 0; a < mc; a++) {
      for (long long b = a + 1; b < mc; b++) {
        const double vmin = v[a] < v[b] ? v[a] : v[b], vmax = v[a] > v[b] ? v[a] : v[b];
        if (vmin < 0.85 * vmax) continue;
        r2[a * mc + b] = best[a * mcp + b];
        bs[a * mc + b] = bidx[a * mcp + b];
      }
    }
  }
  free(utr); free(uti); free(tr); free(ti); free(ar); free(ai); free(best); free(bidx);
  return rc;
}

static void RefineLags(const double *prod_ab, const double *exp_all, const int64_t *pdl,
                       long long npairs, long long len, long long R, long long half_span,
                       int64_t *out_dl, double *out_g) {
  for (long long i = 0; i < npairs; i++) {
    const double *pa = prod_ab + i * 2 * len;
    long long lo = pdl[i] - half_span;
    long long hi = pdl[i] + half_span;
    if (lo < -R) lo = -R;
    if (hi > R) hi = R;
    double best_abs = -1.0, best_re = 0.0, best_im = 0.0;
    long long best_d = lo;
    for (long long dl = lo; dl <= hi; dl++) {
      const double *ex = exp_all + (dl + R) * 2 * len;
      __m256d vre = _mm256_setzero_pd(), vim = _mm256_setzero_pd();
      long long k = 0;
      for (; k + 4 <= len; k += 4) {
        const __m256d p0 = _mm256_loadu_pd(pa + 2 * k);
        const __m256d p1 = _mm256_loadu_pd(pa + 2 * k + 4);
        const __m256d ar = _mm256_unpacklo_pd(p0, p1);
        const __m256d ai = _mm256_unpackhi_pd(p0, p1);
        const __m256d e0 = _mm256_loadu_pd(ex + 2 * k);
        const __m256d e1 = _mm256_loadu_pd(ex + 2 * k + 4);
        const __m256d br = _mm256_unpacklo_pd(e0, e1);
        const __m256d bi = _mm256_unpackhi_pd(e0, e1);
        vre = _mm256_sub_pd(_mm256_add_pd(_mm256_mul_pd(ar, br), vre), _mm256_mul_pd(ai, bi));
        vim = _mm256_add_pd(_mm256_mul_pd(ai, br), _mm256_add_pd(_mm256_mul_pd(ar, bi), vim));
      }
      alignas(32) double rbuf[4], ibuf[4];
      _mm256_store_pd(rbuf, vre);
      _mm256_store_pd(ibuf, vim);
      double re = (rbuf[0] + rbuf[2]) + (rbuf[1] + rbuf[3]);
      double im = (ibuf[0] + ibuf[2]) + (ibuf[1] + ibuf[3]);
      for (; k < len; k++) {
        const double ar = pa[2 * k], ai = pa[2 * k + 1];
        const double br = ex[2 * k], bi = ex[2 * k + 1];
        re += ar * br - ai * bi;
        im += ar * bi + ai * br;
      }
      const double mag = hypot(re, im);
      if (mag > best_abs) {
        best_abs = mag;
        best_d = dl;
        best_re = re;
        best_im = im;
      }
    }
    out_dl[i] = (int64_t)best_d;
    if (out_g) {
      out_g[2 * i] = best_re;
      out_g[2 * i + 1] = best_im;
    }
  }
}

}  // namespace avx1
}  // namespace ap_tier0
HWY_POP_ATTRIBUTES
#endif

namespace ap_tier0 {
HWY_EXPORT(PairScores);
HWY_EXPORT(RefineLags);
#if AP_HAVE_AVX1
static inline bool use_avx1() {
  const ap_backend *b = ap_backend_active();
  return b && !strcmp(b->name, "AVX");
}
#endif
/* Dispatched unqualified from inside the namespace (see gauss.cc). */
static int Dispatch(const float *ur, const float *ui, const float *sr, const float *si,
                    const double *v, long long mc, long long len, long long nsh, float *r2,
                    int32_t *bs) {
#if AP_HAVE_AVX1
  if (use_avx1()) return avx1::PairScores(ur, ui, sr, si, v, mc, len, nsh, r2, bs);
#endif
  return HWY_DYNAMIC_DISPATCH(PairScores)(ur, ui, sr, si, v, mc, len, nsh, r2, bs);
}
static void DispatchRefine(const double *prod_ab, const double *exp_all, const int64_t *pdl,
                           long long npairs, long long len, long long R, long long half_span,
                           int64_t *out_dl, double *out_g) {
#if AP_HAVE_AVX1
  if (use_avx1()) {
    avx1::RefineLags(prod_ab, exp_all, pdl, npairs, len, R, half_span, out_dl, out_g);
    return;
  }
#endif
  HWY_DYNAMIC_DISPATCH(RefineLags)(prod_ab, exp_all, pdl, npairs, len, R, half_span, out_dl, out_g);
}
}  // namespace ap_tier0
/* The tier-0 pair scores of an mc-template chunk (see the top of this file), for the best
   target this CPU runs. Returns 0, or -1 when out of memory. */
extern "C" int ap_tier0_pair_scores(const float *ur, const float *ui, const float *sr,
                                    const float *si, const double *v, long long mc,
                                    long long len, long long nsh, float *r2, int32_t *bs) {
  return ap_tier0::Dispatch(ur, ui, sr, si, v, mc, len, nsh, r2, bs);
}
extern "C" void ap_tier0_refine_lags(const double *prod_ab, const double *exp_all,
                                     const int64_t *pdl, long long npairs, long long len,
                                     long long R, long long half_span, int64_t *out_dl,
                                     double *out_g) {
  ap_tier0::DispatchRefine(prod_ab, exp_all, pdl, npairs, len, R, half_span, out_dl, out_g);
}
#endif
