/* The full n-point spectrum of a real block from the n/2-point transform of its samples read
 * as n/2 complex ones (z[j] = x[2j] + i x[2j+1], Z = FFT_{n/2}(z), h = n/2):
 *
 *     X[k] = E[k] + W^k O[k],  E = (Z[k] + conj Z[h-k]) / 2,  O = (Z[k] - conj Z[h-k]) / 2i,
 *     W = e^{-2 pi i / n},  k = 0 .. h,  and X[n-k] = conj X[k].
 *
 * tw holds cos and sin of 2 pi k / n, interleaved, for k = 0 .. h. Z and X are interleaved
 * complex. Vectorised through the V_* layer so every Highway target and the 8-lane AVX1 build
 * compile the same kernels.
 */
#include <string.h>
#include "simd-inl.h"
#include "loads-inl.h"   /* scale_load, split_store */

#if defined(AP_RSPLIT_INL_H_) == defined(HWY_TARGET_TOGGLE)
#ifdef AP_RSPLIT_INL_H_
#undef AP_RSPLIT_INL_H_
#else
#define AP_RSPLIT_INL_H_
#endif

HWY_BEFORE_NAMESPACE();
namespace ap {
namespace HWY_NAMESPACE {

template <bool MIRROR>
static HWY_INLINE void real_split_t(const float *HWY_RESTRICT Z, const float *HWY_RESTRICT tw,
                                    size_t n, float *HWY_RESTRICT X) {
  const size_t h = n / 2, W = (size_t)AP_W;
  X[0] = Z[0] + Z[1];
  X[1] = 0.f;
  X[2 * h] = Z[0] - Z[1];
  X[2 * h + 1] = 0.f;
  const vf half = V_SET1(0.5f), sg = V_SIGNMASK();
  size_t k = 1;
  for (; k + W <= h; k += W) {
    vf zr, zi, rr, ri, c, s;
    v_deint(Z + 2 * k, &zr, &zi);
    v_deint(Z + 2 * (h - k - W + 1), &rr, &ri);   /* Z[h-k-W+1 .. h-k] */
    rr = v_reverse(rr);
    ri = v_reverse(ri);                           /* now Z[h-k-j], j = 0..W-1 */
    v_deint(tw + 2 * k, &c, &s);
    /* conj Z[h-k] = (rr, -ri) */
    const vf er = V_MUL(half, V_ADD(zr, rr));
    const vf ei = V_MUL(half, V_SUB(zi, ri));
    const vf orr = V_MUL(half, V_ADD(zi, ri));    /* (zi - (-ri)) / 2 */
    const vf oi = V_MUL(half, V_SUB(rr, zr));     /* -(zr - rr) / 2 */
    const vf xr = V_ADD(er, V_FMADD(orr, c, V_MUL(oi, s)));
    const vf xi = V_ADD(ei, V_FMSUB(oi, c, V_MUL(orr, s)));
    v_inter(X + 2 * k, xr, xi);
    if constexpr (MIRROR) {
      v_inter(X + 2 * (n - k - W + 1), v_reverse(xr), V_XOR(v_reverse(xi), sg));
    }
  }
  for (; k < h; k++) {
    const size_t r = h - k;
    const float zr = Z[2 * k], zi = Z[2 * k + 1], cr = Z[2 * r], ci = -Z[2 * r + 1];
    const float er = 0.5f * (zr + cr), ei = 0.5f * (zi + ci);
    const float orr = 0.5f * (zi - ci), oi = -0.5f * (zr - cr);
    const float c = tw[2 * k], s = tw[2 * k + 1];
    const float xr = er + (orr * c + oi * s), xi = ei + (oi * c - orr * s);
    X[2 * k] = xr;
    X[2 * k + 1] = xi;
    if constexpr (MIRROR) {
      X[2 * (n - k)] = xr;
      X[2 * (n - k) + 1] = -xi;
    }
  }
}

static void real_split(const float *HWY_RESTRICT Z, const float *HWY_RESTRICT tw, size_t n,
                       float *HWY_RESTRICT X) {
  real_split_t<true>(Z, tw, n, X);
}

/* Non-negative bins 0 .. n/2 only: coarse tiers never read k > n/2, and the negative bins are
   mirrored lazily on the few blocks whose survivors refine by transform. */
static void real_split_pos(const float *HWY_RESTRICT Z, const float *HWY_RESTRICT tw, size_t n,
                           float *HWY_RESTRICT X) {
  real_split_t<false>(Z, tw, n, X);
}

/* Fill X[n/2 + 1 .. n - 1] = conj(X[n/2 - 1 .. 1]) from a half-spectrum X[0 .. n/2]. */
static void real_split_mirror(float *HWY_RESTRICT X, size_t n) {
  const size_t h = n / 2, W = (size_t)AP_W;
  const vf sg = V_SIGNMASK();
  size_t k = 1;
  for (; k + W <= h; k += W) {
    vf xr, xi;
    v_deint(X + 2 * k, &xr, &xi);
    v_inter(X + 2 * (n - k - W + 1), v_reverse(xr), V_XOR(v_reverse(xi), sg));
  }
  for (; k < h; k++) {
    X[2 * (n - k)] = X[2 * k];
    X[2 * (n - k) + 1] = -X[2 * k + 1];
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
 * with P[0] and P[h] taken real, as a complex-to-real transform takes them. Partitioning
 * [1, h/2) at the active band's endpoints and their mirrors zeroes empty intervals outright and
 * leaves the active ones branchless and mask-free. */
static void root_merge(const float *HWY_RESTRICT D, const float *HWY_RESTRICT T, size_t k0,
                       size_t k1, float scale, const float *HWY_RESTRICT tw, size_t n,
                       float *HWY_RESTRICT Z) {
  const size_t h = n / 2, q = h / 2, W = (size_t)AP_W;
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
  if (q == 0) return;

  /* Partition [1, q) at the active band [k0, k1) and its mirror [h + 1 - k1, h + 1 - k0). */
  auto clamp_q = [&](size_t x) -> size_t { return x < 1 ? 1 : (x > q ? q : x); };
  size_t a_lo = 1, a_hi = 1, r_lo = 1, r_hi = 1;
  if (k0 < k1) {
    a_lo = clamp_q(k0);
    a_hi = clamp_q(k1);
    r_lo = clamp_q(k1 <= h + 1 ? h + 1 - k1 : 0);
    r_hi = clamp_q(k0 <= h ? h + 1 - k0 : 0);
  }
  size_t pts[6] = {1, a_lo, a_hi, r_lo, r_hi, q};
  for (int i = 1; i < 6; i++) {
    size_t v = pts[i];
    int j = i - 1;
    while (j >= 0 && pts[j] > v) { pts[j + 1] = pts[j]; j--; }
    pts[j + 1] = v;
  }

  const vf sc = V_SET1(scale), sg = V_SIGNMASK();
  for (int seg = 0; seg < 5; seg++) {
    const size_t lo_s = pts[seg], hi_s = pts[seg + 1];
    if (lo_s >= hi_s) continue;
    const int hasA = (k0 < k1) && (lo_s >= k0 && lo_s < k1);
    const int hasB = (k0 < k1) && (h - lo_s >= k0 && h - lo_s < k1);
    if (!hasA && !hasB) {
      const size_t cnt = hi_s - lo_s;
      memset(Z + 2 * lo_s, 0, 2 * cnt * sizeof(float));
      memset(Z + 2 * (h - hi_s + 1), 0, 2 * cnt * sizeof(float));
      continue;
    }
    size_t k = lo_s;
    if (hasA && !hasB) {
      for (; k + W <= hi_s; k += W) {
        const size_t r0 = h - k - W + 1;
        vf dr, dI, tr, tI, c, s;
        v_deint(D + 2 * k, &dr, &dI);
        v_deint(T + 2 * k, &tr, &tI);
        v_deint(tw + 2 * k, &c, &s);
        const vf ar = V_MUL(sc, V_FMADD(tr, dr, V_MUL(tI, dI)));
        const vf ai = V_MUL(sc, V_FMSUB(tr, dI, V_MUL(tI, dr)));
        const vf u = V_FMADD(c, ai, V_MUL(s, ar));
        const vf v = V_FMSUB(c, ar, V_MUL(s, ai));
        v_inter(Z + 2 * k, V_SUB(ar, u), V_ADD(ai, v));
        v_inter(Z + 2 * r0, v_reverse(V_ADD(ar, u)), v_reverse(V_SUB(v, ai)));
      }
    } else if (!hasA && hasB) {
      for (; k + W <= hi_s; k += W) {
        const size_t r0 = h - k - W + 1;
        vf er, eI, ur, uI, c, s;
        v_deint(D + 2 * r0, &er, &eI);
        v_deint(T + 2 * r0, &ur, &uI);
        er = v_reverse(er); eI = v_reverse(eI);
        ur = v_reverse(ur); uI = v_reverse(uI);
        v_deint(tw + 2 * k, &c, &s);
        const vf br = V_MUL(sc, V_FMADD(ur, er, V_MUL(uI, eI)));
        const vf bi = V_MUL(sc, V_FMSUB(ur, eI, V_MUL(uI, er)));
        const vf nbr = V_XOR(br, sg), nbi = V_XOR(bi, sg);
        const vf u = V_FMADD(c, bi, V_MUL(s, nbr));
        const vf v = V_FMSUB(c, nbr, V_MUL(s, bi));
        v_inter(Z + 2 * k, V_SUB(br, u), V_ADD(nbi, v));
        v_inter(Z + 2 * r0, v_reverse(V_ADD(br, u)), v_reverse(V_ADD(v, bi)));
      }
    } else {
      for (; k + W <= hi_s; k += W) {
        const size_t r0 = h - k - W + 1;
        vf dr, dI, tr, tI, er, eI, ur, uI, c, s;
        v_deint(D + 2 * k, &dr, &dI);
        v_deint(T + 2 * k, &tr, &tI);
        v_deint(D + 2 * r0, &er, &eI);
        v_deint(T + 2 * r0, &ur, &uI);
        er = v_reverse(er); eI = v_reverse(eI);
        ur = v_reverse(ur); uI = v_reverse(uI);
        v_deint(tw + 2 * k, &c, &s);
        const vf ar = V_MUL(sc, V_FMADD(tr, dr, V_MUL(tI, dI)));
        const vf ai = V_MUL(sc, V_FMSUB(tr, dI, V_MUL(tI, dr)));
        const vf br = V_MUL(sc, V_FMADD(ur, er, V_MUL(uI, eI)));
        const vf bi = V_MUL(sc, V_FMSUB(ur, eI, V_MUL(uI, er)));
        const vf sr = V_ADD(ar, br), si = V_SUB(ai, bi);
        const vf xr = V_SUB(ar, br), xi = V_ADD(ai, bi);
        const vf u = V_FMADD(c, xi, V_MUL(s, xr));
        const vf v = V_FMSUB(c, xr, V_MUL(s, xi));
        v_inter(Z + 2 * k, V_SUB(sr, u), V_ADD(si, v));
        v_inter(Z + 2 * r0, v_reverse(V_ADD(sr, u)), v_reverse(V_SUB(v, si)));
      }
    }
    for (; k < hi_s; k++) pair(k);
  }
  pair(q);                                  /* k = h/2 (its own mirror) */
}

}  // namespace HWY_NAMESPACE
}  // namespace ap
HWY_AFTER_NAMESPACE();

#endif
