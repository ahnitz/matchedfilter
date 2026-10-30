/* matchedfilter: public API over whichever kernel Highway's runtime dispatch
 * selected.  Nothing here is target-specific, so it compiles at the baseline
 * and is safe to execute before the CPU has been interrogated.
 *
 * Set MF_ISA to a Highway target name -- SSE4, AVX2, AVX3, NEON, EMU128 --
 * to narrow the choice; `matchedfilter.backend()` reports what was picked.
 */
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <math.h>
#include "matchedfilter.h"
#include "transform.h"
#include "backend.h"
#include "q15.h"

struct ap_plan { const ap_backend *be; void *h; size_t n; };

#define pick() ap_backend_active()

const char *ap_isa(void){ const ap_backend *b=pick(); return b?b->name:"unsupported"; }

int ap_supported(size_t N){
  const ap_backend *b=pick();
  return b && b->supported(N);
}

/* A sub-plan takes its parent's back end, not whatever is selected when it is built
   (lazily, possibly after set_target): a plan keeps one kernel for every call. */
static const ap_backend *be_of(const ap_plan *like){ return like ? like->be : pick(); }

static ap_plan *create_on(const ap_backend *b,size_t N){
  if(!b || !b->supported(N)) return NULL;
  void *h=b->create(N);
  if(!h) return NULL;
  ap_plan *p=malloc(sizeof(*p));
  if(!p){ b->destroy(h); return NULL; }
  p->be=b; p->h=h; p->n=N;
  return p;
}

ap_plan *ap_create(size_t N){ return create_on(pick(),N); }
ap_plan *ap_create_like(const ap_plan *like,size_t N){ return create_on(be_of(like),N); }

const char *ap_plan_backend(const ap_plan *p){ return p?p->be->name:"none"; }

static ap_plan *create_pairbatch_on(const ap_backend *b,size_t N){
  if(!b || N<64 || N>2048 || !b->supported(N) || !b->create_pairbatch) return NULL;
  void *h=b->create_pairbatch(N);
  if(!h) return NULL;
  ap_plan *p=malloc(sizeof(*p));
  if(!p){ b->destroy(h); return NULL; }
  p->be=b; p->h=h; p->n=N;
  return p;
}

ap_plan *ap_create_pairbatch(size_t N){ return create_pairbatch_on(pick(),N); }
ap_plan *ap_create_pairbatch_like(const ap_plan *like,size_t N){
  return create_pairbatch_on(be_of(like),N);
}

void ap_destroy(ap_plan *p){
  if(!p) return;
  p->be->destroy(p->h);
  free(p);
}

void ap_fft(ap_plan *p,const float *in,float *out,int sign){
  p->be->fft(p->h,in,out,sign==AP_BACKWARD);
}

void ap_td_corr(const float *x,const float *taps,int L,int nlag,float *out){
  pick()->td_corr(x,taps,L,nlag,out);
}
void ap_td_corr_on(const ap_plan *p,const float *x,const float *taps,int L,int nlag,float *out){
  be_of(p)->td_corr(x,taps,L,nlag,out);
}

void ap_split_store_on(const ap_plan *p,const float *x,float *re,float *im,size_t n,int conj,
                       int n1,int n2,int w){
  be_of(p)->split_store(x,re,im,n,conj,n1,n2,w);
}
void ap_scale_load_on(const ap_plan *p,float *dst,const float *src,size_t have,size_t n,
                      size_t stride,float scale){
  be_of(p)->scale_load(dst,src,have,n,stride,scale);
}
void ap_lanes_transpose_on(const ap_plan *p,float *dst,const float *const *src,int cnt,size_t n,
                           int w){
  be_of(p)->lanes_transpose(dst,src,cnt,n,w);
}
void ap_real_split_on(const ap_plan *p,const float *Z,const float *tw,size_t n,float *X){
  be_of(p)->real_split(Z,tw,n,X);
}

void ap_root_merge_on(const ap_plan *p,const float *D,const float *T,size_t k0,size_t k1,
                      float scale,const float *tw,size_t n,float *Z){
  be_of(p)->root_merge(D,T,k0,k1,scale,tw,n,Z);
}

