/* Direct (time-domain) correlation of a complex series with real FIR taps over a short run
 * of consecutive lags: the refine's answer at the few lags a survivor's coarse tier points
 * at, without a whole-block transform.
 *
 *     out[i] = sum_{k<L} taps[k] * x[i + k],   i in [0, nlag)
 *
 * x and out are interleaved complex (re, im) floats; x must hold nlag + L - 1 samples.
 * Vectorised across the OUTPUT lags: a vector of N floats is N/2 consecutive lags, every
 * load is unit stride and each tap is one broadcast, so a single surviving pair fills every
 * lane (the pair-batched transforms vectorise across templates and run nearly empty on a
 * handful of survivors). Two vectors of lags, each split over even and odd taps, are four
 * independent FMA chains, which covers a 4-cycle FMA latency on two pipes.
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

template <bool kFull>
static HWY_INLINE void td_pass(const float *HWY_RESTRICT x, const float *HWY_RESTRICT taps, int L,
                               size_t n0, size_t n1, float *HWY_RESTRICT out) {
  const hn::ScalableTag<float> d;
  const size_t N = hn::Lanes(d);
  auto a0 = hn::Zero(d), b0 = hn::Zero(d), a1 = hn::Zero(d), b1 = hn::Zero(d);
  int k = 0;
  for (; k + 1 < L; k += 2) {
    const float *p = x + 2 * (size_t)k;
    const auto w0 = hn::Set(d, taps[k]), w1 = hn::Set(d, taps[k + 1]);
    if (kFull) {
      a0 = hn::MulAdd(w0, hn::LoadU(d, p), a0);
      b0 = hn::MulAdd(w1, hn::LoadU(d, p + 2), b0);
      if (n1) {
        a1 = hn::MulAdd(w0, hn::LoadU(d, p + N), a1);
        b1 = hn::MulAdd(w1, hn::LoadU(d, p + N + 2), b1);
      }
    } else {
      a0 = hn::MulAdd(w0, hn::LoadN(d, p, n0), a0);
      b0 = hn::MulAdd(w1, hn::LoadN(d, p + 2, n0), b0);
    }
  }
  for (; k < L; k++) {
    const float *p = x + 2 * (size_t)k;
    const auto w0 = hn::Set(d, taps[k]);
    if (kFull) {
      a0 = hn::MulAdd(w0, hn::LoadU(d, p), a0);
      if (n1) a1 = hn::MulAdd(w0, hn::LoadU(d, p + N), a1);
    } else {
      a0 = hn::MulAdd(w0, hn::LoadN(d, p, n0), a0);
    }
  }
  if (kFull) {
    hn::StoreU(hn::Add(a0, b0), d, out);
    if (n1) hn::StoreU(hn::Add(a1, b1), d, out + N);
  } else {
    hn::StoreN(hn::Add(a0, b0), d, out, n0);
  }
}

/* See the header comment. Reads x[0, 2*(nlag + L - 1)) floats, writes out[0, 2*nlag). */
static void td_corr(const float *x, const float *taps, int L, int nlag, float *out) {
  const hn::ScalableTag<float> d;
  const size_t N = hn::Lanes(d);
  const size_t nf = 2 * (size_t)nlag;
  size_t i = 0;
  /* Full vectors: a lane at offset i + 2k + j (j < N) is inside x because i + N <= nf. */
  for (; i + 2 * N <= nf; i += 2 * N) td_pass<true>(x + i, taps, L, N, N, out + i);
  if (i + N <= nf) { td_pass<true>(x + i, taps, L, N, 0, out + i); i += N; }
  if (i < nf) td_pass<false>(x + i, taps, L, nf - i, 0, out + i);
}

}  // namespace HWY_NAMESPACE
}  // namespace ap
HWY_AFTER_NAMESPACE();

#endif
