/* matchedfilter: batched matched filter.
 *
 * D data segments x T templates, reporting the binned maximum of each pair's
 * correlation.  See docs/design.md for where the time goes and which
 * reuse opportunities are real.
 *
 * Segments arrive already transformed.  Ingest only rearranges - conjugate the
 * templates, and store both sides group-major so every pair transform reads
 * sequentially - which keeps the D*T loop free of anything single-sided.
 */
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <limits.h>
#include "alloc.h"
#include "env.h"
#include "matchedfilter.h"
#include "transform.h"
#include "q15.h"

/* Unfused product, for a plan whose geometry the fused stage-A loader cannot take
   (p->gmajor 0: see where it is set). It had hand-written AVX-512 and AVX2 variants;
   the compiler vectorises this loop. The MF_GMAJOR switch that also forced it was
   removed on 2026-10-22: the fused path won at every length on Zen 3, Zen 5 and the M2. */
static void mulspec(const float *ar,const float *ai,const float *br,const float *bi,
                    float *or_,float *oi,size_t n){
  for(size_t k=0;k<n;k++){
    float x=ar[k],y=ai[k],u=br[k],v=bi[k];
    or_[k]=x*u-y*v; oi[k]=-(x*v+y*u);
  }
}

struct ap_mf_plan {
  size_t n;
  int nd, nt;
  /* Each data row's bin phase during an ap_mf_run_series call ([nd], the call's bin_phase
     for the blocks in the rows), NULL otherwise: the scans number row d's bins from
     start - bph[d] (backend.h, binmax). */
  const unsigned *bph;
  int tile;            /* pair-loop tile; read once, not per run */
  ap_plan *fft;        /* shared transform plan: forward at ingest, backward per pair */
  int n1,n2,w;         /* the transform's split and lane count, for group-major storage */
  int gmajor;          /* 0 when the back end cannot take group-major input     */
  /* Spectra are stored SPLIT (re and im in separate arrays), which is what the
     transform wants.  Preprocessing is free here - every segment is ingested once
     and used D or T times - so it is done in the layout the hot loop prefers, and
     the product becomes four FMAs with no permutes and no deinterleave. */
  float *dre,*dim;     /* [nd][n] */
  float *tre,*tim;     /* [nt][n], already conjugated */
  float *pr,*pi;       /* scratch for one product, split */
  float *scratch;      /* interleaved staging for ingest */
  /* run_series staging, allocated on first use so a plan that never
     filters a series does not carry 4n floats it will not touch.
     ONE buffer pair serves a whole group: ap_mf_set_data split_stores
     immediately rather than retaining the pointer, which is what lets
     the flat path skip the per-slot spectrum array the hierarchical
     one needs. */
  float *sfwd,*sspec;         /* [2n] each */
  /* Real series (ap_mf_correlate_series_continuous_real): blocks of real samples transformed
     at half size and split into their full spectrum (ap_real_split_on). */
  int real_series;
  ap_plan *half_fft;
  ap_plan *fwd_cplx_batch, *fwd_real_batch;
  float *bspec;               /* [w][2n] batched forward spectra */
  float *rtw;                 /* [2(n/2+1)] cos, sin of 2 pi k/n */
  /* Pair-batched small-N path.  Below AP_W^2 the transform has no balanced
     split, so the back end puts AP_W independent PAIRS in a vector instead of
     AP_W frequencies of one transform -- see create_small() in
     balanced-inl.h.  What that costs here is a different template bank
     layout, and it has to be decided before ingest. */
  int pb;                     /* lanes per batch, 0 when not this path */
  int ntpad;                  /* template rows, rounded up to a multiple of pb */
  float *ebr,*ebi;            /* fallback lane-expanded data */
  float *tsr,*tsi;            /* [n][pb] gathered template group, when needed  */
  float *dsr,*dsi;            /* [n][pb] gathered data group, for pooled pairs */
  float *tmre,*tmim;          /* [ntpad][n] template-major copy for stride-1 survivor gathers */
  float *corrbuf;             /* [pb][n] full-output staging for pair batches */
  ap_accel *accel;            /* platform FFT for the continuous correlation (fft_accel.c) */
  int use_accel;              /* ap_mf_set_platform_fft: a cost-model candidate */
  float *anr,*ani;            /* [nt][n] natural-order conjugated templates for it */
  unsigned char *aready;      /* which rows of anr/ani are current */
  ap_peak *pkbuf;             /* [pb][nb] dense results, before placement      */
  size_t pkcap;
  /* Optional second layout, created only when an actual call can use it.
     The balanced plan remains available for small sub-ranges and selections. */
  struct ap_mf_plan *pair_alt;
  unsigned char *alt_dready, *alt_tready;
  int allow_pair_alt;
  /* DIF series filtering fields */
  float *twiddles;
  float *sspec_tw;
  ap_peak *dif_pkbuf;
  size_t dif_pkcap;
  ap_plan *fft_fwd;
  float *sfwd_2n, *sspec_2n;
  ap_plan *fft_fwd_n;
  float *sfwd_n, *sspec_n;
  /* Q15 coarse screen (ap_mf_q15_screen): int16 copies of the inputs, made on
     first use and invalidated by the setters. */
  int qw;                     /* int16 lanes per screen call; 0 until first use */
  int qtail;                  /* retained backend has tail tiles at this n */
  int qfull;                  /* tile full template groups across 2 blocks to fit L1D */
  int qnomargin;              /* decide on the int16 maximum itself (ap_mf_set_q15_margin) */
  int16_t *qtr,*qti;          /* [group][n][qw] quantised templates, conjugated */
  float *qts;                 /* [nt] template scale: t_q = t * qts */
  unsigned char *qtok;        /* [nt] quantised copy current */
  int16_t *qd;                /* [nd][n][3] quantised data, (dr, di, -di) */
  float *qds;                 /* [nd] data scale */
  unsigned char *qdok;        /* [nd] */
  void *qscr;                 /* kernel scratch */
  int16_t *qdx;               /* [slab][2][n][qw] quantised data across each slab of qw blocks */
  unsigned char *qdxok;       /* [nd] block's slab copy is current */
  int *qord; int qordcap;     /* listed pairs' bucket order and keys (ap_mf_q15_pairs) */
  float *qzero;               /* [n] zeros: a slab lane past the plan's blocks */
  int16_t *qdm, *qtm;         /* [nd][2*n+32], [nt][2*n+32] contiguous padded rows for gather */
  unsigned char *qdmok, *qtmok;
};

/* Set the rows' bin phases for the calls that follow ([nd], or NULL): for a plan another
   one drives (the hierarchical refine's full plan), which owns the array meanwhile. */
void ap_mf_set_bin_phase(ap_mf_plan *p, const unsigned *bph){ if(p) p->bph = bph; }

/* Row d's bin phase, and the forms the scans take: one value, or a lane array of it for a
   pair batch whose lanes are templates over that one row. */
static inline unsigned row_phase(const ap_mf_plan *p, int d){ return p->bph ? p->bph[d] : 0u; }
static inline const unsigned *one_phase(const ap_mf_plan *p, int d){
  return p->bph ? p->bph + d : NULL;
}
static inline const unsigned *lane_phases(const ap_mf_plan *p, int d, unsigned *buf){
  if(!p->bph) return NULL;
  for(int l=0;l<AP_MAX_LANES;l++) buf[l]=p->bph[d];
  return buf;
}

/* Two scratch buffers of `bytes` each, allocated together: both or neither. A guard on the
   first alone took a half-allocated pair as ready after one failed allocation, and the next
   call dereferenced the missing one. */
static int alloc_pair(float **a,float **b,size_t bytes){
  if(*a && *b) return 0;
  free(*a); free(*b);
  *a=ap_alloc64(bytes); *b=ap_alloc64(bytes);
  if(*a && *b) return 0;
  free(*a); free(*b); *a=*b=NULL;
  return -1;
}

/* like: the plan whose back end a sub-plan uses (NULL: the active target). */
static ap_mf_plan *create_mf(size_t n, int ndata, int ntmpl, int pair, const ap_plan *like){
  if(ndata<1||ntmpl<1||(size_t)ndata>(size_t)INT_MAX/(size_t)ntmpl) return NULL;
  ap_mf_plan *p = calloc(1,sizeof(*p));
  if(!p) return NULL;
  p->n=n; p->nd=ndata; p->nt=ntmpl;
  p->fft = pair ? ap_create_pairbatch_like(like,n) : ap_create_like(like,n);
  if(!p->fft){ free(p); return NULL; }
  /* Ask the plan for its split rather than recomputing it.  Deriving it
     independently means the two disagree the moment the heuristic changes, and
     group-major storage is only correct if they agree - forcing a different
     split through MF_N1 used to produce silently wrong answers. */
  { p->n1=p->n2=0;
    if(!ap_plan_split(p->fft,&p->n1,&p->n2)){ p->n1=p->n2=0; }
    p->w = ap_plan_lanes(p->fft);
    /* Group-major storage is only correct if the fused loader consumes it, so
        ask the plan rather than assuming.  The AVX-512 1024 kernel has no fused
        variant, but AVX2 at 1024 runs on the generic back end, which does - and
        hard-coding n!=1024 silently cost the AVX2 path its fused product. */
    p->gmajor = (p->w>0 && p->n1>0 && p->n1%p->w==0
                 && (size_t)p->n1*p->n2==n && ap_has_fused_prod(p->fft)) ? 1 : 0;
  }
  /* Read once here, not inside ap_mf_run.  The hierarchical filter calls
     ap_mf_run once per pair rather than once per batch, which turned a
     per-batch getenv into a per-pair one. */
  p->tile = 8;
  p->pb = ap_plan_pairbatch(p->fft);
  const int broadcast_data = ap_plan_broadcast_data(p->fft);
  /* The pair-batched alternate (run_pairs), where it was measured: every x86 target, up to
     n = 1024 at 16 lanes and 512 at 8 or 4. Zen 5, 8 x 64 pairs, one bin, alternate/base:
     16 lanes (AVX3) 0.35 0.58 0.74 at n = 256 512 1024; 8 lanes 0.62 0.74 (AVX2), 0.73 0.81
     (AVX); 4 lanes (SSE4) 0.84 0.93. Past the cap it lost or tied in places (AVX 1.08 at 1024,
     SSE4 1.01) and won in others (AVX3 0.72 at 2048), which a rule cannot follow: a measured
     choice per size would. NEON is unmeasured, so it keeps the base path. MF_PBMAX remains a
     way to force either implementation in one build, without changing process state here. */
#if defined(__x86_64__) || defined(_M_X64) || defined(__i386__)
  const size_t alt_max_n = ap_plan_lanes(p->fft) >= 16 ? 1024u : 512u;
  p->allow_pair_alt = !pair && !p->pb && n>=256 && n<=alt_max_n && p->w>0 && ntmpl>=(size_t)p->w
    && ap_env_int("MF_PBMAX",-1) < 0;
#else
  p->allow_pair_alt = 0;
#endif
  p->ntpad = p->pb ? ((ntmpl + p->pb - 1)/p->pb)*p->pb : ntmpl;
  p->dre=ap_alloc64((size_t)ndata*n*sizeof(float));
  p->dim=ap_alloc64((size_t)ndata*n*sizeof(float));
  p->tre=ap_alloc64((size_t)p->ntpad*n*sizeof(float));
  p->tim=ap_alloc64((size_t)p->ntpad*n*sizeof(float));
  p->pr =ap_alloc64(n*sizeof(float));
  p->pi =ap_alloc64(n*sizeof(float));
  p->scratch=ap_alloc64(2*n*sizeof(float));
  if(!p->dre||!p->dim||!p->tre||!p->tim||!p->pr||!p->pi||!p->scratch){
    ap_mf_destroy(p); return NULL; }
  if(p->pb){
    if(!broadcast_data){
      p->ebr=ap_alloc64((size_t)n*p->pb*sizeof(float));
      p->ebi=ap_alloc64((size_t)n*p->pb*sizeof(float));
      if(!p->ebr||!p->ebi){ ap_mf_destroy(p); return NULL; }
    }
    /* The padding rows are transformed like any other lane and their results
       discarded, so they must be finite -- zero, not whatever malloc left. */
    memset(p->tre,0,(size_t)p->ntpad*n*sizeof(float));
    memset(p->tim,0,(size_t)p->ntpad*n*sizeof(float));
    p->tsr=ap_alloc64((size_t)n*p->pb*sizeof(float));
    p->tsi=ap_alloc64((size_t)n*p->pb*sizeof(float));
    p->dsr=ap_alloc64((size_t)n*p->pb*sizeof(float));
    p->dsi=ap_alloc64((size_t)n*p->pb*sizeof(float));
    if(!p->tsr||!p->tsi||!p->dsr||!p->dsi){ ap_mf_destroy(p); return NULL; }
    p->tmre=ap_alloc64((size_t)p->ntpad*n*sizeof(float));
    p->tmim=ap_alloc64((size_t)p->ntpad*n*sizeof(float));
    if(!p->tmre||!p->tmim){ ap_mf_destroy(p); return NULL; }
    memset(p->tmre,0,(size_t)p->ntpad*n*sizeof(float));
    memset(p->tmim,0,(size_t)p->ntpad*n*sizeof(float));
  }
  return p;
}

ap_mf_plan *ap_mf_create(size_t n, int ndata, int ntmpl){
  return create_mf(n,ndata,ntmpl,0,NULL);
}

ap_mf_plan *ap_mf_create_pairbatch(size_t n, int ndata, int ntmpl){
  return create_mf(n,ndata,ntmpl,1,NULL);
}

void ap_mf_destroy(ap_mf_plan *p){
  if(!p) return;
  if(p->fft) ap_destroy(p->fft);
  ap_mf_destroy(p->pair_alt);
  free(p->alt_dready); free(p->alt_tready);
  free(p->dre);free(p->dim);free(p->tre);free(p->tim);
  free(p->pr);free(p->pi);free(p->scratch);
  free(p->sfwd);free(p->sspec);
  if(p->half_fft) ap_destroy(p->half_fft);
  if(p->fwd_cplx_batch) ap_destroy(p->fwd_cplx_batch);
  if(p->fwd_real_batch) ap_destroy(p->fwd_real_batch);
  free(p->bspec);
  free(p->rtw);
  free(p->ebr);free(p->ebi);free(p->tsr);free(p->tsi);free(p->dsr);free(p->dsi);free(p->pkbuf);
  free(p->tmre);free(p->tmim);
  ap_accel_destroy(p->accel);
  free(p->anr); free(p->ani); free(p->aready);
  free(p->corrbuf);
  if(p->fft_fwd) ap_destroy(p->fft_fwd);
  if(p->fft_fwd_n) ap_destroy(p->fft_fwd_n);
  free(p->twiddles);free(p->sspec_tw);free(p->dif_pkbuf);
  free(p->sfwd_2n);free(p->sspec_2n);
  free(p->sfwd_n);free(p->sspec_n);
  free(p->qtr);free(p->qti);free(p->qts);free(p->qtok);
  free(p->qd);free(p->qds);free(p->qdok);free(p->qscr);free(p->qdx);free(p->qdxok);free(p->qord);free(p->qzero);
  free(p->qdm);free(p->qtm);free(p->qdmok);free(p->qtmok);
  free(p);
}

size_t ap_mf_nbins(const ap_mf_plan *p, size_t binsize, size_t start, size_t end){
  if(!p||!binsize) return 0;
  if(end>p->n) end=p->n;
  if(start>=end) return 0;
  return (end-start+binsize-1)/binsize;
}

/* The same with the bins numbered from start - ph (ap_bin_count). */
static size_t ap_mf_nbins_phased(const ap_mf_plan *p, size_t binsize, size_t start,
                                 size_t end, unsigned ph){
  if(!p||!binsize) return 0;
  if(end>p->n) end=p->n;
  return ap_bin_count(binsize,start,end,ph);
}

/* Store a spectrum split AND group-major: [n1 block][n2][lane], n1 = g*W + l,
   from the natural x[n2*N1 + n1].  This is a transpose, paid once per segment at
   ingest, so that every one of the D*T pair transforms reads sequentially.  It is
   the whole reason preprocessing being free matters. The copy is the backend's
   (ap_split_store_on), vectorised at the plan's own width. */

