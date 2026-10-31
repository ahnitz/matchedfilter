/* The gate model's simulation kernels (_core.c's M_simulate), under Highway's dispatch.
 *
 * Power: A[e] = |g y[e] + d[e]|^2 of complex y and d, and the largest A, in one pass.
 *
 * Records: the running-maximum records of one
 * statistic's values (squares: non-negative) read outward from a start, every value that
 * exceeds all before it, as (distance, sqrt value). Records are rare -- about ln L of L values
 * of white noise, more where the profile makes neighbouring lags alike -- so the scan reads 16
 * values at a time, asks whether any exceeds the running maximum, and passes over the block
 * when none does (nearly every block). In a block that has one, a vector's records are its
 * lanes above both the running maximum and every lane before them (a maximum scanned across
 * the lanes), stored compressed, with no branch on each value. Comparisons, maxima and a
 * square root only, so the records are exactly those of a scan of one value at a time on
 * every ISA; a NaN, which that scan never records, sends its vector to that scan. */
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#undef HWY_TARGET_INCLUDE
#define HWY_TARGET_INCLUDE "records.cc"
#include "hwy/foreach_target.h"  // must come before highway.h
#include "hwy/highway.h"

HWY_BEFORE_NAMESPACE();
namespace ap_records {
namespace HWY_NAMESPACE {
namespace hn = hwy::HWY_NAMESPACE;

/* A[e] = |g y[e] + d[e]|^2 for e < m (d NULL: |g y[e]|^2), y and d complex (interleaved);
   returns the largest A. The maximum is taken over the values' bit patterns: for
   non-negative floats they order as the values do, so a NaN orders as it did in the scalar
   loop this replaced. */
float Power(const float *y, const float *d, float g, long long m, float *A) {
  const hn::CappedTag<float, 16> df;
  const hn::RebindToUnsigned<decltype(df)> du;
  using V = hn::Vec<decltype(df)>;
  const long long N = (long long)hn::Lanes(df);
  const V vg = hn::Set(df, g);
  auto mx = hn::Zero(du);
  long long e = 0;
  for (; m - e >= N; e += N) {
    V re, im;
    hn::LoadInterleaved2(df, y + 2 * e, re, im);
    re = hn::Mul(vg, re);
    im = hn::Mul(vg, im);
    if (d) {
      V dr, di;
      hn::LoadInterleaved2(df, d + 2 * e, dr, di);
      re = hn::Add(re, dr);
      im = hn::Add(im, di);
    }
    const V v = hn::MulAdd(re, re, hn::Mul(im, im));
    hn::StoreU(v, df, A + e);
    mx = hn::Max(mx, hn::BitCast(du, v));
  }
  uint32_t best = hn::ReduceMax(du, mx);
  for (; e < m; e++) {
    const float re = g * y[2 * e] + (d ? d[2 * e] : 0.f), im = g * y[2 * e + 1] + (d ? d[2 * e + 1] : 0.f);
    const float v = re * re + im * im;
    uint32_t u;
    memcpy(&u, &v, 4);
    A[e] = v;
    best = u > best ? u : best;
  }
  float r;
  memcpy(&r, &best, 4);
  return r;
}

/* Whether any of the nv vectors v has a lane above b. */
template <class D, class V>
static HWY_INLINE bool AnyAbove(D d, const V *v, size_t nv, V b) {
  auto m = hn::Gt(v[0], b);
  for (size_t i = 1; i < nv; i++) m = hn::Or(m, hn::Gt(v[i], b));
  return !hn::AllFalse(d, m);
}

/* The records among x's lanes read in lane order, the maximum so far in every lane of *bv
   (and updated): lane l is one when x[l] exceeds *bv and x[0 .. l-1], at distance dist + l.
   Appended at pos[kk], val[kk]; returns the new count, or -1 past cap. */
template <class D, class V>
static HWY_INLINE long long LaneRecords(D d, V x, V *bv, long long dist, int32_t *pos,
                                        float *val, long long kk, long long cap) {
  const size_t N = hn::Lanes(d);
  if (HWY_UNLIKELY(!hn::AllTrue(d, hn::Eq(x, x)))) {
    /* a NaN, which is never a record and leaves the maximum be: one lane at a time */
    HWY_ALIGN float xs[16];
    hn::Store(x, d, xs);
    float best = hn::GetLane(*bv);
    for (size_t l = 0; l < N; l++) {
      if (xs[l] > best) {
        best = xs[l];
        if (kk == cap) return -1;
        pos[kk] = (int32_t)(dist + (long long)l); val[kk] = sqrtf(best); kk++;
      }
    }
    *bv = hn::Set(d, best);
    return kk;
  }
  /* the maximum through each lane: of x's lanes so far and *bv (x >= 0, so the zeros the
     slides bring in change nothing), and before each lane */
  V inc = hn::Max(x, *bv);
  if (N > 1) inc = hn::Max(inc, hn::SlideUpLanes(d, inc, 1));
  if (N > 2) inc = hn::Max(inc, hn::SlideUpLanes(d, inc, 2));
  if (N > 4) inc = hn::Max(inc, hn::SlideUpLanes(d, inc, 4));
  if (N > 8) inc = hn::Max(inc, hn::SlideUpLanes(d, inc, 8));
  const V before = hn::IfThenElse(hn::FirstN(d, 1), *bv, hn::SlideUpLanes(d, inc, 1));
  const auto m = hn::Gt(x, before);
  const size_t cnt = hn::CountTrue(d, m);
  if (cnt) {
    if (kk + (long long)cnt > cap) return -1;
    /* Compressed into a vector's worth of local lanes, then the cnt records copied:
       CompressBlendedStore at pos + kk reads and rewrites a whole vector on some targets
       (NEON: a load, a blend and a store), past the arrays' end when the records reach
       it (ASan, arm64, 2026-10-30). Records are rare, so the copy costs nothing. */
    const hn::RebindToSigned<D> di;
    const auto at = hn::Add(hn::Iota(di, 0), hn::Set(di, (int32_t)dist));
    HWY_ALIGN int32_t ps[16];
    HWY_ALIGN float vs[16];
    hn::CompressStore(at, hn::RebindMask(di, m), di, ps);
    hn::CompressStore(hn::Sqrt(x), m, d, vs);
    for (size_t l = 0; l < cnt; l++) {
      pos[kk + (long long)l] = ps[l];
      val[kk + (long long)l] = vs[l];
    }
    kk += (long long)cnt;
  }
  *bv = hn::MaxOfLanes(d, inc);
  return kk;
}

/* The records of a[e0], a[e0 + DIR], ... (L values, non-negative) after those already at
   [0, *k), distances from d0. */
template <int DIR>
static int Scan(const float *a, long long e0, long long L, long long d0, int32_t *pos,
                float *val, long long *k, long long cap) {
  const hn::CappedTag<float, 16> d;
  using V = hn::Vec<decltype(d)>;
  const long long N = (long long)hn::Lanes(d), NV = 16 / N;   // 1, 2 or 4 vectors a block
  V v[4];
  V bv = hn::Set(d, -1.f);                         // below every value: the first is a record
  long long kk = *k, i = 0;
  for (; L - i >= 16; i += 16) {
    const float *q = DIR > 0 ? a + e0 + i : a + e0 - i - 15;
    for (long long j = 0; j < NV; j++) v[j] = hn::LoadU(d, q + j * N);
    if (HWY_LIKELY(!AnyAbove(d, v, (size_t)NV, bv))) continue;
    /* in reading order: forward vector j at distance i + j N, back reversed from the last */
    for (long long j = 0; j < NV; j++) {
      kk = DIR > 0 ? LaneRecords(d, v[j], &bv, i + j * N + d0, pos, val, kk, cap)
                   : LaneRecords(d, hn::Reverse(d, v[NV - 1 - j]), &bv, i + j * N + d0, pos,
                                 val, kk, cap);
      if (kk < 0) { *k = cap; return -1; }
    }
  }
  float best = hn::GetLane(bv);
  for (; i < L; i++) {
    const float x = a[e0 + DIR * i];
    if (x > best) {
      best = x;
      if (kk == cap) { *k = kk; return -1; }
      pos[kk] = (int32_t)(i + d0); val[kk] = sqrtf(best); kk++;
    }
  }
  *k = kk;
  return 0;
}

int Records(const float *a, long long e0, int dir, long long L, long long d0, int32_t *pos,
            float *val, long long *k, long long cap) {
  return dir > 0 ? Scan<1>(a, e0, L, d0, pos, val, k, cap)
                 : Scan<-1>(a, e0, L, d0, pos, val, k, cap);
}

}  // namespace HWY_NAMESPACE
}  // namespace ap_records
HWY_AFTER_NAMESPACE();

