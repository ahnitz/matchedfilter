/* Hierarchical matched filter: raw coarse maximum, then full refinement.
 * Calibration is supplied by the caller. No statistical model or recovery
 * fallback is compiled into this execution engine.
 */
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>
#include <limits.h>
#include "ticks.h"
#include "alloc.h"
#include "env.h"
#include "matchedfilter.h"
#include "transform.h"
#include "q15.h"

/* The FP16 first gate (gate16.cc): an upper bound on the FP32 tier's peak magnitude per
   pair, on ARM with FP16 vectors; unavailable elsewhere (and with MF_GATE16=0). */
int ap_gate16_available(void);
void *ap_gate16_create(size_t m,int nd,int nt);
void ap_gate16_destroy(void *g);
int ap_gate16_set_template(void *g,int t,const float *spec);
int ap_gate16_set_data(void *g,int d,const float *spec);
int ap_gate16_run(void *g,int d0,int nd,int t0,int nt,size_t ws,size_t we,ap_peak *out);
int ap_gate16_run_pairs(void *g,int d0,int t0,const int *dsel,const int *tsel,int n,int nt_row,
                        size_t ws,size_t we,ap_peak *out);
int ap_gate16_run_pairs_lag(void *g,int d0,int t0,const int *dsel,const int *tsel,int n,int nt_row,
                            size_t ws,size_t we,int elect_lag,float thr,
                            int *dst_d,int *dst_t,ap_peak *out);

#define HMF_MAX_DIRECT_BINS 4
#define HMF_COARSE_SUBBINS 16
#define HMF_PEND_MF  1u
#define HMF_PEND_G16 2u
#define HMF_PEND_Q15 4u

/* One coarse tier of the gate chain. Tier i runs on the survivors of tier i-1
   (tier 0 on every pair); the survivors of the last tier get the full refine. */
typedef struct {
  size_t m,k0;                    /* band: coarse transform length and starting fine bin */
  ap_mf_plan *mf;
  float *scratch,*fpow;           /* staging, per-template band fraction */
  float ref_f,thr;                /* reference band fraction; threshold (<0: unconfigured) */
  ap_peak *cebuf;
  unsigned char *pending;         /* [nd] owned series spectrum awaits ingestion */
  int npending;
  int *fire_d,*fire_t;            /* this tier's survivors (grown on demand to fire_cap) */
  size_t fire_cap;
  long passed;                    /* pairs that passed this tier when evaluated */
  long checked;                   /* actual inputs; independent of execution order */
  unsigned long long ticks;       /* time spent in this tier */
  void *g16;                      /* FP16 gate for this tier (tier 0 only), or NULL */
  int lagged;                     /* this call's cebuf index is the pair's largest coarse lag
                                     (not under the FP16 gate, whose index has no reader) */
  int q15;                        /* a later tier gating on the listed Q15 screen
                                     (ap_mf_q15_pairs), with the screen on */
  int last_q15;                   /* this call ran on the listed Q15 screen */
  int16_t *qdm,*qtm;              /* [nd][2*m+32], [nt][2*m+32] Q15 rows for tiers i>0 */
  float *qds,*qts;                /* [nd], [nt] Q15 scales for tiers i>0 */
  void *qscr;                     /* Q15 gather scratch for tiers i>0 */
} hmf_tier;

struct ap_hmf_plan {
  size_t n;
  size_t k;
  /* Each data row's bin phase during an ap_hmf_run_series call ([nd]), NULL otherwise: the
     refine numbers row d's bins from start - bph[d] (ap_mf_run_series). The tiers each take
     one maximum over their window and never see it. */
  const unsigned *bph;
  int is_dif;
  int hermitian;
  int nd,nt,dgroup;
  int ntiers;
  hmf_tier tier[AP_HMF_MAX_TIERS];
  ap_mf_plan *full;
  ap_plan *full_fft;
  float *fwd,*spec;
  const float **dspec;
  float *dcopy;               /* [nd][2n]: ap_hmf_set_data's own copy of each data spectrum */
  int sparse;                 /* ap_hmf_set_sparse: rows that do not fire write counts only */
  char *dready,*tready,*dmirrored;
  int ref_on;
  long pairs,trig;
  unsigned long long c_ref,c_fill;
  unsigned long long c_series;      /* whole ap_hmf_run_series calls: transforms, ingest, tiers, refine */
  int prof,trace;
  FILE *dump;
  float *twiddles,*tw_scratch;
  float *tmpls_half,*prod_scratch;
  /* Q15 screen as the first tier's gate (ap_hmf_set_q15) */
  int q15;
  long first_gate_passed;         /* passes of the first tier */
  unsigned char *qpass;           /* [nd*nt] */
  int *qd,*qt;                    /* the screen's survivors */
  float *qstat;                   /* [nd*nt] the screen's maximum, for MF_HMF_DUMP/TRACE */
  int16_t *qidx;                  /* [nd*nt] coarse argmax lag of listed Q15 screen */
  long qpassed;
  unsigned long long qticks;
  /* Direct refine (ap_hmf_set_taps, ap_hmf_set_direct): a survivor is refined only at the
     lags around its last tier's firing coarse lags, by direct correlation with its real
     taps, where that is priced cheaper than the whole-block transform. */
  float **taps;                   /* [nt] 64-byte aligned taps (split tr, ti if tap_cplx) */
  int *tap_len;                   /* [nt] */
  int tap_cplx;                   /* 1 = complex conjugated taps, 0 = real taps */
  int direct, dir_hw;             /* on; half-width of a window, in last-tier coarse samples */
  const float **dtime;            /* [nd] the block's complex samples (run_series only) */
  size_t *dhave;                  /* [nd] samples present (the rest are zero) */
  float *dx, *dout;               /* [2n] a zero-padded block copy; direct output */
  int dx_d;                       /* block row currently cached in dx, or -1 */
  size_t dx_lo, dx_hi;            /* unpacked sample span [dx_lo, dx_hi) in dx */
  int *dfd, *dft;                 /* [df_cap] pairs the transform refines instead */
  size_t df_cap;
  ap_peak *dir_sub;               /* [ns*HMF_COARSE_SUBBINS] coarse sub-bin peaks of multi-bin survivors */
  size_t dir_sub_cap;
  double dir_lagtap, dir_fftpair; /* priced: ticks per lag x tap, per whole-block refine */
  long dir_pairs, dir_lags, dir_fft, dir_edge;
  unsigned long long dir_ttd, dir_tfft;  /* ticks: direct, and the pairs it left to transform */
  /* Real series (ap_hmf_set_real_series): ap_hmf_run_series reads real samples and
     transforms each block as n/2 complex ones -- half the transform and half the input --
     then splits that into the block's full (Hermitian) spectrum. */
  int real_series;
  size_t real_stride;             /* floats between samples: 1, or 2 for a lane of a complex series */
  ap_plan *half_fft;              /* n/2-point transform */
  ap_plan *fwd_cplx_batch;        /* lane-batched n-point forward (n <= 2048), or NULL */
  ap_plan *fwd_real_batch;        /* lane-batched n/2-point real forward (n <= 4096), or NULL */
  float *rtw;                     /* [2(n/2+1)] cos, sin of 2 pi k/n */
  /* Tier-0 pair-centroid clustering (ap_hmf_set_tier0_clusters): evaluates tier0_nt <= nt
     lag- and phase-aligned coarse centroids at tier 0 on full-bank multi-tier sweeps and
     expands firing centroids to their member template indices for tier 1. */
  int tier0_clustered;
  int tier0_nt;
  int tier0_lag_pad;
  ap_mf_plan *tier0_mf;
  void *tier0_g16;
  int *tier0_off;                 /* [tier0_nt + 1] CSR offsets into tier0_members */
  int *tier0_members;             /* [nt] disjoint member template indices in [0, nt) */
  unsigned char *tier0_uncl_pend; /* [nd] deferred ingest into unclustered tier[0] */
  /* Tier-1 sub-centroid clustering (ap_hmf_set_tier1_clusters): evaluates tier1_nt <= nt
     sub-centroids at tier 1 on survivors of tier 0 and expands firing Tier-1 centroids
     to their member template indices for tier 2 / refine. */
  int tier1_clustered;
  int tier1_nt;
  int tier1_lag_pad;
  ap_mf_plan *tier1_mf;
  void *tier1_g16;
  int16_t *tier1_qtm;             /* [tier1_nt][2*m1+32] Q15 template rows for tier 1 */
  float *tier1_qts;               /* [tier1_nt] Q15 template scales for tier 1 */
  int *tier1_off;                 /* [tier1_nt + 1] CSR offsets into tier1_members */
  int *tier1_members;             /* [nt] disjoint member template indices in [0, nt) */
  int *tier1_map;                 /* [nt] raw template t -> Tier-1 cluster index c1 */
  unsigned char *tier1_uncl_pend; /* [nd] deferred ingest into unclustered tier[1] */
};

int ap_hmf_series_group(const ap_hmf_plan *p){ return p ? p->dgroup : 0; }

/* The series group a plan of size n runs when asked for `requested`: halved until the held
   spectra fit 512 KB (256 KB of active positive-frequency bins under real_series, keeping the
   slab L2-resident per core without thrashing shared L3 under multi-core load, while amortising
   template reloads and sparse pair-batch lanes across 32 blocks at n = 2048). MF_DGROUP
   overrides it for measurement up to the 4 MB safety ceiling. Calibrations key their models by
   this, the group that ran, not the one asked for. */
int ap_hmf_effective_group(size_t n,int requested){
  const long v=ap_env_int("MF_DGROUP",0);
  const size_t cap = v>0 ? (size_t)4*1024*1024 : (size_t)512*1024;
  int grp = v>0 ? (int)v : (requested>0 ? requested : 64);
  while(grp>1 && (size_t)grp*2*n*sizeof(float) > cap) grp>>=1;
  /* Above the 32-block SIMD/pairbatch floor, keep the held spectrum slab
     (grp * 8 * n bytes) within half of per-core L2 so templates stay L2-resident too. */
  if(v<=0 && requested<=0 && grp>32){
    const size_t l2=ap_l2_bytes();
    while(grp>32 && (size_t)grp*8*n > (l2>>1)) grp>>=1;
  }
  return grp;
}

/* Pairbatch forward FFT limit: 8-lane/16-lane x86 targets with Q15 lanes and 32-register
   ARM64 NEON run pairbatch small transforms up to h = 2048; 16-register SSE4 stays at 512. */
static inline size_t hmf_fwd_pb_limit(const ap_hmf_plan *p){
  const int w=ap_plan_lanes(p->full_fft);
  if(w>=16) return 2048u;
  if(w>=8 && p->ntiers>0 && ap_mf_q15_lanes(p->tier[0].mf)>0) return 2048u;
#if defined(__aarch64__)
  if(w>=4) return 2048u;
#endif
  return 512u;
}

static inline int hmf_ensure_cebuf(ap_hmf_plan *p,hmf_tier *tr){
  if(tr->cebuf) return 0;
  tr->cebuf=calloc((size_t)p->nd*(size_t)p->nt,sizeof(ap_peak));
  return tr->cebuf ? 0 : -1;
}

static inline int hmf_ensure_fire(hmf_tier *tr,size_t need){
  if(need<=tr->fire_cap) return 0;
  size_t cap=tr->fire_cap ? tr->fire_cap*2u : 256u;
  if(cap<need) cap=need;
  int *fd=realloc(tr->fire_d,cap*sizeof(int));
  if(!fd) return -1;
  tr->fire_d=fd;
  int *ft=realloc(tr->fire_t,cap*sizeof(int));
  if(!ft) return -1;
  tr->fire_t=ft;
  tr->fire_cap=cap;
  return 0;
}

static inline int hmf_ensure_df(ap_hmf_plan *p,size_t need){
  if(need<=p->df_cap) return 0;
  size_t cap=p->df_cap ? p->df_cap*2u : 256u;
  if(cap<need) cap=need;
  int *fd=realloc(p->dfd,cap*sizeof(int));
  if(!fd) return -1;
  p->dfd=fd;
  int *ft=realloc(p->dft,cap*sizeof(int));
  if(!ft) return -1;
  p->dft=ft;
  p->df_cap=cap;
  return 0;
}

ap_hmf_plan *ap_hmf_create_chain(size_t n,size_t k,int ndata,int ntmpl,
                                 const size_t *bands,int ntiers,int series_group){
  if(series_group<1||series_group>65535||ndata<1||ntmpl<1||!ap_supported(n)
     ||!bands||ntiers<1||ntiers>AP_HMF_MAX_TIERS) return NULL;
  for(int i=0;i<ntiers;i++){
    if(!ap_supported(bands[i])||bands[i]>=n) return NULL;
    if(i>0 && bands[i]<=bands[i-1]) return NULL;       /* strictly increasing */
  }
  if(k>0 && k!=n && k!=n/2) return NULL;
  if(k>0 && k==n/2 && !ap_supported(k)) return NULL;
  ap_hmf_plan *p=calloc(1,sizeof(*p));
  if(!p) return NULL;
  p->n=n;
  p->k=(k>0) ? k : n;
  p->is_dif=(p->k == n/2);
  p->nt=ntmpl; p->ntiers=ntiers;
  const int grp = ap_hmf_effective_group(n, series_group);
  p->dgroup=grp; p->nd=ndata>grp ? ndata : grp;
  if((size_t)p->nd > (size_t)INT_MAX / (size_t)ntmpl){
    ap_hmf_destroy(p); return NULL;
  }
  if(p->is_dif){
    p->full=ap_mf_create(p->k, 2*p->nd, ntmpl);
    p->twiddles=ap_alloc64(2*p->k*sizeof(float));
    p->tw_scratch=ap_alloc64(2*p->k*sizeof(float));
    p->tmpls_half=ap_alloc64((size_t)ntmpl*2*p->k*sizeof(float));
    p->prod_scratch=ap_alloc64(2*p->n*sizeof(float));
    if(!p->twiddles || !p->tw_scratch || !p->tmpls_half || !p->prod_scratch){
      ap_hmf_destroy(p); return NULL;
    }
    const size_t N_tw = 2 * p->k;
    for(size_t j = 0; j < p->k; j++){
      double angle = 2.0 * M_PI * (double)j / (double)N_tw;
      p->twiddles[2 * j]     = (float)cos(angle);
      p->twiddles[2 * j + 1] = (float)sin(angle);
    }
  } else {
    p->full=ap_mf_create(n, p->nd, ntmpl);
  }
  { long pbmax=ap_env_int("MF_PBMAX",-1);
    int lw = ap_lane_width();
    size_t pblim = pbmax>=0 ? (size_t)pbmax : (lw>=16 ? 1024u : 512u);
    size_t min_ntmpl = (lw > 0) ? (size_t)lw : 16u;
    for(int i=0;i<ntiers;i++){
      hmf_tier *tr=&p->tier[i];
      tr->m=bands[i]; tr->thr=-1;
      const size_t pblim_i = (pbmax<0 && i>0 && lw>=8) ? 1024u : pblim;
      if((size_t)ntmpl>=min_ntmpl && tr->m<=pblim_i) tr->mf=ap_mf_create_pairbatch(tr->m,p->nd,ntmpl);
      if(!tr->mf) tr->mf=ap_mf_create(tr->m,p->nd,ntmpl);
      if(ap_gate16_available()) tr->g16=ap_gate16_create(tr->m,p->nd,ntmpl);
      tr->scratch=ap_alloc64(2*tr->m*sizeof(float));
      tr->fpow=calloc((size_t)ntmpl,sizeof(float));
      tr->pending=calloc((size_t)p->nd,1);
      if(!tr->mf||!tr->scratch||!tr->fpow||!tr->pending){
        ap_hmf_destroy(p); return NULL;
      }
      if(i>0 && ap_mf_q15_lanes(tr->mf)>0){
        tr->qtm=ap_alloc64((size_t)ntmpl*(2*tr->m+32)*sizeof(int16_t));
        tr->qts=calloc((size_t)ntmpl,sizeof(float));
        if(!tr->qtm||!tr->qts){ ap_hmf_destroy(p); return NULL; }
      }
    }
  }
  p->full_fft=ap_create(n);
  if(p->full_fft && n>=64 && n<=hmf_fwd_pb_limit(p))
    p->fwd_cplx_batch=ap_create_pairbatch_like(p->full_fft,n);
  p->fwd=ap_alloc64(2*n*sizeof(float));
  p->spec=ap_alloc64((size_t)grp*(2*n+16)*sizeof(float));
  p->dspec=calloc((size_t)p->nd,sizeof(*p->dspec));
  p->dtime=calloc((size_t)p->nd,sizeof(*p->dtime));
  p->dhave=calloc((size_t)p->nd,sizeof(*p->dhave));
  p->dready=calloc((size_t)p->nd,1);
  p->dmirrored=calloc((size_t)p->nd,1);
  p->tready=calloc((size_t)ntmpl,1);
  if(!p->full||!p->full_fft||!p->fwd||!p->spec||!p->dspec||!p->dready||!p->dmirrored||!p->tready
     ||!p->dtime||!p->dhave){
    ap_hmf_destroy(p); return NULL;
  }
  p->prof=ap_env_flag("MF_HMF_PROF",0);
  p->trace=ap_env_flag("MF_HMF_TRACE",0);
  const char *dump=ap_env_text("MF_HMF_DUMP");
  p->dump=dump ? fopen(dump,"wb") : NULL;
  return p;
}

static void hmf_free_tier0_clusters(ap_hmf_plan *p);
static void hmf_free_tier1_clusters(ap_hmf_plan *p);
void ap_hmf_clear_tier1_clusters(ap_hmf_plan *p);

void ap_hmf_destroy(ap_hmf_plan *p){
  if(!p) return;
  hmf_free_tier0_clusters(p);
  hmf_free_tier1_clusters(p);
  ap_mf_destroy(p->full);
  for(int i=0;i<p->ntiers;i++){
    hmf_tier *tr=&p->tier[i];
    if(tr->mf) ap_mf_destroy(tr->mf);
    if(tr->g16) ap_gate16_destroy(tr->g16);
    free(tr->scratch); free(tr->fpow); free(tr->cebuf); free(tr->pending);
    free(tr->fire_d); free(tr->fire_t);
    free(tr->qdm); free(tr->qtm); free(tr->qds); free(tr->qts); free(tr->qscr);
  }
  ap_destroy(p->full_fft);
  if(p->half_fft) ap_destroy(p->half_fft);
  if(p->fwd_cplx_batch) ap_destroy(p->fwd_cplx_batch);
  if(p->fwd_real_batch) ap_destroy(p->fwd_real_batch);
  free(p->rtw);
  free(p->fwd); free(p->spec); free(p->dspec); free(p->dcopy);
  free(p->dready); free(p->dmirrored); free(p->tready);
  if(p->twiddles) free(p->twiddles);
  if(p->tw_scratch) free(p->tw_scratch);
  if(p->tmpls_half) free(p->tmpls_half);
  if(p->prod_scratch) free(p->prod_scratch);
  if(p->dump) fclose(p->dump);
  free(p->qpass); free(p->qd); free(p->qt); free(p->qstat); free(p->qidx);
  if(p->taps){ for(int t=0;t<p->nt;t++) free(p->taps[t]); free(p->taps); }
  free(p->tap_len); free(p->dtime); free(p->dhave);  free(p->dx); free(p->dout); free(p->dfd); free(p->dft);
  free(p->dir_sub);
  free(p);
}

