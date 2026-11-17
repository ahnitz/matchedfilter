/* The gate model's simulation (gatechain._simulate, _core.simulate): the kernel, without
   Python. The binding parses and checks the arguments, fills an ap_sim, and calls
   ap_sim_setup (plans and buffers), ap_sim_run (the rows; it needs no interpreter) and
   ap_sim_free. */
#ifndef AP_SIMULATE_H
#define AP_SIMULATE_H
#include <stddef.h>
#include <stdint.h>
#include "transform.h"

/* One statistic's running-maximum records: pos, val of cap entries, off (nrows + 1). */
typedef struct { int32_t *pos; float *val; long long *off; long long cap; } ap_sim_out;

typedef struct {
  /* the call: see M_simulate in _core.c for what each array holds */
  const float *scale; long long n, kmax, row0, nrows; uint64_t seed; long long nb;
  long long b[32], k0[32], khi[32], max_band_hi; float bs[32], al[32], be[32];
  int any_k0, any_alpha; double fscale, keep_at;
  const float *tab; const long long *t; const int *fi;   /* the signal, or tab NULL */
  const unsigned char *km;                               /* kept rows, or NULL */
  ap_sim_out *sig, *noise;                               /* NULL when not asked for */
  /* work, made by ap_sim_setup */
  long long kfill, nh, max_alpha_hi; int half_split, share_widest, ph_w;
  ap_plan *pf, *ph_own, *ph, *pl[32];
  float *X, *Xorth, *Xw, *Y, *A, *Yhalf, *Yodd, *Xtw, *tw;
  size_t xfloats, xorth_floats, xwfloats, yhfloats;
  /* results: records per statistic, and the rows done */
  long long ks[64], kn[32], done;
} ap_sim;

/* Plans and buffers for sim, which must be zeroed and filled with the call. 0, or -1 when
   a plan or a buffer could not be made (ap_sim_free still frees what was made). */
int ap_sim_setup(ap_sim *sim);
/* Every row, until done == nrows or a record array is full (see M_simulate). */
void ap_sim_run(ap_sim *sim);
void ap_sim_free(ap_sim *sim);

#endif
