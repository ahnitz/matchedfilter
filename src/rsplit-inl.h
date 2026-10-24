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
#include <string.h>
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

/* The root stage of a hierarchical search (docs/hierarchical-search-design.md): the band-limited
 * product of two one-sided spectra of h + 1 bins (h = n/2),
 *
 *     P[k] = scale * conj(T[k]) D[k]  for k0 <= k < k1,  0 otherwise,
 *
 * merged into the h-point spectrum Z whose backward transform is the real n-point series
 * x = C2R(P) read as h complex samples, z[m] = x[2m] + i x[2m+1]:
 *
 *     Z[k] = (P[k] + conj P[h-k]) + i w^k (P[k] - conj P[h-k]),  w = e^{+2 pi i / n},  k < h,
 *
 * with P[0] and P[h] taken real, as a complex-to-real transform takes them. The pair (k, h-k)
 * is formed together, so each input bin is read once: with A = P[k], B = P[h-k] and
 * w^{h-k} = -conj w^k, both outputs come from S = A + conj B and E = A - conj B. tw holds cos
 * and sin of 2 pi k / n for k = 0 .. h (real_split's table). */
static void root_merge(const float *HWY_RESTRICT D, const float *HWY_RESTRICT T, size_t k0,
                       size_t k1, float scale, const float *HWY_RESTRICT tw, size_t n,
                       float *HWY_RESTRICT Z) {
  const size_t h = n / 2, q = h / 2;
  auto prod = [&](size_t k, float &pr, float &pi) {
    if (k >= k0 && k < k1) {
      const float dr = D[2 * k], di = D[2 * k + 1], tr = T[2 * k], ti = T[2 * k + 1];
      pr = scale * (tr * dr + ti * di);
      pi = scale * (tr * di - ti * dr);
    } else {
      pr = pi = 0.f;
    }
  };
  auto pair = [&](size_t k) {               /* scalar: Z[k] and, unless k == h-k, Z[h-k] */
    const size_t r = h - k;
    float ar, ai, br, bi;
    prod(k, ar, ai);
    prod(r, br, bi);
    const float sr = ar + br, si = ai - bi, er = ar - br, ei = ai + bi;
    const float c = tw[2 * k], s = tw[2 * k + 1];
    const float u = c * ei + s * er, v = c * er - s * ei;
    Z[2 * k] = sr - u;
    Z[2 * k + 1] = si + v;
    if (r != k) {
      Z[2 * r] = sr + u;
      Z[2 * r + 1] = v - si;
    }
  };
  {                                         /* k = 0: P[0] and P[h] real */
    float a0, unused, bh;
    prod(0, a0, unused);
    prod(h, bh, unused);
    Z[0] = a0 + bh;
    Z[1] = a0 - bh;
  }
  const hn::ScalableTag<float> d;
  const hn::RebindToSigned<decltype(d)> di;
  const size_t N = hn::Lanes(d);
  const auto sc = hn::Set(d, scale);
  const auto lo = hn::Set(di, (int32_t)k0), hi = hn::Set(di, (int32_t)k1);
  size_t k = 1;
  for (; k + N <= q; k += N) {
    const size_t r0 = h - k - N + 1;        /* P[r0 .. h-k], loaded then reversed */
    hn::Vec<decltype(d)> dr, dI, tr, tI, er, eI, ur, uI, c, s;
    hn::LoadInterleaved2(d, D + 2 * k, dr, dI);
    hn::LoadInterleaved2(d, T + 2 * k, tr, tI);
    hn::LoadInterleaved2(d, D + 2 * r0, er, eI);
    hn::LoadInterleaved2(d, T + 2 * r0, ur, uI);
    er = hn::Reverse(d, er); eI = hn::Reverse(d, eI);
    ur = hn::Reverse(d, ur); uI = hn::Reverse(d, uI);
    const auto fi = hn::Iota(di, (int32_t)k);
    const auto ri = hn::Sub(hn::Set(di, (int32_t)(h - k)), hn::Iota(di, 0));
    const auto mf = hn::RebindMask(d, hn::And(hn::Ge(fi, lo), hn::Lt(fi, hi)));
    const auto mr = hn::RebindMask(d, hn::And(hn::Ge(ri, lo), hn::Lt(ri, hi)));
    const auto ar = hn::IfThenElseZero(mf, hn::Mul(sc, hn::MulAdd(tr, dr, hn::Mul(tI, dI))));
    const auto ai = hn::IfThenElseZero(mf, hn::Mul(sc, hn::MulSub(tr, dI, hn::Mul(tI, dr))));
    const auto br = hn::IfThenElseZero(mr, hn::Mul(sc, hn::MulAdd(ur, er, hn::Mul(uI, eI))));
    const auto bi = hn::IfThenElseZero(mr, hn::Mul(sc, hn::MulSub(ur, eI, hn::Mul(uI, er))));
    hn::LoadInterleaved2(d, tw + 2 * k, c, s);
    const auto sr = hn::Add(ar, br), si = hn::Sub(ai, bi);
    const auto xr = hn::Sub(ar, br), xi = hn::Add(ai, bi);
    const auto u = hn::MulAdd(c, xi, hn::Mul(s, xr));
    const auto v = hn::MulSub(c, xr, hn::Mul(s, xi));
    hn::StoreInterleaved2(hn::Sub(sr, u), hn::Add(si, v), d, Z + 2 * k);
    hn::StoreInterleaved2(hn::Reverse(d, hn::Add(sr, u)), hn::Reverse(d, hn::Sub(v, si)), d,
                          Z + 2 * r0);
  }
  for (; k <= q; k++) pair(k);              /* the tail, and k = h/2 (its own mirror) */
}

}  // namespace HWY_NAMESPACE
}  // namespace ap
HWY_AFTER_NAMESPACE();

#endif
