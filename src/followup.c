/* The follow-up batch kernel: see followup.h. Moved from _core.c unchanged but for the
   pools' lock (a pthread mutex, as matchfilt.c's) and the job record's Python buffers,
   which the binding keeps beside it. */
#include <math.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include "followup.h"
#include "alloc.h"
#include "q15.h"

typedef struct TdFwdReq {
  const float *ser_f;
  int s_kind;
  int64_t S;
  size_t cser_floats;
  size_t s0;
  size_t entry_idx;
} TdFwdReq;

typedef struct TdFftEntry {
  size_t d_idx;
  size_t t_idx;
  size_t bs;
  uint32_t thr_bits;
  float thr;
  size_t ws, we;
  uint32_t ph;
  size_t nb;
  size_t pk_dst;
  size_t orig;
} TdFftEntry;

struct TdFollowupPlan {
  size_t n;
  const char *isa;
  int busy;
  int temp;
  ap_plan *fft;
  int n1, n2, w, gmajor;
  ap_plan *half_fft;
  float *rtw;
  ap_plan *pb_fwd_c;
  ap_plan *pb_fwd_r;
  ap_plan *pb_bwd;
  int w_f_c, w_f_r, w_bwd;
  float *bspec, *bprod;
  float *sfwd, *sspec, *pr, *pi;
  float *fdr, *fdi;
  size_t d_cap;
  float *ftr, *fti;
  size_t t_cap;
  ap_peak *pkbuf;
  size_t pk_cap;
  float *td_x, *td_out;
  size_t td_x_cap, td_out_cap;
};

int ap_binmax_prod_gather_lanes_peaks(ap_plan *p, const float *const *drp, const float *const *dip,
                                      const float *const *trp, const float *const *tip, int nlane,
                                      size_t binsize, float threshold, ap_peak *peaks,
                                      int sign, size_t start, size_t end, const unsigned *ph);

#define TD_FP_SLOTS 16
static TdFollowupPlan td_fp_tab[TD_FP_SLOTS];
static pthread_mutex_t td_fp_lock = PTHREAD_MUTEX_INITIALIZER;   /* both pools */

static void td_fp_free_contents(TdFollowupPlan *fp){
  if(!fp) return;
  if(fp->pb_fwd_c) ap_destroy(fp->pb_fwd_c);
  if(fp->pb_fwd_r) ap_destroy(fp->pb_fwd_r);
  if(fp->half_fft) ap_destroy(fp->half_fft);
  if(fp->fft) ap_destroy(fp->fft);
  free(fp->rtw);
  free(fp->bspec); free(fp->bprod);
  free(fp->sfwd); free(fp->sspec); free(fp->pr); free(fp->pi);
  free(fp->fdr); free(fp->fdi);
  free(fp->ftr); free(fp->fti);
  free(fp->pkbuf);
  free(fp->td_x); free(fp->td_out);
  memset(fp, 0, sizeof(*fp));
}

static int td_fp_init(TdFollowupPlan *fp, size_t n, const char *isa, int temp){
  memset(fp, 0, sizeof(*fp));
  fp->n = n;
  fp->isa = isa;
  fp->busy = 1;
  fp->temp = temp;
  fp->fft = ap_create(n);
  if(!fp->fft){ td_fp_free_contents(fp); return -1; }
  if(!ap_plan_split(fp->fft, &fp->n1, &fp->n2)){ fp->n1 = 0; fp->n2 = 0; }
  fp->w = ap_plan_lanes(fp->fft);
  fp->gmajor = (fp->w > 0 && fp->n1 > 0 && fp->n1 % fp->w == 0
                && (size_t)fp->n1 * (size_t)fp->n2 == n && ap_has_fused_prod(fp->fft)) ? 1 : 0;
  if(n >= 4 && ap_supported(n / 2)){
    const size_t h = n / 2;
    fp->half_fft = ap_create_like(fp->fft, h);
    fp->rtw = (float*)malloc(2 * (h + 1) * sizeof(float));
    if(!fp->half_fft || !fp->rtw){ td_fp_free_contents(fp); return -1; }
    for(size_t k = 0; k <= h; k++){
      const double a = 2.0 * 3.14159265358979323846 * (double)k / (double)n;
      fp->rtw[2 * k] = (float)cos(a);
      fp->rtw[2 * k + 1] = (float)sin(a);
    }
  }
  const size_t pb_lim = fp->w >= 16 ? 2048u : 512u;
  if(n >= 64 && n <= pb_lim){
    fp->pb_fwd_c = ap_create_pairbatch_like(fp->fft, n);
    fp->w_f_c = fp->pb_fwd_c ? ap_plan_lanes(fp->pb_fwd_c) : 0;
  }
  if(n / 2 >= 64 && n / 2 <= pb_lim){
    fp->pb_fwd_r = ap_create_pairbatch_like(fp->fft, n / 2);
    fp->w_f_r = fp->pb_fwd_r ? ap_plan_lanes(fp->pb_fwd_r) : 0;
  }
  if(ap_plan_pairbatch(fp->fft) > 0){
    fp->pb_bwd = fp->fft;
    fp->w_bwd = ap_plan_lanes(fp->fft);
  } else if(fp->pb_fwd_c){
    fp->pb_bwd = fp->pb_fwd_c;
    fp->w_bwd = fp->w_f_c;
  }
  fp->bspec = (float*)ap_alloc64((size_t)AP_MAX_LANES * 2 * n * sizeof(float));
  fp->bprod = (float*)ap_alloc64((size_t)AP_MAX_LANES * 2 * n * sizeof(float));
  fp->sfwd = (float*)ap_alloc64(2 * n * sizeof(float));
  fp->sspec = (float*)ap_alloc64(2 * n * sizeof(float));
  fp->pr = (float*)ap_alloc64(n * sizeof(float));
  fp->pi = (float*)ap_alloc64(n * sizeof(float));
  if(!fp->bspec || !fp->bprod || !fp->sfwd || !fp->sspec || !fp->pr || !fp->pi){
    td_fp_free_contents(fp);
    return -1;
  }
  return 0;
}

