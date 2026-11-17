/* The gate model's simulation kernel: see simulate.h, and M_simulate in _core.c for the
   arrays. Moved from _core.c unchanged but for its buffers, which are plain arrays here. */
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "simulate.h"
#include "alloc.h"

void ap_gauss_fill_rows(float *out, size_t ostride, size_t rows, size_t len, uint64_t seed,
                        uint64_t offset, uint64_t row_step, const float *scale,
                        const unsigned char *rowmask);                /* src/gauss.cc */
float ap_sim_power(const float *y, const float *d, float g, long long m, float *A);
int ap_sim_records(const float *a, long long e0, int dir, long long L, long long d0,
                   int32_t *pos, float *val, long long *k, long long cap);
void ap_sim_twiddle(const float *x, const float *tw, size_t m, float *out);
void ap_sim_interleave_complex(const float *even_c, const float *odd_c, size_t m, float *out);

/* Rows are drawn and transformed in batches of SIM_ROWS (16, the widest SIMD lane count). */
enum { SIM_ROWS = 16 };

/* Emit running-maximum records for one active row r at stage s (0 = fine, 1..nb = coarse bands)
   from its transformed time series Yr (m complex samples). Returns -1 if a record array fills. */
static int sim_emit_row(long long r, long long s, long long n, long long nb, long long m,
                        float g, float keep2, int has_sig, int has_noise, int *kept_r,
                        const float *Yr, float *A, const float *tab, const long long *tv,
                        const int *fi, ap_sim_out *sig, long long *ks, ap_sim_out *noise,
                        long long *kn){
  if(has_noise && s>0){
    const int q=(int)(s-1);
    noise[q].off[r]=kn[q];
    ap_sim_power(Yr,NULL,g,m,A);
    if(ap_sim_records(A,0,1,m,0,noise[q].pos,noise[q].val,&kn[q],noise[q].cap)<0)
      return -1;
  }
  if(!has_sig) return 0;
  if(!*kept_r){
    for(int side=0;side<2;side++){
      const int q=(int)(2*s+side);
      sig[q].off[r]=ks[q];
    }
    return 0;
  }
  /* |noise + response| at lag js + e (mod m), e = 0 .. m-1: the response's table holds,
     per phase rho = t - js R, its values in that order (tab[f, s, rho m + e]) */
  const long long R = n/m, t=tv[r], js = t/R;
  const float *D = tab+(size_t)2*fi[r]*(1+nb)*n + (size_t)2*s*n + (size_t)2*(t - js*R)*m;
  const float m1=ap_sim_power(Yr+2*js,D,g,m-js,A), m2=ap_sim_power(Yr,D+2*(m-js),g,js,A+(m-js));
  if(s==0 && keep2>0.f){
    const float mx = m1>m2 ? m1 : m2;
    if(mx<keep2){
      /* no window keeps this draw: no records, and no band's signal pass */
      *kept_r=0;
      for(int side=0;side<2;side++) sig[side].off[r]=ks[side];
      return 0;
    }
  }
  for(int side=0;side<2;side++){
    const int q=(int)(2*s+side);
    sig[q].off[r]=ks[q];
    /* right: distances 0 .. m-1 forward; left: lag js - e is A[m - e], e = 1 .. m-1 */
    if(ap_sim_records(A, side ? m-1 : 0, side ? -1 : 1, side ? m-1 : m, side ? 1 : 0,
                      sig[q].pos, sig[q].val, &ks[q], sig[q].cap)<0)
      return -1;
  }
  return 0;
}
/* The gate model's simulation, whole (gatechain._simulate): row r of nrows is a block's n
   bins, bins [0, kmax) complex draws (row0 + r) * 2n .. of stream `seed` (ap_gauss_fill_rows)
   times scale[k], the rest empty. Band i's statistic is the b_i-point backward transform of
   bins [0, b_i) times bscale[i]; the fine one the n-point transform of all n times fscale.

   With noise outputs (npos, nval, noff: per band): each band's running maximum of
   the noise alone over its lags from 0, row r's at [off[r], off[r + 1]). With a signal (tab, t, fi
   and spos, sval, soff, pos int32): a signal arriving at t[r] + fi[r] / NF samples is added
   through the transforms' linearity, its response read from tab (complex64 (NF, 1 + nb, n):
   per arrival fraction the fine response, then each band's, in output units; statistic s of
   m lags R = n / m apart at [rho m + e] its response at lag js + e for a signal rho samples
   after coarse lag js), and statistic s (0 the fine, 1 + i band i) has its running maximum
   outward from the signal both ways, as records at [2s + side]: to the right from the lag at
   or before it (distance 0: lag t for the fine, coarse lag floor(t / R) for a band), to the
   left from the lag before (distance 1). A window's maximum is then the larger of the two
   sides' last records within its reach. A row whose fine statistic stays below keep_at at
   every lag (no window's fine stage keeps it) has no signal records. Without a signal no
   fine transform is made. The call stops at the first row whose records do not fit in their
   arrays, which are left as rows [0, done) made them (off[done] their end), so that a caller
   can continue from row0 + done with more room instead of starting over. Returns
   (signal counts, noise counts, done), the counts a tuple per array or None. */
