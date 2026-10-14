/* The full n-point spectrum of a real block from the n/2-point transform of its samples read
 * as n/2 complex ones (z[j] = x[2j] + i x[2j+1], Z = FFT_{n/2}(z), h = n/2):
 *
 *     X[k] = E[k] + W^k O[k],  E = (Z[k] + conj Z[h-k]) / 2,  O = (Z[k] - conj Z[h-k]) / 2i,
 *     W = e^{-2 pi i / n},  k = 0 .. h,  and X[n-k] = conj X[k].
 *
 * tw holds cos and sin of 2 pi k / n, interleaved, for k = 0 .. h. Z and X are interleaved
 * complex. Vectorised over k: a vector of Z[k..k+N) against the same run of Z[h-k] loaded
 * backwards and reversed; X[k..k+N) is stored forward and its conjugate mirror reversed.
 */
#include "simd-inl.h"

#if defined(AP_RSPLIT_INL_H_) == defined(HWY_TARGET_TOGGLE)
#ifdef AP_RSPLIT_INL_H_
#undef AP_RSPLIT_INL_H_
#else
#define AP_RSPLIT_INL_H_
#endif

HWY_BEFORE_NAMESPACE();
namespace ap {
namespace HWY_NAMESPACE {

static void real_split(const float *HWY_RESTRICT Z, const float *HWY_RESTRICT tw, size_t n,
                       float *HWY_RESTRICT X) {
  const size_t h = n / 2;
  X[0] = Z[0] + Z[1];
  X[1] = 0.f;
  X[2 * h] = Z[0] - Z[1];
  X[2 * h + 1] = 0.f;
  const hn::ScalableTag<float> d;
  const size_t N = hn::Lanes(d);
  const auto half = hn::Set(d, 0.5f);
  size_t k = 1;
  for (; k + N <= h; k += N) {
    hn::Vec<decltype(d)> zr, zi, rr, ri, c, s;
    hn::LoadInterleaved2(d, Z + 2 * k, zr, zi);
    hn::LoadInterleaved2(d, Z + 2 * (h - k - N + 1), rr, ri);   /* Z[h-k-N+1 .. h-k] */
    rr = hn::Reverse(d, rr);
    ri = hn::Reverse(d, ri);                                      /* now Z[h-k-j], j = 0..N-1 */
    hn::LoadInterleaved2(d, tw + 2 * k, c, s);
    /* conj Z[h-k] = (rr, -ri) */
    const auto er = hn::Mul(half, hn::Add(zr, rr));
    const auto ei = hn::Mul(half, hn::Sub(zi, ri));
    const auto orr = hn::Mul(half, hn::Add(zi, ri));              /* (zi - (-ri)) / 2 */
    const auto oi = hn::Mul(half, hn::Sub(rr, zr));               /* -(zr - rr) / 2 */
    const auto xr = hn::Add(er, hn::MulAdd(orr, c, hn::Mul(oi, s)));
    const auto xi = hn::Add(ei, hn::MulSub(oi, c, hn::Mul(orr, s)));
    hn::StoreInterleaved2(xr, xi, d, X + 2 * k);
    hn::StoreInterleaved2(hn::Reverse(d, xr), hn::Neg(hn::Reverse(d, xi)), d,
                          X + 2 * (n - k - N + 1));
  }
  for (; k < h; k++) {
    const size_t r = h - k;
    const float zr = Z[2 * k], zi = Z[2 * k + 1], cr = Z[2 * r], ci = -Z[2 * r + 1];
    const float er = 0.5f * (zr + cr), ei = 0.5f * (zi + ci);
    const float orr = 0.5f * (zi - ci), oi = -0.5f * (zr - cr);
    const float c = tw[2 * k], s = tw[2 * k + 1];
    const float xr = er + (orr * c + oi * s), xi = ei + (oi * c - orr * s);
    X[2 * k] = xr; X[2 * k + 1] = xi;
    X[2 * (n - k)] = xr; X[2 * (n - k) + 1] = -xi;
  }
}

}  // namespace HWY_NAMESPACE
}  // namespace ap
HWY_AFTER_NAMESPACE();

#endif
