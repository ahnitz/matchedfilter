/* Hierarchical matched filter: raw coarse maximum, then full refinement.
 * Calibration is supplied by the caller. No statistical model or recovery
 * fallback is compiled into this execution engine.
 */
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>
#include "ticks.h"
#include "alloc.h"
#include "matchedfilter.h"
#include "transform.h"

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

/* One coarse tier of the gate chain. Tier i runs on the survivors of tier i-1
   (tier 0 on every pair); the survivors of the last tier get the full refine. */
typedef struct {
  size_t m;                       /* band: coarse transform length */
  ap_mf_plan *mf;
  float *scratch,*fpow;           /* staging, per-template band fraction */
  float ref_f,thr;                /* reference band fraction; threshold (<0: unconfigured) */
  ap_peak *cebuf;
  unsigned char *pending;         /* [nd] owned series spectrum awaits ingestion */
  int npending;
  int *fire_d,*fire_t;            /* this tier's survivors */
  long passed;                    /* pairs that passed this tier when evaluated */
  long checked;                   /* actual inputs; independent of execution order */
  unsigned long long ticks;       /* time spent in this tier */
  void *g16;                      /* FP16 gate for this tier (tier 0 only), or NULL */
  int lagged;                     /* this call's cebuf index is the pair's largest coarse lag
                                     (not under the FP16 gate, whose index has no reader) */
} hmf_tier;

struct ap_hmf_plan {
  size_t n;
  size_t k;
  int is_dif;
  int hermitian;
  int nd,nt,dgroup;
  int ntiers;
  hmf_tier tier[AP_HMF_MAX_TIERS];
  ap_mf_plan *full;
  ap_plan *full_fft;
  /* The platform FFT for the block forward (fft_accel.c): a candidate the autotuner
     times against the engine's transform on real calls (ap_hmf_set_platform_fft). */
  ap_accel *accel;
  int use_accel;
  float *fwd,*spec;
  const float **dspec;
  float *dcopy;               /* [nd][2n]: ap_hmf_set_data's own copy of each data spectrum */
  int sparse;                 /* ap_hmf_set_sparse: rows that do not fire write counts only */
  char *dready,*tready;
  int ref_on;
  long pairs,trig;
  unsigned long long c_ref,c_fill;
  unsigned long long c_series;      /* whole ap_hmf_run_series calls: transforms, ingest, tiers, refine */
  int prof,trace;
  FILE *dump;
  float *twiddles,*tw_scratch;
  float *tmpls_half,*prod_scratch;
  /* Q15 screen in front of the first tier (ap_hmf_set_q15) */
  int q15;
  int q15_recheck_late;           /* evaluate tier 1 before the Q15 float recheck */
  long first_gate_passed;         /* passes of the first executed float gate */
  unsigned char *qpass;           /* [nd*nt] */
  int *qd,*qt;                    /* the screen's survivors */
  int q15_g16;                    /* tier 0 behind the screen on the FP16 gate (a price:
                                     ap_hmf_set_q15_tier0) instead of the pooled FP32 pass */
  long qpassed;
  unsigned long long qticks;
  /* Direct refine (ap_hmf_set_taps, ap_hmf_set_direct): a survivor is refined only at the
     lags around its last tier's firing coarse lags, by direct correlation with its real
     taps, where that is priced cheaper than the whole-block transform. */
  float **taps;                   /* [nt] 64-byte aligned taps, or NULL */
  int *tap_len;                   /* [nt] */
  int direct, dir_hw;             /* on; half-width of a window, in last-tier coarse samples */
  const float **dtime;            /* [nd] the block's complex samples (run_series only) */
  size_t *dhave;                  /* [nd] samples present (the rest are zero) */
  float *dx, *dout;               /* [2n] a zero-padded block copy; direct output */
  int *dfd, *dft;                 /* [nd*nt] pairs the transform refines instead */
  double dir_lagtap, dir_fftpair; /* priced: ticks per lag x tap, per whole-block refine */
  long dir_pairs, dir_lags, dir_fft, dir_edge;
  unsigned long long dir_ttd, dir_tfft;  /* ticks: direct, and the pairs it left to transform */
  /* Real series (ap_hmf_set_real_series): ap_hmf_run_series reads real samples and
     transforms each block as n/2 complex ones -- half the transform and half the input --
     then splits that into the block's full (Hermitian) spectrum. */
  int real_series;
  size_t real_stride;             /* floats between samples: 1, or 2 for a lane of a complex series */
  ap_plan *half_fft;              /* n/2-point transform */
  float *rtw;                     /* [2(n/2+1)] cos, sin of 2 pi k/n */
};

