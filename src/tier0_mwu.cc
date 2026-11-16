/* Kernels of the shared-screener merging that run several independent sums at once, each in a
 * vector lane and each as the plain loop would: a group's shared screener for many groups
 * (below), and a vector's sums against the coarse shifts (CoarseSums).
 *
 * A group's shared screener (_screeners.cluster_tier0_candidates), for many groups at once.
 *
 * One group: the unit-norm vector over a band of K bins that its m members, each phase-aligned
 * to it, overlap best in the worst case.
 *   u: the members, (m, K) complex128, lag-aligned. ref: the frame they are first phased to,
 *   (K,). w: the K real weights of the inner product <a, b> = sum_k w[k] conj(a[k]) b[k].
 * Two candidates are made and the one whose smallest member overlap is larger is kept (a tie
 * going to the minimax one):
 *   the mean of the members phased to ref, normalised;
 *   a minimax vector by `steps` rounds of multiplicative weights: the weighted sum of the
 *   members, normalised; each member rephased to it; each weight multiplied by
 *   exp(min(25 (deficit - smallest deficit), 10)), deficit = max(1 - overlap, 0), then the
 *   weights scaled to mean 1.
 * c_out: the kept vector (K complex128). ov_out: its overlap with each member as given (m).
 *
 * The groups of a call have one arity and one band, and nothing in a group's arithmetic depends
 * on another group: the batched routine puts a group in each vector lane and does, lane by
 * lane, exactly the operations of the plain routine in its order (sums run over the bins and
 * the members as they do there; hypot and exp are libm's, called per lane). A group's result is
 * therefore bit for bit the plain routine's, whatever the vector width and whichever groups
 * share its vector. That needs every product and sum to stay its own operation: this file is
 * built with floating-point contraction off (setup.py), and uses no fused multiply-add. */
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#undef HWY_TARGET_INCLUDE
#define HWY_TARGET_INCLUDE "tier0_mwu.cc"
#include "hwy/foreach_target.h"  // must come before highway.h
#include "hwy/highway.h"
#include "alloc.h"

