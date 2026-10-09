/* Q15 coarse screen: the constants and tables shared by the kernel (q15-inl.h,
 * compiled per SIMD target) and the matched filter that quantises its inputs
 * (matchfilt.c, compiled at the baseline).  Target-independent C. */
#ifndef AP_Q15_H
#define AP_Q15_H
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <pthread.h>

/* Range contract (q15-inl.h): inputs are quantised so that
       |d_q|_2 |t_q|_2 / 2^15 + 1.5 N <= AP_Q15_L1,
   which bounds sum_k |p_k| (Cauchy-Schwarz, plus the product's own rounding)
   and with it every intermediate of the transform.  The remaining
   32767 - AP_Q15_L1 is headroom for the rounding the transform adds. */
#define AP_Q15_L1 30000.0

/* Template quantisation: |t_q|_2 is set to this, unless the template's
   largest component would then leave int16 (a spectrum more peaked than
   crest sqrt(N)*16384/AP_Q15_TNORM), in which case the largest component is
   set to 16384 instead and the norm comes out smaller. */
#define AP_Q15_TNORM(N) (16384.0 * sqrt((double)(N)) / 4.0)

/* Error margin in Q units (the int16 output's LSB) at transform size N: the
   screen treats |z_q - z sdt| <= ap_q15_margin(N) as the int16 transform's
   error bound.  Measured (docs/cpu-q15-gate.md, 41k pairs per N, noise data,
   random and profile-shaped templates, N = 64..1024): the error is a sum of
   independent roundings with rms 0.46-0.47 sqrt(N) LSB and a largest seen of
   4.6 rms.  The margin is 5 sqrt(N) = ~10.7 rms: a Gaussian tail of ~1e-26
   per lag.  It is derived from the rms, not tuned on pass/fail counts. */
static inline double ap_q15_margin(size_t N){
  return 5.0 * sqrt((double)N);
}

/* Transform sizes the screen implements. */
static inline int ap_q15_factor(size_t N, int *M1, int *M2){
  switch(N){
    case   64: *M1 =  8; *M2 =  8; return 0;
    case  128: *M1 = 16; *M2 =  8; return 0;
    case  256: *M1 = 16; *M2 = 16; return 0;
    case  512: *M1 = 32; *M2 = 16; return 0;
    case 1024: *M1 = 32; *M2 = 32; return 0;
  }
  return -1;
}

/* Bytes of scratch q15_screen needs for N at QW int16 lanes: two
   (M1+1) x M2 element buffers of QW int16 each. */
static inline size_t ap_q15_scratch_bytes(size_t N, int QW){
  int M1, M2;
  if(ap_q15_factor(N, &M1, &M2)) return 0;
  return (size_t)2 * (M1 + 1) * M2 * QW * sizeof(int16_t);
}

/* Four-step twiddles W_N^(e1*k2) in Q15, laid out [k2][e1] as pass 2 reads them. */
typedef struct { int16_t re[1024], im[1024]; } ap_q15_twiddles;
__attribute__((unused)) static ap_q15_twiddles ap_q15_tw_tab[5];
static pthread_once_t ap_q15_tw_once = PTHREAD_ONCE_INIT;

static inline int16_t ap_q15_round(double v){
  double r = nearbyint(v * 32768.0);
  if(r > 32767.0) r = 32767.0;
  if(r < -32767.0) r = -32767.0;
  return (int16_t)r;
}
__attribute__((unused)) static void ap_q15_tw_init(void){
  for(int i = 0; i < 5; i++){
    const size_t N = (size_t)64 << i;
    int M1, M2; ap_q15_factor(N, &M1, &M2);
    for(int k2 = 0; k2 < M2; k2++) for(int e1 = 0; e1 < M1; e1++){
      const double a = -2.0 * M_PI * (double)e1 * k2 / (double)N;
      ap_q15_tw_tab[i].re[k2 * M1 + e1] = ap_q15_round(cos(a));
      ap_q15_tw_tab[i].im[k2 * M1 + e1] = ap_q15_round(sin(a));
    }
  }
}
static inline const ap_q15_twiddles *ap_q15_twiddle_table(size_t N){
  int i = 0;
  while(i < 5 && ((size_t)64 << i) != N) i++;
  if(i == 5) return NULL;
  pthread_once(&ap_q15_tw_once, ap_q15_tw_init);
  return &ap_q15_tw_tab[i];
}

#endif
