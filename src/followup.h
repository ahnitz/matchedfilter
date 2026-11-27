/* The single-template steps of the time-domain banks (_core.HMFTable's single steps): the
   job record a run fills per bound call, the plan and scratch pools, and the kernel, which
   lays out each job's blocks, correlates (time-domain or by transforms), bins, merges partial
   window bins and compacts the peaks. Nothing here uses Python; the binding fills the jobs
   from a table's steps and a run's bound arguments, and builds the result. */
#ifndef AP_FOLLOWUP_H
#define AP_FOLLOWUP_H
#include <stddef.h>
#include <stdint.h>
#include "matchedfilter.h"
#include "transform.h"

typedef struct {
  int64_t single_w[2];
  const float *ser_f;
  size_t cser_floats;
  int s_kind;
  int64_t S;
  const int64_t *W;
  size_t nw;
  size_t n;
  int64_t step;
  int64_t c_bad;
  size_t bs;
  int aligned;
  float thr;
  uint32_t thr_bits;
  int rate_one;
  int L;
  int tr_cplx;
  const float *tr;
  const float *ti;
  float *spec;
  int spec_ready;
  int64_t global_ti;
  size_t nblocks;
  uint64_t total_lags;
  int mode_td;
  int any_ph;
  size_t blk0;
  size_t pk_off;
  size_t pk_cnt;
  size_t hit_off;
  size_t hit_cnt;
} TdJob;

typedef struct {
  int64_t ts;
  size_t ws, we;
  uint32_t ph;
  size_t nb;
  size_t win_id;
  size_t pk_dst;
} TdBlk;

typedef struct {
  size_t nb;
  size_t idx;
} TdBlkOrd;

typedef struct {
  size_t n;
  size_t job_idx;
} TdNGroup;

typedef struct TdFollowupPlan TdFollowupPlan;

typedef struct {
  int busy;
  int temp;
  TdJob *jobs;
  size_t jobs_cap;
  TdBlk *blks;
  size_t blks_cap;
  TdNGroup *ngroups;
  size_t *jidx;
  size_t ng_cap;
  ap_peak *peaks;
  size_t peaks_cap;
  size_t *ord;
  size_t ord_cap;
  struct TdFwdReq *reqs;
  struct TdFftEntry *ents;
  size_t *u_first;
  size_t e_cap;
  float **seen_specs;
  size_t specs_cap;
  float *made_specs;     /* template spectra made without a store slot (td_bscr_spectra) */
  size_t made_cap;
} TdBatchScratch;

/* The batch scratch, from a pool of one (a second caller at once gets a temporary). */
TdBatchScratch *td_bscr_acquire(void);
void td_bscr_release(TdBatchScratch *ws);
/* Grow *ptr to hold want elements of elem_sz bytes (0, or -1 when out of memory). */
int td_grow_raw(void **ptr, size_t *cap, size_t want, size_t elem_sz);
int cmp_blk_ord(const void *a, const void *b);
/* Every job's blocks, by length group, then each job's peaks compacted into the output
   arrays (offs nj + 1; ready nj; per peak its sample, snr pair and block start) with
   partial window bins merged. Returns 0, or -1 when a plan or buffer could not be made. */
int td_followup_run(TdBatchScratch *ws, TdJob *jobs, size_t nj, TdNGroup *ngroups,
                    size_t *jidx_buf, TdBlk *blks, size_t total_blks, ap_peak *all_peaks,
                    size_t *ord_scratch, int64_t *offs_p, unsigned char *rdy_p,
                    int64_t *si_base, float *snr_base, int64_t *bs_base, size_t *total_kept);
/* count template spectra of n bins in the scratch (64-byte aligned), or NULL. */
float *td_bscr_spectra(TdBatchScratch *ws, size_t count, size_t n);
/* Lay out the jobs (their input fields set: series, windows, block geometry, bins, threshold,
   template) and run them (td_followup_run): offs (nj + 1) and, in one block allocated here
   that the caller frees (free(*si)), per kept peak its sample, snr pair and block start. 0, or -1 when a plan
   or buffer could not be made. */
int td_followup_exec(TdBatchScratch *ws, TdJob *jobs, size_t nj, int64_t *offs,
                     int64_t **si, float **snr, int64_t **bs, size_t *total_kept);

#endif
