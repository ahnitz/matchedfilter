#ifndef AP_BACKEND_H
#define AP_BACKEND_H
#include <stddef.h>
#include <stdint.h>
#include "matchedfilter.h"
/* One implementation of the transform, selected at runtime by CPU support. */
typedef struct {
  const char *name;
  int lanes;                 /* floats per vector, which the caller's layout needs */
  void *(*create)(size_t N);
  void  (*destroy)(void *);
  /* Out of place: in is read, never written (one input can feed several plans' transforms,
     as the gate model's simulation does). */
  void  (*fft)(void *, const float *in, float *out, int conj);
  int   (*supported)(size_t N);
  /* Binned maximum; writes exactly nbins dense entries. Every scan takes ph: NULL numbers
     the bins from start; otherwise ph[0] (ph[l] for lane l of a pair batch) puts the bin
     origin at start - ph, so bin j covers [start - ph + j*binsize, start - ph + (j+1)*binsize)
     clipped to [start, end) -- a window's bins rather than the block's (ap_bin_count). A
     whole bin or more of phase leaves that many empty bins first. */
  int   (*binmax)(void *, const float *in, size_t binsize, float thr,
                  ap_peak *out, int conj, size_t start, size_t end, const unsigned *ph);
  /* Same, but the input is already split into re/im.  Two contract differences
     that exist to keep the matched filter's pair loop free of copies:
       - re/im are CONSUMED IN PLACE and left undefined on return;
       - the input is NOT conjugated for a backward transform.  The caller folds
         that into however it produced the data (for a product it is free), and
         conj here only sets the sign of the reported imaginary parts. */
  int   (*binmax_split)(void *, const float *re, const float *im, size_t binsize,
                        float thr, ap_peak *out, int conj, size_t start, size_t end,
                        const unsigned *ph);
  /* matched filter: form conj(D*T) inside stage A's load, so the product never
     reaches memory.  Inputs are read-only here, unlike binmax_split. */
  /* 1 if binmax_prod works for this plan's length */
  int   (*has_prod)(void *);
  /* report the plan's N1 x N2 split; 0 if it has none */
  int   (*split)(void *, int *n1, int *n2);
  int   (*binmax_prod)(void *, const float *dr, const float *di,
                       const float *tr, const float *ti, size_t binsize,
                       float thr, ap_peak *out, int conj, size_t start, size_t end,
                       const unsigned *ph);
  int   (*corr_prod)(void *, const float *dr, const float *di,
                     const float *tr, const float *ti, float *out);
  int   (*corr_split)(void *, const float *re, const float *im, float *out);
  /* Lane count when this plan batches PAIRS instead of frequencies -- the
     small-N path, where no balanced split exists.  0 for every other plan. */
  int   (*pairbatch)(void *);
  /* nlane pairs at once. dr/di are scalar if broadcast_data is true;
     otherwise all inputs have AP_W contiguous lanes; `out` is dense [nlane][nbins]. */
  int   (*binmax_prod_batch)(void *, const float *dr, const float *di,
                             const float *tr, const float *ti, int nlane,
                             size_t binsize, float thr, ap_peak *out, int conj,
                             size_t start, size_t end, const unsigned *ph);
  int   (*binmax_prod_batch_lanes)(void *, const float *dr, const float *di,
                                   const float *tr, const float *ti, int nlane,
                                   size_t binsize, float thr, ap_peak *out, int conj,
                                   size_t start, size_t end, const unsigned *ph);
  int   (*corr_prod_batch)(void *, const float *dr, const float *di,
                           const float *tr, const float *ti, int nlane,
                           float *out);
  void *(*create_pairbatch)(size_t N);
  int (*broadcast_data)(void *);
  /* Optional positive-threshold peak consumer; other calls retain binmax_prod. */
  int (*binmax_prod_threshold)(void *, const float *, const float *,
                              const float *, const float *, size_t,
                              float, ap_peak *, int, size_t, size_t, const unsigned *);
  /* Q15 coarse screen (q15-inl.h): int16 lanes per call; for that many pairs,
     bit l of *bits set when lane l's maximum of |z|^2/2^15 over [start,end)
     reaches lanethr[l] (and the maxima in lanemax, when not NULL). */
  int (*q15_lanes)(void);
  int (*q15_screen)(size_t N, const int16_t *dq, const int16_t *tr, const int16_t *ti,
                    size_t start, size_t end, const int16_t *lanethr, uint64_t *bits,
                    int16_t *lanemax, void *scratch);
  /* Direct correlation with real taps over nlag consecutive lags (td-inl.h):
     out[i] = sum_k taps[k] x[i+k], x and out interleaved complex. */
  void (*td_corr)(const float *x, const float *taps, int L, int nlag, float *out);
  /* A real block's full spectrum from its half-size transform (rsplit-inl.h). */
  void (*real_split)(const float *Z, const float *tw, size_t n, float *X);
  /* The root stage's band-limited product, merged for a half-size backward transform
     (rsplit-inl.h). */
  void (*root_merge)(const float *D, const float *T, size_t k0, size_t k1, float scale,
                     const float *tw, size_t n, float *Z);
  /* Optional N-point tile (any N q15_screen takes): T = QW/4 or QW/2 templates repeated for
     QW/T data blocks. */
  int (*q15_screen_tile)(size_t N, int T, const int16_t *, const int16_t *, const int16_t *,
                         size_t, size_t, const int16_t *, uint64_t *, int16_t *, void *);
  /* Listed pairs: as q15_screen, lane l's data being lane dsel[l] of dr/di ([N][lanes] across
     data blocks) and its template lane tsel[l] of the two template groups at tr/ti, tr/ti+TW. */
  int (*q15_screen_perm)(size_t N, const int16_t *dr, const int16_t *di, const int16_t *tr,
                         const int16_t *ti, long TW, const int16_t *dsel, const int16_t *tsel,
                         size_t start, size_t end, const int16_t *lanethr, uint64_t *bits,
                         int16_t *lanemax, void *scratch);
  /* Eight data rows (float re, im; scales sc) into eight consecutive lanes of a [N][lanes]
     int16 slab, rounded to nearest as the screen's data quantisation is. */
  void (*q15_slab8)(size_t N, const float *const *rr, const float *const *ri, const float *sc,
                    int16_t *xr, int16_t *xi);
  /* A spectrum into a plan's split, group-major layout (loads-inl.h split_store). */
  void (*split_store)(const float *x, float *re, float *im, size_t n, int conj, int n1, int n2,
                      int w);
  /* dst = src[k*stride] * scale for k < have, zero to n (loads-inl.h scale_load). */
  void (*scale_load)(float *dst, const float *src, size_t have, size_t n, size_t stride,
                     float scale);
  /* dst[k*w + l] = src[l][k] (zero past cnt) for k < n (loads-inl.h lanes_transpose). */
  void (*lanes_transpose)(float *dst, const float *const *src, int cnt, size_t n, int w);
} ap_backend;

/* The kernel for the target Highway's runtime dispatch selected, or NULL if
   MF_ISA named something this build does not contain. */
#ifdef __cplusplus
extern "C" {
#endif
const ap_backend *ap_backend_active(void);
#ifdef __cplusplus
}
#endif
#endif