int ap_hmf_series_group(const ap_hmf_plan *p){ return p ? p->dgroup : 0; }

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
  /* Execution policy belongs to the caller; the environment is diagnostic. */
  int grp = series_group;
  { const char *e=getenv("MF_DGROUP"); if(e){ int v=atoi(e); if(v>0) grp=v; } }
  /* bounded by what the held spectra cost, which is what bites at long n */
  while(grp>1 && (size_t)grp*2*n*sizeof(float) > (size_t)4*1024*1024) grp>>=1;
  p->dgroup=grp; p->nd=ndata>grp ? ndata : grp;
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
  { const char *pbmax=getenv("MF_PBMAX");
    size_t pblim = pbmax ? (size_t)atol(pbmax) : 512u;
    int lw = ap_lane_width();
    size_t min_ntmpl = (lw > 0) ? (size_t)lw : 16u;
    for(int i=0;i<ntiers;i++){
      hmf_tier *tr=&p->tier[i];
      tr->m=bands[i]; tr->thr=-1;
      if((size_t)ntmpl>=min_ntmpl && tr->m<=pblim) tr->mf=ap_mf_create_pairbatch(tr->m,p->nd,ntmpl);
      if(!tr->mf) tr->mf=ap_mf_create(tr->m,p->nd,ntmpl);
      /* The first tier sees every pair; it is the one worth halving (see gate16.cc). */
      if(i==0 && ap_gate16_available()) tr->g16=ap_gate16_create(tr->m,p->nd,ntmpl);
      tr->scratch=ap_alloc64(2*tr->m*sizeof(float));
      tr->fpow=calloc((size_t)ntmpl,sizeof(float));
      tr->cebuf=calloc((size_t)p->nd*ntmpl,sizeof(ap_peak));
      tr->pending=calloc((size_t)p->nd,1);
      tr->fire_d=calloc((size_t)p->nd*ntmpl,sizeof(int));
      tr->fire_t=calloc((size_t)p->nd*ntmpl,sizeof(int));
      if(!tr->mf||!tr->scratch||!tr->fpow||!tr->cebuf||!tr->pending||!tr->fire_d||!tr->fire_t){
        ap_hmf_destroy(p); return NULL;
      }
    }
  }
  p->full_fft=ap_create(n);
  p->fwd=ap_alloc64(2*n*sizeof(float));
  p->accel=ap_accel_create(n);           /* NULL where the platform has none */
  p->spec=ap_alloc64((size_t)grp*2*n*sizeof(float));
  p->dspec=calloc((size_t)p->nd,sizeof(*p->dspec));
  p->dtime=calloc((size_t)p->nd,sizeof(*p->dtime));
  p->dhave=calloc((size_t)p->nd,sizeof(*p->dhave));
  p->dready=calloc((size_t)p->nd,1);
  p->tready=calloc((size_t)ntmpl,1);
  if(!p->full||!p->full_fft||!p->fwd||!p->spec||!p->dspec||!p->dready||!p->tready
     ||!p->dtime||!p->dhave){
    ap_hmf_destroy(p); return NULL;
  }
  p->prof=getenv("MF_HMF_PROF")!=NULL;
  { const char *e=getenv("MF_HMF_TRACE"); p->trace=e && *e && strcmp(e,"0")!=0; }   /* unset, empty or 0: off */
  const char *dump=getenv("MF_HMF_DUMP");
  p->dump=dump ? fopen(dump,"wb") : NULL;
  return p;
}

void ap_hmf_destroy(ap_hmf_plan *p){
  if(!p) return;
  ap_mf_destroy(p->full);
  for(int i=0;i<p->ntiers;i++){
    hmf_tier *tr=&p->tier[i];
    if(tr->mf) ap_mf_destroy(tr->mf);
    if(tr->g16) ap_gate16_destroy(tr->g16);
    free(tr->scratch); free(tr->fpow); free(tr->cebuf); free(tr->pending);
    free(tr->fire_d); free(tr->fire_t);
  }
  ap_destroy(p->full_fft);
  if(p->half_fft) ap_destroy(p->half_fft);
  free(p->rtw);
  ap_accel_destroy(p->accel);
  free(p->fwd); free(p->spec); free(p->dspec); free(p->dcopy); free(p->dready); free(p->tready);
  if(p->twiddles) free(p->twiddles);
  if(p->tw_scratch) free(p->tw_scratch);
  if(p->tmpls_half) free(p->tmpls_half);
  if(p->prod_scratch) free(p->prod_scratch);
  if(p->dump) fclose(p->dump);
  free(p->qpass); free(p->qd); free(p->qt);
  if(p->taps){ for(int t=0;t<p->nt;t++) free(p->taps[t]); free(p->taps); }
  free(p->tap_len); free(p->dtime); free(p->dhave);  free(p->dx); free(p->dout); free(p->dfd); free(p->dft);
  free(p);
}

/* Each template's real FIR taps: row t holds counts[t] valid taps (stride floats per row),
   centre tap counts[t]/2 at lag 0 -- the filter whose spectrum ap_hmf_set_template holds
   (time_domain._tap_spectra, rate ratio 1). */
int ap_hmf_set_taps(ap_hmf_plan *p,const float *taps,size_t stride,const int64_t *counts){
  if(!p||!taps||!counts) return -1;
  for(int t=0;t<p->nt;t++) if(counts[t]<1||(size_t)counts[t]>stride||(size_t)counts[t]>p->n) return -1;
  if(!p->taps){
    p->taps=calloc((size_t)p->nt,sizeof(*p->taps));
    p->tap_len=calloc((size_t)p->nt,sizeof(int));
    p->dx=ap_alloc64(2*p->n*sizeof(float));
    p->dout=ap_alloc64(2*p->n*sizeof(float));
    p->dfd=malloc((size_t)p->nd*p->nt*sizeof(int));
    p->dft=malloc((size_t)p->nd*p->nt*sizeof(int));
    if(!p->taps||!p->tap_len||!p->dx||!p->dout||!p->dfd||!p->dft) return -1;
  }
  for(int t=0;t<p->nt;t++){
    free(p->taps[t]);
    p->taps[t]=ap_alloc64((size_t)counts[t]*sizeof(float));
    if(!p->taps[t]) return -1;
    memcpy(p->taps[t],taps+(size_t)t*stride,(size_t)counts[t]*sizeof(float));
    p->tap_len[t]=(int)counts[t];
  }
  return 0;
}

