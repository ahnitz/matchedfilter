/* Q15 coarse screen: the pair-batched coarse transform in int16 fixed point.
 *
 * What it computes.  For QW (data, template) pairs at once -- lanes are
 * templates, twice as many as the float path's at the same vector width --
 * the same four-step transform of conj(d*t) the float pair path computes
 * (efft_prod, product-inl.h), then for every lane the largest |z|^2 over the
 * window, as round(re^2/2^15) + round(im^2/2^15), saturating.  It reports no peak: the caller compares
 * the maximum against the tier threshold LOWERED by an error margin and
 * re-runs the float tier on every pair that clears it, so the screen decides
 * only which pairs need the float answer (matchfilt.c, hmf.c).
 *
 * Range.  Nothing inside the transform rescales.  Every intermediate of an
 * FFT is a partial sum of products with unit-modulus weights, so its
 * magnitude is at most L1 = sum_k |p_k| plus accumulated rounding; the caller
 * quantises the inputs so that sum_k |d_k||t_k| / 2^15 (Cauchy-Schwarz:
 * <= |d|_2 |t|_2 / 2^15) stays at Q15_L1 (q15.h), leaving the rest of the
 * int16 range as headroom for rounding. Adds saturate rather than wrap, so
 * even an input outside that contract cannot alias into a large value.
 *
 * Error.  Each Q_MUL rounds to nearest; the error at the output is a sum of
 * those roundings over the transform -- the per-N margin in q15.h is set from
 * its measured distribution (tools/q15_error.py, docs/cpu-q15-gate.md).
 */
#include "q15.h"
#include "simd-inl.h"

#if defined(AP_Q15_INL_H_) == defined(HWY_TARGET_TOGGLE)
#ifdef AP_Q15_INL_H_
#undef AP_Q15_INL_H_
#else
#define AP_Q15_INL_H_
#endif

HWY_BEFORE_NAMESPACE();
namespace ap {
namespace HWY_NAMESPACE {

using ap_qtag = hn::CappedTag<int16_t, 2 * AP_W>;
constexpr ap_qtag AP_DQ{};
constexpr int AP_QW = (int)HWY_MAX_LANES_D(ap_qtag);
typedef hn::Vec<ap_qtag> vq;

#define Q_ZERO()       hn::Zero(AP_DQ)
#define Q_SET1(x)      hn::Set(AP_DQ, (int16_t)(x))
#define Q_LOADU(p)     hn::LoadU(AP_DQ, (const int16_t *)(p))
#define Q_ADD(a, b)    hn::SaturatedAdd((a), (b))
#define Q_SUB(a, b)    hn::SaturatedSub((a), (b))
#define Q_MUL(a, b)    hn::MulFixedPoint15((a), (b))

}  // namespace HWY_NAMESPACE
}  // namespace ap
HWY_AFTER_NAMESPACE();

#include "codelets-q15-inl.h"

HWY_BEFORE_NAMESPACE();
namespace ap {
namespace HWY_NAMESPACE {

static HWY_INLINE void qcodelet_prod(int m, const int16_t *restrict dq, const int16_t *restrict tr,
                                     const int16_t *restrict ti, vq *restrict ar, vq *restrict ai,
                                     long S, long DS, long TS){
  switch(m){
    case  8: qsr8_prod (dq,tr,ti,ar,ai,S,DS,TS); return;
    case 16: qsr16_prod(dq,tr,ti,ar,ai,S,DS,TS); return;
    default: qsr32_prod(dq,tr,ti,ar,ai,S,DS,TS); return;
  }
}
static HWY_INLINE void qcodelet_tw(int m, vq *restrict ar, vq *restrict ai, long S,
                                   const int16_t *restrict twr, const int16_t *restrict twi){
  switch(m){
    case  8: qsr8_tw (ar,ai,S,twr,twi); return;
    case 16: qsr16_tw(ar,ai,S,twr,twi); return;
    default: qsr32_tw(ar,ai,S,twr,twi); return;
  }
}

/* N x QW pairs: pass 1 forms the product as it loads (M2-point codelets down
   the columns), pass 2 applies the four-step twiddle as it loads (M1-point
   codelets along the rows), then the window's maximum per lane.
   dq is [N][3] = (dr, di, -di); tr/ti are [N][QW].  Bit l of *bits is set
   when lane l's maximum reaches lanethr[l]; lanemax, if not NULL, gets the
   QW maxima. */
static int q15_screen(size_t N, const int16_t *dq, const int16_t *tr, const int16_t *ti,
                      size_t ws, size_t we, const int16_t *lanethr, uint64_t *bits,
                      int16_t *lanemax, void *scratch){
  int M1, M2;
  if(ap_q15_factor(N, &M1, &M2)) return -1;
  const ap_q15_twiddles *tw = ap_q15_twiddle_table(N);
  if(!tw) return -1;
  const int st = M1 + 1;
  vq *X = (vq *)scratch, *Xi = X + (size_t)st * M2;
  for(int e1 = 0; e1 < M1; e1++)
    qcodelet_prod(M2, dq + 3 * e1, tr + (size_t)e1 * AP_QW, ti + (size_t)e1 * AP_QW,
                  X + e1, Xi + e1, st, 3L * M1, (long)M1 * AP_QW);
  for(int k2 = 0; k2 < M2; k2++)
    qcodelet_tw(M1, X + (size_t)k2 * st, Xi + (size_t)k2 * st, 1,
                tw->re + (size_t)k2 * M1, tw->im + (size_t)k2 * M1);
  /* Output k = k2 + M2*k1 sits at X[k2*st + k1]; the maximum does not care
     about order, so walk memory and clip each row to the window. */
  if(we > N) we = N;
  vq m0 = Q_ZERO(), m1 = Q_ZERO();
  for(int k2 = 0; k2 < M2; k2++){
    const long lo = (long)ws > k2 ? ((long)ws - k2 + M2 - 1) / M2 : 0;
    const long hi = (long)we > k2 ? ((long)we - k2 + M2 - 1) / M2 : 0;
    const vq *xr = X + (size_t)k2 * st, *xi = Xi + (size_t)k2 * st;
    long k1 = lo;
    for(; k1 + 1 < hi; k1 += 2){
      const vq a = xr[k1], b = xi[k1], c = xr[k1 + 1], d = xi[k1 + 1];
      m0 = hn::Max(m0, hn::SaturatedAdd(Q_MUL(a, a), Q_MUL(b, b)));
      m1 = hn::Max(m1, hn::SaturatedAdd(Q_MUL(c, c), Q_MUL(d, d)));
    }
    if(k1 < hi){
      const vq a = xr[k1], b = xi[k1];
      m0 = hn::Max(m0, hn::SaturatedAdd(Q_MUL(a, a), Q_MUL(b, b)));
    }
  }
  const vq mx = hn::Max(m0, m1);
  if(lanemax) hn::StoreU(mx, AP_DQ, lanemax);
  uint64_t b = 0;
  hn::StoreMaskBits(AP_DQ, hn::Ge(mx, hn::LoadU(AP_DQ, lanethr)), (uint8_t *)&b);
  *bits = b;
  return 0;
}

static int q15_lanes(void){ return AP_QW; }

}  // namespace HWY_NAMESPACE
}  // namespace ap
HWY_AFTER_NAMESPACE();

#endif