static inline size_t tap_imag_offset(int L){
  return ((size_t)L + 15u) & ~(size_t)15u;
}

static int set_taps_impl(ap_hmf_plan *p,const float *taps,size_t stride,const int64_t *counts,
                         int cplx){
  if(!p||!taps||!counts) return -1;
  for(int t=0;t<p->nt;t++) if(counts[t]<1||(size_t)counts[t]>stride||(size_t)counts[t]>p->n) return -1;
  if(!p->taps){
    p->taps=calloc((size_t)p->nt,sizeof(*p->taps));
    p->tap_len=calloc((size_t)p->nt,sizeof(int));
    p->dx=ap_alloc64(2*p->n*sizeof(float));
    p->dout=ap_alloc64(2*p->n*sizeof(float));
    if(!p->taps||!p->tap_len||!p->dx||!p->dout) goto fail;
  }
  for(int t=0;t<p->nt;t++){
    const int L=(int)counts[t];
    const size_t ioff=tap_imag_offset(L);
    const size_t nfl=cplx ? ioff+(size_t)L : (size_t)L;
    free(p->taps[t]);
    p->taps[t]=ap_alloc64(nfl*sizeof(float));
    if(!p->taps[t]) goto fail;
    if(cplx){
      const float *src=taps+2*(size_t)t*stride;
      float *tr=p->taps[t], *ti=tr+ioff;
      for(int k=0;k<L;k++){ tr[k]=src[2*k]; ti[k]=-src[2*k+1]; }
    } else {
      memcpy(p->taps[t],taps+(size_t)t*stride,(size_t)L*sizeof(float));
    }
    p->tap_len[t]=L;
  }
  p->tap_cplx=cplx?1:0;
  p->dx_d=-1;
  p->dir_lagtap=0;
  return 0;
fail:
  if(p->taps){ for(int t=0;t<p->nt;t++) free(p->taps[t]); free(p->taps); p->taps=NULL; }
  free(p->tap_len); p->tap_len=NULL;
  free(p->dx); p->dx=NULL;
  free(p->dout); p->dout=NULL;
  free(p->dfd); p->dfd=NULL;
  free(p->dft); p->dft=NULL;
  p->df_cap=0;
  p->tap_cplx=0;
  return -1;
}

/* Each template's real FIR taps: row t holds counts[t] valid taps (stride floats per row),
   centre tap counts[t]/2 at lag 0 -- the filter whose spectrum ap_hmf_set_template holds
   (time_domain._tap_spectra, rate ratio 1). */
int ap_hmf_set_taps(ap_hmf_plan *p,const float *taps,size_t stride,const int64_t *counts){
  return set_taps_impl(p,taps,stride,counts,0);
}

/* Complex FIR taps: stride complex64 elements per row; conjugated at ingest so conj(taps[k])
   is stored as (tr[k], ti[k]). */
int ap_hmf_set_taps_complex(ap_hmf_plan *p,const float *taps,size_t stride,const int64_t *counts){
  return set_taps_impl(p,taps,stride,counts,1);
}

/* A direct correlation to time (price_corr_ticks): ap_td_corr_ex_on on fft (NULL: the
   process's backend) of these operands. */
typedef struct {
  const ap_plan *fft; const float *x; int x_real; const float *tr, *ti; int L, nl; float *out;
} price_corr_job;

/* Ticks a timed round spans, at least. A direct correlation of 32 lags x 256 taps takes well
   under the step of macOS's monotonic clock (ap_ticks: nanoseconds, in steps of about a
   microsecond on an M2), so timed once it read 0, and a price of 0 is a failed price: the
   direct refine went unpriced, and so unused, on Apple CPUs (2026-11-01). Rounds of 100,000
   ticks -- 100 us of that clock, ~30 us of x86 cycles -- put its step under 1% of a round. */
#define PRICE_MIN_TICKS 300000ull

/* Ticks per call of job's correlation: the fastest of 7 rounds, each of as many calls as span
   PRICE_MIN_TICKS. */
static double price_corr_ticks(const price_corr_job *j){
  /* Fault output buffer and warm caches before sizing reps so a minor page fault or single
     preemption does not truncate reps at 1 or read an unboosted idle-core clock. */
  ap_td_corr_ex_on(j->fft,j->x,j->x_real,j->tr,j->ti,j->L,j->nl,j->out);
  unsigned long reps=1;
  for(;;){                                   /* calls per round, doubled until long enough */
    unsigned long long span=~0ull;
    for(int p=0;p<2;p++){
      const unsigned long long a=ap_ticks();
      for(unsigned long k=0;k<reps;k++)
        ap_td_corr_ex_on(j->fft,j->x,j->x_real,j->tr,j->ti,j->L,j->nl,j->out);
      const unsigned long long d=ap_ticks()-a;
      if(d<span) span=d;
    }
    if(span>=PRICE_MIN_TICKS || reps>=(1ul<<20)) break;
    reps*=2;
  }
  double best=1e30;
  for(int r=0;r<7;r++){
    const unsigned long long a=ap_ticks();
    for(unsigned long k=0;k<reps;k++)
      ap_td_corr_ex_on(j->fft,j->x,j->x_real,j->tr,j->ti,j->L,j->nl,j->out);
    const unsigned long long b=ap_ticks();
    const double t=(double)(b-a)/(double)reps;
    if(t<best) best=t;
  }
  return best;
}

/* Ticks per lag x tap of the direct correlation on this core (price_corr_ticks): what the
   cost model charges a direct refine (gatechain.CostModel.with_direct). */
double ap_hmf_price_direct_mode(int x_real,int tap_cplx){
  const int L=256, nl=32;
  float *x=ap_alloc64(2*(size_t)(nl+L)*sizeof(float));
  float *tr=ap_alloc64((size_t)L*sizeof(float));
  float *ti=tap_cplx ? ap_alloc64((size_t)L*sizeof(float)) : NULL;
  float *out=ap_alloc64(2*(size_t)nl*sizeof(float));
  double best=-1;
  if(x&&tr&&(!tap_cplx||ti)&&out){
    for(int i=0;i<2*(nl+L);i++) x[i]=(float)((i*7919)%1000)/1000.f-0.5f;
    for(int i=0;i<L;i++) tr[i]=(float)((i*104729)%1000)/1000.f-0.5f;
    if(ti) for(int i=0;i<L;i++) ti[i]=(float)((i*65537)%1000)/1000.f-0.5f;
    const price_corr_job j={NULL,x,x_real?1:0,tr,ti,L,nl,out};
    best=price_corr_ticks(&j)/((double)nl*L);
  }
  free(x); free(tr); free(ti); free(out);
  return best;
}

double ap_hmf_price_direct(void){
  return ap_hmf_price_direct_mode(0,0);
}

/* Price the direct correlation (ticks per lag x tap) and the whole-block refine (ticks per
   surviving pair: real-series mirror if active, split-layout data ingest, fused frequency
   product, inverse transform, and peak scan across L2-resident slots) on this core. */
static void price_direct(ap_hmf_plan *p){
  const size_t n=p->n;
  const int L=256, nl=32, nslot=4;
  float *x=ap_alloc64(2*(size_t)(nl+L)*sizeof(float));
  float *tr=ap_alloc64((size_t)L*sizeof(float));
  float *ti=p->tap_cplx ? ap_alloc64((size_t)L*sizeof(float)) : NULL;
  float *dout=ap_alloc64(2*(size_t)nl*sizeof(float));
  float *spec=ap_alloc64((size_t)nslot*2*n*sizeof(float));
  float *dr=ap_alloc64((size_t)nslot*n*sizeof(float));
  float *di=ap_alloc64((size_t)nslot*n*sizeof(float));
  float *tr_s=ap_alloc64((size_t)nslot*n*sizeof(float));
  float *ti_s=ap_alloc64((size_t)nslot*n*sizeof(float));
  float *prod=ap_alloc64(2*n*sizeof(float));
  ap_peak pk[4];
  if(!x||!tr||(p->tap_cplx&&!ti)||!dout||!spec||!dr||!di||!tr_s||!ti_s||!prod){
    free(x); free(tr); free(ti); free(dout); free(spec);
    free(dr); free(di); free(tr_s); free(ti_s); free(prod);
    return;
  }
  for(int i=0;i<2*(nl+L);i++) x[i]=(float)((i*7919)%1000)/1000.f-0.5f;
  for(int i=0;i<L;i++) tr[i]=(float)((i*104729)%1000)/1000.f-0.5f;
  if(ti) for(int i=0;i<L;i++) ti[i]=(float)((i*65537)%1000)/1000.f-0.5f;
  for(size_t i=0;i<(size_t)nslot*2*n;i++) spec[i]=(float)((i*31337)%1000)/1000.f-0.5f;
  int n1=0, n2=0;
  if(!ap_plan_split(p->full_fft,&n1,&n2)) n1=n2=0;
  const int w=ap_plan_lanes(p->full_fft);
  const int gmajor=!p->is_dif && w>0 && n1>0 && n1%w==0
                   && (size_t)n1*n2==n && ap_has_fused_prod(p->full_fft);
  const ap_prod_kernel pkern=gmajor ? ap_plan_prod_kernel(p->full_fft,1e30f)
                                    : (ap_prod_kernel){NULL,NULL};
  for(int s=0;s<nslot;s++)
    ap_split_store_on(p->full_fft,spec+(size_t)s*2*n,
                      tr_s+(size_t)s*n,ti_s+(size_t)s*n,n,1,gmajor?n1:0,n2,w);
  const price_corr_job job={p->full_fft,x,p->real_series,tr,ti,L,nl,dout};
  const double best_d=price_corr_ticks(&job);
  double best_f=1e30;
  for(int r=0;r<7;r++){
    const int s=r&(nslot-1);
    float *sp=spec+(size_t)s*2*n;
    float *drs=dr+(size_t)s*n, *dis=di+(size_t)s*n;
    const float *trs=tr_s+(size_t)s*n, *tis=ti_s+(size_t)s*n;
    const unsigned long long b=ap_ticks();
    if(p->real_series) ap_real_split_mirror_on(p->full_fft,sp,n);
    if(gmajor && pkern.run){
      ap_split_store_on(p->full_fft,sp,drs,dis,n,0,n1,n2,w);
      pkern.run(pkern.context,drs,dis,trs,tis,n,1e30f,pk,1,0,n,NULL);
    } else {
      for(size_t k=0;k<n;k++){
        const float xr=sp[2*k], xi=sp[2*k+1], hr=trs[k], hi=tis[k];
        prod[2*k]=xr*hr-xi*hi; prod[2*k+1]=xr*hi+xi*hr;
      }
      int c=0;
      ap_binmax(p->full_fft,prod,n,1,n,1e30f,pk,&c,AP_BACKWARD,0,n,NULL);
    }
    const unsigned long long e=ap_ticks();
    if((double)(e-b)<best_f) best_f=(double)(e-b);
  }
  p->dir_lagtap=best_d/((double)nl*L);
  p->dir_fftpair=best_f;
  free(x); free(tr); free(ti); free(dout); free(spec);
  free(dr); free(di); free(tr_s); free(ti_s); free(prod);
}

int ap_hmf_price_direct_pair(ap_hmf_plan *p,double *lagtap,double *fftpair){
  if(!p) return -1;
  const double lt=p->dir_lagtap, fp=p->dir_fftpair;
  p->dir_lagtap=0;
  price_direct(p);
  const int ok=p->dir_lagtap>0;
  if(lagtap) *lagtap=p->dir_lagtap;
  if(fftpair) *fftpair=p->dir_fftpair;
  p->dir_lagtap=lt; p->dir_fftpair=fp;          /* measuring leaves the plan's own prices */
  return ok ? 0 : -1;
}

int ap_hmf_set_direct_prices(ap_hmf_plan *p,double lagtap,double fftpair){
  if(!p || !(lagtap>0) || !(fftpair>0)) return -1;
  p->dir_lagtap=lagtap; p->dir_fftpair=fftpair;
  return 0;
}

int ap_hmf_set_direct(ap_hmf_plan *p,int on,int halfwidth){
  if(!p) return -1;
  if(!on){ p->direct=0; return 0; }
  if(!p->taps||halfwidth<1) return -1;
  p->direct=1; p->dir_hw=halfwidth;
  if(p->dir_lagtap<=0) price_direct(p);
  return 0;
}

int ap_hmf_direct_stats(const ap_hmf_plan *p,long *pairs,long *lags,long *fft,
                        double *lagtap,double *fftpair){
  if(!p) return -1;
  if(pairs) *pairs=p->dir_pairs;
  if(lags) *lags=p->dir_lags;
  if(fft) *fft=p->dir_fft;
  if(lagtap) *lagtap=p->dir_lagtap;
  if(fftpair) *fftpair=p->dir_fftpair;
  return 0;
}

int ap_hmf_set_q15(ap_hmf_plan *p,int on){
  if(!p) return -1;
  if(!on){
    p->q15=0;
    for(int i=0;i<p->ntiers;i++) p->tier[i].q15=0;
    return 0;
  }
  if(ap_mf_q15_lanes(p->tier[0].mf)<=0) return -1;
  if(!p->qpass){
    const size_t np=(size_t)p->nd*p->nt;
    p->qpass=malloc(np); p->qd=malloc(np*sizeof(int)); p->qt=malloc(np*sizeof(int));
    p->qstat=malloc(np*sizeof(float)); p->qidx=malloc(np*sizeof(int16_t));
    if(!p->qpass||!p->qd||!p->qt||!p->qstat||!p->qidx){
      free(p->qpass); free(p->qd); free(p->qt); free(p->qstat); free(p->qidx);
      p->qpass=NULL; p->qd=p->qt=NULL; p->qstat=NULL; p->qidx=NULL; return -1;
    }
  }
  /* The screen decides on its own int16 maximum: no margin (ap_mf_set_q15_margin). Later
     tiers gate the same way on their survivor lists, where their band has a screen; when the
     last tier gates in Q15 for a direct-refine plan, ap_mf_q15_pairs_lag also elects its
     coarse argmax lag. */
  ap_mf_set_q15_margin(p->tier[0].mf,0);
  if(p->tier0_mf) ap_mf_set_q15_margin(p->tier0_mf,0);
  if(p->tier1_mf) ap_mf_set_q15_margin(p->tier1_mf,0);
  for(int i=1;i<p->ntiers;i++){
    hmf_tier *tr=&p->tier[i];
    tr->q15=ap_mf_q15_lanes(tr->mf)>0;
    if(tr->q15) ap_mf_set_q15_margin(tr->mf,0);
  }
  p->q15=1;
  return 0;
}
long ap_hmf_first_gate_passed(const ap_hmf_plan *p){ return p ? p->first_gate_passed : 0; }
int ap_hmf_tier_inputs(const ap_hmf_plan *p,long *checked){
  if(!p) return 0;
  if(checked) for(int i=0;i<p->ntiers;i++) checked[i]=p->tier[i].checked;
  return p->ntiers;
}
int ap_hmf_get_q15(const ap_hmf_plan *p){ return p ? p->q15 : 0; }
int ap_hmf_q15_stats(const ap_hmf_plan *p,long *passed,unsigned long long *ticks){
  if(!p) return -1;
  if(passed) *passed=p->qpassed;
  if(ticks) *ticks=p->qticks;
  return 0;
}

void ap_hmf_clear_tier0_clusters(ap_hmf_plan *p);

int ap_hmf_set_hermitian(ap_hmf_plan *p,int hermitian){
  if(!p) return -1;
  if(p->hermitian == !!hermitian) return 0;
  ap_hmf_clear_tier0_clusters(p);
  ap_hmf_clear_tier1_clusters(p);
  p->hermitian = hermitian ? 1 : 0;
  /* The packed DC/Nyquist convention changes both the coarse normalization
     and the refine's template layout. Replay rows already ingested. */
  if(p->is_dif){
    for(int t=0;t<p->nt;t++)
      if(p->tready[t]==1 && ap_hmf_set_template(p,t,p->tmpls_half+(size_t)t*2*p->k)) return -1;
  }
  return 0;
}

size_t ap_hmf_nbins(const ap_hmf_plan *p,size_t bs,size_t lo,size_t hi){
  if(!p || !bs) return 0;
  if(hi > p->n) hi = p->n;
  if(lo >= hi) return 0;
  return (hi - lo + bs - 1) / bs;
}
/* The same for bins numbered from lo - ph; and row d's phase. */
static size_t hmf_nbins_phased(const ap_hmf_plan *p,size_t bs,size_t lo,size_t hi,unsigned ph){
  if(!p || !bs) return 0;
  if(hi > p->n) hi = p->n;
  return ap_bin_count(bs,lo,hi,ph);
}
static inline unsigned hmf_row_phase(const ap_hmf_plan *p,int d){ return p->bph ? p->bph[d] : 0u; }
void ap_hmf_stats(const ap_hmf_plan *p,long *pairs,long *refined){
  if(!p) return;
  if(pairs) *pairs=p->pairs;
  if(refined) *refined=p->trig;
  if(p->prof && p->pairs){
    fprintf(stderr,"    [prof] cycles/pair:");
    for(int i=0;i<p->ntiers;i++)
      fprintf(stderr," tier%d(%zu)=%.0f",i,p->tier[i].m,(double)p->tier[i].ticks/p->pairs);
    fprintf(stderr," refine=%.0f fill=%.0f\n",(double)p->c_ref/p->pairs,(double)p->c_fill/p->pairs);
  }
}
int ap_hmf_tier_stats(const ap_hmf_plan *p,int tier,long *passed,unsigned long long *ticks){
  if(!p || tier<0 || tier>p->ntiers) return -1;
  if(tier==p->ntiers){                       /* the refine */
    if(passed) *passed=p->trig;
    if(ticks) *ticks=p->c_ref;
  } else {
    if(passed) *passed=p->tier[tier].passed;
    if(ticks) *ticks=p->tier[tier].ticks;
  }
  return 0;
}
int ap_hmf_chain(const ap_hmf_plan *p,size_t *bands){
  if(!p) return 0;
  if(bands) for(int i=0;i<p->ntiers;i++) bands[i]=p->tier[i].m;
  return p->ntiers;
}
static inline size_t tier_khi(const ap_hmf_plan *p,const hmf_tier *tr){
  if(!tr->k0) return tr->m < p->k ? tr->m : p->k;
  const size_t lim = p->n/2 < p->k ? p->n/2 : p->k;
  const size_t hi = tr->k0 + tr->m;
  return hi < lim ? hi : lim;
}
/* Copy data row d's active band [k0, khi) into tier tr, wrapping bin k into cyclic slot
   k & (m - 1) when k0 > 0 so the m-point backward IFFT needs no twiddles. */