#if HWY_ONCE
namespace ap_records {
HWY_EXPORT(Records);
HWY_EXPORT(Power);
/* Dispatched unqualified from inside the namespace (see gauss.cc). */
static int Dispatch(const float *a, long long e0, int dir, long long L, long long d0,
                    int32_t *pos, float *val, long long *k, long long cap) {
  return HWY_DYNAMIC_DISPATCH(Records)(a, e0, dir, L, d0, pos, val, k, cap);
}
static float DispatchPower(const float *y, const float *d, float g, long long m, float *A) {
  return HWY_DYNAMIC_DISPATCH(Power)(y, d, g, m, A);
}
}  // namespace ap_records
/* The records of a[e0], a[e0 + dir], ... (L values, dir +1 or -1), each exceeding all before
   it (the first always), appended at pos[*k], val[*k] as (distance i + d0, sqrt value) for
   the i-th, *k advanced past them. Returns 0, or -1 when the arrays (cap entries) are full. */
/* A[e] = |g y[e] + d[e]|^2 for e < m (d NULL: |g y[e]|^2), y and d complex: simulate's
   statistics, for the best target this CPU runs. Returns the largest A. */
extern "C" float ap_sim_power(const float *y, const float *d, float g, long long m, float *A) {
  return ap_records::DispatchPower(y, d, g, m, A);
}
extern "C" int ap_sim_records(const float *a, long long e0, int dir, long long L, long long d0,
                              int32_t *pos, float *val, long long *k, long long cap) {
  return ap_records::Dispatch(a, e0, dir, L, d0, pos, val, k, cap);
}
#endif