/* Ticks per lag x tap of the direct correlation on this core (best of a few reps): what
   the cost model charges a direct refine (gatechain.CostModel.with_direct). */
double ap_hmf_price_direct(void){
  const int L=256, nl=32;
  float *x=ap_alloc64(2*(size_t)(nl+L)*sizeof(float)), *tp=ap_alloc64((size_t)L*sizeof(float));
  float *out=ap_alloc64(2*(size_t)nl*sizeof(float));
  double best=-1;
  if(x&&tp&&out){
    for(int i=0;i<2*(nl+L);i++) x[i]=(float)((i*7919)%1000)/1000.f-0.5f;
    for(int i=0;i<L;i++) tp[i]=(float)((i*104729)%1000)/1000.f-0.5f;
    best=1e30;
    for(int r=0;r<7;r++){
      unsigned long long a=ap_ticks();
      ap_td_corr(x,tp,L,nl,out);
      unsigned long long b=ap_ticks();
      if((double)(b-a)<best) best=(double)(b-a);
    }
    best/=(double)nl*L;
  }
  free(x); free(tp); free(out);
  return best;
}

/* Price the direct correlation (ticks per lag x tap) and the whole-block refine (ticks per
   pair: one inverse transform and its peak scan) on this core, best of a few reps. */
static void price_direct(ap_hmf_plan *p){
  const size_t n=p->n;
  const int L=256, nl=32;
  float *x=ap_alloc64(2*(size_t)(nl+L)*sizeof(float)), *tp=ap_alloc64((size_t)L*sizeof(float));
  float *spec=ap_alloc64(2*n*sizeof(float));
  ap_peak pk[4];
  if(!x||!tp||!spec){ free(x); free(tp); free(spec); return; }
  for(int i=0;i<2*(nl+L);i++) x[i]=(float)((i*7919)%1000)/1000.f-0.5f;
  for(int i=0;i<L;i++) tp[i]=(float)((i*104729)%1000)/1000.f-0.5f;
  for(size_t i=0;i<2*n;i++) spec[i]=(float)((i*31337)%1000)/1000.f-0.5f;
  double best_d=1e30,best_f=1e30;
  for(int r=0;r<5;r++){
    unsigned long long a=ap_ticks();
    ap_td_corr_on(p->full_fft,x,tp,L,nl,p->dout);
    unsigned long long b=ap_ticks();
    int c=0;
    ap_binmax(p->full_fft,spec,n,1,n,1e30f,pk,&c,AP_BACKWARD,0,n);
    unsigned long long e=ap_ticks();
    if((double)(b-a)<best_d) best_d=(double)(b-a);
    if((double)(e-b)<best_f) best_f=(double)(e-b);
  }
  p->dir_lagtap=best_d/((double)nl*L);
  p->dir_fftpair=best_f;
  free(x); free(tp); free(spec);
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

int ap_hmf_set_q15_tier0(ap_hmf_plan *p,int fp16){
  if(!p) return -1;
  if(fp16 && !p->tier[0].g16) return -1;
  p->q15_g16=fp16?1:0;
  return 0;
}

int ap_hmf_set_platform_fft(ap_hmf_plan *p,int on){
  if(!p) return -1;
  if(on && !p->accel) return -1;
  p->use_accel=on?1:0;
  return 0;
}

int ap_hmf_set_q15(ap_hmf_plan *p,int on){
  if(!p) return -1;
  if(!on){ p->q15=0; return 0; }
  if(ap_mf_q15_lanes(p->tier[0].mf)<=0) return -1;
  if(!p->qpass){
    const size_t np=(size_t)p->nd*p->nt;
    p->qpass=malloc(np); p->qd=malloc(np*sizeof(int)); p->qt=malloc(np*sizeof(int));
    if(!p->qpass||!p->qd||!p->qt){
      free(p->qpass); free(p->qd); free(p->qt); p->qpass=NULL; p->qd=p->qt=NULL; return -1;
    }
  }
  p->q15=1;
  return 0;
}
int ap_hmf_set_q15_recheck_late(ap_hmf_plan *p,int on){
  if(!p) return -1;
  /* Any chain with a second tier: it runs on the screen's survivors before the float
     recheck of the first, which then sees only what it kept. */
  if(on && p->ntiers<2) return -1;
  p->q15_recheck_late=!!on;
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

int ap_hmf_set_hermitian(ap_hmf_plan *p,int hermitian){
  if(!p) return -1;
  if(p->hermitian == !!hermitian) return 0;
  p->hermitian = hermitian ? 1 : 0;
  /* The packed DC/Nyquist convention changes both the coarse normalization
     and the refine's template layout. Replay rows already ingested. */
  if(p->is_dif){
    for(int t=0;t<p->nt;t++)
      if(p->tready[t]==1 && ap_hmf_set_template(p,t,p->tmpls_half+(size_t)t*2*p->k)) return -1;
  }
  return 0;
}

int ap_hmf_get_hermitian(const ap_hmf_plan *p){
  return p ? p->hermitian : 0;
}

size_t ap_hmf_nbins(const ap_hmf_plan *p,size_t bs,size_t lo,size_t hi){
  if(!p || !bs) return 0;
  if(hi > p->n) hi = p->n;
  if(lo >= hi) return 0;
  return (hi - lo + bs - 1) / bs;
}
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
/* Each tier's template t: the in-band part of spec (its first m bins; for a Hermitian-packed
   spectrum the Nyquist value in DC's imaginary part is dropped), scaled to unit expected
   power in the band -- by the reference's band fraction, or the template's own without one.
   Nothing unscaled is kept: a later reference change marks the template stale, and the
   caller loads it again (ap_hmf_set_reference). */
static int load_tiers(ap_hmf_plan *p,int t,const float *spec){
  for(int i=0;i<p->ntiers;i++){
    hmf_tier *tr=&p->tier[i];
    double f=p->ref_on ? tr->ref_f : tr->fpow[t];
    double scale=f>0 ? 1/sqrt(f) : 0;
    for(size_t k=0;k<2*tr->m;k++) tr->scratch[k]=(float)(spec[k]*scale);
    if(p->is_dif && p->hermitian) tr->scratch[1]=0.0f;
    if(ap_mf_set_template(tr->mf,t,tr->scratch)) return -1;
    if(tr->g16 && ap_gate16_set_template(tr->g16,t,tr->scratch)) return -1;
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
      for(int i=0;i<p->ntiers;i++) if(k<p->tier[i].m) low[i]+=power[k];
    }
    if(total<=0) return -1;
    for(int i=0;i<p->ntiers;i++) p->tier[i].ref_f=(float)(low[i]/total);
    p->ref_on=1;
  } else p->ref_on=0;
  /* The tier templates already loaded were scaled for the old reference: stale until set
     again (a run over them fails rather than use the old scale). */
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
    if(i>=eager){
      if(!tr->pending[d]){ tr->pending[d]=1; tr->npending++; }
      continue;
    }
    if(ap_mf_set_data(tr->mf,d,spec)) return -1;
    if(tr->g16 && ap_gate16_set_data(tr->g16,d,spec)) return -1;
    if(tr->pending[d]){ tr->pending[d]=0; tr->npending--; }
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
  /* Preserve the public setter's eager coarse copies. Only series calls defer
     them, because their source spectra live in the plan's own storage. */
  return set_data_tiers(p,d,own,p->ntiers);
}
int ap_hmf_set_template(ap_hmf_plan *p,int t,const float *spec){
  if(!p||t<0||t>=p->nt||!spec) return -1;
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
      for(int i=0;i<p->ntiers;i++) if(k<p->tier[i].m) low[i]+=pwr;
    }
    total=dc_pow+nyq_pow+2.0*pos_pow;
    for(int i=0;i<p->ntiers;i++) low[i]+=dc_pow;
  } else {
    for(size_t k=0;k<p->k;k++){
      double re=spec[2*k],im=spec[2*k+1],power=re*re+im*im;
      total+=power;
      for(int i=0;i<p->ntiers;i++) if(k<p->tier[i].m) low[i]+=power;
    }
  }
  for(int i=0;i<p->ntiers;i++){
    hmf_tier *tr=&p->tier[i];
    tr->fpow[t]=total>0 ? (float)(low[i]/total) : 0;
  }
  p->tready[t]=1;
  return load_tiers(p,t,spec);
}

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
int ap_hmf_get_real_series(const ap_hmf_plan *p){ return p ? p->real_series : 0; }