static inline void sim_prep_band(const float *Xr, const float *Xo, long long kfill, long long m,
                                 long long k_lo, long long k_hi, float alpha, float beta, float *Xw){
  const long long k_end = k_hi < kfill ? k_hi : kfill;
  const long long len = k_end > k_lo ? k_end - k_lo : 0;
  if(k_lo <= 0 && alpha < 1.f){
    for(long long j = 0; j < 2*len; j++)
      Xw[j] = alpha * Xr[j] + beta * Xo[j];
    if(len < m) memset(Xw + 2*len, 0, (size_t)(2*(m - len))*sizeof(float));
    return;
  }
  if(len < m) memset(Xw, 0, (size_t)(2*m)*sizeof(float));
  if(len > 0){
    const long long u0 = k_lo & (m - 1);
    const long long first = len < m - u0 ? len : m - u0;
    if(alpha < 1.f){
      for(long long j = 0; j < 2*first; j++)
        Xw[2*u0 + j] = alpha * Xr[2*k_lo + j] + beta * Xo[2*k_lo + j];
      for(long long j = 0; j < 2*(len - first); j++)
        Xw[j] = alpha * Xr[2*(k_lo + first) + j] + beta * Xo[2*(k_lo + first) + j];
    } else {
      if(first > 0) memcpy(Xw + 2*u0, Xr + 2*k_lo, (size_t)(2*first)*sizeof(float));
      if(len > first) memcpy(Xw, Xr + 2*(k_lo + first), (size_t)(2*(len - first))*sizeof(float));
    }
  }
}