static int ingest_tier_data_target(const ap_hmf_plan *p,hmf_tier *tr,ap_mf_plan *mf,void *g16,
                                   int d,const float *spec,int to_mf,int to_g16){
  const float *src = spec;
  if(tr->k0 > 0){
    const size_t khi = tier_khi(p,tr);
    const size_t len = khi > tr->k0 ? khi - tr->k0 : 0;
    if(len < tr->m) memset(tr->scratch,0,2*tr->m*sizeof(float));
    const size_t u0 = tr->k0 & (tr->m - 1);
    const size_t first = len < tr->m - u0 ? len : tr->m - u0;
    if(first) memcpy(tr->scratch + 2*u0, spec + 2*tr->k0, 2*first*sizeof(float));
    if(len > first) memcpy(tr->scratch, spec + 2*(tr->k0 + first), 2*(len - first)*sizeof(float));
    src = tr->scratch;
  }
  if(to_mf && mf && ap_mf_set_data(mf,d,src)) return -1;
  if(to_g16 && g16 && ap_gate16_set_data(g16,d,src)) return -1;
  return 0;
}
static inline void hmf_set_pending(hmf_tier *tr,int d,unsigned char mask){
  if((tr->pending[d]!=0) != (mask!=0)) tr->npending += mask ? 1 : -1;
  tr->pending[d]=mask;
}
static int ingest_tier_data(ap_hmf_plan *p,hmf_tier *tr,int d,const float *spec,
                            int to_mf,int to_g16){
  if(tr == &p->tier[0] && p->tier0_clustered){
    if(ingest_tier_data_target(p,tr,p->tier0_mf,p->tier0_g16,d,spec,to_mf,to_g16)) return -1;
    if(p->tier0_uncl_pend) p->tier0_uncl_pend[d] = 1;
    return 0;
  }
  if(p->ntiers >= 2 && tr == &p->tier[1] && p->tier1_clustered){
    if(ingest_tier_data_target(p,tr,p->tier1_mf,p->tier1_g16,d,spec,to_mf,to_g16)) return -1;
    if(p->tier1_uncl_pend) p->tier1_uncl_pend[d] = 1;
    return 0;
  }
  return ingest_tier_data_target(p,tr,tr->mf,tr->g16,d,spec,to_mf,to_g16);
}
int ap_hmf_band_offsets(const ap_hmf_plan *p,size_t *k0s){
  if(!p) return 0;
  if(k0s) for(int i=0;i<p->ntiers;i++) k0s[i]=p->tier[i].k0;
  return p->ntiers;
}
int ap_hmf_set_band_offsets(ap_hmf_plan *p,const size_t *k0s,int ntiers){
  if(!p || !k0s || ntiers!=p->ntiers) return -1;
  const size_t lim = p->n/2 < p->k ? p->n/2 : p->k;
  int same = 1;
  for(int i=0;i<ntiers;i++){
    if(k0s[i]>0 && k0s[i]>=lim) return -1;
    if(p->tier[i].k0 != k0s[i]) same = 0;
  }
  if(same) return 0;
  ap_hmf_clear_tier0_clusters(p);
  ap_hmf_clear_tier1_clusters(p);
  for(int i=0;i<ntiers;i++) p->tier[i].k0 = k0s[i];
  for(int t=0;t<p->nt;t++) if(p->tready[t]==1) p->tready[t]=2;
  if(p->dcopy){
    const size_t row = 2*p->n;
    for(int d=0;d<p->nd;d++)
      if(p->dmirrored[d] && p->dspec[d]==p->dcopy+(size_t)d*row){
        for(int i=0;i<p->ntiers;i++){
          hmf_tier *tr=&p->tier[i];
          const unsigned char qbit = tr->qtm ? HMF_PEND_Q15 : 0u;
          if(i==0 && tr->g16 && !p->q15){
            if(ingest_tier_data(p,tr,d,p->dcopy+(size_t)d*row,0,1)) return -1;
            hmf_set_pending(tr,d,(unsigned char)(HMF_PEND_MF | qbit));
          } else {
            if(ingest_tier_data(p,tr,d,p->dcopy+(size_t)d*row,1,1)) return -1;
            hmf_set_pending(tr,d,qbit);
          }
        }
      }
  }
  return 0;
}
int ap_hmf_thresholds(const ap_hmf_plan *p,float *thr){
  if(!p) return 0;
  if(thr) for(int i=0;i<p->ntiers;i++) thr[i]=p->tier[i].thr;
  return p->ntiers;
}
int ap_hmf_set_thresholds(ap_hmf_plan *p,const float *thr,int ntiers){
  if(!p || !thr || ntiers!=p->ntiers) return -1;
  for(int i=0;i<ntiers;i++) if(!isfinite(thr[i])) return -1;
  for(int i=0;i<ntiers;i++) p->tier[i].thr=thr[i];   /* negative marks unconfigured */
  return 0;
}
/* Quantize one conjugated coarse template row spec ([m] interleaved complex) to the Q15
   screen's layout (qrow: [m] real then [m] imaginary int16, scaled to |t_q|_2 = AP_Q15_TNORM
   unless a component would pass int16). Returns the scale t_q = t * scale (0 for an all-zero
   row, negative for a non-finite one; the row is then zeroed). */
static float hmf_q15_template_row(const float *spec,size_t m,int16_t *qrow){
  double ss=0.0, amax=0.0;
  for(size_t k=0;k<m;k++){
    const double r=(double)spec[2*k], im=-(double)spec[2*k+1];
    ss += r*r + im*im;
    if(fabs(r)>amax) amax=fabs(r);
    if(fabs(im)>amax) amax=fabs(im);
  }
  double sc = !isfinite(ss) ? -1.0 : 0.0;
  if(sc==0.0 && ss>0.0){
    sc = AP_Q15_TNORM(m) / sqrt(ss);
    if(sc*amax > 32767.0) sc = 32767.0 / amax;
  }
  int16_t *qr = qrow, *qi = qrow + m;
  if(!(sc > 0.0)){
    memset(qr,0,2*m*sizeof(int16_t));
  } else {
    for(size_t k=0;k<m;k++){
      double vr=nearbyint((double)spec[2*k]*sc), vi=nearbyint(-(double)spec[2*k+1]*sc);
      if(vr>32767.0) vr=32767.0; else if(vr<-32767.0) vr=-32767.0;
      if(vi>32767.0) vi=32767.0; else if(vi<-32767.0) vi=-32767.0;
      qr[k]=(int16_t)vr;
      qi[k]=(int16_t)vi;
    }
  }
  return (float)sc;
}

/* Each tier's template t: the in-band part of spec ([k0, khi), wrapped to cyclic slots
   k & (m - 1) when k0 > 0; for a Hermitian-packed spectrum with k0 == 0 the Nyquist value in
   DC's imaginary part is dropped), scaled to unit expected power in the band -- by the
   reference's band fraction, or the template's own without one. Nothing unscaled is kept: a
   later reference or offset change marks the template stale, and the caller loads it again. */
static int load_tiers(ap_hmf_plan *p,int t,const float *spec){
  for(int i=0;i<p->ntiers;i++){
    hmf_tier *tr=&p->tier[i];
    double f=p->ref_on ? tr->ref_f : tr->fpow[t];
    double scale=f>0 ? 1/sqrt(f) : 0;
    if(tr->k0 == 0){
      for(size_t k=0;k<2*tr->m;k++) tr->scratch[k]=(float)(spec[k]*scale);
      if(p->is_dif && p->hermitian) tr->scratch[1]=0.0f;
    } else {
      const size_t khi = tier_khi(p,tr);
      const size_t len = khi > tr->k0 ? khi - tr->k0 : 0;
      if(len < tr->m) memset(tr->scratch,0,2*tr->m*sizeof(float));
      const size_t u0 = tr->k0 & (tr->m - 1);
      const size_t first = len < tr->m - u0 ? len : tr->m - u0;
      for(size_t k=0;k<2*first;k++)
        tr->scratch[2*u0 + k] = (float)(spec[2*tr->k0 + k]*scale);
      for(size_t k=0;k<2*(len - first);k++)
        tr->scratch[k] = (float)(spec[2*(tr->k0 + first) + k]*scale);
    }
    if(ap_mf_set_template(tr->mf,t,tr->scratch)) return -1;
    if(tr->g16 && ap_gate16_set_template(tr->g16,t,tr->scratch)) return -1;
    if(tr->qtm)
      tr->qts[t]=hmf_q15_template_row(tr->scratch,tr->m,tr->qtm+(size_t)t*(2*tr->m+32));
  }
  return 0;
}
int ap_hmf_set_reference(ap_hmf_plan *p,const float *power){
  if(!p) return -1;
  if(power){
    double total=0,low[AP_HMF_MAX_TIERS]={0};
    for(size_t k=0;k<p->k;k++){
      if(!isfinite(power[k]) || power[k]<0) return -1;
      total+=power[k];
      for(int i=0;i<p->ntiers;i++)
        if(k>=p->tier[i].k0 && k<tier_khi(p,&p->tier[i])) low[i]+=power[k];
    }
    if(total<=0) return -1;
    for(int i=0;i<p->ntiers;i++) p->tier[i].ref_f=(float)(low[i]/total);
    p->ref_on=1;
  } else p->ref_on=0;
  /* The tier templates already loaded were scaled for the old reference: stale until set
     again (a run over them fails rather than use the old scale). */
  ap_hmf_clear_tier0_clusters(p);
  ap_hmf_clear_tier1_clusters(p);
  for(int t=0;t<p->nt;t++) if(p->tready[t]==1) p->tready[t]=2;
  return 0;
}
int ap_hmf_set_sparse(ap_hmf_plan *p,int on){
  if(!p) return -1;
  p->sparse=on?1:0;
  return 0;
}
static int set_data_tiers(ap_hmf_plan *p,int d,const float *spec,int eager){
  p->dspec[d]=spec; p->dready[d]=0;
  for(int i=0;i<p->ntiers;i++){
    hmf_tier *tr=&p->tier[i];
    const unsigned char qbit = tr->qtm ? HMF_PEND_Q15 : 0u;
    if(i>=eager){
      hmf_set_pending(tr,d,(unsigned char)(HMF_PEND_MF | (tr->g16 ? HMF_PEND_G16 : 0u) | qbit));
      continue;
    }
    if(i==0 && tr->g16 && !p->q15){
      if(ingest_tier_data(p,tr,d,spec,0,1)) return -1;
      hmf_set_pending(tr,d,HMF_PEND_MF);
      continue;
    }
    if(i==0 && p->q15 && tr->g16){
      if(ingest_tier_data(p,tr,d,spec,1,0)) return -1;
      hmf_set_pending(tr,d,HMF_PEND_G16);
      continue;
    }
    if(ingest_tier_data(p,tr,d,spec,1,1)) return -1;
    hmf_set_pending(tr,d,qbit);
  }
  return 0;
}
int ap_hmf_set_data(ap_hmf_plan *p,int d,const float *spec){
  if(!p||d<0||d>=p->nd||!spec) return -1;
  /* The plan owns what it reads: the refine ingests the full spectrum lazily, long
     after this returns, so it is copied here (as the flat plan copies), not kept as the
     caller's pointer -- a caller that reused its buffer changed the refine's data. */
  const size_t row=2*p->n;
  if(!p->dcopy){
    p->dcopy=malloc((size_t)p->nd*row*sizeof(float));
    if(!p->dcopy) return -1;
  }
  float *own=p->dcopy+(size_t)d*row;
  memcpy(own,spec,row*sizeof(float));
  p->dmirrored[d]=1;
  /* Preserve the public setter's eager coarse copies. Only series calls defer
     them, because their source spectra live in the plan's own storage. */
  return set_data_tiers(p,d,own,p->ntiers);
}
int ap_hmf_set_template(ap_hmf_plan *p,int t,const float *spec){
  if(!p||t<0||t>=p->nt||!spec) return -1;
  if(p->tier0_clustered) ap_hmf_clear_tier0_clusters(p);
  if(p->tier1_clustered) ap_hmf_clear_tier1_clusters(p);
  if(p->is_dif){
    if(p->tmpls_half && spec!=p->tmpls_half+(size_t)t*2*p->k)
      memcpy(p->tmpls_half+(size_t)t*2*p->k,spec,2*p->k*sizeof(float));
    if(!p->hermitian && ap_mf_set_template(p->full,t,spec)) return -1;
  } else {
    if(ap_mf_set_template(p->full,t,spec)) return -1;
  }
  double total=0,low[AP_HMF_MAX_TIERS]={0};
  if(p->is_dif && p->hermitian){
    double dc_pow=(double)spec[0]*(double)spec[0];
    double nyq_pow=(double)spec[1]*(double)spec[1];
    double pos_pow=0.0;
    for(size_t k=1;k<p->k;k++){
      double re=spec[2*k],im=spec[2*k+1];
      double pwr=re*re+im*im;
      pos_pow+=pwr;
      for(int i=0;i<p->ntiers;i++)
        if(k>=p->tier[i].k0 && k<tier_khi(p,&p->tier[i])) low[i]+=pwr;
    }
    total=dc_pow+nyq_pow+2.0*pos_pow;
    for(int i=0;i<p->ntiers;i++) if(p->tier[i].k0==0) low[i]+=dc_pow;
  } else {
    for(size_t k=0;k<p->k;k++){
      double re=spec[2*k],im=spec[2*k+1],power=re*re+im*im;
      total+=power;
      for(int i=0;i<p->ntiers;i++)
        if(k>=p->tier[i].k0 && k<tier_khi(p,&p->tier[i])) low[i]+=power;
    }
  }
  for(int i=0;i<p->ntiers;i++){
    hmf_tier *tr=&p->tier[i];
    tr->fpow[t]=total>0 ? (float)(low[i]/total) : 0;
  }
  p->tready[t]=1;
  return load_tiers(p,t,spec);
}

static void hmf_free_tier0_clusters(ap_hmf_plan *p){
  if(!p) return;
  if(p->tier0_mf){ ap_mf_destroy(p->tier0_mf); p->tier0_mf=NULL; }
  if(p->tier0_g16){ ap_gate16_destroy(p->tier0_g16); p->tier0_g16=NULL; }
  free(p->tier0_off); p->tier0_off=NULL;
  free(p->tier0_members); p->tier0_members=NULL;
  free(p->tier0_uncl_pend); p->tier0_uncl_pend=NULL;
  p->tier0_clustered=0;
  p->tier0_nt=0;
  p->tier0_lag_pad=0;
}

static void hmf_free_tier1_clusters(ap_hmf_plan *p){
  if(!p) return;
  if(p->tier1_mf){ ap_mf_destroy(p->tier1_mf); p->tier1_mf=NULL; }
  if(p->tier1_g16){ ap_gate16_destroy(p->tier1_g16); p->tier1_g16=NULL; }
  free(p->tier1_qtm); p->tier1_qtm=NULL;
  free(p->tier1_qts); p->tier1_qts=NULL;
  free(p->tier1_off); p->tier1_off=NULL;
  free(p->tier1_members); p->tier1_members=NULL;
  free(p->tier1_map); p->tier1_map=NULL;
  free(p->tier1_uncl_pend); p->tier1_uncl_pend=NULL;
  p->tier1_clustered=0;
  p->tier1_nt=0;
  p->tier1_lag_pad=0;
}

static int hmf_sync_unclustered_tier0(ap_hmf_plan *p,int d0,int nd){
  if(!p->tier0_uncl_pend || p->ntiers<1) return 0;
  hmf_tier *tr=&p->tier[0];
  for(int d=d0;d<d0+nd;d++){
    if(p->tier0_uncl_pend[d]){
      if(p->dspec[d]){
        const int to_mf=(p->q15 || !tr->g16 || !(tr->pending[d] & HMF_PEND_MF)) ? 1 : 0;
        if(ingest_tier_data_target(p,tr,tr->mf,tr->g16,d,p->dspec[d],to_mf,1)) return -1;
      }
      p->tier0_uncl_pend[d]=0;
    }
  }
  return 0;
}

static int hmf_sync_unclustered_tier1(ap_hmf_plan *p,int d0,int nd){
  if(!p->tier1_uncl_pend || p->ntiers<2) return 0;
  hmf_tier *tr=&p->tier[1];
  for(int d=d0;d<d0+nd;d++){
    if(p->tier1_uncl_pend[d]){
      if(p->dspec[d]){
        const int to_mf=(p->q15 || !tr->g16 || !(tr->pending[d] & HMF_PEND_MF)) ? 1 : 0;
        if(ingest_tier_data_target(p,tr,tr->mf,tr->g16,d,p->dspec[d],to_mf,1)) return -1;
      }
      p->tier1_uncl_pend[d]=0;
    }
  }
  return 0;
}

void ap_hmf_clear_tier0_clusters(ap_hmf_plan *p){
  if(!p || !p->tier0_clustered) return;
  /* Tier-1 sub-centroids are only valid nested inside an active Tier-0 partition: a firing
     Tier-1 centroid passes all its members on, which equals the unclustered tier only when
     each of them came out of the same firing Tier-0 centroid. */
  ap_hmf_clear_tier1_clusters(p);
  (void)hmf_sync_unclustered_tier0(p,0,p->nd);
  hmf_free_tier0_clusters(p);
}

void ap_hmf_clear_tier1_clusters(ap_hmf_plan *p){
  if(!p || !p->tier1_clustered) return;
  (void)hmf_sync_unclustered_tier1(p,0,p->nd);
  hmf_free_tier1_clusters(p);
}

int ap_hmf_tier0_cluster_count(const ap_hmf_plan *p){
  return (p && p->tier0_clustered) ? p->tier0_nt : 0;
}

int ap_hmf_tier1_cluster_count(const ap_hmf_plan *p){
  return (p && p->tier1_clustered) ? p->tier1_nt : 0;
}

/* Whether (offsets, members) is a partition of [0, nt) into nc nonempty clusters: CSR offsets
   from 0 to nt, strictly increasing, and every template exactly once. */
static int hmf_valid_partition(int nt,int nc,const int *offsets,const int *members){
  if(nc<1 || nc>nt || offsets[0]!=0 || offsets[nc]!=nt) return 0;
  unsigned char *seen=calloc((size_t)nt,1);
  if(!seen) return 0;
  int ok=1;
  for(int c=0;ok && c<nc;c++){
    if(offsets[c]>=offsets[c+1]){ ok=0; break; }
    for(int m=offsets[c];m<offsets[c+1];m++){
      const int t=members[m];
      if(t<0 || t>=nt || seen[t]){ ok=0; break; }
      seen[t]=1;
    }
  }
  free(seen);
  return ok;
}

/* The coarse plans of a centroid bank at band m: a pair-batched FP32 plan where nc fills a
   vector and m is within the pair-batch limit (as hmf_create_tier sizes a tier's), else a
   plain one, and the FP16 gate where this build has it. Every centroid spectrum is loaded. */