int ap_mf_set_data(ap_mf_plan *p, int d, const float *spec){
  if(!p||d<0||d>=p->nd) return -1;
  if(p->qdok) p->qdok[d]=0;
  if(p->qdxok) p->qdxok[d]=0;
  if(p->qdmok) p->qdmok[d]=0;
  ap_split_store_on(p->fft, spec, p->dre+(size_t)d*p->n, p->dim+(size_t)d*p->n, p->n, 0,
                    p->gmajor?p->n1:0, p->n2, p->w);
  if(p->pair_alt){
    ap_mf_set_data(p->pair_alt,d,spec);
    p->alt_dready[d]=1;
  }
  return 0;
}

int ap_mf_set_platform_fft(ap_mf_plan *p, int on){
  if(!p) return -1;
  if(!on){ p->use_accel=0; return 0; }
  /* Row-major templates are needed: the group-major layout without its copy is refused. */
  if(p->pb && !p->tmre) return -1;
  if(!p->accel) p->accel=ap_accel_create(p->n);
  if(!p->accel) return -1;
  if(!p->pb && !(p->anr && p->ani && p->aready)){
    free(p->aready); p->aready=NULL;
    if(alloc_pair(&p->anr,&p->ani,(size_t)p->nt*p->n*sizeof(float))) return -1;
    p->aready=calloc((size_t)p->nt,1);
    if(!p->aready){ free(p->anr); free(p->ani); p->anr=p->ani=NULL; return -1; }
  }
  p->use_accel=1;
  return 0;
}

/* Template t in natural order (conjugated, as stored): the pair-batch plans keep one
   (tmre); the others' rows are in the element order, undone once per template here. */
static void accel_template(ap_mf_plan *p,int t,const float **tr,const float **ti){
  const size_t n=p->n;
  if(p->tmre){ *tr=p->tmre+(size_t)t*n; *ti=p->tmim+(size_t)t*n; return; }
  float *nr=p->anr+(size_t)t*n, *ni=p->ani+(size_t)t*n;
  if(!p->aready[t]){
    const float *re=p->tre+(size_t)t*n, *im=p->tim+(size_t)t*n;
    for(size_t k=0;k<n;k++){
      size_t j=k;
      if(p->gmajor){
        size_t a=k%(size_t)p->n1, b=k/(size_t)p->n1;
        j=(a/p->w)*p->n2*p->w+b*p->w+a%p->w;
      }
      nr[k]=re[j]; ni[k]=im[j];
    }
    p->aready[t]=1;
  }
  *tr=nr; *ti=ni;
}

int ap_mf_set_template(ap_mf_plan *p, int t, const float *spec){
  if(!p||t<0||t>=p->nt) return -1;
  if(p->aready) p->aready[t]=0;
  if(p->qtok) p->qtok[t]=0;
  if(p->qtmok) p->qtmok[t]=0;
  if(p->pb){
    /* Bank stored [group][element][lane], lane = t % pb.  The pair kernel
       reads a whole group as one contiguous [element][lane] run, so the
       transposition is paid once per template here rather than per pair --
       the same trade that makes group-major storage worth it on the
       balanced path. */
    const size_t n=p->n; const int W=p->pb;
    const size_t base=(size_t)(t/W)*n*W + (size_t)(t%W);
    float *re=p->tre+base, *im=p->tim+base;
    float *mre=p->tmre ? p->tmre+(size_t)t*n : NULL;
    float *mim=p->tmim ? p->tmim+(size_t)t*n : NULL;
    for(size_t k=0;k<n;k++){
      const float r=spec[2*k];
      const float i=-spec[2*k+1];          /* conjugated at ingest, as below */
      re[k*W]=r;
      im[k*W]=i;
      if(mre){ mre[k]=r; mim[k]=i; }
    }
    return 0;
  }
  /* conjugate at ingest, not per pair: this runs T times, the pair loop D*T */
  ap_split_store_on(p->fft, spec, p->tre+(size_t)t*p->n, p->tim+(size_t)t*p->n, p->n, 1,
                    p->gmajor?p->n1:0, p->n2, p->w);
  if(p->pair_alt){
    ap_mf_set_template(p->pair_alt,t,spec);
    p->alt_tready[t]=1;
  }
  return 0;
}

/* Undo the primary layout once when a row first reaches the alternate plan.
   Subsequent setters populate both layouts directly, outside the pair loop. */
static void restore_spectrum(ap_mf_plan *p,const float *re,const float *im,int conj){
  for(size_t k=0;k<p->n;k++){
    size_t j=k;
    if(p->gmajor){
      size_t a=k%(size_t)p->n1, b=k/(size_t)p->n1;
      j=(a/p->w)*p->n2*p->w+b*p->w+a%p->w;
    }
    p->scratch[2*k]=re[j];
    p->scratch[2*k+1]=conj ? -im[j] : im[j];
  }
}

static ap_mf_plan *pair_alternate(ap_mf_plan *p,int d0,int nd,int t0,int nt){
  if(!p->pair_alt){
    ap_mf_plan *q=create_mf(p->n,p->nd,p->nt,1,p->fft);  /* on the plan's own kernel */
    unsigned char *dr=calloc((size_t)p->nd,1), *tr=calloc((size_t)p->nt,1);
    if(!q || !dr || !tr){ ap_mf_destroy(q); free(dr); free(tr); return NULL; }
    p->pair_alt=q; p->alt_dready=dr; p->alt_tready=tr;
  }
  for(int d=d0;d<d0+nd;d++) if(!p->alt_dready[d]){
    restore_spectrum(p,p->dre+(size_t)d*p->n,p->dim+(size_t)d*p->n,0);
    ap_mf_set_data(p->pair_alt,d,p->scratch); p->alt_dready[d]=1;
  }
  for(int t=t0;t<t0+nt;t++) if(!p->alt_tready[t]){
    restore_spectrum(p,p->tre+(size_t)t*p->n,p->tim+(size_t)t*p->n,1);
    ap_mf_set_template(p->pair_alt,t,p->scratch); p->alt_tready[t]=1;
  }
  return p->pair_alt;
}


/* ---- interpolated coarse maximum -------------------------------------
 *
 * The coarse pass samples the correlation on a stride-R lag grid.  The peak
 * between samples is what the second (odd) transform exists to find, and that
 * costs as much as the first.  Interpolating instead cannot replace it -- the
 * kernel for a critically sampled band needs length -- but it BRACKETS it:
 * a statistic S with measured bounds lo <= S/true <= hi settles every pair
 * whose bracket does not straddle the coarse threshold, and only the rest pay the
 * transform.  See docs/hierarchical.md.
 *
 * Candidates are the largest few even samples.  Measured on captured searches,
 * the rank of the true peak's best even neighbour is 0 at the median and 26 at
 * worst, so a handful suffices; an earlier attempt stopped at 16 and wrongly
 * concluded the route was closed.
 */


/* The pair loop.  `tsel` selects which templates to run: NULL means the
   contiguous range [0,nt), and otherwise tsel[0..nsel) holds local indices into
   that range.  A scattered selection is what the hierarchical filter's second
   stage has - the templates that fired are wherever they fell - and running
   them one call at a time costs 4.65 us/pair against 2.76 us in a batch,
   because every call re-reads the data spectrum for a single template.

   Output rows are indexed by the LOCAL template index either way, so a
   selected run writes into the same layout a full run would, leaving the rows
   it skipped untouched. */
/* The pair loop for the small sizes.
 *
 * Lanes are PAIRS here, so the loop nest inverts: a group of pb templates is
 * one call, and the tiling that exists to keep spectra resident is pointless
 * at lengths where the whole bank fits L1.  The data spectrum is the same in
 * every lane, so it is broadcast into [element][lane] once per segment and
 * reused across every template group -- the one expansion this path pays, and
 * it amortises over pb pairs.
 *
 * Results come back dense [lane][nbins] and are placed by the caller's row
 * index, because a scattered template selection has no single stride. */
static inline void gather_template_batch(float * restrict tsr, float * restrict tsi,
                                         const ap_mf_plan *p,
                                         int t0, const int *tsel, int tt, int cnt){
  const size_t n = p->n;
  const int W = p->pb;
  const float *srp[32];
  const float *sip[32];
  const int stride1 = (p->tmre != NULL);

  for(int l=0; l<cnt; l++){
    const int t = t0 + (tsel ? tsel[tt+l] : (tt+l));
    if(stride1){
      srp[l] = p->tmre + (size_t)t * n;
      sip[l] = p->tmim + (size_t)t * n;
    } else {
      srp[l] = p->tre + (size_t)(t/W)*n*W + (size_t)(t%W);
      sip[l] = p->tim + (size_t)(t/W)*n*W + (size_t)(t%W);
    }
  }

  if(stride1){
    ap_lanes_transpose_on(p->fft, tsr, srp, cnt, n, W);
    ap_lanes_transpose_on(p->fft, tsi, sip, cnt, n, W);
  } else {
    if(cnt == W){
      if(W == 8){
        for(size_t k=0; k<n; k++){
          float * restrict dr = tsr + k * 8;
          float * restrict di = tsi + k * 8;
          const size_t kw = k * 8;
          dr[0] = srp[0][kw]; di[0] = sip[0][kw];
          dr[1] = srp[1][kw]; di[1] = sip[1][kw];
          dr[2] = srp[2][kw]; di[2] = sip[2][kw];
          dr[3] = srp[3][kw]; di[3] = sip[3][kw];
          dr[4] = srp[4][kw]; di[4] = sip[4][kw];
          dr[5] = srp[5][kw]; di[5] = sip[5][kw];
          dr[6] = srp[6][kw]; di[6] = sip[6][kw];
          dr[7] = srp[7][kw]; di[7] = sip[7][kw];
        }
      } else if(W == 16){
        for(size_t k=0; k<n; k++){
          float * restrict dr = tsr + k * 16;
          float * restrict di = tsi + k * 16;
          const size_t kw = k * 16;
          for(int l=0; l<16; l++){
            dr[l] = srp[l][kw];
            di[l] = sip[l][kw];
          }
        }
      } else {
        for(size_t k=0; k<n; k++){
          float * restrict dr = tsr + k * W;
          float * restrict di = tsi + k * W;
          const size_t kw = k * W;
          for(int l=0; l<W; l++){
            dr[l] = srp[l][kw];
            di[l] = sip[l][kw];
          }
        }
      }
    } else {
      for(size_t k=0; k<n; k++){
        float * restrict dr = tsr + k * W;
        float * restrict di = tsi + k * W;
        const size_t kw = k * W;
        for(int l=0; l<cnt; l++){
          dr[l] = srp[l][kw];
          di[l] = sip[l][kw];
        }
        for(int l=cnt; l<W; l++){
          dr[l] = 0.0f;
          di[l] = 0.0f;
        }
      }
    }
  }
}

static inline void gather_data_batch(float * restrict dsr, float * restrict dsi,
                                     const ap_mf_plan *p,
                                     int d0, const int *dsel, int tt, int cnt){
  const size_t n = p->n;
  const int W = p->pb;
  const float *drp[32];
  const float *dip[32];

  for(int l=0; l<cnt; l++){
    const int d = d0 + dsel[tt+l];
    drp[l] = p->dre + (size_t)d * n;
    dip[l] = p->dim + (size_t)d * n;
  }

  ap_lanes_transpose_on(p->fft, dsr, drp, cnt, n, W);
  ap_lanes_transpose_on(p->fft, dsi, dip, cnt, n, W);
}

int ap_binmax_prod_gather_lanes_peaks(ap_plan *p, const float *const *drp, const float *const *dip,
                                      const float *const *trp, const float *const *tip, int nlane,
                                      size_t binsize, float threshold, ap_peak *peaks,
                                      int sign, size_t start, size_t end, const unsigned *ph);

static int run_pairs_pb(ap_mf_plan *p, int d0, int nd, int t0, int nt,
                        size_t binsize, float threshold,
                        ap_peak *peaks, int *counts, size_t start, size_t end){
  const size_t n=p->n, nb=ap_bin_count(binsize,start,end,row_phase(p,d0));
  const int W=p->pb;
  unsigned lph[AP_MAX_LANES];
  if(p->pkcap < (size_t)2*W*nb){
    free(p->pkbuf);
    p->pkbuf=ap_alloc64((size_t)2*W*nb*sizeof(ap_peak));
    if(!p->pkbuf){ p->pkcap=0; return -1; }
    p->pkcap=(size_t)2*W*nb;
  }
  int total=0;
  /* Template-outer when the data needs no per-lane expansion: each template
     batch is reused across all nd blocks while it is still in cache, instead of
     re-streaming the whole template set once per block.  The peaks written are
     the same either way; only the order of the calls changes.  Measured on the
     hierarchical coarse pass (2026-10): the gain grows once a group's coarse
     templates outgrow L2. */
  if(!p->ebr && nd>1){
    for(int tt=0; tt<nt; tt+=W){
      const int cnt=(nt-tt<W)?nt-tt:W;
      const int base=t0+tt;
      const float *Tr,*Ti;
      if((base%W)==0){
        Tr=p->tre+(size_t)(base/W)*n*W;
        Ti=p->tim+(size_t)(base/W)*n*W;
      } else {
        gather_template_batch(p->tsr, p->tsi, p, t0, NULL, tt, cnt);
        Tr=p->tsr; Ti=p->tsi;
      }
      for(int d=0;d<nd;d++){
        const float *Dr=p->dre+(size_t)(d0+d)*n, *Di=p->dim+(size_t)(d0+d)*n;
        if(ap_binmax_prod_batch_peaks(p->fft,Dr,Di,Tr,Ti,cnt,binsize,threshold,
                                p->pkbuf,AP_BACKWARD,start,end,lane_phases(p,d0+d,lph))<0)
          return -1;
        for(int l=0;l<cnt;l++){
          const int t = tt+l;
          const size_t row=(size_t)d*nt+t;
          int c=0;
          for(size_t j=0;j<nb;j++){
            const ap_peak pk=p->pkbuf[(size_t)l*nb+j];
            peaks[row*nb+j]=pk;
            if(pk.index>=0) c++;
          }
          if(counts) counts[row]=c;
          total+=c;
        }
      }
    }
    return total;
  }
  for(int d=0;d<nd;d++){
    const float *Dr=p->dre+(size_t)(d0+d)*n, *Di=p->dim+(size_t)(d0+d)*n;
    if(p->ebr){
      for(size_t k=0;k<n;k++){
        const float a=Dr[k], b=Di[k];
        float *er=p->ebr+k*W, *ei=p->ebi+k*W;
        for(int l=0;l<W;l++){ er[l]=a; ei[l]=b; }
      }
      Dr=p->ebr; Di=p->ebi;
    }
    int tt=0;
    for(; tt+2*W<=nt; tt+=2*W){
      const int base0=t0+tt;
      const int base1=base0+W;
      const float *Tr0, *Ti0, *Tr1, *Ti1;
      if((base0%W)==0){
        Tr0=p->tre+(size_t)(base0/W)*n*W;
        Ti0=p->tim+(size_t)(base0/W)*n*W;
        Tr1=p->tre+(size_t)(base1/W)*n*W;
        Ti1=p->tim+(size_t)(base1/W)*n*W;
      } else {
        gather_template_batch(p->tsr, p->tsi, p, t0, NULL, tt, W);
        Tr0=p->tsr; Ti0=p->tsi;
        if(ap_binmax_prod_batch_peaks(p->fft,Dr,Di,Tr0,Ti0,W,binsize,threshold,
                                p->pkbuf,AP_BACKWARD,start,end,lane_phases(p,d0+d,lph))<0)
          return -1;
        gather_template_batch(p->tsr, p->tsi, p, t0, NULL, tt+W, W);
        Tr1=p->tsr; Ti1=p->tsi;
        if(ap_binmax_prod_batch_peaks(p->fft,Dr,Di,Tr1,Ti1,W,binsize,threshold,
                                p->pkbuf+(size_t)W*nb,AP_BACKWARD,start,end,
                                lane_phases(p,d0+d,lph))<0) return -1;
        goto place_peaks;
      }
      if(ap_binmax_prod_batch_peaks(p->fft,Dr,Di,Tr0,Ti0,W,binsize,threshold,
                              p->pkbuf,AP_BACKWARD,start,end,lane_phases(p,d0+d,lph))<0)
        return -1;
      if(ap_binmax_prod_batch_peaks(p->fft,Dr,Di,Tr1,Ti1,W,binsize,threshold,
                              p->pkbuf+(size_t)W*nb,AP_BACKWARD,start,end,
                              lane_phases(p,d0+d,lph))<0) return -1;
place_peaks:
      for(int l=0;l<2*W;l++){
        const int t = tt+l;
        const size_t row=(size_t)d*nt+t;
        int c=0;
        for(size_t j=0;j<nb;j++){
          const ap_peak pk=p->pkbuf[(size_t)l*nb+j];
          peaks[row*nb+j]=pk;
          if(pk.index>=0) c++;
        }
        if(counts) counts[row]=c;
        total+=c;
      }
    }
    for(; tt<nt; tt+=W){
      const int cnt=(nt-tt<W)?nt-tt:W;
      const int base=t0+tt;
      const float *Tr,*Ti;
      if((base%W)==0){
        Tr=p->tre+(size_t)(base/W)*n*W;
        Ti=p->tim+(size_t)(base/W)*n*W;
      } else {
        gather_template_batch(p->tsr, p->tsi, p, t0, NULL, tt, cnt);
        Tr=p->tsr; Ti=p->tsi;
      }
      if(ap_binmax_prod_batch_peaks(p->fft,Dr,Di,Tr,Ti,cnt,binsize,threshold,
                              p->pkbuf,AP_BACKWARD,start,end,lane_phases(p,d0+d,lph))<0)
        return -1;
      for(int l=0;l<cnt;l++){
        const int t = tt+l;
        const size_t row=(size_t)d*nt+t;
        int c=0;
        for(size_t j=0;j<nb;j++){
          const ap_peak pk=p->pkbuf[(size_t)l*nb+j];
          peaks[row*nb+j]=pk;
          if(pk.index>=0) c++;
        }
        if(counts) counts[row]=c;
        total+=c;
      }
    }
  }
  return total;
}