int ap_sim_setup(ap_sim *sim){
  const long long n = sim->n, kmax = sim->kmax, nb = sim->nb, max_band_hi = sim->max_band_hi;
  const long long *b = sim->b, *k0 = sim->k0, *khi = sim->khi;
  const float *al = sim->al;
  const int has_sig = sim->tab != NULL, skip_fine = sim->km != NULL;
  const int any_k0 = sim->any_k0, any_alpha = sim->any_alpha;
  int ok = 1;
  /* the noise alone (or a sub-band splice with precomputed kept_mask) needs no bins past max_band_hi */
  const long long kfill = (has_sig && !skip_fine) ? kmax : (kmax < max_band_hi ? kmax : max_band_hi);
  long long max_alpha_hi = 0;
  if(any_alpha){
    for(long long i=0;i<nb;i++){
      if(al[i] < 1.f){
        const long long hi_i = khi[i] < kfill ? khi[i] : kfill;
        if(hi_i > max_alpha_hi) max_alpha_hi = hi_i;
      }
    }
  }
  /* When simulating signals on a one-sided/bandlimited spectrum (kfill <= n / 2), the fine
     n-point backward transform splits into two n/2-point transforms: its even lags are the
     unmodified n/2-point backward transform (shared directly with the widest band when
     b[nb - 1] == n / 2 and k0[nb - 1] == 0, eliminating its transform entirely), and its odd
     lags are the n/2-point transform of X[k] * exp(+2 pi i k / n). */
  const int half_split = has_sig && !skip_fine && n >= 128 && (n & (n - 1)) == 0 && kfill <= n / 2;
  const long long nh = n / 2;
  const int share_widest = half_split && b[nb - 1] == nh && k0[nb - 1] == 0 && al[nb - 1] >= 1.f;
  ap_plan *pf = NULL, *ph_own = NULL, *ph = NULL, *pl[32] = {0};
  for(long long i=0;i<nb && ok;i++){
    pl[i] = ap_create((size_t)b[i]);
    if(!pl[i]) ok=0;
  }
  if(ok && has_sig && !skip_fine){
    if(half_split){
      ph = share_widest ? pl[nb-1] : (ph_own = ap_create((size_t)nh));
      if(!ph) ok=0;
    } else {
      pf = ap_create((size_t)n);
      if(!pf) ok=0;
    }
  }
  /* Pairbatch outputs are spaced by 2*m + 16 floats (+64B pad avoids L1D set aliasing). */
  size_t max_pb_m = 0;
  if(ok){
    if(pf && ap_plan_pairbatch(pf) > 0 && (size_t)n > max_pb_m) max_pb_m = (size_t)n;
    if(ph && ap_plan_pairbatch(ph) > 0 && (size_t)nh > max_pb_m) max_pb_m = (size_t)nh;
    for(long long i=0;i<nb;i++)
      if(ap_plan_pairbatch(pl[i]) > 0 && (size_t)b[i] > max_pb_m) max_pb_m = (size_t)b[i];
  }
  const int need_xw = any_k0 || any_alpha;
  const int need_xorth = any_alpha && max_alpha_hi > 0;
  const size_t xfloats = ((size_t)(2*kfill)+15u)&~(size_t)15u;
  const size_t xorth_floats = need_xorth ? (((size_t)(2*max_alpha_hi)+15u)&~(size_t)15u) : 0u;
  const size_t xwfloats = need_xw ? (((size_t)(2*b[nb-1])+15u)&~(size_t)15u) : 0u;
  const size_t ysingle = ((size_t)(2*n)+15u)&~(size_t)15u;
  const size_t ypb = max_pb_m ? (size_t)AP_MAX_LANES * (2u * max_pb_m + 16u) : 0u;
  const size_t yalloc = ysingle > ypb ? ysingle : ypb;
  const size_t yhfloats = half_split ? ((size_t)(2*nh) + 16u) : 0u;
  const int ph_w = (half_split && ph) ? ap_plan_pairbatch(ph) : 0;
  const size_t ph_lanes = ph_w > 0 ? (size_t)AP_MAX_LANES : 1u;
  float *X = (float*)ap_alloc64(SIM_ROWS * xfloats * sizeof(float)),
        *Xorth = need_xorth ? (float*)ap_alloc64(SIM_ROWS * xorth_floats * sizeof(float)) : NULL,
        *Xw = need_xw ? (float*)ap_alloc64(SIM_ROWS * xwfloats * sizeof(float)) : NULL,
        *Y = (float*)ap_alloc64(yalloc * sizeof(float)),
        *A = (float*)ap_alloc64((ysingle/2 + 16u) * sizeof(float)),
        *Yhalf = half_split ? (float*)ap_alloc64(SIM_ROWS * yhfloats * sizeof(float)) : NULL,
        *Yodd = half_split ? (float*)ap_alloc64(ph_lanes * yhfloats * sizeof(float)) : NULL,
        *Xtw = half_split ? (float*)ap_alloc64(ph_lanes * xfloats * sizeof(float)) : NULL,
        *tw = half_split ? (float*)ap_alloc64((xfloats + 16u) * sizeof(float)) : NULL;
  const int mem_ok = X && Y && A && (!need_xw || Xw) && (!need_xorth || Xorth)
                     && (!half_split || (Yhalf && Yodd && Xtw && tw));
  sim->kfill = kfill; sim->nh = nh; sim->max_alpha_hi = max_alpha_hi;
  sim->half_split = half_split; sim->share_widest = share_widest; sim->ph_w = ph_w;
  sim->pf = pf; sim->ph_own = ph_own; sim->ph = ph;
  for(long long i=0;i<nb;i++) sim->pl[i] = pl[i];
  sim->X = X; sim->Xorth = Xorth; sim->Xw = Xw; sim->Y = Y; sim->A = A; sim->Yhalf = Yhalf;
  sim->Yodd = Yodd; sim->Xtw = Xtw; sim->tw = tw;
  sim->xfloats = xfloats; sim->xorth_floats = xorth_floats; sim->xwfloats = xwfloats;
  sim->yhfloats = yhfloats;
  return ok && mem_ok ? 0 : -1;
}