static int hmf_cluster_plans(ap_hmf_plan *p,size_t m,int nc,const float *specs,
                             ap_mf_plan **out_mf,void **out_g16){
  const long pbmax=ap_env_int("MF_PBMAX",-1);
  const int lw=ap_lane_width();
  const size_t pblim=pbmax>=0 ? (size_t)pbmax : (lw>=16 ? 1024u : 512u);
  const size_t min_ntmpl=(lw>0) ? (size_t)lw : 16u;
  ap_mf_plan *cmf=NULL;
  if((size_t)nc>=min_ntmpl && m<=pblim) cmf=ap_mf_create_pairbatch(m,p->nd,nc);
  if(!cmf) cmf=ap_mf_create(m,p->nd,nc);
  void *cg16=ap_gate16_available() ? ap_gate16_create(m,p->nd,nc) : NULL;
  int ok = cmf && (!ap_gate16_available() || cg16);
  for(int c=0;ok && c<nc;c++){
    const float *cspec=specs+(size_t)c*2*m;
    if(ap_mf_set_template(cmf,c,cspec) || (cg16 && ap_gate16_set_template(cg16,c,cspec))) ok=0;
  }
  if(!ok){
    if(cmf) ap_mf_destroy(cmf);
    if(cg16) ap_gate16_destroy(cg16);
    return -1;
  }
  if(p->q15) ap_mf_set_q15_margin(cmf,0);
  *out_mf=cmf;
  *out_g16=cg16;
  return 0;
}

/* Ingest the data rows this plan holds its own copy of into a newly built centroid bank of
   tier tr (rows the caller keeps arrive again with its next call). */
static int hmf_cluster_replay_data(ap_hmf_plan *p,hmf_tier *tr,ap_mf_plan *cmf,void *cg16){
  if(!p->dcopy) return 0;
  const size_t row=2*p->n;
  for(int d=0;d<p->nd;d++){
    if(p->dmirrored[d] && p->dspec[d]==p->dcopy+(size_t)d*row){
      const int to_mf=(p->q15 || !cg16) ? 1 : 0;
      if(ingest_tier_data_target(p,tr,cmf,cg16,d,p->dcopy+(size_t)d*row,to_mf,1)) return -1;
      if(!to_mf) hmf_set_pending(tr,d,HMF_PEND_MF);
    }
  }
  return 0;
}

int ap_hmf_set_tier0_clusters(ap_hmf_plan *p,int nc,const float *specs,
                              const int *offsets,const int *members,int lag_pad){
  if(!p || p->ntiers<1 || p->hermitian || !specs || !offsets || !members) return -1;
  if(lag_pad<0 || (size_t)lag_pad>=p->tier[0].m) return -1;
  if(!hmf_valid_partition(p->nt,nc,offsets,members)) return -1;

  ap_hmf_clear_tier0_clusters(p);

  ap_mf_plan *cmf=NULL;
  void *cg16=NULL;
  if(hmf_cluster_plans(p,p->tier[0].m,nc,specs,&cmf,&cg16)) return -1;
  int *coff=malloc((size_t)(nc+1)*sizeof(int));
  int *cmem=malloc((size_t)p->nt*sizeof(int));
  unsigned char *cpend=calloc((size_t)p->nd,1);
  if(!coff || !cmem || !cpend){
    ap_mf_destroy(cmf);
    if(cg16) ap_gate16_destroy(cg16);
    free(coff); free(cmem); free(cpend);
    return -1;
  }
  memcpy(coff,offsets,(size_t)(nc+1)*sizeof(int));
  memcpy(cmem,members,(size_t)p->nt*sizeof(int));
  p->tier0_mf=cmf;
  p->tier0_g16=cg16;
  p->tier0_off=coff;
  p->tier0_members=cmem;
  p->tier0_uncl_pend=cpend;
  p->tier0_nt=nc;
  p->tier0_lag_pad=lag_pad;
  p->tier0_clustered=1;

  if(hmf_cluster_replay_data(p,&p->tier[0],cmf,cg16)){
    ap_hmf_clear_tier0_clusters(p);
    return -1;
  }
  return 0;
}

int ap_hmf_set_tier1_clusters(ap_hmf_plan *p,int nc,const float *specs,
                              const int *offsets,const int *members,int lag_pad){
  if(!p || p->ntiers<2 || p->hermitian || !specs || !offsets || !members) return -1;
  if(lag_pad<0 || (size_t)lag_pad>=p->tier[1].m) return -1;
  if(!p->tier0_clustered || !hmf_valid_partition(p->nt,nc,offsets,members)) return -1;
  /* Every Tier-1 cluster must lie inside one Tier-0 cluster (see ap_hmf_clear_tier0_clusters). */
  int *t0of=malloc((size_t)p->nt*sizeof(int));
  if(!t0of) return -1;
  for(int c=0;c<p->tier0_nt;c++)
    for(int u=p->tier0_off[c];u<p->tier0_off[c+1];u++) t0of[p->tier0_members[u]]=c;
  int nested=1;
  for(int c=0;nested && c<nc;c++)
    for(int u=offsets[c]+1;u<offsets[c+1];u++)
      if(t0of[members[u]]!=t0of[members[offsets[c]]]){ nested=0; break; }
  free(t0of);
  if(!nested) return -1;

  ap_hmf_clear_tier1_clusters(p);

  const size_t m1=p->tier[1].m;
  ap_mf_plan *cmf=NULL;
  void *cg16=NULL;
  if(hmf_cluster_plans(p,m1,nc,specs,&cmf,&cg16)) return -1;
  const int want_q15=ap_mf_q15_lanes(cmf)>0;
  int16_t *cqtm=want_q15 ? ap_alloc64((size_t)nc*(2*m1+32)*sizeof(int16_t)) : NULL;
  float *cqts=want_q15 ? calloc((size_t)nc,sizeof(float)) : NULL;
  int *coff=malloc((size_t)(nc+1)*sizeof(int));
  int *cmem=malloc((size_t)p->nt*sizeof(int));
  int *cmap=malloc((size_t)p->nt*sizeof(int));
  unsigned char *cpend=calloc((size_t)p->nd,1);
  if((want_q15 && (!cqtm || !cqts)) || !coff || !cmem || !cmap || !cpend){
    ap_mf_destroy(cmf);
    if(cg16) ap_gate16_destroy(cg16);
    free(cqtm); free(cqts); free(coff); free(cmem); free(cmap); free(cpend);
    return -1;
  }
  for(int c=0;c<nc;c++){
    if(cqtm) cqts[c]=hmf_q15_template_row(specs+(size_t)c*2*m1,m1,cqtm+(size_t)c*(2*m1+32));
    for(int u=offsets[c];u<offsets[c+1];u++) cmap[members[u]]=c;
  }
  memcpy(coff,offsets,(size_t)(nc+1)*sizeof(int));
  memcpy(cmem,members,(size_t)p->nt*sizeof(int));
  p->tier1_mf=cmf;
  p->tier1_g16=cg16;
  p->tier1_qtm=cqtm;
  p->tier1_qts=cqts;
  p->tier1_off=coff;
  p->tier1_members=cmem;
  p->tier1_map=cmap;
  p->tier1_uncl_pend=cpend;
  p->tier1_nt=nc;
  p->tier1_lag_pad=lag_pad;
  p->tier1_clustered=1;

  if(hmf_cluster_replay_data(p,&p->tier[1],cmf,cg16)){
    ap_hmf_clear_tier1_clusters(p);
    return -1;
  }
  return 0;
}

/* The fewest pairs a later tier screens with the arbitrary-pair Q15 gather (ql lanes): it pools
   survivors across SIMD lanes without slab or template-group bucketing, and pays for its data
   quantisation once nfire exceeds one FP32 vector (ql/2). Below that the tier runs in FP32. */
static inline long hmf_min_q15_pairs(int ql){ return ql > 1 ? ql / 2 + 1 : 1; }

static int hmf_run_tier0_clustered(ap_hmf_plan *p,int d0,int nd,int fast_sparse,size_t nb,
                                   ap_peak *peaks,int *counts,size_t start,size_t end,
                                   const int **out_fire_d,const int **out_fire_t,int *out_nfire);
static int hmf_run_tier1_clustered(ap_hmf_plan *p,int d0,int fast_sparse,size_t nb,
                                   ap_peak *peaks,int *counts,size_t start,size_t end,
                                   const int *in_d,const int *in_t,int nin,
                                   const int **out_fire_d,const int **out_fire_t,int *out_nfire);

int ap_hmf_set_real_series(ap_hmf_plan *p,int on){
  if(!p) return -1;
  if(on && !p->half_fft){
    const size_t h=p->n/2;
    if(p->n<4 || !ap_supported(h)) return -1;
    p->half_fft=ap_create_like(p->full_fft,h);     /* the plan's own kernel */
    p->rtw=malloc(2*(h+1)*sizeof(float));
    if(!p->half_fft||!p->rtw){
      if(p->half_fft) ap_destroy(p->half_fft);
      free(p->rtw); p->half_fft=NULL; p->rtw=NULL; return -1;
    }
    for(size_t k=0;k<=h;k++){
      const double a=2.0*3.14159265358979323846*(double)k/(double)p->n;
      p->rtw[2*k]=(float)cos(a); p->rtw[2*k+1]=(float)sin(a);
    }
    if(h>=64 && h<=hmf_fwd_pb_limit(p))
      p->fwd_real_batch=ap_create_pairbatch_like(p->full_fft,h);
  }
  p->real_series=on?1:0;
  if(!p->real_stride) p->real_stride=1;
  return 0;
}
int ap_hmf_set_real_stride(ap_hmf_plan *p,size_t stride){
  if(!p || stride<1 || stride>2) return -1;
  p->real_stride=stride;
  return 0;
}

#include "hmf.h"

/* The real block at x[s0 .. s0+have) zero-padded to n and scaled by 1/n, transformed into
   non-negative bins 0 .. n/2 of sp: the n reals read as n/2 complex z, Z = FFT_{n/2}(z), then
   X[k] = E[k] + W^k O[k] for k = 0 .. n/2. Negative bins are mirrored lazily on blocks that
   take the transform refine (hmf_refine_fft). */
static void hmf_forward_real(ap_hmf_plan *p,const float *x,size_t s0,size_t have,float *sp){
  const size_t n=p->n;
  const float inv=1.0f/(float)n;
  const size_t st=p->real_stride ? p->real_stride : 1;
  float * restrict Z=p->fwd+n;               /* the h-point transform */
  ap_fft_forward_scaled(p->half_fft,have ? x+s0*st : x,have,st,inv,Z);
  ap_real_split_pos_on(p->half_fft,Z,p->rtw,n,sp);
}

/* Transform blocks start[b0 .. b0+g) of series into p->spec slots 0 .. g-1 and ingest tier 0. */
static int hmf_forward_slab(ap_hmf_plan *p,const float *series,size_t nseries,
                            const size_t *start,int b0,int g){
  const size_t n=p->n;
  const size_t sstride=2*n+16;
  const size_t pblim=hmf_fwd_pb_limit(p);
  if(p->real_series && !p->fwd_real_batch && p->half_fft && n>=128 && n/2<=pblim)
    p->fwd_real_batch=ap_create_pairbatch_like(p->full_fft,n/2);
  if(!p->real_series && !p->fwd_cplx_batch && p->full_fft && n>=64 && n<=pblim)
    p->fwd_cplx_batch=ap_create_pairbatch_like(p->full_fft,n);
  const size_t st_real = p->real_stride ? p->real_stride : 1;
  const int w_real = p->fwd_real_batch ? ap_plan_lanes(p->fwd_real_batch) : 0;
  const int use_real_batch = (w_real > 0 && n <= 4096);
  if(p->real_series && p->fwd_real_batch && use_real_batch){
    const int W = w_real;
    const size_t st = st_real;
    const float inv = 1.0f/(float)n;
    for(int j=0; j<g; j+=W){
      const int cnt = g-j<W ? g-j : W;
      const float *srcs[AP_MAX_LANES];
      size_t haves[AP_MAX_LANES];
      float *outs[AP_MAX_LANES];
      for(int l=0; l<cnt; l++){
        const size_t s0=start[b0+j+l];
        size_t have = s0<nseries ? nseries-s0 : 0;
        if(have>n) have=n;
        srcs[l]=have ? series+s0*st : series;
        haves[l]=have;
        outs[l]=p->spec+(size_t)(j+l)*sstride;
      }
      if(ap_fft_real_batch(p->fwd_real_batch,srcs,haves,st,cnt,inv,p->rtw,0,outs)<0) return -1;
      for(int l=0; l<cnt; l++){
        p->dmirrored[j+l]=0;
        if(set_data_tiers(p,j+l,outs[l],1)) return -1;
        p->dtime[j+l]=haves[l] ? srcs[l] : NULL; p->dhave[j+l]=haves[l];
      }
    }
  } else if(!p->real_series && p->fwd_cplx_batch){
    /* Band-limited/Hermitian plans (is_dif) and direct time-domain refine plans read only
       [0, n/2) in coarse gates, lazily completing [0, n) in hmf_refine_fft only on blocks whose
       survivor needs full-spectrum FFT refine. Unpacked FFT-refine plans emit all n bins in the
       SIMD batch to avoid per-block scalar re-transforms and keep refine calibration clean. */
    const int W = ap_plan_lanes(p->fwd_cplx_batch);
    const float inv = 1.0f/(float)n;
    const int half_prefix = n>=256u && (p->is_dif || (p->direct && p->taps));
    const size_t out_bins = half_prefix ? n/2u : n;
    const unsigned char full_done = half_prefix ? 0u : 1u;
    for(int j=0; j<g; j+=W){
      const int cnt = g-j<W ? g-j : W;
      const float *srcs[AP_MAX_LANES];
      size_t haves[AP_MAX_LANES];
      float *outs[AP_MAX_LANES];
      for(int l=0; l<cnt; l++){
        const size_t s0=start[b0+j+l];
        size_t have = s0<nseries ? nseries-s0 : 0;
        if(have>n) have=n;
        srcs[l]=have ? series+2*s0 : series;
        haves[l]=have;
        outs[l]=p->spec+(size_t)(j+l)*sstride;
      }
      if(ap_fft_forward_batch_prefix(p->fwd_cplx_batch,srcs,haves,cnt,inv,out_bins,outs)<0)
        return -1;
      for(int l=0; l<cnt; l++){
        p->dmirrored[j+l]=full_done;
        if(set_data_tiers(p,j+l,outs[l],1)) return -1;
        p->dtime[j+l]=haves[l] ? srcs[l] : NULL; p->dhave[j+l]=haves[l];
      }
    }
  } else for(int j=0;j<g;j++){
    const size_t s0=start[b0+j];
    size_t have = s0<nseries ? nseries-s0 : 0;
    if(have>n) have=n;
    if(p->real_series){
      /* A real series: the half-size transform (half-spectrum; negative bins mirrored lazily
         on transform refine), with real block samples kept for direct refine. */
      const size_t st=p->real_stride ? p->real_stride : 1;
      float *sp=p->spec+(size_t)j*sstride;
      hmf_forward_real(p,series,s0,have,sp);
      p->dmirrored[j]=0;
      if(set_data_tiers(p,j,sp,1)) return -1;
      p->dtime[j]=have ? series+s0*st : NULL; p->dhave[j]=have;
      continue;
    }
    /* pycbc's inverse is unnormalised and so is matchedfilter's, so the
       caller's convention of pre-dividing the block spectrum by n is kept.
       Doing it on the way IN rather than to the result folds it into a copy
       that has to happen anyway and removes a separate pass over 2n floats
       -- 12% of the per-block cost, which is itself 12% of the total at 37
       templates.  n is a power of two, so 1/n is exact and the transform is
       linear: scaling before is bit-for-bit the same as scaling after, which
       the fixtures check by reproducing pycbc's SNRs to 0.0e+00. */
    float *const sp=p->spec+(size_t)j*sstride;
    ap_fft_forward_scaled(p->full_fft,have ? series+2*s0 : series,2*have,1,1.0f/(float)n,sp);
    p->dmirrored[j]=1;
    if(set_data_tiers(p,j,sp,1)) return -1;
    p->dtime[j]=have ? series+2*s0 : NULL; p->dhave[j]=have;
    /* The full spectrum is NOT ingested here.  Only the coarse band is read
       by every pair; the full one is read only when a pair fires, which at
       threshold 5.5 is 0.1% of pairs and so about 4% of blocks.  Ingesting
       it eagerly costs 0.4-1.0 us a block for nothing on the rest.  What
       forced it was that one staging buffer was reused by the next block,
       so set_data's retained pointer went stale; giving the group a buffer
       per slot removes that and lets ap_hmf_run's existing lazy path do it
       on demand.  dready stays 0 to say so. */
  }
  return 0;
}

int ap_hmf_run_series(ap_hmf_plan *p,
                      const float *series,size_t nseries,
                      const size_t *start,const size_t *win_start,
                      const size_t *win_end,const unsigned *bin_phase,int nblocks,
                      int t0,int nt,size_t binsize,float threshold,
                      ap_peak *peaks,int *counts){
  if(!p||nblocks<1||nt<1||!binsize) return 0;
  if(!ap_range_ok(t0,nt,p->nt)) return -1;
  const unsigned long long call0=ap_ticks();
  const size_t nb0=hmf_nbins_phased(p,binsize,win_start[0],win_end[0],
                                    bin_phase?bin_phase[0]:0u);
  int total=0;
  /* Filter several blocks together where they share a window.  Blocks differ
     only at a segment's edges, so runs of equal windows are long. */
  for(int b0=0;b0<nblocks;){
    int g=1;
    while(g<p->dgroup && b0+g<nblocks
          && win_start[b0+g]==win_start[b0] && win_end[b0+g]==win_end[b0]) g++;
    if(hmf_forward_slab(p,series,nseries,start,b0,g)<0) return -1;
    /* peaks is addressed at a single stride, so every window must produce the
       same bin count. A shorter one at a segment's edge does not: it writes
       where the next block's row begins and runs off the end of the caller's
       buffer -- heap corruption from ordinary overlap-save input, since edge
       blocks are exactly the ragged ones this call exists to accept.
       Refusing is the honest answer; the shape the API returns has one nbins
       in it and cannot express two. */
    for(int j=0;j<g;j++)
      if(hmf_nbins_phased(p,binsize,win_start[b0+j],win_end[b0+j],
                          bin_phase?bin_phase[b0+j]:0u)!=nb0){
        for(int u=0;u<g;u++) p->dtime[u]=NULL;
        return -1;
      }
    p->bph = bin_phase ? bin_phase+b0 : NULL;    /* rows 0..g-1 are blocks b0..b0+g-1 */
    int r=ap_hmf_run(p,0,g,t0,nt,binsize,threshold,
                     peaks+(size_t)b0*nt*nb0,counts?counts+(size_t)b0*nt:NULL,
                     win_start[b0],win_end[b0]);
    p->bph = NULL;
    for(int j=0;j<g;j++) p->dtime[j]=NULL;   /* the caller's series is not held past the call */
    if(r<0) return -1;
    total+=r;
    b0+=g;
  }
  p->c_series += ap_ticks()-call0;
  return total;
}

static int hmf_slab_len(const ap_hmf_sparse_job *jb,int b0,size_t nb0){
  int g=1;
  while(g<jb->p->dgroup && b0+g<jb->nblocks
        && jb->win_start[b0+g]==jb->win_start[b0]
        && jb->win_end[b0+g]==jb->win_end[b0]) g++;
  for(int j=0;j<g;j++)
    if(hmf_nbins_phased(jb->p,jb->binsize,jb->win_start[b0+j],jb->win_end[b0+j],
                        jb->bin_phase?jb->bin_phase[b0+j]:0u)!=nb0) return -1;
  return g;
}