static int run_pairs(ap_mf_plan *p, int d0, int nd, int t0, int nt,
                     size_t binsize, float threshold,
                     ap_peak *peaks, int *counts, size_t start, size_t end){
  if(p->pb) return run_pairs_pb(p,d0,nd,t0,nt,binsize,threshold,
                                peaks,counts,start,end);
  /* Lanes span templates, not D*T: 32x1 cannot fill one vector. Require
     >=75% occupancy, aligned contiguous templates, and a broad single bin.
     Unmeasured sparse/multi-bin/narrow-window cases keep the original path. */
  const size_t n=p->n, nb=ap_bin_count(binsize,start,end,row_phase(p,d0));
  if(p->allow_pair_alt && nd>=4 && p->w>0 && nt>=p->w && t0%p->w==0
     && 4*(size_t)nt>=3*((nt+p->w-1)/p->w)*(size_t)p->w
     && end-start>=p->n/2 && nb==1){
    ap_mf_plan *q=pair_alternate(p,d0,nd,t0,nt);
    if(q){
      q->bph=p->bph;
      int r=run_pairs_pb(q,d0,nd,t0,nt,binsize,threshold,peaks,counts,start,end);
      q->bph=NULL;
      return r;
    }
  }
  /* Tile the pair loop.  Running d outer already keeps one data spectrum resident
     across the t loop, but every template then streams once per d: D*(1+T)
     spectrum reads.  A tile of nd x nt reads nd+nt spectra and does nd*nt pairs,
     so the count falls to (D/nd)(T/nt)(nd+nt).  Tile size is bounded by how many
     spectra fit - each is 2n floats - and there is no point tiling at all once
     two of them fill the cache.

     Measured at 16x16: 2^12 3.40 -> 2.98 (tile 8), 2^14 12.96 -> 12.34, 2^16
     within noise once two spectra fill L2.  8 is never worse, so take it. */
  const ap_prod_kernel prod=ap_plan_prod_kernel(p->fft,threshold);
  const int tile = p->tile;
  int total=0;

  if(p->gmajor && prod.run && nb == 1){
    for(int dt=0;dt<nd;dt+=tile) for(int tt=0;tt<nt;tt+=tile){
      const int dend=(nd-dt<tile)?nd:dt+tile, tend=(nt-tt<tile)?nt:tt+tile;
      for(int d=dt;d<dend;d++){
        const float *Dr=p->dre+(size_t)(d0+d)*n, *Di=p->dim+(size_t)(d0+d)*n;
        ap_peak *pk_row = peaks + (size_t)d * nt + tt;
        int *cnt_row = counts ? (counts + (size_t)d * nt + tt) : NULL;
        for(int j=tt;j<tend;j++, pk_row++){
          const float *Hr=p->tre+(size_t)(t0+j)*n, *Hi=p->tim+(size_t)(t0+j)*n;
          int r = prod.run(prod.context,Dr,Di,Hr,Hi,binsize,threshold,pk_row,1,start,end,
                           one_phase(p,d0+d));
          if(__builtin_expect(r<0, 0)) return -1;
          int c = (pk_row->index >= 0);
          if(cnt_row) *cnt_row++ = c;
          total += c;
        }
      }
    }
    return total;
  }

  for(int dt=0;dt<nd;dt+=tile) for(int tt=0;tt<nt;tt+=tile){
   const int dend=(nd-dt<tile)?nd:dt+tile, tend=(nt-tt<tile)?nt:tt+tile;
   for(int d=dt;d<dend;d++){
    const float *Dr=p->dre+(size_t)(d0+d)*n, *Di=p->dim+(size_t)(d0+d)*n;
    for(int j=tt;j<tend;j++){
      const int t = j;
      const float *Hr=p->tre+(size_t)(t0+t)*n, *Hi=p->tim+(size_t)(t0+t)*n;
      size_t row=(size_t)d*nt+t;
      int c=0;
      /* Fuse the product into the transform where supported; otherwise use
         the materialized-product path. The bank selects its consumer once. */
      int r = p->gmajor && prod.run
          ? prod.run(prod.context,Dr,Di,Hr,Hi,binsize,threshold,
                     peaks+row*nb,1,start,end,one_phase(p,d0+d)) : -1;
      if(r>=0) for(size_t b=0;b<nb;b++) if(peaks[row*nb+b].index>=0) c++;
      if(r<0){
        mulspec(Dr,Di,Hr,Hi,p->pr,p->pi,n);
        r = ap_binmax_split(p->fft,p->pr,p->pi,binsize,threshold,
                            peaks+row*nb,&c,AP_BACKWARD,start,end,one_phase(p,d0+d));
      }
      if(r<0) return -1;
      /* The interpolation block that stood here was unreachable: p->ihlo is
         set only by ap_mf_set_interp, and interpolation is not exposed to
         Python at all, so it was permanently NULL. It was a remnant of the
         U / oversample design, removed at the Python and hmf.c level and
         left behind in the innermost pair loop. */
      if(counts) counts[row]=c;
      total += c;
    }
   }
  }
  return total;
}

int ap_mf_run(ap_mf_plan *p, int d0, int nd, int t0, int nt,
              size_t binsize, float threshold,
              ap_peak *peaks, int *counts, size_t start, size_t end){
  if(!p||nd<1||nt<1||!binsize) return 0;
  if(!ap_range_ok(d0,nd,p->nd)||!ap_range_ok(t0,nt,p->nt)) return -1;
  if(end>p->n) end=p->n;
  if(start>=end) return 0;
  return run_pairs(p,d0,nd,t0,nt,binsize,threshold,
                   peaks,counts,start,end);
}

int ap_mf_correlate(ap_mf_plan *p,int d0,int nd,int t0,int nt,float *out){
  if(!p||!out||nd<1||!ap_range_ok(d0,nd,p->nd)||nt<1||!ap_range_ok(t0,nt,p->nt))
    return -1;
  if(p->pb){
    const size_t n=p->n; const int W=p->pb;
    for(int d=0;d<nd;d++){
      const float *Dr=p->dre+(size_t)(d0+d)*n, *Di=p->dim+(size_t)(d0+d)*n;
      if(p->ebr){
        for(size_t k=0;k<n;k++){
          const float a=Dr[k],b=Di[k];
          for(int l=0;l<W;l++){
            p->ebr[k*W+l]=a; p->ebi[k*W+l]=b;
          }
        }
        Dr=p->ebr; Di=p->ebi;
      }
      for(int tt=0;tt<nt;tt+=W){
        const int cnt=nt-tt<W?nt-tt:W;
        const int base=t0+tt;
        const float *Tr,*Ti;
        if(base%W==0){
          Tr=p->tre+(size_t)(base/W)*n*W;
          Ti=p->tim+(size_t)(base/W)*n*W;
        } else {
          gather_template_batch(p->tsr, p->tsi, p, base, NULL, 0, cnt);
          Tr=p->tsr; Ti=p->tsi;
        }
        float *dst=out+2*((size_t)d*nt+tt)*n;
        if(ap_corr_prod_batch(p->fft,Dr,Di,Tr,Ti,cnt,dst)) return -1;
      }
    }
    return 0;
  }
  const size_t n=p->n;
  const int tile=p->tile;
  for(int dt=0;dt<nd;dt+=tile) for(int tt=0;tt<nt;tt+=tile){
    const int dend=(nd-dt<tile)?nd:dt+tile;
    const int tend=(nt-tt<tile)?nt:tt+tile;
    for(int d=dt;d<dend;d++){
      const float *dr=p->dre+(size_t)(d0+d)*n;
      const float *di=p->dim+(size_t)(d0+d)*n;
      for(int t=tt;t<tend;t++){
        const float *tr=p->tre+(size_t)(t0+t)*n;
        const float *ti=p->tim+(size_t)(t0+t)*n;
        float *dst=out+2*((size_t)d*nt+t)*n;
        if(p->gmajor){
          if(ap_corr_prod(p->fft,dr,di,tr,ti,dst)) return -1;
        } else {
          mulspec(dr,di,tr,ti,p->pr,p->pi,n);
          if(ap_corr_split(p->fft,p->pr,p->pi,dst)) return -1;
        }
      }
    }
  }
  return 0;
}

static ap_plan *ensure_fwd_batch(ap_mf_plan *p,int real){
  const size_t m=real?p->n/2:p->n;
  const size_t lim=ap_plan_lanes(p->fft)>=16 ? 2048u : 512u;
  if(m<64||m>lim) return NULL;
  ap_plan **slot=real?&p->fwd_real_batch:&p->fwd_cplx_batch;
  if(!*slot) *slot=ap_create_pairbatch_like(p->fft,m);
  if(!*slot) return NULL;
  const int W=ap_plan_lanes(*slot);
  if(W<=0) return NULL;
  if(!p->bspec){
    p->bspec=ap_alloc64((size_t)W*2*p->n*sizeof(float));
    if(!p->bspec) return NULL;
  }
  return *slot;
}

static int forward_series_batch(ap_mf_plan *p,ap_plan *fb,const float *series,
                                size_t nseries,const size_t *starts,int cnt){
  const size_t n=p->n;
  const float inv=1.0f/(float)n;
  const float *srcs[AP_MAX_LANES];
  size_t haves[AP_MAX_LANES];
  float *outs[AP_MAX_LANES];
  for(int l=0;l<cnt;l++){
    const size_t s0=starts[l];
    size_t have=s0<nseries?nseries-s0:0;
    if(have>n) have=n;
    srcs[l]=have?series+(p->real_series?s0:2*s0):series;
    haves[l]=have;
    outs[l]=p->bspec+(size_t)l*2*n;
  }
  if(p->real_series)
    return ap_fft_real_batch(fb,srcs,haves,1,cnt,inv,p->rtw,1,outs);
  return ap_fft_forward_batch(fb,srcs,haves,cnt,inv,outs);
}

static int series_spectra(ap_mf_plan *p,const float *series,size_t nseries,
                          const size_t *starts,int count){
  const size_t n=p->n;
  ap_plan *fb=ensure_fwd_batch(p,p->real_series);
  if(fb){
    const int W=ap_plan_lanes(fb);
    for(int j=0;j<count;j+=W){
      const int cnt=count-j<W?count-j:W;
      if(forward_series_batch(p,fb,series,nseries,starts+j,cnt)<0) return -1;
      for(int l=0;l<cnt;l++)
        if(ap_mf_set_data(p,j+l,p->bspec+(size_t)l*2*n)) return -1;
    }
    return 0;
  }
  const float inv=1.0f/(float)n;
  if(p->real_series){
    if(alloc_pair(&p->sfwd,&p->sspec,2*n*sizeof(float))) return -1;
    for(int j=0;j<count;j++){
      size_t start=starts[j];
      size_t have=start<nseries?nseries-start:0;
      if(have>n) have=n;
      ap_fft_forward_scaled(p->half_fft,have ? series+start : series,have,1,inv,p->sfwd);
      ap_real_split_on(p->fft,p->sfwd,p->rtw,n,p->sspec);
      if(ap_mf_set_data(p,j,p->sspec)) return -1;
    }
    return 0;
  }
  for(int j=0;j<count;j++){
    size_t start=starts[j];
    size_t have=start<nseries?nseries-start:0;
    if(have>n) have=n;
    if(p->gmajor && !p->pair_alt){
      if(p->qdok) p->qdok[j]=0;
      if(p->qdxok) p->qdxok[j]=0;
      ap_fft_forward_scaled_gm(p->fft,have ? series+2*start : series,2*have,1,inv,
                               p->dre+(size_t)j*n,p->dim+(size_t)j*n,p->scratch);
    }else{
      ap_fft_forward_scaled(p->fft,have ? series+2*start : series,2*have,1,inv,p->scratch);
      if(ap_mf_set_data(p,j,p->scratch)) return -1;
    }
  }
  return 0;
}

int ap_mf_correlate_series(ap_mf_plan *p,const float *series,size_t nseries,
                           const size_t *starts,int nblocks,int t0,int nt,float *out){
  if(!p||!series||!starts||!out||nblocks<1||nt<1||!ap_range_ok(t0,nt,p->nt))
    return -1;
  const size_t n=p->n;
  for(int b0=0;b0<nblocks;){
    const int g=nblocks-b0<p->nd?nblocks-b0:p->nd;
    if(series_spectra(p,series,nseries,starts+b0,g)) return -1;
    if(ap_mf_correlate(p,0,g,t0,nt,out+2*(size_t)b0*nt*n)) return -1;
    b0+=g;
  }
  return 0;
}

/* Copy a correlation row into the caller's output, with streaming (non-temporal) stores
   when the call's whole output cannot stay in the last-level cache anyway.  The middle stage
   writes nt x S complex values per call -- ~216 MB a detector in the ladder -- and an
   ordinary store first reads each line it writes (read-for-ownership), doubling the DRAM
   traffic of the stage's one unavoidable output.  A non-temporal store writes the line
   without reading it: the 16k/32k correlate pair 18%/30% faster on Zen 5, 12%/10% on
   Haswell.  But an output that fits the LLC is better left there for the fine stage that
   reads it next: with a 21 MB output on a 32 MB-L3 Zen 3 streaming was 15% SLOWER.  So the
   rule is the footprint against the LLC, the same on every machine, not a per-CPU switch. */
#if defined(__x86_64__) || defined(__i386__)
#include <immintrin.h>
#endif
#include <stdint.h>
#include <unistd.h>
/* The last-level cache of this CPU, from the OS: sysconf (glibc reads cpuid), else Linux
   sysfs (index3, then index2), else macOS sysctl. 0 when the OS does not say: then nothing
   streams (no size is assumed). */