/* split-input binned max, for callers that already hold re/im apart */
int ap_binmax_split(ap_plan *p,const float *re,const float *im,
                    size_t binsize,float threshold,ap_peak *peaks,int *count,
                    int sign,size_t start,size_t end,const unsigned *ph){
  if(!p||!binsize) return -1;
  if(end>p->n) end=p->n;
  if(start>=end) return 0;
  if(!p->be->binmax_split) return -1;
  const size_t nb=ap_bin_count(binsize,start,end,ph?ph[0]:0u);
  if(p->be->binmax_split(p->h,re,im,binsize,threshold,peaks,sign==AP_BACKWARD,start,end,ph)<0)
    return -1;
  int c=0; for(size_t j=0;j<nb;j++) if(peaks[j].index>=0) c++;
  if(count) *count=c;
  return c;
}

/* matched-filter product fused into the transform's load; -1 if unavailable */
int ap_plan_split(const ap_plan *p,int *n1,int *n2){
  if(!p||!p->be->split) return 0;
  return p->be->split(p->h,n1,n2);
}

int ap_has_fused_prod(const ap_plan *p){
  if(!p||!p->be->has_prod||!p->be->binmax_prod) return 0;
  return p->be->has_prod(p->h);
}

int ap_plan_pairbatch(const ap_plan *p){
  if(!p||!p->be->pairbatch||!p->be->binmax_prod_batch) return 0;
  return p->be->pairbatch(p->h);
}

int ap_plan_broadcast_data(const ap_plan *p){
  return p && p->be->broadcast_data && p->be->broadcast_data(p->h);
}

int ap_binmax_prod_batch_peaks(ap_plan *p,const float *dr,const float *di,
                         const float *tr,const float *ti,int nlane,
                         size_t binsize,float threshold,ap_peak *peaks,
                         int sign,size_t start,size_t end,const unsigned *ph){
  if(!p||!binsize||nlane<1) return -1;
  if(end>p->n) end=p->n;
  if(start>=end) return 0;
  if(!p->be->binmax_prod_batch) return -1;
  /* The bank counts while scattering these peaks; do not scan them twice. */
  return p->be->binmax_prod_batch(p->h,dr,di,tr,ti,nlane,binsize,threshold,
                                 peaks,sign==AP_BACKWARD,start,end,ph);
}

int ap_binmax_prod_batch_lanes_peaks(ap_plan *p,const float *dr,const float *di,
                                     const float *tr,const float *ti,int nlane,
                                     size_t binsize,float threshold,ap_peak *peaks,
                                     int sign,size_t start,size_t end,const unsigned *ph){
  if(!p||!binsize||nlane<1) return -1;
  if(end>p->n) end=p->n;
  if(start>=end) return 0;
  if(!p->be->binmax_prod_batch_lanes) return -1;
  return p->be->binmax_prod_batch_lanes(p->h,dr,di,tr,ti,nlane,binsize,threshold,
                                       peaks,sign==AP_BACKWARD,start,end,ph);
}

ap_prod_kernel ap_plan_prod_kernel(const ap_plan *p,float threshold){
  ap_prod_kernel k={NULL,NULL};
  if(p){
    k.context=p->h;
    k.run=threshold>0.f && p->be->binmax_prod_threshold
        ? p->be->binmax_prod_threshold : p->be->binmax_prod;
  }
  return k;
}

int ap_corr_prod(ap_plan *p,const float *dr,const float *di,
                 const float *tr,const float *ti,float *out){
  if(!p||!p->be->corr_prod) return -1;
  return p->be->corr_prod(p->h,dr,di,tr,ti,out);
}
int ap_corr_split(ap_plan *p,const float *re,const float *im,float *out){
  if(!p||!p->be->corr_split) return -1;
  return p->be->corr_split(p->h,re,im,out);
}
int ap_corr_prod_batch(ap_plan *p,const float *dr,const float *di,
                       const float *tr,const float *ti,int nlane,float *out){
  if(!p||!p->be->corr_prod_batch) return -1;
  return p->be->corr_prod_batch(p->h,dr,di,tr,ti,nlane,out);
}