static int hmf_forward_real_minibatch(ap_hmf_plan *p,const float *series,size_t nseries,
                                      const size_t *start,int b0,int j,int cnt){
  const size_t n=p->n;
  const size_t sstride=2u*n+16u;
  const size_t st=p->real_stride ? p->real_stride : 1u;
  const float inv=1.0f/(float)n;
  const float *srcs[AP_MAX_LANES];
  size_t haves[AP_MAX_LANES];
  float *outs[AP_MAX_LANES];
  for(int l=0;l<cnt;l++){
    const size_t s0=start[b0+j+l];
    size_t have = s0<nseries ? nseries-s0 : 0;
    if(have>n) have=n;
    srcs[l]=have ? series+s0*st : series;
    haves[l]=have;
    outs[l]=p->spec+(size_t)(j+l)*sstride;
  }
  const unsigned long long t0=ap_ticks();
  if(ap_fft_real_batch(p->fwd_real_batch,srcs,haves,st,cnt,inv,p->rtw,0,outs)<0) return -1;
  for(int l=0;l<cnt;l++){
    p->dmirrored[j+l]=0;
    if(set_data_tiers(p,j+l,outs[l],1)) return -1;
    p->dtime[j+l]=haves[l] ? srcs[l] : NULL;
    p->dhave[j+l]=haves[l];
  }
  p->c_series += ap_ticks()-t0;
  return 0;
}

/* Transform two packed strided real lanes (even/odd floats of one complex64 series) together
   while shared cache lines stay hot in L1/L2: identical block starts fuse into single-load
   ap_fft_quad_pair_batch calls, while unequal block starts interleave W-block mini-batches
   before either fine bank sweeps its template spectra. */
static int hmf_forward_slab_quad_pair(ap_hmf_plan *pa,const float *sa,
                                      const size_t *start_a,int b0a,int ga,
                                      ap_hmf_plan *pb,const float *sb,
                                      const size_t *start_b,int b0b,int gb,
                                      size_t nseries){
  const size_t na=pa->n, nb=pb->n;
  const size_t pblim_a=hmf_fwd_pb_limit(pa);
  const size_t pblim_b=hmf_fwd_pb_limit(pb);
  if(!pa->fwd_real_batch && pa->half_fft && na>=128 && na/2<=pblim_a)
    pa->fwd_real_batch=ap_create_pairbatch_like(pa->full_fft,na/2);
  if(!pb->fwd_real_batch && pb->half_fft && nb>=128 && nb/2<=pblim_b)
    pb->fwd_real_batch=ap_create_pairbatch_like(pb->full_fft,nb/2);
  const int wa = (pa->fwd_real_batch && na<=4096) ? ap_plan_lanes(pa->fwd_real_batch) : 0;
  const int wb = (pb->fwd_real_batch && nb<=4096) ? ap_plan_lanes(pb->fwd_real_batch) : 0;
  if(na==nb && ga==gb && wa>=2 && wa==wb && (sb==sa+1 || sa==sb+1)
     && memcmp(start_a+b0a,start_b+b0b,(size_t)ga*sizeof(size_t))==0){
    const size_t sstride=2u*na+16u;
    const int H = wa / 2;
    const int swap = (sa == sb + 1);
    const float *zbase = swap ? sb : sa;
    const float inv = 1.0f/(float)na;
    for(int j=0;j<ga;j+=H){
      const int cnt = ga-j<H ? ga-j : H;
      const float *zsrcs[AP_MAX_LANES], *srca[AP_MAX_LANES], *srcb[AP_MAX_LANES];
      size_t haves[AP_MAX_LANES];
      float *outa[AP_MAX_LANES], *outb[AP_MAX_LANES];
      for(int l=0;l<cnt;l++){
        const size_t s0=start_a[b0a+j+l];
        size_t have = s0<nseries ? nseries-s0 : 0;
        if(have>na) have=na;
        zsrcs[l]=have ? zbase+2u*s0 : zbase;
        srca[l]=have ? sa+2u*s0 : sa;
        srcb[l]=have ? sb+2u*s0 : sb;
        haves[l]=have;
        outa[l]=pa->spec+(size_t)(j+l)*sstride;
        outb[l]=pb->spec+(size_t)(j+l)*sstride;
      }
      const unsigned long long t0=ap_ticks();
      if(ap_fft_quad_pair_batch(pa->fwd_real_batch,zsrcs,haves,cnt,inv,pa->rtw,
                                swap ? outb : outa,swap ? outa : outb)<0)
        return -1;
      const unsigned long long t1=ap_ticks();
      const unsigned long long dt = t1 - t0;
      pa->c_series += dt / 2u;
      pb->c_series += dt - dt / 2u;
      for(int l=0;l<cnt;l++){
        pa->dmirrored[j+l]=0;
        if(set_data_tiers(pa,j+l,outa[l],1)) return -1;
        pa->dtime[j+l]=haves[l] ? srca[l] : NULL; pa->dhave[j+l]=haves[l];
      }
      const unsigned long long t2=ap_ticks();
      pa->c_series += t2-t1;
      for(int l=0;l<cnt;l++){
        pb->dmirrored[j+l]=0;
        if(set_data_tiers(pb,j+l,outb[l],1)) return -1;
        pb->dtime[j+l]=haves[l] ? srcb[l] : NULL; pb->dhave[j+l]=haves[l];
      }
      pb->c_series += ap_ticks()-t2;
    }
    return 0;
  }
  if(wa>0 && wb>0 && (sb==sa+1 || sa==sb+1)){
    int ja=0, jb=0;
    while(ja<ga || jb<gb){
      if(ja<ga && (jb>=gb || start_a[b0a+ja]<=start_b[b0b+jb])){
        const int cnt = ga-ja<wa ? ga-ja : wa;
        if(hmf_forward_real_minibatch(pa,sa,nseries,start_a,b0a,ja,cnt)<0) return -1;
        ja+=cnt;
      } else {
        const int cnt = gb-jb<wb ? gb-jb : wb;
        if(hmf_forward_real_minibatch(pb,sb,nseries,start_b,b0b,jb,cnt)<0) return -1;
        jb+=cnt;
      }
    }
    return 0;
  }
  const unsigned long long t0=ap_ticks();
  if(hmf_forward_slab(pa,sa,nseries,start_a,b0a,ga)<0) return -1;
  const unsigned long long t1=ap_ticks();
  pa->c_series += t1-t0;
  if(hmf_forward_slab(pb,sb,nseries,start_b,b0b,gb)<0) return -1;
  pb->c_series += ap_ticks()-t1;
  return 0;
}

static int hmf_job_win_ok(const ap_hmf_sparse_job *jb,int b0,int g,size_t nb){
  for(int j=0;j<g;j++){
    if(jb->win_start[b0+j]!=jb->win_start[b0]
       || jb->win_end[b0+j]!=jb->win_end[b0]
       || hmf_nbins_phased(jb->p,jb->binsize,jb->win_start[b0+j],jb->win_end[b0+j],
                           jb->bin_phase?jb->bin_phase[b0+j]:0u)!=nb)
      return 0;
  }
  return 1;
}

static int hmf_run_sparse_slab(ap_hmf_sparse_job *jb,size_t *cap,int b0,int g,size_t nb0,
                               ap_peak *slab_pk,int *slab_cnt){
  ap_hmf_plan *p=jb->p;
  int *cnt_ptr = jb->counts ? jb->counts+(size_t)b0*(size_t)jb->nt : slab_cnt;
  const size_t wend = jb->win_end[b0]>p->n ? p->n : jb->win_end[b0];
  if(jb->counts && jb->win_start[b0]>=wend)
    memset(cnt_ptr,0,(size_t)g*(size_t)jb->nt*sizeof(int));
  const hmf_tier *ltr=&p->tier[p->ntiers-1];
  const long prev_passed=ltr->passed;
  const unsigned long long t_run=ap_ticks();
  p->sparse = jb->counts ? 1 : 2;
  p->bph = jb->bin_phase ? jb->bin_phase+b0 : NULL;
  const int r=ap_hmf_run(p,0,g,jb->t0,jb->nt,jb->binsize,jb->threshold,
                         slab_pk,cnt_ptr,jb->win_start[b0],jb->win_end[b0]);
  p->bph = NULL;
  p->sparse = 0;
  p->c_series += ap_ticks()-t_run;
  if(r<0) return -1;
  jb->total += r;
  const int nfire=(int)(ltr->passed-prev_passed);
  if(r>0 && nfire>0){
    for(int f=0;f<nfire;f++){
      const int d=ltr->fire_d[f], t=ltr->fire_t[f];
      const size_t lrow=(size_t)d*(size_t)jb->nt+(size_t)t;
      if(cnt_ptr[lrow]<=0) continue;
      const size_t grow=((size_t)b0+(size_t)d)*(size_t)jb->nt+(size_t)t;
      const ap_peak *row_pk=slab_pk+lrow*nb0;
      for(size_t b=0;b<nb0;b++){
        if(row_pk[b].index<0) continue;
        if(jb->out_count==*cap){
          const size_t ncap = *cap ? (*cap)*2u : 64u;
          int64_t *nf=realloc(jb->out_flat,ncap*sizeof(int64_t));
          int64_t *ni=realloc(jb->out_idx,ncap*sizeof(int64_t));
          float *nv=realloc(jb->out_val,2u*ncap*sizeof(float));
          if(!nf||!ni||!nv){
            if(nf) jb->out_flat=nf;
            if(ni) jb->out_idx=ni;
            if(nv) jb->out_val=nv;
            return -1;
          }
          jb->out_flat=nf; jb->out_idx=ni; jb->out_val=nv; *cap=ncap;
        }
        const size_t m=jb->out_count++;
        jb->out_flat[m]=(int64_t)(grow*nb0+b);
        jb->out_idx[m]=(int64_t)row_pk[b].index;
        jb->out_val[2u*m]=row_pk[b].re;
        jb->out_val[2u*m+1u]=row_pk[b].im;
      }
    }
  }
  return 0;
}

int ap_hmf_run_series_batch_sparse(ap_hmf_sparse_job *jobs,int njobs){
  if(!jobs || njobs<0) return -1;
  if(njobs==0) return 0;
  for(int i=0;i<njobs;i++){
    jobs[i].out_flat=NULL; jobs[i].out_idx=NULL; jobs[i].out_val=NULL;
    jobs[i].out_count=0; jobs[i].total=0;
  }
  size_t *nb0=calloc((size_t)njobs,sizeof(size_t));
  size_t *caps=calloc((size_t)njobs,sizeof(size_t));
  int *b0=calloc((size_t)njobs,sizeof(int));
  ap_peak *slab_pk=NULL;
  int *slab_cnt=NULL;
  if(!nb0||!caps||!b0) goto fail;

  size_t max_pk=1, max_cnt=1;
  for(int i=0;i<njobs;i++){
    const ap_hmf_sparse_job *jb=&jobs[i];
    if(!jb->p || jb->nt<1 || !jb->binsize || !ap_range_ok(jb->t0,jb->nt,jb->p->nt)) goto fail;
    if(jb->nblocks<1) continue;
    nb0[i]=hmf_nbins_phased(jb->p,jb->binsize,jb->win_start[0],jb->win_end[0],
                            jb->bin_phase?jb->bin_phase[0]:0u);
    if(!nb0[i]) goto fail;
    const size_t rc=(size_t)jb->p->dgroup*(size_t)jb->nt;
    if(nb0[i] > SIZE_MAX/sizeof(ap_peak)/rc) goto fail;
    if(rc*nb0[i]>max_pk) max_pk=rc*nb0[i];
    if(rc>max_cnt) max_cnt=rc;
  }
  slab_pk=ap_alloc64(max_pk*sizeof(ap_peak));
  slab_cnt=malloc(max_cnt*sizeof(int));
  if(!slab_pk||!slab_cnt) goto fail;

  for(int c0=0;c0<njobs;){
    int c1=c0+1;
    while(c1<njobs && jobs[c1].cluster_id==jobs[c0].cluster_id) c1++;
    if(c1==c0+1){
      ap_hmf_sparse_job *jb=&jobs[c0];
      ap_hmf_plan *p=jb->p;
      for(int cur=0;cur<jb->nblocks;){
        const int g=hmf_slab_len(jb,cur,nb0[c0]);
        const unsigned long long t_fwd=ap_ticks();
        if(g<0 || hmf_forward_slab(p,jb->series,jb->nseries,jb->start,cur,g)<0) goto fail;
        p->c_series += ap_ticks()-t_fwd;
        const int rc=hmf_run_sparse_slab(jb,&caps[c0],cur,g,nb0[c0],slab_pk,slab_cnt);
        for(int j=0;j<g;j++) p->dtime[j]=NULL;
        if(rc<0) goto fail;
        cur+=g;
      }
    } else {
      for(;;){
        int lead=-1;
        uintptr_t min_pos=0;
        for(int k=c0;k<c1;k++){
          if(b0[k]>=jobs[k].nblocks) continue;
          const ap_hmf_plan *kp=jobs[k].p;
          const size_t eb=kp->real_series ? (kp->real_stride==2 ? 8u : 4u) : 8u;
          const uintptr_t pos=(uintptr_t)jobs[k].series + jobs[k].start[b0[k]]*eb;
          if(lead<0 || pos<min_pos){ lead=k; min_pos=pos; }
        }
        if(lead<0) break;
        ap_hmf_sparse_job *ljb=&jobs[lead];
        ap_hmf_plan *lp=ljb->p;
        const int g=hmf_slab_len(ljb,b0[lead],nb0[lead]);
        if(g<0) goto fail;

        /* Detect a paired strided quadrature lane on the same complex64 buffer so both lanes
           forward-transform per W-block mini-batch while cache lines are hot in L1/L2. */
        int qpeer=-1, qg=0;
        if(lp->real_series && lp->real_stride==2){
          const size_t a_hi=ljb->start[b0[lead]+g-1]+lp->n;
          size_t best_lo=0;
          for(int k=c0;k<c1;k++){
            if(k==lead || b0[k]>=jobs[k].nblocks) continue;
            ap_hmf_sparse_job *kjb=&jobs[k];
            ap_hmf_plan *kp=kjb->p;
            if(kp==lp || !kp->real_series || kp->real_stride!=2
               || kjb->nseries!=ljb->nseries
               || !(kjb->series==ljb->series+1 || ljb->series==kjb->series+1))
              continue;
            const size_t k_lo=kjb->start[b0[k]];
            if(k_lo>=a_hi) continue;
            const int kg=hmf_slab_len(kjb,b0[k],nb0[k]);
            if(kg<0) goto fail;
            if(kp->n==lp->n && kg==g
               && memcmp(kjb->start+b0[k],ljb->start+b0[lead],(size_t)g*sizeof(size_t))==0){
              qpeer=k; qg=kg;
              break;
            }
            if(qpeer<0 || k_lo<best_lo){
              qpeer=k; qg=kg; best_lo=k_lo;
            }
          }
        }

        if(qpeer>=0){
          ap_hmf_sparse_job *qjb=&jobs[qpeer];
          if(hmf_forward_slab_quad_pair(lp,ljb->series,ljb->start,b0[lead],g,
                                        qjb->p,qjb->series,qjb->start,b0[qpeer],qg,
                                        ljb->nseries)<0) goto fail;
        } else {
          const unsigned long long t_fwd=ap_ticks();
          if(hmf_forward_slab(lp,ljb->series,ljb->nseries,ljb->start,b0[lead],g)<0) goto fail;
          lp->c_series += ap_ticks()-t_fwd;
        }

        for(int pass_q=0;pass_q<(qpeer>=0 ? 2 : 1);pass_q++){
          const int cur_idx = pass_q==0 ? lead : qpeer;
          const int cur_g   = pass_q==0 ? g : qg;
          ap_hmf_sparse_job *cjb=&jobs[cur_idx];
          ap_hmf_plan *cp=cjb->p;
          if(hmf_run_sparse_slab(cjb,&caps[cur_idx],b0[cur_idx],cur_g,nb0[cur_idx],
                                 slab_pk,slab_cnt)<0){
            for(int j=0;j<cur_g;j++) cp->dtime[j]=NULL;
            if(pass_q==0 && qpeer>=0) for(int j=0;j<qg;j++) jobs[qpeer].p->dtime[j]=NULL;
            goto fail;
          }
          /* Share owner's L2-hot forward spectra with any cluster peer on identical block starts. */
          const size_t sstride=2u*cp->n+16u;
          const size_t cst=cp->real_stride ? cp->real_stride : 1u;
          for(int k=c0;k<c1;k++){
            if(k==lead || k==qpeer || b0[k]+cur_g>jobs[k].nblocks) continue;
            ap_hmf_sparse_job *kjb=&jobs[k];
            ap_hmf_plan *kp=kjb->p;
            const size_t kst=kp->real_stride ? kp->real_stride : 1u;
            if(kp->n!=cp->n || cur_g>kp->dgroup || kp->real_series!=cp->real_series || kst!=cst
               || ap_plan_lanes(kp->full_fft)!=ap_plan_lanes(cp->full_fft)
               || kjb->series!=cjb->series || kjb->nseries!=cjb->nseries) continue;
            if(!hmf_job_win_ok(kjb,b0[k],cur_g,nb0[k])) continue;
            if(memcmp(kjb->start+b0[k],cjb->start+b0[cur_idx],(size_t)cur_g*sizeof(size_t))!=0)
              continue;

            if(kp!=cp){
              const unsigned long long t_sh=ap_ticks();
              for(int j=0;j<cur_g;j++){
                kp->dmirrored[j]=cp->dmirrored[j];
                if(set_data_tiers(kp,j,cp->spec+(size_t)j*sstride,1)){
                  for(int u=0;u<=j;u++){ kp->dtime[u]=NULL; kp->dspec[u]=NULL; kp->dready[u]=0; }
                  for(int u=0;u<cur_g;u++) cp->dtime[u]=NULL;
                  if(pass_q==0 && qpeer>=0) for(int u=0;u<qg;u++) jobs[qpeer].p->dtime[u]=NULL;
                  goto fail;
                }
                kp->dtime[j]=cp->dtime[j]; kp->dhave[j]=cp->dhave[j];
              }
              kp->c_series += ap_ticks()-t_sh;
            }
            const int rc=hmf_run_sparse_slab(kjb,&caps[k],b0[k],cur_g,nb0[k],slab_pk,slab_cnt);
            if(kp!=cp){
              for(int j=0;j<cur_g;j++){
                cp->dmirrored[j] |= kp->dmirrored[j];
                kp->dtime[j]=NULL; kp->dspec[j]=NULL; kp->dready[j]=0;
              }
            }
            if(rc<0){
              for(int u=0;u<cur_g;u++) cp->dtime[u]=NULL;
              if(pass_q==0 && qpeer>=0) for(int u=0;u<qg;u++) jobs[qpeer].p->dtime[u]=NULL;
              goto fail;
            }
            b0[k]+=cur_g;
          }
          for(int j=0;j<cur_g;j++) cp->dtime[j]=NULL;
          b0[cur_idx]+=cur_g;
        }
      }
    }
    c0=c1;
  }
  free(slab_pk); free(slab_cnt); free(nb0); free(caps); free(b0);
  return 0;

fail:
  for(int i=0;i<njobs;i++){
    if(jobs[i].p){
      jobs[i].p->bph=NULL; jobs[i].p->sparse=0;
      for(int j=0;j<jobs[i].p->dgroup;j++) jobs[i].p->dtime[j]=NULL;
    }
    free(jobs[i].out_flat); free(jobs[i].out_idx); free(jobs[i].out_val);
    jobs[i].out_flat=NULL; jobs[i].out_idx=NULL; jobs[i].out_val=NULL;
    jobs[i].out_count=0; jobs[i].total=0;
  }
  free(slab_pk); free(slab_cnt); free(nb0); free(caps); free(b0);
  return -1;
}

