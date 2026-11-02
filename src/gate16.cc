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
 * The gate's statistic: each pair's FP16 maximum magnitude over the searched window, its
 * own statistic, which the hierarchical filter compares with the tier threshold, as the
 * GPU's fp16 tier and the x86 Q15 screen do theirs. It tracks the FP32 maximum to FP16
 * precision (u = 2^-11 relative to the pair's output rms); what that rounding does to the
 * search is accepted by the chain's false dismissal against the flat filter
 * (tools/fdr_audit.py on the ARM runner), not bounded here. It once reported an upper
 * bound, |y16|max (1 + 3u) + kappa u rms(y) with kappa 16: that passed pairs no plan priced,
 * and single-tier chains at bands 1024 and 2048 dismissed 0.15-0.22x their plan on Apple
 * silicon (CI macOS arm64, 2026-10-30). See docs/cpu-neon-fp16-gate.md.
 *
 * Elsewhere (x86, ARM without FP16 vectors) this file compiles to stubs that report the
 * gate unavailable, and the FP32 path runs unchanged.
 */
#include <math.h>
#include <stdlib.h>
#include <string.h>

#include "hwy/highway.h"
#include "alloc.h"
#include "env.h"
#include "matchedfilter.h"

#if HWY_HAVE_FLOAT16 && HWY_ARCH_ARM_A64 && !defined(AP_NO_GATE16)
#define AP_GATE16 1
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
  int debug;
  emap ea;
  h16 *tre, *tim;          /* [group][element][lane], conjugated, scaled by 2^-et[t] */
  float *tinv;             /* per template: 2^et, undoes its scale */
  float *tsum2;            /* per template: sum_k |T_k|^2 of stored FP16 values */
  h16 *dre, *dim;          /* [slot][element], scaled */
  float *dinv;             /* per data slot: undoes its scale */
  float *dsum2;            /* per data slot: sum_k |D_k|^2 of stored FP16 values */
  float *t2;               /* [group][element][lane] |T|^2 (allocated only when debug != 0) */
  float *d2;               /* [slot][element] |D|^2 (allocated only when debug != 0) */
  h16 *w1r, *w1i;          /* element split twiddles */
  int *live;               /* storage slots of the window's lags (run_max), cached per window */
  h16 *trow_re, *trow_im;  /* [ntpad][m] contiguous per-template FP16 rows (lazy, run_pairs) */
  int trow_ready;
  h16 *gtre, *gtim;        /* one gathered template group (debug run_pairs) */
  h16 *gdre, *gdim;        /* one gathered data group (debug run_pairs) */
  float *gt2, *gd2;
  size_t live_n, live_ws, live_we;
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
  free(g->tre); free(g->tim); free(g->tinv); free(g->tsum2);
  free(g->dre); free(g->dim); free(g->dinv); free(g->dsum2);
  free(g->w1r); free(g->w1i); free(g->bR); free(g->bI); free(g->sR); free(g->sI);
  free(g->live); free(g->trow_re); free(g->trow_im);
  free(g->gtre); free(g->gtim); free(g->gt2);
  free(g->gdre); free(g->gdim); free(g->gd2);
  free(g->t2); free(g->d2);
  free(g);
}

static Gate *create(size_t m, int nd, int nt) {
  if (!esupported((int)m) || m > 32767 || nd < 1 || nt < 1) return nullptr;  /* int16 lags */
  Gate *g = (Gate *)calloc(1, sizeof(Gate));
  if (!g) return nullptr;
  g->m = m; g->nd = nd; g->nt = nt;
  g->ntpad = (nt + AP_W - 1) / AP_W * AP_W;
  g->debug = ap_env_flag("MF_GATE16_DEBUG", 0) || ap_env_flag("MF_GATE16_DEBUG_MAX", 0);
  efactor((int)m, &g->M1, &g->M2);
  g->ea = emake(g->M1, g->M2);
  const size_t se = (g->M2 == 1) ? m : (size_t)ESTRIDE(g->M1) * g->M2;
  g->tre = (h16 *)ap_alloc64((size_t)g->ntpad * m * sizeof(h16));
  g->tim = (h16 *)ap_alloc64((size_t)g->ntpad * m * sizeof(h16));
  g->tinv = (float *)calloc((size_t)g->ntpad, sizeof(float));
  g->tsum2 = (float *)calloc((size_t)g->ntpad, sizeof(float));
  g->dre = (h16 *)ap_alloc64((size_t)nd * m * sizeof(h16));
  g->dim = (h16 *)ap_alloc64((size_t)nd * m * sizeof(h16));
  g->dinv = (float *)calloc((size_t)nd, sizeof(float));
  g->dsum2 = (float *)calloc((size_t)nd, sizeof(float));
  if (g->debug) {
    g->t2 = (float *)ap_alloc64((size_t)g->ntpad * m * sizeof(float));
    g->d2 = (float *)ap_alloc64((size_t)nd * m * sizeof(float));
  }
  g->w1r = (h16 *)ap_alloc64(m * sizeof(h16));
  g->w1i = (h16 *)ap_alloc64(m * sizeof(h16));
  g->bR = (vf *)ap_alloc64(se * sizeof(vf)); g->bI = (vf *)ap_alloc64(se * sizeof(vf));
  g->sR = (vf *)ap_alloc64(se * sizeof(vf)); g->sI = (vf *)ap_alloc64(se * sizeof(vf));
  if (!g->tre || !g->tim || !g->tinv || !g->tsum2 || !g->dre || !g->dim || !g->dinv || !g->dsum2
      || !g->w1r || !g->w1i || !g->bR || !g->bI || !g->sR || !g->sI
      || (g->debug && (!g->t2 || !g->d2))) { destroy(g); return nullptr; }
  if (g->t2) memset(g->t2, 0, (size_t)g->ntpad * m * sizeof(float));
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
  double sum2 = 0.0;
  for (size_t k = 0; k < m; k++) {
    const h16 r = hwy::F16FromF32(spec[2 * k] * s), i = hwy::F16FromF32(-spec[2 * k + 1] * s);
    g->tre[base + k * AP_W] = r;
    g->tim[base + k * AP_W] = i;
    const float fr = hwy::F32FromF16(r), fi = hwy::F32FromF16(i);
    const float pk = fr * fr + fi * fi;
    sum2 += pk;
    if (g->t2) g->t2[base + k * AP_W] = pk;
  }
  g->tsum2[t] = (float)sum2;
  g->trow_ready = 0;
  return 0;
}

