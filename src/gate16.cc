/* The hierarchical filter's first gate tier in half precision, for ARM NEON with
 * FP16 vector arithmetic (every Apple silicon core).
 *
 * Why: the first tier correlates EVERY (block, template) pair at its coarse band, and on
 * the CPU it is the largest share of the fine stage (36% of samples on an M2). NEON does
 * an FP16 FMA on 8 lanes in the time FP32 does 4 (measured on an M2 performance core:
 * 143 against 72 GFLOP/s), and a gate only has to decide "maybe" -- the exact refine is
 * untouched and still runs in FP32 on every survivor.
 *
 * How: the SAME element transform the FP32 pair-batched path runs (elemfft-inl.h, the
 * generated codelets and the fused product loader), compiled a second time with the
 * lane type FP16, so 8 templates share a vector instead of 4. Inputs are stored in FP16
 * once at ingest, each spectrum scaled by a power of two so its largest component is
 * below 1: products are then bounded by 1 and an m-point transform by m <= 2048, inside
 * FP16's range, and the scale is exact to undo.
 *
 * Error and the dismissal budget: the gate must never dismiss a pair the FP32 gate would
 * pass. Rounding error of the transform at any lag is bounded, to the stated confidence,
 * by GATE16_KAPPA x u x rms(y) where rms(y) is the pair's output rms over ALL m lags
 * (Parseval: an out-of-window glitch raises the error everywhere, so the bound must see
 * it) and u = 2^-11. The gate therefore reports, per pair, an UPPER BOUND on the FP32
 * magnitude, |y16|max (1 + 3u) + kappa*u*rms(y) (the first factor is the proven cost of
 * choosing the lag on FP16 powers, see run()), and the hierarchical filter compares that bound
 * with the tier threshold: every pair the FP32 gate passes also passes here, so the false
 * dismissal budget the thresholds were set for is unchanged; the price is a few more
 * refinements. kappa comes from measurement (tools/gate16_error.py), not from a sweep of
 * the tests: see docs/cpu-neon-fp16-gate.md.
 *
 * Elsewhere (x86, ARM without FP16 vectors) this file compiles to stubs that report the
 * gate unavailable, and the FP32 path runs unchanged.
 */
#include <math.h>
#include <stdlib.h>
#include <string.h>

#include "hwy/highway.h"
#include "alloc.h"
#include "matchedfilter.h"

#if HWY_HAVE_FLOAT16 && HWY_ARCH_ARM_A64 && !defined(AP_NO_GATE16)
#define AP_GATE16 1
#endif

/* Measured bound multiplier on u*rms(y); see the header comment. */
#ifndef GATE16_KAPPA
#define GATE16_KAPPA 16.0
#endif

#ifdef AP_GATE16
/* The element transform with FP16 lanes. Everything the headers call `float` -- input
   pointers, twiddle tables, broadcast constants -- becomes FP16 inside this block only. */
#define float hwy::float16_t
#include "elemfft-inl.h"
#undef float