int ap_binmax(ap_plan *p,const float *in,size_t dist,int B,
              size_t binsize,float threshold,ap_peak *peaks,int *counts,
              int sign,size_t start,size_t end,const unsigned *ph){
  if(B<1||!binsize) return 0;
  if(end>p->n) end=p->n;
  if(start>=end) return 0;
  if(!p->be->binmax) return -1;
  const size_t nb=ap_bin_count(binsize,start,end,ph?ph[0]:0u);
  const int conj = sign==AP_BACKWARD;
  int total=0;
  for(int b=0;b<B;b++){
    ap_peak *o=peaks+(size_t)b*nb;
    if(ap_bin_count(binsize,start,end,ph?ph[b]:0u)!=nb) return -1;   /* one stride */
    if(p->be->binmax(p->h,in+2*(size_t)b*dist,binsize,threshold,o,conj,start,end,
                     ph?ph+b:NULL)<0)
      return -1;
    int c=0;
    for(size_t j=0;j<nb;j++) if(o[j].index>=0) c++;
    if(counts) counts[b]=c;
    total+=c;
  }
  return total;
}


/* SIMD lane width of the active back end, so callers that want to store data
   in the layout stage A walks can compute it.  0 if unsupported.

   This used to be a chain of pointer comparisons against the named back ends,
   and got it wrong once: written as "bal8 ? 8 : 16" it told the portable back
   end it had 16 lanes, the matched filter stored every spectrum group-major
   for the wrong width, the transforms still agreed, and only the correlation
   came out wrong. */
int ap_lane_width(void){
  const ap_backend *b=pick();
  return b?b->lanes:0;
}
int ap_plan_lanes(const ap_plan *p){
  const ap_backend *b=be_of(p);
  return b?b->lanes:0;
}

int ap_q15_lanes(const ap_plan *p){
  const ap_backend *b=p ? p->be : NULL;
  return (b && b->q15_lanes && b->q15_screen) ? b->q15_lanes() : 0;
}

int ap_q15_screen(const ap_plan *p, const int16_t *dq, const int16_t *tr, const int16_t *ti,
                  size_t start, size_t end, const int16_t *lanethr, uint64_t *bits,
                  int16_t *lanemax, void *scratch){
  const ap_backend *b=p ? p->be : NULL;
  if(!b || !b->q15_screen || !dq || !tr || !ti || !lanethr || !bits || !scratch) return -1;
  return b->q15_screen(p->n,dq,tr,ti,start,end,lanethr,bits,lanemax,scratch);
}

int ap_q15_screen_perm(const ap_plan *p, const int16_t *dr, const int16_t *di,
                       const int16_t *tr, const int16_t *ti, long tw, const int16_t *dsel,
                       const int16_t *tsel, size_t start, size_t end, const int16_t *lanethr,
                       uint64_t *bits, int16_t *lanemax, void *scratch){
  const ap_backend *b=p ? p->be : NULL;
  if(!b || !b->q15_screen_perm || !dr || !di || !tr || !ti || !dsel || !tsel || !lanethr ||
     !bits || !scratch) return -1;
  return b->q15_screen_perm(p->n,dr,di,tr,ti,tw,dsel,tsel,start,end,lanethr,bits,lanemax,scratch);
}

int ap_q15_slab8(const ap_plan *p, const float *const *rr, const float *const *ri,
                 const float *sc, int16_t *xr, int16_t *xi){
  const ap_backend *b=p ? p->be : NULL;
  if(!b || !b->q15_slab8 || !rr || !ri || !sc || !xr || !xi) return -1;
  b->q15_slab8(p->n,rr,ri,sc,xr,xi);
  return 0;
}

int ap_q15_has_tile(const ap_plan *p){
  int M1, M2;
  return p && p->be && p->be->q15_screen_tile && !ap_q15_factor(p->n, &M1, &M2);
}

int ap_q15_screen_tile(const ap_plan *p, int T, const int16_t *dq,
                       const int16_t *tr, const int16_t *ti, size_t start, size_t end,
                       const int16_t *lanethr, uint64_t *bits, int16_t *lanemax, void *scratch){
  const ap_backend *b=p ? p->be : NULL;
  if(!b || !b->q15_screen_tile || (T!=4 && T!=8 && T!=16) ||
     !dq || !tr || !ti || !lanethr || !bits || !scratch) return -1;
  return b->q15_screen_tile(p->n,T,dq,tr,ti,start,end,lanethr,bits,lanemax,scratch);
}