static int set_data(Gate *g, int d, const float *spec) {
  if (d < 0 || d >= g->nd) return -1;
  const size_t m = g->m;
  float inv;
  const float s = pow2_scale(spec, m, &inv);
  g->dinv[d] = inv;
  h16 *re = g->dre + (size_t)d * m, *im = g->dim + (size_t)d * m;
  float *p2 = g->d2 ? g->d2 + (size_t)d * m : nullptr;
  double sum2 = 0.0;
  for (size_t k = 0; k < m; k++) {
    re[k] = hwy::F16FromF32(spec[2 * k] * s);
    im[k] = hwy::F16FromF32(spec[2 * k + 1] * s);
    const float fr = hwy::F32FromF16(re[k]), fi = hwy::F32FromF16(im[k]);
    const float pk = fr * fr + fi * fi;
    sum2 += pk;
    if (p2) p2[k] = pk;
  }
  g->dsum2[d] = (float)sum2;
  return 0;
}

static void parseval_group(const float *d2, const float *t2, size_t m, float *pow_out) {
  const hn::ScalableTag<float> df;           /* 4 lanes: each FP16 lane group is two of these */
  using VF = hn::Vec<decltype(df)>;
  VF pw0 = hn::Zero(df), pw1 = hn::Zero(df);
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

/* One data slot against one 8-template group: transform, then the windowed maximum and
   the all-lag power, in FP32. Results per lane: max |y|^2 in [ws, we), its lag, the value,
   and (when g->debug != 0) sum |y|^2 over all m lags. */
static void pair_group(Gate *g, int d, int grp, size_t ws, size_t we,
                       float *m2_out, int *idx_out, float *re_out, float *im_out,
                       float *pow_out) {
  const size_t m = g->m;
  efft_prod_broadcast((int)m, g->dre + (size_t)d * m, g->dim + (size_t)d * m,
                      g->tre + (size_t)grp * m * AP_W, g->tim + (size_t)grp * m * AP_W,
                      g->bR, g->bI, g->sR, g->sI, g->w1r, g->w1i);
  float pmax = 0.f;
  if (g->debug) {
    /* All-lag power by Parseval, sum_k |y_k|^2 = m sum_j |D_j|^2 |T_j|^2, for debug rms. */
    parseval_group(g->d2 + (size_t)d * m, g->t2 + (size_t)grp * m * AP_W, m, pow_out);
    for (int l = 0; l < AP_W; l++) pmax = fmaxf(pmax, pow_out[l]);
  } else {
    /* O(1) Cauchy-Schwarz bound: |y_k|^2 <= (sum_j |D_j|^2)(sum_j |T_j|^2) for every lag k. */
    float tmax = 0.f;
    for (int l = 0; l < AP_W; l++) tmax = fmaxf(tmax, g->tsum2[grp * AP_W + l]);
    pmax = g->dsum2[d] * tmax;
  }
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
  const hn::RebindToUnsigned<decltype(AP_D)> du;
  using V16 = hn::Vec<decltype(d16)>;
  using VU = hn::Vec<decltype(du)>;
  const VU emask = hn::Set(du, (uint16_t)0x7C00u), estep = hn::Set(du, (uint16_t)0x0400u);
  VU ov = hn::Zero(du);
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
    ov = hn::Or(ov, hn::Add(hn::And(hn::BitCast(du, p), emask), estep));
    ov = hn::Or(ov, hn::Add(hn::And(hn::BitCast(du, q2), emask), estep));
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
    ov = hn::Or(ov, hn::Add(hn::And(hn::BitCast(du, p), emask), estep));
    const auto gu = hn::Gt(p, cm);
    cm = hn::IfThenElse(gu, p, cm);
    cx = hn::IfThenElse(hn::RebindMask(d16, gu), hn::Set(d16, (int16_t)k), cx);
  }
  {
    const auto gu = hn::Gt(cm, bm);              /* every chosen power is >= all others */
    bx = hn::IfThenElse(hn::RebindMask(d16, gu), cx, bx);
  }
  alignas(16) int16_t kx[AP_W];
  alignas(16) uint16_t ovx[AP_W];
  alignas(16) h16 lr[AP_W], li[AP_W];
  hn::StoreU(bx, d16, kx);
  hn::StoreU(ov, du, ovx);
  for (int l = 0; l < AP_W; l++) {
    if (ws < we && (ovx[l] & 0x8000u)) {
      idx_out[l] = kx[l] >= 0 ? kx[l] : (int)ws;
      re_out[l] = 3.402823e38f; im_out[l] = 0.f; m2_out[l] = INFINITY;
      continue;
    }
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

/* The gate decision alone: the window maximum of the FP16 powers, no argmax.

   hmf.c reads only whether a tier-0 pair fires (index >= 0, magnitude >= thr); its lag and
   value have no reader. Electing the lag (a compare and two selects per lag, plus the
   output-order index of every lag) was most of pair_group's scan. Here the window's lags
   are walked in storage order through a list built once per window, with one maximum per
   lag. The bound uses the maximum itself: every FP16 power |a y|^2 (one exact scale, one
   product, one FMA) is within (1 +- u)^2 of the FP16 transform's, so |y16|max <=
   sqrt(Pmax)/a / (1 - u) < sqrt(Pmax)/a (1 + 2u) -- the guarantee pair_group's
   |y(chosen)| (1 + 3u) gives. */
static int live_list(Gate *g, size_t ws, size_t we) {
  if (g->live && g->live_ws == ws && g->live_we == we) return 0;
  if (!g->live) {
    g->live = (int *)malloc(g->m * sizeof(int));
    if (!g->live) return -1;
  }
  size_t n = 0;
  for (size_t k = ws; k < we; k++) g->live[n++] = eidx(&g->ea, (int)k);
  g->live_n = n; g->live_ws = ws; g->live_we = we;
  return 0;
}

static void pair_group_max_t(Gate *g, int d, const h16 *tre, const h16 *tim, const float *t2g,
                             float tsum2_max, float *m2_out, float *pow_out);
static void pair_group_max(Gate *g, int d, int grp, float *m2_out, float *pow_out) {
  const size_t m = g->m;
  float tmax = 0.f;
  for (int l = 0; l < AP_W; l++) tmax = fmaxf(tmax, g->tsum2[grp * AP_W + l]);
  pair_group_max_t(g, d, g->tre + (size_t)grp * m * AP_W, g->tim + (size_t)grp * m * AP_W,
                   g->t2 ? g->t2 + (size_t)grp * m * AP_W : nullptr, tmax, m2_out, pow_out);
}

/* Scan the transformed 8-lane bR/bI buffer over [ws, we) with window maximum and elected lag. */
static void scan_elect_window(Gate *g, size_t ws, size_t we, float pmax,
                              float *m2_out, int *idx_out, float *re_out, float *im_out) {
  int q = 0;
  if (pmax > 0.f) {
    int e2;
    frexpf(16384.f / pmax, &e2);
    q = (e2 - 1) >> 1;
    if (q > 7) q = 7;
    if (q < -7) q = -7;
  }
  const hn::RebindToSigned<decltype(AP_D)> d16;
  const hn::RebindToUnsigned<decltype(AP_D)> du;
  using V16 = hn::Vec<decltype(d16)>;
  using VU = hn::Vec<decltype(du)>;
  const VU emask = hn::Set(du, (uint16_t)0x7C00u), estep = hn::Set(du, (uint16_t)0x0400u);
  VU ov = hn::Zero(du);
  const vf av = hn::Set(AP_D, hwy::F16FromF32(ldexpf(1.f, q)));
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
    ov = hn::Or(ov, hn::Add(hn::And(hn::BitCast(du, p), emask), estep));
    ov = hn::Or(ov, hn::Add(hn::And(hn::BitCast(du, q2), emask), estep));
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
    ov = hn::Or(ov, hn::Add(hn::And(hn::BitCast(du, p), emask), estep));
    const auto gu = hn::Gt(p, cm);
    cm = hn::IfThenElse(gu, p, cm);
    cx = hn::IfThenElse(hn::RebindMask(d16, gu), hn::Set(d16, (int16_t)k), cx);
  }
  {
    const auto gu = hn::Gt(cm, bm);
    bx = hn::IfThenElse(hn::RebindMask(d16, gu), cx, bx);
  }
  alignas(16) int16_t kx[AP_W];
  alignas(16) uint16_t ovx[AP_W];
  alignas(16) h16 lr[AP_W], li[AP_W];
  hn::StoreU(bx, d16, kx);
  hn::StoreU(ov, du, ovx);
  for (int l = 0; l < AP_W; l++) {
    if (ws < we && (ovx[l] & 0x8000u)) {
      idx_out[l] = kx[l] >= 0 ? kx[l] : (int)ws;
      re_out[l] = 3.402823e38f; im_out[l] = 0.f; m2_out[l] = INFINITY;
      continue;
    }
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

/* Scan the transformed 8-lane bR/bI buffer in storage order (g->live) for window max only. */
static void scan_max_window(Gate *g, float pmax, float *m2_out) {
  int q = 0;
  if (pmax > 0.f) {
    int e2;
    frexpf(16384.f / pmax, &e2);
    q = (e2 - 1) >> 1;
    if (q > 7) q = 7;
    if (q < -7) q = -7;
  }
  const hn::RebindToUnsigned<decltype(AP_D)> du;
  using VU = hn::Vec<decltype(du)>;
  const VU emask = hn::Set(du, (uint16_t)0x7C00u), estep = hn::Set(du, (uint16_t)0x0400u);
  VU ov = hn::Zero(du);
  const vf av = hn::Set(AP_D, hwy::F16FromF32(ldexpf(1.f, q)));
  vf bm = hn::Zero(AP_D), cm = bm;
  const vf *R = g->bR, *I = g->bI;
  const int *L = g->live;
  size_t j = 0;
  for (; j + 2 <= g->live_n; j += 2) {
    const int e = L[j], f = L[j + 1];
    const vf r = hn::Mul(R[e], av), i = hn::Mul(I[e], av);
    const vf s = hn::Mul(R[f], av), t = hn::Mul(I[f], av);
    const vf p = hn::MulAdd(r, r, hn::Mul(i, i));
    const vf q2 = hn::MulAdd(s, s, hn::Mul(t, t));
    ov = hn::Or(ov, hn::Add(hn::And(hn::BitCast(du, p), emask), estep));
    ov = hn::Or(ov, hn::Add(hn::And(hn::BitCast(du, q2), emask), estep));
    bm = hn::Max(bm, p);
    cm = hn::Max(cm, q2);
  }
  if (j < g->live_n) {
    const int e = L[j];
    const vf r = hn::Mul(R[e], av), i = hn::Mul(I[e], av);
    const vf p = hn::MulAdd(r, r, hn::Mul(i, i));
    ov = hn::Or(ov, hn::Add(hn::And(hn::BitCast(du, p), emask), estep));
    cm = hn::Max(cm, p);
  }
  bm = hn::Max(bm, cm);
  alignas(16) h16 mx[AP_W];
  alignas(16) uint16_t ovx[AP_W];
  hn::StoreU(bm, AP_D, mx);
  hn::StoreU(ov, du, ovx);
  const float ia2 = ldexpf(1.f, -2 * q);
  for (int l = 0; l < AP_W; l++)
    m2_out[l] = (ovx[l] & 0x8000u) ? INFINITY : hwy::F32FromF16(mx[l]) * ia2;
}

static void pair_group_max_t(Gate *g, int d, const h16 *tre, const h16 *tim, const float *t2g,
                             float tsum2_max, float *m2_out, float *pow_out) {
  const size_t m = g->m;
  efft_prod_broadcast((int)m, g->dre + (size_t)d * m, g->dim + (size_t)d * m,
                      tre, tim, g->bR, g->bI, g->sR, g->sI, g->w1r, g->w1i);
  float pmax = 0.f;
  if (g->debug) {
    parseval_group(g->d2 + (size_t)d * m, t2g, m, pow_out);
    for (int l = 0; l < AP_W; l++) pmax = fmaxf(pmax, pow_out[l]);
  } else {
    pmax = g->dsum2[d] * tsum2_max;
  }
  scan_max_window(g, pmax, m2_out);
}

/* Unrolled 8x8 FP16 register transpose directly into bR/bI slots (zero loops, zero stack spill). */
static HWY_ATTR HWY_INLINE void transpose8_store(const vf *in, vf *dst) {
  const vf a0 = hn::InterleaveWholeLower(AP_D, in[0], in[4]);
  const vf a4 = hn::InterleaveWholeUpper(AP_D, in[0], in[4]);
  const vf a1 = hn::InterleaveWholeLower(AP_D, in[1], in[5]);
  const vf a5 = hn::InterleaveWholeUpper(AP_D, in[1], in[5]);
  const vf a2 = hn::InterleaveWholeLower(AP_D, in[2], in[6]);
  const vf a6 = hn::InterleaveWholeUpper(AP_D, in[2], in[6]);
  const vf a3 = hn::InterleaveWholeLower(AP_D, in[3], in[7]);
  const vf a7 = hn::InterleaveWholeUpper(AP_D, in[3], in[7]);

  const vf b0 = hn::InterleaveWholeLower(AP_D, a0, a2);
  const vf b2 = hn::InterleaveWholeUpper(AP_D, a0, a2);
  const vf b1 = hn::InterleaveWholeLower(AP_D, a1, a3);
  const vf b3 = hn::InterleaveWholeUpper(AP_D, a1, a3);
  const vf b4 = hn::InterleaveWholeLower(AP_D, a4, a6);
  const vf b6 = hn::InterleaveWholeUpper(AP_D, a4, a6);
  const vf b5 = hn::InterleaveWholeLower(AP_D, a5, a7);
  const vf b7 = hn::InterleaveWholeUpper(AP_D, a5, a7);

  dst[0] = hn::InterleaveWholeLower(AP_D, b0, b1);
  dst[1] = hn::InterleaveWholeUpper(AP_D, b0, b1);
  dst[2] = hn::InterleaveWholeLower(AP_D, b2, b3);
  dst[3] = hn::InterleaveWholeUpper(AP_D, b2, b3);
  dst[4] = hn::InterleaveWholeLower(AP_D, b4, b5);
  dst[5] = hn::InterleaveWholeUpper(AP_D, b4, b5);
  dst[6] = hn::InterleaveWholeLower(AP_D, b6, b7);
  dst[7] = hn::InterleaveWholeUpper(AP_D, b6, b7);
}

/* Lazily transpose [group][k][lane] templates into contiguous [t][k] FP16 rows for SIMD gather. */
static int ensure_trow(Gate *g) {
  if (g->trow_ready) return 0;
  const size_t m = g->m;
  const size_t total = (size_t)g->ntpad * m;
  if (!g->trow_re) {
    g->trow_re = (h16 *)ap_alloc64(total * sizeof(h16));
    g->trow_im = (h16 *)ap_alloc64(total * sizeof(h16));
    if (!g->trow_re || !g->trow_im) return -1;
  }
  const int ng = g->ntpad / AP_W;
  for (int grp = 0; grp < ng; grp++) {
    const h16 *sr = g->tre + (size_t)grp * m * AP_W;
    const h16 *si = g->tim + (size_t)grp * m * AP_W;
    for (size_t k0 = 0; k0 < m; k0 += AP_W) {
      vf in_r[AP_W], in_i[AP_W], out_r[AP_W], out_i[AP_W];
      for (int u = 0; u < AP_W; u++) {
        in_r[u] = V_LOADU(sr + (k0 + (size_t)u) * AP_W);
        in_i[u] = V_LOADU(si + (k0 + (size_t)u) * AP_W);
      }
      transpose8_store(in_r, out_r);
      transpose8_store(in_i, out_i);
      for (int l = 0; l < AP_W; l++) {
        const int t = grp * AP_W + l;
        V_STOREU(g->trow_re + (size_t)t * m + k0, out_r[l]);
        V_STOREU(g->trow_im + (size_t)t * m + k0, out_i[l]);
      }
    }
  }
  g->trow_ready = 1;
  return 0;
}

/* Listed pairs (d0 + dsel[i], t0 + tsel[i]) across 8 FP16 SIMD lanes: contiguous row loads
   form conj(d * t) in registers and 8x8-transpose directly into bR/bI without intermediate
   staging buffers. Storage-order scan_max_window gates every batch; scan_elect_window runs
   only on batches with at least one survivor when elect_lag != 0. */
static int run_pairs(Gate *g, int d0, int t0, const int *dsel, const int *tsel, int n,
                     int nt_row, size_t ws, size_t we, int elect_lag, float thr,
                     int *dst_d, int *dst_t, ap_peak *out) {
  if (we > g->m) we = g->m;
  if (n <= 0) return 0;
  const size_t m = g->m;
  if (live_list(g, ws, we)) return -1;
  if (!g->debug && ensure_trow(g)) return -1;
  if (g->debug && !g->gtre) {
    g->gtre = (h16 *)ap_alloc64(m * AP_W * sizeof(h16));
    g->gtim = (h16 *)ap_alloc64(m * AP_W * sizeof(h16));
    g->gt2 = (float *)ap_alloc64(m * AP_W * sizeof(float));
    if (!g->gtre || !g->gtim || !g->gt2) return -1;
  }
  const int compact = (dst_d != nullptr && dst_t != nullptr);
  int npass = 0;
  alignas(16) float m2[AP_W], re[AP_W], im[AP_W], pw[AP_W], sc_l[AP_W], mag_l[AP_W];
  alignas(16) int ix[AP_W];
  for (int i = 0; i < n;) {
    const int d_first = dsel[i];
    int same_run = 1;
    while (same_run < AP_W && i + same_run < n && dsel[i + same_run] == d_first) same_run++;
    const int batch = n - i < AP_W ? n - i : AP_W;
    const int one_d = (same_run == batch);
    float pmax = 0.f;
    if (!g->debug) {
      /* Fused contiguous FP16 row gather + complex multiply + 8x8 transpose into bR/bI. */
      const h16 *dr_l[AP_W], *di_l[AP_W], *tr_l[AP_W], *ti_l[AP_W];
      for (int l = 0; l < AP_W; l++) {
        const int u = l < batch ? l : batch - 1;
        const int gd = d0 + dsel[i + u];
        const int gt = t0 + tsel[i + u];
        sc_l[l] = g->dinv[gd] * g->tinv[gt];
        pmax = fmaxf(pmax, g->dsum2[gd] * g->tsum2[gt]);
        dr_l[l] = g->dre + (size_t)gd * m;
        di_l[l] = g->dim + (size_t)gd * m;
        tr_l[l] = g->trow_re + (size_t)gt * m;
        ti_l[l] = g->trow_im + (size_t)gt * m;
      }
      if (one_d) {
        const h16 *HWY_RESTRICT dr0 = dr_l[0], *HWY_RESTRICT di0 = di_l[0];
        for (size_t k0 = 0; k0 < m; k0 += AP_W) {
          vf pr_in[AP_W], pi_in[AP_W];
          const vf dR = V_LOADU(dr0 + k0), dI = V_LOADU(di0 + k0);
          for (int l = 0; l < AP_W; l++) {
            const vf tR = V_LOADU(tr_l[l] + k0), tI = V_LOADU(ti_l[l] + k0);
            pr_in[l] = V_FMSUB(dR, tR, V_MUL(dI, tI));
            pi_in[l] = V_FNMSUB(dR, tI, V_MUL(dI, tR));
          }
          const int slot0 = einp(&g->ea, (int)k0);
          transpose8_store(pr_in, g->bR + slot0);
          transpose8_store(pi_in, g->bI + slot0);
        }
      } else {
        for (size_t k0 = 0; k0 < m; k0 += AP_W) {
          vf pr_in[AP_W], pi_in[AP_W];
          for (int l = 0; l < AP_W; l++) {
            const vf dR = V_LOADU(dr_l[l] + k0), dI = V_LOADU(di_l[l] + k0);
            const vf tR = V_LOADU(tr_l[l] + k0), tI = V_LOADU(ti_l[l] + k0);
            pr_in[l] = V_FMSUB(dR, tR, V_MUL(dI, tI));
            pi_in[l] = V_FNMSUB(dR, tI, V_MUL(dI, tR));
          }
          const int slot0 = einp(&g->ea, (int)k0);
          transpose8_store(pr_in, g->bR + slot0);
          transpose8_store(pi_in, g->bI + slot0);
        }
      }
      efft((int)m, g->bR, g->bI, g->sR, g->sI, g->w1r, g->w1i);
    } else if (one_d) {
      for (int l = 0; l < AP_W; l++) {
        const int u = l < batch ? l : batch - 1;
        const int gd = d0 + d_first;
        const int gt = t0 + tsel[i + u];
        sc_l[l] = g->dinv[gd] * g->tinv[gt];
        const size_t base = (size_t)(gt / AP_W) * m * AP_W + (size_t)(gt % AP_W);
        const h16 *sr = g->tre + base, *si = g->tim + base;
        const float *s2 = g->t2 + base;
        for (size_t e = 0; e < m; e++) {
          g->gtre[e * AP_W + l] = sr[e * AP_W];
          g->gtim[e * AP_W + l] = si[e * AP_W];
          g->gt2[e * AP_W + l] = s2[e * AP_W];
        }
      }
      const int gd = d0 + d_first;
      efft_prod_broadcast((int)m, g->dre + (size_t)gd * m, g->dim + (size_t)gd * m,
                          g->gtre, g->gtim, g->bR, g->bI, g->sR, g->sI, g->w1r, g->w1i);
      parseval_group(g->d2 + (size_t)gd * m, g->gt2, m, pw);
      for (int l = 0; l < AP_W; l++) pmax = fmaxf(pmax, pw[l]);
    } else {
      if (!g->gdre) {
        g->gdre = (h16 *)ap_alloc64(m * AP_W * sizeof(h16));
        g->gdim = (h16 *)ap_alloc64(m * AP_W * sizeof(h16));
        g->gd2 = (float *)ap_alloc64(m * AP_W * sizeof(float));
        if (!g->gdre || !g->gdim || !g->gd2) return -1;
      }
      for (int l = 0; l < AP_W; l++) {
        const int u = l < batch ? l : batch - 1;
        const int gd = d0 + dsel[i + u];
        const int gt = t0 + tsel[i + u];
        sc_l[l] = g->dinv[gd] * g->tinv[gt];
        const h16 *dr = g->dre + (size_t)gd * m, *di = g->dim + (size_t)gd * m;
        const size_t base = (size_t)(gt / AP_W) * m * AP_W + (size_t)(gt % AP_W);
        const h16 *sr = g->tre + base, *si = g->tim + base;
        const float *d2 = g->d2 + (size_t)gd * m, *s2 = g->t2 + base;
        double sp = 0.0;
        for (size_t e = 0; e < m; e++) {
          g->gdre[e * AP_W + l] = dr[e];
          g->gdim[e * AP_W + l] = di[e];
          g->gtre[e * AP_W + l] = sr[e * AP_W];
          g->gtim[e * AP_W + l] = si[e * AP_W];
          g->gd2[e * AP_W + l] = d2[e];
          g->gt2[e * AP_W + l] = s2[e * AP_W];
          sp += (double)d2[e] * (double)s2[e * AP_W];
        }
        pw[l] = (float)(sp * (double)m);
      }
      for (int l = 0; l < AP_W; l++) pmax = fmaxf(pmax, pw[l]);
      efft_prod((int)m, g->gdre, g->gdim, g->gtre, g->gtim,
                g->bR, g->bI, g->sR, g->sI, g->w1r, g->w1i);
    }

    /* Fast storage-order window maximum first; elect lag only if a lane can reach thr. */
    scan_max_window(g, pmax, m2);
    const float thr_trig = elect_lag ? thr * 0.995f : thr;
    unsigned fire_mask = 0u;
    for (int l = 0; l < batch; l++) {
      if (g->live_n == 0 || m2[l] == 0.f) {
        mag_l[l] = 0.f;
        continue;
      }
      const float mag = !isfinite(m2[l]) ? 3.402823e38f : sqrtf(m2[l]) * sc_l[l];
      mag_l[l] = mag;
      if (mag >= thr_trig) fire_mask |= (1u << l);
    }

    if (compact) {
      if (fire_mask) {
        if (elect_lag) scan_elect_window(g, ws, we, pmax, m2, ix, re, im);
        for (int l = 0; l < batch; l++) {
          if (!(fire_mask & (1u << l))) continue;
          const int d = dsel[i + l], t = tsel[i + l];
          if (elect_lag) {
            const float sc = sc_l[l];
            if (ix[l] < 0) {
              if (out) {
                ap_peak *o = out + (size_t)d * nt_row + t;
                o->index = -1; o->re = o->im = o->magnitude = 0.f;
              }
              continue;
            }
            const float mag = !isfinite(m2[l]) ? 3.402823e38f : sqrtf(m2[l]) * sc;
            if (mag < thr) continue;
            if (out) {
              ap_peak *o = out + (size_t)d * nt_row + t;
              o->index = ix[l];
              if (!isfinite(m2[l])) {
                o->re = 3.402823e38f; o->im = 0.f; o->magnitude = 3.402823e38f;
              } else {
                o->re = re[l] * sc;
                o->im = -im[l] * sc;
                o->magnitude = mag;
              }
            }
          } else if (out) {
            ap_peak *o = out + (size_t)d * nt_row + t;
            o->index = 0; o->re = o->im = 0.f; o->magnitude = mag_l[l];
          }
          dst_d[npass] = d;
          dst_t[npass] = t;
          npass++;
        }
      }
    } else if (elect_lag && (fire_mask || thr <= 0.f)) {
      scan_elect_window(g, ws, we, pmax, m2, ix, re, im);
      for (int l = 0; l < batch; l++) {
        const int d = dsel[i + l], t = tsel[i + l];
        ap_peak *o = out + (size_t)d * nt_row + t;
        const float sc = sc_l[l];
        if (ix[l] < 0) {
          o->index = -1; o->re = o->im = o->magnitude = 0.f;
          continue;
        }
        o->index = ix[l];
        if (!isfinite(m2[l])) {
          o->re = 3.402823e38f; o->im = 0.f; o->magnitude = 3.402823e38f;
        } else {
          o->re = re[l] * sc;
          o->im = -im[l] * sc;
          o->magnitude = sqrtf(m2[l]) * sc;
        }
        if (o->magnitude >= thr) npass++;
      }
    } else {
      for (int l = 0; l < batch; l++) {
        const int d = dsel[i + l], t = tsel[i + l];
        ap_peak *o = out + (size_t)d * nt_row + t;
        if (g->live_n == 0 || mag_l[l] == 0.f) {
          o->index = -1; o->re = o->im = o->magnitude = 0.f;
          continue;
        }
        o->index = 0;
        o->re = o->im = 0.f;
        o->magnitude = mag_l[l];
        if (mag_l[l] >= thr) npass++;
      }
    }
    i += batch;
  }
  return npass;
}

static int run_max(Gate *g, int d0, int nd, int t0, int nt, size_t ws, size_t we, ap_peak *out) {
  if (d0 < 0 || d0 + nd > g->nd || t0 < 0 || t0 + nt > g->nt) return -1;
  if (we > g->m) we = g->m;
  /* MF_GATE16_DEBUG_MAX (measurement only, tools/gate16_error.py --scan max): im carries the
     pair's all-lag rms, as MF_GATE16_DEBUG does for the electing scan. */
  const int debug = g->debug && ap_env_flag("MF_GATE16_DEBUG_MAX", 0);
  const size_t m = g->m;
  if (live_list(g, ws, we)) return -1;
  alignas(16) float m2[AP_W], pw[AP_W];
  const int g0 = t0 / AP_W, g1 = (t0 + nt - 1) / AP_W;
  for (int grp = g0; grp <= g1; grp++) {
    for (int d = 0; d < nd; d++) {
      pair_group_max(g, d0 + d, grp, m2, pw);
      const float dinv = g->dinv[d0 + d];
      for (int l = 0; l < AP_W; l++) {
        const int t = grp * AP_W + l;
        if (t < t0 || t >= t0 + nt) continue;
        ap_peak *o = out + (size_t)d * nt + (t - t0);
        const float sc = dinv * g->tinv[t];
        if (g->live_n == 0 || m2[l] == 0.f) {      /* empty window or zero; NaN/Inf fail open */
          o->index = -1; o->re = o->im = o->magnitude = 0.f;
          continue;
        }
        o->index = 0;                               /* fires; the lag has no reader */
        o->re = o->im = 0.f;
        o->magnitude = !isfinite(m2[l]) ? 3.402823e38f : sqrtf(m2[l]) * sc;
        if (debug) o->im = sqrtf(pw[l] / (float)m) * sc;
      }
    }
  }
  return 0;
}

/* The FP16 gate with its elected lag (tools/gate16_error.py), one bin over [ws, we):
   out[d*nt + t] for d in [0,nd), t in [t0, t0+nt). index is the FP16 argmax (or -1 for an
   empty window); magnitude the FP16 maximum, as run_max reports it; re/im the FP16 value. */
static int run(Gate *g, int d0, int nd, int t0, int nt, size_t ws, size_t we, ap_peak *out) {
  if (d0 < 0 || d0 + nd > g->nd || t0 < 0 || t0 + nt > g->nt) return -1;
  if (we > g->m) we = g->m;
  /* MF_GATE16_DEBUG (measurement only, tools/gate16_error.py): im carries the pair's
     all-lag rms instead of a value. */
  const int debug = g->debug && ap_env_flag("MF_GATE16_DEBUG", 0);
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
        if (ix[l] < 0) {
          o->index = -1; o->re = o->im = o->magnitude = 0.f;
          continue;
        }
        o->index = ix[l];
        if (!isfinite(m2[l])) {
          o->re = 3.402823e38f; o->im = 0.f; o->magnitude = 3.402823e38f;
        } else {
          o->re = re[l] * sc;
          o->im = -im[l] * sc;                     /* AP_BACKWARD, as the FP32 scan reports */
          o->magnitude = sqrtf(m2[l]) * sc;
        }
        if (debug) o->im = sqrtf(pw[l] / (float)m) * sc;
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
  return ap_env_flag("MF_GATE16", 1);
#else
  return 0;
#endif
}


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

int ap_gate16_run_pairs_lag(void *g, int d0, int t0, const int *dsel, const int *tsel, int n,
                            int nt_row, size_t ws, size_t we, int elect_lag, float thr,
                            int *dst_d, int *dst_t, ap_peak *out) {
#ifdef AP_GATE16
  return g ? ap16::run_pairs((ap16::Gate *)g, d0, t0, dsel, tsel, n, nt_row, ws, we,
                             elect_lag, thr, dst_d, dst_t, out)
           : -1;
#else
  (void)g; (void)d0; (void)t0; (void)dsel; (void)tsel; (void)n; (void)nt_row; (void)ws; (void)we;
  (void)elect_lag; (void)thr; (void)dst_d; (void)dst_t; (void)out;
  return -1;
#endif
}

int ap_gate16_run_pairs(void *g, int d0, int t0, const int *dsel, const int *tsel, int n,
                        int nt_row, size_t ws, size_t we, ap_peak *out) {
  return ap_gate16_run_pairs_lag(g, d0, t0, dsel, tsel, n, nt_row, ws, we, 0, 0.f,
                                 NULL, NULL, out);
}

int ap_gate16_run(void *g, int d0, int nd, int t0, int nt, size_t ws, size_t we,
                  ap_peak *out) {
#ifdef AP_GATE16
  if (!g) return -1;
  /* The elected lag and value only for the error tools (MF_GATE16_DEBUG);
     the gate itself needs only the bound (run_max). */
  const int elect = ((ap16::Gate *)g)->debug && ap_env_flag("MF_GATE16_DEBUG", 0);
  return elect ? ap16::run((ap16::Gate *)g, d0, nd, t0, nt, ws, we, out)
               : ap16::run_max((ap16::Gate *)g, d0, nd, t0, nt, ws, we, out);
#else
  (void)g; (void)d0; (void)nd; (void)t0; (void)nt; (void)ws; (void)we; (void)out;
  return -1;
#endif
}

}  // extern "C"