namespace ap16 {
namespace hn = hwy::HWY_NAMESPACE;
using namespace ap::HWY_NAMESPACE;
typedef hwy::float16_t h16;
static_assert(AP_W == 8, "the FP16 gate is written for 8-lane FP16 vectors");

struct Gate {
  size_t m;
  int nd, nt, ntpad;
  int M1, M2;
  emap ea;
  h16 *tre, *tim;          /* [group][element][lane], conjugated, scaled by 2^-et[t] */
  float *tinv;             /* per template: 2^et, undoes its scale */
  h16 *dre, *dim;          /* [slot][element], scaled */
  float *dinv;             /* per data slot: undoes its scale */
  float *t2;               /* [group][element][lane] |T|^2 of the stored (rounded) templates */
  float *d2;               /* [slot][element] |D|^2 of the stored data */
  h16 *w1r, *w1i;          /* element split twiddles */
  vf *bR, *bI, *sR, *sI;
};

static float pow2_scale(const float *spec, size_t m, float *inv) {
  float mx = 0.f;
  for (size_t k = 0; k < 2 * m; k++) mx = fmaxf(mx, fabsf(spec[k]));
  if (!(mx > 0.f) || !isfinite(mx)) { *inv = 1.f; return 1.f; }
  int e;
  frexpf(mx, &e);                       /* mx = f * 2^e, f in [0.5, 1) */
  *inv = ldexpf(1.f, e);
  return ldexpf(1.f, -e);               /* scaled max in [0.5, 1) */
}

static void destroy(Gate *g) {
  if (!g) return;
  free(g->tre); free(g->tim); free(g->tinv); free(g->dre); free(g->dim); free(g->dinv);
  free(g->w1r); free(g->w1i); free(g->bR); free(g->bI); free(g->sR); free(g->sI);
  free(g->t2); free(g->d2);
  free(g);
}

static Gate *create(size_t m, int nd, int nt) {
  if (!esupported((int)m) || m > 32767 || nd < 1 || nt < 1) return nullptr;  /* int16 lags */
  Gate *g = (Gate *)calloc(1, sizeof(Gate));
  if (!g) return nullptr;
  g->m = m; g->nd = nd; g->nt = nt;
  g->ntpad = (nt + AP_W - 1) / AP_W * AP_W;
  efactor((int)m, &g->M1, &g->M2);
  g->ea = emake(g->M1, g->M2);
  const size_t se = (g->M2 == 1) ? m : (size_t)ESTRIDE(g->M1) * g->M2;
  g->tre = (h16 *)ap_alloc64((size_t)g->ntpad * m * sizeof(h16));
  g->tim = (h16 *)ap_alloc64((size_t)g->ntpad * m * sizeof(h16));
  g->tinv = (float *)calloc((size_t)g->ntpad, sizeof(float));
  g->dre = (h16 *)ap_alloc64((size_t)nd * m * sizeof(h16));
  g->dim = (h16 *)ap_alloc64((size_t)nd * m * sizeof(h16));
  g->dinv = (float *)calloc((size_t)nd, sizeof(float));
  g->t2 = (float *)ap_alloc64((size_t)g->ntpad * m * sizeof(float));
  g->d2 = (float *)ap_alloc64((size_t)nd * m * sizeof(float));
  g->w1r = (h16 *)ap_alloc64(m * sizeof(h16));
  g->w1i = (h16 *)ap_alloc64(m * sizeof(h16));
  g->bR = (vf *)ap_alloc64(se * sizeof(vf)); g->bI = (vf *)ap_alloc64(se * sizeof(vf));
  g->sR = (vf *)ap_alloc64(se * sizeof(vf)); g->sI = (vf *)ap_alloc64(se * sizeof(vf));
  if (!g->tre || !g->tim || !g->tinv || !g->dre || !g->dim || !g->dinv || !g->w1r || !g->w1i
      || !g->bR || !g->bI || !g->sR || !g->sI || !g->t2 || !g->d2) { destroy(g); return nullptr; }
  memset(g->t2, 0, (size_t)g->ntpad * m * sizeof(float));
  /* padding lanes must be finite: zero templates */
  memset(g->tre, 0, (size_t)g->ntpad * m * sizeof(h16));
  memset(g->tim, 0, (size_t)g->ntpad * m * sizeof(h16));
  for (int t = 0; t < g->ntpad; t++) g->tinv[t] = 1.f;
  /* the same twiddles as the FP32 pair plan (create_small), rounded to FP16 */
  const int M1 = g->M1, M2 = g->M2;
  for (int k = 0; k < (M2 == 1 ? 1 : M2); k++)
    for (int e = 0; e < M1; e++) {
      double a = -2.0 * M_PI * (double)e * k / (double)m;
      g->w1r[(size_t)k * M1 + e] = hwy::F16FromF32((float)cos(a));
      g->w1i[(size_t)k * M1 + e] = hwy::F16FromF32((float)sin(a));
    }
  return g;
}

/* As ap_mf_set_template on a pair-batched plan: conjugated at ingest, [group][k][lane]. */
static int set_template(Gate *g, int t, const float *spec) {
  if (t < 0 || t >= g->nt) return -1;
  const size_t m = g->m;
  float inv;
  const float s = pow2_scale(spec, m, &inv);
  g->tinv[t] = inv;
  const size_t base = (size_t)(t / AP_W) * m * AP_W + (size_t)(t % AP_W);
  for (size_t k = 0; k < m; k++) {
    const h16 r = hwy::F16FromF32(spec[2 * k] * s), i = hwy::F16FromF32(-spec[2 * k + 1] * s);
    g->tre[base + k * AP_W] = r;
    g->tim[base + k * AP_W] = i;
    const float fr = hwy::F32FromF16(r), fi = hwy::F32FromF16(i);
    g->t2[base + k * AP_W] = fr * fr + fi * fi;
  }
  return 0;
}

static int set_data(Gate *g, int d, const float *spec) {
  if (d < 0 || d >= g->nd) return -1;
  const size_t m = g->m;
  float inv;
  const float s = pow2_scale(spec, m, &inv);
  g->dinv[d] = inv;
  h16 *re = g->dre + (size_t)d * m, *im = g->dim + (size_t)d * m;
  float *p2 = g->d2 + (size_t)d * m;
  for (size_t k = 0; k < m; k++) {
    re[k] = hwy::F16FromF32(spec[2 * k] * s);
    im[k] = hwy::F16FromF32(spec[2 * k + 1] * s);
    const float fr = hwy::F32FromF16(re[k]), fi = hwy::F32FromF16(im[k]);
    p2[k] = fr * fr + fi * fi;
  }
  return 0;
}

/* One data slot against one 8-template group: transform, then the windowed maximum and
   the all-lag power, in FP32. Results per lane: max |y|^2 in [ws, we), its lag, the value,
   and sum |y|^2 over all m lags. */
static void pair_group(Gate *g, int d, int grp, size_t ws, size_t we,
                       float *m2_out, int *idx_out, float *re_out, float *im_out,
                       float *pow_out) {
  const size_t m = g->m;
  efft_prod_broadcast((int)m, g->dre + (size_t)d * m, g->dim + (size_t)d * m,
                      g->tre + (size_t)grp * m * AP_W, g->tim + (size_t)grp * m * AP_W,
                      g->bR, g->bI, g->sR, g->sI, g->w1r, g->w1i);
  /* All-lag power by Parseval, sum_k |y_k|^2 = m sum_j |x_j|^2 with |x_j|^2 = |D_j|^2 |T_j|^2,
     in FP32 from the stored values: m FMAs instead of a pass over every output lag. */
  const hn::ScalableTag<float> df;           /* 4 lanes: each FP16 lane group is two of these */
  using VF = hn::Vec<decltype(df)>;
  VF pw0 = hn::Zero(df), pw1 = hn::Zero(df);
  {
    const float *d2 = g->d2 + (size_t)d * m, *t2 = g->t2 + (size_t)grp * m * AP_W;
    /* four elements per step into independent sums: the FMA latency, not its rate,
       bounds a single accumulator chain */
    VF a0 = pw0, a1 = pw0, b0 = pw0, b1 = pw0, c0 = pw0, c1 = pw0;
    size_t k = 0;
    for (; k + 4 <= m; k += 4) {
      const float *t = t2 + k * AP_W;
      const VF d0 = hn::Set(df, d2[k]), d1 = hn::Set(df, d2[k + 1]);
      const VF e0 = hn::Set(df, d2[k + 2]), e1 = hn::Set(df, d2[k + 3]);
      pw0 = hn::MulAdd(d0, hn::LoadU(df, t), pw0);
      pw1 = hn::MulAdd(d0, hn::LoadU(df, t + 4), pw1);
      a0 = hn::MulAdd(d1, hn::LoadU(df, t + 8), a0);
      a1 = hn::MulAdd(d1, hn::LoadU(df, t + 12), a1);
      b0 = hn::MulAdd(e0, hn::LoadU(df, t + 16), b0);
      b1 = hn::MulAdd(e0, hn::LoadU(df, t + 20), b1);
      c0 = hn::MulAdd(e1, hn::LoadU(df, t + 24), c0);
      c1 = hn::MulAdd(e1, hn::LoadU(df, t + 28), c1);
    }
    for (; k < m; k++) {
      const VF dk = hn::Set(df, d2[k]);
      pw0 = hn::MulAdd(dk, hn::LoadU(df, t2 + k * AP_W), pw0);
      pw1 = hn::MulAdd(dk, hn::LoadU(df, t2 + k * AP_W + 4), pw1);
    }
    pw0 = hn::Add(hn::Add(pw0, a0), hn::Add(b0, c0));
    pw1 = hn::Add(hn::Add(pw1, a1), hn::Add(b1, c1));
    const VF mm = hn::Set(df, (float)m);
    hn::StoreU(hn::Mul(pw0, mm), df, pow_out);
    hn::StoreU(hn::Mul(pw1, mm), df, pow_out + 4);
  }
  float pmax = 0.f;
  for (int l = 0; l < AP_W; l++) pmax = fmaxf(pmax, pow_out[l]);
  /* The window maximum of |a y|^2 in FP16, a = 2^q chosen so the largest lane's whole
     output power maps to <= 2^14: every |a y|^2 then fits FP16 (coarse lengths keep lags in
     int16). The lanes share one data block and unit-norm templates, so no lane's power sits
     near FP16's subnormals. The chosen lag's value is then re-read in FP32; choosing it on
     FP16 powers can only pick a near-tie, whose cost run() bounds by the factor (1 + 3u). */
  int q = 0;
  if (pmax > 0.f) {
    int e2;
    frexpf(16384.f / pmax, &e2);             /* 16384/pmax in [2^(e2-1), 2^e2) */
    q = (e2 - 1) >> 1;                       /* a^2 = 2^(2q) <= 16384/pmax */
    if (q > 7) q = 7;
    if (q < -7) q = -7;
  }
  const hn::RebindToSigned<decltype(AP_D)> d16;
  using V16 = hn::Vec<decltype(d16)>;
  const vf av = hn::Set(AP_D, hwy::F16FromF32(ldexpf(1.f, q)));
  /* two interleaved chains (even and odd lags), merged at the end: the compare-select
     latency, not its rate, bounds one chain */
  vf bm = hn::Set(AP_D, hwy::F16FromF32(-1.f)), cm = bm;
  V16 bx = hn::Set(d16, (int16_t)-1), cx = bx;
  const vf *R = g->bR, *I = g->bI;
  size_t k = ws;
  for (; k + 2 <= we; k += 2) {
    const int e = eidx(&g->ea, (int)k), f = eidx(&g->ea, (int)k + 1);
    const vf r = hn::Mul(R[e], av), i = hn::Mul(I[e], av);
    const vf s = hn::Mul(R[f], av), j = hn::Mul(I[f], av);
    const vf p = hn::MulAdd(r, r, hn::Mul(i, i));
    const vf q2 = hn::MulAdd(s, s, hn::Mul(j, j));
    const auto gt = hn::Gt(p, bm);
    const auto gu = hn::Gt(q2, cm);
    bm = hn::IfThenElse(gt, p, bm);
    cm = hn::IfThenElse(gu, q2, cm);
    bx = hn::IfThenElse(hn::RebindMask(d16, gt), hn::Set(d16, (int16_t)k), bx);
    cx = hn::IfThenElse(hn::RebindMask(d16, gu), hn::Set(d16, (int16_t)(k + 1)), cx);
  }
  if (k < we) {
    const int e = eidx(&g->ea, (int)k);
    const vf r = hn::Mul(R[e], av), i = hn::Mul(I[e], av);
    const vf p = hn::MulAdd(r, r, hn::Mul(i, i));
    const auto gu = hn::Gt(p, cm);
    cm = hn::IfThenElse(gu, p, cm);
    cx = hn::IfThenElse(hn::RebindMask(d16, gu), hn::Set(d16, (int16_t)k), cx);
  }
  {
    const auto gu = hn::Gt(cm, bm);              /* every chosen power is >= all others */
    bx = hn::IfThenElse(hn::RebindMask(d16, gu), cx, bx);
  }
  alignas(16) int16_t kx[AP_W];
  alignas(16) h16 lr[AP_W], li[AP_W];
  hn::StoreU(bx, d16, kx);
  for (int l = 0; l < AP_W; l++) {
    if (kx[l] < 0) { idx_out[l] = -1; m2_out[l] = re_out[l] = im_out[l] = 0.f; continue; }
    const int e = eidx(&g->ea, (int)kx[l]);
    hn::StoreU(R[e], AP_D, lr);
    hn::StoreU(I[e], AP_D, li);
    const float xr = hwy::F32FromF16(lr[l]), xi = hwy::F32FromF16(li[l]);
    idx_out[l] = kx[l];
    re_out[l] = xr; im_out[l] = xi;
    m2_out[l] = xr * xr + xi * xi;
  }
}

/* Upper bound on the FP32 gate's peak magnitude for each pair (see the header), one bin
   over [ws, we): out[d*nt + t] for d in [0,nd), t in [t0, t0+nt). index is the FP16
   argmax (or -1 for an empty window); magnitude is the BOUND; re/im the FP16 value. */
static int run(Gate *g, int d0, int nd, int t0, int nt, size_t ws, size_t we, ap_peak *out) {
  if (d0 < 0 || d0 + nd > g->nd || t0 < 0 || t0 + nt > g->nt) return -1;
  if (we > g->m) we = g->m;
  const float u = 1.0f / 2048.0f;
  /* MF_GATE16_DEBUG (measurement only, tools/gate16_error.py): kappa 0, so the magnitude
     is the FP16 maximum with only its proven lag-selection factor, and im carries the pair's all-lag rms instead of a value. */
  static const int debug = getenv("MF_GATE16_DEBUG") != nullptr;
  const float kappa = debug ? 0.f : (float)GATE16_KAPPA;
  const size_t m = g->m;
  alignas(16) float m2[AP_W], re[AP_W], im[AP_W], pw[AP_W];
  alignas(16) int ix[AP_W];
  const int g0 = t0 / AP_W, g1 = (t0 + nt - 1) / AP_W;
  /* template-outer: one group's templates stay in L1 across every block */
  for (int grp = g0; grp <= g1; grp++) {
    for (int d = 0; d < nd; d++) {
      pair_group(g, d0 + d, grp, ws, we, m2, ix, re, im, pw);
      const float dinv = g->dinv[d0 + d];
      for (int l = 0; l < AP_W; l++) {
        const int t = grp * AP_W + l;
        if (t < t0 || t >= t0 + nt) continue;
        ap_peak *o = out + (size_t)d * nt + (t - t0);
        const float sc = dinv * g->tinv[t];
        if (ix[l] < 0 || !(m2[l] >= 0.f)) {
          o->index = -1; o->re = o->im = o->magnitude = 0.f;
          continue;
        }
        const float rms = sqrtf(pw[l] / (float)m);
        o->index = ix[l];
        o->re = re[l] * sc;
        o->im = -im[l] * sc;                     /* AP_BACKWARD, as the FP32 scan reports */
        /* (1 + 3u): the lag was chosen on FP16 powers, each within a factor (1 +- u)^2 of
           the FP16 transform's |y|^2 (one exact power-of-two scale, one product, one FMA),
           so the true maximum of the FP16 transform is at most |y(chosen)| (1+u)/(1-u)
           < |y(chosen)| (1 + 3u). A proof, not a fit, and it grows with the peak, which
           the rms term does not; kappa then covers the transform's own error only. */
        o->magnitude = (sqrtf(m2[l]) * (1.f + 3.f * u) + kappa * u * rms) * sc;
        if (debug) o->im = rms * sc;
      }
    }
  }
  return 0;
}

}  // namespace ap16
#endif  /* AP_GATE16 */