/* The real block at x[s0 .. s0+have) zero-padded to n and scaled by 1/n, transformed into
   its full n-point spectrum sp: the n reals read as n/2 complex z, Z = FFT_{n/2}(z), then
   X[k] = E[k] + W^k O[k] with E = (Z[k] + conj Z[h-k]) / 2, O = (Z[k] - conj Z[h-k]) / 2i,
   W = e^{-2 pi i / n}, for k = 0 .. h, and X[n-k] = conj X[k]. */
static void hmf_forward_real(ap_hmf_plan *p,const float *x,size_t s0,size_t have,float *sp){
  const size_t n=p->n;
  const float inv=1.0f/(float)n;
  float * restrict z=p->fwd;                 /* n reals = h complex */
  float * restrict Z=p->fwd+n;               /* the h-point transform */
  { const size_t st=p->real_stride ? p->real_stride : 1;
    const float * restrict src=x+s0*st;
    if(st==1) for(size_t k=0;k<have;k++) z[k]=src[k]*inv;
    else for(size_t k=0;k<have;k++) z[k]=src[k*st]*inv; }
  if(have<n) memset(z+have,0,(n-have)*sizeof(float));
  ap_fft(p->half_fft,z,Z,AP_FORWARD);
  ap_real_split_on(p->half_fft,Z,p->rtw,n,sp);
}