unsigned long long ap_hmf_series_ticks(const ap_hmf_plan *p){ return p ? p->c_series : 0; }

static int hmf_refine_fft(ap_hmf_plan *p, const int *fire_d, const int *fire_t,
                      int d0, int t0, int nt, int nfire,
                      size_t binsize, float threshold,
                      ap_peak *peaks, int *counts, size_t start, size_t end){
  if(nfire <= 0) return 0;
  /* Complete negative-frequency bins on any block whose survivor reaches FFT refine. */
  if(p->real_series){
    for(int j = 0; j < nfire; j++){
      const int idx = d0 + fire_d[j];
      if(!p->dmirrored[idx]){
        if(!p->dspec[idx]) return -1;
        ap_real_split_mirror_on(p->full_fft, (float *)p->dspec[idx], p->n);
        p->dmirrored[idx] = 1;
      }
    }
  } else if(!p->is_dif || p->hermitian){
    for(int j = 0; j < nfire; j++){
      const int idx = d0 + fire_d[j];
      if(!p->dmirrored[idx]){
        if(!p->dspec[idx]) return -1;
        float *sp = (float *)p->dspec[idx];
        if(p->dtime[idx] && p->dhave[idx] > 0)
          ap_fft_forward_scaled(p->full_fft, p->dtime[idx], 2 * p->dhave[idx], 1,
                                1.0f / (float)p->n, sp);
        else
          memset(sp, 0, 2 * p->n * sizeof(float));
        p->dmirrored[idx] = 1;
      }
    }
  }

  if(p->is_dif && p->hermitian){
    const size_t nb = hmf_nbins_phased(p, binsize, start, end, hmf_row_phase(p, d0 + fire_d[0]));
    const size_t K = p->k;
    const size_t N = p->n;
    int total = 0;

    for(int j = 0; j < nfire; j++){
      int d = fire_d[j];
      int t = fire_t[j];
      const size_t row = (size_t)d * nt + t;
      const float *sp = p->dspec[d0 + d];
      if(!sp) return -1;
      const float *tmpl = p->tmpls_half + (size_t)(t0 + t) * 2 * K;
      float *prod = p->prod_scratch;

      /* DC bin (k = 0): template DC is real in tmpl[0] */
      prod[0] = sp[0] * tmpl[0];
      prod[1] = sp[1] * tmpl[0];

      /* Nyquist bin (k = K): template Nyquist is real in tmpl[1] */
      prod[2 * K]     = sp[2 * K] * tmpl[1];
      prod[2 * K + 1] = sp[2 * K + 1] * tmpl[1];

      /* Positive bins k = 1 .. K - 1 */
      for(size_t k = 1; k < K; k++){
        float xr = sp[2 * k], xi = sp[2 * k + 1];
        float hr = tmpl[2 * k], hi = tmpl[2 * k + 1];
        prod[2 * k]     = xr * hr + xi * hi;
        prod[2 * k + 1] = xi * hr - xr * hi;
      }

      /* Negative bins k = K + 1 .. N - 1:
       * By Hermitian symmetry: H*[k] = H[N - k] = hr + j * hi */
      for(size_t k = K + 1; k < N; k++){
        size_t k_pos = N - k;
        float xr = sp[2 * k], xi = sp[2 * k + 1];
        float hr = tmpl[2 * k_pos], hi = tmpl[2 * k_pos + 1];
        prod[2 * k]     = xr * hr - xi * hi;
        prod[2 * k + 1] = xr * hi + xi * hr;
      }

      int c = 0;
      int r = ap_binmax(p->full_fft, prod, N, 1, binsize, threshold,
                        peaks + row * nb, &c, AP_BACKWARD, start, end,
                        p->bph ? p->bph + d0 + d : NULL);
      if(r < 0) return -1;
      if(counts) counts[row] = c;
      total += c;
    }
    return total;
  } else if(p->is_dif){
    for(int j = 0; j < nfire; j++){
      int d = fire_d[j];
      if(!p->dready[d0 + d]){
        const float *sp = p->dspec[d0 + d];
        if(!sp) return -1;
        if(ap_mf_set_data(p->full, 2 * (d0 + d), sp)) return -1;
        const float * restrict tw = p->twiddles;
        float * restrict d1 = p->tw_scratch;
        for(size_t k = 0; k < p->k; k++){
          float dr = sp[2 * k], di = sp[2 * k + 1];
          float wr = tw[2 * k], wi = tw[2 * k + 1];
          d1[2 * k]     = dr * wr - di * wi;
          d1[2 * k + 1] = dr * wi + di * wr;
        }
        if(ap_mf_set_data(p->full, 2 * (d0 + d) + 1, d1)) return -1;
        p->dready[d0 + d] = 1;
      }
    }

    const size_t nb = hmf_nbins_phased(p, binsize, start, end, hmf_row_phase(p, d0 + fire_d[0]));
    int total = 0;
    for(int j = 0; j < nfire; j++){
      const int d = fire_d[j], t = fire_t[j];
      const size_t row = (size_t)d * nt + t;
      int r = ap_mf_run_dif(p->full, 2 * (d0 + d), t0 + t, 1,
                            binsize, threshold, peaks + row * nb,
                            counts ? counts + row : NULL, start, end,
                            hmf_row_phase(p, d0 + d));
      if(r < 0) return -1;
      total += r;
    }
    return total;
  } else {
    for(int j = 0; j < nfire; j++){
      int d = fire_d[j];
      if(!p->dready[d0 + d]){
        if(!p->dspec[d0 + d]) return -1;
        if(ap_mf_set_data(p->full, d0 + d, p->dspec[d0 + d])) return -1;
        p->dready[d0 + d] = 1;
      }
    }
    ap_mf_set_bin_phase(p->full, p->bph);        /* the full plan's rows are ours */
    int r = ap_mf_run_pairs_pooled(p->full, d0, fire_d, fire_t, nfire,
                                  t0, binsize, threshold,
                                  peaks, counts, start, end, nt);
    ap_mf_set_bin_phase(p->full, NULL);
    return r;
  }
}

/* One survivor by direct correlation: every lag within dir_hw coarse samples of the coarse
   lags in loc (ncl entries; index < 0 skipped), binned with phase offset rem = ph % binsize
   into the row's nb touched output bins. Returns the bins written above threshold, or -2 when
   the pair is priced cheaper as a whole block (or its windows would read past the block). */
static int refine_direct_pair(ap_hmf_plan *p,int d,int t,const ap_peak *loc,size_t ncl,
                              size_t R,size_t binsize,size_t rem,float threshold,
                              ap_peak *out,size_t nb,size_t start,size_t end){
  const size_t n=p->n;
  const int L=p->tap_len[t], c=L/2;
  const long hw=(long)p->dir_hw*(long)R;
  /* Build, sort, and merge touching or overlapping lag windows. */
  long rlo[64], rhi[64]; int nr=0;
  for(size_t j=0;j<ncl;j++){
    if(loc[j].index<0) continue;
    long a=(long)loc[j].index*(long)R-hw, b=(long)loc[j].index*(long)R+hw+1;
    if(a<(long)start) a=(long)start;
    if(b>(long)end) b=(long)end;
    if(a>=b) continue;
    if(nr==64) return -2;
    int pos=nr++;
    while(pos>0 && rlo[pos-1]>a){ rlo[pos]=rlo[pos-1]; rhi[pos]=rhi[pos-1]; pos--; }
    rlo[pos]=a; rhi[pos]=b;
  }
  long lo[64], hi[64]; int nw=0; long nlag=0;
  for(int w=0;w<nr;w++){
    if(nw && rlo[w]<=hi[nw-1]){ if(rhi[w]>hi[nw-1]) hi[nw-1]=rhi[w]; continue; }
    lo[nw]=rlo[w]; hi[nw]=rhi[w]; nw++;
  }
  if(!nw) return -2;
  for(int w=0;w<nw;w++) nlag+=hi[w]-lo[w];
  if(p->trace) fprintf(stderr,"    [direct] pair d=%d t=%d coarse lag %ld R=%zu hw=%ld windows %d lags %ld L=%d"
                       " price %.0f vs %.0f\n",d,t,loc[0].index,R,hw,nw,nlag,L,p->dir_lagtap*(double)nlag*L,
                       p->dir_fftpair);
  if(p->dir_lagtap*(double)nlag*L >= p->dir_fftpair) return -2;
  /* the block's samples; a lag tau reads tau - c .. tau - c + L - 1 */
  const float *x=p->dtime[d];
  const size_t have=p->dhave[d];
  int x_contig=1;
  for(int w=0;w<nw;w++)
    if(lo[w]-c<0 || hi[w]-1-c+L>(long)n) return -2;     /* would wrap: the transform's answer */
  if(nw>0){
    const size_t s_min=(size_t)(lo[0]-c), s_max=(size_t)(hi[nw-1]-1-c+L);
    if(p->real_series){
      const size_t st=p->real_stride ? p->real_stride : 1;
      if(st!=1 || s_max>have){
        /* Reuse or extend the unpacked sample span in p->dx across survivors of block d. */
        if(p->dx_d==d && s_min<=p->dx_hi && s_max>=p->dx_lo){
          if(s_min<p->dx_lo){
            const size_t len=p->dx_lo-s_min;
            const size_t avail=have>s_min ? (have-s_min<len ? have-s_min : len) : 0;
            ap_scale_load_on(p->full_fft,p->dx+s_min,avail ? x+s_min*st : p->dx,avail,len,st,1.0f);
            p->dx_lo=s_min;
          }
          if(s_max>p->dx_hi){
            const size_t len=s_max-p->dx_hi;
            const size_t avail=have>p->dx_hi ? (have-p->dx_hi<len ? have-p->dx_hi : len) : 0;
            ap_scale_load_on(p->full_fft,p->dx+p->dx_hi,avail ? x+p->dx_hi*st : p->dx,avail,len,st,
                             1.0f);
            p->dx_hi=s_max;
          }
        } else {
          const size_t avail=have>s_min ? (have-s_min<s_max-s_min ? have-s_min : s_max-s_min) : 0;
          ap_scale_load_on(p->full_fft,p->dx+s_min,avail ? x+s_min*st : p->dx,avail,s_max-s_min,st,
                           1.0f);
          p->dx_d=d; p->dx_lo=s_min; p->dx_hi=s_max;
        }
        x=p->dx;
        x_contig=0;
      }
    } else if(s_max>have){
      const size_t avail=have>s_min ? have-s_min : 0;
      if(avail) memcpy(p->dx+2*s_min,x+2*s_min,2*avail*sizeof(float));
      memset(p->dx+2*(s_min+avail),0,2*(s_max-s_min-avail)*sizeof(float));
      x=p->dx;
      x_contig=0;
    }
  }
  const float *tr=p->taps[t];
  const float *ti=p->tap_cplx ? tr+tap_imag_offset(L) : NULL;
  const float t2=threshold>0.f ? threshold*threshold : 0.f;
  const int lw=ap_plan_lanes(p->full_fft);
  const int q=lw>0 ? (p->real_series ? lw : (lw>=2 ? lw/2 : 1)) : 1;
  for(size_t b=0;b<nb;b++) out[b]=(ap_peak){-1,0.f,0.f,t2};
  for(int w=0;w<nw;w++){
    const int m=(int)(hi[w]-lo[w]);
    int mcall=m;
    if(q>1 && x_contig){
      /* Round odd 2*hw*R+1 windows up to a full SIMD vector quantum when in-bounds. */
      const int mpad=(m+q-1)&~(q-1);
      if((size_t)mpad<=n && (size_t)(lo[w]-c)+(size_t)mpad-1+(size_t)L<=have) mcall=mpad;
    }
    const float *xw=p->real_series ? x+(lo[w]-c) : x+2*(lo[w]-c);
    ap_td_corr_ex_on(p->full_fft,xw,p->real_series,tr,ti,L,mcall,p->dout);
    for(int i=0;i<m;i++){
      const float re=p->dout[2*i], im=p->dout[2*i+1], m2=re*re+im*im;
      const long k=lo[w]+i;
      const size_t b=((size_t)(k-(long)start)+rem)/binsize;
      if(m2>out[b].magnitude){ out[b].magnitude=m2; out[b].index=k; out[b].re=re; out[b].im=im; }
    }
  }
  /* A maximum on an internal edge of a direct window inside its bin may be the shoulder of a
     peak outside the window; fall back to the whole-block transform to preserve exactness. */
  for(size_t b=0;b<nb;b++){
    const long k=out[b].index;
    if(k<0) continue;
    const size_t blo = b==0 ? start : start+b*binsize-rem;
    size_t bhi = start+(b+1)*binsize-rem;
    if(bhi>end) bhi=end;
    for(int w=0;w<nw;w++)
      if((k==lo[w] && lo[w]>(long)blo) || (k==hi[w]-1 && hi[w]<(long)bhi)){ p->dir_edge++; return -2; }
  }
  int cnt=0;
  for(size_t b=0;b<nb;b++){
    if(out[b].index>=0){ out[b].magnitude=sqrtf(out[b].magnitude); cnt++; }
    else out[b].magnitude=0.f;
  }
  p->dir_pairs++; p->dir_lags+=nlag;
  return cnt;
}

static int survivor_needs_sub(const ap_hmf_plan *p,const hmf_tier *tr,
                              int gd,int gt,size_t row,size_t start,size_t hi,
                              size_t R,size_t binsize){
  if(!p->dtime[gd]) return 0;
  const size_t ph=hmf_row_phase(p,gd);
  const size_t ntouch=(hi-1-start+ph)/binsize - ph/binsize + 1;
  if(ntouch<2 || ntouch>HMF_MAX_DIRECT_BINS) return 0;
  const ap_peak ce=tr->cebuf[row];
  if(ce.index<0) return 0;
  const long hw=(long)p->dir_hw*(long)R;
  long a0=(long)ce.index*(long)R-hw, b0=(long)ce.index*(long)R+hw+1;
  if(a0<(long)start) a0=(long)start;
  if(b0>(long)hi) b0=(long)hi;
  return b0>a0 && p->dir_lagtap*(double)(b0-a0)*p->tap_len[gt] < p->dir_fftpair;
}

static int hmf_refine(ap_hmf_plan *p, const int *fire_d, const int *fire_t,
                      int d0, int t0, int nt, int nfire,
                      size_t binsize, float threshold,
                      ap_peak *peaks, int *counts, size_t start, size_t end){
  if(nfire<=0) return 0;
  const size_t nb=hmf_nbins_phased(p,binsize,start,end,hmf_row_phase(p,d0+fire_d[0]));
  /* Refine rows touching up to HMF_MAX_DIRECT_BINS output bins directly around each touched
     bin's last-tier coarse peak (no extra work when unsplit into 1 bin; batched sub-window
     coarse election on tr->mf for 2..4 touched bins). Rows touching more bins, or whose
     window cost exceeds dir_fftpair, refine by whole-block transform. */
  const size_t hi=end>p->n ? p->n : end;
  if(!(p->direct && p->taps && start<hi
       && (hi-1-start)/binsize < HMF_MAX_DIRECT_BINS
       && p->tier[p->ntiers-1].lagged))
    return hmf_refine_fft(p,fire_d,fire_t,d0,t0,nt,nfire,binsize,threshold,
                          peaks,counts,start,end);
  hmf_tier *tr=&p->tier[p->ntiers-1];
  const size_t R=p->n/tr->m;
  size_t cstart=start/R; if(cstart>0) cstart--;
  size_t cend=(hi+R-1)/R+1; if(cend>tr->m) cend=tr->m;
  const size_t cspan=cend>cstart ? cend-cstart : 1;
  const size_t cbs=(cspan+HMF_COARSE_SUBBINS-1)/HMF_COARSE_SUBBINS;
  const int ncb=(int)((cspan+cbs-1)/cbs);
  const float sthr=tr->last_q15 ? tr->thr*0.97f : tr->thr;
  const float thr2=sthr>0.f ? sthr*sthr : 0.f;
  unsigned long long q1=ap_ticks();

  /* Batch coarse sub-window peaks across multi-bin direct survivors in one call. */
  if(hmf_ensure_df(p,(size_t)nfire)) return -1;
  int ns=0, have_sub=0;
  for(int j=0;j<nfire;j++){
    const int d=fire_d[j], t=fire_t[j];
    if(survivor_needs_sub(p,tr,d0+d,t0+t,(size_t)d*nt+t,start,hi,R,binsize)){
      p->dfd[ns]=d; p->dft[ns]=t; ns++;
    }
  }
  if(ns>0 && ncb>1){
    for(int k=0;tr->npending && k<ns;k++){
      const int gd=d0+p->dfd[k];
      if(tr->pending[gd] & HMF_PEND_MF){
        if(ingest_tier_data(p,tr,gd,p->dspec[gd],1,0)) return -1;
        hmf_set_pending(tr,gd,(unsigned char)(tr->pending[gd] & ~HMF_PEND_MF));
      }
    }
    const size_t need=(size_t)ns*(size_t)ncb;
    if(p->dir_sub_cap<need){
      ap_peak *buf=ap_alloc64(need*sizeof(ap_peak));
      if(!buf) return -1;
      free(p->dir_sub); p->dir_sub=buf; p->dir_sub_cap=need;
    }
    const int rc=ap_mf_run_pairs_packed(tr->mf,d0,p->dfd,p->dft,ns,t0,
                                        cbs,sthr,p->dir_sub,cstart,cend);
    if(rc<0) return -1;
    have_sub=(rc>0);
  }

  int total=0, nf=0, s=0;
  p->dx_d=-1;
  for(int j=0;j<nfire;j++){
    const int d=fire_d[j], t=fire_t[j];
    const size_t row=(size_t)d*nt+t;
    const size_t ph=hmf_row_phase(p,d0+d);
    const size_t jb0=ph/binsize, jb1=(hi-1-start+ph)/binsize;
    const size_t ntouch=jb1-jb0+1, rem=ph%binsize;
    int c=-2;
    if(ntouch==1 && p->dtime[d0+d] && tr->cebuf[row].index>=0){
      const ap_peak ce=tr->cebuf[row];
      c=refine_direct_pair(p,d0+d,t0+t,&ce,1,R,binsize,rem,threshold,
                           peaks+row*nb+jb0,1,start,hi);
    } else if(survivor_needs_sub(p,tr,d0+d,t0+t,row,start,hi,R,binsize)){
      const ap_peak ce=tr->cebuf[row];
      const ap_peak *cp=have_sub ? p->dir_sub+(size_t)s*(size_t)ncb : NULL;
      s++;
      ap_peak loc[HMF_MAX_DIRECT_BINS];
      int need_corr=0, corr_ok=1;
      for(size_t u=0;u<ntouch;u++){
        const size_t blo = u==0 ? start : start+u*binsize-rem;
        size_t bhi = start+(u+1)*binsize-rem;
        if(bhi>hi) bhi=hi;
        size_t cblo=blo/R; if(cblo>0) cblo--;
        size_t cbhi=(bhi+R-1)/R+1; if(cbhi>tr->m) cbhi=tr->m;
        if((size_t)ce.index>=cblo && (size_t)ce.index<cbhi){
          loc[u]=ce;
          continue;
        }
        if(cp){
          const size_t qlo=cblo>cstart ? (cblo-cstart)/cbs : 0;
          size_t qhi=cbhi>cstart ? (cbhi-1-cstart)/cbs : 0;
          if(qhi>=(size_t)ncb) qhi=(size_t)ncb-1;
          ap_peak best={-1,0.f,0.f,0.f};
          int ambig=0;
          for(size_t q=qlo;q<=qhi;q++){
            const ap_peak pk=cp[q];
            if(pk.index<0) continue;
            if((size_t)pk.index>=cblo && (size_t)pk.index<cbhi){
              if(best.index<0 || pk.magnitude>best.magnitude) best=pk;
            } else if(best.index<0 || pk.magnitude>best.magnitude){
              ambig=1;
            }
          }
          if(!ambig){
            loc[u]=best;
            continue;
          }
        }
        if(!need_corr){
          const int gd=d0+d;
          if(tr->pending[gd] & HMF_PEND_MF){
            if(ingest_tier_data(p,tr,gd,p->dspec[gd],1,0)){ corr_ok=0; break; }
            hmf_set_pending(tr,gd,(unsigned char)(tr->pending[gd] & ~HMF_PEND_MF));
          }
          if(ap_mf_correlate(tr->mf,gd,1,t0+t,1,tr->scratch)){ corr_ok=0; break; }
          need_corr=1;
        }
        long bk=-1;
        float bm2=thr2;
        for(size_t jc=cblo;jc<cbhi;jc++){
          const float re=tr->scratch[2*jc], im=tr->scratch[2*jc+1], m2=re*re+im*im;
          if(bk<0 ? (m2>=bm2) : (m2>bm2)){ bm2=m2; bk=(long)jc; }
        }
        loc[u]=(ap_peak){bk,0.f,0.f,0.f};
      }
      if(corr_ok)
        c=refine_direct_pair(p,d0+d,t0+t,loc,ntouch,R,binsize,rem,threshold,
                             peaks+row*nb+jb0,ntouch,start,hi);
    }
    if(c==-2){ p->dfd[nf]=d; p->dft[nf]=t; nf++; continue; }
    for(size_t b=0;b<jb0;b++) peaks[row*nb+b]=(ap_peak){-1,0.f,0.f,0.f};
    for(size_t b=jb1+1;b<nb;b++) peaks[row*nb+b]=(ap_peak){-1,0.f,0.f,0.f};
    if(counts) counts[row]=c;
    total+=c;
  }
  unsigned long long q2=ap_ticks();
  p->dir_ttd+=q2-q1;
  if(nf){
    p->dir_fft+=nf;
    int r=hmf_refine_fft(p,p->dfd,p->dft,d0,t0,nt,nf,binsize,threshold,peaks,counts,start,end);
    if(r<0) return -1;
    total+=r;
    p->dir_tfft+=ap_ticks()-q2;
  }
  return total;
}