#include <stdio.h>
#if defined(__APPLE__)
#include <sys/sysctl.h>
#endif
static size_t llc_bytes(void){
  static size_t v=(size_t)-1;
  if(v==(size_t)-1){
    long r=-1;
#ifdef _SC_LEVEL3_CACHE_SIZE
    r=sysconf(_SC_LEVEL3_CACHE_SIZE);
#endif
    for(int idx=3; r<=0 && idx>=2; idx--){
      char path[96]; snprintf(path,sizeof path,"/sys/devices/system/cpu/cpu0/cache/index%d/size",idx);
      FILE *f=fopen(path,"r");
      if(f){ unsigned long kb=0; char unit=0;
             if(fscanf(f,"%lu%c",&kb,&unit)>=1) r=(long)kb*(unit=='M'?1024L*1024:1024L);
             fclose(f); }
    }
#if defined(__APPLE__)
    if(r<=0){ unsigned long long b=0; size_t len=sizeof b;
              if(!sysctlbyname("hw.l3cachesize",&b,&len,NULL,0) && b) r=(long)b;
              else if(!sysctlbyname("hw.l2cachesize",&b,&len,NULL,0) && b) r=(long)b; }
#endif
    v = r>0 ? (size_t)r : 0;
  }
  return v;
}
static size_t l2_bytes(void){
  static size_t v=(size_t)-1;
  if(v==(size_t)-1){
    long r=-1;
#ifdef _SC_LEVEL2_CACHE_SIZE
    r=sysconf(_SC_LEVEL2_CACHE_SIZE);
#endif
    for(int idx=0; r<=0 && idx<5; idx++){
      char path[96]; int lvl=0;
      snprintf(path,sizeof path,"/sys/devices/system/cpu/cpu0/cache/index%d/level",idx);
      FILE *f=fopen(path,"r");
      if(!f) break;
      if(fscanf(f,"%d",&lvl)!=1) lvl=0;
      fclose(f);
      if(lvl!=2) continue;
      snprintf(path,sizeof path,"/sys/devices/system/cpu/cpu0/cache/index%d/size",idx);
      f=fopen(path,"r");
      if(f){ unsigned long kb=0; char unit=0;
             if(fscanf(f,"%lu%c",&kb,&unit)>=1) r=(long)kb*(unit=='M'?1024L*1024:1024L);
             fclose(f); }
    }
#if defined(__APPLE__)
    if(r<=0){ unsigned long long b=0; size_t len=sizeof b;
              if(!sysctlbyname("hw.l2cachesize",&b,&len,NULL,0) && b) r=(long)b; }
#endif
    v = r>0 ? (size_t)r : (256u<<10);
  }
  return v;
}
static void out_copy(float *dst,const float *src,size_t bytes,int stream){
#if defined(__x86_64__) || defined(__i386__)
  if(stream){
    size_t nf=bytes/sizeof(float);
    while(nf && ((uintptr_t)dst&63u)){
      if((((uintptr_t)dst&15u)==0) && nf>=4){
        _mm_stream_ps(dst,_mm_loadu_ps(src));
        dst+=4; src+=4; nf-=4;
      }else{
        *dst++=*src++; nf--;
      }
    }
    for(;nf>=16;nf-=16,dst+=16,src+=16){
      const __m128 v0=_mm_loadu_ps(src), v1=_mm_loadu_ps(src+4);
      const __m128 v2=_mm_loadu_ps(src+8), v3=_mm_loadu_ps(src+12);
      _mm_stream_ps(dst,v0); _mm_stream_ps(dst+4,v1);
      _mm_stream_ps(dst+8,v2); _mm_stream_ps(dst+12,v3);
    }
    for(;nf>=4;nf-=4,dst+=4,src+=4) _mm_stream_ps(dst,_mm_loadu_ps(src));
    for(size_t i=0;i<nf;i++) dst[i]=src[i];
    return;
  }
#endif
  (void)stream;
  memcpy(dst,src,bytes);
}

typedef struct {
  const ap_mf_plan *p;
  const float *series;
  float *cdr, *cdi;
  size_t cap, n, nseries, s_first, s_last;
  uint64_t sig;
  int nblocks, real_series, use_fb, last_t0, busy;
} corr_fwd_entry;

static pthread_mutex_t corr_fwd_mu = PTHREAD_MUTEX_INITIALIZER;
static corr_fwd_entry corr_fwd_tab[16];
static unsigned corr_fwd_hand;
static __thread float *corr_mirror_dst;
static __thread size_t corr_mirror_stride;

#if defined(__x86_64__) && defined(__GNUC__)
__attribute__((target("avx512f")))
static void nt_stream_avx512(float *dst, const float *src, size_t bytes){
  size_t nf = bytes / sizeof(float);
  while(nf && ((uintptr_t)dst & 63u)){
    if((((uintptr_t)dst & 15u) == 0) && nf >= 4){
      _mm_stream_ps(dst, _mm_loadu_ps(src));
      dst += 4; src += 4; nf -= 4;
    }else{
      *dst++ = *src++; nf--;
    }
  }
  for(; nf >= 64; nf -= 64, dst += 64, src += 64){
    const __m512 v0 = _mm512_loadu_ps(src), v1 = _mm512_loadu_ps(src + 16);
    const __m512 v2 = _mm512_loadu_ps(src + 32), v3 = _mm512_loadu_ps(src + 48);
    _mm512_stream_ps(dst, v0); _mm512_stream_ps(dst + 16, v1);
    _mm512_stream_ps(dst + 32, v2); _mm512_stream_ps(dst + 48, v3);
  }
  for(; nf >= 16; nf -= 16, dst += 16, src += 16)
    _mm512_stream_ps(dst, _mm512_loadu_ps(src));
  for(size_t i = 0; i < nf; i++) dst[i] = src[i];
}
#endif

#if (defined(__x86_64__) || defined(__i386__)) && defined(__GNUC__)
__attribute__((target("avx")))
static void nt_stream_avx(float *dst, const float *src, size_t bytes){
  size_t nf = bytes / sizeof(float);
  while(nf && ((uintptr_t)dst & 63u)){
    if((((uintptr_t)dst & 15u) == 0) && nf >= 4){
      _mm_stream_ps(dst, _mm_loadu_ps(src));
      dst += 4; src += 4; nf -= 4;
    }else{
      *dst++ = *src++; nf--;
    }
  }
  for(; nf >= 32; nf -= 32, dst += 32, src += 32){
    const __m256 v0 = _mm256_loadu_ps(src), v1 = _mm256_loadu_ps(src + 8);
    const __m256 v2 = _mm256_loadu_ps(src + 16), v3 = _mm256_loadu_ps(src + 24);
    _mm256_stream_ps(dst, v0); _mm256_stream_ps(dst + 8, v1);
    _mm256_stream_ps(dst + 16, v2); _mm256_stream_ps(dst + 24, v3);
  }
  for(; nf >= 8; nf -= 8, dst += 8, src += 8)
    _mm256_stream_ps(dst, _mm256_loadu_ps(src));
  for(size_t i = 0; i < nf; i++) dst[i] = src[i];
}
#endif

static void fast_nt_copy(float *dst, const float *src, size_t bytes){
#if defined(__x86_64__) && defined(__GNUC__)
  static int simd_lvl = -1;
  if(simd_lvl < 0){
    if(__builtin_cpu_supports("avx512f")) simd_lvl = 2;
    else if(__builtin_cpu_supports("avx")) simd_lvl = 1;
    else simd_lvl = 0;
  }
  if(simd_lvl == 2){ nt_stream_avx512(dst, src, bytes); return; }
  if(simd_lvl == 1){ nt_stream_avx(dst, src, bytes); return; }
#elif defined(__i386__) && defined(__GNUC__)
  static int has_avx = -1;
  if(has_avx < 0) has_avx = __builtin_cpu_supports("avx") ? 1 : 0;
  if(has_avx){ nt_stream_avx(dst, src, bytes); return; }
#endif
  out_copy(dst, src, bytes, 1);
}

void ap_mf_set_corr_mirror(float *dst, size_t stride){
  corr_mirror_dst = dst;
  corr_mirror_stride = stride;
}

void ap_mf_stream_copy(float *dst, const float *src, size_t bytes){
  fast_nt_copy(dst, src, bytes);
}

void ap_mf_stream_fence(void){
#if defined(__x86_64__) || defined(__i386__)
  _mm_sfence();
#endif
}

static uint64_t corr_quick_sig(const float *series, size_t nseries, int real_series,
                               size_t s0, size_t s1, size_t n){
  const uint32_t *u = (const uint32_t *)series;
  const size_t len = (real_series ? 1u : 2u) * nseries;
  if(!len) return 0;
  size_t a = (real_series ? 1u : 2u) * (s0 < nseries ? s0 : 0u);
  size_t b_end = s1 + n < nseries ? s1 + n : nseries;
  size_t b = (real_series ? 1u : 2u) * b_end;
  if(b <= a || b > len) b = len;
  uint64_t h = (uint64_t)len ^ ((uint64_t)a << 17) ^ ((uint64_t)b << 33);
  const size_t span = b - a;
  for(unsigned k = 0; k < 8; k++){
    const size_t idx = a + ((span - 1u) * k) / 7u;
    h = (h ^ u[idx]) * 0x9e3779b97f4a7c15ULL;
  }
  return h;
}

