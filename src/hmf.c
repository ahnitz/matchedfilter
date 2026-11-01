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

#define HMF_MAX_DIRECT_BINS 4
#define HMF_COARSE_SUBBINS 16

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
  int *fire_d,*fire_t;            /* this tier's survivors */
  long passed;                    /* pairs that passed this tier when evaluated */
  long checked;                   /* actual inputs; independent of execution order */
  unsigned long long ticks;       /* time spent in this tier */
  void *g16;                      /* FP16 gate for this tier (tier 0 only), or NULL */
  int lagged;                     /* this call's cebuf index is the pair's largest coarse lag
                                     (not under the FP16 gate, whose index has no reader) */
  int q15;                        /* a later tier gating on the listed Q15 screen
                                     (ap_mf_q15_pairs), with the screen on */
  int last_q15;                   /* this call ran on the listed Q15 screen */
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
  /* The platform FFT for the block forward (fft_accel.c): a candidate the autotuner
     times against the engine's transform on real calls (ap_hmf_set_platform_fft). */
  ap_accel *accel;
  int use_accel;
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
  int *dfd, *dft;                 /* [nd*nt] pairs the transform refines instead */
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
  int grp = v>0 ? (int)v : (requested>0 ? requested : (n<=2048 ? 32 : 16));
  const size_t cap = v>0 ? (size_t)4*1024*1024 : (size_t)512*1024;
  while(grp>1 && (size_t)grp*2*n*sizeof(float) > cap) grp>>=1;
  return grp;
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
  if(p->full_fft && n>=64 && n<=(ap_plan_lanes(p->full_fft)>=16 ? 2048u : 512u))
    p->fwd_cplx_batch=ap_create_pairbatch_like(p->full_fft,n);
  p->fwd=ap_alloc64(2*n*sizeof(float));
  p->accel=ap_accel_create(n);           /* NULL where the platform has none */
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
  if(p->fwd_cplx_batch) ap_destroy(p->fwd_cplx_batch);
  if(p->fwd_real_batch) ap_destroy(p->fwd_real_batch);
  free(p->rtw);
  ap_accel_destroy(p->accel);
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
    p->dfd=malloc((size_t)p->nd*p->nt*sizeof(int));
    p->dft=malloc((size_t)p->nd*p->nt*sizeof(int));
    if(!p->taps||!p->tap_len||!p->dx||!p->dout||!p->dfd||!p->dft) goto fail;
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