static void empty_row(ap_peak *peaks,int *counts,size_t row,size_t nb){
  if(nb==1){
    peaks[row].index=-1;
    peaks[row].re=peaks[row].im=peaks[row].magnitude=0.f;
  }else{
    const ap_peak empty_peak = {-1, 0.f, 0.f, 0.f};
    ap_peak * restrict dst = peaks + row*nb;
    for(size_t b=0;b<nb;b++) dst[b] = empty_peak;
  }
  if(counts) counts[row]=0;
}

static void reject_row(ap_hmf_plan *p,ap_peak *peaks,int *counts,size_t row,size_t nb){
  unsigned long long f0 = p->prof ? ap_ticks() : 0;
  if(p->sparse && counts) counts[row]=0;
  else empty_row(peaks,counts,row,nb);
  if(p->prof) p->c_fill += ap_ticks()-f0;
}

static int hmf_q15_prepare_data(ap_hmf_plan *p,hmf_tier *tr,int ql){
  if(tr->qdm) return 0;
  const size_t stride = 2*tr->m + 32;
  const size_t qbytes = (size_t)p->nd * stride * sizeof(int16_t);
  tr->qdm = ap_alloc64(qbytes);
  tr->qds = calloc((size_t)p->nd, sizeof(float));
  tr->qscr = ap_alloc64(ap_q15_scratch_bytes(tr->m, ql));
  if(!tr->qdm || !tr->qds || !tr->qscr){
    free(tr->qdm); free(tr->qds); free(tr->qscr);
    tr->qdm=NULL; tr->qds=NULL; tr->qscr=NULL;
    return -1;
  }
  memset(tr->qdm, 0, qbytes);
  return 0;
}

/* Evaluate an already selected pair list. Logical gate identity and thresholds
   stay fixed even when its position in the execution order changes. */
static int run_gate_pairs(ap_hmf_plan *p,hmf_tier *tr,int d0,int t0,int nt,
                          const int *ds,const int *ts,int count,size_t start,size_t end,
                          int use_q15,int elect_g16_lag,int16_t *qlag,int *dst_d,int *dst_t){
  const size_t r=p->n/tr->m;
  size_t lo=start/r, hi=(end+r-1)/r+1;      /* as ap_hmf_run: one coarse sample past each end */
  if(lo>0) lo--;
  if(hi>tr->m) hi=tr->m;
  const int use_g16 = (!use_q15 && tr->g16 != NULL);
  const unsigned char pend_bit = use_g16 ? HMF_PEND_G16 : HMF_PEND_MF;
  for(int j=0;tr->npending && j<count;j++){
    const int d=d0+ds[j];
    if(tr->pending[d] & pend_bit){
      if(ingest_tier_data(p,tr,d,p->dspec[d],!use_g16,use_g16)) return -1;
      hmf_set_pending(tr,d,(unsigned char)(tr->pending[d] & ~pend_bit));
    }
  }
  /* A Q15 tier's decision per listed pair goes to p->qpass[j] (free once the first tier's
     survivors are compacted), with optional coarse argmax lag in qlag[j]; an FP16 or FP32
     tier's maximum goes to its cebuf (with optional direct survivor compaction on FP16). */
  if(use_q15)
    return ap_mf_q15_pairs_lag(tr->mf,d0,ds,ts,count,t0,tr->thr,lo,hi,p->qpass,NULL,qlag);
  if(hmf_ensure_cebuf(p,tr)) return -1;
  if(use_g16)
    return ap_gate16_run_pairs_lag(tr->g16,d0,t0,ds,ts,count,nt,lo,hi,elect_g16_lag,tr->thr,
                                   dst_d,dst_t,tr->cebuf);
  return ap_mf_run_pairs_pooled(tr->mf,d0,ds,ts,count,t0,hi>lo?hi-lo:1,tr->thr,
                                tr->cebuf,NULL,lo,hi,nt);
}

int ap_hmf_run(ap_hmf_plan *p,int d0,int nd,int t0,int nt,
               size_t binsize,float threshold,
               ap_peak *peaks,int *counts,size_t start,size_t end){
  if(!p||nd<1||nt<1||!binsize) return 0;
  if(!ap_range_ok(d0,nd,p->nd)||!ap_range_ok(t0,nt,p->nt)) return -1;
  for(int t=t0;t<t0+nt;t++) if(p->tready[t]==2) return -1;   /* stale since a reference change */
  if(end>p->n) end=p->n;
  if(start>=end) return 0;
  const size_t n=p->n;
  const size_t nb=hmf_nbins_phased(p,binsize,start,end,hmf_row_phase(p,d0));
  for(int i=0;i<p->ntiers;i++)
    if(!isfinite(p->tier[i].thr) || p->tier[i].thr < 0) return -1;

  const int fast_sparse = p->sparse && counts && !p->prof;
  if(fast_sparse && p->sparse == 1) memset(counts, 0, (size_t)nd * (size_t)nt * sizeof(int));

  const int *fire_d=NULL,*fire_t=NULL;
  int nfire=0;
  for(int i=0;i<p->ntiers;i++){
    hmf_tier *tr=&p->tier[i];
    /* Coarse sample j maps to full lag j*R. Widen by one coarse sample at each end, so a
       signal near either end of the caller's window has coarse samples on both sides: without
       the far one, one up to R lags past the last coarse sample kept 0.47 of its SNR. */
    const size_t R=n/tr->m;
    size_t cstart = start/R;
    size_t cend   = (end+R-1)/R+1; if(cend>tr->m) cend=tr->m;
    if(cstart>0) cstart--;
    const size_t cspan = cend>cstart ? cend-cstart : 1;
    if(i==0 && p->tier0_clustered){
      if(t0==0 && nt==p->nt && !p->dump){
        int rc=hmf_run_tier0_clustered(p,d0,nd,fast_sparse,nb,peaks,counts,start,end,
                                       &fire_d,&fire_t,&nfire);
        if(rc<=0) return rc;
        /* For a 1-tier clustered chain with direct time-domain refine active, elect each
           surviving member template's own coarse peak lag at threshold 0 (dismissing none). */
        if(p->ntiers==1 && p->direct && p->taps && start<end
           && (end-1-start)/binsize < HMF_MAX_DIRECT_BINS){
          int any_time=0;
          for(int j=0;j<nfire;j++){ if(p->dtime[d0+fire_d[j]]){ any_time=1; break; } }
          if(any_time){
            unsigned long long t_el=ap_ticks();
            if(hmf_ensure_cebuf(p,tr)) return -1;
            for(int j=0;j<nfire;j++){
              const int gd=d0+fire_d[j];
              if((p->tier0_uncl_pend && p->tier0_uncl_pend[gd])
                 || (tr->pending[gd] & HMF_PEND_MF)){
                if(p->dspec[gd]
                   && ingest_tier_data_target(p,tr,tr->mf,NULL,gd,p->dspec[gd],1,0))
                  return -1;
                if(p->tier0_uncl_pend) p->tier0_uncl_pend[gd]=0;
                hmf_set_pending(tr,gd,(unsigned char)(tr->pending[gd] & ~HMF_PEND_MF));
              }
            }
            if(ap_mf_run_pairs_pooled(tr->mf,d0,fire_d,fire_t,nfire,0,cspan,0.0f,
                                      tr->cebuf,NULL,cstart,cend,nt)<0)
              return -1;
            tr->lagged=1;
            tr->ticks+=ap_ticks()-t_el;
          }
        }
        continue;
      }
      if(hmf_sync_unclustered_tier0(p,d0,nd)) return -1;
    }
    if(i==1 && p->tier1_clustered){
      const int elect_last1 = (i==p->ntiers-1 && p->direct && p->taps) ? 1 : 0;
      if(t0==0 && nt==p->nt && !p->dump && !elect_last1){
        int rc=hmf_run_tier1_clustered(p,d0,fast_sparse,nb,peaks,counts,start,end,
                                       fire_d,fire_t,nfire,&fire_d,&fire_t,&nfire);
        if(rc<=0) return rc;
        continue;
      }
      if(hmf_sync_unclustered_tier1(p,d0,nd)) return -1;
    }
    const float thr=tr->thr;
    tr->lagged = !(tr->g16 && i==0 && !p->q15);
    tr->last_q15 = 0;
    const int *checked_d=fire_d,*checked_t=fire_t;
    int nchecked=i==0 ? nd*nt : nfire;
    if(i==0 && tr->npending){
      const int use_g16_0 = (!p->q15 && tr->g16 != NULL);
      const unsigned char pbit0 = use_g16_0 ? HMF_PEND_G16 : HMF_PEND_MF;
      for(int d=d0;d<d0+nd;d++)
        if(tr->pending[d] & pbit0){
          if(ingest_tier_data(p,tr,d,p->dspec[d],!use_g16_0,use_g16_0)) return -1;
          hmf_set_pending(tr,d,(unsigned char)(tr->pending[d] & ~pbit0));
        }
    }
    unsigned long long t_0=ap_ticks();
    float *qstat=NULL;               /* set: the screen decided, and this is its maximum */
    int16_t *qlag=NULL;
    int use_q15=0;
    int q15_direct_fire=0;
    int nnext=0;
    if(i==0 && p->q15){
      /* The screen is the first tier: a pair passes when its int16 maximum reaches the
         tier's threshold, and no float run of the tier follows.  Like every tier it answers
         to the chain's false-dismissal budget against the flat filter, not to the float
         tier's decisions; its rounding (rms 0.46 sqrt(N) LSB, about 0.2% of the threshold)
         is small beside the band's own loss (docs/reduced-precision-gates.md). */
      unsigned long long q0=ap_ticks();
      qstat=p->qstat;
      int ns=ap_mf_q15_screen(tr->mf,d0,nd,t0,nt,thr,cstart,cend,p->qpass,
                              (p->dump||p->trace) ? qstat : NULL);
      if(ns<0) return -1;
      int k=0;
      if(fast_sparse && !p->dump && !p->trace){
        if(ns>0){
          if(hmf_ensure_fire(tr,(size_t)ns)) return -1;
          int * restrict dst_d = tr->fire_d;
          int * restrict dst_t = tr->fire_t;
          for(int d=0;d<nd;d++){
            const unsigned char *qp = p->qpass + (size_t)d*nt;
            int t=0;
            for(; t+8<=nt; t+=8){
              uint64_t w;
              memcpy(&w, qp+t, sizeof w);
              if(!w) continue;
              uint64_t m = (w | ((w & 0x7f7f7f7f7f7f7f7fULL) + 0x7f7f7f7f7f7f7f7fULL))
                           & 0x8080808080808080ULL;
              while(m){
                const int off = __builtin_ctzll(m) >> 3;
                dst_d[k] = d;
                dst_t[k] = t + off;
                k++;
                m &= m - 1;
              }
            }
            for(; t<nt; t++){
              if(qp[t]){ dst_d[k]=d; dst_t[k]=t; k++; }
            }
          }
        }
        q15_direct_fire = 1;
      } else {
        for(int d=0;d<nd;d++) for(int t=0;t<nt;t++){
          const size_t row=(size_t)d*nt+t;
          if(p->qpass[row]){ p->qd[k]=d; p->qt[k]=t; k++; }
          else if(!fast_sparse) reject_row(p,peaks,counts,row,nb);
        }
      }
      /* Rejected rows are finished; the next tier sees only the compacted survivors,
         without another scan of the full data/template grid. */
      checked_d=p->qd; checked_t=p->qt; nchecked=k;
      p->qpassed+=k;
      p->qticks+=ap_ticks()-q0;
      tr->lagged=0;                  /* the screen reports no coarse lag */
    } else if(i==0){
      /* The first tier runs on every pair of the segment in one call: the data
         spectrum is read once and stays resident across the whole template sweep. */
      if(hmf_ensure_cebuf(p,tr)) return -1;
      if(tr->g16){
        /* FP16: the reported magnitude is an upper bound on the FP32 one, so every pair
           the FP32 gate would pass passes here too (gate16.cc). */
        if(ap_gate16_run(tr->g16,d0,nd,t0,nt,cstart,cend,tr->cebuf)<0) return -1;
      } else if(ap_mf_run(tr->mf,d0,nd,t0,nt,cspan,thr,tr->cebuf,NULL,cstart,cend)<0) return -1;
    } else {
      int ql = 0;
      if(tr->q15){
        ql = ap_mf_q15_lanes(tr->mf);
        use_q15 = ql > 0 && nfire >= hmf_min_q15_pairs(ql);
      }
      const int elect_last = (i==p->ntiers-1 && p->direct && p->taps) ? 1 : 0;
      qlag = (use_q15 && elect_last) ? p->qidx : NULL;
      if(qlag && hmf_ensure_cebuf(p,tr)) return -1;
      if(use_q15 && tr->qtm){
        if(hmf_q15_prepare_data(p,tr,ql)) return -1;
        const size_t stride = 2*tr->m + 32;
        const size_t khi = tier_khi(p,tr);
        for(int j=0;tr->npending && j<nfire;j++){
          const int gd=d0+checked_d[j];
          if(tr->pending[gd] & HMF_PEND_Q15){
            int16_t *qdr = tr->qdm + (size_t)gd * stride;
            if(ap_q15_data_band_on(p->full_fft,tr->m,p->dspec[gd],tr->k0,khi,
                                   qdr,qdr+tr->m,&tr->qds[gd]))
              return -1;
            hmf_set_pending(tr,gd,(unsigned char)(tr->pending[gd] & ~HMF_PEND_Q15));
          }
        }
        if(fast_sparse && checked_d && checked_t){
          if(hmf_ensure_fire(tr,(size_t)nfire)) return -1;
          nnext = ap_q15_pairs_batch_on(p->full_fft,tr->m,tr->qdm,tr->qds,tr->qtm,tr->qts,
                                        d0,t0,checked_d,checked_t,nfire,thr,1,cstart,cend,
                                        tr->fire_d,tr->fire_t,NULL,qlag,tr->qscr);
          if(nnext < 0) return -1;
          if(qlag){
            for(int k=0;k<nnext;k++)
              tr->cebuf[(size_t)tr->fire_d[k]*nt + tr->fire_t[k]].index = qlag[k];
          }
          q15_direct_fire = 2;
        } else {
          if(ap_q15_pairs_batch_on(p->full_fft,tr->m,tr->qdm,tr->qds,tr->qtm,tr->qts,
                                   d0,t0,checked_d,checked_t,nfire,thr,1,cstart,cend,
                                   NULL,NULL,p->qpass,qlag,tr->qscr) < 0)
            return -1;
        }
      } else if(!use_q15 && tr->g16 && fast_sparse && checked_d && checked_t
                && !p->dump && !p->trace){
        if(hmf_ensure_fire(tr,(size_t)nfire)) return -1;
        nnext = run_gate_pairs(p,tr,d0,t0,nt,checked_d,checked_t,nfire,start,end,
                               use_q15,elect_last,qlag,tr->fire_d,tr->fire_t);
        if(nnext < 0) return -1;
        q15_direct_fire = 2;
      } else if(run_gate_pairs(p,tr,d0,t0,nt,checked_d,checked_t,nfire,start,end,
                               use_q15,elect_last,qlag,NULL,NULL)<0){
        return -1;
      }
      if(use_q15){
        tr->lagged = (qlag != NULL);
        tr->last_q15 = 1;
      } else if(tr->g16){
        tr->lagged = elect_last;
      }
    }
    tr->ticks += ap_ticks()-t_0;
    const long first_pair=p->pairs;
    if(i==0) p->pairs+=(long)nd*nt;
    if(q15_direct_fire == 1){
      nnext = nchecked;
    } else if(q15_direct_fire == 2){
      /* Survivors already compacted directly into tr->fire_d, tr->fire_t. */
    } else if(i>0 && use_q15 && fast_sparse && checked_d && checked_t){
      /* Fast 8-byte SWAR scan of p->qpass in incoming (d, t) order without touching cebuf. */
      if(nchecked>0 && hmf_ensure_fire(tr,(size_t)nchecked)) return -1;
      const unsigned char * restrict qp = p->qpass;
      int * restrict dst_d = tr->fire_d;
      int * restrict dst_t = tr->fire_t;
      int j=0;
      for(;j+8<=nchecked;j+=8){
        uint64_t w;
        memcpy(&w,qp+j,sizeof w);
        if(!w) continue;
        uint64_t m=(w | ((w & 0x7f7f7f7f7f7f7f7fULL) + 0x7f7f7f7f7f7f7f7fULL))
                   & 0x8080808080808080ULL;
        while(m){
          const int idx=j+(__builtin_ctzll(m)>>3);
          const int d=checked_d[idx], t=checked_t[idx];
          if(qlag) tr->cebuf[(size_t)d*nt+t].index=qlag[idx];
          dst_d[nnext]=d; dst_t[nnext]=t; nnext++;
          m&=m-1;
        }
      }
      for(;j<nchecked;j++){
        if(!qp[j]) continue;
        const int d=checked_d[j], t=checked_t[j];
        if(qlag) tr->cebuf[(size_t)d*nt+t].index=qlag[j];
        dst_d[nnext]=d; dst_t[nnext]=t; nnext++;
      }
    } else {
      if(nchecked>0 && hmf_ensure_fire(tr,(size_t)nchecked)) return -1;
      for(int j=0;j<nchecked;j++){
        const int d = checked_d ? checked_d[j] : j/nt;
        const int t = checked_t ? checked_t[j] : j%nt;
        const size_t row=(size_t)d*nt+t;
        const ap_peak ce = qstat ? (ap_peak){.index=0,
                                             .magnitude=(p->dump||p->trace) ? qstat[row] : 0.0f}
                                 : (use_q15 ? (ap_peak){0,0.f,0.f,0.f} : tr->cebuf[row]);
        int fire = qstat || (use_q15 ? p->qpass[j]!=0 : (ce.index>=0 && ce.magnitude>=thr));
        if(i==0 && fire){
          /* rec[2] repeats the maximum, except under the FP16 gate, where it carries what
             MF_GATE16_DEBUG puts in im: the pair's all-lag rms (tools/gate16_error.py). */
          if(p->dump){ float rec[8]={ce.magnitude,0.0f,(tr->g16&&!qstat)?ce.im:ce.magnitude,thr,thr,thr,
                                     (float)(d0+d),(float)(t0+t)};
                       fwrite(rec,sizeof rec,1,p->dump); }
          const long pair=first_pair+(long)row+1;
          if(p->trace && pair<6)
            fprintf(stderr,"    [trace] pair=%ld thr=%.3f coarse max=%.3f\n",pair,thr,ce.magnitude);
        }
        if(fire){
          if(qlag) tr->cebuf[row].index = qlag[j];
          tr->fire_d[nnext]=d; tr->fire_t[nnext]=t; nnext++;
        } else if(!fast_sparse){
          reject_row(p,peaks,counts,row,nb);
        }
      }
    }
    tr->checked += i==0 ? (long)nd*nt : nchecked;
    tr->passed += nnext;
    if(i==0) p->first_gate_passed+=nnext;
    fire_d=tr->fire_d; fire_t=tr->fire_t; nfire=nnext;
    if(!nfire) return 0;
  }
  p->trig += nfire;
  unsigned long long r0=ap_ticks();
  int r = hmf_refine(p, fire_d, fire_t, d0, t0, nt, nfire, binsize, threshold,
                     peaks, counts, start, end);
  p->c_ref += ap_ticks()-r0;
  return r;
}