int ap_mf_correlate_series_continuous(ap_mf_plan *p,const float *series,
                                      size_t nseries,const size_t *starts,
                                      int nblocks,size_t lo,size_t hi,
                                      int t0,int nt,float *out,const size_t *bounds){
  float *mirror_dst = corr_mirror_dst;
  const size_t mirror_stride = corr_mirror_stride;
  corr_mirror_dst = NULL;
  corr_mirror_stride = 0;
  if(!p||!series||!starts||!out||nblocks<1||nt<1||!ap_range_ok(t0,nt,p->nt)
     ||lo>=hi||hi>p->n) return -1;
  if(bounds)
    for(int b=0;b<nblocks;b++)
      if(bounds[2*b]<lo||bounds[2*b]>=bounds[2*b+1]||bounds[2*b+1]>hi) return -1;
  const size_t n=p->n;
  const int W=p->pb;
  /* this call's output footprint: nt rows over the blocks' written spans */
  size_t span_sum=0;
  for(int b=0;b<nblocks;b++){
    const size_t start=starts[b];
    const size_t blo=bounds?bounds[2*b]:lo, bhi=bounds?bounds[2*b+1]:hi;
    if(start>=nseries||blo>=nseries-start) continue;
    const size_t end=bhi<nseries-start?bhi:nseries-start;
    span_sum+=end-blo;
  }
  const size_t llc = llc_bytes();
  const size_t cache_lim = llc >= (16u<<20) ? llc/2 : (12u<<20);
  if(mirror_dst && ((!W && !p->gmajor) || (p->use_accel && !p->real_series)
     || nt >= p->nt
     || (size_t)nblocks * (2 * n * sizeof(float)) > cache_lim)){
    if(ap_mf_correlate_series_continuous(p, series, nseries, starts, nblocks,
                                         lo, hi, t0, nt, out, bounds))
      return -1;
    for(int b = 0; b < nblocks; b++){
      const size_t start = starts[b];
      const size_t blo = bounds ? bounds[2 * b] : lo, bhi = bounds ? bounds[2 * b + 1] : hi;
      if(start >= nseries || blo >= nseries - start) continue;
      const size_t end = bhi < nseries - start ? bhi : nseries - start;
      const size_t bytes = 2 * (end - blo) * sizeof(float);
      for(int t = 0; t < nt; t++)
        fast_nt_copy(mirror_dst + 2 * ((size_t)t * mirror_stride + start + blo),
                     out + 2 * ((size_t)t * nseries + start + blo), bytes);
    }
    return 0;
  }
  const int stream = !ap_env_flag("MF_CORR_NO_STREAM",0)
                     && llc && (size_t)nt*span_sum*8u > 3*(llc/4);
  if(W && !p->corrbuf){
    p->corrbuf=ap_alloc64(2*(size_t)W*n*sizeof(float));
    if(!p->corrbuf) return -1;
  }
  if(p->use_accel && !p->real_series){
    /* The whole block through the platform FFT: its spectrum in natural order, then per
       template the product with the row-major (conjugated) copy and the inverse. The
       engine's own data rows are in its element order, so they are not reused. */
    for(int b=0;b<nblocks;b++){
      const size_t start=starts[b];
      const size_t blo=bounds?bounds[2*b]:lo, bhi=bounds?bounds[2*b+1]:hi;
      if(start>=nseries||blo>=nseries-start) continue;
      const size_t end=bhi<nseries-start?bhi:nseries-start;
      size_t have=nseries-start; if(have>n) have=n;
      if(ap_accel_block(p->accel,series+2*start,have,1.0f/(float)n)) return -1;
      for(int t=0;t<nt;t++){
        const float *tr,*ti;
        accel_template(p,t0+t,&tr,&ti);
        if(ap_accel_corr(p->accel,NULL,NULL,tr,ti,blo,end-blo,
                         out+2*((size_t)t*nseries+start+blo))) return -1;
      }
    }
    return 0;
  }
  ap_plan *fb=ensure_fwd_batch(p,p->real_series);
  const int W_fb=fb?ap_plan_lanes(fb):0;
  const int use_fb=fb && W_fb>p->nd;
  if((W || p->gmajor) && nt < p->nt && nblocks >= 1
     && (size_t)nblocks * (2 * n * sizeof(float)) <= cache_lim){
    const size_t spec_bytes = 2 * n * sizeof(float);
    const size_t l1d = ap_l1d_bytes();
    const size_t l2_fit = (l2_bytes() * 7) / 8;
    const int kt_step = (spec_bytes > l1d && 9u * spec_bytes <= l2_fit) ? 4 : 1;
    const float inv = 1.0f / (float)n;
    const int gm_n1 = p->gmajor ? p->n1 : 0;
    if(!use_fb && p->real_series && alloc_pair(&p->sfwd, &p->sspec, spec_bytes))
      return -1;
    const size_t need_fl = (size_t)nblocks * n;
    const size_t s_first = starts[0], s_last = starts[nblocks - 1];
    const uint64_t qsig = corr_quick_sig(series, nseries, p->real_series, s_first, s_last, n);
    int slot = -1, hit = 0;
    float *cdr = NULL, *cdi = NULL;
    pthread_mutex_lock(&corr_fwd_mu);
    if(t0 > 0){
      for(int i = 0; i < 16; i++){
        corr_fwd_entry *e = &corr_fwd_tab[i];
        if(e->p == p && e->series == series && e->s_first == s_first
           && e->s_last == s_last && e->sig == qsig && e->n == n
           && e->nseries == nseries && e->nblocks == nblocks
           && e->real_series == p->real_series && e->use_fb == use_fb
           && e->last_t0 >= 0 && t0 > e->last_t0
           && e->cdr && e->cdi && e->cap >= need_fl){
          e->last_t0 = (t0 + nt < p->nt) ? (t0 + nt - 1) : p->nt;
          e->busy++;
          slot = i; cdr = e->cdr; cdi = e->cdi;
          hit = 1; break;
        }
      }
    }
    if(!hit){
      for(int i = 0; i < 16; i++){
        if(corr_fwd_tab[i].busy == 0 && corr_fwd_tab[i].p == p
           && corr_fwd_tab[i].series == series
           && corr_fwd_tab[i].s_first == s_first
           && corr_fwd_tab[i].nblocks == nblocks){
          slot = i; break;
        }
      }
      for(int tries = 0; slot < 0 && tries < 16; tries++){
        int cand = (int)(corr_fwd_hand++ & 15u);
        if(corr_fwd_tab[cand].busy == 0) slot = cand;
      }
      if(slot >= 0){
        corr_fwd_entry *e = &corr_fwd_tab[slot];
        if(e->cap < need_fl || !e->cdr || !e->cdi){
          float *ndr = ap_alloc64(need_fl * sizeof(float));
          float *ndi = ap_alloc64(need_fl * sizeof(float));
          if(!ndr || !ndi){
            free(ndr); free(ndi);
            slot = -1;
          }else{
            free(e->cdr); free(e->cdi);
            e->cdr = ndr; e->cdi = ndi; e->cap = need_fl;
          }
        }
        if(slot >= 0){
          e->p = NULL;
          e->busy = 1;
          cdr = e->cdr; cdi = e->cdi;
        }
      }
    }
    pthread_mutex_unlock(&corr_fwd_mu);
    if(slot >= 0 && cdr && cdi){
      int err = 0;
      if(!hit){
        if(use_fb){
          for(int b0 = 0; b0 < nblocks; b0 += W_fb){
            const int g = nblocks - b0 < W_fb ? nblocks - b0 : W_fb;
            if(forward_series_batch(p, fb, series, nseries, starts + b0, g) < 0){
              err = -1; break;
            }
            for(int d = 0; d < g; d++)
              ap_split_store_on(p->fft, p->bspec + (size_t)d * 2 * n,
                                cdr + (size_t)(b0 + d) * n, cdi + (size_t)(b0 + d) * n,
                                n, 0, gm_n1, p->n2, p->w);
          }
        }else{
          for(int b = 0; b < nblocks; b++){
            const size_t start = starts[b];
            if(start >= nseries) continue;
            size_t have = nseries - start; if(have > n) have = n;
            float *dr_b = cdr + (size_t)b * n, *di_b = cdi + (size_t)b * n;
            if(p->real_series){
              ap_fft_forward_scaled(p->half_fft, series + start, have, 1, inv, p->sfwd);
              ap_real_split_on(p->fft, p->sfwd, p->rtw, n, p->sspec);
              ap_split_store_on(p->fft, p->sspec, dr_b, di_b, n, 0, gm_n1, p->n2, p->w);
            }else if(p->gmajor){
              ap_fft_forward_scaled_gm(p->fft, series + 2 * start, 2 * have, 1, inv,
                                       dr_b, di_b, p->scratch);
            }else{
              ap_fft_forward_scaled(p->fft, series + 2 * start, 2 * have, 1, inv, p->scratch);
              ap_split_store_on(p->fft, p->scratch, dr_b, di_b, n, 0, 0, p->n2, p->w);
            }
          }
        }
        pthread_mutex_lock(&corr_fwd_mu);
        corr_fwd_entry *e = &corr_fwd_tab[slot];
        if(!err){
          e->p = p; e->series = series; e->n = n; e->nseries = nseries;
          e->s_first = s_first; e->s_last = s_last; e->sig = qsig;
          e->nblocks = nblocks; e->real_series = p->real_series; e->use_fb = use_fb;
          e->last_t0 = (t0 + nt < p->nt) ? (t0 + nt - 1) : p->nt;
        }
        pthread_mutex_unlock(&corr_fwd_mu);
      }
      if(!err){
        for(int b = 0; b < nblocks; b++){
          const size_t start = starts[b];
          const size_t blo = bounds ? bounds[2 * b] : lo, bhi = bounds ? bounds[2 * b + 1] : hi;
          if(start >= nseries || blo >= nseries - start) continue;
          const size_t end = bhi < nseries - start ? bhi : nseries - start;
          const size_t bytes = 2 * (end - blo) * sizeof(float);
          if(W){
            const float *Dr = cdr + (size_t)b * n, *Di = cdi + (size_t)b * n;
            if(p->ebr){
              for(size_t k = 0; k < n; k++){
                const float a = Dr[k], bv = Di[k];
                for(int l = 0; l < W; l++){ p->ebr[k * W + l] = a; p->ebi[k * W + l] = bv; }
              }
              Dr = p->ebr; Di = p->ebi;
            }
            for(int tt = 0; tt < nt; tt += W){
              const int cnt = nt - tt < W ? nt - tt : W;
              const int base = t0 + tt;
              const float *Tr, *Ti;
              if(base % W == 0){
                Tr = p->tre + (size_t)(base / W) * n * W;
                Ti = p->tim + (size_t)(base / W) * n * W;
              }else{
                gather_template_batch(p->tsr, p->tsi, p, base, NULL, 0, cnt);
                Tr = p->tsr; Ti = p->tsi;
              }
              if(ap_corr_prod_batch(p->fft, Dr, Di, Tr, Ti, cnt, p->corrbuf)){
                err = -1; break;
              }
              for(int t = 0; t < cnt; t++){
                const float *csrc = p->corrbuf + 2 * ((size_t)t * n + blo);
                out_copy(out + 2 * ((size_t)(tt + t) * nseries + start + blo), csrc, bytes, stream);
                if(mirror_dst)
                  fast_nt_copy(mirror_dst + 2 * ((size_t)(tt + t) * mirror_stride + start + blo),
                               csrc, bytes);
              }
            }
          }else{
            for(int t = 0; t < nt;){
              int kt = nt - t;
              if(kt > kt_step) kt = kt_step;
              if(ap_corr_prod_window_multi(p->fft, cdr + (size_t)b * n, cdi + (size_t)b * n,
                                           p->tre + (size_t)(t0 + t) * n, p->tim + (size_t)(t0 + t) * n,
                                           n, kt, blo, end,
                                           out + 2 * ((size_t)t * nseries + start + blo),
                                           2 * nseries, p->scratch, stream)){
                err = -1; break;
              }
              if(mirror_dst){
                for(int q = 0; q < kt; q++)
                  fast_nt_copy(mirror_dst + 2 * ((size_t)(t + q) * mirror_stride + start + blo),
                               out + 2 * ((size_t)(t + q) * nseries + start + blo), bytes);
              }
              t += kt;
            }
          }
          if(err) break;
        }
      }
#if defined(__x86_64__) || defined(__i386__)
      if(!err && (stream || mirror_dst)) _mm_sfence();
#endif
      pthread_mutex_lock(&corr_fwd_mu);
      corr_fwd_tab[slot].busy--;
      pthread_mutex_unlock(&corr_fwd_mu);
      return err;
    }
  }
  if(!W && p->gmajor){
    const size_t spec_bytes=2*n*sizeof(float);
    const size_t l1d=ap_l1d_bytes();
    const size_t l2=l2_bytes();
    const size_t l2_fit=(l2*7)/8, l2_tile=(l2*3)/4;
    const int kt_step=(spec_bytes>l1d && 9u*spec_bytes<=l2_fit) ? 4 : 1;
    const size_t out_per_blk=(nblocks>0 ? (span_sum/(size_t)nblocks)*8u : spec_bytes);
    int b_tile=1;
    if(!use_fb && spec_bytes>32768u && spec_bytes<=65536u && nt>kt_step && nblocks>1){
      const size_t untiled=((size_t)nt+1u+(size_t)kt_step)*spec_bytes
                           + (stream ? 0u : (size_t)nt*out_per_blk);
      if(untiled>l2){
        const size_t used=(size_t)(2*kt_step)*spec_bytes;
        const size_t per_blk=spec_bytes+(stream ? 0u : (size_t)kt_step*out_per_blk);
        if(l2_tile>used+per_blk){
          size_t fit=(l2_tile-used)/per_blk;
          if(fit>8) fit=8;
          if((int)fit>nblocks) fit=(size_t)nblocks;
          if(fit>=2) b_tile=(int)fit;
        }
      }
    }
    float *tdr=NULL,*tdi=NULL;
    const int cap_slots=(!use_fb && b_tile>1) ? ap_corr_tile_slots(p->fft,b_tile,&tdr,&tdi) : 0;
    const int step_g=use_fb ? W_fb : (cap_slots>=2 ? (cap_slots<b_tile ? cap_slots : b_tile) : 1);
    const float inv=1.0f/(float)n;
    if(!use_fb && p->real_series && alloc_pair(&p->sfwd,&p->sspec,2*n*sizeof(float)))
      return -1;
    for(int b0=0;b0<nblocks;){
      const int g=nblocks-b0<step_g ? nblocks-b0 : step_g;
      if(use_fb && forward_series_batch(p,fb,series,nseries,starts+b0,g)<0) return -1;
      size_t d_start[AP_MAX_LANES],d_blo[AP_MAX_LANES],d_end[AP_MAX_LANES];
      int scnt=0;
      const int use_tile=(!use_fb && cap_slots>=g && g>1);
      for(int d=0;d<g;d++){
        const size_t start=starts[b0+d];
        const size_t blo=bounds?bounds[2*(b0+d)]:lo, bhi=bounds?bounds[2*(b0+d)+1]:hi;
        if(start>=nseries||blo>=nseries-start) continue;
        float *dr_s=use_tile ? (tdr+(size_t)scnt*n) : p->dre;
        float *di_s=use_tile ? (tdi+(size_t)scnt*n) : p->dim;
        if(!use_tile){
          if(p->qdok) p->qdok[0]=0;
          if(p->qdxok) p->qdxok[0]=0;
          if(p->alt_dready) p->alt_dready[0]=0;
        }
        if(use_fb){
          ap_split_store_on(p->fft,p->bspec+(size_t)d*2*n,dr_s,di_s,n,0,p->n1,p->n2,p->w);
        }else if(p->real_series){
          size_t have=nseries-start; if(have>n) have=n;
          ap_fft_forward_scaled(p->half_fft,series+start,have,1,inv,p->sfwd);
          ap_real_split_on(p->fft,p->sfwd,p->rtw,n,p->sspec);
          ap_split_store_on(p->fft,p->sspec,dr_s,di_s,n,0,p->n1,p->n2,p->w);
        }else{
          size_t have=nseries-start; if(have>n) have=n;
          ap_fft_forward_scaled_gm(p->fft,series+2*start,2*have,1,inv,dr_s,di_s,p->scratch);
        }
        if(!use_tile){
          const size_t end=bhi<nseries-start?bhi:nseries-start;
          for(int t=0;t<nt;){
            int kt=nt-t;
            if(kt>kt_step) kt=kt_step;
            if(ap_corr_prod_window_multi(p->fft,dr_s,di_s,
                                         p->tre+(size_t)(t0+t)*n,p->tim+(size_t)(t0+t)*n,
                                         n,kt,blo,end,
                                         out+2*((size_t)t*nseries+start+blo),
                                         2*nseries,p->scratch,stream))
              return -1;
            t+=kt;
          }
        }else{
          d_start[scnt]=start;
          d_blo[scnt]=blo;
          d_end[scnt]=bhi<nseries-start?bhi:nseries-start;
          scnt++;
        }
      }
      if(use_tile && scnt>0){
        for(int t=0;t<nt;){
          int kt=nt-t;
          if(kt>kt_step) kt=kt_step;
          for(int s=0;s<scnt;s++){
            if(ap_corr_prod_window_multi(p->fft,tdr+(size_t)s*n,tdi+(size_t)s*n,
                                         p->tre+(size_t)(t0+t)*n,p->tim+(size_t)(t0+t)*n,
                                         n,kt,d_blo[s],d_end[s],
                                         out+2*((size_t)t*nseries+d_start[s]+d_blo[s]),
                                         2*nseries,p->scratch,stream))
              return -1;
          }
          t+=kt;
        }
      }
      b0+=g;
    }
#if defined(__x86_64__) || defined(__i386__)
    if(stream) _mm_sfence();
#endif
    return 0;
  }
  /* Keep each large block's spectrum (Dr, Di) in L2 across t = 0..nt-1 rather than
     transforming p->nd blocks upfront and evicting earlier slots before correlation. */
  const int max_g=use_fb ? W_fb : ((!W && 2*n*sizeof(float)>=65536) ? 1 : p->nd);
  for(int b0=0;b0<nblocks;){
    const int g=nblocks-b0<max_g ? nblocks-b0 : max_g;
    if(use_fb){
      if(forward_series_batch(p,fb,series,nseries,starts+b0,g)<0) return -1;
    }else{
      if(series_spectra(p,series,nseries,starts+b0,g)) return -1;
    }
    for(int d=0;d<g;d++){
      const size_t start=starts[b0+d];
      const size_t blo=bounds?bounds[2*(b0+d)]:lo, bhi=bounds?bounds[2*(b0+d)+1]:hi;
      if(start>=nseries||blo>=nseries-start) continue;
      if(use_fb && ap_mf_set_data(p,0,p->bspec+(size_t)d*2*n)) return -1;
      const int slot=use_fb?0:d;
      const size_t end=bhi<nseries-start?bhi:nseries-start;
      const size_t bytes=2*(end-blo)*sizeof(float);
      const float *Dr=p->dre+(size_t)slot*n, *Di=p->dim+(size_t)slot*n;
      if(W){
        if(p->ebr){
          for(size_t k=0;k<n;k++){
            const float a=Dr[k],b=Di[k];
            for(int l=0;l<W;l++){p->ebr[k*W+l]=a;p->ebi[k*W+l]=b;}
          }
          Dr=p->ebr; Di=p->ebi;
        }
        for(int tt=0;tt<nt;tt+=W){
          const int cnt=nt-tt<W?nt-tt:W;
          const int base=t0+tt;
          const float *Tr,*Ti;
          if(base%W==0){
            Tr=p->tre+(size_t)(base/W)*n*W;
            Ti=p->tim+(size_t)(base/W)*n*W;
          }else{
            gather_template_batch(p->tsr, p->tsi, p, base, NULL, 0, cnt);
            Tr=p->tsr; Ti=p->tsi;
          }
          if(ap_corr_prod_batch(p->fft,Dr,Di,Tr,Ti,cnt,p->corrbuf)) return -1;
          for(int t=0;t<cnt;t++)
            out_copy(out+2*((size_t)(tt+t)*nseries+start+blo),
                     p->corrbuf+2*((size_t)t*n+blo),bytes,stream);
        }
      }else{
        for(int t=0;t<nt;t++){
          const float *tr=p->tre+(size_t)(t0+t)*n;
          const float *ti=p->tim+(size_t)(t0+t)*n;
          float *tdst=out+2*((size_t)t*nseries+start+blo);
          if(p->gmajor){
            if(ap_corr_prod_window(p->fft,Dr,Di,tr,ti,blo,end,tdst,p->scratch,stream)) return -1;
          }else{
            mulspec(Dr,Di,tr,ti,p->pr,p->pi,n);
            if(ap_corr_split(p->fft,p->pr,p->pi,p->scratch)) return -1;
            out_copy(tdst,p->scratch+2*blo,bytes,stream);
          }
        }
      }
    }
    b0+=g;
  }
#if defined(__x86_64__) || defined(__i386__)
  if(stream) _mm_sfence();
#endif
  return 0;
}

/* The same correlation of a REAL series of nseries samples (float32): each block transformed
   at half size and split into its full spectrum -- the middle stage of a real-real-complex
   hierarchy, filtering the real top output. out is complex, as above. */