int ap_hmf_run_series(ap_hmf_plan *p,
                      const float *series,size_t nseries,
                      const size_t *start,const size_t *win_start,
                      const size_t *win_end,int nblocks,
                      int t0,int nt,size_t binsize,float threshold,
                      ap_peak *peaks,int *counts){
  if(!p||nblocks<1||nt<1||!binsize) return 0;
  if(t0<0||t0+nt>p->nt) return -1;
  const unsigned long long call0=ap_ticks();
  const size_t n=p->n;
  const size_t nb0=ap_hmf_nbins(p,binsize,win_start[0],win_end[0]);
  int total=0;
  /* Filter several blocks together where they share a window.  Blocks differ
     only at a segment's edges, so runs of equal windows are long. */
  for(int b0=0;b0<nblocks;){
    int g=1;
    while(g<p->dgroup && b0+g<nblocks
          && win_start[b0+g]==win_start[b0] && win_end[b0+g]==win_end[b0]) g++;
    for(int j=0;j<g;j++){
      const size_t s0=start[b0+j];
      size_t have = s0<nseries ? nseries-s0 : 0;
      if(have>n) have=n;
      if(p->real_series){
        /* A real series: the half-size transform, and no complex samples for the direct
           refine (its NULL dtime sends refines to the transform). */
        float *sp=p->spec+(size_t)j*2*n;
        hmf_forward_real(p,series,s0,have,sp);
        if(set_data_tiers(p,j,sp,1)) return -1;
        p->dtime[j]=NULL; p->dhave[j]=0;
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
      float *const sp=p->spec+(size_t)j*2*n;
      if(p->use_accel){
        ap_accel_forward(p->accel,have ? series+2*s0 : series,have,1.0f/(float)n,sp);
      } else {
      { const float inv=1.0f/(float)n;
        const float * restrict src=have ? series+2*s0 : series;
        float * restrict dst=p->fwd;
        for(size_t k=0;k<2*have;k++) dst[k]=src[k]*inv; }
      if(have<n) memset(p->fwd+2*have,0,2*(n-have)*sizeof(float));
      ap_fft(p->full_fft,p->fwd,sp,AP_FORWARD);
      }
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
    size_t nb=ap_hmf_nbins(p,binsize,win_start[b0],win_end[b0]);
    /* peaks is addressed at a single stride, so every window must produce the
       same bin count. A shorter one at a segment's edge does not: it writes
       where the next block's row begins and runs off the end of the caller's
       buffer -- heap corruption from ordinary overlap-save input, since edge
       blocks are exactly the ragged ones this call exists to accept.
       Refusing is the honest answer; the shape the API returns has one nbins
       in it and cannot express two. */
    if(nb!=nb0) return -1;
    int r=ap_hmf_run(p,0,g,t0,nt,binsize,threshold,
                     peaks+(size_t)b0*nt*nb,counts?counts+(size_t)b0*nt:NULL,
                     win_start[b0],win_end[b0]);
    for(int j=0;j<g;j++) p->dtime[j]=NULL;   /* the caller's series is not held past the call */
    if(r<0) return -1;
    total+=r;
    b0+=g;
  }
  p->c_series += ap_ticks()-call0;
  return total;
}

unsigned long long ap_hmf_series_ticks(const ap_hmf_plan *p){ return p ? p->c_series : 0; }

static int hmf_refine_fft(ap_hmf_plan *p, const int *fire_d, const int *fire_t,
                      int d0, int t0, int nt, int nfire,
                      size_t binsize, float threshold,
                      ap_peak *peaks, int *counts, size_t start, size_t end){
  if(nfire <= 0) return 0;

  if(p->is_dif && p->hermitian){
    const size_t nb = ap_hmf_nbins(p, binsize, start, end);
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
                        peaks + row * nb, &c, AP_BACKWARD, start, end);
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

    const size_t nb = ap_hmf_nbins(p, binsize, start, end);
    int total = 0;
    for(int j = 0; j < nfire; j++){
      const int d = fire_d[j], t = fire_t[j];
      const size_t row = (size_t)d * nt + t;
      int r = ap_mf_run_dif(p->full, 2 * (d0 + d), t0 + t, 1,
                            binsize, threshold, peaks + row * nb,
                            counts ? counts + row : NULL, start, end);
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
    int r = ap_mf_run_pairs_pooled(p->full, d0, fire_d, fire_t, nfire,
                                  t0, binsize, threshold,
                                  peaks, counts, start, end, nt);
    return r;
  }
}

/* One survivor by direct correlation: every lag within dir_hw coarse samples of the coarse
   lags in loc (ncl entries; index < 0 skipped), binned exactly as the transform's scan bins
   its lags. Returns the bins written above threshold, or -2 when the pair is priced cheaper
   as a whole block (or its windows would read past the block). */
static int refine_direct_pair(ap_hmf_plan *p,int d,int t,const ap_peak *loc,size_t ncl,
                              size_t R,size_t binsize,float threshold,
                              ap_peak *out,size_t nb,size_t start,size_t end){
  const size_t n=p->n;
  const int L=p->tap_len[t], c=L/2;
  const long hw=(long)p->dir_hw*(long)R;
  /* the windows: sorted (loc is in lag order), merged where they touch */
  long lo[64], hi[64]; int nw=0; long nlag=0;
  for(size_t j=0;j<ncl;j++){
    if(loc[j].index<0) continue;
    long a=(long)loc[j].index*(long)R-hw, b=(long)loc[j].index*(long)R+hw+1;
    if(a<(long)start) a=(long)start;
    if(b>(long)end) b=(long)end;
    if(a>=b) continue;
    if(nw && a<=hi[nw-1]){ if(b>hi[nw-1]) hi[nw-1]=b; continue; }
    if(nw==64) return -2;
    lo[nw]=a; hi[nw]=b; nw++;
  }
  for(int w=0;w<nw;w++) nlag+=hi[w]-lo[w];
  if(p->trace) fprintf(stderr,"    [direct] pair d=%d t=%d coarse lag %ld R=%zu hw=%ld windows %d lags %ld L=%d"
                       " price %.0f vs %.0f\n",d,t,loc[0].index,R,hw,nw,nlag,L,p->dir_lagtap*(double)nlag*L,
                       p->dir_fftpair);
  if(p->dir_lagtap*(double)nlag*L >= p->dir_fftpair) return -2;
  /* the block's samples; a lag tau reads tau - c .. tau - c + L - 1 */
  const float *x=p->dtime[d];
  const size_t have=p->dhave[d];
  for(int w=0;w<nw;w++)
    if(lo[w]-c<0 || hi[w]-1-c+L>(long)n) return -2;     /* would wrap: the transform's answer */
  if(have<n){
    memcpy(p->dx,x,2*have*sizeof(float));
    memset(p->dx+2*have,0,2*(n-have)*sizeof(float));
    x=p->dx;
  }
  const float t2=threshold>0.f ? threshold*threshold : 0.f;
  for(size_t b=0;b<nb;b++) out[b]=(ap_peak){-1,0.f,0.f,t2};
  for(int w=0;w<nw;w++){
    const int m=(int)(hi[w]-lo[w]);
    ap_td_corr_on(p->full_fft,x+2*(lo[w]-c),p->taps[t],L,m,p->dout);
    for(int i=0;i<m;i++){
      const float re=p->dout[2*i], im=p->dout[2*i+1], m2=re*re+im*im;
      const long k=lo[w]+i;
      const size_t b=(size_t)(k-(long)start)/binsize;
      if(m2>out[b].magnitude){ out[b].magnitude=m2; out[b].index=k; out[b].re=re; out[b].im=im; }
    }
  }
  /* A maximum on a window's edge (one the search window did not put there) may be the
     shoulder of a peak outside it: the localisation the window rests on (the gate model's
     draws) did not hold for this pair, and it takes the whole-block transform instead. On
     data the model describes this never fires (captured consumer calls); on data it does
     not, it is what keeps the answer the transform's. */
  for(size_t b=0;b<nb;b++){
    const long k=out[b].index;
    if(k<0) continue;
    for(int w=0;w<nw;w++)
      if((k==lo[w] && lo[w]>(long)start) || (k==hi[w]-1 && hi[w]<(long)end)){ p->dir_edge++; return -2; }
  }
  int cnt=0;
  for(size_t b=0;b<nb;b++){
    if(out[b].index>=0){ out[b].magnitude=sqrtf(out[b].magnitude); cnt++; }
    else out[b].magnitude=0.f;
  }
  p->dir_pairs++; p->dir_lags+=nlag;
  return cnt;
}

static int hmf_refine(ap_hmf_plan *p, const int *fire_d, const int *fire_t,
                      int d0, int t0, int nt, int nfire,
                      size_t binsize, float threshold,
                      ap_peak *peaks, int *counts, size_t start, size_t end){
  if(nfire<=0) return 0;
  const size_t nb=ap_hmf_nbins(p,binsize,start,end);
  /* One bin per pair: the answer is the window's largest |z|, and it lies by its last tier's
     largest coarse lag (ce.index) -- the window is dir_hw coarse samples either side of it.
     Several bins ask for every bin's maximum above threshold, which one window cannot
     promise: those refine by transform. */
  int ok=p->direct && p->taps && nb==1 && p->tier[p->ntiers-1].lagged;
  for(int j=0;ok && j<nfire;j++) if(!p->dtime[d0+fire_d[j]]) ok=0;
  if(!ok) return hmf_refine_fft(p,fire_d,fire_t,d0,t0,nt,nfire,binsize,threshold,
                                peaks,counts,start,end);
  hmf_tier *tr=&p->tier[p->ntiers-1];
  const size_t R=p->n/tr->m;
  unsigned long long q1=ap_ticks();
  int total=0, nf=0;
  for(int j=0;j<nfire;j++){
    const int d=fire_d[j], t=fire_t[j];
    const size_t row=(size_t)d*nt+t;
    const ap_peak ce=tr->cebuf[row];
    int c=-2;
    if(ce.index>=0)
      c=refine_direct_pair(p,d0+d,t0+t,&ce,1,R,binsize,threshold,peaks+row,1,start,end);
    if(c==-2){ p->dfd[nf]=d; p->dft[nf]=t; nf++; continue; }
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

/* Evaluate an already selected pair list. Logical gate identity and thresholds
   stay fixed even when its position in the execution order changes. */
static int run_gate_pairs(ap_hmf_plan *p,hmf_tier *tr,int d0,int t0,int nt,
                          const int *ds,const int *ts,int count,size_t start,size_t end){
  const size_t r=p->n/tr->m;
  size_t lo=start/r, hi=(end+r-1)/r;
  if(lo>0) lo--;
  if(hi>tr->m) hi=tr->m;
  for(int j=0;tr->npending && j<count;j++){
    const int d=d0+ds[j];
    if(tr->pending[d]){
      if(ap_mf_set_data(tr->mf,d,p->dspec[d])) return -1;
      tr->pending[d]=0; tr->npending--;
    }
  }
  return ap_mf_run_pairs_pooled(tr->mf,d0,ds,ts,count,t0,hi-lo,tr->thr,
                                tr->cebuf,NULL,lo,hi,nt);
}

int ap_hmf_run(ap_hmf_plan *p,int d0,int nd,int t0,int nt,
               size_t binsize,float threshold,
               ap_peak *peaks,int *counts,size_t start,size_t end){
  if(!p||nd<1||nt<1||!binsize) return 0;
  if(d0<0||d0+nd>p->nd||t0<0||t0+nt>p->nt) return -1;
  for(int t=t0;t<t0+nt;t++) if(p->tready[t]==2) return -1;   /* stale since a reference change */
  if(end>p->n) end=p->n;
  if(start>=end) return 0;
  const size_t n=p->n;
  const size_t nb=ap_hmf_nbins(p,binsize,start,end);
  for(int i=0;i<p->ntiers;i++)
    if(!isfinite(p->tier[i].thr) || p->tier[i].thr < 0) return -1;

  const int late_recheck=p->q15 && p->q15_recheck_late && !p->q15_g16;
  const int *fire_d=NULL,*fire_t=NULL;
  int nfire=0;
  for(int i=0;i<p->ntiers;i++){
    if(i==1 && late_recheck) continue;
    hmf_tier *tr=&p->tier[i];
    /* Coarse sample j maps to full lag j*R. Widen by one coarse sample
       so rounding the caller's window remains conservative. */
    const size_t R=n/tr->m;
    size_t cstart = start/R;
    size_t cend   = (end+R-1)/R; if(cend>tr->m) cend=tr->m;
    if(cstart>0) cstart--;
    const size_t cspan = cend>cstart ? cend-cstart : 1;
    const float thr=tr->thr;
    tr->lagged = !(tr->g16 && (i==0 && (!p->q15 || p->q15_g16)));
    const int *checked_d=fire_d,*checked_t=fire_t;
    int nchecked=i==0 ? nd*nt : nfire;
    unsigned long long t_0=ap_ticks(), moved_ticks=0;
    if(i==0 && p->q15){
      /* Screen every pair in int16, then run the float tier on the pairs the
         screen could not reject, pooled as a later tier is.  A pair the screen
         rejects cannot reach thr in the float tier (ap_mf_q15_screen), so the
         survivors -- and everything downstream -- are the float tier's. */
      unsigned long long q0=ap_ticks();
      int ns=ap_mf_q15_screen(tr->mf,d0,nd,t0,nt,thr,cstart,cend,p->qpass,NULL);
      if(ns<0) return -1;
      int k=0;
      for(int d=0;d<nd;d++) for(int t=0;t<nt;t++){
        const size_t row=(size_t)d*nt+t;
        if(p->qpass[row]){ p->qd[k]=d; p->qt[k]=t; k++; }
        else reject_row(p,peaks,counts,row,nb);
      }
      /* Rejected rows are finished.  Revisit only the compacted survivors after
         their float check, avoiding another scan of the full data/template grid. */
      checked_d=p->qd; checked_t=p->qt; nchecked=k;
      p->qpassed+=k;
      p->qticks+=ap_ticks()-q0;
      if(late_recheck){
        hmf_tier *next=&p->tier[1];
        const unsigned long long begin=ap_ticks();
        if(run_gate_pairs(p,next,d0,t0,nt,p->qd,p->qt,k,start,end)<0) return -1;
        next->lagged=1;              /* its cebuf holds each pair's largest coarse lag */
        next->checked+=k;
        int kept=0;
        for(int j=0;j<k;j++){
          const int d=p->qd[j], t=p->qt[j];
          const size_t row=(size_t)d*nt+t;
          const ap_peak ce=next->cebuf[row];
          if(ce.index>=0 && ce.magnitude>=next->thr){
            p->qd[kept]=d; p->qt[kept]=t; kept++;
          }else reject_row(p,peaks,counts,row,nb);
        }
        k=kept; nchecked=k;
        next->passed+=k;
        p->first_gate_passed+=k;
        moved_ticks=ap_ticks()-begin; next->ticks+=moved_ticks;
      }
      if(k && p->q15_g16 && tr->g16){
        /* The FP16 gate over the screen's survivors: its magnitude bounds the FP32 one
           (gate16.cc), so the survivors are a superset of the FP32 pass's; the next tier
           and the refine decide them. */
        if(ap_gate16_run_pairs(tr->g16,d0,t0,p->qd,p->qt,k,nt,cstart,cend,tr->cebuf)<0) return -1;
      } else if(k && ap_mf_run_pairs_pooled(tr->mf,d0,p->qd,p->qt,k,t0,cspan,thr,tr->cebuf,NULL,
                                     cstart,cend,nt)<0) return -1;
    } else if(i==0){
      /* The first tier runs on every pair of the segment in one call: the data
         spectrum is read once and stays resident across the whole template sweep. */
      if(tr->g16){
        /* FP16: the reported magnitude is an upper bound on the FP32 one, so every pair
           the FP32 gate would pass passes here too (gate16.cc). */
        if(ap_gate16_run(tr->g16,d0,nd,t0,nt,cstart,cend,tr->cebuf)<0) return -1;
      } else if(ap_mf_run(tr->mf,d0,nd,t0,nt,cspan,thr,tr->cebuf,NULL,cstart,cend)<0) return -1;
    } else {
      if(run_gate_pairs(p,tr,d0,t0,nt,fire_d,fire_t,nfire,start,end)<0) return -1;
    }
    tr->ticks += ap_ticks()-t_0-moved_ticks;
    int nnext=0;
    const long first_pair=p->pairs;
    if(i==0) p->pairs+=(long)nd*nt;
    for(int j=0;j<nchecked;j++){
      const int d = checked_d ? checked_d[j] : j/nt;
      const int t = checked_t ? checked_t[j] : j%nt;
      const size_t row=(size_t)d*nt+t;
      ap_peak ce = tr->cebuf[row];
      int fire = ce.index>=0 && ce.magnitude>=thr;
      if(i==0 && fire){
        /* rec[2] repeats the maximum, except under the FP16 gate, where it carries what
           MF_GATE16_DEBUG puts in im: the pair's all-lag rms (tools/gate16_error.py). */
        if(p->dump){ float rec[8]={ce.magnitude,0.0f,tr->g16?ce.im:ce.magnitude,thr,thr,thr,
                                   (float)(d0+d),(float)(t0+t)};
                     fwrite(rec,sizeof rec,1,p->dump); }
        const long pair=first_pair+(long)row+1;
        if(p->trace && pair<6)
          fprintf(stderr,"    [trace] pair=%ld thr=%.3f coarse max=%.3f\n",pair,thr,ce.magnitude);
      }
      if(fire){
        tr->fire_d[nnext]=d; tr->fire_t[nnext]=t; nnext++;
      } else {
        reject_row(p,peaks,counts,row,nb);
      }
    }
    tr->checked += nchecked;
    tr->passed += nnext;
    if(i==0 && !late_recheck) p->first_gate_passed+=nnext;
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

/* The price of tier 0 behind the Q15 screen, per listed pair at band m: the pooled FP32 pass
   (*fp32) and the FP16 gate over listed pairs (*fp16, -1 without one), timed on a
   synthetic list of nd x ~1/12 of nt survivors (the screen's realistic pass rate; runs of
   templates per data slot as hmf.c lists them), best of reps. Both results only decide
   which survivors reach the next tier (the FP16 bound is an upper bound on the FP32
   magnitude), so the choice is a cost, not a contest (HierarchicalFilter prices it). */
int ap_hmf_price_q15_tier0(size_t m,int nt,int reps,double *fp32,double *fp16){
  const int nd=8;
  *fp32=*fp16=-1;
  ap_mf_plan *mf=ap_mf_create_pairbatch(m,nd,nt);
  if(!mf) mf=ap_mf_create(m,nd,nt);
  void *g=ap_gate16_available()?ap_gate16_create(m,nd,nt):NULL;
  float *spec=malloc(2*m*sizeof(float));
  int *ds=malloc((size_t)nd*nt*sizeof(int)), *ts=malloc((size_t)nd*nt*sizeof(int));
  ap_peak *out=calloc((size_t)nd*nt,sizeof(ap_peak));
  int rc=-1;
  if(!mf||!spec||!ds||!ts||!out) goto done;
  unsigned s=12345u;
  for(int t=0;t<nt;t++){
    for(size_t k=0;k<2*m;k++){ s=s*1103515245u+12345u; spec[k]=((s>>9)&1023)/1024.0f-0.5f; }
    if(ap_mf_set_template(mf,t,spec)) goto done;
    if(g && ap_gate16_set_template(g,t,spec)) goto done;
  }
  float *dsp=malloc((size_t)nd*2*m*sizeof(float));
  if(!dsp) goto done;
  for(int d=0;d<nd;d++){
    for(size_t k=0;k<2*m;k++){ s=s*1103515245u+12345u; dsp[(size_t)d*2*m+k]=((s>>9)&1023)/1024.0f-0.5f; }
    if(ap_mf_set_data(mf,d,dsp+(size_t)d*2*m)){ free(dsp); goto done; }
    if(g && ap_gate16_set_data(g,d,dsp+(size_t)d*2*m)){ free(dsp); goto done; }
  }
  int n=0;
  for(int d=0;d<nd;d++) for(int t=0;t<nt;t++){
    s=s*1103515245u+12345u;
    if(((s>>8)%12)==0){ ds[n]=d; ts[n]=t; n++; }
  }
  if(n==0){ ds[0]=0; ts[0]=0; n=1; }
  double b32=1e30,b16=1e30;
  for(int r=0;r<reps;r++){
    unsigned long long a=ap_ticks();
    if(ap_mf_run_pairs_pooled(mf,0,ds,ts,n,0,m,1e30f,out,NULL,0,m,nt)<0){ free(dsp); goto done; }
    unsigned long long b=ap_ticks();
    if(g && ap_gate16_run_pairs(g,0,0,ds,ts,n,nt,0,m,out)<0){ free(dsp); goto done; }
    unsigned long long c=ap_ticks();
    if((double)(b-a)<b32) b32=(double)(b-a);
    if(g && (double)(c-b)<b16) b16=(double)(c-b);
  }
  *fp32=b32/n;
  if(g) *fp16=b16/n;
  free(dsp);
  rc=0;
done:
  if(mf) ap_mf_destroy(mf);
  if(g) ap_gate16_destroy(g);
  free(spec); free(ds); free(ts); free(out);
  return rc;
}