static TdFollowupPlan *td_fp_acquire(size_t n){
  const char *isa = ap_isa();
  pthread_mutex_lock(&td_fp_lock);
  int free_idx = -1;
  for(int i = 0; i < TD_FP_SLOTS; i++){
    if(td_fp_tab[i].fft && td_fp_tab[i].n == n && td_fp_tab[i].isa == isa && !td_fp_tab[i].busy){
      td_fp_tab[i].busy = 1;
      pthread_mutex_unlock(&td_fp_lock);
      return &td_fp_tab[i];
    }
    if(free_idx < 0 && !td_fp_tab[i].busy && !td_fp_tab[i].fft) free_idx = i;
  }
  if(free_idx < 0){
    for(int i = 0; i < TD_FP_SLOTS; i++){
      if(!td_fp_tab[i].busy){
        td_fp_free_contents(&td_fp_tab[i]);
        free_idx = i;
        break;
      }
    }
  }
  if(free_idx >= 0){
    td_fp_tab[free_idx].busy = 1;
    pthread_mutex_unlock(&td_fp_lock);
    if(td_fp_init(&td_fp_tab[free_idx], n, isa, 0) < 0){
      pthread_mutex_lock(&td_fp_lock);
      td_fp_tab[free_idx].busy = 0;
      pthread_mutex_unlock(&td_fp_lock);
      return NULL;
    }
    return &td_fp_tab[free_idx];
  }
  pthread_mutex_unlock(&td_fp_lock);
  TdFollowupPlan *tmp = (TdFollowupPlan*)calloc(1, sizeof(*tmp));
  if(!tmp) return NULL;
  if(td_fp_init(tmp, n, isa, 1) < 0){ free(tmp); return NULL; }
  return tmp;
}

static void td_fp_release(TdFollowupPlan *fp){
  if(!fp) return;
  if(fp->temp){
    td_fp_free_contents(fp);
    free(fp);
    return;
  }
  pthread_mutex_lock(&td_fp_lock);
  fp->busy = 0;
  pthread_mutex_unlock(&td_fp_lock);
}

static int td_fp_reserve_pair(float **a, float **b, size_t *cap, size_t want, size_t n){
  if(*cap >= want && *a && *b) return 0;
  size_t nc = *cap ? *cap : 64u;
  while(nc < want) nc *= 2u;
  float *na = (float*)ap_alloc64(nc * n * sizeof(float));
  float *nb = (float*)ap_alloc64(nc * n * sizeof(float));
  if(!na || !nb){ free(na); free(nb); return -1; }
  free(*a); free(*b);
  *a = na; *b = nb; *cap = nc;
  return 0;
}

static int td_fp_reserve_floats(float **buf, size_t *cap, size_t want){
  if(*cap >= want && *buf) return 0;
  size_t nc = *cap ? *cap : 4096u;
  while(nc < want) nc *= 2u;
  float *nb = (float*)ap_alloc64(nc * sizeof(float));
  if(!nb) return -1;
  free(*buf);
  *buf = nb;
  *cap = nc;
  return 0;
}

static int td_fp_reserve_peaks(ap_peak **buf, size_t *cap, size_t want){
  if(*cap >= want && *buf) return 0;
  size_t nc = *cap ? *cap : 512u;
  while(nc < want) nc *= 2u;
  ap_peak *nb = (ap_peak*)ap_alloc64(nc * sizeof(ap_peak));
  if(!nb) return -1;
  free(*buf);
  *buf = nb;
  *cap = nc;
  return 0;
}

static void td_mulspec(const float *ar, const float *ai, const float *br, const float *bi,
                       float *or_, float *oi, size_t n){
  for(size_t k = 0; k < n; k++){
    const float x = ar[k], y = ai[k], u = br[k], v = bi[k];
    or_[k] = x * u - y * v;
    oi[k] = -(x * v + y * u);
  }
}

int cmp_blk_ord(const void *a, const void *b){
  const TdBlkOrd *x = (const TdBlkOrd*)a, *y = (const TdBlkOrd*)b;
  if(x->nb != y->nb) return x->nb < y->nb ? -1 : 1;
  return x->idx < y->idx ? -1 : (x->idx > y->idx ? 1 : 0);
}

static int cmp_fwd_req(const void *a, const void *b){
  const TdFwdReq *x = (const TdFwdReq*)a, *y = (const TdFwdReq*)b;
  if(x->s_kind != y->s_kind) return x->s_kind < y->s_kind ? -1 : 1;
  if(x->ser_f != y->ser_f) return (uintptr_t)x->ser_f < (uintptr_t)y->ser_f ? -1 : 1;
  if(x->S != y->S) return x->S < y->S ? -1 : 1;
  if(x->s0 != y->s0) return x->s0 < y->s0 ? -1 : 1;
  return x->entry_idx < y->entry_idx ? -1 : (x->entry_idx > y->entry_idx ? 1 : 0);
}