extern "C" {

int ap_gate16_available(void) {
#ifdef AP_GATE16
  const char *e = getenv("MF_GATE16");
  return !(e && !atoi(e));
#else
  return 0;
#endif
}

double ap_gate16_kappa_u(void) { return GATE16_KAPPA / 2048.0; }

void *ap_gate16_create(size_t m, int nd, int nt) {
#ifdef AP_GATE16
  return ap16::create(m, nd, nt);
#else
  (void)m; (void)nd; (void)nt; return NULL;
#endif
}

void ap_gate16_destroy(void *g) {
#ifdef AP_GATE16
  ap16::destroy((ap16::Gate *)g);
#else
  (void)g;
#endif
}

int ap_gate16_set_template(void *g, int t, const float *spec) {
#ifdef AP_GATE16
  return g ? ap16::set_template((ap16::Gate *)g, t, spec) : -1;
#else
  (void)g; (void)t; (void)spec; return -1;
#endif
}

int ap_gate16_set_data(void *g, int d, const float *spec) {
#ifdef AP_GATE16
  return g ? ap16::set_data((ap16::Gate *)g, d, spec) : -1;
#else
  (void)g; (void)d; (void)spec; return -1;
#endif
}

int ap_gate16_run(void *g, int d0, int nd, int t0, int nt, size_t ws, size_t we,
                  ap_peak *out) {
#ifdef AP_GATE16
  return g ? ap16::run((ap16::Gate *)g, d0, nd, t0, nt, ws, we, out) : -1;
#else
  (void)g; (void)d0; (void)nd; (void)t0; (void)nt; (void)ws; (void)we; (void)out;
  return -1;
#endif
}

}  // extern "C"
