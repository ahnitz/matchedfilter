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

}  // namespace HWY_NAMESPACE
}  // namespace ap_tier0
HWY_AFTER_NAMESPACE();

#if HWY_ONCE
namespace ap_tier0 {
HWY_EXPORT(PairScores);
/* Dispatched unqualified from inside the namespace (see gauss.cc). */
static int Dispatch(const float *ur, const float *ui, const float *sr, const float *si,
                    const double *v, long long mc, long long len, long long nsh, float *r2,
                    int32_t *bs) {
  return HWY_DYNAMIC_DISPATCH(PairScores)(ur, ui, sr, si, v, mc, len, nsh, r2, bs);
}
}  // namespace ap_tier0
/* The tier-0 pair scores of an mc-template chunk (see the top of this file), for the best
   target this CPU runs. Returns 0, or -1 when out of memory. */
extern "C" int ap_tier0_pair_scores(const float *ur, const float *ui, const float *sr,
                                    const float *si, const double *v, long long mc,
                                    long long len, long long nsh, float *r2, int32_t *bs) {
  return ap_tier0::Dispatch(ur, ui, sr, si, v, mc, len, nsh, r2, bs);
}
#endif
