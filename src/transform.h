#ifndef AP_TRANSFORM_H
#define AP_TRANSFORM_H
/* Internal transform API.
 *
 * matchedfilter's interface is the matched filter; this is the machinery under it.  It
 * is a separate header rather than part of matchedfilter.h because a caller has no
 * reason to hold a transform plan - the MatchedFilter is the plan - and every
 * symbol here is used only by src/matchfilt.c, the tests and the benchmarks. */
#include <stddef.h>
#include <stdint.h>
#include "matchedfilter.h"

typedef struct ap_plan ap_plan;

/* Whether [lo, lo + cnt) lies in [0, max), without forming lo + cnt (which overflows int for
   a caller's lo near INT_MAX, and the check then passes). */
static inline int ap_range_ok(int lo, int cnt, int max){
  return lo >= 0 && cnt >= 0 && lo <= max && cnt <= max - lo;
}

ap_plan *ap_create(size_t N);
ap_plan *ap_create_pairbatch(size_t N);
void     ap_destroy(ap_plan *p);
const char *ap_plan_backend(const ap_plan *p);
int      ap_lane_width(void);

/* The same on a given plan's back end (the active one when like is NULL): a plan's
   sub-plans and kernel calls use the kernel the plan was built with, whatever target is
   selected when they are made. */
ap_plan *ap_create_like(const ap_plan *like, size_t N);
ap_plan *ap_create_pairbatch_like(const ap_plan *like, size_t N);
int      ap_plan_lanes(const ap_plan *p);

/* The SIMD targets this build holds that this CPU can run, widest first (only MF_ISA's
   when it is set), and a way to narrow the choice to one of them for a comparison.
   NULL restores the baseline: MF_ISA's target, else the hardware's choice.  A target
   outside that list returns -1 and changes nothing.  ap_isa_init applies MF_ISA and
   returns -1 when it names no target of this build. */
int         ap_isa_init(void);
int         ap_target_count(void);
const char *ap_target_name(int i);
int         ap_set_target(const char *name);

/* The plan's actual N1 x N2 split.  The matched filter stores spectra in the
   layout stage A walks, which depends on this - recomputing it independently
   would silently diverge the moment the split heuristic changed.  Returns 0 if
   the plan has no such split (the specialised 1024 kernel). */
int      ap_plan_split(const ap_plan *p, int *n1, int *n2);

/* Full transform, AP_FORWARD or AP_BACKWARD.  Neither direction scales by 1/N. */
void ap_fft(ap_plan *p, const float *in, float *out, int sign);

/* Direct correlation of an interleaved complex series with real taps over nlag consecutive
   lags: out[i] = sum_{k<L} taps[k] x[i+k] (td-inl.h). x holds nlag + L - 1 samples. */
void ap_td_corr(const float *x, const float *taps, int L, int nlag, float *out);
void ap_td_corr_on(const ap_plan *p, const float *x, const float *taps, int L, int nlag,
                   float *out);

/* A real block's full n-point spectrum X from Z, the n/2-point transform of its samples read
   as n/2 complex ones; tw: cos, sin of 2 pi k/n for k = 0 .. n/2 (rsplit-inl.h). */
void ap_real_split_on(const ap_plan *p, const float *Z, const float *tw, size_t n, float *X);

/* The root stage's product scale * conj(T) D over bins [k0, k1) of two one-sided spectra of
   n/2 + 1 bins, merged into the n/2-point spectrum Z whose backward transform is the real
   series C2R(product) read as n/2 complex samples; tw as for ap_real_split_on (rsplit-inl.h). */
void ap_root_merge_on(const ap_plan *p, const float *D, const float *T, size_t k0, size_t k1,
                      float scale, const float *tw, size_t n, float *Z);

/* The platform's FFT for the block forward (fft_accel.c): NULL where there is none. */
typedef struct ap_accel ap_accel;
ap_accel *ap_accel_create(size_t n);
void ap_accel_destroy(ap_accel *a);
void ap_accel_forward(ap_accel *a, const float *src, size_t have, float scale, float *out);
int ap_accel_block(ap_accel *a, const float *src, size_t have, float scale);
int ap_accel_corr(ap_accel *a, const float *dr, const float *di, const float *tr,
                  const float *ti, size_t lo, size_t len, float *out);

/* The widest CPU vector, in floats: lane arrays (a pair batch's bin phases) are this long. */
#define AP_MAX_LANES 16

/* Bins of a peak search over [start, end) whose bins are numbered from start - ph: ph = 0
   numbers them from start, the block's own window; a window's bins put the origin where
   the window's bin grid does (backend.h, binmax), and a whole bin or more of phase leaves
   empty bins before start. (Differences are modular, so start - ph may wrap.) */
static inline size_t ap_bin_count(size_t binsize, size_t start, size_t end, unsigned ph){
  return end > start ? (end - start + ph + binsize - 1) / binsize : 0;
}

/* Binned maximum over one transform, and the split-input variant the matched
   filter uses (consumed in place, input not conjugated); the fused product form
   that builds conj(D*T) inside the transform's load is ap_plan_prod_kernel. Every scan
   takes ph, the bin origin's offset before start: NULL for 0, else one per transform
   (ap_binmax: B of them) or per lane (the pair batches). */
