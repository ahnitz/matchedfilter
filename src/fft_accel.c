/* The block forward transform through the platform's own FFT, where it has one that beats
 * ours: Apple's vDSP (Accelerate) on macOS. Elsewhere every function here reports "absent"
 * and the engine's transform runs as before.
 *
 * Measured on one M2 performance core, 2048-point complex forward: vDSP_DFT_Execute on
 * split-complex data 2.00 us, its interleaved form 2.87, FFTW 3.3 (NEON, PATIENT) 3.00, the
 * engine's balanced four-step about 4.6. The split form needs the block de-interleaved,
 * which folds into the copy-and-scale the block is read with anyway, and the spectrum
 * re-interleaved for the tiers (vDSP_ztoc). Whether that wins on a given machine is not
 * assumed: it is an autotuner candidate (HierarchicalFilter's platform-FFT trial, timed on
 * real calls and kept in MF_COST_FILE), switched per plan by ap_hmf_set_platform_fft. */
#include <stdlib.h>
#include <string.h>
#include "alloc.h"
#include "transform.h"
#include "ticks.h"

#if defined(__APPLE__)
#include <Accelerate/Accelerate.h>
#if defined(__aarch64__)
#include <arm_neon.h>
#endif

struct ap_accel {
  size_t n;
  vDSP_DFT_Setup setup, inv;
  float *re, *im, *ore, *oim, *dre, *dim;
};

ap_accel *ap_accel_create(size_t n){
  if(n < 16 || (n & (n - 1))) return NULL;
  ap_accel *a = calloc(1, sizeof *a);
  if(!a) return NULL;
  a->n = n;
  a->setup = vDSP_DFT_zop_CreateSetup(NULL, (vDSP_Length)n, vDSP_DFT_FORWARD);
  a->re = ap_alloc64(n * sizeof(float)); a->im = ap_alloc64(n * sizeof(float));
  a->ore = ap_alloc64(n * sizeof(float)); a->oim = ap_alloc64(n * sizeof(float));
  if(!a->setup || !a->re || !a->im || !a->ore || !a->oim){ ap_accel_destroy(a); return NULL; }
  return a;
}

void ap_accel_destroy(ap_accel *a){
  if(!a) return;
  if(a->setup) vDSP_DFT_DestroySetup(a->setup);
  if(a->inv) vDSP_DFT_DestroySetup(a->inv);
  free(a->re); free(a->im); free(a->ore); free(a->oim); free(a->dre); free(a->dim);
  free(a);
}

/* out (interleaved, n complex) = forward DFT of scale * src[0 .. have), zero padded to n.
   The engine's forward convention (exp(-2 pi i jk/n), unnormalised). */
void ap_accel_forward(ap_accel *a, const float *src, size_t have, float scale, float *out){
  const size_t n = a->n;
  if(have > n) have = n;
  size_t k = 0;
#if defined(__aarch64__)
  const float32x4_t s = vdupq_n_f32(scale);
  for(; k + 4 <= have; k += 4){
    float32x4x2_t v = vld2q_f32(src + 2 * k);
    vst1q_f32(a->re + k, vmulq_f32(v.val[0], s));
    vst1q_f32(a->im + k, vmulq_f32(v.val[1], s));
  }
#endif
  for(; k < have; k++){ a->re[k] = src[2 * k] * scale; a->im[k] = src[2 * k + 1] * scale; }
  if(have < n){
    memset(a->re + have, 0, (n - have) * sizeof(float));
    memset(a->im + have, 0, (n - have) * sizeof(float));
  }
  vDSP_DFT_Execute(a->setup, a->re, a->im, a->ore, a->oim);
  DSPSplitComplex z = { a->ore, a->oim };
  vDSP_ztoc(&z, 1, (DSPComplex *)out, 2, (vDSP_Length)n);
}
/* The block's spectrum in natural order, split, into the plan's own data rows (for
   ap_accel_corr_block). */
static void accel_load(ap_accel *a, const float *src, size_t have, float scale){
  const size_t n = a->n;
  if(have > n) have = n;
  size_t k = 0;
#if defined(__aarch64__)
  const float32x4_t s = vdupq_n_f32(scale);
  for(; k + 4 <= have; k += 4){
    float32x4x2_t v = vld2q_f32(src + 2 * k);
    vst1q_f32(a->re + k, vmulq_f32(v.val[0], s));
    vst1q_f32(a->im + k, vmulq_f32(v.val[1], s));
  }
#endif
  for(; k < have; k++){ a->re[k] = src[2 * k] * scale; a->im[k] = src[2 * k + 1] * scale; }
  if(have < n){
    memset(a->re + have, 0, (n - have) * sizeof(float));
    memset(a->im + have, 0, (n - have) * sizeof(float));
  }
}

int ap_accel_block(ap_accel *a, const float *src, size_t have, float scale){
  const size_t n = a->n;
  if(!a->dre){
    a->dre = ap_alloc64(n * sizeof(float)); a->dim = ap_alloc64(n * sizeof(float));
    if(!a->dre || !a->dim) return -1;
  }
  accel_load(a, src, have, scale);
  vDSP_DFT_Execute(a->setup, a->re, a->im, a->dre, a->dim);
  return 0;
}

/* out[0 .. len) (interleaved) = lags lo .. lo+len of the unnormalised inverse DFT of the
   product (dr + i di)(tr + i ti), split rows of n: the engine's correlation (templates
   stored conjugated) through vDSP. */
int ap_accel_corr(ap_accel *a, const float *dr, const float *di, const float *tr,
                  const float *ti, size_t lo, size_t len, float *out){
  const size_t n = a->n;
  if(!a->inv){
    a->inv = vDSP_DFT_zop_CreateSetup(a->setup, (vDSP_Length)n, vDSP_DFT_INVERSE);
    if(!a->inv) return -1;
  }
  if(!dr){ dr = a->dre; di = a->dim; }
  DSPSplitComplex D = { (float *)dr, (float *)di }, T = { (float *)tr, (float *)ti },
                  P = { a->re, a->im };
  vDSP_zvmul(&D, 1, &T, 1, &P, 1, (vDSP_Length)n, 1);
  vDSP_DFT_Execute(a->inv, a->re, a->im, a->ore, a->oim);
  DSPSplitComplex z = { a->ore + lo, a->oim + lo };
  vDSP_ztoc(&z, 1, (DSPComplex *)out, 2, (vDSP_Length)len);
  return 0;
}
#else
int ap_accel_block(ap_accel *a, const float *src, size_t have, float scale){
  (void)a; (void)src; (void)have; (void)scale; return -1;
}
int ap_accel_corr(ap_accel *a, const float *dr, const float *di, const float *tr,
                  const float *ti, size_t lo, size_t len, float *out){
  (void)a; (void)dr; (void)di; (void)tr; (void)ti; (void)lo; (void)len; (void)out;
  return -1;
}
ap_accel *ap_accel_create(size_t n){ (void)n; return NULL; }
void ap_accel_destroy(ap_accel *a){ (void)a; }
void ap_accel_forward(ap_accel *a, const float *src, size_t have, float scale, float *out){
  (void)a; (void)src; (void)have; (void)scale; (void)out;
}
#endif