HWY_BEFORE_NAMESPACE();
namespace ap_t0mwu {
namespace HWY_NAMESPACE {
namespace hn = hwy::HWY_NAMESPACE;

/* nb groups of m members over K bins: u (nb, m, K) complex128, ref (nb, K) complex128,
   w (K), c_out (nb, K) complex128, ov_out (nb, m). Returns 0, or -1 when out of memory. */
int MwuBatch(const double *u, const double *ref, const double *w, long long nb, long long m,
             long long K, int steps, double *c_out, double *ov_out) {
  const hn::ScalableTag<double> d;
  using V = hn::Vec<decltype(d)>;
  const long long N = (long long)hn::Lanes(d);
  // per element one vector, a lane a group: members as given and as iterated (m K each, real
  // and imaginary), the frame / minimax candidate and the mean candidate (K each), the
  // weights, the mean candidate's overlaps and the minimax one's (m each)
  const size_t vecs = (size_t)(4 * m * K + 4 * K + 3 * m);
  double *buf = ap_alloc64(vecs * (size_t)N * sizeof(double));
  if (!buf) return -1;
  double *ur = buf, *ui = ur + m * K * N, *tr = ui + m * K * N, *ti = tr + m * K * N;
  double *cr = ti + m * K * N, *ci = cr + K * N, *mr = ci + K * N, *mi = mr + K * N;
  double *wt = mi + K * N, *om = wt + m * N, *ov = om + m * N;
  HWY_ALIGN double a[HWY_MAX_LANES_D(hn::ScalableTag<double>)];
  HWY_ALIGN double b[HWY_MAX_LANES_D(hn::ScalableTag<double>)];
  const V one = hn::Set(d, 1.0), zero = hn::Zero(d), tiny = hn::Set(d, 1e-12);
  const V floor_ = hn::Set(d, 1e-30), inf = hn::Set(d, HUGE_VAL), count = hn::Set(d, (double)m);

  // hypot(x, y) of every lane, by libm
  auto hyp = [&](V x, V y) {
    hn::Store(x, d, a);
    hn::Store(y, d, b);
    for (long long l = 0; l < N; l++) a[l] = hypot(a[l], b[l]);
    return hn::Load(d, a);
  };
  // sum_k w[k] conj(c[k]) x[k] of every lane: the plain routine's sums, term by term
  auto dot = [&](const double *xr, const double *xi, const double *yr, const double *yi, V *gr,
                 V *gi) {
    V sr = zero, si = zero;
    for (long long k = 0; k < K; k++) {
      const V wk = hn::Set(d, w[k]);
      const V ar = hn::Mul(wk, hn::Load(d, xr + k * N));
      const V ai = hn::Mul(hn::Neg(wk), hn::Load(d, xi + k * N));
      const V vr = hn::Load(d, yr + k * N), vi = hn::Load(d, yi + k * N);
      sr = hn::Add(sr, hn::Sub(hn::Mul(ar, vr), hn::Mul(ai, vi)));
      si = hn::Add(si, hn::Add(hn::Mul(ar, vi), hn::Mul(ai, vr)));
    }
    *gr = sr;
    *gi = si;
  };
  // the candidate (cr, ci) scaled to unit norm under w
  auto normalise = [&](double *xr, double *xi, V nrm) {
    nrm = hn::Sqrt(hn::IfThenElse(hn::Gt(nrm, floor_), nrm, floor_));
    for (long long k = 0; k < K; k++) {
      hn::Store(hn::Div(hn::Load(d, xr + k * N), nrm), d, xr + k * N);
      hn::Store(hn::Div(hn::Load(d, xi + k * N), nrm), d, xi + k * N);
    }
  };

  for (long long g0 = 0; g0 < nb; g0 += N) {
    // a group a lane; a short last batch repeats its last group (computed, not written)
    for (long long l = 0; l < N; l++) {
      const long long g = g0 + l < nb ? g0 + l : nb - 1;
      const double *ug = u + 2 * g * m * K, *rg = ref + 2 * g * K;
      for (long long e = 0; e < m * K; e++) {
        ur[e * N + l] = ug[2 * e];
        ui[e * N + l] = ug[2 * e + 1];
      }
      for (long long k = 0; k < K; k++) {
        cr[k * N + l] = rg[2 * k];
        ci[k * N + l] = rg[2 * k + 1];
      }
    }
    // phase every member to the reference frame
    for (long long j = 0; j < m; j++) {
      V gr, gi;
      dot(cr, ci, ur + j * K * N, ui + j * K * N, &gr, &gi);
      const V ag = hyp(gr, gi);
      const auto ok = hn::Gt(ag, tiny);
      const V pr = hn::IfThenElse(ok, hn::Div(gr, ag), one);
      const V pi = hn::IfThenElse(ok, hn::Div(hn::Neg(gi), ag), zero);
      for (long long k = 0; k < K; k++) {
        const V xr = hn::Load(d, ur + (j * K + k) * N), xi = hn::Load(d, ui + (j * K + k) * N);
        hn::Store(hn::Sub(hn::Mul(xr, pr), hn::Mul(xi, pi)), d, tr + (j * K + k) * N);
        hn::Store(hn::Add(hn::Mul(xr, pi), hn::Mul(xi, pr)), d, ti + (j * K + k) * N);
      }
    }
    // the mean candidate and its overlaps with the members as given
    V nrm = zero;
    for (long long k = 0; k < K; k++) {
      V sr = zero, si = zero;
      for (long long j = 0; j < m; j++) {
        sr = hn::Add(sr, hn::Load(d, tr + (j * K + k) * N));
        si = hn::Add(si, hn::Load(d, ti + (j * K + k) * N));
      }
      sr = hn::Div(sr, count);
      si = hn::Div(si, count);
      hn::Store(sr, d, mr + k * N);
      hn::Store(si, d, mi + k * N);
      nrm = hn::Add(nrm, hn::Mul(hn::Add(hn::Mul(sr, sr), hn::Mul(si, si)), hn::Set(d, w[k])));
    }
    normalise(mr, mi, nrm);
    V min_mean = inf;
    for (long long j = 0; j < m; j++) {
      V gr, gi;
      dot(mr, mi, ur + j * K * N, ui + j * K * N, &gr, &gi);
      const V o = hyp(gr, gi);
      hn::Store(o, d, om + j * N);
      min_mean = hn::IfThenElse(hn::Lt(o, min_mean), o, min_mean);
    }
    // the minimax candidate: steps rounds of multiplicative weights, then the final sum
    for (long long j = 0; j < m; j++) hn::Store(one, d, wt + j * N);
    for (int it = 0; it <= steps; it++) {
      nrm = zero;
      for (long long k = 0; k < K; k++) {
        V sr = zero, si = zero;
        for (long long j = 0; j < m; j++) {
          const V wj = hn::Load(d, wt + j * N);
          sr = hn::Add(sr, hn::Mul(wj, hn::Load(d, tr + (j * K + k) * N)));
          si = hn::Add(si, hn::Mul(wj, hn::Load(d, ti + (j * K + k) * N)));
        }
        hn::Store(sr, d, cr + k * N);
        hn::Store(si, d, ci + k * N);
        nrm = hn::Add(nrm, hn::Mul(hn::Add(hn::Mul(sr, sr), hn::Mul(si, si)), hn::Set(d, w[k])));
      }
      normalise(cr, ci, nrm);
      if (it == steps) break;
      V dmin = inf;
      for (long long j = 0; j < m; j++) {
        double *yr = tr + j * K * N, *yi = ti + j * K * N;
        V gr, gi;
        dot(cr, ci, yr, yi, &gr, &gi);
        const V ag = hyp(gr, gi);
        const auto ok = hn::Gt(ag, tiny);
        const V pr = hn::IfThenElse(ok, hn::Div(gr, ag), one);
        const V pi = hn::IfThenElse(ok, hn::Div(hn::Neg(gi), ag), zero);
        for (long long k = 0; k < K; k++) {
          const V xr = hn::Load(d, yr + k * N), xi = hn::Load(d, yi + k * N);
          hn::Store(hn::Sub(hn::Mul(xr, pr), hn::Mul(xi, pi)), d, yr + k * N);
          hn::Store(hn::Add(hn::Mul(xr, pi), hn::Mul(xi, pr)), d, yi + k * N);
        }
        const V gap = hn::Sub(one, ag);
        const V def = hn::IfThenElse(hn::Gt(gap, zero), gap, zero);
        hn::Store(def, d, ov + j * N);                 // the deficit, for the weights below
        dmin = hn::IfThenElse(hn::Lt(def, dmin), def, dmin);
      }
      V mean = zero;
      const V rate = hn::Set(d, 25.0), cap = hn::Set(d, 10.0);
      for (long long j = 0; j < m; j++) {
        const V e = hn::Mul(rate, hn::Sub(hn::Load(d, ov + j * N), dmin));
        hn::Store(hn::IfThenElse(hn::Lt(e, cap), e, cap), d, a);
        for (long long l = 0; l < N; l++) a[l] = exp(a[l]);
        const V wj = hn::Mul(hn::Load(d, wt + j * N), hn::Load(d, a));
        hn::Store(wj, d, wt + j * N);
        mean = hn::Add(mean, wj);
      }
      mean = hn::Div(mean, count);
      for (long long j = 0; j < m; j++)
        hn::Store(hn::Div(hn::Load(d, wt + j * N), mean), d, wt + j * N);
    }
    V min_mwu = inf;
    for (long long j = 0; j < m; j++) {
      V gr, gi;
      dot(cr, ci, ur + j * K * N, ui + j * K * N, &gr, &gi);
      const V o = hyp(gr, gi);
      hn::Store(o, d, ov + j * N);
      min_mwu = hn::IfThenElse(hn::Lt(o, min_mwu), o, min_mwu);
    }
    // each group keeps the candidate whose worst member overlaps better
    hn::Store(hn::IfThenElse(hn::Ge(min_mwu, min_mean), one, zero), d, a);
    for (long long l = 0; l < N && g0 + l < nb; l++) {
      const long long g = g0 + l;
      const double *xr = a[l] != 0.0 ? cr : mr, *xi = a[l] != 0.0 ? ci : mi;
      const double *xo = a[l] != 0.0 ? ov : om;
      for (long long k = 0; k < K; k++) {
        c_out[2 * (g * K + k)] = xr[k * N + l];
        c_out[2 * (g * K + k) + 1] = xi[k * N + l];
      }
      for (long long j = 0; j < m; j++) ov_out[g * m + j] = xo[j * N + l];
    }
  }
  free(buf);
  return 0;
}

/* A vector's sums against every coarse shift (src/tier0_pass.cc), a shift a lane:
   re[s] + i im[s] = sum_k x[k] shift_s[k] in float32, bin after bin, each lane the plain
   loop's operations. x (K) as xr, xi; the shifts transposed, (K, nshp) each of sr and si,
   nshp a multiple of 16 (the lanes past the shifts there are hold zeros). */
void CoarseSums(const float *xr, const float *xi, const float *sr, const float *si,
                long long K, long long nshp, float *re, float *im) {
  const hn::ScalableTag<float> d;
  using V = hn::Vec<decltype(d)>;
  const long long N = (long long)hn::Lanes(d);
  for (long long s0 = 0; s0 < nshp; s0 += N) {
    V ar = hn::Zero(d), ai = hn::Zero(d);
    for (long long k = 0; k < K; k++) {
      const V a = hn::Set(d, xr[k]), b = hn::Set(d, xi[k]);
      const V cr = hn::LoadU(d, sr + k * nshp + s0), ci = hn::LoadU(d, si + k * nshp + s0);
      ar = hn::Add(ar, hn::Sub(hn::Mul(a, cr), hn::Mul(b, ci)));
      ai = hn::Add(ai, hn::Add(hn::Mul(a, ci), hn::Mul(b, cr)));
    }
    hn::StoreU(ar, d, re + s0);
    hn::StoreU(ai, d, im + s0);
  }
}

}  // namespace HWY_NAMESPACE
}  // namespace ap_t0mwu
HWY_AFTER_NAMESPACE();