void ap_sim_run(ap_sim *sim){
  const long long n = sim->n, nrows = sim->nrows, row0 = sim->row0, nb = sim->nb;
  const long long ns = 2*(1+nb), kfill = sim->kfill, nh = sim->nh, max_alpha_hi = sim->max_alpha_hi;
  const long long *b = sim->b, *k0 = sim->k0, *khi = sim->khi;
  const float *bs = sim->bs, *al = sim->al, *be = sim->be;
  const unsigned long long seed = sim->seed;
  const int has_sig = sim->tab != NULL, has_noise = sim->noise != NULL, skip_fine = sim->km != NULL;
  const int half_split = sim->half_split, share_widest = sim->share_widest, ph_w = sim->ph_w;
  ap_plan *pf = sim->pf, *ph = sim->ph, *const *pl = sim->pl;
  float *X = sim->X, *Xorth = sim->Xorth, *Xw = sim->Xw, *Y = sim->Y, *A = sim->A;
  float *Yhalf = sim->Yhalf, *Yodd = sim->Yodd, *Xtw = sim->Xtw, *tw = sim->tw;
  const size_t xfloats = sim->xfloats, xorth_floats = sim->xorth_floats;
  const size_t xwfloats = sim->xwfloats, yhfloats = sim->yhfloats;
  ap_sim_out *sig = sim->sig, *noise = sim->noise;
  long long *ks = sim->ks, *kn = sim->kn, done = nrows;
  const float *scale = sim->scale, *tab = sim->tab;
  const long long *tv = sim->t; const int *fi = sim->fi; const unsigned char *km = sim->km;
  const long long s0 = (has_sig && !skip_fine) ? 0 : 1;
  const float fs = (float)sim->fscale, keep2 = (float)(sim->keep_at*sim->keep_at);
  if(half_split){
    const double step_ang = 2.0 * 3.14159265358979323846 / (double)n;
    for(long long k=0;k<kfill;k++){
      const double ang = step_ang * (double)k;
      tw[2*k] = (float)cos(ang);
      tw[2*k+1] = (float)sin(ang);
    }
  }
  for(long long r0=0;r0<nrows;r0+=SIM_ROWS){
    const int B = (int)(nrows-r0 < SIM_ROWS ? nrows-r0 : SIM_ROWS);
    long long ks_batch[64], kn_batch[32];
    memcpy(ks_batch,ks,(size_t)ns*sizeof *ks); memcpy(kn_batch,kn,(size_t)nb*sizeof *kn);
    /* a retention's bands read the kept rows only: the others are not drawn */
    const unsigned char *drawn = (km && !has_noise) ? km+r0 : NULL;
    ap_gauss_fill_rows(X,xfloats,(size_t)B,(size_t)(2*kfill),(uint64_t)seed,
                       (uint64_t)(2*(row0+r0)*n),(uint64_t)(2*n),scale,drawn);
    if(Xorth){
      ap_gauss_fill_rows(Xorth,xorth_floats,(size_t)B,(size_t)(2*max_alpha_hi),
                         (uint64_t)seed^(2ULL<<32),
                         (uint64_t)(2*(row0+r0)*n),(uint64_t)(2*n),scale,drawn);
    }
    int kept[SIM_ROWS];
    for(int bi=0;bi<B;bi++) kept[bi] = km ? (km[r0+bi]!=0) : 1;
    if(skip_fine){
      for(int bi=0;bi<B;bi++){
        sig[0].off[r0+bi]=0;
        sig[1].off[r0+bi]=0;
      }
    }
    int batch_full=0;
    if(half_split){
      /* Precompute even half-transforms Yhalf[0..B-1] once (reused at s = nb when share_widest). */
      const size_t hv_h = (size_t)kfill;
      if(ph_w > 0){
        for(int a0=0;a0<B;a0+=ph_w){
          const int cnt = B-a0 < ph_w ? B-a0 : ph_w;
          const float *srcs[AP_MAX_LANES];
          float *outs[AP_MAX_LANES];
          for(int l=0;l<cnt;l++){
            srcs[l] = X + (size_t)(a0+l)*xfloats;
            outs[l] = Yhalf + (size_t)(a0+l)*yhfloats;
          }
          ap_fft_backward_batch(ph,srcs,hv_h,cnt,outs);
        }
      } else {
        for(int bi=0;bi<B;bi++)
          ap_fft_backward_padded(ph,X+(size_t)bi*xfloats,hv_h,Yhalf+(size_t)bi*yhfloats);
      }
    }
    for(long long s = s0; s<=nb && !batch_full; s++){
      const long long m = s==0 ? n : b[s-1];
      const float g = s==0 ? fs : bs[s-1];
      if(s==0 && half_split){
        const size_t hv_h = (size_t)kfill;
        if(ph_w > 0){
          for(int a0=0;a0<B && !batch_full;a0+=ph_w){
            const int cnt = B-a0 < ph_w ? B-a0 : ph_w;
            const float *srcs[AP_MAX_LANES];
            float *outs[AP_MAX_LANES];
            for(int l=0;l<cnt;l++){
              float *xt = Xtw + (size_t)l*xfloats;
              ap_sim_twiddle(X+(size_t)(a0+l)*xfloats,tw,hv_h,xt);
              srcs[l] = xt;
              outs[l] = Yodd + (size_t)l*yhfloats;
            }
            ap_fft_backward_batch(ph,srcs,hv_h,cnt,outs);
            for(int l=0;l<cnt;l++){
              const int bi = a0+l;
              ap_sim_interleave_complex(Yhalf+(size_t)bi*yhfloats,outs[l],(size_t)nh,Y);
              if(sim_emit_row(r0+bi,0,n,nb,n,g,keep2,has_sig,has_noise,&kept[bi],
                              Y,A,tab,tv,fi,sig,ks,noise,kn)<0){
                batch_full=1;
                break;
              }
            }
          }
        } else {
          for(int bi=0;bi<B;bi++){
            ap_sim_twiddle(X+(size_t)bi*xfloats,tw,hv_h,Xtw);
            ap_fft_backward_padded(ph,Xtw,hv_h,Yodd);
            ap_sim_interleave_complex(Yhalf+(size_t)bi*yhfloats,Yodd,(size_t)nh,Y);
            if(sim_emit_row(r0+bi,0,n,nb,n,g,keep2,has_sig,has_noise,&kept[bi],
                            Y,A,tab,tv,fi,sig,ks,noise,kn)<0){
              batch_full=1;
              break;
            }
          }
        }
        continue;
      }
      if(share_widest && s==nb){
        for(int bi=0;bi<B;bi++){
          if(!(has_noise || kept[bi])){
            const long long r=r0+bi;
            for(int side=0;side<2;side++) sig[2*s+side].off[r]=ks[2*s+side];
            continue;
          }
          if(sim_emit_row(r0+bi,s,n,nb,m,g,keep2,has_sig,has_noise,&kept[bi],
                          Yhalf+(size_t)bi*yhfloats,A,tab,tv,fi,sig,ks,noise,kn)<0){
            batch_full=1;
            break;
          }
        }
        continue;
      }
      ap_plan *ps = s==0 ? pf : pl[s-1];
      const int wrap_band = s>0 && k0[s-1]>0;
      const int prep_band = s>0 && (k0[s-1]>0 || al[s-1]<1.f);
      const size_t hv = wrap_band ? (size_t)m : (size_t)(kfill < m ? kfill : m);
      const int w = ap_plan_pairbatch(ps);
      if(w > 0){
        const size_t bstride = 2u * (size_t)m + 16u;
        int active[SIM_ROWS], nact=0;
        const float *srcs[SIM_ROWS];
        for(int bi=0;bi<B;bi++){
          if(s==0 || has_noise || kept[bi]){
            const float *Xr = X+(size_t)bi*xfloats;
            if(prep_band){
              const float *Xo = Xorth ? Xorth+(size_t)bi*xorth_floats : NULL;
              float *dst = Xw + (size_t)nact * xwfloats;
              sim_prep_band(Xr, Xo, kfill, m, k0[s-1], khi[s-1], al[s-1], be[s-1], dst);
              srcs[nact] = dst;
            } else {
              srcs[nact] = Xr;
            }
            active[nact++]=bi;
          }
        }
        int next_bi=0;
        for(int a0=0;a0<nact && !batch_full;a0+=w){
          const int cnt = nact-a0 < w ? nact-a0 : w;
          float *outs[AP_MAX_LANES];
          for(int l=0;l<cnt;l++) outs[l]=Y+(size_t)l*bstride;
          ap_fft_backward_batch(ps,srcs+a0,hv,cnt,outs);
          for(int l=0;l<cnt;l++){
            const int target=active[a0+l];
            while(next_bi<target){
              const long long r=r0+next_bi++;
              for(int side=0;side<2;side++) sig[2*s+side].off[r]=ks[2*s+side];
            }
            if(sim_emit_row(r0+target,s,n,nb,m,g,keep2,has_sig,has_noise,&kept[target],
                            outs[l],A,tab,tv,fi,sig,ks,noise,kn)<0){
              batch_full=1;
              break;
            }
            next_bi++;
          }
        }
        while(next_bi<B && !batch_full){
          const long long r=r0+next_bi++;
          for(int side=0;side<2;side++) sig[2*s+side].off[r]=ks[2*s+side];
        }
      } else {
        for(int bi=0;bi<B;bi++){
          if(!(s==0 || has_noise || kept[bi])){
            const long long r=r0+bi;
            for(int side=0;side<2;side++) sig[2*s+side].off[r]=ks[2*s+side];
            continue;
          }
          const float *Xin = X+(size_t)bi*xfloats;
          if(prep_band){
            const float *Xo = Xorth ? Xorth+(size_t)bi*xorth_floats : NULL;
            sim_prep_band(Xin, Xo, kfill, m, k0[s-1], khi[s-1], al[s-1], be[s-1], Xw);
            Xin = Xw;
          }
          ap_fft_backward_padded(ps,Xin,hv,Y);
          if(sim_emit_row(r0+bi,s,n,nb,m,g,keep2,has_sig,has_noise,&kept[bi],
                          Y,A,tab,tv,fi,sig,ks,noise,kn)<0){
            batch_full=1;
            break;
          }
        }
      }
    }
    if(batch_full){
      /* A record array filled inside this batch: rewind to batch start and replay row by row
         so `done` stops at the exact first row whose records do not fit. */
      memcpy(ks,ks_batch,(size_t)ns*sizeof *ks); memcpy(kn,kn_batch,(size_t)nb*sizeof *kn);
      for(int bi=0;bi<B;bi++){
        const long long r=r0+bi;
        long long ks0[64], kn0[32];
        memcpy(ks0,ks,(size_t)ns*sizeof *ks); memcpy(kn0,kn,(size_t)nb*sizeof *kn);
        int full=0, kept1 = km ? (km[r]!=0) : 1;
        if(skip_fine){
          sig[0].off[r]=0;
          sig[1].off[r]=0;
        }
        const float *Xr=X+(size_t)bi*xfloats;
        const float *Xo=Xorth ? Xorth+(size_t)bi*xorth_floats : NULL;
        for(long long s = s0; s<=nb && !full; s++){
          const long long m = s==0 ? n : b[s-1];
          const float g = s==0 ? fs : bs[s-1];
          if(!(s==0 || has_noise || kept1)){
            for(int side=0;side<2;side++) sig[2*s+side].off[r]=ks[2*s+side];
            continue;
          }
          const float *Yr_row = Y;
          if(s==0 && half_split){
            const size_t hv_h = (size_t)kfill;
            ap_sim_twiddle(Xr,tw,hv_h,Xtw);
            const float *xt = Xtw;
            if(ph_w > 0) ap_fft_backward_batch(ph,&xt,hv_h,1,&Yodd);
            else ap_fft_backward_padded(ph,Xtw,hv_h,Yodd);
            ap_sim_interleave_complex(Yhalf+(size_t)bi*yhfloats,Yodd,(size_t)nh,Y);
          } else if(share_widest && s==nb){
            Yr_row = Yhalf + (size_t)bi * yhfloats;
          } else {
            ap_plan *ps = s==0 ? pf : pl[s-1];
            const int wrap_band = s>0 && k0[s-1]>0;
            const int prep_band = s>0 && (k0[s-1]>0 || al[s-1]<1.f);
            const float *Xin = Xr;
            if(prep_band){
              sim_prep_band(Xr, Xo, kfill, m, k0[s-1], khi[s-1], al[s-1], be[s-1], Xw);
              Xin = Xw;
            }
            const size_t hv = wrap_band ? (size_t)m : (size_t)(kfill < m ? kfill : m);
            if(ap_plan_pairbatch(ps) > 0) ap_fft_backward_batch(ps,&Xin,hv,1,&Y);
            else ap_fft_backward_padded(ps,Xin,hv,Y);
          }
          if(sim_emit_row(r,s,n,nb,m,g,keep2,has_sig,has_noise,&kept1,
                          Yr_row,A,tab,tv,fi,sig,ks,noise,kn)<0){
            full=1;
            break;
          }
        }
        if(full){
          memcpy(ks,ks0,(size_t)ns*sizeof *ks); memcpy(kn,kn0,(size_t)nb*sizeof *kn);
          done=r;
          break;
        }
      }
      break;
    }
  }
  if(has_sig) for(long long q=0;q<ns;q++) sig[q].off[done]=ks[q];
  if(has_noise) for(long long q=0;q<nb;q++) noise[q].off[done]=kn[q];
  sim->done = done;
}

void ap_sim_free(ap_sim *sim){
free(sim->X); free(sim->Xorth); free(sim->Xw); free(sim->Y); free(sim->A); free(sim->Yhalf); free(sim->Yodd); free(sim->Xtw); free(sim->tw);
if(sim->pf) ap_destroy(sim->pf);
if(sim->ph_own) ap_destroy(sim->ph_own);
for(long long i=0;i<sim->nb;i++){ if(sim->pl[i]) ap_destroy(sim->pl[i]); }
}