int ap_mf_correlate_series_continuous_real(ap_mf_plan *p,const float *series,
                                           size_t nseries,const size_t *starts,
                                           int nblocks,size_t lo,size_t hi,
                                           int t0,int nt,float *out,const size_t *bounds){
  if(!p||p->n<4) return -1;
  if(!p->half_fft){
    const size_t h=p->n/2;
    if(!ap_supported(h)) return -1;
    p->half_fft=ap_create_like(p->fft,h);
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
  if(alloc_pair(&p->sfwd,&p->sspec,2*p->n*sizeof(float))) return -1;
  p->real_series=1;
  const int r=ap_mf_correlate_series_continuous(p,series,nseries,starts,nblocks,lo,hi,t0,nt,out,
                                                bounds);
  p->real_series=0;
  return r;
}

/* Filter a time series over a caller-supplied block layout.
 *
 * The flat twin of ap_hmf_run_series, and it exists for the same reason: one
 * call per segment rather than one per block removes the per-block round trip
 * -- no separately planned forward transform, no spectrum handed back and
 * forth. Until now only the hierarchical filter could express this, which made
 * the wide interface unavailable to exactly the callers most likely to want
 * it: flat needs no reference spectrum and no (n, snr, fd) tables, so it is
 * what a non-gravitational-wave domain reaches for.
 *
 * Blocks sharing a window are filtered together, up to the plan's own nd.
 * That is the grouping knob and there is no other: a flat plan's ndata is
 * already how many segments it can hold, so inventing a second control would
 * let the two disagree.
 */
int ap_mf_run_series(ap_mf_plan *p,
                     const float *series,size_t nseries,
                     const size_t *start,const size_t *win_start,
                     const size_t *win_end,const unsigned *bin_phase,int nblocks,
                     int t0,int nt,size_t binsize,float threshold,
                     ap_peak *peaks,int *counts){
  if(!p||nblocks<1||nt<1||!binsize) return 0;
  if(!series||!start||!win_start||!win_end) return -1;
  if(!ap_range_ok(t0,nt,p->nt)) return -1;
  const size_t n=p->n;
  if(alloc_pair(&p->sfwd,&p->sspec,2*n*sizeof(float))) return -1;
  const size_t nb0=ap_mf_nbins_phased(p,binsize,win_start[0],win_end[0],
                                      bin_phase?bin_phase[0]:0u);
  int total=0;
  for(int b0=0;b0<nblocks;){
    int g=1;
    while(g<p->nd && b0+g<nblocks
          && win_start[b0+g]==win_start[b0] && win_end[b0+g]==win_end[b0]) g++;
    if(series_spectra(p,series,nseries,start+b0,g)) return -1;
    /* peaks is addressed at a single stride, so every window must produce the
       same bin count. A shorter one at a segment's edge does not: it writes
       where the next block's row begins and runs off the end of the caller's
       buffer -- heap corruption from ordinary overlap-save input, since edge
       blocks are exactly the ragged ones this call exists to accept.
       Refusing is the honest answer; the shape the API returns has one nbins
       in it and cannot express two. */
    for(int j=0;j<g;j++)
      if(ap_mf_nbins_phased(p,binsize,win_start[b0+j],win_end[b0+j],
                            bin_phase?bin_phase[b0+j]:0u)!=nb0) return -1;
    p->bph = bin_phase ? bin_phase+b0 : NULL;    /* rows 0..g-1 are blocks b0..b0+g-1 */
    int r=ap_mf_run(p,0,g,t0,nt,binsize,threshold,
                    peaks+(size_t)b0*nt*nb0,counts?counts+(size_t)b0*nt:NULL,
                    win_start[b0],win_end[b0]);
    p->bph = NULL;
    if(r<0) return -1;
    total+=r;
    b0+=g;
  }
  return total;
}

/* The half-size transforms contain even and odd full-rate lags in separate
   data rows. Even bin widths have regular half-size bins. Odd widths alternate
   their parity boundaries, so retain individual reduced lags and place each
   on the caller's full-rate grid. Bound their staging to one template tile. */
int ap_mf_run_dif(ap_mf_plan *p,int d0,int t0,int nt,size_t binsize,float threshold,
                  ap_peak *peaks,int *counts,size_t start,size_t end,unsigned ph){
  if(!p || !binsize || nt<1 || d0<0 || d0>p->nd-2 || t0<0 || t0>p->nt-nt) return -1;
  if(end>2*p->n) end=2*p->n;
  if(start>=end) return 0;
  const size_t org=start-ph;            /* bins numbered from here (ap_bin_count) */
  const size_t nb=ap_bin_count(binsize,start,end,ph);
  /* Odd widths, and bins not numbered from start, keep each reduced lag and place it on
     the full-rate grid; the regular reduced bins below align only from start. */
  const int samples=((binsize&1) || ph) && nb>1;
  const size_t reduced_bs=samples ? 1 : (nb==1 ? p->n : binsize/2);
  const size_t lo[2]={(start+1)/2,start/2};
  const size_t hi[2]={(end+1)/2,end/2};
  const size_t nr[2]={ap_mf_nbins(p,reduced_bs,lo[0],hi[0]),
                      ap_mf_nbins(p,reduced_bs,lo[1],hi[1])};
  const int tile=samples && nt>p->tile ? p->tile : nt;
  const size_t need=samples ? (size_t)tile*(nr[0]>nr[1]?nr[0]:nr[1])
                            : (size_t)nt*(nr[0]+nr[1]);
  if(need>p->dif_pkcap){
    ap_peak *next=malloc(need*sizeof(ap_peak));
    if(!next) return -1;
    free(p->dif_pkbuf); p->dif_pkbuf=next; p->dif_pkcap=need;
  }
  if(!samples){
    /* Regular reduced bins already align with output bins. Merge directly,
       without clearing/scattering/rescanning the output or dividing per peak. */
    const size_t odd_offset=(size_t)nt*nr[0];
    if(lo[0]==lo[1] && hi[0]==hi[1]){
      /* Preserve template-batch reuse across both parity rows. */
      if(ap_mf_run(p,d0,2,t0,nt,reduced_bs,threshold,p->dif_pkbuf,NULL,lo[0],hi[0])<0)
        return -1;
    }else{
      for(int parity=0;parity<2;parity++){
        if(nr[parity] && ap_mf_run(p,d0+parity,1,t0,nt,reduced_bs,threshold,
                                   p->dif_pkbuf+(parity?odd_offset:0),NULL,
                                   lo[parity],hi[parity])<0) return -1;
      }
    }
    int total=0;
    const ap_peak empty={-1,0.f,0.f,0.f};
    for(int t=0;t<nt;t++){
      int count=0;
      for(size_t b=0;b<nb;b++){
        ap_peak even=b<nr[0]?p->dif_pkbuf[(size_t)t*nr[0]+b]:empty;
        ap_peak odd=b<nr[1]?p->dif_pkbuf[odd_offset+(size_t)t*nr[1]+b]:empty;
        if(even.index>=0) even.index*=2;
        if(odd.index>=0) odd.index=2*odd.index+1;
        ap_peak best=even;
        if(odd.index>=0 && (even.index<0 || odd.magnitude>even.magnitude
             || (odd.magnitude==even.magnitude && odd.index<even.index))) best=odd;
        peaks[(size_t)t*nb+b]=best;
        count+=best.index>=0;
      }
      if(counts) counts[t]=count;
      total+=count;
    }
    return total;
  }
  for(size_t j=0;j<(size_t)nt*nb;j++) peaks[j]=(ap_peak){-1,0.f,0.f,0.f};
  for(int parity=0;parity<2;parity++){
    if(!nr[parity]) continue;
    for(int tt=0;tt<nt;tt+=tile){
      const int count=nt-tt<tile?nt-tt:tile;
      if(ap_mf_run(p,d0+parity,1,t0+tt,count,reduced_bs,threshold,
                   p->dif_pkbuf,NULL,lo[parity],hi[parity])<0) return -1;
      for(int t=0;t<count;t++) for(size_t b=0;b<nr[parity];b++){
        ap_peak pk=p->dif_pkbuf[(size_t)t*nr[parity]+b];
        if(pk.index<0) continue;
        pk.index=2*pk.index+parity;
        const size_t bin=((size_t)pk.index-org)/binsize;
        ap_peak *dst=peaks+(size_t)(tt+t)*nb+bin;
        if(dst->index<0 || pk.magnitude>dst->magnitude
           || (pk.magnitude==dst->magnitude && pk.index<dst->index)) *dst=pk;
      }
    }
  }
  int total=0;
  for(int t=0;t<nt;t++){
    int count=0;
    for(size_t b=0;b<nb;b++) count+=peaks[(size_t)t*nb+b].index>=0;
    if(counts) counts[t]=count;
    total+=count;
  }
  return total;
}

int ap_mf_run_series_dif(ap_mf_plan *p,
                         const float *series, size_t nseries,
                         const size_t *start, const size_t *win_start,
                         const size_t *win_end, const unsigned *bin_phase, int nblocks,
                         int t0, int nt, size_t binsize, float threshold,
                         int decimated,
                         ap_peak *peaks, int *counts){
  if(!p || nblocks < 1 || nt < 1 || !binsize) return 0;
  if(!series || !start || !win_start || !win_end || !peaks) return -1;
  if(!ap_range_ok(t0,nt,p->nt)) return -1;
  if(p->nd < 2) return -1;

  const size_t n = p->n;

  if(!p->sspec_tw){
    p->sspec_tw = ap_alloc64(2 * n * sizeof(float));
    p->twiddles = ap_alloc64(2 * n * sizeof(float));
    if(!p->sspec_tw || !p->twiddles) return -1;
    const size_t N_tw = 2 * n;
    for(size_t k = 0; k < n; k++){
      double angle = 2.0 * M_PI * (double)k / (double)N_tw;
      p->twiddles[2 * k]     = (float)cos(angle);
      p->twiddles[2 * k + 1] = (float)sin(angle);
    }
  }

  const size_t input_n=decimated?n:2*n;
  const size_t first_end=win_end[0]<input_n?win_end[0]:input_n;
  if(win_start[0]>=first_end) return -1;
  const size_t nb0=ap_bin_count(binsize,win_start[0],first_end,bin_phase?bin_phase[0]:0u);
  if(decimated){
    if(!(p->fft_fwd_n && p->sfwd_n && p->sspec_n)){   /* all three, or none */
      ap_destroy(p->fft_fwd_n); p->fft_fwd_n = ap_create_like(p->fft,n);
      if(!p->fft_fwd_n || alloc_pair(&p->sfwd_n,&p->sspec_n,2 * n * sizeof(float))){
        ap_destroy(p->fft_fwd_n); p->fft_fwd_n = NULL; return -1;
      }
    }
  } else {
    if(!(p->fft_fwd && p->sfwd_2n && p->sspec_2n)){   /* all three, or none */
      ap_destroy(p->fft_fwd); p->fft_fwd = ap_create_like(p->fft,input_n);
      if(!p->fft_fwd || alloc_pair(&p->sfwd_2n,&p->sspec_2n,2 * input_n * sizeof(float))){
        ap_destroy(p->fft_fwd); p->fft_fwd = NULL; return -1;
      }
    }
  }

  int total = 0;

  for(int b = 0; b < nblocks; b++){
    const size_t s0 = start[b];
    const size_t ws = win_start[b];
    const size_t we = win_end[b]<input_n?win_end[b]:input_n;
    if(ws>=we) return -1;
    const unsigned ph=bin_phase?bin_phase[b]:0u;
    const size_t nb=ap_bin_count(binsize,ws,we,ph);
    if(nb!=nb0) return -1;
    const float * restrict d0_ptr;

    if(decimated){
      size_t have = s0 < nseries ? nseries - s0 : 0;
      if(have > n) have = n;
      const float inv = 1.0f / (float)n;
      ap_fft_forward_scaled(p->fft_fwd_n, have ? series + 2 * s0 : series, 2 * have, 1, inv,
                            p->sspec_n);
      d0_ptr = p->sspec_n;
    } else {
      const size_t N = 2 * n;
      size_t have = s0 < nseries ? nseries - s0 : 0;
      if(have > N) have = N;
      const float inv = 1.0f / (float)N;
      ap_fft_forward_scaled(p->fft_fwd, have ? series + 2 * s0 : series, 2 * have, 1, inv,
                            p->sspec_2n);
      d0_ptr = p->sspec_2n;
    }

    const float * restrict tw = p->twiddles;
    float * restrict d1_ptr = p->sspec_tw;
    for(size_t k = 0; k < n; k++){
      float dr = d0_ptr[2 * k];
      float di = d0_ptr[2 * k + 1];
      float wr = tw[2 * k];
      float wi = tw[2 * k + 1];
      d1_ptr[2 * k]     = dr * wr - di * wi;
      d1_ptr[2 * k + 1] = dr * wi + di * wr;
    }

    if(ap_mf_set_data(p, 0, d0_ptr)) return -1;
    if(ap_mf_set_data(p, 1, d1_ptr)) return -1;

    const size_t full_ws = decimated ? 2 * ws : ws;
    const size_t full_we = decimated ? 2 * we : we;
    /* In decimated mode binsize is measured in input samples; indices still
       describe the reconstructed full-rate output. */
    const size_t full_bs = decimated ? (binsize>=n?2*n:2*binsize) : binsize;
    int r=ap_mf_run_dif(p,0,t0,nt,full_bs,threshold,
                        peaks+(size_t)b*nt*nb,counts?counts+(size_t)b*nt:NULL,
                        full_ws,full_we,decimated?2*ph:ph);
    if(r<0) return -1;
    total+=r;
  }
  return total;
}

static int run_pairs_pooled_pb(ap_mf_plan *p, int d0,
                               const int *dsel, const int *tsel, int npairs,
                               int t0, size_t binsize, float threshold,
                               ap_peak *peaks, int *counts, size_t start, size_t end,
                               int nt){
  const size_t n = p->n, nb = ap_bin_count(binsize, start, end, row_phase(p, d0 + dsel[0]));
  const int W = p->pb;
  unsigned lph[AP_MAX_LANES];
  if(p->pkcap < (size_t)W * nb){
    free(p->pkbuf);
    p->pkbuf = ap_alloc64((size_t)W * nb * sizeof(ap_peak));
    if(!p->pkbuf){ p->pkcap = 0; return -1; }
    p->pkcap = (size_t)W * nb;
  }
  int total = 0;
  for(int tt = 0; tt < npairs; tt += W){
    const int cnt = (npairs - tt < W) ? npairs - tt : W;
    int same_data = !p->ebr;
    const int base = t0 + tsel[tt];
    int packed_templates = base % W == 0;
    for(int l = 1; l < cnt; l++){
      same_data &= dsel[tt+l] == dsel[tt];
      packed_templates &= tsel[tt+l] == tsel[tt]+l;
    }
    /* Survivors retain their data-major order. A batch from one block with packed
       templates reads both inputs directly; scattered pairs fuse gather + multiply. */
    if(same_data && (packed_templates || n <= 64 || !p->tmre)){
      const float *Tr, *Ti;
      if(packed_templates){
        Tr = p->tre + (size_t)(base/W)*n*W;
        Ti = p->tim + (size_t)(base/W)*n*W;
      } else {
        gather_template_batch(p->tsr, p->tsi, p, t0, tsel, tt, cnt);
        Tr = p->tsr; Ti = p->tsi;
      }
      const size_t off = (size_t)(d0+dsel[tt])*n;
      if(ap_binmax_prod_batch_peaks(p->fft, p->dre+off, p->dim+off, Tr, Ti, cnt,
                                    binsize, threshold, p->pkbuf, AP_BACKWARD, start, end,
                                    lane_phases(p, d0+dsel[tt], lph))<0)
        return -1;
    } else if(p->tmre && (!packed_templates || n >= 128)){
      const float *drp[AP_MAX_LANES], *dip[AP_MAX_LANES];
      const float *trp[AP_MAX_LANES], *tip[AP_MAX_LANES];
      for(int l = 0; l < cnt; l++){
        const size_t doff = (size_t)(d0 + dsel[tt + l]) * n;
        const size_t toff = (size_t)(t0 + tsel[tt + l]) * n;
        drp[l] = p->dre + doff; dip[l] = p->dim + doff;
        trp[l] = p->tmre + toff; tip[l] = p->tmim + toff;
      }
      const unsigned *ph = NULL;          /* lanes are pairs: each its own row's phase */
      if(p->bph){
        for(int l = 0; l < AP_MAX_LANES; l++) lph[l] = l < cnt ? p->bph[d0+dsel[tt+l]] : 0u;
        ph = lph;
      }
      if(ap_binmax_prod_gather_lanes_peaks(p->fft, drp, dip, trp, tip, cnt,
                                           binsize, threshold, p->pkbuf, AP_BACKWARD, start, end,
                                           ph)<0)
        return -1;
    } else {
      const float *Tr, *Ti;
      if(packed_templates){
        Tr = p->tre + (size_t)(base/W)*n*W;
        Ti = p->tim + (size_t)(base/W)*n*W;
      } else {
        gather_template_batch(p->tsr, p->tsi, p, t0, tsel, tt, cnt);
        Tr = p->tsr; Ti = p->tsi;
      }
      gather_data_batch(p->dsr, p->dsi, p, d0, dsel, tt, cnt);
      const unsigned *ph = NULL;          /* lanes are pairs: each its own row's phase */
      if(p->bph){
        for(int l = 0; l < AP_MAX_LANES; l++) lph[l] = l < cnt ? p->bph[d0+dsel[tt+l]] : 0u;
        ph = lph;
      }
      if(ap_binmax_prod_batch_lanes_peaks(p->fft, p->dsr, p->dsi, Tr, Ti, cnt,
                                          binsize, threshold, p->pkbuf, AP_BACKWARD, start, end,
                                          ph)<0)
        return -1;
    }
    for(int l = 0; l < cnt; l++){
      const int d = dsel[tt + l];
      const int t = tsel[tt + l];
      const size_t row = (size_t)d * nt + t;
      int c = 0;
      for(size_t j = 0; j < nb; j++){
        const ap_peak pk = p->pkbuf[(size_t)l * nb + j];
        peaks[row * nb + j] = pk;
        if(pk.index >= 0) c++;
      }
      if(counts) counts[row] = c;
      total += c;
    }
  }
  return total;
}

int ap_mf_run_pairs_pooled(ap_mf_plan *p, int d0,
                           const int *dsel, const int *tsel, int npairs,
                           int t0, size_t binsize, float threshold,
                           ap_peak *peaks, int *counts, size_t start, size_t end,
                           int nt){
  if(!p || npairs < 1 || !binsize) return 0;
  if(d0 < 0 || d0 >= p->nd || !ap_range_ok(t0,nt,p->nt)) return -1;
  for(int j = 0; j < npairs; j++){
    if(dsel[j] < 0 || d0 + dsel[j] >= p->nd) return -1;
    if(tsel[j] < 0 || tsel[j] >= nt) return -1;
  }
  if(end > p->n) end = p->n;
  if(start >= end) return 0;
  if(p->pb && p->dsr && p->tsr){
    return run_pairs_pooled_pb(p, d0, dsel, tsel, npairs, t0, binsize, threshold,
                               peaks, counts, start, end, nt);
  }
  const size_t nb = ap_bin_count(binsize, start, end, row_phase(p, d0 + dsel[0]));
  int total = 0;
  for(int i = 0; i < npairs; i++){
    int d = dsel[i];
    int t = tsel[i];
    const size_t row = (size_t)d * nt + t;
    int r = ap_mf_run(p, d0 + d, 1, t0 + t, 1, binsize, threshold,
                      peaks + row * nb, counts ? counts + row : NULL,
                      start, end);
    if(r < 0) return -1;
    total += r;
  }
  return total;
}

int ap_mf_run_pairs_packed(ap_mf_plan *p, int d0,
                           const int *dsel, const int *tsel, int npairs,
                           int t0, size_t binsize, float threshold,
                           ap_peak *peaks, size_t start, size_t end){
  if(!p || npairs < 1 || !binsize) return 0;
  if(d0 < 0 || d0 >= p->nd) return -1;
  for(int j = 0; j < npairs; j++){
    if(dsel[j] < 0 || d0 + dsel[j] >= p->nd) return -1;
    if(tsel[j] < 0 || t0 + tsel[j] < 0 || t0 + tsel[j] >= p->nt) return -1;
  }
  if(end > p->n) end = p->n;
  if(start >= end) return 0;
  const size_t n = p->n, nb = ap_bin_count(binsize, start, end, 0u);
  if(!(p->pb && p->dsr && p->tsr)){
    const unsigned *saved = p->bph;
    p->bph = NULL;
    for(int j = 0; j < npairs; j++){
      if(ap_mf_run(p, d0 + dsel[j], 1, t0 + tsel[j], 1, binsize, threshold,
                   peaks + (size_t)j * nb, NULL, start, end) < 0){
        p->bph = saved;
        return -1;
      }
    }
    p->bph = saved;
    return 1;
  }
  const int W = p->pb;
  if(p->pkcap < (size_t)W * nb){
    free(p->pkbuf);
    p->pkbuf = ap_alloc64((size_t)W * nb * sizeof(ap_peak));
    if(!p->pkbuf){ p->pkcap = 0; return -1; }
    p->pkcap = (size_t)W * nb;
  }
  for(int tt = 0; tt < npairs; tt += W){
    const int cnt = (npairs - tt < W) ? npairs - tt : W;
    int same_data = !p->ebr;
    const int base = t0 + tsel[tt];
    int packed_templates = base % W == 0;
    for(int l = 1; l < cnt; l++){
      same_data &= dsel[tt + l] == dsel[tt];
      packed_templates &= tsel[tt + l] == tsel[tt] + l;
    }
    if(same_data && (packed_templates || n <= 64 || !p->tmre)){
      const float *Tr, *Ti;
      if(packed_templates){
        Tr = p->tre + (size_t)(base / W) * n * W;
        Ti = p->tim + (size_t)(base / W) * n * W;
      } else {
        gather_template_batch(p->tsr, p->tsi, p, t0, tsel, tt, cnt);
        Tr = p->tsr; Ti = p->tsi;
      }
      const size_t off = (size_t)(d0 + dsel[tt]) * n;
      if(ap_binmax_prod_batch_peaks(p->fft, p->dre + off, p->dim + off, Tr, Ti, cnt,
                                    binsize, threshold, p->pkbuf, AP_BACKWARD, start, end,
                                    NULL) < 0)
        return -1;
    } else if(p->tmre && (!packed_templates || n >= 128)){
      const float *drp[AP_MAX_LANES], *dip[AP_MAX_LANES];
      const float *trp[AP_MAX_LANES], *tip[AP_MAX_LANES];
      for(int l = 0; l < cnt; l++){
        const size_t doff = (size_t)(d0 + dsel[tt + l]) * n;
        const size_t toff = (size_t)(t0 + tsel[tt + l]) * n;
        drp[l] = p->dre + doff; dip[l] = p->dim + doff;
        trp[l] = p->tmre + toff; tip[l] = p->tmim + toff;
      }
      if(ap_binmax_prod_gather_lanes_peaks(p->fft, drp, dip, trp, tip, cnt,
                                           binsize, threshold, p->pkbuf, AP_BACKWARD, start, end,
                                           NULL) < 0)
        return -1;
    } else {
      const float *Tr, *Ti;
      if(packed_templates){
        Tr = p->tre + (size_t)(base / W) * n * W;
        Ti = p->tim + (size_t)(base / W) * n * W;
      } else {
        gather_template_batch(p->tsr, p->tsi, p, t0, tsel, tt, cnt);
        Tr = p->tsr; Ti = p->tsi;
      }
      gather_data_batch(p->dsr, p->dsi, p, d0, dsel, tt, cnt);
      if(ap_binmax_prod_batch_lanes_peaks(p->fft, p->dsr, p->dsi, Tr, Ti, cnt,
                                          binsize, threshold, p->pkbuf, AP_BACKWARD, start, end,
                                          NULL) < 0)
        return -1;
    }
    memcpy(peaks + (size_t)tt * nb, p->pkbuf, (size_t)cnt * nb * sizeof(ap_peak));
  }
  return 1;
}

/* ---- Q15 coarse screen ---------------------------------------------------
 *
 * The coarse tier's question is only "can this pair's maximum reach the
 * threshold".  The screen answers it for 2*AP_W pairs per call in int16 fixed
 * point (q15-inl.h) and says "maybe" whenever the int16 maximum, plus the
 * transform's error margin, reaches the threshold.  The caller then runs the
 * float tier on exactly those pairs, so its decisions -- and every peak -- are
 * the float tier's own; the screen only removes pairs the float tier would
 * have rejected anyway.  See docs/cpu-q15-gate.md for the error model and the
 * measurement behind ap_q15_margin.
 *
 * Inputs are quantised per template (once) and per data slot (on first use
 * after set_data), from the plan's own float copies. */
static size_t q15_nat(const ap_mf_plan *p,size_t k){
  if(!p->gmajor) return k;
  const size_t a=k%(size_t)p->n1, b=k/(size_t)p->n1;
  return (a/(size_t)p->w)*(size_t)p->n2*(size_t)p->w+b*(size_t)p->w+a%(size_t)p->w;
}

int ap_mf_q15_lanes(const ap_mf_plan *p){
  if(!p) return 0;
  int M1,M2;
  if(ap_q15_factor(p->n,&M1,&M2)) return 0;
  return ap_q15_lanes(p->fft);
}

static int q15_prepare_common(ap_mf_plan *p){
  if(p->qw) return 0;
  const int qw=ap_mf_q15_lanes(p);
  if(qw<=0) return -1;
  const size_t n=p->n;
  p->qts=calloc((size_t)p->nt,sizeof(float));
  p->qds=calloc((size_t)p->nd,sizeof(float));
  p->qscr=ap_alloc64(ap_q15_scratch_bytes(n,qw));
  if(!p->qts||!p->qds||!p->qscr){
    free(p->qts);free(p->qds);free(p->qscr);
    p->qts=NULL;p->qds=NULL;p->qscr=NULL;
    return -1;
  }
  p->qw=qw;
  p->qtail=ap_q15_has_tile(p->fft);
  {
    const size_t l1d=ap_l1d_bytes();
    p->qfull=p->qtail && qw>=32 && n>=512 && (!l1d || ap_q15_batch_bytes(n,qw)>2*l1d);
  }
  return 0;
}

static int q15_prepare(ap_mf_plan *p){
  if(q15_prepare_common(p)) return -1;
  if(p->qtr) return 0;
  const size_t n=p->n, qw=(size_t)p->qw, ng=((size_t)p->nt+qw-1)/qw;
  p->qtr=ap_alloc64(ng*n*qw*sizeof(int16_t));
  p->qti=ap_alloc64(ng*n*qw*sizeof(int16_t));
  p->qtok=calloc((size_t)p->nt,1);
  p->qd=ap_alloc64((size_t)p->nd*n*3*sizeof(int16_t));
  p->qdok=calloc((size_t)p->nd,1);
  if(!p->qtr||!p->qti||!p->qtok||!p->qd||!p->qdok){
    free(p->qtr);free(p->qti);free(p->qtok);free(p->qd);free(p->qdok);
    p->qtr=p->qti=NULL;p->qtok=NULL;p->qd=NULL;p->qdok=NULL;
    return -1;
  }
  /* padding lanes of the last group stay zero */
  memset(p->qtr,0,ng*n*qw*sizeof(int16_t));
  memset(p->qti,0,ng*n*qw*sizeof(int16_t));
  return 0;
}

static int q15_prepare_gather(ap_mf_plan *p){
  if(q15_prepare_common(p)) return -1;
  if(p->qdm) return 0;
  /* +32 int16 (64 B) row padding makes every row stride an odd multiple of 64 B,
     preventing 4 KB L1D/L2 set-conflict aliasing across gathered rows at n = 1024. */
  const size_t stride=2*p->n+32;
  p->qdm=ap_alloc64((size_t)p->nd*stride*sizeof(int16_t));
  p->qdmok=calloc((size_t)p->nd,1);
  p->qtm=ap_alloc64((size_t)p->nt*stride*sizeof(int16_t));
  p->qtmok=calloc((size_t)p->nt,1);
  if(!p->qdm||!p->qdmok||!p->qtm||!p->qtmok){
    free(p->qdm);free(p->qdmok);free(p->qtm);free(p->qtmok);
    p->qdm=p->qtm=NULL;p->qdmok=p->qtmok=NULL;
    return -1;
  }
  return 0;
}

static inline int16_t q15_q(float v,double s){
  double r=nearbyint((double)v*s);
  if(r>32767.0) r=32767.0;
  if(r<-32767.0) r=-32767.0;
  return (int16_t)r;
}

/* Templates are stored conjugated already; quantise as stored. |t_q|_2 is
   AP_Q15_TNORM unless that would put a component past int16. */
static void q15_template(ap_mf_plan *p,int t){
  const size_t n=p->n; const int qw=p->qw;
  const float *re,*im; int nat=0;
  if(p->pb && p->tmre){ re=p->tmre+(size_t)t*n; im=p->tmim+(size_t)t*n; }
  else { re=p->tre+(size_t)t*n; im=p->tim+(size_t)t*n; nat=1; }
  double ss=0, amax=0;
  for(size_t k=0;k<n;k++){
    const size_t j=nat?q15_nat(p,k):k;
    const double r=re[j], i=im[j];
    ss+=r*r+i*i;
    if(fabs(r)>amax) amax=fabs(r);
    if(fabs(i)>amax) amax=fabs(i);
  }
  double sc = !isfinite(ss) ? -1.0 : 0.0;
  if(sc==0.0 && ss>0){
    sc=AP_Q15_TNORM(n)/sqrt(ss);
    if(sc*amax>32767.0) sc=32767.0/amax;
  }
  int16_t *qr=p->qtr+(size_t)(t/qw)*n*qw+(t%qw), *qi=p->qti+(size_t)(t/qw)*n*qw+(t%qw);
  for(size_t k=0;k<n;k++){
    const size_t j=nat?q15_nat(p,k):k;
    qr[k*qw]=sc>0?q15_q(re[j],sc):0;
    qi[k*qw]=sc>0?q15_q(im[j],sc):0;
  }
  p->qts[t]=(float)sc;
  p->qtok[t]=1;
}

/* |d_q|_2 is set so that |d_q|_2 * AP_Q15_TNORM / 2^15 + 1.5 n <= AP_Q15_L1:
   every template's |t_q|_2 is at most AP_Q15_TNORM, so this holds for every
   pair (the sqrt(n) is the rounding's worst growth of the norm). */
/* Keep preparation in its consumer's loop even with the separate tail caller;
   outlining it changed the cost of ordinary series calls on narrow targets. */
static inline int q15_popcnt64(uint64_t v){
#if defined(__GNUC__) || defined(__clang__)
  return __builtin_popcountll(v);
#else
  int c=0;
  while(v){ v&=v-1; c++; }
  return c;
#endif
}

/* Block d's quantisation scale: |d_q|_2 = D (below), from the plan's float copy. */
static inline __attribute__((always_inline)) double q15_data_scale(const ap_mf_plan *p,int d){
  const size_t n=p->n;
  const float *re=p->dre+(size_t)d*n, *im=p->dim+(size_t)d*n;
  double ss=0;
  if(ap_q15_sumsq(p->fft,re,im,&ss)){
    /* Sum of squares is invariant to group-major element permutation. */
    float s4[4]={0,0,0,0};
    size_t k=0;
    for(;k+4<=n;k+=4) for(int u=0;u<4;u++) s4[u]+=re[k+u]*re[k+u]+im[k+u]*im[k+u];
    for(;k<n;k++) s4[0]+=re[k]*re[k]+im[k]*im[k];
    ss=(double)s4[0]+s4[1]+s4[2]+s4[3];
  }
  const double D=(AP_Q15_L1-1.5*(double)n)*32768.0/AP_Q15_TNORM(n)-sqrt((double)n);
  /* float rounding of the sum can overstate or understate it by ~1e-7
     relative; the 0.999 keeps the bound on the side that matters. */
  return !isfinite(ss) ? -1.0 : ss>0 ? 0.999*D/sqrt(ss) : 0.0;
}

static inline __attribute__((always_inline)) void q15_data(ap_mf_plan *p,int d){
  const size_t n=p->n;
  const float *re=p->dre+(size_t)d*n, *im=p->dim+(size_t)d*n;
  int16_t *q=p->qd+(size_t)d*n*3;
  if(!ap_q15_data(p->fft,re,im,p->gmajor?p->n1:0,p->n2,p->w,q,&p->qds[d])){
    p->qdok[d]=1;
    return;
  }
  const double sc=q15_data_scale(p,d);
  const float scf=(float)sc;
  if(!(sc>0)){ memset(q,0,n*3*sizeof(int16_t)); }
  else if(p->gmajor){
    for(size_t k=0;k<n;k++){
      const size_t j=q15_nat(p,k);
      const int r=(int)lrintf(re[j]*scf), i=(int)lrintf(im[j]*scf);
      q[3*k]=(int16_t)r; q[3*k+1]=(int16_t)i; q[3*k+2]=(int16_t)-i;
    }
  } else {
    /* |x*scf| <= |d_q|_2 < 32767 by construction, so no clamp is needed */
    for(size_t k=0;k<n;k++){
      const int r=(int)lrintf(re[k]*scf), i=(int)lrintf(im[k]*scf);
      q[3*k]=(int16_t)r; q[3*k+1]=(int16_t)i; q[3*k+2]=(int16_t)-i;
    }
  }
  p->qds[d]=(float)sc;
  p->qdok[d]=1;
}

/* One lane's int16 threshold from its data and template scales.  Without the margin
   (p->qnomargin) the screen gates on its own statistic when quantisation rounding is small
   against one SNR unit; when an out-of-window glitch crushes qds*qts/2^15 below 2*margin,
   the deterministic bound margin is restored so an in-window signal cannot be rounded below
   threshold.  Non-finite inputs (scale < 0) fail open; exact-zero inputs (scale == 0) have
   exact correlation 0 and pass only when threshold <= 0. */
static inline int16_t q15_lanethr(float threshold,float qds,float qts,float margin,int nomargin){
  if(qds<0.f || qts<0.f) return (int16_t)-32768;
  if(qds==0.f || qts==0.f) return !(threshold>0.f) ? (int16_t)-32768 : (int16_t)32767;
  const float ds=qds*(float)(1.0/32768.0);
  const float eq=(!nomargin || ds*qts<2.0f*margin) ? margin : 0.0f;
  const float q=threshold*ds*(1.0f-1e-4f)*qts-eq;
  const float T=q*q*(float)(1.0/32768.0)-1.0f;
  return !(q>0.f) ? (int16_t)-32768 : T>=32767.f ? (int16_t)32767 : (int16_t)ceilf(T);
}

static inline float q15_stat_val(float qds,float qts,int16_t lanemax){
  if(qds<0.f || qts<0.f) return -1.0f;
  const double sdt=(double)qds*qts/32768.0;
  return sdt>0 ? (float)(sqrt((double)lanemax*32768.0)/sdt) : 0.0f;
}

/* Keep tail scheduling separate so it does not expand the ordinary screen's
   register allocation or data-quantization call sites on other backends. */
static __attribute__((noinline)) int q15_tail_group(ap_mf_plan *p, int d0, int first,
                      int t0, int nt, int g, int l1, int max_width, float threshold,
                      size_t start, size_t end, const float *bl,
                      const int16_t *tr, const int16_t *ti,
                      unsigned char *pass, float *stat){
  const size_t n=p->n;
  const int qw=p->qw;                      /* 32 on AVX-512, 16 on AVX2 */
  const float margin=(float)ap_q15_margin(n);
  float qds_lane[64], qts_lane[64];
  int16_t lanethr[64], lanemax[64];
  int total=0;
  for(int d=d0;d<first;d++) if(!p->qdok[d]) q15_data(p,d);
  for(int off=0;off<l1;){
    /* tiles of qw/4 or qw/2 templates, repeated for 4 or 2 blocks */
    const int width=(l1-off<=qw/4 || max_width<=qw/4) ? qw/4 : qw/2;
    const int blocks=qw/width, active=l1-off<width ? l1-off : width;
    for(int l=0;l<width;l++){
      const float ts=bl[off+l];
      for(int b=0;b<blocks;b++) qts_lane[b*width+l]=ts;
    }
    const uint64_t act_mask=((uint64_t)1<<active)-1u;
    for(int d=d0;d<first;d+=blocks){
      for(int b=0;b<blocks;b++){
        const float ds=p->qds[d+b];
        for(int l=0;l<width;l++) qds_lane[b*width+l]=ds;
      }
      if(ap_q15_lanethr(p->fft,threshold,qds_lane,1,qts_lane,margin,p->qnomargin,lanethr)){
        for(int l=0;l<qw;l++)
          lanethr[l]=q15_lanethr(threshold,qds_lane[l],qts_lane[l],margin,p->qnomargin);
      }
      uint64_t bits=0;
      if(ap_q15_screen_tile(p->fft,width,p->qd+(size_t)d*n*3,tr+off,ti+off,
                            start,end,lanethr,&bits,stat?lanemax:NULL,p->qscr)) return -1;
      if(!bits && !stat){
        for(int b=0;b<blocks;b++)
          memset(pass+(size_t)(d+b-d0)*nt+(size_t)(g*qw+off-t0),0,(size_t)active);
        continue;
      }
      for(int b=0;b<blocks;b++){
        const size_t row=(size_t)(d+b-d0)*nt+(size_t)(g*qw+off-t0);
        const uint64_t mbits=(bits>>(b*width))&act_mask;
        if(!mbits){
          memset(pass+row,0,(size_t)active);
        } else {
          for(int l=0;l<active;l++) pass[row+l]=(unsigned char)((mbits>>l)&1u);
          total+=q15_popcnt64(mbits);
        }
        if(stat){
          for(int l=0;l<active;l++)
            stat[row+l]=q15_stat_val(p->qds[d+b],bl[off+l],lanemax[b*width+l]);
        }
      }
    }
    off+=width;
  }
  return total;
}

int ap_mf_q15_screen(ap_mf_plan *p,int d0,int nd,int t0,int nt,float threshold,
                     size_t start,size_t end,unsigned char *pass,float *stat){
  if(!p||nd<1||nt<1) return 0;
  if(!ap_range_ok(d0,nd,p->nd)||!ap_range_ok(t0,nt,p->nt)) return -1;
  if(end>p->n) end=p->n;
  if(start>=end) return 0;
  if(q15_prepare(p)) return -1;
  const size_t n=p->n; const int qw=p->qw;
  const float margin=(float)ap_q15_margin(n);
  float bl[64];
  int16_t lanethr[64], lanemax[64];
  int total=0;
  for(int g=t0/qw; g*qw<t0+nt; g++){
    const int l0 = g*qw<t0 ? t0-g*qw : 0;
    const int l1 = (g+1)*qw>t0+nt ? t0+nt-g*qw : qw;
    for(int l=0;l<qw;l++){
      const int t=g*qw+l;
      bl[l]=0.f;
      if(l<l0 || l>=l1) continue;
      if(!p->qtok[t]) q15_template(p,t);
      bl[l]=p->qts[t];
    }
    const int16_t *tr=p->qtr+(size_t)g*n*qw, *ti=p->qti+(size_t)g*n*qw;
    int first=d0;
    /* Tile full template groups across pairs of blocks when a full batch spills well
       past L1D on 512-bit targets (b >= 512); aligned partial tails up to 3/4 of a
       group tile across 4 blocks at any size. */
    if(p->qfull && l0==0 && l1==qw && nd>=2){
      first=d0+(nd/2)*2;
      const int r=q15_tail_group(p,d0,first,t0,nt,g,l1,qw/2,threshold,
                                 start,end,bl,tr,ti,pass,stat);
      if(r<0) return -1;
      total+=r;
    } else if(p->qtail && l0==0 && l1<=3*qw/4 && nd>=4){
      first=d0+(nd/4)*4;
      const int r=q15_tail_group(p,d0,first,t0,nt,g,l1,qw/2,threshold,start,end,bl,tr,ti,pass,stat);
      if(r<0) return -1;
      total+=r;
    }
    const int nlanes=l1-l0;
    const uint64_t act_mask=((uint64_t)1<<nlanes)-1u;
    for(int d=first;d<d0+nd;d++){
      if(!p->qdok[d]) q15_data(p,d);
      /* Lane l's int16 maximum m satisfies m >= |z_q|^2/2^15 - 1, and
         z_q = z * sd*st/2^15 to within EQ (ap_q15_margin).  So the float
         maximum can reach `threshold` only if m >= q^2/2^15 - 1 with
         q = threshold*sd*st/2^15 - EQ.  A lane with q <= 0, or with a
         non-finite scale, always passes.  The 1e-4 covers the float
         tier's own rounding (~1e-6 relative). */
      if(ap_q15_lanethr(p->fft,threshold,&p->qds[d],0,bl,margin,p->qnomargin,lanethr)){
        for(int l=0;l<qw;l++)
          lanethr[l] = q15_lanethr(threshold,p->qds[d],bl[l],margin,p->qnomargin);
      }
      uint64_t bits=0;
      if(ap_q15_screen(p->fft,p->qd+(size_t)d*n*3,tr,ti,start,end,lanethr,&bits,
                       stat?lanemax:NULL,p->qscr)) return -1;
      /* lanes l0..l1 are templates g*qw+l0-t0 .. in the caller's rows */
      unsigned char *row=pass+(size_t)(d-d0)*nt+(size_t)(g*qw+l0-t0);
      if(!bits){
        memset(row,0,(size_t)nlanes);
        if(!stat) continue;
      } else {
        const uint64_t mbits=(bits>>l0)&act_mask;
        if(!mbits){
          memset(row,0,(size_t)nlanes);
        } else {
          for(int l=0;l<nlanes;l++) row[l]=(unsigned char)((mbits>>l)&1u);
          total+=q15_popcnt64(mbits);
        }
      }
      if(stat){
        float *srow=stat+(size_t)(d-d0)*nt+(size_t)(g*qw+l0-t0);
        for(int l=l0;l<l1;l++) srow[l-l0]=q15_stat_val(p->qds[d],bl[l],lanemax[l]);
      }
    }
  }
  return total;
}

/* With the margin (the default) a pair the screen rejects cannot reach `threshold` in the
   float tier: the screen stands in for that tier.  Without it the screen decides on its own
   int16 maximum, as a gate in its own right whose threshold the chain's model sets. */
int ap_mf_set_q15_margin(ap_mf_plan *p,int on){
  if(!p) return -1;
  p->qnomargin=!on;
  return 0;
}

/* The screen over an arbitrary list of pairs: pair j is data d0+dsel[j] against template
   t0+tsel[j].  pass[j] is set when its int16 maximum over [start, end) can reach `threshold`
   (with the margin, as ap_mf_q15_screen decides; without it, on the maximum itself); stat,
   when not NULL, gets the maximum in the float tier's units; lag_idx, when not NULL, gets the
   window's argmax lag index (ties broken to earliest lag).  Returns the passes, or -1.
   Only touched data blocks and templates are quantised into contiguous padded rows (qdm, qtm),
   and pairs are pooled directly in QW-lane gather batches at 100% SIMD occupancy without slab
   or template-group bucketing. */
static void q15_template_contig(ap_mf_plan *p,int t){
  const size_t n=p->n, stride=2*n+32;
  const float *re,*im; int nat=0;
  if(p->pb && p->tmre){ re=p->tmre+(size_t)t*n; im=p->tmim+(size_t)t*n; }
  else { re=p->tre+(size_t)t*n; im=p->tim+(size_t)t*n; nat=1; }
  double ss=0, amax=0;
  for(size_t k=0;k<n;k++){
    const size_t j=nat?q15_nat(p,k):k;
    const double r=re[j], i=im[j];
    ss+=r*r+i*i;
    if(fabs(r)>amax) amax=fabs(r);
    if(fabs(i)>amax) amax=fabs(i);
  }
  double sc = !isfinite(ss) ? -1.0 : 0.0;
  if(sc==0.0 && ss>0){
    sc=AP_Q15_TNORM(n)/sqrt(ss);
    if(sc*amax>32767.0) sc=32767.0/amax;
  }
  int16_t *qr=p->qtm+(size_t)t*stride, *qi=qr+n;
  if(!(sc>0)){
    memset(qr,0,2*n*sizeof(int16_t));
  } else {
    for(size_t k=0;k<n;k++){
      const size_t j=nat?q15_nat(p,k):k;
      qr[k]=q15_q(re[j],sc);
      qi[k]=q15_q(im[j],sc);
    }
  }
  p->qts[t]=(float)sc;
  p->qtmok[t]=1;
}

static void q15_data_row(ap_mf_plan *p,int d){
  const size_t n=p->n, stride=2*n+32;
  const float *re=p->dre+(size_t)d*n, *im=p->dim+(size_t)d*n;
  int16_t *qdr=p->qdm+(size_t)d*stride, *qdi=qdr+n;
  if(!ap_q15_data_contig(p->fft,re,im,p->gmajor?p->n1:0,p->n2,p->w,qdr,qdi,&p->qds[d])){
    p->qdmok[d]=1;
    return;
  }
  const double sc=q15_data_scale(p,d);
  const float scf=(float)sc;
  if(!(sc>0)){
    memset(qdr,0,2*n*sizeof(int16_t));
  } else if(p->gmajor){
    for(size_t k=0;k<n;k++){
      const size_t j=q15_nat(p,k);
      qdr[k]=(int16_t)lrintf(re[j]*scf);
      qdi[k]=(int16_t)lrintf(im[j]*scf);
    }
  } else {
    for(size_t k=0;k<n;k++){
      qdr[k]=(int16_t)lrintf(re[k]*scf);
      qdi[k]=(int16_t)lrintf(im[k]*scf);
    }
  }
  p->qds[d]=(float)sc;
  p->qdmok[d]=1;
}

int ap_mf_q15_pairs_lag(ap_mf_plan *p,int d0,const int *dsel,const int *tsel,int npairs,int t0,
                        float threshold,size_t start,size_t end,unsigned char *pass,float *stat,
                        int16_t *lag_idx){
  if(!p||npairs<1) return 0;
  if(!pass) return -1;
  if(end>p->n) end=p->n;
  if(start>=end) return 0;
  for(int j=0;j<npairs;j++)
    if(d0+dsel[j]<0||d0+dsel[j]>=p->nd||t0+tsel[j]<0||t0+tsel[j]>=p->nt) return -1;
  if(q15_prepare_gather(p)) return -1;
  const size_t n=p->n, stride=2*n+32;
  const int qw=p->qw;
  const float margin=(float)ap_q15_margin(n);
  float qds_lane[64], qts_lane[64];
  int16_t lanethr[64], lanemax[64], laneidx[64];
  const int16_t *drp[64], *dip[64], *trp[64], *tip[64];
  int total=0;
  for(int i0=0;i0<npairs;i0+=qw){
    const int cnt=npairs-i0<qw ? npairs-i0 : qw;
    for(int l=0;l<cnt;l++){
      const int d=d0+dsel[i0+l], t=t0+tsel[i0+l];
      if(!p->qdmok[d]) q15_data_row(p,d);
      if(!p->qtmok[t]) q15_template_contig(p,t);
      const int16_t *dq=p->qdm+(size_t)d*stride;
      const int16_t *tq=p->qtm+(size_t)t*stride;
      drp[l]=dq; dip[l]=dq+n;
      trp[l]=tq; tip[l]=tq+n;
      qds_lane[l]=p->qds[d]; qts_lane[l]=p->qts[t];
    }
    for(int l=cnt;l<qw;l++){
      qds_lane[l]=0.f; qts_lane[l]=0.f;
    }
    if(ap_q15_lanethr(p->fft,threshold,qds_lane,1,qts_lane,margin,p->qnomargin,lanethr)){
      for(int l=0;l<cnt;l++)
        lanethr[l]=q15_lanethr(threshold,qds_lane[l],qts_lane[l],margin,p->qnomargin);
      for(int l=cnt;l<qw;l++)
        lanethr[l]=32767;
    }
    uint64_t bits=0;
    if(ap_q15_screen_gather(p->fft,drp,dip,trp,tip,cnt,start,end,lanethr,&bits,
                            stat?lanemax:NULL,lag_idx?laneidx:NULL,p->qscr)) return -1;
    if(!bits && !stat && !lag_idx){
      memset(pass+i0,0,(size_t)cnt);
      continue;
    }
    for(int l=0;l<cnt;l++){
      const int ok=(int)((bits>>l)&1u);
      pass[i0+l]=(unsigned char)ok;
      total+=ok;
      if(stat) stat[i0+l]=q15_stat_val(qds_lane[l],qts_lane[l],lanemax[l]);
      if(lag_idx) lag_idx[i0+l]=(qds_lane[l]>0.f && qts_lane[l]>0.f) ? laneidx[l] : (int16_t)-1;
    }
  }
  return total;
}

int ap_mf_q15_pairs(ap_mf_plan *p,int d0,const int *dsel,const int *tsel,int npairs,int t0,
                    float threshold,size_t start,size_t end,unsigned char *pass,float *stat){
  return ap_mf_q15_pairs_lag(p,d0,dsel,tsel,npairs,t0,threshold,start,end,pass,stat,NULL);
}

/* Debug accessor: how many data slots the plan actually has. */

/* The root stage of a hierarchical search: one transformed input block against one root
   filter, both one-sided spectra of n/2 + 1 bins, to the real n-point series
   scale * C2R(conj(T) D) over bins [k0, k1). The product, the band and the scale are formed
   in one pass that also merges the spectrum for a half-size backward transform
   (ap_root_merge_on), so the series costs one n/2-point transform and one read of each input. */
struct ap_root { size_t n; ap_plan *half; float *tw; float *Z; };

ap_root *ap_root_create(size_t n){
  if(n<128 || (n&(n-1)) || !ap_supported(n/2)) return NULL;
  ap_root *r=calloc(1,sizeof(*r));
  if(!r) return NULL;
  const size_t h=n/2;
  r->n=n;
  r->half=ap_create(h);
  r->tw=malloc(2*(h+1)*sizeof(float));
  r->Z=ap_alloc64(n*sizeof(float));
  if(!r->half||!r->tw||!r->Z){ ap_root_destroy(r); return NULL; }
  for(size_t k=0;k<=h;k++){
    const double a=2.0*3.14159265358979323846*(double)k/(double)n;
    r->tw[2*k]=(float)cos(a); r->tw[2*k+1]=(float)sin(a);
  }
  return r;
}

void ap_root_destroy(ap_root *r){
  if(!r) return;
  if(r->half) ap_destroy(r->half);
  free(r->tw);
  free(r->Z);
  free(r);
}

size_t ap_root_length(const ap_root *r){ return r ? r->n : 0; }

int ap_root_real(ap_root *r,const float *D,const float *T,size_t nbins,
                 size_t k0,size_t k1,float scale,float *out){
  if(!r||!D||!T||!out) return -1;
  const size_t h=r->n/2;
  if(nbins<h+1 || k0>k1 || k1>h+1) return -1;
  ap_root_merge_on(r->half,D,T,k0,k1,scale,r->tw,r->n,r->Z);
  ap_fft(r->half,r->Z,out,AP_BACKWARD);
  return 0;
}