#if HWY_ONCE
namespace ap_t0mwu {
HWY_EXPORT(MwuBatch);
HWY_EXPORT(CoarseSums);

/* The plain routine, one group: what the batched one reproduces lane by lane, and its test's
   reference. work: 2 m K + 4 K + 2 m doubles. */
static void MwuOne(const double *u, const double *ref, const double *w, long long m, long long K,
                   int steps, double *c_out, double *ov_out, double *work) {
  double *ut = work;                    /* members as iterated, (m, K) complex */
  double *cm = ut + 2 * m * K;          /* the mean candidate, K complex */
  double *cw = cm + 2 * K;              /* the minimax candidate, K complex */
  double *wt = cw + 2 * K;              /* weights, m */
  double *om = wt + m;                  /* the mean candidate's overlaps, m */
  /* phase every member to the reference frame */
  for (long long j = 0; j < m; j++) {
    const double *uj = u + 2 * j * K;
    double gr = 0.0, gi = 0.0;
    for (long long k = 0; k < K; k++) {
      const double ar = w[k] * ref[2 * k], ai = -w[k] * ref[2 * k + 1];
      gr += ar * uj[2 * k] - ai * uj[2 * k + 1];
      gi += ar * uj[2 * k + 1] + ai * uj[2 * k];
    }
    const double ag = hypot(gr, gi);
    double pr = 1.0, pi = 0.0;
    if (ag > 1e-12) { pr = gr / ag; pi = -gi / ag; }
    double *tj = ut + 2 * j * K;
    for (long long k = 0; k < K; k++) {
      tj[2 * k] = uj[2 * k] * pr - uj[2 * k + 1] * pi;
      tj[2 * k + 1] = uj[2 * k] * pi + uj[2 * k + 1] * pr;
    }
  }
  /* the mean candidate and its overlaps with the members as given */
  double nrm = 0.0;
  for (long long k = 0; k < K; k++) {
    double sr = 0.0, si = 0.0;
    for (long long j = 0; j < m; j++) { sr += ut[2 * (j * K + k)]; si += ut[2 * (j * K + k) + 1]; }
    sr /= (double)m; si /= (double)m;
    cm[2 * k] = sr; cm[2 * k + 1] = si;
    nrm += (sr * sr + si * si) * w[k];
  }
  nrm = sqrt(nrm > 1e-30 ? nrm : 1e-30);
  for (long long k = 0; k < 2 * K; k++) cm[k] /= nrm;
  double min_mean = HUGE_VAL;
  for (long long j = 0; j < m; j++) {
    const double *uj = u + 2 * j * K;
    double gr = 0.0, gi = 0.0;
    for (long long k = 0; k < K; k++) {
      const double ar = w[k] * cm[2 * k], ai = -w[k] * cm[2 * k + 1];
      gr += ar * uj[2 * k] - ai * uj[2 * k + 1];
      gi += ar * uj[2 * k + 1] + ai * uj[2 * k];
    }
    om[j] = hypot(gr, gi);
    if (om[j] < min_mean) min_mean = om[j];
  }
  /* the minimax candidate: steps rounds of multiplicative weights, then the final sum */
  for (long long j = 0; j < m; j++) wt[j] = 1.0;
  for (int it = 0; it <= steps; it++) {
    nrm = 0.0;
    for (long long k = 0; k < K; k++) {
      double sr = 0.0, si = 0.0;
      for (long long j = 0; j < m; j++) {
        sr += wt[j] * ut[2 * (j * K + k)];
        si += wt[j] * ut[2 * (j * K + k) + 1];
      }
      cw[2 * k] = sr; cw[2 * k + 1] = si;
      nrm += (sr * sr + si * si) * w[k];
    }
    nrm = sqrt(nrm > 1e-30 ? nrm : 1e-30);
    for (long long k = 0; k < 2 * K; k++) cw[k] /= nrm;
    if (it == steps) break;
    double dmin = HUGE_VAL;
    for (long long j = 0; j < m; j++) {
      double *tj = ut + 2 * j * K;
      double gr = 0.0, gi = 0.0;
      for (long long k = 0; k < K; k++) {
        const double ar = w[k] * cw[2 * k], ai = -w[k] * cw[2 * k + 1];
        gr += ar * tj[2 * k] - ai * tj[2 * k + 1];
        gi += ar * tj[2 * k + 1] + ai * tj[2 * k];
      }
      const double ag = hypot(gr, gi);
      double pr = 1.0, pi = 0.0;
      if (ag > 1e-12) { pr = gr / ag; pi = -gi / ag; }
      for (long long k = 0; k < K; k++) {
        const double xr = tj[2 * k], xi = tj[2 * k + 1];
        tj[2 * k] = xr * pr - xi * pi;
        tj[2 * k + 1] = xr * pi + xi * pr;
      }
      const double dj = 1.0 - ag > 0.0 ? 1.0 - ag : 0.0;
      ov_out[j] = dj;                                /* the deficit, for the weights below */
      if (dj < dmin) dmin = dj;
    }
    double mean = 0.0;
    for (long long j = 0; j < m; j++) {
      const double e = 25.0 * (ov_out[j] - dmin);
      wt[j] *= exp(e < 10.0 ? e : 10.0);
      mean += wt[j];
    }
    mean /= (double)m;
    for (long long j = 0; j < m; j++) wt[j] /= mean;
  }
  double min_mwu = HUGE_VAL;
  for (long long j = 0; j < m; j++) {
    const double *uj = u + 2 * j * K;
    double gr = 0.0, gi = 0.0;
    for (long long k = 0; k < K; k++) {
      const double ar = w[k] * cw[2 * k], ai = -w[k] * cw[2 * k + 1];
      gr += ar * uj[2 * k] - ai * uj[2 * k + 1];
      gi += ar * uj[2 * k + 1] + ai * uj[2 * k];
    }
    ov_out[j] = hypot(gr, gi);
    if (ov_out[j] < min_mwu) min_mwu = ov_out[j];
  }
  if (min_mwu >= min_mean) {
    memcpy(c_out, cw, 2 * (size_t)K * sizeof(double));
  } else {
    memcpy(c_out, cm, 2 * (size_t)K * sizeof(double));
    memcpy(ov_out, om, (size_t)m * sizeof(double));
  }
}
}  // namespace ap_t0mwu

