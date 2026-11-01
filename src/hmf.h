#ifndef AP_HMF_H
#define AP_HMF_H
/* Internal batch sparse series interface between src/hmf.c and _core.c. */

#include <stddef.h>
#include <stdint.h>
#include "matchedfilter.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
  ap_hmf_plan *p;
  const float *series;
  size_t nseries;
  const size_t *start;
  const size_t *win_start;
  const size_t *win_end;
  const unsigned *bin_phase;
  int nblocks;
  int t0, nt;
  size_t binsize;
  float threshold;
  int *counts;         /* optional [nblocks * nt] crossing counts, or NULL */
  int cluster_id;      /* jobs with equal adjacent cluster_id co-execute in L2 lockstep */
  int64_t *out_flat;
  int64_t *out_idx;
  float *out_val;      /* 2 * out_count interleaved (re, im) floats */
  size_t out_count;
  int total;
} ap_hmf_sparse_job;

int ap_hmf_run_series_batch_sparse(ap_hmf_sparse_job *jobs, int njobs);

#ifdef __cplusplus
}
#endif
#endif
