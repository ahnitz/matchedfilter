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

/* One coarse tier of the gate chain. Tier i runs on the survivors of tier i-1
   (tier 0 on every pair); the survivors of the last tier get the full refine. */
typedef struct {
  size_t m;                       /* band: coarse transform length */
  ap_mf_plan *mf;
  float *ct0,*scratch,*fpow;      /* unscaled in-band templates, staging, per-template band fraction */
  float ref_f,thr;                /* reference band fraction; threshold (<0: unconfigured) */
  ap_peak *cebuf;
  int *fire_d,*fire_t;            /* this tier's survivors */
  long passed;                    /* pairs that passed this tier */
  unsigned long long ticks;       /* time spent in this tier */
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
  float *fwd,*spec;
  const float **dspec;
  char *dready,*tready;
  int ref_on;
  long pairs,trig;
  unsigned long long c_ref,c_fill;
  unsigned long long c_series;      /* whole ap_hmf_run_series calls: transforms, ingest, tiers, refine */
  int prof,trace;
  FILE *dump;
  float *twiddles,*tw_scratch;
  float *tmpls_half,*prod_scratch;
  ap_peak *dif_pk_e,*dif_pk_o;
  size_t dif_pkcap;
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
    p->dif_pkcap=16;
    p->dif_pk_e=malloc(p->dif_pkcap*sizeof(ap_peak));
    p->dif_pk_o=malloc(p->dif_pkcap*sizeof(ap_peak));
    if(!p->twiddles || !p->tw_scratch || !p->dif_pk_e || !p->dif_pk_o
       || !p->tmpls_half || !p->prod_scratch){
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
      tr->ct0=ap_alloc64((size_t)ntmpl*2*tr->m*sizeof(float));
      tr->scratch=ap_alloc64(2*tr->m*sizeof(float));
      tr->fpow=calloc((size_t)ntmpl,sizeof(float));
      tr->cebuf=calloc((size_t)p->nd*ntmpl,sizeof(ap_peak));
      tr->fire_d=calloc((size_t)p->nd*ntmpl,sizeof(int));
      tr->fire_t=calloc((size_t)p->nd*ntmpl,sizeof(int));
      if(!tr->mf||!tr->ct0||!tr->scratch||!tr->fpow||!tr->cebuf||!tr->fire_d||!tr->fire_t){
        ap_hmf_destroy(p); return NULL;
      }
    }
  }
  p->full_fft=ap_create(n);
  p->fwd=ap_alloc64(2*n*sizeof(float));
  p->spec=ap_alloc64((size_t)grp*2*n*sizeof(float));
  p->dspec=calloc((size_t)p->nd,sizeof(*p->dspec));
  p->dready=calloc((size_t)p->nd,1);
  p->tready=calloc((size_t)ntmpl,1);
  if(!p->full||!p->full_fft||!p->fwd||!p->spec||!p->dspec||!p->dready||!p->tready){
    ap_hmf_destroy(p); return NULL;
  }
  p->prof=getenv("MF_HMF_PROF")!=NULL;
  p->trace=getenv("MF_HMF_TRACE")!=NULL;
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
    free(tr->ct0); free(tr->scratch); free(tr->fpow); free(tr->cebuf);
    free(tr->fire_d); free(tr->fire_t);
  }
  ap_destroy(p->full_fft);
  free(p->fwd); free(p->spec); free(p->dspec); free(p->dready); free(p->tready);
  if(p->twiddles) free(p->twiddles);
  if(p->tw_scratch) free(p->tw_scratch);
  if(p->tmpls_half) free(p->tmpls_half);
  if(p->prod_scratch) free(p->prod_scratch);
  if(p->dif_pk_e) free(p->dif_pk_e);
  if(p->dif_pk_o) free(p->dif_pk_o);
  if(p->dump) fclose(p->dump);
  free(p);
}