static int cmp_fft_entry(const void *a, const void *b){
  const TdFftEntry *x = (const TdFftEntry*)a, *y = (const TdFftEntry*)b;
  if(x->bs != y->bs) return x->bs < y->bs ? -1 : 1;
  if(x->thr_bits != y->thr_bits) return x->thr_bits < y->thr_bits ? -1 : 1;
  if(x->ws != y->ws) return x->ws < y->ws ? -1 : 1;
  if(x->we != y->we) return x->we < y->we ? -1 : 1;
  if(x->nb != y->nb) return x->nb < y->nb ? -1 : 1;
  if(x->d_idx != y->d_idx) return x->d_idx < y->d_idx ? -1 : 1;
  if(x->t_idx != y->t_idx) return x->t_idx < y->t_idx ? -1 : 1;
  return x->orig < y->orig ? -1 : (x->orig > y->orig ? 1 : 0);
}

static TdBatchScratch td_bscr;

static void td_bscr_free(TdBatchScratch *ws){
  if(!ws) return;
  free(ws->jobs);
  free(ws->blks);
  free(ws->ngroups);
  free(ws->jidx);
  free(ws->peaks);
  free(ws->ord);
  free(ws->reqs);
  free(ws->ents);
  free(ws->u_first);
  free(ws->seen_specs);
  free(ws->bufs);
  memset(ws, 0, sizeof(*ws));
}

TdBatchScratch *td_bscr_acquire(void){
  pthread_mutex_lock(&td_fp_lock);
  if(!td_bscr.busy){
    td_bscr.busy = 1;
    td_bscr.temp = 0;
    pthread_mutex_unlock(&td_fp_lock);
    return &td_bscr;
  }
  pthread_mutex_unlock(&td_fp_lock);
  TdBatchScratch *tmp = (TdBatchScratch*)calloc(1, sizeof(*tmp));
  if(tmp){ tmp->busy = 1; tmp->temp = 1; }
  return tmp;
}

void td_bscr_release(TdBatchScratch *ws){
  if(!ws) return;
  if(ws->temp){
    td_bscr_free(ws);
    free(ws);
    return;
  }
  pthread_mutex_lock(&td_fp_lock);
  ws->busy = 0;
  pthread_mutex_unlock(&td_fp_lock);
}

int td_grow_raw(void **ptr, size_t *cap, size_t want, size_t elem_sz){
  if(*cap >= want && *ptr) return 0;
  size_t nc = *cap ? *cap : 64u;
  while(nc < want) nc *= 2u;
  void *np = malloc(nc * elem_sz);
  if(!np) return -1;
  free(*ptr);
  *ptr = np;
  *cap = nc;
  return 0;
}

static int cmp_ngroup(const void *a, const void *b){
  const TdNGroup *x = (const TdNGroup*)a, *y = (const TdNGroup*)b;
  if(x->n != y->n) return x->n < y->n ? -1 : 1;
  return x->job_idx < y->job_idx ? -1 : (x->job_idx > y->job_idx ? 1 : 0);
}

static void td_roll_taps(float *in_buf, const float *tr, const float *ti, int tr_cplx,
                         int L, size_t n){
  memset(in_buf, 0, 2 * n * sizeof(float));
  if(L <= 0) return;
  const size_t cnt = (size_t)L <= n ? (size_t)L : n;
  const size_t half = cnt / 2;
  if(tr_cplx){
    memcpy(in_buf, tr + 2 * half, 2 * (cnt - half) * sizeof(float));
    if(half) memcpy(in_buf + 2 * (n - half), tr, 2 * half * sizeof(float));
  } else if(ti){
    for(size_t i = 0; i < cnt - half; i++){
      in_buf[2 * i] = tr[half + i];
      in_buf[2 * i + 1] = -ti[half + i];
    }
    for(size_t i = 0; i < half; i++){
      in_buf[2 * (n - half + i)] = tr[i];
      in_buf[2 * (n - half + i) + 1] = -ti[i];
    }
  } else {
    for(size_t i = 0; i < cnt - half; i++) in_buf[2 * i] = tr[half + i];
    for(size_t i = 0; i < half; i++) in_buf[2 * (n - half + i)] = tr[i];
  }
}