/* Every group's shared screener, for the best target this CPU runs. Returns 0, or -1 when out
   of memory. */
extern "C" int ap_tier0_mwu(const double *u, const double *ref, const double *w, long long nb,
                            long long m, long long K, int steps, double *c_out,
                            double *ov_out) {
  return HWY_DYNAMIC_DISPATCH(ap_t0mwu::MwuBatch)(u, ref, w, nb, m, K, steps, c_out, ov_out);
}
/* A vector's float32 sums against every coarse shift (CoarseSums above). */
extern "C" void ap_tier0_coarse_sums(const float *xr, const float *xi, const float *sr,
                                     const float *si, long long K, long long nshp, float *re,
                                     float *im) {
  HWY_DYNAMIC_DISPATCH(ap_t0mwu::CoarseSums)(xr, xi, sr, si, K, nshp, re, im);
}
/* The same by the plain routine, group by group. */
extern "C" int ap_tier0_mwu_plain(const double *u, const double *ref, const double *w,
                                  long long nb, long long m, long long K, int steps,
                                  double *c_out, double *ov_out) {
  double *work = (double *)malloc((size_t)(2 * m * K + 4 * K + 2 * m) * sizeof(double));
  if (!work) return -1;
  for (long long g = 0; g < nb; g++)
    ap_t0mwu::MwuOne(u + 2 * g * m * K, ref + 2 * g * K, w, m, K, steps, c_out + 2 * g * K,
                         ov_out + g * m, work);
  free(work);
  return 0;
}
#endif