int ap_binmax(ap_plan *p, const float *in, size_t dist, int B,
              size_t binsize, float threshold, ap_peak *peaks, int *counts,
              int sign, size_t start, size_t end, const unsigned *ph);
int ap_binmax_split(ap_plan *p, const float *re, const float *im,
                    size_t binsize, float threshold, ap_peak *peaks, int *count,
                    int sign, size_t start, size_t end, const unsigned *ph);
/* Does this plan have a fused product path?  The matched filter needs to know
   before ingest, because group-major storage is only correct if the fused
   loader will consume it. */
int ap_has_fused_prod(const ap_plan *p);

/* AP_W when this plan runs the pair-batched small-N path, 0 otherwise.  A
   caller that gets a non-zero answer must store its template bank
   [group][element][lane] and hand pairs over AP_W at a time. */
int ap_plan_pairbatch(const ap_plan *p);
/* Data is scalar [element] iff ap_plan_broadcast_data; otherwise lane-expanded. */
int ap_plan_broadcast_data(const ap_plan *p);
/* Peak-only batch: 0 on success, -1 on error; the bank owns crossing counts. */
int ap_binmax_prod_batch_peaks(ap_plan *p, const float *dr, const float *di,
                         const float *tr, const float *ti, int nlane,
                         size_t binsize, float threshold, ap_peak *peaks,
                         int sign, size_t start, size_t end, const unsigned *ph);
int ap_binmax_prod_batch_lanes_peaks(ap_plan *p, const float *dr, const float *di,
                                     const float *tr, const float *ti, int nlane,
                                     size_t binsize, float threshold, ap_peak *peaks,
                                     int sign, size_t start, size_t end, const unsigned *ph);

/* Bind once after bank-level argument validation. run returns 0 on success;
   the caller counts nonnegative peak indices. Valid only while the plan lives. */
typedef struct {
  void *context;
  int (*run)(void *,const float *,const float *,const float *,const float *,
             size_t,float,ap_peak *,int,size_t,size_t,const unsigned *);
} ap_prod_kernel;
ap_prod_kernel ap_plan_prod_kernel(const ap_plan *,float threshold);
int ap_corr_prod(ap_plan *p, const float *dr, const float *di,
                 const float *tr, const float *ti, float *out);
int ap_corr_split(ap_plan *p, const float *re, const float *im, float *out);
int ap_corr_prod_batch(ap_plan *p, const float *dr, const float *di,
                       const float *tr, const float *ti, int nlane, float *out);

/* Merge the even/odd correlations in consecutive data rows of a half-size
   filter into bins on the full-rate lag grid. */
/* Bin phases of a matched filter's data rows for the calls that follow, NULL to clear:
   row d's bins are numbered from start - bph[d] (ap_mf_run_series' bin_phase). */
void ap_mf_set_bin_phase(ap_mf_plan *p, const unsigned *bph);

int ap_mf_run_dif(ap_mf_plan *p, int d0, int t0, int nt,
                  size_t binsize, float threshold, ap_peak *peaks, int *counts,
                  size_t start, size_t end, unsigned ph);

/* Q15 coarse screen (q15-inl.h).  ap_q15_lanes: int16 lanes per screen call
   on the plan's back end, 0 if it has none.  ap_q15_screen: for that many
   pairs, bit l of *bits is set when lane l's maximum of |z|^2/2^15 over
   [start,end) reaches lanethr[l]; lanemax (may be NULL) receives the maxima.
   dq is [N][3] = (dr, di, -di), tr/ti are [N][lanes].  0 on success. */
int ap_q15_lanes(const ap_plan *p);
int ap_q15_has_tile(const ap_plan *p);
int ap_q15_screen(const ap_plan *p, const int16_t *dq, const int16_t *tr, const int16_t *ti,
                  size_t start, size_t end, const int16_t *lanethr, uint64_t *bits,
                  int16_t *lanemax, void *scratch);
/* Listed pairs: as ap_q15_screen, but lane l's data element is lane dsel[l] of dr/di (one
   element across up to `lanes` data blocks, laid out [N][lanes] as tr/ti are), and its template
   is lane tsel[l] (< 2 lanes) of the two template groups at tr/ti and tr/ti + tw. */
/* Eight data rows quantised (x = nearest(row * sc), re and im) into eight consecutive lanes of
   an [N][lanes] slab at xr/xi. */
int ap_q15_slab8(const ap_plan *p, const float *const *rr, const float *const *ri,
                 const float *sc, int16_t *xr, int16_t *xi);
int ap_q15_screen_perm(const ap_plan *p, const int16_t *dr, const int16_t *di,
                       const int16_t *tr, const int16_t *ti, long tw, const int16_t *dsel,
                       const int16_t *tsel, size_t start, size_t end, const int16_t *lanethr,
                       uint64_t *bits, int16_t *lanemax, void *scratch);
/* A partial lane group's tile, at any N ap_q15_screen takes (ap_q15_has_tile). dq has QW/T
   consecutive [N][3] blocks; tr/ti retain stride QW and contain at least T lanes from the
   selected offset. Output lane b*T+l is data block b, template l. */
int ap_q15_screen_tile(const ap_plan *p, int T, const int16_t *dq,
                       const int16_t *tr, const int16_t *ti, size_t start, size_t end,
                       const int16_t *lanethr, uint64_t *bits, int16_t *lanemax, void *scratch);

#endif