int ap_hmf_set_hermitian(ap_hmf_plan *p,int hermitian){
  if(!p) return -1;
  p->hermitian = hermitian ? 1 : 0;
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
static int refresh_template(ap_hmf_plan *p,int t){
  for(int i=0;i<p->ntiers;i++){
    hmf_tier *tr=&p->tier[i];
    double f=p->ref_on ? tr->ref_f : tr->fpow[t];
    double scale=f>0 ? 1/sqrt(f) : 0;
    const float *original=tr->ct0+(size_t)t*2*tr->m;
    for(size_t k=0;k<2*tr->m;k++) tr->scratch[k]=(float)(original[k]*scale);
    if(ap_mf_set_template(tr->mf,t,tr->scratch)) return -1;
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
  for(int t=0;t<p->nt;t++) if(p->tready[t] && refresh_template(p,t)) return -1;
  return 0;
}
int ap_hmf_set_data(ap_hmf_plan *p,int d,const float *spec){
  if(!p||d<0||d>=p->nd||!spec) return -1;
  p->dspec[d]=spec; p->dready[d]=0;
  for(int i=0;i<p->ntiers;i++) if(ap_mf_set_data(p->tier[i].mf,d,spec)) return -1;
  return 0;
}
int ap_hmf_set_template(ap_hmf_plan *p,int t,const float *spec){
  if(!p||t<0||t>=p->nt||!spec) return -1;
  if(p->is_dif){
    if(p->tmpls_half) memcpy(p->tmpls_half+(size_t)t*2*p->k,spec,2*p->k*sizeof(float));
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
    memcpy(tr->ct0+(size_t)t*2*tr->m,spec,2*tr->m*sizeof(float));
    if(p->is_dif && p->hermitian) (tr->ct0+(size_t)t*2*tr->m)[1]=0.0f;
  }
  p->tready[t]=1;
  return refresh_template(p,t);
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
      /* pycbc's inverse is unnormalised and so is matchedfilter's, so the
         caller's convention of pre-dividing the block spectrum by n is kept.
         Doing it on the way IN rather than to the result folds it into a copy
         that has to happen anyway and removes a separate pass over 2n floats
         -- 12% of the per-block cost, which is itself 12% of the total at 37
         templates.  n is a power of two, so 1/n is exact and the transform is
         linear: scaling before is bit-for-bit the same as scaling after, which
         the fixtures check by reproducing pycbc's SNRs to 0.0e+00. */
      { const float inv=1.0f/(float)n;
        const float * restrict src=have ? series+2*s0 : series;
        float * restrict dst=p->fwd;
        for(size_t k=0;k<2*have;k++) dst[k]=src[k]*inv; }
      if(have<n) memset(p->fwd+2*have,0,2*(n-have)*sizeof(float));
      float *const sp=p->spec+(size_t)j*2*n;
      ap_fft(p->full_fft,p->fwd,sp,AP_FORWARD);
      if(ap_hmf_set_data(p,j,sp)) return -1;
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
    if(r<0) return -1;
    total+=r;
    b0+=g;
  }
  p->c_series += ap_ticks()-call0;
  return total;
}

unsigned long long ap_hmf_series_ticks(const ap_hmf_plan *p){ return p ? p->c_series : 0; }

static int hmf_refine(ap_hmf_plan *p, const int *fire_d, const int *fire_t,
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
    size_t wk_s_e = (start + 1) / 2;
    size_t wk_e_e = (end + 1) / 2;
    if(wk_e_e > p->k) wk_e_e = p->k;
    if(wk_s_e > wk_e_e) wk_s_e = wk_e_e;

    size_t wk_s_o = start / 2;
    size_t wk_e_o = end / 2;
    if(wk_e_o > p->k) wk_e_o = p->k;
    if(wk_s_o > wk_e_o) wk_s_o = wk_e_o;

    size_t bs_k = (binsize >= p->n) ? p->k : (binsize / 2 > 0 ? binsize / 2 : 1);
    size_t nb_e = (wk_e_e > wk_s_e) ? (wk_e_e - wk_s_e + bs_k - 1) / bs_k : 0;
    size_t nb_o = (wk_e_o > wk_s_o) ? (wk_e_o - wk_s_o + bs_k - 1) / bs_k : 0;
    size_t nb_alloc = nb > nb_e ? nb : nb_e;
    if(nb_o > nb_alloc) nb_alloc = nb_o;
    if(nb_alloc == 0) nb_alloc = 1;
    if(p->dif_pkcap < nb_alloc){
      free(p->dif_pk_e); free(p->dif_pk_o);
      p->dif_pk_e = malloc(nb_alloc * sizeof(ap_peak));
      p->dif_pk_o = malloc(nb_alloc * sizeof(ap_peak));
      if(!p->dif_pk_e || !p->dif_pk_o){ p->dif_pkcap = 0; return -1; }
      p->dif_pkcap = nb_alloc;
    }

    int total = 0;

    for(int j = 0; j < nfire; j++){
      int d = fire_d[j];
      int t = fire_t[j];
      const size_t row = (size_t)d * nt + t;

      for(size_t b = 0; b < nb_alloc; b++){
        p->dif_pk_e[b] = (ap_peak){-1, 0.f, 0.f, 0.f};
        p->dif_pk_o[b] = (ap_peak){-1, 0.f, 0.f, 0.f};
      }

      int r_e = (wk_s_e < wk_e_e)
        ? ap_mf_run(p->full, 2 * (d0 + d), 1, t0 + t, 1, bs_k, threshold,
                    p->dif_pk_e, NULL, wk_s_e, wk_e_e)
        : 0;
      if(r_e < 0) return -1;

      int r_o = (wk_s_o < wk_e_o)
        ? ap_mf_run(p->full, 2 * (d0 + d) + 1, 1, t0 + t, 1, bs_k, threshold,
                    p->dif_pk_o, NULL, wk_s_o, wk_e_o)
        : 0;
      if(r_o < 0) return -1;

      int c = 0;
      for(size_t b = 0; b < nb; b++){
        ap_peak pke = (b < nb_e) ? p->dif_pk_e[b] : (ap_peak){-1, 0.f, 0.f, 0.f};
        ap_peak pko = (b < nb_o) ? p->dif_pk_o[b] : (ap_peak){-1, 0.f, 0.f, 0.f};

        int64_t idx_e = (pke.index >= 0) ? 2 * (int64_t)pke.index : -1;
        if(idx_e >= 0 && ((size_t)idx_e < start || (size_t)idx_e >= end)) idx_e = -1;

        int64_t idx_o = (pko.index >= 0) ? 2 * (int64_t)pko.index + 1 : -1;
        if(idx_o >= 0 && ((size_t)idx_o < start || (size_t)idx_o >= end)) idx_o = -1;

        float mag_e = (idx_e >= 0) ? ((pke.magnitude > 0.f) ? pke.magnitude : sqrtf(pke.re * pke.re + pke.im * pke.im)) : -1.0f;
        float mag_o = (idx_o >= 0) ? ((pko.magnitude > 0.f) ? pko.magnitude : sqrtf(pko.re * pko.re + pko.im * pko.im)) : -1.0f;

        ap_peak *outp = peaks + row * nb + b;
        if(idx_e >= 0 && (idx_o < 0 || mag_e >= mag_o)){
          outp->index = (long)idx_e;
          outp->re = pke.re;
          outp->im = pke.im;
          outp->magnitude = (pke.magnitude > 0.f) ? pke.magnitude : mag_e;
          c++;
        } else if(idx_o >= 0){
          outp->index = (long)idx_o;
          outp->re = pko.re;
          outp->im = pko.im;
          outp->magnitude = (pko.magnitude > 0.f) ? pko.magnitude : mag_o;
          c++;
        } else {
          outp->index = -1;
          outp->re = 0.0f;
          outp->im = 0.0f;
          outp->magnitude = 0.0f;
        }
      }
      if(counts) counts[row] = c;
      total += c;
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

int ap_hmf_run(ap_hmf_plan *p,int d0,int nd,int t0,int nt,
               size_t binsize,float threshold,
               ap_peak *peaks,int *counts,size_t start,size_t end){
  if(!p||nd<1||nt<1||!binsize) return 0;
  if(d0<0||d0+nd>p->nd||t0<0||t0+nt>p->nt) return -1;
  if(end>p->n) end=p->n;
  if(start>=end) return 0;
  const size_t n=p->n;
  const size_t nb=ap_hmf_nbins(p,binsize,start,end);
  for(int i=0;i<p->ntiers;i++)
    if(!isfinite(p->tier[i].thr) || p->tier[i].thr < 0) return -1;

  const int *fire_d=NULL,*fire_t=NULL;
  int nfire=0;
  for(int i=0;i<p->ntiers;i++){
    hmf_tier *tr=&p->tier[i];
    /* Coarse sample j maps to full lag j*R. Widen by one coarse sample
       so rounding the caller's window remains conservative. */
    const size_t R=n/tr->m;
    size_t cstart = start/R;
    size_t cend   = (end+R-1)/R; if(cend>tr->m) cend=tr->m;
    if(cstart>0) cstart--;
    const size_t cspan = cend>cstart ? cend-cstart : 1;
    const float thr=tr->thr;
    unsigned long long t_0=ap_ticks();
    if(i==0){
      /* The first tier runs on every pair of the segment in one call: the data
         spectrum is read once and stays resident across the whole template sweep. */
      if(ap_mf_run(tr->mf,d0,nd,t0,nt,cspan,thr,tr->cebuf,NULL,cstart,cend)<0) return -1;
    } else {
      /* Later tiers run only on the previous tier's survivors, pooled across blocks. */
      if(ap_mf_run_pairs_pooled(tr->mf,d0,fire_d,fire_t,nfire,t0,cspan,thr,tr->cebuf,NULL,
                                cstart,cend,nt)<0) return -1;
    }
    tr->ticks += ap_ticks()-t_0;
    int nnext=0;
    const int npairs = i==0 ? nd*nt : nfire;
    for(int j=0;j<npairs;j++){
      const int d = i==0 ? j/nt : fire_d[j];
      const int t = i==0 ? j%nt : fire_t[j];
      const size_t row=(size_t)d*nt+t;
      if(i==0) p->pairs++;
      ap_peak ce = tr->cebuf[row];
      int fire = ce.index>=0 && ce.magnitude>=thr;
      if(i==0 && fire){
        if(p->dump){ float rec[8]={ce.magnitude,0.0f,ce.magnitude,thr,thr,thr,
                                   (float)(d0+d),(float)(t0+t)};
                     fwrite(rec,sizeof rec,1,p->dump); }
        if(p->trace && p->pairs<6)
          fprintf(stderr,"    [trace] pair=%ld thr=%.3f coarse max=%.3f\n",p->pairs,thr,ce.magnitude);
      }
      if(fire){
        tr->fire_d[nnext]=d; tr->fire_t[nnext]=t; nnext++;
      } else {
        unsigned long long f0 = p->prof ? ap_ticks() : 0;
        empty_row(peaks,counts,row,nb);
        if(p->prof) p->c_fill += ap_ticks()-f0;
      }
    }
    tr->passed += nnext;
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