static int td_run_n_group(TdFollowupPlan *fp, TdBatchScratch *ws, TdJob *jobs,
                          const size_t *jidx, size_t nj, TdBlk *blks, ap_peak *all_peaks){
  const size_t n = fp->n;
  const float inv_n = 1.0f / (float)n;

  /* 1. Execute narrow-window Direct TD SIMD jobs for this block length n. */
  for(size_t jj = 0; jj < nj; jj++){
    TdJob *jb = &jobs[jidx[jj]];
    if(!jb->mode_td || jb->nblocks == 0) continue;
    if(td_fp_reserve_floats(&fp->td_out, &fp->td_out_cap, 2 * (size_t)jb->total_lags) < 0) return -1;
    const float *tr_td = jb->tr;
    const float *ti_td = jb->ti;
    if(jb->tr_cplx){
      for(int k = 0; k < jb->L; k++){
        fp->pr[k] = jb->tr[2 * k];
        fp->pi[k] = -jb->tr[2 * k + 1];
      }
      tr_td = fp->pr;
      ti_td = fp->pi;
    }

    size_t lag_cursor = 0;
    size_t b_cursor = jb->blk0;
    for(size_t w = 0; w < jb->nw; w++){
      const int64_t v0 = jb->W[2 * w], v1 = jb->W[2 * w + 1];
      const int64_t fidx = v0 > jb->c_bad ? (v0 - jb->c_bad) / jb->step : 0;
      const int64_t fts = fidx * jb->step;
      const int64_t lim = jb->S < (v1 - jb->c_bad) ? jb->S : (v1 - jb->c_bad);
      if(fts >= lim) continue;
      const int64_t nblk_w = (lim - 1 - fts) / jb->step + 1;
      const int64_t lts = fts + (nblk_w - 1) * jb->step;
      const int64_t rs0 = v0 > (fts + jb->c_bad) ? v0 : (fts + jb->c_bad);
      const int64_t re_last = v1 < (lts + jb->c_bad + jb->step) ? v1 : (lts + jb->c_bad + jb->step);
      const int nlag = (int)(re_last - rs0);
      if(nlag > 0){
        const int c = jb->L / 2;
        const size_t x0 = (size_t)(rs0 - (int64_t)c);
        const size_t need = (size_t)nlag + (size_t)jb->L - 1u;
        const size_t have = x0 < (size_t)jb->S
            ? ((size_t)jb->S - x0 < need ? (size_t)jb->S - x0 : need) : 0u;
        float *dout = fp->td_out + 2 * lag_cursor;
        if(jb->s_kind == 0){
          if(have == need){
            ap_td_corr_ex_on(fp->fft, jb->ser_f + 2 * x0, 0, tr_td, ti_td, jb->L, nlag, dout);
          } else {
            if(td_fp_reserve_floats(&fp->td_x, &fp->td_x_cap, 2 * need) < 0) return -1;
            if(have) memcpy(fp->td_x, jb->ser_f + 2 * x0, 2 * have * sizeof(float));
            memset(fp->td_x + 2 * have, 0, 2 * (need - have) * sizeof(float));
            ap_td_corr_ex_on(fp->fft, fp->td_x, 0, tr_td, ti_td, jb->L, nlag, dout);
          }
        } else if(jb->s_kind == 1 && have == need){
          ap_td_corr_ex_on(fp->fft, jb->ser_f + x0, 1, tr_td, ti_td, jb->L, nlag, dout);
        } else {
          if(td_fp_reserve_floats(&fp->td_x, &fp->td_x_cap, need) < 0) return -1;
          const size_t st = jb->s_kind == 2 ? 2u : 1u;
          ap_scale_load_on(fp->fft, fp->td_x, have ? jb->ser_f + x0 * st : jb->ser_f,
                           have, need, st, 1.0f);
          ap_td_corr_ex_on(fp->fft, fp->td_x, 1, tr_td, ti_td, jb->L, nlag, dout);
        }
      }
      const float t2 = jb->thr > 0.f ? jb->thr * jb->thr : 0.f;
      for(int64_t bi = 0; bi < nblk_w; bi++, b_cursor++){
        const TdBlk *bk = &blks[b_cursor];
        ap_peak *dst = all_peaks + bk->pk_dst;
        for(size_t q = 0; q < bk->nb; q++) dst[q] = (ap_peak){-1, 0.f, 0.f, t2};
        const float *wout = fp->td_out + 2 * lag_cursor;
        for(size_t kr = bk->ws; kr < bk->we; kr++){
          const size_t off = (size_t)((bk->ts + (int64_t)kr) - rs0);
          const float re = wout[2 * off], im = wout[2 * off + 1];
          const float m2 = re * re + im * im;
          const size_t bj = ((kr - bk->ws) + (size_t)bk->ph) / jb->bs;
          if(m2 > dst[bj].magnitude){
            dst[bj].magnitude = m2;
            dst[bj].index = (long)kr;
            dst[bj].re = re;
            dst[bj].im = im;
          }
        }
      }
      lag_cursor += (size_t)(nlag > 0 ? nlag : 0);
    }
  }

  /* 2. Collect all Mode 0 (FFT) jobs & block entries for this block length n. */
  size_t n_fft_jobs = 0, total_e = 0;
  for(size_t jj = 0; jj < nj; jj++){
    TdJob *jb = &jobs[jidx[jj]];
    if(!jb->mode_td && jb->nblocks > 0){
      n_fft_jobs++;
      total_e += jb->nblocks;
    }
  }
  if(total_e == 0) return 0;

  if(total_e > ws->e_cap || !ws->reqs || !ws->ents || !ws->u_first){
    size_t nc = ws->e_cap ? ws->e_cap : 256u;
    while(nc < total_e) nc *= 2u;
    TdFwdReq *nr = (TdFwdReq*)malloc(nc * sizeof(TdFwdReq));
    TdFftEntry *ne = (TdFftEntry*)malloc(nc * sizeof(TdFftEntry));
    size_t *nu = (size_t*)malloc(nc * sizeof(size_t));
    if(!nr || !ne || !nu){ free(nr); free(ne); free(nu); return -1; }
    free(ws->reqs); free(ws->ents); free(ws->u_first);
    ws->reqs = nr; ws->ents = ne; ws->u_first = nu; ws->e_cap = nc;
  }
  if(td_grow_raw((void**)&ws->seen_specs, &ws->specs_cap, n_fft_jobs, sizeof(float*)) < 0) return -1;
  TdFwdReq *reqs = ws->reqs;
  TdFftEntry *ents = ws->ents;
  size_t *u_first = ws->u_first;
  float **seen_specs = ws->seen_specs;

  if(td_fp_reserve_pair(&fp->ftr, &fp->fti, &fp->t_cap, n_fft_jobs, n) < 0) return -1;

  const int use_pb = (fp->pb_bwd != NULL && fp->w_bwd > 0);
  const int gm_n1 = (!use_pb && fp->gmajor) ? fp->n1 : 0;
  size_t t_cursor = 0, e_cursor = 0, n_unready = 0;
  for(size_t jj = 0; jj < nj; jj++){
    TdJob *jb = &jobs[jidx[jj]];
    if(jb->mode_td || jb->nblocks == 0) continue;
    size_t t_slot = (size_t)-1;
    for(size_t prev = 0; prev < t_cursor; prev++){
      if(seen_specs[prev] == jb->spec){ t_slot = prev; break; }
    }
    if(t_slot == (size_t)-1){
      t_slot = t_cursor++;
      seen_specs[t_slot] = jb->spec;
      if(!jb->spec_ready){
        u_first[n_unready++] = jidx[jj];
        jb->spec_ready = 1;
      } else {
        ap_split_store_on(fp->fft, jb->spec, fp->ftr + t_slot * n, fp->fti + t_slot * n,
                          n, 1, gm_n1, fp->n2, fp->w);
      }
    } else {
      jb->spec_ready = 1;
    }
    for(size_t b = 0; b < jb->nblocks; b++){
      const TdBlk *bk = &blks[jb->blk0 + b];
      reqs[e_cursor] = (TdFwdReq){
        jb->ser_f, jb->s_kind, jb->S, jb->cser_floats, (size_t)bk->ts, e_cursor
      };
      ents[e_cursor] = (TdFftEntry){
        0, t_slot, jb->bs, jb->thr_bits, jb->thr,
        bk->ws, bk->we, bk->ph, bk->nb, bk->pk_dst, e_cursor
      };
      e_cursor++;
    }
  }

  /* Batch-transform unready template tap rows across SIMD lanes before split_store. */
  if(n_unready > 0){
    const int Wt = (fp->pb_fwd_c && fp->w_f_c > 0) ? fp->w_f_c : 0;
    size_t u0 = 0;
    while(Wt > 0 && u0 < n_unready){
      const int bcnt = (n_unready - u0 < (size_t)Wt) ? (int)(n_unready - u0) : Wt;
      const float *srcs[AP_MAX_LANES];
      size_t haves_n[AP_MAX_LANES];
      float *outs[AP_MAX_LANES];
      for(int l = 0; l < bcnt; l++){
        const TdJob *jb = &jobs[u_first[u0 + (size_t)l]];
        float *in_b = fp->bprod + (size_t)l * 2 * n;
        td_roll_taps(in_b, jb->tr, jb->ti, jb->tr_cplx, jb->L, n);
        srcs[l] = in_b;
        haves_n[l] = n;
        outs[l] = jb->spec;
      }
      if(ap_fft_forward_batch(fp->pb_fwd_c, srcs, haves_n, bcnt, 1.0f, outs) < 0) break;
      for(int l = 0; l < bcnt; l++){
        const TdJob *jb = &jobs[u_first[u0 + (size_t)l]];
        for(size_t s = 0; s < t_cursor; s++){
          if(seen_specs[s] == jb->spec){
            ap_split_store_on(fp->fft, jb->spec, fp->ftr + s * n, fp->fti + s * n,
                              n, 1, gm_n1, fp->n2, fp->w);
            break;
          }
        }
      }
      u0 += (size_t)bcnt;
    }
    for(; u0 < n_unready; u0++){
      const TdJob *jb = &jobs[u_first[u0]];
      td_roll_taps(fp->sfwd, jb->tr, jb->ti, jb->tr_cplx, jb->L, n);
      ap_fft(fp->fft, fp->sfwd, jb->spec, AP_FORWARD);
      for(size_t s = 0; s < t_cursor; s++){
        if(seen_specs[s] == jb->spec){
          ap_split_store_on(fp->fft, jb->spec, fp->ftr + s * n, fp->fti + s * n,
                            n, 1, gm_n1, fp->n2, fp->w);
          break;
        }
      }
    }
  }

  /* 3. Deduplicate unique data blocks and batch forward FFTs across SIMD lanes. */
  qsort(reqs, total_e, sizeof(TdFwdReq), cmp_fwd_req);
  size_t n_uniq = 0;
  for(size_t i = 0; i < total_e; i++){
    if(i == 0 || reqs[i].ser_f != reqs[i - 1].ser_f || reqs[i].s_kind != reqs[i - 1].s_kind
       || reqs[i].S != reqs[i - 1].S || reqs[i].s0 != reqs[i - 1].s0){
      u_first[n_uniq++] = i;
    }
    ents[reqs[i].entry_idx].d_idx = n_uniq - 1;
  }

  if(td_fp_reserve_pair(&fp->fdr, &fp->fdi, &fp->d_cap, n_uniq, n) < 0) return -1;

  static const float zero_f[2] = {0.f, 0.f};
  for(size_t u = 0; u < n_uniq;){
    const TdFwdReq *r0 = &reqs[u_first[u]];
    const int sk = r0->s_kind;
    if((sk == 1 || sk == 2) && fp->pb_fwd_r && fp->w_f_r > 0){
      const int W = fp->w_f_r;
      const size_t st = (size_t)sk;
      const float *srcs[AP_MAX_LANES];
      size_t haves[AP_MAX_LANES];
      float *outs[AP_MAX_LANES];
      size_t d_ids[AP_MAX_LANES];
      int cnt = 0;
      while(cnt < W && u < n_uniq){
        const TdFwdReq *ru = &reqs[u_first[u]];
        if(ru->s_kind != sk) break;
        if(sk == 2 && 2 * (ru->s0 + n) > ru->cser_floats) break;
        const size_t hv = ru->s0 < (size_t)ru->S
            ? ((size_t)ru->S - ru->s0 < n ? (size_t)ru->S - ru->s0 : n) : 0u;
        srcs[cnt] = hv ? ru->ser_f + ru->s0 * st : zero_f;
        haves[cnt] = hv;
        outs[cnt] = fp->bspec + (size_t)cnt * 2 * n;
        d_ids[cnt] = u;
        cnt++;
        u++;
      }
      if(cnt > 0){
        if(ap_fft_real_batch(fp->pb_fwd_r, srcs, haves, st, cnt, inv_n, fp->rtw, 1, outs) < 0){
          return -1;
        }
        for(int l = 0; l < cnt; l++){
          ap_split_store_on(fp->fft, outs[l], fp->fdr + d_ids[l] * n, fp->fdi + d_ids[l] * n,
                            n, 0, gm_n1, fp->n2, fp->w);
        }
        continue;
      }
    } else if(sk == 0 && fp->pb_fwd_c && fp->w_f_c > 0){
      const int W = fp->w_f_c;
      const float *srcs[AP_MAX_LANES];
      size_t haves[AP_MAX_LANES];
      float *outs[AP_MAX_LANES];
      size_t d_ids[AP_MAX_LANES];
      int cnt = 0;
      while(cnt < W && u < n_uniq){
        const TdFwdReq *ru = &reqs[u_first[u]];
        if(ru->s_kind != 0) break;
        const size_t hv = ru->s0 < (size_t)ru->S
            ? ((size_t)ru->S - ru->s0 < n ? (size_t)ru->S - ru->s0 : n) : 0u;
        srcs[cnt] = hv ? ru->ser_f + 2 * ru->s0 : zero_f;
        haves[cnt] = hv;
        outs[cnt] = fp->bspec + (size_t)cnt * 2 * n;
        d_ids[cnt] = u;
        cnt++;
        u++;
      }
      if(ap_fft_forward_batch(fp->pb_fwd_c, srcs, haves, cnt, inv_n, outs) < 0) return -1;
      for(int l = 0; l < cnt; l++){
        ap_split_store_on(fp->fft, outs[l], fp->fdr + d_ids[l] * n, fp->fdi + d_ids[l] * n,
                          n, 0, gm_n1, fp->n2, fp->w);
      }
      continue;
    }

    /* Single-block forward transform fallback (large n or page-edge stride-2 real block). */
    const size_t hv = r0->s0 < (size_t)r0->S
        ? ((size_t)r0->S - r0->s0 < n ? (size_t)r0->S - r0->s0 : n) : 0u;
    float *dr_u = fp->fdr + u * n, *di_u = fp->fdi + u * n;
    if((sk == 1 || sk == 2) && fp->half_fft){
      const size_t st = (size_t)sk;
      ap_fft_forward_scaled(fp->half_fft, hv ? r0->ser_f + r0->s0 * st : zero_f,
                            hv, st, inv_n, fp->sfwd);
      ap_real_split_on(fp->fft, fp->sfwd, fp->rtw, n, fp->sspec);
      ap_split_store_on(fp->fft, fp->sspec, dr_u, di_u, n, 0, gm_n1, fp->n2, fp->w);
    } else if(sk == 0){
      if(gm_n1){
        ap_fft_forward_scaled_gm(fp->fft, hv ? r0->ser_f + 2 * r0->s0 : zero_f,
                                 2 * hv, 1, inv_n, dr_u, di_u, fp->sfwd);
      } else {
        ap_fft_forward_scaled(fp->fft, hv ? r0->ser_f + 2 * r0->s0 : zero_f,
                              2 * hv, 1, inv_n, fp->sfwd);
        ap_split_store_on(fp->fft, fp->sfwd, dr_u, di_u, n, 0, 0, fp->n2, fp->w);
      }
    } else {
      const size_t st = (size_t)sk;
      memset(fp->sfwd, 0, 2 * n * sizeof(float));
      for(size_t k = 0; k < hv; k++) fp->sfwd[2 * k] = r0->ser_f[(r0->s0 + k) * st] * inv_n;
      ap_fft(fp->fft, fp->sfwd, fp->sspec, AP_FORWARD);
      ap_split_store_on(fp->fft, fp->sspec, dr_u, di_u, n, 0, gm_n1, fp->n2, fp->w);
    }
    u++;
  }

  /* 4. Fused SIMD backward transform + binned peak scan across Mode 0 entries. */
  if(use_pb){
    qsort(ents, total_e, sizeof(TdFftEntry), cmp_fft_entry);
    const int W = fp->w_bwd;
    size_t n_rem = 0;
    for(size_t e0 = 0; e0 < total_e;){
      const TdFftEntry *eh = &ents[e0];
      const size_t nb0 = eh->nb;
      int cnt = 1;
      while(cnt < W && e0 + (size_t)cnt < total_e){
        const TdFftEntry *ec = &ents[e0 + (size_t)cnt];
        if(ec->bs != eh->bs || ec->thr_bits != eh->thr_bits
           || ec->ws != eh->ws || ec->we != eh->we || ec->nb != nb0) break;
        cnt++;
      }
      /* Defer ragged/edge blocks (unique [ws, we)) to a 16-lane backward FFT batch below. */
      if(cnt < 4){
        for(int l = 0; l < cnt; l++) u_first[n_rem++] = e0 + (size_t)l;
        e0 += (size_t)cnt;
        continue;
      }
      if(td_fp_reserve_peaks(&fp->pkbuf, &fp->pk_cap, (size_t)W * nb0) < 0) return -1;
      const float *drp[AP_MAX_LANES], *dip[AP_MAX_LANES];
      const float *trp[AP_MAX_LANES], *tip[AP_MAX_LANES];
      unsigned ph_arr[AP_MAX_LANES];
      int any_ph = 0;
      for(int l = 0; l < cnt; l++){
        const TdFftEntry *el = &ents[e0 + (size_t)l];
        drp[l] = fp->fdr + el->d_idx * n;
        dip[l] = fp->fdi + el->d_idx * n;
        trp[l] = fp->ftr + el->t_idx * n;
        tip[l] = fp->fti + el->t_idx * n;
        ph_arr[l] = (unsigned)el->ph;
        if(ph_arr[l]) any_ph = 1;
      }
      if(ap_binmax_prod_gather_lanes_peaks(
             fp->pb_bwd, drp, dip, trp, tip, cnt,
             eh->bs, eh->thr, fp->pkbuf, AP_BACKWARD, eh->ws, eh->we,
             any_ph ? ph_arr : NULL) >= 0){
        for(int l = 0; l < cnt; l++){
          memcpy(all_peaks + ents[e0 + (size_t)l].pk_dst,
                 fp->pkbuf + (size_t)l * nb0,
                 nb0 * sizeof(ap_peak));
        }
        e0 += (size_t)cnt;
        continue;
      }
      for(int l = 0; l < cnt; l++) u_first[n_rem++] = e0 + (size_t)l;
      e0 += (size_t)cnt;
    }

    /* Batch all ragged/edge blocks W-wide across SIMD lanes via ap_fft_backward_batch. */
    for(size_t r0 = 0; r0 < n_rem; r0 += (size_t)W){
      const int bcnt = (n_rem - r0 < (size_t)W) ? (int)(n_rem - r0) : W;
      const float *srcs[AP_MAX_LANES];
      float *outs[AP_MAX_LANES];
      for(int l = 0; l < bcnt; l++){
        const TdFftEntry *el = &ents[u_first[r0 + (size_t)l]];
        const float *dr = fp->fdr + el->d_idx * n, *di = fp->fdi + el->d_idx * n;
        const float *tr = fp->ftr + el->t_idx * n, *ti = fp->fti + el->t_idx * n;
        float *pout = fp->bprod + (size_t)l * 2 * n;
        for(size_t k = 0; k < n; k++){
          const float x = dr[k], y = di[k], u = tr[k], v = ti[k];
          pout[2 * k] = x * u - y * v;
          pout[2 * k + 1] = x * v + y * u;
        }
        srcs[l] = pout;
        outs[l] = fp->bspec + (size_t)l * 2 * n;
      }
      if(ap_fft_backward_batch(fp->pb_bwd, srcs, n, bcnt, outs) >= 0){
        for(int l = 0; l < bcnt; l++){
          const TdFftEntry *el = &ents[u_first[r0 + (size_t)l]];
          ap_peak *dst = all_peaks + el->pk_dst;
          const float t2 = el->thr > 0.f ? el->thr * el->thr : 0.f;
          for(size_t q = 0; q < el->nb; q++) dst[q] = (ap_peak){-1, 0.f, 0.f, t2};
          const float *wout = outs[l];
          for(size_t kr = el->ws; kr < el->we; kr++){
            const float re = wout[2 * kr], im = wout[2 * kr + 1];
            const float m2 = re * re + im * im;
            const size_t bj = ((kr - el->ws) + (size_t)el->ph) / el->bs;
            if(m2 > dst[bj].magnitude){
              dst[bj].magnitude = m2;
              dst[bj].index = (long)kr;
              dst[bj].re = re;
              dst[bj].im = im;
            }
          }
        }
        continue;
      }
      for(int l = 0; l < bcnt; l++){
        const TdFftEntry *el = &ents[u_first[r0 + (size_t)l]];
        td_mulspec(fp->fdr + el->d_idx * n, fp->fdi + el->d_idx * n,
                   fp->ftr + el->t_idx * n, fp->fti + el->t_idx * n,
                   fp->pr, fp->pi, n);
        int c_unused = 0;
        unsigned ph1 = (unsigned)el->ph;
        if(ap_binmax_split(fp->fft, fp->pr, fp->pi, el->bs, el->thr,
                           all_peaks + el->pk_dst, &c_unused,
                           AP_BACKWARD, el->ws, el->we, ph1 ? &ph1 : NULL) < 0){
          return -1;
        }
      }
    }
  } else {
    for(size_t e0 = 0; e0 < total_e; e0++){
      const TdFftEntry *el = &ents[e0];
      const float *dr = fp->fdr + el->d_idx * n, *di = fp->fdi + el->d_idx * n;
      const float *tr = fp->ftr + el->t_idx * n, *ti = fp->fti + el->t_idx * n;
      ap_peak *dst = all_peaks + el->pk_dst;
      unsigned ph1 = el->ph;
      const unsigned *php = ph1 ? &ph1 : NULL;
      const ap_prod_kernel prod = ap_plan_prod_kernel(fp->fft, el->thr);
      int r = (fp->gmajor && prod.run)
          ? prod.run(prod.context, dr, di, tr, ti, el->bs, el->thr, dst, 1, el->ws, el->we, php)
          : -1;
      if(r < 0){
        td_mulspec(dr, di, tr, ti, fp->pr, fp->pi, n);
        int c_unused = 0;
        r = ap_binmax_split(fp->fft, fp->pr, fp->pi, el->bs, el->thr, dst, &c_unused,
                            AP_BACKWARD, el->ws, el->we, php);
      }
      if(r < 0) return -1;
    }
  }
  return 0;
}