/* Ticks per lag x tap of the direct correlation on this core (best of a few reps): what
   the cost model charges a direct refine (gatechain.CostModel.with_direct). */
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
    best=1e30;
    for(int r=0;r<7;r++){
      unsigned long long a=ap_ticks();
      ap_td_corr_ex(x,x_real?1:0,tr,ti,L,nl,out);
      unsigned long long b=ap_ticks();
      if((double)(b-a)<best) best=(double)(b-a);
    }
    best/=(double)nl*L;
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
  double best_d=1e30, best_f=1e30;
  for(int r=0;r<7;r++){
    const int s=r&(nslot-1);
    float *sp=spec+(size_t)s*2*n;
    float *drs=dr+(size_t)s*n, *dis=di+(size_t)s*n;
    const float *trs=tr_s+(size_t)s*n, *tis=ti_s+(size_t)s*n;
    unsigned long long a=ap_ticks();
    ap_td_corr_ex_on(p->full_fft,x,p->real_series,tr,ti,L,nl,dout);
    unsigned long long b=ap_ticks();
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
    unsigned long long e=ap_ticks();
    if((double)(b-a)<best_d) best_d=(double)(b-a);
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

int ap_hmf_set_platform_fft(ap_hmf_plan *p,int on){
  if(!p) return -1;
  if(on && !p->accel) return -1;
  p->use_accel=on?1:0;
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
static int ingest_tier_data(const ap_hmf_plan *p,hmf_tier *tr,int d,const float *spec,
                            int to_mf,int to_g16){
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
  if(to_mf && ap_mf_set_data(tr->mf,d,src)) return -1;
  if(to_g16 && tr->g16 && ap_gate16_set_data(tr->g16,d,src)) return -1;
  return 0;
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
  for(int i=0;i<ntiers;i++) p->tier[i].k0 = k0s[i];
  for(int t=0;t<p->nt;t++) if(p->tready[t]==1) p->tready[t]=2;
  if(p->dcopy){
    const size_t row = 2*p->n;
    for(int d=0;d<p->nd;d++)
      if(p->dmirrored[d] && p->dspec[d]==p->dcopy+(size_t)d*row){
        for(int i=0;i<p->ntiers;i++){
          hmf_tier *tr=&p->tier[i];
          if(i==0 && tr->g16 && !p->q15){
            if(ingest_tier_data(p,tr,d,p->dcopy+(size_t)d*row,0,1)) return -1;
            if(!tr->pending[d]){ tr->pending[d]=1; tr->npending++; }
          } else {
            if(ingest_tier_data(p,tr,d,p->dcopy+(size_t)d*row,1,1)) return -1;
            if(tr->pending[d]){ tr->pending[d]=0; tr->npending--; }
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
    if(i==0 && tr->g16 && !p->q15){
      if(ingest_tier_data(p,tr,d,spec,0,1)) return -1;
      if(!tr->pending[d]){ tr->pending[d]=1; tr->npending++; }
      continue;
    }
    if(ingest_tier_data(p,tr,d,spec,1,1)) return -1;
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
  p->dmirrored[d]=1;
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
    if(h>=64 && h<=(ap_plan_lanes(p->full_fft)>=16 ? 2048u : 512u))
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
  if(p->real_series && !p->fwd_real_batch && p->half_fft && n>=128 && n<=4096)
    p->fwd_real_batch=ap_create_pairbatch_like(p->full_fft,n/2);
  if(!p->real_series && !p->use_accel && !p->fwd_cplx_batch && p->full_fft && n>=64 && n<=2048)
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
  } else if(!p->real_series && !p->use_accel && p->fwd_cplx_batch){
    const int W = ap_plan_lanes(p->fwd_cplx_batch);
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
        srcs[l]=have ? series+2*s0 : series;
        haves[l]=have;
        outs[l]=p->spec+(size_t)(j+l)*sstride;
      }
      if(ap_fft_forward_batch(p->fwd_cplx_batch,srcs,haves,cnt,inv,outs)<0) return -1;
      for(int l=0; l<cnt; l++){
        p->dmirrored[j+l]=1;
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
    if(p->use_accel){
      ap_accel_forward(p->accel,have ? series+2*s0 : series,have,1.0f/(float)n,sp);
    } else {
      ap_fft_forward_scaled(p->full_fft,have ? series+2*s0 : series,2*have,1,1.0f/(float)n,sp);
    }
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

/* Transform two packed strided real lanes (even/odd floats of one complex64 series) per
   W-block mini-batch so the second lane hits L1/L2 before template sweeps evict the input. */
static int hmf_forward_slab_quad_pair(ap_hmf_plan *pa,const float *sa,
                                      ap_hmf_plan *pb,const float *sb,
                                      size_t nseries,const size_t *start,int b0,int g){
  const size_t n=pa->n;
  const size_t sstride=2u*n+16u;
  if(!pa->fwd_real_batch && pa->half_fft && n>=128 && n<=4096)
    pa->fwd_real_batch=ap_create_pairbatch_like(pa->full_fft,n/2);
  if(!pb->fwd_real_batch && pb->half_fft && n>=128 && n<=4096)
    pb->fwd_real_batch=ap_create_pairbatch_like(pb->full_fft,n/2);
  const int wa = pa->fwd_real_batch ? ap_plan_lanes(pa->fwd_real_batch) : 0;
  const int wb = pb->fwd_real_batch ? ap_plan_lanes(pb->fwd_real_batch) : 0;
  if(!(wa>0 && wa==wb && n<=4096)){
    const unsigned long long t0=ap_ticks();
    if(hmf_forward_slab(pa,sa,nseries,start,b0,g)<0) return -1;
    const unsigned long long t1=ap_ticks();
    pa->c_series += t1-t0;
    if(hmf_forward_slab(pb,sb,nseries,start,b0,g)<0) return -1;
    pb->c_series += ap_ticks()-t1;
    return 0;
  }
  const int W = wa;
  const float inv = 1.0f/(float)n;
  for(int j=0;j<g;j+=W){
    const int cnt = g-j<W ? g-j : W;
    const float *srca[AP_MAX_LANES], *srcb[AP_MAX_LANES];
    size_t haves[AP_MAX_LANES];
    float *outa[AP_MAX_LANES], *outb[AP_MAX_LANES];
    for(int l=0;l<cnt;l++){
      const size_t s0=start[b0+j+l];
      size_t have = s0<nseries ? nseries-s0 : 0;
      if(have>n) have=n;
      srca[l]=have ? sa+2u*s0 : sa;
      srcb[l]=have ? sb+2u*s0 : sb;
      haves[l]=have;
      outa[l]=pa->spec+(size_t)(j+l)*sstride;
      outb[l]=pb->spec+(size_t)(j+l)*sstride;
    }
    const unsigned long long t0=ap_ticks();
    if(ap_fft_real_batch(pa->fwd_real_batch,srca,haves,2,cnt,inv,pa->rtw,0,outa)<0) return -1;
    const unsigned long long t1=ap_ticks();
    pa->c_series += t1-t0;
    if(ap_fft_real_batch(pb->fwd_real_batch,srcb,haves,2,cnt,inv,pb->rtw,0,outb)<0) return -1;
    const unsigned long long t2=ap_ticks();
    pb->c_series += t2-t1;
    for(int l=0;l<cnt;l++){
      pa->dmirrored[j+l]=0;
      if(set_data_tiers(pa,j+l,outa[l],1)) return -1;
      pa->dtime[j+l]=haves[l] ? srca[l] : NULL; pa->dhave[j+l]=haves[l];
    }
    const unsigned long long t3=ap_ticks();
    pa->c_series += t3-t2;
    for(int l=0;l<cnt;l++){
      pb->dmirrored[j+l]=0;
      if(set_data_tiers(pb,j+l,outb[l],1)) return -1;
      pb->dtime[j+l]=haves[l] ? srcb[l] : NULL; pb->dhave[j+l]=haves[l];
    }
    pb->c_series += ap_ticks()-t3;
  }
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
        int qpeer=-1;
        if(lp->real_series && lp->real_stride==2 && !lp->use_accel){
          for(int k=c0;k<c1;k++){
            if(k==lead || b0[k]+g>jobs[k].nblocks) continue;
            ap_hmf_sparse_job *kjb=&jobs[k];
            ap_hmf_plan *kp=kjb->p;
            if(kp==lp || !kp->real_series || kp->real_stride!=2 || kp->use_accel
               || kp->n!=lp->n || g>kp->dgroup || kjb->nseries!=ljb->nseries
               || !(kjb->series==ljb->series+1 || ljb->series==kjb->series+1))
              continue;
            if(!hmf_job_win_ok(kjb,b0[k],g,nb0[k])) continue;
            if(memcmp(kjb->start+b0[k],ljb->start+b0[lead],(size_t)g*sizeof(size_t))!=0) continue;
            qpeer=k;
            break;
          }
        }

        if(qpeer>=0){
          ap_hmf_sparse_job *qjb=&jobs[qpeer];
          if(hmf_forward_slab_quad_pair(lp,ljb->series,qjb->p,qjb->series,
                                        ljb->nseries,ljb->start,b0[lead],g)<0) goto fail;
        } else {
          const unsigned long long t_fwd=ap_ticks();
          if(hmf_forward_slab(lp,ljb->series,ljb->nseries,ljb->start,b0[lead],g)<0) goto fail;
          lp->c_series += ap_ticks()-t_fwd;
        }

        if(hmf_run_sparse_slab(ljb,&caps[lead],b0[lead],g,nb0[lead],slab_pk,slab_cnt)<0){
          for(int j=0;j<g;j++) lp->dtime[j]=NULL;
          if(qpeer>=0) for(int j=0;j<g;j++) jobs[qpeer].p->dtime[j]=NULL;
          goto fail;
        }

        /* Share lead's L2-hot forward spectra with any cluster peer on identical block starts. */
        const size_t sstride=2u*lp->n+16u;
        const size_t lst=lp->real_stride ? lp->real_stride : 1u;
        for(int k=c0;k<c1;k++){
          if(k==lead || k==qpeer || b0[k]+g>jobs[k].nblocks) continue;
          ap_hmf_sparse_job *kjb=&jobs[k];
          ap_hmf_plan *kp=kjb->p;
          const size_t kst=kp->real_stride ? kp->real_stride : 1u;
          if(kp->n!=lp->n || g>kp->dgroup || kp->real_series!=lp->real_series || kst!=lst
             || kp->use_accel!=lp->use_accel
             || ap_plan_lanes(kp->full_fft)!=ap_plan_lanes(lp->full_fft)
             || kjb->series!=ljb->series || kjb->nseries!=ljb->nseries) continue;
          if(!hmf_job_win_ok(kjb,b0[k],g,nb0[k])) continue;
          if(memcmp(kjb->start+b0[k],ljb->start+b0[lead],(size_t)g*sizeof(size_t))!=0) continue;

          if(kp!=lp){
            const unsigned long long t_sh=ap_ticks();
            for(int j=0;j<g;j++){
              kp->dmirrored[j]=lp->dmirrored[j];
              if(set_data_tiers(kp,j,lp->spec+(size_t)j*sstride,1)){
                for(int u=0;u<=j;u++){ kp->dtime[u]=NULL; kp->dspec[u]=NULL; kp->dready[u]=0; }
                for(int u=0;u<g;u++) lp->dtime[u]=NULL;
                if(qpeer>=0) for(int u=0;u<g;u++) jobs[qpeer].p->dtime[u]=NULL;
                goto fail;
              }
              kp->dtime[j]=lp->dtime[j]; kp->dhave[j]=lp->dhave[j];
            }
            kp->c_series += ap_ticks()-t_sh;
          }
          const int rc=hmf_run_sparse_slab(kjb,&caps[k],b0[k],g,nb0[k],slab_pk,slab_cnt);
          if(kp!=lp){
            for(int j=0;j<g;j++){
              lp->dmirrored[j] |= kp->dmirrored[j];
              kp->dtime[j]=NULL; kp->dspec[j]=NULL; kp->dready[j]=0;
            }
          }
          if(rc<0){
            for(int u=0;u<g;u++) lp->dtime[u]=NULL;
            if(qpeer>=0) for(int u=0;u<g;u++) jobs[qpeer].p->dtime[u]=NULL;
            goto fail;
          }
          b0[k]+=g;
        }
        for(int j=0;j<g;j++) lp->dtime[j]=NULL;
        b0[lead]+=g;

        if(qpeer>=0){
          ap_hmf_sparse_job *qjb=&jobs[qpeer];
          ap_hmf_plan *qp=qjb->p;
          const int qrc=hmf_run_sparse_slab(qjb,&caps[qpeer],b0[qpeer],g,nb0[qpeer],slab_pk,slab_cnt);
          for(int j=0;j<g;j++) qp->dtime[j]=NULL;
          if(qrc<0) goto fail;
          b0[qpeer]+=g;
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
  /* Complete negative-frequency bins on any real-series block whose survivor reaches FFT refine. */
  if(p->real_series){
    for(int j = 0; j < nfire; j++){
      const int idx = d0 + fire_d[j];
      if(!p->dmirrored[idx]){
        if(!p->dspec[idx]) return -1;
        ap_real_split_mirror_on(p->full_fft, (float *)p->dspec[idx], p->n);
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
      }
    } else if(s_max>have){
      const size_t avail=have>s_min ? have-s_min : 0;
      if(avail) memcpy(p->dx+2*s_min,x+2*s_min,2*avail*sizeof(float));
      memset(p->dx+2*(s_min+avail),0,2*(s_max-s_min-avail)*sizeof(float));
      x=p->dx;
    }
  }
  const float *tr=p->taps[t];
  const float *ti=p->tap_cplx ? tr+tap_imag_offset(L) : NULL;
  const float t2=threshold>0.f ? threshold*threshold : 0.f;
  for(size_t b=0;b<nb;b++) out[b]=(ap_peak){-1,0.f,0.f,t2};
  for(int w=0;w<nw;w++){
    const int m=(int)(hi[w]-lo[w]);
    const float *xw=p->real_series ? x+(lo[w]-c) : x+2*(lo[w]-c);
    ap_td_corr_ex_on(p->full_fft,xw,p->real_series,tr,ti,L,m,p->dout);
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
  int ns=0, have_sub=0;
  for(int j=0;j<nfire;j++){
    const int d=fire_d[j], t=fire_t[j];
    if(survivor_needs_sub(p,tr,d0+d,t0+t,(size_t)d*nt+t,start,hi,R,binsize)){
      p->dfd[ns]=d; p->dft[ns]=t; ns++;
    }
  }
  if(ns>0 && ncb>1){
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
          if(ap_mf_correlate(tr->mf,d0+d,1,t0+t,1,tr->scratch)){ corr_ok=0; break; }
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

/* Evaluate an already selected pair list. Logical gate identity and thresholds
   stay fixed even when its position in the execution order changes. */
static int run_gate_pairs(ap_hmf_plan *p,hmf_tier *tr,int d0,int t0,int nt,
                          const int *ds,const int *ts,int count,size_t start,size_t end,
                          int use_q15,int16_t *qlag){
  const size_t r=p->n/tr->m;
  size_t lo=start/r, hi=(end+r-1)/r+1;      /* as ap_hmf_run: one coarse sample past each end */
  if(lo>0) lo--;
  if(hi>tr->m) hi=tr->m;
  for(int j=0;tr->npending && j<count;j++){
    const int d=d0+ds[j];
    if(tr->pending[d]){
      if(ingest_tier_data(p,tr,d,p->dspec[d],1,0)) return -1;
      tr->pending[d]=0; tr->npending--;
    }
  }
  /* A Q15 tier's decision per listed pair goes to p->qpass[j] (free once the first tier's
     survivors are compacted), with optional coarse argmax lag in qlag[j]; an FP32 tier's
     maximum goes to its cebuf. */
  if(use_q15)
    return ap_mf_q15_pairs_lag(tr->mf,d0,ds,ts,count,t0,tr->thr,lo,hi,p->qpass,NULL,qlag);
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
    const float thr=tr->thr;
    tr->lagged = !(tr->g16 && i==0 && !p->q15);
    tr->last_q15 = 0;
    const int *checked_d=fire_d,*checked_t=fire_t;
    int nchecked=i==0 ? nd*nt : nfire;
    if(i==0 && (p->q15 || !tr->g16) && tr->npending){
      for(int d=d0;d<d0+nd;d++)
        if(tr->pending[d]){
          if(ingest_tier_data(p,tr,d,p->dspec[d],1,0)) return -1;
          tr->pending[d]=0; tr->npending--;
        }
    }
    unsigned long long t_0=ap_ticks();
    float *qstat=NULL;               /* set: the screen decided, and this is its maximum */
    int16_t *qlag=NULL;
    int use_q15=0;
    int q15_direct_fire=0;
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
      if(tr->g16){
        /* FP16: the reported magnitude is an upper bound on the FP32 one, so every pair
           the FP32 gate would pass passes here too (gate16.cc). */
        if(ap_gate16_run(tr->g16,d0,nd,t0,nt,cstart,cend,tr->cebuf)<0) return -1;
      } else if(ap_mf_run(tr->mf,d0,nd,t0,nt,cspan,thr,tr->cebuf,NULL,cstart,cend)<0) return -1;
    } else {
      if(tr->q15){
        const int ql = ap_mf_q15_lanes(tr->mf);
        const long nslabs = ql>0 ? ((long)nd+ql-1)/ql : 1;
        /* Intermediate tiers gate in listed Q15 down to ~0.25 survivors per (slab, template);
           the final tier also elects coarse lags and only switches to Q15 above ~2 per group. */
        const long min_q15 = (i+1<p->ntiers) ? ((nslabs*(long)nt)>>2) : (2L*nslabs*(long)nt);
        use_q15 = nfire >= min_q15;
      }
      qlag = (use_q15 && i==p->ntiers-1 && p->direct && p->taps) ? p->qidx : NULL;
      if(run_gate_pairs(p,tr,d0,t0,nt,fire_d,fire_t,nfire,start,end,use_q15,qlag)<0) return -1;
      if(use_q15){ tr->lagged = (qlag != NULL); tr->last_q15 = 1; }
    }
    tr->ticks += ap_ticks()-t_0;
    int nnext=0;
    const long first_pair=p->pairs;
    if(i==0) p->pairs+=(long)nd*nt;
    if(q15_direct_fire){
      nnext = nchecked;
    } else for(int j=0;j<nchecked;j++){
      const int d = checked_d ? checked_d[j] : j/nt;
      const int t = checked_t ? checked_t[j] : j%nt;
      const size_t row=(size_t)d*nt+t;
      const ap_peak ce = qstat ? (ap_peak){.index=0,
                                           .magnitude=(p->dump||p->trace) ? qstat[row] : 0.0f}
                               : tr->cebuf[row];
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