static inline void hmf_sort_ints(int * restrict a,int n){
  static const int gaps[5]={57,23,10,4,1};
  for(int gi=(n>32 ? 0 : 4);gi<5;gi++){
    const int gap=gaps[gi];
    for(int i=gap;i<n;i++){
      const int v=a[i];
      if(v>=a[i-gap]) continue;
      int j=i-gap;
      do { a[j+gap]=a[j]; j-=gap; } while(j>=0 && a[j]>v);
      a[j+gap]=v;
    }
  }
}

static int hmf_run_tier0_clustered(ap_hmf_plan *p,int d0,int nd,int fast_sparse,size_t nb,
                                   ap_peak *peaks,int *counts,size_t start,size_t end,
                                   const int **out_fire_d,const int **out_fire_t,int *out_nfire){
  hmf_tier *tr=&p->tier[0];
  const int nc=p->tier0_nt, nt=p->nt;
  const int * restrict off=p->tier0_off;
  const int * restrict members=p->tier0_members;
  const size_t R=p->n/tr->m;
  const size_t pad=(size_t)(1+p->tier0_lag_pad);
  size_t cstart=start/R;
  size_t cend=(end+R-1)/R+pad;
  if(cend>tr->m) cend=tr->m;
  cstart=cstart>pad ? cstart-pad : 0;
  if(p->tier0_lag_pad>0 && (start<(size_t)p->tier0_lag_pad*R
                            || end+(size_t)p->tier0_lag_pad*R>p->n)){
    cstart=0;
    cend=tr->m;
  }
  const size_t cspan=cend>cstart ? cend-cstart : 1;
  const float thr=tr->thr;
  tr->lagged=0;
  tr->last_q15=0;

  if(tr->npending){
    const int use_g16_0 = (!p->q15 && p->tier0_g16 != NULL);
    const unsigned char pbit0 = use_g16_0 ? HMF_PEND_G16 : HMF_PEND_MF;
    for(int d=d0;d<d0+nd;d++){
      if(tr->pending[d] & pbit0){
        if(ingest_tier_data_target(p,tr,p->tier0_mf,p->tier0_g16,d,p->dspec[d],!use_g16_0,use_g16_0))
          return -1;
        hmf_set_pending(tr,d,(unsigned char)(tr->pending[d] & ~pbit0));
      }
    }
  }

  unsigned long long t_0=ap_ticks();
  const int dump_or_trace=(p->dump || p->trace);
  const long first_pair=p->pairs;
  int nnext=0;

  if(p->q15){
    unsigned long long q0=ap_ticks();
    int ns=ap_mf_q15_screen(p->tier0_mf,d0,nd,0,nc,thr,cstart,cend,p->qpass,
                            dump_or_trace ? p->qstat : NULL);
    if(ns<0) return -1;
    if(fast_sparse && !dump_or_trace){
      if(ns>0){
        for(int d=0;d<nd;d++){
          const int d_start=nnext;
          const unsigned char *qp=p->qpass+(size_t)d*nc;
          int c=0;
          for(;c+8<=nc;c+=8){
            uint64_t w;
            memcpy(&w,qp+c,sizeof w);
            if(!w) continue;
            uint64_t m=(w | ((w & 0x7f7f7f7f7f7f7f7fULL) + 0x7f7f7f7f7f7f7f7fULL))
                       & 0x8080808080808080ULL;
            while(m){
              const int ci=c+(__builtin_ctzll(m)>>3);
              const int u0=off[ci], u1=off[ci+1];
              if(hmf_ensure_fire(tr,(size_t)(nnext+(u1-u0)))) return -1;
              int * restrict dst_d=tr->fire_d;
              int * restrict dst_t=tr->fire_t;
              for(int u=u0;u<u1;u++){
                dst_d[nnext]=d;
                dst_t[nnext]=members[u];
                nnext++;
              }
              m&=m-1;
            }
          }
          for(;c<nc;c++){
            if(qp[c]){
              const int u0=off[c], u1=off[c+1];
              if(hmf_ensure_fire(tr,(size_t)(nnext+(u1-u0)))) return -1;
              int * restrict dst_d=tr->fire_d;
              int * restrict dst_t=tr->fire_t;
              for(int u=u0;u<u1;u++){
                dst_d[nnext]=d;
                dst_t[nnext]=members[u];
                nnext++;
              }
            }
          }
          if(nnext-d_start>1) hmf_sort_ints(tr->fire_t+d_start,nnext-d_start);
        }
      }
    } else {
      for(int d=0;d<nd;d++){
        const int d_start=nnext;
        for(int c=0;c<nc;c++){
          const size_t crow=(size_t)d*nc+c;
          const int fire=p->qpass[crow]!=0;
          const float mag=dump_or_trace ? p->qstat[crow] : 0.0f;
          if(fire && hmf_ensure_fire(tr,(size_t)(nnext+(off[c+1]-off[c])))) return -1;
          for(int u=off[c];u<off[c+1];u++){
            const int t=members[u];
            const size_t row=(size_t)d*nt+t;
            if(fire){
              if(p->dump){
                float rec[8]={mag,0.0f,mag,thr,thr,thr,(float)(d0+d),(float)t};
                fwrite(rec,sizeof rec,1,p->dump);
              }
              const long pair=first_pair+(long)row+1;
              if(p->trace && pair<6)
                fprintf(stderr,"    [trace] pair=%ld thr=%.3f coarse max=%.3f\n",pair,thr,mag);
              tr->fire_d[nnext]=d;
              tr->fire_t[nnext]=t;
              nnext++;
            } else if(!fast_sparse){
              reject_row(p,peaks,counts,row,nb);
            }
          }
        }
        if(nnext-d_start>1) hmf_sort_ints(tr->fire_t+d_start,nnext-d_start);
      }
    }
    p->qpassed+=nnext;
    p->qticks+=ap_ticks()-q0;
    tr->ticks+=ap_ticks()-t_0;
  } else {
    if(hmf_ensure_cebuf(p,tr)) return -1;
    if(p->tier0_g16){
      if(ap_gate16_run(p->tier0_g16,d0,nd,0,nc,cstart,cend,tr->cebuf)<0) return -1;
    } else if(ap_mf_run(p->tier0_mf,d0,nd,0,nc,cspan,thr,tr->cebuf,NULL,cstart,cend)<0){
      return -1;
    }
    tr->ticks+=ap_ticks()-t_0;
    if(fast_sparse && !dump_or_trace){
      for(int d=0;d<nd;d++){
        const int d_start=nnext;
        const ap_peak *ce_row=tr->cebuf+(size_t)d*nc;
        for(int c=0;c<nc;c++){
          if(ce_row[c].index>=0 && ce_row[c].magnitude>=thr){
            const int u0=off[c], u1=off[c+1];
            if(hmf_ensure_fire(tr,(size_t)(nnext+(u1-u0)))) return -1;
            int * restrict dst_d=tr->fire_d;
            int * restrict dst_t=tr->fire_t;
            for(int u=u0;u<u1;u++){
              dst_d[nnext]=d;
              dst_t[nnext]=members[u];
              nnext++;
            }
          }
        }
        if(nnext-d_start>1) hmf_sort_ints(tr->fire_t+d_start,nnext-d_start);
      }
    } else {
      for(int d=0;d<nd;d++){
        const int d_start=nnext;
        for(int c=0;c<nc;c++){
          const ap_peak ce=tr->cebuf[(size_t)d*nc+c];
          const int fire=(ce.index>=0 && ce.magnitude>=thr);
          if(fire && hmf_ensure_fire(tr,(size_t)(nnext+(off[c+1]-off[c])))) return -1;
          for(int u=off[c];u<off[c+1];u++){
            const int t=members[u];
            const size_t row=(size_t)d*nt+t;
            if(fire){
              if(p->dump){
                float rec[8]={ce.magnitude,0.0f,p->tier0_g16 ? ce.im : ce.magnitude,
                              thr,thr,thr,(float)(d0+d),(float)t};
                fwrite(rec,sizeof rec,1,p->dump);
              }
              const long pair=first_pair+(long)row+1;
              if(p->trace && pair<6)
                fprintf(stderr,"    [trace] pair=%ld thr=%.3f coarse max=%.3f\n",
                        pair,thr,ce.magnitude);
              tr->fire_d[nnext]=d;
              tr->fire_t[nnext]=t;
              nnext++;
            } else if(!fast_sparse){
              reject_row(p,peaks,counts,row,nb);
            }
          }
        }
        if(nnext-d_start>1) hmf_sort_ints(tr->fire_t+d_start,nnext-d_start);
      }
    }
  }

  p->pairs+=(long)nd*nt;
  tr->checked+=(long)nd*nc;
  tr->passed+=nnext;
  p->first_gate_passed+=nnext;
  *out_fire_d=tr->fire_d;
  *out_fire_t=tr->fire_t;
  *out_nfire=nnext;
  return nnext>0 ? 1 : 0;
}

static int hmf_run_tier1_clustered(ap_hmf_plan *p,int d0,int fast_sparse,size_t nb,
                                   ap_peak *peaks,int *counts,size_t start,size_t end,
                                   const int *in_d,const int *in_t,int nin,
                                   const int **out_fire_d,const int **out_fire_t,int *out_nfire){
  if(nin<=0){ *out_nfire=0; return 0; }
  hmf_tier *tr=&p->tier[1];
  const int nc1=p->tier1_nt, nt=p->nt;
  const int * restrict off1=p->tier1_off;
  const int * restrict mem1=p->tier1_members;
  const int * restrict map1=p->tier1_map;
  const size_t R=p->n/tr->m;
  const size_t pad=(size_t)(1+p->tier1_lag_pad);
  size_t cstart=start/R;
  size_t cend=(end+R-1)/R+pad;
  if(cend>tr->m) cend=tr->m;
  cstart=cstart>pad ? cstart-pad : 0;
  if(p->tier1_lag_pad>0 && (start<(size_t)p->tier1_lag_pad*R
                            || end+(size_t)p->tier1_lag_pad*R>p->n)){
    cstart=0;
    cend=tr->m;
  }
  const size_t cspan=cend>cstart ? cend-cstart : 1;
  const float thr=tr->thr;
  tr->lagged=0;
  tr->last_q15=0;

  /* Map incoming (d, t) pairs to unique (d, c1) Tier-1 centroid pairs per block. */
  if(!p->qd || !p->qt || !p->qpass){
    const size_t np=(size_t)p->nd*p->nt;
    if(!p->qpass) p->qpass=malloc(np);
    if(!p->qd) p->qd=malloc(np*sizeof(int));
    if(!p->qt) p->qt=malloc(np*sizeof(int));
    if(!p->qpass || !p->qd || !p->qt) return -1;
  }
  int * restrict cd=p->qd;
  int * restrict ct=p->qt;
  int ncand=0;
  for(int j0=0;j0<nin;){
    const int d=in_d[j0];
    int j1=j0;
    const int c_start=ncand;
    while(j1<nin && in_d[j1]==d){
      ct[ncand++]=map1[in_t[j1]];
      j1++;
    }
    const int len=ncand-c_start;
    if(len>1){
      hmf_sort_ints(ct+c_start,len);
      int w=c_start+1;
      for(int r=c_start+1;r<ncand;r++){
        if(ct[r]!=ct[w-1]) ct[w++]=ct[r];
      }
      ncand=w;
    }
    for(int r=c_start;r<ncand;r++) cd[r]=d;
    j0=j1;
  }

  unsigned long long t_0=ap_ticks();
  int ql=0, use_q15=0;
  if(tr->q15 && p->tier1_qtm){
    ql=ap_mf_q15_lanes(p->tier1_mf);
    use_q15 = ql > 0 && ncand >= hmf_min_q15_pairs(ql);
  }
  if(use_q15){
    if(hmf_q15_prepare_data(p,tr,ql)) return -1;
    const size_t stride=2*tr->m+32;
    const size_t khi=tier_khi(p,tr);
    for(int j=0;tr->npending && j<ncand;j++){
      const int gd=d0+cd[j];
      if(tr->pending[gd] & HMF_PEND_Q15){
        int16_t *qdr=tr->qdm+(size_t)gd*stride;
        if(ap_q15_data_band_on(p->full_fft,tr->m,p->dspec[gd],tr->k0,khi,
                               qdr,qdr+tr->m,&tr->qds[gd]))
          return -1;
        hmf_set_pending(tr,gd,(unsigned char)(tr->pending[gd] & ~HMF_PEND_Q15));
      }
    }
    if(ap_q15_pairs_batch_on(p->full_fft,tr->m,tr->qdm,tr->qds,p->tier1_qtm,p->tier1_qts,
                             d0,0,cd,ct,ncand,thr,1,cstart,cend,
                             NULL,NULL,p->qpass,NULL,tr->qscr) < 0)
      return -1;
    tr->last_q15=1;
  } else {
    const int use_g16=(p->tier1_g16 != NULL);
    const unsigned char pbit=use_g16 ? HMF_PEND_G16 : HMF_PEND_MF;
    for(int j=0;tr->npending && j<ncand;j++){
      const int gd=d0+cd[j];
      if(tr->pending[gd] & pbit){
        if(ingest_tier_data_target(p,tr,p->tier1_mf,p->tier1_g16,gd,p->dspec[gd],!use_g16,use_g16))
          return -1;
        hmf_set_pending(tr,gd,(unsigned char)(tr->pending[gd] & ~pbit));
      }
    }
    if(hmf_ensure_cebuf(p,tr)) return -1;
    if(use_g16){
      if(ap_gate16_run_pairs_lag(p->tier1_g16,d0,0,cd,ct,ncand,nc1,cstart,cend,0,thr,
                                 NULL,NULL,tr->cebuf)<0)
        return -1;
    } else if(ap_mf_run_pairs_pooled(p->tier1_mf,d0,cd,ct,ncand,0,cspan,thr,
                                     tr->cebuf,NULL,cstart,cend,nc1)<0){
      return -1;
    }
    for(int j=0;j<ncand;j++){
      const ap_peak ce=tr->cebuf[(size_t)cd[j]*nc1+ct[j]];
      p->qpass[j]=(unsigned char)(ce.index>=0 && ce.magnitude>=thr);
    }
  }
  tr->ticks+=ap_ticks()-t_0;

  /* Expand firing Tier-1 centroids into sorted member template indices per block. Every member
     of a firing centroid came in as a Tier-0 survivor: Tier-1 clusters nest inside Tier-0
     clusters (ap_hmf_set_tier1_clusters), and this path runs only after hmf_run_tier0_clustered
     passed whole Tier-0 clusters on in the same call (ap_hmf_run's conditions match). */
  int nnext=0;
  for(int j0=0;j0<ncand;){
    const int d=cd[j0];
    const int d_start=nnext;
    int j1=j0;
    while(j1<ncand && cd[j1]==d){
      const int c1=ct[j1];
      const int fire=p->qpass[j1]!=0;
      const int u0=off1[c1], u1=off1[c1+1];
      if(fire){
        if(hmf_ensure_fire(tr,(size_t)(nnext+(u1-u0)))) return -1;
        int * restrict dst_d=tr->fire_d;
        int * restrict dst_t=tr->fire_t;
        for(int u=u0;u<u1;u++){
          dst_d[nnext]=d;
          dst_t[nnext]=mem1[u];
          nnext++;
        }
      } else if(!fast_sparse){
        for(int u=u0;u<u1;u++)
          reject_row(p,peaks,counts,(size_t)d*nt+mem1[u],nb);
      }
      j1++;
    }
    if(nnext-d_start>1) hmf_sort_ints(tr->fire_t+d_start,nnext-d_start);
    j0=j1;
  }

  tr->checked+=ncand;
  tr->passed+=nnext;
  *out_fire_d=tr->fire_d;
  *out_fire_t=tr->fire_t;
  *out_nfire=nnext;
  return nnext>0 ? 1 : 0;
}