int td_followup_run(TdBatchScratch *ws, TdJob *jobs, size_t nj, TdNGroup *ngroups,
                    size_t *jidx_buf, TdBlk *blks, size_t total_blks, ap_peak *all_peaks,
                    size_t *ord_scratch, int64_t *offs_p, unsigned char *rdy_p,
                    int64_t *si_base, float *snr_base, int64_t *bs_base, size_t *total_kept_out){
  int run_err = 0;
  size_t total_kept = 0;
  if(nj > 0 && total_blks > 0){
    qsort(ngroups, nj, sizeof(TdNGroup), cmp_ngroup);
    for(size_t g0 = 0; g0 < nj;){
      const size_t n_cur = ngroups[g0].n;
      size_t g1 = g0;
      while(g1 < nj && ngroups[g1].n == n_cur){
        jidx_buf[g1 - g0] = ngroups[g1].job_idx;
        g1++;
      }
      TdFollowupPlan *fp = td_fp_acquire(n_cur);
      if(!fp){ run_err = -1; break; }
      run_err = td_run_n_group(fp, ws, jobs, jidx_buf, g1 - g0, blks, all_peaks);
      td_fp_release(fp);
      if(run_err) break;
      g0 = g1;
    }
  }

  /* Compact peaks directly into output bytearrays and merge partial window bins per job. */
  if(!run_err){
    size_t out_cur = 0;
    offs_p[0] = 0;
    for(size_t j = 0; j < nj; j++){
      TdJob *jb = &jobs[j];
      jb->hit_off = out_cur;
      rdy_p[j] = (unsigned char)(jb->spec_ready ? 1 : 0);
      if(jb->nblocks == 0 || jb->pk_cnt == 0){
        jb->hit_cnt = 0;
        offs_p[j + 1] = (int64_t)out_cur;
        continue;
      }
      if(!jb->any_ph && jb->bs < jb->n && jb->nblocks > 1){
        TdBlkOrd stack_ord[64];
        TdBlkOrd *ord = jb->nblocks <= 64 ? stack_ord
            : (TdBlkOrd*)malloc(jb->nblocks * sizeof(TdBlkOrd));
        if(!ord){ run_err = -1; break; }
        for(size_t b = 0; b < jb->nblocks; b++) ord[b] = (TdBlkOrd){blks[jb->blk0 + b].nb, b};
        qsort(ord, jb->nblocks, sizeof(TdBlkOrd), cmp_blk_ord);
        for(size_t s = 0; s < jb->nblocks; s++) ord_scratch[s] = ord[s].idx;
        if(ord != stack_ord) free(ord);
      } else {
        for(size_t b = 0; b < jb->nblocks; b++) ord_scratch[b] = b;
      }

      size_t raw_hits = 0;
      int64_t *si_j = si_base + out_cur;
      float *snr_j = snr_base + 2 * out_cur;
      int64_t *bs_j = bs_base + out_cur;
      for(size_t s = 0; s < jb->nblocks; s++){
        const TdBlk *bk = &blks[jb->blk0 + ord_scratch[s]];
        const ap_peak *pks = all_peaks + bk->pk_dst;
        for(size_t q = 0; q < bk->nb; q++){
          if(pks[q].index >= 0){
            si_j[raw_hits] = bk->ts + (int64_t)pks[q].index;
            snr_j[2 * raw_hits] = pks[q].re;
            snr_j[2 * raw_hits + 1] = pks[q].im;
            bs_j[raw_hits] = bk->ts;
            raw_hits++;
          }
        }
      }

      if(jb->any_ph && raw_hits >= 2){
        size_t w = 0, kept = 0, kw = 0;
        int64_t kb = 0;
        int bestm_ok = 0;
        float bestm = 0.f;
        int mono = 1;
        for(size_t i = 1; i < raw_hits; i++){
          if(si_j[i] <= si_j[i - 1]){ mono = 0; break; }
        }
        if(mono){
          for(size_t i = 0; i < raw_hits; i++){
            while(w + 1 < jb->nw && jb->W[2 * (w + 1)] <= si_j[i]) w++;
            const int64_t b = (si_j[i] - jb->W[2 * w]) / (int64_t)jb->bs;
            if(kept > 0 && w == kw && b == kb){
              if(!bestm_ok){
                bestm = hypotf(snr_j[2 * (kept - 1)], snr_j[2 * (kept - 1) + 1]);
                bestm_ok = 1;
              }
              const float m = hypotf(snr_j[2 * i], snr_j[2 * i + 1]);
              if(m > bestm){
                bestm = m;
                si_j[kept - 1] = si_j[i];
                snr_j[2 * (kept - 1)] = snr_j[2 * i];
                snr_j[2 * (kept - 1) + 1] = snr_j[2 * i + 1];
                bs_j[kept - 1] = bs_j[i];
              }
              continue;
            }
            kw = w; kb = b; bestm_ok = 0;
            if(kept != i){
              si_j[kept] = si_j[i];
              snr_j[2 * kept] = snr_j[2 * i];
              snr_j[2 * kept + 1] = snr_j[2 * i + 1];
              bs_j[kept] = bs_j[i];
            }
            kept++;
          }
          raw_hits = kept;
        }
      }
      jb->hit_cnt = raw_hits;
      out_cur += raw_hits;
      offs_p[j + 1] = (int64_t)out_cur;
    }
    total_kept = out_cur;
  }
  *total_kept_out = total_kept;
  return run_err;
}
